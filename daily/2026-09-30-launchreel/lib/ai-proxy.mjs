// The hosted prompt-to-video service (for the seller to deploy, e.g. on Vercel). Guards against
// abuse and runaway cost:
//  - only valid Pro license keys (Ed25519, checked offline)
//  - a monthly cap per key (default 50 videos), counted atomically in Supabase
//  - a per-IP rate limit (5 a minute)
//  - small inputs only; the prompt is built here, so it can't be used as a general AI
//  - short answers (max_tokens 1500) and at most 2 AI calls per video
// Set a monthly spend limit in the Anthropic console too, so the worst case is capped there.
import { createHash } from 'node:crypto';
import { checkLicense } from './license.mjs';
import { promptToScript, anthropicCaller, cleanInventory } from './ai.mjs';

const hits = new Map(); // ip -> [timestamps]
export function rateLimited(ip, now = Date.now(), perMin = 5) {
  const list = (hits.get(ip) || []).filter((t) => now - t < 60000);
  if (list.length >= perMin) { hits.set(ip, list); return true; }
  list.push(now); hits.set(ip, list);
  if (hits.size > 5000) for (const [k, v] of hits) if (!v.some((t) => now - t < 60000)) hits.delete(k);
  return false;
}

// Atomic monthly counter in Supabase (see hosted/supabase.sql). Returns the new count, or null when over the cap.
export function supabaseUsage({ url, serviceKey, fetchImpl = fetch }) {
  return async (keyHash, month, cap) => {
    const r = await fetchImpl(`${url}/rest/v1/rpc/launchreel_use_ai`, {
      method: 'POST', headers: { apikey: serviceKey, authorization: `Bearer ${serviceKey}`, 'content-type': 'application/json' },
      body: JSON.stringify({ p_key: keyHash, p_month: month, p_cap: cap }),
    });
    if (!r.ok) throw new Error('usage store error ' + r.status);
    return r.json();
  };
}

export async function handle(body, { ip = '?', env = process.env, usage, call, now = new Date() } = {}) {
  if (rateLimited(ip, now.getTime())) return [429, { error: 'Too many requests. Wait a minute and try again.' }];
  const b = body && typeof body === 'object' ? body : {};
  const lic = checkLicense(b.licenseKey, env.LAUNCHREEL_PUBLIC_KEY || undefined);
  if (!lic) return [401, { error: 'Prompt-to-video needs a LaunchReel Pro key.' }];
  const prompt = String(b.prompt || '').trim();
  if (!prompt) return [400, { error: 'Describe the video you want first.' }];
  if (prompt.length > 600) return [400, { error: 'Keep the description under 600 characters.' }];
  if (JSON.stringify(b.inventory || {}).length > 20000) return [400, { error: 'That page list is too big.' }];
  let pageUrl;
  try { pageUrl = new URL(b.url).href; } catch { return [400, { error: 'Missing the app address.' }]; }
  const keyHash = createHash('sha256').update(String(b.licenseKey)).digest('hex').slice(0, 32);
  const month = now.toISOString().slice(0, 7);
  const cap = Number(env.LAUNCHREEL_AI_MONTHLY_CAP) || 50;
  const used = await usage(keyHash, month, cap);
  if (used == null) return [402, { error: `You've used all ${cap} AI videos for this month. It resets on the 1st.` }];
  try {
    const r = await promptToScript({ prompt, url: pageUrl, inv: cleanInventory(b.inventory), call: call || anthropicCaller({ apiKey: env.ANTHROPIC_API_KEY }), format: ['landscape', 'vertical', 'square'].includes(b.format) ? b.format : 'landscape' });
    return [200, { script: r.script, used, cap }];
  } catch (e) { return [422, { error: e.message, used, cap }]; }
}
