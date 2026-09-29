# VibeGuard

A self-check for the security holes AI-built apps ship with. You point it at **your own** app's URL and it tells you, in plain English, what a stranger could already see or take — and gives you a fix you can paste straight back into Lovable, Base44, Cursor or Claude.

Built Sept 29, 2026, as a daily build. Product, not a service: it runs on its own, no human in the loop per customer.

## Why

AI can build a working app in an afternoon. The part it quietly skips is security. The most common leaks in these apps are boringly consistent:

- a secret API key (Stripe, OpenAI) left sitting in the code the browser downloads
- a Supabase database with Row Level Security turned off, so anyone can read everyone's data
- source code shipped to production, missing security headers

VibeGuard checks exactly these, because they're the ones that actually bite, and they're checkable from the outside without touching your code.

## What it checks

1. **Exposed secret keys** in your shipped HTML and JavaScript — and it knows the difference between a *publishable* key (fine) and a *secret* key (not fine), so it doesn't cry wolf.
2. **Open Supabase tables.** If your app hands the browser a Supabase anon key (normal), VibeGuard asks Supabase which tables that key can read. Any table without Row Level Security shows up, with a row count — the single most common way these apps leak user data.
3. **Missing security headers** (Content-Security-Policy, HSTS, and more).
4. **Public source maps** that hand out your original code.

## What it will not do

It only reads, the way a normal visitor's browser does: `GET` the page, the public scripts, the headers, and — using the anon key your app already exposes — a count of readable rows. It **never writes or deletes**, never downloads your data (counts only), never guesses passwords or hidden URLs, and never touches a site that isn't yours to check. Scan your own app.

## Run it

Node 18+ (uses built-in `fetch`), no install needed for the scan itself.

```
node cli.mjs https://your-app.com
node cli.mjs https://your-app.com --md report.md      # also write a shareable report
node cli.mjs https://your-app.com --no-supabase       # skip the database read check
```

It prints a plain-English report and, in the markdown file, a **paste-back fix prompt** — one block you drop into your AI builder to fix everything found. It exits non-zero when anything critical or high turns up, so you can wire it into CI.

### From your phone

GitHub → **Actions** → **VibeGuard scan** → Run workflow, type your app's URL. The report lands in the run summary.

## Files

- `scan.mjs` — the checks (fetch pages + scripts, secrets, Supabase RLS, headers, source maps).
- `patterns.mjs` — secret patterns and the anon-vs-secret key logic.
- `report.mjs` — plain-English report + paste-back fix prompt.
- `cli.mjs` — command line.
- `test/` — offline tests: a fake vulnerable app and a clean one.

## Tests

```
node --test "test/*.test.mjs"
```

MIT license.
