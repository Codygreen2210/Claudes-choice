import { test } from 'node:test';
import assert from 'node:assert/strict';
import { jsPDF } from 'jspdf';
import { makePlan } from '../plan.js';
import { PAGE, THEMES, contentBox, layoutAll, layoutPage, toSvg, measurer } from '../layout.js';

const measure = measurer(jsPDF);
const CREDIT = 'Made with Planner Press';
const EPS = 0.01;

test('four themes, two page shapes, every color a real hex', () => {
  assert.deepEqual(Object.keys(THEMES), ['classic', 'sage', 'rose', 'night']);
  assert.deepEqual(Object.keys(PAGE), ['landscape', 'portrait']);
  assert.ok(PAGE.landscape.w > PAGE.landscape.h && PAGE.portrait.h > PAGE.portrait.w);
  for (const t of Object.values(THEMES)) for (const [k, v] of Object.entries(t)) if (k !== 'label') assert.match(v, /^#[0-9a-f]{6}$/i, k);
});

test('both orientations, all four themes, every page: nothing is drawn outside the page', () => {
  for (const orientation of ['landscape', 'portrait']) for (const weekStart of [0, 1]) {
    const plan = makePlan({ year: 2028, weekStart, orientation });
    for (const theme of Object.keys(THEMES)) {
      const pages = layoutAll(plan, measure, { theme, credit: CREDIT });
      assert.equal(pages.length, plan.count);
      for (const pg of pages) {
        const where = `${orientation} ${theme} page ${pg.number} (${pg.kind})`;
        assert.deepEqual([pg.w, pg.h], [PAGE[orientation].w, PAGE[orientation].h]);
        for (const it of pg.items) {
          if (it.t === 'rect') assert.ok(it.x >= -EPS && it.y >= -EPS && it.x + it.w <= pg.w + EPS && it.y + it.h <= pg.h + EPS, `${where} rect ${JSON.stringify(it)}`);
          else if (it.t === 'line') assert.ok([it.x1, it.x2].every((x) => x >= -EPS && x <= pg.w + EPS) && [it.y1, it.y2].every((y) => y >= -EPS && y <= pg.h + EPS), `${where} line`);
          else assert.ok(it.x >= -EPS && it.x + it.w <= pg.w + EPS && it.y - it.size >= -EPS && it.y + it.size * 0.3 <= pg.h + EPS, `${where} text "${it.text}" x=${it.x} w=${it.w} y=${it.y}`);
        }
        for (const l of pg.links) assert.ok(l.x >= 0 && l.y >= 0 && l.x + l.w <= pg.w + EPS && l.y + l.h <= pg.h + EPS, `${where} link`);
      }
    }
  }
});

test('page content stays inside its margins and clear of the tab column; only the tabs and the credit line go further', () => {
  for (const orientation of ['landscape', 'portrait']) {
    const plan = makePlan({ year: 2027, weekStart: 0, orientation });
    const C = contentBox(orientation);
    const pages = layoutAll(plan, measure, { theme: 'classic', credit: CREDIT });
    for (const pg of pages) for (const [i, it] of pg.items.entries()) {
      if (i === 0 || it.nav || it.text === CREDIT) continue; // the paper itself, the tabs, the credit line
      const where = `${orientation} page ${pg.number} (${pg.kind}) ${it.text || it.t}`;
      const x2 = it.t === 'line' ? Math.max(it.x1, it.x2) : it.x + (it.w || 0);
      const x1 = it.t === 'line' ? Math.min(it.x1, it.x2) : it.x;
      const y2 = it.t === 'line' ? Math.max(it.y1, it.y2) : it.t === 'text' ? it.y : it.y + it.h;
      assert.ok(x1 >= C.x - EPS && x2 <= C.r + EPS, `${where} sideways x=${x1}..${x2} box ${C.x}..${C.r}`);
      assert.ok(y2 <= C.b + EPS, `${where} runs into the bottom`);
    }
  }
});

test('the credit line is on every page of the free file and on none of the paid one', () => {
  const plan = makePlan({ year: 2027, weekStart: 0, sections: { year: true, month: true, week: true, day: false, notes: true } });
  const free = layoutAll(plan, measure, { theme: 'sage', credit: CREDIT });
  const paid = layoutAll(plan, measure, { theme: 'sage', credit: '' });
  for (const pg of free) assert.equal(pg.items.filter((i) => i.text === CREDIT).length, 1, `page ${pg.number}`);
  for (const pg of paid) assert.equal(pg.items.filter((i) => i.text === CREDIT).length, 0);
  assert.equal(free.length, paid.length);
  // paid and free differ only by that one line
  free.forEach((pg, i) => assert.equal(pg.items.length - 1, paid[i].items.length));
});

test('a single page can be laid out on its own and matches the same page from the whole book', () => {
  const plan = makePlan({ year: 2027, weekStart: 1, orientation: 'portrait' });
  const all = layoutAll(plan, measure, { theme: 'rose', credit: CREDIT });
  for (const i of [0, 5, 40, 200, plan.count - 1]) assert.deepEqual(layoutPage(plan, i, measure, { theme: 'rose', credit: CREDIT }), all[i]);
});

test('the picture for the screen has the page size, the text, and tappable link boxes', () => {
  const plan = makePlan({ year: 2027, weekStart: 0 });
  const pg = layoutPage(plan, plan.at.month[3] - 1, measure, { theme: 'night', credit: CREDIT });
  const svg = toSvg(pg, { links: true });
  assert.ok(svg.includes('viewBox="0 0 842 595"'));
  assert.ok(svg.includes('>March<') && svg.includes(CREDIT) && svg.includes('#161d2e'));
  assert.equal((svg.match(/class="lnk"/g) || []).length, pg.links.length);
  assert.equal((toSvg(pg).match(/class="lnk"/g) || []).length, 0);
});

test('the 31 days of March sit under the right weekdays on a Monday-start month page', () => {
  const plan = makePlan({ year: 2027, weekStart: 1 });
  const pg = layoutPage(plan, plan.at.month[3] - 1, measure, { theme: 'classic' });
  const heads = pg.items.filter((i) => i.text && /^(MON|TUE|WED|THU|FRI|SAT|SUN)$/.test(i.text)).map((i) => i.text);
  assert.deepEqual(heads, ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']);
  const nums = pg.items.filter((i) => i.text && /^\d+$/.test(i.text) && i.size === 11 && i.font === 'sans-bold');
  assert.equal(nums.length, 31);
  const cw = (contentBox('landscape').r - 28) / 7;
  const col = (n) => { const it = nums.find((i) => i.text === String(n)); return Math.floor((it.x + it.w / 2 - 28) / cw); }; // March 1 2027 is a Monday
  assert.equal(col(1), 0);
  assert.equal(col(7), 6);
  assert.equal(col(8), 0);
});
