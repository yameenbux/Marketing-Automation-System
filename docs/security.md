# Security

## Threat model, in short

The system reads untrusted text (READMEs, websites, research), produces content that could reach the
public, and could, if misconfigured, message real people. The main risks are: publishing or messaging
without approval, leaking secrets or personal data, being steered by injected instructions, and runaway
spend.

## Controls implemented, all tested

| Risk | Control | Where |
|---|---|---|
| Unauthorised publication or messaging | One policy gate; dry-run default; `live.*` flags **and** `dry_run=false` **and** limits; approval required; outreach has no sending code at all | `policy.py`, `publishing/`, `outreach/sender.py` |
| Emergency stop | Kill switch via settings, the `MAS_KILL_SWITCH` env var, or `var/KILL_SWITCH` (`mas kill-switch on`); blocks every action including reads | `policy.py` |
| Duplicate posts | UNIQUE idempotency key per (content, destination, time); content fingerprints are UNIQUE | `store.py`, `publisher.py` |
| Runaway loops or spend | Per-run GitHub request budget; daily render/post/draft limits; monthly £ and LLM caps counted from the audit table (survives restarts) | `policy.py` |
| Prompt injection from repos or web | Repo text is never treated as instructions; it's only *quoted* as evidence; suspicious lines are flagged in the sync report; `wrap_as_data()` fences any future LLM use | `github_sync/untrusted.py` |
| Secrets in public repos | Every synced file is scanned; findings are flagged in the audit log and the stored copy is redacted; credentials are never used | `redact.py`, `sync.py` |
| Secret leakage via logs | Audit entries pass through `redact()`, including live env-var values; `settings.json` refuses secret-looking keys; secrets come from the environment only | `store.py`, `config.py` |
| Path traversal | Approved paths validated (no `..`, absolute paths, or backslashes); destination must stay inside `sources/`; docs-only extensions | `client.py`, `sync.py` |
| SSRF via screenshots | HTTPS only; host must be a verified product host; DNS must resolve publicly (no private, loopback, link-local or metadata IPs); off-host navigations aborted; no forms or logins | `creative/screenshots.py` |
| Command injection | Every subprocess uses a fixed argv list, never `shell=True`; TTS text goes via stdin | `tts.py`, `video.py`, `client.py` |
| Over-broad GitHub access | Read-only; GET only (tested); an optional token is only sent to api.github.com; never write access to product repos | `client.py` |
| Personal data | Leads are organisations; extra CSV columns rejected; personal webmail rejected; `data/leads`, `var/` and `*.sqlite` are gitignored | `leads.py`, `.gitignore` |
| Least privilege across connectors | Production-infra connectors (Stripe, Supabase, Railway, Render, Cloudflare, Twilio, OneSignal) are out of scope for every marketing session | operations.md |
| Committed secrets | `scripts/scan_secrets.py` runs in CI | `.github/workflows/ci.yml` |
| Dependency risk | Single runtime dependency (Pillow), plus optional piper and playwright; `pip-audit` in CI | `pyproject.toml` |

XSS, CSRF and webhooks: **not applicable**. Nothing serves HTTP or receives webhooks. Keep it that way. If you
add n8n or a dashboard, put it behind authentication and don't expose it publicly.

## Outstanding risks, honestly

1. **The repository is public.** Nothing sensitive is committed today, but one wrong `git add -f` would publish
   lead data. Make it private.
2. **Metricool hand-off via a Claude session** means that session holds a connector able to post. Give that
   session only the Metricool connector, and keep the review variant (`createScheduledPostForReview`).
3. **Fact verification proves a quote exists, not that the paraphrase is faithful.** The agent-drafted
   paraphrases need your eye once, at profile approval.
4. **Screenshot visuals aren't matched to the narrated claim.** Review each video before approving it.
5. **The injection flagger is heuristic** (it already produced one false positive on Domi). It's a review
   aid, not a defence. The real defence is that nothing executes repo text.

## Backup and recovery

- State lives in `var/mas.sqlite` (content, approvals, publications, leads, suppression, audit). Back it up daily:
  `sqlite3 var/mas.sqlite ".backup var/backup-$(date +%F).sqlite"`, or simply copy the file while no job is running.
- **The suppression list is the one thing you must never lose.** Losing it means re-contacting people who opted out.
- Everything else (synced sources, renders) is regenerable with `mas sync` and `mas campaign`.
