"""Programmatic video and motion graphics.

Frames are drawn with Pillow (kinetic typography, animated screenshot cards,
burned-in captions, crossfades, progress bar) and piped straight into ffmpeg
(H.264/yuv420p + AAC) — no intermediate frames on disk, deterministic output,
zero cost. Everything on screen comes from the script, which comes from
verified product facts.
"""
from __future__ import annotations

import math
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw

from .brand import Brand, fit, font, wrap
from .graphics import background, shadowed_card

FPS = 30
FORMATS = {"story": (1080, 1920), "square": (1080, 1080), "landscape": (1920, 1080)}
XFADE = 0.35
ROLE_LABEL = {"problem": "The problem", "feature": "How it helps", "value": "Why it matters",
              "hook": "", "cta": "Find out more"}


@dataclass
class Scene:
    role: str
    on_screen: str
    narration: str
    duration: float
    screenshot: Image.Image | None = None
    speech_s: float | None = None          # length of narration audio, for caption timing
    captions: list[tuple[float, float, str]] = field(default_factory=list)


def ease(p: float) -> float:
    p = max(0.0, min(1.0, p))
    return 1 - (1 - p) ** 3


def caption_chunks(text: str, span: float, max_words: int = 7) -> list[tuple[float, float, str]]:
    words = text.split()
    if not words:
        return []
    chunks = [words[i:i + max_words] for i in range(0, len(words), max_words)]
    total = sum(len(c) for c in chunks)
    out, t = [], 0.0
    for c in chunks:
        d = span * len(c) / total
        out.append((t, t + d, " ".join(c)))
        t += d
    return out


def layout(fmt: str) -> dict:
    w, h = FORMATS[fmt]
    m = int(min(w, h) * 0.075)
    if fmt == "landscape":
        return dict(w=w, h=h, m=m, label_y=int(h * 0.2), head=(m, int(h * 0.26), int(w * 0.44), int(h * 0.42)),
                    shot=(int(w * 0.5), int(h * 0.12), int(w * 0.46), int(h * 0.66)),
                    cap=(m, int(h * 0.80), w - 2 * m, int(h * 0.11)), head_size=int(h * 0.085))
    if fmt == "square":
        return dict(w=w, h=h, m=m, label_y=int(h * 0.14), head=(m, int(h * 0.19), w - 2 * m, int(h * 0.25)),
                    shot=(m, int(h * 0.45), w - 2 * m, int(h * 0.33)),
                    cap=(m, int(h * 0.81), w - 2 * m, int(h * 0.11)), head_size=int(w * 0.075))
    return dict(w=w, h=h, m=m, label_y=int(h * 0.15), head=(m, int(h * 0.19), w - 2 * m, int(h * 0.27)),
                shot=(m, int(h * 0.48), w - 2 * m, int(h * 0.30)),
                cap=(m, int(h * 0.82), w - 2 * m, int(h * 0.09)), head_size=int(w * 0.09))


class SceneRenderer:
    def __init__(self, brand: Brand, fmt: str, total_s: float):
        self.b, self.fmt, self.total = brand, fmt, total_s
        self.L = layout(fmt)
        self.bg = background((self.L["w"], self.L["h"]), brand).convert("RGBA")
        self._card_cache: dict[int, Image.Image] = {}

    def _card(self, shot: Image.Image) -> Image.Image:
        key = id(shot)
        if key not in self._card_cache:
            x, y, bw, bh = self.L["shot"]
            self._card_cache[key] = shadowed_card(shot, bw, bh, radius=max(12, self.L["w"] // 60))
        return self._card_cache[key]

    def frame(self, sc: Scene, t: float, t_global: float) -> Image.Image:
        L, b = self.L, self.b
        img = self.bg.copy()
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        w, h, m = L["w"], L["h"], L["m"]

        # small persistent wordmark (except hook, which has the big one)
        if sc.role != "hook":
            size = int(min(w, h) * 0.03)
            r = size // 4
            d.ellipse([m, m + size // 2 - r, m + 2 * r, m + size // 2 + r], fill=b.accent)
            d.text((m + 2 * r + size // 3, m), b.name, font=font("display_semibold", size), fill=b.text)

        if sc.role == "hook":
            self._hook(d, ov, sc, t)
        elif sc.role == "cta":
            self._cta(d, sc, t)
        else:
            label = ROLE_LABEL.get(sc.role, "")
            if label:
                p = ease(t / 0.4)
                d.text((m, L["label_y"] + int((1 - p) * 12)), label.upper(),
                       font=font("label", int(min(w, h) * 0.026)), fill=(*b.accent, int(255 * p)))
            self._kinetic(d, sc.on_screen, L["head"], L["head_size"], t, start=0.15)
            if sc.screenshot is not None:
                card = self._card(sc.screenshot)
                p = ease((t - 0.25) / 0.6)
                if p > 0:
                    x, y, bw, bh = L["shot"]
                    cx = x + (bw - card.width) // 2
                    cy = y + (bh - card.height) // 2 + int((1 - p) * h * 0.05)
                    c = card if p >= 1 else _fade(card, p)
                    ov.alpha_composite(c, (max(0, cx), max(0, cy)))

        self._caption(d, sc, t)
        # progress bar
        d.rectangle([0, h - 6, int(w * min(1.0, t_global / self.total)), h], fill=(*b.accent, 255))
        img.alpha_composite(ov)
        return img.convert("RGB")

    def _kinetic(self, d: ImageDraw.ImageDraw, text: str, box: tuple[int, int, int, int], start_size: int,
                 t: float, start: float = 0.0, stagger: float = 0.06, dur: float = 0.35) -> None:
        x0, y0, bw, bh = box
        f, lines, lh = fit(text, "display", bw, bh, start=start_size, minimum=max(24, start_size // 3), line_gap=1.12)
        i = 0
        y = y0
        space = f.getlength(" ")
        for line in lines:
            x = x0
            for word in line.split():
                p = ease((t - start - i * stagger) / dur)
                if p > 0:
                    d.text((x, y + int((1 - p) * lh * 0.45)), word, font=f, fill=(*self.b.text, int(255 * p)))
                x += f.getlength(word) + space
                i += 1
            y += lh

    def _hook(self, d: ImageDraw.ImageDraw, ov: Image.Image, sc: Scene, t: float) -> None:
        w, h = self.L["w"], self.L["h"]
        size = int(min(w, h) * 0.11)
        p = ease(t / 0.7)
        f = font("display", size)
        name_w = f.getlength(self.b.name)
        r = int(size * 0.28 * ease(t / 0.4))
        total_w = name_w + size * 0.9
        x = (w - total_w) / 2
        y = h * 0.40
        if r > 0:
            d.ellipse([x, y + size / 2 - r, x + 2 * r, y + size / 2 + r], fill=self.b.accent)
        d.text((x + size * 0.9 + (1 - p) * size * 0.4, y), self.b.name, font=f, fill=(*self.b.text, int(255 * p)))
        lw = int((w * 0.5) * ease((t - 0.5) / 0.6))
        if lw > 0:
            d.rectangle([(w - lw) // 2, int(y + size * 1.45), (w + lw) // 2, int(y + size * 1.45) + 6],
                        fill=self.b.accent)

    def _cta(self, d: ImageDraw.ImageDraw, sc: Scene, t: float) -> None:
        w, h, m = self.L["w"], self.L["h"], self.L["m"]
        p = ease(t / 0.5)
        lab = font("label", int(min(w, h) * 0.03))
        txt = ROLE_LABEL["cta"].upper()
        d.text(((w - lab.getlength(txt)) / 2, h * 0.36), txt, font=lab, fill=(*self.b.accent, int(255 * p)))
        f, lines, lh = fit(sc.on_screen, "display", w - 2 * m, int(h * 0.2), start=int(min(w, h) * 0.085),
                           minimum=28)
        y = h * 0.43
        for line in lines:
            q = ease((t - 0.2) / 0.5)
            d.text(((w - f.getlength(line)) / 2, y + (1 - q) * 20), line, font=f, fill=(*self.b.text, int(255 * q)))
            y += lh
        name_f = font("display_semibold", int(min(w, h) * 0.04))
        d.text(((w - name_f.getlength(self.b.name)) / 2, y + lh * 0.6), self.b.name, font=name_f,
               fill=(*self.b.muted, int(255 * ease((t - 0.5) / 0.5))))

    def _caption(self, d: ImageDraw.ImageDraw, sc: Scene, t: float) -> None:
        cur = next((c for a, z, c in sc.captions if a <= t < z), None)
        if not cur:
            return
        x, y, bw, bh = self.L["cap"]
        f = font("body_medium", max(22, int(min(self.L["w"], self.L["h"]) * 0.034)))
        lines = wrap(cur, f, bw - 48)[:2]
        lh = int(f.size * 1.3)
        box_h = lh * len(lines) + 28
        widest = max(f.getlength(line) for line in lines)
        bx0 = x + (bw - widest) / 2 - 24
        d.rounded_rectangle([bx0, y, bx0 + widest + 48, y + box_h], radius=14, fill=(0, 0, 0, 150))
        ty = y + 14
        for line in lines:
            d.text((x + (bw - f.getlength(line)) / 2, ty), line, font=f, fill=(255, 255, 255, 255))
            ty += lh


def _fade(img: Image.Image, p: float) -> Image.Image:
    a = img.getchannel("A").point(lambda v: int(v * p))
    out = img.copy()
    out.putalpha(a)
    return out


def render(scenes: list[Scene], brand: Brand, fmt: str, out: Path, audio: Path | None = None,
           fps: int = FPS, keyframes: dict[int, Path] | None = None) -> Path:
    total = sum(s.duration for s in scenes)
    for s in scenes:
        if not s.captions and s.narration:
            s.captions = caption_chunks(s.narration, min(s.speech_s or s.duration - 0.3, s.duration - 0.1) - 0.1)
            s.captions = [(a + 0.15, z + 0.15, c) for a, z, c in s.captions]
    w, h = FORMATS[fmt]
    r = SceneRenderer(brand, fmt, total)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(fps),
           "-i", "-"]
    if audio:
        cmd += ["-i", str(audio), "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "128k"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "20",
            "-movflags", "+faststart", "-t", f"{total:.3f}", str(out)]
    out.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)  # noqa: S603
    prev_last: Image.Image | None = None
    t_global = 0.0
    try:
        for idx, sc in enumerate(scenes):
            n = max(1, int(round(sc.duration * fps)))
            last = None
            for i in range(n):
                t = i / fps
                fr = r.frame(sc, t, t_global + t)
                if prev_last is not None and t < XFADE:
                    fr = Image.blend(prev_last, fr, ease(t / XFADE))
                if keyframes is not None and i == int(n * 0.7):
                    kf = out.parent / f"keyframe_{fmt}_{idx + 1:02d}.png"
                    fr.save(kf)
                    keyframes[idx] = kf
                proc.stdin.write(fr.tobytes())  # type: ignore[union-attr]
                last = fr
            prev_last = last
            t_global += sc.duration
        proc.stdin.close()  # type: ignore[union-attr]
        rc = proc.wait(timeout=600)
    except BaseException:
        proc.kill()
        raise
    if rc != 0:
        raise RuntimeError(f"ffmpeg failed: {proc.stderr.read().decode()[-500:]}")  # type: ignore[union-attr]
    return out


def write_srt(scenes: list[Scene], out: Path) -> Path:
    def ts(s: float) -> str:
        ms = int(round(s * 1000))
        return f"{ms // 3_600_000:02d}:{ms // 60_000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    lines, n, offset = [], 1, 0.0
    for sc in scenes:
        for a, z, c in sc.captions:
            lines += [str(n), f"{ts(offset + a)} --> {ts(offset + min(z, sc.duration))}", c, ""]
            n += 1
        offset += sc.duration
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def total_duration(scenes: list[Scene]) -> float:
    return math.fsum(s.duration for s in scenes)
