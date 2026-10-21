"""Workflow entry points (A–G). Each is idempotent per London date where it matters.

These are thin orchestration functions; the logic lives in the modules they call.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from .config import Settings
from .context import Context
from .github_sync.client import GitHubClient
from .github_sync.sync import sync_all
from .marketing.planner import build_plan
from .marketing.validator import validate
from .marketing.writer import TemplateWriter
from .products.profile import load_profile
from .publishing.publisher import Publisher


def _today(ctx: Context) -> str:
    return ctx.policy.london_now().date().isoformat()


def _plans_dir(ctx: Context) -> Path:
    d = ctx.root / "var" / "plans"
    d.mkdir(parents=True, exist_ok=True)
    return d


# --- sync ------------------------------------------------------------------
def run_sync(ctx: Context, only: str | None = None) -> list[dict]:
    client = GitHubClient(token=Settings.secret("GITHUB_TOKEN"),
                          max_requests=int(ctx.settings.limit("max_github_requests_per_run")))
    return [r.as_dict() for r in sync_all(client, ctx.policy, ctx.root, only=only)]


# --- A: daily planner ------------------------------------------------------
def run_planner(ctx: Context, force: bool = False) -> dict:
    key = f"planner:{_today(ctx)}"
    plan_path = _plans_dir(ctx) / f"{_today(ctx)}.json"
    if not ctx.store.start_run(key, "planner") and not force:
        return {"skipped": "planner already ran today", "plan": str(plan_path)}
    try:
        if ctx.policy.kill_switch_active():
            raise PermissionError("kill switch is active")
        sync = run_sync(ctx)
        plan = build_plan(ctx.root, ctx.store, int(ctx.settings.limit("max_posts_per_day")))
        plan["sync"] = [{k: s[k] for k in ("slug", "commit", "changed", "errors")} for s in sync]
        plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
        ctx.store.finish_run(key, "ok", {"plan": str(plan_path)})
        return plan
    except Exception as e:
        ctx.store.finish_run(key, "error", {"error": str(e)})
        ctx.store.audit("workflow", "planner", "error", str(e))
        raise


# --- B + C: production and validation ---------------------------------------
def run_production(ctx: Context, plan: dict | None = None) -> list[dict]:
    if ctx.policy.kill_switch_active():
        raise PermissionError("kill switch is active")
    plan = plan or json.loads((_plans_dir(ctx) / f"{_today(ctx)}.json").read_text())
    writer, out = TemplateWriter(), []
    from .acquisition import content_gate
    from .marketing.calendar import _posted_on
    gate, today = content_gate(ctx.root), ctx.policy.london_now().date()
    for pp in plan["products"]:
        if gate is not None and (pp["slug"] not in gate or today.weekday() not in gate[pp["slug"]]["post_days"]
                                 or not pp["destinations"] or _posted_on(ctx, pp["slug"], today)):
            out.append({"product": pp["slug"], "status": "skipped: no acquisition hypothesis needs content today"})
            continue
        prof = load_profile(ctx.root, pp["slug"])
        for action in pp["actions"]:
            if not action.startswith(("produce_post:", "draft_only:")):
                continue
            pillar = action.split(":", 1)[1]
            primary = json.loads((ctx.root / "config" / "channels.json").read_text()).get("primary_platform", {})
            platforms = [d.split(":", 1)[1] for d in pp["destinations"]] or [primary.get(pp["slug"], "linkedin")]
            for platform in platforms:
                from .marketing.validator import guardrail_blocked_facts
                draft = writer.social_post(prof, platform, pillar, avoid=set(pp["avoid_fact_ids"]),
                                           exclude=guardrail_blocked_facts(prof))
                if draft is None:
                    out.append({"product": pp["slug"], "pillar": pillar, "status": "skipped (not enough facts)"})
                    continue
                cid, created = ctx.store.add_content(product=draft.product, kind=draft.kind, platform=platform,
                                                     body=draft.body() | {"planned_destinations": pp["destinations"],
                                                                          "hypothesis": (gate or {}).get(pp["slug"], {}).get("hypothesis")},
                                                     fingerprint=draft.fingerprint())
                out.append({"content_id": cid, "product": pp["slug"], "platform": platform, "pillar": pillar,
                            "created": created, **validate_content(ctx, cid)})
    return out


def validate_content(ctx: Context, cid: str) -> dict:
    item = ctx.store.get_content(cid)
    prof = load_profile(ctx.root, item["product"])
    res = validate(item["body"]["text"], product=prof, platform=item["platform"],
                   fact_ids=item["body"].get("fact_ids", []))
    if item["status"] in ("draft", "rejected", "validated"):
        new = "validated" if res.ok else "rejected"
        if item["status"] == "rejected" and new == "validated":
            ctx.store.set_content_status(cid, "draft")
        if item["status"] != new:
            ctx.store.set_content_status(cid, new, res.as_dict())
        else:
            ctx.store.conn.execute("UPDATE content SET validation=? WHERE id=?", (json.dumps(res.as_dict()), cid))
            ctx.store.conn.commit()
    return {"status": ctx.store.get_content(cid)["status"], "validation": res.as_dict()}


def approve_content(ctx: Context, cid: str, approver: str) -> dict:
    """Human approval. Re-validates at approval time; requires an approved product profile."""
    item = ctx.store.get_content(cid)
    if item is None:
        raise KeyError(cid)
    prof = load_profile(ctx.root, item["product"])
    if not prof.approved:
        raise PermissionError(f"profile '{prof.slug}' is not approved — approve it first (mas profile approve)")
    result = validate_content(ctx, cid)
    if result["status"] != "validated":
        raise PermissionError(f"content does not pass validation: {result['validation']['errors']}")
    ctx.store.set_content_status(cid, "approved")
    ctx.store.audit("approve_content", "human", "ok", f"approved by {approver}", {"content_id": cid})
    return {"content_id": cid, "status": "approved"}


def approve_profile(ctx: Context, slug: str, approver: str) -> dict:
    path = ctx.root / "data" / "products" / slug / "profile.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    prof = load_profile(ctx.root, slug)
    bad = [f.id for f in prof.facts if f.status != "verified"]
    if bad:
        raise PermissionError(f"cannot approve: unverified facts {bad}")
    data["approval"] = {"status": "approved", "approved_by": approver,
                        "approved_at": ctx.policy.london_now().isoformat(timespec="seconds")}
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ctx.store.audit("approve_profile", "human", "ok", f"{slug} approved by {approver}")
    return data["approval"]


# --- D: publishing -----------------------------------------------------------
def run_publishing(ctx: Context, when: datetime | None = None) -> list[dict]:
    settings = ctx.settings.data
    pub = Publisher(ctx.policy, ctx.store, ctx.root,
                    metricool_blog_id=str(settings.get("metricool", {}).get("blog_id") or "") or None,
                    reviewer=settings.get("metricool", {}).get("reviewer_email"),
                    media_base=settings.get("media", {}).get("base_url"))
    when = when or (ctx.policy.london_now() + timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0)
    out = []
    for row in ctx.store.q("SELECT id, body FROM content WHERE status='approved' ORDER BY created_at"):
        body = json.loads(row["body"])
        slot_time = body.get("scheduled_for") or when.isoformat(timespec="seconds")   # calendar slot wins
        for dest in body.get("planned_destinations", []):
            r = pub.schedule(row["id"], dest, slot_time)
            out.append({"content_id": row["id"], "destination": dest, **r.__dict__})
    return out
