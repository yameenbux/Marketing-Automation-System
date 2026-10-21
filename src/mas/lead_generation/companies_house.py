"""Companies House public data API — a lawful, free source of organisation-level data.

It also tells us the legal form, which drives the PECR subscriber-type decision.
Requires COMPANIES_HOUSE_API_KEY (free registration). Disabled by default.
Docs: https://developer.company-information.service.gov.uk/
"""
from __future__ import annotations

import base64
import json
import urllib.parse
from datetime import date

from ..config import Settings
from ..github_sync.client import Response, Transport, urllib_transport
from ..policy import Action, Policy
from .leads import Lead

API = "https://api.company-information.service.gov.uk"
CORPORATE_TYPES = {"ltd", "plc", "llp", "private-limited-guarant-nsc", "private-limited-guarant-nsc-limited-exemption",
                   "charitable-incorporated-organisation", "scottish-charitable-incorporated-organisation",
                   "private-unlimited", "royal-charter", "registered-society-non-jurisdictional"}


def subscriber_type(company_type: str | None) -> str:
    return "corporate" if company_type in CORPORATE_TYPES else "unknown"


def search(policy: Policy, query: str, *, transport: Transport = urllib_transport, limit: int = 20) -> list[Lead]:
    key = Settings.secret("COMPANIES_HOUSE_API_KEY")
    if not key:
        raise PermissionError("COMPANIES_HOUSE_API_KEY not set")
    if not policy.authorize(Action.FETCH_EXTERNAL, "companies_house", detail={"query": query}).allowed:
        return []
    url = f"{API}/search/companies?q={urllib.parse.quote(query)}&items_per_page={min(limit, 50)}"
    auth = base64.b64encode(f"{key}:".encode()).decode()
    r: Response = transport(url, {"Authorization": f"Basic {auth}", "Accept": "application/json"})
    if r.status != 200:
        raise RuntimeError(f"Companies House HTTP {r.status}")
    leads = []
    for item in json.loads(r.body).get("items", []):
        if item.get("company_status") != "active":
            continue
        number = item.get("company_number")
        leads.append(Lead(
            company=item.get("title", "").title(),
            source_url=f"https://find-and-update.company-information.service.gov.uk/company/{number}",
            research_date=date.today().isoformat(),
            qualification_reason=f"matched Companies House search '{query}' — relevance must be confirmed by a person",
            country="GB", company_number=number, subscriber_type=subscriber_type(item.get("company_type")),
            signals=[f"ch_type:{item.get('company_type')}"],
        ))
    return leads
