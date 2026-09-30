// Turn the changes across all watched stores into a morning digest:
// plain text for a terminal or email, and markdown for GitHub.
import { sortEvents } from './diff.mjs';

const HEAD = {
  price_down: 'Price cuts', sale_start: 'Sales started', price_up: 'Price raises',
  sold_out: 'Sold out', restock: 'Back in stock', sale_end: 'Sales ended',
  new: 'New products', removed: 'Removed',
};

export function summarize(results) {
  const total = results.reduce((n, r) => n + r.events.length, 0);
  const lines = [];
  lines.push(total ? `${total} change${total === 1 ? '' : 's'} across ${results.length} store${results.length === 1 ? '' : 's'} since yesterday.` : 'No changes at the stores you watch since yesterday.');
  return lines.join('\n');
}

export function toMarkdown(results, date = new Date().toISOString().slice(0, 10)) {
  const out = [`# RivalWatch — ${date}`, '', summarize(results), ''];
  for (const r of results) {
    const host = new URL(r.store).host;
    if (r.error) { out.push(`## ${host}`, '', `Could not check: ${r.error}`, ''); continue; }
    if (r.firstRun) { out.push(`## ${host}`, '', `Started watching ${r.count} products. Changes show up from tomorrow.`, ''); continue; }
    if (!r.events.length) { out.push(`## ${host}`, '', 'No changes.', ''); continue; }
    out.push(`## ${host} — ${r.events.length} change${r.events.length === 1 ? '' : 's'}`, '');
    let current = null;
    for (const e of sortEvents(r.events)) {
      if (e.type !== current) { if (current) out.push(''); current = e.type; out.push(`**${HEAD[e.type]}**`, ''); }
      out.push(`- ${e.text} — ${r.store}/products/${e.handle}`);
    }
    out.push('');
  }
  return out.join('\n');
}
