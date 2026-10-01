import { cookies, headers } from 'next/headers';
import CopyBox from '../components/CopyBox.tsx';
import { getStore } from '../lib/store.ts';
export const dynamic = 'force-dynamic';

export default async function Home() {
  const h = await headers();
  const origin = `${h.get('x-forwarded-proto') || 'https'}://${h.get('host')}`;
  const dash = (await cookies()).get('sl_dash')?.value;
  const me = dash ? await (await getStore()).userByKey(dash) : null;
  return (
    <main className="wrap">
      {me && <div className="card" style={{ marginTop: 16 }}>Welcome back. <a href={`/me/${me.key}`}>Open your spending book</a>.</div>}
      <h1>Tell Claude what you spent.<br />It keeps your budget.</h1>
      <p className="lead">Spendlog is a spending book that lives inside Claude. Say “$42 at Walmart for groceries” and it's written down. Ask “how am I doing this month?” and you get the totals. No bank login, no app to open, no spreadsheet.</p>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>Add it to Claude</h2>
        <ol style={{ paddingLeft: 22 }}>
          <li>On <b>claude.ai</b>, open <b>Settings → Connectors → Add custom connector</b>.</li>
          <li>Name it <b>Spendlog</b> and paste this address:</li>
        </ol>
        <CopyBox text={`${origin}/api/mcp`} />
        <ol start={3} style={{ paddingLeft: 22 }}>
          <li>Tap <b>Add</b>, then <b>Connect</b>, then <b>Allow</b>. That's the whole sign-up.</li>
          <li>Works on web, desktop and the Claude phone app.</li>
        </ol>
      </div>

      <h2>Things to say</h2>
      <ul>
        <li>“$42.18 groceries at Walmart.”</li>
        <li>“Got paid $1,250.”</li>
        <li>“Set my eating out budget to $150 a month.”</li>
        <li>“How am I doing this month?”</li>
        <li>“That gas one was wrong, delete it.”</li>
      </ul>

      <h2>Why it's different</h2>
      <ul>
        <li><b>No bank login.</b> It only knows what you tell it.</li>
        <li><b>Nothing to open.</b> You're already talking to Claude; logging takes one sentence.</li>
        <li><b>Your numbers, your way.</b> See your book any time, download it as a spreadsheet, or delete it for good.</li>
      </ul>
      <p className="note">Spendlog tracks numbers; it doesn't give financial advice. For people 18 and older. <a href="/privacy">Privacy</a> · <a href="/docs">How to use</a></p>
    </main>
  );
}
