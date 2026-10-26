// node jointjerk.mjs page.html  -> for any 3D Short: steps every frame's pose in order (no drawing) and reports, per beat,
// the fastest joint (deg/frame) and the loop seam (last frame vs frame 0). Rig rule: <= 25 deg/frame inside a beat;
// over ~12 reads as a pop. Joints come from window.rigReport(i).ang (Euler triples, or [flex, abd, rot, elbow, roll] arms).
// A beat boundary is a cut, so the first frame of each beat is skipped; hips are reported relative to the car/rig base
// when rigReport gives `car` (a number = base height).
// Thumbs: if rigReport gives `thumbs` ([R, L] index-minus-little-knuckle vectors in his own frame, facing -z), any frame where
// the thumb side of a hand points backward (> 2.5 cm) without pointing up is a turned-around hand ("thumb on the wrong side").
// Only judged while that forearm hangs down (if rigReport gives `forearms`): with the elbow bent up past ~120 deg (a hammer curl,
// a phone at the ear) the thumb really does point back.
import http from 'http'; import fs from 'fs'; import path from 'path';
import { chromium } from 'playwright-core';
import { CHROME } from './browser.mjs';
process.env.GALLIUM_DRIVER = 'llvmpipe';
const [,, pg] = process.argv;
const root = import.meta.dirname;
const srv = http.createServer((req, res) => { const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); res.end(); return; } res.writeHead(200, { 'Content-Type': p.endsWith('.js') ? 'text/javascript' : p.endsWith('.html') ? 'text/html' : 'application/octet-stream' }); res.end(d); }); }).listen(0);
const browser = await chromium.launch({ executablePath: CHROME, args: ['--use-gl=angle', '--use-angle=gl-egl', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 90, height: 160 } });
page.on('pageerror', e => console.log('[err]', e.message));
await page.goto(`http://127.0.0.1:${srv.address().port}/${pg}?w=90&h=160&ao=0`);
await page.waitForFunction('window.READY === true', null, { timeout: 180000 });
const rows = await page.evaluate(() => { const out = []; for (let i = 0; i < window.FRAMES; i++) { const r = window.rigReport(i);
  out.push({ b: r.beat, ang: r.ang, hip: r.hips, car: typeof r.car === 'number' ? r.car : 0, show: r.show !== false, th: r.thumbs || null, fa: r.forearms || null }); } return out; });
await browser.close(); srv.close();
const diff = (a, b) => { let m = 0, k = ''; for (const n of Object.keys(b)) { if (!Array.isArray(b[n]) || !Array.isArray(a[n])) continue; const d = Math.max(...b[n].map((v, j) => Math.abs(v - a[n][j]))); if (d > m) { m = d; k = n; } } return [m, k]; };
const worst = {};
for (let i = 1; i < rows.length; i++) { const a = rows[i - 1], b = rows[i]; if (a.b !== b.b || !b.show) continue;
  const [m, k] = diff(a.ang, b.ang); const hipMove = Math.hypot(b.hip[0] - a.hip[0], (b.hip[1] - b.car) - (a.hip[1] - a.car), b.hip[2] - a.hip[2]);
  const w = worst[b.b] || (worst[b.b] = { m: 0, k: '', t: 0, hip: 0, th: 0 });
  if (m > w.m) Object.assign(w, { m, k, t: (i / 30).toFixed(2) });
  if (hipMove > w.hip) Object.assign(w, { hip: hipMove, th: (i / 30).toFixed(2) }); }
let bad = 0;
for (const [b, w] of Object.entries(worst)) { const flag = w.m > 25 ? '  POP' : w.m > 12 ? '  fast' : ''; if (w.m > 25) bad++;
  console.log(`beat ${b}: fastest joint ${w.k.padEnd(8)} ${w.m.toFixed(1).padStart(5)} deg/frame at ${w.t}s | hips ${(w.hip * 100).toFixed(1)} cm/frame at ${w.th}s${flag}`); }
const a = rows[rows.length - 1], z = rows[0];
const [sm, sk] = diff(a.ang, z.ang);
console.log(`loop seam: ${sm.toFixed(1)} deg (${sk}), hips ${(Math.hypot(a.hip[0] - z.hip[0], (a.hip[1] - a.car) - (z.hip[1] - z.car), a.hip[2] - z.hip[2]) * 100).toFixed(1)} cm (one frame of motion is normal)`);
let thumbBad = 0;
for (let i = 0; i < rows.length; i++) { const r = rows[i]; if (!r.th || !r.show) continue;
  r.th.forEach((v, j) => { const back = v[2], up = v[1]; if (r.fa && r.fa[j][1] > -0.5) return; if (back > 0.025 && up < 0.01) { if (thumbBad < 6) console.log(`THUMB: ${j ? 'left' : 'right'} hand turned around at ${(i / 30).toFixed(2)}s (beat ${r.b})`); thumbBad++; } }); }
if (rows[0].th) console.log(thumbBad ? `${thumbBad} frame-hands with the thumb on the wrong side` : 'thumbs: all on the right side');
console.log(bad || thumbBad ? `${bad} beat(s) with a pop, ${thumbBad} thumb flags` : 'clean');
