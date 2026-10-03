// Planner Press: the page plan. Decides which pages exist, in what order, and
// where every link must go. No drawing here; layout.js draws, and the tests
// compare what was drawn against `expectedLinks` below.
import { daysOfYear, weeksOfYear, monthRows, toDays, day, iso } from './dates.js';

export const YEARS = [2026, 2027, 2028];
export const NOTES_PAGES = 10;
export const SECTION_IDS = ['year', 'month', 'week', 'day', 'notes'];

// opts: { year, weekStart: 0|1, orientation: 'landscape'|'portrait', sections: { year, month, week, day, notes } }
export function makePlan(opts) {
  const year = opts.year;
  const weekStart = opts.weekStart === 1 ? 1 : 0;
  const sections = { year: true, month: true, week: true, day: true, notes: true, ...opts.sections };
  const orientation = opts.orientation === 'portrait' ? 'portrait' : 'landscape';
  const weeks = weeksOfYear(year, weekStart);
  const days = daysOfYear(year);

  const pages = [];
  const add = (p) => { pages.push({ ...p, number: pages.length + 1 }); return pages.length; };
  const at = { year: null, month: {}, week: {}, day: {}, notes: [] };

  if (sections.year) at.year = add({ kind: 'year' });
  if (sections.month) for (let m = 1; m <= 12; m++) at.month[m] = add({ kind: 'month', month: m, rows: monthRows(year, m, weekStart) });
  if (sections.week) for (const w of weeks) at.week[w.n] = add({ kind: 'week', week: w.n, days: w.days });
  if (sections.day) for (const d of days) at.day[d.iso] = add({ kind: 'day', date: d });
  if (sections.notes) for (let i = 1; i <= NOTES_PAGES; i++) at.notes.push(add({ kind: 'notes', n: i }));
  if (!pages.length) throw new Error('A planner needs at least one section');

  const weekOfIso = {};
  for (const w of weeks) for (const d of w.days) if (d.y === year) weekOfIso[d.iso] = w.n;

  // The week page that holds a date, or null.
  const weekNumberOf = (isoDate) => weekOfIso[isoDate] ?? null;
  // The month a week page belongs to (for the highlighted tab): the month of its middle day, held inside the year.
  const weekMonth = (w) => {
    const mid = w.days[3].n;
    const lo = toDays(year, 1, 1), hi = toDays(year, 12, 31);
    return day(Math.min(hi, Math.max(lo, mid))).m;
  };

  // Where a month tab goes: the month page, else the week page that holds the 1st,
  // else the day page for the 1st, else (year only) the year page.
  const monthTarget = (m) => {
    if (sections.month) return at.month[m];
    const first = iso(year, m, 1);
    if (sections.week) return at.week[weekNumberOf(first)];
    if (sections.day) return at.day[first];
    return at.year; // may be null
  };
  const homeTarget = at.year || 1;
  const homeLabel = at.year ? 'YEAR' : 'START';
  const notesTarget = at.notes[0] || null;
  // Day number on a month page: its week page, or its day page when there are no week pages.
  const dayNumberTarget = (isoDate) => (sections.week ? at.week[weekNumberOf(isoDate)] : sections.day ? at.day[isoDate] : null);
  // The rest of the day's box: its day page, only when week pages took the number.
  const dayBodyTarget = (isoDate) => (sections.week && sections.day ? at.day[isoDate] : null);
  const weekDayTarget = (isoDate) => (sections.day ? at.day[isoDate] ?? null : null);
  const dayWeekTarget = (isoDate) => (sections.week ? at.week[weekNumberOf(isoDate)] : null);

  const plan = { year, weekStart, orientation, sections, weeks, days, pages, count: pages.length, at, weekNumberOf, weekMonth, monthTarget, homeTarget, homeLabel, notesTarget, dayNumberTarget, dayBodyTarget, weekDayTarget, dayWeekTarget };
  plan.expected = expectedLinks(plan);
  return plan;
}

// Every link the finished planner must have, worked out from the plan alone:
// { from, kind, key, to } with page numbers (1-based).
export function expectedLinks(plan) {
  const out = [];
  const push = (from, kind, key, to) => { if (to) out.push({ from, kind, key: String(key), to }); };
  for (const p of plan.pages) {
    const from = p.number;
    push(from, 'tab-home', 'home', plan.homeTarget);
    for (let m = 1; m <= 12; m++) push(from, 'tab-month', m, plan.monthTarget(m));
    push(from, 'tab-notes', 'notes', plan.notesTarget);
    if (p.kind === 'year') for (let m = 1; m <= 12; m++) push(from, 'year-month', m, plan.monthTarget(m));
    if (p.kind === 'month') for (const row of p.rows) for (const d of row) {
      if (!d) continue;
      push(from, 'day-num', d.iso, plan.dayNumberTarget(d.iso));
      push(from, 'day-body', d.iso, plan.dayBodyTarget(d.iso));
    }
    if (p.kind === 'week') for (const d of p.days) if (d.y === plan.year) push(from, 'week-day', d.iso, plan.weekDayTarget(d.iso));
    if (p.kind === 'day') push(from, 'day-week', p.date.iso, plan.dayWeekTarget(p.date.iso));
  }
  return out;
}

// Compare drawn links against the plan and against the real pages. Returns a
// list of problems; an empty list means every link is present and correct.
// `pages` is the layout output: [{ links: [{ kind, key, page }] }], one per plan page.
export function verifyLinks(plan, pages) {
  const problems = [];
  if (pages.length !== plan.count) problems.push(`drew ${pages.length} pages, planned ${plan.count}`);
  const want = new Map(plan.expected.map((l) => [`${l.from}|${l.kind}|${l.key}`, l.to]));
  const seen = new Set();
  pages.forEach((pg, i) => {
    for (const l of pg.links) {
      const id = `${i + 1}|${l.kind}|${l.key}`;
      if (seen.has(id)) problems.push(`page ${i + 1}: ${l.kind} ${l.key} drawn twice`);
      seen.add(id);
      if (!Number.isInteger(l.page) || l.page < 1 || l.page > plan.count) problems.push(`page ${i + 1}: ${l.kind} ${l.key} points at page ${l.page}, past the ${plan.count} that exist`);
      else if (!want.has(id)) problems.push(`page ${i + 1}: ${l.kind} ${l.key} is not in the plan`);
      else if (want.get(id) !== l.page) problems.push(`page ${i + 1}: ${l.kind} ${l.key} goes to page ${l.page}, should be ${want.get(id)}`);
    }
  });
  for (const id of want.keys()) if (!seen.has(id)) problems.push(`missing link ${id}`);
  return problems;
}
