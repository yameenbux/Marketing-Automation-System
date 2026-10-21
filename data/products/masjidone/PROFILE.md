# MasjidOne

> Generated from `profile.json` — edit that, not this file. Source: `yameenbux/MasjidOne` README.

- **Maker:** not stated  
- **Type:** b2b_saas · **Maturity:** Live with one customer masjid; the madrasah portal and congregation side are running, parent access status is disputed within the README, and onboarding a second masjid is blocked by a known fix.  
- **Approval:** draft
- **Brand:** primary #0C2A21, secondary #2C4C40, accent #C0A46A — Plain-spoken, candid and community-minded, careful never to overclaim and respectful of Islamic terminology.

## Overview

- MasjidOne is one system that brings together a masjid's madrasah and its congregation.  
  <sub>`overview-one-system` — “**One system for a masjid's madrasah and its congregation.**”</sub>
- Registers and fees sit on the madrasah side, with prayer times, a congregation app, the website, hall screens and donations on the congregation side.  
  <sub>`overview-two-sides` — “Registers, fees and parent access on one side. Prayer times, a congregation app, the website, the hall screens and donations on the other.”</sub>

## Target audience

- Built in Bolton for masājid across the UK.  
  <sub>`audience-uk-masajid` — “Built in Bolton, for masājid across the UK.”</sub>
- The website is designed for masjid committees who want to see what they would be buying and ask for a demo.  
  <sub>`audience-committees` — “The marketing site. Its job is to give a masjid committee somewhere to”</sub>

## Pain points addressed

- Many masājid run their week across several tools that do not talk to each other.  
  <sub>`pain-disconnected-tools` — “A typical masjid runs its week across half a dozen things that have never”</sub>
- The office often holds the same family in separate places and can only connect them from memory.  
  <sub>`pain-family-known-three-times` — “can join them up only by remembering.”</sub>
- A masjid should not have to open a ticket just to change its own prayer times.  
  <sub>`pain-waiting-on-support` — “**A masjid never waits on us for its own content.** If the office has to open a”</sub>

## Value proposition

- MasjidOne runs the madrasah's daily operations — the register, the sabaq heard and the fee due — in the same system as the congregation side.  
  <sub>`value-madrasah-operations` — “nobody else does is running the **madrasah's daily operations** — the”</sub>
- The child in an evening register is the same record the congregation side already holds.  
  <sub>`value-one-family-record` — “*didn't*; and the child in that register is the same record the congregation”</sub>
- There is no overseas or outsourced support desk; masājid speak to the team who wrote the system and can fix it.  
  <sub>`value-local-support` — “There is no overseas support desk and no outsourced queue. A masjid talks to”</sub>

## Verified features

- Every masjid gets four surfaces: a website, in-masjid screens, a congregation app and a madrasah portal, in its own colours and on its own domain.  
  <sub>`feature-four-surfaces` — “The four surfaces: website, in-masjid screens, congregation app, madrasah portal”</sub>
- The madrasah portal holds the masjid's roll, classes, staff and households, with registers and fees configured.  
  <sub>`feature-madrasah-portal` — “**The madrasah portal is built. Parent access is not.** The portal holds a”</sub>
- When a teacher marks the evening register, the office knows by the next morning which class did not.  
  <sub>`feature-missed-register-flag` — “The clearest way to explain the product is to follow a single Tuesday. A teacher”</sub>
- The congregation app brings times, reminders, notices and giving to iOS and Android.  
  <sub>`feature-congregation-app` — “| **React Native · Expo** | The congregation app, iOS and Android |”</sub>
- Prayer-time screens run from one timetable across every screen in the masjid.  
  <sub>`feature-prayer-screens` — “| `/mosque-prayer-times-screens/` | One timetable, every screen |”</sub>
- Donations carry zero commission and support Gift Aid.  
  <sub>`feature-donations` — “| `/mosque-donations/` | 0% commission and Gift Aid |”</sub>
- The masjid changes its own jamāʿah times, notices, fee rates and access straight away in the portal.  
  <sub>`feature-self-service-content` — “| A wrong jamāʿah time, a notice, a fee rate, who has access | **The masjid**, in the portal | Immediately |”</sub>
- The demo can be opened with the committee's own masjid name shown.  
  <sub>`feature-demo-own-name` — “the committee sees their own name”</sub>

## Integrations

- Payments go through the masjid's own Stripe account, and MasjidOne never touches the money.  
  <sub>`integration-stripe` — “| **Stripe** | The masjid's own account. We never touch the money |”</sub>
- Push notifications are delivered through OneSignal, scoped to each masjid.  
  <sub>`integration-onesignal` — “| **OneSignal** | Push, scoped per masjid |”</sub>

## Privacy and data

- Each masjid's data is separated by the database itself, so an administrator only ever reaches their own masjid's records.  
  <sub>`privacy-row-level-security` — “| **Row Level Security** | The database refuses the wrong rows; it is not an `if` statement in the app |”</sub>
- When MasjidOne support staff enter a masjid they do not belong to, a support-access entry is written to that masjid's own audit trail.  
  <sub>`privacy-support-access-audited` — “Refuses a masjid you neither belong to nor administer, and writes `masjidone_support_access` into **their** audit trail when it is the latte…”</sub>
- MasjidOne's support console requires platform administrators to complete a second sign-in factor.  
  <sub>`privacy-support-console-2fa` — “Requires `is_aal2()` — a completed second factor, so the console has a real authenticator step”</sub>
- Marketing and demo imagery never publishes a real child's record or a family's fee history.  
  <sub>`privacy-no-real-child-data-published` — “no real child's record or family's fee history is ever published.”</sub>

## Pricing (as stated in the README)

- Pricing is banded by madrasah size across two plans, Madrasah and Masjid Complete, which adds the website, app, screens and donations.  
  <sub>`pricing-bands` — “**Pricing is banded by the size of the madrasah** — four bands by pupil count,”</sub>
- A one-off setup fee of £499 applies, waived when twelve months are prepaid.  
  <sub>`pricing-setup-fee` — “the app, the screens and donations). Setup is **£499 once**, waived on twelve”</sub>
- Yearly billing is the monthly rate twelve times over, not a discount; only the setup fee is waived.  
  <sub>`pricing-yearly-not-discounted` — “Yearly billing is the same rate shown twelve times over, not a discount.”</sub>
- Bands are not per-pupil pricing: the price changes only at renewal, and only when the madrasah crosses a band threshold.  
  <sub>`pricing-band-changes-at-renewal` — “A band is **not** per-pupil pricing: the figure changes only at renewal, and only on crossing a threshold.”</sub>
- The old flat prices of £79 and £179 are no longer current and should not be quoted; prices now come from the banded table.  
  <sub>`pricing-old-flat-rates-retired` — “This README printed `£79` and `£179` until 8 October 2026 — the flat rates”</sub>
- There are four pricing bands by pupil count, across the two plans.  
  <sub>`pricing-four-bands-two-plans` — “**Pricing is banded by the size of the madrasah** — four bands by pupil count,”</sub>

## Links

- MasjidOne's website is at masjidone.co.uk.  
  <sub>`url-website` — “console is served from `masjidone.co.uk`; a masjid's portal is served from”</sub>
- A demonstration walkthrough at /demo/ shows the office, teacher, parent and app views using invented data.  
  <sub>`url-demo` — “`/demo/` is a sales walkthrough built from invented data in `lib/demo-data.ts`.”</sub>
- Customer support is reached at support@masjidone.co.uk.  
  <sub>`url-support-email` — “customer support reaches `support@masjidone.co.uk`”</sub>

## Calls to action

- Masjid committees can request a demo; MasjidOne is sold through a conversation rather than self-serve sign-up.  
  <sub>`cta-request-demo` — “a demo. It is not a self-serve signup — nobody buys this without a”</sub>
- The support route is live, and enquiries can be sent to info@masjidone.co.uk.  
  <sub>`cta-enquiries-email` — “**The support route is live.** Enquiries reach `info@masjidone.co.uk` and”</sub>

## Known limitations — never market these as done

- The README contradicts itself. One section says parent access and Hifz and sabaq progress are in development and tagged as such. Another says both are built and that only the screen heartbeat is still tagged. Confirm their status before promoting either.  
  <sub>`limitation-parent-access-status` — “What is still in development is *parent access* — the half a”</sub>
- The screen heartbeat is still tagged as in development and appears only in the demo.  
  <sub>`limitation-screen-heartbeat` — “Today **one thing carries the tag: the screen heartbeat**, and it is in the”</sub>
- The demo request form's email service is written and tested but not yet deployed, so the form currently opens the visitor's own mail client.  
  <sub>`limitation-demo-form-worker` — “**Resend's REST API**, which sends the email. **Written and tested, not yet”</sub>
- ICO registration and the data processing agreement are commitments promised before a masjid is invoiced, not yet completed facts.  
  <sub>`limitation-compliance-pending` — “data processing agreement are promised *before a masjid is invoiced*.”</sub>
- A known platform change has to be made before a second masjid can be signed.  
  <sub>`limitation-second-masjid-blocker` — “Blocking the moment a second masjid is signed.”</sub>
- Other products already cover the congregation side well, so MasjidOne should not be described as the only product that runs the whole masjid.  
  <sub>`limitation-competitors-congregation-side` — “Plenty of products do the congregation side, and do it well.”</sub>

## Competitors

_research — re-verify before any public comparative claim (CAP Code 3.33–3.44) — researched 2026-10-21 via WebSearch/WebFetch of public pages._

- **IBEAMS (IBEUK)** (partial) — Cloud management system for maktabs, madrasahs and Islamic private schools covering attendance, fees (outstanding balances, reminders), a parent portal showing attendance, invoices and communications, and student records. Pricing: Published in GBP per month: Basic £15 (up to 50 students), Standard £30 (up to 150), Enterprise £60 (unlimited); unlimited teachers, email support, no set-up fee. Add-ons include Student Diary £10/month, phone & Telegram support £10/month, remove ads £5/month.. <sub>https://ibeuk.org/, https://ibeuk.org/pricing/</sub>
- **Teach 'n Go** (partial) — General class-management platform with an Islamic school/Qur'an programme page: per-session attendance, invoices/receipts and fee tracking, a parent and learner portal, recurring evening/weekend scheduling, announcements, mobile app, 24 languages including Arabic. Pricing: not published. <sub>https://www.teachngo.com/solutions/islamic-school-software</sub>
- **Masjidbox** (direct) — Suite of mosque products: Screens (digital signage with prayer times, countdown, announcements, donation campaigns), branded Applications, web Pages with custom domain, Donations, widgets, social visuals and calendars, plus a worshipper app (Masjidbox One). Pricing: Published in EUR per month: Screens Free €0 / Silver €29; Applications Free €0 / Silver €29; Pages Free €0 / Silver €15; Global plan (all three) €62. Donations listed as free with a '0% platform fee' (Stripe/bank transfer fees may apply). Annual billing advertised as '1 month free'.. <sub>https://www.masjidbox.com/, https://www.masjidbox.com/pricing</sub>
- **MosqueApp Ltd** (direct) — UK company (High Wycombe) building custom-branded iOS/Android apps for mosques with prayer times, Adhan and push notifications, donations (Sadaqah, Zakat, appeals) and live streaming; also offers app-synced display screens and mosque websites. Pricing: Figures not published. Site states no subscription fees: a one-off build cost plus a small annual hosting and maintenance fee; quote/demo required.. <sub>https://mosqueapp.co.uk/</sub>
- **MAWAQIT** (substitute) — Non-profit, open-source prayer-time platform; its app lists mosque-set Salah and iqamah timetables, Azan notifications, Qibla, Hijri calendar, mosque search and donation options, with admins able to manage Iqama, Ramadan and Eid schedules. Pricing: App listing states '100% Free and without any Ads, no subscription needed'.. <sub>https://apps.apple.com/us/app/-/id1460522683, https://mawaqit.net/en/</sub>
- **easyDonate** (substitute) — UK donation platform for charities and organisations: in-person donation kiosks, online donations and Gift Aid (Standard and Small Donations Scheme) with HMRC-ready reports. Pricing: No figures published on the homepage; it states 'We don't work on any percentages or commission, you keep all the donations you make.'. <sub>https://easydonate.uk/</sub>

**Positioning takeaways (hypotheses):**
- On the pages fetched, no competitor appeared to combine madrasah management (registers, fees, parent access) with congregation tools; madrasah tools (IBEAMS, Teach 'n Go) and congregation tools (Masjidbox, MosqueApp, MAWAQIT) appear to sit in separate products — this supports the 'one system / one family record' message, but must be re-verified before any comparative claim.
- '0% commission and Gift Aid' is unlikely to be a differentiator on its own: Masjidbox advertises a 0% platform fee and automatic UK Gift Aid claiming, and easyDonate says it takes no commission. Lead with integration, not fee.
- Price anchors are low on single-purpose tools: IBEAMS starts at £15/month with no set-up fee, Masjidbox has free tiers, MAWAQIT is free. MasjidOne's £499 setup fee will need justifying by the joined-up madrasah + congregation value and direct UK support.
- MosqueApp Ltd is the closest UK-based like-for-like on the congregation side and lists a madrasah module as a future feature — MasjidOne's window to claim 'built madrasah portal' is real but may narrow; also avoid promoting parent access as done until its status is confirmed.
- Support model may differentiate: IBEAMS charges £10/month for phone support, whereas MasjidOne's profile states masājid speak directly to the team who wrote the system — usable as a hedged, non-comparative claim about MasjidOne itself.
