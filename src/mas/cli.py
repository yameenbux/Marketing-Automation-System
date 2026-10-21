"""`mas` command-line interface — the one operator interface for every workflow."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .context import Context


def _print(obj) -> None:
    print(json.dumps(obj, indent=2, default=str, ensure_ascii=False) if not isinstance(obj, str) else obj)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="mas", description="YSB marketing automation (dry-run by default)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="mode, kill switch, profiles, pending approvals")
    p = sub.add_parser("sync", help="sync approved docs from public product repos"); p.add_argument("--product")
    p = sub.add_parser("plan", help="Workflow A: daily plan"); p.add_argument("--force", action="store_true")
    sub.add_parser("produce", help="Workflow B+C: write and validate today's planned posts")
    p = sub.add_parser("calendar", help="portfolio content calendar for all products (validated drafts)")
    p.add_argument("--weeks", type=int, default=2); p.add_argument("--start", help="YYYY-MM-DD (default tomorrow)")
    p = sub.add_parser("campaign", help="Workflow B: full creative pack (video, graphics, copy)")
    p.add_argument("product"); p.add_argument("--objective", required=True)
    p.add_argument("--formats", default="story,square,landscape"); p.add_argument("--no-narration", action="store_true")
    p.add_argument("--no-screenshots", action="store_true"); p.add_argument("--force", action="store_true")
    p = sub.add_parser("film", help="cinematic film in the product's own art direction (HTML motion engine)")
    p.add_argument("product"); p.add_argument("--formats", default="story,square,landscape,portrait")
    p.add_argument("--fps", type=int, default=30); p.add_argument("--no-screenshots", action="store_true")
    p = sub.add_parser("profile", help="show a product profile and fact verification"); p.add_argument("product")
    p = sub.add_parser("approve-profile"); p.add_argument("product"); p.add_argument("--by", required=True)
    p = sub.add_parser("content", help="list content"); p.add_argument("--status")
    p = sub.add_parser("show", help="show one content item"); p.add_argument("content_id")
    p = sub.add_parser("approve", help="human-approve validated content"); p.add_argument("content_id")
    p.add_argument("--by", required=True)
    p = sub.add_parser("cancel", help="cancel content"); p.add_argument("content_id")
    sub.add_parser("publish", help="Workflow D: schedule approved content (dry-run unless live)")
    p = sub.add_parser("leads-import", help="Workflow E: import researched leads CSV"); p.add_argument("product")
    p.add_argument("csv")
    p = sub.add_parser("leads", help="list leads"); p.add_argument("--product")
    p = sub.add_parser("suppress", help="add to suppression list"); p.add_argument("key"); p.add_argument("--reason", required=True)
    p = sub.add_parser("outreach-prepare", help="Workflow F: eligibility + draft"); p.add_argument("lead_id")
    p.add_argument("--channel", default="email"); p.add_argument("--consent")
    sub.add_parser("report", help="Workflow G: daily report")
    sub.add_parser("tick", help="run whatever is due now (call every 15–30 min)")
    p = sub.add_parser("ops", help="scheduled runs: morning (plan, calendar, approvals, schedule) / evening (report)")
    p.add_argument("run", choices=["morning", "evening"]); p.add_argument("--decisions", help="desk decisions JSON")
    p = sub.add_parser("state", help="persist operational state across sessions"); p.add_argument("op", choices=["export", "import"])
    p = sub.add_parser("desk", help="approval desk queue / apply decisions"); p.add_argument("op", choices=["queue", "apply"])
    p.add_argument("--file")
    p = sub.add_parser("acq", help="customer acquisition: plan checks, prospects, pipeline report, plan docs")
    p.add_argument("op", choices=["check", "prospects", "report", "docs", "seed"]); p.add_argument("product", nargs="?")
    p.add_argument("--events", help="pipeline events JSON (default var/pipeline/events.json)")
    p.add_argument("--date", help="report as of YYYY-MM-DD (default today, London)")
    p = sub.add_parser("kill-switch", help="engage or release the global kill switch")
    p.add_argument("state", choices=["on", "off"]); p.add_argument("--reason", default="manual")

    a = ap.parse_args(argv)
    ctx = Context.create()

    if a.cmd == "acq":
        from datetime import date as _date
        from . import acquisition as acq
        if a.op == "check":
            problems = acq.check_plan(ctx.root)
            _print({"ok": not problems, "problems": problems})
            return 1 if problems else 0
        if a.op == "prospects":
            _print(acq.prospects(ctx, a.product) if a.product else
                   {s: acq.prospects(ctx, s) for s in acq.active(acq.load_plan(ctx.root))})
        elif a.op == "report":
            print(acq.report(ctx, Path(a.events) if a.events else None,
                             _date.fromisoformat(a.date) if a.date else None))
        elif a.op == "seed":
            _print(acq.desk_docs(ctx, Path(a.events) if a.events else None))
        elif a.op == "docs":
            _print([str(x) for x in acq.write_docs(ctx.root)])
        return 0

    if a.cmd == "status":
        from .products.profile import list_profiles, load_profile
        _print({"dry_run": ctx.settings["dry_run"], "live": ctx.settings["live"],
                "kill_switch": ctx.policy.kill_switch_active(),
                "within_operating_hours": ctx.policy.within_operating_hours(),
                "london_time": ctx.policy.london_now().isoformat(timespec="minutes"),
                "profiles": [load_profile(ctx.root, s).summary() for s in list_profiles(ctx.root)],
                "content": {r["status"]: r["n"] for r in ctx.store.q("SELECT status, COUNT(*) n FROM content GROUP BY status")}})
    elif a.cmd == "sync":
        from .workflows import run_sync
        _print(run_sync(ctx, a.product))
    elif a.cmd == "plan":
        from .workflows import run_planner
        _print(run_planner(ctx, force=a.force))
    elif a.cmd == "produce":
        from .workflows import run_production
        _print(run_production(ctx))
    elif a.cmd == "calendar":
        from datetime import date
        from .marketing.calendar import build_calendar, render_markdown
        cal = build_calendar(ctx, date.fromisoformat(a.start) if a.start else None, a.weeks)
        print(render_markdown(cal))
    elif a.cmd == "campaign":
        from .creative.pipeline import produce_campaign
        r = produce_campaign(ctx, a.product, a.objective, a.formats.split(","), narration=not a.no_narration,
                             capture=not a.no_screenshots, force=a.force)
        _print(r.__dict__)
    elif a.cmd == "film":
        from .creative.motion.film import render_film
        r = render_film(ctx, a.product, a.formats.split(","), a.fps, capture=not a.no_screenshots)
        _print(r.__dict__)
    elif a.cmd == "profile":
        from .products.profile import load_profile
        p = load_profile(ctx.root, a.product)
        _print(p.summary() | {"facts": [{"id": f.id, "kind": f.kind, "status": f.status, "text": f.text,
                                         "problems": f.problems} for f in p.facts]})
    elif a.cmd == "approve-profile":
        from .workflows import approve_profile
        _print(approve_profile(ctx, a.product, a.by))
    elif a.cmd == "content":
        rows = ctx.store.q("SELECT id, product, platform, kind, status, created_at FROM content"
                           + (" WHERE status=?" if a.status else "") + " ORDER BY created_at DESC LIMIT 50",
                           (a.status,) if a.status else ())
        _print([dict(r) for r in rows])
    elif a.cmd == "show":
        _print(ctx.store.get_content(a.content_id))
    elif a.cmd == "approve":
        from .workflows import approve_content
        _print(approve_content(ctx, a.content_id, a.by))
    elif a.cmd == "cancel":
        ctx.store.set_content_status(a.content_id, "cancelled")
        _print({"content_id": a.content_id, "status": "cancelled"})
    elif a.cmd == "publish":
        from .workflows import run_publishing
        _print(run_publishing(ctx))
    elif a.cmd == "leads-import":
        from .lead_generation.leads import import_csv
        icp = json.loads((ctx.root / "config" / "icp.json").read_text()).get(a.product)
        _print(import_csv(ctx.store, a.product, Path(a.csv), icp))
    elif a.cmd == "leads":
        rows = ctx.store.q("SELECT id, product, company, score, status, created_at FROM leads"
                           + (" WHERE product=?" if a.product else "") + " ORDER BY score DESC",
                           (a.product,) if a.product else ())
        _print([dict(r) for r in rows])
    elif a.cmd == "suppress":
        from .lead_generation.leads import suppress
        suppress(ctx.store, a.key, a.reason)
        _print({"suppressed": a.key})
    elif a.cmd == "outreach-prepare":
        from .outreach.drafts import prepare
        _print(prepare(ctx, a.lead_id, a.channel, a.consent))
    elif a.cmd == "report":
        from .analytics.report import build
        text, path = build(ctx)
        print(text)
        print(f"(saved to {path})")
    elif a.cmd == "ops":
        from . import ops
        _print(ops.morning(ctx, Path(a.decisions) if a.decisions else None) if a.run == "morning" else ops.evening(ctx))
    elif a.cmd == "state":
        from . import ops
        _print(str(ops.export_state(ctx)) if a.op == "export" else ops.import_state(ctx))
    elif a.cmd == "desk":
        from . import ops
        if a.op == "queue":
            web = ctx.settings.data.get("media", {}).get("repo_web")
            _print(ops.desk_queue(ctx, web))
        else:
            _print(ops.apply_decisions(ctx, json.loads(Path(a.file).read_text())))
    elif a.cmd == "tick":
        from .scheduler import tick
        _print(tick(ctx))
    elif a.cmd == "kill-switch":
        if a.state == "on":
            ctx.policy.engage_kill_switch(a.reason)
        else:
            ctx.policy.release_kill_switch()
        _print({"kill_switch": ctx.policy.kill_switch_active()})
    return 0


if __name__ == "__main__":
    sys.exit(main())
