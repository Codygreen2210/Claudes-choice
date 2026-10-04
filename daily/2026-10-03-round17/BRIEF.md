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
