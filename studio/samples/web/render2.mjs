// Fast render: the page renders every frame itself and POSTs raw RGBA straight to us; we stream it to stdout.
//   node render2.mjs "scene.html?level=3" frames [w] [h] | python3 ../finish.py ...
import http from 'http'; import fs from 'fs'; import path from 'path';
import { chromium } from 'playwright-core';
const GLARGS = process.env.GL === 'swiftshader' ? ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] : ['--use-gl=angle', '--use-angle=gl-egl', '--ignore-gpu-blocklist'];
process.env.GALLIUM_DRIVER = process.env.GALLIUM_DRIVER || 'llvmpipe';
const [,, pageArg, framesS, wS = '1080', hS = '1920'] = process.argv;
const W = +wS, H = +hS, FR = +framesS;
const root = import.meta.dirname;
const types = { '.html': 'text/html', '.js': 'text/javascript' };
let got = 0; const t0 = Date.now();
const srv = http.createServer((req, res) => {
  if (req.method === 'POST' && req.url.startsWith('/frame')) {
    const parts = [];
    req.on('data', c => parts.push(c));
    req.on('end', () => {
      const buf = Buffer.concat(parts);
      const ok = process.stdout.write(buf);
      const done = () => { res.writeHead(200); res.end(); got++; if (got % 15 === 0) process.stderr.write(`frame ${got}/${FR} ${((Date.now() - t0) / 1000 / got).toFixed(2)} s/frame\n`); };
      if (ok) done(); else process.stdout.once('drain', done);
    });
    return;
  }
  const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); res.end(); return; } res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' }); res.end(d); });
}).listen(0);
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell', args: GLARGS });
const page = await browser.newPage({ viewport: { width: W, height: H } });
page.on('pageerror', e => process.stderr.write('[err] ' + e.message + '\n'));
const [pf, pq] = pageArg.split('?');
await page.goto(`http://127.0.0.1:${srv.address().port}/${pf}?w=${W}&h=${H}&${pq || ''}`);
await page.waitForFunction('window.READY === true', null, { timeout: 180000 });
await page.evaluate(([a, b]) => window.renderAll(a, b), [0, FR]);
await browser.close(); srv.close();
process.stderr.write(`done ${FR} frames in ${((Date.now() - t0) / 1000).toFixed(1)} s\n`);
