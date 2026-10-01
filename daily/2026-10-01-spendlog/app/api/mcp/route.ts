// The one connector address for everyone: https://<site>/api/mcp
// No token -> 401 pointing at our sign-in metadata, which is how Claude knows to show "Connect".
import { getStore } from '../../../lib/store.ts';
import { fromBearer } from '../../../lib/oauth.ts';
import { originOf } from '../../../lib/origin.ts';
import { CORS, rpcResponse } from '../../../lib/mcpHttp.ts';
export const dynamic = 'force-dynamic';

const unauthorized = (req: Request) => new Response(JSON.stringify({ error: 'unauthorized', error_description: 'Sign in to Spendlog to connect.' }), {
  status: 401,
  headers: { ...CORS, 'content-type': 'application/json', 'WWW-Authenticate': `Bearer resource_metadata="${originOf(req)}/.well-known/oauth-protected-resource/api/mcp", scope="spending"` },
});

export async function OPTIONS() { return new Response(null, { status: 204, headers: CORS }); }
export async function DELETE() { return new Response(null, { status: 204, headers: CORS }); }
export async function GET(req: Request) {
  if ((req.headers.get('accept') || '').includes('text/html')) return Response.redirect(`${originOf(req)}/docs`, 302);
  return new Response('Spendlog MCP: POST JSON-RPC here.', { status: 405, headers: { ...CORS, Allow: 'POST' } });
}
export async function POST(req: Request) {
  const ctx = await fromBearer(await getStore(), req.headers.get('authorization'));
  if (!ctx) return unauthorized(req);
  return rpcResponse(req, ctx, ctx.user.id);
}
