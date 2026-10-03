// ProSal Ledger: the screen. All the pay math lives in engine.js.
// Everything typed here stays in this browser. Nothing is sent anywhere,
// except a license key to /api/check when there is one.
import {
  CATEGORIES, toCents, fmt, pctToBps, bpsToPct, ymToIndex, indexToYm, monthLabel,
  drawForMonth, runLedger, checks, payrollCsv,
} from './engine.js';
import { CONFIG } from './config.js';

const DEMO = !!globalThis.PL_DEMO; // the phone-preview build: paid features on, no printing or files
const SAVE = 'prosal-ledger-v1';
const LIC = 'prosal-ledger-key';
const $ = (sel, el = document) => el.querySelector(sel);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const dollars = (n) => Math.round(n * 100);
const money = (c) => (c / 100).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const store = {
  get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); return true; } catch { return false; } },
  del(k) { try { localStorage.removeItem(k); } catch { /* nothing to remove */ } },
};

// ---------- state ----------

let uid = 0;
const newId = () => `d${Date.now().toString(36)}${uid++}`;

function blankDoc(name = '') {
  const y = new Date().getFullYear();
  return {
    id: newId(), name, baseCents: 0, yearStart: `${y}-01`,
    ratesBps: { services: 2000, lab: 2000, pharmacy: 2000, preventives: 2000, other: 2000 },
    period: 'monthly', drawMode: 'full', carry: true, resetAtYearEnd: true, benefitsCents: 0, entries: {},
  };
}

function example() {
  const rows = (list) => Object.fromEntries(list.map(([ym, s, l, p, v, o]) => [ym, { services: dollars(s), lab: dollars(l), pharmacy: dollars(p), preventives: dollars(v), other: dollars(o) }]));
  return {
    v: 1, example: true, practice: 'Pine Hollow Animal Clinic',
    docs: [
      {
        id: 'ex1', name: 'Dr. Avery Example', baseCents: dollars(132000), yearStart: '2026-01',
        ratesBps: { services: 2200, lab: 1800, pharmacy: 800, preventives: 500, other: 0 },
        period: 'monthly', drawMode: 'full', carry: true, resetAtYearEnd: true, benefitsCents: dollars(14500),
        entries: rows([
          ['2026-01', 41250, 8420, 6180, 2350, 940],
          ['2026-02', 33800, 6950, 5240, 1980, 810],
          ['2026-03', 46900, 9310, 6720, 2640, 1020],
          ['2026-04', 49300, 9870, 7050, 2810, 1100],
          ['2026-05', 44150, 8640, 6390, 3120, 980],
          ['2026-06', 51700, 10480, 7310, 3380, 1150],
          ['2026-07', 38400, 7720, 5880, 2900, 870],
          ['2026-08', 47650, 9540, 6830, 2710, 1040],
          ['2026-09', 50200, 10130, 7240, 2480, 1090],
        ]),
      },
      {
        id: 'ex2', name: 'Dr. Jordan Example', baseCents: dollars(120000), yearStart: '2026-01',
        ratesBps: { services: 2000, lab: 2000, pharmacy: 2000, preventives: 2000, other: 2000 },
        period: 'quarterly', drawMode: 'full', carry: false, resetAtYearEnd: true, benefitsCents: 0,
        entries: rows([
          ['2026-01', 36400, 7100, 4900, 1800, 600], ['2026-02', 39800, 7600, 5200, 1900, 700], ['2026-03', 44100, 8300, 5600, 2100, 650],
          ['2026-04', 47500, 9000, 6100, 2300, 800], ['2026-05', 45200, 8700, 5900, 2600, 750], ['2026-06', 49900, 9400, 6400, 2800, 820],
          ['2026-07', 40300, 7800, 5300, 2400, 690], ['2026-08', 46800, 8900, 6000, 2200, 760], ['2026-09', 48600, 9200, 6200, 2000, 780],
        ]),
      },
    ],
  };
}

function load() {
  const raw = store.get(SAVE);
  if (!raw) return null;
  try { const s = JSON.parse(raw); return s && s.v === 1 && Array.isArray(s.docs) && s.docs.length ? s : null; } catch { return null; }
}

let checkMode = false; // opened from a doctor's check link: nothing is saved
let S = readCheckLink() || load() || example();
const ui = { doc: S.docs[0].id, month: null, removing: false, copy: null, termsOpen: !S.example };
const license = { paid: DEMO, name: DEMO ? 'Demo' : '', exp: 0, msg: '' };

const save = () => { if (!checkMode) store.set(SAVE, JSON.stringify(S)); };
const cur = () => S.docs.find((d) => d.id === ui.doc) || S.docs[0];
const monthsOf = (d) => Object.keys(d.entries).sort();

// ---------- doctor's check link ----------
// The whole statement rides in the link itself, after the #. Nothing is
// uploaded: the doctor's browser does the math again from the same numbers.

function b64(s) { return btoa(String.fromCharCode(...new TextEncoder().encode(s))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); }
function unb64(s) { return new TextDecoder().decode(Uint8Array.from(atob(s.replace(/-/g, '+').replace(/_/g, '/')), (c) => c.charCodeAt(0))); }

function checkLink(d) {
  const pack = { v: 1, practice: S.practice || '', docs: [d] };
  return `${location.origin}${location.pathname}#check=${b64(JSON.stringify(pack))}`;
}

function readCheckLink() {
  const m = /^#check=([A-Za-z0-9_-]+)$/.exec(globalThis.location ? location.hash : '');
  if (!m) return null;
  try {
    const s = JSON.parse(unb64(m[1]));
    if (s.v !== 1 || !Array.isArray(s.docs) || !s.docs[0] || !s.docs[0].ratesBps) return null;
    checkMode = true;
    return s;
  } catch { return null; }
}

// ---------- license ----------

async function startLicense() {
  if (DEMO || checkMode || !location.protocol.startsWith('http')) return;
  const params = new URLSearchParams(location.search);
  const session = params.get('session_id');
  try {
    if (session) {
      const r = await (await fetch(`/api/claim?session_id=${encodeURIComponent(session)}`)).json();
      if (r.ok) { store.set(LIC, r.key); toast(`Thank you. ${r.name} is licensed.`); }
      else license.msg = r.error;
      history.replaceState(null, '', location.pathname + location.hash);
    }
    const key = store.get(LIC);
    if (key) await applyKey(key, false);
  } catch { /* offline or no server: stay on the free plan */ }
  render();
}

async function applyKey(key, loud) {
  let r;
  try { r = await (await fetch(`/api/check?key=${encodeURIComponent(key.trim())}`)).json(); }
  catch { r = { ok: false, reason: 'Could not check the key. Are you online?' }; }
  if (r.ok) {
    Object.assign(license, { paid: true, name: r.name, exp: r.exp, msg: '' });
    store.set(LIC, key.trim());
    if (loud) toast(`${r.name} is licensed.`);
  } else {
    Object.assign(license, { paid: false, msg: r.reason || 'That key did not work.' });
  }
  return r.ok;
}

// ---------- rendering ----------

function render() {
  const d = cur();
  const months = monthsOf(d);
  if (!ui.month || !d.entries[ui.month]) ui.month = months[months.length - 1] || null;
  $('#app').innerHTML = `
    ${top()}
    ${S.example && !checkMode ? `<div class="banner noprint"><span><strong>Example numbers.</strong> Change anything to see how it works.</span><button class="btn" data-act="start">Start with my own</button></div>` : ''}
    ${checkMode ? `<div class="banner noprint"><span><strong>${esc(S.practice || 'Your practice')} sent you this statement.</strong> Every line of the math is shown. Change any number to see what it does. Changes stay on your screen.</span></div>` : ''}
    ${checkMode ? '' : docChips()}
    <div class="grid">
      <div class="col noprint">${terms(d)}${monthsPanel(d)}</div>
      <div class="col" id="results"></div>
    </div>
    <section class="panel" id="ledger"></section>
    ${checkMode ? checkFooter() : plans() + dataPanel()}
    <footer class="fine noprint">
      <p>ProSal Ledger does the arithmetic your contract describes. It is not legal, tax or payroll advice. The contract is the final word, so check these settings against it.</p>
      <p>Your numbers stay in this browser. They are not sent to us or anyone else.</p>
    </footer>`;
  refresh();
}

function top() {
  const badge = DEMO ? '<span class="pill on noprint">Demo: paid features on</span>'
    : license.paid ? `<span class="pill on noprint">Licensed to ${esc(license.name)}</span>`
      : '<span class="pill noprint">Free plan</span>';
  return `<header class="top">
    <div class="brand"><span class="mark">ProSal <b>Ledger</b></span>${checkMode ? '' : badge}</div>
    <p class="lede muted noprint">Production pay statements for veterinary practices. Type in each doctor's numbers and get a statement that shows every line of the math.</p>
  </header>`;
}

function docChips() {
  return `<nav class="docs noprint" aria-label="Doctors">
    ${S.docs.map((d) => `<button class="chip" data-act="doc" data-id="${d.id}" aria-pressed="${d.id === ui.doc}">${esc(d.name || 'New doctor')}</button>`).join('')}
    <button class="chip add" data-act="add-doc">+ Add a doctor</button>
  </nav>`;
}

const seg = (name, value, opts) => `<div class="seg" role="group">${opts.map(([v, text]) => `<button type="button" data-act="set" data-k="${name}" data-v="${v}" aria-pressed="${String(value) === String(v)}">${text}</button>`).join('')}</div>`;

function terms(d) {
  return `<details class="panel" id="terms" ${ui.termsOpen ? 'open' : ''}>
    <summary><h2>Contract terms</h2></summary>
    <div class="fields">
      <label class="f"><span>Practice name</span><input type="text" id="t-practice" data-k="practice" value="${esc(S.practice || '')}" placeholder="Shown on statements"></label>
      <label class="f"><span>Doctor</span><input type="text" id="t-name" data-k="name" value="${esc(d.name)}" placeholder="Dr. ..."></label>
      <label class="f"><span>Guaranteed base, per year</span><input class="money" inputmode="decimal" id="t-base" data-k="baseCents" value="${d.baseCents ? money(d.baseCents) : ''}" placeholder="0.00"></label>
      <label class="f"><span>Contract year starts</span><input type="month" id="t-start" data-k="yearStart" value="${esc(d.yearStart)}"></label>
      <div class="q wide"><span>Percent of production the doctor earns</span>
        <div class="rates">${CATEGORIES.map((c) => `<label class="f"><span>${c.short}</span><input class="pct" inputmode="decimal" id="t-rate-${c.id}" data-rate="${c.id}" value="${bpsToPct(d.ratesBps[c.id] || 0)}"></label>`).join('')}</div>
      </div>
      <div class="q"><span>Bonus is figured</span>${seg('period', d.period, [['monthly', 'Every month'], ['quarterly', 'Every quarter']])}</div>
      <div class="q"><span>Base pay goes out as</span>${seg('drawMode', d.drawMode, [['full', 'The full base, spread over the year'], ['half', 'Half the base (one fixed check a month)']])}</div>
      <div class="q"><span>When production pay falls short of base</span>${seg('carry', d.carry, [['true', 'Carry the shortfall forward'], ['false', 'Let it go']])}</div>
      ${d.carry ? `<div class="q"><span>At the end of the contract year</span>${seg('resetAtYearEnd', d.resetAtYearEnd, [['true', 'Wipe the shortfall'], ['false', 'Keep carrying it']])}</div>` : '<div></div>'}
      <label class="f"><span>Benefits cost per year (optional)</span><input class="money" inputmode="decimal" id="t-benefits" data-k="benefitsCents" value="${d.benefitsCents ? money(d.benefitsCents) : ''}" placeholder="Used for the 25% check"></label>
      ${S.docs.length > 1 ? `<div class="q"><span>&nbsp;</span><button class="btn quiet" data-act="del-doc">${ui.removing === 'doc' ? 'Tap again to remove this doctor' : 'Remove this doctor'}</button></div>` : ''}
    </div>
  </details>`;
}

function monthsPanel(d) {
  const months = monthsOf(d);
  const next = months.length ? indexToYm(ymToIndex(months[months.length - 1]) + 1) : d.yearStart;
  const start = ymToIndex(d.yearStart);
  return `<section class="panel">
    <header><h2>Monthly production</h2><span class="muted small">From your practice software's production report</span></header>
    <div class="months">
      ${months.map((ym) => {
        const e = d.entries[ym];
        const k = ((ymToIndex(ym) - start) % 12 + 12) % 12;
        const open = ym === ui.month;
        return `<div class="month ${open ? 'sel' : ''}">
          <button data-act="month" data-ym="${ym}" aria-expanded="${open}"><span class="when">${monthLabel(ym)}</span><span class="num" data-total="${ym}"></span></button>
          ${open ? `<div class="edit">
            ${CATEGORIES.map((c) => `<label class="f"><span>${c.label}</span><input class="money" inputmode="decimal" id="m-${ym}-${c.id}" data-ym="${ym}" data-cat="${c.id}" value="${e[c.id] ? money(e[c.id]) : ''}" placeholder="0.00"></label>`).join('')}
            <label class="f"><span>Base paid this month</span><input class="money" inputmode="decimal" id="m-${ym}-base" data-ym="${ym}" data-cat="basePaid" value="${Number.isInteger(e.basePaid) ? money(e.basePaid) : ''}" placeholder="${money(drawForMonth(d.baseCents, d.drawMode, k))} unless changed"></label>
          </div>` : ''}
        </div>`;
      }).join('')}
    </div>
    <div class="row">
      <button class="btn" data-act="add-month" data-ym="${next}">Add ${monthLabel(next)}</button>
      ${months.length ? `<button class="btn quiet" data-act="del-month">${ui.removing === 'month' ? `Tap again to remove ${monthLabel(months[months.length - 1])}` : `Remove ${monthLabel(months[months.length - 1])}`}</button>` : ''}
    </div>
    <p class="muted small">Enter refunds as a minus number in the category they came from.</p>
  </section>`;
}

// The part that changes on every keystroke. Inputs are left alone so typing never loses its place.
function refresh() {
  const d = cur();
  const ledger = runLedger(d, d.entries);
  for (const el of document.querySelectorAll('[data-total]')) {
    const e = d.entries[el.dataset.total];
    el.textContent = e ? fmt(CATEGORIES.reduce((s, c) => s + (e[c.id] || 0), 0)) : '';
  }
  const period = ledger.periods.find((p) => p.months.some((m) => m.ym === ui.month)) || ledger.periods[ledger.periods.length - 1];
  $('#results').innerHTML = statement(d, ledger, period) + notes(d, ledger);
  $('#ledger').innerHTML = ledgerTable(d, ledger, period);
}

function termsLine(d) {
  const rates = CATEGORIES.map((c) => `${c.short} ${bpsToPct(d.ratesBps[c.id] || 0)}%`).join(' · ');
  const carry = d.carry ? `Shortfalls carry forward${d.resetAtYearEnd ? ', wiped at contract year end' : ' and keep carrying'}` : 'Shortfalls are not carried';
  return `Base ${fmt(d.baseCents, { whole: true })} a year, ${d.drawMode === 'half' ? 'half paid as one fixed check a month' : 'paid in full over the year'}. ${rates}. Bonus figured ${d.period === 'quarterly' ? 'every quarter' : 'every month'}. ${carry}.`;
}

function statement(d, ledger, p) {
  if (!d.baseCents && !p) {
    return `<section class="sheet"><span class="eyebrow">Statement</span><p>Fill in the contract terms, then add the first month's production. The statement builds itself here.</p></section>`;
  }
  if (!p) {
    return `<section class="sheet"><span class="eyebrow">Statement</span><p>Add the first month's production to see the statement.</p></section>`;
  }
  const settled = p.status === 'settled';
  const y = ledger.years.find((x) => x.no === p.yearNo);
  const shown = p.lines.some((l) => l.production !== 0) ? p.lines.filter((l) => l.production !== 0) : p.lines.slice(0, 1);
  const lines = shown.map((l) => `
    <div class="line"><div class="what">${l.label}<small>${fmt(l.production)} × ${bpsToPct(l.bps)}%</small></div><div class="amt">${fmt(l.earned)}</div></div>`).join('');
  const baseHow = `${fmt(d.baseCents, { whole: true })} a year${p.months.length > 1 ? `, ${p.months.length} months` : ''}${d.drawMode === 'half' ? ', half paid as you go' : ''}`;

  let result = '';
  if (!settled) {
    const missing = p.months.filter((m) => !m.has).map((m) => monthLabel(m.ym)).join(', ');
    result = `<div class="note warn">${p.status === 'open' ? `Not settled yet. Waiting on ${missing}.` : 'These numbers are in, but an earlier period is still missing a month. Periods settle in order.'}</div>`;
  } else {
    result = `<div class="line total ${p.bonus ? '' : 'zero'}"><div class="what">Production bonus due</div><div class="amt" id="bonus">${fmt(p.bonus)}</div></div>`;
    const short = p.basePaid + p.carryIn - p.earned;
    if (!p.bonus && d.carry && short > 0 && !(p.yearEnd && p.yearEnd.forgiven)) {
      result += `<div class="note warn">Production pay came to ${fmt(short)} less than base pay${p.carryIn ? ' plus the shortfall carried in' : ''}. That amount carries into the next period.</div>`;
    } else if (p.absorbed) {
      result += `<div class="note">Production pay came to ${fmt(p.absorbed)} less than base pay. Under this contract that is not carried forward.</div>`;
    }
    if (p.yearEnd) {
      if (p.yearEnd.trueUp) result += `<div class="line total"><div class="what">Year-end guarantee owed<small>guaranteed base less everything paid this contract year</small></div><div class="amt">${fmt(p.yearEnd.trueUp)}</div></div>`;
      if (p.yearEnd.forgiven) result += `<div class="note">Contract year closed. The ${fmt(p.yearEnd.forgiven)} shortfall still on the books is wiped.</div>`;
    }
  }

  const paid = y ? y.basePaid + y.bonus + y.trueUp : 0;
  const pctOfProd = y && y.production > 0 ? `${bpsToPct(Math.round((paid * 10000) / y.production))}%` : '-';
  const can = license.paid;
  const actions = checkMode ? '' : `<div class="row noprint">
      ${DEMO ? '' : `<button class="btn ${can ? '' : 'lock'}" data-act="print">Print statement</button>
      <button class="btn ghost ${can ? '' : 'lock'}" data-act="link">Copy the doctor's check link</button>`}
      <button class="btn ghost ${can ? '' : 'lock'}" data-act="csv">Copy payroll lines</button>
    </div>
    ${DEMO ? '<p class="muted small noprint">On the live site you can also print the statement and send the doctor a link to check it.</p>' : ''}
    ${ui.copy ? `<textarea class="copybox noprint" id="copybox" readonly aria-label="Text to copy">${esc(ui.copy)}</textarea>` : ''}`;

  return `<section class="sheet" id="sheet">
    <div class="who">
      <div><span class="eyebrow">Production pay statement</span><h2>${esc(d.name || 'Doctor')}</h2></div>
      <div style="text-align:right"><div class="eyebrow">${esc(S.practice || '')}</div><strong>${p.label}</strong></div>
    </div>
    <div class="lines">
      ${lines}
      <div class="line sub"><div class="what">Earned on ${fmt(p.production)} of production</div><div class="amt">${fmt(p.earned)}</div></div>
      <div class="line less"><div class="what">Less base pay already paid<small>${baseHow}</small></div><div class="amt">-${fmt(p.basePaid)}</div></div>
      ${settled && d.carry ? `<div class="line ${p.carryIn ? 'less' : ''}"><div class="what">Less shortfall carried in</div><div class="amt">${p.carryIn ? '-' : ''}${fmt(p.carryIn)}</div></div>` : ''}
      ${result}
    </div>
    ${y ? `<div class="ytd">
      <div><span>Contract year production so far</span><b>${fmt(y.production)}</b></div>
      <div><span>Earned on production</span><b>${fmt(y.earned)}</b></div>
      <div><span>Paid: base, bonus and guarantee</span><b>${fmt(paid)}</b></div>
      <div><span>Pay as a share of production</span><b>${pctOfProd}</b></div>
    </div>` : ''}
    <p class="muted small">${esc(termsLine(d))}</p>
    <div class="printonly signs"><span>Prepared by</span><span>Doctor</span><span>Date</span></div>
    ${actions}
  </section>`;
}

function notes(d, ledger) {
  const list = checks(d, ledger, d.benefitsCents || 0).filter((n) => n.id !== 'open');
  if (!list.length) return '';
  return `<section class="panel noprint"><h2>Worth a second look</h2><div class="checks">${list.map((n) => `<div class="note ${n.level === 'warn' ? 'warn' : ''}">${esc(n.text)}</div>`).join('')}</div></section>`;
}

function ledgerTable(d, ledger, picked) {
  if (!ledger.periods.length) return `<h2>Ledger</h2><p class="muted">Each settled period will show here, with what was carried in and out.</p>`;
  const rows = [];
  ledger.periods.forEach((p, i) => {
    const settled = p.status === 'settled';
    rows.push(`<tr class="pick ${p === picked ? 'cur' : ''} ${settled ? '' : 'pending'}" data-act="period" data-ym="${p.months[p.months.length - 1].has ? p.months[p.months.length - 1].ym : (p.months.find((m) => m.has) || p.months[0]).ym}">
      <td>${p.label}${settled ? '' : ' (not settled)'}</td><td>${fmt(p.production)}</td><td>${fmt(p.earned)}</td><td>${fmt(p.basePaid)}</td>
      <td class="${p.carryIn ? 'neg' : ''}">${settled ? fmt(p.carryIn) : ''}</td><td>${settled ? fmt(p.bonus + (p.yearEnd ? p.yearEnd.trueUp : 0)) : ''}</td><td class="${p.carryOut ? 'neg' : ''}">${settled ? fmt(p.carryOut) : ''}</td></tr>`);
    const nextP = ledger.periods[i + 1];
    const y = ledger.years.find((x) => x.no === p.yearNo);
    if ((!nextP || nextP.yearNo !== p.yearNo) && y && y.monthsSettled) {
      rows.push(`<tr class="yr"><td>${y.complete ? 'Contract year' : 'Contract year so far'}</td><td>${fmt(y.production)}</td><td>${fmt(y.earned)}</td><td>${fmt(y.basePaid)}</td><td></td><td>${fmt(y.bonus + y.trueUp)}</td><td></td></tr>`);
    }
  });
  return `<header><h2>Ledger: ${esc(d.name || 'Doctor')}</h2><span class="muted small noprint">Tap a row to see its statement</span></header>
    <div class="scroll"><table>
      <thead><tr><th>Period</th><th>Production</th><th>Earned</th><th>Base paid</th><th>Carried in</th><th>Bonus due</th><th>Carried out</th></tr></thead>
      <tbody>${rows.join('')}</tbody>
    </table></div>`;
}

function plans() {
  if (DEMO) return '';
  const buy = CONFIG.buyUrl
    ? `<a class="btn" href="${esc(CONFIG.buyUrl)}">Get the practice license</a>`
    : '<span class="muted small">Not on sale yet.</span>';
  return `<section class="panel noprint" id="plans">
    <h2>${license.paid ? 'Your license' : 'Plans'}</h2>
    ${license.paid ? `<p>Licensed to <strong>${esc(license.name)}</strong> through ${new Date(license.exp).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}.</p>` : `
    <div class="plans">
      <div class="plan"><h3>Free</h3><div class="price">$0</div><ul><li>One doctor</li><li>Every line of the math on screen</li><li>The full year ledger</li></ul></div>
      <div class="plan best"><h3>Practice license</h3><div class="price">${esc(CONFIG.price)}</div><ul><li>Every doctor in the practice</li><li>Printable statements to hand over</li><li>A check link each doctor can open</li><li>Payroll lines to paste into your sheet</li></ul><p class="muted small">${esc(CONFIG.priceNote)}</p>${buy}</div>
    </div>
    <div class="q"><span>Already have a key?</span><div class="keyrow"><input type="text" id="key" placeholder="PL1...." autocomplete="off"><button class="btn ghost" data-act="key">Use key</button></div>${license.msg ? `<span style="color:var(--neg)">${esc(license.msg)}</span>` : ''}</div>`}
  </section>`;
}

function dataPanel() {
  if (DEMO) return '';
  return `<section class="panel noprint">
    <h2>Your data</h2>
    <p class="muted">Saved in this browser on this computer. Keep a backup file so a cleared browser doesn't cost you the year.</p>
    <div class="row"><button class="btn ghost" data-act="backup">Save a backup file</button><label class="btn quiet" for="restore">Load a backup file</label><input type="file" id="restore" accept="application/json,.json" hidden></div>
  </section>`;
}

function checkFooter() {
  return `<section class="panel noprint"><h2>Run your own practice's statements</h2><p class="muted">ProSal Ledger is free for one doctor.</p><div class="row"><a class="btn" href="${esc(location.pathname)}">Open ProSal Ledger</a></div></section>`;
}

let toastTimer;
function toast(text) {
  const t = $('#toast');
  t.textContent = text;
  t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { t.hidden = true; }, 3200);
}

function needLicense() {
  if (license.paid) return false;
  toast('That comes with the practice license.');
  const el = $('#plans');
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  return true;
}

async function copy(text, done) {
  try {
    await navigator.clipboard.writeText(text);
    toast(done);
  } catch {
    ui.copy = text;
    refresh();
    const box = $('#copybox');
    if (box) { box.focus(); box.select(); }
    toast('Select the text and copy it.');
  }
}

// ---------- events ----------

document.addEventListener('click', (ev) => {
  const el = ev.target.closest('[data-act]');
  if (!el) return;
  const act = el.dataset.act;
  const d = cur();
  if (act !== 'del-month' && act !== 'del-doc') ui.removing = false;
  if (act !== 'csv' && act !== 'link') ui.copy = null;

  if (act === 'start') {
    S = { v: 1, practice: '', docs: [blankDoc()] };
    ui.doc = S.docs[0].id; ui.month = null; ui.termsOpen = true;
    save(); render();
  } else if (act === 'doc') {
    ui.doc = el.dataset.id; ui.month = null; render();
  } else if (act === 'add-doc') {
    if (!S.example && S.docs.length >= 1 && needLicense()) return;
    const nd = blankDoc(); S.docs.push(nd); ui.doc = nd.id; ui.month = null; ui.termsOpen = true;
    save(); render();
  } else if (act === 'del-doc') {
    if (ui.removing !== 'doc') { ui.removing = 'doc'; render(); return; }
    S.docs = S.docs.filter((x) => x.id !== d.id); ui.doc = S.docs[0].id; ui.month = null; ui.removing = false;
    save(); render();
  } else if (act === 'set') {
    const v = el.dataset.v;
    d[el.dataset.k] = v === 'true' ? true : v === 'false' ? false : v;
    ui.termsOpen = true;
    save(); render();
  } else if (act === 'month' || act === 'period') {
    ui.month = el.dataset.ym; ui.termsOpen = $('#terms') ? $('#terms').open : ui.termsOpen;
    render();
    if (act === 'period') { const s = $('#sheet'); if (s) s.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
  } else if (act === 'add-month') {
    d.entries[el.dataset.ym] = {}; ui.month = el.dataset.ym; ui.termsOpen = $('#terms').open;
    save(); render();
    const first = $(`#m-${el.dataset.ym}-services`); if (first) first.focus();
  } else if (act === 'del-month') {
    if (ui.removing !== 'month') { ui.removing = 'month'; render(); return; }
    const months = monthsOf(d); delete d.entries[months[months.length - 1]]; ui.month = null; ui.removing = false;
    save(); render();
  } else if (act === 'print') {
    if (needLicense()) return;
    window.print();
  } else if (act === 'link') {
    if (needLicense()) return;
    copy(checkLink(d), "Link copied. Send it to the doctor.");
  } else if (act === 'csv') {
    if (needLicense()) return;
    copy(payrollCsv(S.docs, S.docs.map((x) => runLedger(x, x.entries))), 'Payroll lines copied. Paste them into your sheet.');
  } else if (act === 'key') {
    applyKey($('#key').value, true).then(render);
  } else if (act === 'backup') {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([JSON.stringify(S, null, 2)], { type: 'application/json' }));
    a.download = `prosal-ledger-backup-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  }
});

document.addEventListener('input', (ev) => {
  const el = ev.target;
  const d = cur();
  if (el.id === 'key' || el.type === 'file') return;
  let ok = true;
  if (el.dataset.cat) {
    const e = d.entries[el.dataset.ym];
    const c = el.value.trim() === '' ? null : toCents(el.value);
    ok = el.value.trim() === '' || c !== null;
    if (ok) {
      if (el.dataset.cat === 'basePaid') { if (c === null) delete e.basePaid; else e.basePaid = c; }
      else e[el.dataset.cat] = c || 0;
    }
  } else if (el.dataset.rate) {
    const b = pctToBps(el.value);
    ok = b !== null;
    if (ok) d.ratesBps[el.dataset.rate] = b;
  } else if (el.dataset.k === 'baseCents' || el.dataset.k === 'benefitsCents') {
    const c = el.value.trim() === '' ? 0 : toCents(el.value);
    ok = c !== null && c >= 0;
    if (ok) d[el.dataset.k] = c;
  } else if (el.dataset.k === 'practice') {
    S.practice = el.value;
  } else if (el.dataset.k === 'name') {
    d.name = el.value;
    const chip = document.querySelector(`.chip[data-id="${d.id}"]`); if (chip) chip.textContent = el.value || 'New doctor';
  } else if (el.dataset.k === 'yearStart') {
    ok = ymToIndex(el.value) !== null;
    if (ok) d.yearStart = el.value;
  } else return;
  el.classList.toggle('bad', !ok);
  if (ok) { save(); refresh(); }
});

// Tidy a money box when you leave it: 39000 becomes 39,000.00.
document.addEventListener('change', (ev) => {
  const el = ev.target;
  if (el.type === 'file') {
    const f = el.files && el.files[0];
    if (!f) return;
    f.text().then((t) => {
      const s = JSON.parse(t);
      if (s.v !== 1 || !Array.isArray(s.docs) || !s.docs.length) throw new Error('bad');
      S = s; ui.doc = S.docs[0].id; ui.month = null; save(); render(); toast('Backup loaded.');
    }).catch(() => toast('That file is not a ProSal Ledger backup.'));
    return;
  }
  if (el.id === 't-start') { ui.termsOpen = true; render(); return; }
  if (!el.classList.contains('money')) return;
  const c = toCents(el.value);
  if (c !== null && el.value.trim() !== '') el.value = money(c);
  if (el.dataset.k === 'baseCents') { ui.termsOpen = true; render(); }
});

// Remember whether the contract terms are folded away.
document.addEventListener('toggle', (ev) => { if (ev.target.id === 'terms') ui.termsOpen = ev.target.open; }, true);

render();
startLicense();
