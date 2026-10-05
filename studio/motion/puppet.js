// puppet.js: Lump, the studio's clay character, drawn from numbers so actor.js can perform it.
// Load after kit.js and clay.js. Lump.RIG is the rig to hand to Actor.perform; Lump.draw(p, extras) draws one pose.
//
// The numbers (all optional in a pose; RIG has the resting values):
//   x, y        where the feet stand            lean      tilt of the whole body, radians (+ = toward its left, screen right)
//   crouch      0 standing .. 1 squashed down   lookX/Y   where the eyes point, -1..1
//   wide        eyes: 0 normal .. 1 startled    brow      -1 worried .. 0 .. 1 raised
//   mouth       0 shut .. 1 open                smile     -1 frown .. 1 smile
//   armL, armR  arm angle in radians: 0 hangs down, 1.5 straight out, 3 straight up
// Lags (overlapping action): eyes lead by 0.12 s, brows by 0.06; the body is the beat; arms trail by 0.09 and 0.13
// (not the same number, so they never move as twins).
(function () {
  const RIG = {
    x: { v: 0 }, y: { v: 0 }, lean: { v: 0, alive: 0.012 }, crouch: { v: 0, alive: 0.012 },
    lookX: { v: 0, lag: -0.12 }, lookY: { v: 0, lag: -0.12 }, wide: { v: 0, lag: -0.08 }, brow: { v: 0, lag: -0.06 },
    mouth: { v: 0, lag: 0.02 }, smile: { v: 0.3, lag: 0.03 },
    armL: { v: 0.25, lag: 0.09, alive: 0.03 }, armR: { v: 0.25, lag: 0.13, alive: 0.03 },
  }
  const BODY = [16, 66, 56], HAND = [18, 62, 62], FOOT = [14, 56, 40], WHITE = [45, 30, 94]
  // p: the pose. o: { scale, sq: {sx, sy, angle} from Actor.squash, lid: 0..1 from Actor.blink, air: off the ground }
  function draw(p, o = {}) {
    const sc = o.scale || 1, sq = o.sq || { sx: 1, sy: 1, angle: 0 }, lid = o.lid || 0
    const cr = clamp(p.crouch, -0.4, 1.2), sy = (1 - 0.34 * cr) * sq.sy, sx = (1 / (1 - 0.34 * cr)) ** 0.6 * sq.sx
    g.save(); g.translate(p.x, p.y); g.scale(sc, sc)
    if (!o.noShadow) { const h = clamp(-(o.height || 0) / 260); g.fillStyle = `rgba(52,30,10,${0.24 - 0.12 * h})`; g.beginPath(); g.ellipse(0, 6 + (o.height || 0) * -1 / sc * 0 , 118 * (1 - 0.3 * h), 18 * (1 - 0.3 * h), 0, 0, 6.283); g.fill() }
    // feet stay under the body; in the air they tuck and trail
    for (const s of [-1, 1]) clay(blob(s * 46, o.air ? -18 : -8, 34, 17, 40 + s, 0.05, 10), FOOT, { seed: 40 + s, shadow: false })
    g.rotate(p.lean)
    const H = 104 * sy, top = -18 - 2 * H                          // body centre sits one half-height above the feet
    g.save(); g.translate(0, -18 - H); g.rotate(sq.angle * 0.3)
    // arms behind the body edge: shoulder, a soft elbow, a mitten
    const arm = (side, ang) => {
      const sh = [side * 96 * sx, -6 * sy], a = Math.PI / 2 - side * 0 + 0, dir = [side * Math.sin(ang), Math.cos(ang) * -1 * -1]
      const ex = sh[0] + side * Math.sin(ang) * 96, ey = sh[1] + Math.cos(ang) * 96
      const droop = Math.max(0, Math.cos(ang)) * 10
      const el = [sh[0] + side * Math.sin(ang) * 50 + side * 8, sh[1] + Math.cos(ang) * 50 + droop * 0.5]
      clay(capsule(sh, el, 30, 25), BODY, { seed: 50 + side, shadow: false }); clay(capsule(el, [ex, ey], 25, 21), BODY, { seed: 52 + side, shadow: false })
      clay(blob(ex + side * Math.sin(ang) * 10, ey + Math.cos(ang) * 10, 21, 19, 54 + side, 0.05, 10), HAND, { seed: 54 + side, shadow: false })
      return [ex + side * Math.sin(ang) * 10, ey + Math.cos(ang) * 10]
    }
    const hl = arm(-1, p.armL), hr = arm(1, p.armR)
    const body = blob(0, 0, 122 * sx, H, 7, 0.055, 20)
    body.forEach(q => { if (q[1] > H * 0.55) q[1] = H * 0.55 + (q[1] - H * 0.55) * 0.7 })
    clay(body, BODY, { seed: 77 })
    // face
    const lx = clamp(p.lookX, -1, 1) * 10, ly = clamp(p.lookY, -1, 1) * 8, wide = clamp(p.wide), ey = -24 * sy
    for (const s of [-1, 1]) {
      const cx = s * 42 * sx
      if (lid > 0.8) { g.strokeStyle = '#4a2413'; g.lineWidth = 7; g.lineCap = 'round'; g.beginPath(); g.moveTo(cx - 20, ey); g.quadraticCurveTo(cx, ey + 10, cx + 20, ey); g.stroke() }
      else {
        const er = 29 + wide * 6
        clay(blob(cx, ey, er, (er + 2) * (1 - lid * 0.5), 20 + s, 0.04, 12), WHITE, { seed: 30 + s, shadow: false })
        g.fillStyle = '#2a1a12'; g.beginPath(); g.arc(cx + lx, ey + 2 + ly, 12.5 - wide * 2.5, 0, 6.283); g.fill()
        g.fillStyle = 'rgba(255,255,255,0.85)'; g.beginPath(); g.arc(cx + lx - 4, ey - 3 + ly, 3.6, 0, 6.283); g.fill()
      }
      // brow: a little clay bar that lifts, or tips inward for worry
      const b = clamp(p.brow, -1, 1), by = ey - 44 - Math.max(0, b) * 16 - wide * 6, tip = b < 0 ? -b * 0.5 * s : -0.08 * s
      g.save(); g.translate(cx, by); g.rotate(tip); clay(capsule([-20, 0], [20, 0], 11, 11), [14, 60, 38], { seed: 60 + s, shadow: false }); g.restore()
    }
    const m = clamp(p.mouth), sm = clamp(p.smile, -1, 1), my = 36 * sy
    g.fillStyle = '#4a1d12'; g.beginPath()
    if (m > 0.08) g.ellipse(0, my + 2, 20 + m * 6, 4 + m * 19, 0, 0, 6.283)
    else { g.moveTo(-24, my - sm * 4); g.quadraticCurveTo(0, my + sm * 20, 24, my - sm * 4); g.quadraticCurveTo(0, my + sm * 10, -24, my - sm * 4) }
    g.fill()
    g.restore(); g.restore()
    return { hands: [hl, hr] }
  }
  window.Lump = { RIG, draw }
})()
