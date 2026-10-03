// The worked examples here come from published articles on ProSal, so the
// engine is checked against numbers someone else did by hand.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  toCents, fmt, pctToBps, bpsToPct, ymToIndex, indexToYm, monthLabel,
  drawForMonth, earnedFor, runLedger, checks, payrollCsv,
} from '../engine.js';

const $ = (n) => Math.round(n * 100);
const flat = (pct) => ({ services: pct * 100, lab: pct * 100, pharmacy: pct * 100, preventives: pct * 100, other: pct * 100 });
const doc = (o = {}) => ({
  name: 'Dr. Test', baseCents: $(96000), yearStart: '2026-01', ratesBps: flat(22),
  period: 'monthly', drawMode: 'full', carry: true, resetAtYearEnd: true, ...o,
});
const year = (fn, start = '2026-01') => {
  const e = {};
  const s = ymToIndex(start);
  for (let k = 0; k < 12; k++) e[indexToYm(s + k)] = { services: $(fn(k)) };
  return e;
};

// ---------- money and dates ----------

test('toCents reads the ways people type money', () => {
  assert.equal(toCents('$39,000.50'), 3900050);
  assert.equal(toCents('39000'), 3900000);
  assert.equal(toCents(' 1,234.5 '), 123450);
  assert.equal(toCents('(1,200.00)'), -120000);
  assert.equal(toCents('-45.10'), -4510);
  assert.equal(toCents('.5'), 50);
  assert.equal(toCents('0.125'), 13);
  assert.equal(toCents('1.005'), 101);
  assert.equal(toCents(19.99), 1999);
});

test('toCents refuses junk instead of guessing', () => {
  for (const bad of ['', '   ', 'abc', '12..3', '1e5', '$', '.', '12,3x', null, undefined, NaN]) {
    assert.equal(toCents(bad), null, `should refuse ${JSON.stringify(bad)}`);
  }
});

test('fmt prints dollars the way a pay statement does', () => {
  assert.equal(fmt(819000), '$8,190.00');
  assert.equal(fmt(-206000), '-$2,060.00');
  assert.equal(fmt(5), '$0.05');
  assert.equal(fmt(123456789), '$1,234,567.89');
  assert.equal(fmt(9000000, { whole: true }), '$90,000');
  assert.equal(fmt(9000050, { whole: true }), '$90,000.50');
});

test('percentages become basis points and back', () => {
  assert.equal(pctToBps('21'), 2100);
  assert.equal(pctToBps('21.5%'), 2150);
  assert.equal(pctToBps('0'), 0);
  assert.equal(pctToBps('101'), null);
  assert.equal(pctToBps('-5'), null);
  assert.equal(pctToBps('abc'), null);
  assert.equal(bpsToPct(2150), '21.5');
  assert.equal(bpsToPct(2100), '21');
  assert.equal(bpsToPct(2000), '20');
});

test('months round-trip, including across a year end', () => {
  assert.equal(indexToYm(ymToIndex('2026-12') + 1), '2027-01');
  assert.equal(monthLabel('2027-01'), 'Jan 2027');
  assert.equal(ymToIndex('2026-13'), null);
  assert.equal(ymToIndex('nope'), null);
});

// ---------- base pay ----------

test('twelve months of base pay add up to the salary exactly, odd salaries too', () => {
  for (const base of [$(90000), $(100000), $(133000), $(140000), 12345678, 9999999]) {
    for (const mode of ['full', 'half']) {
      let sum = 0;
      for (let k = 0; k < 12; k++) sum += drawForMonth(base, mode, k);
      assert.equal(sum, mode === 'half' ? Math.round(base / 2) : base, `${base} ${mode}`);
    }
  }
});

test('classic ProSal first check is base / 24', () => {
  assert.equal(drawForMonth($(90000), 'half', 0), $(3750));
  assert.equal(drawForMonth($(75000), 'half', 5), $(3125));
});

// ---------- worked examples from the published articles ----------

test('Opperman, dvm360: $90,000 base, 21%, $39,000 month -> $4,440 second check', () => {
  const d = doc({ baseCents: $(90000), ratesBps: flat(21), drawMode: 'half', carry: false });
  const l = runLedger(d, { '2026-01': { services: $(39000) } });
  const p = l.periods[0];
  assert.equal(p.earned, $(8190));
  assert.equal(p.basePaid, $(3750));
  assert.equal(p.bonus, $(4440));
});

test("Opperman, Today's Veterinary Business: $75,000 base, 23%, $30,000 month -> $3,775", () => {
  const d = doc({ baseCents: $(75000), ratesBps: flat(23), drawMode: 'half', carry: false });
  const p = runLedger(d, { '2026-01': { services: $(30000) } }).periods[0];
  assert.equal(p.earned, $(6900));
  assert.equal(p.bonus, $(3775));
});

test('Owner Exchange: $8,000 draw, 22% earns $5,940 -> $2,060 shortfall carried', () => {
  const d = doc(); // $96,000 base paid in full = $8,000 a month
  const l = runLedger(d, { '2026-01': { services: $(27000) }, '2026-02': { services: $(40000) }, '2026-03': { services: $(50000) } });
  const [jan, feb, mar] = l.periods;
  assert.equal(jan.earned, $(5940));
  assert.equal(jan.bonus, 0);
  assert.equal(jan.carryOut, $(2060));
  // Feb: 8,800 earned - 8,000 base - 2,060 carried = -1,260
  assert.equal(feb.carryIn, $(2060));
  assert.equal(feb.bonus, 0);
  assert.equal(feb.carryOut, $(1260));
  // Mar: 11,000 - 8,000 - 1,260 = 1,740 bonus, and the slate is clean
  assert.equal(mar.bonus, $(1740));
  assert.equal(mar.carryOut, 0);
  assert.equal(l.carry, 0);
});

test('Bash Halow: $120,000 base, 20%, quarterly: bonus starts past $150,000 a quarter', () => {
  const d = doc({ baseCents: $(120000), ratesBps: flat(20), period: 'quarterly', carry: false });
  const at = (q) => runLedger(d, { '2026-01': { services: $(q / 3) }, '2026-02': { services: $(q / 3) }, '2026-03': { services: $(q / 3) } }).periods[0];
  assert.equal(at(150000).bonus, 0);
  assert.equal(at(150000).absorbed, 0);
  assert.equal(at(160000).bonus, $(2000));
  assert.equal(at(160000).label, 'Jan 2026 to Mar 2026');
});

// ---------- the rules that cause the arguments ----------

test('without carry-forward, a short month costs the doctor nothing later', () => {
  const d = doc({ carry: false });
  const l = runLedger(d, { '2026-01': { services: $(27000) }, '2026-02': { services: $(40000) } });
  assert.equal(l.periods[0].absorbed, $(2060));
  assert.equal(l.periods[0].carryOut, 0);
  assert.equal(l.periods[1].carryIn, 0);
  assert.equal(l.periods[1].bonus, $(800));
});

test('with carry-forward the same two months pay $800 less', () => {
  const l = runLedger(doc({ carry: true }), { '2026-01': { services: $(27000) }, '2026-02': { services: $(40000) } });
  assert.equal(l.periods[1].bonus, 0);
  assert.equal(l.periods[1].carryOut, $(1260));
});

test('each category uses its own percentage', () => {
  const rates = { services: 2200, lab: 1800, pharmacy: 800, preventives: 500, other: 0 };
  const r = earnedFor({ services: $(30000), lab: $(8000), pharmacy: $(6000), preventives: $(2000), other: $(1500) }, rates);
  assert.equal(r.production, $(47500));
  // 6,600 + 1,440 + 480 + 100 + 0
  assert.equal(r.earned, $(8620));
  assert.deepEqual(r.lines.map((l) => l.earned), [$(6600), $(1440), $(480), $(100), 0]);
});

test('a slightly wrong percentage gives a different answer (the check is not loose)', () => {
  const a = earnedFor({ services: $(39000) }, { services: 2100 }).earned;
  const b = earnedFor({ services: $(39000) }, { services: 2150 }).earned;
  assert.equal(a, $(8190));
  assert.equal(b, $(8385));
  assert.notEqual(a, b);
});

test('refunds entered as a negative reduce what is earned', () => {
  const r = earnedFor({ services: $(30000), pharmacy: -$(500) }, { services: 2000, pharmacy: 1000 });
  assert.equal(r.earned, $(6000) - $(50));
});

test('half-cent amounts round to the nearest cent, half up', () => {
  // $0.25 at 22% is 5.5 cents
  assert.equal(earnedFor({ services: 25 }, { services: 2200 }).earned, 6);
  assert.equal(earnedFor({ services: -25 }, { services: 2200 }).earned, -6);
});

test('a month the doctor was paid less base (unpaid leave) can be overridden', () => {
  const l = runLedger(doc(), { '2026-01': { services: $(30000), basePaid: $(4000) } });
  assert.equal(l.periods[0].basePaid, $(4000));
  assert.equal(l.periods[0].bonus, $(6600) - $(4000));
});

// ---------- settling in order ----------

test('a missing month stops the ledger so a shortfall cannot skip it', () => {
  const l = runLedger(doc(), { '2026-01': { services: $(27000) }, '2026-03': { services: $(60000) } });
  assert.deepEqual(l.periods.map((p) => p.status), ['settled', 'open', 'waiting']);
  assert.equal(l.periods[2].bonus, 0);
  assert.equal(l.carry, $(2060));
  const note = checks(doc(), l).find((n) => n.id === 'open');
  assert.match(note.text, /Feb 2026/);
});

test('a quarter is not settled until all three months are in', () => {
  const d = doc({ period: 'quarterly' });
  const l = runLedger(d, { '2026-01': { services: $(50000) }, '2026-02': { services: $(50000) } });
  assert.equal(l.periods.length, 1);
  assert.equal(l.periods[0].status, 'open');
  assert.equal(l.periods[0].bonus, 0);
  assert.equal(l.periods[0].production, $(100000));
});

test('months before the contract year start are left out and flagged', () => {
  const l = runLedger(doc({ yearStart: '2026-07' }), { '2026-06': { services: $(40000) }, '2026-07': { services: $(40000) } });
  assert.equal(l.periods.length, 1);
  assert.deepEqual(l.ignored, ['2026-06']);
});

test('a contract year can start mid-year and quarters follow it', () => {
  const d = doc({ yearStart: '2026-07', period: 'quarterly' });
  const l = runLedger(d, year(() => 40000, '2026-07'));
  assert.deepEqual(l.periods.map((p) => p.label), ['Jul 2026 to Sep 2026', 'Oct 2026 to Dec 2026', 'Jan 2027 to Mar 2027', 'Apr 2027 to Jun 2027']);
  assert.equal(l.years.length, 1);
  assert.equal(l.years[0].complete, true);
});

// ---------- year end ----------

test('classic ProSal year end: the practice owes the gap up to the guaranteed base', () => {
  // $90,000 base, one $3,750 check a month. A slow year at 21%.
  const d = doc({ baseCents: $(90000), ratesBps: flat(21), drawMode: 'half', carry: false });
  const l = runLedger(d, year(() => 30000));
  const y = l.years[0];
  // each month: 6,300 earned - 3,750 = 2,550 bonus. 12 x (3,750 + 2,550) = 75,600
  assert.equal(y.basePaid, $(45000));
  assert.equal(y.bonus, $(30600));
  assert.equal(y.trueUp, $(14400));
  assert.equal(y.paid, $(90000));
  assert.equal(l.periods[11].yearEnd.trueUp, $(14400));
  assert.ok(checks(d, l).some((n) => n.id === 'trueup'));
});

test('a good year owes no year-end guarantee', () => {
  const d = doc({ baseCents: $(90000), ratesBps: flat(21), drawMode: 'half', carry: false });
  const y = runLedger(d, year(() => 45000)).years[0];
  assert.equal(y.trueUp, 0);
  assert.equal(y.paid, $(113400)); // 21% of $540,000
});

test('a carried shortfall is wiped at year end when the contract says so', () => {
  const l = runLedger(doc(), { ...year(() => 30000), '2027-01': { services: $(40000) } });
  // every month: 6,600 - 8,000 = -1,400. Twelve months = 16,800.
  assert.equal(l.years[0].forgiven, $(16800));
  assert.equal(l.periods[11].carryOut, 0);
  assert.equal(l.periods[12].carryIn, 0);
  assert.equal(l.periods[12].bonus, $(800));
});

test('and follows the doctor into the next year when it does not', () => {
  const l = runLedger(doc({ resetAtYearEnd: false }), { ...year(() => 30000), '2027-01': { services: $(40000) } });
  assert.equal(l.years[0].forgiven, 0);
  assert.equal(l.periods[12].carryIn, $(16800));
  assert.equal(l.periods[12].bonus, 0);
  assert.equal(l.periods[12].carryOut, $(16000));
});

test('what was paid always equals base paid plus bonuses plus the guarantee', () => {
  for (const mode of ['full', 'half']) for (const carry of [true, false]) for (const period of ['monthly', 'quarterly']) {
    const d = doc({ drawMode: mode, carry, period, baseCents: $(133000), ratesBps: flat(21.5) });
    const l = runLedger(d, year((k) => 25000 + k * 3777.77));
    const y = l.years[0];
    const bonuses = l.periods.reduce((s, p) => s + p.bonus, 0);
    assert.equal(y.paid, y.basePaid + bonuses + y.trueUp);
    assert.ok(y.paid >= d.baseCents, 'the guarantee holds');
    assert.equal(y.production, l.periods.reduce((s, p) => s + p.production, 0));
  }
});

// ---------- checks ----------

test('three periods under water in a row gets flagged', () => {
  const l = runLedger(doc(), { '2026-01': { services: $(30000) }, '2026-02': { services: $(30000) }, '2026-03': { services: $(30000) } });
  const n = checks(doc(), l).find((x) => x.id === 'underwater');
  assert.ok(n);
  assert.match(n.text, /\$4,200\.00/);
});

test('two periods under water is not flagged yet', () => {
  const l = runLedger(doc(), { '2026-01': { services: $(30000) }, '2026-02': { services: $(30000) } });
  assert.equal(checks(doc(), l).find((x) => x.id === 'underwater'), undefined);
});

test('pay over 25% of production gets flagged, with benefits counted if given', () => {
  const d = doc({ carry: false });
  const l = runLedger(d, { '2026-01': { services: $(30000) }, '2026-02': { services: $(30000) }, '2026-03': { services: $(30000) } });
  // paid 24,000 on 90,000 = 26.67%
  assert.match(checks(d, l).find((x) => x.id === 'over25').text, /26\.67%/);
  const ok = runLedger(d, { '2026-01': { services: $(40000) }, '2026-02': { services: $(40000) }, '2026-03': { services: $(40000) } });
  assert.equal(checks(d, ok).find((x) => x.id === 'over25'), undefined);
  // 26,400 pay + 3 months of $18,000 benefits (4,500) on 120,000 = 25.75%
  assert.match(checks(d, ok, $(18000)).find((x) => x.id === 'over25').text, /plus benefits is running at 25\.75%/);
});

// ---------- payroll export ----------

test('payroll export has one line per settled period and quotes names with commas', () => {
  const d = doc({ name: 'Okafor, Dana DVM' });
  const l = runLedger(d, { '2026-01': { services: $(27000) }, '2026-02': { services: $(50000) }, '2026-04': { services: $(50000) } });
  const rows = payrollCsv([d], [l]).split('\n');
  assert.equal(rows.length, 3);
  assert.equal(rows[1], '"Okafor, Dana DVM",Jan 2026,27000.00,5940.00,8000.00,0.00,0.00,0.00,2060.00');
  assert.equal(rows[2], '"Okafor, Dana DVM",Feb 2026,50000.00,11000.00,8000.00,2060.00,940.00,0.00,0.00');
});
