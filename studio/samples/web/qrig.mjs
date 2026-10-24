// node qrig.mjs out.json : per-frame joint angles for the quicksand Short (rig speed/limit check)
import http from 'http'; import fs from 'fs'; import path from 'path';
import { chromium } from 'playwright-core';
process.env.GALLIUM_DRIVER = process.env.GALLIUM_DRIVER || 'llvmpipe';
const root = import.meta.dirname;
const srv = http.createServer((req, res) => { const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); res.end(); return; } res.writeHead(200, { 'Content-Type': p.endsWith('.js') ? 'text/javascript' : p.endsWith('.html') ? 'text/html' : 'application/json' }); res.end(d); }); }).listen(0);
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell', args: ['--use-gl=angle', '--use-angle=gl-egl', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 64, height: 114 } });
page.on('pageerror', e => console.log('[err]', e.message));
await page.goto(`http://127.0.0.1:${srv.address().port}/quick.html?w=64&h=114`);
await page.waitForFunction('window.READY === true', null, { timeout: 180000 });
const rows = await page.evaluate(() => Array.from({ length: window.FRAMES }, (_, i) => window.rigReport(i)));
fs.writeFileSync(process.argv[2], JSON.stringify(rows)); await browser.close(); srv.close();
