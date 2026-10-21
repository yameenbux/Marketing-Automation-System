"""Workflow G — daily report (16:30). Built only from the store and audit log, so it reports what
actually happened, not what was intended."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from ..context import Context
from ..products.profile import list_profiles, load_profile


def build(ctx: Context) -> tuple[str, Path]:
    s, pol = ctx.store, ctx.policy
    day = pol.start_of_london_day_utc()
    month = pol.start_of_london_month_utc()
    today = pol.london_now().date().isoformat()

    runs = s.q("SELECT workflow, status, summary FROM runs WHERE started_at>=? ORDER BY started_at", (day,))
    content = Counter(r["status"] for r in s.q("SELECT status FROM content"))
    new_content = s.q("SELECT id, product, platform, status FROM content WHERE created_at>=?", (day,))
    awaiting = s.q("SELECT id, product, platform FROM content WHERE status='validated' ORDER BY created_at")
    rejected = s.q("SELECT id, product, validation FROM content WHERE status='rejected' AND updated_at>=?", (day,))
    pubs = s.q("SELECT content_id, destination, status, scheduled_for FROM publications WHERE ts>=?", (day,))
    camps = s.q("SELECT id, product, data FROM campaigns WHERE created_at>=?", (day,))
    leads = Counter(r["status"] for r in s.q("SELECT status FROM leads WHERE created_at>=?", (day,)))
    outreach = Counter(r["status"] for r in s.q("SELECT status FROM outreach WHERE created_at>=?", (day,)))
    blocked = s.q("SELECT action, integration, reason, COUNT(*) n FROM audit WHERE ts>=? AND outcome='blocked' "
                  "GROUP BY action, integration, reason ORDER BY n DESC", (day,))
    errors = s.q("SELECT action, integration, reason FROM audit WHERE ts>=? AND outcome='error'", (day,))
    flags = s.q("SELECT reason FROM audit WHERE ts>=? AND action='secret_exposure_flag'", (day,))
    spend = s.spend_since(month)

    L = [f"# Daily report — {today}", ""]
    status = "🛑 KILL SWITCH ACTIVE" if pol.kill_switch_active() else ("dry-run" if ctx.settings["dry_run"] else "LIVE")
    L += [f"**Mode:** {status} · live publishing: {ctx.settings['live']['publishing']} · "
          f"live outreach: {ctx.settings['live']['outreach_sending']}", ""]

    from ..acquisition import report as acquisition_report
    acq = acquisition_report(ctx, short=True)               # outcomes first: conversations, demos, pilots, paying
    if acq:
        L += [acq.rstrip(), "", "---", "", "*Production detail below is secondary: it only matters if it moves the numbers above.*", ""]

    L += ["## Workflows run today"] + ([f"- {r['workflow']}: **{r['status']}**" for r in runs] or ["- none"]) + [""]

    L += ["## Content", f"- Totals by status: {dict(content) or 'none'}",
          f"- Created today: {len(new_content)}"]
    L += [f"  - `{r['id']}` {r['product']}/{r['platform']} → {r['status']}" for r in new_content[:20]]
    if rejected:
        L += ["- Rejected by validation today:"]
        L += [f"  - `{r['id']}` {r['product']}: {json.loads(r['validation']).get('errors', [])[:2]}" for r in rejected]
    L += [""]

    L += ["## Creative assets"]
    for c in camps:
        path = Path(json.loads(c["data"]).get("path", ""))
        man = path / "manifest.json"
        qc = json.loads(man.read_text()).get("qc_ok") if man.exists() else None
        L.append(f"- `{c['id']}` ({c['product']}) — QC {'passed' if qc else 'FAILED/unknown'} — `{path}`")
    L += (["- none today"] if not camps else []) + [""]

    L += ["## Publishing"] + ([f"- {p['destination']} `{p['content_id']}` → **{p['status']}** for {p['scheduled_for']}"
                              for p in pubs] or ["- nothing scheduled or simulated today"]) + [""]

    L += ["## Leads and outreach", f"- Leads added today: {dict(leads) or 'none'}",
          f"- Outreach decisions today: {dict(outreach) or 'none'}", "- Messages sent: 0 (no sending integration)", ""]

    L += ["## Blocked actions"] + ([f"- {b['n']}× {b['action']} via {b['integration']}: {b['reason']}" for b in blocked]
                                   or ["- none"]) + [""]
    if errors or flags:
        L += ["## ⚠️ Failures and alerts"] + [f"- {e['action']}/{e['integration']}: {e['reason']}" for e in errors]
        L += [f"- Possible secret exposure: {f['reason']}" for f in flags] + [""]

    L += ["## Awaiting your approval"]
    unapproved = [slug for slug in list_profiles(ctx.root) if not load_profile(ctx.root, slug).approved]
    if unapproved:
        L.append(f"- Product profiles (approve with `mas approve-profile <slug> --by <name>`): {', '.join(unapproved)}")
    L += [f"- Content `{r['id']}` ({r['product']}/{r['platform']}) — `mas approve {r['id']} --by <name>`" for r in awaiting[:15]]
    if not unapproved and not awaiting:
        L.append("- nothing")
    L += [""]

    budget = ctx.settings.limit("monthly_budget_gbp")
    L += ["## Costs", f"- Recorded spend this month: £{spend:.2f} of £{budget:.0f} budget",
          "- Local rendering, local TTS and the public GitHub sync cost £0. Claude/connector usage is not metered here.", ""]

    plan_path = ctx.root / "var" / "plans" / f"{today}.json"
    L += ["## Recommended next priorities"]
    if plan_path.exists():
        plan = json.loads(plan_path.read_text())
        for p in plan["products"][:4]:
            L.append(f"- **{p['slug']}** (readiness {p['readiness']}): {', '.join(p['actions'])}")
    else:
        L.append("- run the planner (`mas plan`)")
    text = "\n".join(L) + "\n"
    out = ctx.root / "var" / "reports" / f"{today}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return text, out
