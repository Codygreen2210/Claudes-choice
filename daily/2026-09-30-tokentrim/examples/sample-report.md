# TokenTrim report

6000 calls over 7 day(s), costing $86.31 (about $370/month at this pace).

## Where the money leaks

| Fix | Saves | Share of bill | Effort |
|---|---|---|---|
| Turn on prompt caching for repeated openings | $170/mo | 46% | One setting or one line per call |
| Cache exact repeat questions | $133/mo | 36% | Small cache in front of the API |
| Try a cheaper model on short answers | up to $0.71/mo | 0% | Test quality first |

## Repeated openings (best first)

- gpt-4o: 3611 calls share ~8768 tokens ("system:You are the help assistant for Brightside Plumbing Supply. Product catalo…") — saves $170/mo

## Exact repeats

1686 calls asked something already asked (167 distinct questions).

## Cheaper-model candidates

- 1813 short claude-sonnet calls → try claude-haiku: up to $0.71/mo

Savings are estimates from your own logs and the prices in prices.mjs. Cheaper-model savings only hold if quality holds, so test first. Overlapping fixes don't fully add up.
