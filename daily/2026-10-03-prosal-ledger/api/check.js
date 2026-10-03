// GET /api/check?key=PL1....  ->  { ok, name, exp } or { ok: false, reason }
// The app asks this when it opens. Only the key is sent. Production and pay
// numbers never leave the browser.
import { readKey } from '../lib/license.mjs';

export default function handler(req, res) {
  const key = new URL(req.url, 'http://x').searchParams.get('key');
  res.setHeader('Cache-Control', 'no-store');
  if (!process.env.PL_SECRET) return res.status(503).json({ ok: false, reason: 'Licensing is not set up yet.' });
  res.status(200).json(readKey(key, process.env.PL_SECRET));
}
