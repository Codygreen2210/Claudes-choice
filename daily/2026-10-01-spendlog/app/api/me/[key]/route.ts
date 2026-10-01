// Owner actions; the book key in the URL proves it's theirs.
import { getStore } from '../../../../lib/store.ts';
import { allow } from '../../../../lib/limit.ts';
export const dynamic = 'force-dynamic';
export async function POST(req: Request, ctx: { params: Promise<{ key: string }> }) {
  const { key } = await ctx.params;
  if (!allow('me:' + key, 20)) return Response.json({ error: 'Slow down.' }, { status: 429 });
  const store = await getStore();
  const u = await store.userByKey(key);
  if (!u) return Response.json({ error: 'Unknown book.' }, { status: 404 });
  const b = await req.json().catch(() => ({}));
  if (b.delete === 'DELETE') {
    await store.deleteUser(u.id);
    return Response.json({ ok: true, deleted: true }, { headers: { 'Set-Cookie': 'sl_dash=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax' } });
  }
  return Response.json({ error: 'Nothing to do.' }, { status: 400 });
}
