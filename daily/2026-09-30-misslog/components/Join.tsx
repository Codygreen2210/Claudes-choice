'use client';
import { useState } from 'react';

export default function Join() {
  const [state, setState] = useState<{ key: string; handle: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [copied, setCopied] = useState(false);
  const origin = typeof window !== 'undefined' ? window.location.origin : '';
  async function go() {
    setBusy(true); setErr('');
    try {
      const r = await fetch('/api/join', { method: 'POST' });
      const j = await r.json();
      if (!r.ok) throw new Error(j.error || 'Something went wrong.');
      setState(j);
    } catch (e: any) { setErr(e.message); } finally { setBusy(false); }
  }
  if (!state) return (
    <div>
      <button className="btn" onClick={go} disabled={busy}>{busy ? 'Making your link…' : 'Get my link'}</button>
      {err && <p style={{ color: 'var(--accent)' }}>{err}</p>}
      <p className="note">No sign-up. Your link is your journal; keep it to yourself like a key.</p>
    </div>
  );
  const link = `${origin}/api/mcp/${state.key}`;
  const copy = async () => { await navigator.clipboard.writeText(link); setCopied(true); setTimeout(() => setCopied(false), 1500); };
  return (
    <div className="card">
      <b>Your journal: {state.handle}</b>
      <p style={{ margin: '8px 0' }}>Paste this link into your AI as a connector:</p>
      <div className="link">{link}</div>
      <p><button className="btn" onClick={copy}>{copied ? 'Copied' : 'Copy link'}</button>{' '}
        <a className="btn ghost" href={`/me/${state.key}`}>Open my dashboard</a></p>
      <details open><summary>Claude</summary><p>Settings → Connectors → Add custom connector → paste the link.</p></details>
      <details><summary>ChatGPT</summary><p>Settings → Connectors → turn on Developer mode → Create → paste the link.</p></details>
      <details><summary>Cursor</summary><p>Add to <code>~/.cursor/mcp.json</code>: <code>{`{"mcpServers":{"misslog":{"url":"${link}"}}}`}</code></p></details>
      <details><summary>Gemini CLI</summary><p>Add to <code>~/.gemini/settings.json</code>: <code>{`{"mcpServers":{"misslog":{"httpUrl":"${link}"}}}`}</code></p></details>
      <p className="note">Bookmark your dashboard link; it's the only way back in.</p>
    </div>
  );
}
