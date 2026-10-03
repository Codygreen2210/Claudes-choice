// Our Crossword: page layout. Turns a built puzzle into a list of shapes and
// text for each page, in printer's points (72 to the inch). The same list is
// drawn on screen as a picture and written into the PDF, so what you see is
// what prints. No dependencies; text is measured by a function handed in.

export const SIZES = {
  '5x7': { w: 360, h: 504, label: '5 × 7 in', note: 'table card' },
  '8x10': { w: 576, h: 720, label: '8 × 10 in', note: 'frame' },
  letter: { w: 612, h: 792, label: '8.5 × 11 in', note: 'home printer' },
  a4: { w: 595.28, h: 841.89, label: 'A4', note: 'home printer' },
  '11x14': { w: 792, h: 1008, label: '11 × 14 in', note: 'frame' },
  '18x24': { w: 1296, h: 1728, label: '18 × 24 in', note: 'poster' },
  '24x36': { w: 1728, h: 2592, label: '24 × 36 in', note: 'welcome sign' },
};

export const THEMES = {
  classic: { label: 'Classic', paper: '#ffffff', ink: '#141414', accent: '#141414', cell: '#ffffff', cellInk: '#141414', line: '#141414' },
  garden: { label: 'Garden', paper: '#f7f9f3', ink: '#24352b', accent: '#5b7d61', cell: '#ffffff', cellInk: '#24352b', line: '#5b7d61' },
  blush: { label: 'Blush', paper: '#fcf4f1', ink: '#4a2b2a', accent: '#bf6c62', cell: '#ffffff', cellInk: '#4a2b2a', line: '#bf6c62' },
  midnight: { label: 'Midnight', paper: '#16213a', ink: '#f3ede2', accent: '#d8b46a', cell: '#f8f3e9', cellInk: '#16213a', line: '#d8b46a' },
};

// Break text into lines no wider than `width`. A single word wider than the
// line is left on its own line rather than chopped.
export function wrap(text, width, font, size, measure) {
  const words = String(text).split(/\s+/).filter(Boolean);
  const lines = [];
  let line = '';
  for (const w of words) {
    const trial = line ? `${line} ${w}` : w;
    if (line && measure(trial, font, size) > width) { lines.push(line); line = w; } else line = trial;
  }
  if (line) lines.push(line);
  return lines.length ? lines : [''];
}

// The PDF's built-in fonts only know plain Western letters. Curly quotes and
// long dashes are swapped for plain ones; anything else unknown (emoji) is dropped.
export function clean(s) {
  return String(s ?? '')
    .replace(/[\u2018\u2019\u2032]/g, "'").replace(/[\u201c\u201d\u2033]/g, '"')
    .replace(/[\u2013\u2014]/g, '-').replace(/\u2026/g, '...')
    .replace(/[^\x20-\x7e\u00a1-\u00ff]/g, '').replace(/\s+/g, ' ').trim();
}

// The clue as printed: "Where we met (3,4)" for a two-word answer.
export function clueText(w) {
  const base = clean(w.clue) || '(no clue yet)';
  return w.count.includes(',') ? `${base} (${w.count})` : base;
}

// design: { title, subtitle, footer, theme, size, credit }
// measure(text, font, size) -> width in points
// returns { pages: [{ w, h, items }], overflow, clueSize, cell }
export function layout(puzzle, design, measure) {
  const page = SIZES[design.size] || SIZES.letter;
  const theme = THEMES[design.theme] || THEMES.classic;
  const W = page.w, H = page.h;
  const margin = Math.max(26, W * 0.075);
  const inner = W - margin * 2;
  const textW = (t, font, size, spacing = 0) => measure(t, font, size) + spacing * Math.max(0, t.length - 1);
  const centered = (t, y, font, size, color, spacing = 0) => {
    const w = textW(t, font, size, spacing);
    return { t: 'text', x: (W - w) / 2, y, text: t, font, size, color, spacing, w };
  };
  // Largest size, up to `max`, at which the text fits the line.
  const fit = (t, font, max, spacing = 0, min = max * 0.15) => {
    let s = max;
    while (s > min && textW(t, font, s, spacing * (s / max)) > inner) s *= 0.96;
    return s;
  };

  const head = [];
  let y = margin;
  const title = clean(design.title);
  const subtitle = clean(design.subtitle).toUpperCase();
  if (title) {
    const size = fit(title, 'serif-italic', W * 0.092);
    y += size * 0.82;
    head.push(centered(title, y, 'serif-italic', size, theme.ink));
    y += size * 0.34;
  }
  if (subtitle) {
    const max = W * 0.0215, sp = max * 0.28;
    const size = fit(subtitle, 'sans', max, sp);
    y += size * 1.25;
    head.push(centered(subtitle, y, 'sans', size, theme.accent, sp * (size / max)));
    y += size * 0.9;
  }
  if (title || subtitle) {
    y += W * 0.018;
    const half = W * 0.06;
    head.push({ t: 'line', x1: W / 2 - half, y1: y, x2: W / 2 + half, y2: y, color: theme.accent, sw: Math.max(0.6, W * 0.0016) });
    y += W * 0.03;
  }
  const top = y;

  const footer = clean(design.footer);
  const footSize = W * 0.021;
  const creditSize = Math.max(5, W * 0.0105);
  const bottom = H - margin - (footer ? footSize * 2.2 : 0) - (design.credit ? creditSize * 1.6 : 0);

  const across = puzzle.words.filter((w) => w.dir === 'across');
  const down = puzzle.words.filter((w) => w.dir === 'down');
  const cols = W >= 1100 ? 3 : 2;
  const gap = W * 0.04;
  const colW = (inner - gap * (cols - 1)) / cols;

  // Flow the clues into columns at a given type size. Returns the blocks and
  // whether they fit the height available.
  const flow = (size, room) => {
    const lead = size * 1.32;
    const numW = measure('00.', 'sans-bold', size) + size * 0.35;
    const blocks = [];
    for (const [name, list] of [['ACROSS', across], ['DOWN', down]]) {
      if (!list.length) continue;
      blocks.push({ head: name, h: lead * 1.5, space: blocks.length ? lead * 0.7 : 0 });
      for (const w of list) {
        const lines = wrap(clueText(w), colW - numW, 'serif', size, measure);
        blocks.push({ num: `${w.number}.`, lines, h: lines.length * lead + size * 0.22 });
      }
    }
    // Fill each column up to an even share, keeping a heading with its first clue.
    const total = blocks.reduce((s, b) => s + b.h + (b.space || 0), 0);
    const target = total / cols;
    const columns = [[]];
    let used = 0;
    blocks.forEach((b, i) => {
      const need = b.h + (b.head ? (blocks[i + 1] ? blocks[i + 1].h : 0) : 0);
      const here = columns[columns.length - 1];
      if (here.length && columns.length < cols && used + need > target * 1.04) { columns.push([]); used = 0; }
      const col = columns[columns.length - 1];
      const space = col.length ? (b.space || 0) : 0;
      col.push({ ...b, y: used + space });
      used += space + b.h;
    });
    const tall = Math.max(...columns.map((c) => (c.length ? c[c.length - 1].y + c[c.length - 1].h : 0)));
    return { columns, tall, lead, numW, size, ok: tall <= room };
  };

  // Give the grid as much of the page as the clues can spare.
  const maxCell = W * 0.072;
  const clueMax = W * 0.027, clueMin = Math.max(5.2, W * 0.0128);
  let chosen = null;
  for (const share of [0.5, 0.44, 0.38, 0.32, 0.27]) {
    const gridH = (bottom - top) * share;
    const cell = Math.min(inner / puzzle.width, gridH / puzzle.height, maxCell);
    const gridBottom = top + cell * puzzle.height;
    const room = bottom - gridBottom - W * 0.05;
    for (let size = clueMax; size >= clueMin; size *= 0.95) {
      const f = flow(size, room);
      if (f.ok) { chosen = { cell, f, gridBottom }; break; }
    }
    if (chosen) break;
    if (share === 0.27) chosen = { cell, f: flow(clueMin, room), gridBottom, overflow: true };
  }

  const { cell, f, gridBottom } = chosen;
  const gx = (W - cell * puzzle.width) / 2;
  const sw = Math.max(0.5, cell * 0.035);
  const grid = (answers) => {
    const items = [];
    for (const c of puzzle.cells) {
      const x = gx + c.col * cell, yy = top + c.row * cell;
      items.push({ t: 'rect', x, y: yy, w: cell, h: cell, fill: theme.cell, stroke: theme.line, sw });
      if (c.number) items.push({ t: 'text', x: x + cell * 0.08, y: yy + cell * 0.31, text: String(c.number), font: 'sans', size: cell * 0.26, color: theme.cellInk, spacing: 0, w: measure(String(c.number), 'sans', cell * 0.26) });
      if (answers) {
        const s = cell * 0.56, w = measure(c.letter, 'sans-bold', s);
        items.push({ t: 'text', x: x + (cell - w) / 2, y: yy + cell * 0.8, text: c.letter, font: 'sans-bold', size: s, color: theme.cellInk, spacing: 0, w });
      }
    }
    return items;
  };

  const clues = [];
  const cy = gridBottom + W * 0.05;
  f.columns.forEach((col, i) => {
    const cx = margin + i * (colW + gap);
    for (const b of col) {
      if (b.head) {
        const sp = f.size * 0.22;
        clues.push({ t: 'text', x: cx, y: cy + b.y + f.lead * 0.95, text: b.head, font: 'sans-bold', size: f.size * 0.86, color: theme.accent, spacing: sp, w: textW(b.head, 'sans-bold', f.size * 0.86, sp) });
        continue;
      }
      clues.push({ t: 'text', x: cx, y: cy + b.y + f.lead * 0.8, text: b.num, font: 'sans-bold', size: f.size * 0.9, color: theme.ink, spacing: 0, w: measure(b.num, 'sans-bold', f.size * 0.9) });
      b.lines.forEach((ln, j) => clues.push({ t: 'text', x: cx + f.numW, y: cy + b.y + f.lead * (0.8 + j), text: ln, font: 'serif', size: f.size, color: theme.ink, spacing: 0, w: measure(ln, 'serif', f.size) }));
    }
  });

  const foot = [];
  if (footer) foot.push(centered(footer, H - margin - (design.credit ? creditSize * 1.6 : 0), 'serif-italic', fit(footer, 'serif-italic', footSize), theme.ink));
  if (design.credit) foot.push(centered(design.credit, H - margin * 0.62, 'sans', creditSize, theme.accent, creditSize * 0.08));

  // A short puzzle would sit high on the page with a blank bottom half.
  // Slide the whole block down so the space is shared above and below.
  const spare = chosen.overflow ? 0 : Math.max(0, bottom - (cy + f.tall));
  const dy = spare * 0.42;
  const lower = (it) => (it.t === 'line' ? { ...it, y1: it.y1 + dy, y2: it.y2 + dy } : { ...it, y: it.y + dy });

  const paper = { t: 'rect', x: 0, y: 0, w: W, h: H, fill: theme.paper, stroke: null, sw: 0 };
  const puzzlePage = { w: W, h: H, items: [paper, ...[...head, ...grid(false), ...clues].map(lower), ...foot] };

  // Answer key: the same grid, filled in, as large as the page allows.
  const keyHead = [];
  let ky = margin + W * 0.05;
  keyHead.push(centered('ANSWER KEY', ky, 'sans-bold', W * 0.026, theme.accent, W * 0.008));
  if (title) { ky += W * 0.062; keyHead.push(centered(title, ky, 'serif-italic', fit(title, 'serif-italic', W * 0.05), theme.ink)); }
  ky += W * 0.05;
  const kCell = Math.min(inner / puzzle.width, (H - margin - ky) / puzzle.height, maxCell * 1.25);
  const kx = (W - kCell * puzzle.width) / 2;
  const keyItems = grid(true).map((it) => {
    const s = kCell / cell;
    return { ...it, x: kx + (it.x - gx) * s, y: ky + (it.y - top) * s, ...(it.t === 'rect' ? { w: kCell, h: kCell, sw: it.sw * s } : { size: it.size * s, w: it.w * s }) };
  });
  const keyPage = { w: W, h: H, items: [paper, ...keyHead, ...keyItems] };

  return { pages: [puzzlePage, keyPage], overflow: !!chosen.overflow, clueSize: f.size, cell };
}

// ---------- drawing ----------

const FAMILY = {
  serif: ['"Times New Roman", Times, "Nimbus Roman", "Liberation Serif", serif', 'normal', 'normal'],
  'serif-italic': ['"Times New Roman", Times, "Nimbus Roman", "Liberation Serif", serif', 'italic', 'normal'],
  'serif-bold': ['"Times New Roman", Times, "Nimbus Roman", "Liberation Serif", serif', 'normal', 'bold'],
  sans: ['Helvetica, Arial, "Nimbus Sans", "Liberation Sans", sans-serif', 'normal', 'normal'],
  'sans-bold': ['Helvetica, Arial, "Nimbus Sans", "Liberation Sans", sans-serif', 'normal', 'bold'],
};
const xml = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const n2 = (v) => Math.round(v * 100) / 100;

// One page as an SVG picture. Each line of text is pinned to the width it was
// measured at, so the screen matches the PDF even when the device lacks the font.
export function toSvg(page, { watermark } = {}) {
  const out = [`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${n2(page.w)} ${n2(page.h)}" role="img" aria-label="Crossword page preview">`];
  for (const it of page.items) {
    if (it.t === 'rect') out.push(`<rect x="${n2(it.x)}" y="${n2(it.y)}" width="${n2(it.w)}" height="${n2(it.h)}" fill="${it.fill || 'none'}"${it.stroke ? ` stroke="${it.stroke}" stroke-width="${n2(it.sw)}"` : ''}/>`);
    else if (it.t === 'line') out.push(`<line x1="${n2(it.x1)}" y1="${n2(it.y1)}" x2="${n2(it.x2)}" y2="${n2(it.y2)}" stroke="${it.color}" stroke-width="${n2(it.sw)}"/>`);
    else if (it.text) {
      const [family, style, weight] = FAMILY[it.font];
      out.push(`<text x="${n2(it.x)}" y="${n2(it.y)}" font-family='${family}' font-style="${style}" font-weight="${weight}" font-size="${n2(it.size)}" fill="${it.color}"${it.w > 0.5 ? ` textLength="${n2(it.w)}" lengthAdjust="${it.spacing ? 'spacing' : 'spacingAndGlyphs'}"` : ''}>${xml(it.text)}</text>`);
    }
  }
  if (watermark) {
    const s = page.w * 0.11;
    out.push(`<text x="${n2(page.w / 2)}" y="${n2(page.h * 0.52)}" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" font-weight="bold" font-size="${n2(s)}" fill="#808080" fill-opacity="0.2" transform="rotate(-28 ${n2(page.w / 2)} ${n2(page.h / 2)})">${xml(watermark)}</text>`);
  }
  out.push('</svg>');
  return out.join('');
}

const PDF_FONT = { serif: ['times', 'normal'], 'serif-italic': ['times', 'italic'], 'serif-bold': ['times', 'bold'], sans: ['helvetica', 'normal'], 'sans-bold': ['helvetica', 'bold'] };

// A text measurer backed by the PDF library's own font tables.
export function measurer(JsPDF) {
  const doc = new JsPDF({ unit: 'pt', format: [100, 100] });
  return (text, font, size) => {
    doc.setFont(...PDF_FONT[font]);
    doc.setFontSize(size);
    return doc.getTextWidth(String(text));
  };
}

// The pages as a vector PDF at the exact paper size.
export function toPdf(pages, JsPDF) {
  const first = pages[0];
  const doc = new JsPDF({ unit: 'pt', format: [first.w, first.h], orientation: first.w > first.h ? 'landscape' : 'portrait', compress: true });
  pages.forEach((page, i) => {
    if (i) doc.addPage([page.w, page.h], page.w > page.h ? 'landscape' : 'portrait');
    for (const it of page.items) {
      if (it.t === 'rect') {
        if (it.fill) doc.setFillColor(it.fill);
        if (it.stroke) { doc.setDrawColor(it.stroke); doc.setLineWidth(it.sw); }
        doc.rect(it.x, it.y, it.w, it.h, it.fill && it.stroke ? 'FD' : it.fill ? 'F' : 'S');
      } else if (it.t === 'line') {
        doc.setDrawColor(it.color); doc.setLineWidth(it.sw);
        doc.line(it.x1, it.y1, it.x2, it.y2);
      } else if (it.text) {
        doc.setFont(...PDF_FONT[it.font]);
        doc.setFontSize(it.size);
        doc.setTextColor(it.color);
        doc.text(it.text, it.x, it.y, it.spacing ? { charSpace: it.spacing } : undefined);
      }
    }
  });
  return doc;
}
