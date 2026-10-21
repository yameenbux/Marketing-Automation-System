# 30-day customer-acquisition plan (22 Oct – 20 Nov 2026)

**Goal:** real conversations, demos, pilots and paying customers, measured by source. Not posts, not views.
**Order:** MasjidOne → Domi → Bolton Vouched. Booked In and Tidemark stay in readiness mode until launch.

Per-product plans (generated from `config/acquisition.json`; edit the config, then `mas acq docs`):
[MasjidOne](masjidone.md) · [Domi](domi.md) · [Bolton Vouched](bolton-vouched.md)

## What the evidence says before you start
- **MasjidOne can't be invoiced yet.** Its own README promises ICO registration and a data processing agreement
  before a masjid is invoiced. Start those in week 1 or the week-4 sale cannot happen. The demo-request form also
  only opens the visitor's mail client, so web enquiries can be lost.
- **Domi's headline may not apply to most of its market.** NHS sight tests need a pre-visit notification 48 hours
  ahead, so same-day or day-before refills only fit private work or longer-notice cancellations. That is assumption
  D-A2, and it is the first thing to find out. Domi also can't hold real patient data yet, so a pilot means a
  design partner on invented data, and paying customers within 30 days are zero by design.
- **Bolton Vouched has nothing to sell yet.** Pro isn't built. The 30-day outcome is supply (traders listed) and
  then demand (enquiries delivered). Paying customers are zero by design.
- **Distribution is the bottleneck.** The only connected social account has about 1 follower. Acquisition here is
  relationships: referrals, visits, phone calls, letters. Content is kept to two MasjidOne posts a week, as proof
  for prospects who look you up.

## Week by week

| Week | MasjidOne (priority 1) | Domi (priority 2) | Bolton Vouched (priority 3) |
|---|---|---|---|
| 1 · 22–28 Oct | Ask the live masjid for two introductions and a reference call (M-A4). Visit three Bolton masājid. Post five letters to the top-ranked prospects. Start ICO registration. | Screen the top 6 numbers against TPS/CTPS, then call. Ask about cancellations, notice and the NHS/private split (D-A1, D-A2). | Ask the group admins for permission. One invitation post; send consent links only to traders who reply. |
| 2 · 29 Oct–4 Nov | Demos for the qualified conversations; ask the price question every time (M-A2). Follow up letters with a visit or call. | Demo to the practices that confirmed the pain. Offer the design-partner trial. | Keep listing traders. A resident-facing post once at least 3 trades have 2+ listings. |
| 3 · 5–11 Nov | Propose a pilot to the warmest masjid. Confirm the parent-access status first (M-P2). | First design partner. If D-A1/D-A2 fail, switch to the route-planning message. | Ask listed traders to point customers to reviews. Log enquiries from trader dashboards weekly. |
| 4 · 12–18 Nov | Pilot running. Paying customer only if ICO and DPA are done; otherwise a signed letter of intent. | Second design partner. Decide whether to build real-data hosting (D-P1) or reposition. | Compare enquiries per trade against listings (B-A4) and recruit where demand is. |
| 19–20 Nov | Review: which sources produced conversations, which assumptions held, what to do in the next 30 days. | | |

Weekly targets per stage are in each product plan and on the desk.

## Who does what

| Automated (the system) | You |
|---|---|
| Ranks prospects and shows the permitted contact methods for each | Visits, calls, letters, referral asks, demos, pilots, closing |
| Checks every message against verified facts before you use it | Logging each conversation in the desk, with its source |
| Drafts letters and emails; eligibility recorded per organisation | Approving drafts; setting the sender identity; ICO, DPA and legal reviews |
| Keeps the weekly funnel, source attribution and assumption tests on the desk | Answering the assumption questions in conversations and logging the answer |
| Refreshes "Do next" every weekday at 16:30 | Deciding when an assumption is disproved and changing course |
| Two MasjidOne posts a week, after your approval | Approving them, or not |

Nothing is sent or published without your approval. Email stays blocked until your sender identity is set.
Letters, visits, calls and LinkedIn messages are yours to make.

## How to log (the one habit that makes this work)
Open the [desk](https://claude.ai/artifact/SSsMno35am8MSUXCC8R2JY) → **Log a conversation**. One entry each time an
organisation reaches a stage (contacted, conversation, qualified, demo, pilot, paying; for Bolton Vouched: listed,
enquiry, review). Pick how it started (the source). When they answer one of the assumption questions, pick the
assumption and whether the answer supports or contradicts it. Organisation names only, no personal details.

## Where things live
- Plan and targets: `config/acquisition.json` (committed, no personal data).
- Prospects: the desk's Prospects tab and the private lead sheet. Never in this repository.
- Your log: the desk's database (private to you). Scheduled runs copy it into the gitignored `var/pipeline/`.
- Reports: `mas acq report`, the daily report, and the desk's Pipeline tab.
