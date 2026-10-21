# MasjidOne: 30-day acquisition plan

Priority 1 · 2026-10-22 to 2026-11-20 · generated from `config/acquisition.json` by `mas acq docs` (edit the config, not this file).

## Ideal customer
- **Who:** A UK masjid that is a registered charity and runs an evening madrasah, where the office keeps registers, fees and family records by hand or across several tools.
- **Where:** Within driving distance of Bolton first (Bolton, Blackburn, Manchester, Preston, Oldham, Rochdale, Burnley), so you can demo in person.
- **Buyer:** The masjid committee decides; the madrasah head and office administrator feel the pain and will champion it.
- **Disqualify:** No madrasah or classes; Already committed to another masjid platform in the last 12 months; No one on the committee willing to meet

## Value proposition
> One system for the madrasah and the congregation: the child in tonight's register is the same family record the office already holds.

Evidence (verified facts):
- `value-one-family-record`: The child in an evening register is the same record the congregation side already holds.
- `value-madrasah-operations`: MasjidOne runs the madrasah's daily operations — the register, the sabaq heard and the fee due — in the same system as the congregation side.
- `pain-family-known-three-times`: The office often holds the same family in separate places and can only connect them from memory.
- `feature-missed-register-flag`: When a teacher marks the evening register, the office knows by the next morning which class did not.
- `value-local-support`: There is no overseas or outsourced support desk; masājid speak to the team who wrote the system and can fix it.

Don't lead with: Zero-commission donations and Gift Aid (a competitor advertises both); Parent access or Hifz/sabaq progress (README contradicts itself on status); That MasjidOne is the only product that runs the whole masjid (its README says plenty of products do the congregation side, and do it well)

## Biggest unresolved assumptions
| ID | Risk | Assumption | How we test it | Decision rule |
|---|---|---|---|---|
| M-A1 | highest | Madrasah admin (registers, fees, family records) is a top-three problem for the committee, painful enough to change systems. | Ask in each discovery conversation, before showing anything: 'What takes the office the most time each week?' Record whether madrasah admin comes up unprompted. | Needs 8 answers; ≥60% supporting. If not: Stop leading with the madrasah. Re-run discovery around what they did name (often prayer-time screens or the website) and check MasjidOne's facts support it before pitching. |
| M-A2 | high | Committees will pay a banded subscription plus the £499 setup fee (waived on twelve months prepaid). | In every demo, state the price structure plainly and ask 'Is that within what the committee would approve?' Record yes / no / needs committee. | Needs 5 answers; ≥40% supporting. If not: Test the setup fee as the objection: offer the prepaid waiver first. If price still fails, collect the figure they would approve before changing anything. |
| M-A3 | high | Referrals and in-person visits reach decision-makers far better than letters, email or social media. | Every conversation is logged with its source; compare conversation rate per source after 30 contacts. | Needs 10 answers; ≥50% supporting. If not: Shift effort to whichever source converts best in the dashboard's source table. |
| M-A4 | high | The masjid already running MasjidOne will introduce you to neighbouring masājid and take a reference call. | Ask the committee in week 1 for two introductions and permission for one reference call. | Needs 1 answers; ≥100% supporting. If not: Ask what would make them comfortable recommending it; fix that first, because a product its first masjid won't vouch for will not sell to the second. |
| M-A5 | medium | Moving existing rolls and family records is not a deal-breaker. | Ask what they use today and whether they can export it (spreadsheet or CSV). | Needs 5 answers; ≥60% supporting. If not: Offer to do the first import by hand for early masājid and time how long it takes. |

## Prerequisites (yours)
- [ ] **M-P5** blocks *pilot*: A known platform fix is needed before a second masjid can be signed (README: 'Blocking the moment a second masjid is signed'). Schedule it before proposing any pilot.
- [ ] **M-P1** blocks *paying*: ICO registration and a data processing agreement: the README says both are promised before a masjid is invoiced, and neither is done.
- [ ] **M-P2** blocks *pilot*: Resolve the README's contradiction: one section says parent access and Hifz/sabaq progress are in development, another says both are built. Never demo or promise either until it is settled.
- [ ] **M-P3** blocks *website_inbound*: Deploy the demo-request form's email service; today it opens the visitor's own mail client, so web enquiries can be lost.
- [ ] **M-P4** blocks *pilot*: Approve the MasjidOne profile in the approval desk.

## Channels, in order
| # | Source | Who acts | How | Compliance |
|---|---|---|---|---|
| 1 | referral | you | Ask the masjid already using MasjidOne for two introductions; they make the first contact. | Not unsolicited marketing: the introducer contacts them, or they ask to hear from you. |
| 2 | in_person | you | Visit Bolton-area masājid at office hours or after Jumu'ah; ask for the secretary or madrasah head and leave the one-page summary. | No PECR restriction on face-to-face contact. Respect a no. |
| 3 | post | you (system drafts) | Letter addressed 'To the Committee' at the address on the Charity Commission register, followed by a visit or call a week later. | Post is outside PECR. Addressed to a role, not a named person, so no personal data is processed. Honour any request to stop. |
| 4 | email | you, after approval | Only to the leads the eligibility engine marks eligible (corporate subscriber, generic address). | Blocked until your sender identity and opt-out are set in config/outreach.json. Unincorporated masājid are individual subscribers under PECR: no unsolicited email. |
| 5 | phone | you | Call the masjid office number to ask who handles the madrasah. | Screen the number against TPS/CTPS first; don't call if it is registered or if they object. |
| 6 | instagram | system drafts, you approve | Two posts a week as proof the product is real when a committee member looks you up. Not expected to generate leads at about 1 follower. | Approval desk; live publishing only after approval. |

The prioritised prospect list (organisations, sources, qualification reasons and permitted contact methods per organisation) is in the approval desk's Pipeline tab and `mas acq prospects masjidone`. It is not stored in this repository.

## Weekly targets
| Stage | Definition | W1 | W2 | W3 | W4 |
|---|---|---|---|---|---|
| contacted | Committee or office reached (letter, visit, introduction or email) | 8 | 10 | 10 | 8 |
| conversation | A real two-way conversation with someone at the masjid | 3 | 4 | 4 | 4 |
| qualified | Runs an evening madrasah, the admin pain is confirmed, and a decision-maker (chair, secretary, treasurer or madrasah head) is involved | 2 | 3 | 3 | 3 |
| demo | Walkthrough of the office, teacher and parent views held with the decision-maker | 1 | 2 | 2 | 2 |
| pilot | Agreed to run their own classes in MasjidOne for a set period | 0 | 0 | 1 | 1 |
| paying | Signed and invoiced | 0 | 0 | 0 | 1 |

Paying in week 4 is a stretch and only possible once M-P1 is done; otherwise count a signed letter of intent as the week-4 win.

## Messages (each passes the claim validator)
**masjidone-letter-core** — Letter or eligible email: the core paragraph (facts: pain-family-known-three-times, value-madrasah-operations, value-one-family-record, cta-request-demo, url-website)

> The office often holds the same family in separate places and can only connect them from memory. MasjidOne runs the madrasah's daily operations — the register, the sabaq heard and the fee due — in the same system as the congregation side, so the child in an evening register is the same record the congregation side already holds. Masjid committees can request a demo at https://masjidone.co.uk

**masjidone-office-hook** — Opening line for a visit or call with the office (facts: feature-missed-register-flag, value-local-support, cta-request-demo)

> When a teacher marks the evening register, the office knows by the next morning which class did not. There is no overseas or outsourced support desk; you speak to the team who wrote the system. Committees can request a demo.

**masjidone-control** — When the committee worries about depending on a supplier (facts: feature-self-service-content, pain-waiting-on-support, integration-stripe, cta-request-demo)

> A masjid should not have to open a ticket just to change its own prayer times. The masjid changes its own jamāʿah times, notices, fee rates and access straight away in the portal, and payments go through the masjid's own Stripe account. Request a demo to see it.

## Discovery questions
1. How do you run the madrasah week today: registers, fees, contacting parents?
2. Roughly how many pupils are in the madrasah? (It sets the pricing band.)
3. What takes the office the most time each week?
4. When a family has children in classes and parents in the congregation, where does each part live?
5. Who decides on new systems, and when does the committee next meet?
6. What would you need to see to try something new with one class?

## Demo
Assets: https://masjidone.co.uk/demo/ (walkthrough with invented data); assets/masjidone/film/ (cinematic film); assets/masjidone/masjidone-2026-10-21-2fad1a/ (campaign pack: video, cards, storyboard)

1. Ask the discovery questions first; only demo once M-A1 has been answered.
2. Open the demo with the committee's own masjid name (feature-demo-own-name).
3. Office view: one family record shared by the madrasah and congregation sides (value-one-family-record).
4. Teacher view: mark a register; show the next-morning missed-register flag (feature-missed-register-flag).
5. Fees configured in the madrasah portal (feature-madrasah-portal).
6. Self-service: change a jamāʿah time live (feature-self-service-content).
7. Price: two plans, four bands by pupil count; yearly is the same rate twelve times over, not a discount; the £499 setup fee is waived when twelve months are prepaid (pricing-four-bands-two-plans, pricing-yearly-not-discounted, pricing-setup-fee). Never quote the retired £79/£179 flat rates. Ask the M-A2 question.
8. Close: propose a pilot with their own classes and a date to decide.

Never show: Parent access or Hifz/sabaq progress until M-P2 confirms the status; The screen heartbeat (still in development)

## Pilot offer
Run one or more of your own classes in MasjidOne for an agreed period, with weekly check-ins and you doing any setup. At the end the committee decides. Real pupil data only after M-P1 (ICO registration and data processing agreement) is done.

## Content
Post days: [1, 3] · hypothesis: M-A3. Credibility for prospects who check Instagram after a letter or visit; measured by whether conversations mention it, not by views.
