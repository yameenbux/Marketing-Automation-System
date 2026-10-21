"""Media for posts, and UTM tagging.

Instagram rejects text-only posts, so every post carries an image. Feed images are the product's 4:5 film stills,
which are committed to the repository and served from a public base URL (settings `media.base_url`). Reels need
a hosted video; until video hosting is configured (`media.video_base_url`) they are held as "needs media".
"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import re

# Which still best illustrates each content pillar.
PILLAR_STILL = {
    "problem_solution": "still_02_problem.jpg",
    "feature_spotlight": "still_03_feature.jpg",
    "how_it_works": "still_04_feature.jpg",
    "privacy_trust": "still_05_value.jpg",
    "behind_the_build": "still_01_hook.jpg",
}


def still_for(root: Path, product: str, pillar: str | None) -> str | None:
    """Relative repo path of the still for this product/pillar, if it exists."""
    name = PILLAR_STILL.get(pillar or "", "still_01_hook.jpg")
    for candidate in (name, "still_01_hook.jpg"):
        rel = f"assets/{product}/film/{candidate}"
        if (root / rel).exists():
            return rel
    return None


def public_url(base_url: str | None, rel: str | None) -> str | None:
    if not base_url or not rel:
        return None
    return base_url.rstrip("/") + "/" + rel.lstrip("/")


def utm(url: str, *, source: str, campaign: str, content: str, medium: str = "social") -> str:
    parts = urlsplit(url)
    q = dict(parse_qsl(parts.query))
    q.update({"utm_source": source, "utm_medium": medium, "utm_campaign": campaign, "utm_content": content})
    return urlunsplit((parts.scheme, parts.netloc, parts.path or "/", urlencode(q), parts.fragment))


URL_RE = re.compile(r"https?://[^\s)\]>]+")


def tag_links(text: str, network: str, product: str, content_id: str) -> str:
    """Add UTM parameters to links. Instagram captions can't hold clickable links, so they stay clean there."""
    if network == "instagram":
        return text
    return URL_RE.sub(lambda m: utm(m.group(0), source=network, campaign=f"{product}-organic", content=content_id), text)
