# Domi

> Generated from `profile.json` — edit that, not this file. Source: `yameenbux/audiologydomi` README.

- **Maker:** YSB Ventures Ltd  
- **Type:** b2b_saas · **Maturity:** Working demo plus a live London pilot environment. It has no customers or patients yet, and the compliance paperwork is outstanding.  
- **Approval:** draft
- **Brand:** primary #1E4D40, secondary #15241F, accent #E07B4F — Plain-spoken, practical and scrupulously honest about what is and isn't built, written for busy home-visit practices in British English.

## Overview

- Domi is a diary for home-visit healthcare that refills itself when patients cancel.  
  <sub>`tagline` — “**Home-visit diaries that refill themselves.**”</sub>
- When a patient cancels, Domi works out who on the waiting list could take the slot, then either gives the office a ranked call list, texts the best match and books the first yes, or books them straight in.  
  <sub>`overview-refill` — “It either hands the office a ranked call list (many home-visit patients never answer a text), texts the best match and books the first yes, …”</sub>
- An environment is set up for a first pilot practice; it holds no patients until that pilot is signed.  
  <sub>`overview-live-pilot-environment` — “set up > for a first pilot practice. It holds no patients until that pilot is signed”</sub>

## Target audience

- Domi is built for healthcare that comes to the patient's home, including eye care, hearing, foot care, dental, physio, blood tests, nursing and therapy assessments.  
  <sub>`audience-services` — “The diary for healthcare that comes to the patient's home: eye care, hearing,”</sub>
- Domiciliary eye care is the service Domi is built for today, and the demo is an eye-care practice.  
  <sub>`audience-eyecare` — “| **Domiciliary eye care** | Built for it: the demo is an eye-care practice |”</sub>

## Pain points addressed

- A cancellation costs a home-visit practice more than a clinic, because the clinician is already on the road and the gap is too short to fill by ringing round.  
  <sub>`pain-cancellations` — “A home-visit practice loses more to a cancellation than a clinic does. The”</sub>
- Patients on the waiting list who would happily take a freed slot often never hear about it.  
  <sub>`pain-waiting-list` — “round, and the people on the waiting list who would have taken it never hear”</sub>

## Value proposition

- Domi acts on the gap in the way the practice chooses: a ranked call list for the office, an offer by text that books the first yes, or booking the best match straight in.  
  <sub>`value-act-on-gap` — “That's a ranked call list for the office, an offer by text that books the first yes, or booking the best match straight in.”</sub>
- Patients see the practice's own name in every text, on the booking page and on invoices, never Domi's.  
  <sub>`value-own-name` — “**Patients see the practice, not Domi.** Every patient text, the booking page and invoices use the practice's name”</sub>

## Verified features

- The refill engine ranks candidates by clinical priority, locality, days waiting and preferred clinician, and shows the reasons for each.  
  <sub>`feature-refill-engine` — “Ranking: clinical priority, then local, days waiting, preferred clinician. Each candidate shows the reasons”</sub>
- Patients can cancel by texting CANCEL, which starts the refill with no staff involved.  
  <sub>`feature-cancel-by-text` — “A patient texting CANCEL cancels the visit and starts the refill, with no staff involved.”</sub>
- New visits are booked where they add the least driving, weighed against how soon the patient needs to be seen.  
  <sub>`feature-book-by-road` — “putting them where they add the least driving, weighed against how soon the”</sub>
- Route planning puts visits that haven't started in the order that drives least, from the clinician's home base and back.  
  <sub>`feature-route-planning` — “Visits that haven't started are put in the order that drives least, from the clinician's home base and back.”</sub>
- A phone-first clinician view shows today's round with drive times, patient records, quick notes and an On my way text to the patient.  
  <sub>`feature-clinician-app` — “Phone-first. Today's round with drive times, patient records (alerts, last prescription, glasses, history)”</sub>
- The clinician app works offline, syncing notes and visit updates in order when signal returns.  
  <sub>`feature-offline` — “notes and visit updates made without signal sync in order when it returns. Signing out wipes the copy”</sub>
- An online referral form replaces callback forms and paper, and accepting a referral creates the patient record and a waiting-list place.  
  <sub>`feature-referral-form` — “accepting one creates the patient record and a waiting-list place and texts whoever gave a mobile”</sub>
- A CANCEL reply to a reminder refills that slot a day ahead.  
  <sub>`feature-reminders` — “A CANCEL reply refills that slot a day ahead”</sub>
- Domi reports recovered income and cancellations refilled, plus per-clinician mileage and utilisation downloadable as CSV.  
  <sub>`feature-income-mileage` — “Recovered income, cancellations refilled, average time to refill and income still unfilled, from the office's own fee per visit”</sub>
- With Phone them, the office gets a ranked call list, best match first, with numbers ready, and logs each outcome in one tap.  
  <sub>`feature-three-fill-modes` — “**Phone them** (for practices whose patients don't text; the demo's default is *Text an offer*): the office gets a ranked call list, best ma…”</sub>
- Each NHS sight test visit gets its PCSE notice rule: 48 working hours, 3 weeks for three or more patients at one address, and never more than 8 weeks ahead.  
  <sub>`feature-pcse-notice-rules` — “Each NHS sight test visit (one address on one day) gets its notice rule: 48 working hours, 3 weeks for three or more at one address, never m…”</sub>
- Bookings that can't meet the PCSE notice are refused unless the ICB's approval is recorded.  
  <sub>`feature-pcse-icb-approval` — “Bookings that can't meet the notice are refused unless the ICB's approval is recorded.”</sub>
- Each visit gets three confirmation calls: when it's booked, in the week before with a 3-hour arrival window from the planned route, and on the working day before.  
  <sub>`feature-confirmation-calls` — “Each visit gets three calls: **CC1** when it's booked (the date only), **CC2** in the week before (a 3-hour arrival window worked out from t…”</sub>
- Pilot results use figures from the diary or from what the office records, never estimates.  
  <sub>`feature-pilot-results` — “Every number comes from the diary or from what the office records, never from an estimate”</sub>
- Staff sign in with a password and then a six-digit authenticator code.  
  <sub>`feature-two-factor` — “Password (scrypt) then a six-digit authenticator code (TOTP).”</sub>
- Practices can import patients from a CSV saved from Google Sheets or Excel, up to 5,000 rows.  
  <sub>`feature-patient-import` — “Upload a CSV saved from Google Sheets or Excel (up to 5,000 rows).”</sub>

## Integrations

- Leads from the practice's Facebook ad forms can arrive in Domi via a connector such as Zapier, Make or Meta's own webhook.  
  <sub>`integration-facebook-leads` — “A connector (Zapier or Make's Facebook Lead Ads trigger, or Meta's own webhook) posts each lead to”</sub>
- Domi works alongside Opticabase, which stays the record for eye tests and claims: a daily CSV export imports cleanly, matched by Opticabase ID.  
  <sub>`integration-opticabase` — “Opticabase stays the record for eye tests and claims. A daily CSV export imports cleanly, matched by Opticabase ID:”</sub>

## Privacy and data

- From a patient's record, the office can download everything held about them or erase their details on request, in line with UK GDPR.  
  <sub>`privacy-gdpr` — “From the record: download everything held about a patient (subject access), or erase their details on request.”</sub>
- Live data sits in a permanent UK database, Supabase Postgres in London, with daily backups and a tested restore.  
  <sub>`privacy-uk-database` — “**A permanent UK database:** Supabase Postgres in London (Pro plan, daily backups), with a restore tested by `scripts/restore-test.sh`.”</sub>
- ICO registration is listed as done.  
  <sub>`privacy-ico` — “- **ICO registration.** Still to do before the first real patient:”</sub>

## Pricing (as stated in the README)

_Not stated — do not publish prices._

## Links

- Find out more at domi.ysbdesigns.uk.  
  <sub>`url-website` — “Made by YSB Ventures Ltd · [domi.ysbdesigns.uk](https://domi.ysbdesigns.uk)”</sub>
- Try the neutral working demo at app.domi.ysbdesigns.uk.  
  <sub>`url-demo` — “demo at [app.domi.ysbdesigns.uk](https://app.domi.ysbdesigns.uk/?brand=domi)”</sub>

## Known limitations — never market these as done

- Domi is a working demo and is not yet used by any practice.  
  <sub>`limitation-not-used` — “**Everything in green is built, tested and working in the demo. Domi is not yet”</sub>
- The demo is not for real patient data.  
  <sub>`limitation-no-real-data` — “**The demo is not for real patient data.** It keeps everything in memory, holds”</sub>
- Before the first real patient, the paperwork with the practice is still to do: the DPIA (drafted), the data processing agreement and a check that the practice's DSPT is in place.  
  <sub>`limitation-hosting` — “**The paperwork with the practice:** the DPIA (drafted), the data processing agreement, and a check that their DSPT is in place.”</sub>
- Domi has no customers yet, so there are no testimonials or logos to show.  
  <sub>`limitation-no-customers` — “Domi has none yet, so no testimonials, logos or "trusted”</sub>
- Hearing care is ready to set up rather than built for, and Noah 4 integration is not built.  
  <sub>`limitation-ready-to-set-up` — “| **Hearing care** | Ready to set up | Hearing tests, fittings, wax removal and aid reviews as visit types; audiogram records set up with th…”</sub>
- PCSE notifications are still lodged by hand; sending them automatically waits on PCSE accepting Domi as a connected system.  
  <sub>`limitation-pcse-manual` — “Sending to PCSE automatically waits on PCSE accepting Domi as a connected system”</sub>
- Scotland, Wales and Northern Ireland have their own sight-test rules, which Domi doesn't model yet.  
  <sub>`limitation-nations` — “Scotland, Wales and Northern Ireland have their own rules, which Domi doesn't”</sub>
- NHS sight tests can't fill a same-day gap.  
  <sub>`limitation-nhs-same-day` — “**NHS sight tests can't fill a same-day gap.** In England, an NHS sight test at”</sub>
- The hosted demo runs on a free plan that sleeps when idle and takes a short while to wake.  
  <sub>`limitation-demo-sleeps` — “On the free plan it **sleeps after 15 minutes without visits** and takes about”</sub>
- Domi and Opticabase can't talk to each other yet, so bookings, moves and cancellations made in Domi are copied across to Opticabase by hand from a checklist.  
  <sub>`limitation-opticabase-manual` — “The two systems can't talk to each other yet, so that copying is done by hand”</sub>

## Competitors

_research — re-verify before any public comparative claim (CAP Code 3.33–3.44) — researched 2026-10-21 via WebSearch/WebFetch of public pages._

- **Opticabase (with Opticabase Home add-on)** (direct) — UK optical practice management system (recalls, dispensing, clinical notes, eGOS England) with an 'Opticabase Home' add-on described as 'Software for Optician domiciliary providers without the need for an internet connnection'. A 2022 AOP feature says it also provides an electronic solution for pre-visit notifications and that over 650 practices in the UK and Ireland use Opticabase. Pricing: Published ex VAT: Full Clinical System £195/month/practice; Opticabase Home add-on £70/month/practice (£35/month for fewer than 35 domiciliary visits/month); SMS 5.5p per text. <sub>https://www.opticabase.co.uk, https://www.opticabase.co.uk/prices</sub>
- **Blink OMS (GenerationNET)** (partial) — Cloud-based optician management system with integrated eGOS submission to PCSE, online booking through the practice website, recalls and SMS text reminders to patients in the next clinic. Pricing: not published. <sub>https://www.blinkoms.co.uk</sub>
- **Acuitas 3 (Ocuco)** (partial) — Optical practice management software for UK practices covering scheduling, staff and clinic performance, eGOS integration (GOS1, GOS3, GOS4), and recall/marketing with automatic recalls, SMS reminders and email marketing. Pricing: not published. <sub>https://www.ocuco.com/uk/</sub>
- **OctopusPro (Mobile Optometrist & Domiciliary Optician Scheduling)** (partial) — Generic field-service platform with a page marketed at mobile optometrists and domiciliary opticians: practitioner rotas and visit routes on one calendar, proximity-based scheduling, GPS tracking, branded online booking portal, automated email/SMS/app reminders and a practitioner mobile app with forms that 'can be completed online or offline'. Pricing: Published: Starter $36.25/month ($348/year); Established $60 USD per admin seat + $6 USD per fieldworker seat per month; Unlimited Users $99 USD platform fee/month plus $1 per booked job or 2% of invoiced revenue. <sub>https://octopuspro.com/mobile-optic-schedule-software, https://octopuspro.com/pricing/</sub>
- **OptimoRoute** (substitute) — Route optimisation and planning tool with automated planning, weekly planning (Pro), a driver mobile app that receives routes and sends real-time updates, and real-time order tracking with customer ETA notifications. Pricing: Published per driver per month, billed annually: Lite $35.10; Pro $44.10; Custom on request. <sub>https://optimoroute.com/pricing/</sub>
- **Cal.com** (substitute) — General booking/scheduling tool with an optometry page offering routing/intake forms that match patients to the right optometrist, calendar sync with Google/Outlook/Apple, multi-location bookings, analytics and a self-hosting option. Pricing: not published. <sub>https://cal.com/routing/routing-for-optometrists</sub>

**Positioning takeaways (hypotheses):**
- None of the six fetched competitor pages mention automatically refilling a cancelled slot from a waiting list by text, so 'acts on the gap' appears to be a genuine differentiator — re-verify each vendor before saying so publicly, and avoid absolute 'only' claims.
- Optical PMS vendors (Opticabase, Blink OMS, Acuitas 3) lead on NHS eGOS integration and, for Opticabase, pre-visit notifications; Domi lodges PCSE notifications by hand, so messaging should position Domi on diary/refill/routing rather than NHS claims, or as complementary to an existing PMS.
- Opticabase publishes a dedicated domiciliary add-on price (£70/month, or £35/month under 35 visits/month, on top of £195/month), giving a visible UK price anchor for domiciliary software buyers.
- Generic field-service and routing tools (OctopusPro, OptimoRoute) cover route optimisation and SMS reminders but publish USD pricing and do not mention NHS/eye-care records; Domi can stress being built for UK domiciliary eye care with clinical context (prescriptions, alerts) in the clinician app.
- Offline working is offered by Opticabase Home and OctopusPro forms, so offline support is table stakes rather than a differentiator; recovered-income reporting and least-driving booking are not mentioned by any fetched competitor and may resonate more.
