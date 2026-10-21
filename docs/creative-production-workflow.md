# Creative production workflow

There are two renderers:

| | `mas film <product>`: **cinematic (primary)** | `mas campaign <product>`: template pack |
|---|---|---|
| Look | A distinct art direction per product | One shared template |
| Engine | HTML/CSS/SVG timeline captured frame by frame in Chromium | Pillow frames |
| Output | 9:16, 1:1, 16:9 films + 4:5 carousel stills | 3 videos + cards + carousel + copy pack |

## Art directions (`src/mas/creative/motion/styles/`)

| Product | Concept | Type | Signature motion | Transition | Camera and texture | Voice | Score |
|---|---|---|---|---|---|---|---|
| MasjidOne | Lantern & lattice | Marcellus + Instrument Sans | 8-point *khatam* lattice draws itself, then becomes a window onto the real site | lattice iris | crane, lamp-glow leaks, grain | VCTK p226 | **no music**: courtyard ambience (breeze, birdsong, water), out of respect for audiences who avoid music |
| Domi | The round | IBM Plex Sans Condensed + Plex Mono | cancelled slot struck through → route line across the map → CANCEL text → slot refilled | route-line wipe | drone drift, handheld | Alba | 100 bpm plucked arpeggios |
| Booked In | Link in bio | Bodoni Moda italic + Jost | late-night DMs pile up and fade to "Seen" → Save → Live → one slot, two clients, one booking | bloom flash | rack-focus bokeh, push-ins | Cori | 84 bpm lo-fi electric piano and snaps |
| Tidemark | Signal from noise | Manrope + JetBrains Mono | noisy weigh-ins → Holt trend glides through, moving average lags | tide-wave wipe | lateral dolly, sine waves | VCTK p232 | 60 bpm tidal pads, heartbeat, bells |
| Bolton Vouched | Shopfront signwriting | Alfa Slab One + Work Sans | shutter rolls up on a signwritten sign → group-chat asks scroll away → 43 counter + 7 group stamps → £ coin bounces off the list | roller shutter | handheld, stamp-impact shake, brick bond | Northern English male | 112 bpm strummed folk, claps, horns |

Rules every style follows:
- **Words on screen come from verified facts.** Scripts are validated before rendering.
- **Real UI only from the product's own site** (Playwright, SSRF-guarded). Bolton Vouched screenshots are disabled
  because live listings show real traders.
- **Dramatised scenes are labelled "Illustration"** (chats, DMs, diaries, charts, maps).
- **No fake UI presented as real, no fake customers, no outcome claims.** Tidemark's illustrative chart is
  deliberately near-level, so it implies no weight-loss result.
- Long headlines auto-fit the space above the visual. Captions are burned in, and the audio is loudness-normalised
  to −16 LUFS with the music ducked under the voice.

## Connectors: what was attempted (21 Oct 2026)

| Connector | Attempted | Result |
|---|---|---|
| ElevenLabs | 5 narrations, 4 music beds, 1 ambience, 5 stills | **Quota exhausted** (47 credits left of 31,105). Only the ambience succeeded (~17 credits), and it's mixed into the MasjidOne bed |
| Canva | 5 AI images | **Credit quota exceeded**, nothing generated |
| Figma | — | View seat on Starter, can't create |

Everything planned for those connectors is produced locally instead (Piper voices, procedural music, procedural
visuals). Top up ElevenLabs to replace the voices: the voice IDs chosen per product are listed in
`docs/integration-gaps.md`.

## Cost per film

£0 local, plus whatever you choose to spend on connectors. CPU time is about 0.25 s per 1080p frame, so a 36-second
film takes about 5 minutes per format.

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
