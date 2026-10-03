import { test } from 'node:test';
import assert from 'node:assert/strict';
import { normalize, problem, rng, build, check, parseList } from '../construct.js';

const WEDDING = ['Savannah', 'Golden retriever', 'Tacos', 'Lake Tahoe', 'Biscuit', 'Chemistry', 'The Office', 'Paris', 'Hiking', 'Coffee', 'June', 'Navy', 'Karaoke', 'Jeep', 'Pancakes', 'Florist', 'Denver', 'Best man'];
const list = (words) => words.map((a) => ({ answer: a, clue: `Clue for ${a}` }));
const POOL = ['apple', 'river', 'mountain', 'guitar', 'sunset', 'bicycle', 'lantern', 'harbor', 'meadow', 'thunder', 'violet', 'copper', 'window', 'garden', 'pepper', 'candle', 'summer', 'winter', 'bridge', 'forest', 'ocean', 'piano', 'rocket', 'silver', 'tiger', 'umbrella', 'village', 'whistle', 'yellow', 'zipper', 'anchor', 'butter', 'cactus', 'dragon', 'engine', 'feather', 'granite', 'hammer', 'island', 'jungle', 'kettle', 'ladder', 'magnet', 'napkin', 'orchard', 'pillow', 'quarter', 'ribbon', 'saddle', 'tunnel'];

test('answers are flattened to plain capital letters, with a letter count for the clue', () => {
  assert.deepEqual(normalize('New York'), { letters: 'NEWYORK', count: '3,4' });
  assert.deepEqual(normalize("Rock 'n' Roll"), { letters: 'ROCKNROLL', count: '4,1,4' });
  assert.deepEqual(normalize('  café  '), { letters: 'CAFE', count: '4' });
  assert.deepEqual(normalize('Zoë & José'), { letters: 'ZOEJOSE', count: '3,4' });
  assert.deepEqual(normalize('1999'), { letters: '', count: '' });
});

test('an answer that cannot go in says why', () => {
  assert.equal(problem('A'), 'Needs at least 2 letters.');
  assert.equal(problem('42'), 'Needs at least 2 letters.');
  assert.match(problem('Supercalifragilisticexpialidocious'), /Too long/);
  assert.equal(problem('Paris', new Set(['PARIS'])), 'This answer is in the list twice.');
  assert.equal(problem('Paris'), null);
});

test('the same list and seed give the same puzzle; a new seed gives another', () => {
  const a = build(list(WEDDING), { seed: 7 }), b = build(list(WEDDING), { seed: 7 }), c = build(list(WEDDING), { seed: 8 });
  assert.deepEqual(a, b);
  assert.notDeepEqual(a.words.map((w) => [w.row, w.col]), c.words.map((w) => [w.row, w.col]));
});

test('a wedding list of 18 answers all fit, cross, and pass the referee, on 30 seeds', () => {
  for (let seed = 1; seed <= 30; seed++) {
    const p = build(list(WEDDING), { seed });
    assert.equal(p.words.length, 18, `seed ${seed}`);
    assert.deepEqual(check(p), [], `seed ${seed}`);
    assert.ok(p.crossings >= 17, 'every answer after the first crosses another');
  }
});

test('60 random lists of 3 to 30 answers: every puzzle is sound and nothing goes missing', () => {
  const rand = rng(99);
  for (let i = 0; i < 60; i++) {
    const n = 3 + Math.floor(rand() * 28);
    const words = [...POOL].sort(() => rand() - 0.5).slice(0, n);
    const p = build(list(words), { seed: i + 1, tries: 60 });
    assert.deepEqual(check(p), [], `list ${i}`);
    assert.equal(p.words.length + p.unplaced.length + p.skipped.length, n);
    for (const w of p.words) assert.ok(w.row >= 0 && w.col >= 0);
  }
});

test('the grid leans wider than tall so clues fit underneath', () => {
  let wide = 0;
  for (let seed = 1; seed <= 20; seed++) { const p = build(list(WEDDING), { seed }); if (p.width >= p.height) wide++; }
  assert.ok(wide >= 16, `${wide} of 20`);
});

test('answers that share no letter with the rest are set aside with a reason, not dropped silently', () => {
  const p = build(list(['banana', 'cabana', 'xyz']), { seed: 1 });
  assert.deepEqual(p.words.map((w) => w.letters).sort(), ['BANANA', 'CABANA']);
  assert.equal(p.unplaced.length, 1);
  assert.equal(p.unplaced[0].answer, 'xyz');
  assert.match(p.unplaced[0].why, /no usable letter/);
  assert.deepEqual(check(p), []);
});

test('duplicates, blanks and too-short answers are skipped with a reason', () => {
  const p = build([{ answer: 'Paris' }, { answer: 'paris!' }, { answer: '' }, { answer: 'A' }, { answer: 'Rome' }], { seed: 1 });
  assert.equal(p.words.length, 2);
  assert.deepEqual(p.skipped.map((s) => s.why), ['This answer is in the list twice.', 'Needs at least 2 letters.']);
});

test('one answer and no answers both work', () => {
  const one = build(list(['Hello']), { seed: 1 });
  assert.equal(one.words.length, 1);
  assert.equal(one.words[0].number, 1);
  assert.deepEqual([one.width, one.height], [5, 1]);
  assert.deepEqual(check(one), []);
  const none = build([], { seed: 1 });
  assert.equal(none.words.length, 0);
});

test('numbers run in reading order, and across and down from one square share a number', () => {
  const p = build(list(WEDDING), { seed: 3 });
  const starts = p.words.map((w) => [w.number, w.row, w.col]).sort((a, b) => a[0] - b[0]);
  for (let i = 1; i < starts.length; i++) {
    const [n0, r0, c0] = starts[i - 1], [n1, r1, c1] = starts[i];
    if (n0 === n1) assert.deepEqual([r0, c0], [r1, c1]);
    else assert.ok(r1 > r0 || (r1 === r0 && c1 > c0), 'reading order');
  }
  for (const c of p.cells.filter((x) => x.number)) assert.ok(p.words.some((w) => w.number === c.number && w.row === c.row && w.col === c.col));
});

// ---------- the referee has to catch real faults, or a clean result means nothing ----------

const copy = (p) => JSON.parse(JSON.stringify(p));

test('referee catches two answers clashing on a square', () => {
  const p = copy(build(list(WEDDING), { seed: 1 }));
  const a = p.words.find((w) => w.dir === 'across');
  a.letters = 'Q'.repeat(a.letters.length);
  assert.ok(check(p).some((f) => /clashes/.test(f)));
});

test('referee catches an answer nudged beside another (stray letters)', () => {
  const p = { width: 4, height: 2, words: [{ letters: 'CATS', row: 0, col: 0, dir: 'across', number: 1 }, { letters: 'OWL', row: 1, col: 0, dir: 'across', number: 2 }] };
  assert.ok(check(p).some((f) => /stray letters/.test(f)));
});

test('referee catches a puzzle in two pieces', () => {
  const p = { width: 5, height: 3, words: [{ letters: 'CAT', row: 0, col: 0, dir: 'across', number: 1 }, { letters: 'DOG', row: 2, col: 2, dir: 'across', number: 2 }] };
  assert.deepEqual(check(p), ['the puzzle is in separate pieces']);
});

test('referee catches skipped clue numbers and answers off the grid', () => {
  const p = copy(build(list(['banana', 'cabana']), { seed: 1 }));
  p.words[1].number = 5;
  assert.ok(check(p).includes('clue numbers skip'));
  const q = copy(build(list(['banana', 'cabana']), { seed: 1 }));
  q.width -= 1;
  assert.ok(check(q).some((f) => /runs off the grid/.test(f)));
});

test('30 answers build in well under a second', () => {
  const t = Date.now();
  const p = build(list(POOL.slice(0, 30)), { seed: 5 });
  assert.ok(Date.now() - t < 1500, `${Date.now() - t}ms`);
  assert.ok(p.words.length >= 28);
});

test('a pasted list is split into answers and clues, whatever separator is used', () => {
  assert.deepEqual(parseList('Paris - Honeymoon city\nBiscuit: Our dog\nTacos\tFirst-date dinner\n\n  Jeep  \nRock-and-roll — Our song'), [
    { answer: 'Paris', clue: 'Honeymoon city' }, { answer: 'Biscuit', clue: 'Our dog' }, { answer: 'Tacos', clue: 'First-date dinner' },
    { answer: 'Jeep', clue: '' }, { answer: 'Rock-and-roll', clue: 'Our song' },
  ]);
  assert.deepEqual(parseList(''), []);
});
