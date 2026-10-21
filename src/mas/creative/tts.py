"""Narration via Piper (local, free, offline).

Licence caution: the en_GB 'alba' voice's dataset is CC BY 4.0 (attribution
required), but the model is fine-tuned from the 'lessac' voice whose source data
was released for research. Treat Piper narration as *draft* audio until you're
satisfied with the licensing, or swap in a voice you hold commercial rights to
(e.g. ElevenLabs on a paid plan, or your own recorded voice).
"""
from __future__ import annotations

import subprocess
import sys
import wave
from pathlib import Path

from ..policy import Action, Policy

DEFAULT_VOICE = Path(__file__).resolve().parents[3] / "models" / "piper" / "en_GB-alba-medium.onnx"
VOICE_CREDIT = ("Narration: Piper TTS (MIT/GPL, rhasspy) with the en_GB 'alba' voice — dataset © University of "
                "Edinburgh, CC BY 4.0 (https://datashare.ed.ac.uk/handle/10283/3270). Model fine-tuned from the "
                "'lessac' voice; confirm commercial-use terms before publishing.")


def available(voice: Path = DEFAULT_VOICE) -> bool:
    try:
        import piper  # noqa: F401
    except ImportError:
        return False
    return voice.exists()


def synthesize(policy: Policy, text: str, out: Path, voice: Path = DEFAULT_VOICE, speaker: int | None = None,
               length_scale: float | None = None) -> Path | None:
    if not available(voice):
        return None
    if not policy.authorize(Action.SYNTH_AUDIO, "piper_tts", detail={"chars": len(text)}).allowed:
        return None
    out.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(  # noqa: S603 — fixed argv; text goes via stdin, never the command line
        [sys.executable, "-m", "piper", "-m", str(voice), "-f", str(out)]
        + (["-s", str(int(speaker))] if speaker is not None else [])
        + (["--length-scale", f"{float(length_scale):.3f}"] if length_scale else []),
        input=text, text=True, capture_output=True, timeout=120, check=False)
    if proc.returncode != 0 or not out.exists():
        raise RuntimeError(f"piper failed: {proc.stderr[-400:]}")
    return out


def wav_duration(path: Path) -> float:
    with wave.open(str(path)) as w:
        return w.getnframes() / float(w.getframerate())


def concat_with_gaps(parts: list[tuple[Path | None, float]], out: Path, rate: int = 22050) -> Path:
    """Lay each clip at the start of its slot; slot length is in seconds. None = silence."""
    frames = bytearray()
    params = None
    for clip, slot in parts:
        slot_frames = int(slot * rate)
        data = b""
        if clip is not None:
            with wave.open(str(clip)) as w:
                params = params or w.getparams()
                if w.getframerate() != rate or w.getnchannels() != 1 or w.getsampwidth() != 2:
                    raise ValueError("unexpected wav format")
                data = w.readframes(w.getnframes())
        data = data[: slot_frames * 2]
        frames += data + b"\x00\x00" * (slot_frames - len(data) // 2)
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(frames))
    return out
