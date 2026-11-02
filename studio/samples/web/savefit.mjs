// node savefit.mjs page.html out.json -> load the scene once (its load-time fits run) and save window.FITSAVE, which the scene loads
// next time instead of fitting again (a fit can take half the load; every farm runner and every check loads the scene).
import http from 'http'; import fs from 'fs'; import path from 'path';
import { chromium } from 'playwright-core';
import { CHROME } from './browser.mjs';
process.env.GALLIUM_DRIVER = 'llvmpipe';
const [,, pg, out] = process.argv, root = import.meta.dirname;
if (fs.existsSync(path.join(root, out))) fs.unlinkSync(path.join(root, out));          // fit fresh, never from the old file
const srv = http.createServer((req, res) => { const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); res.end(); return; } res.writeHead(200, { 'Content-Type': p.endsWith('.js') ? 'text/javascript' : p.endsWith('.html') ? 'text/html' : 'application/octet-stream' }); res.end(d); }); }).listen(0);
const b = await chromium.launch({ executablePath: CHROME, args: ['--use-gl=angle', '--use-angle=gl-egl', '--ignore-gpu-blocklist'] });
const page = await b.newPage({ viewport: { width: 90, height: 160 } }); page.on('pageerror', e => console.log('[err]', e.message));
await page.goto(`http://127.0.0.1:${srv.address().port}/${pg}?w=90&h=160`); await page.waitForFunction('window.READY === true', null, { timeout: 900000 });
const fit = await page.evaluate(() => window.FITSAVE || null); await b.close(); srv.close();
if (!fit) { console.log('the scene has no window.FITSAVE'); process.exit(1); }
fs.writeFileSync(path.join(root, out), JSON.stringify(fit, null, 1)); console.log('saved', out);
