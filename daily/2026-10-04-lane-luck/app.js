// Lane Luck: DOM, drawing and input. All game logic lives in sim.js.
import {
  makeGame, scoreRound, summarize, laneTimeline, seedFrom, fmtDuration, ordinal,
  ROUNDS, LANES, VERDICTS,
} from './sim.js';

const $ = (id) => document.getElementById(id);
const lanesEl = $('lanes');
const promptEl = $('prompt');
const stripEl = $('strip');
const verdictEl = $('verdict');
const nextBtn = $('next');
const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
const CHEVRONS = { quick: '›››', steady: '››', slow: '›' };
const FONT = 'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif';

let seed = 0;
let vs = null;
let game = [];
let roundIx = 0;
let results = [];
let phase = 'pick'; // pick | race | done | card
let shareText = '';

function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text != null) node.textContent = text;
  return node;
}
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
const clock = (s) => Math.floor(Math.round(s) / 60) + ':' + String(Math.round(s) % 60).padStart(2, '0');

function newSeed() {
  const buf = new Uint32Array(1);
  if (window.crypto && crypto.getRandomValues) crypto.getRandomValues(buf);
  else buf[0] = Math.floor(Math.random() * 4294967296);
  return (buf[0] % 900000) + 100000;
}

function setUrl() {
  const q = new URLSearchParams();
  q.set('s', String(seed));
  if (vs != null) q.set('vs', String(vs));
  history.replaceState(null, '', location.pathname + '?' + q.toString());
}

function start(fresh) {
  const q = new URLSearchParams(location.search);
  if (fresh) { seed = newSeed(); vs = null; }
  else {
    seed = q.has('s') && q.get('s') !== '' ? seedFrom(q.get('s')) : newSeed();
    const n = parseInt(q.get('vs'), 10);
    vs = q.has('vs') && n >= 0 && n <= ROUNDS ? n : null;
  }
  setUrl();
  game = makeGame(seed);
  roundIx = 0;
  results = [];
  const banner = $('banner');
  banner.hidden = vs == null;
  if (vs != null) banner.textContent = `A friend got ${vs} / ${ROUNDS} on these same ten rounds. Beat it.`;
  $('result').hidden = true;
  $('play').hidden = false;
  $('status').textContent = '';
  renderRound();
}

function cart(items, cls, label) {
  const c = el('span', 'cart' + (cls ? ' ' + cls : ''));
  c.style.height = 18 + Math.round(items * 0.6) + 'px';
  c.append(el('span', 'load'), el('span', 'n', label != null ? label : String(items)));
  return c;
}

function updateTop() {
  const s = summarize(results);
  $('round').textContent = `${Math.min(roundIx + 1, ROUNDS)} / ${ROUNDS}`;
  $('score').textContent = `Top two ${s.topTwo} · Wins ${s.wins}`;
}

function renderRound() {
  phase = 'pick';
  const round = game[roundIx];
  lanesEl.textContent = '';
  round.lanes.forEach((lane, i) => {
    const b = el('button', 'lane');
    b.type = 'button';
    b.dataset.lane = String(i);
    const items = lane.shoppers.map((s) => s.items);
    b.setAttribute('aria-label',
      `Lane ${i + 1}${lane.express ? ', express' : ''}: ${lane.label} cashier, ${items.length} waiting, carts of ${items.join(', ')} items`);
    const till = el('span', 'till');
    till.append(
      el('span', 'num', String(i + 1)),
      el('span', 'chev', CHEVRONS[lane.label]),
      el('span', 'speed', lane.label),
      el('span', 'tag', lane.express ? 'express' : ''),
    );
    const queue = el('span', 'queue');
    lane.shoppers.forEach((s) => queue.append(cart(s.items)));
    b.append(till, queue, el('span', 'foot'));
    b.addEventListener('click', () => pick(i));
    lanesEl.append(b);
  });
  stripEl.hidden = true;
  promptEl.textContent = `Your cart: ${round.playerItems} items. Tap the lane you'd join.`;
  updateTop();
}

function pick(i) {
  if (phase !== 'pick') return;
  phase = 'race';
  const round = game[roundIx];
  const res = scoreRound(round, i);
  const lanes = [...lanesEl.children];
  const state = lanes.map((b, k) => {
    b.disabled = true;
    const queue = b.querySelector('.queue');
    if (k === i) {
      b.classList.add('mine');
      b.querySelector('.tag').textContent = 'yours';
      queue.append(cart(round.playerItems, 'you', 'you'));
    } else {
      queue.append(cart(round.playerItems, 'ghost'));
    }
    const carts = [...queue.querySelectorAll('.cart')];
    const bubble = el('span', 'bubble');
    bubble.hidden = true;
    queue.append(bubble);
    return { b, carts, bubble, tl: laneTimeline(round, k), done: false };
  });
  promptEl.textContent = 'Racing. Dashed carts are ghost copies of your cart in the other lanes.';

  const maxT = Math.max(...res.times.map((t) => t.actual));
  const dur = reduced.matches ? 0 : clamp(6000 + (maxT - 300) * 5, 6000, 9000);
  const t0 = performance.now();

  function draw(t) {
    state.forEach((st, k) => {
      let active = false;
      let stalled = null;
      st.tl.forEach((seg, c) => {
        const node = st.carts[c];
        if (t >= seg.end) { node.hidden = true; return; }
        if (active) return;
        active = true;
        const span = seg.scanEnd - seg.start;
        node.style.setProperty('--left', String(1 - clamp((t - seg.start) / span, 0, 1)));
        if (seg.snag && t >= seg.scanEnd && t < seg.snagEnd) stalled = seg.snag.kind;
      });
      st.bubble.hidden = !stalled;
      if (stalled) st.bubble.textContent = stalled;
      if (!st.done && t >= res.times[k].actual) {
        st.done = true;
        const foot = st.b.querySelector('.foot');
        foot.append(el('b', '', ordinal(res.ranks[k])), document.createTextNode(clock(res.times[k].actual)));
        if (res.times[k].snagSeconds > 0) foot.append(el('span', 'snag', `snag +${clock(res.times[k].snagSeconds)}`));
      }
    });
  }

  function frame(now) {
    const p = dur ? Math.min(1, (now - t0) / dur) : 1;
    draw(p * maxT);
    if (p < 1) requestAnimationFrame(frame);
    else { draw(maxT + 1); finish(res); }
  }
  if (dur) requestAnimationFrame(frame); else frame(t0);
}

function finish(res) {
  phase = 'done';
  results.push(res);
  updateTop();
  promptEl.textContent = '';
  const cut = res.text.indexOf(':');
  verdictEl.textContent = '';
  verdictEl.append(el('strong', '', res.text.slice(0, cut)), document.createTextNode(res.text.charAt(cut + 2).toUpperCase() + res.text.slice(cut + 3)));
  nextBtn.textContent = roundIx + 1 >= ROUNDS ? 'See your card' : 'Next round';
  stripEl.hidden = false;
  nextBtn.focus({ preventScroll: true });
  nextBtn.scrollIntoView({ block: 'nearest', behavior: reduced.matches ? 'auto' : 'smooth' });
}

function next() {
  if (phase !== 'done') return;
  roundIx++;
  if (roundIx >= ROUNDS) showCard();
  else { renderRound(); window.scrollTo(0, 0); }
}

/* ---------- result card ---------- */

function challengeUrl(score) {
  return `${location.origin}${location.pathname}?s=${seed}&vs=${score}`;
}

function showCard() {
  phase = 'card';
  const s = summarize(results);
  $('play').hidden = true;
  $('result').hidden = false;
  const url = challengeUrl(s.topTwo);
  shareText = `I got ${s.topTwo}/${ROUNDS} on Lane Luck and it says ${s.pickShare}% of my bad luck was me. Same ten rounds: ${url}`;
  $('challenge').dataset.shareText = shareText;
  const canvas = $('card');
  drawCard(canvas, s, url);
  canvas.setAttribute('aria-label',
    `${s.title}. ${s.topTwo} of ${ROUNDS} in the top two, ${s.wins} wins. ` +
    `Time lost: ${fmtDuration(s.lost)}, ${s.luckShare}% luck and ${s.pickShare}% your pick.` +
    (vs != null ? ` Your friend got ${vs}.` : ''));
  window.scrollTo(0, 0);
  $('challenge').focus({ preventScroll: true });
}

function mark(ctx, key, x, y, r, ink) {
  ctx.save();
  ctx.lineWidth = r * 0.34;
  ctx.strokeStyle = ink;
  ctx.fillStyle = ink;
  ctx.lineCap = 'round';
  ctx.beginPath();
  if (key === 'gg') { ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill(); }
  else if (key === 'gb') { ctx.arc(x, y, r * 0.83, 0, Math.PI * 2); ctx.stroke(); }
  else if (key === 'bg') { ctx.moveTo(x, y - r); ctx.lineTo(x + r, y + r * 0.85); ctx.lineTo(x - r, y + r * 0.85); ctx.closePath(); ctx.fill(); }
  else { ctx.moveTo(x - r * 0.8, y - r * 0.8); ctx.lineTo(x + r * 0.8, y + r * 0.8); ctx.moveTo(x + r * 0.8, y - r * 0.8); ctx.lineTo(x - r * 0.8, y + r * 0.8); ctx.stroke(); }
  ctx.restore();
}

function fitText(ctx, text, weight, size, maxWidth) {
  do { ctx.font = `${weight} ${size}px ${FONT}`; size -= 2; } while (ctx.measureText(text).width > maxWidth && size > 18);
}

function drawCard(canvas, s, url) {
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  const ink = '#2a2320', soft = '#6a5d55', accent = '#b8430f', teal = '#1f6f6b', paper = '#faf3e7', line = '#d9cbb6';
  ctx.fillStyle = paper; ctx.fillRect(0, 0, W, H);
  // five lane stripes along the top
  for (let i = 0; i < 5; i++) {
    ctx.fillStyle = i === 3 ? accent : '#e9dcc6';
    ctx.fillRect(90 + i * 184, 0, 164, 46 + (i * 37) % 60);
  }
  ctx.textBaseline = 'alphabetic';
  ctx.fillStyle = soft; ctx.font = `700 34px ${FONT}`;
  ctx.fillText('Was it bad luck, or was it you?', 90, 190);
  ctx.fillStyle = ink; fitText(ctx, s.title, 800, 104, W - 180);
  ctx.fillText(s.title, 90, 310);

  ctx.font = `800 70px ${FONT}`;
  ctx.fillText(`${s.topTwo} / ${ROUNDS} in the top two`, 90, 440);
  ctx.fillStyle = soft; ctx.font = `600 36px ${FONT}`;
  ctx.fillText(`Fastest lane picked ${s.wins} of ${ROUNDS}. Random picking gets ${s.randomWins}.`, 90, 500);
  if (vs != null) {
    const d = s.topTwo - vs;
    const tail = d > 0 ? `You beat it by ${d}.` : d < 0 ? `You are ${-d} behind.` : 'Dead level.';
    ctx.fillStyle = teal; ctx.font = `700 36px ${FONT}`;
    ctx.fillText(`Your friend got ${vs} / ${ROUNDS}. ${tail}`, 90, 556);
  }

  // luck versus pick bar
  const bx = 90, by = 660, bw = W - 180, bh = 96;
  ctx.fillStyle = ink; ctx.font = `700 38px ${FONT}`;
  ctx.fillText(s.lost > 0 ? `Time lost to the fastest lane: ${fmtDuration(s.lost)}` : 'No time lost. Ten clean rounds.', bx, by - 26);
  const lw = s.lost > 0 ? Math.round(bw * s.lostToLuck / s.lost) : 0;
  ctx.fillStyle = '#fffaf1'; ctx.fillRect(bx, by, bw, bh);
  if (s.lost > 0) {
    ctx.fillStyle = teal; ctx.fillRect(bx, by, lw, bh);
    ctx.fillStyle = accent; ctx.fillRect(bx + lw, by, bw - lw, bh);
    ctx.save();
    ctx.beginPath(); ctx.rect(bx + lw, by, bw - lw, bh); ctx.clip();
    ctx.strokeStyle = paper; ctx.lineWidth = 6;
    for (let x = bx + lw - bh; x < bx + bw; x += 26) { ctx.beginPath(); ctx.moveTo(x, by + bh); ctx.lineTo(x + bh, by); ctx.stroke(); }
    ctx.restore();
  }
  ctx.strokeStyle = ink; ctx.lineWidth = 5; ctx.strokeRect(bx, by, bw, bh);
  ctx.font = `800 40px ${FONT}`;
  ctx.fillStyle = teal; ctx.textAlign = 'left';
  ctx.fillText(`Luck ${s.luckShare}%`, bx, by + bh + 56);
  ctx.fillStyle = accent; ctx.textAlign = 'right';
  ctx.fillText(`Your pick ${s.pickShare}%`, bx + bw, by + bh + 56);
  ctx.font = `600 30px ${FONT}`; ctx.fillStyle = soft;
  ctx.fillText(`${fmtDuration(s.lostToPick)} (striped)`, bx + bw, by + bh + 98);
  ctx.textAlign = 'left';
  ctx.fillText(`${fmtDuration(s.lostToLuck)} (solid)`, bx, by + bh + 98);

  // ten round marks
  const my = 950, step = (W - 180) / ROUNDS;
  results.forEach((r, i) => {
    const x = 90 + step * i + step / 2;
    mark(ctx, r.verdictKey, x, my, 26, ink);
    ctx.fillStyle = soft; ctx.font = `600 24px ${FONT}`; ctx.textAlign = 'center';
    ctx.fillText(String(i + 1), x, my + 62);
  });
  ctx.textAlign = 'left';
  Object.keys(VERDICTS).forEach((key, i) => {
    const x = 90 + (i % 2) * 460, y = 1068 + Math.floor(i / 2) * 50;
    mark(ctx, key, x + 14, y - 10, 13, ink);
    ctx.fillStyle = ink; ctx.font = `600 27px ${FONT}`;
    ctx.fillText(`${VERDICTS[key]} (${s.verdicts[key]})`, x + 42, y);
  });

  ctx.strokeStyle = line; ctx.lineWidth = 3;
  ctx.beginPath(); ctx.moveTo(90, 1168); ctx.lineTo(W - 90, 1168); ctx.stroke();
  ctx.fillStyle = soft; ctx.font = `600 28px ${FONT}`;
  ctx.fillText('Same ten rounds, your turn:', 90, 1216);
  ctx.fillStyle = ink; fitText(ctx, url, 700, 32, W - 180);
  ctx.fillText(url, 90, 1260);
  ctx.fillStyle = accent; ctx.font = `800 40px ${FONT}`; ctx.textAlign = 'right';
  ctx.fillText('lane-luck', W - 90, 1318);
  ctx.textAlign = 'left';
}

async function challenge() {
  const status = $('status');
  if (navigator.share) {
    try { await navigator.share({ text: shareText }); return; }
    catch (err) { if (err && err.name === 'AbortError') return; }
  }
  let ok = false;
  try { await navigator.clipboard.writeText(shareText); ok = true; }
  catch (err) {
    const ta = el('textarea');
    ta.value = shareText; ta.setAttribute('readonly', '');
    ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.append(ta); ta.select();
    try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
    ta.remove();
  }
  status.textContent = ok ? 'Copied' : shareText;
}

function saveCard() {
  $('card').toBlob((blob) => {
    if (!blob) return;
    const a = el('a');
    a.href = URL.createObjectURL(blob);
    a.download = `lane-luck-${seed}.png`;
    document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  }, 'image/png');
}

nextBtn.addEventListener('click', next);
$('challenge').addEventListener('click', challenge);
$('save').addEventListener('click', saveCard);
$('again').addEventListener('click', () => start(true));

document.addEventListener('keydown', (e) => {
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  if (phase === 'pick' && e.key >= '1' && e.key <= String(LANES)) {
    e.preventDefault();
    pick(Number(e.key) - 1);
    return;
  }
  if ((e.key === 'Enter' || e.key === ' ') && phase === 'done') {
    if (e.target && e.target.closest && e.target.closest('button, summary, a')) return; // native activation
    e.preventDefault();
    next();
  }
});

start(false);
