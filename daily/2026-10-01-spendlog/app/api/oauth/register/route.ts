// Dynamic Client Registration (RFC 7591). Claude falls back to this if it isn't using CIMD.
import { getStore } from '../../../../lib/store.ts';
import { registerClient } from '../../../../lib/oauth.ts';
import { allow } from '../../../../lib/limit.ts';
export const dynamic = 'force-dynamic';
export async function POST(req: Request) {
  const ip = (req.headers.get('x-forwarded-for') || 'local').split(',')[0].trim();
  if (!allow('reg:' + ip, 30, 60 * 60_000)) return Response.json({ error: 'slow_down' }, { status: 429 });
  const body = await req.json().catch(() => null);
  const c = await registerClient(await getStore(), body);
  if ('error' in c) return Response.json({ error: 'invalid_client_metadata', error_description: c.error }, { status: 400 });
  return Response.json({ client_id: c.client_id, client_name: c.client_name, redirect_uris: c.redirect_uris, token_endpoint_auth_method: 'none', grant_types: ['authorization_code', 'refresh_token'], response_types: ['code'] }, { status: 201 });
}
