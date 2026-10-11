// scB.js: scenes 6-10 of The Battle of New Orleans.
(function () {
  const { clamp, lerp, EZ, prog, bump, rng, noise, track, mix } = K
  const { W, H, C, F, paper, finish, hatch, rr, text, typeset, rule, person, glow, tw, clock } = L
  const { RED, INK, GY, view, stubble, fog, smoke, flash, soldier, front, wallFront, cannon, wall, cypress, horse, rider, ship, ladder, bundle, house } = B
  const { flame, fade, fogCol, lineF, MEN, GAPS, plan } = NO
  const fire = flame
  const R = rng(77), RV = Array.from({ length: 400 }, () => R())

  // the British seen from behind, going up the field. rows: [{u: 0 near .. 1 at the ditch}], fall(row, i) -> 0..1
  function redRows(c, t, us, o = {}) {
    us.slice().sort((a, b) => b - a).forEach((u, ri) => {
      const r = us.indexOf(u), y = lerp(1340, 915, clamp(u)), h = (y - 775) * 0.6, dx = h * 0.58, n = Math.ceil(2700 / dx)
      for (let i = 0; i < n; i++) {
        const x = -380 + i * dx + ((r % 2) * dx) / 2, k = (r * 53 + i * 17) % 400, dn = o.fall ? o.fall(r, i, RV[k]) : 0
        if (o.thin && RV[(k + 9) % 400] < o.thin(r)) continue
        front(c, x, y, h, { kind: o.kind || 'brit', col: o.col || RED, gun: 'slope', walk: t * 5.2 + RV[k] * 0.6 + r, stride: dn > 0 ? 0 : (o.stride ?? 1), down: dn, side: RV[k] < 0.5 ? -1 : 1 })
      }
    })
  }

  // =============================== 6. the assault ===============================
  function s6(c, t, q, S) {
    const qDr = q('drums going'), qFog = q('and then the fog') - 0.3, qOpen = q('they were in the open'), qEv = q('in front of every'), qCan = q('the cannon opened') - 0.35, qRif = q('then the rifles') - 0.25, qMus = q('then the muskets') - 0.3, qStep = q('one stepping up'), qStop = q('it did not stop') - 0.4, qDit = q('the men who reached') - 0.4, qNo = q('there were no ladders'), qSt = q('so they stood'), qDie = q('and they died')
    if (t < qMus + 0.3 || (t >= qStop + 0.3 && t < qDit + 0.3)) {
      const late = t >= qStop, d = lerp(0.36, 0.8, prog(t, qFog, qFog + 2.5))
      const lift = prog(t, qFog + 0.5, qFog + 2.6, 'io'), adv = (t - S.vis) * 0.012
      const shake = (bump(t, qCan + 0.35, 0.5) + bump(t, qCan + 1.0, 0.5) + bump(t, qCan + 1.7, 0.5)) * 7
      const cy = track(t, [[S.vis, 1000], [qFog, 985, 'l'], [qEv, 940, 'io'], [qCan, 940], [qCan + 1.2, 915, 'io']]) + Math.sin(t * 47) * shake * 0.5
      const s = track(t, [[S.vis, 1.0], [qEv, 1.0], [qCan + 1.2, 1.12, 'io']])
      const gun = (k) => late ? bump(t, qStop + 0.5 + k * 0.8 + Math.floor((t - qStop) / 2.6) * 2.6, 0.22) : bump(t, qCan + 0.35 + k * 0.65, 0.24) + bump(t, qRif + 1.2 + k * 0.5, 0.24)
      const mfire = (m, i) => { if (t < qRif && !late) return 0; const per = 1.9 + m.f * 1.6, t0 = late ? qStop : qRif + 0.15; return bump(t, t0 + m.f * per + Math.floor((t - t0) / per) * per, 0.13) }
      const us = [0.0, 0.26, 0.5, 0.72].map(u => Math.min(0.9, u + adv + (late ? 0.06 : 0)))
      const fallAt = (r, i, v) => { const t0 = late ? qStop - 2.5 + v * 7 : qCan + 0.5 + v * 14 - us[r] * 5; return (v < (late ? 0.62 : 0.4)) ? prog(t, t0, t0 + 0.5, 'i') : 0 }
      view(c, { cx: 960 + Math.sin(t * 53) * shake, cy, s, d }, () => {
        stubble(c, -400, 2400, d, 9)
        lineF(c, t, { water: mix('#39414d', '#b9b39c', d), fire: mfire, gun, men: late ? 1 : prog(t, qFog + 0.6, qEv + 0.5) * 1.05 })
        const sa = late ? 0.75 : prog(t, qCan + 0.4, qRif + 2) * 0.75
        if (sa > 0) for (let i = 0; i < 16; i++) smoke(c, -200 + i * 160 + Math.sin(t * 0.3 + i) * 40, 800 - 20 * Math.sin(t * 0.5 + i * 2), 110, sa * (0.5 + 0.5 * noise(t * 0.4, i)), i + 3)
      })
      // fog over the wall, lifting
      fog(c, t, (1 - lift) * 0.95, { col: fogCol(d), y0: 250, y1: 620, n: 34, seed: 5 })
      view2(c, { cx: 960 + Math.sin(t * 53) * shake, cy, s }, () => redRows(c, t, us, { fall: (t > qCan || late) ? fallAt : null, stride: 1 }))
      fog(c, t, (1 - lift) * 0.5 + 0.08, { col: fogCol(d), y0: 420, y1: 1000, n: 22, seed: 12 })
      fade(c, late ? 1 - prog(t, qStop + 0.3, qStop + 0.6) : 0); finish(c, t, d < 0.5); return d < 0.5
    }
    if (t < qStop + 0.3) {
      // rank after rank: one man fires, steps down, the next steps up
      const d = 0.8, T = 2.4
      view(c, { cx: 640 + 20 * prog(t, qMus, qStop, 'l'), cy: 640, s: 1.7, d }, () => {
        stubble(c, 900, 2400, d)
        for (let k = 0; k < 4; k++) soldier(c, 250 - k * 64, GY + 4, 180 + (k % 2) * 8, { kind: ['mil', 'reg', 'city', 'sailor'][k], pose: 'load', col: INK })
        for (let k = 0; k < 3; k++) {
          const u = (((t - qMus) / T + k / 3) % 1 + 1) % 1, kind = ['mil', 'reg', 'pirate'][k]
          let x, y, pose = 'load', face = 1, st = 0, kick = 0
          if (u < 0.3) { x = 632; y = GY - 45; pose = 'aim'; const f = bump(u, 0.12, 0.07); kick = -f * 0.15; if (f > 0) { flash(c, 632 + 128, GY - 45 - 138, 1.0, f); } }
          else if (u < 0.5) { const p = (u - 0.3) / 0.2; x = lerp(632, 400, p); y = GY - 45 + 49 * clamp(p * 2.2); face = -1; st = 1 }
          else if (u < 0.8) { x = 400; y = GY + 4 }
          else { const p = (u - 0.8) / 0.2; x = lerp(400, 632, p); y = GY + 4 - 49 * clamp(p * 2.2 - 1.2); st = 1; pose = 'march' }
          soldier(c, x, y, 190, { kind, pose, face, col: INK, walk: x * 0.07, stride: st, kick })
        }
        wall(c, 760, GY, 118, { col: INK, water: '#b9b39c' })
        for (let k = 0; k < 5; k++) { const a = (((t - qMus) / T * 3 + k / 5) % 1); smoke(c, 800 + a * 500, GY - 190 - a * 90, 40 + a * 90, 0.6 * (1 - a), k + 1) }
      })
      fade(c, 1 - prog(t, qMus + 0.3, qMus + 0.55) + prog(t, qStop - 0.05, qStop + 0.3)); finish(c, t, false); return false
    }
    // the ditch
    const d = 0.74, die = [0.2, 1.3, 0.7, 1.9, 2.5, 1.0]
    view(c, { cx: 900 + 30 * prog(t, qDit, S.out, 'l'), cy: lerp(640, 620, prog(t, qDit, S.out)), s: 1.55 + 0.1 * prog(t, qDit, S.out, 'l'), d }, () => {
      stubble(c, 950, 2600, d)
      const f1 = bump(t, qDie + 0.25, 0.14) + bump(t, qDie + 1.35, 0.14), f2 = bump(t, qDie + 0.75, 0.14) + bump(t, qDie + 1.95, 0.14)
      soldier(c, 560, GY + 4, 186, { kind: 'reg', pose: 'load', col: INK }); soldier(c, 470, GY + 4, 180, { kind: 'city', pose: 'load', col: INK })
      soldier(c, 640, GY - 45, 190, { kind: 'mil', pose: 'aim', col: INK, kick: 0.3 - f1 * 0.1 }); flash(c, 640 + 118, GY - 45 - 102, 0.9, f1)
      wall(c, 760, GY, 118, { col: INK, water: '#b9b39c' })
      const look = prog(t, qDit + 1.6, qDit + 2.4) * (1 - prog(t, qNo + 1.2, qNo + 1.8))
      if (look > 0) { c.save(); c.globalAlpha = look * (0.6 + 0.3 * Math.sin(t * 5)); c.setLineDash([12, 10]); ladder(c, 880, GY + 56, 250, -2.05, C.gold, 5); c.restore() }
      ;[[850, GY + 58], [912, GY + 58], [985, GY + 4], [1050, GY + 4], [1120, GY + 4], [1200, GY + 4]].forEach(([x, y], i) => {
        const dn = prog(t, qDie + die[i], qDie + die[i] + 0.5, 'i')
        soldier(c, x, y, 188, { kind: 'brit', face: -1, pose: 'stand', lean: 0.1 * look * (i < 3 ? 1 : 0.4), down: dn })
      })
      smoke(c, 860, GY - 170, 90, 0.4 * (f1 + f2) + 0.25 * prog(t, qDie, qDie + 2), 4)
    })
    fade(c, 1 - prog(t, qDit + 0.3, qDit + 0.6) + 0.55 * prog(t, qDie + 2.2, S.out)); finish(c, t, false); return false
  }
  // a second camera pass with no sky (for layers that go over fog)
  function view2(c, o, draw) { const s = o.s || 1; c.save(); c.translate(W / 2, H / 2); c.scale(s, s); c.translate(-o.cx, -(o.cy ?? 560)); draw(); c.restore() }

  // =============================== 7. the generals, the Highlanders ===============================
  const FIELD = Array.from({ length: 26 }, (_, i) => ({ x: 700 + RV[i] * 2600, y: GY + 6 + RV[i + 40] * 150, h: 170 + RV[i + 80] * 30, v: RV[i + 120] }))
  function s7(c, t, q, S) {
    const qHit = q('he was hit'), qHit2 = q('then hit again'), qLive = q('he did not live'), qSec = q('his second in command') - 0.4, qDown = q('went down'), qThird = q('then his third'), qHigh = q('one regiment of highlanders') - 0.4, qHalt = q('halted in the open'), qStood = q('so they stood') - 0.2, qNob = q('because nobody'), qAll = q('all across the field') - 0.4, qAlive = q('just to stay')
    const d = 0.8
    if (t < qSec + 0.3) {
      const hx = track(t, [[S.vis, 2900], [qHit, 1700, 'l'], [qHit2, 1420, 'o'], [qHit2 + 2.4, 300, 'i'], [qHit2 + 5, -1600, 'l']])
      const fallen = t > qHit2 + 0.15, jerk = bump(t, qHit, 0.5), fp = prog(t, qHit2 + 0.15, qHit2 + 0.8, 'i')
      const cx = fallen ? lerp(hx + 0, 1400, 1) : hx - 60
      view(c, { cx: track(t, [[S.vis, 2800], [qHit, 1640, 'l'], [qHit2, 1400, 'o'], [S.out, 1370, 'l']]), cy: track(t, [[qHit2, 590], [qLive + 1.5, 650, 'io']]), s: track(t, [[qHit2, 1.2], [qLive + 1.8, 1.6, 'io']]), d }, () => {
        stubble(c, -300, 4000, d)
        FIELD.forEach((m, i) => { if (m.y < GY + 60) soldier(c, m.x, m.y, m.h, { kind: 'brit', face: -1, pose: 'stand', down: i % 3 ? 1 : 0 }) })
        if (fallen) soldier(c, 1440, GY + 40 + 0, 250, { kind: 'officer', col: RED, face: -1, pose: 'none', down: fp })
        horse(c, hx, GY + 40, 2.9, { col: INK, face: -1, gait: hx * 0.022, stride: 1, gallop: fallen ? 1 : 0.8 * (1 - prog(t, qHit, qHit2)), rear: jerk * 0.25, head: -jerk * 0.3, rider: fallen ? null : rider('officer', RED, { lean: -0.2 + jerk * 0.5 + prog(t, qHit2 - 0.1, qHit2 + 0.15) * 0.7, arm: 1.0 * (1 - prog(t, qHit - 0.1, qHit + 0.1)) }) })
        FIELD.forEach((m, i) => { if (m.y >= GY + 60) soldier(c, m.x, m.y, m.h, { kind: 'brit', face: -1, pose: 'stand', down: i % 3 ? 1 : 0 }) })
        for (let i = 0; i < 9; i++) smoke(c, 300 + i * 420 + Math.sin(t * 0.3 + i) * 60, GY - 150 - 40 * Math.sin(i * 1.7), 150, 0.2, i + 20)
      })
      const hf = bump(t, qHit - 0.05, 0.25) + bump(t, qHit2 - 0.05, 0.25); if (hf > 0) fade(c, hf * 0.25, '255,236,190')
      finish(c, t, false); return false
    }
    if (t < qHigh + 0.3) {
      const off = [[1010, qDown], [1400, qThird + 0.55]]
      view(c, { cx: 1200 + 30 * prog(t, qSec, qHigh, 'l'), cy: 600, s: 1.25, d }, () => {
        stubble(c, -300, 3000, d)
        for (let i = 0; i < 12; i++) { const x = 520 + i * 118 + RV[i] * 30; if (Math.abs(x - 1010) < 60 || Math.abs(x - 1400) < 60) continue; soldier(c, x, GY + 4 + RV[i + 20] * 20, 182, { kind: 'brit', face: -1, pose: i % 4 === 1 ? 'aim' : 'stand', down: i % 5 === 3 ? 1 : 0 }) }
        off.forEach(([x, at], k) => { const dn = prog(t, at, at + 0.55, 'i'); soldier(c, x, GY + 24, 236, { kind: 'officer', col: RED, face: -1, pose: 'up', down: dn }); const f = bump(t, at - 0.1, 0.25); if (f > 0) glow(c, x - 40, GY - 150, 260, '246,199,112', 0.5 * f) })
        for (let i = 0; i < 7; i++) smoke(c, 300 + i * 330 + Math.sin(t * 0.4 + i) * 50, GY - 160, 140, 0.4, i + 40)
      })
      fade(c, 1 - prog(t, qSec + 0.3, qSec + 0.6)); finish(c, t, false); return false
    }
    if (t < qAll + 0.3) {
      const arr = prog(t, qHigh, qHalt + 0.4, 'o')
      view(c, { cx: 1250, cy: lerp(610, 590, prog(t, qHigh, qAll)), s: lerp(1.05, 1.22, prog(t, qHalt, qAll, 'io')), d }, () => {
        stubble(c, -300, 3200, d)
        const fl = bump(t, qStood + 0.5 + Math.floor((t - qStood) / 0.9) * 0.9, 0.2) * (t > qStood ? 1 : 0)
        if (fl > 0) glow(c, 250, GY - 140, 700, '246,199,112', 0.35 * fl)
        for (let r = 0; r < 3; r++) for (let i = 0; i < 9; i++) {
          const k = r * 9 + i, x = 900 + i * 92 + r * 34 + (1 - arr) * 1300, v = RV[k + 200]
          const dn = v < 0.5 ? prog(t, qStood + 0.6 + v * 12, qStood + 1.1 + v * 12, 'i') : 0
          soldier(c, x, GY + r * 16, 196 + r * 5, { kind: 'high', face: -1, pose: arr < 1 ? 'march' : 'stand', walk: x * 0.07, stride: arr < 1 ? 1 : 0, down: dn })
        }
        for (let i = 0; i < 8; i++) { const a = ((t * 0.07 + i / 8) % 1); smoke(c, -200 + a * 2800, GY - 130 - 50 * Math.sin(i * 2.1), 150, 0.24 * prog(t, qHalt, qStood) * Math.sin(a * Math.PI), i + 60) }
      })
      fade(c, 1 - prog(t, qHigh + 0.3, qHigh + 0.6)); finish(c, t, false); return false
    }
    view(c, { cx: 1900 + 80 * prog(t, qAll, S.out, 'l'), cy: 640, s: 0.95, d: 0.84 }, () => {
      stubble(c, -300, 4400, 0.84)
      FIELD.slice().sort((a, b) => a.y - b.y).forEach((m, i) => { const lie = m.v < 0.45; soldier(c, m.x, m.y + 40, m.h * 1.1, { kind: 'brit', face: m.v < 0.7 ? -1 : 1, pose: lie ? 'none' : 'stand', gun: false, down: lie ? prog(t, qAll + 0.4 + m.v * 9, qAll + 1.6 + m.v * 9, 'io') : 1 }) })
      for (let i = 0; i < 10; i++) { const a = ((t * 0.05 + i / 10) % 1); smoke(c, 400 + a * 3200, GY - 120 - 40 * Math.sin(i * 2.1), 170, 0.4 * Math.sin(a * Math.PI), i + 80) }
    })
    fade(c, 1 - prog(t, qAll + 0.3, qAll + 0.6)); finish(c, t, false); return false
  }

  // =============================== 8. the count ===============================
  function s8(c, t, q, S) {
    const qHalf = q('about half an hour'), qBrit = q('the british lost') - 0.35, qKil = q('killed wounded'), qAm = q('the americans lost') - 0.3, q71 = q('71'), q13 = q('13 of them'), qKy = q('a kentucky soldier') - 0.4, qCov = q('entirely covered'), qThen = q('and then some'), qUp = q('stood up'), qLiv = q('living men'), qWalk = q('and now walked')
    if (t < qBrit + 0.3) {
      paper(c, t)
      const sw = prog(t, qHalf - 0.3, qHalf + 1.6, 'io') * 0.5
      clock(c, W / 2, 520, 260, 6 + sw, {})
      c.save(); c.translate(W / 2, 520); c.fillStyle = C.red2; c.globalAlpha = 0.5; c.beginPath(); c.moveTo(0, 0); c.arc(0, 0, 258, -Math.PI / 2, -Math.PI / 2 + sw * Math.PI * 2); c.closePath(); c.fill(); c.restore()
      typeset(c, 'about half an hour', W / 2, 900, F.headI(80, 700), C.ink, prog(t, qHalf - 0.2, qHalf + 0.9))
      finish(c, t, false); return false
    }
    if (t < qKy + 0.3) {
      paper(c, t)
      const n = Math.floor(2037 * prog(t, qBrit + 0.3, qKil + 0.6, 'o')), x0 = 110, y0 = 400, cell = 12
      text(c, 'BRITISH', x0, 250, F.sc(44), C.red, { align: 'left', track: 8, alpha: prog(t, qBrit, qBrit + 0.4) })
      text(c, n.toLocaleString('en-US'), x0, 360, F.head(110, 900), C.red, { align: 'left', alpha: prog(t, qBrit, qBrit + 0.4) })
      typeset(c, 'killed, wounded, or captured', x0 + 420, 356, F.bodyI(46), C.ink2, prog(t, qKil - 0.2, qKil + 1.2), { align: 'left' })
      c.fillStyle = C.red2; for (let i = 0; i < n; i++) c.fillRect(x0 + (i % 97) * cell, y0 + Math.floor(i / 97) * cell * 1.5, 8, 13)
      const ax = 1450, m = Math.floor(71 * prog(t, q71 - 0.2, q71 + 0.5)), dead = prog(t, q13 - 0.2, q13 + 0.4)
      text(c, 'AMERICAN', ax, 250, F.sc(44), C.ink, { align: 'left', track: 8, alpha: prog(t, qAm, qAm + 0.4) })
      text(c, String(m), ax, 360, F.head(110, 900), C.ink, { align: 'left', alpha: prog(t, q71 - 0.2, q71 + 0.1) })
      for (let i = 0; i < m; i++) { const x = ax + (i % 24) * cell, y = y0 + Math.floor(i / 24) * cell * 1.5; if (i < 13 || dead <= 0) { c.fillStyle = C.ink; c.fillRect(x, y, 8, 13) } else { c.fillStyle = mix(C.ink, C.paper3, dead * 0.85); c.fillRect(x, y, 8, 13) } }
      if (dead > 0) { c.save(); c.globalAlpha = dead; c.strokeStyle = C.ink; c.lineWidth = 3; c.beginPath(); c.moveTo(ax - 4, y0 + 26); c.lineTo(ax + 13 * cell + 2, y0 + 26); c.stroke(); c.restore(); text(c, '13 dead', ax, y0 + 150, F.headI(70, 700), C.ink, { align: 'left', alpha: dead }) }
      rule(c, 110, 1810, 830, C.ink, prog(t, qBrit + 0.2, qBrit + 1.2))
      text(c, 'January 8, 1815', W / 2, 900, F.bodyI(44), C.ink2, { alpha: prog(t, qBrit + 0.6, qBrit + 1.2) })
      finish(c, t, false); return false
    }
    const d = 0.86, UPS = FIELD.map((m, i) => m.v > 0.55)
    view(c, { cx: 1560 + 60 * prog(t, qKy, S.out, 'l'), cy: 650, s: 0.9, d }, () => {
      stubble(c, 900, 4400, d)
      soldier(c, 560, GY + 4, 186, { kind: 'reg', pose: 'stand', col: INK }); soldier(c, 460, GY + 4, 180, { kind: 'city', pose: 'stand', col: INK }); soldier(c, 370, GY + 4, 184, { kind: 'sailor', pose: 'stand', col: INK })
      soldier(c, 640, GY - 45, 190, { kind: 'mil', pose: 'stand', col: INK, lean: 0.1 * prog(t, qKy, qKy + 1) })
      wall(c, 760, GY, 118, { col: INK, water: '#b9b39c' })
      FIELD.slice().sort((a, b) => a.y - b.y).forEach((m, i) => {
        const up = m.v > 0.55, t0 = qUp - 0.3 + (m.v - 0.55) * 5, r = up ? prog(t, t0, t0 + 1.3, 'io') : 0
        const x = m.x + 250 - (up ? Math.max(0, t - t0 - 1.4) * 70 : 0)
        soldier(c, Math.max(x, 1010 + m.v * 300), m.y + 30, m.h * 1.05, { kind: 'brit', face: -1, pose: r >= 1 ? 'up' : 'none', gun: false, down: 1 - r, walk: x * 0.06, stride: r >= 1 && x > 1010 + m.v * 300 ? 1 : 0 })
      })
      for (let i = 0; i < 10; i++) { const a = ((t * 0.04 + i / 10) % 1); smoke(c, 700 + a * 3200, GY - 150 - 60 * Math.sin(i * 2.1), 190, 0.45 * (1 - prog(t, qCov, qLiv)) * Math.sin(a * Math.PI), i + 90) }
    })
    finish(c, t, false); return false
  }

  // =============================== 9. the treaty ===============================
  function treaty(c, x, y, s, o = {}) {
    c.save(); c.translate(x, y); c.rotate(o.rot ?? -0.02); c.scale(s, s)
    c.fillStyle = 'rgba(0,0,0,0.4)'; c.fillRect(-248, -328, 520, 680)
    c.fillStyle = C.paper; c.fillRect(-260, -340, 520, 680); c.strokeStyle = C.ink; c.lineWidth = 3; c.strokeRect(-238, -318, 476, 636)
    text(c, 'TREATY', 0, -240, F.sc(64), C.ink, { track: 10 }); text(c, 'of Peace and Amity', 0, -188, F.bodyI(38), C.ink)
    rule(c, -150, 150, -160, C.ink, 1)
    const r = rng(12); c.strokeStyle = C.ink2; c.lineWidth = 3
    for (let i = 0; i < 11; i++) { const yy = -116 + i * 27; c.beginPath(); c.moveTo(-200, yy); c.lineTo(-200 + 400 * (i === 10 ? 0.5 : 0.9 + r() * 0.1), yy); c.stroke() }
    const sg = clamp(o.sign ?? 1)
    c.strokeStyle = C.ink; c.lineWidth = 3; c.lineCap = 'round'
    for (const [sx, sd] of [[-190, 5], [-30, 9]]) { const q2 = rng(sd); c.beginPath(); c.moveTo(sx, 236); for (let k = 1; k <= Math.floor(14 * sg); k++) c.lineTo(sx + k * 10, 236 + (q2() - 0.5) * 30); c.stroke() }
    const sl = clamp(o.seal ?? 1); if (sl > 0) { const z = 1 + (1 - sl) * 1.5; c.globalAlpha = sl; c.fillStyle = C.red; c.beginPath(); for (let k = 0; k <= 24; k++) { const a = k / 24 * 6.283, rr2 = 44 * z * (1 + 0.07 * Math.sin(a * 7)); c.lineTo(170 + Math.cos(a) * rr2, 232 + Math.sin(a) * rr2) } c.fill(); c.strokeStyle = 'rgba(0,0,0,0.3)'; c.lineWidth = 3; c.beginPath(); c.arc(170, 232, 28 * z, 0, 7); c.stroke() }
    c.restore()
  }
  function room(c, t) {
    c.fillStyle = '#15110d'; c.fillRect(0, 0, W, H); c.fillStyle = '#0c0907'; c.fillRect(0, 880, W, 200)
    glow(c, 300, 560, 900, '246,170,90', 0.3 * (0.9 + 0.1 * noise(t * 5, 2)))
    c.fillStyle = C.paper2; c.fillRect(278, 640, 44, 240); c.fillStyle = '#2a2018'; c.fillRect(240, 872, 120, 14)
    fire(c, 300, 642, 1.0, t, 0.8)
  }
  function s9(c, t, q, S) {
    const q15 = q('15 days earlier') - 0.35, qEve = q('on christmas eve'), qCity = q('in a city'), qSign = q('had signed a peace'), qNews = q('the news was on') - 0.4, qStill = q('still crossing'), qTr = q('the treaty still') - 0.4, qBut = q('but its terms'), qWord = q('changed a word')
    if (t < q15 + 0.3) {
      const d = 0.86
      view(c, { cx: 1500, cy: 620, s: 0.9 + 0.05 * prog(t, S.vis, q15, 'l'), d }, () => { stubble(c, 900, 4400, d); wall(c, 760, GY, 118, { col: INK, water: '#b9b39c' }); FIELD.forEach(m => soldier(c, m.x + 250, m.y + 30, m.h, { kind: 'brit', face: -1, pose: 'none', gun: false, down: 1 })) })
      fade(c, 0.45 + 0.55 * prog(t, q15 - 0.1, q15 + 0.3)); finish(c, t, true); return true
    }
    if (t < qNews + 0.3 || t >= qTr + 0.3) {
      const second = t >= qTr
      room(c, t)
      const z = second ? 1.06 + 0.05 * prog(t, qTr, S.out, 'l') : 1 + 0.04 * prog(t, q15, qNews, 'l')
      treaty(c, 800, 590, 1.05 * z, { sign: second ? 1 : prog(t, qSign - 0.9, qSign + 0.3), seal: second ? 1 : prog(t, qSign + 0.25, qSign + 0.6, 'i') })
      if (!second) {
        // fifteen days, counted back
        const bx = 240, bw = 90, back = prog(t, q15 + 0.3, qEve + 0.2, 'io')
        for (let i = 0; i < 16; i++) {
          const day = i < 8 ? 24 + i : i - 7, hot = i >= Math.round(15 * (1 - back))
          c.fillStyle = i === 15 ? C.red : (i === 0 && back >= 1 ? C.gold : hot ? 'rgba(238,226,200,0.9)' : 'rgba(238,226,200,0.14)'); c.fillRect(bx + i * bw + 4, 60, bw - 8, 78)
          text(c, String(day), bx + i * bw + bw / 2, 116, F.old(40, true), i === 15 ? C.paper : hot ? C.ink : C.paper3)
        }
        text(c, 'DECEMBER', bx + 4, 176, F.sc(28), C.paper2, { align: 'left', track: 4 }); text(c, 'JANUARY', bx + 16 * bw - 4, 176, F.sc(28), C.paper2, { align: 'right', track: 4 })
        typeset(c, 'Ghent, Belgium', 1500, 480, F.headI(64, 700), C.paper, prog(t, qCity - 0.1, qCity + 0.9), { shadow: '#000' })
        typeset(c, 'December 24, 1814', 1500, 560, F.bodyI(50), C.gold2, prog(t, qEve - 0.1, qEve + 0.9), { shadow: '#000' })
      } else {
        typeset(c, 'approved February 16, 1815', 1500, 500, F.bodyI(50), C.gold2, prog(t, qTr + 0.6, qTr + 1.6), { shadow: '#000' })
        typeset(c, 'not a word changed', 1500, 590, F.headI(60, 700), C.paper, prog(t, qWord - 0.5, qWord + 0.6), { shadow: '#000' })
      }
      fade(c, 1 - prog(t, (second ? qTr : q15) + 0.3, (second ? qTr : q15) + 0.7)); finish(c, t, true); return true
    }
    // the ocean
    paper(c, t)
    hatch(c, k => k.rect(0, 0, W, H), { gap: 14, alpha: 0.22, angle: 0, box: [0, 0, W, H], wob: 3 })
    const am = k => { k.moveTo(-50, 120); k.bezierCurveTo(260, 160, 420, 300, 360, 470); k.bezierCurveTo(330, 560, 420, 640, 330, 700); k.bezierCurveTo(240, 740, 200, 860, 60, 840); k.lineTo(-50, 1100); k.closePath() }
    const eu = k => { k.moveTo(1980, 60); k.bezierCurveTo(1700, 120, 1640, 260, 1560, 330); k.bezierCurveTo(1480, 400, 1560, 480, 1500, 560); k.bezierCurveTo(1440, 660, 1560, 760, 1620, 900); k.lineTo(1980, 1100); k.closePath() }
    for (const land of [am, eu]) { c.fillStyle = C.paper3; c.beginPath(); land(c); c.fill(); c.strokeStyle = C.ink; c.lineWidth = 4; c.beginPath(); land(c); c.stroke() }
    c.fillStyle = C.gold; c.strokeStyle = C.ink; c.lineWidth = 4; c.beginPath(); c.arc(1590, 380, 14, 0, 7); c.fill(); c.stroke(); text(c, 'Ghent', 1630, 370, F.headI(50, 700), C.ink, { align: 'left' })
    c.fillStyle = C.red2; c.beginPath(); c.arc(250, 790, 14, 0, 7); c.fill(); c.stroke(); text(c, 'New Orleans', 40, 720, F.headI(50, 700), C.ink, { align: 'left' })
    const P = p => [lerp(1540, 390, p), lerp(420, 720, p) + Math.sin(p * Math.PI) * 120]
    c.strokeStyle = C.ink; c.lineWidth = 4; c.setLineDash([4, 16]); c.lineCap = 'round'; c.beginPath(); for (let p = 0; p <= 1.001; p += 0.02) { const [x, y] = P(p); p ? c.lineTo(x, y) : c.moveTo(x, y) } c.stroke(); c.setLineDash([])
    const sp = lerp(0.3, 0.42, prog(t, qNews, qTr, 'l')), [sx, sy] = P(sp)
    c.strokeStyle = C.ink; c.lineWidth = 6; c.beginPath(); for (let p = 0; p <= sp; p += 0.02) { const [x, y] = P(p); p ? c.lineTo(x, y) : c.moveTo(x, y) } c.stroke()
    ship(c, sx - 40, sy + 20, 1.15, { face: -1, t, col: C.ink })
    typeset(c, 'the news', sx - 40, sy - 290, F.headI(60, 700), C.ink, prog(t, qNews + 0.3, qNews + 1.0))
    typeset(c, 'still at sea', sx - 40, sy - 235, F.bodyI(44), C.red, prog(t, qStill - 0.1, qStill + 0.8))
    finish(c, t, false); return false
  }

  // =============================== 10. what it changed ===============================
  function sheet(c, x, y, rot, head, sub, hc) {
    c.save(); c.translate(x, y); c.rotate(rot); c.fillStyle = 'rgba(60,40,20,0.25)'; c.fillRect(-282, -332, 580, 700); c.fillStyle = '#f4ead2'; c.fillRect(-290, -340, 580, 700); c.strokeStyle = C.ink; c.lineWidth = 3; c.strokeRect(-290, -340, 580, 700)
    text(c, 'THE GAZETTE', 0, -280, F.sc(34), C.ink, { track: 8 }); rule(c, -250, 250, -262, C.ink, 1)
    text(c, head, 0, -150, F.head(head.length > 6 ? 84 : 130, 900), hc); text(c, sub, 0, -80, F.bodyI(40), C.ink)
    c.strokeStyle = C.ink3; c.lineWidth = 2.5; for (let col = 0; col < 3; col++) for (let i = 0; i < 12; i++) { c.beginPath(); c.moveTo(-250 + col * 172, -20 + i * 28); c.lineTo(-250 + col * 172 + 150 - ((i * 7 + col * 3) % 5 === 0 ? 60 : 0), -20 + i * 28); c.stroke() }
    c.restore()
  }
  const icon = {
    paw: (c) => { c.beginPath(); c.ellipse(0, 22, 40, 34, 0, 0, 7); c.fill(); for (const [x, y, r] of [[-46, -22, 17], [-17, -48, 18], [17, -48, 18], [46, -22, 17]]) { c.beginPath(); c.ellipse(x, y, r * 0.85, r, x * 0.006, 0, 7); c.fill() } },
    swords: (c) => { for (const s of [-1, 1]) { c.save(); c.rotate(s * 0.78); c.fillRect(-6, -84, 12, 126); c.beginPath(); c.moveTo(-6, -84); c.lineTo(0, -102); c.lineTo(6, -84); c.fill(); c.fillRect(-28, 36, 56, 10); c.fillRect(-5, 46, 10, 30); c.beginPath(); c.arc(0, 82, 9, 0, 7); c.fill(); c.restore() } },
    crash: (c) => { c.lineWidth = 11; c.lineJoin = 'round'; c.lineCap = 'round'; c.beginPath(); c.moveTo(-84, 20); c.lineTo(-44, -30); c.lineTo(-14, -8); c.lineTo(16, -64); c.lineTo(44, 44); c.lineTo(84, 70); c.stroke(); c.beginPath(); c.moveTo(84, 70); c.lineTo(52, 72); c.lineTo(76, 44); c.closePath(); c.fill(); c.stroke() },
  }
  const CROWD = L.crowd(22, 1815, { h: 250, ladies: 0.25 })
  function s10(c, t, q, S) {
    const qNoth = q('on paper nothing') - 0.2, qCo = q('but the country') - 0.4, qVic = q('the news of the victory'), qPe = q('and the news of the peace'), qDec = q('and americans decided'), qPat = q('a patchwork army') - 0.4, qMan = q('and the man behind') - 0.4, qWH = q('all the way to'), qLast = q('the last great battle') - 0.4, qAft = q('was fought after'), qMat = q('and it mattered'), qSub = q('subscribe') - 0.35, qAn = q('animal facts'), qBat = q('historys greatest'), qCol = q('worlds craziest')
    if (t < qCo + 0.3) {
      room(c, t); treaty(c, 800, 590, 1.16 + 0.04 * prog(t, S.vis, qCo, 'l'), {})
      typeset(c, 'On paper, nothing.', 1500, 540, F.headI(64, 700), C.paper, prog(t, qNoth, qNoth + 1.0), { shadow: '#000' })
      finish(c, t, true); return true
    }
    if (t < qPat + 0.3) {
      paper(c, t, C.paper2)
      const a = prog(t, qVic - 0.3, qVic + 0.5, 'o'), b = prog(t, qPe - 0.3, qPe + 0.5, 'o')
      if (a > 0) sheet(c, 600, 430 + (1 - a) * 900, -0.05, 'VICTORY', 'at New Orleans', C.red)
      if (b > 0) sheet(c, 1320, 430 + (1 - b) * 900, 0.04, 'PEACE', 'signed at Ghent', C.ink)
      const up = prog(t, qDec, qDec + 0.6, 'o')
      CROWD.forEach((p, i) => { const x = 60 + i * 86 + p.jit * 30, cheer = up * (0.6 + 0.4 * Math.sin(t * 6 + p.ph)); person(c, x, 1120 + (1 - prog(t, qDec - 0.4, qDec + 0.3, 'o')) * 400 - cheer * 14, p.h, { hat: p.hat, lady: p.lady, bulk: p.bulk, col: C.ink, face: i % 2 ? 1 : -1, arm: p.lady ? 0 : 1.05 * up + 0.1 * Math.sin(t * 7 + p.ph) * up }) })
      finish(c, t, false); return false
    }
    if (t < qMan + 0.3) {
      const d = 0.95
      view(c, { cx: 760 + 300 * prog(t, qPat, qMan, 'l'), cy: 840, s: 1.9, d }, () => { glow(c, 1100, 760, 900, '246,199,112', 0.55); stubble(c, -300, 2400, d, 9); lineF(c, t, { water: '#cdbf96' }) })
      c.save(); c.globalCompositeOperation = 'multiply'; c.fillStyle = 'rgba(240,200,104,0.35)'; c.fillRect(0, 0, W, H); c.restore()
      fade(c, 1 - prog(t, qPat + 0.3, qPat + 0.6), '238,226,200'); finish(c, t, false); return false
    }
    if (t < qLast + 0.3) {
      paper(c, t)
      const gy = 800; c.strokeStyle = C.ink; c.lineWidth = 5; c.beginPath(); c.moveTo(0, gy); c.lineTo(W, gy); c.stroke(); hatch(c, k => k.rect(0, gy + 2, W, 280), { gap: 9, alpha: 0.25, angle: 0.03, box: [0, gy, W, 280] })
      const hsx = track(t, [[qMan, 2700], [qWH + 1.2, 1420, 'o']]); house(c, hsx, gy, 1.7, C.ink, C.paper2)
      const hx = track(t, [[qMan, 100], [qLast, 620, 'l']])
      horse(c, hx, gy, 2.2, { col: C.ink, gait: hx * 0.04, stride: 0.9, head: 0.05 * Math.sin(t * 2), rider: rider('officer', C.ink) })
      typeset(c, 'Andrew Jackson, seventh President', W / 2, 190, F.headI(64, 700), C.ink, prog(t, qWH - 0.2, qWH + 1.3))
      text(c, '1829', W / 2, 270, F.head(64, 900), C.red, { alpha: prog(t, qWH + 1.0, qWH + 1.5) })
      finish(c, t, false); return false
    }
    if (t < qSub + 0.3) {
      const d = lerp(0.4, 0.75, prog(t, qLast, qSub))
      view(c, { cx: 960, cy: 860, s: 1.2 + 0.12 * prog(t, qLast, qSub, 'l'), d }, () => { glow(c, 960, 790, 700, '246,199,112', 0.35 * prog(t, qMat, qSub)); stubble(c, -300, 2400, d, 9); lineF(c, t, { water: mix('#39414d', '#b9b39c', d), men: 0 }) })
      fog(c, t, 0.5 - 0.25 * prog(t, qAft, qSub), { col: fogCol(d), y0: 520, y1: 1000 })
      fade(c, 1 - prog(t, qLast + 0.3, qLast + 0.7) + prog(t, qSub - 0.1, qSub + 0.3)); finish(c, t, d < 0.5); return d < 0.5
    }
    c.fillStyle = '#0c0c10'; c.fillRect(0, 0, W, H); glow(c, W / 2, 480, 1000, '150,80,50', 0.14)
    const a = qSub + 0.3, z = 1 + 0.03 * prog(t, a, S.out, 'l')
    c.save(); c.translate(W / 2, H / 2); c.scale(z, z); c.translate(-W / 2, -H / 2)
    c.save(); c.globalAlpha = prog(t, a, a + 0.6); cannon(c, W / 2 - 20, 215, 1.5, { col: C.paper2 }); c.restore()
    rule(c, 520, 1400, 250, C.paper3, prog(t, a, a + 0.8))
    text(c, 'SUBSCRIBE', W / 2, 400, F.head(150, 900), C.paper, { track: 16, alpha: prog(t, a + 0.1, a + 0.6) })
    text(c, 'and we’ll tell you more', W / 2, 470, F.bodyI(50), C.paper2, { alpha: prog(t, a + 0.6, a + 1.2) })
    const items = [['paw', 'Animal facts', qAn], ['swords', 'History’s greatest battles', qBat], ['crash', 'The world’s craziest financial collapses', qCol]]
    items.forEach(([ic, label, at], i) => {
      const p = prog(t, at - 0.1, at + 0.3, 'back'), x = 420 + i * 540; if (p <= 0) return
      c.save(); c.translate(x, 680); c.scale(p, p); c.strokeStyle = C.gold; c.lineWidth = 4; c.beginPath(); c.arc(0, 0, 120, 0, 7); c.stroke()
      c.fillStyle = i === 1 ? C.gold2 : C.paper; c.strokeStyle = i === 2 ? C.red2 : C.paper; if (i === 2) c.fillStyle = C.red2; icon[ic](c); c.restore()
      const ws = label.split(' '), l1 = ws.length > 3 ? ws.slice(0, 3).join(' ') : label, l2 = ws.length > 3 ? ws.slice(3).join(' ') : ''
      text(c, l1, x, 870, F.body(40), C.paper, { alpha: clamp(p) }); if (l2) text(c, l2, x, 918, F.body(40), C.paper, { alpha: clamp(p) })
    })
    c.restore()
    fade(c, 1 - prog(t, a, a + 0.4)); finish(c, t, true); return true
  }

  window.SCENES.push(s6, s7, s8, s9, s10)
})()
