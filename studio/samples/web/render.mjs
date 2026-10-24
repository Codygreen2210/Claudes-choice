// Render a three.js page frame by frame in headless Chromium and pipe raw RGBA frames to ffmpeg.
//   node render.mjs <page.html> <out.mp4> <frames> [w] [h] [fps] [first]
import http from 'http';
import fs from 'fs';
import path from 'path';
import { spawn } from 'child_process';
import { chromium } from 'playwright-core';

const [,, pageFile, out, framesS, wS = '1080', hS = '1920', fpsS = '30', firstS = '0'] = process.argv;
const W = +wS, H = +hS, FR = +framesS, FPS = +fpsS, FIRST = +firstS;
const root = path.dirname(path.resolve(import.meta.dirname, 'x'));
const types = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.png': 'image/png', '.json': 'application/json', '.bin': 'application/octet-stream' };
const srv = http.createServer((req, res) => {
  const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); res.end(); return; } res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' }); res.end(d); });
}).listen(0);
const port = srv.address().port;

const browser = await chromium.launch({
  executablePath: process.env.CHROME || '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell',
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--disable-gpu-sandbox'],
});
const page = await browser.newPage({ viewport: { width: W, height: H } });
page.on('console', m => console.log('[page]', m.text()));
page.on('pageerror', e => console.log('[err]', e.message));
const [pf, pq] = pageFile.split('?');
await page.goto(`http://127.0.0.1:${port}/${path.relative(root, path.resolve(pf))}?w=${W}&h=${H}&${pq || ''}`);
await page.waitForFunction('window.READY === true', null, { timeout: 120000 });

const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${W}x${H}`, '-r', `${FPS}`, '-i', '-',
  '-vf', 'vflip', '-c:v', 'libx264', '-crf', '16', '-preset', 'medium', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
const t0 = Date.now();
for (let i = FIRST; i < FR; i++) {
  const b64 = await page.evaluate(i => window.renderFrame(i), i);
  const buf = Buffer.from(b64, 'base64');
  if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  if (i % 10 === 0) console.log(`frame ${i}/${FR}  ${((Date.now() - t0) / 1000 / (i - FIRST + 1)).toFixed(2)} s/frame`);
}
ff.stdin.end();
await new Promise(r => ff.on('close', r));
await browser.close(); srv.close();
console.log('done', out);
