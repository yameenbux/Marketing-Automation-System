# 30-day customer-acquisition plan (22 Oct – 20 Nov 2026)

**Goal:** real conversations, demos, pilots and paying customers, measured by source. Not posts, not views.
**Order:** MasjidOne → Domi → Bolton Vouched → Booked In (active from 26 Oct). Tidemark stays in readiness mode until launch.

Per-product plans (generated from `config/acquisition.json`; edit the config, then `mas acq docs`):
[MasjidOne](masjidone.md) · [Domi](domi.md) · [Bolton Vouched](bolton-vouched.md) · [Booked In](booked-in.md)

## What the evidence says before you start (READMEs re-read 21 Oct, evening)
- **MasjidOne can't take a second masjid yet.** Its README says a known platform fix is "Blocking the moment a
  second masjid is signed". That gates any pilot (prerequisite M-P5). It also can't be invoiced until ICO
  registration and the data processing agreement are done, and the demo-request form still only opens the
  visitor's mail client. Parent-access status is still contradictory inside the README: never demo it.
- **Domi is closer to a real pilot than it was.** UK hosting, real accounts and ICO registration are done, and a
  live London environment is set up for a first pilot practice. What remains before a real patient is the
  practice paperwork (DPIA, DPA, DSPT check), processor DPAs, encrypting phones' offline copy and hardening.
  Refills are no longer text-only: phone list, text offer or book instantly. It works alongside Opticabase, with
  bookings copied back by hand. NHS sight tests still can't fill a same-day gap (D-A2 is still the first question).
- **Bolton Vouched now has something to sell, but almost nothing listed.** Pro is live (£10 a month or £100 a
  year, offered, never pushed). The site moved to www.boltonvouched.co.uk (the old ysbdesigns address no
  longer responds). The live directory had **2 listings** on 21 Oct and every home and trades category says
  "soon". Supply is the whole game for the first fortnight.
- **Booked In went active on 26 Oct: free sign-up works, paying doesn't.** The live site takes free sign-ups and
  starts every studio on a fourteen-day Pro+ trial, but billing has only run against a Stripe sandbox and has never
  taken a real payment (K-P1, which turns urgent with the first sign-up). Before any public push: confirm the
  security fixes 029/032 are in production (K-P2), test a booking on a real iPhone (K-P3), and fix the footer and
  the "next" promises on the pricing card (K-P4). The measure is pages taking real bookings, because each live page
  carries "Powered by Booked In" to its clients. No cold messages: buyers are sole traders.
- **Tidemark stays in readiness.** No signed iPhone build yet, and the site has no sign-up form.
- **Distribution is the bottleneck.** The only connected social account has about 1 follower. Acquisition here is
  relationships: referrals, visits, phone calls, letters. Content is kept to two MasjidOne posts a week.

## Week by week

| Week | MasjidOne (priority 1) | Domi (priority 2) | Bolton Vouched (priority 3) |
|---|---|---|---|
| 1 · 22–28 Oct | Ask the live masjid for two introductions and a reference call (M-A4). Visit three Bolton masājid. Post five letters to the top-ranked prospects. Start ICO registration. | Screen the top 6 numbers against TPS/CTPS, then call. Ask about cancellations, notice and the NHS/private split (D-A1, D-A2). | Ask the group admins for permission. One invitation post pointing recommended traders to /get-listed (no account needed). |
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
