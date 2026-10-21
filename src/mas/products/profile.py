"""Product knowledge profiles — the single source of truth for every claim.

A profile is a list of facts. Each fact carries a verbatim quote from a synced
source file. On every load the quote is re-checked against the latest synced
copy, so when a README changes, any fact it no longer supports becomes
`stale` automatically and can no longer be used in content.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

FACT_KINDS = {"overview", "feature", "audience", "pain_point", "value_prop", "limitation",
              "pricing", "url", "cta", "integration", "privacy"}
PROMOTABLE_KINDS = FACT_KINDS - {"limitation"}
_WS = re.compile(r"\s+")
_NUM = re.compile(r"(?<![\w#])£?\d+(?:[.,]\d+)*%?")


def norm(s: str) -> str:
    return _WS.sub(" ", s).strip()


def numbers_in(s: str) -> set[str]:
    return {n.lstrip("£").rstrip("%").replace(",", "") for n in _NUM.findall(s)}


_WORD_NUMS = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7",
              "eight": "8", "nine": "9", "ten": "10", "twelve": "12", "fifteen": "15", "twenty": "20",
              "thirty": "30", "fifty": "50", "hundred": "100"}


def numbers_supported(text: str, quote: str) -> set[str]:
    """Numbers in `text` that the quote does not contain (digits or words)."""
    q = numbers_in(quote) | {v for k, v in _WORD_NUMS.items() if re.search(rf"\b{k}\b", quote, re.I)}
    return numbers_in(text) - q


@dataclass
class Fact:
    id: str
    kind: str
    text: str
    source_path: str
    quote: str
    status: str = "unchecked"     # verified | stale | unverifiable | invalid
    problems: list[str] = field(default_factory=list)

    @property
    def usable(self) -> bool:
        return self.status == "verified" and self.kind in PROMOTABLE_KINDS


@dataclass
class Profile:
    slug: str
    name: str
    data: dict
    facts: list[Fact]
    problems: list[str]

    @property
    def approved(self) -> bool:
        return self.data.get("approval", {}).get("status") == "approved"

    @property
    def brand(self) -> dict:
        return self.data.get("brand", {})

    def fact(self, fid: str) -> Fact | None:
        return next((f for f in self.facts if f.id == fid), None)

    def by_kind(self, kind: str, usable_only: bool = True) -> list[Fact]:
        return [f for f in self.facts if f.kind == kind and (f.usable or not usable_only)]

    def limitations(self) -> list[Fact]:
        return [f for f in self.facts if f.kind == "limitation"]

    def summary(self) -> dict:
        counts: dict[str, int] = {}
        for f in self.facts:
            counts[f.status] = counts.get(f.status, 0) + 1
        return {"slug": self.slug, "approved": self.approved, "facts": len(self.facts),
                "status_counts": counts, "problems": self.problems}


def products_dir(root: Path) -> Path:
    return root / "data" / "products"


def load_profile(root: Path, slug: str) -> Profile:
    pdir = products_dir(root) / slug
    data = json.loads((pdir / "profile.json").read_text(encoding="utf-8"))
    problems: list[str] = []
    for key in ("slug", "name", "repo", "facts", "approval"):
        if key not in data:
            problems.append(f"missing field: {key}")
    if data.get("slug") != slug:
        problems.append(f"slug mismatch: {data.get('slug')} != {slug}")

    sources: dict[str, str | None] = {}
    facts: list[Fact] = []
    seen: set[str] = set()
    for raw in data.get("facts", []):
        src = raw.get("source", {})
        f = Fact(id=raw.get("id", ""), kind=raw.get("kind", ""), text=raw.get("text", ""),
                 source_path=src.get("path", ""), quote=src.get("quote", ""))
        if not f.id or f.id in seen:
            f.problems.append("missing or duplicate id")
        seen.add(f.id)
        if f.kind not in FACT_KINDS:
            f.problems.append(f"unknown kind {f.kind!r}")
        if len(norm(f.quote)) < 12:
            f.problems.append("quote too short to be evidence")
        extra = numbers_supported(f.text, f.quote)
        if extra:
            f.problems.append(f"numbers not in quote: {sorted(extra)}")
        if f.problems:
            f.status = "invalid"
        else:
            if f.source_path not in sources:
                sp = pdir / "sources" / f.source_path
                sources[f.source_path] = norm(sp.read_text(encoding="utf-8")) if sp.is_file() else None
            src_text = sources[f.source_path]
            if src_text is None:
                f.status = "unverifiable"
                f.problems.append("source not synced — run `mas sync`")
            elif norm(f.quote) in src_text:
                f.status = "verified"
            else:
                f.status = "stale"
                f.problems.append("quote no longer present in source — re-verify this fact")
        facts.append(f)
    return Profile(slug=slug, name=data.get("name", slug), data=data, facts=facts, problems=problems)


def list_profiles(root: Path) -> list[str]:
    d = products_dir(root)
    return sorted(p.name for p in d.iterdir() if (p / "profile.json").exists()) if d.exists() else []


KIND_TITLES = [("overview", "Overview"), ("audience", "Target audience"), ("pain_point", "Pain points addressed"),
               ("value_prop", "Value proposition"), ("feature", "Verified features"), ("integration", "Integrations"),
               ("privacy", "Privacy and data"), ("pricing", "Pricing (as stated in the README)"),
               ("url", "Links"), ("cta", "Calls to action"), ("limitation", "Known limitations — never market these as done")]


def render_markdown(p: Profile, root: Path | None = None) -> str:
    """Human-readable profile for review/approval. Generated — edit profile.json, not this file."""
    d = dict(p.data, _root=str(root or "."))
    lines = [f"# {p.name}", "",
             f"> Generated from `profile.json` — edit that, not this file. Source: `{d.get('repo')}` README.",
             "", f"- **Maker:** {d.get('maker') or 'not stated'}  ",
             f"- **Type:** {d.get('product_type')} · **Maturity:** {d.get('maturity')}  ",
             f"- **Approval:** {d.get('approval', {}).get('status')}"
             + (f" by {d['approval']['approved_by']}" if d.get("approval", {}).get("approved_by") else ""),
             f"- **Brand:** primary {p.brand.get('primary_color')}, secondary {p.brand.get('secondary_color')}, "
             f"accent {p.brand.get('accent_color')} — {p.brand.get('tone', '')}", ""]
    for kind, title in KIND_TITLES:
        facts = [f for f in p.facts if f.kind == kind]
        if not facts:
            if kind == "pricing":
                lines += [f"## {title}", "", "_Not stated — do not publish prices._", ""]
            continue
        lines += [f"## {title}", ""]
        for f in facts:
            mark = "" if f.status == "verified" else f" **[{f.status.upper()}]**"
            lines.append(f"- {f.text}{mark}  \n  <sub>`{f.id}` — “{f.quote[:140]}{'…' if len(f.quote) > 140 else ''}”</sub>")
        lines.append("")
    comp_path = Path(d.get("_root", ".")) / "data" / "products" / p.slug / "competitors.json"
    lines += ["## Competitors", ""]
    if comp_path.exists():
        c = json.loads(comp_path.read_text(encoding="utf-8"))
        lines += [f"_{c.get('status', 'research')} — researched {c.get('researched_at')} via {c.get('method')}._", ""]
        for comp in c.get("competitors", []):
            src = ", ".join(comp.get("sources", [])[:2])
            lines.append(f"- **{comp.get('name')}** ({comp.get('category')}) — {comp.get('what_they_offer')} "
                         f"Pricing: {comp.get('pricing') or 'not published'}. <sub>{src}</sub>")
        if c.get("positioning_takeaways"):
            lines += ["", "**Positioning takeaways (hypotheses):**"] + [f"- {t}" for t in c["positioning_takeaways"]]
        lines.append("")
    else:
        lines += ["_Not yet researched. Add only from permitted sources with citations._", ""]
    return "\n".join(lines)
