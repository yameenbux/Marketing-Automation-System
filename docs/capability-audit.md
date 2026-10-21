# Capability audit

**Date:** 21 Oct 2026. **Where:** a Claude Code *cloud* session (an ephemeral Linux container), not your desktop.
Machine-readable version: [`config/capabilities.json`](../config/capabilities.json).

"Verified" below means a real, read-only call or a local run succeeded in this session. Nothing was
purchased, published, or sent.

## What actually works today

| Capability | Status | How verified |
|---|---|---|
| Python 3.13, Pillow 12, FFmpeg 6.1 (H.264/AAC/xfade), Inter fonts | ✅ usable | Rendered 3 videos + 10 stills |
| Headless Chromium (Playwright 1.56) | ✅ usable | Screenshotted masjidone.co.uk, domi.ysbdesigns.uk |
| Piper TTS, British "alba" voice | ✅ usable (licence caveat) | Generated narration for the sample video |
| Public GitHub docs via raw.githubusercontent.com + `git ls-remote` | ✅ usable | Synced 4 READMEs with commit SHAs |
| GitHub REST API for *other* repos | ❌ blocked **here** | 403 from this session's proxy; should work on your machine |
| Repo discovery (`list_repos`) | ✅ | 19 repos listed (18 public + 1 private) |
| **Metricool** connector | ✅ read verified | Brand "YBTweetss" → Instagram **masjidone.uk** only |
| **ElevenLabs** connector | ✅ connected, 💷 credits | TTS v4, Veo 3.1, Kling, Seedance, Music v2.5 available |
| **Canva** connector | ✅ connected | No brand kits set up |
| Figma | ⚠️ View seat on Starter | Can read, can't meaningfully create |
| Exa, Firecrawl, Google Sheets/Drive/Docs, Gmail, Notion, Resend | connected, not exercised | Listed by the connector registry |
| Docker | ⚠️ client only, no daemon | Dockerfile written but untested |

## The five status buckets

1. **Installed and verified usable:** local rendering stack, Chromium, Piper, GitHub raw/ls-remote, Metricool (read), repo discovery.
2. **Installed but not configured:** Companies House adapter (needs a free key), Docker (needs a daemon), Anthropic API (needs a key).
3. **Needs authentication or your permission:** Higgsfield, Apollo and Microsoft 365 (`connect_incomplete`); Metricool scheduling (it would post for real); Canva/Figma generation; Google Sheets as a CRM.
4. **Available but costs money or credits:** ElevenLabs generations, Exa/Firecrawl requests, Anthropic API, a Metricool plan upgrade if review/approval or API access is needed.
5. **Unavailable here:** Buffer (not connected), HubSpot (the plugin failed to connect), n8n (not installed), Claude *Desktop* local skills and computer use (they can't be seen from a cloud session).

## Things I could not inspect, and what you need to do

- **Claude Desktop skills and local MCP servers.** These live on your computer. If you have desktop-only skills (video editors, local apps), open this repo in Claude Code Desktop and ask it to append them to this file.
- **Your Metricool plan tier.** Check it in Metricool → Billing. The `createScheduledPostForReview` flow needs a plan with team management. If your plan lacks it, the outbox falls back to drafts you post by hand.
- **ElevenLabs credit balance and licence terms** for commercial use on your plan.

## Connectors you have that the marketing system must NOT use

Stripe, Supabase, Railway, Render, Cloudflare, Twilio, OneSignal, Sentry and UptimeRobot all reach your
**production SaaS infrastructure**. The marketing system needs none of them. Least privilege means they stay out
of every scheduled marketing session. See [security.md](security.md).
