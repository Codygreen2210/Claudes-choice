// Owner settings: make the profile public, opt in to sharing anonymous totals.
import { getStore } from '../../../../lib/store.ts';
export const dynamic = 'force-dynamic';
export async function POST(req: Request, ctx: { params: Promise<{ key: string }> }) {
  const { key } = await ctx.params;
  const store = await getStore();
  const u = await store.userByKey(key);
  if (!u) return Response.json({ error: 'Unknown journal.' }, { status: 404 });
  const b = await req.json().catch(() => ({}));
  const patch: { public?: boolean; share_data?: boolean } = {};
  if (typeof b.public === 'boolean') patch.public = b.public;
  if (typeof b.share_data === 'boolean') patch.share_data = b.share_data;
  await store.updateUser(u.id, patch);
  return Response.json({ ok: true, ...patch });
}
