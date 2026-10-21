"""Outreach drafts — draft-only. Personalisation is limited to verifiable research
(company name + the recorded qualification reason with its source). No invented
familiarity, no fake 'I loved your post', no claims beyond verified product facts.
"""
from __future__ import annotations

import json

from ..company import company, email_footer
from ..context import Context
from ..lead_generation.leads import get_lead
from ..marketing.validator import validate
from ..marketing.writer import cta_line
from ..policy import Action
from ..products.profile import load_profile
from ..store import new_id, now_iso
from .eligibility import assess, load_outreach_config


def prepare(ctx: Context, lead_id: str, channel: str = "email", consent_record: str | None = None) -> dict:
    found = get_lead(ctx.store, lead_id)
    if not found:
        raise KeyError(lead_id)
    lead, meta = found
    product = meta["product"]
    cfg = load_outreach_config(ctx.root)
    decision = assess(ctx.store, cfg, product, lead, channel, consent_record)

    existing = ctx.store.conn.execute("SELECT id, draft FROM outreach WHERE lead_id=? AND product=? AND channel=?",
                                      (lead_id, product, channel)).fetchone()
    from .history import already_contacted
    if channel == "email" and already_contacted(ctx, product, lead.contact_email, lead.website):
        decision.status, decision.reasons, decision.rules = ("blocked", decision.reasons +
            ["already emailed (contact history): a first email would be a duplicate; follow up in the existing thread"],
            decision.rules + ["ALREADY_CONTACTED"])
        decision.lead_status = "blocked"
    oid = existing["id"] if existing else new_id("out")

    draft_text, status = None, decision.status if decision.status != "eligible" else "draft"
    # Draft whenever the lead itself passes (or needs review), even if a sender gate blocks sending:
    # a blocked item can never be approved or sent (sender.approve / sender.send re-check).
    if decision.status in ("eligible", "manual_review") or decision.lead_status in ("eligible", "manual_review"):
        if ctx.policy.authorize(Action.DRAFT_OUTREACH, "local_render", detail={"lead": lead_id}).allowed:
            draft_text, evidence = _compose(ctx, product, lead, cfg, channel)
            decision.reasons = decision.reasons + [f"evidence: facts {', '.join(evidence['fact_ids'])}; "
                                                   f"reason from {evidence['source_url']}"]
        else:   # keep any draft already written; a refused re-draft must not destroy earlier work
            draft_text = existing["draft"] if existing else None
            status, decision.reasons = "blocked", decision.reasons + ["draft limit / kill switch"]
    with ctx.store.tx() as c:
        c.execute("INSERT INTO outreach(id, lead_id, product, channel, status, decision, draft, created_at)"
                  " VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(lead_id, product, channel) DO UPDATE SET"
                  " status=excluded.status, decision=excluded.decision, draft=excluded.draft",
                  (oid, lead_id, product, channel, status, json.dumps(decision.as_dict()), draft_text, now_iso()))
    ctx.store.audit("eligibility", "outreach", "ok", f"{lead_id}: {decision.status}",
                    {"lead": lead_id, "rules": decision.rules})
    return {"outreach_id": oid, "status": status, "decision": decision.as_dict(), "draft": draft_text}


def _second_person(reason: str) -> str:
    """Research notes say 'its website…'; a letter to the organisation says 'your website…'."""
    return "your " + reason[4:] if reason.lower().startswith("its ") else reason


def _email_plan(ctx: Context, product: str) -> dict:
    """Per-brand email shape from the acquisition plan: subject, cited facts and the ask (a phone call)."""
    from ..acquisition import load_plan
    plan = load_plan(ctx.root) or {}
    return plan.get("products", {}).get(product, {}).get("email") or {}


def _compose(ctx: Context, product: str, lead, cfg: dict, channel: str = "email") -> tuple[str, dict]:
    prof = load_profile(ctx.root, product)
    ep = _email_plan(ctx, product)
    if ep.get("fact_ids"):
        used = [f for f in (prof.fact(i) for i in ep["fact_ids"]) if f and f.usable]
    else:
        used = prof.by_kind("pain_point")[:1] + prof.by_kind("feature")[:2]
    cta, cta_ids = (ep["ask"], []) if ep.get("ask") else cta_line(prof)
    addressee = cfg["products"].get(product, {}).get("post_addressee", "The Manager")
    subject = (ep.get("subject") or f"{prof.name} for {{org}}").format(org=lead.company)
    opening = ([f"Subject: {subject}", "", "Hello,"] if channel == "email"
               else [f"To: {addressee}, {lead.company}", "[REGISTERED ADDRESS — from the public register]", "",
                     f"Dear {addressee.removeprefix('The ').lower()},"])
    facts = [f.text for f in used]
    body = [*opening, "", f"I'm getting in touch because {_second_person(lead.qualification_reason.rstrip('.'))}.", ""]
    body += ([facts[0], "", " ".join(facts[1:]), ""] if ep.get("fact_ids") else
             [*([facts[0], ""] if facts else []), f"{prof.name} may help:", *[f"- {t}" for t in facts[1:]], ""])
    body += [cta, ""]
    if (ctx.root / "config" / "company.json").exists() and product in company(ctx.root)["brands"]:
        body += [email_footer(ctx.root, product)]
    else:                                                    # legacy: sender block from outreach.json
        s = cfg["sender"]
        body += ["If this isn't relevant, reply and I won't contact you again.", "",
                 f"{s.get('legal_name') or '[SENDER LEGAL NAME]'}, {s.get('postal_address') or '[POSTAL ADDRESS]'}",
                 f"{s.get('opt_out_instructions') or '[OPT-OUT INSTRUCTIONS]'}"]
    text = "\n".join(body)
    v = validate("\n".join(facts) + "\n" + cta, product=prof, platform="email",
                 fact_ids=[f.id for f in used] + cta_ids, require_cta=False)
    if not v.ok:
        text = "[VALIDATION FAILED — do not send]\n" + "\n".join(v.errors) + "\n\n" + text
    return text, {"fact_ids": [f.id for f in used] + cta_ids, "reason": lead.qualification_reason,
                  "source_url": lead.source_url}
