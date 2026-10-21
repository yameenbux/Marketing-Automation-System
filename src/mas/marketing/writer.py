"""Content writer.

The default writer is deterministic: it assembles copy only from verified
profile facts, so every sentence is traceable to a quoted source. It is free and
cannot hallucinate. The optional LLM writer (llm.py) can polish the wording, but
its output goes through the same validator and still needs human approval.

Every generated item records the fact IDs it used (`fact_ids`).
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field

from ..products.profile import Fact, Profile

PLATFORM_LIMITS = {"instagram": 2200, "linkedin": 3000, "x": 280, "facebook": 5000, "email": 8000, "blog": 50000}
PILLARS = ("problem_solution", "feature_spotlight", "how_it_works", "privacy_trust", "behind_the_build")

HASHTAGS = {
    "masjidone": ["#masjid", "#madrasah", "#mosque", "#UKmasjid"],
    "domi": ["#domiciliary", "#homevisits", "#eyecare", "#healthtech"],
    "booked-in": ["#beautybusiness", "#lashtech", "#bookingpage", "#solobusiness"],
    "tidemark": ["#weighttracker", "#privacyfirst", "#iphoneapp"],
    "bolton-vouched": ["#Bolton", "#BoltonTrades", "#LocalTrades", "#SupportLocal"],
}


@dataclass
class Draft:
    product: str
    kind: str              # social_post | video_script | email | blog_outline
    platform: str
    pillar: str
    text: str
    fact_ids: list[str]
    meta: dict = field(default_factory=dict)

    def fingerprint(self) -> str:
        return hashlib.sha256(f"{self.product}|{self.kind}|{self.platform}|{self.text}".encode()).hexdigest()

    def body(self) -> dict:
        return {"text": self.text, "pillar": self.pillar, "fact_ids": self.fact_ids, **self.meta}


def _pick(facts: list[Fact], avoid: set[str], n: int = 1, offset: int = 0) -> list[Fact]:
    fresh = [f for f in facts if f.id not in avoid] or facts
    if not fresh:
        return []
    start = offset % len(fresh)
    rotated = fresh[start:] + fresh[:start]
    return rotated[:n]


def cta_line(p: Profile) -> tuple[str, list[str]]:
    for kind in ("cta", "url"):
        for f in p.by_kind(kind):
            url = _first_url(f.quote) or _first_url(f.text)
            if url:
                return f"Find out more: {url}", [f.id]
    return f"Find out more about {p.name}.", []


def _first_url(s: str) -> str | None:
    m = re.search(r"https?://[^\s)\]>*`]+|\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:co\.uk|uk|com|app)(?:/[^\s)\]>*`]*)?", s)
    if not m:
        return None
    url = m.group(0).rstrip(".,;:")
    return url if url.startswith("http") else f"https://{url}"


class TemplateWriter:
    """Facts-only copywriter. `avoid` holds fact IDs used recently, to reduce repetition."""

    def social_post(self, p: Profile, platform: str, pillar: str, avoid: set[str] = frozenset(),
                    offset: int = 0) -> Draft | None:
        pains, feats = p.by_kind("pain_point"), p.by_kind("feature")
        values, privacy = p.by_kind("value_prop"), p.by_kind("privacy")
        overview = p.by_kind("overview")
        used: list[Fact] = []
        lines: list[str] = []

        if pillar == "problem_solution" and pains and feats:
            (pain,) = _pick(pains, avoid, 1, offset)
            fs = _pick(feats, avoid, 2, offset)
            used += [pain, *fs]
            lines += [pain.text, "", f"{p.name} is built for that:"] + [f"• {f.text}" for f in fs]
        elif pillar == "feature_spotlight" and feats:
            (f,) = _pick(feats, avoid, 1, offset)
            used.append(f)
            lines += [f"Feature spotlight — {p.name}", "", f.text]
            if values:
                (v,) = _pick(values, avoid, 1, offset)
                used.append(v)
                lines += ["", v.text]
        elif pillar == "how_it_works" and feats:
            fs = _pick(feats, avoid, 3, offset)
            used += fs
            lines += [f"How {p.name} works:", ""] + [f"→ {f.text}" for f in fs]
        elif pillar == "privacy_trust" and privacy:
            (pr,) = _pick(privacy, avoid, 1, offset)
            used.append(pr)
            lines += [pr.text]
            if values:
                (v,) = _pick(values, avoid, 1, offset)
                used.append(v)
                lines += ["", v.text]
        elif pillar == "behind_the_build" and overview:
            (o,) = _pick(overview, avoid, 1, offset)
            used.append(o)
            lines += [f"Behind the build: {p.name}", "", o.text]
            fs = _pick(feats, avoid, 1, offset)
            used += fs
            lines += [f"One thing we cared about: {fs[0].text[0].lower() + fs[0].text[1:]}"] if fs else []
        else:
            return None

        cta, cta_ids = cta_line(p)
        lines += ["", cta]
        tags = HASHTAGS.get(p.slug, [])
        if platform in ("instagram", "linkedin", "facebook") and tags:
            lines += ["", " ".join(tags[:4])]
        text = "\n".join(lines).strip()
        if platform == "x":
            text = self._shorten_for_x(used, cta)
        return Draft(p.slug, "social_post", platform, pillar, text, [f.id for f in used] + cta_ids)

    @staticmethod
    def _shorten_for_x(used: list[Fact], cta: str) -> str:
        body = used[0].text if used else ""
        limit = PLATFORM_LIMITS["x"] - len(cta) - 2
        if len(body) > limit:
            body = body[: limit - 1].rsplit(" ", 1)[0] + "…"
        return f"{body}\n\n{cta}"

    def video_script(self, p: Profile, seconds: int = 30, avoid: set[str] = frozenset(), features: int = 2) -> Draft:
        """A short-form script: hook → problem → 3 features → value → CTA. One scene per fact."""
        pains, feats, values = p.by_kind("pain_point"), p.by_kind("feature"), p.by_kind("value_prop")
        overview = p.by_kind("overview")
        scenes: list[dict] = []
        hook = overview[0] if overview else None
        if hook:
            scenes.append({"role": "hook", "fact_id": hook.id, "on_screen": p.name, "narration": hook.text})
        if pains:
            (pain,) = _pick(pains, avoid, 1)
            scenes.append({"role": "problem", "fact_id": pain.id, "on_screen": _headline(pain.text),
                           "narration": pain.text})
        for f in _pick(feats, avoid, features):
            scenes.append({"role": "feature", "fact_id": f.id, "on_screen": _headline(f.text), "narration": f.text})
        if values:
            (v,) = _pick(values, avoid, 1)
            scenes.append({"role": "value", "fact_id": v.id, "on_screen": _headline(v.text), "narration": v.text})
        cta, cta_ids = cta_line(p)
        scenes.append({"role": "cta", "fact_id": cta_ids[0] if cta_ids else None,
                       "on_screen": cta.replace("Find out more: ", ""), "narration": f"{cta.split(':')[0]} at the link."})
        per = round(seconds / len(scenes), 2)
        for s in scenes:
            s["seconds"] = per
        text = "\n".join(f"[{s['role'].upper()} {s['seconds']}s] {s['narration']}" for s in scenes)
        return Draft(p.slug, "video_script", "video", "explainer", text,
                     [s["fact_id"] for s in scenes if s["fact_id"]], {"scenes": scenes, "target_seconds": seconds})

    def email(self, p: Profile, avoid: set[str] = frozenset()) -> Draft:
        pains, feats = p.by_kind("pain_point"), p.by_kind("feature")
        used = _pick(pains, avoid, 1) + _pick(feats, avoid, 3)
        cta, cta_ids = cta_line(p)
        body = [f"Subject: {p.name} — {_headline(used[0].text) if used else 'an introduction'}", ""]
        body += [used[0].text, ""] if used else []
        body += [f"{p.name} helps with that:"] + [f"- {f.text}" for f in used[1:]] + ["", cta]
        return Draft(p.slug, "email", "email", "newsletter", "\n".join(body), [f.id for f in used] + cta_ids)

    def blog_outline(self, p: Profile) -> Draft:
        sections = [("The problem", p.by_kind("pain_point")[:3]), ("What it does", p.by_kind("feature")[:6]),
                    ("Why it matters", p.by_kind("value_prop")[:3]), ("Privacy and trust", p.by_kind("privacy")[:2])]
        lines, ids = [f"# {p.name}: an overview", ""], []
        for title, facts in sections:
            if not facts:
                continue
            lines.append(f"## {title}")
            for f in facts:
                lines.append(f"- {f.text}  <!-- fact:{f.id} -->")
                ids.append(f.id)
            lines.append("")
        cta, cta_ids = cta_line(p)
        lines.append(cta)
        return Draft(p.slug, "blog_outline", "blog", "education", "\n".join(lines), ids + cta_ids)


def _headline(sentence: str, max_words: int = 9) -> str:
    whole = sentence.strip().rstrip(".")
    if len(whole.split()) <= 14:
        return whole                       # short enough: never cut a sentence into a fragment
    s = re.split(r"[,;:—–]| so | because | which ", whole, maxsplit=1)[0]
    if s.lower().startswith(("when ", "if ", "because ", "while ", "once ")):
        s = whole                          # a subordinate clause alone is a fragment
    words = s.split()
    return " ".join(words[:max_words]) + ("…" if len(words) > max_words else "")


def dumps(d: Draft) -> str:
    return json.dumps(d.__dict__, indent=2, ensure_ascii=False)
