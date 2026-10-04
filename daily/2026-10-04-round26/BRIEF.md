# Round 26 brief (Oct 4, 2026). Parameters set by Claude at Cody's request. Compact: this replaces the long brief.

Read first: `daily/PLAYBOOK.md`, `daily/LESSONS.md`, `daily/DISCUSSED.md`, `daily/SCORECARD.md`. Do NOT read `daily/IDEA-JOURNAL.md`.

You are a top MIT graduate looking for the next million-dollar startup that ONE person can build alone on a laptop (Next.js, TypeScript, Supabase, Vercel, AI APIs). 46 ideas have died. They died three ways: no way to reach buyers, the thing already existed, or the bottom of the market was already full of cheap newcomers. These parameters are built against those three.

## The seven parameters (all must hold; each needs a link you opened)
1. **Buyers first, from a public list.** A group of businesses or professionals found in a public directory with contact details (a state licence board search, an association member list, a marketplace seller list, a government registry in open form). Record TEN real entries from it. No directory, no idea.
2. **A fresh dated change that hits that group.** A rule, form, deadline, platform policy or technical requirement announced in the last 120 days (after June 6, 2026) or taking effect between now and July 2027. Confirm it from the PRIMARY source (the agency's or platform's own page). Old, well-covered changes do not count: timing is the one edge a solo builder has.
3. **The gap is still open.** Search four wordings for tools that already handle this change. Two or fewer cheap or free tools, and the platform or agency does not give the job away itself. Three or more: say "bottom taken" and drop it.
4. **One chore, one page, checkable.** The buyer does it on one click, paste, upload or link: no install, no account before the first result, no logins to other systems. The buyer can see the result is right without trusting you.
5. **Price of $49 a month or more, or $99 or more per use,** with an opened price for what they pay today for the nearest thing (software, a freelancer, a consultant's hour). State customers needed for $1M a year and what share of the counted group that is. Over 10% of the group: say so plainly.
6. **Not a licensed act, holds no money.** No legal advice, licensed financial advice, or filing on someone's behalf. Name the line.
7. **A stop rule for the cheapest test.** The test is a plain message to 20 entries from the directory. Write the pass mark before it runs (for example: 3 of 20 reply asking for it, or 1 pays).

## Hard rules
No planners or calendars; no gambling; nothing from tank car or railcar work; nothing waiting on a gatekeeper's approval; nothing in `daily/DISCUSSED.md` (accessibility audits, AI governance compliance, EU Data Act page, certified payroll forms, licence and continuing-education trackers, legal text generators and many more are used). Reddit and Stack Exchange are blocked: do not try them. Do not use any Ubersuggest tool. Never use the words "ship" or "shipping". Do not build anything, do not spawn agents, do not commit. If a search fails because of a usage limit, stop and report.

## Files (round folder `daily/2026-10-04-round26/`, X is your letter; write with Bash heredocs if another tool refuses)
- `log-X.jsonl`: one line per search or page opened: {"n":1,"did":"search|open|dropped","q":"query or url","found":"one plain sentence","thought":"one plain sentence"}
- `data-X.jsonl`: at least 14 records, each with a `url` you opened: ten {"kind":"buyer","name":..,"where_listed":..}, at least one {"kind":"change","date":..,"what":..}, at least two {"kind":"price_today",..}, and one {"kind":"existing_tool",..} per tool found. Never invent a record; a name you did not see on a page is left out. Report honest counts.
- `report-X.md`: under 450 words: the seven parameters in order, pass or fail each with its link; then odds (working version in two weeks / 100 paying customers in 90 days / $1M a year within three years / gap closed by someone else in six months).

Budget: 18 web searches or fetches. Return 120 words or less: the group, the change and its date, the idea in one line, which parameters failed, your odds, record counts by kind.
