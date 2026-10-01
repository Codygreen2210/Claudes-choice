'use client';
import { useEffect, useState } from 'react';
import { token, unpack } from '../lib/client.ts';
import type { Result } from '../lib/wages.ts';

const $ = (n: number) => '$' + n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const $0 = (n: number) => '$' + Math.round(n).toLocaleString('en-US');
const ord = (n: number) => n + (['th', 'st', 'nd', 'rd'][((n % 100) - 20) % 10] || ['th', 'st', 'nd', 'rd'][n % 100] || 'th');

export default function Results() {
  const [r, setR] = useState<Result | null>(null);
  const [err, setErr] = useState('');
  const [copied, setCopied] = useState(false);
  useEffect(() => {
    (async () => {
      const p = new URLSearchParams(location.search);
      const answers = unpack(p.get('a') || '');
      if (!answers) return setErr('Your answers didn\'t come through. Start again from the home page.');
      for (let i = 0; i < 10; i++) { // sign-in can take a moment to land after the redirect
        const t = await token();
        if (t) {
          const res = await fetch('/api/submit', { method: 'POST', headers: { 'content-type': 'application/json', authorization: 'Bearer ' + t }, body: JSON.stringify(answers) });
          const j = await res.json().catch(() => ({}));
          if (!res.ok) return setErr(j.error || 'Something went wrong.');
          history.replaceState(null, '', '/results');
          return setR(j);
        }
        await new Promise((ok) => setTimeout(ok, 300));
      }
      setErr('Sign-in didn\'t finish. Go back and try again.');
    })();
  }, []);
  if (err) return <div className="card"><p className="bad">{err}</p><a className="btn ghost" href="/">Start over</a></div>;
  if (!r) return <p className="lead">Lining up your numbers…</p>;
  const share = async () => {
    const text = 'See how your pay stacks up against your trade in your area. Takes a minute:';
    const url = location.origin;
    try { if (navigator.share) await navigator.share({ text, url }); else { await navigator.clipboard.writeText(text + ' ' + url); setCopied(true); } } catch { /* closed */ }
  };
  const pct = r.percentile;
  return (
    <div>
      <p className="note">{r.job} · {r.area}</p>
      {r.local && pct !== null ? (<>
        <h1 style={{ fontSize: 'clamp(30px,8vw,44px)' }}>You make more than about {pct}% of {r.job.toLowerCase().replace(/,.*$/, '')} here.</h1>
        <div className="scale" role="img" aria-label={`Your ${$(r.hourly)} lands around the ${ord(pct)} percentile`}>
          <div className="band" />
          <div className="you" style={{ left: `${Math.min(98, Math.max(2, pct))}%` }}><span>You<br />{$(r.hourly)}</span></div>
        </div>
        <div className="grid" style={{ marginTop: 18 }}>
          <div className="card stat"><b>{$(r.local.median)}</b><span>middle pay here (half make more)</span></div>
          <div className="card stat"><b className={r.vsMedian! < 0 ? 'bad' : 'good'}>{r.vsMedian! >= 0 ? '+' : '−'}{$(Math.abs(r.vsMedian!))}/hr</b><span>you vs. the middle</span></div>
          {r.local.p25 !== null && r.local.p75 !== null && <div className="card stat"><b>{$(r.local.p25)}–{$(r.local.p75)}</b><span>what most people here make</span></div>}
          {r.local.employment && <div className="card stat"><b>{r.local.employment.toLocaleString()}</b><span>people in this job here</span></div>}
        </div>
      </>) : <h1 style={{ fontSize: 32 }}>There's no government pay data for this job in this area yet.</h1>}

      {r.buysLike !== null && r.priceLevel !== null && (<>
        <h2>After the cost of living</h2>
        <p>Prices here run <b>{r.priceLevel < 100 ? `${(100 - r.priceLevel).toFixed(0)}% below` : `${(r.priceLevel - 100).toFixed(0)}% above`}</b> the U.S. average, so your {$(r.hourly)} buys what <b>{$(r.buysLike)}</b> buys in a typical U.S. town.</p>
        {r.usMedian !== null && r.vsUS !== null && <p>The middle pay for this job across the U.S. is about {$(r.usMedian)}. After prices, you're <b className={r.vsUS < 0 ? 'bad' : 'good'}>{$(Math.abs(r.vsUS))}/hr {r.vsUS >= 0 ? 'ahead' : 'behind'}</b>.</p>}
      </>)}

      <h2>Your year</h2>
      <p>At your hours, with overtime at time and a half, that's about <b>{$0(r.yearly)}</b> a year before taxes.</p>

      <h2>From people like you</h2>
      {r.community.median !== null
        ? <p>{r.community.count} people in this job and area have shared. Their middle pay: <b>{$(r.community.median)}</b>.</p>
        : <p>You're one of the first {r.community.count <= 1 ? '' : r.community.count + ' '}here. Real pay from people in your trade shows up once 5 people in this job and area have shared. Send it to your crew:</p>}
      <button className="btn" onClick={share} style={{ width: '100%' }}>{copied ? 'Link copied' : 'Share with your crew'}</button>

      <p className="note" style={{ marginTop: 22 }}>Pay ranges: U.S. Bureau of Labor Statistics, May 2024 (hourly, before overtime). Prices: U.S. Bureau of Economic Analysis, 2024. This is a comparison, not financial or legal advice.</p>
      <p className="note"><a href="/">Check another job</a> · <a href="/privacy">Your info</a></p>
    </div>
  );
}
