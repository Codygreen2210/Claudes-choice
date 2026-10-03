// Planner Press: page layout. Turns one planned page into a list of shapes and
// text (in points, 72 to the inch) plus a list of links. The same list is drawn
// on screen as an SVG picture and written into the PDF, so the preview is the
// file. No dependencies; text is measured by a function handed in.
import { MONTHS, WEEKDAYS, daysInMonth, weekday } from './dates.js';

export const PAGE = {
  landscape: { w: 842, h: 595 },
  portrait: { w: 595, h: 842 },
};

export const THEMES = {
  classic: { label: 'Classic', paper: '#ffffff', ink: '#1f2933', muted: '#6b7785', accent: '#2f5d8a', accentInk: '#ffffff', line: '#c9d1da', cell: '#ffffff', dim: '#f1f4f7', tab: '#e3eaf1', tabInk: '#2f5d8a', soft: '#dce8f4' },
  sage: { label: 'Sage', paper: '#f8f6ef', ink: '#2b3a2f', muted: '#6d7a6c', accent: '#5b7d61', accentInk: '#ffffff', line: '#cfd6c4', cell: '#fffdf8', dim: '#eeeadd', tab: '#dfe6d3', tabInk: '#3f5c45', soft: '#dbe6d2' },
  rose: { label: 'Rose', paper: '#fdf6f3', ink: '#4a2b2f', muted: '#85686b', accent: '#b4566a', accentInk: '#ffffff', line: '#ecd3d2', cell: '#fffefd', dim: '#f7e9e6', tab: '#f4dcdc', tabInk: '#9a3f55', soft: '#f6dbe0' },
  night: { label: 'Night', paper: '#161d2e', ink: '#eef1f7', muted: '#9aa6bd', accent: '#e0b861', accentInk: '#161d2e', line: '#35405a', cell: '#1c2438', dim: '#121827', tab: '#2a3550', tabInk: '#e0b861', soft: '#303b58' },
};

const M = 28; // outer margin
const TAB = 40; // width of the tab column on the right edge
const CREDIT_ROOM = 16; // always kept free at the bottom so paid and free pages line up

export const contentBox = (orientation) => {
  const { w, h } = PAGE[orientation];
  return { x: M, y: M, r: w - TAB - M, b: h - M - CREDIT_ROOM };
};

const short = (name) => name.slice(0, 3);
const longDate = (d) => `${MONTHS[d.m - 1]} ${d.d}, ${d.y}`;

// opts: { theme, credit }   measure(text, font, size) -> width in points
// returns { w, h, kind, number, items, links }
export function layoutPage(plan, index, measure, opts = {}) {
  const pg = plan.pages[index];
  const { w: W, h: H } = PAGE[plan.orientation];
  const T = THEMES[opts.theme] || THEMES.classic;
  const C = contentBox(plan.orientation);
  const CW = C.r - C.x;
  const land = plan.orientation === 'landscape';
  const items = [];
  const links = [];

  const rect = (x, y, w, h, o = {}) => items.push({ t: 'rect', x, y, w, h, fill: o.fill, stroke: o.stroke, sw: o.sw ?? 0.6, nav: o.nav });
  const line = (x1, y1, x2, y2, color = T.line, sw = 0.6) => items.push({ t: 'line', x1, y1, x2, y2, color, sw });
  // Text with its baseline at y. align: left | center | right, relative to x. maxW shrinks the type to fit.
  const text = (str, x, y, o = {}) => {
    const font = o.font || 'sans';
    let size = o.size || 10;
    if (o.maxW) while (size > 5 && measure(str, font, size) > o.maxW) size *= 0.95;
    const w = measure(str, font, size);
    const left = o.align === 'center' ? x - w / 2 : o.align === 'right' ? x - w : x;
    items.push({ t: 'text', x: left, y, text: str, font, size, color: o.color || T.ink, w, nav: o.nav });
  };
  const link = (x, y, w, h, page, kind, key) => { if (page) links.push({ x, y, w, h, page, kind, key: String(key) }); };

  rect(0, 0, W, H, { fill: T.paper });

  // ----- tab column (every page) -----
  const tabs = [{ label: plan.homeLabel, page: plan.homeTarget, kind: 'tab-home', key: 'home', active: pg.kind === 'year' }];
  const activeMonth = pg.kind === 'month' ? pg.month : pg.kind === 'week' ? plan.weekMonth({ days: pg.days }) : pg.kind === 'day' ? pg.date.m : 0;
  for (let m = 1; m <= 12; m++) {
    const target = plan.monthTarget(m);
    if (target) tabs.push({ label: short(MONTHS[m - 1]).toUpperCase(), page: target, kind: 'tab-month', key: m, active: m === activeMonth });
  }
  if (plan.notesTarget) tabs.push({ label: 'NOTES', page: plan.notesTarget, kind: 'tab-notes', key: 'notes', active: pg.kind === 'notes' });
  const th = Math.min(48, (H - 2 * M) / tabs.length);
  tabs.forEach((t, i) => {
    const y = M + i * th;
    rect(W - TAB, y + 1.5, TAB, th - 3, { fill: t.active ? T.accent : T.tab, nav: true });
    text(t.label, W - TAB / 2, y + th / 2 + 3, { font: 'sans-bold', size: 8, color: t.active ? T.accentInk : T.tabInk, align: 'center', maxW: TAB - 6, nav: true });
    link(W - TAB, y + 1.5, TAB, th - 3, t.page, t.kind, t.key);
  });

  if (opts.credit) text(opts.credit, (C.x + C.r) / 2, H - M + 2, { size: 7.5, color: T.muted, align: 'center' });

  const header = (title, sub, o = {}) => {
    text(title, C.x, C.y + 26, { font: 'serif-bold', size: o.size || 30, color: T.ink, maxW: o.maxW || CW });
    if (sub) text(sub, C.x, C.y + 44, { size: 11, color: T.muted, maxW: o.maxW || CW });
  };
  const bodyTop = C.y + 58;

  // ----- year at a glance -----
  if (pg.kind === 'year') {
    header(String(plan.year), 'Year at a glance. Tap a month name to open it.');
    const cols = land ? 4 : 3, rows = land ? 3 : 4;
    const gx = 14, gy = land ? 10 : 8;
    const cellW = (CW - gx * (cols - 1)) / cols;
    const cellH = (C.b - bodyTop - gy * (rows - 1)) / rows;
    for (let m = 1; m <= 12; m++) {
      const col = (m - 1) % cols, row = Math.floor((m - 1) / cols);
      const x = C.x + col * (cellW + gx), y = bodyTop + row * (cellH + gy);
      const lead = (weekday(plan.year, m, 1) - plan.weekStart + 7) % 7;
      rect(x, y, cellW, cellH, { fill: T.cell, stroke: T.line });
      rect(x, y, cellW, 20, { fill: T.soft });
      text(MONTHS[m - 1], x + 8, y + 14, { font: 'sans-bold', size: 11, color: T.tabInk });
      link(x, y, cellW, 20, plan.monthTarget(m), 'year-month', m);
      const dx = (cellW - 10) / 7;
      for (let c = 0; c < 7; c++) text(WEEKDAYS[(plan.weekStart + c) % 7][0], x + 5 + c * dx + dx / 2, y + 31, { size: 7, color: T.muted, align: 'center' });
      const dh = (cellH - 36) / 6;
      const n = daysInMonth(plan.year, m);
      for (let k = 0; k < n; k++) {
        const pos = lead + k;
        text(String(k + 1), x + 5 + (pos % 7) * dx + dx / 2, y + 36 + Math.floor(pos / 7) * dh + dh / 2 + 3, { size: 8, align: 'center' });
      }
    }
  }

  // ----- month -----
  if (pg.kind === 'month') {
    header(MONTHS[pg.month - 1], String(plan.year));
    const gridTop = bodyTop + 16;
    const rows = pg.rows.length;
    const cw = CW / 7, ch = (C.b - gridTop) / rows;
    for (let c = 0; c < 7; c++) text(WEEKDAYS[(plan.weekStart + c) % 7].toUpperCase().slice(0, 3), C.x + c * cw + cw / 2, gridTop - 5, { font: 'sans-bold', size: 8.5, color: T.muted, align: 'center' });
    pg.rows.forEach((row, r) => row.forEach((d, c) => {
      const x = C.x + c * cw, y = gridTop + r * ch;
      rect(x, y, cw, ch, { fill: d ? T.cell : T.dim, stroke: T.line });
      if (!d) return;
      const numTarget = plan.dayNumberTarget(d.iso);
      const bodyTarget = plan.dayBodyTarget(d.iso);
      if (numTarget) rect(x + 3, y + 3, 28, 18, { fill: T.soft });
      text(String(d.d), x + 17, y + 16, { font: 'sans-bold', size: 11, color: numTarget ? T.tabInk : T.ink, align: 'center' });
      link(x + 3, y + 3, 28, 18, numTarget, 'day-num', d.iso);
      if (bodyTarget) link(x, y + 23, cw, ch - 23, bodyTarget, 'day-body', d.iso);
    }));
  }

  // ----- week -----
  if (pg.kind === 'week') {
    const first = pg.days[0], lastD = pg.days[6];
    const range = first.m === lastD.m ? `${MONTHS[first.m - 1]} ${first.d} - ${lastD.d}, ${lastD.y}` : first.y === lastD.y ? `${MONTHS[first.m - 1]} ${first.d} - ${MONTHS[lastD.m - 1]} ${lastD.d}, ${lastD.y}` : `${MONTHS[first.m - 1]} ${first.d}, ${first.y} - ${MONTHS[lastD.m - 1]} ${lastD.d}, ${lastD.y}`;
    header(`Week ${pg.week}`, range);
    const notesH = land ? 78 : 96;
    const top = bodyTop, bottom = C.b - notesH - 10;
    const dayHead = (d, x, y, w, h, vertical) => {
      const inYear = d.y === plan.year;
      const target = inYear ? plan.weekDayTarget(d.iso) : null;
      rect(x, y, w, h, { fill: inYear ? T.soft : T.dim });
      const col = inYear ? T.tabInk : T.muted;
      const name = WEEKDAYS[d.dow].toUpperCase().slice(0, 3);
      const num = inYear ? String(d.d) : `${short(MONTHS[d.m - 1])} ${d.d}`;
      if (vertical) {
        text(name, x + w / 2, y + 14, { font: 'sans-bold', size: 8.5, color: col, align: 'center' });
        text(num, x + w / 2, y + 31, { font: 'sans-bold', size: inYear ? 16 : 11, color: col, align: 'center', maxW: w - 6 });
      } else {
        text(name, x + 8, y + 16, { font: 'sans-bold', size: 8.5, color: col, maxW: w - 12 });
        text(num, x + 8, y + 38, { font: 'sans-bold', size: inYear ? 18 : 12, color: col, maxW: w - 12 });
      }
      link(x, y, w, h, target, 'week-day', d.iso);
    };
    if (land) {
      const cw = CW / 7, hh = 40;
      pg.days.forEach((d, i) => {
        const x = C.x + i * cw;
        rect(x, top, cw, bottom - top, { fill: T.cell, stroke: T.line });
        dayHead(d, x, top, cw, hh, true);
        for (let y = top + hh + 24; y < bottom - 4; y += 24) line(x + 6, y, x + cw - 6, y);
      });
    } else {
      const rh = (bottom - top) / 7, hw = 74;
      pg.days.forEach((d, i) => {
        const y = top + i * rh;
        rect(C.x, y, CW, rh, { fill: T.cell, stroke: T.line });
        dayHead(d, C.x, y, hw, rh, false);
        for (let ly = y + 22; ly < y + rh - 4; ly += 22) line(C.x + hw + 8, ly, C.r - 8, ly);
      });
    }
    const ny = C.b - notesH;
    rect(C.x, ny, CW, notesH, { fill: T.cell, stroke: T.line });
    text('WEEK NOTES', C.x + 8, ny + 14, { font: 'sans-bold', size: 8.5, color: T.muted });
    for (let y = ny + 36; y < C.b - 4; y += 22) line(C.x + 8, y, C.r - 8, y);
  }

  // ----- day -----
  if (pg.kind === 'day') {
    const d = pg.date;
    header(WEEKDAYS[d.dow], longDate(d), { maxW: CW - 110 });
    const wk = plan.dayWeekTarget(d.iso);
    if (wk) {
      const label = `< Week ${plan.weekNumberOf(d.iso)}`;
      rect(C.r - 96, C.y + 6, 96, 24, { fill: T.soft });
      text(label, C.r - 48, C.y + 22, { font: 'sans-bold', size: 10, color: T.tabInk, align: 'center', maxW: 88 });
      link(C.r - 96, C.y + 6, 96, 24, wk, 'day-week', d.iso);
    }
    const top = bodyTop, bottom = C.b;
    const gap = 16;
    const leftW = land ? CW * 0.58 : CW * 0.52;
    const rx = C.x + leftW + gap, rw = CW - leftW - gap;
    // schedule, 6 AM to 9 PM
    text('SCHEDULE', C.x, top + 8, { font: 'sans-bold', size: 8.5, color: T.muted });
    const hours = 16, st = top + 16, rh = (bottom - st) / hours;
    rect(C.x, st, leftW, bottom - st, { fill: T.cell, stroke: T.line });
    for (let i = 0; i < hours; i++) {
      const y = st + i * rh;
      if (i) line(C.x, y, C.x + leftW, y);
      const hr = 6 + i;
      text(`${hr > 12 ? hr - 12 : hr} ${hr >= 12 ? 'PM' : 'AM'}`, C.x + 8, y + Math.min(rh - 4, 14), { size: 8, color: T.muted });
    }
    line(C.x + 46, st, C.x + 46, bottom);
    // to do
    text('TO DO', rx, top + 8, { font: 'sans-bold', size: 8.5, color: T.muted });
    const todoRows = land ? 8 : 7;
    const trh = 26;
    rect(rx, st, rw, trh * todoRows, { fill: T.cell, stroke: T.line });
    for (let i = 0; i < todoRows; i++) {
      const y = st + i * trh;
      if (i) line(rx, y, rx + rw, y);
      rect(rx + 8, y + 8, 10, 10, { stroke: T.muted, sw: 0.8 });
    }
    // notes
    const ny = st + trh * todoRows + 18;
    text('NOTES', rx, ny - 6, { font: 'sans-bold', size: 8.5, color: T.muted });
    rect(rx, ny, rw, bottom - ny, { fill: T.cell, stroke: T.line });
    for (let y = ny + 24; y < bottom - 4; y += 24) line(rx + 8, y, rx + rw - 8, y);
  }

  // ----- notes -----
  if (pg.kind === 'notes') {
    header('Notes', `Page ${pg.n} of ${plan.at.notes.length}`);
    for (let y = bodyTop + 14; y < C.b - 2; y += 26) line(C.x, y, C.r, y);
  }

  return { w: W, h: H, kind: pg.kind, number: pg.number, items, links };
}

export function layoutAll(plan, measure, opts) {
  return plan.pages.map((_, i) => layoutPage(plan, i, measure, opts));
}

// ---------- drawing ----------

const FAMILY = {
  serif: ['"Times New Roman", Times, "Nimbus Roman", "Liberation Serif", serif', 'normal', 'normal'],
  'serif-bold': ['"Times New Roman", Times, "Nimbus Roman", "Liberation Serif", serif', 'normal', 'bold'],
  sans: ['Helvetica, Arial, "Nimbus Sans", "Liberation Sans", sans-serif', 'normal', 'normal'],
  'sans-bold': ['Helvetica, Arial, "Nimbus Sans", "Liberation Sans", sans-serif', 'normal', 'bold'],
};
const xml = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const n2 = (v) => Math.round(v * 100) / 100;

// One page as an SVG picture. Each line of text is pinned to the width it was
// measured at, so the screen matches the PDF even when the device lacks the font.
// With links: true, each link is an invisible tappable box carrying data-page.
export function toSvg(page, { links = false } = {}) {
  const out = [`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${n2(page.w)} ${n2(page.h)}" role="img" aria-label="Planner page preview">`];
  for (const it of page.items) {
    if (it.t === 'rect') out.push(`<rect x="${n2(it.x)}" y="${n2(it.y)}" width="${n2(it.w)}" height="${n2(it.h)}" fill="${it.fill || 'none'}"${it.stroke ? ` stroke="${it.stroke}" stroke-width="${n2(it.sw)}"` : ''}/>`);
    else if (it.t === 'line') out.push(`<line x1="${n2(it.x1)}" y1="${n2(it.y1)}" x2="${n2(it.x2)}" y2="${n2(it.y2)}" stroke="${it.color}" stroke-width="${n2(it.sw)}"/>`);
    else if (it.text) {
      const [family, style, weight] = FAMILY[it.font];
      out.push(`<text x="${n2(it.x)}" y="${n2(it.y)}" font-family='${family}' font-style="${style}" font-weight="${weight}" font-size="${n2(it.size)}" fill="${it.color}"${it.w > 0.5 ? ` textLength="${n2(it.w)}" lengthAdjust="spacingAndGlyphs"` : ''}>${xml(it.text)}</text>`);
    }
  }
  if (links) for (const l of page.links) out.push(`<rect class="lnk" data-page="${l.page}" x="${n2(l.x)}" y="${n2(l.y)}" width="${n2(l.w)}" height="${n2(l.h)}" fill="transparent"/>`);
  out.push('</svg>');
  return out.join('');
}

const PDF_FONT = { serif: ['times', 'normal'], 'serif-bold': ['times', 'bold'], sans: ['helvetica', 'normal'], 'sans-bold': ['helvetica', 'bold'] };

// A text measurer backed by the PDF library's own font tables.
export function measurer(JsPDF) {
  const doc = new JsPDF({ unit: 'pt', format: [100, 100] });
  return (text, font, size) => {
    doc.setFont(...PDF_FONT[font]);
    doc.setFontSize(size);
    return doc.getTextWidth(String(text));
  };
}

// The pages as a vector PDF with real internal links.
export function toPdf(pages, JsPDF, { title = 'Planner' } = {}) {
  const first = pages[0];
  const orient = (p) => (p.w > p.h ? 'landscape' : 'portrait');
  const doc = new JsPDF({ unit: 'pt', format: [first.w, first.h], orientation: orient(first), compress: true });
  doc.setProperties({ title });
  pages.forEach((page, i) => {
    if (i) doc.addPage([page.w, page.h], orient(page));
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
        doc.text(it.text, it.x, it.y);
      }
    }
    for (const l of page.links) doc.link(l.x, l.y, l.w, l.h, { pageNumber: l.page });
  });
  return doc;
}
