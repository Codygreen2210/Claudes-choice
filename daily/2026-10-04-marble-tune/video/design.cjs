// design: build a layout line by line so one marble's bounces land on a 16th-note grid.
// Each new line is put under the marble's path at a chosen moment, then checked by running the real physics.
// node video/design.cjs  -> writes video/layout.json
require('../sim.js'); const Sim = globalThis.Sim
const fs = require('fs')
const H = 1778, R = Sim.R
function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296 } }
const lenFor = idx => Sim.LMIN + (1 - idx / (Sim.SCALE.length - 1)) * (Sim.LMAX - Sim.LMIN)

function run(lines, dropX, until = 8) {
  const hits = [], path = []
  const s = Sim.create({ lines, dropX, H, interval: 100, onHit: e => hits.push({ t: e.t, index: e.index, midi: e.midi, vel: e.vel, x: e.x, y: e.y }) })
  while (s.time < until && (s.marbles.length || s.step === 0)) {
    Sim.tick(s)
    const m = s.marbles[0]; if (m) path.push({ t: s.time, x: m.x, y: m.y, vx: m.vx, vy: m.vy })
  }
  return { hits, path }
}
const same = (a, b, n) => { for (let i = 0; i < n; i++) if (!b[i] || a[i].index !== b[i].index || Math.abs(a[i].t - b[i].t) > 1e-6) return false; return true }

// add one line with note index idx; returns the new line or null
function addLine(lines, dropX, idx, rand, opt = {}) {
  const base = run(lines, dropX)
  const lastT = base.hits.length ? base.hits[base.hits.length - 1].t : 0
  const lastY = base.hits.length ? base.hits[base.hits.length - 1].y : 0
  const L = lenFor(idx)
  for (let tries = 0; tries < 400; tries++) {
    const gaps = base.hits.length ? [0.375, 0.5, 0.5, 0.625, 0.625, 0.75] : [0.5, 0.625]
    const T = Math.round((lastT + gaps[Math.floor(rand() * gaps.length)]) * 8) / 8
    const p = base.path.find(q => q.t >= T - 1e-9)
    if (!p || p.vy < 250) continue
    if (p.y < Math.max(opt.yMin || 260, lastY + 25) || p.y > (opt.yMax || 1380) || p.x < 120 || p.x > 880) continue
    // tilt so the marble is sent back toward the middle (or wherever opt.aim says)
    const aim = opt.aim != null ? opt.aim : 500
    const dir = p.x < aim ? 1 : -1
    const tilt = dir * (10 + rand() * 24) * Math.PI / 180
    const n = { x: Math.sin(tilt), y: -Math.cos(tilt) }, d = { x: Math.cos(tilt), y: Math.sin(tilt) }
    const cx = p.x - n.x * R, cy = p.y - n.y * R
    const off = (rand() - 0.5) * 0.5 * L
    const line = { x1: cx + d.x * (off - L / 2), y1: cy + d.y * (off - L / 2), x2: cx + d.x * (off + L / 2), y2: cy + d.y * (off + L / 2) }
    if (Math.min(line.x1, line.x2) < 60 || Math.max(line.x1, line.x2) > 940) continue
    // keep clear of other lines so they read as separate bars
    if (lines.some(o => Math.hypot((o.x1 + o.x2) / 2 - cx, (o.y1 + o.y2) / 2 - cy) < 150)) continue
    const next = run(lines.concat([line]), dropX)
    const k = base.hits.length
    if (next.hits.length <= k || !same(base.hits, next.hits, k)) continue
    const h = next.hits[k]
    if (h.index !== lines.length || Math.abs(h.t - T) > 0.012) continue
    if (next.hits.slice(k + 1).some(x => x.t - h.t < 0.2)) continue     // no stutter bounces
    line.x1 = Math.round(line.x1); line.y1 = Math.round(line.y1); line.x2 = Math.round(line.x2); line.y2 = Math.round(line.y2)
    const chk = run(lines.concat([line]), dropX)
    if (chk.hits.length <= k || !same(base.hits, chk.hits, k) || chk.hits[k].index !== lines.length || Math.abs(chk.hits[k].t - T) > 0.015) continue
    if (chk.hits.length !== k + 1) continue                              // one clean bounce per line
    return line
  }
  return null
}

const ST = { extraA: 0, okA: 0, b0: 0, bAdd: 0, bExtra: 0 }
function build(seed) {
  const rand = rng(seed), dropX = 320
  // A: E4 G4 A4 C5, then a long low G3, a short high G5, then E5
  const A = [7, 8, 9, 10, 3, 13, 12]
  let lines = []
  for (const idx of A) { const l = addLine(lines, dropX, idx, rand); if (!l) return null; lines.push(l) }
  const a = run(lines, dropX)
  if (a.hits.length !== A.length) { ST.extraA++; return null }
  ST.okA++
  // B: tip line 4 (index 3) the other way; lines 5 to 7 of A go, three new ones catch the new path
  for (let v = 0; v < 60; v++) {
    const o = lines[3], cx = (o.x1 + o.x2) / 2, cy = (o.y1 + o.y2) / 2, L = Sim.len(o) / 2
    const ang0 = Math.atan2(o.y2 - o.y1, o.x2 - o.x1), ang = -ang0 * (0.6 + rand() * 0.9)
    const t4 = { x1: Math.round(cx - Math.cos(ang) * L), y1: Math.round(cy - Math.sin(ang) * L), x2: Math.round(cx + Math.cos(ang) * L), y2: Math.round(cy + Math.sin(ang) * L) }
    if (Sim.midi(t4) !== Sim.midi(o)) continue
    let bl = lines.slice(0, 3).concat([t4])
    const b0 = run(bl, dropX)
    if (b0.hits.length !== 4 || !same(a.hits, b0.hits, 3)) { ST.b0++; continue }
    let ok = true
    for (const idx of [11, 9, 12]) { const l = addLine(bl, dropX, idx, rand, { yMin: 300 }); if (!l) { ok = false; break } bl.push(l) }
    if (!ok) { ST.bAdd++; continue }
    const b = run(bl, dropX)
    if (b.hits.length !== 7) { ST.bExtra++; continue }
    return { dropX, H, A: lines, B: bl, hitsA: a.hits, hitsB: b.hits }
  }
  return null
}

for (let seed = 1; seed < 4000; seed++) {
  if (seed % 500 === 0) console.log(seed, JSON.stringify(ST))
  const r = build(seed)
  if (!r) continue
  r.seed = seed
  const show = hs => hs.map(h => `${h.t.toFixed(3)} ${Sim.noteName(h.midi)}`).join('  ')
  console.log('seed', seed); console.log('A', show(r.hitsA)); console.log('B', show(r.hitsB))
  const ys = r.A.concat(r.B).flatMap(l => [l.y1, l.y2]); console.log('y range', Math.min(...ys), Math.max(...ys))
  fs.writeFileSync(__dirname + '/layout.json', JSON.stringify(r, null, 1))
  break
}
