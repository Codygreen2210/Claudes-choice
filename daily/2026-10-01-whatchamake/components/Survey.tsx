'use client';
import { useState } from 'react';
import { signIn } from '../lib/client.ts';

type Opt = { id: string; label: string };
const field = { width: '100%', margin: '4px 0 14px', padding: 12, fontSize: 17, borderRadius: 8, border: '1px solid var(--line)', background: 'var(--card)', color: 'var(--ink)' } as const;

function Pick({ id, label, options, value, onChange, placeholder }: { id: string; label: string; options: Opt[]; value: string; onChange: (v: string) => void; placeholder: string }) {
  const [q, setQ] = useState('');
  const chosen = options.find((o) => o.id === value);
  const list = q ? options.filter((o) => o.label.toLowerCase().includes(q.toLowerCase())).slice(0, 8) : [];
  return (
    <div>
      <label htmlFor={id}><b>{label}</b></label>
      {chosen ? (
        <div className="picked"><span>{chosen.label}</span><button type="button" className="btn ghost" onClick={() => { onChange(''); setQ(''); }}>Change</button></div>
      ) : (<>
        <input id={id} style={field} value={q} onChange={(e) => setQ(e.target.value)} placeholder={placeholder} autoComplete="off" role="combobox" aria-expanded={list.length > 0} aria-controls={id + '-list'} />
        {list.length > 0 && <ul id={id + '-list'} role="listbox" className="choices">{list.map((o) => <li key={o.id} role="option" aria-selected="false"><button type="button" onClick={() => { onChange(o.id); setQ(''); }}>{o.label}</button></li>)}</ul>}
      </>)}
    </div>
  );
}

export default function Survey({ jobs, areas }: { jobs: Opt[]; areas: Opt[] }) {
  const [a, setA] = useState({ occ: '', area: '', hourly: '', hours: '40', otHours: '0', years: '' });
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);
  const set = (k: keyof typeof a) => (v: string) => setA({ ...a, [k]: v });
  async function go(e: React.FormEvent) {
    e.preventDefault();
    if (!a.occ) return setErr('Pick your job.');
    if (!a.area) return setErr('Pick your area.');
    const h = Number(a.hourly.replace(/[$,\s]/g, ''));
    if (!(h >= 5 && h <= 250)) return setErr('Enter your hourly pay, like 28.50.');
    setErr(''); setBusy(true);
    await signIn({ ...a, hourly: h });
  }
  return (
    <form onSubmit={go} className="card">
      <Pick id="job" label="Your job" options={jobs} value={a.occ} onChange={set('occ')} placeholder="Type it: electrician, welder, diesel…" />
      <Pick id="area" label="Where you work" options={areas} value={a.area} onChange={set('area')} placeholder="Type your city: Baton Rouge, Houston…" />
      <label htmlFor="hourly"><b>Your hourly pay</b> (before taxes)</label>
      <input id="hourly" style={field} inputMode="decimal" placeholder="$28.50" value={a.hourly} onChange={(e) => set('hourly')(e.target.value)} />
      <div className="two">
        <div><label htmlFor="hours"><b>Regular hours a week</b></label><input id="hours" style={field} inputMode="numeric" value={a.hours} onChange={(e) => set('hours')(e.target.value)} /></div>
        <div><label htmlFor="ot"><b>Overtime hours a week</b></label><input id="ot" style={field} inputMode="numeric" value={a.otHours} onChange={(e) => set('otHours')(e.target.value)} /></div>
      </div>
      <label htmlFor="years"><b>Years in the trade</b> <span className="note">(optional)</span></label>
      <input id="years" style={field} inputMode="numeric" value={a.years} onChange={(e) => set('years')(e.target.value)} />
      {err && <p className="bad" role="alert">{err}</p>}
      <button className="btn" style={{ width: '100%' }} disabled={busy}>{busy ? 'One sec…' : 'Sign in with Google to see where you stand'}</button>
      <p className="note">Signing in keeps it one answer per real person. Your name and email are never shown or shared; only your pay numbers join the count. <a href="/privacy">How your info is used</a></p>
    </form>
  );
}
