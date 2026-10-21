# Final report (master prompt §16)

**As of 21 Oct 2026.** Status labels: **✅ implemented and tested** · **🟡 partially implemented** ·
**🔒 awaiting your authorisation or action** · **❌ not available**. Nothing below is claimed from a plan or a mock
unless it says so.

## 1. Environment audit
Full detail: [capability-audit.md](capability-audit.md), [`config/capabilities.json`](../config/capabilities.json).

| Capability | Status |
|---|---|
| Python 3.13, FFmpeg 6.1, Pillow, headless Chromium (Playwright 1.56), Piper TTS (4 British voices) | ✅ used to render every asset in this repo |
| Public GitHub sync (raw + `git ls-remote`; REST API with retries/ETag/pagination where the network allows) | ✅ 5 product repos synced with commit SHAs |
| Metricool connector (brand YBTweetss → Instagram `masjidone.uk`) | ✅ read verified · 🔒 writes only from the morning run (see §4) |
| Claude artifacts (approval desk with shared database) | ✅ published and verified |
| Scheduled tasks (claude.ai) | ✅ two weekday runs created · 🔒 they receive **no connectors** until you add Metricool in the scheduled-task settings |
| Google Sheets / Drive | ✅ private lead sheet created; only you have access |
| Exa / WebSearch / WebFetch (research) | ✅ used for lead research |
| ElevenLabs | 🟡 connected, credits exhausted (one 2 s SFX produced) |
| Canva | 🟡 connected, AI credits exhausted |
| Figma | 🟡 View seat only; can read, can't create |
| Buffer, HubSpot, n8n | ❌ not connected / not installed in this environment |
| Docker | 🟡 Dockerfile and compose written; no daemon here, so untested |
| Claude Desktop local skills | ❌ not visible from a cloud session (see capability-audit.md for how to add them) |

## 2. Architecture
See [architecture.md](architecture.md). One Python package (`mas`) with a CLI and SQLite, one policy gate
(`Policy.authorize`) that every side effect must pass (kill switch, per-integration switch, dry-run, live flags,
daily and monthly limits, budget, audit). The eight roles in §4 of the prompt map to modules:

| Role | Module | Status |
|---|---|---|
| A Marketing strategist | `marketing/planner.py`, `marketing/calendar.py`, `docs/portfolio-strategy.md` | ✅ |
| B Content writer | `marketing/writer.py` (facts-only templates) | ✅ social, scripts, email drafts · 🟡 blog/landing copy not built |
| C Creative director | `creative/motion/styles/*` (5 distinct art directions), briefs, storyboards | ✅ |
| D Video and motion | `creative/pipeline.py`, `creative/film.py`, HTML motion engine | ✅ |
| E Lead researcher | `lead_generation/` (CSV import, Companies House adapter, scoring, dedupe) | ✅ |
| F Outreach preparation | `outreach/eligibility.py`, `outreach/drafts.py` | ✅ draft-only |
| G Publishing | `publishing/` + approval desk + morning run | ✅ dry-run path tested · 🔒 live path needs the connector on the scheduled task |
| H Analytics and reporting | `analytics/report.py` + evening run (Metricool read-only) | 🟡 report ✅; Metricool metrics only once the connector is attached |

n8n was evaluated and **not adopted**: it isn't installed here, would need an always-on host, and the claude.ai
scheduled tasks plus the CLI cover Workflows A–G at £0. Reasoning in architecture.md.

## 3. Repository discovery

| Product | Repo | Synced | Profile |
|---|---|---|---|
| MasjidOne | yameenbux/MasjidOne | ✅ | ✅ quote-verified, awaiting your approval |
| Domi | yameenbux/audiologydomi | ✅ | ✅ awaiting approval |
| Booked In | yameenbux/Peony-Beauty-Platform | ✅ | ✅ awaiting approval |
| Tidemark | yameenbux/Tidemark-Fitness | ✅ | ✅ awaiting approval |
| Bolton Vouched | yameenbux/Boltontradesmen | ✅ | ✅ awaiting approval |

Registry: [`config/repositories.json`](../config/repositories.json) (owner, repo, branch, approved paths,
website, brand, target audience, enabled, last sync and commit). Read-only: the system has no write path to
these repositories.

## 4. Marketing workflows

| Workflow | Command | Status |
|---|---|---|
| A Daily planner 09:00 | `mas plan`, inside `mas ops morning` | ✅ tested (DST-aware, idempotent per day) |
| B Content production | `mas produce`, `mas calendar`, `mas campaign`, `mas film` | ✅ |
| C Validation | `marketing/validator.py` | ✅ numbers must come from evidence; superlatives, social proof, exclusivity, health and compliance claims blocked; per-product guardrails; hosts; platform limits |
| D Social publishing | `mas publish`, approval desk, morning run → Metricool | ✅ dry-run and outbox tested · 🔒 live submission needs the connector on the scheduled task |
| E Lead research | `mas leads-import` | ✅ 36 real leads imported (20 MasjidOne, 16 Domi) |
| F Outreach preparation | `mas outreach-prepare` | ✅ eligibility recorded for all 36; 5 drafts written, 10 more due tomorrow (daily draft limit) |
| G Daily report 16:30 | `mas report`, inside `mas ops evening` | ✅ |

Content states: draft → validated → approved → scheduled → published / failed / cancelled. Every campaign and
calendar slot has a unique id; publications have a UNIQUE idempotency key.

**Live calendar:** 30 validated posts, 6 per product, 22 Oct to 4 Nov. Only MasjidOne has a connected account,
so only its 6 have a live route. The other 24 are drafts until you connect accounts.

## 5. Creative production

| Output | How | Status |
|---|---|---|
| Short-form video, 9:16 / 1:1 / 16:9 with burned-in captions, transitions, end card | Pillow frames + FFmpeg, or the HTML motion engine (Playwright frame capture) | ✅ |
| Cinematic films, a distinct art direction per product (fonts, camera moves, transitions, grain, light leaks) | `mas film <product>` | ✅ all 5 |
| Motion typography, animated UI mock-ups, animated charts, logo sting | motion engine | ✅ |
| Narration | Piper, a different British voice per product | ✅ (Lessac licence caveat in LICENCES.md) |
| Background music, ducking, loudness at -16 LUFS | procedural score in numpy (`creative/music.py`) | ✅ |
| Subtitles (.srt) | per format | ✅ |
| Social cards, carousels, thumbnails, storyboard sheets | Pillow | ✅ |
| AI images and voices | ElevenLabs, Canva | 🔒 credits exhausted |
| Lottie export | — | ❌ not built (no target that needs it yet) |
| Screen-recorded walkthroughs | Playwright screenshots of live public sites (not recordings) | 🟡 |

## 6. Sample assets
Each folder holds a brief, script, storyboard, prompts, 3 videos, SRTs, a logo sting, cards, carousel, thumbnail,
copy, manifest, QC results and licences. Large MP4/WAV files are gitignored and regenerate with the command shown.

| Product | Campaign pack | Film |
|---|---|---|
| MasjidOne | [`assets/masjidone/masjidone-2026-10-21-2fad1a/`](../assets/masjidone/masjidone-2026-10-21-2fad1a/): 9:16, 1:1, 16:9, 42.5s each, QC ✅ | `assets/masjidone/film/` (`mas film masjidone`) |
| Domi | [`assets/domi/domi-2026-10-21-749d0c/`](../assets/domi/domi-2026-10-21-749d0c/): 9:16, 1:1, 16:9, 39.8s each, QC ✅ | `assets/domi/film/` (`mas film domi`) |
| Booked In | [`assets/booked-in/booked-in-2026-10-21-749d0c/`](../assets/booked-in/booked-in-2026-10-21-749d0c/): 9:16, 1:1, 16:9, 34.3s each, QC ✅ | `assets/booked-in/film/` (`mas film booked-in`) |
| Tidemark | [`assets/tidemark/tidemark-2026-10-21-749d0c/`](../assets/tidemark/tidemark-2026-10-21-749d0c/): 9:16, 1:1, 16:9, 38.3s each, QC ✅ | `assets/tidemark/film/` (`mas film tidemark`) |
| Bolton Vouched | [`assets/bolton-vouched/bolton-vouched-2026-10-21-749d0c/`](../assets/bolton-vouched/bolton-vouched-2026-10-21-749d0c/): 9:16, 1:1, 16:9, 35.9s each, QC ✅ | `assets/bolton-vouched/film/` (`mas film bolton-vouched`) |

## 7. Lead generation
Sources used: Charity Commission register (through opencharities.uk mirror and search summaries, because the
register blocked direct fetching), Companies House pages, the organisations' own websites, council and trade
directories. Each lead records its source URL and research date. No personal webmail or named-person addresses
are collected. Leads are stored **only** in the private Google Sheet *YSB Leads (private, do not share)* and the
local gitignored database, never in this repository.

| | MasjidOne | Domi |
|---|---|---|
| Leads | 20 | 16 |
| Passes lead-level PECR checks (company + generic address) | 3 | 5 |
| Manual review (legal form unclear) | 2 | 5 |
| Blocked: non-company organisation, no consent (PECR reg 22) | 6 | 0 |
| Blocked: no usable business address | 9 | 6 |

Booked In, Tidemark and Bolton Vouched have **no outbound route by design**: their buyers are individuals or
sole traders under PECR. Growth for them is organic (see portfolio-strategy.md).

## 8. Outreach compliance
✅ Enforced in code, fail-closed (any error results in a block): suppression first; per-product channel policy; phone and LinkedIn
never automated; corporate vs individual subscribers (PECR reg 22); a documented LIA required for named contacts;
sender identity and opt-out required (reg 23); stale research forces review; drafts use only the recorded
reason and verified facts. Approval and sending re-check eligibility.

🔒 **Blocked until you act:** every send. `config/outreach.json` has no sender legal name, postal address,
reply-to or opt-out text, and no LIA is documented. Even with all of that, `sender.send()` stops at
`NoSendingIntegration`: no email provider is wired, by design, until you authorise one with limits.

## 9. Testing
179 tests, all passing (`pytest -q`). They cover GitHub sync (retries, rate limits, ETag, pagination, path
traversal, token scoping, secret redaction, injection flags), profile verification, duplicate detection,
content validation, eligibility and suppression, publishing dry-run, media and UTM rules, kill switch and limits,
DST-aware scheduling, state export (excludes personal data), the approval desk, creative QC and art-direction
distinctness. CI (`.github/workflows/ci.yml`) runs a secret scan, the tests and `pip-audit` (advisory: it warns, it doesn't fail the build) with no credentials. There is no linter step. Test data
is synthetic.

## 10. Security
✅ Implemented: global kill switch (file, env or setting); per-integration switches; dry-run; live flags;
daily and monthly limits; audit log; idempotency; host allowlist; secrets only from the environment (the
settings loader rejects secret-like keys); secret redaction on sync; repository content wrapped as data and
injection-flagged; path-traversal guards; GET-only GitHub client; no write access to product repos; production
connectors (Stripe, Supabase, Railway…) excluded from marketing sessions. See security.md.

⚠️ **Outstanding risks**
1. **This repository is public** and named `Marketing-Automation-System`, not the private `ysb-marketing-automation`
   the brief asked for. I can't rename it or change its visibility from here. Lead data has never been committed.
   Caveat: post images are currently served from this public repo's raw URLs, so making it private breaks
   them until media moves to other hosting (Cloudflare R2 free tier or Google Drive linked in Metricool).
2. Live publishing is enabled in `config/settings.ops.json` on your instruction. Each post still needs your
   approval in the desk.
3. The approval desk accepts decisions from anyone you give edit access; keep it private.

## 11. Budget
**Spent: £0.** Nothing purchased. All rendering, voices and music are local and free. ElevenLabs and Canva
credits from your existing plans were used until exhausted. Running cost now: £0/month (claude.ai scheduled
tasks, Metricool free tier, Google Sheets). Cost per finished video: £0 locally; about £0.20 if re-voiced with
ElevenLabs (about $1.20 for all five films, from current credit pricing). Spending limits:
`monthly_budget_gbp: 50`, `monthly_llm_budget_gbp: 5`, plus render, post and draft limits per day.

## 12. Setup instructions
```bash
bash scripts/session_setup.sh --render   # install, voices, Playwright, restore state
pytest -q                                # 179 tests
mas status
```
Daily operation needs nothing from a terminal: approve in the desk; the 09:00 and 16:30 scheduled tasks do the
rest (operations.md has the full loop and how to stop it).

## 13. Outstanding dependencies (what only you can do)
1. **Add the Metricool connector to both scheduled tasks** (claude.ai → scheduled tasks). Without it the morning run stops safely and posts nothing.
2. **Approve the five product profiles and the posts** in the [approval desk](https://claude.ai/artifact/SSsMno35am8MSUXCC8R2JY).
3. **Rename the repo to `ysb-marketing-automation` and make it private**, then choose media hosting (R2 or Drive).
4. **Connect social accounts** for Domi, Booked In, Tidemark and Bolton Vouched in Metricool.
5. **Outreach:** fill in the sender identity in `config/outreach.json`, write the LIA, and authorise a sending provider with limits.
6. Optional: top up ElevenLabs (about £1) to re-voice the films; a Companies House API key (free).

## 14. Next steps within £0–£50
1. Distribution before volume: masjidone.uk has about 1 follower. Use borrowed audiences (masjid networks, local groups you belong to) and launch-gated posts.
2. Connect one account per product (free) so the 24 waiting drafts have somewhere to go.
3. Move media to Cloudflare R2's free tier, then go private and publish Reels.
4. Re-voice films with ElevenLabs (about £1) once credits are topped up.
5. Optional Anthropic API copy polish under the £5 LLM cap.
