# Report C: AI model and API retirement table (cross-vendor)

1. What it is: one page listing every dated retirement of an AI model or API across vendors, with replacement, hand-checked against the vendor page.
2. Already exists: YES, in part. hidekazu-konishi.com calendar (free, 4 platforms, updated 2026-09-25); vorplabs.com/models/deprecations; Product Hunt "The Model Graveyard"; endoflife.date now lists Claude and OpenAI models. Not covered by the calendar I opened: Mistral, xAI, Cohere, DeepSeek, Azure OpenAI. vorplabs and Model Graveyard were NOT opened, so they may cover those.
3. Users: developers with pinned model names. Posting places: Hacker News, r/LocalLLaMA.
4. Proof number: 100 visitors in 30 days; cheapest test is the page plus one post.
5. Odds: two-week version 5/6 / 100 free users in 30 days 3/6 / 10,000 in six months under 1/6 / someone bigger builds it in six months 4/6 (endoflife.date already adds models).

Other candidates dropped: free-tier cut history (agentdeals.dev, 433 dated changes, 1,576 tools); open-source license changes (Wikipedia list, WZ-IT chronicle, TechCrunch timeline); device update promise versus delivered (endoflife.date covers phones; no clean delivered-record source found).

Searches for existing version: 16 of 16 used; wordings in log-C.jsonl. Anthropic and OpenAI pages redirected and were not opened.
First-user answer: yes, a lookup of a model name gives its date at once.
The data: one record = vendor, model, announce date, retire date, replacement, source URL. 10,000 would need years; today the world makes about 8 to 15 per month across the 4 covered vendors (40+ upcoming rows on one calendar); Cohere gave 12 rows in 16 months (about 0.75 a month, 5 distinct announcement days). Buyer: no paying buyer found.
Grows by itself: no; it needs a news hook or a named incident.
Campaign: no.

## Proof counts (data-C.jsonl, 20 records)
- 8 from the calendar, all in it (by construction, 8 of 8 covered).
- 4 Gemini from Google's own page: unchecked against the calendar (it lists Gemini; I read only 15 of its 40+ rows).
- 8 Cohere rows from Cohere's page: 0 of 8 in the calendar (it does not cover Cohere); other lists unopened.
- Mistral: 12 deprecated models found but with no dates, left out.
- Honest coverage: for covered vendors an existing free list holds roughly everything; the uncovered vendors are a thin 1 to 3 records a month.
Verdict: weakened to existing; the owned layer would only be the small set of uncovered vendors.
