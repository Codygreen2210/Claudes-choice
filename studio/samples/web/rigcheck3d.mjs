// node rigcheck3d.mjs "scene.html?level=2" out.json  -> per-frame rig data for rigcheck3d.py
import http from 'http'; import fs from 'fs'; import path from 'path';
import { chromium } from 'playwright-core';
import { CHROME } from './browser.mjs';
process.env.GALLIUM_DRIVER = process.env.GALLIUM_DRIVER || 'llvmpipe';
const [,, pg, out, nS = '150'] = process.argv;
const root = import.meta.dirname;
const srv = http.createServer((req, res) => { const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); res.end(); return; } res.writeHead(200, { 'Content-Type': p.endsWith('.js') ? 'text/javascript' : p.endsWith('.html') ? 'text/html' : 'application/octet-stream' }); res.end(d); }); }).listen(0);
const browser = await chromium.launch({ executablePath: CHROME, args: ['--use-gl=angle', '--use-angle=gl-egl', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 64, height: 114 } });
page.on('pageerror', e => console.log('[err]', e.message));
const [file, q] = pg.split('?');
await page.goto(`http://127.0.0.1:${srv.address().port}/${file}?w=64&h=114&${q || ''}`);
await page.waitForFunction('window.READY === true', null, { timeout: 180000 });
const rows = await page.evaluate(n => Array.from({ length: n }, (_, i) => window.rigReport(i)), +nS);
fs.writeFileSync(out, JSON.stringify(rows)); await browser.close(); srv.close();
