# Creative production workflow

```
mas campaign masjidone --objective "Introduce MasjidOne to UK masjid committees and drive demo requests"
```

| Step | What happens | Tool | Cost |
|---|---|---|---|
| 1 | Load the profile; every fact re-verified against the synced README | `products/profile.py` | £0 |
| 2 | Script: hook → problem → 2 features → value → CTA, one scene per fact | `writer.video_script` | £0 |
| 3 | **Validate the script before rendering** (aborts on any error) | `validator.py` | £0 |
| 4 | Brief, storyboard table, optional generative prompts, social copy (validated and stored as content) | `pipeline._write_docs` | £0 |
| 5 | Screenshots of the product's own site: desktop hero, 6 scrolled sections (near-blank ones discarded), mobile | Playwright (SSRF-guarded) | £0 |
| 6 | Narration, one clip per scene so captions sync exactly | Piper, en_GB alba | £0 |
| 7 | Frames: kinetic word-by-word headlines, screenshot cards sliding in, burned-in captions, crossfades, progress bar | Pillow | £0 |
| 8 | Encode to H.264 / yuv420p / AAC with faststart, at 9:16, 1:1 and 16:9 | FFmpeg | £0 |
| 9 | Logo sting (motion sample), storyboard sheet from real keyframes, thumbnail, 3 cards, 3-slide carousel | Pillow / FFmpeg | £0 |
| 10 | QC: resolution, codec, pixel format, audio present, duration window, file hashes, blank-image detection, WCAG contrast | `qc.py` | £0 |
| 11 | `manifest.json` with input hash, so unchanged inputs are never re-rendered | `pipeline.py` | £0 |

**Cost per finished campaign pack: £0** (≈2.5–3 minutes of CPU on 4 cores for 3 video formats plus 8 stills).

## Output: `assets/<product>/<campaign_id>/`

`brief.md` · `script.md` / `script.json` · `storyboard.md` / `storyboard.png` · `prompts.md` · `copy.md` ·
`video_{story,square,landscape}.mp4` · `captions_*.srt` · `motion_logo_sting.mp4` · `thumbnail.jpg` ·
`card_{portrait,square,story}.jpg` · `carousel_{1,2,3}.jpg` · `source/` (screenshots) · `audio/` (narration) ·
`qc.json` · `manifest.json` · `LICENCES.md`

MP4 and WAV files are gitignored. They're regenerable, and this repo is currently public.

## Honest quality notes on the sample (MasjidOne)

- **Length: 41.5s** against a 30s target. The narration is the full verified sentences. Tighter copy is a
  human or LLM job; the renderer simply follows the script.
- **Screenshot sections aren't matched to claims.** Scenes 3–4 show the site's hero mid-scroll-animation.
  Better: capture specific pages (e.g. `/demo/`) per feature. That's a small change once you choose which pages.
- **Narration voice** is serviceable but synthetic, and its licence is unclear for commercial use (see LICENCES.md).
- No music.

## Using the paid connectors (optional, credits)

The ElevenLabs connector can replace step 6 (a better voice), add music or SFX, or generate AI B-roll (Veo, Kling).
Those calls must be made from a Claude session; this Python process can't reach connectors. The prompts are in
`prompts.md`. **Never generate fake UI, fake customers or fake testimonials.** Generated imagery is for abstract
backgrounds only.

## Not implemented

Lottie export; music; avatar or lip-sync video; automatic matching of a screenshot to the specific claim narrated.
