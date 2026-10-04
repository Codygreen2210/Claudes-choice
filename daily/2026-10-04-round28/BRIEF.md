# Round 28 brief (Oct 4, 2026). Cody's bar: USERS ONLY.

Read first: `daily/LESSONS.md`, `daily/DISCUSSED.md`. Do NOT read `daily/IDEA-JOURNAL.md`.

One person builds it alone on a laptop in about two weeks (Next.js, TypeScript, Supabase, Vercel, AI APIs). No audience, no ad money, no search ranking in month one. **Money does not matter this round. The only question: which idea would get the most people using it in its first 30 days, why, and how many.**

A "user" is a person who actually does the thing once (plays, pastes, gets a result), not a page view.

## What your report must contain (each with a link you opened)
1. **The idea** in one sentence a non-engineer follows, and what the first user gets in the first ten seconds.
2. **Why people would come:** the exact route from zero. Name the place the first people see it, why they would click, and why each user brings another (a result worth showing, a challenge link, a thing a group needs together). If nothing makes one user bring the next, say so.
3. **The comparison cases.** At least FOUR named, dated cases (2024 to 2026 preferred) of a solo or tiny-team thing of the same kind that started from no audience, with a real number each (visitors, users, plays, points, installs) from a page you opened. Include at least one that flopped, with its number. Your estimate must come from these, not from hope.
4. **What already exists** that is the same thing, and how many people use it. Rivals are not a kill this round if yours has a clear reason to be shown around; an identical free thing that flopped IS evidence against you.
5. **The estimate: users in the first 30 days as three numbers: low (things go badly) / likely / high (it catches),** and the odds of each. Then the odds of passing 1,000 users and 10,000 users in 30 days.
6. **Running cost** at the likely and high numbers (AI calls, hosting). An idea that costs more than about $50 at the likely number: say so.
7. **What is left after day 30:** do they come back, or is it a one-day spike?

## Rules
One click, paste, upload or link, with no install, no account and no permission prompt before the first result. No planners or calendars; no gambling or real-money prizes; nothing from tank car or railcar work; no voice, faces, health, children, private messages or bank logins; nothing that names a real person or company as having done wrong without a dated source; nothing in `daily/DISCUSSED.md` (howmanybananas, SHIFT word ladder, Our Crossword, Fewer Words, Hours Guess, AI Footprint Card, Heard Wrong, Will It Run, AI Speedtest and many more are used). Known from earlier rounds: a daily puzzle from an unknown maker does not grow by itself; Hacker News gives 1 to 4 points to dry topics and hundreds to a named household brand or a delightful toy; Hugging Face Spaces by strangers top out near 100 to 150 likes; a launch post can get 9 points and still be picked up months later. Reddit and Stack Exchange are blocked: do not try them. Do not use any Ubersuggest tool. Never use the words "ship" or "shipping". Do not build anything, do not spawn agents, do not commit. If a search fails because of a usage limit, stop and report.

## Files (round folder `daily/2026-10-04-round28/`, X is your letter; write with Bash heredocs if another tool refuses)
- `log-X.jsonl`: one line per search or page opened: {"n":1,"did":"search|open|dropped","q":"query or url","found":"one plain sentence","thought":"one plain sentence"}
- `data-X.jsonl`: at least 6 records, each with a `url` you opened: at least four {"kind":"case","what":..,"maker":..,"date":..,"number":..,"where_it_spread":..} (one a flop), and one {"kind":"rival",..} per same thing found. Never invent a record.
- `report-X.md`: under 450 words, the seven items in order.

Budget: 18 web searches or fetches. Return 120 words or less: the idea, the route in one line, your three numbers for 30 days with odds of 1,000 and 10,000, the strongest comparison case, the biggest hole.
