// Our Crossword: the puzzle builder. Pure functions, no dependencies.
// Takes a list of answers and clues and lays them out as a real interlocking
// crossword: every answer crosses another, and no two answers ever touch side
// by side to spell something by accident.

// ---------- words ----------

// "New York" -> { letters: 'NEWYORK', count: '3,4' }. Accents are flattened,
// anything that is not a letter is dropped.
export function normalize(answer) {
  const flat = String(answer ?? '').normalize('NFD').replace(/[̀-ͯ]/g, '').toUpperCase();
  const parts = flat.split(/[^A-Z]+/).filter(Boolean);
  return { letters: parts.join(''), count: parts.map((p) => p.length).join(',') };
}

// Why an entry can't go in the puzzle, in words a person can act on. null = fine.
export function problem(answer, seen = new Set()) {
  const { letters } = normalize(answer);
  if (letters.length < 2) return 'Needs at least 2 letters.';
  if (letters.length > 18) return 'Too long. Keep answers to 18 letters.';
  if (seen.has(letters)) return 'This answer is in the list twice.';
  return null;
}

// A pasted list, one per line: "Answer - clue", "Answer: clue" or a tab between them.
export function parseList(text) {
  return String(text).split(/\r?\n/).map((line) => line.trim()).filter(Boolean).map((line) => {
    const m = /^(.+?)\s*(?:\t|\s[-–—]\s|:\s)\s*(.+)$/.exec(line);
    return m ? { answer: m[1].trim(), clue: m[2].trim() } : { answer: line, clue: '' };
  });
}

// Small seeded random source, so the same list and seed always give the same puzzle.
export function rng(seed) {
  let a = (seed >>> 0) || 1;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ---------- one attempt ----------

const SIZE = 64; // working board; answers are placed around the middle
const at = (r, c) => r * SIZE + c;

function attempt(words, rand, shape) {
  const letter = new Array(SIZE * SIZE).fill('');
  const across = new Uint8Array(SIZE * SIZE); // cell is part of an across answer
  const down = new Uint8Array(SIZE * SIZE);
  const byLetter = {}; // letter -> cells holding it
  const placed = [];
  let top = SIZE, left = SIZE, bottom = -1, right = -1, crossings = 0;

  const fits = (w, r, c, dir) => {
    const n = w.length;
    if (r < 1 || c < 1) return -1;
    if (dir === 0) { if (c + n >= SIZE - 1) return -1; if (letter[at(r, c - 1)] || letter[at(r, c + n)]) return -1; }
    else { if (r + n >= SIZE - 1) return -1; if (letter[at(r - 1, c)] || letter[at(r + n, c)]) return -1; }
    let cross = 0;
    for (let i = 0; i < n; i++) {
      const rr = dir === 0 ? r : r + i, cc = dir === 0 ? c + i : c;
      const k = at(rr, cc);
      if (letter[k]) {
        if (letter[k] !== w[i]) return -1;
        if (dir === 0 ? across[k] : down[k]) return -1; // would run along an answer going the same way
        cross++;
      } else if (dir === 0 ? (letter[at(rr - 1, cc)] || letter[at(rr + 1, cc)]) : (letter[at(rr, cc - 1)] || letter[at(rr, cc + 1)])) {
        return -1; // would sit beside another answer and spell something by accident
      }
    }
    return cross;
  };

  const put = (word, r, c, dir, cross) => {
    for (let i = 0; i < word.letters.length; i++) {
      const rr = dir === 0 ? r : r + i, cc = dir === 0 ? c + i : c;
      const k = at(rr, cc);
      if (!letter[k]) { letter[k] = word.letters[i]; (byLetter[word.letters[i]] ||= []).push(k); }
      if (dir === 0) across[k] = 1; else down[k] = 1;
    }
    const r2 = dir === 0 ? r : r + word.letters.length - 1, c2 = dir === 0 ? c + word.letters.length - 1 : c;
    top = Math.min(top, r); left = Math.min(left, c); bottom = Math.max(bottom, r2); right = Math.max(right, c2);
    crossings += cross;
    placed.push({ ...word, row: r, col: c, dir: dir === 0 ? 'across' : 'down' });
  };

  const best = (word) => {
    const w = word.letters;
    let pick = null, pickScore = -Infinity;
    const tried = new Set();
    for (let i = 0; i < w.length; i++) {
      for (const k of byLetter[w[i]] || []) {
        const dir = across[k] ? 1 : 0; // cross the answer that is already there
        if (across[k] && down[k]) continue;
        const r0 = Math.floor(k / SIZE), c0 = k % SIZE;
        const r = dir === 0 ? r0 : r0 - i, c = dir === 0 ? c0 - i : c0;
        const key = (r * SIZE + c) * 2 + dir;
        if (tried.has(key)) continue;
        tried.add(key);
        const cross = fits(w, r, c, dir);
        if (cross < 1) continue;
        const r2 = dir === 0 ? r : r + w.length - 1, c2 = dir === 0 ? c + w.length - 1 : c;
        const h = Math.max(bottom, r2) - Math.min(top, r) + 1, wd = Math.max(right, c2) - Math.min(left, c) + 1;
        const grow = h * wd - (bottom - top + 1) * (right - left + 1);
        const off = Math.abs(Math.log((wd / h) / shape));
        const score = cross * 14 - grow * 0.35 - off * 9 + rand() * 6;
        if (score > pickScore) { pickScore = score; pick = { r, c, dir, cross }; }
      }
    }
    return pick;
  };

  const first = words[0];
  put(first, SIZE >> 1, (SIZE >> 1) - (first.letters.length >> 1), 0, 0);
  let waiting = words.slice(1);
  // Answers that can't cross anything yet get another go after others are down.
  for (let pass = 0; pass < 4 && waiting.length; pass++) {
    const next = [];
    for (const word of waiting) {
      const p = best(word);
      if (p) put(word, p.r, p.c, p.dir, p.cross); else next.push(word);
    }
    if (next.length === waiting.length) break;
    waiting = next;
  }

  const height = bottom - top + 1, width = right - left + 1;
  for (const p of placed) { p.row -= top; p.col -= left; }
  const score = placed.length * 1000 + crossings * 14 - width * height * 0.5 - Math.abs(Math.log((width / height) / shape)) * 60;
  return { width, height, words: placed, unplaced: waiting, crossings, score };
}

// ---------- the builder ----------
//
// entries: [{ answer, clue }]
// options: seed (same seed, same puzzle), tries, shape (width / height to aim for)
// returns { width, height, words: [{ answer, letters, count, clue, row, col, dir, number }],
//           unplaced: [...], skipped: [{ answer, why }], crossings, cells }
export function build(entries, { seed = 1, tries = 220, shape = 1.25 } = {}) {
  const seen = new Set();
  const words = [], skipped = [];
  entries.forEach((e, index) => {
    if (!String(e.answer ?? '').trim()) return;
    const why = problem(e.answer, seen);
    if (why) { skipped.push({ answer: e.answer, why }); return; }
    const n = normalize(e.answer);
    seen.add(n.letters);
    words.push({ index, answer: String(e.answer).trim(), clue: String(e.clue ?? '').trim(), letters: n.letters, count: n.count });
  });
  if (!words.length) return { width: 0, height: 0, words: [], unplaced: [], skipped, crossings: 0, cells: [] };

  const rand = rng(seed);
  let bestRun = null;
  for (let t = 0; t < tries; t++) {
    // Long answers first builds a better spine; shuffle a little so each try differs.
    const order = words.map((w) => ({ w, k: w.letters.length + rand() * (t === 0 ? 0 : 3.5) })).sort((a, b) => b.k - a.k).map((x) => x.w);
    const run = attempt(order, rand, shape);
    if (!bestRun || run.score > bestRun.score) bestRun = run;
  }
  return number(bestRun, skipped);
}

// Standard crossword numbering: left to right, top to bottom; a cell gets a
// number when an answer starts there, shared by across and down.
function number(run, skipped) {
  const starts = new Map();
  for (const w of run.words) {
    const k = w.row * 1000 + w.col;
    if (!starts.has(k)) starts.set(k, 0);
  }
  [...starts.keys()].sort((a, b) => a - b).forEach((k, i) => starts.set(k, i + 1));
  for (const w of run.words) w.number = starts.get(w.row * 1000 + w.col);
  run.words.sort((a, b) => a.number - b.number || (a.dir === 'across' ? -1 : 1));
  const cells = [];
  const grid = new Map();
  for (const w of run.words) {
    for (let i = 0; i < w.letters.length; i++) {
      const r = w.dir === 'across' ? w.row : w.row + i, c = w.dir === 'across' ? w.col + i : w.col;
      const k = r * 1000 + c;
      if (!grid.has(k)) { const cell = { row: r, col: c, letter: w.letters[i], number: i === 0 ? w.number : 0 }; grid.set(k, cell); cells.push(cell); }
      else if (i === 0) grid.get(k).number = w.number;
    }
  }
  cells.sort((a, b) => a.row - b.row || a.col - b.col);
  return { width: run.width, height: run.height, words: run.words, unplaced: run.unplaced.map((w) => ({ answer: w.answer, why: 'Shares no usable letter with the other answers.' })), skipped, crossings: run.crossings, cells };
}

// ---------- the referee ----------
//
// Checks a finished puzzle from scratch, the way a solver would see it.
// Returns a list of faults; an empty list means the puzzle is sound.
export function check(puzzle) {
  const faults = [];
  const grid = new Map();
  for (const w of puzzle.words) {
    for (let i = 0; i < w.letters.length; i++) {
      const r = w.dir === 'across' ? w.row : w.row + i, c = w.dir === 'across' ? w.col + i : w.col;
      if (r < 0 || c < 0 || r >= puzzle.height || c >= puzzle.width) faults.push(`${w.letters} runs off the grid`);
      const k = r * 1000 + c;
      if (grid.has(k) && grid.get(k) !== w.letters[i]) faults.push(`${w.letters} clashes at row ${r}, column ${c}`);
      grid.set(k, w.letters[i]);
    }
  }
  // Every run of two or more letters, across or down, must be exactly one answer.
  const want = new Set(puzzle.words.map((w) => `${w.dir}:${w.row}:${w.col}:${w.letters}`));
  const found = new Set();
  const scan = (dir) => {
    const outer = dir === 'across' ? puzzle.height : puzzle.width, inner = dir === 'across' ? puzzle.width : puzzle.height;
    for (let a = 0; a < outer; a++) {
      let run = '', start = 0;
      for (let b = 0; b <= inner; b++) {
        const ch = b < inner ? grid.get(dir === 'across' ? a * 1000 + b : b * 1000 + a) : undefined;
        if (ch) { if (!run) start = b; run += ch; continue; }
        if (run.length > 1) {
          const key = dir === 'across' ? `across:${a}:${start}:${run}` : `down:${start}:${a}:${run}`;
          if (want.has(key)) found.add(key); else faults.push(`stray letters spell ${run} going ${dir}`);
        }
        run = '';
      }
    }
  };
  scan('across'); scan('down');
  for (const k of want) if (!found.has(k)) faults.push(`${k.split(':')[3]} is not readable in the grid`);
  // Everything must hang together as one puzzle.
  if (puzzle.words.length > 1) {
    const linked = new Set([0]);
    const cellsOf = (w) => Array.from(w.letters, (_, i) => (w.dir === 'across' ? w.row * 1000 + w.col + i : (w.row + i) * 1000 + w.col));
    const sets = puzzle.words.map((w) => new Set(cellsOf(w)));
    for (let grew = true; grew;) {
      grew = false;
      sets.forEach((s, i) => {
        if (linked.has(i)) return;
        for (const j of linked) if ([...s].some((k) => sets[j].has(k))) { linked.add(i); grew = true; break; }
      });
    }
    if (linked.size !== puzzle.words.length) faults.push('the puzzle is in separate pieces');
  }
  // Numbers run in reading order with no gaps.
  const nums = [...new Set(puzzle.words.map((w) => w.number))].sort((a, b) => a - b);
  nums.forEach((n, i) => { if (n !== i + 1) faults.push('clue numbers skip'); });
  return [...new Set(faults)];
}
