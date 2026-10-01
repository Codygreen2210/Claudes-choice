// Small in-memory rate limit (per server instance). Keeps one runaway agent from flooding a journal.
const hits = new Map<string, number[]>();
export function allow(id: string, max = 60, windowMs = 60_000): boolean {
  const t = Date.now(), arr = (hits.get(id) || []).filter((x) => t - x < windowMs);
  if (arr.length >= max) { hits.set(id, arr); return false; }
  arr.push(t); hits.set(id, arr);
  if (hits.size > 5000) for (const [k, v] of hits) if (!v.length || t - v[v.length - 1] > windowMs) hits.delete(k);
  return true;
}
