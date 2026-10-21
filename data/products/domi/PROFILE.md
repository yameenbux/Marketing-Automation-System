# Domi

> Generated from `profile.json` — edit that, not this file. Source: `yameenbux/audiologydomi` README.

- **Maker:** YSB Ventures Ltd  
- **Type:** b2b_saas · **Maturity:** working demo  
- **Approval:** draft
- **Brand:** primary #1E4D40, secondary #15241F, accent #E07B4F — Plain-spoken, practical and scrupulously honest about what is and isn't built, written for busy home-visit practices in British English.

## Overview

- Domi is a diary for home-visit healthcare that refills itself when patients cancel.  
  <sub>`tagline` — “**Home-visit diaries that refill themselves.**”</sub>
- When a patient cancels, Domi texts the best-matched person on the waiting list and books the first one who says yes.  
  <sub>`overview-refill` — “patient cancels, Domi texts the best-matched person on the waiting list and books”</sub>

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

- Plenty of systems keep a diary; Domi acts on the gap by finding who fits it, asking them by text and booking the first yes.  
  <sub>`value-act-on-gap` — “Plenty of systems keep a diary. What Domi does differently is **act on the gap**:”</sub>
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
- Every visit gets a day-before reminder text, and a CANCEL reply refills that slot a day ahead.  
  <sub>`feature-reminders` — “A CANCEL reply refills that slot a day ahead”</sub>
- Domi reports recovered income and cancellations refilled, plus per-clinician mileage and utilisation downloadable as CSV.  
  <sub>`feature-income-mileage` — “Recovered income, cancellations refilled, average time to refill and income still unfilled, from the office's own fee per visit”</sub>

## Integrations

- Leads from the practice's Facebook ad forms can arrive in Domi via a connector such as Zapier, Make or Meta's own webhook.  
  <sub>`integration-facebook-leads` — “A connector (Zapier or Make's Facebook Lead Ads trigger, or Meta's own webhook) posts each lead to”</sub>

## Privacy and data

- From a patient's record, the office can download everything held about them or erase their details on request, in line with UK GDPR.  
  <sub>`privacy-gdpr` — “From the record: download everything held about a patient (subject access), or erase their details on request.”</sub>

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
- The demo is not for real patient data: it keeps everything in memory and holds invented patients only.  
  <sub>`limitation-no-real-data` — “**The demo is not for real patient data.** It keeps everything in memory, holds”</sub>
- Before real patients, Domi still needs a permanent UK database with tested backups, along with real accounts and compliance paperwork.  
  <sub>`limitation-hosting` — “**A permanent UK database:** managed Postgres in London, encrypted, with daily backups and a restore that has actually been tested.”</sub>
- Domi has no customers yet, so there are no testimonials or logos to show.  
  <sub>`limitation-no-customers` — “Domi has none yet, so no testimonials, logos or "trusted”</sub>
- Hearing care is ready to set up rather than built for, and Noah 4 integration is not built.  
  <sub>`limitation-ready-to-set-up` — “| **Hearing care** | Ready to set up | Hearing tests, fittings, wax removal and aid reviews as visit types; audiogram records set up with th…”</sub>
- PCSE notifications are still lodged by hand; sending them automatically is on the roadmap.  
  <sub>`limitation-pcse-manual` — “Sending them to PCSE automatically is on the roadmap”</sub>
- Scotland, Wales and Northern Ireland have their own sight-test rules, which Domi doesn't model yet.  
  <sub>`limitation-nations` — “Ireland have their own rules, which Domi doesn't model yet.”</sub>
- NHS sight tests can't fill a same-day gap: PCSE needs a pre-visit notification at least 48 hours ahead.  
  <sub>`limitation-nhs-same-day` — “home needs a pre-visit notification (PVN) to PCSE at least 48 hours ahead”</sub>
- The hosted demo runs on a free plan that sleeps when idle and takes a short while to wake.  
  <sub>`limitation-demo-sleeps` — “On the free plan it **sleeps after 15 minutes without visits** and takes about”</sub>

## Competitors

_Not yet researched. Add only from permitted sources with citations._
