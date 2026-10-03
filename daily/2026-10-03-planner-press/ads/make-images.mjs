// Makes the Planner Press still ads from real pages drawn by the product.
// Run from the build folder: node ads/make-images.mjs
import { chromium } from '/opt/npm-tools/node_modules/playwright/index.mjs';
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const OUT = path.join(HERE, 'images');
const SCRATCH = '/tmp/claude-0/-home-claude-claudes-choice/e26d0668-ab2a-56ca-9d30-9d847b2f5ab0/scratchpad/ppad-images';
const SHOTS = path.join(SCRATCH, 'shots');
fs.mkdirSync(OUT, { recursive: true });
fs.mkdirSync(SHOTS, { recursive: true });

const PORT = 4192;
const server = spawn('node', ['tools/dev-server.mjs', String(PORT)], { cwd: ROOT, stdio: 'ignore' });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// ---------- 1. capture real pages ----------
async function capture() {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1400, height: 1100 }, deviceScaleFactor: 3 });
  const page = await ctx.newPage();
  for (let i = 0; i < 40; i++) { try { const r = await fetch(`http://localhost:${PORT}/`); if (r.ok) break; } catch {} await sleep(250); }
  await page.goto(`http://localhost:${PORT}/`);
  await page.waitForSelector('#paper svg');
  const click = async (sel) => { await page.click(sel); await page.waitForSelector('#paper svg'); await sleep(150); };
  const snap = async (name) => {
    const el = await page.$('#paper svg');
    await el.screenshot({ path: path.join(SHOTS, name + '.png') });
  };
  const tap = {
    year: '[data-act="key-page"][data-v="year"]', month: '[data-act="key-page"][data-v="month"]',
    week: '[data-act="key-page"][data-v="week"]', day: '[data-act="key-page"][data-v="day"]',
  };
  for (const orient of ['landscape', 'portrait']) {
    await click(`[data-act="orient"][data-v="${orient}"]`);
    for (const theme of ['classic', 'sage', 'rose', 'night']) {
      await click(`[data-act="theme"][data-v="${theme}"]`);
      for (const k of ['year', 'month', 'week', 'day']) {
        await click(tap[k]);
        await snap(`${orient}-${theme}-${k}`);
      }
    }
  }
  await browser.close();
}

// ---------- 2. compose ads ----------
const img = (n) => 'file://' + path.join(SHOTS, n + '.png');
const CSS = `
*{box-sizing:border-box;margin:0;padding:0}
body{background:#f3f0e8;color:#1d2733;font-family:'DejaVu Serif',serif;overflow:hidden;position:relative}
.sans{font-family:'DejaVu Sans',sans-serif}
.pg{position:absolute;background:#fff;border-radius:6px;box-shadow:0 2px 4px rgba(29,39,51,.10),0 18px 40px rgba(29,39,51,.20)}
.pg img{display:block;width:100%;height:100%;border-radius:6px}
.h{position:absolute;font-weight:700;letter-spacing:-.01em;line-height:1.12}
.s{position:absolute;font-family:'DejaVu Sans',sans-serif;color:#5d6877;line-height:1.4}
.brand{position:absolute;font-family:'DejaVu Sans',sans-serif;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#2f5d8a}
.rule{position:absolute;height:4px;width:64px;background:#2f5d8a;border-radius:2px}
.pill{position:absolute;font-family:'DejaVu Sans',sans-serif;font-weight:700;color:#fff;background:#2f5d8a;border-radius:999px;text-align:center}
.lab{position:absolute;font-family:'DejaVu Sans',sans-serif;font-weight:700;color:#2f5d8a;text-align:center;letter-spacing:.08em;text-transform:uppercase}
`;
const L = 842 / 595; // landscape ratio w/h
const el = (cls, st, html = '') => `<div class="${cls}" style="${st}">${html}</div>`;
const pg = (n, x, y, w, h, extra = '') => `<div class="pg" style="left:${x}px;top:${y}px;width:${w}px;height:${h}px;${extra}"><img src="${img(n)}"></div>`;

// Pinterest pins, 1000x1500
const pinHead = (brand, head, sub, top = 110) =>
  el('brand', `left:80px;top:${top}px;font-size:26px`, brand) +
  el('rule', `left:80px;top:${top + 56}px`) +
  el('h', `left:80px;top:${top + 90}px;width:840px;font-size:84px`, head) +
  el('s', `left:80px;top:${top + 90 + 84 * 1.12 * (head.split('<br>').length) + 28}px;width:780px;font-size:34px`, sub);

const pin = (inner) => `<!doctype html><meta charset=utf-8><style>${CSS}body{width:1000px;height:1500px}</style><body>${inner}</body>`;
const sq = (inner) => `<!doctype html><meta charset=utf-8><style>${CSS}body{width:1080px;height:1080px}</style><body>${inner}</body>`;

const ads = [];

// Pin 1: tabs and tap to jump (portrait month page large, with callout)
ads.push({ file: 'pin-1-tabs.png', w: 1000, h: 1500, html: pin(
  pinHead('Planner Press', 'Every tab and<br>date is a tap', 'Month tabs on every page. Tap a date to open its week or day.') +
  pg('portrait-classic-month', 190, 560, 620, Math.round(620 * 842 / 595)) +
  ''
) });

// Pin 2: year, month, week and day, 2 x 2 with no overlap
{
  const w = 430, h = Math.round(w / L);
  const cells = [['year', 'Year', 60, 590], ['month', 'Month', 510, 590], ['week', 'Week', 60, 980], ['day', 'Day', 510, 980]];
  ads.push({ file: 'pin-2-four-pages.png', w: 1000, h: 1500, html: pin(
    pinHead('Planner Press', 'Year, month,<br>week and day', 'Four kinds of pages, all linked to each other.', 90) +
    cells.map(([k, n, x, y]) => pg('landscape-classic-' + k, x, y, w, h) + el('lab', `left:${x}px;top:${y + h + 16}px;width:${w}px;font-size:22px`, n)).join('')
  ) });
}

// Pin 3: four color looks, 2 x 2 with no overlap
{
  const cw = 310, ch = Math.round(cw * 842 / 595);
  const names = ['classic', 'sage', 'rose', 'night'], lab = ['Classic', 'Sage', 'Rose', 'Night'];
  const inner = pinHead('Planner Press', 'Four color looks', 'Classic, Sage, Rose and Night. Change it and the page redraws.') +
    names.map((n, i) => {
      const x = 155 + (i % 2) * 380, y = 480 + Math.floor(i / 2) * 500;
      return pg(`portrait-${n}-month`, x, y, cw, ch) + el('lab', `left:${x}px;top:${y + ch + 14}px;width:${cw}px;font-size:22px`, lab[i]);
    }).join('');
  ads.push({ file: 'pin-3-colors.png', w: 1000, h: 1500, html: pin(inner) });
}

// Pin 4: 2027 in a minute
ads.push({ file: 'pin-4-minute.png', w: 1000, h: 1500, html: pin(
  pinHead('Planner Press', '2027, made<br>in a minute', 'Pick the year, the pages and a color. Download the PDF.') +
  pg('landscape-sage-week', 70, 600, 860, Math.round(860 / L)) +
  el('pill', 'left:250px;top:1290px;width:500px;height:84px;line-height:84px;font-size:34px', 'Free to make') +
  el('s', 'left:0;top:1400px;width:1000px;text-align:center;font-size:28px', '$9 once to remove the credit line')
) });

// Square 1: portrait and landscape, side by side
{
  const wp = 424, hp = 600, wl = 480, hl = Math.round(wl / L);
  ads.push({ file: 'square-1-portrait-landscape.png', w: 1080, h: 1080, html: sq(
    el('brand', 'left:70px;top:64px;font-size:22px', 'Planner Press') +
    el('h', 'left:70px;top:112px;width:940px;font-size:62px', 'Tall or wide, your pick') +
    el('s', 'left:70px;top:200px;width:940px;font-size:28px', 'Portrait and landscape pages, with the same tabs on both.') +
    pg('portrait-rose-month', 73, 340, wp, hp) + el('lab', `left:73px;top:${340 + hp + 20}px;width:${wp}px;font-size:22px`, 'Portrait') +
    pg('landscape-rose-week', 527, 340 + hp - hl, wl, hl) + el('lab', `left:527px;top:${340 + hp + 20}px;width:${wl}px;font-size:22px`, 'Landscape')
  ) });
}

// Square 2: free to make
ads.push({ file: 'square-2-free.png', w: 1080, h: 1080, html: sq(
  el('brand', 'left:70px;top:64px;font-size:22px', 'Planner Press') +
  el('h', 'left:70px;top:112px;width:940px;font-size:68px', 'Free to make') +
  el('s', 'left:70px;top:205px;width:940px;font-size:28px', '$9 once to remove the credit line') +
  pg('landscape-night-month', 70, 330, 940, Math.round(940 / L))
) });

async function compose() {
  const browser = await chromium.launch();
  for (const a of ads) {
    const ctx = await browser.newContext({ viewport: { width: a.w, height: a.h }, deviceScaleFactor: 1 });
    const p = await ctx.newPage();
    const f = path.join(SCRATCH, a.file.replace('.png', '.html'));
    fs.writeFileSync(f, a.html);
    await p.goto('file://' + f);
    await p.waitForLoadState('load');
    await sleep(200);
    await p.screenshot({ path: path.join(OUT, a.file), clip: { x: 0, y: 0, width: a.w, height: a.h } });
    await ctx.close();
  }
  await browser.close();
}

try {
  if (!process.argv.includes('--skip-capture')) await capture();
  await compose();
} finally {
  server.kill();
}
