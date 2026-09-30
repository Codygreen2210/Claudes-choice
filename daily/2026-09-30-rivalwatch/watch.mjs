#!/usr/bin/env node
// RivalWatch: keep an eye on competitor Shopify stores and get a daily digest.
//   node watch.mjs add rival-store.com     add a store to watch
//   node watch.mjs list                     show watched stores
//   node watch.mjs run [--out digest.md]    check every store, save snapshots, print the digest
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { fetchCatalog, storeRoot } from './lib/feed.mjs';
import { diffCatalogs } from './lib/diff.mjs';
import { toMarkdown } from './lib/digest.mjs';

const DATA = process.env.RIVALWATCH_DATA || join(process.cwd(), 'data');
const LIST = join(DATA, 'stores.json');
const snapPath = (store) => join(DATA, 'snapshots', new URL(store).host + '.json');

function loadStores() { return existsSync(LIST) ? JSON.parse(readFileSync(LIST, 'utf8')) : []; }
function saveStores(s) { mkdirSync(DATA, { recursive: true }); writeFileSync(LIST, JSON.stringify(s, null, 2) + '\n'); }

export async function runAll(stores, { fetchImpl, sleep } = {}) {
  mkdirSync(join(DATA, 'snapshots'), { recursive: true });
  const results = [];
  for (const store of stores) {
    try {
      const after = await fetchCatalog(store, { fetchImpl, sleep });
      const path = snapPath(after.store);
      if (!existsSync(path)) {
        results.push({ store: after.store, firstRun: true, count: after.products.length, events: [] });
      } else {
        const before = JSON.parse(readFileSync(path, 'utf8'));
        results.push({ store: after.store, events: diffCatalogs(before, after) });
      }
      writeFileSync(path, JSON.stringify(after));
    } catch (e) {
      results.push({ store: storeRoot(store), error: e.message, events: [] });
    }
  }
  return results;
}

const isMain = process.argv[1] && import.meta.url.endsWith(process.argv[1].split('/').pop());
if (isMain) {
  const [cmd, arg] = process.argv.slice(2);
  if (cmd === 'add' && arg) {
    const s = loadStores(); const root = storeRoot(arg);
    if (!s.includes(root)) { s.push(root); saveStores(s); }
    console.log(`Watching ${s.length} store(s): ${s.join(', ')}`);
  } else if (cmd === 'list') {
    console.log(loadStores().join('\n') || 'No stores yet. Add one: node watch.mjs add rival-store.com');
  } else if (cmd === 'run') {
    const md = toMarkdown(await runAll(loadStores()));
    console.log(md);
    const i = process.argv.indexOf('--out');
    if (i !== -1 && process.argv[i + 1]) writeFileSync(process.argv[i + 1], md + '\n');
  } else {
    console.log('Usage:\n  node watch.mjs add rival-store.com\n  node watch.mjs list\n  node watch.mjs run [--out digest.md]');
  }
}
