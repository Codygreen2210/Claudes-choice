# RivalWatch

A morning digest of what your competitors changed overnight. Point it at the Shopify stores you compete with, and every day it tells you, in plain English:

- **Price cuts and raises**, with the before and after and the percent
- **Sales that started or ended**
- **Items that sold out or came back in stock**
- **New products they added, and products they pulled**

Built Sept 30, 2026, as a daily build. It's a product: it runs on its own every morning with nobody's time per customer.

## Why

Small shops lose sales to a competitor's quiet price cut and find out a week later. The tools that watch competitors are built for bigger sellers and priced like it. A shop owner with three rivals just needs to know what changed this morning, with a link to see it.

## How it works

Every Shopify store publishes its product list at `/products.json`. It's the same catalog shoppers see, served to anyone, and it's how the store's own pages load. RivalWatch reads it once a day, saves a snapshot, and compares it to yesterday's. It reads only public product data, goes one page per second, stops at 5,000 products per store, and identifies itself honestly.

Because the data comes straight from the store's own catalog, prices are exact. Nothing is guessed from page layouts that break when a site gets redesigned.

## Use it

Node 18+, no install.

```
node watch.mjs add rival-store.com
node watch.mjs add another-rival.com
node watch.mjs run --out digest.md
```

The first run starts watching. From the second run on, you get a digest like this:

```
## rival-bbq.com — 7 changes

**Price cuts**
- Price cut: Cast Iron Skillet $39.99 → $34.99 (-13%)

**Sold out**
- Sold out: Smoker Chips (Mesquite)

**New products**
- New product: Rib Rack at $24.00
```

### Free, every morning, from your phone

Copy `github-workflow-example.yml` to `.github/workflows/rivalwatch.yml` in your own copy of this folder. GitHub runs it every morning for free, keeps the snapshots in the repo, and puts the digest on the run summary page and in `digest.md`.

## Files

- `lib/feed.mjs` — reads a store's public catalog, politely.
- `lib/diff.mjs` — compares two snapshots; finds price, sale, stock and catalog changes.
- `lib/digest.mjs` — writes the plain-English digest.
- `watch.mjs` — `add`, `list`, `run`. One broken store never stops the others.
- `test/` — offline tests with a fake store that changes between days.

```
node --test "test/*.test.mjs"
```

## Limits

Shopify stores only for now (a big share of small online shops). Some stores turn the public catalog off; RivalWatch says so plainly instead of guessing.

MIT license.
