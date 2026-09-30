// POST https://<site>/api/mcp/<key>  (MCP over HTTP, JSON responses)
import { getStore } from '../../../../lib/store.ts';
import { handleRpc } from '../../../../lib/mcp.ts';
import { allow } from '../../../../lib/limit.ts';

export const dynamic = 'force-dynamic';
const CORS = { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'content-type, mcp-protocol-version, mcp-session-id, authorization', 'Access-Control-Allow-Methods': 'POST, OPTIONS' };

export async function OPTIONS() { return new Response(null, { status: 204, headers: CORS }); }
export async function GET() { return new Response('Misslog MCP: POST JSON-RPC here.', { status: 405, headers: { ...CORS, Allow: 'POST' } }); }
export async function DELETE() { return new Response(null, { status: 204, headers: CORS }); }

export async function POST(req: Request, ctx: { params: Promise<{ key: string }> }) {
  const { key } = await ctx.params;
  const json = (body: unknown, status = 200) => Response.json(body, { status, headers: CORS });
  if (!allow(key)) return json({ jsonrpc: '2.0', id: null, error: { code: -32000, message: 'Slow down: 60 calls a minute max.' } }, 429);
  const raw = await req.text();
  if (raw.length > 64_000) return json({ jsonrpc: '2.0', id: null, error: { code: -32600, message: 'Request too large.' } }, 413);
  let body: any;
  try { body = JSON.parse(raw); } catch { return json({ jsonrpc: '2.0', id: null, error: { code: -32700, message: 'Bad JSON.' } }, 400); }
  const store = await getStore();
  const user = await store.userByKey(key);
  if (!user) return json({ jsonrpc: '2.0', id: body?.id ?? null, error: { code: -32001, message: 'Unknown journal link. Get a new one at the Misslog home page.' } }, 404);
  const client = req.headers.get('user-agent') || '';
  if (Array.isArray(body)) {
    const out = (await Promise.all(body.map((m) => handleRpc(m, user, store, client)))).filter(Boolean);
    return out.length ? json(out) : new Response(null, { status: 202, headers: CORS });
  }
  const res = await handleRpc(body, user, store, client);
  return res ? json(res) : new Response(null, { status: 202, headers: CORS });
}
