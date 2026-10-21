"""Workflow E — lead research records, scoring, deduplication, suppression.

Data minimisation is enforced by the schema: a lead is an *organisation*. The
only person-level field is an optional business contact (role + work address),
and personal-webmail addresses are rejected outright.
"""
from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

from ..store import Store, new_id, now_iso

SUBSCRIBER_TYPES = {"corporate", "sole_trader", "partnership", "scottish_partnership", "unincorporated",
                    "individual", "public_body", "unknown"}
PERSONAL_WEBMAIL = {"gmail.com", "googlemail.com", "hotmail.com", "hotmail.co.uk", "outlook.com", "live.com",
                    "live.co.uk", "yahoo.com", "yahoo.co.uk", "icloud.com", "me.com", "aol.com", "btinternet.com",
                    "sky.com", "proton.me", "protonmail.com", "msn.com"}
ROLE_LOCALPARTS = {"info", "hello", "office", "admin", "enquiries", "enquiry", "contact", "sales", "secretary",
                   "team", "reception", "general", "accounts", "madrasah", "committee", "bookings"}
ALLOWED_FIELDS = {"company", "website", "country", "region", "subscriber_type", "company_number", "charity_number",
                  "contact_role", "contact_email", "signals", "qualification_reason", "source_url", "research_date",
                  "notes"}


class LeadError(ValueError):
    pass


@dataclass
class Lead:
    company: str
    source_url: str
    research_date: str                 # ISO date the research was done
    qualification_reason: str          # why this organisation might be relevant (must be verifiable)
    website: str | None = None
    country: str | None = None
    region: str | None = None
    subscriber_type: str = "unknown"
    company_number: str | None = None
    charity_number: str | None = None
    contact_role: str | None = None
    contact_email: str | None = None
    signals: list[str] = field(default_factory=list)
    notes: str | None = None

    def validate(self) -> None:
        if not self.company.strip():
            raise LeadError("company is required")
        if not re.match(r"^https?://", self.source_url or ""):
            raise LeadError("source_url (where this was found) is required")
        date.fromisoformat(self.research_date)
        if self.subscriber_type not in SUBSCRIBER_TYPES:
            raise LeadError(f"subscriber_type must be one of {sorted(SUBSCRIBER_TYPES)}")
        if not self.qualification_reason.strip():
            raise LeadError("qualification_reason is required")
        if self.contact_email:
            dom = email_domain(self.contact_email)
            if dom is None:
                raise LeadError("contact_email is not a valid address")
            if dom in PERSONAL_WEBMAIL:
                raise LeadError("personal webmail addresses are not collected (data minimisation / PECR)")


def email_domain(email: str) -> str | None:
    m = re.fullmatch(r"[A-Za-z0-9._%+'-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})", email.strip())
    return m.group(1).lower() if m else None


def is_role_address(email: str) -> bool:
    return email.split("@", 1)[0].lower() in ROLE_LOCALPARTS


def norm_domain(url_or_domain: str | None) -> str | None:
    if not url_or_domain:
        return None
    d = re.sub(r"^https?://", "", url_or_domain.strip().lower()).split("/")[0]
    return d[4:] if d.startswith("www.") else d


def norm_name(name: str) -> str:
    n = re.sub(r"[^a-z0-9 ]", " ", name.lower())
    n = re.sub(r"\b(ltd|limited|llp|plc|cio|the|trust|uk)\b", " ", n)
    return re.sub(r"\s+", " ", n).strip()


def dedupe_key(lead: Lead) -> str:
    if lead.company_number:
        return f"ch:{lead.company_number.strip().upper()}"
    if lead.charity_number:
        return f"cc:{lead.charity_number.strip()}"
    if lead.website:
        return f"dom:{norm_domain(lead.website)}"
    return f"name:{norm_name(lead.company)}"


def score(lead: Lead, icp: dict) -> tuple[float, list[str]]:
    """Transparent additive score. Returns (0–100, explanation lines)."""
    data = asdict(lead)
    for ex in icp.get("exclude", []):
        if _match(data, ex):
            return 0.0, [f"excluded by rule {ex}"]
    total = sum(c["weight"] for c in icp["criteria"]) or 1
    got, why = 0, []
    for c in icp["criteria"]:
        hit = _match(data, c)
        got += c["weight"] if hit else 0
        why.append(f"{'+' if hit else ' '}{c['weight']:>3} {c['label']}")
    return round(100 * got / total, 1), why


def _match(data: dict, rule: dict) -> bool:
    v = data.get(rule["field"])
    if "equals" in rule:
        return v == rule["equals"]
    if "contains" in rule:
        return rule["contains"] in (v or [])
    if "present" in rule:
        return bool(v) == rule["present"]
    return False


# --- persistence ----------------------------------------------------------
def suppression_keys(lead: Lead) -> list[str]:
    keys = [dedupe_key(lead), f"name:{norm_name(lead.company)}"]
    if lead.website:
        keys.append(f"dom:{norm_domain(lead.website)}")
    if lead.contact_email:
        keys += [f"email:{lead.contact_email.strip().lower()}", f"dom:{email_domain(lead.contact_email)}"]
    return keys


def is_suppressed(store: Store, lead: Lead) -> str | None:
    for k in suppression_keys(lead):
        row = store.conn.execute("SELECT reason FROM suppression WHERE key=?", (k,)).fetchone()
        if row:
            return f"{k}: {row['reason']}"
    return None


def suppress(store: Store, key: str, reason: str) -> None:
    kind = key.split(":", 1)[0]
    if kind not in {"email", "dom", "ch", "cc", "name"}:
        raise LeadError("suppression key must start with email:, dom:, ch:, cc: or name:")
    with store.tx() as c:
        c.execute("INSERT OR REPLACE INTO suppression(key, kind, reason, added_at) VALUES (?,?,?,?)",
                  (key.strip().lower() if kind in ("email", "dom", "name") else key.strip(), kind, reason, now_iso()))
    store.audit("suppress", "human", "ok", f"{key}: {reason}")


def add_lead(store: Store, product: str, lead: Lead, icp: dict | None) -> tuple[str, str]:
    """Insert a validated lead. Returns (lead_id, status). Duplicates return the existing id."""
    lead.validate()
    key = dedupe_key(lead)
    existing = store.conn.execute("SELECT id FROM leads WHERE product=? AND dedupe_key=?", (product, key)).fetchone()
    if existing:
        return existing["id"], "duplicate"
    status = "suppressed" if is_suppressed(store, lead) else "new"
    s, why = score(lead, icp) if icp else (None, ["no ICP configured"])
    lid = new_id("lead")
    with store.tx() as c:
        c.execute("INSERT INTO leads(id, product, company, domain, dedupe_key, score, status, data, created_at)"
                  " VALUES (?,?,?,?,?,?,?,?,?)",
                  (lid, product, lead.company, norm_domain(lead.website), key, s, status,
                   json.dumps(asdict(lead) | {"score_explanation": why}), now_iso()))
    return lid, status


def get_lead(store: Store, lid: str) -> tuple[Lead, dict] | None:
    row = store.conn.execute("SELECT * FROM leads WHERE id=?", (lid,)).fetchone()
    if not row:
        return None
    data = json.loads(row["data"])
    extra = {"score_explanation": data.pop("score_explanation", []), "product": row["product"],
             "score": row["score"], "status": row["status"]}
    return Lead(**data), extra


def import_csv(store: Store, product: str, path: Path, icp: dict | None) -> dict:
    """Import researched leads. Unknown columns are rejected (data minimisation)."""
    counts = {"new": 0, "duplicate": 0, "suppressed": 0, "rejected": 0}
    errors = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        extra_cols = set(reader.fieldnames or []) - ALLOWED_FIELDS
        if extra_cols:
            raise LeadError(f"columns not permitted (data minimisation): {sorted(extra_cols)}")
        for i, row in enumerate(reader, start=2):
            try:
                row = {k: (v.strip() or None) for k, v in row.items() if v is not None}
                row["signals"] = [s.strip() for s in (row.get("signals") or "").split(";") if s.strip()]
                row["subscriber_type"] = row.get("subscriber_type") or "unknown"
                _, status = add_lead(store, product, Lead(**row), icp)
                counts[status] += 1
            except (LeadError, TypeError, ValueError) as e:
                counts["rejected"] += 1
                errors.append(f"row {i}: {e}")
    return {"counts": counts, "errors": errors}
