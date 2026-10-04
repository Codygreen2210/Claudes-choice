// Lane Luck promo clip: real play of the game, captions burnt in, the studio track underneath.
//
//   python3 daily/2026-10-04-lane-luck/ads/make-track.py          # track.wav first (then listen.py on it)
//   node daily/2026-10-04-lane-luck/ads/make-clip.mjs             # lane-luck-vertical.mp4 + lane-luck-square.mp4
//
// The game's own files are loaded straight from disk and are not changed. They are served to the
// browser under the public address below (Playwright answers the requests from the folder, nothing
// goes over the network), so the result card prints the real address instead of localhost.
// To record through `python3 -m http.server` instead: BASE=http://localhost:8765 node make-clip.mjs
import { chromium } from 'playwright';
import { spawnSync } from 'node:child_process';
import { mkdirSync, rmSync, writeFileSync, readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { join, extname, normalize } from 'node:path';
import { makeGame, scoreRound, summarize } from '../sim.js';

// ---- the one place the address lives ----
const SITE = 'lane-luck.vercel.app';

const SEED = 12505;            // round 1: the smart lane gets a declined card and comes in last
const FPS = 30;
const T = {                    // seconds; every cut sits on a beat of the 120 BPM track
  tap: 2.5,                    // finger goes down on the lane
  verdict: 9.5,                // race is over, verdict line shows
  card: 12.5,                  // jump to the result card
  end: 17.5,                   // end card
  total: 21.0,
};
const COLORS = { bg: '0xE9DCC6', ink: '0x2A2320', accent: '0xB8430F', soft: '0x6A5D55', line: '0xD9CBB6', paper: '0xFAF3E7' };
const FONT = '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf';
const VIEW = { width: 390, height: 572 };
const SCALE = 900 / 390;       // capture is 900 x 1320

const here = fileURLToPath(new URL('.', import.meta.url));
const gameDir = fileURLToPath(new URL('..', import.meta.url));
const work = join(here, '.work');
const frames = join(work, 'frames');
const track = join(here, 'track.wav');
if (!existsSync(track)) throw new Error('track.wav is missing: run make-track.py (and listen.py) first');
rmSync(work, { recursive: true, force: true });
mkdirSync(frames, { recursive: true });

// ---- the ten picks: the on-paper best lane, except two lazy "shortest queue" picks ----
const game = makeGame(SEED);
const picks = game.map((round, i) => {
  const best = scoreRound(round, 0).bestExpectedLane;
  if (i !== 3 && i !== 7) return best;
  let short = 0;
  round.lanes.forEach((l, k) => { if (l.shoppers.length < round.lanes[short].shoppers.length) short = k; });
  return short;
});
const first = scoreRound(game[0], picks[0]);
const maxT = Math.max(...first.times.map((t) => t.actual));
const raceMs = Math.max(6000, Math.min(9000, 6000 + (maxT - 300) * 5));   // same sum as app.js
const expected = summarize(game.map((round, i) => scoreRound(round, picks[i])));
console.log(`seed ${SEED}, picks ${picks.map((p) => p + 1).join(' ')}; round 1: ${first.text}`);
console.log(`card: "${expected.title}", top two ${expected.topTwo}/10, luck ${expected.luckShare}% / pick ${expected.pickShare}%`);

// ---- record the play, one screenshot per video frame, on a stepped clock ----
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml', '.png': 'image/png' };
const base = (process.env.BASE || `https://${SITE}`).replace(/\/$/, '');
const browser = await chromium.launch().catch(() => chromium.launch({ executablePath: '/opt/pw-browsers/chromium' }));
const ctx = await browser.newContext({ viewport: VIEW, deviceScaleFactor: SCALE, hasTouch: true, isMobile: true, colorScheme: 'light' });
if (!process.env.BASE) {
  await ctx.route('**/*', (route) => {
    const url = new URL(route.request().url());
    if (url.host !== SITE) return route.abort();
    const rel = normalize(url.pathname === '/' ? '/index.html' : url.pathname);
    const file = join(gameDir, rel);
    if (!file.startsWith(gameDir) || !existsSync(file)) return route.fulfill({ status: 404, body: 'not found' });
    return route.fulfill({ status: 200, contentType: MIME[extname(file)] || 'application/octet-stream', body: readFileSync(file) });
  });
}
const page = await ctx.newPage();
const errors = [];
page.on('pageerror', (e) => errors.push(e.message));
await page.clock.install({ time: new Date('2026-10-04T12:00:00') });
await page.goto(`${base}/?s=${SEED}`);
await page.waitForSelector('.lane');
await page.clock.pauseAt(new Date('2026-10-04T12:01:00'));

let n = 0;
const shot = async () => { await page.screenshot({ path: join(frames, String(n++).padStart(4, '0') + '.png') }); };
const step = async (ms) => { await page.clock.runFor(ms); };

// A: the five lanes, then a finger dot lands on the pick (the dot is laid over the page, not part of the game)
const tapFrames = Math.round(T.tap * FPS);
const box = await page.locator(`.lane[data-lane="${picks[0]}"]`).boundingBox();
const tx = box.x + box.width / 2, ty = box.y + box.height * 0.42;
for (let f = 0; f < tapFrames; f++) {
  const left = tapFrames - f;                       // frames until the tap
  if (left <= 14) {
    const p = 1 - left / 14;                        // 0..1 as the finger arrives
    await page.evaluate(([x, y, p]) => {
      let d = document.getElementById('__tap');
      if (!d) { d = document.createElement('div'); d.id = '__tap'; document.body.append(d); }
      const r = 34 - 12 * p;
      d.style.cssText = `position:fixed;left:${x - r}px;top:${y - r}px;width:${2 * r}px;height:${2 * r}px;border-radius:50%;` +
        `background:rgba(42,35,32,${0.18 + 0.3 * p});border:3px solid rgba(255,250,241,0.95);box-shadow:0 2px 10px rgba(0,0,0,.25);z-index:99;pointer-events:none`;
    }, [tx, ty, p]);
  }
  await shot();
}
await page.locator(`.lane[data-lane="${picks[0]}"]`).click();

// B: the race, fitted to its slot (the game runs it in raceMs; we step the clock to land on the beat)
const raceFrames = Math.round((T.verdict - T.tap) * FPS);
let sawBubble = false;
for (let f = 0; f < raceFrames; f++) {
  await step(raceMs / raceFrames);
  if (f < 10) await page.evaluate((o) => { const d = document.getElementById('__tap'); if (d) { d.style.opacity = String(o); d.style.transform = `scale(${1 + (1 - o) * 0.8})`; } }, 1 - (f + 1) / 10);
  if (f === 10) await page.evaluate(() => document.getElementById('__tap')?.remove());
  if (!sawBubble && await page.locator('.bubble:visible').count()) { sawBubble = true; console.log(`snag bubble on screen from ${(n / FPS).toFixed(2)} s`); }
  await shot();
}
if (!sawBubble) throw new Error('no snag bubble showed during the race');

// C: the verdict line
await step(400);
await page.locator('#next').waitFor({ state: 'visible' });
const verdictText = await page.locator('#verdict').innerText();
const verdictFrames = Math.round((T.card - T.verdict) * FPS);
for (let f = 0; f < verdictFrames; f++) { await step(1000 / FPS); await shot(); }

// rounds 2 to 10, off camera
for (let r = 1; r < 10; r++) {
  await page.locator('#next').click();
  await page.locator(`.lane[data-lane="${picks[r]}"]`).click();
  await step(10000);
  await page.locator('#next').waitFor({ state: 'visible' });
}
await page.locator('#next').click();
await page.locator('#result').waitFor({ state: 'visible' });
const score = await page.locator('#score').innerText();
const cardPng = await page.evaluate(() => document.getElementById('card').toDataURL('image/png'));
writeFileSync(join(work, 'card.png'), Buffer.from(cardPng.split(',')[1], 'base64'));
await browser.close();
if (errors.length) throw new Error('page errors: ' + errors.join('; '));
console.log(`recorded ${n} frames; verdict: ${verdictText.replace(/\n/g, ' ')}; ${score}`);

// ---- lay it out and encode ---- (AAC at 256k: at 192k the encoder overshot to +0.2 dB on two drum hits)
const CAPS = {
  c1a: 'You always pick', c1b: 'the slow lane.',
  c2: 'Or do you?',
  c3a: 'Ten rounds. Find out', c3b: "if it's luck or you.",
  title: 'Lane Luck', site: SITE,
};
for (const [k, v] of Object.entries(CAPS)) writeFileSync(join(work, k + '.txt'), v);

function text(key, { size, y, color = COLORS.ink, from, to }) {
  const fade = `alpha='min(1,max(0,(t-${from})/0.2))'`;
  return `drawtext=fontfile=${FONT}:textfile=${join(work, key + '.txt')}:fontsize=${size}:fontcolor=${color}:` +
    `x=(w-text_w)/2:y=${y}:${fade}:enable='between(t,${from},${to})'`;
}

function render(name, L) {
  const { W, H } = L;
  const end = T.total;
  const f = [
    `color=c=${COLORS.bg}:s=${W}x${H}:r=${FPS}:d=${end}[bg]`,
    `[0:v]scale=${L.game.w}:${L.game.h}:flags=lanczos,pad=iw+8:ih+8:4:4:color=${COLORS.line}[g]`,
    `[1:v]scale=${L.card.w}:${L.card.h}:flags=lanczos,pad=iw+8:ih+8:4:4:color=${COLORS.line}[c]`,
    `[bg][g]overlay=${L.game.x - 4}:${L.game.y - 4}:eof_action=pass:enable='lt(t,${T.card})'[v1]`,
    `[v1][c]overlay=${L.card.x - 4}:${L.card.y - 4}:enable='between(t,${T.card},${T.end})'[v2]`,
    '[v2]' + [
      text('c1a', { size: L.cap, y: L.capY, from: 0.15, to: T.tap + 0.9 }),
      text('c1b', { size: L.cap, y: L.capY + L.capLine, from: 0.15, to: T.tap + 0.9 }),
      text('c2', { size: L.big, y: L.bigY, color: COLORS.accent, from: T.tap + 1.5, to: T.card }),
      text('c3a', { size: L.cap3, y: L.capY, from: T.card, to: T.end }),
      text('c3b', { size: L.cap3, y: L.capY + L.capLine, from: T.card, to: T.end }),
      `drawbox=x=(iw-${L.bar})/2:y=${L.titleY - L.barGap}:w=${L.bar}:h=14:color=${COLORS.accent}:t=fill:enable='gte(t,${T.end})'`,
      text('title', { size: L.title, y: L.titleY, from: T.end, to: end }),
      text('site', { size: L.site, y: L.siteY, color: COLORS.accent, from: T.end + 0.3, to: end }),
      'format=yuv420p',
    ].join(',') + '[v]',
  ].join(';');
  const out = join(here, name);
  const r = spawnSync('ffmpeg', ['-y', '-loglevel', 'error',
    '-framerate', String(FPS), '-i', join(frames, '%04d.png'),
    '-loop', '1', '-framerate', String(FPS), '-t', String(end), '-i', join(work, 'card.png'),
    '-i', track,
    '-filter_complex', f, '-map', '[v]', '-map', '2:a',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-r', String(FPS), '-pix_fmt', 'yuv420p',
    '-c:a', 'aac', '-b:a', '256k', '-ar', '44100', '-t', String(end), '-movflags', '+faststart', out], { stdio: 'inherit' });
  if (r.status !== 0) throw new Error('ffmpeg failed for ' + name);
  console.log('wrote ' + out);
}

// Captions sit inside the middle 80% (vertical: x 108..972, y 192..1728; square: 108..972 both ways).
render('lane-luck-vertical.mp4', {
  W: 1080, H: 1920,
  game: { w: 818, h: 1200, x: 131, y: 500 },
  card: { w: 864, h: 1080, x: 108, y: 540 },
  cap: 84, cap3: 76, capY: 232, capLine: 108, big: 128, bigY: 262,
  title: 170, titleY: 760, bar: 200, barGap: 70, site: 34, siteY: 1030,
});
render('lane-luck-square.mp4', {
  W: 1080, H: 1080,
  game: { w: 532, h: 780, x: 274, y: 280 },
  card: { w: 624, h: 780, x: 228, y: 280 },
  cap: 56, cap3: 56, capY: 122, capLine: 70, big: 96, bigY: 136,
  title: 150, titleY: 400, bar: 180, barGap: 60, site: 34, siteY: 640,
});
if (!process.env.KEEP_WORK) rmSync(work, { recursive: true, force: true });
