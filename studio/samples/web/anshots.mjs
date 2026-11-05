// node anshots.mjs page.html out_prefix 'expr1' 'expr2' ...  -> one page load, each expr (JS, may return a dataURL) run in turn; a returned dataURL is saved as out_prefix_<n>.png
import http from 'http'; import fs from 'fs'; import path from 'path';
import { chromium } from 'playwright-core';
import { CHROME } from './browser.mjs';
process.env.GALLIUM_DRIVER = 'llvmpipe';
const [,, pg, prefix, ...exprs] = process.argv;
const root = import.meta.dirname;
const srv = http.createServer((req, res) => { const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); res.end(); return; } res.writeHead(200, { 'Content-Type': p.endsWith('.js') ? 'text/javascript' : p.endsWith('.html') ? 'text/html' : p.endsWith('.json') ? 'application/json' : 'application/octet-stream' }); res.end(d); }); }).listen(0);
const browser = await chromium.launch({ executablePath: CHROME, args: ['--use-gl=angle', '--use-angle=gl-egl', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 540, height: 960 } });
page.on('pageerror', e => console.log('[err]', e.message)); page.on('console', m => { const t = m.text(); if (!/GPU stall|not a property/.test(t)) console.log('[page]', t); });
await page.goto(`http://127.0.0.1:${srv.address().port}/${pg}?w=540&h=960`);
await page.waitForFunction('window.READY === true', null, { timeout: 180000 });
let n = 0; for (const e of exprs) { const r = await page.evaluate(e); if (typeof r === 'string' && r.startsWith('data:image')) fs.writeFileSync(`${prefix}_${n++}.png`, Buffer.from(r.split(',')[1], 'base64')); else console.log(JSON.stringify(r)); }
await browser.close(); srv.close();
