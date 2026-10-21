"""Workflow A — daily planner.

Ranks products by marketing readiness (evidence-based: has a live URL, stated
pricing, a connected channel, few blocking limitations), picks content pillars
that haven't been used recently, and avoids re-using recently cited facts.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ..github_sync.sync import load_registry
from ..products.profile import Profile, list_profiles, load_profile
from ..store import Store
from .writer import PILLARS


@dataclass
class ProductPlan:
    slug: str
    readiness: float
    reasons: list[str]
    destinations: list[str]
    pillar: str | None
    avoid_fact_ids: list[str]
    actions: list[str] = field(default_factory=list)


def readiness(p: Profile, destinations: list[str]) -> tuple[float, list[str]]:
    score, why = 0.0, []
    if p.by_kind("url") or p.by_kind("cta"):
        score += 2; why.append("+2 has a verified URL/CTA")
    if p.by_kind("pricing"):
        score += 1; why.append("+1 pricing is stated")
    if destinations:
        score += 3; why.append(f"+3 connected channel ({', '.join(destinations)})")
    else:
        why.append("+0 no connected publishing channel")
    lim = len(p.limitations())
    penalty = min(lim * 0.25, 2.0)
    if penalty:
        score -= penalty; why.append(f"-{penalty:g} {lim} known limitations")
    unusable = sum(1 for f in p.facts if f.status != "verified")
    if unusable:
        score -= 1; why.append(f"-1 {unusable} unverified facts")
    return round(score, 2), why


def recent_usage(store: Store, slug: str, days: int = 14) -> tuple[dict[str, str], set[str]]:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat(timespec="seconds")
    pillars: dict[str, str] = {}
    facts: set[str] = set()
    for row in store.q("SELECT body, created_at FROM content WHERE product=? AND created_at>=? "
                       "AND status NOT IN ('cancelled','rejected') ORDER BY created_at", (slug, since)):
        body = json.loads(row["body"])
        pillars[body.get("pillar", "")] = row["created_at"]
        facts.update(body.get("fact_ids", []))
    return pillars, facts


def next_pillar(used: dict[str, str]) -> str:
    never = [p for p in PILLARS if p not in used]
    return never[0] if never else min(PILLARS, key=lambda p: used.get(p, ""))


def build_plan(root: Path, store: Store, max_posts: int) -> dict:
    reg = load_registry(root)
    channels = json.loads((root / "config" / "channels.json").read_text())["products"]
    enabled = {e["slug"]: e for e in reg["products"] if e.get("enabled")}
    plans: list[ProductPlan] = []
    for slug in list_profiles(root):
        if slug not in enabled:
            continue
        p = load_profile(root, slug)
        dests = [c["destination"] for c in channels.get(slug, []) if c.get("verified")]
        score, why = readiness(p, dests)
        used_pillars, used_facts = recent_usage(store, slug)
        pp = ProductPlan(slug, score, why, dests, next_pillar(used_pillars), sorted(used_facts))
        last = enabled[slug].get("last_successful_sync")
        if not last or datetime.fromisoformat(last) < datetime.now(timezone.utc) - timedelta(hours=24):
            pp.actions.append("sync")
        if not p.approved:
            pp.actions.append("needs_human_profile_approval")
        plans.append(pp)

    plans.sort(key=lambda x: x.readiness, reverse=True)
    budget = max_posts
    for pp in plans:
        if budget > 0 and pp.destinations:
            pp.actions.append(f"produce_post:{pp.pillar}")
            budget -= 1
        else:
            pp.actions.append(f"draft_only:{pp.pillar}")   # drafts build a backlog even without a channel
    return {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "products": [pp.__dict__ for pp in plans]}
