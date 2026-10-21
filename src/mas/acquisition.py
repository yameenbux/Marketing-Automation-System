"""Customer acquisition: the 30-day plan in `config/acquisition.json`, prospects with permitted contact
methods, and a pipeline report that ranks outcomes (conversations, demos, pilots, paying) above output.

Pipeline events are logged by the owner in the approval desk (one event = one organisation reaching a
stage, with its source). They are read here from a JSON export (default `var/pipeline/events.json`,
gitignored): organisation names are business data and never go into this public repository.
Nothing in this module contacts anyone or publishes anything.
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from .context import Context
from .lead_generation.leads import get_lead
from .marketing.validator import validate
from .products.profile import load_profile

EVIDENCE = ("supports", "contradicts")
# MasjidOne's top channels are referral and in-person visits, so distance from Bolton outweighs an emailable address.
NEAR = {"bolton": 40, "blackburn": 15, "manchester": 15, "oldham": 15, "rochdale": 15, "preston": 15,
        "burnley": 15, "ashton": 15, "tameside": 15}


# --- plan ---------------------------------------------------------------------------------
def load_plan(root: Path) -> dict | None:
    """The committed plan, plus dated commitments to named prospects from var/pipeline/commitments.json
    ({slug: [{date, item}]}). Those name real organisations, so they stay in the gitignored var/ folder."""
    p = root / "config" / "acquisition.json"
    if not p.exists():
        return None
    plan = json.loads(p.read_text(encoding="utf-8"))
    cp = root / "var" / "pipeline" / "commitments.json"
    for slug, items in (json.loads(cp.read_text(encoding="utf-8")) if cp.exists() else {}).items():
        if slug in plan["products"]:
            plan["products"][slug]["commitments"] = plan["products"][slug].get("commitments", []) + items
    return plan


def active(plan: dict | None) -> list[str]:
    if not plan:
        return []
    items = [(v.get("priority", 99), k) for k, v in plan["products"].items() if v.get("mode") == "active"]
    return [k for _, k in sorted(items)]


def content_gate(root: Path) -> dict | None:
    """Per active product: {post_days, post_time, hypothesis}. None when no plan exists (legacy behaviour).
    Products that aren't active, or have no post days, get no content at all."""
    plan = load_plan(root)
    if plan is None:
        return None
    return {s: plan["products"][s]["content"] for s in active(plan) if plan["products"][s]["content"].get("post_days")}


def check_plan(root: Path) -> list[str]:
    """Everything the plan claims must trace to verified facts and pass the validator."""
    plan, problems = load_plan(root), []
    if plan is None:
        return ["config/acquisition.json missing"]
    for slug in active(plan):
        p, prof = plan["products"][slug], load_profile(root, slug)
        for fid in p["value_proposition"]["fact_ids"] + p["icp"].get("evidence_fact_ids", []):
            f = prof.fact(fid)
            if f is None or f.status != "verified":
                problems.append(f"{slug}: cites {fid}, which is {'missing' if f is None else f.status}")
        for m in p.get("messages", []):
            r = validate(m["text"], product=prof, platform=m["platform"], fact_ids=m["fact_ids"])
            problems += [f"{slug}/{m['id']}: {e}" for e in r.errors]
        for stage, row in p["targets"].items():
            if stage not in p["stages"]:
                problems.append(f"{slug}: target for unknown stage {stage}")
            if len(row) != 4:
                problems.append(f"{slug}: {stage} needs 4 weekly targets")
        for c in p["channels"]:
            if c["source"] not in plan["sources"]:
                problems.append(f"{slug}: unknown source {c['source']}")
    return problems


def plan_week(plan: dict, d: date) -> int:
    """1-based week of the plan (1–4 carry targets; the last days of a 30-day plan are week 5)."""
    start = date.fromisoformat(plan["start"])
    return max(1, (d - start).days // 7 + 1)


# --- prospects ----------------------------------------------------------------------------
def _methods(plan: dict, slug: str, lead, outreach: dict[str, dict], allowed: list[str]) -> list[dict]:
    """Permitted contact methods for one prospect, in the plan's channel order."""
    out = []
    for ch in sorted(plan["products"][slug]["channels"], key=lambda c: c["priority"]):
        src = ch["source"]
        if src == "email":
            d = outreach.get("email")
            verdict = (d or {}).get("lead_status") or (d or {}).get("status")
            rules = [r for r in (d or {}).get("rules", []) if r != "SENDER_ID"]
            if verdict == "eligible":
                st = "allowed once sender identity is set" if "SENDER_ID" in (d or {}).get("rules", []) else "allowed"
            elif verdict == "manual_review":
                st = "manual review first (" + ", ".join(rules) + ")"
            else:
                st = "not permitted (" + (", ".join(rules) or "not assessed") + ")"
            out.append({"method": "email", "status": st})
        elif src == "post":
            if "post" in allowed:
                out.append({"method": "post", "status": "allowed: letter to the committee or practice at its registered address"})
        elif src == "phone":
            out.append({"method": "phone", "status": "allowed after a TPS/CTPS check"})
        elif src == "in_person":
            out.append({"method": "in_person", "status": "allowed"})
        elif src == "referral":
            out.append({"method": "referral", "status": "ask an existing contact for an introduction"})
        elif src == "linkedin_manual":
            out.append({"method": "linkedin_manual", "status": "allowed if written and sent by you (no automation)"})
    return out


def prospects(ctx: Context, slug: str) -> list[dict]:
    """Prioritised prospect list from the lead database (organisations only; no personal contacts)."""
    plan = load_plan(ctx.root)
    if not plan or slug not in active(plan):
        return []
    ocfg = ctx.root / "config" / "outreach.json"           # missing policy -> no automated channel is allowed
    allowed = json.loads(ocfg.read_text())["products"].get(slug, {}).get("allowed_channels", []) if ocfg.exists() else []
    rows = []
    for r in ctx.store.q("SELECT id FROM leads WHERE product=? AND status!='suppressed'", (slug,)):
        lead, meta = get_lead(ctx.store, r["id"])
        decisions = {o["channel"]: json.loads(o["decision"]) for o in ctx.store.q(
            "SELECT channel, decision FROM outreach WHERE lead_id=?", (r["id"],))}
        methods = _methods(plan, slug, lead, decisions, allowed)
        region = (lead.region or "").lower()
        bonus = max([v for k, v in NEAR.items() if k in region] or [0]) if slug == "masjidone" else 0
        bonus += 10 if "multi_clinician" in lead.signals else 0
        bonus += 10 if any(m["method"] == "email" and m["status"].startswith("allowed") for m in methods) else 0
        rows.append({"id": r["id"], "product": slug, "org": lead.company, "region": lead.region,
                     "subscriber_type": lead.subscriber_type, "score": meta["score"],
                     "priority": round((meta["score"] or 0) + bonus, 1), "reason": lead.qualification_reason,
                     "source_url": lead.source_url, "research_date": lead.research_date, "methods": methods})
    rows.sort(key=lambda x: -x["priority"])
    for i, row in enumerate(rows, 1):
        row["rank"] = i
    return rows


# --- pipeline -----------------------------------------------------------------------------
def load_events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else data.get("events", [])


def clean_events(plan: dict, events: list[dict]) -> tuple[list[dict], list[str]]:
    ok, bad = [], []
    for i, e in enumerate(events):
        p = plan["products"].get(e.get("product"))
        try:
            d = date.fromisoformat(str(e.get("date", ""))[:10])
        except ValueError:
            bad.append(f"event {i}: bad date {e.get('date')!r}")
            continue
        if not p or p.get("mode") != "active":
            bad.append(f"event {i}: unknown or inactive product {e.get('product')!r}")
        elif e.get("stage") not in p["stages"]:
            bad.append(f"event {i}: unknown stage {e.get('stage')!r} for {e['product']}")
        elif e.get("source") not in plan["sources"]:
            bad.append(f"event {i}: unknown source {e.get('source')!r}")
        elif e.get("evidence") and e["evidence"] not in EVIDENCE:
            bad.append(f"event {i}: evidence must be one of {EVIDENCE}")
        else:
            ok.append(e | {"_date": d, "_count": max(1, int(e.get("count") or 1))})
    return ok, bad


def funnel(plan: dict, events: list[dict], today: date) -> dict:
    wk = plan_week(plan, today)
    start = date.fromisoformat(plan["start"])
    w_from = start + timedelta(days=7 * (wk - 1))
    out = {}
    for slug in active(plan):
        p, ev = plan["products"][slug], [e for e in events if e["product"] == slug]
        rows = []
        for stage, label in p["stages"].items():
            tgt = p["targets"].get(stage, [0, 0, 0, 0])
            week_t = tgt[wk - 1] if wk <= 4 else 0
            cum_t = sum(tgt[:min(wk, 4)])
            week_a = sum(e["_count"] for e in ev if e["stage"] == stage and w_from <= e["_date"] <= today)
            cum_a = sum(e["_count"] for e in ev if e["stage"] == stage and e["_date"] <= today)
            rows.append({"stage": stage, "label": label, "week_actual": week_a, "week_target": week_t,
                         "total_actual": cum_a, "total_target": cum_t})
        out[slug] = rows
    return {"week": wk, "from": w_from.isoformat(), "to": today.isoformat(), "products": out}


def sources(plan: dict, events: list[dict]) -> dict:
    """First-touch attribution: each organisation is credited to the source of its earliest event."""
    out = {}
    for slug in active(plan):
        stages = list(plan["products"][slug]["stages"])
        orgs: dict[str, dict] = {}
        for e in sorted((e for e in events if e["product"] == slug and e.get("org")), key=lambda e: e["_date"]):
            o = orgs.setdefault(e["org"].strip().lower(), {"source": e["source"], "stages": set()})
            o["stages"].add(e["stage"])
        table: dict[str, dict] = defaultdict(lambda: {s: 0 for s in stages} | {"orgs": 0})
        for o in orgs.values():
            row = table[o["source"]]
            row["orgs"] += 1
            for s in o["stages"]:
                row[s] += 1
        out[slug] = dict(table)
    return out


def hypotheses(plan: dict, events: list[dict]) -> dict:
    out = {}
    for slug in active(plan):
        rows = []
        for a in plan["products"][slug]["assumptions"]:
            ev = [e for e in events if e.get("hypothesis") == a["id"] and e.get("evidence")]
            yes = sum(1 for e in ev if e["evidence"] == "supports")
            n = len(ev)
            if n < a["min_sample"]:
                status = f"testing ({n}/{a['min_sample']})" if n else "untested"
            else:
                status = "supported" if yes / n >= a["success_ratio"] else "contradicted"
            rows.append({"id": a["id"], "risk": a["risk"], "statement": a["statement"], "supports": yes,
                         "contradicts": n - yes, "status": status, "if_contradicted": a["if_contradicted"]})
        out[slug] = rows
    return out


def _urgent(p: dict, blocks: str, wk: int) -> bool:
    """A prerequisite is urgent if what it blocks is needed this week or next."""
    if blocks in p["targets"]:
        return any(p["targets"][blocks][i] for i in range(min(wk, 4) - 1, min(wk + 1, 4)))
    return any(c["source"] == blocks and c["priority"] <= 3 for c in p["channels"])


def next_actions(plan: dict, events: list[dict], today: date, email: dict | None = None) -> list[dict]:
    """Ranked actions for the owner: what unblocks this week, then this week's shortfalls, then evidence,
    then blockers for later weeks. Higher-priority products first within each band."""
    acts: list[tuple[float, dict]] = []
    f, src, hyp = funnel(plan, events, today), sources(plan, events), hypotheses(plan, events)
    wk = f["week"]
    if not events:
        acts.append((0, {"product": "all", "who": "you", "action": "Log every conversation in the desk ('Log a conversation' tab) "
                         "with its source. Without that log nothing below can be measured."}))
    for slug in active(plan):
        p = plan["products"][slug]
        pr = p.get("priority", 9) / 10
        for cm in p.get("commitments", []):                      # dated promises to real prospects come first
            due = date.fromisoformat(cm["date"])
            if today <= due <= today + timedelta(days=7):
                acts.append((0.5 + pr, {"product": slug, "who": "you", "action": f"By {cm['date']}: {cm['item']}"}))
        for pre in p.get("prerequisites", []):
            if not pre.get("done"):
                band = 1 if _urgent(p, pre["blocks"], wk) else 4
                acts.append((band + pr, {"product": slug, "who": pre.get("owner", "you"),
                                         "action": f"Unblock {pre['blocks']}: {pre['item']}"}))
        gaps = [(r["week_target"] - r["week_actual"], r) for r in f["products"][slug] if r["week_target"]]
        gaps = [g for g in gaps if g[0] > 0]
        if gaps:
            short, row = max(gaps, key=lambda g: g[0] / max(1, g[1]["week_target"]))
            best = _best_source(src[slug], p)
            acts.append((2 + pr, {"product": slug, "who": "you", "action": f"{short} more '{row['stage']}' needed this "
                                  f"week ({row['week_actual']}/{row['week_target']}). Best channel so far: {best}."}))
        for source, row in src[slug].items():
            first_reply = list(p["stages"])[1]
            if row["orgs"] >= 5 and row[first_reply] == 0:
                acts.append((3 + pr, {"product": slug, "who": "you", "action": f"Pause '{source}': {row['orgs']} "
                                      f"contacted, no '{first_reply}' yet. Move that time to the best channel."}))
        for h in hyp[slug]:
            if h["status"] == "contradicted":
                acts.append((3 + pr, {"product": slug, "who": "you",
                                      "action": f"{h['id']} contradicted: {h['if_contradicted']}"}))
    for slug, st in (email or {}).items():
        if slug in plan["products"] and st["organisations_emailed"] >= 30 and (st["days_since_first"] or 0) >= 7 \
                and (st["reply_rate"] or 0) < 0.02:
            acts.append((1.5 + plan["products"][slug].get("priority", 9) / 10, {"product": slug, "who": "you", "action":
                f"Cold email isn't working: {st['replied']} replies from {st['organisations_emailed']} organisations in "
                f"{st['days_since_first']} days. Stop new cold emails; phone the best-fit ones instead, starting with "
                f"the segment the product is built for."}))
    return [a for _, a in sorted(acts, key=lambda x: x[0])]


def _best_source(table: dict, p: dict) -> str:
    stages = list(p["stages"])
    reply = stages[1]
    ranked = sorted(((row[reply] / row["orgs"], s) for s, row in table.items() if row["orgs"] >= 3), reverse=True)
    if ranked and ranked[0][0] > 0:
        rate, s = ranked[0]
        return f"{s} ({rate:.0%} reach '{reply}')"
    first = min(p["channels"], key=lambda c: c["priority"])
    return f"not enough data; start with {first['source']} (plan priority 1)"


def _pct(x: float | None) -> str:
    return "—" if x is None else f"{x:.0%}"


def report_markdown(plan: dict, events: list[dict], bad: list[str], today: date, short: bool = False,
                    email: dict | None = None) -> str:
    f, src, hyp = funnel(plan, events, today), sources(plan, events), hypotheses(plan, events)
    acts = next_actions(plan, events, today, email)
    start = date.fromisoformat(plan["start"])
    when = (f"starts {start.isoformat()}; showing week 1 targets" if today < start
            else f"week {f['week']} ({f['from']} → {f['to']})")
    L = [f"## Customer acquisition — {when}", ""]
    L += ["**Next actions**"] + [f"{i}. [{a['product']}] {a['action']}" for i, a in enumerate(acts[:8 if short else 50], 1)] + [""]
    for slug in active(plan):
        L += [f"### {slug}", "| Stage | This week | Target | Total | Target to date |", "|---|---|---|---|---|"]
        L += [f"| {r['stage']} | {r['week_actual']} | {r['week_target']} | {r['total_actual']} | {r['total_target']} |"
              for r in f["products"][slug]]
        if src[slug]:
            stages = list(plan["products"][slug]["stages"])
            L += ["", "Source (first touch) → organisations reaching each stage:", "",
                  "| Source | Orgs | " + " | ".join(stages[1:]) + " |", "|---" * (len(stages) + 1) + "|"]
            L += [f"| {s} | {row['orgs']} | " + " | ".join(str(row[x]) for x in stages[1:]) + " |" for s, row in src[slug].items()]
        if not short:
            L += ["", "Assumptions:"] + [f"- **{h['id']}** ({h['risk']}) {h['status']}: {h['statement']}" for h in hyp[slug]]
        L += [""]
    if email:
        L += ["**Email outreach (from Gmail, all senders)**", "", "| Brand | Organisations emailed | Follow-ups | Replied |"
              " Reply rate | Opted out | Bounced | Since |", "|---|---|---|---|---|---|---|---|"]
        L += [f"| {k} | {v['organisations_emailed']} | {v['follow_ups']} | {v['replied']} | "
              f"{_pct(v['reply_rate'])} | "
              f"{v['opted_out']} | {v['bounced']} | {v['first_sent']} |" for k, v in email.items()] + [""]
    working = [f"{slug}: {h['id']} supported" for slug in hyp for h in hyp[slug] if h["status"] == "supported"]
    working += [f"{slug}: '{s}' reaches conversations" for slug in src for s, row in src[slug].items()
                if row["orgs"] >= 3 and row[list(plan['products'][slug]['stages'])[1]] / row["orgs"] >= 0.3]
    failing = [f"{slug}: {h['id']} contradicted" for slug in hyp for h in hyp[slug] if h["status"] == "contradicted"]
    failing += [f"{slug}: {r['stage']} at {r['total_actual']} of {r['total_target']} to date" for slug in f["products"]
                for r in f["products"][slug] if r["total_target"] and r["total_actual"] < 0.5 * r["total_target"]]
    L += ["**Working:** " + ("; ".join(working) or "nothing proven yet"), "",
          "**Not working:** " + ("; ".join(failing) or "nothing below half of target yet"), ""]
    if bad:
        L += ["**Log entries ignored (fix them in the desk):**"] + [f"- {b}" for b in bad] + [""]
    return "\n".join(L) + "\n"


def report(ctx: Context, events_path: Path | None = None, today: date | None = None, short: bool = False) -> str:
    plan = load_plan(ctx.root)
    if not plan:
        return ""
    events, bad = clean_events(plan, load_events(events_path or ctx.root / "var" / "pipeline" / "events.json"))
    from .outreach.history import stats as email_stats
    return report_markdown(plan, events, bad, today or ctx.policy.london_now().date(), short=short, email=email_stats(ctx))


# --- per-product plan documents -------------------------------------------------------------
def render_doc(root: Path, slug: str) -> str:
    plan = load_plan(root)
    p, prof = plan["products"][slug], load_profile(root, slug)
    fact = lambda fid: (prof.fact(fid).text if prof.fact(fid) else f"[missing {fid}]")  # noqa: E731
    start = date.fromisoformat(plan["start"])
    L = [f"# {prof.name}: 30-day acquisition plan", "",
         f"Priority {p['priority']} · {start.isoformat()} to {(start + timedelta(days=plan['days'] - 1)).isoformat()} · "
         "generated from `config/acquisition.json` by `mas acq docs` (edit the config, not this file).", "",
         "## Ideal customer", f"- **Who:** {p['icp']['who']}", f"- **Where:** {p['icp']['where']}",
         f"- **Buyer:** {p['icp']['buyer']}", "- **Disqualify:** " + "; ".join(p["icp"]["disqualify"]), "",
         "## Value proposition", f"> {p['value_proposition']['headline']}", "", "Evidence (verified facts):"]
    L += [f"- `{fid}`: {fact(fid)}" for fid in p["value_proposition"]["fact_ids"]]
    L += ["", "Don't lead with: " + "; ".join(p["value_proposition"]["do_not_lead_with"]), "",
          "## Biggest unresolved assumptions", "| ID | Risk | Assumption | How we test it | Decision rule |",
          "|---|---|---|---|---|"]
    L += [f"| {a['id']} | {a['risk']} | {a['statement']} | {a['test']} | Needs {a['min_sample']} answers; "
          f"≥{a['success_ratio']:.0%} supporting. If not: {a['if_contradicted']} |" for a in p["assumptions"]]
    L += ["", "## Prerequisites (yours)"] + [f"- [{'x' if x.get('done') else ' '}] **{x['id']}** blocks *{x['blocks']}*: {x['item']}"
                                            for x in p["prerequisites"]]
    L += ["", "## Channels, in order", "| # | Source | Who acts | How | Compliance |", "|---|---|---|---|---|"]
    L += [f"| {c['priority']} | {c['source']} | {c['who_acts']} | {c['how']} | {c['compliance']} |"
          for c in sorted(p["channels"], key=lambda c: c["priority"])]
    L += ["", "The prioritised prospect list (organisations, sources, qualification reasons and permitted contact "
          "methods per organisation) is in the approval desk's Pipeline tab and `mas acq prospects " + slug + "`. "
          "It is not stored in this repository.", "",
          "## Weekly targets", "| Stage | Definition | W1 | W2 | W3 | W4 |", "|---|---|---|---|---|---|"]
    L += [f"| {s} | {p['stages'][s]} | " + " | ".join(str(x) for x in p["targets"].get(s, [0] * 4)) + " |" for s in p["stages"]]
    L += ["", p.get("targets_note", ""), "", "## Messages (each passes the claim validator)"]
    for m in p["messages"]:
        L += [f"**{m['id']}** — {m['use']} (facts: {', '.join(m['fact_ids'])})", "", f"> {m['text']}", ""]
    L += ["## Discovery questions"] + [f"{i}. {q}" for i, q in enumerate(p["discovery_questions"], 1)]
    L += ["", "## Demo", "Assets: " + "; ".join(p["demo"]["assets"]), ""] + [f"{i}. {s}" for i, s in enumerate(p["demo"]["flow"], 1)]
    L += ["", "Never show: " + "; ".join(p["demo"]["never_show"]), "", "## Pilot offer", p["pilot_offer"], "",
          "## Content", f"Post days: {p['content']['post_days'] or 'none'} · hypothesis: {p['content']['hypothesis'] or '—'}. "
          + p["content"]["why"], ""]
    return "\n".join(L)


def write_docs(root: Path) -> list[Path]:
    plan, out = load_plan(root), []
    d = root / "docs" / "acquisition"
    d.mkdir(parents=True, exist_ok=True)
    for slug in active(plan):
        path = d / f"{slug}.md"
        path.write_text(render_doc(root, slug), encoding="utf-8")
        out.append(path)
    return out


# --- approval desk (shared database) -------------------------------------------------------------
def desk_docs(ctx: Context, events_path: Path | None = None, today: date | None = None) -> list[dict]:
    """Documents for the desk's plan / prospects / report collections, as ArtifactData batch writes."""
    plan = load_plan(ctx.root)
    if not plan:
        return []
    out = []
    for slug in active(plan):
        p, prof = plan["products"][slug], load_profile(ctx.root, slug)
        doc = {"slug": slug, "name": prof.name, "priority": p["priority"], "start": plan["start"], "sources": plan["sources"],
               "stages": p["stages"], "targets": p["targets"], "value_headline": p["value_proposition"]["headline"],
               "assumptions": [{k: a[k] for k in ("id", "risk", "statement", "min_sample", "success_ratio")} for a in p["assumptions"]],
               "channels": [{k: c[k] for k in ("source", "priority", "how", "compliance")} for c in p["channels"]],
               "prerequisites": p["prerequisites"]}
        out.append({"collection": "plan", "doc_id": slug, "data": doc})
        out += [{"collection": "prospects", "doc_id": r["id"], "data": r} for r in prospects(ctx, slug)]
    events, _ = clean_events(plan, load_events(events_path or ctx.root / "var" / "pipeline" / "events.json"))
    from .outreach.history import stats as email_stats
    acts = next_actions(plan, events, today or ctx.policy.london_now().date(), email_stats(ctx))
    out.append({"collection": "report", "doc_id": "latest",
                "data": {"generated_at": ctx.policy.london_now().isoformat(timespec="minutes"), "actions": acts[:12]}})
    return out
