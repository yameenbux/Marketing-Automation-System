"""Workflow F — outreach eligibility. Compliance enforced by code, failing closed.

This encodes a conservative reading of PECR (regs 21–22) and UK GDPR for
*unsolicited direct marketing*. It is a safety net, not legal advice. Any
uncertainty → manual_review; any error → blocked.

Key rules
- Electronic mail to INDIVIDUAL subscribers (individuals, sole traders, non-Scottish
  partnerships, unincorporated associations) needs prior consent. Soft opt-in
  can't apply to cold prospects (no previous sale/negotiation). → blocked without consent.
- CORPORATE subscribers (companies, LLPs, Scottish partnerships, public bodies) are
  outside reg 22, but a *named* employee's address is personal data → UK GDPR
  lawful basis needed: we require a documented LIA for that product.
- Every message must identify the sender and give a working opt-out (PECR reg 23,
  UK GDPR art. 21) → required config, else blocked.
- Phone (TPS/CTPS screening not implemented) and LinkedIn messaging (platform terms)
  are never automated → blocked.
- Suppressed / opted-out → blocked, always, first.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

from ..store import Store, now_iso
from ..lead_generation.leads import PERSONAL_WEBMAIL, Lead, email_domain, is_role_address, is_suppressed

INDIVIDUAL_SUBSCRIBERS = {"individual", "sole_trader", "partnership", "unincorporated"}
CORPORATE_SUBSCRIBERS = {"corporate", "scottish_partnership", "public_body"}


@dataclass
class Eligibility:
    status: str                       # eligible | manual_review | blocked
    reasons: list[str] = field(default_factory=list)
    rules: list[str] = field(default_factory=list)
    checked_at: str = field(default_factory=now_iso)

    def as_dict(self) -> dict:
        return asdict(self)


def load_outreach_config(root: Path) -> dict:
    return json.loads((root / "config" / "outreach.json").read_text(encoding="utf-8"))


def assess(store: Store, cfg: dict, product: str, lead: Lead, channel: str,
           consent_record: str | None = None, today: date | None = None) -> Eligibility:
    try:
        return _assess(store, cfg, product, lead, channel, consent_record, today or date.today())
    except Exception as e:  # noqa: BLE001 — fail closed on anything unexpected
        return Eligibility("blocked", [f"eligibility check could not complete: {e}"], ["FAIL_CLOSED"])


def _assess(store, cfg, product, lead: Lead, channel, consent, today) -> Eligibility:
    sup = is_suppressed(store, lead)
    if sup:
        return Eligibility("blocked", [f"on suppression list ({sup})"], ["SUPPRESSED"])

    pcfg = cfg.get("products", {}).get(product)
    if pcfg is None:
        return Eligibility("blocked", [f"no outreach policy for product {product}"], ["NO_POLICY"])
    if channel not in pcfg.get("allowed_channels", []):
        return Eligibility("blocked", [f"channel '{channel}' not allowed for {product}: {pcfg.get('note', '')}"],
                           ["CHANNEL_NOT_ALLOWED"])
    if channel == "phone":
        return Eligibility("blocked", ["phone marketing needs TPS/CTPS screening, which is not implemented"], ["PHONE"])
    if channel == "linkedin":
        return Eligibility("blocked", ["automated LinkedIn messaging breaches platform terms"], ["LINKEDIN"])
    if channel != "email":
        return Eligibility("blocked", [f"unsupported channel {channel}"], ["UNSUPPORTED"])

    reasons, rules = [], []
    sender = cfg.get("sender", {})
    missing = [k for k in ("legal_name", "postal_address", "reply_to", "opt_out_instructions") if not sender.get(k)]
    if missing:
        return Eligibility("blocked", [f"sender identification/opt-out not configured: {missing}"], ["SENDER_ID"])

    if not lead.contact_email:
        return Eligibility("blocked", ["no business email address on record"], ["NO_ADDRESS"])
    dom = email_domain(lead.contact_email)
    if dom is None or dom in PERSONAL_WEBMAIL:
        return Eligibility("blocked", ["personal/invalid address — treated as an individual subscriber"], ["PERSONAL_ADDR"])

    age = (today - date.fromisoformat(lead.research_date)).days
    if age > int(cfg.get("research_max_age_days", 180)):
        reasons.append(f"research is {age} days old — re-verify the organisation and contact")
        rules.append("STALE_RESEARCH")

    st = lead.subscriber_type
    if st == "unknown":
        return Eligibility("manual_review", reasons + ["subscriber type unknown — confirm legal form (Companies House "
                                                       "/ Charity Commission) before any email"], rules + ["UNKNOWN_SUBSCRIBER"])
    if st in INDIVIDUAL_SUBSCRIBERS:
        if not consent:
            return Eligibility("blocked", [f"'{st}' is an individual subscriber under PECR: unsolicited email "
                                           "requires prior consent, and none is recorded"], ["PECR_REG22"])
        reasons.append(f"consent on record: {consent}")
        rules.append("CONSENT")
    elif st in CORPORATE_SUBSCRIBERS:
        if not is_role_address(lead.contact_email):
            if not pcfg.get("lia_documented"):
                return Eligibility("blocked", ["named contact at a corporate subscriber is personal data: a "
                                               "Legitimate Interests Assessment must be documented for this product"],
                                   ["UKGDPR_LIA"])
            reasons.append(f"named business contact; LIA {pcfg.get('lia_reference')}")
            rules.append("LIA")
        else:
            reasons.append("generic role address at a corporate subscriber")
            rules.append("CORPORATE_ROLE_ADDR")
    else:
        return Eligibility("blocked", [f"unrecognised subscriber type {st}"], ["UNKNOWN_TYPE"])

    if "STALE_RESEARCH" in rules:
        return Eligibility("manual_review", reasons, rules)
    return Eligibility("eligible", reasons + ["sender ID and opt-out configured"], rules + ["SENDER_ID_OK"])
