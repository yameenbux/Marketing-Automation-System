"""Content validation — rules enforced in code before anything can be approved.

Errors block progression. Warnings are shown to the human approver.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..products.profile import Profile, numbers_in
from .writer import PLATFORM_LIMITS

# Claims we can't substantiate for any product without evidence we don't have.
UNSUBSTANTIATED = [
    (r"#\s?1\b|\bnumber one\b", "ranking claim"),
    (r"\b(?:the )?best\b|\bleading\b|\bworld[- ]class\b|\bunrivalled\b", "superlative"),
    (r"\bguarantee[ds]?\b", "guarantee"),
    (r"\btrusted by\b|\bused by\b|\bloved by\b|\b(?:hundreds|thousands|millions|dozens) of (?:happy |satisfied )?"
     r"(?:customers|users|clients|businesses|traders|tradespeople|people|families|masjids|mas\u0101jid|masajid|"
     r"practices|salons|downloads|reviews|members|residents)\b", "social proof without customers"),
    (r"\btestimonial\b|[\"“][^\"”]{10,}[\"”]\s*[—–-]\s*[A-Z]", "testimonial"),
    (r"\baward[- ]winning\b", "award claim"),
    (r"\b100\s?%", "absolute percentage"),
    (r"\blose weight\b|\bweight[- ]loss results?\b|\bburn fat\b|\bcure\b|\bclinically\b", "health outcome claim"),
    (r"\bGDPR[- ]compliant\b|\bfully compliant\b|\bNHS[- ]approved\b", "compliance/endorsement claim"),
]

# Product guardrails from each profile's limitations. Phrases that would imply something unbuilt/unlaunched.
GUARDRAILS: dict[str, list[tuple[str, str]]] = {
    "tidemark": [(r"\bavailable (?:now )?on the app store\b|\bdownload (?:it )?(?:now|today)\b", "not yet on the App Store"),
                 (r"\bicloud sync\b|\bapple watch\b", "not built"),
                 (r"\bapple health\b|\bwidgets?\b|\bautomatic backups?\b", "in development — say so explicitly")],
    "booked-in": [(r"\bdeposits?\b|\bcustom domains?\b|\breschedul", "not built"),
                  (r"\bpublish(?:es|ing)? (?:straight |directly )?to instagram\b", "not built"),
                  (r"\bsign up (?:now|today)\b|\bstart (?:your )?free\b", "not provisioned for live sign-ups")],
    "domi": [(r"\bpractices? (?:use|love|rely)\b|\bour customers\b", "no customers yet"),
             (r"\bnoah\b|\bdental charting\b|\bwound charts?\b", "not built"),
             (r"\b(?:scotland|wales|northern ireland)\b", "rules not modelled")],
    "bolton-vouched": [(r"\bpro\b(?!\s+is\s+coming\s+soon)", "Pro is not built — say 'coming soon' or nothing"),
                       (r"\b(?:upgrade|subscribe|pay)\b[^.\n]{0,30}\b(?:listing|tier|plan|rank)", "nothing to buy yet"),
                       (r"\b(?:featured|sponsored|promoted|paid) (?:listing|placement|spot)s?\b|\btop spot\b|\bpay to rank\b",
                        "payment never affects ranking"),
                       (r"\breviews (?:are|coming) (?:coming|soon)\b", "stale wording — reviews are live"),
                       (r"\b(?:every|all) (?:trader|tradesperson|tradespeople|tradesmen)s? (?:is|are) "
                        r"(?:verified|vetted|checked|approved)\b|\bfully vetted\b|\b(?:dbs|police|background)[- ]checked\b",
                        "'Verified' means the admin's recorded checks for that listing only"),
                       (r"\bguaranteed? (?:work|quality|price)\b", "no guarantee is offered")],
    "masjidone": [(r"\bparent (?:app|access|portal)\b|\bhifz progress\b|\bsabaq progress\b",
                   "status contradictory in README — confirm before promoting"),
                  (r"\bICO[- ]registered\b|\bdata processing agreement\b", "not yet in place")],
}

US_SPELLINGS = {"color": "colour", "organize": "organise", "organization": "organisation", "center": "centre",
                "favorite": "favourite", "behavior": "behaviour", "customize": "customise", "analyze": "analyse",
                "program ": "programme ", "license ": "licence ", "catalog ": "catalogue ", "enrollment": "enrolment"}
URL_RE = re.compile(r"https?://[^\s)\]>]+")


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict:
        return {"ok": self.ok, "errors": self.errors, "warnings": self.warnings}


def allowed_hosts(p: Profile) -> set[str]:
    hosts = set()
    for f in p.facts:
        if f.status != "verified":
            continue
        for s in (f.quote, f.text):
            for m in re.finditer(r"\b([a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:co\.uk|uk|com|app))\b", s):
                hosts.add(m.group(1).lower())
    return hosts


def validate(text: str, *, product: Profile, platform: str, fact_ids: list[str],
             require_cta: bool = True) -> ValidationResult:
    r = ValidationResult()
    lower = text.lower()

    # 1. Evidence: every cited fact must exist, be verified, and be promotable.
    if not fact_ids:
        r.errors.append("no fact IDs cited — copy must be traceable to product sources")
    evidence_numbers: set[str] = set()
    for fid in fact_ids:
        f = product.fact(fid)
        if f is None:
            r.errors.append(f"cites unknown fact {fid}")
        elif f.status != "verified":
            r.errors.append(f"cites {f.status} fact {fid}: {'; '.join(f.problems)}")
        elif f.kind == "limitation":
            r.errors.append(f"cites a limitation ({fid}) as a selling point")
        else:
            evidence_numbers |= numbers_in(f.quote) | numbers_in(f.text)

    # 2. Numbers in copy must come from cited evidence (ignore hashtags and URLs).
    plain = URL_RE.sub(" ", re.sub(r"#\w+", " ", text))
    plain = re.sub(r"(?m)^\s*\d+[.)]\s", " ", plain)          # ordered-list markers are not claims
    stray = numbers_in(plain) - evidence_numbers
    if stray:
        r.errors.append(f"numbers not supported by cited facts: {sorted(stray)}")

    # 3. Unsubstantiated marketing claims.
    for pat, label in UNSUBSTANTIATED:
        m = re.search(pat, text, re.I)
        if m:
            r.errors.append(f"{label}: '{m.group(0)}'")

    # 4. Product-specific guardrails derived from known limitations.
    for pat, why in GUARDRAILS.get(product.slug, []):
        m = re.search(pat, lower, re.I)
        if m:
            r.errors.append(f"guardrail ({why}): '{m.group(0)}'")

    # 5. Links must point to the product's own verified hosts.
    hosts = allowed_hosts(product)
    for url in URL_RE.findall(text):
        host = re.sub(r"^https?://", "", url).split("/")[0].lower()
        if host not in hosts:
            r.errors.append(f"link to unverified host: {host}")

    # 6. Platform technical limits.
    limit = PLATFORM_LIMITS.get(platform)
    if limit and len(text) > limit:
        r.errors.append(f"{len(text)} chars exceeds {platform} limit {limit}")
    if platform == "instagram" and text.count("#") > 30:
        r.errors.append("more than 30 hashtags")
    if platform == "x" and text.count("#") > 2:
        r.warnings.append("more than 2 hashtags on X")

    # 7. Call to action.
    if require_cta and not re.search(r"find out more|request a demo|book|visit|learn more|https?://", lower):
        r.warnings.append("no call to action")

    # 8. British English (light check — not a full spell checker).
    for us, uk in US_SPELLINGS.items():
        if re.search(rf"\b{us.strip()}\b", lower):
            r.warnings.append(f"US spelling '{us.strip()}' — use '{uk.strip()}'")
    if re.search(r"\b(\w+) \1\b", lower):
        r.warnings.append("repeated word")

    # 9. Profile approval gates approval, not drafting.
    if not product.approved:
        r.warnings.append("product profile not yet human-approved — content cannot be approved until it is")
    return r
