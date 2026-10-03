// Builds the how-to ad for Planner Press. Every frame is the real page, driven by Playwright:
// a screenshot of the live preview plus the control in use, under a plain caption.
// Needs SP (scratch folder). Music is made separately into $SP/music.wav (see report), then muxed here.
// Usage: SP=<scratch> node make-ad.mjs
import { spawn, execFileSync } from 'node:child_process';
import { writeFile, mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
const { chromium } = await import('/opt/npm-tools/node_modules/playwright/index.mjs');
const SP = process.env.SP, ROOT = '/home/claude/claudes-choice/daily/2026-10-03-planner-press';
const OUT = `${SP}/frames`;
await mkdir(OUT, { recursive: true });

const server = spawn(process.execPath, ['tools/dev-server.mjs', '4191'], { cwd: ROOT, stdio: ['ignore', 'pipe', 'inherit'] });
await new Promise((ok) => server.stdout.once('data', ok));
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1100, height: 1500 }, deviceScaleFactor: 3, acceptDownloads: true });
await ctx.route(/googleapis|gstatic/, (r) => r.abort()); // no internet here; the page falls back to its own serif/sans
const pg = await ctx.newPage();
const comp = await (await browser.newContext({ viewport: { width: 1080, height: 1920 } })).newPage();

let n = 0;
const list = [];
const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
const shell = (inner) => `<!doctype html><meta charset="utf-8"><style>
*{box-sizing:border-box}html,body{margin:0;width:1080px;height:1920px;background:#f3f0e8;color:#1d2733;font-family:"DejaVu Sans",sans-serif;overflow:hidden}
.cap{height:270px;padding:70px 70px 0;font-size:60px;line-height:1.16;font-weight:bold;letter-spacing:-.5px}
.cap small{display:block;font-size:30px;font-weight:normal;color:#2f5d8a;letter-spacing:3px;text-transform:uppercase;margin-bottom:14px}
.paper{height:900px;display:flex;align-items:center;justify-content:center}
.paper img{max-height:880px;max-width:960px;box-shadow:0 18px 50px rgba(29,39,51,.28);background:#fff}
.form{height:630px;display:flex;align-items:flex-start;justify-content:center;padding-top:30px}
.form img{max-width:960px;max-height:560px;border-radius:14px;box-shadow:0 8px 26px rgba(29,39,51,.16)}
.brand{position:absolute;left:0;right:0;bottom:44px;text-align:center;font-family:"DejaVu Serif",serif;font-size:36px;color:#2f5d8a}
.big{height:1920px;display:flex;flex-direction:column;justify-content:center;padding:0 90px;gap:36px}
.big h1{font-family:"DejaVu Serif",serif;font-size:100px;line-height:1.1;margin:0}
.big h1 em{color:#2f5d8a}
.big p{font-size:46px;line-height:1.35;margin:0;color:#5d6877}
.big .rule{width:200px;height:6px;background:#2f5d8a}
</style>${inner}`;

const emit = async (html, hold) => {
  const f = `${OUT}/${String(++n).padStart(4, '0')}.png`;
  await writeFile(`${SP}/frame.html`, html);
  await comp.goto(`file://${SP}/frame.html`);
  await comp.screenshot({ path: f });
  list.push({ f, hold });
};
const card = (h1, p, hold) => emit(shell(`<div class="big"><div class="rule"></div><h1>${h1}</h1><p>${p}</p></div>`), hold);

const frame = async (step, caption, formSel, hold) => {
  await pg.evaluate(() => { const t = document.querySelector('#toast'); if (t) t.hidden = true; });
  await pg.locator('#paper').screenshot({ path: `${SP}/paper-${n}.png` });
  await pg.locator(formSel).first().screenshot({ path: `${SP}/form-${n}.png` });
  await emit(shell(`<div class="cap"><small>${esc(step)}</small>${esc(caption)}</div>
    <div class="paper"><img src="paper-${n}.png"></div>
    <div class="form"><img src="form-${n}.png"></div><div class="brand">Planner Press</div>`), hold);
};
// A small ring where a finger would tap, drawn on the live page just for the screenshot.
const ring = async (loc) => {
  const b = await loc.boundingBox();
  await pg.evaluate(({ x, y }) => { const d = document.createElement('div'); d.id = 'tapring'; d.style.cssText = `position:fixed;left:${x - 22}px;top:${y - 22}px;width:44px;height:44px;border-radius:50%;border:5px solid #d8531f;background:rgba(216,83,31,.18);z-index:99;pointer-events:none`; document.body.appendChild(d); }, { x: b.x + b.width / 2, y: b.y + b.height / 2 });
};
const unring = () => pg.evaluate(() => { const d = document.getElementById('tapring'); if (d) d.remove(); });
const tap = async (loc, step, cap, formSel, hold1, hold2) => {
  await ring(loc); await frame(step, cap, formSel, hold1); await unring();
  await loc.click(); await pg.waitForTimeout(150);
  await frame(step, cap, formSel, hold2);
};
const links = (excludeTabs) => pg.locator(`#paper .lnk`);
// pick a link on the current page that is not a right-edge tab; by smallest width, then the n-th of those
const pickNonTab = async (which) => {
  const info = await pg.evaluate(() => {
    const pr = document.querySelector('#paper').getBoundingClientRect();
    return [...document.querySelectorAll('#paper .lnk')].map((e, i) => { const r = e.getBoundingClientRect(); return { i, x: r.x - pr.x, w: r.width, h: r.height, y: r.y - pr.y }; })
      .filter((o) => o.x + o.w < pr.width - 50);
  });
  return info[which] ? info[which].i : null;
};

try {
  await pg.goto('http://localhost:4191/'); await pg.waitForSelector('#paper svg');
  const chip = (act, v) => pg.locator(`[data-act="${act}"][data-v="${v}"]`);
  const P1 = '.panel:has([aria-label="Year"])', P2 = '.panel:has([aria-label="Sections"])', P3 = '.panel:has([aria-label="Color"])', NAV = '.sheet > .nav', STAT = '.sheet';

  await card('A planner for<br>your tablet,<br><em>made to order.</em>', 'Every tab and date is a tap.', 2.6);
  await frame('Step 1', 'Open the link. A 2027 planner is already made.', '#status', 2.3);

  await frame('Step 2', 'Pick the year and the week start.', P1, 0.5);
  await chip('weekstart', 1).click(); await frame('Step 2', 'Pick the year and the week start.', P1, 1.4);
  await chip('year', 2028).click(); await frame('Step 2', 'Pick the year and the week start.', P1, 0.9);
  await chip('year', 2027).click(); await frame('Step 2', 'Pick the year and the week start.', P1, 0.8);

  await frame('Step 3', 'Choose what goes in.', P2, 0.6);
  const notes = pg.locator('input[data-sec="notes"]');
  await notes.uncheck(); await frame('Step 3', 'Choose what goes in.', P2, 1.1);
  await pg.locator('input[data-sec="notes"]').check(); await frame('Step 3', 'Choose what goes in.', P2, 0.7);

  for (const [t, name] of [['sage', 'Sage'], ['rose', 'Rose'], ['night', 'Night']]) {
    if (!(await chip('theme', t).count())) continue;
    await chip('theme', t).click();
    await frame('Step 4', `Pick a color: ${name}.`, P3, 0.95);
  }
  await chip('orient', 'portrait').click(); await frame('Step 4', 'Pick a page shape: portrait.', P3, 1.3);
  await chip('orient', 'landscape').click(); await frame('Step 4', 'Or landscape.', P3, 0.9);
  await chip('theme', 'sage').click(); await frame('Step 4', 'Or landscape.', P3, 0.1);

  await frame('Step 5', 'Tap a month tab.', NAV, 0.4);
  await tap(pg.locator('#paper .lnk[data-page="4"]').first(), 'Step 5', 'Tap a month tab.', NAV, 0.8, 1.0);
  let k = await pickNonTab(4);
  if (k !== null) await tap(pg.locator('#paper .lnk').nth(k), 'Step 5', 'Tap a date for its week.', NAV, 0.7, 1.0);
  k = await pickNonTab(1);
  if (k !== null) await tap(pg.locator('#paper .lnk').nth(k), 'Step 5', 'Tap a day for its page.', NAV, 0.7, 1.0);
  await tap(pg.locator('#paper .lnk[data-page="1"]').first(), 'Step 5', 'The Year tab takes you back.', NAV, 0.7, 1.1);

  await frame('Step 6', 'Download the PDF.', '.pay', 0.7);
  const dl = pg.waitForEvent('download', { timeout: 120000 });
  await ring(pg.locator('[data-act="download"]')); await frame('Step 6', 'Download the PDF.', '.pay', 0.5); await unring();
  await pg.locator('[data-act="download"]').click(); await pg.waitForTimeout(60);
  await frame('Step 6', 'It builds on your device.', '.pay', 0.9);
  await dl; await pg.waitForTimeout(300);
  const pages = await pg.evaluate(() => (document.querySelector('#count').textContent.match(/whole planner is (\d+) pages/) || [])[1]);
  await frame('Step 6', `Done. ${pages} pages, every tab a link.`, '.pay', 1.3);

  await card('Planner <em>Press</em>', 'Free to make.<br>$9 once to remove the credit line.', 3.2);
} finally { await browser.close(); server.kill(); }

const total = list.reduce((s, x) => s + x.hold, 0);
await writeFile(`${SP}/list.txt`, 'ffconcat version 1.0\n' + list.map((x) => `file '${x.f}'\nduration ${x.hold.toFixed(3)}`).join('\n') + `\nfile '${list[list.length - 1].f}'\n`);
console.log(n, 'frames', total.toFixed(2), 'seconds');

if (existsSync(`${SP}/music.wav`)) {
  const fade = Math.max(0, total - 1.5);
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', `${SP}/list.txt`, '-i', `${SP}/music.wav`,
    '-vf', 'fps=30,format=yuv420p', '-af', `atrim=0:${total},afade=t=out:st=${fade}:d=1.5`, '-t', String(total),
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '24', '-profile:v', 'high', '-movflags', '+faststart', '-c:a', 'aac', '-b:a', '160k', `${ROOT}/ads/video/how-to.mp4`]);
  console.log('wrote how-to.mp4');
}
