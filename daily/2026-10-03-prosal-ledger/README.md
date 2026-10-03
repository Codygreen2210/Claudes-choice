# ProSal Ledger

Production pay statements for veterinary practices. The practice manager types in each doctor's monthly production and gets a statement that shows every line of the math, a year ledger with what was carried in and out, and a link the doctor can open to check it.

**Product.** People find it, use it and pay for it on their own. No calls, no custom work.

## Why this exists

Most associate vets are paid "ProSal": a guaranteed base plus a percentage of what they produce. 56% of associates were paid this way in 2024 ([AVMA](https://www.avma.org/blog/chart-month-look-compensation-trends)). Somebody at the practice has to work it out every month or quarter, per doctor, and the rules differ by contract:

- different percentages for services, lab, pharmacy, preventives and retail
- a shortfall that carries into the next period (negative accrual), or doesn't
- a carried shortfall that is wiped at the end of the contract year, or isn't
- base paid in full, or the classic setup of one fixed check a month with a year-end guarantee

Practice software mostly can't do this, so it's done in a spreadsheet. One consultant's published advice is to "export sales data, by associate, into an Excel spreadsheet, organize sales by product class, and then calculate the total production bonus" ([Bash Halow](https://www.bashhalow.com/determining-a-fair-salary-for-associates-and-pro-sal-explained/)). A contract-review firm says "most bonus disputes arise from vague math" ([Review Veterinary Contracts](https://reviewveterinarycontracts.com/resources/veterinary-associate-bonus-structures/)).

## What the customer does

1. Opens the link. It loads with example numbers already worked.
2. Taps "Start with my own", types the contract terms once, then each month's production.

That's it. No account, no install, no setup. Numbers stay in their browser.

## What's free and what's paid

| | Free | Practice license ($149 a year) |
|---|---|---|
| Doctors | 1 | All of them |
| Line-by-line statement and year ledger | Yes | Yes |
| Printable statement with sign-off lines | | Yes |
| Check link the doctor opens on their own phone | | Yes |
| Payroll lines to paste into a sheet | | Yes |

## Files

| File | What it does |
|---|---|
| `engine.js` | All the pay math. Whole cents, no dependencies, same code in browser and tests. |
| `app.js` | The screen. |
| `index.html` | Page and styles. |
| `config.js` | The one file to edit to start charging (Stripe link and price). |
| `lib/license.mjs` | Makes and checks license keys. |
| `api/claim.js` | After Stripe checkout, confirms payment with Stripe and hands back a key. |
| `api/check.js` | Tells the app whether a key is good. |
| `tools/dev-server.mjs` | Runs it locally. |
| `tools/build-demo.mjs` | Packs everything into one file for a phone preview (`demo/`). |
| `test/` | 43 unit tests and a 14-step run in a real browser. |

## Run it

```
node tools/dev-server.mjs        # then open http://localhost:4173
npm test                         # 43 unit tests, quiet output
node test/e2e.mjs                # real browser run (needs Playwright)
```

## How it was tested

- The engine is checked against worked examples other people published: Mark Opperman's two ([dvm360](https://www.dvm360.com/view/prosal-method-pay-doctors), [Today's Veterinary Business](https://todaysveterinarybusiness.com/pro-on-prosal/)), Owner Exchange's [negative accrual example](https://ownerexchange.com/veterinary-associate-compensation/), and Bash Halow's quarterly example.
- A test that a slightly wrong percentage gives a different answer, so the checks aren't loose.
- Twelve months of base pay always add up to the salary to the cent, for odd salaries too.
- A missing month stops the ledger, so a carried shortfall can't skip it.
- License keys: a forged end date, a wrong secret, an expired key and a made-up checkout id are all refused.
- Browser run at desktop and phone width: enters real numbers, checks the statement, reloads, tries paid features on the free plan, applies a key, copies payroll lines, opens the doctor's check link in a second browser, checks print and dark mode.

## To start charging

1. Put this folder on Vercel (New Project, pick this repo, set Root Directory to `daily/2026-10-03-prosal-ledger`). No build step.
2. In Stripe, make a Payment Link for $149 a year. Set "after payment" to redirect to `https://YOUR-SITE/?session_id={CHECKOUT_SESSION_ID}`. Optional: add a custom text field with the key `practice` so the license shows the practice's name.
3. In Vercel, add two environment variables: `STRIPE_SECRET_KEY` (from Stripe) and `PL_SECRET` (any long random phrase, 16+ characters; never change it or old keys stop working).
4. Paste the Payment Link into `config.js` as `buyUrl`.

After that it runs with nobody touching it: the buyer pays, lands back on the app, and it unlocks.

## What's not here yet

- **No benchmark data collection.** The numbers never leave the browser. That's the selling point for a practice, and it also means there's no data set building up. An opt-in "share anonymously, see how you compare" would be the way to add it later.
- **No import from practice software.** Numbers are typed in from the production report.
- **Renewal is manual.** The key runs out after a year and a week; the buyer pays again.
- **Vercel's free plan is for non-commercial use.** Once it takes money, that's $20 a month for Pro, or move the two small `api/` files to a host whose free tier allows it.

## The limits of what it knows

It does the arithmetic the contract describes. It is not legal, tax or payroll advice, and it says so on the page. Mark Opperman, who designed ProSal, says a true ProSal has no carry-forward at all; plenty of contracts have one anyway, so it's a setting, off or on.
