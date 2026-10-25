// node armjerk.mjs page.html  -> renders every frame's pose in order (no drawing) and reports, per beat, the biggest
// frame-to-frame jump of each arm joint of the hold solver (deg/frame). Over ~6 deg/frame reads as a jerk.
import http from 'http'; import fs from 'fs'; import path from 'path';
import { chromium } from 'playwright-core';
process.env.GALLIUM_DRIVER = 'llvmpipe';
const [,, pg] = process.argv;
const root = import.meta.dirname;
const srv = http.createServer((req, res) => { const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); res.end(); return; } res.writeHead(200, { 'Content-Type': p.endsWith('.js') ? 'text/javascript' : p.endsWith('.html') ? 'text/html' : 'application/octet-stream' }); res.end(d); }); }).listen(0);
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell', args: ['--use-gl=angle', '--use-angle=gl-egl', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 90, height: 160 } });
page.on('pageerror', e => console.log('[err]', e.message));
await page.goto(`http://127.0.0.1:${srv.address().port}/${pg}?w=90&h=160&ao=0`);
await page.waitForFunction('window.READY === true', null, { timeout: 180000 });
const res = await page.evaluate(() => { const out = []; for (let i = 0; i < window.FRAMES; i++) { window.wristLog(); const r = window.rigReport(i); const L = window.wristLog();
  out.push([i, r.beat, L.R ? L.R.x : null, L.L ? L.L.x : null, r.ang]); } return out; });
const worst = {};
for (let i = 1; i < res.length; i++) for (const [si, S] of [[2, 'R'], [3, 'L']]) { const a = res[i - 1][si], b = res[i][si]; if (!a || !b || res[i - 1][1] !== res[i][1]) continue;
  let m = 0, mk = ''; for (const k of Object.keys(b)) { const d = Math.abs(b[k] - a[k]); if (d > m) { m = d; mk = k; } }
  const key = `b${res[i][1]} ${S}`; if (!worst[key] || m > worst[key][0]) worst[key] = [m, mk, (i / 30).toFixed(2)]; }
// all arm bones (posed result) too, incl. un-held arms
const bw = {};
for (let i = 1; i < res.length; i++) { const a = res[i - 1][4], b = res[i][4], bt = res[i][1]; if (res[i - 1][1] !== bt) continue;
  for (const n of ['uarmR', 'farmR', 'uarmL', 'farmL']) { if (!a[n] || !b[n]) continue; const d = Math.max(...b[n].map((v, j) => Math.abs(v - a[n][j]))); const key = `b${bt} ${n}`; if (!bw[key] || d > bw[key][0]) bw[key] = [d, (i / 30).toFixed(2)]; } }
for (const [k, v] of Object.entries(worst)) console.log('solver', k.padEnd(6), v[0].toFixed(1).padStart(6), 'deg/frame', v[1], 'at', v[2]);
{ const a = res[res.length - 1][2], b = res[0][2]; if (a && b) console.log('loop seam R', Math.max(...Object.keys(b).map(k => Math.abs(b[k] - a[k]))).toFixed(1), 'deg'); }
await browser.close(); srv.close();
