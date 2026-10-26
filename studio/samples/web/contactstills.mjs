// node contactstills.mjs page out_prefix shots.json -> stills with a fixed camera per shot ({name, t, pos, tgt, fov})
import http from 'http'; import fs from 'fs'; import path from 'path';
import { chromium } from 'playwright-core';
import { CHROME } from './browser.mjs';
process.env.GALLIUM_DRIVER = 'llvmpipe';
const [,, pg, prefix, shotsF] = process.argv;
const root = import.meta.dirname;
const srv = http.createServer((req, res) => { const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); res.end(); return; } res.writeHead(200, { 'Content-Type': p.endsWith('.js') ? 'text/javascript' : p.endsWith('.html') ? 'text/html' : 'application/octet-stream' }); res.end(d); }); }).listen(0);
const browser = await chromium.launch({ executablePath: CHROME, args: ['--use-gl=angle', '--use-angle=gl-egl', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 480, height: 480 } });
page.on('pageerror', e => console.log('[err]', e.message));
await page.goto(`http://127.0.0.1:${srv.address().port}/${pg}?w=480&h=480&ao=0`);
await page.waitForFunction('window.READY === true', null, { timeout: 180000 });
if (process.env.CLIPTEST) console.log(JSON.stringify(await page.evaluate(() => [window.clipTest(10, 0.6), window.clipTest(10, -0.6)])).slice(0, 600));
for (const s of JSON.parse(fs.readFileSync(shotsF))) {
  const d = await page.evaluate(s => { window.CAM = s.pos ? s : null; const r = window.renderAtT(s.t); window.CAM = null; return r; }, s);
  fs.writeFileSync(`${prefix}_${s.name}.png`, Buffer.from(d.split(',')[1], 'base64'));
}
await browser.close(); srv.close();
