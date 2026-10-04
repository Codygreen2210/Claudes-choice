# Report B: AI plan limits and price ledger (ALREADY EXISTS)

1. What it is: a dated public ledger of changes to ChatGPT, Claude, Gemini and Copilot plan limits, model access and prices.
2. Does it already exist? Yes, free, several times. aiplanfinder.com/changelog (7 dated entries, Jun 2025 to Jul 2026, 65 tracked facts); christopheralarcon.com/ai-plan-tracker (20 logged changes since Jul 2026, primary sources only, GitHub CSV at github.com/financiallywelloff-cmyk/ai-plan-pricing-history); costbench.com and getpulsesignal.com also keep price histories (seen in results, not opened).
3. Who uses it: people comparing plans. Where: Hacker News, Reddit, X (not tested).
4. Proof number: of 24 records collected, 14 already sit in the two free trackers (58%). The 10 that were not are real but are mostly Gemini/OpenAI/Claude release-note items the trackers skip, and 4 of the 24 trackers' lists were only partly visible (3 alarcon entries unreadable), so the true overlap is probably higher.
5. Odds: working version in two weeks 85% / 100 free users in 30 days 30% (lowered because trackers already hold the niche) / 10,000 free users in 6 months 3% / someone bigger builds it in six months 35% (costbench and others already do).

Searches for an existing version: three wordings (plan limit history timeline, pricing history tracker, GitHub dataset wayback), plus Product Hunt/Hugging Face wording. All found live trackers. Wayback CDX call was blocked by the tool, so Wayback depth is not counted. 13 of 16 budget used.

First-user answer: current limits and last changes per plan, available from the first visit.

The data: one record = date, product, plan, what changed (cap, model, price), source URL. 24 records in data-B.jsonl, every one from a page opened; fetch summaries are not verbatim, so quotes need a recheck. No paying buyer found.

New events per month (honest): from Jul to Sep 2026 about 20 dated plan events across the four brands, roughly 6 to 8 a month; the older months look near 1 to 2 a month only because the older lists are thin. Release notes carry few limit changes (Claude's notes contain mostly features), so most limit changes appear only on pricing pages, which a daily snapshot would catch.

How it grows by itself: no built-in loop. One household brand is a hook only when a named change lands (Claude limit increase Sep 22 is an example).

Campaign: yes, hook "what ChatGPT Plus gave you a year ago versus today", but trackers already own it.

Verdict: pile is real but already covered free, and thin per month. Drop, or only as a quiet feeder under another idea.
