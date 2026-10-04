# Checker report, round 18 (21 of 28 fetches/searches used; log-checker.jsonl)

## A. Paywalled or removed features list: WEAKENED (fix: drop the "list" framing, only viable as a press-hook page on one named-brand incident)
- Open lists: GNU Proprietary Subscriptions (https://www.gnu.org/proprietary/proprietary-subscriptions.html) opened: 17 entries 2014 to 2025 (A said about 10), no source links, includes BMW 2023-09 too. Rossmann wiki Canon page (https://wiki.rossmanngroup.com/wiki/Canon) opened: Canon 2025, status "Unknown", no list of similar products. No dedicated free tracker turned up in a fresh search; Techdirt company pages (e.g. Snoo) act as informal archive.
- Spot-check (5 records): Canon (Slashdot 2025-01-17, $4.99/$49.99, HD/brightness/colour) held. Peloton Just Run ($39.99/mo, 3 months waived) held. Echo (pcper: article 2025-03-17, effective 2025-03-28) held but it is a privacy-option removal, not a paywall. Cloud Cam (9to5mac: shutdown 2022-12-02, Blink $30/yr, Zigbee lost) held but it is a shutdown. Zero motorcycles did NOT hold: 9to5mac gives a passing mention only, no 2021 date. GNU-based records (Echelon, Snoo, Tesla, BMW, Wink, HP, Canary) match GNU wording and dates exactly (GNU lists 9 of the companies; verified 7 dates), but carry no primary source, so they fail the "source URL you opened" rule. Held up: 4 of 5 outside GNU; 1 unsupported; 9 of 13 are one unsourced page.
- Buyer: none found. Odds: 100 free users in 30 days about 35% (one press hook needed; A's 50% is too kind); 10,000 in six months about 4%.
- Cheapest test: static page of 30 sourced events, post one named-brand story (BMW, Canon, Echo) to Hacker News and r/rightToRepair; count visits.

## C. AI model retirement table: KILLED (already exists, including the "uncovered vendors" slice)
- vorplabs.com/models/deprecations opened: covers Cohere, Mistral, xAI, DeepSeek plus about 13 more vendors, 34 entries as of 2026-09-07, free JSON and CSV, CC BY 4.0, lists Cohere embed-english-v2.0 retired 2026-04-04.
- aimodelgraveyard.com opened (Product Hunt: free, no sign-up, 8 points): 458+ models, "Buried 84", covers Cohere, Mistral, xAI, DeepSeek and 70+ providers.
- hidekazu-konishi calendar opened: 4 platforms, updated 2026-09-25. Inventor guessed vorplabs and Graveyard might cover the gap; both do.
- Spot-check (7 records): Opus 4.1 2026-08-05, GPT-5-codex 2026-07-23, Sora-2 2026-09-24, whisper-1 2027-02-26 held on the calendar; Cohere embed-v2 2026-04-04, command-r/r-plus 2025-09-15, rerank-v2 (announced 2024-12-02, shutdown 2025-04-30) held on Cohere's page. 7 of 7 true, but every one is in a free list.
- Buyer: none found. Odds: 100 users in 30 days 15%; 10,000 in six months under 1%. Cheapest test: none worth running.

## D. Maintainer Wanted: KILLED (existing free lists, crowded verdict lookups, no spread)
- seeking-maintainers.net opened: live, free, about 26 projects, no dates. GitHub topic looking-for-maintainer opened: 47 repos. Fresh search for "is this package abandoned" lookups: Apify actors, graveyard-check, deps-scout, many scanners.
- Spot-check (4 records): Scientist.NET (2019-01-21, archive deadline 2019-02-04, moved to scientistproject) held. PeerJS (2023-12-05, joiners 18 and 30 Dec) held. m-cli 9.9k stars and phplint, redmine client held on the topic page, but the "date" is the repo's last update, not the date of the call for help, so those 10 records have no true date. Held: 4 of 4 factually; 10 of 15 records mislabel the date. 2 of the 5 "new" records are undated.
- Buyer: none found; 47 topic repos and about 26 listed projects mean the pile is tiny. Odds: 100 users in 30 days 15%; 10,000 in six months 1%. The LMGTFY analogy launched on a Digg front page, not a cold start.

## B. AI plan ledger: dropped, confirmed existing
aiplanfinder.com/changelog opened: live, free with attribution, 7 entries to 2026-07-29, 6 vendors. One fetch used.

## Lesson
Proof-first worked: opening three named competitors in one pass killed C in minutes, and counting records showed A and D are thin piles (a handful of events a quarter) built on one unsourced page or a free GitHub topic. Next round, pick angles where (1) the collector must record something no one is archiving now, so the history cannot be rebuilt, (2) the first records need a primary source URL, not a secondary list, and (3) the competitor search must open the full vendor lists of the free trackers before the inventor claims an uncovered slice. Reject any idea whose growth needs a household-name incident.
