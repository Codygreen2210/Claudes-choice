// node contactsheet.mjs page.html out_prefix   -> for every hand/prop contact the scene reports (rigReport(i).contacts, contact.js),
// finds its worst frame (a clip, or else the nearest-to-clipping frame) and renders it close up from 4 sides (front, both sides, top),
// (window.CAM.nohud: scenes hide camera-stuck overlays like gauges in close-ups) then joins them into out_prefix_sheet.png (one row per contact). Look at it before any render: a low cost or a clean number only says
// the hand is where you asked; the close-up shows whether that's how a person really holds or rests on the thing.
import http from 'http'; import fs from 'fs'; import path from 'path'; import { execFileSync } from 'child_process';
import { chromium } from 'playwright-core';
import { CHROME } from './browser.mjs';
process.env.GALLIUM_DRIVER = 'llvmpipe';
const [,, pg, prefix] = process.argv, S = 420;
const root = import.meta.dirname;
const srv = http.createServer((req, res) => { const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); res.end(); return; } res.writeHead(200, { 'Content-Type': p.endsWith('.js') ? 'text/javascript' : p.endsWith('.html') ? 'text/html' : 'application/octet-stream' }); res.end(d); }); }).listen(0);
const browser = await chromium.launch({ executablePath: CHROME, args: ['--use-gl=angle', '--use-angle=gl-egl', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: S, height: S } });
page.on('pageerror', e => console.log('[err]', e.message));
await page.goto(`http://127.0.0.1:${srv.address().port}/${pg}?w=${S}&h=${S}`);
await page.waitForFunction('window.READY === true', null, { timeout: 900000 });
const worst = await page.evaluate(() => { const W = {}; for (let i = 0; i < window.FRAMES; i += 2) { const r = window.rigReport(i); if (!r.show) continue;
  for (const c of (r.contacts || [])) { if (!c.at) continue; const k = c.S + '|' + c.prop, sc = c.verdict === 'CLIP' ? 1000 + c.depth : -c.near;
    if (!W[k] || sc > W[k].sc) W[k] = { sc, i, at: c.at, verdict: c.verdict, near: c.near, depth: c.depth, mode: c.mode }; } } return W; });
const rows = [];
for (const [k, w] of Object.entries(worst)) { const [Sd, prop] = k.split('|'), files = [];
  const views = [[0, 0.06, 0.32], [0.32, 0.06, 0], [-0.32, 0.06, 0], [0.02, 0.33, 0.04]];
  for (const [vi, off] of views.entries()) {
    const png = await page.evaluate(([i, at, off]) => { window.CAM = { pos: [at[0] + off[0], at[1] + off[1], at[2] + off[2]], tgt: at, fov: 34, nohud: true }; const d = window.renderAtT(i / 30); window.CAM = null; return d; }, [w.i, w.at, off]);
    const f = `${prefix}_${Sd}_${prop.replace(/\W+/g, '-')}_${vi}.png`; fs.writeFileSync(f, Buffer.from(png.split(',')[1], 'base64')); files.push(f); }
  rows.push({ files, label: `${Sd === 'R' ? 'right' : 'left'} hand / ${prop} (${w.mode}) at ${(w.i / 30).toFixed(2)}s: ${w.verdict}${w.verdict === 'CLIP' ? ' ' + w.depth + ' cm' : ''}, nearest ${w.near} mm` });
  console.log(rows[rows.length - 1].label); }
await browser.close(); srv.close();
if (rows.length) { execFileSync('python3', ['-c', `
import json, sys
from PIL import Image, ImageDraw
rows = json.loads(sys.argv[1]); S = ${S}
W = Image.new('RGB', (S * 4, (S + 28) * len(rows)), (16, 16, 18)); d = ImageDraw.Draw(W)
for r, row in enumerate(rows):
    y = r * (S + 28); d.text((8, y + 8), row['label'], fill=(255, 220, 80))
    for c, f in enumerate(row['files']): W.paste(Image.open(f), (c * S, y + 28))
W.save(sys.argv[2])`, JSON.stringify(rows), `${prefix}_sheet.png`]); console.log(`sheet: ${prefix}_sheet.png`); }
else console.log('no contacts reported (does rigReport return contacts?)');
