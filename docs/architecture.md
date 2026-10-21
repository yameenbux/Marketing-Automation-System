# Architecture

## Design in one paragraph

A single Python package (`mas`) with a CLI, a SQLite state file, and one policy gate that every outward
action must pass. Product knowledge comes from your public READMEs. Each marketing "fact" is stored with a
**verbatim quote** and re-checked against the latest synced README every time it's used, so copy can't
drift from what the product actually does. Content and creative are produced from those facts only,
validated in code, and approved by a human. Publishing and outreach default to dry-run; outreach has no
sending integration at all.

```
 public GitHub READMEs ──► github_sync ──► data/products/<slug>/sources/   (secret-redacted, injection-flagged)
                                              │
                         profile.json (facts + verbatim quotes) ◄── re-verified on every load
                                              │
            ┌─────────── planner (A) ─────────┴────────── creative pipeline (B) ───────────┐
            │  readiness ranking, pillar rotation,        script → storyboard → screenshots │
            │  fact de-duplication                        → Piper narration → Pillow frames │
            ▼                                              → ffmpeg → QC → manifest          ▼
       writer (B) ──► validator (C) ──► human approve ──► publisher (D) ──► var/outbox/{dry-run,metricool}
                      numbers ⊆ evidence, claims,          idempotency key        │
                      guardrails, hosts, limits            (UNIQUE)               └─► Claude session submits
                                                                                      via Metricool connector
 CSV / Companies House ──► leads (E): minimise, dedupe, score ──► eligibility (F, PECR/UK GDPR, fail-closed)
                                                                     ──► local draft ──► (no sender exists)
 store + audit ──► daily report (G, 16:30)

             ALL side effects ──► Policy.authorize(): kill switch · integration on/off · dry-run · limits · budget · audit
```

## Modules

| Module | Role (brief's agent) | Notes |
|---|---|---|
| `github_sync/` | product knowledge sync | REST API → raw + ls-remote fallback; ETag cache, pagination, retries, rate limits, per-run request budget; docs-only allowlist; path-traversal-proof |
| `products/profile.py` | source of truth | facts carry quotes; status verified / stale / invalid / unverifiable |
| `marketing/planner.py` | **strategist** | readiness score is evidence-based and explained |
| `marketing/writer.py` | **content writer** | deterministic, facts-only; posts, video scripts, emails, blog outlines |
| `marketing/validator.py` | **QA** | unsupported numbers, superlatives, social proof, health/compliance claims, per-product guardrails from limitations, link hosts, platform limits, UK spelling |
| `creative/` | **creative director + video producer** | brand tokens with WCAG contrast, graphics, kinetic-type video, captions, SRT, logo sting, storyboard sheet, QC |
| `publishing/` | **publisher** | approved-only, idempotent, Metricool-shaped outbox |
| `lead_generation/` | **lead researcher** | organisation-level records, transparent ICP scoring |
| `outreach/` | **outreach preparer** | PECR/UK GDPR rules in code; draft-only |
| `analytics/report.py` | **analyst** | reports from the store and audit log, not from intentions |
| `policy.py` | permissions framework | the one gate; no module can bypass it |
| `scheduler.py` | orchestrator | `mas tick` every 15–30 minutes; London time; idempotent per day |

These are modules, not autonomous LLM agents. The brief listed eight agents. Eight LLM agents passing work
between each other would cost money every run, be non-deterministic, and add failure modes, with no gain
at this volume (a few posts a day). Where judgement is genuinely needed (strategy, approving copy,
legitimate-interest decisions), that's you, at the approval step.

## Why not n8n (evaluated, not adopted)

| | n8n CE (self-hosted) | `mas tick` from cron / systemd / Docker |
|---|---|---|
| Cost | £0 + a host | £0 + a host |
| Testability | workflows are JSON in a GUI; hard to unit-test | 126 pytest tests in CI |
| Shell access | Execute Command node disabled by default in recent versions; enabling it gives the workflow engine a shell | none needed |
| Attack surface | a web UI with credentials store that must not be internet-exposed | nothing listens on the network |
| Fit | great for gluing SaaS APIs | our heavy work is local rendering and policy logic |

n8n becomes worth it if you later want non-developers to build integrations visually. The CLI is the
integration point: an n8n workflow can call `mas tick` without any redesign.

## Where it should run

- **Recommended: an always-on machine you own** (your homelab, or any always-on PC) with a systemd timer or
  `docker compose up -d`. £0. The machine must stay on and online, and nothing needs to be exposed to the internet.
- **Claude Code scheduled task** (a weekday cloud session). This is the only way to use the Metricool, ElevenLabs
  and Canva *connectors* unattended. The container is ephemeral, so state (`var/`) must be persisted elsewhere
  first, for example by committing reports to the private repo. A good fit for the "submit outbox to Metricool"
  step.
- **Not recommended: GitHub Actions cron.** Runners are ephemeral, so SQLite state, idempotency and
  limits would reset every run unless cached. On this *public* repo, logs would also be public.
