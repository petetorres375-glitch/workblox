# Workblox — To-Do

Open items as of September 24, 2026. Check them off (or delete them) as they're done.

## Accounts & safety
- [ ] Set spending caps on the AI provider accounts (Anthropic, OpenAI): turn off auto-reload/auto-recharge and set a monthly limit. OpenAI is only the backup provider, so keep a small balance there.
- [ ] Make this repository private. Decided September 24, 2026; started, then paused.
  - [x] Scanned the full git history for committed secrets. None found.
  - [x] Chose the free route: publish the Personal app from a separate public repo, the way the Business app already works.
  - [ ] Create the public `workblox-personal` repo and give the deploy token access to it.
  - [ ] Check that Railway's GitHub app can still read this repo once it's private.
  - [ ] Push the deploy-workflow change (drafted, saved in `git stash`), then move the `workblox.torrestechremote.com` domain to the new repo in Pages settings.
  - [ ] Make this repo private, then confirm the site and the next Railway deploy still work.

## Testing & follow-ups
- [ ] Approve your own Spreadsheet Organizer and Expense Organizer requests (Personal app → Admin → pending requests).
- [ ] Have a friend test both apps. If they have a Mac or iPhone, ask them to upload a `.numbers` file to Spreadsheet Organizer and open the file it returns.
- [ ] Contract Analyzer: the AI also returns "important dates" and "termination clauses", but the screen and the PDF don't show them. The 120-day auto-renewal on the sample contract sometimes landed there and never reached the customer. Show both sections.
- [ ] Before real traffic: the server handles 8 requests at once. For a few hundred active users, raise the thread count, and check Anthropic's per-minute rate limits for the account.
- [ ] Some past contract reports may have come from the OpenAI backup instead of Claude (the old 25-second timeout sent long analyses there). Fixed September 24; nothing to do unless a customer asks about an old report.

## Get found on search
- [ ] Add torrestechremote.com to Google Search Console (verify via DNS at Porkbun), submit the sitemap, request indexing.
- [ ] Add the site to Bing Webmaster Tools (import from Search Console).
- [ ] Create a Google Business Profile for Torres Tech Remote.
- [ ] List Workblox on a LinkedIn company page and AI-tool directories.
- [ ] Website fixes: clean up sitemap.xml (drop the page that no longer exists, refresh dates), add canonical tags and structured data, sharpen the home page title.
- [ ] Later: a landing page per tool (e.g. AI resume builder, AI contract analyzer).

## Payments
- [ ] Get an EIN (free, at irs.gov).
- [ ] Open a Stripe account.
- [ ] Connect Workblox to Stripe so a payment turns on access automatically.
- [ ] Once customers can cancel through Stripe, update the cancellation line in the website's Terms of Service.

## When revenue allows
- [ ] Check New Jersey business registration and sales-tax rules for software subscriptions.
- [ ] Business license and insurance.
- [ ] Native-speaker review of translations for the languages customers actually use.
- [ ] Confirm the `.numbers` and `.pages` support on a real Apple device.

## Done September 24, 2026
- Fixed a 2.5-hour outage: a library update (SQLAlchemy 2.1) crashed the server. The version is now pinned in **both** requirements files; Railway builds from the root one.
- Report times show the customer's local time instead of UTC.
- PDF reports: headings no longer sit alone at the bottom of a page, and the Contract Analyzer shows a colored risk badge.
- Contract Analyzer moved to Claude Sonnet 5 (~3¢ per contract) with stricter accuracy rules. It now gets 90 seconds to respond, and the server allows 120.
- The server handles 8 requests at once instead of one. PDF reading and OCR were made safe for this.
- Long PDFs: tools stop reading once they have enough text, and one person's long upload no longer blocks others.
- Doc Analyzer takes up to 10 scanned pages per PDF, and both analyzers show their upload limits under the upload box.
