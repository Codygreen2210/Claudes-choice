// The comparison: where someone's pay lands among others in the same job and metro (BLS OEWS),
// what it's worth after local prices (BEA price parities), and the yearly estimate with overtime.
// Numbers only, no advice.
import data from '../data/wages.json' with { type: 'json' };

type Row = [number | null, number | null, number, number | null, number | null, number | null]; // p10,p25,median,p75,p90,employment
const D = data as unknown as { source: string; occupations: Record<string, string>; areas: Record<string, { name: string; state: string; rpp: number | null }>; wages: Record<string, Record<string, Row>> };
export const SOURCE = D.source;

// The trades most people will look for, shown first. Everything else is searchable.
export const COMMON = ['47-2111', '47-2152', '51-4121', '49-9021', '49-3023', '49-3031', '47-2031', '47-2061', '47-2073', '53-3032', '49-9041', '49-9071', '51-4041', '47-2221', '49-9051', '47-2141', '47-2181', '51-8093', '51-8091', '47-2011', '53-7051', '53-7062', '47-1011', '51-1011', '47-2051', '51-2092'];

export type Option = { id: string; label: string };
export function occupations(): Option[] {
  const label = (c: string) => D.occupations[c].replace(/, Except.*$/, '').replace(/\s+and\s+/g, ' & ');
  const rest = Object.keys(D.occupations).filter((c) => !COMMON.includes(c)).sort((a, b) => label(a).localeCompare(label(b)));
  return [...COMMON.filter((c) => D.occupations[c]), ...rest].map((c) => ({ id: c, label: label(c) }));
}
export function areas(): Option[] {
  return Object.entries(D.areas).map(([id, a]) => ({ id, label: a.name })).sort((a, b) => a.label.localeCompare(b.label));
}
export const occTitle = (c: string) => D.occupations[c] || null;
export const areaInfo = (a: string) => D.areas[a] || null;
export const hasData = (occ: string, area: string) => !!D.wages[occ]?.[area];

// Percentile of a wage given the published points, by straight-line interpolation between them.
export function percentile(w: number, row: Row): number {
  const pts = ([[10, row[0]], [25, row[1]], [50, row[2]], [75, row[3]], [90, row[4]]] as [number, number | null][]).filter((p): p is [number, number] => p[1] !== null);
  if (w <= pts[0][1]) return pts[0][0] === 10 ? Math.max(1, Math.round(10 * (w / pts[0][1]))) : pts[0][0];
  for (let i = 1; i < pts.length; i++) {
    const [p0, w0] = pts[i - 1], [p1, w1] = pts[i];
    if (w <= w1) return Math.round(p0 + ((w - w0) / (w1 - w0 || 1)) * (p1 - p0));
  }
  return pts[pts.length - 1][0] === 90 ? Math.min(99, 90 + Math.round(((w - pts[pts.length - 1][1]) / pts[pts.length - 1][1]) * 50)) : pts[pts.length - 1][0];
}

// Employment-weighted median across all metros: a stand-in for "the U.S." in this job.
const usCache = new Map<string, number>();
export function usMedian(occ: string): number | null {
  if (usCache.has(occ)) return usCache.get(occ)!;
  const rows = Object.values(D.wages[occ] || {});
  let num = 0, den = 0;
  for (const r of rows) { const e = r[5] || 0; if (e > 0) { num += r[2] * e; den += e; } }
  const v = den ? Math.round((num / den) * 100) / 100 : null;
  if (v !== null) usCache.set(occ, v);
  return v;
}

export type Input = { occ: string; area: string; hourly: number; hours: number; otHours: number; years?: number };
export function cleanInput(b: any): { ok: true; input: Input } | { ok: false; error: string } {
  const occ = String(b?.occ || ''), area = String(b?.area || '');
  if (!occTitle(occ)) return { ok: false, error: 'Pick your job from the list.' };
  if (!areaInfo(area)) return { ok: false, error: 'Pick your area from the list.' };
  const hourly = Math.round(Number(String(b?.hourly ?? '').replace(/[$,\s]/g, '')) * 100) / 100;
  if (!(hourly >= 5 && hourly <= 250)) return { ok: false, error: 'Hourly pay should be between $5 and $250.' };
  const hours = Math.round(Number(b?.hours ?? 40));
  if (!(hours >= 1 && hours <= 80)) return { ok: false, error: 'Regular hours a week should be 1 to 80.' };
  const otHours = Math.round(Number(b?.otHours || 0));
  if (!(otHours >= 0 && otHours <= 60)) return { ok: false, error: 'Overtime hours a week should be 0 to 60.' };
  const yrs = b?.years === '' || b?.years === undefined || b?.years === null ? undefined : Math.round(Number(b.years));
  if (yrs !== undefined && !(yrs >= 0 && yrs <= 60)) return { ok: false, error: 'Years in the trade should be 0 to 60.' };
  return { ok: true, input: { occ, area, hourly, hours, otHours, years: yrs } };
}

export type Community = { count: number; median: number | null };
export type Result = {
  job: string; area: string; hourly: number;
  local: { p25: number | null; median: number; p75: number | null; employment: number | null } | null;
  percentile: number | null;
  vsMedian: number | null;            // dollars per hour above (+) or below (-) the local median
  priceLevel: number | null;          // 100 = U.S. average prices
  buysLike: number | null;            // what this hourly buys in average-U.S. dollars
  usMedian: number | null;
  vsUS: number | null;                // buysLike minus U.S. median (both in U.S.-average dollars)
  yearly: number;                     // regular + OT at time and a half, 52 weeks
  community: Community;
};

const r2 = (n: number) => Math.round(n * 100) / 100;
export function compare(i: Input, community: Community = { count: 0, median: null }): Result {
  const row = D.wages[i.occ]?.[i.area] || null;
  const a = D.areas[i.area];
  const priceLevel = a.rpp;
  const buysLike = priceLevel ? r2(i.hourly / (priceLevel / 100)) : null;
  const us = usMedian(i.occ);
  return {
    job: D.occupations[i.occ], area: a.name, hourly: i.hourly,
    local: row ? { p25: row[1], median: row[2], p75: row[3], employment: row[5] } : null,
    percentile: row ? percentile(i.hourly, row) : null,
    vsMedian: row ? r2(i.hourly - row[2]) : null,
    priceLevel, buysLike, usMedian: us,
    vsUS: buysLike !== null && us !== null ? r2(buysLike - us) : null,
    yearly: Math.round((i.hourly * i.hours + i.hourly * 1.5 * i.otHours) * 52),
    community,
  };
}

export const MIN_GROUP = 5; // community numbers are only shown once 5+ people share a job and area
