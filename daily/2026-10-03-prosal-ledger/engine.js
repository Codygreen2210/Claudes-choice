// ProSal Ledger: the pay math. Pure functions, whole cents, no dependencies.
// Runs the same in the browser and in the tests.
//
// ProSal in one line: the doctor is paid a guaranteed base, and earns a
// percentage of their production. When the percentage comes to more than the
// base already paid, the difference is the production bonus.

export const CATEGORIES = [
  { id: 'services', label: 'Professional services', short: 'Services' },
  { id: 'lab', label: 'Lab work', short: 'Lab' },
  { id: 'pharmacy', label: 'Pharmacy', short: 'Pharmacy' },
  { id: 'preventives', label: 'Preventives', short: 'Preventives' },
  { id: 'other', label: 'Food, retail and other', short: 'Other' },
];

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

// ---------- money and dates ----------

// "$39,000.50" -> 3900050. "(1,200)" and "-1200" are negative. Bad input -> null.
export function toCents(v) {
  if (typeof v === 'number') return Number.isFinite(v) ? Math.round(v * 100) : null;
  if (v == null) return null;
  let s = String(v).trim();
  if (s === '') return null;
  let neg = false;
  if (/^\(.*\)$/.test(s)) { neg = true; s = s.slice(1, -1); }
  s = s.replace(/[$,\s]/g, '');
  if (s.startsWith('-')) { neg = !neg; s = s.slice(1); }
  if (!/^\d*(\.\d*)?$/.test(s) || s === '' || s === '.') return null;
  const [whole, frac = ''] = s.split('.');
  // Round on the third decimal by hand so 0.125 never drifts through floats.
  const f = (frac + '000').slice(0, 3);
  let cents = Number(whole || '0') * 100 + Number(f.slice(0, 2));
  if (Number(f[2]) >= 5) cents += 1;
  return neg ? -cents : cents;
}

export function fmt(cents, opts = {}) {
  const neg = cents < 0;
  const abs = Math.abs(cents);
  const whole = Math.floor(abs / 100).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  const frac = String(abs % 100).padStart(2, '0');
  const body = opts.whole && abs % 100 === 0 ? `$${whole}` : `$${whole}.${frac}`;
  return neg ? `-${body}` : body;
}

// "21.5" -> 2150 basis points. Bad or out-of-range input -> null.
export function pctToBps(v) {
  const s = String(v ?? '').replace(/[%\s]/g, '');
  if (!/^\d+(\.\d+)?$/.test(s)) return null;
  const bps = Math.round(Number(s) * 100);
  return bps >= 0 && bps <= 10000 ? bps : null;
}

export function bpsToPct(bps) {
  return (bps / 100).toFixed(2).replace(/\.?0+$/, '');
}

export function ymToIndex(ym) {
  const m = /^(\d{4})-(\d{2})$/.exec(ym || '');
  if (!m) return null;
  const month = Number(m[2]);
  if (month < 1 || month > 12) return null;
  return Number(m[1]) * 12 + month - 1;
}

export function indexToYm(i) {
  return `${Math.floor(i / 12)}-${String((i % 12) + 1).padStart(2, '0')}`;
}

export function monthLabel(ym) {
  const i = ymToIndex(ym);
  return `${MONTHS[i % 12]} ${Math.floor(i / 12)}`;
}

// ---------- the pieces of the math ----------

// Round half away from zero, on whole cents.
function share(cents, bps) {
  const sign = cents < 0 ? -1 : 1;
  return sign * Math.round((Math.abs(cents) * bps) / 10000);
}

// Base pay for month k (0-11) of the contract year. The twelve months always
// add up to the yearly figure exactly, so odd salaries don't leak pennies.
// 'full' pays the whole base across the year. 'half' is the classic ProSal
// setup: one guaranteed check a month (base / 24), the second check variable.
export function drawForMonth(baseCents, drawMode, k) {
  const yearly = drawMode === 'half' ? Math.round(baseCents / 2) : baseCents;
  return Math.round((yearly * (k + 1)) / 12) - Math.round((yearly * k) / 12);
}

// One month of production against the contract's percentages.
export function earnedFor(production = {}, ratesBps = {}) {
  const lines = [];
  let total = 0;
  let earned = 0;
  for (const c of CATEGORIES) {
    const p = production[c.id] || 0;
    const bps = ratesBps[c.id] || 0;
    const e = share(p, bps);
    lines.push({ id: c.id, label: c.label, production: p, bps, earned: e });
    total += p;
    earned += e;
  }
  return { lines, production: total, earned };
}

// ---------- the ledger ----------
//
// doc: {
//   name, baseCents, yearStart: 'YYYY-MM',
//   ratesBps: { services, lab, pharmacy, preventives, other },
//   period: 'monthly' | 'quarterly',   how often the bonus is figured
//   drawMode: 'full' | 'half',         how much of the base is paid out as you go
//   carry: boolean,                    carry a shortfall into the next period (negative accrual)
//   resetAtYearEnd: boolean,           wipe any carried shortfall when the contract year ends
// }
// entries: { 'YYYY-MM': { services, lab, pharmacy, preventives, other, basePaid? } } in cents
//
// A period is only settled when every month in it has numbers, and periods are
// settled in order. A missing month stops the ledger there, so a carried
// shortfall can never skip a month.
export function runLedger(doc, entries = {}) {
  const start = ymToIndex(doc.yearStart);
  const out = { periods: [], years: [], carry: 0, ignored: [] };
  if (start == null) return out;

  let last = null;
  for (const ym of Object.keys(entries)) {
    const i = ymToIndex(ym);
    if (i == null) continue;
    if (i < start) { out.ignored.push(ym); continue; }
    if (last == null || i > last) last = i;
  }
  if (last == null) return out;

  const len = doc.period === 'quarterly' ? 3 : 1;
  let carry = 0;
  let stopped = false;
  let year = null;

  for (let p = 0; start + p * len <= last; p++) {
    const first = start + p * len;
    const yearNo = Math.floor((p * len) / 12);
    if (!year || year.no !== yearNo) {
      year = {
        no: yearNo, from: indexToYm(start + yearNo * 12), to: indexToYm(start + yearNo * 12 + 11),
        production: 0, earned: 0, basePaid: 0, bonus: 0, absorbed: 0,
        monthsSettled: 0, complete: false, trueUp: 0, forgiven: 0, paid: 0,
      };
      out.years.push(year);
    }

    const months = [];
    const lines = CATEGORIES.map((c) => ({ id: c.id, label: c.label, production: 0, bps: doc.ratesBps[c.id] || 0, earned: 0 }));
    let production = 0, earned = 0, basePaid = 0, entered = 0;
    for (let i = first; i < first + len; i++) {
      const ym = indexToYm(i);
      const e = entries[ym];
      const k = (i - start) % 12;
      const has = !!e;
      const m = { ym, has, production: 0, earned: 0, basePaid: 0 };
      if (has) {
        const r = earnedFor(e, doc.ratesBps);
        r.lines.forEach((l, j) => { lines[j].production += l.production; });
        m.production = r.production;
        m.earned = r.earned;
        m.basePaid = Number.isInteger(e.basePaid) ? e.basePaid : drawForMonth(doc.baseCents, doc.drawMode, k);
        production += m.production; basePaid += m.basePaid;
        entered++;
      }
      months.push(m);
    }
    // The percentage is taken once on the period's total for each category,
    // not month by month, so a quarter never drifts a cent from rounding.
    for (const l of lines) { l.earned = share(l.production, l.bps); earned += l.earned; }

    const label = len === 1
      ? monthLabel(months[0].ym)
      : `${monthLabel(months[0].ym)} to ${monthLabel(months[len - 1].ym)}`;
    const period = { label, yearNo, months, lines, production, earned, basePaid, carryIn: 0, bonus: 0, carryOut: 0, absorbed: 0, status: 'settled', yearEnd: null };

    if (stopped || entered < len) {
      // Not settled: either its own months are missing, or an earlier period is.
      period.status = entered < len ? 'open' : 'waiting';
      stopped = true;
      out.periods.push(period);
      continue;
    }

    period.carryIn = carry;
    const net = earned - basePaid - carry;
    if (net >= 0) {
      period.bonus = net;
      carry = 0;
    } else if (doc.carry) {
      carry = -net;
    } else {
      period.absorbed = -net;
      carry = 0;
    }
    period.carryOut = carry;

    year.production += production;
    year.earned += earned;
    year.basePaid += basePaid;
    year.bonus += period.bonus;
    year.absorbed += period.absorbed;
    year.monthsSettled += len;

    if (year.monthsSettled === 12) {
      // The guarantee is yearly: if base paid plus bonuses came to less than
      // the guaranteed base, the practice owes the difference.
      year.complete = true;
      year.trueUp = Math.max(0, doc.baseCents - (year.basePaid + year.bonus));
      if (doc.resetAtYearEnd) { year.forgiven = carry; carry = 0; }
      period.yearEnd = { trueUp: year.trueUp, forgiven: year.forgiven };
      period.carryOut = carry;
    }
    year.paid = year.basePaid + year.bonus + year.trueUp;
    out.periods.push(period);
  }

  out.carry = carry;
  return out;
}

// ---------- plain-English checks ----------
//
// Things worth a second look before the statement goes to the doctor. These
// are rules of thumb from the people who designed ProSal, not law.
export function checks(doc, ledger, benefitsCents = 0) {
  const notes = [];
  const settled = ledger.periods.filter((p) => p.status === 'settled');

  let run = 0;
  for (const p of settled) run = p.carryOut > 0 ? run + 1 : 0;
  if (run >= 3) {
    notes.push({ level: 'warn', id: 'underwater', text: `A shortfall has been carried for ${run} periods in a row (${fmt(ledger.carry)} now). The base may be set higher than this doctor's production supports.` });
  }

  const y = ledger.years[ledger.years.length - 1];
  if (y && y.production > 0 && y.monthsSettled >= 3) {
    const paid = y.basePaid + y.bonus + y.trueUp;
    const withBenefits = paid + Math.round((benefitsCents * y.monthsSettled) / 12);
    const bps = Math.round((withBenefits * 10000) / y.production);
    if (bps > 2500) {
      notes.push({ level: 'warn', id: 'over25', text: `Pay${benefitsCents ? ' plus benefits' : ''} is running at ${bpsToPct(bps)}% of production this contract year. The usual ceiling is 25%.` });
    }
    if (y.complete && y.trueUp > 0) {
      notes.push({ level: 'info', id: 'trueup', text: `Year-end guarantee: base paid plus bonuses came to less than the guaranteed base, so ${fmt(y.trueUp)} is owed to bring the doctor up to it.` });
    }
  }

  const open = ledger.periods.find((p) => p.status === 'open');
  if (open) {
    const missing = open.months.filter((m) => !m.has).map((m) => monthLabel(m.ym)).join(', ');
    notes.push({ level: 'info', id: 'open', text: `Waiting on ${missing}. Nothing after that is settled until those numbers are in.` });
  }
  if (ledger.ignored.length) {
    notes.push({ level: 'info', id: 'ignored', text: `${ledger.ignored.length} month(s) before the contract year start are not counted.` });
  }
  return notes;
}

// One line per settled period, ready to paste into a payroll sheet.
export function payrollCsv(docs, ledgers) {
  const rows = [['Doctor', 'Period', 'Production', 'Earned on production', 'Base paid', 'Shortfall carried in', 'Bonus due', 'Year-end guarantee owed', 'Shortfall carried out']];
  docs.forEach((d, i) => {
    for (const p of ledgers[i].periods) {
      if (p.status !== 'settled') continue;
      const c = (n) => (n / 100).toFixed(2);
      rows.push([d.name, p.label, c(p.production), c(p.earned), c(p.basePaid), c(p.carryIn), c(p.bonus), c(p.yearEnd ? p.yearEnd.trueUp : 0), c(p.carryOut)]);
    }
  });
  return rows.map((r) => r.map((v) => (/[",\n]/.test(v) ? `"${String(v).replace(/"/g, '""')}"` : v)).join(',')).join('\n');
}
