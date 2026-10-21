# YSB marketing automation

Marketing system for the YSB products (MasjidOne, Domi, Booked In, Tidemark, Bolton Vouched). It reads each product's
**public README**, turns it into a profile of **quote-verified facts**, and produces social copy, short-form
video (9:16, 1:1, 16:9), graphics and outreach drafts from those facts only. Everything is validated in code
and held for human approval. **Dry-run by default; nothing is published or sent without you.**

```bash
pip install -e ".[tts,dev]" && pytest -q   # 137 tests
mas status                                 # mode, kill switch, profile verification
mas sync                                   # pull approved docs from the product repos (read-only)
mas plan && mas produce                    # daily plan → validated drafts
mas campaign masjidone --objective "..."   # full creative pack → assets/masjidone/<id>/
mas report                                 # what actually happened today
mas kill-switch on                         # stop everything
```

| Doc | |
|---|---|
| [docs/capability-audit.md](docs/capability-audit.md) | what's verified available, and what isn't |
| [docs/architecture.md](docs/architecture.md) | design, the n8n evaluation, where to run it |
| [docs/integration-gaps.md](docs/integration-gaps.md) | what's missing and how to close it |
| [docs/creative-production-workflow.md](docs/creative-production-workflow.md) | the video and graphics pipeline |
| [docs/security.md](docs/security.md) | controls, outstanding risks, backups |
| [docs/operations.md](docs/operations.md) | setup, scheduling, approvals, going live |
| `data/products/<slug>/PROFILE.md` | readable product profiles to review before approving |

> ⚠️ This repository is currently **public**. Make it private before storing any lead data or running it on a schedule.
