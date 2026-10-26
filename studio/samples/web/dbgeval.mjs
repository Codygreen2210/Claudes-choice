// node dbgeval.mjs page.html "js expression"  -> prints JSON of evaluating the expression in the page once READY (debug helper)
import http from 'http'; import fs from 'fs'; import path from 'path';
import { chromium } from 'playwright-core';
import { CHROME } from './browser.mjs';
process.env.GALLIUM_DRIVER = 'llvmpipe';
const [,, pg, expr] = process.argv;
const root = import.meta.dirname;
const srv = http.createServer((req, res) => { const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); res.end(); return; } res.writeHead(200, { 'Content-Type': p.endsWith('.js') ? 'text/javascript' : p.endsWith('.html') ? 'text/html' : 'application/octet-stream' }); res.end(d); }); }).listen(0);
const browser = await chromium.launch({ executablePath: CHROME, args: ['--use-gl=angle', '--use-angle=gl-egl', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 90, height: 160 } });
page.on('pageerror', e => console.log('[err]', e.message));
await page.goto(`http://127.0.0.1:${srv.address().port}/${pg}?w=90&h=160&ao=0`);
await page.waitForFunction('window.READY === true', null, { timeout: 180000 });
console.log(JSON.stringify(await page.evaluate(expr)));
await browser.close(); srv.close();
