// Game rules: XP, levels, badges and streaks, all computed from a person's events.
import type { Ev } from './types.ts';

export const XP = { miss: 10, fix: 15, search: 2 };

export function xpFor(events: Ev[]): number {
  let xp = 0;
  for (const e of events) {
    if (e.type === 'miss') xp += XP.miss + (e.fix ? XP.fix : 0);
    else if (e.type === 'search') xp += XP.search;
  }
  return xp;
}

export function level(xp: number) {
  // each level needs 50 more XP than the last: 100, 150, 200...
  let lvl = 1, need = 100, left = xp;
  while (left >= need) { left -= need; lvl++; need += 50; }
  return { level: lvl, into: left, need };
}

const day = (iso: string) => iso.slice(0, 10);
export function streak(events: Ev[], today = new Date()): number {
  const days = new Set(events.map((e) => day(e.created_at)));
  let n = 0;
  const d = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate()));
  if (!days.has(d.toISOString().slice(0, 10))) d.setUTCDate(d.getUTCDate() - 1); // today not logged yet doesn't break it
  while (days.has(d.toISOString().slice(0, 10))) { n++; d.setUTCDate(d.getUTCDate() - 1); }
  return n;
}

export type Badge = { id: string; name: string; why: string };
export function badges(events: Ev[]): Badge[] {
  const misses = events.filter((e) => e.type === 'miss');
  const fixed = misses.filter((e) => e.fix);
  const fams = new Set(events.map((e) => e.family));
  const out: Badge[] = [];
  if (misses.length >= 1) out.push({ id: 'first', name: 'First Catch', why: 'Logged a first mistake' });
  if (fixed.length >= 10) out.push({ id: 'owned', name: 'Owned It', why: '10 mistakes logged with a fix' });
  if (misses.length >= 50) out.push({ id: 'ledger', name: 'Ledger Keeper', why: '50 mistakes logged' });
  if (misses.some((e) => e.tokens >= 50_000)) out.push({ id: 'bigone', name: 'The Big One', why: 'One mistake burned 50K+ tokens' });
  if (fams.size >= 3) out.push({ id: 'poly', name: 'Model Hopper', why: 'Logged from 3 or more AI families' });
  if (streak(events) >= 3) out.push({ id: 'streak3', name: 'On a Roll', why: '3-day logging streak' });
  if (events.filter((e) => e.type === 'search').length >= 25) out.push({ id: 'digger', name: 'Digger', why: '25 research sessions logged' });
  return out;
}

export type ProfileStats = {
  misses: number; fixed: number; searches: number; tokens: number; dollars: number;
  xp: number; level: ReturnType<typeof level>; streak: number; badges: Badge[];
  byFamily: { family: string; misses: number; tokens: number; dollars: number }[];
  byKind: { kind: string; misses: number; tokens: number }[];
};

export function profileStats(events: Ev[]): ProfileStats {
  const misses = events.filter((e) => e.type === 'miss');
  const fam = new Map<string, { family: string; misses: number; tokens: number; dollars: number }>();
  const kind = new Map<string, { kind: string; misses: number; tokens: number }>();
  let searches = 0;
  for (const e of events) {
    if (e.type === 'search') { searches += e.searches || 1; continue; }
    const f = fam.get(e.family) || { family: e.family, misses: 0, tokens: 0, dollars: 0 };
    f.misses++; f.tokens += e.tokens; f.dollars += e.dollars; fam.set(e.family, f);
    const k = kind.get(e.kind || 'other') || { kind: e.kind || 'other', misses: 0, tokens: 0 };
    k.misses++; k.tokens += e.tokens; kind.set(k.kind, k);
  }
  const xp = xpFor(events);
  return {
    misses: misses.length, fixed: misses.filter((e) => e.fix).length, searches,
    tokens: misses.reduce((a, e) => a + e.tokens, 0), dollars: misses.reduce((a, e) => a + e.dollars, 0),
    xp, level: level(xp), streak: streak(events), badges: badges(events),
    byFamily: [...fam.values()].sort((a, b) => b.misses - a.misses),
    byKind: [...kind.values()].sort((a, b) => b.misses - a.misses),
  };
}

export type BoardRow = { family: string; misses: number; fixed: number; tokens: number; dollars: number; searches: number; people: number };
// Leaderboard per AI family. Sorted by fix rate (owning mistakes is the point), then fewest tokens burned per miss.
export function board(events: Ev[]): BoardRow[] {
  const m = new Map<string, BoardRow & { users: Set<string> }>();
  for (const e of events) {
    const r = m.get(e.family) || { family: e.family, misses: 0, fixed: 0, tokens: 0, dollars: 0, searches: 0, people: 0, users: new Set<string>() };
    r.users.add(e.user_id);
    if (e.type === 'search') r.searches += e.searches || 1;
    else { r.misses++; if (e.fix) r.fixed++; r.tokens += e.tokens; r.dollars += e.dollars; }
    m.set(e.family, r);
  }
  return [...m.values()].map(({ users, ...r }) => ({ ...r, people: users.size }))
    .sort((a, b) => (b.misses ? b.fixed / b.misses : 0) - (a.misses ? a.fixed / a.misses : 0) || (a.misses ? a.tokens / a.misses : 0) - (b.misses ? b.tokens / b.misses : 0));
}
