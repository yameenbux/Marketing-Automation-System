# Bolton Vouched: 30-day acquisition plan

Priority 3 · 2026-10-22 to 2026-11-20 · generated from `config/acquisition.json` by `mas acq docs` (edit the config, not this file).

## Ideal customer
- **Who:** Supply: Bolton tradespeople already recommended in the Bolton Tradesmen WhatsApp group, in the trades residents ask for most. Demand: Bolton residents (BL1–BL7) in local community groups.
- **Where:** Bolton only.
- **Buyer:** Traders join free; residents use it free. Revenue (Pro) is a later test, not a 30-day goal.
- **Disqualify:** Gas or boiler work without a Gas Safe check; Driving instructors without a DVSA ADI check; Anyone who hasn't consented after reading how they'll appear

## Value proposition
> Traders: a free basic listing, for good, where nobody can pay to move up the list and your number is never in the page. Residents: recommended people you can actually find again, free, with no account needed to look or call.

Evidence (verified facts):
- `audience-traders`: For local tradespeople, a basic listing is free for good, including the page, Call and WhatsApp buttons, reviews, the review link and QR card, the enquiry count, the Taking on work switch and the website badge.
- `value-free-forever`: The basic listing is free forever, and nobody is removed, hidden or moved down for not paying.
- `value-no-pay-to-rank`: Nobody can pay to move up the list, and that promise is the heart of the product.
- `privacy-numbers-hidden`: Traders' phone numbers are never in the page's HTML, so scrapers reading the page find no phone numbers.
- `value-findable`: Recommended people are kept where you can find them, sorted by trade and by the BL areas they cover, with a button to call or WhatsApp them.
- `audience-residents`: For Bolton residents who need a trusted tradesperson, it is free, with no account needed to look or call.
- `pain-buried-recommendations`: Good recommendations in the local WhatsApp group scroll away under hundreds of messages, so the next person has to ask all over again.

Don't lead with: 'Vetted' or 'checked' traders as a blanket claim (checks are per listing); Pro as a way to rank higher (payment never affects ranking)

## Biggest unresolved assumptions
| ID | Risk | Assumption | How we test it | Decision rule |
|---|---|---|---|---|
| B-A1 | highest | Traders recommended in the group will consent to a listing when invited. | Track invited versus listed. | Needs 10 answers; ≥60% supporting. If not: Ask the ones who declined why (privacy, cold calls, effort) and address that first. |
| B-A2 | highest | Residents will use the directory instead of asking the group, producing enquiries for listed traders. | Enquiries from trader dashboards, logged weekly (the site deliberately has no analytics). | Needs 1 answers; ≥100% supporting. If not: Coverage is probably too thin: concentrate on three to five trades until each has several listings. |
| B-A3 | high | Group admins will allow a post about Bolton Vouched. | Ask the admin of each group before posting; record yes or no. | Needs 3 answers; ≥50% supporting. If not: Use offline channels: noticeboards, local shops, local press. |
| B-A4 | medium | A trade needs several listings before residents find it useful. | Compare enquiries per trade against listings per trade. | Needs 3 answers; ≥50% supporting. If not: Spread recruitment across more trades. |
| B-A5 | medium | Listed traders who get enquiries will pay for Pro's quotes, invoices and job requests. | After a trader's first enquiries, ask whether quotes and invoices as links would save them time. Never push. | Needs 5 answers; ≥20% supporting. If not: Keep Pro available but stop discussing it; the free listing is the product. |

## Prerequisites (yours)
- [ ] **B-P1** blocks *facebook_group*: The policy pages are still drafts pending legal review; get them reviewed before a wide public push.
- [ ] **B-P4** blocks *facebook_group*: The README's launch checklist still lists ICO registration; confirm it is done (the site holds residents' and traders' personal data).
- [ ] **B-P2** blocks *contacted*: List the Bolton WhatsApp and Facebook groups you belong to, and ask each admin for permission.
- [ ] **B-P3** blocks *listed*: Approve the Bolton Vouched profile in the approval desk.

## Channels, in order
| # | Source | Who acts | How | Compliance |
|---|---|---|---|---|
| 1 | whatsapp_group | you | With the admin's agreement, post once in the Bolton Tradesmen group inviting recommended traders to request a free listing at /get-listed (no account needed). | Traders are mostly sole traders (individual subscribers): no unsolicited one-to-one marketing messages. An open invitation they act on themselves is solicited. |
| 2 | in_person | you | Ask traders you know or meet; show them how their listing will look. | Face to face; consent link only when they agree. |
| 3 | facebook_group | you | Resident-facing post in local community groups you belong to, with admin permission. | Posted by you, never automated; respect group rules. |
| 4 | other | you | Noticeboards, local shops, local press story ('a directory where nobody can pay to move up'). | — |

The prioritised prospect list (organisations, sources, qualification reasons and permitted contact methods per organisation) is in the approval desk's Pipeline tab and `mas acq prospects bolton-vouched`. It is not stored in this repository.

## Weekly targets
| Stage | Definition | W1 | W2 | W3 | W4 |
|---|---|---|---|---|---|
| contacted | Trader invited to opt in (in person, in the group, or they asked) | 12 | 10 | 10 | 8 |
| conversation | Trader replied or asked about listing | 8 | 7 | 7 | 5 |
| listed | Trader consented and the listing is live | 5 | 6 | 6 | 5 |
| enquiry | Resident enquiries delivered to listed traders (log the count from the trader dashboard) | 0 | 3 | 5 | 8 |
| review | Resident reviews left | 0 | 1 | 2 | 3 |
| paying | A listed trader subscribes to Pro (£10 a month or £100 a year): offered, never pushed | 0 | 0 | 0 | 1 |

Supply first: the live directory has 2 listings and no home or trades listings at all. Enquiries only follow once several trades have listings. Paying (Pro) is a week-4 stretch and must never be pushed.

## Messages (each passes the claim validator)
**bv-trader-invite** — Group post inviting traders to request a listing (facts: value-free-forever, value-no-pay-to-rank, privacy-numbers-hidden, cta-get-listed, url-site)

> The basic listing on Bolton Vouched is free forever, and nobody is removed, hidden or moved down for not paying. Nobody can pay to move up the list, and traders' phone numbers are never in the page's HTML. Traders can request a listing without an account: https://www.boltonvouched.co.uk/get-listed

**bv-resident** — Resident-facing post in a community group (only once several trades have listings) (facts: pain-buried-recommendations, value-findable, audience-residents, url-site)

> Good recommendations in the local WhatsApp group scroll away under hundreds of messages, so the next person has to ask all over again. Bolton Vouched keeps recommended people where you can find them, sorted by trade and by the BL areas they cover, with a button to call or WhatsApp them. Free, with no account needed to look or call: https://www.boltonvouched.co.uk

## Discovery questions
1. Where do most of your new jobs come from today?
2. What puts you off being listed in directories?
3. Which BL areas do you cover?
4. Would you tell customers you're on Bolton Vouched so they can leave a review?

## Demo
Assets: https://www.boltonvouched.co.uk (live); assets/bolton-vouched/film/ (cinematic film); assets/bolton-vouched/bolton-vouched-2026-10-21-749d0c/ (campaign pack)

1. For a trader: show a live listing in their trade, the checks shown, the call/WhatsApp buttons, and that numbers are not in the page's HTML.
2. Show the trader dashboard: enquiries this month, edit description and areas, pause listing.
3. Explain consent: they read exactly how they'll appear before it goes live.
4. If a trader asks about Pro: £10 a month or £100 a year for job requests, alerts, quotes and invoices, review requests, an ID check, work photos and a monthly report (pricing-pro). Offered, never pushed.

Never show: Any suggestion that Pro affects ranking

## Pilot offer
Free listing, for good. Ask each listed trader to point happy customers to leave a review, using their review link and QR card.

## Content
Post days: none · hypothesis: —. No connected page. Group posts are written and posted by you, using the messages below.
