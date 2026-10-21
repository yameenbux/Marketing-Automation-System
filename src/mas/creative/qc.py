"""Technical quality control for rendered assets. Nothing is marked done without passing these."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from PIL import Image

PLATFORM_VIDEO_SPECS = {
    # (width, height, max_seconds) — conservative targets for organic posting
    "story": (1080, 1920, 90),
    "square": (1080, 1080, 60),
    "landscape": (1920, 1080, 600),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def probe(path: Path) -> dict:
    out = subprocess.run(  # noqa: S603,S607
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        capture_output=True, text=True, timeout=60, check=False)
    if out.returncode != 0:
        raise RuntimeError(out.stderr[-300:])
    return json.loads(out.stdout)


def check_video(path: Path, fmt: str, expect_audio: bool) -> dict:
    errors: list[str] = []
    if not path.exists() or path.stat().st_size < 10_000:
        return {"ok": False, "errors": ["missing or tiny file"]}
    info = probe(path)
    v = [s for s in info["streams"] if s["codec_type"] == "video"]
    a = [s for s in info["streams"] if s["codec_type"] == "audio"]
    w, h, max_s = PLATFORM_VIDEO_SPECS[fmt]
    dur = float(info["format"].get("duration", 0))
    if not v:
        errors.append("no video stream")
    else:
        vs = v[0]
        if (vs["width"], vs["height"]) != (w, h):
            errors.append(f"resolution {vs['width']}x{vs['height']} != {w}x{h}")
        if vs["codec_name"] != "h264":
            errors.append(f"codec {vs['codec_name']} != h264")
        if vs.get("pix_fmt") != "yuv420p":
            errors.append(f"pix_fmt {vs.get('pix_fmt')} != yuv420p (needed for broad playback)")
    if expect_audio and not a:
        errors.append("expected an audio stream")
    if a and a[0]["codec_name"] != "aac":
        errors.append("audio codec should be aac")
    if not 3 <= dur <= max_s:
        errors.append(f"duration {dur:.1f}s outside 3–{max_s}s")
    return {"ok": not errors, "errors": errors, "duration_s": round(dur, 2),
            "size_bytes": path.stat().st_size, "sha256": sha256(path)}


def check_image(path: Path, size: tuple[int, int]) -> dict:
    errors = []
    try:
        with Image.open(path) as im:
            im.verify()
        with Image.open(path) as im:
            if im.size != size:
                errors.append(f"size {im.size} != {size}")
            extrema = im.convert("L").getextrema()
            if extrema[1] - extrema[0] < 40:
                errors.append("image is nearly blank (low tonal range)")
    except Exception as e:  # noqa: BLE001 — any decode failure is a QC failure
        errors.append(f"unreadable: {e}")
    return {"ok": not errors, "errors": errors, "sha256": sha256(path) if path.exists() else None}


def extract_frame(video: Path, at_s: float, out: Path) -> Path:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{at_s:.2f}", "-i", str(video), "-frames:v", "1",  # noqa: S603,S607
                    str(out)], check=True, timeout=60)
    return out
