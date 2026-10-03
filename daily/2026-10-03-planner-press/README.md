# Planner Press

Builds a tap-to-navigate planner PDF in the browser, for GoodNotes, Notability and Xodo on a tablet. Pick the year, the sections, the page shape and a color, then download.

**Product.** People open a link, see a finished planner, change what they want, download it. Free with a small credit line on every page; $9 once takes the credit line off. Nobody on our side touches an order.

## Why this exists

Hyperlinked planners are sold two ways: Fiverr sellers build one by hand (listings start around $25) and Etsy sellers resell fixed ones. This makes one, with your year and week start, in a few seconds.

## What the customer does

1. Opens the link. A 2027 planner is already on the page (no sign-up, no install).
2. Changes the year (2026, 2027, 2028), week start (Sunday or Monday), sections (year overview, monthly, weekly, daily, notes), page shape (landscape or portrait) and color (Classic, Sage, Rose, Night). The page redraws. Flip through a year, month, week, day or notes page, or tap the tabs and dates right on the preview.
3. Taps Download. Free file has "Made with Planner Press" at the bottom of every page, for personal use. Paying $9 removes it.

Everything is built on the person's device. The page says so.

## How the links work

- Month tabs run down the right edge of every page and jump to that month. A Year tab goes back to the year overview, a Notes tab to the notes.
- On a month page, a day number opens its week page. The rest of that day's box opens its day page (when daily pages are included). With no weekly pages, the number opens the day page.
- On a week page, each day header opens that day. A day page has a "Week N" link back.
- Year overview: each month name opens that month.
- If a section is left out, links fall back sensibly: with no monthly pages, a month tab opens the week (or day) that holds the 1st.

Week 1 is the week that holds January 1. The first and last weeks can include days from the next or last year; those are dimmed and are not counted as part of the year.

## What's in it

| File | What it does |
|---|---|
| `dates.js` | Calendar math with no Date object: weekdays, leap years, weeks, month grids. |
| `plan.js` | The page plan: which pages exist, their order, and every link that must exist. Also the link checker. |
| `layout.js` | Draws each page as a list of shapes, text and links in points, for both orientations and 4 colors. The same list makes the SVG preview and the PDF (via jsPDF `doc.link`). |
| `app.js`, `index.html` | The screen. |
| `config.js` | The one file to edit to start charging (Stripe link, price, credit line). |
| `lib/license.mjs`, `api/` | After Stripe checkout, confirms payment with Stripe and hands back a pass good for 31 days. Same as the crossword build. |
| `vendor/jspdf.umd.min.js` | jsPDF 2.5.2 (MIT license), the PDF writer. |
| `tools/` | Local server and the one-file demo packer (`demo/planner-press.html`). |
| `test/` | 40 unit tests and a 16-step run in a real browser. |

## Run it

```
npm install                      # only needed for the tests
node tools/dev-server.mjs        # then open http://localhost:4173
npm test                         # 40 unit tests, quiet output
node test/e2e.mjs                # real browser run (needs Playwright)
node tools/build-demo.mjs        # rebuilds the one-file demo
```

## How it was tested

- Dates: known weekdays, every day from 2000 to 2040 against the built-in Date, 2028 leap year, 365 and 366 daily pages, weeks start on the chosen day, every date in exactly one week page, weeks that cross a year end.
- Links: in 10 section setups, every drawn link matches the plan, and a second checker that does not trust the plan looks at the page each link lands on. Every month tab on every page, every day number, nothing past the last page. Planted faults (a wrong tab, a link past the end, a missing link, a wrong week, a wrong plan) are all caught.
- Layout: both shapes, all four colors, Sunday and Monday starts, every page of a 2028 planner: nothing outside the page, nothing in the margins or under the tabs.
- PDF: page count and page size, link annotations in the file equal the planned count, each one sits where it was drawn and points at the planned page, the credit line is on every free page and none of the paid pages.
- Browser (Chromium): desktop and 400px phone, no sideways scroll, no console errors, options change the preview, tapping preview links works, free download (441 pages, 7,6xx links, credit on every page), a real signed pass removes the credit line from the screen and the downloaded file, reload keeps the pass, dark mode, and the one-file demo.
- Looked at screenshots and rasterized PDF pages by eye.
- Not tested: opening the PDF in GoodNotes, Notability or Xodo on a tablet. These are standard PDF internal links, which those apps are meant to follow, but nobody has tapped one on a tablet yet.

## To start charging

1. Put this folder on Vercel (New Project, this repo, Root Directory `daily/2026-10-03-planner-press`). No build step.
2. In Stripe, make a Payment Link for $9. Set "after payment" to redirect to `https://YOUR-SITE/?session_id={CHECKOUT_SESSION_ID}`.
3. In Vercel, add two environment variables: `STRIPE_SECRET_KEY` and `PP_SECRET` (any long random phrase, 16+ characters).
4. Paste the Payment Link into `config.js` as `buyUrl`.

## Choices made

- Page sizes are 842 × 595 pt (landscape) and 595 × 842 pt (portrait), A4 proportions. Fits most tablet note apps.
- Default planner is 441 pages (about 1.5 MB). Turning off daily pages brings it to 76.
- 10 notes pages. Fonts are the PDF built-ins (Helvetica, Times).
- The pass lasts 31 days, copied from the crossword build, even though the price says "once".
- Without a Stripe link the page says "Not on sale yet."

## What's not here yet

- Only 2026, 2027 and 2028. Only Sunday or Monday starts.
- No holidays, no habit trackers, no cover page, no sticker or hyperlinked index of notes.
- The preview is one page at a time; there is no thumbnail strip.
- Week numbers count from the week holding January 1, not ISO week numbers.
- The credit line is the only lock. A determined person could cover it in the note app.
- Vercel's free plan is for non-commercial use. Once it takes money, that's $20 a month, or move the two small `api/` files elsewhere.

## Who else does this

Fiverr sellers (hand-built, from about $25), Etsy digital planner sellers (fixed designs, no custom year or week start), and free template makers. Not an empty field; the pitch is instant and custom.
