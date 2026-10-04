// Play-check for Cannon Collapse. From the repo root:
//   node daily/2026-10-04-cannon-collapse/tools/play-check.mjs [--quick]
// Starts its own static server, drives the game in headless Chromium, prints a per-level table.
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import fs from 'node:fs';

process.env.PLAYWRIGHT_BROWSERS_PATH ||= '/opt/pw-browsers';
const DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const PORT = 8000 + Math.floor(Math.random() * 900), URL = `http://127.0.0.1:${PORT}/index.html`;
const QUICK = process.argv.includes('--quick');
const ONLY = (process.argv.find(a => a.startsWith('--levels=')) || '').slice(9).split(',').filter(Boolean).map(n => +n - 1);
const N_SINGLE = QUICK ? 120 : 300, N_SEQ = QUICK ? 120 : 260;
const SCREENS = path.join(DIR, 'screens'); fs.mkdirSync(SCREENS, { recursive: true });
const fails = [], note = (ok, msg) => { console.log((ok ? 'PASS ' : 'FAIL ') + msg); if (!ok) fails.push(msg); };
const sleep = ms => new Promise(r => setTimeout(r, ms));

const server = spawn('python3', ['-m', 'http.server', String(PORT), '--bind', '127.0.0.1'], { cwd: DIR, stdio: 'ignore' });
await sleep(700);
const browser = await chromium.launch();
try {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, hasTouch: true, isMobile: true });
  const page = await ctx.newPage();
  const errors = [], foreign = [];
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', e => errors.push(String(e)));
  page.on('request', r => { const u = r.url(); if (!u.startsWith(`http://127.0.0.1:${PORT}/`) && !u.startsWith('data:')) foreign.push(u); });
  await page.goto(URL); await page.waitForFunction(() => window.__cc);
  const cdp = await ctx.newCDPSession(page);
  const touch = (type, x, y) => cdp.send('Input.dispatchTouchEvent', { type, touchPoints: type === 'touchEnd' ? [] : [{ x, y }] });
  const st = () => page.evaluate(() => window.__cc.state());

  // 1. load
  note((await page.title()) === 'Cannon Collapse (rough version)', 'title is right');
  const scroll = await page.evaluate(() => { const e = document.scrollingElement; return { sh: e.scrollHeight, sw: e.scrollWidth, ih: innerHeight, iw: innerWidth }; });
  note(scroll.sh <= scroll.ih && scroll.sw <= scroll.iw, `no page scroll at 390x844 (${JSON.stringify(scroll)})`);

  // 5a. one real touch drag: aim, see the arc, let go
  await touch('touchStart', 230, 640); 
  for (let i = 1; i <= 10; i++) { await touch('touchMove', 230 - 8.5 * i, 640 + 6 * i); await sleep(16); }
  await sleep(120);
  let s = await st();
  note(s.aiming && s.aim.power > 0.5 && s.aim.angle > 20 && s.aim.angle < 50, `touch drag aims (angle ${s.aim && s.aim.angle.toFixed(1)}, power ${s.aim && s.aim.power.toFixed(2)})`);
  await page.screenshot({ path: path.join(SCREENS, '1-aiming.png') });
  await touch('touchEnd'); await sleep(250);
  s = await st(); note(s.used === 1, 'letting go fires one shot');
  note(await page.evaluate(() => scrollY === 0 && scrollX === 0), 'page did not scroll during the drag');
  await page.evaluate(() => window.__cc.unlockAll());

  // 2. towers stand by themselves
  const nLevels = await page.evaluate(() => window.__cc.levels);
  const levels = ONLY.length ? ONLY : [...Array(nLevels).keys()];
  for (const i of levels) {
    const a = await page.evaluate(i => { window.__cc.goto(i); return window.__cc.state(); }, i);
    await sleep(3000);
    const b = await st();
    let worst = 0; b.blocks.forEach((k, j) => { worst = Math.max(worst, Math.hypot(k.x - k.hx, k.y - k.hy), Math.hypot(k.x - a.blocks[j].x, k.y - a.blocks[j].y), Math.abs(k.a) * 40); });
    note(worst < 2 && b.remaining === b.total && b.phase === 'aim', `level ${i + 1} stands still for 3 s (worst drift ${worst.toFixed(2)} px)`);
  }

  // 3. winnable, not trivial
  const table = []; let nearCase = null, winCase = null;
  for (const i of levels) {
    const r = await page.evaluate(({ i, N_SINGLE, N_SEQ }) => {
      let seed = 1234 + i * 99; const rnd = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
      const L = window.LEVELS[i], types = [...new Set(L.shots)];
      const shot = t => [5 + rnd() * 70, 0.25 + rnd() * 0.75, t];
      let single = 0, hit = 0;
      for (let k = 0; k < N_SINGLE; k++) { const o = window.__cc.run(i, [shot(types[Math.floor(rnd() * types.length)])]); if (o.phase === 'won') single++; if (o.remaining < L.blocks.length) hit++; }
      let wins = 0, near = 0, best = null, nearSeq = null; const t0 = performance.now();
      for (let k = 0; k < N_SEQ; k++) {
        const order = L.shots.slice().sort(() => rnd() - 0.5), seq = order.map(shot), o = window.__cc.run(i, seq);
        if (o.phase === 'won') { wins++; if (!best || o.used < best.used) best = { used: o.used, seq: seq.slice(0, o.used) }; }
        else if (o.phase === 'lost' && o.remaining <= 2) { near++; if (o.remaining === 1 && !nearSeq) nearSeq = seq; }
      }
      return { shots: L.shots.join(''), blocks: L.blocks.length, single: single / N_SINGLE, hit: hit / N_SINGLE, winRate: wins / N_SEQ, nearRate: near / N_SEQ, best, nearSeq, ms: Math.round(performance.now() - t0) };
    }, { i, N_SINGLE, N_SEQ });
    table.push({ level: i + 1, name: await page.evaluate(i => window.LEVELS[i].name, i), ...r });
    note(!!r.best, `level ${i + 1} is winnable within ${r.shots.length} shots` + (r.best ? ` (found a ${r.best.used}-shot clear)` : ''));
    if (i >= 2) note(r.single <= 0.35, `level ${i + 1} is not trivial (random first shot clears it ${(r.single * 100).toFixed(1)}% of the time)`);
    if (r.nearSeq && (!nearCase || i < 4)) nearCase = nearCase && nearCase.i < 4 ? nearCase : { i, seq: r.nearSeq };
    if (r.best && r.blocks >= 5) winCase = { i, seq: r.best.seq };
    if (r.best && !winCase) winCase = { i, seq: r.best.seq };
  }
  console.log('\nlevel | name              | shots | blocks | winnable | best | 1st random shot clears | random full attempts win | end 1-2 left');
  for (const t of table) console.log(`${String(t.level).padStart(5)} | ${t.name.padEnd(17)} | ${t.shots.padEnd(5)} | ${String(t.blocks).padStart(6)} | ${(t.best ? 'yes' : 'NO').padEnd(8)} | ${String(t.best ? t.best.used : '-').padStart(4)} | ${(t.single * 100).toFixed(1).padStart(21)}% | ${(t.winRate * 100).toFixed(1).padStart(23)}% | ${(t.nearRate * 100).toFixed(1).padStart(10)}%`);
  console.log('');
  fs.writeFileSync(path.join(SCREENS, 'table.json'), JSON.stringify(table, null, 1));

  // 4. near miss, played live
  if (!nearCase) note(false, 'found a run that ends with 1 block left');
  else {
    await page.evaluate(({ i, seq }) => { window.__cc.goto(i); window.__cc.queue(seq); }, nearCase);
    await page.waitForFunction(() => window.__cc.state().phase !== 'aim', null, { timeout: 60000 });
    await sleep(200); s = await st();
    note(s.phase === 'lost' && s.remaining === 1 && s.overlay && /^So close\. 1 block left\.$/.test(s.overlayText), `near miss shows "${s.overlayText}" (level ${nearCase.i + 1})`);
    const again = page.locator('#again'); note(await again.isVisible(), '"Again" button is showing');
    await page.screenshot({ path: path.join(SCREENS, '3-near-miss.png') });
    await page.evaluate(() => { const b = document.getElementById('again'); window.__tap = null;
      b.addEventListener('pointerdown', () => { window.__tap = { down: performance.now() }; }, { capture: true, once: true });
      const tick = () => { const q = window.__cc.state(); if (window.__tap && !window.__tap.done && q.phase === 'aim' && q.used === 0 && q.remaining === q.total && !q.overlay) { window.__tap.done = performance.now(); return; } requestAnimationFrame(tick); }; tick(); });
    const box = await again.boundingBox(); await page.touchscreen.tap(box.x + box.width / 2, box.y + box.height / 2);
    await page.waitForFunction(() => window.__tap && window.__tap.done, null, { timeout: 5000 });
    const ms = await page.evaluate(() => window.__tap.done - window.__tap.down);
    note(ms < 300, `"Again" resets the level in ${ms.toFixed(0)} ms (limit 300), straight back to aiming`);
  }

  // 5b. mid-collapse and level cleared screenshots, from a real clear
  if (winCase) {
    await page.evaluate(({ i, seq }) => { window.__cc.goto(i); window.__cc.queue(seq); }, winCase);
    await page.waitForFunction(() => window.__cc.state().blocks.some(b => !b.gone && Math.hypot(b.x - b.hx, b.y - b.hy) > 22), null, { timeout: 30000, polling: 'raf' });
    await page.screenshot({ path: path.join(SCREENS, '2-mid-collapse.png') });
    await page.waitForFunction(() => window.__cc.state().overlay, null, { timeout: 60000 });
    await sleep(250); s = await st();
    note(s.phase === 'won' && s.stars >= 1 && await page.locator('#nextBtn').isVisible(), `live replay clears level ${winCase.i + 1}: ${s.stars} star(s), "Next" showing`);
    await page.screenshot({ path: path.join(SCREENS, '4-cleared.png') });
  }
  note(errors.length === 0, 'no console errors' + (errors.length ? ': ' + errors.slice(0, 3).join(' | ') : ''));
  note(foreign.length === 0, 'no requests to other hosts' + (foreign.length ? ': ' + foreign.slice(0, 3).join(', ') : ''));
  await ctx.close();

  // small phone: fits, no scroll
  const c2 = await browser.newContext({ viewport: { width: 360, height: 640 }, deviceScaleFactor: 2, hasTouch: true, isMobile: true });
  const p2 = await c2.newPage(); await p2.goto(URL); await p2.waitForFunction(() => window.__cc);
  const sc2 = await p2.evaluate(() => { const e = document.scrollingElement; return e.scrollHeight <= innerHeight && e.scrollWidth <= innerWidth; });
  note(sc2, 'no page scroll at 360x640');
  await p2.evaluate(() => { window.__cc.goto(9); }); await sleep(200); await p2.screenshot({ path: path.join(SCREENS, '5-small-phone-level10.png') });
  await p2.evaluate(() => { window.__cc.goto(0); window.__cc.queue([[10, 0.2], [10, 0.2], [10, 0.2]]); });
  await p2.waitForFunction(() => window.__cc.state().overlay, null, { timeout: 60000 }); await sleep(200);
  await p2.screenshot({ path: path.join(SCREENS, '6-small-phone-out-of-shots.png') }); await c2.close();

  // desktop: mouse drag fires
  const c3 = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const p3 = await c3.newPage(); await p3.goto(URL); await p3.waitForFunction(() => window.__cc);
  const bx = await p3.locator('#c').boundingBox();
  await p3.mouse.move(bx.x + bx.width * 0.6, 500); await p3.mouse.down(); await p3.mouse.move(bx.x + bx.width * 0.6 - 80, 560, { steps: 8 });
  await sleep(100); await p3.screenshot({ path: path.join(SCREENS, '7-desktop-aiming.png') }); await p3.mouse.up(); await sleep(200);
  note((await p3.evaluate(() => window.__cc.state().used)) === 1, 'mouse drag on desktop fires a shot'); await c3.close();
} finally {
  await browser.close(); server.kill();
}
console.log(fails.length ? `\nPLAY-CHECK FAILED (${fails.length}):\n - ` + fails.join('\n - ') : '\nPLAY-CHECK PASSED');
process.exit(fails.length ? 1 : 0);
