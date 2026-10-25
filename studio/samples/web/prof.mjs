// time render vs readback vs base64 inside the page
import http from 'http'; import fs from 'fs'; import path from 'path';
import { chromium } from 'playwright-core';
import { CHROME } from './browser.mjs';
const GLARGS = process.env.GL === 'swiftshader' ? ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] : ['--use-gl=angle', '--use-angle=gl-egl', '--ignore-gpu-blocklist'];
process.env.GALLIUM_DRIVER = process.env.GALLIUM_DRIVER || 'llvmpipe';
const [,, q] = process.argv;
const root = import.meta.dirname;
const srv = http.createServer((req, res) => { const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); res.end(); return; } res.writeHead(200, { 'Content-Type': p.endsWith('.js') ? 'text/javascript' : p.endsWith('.html') ? 'text/html' : 'application/octet-stream' }); res.end(d); }); }).listen(0);
const browser = await chromium.launch({ executablePath: CHROME, args: GLARGS });
const [PW, PH] = (process.argv[3] || '1080x1920').split('x').map(Number);
const page = await browser.newPage({ viewport: { width: PW, height: PH } });
page.on('pageerror', e => console.log('[err]', e.message));
await page.goto(`http://127.0.0.1:${srv.address().port}/scene.html?w=${PW}&h=${PH}&${q}`);
await page.waitForFunction('window.READY === true', null, { timeout: 180000 });
await page.evaluate(i => window.renderFrame(i), 5);
await page.evaluate(i => window.renderFrame(i), 60);
await page.evaluate(i => window.renderFrame(i), 120);
const frames = (process.argv[4] || '10,40,70,100,130').split(',').map(Number);
let tot = 0;
for (const f of frames) { const t0 = Date.now(); await page.evaluate(i => window.renderFrame(i), f); tot += Date.now() - t0; }
console.log('avg s/frame', (tot / frames.length / 1000).toFixed(3));
await browser.close(); srv.close();
