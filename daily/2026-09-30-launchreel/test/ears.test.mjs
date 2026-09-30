// The studio ears hook: finds listen.py, reads its report, fixes true peak, and never breaks a render when missing.
import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { findEars, fixable, checkAudio, listen } from '../lib/ears.mjs';
import { makeMusic } from '../lib/music.mjs';
import { toneBalance, bandSplit } from '../lib/music/engine.mjs';

const ears = findEars();

test('fixable: true peak over -1 dBTP or clipping', () => {
  assert.equal(fixable({ loudness: { true_peak_dbtp: -0.5, clipped_samples: 0 } }), true);
  assert.equal(fixable({ loudness: { true_peak_dbtp: -2, clipped_samples: 3 } }), true);
  assert.equal(fixable({ loudness: { true_peak_dbtp: -1.5, clipped_samples: 0 } }), false);
});

test('missing ears: skipped with a reason, no throw', async () => {
  const old = process.env.LAUNCHREEL_EARS;
  process.env.LAUNCHREEL_EARS = '/nope/listen.py';
  try { const r = await listen('/nope.wav', { out: tmpdir() }); assert.match(r.skipped, /not found/); }
  finally { if (old === undefined) delete process.env.LAUNCHREEL_EARS; else process.env.LAUNCHREEL_EARS = old; }
});

test('tone balance pulls a sub-heavy mix toward the ears target', () => {
  const n = 44100 * 2, L = new Float32Array(n), R = new Float32Array(n);
  for (let i = 0; i < n; i++) { const t = i / 44100; L[i] = R[i] = 0.5 * Math.sin(2 * Math.PI * 50 * t) + 0.02 * Math.sin(2 * Math.PI * 1000 * t) + 0.005 * Math.sin(2 * Math.PI * 8000 * t); }
  const before = bandSplit(L, R);
  const r = toneBalance(L, R);
  const after = bandSplit(L, R);
  assert.ok(r.cutDb < 0 && after.low < before.low);
  assert.ok(r.cutDb >= -6 && r.liftDb <= 6);
});

test('real track through the studio ears: peak ends under -1 dBTP, notes written', { skip: !ears && 'studio ears not present' }, async () => {
  const dir = mkdtempSync(join(tmpdir(), 'ears-'));
  const wav = join(dir, 'm.wav');
  writeFileSync(wav, makeMusic({ seconds: 8, genre: 'blues', key: 'F', seed: 3, volume: 0.5, parts: {} }));
  const r = await checkAudio(wav, { out: join(dir, 'notes'), picture: false });
  if (r.skipped) return; // python deps missing on this machine
  assert.ok(r.report.loudness.true_peak_dbtp <= -1, 'true peak ' + r.report.loudness.true_peak_dbtp);
  assert.equal(r.ok, true);
});
