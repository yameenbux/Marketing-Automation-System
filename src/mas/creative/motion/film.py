"""Cinematic film renderer: per-product art direction rendered from HTML/CSS/SVG in headless Chromium.

Pipeline: verified script → per-scene narration (product's own voice) → scene timing → screenshots of the
product's own public site → HTML timeline (runtime.js + style pack) → frame-by-frame capture (renderAt(t)) →
ffmpeg (H.264) → audio mix (narration + procedural music, side-chain ducked) → QC.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ...context import Context
from ...marketing.validator import validate
from ...marketing.writer import TemplateWriter
from ...policy import Action
from ...products.profile import load_profile
from .. import music, qc, screenshots, tts
from ..video import caption_chunks

HERE = Path(__file__).resolve().parent
FONTS_CSS = HERE.parents[3] / "assets" / "fonts" / "fonts.css"
MODELS = HERE.parents[3] / "models" / "piper"
FORMATS = {"story": (1080, 1920), "square": (1080, 1080), "landscape": (1920, 1080), "portrait": (1080, 1350)}

# One distinct voice per product. Licences: see LICENCES.md written into each campaign.
VOICES = {
    "masjidone": {"model": "en_GB-vctk-medium.onnx", "speaker": 95, "rate": 1.08,   # p226, male, measured
                  "credit": "Piper VCTK voice (speaker p226) — dataset CC BY 4.0, University of Edinburgh"},
    "domi": {"model": "en_GB-alba-medium.onnx", "speaker": None, "rate": 1.0,
             "credit": "Piper 'alba' voice — dataset CC BY 4.0, University of Edinburgh"},
    "booked-in": {"model": "en_GB-cori-high.onnx", "speaker": None, "rate": 0.98,
                  "credit": "Piper 'cori' voice — trained on public-domain LibriVox recordings"},
    "tidemark": {"model": "en_GB-vctk-medium.onnx", "speaker": 60, "rate": 1.06,      # p232
                 "credit": "Piper VCTK voice (speaker p232) — dataset CC BY 4.0, University of Edinburgh"},
    "bolton-vouched": {"model": "en_GB-northern_english_male-medium.onnx", "speaker": None, "rate": 1.0,
                       "credit": "Piper 'northern_english_male' voice — dataset CC BY-SA 4.0 (OpenSLR 83)"},
}
LESSAC_NOTE = ("Voices other than 'cori' are fine-tuned from the 'lessac' voice, whose source data was released for "
               "research; confirm commercial-use terms before paid promotion.")


@dataclass
class FilmResult:
    slug: str
    out_dir: Path
    files: list[str]
    qc_ok: bool
    notes: list[str]


def _run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)  # noqa: S603
    if r.returncode != 0:
        raise RuntimeError(f"{cmd[0]} failed: {r.stderr[-600:]}")


def _duration(path: Path) -> float:
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",  # noqa: S603,S607
                                 str(path)], capture_output=True, text=True).stdout.strip() or 0)


def prepare(ctx: Context, slug: str, out: Path, capture: bool = True) -> dict:
    """Script, narration, timings and screenshots — shared by every format."""
    prof = load_profile(ctx.root, slug)
    script = TemplateWriter().video_script(prof)
    scenes = script.meta["scenes"]
    text = "\n".join(s["narration"] + " " + s["on_screen"] for s in scenes)
    v = validate(text, product=prof, platform="blog", fact_ids=script.fact_ids)
    if not v.ok:
        raise ValueError(f"script failed validation: {v.errors}")

    voice = VOICES[slug]
    t, spec_scenes = 0.0, []
    for i, s in enumerate(scenes):
        wav = out / "audio" / f"vo_{i + 1:02d}.wav"
        if not wav.exists():
            tts.synthesize(ctx.policy, s["narration"], wav, MODELS / voice["model"], voice["speaker"], voice["rate"])
        speech = _duration(wav) if wav.exists() else 0.0
        lead = 0.35 if i else 0.9                      # let the hook breathe before the first word
        dur = round(max(3.2 if s["role"] in ("hook", "cta") else 3.0, lead + speech + 0.55), 2)
        caps = [(a + lead, z + lead, c) for a, z, c in caption_chunks(s["narration"], speech, 6)] if speech else []
        spec_scenes.append({"role": s["role"], "on_screen": s["on_screen"], "narration": s["narration"],
                            "fact_id": s["fact_id"], "start": round(t, 3), "dur": dur, "lead": lead,
                            "captions": caps, "audio": str(wav) if wav.exists() else None})
        t += dur

    assets: dict = {"hero": None, "sections": [], "mobile": None}
    from ...github_sync.sync import load_registry
    entry = next((e for e in load_registry(ctx.root)["products"] if e["slug"] == slug), {})
    from ..pipeline import product_urls
    urls = product_urls(prof)
    if capture and urls and entry.get("screenshots") is not False:
        hosts = {u.split("/")[2] for u in urls}
        desk = screenshots.capture(ctx.policy, urls[0], out / "source" / "desktop.png", hosts, scroll_sections=5)
        mob = screenshots.capture(ctx.policy, urls[0], out / "source" / "mobile.png", hosts, mobile=True)
        from PIL import Image
        if desk:
            assets["hero"] = desk[0].as_uri()
            assets["sections"] = [p.as_uri() for p in desk[1:] if not screenshots.is_blank(Image.open(p))]
        if mob and not screenshots.is_blank(Image.open(mob[0])):
            assets["mobile"] = mob[0].as_uri()
    feats = [s for s in spec_scenes if s["role"] == "feature"]
    for i, s in enumerate(feats):                       # each feature scene gets a different real section
        pool = assets["sections"][1:] or assets["sections"] or ([assets["hero"]] if assets["hero"] else [])
        s["shot"] = pool[(i * 2) % len(pool)] if pool else None   # skip the hero-transition section, spread picks
    return {"slug": slug, "name": prof.name, "scenes": spec_scenes, "total": round(t, 3), "assets": assets,
            "fact_ids": script.fact_ids, "voice": voice}


def build_html(spec: dict, fmt: str, out: Path, fps: int) -> Path:
    w, h = FORMATS[fmt]
    film = dict(spec, format=fmt, width=w, height=h, fps=fps)
    style_css = (HERE / "styles" / f"{spec['slug']}.css").as_uri()
    style_js = (HERE / "styles" / f"{spec['slug']}.js").as_uri()
    html = f"""<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="{FONTS_CSS.as_uri()}"><link rel="stylesheet" href="{(HERE / 'base.css').as_uri()}">
<link rel="stylesheet" href="{style_css}">
<style>:root{{--w:{w}px;--h:{h}px;--u:{min(w, h) / 100}px}}</style>
<script>window.FILM = {json.dumps(film)};</script>
</head><body><div id="stage"></div>
<script src="{style_js}"></script><script src="{(HERE / 'runtime.js').as_uri()}"></script>
<script>/* style scenes reference runtime helpers lazily */</script></body></html>"""
    page = out / f".film_{fmt}.html"
    page.write_text(html, encoding="utf-8")
    return page


def capture_frames(page: Path, fmt: str, total: float, fps: int, video_out: Path,
                   stills: dict[str, float] | None = None) -> dict[str, Path]:
    from playwright.sync_api import sync_playwright
    w, h = FORMATS[fmt]
    n = int(round(total * fps))
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "image2pipe", "-vcodec", "mjpeg", "-r", str(fps),  # noqa: S603,S607
                           "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "19",
                           "-movflags", "+faststart", str(video_out)], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    saved: dict[str, Path] = {}
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(args=["--allow-file-access-from-files", "--disable-web-security"])
            pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
            errors: list[str] = []
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.goto(page.as_uri(), wait_until="load")
            pg.evaluate("window.READY")
            pg.wait_for_timeout(300)
            if errors:
                raise RuntimeError("page error: " + "; ".join(errors[:3]))
            for i in range(n):
                pg.evaluate(f"renderAt({i / fps:.4f})")
                ff.stdin.write(pg.screenshot(type="jpeg", quality=90))  # type: ignore[union-attr]
            for name, at in (stills or {}).items():
                pg.evaluate(f"renderAt({at:.4f})")
                path = video_out.parent / name
                pg.screenshot(path=str(path), type="jpeg", quality=93)
                saved[name] = path
            if errors:
                raise RuntimeError("page error: " + "; ".join(errors[:3]))
            b.close()
        ff.stdin.close()  # type: ignore[union-attr]
        if ff.wait(timeout=900) != 0:
            raise RuntimeError(ff.stderr.read().decode()[-500:])  # type: ignore[union-attr]
    except BaseException:
        ff.kill()
        raise
    return saved


def mix_audio(spec: dict, out: Path, music_wav: Path) -> Path:
    """Narration clips placed at their scene times, music bed ducked under the voice."""
    inputs, filters, labels = [], [], []
    for i, s in enumerate(s for s in spec["scenes"] if s["audio"]):
        inputs += ["-i", s["audio"]]
        ms = int((s["start"] + s["lead"]) * 1000)
        filters.append(f"[{i}:a]aresample=44100,adelay={ms}|{ms},apad[v{i}]")
        labels.append(f"[v{i}]")
    k = len(labels)
    inputs += ["-i", str(music_wav)]
    total = spec["total"]
    filters.append(f"{''.join(labels)}amix=inputs={k}:normalize=0,atrim=0:{total:.3f},asplit=2[vo][sc]")
    filters.append(f"[{k}:a]aresample=44100,volume=0.55,atrim=0:{total:.3f}[mu]")
    filters.append("[mu][sc]sidechaincompress=threshold=0.02:ratio=9:attack=15:release=450[duck]")
    filters.append("[vo][duck]amix=inputs=2:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11[out]")
    dest = out / "audio" / "mix.m4a"
    _run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filters), "-map", "[out]",
          "-c:a", "aac", "-b:a", "160k", "-ar", "44100", str(dest)])
    return dest


def render_film(ctx: Context, slug: str, formats: list[str] | None = None, fps: int = 30,
                out: Path | None = None, capture: bool = True) -> FilmResult:
    formats = formats or ["story", "square", "landscape", "portrait"]
    if ctx.policy.kill_switch_active():
        raise PermissionError("kill switch is active")
    out = out or ctx.root / "assets" / slug / "film"
    out.mkdir(parents=True, exist_ok=True)
    notes: list[str] = []
    spec = prepare(ctx, slug, out, capture)
    (out / "film.json").write_text(json.dumps(spec, indent=2))
    bed = music.render(slug, spec["total"], out / "audio" / "music.wav",
                       ctx.root / "assets" / "masjidone" / "_audio" / "courtyard_elevenlabs.mp3")
    mix = mix_audio(spec, out, bed)
    files, results = [], {}
    for fmt in formats:
        if not ctx.policy.authorize(Action.RENDER, "local_render", detail={"film": slug, "fmt": fmt}).allowed:
            notes.append(f"{fmt} blocked by policy")
            results[f"film_{fmt}.mp4"] = {"ok": False, "errors": ["blocked by policy"]}
            continue
        page = build_html(spec, fmt, out, fps)
        if fmt == "portrait":   # 4:5 feed stills (carousel): one per scene at its most resolved moment
            stills = {f"still_{i + 1:02d}_{s['role']}.jpg": s["start"] + s["dur"] * 0.82 for i, s in enumerate(spec["scenes"])}
            saved = capture_frames(page, fmt, 1 / fps, fps, out / ".tmp_portrait.mp4", stills)
            (out / ".tmp_portrait.mp4").unlink(missing_ok=True)
            page.unlink(missing_ok=True)
            for name, p in saved.items():
                results[name] = qc.check_image(p, FORMATS["portrait"])
                files.append(name)
            continue
        silent = out / f".silent_{fmt}.mp4"
        saved = capture_frames(page, fmt, spec["total"], fps, silent)
        final = out / f"film_{fmt}.mp4"
        _run(["ffmpeg", "-v", "error", "-y", "-i", str(silent), "-i", str(mix), "-map", "0:v", "-map", "1:a",
              "-c:v", "copy", "-c:a", "copy", "-shortest", "-movflags", "+faststart", str(final)])
        silent.unlink(missing_ok=True)
        page.unlink(missing_ok=True)
        if fmt in qc.PLATFORM_VIDEO_SPECS:
            results[final.name] = qc.check_video(final, fmt, expect_audio=True)
        files.append(final.name)
    qc_ok = bool(results) and all(r.get("ok") for r in results.values())
    (out / "qc.json").write_text(json.dumps({"ok": qc_ok, "results": results}, indent=2))
    (out / "LICENCES.md").write_text(
        "# Licences\n\n- Fonts: SIL Open Font License 1.1 (see assets/fonts/LICENCE.md).\n"
        f"- Narration: {spec['voice']['credit']}. {LESSAC_NOTE if 'cori' not in spec['voice']['model'] else ''}\n"
        "- Music: procedurally synthesised for this film (own work, no third-party samples)."
        + (" Courtyard ambience includes a 2-second ElevenLabs sound-effect clip generated on your account."
           if slug == "masjidone" else "") + "\n"
        "- Screenshots: the product's own public website. Illustrative scenes are labelled 'Illustration'.\n",
        encoding="utf-8")
    return FilmResult(slug, out, files, qc_ok, notes)
