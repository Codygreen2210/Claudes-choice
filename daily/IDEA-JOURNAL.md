# Idea journal

Every idea the studio's scouts looked at, and why it was liked or killed. Newest round first.

**The bar (set by Cody, Oct 3, 2026):** build only when an idea has at least a 3 in 6 chance of 100 paying customers within 30 days of launch, starting with no audience and no ad money. If nothing clears it, ideas are introduced here and not built.

Odds are the scout's own estimate of reaching 100 paying customers in 30 days. Founder numbers quoted from the web are self-reported unless noted.

---

## Synthesis after round 16 (Oct 3, 2026, 10pm). Next one due after round 21.

**Count, corrected.** Rounds 8 to 16 put 25 new ideas through the checker or an inventor's own existence check, plus 1 returned unchecked. None got "stands". (Earlier notes said 30 and 33; that was a miscount.)

**How they died (25 ideas):**
- Already exists free: 9 (Will It Run, AI Speedtest, AI Footprint Card, Who Gets My Data, contractor bids, deduction checker, package votes, Since Cutoff, and Env Forge's closed bounty).
- No way to spread without an audience: the remaining hole in every idea that was new (Hours Guess, Breaking-Change Table, Router Pulse, HF Tape, Pulled, Undo.fyi).
- Cold start or thin data: Neighbor Bill, Heard Wrong, Swap Notes, StackDex.
- Terms or law in the way: Run Autopsy (model output cannot train rivals), Router Pulse (vendor terms ban copying), Heard Wrong (voice lawsuits), Telegram and Reddit platform terms.

**What moved the odds.** The checker's own odds for 100 free users in 30 days rose as the method changed: about 1 in 6 for user-created-data ideas (rounds 9 to 12), 2 to 3 in 6 for pages that collect public data themselves (rounds 13 to 14), and 40% for a press-cited public tracker (Pulled, round 16). The best 10,000-in-six-months figure is 10%, also Pulled. No idea has beaten 10% on fast growth.

**The pattern that held every time.** Every verified solo win had a head start: Base44's founder had a prior funded company; Cal AI used paid creators; layoffs.fyi's founder was a funded founder who launched on a pandemic news hook; Killed by Google rode press coverage of one household name. Nothing verified started from zero audience and grew fast.

**Closest five, in order:** Pulled (features removed or paywalled after purchase; stands only if narrowed to one newsworthy category with a press hook) / Breaking-Change Table (real sources, nobody has published it, but Hacker News shrugs at the topic) / Hours Guess (cheap quiz, data is a curiosity) / Undo.fyi (accuracy risk) / HF Tape (weekend test only).

**Method changes that worked:** a separate checker that opens links; one shared brief listing every past kill reason; inventors forced to search for their own idea first (four inventors then marked their own idea "already exists"); a repair step for weakened ideas; logging each search to a file.
**Method changes that did not:** repairing an idea twice (HF Tape, Swap Notes, Router Pulse all got worse on the second look); building inside chat platforms.

**Usage (from `studio/usage/data/JOURNAL.md`).** Two sessions on record. Session 1 (rounds 1 to 7, ten scouts a round): 1.0M main-chat units, 11.4M subagent units. Session 2 (rounds 8 to 16, this chat): 2.8M main, 5.7M subagent, chat size 324k. Subagents are 82% of all units. A five-agent round costs roughly 500k subagent tokens and 70 to 90 web searches; a chat caps at 200 searches. The tuner (`evolve.py`) ran and changed nothing: it needs 5 sessions and has 2. Its standing proposal: have subagents write findings to a file and return one line (their reports are the costliest thing kept in the chat, 184k carried).

**Evolved for round 17 on (written into `daily/ROUND.md`):** agents write the full scorecard to a file and return 120 words; a twice-weakened idea is retired, not repaired again; before any repair, a real-world proof step (collect real seed data) replaces more opinion; synthesis like this one every 5 rounds.

## Oct 4, 2026: Round 29, mobile game trends then ideas (4 scouts + 1 checker, Sonnet). Pick: Cannon Collapse. Not built.

Why: Lane Luck (round 28's pick) was built and Cody said there was no reason to play it. Round 28 chose for novelty and ease of posting, not fun. This round started from what people play on phones and made every idea name its reason to play and reason to come back. Files in `daily/2026-10-04-round29/`.

**Trend (figures the checker confirmed):** phone game spend was flat to down in the first half of 2026 ($40B, down 2%; downloads 24B, down 12%) but puzzle revenue rose nearly 20%. The growth is in new puzzle loops: block puzzles $183M, sort puzzles $280M, screw puzzles $206M (Naavik). Color Block Jam took $42M on 21.8M installs in one quarter of 2025; All in Hole $22.3M. Block Blast had 368M downloads in 2025. Smash Fest! reached number 1 on US iPhone in June 2026 with 2.9M downloads and no paid ads, on limited shots, near-miss retries and good material sound. Match and puzzle games hold players best (about 33% next day, 14% at a week, 7% at a month). Games with nothing to progress in die; about 60% quit when a game gets hard too fast.
**Did not hold:** Block Blast's 17.3M daily players and 870M total (not found; 70M daily is the maker's own press release); Suika's 11M is mostly Nintendo Switch sales, not phones; "67 Speed" is only its maker's claim.

**Fun test (checker), eight ideas:**
- **Cannon Collapse** (drag and release to fire limited shots at a physics tower; fewer shots, more stars; shared daily tower) | real reason to play | pick. Likely 300 players in 30 days (low 50, high 3,000). Riskiest part: physics tuning.
- **Bolt Rush** (tap screws out of stacked plates into a 4-slot tray, scored 3-minute run) | real, weak reason to return | second. Likely 200. Riskiest: board generator and solver.
- **Slosh** (merge physics in a jar with a timed wave) | real, but merge clones are everywhere | third. Likely 200.
- **Hungry Hole** (drag a growing hole before a hunger meter drains) | real, but a famous game in a new skin.
- **Orbit Ghost** (tap to hop between rings against a ghost of the best run) | thin to real.
- **Grid Run** (block puzzle with the same daily pieces for all) | thin, a Block Blast clone.
- **Ghost Wire** (drag a ball along a shaking wire) | thin, one trick.
- **Half a Hand** (two phones, one steers each axis) | thin, needs two people online at once.

**Count:** 8 ideas. 62 checked since round 8 on this branch's record (54 + 8).
**The checker's one-day test for the pick:** a rough version with boxes for art, played by five people; if fewer than three ask for "again" after a near miss, drop it.

## Oct 4, 2026: Round 28, users only (4 inventors + 1 checker, Sonnet). Best: Lane Luck, likely about 300 users in 30 days.

Cody's bar: the idea that would get the most people using it in its first 30 days, the reason, and a number. Money ignored. First attempt at 10:30am stopped on the lookup limit; rerun at 1:25pm. Files in `daily/2026-10-04-round28/`. Numbers below are the checker's (low / likely / high not all restated; "likely" and odds of passing 1,000 users).

1. **Lane Luck** (five checkout lanes, tap one, watch it race the others, ten rounds, a card showing whether your "bad luck" was your choice) | likely 300, 13% to pass 1,000 (inventor: likely 700, 28%) | No playable version found in three searches. Route: a Show HN post plus posts elsewhere. Case for it: john.fun/elevators, a solo elevator simulator, got 1,680 points in Jul 2026 from a maker whose earlier posts got 2 points each. Case against: LightSpeed, a time-dilation toy, got 2 points in Sep 2026. Needs no file, login or wait; costs almost nothing to run. A spike, not a habit.
2. **Wrapped card for a history the big platforms skip** (drop in an AI-chat or viewing-history file, get a year card; live by Nov 25) | likely 200, 12% | Receiptify's "1M users in 24 hours from a tweet to about 20 followers" (Feb 2021) is supported only by its maker's own interview. OpenAI launched its own "Your Year with ChatGPT" on Dec 23, 2025; Kapwing has a Netflix one; about 20 self-hosted tools exist. A data export is requested and emailed, so it is not one click.
3. **Rival Card** (two Lichess usernames, a head-to-head card with a verdict, no login) | likely 120, 8% | GitRoast case (1,000+ visitors in 2 days) not re-opened; Lichess terms page did not load; "Roast My Chess Game" got 3 upvotes.
4. **Planet Zoo 2 habitat and compatibility checker** (game out Oct 13) | likely 60, 8% | No public game data confirmed; nothing makes one user bring the next.

**Count:** 4 ideas. 54 checked since round 8 on this branch's record (50 + 4). This round ranks, it does not pass or fail.

**What this round showed:** with money taken out, the honest 30-day number for the best cold-start idea is still about 300 people, with roughly a 1 in 8 chance of passing 1,000. The outcome is a lottery on one post landing: the same maker got 2 points twice and then 1,680. What raises the odds is several posts in several places and a challenge card that sends a friend back, not a better idea.

## Oct 4, 2026: Round 27, lower bar: 2 in 6 for $1,000 a month plus a scale path (4 inventors + 1 checker, Sonnet). Nothing passed.

Cody lowered the bar: pass at 2 in 6 for $1,000 a month (set here as within six months of a working version) and a real way to scale. Inventors had to bring a base rate: named solo makers earning $1,000 a month the same way. Existing rivals were not a kill. Files in `daily/2026-10-04-round27/`. All four came back as routes, not specific products; none named a gap.

- **Small one-job Shopify app** (two inventors) | fail | Earners held on spot-check: BeSure $2,000 a month after 3 months (2023), WideBundle $25,000 a month (2021), a Jira app $4,149 a month after 18 months (2020). Against that: of 22,546 Shopify apps, 51% have zero reviews and about 36% appear to earn anything (RevenueHunt, June 2026); a new app with no reviews gets 0 to 2 store installs a week; review took 5 to 10 weeks for some developers in April 2026. Checker odds: about 6% for $1,000 a month in six months, 1.5% for $10,000 a month in eighteen. apps.shopify.com was blocked, so no specific gap could be looked for. What would raise it most: hand-recruiting the first ten merchants and their reviews.
- **Pay-per-result listing on the Apify Store** | fail | Two named earners (over $2,000 a month; over $3,500 in one month). Apify pays $1.6M a month across 4,500 developers, about $355 each on average, across 80,341 tools; one maker's 98 listings drew 2,500 users, about 25 each. Crowded sources (SEC filings 10+, FDA 9+). Checker odds: about 7% / 1%.
- **Browser game on an ad-share portal** (CrazyGames) | fail | No dated maker found earning $1,000 a month this way. 451,327 plays paid 557 euros (2018); about 1.20 euros per 1,000 plays, so $1,000 a month needs about 800,000 plays a month. Poki hand-picks (227 games finalised in 2025). Inventor odds: under 1 in 6.
- **App stores inside other business software** (Atlassian, Wix and others) | fail | No specific add-on could be named; listing pages did not load.

**Count:** 0 new specific ideas (four routes judged). Still 50 ideas checked since round 8 on this branch's record. Nothing has passed either bar.

**What this round showed:** even at $1,000 a month, the measured odds for an unknown solo seller on a store that "brings the buyers" are about 6 to 8%, not 33%. The stores do not bring buyers to a listing with no reviews. The one lever every source points to is the same as the playbook's: win the first ten customers by hand.

## Oct 4, 2026: Round 26, Claude's own parameters (4 inventors + 1 checker, Sonnet). None stood.

Cody said: pick a strong set of parameters and run it. Seven parameters (`daily/2026-10-04-round26/BRIEF.md`): buyers from a public directory first; a fresh dated change confirmed from the primary source; two or fewer tools at the bottom; one chore on one page with a checkable result; $49 a month or more; no licensed act and no held money; a stop rule written before any test.

- **Louisiana contractor insurance certificate check** (upload a certificate, get a tick-list against the licensing board's Aug 1, 2026 rule: $500,000 liability cover for residential, mold and home-improvement licensees, lapse means suspension) | killed | The rule is real, but the board's own memo says proof must be submitted by the agent, broker or insurer, and the board receives and checks it, so the contractor has no chore to pay for. 6,627 licensees, not 50,000; $1M a year at $49 a month would need about 26% of them. Generic certificate checkers cost $3 to $10 per vendor a year. Checker odds: 1% for 100 paying in 90 days / under 1% for $1M a year.
- **W-2 overtime worksheet** (upload a payroll register, get the per-employee figure for the new box 12 code TT; IRS Fact Sheet FS-2026-13, Aug 6, 2026) | killed | The change is real, but payroll software already computes it (Patriot confirmed; QuickBooks has a method; Clockspot has a free calculator) and it is a once-a-year chore.
- **Amazon AI-person image tagger** (tag required on images with AI-generated people, Jul 22, 2026, seen only on a blog) | dropped by inventor | Three tools already there, including Amalytix. Other platform changes checked were either old or handled by the platform itself.
- **Broadband label maker for small internet providers** (FCC rule published Aug 13, 2026) | dropped by inventor | The rule loosens duties, and Sonar and ETI give label makers away. Other federal rules checked removed paperwork or had no open list of who is affected.

**Count:** 4 ideas. 50 checked since round 8 on this branch's record (46 + 4), none stands.

**What this round showed:** fresh rule changes do exist and can be confirmed from primary sources, but each one checked was already absorbed by whoever sits next to the buyer: the insurance agent, the payroll software, the platform, an existing vendor giving the tool away. A new chore lands on the party that already serves the buyer, not on an open market. Directories were also harder than expected: licence searches sit behind forms the agents cannot submit, so only one inventor recorded ten names.

## Oct 4, 2026: Study step, then round 25 "overtake a leader" (3 study agents; 4 inventors + 1 checker, Sonnet). None stood.

Cody asked for business courses from the top schools to be studied first, then a search for markets that can be taken from the leader. Study notes: `daily/study/` (about 22 pages opened across MIT, Stanford and Y Combinator, Harvard, Wharton; several were second-hand summaries). One-page result: `daily/PLAYBOOK.md` (six gates). Round 25 used it: a paid leader was required, "already exists" was not a kill, and each report was the six gates. Files in `daily/2026-10-04-round25/`.

- **Dispute Reply** (paste a Stripe or PayPal chargeback, get the evidence reply for a flat $9; leader Chargeflow takes 25% of what it recovers) | weakened, nearly killed | Stripe's own Smart Disputes builds and submits the evidence with a fee only on a win; WinDispute.pro is about $9 a month, Chargemate is free for 3 cases a month, ChargePay is $19.99 to $99.99 flat; Chargeflow has no minimum, so nobody is left out. One open slice: PayPal-only sellers. Checker odds: 1 in 15 for 100 paying in 90 days / under 1 in 100 for $1M a year. Test if wanted: offer it to 10 PayPal sellers, count paid replies.
- **Late-parcel refund finder, flat fee** (leaders ShipScience and Refund Retriever take 25 to 50% of refunds) | killed | Refund Retriever has no minimum, so small senders are already served; FedEx guarantees only overnight and international priority; needs the customer's carrier login. 1 in 30 / under 1 in 200.
- **Cheaper tax-preparer software for small preparers** (against Lacerte, ProSeries) | dropped by inventor | No single leader (UltraTax 22.9%, Drake 16.3%, Lacerte 15.8%, AICPA 2025); Drake already sells at about a third of the price; a full return is not one click. Also dropped: property management, roof measurement, home inspection (three or more cheap newcomers each), appraisal software.
- **Phone-first homebrew recipe app** (against BeerSmith, whose iOS app was last updated Oct 2020) | dropped by inventor | Six newcomers already at the bottom (Brewfather about $29.99 a year, Brewtarget free, Brewer's Friend, BrewPal, Beer Tools Pro, BeerAlchemy); no sourced earnings; BeerSmith's desktop is active.

**Count:** 4 ideas. 46 checked since round 8 on this branch's record (42 + 4), none stands.

**What this round showed:** the playbook changed the question but not the answer. In every market looked at, the bottom was already taken: wherever a leader charged a lot, three to six cheap or free newcomers were already there, and often the platform itself (Stripe) gives the job away. No inventor could name ten real buyers (gate 4): 0 buyer records across all four proof files. That gate cannot be passed by web search; it needs someone who already knows people in a trade.

## Oct 4, 2026: Round 24, field widened to apps, games and finance (4 inventors + 1 checker, Sonnet). None stood.

Cody widened the brief at 9:40am: apps, games and the financial sector are allowed, not tech only. New rule in the brief: find dated asks before inventing. Files in `daily/2026-10-04-round24/`.

- **Plant ID page with a toxic-lookalike warning** (consumer app) | paying | weakened | iNaturalist already shows its top 10 candidate species free (no toxic flag); PlantNet is free too (not opened by the checker). About 33,000 subscribers needed at $30 a year, no reach route, no solo-maker earnings found, and a wrong answer on a foraged plant is a documented harm (Public Citizen, OECD). Checker odds: 1 in 6 for 100 free users / 1 in 20 for 100 paying in 90 days / under 2% for $1M a year.
- **Fewer Words** (daily game: write a clue, an AI guesses the target, fewest words wins, result link challenges a friend) | ad money | killed | Language1 is the same game live on Product Hunt with 0 upvotes; Taboo AI and anoun exist too. No 2025 or 2026 case found of an unknown maker's daily game growing. Earnings spread, opened: Actorle about $4,000 a month (Oct 2022) then $3,000 (Oct 2023); Plus15 $18 all-time; Wordle sold for "low seven figures". Checker's own arithmetic (not sourced): most ad income per play would go to AI calls. 2 in 6 / n/a / under 1%.
- **Adviser staff-trade review sheet** (small SEC-registered advisers upload staff brokerage statements, get a restricted-list review for Rule 204A-1) | paying | dropped by inventor: exists | Comply (from $3,000 a year), Orion (from $8,500), SmartRIA, Simple Trade Monitor. 16,544 SEC-registered advisers at end of 2025, so $1M a year at $250 a month needs 333 firms (2%). Zero dated asks. A loan-estimate checker for mortgage brokers was dropped too: several exist.
- **401(k) fee disclosure explained in plain words** (paste or upload, no login, no advice) | paying | dropped by inventor: exists | Walnut (walnutinvest.com) does it free, and general chatbots do the same. Zero dated asks found.

**Count:** 4 ideas. 42 checked since round 8 on this branch's record (38 + 4), none stands.

**What this round showed:** widening the field did not change the result. The demand-first rule mostly failed for a plain reason: Reddit and Stack Exchange were blocked to the agents and Hacker News has few ordinary-people asks, so three of four inventors found zero or one dated ask. The one finance idea with checkable arithmetic (333 adviser firms at $250 a month) sits beside four paid tools.

## Oct 4, 2026: Rounds 22 and 23, MIT-graduate brief, either bar (4 inventors + 1 checker each, Sonnet). None stood.

Cody's brief: a top MIT graduate trying to start the next million-dollar tech startup. Either bar allowed (paying customers, or free users whose data pays). Proof files required. Numbered 22 on Cody's word; rounds 19 to 21 are not in the repo, so their ideas are unknown here. Files in `daily/2026-10-04-round22/` and `round23/`.

**Round 22**
- **Data Act Switch Page** (EU Data Act switching clause and exit page for small SaaS) | paying | weakened, close to killed | The duty is real (switching rules since 12 Sep 2025, charges banned 12 Jan 2027, no small-company exemption), but free guides and a fixed-fee law-firm addendum cover it, generators sell at $14 to $20 a month, zero dated asks. Checker odds: 2 in 6 for 100 free users / 3% for 100 paying in 90 days / under 1% for $1M a year. Cheapest test: a $49 one-pager sent by hand to 20 founders.
- **Vendor Trust Link** (paste a domain, get subprocessor list and DPA behind one link) | paying | killed | Free-forever trust centres exist (Cyberbase, SecurityPal); a domain scan cannot see back-end vendors. 2 in 6 / 2% / under 1%.
- **WordPress plugin history lookup** | free-with-data | dropped by inventor: exists | Plugin Pulse (plugins.wpmayor.com) tracks 74,666 plugins daily back to 2015. 11 of 11 proof records already there.
- **Postman team-plan replacement** (share an API collection by link) | paying | dropped by inventor: exists | Hoppscotch, Bruno ($6), Apidog (free for 4).

**Round 23** (higher-price angles, because $15 a month needs about 5,600 customers for $1M a year)
- **AWS bill savings from an uploaded cost export** | paying, high ticket | dropped by inventor: exists | Usage.ai's calculator does it free with no sign-up; a $25 Fiverr scan undercuts the $600 Upwork audit.
- **Mercado Libre listing writer in Spanish** | paying, other-language market | dropped by inventor: exists | A free no-signup generator and three paid suites exist; the Brazilian tax-code classifier exists too.
- **EPREL phone lookup** (maker-declared update years, battery cycles, repair class from the EU registry) | free-with-data | killed | EPREL's own site is a free search; iFixit and Right to Repair Europe bulk-read 2,334 records in September 2026; bulk access without an approved key is unproven; only 3 records collected, all Apple; no buyer. 1 in 6 / under 1 in 50 / under 1 in 200.
- **Apify Store listing** (a route, not an idea: no missing listing was found) | not worth another round | Checker verified: Apify pays about $1.6M a month across 4,500 publishing developers; the best named independent seller stated over $2,000 a month (Oct 2024). No review before listing, but Apify can remove any listing.

**Count:** 7 ideas and 1 route in these two rounds. 38 ideas checked since round 8 on this branch's record (31 + 4 + 3), none stands.

**What these two rounds showed:** switching to the paying bar did not help. No inventor in either round found three dated asks from real people, so demand was unproven every time. Every paying idea landed on a shelf priced at $6 to $25 a month with free versions beside it.

## Oct 4, 2026: Round 18, proof-first (4 proof agents, 1 checker). None stood.

Every agent handed back a file of real sourced records (`daily/2026-10-04-round18/data-*.jsonl`, 72 records in all) as well as a report. 82 lookups used.

- **Paywalled or removed features list** (Pulled, narrowed to paywalls and removals) | weakened, now retired for good | 13 records collected; 10 were already on GNU's "Proprietary Subscriptions" page (17 entries, no source links) and the Consumer Action Taskforce wiki covers some. About 1 to 3 notable events a quarter. Checker spot-check: 4 of 5 held; one date unsupported. Odds 35% for 100 users in 30 days, 4% for 10,000 in six months. No buyer.
- **AI plan limit and price change ledger** (ChatGPT, Claude, Gemini, Copilot) | dropped by its inventor: exists | aiplanfinder.com/changelog is live and free (checker confirmed); a second tracker with a GitHub CSV exists. 24 records collected, 14 already listed. Real rate: 6 to 8 changes a month.
- **AI model retirement table across vendors** | killed | vorplabs and aimodelgraveyard.com cover even the "uncovered" vendors (Cohere, Mistral, xAI, DeepSeek); endoflife.date has Claude and OpenAI. 7 of 7 spot-checked records true and all already listed. Odds 15% / under 1%.
- **Maintainer Wanted** (paste a package, get maintained-or-abandoned, nominate a named person) | killed | seeking-maintainers.net and a GitHub topic already list them; 10 of 15 "dates" were only last-push dates. No true cold-start example of person-to-person spread found (LMGTFY rode a Digg front page). Odds 15% / 1%.

**What the proof step showed:** in all four cases the collected records themselves exposed the existing list (10 of 13, 14 of 24, 20 of 20, 10 of 15 already held elsewhere). Household-name hooks point straight at ground that is already covered.

## Oct 3, 2026: Round 17, first round the version 2 way (2 proof agents, 1 repair, 1 inventor, 1 checker)

Reports are in `daily/2026-10-03-round17/report-*.md`; 16 real seed events in `seed.jsonl`.

- **Pulled**, narrowed to connected hardware | weakened, close to killed (second weakened verdict, so retired under the version 2 rule) | the proof agent verified 16 real events in 20 lookups, but 12 were cloud shut-offs, and PIRG's Electronic Waste Graveyard already lists 100+ of those, dated, updated July 2026 (6 of the 16 seed events were in its table). Only paywalled and removed features are open, and those run about one big-name event a month: a reference page, not a data asset. Checker odds: 100 visitors in 30 days about 60%, 10,000 in six months about 8%. No paying buyer.
- **Spread evidence (proof agent C):** six tracker cases opened, two true cold starts. Killed by Google's own launch post got 9 points; strangers' reposts later got 102 and 62, with press about six months on. endoflife.date's launch post got 248 points. BundlePhobia's four launch posts got 1 to 4. The subject "features removed after purchase" only gets attention through one named brand incident (a Motorola router story, 238 points), never as a category.
- **Keynote promises versus delivery** (dated record of what big tech announced and when it arrived) | weak by its own inventor | only a Tesla slice exists, but Siri-delay stories get 1 to 12 points. AI compute-deal and data-centre trackers already exist free (AI Compute Deal Ledger, Epoch AI).

## Oct 3, 2026: Round 16, press-cited tracker and free dataset angles (4 + 1, Sonnet)

- **Pulled** (public, sourced, dated list of features companies removed or paywalled after purchase) | weakened, closest so far | no structured tracker exists (PIRG's graveyard covers dead devices only; Consumer Rights Wiki is an unstructured crowd wiki). Spread evidence is weak: neither layoffs.fyi nor Killed by Google was a cold start. Fix: one tight newsworthy category and a press hook at launch. Checker odds: 100 users in 30 days 40%, 10,000 in six months 10%.
- **Undo.fyi** (companies that said AI replaced jobs, and what happened next) | weakened | no tracker exists, but calling a named company's move a "reversal" from a reopened job post is an accuracy and defamation risk; few rows have a knowable outcome.
- **Since Cutoff** (monthly question set from library release notes, to show which AI models are out of date) | killed | GitChameleon, VersiCode and CodeUpdateArena exist; models with docs tools make it moot.
- **Breaking-Change Table** (third look) | weakened | raw spec diffs overcount (136 raw removals, 17 real in one vendor's case); Hacker News posts on the topic get 1 to 4 points.

## Oct 3, 2026: Rounds 11 to 15, five agents a round (4 inventors or repairers + 1 checker, Sonnet)

Cody's order: five agents, keep going until the checker says "stands". Brief: tech sector, free, money from data, fast self-growth. Stopped after round 15 because the session hit its cap of 200 web searches. **Nothing stood.** Briefs and search logs: `daily/2026-10-03-round11/` to `round15/`. From round 13 the mechanism was changed (my call): the page collects public data itself, BuiltWith style, instead of waiting for users to create it.

- R11 **Will It Run** (browser test of which AI models your device runs) | killed | inventivehq.com/tools/developer/llm-gpu-benchmark does it.
- R11 **Package worked/broke votes** | dropped by its inventor | Renovate Merge Confidence; no cold-start answer.
- R11-12 **Hours Guess** (guess how long real GitHub fixes took, share a calibration card) | weakened | no such game exists, but answer-key licence unclear and the data is a curiosity. Could live as a cheap quiz, not a data business.
- R11-12 **Swap Notes** (AI model migration brief plus "what broke" reports) | weakened | vendor guides and coding assistants cover the brief; the inventor's retirement counts did not check out; nobody pastes a stranger's link into company code review.
- R12 **Still Installs?** (Android sideload verification check) | weakened | rests on a Google API with a 1,000-a-day cap; audience is sideloaders in four non-English countries.
- R12 **AI Footprint Card** (badge for how much of a repo AI wrote) | exists | AI Maxing.
- R13 **StackDex** (which repos wire up which MCP servers) | partly exists, thin | GitHub code search limits make a census impossible.
- R13-15 **HF Tape** (Hugging Face download history per model with rivals) | weakened, close to dead | history is already a free dataset (cfahlgren1/hub-stats); stranger-made Spaces top out near 100 to 150 likes; no buyer.
- R13 **Hub Graveyard** (deleted or relicensed model tracker) | weakened | a feature of the same snapshot; paid Apify monitors exist.
- R13-14 **Breaking-Change Table** (league table of which public APIs break callers most, from vendors' own spec repos with oasdiff) | weakened | no public ranking exists and sources are real (Stripe, GitHub, Cloudflare, OpenAI, Twilio, Adyen, DigitalOcean, Plaid), but the past is rebuildable by anyone and repeat visits are weak. A good one-off study.
- R14 **Who Gets My Data** (which AI companies are on a tool's subprocessor list) | killed | conductatlas.com archives these free for 352+ platforms; Wayback holds the past.
- R14-15 **Router Pulse** (is my router model still getting updates) | weakened, leaning dead | no cross-brand tracker exists, but TP-Link's and Asus's terms ban bots and copying; spread untested.
- R15 platform angle (unfinished, search cap): Telegram's bot terms ban collecting data to build datasets; Reddit's developer platform needs app review and bars selling Reddit data; Discord is open but its crowd is gamers. "Settle It" (group tool comparison) returned unchecked.

## Oct 3, 2026: Round 10, free-with-data inside the tech sector (2 inventors + 1 checker, Sonnet)

Brief from Cody: same as round 9 but tech sector only. Inventors were told the round 9 lessons (must work for the first user; one record must be worth something; no installs; nothing sensitive). Result: **neither cleared the bar.** Search logs: `daily/2026-10-03-round10/log-*.jsonl`. No video made.

- **Run Autopsy** (paste an AI coding session log, see where the agent looped or wasted tokens, donate the cleaned log with a worked/didn't-work label) | weakened | the analysis half exists free (agentfdr, claude-replay, claude-code-transcripts, agentlore); Anthropic's terms bar using Claude output to train competing models, so logs full of it are hard to sell to rival labs; finding the log in a hidden folder is not one click; secret stripping cannot be trusted; two of the inventor's links did not say what was claimed. No paying buyer found. Checker odds: 100 users in 30 days 1 in 6.
- **AI Speedtest** (one click times your connection to ChatGPT, Claude, Gemini and others) | killed | myaispeed.com already does it in the browser for 18+ providers with share buttons and anonymous data collection; browsers cannot read connect or first-byte timings across sites, so it mostly measures distance to the nearest network edge, which is already mapped. No paying buyer found.

## Oct 3, 2026: Round 9, free users whose data makes the money (2 inventors + 1 checker, Sonnet)

Brief from Cody: free product, growth built in, money from the data. He ruled the checker does not kill for lacking a paying data buyer today. Result: **neither cleared the bar.** Search logs: `daily/2026-10-03-round9/log-*.jsonl`. No session video made (condition was an idea standing). Cost about 560k subagent units, including two runs cut short by the web search limit.

- **Neighbor Bill** (type your internet bill and ZIP, see what neighbors pay; add yours to see) | weakened | Consumer Reports already ran it once with 22,000 bills, using a trusted brand and an email list; first user in most of about 41,000 ZIPs gets an empty answer; fake entries with no sign-up; no buyer for paid-price data found (buyers exist for advertised prices only). Checker odds: 100 users in 30 days about 40%, 10,000 in six months about 5%.
- **Heard Wrong** (read a sentence aloud, see what three speech AIs typed, share the miss card) | weakened, close to killed | voice is biometric: nine BIPA class actions filed May 2026 over voice used for AI training; microphone prompt is a second click; 3,000 ten-second clips is under 10 hours, worth a few hundred euros at Defined.ai's roughly 160 euros an hour, and Common Voice gives hours away free. The share-card format itself is open. Checker odds: 35% and 4%.

## Oct 3, 2026: Round 8, first round run the ROUND.md way (three passes, 2 inventors + 1 checker each, Sonnet)

Brief from Cody: an idea top MIT graduates would start and get funded at multi-million or billion scale, that one person could build alone at home on a laptop. Result: **nothing stood.** Six ideas, six knocked down. Cost: about 925k subagent units for all three passes (earlier rounds: 2.75M to 5.3M each).

- **Obey Test** (link that tests whether an AI obeys hidden instructions) | weakened | free versions exist (Agent Arena, Prefactor); server logs cannot see "obeyed"; nobody pays for a chart.
- **Deduction report checker** (small food brands, KeHE/UNFI/Walmart) | killed | Glimpse (a16z) already serves small brands with a free trial; one report cannot prove a line wrong without PO and delivery papers; disputes go through portals.
- **Balance Check** (vendor statement matching with a reply link) | weakened | Dext does the matching for small business; reply link reads as phishing; needs two uploads.
- **Tested version sets for coding agents** | weakened | depscope MCP has the same tool; agents pay about $5k to $11k a month in total across x402 (TRM Labs); an MCP server is an install.
- **Contractor bid comparison** | killed by its own inventor | ReadMyBid, GreatBuildz BidCompare, EstimateHawk.
- **Env Forge** (fill Prime Intellect environment bounties) | killed | checker opened the bounty sheet: program closed, no claims accepted.

**Finding that held under the checker:** every verified 2024 to 2026 solo or two-person software win (Base44 to Wix for $80M, Cal AI, OpenClaw) had a track record, an audience, creator videos or open-source fame. No verified case of a no-audience first-timer was found.

## Oct 3, 2026: Round 7, make a Pro plan last like Max (5 teams, Sonnet)

Brief: cut usage per finished piece of work toward 5x, going past Anthropic's own tips, no repeats. **All savings below are estimates. Nobody has measured them on a real account, and Anthropic does not publish how plan limits weigh cached text or each model.**

| Method | What it is | Est. saving, whole account | Odds it holds | Build time |
|---|---|---|---|---|
| **Offload Ledger** | A script ranks which tool outputs cost most in your own logs (size x turns kept), then caps the top three: partial file reads, failures-only logs, diffs. | 1.3x to 1.8x | 4/6 for 1.3x | ~2 days |
| **Gearbox** | Plan on Opus in a small session, do the work on Sonnet at medium in a fresh one, never switch model mid-session (a switch re-reads everything), subagent only if it keeps 20k+ tokens out of a chat with 15+ turns left. | ~1.5x | 4/6 | ~2 days |
| **Lean Roster** | A small connector set per kind of job instead of everything on. Biggest in the chat app, where 10+ connectors may load 30k to 70k tokens every turn. | 1.2x in Claude Code, up to 2x to 3x in connector-heavy chat | 4/6 chat, 3/6 Code | ~1 day |
| **Ledger Reset** | Claude adds 3 lines to a notes file after each step, so a fresh chat can start any time for free. Reset after a break or when history gets long, by rule not feel. | 1.2x to 1.5x | 3/6 | ~1 day |
| **Read-Back Gate** | Before big work, a 60-word read-back: deliverable, done test, two assumptions, one thing it will not touch. If it still goes wrong, restart with the read-back, do not argue in the old chat. | 1.2x to 1.4x | 3/6 | ~1 day |

**All five teams' verdict:** stacked, about 2x to 3x. 5x is unlikely: the methods overlap (most cut the same re-read cost), and nobody found a measured share of usage that is pure waste.
**Open facts:** teams disagreed on how long cached text stays cheap on a plan (5 minutes vs 1 hour), and on model prices; neither was checked against Anthropic's pages.
**Liked:** Lean Roster (fits a many-connector phone user, free, testable today) and Offload Ledger (biggest single lever, measures before it cuts).
**Status:** introduced, not built, not measured. Waiting on Cody.

## Oct 3, 2026: Round 6, frontier startups for Claude only (5 teams, Sonnet)

Brief: round 4 rules, but each idea must make Claude specifically better, from the outside, with nothing repeated. **Nothing built or measured. Odds are the teams' own.**

| Idea | What it does | Demo number | Odds: demo in 2 wks / 100 users in 30 days / press / Anthropic builds it in 6 months |
|---|---|---|---|
| **Stencil** | After Claude does the same edit by hand 2 or 3 times, it writes a script, proves the script reproduces those edits exactly, then finishes the rest for zero tokens. | Tokens and time on a 60-file job, with and without | 4/6, 2/6, 2/6, 2/6 |
| **Bedrock** | Traces every line in Claude's memory back to words the person actually said; lines it cannot trace are set aside, not deleted. | Share of planted false memory lines caught | 5/6, 3/6 (free installs), 2/6, 2/6 |
| **Foreman** | An outside supervisor for long Claude Code runs: keeps a list of dead ends the agent cannot edit, puts it back after each compaction, blocks repeats. | Tokens wasted on repeated failures over 8 hours | 4/6, 2/6, 2/6, 3/6 |
| **Bylaw** | Turns written rules (like "never delete in a connected app") into hard blocks, tested first, with a count of how often each rule held. | Rule breaks per 100 tasks, with and without | 4/6, 2/6, 2/6, 2/6 |
| **Spec Pass** | Claude writes code that checks an image against a written spec and fixes failures; text and colours placed by code. | Pass rate on 100 exact-spec prompts vs raw image models | 4/6, 2/6, 2/6, 1/6 |

**Liked:** Stencil (clearest before/after number, goes at usage caps, the loudest complaint) and Bedrock (best odds, a failure Anthropic's own issue tracker documents).
**Liked less:** Foreman (most likely to be built by Anthropic), Spec Pass (dead if rival image models already pass; helps any model, not just Claude).
**Doubt on Bylaw:** the Bedrock team found rules-into-blocking-hooks already crowded (Claude Rule Enforcer, sentinel-ai); the Bylaw team said nobody does it. Needs a check before any build.
**Honest read:** these fix known weak spots. None would by itself put Claude far ahead of every other model; that takes changes inside the model, which an outside add-on cannot make.
**Status:** introduced, not built. Waiting on Cody.

## Oct 3, 2026: Round 5, breakthrough bets (5 researchers, Sonnet)

Brief: each agent acts as a top new researcher going after an unproven breakthrough that works on top of most AI models. No customer target. Every bet needs an experiment that could prove it wrong. **Nothing here has been run. These are conjectures, and the agents read mostly paper summaries, not full papers.**

| Bet | The claim | The proof experiment | Time and cost | Odds: can run / comes out right / as big as hoped |
|---|---|---|---|---|
| **Checker-Once Cascade** | An expensive model writes a checker once per kind of task; cheap models do the work; only rejected answers go back to the expensive model. | Cost per correct answer at least 8x lower, accuracy within 1 point, wrong answers let through 2% or less. | ~3 weeks, $500 to $2,000 | 5/6, 1.5/6, 2/6 |
| **Tiebreaker Court** | When models disagree, settle it with a written test that is actually run, not by vote or debate. | At least 3 points better than the best single model at equal cost on fresh coding problems. | ~3 weeks, $500 to $1,500 | 5/6, 2/6 (3/6 to beat voting), 1/6 |
| **Disguise Test** | Reword a question to strip its surface cues; if the answer changes, the model was guessing. | Predicts right vs wrong at 0.80 or better (1.0 is perfect, 0.5 is a coin flip) on six fields it was not tuned on. | 3 to 4 weeks, up to ~$1,500 | 5/6, 1/6, 2/6 |
| **Fork Test** | Have several models each write a simulator of the situation; where they disagree is where the model's picture of the world is wrong. | Flags bad plans at 0.80 or better and lifts plan success 15 points. | 3 to 4 weeks, $2,000 to $5,000 | 5/6, 2/6, 1/6 |
| **Ratchet** | A model's playbook only changes when the change wins a replay and holds up on a second model, so it learns from use without retraining and without drifting. | ~300 recurring tasks, 3 models: beat the ungated method by 10 points at task 100, and 60% of the gain carries to another model. | 3 to 4 weeks, $3,000 to $10,000 | 4/6, 2/6, 1/6 |

**Liked:** Checker-Once Cascade (cost is the thing every buyer already measures, and the test is cheap and clear) and Tiebreaker Court (cheapest test, best odds of a real result).
**Liked less:** Ratchet (biggest prize, most expensive test, longest odds), Fork Test (hard to pick fair tasks), Disguise Test (1 in 6 to come out right; rewording itself can change the question).
**Status:** introduced, not built, not tested. Waiting on Cody.

### Checker-Once Cascade: small pilot run Oct 3 (not the full proof)

36 tasks with exact answer keys (12 crew schedules, 12 invoices, 12 pick-a-set puzzles). Opus wrote one checker per kind from one example. Haiku answered everything; Opus answered everything as the baseline. Models were told not to run code.

| | Right out of 36 |
|---|---|
| Haiku alone | 29 |
| Opus alone | 34 |
| Cascade (Haiku, checker, Opus on rejects) | 34 |

- Wrong answers the checkers let through: 0 of 7.
- Haiku kept 24 of 36 tasks; 12 went up to Opus (11 of them invoices, where the checker turned away 5 correct answers because it would not accept anything it could not fully recompute).
- If Opus costs about 5x Haiku per task (assumed, not measured), that is roughly 2x cheaper overall, about 4x on the two kinds with a clean checker. The 8x target cannot be reached with these two models; it needs a much cheaper small model.
- Limits: tiny sample, one family of models, tasks I made up, cost not metered, and the invoice key rounds half-cents up, which the task wording did not say (may explain Opus's two misses).

## Oct 3, 2026: Round 4, frontier startups (5 teams, Sonnet)

Cody changed the rules for this round: each agent acts as a startup inventing new technology that makes today's AI models far better. The only rules kept: nothing repeated, and get to 100 customers as fast as possible. Aim for something the AI newsletters would lead with.

Odds are each team's own: a working demo in two weeks / 100 customers in 30 days of showing it (free users count) / real newsletter pickup. Nothing here has been built or measured.

| Idea | What it does | The demo | Closest existing things | Demo | 100 users | Press |
|---|---|---|---|---|---|---|
| **Stale Stamp** | Stops an AI coding agent from saying "done, tests pass" when it changed the code after the tests ran. It runs the checks itself, records exactly which files they read, and voids the result if any of those files change. | Replay real agent sessions and show what share of "done" claims were stale and how many it blocked. One developer measured 35% stale in 101 claims. | Tool receipts (record calls, not whether still true); ORP; the studio's own second-look and Misslog | 4 in 6 | 2 in 6 | 2 in 6 |
| **Gap** | Lists what an AI summary or rewrite left out of the original, each with a quote. Models are measurably bad at noticing what is missing (AbsenceBench, NeurIPS 2025). | 100 documents, 3 planted omissions each: how many does plain asking find, versus Gap. | A developer coverage metric; a French medical checker; contract clause tools | 4 in 6 | 2 in 6 | 2 in 6 |
| **Earshot** | Gives a text-only model ears for tone: a timeline of how each phrase was said (pace, pitch, pauses) next to the words, flagging when the words and the voice disagree. | A public scoreboard on VoxParadox, a test where words and tone conflict; today's best audio model scores 17.4%. | Hume (emotion score per clip); research cascades with no packaged tool | 4 in 6 | 2 in 6 | 2 in 6 |
| **Patchwork** | Finds the one broken part of an AI-made video (wrong hand, changed jacket), repairs only that region, and proves the rest of the frame was untouched. | 14 benchmark clips, before and after, with defects found, fixed and pixels changed outside the repair. | Checkers that only flag; region editors that need a person to draw the mask | 4 in 6 | 1 in 6 | 2 in 6 |
| **Receipts** | Sits between a coding agent and the model, replaces repeat file reads with short "unchanged" stubs, and replays your own past sessions to show the savings before you turn it on. | Ten real tasks with and without it: tokens, dollars, tests passing. | Several token-saving tools already; the gap is the replay proof | 4 in 6 | 2 in 6 | 1 in 6 |

Ideas the teams passed on: turning repeated agent runs into fixed scripts (academic work exists, small savings); shared model cache across teams (needs control of the model servers); cross-user mistake store (Misslog covers it); a "stop and ask" gate (research project, no buyer); a scene file for exact visual edits (Remotion and others do it); a character-lock layer for video (the big labs' race); a pause-and-stress score for speech (close research exists); a fast voice that holds the floor while a slow model thinks (OpenAI and NVIDIA do it); a freshness checker for outdated facts (search tools cover it); a reader-stumble map (not new enough).

---

## Oct 3, 2026: Round 3, each scout brings its one best idea (10 scouts, Sonnet)

Cody asked for another run and said he would decide on a build himself. Each scout had to bring back its single best idea even if it fell short, with odds at 30 and 90 days.

**Result: 0 of 10 met the bar. Best odds: 1 in 6 at 30 days, 1.5 in 6 at 90 days.**

| Scout's best idea | Who pays today | What kills it | 30 days | 90 days |
|---|---|---|---|---|
| **Prop Rule Check**: drop in a trade export, pick a prop firm, see pass or fail on its loss and consistency rules | Traders spend about $4,270 each on evaluations; journals cost $19.99 a month | TradesViz covers 37+ firms with a free tier; five free calculators; no proven way to reach traders | 1 in 6 | 1.5 in 6 |
| **Year-End Packet**: upload a giving spreadsheet, get a statement for every donor | One statements-only add-on sells at $497 a year; church software $29 to $119 a month | MosesTab does it free from a CSV with no signup (one donor at a time); no channel to volunteer treasurers; January only | 1 in 6 | 1.5 in 6 |
| **Client Question Sheet**: bookkeeper sends clients one link to explain unclear transactions | Uncat, $9 per client a month, 263 reviews | Uncat is the default and plugs into QuickBooks; free forms; bookkeepers are wary of new tools with client data | 1 in 6 | 1.5 in 6 |
| Hearing packet builder (exhibit stickers, page numbers, index) | $5 to $20 per packet | Twelve tools already, some free | 1 in 6 | 1.5 in 6 |
| Print-size pack sold through Fiverr | $5 to $20 gigs | New Fiverr sellers get 0 to 20 orders in month one; it is a service, not a product | 1 in 6 | 1.5 in 6 |
| Thesis format pre-check | $200 Fiverr formatters; $3 a page at one university | Four upload-and-format tools plus a $5 checker; one-time need; no channel | 1 in 6 | 1 in 6 |
| Vendor W-9 request link | getW9 from $19 a year | Eight tools, one free; the 2026 threshold change shrinks the need; holds tax ID numbers | under 1 in 6 | 1 in 6 |
| Course video check before Udemy review | No one, as far as found | Udemy publishes no pass/fail numbers; free audio tools | under 1 in 6 | 1 in 6 |
| Windows 10 renew-or-replace sheet | No one pays for the sheet | Free calculators and ChatGPT | 1 in 6 | 1 in 6 |
| Google Play external-link fee ledger (reporting began Oct 1, 2026) | No one yet; no tool exists | Tiny pool of developers; the real report needs API keys; Google keeps moving the date | under 1 in 6 | 1 in 6 |

Also killed this round (0 to 1 in 6): Exchange EWS usage decoder (a free one is live), privilege log builder, redaction checker, spreadsheet to legal billing format, table of authorities, journal figure checker, poster resizer, reference list cleaner, prop spend ledger, profit cards from statements, reference check link, change order approval link, contractor pay application generator, supplier quote compare, subtitle gigs, audiobook loudness fixer, podcast feed validator, flashing checker, musician loudness check, auction receipts, volunteer hour certificates, HOA dues notices, French e-invoice maker (nine free ones), Teamer shutdown exporter, Amazon peak fee recalculator, AI memory transfer.

Checked after the round: MosesTab's free giving-statement tool takes a CSV with no signup and adds the acknowledgement wording, so Year-End Packet's only gap is doing every donor in one go.

---

## Oct 3, 2026: Round 2, channel first (10 scouts, Sonnet)

Round 1 showed the products were fine and the channel was the problem, so this round started from the channel: what can a brand-new seller with no following really get from it in 30 days?

**Result: 0 of 10 passed.**

| Channel | Verdict | What a new seller really gets in month one | Odds |
|---|---|---|---|
| Etsy digital, new shop | Killed | Typical 0 to 10 sales; best found about 20. One shop: 126 views, 8 orders. New shops are slow to show in search. | 1 in 6 |
| Teachers Pay Teachers | Killed | $29 to join. Cases: 0 sales, 14 sales, $0. Best case 235 sales took 3 months. TpT demotes AI-made stores. | 1 in 6 |
| Gumroad Discover | Killed | Discover shows nothing until a product has sales. Two sellers with 25+ products each made $0. | 0 in 6 |
| Lemon Squeezy marketplace | Killed | Needs approval plus prior sales. | 0 in 6 |
| Whop | Killed | One unverified case of 87 members in 60 days, for a paid community. Buyers there want communities and signals. | 1 in 6 |
| TikTok and Reels, new account | Killed | Median about 350 views a video. 100 buyers needs roughly 3 to 25 million views. Winners rode one or two viral videos. | 1 in 6 |
| Pinterest, new account | Killed | About 900 visits a month at best; buyers arrive 4 to 12 weeks after the click. | 1 in 6 |
| YouTube how-to search | Killed for 30 days | Videos take 250 days to a year to rank. Good slow channel (Tiiny Host, Atlist). | 1 in 6 |
| Hand-written replies in communities | Killed | Cleanest case: 6 paying customers for 15 hours of work. The "60 customers in 45 days" case from round 1 is contradicted by the same founder reporting 4 in 90 days. | 1 in 6 |
| Launch platforms (Product Hunt, Show HN, others) | Killed | Typical unknown launch: 100 to 500 visits, 0 to 5 paying. Front page of HN: 500 visitors, no sales. | 1 in 6 |
| Template marketplaces | Killed | Notion, Figma, Canva closed or months of review. Framer is open: 1 to 21 sales in the cases found. | 0 to 1 in 6 |
| AI assistant add-on stores | Killed | Instant ones can't charge; ones that charge have a review step or almost no buyers. Best case: 1 customer in a week. | 0 in 6 |

Products considered inside those channels, all killed at 0 or 1 in 6: free web tool sold as an Etsy link, budget spreadsheet packs, Canva template links, bulk worksheets for TpT, $5 one-tap consumer tool for TikTok, sticker and template packs, resume template packs, Notion and Canva packs, wedding printables, pin-making tool, niche Framer templates, paid MCP servers, skill packs, pay-per-call agent tools, small paid developer tools launched on Product Hunt.

---

## Oct 3, 2026: Round 1, sector first (10 scouts, Sonnet)

Sectors per Cody's direction: people actively searching for a fix, plus tech and finance.

**Result: 0 of 10 passed.**

### Developers and AI builders
- Play Store 12-tester helper | killed | It's a service (needs real people on real phones); five sellers plus free swap groups | 1 in 6
- App store screenshot maker | killed | Eight or more paid tools plus Figma and Canva | under 1 in 6
- Fix for AI-built sites not showing in search | killed | Three sellers already, and it needs DNS setup, so not one click | 1 in 6
- CLAUDE.md / AGENTS.md generator, rules packs | killed | Free generators and free rule libraries | under 1 in 6
- Supabase keep-alive pinger | killed | Free fix is everywhere; would need the customer's keys | under 1 in 6
- App privacy label and policy generators | killed | Established sellers; edges into legal advice | 1 in 6

### Small-business money chores
- Bank statement PDF to Excel | killed for 30 days | **Proven money** ($12.5K to $38K a month for the leader) but it took years of Google ranking; the leader's own ads and 1,000 cold emails failed | 1 in 6
- Bank CSV to QuickBooks formats | killed | Nine free tools | 0 in 6
- Stripe payouts to QuickBooks entries | killed | Already sold from $5 with a free preview | 1 in 6
- Amazon or Etsy settlements to accounting | killed | A2X plus four cheaper rivals | 1 in 6
- Venmo, Cash App, PayPal statements to CSV | killed | Five free converters | 0 in 6
- Payroll report to journal entry | killed | Gusto does it natively | 1 in 6

### Personal money paperwork
- Crypto or brokerage export to tax-software format | killed | Free tools and the exchanges' own reports | 0 in 6
- 1099-DA check against own records | killed | Sold by CoinLedger and CPA firms; needs whole wallet history | 1 in 6
- Visa bank-balance evidence checker | killed | Existing analyzers hold the searches; no channel | 1 in 6
- Gig driver income merger | killed | Platforms give drivers a summary already | 1 in 6
- eBay/Etsy 1099-K vs sales reconciler | killed | Sellers complain, but no one is paying for a fix and no channel | 1 in 6

### Online sellers
- **Whatnot true-profit page, no login** | killed, best lead in the sector | Real pain in sellers' own words ("takes hours every week"), spreadsheets for it sell on Etsy at $5 to $47, but Aftershows already does it at $19 a month and there's no open channel to Whatnot sellers | 1 in 6
- Shipping label cropper | killed | Six free sites | 0 in 6
- Shopify product CSV fixer | killed | Six existing tools | 0 in 6
- Packing slips from an orders file | killed | Free generators; platforms print them | 0 in 6
- Reseller profit per item | killed | Free calculators; Seller Ledger from $10 a month | 1 in 6
- Replacement for Shopify's Stocky (shut down Aug 2026) | killed | Eight alternatives already listed | 1 in 6

### Freelancers and creators
- Media kit generator | killed | Nine free ones | under 1 in 6
- Podcast sponsor report | killed | BuzzyPod bundles it at $10 a month | 1 in 6
- Rate cards, retainer reports, handoff pages | killed | Free templates and free tiers | 1 in 6
- Note: this group pays for platforms, not single documents.

### Job seekers
- **Unemployment work-search log, all states** | killed | About 35 states require written records and one Texas tool charges for it, but every state posts a free form and a new site can't rank in 30 days | 1 in 6
- Federal resume formatter | killed | Six builders plus the government's free one | 1 in 6
- Resume-to-application-field kit, portfolio packager, clearance prep sheet | killed | Free tools or tiny markets | 1 in 6

### File and data conversion
- WhatsApp chat to court-ready PDF | killed | Eight sites already | 1 in 6
- Fuel tax mileage report | killed | Free calculators; close to tax filing | 1 in 6
- Google Takeout photo fixer | killed | Won't run in a browser tab at that size | 1 in 6
- Bank file formats (BAI2, MT940) to Excel | killed | Free converters | 1 in 6
- Court e-filing PDF fixer | killed | Needs a server; buyer already has Adobe | 1 in 6
- A 2025 clone of the bank statement converter has 17,000 visitors a month and $1 of revenue: traffic alone doesn't convert on a new domain.

### Marketers and SEO
- Negative keyword finder, AI-traffic report, redirect map builder, keyword clustering, llms.txt generator, ad copy bulk editor | all killed | Several free tools each, plus ChatGPT | 0 to 1 in 6

### Landlords and property
- Airbnb payout file to per-property profit | killed | Three small tools with free tiers | 1 in 6
- Lender-ready financial statement | killed | One seller at $79; rare buyer; needs a paid bank link | 1 in 6
- Inspection report to repair request | killed | Sold at $29 a report; needs a paid AI model | 1 in 6
- Rent ledgers, condition reports, utility splits | killed | Free from the big landlord apps | 0 to 1 in 6

### Proof hunt: who actually got 100 paying customers fast?
- SuperX (650 customers at launch) | evidence | Founder built 40K followers first | n/a
- SoloPush (60+ customers in 19 days) | evidence | Sold to makers through Reddit and X posts | n/a
- RankInPublic | evidence | Audience first; under $300 a month for a long stretch | n/a
- $9 invoice tool, zero audience | evidence of failure | $0 by day 4 | n/a
- Reply helper for Reddit help threads | liked as a lead only | Aims at a channel that has worked, but no proof anyone pays and ChatGPT does it | 1.5 in 6

---

## What both rounds say

1. **No idea and no channel cleared the bar.** 30 scouts across three rounds, about 150 ideas and 12 channels, best odds 1.5 in 6.
2. **The products are not the problem.** People pay for many of these jobs. What fails every time is getting in front of about 7,000 to 8,000 likely buyers in 30 days from a standing start.
3. **Every fast winner found had one of three things:** an audience built first, ad money, or months of search ranking.
4. **Self-reported wins need a second source.** The best-looking case in round 1 fell apart when the same founder's other write-up was read.

## Earlier today (before the bar was set)

- Planner Press (built) | 1 in 6 for 10 customers by its scout | Cody ruled planners out afterwards: too much free.
- Our Crossword (built) | four competitors including one free.
- ProSal Ledger (built) | almost no search demand; reached through groups and email.
- Cook-off voting page, pinewood derby manager, scan-to-pay sign, funeral program, treasure hunt maker | not built | weak evidence, free alternatives.
