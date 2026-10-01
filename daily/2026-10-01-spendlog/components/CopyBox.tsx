'use client';
import { useState } from 'react';
export default function CopyBox({ text }: { text: string }) {
  const [done, setDone] = useState(false);
  return (
    <div style={{ display: 'flex', gap: 8, alignItems: 'stretch', flexWrap: 'wrap' }}>
      <div className="link" style={{ flex: '1 1 220px' }}>{text}</div>
      <button className="btn" onClick={async () => { try { await navigator.clipboard.writeText(text); setDone(true); setTimeout(() => setDone(false), 1500); } catch { /* long-press fallback */ } }}>{done ? 'Copied' : 'Copy'}</button>
    </div>
  );
}
