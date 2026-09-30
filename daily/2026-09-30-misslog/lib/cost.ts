// What a mistake cost, in tokens and dollars. These are ESTIMATES and are labeled that way everywhere.
// Tokens: the model's own estimate of the tokens spent on the wrong path (capped), or a default by kind.
// Dollars: tokens x a blended price per million tokens for the model family (mostly output-heavy rework).
// Prices change; this table is dated so nobody mistakes it for a live quote. Edit it here.
export const PRICES_AS_OF = '2026-09';

export const KINDS = {
  guess: { label: 'Guessed instead of checking', tokens: 3000 },
  misread: { label: 'Misread the ask', tokens: 15000 },
  wrong_fix: { label: 'Fix that did not fix it', tokens: 8000 },
  unverified: { label: 'Said done without checking', tokens: 6000 },
  broke_something: { label: 'Broke something that worked', tokens: 20000 },
  overbuilt: { label: 'Built more than was asked', tokens: 25000 },
  made_up: { label: 'Made something up', tokens: 5000 },
  other: { label: 'Other', tokens: 5000 },
} as const;
export type Kind = keyof typeof KINDS;
export const isKind = (k: unknown): k is Kind => typeof k === 'string' && k in KINDS;

// Blended $ per 1M tokens by family. Rough on purpose.
const FAMILY_PRICE: [RegExp, number, string][] = [
  [/opus|mythos|fable/, 30, 'Claude (large)'],
  [/sonnet/, 9, 'Claude (mid)'],
  [/haiku/, 3, 'Claude (small)'],
  [/claude/, 9, 'Claude'],
  [/gpt-?5|o[134]\b|o\d-|gpt-?4\.?1|gpt-?4o/, 8, 'ChatGPT'],
  [/gpt|chatgpt|openai/, 8, 'ChatGPT'],
  [/gemini.*(flash|lite)/, 2, 'Gemini (fast)'],
  [/gemini/, 8, 'Gemini'],
  [/grok/, 10, 'Grok'],
  [/deepseek/, 1.5, 'DeepSeek'],
  [/llama|mistral|qwen/, 1, 'Open model'],
];

// Group raw model names into a leaderboard name, e.g. "claude-opus-5-5" -> "Claude".
export function modelFamily(raw: unknown): string {
  const m = String(raw ?? '').toLowerCase();
  if (/claude|opus|sonnet|haiku|mythos|fable/.test(m)) return 'Claude';
  if (/gpt|chatgpt|openai|\bo[134]\b/.test(m)) return 'ChatGPT';
  if (/gemini|bard/.test(m)) return 'Gemini';
  if (/grok/.test(m)) return 'Grok';
  if (/deepseek/.test(m)) return 'DeepSeek';
  if (/llama|meta/.test(m)) return 'Llama';
  if (/mistral/.test(m)) return 'Mistral';
  if (/qwen/.test(m)) return 'Qwen';
  return 'Other';
}

export function cleanModel(raw: unknown): string {
  return String(raw ?? 'unknown').toLowerCase().replace(/[^a-z0-9.\- ]/g, '').trim().slice(0, 48) || 'unknown';
}

export function pricePerMillion(model: string): number {
  const m = model.toLowerCase();
  for (const [re, p] of FAMILY_PRICE) if (re.test(m)) return p;
  return 5;
}

export const MAX_TOKENS = 200_000;
export function estimateTokens(kind: Kind, given?: unknown): number {
  const n = Number(given);
  if (Number.isFinite(n) && n > 0) return Math.min(MAX_TOKENS, Math.round(n));
  return KINDS[kind].tokens;
}

export function estimateDollars(model: string, tokens: number): number {
  return Math.round((tokens / 1_000_000) * pricePerMillion(model) * 10000) / 10000;
}

export const fmtTokens = (n: number) => (n >= 1e6 ? (n / 1e6).toFixed(1) + 'M' : n >= 1e3 ? (n / 1e3).toFixed(1) + 'K' : String(n));
export const fmtDollars = (n: number) => (n < 0.01 && n > 0 ? '<$0.01' : '$' + n.toFixed(2));
