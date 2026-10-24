// node stills.mjs <page.html?query> <prefix> <frame,frame,...> [w] [h]
import http from 'http'; import fs from 'fs'; import path from 'path';
import { chromium } from 'playwright-core';
const GLARGS = process.env.GL === 'swiftshader' ? ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] : ['--use-gl=angle', '--use-angle=gl-egl', '--ignore-gpu-blocklist'];
process.env.GALLIUM_DRIVER = process.env.GALLIUM_DRIVER || 'llvmpipe';
const [,, pg, prefix, list, wS = '540', hS = '960'] = process.argv;
const root = import.meta.dirname;
const types = { '.html': 'text/html', '.js': 'text/javascript', '.bin': 'application/octet-stream' };
const srv = http.createServer((req, res) => { const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); res.end(); return; } res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' }); res.end(d); }); }).listen(0);
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell', args: GLARGS });
const page = await browser.newPage({ viewport: { width: +wS, height: +hS } });
page.on('console', m => { if (!m.text().includes('GPU stall')) console.log('[page]', m.text()); });
page.on('pageerror', e => console.log('[err]', e.message));
const [file, q] = pg.split('?');
await page.goto(`http://127.0.0.1:${srv.address().port}/${file}?w=${wS}&h=${hS}&${q || ''}`);
await page.waitForFunction('window.READY === true', null, { timeout: 180000 });
for (const f of list.split(',')) {
  const t0 = Date.now();
  const d = await page.evaluate(i => window.renderPNG(i), +f);
  fs.writeFileSync(`${prefix}_${f}.png`, Buffer.from(d.split(',')[1], 'base64'));
  console.log('frame', f, (Date.now() - t0) / 1000, 's');
}
await browser.close(); srv.close();
