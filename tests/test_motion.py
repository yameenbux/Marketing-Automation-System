import json
import re
import wave
from pathlib import Path

import pytest

from mas.creative import music

STYLES = Path(__file__).resolve().parents[1] / "src" / "mas" / "creative" / "motion" / "styles"
PRODUCTS = ["masjidone", "domi", "booked-in", "tidemark", "bolton-vouched"]


@pytest.mark.parametrize("slug", PRODUCTS)
def test_music_bed_length_and_level(tmp_path, slug):
    out = music.render(slug, 6.0, tmp_path / f"{slug}.wav")
    with wave.open(str(out)) as w:
        assert abs(w.getnframes() / w.getframerate() - 7.0) < 0.05   # +1s tail
        import numpy as np
        x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
    assert 0.5 < abs(x).max() / 32767 <= 0.81                         # normalised, never clipping
    assert x[:200].std() < x.std()                                      # fades in


def test_masjidone_has_no_musical_instruments():
    assert "masjidone" in music.COMPOSERS and music.COMPOSERS["masjidone"] is music.masjidone
    src = Path(music.__file__).read_text()
    body = src[src.index("def masjidone"):src.index("COMPOSERS =")]
    for instrument in ("pluck(", "fm(", "kick(", "chord_notes("):
        assert instrument not in body, f"masjidone ambience must not use {instrument}"


@pytest.mark.parametrize("slug", PRODUCTS)
def test_each_product_has_its_own_style_pack(slug):
    js, css = (STYLES / f"{slug}.js").read_text(), (STYLES / f"{slug}.css").read_text()
    assert "window.STYLE" in js and "transition:" in js
    for role in ("hook", "problem", "feature", "value", "cta"):
        assert re.search(rf"\b{role}: \{{", js), f"{slug} missing {role} scene"
    assert "--bg" in css and "--accent" in css


def test_style_packs_are_distinct():
    transitions, fonts = set(), set()
    for slug in PRODUCTS:
        js, css = (STYLES / f"{slug}.js").read_text(), (STYLES / f"{slug}.css").read_text()
        transitions.add(re.search(r'transition: "(\w+)"', js).group(1))
        fonts.add(re.search(r'\.headline[^{]*\{[^}]*?font(?:-family)?:[^;]*?"([^"]+)"', css).group(1))
    assert len(transitions) == 5, transitions
    assert len(fonts) == 5, fonts


def test_illustrative_scenes_are_labelled():
    for slug in PRODUCTS:
        js = (STYLES / f"{slug}.js").read_text()
        if slug != "masjidone":
            assert js.count("illus(cam)") >= 2, slug


def test_voices_are_distinct_and_licensed():
    from mas.creative.motion.film import VOICES
    keys = {(v["model"], v["speaker"]) for v in VOICES.values()}
    assert len(keys) == 5
    assert all(v["credit"] for v in VOICES.values())
    assert not any("semaine" in v["model"] for v in VOICES.values())   # CC BY-NC: never for marketing
