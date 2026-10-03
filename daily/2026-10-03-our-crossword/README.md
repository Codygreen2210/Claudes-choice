# Our Crossword

Type answers and clues about a couple (or a birthday, a retirement, a family) and get a real interlocking crossword, laid out as a print-ready PDF with the answer key. Sizes run from 5 × 7 table cards to a 24 × 36 welcome sign.

**Product.** People open a link, make their puzzle, pay, download. Nobody on our side touches an order.

## Why this exists

"Sip and solve" crosswords are a wedding and shower table game. On Etsy they are sold as custom orders: the buyer sends up to 40 clues, the seller builds the puzzle by hand, a first draft comes back in 1 to 2 business days, and the price runs about $14 on sale to $35 regular ([example listing](https://www.etsy.com/listing/1419910020/custom-crossword-puzzle-giant-crossword)).

This does the same job in the time it takes to type the clues, for $9, and the buyer can keep changing it.

## What the customer does

1. Opens the link. A finished example is already on the page.
2. Taps "Start with my own" and types answers and clues (or pastes a list).
3. Picks a look and a paper size, taps Download, pays once.

Free to make and preview (with a watermark). No account, no install.

## What's in it

| File | What it does |
|---|---|
| `construct.js` | Builds the puzzle: every answer crosses another, nothing touches side by side. Includes a referee that re-checks every finished puzzle from scratch. |
| `layout.js` | Lays out the page in printer's points for 7 paper sizes and 4 looks, then draws it on screen and into the PDF from the same list, so the preview is the print. |
| `app.js`, `index.html` | The screen. |
| `config.js` | The one file to edit to start charging (Stripe link, price, credit line). |
| `lib/license.mjs`, `api/` | After Stripe checkout, confirms payment with Stripe and hands back a download pass good for a month. |
| `vendor/jspdf.umd.min.js` | jsPDF 2.5.2 (MIT license), the PDF writer. |
| `tools/` | Local server and the one-file demo packer. |
| `test/` | 36 unit tests and a 14-step run in a real browser. |

## Run it

```
npm install                      # only needed for the tests
node tools/dev-server.mjs        # then open http://localhost:4173
npm test                         # 36 unit tests, quiet output
node test/e2e.mjs                # real browser run (needs Playwright)
```

## How it was tested

- 30 seeds of an 18-answer wedding list: all 18 placed, all crossing, zero faults from the referee.
- 60 random lists of 3 to 30 answers: every puzzle sound, no answer lost without a reason.
- The referee itself is tested with planted faults (clashing letters, stray letters, a puzzle in two pieces, skipped numbers), so a clean result means something.
- Every paper size with every look: nothing runs off the page, clues never run into the grid or the footer.
- Too many clues for a small card is flagged on screen instead of being cut off.
- The PDF is checked for two pages at the exact paper size, as real text.
- Browser run on phone and desktop: edit, shuffle, change look and size, start fresh, paste a list, reload, hit the pay step, refuse a bad pass, accept a good one, download the file and check its page size.

## To start charging

1. Put this folder on Vercel (New Project, this repo, Root Directory `daily/2026-10-03-our-crossword`). No build step.
2. In Stripe, make a Payment Link for $9. Set "after payment" to redirect to `https://YOUR-SITE/?session_id={CHECKOUT_SESSION_ID}`.
3. In Vercel, add two environment variables: `STRIPE_SECRET_KEY` and `OC_SECRET` (any long random phrase, 16+ characters).
4. Paste the Payment Link into `config.js` as `buyUrl`. Put your web address in `credit` so it prints small at the bottom of every page: the guests at the table are the next customers.

## What's not here yet

- **No shaped grids** (hearts and so on).
- **Plain built-in PDF fonts only** (Times and Helvetica). Emoji and non-Western letters in clues are dropped.
- **No solve-on-your-phone link.** Print only.
- **The watermark is the only lock on the preview.** Someone determined could screenshot a small copy; the full-size print file needs the pass.
- **Vercel's free plan is for non-commercial use.** Once it takes money, that's $20 a month, or move the two small `api/` files elsewhere.

## Who else does this

Counted Oct 3, 2026: Etsy custom-order sellers (by hand, 1 to 2 days), [Crossword Your Event](https://crossword-your-event.com/en/) (from €19.99), [Love Puzzle](https://lovepuzzle.com/games/custom-crossword-puzzle-gift/) ($5, solved on a phone, not a print file), [PuzzleGenio](https://puzzlegenio.com/wedding-crossword-puzzle-maker) (free PDFs), Perfect Crosswords (price not shown). It is not an empty field.
