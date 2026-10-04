# Inventor brief, rounds 11+ (read fully)

Work at high effort: think like a top MIT computer-science graduate picking a startup. Check your own claims. Keep your report short. If a search or fetch fails because of a usage limit, stop and say how many you completed.

First read: daily/LESSONS.md, daily/DISCUSSED.md, daily/SCORECARD.md. Do NOT read daily/IDEA-JOURNAL.md.

## The brief (from Cody, the owner)
TECH SECTOR only. A FREE product one ordinary person can build alone at home on a laptop (Next.js, TypeScript, Supabase, Vercel, AI APIs). The money comes from the DATA the free users create, not from charging them. Because it is free, the user base has to grow fast by itself (each use brings the next user), with no ad money and no audience. The prize should be large: the kind of data business investors fund.

## Change for round 13 (read this)
Eighteen ideas have died. The two things that kill most are "users must create the data" (cold start, nobody reports, small piles) and "it already exists". So this round uses a different, proven mechanism: THE PAGE COLLECTS THE DATA ITSELF from public sources, and users come for a free lookup. BuiltWith was built by one person in about two weeks this way and sells technology-usage data; SteamDB, Keepa and Have I Been Pwned are the same shape. The money still comes from the data and the product is still free, but the data does not wait for users. Users still matter: their lookups show demand and their corrections improve it. Your idea must say (a) exactly which public source is read and that reading it is allowed and practical for one laptop (rate limits, size, terms), (b) why the pile is hard for the next person to copy (history that cannot be collected afterwards is the best answer: start recording now what nobody is archiving), and (c) what the free lookup gives one person.

## What killed the last ten ideas (yours must survive all of these)
1. It already existed. Inventors said "nothing like it" and the checker found the same product live in minutes (myaispeed.com, Glimpse, Dext, depscope, agentfdr). BEFORE you settle, search for your exact product in at least three different wordings, including "free", "online", and the obvious product name plus .com. Log each. If it exists free for the same people, drop it.
2. Cold start: it must give a useful answer to the VERY FIRST user with zero crowd data.
3. Small piles of data are worth nothing. Say what one record is, and why 10,000 of them are worth something nobody can scrape in an afternoon.
4. Installs: an extension, CLI, npm package, MCP server or script tag is an install. It must be a web page that works on one click, paste, upload or link. Finding a file in a hidden folder is not one click. A browser permission prompt (microphone, camera, location) is a second click.
5. Sensitive data: no voice, faces, health, money accounts, children, private messages, private code or secrets.
6. Data you cannot sell: output of an AI model cannot be sold to train rival models under the maker's terms. Data a big company already has is worth little.
7. Technical claims that were false (a browser cannot read connection timings to other sites). Only claim what a browser page can really do.
8. Links that did not say what the inventor claimed. Open a page before citing it; say "not opened" otherwise.
9. No buyer today is NOT a kill (Cody's ruling), but say plainly whether one exists.

Round 11 added: Will It Run (browser test of which AI models your device runs) was killed, inventivehq.com/tools/developer/llm-gpu-benchmark already does it. A new site has no search ranking in month one, so growth cannot depend on people finding the page by search. Nobody writes a report for no reward: the user must get something back for every record they give.

Round 12 added: Android sideload verification checker, AI footprint badge for GitHub repos (AI Maxing exists), AI model migration notes, fix-time guessing game: all weakened or existing.

Round 13 added: before claiming "nobody keeps this history", search the Hugging Face Hub datasets, Apify store, Kaggle and GitHub for an existing daily snapshot (a free daily dataset, cfahlgren1/hub-stats, already holds Hugging Face download history; several Apify actors sell change monitors). If a free raw dataset exists, the gap is only the lookup page on top, and you must say what data YOU would own that the free dataset does not. A badge from an unknown site will not be displayed by big vendors. Round 13 ideas, all weakened: Hugging Face download history charts (HF Tape), Hub deleted-model tracker, API breaking-change grades, MCP/agent stack lookup for repos.

Round 14 added: "Who Gets My Data" (AI subprocessor lookup) was killed: conductatlas.com already archives subprocessor lists and terms for 352+ platforms free, and the Wayback Machine holds the past. Always check the Wayback Machine and conductatlas before claiming a page's history is unarchived. Router Pulse (router firmware update history by model) is weakened, not existing. The remaining wall for every idea is SPREAD: a believable way to reach people with no audience, no ad money and no search ranking. Your idea must name that way and give evidence it works for strangers.

Round 15 added: stranger-made Hugging Face Spaces top out near 100 to 150 likes; Telegram's bot terms ban building datasets from app users; Reddit's developer platform needs app review and bars selling Reddit data; TP-Link and Asus terms ban bots and copying support pages (check a source's terms before relying on it). If web search stops working because of a session cap, stop at once and report what you have.

Round 16 added: neither layoffs.fyi nor Killed by Google was a cold start (a funded founder with a news hook; press coverage of one household name). Hacker News gives 1 to 4 points to dry topics and hundreds to a named household brand. Calling a named company's action a "reversal" or similar from weak evidence is an accuracy and defamation risk: state only dated, sourced facts. Version-aware code benchmarks already exist (GitChameleon, VersiCode, CodeUpdateArena).

Already used, stay clear: AI layoff reversal tracker, post-cutoff library question sets, browser AI-model device test, package-version worked/broke votes, everything in DISCUSSED.md, plus AI hidden-instruction test, internet bill comparison, speech mishearing test, coding session log analysis, AI service speed test, website checkers, AI-traffic reports, multi-LLM comparison, AI cost trackers, pay surveys, mistake journals.

Hard rules: no planners or calendars; no gambling; nothing from tank car or railcar manufacturing; no file converters; nothing that waits on a gatekeeper; data sellable self-serve (public report, subscription, download) as well as to big buyers; plain consent line shown first; sourced numbers only. Do not use any Ubersuggest tool. Never use the words "ship" or "shipping". Do not build anything; the only file you may write is your log. Do not spawn agents.

## Record your session (required; it becomes a video)
Every search or page opened: append one line to your log file with Bash, e.g.
echo '{"n":1,"did":"search","q":"query or url","found":"one short plain sentence","thought":"one short plain sentence on what you decided next"}' >> LOGFILE
Also log dropped ideas: {"n":..,"did":"dropped","q":"idea name","found":"why it died"}.

## Budget
Up to 18 web searches/fetches. Spend at least 5 of them trying to find your own idea already existing.

## Where your report goes (new rule)
Write your full report to the report file named in your instructions (in the round folder). Then RETURN ONLY 120 words or less: the idea in one line, your own verdict, your odds, and the biggest hole. The log file and the report file (and any data file your instructions name) are the only files you may write.

## Full report format (goes in the file, under 400 words, plain language, nothing else)
ONE idea as a filled scorecard in the SCORECARD.md shape (lines 1 to 5; line 5 odds for: working version in two weeks / 100 free users in 30 days / 10,000 free users in 6 months / someone bigger builds it in six months). Then five lines: "Searches for an existing version" (the wordings you tried and what came up); "First-user answer"; "The data" (one record; why 10,000 matter; who buys data like it today with a link, or "no paying buyer found"); "How it grows by itself"; "Campaign" (yes/no and a one-sentence hook). If every candidate you found already exists, say so plainly and return your best one marked "already exists" rather than dressing it up.

## Round 17 added (read this)
"Pulled" (features removed or paywalled after purchase) was retired: PIRG's Electronic Waste Graveyard already lists 100+ cloud shut-off devices, dated. Check PIRG, Consumer Reports and iFixit before claiming a consumer-harm list is open. Keynote-promise trackers are weak (Siri-delay stories get 1 to 12 points). AI compute-deal and data-centre trackers exist free (AI Compute Deal Ledger, Epoch AI). Spread evidence: Killed by Google's own launch post got 9 points and was picked up by strangers months later; endoflife.date's launch got 248; a topic only gets attention through ONE named household brand incident, never as a category. Honest cold-start odds for a public tracker: about 60% for 100 visitors in 30 days, 8 to 10% for 10,000 in six months.

## Round 18 is PROOF-FIRST (overrides the budget and file rules above where they differ)
A scorecard alone is not accepted. You must hand back REAL COLLECTED DATA for your candidate: a file `data-X.jsonl` in the round folder (X is your letter), one JSON record per line, at least 12 records, each with: what it is, the date, the named company or product, a source URL you actually opened, and `"in_existing_list": "yes/no/unchecked"` saying whether an existing free list (name it) already holds that record. Never invent or guess a record; a record you could not open a source for is left out. State only dated, sourced facts about named companies.
Then count honestly in your report: how many records you found per lookup, how many were already in an existing free list, and how many new records a month the world produces. If the proof shows the pile is thin or already covered, say so plainly; that is a useful result, not a failure.
Budget: up to 16 web searches or page fetches in total. Files you may write: your log, your report, your data file. Under the brief: the page must work for the very first user in one click (no install, sign-up or permission prompt), and the data may be collected by the page from public sources or created by users.

## Round 18 added
All four proof files exposed an existing free list (GNU Proprietary Subscriptions page, aiplanfinder.com/changelog, vorplabs, aimodelgraveyard.com, seeking-maintainers.net, Consumer Action Taskforce wiki). Household-name hooks point at covered ground. "Last pushed" dates are not event dates. No true cold-start case of person-to-person spread was found.

## ROUND 22 ON (Oct 4; overrides anything above where they differ)
Cody's brief: you are a top MIT graduate trying to start the next million-dollar tech startup, alone, on a laptop (Next.js, TypeScript, Supabase, Vercel, AI APIs). 31 ideas have been checked since round 8 and none stood.

**Either bar is allowed. Say which one you chose on line 1 of your report:**
- PAYING: a believable path to $1M a year from people or companies who pay. Show the arithmetic (price x customers) with a sourced price from something they pay for today.
- FREE-WITH-DATA: free product, the money comes from the data, growth built in (rules above).

**The "page collects public data" and "proof-first round 18" sections above are options, not requirements.** Everything else above still holds: one click for the customer, no installs, no gatekeepers, cold start must work, search three wordings for your own idea first, name the spread route with evidence it works for strangers.

**Proof is still required, sized to the bar you chose.** Write it to `data-X.jsonl` in the round folder, one JSON record per line, every record with a `url` you actually opened:
- PAYING: at least 6 records. Each is either `{"kind":"price","who":..,"price":..,"url":..}` (something the buyer pays for today) or `{"kind":"ask","where":..,"date":..,"quote_gist":..,"url":..}` (a real person asking for this, dated 2025 or 2026, in a place a new account can reply). At least 3 of each kind.
- FREE-WITH-DATA: at least 10 real records of the data itself, each with `"in_existing_list":"yes/no/unchecked"` and the list named.
Never invent a record. Fewer real records than the minimum is an honest result: report the count.

**Scorecard line 5 for this round:** working version in two weeks / 100 free users in 30 days / 100 paying customers in 90 days / reaches $1M a year within three years / someone bigger builds it in six months. Odds as X in 6 or a percent.

**Budget:** up to 16 web searches or page fetches in total. Files you may write: your log, your report, your data file, all in the round folder named in your instructions. Return 120 words or less.

## Round 22 added (read this; the ROUND 22 ON rules above still apply in round 23)
Four more died. 35 checked since round 8, none stands.
- Data Act Switch Page (EU Data Act switching clause generator): weakened. Duty is real with no small-company exemption, but free guides and a fixed-fee law-firm addendum cover it, legal generators sell at $14 to $20 a month, and there were zero dated asks.
- Vendor Trust Link (subprocessor list and DPA behind a link): killed. Free-forever trust centres exist (Cyberbase, SecurityPal); a domain scan cannot see back-end vendors.
- WordPress plugin history: exists (Plugin Pulse, plugins.wpmayor.com, daily since 2015). Atlassian Marketplace, job-board and Azure price histories also exist.
- Postman team-plan replacement: exists (Hoppscotch, Bruno, Apidog). When a tool raises prices, free or $6 replacements fill the gap within months.
- Also covered: EU Cyber Resilience Act (free Eclipse toolkit), UK Companies House filing (TinyTax).
New kill reasons: (10) A price of $15 a month needs about 5,600 customers for $1M a year; nobody showed that many buyers exist. State the customer count needed at your price and a sourced count of buyers. (11) Legal and compliance text generators are a low-price, crowded shelf. (12) No inventor found 3 dated asks: if you cannot find real people asking in 2025 or 2026, say so and treat demand as unproven.

## Round 23 added
Three more died, 38 checked, none stands: AWS bill savings from an upload (Usage.ai does it free), Mercado Libre listing writer in Spanish (free generator exists), EPREL phone update-years lookup (the registry's own site is a free search; no buyer). Selling a listing on the Apify Store caps low: best named independent seller stated just over $2,000 a month. In two rounds NO inventor found three dated asks.

## ROUND 24 ON: Cody widened the field (Oct 4, 9:40am). This overrides anything above where they differ.
Same brief (top MIT graduate, next million-dollar startup, solo on a laptop, either bar) but no longer tech sector only. Now allowed:
- **Apps**: phone apps and web apps for ordinary people. An app-store install counts as the customer's one click, but nothing after it: no setup, account or choices before it works. Say how long store review takes and how often a first app is refused (it is a gatekeeper; report it, do not hide it).
- **Games**: allowed. Still no gambling, no real-money prizes, no loot boxes aimed at children.
- **Financial sector**: allowed. But the product may not hold or move money, ask for bank or brokerage logins, or give advice that needs a licence. Say which regulator's rules apply, from a source you open.
Still banned: planners and calendars, anything from tank car or railcar work, everything in DISCUSSED.md (note how much finance is already there: statement converters, budget tracker, pay surveys, betting, 1099-K, crypto export converters, prop firm rule checker).

**Demand first (new rule).** Before you invent anything, spend your first 5 lookups finding real, dated (2025 or 2026) asks or complaints from ordinary people in your area, in places a new account can reply. Invent only from what you found. If Reddit is blocked, use Hacker News, app store reviews, Google Play reviews, Steam reviews and discussions, itch.io, Stack Exchange, Indie Hackers, forum threads.
For games and consumer apps, "price" records may be sourced earnings of a named solo maker (dated, with a link you opened) and "ask" records may be dated reviews saying what is missing in the leading app or game.

## Round 24 added
Four more died, 42 checked, none stands: plant ID page with toxic-lookalike warning (weakened; free ID exists), Fewer Words AI clue game (killed; Language1 exists with 0 upvotes), adviser staff-trade review sheet (four paid tools exist), 401(k) fee explainer (Walnut is free). Reddit and Stack Exchange are blocked to you; do not spend lookups on them.

## ROUND 25 ON: OVERTAKE A LEADER (Cody, Oct 4, 9:54am). This overrides anything above where they differ.
Cody had course material from MIT, Stanford, Harvard and Wharton studied and asked for ideas where the market can be taken from whoever leads it. **Read `daily/PLAYBOOK.md` before anything else; it is one page.** Field stays wide: tech, apps, games, finance (round 24 limits still apply). PAYING bar only this round.

**The big change: "it already exists" is no longer a kill.** A paid leader is required: it proves demand. Your job is to find a leader that is stuck, and the group it leaves out.

**Your report is the six gates from the playbook, each with a link you opened:** (1) the leader, its price, a sign of its revenue; (2) the group it leaves out, with evidence; (3) what the leader loses by copying you; (4) ten named real buyers in that group and how each is reached; (5) the bottom-up sum to $1M a year; (6) what one customer is worth against the hours it takes to win one. Then scorecard line 5 odds (working version in two weeks / 100 paying customers in 90 days / $1M a year within three years / the leader or another newcomer closes the gap in six months), and one line: "Other newcomers already at the bottom" (name them with prices; three or more cheap newcomers means the bottom is already taken, say so plainly).

**Proof file `data-X.jsonl`:** at least 8 records with a `url` you opened: `{"kind":"leader_price",...}`, `{"kind":"left_out","date":..,"gist":..}` (a dated review or post from the ignored group), `{"kind":"buyer","name":..,"how_reached":..}` (toward the ten named buyers), `{"kind":"newcomer","name":..,"price":..}`. Never invent a record or a buyer; a name you did not see on a page is left out. Report honest counts.

The one-click rule for the customer still holds. Budget: 16 web searches or fetches. Return 120 words or less.
