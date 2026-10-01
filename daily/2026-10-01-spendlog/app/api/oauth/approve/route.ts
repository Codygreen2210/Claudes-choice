// The consent form posts here. It only works with a consent id the page itself issued,
// and only from this site, so another site can't trick someone into approving.
import { getStore } from '../../../../lib/store.ts';
import { approve, type AuthReq } from '../../../../lib/oauth.ts';
import { originOf } from '../../../../lib/origin.ts';
export const dynamic = 'force-dynamic';
export async function POST(req: Request) {
  const origin = originOf(req);
  const from = req.headers.get('origin');
  if (from && from !== origin) return new Response('Bad origin', { status: 403 });
  const f = Object.fromEntries(new URLSearchParams(await req.text()));
  const store = await getStore();
  const consent = await store.kvGet<AuthReq>('consent', String(f.consent || ''));
  if (!consent) return new Response('This sign-in page expired. Go back to your AI app and connect again.', { status: 400 });
  await store.kvDel('consent', String(f.consent)); // one use (put back below only if a pasted link was wrong)
  const back = new URL(consent.redirect_uri);
  if (consent.state) back.searchParams.set('state', consent.state);
  if (f.choice === 'deny') { back.searchParams.set('error', 'access_denied'); return Response.redirect(back.toString(), 303); }
  const cookie = /(?:^|;\s*)sl_dash=([^;]+)/.exec(req.headers.get('cookie') || '')?.[1];
  // "link": they pasted their dashboard link (or just the sl_ key) to use the book they already have.
  let dashKey = f.choice === 'existing' ? cookie : undefined;
  if (f.choice === 'link') {
    const k = /sl_[A-Za-z0-9_-]{10,}/.exec(String(f.book || ''))?.[0];
    if (!k || !(await store.userByKey(k))) {
      await store.kvPut('consent', String(f.consent), consent, 600); // let them try again
      return new Response(`<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><body style="font:17px system-ui;max-width:520px;margin:40px auto;padding:0 16px"><h2>That link didn't match a spending book</h2><p>Paste the dashboard link that looks like <code>…/me/sl_…</code>. Go back and try again.</p><p><a href="javascript:history.back()">Back</a></p>`, { status: 400, headers: { 'content-type': 'text/html; charset=utf-8' } });
    }
    dashKey = k;
  }
  const r = await approve(store, consent, { dashKey });
  return new Response(null, { status: 303, headers: { Location: r.redirect, 'Set-Cookie': `sl_dash=${r.user.key}; Path=/; Max-Age=31536000; HttpOnly; Secure; SameSite=Lax` } });
}
