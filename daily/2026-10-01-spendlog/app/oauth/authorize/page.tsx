// What people see when they tap Connect in Claude: one tap to allow.
import { cookies } from 'next/headers';
import { randomBytes } from 'node:crypto';
import { getStore } from '../../../lib/store.ts';
import { checkAuthorize } from '../../../lib/oauth.ts';
export const dynamic = 'force-dynamic';
export const metadata = { title: 'Connect Spendlog', robots: { index: false } };

const input = { width: '100%', margin: '8px 0', padding: 12, fontSize: 16, borderRadius: 8, border: '1px solid var(--line)', background: 'var(--bg)', color: 'var(--ink)' } as const;

export default async function Authorize({ searchParams }: { searchParams: Promise<Record<string, string>> }) {
  const q = await searchParams;
  const store = await getStore();
  const chk = await checkAuthorize(store, q);
  if (!chk.ok) return (
    <main className="wrap"><h1 style={{ fontSize: 30 }}>Couldn't connect</h1><p className="lead">{chk.error}</p>
      {chk.redirect && <a className="btn ghost" href={chk.redirect}>Back to the app</a>}</main>
  );
  const consent = randomBytes(24).toString('base64url');
  await store.kvPut('consent', consent, chk.req, 600);
  const dash = (await cookies()).get('sl_dash')?.value;
  const me = dash ? await store.userByKey(dash) : null;
  const host = new URL(chk.req.redirect_uri).host;
  return (
    <main className="wrap" style={{ maxWidth: 520 }}>
      <h1 style={{ fontSize: 32 }}>Connect {chk.client.client_name} to Spendlog</h1>
      <p className="lead">It will be able to add what you spend and earn to your spending book, set budgets, and read your totals.</p>
      <form method="post" action="/api/oauth/approve">
        <input type="hidden" name="consent" value={consent} />
        {me && <button className="btn" name="choice" value="existing" style={{ width: '100%', marginBottom: 14 }}>Allow, use my book ({me.handle})</button>}
        <button className={me ? 'btn ghost' : 'btn'} name="choice" value="new" style={{ width: '100%', marginBottom: 14 }}>{me ? 'Start a new book instead' : 'Allow and start my book'}</button>
        <details className="card" style={{ marginBottom: 14 }}>
          <summary>Already have a book on another device?</summary>
          <label htmlFor="book">Paste your book link:</label>
          <input id="book" name="book" inputMode="url" autoComplete="off" placeholder="https://…/me/sl_…" style={input} />
          <button className="btn ghost" name="choice" value="link" style={{ width: '100%' }}>Allow, use that book</button>
        </details>
        <p style={{ textAlign: 'center' }}><button className="btn ghost" name="choice" value="deny">Cancel</button></p>
      </form>
      <p className="note">By allowing, you confirm you're 18 or older. No bank login, ever: Spendlog only knows what you tell it. You'll be sent back to <b>{host}</b>. <a href="/privacy">Privacy</a></p>
    </main>
  );
}
