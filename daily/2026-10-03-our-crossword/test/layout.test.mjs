import { test } from 'node:test';
import assert from 'node:assert/strict';
import { jsPDF } from 'jspdf';
import { build } from '../construct.js';
import { SIZES, THEMES, wrap, clean, clueText, layout, toSvg, toPdf, measurer } from '../layout.js';

const measure = measurer(jsPDF);
const CLUES = [
  ['Savannah', 'City where we met'], ['Golden retriever', "Biscuit's breed"], ['Tacos', 'First-date dinner'], ['Lake Tahoe', 'Where he proposed'],
  ['Biscuit', 'Our dog'], ['Chemistry', "Emma's college major"], ['The Office', 'Show we have watched four times through'], ['Paris', 'Honeymoon city'],
  ['Hiking', 'Our favorite weekend plan'], ['Coffee', "Jack can't start a day without it"], ['June', 'Month of the wedding'], ['Navy', 'Color of the groomsmen suits'],
  ['Karaoke', 'How the first date ended'], ['Jeep', "Jack's first car"], ['Pancakes', 'Sunday morning tradition'], ['Florist', "The bride's first job"],
  ['Denver', 'Where we live now'], ['Best man', 'Tyler, to Jack'],
].map(([answer, clue]) => ({ answer, clue }));
const puzzle = build(CLUES, { seed: 3 });
const design = (o = {}) => ({ title: 'Emma & Jack', subtitle: 'June 14, 2027 · Sip & Solve', footer: 'Thank you for celebrating with us', theme: 'classic', size: 'letter', credit: 'ourcrossword.com', ...o });

test('text wraps at the width given and never loses a word', () => {
  const text = 'Show we have watched four times through and still quote daily';
  const lines = wrap(text, 120, 'serif', 12, measure);
  assert.ok(lines.length >= 3);
  for (const l of lines) assert.ok(measure(l, 'serif', 12) <= 120, l);
  assert.equal(lines.join(' '), text);
  assert.deepEqual(wrap('Supercalifragilistic', 20, 'serif', 12, measure), ['Supercalifragilistic']);
});

test('curly quotes and dashes become plain; emoji is dropped', () => {
  assert.equal(clean('Jack’s “big” day — finally…'), 'Jack\'s "big" day - finally...');
  assert.equal(clean('Our dog 🐶 Biscuit'), 'Our dog Biscuit');
  assert.equal(clean('Café in Zürich'), 'Café in Zürich');
  assert.equal(clueText({ clue: 'Where he proposed', count: '4,5' }), 'Where he proposed (4,5)');
  assert.equal(clueText({ clue: '', count: '5' }), '(no clue yet)');
});

test('every paper size and theme: nothing runs off the page or into the margins, on both pages', () => {
  for (const size of Object.keys(SIZES)) for (const theme of Object.keys(THEMES)) {
    const out = layout(puzzle, design({ size, theme }), measure);
    assert.equal(out.overflow, false, `${size} ${theme}`);
    assert.equal(out.pages.length, 2);
    for (const page of out.pages) {
      assert.deepEqual([page.w, page.h], [SIZES[size].w, SIZES[size].h]);
      for (const it of page.items.slice(1)) {
        const edge = 12;
        if (it.t === 'rect') assert.ok(it.x >= edge && it.y >= edge && it.x + it.w <= page.w - edge && it.y + it.h <= page.h - edge, `${size} rect`);
        if (it.t === 'text') assert.ok(it.x >= edge && it.x + it.w <= page.w - edge + 0.5 && it.y > edge && it.y <= page.h - edge, `${size} "${it.text}" x=${it.x} w=${it.w}`);
      }
    }
  }
});

test('clues start below the grid and stay above the footer', () => {
  for (const size of Object.keys(SIZES)) {
    const { pages } = layout(puzzle, design({ size }), measure);
    const items = pages[0].items;
    const gridBottom = Math.max(...items.filter((i) => i.t === 'rect' && i.w < pages[0].w).map((i) => i.y + i.h));
    const acrossHead = items.find((i) => i.text === 'ACROSS');
    const footer = items.find((i) => i.text === 'Thank you for celebrating with us');
    const clues = items.filter((i) => i.t === 'text' && i.font === 'serif');
    assert.ok(acrossHead.y - acrossHead.size > gridBottom, size);
    for (const c of clues) assert.ok(c.y < footer.y - footer.size, `${size}: "${c.text}" runs into the footer`);
  }
});

test('every clue is printed once, with its number, under the right heading', () => {
  const { pages } = layout(puzzle, design(), measure);
  const text = pages[0].items.filter((i) => i.t === 'text').map((i) => i.text);
  for (const w of puzzle.words) assert.ok(text.includes(`${w.number}.`), `number ${w.number}`);
  const joined = text.join(' ');
  for (const c of CLUES) assert.ok(joined.includes(c.clue.split(' ')[0]), c.clue);
  assert.ok(joined.includes('(6,9)'), 'two-word answers show their letter count');
  assert.equal(text.filter((t) => t === 'ACROSS').length, 1);
  assert.equal(text.filter((t) => t === 'DOWN').length, 1);
});

test('the puzzle page shows no answers; the answer key shows every letter', () => {
  const { pages } = layout(puzzle, design(), measure);
  const letters = (p) => p.items.filter((i) => i.t === 'text' && i.font === 'sans-bold' && /^[A-Z]$/.test(i.text)).length;
  assert.equal(letters(pages[0]), 0);
  assert.equal(letters(pages[1]), puzzle.cells.length);
  assert.ok(pages[1].items.some((i) => i.text === 'ANSWER KEY'));
});

test('a very long title shrinks to fit instead of running off the page', () => {
  const { pages } = layout(puzzle, design({ title: 'Alexandria Montgomery-Fitzgerald & Bartholomew Wolfeschlegelstein' }), measure);
  const t = pages[0].items.find((i) => i.font === 'serif-italic');
  assert.ok(t.x >= 26 && t.x + t.w <= 612 - 26, `x=${t.x} w=${t.w}`);
});

test('too many clues for a small card is flagged, never silently clipped; a poster takes them', () => {
  const many = Array.from({ length: 34 }, (_, i) => ({ answer: ['apple', 'river', 'mountain', 'guitar', 'sunset', 'bicycle', 'lantern', 'harbor', 'meadow', 'thunder', 'violet', 'copper', 'window', 'garden', 'pepper', 'candle', 'summer', 'winter', 'bridge', 'forest', 'ocean', 'piano', 'rocket', 'silver', 'tiger', 'umbrella', 'village', 'whistle', 'yellow', 'zipper', 'anchor', 'butter', 'cactus', 'dragon'][i], clue: 'A fairly long clue that takes up a good bit of room on the card for this one' }));
  const big = build(many, { seed: 2 });
  assert.equal(layout(big, design({ size: '5x7' }), measure).overflow, true);
  assert.equal(layout(big, design({ size: '24x36' }), measure).overflow, false);
});

test('works with no title, subtitle, footer or credit', () => {
  const out = layout(puzzle, { theme: 'garden', size: '8x10' }, measure);
  assert.equal(out.overflow, false);
  assert.ok(out.cell > 10);
});

test('the PDF has two pages at the exact paper size, as real text (not a picture)', () => {
  for (const size of ['5x7', 'letter', '24x36']) {
    const { pages } = layout(puzzle, design({ size, theme: 'midnight' }), measure);
    const bytes = Buffer.from(toPdf(pages, jsPDF).output('arraybuffer'));
    const raw = bytes.toString('latin1');
    assert.ok(raw.startsWith('%PDF-'));
    const boxes = [...raw.matchAll(/\/MediaBox \[0 0 ([\d.]+) ([\d.]+)\]/g)].map((m) => [Number(m[1]), Number(m[2])]);
    assert.equal(boxes.length, 2, size);
    for (const b of boxes) { assert.ok(Math.abs(b[0] - SIZES[size].w) < 0.1); assert.ok(Math.abs(b[1] - SIZES[size].h) < 0.1); }
    assert.ok(/\/BaseFont \/Times-Italic/.test(raw) && /\/BaseFont \/Helvetica/.test(raw));
    assert.ok(bytes.length < 400000, `${size}: ${bytes.length} bytes`);
  }
});

test('the screen picture pins each line to its measured width and escapes names with &', () => {
  const { pages } = layout(puzzle, design(), measure);
  const svg = toSvg(pages[0], { watermark: 'PREVIEW' });
  assert.ok(svg.startsWith('<svg') && svg.endsWith('</svg>'));
  assert.ok(svg.includes('Emma &amp; Jack'));
  assert.ok(!/&(?!amp;|lt;|gt;|quot;)/.test(svg));
  assert.ok((svg.match(/textLength=/g) || []).length > 40);
  assert.ok(svg.includes('PREVIEW'));
  assert.ok(!toSvg(pages[0]).includes('PREVIEW'));
});
