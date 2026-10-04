# Report D: "Maintainer Wanted, Nominate Someone" (proof round 18)

Verdict first: ALREADY EXISTS in free form. Weak on spread. Not recommended.

1. What it is: paste a GitHub or npm package name, get a verdict (maintained, abandoned, seeking a maintainer) from public data, plus a one-click "nominate @person to take this over" message you send to that named person; each nomination is a public record.
2. Does it exist: seeking-maintainers.net (live, 27 projects, no dates; opened), flxwu/maintainerswanted.com, byalex33/maintain.help, pickhardt/maintainers-wanted, open-source-chest/take-it-over, GitHub topic looking-for-maintainer (47 repos; opened), sparkYJO1/npm-rot (scanner for packages many depend on and nobody maintains). Different in substance only: the named-person nomination and a verdict lookup.
3. Who uses it: maintainers handing off and developers whose dependency stalled; they post on GitHub issues today (example: github.com/github/Scientist.net/issues/114).
4. Proof number: nominations sent per 100 lookups; cheapest test is a static page of 50 seeded packages and a count of nomination clicks (about 3 days).
5. Odds: working version in two weeks 5/6 / 100 free users in 30 days 2/6 / 100 paying 0/6 / someone bigger builds it in six months 1/6 (GitHub could add a "seeking maintainer" flag; the May 2026 essay nesbitt.io/2026/05/02/a-github-for-maintainers.html argues for it, not opened beyond the search result).

Searches for an existing version (3 wordings): "free website list of open source projects looking for a new maintainer abandoned packages adopt"; "maintainer wanted board online find new owner for abandoned npm package or GitHub repo"; "seekingmaintainers.com OR maintainerwanted.com ... free online". All three found live or maintained free versions.

First-user answer: yes, from public repo data with zero crowd data (but the GitHub search API was blocked in this session, so I could not test that part).

The data: one record = package, owner, date of the call for help, outcome. 15 records in data-D.jsonl; 10 came from the topic page (all already in that free list; 2 also on seeking-maintainers.net), 5 were issue or discussion pages not on seeking-maintainers.net or the 20 shown topic repos (other lists unchecked). Only 2 of the 5 carry a date in the fetched text. New records a month: unmeasured (the search API was blocked); the topic holds 47 repos in total and the live list 27, so the pile is thin. No paying buyer found. 10,000 records would not be rare: nobody pays for a list GitHub topics already give away.

How it grows by itself: a nomination message goes to one named person, so each use can bring one new visitor. No evidence it does for strangers.

Proof 2, cold-start spread: none found. Closest is LMGTFY (link sent to the person you want to answer a question): made Nov 2008 by two people, posted to Reddit and Digg, got "crickets" first, then reached the top of Digg that day (codementor.io interview, opened); Lifehacker, Gizmodo and CNET covered it within a week (knowyourmeme, opened); later 5 to 6 million uniques a month. That is person-to-person built into use, but launched on a front-page spike and press, not a cold start, in a 2008 link-sharing era. A general search for no-audience solo spread returned only advice posts (not opened).

Campaign: no. Hook if any: "Tell the person who should take over this package."

Counts: searches/fetches used 16 of 16 (3 existence searches, 1 listing search, 1 failed GitHub API attempt group, 1 topic page, 5 issue pages, 1 existing-list page, 2 spread searches, 2 LMGTFY pages).
