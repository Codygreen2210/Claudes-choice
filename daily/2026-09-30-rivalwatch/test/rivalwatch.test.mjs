import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fetchCatalog, storeRoot } from '../lib/feed.mjs';
import { diffCatalogs, sortEvents } from '../lib/diff.mjs';
import { toMarkdown } from '../lib/digest.mjs';

process.env.RIVALWATCH_DATA = mkdtempSync(join(tmpdir(), 'rw-'));
const { runAll } = await import('../watch.mjs');

// A fake Shopify store whose catalog we can change between "days".
const prod = (id, title, variants) => ({ id, handle: title.toLowerCase().replace(/\s+/g, '-'), title,
  variants: variants.map(([vid, vt, price, compare, available]) => ({ id: vid, title: vt, price: String(price), compare_at_price: compare ? String(compare) : null, available })) });
const DAY1 = [
  prod(1, 'Cast Iron Skillet', [[11, 'Default Title', 39.99, null, true]]),
  prod(2, 'Smoker Chips', [[21, 'Hickory', 12.0, null, true], [22, 'Mesquite', 12.0, null, true]]),
  prod(3, 'Grill Brush', [[31, 'Default Title', 15.0, null, true]]),
];
const DAY2 = [
  prod(1, 'Cast Iron Skillet', [[11, 'Default Title', 34.99, 39.99, true]]),   // price cut + sale
  prod(2, 'Smoker Chips', [[21, 'Hickory', 13.5, null, true], [22, 'Mesquite', 12.0, null, false]]), // raise + sold out
  prod(4, 'Rib Rack', [[41, 'Default Title', 24.0, null, true]]),               // new; grill brush removed
];
function shop(catalog) {
  return async (url) => {
    const page = Number(new URL(url).searchParams.get('page'));
    const body = { products: page === 1 ? catalog : [] };
    return { ok: true, status: 200, json: async () => body };
  };
}
const noSleep = async () => {};

test('store address is cleaned up', () => {
  assert.equal(storeRoot('rival-bbq.com'), 'https://rival-bbq.com');
  assert.equal(storeRoot('https://rival-bbq.com/collections/all?x=1'), 'https://rival-bbq.com');
});

test('reads every page of a big catalog, politely', async () => {
  const many = Array.from({ length: 251 }, (_, i) => prod(i + 1, `Item ${i + 1}`, [[1000 + i, 'Default Title', 5, null, true]]));
  let calls = 0, sleeps = 0;
  const f = async (url) => { calls++; const p = Number(new URL(url).searchParams.get('page'));
    return { ok: true, status: 200, json: async () => ({ products: many.slice((p - 1) * 250, p * 250) }) }; };
  const cat = await fetchCatalog('big-shop.com', { fetchImpl: f, sleep: async () => { sleeps++; } });
  assert.equal(cat.products.length, 251);
  assert.equal(calls, 2);
  assert.equal(sleeps, 1, 'waits between pages');
});

test('not a Shopify store gives a plain message', async () => {
  const f = async () => ({ ok: false, status: 404 });
  await assert.rejects(fetchCatalog('not-shopify.com', { fetchImpl: f }), /doesn't look like a Shopify store/);
});

test('spots every kind of change a seller cares about', async () => {
  const before = await fetchCatalog('rival-bbq.com', { fetchImpl: shop(DAY1), sleep: noSleep });
  const after = await fetchCatalog('rival-bbq.com', { fetchImpl: shop(DAY2), sleep: noSleep });
  const types = sortEvents(diffCatalogs(before, after)).map((e) => e.type);
  assert.deepEqual(types, ['price_down', 'sale_start', 'price_up', 'sold_out', 'new', 'removed']);
  const cut = diffCatalogs(before, after).find((e) => e.type === 'price_down');
  assert.match(cut.text, /\$39\.99 → \$34\.99 \(-13%\)/);
});

test('first run starts watching, second run reports changes', async () => {
  const first = await runAll(['rival-bbq.com'], { fetchImpl: shop(DAY1), sleep: noSleep });
  assert.equal(first[0].firstRun, true);
  assert.match(toMarkdown(first), /Started watching 3 products/);

  const second = await runAll(['rival-bbq.com'], { fetchImpl: shop(DAY2), sleep: noSleep });
  const md = toMarkdown(second, '2026-09-30');
  assert.match(md, /6 changes across 1 store/);
  assert.match(md, /\*\*Price cuts\*\*/);
  assert.match(md, /Back in stock|Sold out: Smoker Chips \(Mesquite\)/);
  assert.match(md, /https:\/\/rival-bbq\.com\/products\/rib-rack/);
});

test('one broken store does not stop the others', async () => {
  const f = async (url) => url.includes('down-shop') ? { ok: false, status: 503 } : shop(DAY1)(url);
  const res = await runAll(['down-shop.com', 'rival-bbq.com'], { fetchImpl: f, sleep: noSleep });
  assert.match(res[0].error, /HTTP 503/);
  assert.ok(!res[1].error);
});
