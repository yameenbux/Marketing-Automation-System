"""Brand tokens and typographic helpers shared by graphics and video."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from PIL import ImageFont

FONT_DIRS = [Path("/usr/share/fonts/opentype/inter"), Path(__file__).resolve().parents[3] / "assets" / "fonts"]
FONT_FILES = {
    "display": "InterDisplay-Bold.otf",
    "display_semibold": "InterDisplay-SemiBold.otf",
    "body": "Inter-Regular.otf",
    "body_medium": "Inter-Medium.otf",
    "label": "Inter-SemiBold.otf",
}
FALLBACK = "DejaVuSans.ttf"


@lru_cache(maxsize=256)
def font(role: str, size: int) -> ImageFont.FreeTypeFont:
    name = FONT_FILES[role]
    for d in FONT_DIRS:
        if (d / name).exists():
            return ImageFont.truetype(str(d / name), size)
    return ImageFont.truetype(FALLBACK, size)


def hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def luminance(rgb: tuple[int, int, int]) -> float:
    def ch(c: int) -> float:
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


@dataclass(frozen=True)
class Brand:
    name: str
    bg: tuple[int, int, int]
    surface: tuple[int, int, int]
    accent: tuple[int, int, int]
    text: tuple[int, int, int]
    muted: tuple[int, int, int]

    @classmethod
    def from_profile(cls, name: str, brand: dict) -> "Brand":
        bg = hex_rgb(brand.get("primary_color") or "#1B1F24")
        surface = hex_rgb(brand.get("secondary_color") or "#2B3138")
        accent = hex_rgb(brand.get("accent_color") or "#E0A84F")
        light, dark = (246, 243, 236), (18, 18, 18)
        text = light if contrast(light, bg) >= contrast(dark, bg) else dark
        muted = tuple(int(t * 0.72 + b * 0.28) for t, b in zip(text, bg))
        # Accent must stay legible on the background; nudge towards text colour until AA-large (3:1).
        for _ in range(10):
            if contrast(accent, bg) >= 3.0:
                break
            accent = tuple(int(a * 0.8 + t * 0.2) for a, t in zip(accent, text))
        return cls(name, bg, surface, accent, text, muted)  # type: ignore[arg-type]

    def checks(self) -> dict:
        return {"text_on_bg": round(contrast(self.text, self.bg), 2),
                "muted_on_bg": round(contrast(self.muted, self.bg), 2),
                "accent_on_bg": round(contrast(self.accent, self.bg), 2)}


def wrap(text: str, fnt: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if fnt.getlength(trial) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit(text: str, role: str, max_w: int, max_h: int, start: int, minimum: int = 18,
        line_gap: float = 1.15) -> tuple[ImageFont.FreeTypeFont, list[str], int]:
    """Largest font size at which `text` fits the box. Returns (font, lines, line_height)."""
    size = start
    while size >= minimum:
        f = font(role, size)
        lines = wrap(text, f, max_w)
        lh = int(size * line_gap)
        if lh * len(lines) <= max_h and all(f.getlength(line) <= max_w for line in lines):
            return f, lines, lh
        size -= 2
    f = font(role, minimum)
    return f, wrap(text, f, max_w), int(minimum * line_gap)
