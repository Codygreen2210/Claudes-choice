# TokenTrim

Find where your AI API bill leaks, from your own call logs, in about a second.

If your app calls OpenAI or Claude, you're probably paying full price to send the same long system prompt thousands of times, paying again for questions you already answered, and using a big model for one-word answers. TokenTrim reads a log of your calls and puts a dollar figure on each of those, per month, with the fix.

It runs on your own computer, uses no AI, and never uploads your prompts.

Built Sept 30, 2026, as a daily build. It's a product: it runs on its own, with nobody's time per customer.

## Run it

Node 18+, no install.

```
node tokentrim.mjs calls.jsonl --days 7
```

`calls.jsonl` is one JSON object per line, one per API call: `{model, messages or prompt, output, usage}`. That's the shape most logging tools and the OpenAI/Anthropic request bodies already use. If `usage` token counts are there, they're used; if not, tokens are estimated (4 characters ≈ 1 token).

## What it checks

1. **Repeated openings.** Calls that start with the same long text (system prompt, docs, tool list) of 1,024+ tokens. Prompt caching bills those at the cached rate. The saving is priced per model.
2. **Exact repeats.** The same model asked the same thing again. A small response cache pays for each once.
3. **Cheaper-model candidates.** Expensive models giving short answers (60 tokens or less). Flagged with an upper-bound saving; only real if quality holds, so test first.

Models it can't price are listed, not guessed. Prices live in `prices.mjs`; check them against the provider's page.

## A real run

`examples/make-sample.mjs` builds a simulated week (6,000 calls) for a typical AI support app. Result in `examples/sample-report.md`: a $370/month bill with about $170/month in caching savings on one system prompt. It's simulated data, not a customer's.

## Tests

```
node --test --test-reporter=dot "test/*.test.mjs"
```

MIT license.
