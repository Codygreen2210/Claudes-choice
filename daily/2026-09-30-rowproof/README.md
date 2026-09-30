# RowProof

Bank statement PDFs to Excel, CSV or OFX, with every row checked against the bank's own numbers.

Bookkeepers, accountants, loan officers and small business owners copy transactions out of PDF statements all the time. Converter tools exist, but they hand back a spreadsheet and you still have to check it by hand, because one misread digit throws off the books. RowProof does that checking: each row has to match the bank's printed running balance, and the opening balance plus every row has to land on the closing balance. Rows that don't fit are marked red with their page number. Its answer is one of:

- **Proven**: every row adds up, and the printed opening and closing balances bracket all of them, so nothing is missing.
- **Rows proven**: every row adds up, but the opening or closing balance wasn't printed, so a lost page at one end can't be ruled out.
- **Check these**: named rows don't add up.
- **Read, not proven**: the statement prints nothing to check against.

It runs entirely on your own computer or in your browser. Statements are never uploaded, it uses no AI, and it has no dependencies.

Built Sept 30, 2026, as a daily build. It's a product: it runs on its own, with nobody's time per customer.

## Use it

In a browser: open `web/index.html`, drop in PDFs, download Excel, CSV or OFX. It's a single static file with no server, so it can be hosted on Vercel as-is.

From the command line (Node 18+, no install):

```
node rowproof.mjs statement.pdf [more.pdf ...] --xlsx --csv --ofx
```

## How it works

1. **`lib/pdf.mjs`** reads the PDF itself: objects, compressed and object streams, fonts (including embedded CID fonts via their text maps), and the page drawing commands. It records every piece of text with its exact position and width.
2. **`lib/statement.mjs`** rebuilds lines and columns. It copes with numbers that are right-, left- or centre-aligned, rows padded with spaces, letter-spaced labels, descriptions that wrap above or below the date line, balances printed under a label, and section-style statements (deposits and withdrawals listed separately). It reads dates in most formats, works out day-first vs month-first, and fills in the year across a December to January boundary.
3. It then tries each sensible reading of the columns: money out or money in, one signed column, flipped signs, sections, with or without a balance column. It keeps the reading that the bank's printed balances agree with. It also tells a misread row from a typo in the bank's own printed balance.
4. **`lib/export.mjs`** writes CSV (with formula text defused for Excel), a real `.xlsx` (zip and XML written by hand) and OFX 1.02.

## Tested

`node --test --test-reporter=dot "test/*.test.mjs"` (13 tests):

- Six generated statements with known answers, each a different style: two money columns over a year end and page break; the same file with compressed object streams; one signed column with balances only at day end; Chase-style sections; a Chrome-printed UK statement with embedded fonts and a planted balance typo; and a scan.
- **A blind test on someone else's statements**: three sample statements from [AyonPal/bank-statement-pdf-parser](https://github.com/AyonPal/bank-statement-pdf-parser) (MIT). RowProof was not built against them. After fixes, all 54 rows match their answer files on date, amount, balance and full description.
- **Corruption**: 400 randomly damaged files. None came back "proven" with a wrong number. (An earlier version did, when a whole page was lost; that's why "proven" now needs both printed ends.)
- Speed: 61 pages and 1,700 rows in about 0.25 seconds.
- The web page was driven in Chromium: samples, upload, Excel download, scan message, phone width and dark mode.

## What it doesn't do (yet)

- Scanned or photographed statements need OCR. It says so rather than guessing.
- Password-protected PDFs: print them to a new PDF first.
- Amounts must use a dot for decimals (1,234.56). European 1.234,56 isn't read yet.
- It hasn't met real bank PDFs beyond public samples. The generated ones copy real layouts, but every bank is a little different. When it can't prove a statement, it says so.

`build-web.mjs` bundles `lib/` into `web/index.html`. Samples in `web/samples/` are fictional banks.

MIT license.
