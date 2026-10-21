# Portfolio marketing strategy — all five products

**Status:** strategist output, 21 Oct 2026; stages refreshed from the READMEs the same evening. Built from verified profiles (`data/products/*/profile.json`),
competitor research (`competitors.json`, which must be re-verified before any public comparison, per CAP Code
3.33–3.44), ICPs (`config/icp.json`) and the Metricool baseline. Hypotheses are marked as such.

## The portfolio at a glance

| Product | Audience | Stage (README) | Where the audience is | Outbound allowed? | Connected channel |
|---|---|---|---|---|---|
| **MasjidOne** | UK masjid committees | Live with one customer masjid; signing a second is blocked by a known platform fix; parent-access status contradictory in the README | Instagram, WhatsApp, word of mouth between masājid | Only to corporate subscribers (CIOs, charitable companies) with an LIA; most masājid are individual subscribers | Instagram `masjidone.uk` (~1 follower) |
| **Domi** | Domiciliary eye-care practices (England) | Working demo plus a live London pilot environment (UK hosting and ICO registration done); no customers; practice paperwork outstanding | LinkedIn, optical trade press | Limited companies only, with an LIA | none |
| **Booked In** | Solo beauty pros (lash, brows, nails; also barbers and clinics) | Built; email live, **subscription billing not live**; three features not built | Instagram | No: sole traders | none |
| **Tidemark** | Privacy-minded iPhone users | Built, **no signed build, not on the App Store**; no waitlist | Instagram, App Store | No: consumers | none |
| **Bolton Vouched** | Bolton residents + local traders | Live at www.boltonvouched.co.uk with Pro (£10/month) built; **2 listings** on 21 Oct | Facebook, local community groups | No: consumers and sole traders | none |

## What the evidence says about positioning

| Product | Lead with | Don't lead with (and why) |
|---|---|---|
| MasjidOne | **One system, one family record**: madrasah *and* congregation together. None of the 6 competitors researched combined both on the pages fetched | "0% commission + Gift Aid": Masjidbox advertises both |
| Domi | **Acts on the gap**: refills a cancelled slot by text, plans routes, shows recovered income. None of the 6 competitors mentioned this on the pages fetched | Replacing the practice system: incumbents (e.g. Opticabase) lead on eGOS and pre-visit notifications, which Domi still does by hand. Position it as working *alongside* the practice system |
| Booked In | **No marketplace: her page shows only her.** Patch-test records | "No commission": Fresha, Booksy and Treatwell say bookings through the pro's own link are commission-free too |
| Tidemark | **How it explains the trend** ("a guide, not a verdict"), plus the dose log | "The only trend tracker" or "the only no-account app": at least four apps smooth the trend, and two also claim no account |
| Bolton Vouched | **Nobody can pay to move up the list**, and each listing shows which checks were actually recorded | "Vetted traders": the checks are per listing, and blanket claims are blocked by the validator |

The validator enforces the "don't" column wherever it's a factual risk: exclusivity claims, superlatives,
unbuilt features, paid ranking, and medicine names for Tidemark.

## The uncomfortable truth: distribution, not content, is the bottleneck

The only connected account has **about 1 follower**, reach of 0–1 a day, and has posted daily since 14 October.
A calendar of 30 well-made posts into that account will not produce demo requests. Four of the five products
have **no channel at all**. More content is not the next lever. These are, in order:

1. **Owned channels per product** (£0): an Instagram for Booked In and Tidemark, a Facebook page for Bolton
   Vouched, LinkedIn for Domi, all connected in Metricool. Until then the calendar produces drafts only for them.
2. **Borrowed audiences you already belong to** (£0, posted by you, never automated):
   - Bolton Vouched: the Bolton Tradesmen WhatsApp group it was built from.
   - MasjidOne: the masjid it already runs in; ask that committee for an introduction to neighbouring masājid
     (a referral, not marketing).
   - Domi: optical trade communities on LinkedIn.
3. **Launch-gated products:** Tidemark's real launch moment is App Store approval, and Booked In's is provisioning.
   Build a waitlist now (a website form with explicit consent, so it's lawful to email later). Spend the
   creative effort at launch, not before.

## Weekly operating rhythm (all five together)

- **Calendar:** `mas calendar --weeks 2`. Round-robin across all five products, 3 posts a day on weekdays, one per
  product per day, so each product gets about 6 posts a fortnight on its primary platform. Every slot is a
  validated draft.
- **Your time:** about 20 minutes a week approving drafts (`mas content --status validated`, then `mas approve`).
- **Creative:** one campaign pack per product per month (`mas campaign <slug>`, about 3 minutes of CPU, £0).
- **Measurement:** profile visits and link clicks per product. Add UTM tags when links go live. Review the daily report.

## Budget (£0–£50/month)

| Item | Cost | Verdict |
|---|---|---|
| Rendering, TTS, sync, calendar, validation | £0 | in use |
| Metricool | your current plan | check whether it covers 5 brands; the free tier limits brands |
| ElevenLabs re-voicing for 5 launch videos | credits on your plan | worthwhile for the 5 hero videos only |
| Small paid boosts | £0 until there's an organic baseline | no evidence yet to justify spend |

## Decisions only you can make

1. Confirm MasjidOne parent-access status (the README contradicts itself).
2. Is Booked In marketed **pre-launch** (waitlist) or held until provisioned?
3. Which accounts will you create or connect for Domi, Booked In, Tidemark and Bolton Vouched?
4. Approve the five profiles. Nothing can be approved for publishing until you do.
