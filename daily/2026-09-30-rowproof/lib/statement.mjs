// Turns positioned text into bank transactions, then proves them against the statement's
// own numbers. Several readings of the columns are tried; the one the bank's printed
// balances agree with wins. No guessing is hidden: every row says how it was checked.

// ---------- lines and cells ----------
export function toLines(pages) {
  const out = [];
  pages.forEach((p, pi) => {
    // One piece of text holding several columns ("01/04  Coffee   5.00") gets split on runs of
    // 2+ spaces, with positions shared out by character count (exact for fixed-width fonts).
    const pieces = [];
    for (const it of p.items) {
      if (!/\S\s{2,}\S/.test(it.str)) { pieces.push(it); continue; }
      const per = (it.x2 - it.x) / it.str.length;
      for (const m of it.str.matchAll(/\S+(?: \S+)*/g)) pieces.push({ ...it, x: it.x + m.index * per, x2: it.x + (m.index + m[0].length) * per, str: m[0] });
    }
    const items = pieces.sort((a, b) => b.y - a.y || a.x - b.x);
    const rows = [];
    for (const it of items) {
      const r = rows.find((row) => Math.abs(row.y - it.y) <= 0.45 * Math.max(row.size, it.size));
      if (r) { r.items.push(it); r.size = Math.max(r.size, it.size); }
      else rows.push({ y: it.y, size: it.size, items: [it] });
    }
    rows.sort((a, b) => b.y - a.y);
    for (const r of rows) {
      r.items.sort((a, b) => a.x - b.x);
      const cells = [];
      for (const it of r.items) {
        const c = cells.at(-1);
        const gap = c ? it.x - c.x2 : Infinity;
        const em = Math.max(it.size, 1);
        if (c && gap < 0.9 * em && !(isAmount(c.parts.at(-1).s.trim()) && gap > 0.12 * em) && !(isAmount(it.str.trim()) && gap > 0.12 * em)) {
          c.parts.push({ s: it.str, gap }); c.x2 = Math.max(c.x2, it.x2);
        } else cells.push({ x: it.x, x2: it.x2, parts: [{ s: it.str, gap: 0 }] });
      }
      for (const c of cells) c.t = joinParts(c.parts, r.size);
      out.push({ page: pi + 1, y: r.y, size: r.size, cells: splitTrailingAmounts(cells.filter((c) => c.t).map(({ x, x2, t }) => ({ x, x2, t }))) });
    }
  });
  return out;
}

// Decide where the spaces go between pieces. Letter-spaced text ("O P E N I N G") is drawn one
// letter at a time with even gaps; a word break is a gap clearly wider than the letter gaps.
function joinParts(parts, size) {
  const singles = parts.filter((p, k) => k > 0 && p.s.trim().length <= 2).map((p) => p.gap);
  const spaced = parts.length >= 4 && singles.length >= parts.length * 0.6;
  const sorted = [...singles].sort((a, b) => a - b);
  const unit = spaced ? Math.max(sorted[Math.floor(sorted.length / 2)], 0) : 0; // typical letter gap (often 0)
  let t = '';
  parts.forEach((p, k) => {
    if (k === 0) { t = p.s; return; }
    const brk = spaced ? p.gap > unit * 1.5 + 0.1 * size : p.gap >= 0.12 * size;
    t += brk && !/\s$/.test(t) && !/^\s/.test(p.s) ? ' ' + p.s : p.s;
  });
  return t.replace(/\s+/g, ' ').trim();
}

// "SHELL OIL 12.50" drawn as one piece: split the amount off, estimating its position.
function splitTrailingAmounts(cells) {
  const out = [];
  for (const c of cells) {
    const m = /^(.*\S)\s+(\(?[-+]?[$£€]?-?[\d,]+\.\d{2}\)?-?(?:\s?(?:CR|DR|OD))?)$/i.exec(c.t);
    if (m && !isAmount(c.t) && parseAmount(m[2]) != null) {
      const cut = c.x + (c.x2 - c.x) * ((m[1].length + 1) / c.t.length);
      out.push({ x: c.x, x2: cut, t: m[1] }, { x: cut, x2: c.x2, t: m[2] });
    } else out.push(c);
  }
  return out;
}

// ---------- amounts ----------
export function parseAmount(t) {
  let s = String(t).replace(/\s+/g, '');
  let neg = false;
  const suf = /(CR|DR|OD)$/i.exec(s);
  if (suf) { if (/DR|OD/i.test(suf[1])) neg = true; s = s.slice(0, -2); }
  if (/^\(.*\)$/.test(s)) { neg = true; s = s.slice(1, -1); }
  if (s.endsWith('-')) { neg = true; s = s.slice(0, -1); }
  if (s.startsWith('-')) { neg = true; s = s.slice(1); } else if (s.startsWith('+')) s = s.slice(1);
  s = s.replace(/^[$£€]/, '');
  if (s.startsWith('-')) { neg = true; s = s.slice(1); }
  if (!/^(\d{1,3}(,\d{3})+|\d+)\.\d{2}$/.test(s)) return null;
  const v = Number(s.replace(/,/g, ''));
  return neg ? -v : v;
}
const isAmount = (t) => parseAmount(t) != null;

// ---------- dates ----------
const MON = { jan: 1, feb: 2, mar: 3, apr: 4, may: 5, jun: 6, jul: 7, aug: 8, sep: 9, oct: 10, nov: 11, dec: 12 };
const MONRE = '(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\\.?';
const DATE_RES = [
  [/^(\d{4})-(\d{1,2})-(\d{1,2})(?![\d])/, (m) => ({ y: +m[1], a: +m[2], b: +m[3], iso: true })],
  [/^(\d{1,2})[/-](\d{1,2})(?:[/-](\d{4}|\d{2}))?(?![\d/.-])/, (m) => ({ a: +m[1], b: +m[2], y: yr(m[3]), num: true })],
  [/^(\d{1,2})\.(\d{1,2})\.(\d{4}|\d{2})(?![\d])/, (m) => ({ a: +m[1], b: +m[2], y: yr(m[3]), num: true })],
  [new RegExp('^(\\d{1,2})[ -]?' + MONRE + '(?:[ -,]+(\\d{4}|\\d{2}))?(?![a-z\\d])', 'i'), (m) => ({ m: MON[m[2].slice(0, 3).toLowerCase()], d: +m[1], y: yr(m[3]) })],
  [new RegExp('^' + MONRE + ' ?(\\d{1,2})(?:,? (\\d{4}))?(?![\\d])', 'i'), (m) => ({ m: MON[m[1].slice(0, 3).toLowerCase()], d: +m[2], y: yr(m[3]) })],
];
function yr(s) { if (!s) return null; const n = +s; return n < 100 ? 2000 + n : n; }
export function leadingDate(t) {
  for (const [re, f] of DATE_RES) {
    const m = re.exec(t);
    if (!m) continue;
    const d = f(m);
    d.len = m[0].length;
    if (d.iso) { d.m = d.a; d.d = d.b; }
    if (d.m ? d.d >= 1 && d.d <= 31 : d.a >= 1 && d.b >= 1 && d.a <= 31 && d.b <= 31 && (d.a <= 12 || d.b <= 12)) return d;
  }
  return null;
}
// Full dates anywhere in the text ("January 31, 2026", "01/31/2026", "31/01/2026"), for the statement year.
function fullDates(text, dmy) {
  const out = [];
  for (const m of text.matchAll(new RegExp('\\b' + MONRE + ' (\\d{1,2}),? (\\d{4})', 'gi'))) out.push({ y: +m[3], m: MON[m[1].slice(0, 3).toLowerCase()] });
  for (const m of text.matchAll(new RegExp('\\b(\\d{1,2}) ' + MONRE + ',? (\\d{4})', 'gi'))) out.push({ y: +m[3], m: MON[m[2].slice(0, 3).toLowerCase()] });
  for (const m of text.matchAll(/\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})\b/g)) out.push({ y: +m[3], m: dmy ? +m[2] : +m[1] });
  for (const m of text.matchAll(/\b(\d{4})-(\d{2})-(\d{2})\b/g)) out.push({ y: +m[1], m: +m[2] });
  return out.filter((d) => d.m >= 1 && d.m <= 12 && d.y > 1990 && d.y < 2100);
}

// ---------- reading the statement ----------
const OPEN_RE = /\b(beginning|opening|starting|previous|prior)\b.*\bbalance\b|\bbalance\b.*\b(brought|carried) forward\b|\bbalance forward\b/i;
const CLOSE_RE = /\b(ending|closing|new)\b.*\bbalance\b|\bbalance\b.*\bcarried forward\b/i;
const TOTAL_RE = /\b(total|subtotal|sub-total)\b|\bpage \d+\b|\bdaily balance\b|\bsummary\b/i;
const HEAD = [
  ['debit', /withdrawal|debit|paid out|money out|charges|payments? out|\bout\b/i],
  ['credit', /deposit|credit|paid in|money in|\bin\b/i],
  ['balance', /balance/i],
  ['amount', /amount/i],
];
const SEC_IN = /\b(deposits?|credits?|additions|paid in|money in)\b/i;
const SEC_OUT = /\b(withdrawals?|debits?|checks? paid|fees|purchases|payments|charges|money out|paid out|atm)\b/i;

export function readStatement(pages) {
  const lines = toLines(pages);
  const allText = lines.map((l) => l.cells.map((c) => c.t).join(' ')).join('\n');
  const warnings = [];
  if (!lines.length) return { rows: [], summary: { verdict: 'no-text' }, warnings: ["This PDF has no text in it — it's probably a scan or a photo. Scanned statements need OCR first, which RowProof doesn't do."] };

  // Day/month order: if any numeric date has a first part over 12, it's day-first.
  let dmy = false;
  for (const l of lines) { const d = l.cells[0] && leadingDate(l.cells[0].t); if (d && d.num && d.a > 12) dmy = true; }
  if (!dmy && /\d{1,2}\/\d{1,2}\/\d{4}/.test(allText)) for (const m of allText.matchAll(/\b(\d{1,2})\/(\d{1,2})\/\d{4}\b/g)) if (+m[1] > 12) dmy = true;

  let opening = null, closing = null, headers = [];
  let section = 0;
  const txns = [];
  const orphans = [];
  let last = null;
  for (let i = 0; i < lines.length; i++) {
    const l = lines[i];
    const text = l.cells.map((c) => c.t).join(' ');
    const amts = l.cells.filter((c) => isAmount(c.t));
    const words = l.cells.filter((c) => !isAmount(c.t)).map((c) => c.t).join(' ');

    // Column headers: a line with two or more header words and no amounts.
    const hits = HEAD.filter(([, re]) => l.cells.some((c) => re.test(c.t) && c.t.length < 30)).length;
    if (!amts.length && hits >= 2 && /date|posted|description|details|transaction/i.test(text)) {
      headers.push({ page: l.page, cells: l.cells });
      last = null;
      continue;
    }
    if (amts.length && OPEN_RE.test(words)) { if (opening == null) opening = parseAmount(amts.at(-1).t); last = null; continue; }
    if (amts.length && CLOSE_RE.test(words)) { closing = parseAmount(amts.at(-1).t); last = null; continue; }
    if (!amts.length) {
      // A summary box: "OPENING BALANCE" as a label with the number printed under it.
      const below = (cell) => {
        for (let k = i + 1; k < lines.length && k <= i + 3 && lines[k].page === l.page && l.y - lines[k].y < 3 * l.size; k++) {
          const hit = lines[k].cells.find((c) => isAmount(c.t) && c.x2 > cell.x - 20 && c.x < cell.x2 + 20);
          if (hit) return parseAmount(hit.t);
        }
        return null;
      };
      for (const c of l.cells) {
        if (OPEN_RE.test(c.t) && opening == null) opening = below(c);
        else if (CLOSE_RE.test(c.t) && closing == null) closing = below(c);
      }
    }
    if (TOTAL_RE.test(words)) { last = null; continue; }
    if (!amts.length && l.cells.length <= 3 && text.length < 60 && !leadingDate(text)) {
      if (SEC_IN.test(text) && !SEC_OUT.test(text)) section = 1;
      else if (SEC_OUT.test(text)) section = -1;
    }

    const first = l.cells[0];
    const d = first && leadingDate(first.t);
    const amtX = amts.length ? amts[0].x - 2 : Infinity; // description text sits left of the money
    if (d && amts.length) {
      const descParts = [];
      const rest = first.t.slice(d.len).trim();
      const rest2 = rest && leadingDate(rest) ? rest.slice(leadingDate(rest).len).trim() : rest; // "01/03 01/04 DESC": drop the second date
      if (rest2) descParts.push(rest2);
      for (const c of l.cells.slice(1)) if (!isAmount(c.t) && c.x < amtX) descParts.push(c.t.replace(/^\d{1,2}\/\d{1,2}\s+/, ''));
      last = { date: d, parts: [{ y: l.y, t: descParts.join(' ') }], amounts: amts.map((c) => ({ v: parseAmount(c.t), x2: c.x2, x: c.x })), page: l.page, y: l.y, lowY: l.y, size: l.size, descX: l.cells[1]?.x ?? first.x, section };
      txns.push(last);
    } else if (!amts.length && !d && text.length < 120) {
      orphans.push({ page: l.page, y: l.y, size: l.size, cells: l.cells, after: txns.length });
    } else if (!d && amts.length && last && words && l.page === last.page && last.lowY - l.y < 2.4 * l.size) {
      // Same-day line without its own date (some banks only print the date once).
      last = { ...last, parts: [{ y: l.y, t: l.cells.filter((c) => !isAmount(c.t) && c.x < amtX).map((c) => c.t).join(' ') }], amounts: amts.map((c) => ({ v: parseAmount(c.t), x2: c.x2, x: c.x })), y: l.y, lowY: l.y, sameDay: true };
      txns.push(last);
    }
  }

  // Wrapped description lines. Some banks hang them under the date line; others centre the
  // date line on a block of text, so a line can belong to the row below. Tell which by
  // checking for text between a header and the first row of a block.
  const fits = (o, t) => o.page === t.page && o.cells[0].x >= t.descX - 2;
  const textOf = (o, t) => o.cells.filter((c) => c.x < (t.amounts[0]?.x ?? Infinity) - 2).map((c) => c.t).join(' ');
  const centred = orphans.some((o) => {
    const prev = txns[o.after - 1], next = txns[o.after];
    return next && fits(o, next) && o.y - next.y < 1.2 * o.size && (!prev || prev.page !== o.page || prev.y - o.y > 2.4 * o.size);
  });
  for (const o of orphans) {
    const prev = txns[o.after - 1], next = txns[o.after];
    let t = null;
    if (centred) {
      const dp = prev && fits(o, prev) ? prev.y - o.y : Infinity, dn = next && fits(o, next) ? o.y - next.y : Infinity;
      if (Math.min(dp, dn) < 2.4 * o.size) t = dp <= dn ? prev : next;
    } else if (prev && fits(o, prev) && prev.lowY - o.y < 2.4 * o.size) t = prev;
    if (!t) continue;
    const txt = textOf(o, t);
    if (!txt) continue;
    t.parts.push({ y: o.y, t: txt });
    t.lowY = Math.min(t.lowY, o.y);
  }
  for (const t of txns) t.desc = t.parts.sort((a, b) => b.y - a.y).map((p) => p.t).filter(Boolean).join(' ');

  // Years: dates without a year get the statement's year, stepping back across a year end.
  const fd = fullDates(allText, dmy);
  let end = fd.length ? fd.reduce((a, b) => (b.y * 12 + b.m > a.y * 12 + a.m ? b : a)) : null;
  for (const t of txns) {
    const d = t.date;
    if (d.num && !d.iso) { d.m = dmy ? d.b : d.a; d.d = dmy ? d.a : d.b; }
    if (d.y == null) d.y = end ? (d.m <= end.m ? end.y : end.y - 1) : null;
  }
  if (txns.some((t) => t.date.y == null)) warnings.push("Couldn't tell the year from the statement, so dates are month and day only.");

  // Columns: amounts whose printed spans overlap belong to the same column. This works for
  // right-aligned, left-aligned and centred numbers alike, since separate columns never overlap.
  const all = txns.flatMap((t) => t.amounts);
  const spans = all.map((a) => [a.x - 1.5, a.x2 + 1.5]).sort((a, b) => a[0] - b[0]);
  const cols = [];
  for (const [lo, hi] of spans) { const c = cols.at(-1); if (c && lo <= c.hi) c.hi = Math.max(c.hi, hi); else cols.push({ lo, hi }); }
  for (const a of all) a.col = cols.findIndex((c) => a.x2 <= c.hi && a.x >= c.lo - 0.01);
  // Name columns from the nearest header word, when there is one.
  const hcells = headers.flatMap((h) => h.cells);
  cols.forEach((c) => {
    const mid = (c.lo + c.hi) / 2;
    let best = null, bd = Infinity;
    for (const h of hcells) {
      const dist = mid < h.x ? h.x - mid : mid > h.x2 ? mid - h.x2 : 0;
      if (dist < bd) { bd = dist; best = h; }
    }
    c.label = best && bd < 60 ? (HEAD.find(([, re]) => re.test(best.t)) || [null])[0] : null;
  });

  // Try every sensible reading of the columns and keep the one the statement agrees with.
  const n = cols.length;
  const idx = [...Array(n).keys()];
  const hyps = [];
  for (const bal of [n - 1, -1]) {
    const rest = idx.filter((k) => k !== bal);
    for (const k of rest) { hyps.push({ bal, signed: k, flip: 1 }); hyps.push({ bal, signed: k, flip: -1 }); }
    for (const a of rest) for (const b of rest) if (a !== b) hyps.push({ bal, debit: a, credit: b });
    if (bal === -1) for (const k of rest) hyps.push({ bal, section: k });
  }
  let best = null;
  for (const h of hyps) {
    const r = score(h, txns, opening, closing, cols);
    if (!best || r.score > best.score) best = r;
  }
  if (!txns.length) return { rows: [], summary: { verdict: 'no-rows', opening, closing }, warnings: [...warnings, "Couldn't find transaction lines (a date followed by an amount) in this PDF."] };

  const iso = (d) => (d.y ? `${d.y}-${String(d.m).padStart(2, '0')}-${String(d.d).padStart(2, '0')}` : `${String(d.m).padStart(2, '0')}-${String(d.d).padStart(2, '0')}`);
  const rows = txns.map((t, i) => ({
    date: iso(t.date), description: t.desc.replace(/\s+/g, ' ').trim(), amount: best.delta[i],
    balance: best.bal[i], page: t.page, check: best.status[i],
  }));
  const counts = {};
  for (const r of rows) counts[r.check] = (counts[r.check] || 0) + 1;
  const sum = rows.reduce((s, r) => s + (r.amount ?? 0), 0);
  const open = opening ?? best.opening;
  const endBal = open != null ? round(open + sum) : null;
  const totalsMatch = closing != null && endBal != null ? Math.abs(endBal - closing) < 0.005 : null;
  if (totalsMatch === false) warnings.push(`Opening ${fmt(open)} plus all rows is ${fmt(endBal)}, but the statement says it ends at ${fmt(closing)}. Something was missed or misread.`);
  if (counts.mismatch) warnings.push(`${counts.mismatch} row(s) don't add up against the printed balance. They're marked; check them against the PDF.`);
  if (counts['balance-typo']) warnings.push(`${counts['balance-typo']} printed balance(s) look wrong on the statement itself, but the rows around them add up.`);
  const proven = (counts.verified || 0) + (counts['totals-match'] || 0) + (counts['balance-typo'] || 0);
  // "proven" means the bank's own printed opening and closing balances bracket every row and
  // they all add up, so nothing can be missing at either end. Rows that add up without that
  // bracket are "rows-proven": each is right, but a lost page at the start or end can't be ruled out.
  const bracketed = opening != null && closing != null && totalsMatch === true;
  let verdict = (counts.mismatch || totalsMatch === false) ? 'check' : proven === rows.length ? (bracketed ? 'proven' : 'rows-proven') : 'unchecked';
  if (verdict === 'rows-proven') warnings.push(`Every row adds up, but the statement's ${opening == null ? 'opening' : 'closing'} balance wasn't found, so a missing page at the ${opening == null ? 'start' : 'end'} can't be ruled out. Check the row count against the PDF.`);
  if (verdict === 'unchecked') warnings.push(rows.some((r) => r.balance != null) ? "Balances are printed but the rows couldn't be matched to them, so these rows are read but not proven." : 'No balances were printed to check against, so these rows are read but not proven.');
  return { rows, summary: { verdict, rows: rows.length, counts, opening: open, closing, computedClosing: endBal, totalsMatch, reading: best.name, dayFirst: dmy }, warnings };
}

const round = (x) => Math.round(x * 100) / 100;
const fmt = (x) => (x == null ? '?' : x.toFixed(2));

function score(h, txns, opening, closing, cols) {
  const delta = [], bal = [], status = [];
  let used = 0;
  for (const t of txns) {
    let d = 0, b = null, any = false;
    for (const a of t.amounts) {
      if (a.col === h.bal) b = Math.abs(a.v) * (a.v < 0 ? -1 : 1);
      else if (a.col === h.signed) { d += a.v * h.flip; any = true; }
      else if (a.col === h.debit) { d -= Math.abs(a.v); any = true; }
      else if (a.col === h.credit) { d += Math.abs(a.v); any = true; }
      else if (a.col === h.section) { d += Math.abs(a.v) * (t.section || 0); any = any || !!t.section; }
    }
    if (any) used++;
    delta.push(any ? round(d) : null); bal.push(b); status.push('unchecked');
  }
  let s = 0;
  let startBal = opening;
  if (h.bal >= 0) {
    // Running balance check. Rows without a printed balance are checked by the next one that has one.
    let run = opening;
    if (run == null) { const k = bal.findIndex((x) => x != null); if (k >= 0 && delta[k] != null) run = startBal = round(bal[k] - txns.slice(0, k + 1).reduce((a, _, j) => a + (delta[j] ?? 0), 0)); }
    let pending = [];
    let prevPrinted = null;
    for (let i = 0; i < txns.length; i++) {
      if (run == null || delta[i] == null) { pending = []; continue; }
      run = round(run + delta[i]);
      pending.push(i);
      if (bal[i] == null) continue;
      if (Math.abs(run - bal[i]) < 0.005) { for (const k of pending) status[k] = 'verified'; s += pending.length; }
      else if (prevPrinted && Math.abs(round(prevPrinted.bal + delta[i]) - bal[i]) < 0.005) {
        // Adds up from the last printed balance, not from our running total: that printed balance was the bad one.
        status[prevPrinted.i] = 'balance-typo';
        for (const k of pending) status[k] = 'verified';
        s += pending.length;
      } else for (const k of pending) status[k] = 'mismatch';
      if (status[i] === 'mismatch' && i + 1 < txns.length && delta[i + 1] != null && bal[i + 1] != null && Math.abs(round(run + delta[i + 1]) - bal[i + 1]) < 0.005) {
        status[i] = 'balance-typo'; // our total was right and the next row agrees: the printed number is off
        s += 1;
        prevPrinted = { i, bal: bal[i] };
        pending = [];
        continue;
      }
      if (status[i] === 'mismatch') run = bal[i]; // re-sync to the bank's number and carry on
      prevPrinted = { i, bal: bal[i] };
      pending = [];
    }
  }
  // Totals check: opening + every row = closing.
  const sum = delta.reduce((a, x) => a + (x ?? 0), 0);
  const totals = startBal != null && closing != null && Math.abs(round(startBal + sum) - closing) < 0.005;
  if (h.bal < 0 && totals) { for (let i = 0; i < status.length; i++) if (delta[i] != null) status[i] = 'totals-match'; s += used * 0.9; }
  if (h.bal >= 0 && totals) s += 0.5;
  // Small nudges: match the header names, cover every row, prefer the plain reading on ties.
  const lab = (k) => cols[k]?.label;
  if (h.debit != null && lab(h.debit) === 'debit') s += 0.2;
  if (h.credit != null && lab(h.credit) === 'credit') s += 0.2;
  if (h.bal >= 0 && lab(h.bal) === 'balance') s += 0.2;
  if (h.flip === 1) s += 0.05;
  s += used * 0.01;
  const name = h.bal >= 0 ? 'running balance' : h.section != null ? 'section totals' : 'statement totals';
  const how = h.signed != null ? 'one signed amount column' : h.section != null ? 'amounts signed by section (deposits / withdrawals)' : 'separate money-out and money-in columns';
  return { score: s, delta, bal, status, opening: startBal, name: `${how}, checked by ${name}` };
}
