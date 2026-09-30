import { createHash } from 'node:crypto';
import { PRICES, CHEAPER, priceKey } from './prices.mjs';

const estTokens = (s) => Math.ceil((s || '').length / 4);
const textOf = (r) => typeof r.prompt === 'string' ? r.prompt
  : (r.messages || []).map((m) => `${m.role}:${typeof m.content === 'string' ? m.content : JSON.stringify(m.content)}`).join('\n');
const cost = (k, inT, outT) => k ? (inT * PRICES[k].in + outT * PRICES[k].out) / 1e6 : 0;

// rows: one object per logged API call: {model, messages|prompt, output?, input_tokens?, output_tokens?}
export function analyze(rows, { minPrefix = 1024, shortOut = 60 } = {}) {
  const calls = rows.map((r) => {
    const text = textOf(r); const k = priceKey(r.model);
    const inT = r.input_tokens ?? r.usage?.prompt_tokens ?? r.usage?.input_tokens ?? estTokens(text);
    const outT = r.output_tokens ?? r.usage?.completion_tokens ?? r.usage?.output_tokens ?? estTokens(r.output);
    return { model: r.model, k, text, inT, outT, cost: cost(k, inT, outT), hash: createHash('sha1').update(r.model + '\0' + text).digest('hex') };
  });
  const total = calls.reduce((s, c) => s + c.cost, 0);
  const unknownModels = [...new Set(calls.filter((c) => !c.k).map((c) => c.model))];

  // 1. Exact repeats: the same model + same input asked again. A response cache pays these once.
  const byHash = new Map();
  for (const c of calls) byHash.set(c.hash, [...(byHash.get(c.hash) || []), c]);
  const dupGroups = [...byHash.values()].filter((g) => g.length > 1);
  const dupSave = dupGroups.reduce((s, g) => s + g.slice(1).reduce((a, c) => a + c.cost, 0), 0);

  // 2. Shared opening text (system prompt, docs, tools) sent over and over: prompt caching bills it at the cached rate.
  const byStart = new Map();
  for (const c of calls) {
    if (!c.k) continue;
    const key = c.k + '\0' + c.text.slice(0, 200);
    byStart.set(key, [...(byStart.get(key) || []), c]);
  }
  const prefixes = [];
  for (const g of byStart.values()) {
    if (g.length < 2) continue;
    let p = g[0].text;
    for (const c of g) { let i = 0; while (i < p.length && i < c.text.length && p[i] === c.text[i]) i++; p = p.slice(0, i); }
    const pT = estTokens(p);
    if (pT < minPrefix) continue;
    const P = PRICES[g[0].k];
    const save = (g.length - 1) * pT * (P.in - P.cachedIn) / 1e6;
    prefixes.push({ model: g[0].k, calls: g.length, tokens: pT, save, preview: p.slice(0, 80).replace(/\s+/g, ' ') });
  }
  prefixes.sort((a, b) => b.save - a.save);
  const prefixSave = prefixes.reduce((s, p) => s + p.save, 0);

  // 3. Expensive model giving short answers: often a cheaper model does the same job. Flag, don't promise.
  const down = new Map();
  for (const c of calls) {
    const cheap = CHEAPER[c.k];
    if (!cheap || c.outT > shortOut) continue;
    const d = down.get(c.k) || { from: c.k, to: cheap, calls: 0, save: 0 };
    d.calls++; d.save += c.cost - cost(cheap, c.inT, c.outT); down.set(c.k, d);
  }
  const downgrades = [...down.values()].sort((a, b) => b.save - a.save);
  const downSave = downgrades.reduce((s, d) => s + d.save, 0);

  return { calls: calls.length, total, unknownModels,
    duplicates: { groups: dupGroups.length, extraCalls: dupGroups.reduce((s, g) => s + g.length - 1, 0), save: dupSave },
    prefixes, prefixSave, downgrades, downSave };
}
