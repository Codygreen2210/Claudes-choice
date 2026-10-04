# Report C (inventor C, round 22)

**Bar chosen: FREE-WITH-DATA.**

1. **What it is:** a free page where anyone types a WordPress plugin name and sees its install, rating and closure history, with the history recorded daily from today because wordpress.org keeps only a current bucket.
2. **Does it already exist?** Yes. Plugin Pulse (https://plugins.wpmayor.com/) says it tracks 74,666 plugins daily with history back to 2015, from the public WordPress.org APIs; one plugin page showed 1,404 observations since 2015-04-22. Plugins Database (https://pluginsdb.com/tag/plugin-status) holds a thinner current snapshot with maintenance labels. Apify has similar change monitors for other marketplaces (Atlassian: three actors; job boards: nine; Azure prices: CostBench).
3. **Who pays or uses it:** plugin buyers and agencies. No paying buyer found, no link opened.
4. **The one number:** none worth testing, since the free list exists with years of head start.
5. **Odds:** working version in two weeks 5 in 6 / 100 free users in 30 days 1 in 6 / 100 paying customers in 90 days under 1 in 20 / $1M a year within three years under 1 in 100 / someone bigger builds it in six months: already built.

**Searches for an existing version:** "Atlassian Marketplace app install count history tracker" (three Apify monitors); "job posting history tracker Greenhouse Lever Ashby" (nine Apify actors); "EPREL smartphone energy label lookup" (nothing third party, but the portal is a script page I could not open); "Azure retail prices price history" (CostBench, cloudprice.net); "WordPress plugin active installs history" (Plugin Pulse, pluginsdb). The wordpress.org API and Atlassian API are robots-disallowed to my fetch tool; I did not test the rules for a normal program.
**First-user answer:** works on day one only because the history is imported from public APIs, which Plugin Pulse already does.
**The data:** one record is plugin, date, install bucket, rating, status. 10,000 plugin-days matter only if nobody else has them; Plugin Pulse does. No paying buyer found.
**How it grows by itself:** it does not; no evidence found.
**Campaign:** no.

**Proof:** 11 records in data-C.jsonl, all 11 already on an existing free list (Plugin Pulse or Plugins Database). Only the Plugin Pulse pages were opened with full text; the numbers come from the fetch tool's summary of each page. New records a month: not measurable, the daily history is already collected.

**Honest result:** sources checked and dropped: Atlassian Marketplace, ATS job boards, Azure price history, WordPress plugin history (all exist). EPREL phone update promises (EU energy label for phones, with years of updates and repair class) was the only gap not shown to exist, but I could not open the source, the buyer is unclear and consumer phone-update ground is crowded. Verdict: already exists. 3 searches or fetches left unused.
