// Our Crossword: the screen. The puzzle is built by construct.js and laid out
// by layout.js. Names and clues stay in this browser; nothing is uploaded.
import { build, check, problem, normalize, parseList } from './construct.js';
import { SIZES, THEMES, layout, toSvg, toPdf, measurer } from './layout.js';
import { CONFIG } from './config.js';

const DEMO = !!globalThis.OC_DEMO; // the phone-preview build: no watermark, no file download
const SAVE = 'our-crossword-v1';
const PASS = 'our-crossword-pass';
const JsPDF = globalThis.jspdf && globalThis.jspdf.jsPDF;
const measure = JsPDF ? measurer(JsPDF) : (t, f, s) => String(t).length * s * 0.5;
const $ = (sel, el = document) => el.querySelector(sel);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const store = {
  get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch { /* private window: carry on without saving */ } },
};

function example() {
  return {
    v: 1, example: true, title: 'Emma & Jack', subtitle: 'June 14, 2027 · Sip & Solve', footer: 'Thank you for celebrating with us',
    theme: 'classic', size: 'letter', seed: 3,
    entries: [
      ['Savannah', 'City where we met'], ['Golden retriever', "Biscuit's breed"], ['Tacos', 'First-date dinner'], ['Lake Tahoe', 'Where he proposed'],
      ['Biscuit', 'Our dog'], ['Chemistry', "Emma's college major"], ['The Office', 'Show we have watched four times through'], ['Paris', 'Honeymoon city'],
      ['Hiking', 'Our favorite weekend plan'], ['Coffee', "Jack can't start a day without it"], ['June', 'Month of the wedding'], ['Navy', 'Color of the groomsmen suits'],
      ['Karaoke', 'How the first date ended'], ['Jeep', "Jack's first car"], ['Pancakes', 'Sunday morning tradition'], ['Florist', "The bride's first job"],
      ['Denver', 'Where we live now'], ['Best man', 'Tyler, to Jack'],
    ].map(([answer, clue]) => ({ answer, clue })),
  };
}
const blank = () => ({ v: 1, title: '', subtitle: '', footer: '', theme: 'classic', size: 'letter', seed: 1, entries: Array.from({ length: 6 }, () => ({ answer: '', clue: '' })) });

function load() {
  try { const s = JSON.parse(store.get(SAVE)); return s && s.v === 1 && Array.isArray(s.entries) ? s : null; } catch { return null; }
}

let S = load() || example();
const ui = { tab: 'puzzle', paste: false, pay: false };
const pass = { paid: false, exp: 0, msg: '' };
const save = () => store.set(SAVE, JSON.stringify(S));

// ---------- rendering ----------

function render() {
  $('#app').innerHTML = `
    <header class="top">
      <h1>Our <em>Crossword</em></h1>
      <p class="muted">A crossword about the two of you. Type your answers and clues, pick a look, print it.</p>
    </header>
    ${S.example ? '<div class="banner"><span><strong>This one is an example.</strong> Change any word and watch the page redraw.</span><button class="btn" data-act="start">Start with my own</button></div>' : ''}
    <div class="grid">
      <div class="col">
        <section class="panel">
          <h2>What goes at the top</h2>
          <label class="f"><span>Names or title</span><input type="text" id="d-title" data-d="title" value="${esc(S.title)}" placeholder="Emma &amp; Jack"></label>
          <label class="f"><span>Line under it</span><input type="text" id="d-subtitle" data-d="subtitle" value="${esc(S.subtitle)}" placeholder="June 14, 2027 · Sip &amp; Solve"></label>
          <label class="f"><span>Line at the bottom</span><input type="text" id="d-footer" data-d="footer" value="${esc(S.footer)}" placeholder="Thank you for celebrating with us"></label>
        </section>
        <section class="panel">
          <header><h2>Answers and clues</h2><button class="btn quiet" data-act="paste">${ui.paste ? 'Back to the list' : 'Paste a list instead'}</button></header>
          ${ui.paste ? `
            <label class="f"><span>One per line, like: Paris - Honeymoon city</span><textarea id="pastebox" placeholder="Paris - Honeymoon city&#10;Biscuit - Our dog&#10;Tacos - First-date dinner"></textarea></label>
            <div class="row"><button class="btn" data-act="use-paste">Use this list</button></div>` : `
            <div class="rows" id="rows">${S.entries.map(row).join('')}</div>
            <div class="row"><button class="btn ghost" data-act="add">Add another</button></div>`}
          <p class="muted small">12 to 20 answers makes a good table puzzle. Spaces and punctuation in answers are fine.</p>
        </section>
        <section class="panel">
          <h2>Look and paper</h2>
          <div class="chips" role="group" aria-label="Look">${Object.entries(THEMES).map(([id, t]) => `<button class="chip" data-act="theme" data-v="${id}" aria-pressed="${S.theme === id}"><i style="background:${t.paper};border-color:${t.accent}"></i>${t.label}</button>`).join('')}</div>
          <label class="f"><span>Paper size</span><select id="d-size" data-d="size">${Object.entries(SIZES).map(([id, z]) => `<option value="${id}" ${S.size === id ? 'selected' : ''}>${z.label} (${z.note})</option>`).join('')}</select></label>
        </section>
      </div>
      <div class="col sheetcol">
        <section class="sheet">
          <div class="row" style="justify-content:space-between">
            <div class="tabs" role="group" aria-label="Page">
              <button class="chip" data-act="tab" data-v="puzzle" aria-pressed="${ui.tab === 'puzzle'}">Puzzle</button>
              <button class="chip" data-act="tab" data-v="key" aria-pressed="${ui.tab === 'key'}">Answer key</button>
            </div>
            <button class="btn quiet" data-act="shuffle">Try another layout</button>
          </div>
          <div class="paper" id="paper"></div>
          <div class="status" id="status"></div>
          <div id="buy"></div>
        </section>
      </div>
    </div>
    <footer class="fine"><p>Your names and clues stay in this browser. They are not sent to us or anyone else.</p></footer>`;
  refresh();
}

function row(e, i) {
  return `<div class="entry" data-i="${i}">
    <input type="text" id="a-${i}" data-f="answer" value="${esc(e.answer)}" placeholder="Answer" autocapitalize="words" aria-label="Answer ${i + 1}">
    <input type="text" id="c-${i}" data-f="clue" value="${esc(e.clue)}" placeholder="Clue" aria-label="Clue ${i + 1}">
    <button class="x" data-act="remove" data-i="${i}" aria-label="Remove answer ${i + 1}">×</button>
    <div class="why" data-why="${i}" hidden></div>
  </div>`;
}

let current = null; // the last built puzzle and its pages

// Rebuild the puzzle and redraw the sheet. Text boxes are left alone so typing never loses its place.
function refresh() {
  const puzzle = build(S.entries, { seed: S.seed });
  const faults = check(puzzle);
  const seen = new Set();
  S.entries.forEach((e, i) => {
    const el = document.querySelector(`[data-why="${i}"]`);
    if (!el) return;
    const filled = String(e.answer).trim() !== '';
    const why = filled ? problem(e.answer, seen) : null;
    if (filled && !why) seen.add(normalize(e.answer).letters);
    const left = puzzle.unplaced.find((u) => u.answer === String(e.answer).trim());
    const text = why || (left ? 'No letter in common with the others yet. It will join once another answer shares one.' : '');
    el.textContent = text; el.hidden = !text;
  });

  const paper = $('#paper'), status = $('#status');
  if (puzzle.words.length < 2 || faults.length) {
    current = null;
    paper.innerHTML = '';
    status.innerHTML = `<div class="note">${faults.length ? 'Something went wrong building this one. Try another layout.' : 'Add at least two answers that share a letter and the puzzle appears here.'}</div>`;
    $('#buy').innerHTML = '';
    return;
  }
  const out = layout(puzzle, { title: S.title, subtitle: S.subtitle, footer: S.footer, theme: S.theme, size: S.size, credit: CONFIG.credit }, measure);
  current = { puzzle, out };
  paper.innerHTML = toSvg(out.pages[ui.tab === 'key' ? 1 : 0], { watermark: pass.paid || DEMO ? '' : 'PREVIEW' });

  const notes = [];
  const z = SIZES[S.size];
  notes.push(`<div class="note" id="count">${puzzle.words.length} answers, every one crossing another. ${out.overflow ? '' : `Fits ${esc(z.label)}.`}</div>`);
  if (out.overflow) notes.push(`<div class="note warn">That is a lot of clues for ${esc(z.label)}. Pick a bigger paper size or trim a few clues so nothing gets cut off.</div>`);
  if (puzzle.unplaced.length) notes.push(`<div class="note warn">Left out for now: ${puzzle.unplaced.map((u) => esc(u.answer)).join(', ')}. No letter in common with the rest.</div>`);
  status.innerHTML = notes.join('');
  $('#buy').innerHTML = buy();
}

function buy() {
  if (DEMO) return '<p class="muted small">This is the preview. On the live page, one button downloads the print file at the exact paper size.</p>';
  if (pass.paid) {
    return `<div class="pay"><div class="row"><button class="btn big" data-act="download">Download the print file</button></div>
      <p class="muted small">Two pages: the puzzle and the answer key. Change anything and download again until ${new Date(pass.exp).toLocaleDateString('en-US', { month: 'long', day: 'numeric' })}.</p></div>`;
  }
  if (!ui.pay) return '<div class="pay"><div class="row"><button class="btn big" data-act="want">Download the print file</button></div><p class="muted small">Free to make and preview. Pay only when you want the file.</p></div>';
  return `<div class="pay" id="paybox">
    <p><strong>${esc(CONFIG.price)}, once.</strong> For a month you can download as often as you like:</p>
    <ul><li>Every paper size, from table cards to a 24 × 36 welcome sign</li><li>All four looks</li><li>The answer key</li><li>No watermark</li></ul>
    <div class="row">${CONFIG.buyUrl ? `<a class="btn big" href="${esc(CONFIG.buyUrl)}">Pay ${esc(CONFIG.price)}</a>` : '<span class="muted">Not on sale yet.</span>'}</div>
    <label class="f"><span>Already paid? Paste your pass</span><span class="keyrow"><input type="text" id="key" placeholder="OC1...." autocomplete="off"><button class="btn ghost" data-act="key">Use pass</button></span></label>
    ${pass.msg ? `<span style="color:var(--warn)">${esc(pass.msg)}</span>` : ''}
  </div>`;
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
  if (r.ok) { Object.assign(pass, { paid: true, exp: r.exp, msg: '' }); store.set(PASS, String(key).trim()); if (loud) toast('Pass accepted. Download away.'); }
  else Object.assign(pass, { paid: false, msg: r.reason || 'That pass did not work.' });
  return r.ok;
}

async function startPass() {
  if (DEMO || !location.protocol.startsWith('http')) return;
  try {
    const session = new URLSearchParams(location.search).get('session_id');
    if (session) {
      const r = await (await fetch(`/api/claim?session_id=${encodeURIComponent(session)}`)).json();
      if (r.ok) { store.set(PASS, r.key); toast('Thank you. Your print file is ready to download.'); }
      else { pass.msg = r.error; ui.pay = true; }
      history.replaceState(null, '', location.pathname);
    }
    const key = store.get(PASS);
    if (key) await applyKey(key, false);
  } catch { /* offline or no server: previews still work */ }
  refresh();
}

// ---------- events ----------

let timer;
const soon = () => { clearTimeout(timer); timer = setTimeout(() => { save(); refresh(); }, 140); };

document.addEventListener('click', (ev) => {
  const el = ev.target.closest('[data-act]');
  if (!el) return;
  const act = el.dataset.act;
  if (act === 'start') { S = blank(); ui.pay = false; save(); render(); $('#d-title').focus(); }
  else if (act === 'add') { S.entries.push({ answer: '', clue: '' }); save(); render(); $(`#a-${S.entries.length - 1}`).focus(); }
  else if (act === 'remove') { S.entries.splice(Number(el.dataset.i), 1); if (!S.entries.length) S.entries.push({ answer: '', clue: '' }); save(); render(); }
  else if (act === 'paste') { ui.paste = !ui.paste; render(); }
  else if (act === 'use-paste') {
    const list = parseList($('#pastebox').value);
    if (!list.length) { toast('Paste at least one line first.'); return; }
    S.entries = list; delete S.example; ui.paste = false; save(); render();
  }
  else if (act === 'theme') { S.theme = el.dataset.v; save(); render(); }
  else if (act === 'tab') { ui.tab = el.dataset.v; render(); }
  else if (act === 'shuffle') { S.seed = (S.seed % 9999) + 1; save(); refresh(); }
  else if (act === 'want') { ui.pay = true; refresh(); const b = $('#paybox'); if (b) b.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }
  else if (act === 'key') { applyKey($('#key').value, true).then(refresh); }
  else if (act === 'download') {
    if (!current || !pass.paid || !JsPDF) return;
    const name = (S.title || 'our-crossword').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'our-crossword';
    toPdf(current.out.pages, JsPDF).save(`${name}-${S.size}.pdf`);
  }
});

document.addEventListener('input', (ev) => {
  const el = ev.target;
  if (el.dataset.d) { S[el.dataset.d] = el.value; if (el.tagName === 'SELECT') { save(); refresh(); } else soon(); }
  else if (el.dataset.f) { S.entries[Number(el.closest('.entry').dataset.i)][el.dataset.f] = el.value; soon(); }
});

render();
startPass();
