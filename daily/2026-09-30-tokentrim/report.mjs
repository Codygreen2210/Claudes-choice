const $ = (n) => '$' + (n >= 100 ? n.toFixed(0) : n.toFixed(2));
const pct = (a, b) => b ? Math.round((a / b) * 100) + '%' : '0%';
export function report(a, days = 1) {
  const month = (n) => $(n * (30 / days));
  const L = [`# TokenTrim report`, '', `${a.calls} calls over ${days} day(s), costing ${$(a.total)} (about ${month(a.total)}/month at this pace).`, ''];
  if (a.unknownModels.length) L.push(`Not priced (add to prices.mjs): ${a.unknownModels.join(', ')}`, '');
  L.push('## Where the money leaks', '', '| Fix | Saves | Share of bill | Effort |', '|---|---|---|---|');
  L.push(`| Turn on prompt caching for repeated openings | ${month(a.prefixSave)}/mo | ${pct(a.prefixSave, a.total)} | One setting or one line per call |`);
  L.push(`| Cache exact repeat questions | ${month(a.duplicates.save)}/mo | ${pct(a.duplicates.save, a.total)} | Small cache in front of the API |`);
  L.push(`| Try a cheaper model on short answers | up to ${month(a.downSave)}/mo | ${pct(a.downSave, a.total)} | Test quality first |`, '');
  if (a.prefixes.length) { L.push('## Repeated openings (best first)', ''); for (const p of a.prefixes.slice(0, 5)) L.push(`- ${p.model}: ${p.calls} calls share ~${p.tokens} tokens ("${p.preview}…") — saves ${month(p.save)}/mo`); L.push(''); }
  if (a.duplicates.groups) L.push(`## Exact repeats`, '', `${a.duplicates.extraCalls} calls asked something already asked (${a.duplicates.groups} distinct questions).`, '');
  if (a.downgrades.length) { L.push('## Cheaper-model candidates', ''); for (const d of a.downgrades) L.push(`- ${d.calls} short ${d.from} calls → try ${d.to}: up to ${month(d.save)}/mo`); L.push(''); }
  L.push('Savings are estimates from your own logs and the prices in prices.mjs. Cheaper-model savings only hold if quality holds, so test first. Overlapping fixes don\'t fully add up.');
  return L.join('\n');
}
