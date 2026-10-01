import { notFound } from 'next/navigation';
import { getStore } from '../../../lib/store.ts';
import { summarize, money, monthLabel, cleanMonth, thisMonth } from '../../../lib/money.ts';
import DeleteBook from '../../../components/DeleteBook.tsx';
export const dynamic = 'force-dynamic';
export const metadata = { robots: { index: false } };

function shift(m: string, by: number) { const [y, mo] = m.split('-').map(Number); const d = new Date(Date.UTC(y, mo - 1 + by, 15)); return d.toISOString().slice(0, 7); }

export default async function Book({ params, searchParams }: { params: Promise<{ key: string }>; searchParams: Promise<{ m?: string }> }) {
  const { key } = await params;
  const store = await getStore();
  const u = await store.userByKey(key);
  if (!u) notFound();
  const month = cleanMonth((await searchParams).m);
  const [entries, budgets] = await Promise.all([store.entries(u.id, { month }), store.budgets(u.id)]);
  const s = summarize(entries, budgets, month);
  const top = Math.max(1, ...s.categories.map((c) => Math.max(c.spent, c.budget || 0)));
  return (
    <main className="wrap">
      <p className="note">Your spending book · {u.handle}</p>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        <a className="btn ghost" href={`?m=${shift(month, -1)}`} aria-label="Previous month">←</a>
        <h1 style={{ fontSize: 30, margin: 0 }}>{monthLabel(month)}</h1>
        {month < thisMonth() && <a className="btn ghost" href={`?m=${shift(month, 1)}`} aria-label="Next month">→</a>}
      </div>
      <div className="grid" style={{ marginTop: 16 }}>
        <div className="card stat"><b>{money(s.spent)}</b><span>spent</span></div>
        <div className="card stat"><b>{money(s.income)}</b><span>came in</span></div>
        <div className="card stat"><b className={s.net < 0 ? 'bad' : ''}>{s.net < 0 ? '-' : ''}{money(Math.abs(s.net))}</b><span>{s.net < 0 ? 'short' : 'left over'}</span></div>
        {s.budgeted > 0 && <div className="card stat"><b>{money(s.budgeted)}</b><span>budgeted</span></div>}
      </div>

      <h2>By category</h2>
      {s.categories.length === 0 ? <p className="note">Nothing yet. In Claude, try “$12 lunch” or “set my groceries budget to $400”.</p> : s.categories.map((c) => (
        <div key={c.category} style={{ margin: '12px 0' }}>
          <div className="catrow">
            <b style={{ textTransform: 'capitalize' }}>{c.category}</b>
            <span>{money(c.spent)}{c.budget !== null && <> of {money(c.budget)} · <span className={c.left! < 0 ? 'bad' : ''}>{c.left! < 0 ? money(-c.left!) + ' over' : money(c.left!) + ' left'}</span></>}</span>
          </div>
          <div className={'bar' + (c.left !== null && c.left < 0 ? ' over' : '')} role="img" aria-label={`${c.category}: ${money(c.spent)}${c.budget !== null ? ' of ' + money(c.budget) : ''}`}><i style={{ width: Math.min(100, (c.spent / (c.budget || top)) * 100) + '%' }} /></div>
        </div>
      ))}

      <h2>Entries</h2>
      {entries.length === 0 ? <p className="note">No entries this month.</p> : (
        <div className="scroll"><table>
          <thead><tr><th>Date</th><th>Category</th><th>Note</th><th className="n">Amount</th></tr></thead>
          <tbody>{entries.map((e) => <tr key={e.id}><td>{e.day.slice(5)}</td><td style={{ textTransform: 'capitalize' }}>{e.category}</td><td>{e.note}</td><td className={'n' + (e.kind === 'income' ? '' : '')}>{e.kind === 'income' ? '+' : '-'}{money(e.cents)}</td></tr>)}</tbody>
        </table></div>
      )}
      <p style={{ marginTop: 20, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        <a className="btn ghost" href={`/api/me/${u.key}/csv`}>Download everything (spreadsheet)</a>
      </p>
      <p className="note">Bookmark this page; it's your book. Anyone with this link can see it, so keep it to yourself.</p>
      <DeleteBook k={u.key} />
    </main>
  );
}
