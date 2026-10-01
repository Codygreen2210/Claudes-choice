'use client';
export default function DeleteBook({ k }: { k: string }) {
  return (
    <details style={{ marginTop: 16 }}><summary>Delete my book</summary>
      <p className="note">Deletes every entry and budget. This can't be undone; Claude will be disconnected.</p>
      <button className="btn ghost" style={{ borderColor: 'var(--bad)', color: 'var(--bad)' }} onClick={async () => {
        if (window.prompt('Type DELETE to delete your book for good') !== 'DELETE') return;
        const r = await fetch(`/api/me/${k}`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ delete: 'DELETE' }) });
        if (r.ok) window.location.href = '/';
      }}>Delete my book</button>
    </details>
  );
}
