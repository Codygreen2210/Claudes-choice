import { test } from 'node:test';
import assert from 'node:assert/strict';
import { jsPDF } from 'jspdf';
import { makePlan } from '../plan.js';
import { PAGE, layoutAll, toPdf, measurer } from '../layout.js';
import { readPdf } from './pdftext.mjs';

const measure = measurer(jsPDF);
const CREDIT = 'Made with Planner Press';
const only = (...ids) => Object.fromEntries(['year', 'month', 'week', 'day', 'notes'].map((k) => [k, ids.includes(k)]));
const make = (o, credit = CREDIT) => {
  const plan = makePlan(o);
  const pages = layoutAll(plan, measure, { theme: o.theme || 'classic', credit });
  const buf = Buffer.from(toPdf(pages, jsPDF, { title: 't' }).output('arraybuffer'));
  return { plan, pages, pdf: readPdf(buf), buf };
};

test('page count matches the plan, and every page is the right size, in both orientations', () => {
  for (const orientation of ['landscape', 'portrait']) {
    const { plan, pdf } = make({ year: 2027, weekStart: 0, orientation, sections: only('year', 'month', 'week', 'notes') });
    assert.equal(plan.count, 1 + 12 + 53 + 10);
    assert.equal(pdf.pageCount, plan.count);
    assert.equal(pdf.pages.length, plan.count);
    for (const p of pdf.pages) assert.deepEqual([p.w, p.h], [PAGE[orientation].w, PAGE[orientation].h], `page ${p.number}`);
  }
});

test('the default planner (2027, Sunday, landscape, everything) is 441 pages', () => {
  const { plan, pdf } = make({ year: 2027, weekStart: 0 });
  assert.equal(plan.count, 441);
  assert.equal(pdf.pageCount, 441);
});

test('2028 daily pages: 366 of them, one for Feb 29', () => {
  const { plan, pdf } = make({ year: 2028, weekStart: 1, sections: only('day') });
  assert.equal(plan.count, 366);
  assert.equal(pdf.pageCount, 366);
  assert.match(pdf.text, /\(Tuesday\) Tj/);
  assert.ok(pdf.text.includes('(February 29, 2028) Tj'));
});

test('link annotations in the PDF equal the links planned, one for one', () => {
  for (const cfg of [{ year: 2027, weekStart: 0 }, { year: 2028, weekStart: 1, orientation: 'portrait' }, { year: 2026, weekStart: 0, sections: only('month', 'week') }, { year: 2027, weekStart: 0, sections: only('notes') }]) {
    const { plan, pages, pdf } = make(cfg);
    const drawn = pages.reduce((n, p) => n + p.links.length, 0);
    assert.equal(drawn, plan.expected.length);
    assert.equal(pdf.linkCount, plan.expected.length, JSON.stringify(cfg));
  }
});

test('every link in the file sits where it was drawn and jumps to the planned page', () => {
  const { plan, pages, pdf } = make({ year: 2027, weekStart: 1, orientation: 'portrait' });
  pdf.pages.forEach((p, i) => {
    const want = pages[i].links;
    assert.equal(p.links.length, want.length, `page ${i + 1}`);
    p.links.forEach((l, k) => {
      assert.equal(l.page, want[k].page, `page ${i + 1} link ${k}`);
      assert.ok(Math.abs(l.x1 - want[k].x) < 0.5 && Math.abs(l.x2 - (want[k].x + want[k].w)) < 0.5);
      assert.ok(Math.abs(l.y1 - (pages[i].h - want[k].y)) < 0.5 && Math.abs(l.y2 - (pages[i].h - want[k].y - want[k].h)) < 0.5);
      assert.ok(l.page >= 1 && l.page <= plan.count);
    });
  });
});

test('the credit line is on every page of the free file and gone from the paid file', () => {
  const free = make({ year: 2027, weekStart: 0, sections: only('year', 'month', 'week', 'notes') });
  assert.equal(free.pdf.count(CREDIT), free.plan.count);
  const paid = make({ year: 2027, weekStart: 0, sections: only('year', 'month', 'week', 'notes') }, '');
  assert.equal(paid.pdf.count(CREDIT), 0);
  assert.ok(!paid.pdf.text.includes('Planner Press'));
  assert.equal(paid.pdf.pageCount, free.pdf.pageCount);
});

test('the default planner is a reasonable size to hold on a tablet', () => {
  const { buf } = make({ year: 2027, weekStart: 0 });
  assert.ok(buf.length < 3 * 1024 * 1024, `${buf.length} bytes`);
});
