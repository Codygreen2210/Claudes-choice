// node avpose.mjs out.png t [OVR-json] [CAM-json] [w h]  -> debug stills of av.html: OVR = {"b": beat, "p": {joint: [x,y,z]}} overrides the pose, CAM = {"pos","tgt","fov"}; ";" separates several
import http from 'http'; import fs from 'fs'; import path from 'path';
import { chromium } from 'playwright-core';
process.env.GALLIUM_DRIVER = 'llvmpipe';
const [,, out, t, ovr = 'null', cam = 'null', W = '540', H = '960'] = process.argv;
const root = import.meta.dirname;
const srv = http.createServer((req, res) => { const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); res.end(); return; } res.writeHead(200, { 'Content-Type': p.endsWith('.js') ? 'text/javascript' : p.endsWith('.html') ? 'text/html' : 'application/octet-stream' }); res.end(d); }); }).listen(0);
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell', args: ['--use-gl=angle', '--use-angle=gl-egl', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: +W, height: +H } });
page.on('pageerror', e => console.log('[err]', e.message));
await page.goto(`http://127.0.0.1:${srv.address().port}/av.html?w=${W}&h=${H}&ao=0${process.env.QS || ''}`);
await page.waitForFunction('window.READY === true', null, { timeout: 180000 });
const outs = out.split(';'), ts = t.split(';'), ovs = ovr.split(';'), cams = cam.split(';');
for (let i = 0; i < outs.length; i++) {
  const d = await page.evaluate(([t, o, c]) => { window.OVR = JSON.parse(o); window.CAM = JSON.parse(c); return window.renderAtT(+t); }, [ts[i] ?? ts[0], ovs[i] ?? ovs[0], cams[i] ?? cams[0]]);
  fs.writeFileSync(outs[i], Buffer.from(d.split(',')[1], 'base64'));
}
await browser.close(); srv.close();
