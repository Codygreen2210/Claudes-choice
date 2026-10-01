// Signed-in person sends their answers; gets their comparison back. Their answer joins the pay data.
import { backend, userFrom } from '../../../lib/store.ts';
import { cleanInput, compare } from '../../../lib/wages.ts';
import { allow } from '../../../lib/limit.ts';
export const dynamic = 'force-dynamic';

export async function POST(req: Request) {
  const user = await userFrom(req);
  if (!user) return Response.json({ error: 'Sign in to see your results.' }, { status: 401 });
  if (!allow('submit:' + user, 10)) return Response.json({ error: 'Slow down a little.' }, { status: 429 });
  const c = cleanInput(await req.json().catch(() => null));
  if (!c.ok) return Response.json({ error: c.error }, { status: 400 });
  const { store } = await backend();
  await store.save(user, c.input);
  return Response.json(compare(c.input, await store.community(c.input.occ, c.input.area)));
}

export async function DELETE(req: Request) {
  const user = await userFrom(req);
  if (!user) return Response.json({ error: 'Sign in first.' }, { status: 401 });
  await (await backend()).store.remove(user);
  return Response.json({ ok: true });
}
