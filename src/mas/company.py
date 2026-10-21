"""Legal identity: five brands, one company. Every brand is a trading name of YSB Ventures Ltd.

Business emails and letters must identify the company (Companies Act 2006 and the Company, LLP and
Business (Names and Trading Disclosures) Regulations 2015: registered name, part of the UK where it is
registered, company number, registered office). Marketing emails must also not disguise the sender and must
give a valid way to opt out (PECR reg 23). Websites need the same company details; that is a change to the
product sites, which this system never edits.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=4)
def _load(root: str) -> dict:
    return json.loads((Path(root) / "config" / "company.json").read_text(encoding="utf-8"))


def company(root: Path) -> dict:
    return _load(str(root))


def brand_name(root: Path, slug: str) -> str:
    return company(root)["brands"][slug]["name"]


def trading_line(root: Path, slug: str) -> str:
    c = company(root)
    return f"{brand_name(root, slug)} is a trading name of {c['legal_name']}."


def disclosure(root: Path) -> str:
    c = company(root)
    return (f"{c['legal_name']}, registered in {c['registered_in']}, company number {c['company_number']}. "
            f"Registered office: {c['registered_office']}.")


def email_footer(root: Path, slug: str) -> str:
    """Signature + trading name + statutory company details + opt-out, for one brand."""
    c = company(root)
    b = c["brands"][slug]
    return "\n".join([c["sender"]["name"], f"{b['name']} · {b['website'].removeprefix('https://')}", "",
                      trading_line(root, slug), disclosure(root), "", c["opt_out"]])
