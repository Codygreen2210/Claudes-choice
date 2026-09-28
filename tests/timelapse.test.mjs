// Tests for studio/timelapse/timelapse.js: the recording must be honest about time, and the replay must be exact.
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { createRequire } from 'node:module'
const require = createRequire(import.meta.url)
const TL = require('../studio/timelapse/timelapse.js')
const D = require('../studio/works/dragon/dragon.js')

test('points are timed in order, and every stroke starts after the last one ends', () => {
  const r = TL.recorder()
  r.step('a').pencil([[0, 0], [300, 0], [300, 300]]).ink([[0, 0], [100, 100]]).erase('guide', 1)
  let prev = -1
  for (const s of r.strokes) {
    assert.ok(s.t0 >= prev, 'stroke overlaps the one before')
    for (let i = 1; i < s.pts.length; i++) assert.ok(s.pts[i][3] > s.pts[i - 1][3], 'time went backwards inside a stroke')
    prev = s.t1
  }
  assert.equal(r.duration, r.strokes.at(-1).t1)
})

test('the pen slows into a corner', () => {
  const [p] = [TL._timePath([[0, 0], [400, 0], [400, 400]], 600, 0, 4)]
  const v = i => Math.hypot(p[i + 1][0] - p[i][0], p[i + 1][1] - p[i][1]) / (p[i + 1][3] - p[i][3])
  const corner = p.findIndex(q => q[0] >= 399.9)
  const straight = Math.floor(corner / 2)
  assert.ok(v(corner - 1) < v(straight) * 0.8, `corner ${v(corner - 1).toFixed(0)} vs straight ${v(straight).toFixed(0)}`)
})

test('pressure tapers at both ends of a stroke', () => {
  const p = TL._timePath([[0, 0], [500, 0]], 600, 0)
  assert.ok(p[0][2] < 0.4 && p.at(-1)[2] < 0.4 && p[Math.floor(p.length / 2)][2] === 1)
})

test('a fill covers its whole region, not just the middle', () => {
  const region = [[0, 0], [200, 0], [200, 120], [0, 120]]
  const path = TL._scribble(region, 30, 0)
  const ys = path.map(p => p[1]), xs = path.map(p => p[0])
  assert.ok(Math.min(...ys) <= 30 * 0.5 && Math.max(...ys) >= 120 - 30 * 0.5, 'fill misses the top or bottom edge')
  assert.ok(Math.min(...xs) <= 0 && Math.max(...xs) >= 200, 'fill misses a side')
})

test('the timeline holds on each step, never runs backwards, and maps drawing time back to video time', () => {
  const rec = D.build(TL), tl = TL.timeline(rec, { speed: 3, holdStep: 1, intro: 2, outro: 2 })
  let prev = 0
  for (let v = 0; v <= tl.duration; v += 0.05) { const d = tl.draw(v); assert.ok(d >= prev - 1e-9); prev = d }
  assert.equal(tl.draw(tl.duration), rec.duration)
  for (const s of rec.steps) {
    const v = tl.videoTimeOf(s.t)
    assert.ok(Math.abs(tl.draw(v) - s.t) < 1e-6)
    assert.ok(Math.abs(tl.draw(v + 0.5) - s.t) < 1e-6, 'no hold on the step caption')
  }
})

test('a recording survives JSON and replays the same', () => {
  const rec = D.build(TL), back = TL.load(JSON.parse(JSON.stringify(rec.toJSON())))
  assert.equal(back.duration, rec.duration)
  assert.deepEqual(back.strokes.map(s => s.t1), rec.strokes.map(s => s.t1))
})

test('the dragon lesson is complete: every step draws something, and guides are erased before colour', () => {
  const rec = D.build(TL)
  for (const s of rec.steps) assert.ok(rec.strokes.some(st => st.step === s.i), `empty step: ${s.title}`)
  const erase = rec.strokes.find(s => s.tool === 'erase' && s.layer === 'guide')
  const firstColour = rec.strokes.find(s => s.tool === 'fill')
  assert.ok(erase && erase.t1 <= firstColour.t0)
})

test('hatching lines stay inside their region, including a concave one', () => {
  const U = [[0, 0], [300, 0], [300, 200], [200, 200], [200, 60], [100, 60], [100, 200], [0, 200]]   // a U shape
  const inside = (p, poly) => { let c = false; for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) { const a = poly[i], b = poly[j]; if ((a[1] > p[1]) !== (b[1] > p[1]) && p[0] < (b[0] - a[0]) * (p[1] - a[1]) / (b[1] - a[1]) + a[0]) c = !c } return c }
  const lines = TL._lanes(U, 10, 0)
  assert.ok(lines.length > 10)
  for (const [a, b] of lines) { const mid = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]; assert.ok(inside(mid, U), `hatch line crosses the gap at ${mid}`) }
})

test('per-step pacing: a slow step and a fast step, each with its own hold', () => {
  const r = TL.recorder({ lift: 0 })
  r.step('slow').pencil([[0, 0], [900, 0]]).step('fast').pencil([[0, 0], [900, 0]])
  const tl = TL.timeline(r, { speed: (s, i) => (i === 0 ? 1 : 10), holdStep: (s, i) => (i === 0 ? 2 : 0.5), intro: 0, outro: 0 })
  const d0 = r.steps[1].t, d1 = r.duration - d0
  assert.ok(Math.abs(tl.duration - (2 + d0 / 1 + 0.5 + d1 / 10)) < 1e-6)
})

test('the serpent lesson: every step draws something, the tail really passes behind the body, and captions fit', () => {
  const S = require('../studio/works/serpent-dragon/serpent.js')
  const rec = S.build(TL)
  for (const s of rec.steps) assert.ok(rec.strokes.some(st => st.step === s.i), `empty step: ${s.title}`)
  assert.ok(rec.strokes.some(st => st.mask && st.mask.length > 3), 'nothing is masked, so nothing sits behind anything')
  for (const s of rec.steps) assert.ok(s.note.length <= 190, `caption too long for three lines: ${s.title}`)
  const tl = TL.timeline(rec, S.timing(rec))
  rec.steps.forEach((s, i) => {                                  // enough time on screen to read each caption
    const end = rec.steps[i + 1] ? tl.videoTimeOf(rec.steps[i + 1].t) : tl.duration - tl.outro
    assert.ok(end - tl.videoTimeOf(s.t) >= 1.6 + (s.title.length + s.note.length) / 15 - 1e-6, `too fast to read: ${s.title}`)
  })
})

test('the serpent never freezes on a caption for more than 2.5 seconds', () => {
  const S = require('../studio/works/serpent-dragon/serpent.js')
  const rec = S.build(TL), T = S.timing(rec)
  rec.steps.forEach((s, i) => assert.ok(T.holdStep(s, i) <= 2.5, `holds ${T.holdStep(s, i).toFixed(1)} s on: ${s.title}`))
})
