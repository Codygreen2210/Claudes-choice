// node qstills.mjs out_prefix t1,t2,...  [w h]  -> PNG stills of quick.html at those times (seconds)
import http from 'http'; import fs from 'fs'; import path from 'path';
import { chromium } from 'playwright-core';
process.env.GALLIUM_DRIVER = process.env.GALLIUM_DRIVER || 'llvmpipe';
const [,, prefix, ts, wS = '540', hS = '960'] = process.argv;
const root = import.meta.dirname;
const srv = http.createServer((req, res) => { const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); res.end(); return; } res.writeHead(200, { 'Content-Type': p.endsWith('.js') ? 'text/javascript' : p.endsWith('.html') ? 'text/html' : p.endsWith('.json') ? 'application/json' : 'application/octet-stream' }); res.end(d); }); }).listen(0);
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell', args: ['--use-gl=angle', '--use-angle=gl-egl', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: +wS, height: +hS } });
page.on('pageerror', e => console.log('[err]', e.message)); page.on('console', m => { if (!m.text().includes('GPU stall')) console.log('[page]', m.text()); });
await page.goto(`http://127.0.0.1:${srv.address().port}/quick.html?w=${wS}&h=${hS}${process.env.QS || ''}`);
await page.waitForFunction('window.READY === true', null, { timeout: 180000 });
for (const t of ts.split(',')) {
  const d = await page.evaluate(t => window.renderAtT(t), +t);
  fs.writeFileSync(`${prefix}_${t}.png`, Buffer.from(d.split(',')[1], 'base64'));
}
await browser.close(); srv.close();
