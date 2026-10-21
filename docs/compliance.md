# Compliance: identity, email and calls

**Not legal advice.** This is the working position the system enforces, written from the ICO's published guidance
on PECR and UK GDPR and the Companies House disclosure rules. Have it checked before you rely on it at volume.
Last reviewed 21 Oct 2026.

## 1. One company, five brands

MasjidOne, Domi, Booked In, Tidemark and Bolton Vouched are **trading names of YSB Ventures Ltd** (company number
16022339, registered in England and Wales, registered office 711 Crompton Way, Bolton, England, BL1 8TL; source:
Companies House, checked 21 Oct 2026). No brand is ever described as a separate company. The single source of truth
is [`config/company.json`](../config/company.json); everything below reads from it.

The Companies Act 2006 and the 2015 trading-disclosure regulations require the company's registered name, where it
is registered, its number and its registered office on **business letters, order forms and emails, and on its
websites**. Using a trading name doesn't remove that duty.

| Where | Status |
|---|---|
| Emails drafted by this system | ✅ Footer: sender, brand and site, "X is a trading name of YSB Ventures Ltd", registered name, place, number and office, opt-out (`mas.company.email_footer`) |
| Letters drafted by this system | ✅ Same disclosure; the addressee's registered address is filled in by you from the public register |
| Emails you sent by hand, 13–21 Oct | ⚠️ See section 3 |
| The five product websites | ❌ Not checked into this system and not editable by it. Each site's footer needs the same line. That's a change in each product repository, which you make (this system has read-only access) |

## 2. Email rules the system enforces

**Who may get an unsolicited marketing email (PECR reg 22).** Corporate subscribers (limited companies, LLPs,
public bodies) may, without prior consent, if the sender is identified and every message offers a simple way to opt
out. **Sole traders and partnerships count as individuals**: they need prior consent, and the "soft opt-in" doesn't
cover prospects. So:

- A role address at a limited company (info@, practice@) is the default target.
- A personal webmail address (gmail, outlook, hotmail…) usually means a sole trader or a person: **blocked** unless
  you have their consent recorded.
- If the legal form is unknown, the eligibility engine treats it as `manual_review`, never as eligible.

**A named person at a company is still personal data (UK GDPR).** The lawful basis is legitimate interests, which
needs an assessment (section 4). The person must be told who you are and how you got their details within a month,
and at the latest in the first message. A one-line link to a short **prospecting privacy notice** does that. **There
isn't one yet**, which is item 6 on your checklist.

**Every email:** honest subject (no "Re:" or "Fwd:" on a first email, nothing implying an existing relationship),
claims only from verified product facts (`mas.marketing.validator`), and the footer from section 1. Opt-outs and
bounces become suppressions automatically (`mas outreach sync-replies`) and are checked before any future draft.
**Never twice:** the ALREADY_CONTACTED rule blocks a second first email to any organisation already in the contact
history; follow-ups go in the existing thread.

**Sending stays off.** The Gmail connector can send, but no session sends without your explicit authorisation,
per brand and per batch. Until then the system's furthest step is a Gmail draft you review.

## 3. Emails sent by hand

Anything you send outside the system must meet section 2 too: opt-out line, full company details, no personal-webmail
recipients without consent, one follow-up at most. When you ask a Claude session to sync Gmail, it reads the Sent folder
(read-only) so these emails count in the contact history and their replies and opt-outs are honoured. Scheduled
runs can't do this yet: no connectors are attached to them. The review of the 13–21 Oct
campaign, which names recipients and numbers, is kept privately in `var/reports/` and never committed.

## 4. Legitimate Interests Assessment: B2B prospecting (DRAFT for you to approve)

**Purpose.** To offer YSB Ventures Ltd's products to organisations they're built for (masājid and madrasahs;
domiciliary eye-care and similar home-visit practices; Bolton tradespeople), by a short, relevant business email,
letter or call to a role contact or a named decision-maker.

**Necessity.** Small organisations rarely publish an alternative route. One business email or letter to a published
work contact is the least intrusive way to reach them. No purchased lists and no scraping of personal profiles:
contacts come from the organisation's own website or a public register, with the source URL recorded per lead.

**Balancing.**
- *Reasonable expectations:* a published work contact at an organisation can expect occasional relevant business
  approaches. Low for personal addresses, so they're excluded.
- *Impact:* low. One email, at most one follow-up in the same thread, an opt-out in every message, honoured
  immediately and kept on a suppression list.
- *Safeguards:* data minimised to organisation, role or name, work email, source URL, reason for fit. Stored in
  the gitignored local database and a private owner-only sheet, never in the public repository. Retention: prospects
  with no reply are deleted 12 months after last contact (**you to confirm**).
- *Vulnerable groups:* none targeted. Patients' and pupils' data is never used for prospecting.

**Outcome (draft).** Legitimate interests applies for B2B email and letters to corporate subscribers and named work
contacts, with the safeguards above. **Approve per brand in `config/outreach.json`: set `lia_documented: true` and
`lia_reference` to "docs/compliance.md#4" plus the date you approved it.** Until then
email eligibility stays blocked by the system.

## 5. Phone calls

Live marketing calls to businesses are allowed unless the number is on the **Corporate TPS** (or the TPS, for sole
traders) or the organisation has told you not to call. Screen each number against TPS/CTPS before calling (a
screening service may cost money and needs your approval). Say who you are and which company you're calling from,
and give the number on request. Never use automated or recorded calls: they need prior consent.

## 6. Company housekeeping spotted while checking

- **Confirmation statement due by 29 Oct 2026** (Companies House). Late filing can lead to the company being struck
  off.
- **ICO data-protection fee:** confirm that YSB Ventures Ltd, the controller for prospecting and for the product data,
  is registered (the Domi README says its ICO registration is done; MasjidOne's isn't).
