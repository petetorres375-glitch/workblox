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
