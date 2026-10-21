import shutil

import pytest
from PIL import Image

from mas.creative import graphics, qc, screenshots
from mas.creative.brand import Brand, contrast
from mas.creative.video import Scene, caption_chunks, render, write_srt

needs_ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
BRAND = Brand.from_profile("Acme", {"primary_color": "#0C2A21", "secondary_color": "#2C4C40", "accent_color": "#C0A46A"})


def test_brand_text_contrast_meets_wcag_aa():
    for colours in ({"primary_color": "#FFFFFF"}, {"primary_color": "#000000"}, {"primary_color": "#43192A"},
                    {"primary_color": "#E0E0E0", "accent_color": "#F0F0F0"}):
        b = Brand.from_profile("x", colours)
        assert contrast(b.text, b.bg) >= 4.5
        assert contrast(b.accent, b.bg) >= 3.0 or b.accent == b.text


def test_social_card_and_thumbnail(tmp_path):
    shot = Image.new("RGB", (1440, 900), (240, 240, 230))
    for size in ("portrait", "square", "story"):
        p = graphics.social_card(BRAND, "A reasonably long headline that has to wrap onto several lines",
                                 "Body copy.", "https://acme.example.co.uk", size, tmp_path / f"{size}.jpg",
                                 label="The problem", screenshot=shot)
        assert qc.check_image(p, graphics.SIZES[size])["ok"]
    t = graphics.thumbnail(BRAND, "Headline", tmp_path / "t.jpg", shot)
    assert qc.check_image(t, graphics.SIZES["thumbnail"])["ok"]


def test_qc_flags_blank_and_wrong_size(tmp_path):
    p = tmp_path / "blank.png"
    Image.new("RGB", (100, 100), (10, 10, 10)).save(p)
    r = qc.check_image(p, (200, 200))
    assert not r["ok"] and len(r["errors"]) == 2


def test_blank_screenshot_detection():
    assert screenshots.is_blank(Image.new("RGB", (100, 100), (243, 240, 233)))
    noisy = Image.effect_noise((100, 100), 60).convert("RGB")
    assert not screenshots.is_blank(noisy)


def test_caption_chunks_cover_span():
    c = caption_chunks("one two three four five six seven eight nine ten", 5.0, max_words=4)
    assert [x[2] for x in c] == ["one two three four", "five six seven eight", "nine ten"]
    assert c[0][0] == 0 and abs(c[-1][1] - 5.0) < 1e-9


@pytest.mark.media
@needs_ffmpeg
def test_render_video_meets_spec(tmp_path):
    scenes = [Scene("hook", "Acme", "Acme builds rotas.", 1.5), Scene("feature", "Swap shifts", "Staff swap shifts.", 1.5),
              Scene("cta", "acme.example.co.uk", "", 1.2)]
    out = render(scenes, BRAND, "square", tmp_path / "v.mp4")
    r = qc.check_video(out, "square", expect_audio=False)
    assert r["ok"], r
    assert abs(r["duration_s"] - 4.2) < 0.2
    srt = write_srt(scenes, tmp_path / "c.srt").read_text()
    assert "00:00:00" in srt and "Staff swap shifts." in srt
    frame = qc.extract_frame(out, 2.5, tmp_path / "f.png")
    assert not screenshots.is_blank(Image.open(frame))


@pytest.mark.media
@needs_ffmpeg
def test_qc_rejects_wrong_format(tmp_path):
    out = render([Scene("hook", "A", "", 3.2)], BRAND, "square", tmp_path / "v.mp4")
    assert not qc.check_video(out, "story", expect_audio=False)["ok"]
    assert not qc.check_video(out, "square", expect_audio=True)["ok"]


@pytest.mark.parametrize("url,ok", [
    ("https://acme.example.co.uk/", True),
    ("http://acme.example.co.uk/", False),
    ("https://evil.example.com/", False),
    ("https://user:pw@acme.example.co.uk/", False),
    ("https://acme.example.co.uk:8443/", False),
    ("file:///etc/passwd", False),
])
def test_screenshot_url_guard(url, ok):
    fake_resolve = lambda host, port: [(None, None, None, None, ("93.184.216.34", 443))]
    if ok:
        assert screenshots.check_url(url, {"acme.example.co.uk"}, resolve=fake_resolve)
    else:
        with pytest.raises(screenshots.UnsafeURL):
            screenshots.check_url(url, {"acme.example.co.uk"}, resolve=fake_resolve)


@pytest.mark.parametrize("ip", ["127.0.0.1", "10.0.0.5", "169.254.169.254", "192.168.1.1", "::1"])
def test_screenshot_guard_blocks_private_resolution(ip):
    with pytest.raises(screenshots.UnsafeURL):
        screenshots.check_url("https://acme.example.co.uk/", {"acme.example.co.uk"},
                              resolve=lambda h, p: [(None, None, None, None, (ip, 443))])
