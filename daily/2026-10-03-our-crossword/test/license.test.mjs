import { test } from 'node:test';
import assert from 'node:assert/strict';
import { makeKey, readKey, claim, TERM_DAYS } from '../lib/license.mjs';
import claimHandler from '../api/claim.js';
import checkHandler from '../api/check.js';

// Built at run time so nothing here looks like a real credential to a scanner.
const SECRET = ['test', 'secret', 'for', 'unit', 'tests'].join('-');
const STRIPE = ['sk', 'test', 'x'.repeat(24)].join('_');
const SESSION = ['cs', 'test', 'a1B2c3D4e5F6g7H8'].join('_');
const NOW = Date.UTC(2026, 9, 3);
const DAY = 86400000;
const calls = [];
const stripe = (session, status = 200) => async (url, opts) => { calls.push({ url, auth: opts.headers.Authorization }); return { ok: status >= 200 && status < 300, status, json: async () => session }; };
const paid = (o = {}) => ({ status: 'complete', payment_status: 'paid', created: NOW / 1000, ...o });

test('a pass reads back with its end date, even pasted with spaces', () => {
  const key = makeKey({ exp: NOW + 5 * DAY, id: 'abc' }, SECRET);
  assert.match(key, /^OC1\.[\w-]+\.[\w-]+$/);
  assert.deepEqual(readKey(`  ${key}\n`, SECRET, NOW), { ok: true, exp: NOW + 5 * DAY });
});

test('a forged, damaged or foreign pass is refused', () => {
  const key = makeKey({ exp: NOW + DAY, id: 'x' }, SECRET);
  const [v, body, sig] = key.split('.');
  const forged = Buffer.from(JSON.stringify({ e: NOW + 9999 * DAY, i: 'x' })).toString('base64url');
  assert.equal(readKey(`${v}.${forged}.${sig}`, SECRET, NOW).ok, false);
  assert.equal(readKey(`${v}.${body}.${sig.slice(0, -2)}AA`, SECRET, NOW).ok, false);
  assert.equal(readKey(key, 'a-different-secret-entirely', NOW).ok, false);
  for (const junk of ['', 'OC1', 'OC1..', 'hello', null, undefined, 'PL1.a.b']) assert.equal(readKey(junk, SECRET, NOW).ok, false);
});

test('a pass past its end date is refused and says why; good the moment before', () => {
  const key = makeKey({ exp: NOW - 1, id: 'x' }, SECRET);
  assert.match(readKey(key, SECRET, NOW).reason, /run out/);
  assert.equal(readKey(key, SECRET, NOW - 2).ok, true);
});

test('a short secret is refused rather than making weak passes', () => {
  assert.throws(() => makeKey({ exp: NOW, id: 'x' }, 'short'));
});

test('a paid checkout becomes a pass good for a month, and the same checkout gives the same pass', async () => {
  const a = await claim(SESSION, { stripeKey: STRIPE, secret: SECRET, fetchImpl: stripe(paid()) });
  const b = await claim(SESSION, { stripeKey: STRIPE, secret: SECRET, fetchImpl: stripe(paid()) });
  assert.equal(a.ok, true);
  assert.equal(a.exp, NOW + TERM_DAYS * DAY);
  assert.equal(a.key, b.key);
  assert.equal(readKey(a.key, SECRET, NOW).ok, true);
  assert.equal(calls[0].url, `https://api.stripe.com/v1/checkout/sessions/${SESSION}`);
  assert.equal(calls[0].auth, `Bearer ${STRIPE}`);
});

test('an unpaid or unfinished checkout gets nothing', async () => {
  for (const s of [paid({ payment_status: 'unpaid' }), paid({ status: 'open' }), paid({ status: 'expired' })]) {
    const r = await claim(SESSION, { stripeKey: STRIPE, secret: SECRET, fetchImpl: stripe(s) });
    assert.equal(r.status, 402);
    assert.equal(r.key, undefined);
  }
});

test('a made-up checkout id never reaches Stripe', async () => {
  calls.length = 0;
  for (const id of ['', 'abc', 'cs_test_', 'cs_test_../../charges', "cs_test_abc'; drop", null]) {
    assert.equal((await claim(id, { stripeKey: STRIPE, secret: SECRET, fetchImpl: stripe(paid()) })).status, 400);
  }
  assert.equal(calls.length, 0);
});

test('Stripe not finding it, being down, or not set up each say so plainly', async () => {
  assert.equal((await claim(SESSION, { stripeKey: STRIPE, secret: SECRET, fetchImpl: stripe({}, 404) })).status, 404);
  assert.equal((await claim(SESSION, { stripeKey: STRIPE, secret: SECRET, fetchImpl: stripe({}, 500) })).status, 502);
  assert.equal((await claim(SESSION, { stripeKey: STRIPE, secret: SECRET, fetchImpl: async () => { throw new Error('down'); } })).status, 502);
  assert.equal((await claim(SESSION, { stripeKey: '', secret: SECRET, fetchImpl: stripe(paid()) })).status, 503);
});

const call = async (handler, url) => {
  const res = { code: 0, body: null, headers: {}, setHeader(k, v) { this.headers[k] = v; }, status(c) { this.code = c; return this; }, json(b) { this.body = b; return this; } };
  await handler({ url }, res);
  return res;
};

test('the two web endpoints answer the way the app expects', async () => {
  process.env.OC_SECRET = SECRET;
  const key = makeKey({ exp: Date.now() + DAY, id: 'x' }, SECRET);
  const good = await call(checkHandler, `/api/check?key=${encodeURIComponent(key)}`);
  assert.equal(good.body.ok, true);
  assert.equal(good.headers['Cache-Control'], 'no-store');
  assert.equal((await call(checkHandler, '/api/check?key=nope')).body.ok, false);
  const bad = await call(claimHandler, '/api/claim?session_id=abc');
  assert.equal(bad.code, 400);
  assert.deepEqual(Object.keys(bad.body).sort(), ['error', 'ok']);
  delete process.env.OC_SECRET;
  assert.equal((await call(checkHandler, `/api/check?key=${key}`)).code, 503);
});
