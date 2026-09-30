#!/usr/bin/env node
// Usage: node tokentrim.mjs calls.jsonl [--days N]
// Input: one JSON object per line per API call: {model, messages|prompt, output?, usage?}
import { readFileSync } from 'node:fs';
import { analyze } from './analyze.mjs';
import { report } from './report.mjs';
const args = process.argv.slice(2);
const file = args.find((x) => !x.startsWith('--'));
if (!file) { console.error('Usage: node tokentrim.mjs calls.jsonl [--days N]'); process.exit(1); }
const di = args.indexOf('--days'); const days = di >= 0 ? Number(args[di + 1]) || 1 : 1;
const rows = readFileSync(file, 'utf8').split('\n').filter((l) => l.trim()).flatMap((l, i) => {
  try { return [JSON.parse(l)]; } catch { console.error(`Skipped line ${i + 1}: not JSON`); return []; } });
console.log(report(analyze(rows), days));
