# Report A: Louisiana residential contractor insurance proof (state law angle)

1. Buyers from a public list: FAIL. LSLBC search exists (https://arlspublic.lslbc.louisiana.gov/Public/Search) but shows rows only after a form submit my fetch could not do. Only 2 real entries seen, via Apify samples (https://apify.com/scrapebench/louisiana-contractor-license-lookup). Roster is 50,000+ licences.
2. Fresh dated change: PASS. Aug 1, 2026: $500k liability proof naming LSLBC as holder, 6 months, no exclusions; lapse means suspension. https://lslbc.gov/wp-content/uploads/LSLBC_Memorandum_Statutory_Changes_July_13_2026_REVISED.pdf and https://lslbc.gov/wp-content/uploads/Memorandum-6-25-2026.pdf
3. Gap open: FAIL on generic checking (ImageToTable, COI Rocket, myCOI, 1099Policy, more: bottom taken). No Louisiana-specific checker seen.
4. One page: PASS in form (upload certificate, see tick list), but brokers send the proof to the board.
5. Price: FAIL. Cheapest tool $19 a month; contractors do this once a year. $1M at $49 a month is about 1,700 customers, 3.4% of 50,000 licences (the residential share is unknown).
6. Not a licensed act: PASS. Reads a certificate against the board's list; no insurance advice.
7. Stop rule: 20 contractors, pass if 3 reply asking; fail otherwise.

Odds: two weeks 80% / 100 paying in 90 days 3% / $1M in three years under 1% / closed in six months 20%.
