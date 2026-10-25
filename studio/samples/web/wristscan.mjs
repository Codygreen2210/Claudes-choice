// node wristscan.mjs page.html step  -> per beat, the largest wrist angles each hand was ASKED for (before clamping)
import http from 'http'; import fs from 'fs'; import path from 'path';
import { chromium } from 'playwright-core';
import { CHROME } from './browser.mjs';
process.env.GALLIUM_DRIVER = 'llvmpipe';
const [,, pg, stepS = '0.2'] = process.argv;
const root = import.meta.dirname;
const srv = http.createServer((req, res) => { const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); res.end(); return; } res.writeHead(200, { 'Content-Type': p.endsWith('.js') ? 'text/javascript' : p.endsWith('.html') ? 'text/html' : 'application/octet-stream' }); res.end(d); }); }).listen(0);
const browser = await chromium.launch({ executablePath: CHROME, args: ['--use-gl=angle', '--use-angle=gl-egl', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 90, height: 160 } });
page.on('pageerror', e => console.log('[err]', e.message));
await page.goto(`http://127.0.0.1:${srv.address().port}/${pg}?w=90&h=160&ao=0`);
await page.waitForFunction('window.READY === true', null, { timeout: 180000 });
const out = await page.evaluate(step => { const res = []; for (let t = 0; t < window.TOTAL; t += step) { window.wristLog(); const r = window.rigReport(Math.round(t * 30)); res.push([+t.toFixed(2), r.beat, window.wristLog()]); } return res; }, +stepS);
const byBeat = {};
for (const [t, b, L] of out) for (const S of Object.keys(L)) for (const k of ['cost']) { const key = `b${b} ${S} ${k}`; if (!byBeat[key] || L[S][k] > byBeat[key][0]) byBeat[key] = [Math.round(L[S][k]), t]; }
for (const [k, v] of Object.entries(byBeat)) if (v[0] > 0) console.log(k.padEnd(14), String(v[0]).padStart(4), 'deg at', v[1]);
await browser.close(); srv.close();
