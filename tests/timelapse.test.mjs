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
