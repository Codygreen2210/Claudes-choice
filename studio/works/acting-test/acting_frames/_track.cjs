
const { createRequire } = require('node:module');
const req = createRequire(__filename);
let pw; for (const p of ['playwright', '/home/claude/.npm-global/lib/node_modules/playwright']) { try { pw = req(p); break } catch (e) {} }
const url = require('node:url'); const path = require('node:path'); const fs = require('node:fs');
(async () => {
  const A = JSON.parse(process.argv[2]);
  const b = await pw.chromium.launch({ args: ['--allow-file-access-from-files'] });
  const p = await b.newPage({ viewport: { width: A.w, height: A.h } });
  p.on('pageerror', e => console.error('page error:', e.message));
  await p.goto(url.pathToFileURL(path.resolve(A.page)).href + (A.hash || ''));
  await p.evaluate(async () => { if (window.__init) await window.__init(); if (document.fonts) await document.fonts.ready });
  const frames = [];
  const n = Math.round((A.to - A.from) * A.fps);
  for (let i = 0; i <= n; i++) {
    const t = A.from + i / A.fps;
    await p.evaluate(t => window.__seek(t), t);
    const st = await p.evaluate(t => {
      const out = {};
      if (window.__track) Object.assign(out, window.__track(t));
      for (const el of document.querySelectorAll('[data-track]')) {
        const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
        let rot = 0; const m = cs.transform;
        if (m && m !== 'none') { const v = m.match(/matrix\(([^)]+)\)/); if (v) { const [a, bb] = v[1].split(',').map(Number); rot = Math.atan2(bb, a) * 180 / Math.PI } }
        let o = 1; for (let e = el; e; e = e.parentElement) o *= parseFloat(getComputedStyle(e).opacity || 1);
        out[el.dataset.track] = { x: r.left + r.width / 2, y: r.top + r.height / 2, s: Math.sqrt(Math.max(r.width * r.height, 0)), r: rot, o, vis: cs.visibility !== 'hidden' && cs.display !== 'none', body: el.dataset.body || null };
      }
      return out;
    }, t);
    frames.push({ t, st });
    if (A.strobe && i % A.strobeEvery === 0) await p.screenshot({ path: path.join(A.dir, `s${String(i).padStart(4, '0')}.png`) });
  }
  const accents = await p.evaluate(() => (window.__accents || []));
  fs.writeFileSync(path.join(A.dir, 'track.json'), JSON.stringify({ frames, accents }));
  await b.close();
})().catch(e => { console.error(e); process.exit(1) });
