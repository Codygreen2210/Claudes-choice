// Dollars per million tokens. Check the provider's page before relying on these; edit here.
export const PRICES = {
  'gpt-4o': { in: 2.5, out: 10, cachedIn: 1.25 },
  'gpt-4o-mini': { in: 0.15, out: 0.6, cachedIn: 0.075 },
  'gpt-4.1': { in: 2, out: 8, cachedIn: 0.5 },
  'gpt-4.1-mini': { in: 0.4, out: 1.6, cachedIn: 0.1 },
  'claude-sonnet': { in: 3, out: 15, cachedIn: 0.3 },
  'claude-haiku': { in: 0.8, out: 4, cachedIn: 0.08 },
  'claude-opus': { in: 15, out: 75, cachedIn: 1.5 },
};
// A cheaper model in the same family, for short, simple calls.
export const CHEAPER = { 'gpt-4o': 'gpt-4o-mini', 'gpt-4.1': 'gpt-4.1-mini', 'claude-sonnet': 'claude-haiku', 'claude-opus': 'claude-sonnet' };
export function priceKey(model = '') {
  const m = model.toLowerCase();
  if (m.includes('claude')) return ['opus', 'sonnet', 'haiku'].map((f) => 'claude-' + f).find((k) => m.includes(k.slice(7))) || null;
  return Object.keys(PRICES).filter((k) => !k.startsWith('claude')).sort((a, b) => b.length - a.length).find((k) => m.startsWith(k)) || null;
}
