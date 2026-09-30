// Vercel function: POST /api/ai. Deploy the launchreel folder with these env vars:
//   ANTHROPIC_API_KEY, LAUNCHREEL_PUBLIC_KEY (from tools/keygen.mjs init),
//   SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, optional LAUNCHREEL_AI_MONTHLY_CAP (default 50).
// Run hosted/supabase.sql once in the Supabase SQL editor.
import { handle, supabaseUsage } from '../../lib/ai-proxy.mjs';

export default async function (req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'POST only' });
  const ip = String(req.headers['x-forwarded-for'] || '').split(',')[0].trim() || 'unknown';
  const usage = supabaseUsage({ url: process.env.SUPABASE_URL, serviceKey: process.env.SUPABASE_SERVICE_ROLE_KEY });
  const [status, body] = await handle(req.body, { ip, usage });
  res.status(status).json(body);
}
