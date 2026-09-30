'use client';
import { useState } from 'react';
export default function Settings({ k, handle, pub, share, origin }: { k: string; handle: string; pub: boolean; share: boolean; origin: string }) {
  const [p, setP] = useState(pub), [s, setS] = useState(share);
  const save = async (patch: object) => { await fetch(`/api/me/${k}`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(patch) }); };
  return (
    <div className="card" style={{ marginTop: 16 }}>
      <b>Your connector link</b>
      <div className="link" style={{ margin: '8px 0' }}>{origin}/api/mcp/{k}</div>
      <label style={{ display: 'block', margin: '8px 0' }}><input type="checkbox" checked={p} onChange={(e) => { setP(e.target.checked); save({ public: e.target.checked }); }} /> Make my profile public{p && <> at <a href={`/u/${handle}`}>/u/{handle}</a></>}</label>
      <label style={{ display: 'block', margin: '8px 0' }}><input type="checkbox" checked={s} onChange={(e) => { setS(e.target.checked); save({ share_data: e.target.checked }); }} /> Share my anonymous totals for AI research reports (off by default; never your text)</label>
      <p className="note">Leaderboard totals always include your counts, never your words or your handle unless you go public.</p>
    </div>
  );
}
