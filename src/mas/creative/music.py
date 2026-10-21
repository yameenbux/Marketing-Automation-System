"""Procedural, royalty-free music beds (numpy only). Our own compositions, so no licensing questions.

Each product gets a different instrument palette, tempo and harmony:
  domi           100 bpm  plucked arpeggios + felt pad + brushed hats          (calm, optimistic, clock-like)
  booked-in       84 bpm  FM electric piano 7th chords + finger snaps + sub    (lo-fi R&B, intimate)
  tidemark        60 bpm  swelling pads + heartbeat pulse + glass bells       (ambient, tidal)
  bolton-vouched 112 bpm  strummed acoustic (Karplus-Strong) + claps + horns  (indie-folk, community)
  masjidone        —      courtyard ambience only: breeze, birdsong, water   (no instruments, out of respect
                                                                              for audiences who avoid music)
"""
from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

SR = 44100


def midi(n: float) -> float:
    return 440.0 * 2 ** ((n - 69) / 12)


def env(n: int, a: float, d: float, s: float, r: float) -> np.ndarray:
    a_, d_, r_ = int(a * SR), int(d * SR), int(r * SR)
    sus = max(0, n - a_ - d_ - r_)
    e = np.concatenate([np.linspace(0, 1, max(a_, 1)), np.linspace(1, s, max(d_, 1)), np.full(sus, s),
                        np.linspace(s, 0, max(r_, 1))])
    return np.pad(e, (0, max(0, n - len(e))))[:n]


def fft_filter(x: np.ndarray, low: float | None = None, high: float | None = None) -> np.ndarray:
    """Gentle (1st-order-like) high/low-pass in the frequency domain."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR) + 1e-9
    g = np.ones_like(f)
    if high:
        g /= np.sqrt(1 + (f / high) ** 4)
    if low:
        g /= np.sqrt(1 + (low / f) ** 4)
    return np.fft.irfft(X * g, n=len(x))


def reverb(x: np.ndarray, seconds: float = 1.6, mix: float = 0.25, seed: int = 1) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    ir = rng.standard_normal(n) * np.exp(-np.linspace(0, 7, n))
    ir = fft_filter(ir, high=6000)
    ir /= np.sqrt(np.sum(ir ** 2)) + 1e-9
    L = len(x) + n
    wet = np.fft.irfft(np.fft.rfft(x, L) * np.fft.rfft(ir, L), n=L)[: len(x)]
    return (1 - mix) * x + mix * wet


def sine(f: float, n: int, phase: float = 0) -> np.ndarray:
    return np.sin(2 * np.pi * f * np.arange(n) / SR + phase)


def pluck(f: float, dur: float, decay: float = 0.996, seed: int = 0, bright: float = 0.5) -> np.ndarray:
    """Karplus-Strong plucked string, vectorised per period."""
    n, p = int(dur * SR), max(2, int(SR / f))
    rng = np.random.default_rng(seed)
    buf = rng.uniform(-1, 1, p)
    buf = bright * buf + (1 - bright) * np.convolve(buf, [0.5, 0.5], "same")
    out = np.empty(n)
    i = 0
    while i < n:
        k = min(p, n - i)
        out[i:i + k] = buf[:k]
        buf = decay * 0.5 * (buf + np.roll(buf, -1))
        i += k
    return out * env(n, 0.002, 0.05, 0.9, 0.08)


def fm(f: float, dur: float, ratio: float = 1.0, index: float = 2.0, a: float = .005, d: float = .4, s: float = .35,
       r: float = .4) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    idx = index * np.exp(-t * 3)
    return np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * ratio * t)) * env(n, a, d, s, r)


def noise_hit(dur: float, low: float, high: float, decay: float, seed: int) -> np.ndarray:
    n = int(dur * SR)
    x = np.random.default_rng(seed).standard_normal(n)
    return fft_filter(x, low=low, high=high) * np.exp(-np.arange(n) / SR * decay)


def kick(dur: float = .35, f0: float = 110, f1: float = 45) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    freq = f1 + (f0 - f1) * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-t * 9)


def place(track: np.ndarray, clip: np.ndarray, at: float, gain: float = 1.0) -> None:
    i = int(at * SR)
    if i >= len(track):
        return
    k = min(len(clip), len(track) - i)
    track[i:i + k] += clip[:k] * gain


def chord_notes(root: int, kind: str) -> list[int]:
    shapes = {"maj": [0, 4, 7], "min": [0, 3, 7], "maj7": [0, 4, 7, 11], "min7": [0, 3, 7, 10], "dom7": [0, 4, 7, 10],
              "maj9": [0, 4, 7, 11, 14], "min9": [0, 3, 7, 10, 14], "6": [0, 4, 7, 9]}
    return [root + i for i in shapes[kind]]


# ---------------------------------------------------------------- compositions
def domi(T: float) -> np.ndarray:
    bpm, out = 100, np.zeros(int(T * SR))
    beat = 60 / bpm
    prog = [(57, "min"), (53, "maj"), (60, "maj"), (55, "maj")]          # Am F C G
    bar = 4 * beat
    for b in range(int(T / bar) + 1):
        root, kind = prog[b % 4]
        notes = chord_notes(root, kind)
        t0 = b * bar
        pad = sum(sine(midi(n - 12), int(bar * SR)) * 0.6 + sine(midi(n - 12) * 1.003, int(bar * SR)) * 0.4 for n in notes)
        place(out, pad * env(int(bar * SR), .6, .3, .7, .6) * 0.07, t0)
        arp = notes + [notes[1] + 12]
        for k in range(8):                                                  # 8th-note arpeggio, clock-like
            n = arp[k % len(arp)] + 12
            place(out, pluck(midi(n), 0.9, 0.995, seed=b * 8 + k, bright=0.35), t0 + k * beat / 2, 0.22)
        place(out, sine(midi(root - 24), int(bar * SR)) * env(int(bar * SR), .02, .2, .6, .3), t0, 0.16)
        if b >= 2:
            for k in range(8):
                place(out, noise_hit(.08, 6000, 14000, 60, b * 100 + k), t0 + k * beat / 2 + beat / 4, 0.05)
    return reverb(out, 1.4, 0.22)


def booked_in(T: float) -> np.ndarray:
    bpm, out = 84, np.zeros(int(T * SR))
    beat = 60 / bpm
    prog = [(62, "maj7"), (59, "min7"), (55, "maj7"), (57, "dom7")]       # Dmaj7 Bm7 Gmaj7 A7
    bar = 4 * beat
    rng = np.random.default_rng(4)
    for b in range(int(T / bar) + 1):
        root, kind = prog[b % 4]
        t0 = b * bar
        for k, hit in enumerate([0, 1.5, 2.5]):                           # lazy, syncopated Rhodes comping
            for j, n in enumerate(chord_notes(root, kind)):
                place(out, fm(midi(n - 12), 1.6, 1.0, 1.4, d=.6, s=.25, r=.6), t0 + hit * beat + j * 0.012, 0.08)
        place(out, fm(midi(root - 24), bar, 0.5, 0.6, a=.01, d=.3, s=.5, r=.3), t0, 0.22)    # round sub
        for k in (1, 3):
            place(out, noise_hit(.12, 1500, 5000, 45, b * 10 + k), t0 + k * beat, 0.32)   # finger snaps
        for k in (0, 2.5):
            place(out, kick(.3, 90, 45), t0 + k * beat, 0.35)
    crackle = np.zeros_like(out)
    for i in rng.integers(0, len(out), int(T * 9)):
        crackle[i] = rng.uniform(-1, 1)
    out += fft_filter(crackle, low=1000) * 0.15 + fft_filter(rng.standard_normal(len(out)), low=2000) * 0.004
    return reverb(out, 1.0, 0.15)


def tidemark(T: float) -> np.ndarray:
    out = np.zeros(int(T * SR))
    prog = [(60, "maj9"), (57, "min9"), (53, "maj9"), (55, "6")]
    span = 8.0
    for b in range(int(T / span) + 1):
        root, kind = prog[b % 4]
        n = int(span * 1.25 * SR)
        pad = sum(sine(midi(x - 12), n) + 0.5 * sine(midi(x - 12) * 2.002, n) for x in chord_notes(root, kind))
        swell = np.sin(np.linspace(0, np.pi, n)) ** 2                    # in and out, like a tide
        place(out, pad * swell * 0.05, b * span)
    beat = 1.0                                                           # 60 bpm heartbeat, felt more than heard
    for k in range(int(T / beat)):
        place(out, kick(.4, 70, 38), k * beat, 0.22)
        place(out, kick(.3, 60, 36), k * beat + 0.22, 0.12)
    bells = [72, 76, 79, 84, 81, 79]
    for k, n in enumerate(bells * 4):
        at = 4 + k * 2.75
        if at < T - 2:
            place(out, fm(midi(n), 3.0, 3.5, 2.5, a=.002, d=1.5, s=.1, r=1.2), at, 0.05)
    return reverb(out, 2.6, 0.35)


def bolton(T: float) -> np.ndarray:
    bpm, out = 112, np.zeros(int(T * SR))
    beat = 60 / bpm
    prog = [(55, "maj"), (60, "maj"), (62, "maj"), (52, "min")]          # G C D Em
    bar = 4 * beat
    pattern = [(0, 1), (1, 1), (1.5, -1), (2.5, -1), (3, 1), (3.5, -1)]   # D D U U D U
    for b in range(int(T / bar) + 1):
        root, kind = prog[b % 4]
        voicing = [root - 12, root - 5] + chord_notes(root, kind) + [root + 12]
        t0 = b * bar
        for k, (pos, direction) in enumerate(pattern):
            strings = voicing if direction > 0 else voicing[::-1][:4]
            for j, n in enumerate(strings):                              # strum: strings 12 ms apart
                place(out, pluck(midi(n), 1.2, 0.994, seed=b * 50 + k * 7 + j, bright=0.7), t0 + pos * beat + j * 0.012,
                      0.07 if direction > 0 else 0.045)
        for k in (0, 2):
            place(out, kick(.3, 100, 48), t0 + k * beat, 0.45)
        for k in (1, 3):
            place(out, sum(noise_hit(.14, 900, 4500, 30, b * 20 + k + s) for s in range(3)) / 2, t0 + k * beat, 0.25)
        if b >= 4 and b % 2 == 0:                                         # warm horn stabs in the second half
            n = int(1.4 * SR)
            horn = sum(np.sign(sine(midi(x), n)) * 0.3 + sine(midi(x), n) for x in chord_notes(root, kind))
            place(out, fft_filter(horn, high=1800) * env(n, .06, .3, .5, .5), t0 + 2 * beat, 0.05)
    return reverb(out, 1.2, 0.18)


def masjidone(T: float, field_recording: Path | None = None) -> np.ndarray:
    n = int(T * SR)
    rng = np.random.default_rng(11)
    wind = np.cumsum(rng.standard_normal(n))                             # brown noise breeze
    wind = fft_filter(wind - np.convolve(wind, np.ones(4410) / 4410, "same"), low=80, high=900)
    wind /= np.abs(wind).max() + 1e-9
    wind *= 0.5 + 0.5 * np.sin(2 * np.pi * np.arange(n) / SR / 9.0) ** 2
    water = fft_filter(rng.standard_normal(n), low=1500, high=6000) * (0.6 + 0.4 * np.abs(np.sin(np.arange(n) / SR * 13)))
    out = wind * 0.12 + water * 0.012
    for at in rng.uniform(2, T - 2, int(T / 4)):                          # distant birdsong chirps
        k = int(0.18 * SR)
        f = np.linspace(rng.uniform(2800, 3600), rng.uniform(3800, 5200), k)
        chirp = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.linspace(0, np.pi, k)) ** 2
        for rep in range(rng.integers(1, 4)):
            place(out, chirp, at + rep * 0.22, 0.03)
    if field_recording and field_recording.exists():                     # the ElevenLabs courtyard clip, looped
        try:
            import subprocess
            raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(field_recording), "-f", "f32le", "-ac", "1",  # noqa: S603,S607
                                  "-ar", str(SR), "-"], capture_output=True, check=True).stdout
            clip = np.frombuffer(raw, dtype=np.float32).astype(float)
            fade = min(len(clip) // 4, int(0.3 * SR))
            ramp = np.linspace(0, 1, fade)
            step = len(clip) - fade
            for start in range(0, n, step):
                c = clip.copy()
                c[:fade] *= ramp
                c[-fade:] *= ramp[::-1]
                place(out, c, start / SR, 0.25)
        except Exception:  # noqa: BLE001 — ambience is optional
            pass
    return reverb(out, 2.0, 0.3)


COMPOSERS = {"domi": domi, "booked-in": booked_in, "tidemark": tidemark, "bolton-vouched": bolton, "masjidone": masjidone}


def render(slug: str, seconds: float, out: Path, field_recording: Path | None = None) -> Path:
    T = seconds + 1.0
    x = masjidone(T, field_recording) if slug == "masjidone" else COMPOSERS[slug](T)
    fade = int(2.0 * SR)
    x[:int(0.4 * SR)] *= np.linspace(0, 1, int(0.4 * SR))
    x[-fade:] *= np.linspace(1, 0, fade)
    x = x / (np.abs(x).max() + 1e-9) * 0.8
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return out
