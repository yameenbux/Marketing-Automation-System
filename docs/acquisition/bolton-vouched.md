# Bolton Vouched: 30-day acquisition plan

Priority 3 · 2026-10-22 to 2026-11-20 · generated from `config/acquisition.json` by `mas acq docs` (edit the config, not this file).

## Ideal customer
- **Who:** Supply: Bolton tradespeople already recommended in the Bolton Tradesmen WhatsApp group, in the trades residents ask for most. Demand: Bolton residents (BL1–BL7) in local community groups.
- **Where:** Bolton only.
- **Buyer:** Traders join free; residents use it free. Revenue (Pro) is a later test, not a 30-day goal.
- **Disqualify:** Gas or boiler work without a Gas Safe check; Driving instructors without a DVSA ADI check; Anyone who hasn't consented after reading how they'll appear

## Value proposition
> Traders: a free basic listing, for good, where nobody can pay to move up the list and your number is hidden from scrapers. Residents: recommended people you can actually find again, free, with no sign-up.

Evidence (verified facts):
- `audience-traders`: For local tradespeople, a basic listing on Bolton Vouched is free, for good.
- `value-no-pay-to-rank`: Nobody can pay to move up the list, and that promise is the heart of the product.
- `privacy-numbers-hidden`: Traders' phone numbers are never in the page's HTML, so scrapers reading the page find no phone numbers.
- `value-findable`: Recommended people are kept where you can find them, sorted by trade and by the BL areas they cover, with a button to call or WhatsApp them.
- `audience-residents`: For Bolton residents who need a trusted tradesperson, it is free to use with no account and no sign-up.
- `pain-buried-recommendations`: Good recommendations in the local WhatsApp group scroll away under hundreds of messages, so the next person has to ask all over again.

Don't lead with: 'Vetted' or 'checked' traders as a blanket claim (checks are per listing); Pro features or pricing (not built)

## Biggest unresolved assumptions
| ID | Risk | Assumption | How we test it | Decision rule |
|---|---|---|---|---|
| B-A1 | highest | Traders recommended in the group will consent to a listing when invited. | Track invited versus listed. | Needs 10 answers; ≥60% supporting. If not: Ask the ones who declined why (privacy, cold calls, effort) and address that first. |
| B-A2 | highest | Residents will use the directory instead of asking the group, producing enquiries for listed traders. | Enquiries from trader dashboards, logged weekly (the site deliberately has no analytics). | Needs 1 answers; ≥100% supporting. If not: Coverage is probably too thin: concentrate on three to five trades until each has several listings. |
| B-A3 | high | Group admins will allow a post about Bolton Vouched. | Ask the admin of each group before posting; record yes or no. | Needs 3 answers; ≥50% supporting. If not: Use offline channels: noticeboards, local shops, local press. |
| B-A4 | medium | A trade needs several listings before residents find it useful. | Compare enquiries per trade against listings per trade. | Needs 3 answers; ≥50% supporting. If not: Spread recruitment across more trades. |

## Prerequisites (yours)
- [ ] **B-P1** blocks *facebook_group*: The policy pages are drafts pending legal review; get them reviewed before a wide public push.
- [ ] **B-P2** blocks *contacted*: List the Bolton WhatsApp and Facebook groups you belong to, and ask each admin for permission.
- [ ] **B-P3** blocks *listed*: Approve the Bolton Vouched profile in the approval desk.

## Channels, in order
| # | Source | Who acts | How | Compliance |
|---|---|---|---|---|
| 1 | whatsapp_group | you | With the admin's agreement, post once in the Bolton Tradesmen group inviting recommended traders to reply if they want a free listing; send the consent link to those who ask. | Traders are mostly sole traders (individual subscribers): no unsolicited one-to-one marketing messages. An open invitation they answer makes the follow-up solicited. |
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
| paying | Paid (zero by design: Pro is not built) | 0 | 0 | 0 | 0 |

Supply first: enquiries only follow once several trades have listings.

## Messages (each passes the claim validator)
**bv-trader-invite** — Group post inviting traders to opt in (facts: audience-traders, value-no-pay-to-rank, privacy-numbers-hidden, feature-consent, url-site)

> For local tradespeople, a basic listing on Bolton Vouched is free, for good. Nobody can pay to move up the list, and traders' phone numbers are never in the page's HTML, so scrapers reading the page find no phone numbers. Every trader has agreed to be listed after reading exactly how they will appear. Reply if you'd like a listing. Find out more: https://boltonvouched.ysbdesigns.uk

**bv-resident** — Resident-facing post in a community group (facts: pain-buried-recommendations, value-findable, audience-residents, url-site)

> Good recommendations in the local WhatsApp group scroll away under hundreds of messages, so the next person has to ask all over again. Bolton Vouched keeps recommended people where you can find them, sorted by trade and by the BL areas they cover, with a button to call or WhatsApp them. Free to use with no account and no sign-up: https://boltonvouched.ysbdesigns.uk

## Discovery questions
1. Where do most of your new jobs come from today?
2. What puts you off being listed in directories?
3. Which BL areas do you cover?
4. Would you tell customers you're on Bolton Vouched so they can leave a review?

## Demo
Assets: https://boltonvouched.ysbdesigns.uk (live); assets/bolton-vouched/film/ (cinematic film); assets/bolton-vouched/bolton-vouched-2026-10-21-749d0c/ (campaign pack)

1. For a trader: show a live listing in their trade, the checks shown, the call/WhatsApp buttons, and that numbers are not in the page's HTML.
2. Show the trader dashboard: enquiries this month, edit description and areas, pause listing.
3. Explain consent: they read exactly how they'll appear before it goes live.

Never show: Pro tier or a price (not built)

## Pilot offer
Free listing, for good. Ask each listed trader to point happy customers to leave a review.

## Content
Post days: none · hypothesis: —. No connected page. Group posts are written and posted by you, using the messages below.
