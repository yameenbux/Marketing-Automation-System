# Domi: 30-day acquisition plan

Priority 2 · 2026-10-22 to 2026-11-20 · generated from `config/acquisition.json` by `mas acq docs` (edit the config, not this file).

## Ideal customer
- **Who:** An England-based domiciliary optometry practice run as a limited company, with several clinicians on the road and a waiting list.
- **Where:** England only (Domi models English sight-test rules only).
- **Buyer:** The owner or director; the practice manager who builds the diary is the day-to-day champion.
- **Disqualify:** Scotland, Wales or Northern Ireland; Single-clinician sole trader (routing and refills matter less, and they are individual subscribers under PECR); Almost all visits are NHS sight tests booked under 48 hours ahead (see D-A2)

## Value proposition
> Plenty of systems keep a diary; Domi acts on the gap. When a patient cancels, it texts the best-matched person on the waiting list and books the first yes.

Evidence (verified facts):
- `value-act-on-gap`: Plenty of systems keep a diary; Domi acts on the gap by finding who fits it, asking them by text and booking the first yes.
- `overview-refill`: When a patient cancels, Domi texts the best-matched person on the waiting list and books the first one who says yes.
- `pain-cancellations`: A cancellation costs a home-visit practice more than a clinic, because the clinician is already on the road and the gap is too short to fill by ringing round.
- `feature-cancel-by-text`: Patients can cancel by texting CANCEL, which starts the refill with no staff involved.
- `feature-book-by-road`: New visits are booked where they add the least driving, weighed against how soon the patient needs to be seen.
- `feature-income-mileage`: Domi reports recovered income and cancellations refilled, plus per-clinician mileage and utilisation downloadable as CSV.

Don't lead with: Replacing the practice management system (incumbents lead on eGOS; Domi still lodges PCSE notifications by hand); Same-day refills of NHS sight tests (PCSE needs 48 hours' notice)

## Biggest unresolved assumptions
| ID | Risk | Assumption | How we test it | Decision rule |
|---|---|---|---|---|
| D-A1 | highest | Cancellations happen often enough, and cost enough, that a practice would pay to refill them. | Ask: 'In a typical week, how many visits cancel per clinician, and what happens to that time?' Record their numbers and whether they call it a cost. | Needs 6 answers; ≥50% supporting. If not: Reposition around route planning and booking by road (feature-book-by-road, feature-route-planning) and test that instead. |
| D-A2 | highest | Enough cancelled slots can legally be refilled: private visits, or NHS visits cancelled at least 48 hours ahead. | Ask the NHS/private split and how much notice cancellations usually give. | Needs 5 answers; ≥50% supporting. If not: The refill engine only fits private or longer-notice work; target private-heavy practices or other home-visit services (hearing, foot care) and re-check the facts before pitching them. |
| D-A3 | high | Practices will run Domi alongside their existing practice system rather than demand a full replacement or integration. | Ask what they use for the diary and records, and whether a separate refill and route tool is acceptable. | Needs 5 answers; ≥60% supporting. If not: Find out which integration matters most and size it before building. |
| D-A4 | medium | Practices will invest time as design partners before Domi can hold real patient data. | Offer a structured two-week design-partner review on invented data. | Needs 4 answers; ≥50% supporting. If not: Real-data readiness (D-P1) becomes the first job before more selling. |

## Prerequisites (yours)
- [ ] **D-P1** blocks *paying*: Before real patients: a permanent UK database with tested backups, real accounts and compliance paperwork (from the README).
- [ ] **D-P3** blocks *email*: Set sender identity and opt-out in config/outreach.json before any email.
- [ ] **D-P4** blocks *pilot*: Approve the Domi profile in the approval desk.

## Channels, in order
| # | Source | Who acts | How | Compliance |
|---|---|---|---|---|
| 1 | phone | you | Call the practice number and ask for the owner or practice manager; offer a 15-minute conversation about cancellations, not a demo. | Live calls to businesses are allowed unless the number is on CTPS/TPS or they object. Screen first. |
| 2 | email | you, after approval | The 5 practices the engine marks eligible (limited company, generic address). | Blocked until D-P3. Sole traders are excluded automatically. |
| 3 | linkedin_manual | you | Connect with owners and practice managers personally and write each message yourself; join optometry discussions. | Manual only: LinkedIn's terms forbid automated connection requests, messages and scraping. |
| 4 | post | you (system drafts) | Letter to the practice (role-addressed) before a follow-up call. | Post is outside PECR; role-addressed. |
| 5 | event | you | Optical trade events and press (e.g. Optometry Today) for later; not a 30-day channel. | — |

The prioritised prospect list (organisations, sources, qualification reasons and permitted contact methods per organisation) is in the approval desk's Pipeline tab and `mas acq prospects domi`. It is not stored in this repository.

## Weekly targets
| Stage | Definition | W1 | W2 | W3 | W4 |
|---|---|---|---|---|---|
| contacted | Practice reached (call, email, LinkedIn message written by you, or letter) | 6 | 8 | 8 | 6 |
| conversation | A two-way conversation with the owner, director or practice manager | 2 | 3 | 3 | 3 |
| qualified | England domiciliary eye care, more than one clinician, and cancellations are a stated cost | 1 | 2 | 2 | 2 |
| demo | Working demo walked through with the decision-maker | 1 | 1 | 2 | 2 |
| pilot | Design partner: agreed to a structured trial on invented data and regular feedback | 0 | 0 | 1 | 1 |
| paying | Paid (not expected within 30 days: Domi can't hold real patient data yet) | 0 | 0 | 0 | 0 |

Paying is zero by design until D-P1. The 30-day win is two design partners and clear answers on D-A1 and D-A2.

## Messages (each passes the claim validator)
**domi-core** — Email or letter core paragraph (facts: pain-cancellations, value-act-on-gap, feature-cancel-by-text, url-demo)

> A cancellation costs a home-visit practice more than a clinic, because the clinician is already on the road and the gap is too short to fill by ringing round. Plenty of systems keep a diary; Domi acts on the gap by finding who fits it, asking them by text and booking the first yes. Patients can cancel by texting CANCEL, which starts the refill with no staff involved. Try the working demo: https://app.domi.ysbdesigns.uk

**domi-roads** — If refills don't land (D-A1 or D-A2 contradicted) (facts: feature-book-by-road, feature-route-planning, feature-income-mileage, url-website)

> New visits are booked where they add the least driving, weighed against how soon the patient needs to be seen. Route planning puts visits that haven't started in the order that drives least, and Domi reports per-clinician mileage and utilisation. Find out more at https://domi.ysbdesigns.uk

## Discovery questions
1. How many clinicians are on the road, and how is the diary built today?
2. In a typical week, how many visits cancel per clinician, and how much notice do you get?
3. Roughly what share of visits are NHS sight tests versus private?
4. What happens to a cancelled slot today?
5. Would a separate refill and route tool alongside your current system be acceptable?

## Demo
Assets: https://app.domi.ysbdesigns.uk (working demo, invented patients; wake it first); assets/domi/film/ (cinematic film); assets/domi/domi-2026-10-21-749d0c/ (campaign pack)

1. Open the hosted demo a few minutes beforehand: it sleeps when idle.
2. Discovery questions first (D-A1, D-A2, D-A3).
3. Cancel a visit by text and watch the refill rank candidates with reasons (feature-refill-engine, feature-cancel-by-text).
4. Book a new visit by road (feature-book-by-road) and show route planning.
5. Clinician phone view and offline notes (feature-clinician-app, feature-offline).
6. Recovered income, refills and mileage reports (feature-income-mileage).
7. Be upfront: working demo, no customers yet, not for real patient data until D-P1. Offer the design-partner trial.

Never show: Hearing-care workflows as built (ready to set up, not built); Automatic PCSE notifications (lodged by hand)

## Pilot offer
Design partner: two weeks using the working demo with invented patients modelled on a typical week of yours, a 30-minute review each week, and first say on what gets built next. No real patient data until D-P1.

## Content
Post days: none · hypothesis: —. No connected account and no evidence that social posts reach practice owners. No content until a channel is connected and a hypothesis needs it.
