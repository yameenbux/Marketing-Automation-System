"""Unattended operations: state that survives fresh cloud sessions, the approval desk, morning/evening runs.

State lives in `state/ops_state.json` (committed). It deliberately EXCLUDES leads, suppression and outreach —
personal-data-adjacent records never go into this repository; they live in the private Google Sheet.
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from .context import Context
from .store import now_iso

STATE_TABLES = ("content", "campaigns", "publications", "runs", "costs", "sync_state")
NEVER_EXPORT = ("leads", "suppression", "outreach")
AUDIT_DAYS = 30


def state_path(ctx: Context) -> Path:
    return ctx.root / "state" / "ops_state.json"


def export_state(ctx: Context, path: Path | None = None) -> Path:
    path = path or state_path(ctx)
    since = (date.today() - timedelta(days=AUDIT_DAYS)).isoformat()
    data = {"exported_at": now_iso(), "tables": {}}
    for t in STATE_TABLES:
        data["tables"][t] = [dict(r) for r in ctx.store.q(f"SELECT * FROM {t}")]  # noqa: S608 — fixed table names
    data["tables"]["audit"] = [dict(r) for r in ctx.store.q("SELECT * FROM audit WHERE ts >= ?", (since,))]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, sort_keys=True, default=str), encoding="utf-8")
    return path


def import_state(ctx: Context, path: Path | None = None) -> dict:
    path = path or state_path(ctx)
    if not path.exists():
        return {"imported": False, "reason": "no state file"}
    data = json.loads(path.read_text(encoding="utf-8"))
    counts = {}
    with ctx.store.tx() as c:
        for t, rows in data["tables"].items():
            if t in NEVER_EXPORT or not rows:
                continue
            cols = list(rows[0].keys())
            marks = ",".join("?" * len(cols))
            for r in rows:
                c.execute(f"INSERT OR REPLACE INTO {t} ({','.join(cols)}) VALUES ({marks})",  # noqa: S608
                          [r[k] for k in cols])
            counts[t] = len(rows)
    return {"imported": True, "counts": counts, "exported_at": data.get("exported_at")}


# --- approval desk ----------------------------------------------------------------
def desk_queue(ctx: Context, repo_web: str | None = None) -> list[dict]:
    """Everything waiting on a human: unapproved profiles and validated content, newest first."""
    from .products.profile import list_profiles, load_profile
    from .publishing.media import public_url, still_for
    media_base = ctx.settings.data.get("media", {}).get("base_url")
    items = []
    for slug in list_profiles(ctx.root):
        p = load_profile(ctx.root, slug)
        if p.approved:
            continue
        lims = [f.text for f in p.limitations()][:4]
        items.append({"id": f"profile:{slug}", "kind": "profile", "product": slug, "title": f"{p.name} — product profile",
                      "text": f"{len(p.facts)} facts, all quote-verified against the README. Approving lets this "
                              f"product's posts be approved. Known limitations the copy will never claim: "
                              + " · ".join(lims),
                      "link": f"{repo_web}/data/products/{slug}/PROFILE.md" if repo_web else None,
                      "media": public_url(media_base, still_for(ctx.root, slug, None))})
    for r in ctx.store.q("SELECT id, product, platform, body, created_at FROM content WHERE status='validated' "
                         "ORDER BY json_extract(body, '$.scheduled_for'), created_at"):
        b = json.loads(r["body"])
        routes = b.get("planned_destinations") or []
        items.append({"id": f"content:{r['id']}", "kind": b.get("post_type", "post").lower(), "product": r["product"],
                      "title": f"{r['product']} · {r['platform']} · {b.get('pillar', '')}",
                      "text": b["text"], "when": b.get("scheduled_for"),
                      "route": routes[0] if routes else "draft only — no connected account",
                      "media": (b.get("media_urls") or [public_url(media_base, still_for(ctx.root, r["product"], b.get("pillar")))])[0]})
    return items


def apply_decisions(ctx: Context, decisions: list[dict]) -> list[dict]:
    """Apply desk decisions: [{"id": "profile:x"|"content:cnt_..", "decision": "approve"|"reject", "by": "..."}]."""
    from .workflows import approve_content, approve_profile
    out = []
    for d in sorted(decisions, key=lambda d: 0 if d["id"].startswith("profile:") else 1):   # profiles first
        kind, ref = d["id"].split(":", 1)
        who = f"approval desk ({d.get('by') or 'owner'})"
        try:
            if d["decision"] == "approve":
                if kind == "profile":
                    approve_profile(ctx, ref, who)
                else:
                    approve_content(ctx, ref, who)
            elif d["decision"] == "reject" and kind == "content":
                item = ctx.store.get_content(ref)
                if item and item["status"] in ("validated", "draft", "rejected"):
                    ctx.store.set_content_status(ref, "cancelled")
                    ctx.store.audit("reject_content", "human", "ok", f"rejected by {who}: {d.get('note', '')}",
                                    {"content_id": ref})
            out.append({"id": d["id"], "applied": True})
        except Exception as e:  # noqa: BLE001 — report per item, keep going
            out.append({"id": d["id"], "applied": False, "error": str(e)})
    return out


# --- the two daily runs -----------------------------------------------------------------
def morning(ctx: Context, decisions_file: Path | None = None) -> dict:
    """Sync → plan → produce → keep a 2-week calendar → apply approvals → schedule approved posts (outbox)."""
    from . import workflows
    from .marketing.calendar import build_calendar
    if ctx.policy.kill_switch_active():
        return {"ran": False, "reason": "kill switch active"}
    summary: dict = {"state": import_state(ctx)}
    if decisions_file and decisions_file.exists():
        summary["decisions"] = apply_decisions(ctx, json.loads(decisions_file.read_text()))
    summary["plan"] = {"skipped": "already ran"} if not ctx.store.start_run(
        f"planner:{ctx.policy.london_now().date()}", "planner") else _plan(ctx)
    start = ctx.policy.london_now().date()          # today's later slots (12:00, 13:30, 15:00) are still ahead at 09:07
    cal = build_calendar(ctx, start, weeks=2)
    summary["calendar_slots"] = len(cal["slots"])
    summary["published"] = workflows.run_publishing(ctx)
    export_state(ctx)
    return summary


def _plan(ctx: Context) -> dict:
    from . import workflows
    from .marketing.planner import build_plan
    try:
        sync = workflows.run_sync(ctx)
        plan = build_plan(ctx.root, ctx.store, int(ctx.settings.limit("max_posts_per_day")))
        out = ctx.root / "var" / "plans" / f"{ctx.policy.london_now().date()}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(plan, indent=2))
        ctx.store.finish_run(f"planner:{ctx.policy.london_now().date()}", "ok", {"plan": str(out)})
        return {"products": [p["slug"] for p in plan["products"]],
                "sync": [{"slug": s["slug"], "changed": s["changed"], "errors": s["errors"]} for s in sync]}
    except Exception as e:  # noqa: BLE001
        ctx.store.finish_run(f"planner:{ctx.policy.london_now().date()}", "error", {"error": str(e)})
        raise


def evening(ctx: Context) -> dict:
    from .analytics import report
    import_state(ctx)
    text, path = report.build(ctx)
    export_state(ctx)
    return {"report": str(path)}
