import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { nodeInflate } from '../lib/pdf.mjs';
import { convert, toCSV, toXLSX, toOFX } from '../lib/rowproof.mjs';
import { readStatement, parseAmount, leadingDate } from '../lib/statement.mjs';

const fx = (f) => new URL('./fixtures/' + f, import.meta.url);
const run = async (f) => convert(readFileSync(fx(f)), { inflate: nodeInflate });
const truth = (f) => JSON.parse(readFileSync(fx(f)));

// Every row must match the generator's answer exactly: date, amount and description.
async function matchesTruth(pdf, json) {
  const r = await run(pdf), t = truth(json);
  assert.equal(r.rows.length, t.rows.length, 'row count');
  t.rows.forEach((w, i) => {
    const g = r.rows[i];
    assert.equal(g.date, w.date, `row ${i + 1} date`);
    assert.equal(g.amount, w.amount, `row ${i + 1} amount`);
    assert.equal(g.description, w.desc, `row ${i + 1} description`);
  });
  assert.equal(r.summary.opening, t.opening);
  return r;
}

test('two money columns + running balance, across a year end and a page break', async () => {
  const r = await matchesTruth('bayou.pdf', 'bayou.json');
  assert.equal(r.summary.verdict, 'proven');
  assert.equal(r.summary.counts.verified, 46);
  assert.equal(r.rows[0].date.slice(0, 4), '2025');
  assert.equal(r.rows.at(-1).date.slice(0, 4), '2026');
});

test('same file with compressed object streams reads the same', async () => {
  const a = await run('bayou.pdf'), b = await run('bayou-objstm.pdf');
  assert.deepEqual(b.rows, a.rows);
});

test('one signed column, balance only at end of day, "Mar 05" dates, Times font', async () => {
  const r = await matchesTruth('delta.pdf', 'delta.json');
  assert.equal(r.summary.verdict, 'proven');
  assert.ok(r.rows.some((x) => x.balance == null), 'some rows have no printed balance and are proven by the next one');
  assert.equal(r.summary.counts.verified, 30);
});

test('big-bank sections: positive amounts signed by section, proven by totals', async () => {
  const r = await matchesTruth('sections.pdf', 'sections.json');
  assert.equal(r.summary.verdict, 'proven');
  assert.equal(r.summary.counts['totals-match'], 26);
  assert.equal(r.summary.totalsMatch, true);
});

test('Chrome-printed UK statement (embedded fonts, day-first dates) and a wrong printed balance', async () => {
  const r = await matchesTruth('chrome.pdf', 'chrome.json');
  assert.equal(r.summary.dayFirst, true);
  assert.equal(r.rows[9].check, 'balance-typo', 'the bank typo on row 10 is caught');
  assert.equal(r.summary.counts.verified, 21);
  assert.equal(r.summary.verdict, 'rows-proven', 'no closing balance printed, so the end is not confirmed');
});

test('a scan with no text says so plainly', async () => {
  const r = await run('scanned.pdf');
  assert.equal(r.rows.length, 0);
  assert.match(r.warnings.join(' '), /scan/);
});

test('encrypted and non-PDF files get a clear message', async () => {
  await assert.rejects(convert(new TextEncoder().encode('%PDF-1.4\n1 0 obj <</Encrypt 2 0 R>> endobj'), { inflate: nodeInflate }), /password|encrypted/);
  await assert.rejects(convert(new TextEncoder().encode('hello'), { inflate: nodeInflate }), /pages|PDF/);
});

// Hand-built pages to test the checks themselves.
const page = (lines) => [{ items: lines.flatMap((l, i) => l.map(([x, x2, str]) => ({ x, x2, y: 700 - i * 12, str, size: 9 }))) }];
const H = [[50, 70, 'Date'], [100, 150, 'Description'], [350, 400, 'Debit'], [440, 480, 'Credit'], [520, 560, 'Balance']];
const OPEN = [[100, 170, 'Opening balance'], [520, 560, '100.00']];

test('a misread amount is flagged, and the rows after it still check out', () => {
  const r = readStatement(page([H, OPEN,
    [[50, 70, '01/02/2026'], [100, 140, 'Coffee'], [370, 400, '5.00'], [530, 560, '95.00']],
    [[50, 70, '01/03/2026'], [100, 140, 'Groceries'], [370, 400, '8.00'], [530, 560, '15.00']], // should be 80.00
    [[50, 70, '01/04/2026'], [100, 140, 'Pay'], [450, 480, '200.00'], [530, 560, '215.00']]]));
  assert.deepEqual(r.rows.map((x) => x.check), ['verified', 'mismatch', 'verified']);
  assert.equal(r.summary.verdict, 'check');
});

test('a missing row shows up when the totals do not match the closing balance', () => {
  const r = readStatement(page([[[50, 70, 'Date'], [100, 150, 'Description'], [520, 560, 'Amount']],
    [[100, 170, 'Beginning Balance'], [520, 560, '100.00']],
    [[50, 70, '01/02'], [100, 140, 'Coffee'], [530, 560, '-5.00']],
    [[100, 170, 'Ending Balance'], [520, 560, '75.00']]]));
  assert.equal(r.summary.totalsMatch, false);
  assert.equal(r.summary.verdict, 'check');
  assert.match(r.warnings.join(' '), /Something was missed/);
});

test('amounts and dates in the many ways banks print them', () => {
  const cases = { '1,234.56': 1234.56, '$12.00': 12, '-$12.00': -12, '(45.10)': -45.1, '45.10-': -45.1, '45.10 DR': -45.1, '45.10CR': 45.1, '£9.99': 9.99, '+60,000.00': 60000, '12.00 OD': -12, '1234': null, '12.5': null, '2026': null };
  for (const [k, v] of Object.entries(cases)) assert.equal(parseAmount(k), v, k);
  assert.deepEqual([leadingDate('Jan 5 AMAZON').m, leadingDate('05 Jan 2026 x').d, leadingDate('2026-01-05').y], [1, 5, 2026]);
  assert.equal(leadingDate('1.05 fee'), null, 'a bare decimal is not a date');
  assert.equal(leadingDate('13/13/2026'), null);
});

test('CSV is safe for Excel, XLSX is a real zip, OFX has every row', async () => {
  const r = await run('bayou.pdf');
  const rows = [...r.rows, { date: '2026-01-20', description: '=HYPERLINK("x")', amount: -1, balance: null, page: 2, check: 'unchecked' }];
  const csv = toCSV(rows);
  assert.match(csv, /"'=HYPERLINK\(""x""\)"/, 'formula text is defused');
  assert.equal(csv.trim().split('\r\n').length, rows.length + 1);
  const x = toXLSX(rows);
  assert.equal(new DataView(x.buffer).getUint32(0, true), 0x04034b50, 'zip header');
  assert.equal(new DataView(x.buffer).getUint32(x.length - 22, true), 0x06054b50, 'zip end record');
  const ofx = toOFX(r.rows, { closing: r.summary.closing });
  assert.equal(ofx.match(/<STMTTRN>/g).length, 46);
  assert.match(ofx, /<LEDGERBAL><BALAMT>677\.57/);
});

test('third-party statements (built by someone else, blind-tested): every field matches their answer files', async () => {
  for (const n of ['astra-premier-checking-jan-2026', 'meridian-salary-account-feb-2026', 'northstar-business-current-mar-2026']) {
    const want = JSON.parse(readFileSync(fx('third-party/' + n + '.json')));
    const r = await run('third-party/' + n + '.pdf');
    assert.equal(r.summary.verdict, 'proven', n);
    assert.equal(r.summary.totalsMatch, true, n + ' opening + rows = closing');
    assert.equal(r.rows.length, want.length, n);
    want.forEach((w, i) => {
      const [d, m, y] = w.date.split('-');
      assert.deepEqual([r.rows[i].date, r.rows[i].amount, r.rows[i].balance, r.rows[i].description],
        [`${y}-${m}-${d}`, w.deposit ? +w.deposit : -w.withdrawal, +w.balance, w.description], `${n} row ${i + 1}`);
    });
  }
});

test('damaged files never come back "proven" with wrong numbers (400 random corruptions)', async () => {
  let opened = 0;
  for (const name of ['bayou', 'delta']) {
    const base = readFileSync(fx(name + '.pdf')), want = truth(name + '.json');
    let seed = 3; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
    for (let i = 0; i < 200; i++) {
      const b = Uint8Array.from(base);
      for (let k = 0; k <= i % 5; k++) b[Math.floor(rnd() * b.length)] = Math.floor(rnd() * 256);
      let r;
      try { r = await convert(b, { inflate: nodeInflate }); } catch { continue; } // a clear error is fine
      opened++;
      if (r.summary.verdict !== 'proven') continue;
      assert.equal(r.rows.length, want.rows.length, `${name} #${i}: proven but rows missing`);
      r.rows.forEach((x, j) => assert.equal(x.amount, want.rows[j].amount, `${name} #${i} row ${j + 1}`));
    }
  }
  assert.ok(opened > 100);
});
