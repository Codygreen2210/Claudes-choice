# How an idea round runs (version 2, Oct 3 2026, after the round 16 synthesis)

Five agents unless Cody says otherwise: four inventors or repairers, then one checker. Sonnet, high effort.

1. **Main session** reads `daily/LESSONS.md`, `daily/DISCUSSED.md`, `notes/STATE.md` and Cody's brief. Not the whole idea journal.
2. **One shared brief file** per round (`daily/<date>-roundN/BRIEF.md`), copied from the last round and extended with every new kill reason. Each agent reads it.
3. **Inventors**, run together, each on a different angle. Up to 18 searches. Each must search for its own idea in three wordings before settling, and say "already exists" plainly if it does. Each logs every search to `log-X.jsonl` in the round folder (these feed a session video if an idea stands).
4. **Reports go to a file.** Each agent writes its full scorecard to `report-X.md` in the round folder and returns 120 words or less: idea in one line, own verdict, odds, biggest hole. The main session reads a report file only when it needs it.
5. **Checker**, run after, gets every idea the inventors did not kill themselves. About 9 searches per idea. Verdicts: stands, weakened (with a one-line fix), killed. It reports whether a paying data buyer exists but does not kill on that alone.
6. **Weakened ideas:** one repair at most. Before a repair, prefer a proof step that produces real data (seed entries, a count, a test file) over more opinion. Two weakened verdicts and the idea is retired.
7. **Report to Cody:** survivor or "none stood", the checker's verdict, the cheapest test. Offer to run the test if it is cheap.
8. **Journal it:** a short section in `daily/IDEA-JOURNAL.md`, a line in `daily/DISCUSSED.md`, `notes/STATE.md`. A line in `daily/LESSONS.md` only if something new was learned.
9. **Every 5 rounds** (next after round 21): stop and synthesize before the next round. Finish the last round's data; write a synthesis section at the top of the idea journal (count, how ideas died, what moved the odds, closest five); rewrite `daily/LESSONS.md` back down to one page; run `python3 studio/usage/journal.py` and put the usage figures and the tuner's result in the synthesis; change this file if the synthesis says the method should change.
10. **Limits:** a chat caps at 200 web searches, about two rounds. When the cap or a usage limit hits, save state and continue in a fresh chat from `notes/STATE.md`.

Do not use any Ubersuggest tool. Never the words "ship" or "shipping".
