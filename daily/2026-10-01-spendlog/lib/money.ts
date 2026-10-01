// Money and dates. Everything is whole cents; months are "YYYY-MM".
import type { Budget, Entry } from './types.ts';

export const MAX_CENTS = 10_000_000_00; // $10 million per line is plenty

// "$42", "42.5", "1,250.00", 42 -> cents. Returns null if it isn't a sensible positive amount.
export function toCents(v: unknown): number | null {
  const s = String(v ?? '').replace(/[$,\s]/g, '');
  if (!/^\d+(\.\d{1,2})?$/.test(s)) return null;
  const [w, f = ''] = s.split('.');
  const c = Number(w) * 100 + Number((f + '00').slice(0, 2));
  return c > 0 && c <= MAX_CENTS ? c : null;
}

export const money = (c: number) => (c < 0 ? '-' : '') + '$' + (Math.abs(c) / 100).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export function cleanCategory(v: unknown): string {
  const s = String(v ?? '').toLowerCase().replace(/[^a-z0-9 &'-]/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 30);
  return s || 'other';
}

const pad = (n: number) => String(n).padStart(2, '0');
export const today = (d = new Date()) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
export const thisMonth = (d = new Date()) => today(d).slice(0, 7);

// Accepts YYYY-MM-DD; anything else (or a far-off date) falls back to today.
export function cleanDay(v: unknown, now = new Date()): string {
  const s = String(v ?? '');
  if (!/^\d{4}-\d{2}-\d{2}$/.test(s)) return today(now);
  const t = Date.parse(s + 'T12:00:00Z');
  if (Number.isNaN(t) || Math.abs(t - now.getTime()) > 400 * 864e5) return today(now);
  return s;
}
export const cleanMonth = (v: unknown, now = new Date()) => (/^\d{4}-(0[1-9]|1[0-2])$/.test(String(v ?? '')) ? String(v) : thisMonth(now));

export type CategoryLine = { category: string; spent: number; budget: number | null; left: number | null };
export type MonthSummary = { month: string; spent: number; income: number; net: number; count: number; categories: CategoryLine[]; budgeted: number; over: string[] };

export function summarize(entries: Entry[], budgets: Budget[], month: string): MonthSummary {
  const inMonth = entries.filter((e) => e.day.startsWith(month));
  const spentBy = new Map<string, number>();
  let spent = 0, income = 0;
  for (const e of inMonth) {
    if (e.kind === 'income') income += e.cents;
    else { spent += e.cents; spentBy.set(e.category, (spentBy.get(e.category) || 0) + e.cents); }
  }
  const cats = new Set([...spentBy.keys(), ...budgets.map((b) => b.category)]);
  const budgetOf = new Map(budgets.map((b) => [b.category, b.cents]));
  const categories = [...cats].map((c) => {
    const s = spentBy.get(c) || 0, b = budgetOf.get(c) ?? null;
    return { category: c, spent: s, budget: b, left: b === null ? null : b - s };
  }).sort((a, b) => b.spent - a.spent || a.category.localeCompare(b.category));
  return {
    month, spent, income, net: income - spent, count: inMonth.length, categories,
    budgeted: budgets.reduce((a, b) => a + b.cents, 0),
    over: categories.filter((c) => c.left !== null && c.left < 0).map((c) => c.category),
  };
}

export function monthLabel(m: string) {
  const [y, mo] = m.split('-').map(Number);
  return new Date(Date.UTC(y, mo - 1, 15)).toLocaleString('en-US', { month: 'long', year: 'numeric', timeZone: 'UTC' });
}

export function toCsv(entries: Entry[]) {
  // Text cells that start like a formula (= + - @) get a leading ' so Excel won't run them.
  const q = (raw: string) => { const s = /^[=+\-@\t\r]/.test(raw) ? "'" + raw : raw; return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
  const rows = entries.slice().sort((a, b) => a.day.localeCompare(b.day)).map((e) => [e.day, e.kind, (e.kind === 'expense' ? '-' : '') + (e.cents / 100).toFixed(2), q(e.category), q(e.note)].join(','));
  return ['date,type,amount,category,note', ...rows].join('\n') + '\n';
}
