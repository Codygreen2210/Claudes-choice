// GET /api/check?key=OC1....  ->  { ok, exp } or { ok: false, reason }
// Only the pass is sent. The names and clues never leave the browser.
import { readKey } from '../lib/license.mjs';

export default function handler(req, res) {
  const key = new URL(req.url, 'http://x').searchParams.get('key');
  res.setHeader('Cache-Control', 'no-store');
  if (!process.env.OC_SECRET) return res.status(503).json({ ok: false, reason: 'Payments are not set up yet.' });
  res.status(200).json(readKey(key, process.env.OC_SECRET));
}
