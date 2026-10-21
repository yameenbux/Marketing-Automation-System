# Operations runbook

## First-time setup (on the machine that will run it)

```bash
git clone https://github.com/yameenbux/Marketing-Automation-System.git ysb-marketing-automation
cd ysb-marketing-automation
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[tts,dev]" playwright==1.56.0
python -m playwright install chromium          # skip if Chromium is already provided
sudo apt-get install -y ffmpeg fonts-inter      # macOS: brew install ffmpeg; install Inter from rsms.me/inter

# British narration voice (63 MB, CC BY 4.0 dataset — see LICENCES note)
mkdir -p models/piper && cd models/piper
for f in en_GB-alba-medium.onnx en_GB-alba-medium.onnx.json; do
  curl -LO "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alba/medium/$f"; done
cd ../..

cp .env.example .env              # optional: GITHUB_TOKEN (public read-only), COMPANIES_HOUSE_API_KEY
pytest -q                          # expect all tests to pass
mas sync && mas status
```

## Daily operation (weekdays, Europe/London)

Schedule `mas tick` every 15 minutes. It runs only what is due, only during 09:00–17:00 Monday to Friday,
and each job only once a day:

| London time | Job |
|---|---|
| ≥ 09:00 | **A** sync + plan → **B/C** write + validate → **D** publish approved items (dry-run) |
| ≥ 16:30 | **G** daily report → `var/reports/YYYY-MM-DD.md` |

**systemd (recommended):**
```ini
# /etc/systemd/system/mas-tick.service
[Service]
Type=oneshot
WorkingDirectory=/opt/ysb-marketing-automation
EnvironmentFile=-/opt/ysb-marketing-automation/.env
ExecStart=/opt/ysb-marketing-automation/.venv/bin/mas tick
User=mas
# /etc/systemd/system/mas-tick.timer
[Timer]
OnCalendar=Mon..Fri *-*-* 08..17:00/15:00
Persistent=true
[Install]
WantedBy=timers.target
```
**cron:** `*/15 8-17 * * 1-5 cd /opt/ysb-marketing-automation && .venv/bin/mas tick >> var/tick.log 2>&1`
**Docker (untested here):** `docker compose up -d --build`

The machine must be on and online at those times. Nothing listens on the network, so there's nothing to expose.

## Your part (the human approvals)

```bash
mas profile masjidone                  # read every fact; edit data/products/masjidone/profile.json if wrong
mas approve-profile masjidone --by "Yameen"
mas calendar --weeks 2                 # plan the next fortnight across all products
mas content --status validated         # list drafts that passed validation
mas show <content_id>
mas approve <content_id> --by "Yameen" # re-validates at approval time
mas publish                            # dry-run: writes var/outbox/dry-run/*.json
```

## Going live with publishing (when you decide to)

1. In `config/settings.json`, set `"dry_run": false, "live": {"publishing": true}` and add
   `"metricool": {"blog_id": "<from Metricool>", "reviewer_email": "<you>"}`.
2. `mas publish` now writes `var/outbox/metricool/*.json`.
3. Submit them from a Claude session that has **only** the Metricool connector: *"For each file in
   var/outbox/metricool, call createScheduledPostForReview with its args, upload local_media first, then move the
   file to var/outbox/submitted/."* Metricool then holds each post for your approval before it goes out.
4. Roll back at any time: `mas kill-switch on`.

## Leads and outreach

```bash
mas leads-import masjidone research.csv          # columns: see src/mas/lead_generation/leads.py ALLOWED_FIELDS
mas leads --product masjidone
mas outreach-prepare <lead_id>                    # eligibility decision + local draft (never sent)
mas suppress "email:someone@org.example" --reason "asked not to be contacted"
```

Before any lead can become *eligible* you must fill in `config/outreach.json`: sender legal name, postal
address, reply-to, opt-out wording, and, for named contacts, a documented Legitimate Interests Assessment.
Even then, **no sending integration exists**. That needs a separate, explicit decision.

## Emergency stop

`mas kill-switch on --reason "..."`, or `export MAS_KILL_SWITCH=1`, or `touch var/KILL_SWITCH`. Release with
`mas kill-switch off`, then check `mas status`.

## Maintenance

- Sync is automatic. When a README changes, affected facts turn `stale` and any content citing them is
  rejected on re-validation. Re-verify the fact or fix its quote, then re-approve the profile.
- Back up `var/mas.sqlite` daily. **Never lose the suppression list.**
- Add a product: add it to `config/repositories.json`, run `mas sync --product <slug>`, write
  `data/products/<slug>/profile.json` (every fact with a verbatim quote), then `mas profile <slug>`.

## Daily loop (live from 22 Oct 2026)

| When (Europe/London, weekdays) | What |
|---|---|
| Any time | Owner approves/rejects in the **Approval Desk**: https://claude.ai/artifact/SSsMno35am8MSUXCC8R2JY (profiles first, then posts by slot). |
| 09:07 | Scheduled task *YSB marketing — morning run*: pre-flight (Metricool connector + ArtifactData must be present, else stop with nothing changed) → read desk decisions → `mas ops morning --decisions var/decisions.json` → submit `var/outbox/metricool/*.json` via Metricool `createScheduledPost` → reseed desk queue → commit `state/ops_state.json`. |
| 16:37 | Scheduled task *YSB marketing — evening report*: `mas ops evening` + read-only Metricool analytics → `reports/daily/YYYY-MM-DD.md`. |

Settings: `config/settings.ops.json` (committed) sets `dry_run: false`, `live.publishing: true`, max 3 posts/day. Outreach sending stays off.
Stop everything: create `var/KILL_SWITCH` locally, or set `"kill_switch": true` in `config/settings.ops.json` and push — the next run halts. Or disable the scheduled tasks in claude.ai.
State: fresh sessions rebuild the DB from `state/ops_state.json` (content, calendar, publications, runs, costs, 30 days of audit). Leads, suppression and outreach are never exported to the repo.
Only products with a verified account in `config/channels.json` get a live route; today that is MasjidOne → Instagram (masjidone.uk). Everything else is drafted and waits.
