// Download passes. A pass is an end date signed with a secret only the server
// knows. No database: the pass carries its own proof.
import { createHmac, timingSafeEqual } from 'node:crypto';

const DAY = 86400000;
export const TERM_DAYS = 31; // a month to build, tweak and download again

const enc = (buf) => Buffer.from(buf).toString('base64url');
const sign = (body, secret) => createHmac('sha256', secret).update(body).digest();
const BAD = 'That pass is not one of ours. Check for a missing character.';

export function makeKey({ exp, id }, secret) {
  if (!secret || secret.length < 16) throw new Error('PP_SECRET must be at least 16 characters');
  const body = enc(JSON.stringify({ e: exp, i: id }));
  return `PP1.${body}.${enc(sign(body, secret))}`;
}

export function readKey(key, secret, now = Date.now()) {
  const m = /^PP1\.([A-Za-z0-9_-]+)\.([A-Za-z0-9_-]+)$/.exec(String(key || '').trim());
  if (!m || !secret) return { ok: false, reason: BAD };
  const want = sign(m[1], secret);
  const got = Buffer.from(m[2], 'base64url');
  if (got.length !== want.length || !timingSafeEqual(got, want)) return { ok: false, reason: BAD };
  let p;
  try { p = JSON.parse(Buffer.from(m[1], 'base64url').toString('utf8')); } catch { return { ok: false, reason: 'That pass could not be read.' }; }
  if (!Number.isFinite(p.e) || p.e < now) return { ok: false, reason: 'This pass has run out. A new one covers another month.', exp: p.e };
  return { ok: true, exp: p.e };
}

// Turn a finished Stripe checkout into a pass. Asks Stripe directly whether
// the session was paid, so a made-up session id gets nothing. The same
// session always gives the same pass, so refreshing the page is harmless.
export async function claim(sessionId, { stripeKey, secret, fetchImpl = fetch }) {
  if (!/^cs_(test|live)_[A-Za-z0-9]{10,200}$/.test(String(sessionId || ''))) return { ok: false, status: 400, error: 'That does not look like a checkout from us.' };
  if (!stripeKey || !secret) return { ok: false, status: 503, error: 'Payments are not set up yet.' };
  let r;
  try {
    r = await fetchImpl(`https://api.stripe.com/v1/checkout/sessions/${sessionId}`, { headers: { Authorization: `Bearer ${stripeKey}` } });
  } catch {
    return { ok: false, status: 502, error: 'Could not reach the payment company. Try again in a minute.' };
  }
  if (r.status === 404) return { ok: false, status: 404, error: 'No checkout found with that id.' };
  if (!r.ok) return { ok: false, status: 502, error: 'The payment company did not answer. Try again in a minute.' };
  const s = await r.json();
  if (!(s.status === 'complete' && (s.payment_status === 'paid' || s.payment_status === 'no_payment_required'))) return { ok: false, status: 402, error: 'That checkout has not been paid.' };
  const exp = s.created * 1000 + TERM_DAYS * DAY;
  return { ok: true, key: makeKey({ exp, id: sessionId.slice(-8) }, secret), exp };
}
