"""Workflow B (creative) — turn a verified product profile into a campaign asset pack.

assets/<product>/<campaign_id>/
  brief.md, script.md, script.json, storyboard.md, storyboard.png, prompts.md, copy.md,
  captions_<fmt>.srt, video_<fmt>.mp4, motion_logo_sting.mp4, thumbnail.jpg, card_*.jpg, carousel_*.jpg,
  source/ (screenshots), manifest.json, qc.json, LICENCES.md

Idempotent: if manifest.json records the same input hash and every QC check
passed, nothing is regenerated.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from ..context import Context
from ..marketing.validator import validate
from ..marketing.writer import TemplateWriter
from ..policy import Action
from ..products.profile import Profile, load_profile
from ..store import now_iso
from . import graphics, qc, screenshots, tts
from .brand import Brand
from .video import FORMATS, Scene, render, write_srt

MIN_SCENE = {"hook": 3.0, "cta": 3.2}


@dataclass
class CampaignResult:
    campaign_id: str
    path: Path
    skipped: bool
    qc_ok: bool
    files: list[str]
    notes: list[str]


def campaign_id(slug: str, objective: str, date: str) -> str:
    return f"{slug}-{date}-{hashlib.sha256(objective.encode()).hexdigest()[:6]}"


def _input_hash(profile: Profile, script: dict, formats: list[str], narration: bool) -> str:
    payload = json.dumps({"facts": [(f.id, f.text, f.status) for f in profile.facts], "brand": profile.brand,
                          "script": script, "formats": formats, "narration": narration, "v": 3}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def product_urls(profile: Profile) -> list[str]:
    from ..marketing.writer import _first_url
    urls = []
    for f in profile.by_kind("url") + profile.by_kind("cta"):
        u = _first_url(f.quote) or _first_url(f.text)
        if u and u not in urls:
            urls.append(u)
    return urls


def produce_campaign(ctx: Context, slug: str, objective: str, formats: list[str] | None = None,
                     narration: bool = True, capture: bool = True, force: bool = False) -> CampaignResult:
    formats = formats or ["story", "square", "landscape"]
    if ctx.policy.kill_switch_active():
        raise PermissionError("kill switch is active")
    prof = load_profile(ctx.root, slug)
    brand = Brand.from_profile(prof.name, prof.brand)
    writer = TemplateWriter()
    date = ctx.policy.london_now().date().isoformat()
    cid = campaign_id(slug, objective, date)
    out = ctx.root / "assets" / slug / cid
    out.mkdir(parents=True, exist_ok=True)
    notes: list[str] = []

    # 1–2. Script from verified facts, validated *before* any rendering.
    script = writer.video_script(prof, seconds=30)
    full_text = "\n".join(s["narration"] + " " + s["on_screen"] for s in script.meta["scenes"])
    v = validate(full_text, product=prof, platform="blog", fact_ids=script.fact_ids)
    if not v.ok:
        raise ValueError(f"script failed validation: {v.errors}")

    ih = _input_hash(prof, script.meta, formats, narration)
    manifest_path = out / "manifest.json"
    if manifest_path.exists() and not force:
        old = json.loads(manifest_path.read_text())
        if old.get("input_hash") == ih and old.get("qc_ok"):
            return CampaignResult(cid, out, True, True, old["files"], ["unchanged inputs; reused QC-passed assets"])

    # 3. Brief, script, storyboard text, prompts, social copy.
    posts = []
    for platform, pillar in (("instagram", "problem_solution"), ("linkedin", "how_it_works"), ("x", "feature_spotlight")):
        d = writer.social_post(prof, platform, pillar)
        if d:
            r = validate(d.text, product=prof, platform=platform, fact_ids=d.fact_ids)
            content_id, _ = ctx.store.add_content(product=slug, kind="social_post", platform=platform,
                                                  body=d.body() | {"campaign_id": cid}, fingerprint=d.fingerprint(),
                                                  campaign_id=cid)
            from ..workflows import validate_content   # records validated/rejected status on the item
            validate_content(ctx, content_id)
            posts.append((platform, d, r, content_id))
    _write_docs(out, prof, objective, cid, script, posts, brand)

    # 4. Source visuals: screenshots of the product's own public site.
    shots: dict[str, Image.Image] = {}
    urls = product_urls(prof)
    hosts = {u.split("/")[2] for u in urls}
    from ..github_sync.sync import load_registry
    reg_entry = next((e for e in load_registry(ctx.root)["products"] if e["slug"] == slug), {})
    if capture and reg_entry.get("screenshots") is False:
        capture = False
        notes.append("screenshots disabled for this product: " + reg_entry.get("screenshots_note", "see registry"))
    if capture and urls and ctx.settings.integration_enabled("playwright_screenshots"):
        try:
            desk = screenshots.capture(ctx.policy, urls[0], out / "source" / "site_desktop.png", hosts,
                                       scroll_sections=6)
            mob = screenshots.capture(ctx.policy, urls[0], out / "source" / "site_mobile.png", hosts, mobile=True)
            if desk:
                shots["hero"] = Image.open(desk[0]).convert("RGB")
                usable = [Image.open(p).convert("RGB") for p in desk[1:]]
                usable = [im for im in usable if not screenshots.is_blank(im)]
                skipped = len(desk) - 1 - len(usable)
                if skipped:
                    notes.append(f"{skipped} near-blank page section(s) discarded")
                for i, im in enumerate(usable[:3]):   # different sections of the page for each feature scene
                    shots[f"section{i}"] = im
            if mob and not screenshots.is_blank(Image.open(mob[0])):
                shots["mobile"] = Image.open(mob[0]).convert("RGB")
            notes.append("screenshots captured from " + urls[0] +
                         " — page sections are not matched to claims; review that visuals fit the narration")
        except Exception as e:  # noqa: BLE001 — degrade to text-only visuals
            notes.append(f"screenshot capture failed ({e}); rendering text-only scenes")
    elif not urls:
        notes.append("no verified product URL — text-only visuals")

    # 5. Narration (local Piper), one clip per scene so timing is exact.
    scenes_meta = script.meta["scenes"]
    clips: list[Path | None] = []
    if narration and tts.available():
        for i, s in enumerate(scenes_meta):
            clips.append(tts.synthesize(ctx.policy, s["narration"], out / "audio" / f"scene_{i + 1:02d}.wav"))
    else:
        clips = [None] * len(scenes_meta)
        if narration:
            notes.append("Piper not available — rendering without narration")

    def build_scenes(fmt: str) -> list[Scene]:
        scenes, feat_i = [], 0
        for s, clip in zip(scenes_meta, clips):
            speech = tts.wav_duration(clip) if clip else None
            dur = max(MIN_SCENE.get(s["role"], 3.5), (speech or 0) + 0.8, 2.5)
            shot = None
            if s["role"] == "problem":
                shot = shots.get("mobile") if fmt == "story" else shots.get("hero")
            elif s["role"] == "feature":
                shot = shots.get(f"section{feat_i}") if fmt != "story" else (shots.get(f"section{feat_i}") or shots.get("mobile"))
                feat_i += 1
            elif s["role"] == "value":
                shot = shots.get("hero")
            scenes.append(Scene(s["role"], s["on_screen"], s["narration"], round(dur, 2), shot, speech))
        return scenes

    files: list[str] = []
    qc_results: dict[str, dict] = {}
    keyframes: dict[int, Path] = {}

    audio_mix = None
    base_scenes = build_scenes("story")
    if any(clips):
        audio_mix = tts.concat_with_gaps([(c, s.duration) for c, s in zip(clips, base_scenes)], out / "audio" / "narration.wav")

    # 6–8. Render each format (policy-gated: counts against the daily render limit).
    for fmt in formats:
        if not ctx.policy.authorize(Action.RENDER, "local_render", detail={"campaign": cid, "fmt": fmt}).allowed:
            notes.append(f"render of {fmt} blocked by policy (limit or kill switch)")
            (out / f"video_{fmt}.mp4").unlink(missing_ok=True)       # never leave a stale render behind
            (out / f"captions_{fmt}.srt").unlink(missing_ok=True)
            qc_results[f"video_{fmt}.mp4"] = {"ok": False, "errors": ["not rendered (blocked by policy)"]}
            continue
        scenes = build_scenes(fmt)
        vid = render(scenes, brand, fmt, out / f"video_{fmt}.mp4", audio_mix,
                     keyframes=keyframes if fmt == "story" else None)
        srt = write_srt(scenes, out / f"captions_{fmt}.srt")
        qc_results[vid.name] = qc.check_video(vid, fmt, expect_audio=audio_mix is not None)
        files += [vid.name, srt.name]

    # Motion sample: a standalone animated logo sting (square, silent).
    if ctx.policy.authorize(Action.RENDER, "local_render", detail={"campaign": cid, "fmt": "sting"}).allowed:
        sting = render([Scene("hook", prof.name, "", 3.2)], brand, "square", out / "motion_logo_sting.mp4")
        qc_results[sting.name] = qc.check_video(sting, "square", expect_audio=False)
        files.append(sting.name)

    # Storyboard contact sheet from real rendered keyframes.
    if keyframes:
        frames = [(scenes_meta[i]["role"] + ": " + scenes_meta[i]["on_screen"], Image.open(p))
                  for i, p in sorted(keyframes.items())]
        graphics.contact_sheet(frames, out / "storyboard.png")
        files.append("storyboard.png")
        for p in keyframes.values():
            p.unlink(missing_ok=True)

    # Static graphics.
    head = scenes_meta[1]["on_screen"] if len(scenes_meta) > 1 else prof.name
    cta = next((s["on_screen"] for s in scenes_meta if s["role"] == "cta"), prof.name)
    graphics.thumbnail(brand, head, out / "thumbnail.jpg", shots.get("hero"))
    qc_results["thumbnail.jpg"] = qc.check_image(out / "thumbnail.jpg", graphics.SIZES["thumbnail"])
    files.append("thumbnail.jpg")
    if posts:
        platform, d, _, _ = posts[0]
        first = prof.fact(d.fact_ids[0])
        for size in ("portrait", "square", "story"):
            p = graphics.social_card(brand, first.text if first else head, "", cta, size, out / f"card_{size}.jpg",
                                     label=ROLE(first.kind) if first else None, screenshot=shots.get("hero"))
            qc_results[p.name] = qc.check_image(p, graphics.SIZES[size])
            files.append(p.name)
    for i, f in enumerate(prof.by_kind("feature")[:3], 1):
        p = graphics.social_card(brand, f.text, "", f"{i}/3 · {cta}", "portrait", out / f"carousel_{i}.jpg",
                                 label="How it helps")
        qc_results[p.name] = qc.check_image(p, graphics.SIZES["portrait"])
        files.append(p.name)

    qc_ok = all(r.get("ok") for r in qc_results.values()) and bool(qc_results)
    (out / "qc.json").write_text(json.dumps({"checked_at": now_iso(), "ok": qc_ok, "brand_contrast": brand.checks(),
                                             "results": qc_results, "copy_validation": {
                                                 p: r.as_dict() for p, _, r, _ in posts}}, indent=2))
    _write_licences(out, bool(any(clips)), bool(shots))
    manifest = {"campaign_id": cid, "product": slug, "objective": objective, "created_at": now_iso(),
                "input_hash": ih, "profile_commit": _profile_commit(ctx, slug), "qc_ok": qc_ok,
                "status": "draft — unpublished, awaiting human review",
                "fact_ids": script.fact_ids, "files": files + ["brief.md", "script.md", "script.json",
                                                                "storyboard.md", "prompts.md", "copy.md", "qc.json",
                                                                "LICENCES.md"],
                "content_ids": [c for *_, c in posts], "notes": notes,
                "cost_gbp": 0.0, "cost_note": "local rendering and local TTS — no paid APIs used"}
    manifest_path.write_text(json.dumps(manifest, indent=2))
    with ctx.store.tx() as c:
        c.execute("INSERT OR IGNORE INTO campaigns(id, product, objective, status, created_at, data) VALUES (?,?,?,?,?,?)",
                  (cid, slug, objective, "draft", now_iso(), json.dumps({"path": str(out)})))
    return CampaignResult(cid, out, False, qc_ok, manifest["files"], notes)


def ROLE(kind: str) -> str:  # noqa: N802 — small label helper
    return {"pain_point": "The problem", "feature": "How it helps", "value_prop": "Why it matters",
            "privacy": "Your data", "overview": "Introducing"}.get(kind, "")


def _profile_commit(ctx: Context, slug: str) -> str | None:
    p = ctx.root / "data" / "products" / slug / "sources" / "_sync.json"
    return json.loads(p.read_text()).get("commit") if p.exists() else None


def _write_docs(out: Path, prof: Profile, objective: str, cid: str, script, posts, brand: Brand) -> None:
    aud = "\n".join(f"- {f.text} `[{f.id}]`" for f in prof.by_kind("audience")) or "- (no audience facts)"
    lim = "\n".join(f"- {f.text}" for f in prof.limitations()) or "- none recorded"
    (out / "brief.md").write_text(f"""# Creative brief — {prof.name}

**Campaign:** `{cid}`  **Objective:** {objective}
**Status:** draft — not published. Needs human review of copy, visuals and narration.

## Audience (from verified facts)
{aud}

## Single-minded message
{script.meta['scenes'][0]['narration']}

## Call to action
{next((s['on_screen'] for s in script.meta['scenes'] if s['role'] == 'cta'), '')}

## Must not say (known limitations — never imply these are done)
{lim}

## Visual direction
Brand background {brand.bg}, accent {brand.accent}, Inter Display headlines, real screenshots of the product's own
public site, word-by-word kinetic headlines, burned-in captions (most social video is watched muted).

## Formats
9:16 (Reels/Shorts/TikTok/Stories), 1:1 (feed), 16:9 (YouTube/LinkedIn/web), plus stills and a 3-slide carousel.

## Success measure
Profile visits / link clicks / demo requests attributable to the post (UTM-tag the link when publishing).
""", encoding="utf-8")
    (out / "script.json").write_text(json.dumps(script.meta, indent=2, ensure_ascii=False))
    (out / "script.md").write_text(f"# Script — {prof.name}\n\n" + "\n".join(
        f"**{i}. {s['role'].upper()}** (~{s['seconds']}s, fact `{s['fact_id']}`)\n\n- On screen: {s['on_screen']}\n"
        f"- Voice-over: {s['narration']}\n" for i, s in enumerate(script.meta["scenes"], 1)), encoding="utf-8")
    (out / "storyboard.md").write_text(f"# Storyboard — {prof.name}\n\nKeyframes: `storyboard.png` (rendered).\n\n" + "\n".join(
        f"| {i} | {s['role']} | {s['on_screen']} | "
        f"{'kinetic headline + screenshot card slides up' if s['role'] in ('problem', 'feature', 'value') else 'logo animation' if s['role'] == 'hook' else 'end card'} | captions |"
        for i, s in enumerate(script.meta["scenes"], 1)), encoding="utf-8")
    (out / "prompts.md").write_text(f"""# Optional generative prompts (NOT executed — each costs credits)

These are for the connected ElevenLabs / Canva tools if you choose to spend credits. The local pipeline
did not use them.

- Background music (ElevenLabs Music, instrumental, ~35s): "Calm, modern, understated instrumental bed for a
  software explainer; soft piano and light percussion; no vocals; steady 90 bpm."
- Narration (ElevenLabs TTS): use `script.md` voice-over lines verbatim; British English; neutral, warm.
- Hero image (ElevenLabs/Canva image): "Abstract editorial illustration in {'#%02x%02x%02x' % brand.bg} and
  {'#%02x%02x%02x' % brand.accent}, calm geometric shapes, lots of negative space, no text, no people, no logos."
  Never generate fake UI, fake customers or fake screenshots of the product.
""", encoding="utf-8")
    copy = [f"# Social copy — {prof.name}\n"]
    for platform, d, r, content_id in posts:
        copy.append(f"## {platform} (`{content_id}`, validation: {'PASS' if r.ok else 'FAIL'})\n\n```\n{d.text}\n```\n"
                    f"Facts: {', '.join(d.fact_ids)}\n" + (f"Errors: {r.errors}\n" if r.errors else ""))
    (out / "copy.md").write_text("\n".join(copy), encoding="utf-8")


def _write_licences(out: Path, narration: bool, screenshots_used: bool) -> None:
    lines = ["# Licences and attribution", "",
             "- Fonts: Inter / Inter Display — SIL Open Font License 1.1 (rsms.me/inter).",
             "- Rendering: FFmpeg (LGPL/GPL build), Pillow (HPND). Output is our own work.",
             "- Music: none used. Add only tracks you hold a licence for."]
    if narration:
        lines.append(f"- {tts.VOICE_CREDIT}")
    if screenshots_used:
        lines.append("- Screenshots: captured from the product's own public website (owned by YSB). "
                     "Check they show no real customer or personal data before publishing.")
    (out / "LICENCES.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
