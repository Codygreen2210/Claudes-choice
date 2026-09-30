// LaunchReel Studio: the editor. The same timeline code the exporter uses runs here, so what
// you scrub is what you export. Only changing what gets clicked needs a new capture.
import { buildTimeline, frameAt } from '/lib/timeline.mjs';

const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const KEYS = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B'];
const STAGE = { landscape: [1920, 1080], vertical: [1080, 1920], square: [1080, 1080] };
const KINDS = ['click', 'hover', 'type', 'scroll', 'zoom', 'wait'];

let setup, script, fmt = 'landscape', tl = null, sel = 0, playing = false, t = 0, stale = false, muted = false;
const caps = {}; // format -> capture result
let frameReady = false;

const kindOf = (s) => KINDS.find((k) => k in s) || 'caption';
const fmtTime = (x) => `${Math.floor(x / 60)}:${(x % 60).toFixed(1).padStart(4, '0')}`;
function toast(msg, bad = false, ms = 3500) { const el = $('#toast'); el.textContent = msg; el.className = bad ? 'bad' : ''; el.style.display = 'block'; clearTimeout(toast.t); toast.t = setTimeout(() => (el.style.display = 'none'), ms); }
const debounce = (fn, ms) => { let h; return (...a) => { clearTimeout(h); h = setTimeout(() => fn(...a), ms); }; };
async function api(path, data) {
  const r = await fetch(path, data ? { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(data) } : undefined);
  const ct = r.headers.get('content-type') || '';
  const out = ct.includes('json') ? await r.json() : await r.text();
  if (!r.ok) throw new Error(out.error || out || r.statusText);
  return out;
}

// ---------- the script, with edits that don't need a new capture ----------
function editedEvents(cap) {
  const ev = cap.events.map((e) => ({ ...e }));
  script.steps.forEach((s, i) => {
    const capEv = i === 0 ? ev[0] : ev[i + 1];
    if (capEv) capEv.caption = s.caption === undefined ? (i === 0 ? '' : undefined) : s.caption;
    const own = ev[i + 1];
    if (!own) return;
    if (s.hold != null) own.hold = Number(s.hold);
    if (own.kind === 'wait' && s.wait != null) own.ms = Number(s.wait);
    if (own.kind === 'scroll' && s.scroll != null) own.by = Number(s.scroll);
  });
  return ev;
}
function rebuild() {
  const cap = caps[fmt];
  if (!cap) { tl = null; drawStrip(); return; }
  const v = setup.views[fmt];
  const follow = script.follow === false ? 1 : Math.min(Number(script.follow) || 1.4, fmt === 'vertical' ? 1.15 : 3);
  tl = buildTimeline(editedEvents(cap), { view: { w: v[0], h: v[1] }, states: cap.states, pace: Number(script.pace) || 1, follow, title: script.intro !== false, outro: script.outro !== false });
  t = Math.min(t, tl.duration);
  pushTL(); drawStrip(); loadMusic();
}
function pushTL() { const w = $('#frame').contentWindow; if (frameReady && w && tl && typeof w.draw === 'function') { w.TL = tl; w.draw(t); } }

// ---------- preview frame ----------
const refreshStudio = debounce(async () => {
  const cap = caps[fmt];
  $('#empty').hidden = !!cap;
  if (!cap) return;
  try {
    const html = await api('/api/studio', { id: cap.id, script: { ...script, _events: editedEvents(cap) } });
    frameReady = false;
    const f = $('#frame');
    f.onload = async () => { if (typeof f.contentWindow.draw !== 'function') return; await f.contentWindow.ready; frameReady = true; pushTL(); };
    f.srcdoc = html;
  } catch (e) { toast(e.message, true); }
}, 250);
function fitStage() {
  const [W, H] = STAGE[fmt];
  const box = $('#stage').getBoundingClientRect();
  const k = Math.min((box.width - 32) / W, (box.height - 32) / H);
  const fb = $('#frameBox'); fb.style.width = W * k + 'px'; fb.style.height = H * k + 'px';
  const f = $('#frame'); f.style.width = W + 'px'; f.style.height = H + 'px'; f.style.transform = `scale(${k})`;
}
function drawAt(x) {
  t = Math.max(0, Math.min(x, tl ? tl.duration : 0));
  const w = $('#frame').contentWindow;
  if (frameReady && w && typeof w.draw === 'function' && w.TL && tl) w.draw(t);
  $('#time').textContent = `${fmtTime(t)} / ${fmtTime(tl ? tl.duration : 0)}`;
  const tr = $('#tracks').getBoundingClientRect();
  $('#playhead').style.left = 12 + (tl ? (t / tl.duration) * (tr.width - 24) : 0) + 'px';
}

// ---------- playback (the music is the clock) ----------
let last = 0;
function loop(now) {
  if (!playing) return;
  const a = $('#audio');
  if (!muted && a.src && !a.paused) t = a.currentTime; else t += (now - last) / 1000;
  last = now;
  if (tl && t >= tl.duration) { t = 0; if (!muted) a.currentTime = 0; }
  drawAt(t);
  requestAnimationFrame(loop);
}
function play(on) {
  if (!tl) return toast('Capture first, then press play.');
  playing = on; $('#play').textContent = on ? '❚❚' : '▶'; $('#play').setAttribute('aria-label', on ? 'Pause' : 'Play');
  const a = $('#audio');
  if (on) { if (!muted) { a.currentTime = t; a.play().catch(() => {}); } last = performance.now(); requestAnimationFrame(loop); }
  else a.pause();
}
function seek(x) { drawAt(x); const a = $('#audio'); if (a.src) a.currentTime = t; }

// ---------- music ----------
const loadMusic = debounce(async () => {
  if (!tl) return;
  try {
    const cap = caps[fmt];
    let buf;
    if (cap) buf = await (await fetch('/api/audio', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ id: cap.id, script: { ...script, _events: editedEvents(cap) } }) })).arrayBuffer();
    else {
      const m = script.music;
      const q = new URLSearchParams({ genre: m.genre, key: m.key, seed: m.seed, bpm: m.bpm || '', volume: m.volume ?? 0.45, seconds: (tl.duration + 0.6).toFixed(1) });
      for (const p of ['drums', 'bass', 'chords', 'lead']) q.set(p, m.parts?.[p] === false ? '0' : '1');
      buf = await (await fetch('/api/music?' + q)).arrayBuffer();
    }
    if (new TextDecoder().decode(new Uint8Array(buf, 0, 4)) !== 'RIFF') throw new Error(new TextDecoder().decode(buf).slice(0, 200));
    const a = $('#audio'); const wasPlaying = playing && !muted;
    a.src = URL.createObjectURL(new Blob([buf], { type: 'audio/wav' }));
    a.currentTime = t; if (wasPlaying) a.play().catch(() => {});
    drawWave(new DataView(buf)); drawVoiceBand();
  } catch (e) { toast('Sound: ' + e.message, true); }
}, 350);
function drawVoiceBand() {
  const b = $('#voiceBand'); const v = script.voice;
  if (!v || !v.id || !tl) { b.hidden = true; return; }
  b.hidden = false; b.style.left = (v.at / tl.duration) * 100 + '%'; b.style.width = Math.min(100 - (v.at / tl.duration) * 100, (v.seconds / tl.duration) * 100) + '%';
}
function drawWave(dv) {
  const c = $('#wave'); const w = (c.width = c.clientWidth * devicePixelRatio), h = (c.height = c.clientHeight * devicePixelRatio);
  const g = c.getContext('2d'); g.clearRect(0, 0, w, h); g.fillStyle = 'rgba(120,230,180,.75)';
  const n = (dv.byteLength - 44) / 4, per = Math.max(1, Math.floor(n / w));
  for (let x = 0; x < w; x++) { let pk = 0; for (let i = x * per; i < (x + 1) * per && i < n; i += 8) pk = Math.max(pk, Math.abs(dv.getInt16(44 + i * 4, true))); const bh = (pk / 32767) * h * 0.9; g.fillRect(x, (h - bh) / 2, 1, Math.max(1, bh)); }
}

// ---------- timeline strip ----------
function drawStrip() {
  const ev = $('#evTrack'), cp = $('#capTrack'), ru = $('#ruler');
  ev.innerHTML = cp.innerHTML = ru.innerHTML = '';
  if (!tl) return;
  const D = tl.duration, pct = (x) => (x / D) * 100 + '%';
  const blk = (el, a, b, cls, text, step) => { const d = document.createElement('div'); d.className = 'blk ' + cls; d.style.left = pct(a); d.style.width = `calc(${pct(b - a)} - 2px)`; d.textContent = text; d.title = text; if (step != null) d.dataset.step = step; el.appendChild(d); };
  const m = tl.marks;
  if (m[0].t > 0.01) blk(ev, 0, m[0].t, 'card', 'Title card');
  for (let k = 0; k < m.length - 1; k++) {
    const step = k === 0 ? 0 : k - 1;
    const s = script.steps[step];
    if (!s || m[k + 1].t - m[k].t < 0.02) continue;
    const kind = kindOf(s);
    const label = k === 0 ? 'Open' : kind === 'caption' ? 'Pause' : `${kind[0].toUpperCase() + kind.slice(1)} ${s[kind] && typeof s[kind] !== 'object' ? '· ' + s[kind] : Array.isArray(s.type) ? '· ' + s.type[1] : ''}`;
    blk(ev, m[k].t, m[k + 1].t, 'ev' + (step === sel ? ' sel' : ''), label, step);
  }
  if (D - m.at(-1).t > 0.05) blk(ev, m.at(-1).t, D, 'card', 'End card');
  // Caption spans, read straight from the timeline.
  let cur = null, start = 0;
  for (let x = 0; x <= D + 0.05; x += 0.05) {
    const c = x <= D ? frameAt(tl, x).caption || null : null;
    if (c !== cur) { if (cur) blk(cp, start, x, 'cap', cur); cur = c; start = x; }
  }
  const stepS = D > 40 ? 5 : D > 16 ? 2 : 1;
  for (let x = 0; x <= D; x += stepS) { const s = document.createElement('span'); s.style.left = `calc(12px + (100% - 24px) * ${x / D})`; s.textContent = fmtTime(x).replace(/\.\d$/, ''); ru.appendChild(s); }
  drawAt(t);
}
$('#tracks').addEventListener('pointerdown', (e) => {
  if (!tl) return;
  const r = $('#tracks').getBoundingClientRect();
  const go = (ev) => seek(Math.max(0, Math.min(1, (ev.clientX - r.left - 12) / (r.width - 24))) * tl.duration);
  go(e);
  const b = e.target.closest('.blk'); if (b && b.dataset.step) selectStep(+b.dataset.step, false);
  const mv = (ev) => go(ev); const up = () => { removeEventListener('pointermove', mv); removeEventListener('pointerup', up); };
  addEventListener('pointermove', mv); addEventListener('pointerup', up);
});

// ---------- steps panel + inspector ----------
function markStale() { stale = true; $('#stale').hidden = !Object.keys(caps).length; }
function renderSteps() {
  const box = $('#steps'); box.innerHTML = '';
  script.steps.forEach((s, i) => {
    const k = kindOf(s);
    const tgt = k === 'type' ? `${s.type[0]} ← "${s.type[1]}"` : k === 'caption' ? 'caption only' : k === 'wait' ? `${s.wait} ms` : k === 'scroll' ? `${s.scroll}px` : s[k];
    const d = document.createElement('div');
    d.className = 'step'; d.tabIndex = 0; d.setAttribute('aria-selected', i === sel);
    d.innerHTML = `<div class="top"><span class="n">${i + 1}</span><span class="chip ${k}">${k === 'caption' ? 'text' : k}</span><span class="tg"></span></div><div class="cp"></div>`;
    d.querySelector('.tg').textContent = tgt; d.querySelector('.cp').textContent = s.caption || '';
    d.onclick = () => selectStep(i); d.onkeydown = (e) => { if (e.key === 'Enter') selectStep(i); };
    box.appendChild(d);
  });
}
function selectStep(i, jump = true) {
  sel = i; renderSteps(); renderInspector(); drawStrip();
  if (jump && tl) { const k = i === 0 ? 0 : i + 1; const m = tl.marks.find((x) => x.event === k); if (m) seek(m.t + 0.05); }
}
function renderInspector() {
  const s = script.steps[sel]; const box = $('#inspector');
  if (!s) { box.innerHTML = '<p class="note">Select a step to edit it.</p>'; return; }
  const k = kindOf(s);
  box.innerHTML = `
    <div class="h">Step ${sel + 1}</div>
    <label class="f">Action<select id="iKind">${['caption', ...KINDS].map((x) => `<option value="${x}" ${x === k ? 'selected' : ''}>${{ caption: 'Just a caption', click: 'Click', hover: 'Hover', type: 'Type', scroll: 'Scroll', zoom: 'Zoom in', wait: 'Pause' }[x]}</option>`).join('')}</select></label>
    <div id="iTarget"></div>
    <label class="f">Caption<textarea id="iCap" maxlength="70" placeholder="What should viewers notice?"></textarea></label>
    <label class="f">Hold after <span id="iHoldV"></span><input id="iHold" type="range" min="0.2" max="4" step="0.1"></label>
    <div class="row"><button class="btn" id="iUp">Move up</button><button class="btn" id="iDown">Move down</button><button class="btn" id="iDel" style="color:var(--bad)">Delete</button></div>
    <p class="note">Caption, hold and timing update the preview right away. Changing the action or target needs a new capture.</p>`;
  const tg = $('#iTarget');
  if (k === 'type') tg.innerHTML = `<label class="f">Field (text or selector)<input id="iF" type="text"></label><label class="f">Text to type<input id="iT" type="text"></label>`;
  else if (['click', 'hover', 'zoom'].includes(k)) tg.innerHTML = `<label class="f">Button text or CSS selector<input id="iF" type="text"></label>`;
  else if (k === 'scroll') tg.innerHTML = `<label class="f">Scroll by <span id="iSV"></span><input id="iS" type="range" min="-1500" max="2500" step="50"></label>`;
  else if (k === 'wait') tg.innerHTML = `<label class="f">Pause <span id="iWV"></span><input id="iW" type="range" min="300" max="4000" step="100"></label>`;
  $('#iCap').value = s.caption || '';
  $('#iCap').oninput = (e) => { s.caption = e.target.value; renderSteps(); rebuild(); refreshStudio(); };
  const hold = s.hold ?? 1; $('#iHold').value = hold; $('#iHoldV').textContent = hold + 's';
  $('#iHold').oninput = (e) => { s.hold = +e.target.value; $('#iHoldV').textContent = s.hold + 's'; rebuild(); };
  $('#iKind').onchange = (e) => { const nk = e.target.value; for (const x of KINDS) delete s[x]; if (nk === 'type') s.type = ['input', 'hello']; else if (nk === 'scroll') s.scroll = 500; else if (nk === 'wait') s.wait = 1200; else if (nk !== 'caption') s[nk] = 'Get started'; markStale(); renderSteps(); renderInspector(); };
  if ($('#iF')) { $('#iF').value = k === 'type' ? s.type[0] : s[k]; $('#iF').oninput = (e) => { if (k === 'type') s.type[0] = e.target.value; else s[k] = e.target.value; markStale(); renderSteps(); }; }
  if ($('#iT')) { $('#iT').value = s.type[1]; $('#iT').oninput = (e) => { s.type[1] = e.target.value; markStale(); renderSteps(); }; }
  if ($('#iS')) { $('#iS').value = s.scroll; $('#iSV').textContent = s.scroll + 'px'; $('#iS').oninput = (e) => { s.scroll = +e.target.value; $('#iSV').textContent = s.scroll + 'px'; renderSteps(); rebuild(); }; }
  if ($('#iW')) { $('#iW').value = s.wait; $('#iWV').textContent = (s.wait / 1000).toFixed(1) + 's'; $('#iW').oninput = (e) => { s.wait = +e.target.value; $('#iWV').textContent = (s.wait / 1000).toFixed(1) + 's'; renderSteps(); rebuild(); }; }
  const move = (d) => { const j = sel + d; if (j < 0 || j >= script.steps.length) return; [script.steps[sel], script.steps[j]] = [script.steps[j], script.steps[sel]]; sel = j; markStale(); renderSteps(); renderInspector(); };
  $('#iUp').onclick = () => move(-1); $('#iDown').onclick = () => move(1);
  $('#iDel').onclick = () => { if (script.steps.length < 2) return toast('Keep at least one step.'); script.steps.splice(sel, 1); sel = Math.max(0, sel - 1); markStale(); renderSteps(); renderInspector(); };
}
$('#add').onclick = () => {
  const k = $('#addKind').value;
  const s = k === 'type' ? { type: ['input', 'hello'] } : k === 'scroll' ? { scroll: 500 } : k === 'wait' ? { wait: 1200 } : { [k]: 'Get started' };
  s.caption = '';
  script.steps.splice(sel + 1, 0, s); sel += 1; markStale(); renderSteps(); renderInspector();
};

// ---------- text + style ----------
function renderText() {
  $('#tTitle').value = script.title || ''; $('#tTag').value = script.tagline || ''; $('#tCta').value = script.cta || '';
  const bindText = (id, key) => ($(id).oninput = (e) => { script[key] = e.target.value; if (key === 'title') $('#title').value = script.title; refreshStudio(); });
  bindText('#tTitle', 'title'); bindText('#tTag', 'tagline'); bindText('#tCta', 'cta');
  const box = $('#styles'); box.innerHTML = '';
  for (const [k, v] of Object.entries(setup.styles)) {
    const b = document.createElement('button'); b.className = 'sty'; b.setAttribute('aria-pressed', (script.captionStyle || 'clean') === k);
    b.innerHTML = `<span style="font-family:'${v.font}',sans-serif;font-weight:${v.weight}">Ship it fast</span><small></small>`;
    b.querySelector('span').textContent = 'Sign up in one step'.split(' ').slice(0, 3).join(' ');
    b.querySelector('small').textContent = v.label;
    b.onclick = () => { script.captionStyle = k; $$('.sty').forEach((x) => x.setAttribute('aria-pressed', x === b)); refreshStudio(); };
    box.appendChild(b);
  }
  const pace = $('#pace'); pace.value = script.pace ?? 1; $('#paceV').textContent = (+pace.value).toFixed(2) + '×';
  pace.oninput = () => { script.pace = +pace.value; $('#paceV').textContent = (+pace.value).toFixed(2) + '×'; rebuild(); };
  const fol = $('#follow'); fol.value = script.follow === false ? 1 : script.follow ?? 1.4; $('#followV').textContent = +fol.value <= 1 ? 'off' : (+fol.value).toFixed(2) + '×';
  fol.oninput = () => { script.follow = +fol.value <= 1 ? false : +fol.value; $('#followV').textContent = +fol.value <= 1 ? 'off' : (+fol.value).toFixed(2) + '×'; rebuild(); };
  for (const id of ['intro', 'outro']) { const b = $('#' + id); b.setAttribute('aria-pressed', script[id] !== false); b.onclick = () => { script[id] = script[id] === false; b.setAttribute('aria-pressed', script[id] !== false); rebuild(); }; }
}

// ---------- music panel ----------
function renderMusic() {
  const m = script.music;
  const box = $('#genres'); box.innerHTML = '';
  for (const [k, v] of Object.entries(setup.genres)) {
    const b = document.createElement('button'); b.className = 'gen'; b.setAttribute('aria-pressed', m.genre === k);
    b.innerHTML = '<b></b><span></span>'; b.querySelector('b').textContent = v.label; b.querySelector('span').textContent = `${v.blurb} · ${v.bpm} bpm`;
    b.onclick = () => { m.genre = k; m.bpm = setup.genres[k].bpm; $$('.gen').forEach((x) => x.setAttribute('aria-pressed', x === b)); syncBpm(); loadMusic(); };
    box.appendChild(b);
  }
  $('#key').innerHTML = KEYS.map((k) => `<option ${k === m.key ? 'selected' : ''}>${k}</option>`).join('');
  $('#key').onchange = (e) => { m.key = e.target.value; loadMusic(); };
  const syncBpm = () => { $('#bpm').value = m.bpm || setup.genres[m.genre].bpm; $('#bpmV').textContent = $('#bpm').value + ' bpm'; };
  syncBpm();
  $('#bpm').oninput = (e) => { m.bpm = +e.target.value; $('#bpmV').textContent = m.bpm + ' bpm'; loadMusic(); };
  $$('#parts button').forEach((b) => { const p = b.dataset.p; b.setAttribute('aria-pressed', m.parts?.[p] !== false); b.onclick = () => { m.parts = m.parts || {}; m.parts[p] = m.parts[p] === false; b.setAttribute('aria-pressed', m.parts[p] !== false); loadMusic(); }; });
  $('#vol').value = m.volume ?? 0.45; $('#vol').oninput = (e) => { m.volume = +e.target.value; loadMusic(); };
  $('#newTake').onclick = () => { m.seed = (m.seed || 1) + 1; loadMusic(); toast(`Take ${m.seed}`); };
  $('#musicOff').setAttribute('aria-pressed', !!m.off);
  $('#musicOff').onclick = () => { m.off = !m.off; $('#musicOff').setAttribute('aria-pressed', m.off); loadMusic(); };
  script.sfx = script.sfx || { on: true, volume: 0.7, off: [] };
  const fx = script.sfx; fx.off = fx.off || [];
  $('#sfxOn').setAttribute('aria-pressed', fx.on !== false);
  $('#sfxOn').onclick = () => { fx.on = fx.on === false; $('#sfxOn').setAttribute('aria-pressed', fx.on !== false); loadMusic(); };
  $$('#sfxKinds [data-k]').forEach((b) => { const k = b.dataset.k; b.setAttribute('aria-pressed', !fx.off.includes(k)); b.onclick = () => { fx.off = fx.off.includes(k) ? fx.off.filter((x) => x !== k) : [...fx.off, k]; b.setAttribute('aria-pressed', !fx.off.includes(k)); loadMusic(); }; });
  $('#sfxVol').value = fx.volume ?? 0.7; $('#sfxVol').oninput = (e) => { fx.volume = +e.target.value; loadMusic(); };
  renderVoice();
  $('#mute').onclick = () => { muted = !muted; $('#mute').setAttribute('aria-pressed', muted); if (muted) $('#audio').pause(); else if (playing) { $('#audio').currentTime = t; $('#audio').play().catch(() => {}); } };
}

// ---------- voiceover ----------
function renderVoice() {
  const v = script.voice;
  const has = !!(v && v.id);
  $('#voiceCtl').hidden = !has; $('#voiceDel').hidden = !has;
  $('#voiceInfo').textContent = has ? `Voiceover: ${v.seconds?.toFixed(1) ?? '?'}s. The music drops under it automatically.` : 'Talk over your video. The music drops under your voice and comes back up in the gaps.';
  if (has) {
    $('#vAt').max = Math.max(1, (tl?.duration || 20) - 0.5).toFixed(1); $('#vAt').value = v.at ?? 0; $('#vAtV').textContent = (+$('#vAt').value).toFixed(1) + 's';
    $('#vVol').value = v.volume ?? 1;
  }
  drawVoiceBand();
}
async function uploadVoice(blob) {
  $('#voiceInfo').textContent = 'Adding your voiceover…';
  try {
    const r = await fetch('/api/voice', { method: 'POST', body: blob });
    const j = await r.json(); if (!r.ok) throw new Error(j.error);
    script.voice = { id: j.id, seconds: j.seconds, at: script.voice?.at ?? 0.6, volume: script.voice?.volume ?? 1 };
    renderVoice(); loadMusic(); toast('Voiceover added');
  } catch (e) { toast(e.message, true); renderVoice(); }
}
$('#voiceFile').onchange = (e) => { const f = e.target.files[0]; if (f) uploadVoice(f); e.target.value = ''; };
$('#voiceDel').onclick = () => { script.voice = null; renderVoice(); loadMusic(); };
$('#vAt').oninput = (e) => { script.voice.at = +e.target.value; $('#vAtV').textContent = script.voice.at.toFixed(1) + 's'; drawVoiceBand(); loadMusic(); };
$('#vVol').oninput = (e) => { script.voice.volume = +e.target.value; loadMusic(); };
let recorder = null;
$('#rec').onclick = async () => {
  if (recorder) { recorder.stop(); return; }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const chunks = []; recorder = new MediaRecorder(stream);
    recorder.ondataavailable = (e) => chunks.push(e.data);
    recorder.onstop = () => { stream.getTracks().forEach((x) => x.stop()); recorder = null; $('#rec').textContent = '● Record'; uploadVoice(new Blob(chunks, { type: chunks[0]?.type || 'audio/webm' })); };
    recorder.start(); $('#rec').textContent = '■ Stop'; t = 0; play(true); toast('Recording. The video plays so you can talk over it. Press Stop when done.', false, 5000);
  } catch { toast("Couldn't use the microphone. Check your browser's permission, or upload a file instead.", true, 6000); }
};

// ---------- actions ----------
async function doCapture() {
  script.url = $('#url').value.trim();
  const btn = $('#capture'); btn.disabled = true; $('#status').textContent = 'Walking through your app…';
  try {
    const r = await api('/api/capture', { script, format: fmt });
    caps[fmt] = r; stale = false; $('#stale').hidden = true;
    if (!script.accent && r.meta.accent) $('#status').textContent = 'Picked up your app\'s colour';
    else $('#status').textContent = '';
    t = 0; rebuild(); refreshStudio(); toast(`Captured ${Object.keys(r.states).length} screens. Edit away: the preview updates live.`);
  } catch (e) { $('#status').textContent = ''; toast(e.message, true, 8000); }
  finally { btn.disabled = false; }
}
$('#capture').onclick = doCapture;
$('#aiGo').onclick = async () => {
  const url = $('#url').value.trim(); const prompt = $('#aiPrompt').value.trim();
  if (!prompt) return toast('Describe the video first.');
  const b = $('#aiGo'); b.disabled = true; $('#aiNote').textContent = 'Reading your page and writing the script…';
  try {
    const r = await api('/api/ai', { prompt, url, format: fmt });
    const s = r.script;
    script = { ...script, ...s, url, music: { ...script.music, ...(s.music || {}), seed: script.music.seed, parts: script.music.parts } };
    if (s.music?.genre) script.music.bpm = setup.genres[s.music.genre]?.bpm;
    sel = 0; $('#title').value = script.title || ''; renderSteps(); renderInspector(); renderText(); renderMusic();
    $('#aiNote').textContent = r.cap ? `Done. ${r.used} of ${r.cap} AI videos used this month.` : 'Done. Capturing it now…';
    await doCapture();
  } catch (e) { toast(e.message, true, 9000); $('#aiNote').textContent = 'Uses only buttons that are really on your page.'; }
  finally { b.disabled = false; }
};
// What the studio's ears said about the soundtrack that went into the video.
function earsHtml(e) {
  if (!e) return '';
  const h = (x) => String(x).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  if (e.skipped) return `<p class="note">Sound check skipped: ${h(e.skipped)}</p>`;
  const items = [...(e.fixed || []).map((f) => 'Fixed: ' + f), ...(e.warnings || []), ...(e.balance || [])];
  return `<div class="h">Sound check</div><p class="note">${e.ok && !(e.warnings || []).length ? 'Passed the studio ears.' : 'The studio ears flagged:'}</p>` +
    (items.length ? `<ul class="note">${items.map((i) => `<li>${h(i)}</li>`).join('')}</ul>` : '') +
    `<a href="${e.picture}" target="_blank"><img alt="Sound check picture" src="${e.picture}" style="width:100%;border-radius:6px"></a>`;
}
$('#export').onclick = async () => {
  const cap = caps[fmt]; if (!cap) return toast('Capture first.');
  if (stale) toast('Heads up: steps changed since the last capture; exporting what you see.', false, 5000);
  const b = $('#export'); b.disabled = true; play(false);
  $('#status').textContent = 'Rendering… (about a minute)';
  try {
    const r = await api('/api/export', { id: cap.id, script: { ...script, _events: editedEvents(cap) } });
    const box = $('#result'); box.hidden = false;
    box.innerHTML = `<div class="h">Exported</div><video controls src="${r.url}"></video><a class="btn primary" href="${r.url}" download>Download ${r.file}</a><p class="note">Also saved to ${r.path}</p>${earsHtml(r.ears)}`;
    toast('Exported ' + r.file);
  } catch (e) { toast(e.message, true, 8000); }
  finally { b.disabled = false; $('#status').textContent = ''; }
};
$('#save').onclick = async () => { try { const r = await api('/api/save', { script }); toast('Saved to ' + r.saved); } catch (e) { toast(e.message, true); } };
$('#play').onclick = () => play(!playing);
addEventListener('keydown', (e) => { if (e.code === 'Space' && !/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)) { e.preventDefault(); play(!playing); } });
$$('.seg button').forEach((b) => b.onclick = () => {
  fmt = b.dataset.fmt; $$('.seg button').forEach((x) => x.setAttribute('aria-pressed', x === b)); play(false); fitStage();
  frameReady = false; $('#frame').onload = null; $('#frame').srcdoc = ''; rebuild(); refreshStudio();
  if (!caps[fmt]) { $('#empty').hidden = false; $('#empty').querySelector('div').innerHTML = '<b>Not captured at this size yet</b>Press Capture: phone size uses a phone-shaped window of your app.'; }
});
$$('.tabs [role=tab]').forEach((b) => b.onclick = () => { $$('.tabs [role=tab]').forEach((x) => x.setAttribute('aria-selected', x === b)); $$('[data-pane]').forEach((p) => (p.hidden = p.dataset.pane !== b.dataset.tab)); });
$('#title').oninput = (e) => { script.title = e.target.value; $('#tTitle').value = script.title; refreshStudio(); };
$('#url').oninput = () => markStale();
addEventListener('resize', () => { fitStage(); drawStrip(); });

// ---------- start ----------
setup = await api('/api/setup');
if (setup.fontHead) document.head.insertAdjacentHTML('beforeend', setup.fontHead);
script = setup.script || { url: '', title: 'My app', tagline: '', cta: '', steps: [{ caption: 'Meet my app' }, { click: 'Get started', caption: 'Sign up in one step' }] };
script.music = { genre: 'lofi', key: 'F', seed: 7, volume: 0.45, parts: {}, ...(script.music || {}) };
if (script.music.mood && !script.music.genre) script.music.genre = script.music.mood;
if (!setup.genres[script.music.genre]) script.music.genre = { chill: 'lofi', bright: 'pop' }[script.music.genre] || 'lofi';
script.captionStyle = script.captionStyle || 'clean';
$('#url').value = script.url || ''; $('#title').value = script.title || 'My app';
renderSteps(); renderInspector(); renderText(); renderMusic(); fitStage(); drawStrip();
