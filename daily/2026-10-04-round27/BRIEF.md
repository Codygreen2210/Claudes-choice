# Round 27 brief (Oct 4, 2026). Bar set by Cody: 2 in 6 for $1,000 a month, and it can be scaled aggressively.

Read first: `daily/LESSONS.md`, `daily/DISCUSSED.md`, `daily/PLAYBOOK.md`. Do NOT read `daily/IDEA-JOURNAL.md`.

One person builds it alone on a laptop (Next.js, TypeScript, Supabase, Vercel, AI APIs), with no audience and no ad money. 50 ideas died against a $1M-a-year bar. The bar is now much lower and different in kind.

## The bar
An idea PASSES if both hold:
- **A.** The odds are 2 in 6 or better that it earns $1,000 a month within six months of a working version. $1,000 a month is 20 customers at $49, 67 at $15, 100 at $10, or about 250,000 ad-paid plays at $4 per thousand.
- **B.** There is a named way to scale it hard once it works: the same thing repeated (more listings, more niches, more states, more languages, more platforms) or a channel that grows with use. Say what 10 times looks like and what stops it.

## What your report must contain (each with a link you opened)
1. **The idea** in one sentence, and the price.
2. **The base rate.** At least THREE named solo makers earning $1,000 a month or more from the same kind of thing through the same channel, each dated, each from a page you opened (a public revenue page, a verified-revenue listing, a sale listing with revenue, the maker's own dated post, a marketplace's published payout). Also the failures if a source gives them: what share earn nothing. Odds must come from this, not from hope.
3. **The channel.** Exactly where the first 20 to 100 customers come from with no audience: a marketplace that brings its own buyers, a store with search, a directory of buyers to message. Say what a new, unknown seller really gets there, from a source.
4. **What already exists** on that exact shelf, with prices and any visible numbers (installs, users, reviews). Existing rivals are NOT a kill at this bar if the shelf is big enough for a newcomer to take a small share; say what share $1,000 a month needs.
5. **Costs per customer** (AI calls, marketplace fee) against the price.
6. **The scale path** (part B).
7. **Odds**, from the base rate: working version in two weeks / $1,000 a month within six months / $10,000 a month within eighteen months / shut out by the platform or a rival within a year.

## Rules
Customer does one click at most (a store install counts as that click; nothing after it). No planners or calendars; no gambling; nothing from tank car or railcar work; no licensed advice and no held money; nothing in `daily/DISCUSSED.md`. If your channel needs an approval that can refuse you (store review), say how long it takes and how often it refuses; that is reported, not an automatic kill, but an invite-only programme is a kill. Reddit and Stack Exchange are blocked: do not try them. Do not use any Ubersuggest tool. Never use the words "ship" or "shipping". Do not build anything, do not spawn agents, do not commit. If a search fails because of a usage limit, stop and report.

## Files (round folder `daily/2026-10-04-round27/`, X is your letter; write with Bash heredocs if another tool refuses)
- `log-X.jsonl`: one line per search or page opened: {"n":1,"did":"search|open|dropped","q":"query or url","found":"one plain sentence","thought":"one plain sentence"}
- `data-X.jsonl`: at least 8 records, each with a `url` you opened: at least three {"kind":"earner","who":..,"what":..,"per_month":..,"date":..}, at least three {"kind":"rival","name":..,"price":..,"numbers":..}, at least one {"kind":"channel_fact",..}. Never invent a record.
- `report-X.md`: under 450 words, the seven items in order.

Budget: 18 web searches or fetches. Return 120 words or less: the idea and price, the base rate you found (how many earners, how much), the channel, your odds for $1,000 a month, the scale path in one line, the biggest hole.
