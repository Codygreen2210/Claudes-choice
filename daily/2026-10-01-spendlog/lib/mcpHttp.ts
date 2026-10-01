// Shared HTTP handling for both connector addresses:
//   /api/mcp        one address for everyone, signed in with OAuth (what the Claude directory uses)
import { getStore } from './store.ts';
import type { User } from './types.ts';
import { handleRpc } from './mcp.ts';
import { allow } from './limit.ts';

export const CORS = { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'content-type, mcp-protocol-version, mcp-session-id, authorization', 'Access-Control-Expose-Headers': 'www-authenticate', 'Access-Control-Allow-Methods': 'POST, OPTIONS' };

export async function rpcResponse(req: Request, ctx: { user: User }, limitId: string) {
  const json = (body: unknown, status = 200) => Response.json(body, { status, headers: CORS });
  if (!allow(limitId)) return json({ jsonrpc: '2.0', id: null, error: { code: -32000, message: 'Slow down: 60 calls a minute max.' } }, 429);
  const raw = await req.text();
  if (raw.length > 64_000) return json({ jsonrpc: '2.0', id: null, error: { code: -32600, message: 'Request too large.' } }, 413);
  let body: any;
  try { body = JSON.parse(raw); } catch { return json({ jsonrpc: '2.0', id: null, error: { code: -32700, message: 'Bad JSON.' } }, 400); }
  const store = await getStore();
  if (Array.isArray(body)) {
    const out = (await Promise.all(body.map((m) => handleRpc(m, ctx, store)))).filter(Boolean);
    return out.length ? json(out) : new Response(null, { status: 202, headers: CORS });
  }
  const res = await handleRpc(body, ctx, store);
  return res ? json(res) : new Response(null, { status: 202, headers: CORS });
}
