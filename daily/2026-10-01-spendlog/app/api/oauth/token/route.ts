// Token endpoint: code -> tokens (with PKCE), and refresh (rotating). Form-encoded, per RFC 6749.
import { getStore } from '../../../../lib/store.ts';
import { tokenGrant } from '../../../../lib/oauth.ts';
import { allow } from '../../../../lib/limit.ts';
export const dynamic = 'force-dynamic';
export async function POST(req: Request) {
  const ip = (req.headers.get('x-forwarded-for') || 'local').split(',')[0].trim();
  if (!allow('tok:' + ip, 60)) return Response.json({ error: 'slow_down' }, { status: 429 });
  const type = req.headers.get('content-type') || '';
  const raw = await req.text();
  let f: Record<string, string> = {};
  if (type.includes('json')) { try { f = JSON.parse(raw); } catch { /* empty */ } }
  else f = Object.fromEntries(new URLSearchParams(raw));
  const r = await tokenGrant(await getStore(), f);
  return Response.json(r.body, { status: r.status, headers: { 'Cache-Control': 'no-store', Pragma: 'no-cache' } });
}
