# Booked In: 30-day acquisition plan

Priority 4 · 2026-10-22 to 2026-11-20 · generated from `config/acquisition.json` by `mas acq docs` (edit the config, not this file).

## Ideal customer
- **Who:** A UK lash, brow or tinting technician working on her own, mobile or from home or a rented chair, who takes bookings through Instagram DMs today.
- **Where:** Online UK-wide; in person around Bolton and Manchester so you can sit with her while she sets it up.
- **Buyer:** She is the buyer and the user. She decides in a minute, on her phone, between clients.
- **Disqualify:** Works in a salon whose owner runs the booking system; Happy on Fresha, Booksy or Treatwell and gets most new clients from their marketplace; No Instagram or link-in-bio habit

## Value proposition
> Her clients book themselves from her own page, and a treatment that needs a patch test can't be booked without one.

Evidence (verified facts):
- `overview-self-booking`: Her clients book themselves from a link in her Instagram bio.
- `pain-dm-eleven-pm`: A client asks at eleven at night whether Saturday is free; by the time she answers, the client has gone quiet and the slot is still empty.
- `value-page-is-hers`: The page is hers: her photographs, her prices, her link, and no marketplace showing her client three other technicians nearby.
- `feature-patch-test`: Treatments that need a patch test cannot be booked by someone who has not had one in time, and the patch-test booking itself becomes the record.
- `pain-patch-test-compliance`: Most booking platforms leave patch-test compliance to the technician, even though a missing dated record can put her insurance cover at risk.
- `pricing-free-tier`: There is a Free plan, and the patch-test rule is on it as well as on the paid plans.

Don't lead with: The fourteen-day Pro+ trial or any paid tier: billing has never taken a real payment (K-P1); Custom domains, rescheduling or posting straight to Instagram: not built; Named competitors' prices, unless you have checked them that week (the site's own calculator does this); Anything implying existing customers: there are none to point to yet

## Biggest unresolved assumptions
| ID | Risk | Assumption | How we test it | Decision rule |
|---|---|---|---|---|
| K-A1 | highest | A technician who signs up will put the link in her bio and take a real client booking within fourteen days. | Track signed_up against live for each signup. | Needs 5 answers; ≥50% supporting. If not: Stop promoting. Ask each one what stopped her (setup, trust, clients prefer DMs) and fix the first week before finding more signups. |
| K-A2 | high | Patch-test enforcement is a reason to switch that DM booking and the big platforms don't give her. | Ask every signup and conversation what made her try it; log 'supports' when she names patch tests or insurance. | Needs 8 answers; ≥30% supporting. If not: Lead with the eleven o'clock DM and 'the page is hers' instead; keep patch tests as the reason to stay. |
| K-A3 | medium | The 'Powered by Booked In' line on live pages brings new studios. | Ask every signup how she heard; log 'supports' when it was a client's booking page. | Needs 10 answers; ≥10% supporting. If not: Growth has to come from referrals and groups; ask live studios for introductions instead. |
| K-A4 | high | A studio on the Free plan will pay ten pounds a month for deposits, reminders and rebooking. | Untestable until K-P1. Then offer Pro to active studios and log yes or no. | Needs 5 answers; ≥40% supporting. If not: Ask what would be worth paying for; don't cut the price first. |

## Prerequisites (yours)
- [ ] **K-P1** blocks *signed_up*: Billing has never taken a real payment (README). Every new studio starts a fourteen-day Pro+ trial, so the first one ends fourteen days after the first signup. Before then, either make Stripe live and run one real payment end to end (check the stripe-webhook's SUPABASE_SERVICE_ROLE_KEY first, the README's open question), or change the site so nobody is asked to pay.
- [ ] **K-P2** blocks *instagram*: Confirm migrations 029 and 032 are applied in production. The README found that anyone holding the page's public key could delete every booking; re-run its own non-destructive check (a DELETE filtered to a tenant that cannot exist must be refused, not return 204) before driving any traffic.
- [ ] **K-P3** blocks *instagram*: Book an appointment end to end on a real iPhone in Safari. The README says it hasn't been tested there, and most of her clients will book from an iPhone.
- [ ] **K-P4** blocks *instagram*: Site: the footer says 'a YSB Designs product'; add 'Booked In is a trading name of YSB Ventures Ltd' with the company number, place of registration and registered office. And remove 'your own domain and posting a Story straight to Instagram are next' from the Pro+ card: the README says never to describe them, and 'this price is locked' turns it into a promise.
- [ ] **K-P5** blocks *instagram*: Connect @bookedin.uk (Instagram, and TikTok if you want it) to Metricool, then list it under booked-in in config/channels.json. Until then you post by hand; the system will never post Booked In to another product's account.

## Channels, in order
| # | Source | Who acts | How | Compliance |
|---|---|---|---|---|
| 1 | referral | you | Ask the technicians you already know (first, the technician whose page Booked In grew from) who they'd introduce, and ask every new signup for two names. | The introducer makes the first contact; you reply. No messages to people who haven't asked. |
| 2 | instagram | you | Post from @bookedin.uk using the messages below (by hand until K-P5). Comment helpfully under UK lash and brow posts as yourself; answer anyone who messages first. | Never send an unsolicited DM: the ICO treats direct messages as electronic mail, and sole traders are individuals under PECR. |
| 3 | facebook_group | you | In UK lash and brow business groups you belong to, with the admin's agreement, share the patch-test and insurance point (the group post below) rather than an advert. | Posted by you, never automated; respect each group's rules. |
| 4 | in_person | you | Lash and brow training academies (their students need a booking page on day one) and technicians you meet around Bolton and Manchester: set the page up with her, on her phone. | Face to face. Academies are businesses: a phone call is fine after a TPS/CTPS check; email stays off. |
| 5 | website_inbound | system | The site's guides (patch tests and insurers; a Booksy alternative) bring searchers. Ask every signup how she heard and log it. | — |

The prioritised prospect list (organisations, sources, qualification reasons and permitted contact methods per organisation) is in the approval desk's Pipeline tab and `mas acq prospects booked-in`. It is not stored in this repository.

## Weekly targets
| Stage | Definition | W1 | W2 | W3 | W4 |
|---|---|---|---|---|---|
| contacted | A beauty pro reached in person, by a referral, or one who answered a group or Instagram post (not views or likes) | 3 | 12 | 15 | 15 |
| signed_up | She created a page (count from the platform's studio list) | 1 | 4 | 6 | 8 |
| live | Her page took its first real client booking | 0 | 2 | 3 | 5 |
| active | Five or more real bookings in her first fourteen days, with the link in her bio | 0 | 0 | 2 | 3 |
| paying | Paid for Pro or Pro+ (none possible until billing is live: K-P1) | 0 | 0 | 0 | 0 |

Guesses for a product with no customers yet; week 1 is nearly over. Paying stays at 0 until K-P1. The number that matters is live: a live page carries 'Powered by Booked In' to her clients.

## Messages (each passes the claim validator)
**bookedin-dm-pain** — Instagram post: the problem (facts: pain-dm-eleven-pm, overview-self-booking, value-not-the-bottleneck, url-website)

> A client asks at eleven at night whether Saturday is free. By the time you answer, she has gone quiet and the slot is still empty. With Booked In your clients book themselves from a link in your Instagram bio, and bookings arrive while you are working. booked-in.co.uk

**bookedin-patch-test** — Instagram post: the reason to switch (tests K-A2) (facts: pain-patch-test-compliance, feature-patch-test, pricing-free-tier, url-website)

> Most booking platforms leave patch tests to you, even though a missing dated record can put your insurance cover at risk. On Booked In, a treatment that needs a patch test can't be booked by someone who hasn't had one in time, and the patch-test booking itself becomes the record. That rule is on the Free plan too. booked-in.co.uk

**bookedin-page-is-hers** — Instagram post: against the marketplaces (facts: value-page-is-hers, value-no-commission, url-website)

> Your page should be yours: your photographs, your prices, your link, and no marketplace showing your client three other technicians nearby. No commission, and nobody else advertised on it. booked-in.co.uk

**bookedin-group-post** — Facebook group post, with the admin's agreement (facts: pain-reaction-claim, overview-booking-page, feature-patch-test, pricing-free-tier, url-website)

> For anyone doing lashes, brows or tinting: if a client reacts and you can't produce a dated patch-test record, the insurance meant to cover it may not. Booked In is a booking page built for solo beauty professionals, and a treatment that needs a patch test can't be booked by someone who hasn't had one in time. The patch-test booking itself becomes the record, and that's on the Free plan. booked-in.co.uk

**bookedin-in-person** — What to say when you meet a technician or an academy (facts: overview-self-booking, feature-no-double-booking, feature-live-changes, pricing-free-tier, url-website)

> Your clients book themselves from a link in your Instagram bio. Two clients can't take the same slot, and a change to a price, your hours or a day off is live on your page as soon as you save it. There's a Free plan. booked-in.co.uk

## Discovery questions
1. How do clients book you today, and what happens to a DM you see at eleven at night?
2. Does your insurer ask for patch tests on anything you do? Where is your record of them now?
3. Have you used Fresha, Booksy or Treatwell? What made you stay or leave?
4. How did you hear about Booked In?

## Demo
Assets: booked-in.co.uk on her phone; your phone, to book as a client

1. Start free with her email and trade; the treatments and prices arrive filled in
2. Check the prices and add one photograph
3. Book a test appointment from your phone and watch it land in her diary
4. Show the patch-test rule refusing a lash booking for a client with no test
5. Put the link in her Instagram bio

Never show: The Pro+ trial or a checkout: billing has never taken a real payment; Custom domains, rescheduling or posting to Instagram: not built; The original client's page as a sample: her clients' faces are on it

## Pilot offer
No pilot needed: the Free plan is the trial. Offer to set her page up with her, on her phone, in ten minutes.

## Content
Post days: none · hypothesis: K-A2. @bookedin.uk isn't connected to Metricool (K-P5), so you post the messages below by hand. Judge them by signups that mention them, not views.
