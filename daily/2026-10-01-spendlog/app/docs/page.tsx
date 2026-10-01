import { headers } from 'next/headers';
import { CONTACT, contactLink } from '../../lib/site.ts';
import { TOOLS } from '../../lib/mcp.ts';
export const metadata = { title: 'How to use Spendlog' };
export default async function Docs() {
  const h = await headers();
  const origin = `${h.get('x-forwarded-proto') || 'https'}://${h.get('host')}`;
  return (
    <main className="wrap" style={{ maxWidth: 720 }}>
      <h1 style={{ fontSize: 36 }}>How to use Spendlog</h1>
      <p className="lead">Spendlog is a spending book inside Claude. Tell Claude what you spent or earned, set monthly budgets by category, and ask for your totals. It never connects to your bank.</p>
      <h2>Connect Claude</h2>
      <ol>
        <li>On claude.ai, go to <b>Settings → Connectors → Add custom connector</b>.</li>
        <li>Name: <b>Spendlog</b>. URL: <code>{origin}/api/mcp</code></li>
        <li>Tap <b>Add</b>, then <b>Connect</b>, then <b>Allow</b>. Allowing creates your book.</li>
        <li>Works on web, desktop and the Claude phone app.</li>
      </ol>
      <h2>Try it</h2>
      <ul>
        <li>“$42.18 groceries at Walmart” logs spending.</li>
        <li>“Got paid $1,250 on the 15th” logs income.</li>
        <li>“Set my gas budget to $200” sets a monthly budget.</li>
        <li>“How am I doing this month?” shows totals by category against budgets.</li>
        <li>“Show my last 10 entries” then “delete the second one” fixes mistakes.</li>
      </ul>
      <h2>Tools</h2>
      <ul>{TOOLS.map((t) => <li key={t.name}><b>{t.title}</b> (<code>{t.name}</code>): {t.description}</li>)}</ul>
      <h2>See your book</h2>
      <p>After connecting, open <a href="/">{origin.replace(/^https?:\/\//, '')}</a> in the same browser and tap <b>Open your spending book</b>. Bookmark that page. It has monthly totals, category bars against budgets, every entry, a spreadsheet download, and <b>Delete my book</b>.</p>
      <h2>What it isn't</h2>
      <p>Spendlog records and adds up numbers. It doesn't give financial, tax or investment advice, and it can't move money.</p>
      <h2>Help</h2>
      <p>{CONTACT ? <a href={contactLink()}>{CONTACT}</a> : 'See the home page.'} · <a href="/privacy">Privacy policy</a></p>
    </main>
  );
}
