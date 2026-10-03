// Planner Press: the screen. The page plan comes from plan.js, the drawing
// from layout.js. Nothing here is uploaded: the PDF is built in this browser.
import { YEARS, SECTION_IDS, makePlan } from './plan.js';
import { iso } from './dates.js';
import { THEMES, layoutPage, layoutAll, toSvg, toPdf, measurer } from './layout.js';
import { CONFIG } from './config.js';

const DEMO = !!globalThis.PP_DEMO; // the phone-preview build: no file download
const SAVE = 'planner-press-v1';
const PASS = 'planner-press-pass';
const JsPDF = globalThis.jspdf && globalThis.jspdf.jsPDF;
const measure = JsPDF ? measurer(JsPDF) : (t, f, s) => String(t).length * s * 0.5;
const $ = (sel, el = document) => el.querySelector(sel);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const store = {
  get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch { /* private window: carry on without saving */ } },
};

const SECTION_NAMES = { year: 'Year overview', month: 'Monthly pages', week: 'Weekly pages', day: 'Daily pages', notes: 'Notes pages' };
const KEY_NAMES = { year: 'Year', month: 'Month', week: 'Week', day: 'Day', notes: 'Notes' };
const fresh = () => ({ v: 1, year: 2027, weekStart: 0, orientation: 'landscape', theme: 'classic', sections: { year: true, month: true, week: true, day: true, notes: true } });

function load() {
  try {
    const s = JSON.parse(store.get(SAVE));
    if (!s || s.v !== 1 || !YEARS.includes(s.year) || !THEMES[s.theme]) return null;
    return { ...fresh(), ...s, sections: { ...fresh().sections, ...s.sections }, weekStart: s.weekStart === 1 ? 1 : 0, orientation: s.orientation === 'portrait' ? 'portrait' : 'landscape' };
  } catch { return null; }
}

let S = load() || fresh();
const ui = { kind: 'year', num: 1, pay: false, busy: false };
const pass = { paid: false, exp: 0, msg: '' };
const save = () => store.set(SAVE, JSON.stringify(S));
let plan = null;

// The page to show for each kind of page, picked so each one is a typical full page.
function keyPages() {
  const p = plan, a = p.at;
  return {
    year: a.year,
    month: a.month[1] || null,
    week: a.week[2] || null,
    day: a.day[iso(p.year, 1, 4)] || null,
    notes: a.notes[0] || null,
  };
}

function replan() {
  plan = makePlan(S);
  const keys = keyPages();
  if (!ui.num || ui.num > plan.count) ui.num = 1;
  // keep showing the same kind of page after an option changes
  if (keys[ui.kind]) ui.num = keys[ui.kind]; else { ui.num = 1; ui.kind = plan.pages[0].kind; }
}

// ---------- rendering ----------

function render() {
  replan();
  $('#app').innerHTML = `
    <header class="top">
      <h1>Planner <em>Press</em></h1>
      <p class="muted">A planner PDF where every tab and date is a tap, for GoodNotes, Notability and Xodo. It is already made below. Change anything and the page redraws.</p>
    </header>
    <div class="grid">
      <div class="col">
        <section class="panel">
          <span class="lead">Year</span>
          <div class="chips" role="group" aria-label="Year">${YEARS.map((y) => `<button class="chip" data-act="year" data-v="${y}" aria-pressed="${S.year === y}">${y}</button>`).join('')}</div>
          <span class="lead">Week starts on</span>
          <div class="chips" role="group" aria-label="Week starts on">${[[0, 'Sunday'], [1, 'Monday']].map(([v, n]) => `<button class="chip" data-act="weekstart" data-v="${v}" aria-pressed="${S.weekStart === v}">${n}</button>`).join('')}</div>
        </section>
        <section class="panel">
          <span class="lead">What to include</span>
          <div class="chips" role="group" aria-label="Sections">${SECTION_IDS.map((id) => `<label class="chip"><input type="checkbox" data-sec="${id}" ${S.sections[id] ? 'checked' : ''}>${SECTION_NAMES[id]}</label>`).join('')}</div>
          <p class="muted small">Month tabs run down the right edge of every page. A day number on a month page opens its week; the rest of that day's box opens its day page.</p>
        </section>
        <section class="panel">
          <span class="lead">Page shape</span>
          <div class="chips" role="group" aria-label="Page shape">${[['landscape', 'Landscape (wide)'], ['portrait', 'Portrait (tall)']].map(([v, n]) => `<button class="chip" data-act="orient" data-v="${v}" aria-pressed="${S.orientation === v}">${n}</button>`).join('')}</div>
          <span class="lead">Color</span>
          <div class="chips" role="group" aria-label="Color">${Object.entries(THEMES).map(([id, t]) => `<button class="chip" data-act="theme" data-v="${id}" aria-pressed="${S.theme === id}"><i style="background:${t.paper};border-color:${t.accent}"></i>${t.label}</button>`).join('')}</div>
        </section>
      </div>
      <div class="col sheetcol">
        <section class="sheet">
          <div class="nav">
            <div class="chips" id="keys" role="group" aria-label="Pages to look at"></div>
            <div class="row"><button class="btn quiet" data-act="prev" aria-label="Previous page">&lsaquo; Back</button><button class="btn quiet" data-act="next" aria-label="Next page">Next &rsaquo;</button></div>
          </div>
          <div class="paper" id="paper"></div>
          <div class="status" id="status"></div>
          <div id="buy"></div>
        </section>
      </div>
    </div>
    <footer class="fine">
      <p>Everything happens in this browser. The planner is built on your device and nothing about it is sent to us or anyone else.</p>
      <p>Free to make and keep for personal use. The free file has a small "${esc(CONFIG.credit)}" line at the bottom of each page.</p>
    </footer>`;
  refresh();
}

let current = null;

// Redraw the page on screen. Only the page being looked at is laid out; the whole book is laid out when you download.
function refresh() {
  const theme = S.theme;
  const credit = pass.paid ? '' : CONFIG.credit;
  const idx = ui.num - 1;
  const page = layoutPage(plan, idx, measure, { theme, credit });
  current = { page };
  const paper = $('#paper');
  paper.className = `paper${S.orientation === 'portrait' ? ' tall' : ''}`;
  paper.innerHTML = toSvg(page, { links: true });

  const keys = keyPages();
  $('#keys').innerHTML = Object.keys(KEY_NAMES).filter((k) => keys[k]).map((k) => `<button class="chip" data-act="key-page" data-v="${k}" aria-pressed="${plan.pages[idx].kind === k}">${KEY_NAMES[k]}</button>`).join('');

  const kinds = { year: 'Year overview', month: 'Month page', week: 'Week page', day: 'Day page', notes: 'Notes page' };
  $('#status').innerHTML = `<div class="note" id="count"><strong id="where">${kinds[page.kind]}</strong>, page ${ui.num} of ${plan.count}. The whole planner is ${plan.count} pages with ${plan.expected.length.toLocaleString('en-US')} tap links. Tap a tab or a date on the page above to follow it.</div>`;
  $('#buy').innerHTML = buy();
}

function buy() {
  if (DEMO) return '<p class="muted small">This is the preview. The PDF download works on the live site.</p>';
  const busy = ui.busy;
  if (pass.paid) {
    return `<div class="pay"><div class="row"><button class="btn big" data-act="download" ${busy ? 'disabled' : ''}>${busy ? `Building ${plan.count} pages...` : 'Download the PDF'}</button></div>
      <p class="muted small">No credit line on any page. Change anything and download again until ${new Date(pass.exp).toLocaleDateString('en-US', { month: 'long', day: 'numeric' })}.</p></div>`;
  }
  const payBox = !ui.pay ? '' : `<div id="paybox" class="pay">
    <p><strong>${esc(CONFIG.price)}, once.</strong> Takes the "${esc(CONFIG.credit)}" line off every page. For a month you can download as often as you like.</p>
    <div class="row">${CONFIG.buyUrl ? `<a class="btn big" href="${esc(CONFIG.buyUrl)}">Pay ${esc(CONFIG.price)}</a>` : '<span class="muted">Not on sale yet.</span>'}</div>
    <label class="f"><span>Already paid? Paste your pass</span><span class="keyrow"><input type="text" id="key" placeholder="PP1...." autocomplete="off"><button class="btn ghost" data-act="key">Use pass</button></span></label>
    ${pass.msg ? `<span style="color:var(--warn)">${esc(pass.msg)}</span>` : ''}
  </div>`;
  return `<div class="pay"><div class="row"><button class="btn big" data-act="download" ${busy ? 'disabled' : ''}>${busy ? `Building ${plan.count} pages...` : 'Download free PDF'}</button><button class="btn quiet" data-act="want">Remove the credit line (${esc(CONFIG.price)})</button></div>
    <p class="muted small">Free, for personal use. No sign-up. Open the file in GoodNotes, Notability or Xodo and tap a tab.</p></div>${payBox}`;
}

let toastTimer;
function toast(text) {
  const t = $('#toast');
  t.textContent = text; t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { t.hidden = true; }, 3200);
}

// ---------- pass ----------

async function applyKey(key, loud) {
  let r;
  try { r = await (await fetch(`/api/check?key=${encodeURIComponent(String(key).trim())}`)).json(); }
  catch { r = { ok: false, reason: 'Could not check the pass. Are you online?' }; }
  if (r.ok) { Object.assign(pass, { paid: true, exp: r.exp, msg: '' }); store.set(PASS, String(key).trim()); if (loud) toast('Pass accepted. The credit line is gone.'); }
  else Object.assign(pass, { paid: false, msg: r.reason || 'That pass did not work.' });
  return r.ok;
}

async function startPass() {
  if (DEMO || !location.protocol.startsWith('http')) return;
  try {
    const session = new URLSearchParams(location.search).get('session_id');
    if (session) {
      const r = await (await fetch(`/api/claim?session_id=${encodeURIComponent(session)}`)).json();
      if (r.ok) { store.set(PASS, r.key); toast('Thank you. Your PDF will come without the credit line.'); }
      else { pass.msg = r.error; ui.pay = true; }
      history.replaceState(null, '', location.pathname);
    }
    const key = store.get(PASS);
    if (key) await applyKey(key, false);
  } catch { /* offline or no server: previews still work */ }
  refresh();
}

// ---------- download ----------

async function download() {
  if (!JsPDF || ui.busy) return;
  ui.busy = true; refresh();
  await new Promise((r) => setTimeout(r, 40)); // let the "Building" label paint first
  try {
    const pages = layoutAll(plan, measure, { theme: S.theme, credit: pass.paid ? '' : CONFIG.credit });
    const doc = toPdf(pages, JsPDF, { title: `${plan.year} planner` });
    doc.save(`planner-${plan.year}-${plan.weekStart ? 'monday' : 'sunday'}-${plan.orientation}.pdf`);
  } catch (e) {
    toast('Something went wrong building the file. Try again.');
    console.warn(e);
  }
  ui.busy = false; refresh();
}

// ---------- events ----------

function go(num) {
  ui.num = Math.max(1, Math.min(plan.count, num));
  ui.kind = plan.pages[ui.num - 1].kind;
  refresh();
}

document.addEventListener('click', (ev) => {
  const lnk = ev.target.closest && ev.target.closest('.lnk');
  if (lnk) { go(Number(lnk.dataset.page)); return; }
  const el = ev.target.closest('[data-act]');
  if (!el) return;
  const act = el.dataset.act, v = el.dataset.v;
  if (act === 'year') { S.year = Number(v); save(); render(); }
  else if (act === 'weekstart') { S.weekStart = Number(v); save(); render(); }
  else if (act === 'orient') { S.orientation = v; save(); render(); }
  else if (act === 'theme') { S.theme = v; save(); render(); }
  else if (act === 'key-page') { ui.kind = v; go(keyPages()[v]); }
  else if (act === 'prev') go(ui.num - 1);
  else if (act === 'next') go(ui.num + 1);
  else if (act === 'want') { ui.pay = true; refresh(); const b = $('#paybox'); if (b) b.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }
  else if (act === 'key') { applyKey($('#key').value, true).then(refresh); }
  else if (act === 'download') download();
});

document.addEventListener('change', (ev) => {
  const el = ev.target;
  if (!el.dataset || !el.dataset.sec) return;
  const next = { ...S.sections, [el.dataset.sec]: el.checked };
  if (!SECTION_IDS.some((id) => next[id])) { el.checked = true; toast('A planner needs at least one section.'); return; }
  S.sections = next; save(); render();
});

render();
startPass();
