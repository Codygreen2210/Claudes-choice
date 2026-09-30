// One click: makes a journal and hands back its link. No sign-up.
import { getStore } from '../../../lib/store.ts';
import { allow } from '../../../lib/limit.ts';
export const dynamic = 'force-dynamic';
export async function POST(req: Request) {
  const ip = (req.headers.get('x-forwarded-for') || 'local').split(',')[0].trim();
  if (!allow('join:' + ip, 5, 60 * 60_000)) return Response.json({ error: 'Too many new journals from here. Try again in an hour.' }, { status: 429 });
  const u = await (await getStore()).createUser();
  return Response.json({ key: u.key, handle: u.handle });
}
