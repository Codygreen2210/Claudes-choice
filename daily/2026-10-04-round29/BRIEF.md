# Round 29 brief (Oct 4, 2026). Mobile game trends, then ideas.

Read first: `daily/LESSONS.md`, `daily/DISCUSSED.md`. Do NOT read `daily/IDEA-JOURNAL.md`.

**Why this round exists.** The last pick, Lane Luck (pick a checkout lane, watch five lanes race, get a card about your luck), was built today. Cody's verdict: "there's literally no reason to play that." He is right: it was chosen for being new and easy to post, not for being fun. It had no skill to get better at, no tension while watching, nothing to come back for. Do not repeat that. This round starts from what people on phones are actually playing in 2026 and why.

One person builds it alone in about two weeks with web tech (a game that runs in a phone browser, can be installed to the home screen, and could later be wrapped for the app stores) and AI coding help. No audience, no ad money to start (maybe $5 a day later).

## Your job has two halves
**Half 1: the trend, from sources you open.** What is being played on phones in 2025 and 2026 in your slice, with numbers (downloads, players, revenue, chart positions, retention figures), named games, and dates. Say what the players actually DO minute to minute in those games and why they keep doing it.

**Half 2: up to TWO game ideas that come out of the trend.** For each:
1. **The game in one sentence,** and what your thumb does (tap, drag, swipe, hold, draw).
2. **The first 30 seconds:** exactly what happens, and the moment the player first thinks "one more go".
3. **The reason to play.** Name it plainly: what gets better with skill, what is tense or satisfying each second, what the player is trying to beat. If the honest answer is "nothing much", drop the idea.
4. **The reason to come back tomorrow,** and next week.
5. **Which trending games it borrows from** (named, with their numbers) and what is different. A clone with a new skin is not an idea; a proven loop with one real twist is.
6. **Can one person build it in two weeks?** What is hard (art, levels, physics, balance, sound). Level-heavy games need hundreds of hand-made levels: say how levels get made.
7. **How a stranger finds it** with no audience, and your honest guess at players in the first 30 days (low / likely / high).

## Rules
No gambling, no real-money prizes, no loot boxes; nothing aimed at children; no copying a named game's characters, art, name or levels; no planners or calendars; nothing from tank car or railcar work; nothing in `daily/DISCUSSED.md` (SHIFT word ladder, Our Crossword, Fewer Words, Hours Guess, Lane Luck, howmanybananas are used). Known from earlier rounds: a daily word puzzle from an unknown maker does not grow by itself; browser game portals pay about 1.20 euros per 1,000 plays; Poki hand-picks, CrazyGames takes anyone. Reddit and Stack Exchange are blocked: do not try them. Do not use any Ubersuggest tool. Never use the words "ship" or "shipping". Do not build anything, do not spawn agents, do not commit. If a search fails because of a usage limit, stop at once and report what you have.

## Files (round folder `daily/2026-10-04-round29/`, X is your letter; write with Bash heredocs if another tool refuses)
- `log-X.jsonl`: one line per search or page opened: {"n":1,"did":"search|open|dropped","q":"query or url","found":"one plain sentence","thought":"one plain sentence"}
- `data-X.jsonl`: at least 6 records, each with a `url` you opened: {"kind":"trend","game":..,"maker":..,"date":..,"number":..,"what_players_do":..}. Never invent a record.
- `report-X.md`: under 500 words: the trend in five lines with links, then the idea or two ideas, items 1 to 7 each.

Budget: 16 web searches or fetches. Return 150 words or less: the trend in two lines with its strongest number, then each idea in one line with its reason to play and reason to come back.
