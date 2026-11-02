// node jointjerk.mjs page.html  -> for any 3D Short: steps every frame's pose in order (no drawing) and reports, per beat,
// the fastest joint (deg/frame) and the loop seam (last frame vs frame 0). Rig rule: <= 25 deg/frame inside a beat;
// over ~12 reads as a pop. Joints come from window.rigReport(i).ang (Euler triples, or [flex, abd, rot, elbow, roll] arms).
// A beat boundary is a cut, so the first frame of each beat is skipped; hips are reported relative to the car/rig base
// when rigReport gives `car` (a number = base height).
// Thumbs: if rigReport gives `thumbs` ([R, L] index-minus-little-knuckle vectors in his own frame, facing -z), any frame where
// the thumb side of a hand points backward (> 2.5 cm) without pointing up is a turned-around hand ("thumb on the wrong side").
// Only judged while that forearm hangs down (if rigReport gives `forearms`): with the elbow bent up past ~120 deg (a hammer curl,
// a phone at the ear) the thumb really does point back.
// Hold costs (rigReport cost [R, L]): > 30 means the hand misses what it holds. Clipping (rigReport clip): every body point or
// prop found inside a solid (car, pump, ground) is listed - any hit fails the check. Run this before anyone sees a frame.
// Contacts (rigReport contacts, from contact.js): his hand SKIN against props. CLIP = skin inside a prop; FLOATING = a hand that should
// touch doesn't; LOOSE = a hold that nothing grips from the opposite side. Any of those fails the check. The detector is proven on
// every run (window.contactSelfTest: each listed prop pushed 2 cm into its hand must be caught).
// Faster: --from A --to B --json out.json checks frames A..B-1 only and saves the rows; --merge a.json b.json ... judges saved rows.
// rigpar.sh runs slices on every core and merges (2 cores here: about half the time); the farm runs slices on its runners.
import http from 'http'; import fs from 'fs'; import path from 'path';
import { chromium } from 'playwright-core';
import { CHROME } from './browser.mjs';
process.env.GALLIUM_DRIVER = 'llvmpipe';
const argv = process.argv.slice(2), opt = k => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : null; };
const MERGE = argv.includes('--merge') ? argv.slice(argv.indexOf('--merge') + 1).filter(x => !x.startsWith('--')) : null;
const pg = MERGE ? null : argv[0], FROM = opt('--from'), TO = opt('--to'), JSONOUT = opt('--json');
let rows, NF, SELF;
if (MERGE) { const parts = MERGE.map(f => JSON.parse(fs.readFileSync(f, 'utf8'))); NF = parts[0].N; const seen = new Map();
  for (const p of parts) for (const r of p.rows) seen.set(r.i, r); rows = [...seen.values()].sort((x, y) => x.i - y.i); SELF = parts.map(p => p.self).find(x => x) || null;
  if (rows.length !== NF) console.log(`WARNING: merged ${rows.length} of ${NF} frames`); }
else {
const root = import.meta.dirname;
const srv = http.createServer((req, res) => { const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); res.end(); return; } res.writeHead(200, { 'Content-Type': p.endsWith('.js') ? 'text/javascript' : p.endsWith('.html') ? 'text/html' : 'application/octet-stream' }); res.end(d); }); }).listen(0);
const browser = await chromium.launch({ executablePath: CHROME, args: ['--use-gl=angle', '--use-angle=gl-egl', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 90, height: 160 } });
page.on('pageerror', e => console.log('[err]', e.message));
await page.goto(`http://127.0.0.1:${srv.address().port}/${pg}?w=90&h=160&ao=0`);
await page.waitForFunction('window.READY === true', null, { timeout: 180000 });
const res = await page.evaluate(([f0, f1]) => { const out = []; const N = window.FRAMES, a = f0 == null ? 0 : Math.max(0, +f0), b = f1 == null ? N : Math.min(N, +f1);
  for (let i = a; i < b; i++) { const r = window.rigReport(i);
    out.push({ i, b: r.beat, ang: r.ang, hip: r.hips, car: typeof r.car === 'number' ? r.car : 0, show: r.show !== false, th: r.thumbs || null, fa: r.forearms || null, cost: r.cost || null, clip: r.clip || null, ct: r.contacts || null, cut: !!r.cut }); }
  let self = null; if (window.contactSelfTest) { for (let i = a; i < b && !self; i++) { window.rigReport(i); const st = window.contactSelfTest(); if (st.length) self = st; } }
  return { rows: out, N, self }; }, [FROM, TO]);
await browser.close(); srv.close();
rows = res.rows; NF = res.N; SELF = res.self;
if (JSONOUT) { fs.writeFileSync(JSONOUT, JSON.stringify(res)); console.log(`saved frames ${rows[0]?.i}..${rows[rows.length - 1]?.i} to ${JSONOUT}`); process.exit(0); } }
const diff = (a, b) => { let m = 0, k = ''; for (const n of Object.keys(b)) { if (!Array.isArray(b[n]) || !Array.isArray(a[n])) continue; const d = Math.max(...b[n].map((v, j) => Math.abs(v - a[n][j]))); if (d > m) { m = d; k = n; } } return [m, k]; };
const worst = {};
for (let i = 1; i < rows.length; i++) { const a = rows[i - 1], b = rows[i]; if (b.i !== a.i + 1 || a.b !== b.b || !b.show || b.cut) continue;   // a beat change or an in-beat hard cut (rigReport cut) is a new shot
  const [m, k] = diff(a.ang, b.ang); const hipMove = Math.hypot(b.hip[0] - a.hip[0], (b.hip[1] - b.car) - (a.hip[1] - a.car), b.hip[2] - a.hip[2]);
  const w = worst[b.b] || (worst[b.b] = { m: 0, k: '', t: 0, hip: 0, th: 0 });
  if (m > w.m) Object.assign(w, { m, k, t: (b.i / 30).toFixed(2) });
  if (hipMove > w.hip) Object.assign(w, { hip: hipMove, th: (b.i / 30).toFixed(2) }); }
let bad = 0;
for (const [b, w] of Object.entries(worst)) { const flag = w.m > 25 ? '  POP' : w.m > 12 ? '  fast' : ''; if (w.m > 25) bad++;
  console.log(`beat ${b}: fastest joint ${w.k.padEnd(8)} ${w.m.toFixed(1).padStart(5)} deg/frame at ${w.t}s | hips ${(w.hip * 100).toFixed(1)} cm/frame at ${w.th}s${flag}`); }
const a = rows[rows.length - 1], z = rows[0];
const [sm, sk] = diff(a.ang, z.ang);
console.log(`loop seam: ${sm.toFixed(1)} deg (${sk}), hips ${(Math.hypot(a.hip[0] - z.hip[0], (a.hip[1] - a.car) - (z.hip[1] - z.car), a.hip[2] - z.hip[2]) * 100).toFixed(1)} cm (one frame of motion is normal)`);
let thumbBad = 0;
for (let i = 0; i < rows.length; i++) { const r = rows[i]; if (!r.th || !r.show) continue;
  r.th.forEach((v, j) => { const back = v[2], up = v[1]; if (r.fa && r.fa[j][1] > -0.5) return; if (back > 0.025 && up < 0.01) { if (thumbBad < 6) console.log(`THUMB: ${j ? 'left' : 'right'} hand turned around at ${(r.i / 30).toFixed(2)}s (beat ${r.b})`); thumbBad++; } }); }
if (rows[0].th) console.log(thumbBad ? `${thumbBad} frame-hands with the thumb on the wrong side` : 'thumbs: all on the right side');
// hold costs: how far each solved hand is from where it should be (> 30 = the hand misses its target)
let missBad = 0; const cw = {};
rows.forEach((r, i) => { if (!r.cost || !r.show) return; r.cost.forEach((c, j) => { if (c == null) return; const k = `beat ${r.b} ${j ? 'left' : 'right'}`; if (!cw[k] || c > cw[k][0]) cw[k] = [c, (r.i / 30).toFixed(2)]; }); });
for (const [k, v] of Object.entries(cw)) { if (v[0] > 30) missBad++; console.log(`${k.padEnd(14)} hand hold cost ${v[0].toFixed(1).padStart(7)} at ${v[1]}s${v[0] > 30 ? '  MISSES (fix the scene, not the limits)' : ''}`); }
// clipping: body points / props inside solid things (rigReport(i).clip = [{what, into, depth cm}])
let clipBad = 0; const clw = {};
rows.forEach((r, i) => { if (!r.clip) return; for (const c of r.clip) { const k = `${c.what} into ${c.into}`; clipBad++; if (!clw[k] || c.depth > clw[k].d) clw[k] = { d: c.depth, t: (r.i / 30).toFixed(2), n: (clw[k]?.n || 0) + 1 }; else clw[k].n++; } });
for (const [k, v] of Object.entries(clw)) console.log(`CLIP: ${k}, ${v.n} frames, worst ${v.d} cm at ${v.t}s`);
if (rows[0].clip) console.log(clipBad ? `${clipBad} clip hits` : 'clipping: none');
// contacts: hand skin vs props (contact.js)
let ctBad = 0; const ctw = {};
rows.forEach(r => { if (!r.ct || !r.show) return; for (const c of r.ct) { const k = `${c.S === 'R' ? 'right' : 'left'} hand / ${c.prop} (${c.mode})`, w = ctw[k] || (ctw[k] = { n: 0, bad: {}, worstD: 0, worstT: null, near: [1e9, -1e9] });
  w.n++; w.near = [Math.min(w.near[0], c.near), Math.max(w.near[1], c.near)];
  if (c.verdict !== 'ok') { ctBad++; const b = w.bad[c.verdict] || (w.bad[c.verdict] = { n: 0, t: (r.i / 30).toFixed(2), d: 0 }); b.n++; if (c.depth > b.d) { b.d = c.depth; b.t = (r.i / 30).toFixed(2); } } } });
for (const [k, w] of Object.entries(ctw)) { const bads = Object.entries(w.bad).map(([v, b]) => `${v} ${b.n} frames (worst${v === 'CLIP' ? ' ' + b.d + ' cm' : ''} at ${b.t}s)`).join(', ');
  console.log(`CONTACT ${k}: ${bads || 'ok'} | nearest gap ${w.near[0]}..${w.near[1]} mm`); }
if (rows.some(r => r.ct)) { console.log(ctBad ? `${ctBad} contact faults` : 'contacts: all ok');
  if (SELF) { const miss = SELF.filter(x => !x.caught); console.log(miss.length ? `CONTACT DETECTOR FAILED its self-test (${miss.map(x => x.prop).join(', ')}): fix contact.js before trusting the result` : `contact detector: proven (a 2 cm push into ${SELF.map(x => x.prop).join(', ')} was caught)`); if (miss.length) ctBad++; } }
bad += missBad + (clipBad ? 1 : 0); bad += ctBad ? 1 : 0;
console.log(bad || thumbBad ? `${bad} beat(s) with a pop, ${thumbBad} thumb flags` : 'clean');
