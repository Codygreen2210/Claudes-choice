import type { Ev } from '../lib/types.ts';
import { profileStats } from '../lib/game.ts';
import { KINDS, fmtTokens, fmtDollars, PRICES_AS_OF } from '../lib/cost.ts';

const kindLabel = (k?: string) => KINDS[k as keyof typeof KINDS]?.label || k || 'Other';

export default function Profile({ handle, events, showSearches = true }: { handle: string; events: Ev[]; showSearches?: boolean }) {
  const s = profileStats(events);
  const misses = events.filter((e) => e.type === 'miss');
  const searches = events.filter((e) => e.type === 'search');
  const pct = Math.round((s.level.into / s.level.need) * 100);
  return (
    <div>
      <h1 style={{ fontSize: 34 }}>{handle}</h1>
      <p className="note">Level {s.level.level} · {s.xp} XP · {s.streak}-day streak</p>
      <div className="bar" aria-label={`${pct}% to next level`}><i style={{ width: pct + '%' }} /></div>
      <div className="grid" style={{ marginTop: 16 }}>
        <div className="card stat"><b>{s.misses}</b><span>mistakes logged</span></div>
        <div className="card stat"><b>{s.misses ? Math.round((s.fixed / s.misses) * 100) : 0}%</b><span>with a fix</span></div>
        <div className="card stat"><b>{fmtTokens(s.tokens)}</b><span>tokens burned (est.)</span></div>
        <div className="card stat"><b>{fmtDollars(s.dollars)}</b><span>cost (est.)</span></div>
        <div className="card stat"><b>{s.searches}</b><span>searches logged</span></div>
      </div>
      {s.badges.length > 0 && (<><h2>Badges</h2><div>{s.badges.map((b) => <span key={b.id} className="badge" title={b.why}>{b.name}</span>)}</div></>)}
      {s.byFamily.length > 0 && (<>
        <h2>By AI</h2>
        <div className="scroll"><table><thead><tr><th>AI</th><th className="n">Mistakes</th><th className="n">Tokens (est.)</th><th className="n">Cost (est.)</th></tr></thead>
          <tbody>{s.byFamily.map((f) => <tr key={f.family}><td>{f.family}</td><td className="n">{f.misses}</td><td className="n">{fmtTokens(f.tokens)}</td><td className="n">{fmtDollars(f.dollars)}</td></tr>)}</tbody></table></div>
      </>)}
      {s.byKind.length > 0 && (<>
        <h2>What kind</h2>
        <div className="scroll"><table><thead><tr><th>Kind</th><th className="n">Mistakes</th><th className="n">Tokens (est.)</th></tr></thead>
          <tbody>{s.byKind.map((k) => <tr key={k.kind}><td>{kindLabel(k.kind)}</td><td className="n">{k.misses}</td><td className="n">{fmtTokens(k.tokens)}</td></tr>)}</tbody></table></div>
      </>)}
      <h2>Mistakes</h2>
      {misses.length === 0 && <p className="note">Nothing yet. Once your AI is connected, it logs mistakes when you correct it.</p>}
      {misses.slice(0, 100).map((e) => (
        <div key={e.id} className="miss">
          <div className="meta">{e.created_at.slice(0, 10)} · {e.family} ({e.model}) · {kindLabel(e.kind)} · ~{fmtTokens(e.tokens)} tokens</div>
          {e.trying_to && <div><b>Trying to:</b> {e.trying_to}</div>}
          {e.ask && <div><b>Ask:</b> {e.ask}</div>}
          <div><b>Mistake:</b> {e.mistake}</div>
          {e.fix ? <div className="fix"><b>Fix:</b> {e.fix}</div> : <div className="note">No fix logged yet.</div>}
        </div>
      ))}
      {showSearches && searches.length > 0 && (<>
        <h2>Research</h2>
        <div className="scroll"><table><thead><tr><th>Date</th><th>AI</th><th>Topic</th><th className="n">Searches</th></tr></thead>
          <tbody>{searches.slice(0, 50).map((e) => <tr key={e.id}><td>{e.created_at.slice(0, 10)}</td><td>{e.family}</td><td>{e.topic}</td><td className="n">{e.searches}</td></tr>)}</tbody></table></div>
      </>)}
      <p className="note" style={{ marginTop: 24 }}>Token counts are the AI's own estimates (or a default by kind). Dollar costs use rough blended prices as of {PRICES_AS_OF}. Treat both as ballparks.</p>
    </div>
  );
}
