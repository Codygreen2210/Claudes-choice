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

const stripe = (session, status = 200) => async (url, opts) => {
  stripe.calls.push({ url, auth: opts.headers.Authorization });
  return { ok: status >= 200 && status < 300, status, json: async () => session };
};
stripe.calls = [];
const paid = (o = {}) => ({ status: 'complete', payment_status: 'paid', created: NOW / 1000, customer_details: { name: 'Pine Hollow Animal Clinic' }, ...o });

test('a key reads back with the practice name and end date', () => {
  const key = makeKey({ name: 'Pine Hollow Animal Clinic', exp: NOW + 30 * DAY, id: 'abc' }, SECRET);
  assert.match(key, /^PL1\.[\w-]+\.[\w-]+$/);
  assert.deepEqual(readKey(key, SECRET, NOW), { ok: true, name: 'Pine Hollow Animal Clinic', exp: NOW + 30 * DAY });
  assert.equal(readKey(`  ${key}\n`, SECRET, NOW).ok, true, 'pasted with spaces around it');
});

test('a changed key is refused', () => {
  const key = makeKey({ name: 'A', exp: NOW + DAY, id: 'x' }, SECRET);
  const [v, body, sig] = key.split('.');
  // Forge a later end date and keep the old signature.
  const forged = Buffer.from(JSON.stringify({ n: 'A', e: NOW + 9999 * DAY, i: 'x' })).toString('base64url');
  assert.equal(readKey(`${v}.${forged}.${sig}`, SECRET, NOW).ok, false);
  assert.equal(readKey(`${v}.${body}.${sig.slice(0, -2)}AA`, SECRET, NOW).ok, false);
  assert.equal(readKey(key, 'a-different-secret-entirely', NOW).ok, false);
  for (const junk of ['', 'PL1', 'PL1..', 'hello', null, undefined, 'PL2.a.b']) assert.equal(readKey(junk, SECRET, NOW).ok, false);
});

test('a key past its end date is refused and says why', () => {
  const key = makeKey({ name: 'A', exp: NOW - 1, id: 'x' }, SECRET);
  const r = readKey(key, SECRET, NOW);
  assert.equal(r.ok, false);
  assert.match(r.reason, /run out/);
  assert.equal(readKey(key, SECRET, NOW - 2).ok, true, 'still good the moment before');
});

test('a short secret is refused rather than making weak keys', () => {
  assert.throws(() => makeKey({ name: 'A', exp: NOW, id: 'x' }, 'short'));
});

test('a paid checkout becomes a key good for a year and a week', async () => {
  stripe.calls = [];
  const r = await claim(SESSION, { stripeKey: STRIPE, secret: SECRET, fetchImpl: stripe(paid()) });
  assert.equal(r.ok, true);
  assert.equal(r.name, 'Pine Hollow Animal Clinic');
  assert.equal(r.exp, NOW + TERM_DAYS * DAY);
  assert.equal(readKey(r.key, SECRET, NOW).ok, true);
  assert.equal(stripe.calls[0].url, `https://api.stripe.com/v1/checkout/sessions/${SESSION}`);
  assert.equal(stripe.calls[0].auth, `Bearer ${STRIPE}`);
});

test('the same checkout always gives the same key', async () => {
  const a = await claim(SESSION, { stripeKey: STRIPE, secret: SECRET, fetchImpl: stripe(paid()) });
  const b = await claim(SESSION, { stripeKey: STRIPE, secret: SECRET, fetchImpl: stripe(paid()) });
  assert.equal(a.key, b.key);
});

test('the practice name typed at checkout wins over the cardholder name', async () => {
  const s = paid({ custom_fields: [{ key: 'practice', text: { value: 'Bayou Road Vet' } }] });
  const r = await claim(SESSION, { stripeKey: STRIPE, secret: SECRET, fetchImpl: stripe(s) });
  assert.equal(r.name, 'Bayou Road Vet');
});

test('an unpaid or unfinished checkout gets nothing', async () => {
  for (const s of [paid({ payment_status: 'unpaid' }), paid({ status: 'open' }), paid({ status: 'expired' })]) {
    const r = await claim(SESSION, { stripeKey: STRIPE, secret: SECRET, fetchImpl: stripe(s) });
    assert.equal(r.ok, false);
    assert.equal(r.status, 402);
    assert.equal(r.key, undefined);
  }
});

test('a made-up checkout id never reaches Stripe', async () => {
  stripe.calls = [];
  for (const id of ['', 'abc', 'cs_test_', 'cs_test_../../charges', "cs_test_abc'; drop", null]) {
    const r = await claim(id, { stripeKey: STRIPE, secret: SECRET, fetchImpl: stripe(paid()) });
    assert.equal(r.status, 400);
  }
  assert.equal(stripe.calls.length, 0);
});

test('Stripe not finding it, being down, or not set up each say so plainly', async () => {
  assert.equal((await claim(SESSION, { stripeKey: STRIPE, secret: SECRET, fetchImpl: stripe({}, 404) })).status, 404);
  assert.equal((await claim(SESSION, { stripeKey: STRIPE, secret: SECRET, fetchImpl: stripe({}, 500) })).status, 502);
  assert.equal((await claim(SESSION, { stripeKey: STRIPE, secret: SECRET, fetchImpl: async () => { throw new Error('down'); } })).status, 502);
  assert.equal((await claim(SESSION, { stripeKey: '', secret: SECRET, fetchImpl: stripe(paid()) })).status, 503);
});

// ---------- the two web endpoints, called the way Vercel calls them ----------

const call = async (handler, url) => {
  const res = { code: 0, body: null, headers: {}, setHeader(k, v) { this.headers[k] = v; }, status(c) { this.code = c; return this; }, json(b) { this.body = b; return this; } };
  await handler({ url }, res);
  return res;
};

test('/api/check answers for a good key, a bad key, and when not set up', async () => {
  const old = process.env.PL_SECRET;
  process.env.PL_SECRET = SECRET;
  const key = makeKey({ name: 'Bayou Road Vet', exp: Date.now() + DAY, id: 'x' }, SECRET);
  const good = await call(checkHandler, `/api/check?key=${encodeURIComponent(key)}`);
  assert.equal(good.code, 200);
  assert.equal(good.body.ok, true);
  assert.equal(good.body.name, 'Bayou Road Vet');
  assert.equal(good.headers['Cache-Control'], 'no-store');
  assert.equal((await call(checkHandler, '/api/check?key=nope')).body.ok, false);
  assert.equal((await call(checkHandler, '/api/check')).body.ok, false);
  delete process.env.PL_SECRET;
  assert.equal((await call(checkHandler, `/api/check?key=${key}`)).code, 503);
  if (old) process.env.PL_SECRET = old;
});

test('/api/claim refuses a bad id and never leaks a key in the error', async () => {
  const r = await call(claimHandler, '/api/claim?session_id=abc');
  assert.equal(r.code, 400);
  assert.deepEqual(Object.keys(r.body).sort(), ['error', 'ok']);
});
