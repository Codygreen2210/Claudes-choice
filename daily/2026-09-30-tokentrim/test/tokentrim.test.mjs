import { test } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { writeFileSync, mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { priceKey } from '../prices.mjs';
import { analyze } from '../analyze.mjs';
import { report } from '../report.mjs';

const SYS = 'You are a support bot for Acme. Policy: ' + 'Refunds within 30 days. '.repeat(400); // ~2,400 tokens
const call = (q, model = 'gpt-4o', out = 'ok') => ({ model, messages: [{ role: 'system', content: SYS }, { role: 'user', content: q }], output: out });

test('model names map to prices, unknown stays unknown', () => {
  assert.equal(priceKey('gpt-4o-mini-2024-07-18'), 'gpt-4o-mini');
  assert.equal(priceKey('gpt-4o-2024-08-06'), 'gpt-4o');
  assert.equal(priceKey('claude-3-5-sonnet-latest'), 'claude-sonnet');
  assert.equal(priceKey('llama-3'), null);
});

test('finds the shared system prompt and prices the caching saving', () => {
  const a = analyze([call('where is my order'), call('cancel please'), call('refund?')]);
  assert.equal(a.prefixes.length, 1);
  assert.equal(a.prefixes[0].calls, 3);
  assert.ok(a.prefixes[0].tokens > 2000);
  // 2 repeat calls * ~2,400 tokens * ($2.50 - $1.25)/M ≈ $0.006
  assert.ok(Math.abs(a.prefixSave - 2 * a.prefixes[0].tokens * 1.25 / 1e6) < 1e-9);
});

test('exact repeats counted once as paid, extras as savings', () => {
  const a = analyze([call('hi'), call('hi'), call('hi'), call('bye')]);
  assert.equal(a.duplicates.groups, 1);
  assert.equal(a.duplicates.extraCalls, 2);
  assert.ok(a.duplicates.save > 0);
});

test('short answers on expensive models become downgrade candidates, long ones do not', () => {
  const a = analyze([call('yes or no?', 'claude-opus-4', 'yes'), call('write an essay', 'claude-opus-4', 'x'.repeat(4000))]);
  assert.equal(a.downgrades[0].calls, 1);
  assert.equal(a.downgrades[0].to, 'claude-sonnet');
});

test('uses logged token counts over estimates, and flags unpriced models', () => {
  const a = analyze([{ model: 'gpt-4o', prompt: 'x', usage: { prompt_tokens: 1e6, completion_tokens: 0 } }, { model: 'mystery-1', prompt: 'x' }]);
  assert.equal(a.total, 2.5);
  assert.deepEqual(a.unknownModels, ['mystery-1']);
  assert.match(report(a), /Not priced.*mystery-1/);
});

test('CLI reads JSONL, skips bad lines, scales to a month', () => {
  const f = join(mkdtempSync(join(tmpdir(), 'tt-')), 'c.jsonl');
  writeFileSync(f, [call('a'), call('b')].map((x) => JSON.stringify(x)).join('\n') + '\nnot json\n');
  const out = execFileSync(process.execPath, [new URL('../tokentrim.mjs', import.meta.url).pathname, f, '--days', '1'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
  assert.match(out, /2 calls over 1 day/);
  assert.match(out, /prompt caching/);
});
