"""Static graphics: social cards, carousels, thumbnails, storyboard sheets. Pure Pillow, no network, no cost."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from .brand import Brand, fit, font

SIZES = {
    "square": (1080, 1080),
    "portrait": (1080, 1350),     # Instagram feed 4:5
    "story": (1080, 1920),        # Reels / Stories / Shorts 9:16
    "landscape": (1920, 1080),
    "thumbnail": (1280, 720),     # YouTube thumbnail
}


def background(size: tuple[int, int], b: Brand) -> Image.Image:
    """Brand background with a soft diagonal glow — avoids flat, template-looking fills."""
    w, h = size
    img = Image.new("RGB", size, b.bg)
    glow = Image.new("RGB", size, b.bg)
    d = ImageDraw.Draw(glow)
    r = int(max(w, h) * 0.55)
    d.ellipse([w - r, -r // 2, w + r, r + r // 2], fill=b.surface)
    glow = glow.filter(ImageFilter.GaussianBlur(max(w, h) // 6))
    return Image.blend(img, glow, 0.85)


def rounded(img: Image.Image, radius: int) -> Image.Image:
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, *img.size], radius, fill=255)
    out = Image.new("RGBA", img.size)
    out.paste(img.convert("RGBA"), (0, 0), mask)
    return out


def shadowed_card(shot: Image.Image, box_w: int, box_h: int, radius: int = 24) -> Image.Image:
    shot = shot.convert("RGB")
    scale = min(box_w / shot.width, box_h / shot.height)
    shot = shot.resize((max(1, int(shot.width * scale)), max(1, int(shot.height * scale))), Image.LANCZOS)
    card = rounded(shot, radius)
    pad = 40
    canvas = Image.new("RGBA", (card.width + pad * 2, card.height + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([pad, pad + 14, pad + card.width, pad + card.height + 14], radius,
                                         fill=(0, 0, 0, 110))
    canvas = Image.alpha_composite(canvas, sh.filter(ImageFilter.GaussianBlur(18)))
    canvas.alpha_composite(card, (pad, pad))
    return canvas


def wordmark(draw: ImageDraw.ImageDraw, b: Brand, xy: tuple[int, int], size: int) -> None:
    x, y = xy
    r = size // 4
    draw.ellipse([x, y + size // 2 - r, x + 2 * r, y + size // 2 + r], fill=b.accent)
    draw.text((x + 2 * r + size // 3, y), b.name, font=font("display", size), fill=b.text)


def social_card(b: Brand, headline: str, body: str, footer: str, size_name: str, out: Path,
                label: str | None = None, screenshot: Image.Image | None = None) -> Path:
    w, h = SIZES[size_name]
    img = background((w, h), b).convert("RGBA")
    d = ImageDraw.Draw(img)
    m = int(w * 0.08)
    wordmark(d, b, (m, m), int(w * 0.035))
    y = int(h * 0.2)
    if label:
        d.text((m, y), label.upper(), font=font("label", int(w * 0.024)), fill=b.accent)
        y += int(w * 0.06)
    text_h = int(h * (0.32 if screenshot is not None else 0.42))
    f, lines, lh = fit(headline, "display", w - 2 * m, text_h, start=int(w * 0.085), minimum=int(w * 0.04))
    for line in lines:
        d.text((m, y), line, font=f, fill=b.text)
        y += lh
    y += int(h * 0.025)
    if body:
        fb, blines, blh = fit(body, "body", w - 2 * m, int(h * 0.18), start=int(w * 0.034), minimum=int(w * 0.022),
                              line_gap=1.4)
        for line in blines:
            d.text((m, y), line, font=fb, fill=b.muted)
            y += blh
    if screenshot is not None:
        avail = h - y - int(h * 0.16)
        if avail > h * 0.15:
            card = shadowed_card(screenshot, w - 2 * m, avail)
            img.alpha_composite(card, ((w - card.width) // 2, y + int(h * 0.01)))
    ff = font("body_medium", int(w * 0.028))
    fy = h - m - ff.size
    d.line([m, fy - int(h * 0.03), w - m, fy - int(h * 0.03)], fill=b.muted, width=2)
    d.text((m, fy), footer, font=ff, fill=b.accent)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out, quality=92)
    return out


def thumbnail(b: Brand, title: str, out: Path, screenshot: Image.Image | None = None) -> Path:
    w, h = SIZES["thumbnail"]
    img = background((w, h), b).convert("RGBA")
    d = ImageDraw.Draw(img)
    m = 64
    text_w = int(w * (0.5 if screenshot is not None else 0.84))
    wordmark(d, b, (m, m), 34)
    f, lines, lh = fit(title, "display", text_w, int(h * 0.55), start=96, minimum=44, line_gap=1.08)
    y = (h - lh * len(lines)) // 2 + 20
    for line in lines:
        d.text((m, y), line, font=f, fill=b.text)
        y += lh
    d.rectangle([m, y + 16, m + 120, y + 26], fill=b.accent)
    if screenshot is not None:
        card = shadowed_card(screenshot, int(w * 0.46), int(h * 0.78), radius=18)
        img.alpha_composite(card, (w - card.width + 10, (h - card.height) // 2))
    out.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out, quality=92)
    return out


def contact_sheet(frames: list[tuple[str, Image.Image]], out: Path, cols: int = 4, cell_w: int = 360) -> Path:
    """Storyboard sheet: one keyframe per scene with its label underneath."""
    if not frames:
        raise ValueError("no frames")
    aspect = frames[0][1].height / frames[0][1].width
    cell_h = int(cell_w * aspect)
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (cell_w + 24) + 24, rows * (cell_h + 84) + 24), (245, 245, 242))
    d = ImageDraw.Draw(sheet)
    lf = font("label", 18)
    for i, (label, fr) in enumerate(frames):
        x = 24 + (i % cols) * (cell_w + 24)
        y = 24 + (i // cols) * (cell_h + 84)
        sheet.paste(fr.convert("RGB").resize((cell_w, cell_h), Image.LANCZOS), (x, y))
        text = f"{i + 1}. {label}"
        while lf.getlength(text) > cell_w and len(text) > 4:
            text = text[:-2].rstrip() + "…"
        d.text((x, y + cell_h + 10), text, font=lf, fill=(30, 30, 30))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return out
