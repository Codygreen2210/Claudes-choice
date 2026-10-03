// GET /api/claim?session_id=cs_...  ->  { ok, key, exp }
// Stripe sends the buyer back with their checkout id. This trades it for a
// download pass, after asking Stripe whether it was really paid.
import { claim } from '../lib/license.mjs';

export default async function handler(req, res) {
  const id = new URL(req.url, 'http://x').searchParams.get('session_id');
  const out = await claim(id, { stripeKey: process.env.STRIPE_SECRET_KEY, secret: process.env.PP_SECRET });
  res.setHeader('Cache-Control', 'no-store');
  res.status(out.ok ? 200 : out.status).json(out.ok ? out : { ok: false, error: out.error });
}
