#!/usr/bin/env node
// Usage: node rowproof.mjs statement.pdf [more.pdf ...] [--csv] [--xlsx] [--ofx]
// Prints what it found and whether it adds up; writes files next to each PDF.
import { readFileSync, writeFileSync } from 'node:fs';
import { nodeInflate } from './lib/pdf.mjs';
import { convert, toCSV, toXLSX, toOFX } from './lib/rowproof.mjs';

const args = process.argv.slice(2);
const files = args.filter((a) => !a.startsWith('--'));
if (!files.length) { console.error('Usage: node rowproof.mjs statement.pdf [--csv] [--xlsx] [--ofx]'); process.exit(1); }
const want = (f) => args.includes('--' + f);
let bad = 0;
for (const f of files) {
  let r;
  try { r = await convert(readFileSync(f), { inflate: nodeInflate }); }
  catch (e) { console.log(`${f}: ${e.message}`); bad++; continue; }
  const s = r.summary, c = s.counts || {};
  const tag = { proven: 'PROVEN', 'rows-proven': 'ROWS PROVEN (ends not confirmed)', check: 'CHECK THESE', unchecked: 'READ, NOT PROVEN' }[s.verdict] || 'NOTHING FOUND';
  console.log(`${f}: ${tag} — ${s.rows || 0} rows from ${r.pages} page(s)`);
  if (s.rows) {
    console.log(`  How: ${s.reading}`);
    console.log(`  Proven by running balance: ${c.verified || 0}, by totals: ${c['totals-match'] || 0}, don't add up: ${c.mismatch || 0}, bank's own balance typo: ${c['balance-typo'] || 0}`);
    console.log(`  Opening ${s.opening?.toFixed(2) ?? '?'} → closing ${s.closing?.toFixed(2) ?? '?'} (rows add to ${s.computedClosing?.toFixed(2) ?? '?'})`);
  }
  for (const w of r.warnings) console.log('  ! ' + w);
  if (s.verdict !== 'proven') bad++;
  const base = f.replace(/\.pdf$/i, '');
  if (want('csv')) writeFileSync(base + '.csv', toCSV(r.rows));
  if (want('xlsx')) writeFileSync(base + '.xlsx', toXLSX(r.rows));
  if (want('ofx')) writeFileSync(base + '.ofx', toOFX(r.rows, { closing: s.closing }));
}
process.exitCode = bad ? 2 : 0;
