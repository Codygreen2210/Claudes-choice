import { test } from 'node:test';
import assert from 'node:assert/strict';
import { isLeap, daysInMonth, daysInYear, weekday, toDays, fromDays, daysOfYear, weeksOfYear, monthRows, iso } from '../dates.js';
import { makePlan } from '../plan.js';

test('weekday is right for dates we know', () => {
  const known = [[1970, 1, 1, 4], [2000, 1, 1, 6], [2026, 1, 1, 4], [2026, 10, 3, 6], [2027, 1, 1, 5], [2027, 12, 31, 5], [2028, 1, 1, 6], [2028, 2, 29, 2], [2028, 12, 31, 0]];
  for (const [y, m, d, dow] of known) assert.equal(weekday(y, m, d), dow, `${y}-${m}-${d}`);
});

test('every day from 2000 to 2040 matches the built-in Date, and converts back', () => {
  for (let n = toDays(2000, 1, 1); n <= toDays(2040, 12, 31); n++) {
    const dt = new Date(n * 86400000);
    const want = { y: dt.getUTCFullYear(), m: dt.getUTCMonth() + 1, d: dt.getUTCDate() };
    assert.deepEqual(fromDays(n), want);
    assert.equal(weekday(want.y, want.m, want.d), dt.getUTCDay());
    assert.equal(toDays(want.y, want.m, want.d), n);
  }
});

test('leap years: 2028 has a Feb 29, 2026 and 2027 do not, century rules hold', () => {
  assert.equal(isLeap(2028), true);
  assert.equal(isLeap(2026) || isLeap(2027), false);
  assert.equal(isLeap(1900), false);
  assert.equal(isLeap(2000), true);
  assert.equal(daysInMonth(2028, 2), 29);
  assert.equal(daysInMonth(2027, 2), 28);
  assert.equal(daysInYear(2028), 366);
  assert.ok(daysOfYear(2028).some((d) => d.iso === '2028-02-29'));
  assert.ok(!daysOfYear(2027).some((d) => d.iso === '2027-02-29'));
});

test('daily pages: 365 in a normal year, 366 in 2028, one per date, in order', () => {
  for (const [year, n] of [[2026, 365], [2027, 365], [2028, 366]]) {
    const plan = makePlan({ year, weekStart: 0, sections: { year: false, month: false, week: false, day: true, notes: false } });
    assert.equal(plan.count, n);
    const dates = plan.pages.map((p) => p.date.iso);
    assert.equal(new Set(dates).size, n);
    assert.equal(dates[0], `${year}-01-01`);
    assert.equal(dates.at(-1), `${year}-12-31`);
    for (let i = 1; i < n; i++) assert.equal(toDays(...dates[i].split('-').map(Number)), toDays(...dates[i - 1].split('-').map(Number)) + 1);
  }
});

test('weeks start on the chosen day, have 7 consecutive days, and cover Jan 1 to Dec 31', () => {
  for (const year of [2026, 2027, 2028]) for (const start of [0, 1]) {
    const weeks = weeksOfYear(year, start);
    weeks.forEach((w, i) => {
      assert.equal(w.n, i + 1);
      assert.equal(w.days.length, 7);
      assert.equal(w.days[0].dow, start, `${year} start ${start} week ${w.n}`);
      for (let k = 1; k < 7; k++) assert.equal(w.days[k].n, w.days[k - 1].n + 1);
    });
    assert.ok(weeks[0].days.some((d) => d.iso === `${year}-01-01`));
    assert.ok(weeks.at(-1).days.some((d) => d.iso === `${year}-12-31`));
    assert.ok(!weeks[1].days.some((d) => d.iso === `${year}-01-01`));
  }
});

test('every date of the year is in exactly one week page, and nothing else is counted', () => {
  for (const year of [2026, 2027, 2028]) for (const start of [0, 1]) {
    const plan = makePlan({ year, weekStart: start, sections: { year: false, month: false, week: true, day: false, notes: false } });
    const seen = new Map();
    for (const p of plan.pages) for (const d of p.days) if (d.y === year) seen.set(d.iso, (seen.get(d.iso) || 0) + 1);
    const all = daysOfYear(year);
    assert.equal(seen.size, all.length);
    for (const d of all) assert.equal(seen.get(d.iso), 1, `${d.iso} in ${seen.get(d.iso)} weeks`);
    for (const d of all) assert.equal(plan.pages[plan.weekNumberOf(d.iso) - 1].days.some((x) => x.iso === d.iso), true);
  }
});

test('weeks that spill over a year end: 2027 starting Sunday opens on Dec 27 2026 and closes on Jan 1 2028; Monday 2028 opens on Dec 27 2027', () => {
  const a = weeksOfYear(2027, 0);
  assert.equal(a.length, 53);
  assert.equal(a[0].days[0].iso, '2026-12-27');
  assert.equal(a[0].days[6].iso, '2027-01-02');
  assert.equal(a.at(-1).days[0].iso, '2027-12-26');
  assert.equal(a.at(-1).days[6].iso, '2028-01-01');
  const b = weeksOfYear(2028, 1);
  assert.equal(b[0].days[0].iso, '2027-12-27');
  assert.equal(b[0].days[6].iso, '2028-01-02');
  assert.equal(b.at(-1).days[0].iso, '2028-12-25'); // Dec 31 2028 is a Sunday, the last day of a Monday week
  assert.equal(b.at(-1).days[6].iso, '2028-12-31');
  // a week that crosses a month inside the year
  const w = a.find((x) => x.days.some((d) => d.iso === '2027-03-01'));
  assert.deepEqual([w.days[0].iso, w.days[6].iso], ['2027-02-28', '2027-03-06']);
});

test('week numbers run 1, 2, 3 in order and the plan numbers pages the same way', () => {
  const plan = makePlan({ year: 2028, weekStart: 1, sections: { year: true, month: false, week: true, day: false, notes: false } });
  assert.equal(plan.weekNumberOf('2028-01-01'), 1);
  assert.equal(plan.weekNumberOf('2028-01-02'), 1);
  assert.equal(plan.weekNumberOf('2028-01-03'), 2);
  assert.equal(plan.weekNumberOf('2028-02-29'), 10);
  assert.equal(plan.at.week[1], 2); // year page is page 1
});

test('month grids hold every day once, with the 1st under the right weekday', () => {
  for (const year of [2026, 2027, 2028]) for (const start of [0, 1]) for (let m = 1; m <= 12; m++) {
    const rows = monthRows(year, m, start);
    const cells = rows.flat().filter(Boolean);
    assert.deepEqual(cells.map((d) => d.d), Array.from({ length: daysInMonth(year, m) }, (_, i) => i + 1));
    assert.ok(rows.length >= 4 && rows.length <= 6);
    const first = rows[0].findIndex(Boolean);
    assert.equal(rows[0][first].d, 1);
    assert.equal((weekday(year, m, 1) - start + 7) % 7, first);
    for (const row of rows) assert.equal(row.length, 7);
    assert.equal(cells[0].iso, iso(year, m, 1));
  }
});
