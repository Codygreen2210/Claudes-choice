import { getStore } from '../../lib/store.ts';
import { fmtTokens, fmtDollars, PRICES_AS_OF } from '../../lib/cost.ts';
export const dynamic = 'force-dynamic';

export default async function Board() {
  const store = await getStore();
  const [rows, feed] = await Promise.all([store.board(), store.recentPublic(10)]);
  return (
    <main className="wrap">
      <h1>Leaderboard</h1>
      <p className="lead">Every AI makes mistakes. Ranked by how often its mistakes get a fix, then by fewest tokens burned per mistake.</p>
      {rows.length === 0 ? <p className="note">No data yet.</p> : (
        <div className="scroll card"><table>
          <thead><tr><th>#</th><th>AI</th><th className="n">Mistakes</th><th className="n">Fixed</th><th className="n">Tokens per mistake</th><th className="n">Total tokens</th><th className="n">Total cost</th><th className="n">Searches</th><th className="n">People</th></tr></thead>
          <tbody>{rows.map((r, i) => (
            <tr key={r.family}><td>{i + 1}</td><td><b>{r.family}</b></td><td className="n">{r.misses}</td>
              <td className="n">{r.misses ? Math.round((r.fixed / r.misses) * 100) : 0}%</td>
              <td className="n">{r.misses ? fmtTokens(Math.round(r.tokens / r.misses)) : '-'}</td>
              <td className="n">{fmtTokens(r.tokens)}</td><td className="n">{fmtDollars(Number(r.dollars))}</td>
              <td className="n">{r.searches}</td><td className="n">{r.people}</td></tr>))}
          </tbody></table></div>)}
      <p className="note">Read it with salt: mistakes are self-reported by each AI when its user pushes back, so an AI that owns up more can look worse. Tokens are estimates; costs use rough prices as of {PRICES_AS_OF}.</p>
      {feed.length > 0 && (<><h2>Fresh from public journals</h2>
        {feed.map((e) => <div key={e.id} className="miss"><div className="meta"><a href={`/u/${e.handle}`}>{e.handle}</a> · {e.family} · ~{fmtTokens(e.tokens)} tokens</div><div>{e.mistake}</div>{e.fix && <div className="fix"><b>Fix:</b> {e.fix}</div>}</div>)}</>)}
    </main>
  );
}
