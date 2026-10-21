"""Portfolio content calendar — all enabled products, planned together.

Round-robin across products (ordered by readiness, so the most ready product
leads each day), at most one post per product per day, weekdays only,
`max_posts_per_day` slots a day. Each slot gets the product's primary platform,
the next unused pillar for that product, and avoids facts already used in the
calendar. Every slot becomes a validated draft awaiting human approval; slots
for products with no connected account are marked draft-only.
"""
from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from ..context import Context
from ..products.profile import load_profile
from .planner import build_plan, recent_usage
from .validator import guardrail_blocked_facts
from .writer import PILLARS, TemplateWriter

SLOT_TIMES = [time(12, 0), time(13, 30), time(15, 0), time(10, 30), time(16, 0)]


def _weekdays(start: date, weeks: int, days: list[int]) -> list[date]:
    out, d = [], start
    while len(out) < weeks * len(days):
        if d.weekday() in days:
            out.append(d)
        d += timedelta(days=1)
    return out


def build_calendar(ctx: Context, start: date | None = None, weeks: int = 2) -> dict:
    if ctx.policy.kill_switch_active():
        raise PermissionError("kill switch is active")
    from ..workflows import validate_content

    tz = ZoneInfo(ctx.settings["timezone"])
    start = start or (ctx.policy.london_now().date() + timedelta(days=1))
    per_day = int(ctx.settings.limit("max_posts_per_day"))
    channels = json.loads((ctx.root / "config" / "channels.json").read_text())
    primary = channels.get("primary_platform", {})
    plan = build_plan(ctx.root, ctx.store, per_day)
    order = [p["slug"] for p in plan["products"]]           # readiness order
    if not order:
        return {"slots": []}

    profiles = {s: load_profile(ctx.root, s) for s in order}
    used_facts: dict[str, set[str]] = {}
    blocked = {s: guardrail_blocked_facts(profiles[s]) for s in order}
    pillar_cursor: dict[str, int] = {}
    for s in order:
        used_p, used_f = recent_usage(ctx.store, s)
        used_facts[s] = set(used_f)
        unused = [i for i, p in enumerate(PILLARS) if p not in used_p]
        pillar_cursor[s] = unused[0] if unused else 0

    writer, slots, rr = TemplateWriter(), [], 0
    for day in _weekdays(start, weeks, ctx.settings["operating_hours"]["days"]):
        for k in range(min(per_day, len(order))):
            slug = order[rr % len(order)]
            rr += 1
            prof = profiles[slug]
            connected = [c["destination"].split(":", 1)[1] for c in channels["products"].get(slug, []) if c.get("verified")]
            platform = primary.get(slug) or (connected[0] if connected else "linkedin")
            dests = [c["destination"] for c in channels["products"].get(slug, [])
                     if c.get("verified") and c["destination"].endswith(":" + platform)]
            when = datetime.combine(day, SLOT_TIMES[k % len(SLOT_TIMES)], tzinfo=tz)
            slot_key = f"{slug}|{when.isoformat(timespec='minutes')}"
            existing = ctx.store.conn.execute(
                "SELECT id, status FROM content WHERE json_extract(body, '$.calendar_slot')=? "
                "AND status NOT IN ('cancelled','rejected')", (slot_key,)).fetchone()
            if existing:                                       # idempotent: a re-run reuses the slot's draft
                item = ctx.store.get_content(existing["id"])
                used_facts[slug].update(item["body"].get("fact_ids", []))
                slots.append({"date": day.isoformat(), "time": when.strftime("%H:%M"), "product": slug,
                              "platform": item["platform"], "pillar": item["body"].get("pillar"),
                              "publish_route": dests[0] if dests else "draft-only (no connected account)",
                              "content_id": existing["id"], "status": existing["status"], "errors": []})
                pillar_cursor[slug] += 1
                continue
            draft, pillar = None, None
            for attempt in range(len(PILLARS)):                # first pillar this product can fill
                pillar = PILLARS[(pillar_cursor[slug] + attempt) % len(PILLARS)]
                draft = writer.social_post(prof, platform, pillar, avoid=used_facts[slug], offset=rr,
                                           exclude=blocked[slug])
                if draft is not None:
                    pillar_cursor[slug] += attempt + 1
                    break
            slot = {"date": day.isoformat(), "time": when.strftime("%H:%M"), "product": slug, "platform": platform,
                    "pillar": pillar, "publish_route": dests[0] if dests else "draft-only (no connected account)"}
            if draft is None:
                slots.append(slot | {"status": "skipped: not enough verified facts"})
                continue
            used_facts[slug].update(draft.fact_ids)
            cid, created = ctx.store.add_content(
                product=slug, kind="social_post", platform=platform, fingerprint=draft.fingerprint(),
                body=draft.body() | {"planned_destinations": dests, "scheduled_for": when.isoformat(timespec="seconds"),
                                     "calendar_start": start.isoformat(), "calendar_slot": slot_key})
            res = validate_content(ctx, cid)
            slots.append(slot | {"content_id": cid, "status": res["status"] if created else "duplicate of existing draft",
                                 "errors": res["validation"]["errors"]})

    cal = {"start": start.isoformat(), "weeks": weeks, "products": order, "slots": slots,
           "generated_at": ctx.policy.london_now().isoformat(timespec="seconds")}
    out = ctx.root / "var" / "calendar"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{start.isoformat()}.json").write_text(json.dumps(cal, indent=2))
    (out / f"{start.isoformat()}.md").write_text(render_markdown(cal))
    return cal


def render_markdown(cal: dict) -> str:
    lines = [f"# Content calendar from {cal['start']} ({cal['weeks']} weeks, all products)", "",
             "| Date | Time | Product | Platform | Pillar | Route | Content | Status |", "|---|---|---|---|---|---|---|---|"]
    for s in cal["slots"]:
        lines.append(f"| {s['date']} | {s['time']} | {s['product']} | {s['platform']} | {s['pillar']} | "
                     f"{s['publish_route']} | `{s.get('content_id', '—')}` | {s['status']} |")
    counts: dict[str, int] = {}
    for s in cal["slots"]:
        counts[s["product"]] = counts.get(s["product"], 0) + 1
    lines += ["", "**Share of slots:** " + ", ".join(f"{k} {v}" for k, v in counts.items()),
              "", "Approve with `mas approve <content_id> --by <name>`; nothing posts until approved and live."]
    return "\n".join(lines) + "\n"
