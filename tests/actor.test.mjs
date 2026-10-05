// actor.js: does each principle actually show up in the numbers?
import { test } from 'node:test'
import assert from 'node:assert/strict'
import '../studio/motion/actor.js'
const Actor = globalThis.Actor
const rig = { x: { v: 0 }, eye: { v: 0, lag: -0.1 }, arm: { v: 0, lag: 0.12 }, y: { v: 0 } }

test('anticipation goes the wrong way first, then arrives', () => {
  const act = Actor.perform(rig, [{ t: 1, pose: { x: 100 }, dur: 0.5, antic: 1, settle: 0 }])
  assert.ok(act(1.1).x < -5, 'pulls back before going')
  assert.ok(Math.abs(act(3).x - 100) < 0.5, 'ends on the pose')
})
test('settle overshoots the pose and comes back; settle 0 does not', () => {
  const springy = Actor.perform(rig, [{ t: 0, pose: { x: 100 }, dur: 0.5, settle: 0.8 }])
  const soft = Actor.perform(rig, [{ t: 0, pose: { x: 100 }, dur: 0.5, settle: 0 }])
  let hi = 0, hi2 = 0
  for (let t = 0; t < 3; t += 0.005) { hi = Math.max(hi, springy(t).x); hi2 = Math.max(hi2, soft(t).x) }
  assert.ok(hi > 103, 'overshoot ' + hi); assert.ok(hi2 <= 100.01, 'no overshoot ' + hi2)
  assert.ok(Math.abs(springy(4).x - 100) < 0.2)
})
test('overlap: the eye leads, the arm trails', () => {
  const act = Actor.perform(rig, [{ t: 1, pose: { x: 100, eye: 100, arm: 100 }, dur: 0.5 }])
  const p = act(1.05)
  assert.ok(p.eye > p.x && p.x > p.arm, JSON.stringify(p))
  assert.equal(act(0.95).x, 0); assert.ok(act(0.95).eye > 0, 'eye already moving')
})
test('plain mode: no pull-back, no overshoot, all together', () => {
  const act = Actor.perform(rig, [{ t: 1, pose: { x: 100, eye: 100, arm: 100 }, dur: 0.5, antic: 1, settle: 0.8 }], { plain: true })
  for (let t = 0; t < 3; t += 0.01) { const p = act(t); assert.ok(p.x >= -1e-9 && p.x <= 100 + 1e-9); assert.ok(Math.abs(p.x - p.eye) < 1e-9 && Math.abs(p.x - p.arm) < 1e-9) }
})
test('no jumps: the value never teleports between frames', () => {
  const act = Actor.perform(rig, [{ t: 0.5, pose: { x: 100 }, dur: 0.4, antic: 1 }, { t: 0.7, pose: { x: -50 }, dur: 0.3, settle: 0.9 }, { t: 1.4, pose: { x: 30 } }])
  let prev = act(0).x, worst = 0
  for (let t = 0; t < 4; t += 1 / 240) { const v = act(t).x; worst = Math.max(worst, Math.abs(v - prev)); prev = v }
  assert.ok(worst < 12, 'largest step in 1/240 s: ' + worst)
})
test('a hop travels straight in x and on an arc in y, and lands on the pose', () => {
  const act = Actor.perform(rig, [{ t: 1, pose: { x: 200, y: 0 }, dur: 0.6, hop: { x: 'x', y: 'y', lift: 150 } }])
  assert.ok(Math.abs(act(1.3).x - 100) < 1e-6); assert.ok(Math.abs(act(1.3).y + 150) < 1e-6); assert.equal(act(1.3).air, 1)
  assert.ok(Math.abs(act(1.7).y) < 1e-6); assert.equal(act(1.7).air, 0)
})
test('squash keeps volume', () => {
  const act = Actor.perform(rig, [{ t: 1, pose: { x: 400, y: 0 }, dur: 0.5, hop: { x: 'x', y: 'y', lift: 200 } }])
  const s = Actor.squash(act, 1.1); assert.ok(s.sy > 1.05); assert.ok(Math.abs(s.sx * s.sy - 1) < 1e-9)
})
