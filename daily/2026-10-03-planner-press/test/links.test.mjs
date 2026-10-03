import { test } from 'node:test';
import assert from 'node:assert/strict';
import { jsPDF } from 'jspdf';
import { makePlan, verifyLinks } from '../plan.js';
import { layoutAll, measurer } from '../layout.js';
import { iso, daysInMonth } from '../dates.js';

const measure = measurer(jsPDF);
const only = (...ids) => Object.fromEntries(['year', 'month', 'week', 'day', 'notes'].map((k) => [k, ids.includes(k)]));
const build = (o) => { const plan = makePlan(o); return { plan, pages: layoutAll(plan, measure, { theme: 'classic', credit: 'x' }) }; };

// A checker that does not trust plan.js's link helpers: it looks at the page a
// link lands on and asks whether that page is the right one.
function semantic({ plan, pages }) {
  const bad = [];
  const S = plan.sections;
  const first = (m) => iso(plan.year, m, 1);
  const holds = (p, isoDate) => (p.kind === 'week' ? p.days.some((d) => d.iso === isoDate && d.y === plan.year) : p.kind === 'day' ? p.date.iso === isoDate : false);
  pages.forEach((pg, i) => {
    const from = i + 1;
    for (const l of pg.links) {
      const to = plan.pages[l.page - 1];
      if (!to) { bad.push(`p${from} ${l.kind} ${l.key}: no page ${l.page}`); continue; }
      if (l.kind === 'tab-month') {
        const m = Number(l.key);
        const ok = S.month ? to.kind === 'month' && to.month === m : S.week ? holds(to, first(m)) : S.day ? holds(to, first(m)) : to.kind === 'year';
        if (!ok) bad.push(`p${from} tab ${m} lands on ${to.kind} page ${l.page}`);
      } else if (l.kind === 'tab-home') {
        if (!(S.year ? to.kind === 'year' : l.page === 1)) bad.push(`p${from} home lands on ${to.kind}`);
      } else if (l.kind === 'tab-notes') {
        if (to.kind !== 'notes' || to.n !== 1) bad.push(`p${from} notes tab lands on ${to.kind}`);
      } else if (l.kind === 'year-month') {
        const m = Number(l.key);
        if (S.month ? !(to.kind === 'month' && to.month === m) : !(holds(to, first(m)) || to.kind === 'year')) bad.push(`p${from} year-month ${m} lands on ${to.kind}`);
      } else if (l.kind === 'day-num') {
        if (S.week ? !(to.kind === 'week' && holds(to, l.key)) : !holds(to, l.key)) bad.push(`p${from} day ${l.key} number lands on ${to.kind} ${l.page}`);
      } else if (l.kind === 'day-body') {
        if (!(to.kind === 'day' && to.date.iso === l.key)) bad.push(`p${from} day ${l.key} body lands on ${to.kind} ${l.page}`);
      } else if (l.kind === 'week-day') {
        if (!(to.kind === 'day' && to.date.iso === l.key)) bad.push(`p${from} week day ${l.key} lands on ${to.kind}`);
      } else if (l.kind === 'day-week') {
        if (!(to.kind === 'week' && holds(to, l.key))) bad.push(`p${from} day ${l.key} back-link lands on ${to.kind}`);
      } else bad.push(`unknown link kind ${l.kind}`);
    }
  });
  return bad;
}

const CONFIGS = [
  { year: 2027, weekStart: 0, sections: only('year', 'month', 'week', 'day', 'notes') },
  { year: 2028, weekStart: 1, orientation: 'portrait', sections: only('year', 'month', 'week', 'day', 'notes') },
  { year: 2026, weekStart: 1, sections: only('year', 'month', 'week') },
  { year: 2027, weekStart: 0, sections: only('month', 'day') },
  { year: 2028, weekStart: 0, sections: only('week', 'day', 'notes') },
  { year: 2027, weekStart: 1, sections: only('year', 'week') },
  { year: 2026, weekStart: 0, sections: only('day') },
  { year: 2027, weekStart: 0, sections: only('year') },
  { year: 2027, weekStart: 0, sections: only('notes') },
  { year: 2028, weekStart: 1, sections: only('month') },
];

test('every drawn link matches the plan, and each one lands on the right page, in ten different setups', () => {
  for (const cfg of CONFIGS) {
    const b = build(cfg);
    assert.deepEqual(verifyLinks(b.plan, b.pages), [], JSON.stringify(cfg));
    assert.deepEqual(semantic(b), [], JSON.stringify(cfg));
  }
});

test('month tabs: all 12 on every page of the full planner, each going to that month page', () => {
  const b = build(CONFIGS[0]);
  for (const [i, pg] of b.pages.entries()) {
    const tabs = pg.links.filter((l) => l.kind === 'tab-month');
    assert.equal(tabs.length, 12, `page ${i + 1}`);
    for (const t of tabs) {
      const target = b.plan.pages[t.page - 1];
      assert.equal(target.kind, 'month');
      assert.equal(target.month, Number(t.key));
      assert.equal(t.page, 1 + Number(t.key)); // year is page 1, then January is page 2
    }
  }
});

test('every page has a way back to the year overview', () => {
  const b = build(CONFIGS[0]);
  for (const [i, pg] of b.pages.entries()) {
    const home = pg.links.filter((l) => l.kind === 'tab-home');
    assert.equal(home.length, 1, `page ${i + 1}`);
    assert.equal(b.plan.pages[home[0].page - 1].kind, 'year');
  }
});

test('every day number on a month page opens the week that holds it; the rest of the box opens that day', () => {
  const b = build(CONFIGS[0]);
  let nums = 0;
  for (let m = 1; m <= 12; m++) {
    const pg = b.pages[b.plan.at.month[m] - 1];
    const num = pg.links.filter((l) => l.kind === 'day-num');
    const body = pg.links.filter((l) => l.kind === 'day-body');
    assert.equal(num.length, daysInMonth(2027, m));
    assert.equal(body.length, daysInMonth(2027, m));
    for (const l of num) {
      const week = b.plan.pages[l.page - 1];
      assert.equal(week.kind, 'week');
      assert.ok(week.days.some((d) => d.iso === l.key), `${l.key} in week ${week.week}`);
      nums++;
    }
    for (const l of body) assert.equal(b.plan.pages[l.page - 1].date.iso, l.key);
  }
  assert.equal(nums, 365);
});

test('with only daily pages, the day number goes straight to the day page', () => {
  const b = build(CONFIGS[3]);
  const pg = b.pages[b.plan.at.month[2] - 1];
  const nums = pg.links.filter((l) => l.kind === 'day-num');
  assert.equal(nums.length, 28);
  for (const l of nums) assert.equal(b.plan.pages[l.page - 1].date.iso, l.key);
  assert.equal(pg.links.filter((l) => l.kind === 'day-body').length, 0);
});

test('month tabs still work with no monthly pages: they open the week (or day) that holds the 1st', () => {
  const b = build(CONFIGS[4]); // 2028, weeks + days + notes
  const march = b.pages[0].links.find((l) => l.kind === 'tab-month' && l.key === '3');
  const to = b.plan.pages[march.page - 1];
  assert.equal(to.kind, 'week');
  assert.ok(to.days.some((d) => d.iso === '2028-03-01'));
});

test('no link points past the last page, and none starts outside its page', () => {
  for (const cfg of CONFIGS) {
    const { plan, pages } = build(cfg);
    for (const pg of pages) for (const l of pg.links) {
      assert.ok(l.page >= 1 && l.page <= plan.count, `${l.kind} ${l.key} -> ${l.page} of ${plan.count}`);
      assert.ok(l.x >= 0 && l.y >= 0 && l.x + l.w <= pg.w + 0.01 && l.y + l.h <= pg.h + 0.01);
      assert.ok(l.w > 4 && l.h > 4, 'big enough to tap');
    }
  }
});

test('the checkers catch planted faults: a wrong tab, a link past the end, a missing link, a link to the wrong week', () => {
  const clean = () => build(CONFIGS[0]);
  assert.deepEqual(verifyLinks(...Object.values(clean())), []);

  let b = clean();
  b.pages[4].links.find((l) => l.kind === 'tab-month' && l.key === '7').page += 1; // July tab to August
  assert.ok(verifyLinks(b.plan, b.pages).length > 0, 'plan check misses a wrong tab');
  assert.ok(semantic(b).length > 0, 'page check misses a wrong tab');

  b = clean();
  b.pages[0].links[3].page = b.plan.count + 1;
  assert.match(verifyLinks(b.plan, b.pages).join('\n'), /past the 441/);
  assert.ok(semantic(b).length > 0);

  b = clean();
  b.pages[10].links.splice(5, 1);
  assert.match(verifyLinks(b.plan, b.pages).join('\n'), /missing link/);

  b = clean();
  const feb = b.pages[b.plan.at.month[2] - 1].links.find((l) => l.kind === 'day-num' && l.key === '2027-02-10');
  feb.page += 1; // the next week
  assert.ok(verifyLinks(b.plan, b.pages).length > 0);
  assert.ok(semantic(b).length > 0, 'page check misses a link to the wrong week');

  // the page check catches a planner whose own helpers are wrong, which the plan check alone would not
  b = clean();
  const real = b.plan.at.week[12];
  b.plan.at.week[12] = real + 1;
  const wrong = build({ ...CONFIGS[0] });
  wrong.plan.at.week[12] = real + 1;
  const redrawn = { plan: wrong.plan, pages: layoutAll(wrong.plan, measure, { theme: 'classic' }) };
  assert.ok(semantic(redrawn).length > 0);
});
