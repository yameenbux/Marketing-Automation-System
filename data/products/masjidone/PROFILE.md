# MasjidOne

> Generated from `profile.json` — edit that, not this file. Source: `yameenbux/MasjidOne` README.

- **Maker:** not stated  
- **Type:** b2b_saas · **Maturity:** Live in a masjid today; some parts still tagged in development  
- **Approval:** draft
- **Brand:** primary #0C2A21, secondary #2C4C40, accent #C0A46A — Plain-spoken, candid and community-minded, careful never to overclaim and respectful of Islamic terminology.

## Overview

- MasjidOne is one system that brings together a masjid's madrasah and its congregation.  
  <sub>`overview-one-system` — “**One system for a masjid's madrasah and its congregation.**”</sub>
- Registers, fees and parent access sit on one side, with prayer times, a congregation app, the website, hall screens and donations on the other.  
  <sub>`overview-two-sides` — “Registers, fees and parent access on one side. Prayer times, a congregation”</sub>

## Target audience

- Built in Bolton for masājid across the UK.  
  <sub>`audience-uk-masajid` — “Built in Bolton, for masājid across the UK.”</sub>
- The website is designed for masjid committees who want to see what they would be buying and ask for a demo.  
  <sub>`audience-committees` — “The marketing site. Its job is to give a masjid committee somewhere to”</sub>
- Teachers, parents and the masjid office each get their own separate view, so a parent only ever sees their own children.  
  <sub>`audience-roles` — “The doors are deliberately separate. A parent is not a smaller administrator —”</sub>

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

## Integrations

- Payments go through the masjid's own Stripe account, and MasjidOne never touches the money.  
  <sub>`integration-stripe` — “| **Stripe** | The masjid's own account. We never touch the money |”</sub>
- Push notifications are delivered through OneSignal, scoped to each masjid.  
  <sub>`integration-onesignal` — “| **OneSignal** | Push, scoped per masjid |”</sub>

## Privacy and data

- Each masjid's data is separated by the database itself, so an administrator only ever reaches their own masjid's records.  
  <sub>`privacy-row-level-security` — “| **Row Level Security** | The database refuses the wrong rows; it is not an `if` statement in the app |”</sub>

## Pricing (as stated in the README)

- Pricing is banded by madrasah size across two plans, Madrasah and Masjid Complete, which adds the website, app, screens and donations.  
  <sub>`pricing-bands` — “**Pricing is banded by the size of the madrasah** — four bands by pupil count,”</sub>
- A one-off setup fee of £499 applies, waived when twelve months are prepaid.  
  <sub>`pricing-setup-fee` — “the app, the screens and donations). Setup is **£499 once**, waived on twelve”</sub>

## Links

- MasjidOne's website is at masjidone.co.uk.  
  <sub>`url-website` — “console is served from `masjidone.co.uk`; a masjid's portal is served from”</sub>
- A demonstration walkthrough at /demo/ shows the office, teacher, parent and app views using invented data.  
  <sub>`url-demo` — “`/demo/` is a sales walkthrough built from invented data in `lib/demo-data.ts`.”</sub>

## Calls to action

- Masjid committees can request a demo; MasjidOne is sold through a conversation rather than self-serve sign-up.  
  <sub>`cta-request-demo` — “a demo. It is not a self-serve signup — nobody buys this without a”</sub>

## Known limitations — never market these as done

- Parent access and Hifz and sabaq progress are described as in development in one section, though a later section says both are built; confirm status before promoting them.  
  <sub>`limitation-parent-access-status` — “What is still in development is *parent access* — the half a”</sub>
- The screen heartbeat is still tagged as in development and appears only in the demo.  
  <sub>`limitation-screen-heartbeat` — “Today **one thing carries the tag: the screen heartbeat**, and it is in the”</sub>
- The demo request form's email service is written and tested but not yet deployed, so the form currently opens the visitor's own mail client.  
  <sub>`limitation-demo-form-worker` — “**Resend's REST API**, which sends the email. **Written and tested, not yet”</sub>
- ICO registration and the data processing agreement are commitments promised before a masjid is invoiced, not yet completed facts.  
  <sub>`limitation-compliance-pending` — “data processing agreement are promised *before a masjid is invoiced*.”</sub>

## Competitors

_Not yet researched. Add only from permitted sources with citations._
