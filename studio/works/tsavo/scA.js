// scA.js: scenes 1-3 of The Man-Eaters of Tsavo. Each scene is draw(c, t, q, S) -> true if the picture is dark.
(function () {
  const { clamp, lerp, EZ, prog, bump, rng, noise, track } = K
  const { W, H, C, F, layer, paper, finish, hatch, rr, text, typeset, rule, person, crowd, glow, tw } = L
  const { ghost, N, lion, lionDown, eyes, night, ground, acacia, thorn, tent, fire, train, rails, patterson, turban } = T2
  const cam = (c, cx, cy, s) => { c.translate(W / 2, H / 2); c.scale(s, s); c.translate(-cx, -cy) }
  const fade = (c, a, col = '4,5,9') => { if (a > 0) { c.fillStyle = `rgba(${col},${clamp(a)})`; c.fillRect(0, 0, W, H) } }
  const INK = '#05060a'
  // the moonlit plain: sky, a far ridge, pale ground that silhouettes read against
  function plain(c, t, o = {}) {
    const hy = o.hy ?? 660
    night(c, t, { moon: o.moon })
    c.fillStyle = '#1a2542'; c.beginPath(); c.moveTo(-200, hy + 10); for (let x = -200; x <= W + 400; x += 60) c.lineTo(x, hy - 26 - 34 * noise(x * 0.0016 + (o.seed || 0), 2)); c.lineTo(W + 400, hy + 10); c.closePath(); c.fill()
    const g = c.createLinearGradient(0, hy, 0, H); g.addColorStop(0, o.g0 || '#42537f'); g.addColorStop(1, o.g1 || '#161d34'); c.fillStyle = g; c.fillRect(-400, hy, W + 800, H - hy + 200)
    const r = rng(60 + (o.seed || 0)); for (let i = 0; i < (o.trees ?? 5); i++) acacia(c, -100 + r() * (W + 300), hy + 6, 0.5 + r() * 0.5, '#0d1326', i + (o.seed || 0))
  }
  const WORK = crowd(40, 77, { h: 200, ladies: 0 })

  // =============================== 1. the tent ===============================
  function s1(c, t, q, S) {
    const qM = q('its the middle') - 0.3, qL = q('a lion puts'), qT = q('and takes him'), qA = q('he gets his arms'), qG = q('let go'), qF = q('he was the first') - 0.2, qN = q('he would not')
    if (t < qM + 0.35) {
      const z = 1 + 0.06 * prog(t, 0, qM + 0.4, 'sine')
      c.save(); cam(c, W / 2, H / 2 + 20, z)
      plain(c, t, { moon: [1480, 210, 74], hy: 700, trees: 6 })
      for (const [x, k] of [[620, 1], [700, 0.7], [800, 0.9]]) glow(c, x, 708, 60, N.fire, 0.5 * k * (0.8 + 0.2 * noise(t * 5, x)))
      for (const x of [600, 650, 700, 750, 800]) { c.fillStyle = INK; c.beginPath(); c.moveTo(x - 16, 712); c.lineTo(x, 692); c.lineTo(x + 16, 712); c.closePath(); c.fill() }
      c.restore()
      const a0 = S.start - 0.3
      text(c, 'TSAVO', W / 2, 400, F.head(210, 900), C.paper, { track: 60, alpha: prog(t, a0, a0 + 1.0), shadow: '#000', blur: 40 })
      rule(c, 660, 1260, 440, C.paper3, prog(t, a0 + 0.4, a0 + 1.4))
      typeset(c, 'East Africa · 1898', W / 2, 520, F.bodyI(60), C.paper2, prog(t, a0 + 1.3, a0 + 2.6), { shadow: '#000' })
      fade(c, prog(t, qM - 0.1, qM + 0.35)); finish(c, t, true); return true
    }
    const gy = 830, z = 1.0 + 0.07 * prog(t, qM, qN, 'l')
    c.save(); cam(c, 1000 + 40 * prog(t, qM, qF, 'sine'), 580, z)
    plain(c, t, { moon: [300, 170, 54], hy: 700, trees: 4, seed: 4 })
    thorn(c, -200, 300, gy + 4, 50, INK, 3); thorn(c, 1820, 2300, gy + 4, 56, INK, 5)
    // the camp
    const lit = (1 - prog(t, qT + 0.2, qT + 0.45)) * (0.82 + 0.18 * noise(t * 7, 3))
    const shake = (t > qT && t < qF) ? Math.sin(t * 31) * 0.02 * (1 - prog(t, qG + 0.6, qF)) * prog(t, qT, qT + 0.2) : 0
    tent(c, 380, gy, 1.5, { col: INK }); tent(c, 1640, gy, 1.5, { col: INK })
    // the lion, low, coming in from the right
    const lx = track(t, [[qL - 1.2, 2400], [qT - 0.15, 1250, 'sine'], [qT + 0.12, 1180, 'i'], [qF, 1180, 'l'], [qF + 0.9, 1290, 'io'], [qN + 2.6, 2600, 'i']])
    const leaving = t > qF + 0.5
    if (leaving) { c.save(); c.strokeStyle = 'rgba(5,6,10,0.55)'; c.lineWidth = 9; c.setLineDash([26, 14]); c.beginPath(); c.moveTo(1040, gy + 44); c.lineTo(Math.min(lx - 150, 2300), gy + 44); c.stroke(); c.restore() }
    c.save(); c.translate(1000, gy); c.rotate(shake); c.translate(-1000, -gy); tent(c, 1000, gy, 1.5, { col: INK, lit }); c.restore()
    lion(c, lx, gy + 46, 2.9, { face: leaving ? 1 : -1, walk: lx * 0.035, stride: (t < qT || leaving) ? 1 : 0, crouch: leaving ? 0.25 : 0.75, eye: true, col: INK, head: leaving ? 0.25 : 0 })
    // the second one, watching
    const e2 = prog(t, qN, qN + 0.5) * (Math.sin(t * 0.9) > -0.93 ? 1 : 0.1)
    if (e2 > 0) eyes(c, 250, 770, 2.4, e2)
    c.restore()
    const ca = prog(t, qG - 0.15, qG + 0.2) * (1 - prog(t, qF - 0.3, qF + 0.2))
    if (ca > 0) { text(c, '“Choro!”', W / 2, 250, F.headI(150, 700), C.paper, { alpha: ca, shadow: '#000', blur: 40 }); text(c, 'Let go.', W / 2, 340, F.bodyI(58), C.paper2, { alpha: ca, shadow: '#000' }) }
    // title
    const ta = qN + 1.0, tp = prog(t, ta, ta + 0.7)
    if (tp > 0) {
      fade(c, tp * 0.62)
      rule(c, 420, 1500, 330, C.paper3, prog(t, ta, ta + 0.9))
      text(c, 'THE MAN-EATERS', W / 2, 500, F.head(150, 900), C.paper, { track: 10, alpha: prog(t, ta + 0.1, ta + 0.7) })
      text(c, 'OF TSAVO', W / 2, 670, F.head(150, 900), C.red2, { track: 14, alpha: prog(t, ta + 0.4, ta + 1.0) })
      rule(c, 420, 1500, 740, C.paper3, prog(t, ta + 0.4, ta + 1.3))
    }
    fade(c, 1 - prog(t, qM + 0.35, qM + 0.9)); finish(c, t, true); return true
  }

  // =============================== 2. the railway ===============================
  function bridge(c, t, build, o = {}) {
    // a river gorge with two stone piers; build 0..1 raises the piers, 1..2 lays the girders
    const by = 600
    c.fillStyle = C.paper2; c.strokeStyle = C.ink; c.lineWidth = 5
    for (const [x0, x1] of [[-600, 640], [1280, 2600]]) { c.beginPath(); c.moveTo(x0, by); c.lineTo(x1, by); c.lineTo(x1 + (x0 < 0 ? 70 : -70), 940); c.lineTo(x0, 940); c.closePath(); c.fill(); c.stroke(); hatch(c, k => { k.moveTo(x0, by); k.lineTo(x1, by); k.lineTo(x1 + (x0 < 0 ? 70 : -70), 940); k.lineTo(x0, 940); k.closePath() }, { gap: 9, alpha: 0.3, angle: x0 < 0 ? -0.9 : 0.9, box: [x0, by, x1 - x0, 340] }) }
    // water
    c.strokeStyle = C.ink2; c.lineWidth = 3; for (let i = 0; i < 5; i++) { c.beginPath(); for (let x = 640; x <= 1300; x += 20) { const y = 900 + i * 22 + Math.sin(x * 0.03 + t * 1.6 + i) * 5; x === 640 ? c.moveTo(x, y) : c.lineTo(x, y) } c.stroke() }
    c.fillStyle = C.paper3; c.fillRect(-600, 938, 3200, 400); c.strokeStyle = C.ink; c.lineWidth = 5; c.beginPath(); c.moveTo(-600, 940); c.lineTo(2600, 940); c.stroke(); hatch(c, k => k.rect(-600, 942, 3200, 400), { gap: 10, alpha: 0.3, angle: 0.02, box: [-600, 940, 3200, 400] })
    const ph = clamp(build)
    for (const px of [850, 1070]) {
      const h = 330 * ph; c.fillStyle = C.paper3; c.strokeStyle = C.ink; c.lineWidth = 5; c.fillRect(px - 38, 930 - h, 76, h); c.strokeRect(px - 38, 930 - h, 76, h)
      c.lineWidth = 2; for (let y = 930 - 30; y > 930 - h; y -= 30) { c.beginPath(); c.moveTo(px - 38, y); c.lineTo(px + 38, y); c.stroke() }
      if (ph < 1) { c.lineWidth = 3; for (const dx of [-54, 54]) { c.beginPath(); c.moveTo(px + dx, 930); c.lineTo(px + dx, 930 - h - 60); c.stroke() } c.beginPath(); c.moveTo(px - 54, 930 - h - 30); c.lineTo(px + 54, 930 - h - 30); c.stroke() }
    }
    rails(c, -600, 640, by - 3); rails(c, 1280, 2600, by - 3)
    const g = clamp(build - 1)
    if (g > 0) { c.fillStyle = C.ink; c.fillRect(640, by - 8, 640 * g, 22); c.strokeStyle = C.ink; c.lineWidth = 5; for (let x = 640; x < 640 + 640 * g - 40; x += 80) { c.beginPath(); c.moveTo(x, by + 12); c.lineTo(x + 40, by + 60); c.lineTo(x + 80, by + 12); c.stroke() } c.fillRect(640, by + 56, 640 * g, 8); if (g >= 1) rails(c, 640, 1280, by - 3) }
  }
  function s2(c, t, q, S) {
    const qI = q('from the indian'), qR = q('and at a river') - 0.3, qM = q('several thousand') - 0.3, qC = q('their camps'), qP = q('the man in charge') - 0.35, qW = q('he had been')
    paper(c, t)
    if (t < qR + 0.3) {
      // the line on the map
      const z = 1 + 0.05 * prog(t, S.vis, qR, 'l')
      c.save(); cam(c, W / 2 - 30 * prog(t, S.vis, qR), H / 2, z)
      hatch(c, k => { k.moveTo(1500, -50); k.bezierCurveTo(1420, 300, 1620, 520, 1480, 760); k.bezierCurveTo(1420, 900, 1560, 1000, 1500, 1150); k.lineTo(2100, 1150); k.lineTo(2100, -50); k.closePath() }, { gap: 12, alpha: 0.45, angle: 0.05, wob: 2, box: [1380, -50, 720, 1200] })
      c.strokeStyle = C.ink; c.lineWidth = 5; c.beginPath(); c.moveTo(1500, -50); c.bezierCurveTo(1420, 300, 1620, 520, 1480, 760); c.bezierCurveTo(1420, 900, 1560, 1000, 1500, 1150); c.stroke()
      text(c, 'INDIAN', 1690, 400, F.sc(34), C.ink2, { track: 8 }); text(c, 'OCEAN', 1690, 446, F.sc(34), C.ink2, { track: 8 })
      // the lake
      c.fillStyle = C.paper2; c.beginPath(); c.ellipse(250, 300, 150, 110, 0.2, 0, 7); c.fill(); c.stroke(); hatch(c, k => k.ellipse(250, 300, 150, 110, 0.2, 0, 7), { gap: 10, alpha: 0.4, angle: 0.05, box: [100, 190, 300, 220] })
      text(c, 'UGANDA', 330, 150, F.sc(40), C.ink, { track: 8 }); text(c, 'Lake Victoria', 250, 310, F.bodyI(30), C.ink2)
      const P = u => [lerp(1470, 400, u) + 60 * Math.sin(u * 5), lerp(720, 330, u) + 46 * Math.sin(u * 3.1 + 1)]
      const lp = prog(t, S.vis + 0.5, qI + 2.0, 'io')
      c.strokeStyle = C.red; c.lineWidth = 7; c.setLineDash([22, 10]); c.beginPath(); for (let i = 0; i <= 100 * lp; i++) { const [x, y] = P(i / 100); i ? c.lineTo(x, y) : c.moveTo(x, y) } c.stroke(); c.setLineDash([])
      c.fillStyle = C.ink; c.beginPath(); c.arc(1470, 720, 13, 0, 7); c.fill(); text(c, 'MOMBASA', 1450, 790, F.sc(36), C.ink, { track: 5, align: 'right' })
      const [tx, ty] = P(0.2), ta = prog(t, qR - 0.9, qR - 0.4, 'back')
      if (ta > 0) { c.save(); c.translate(tx, ty); c.scale(ta, ta); c.strokeStyle = C.ink2; c.lineWidth = 4; c.beginPath(); c.moveTo(-30, -90); c.quadraticCurveTo(10, 0, -20, 90); c.stroke(); c.fillStyle = C.red; c.beginPath(); c.arc(0, 0, 17, 0, 7); c.fill(); c.strokeStyle = C.red; c.lineWidth = 4; c.beginPath(); c.arc(0, 0, 30 + 6 * Math.sin(t * 5), 0, 7); c.stroke(); text(c, 'TSAVO', 0, -62, F.head(54, 900), C.red, { track: 5 }); c.restore() }
      text(c, 'THE UGANDA RAILWAY', 980, 130, F.sc(46), C.ink, { track: 12, alpha: prog(t, S.vis + 0.3, S.vis + 1) }); rule(c, 700, 1260, 154, C.ink, prog(t, S.vis + 0.5, S.vis + 1.4))
      c.restore()
      if (t > qR - 0.1) { c.fillStyle = C.paper; c.globalAlpha = prog(t, qR - 0.1, qR + 0.3); c.fillRect(0, 0, W, H); c.globalAlpha = 1 }
      finish(c, t, false); return false
    }
    if (t < qP + 0.25) {
      // the bridge, the men, the camps
      const z = track(t, [[qR, 1.02], [qM, 0.96, 'sine'], [qC, 0.86, 'io'], [qP + 0.3, 0.82, 'l']])
      c.save(); cam(c, 960, track(t, [[qR, 600], [qC, 640, 'io']]), z)
      bridge(c, t, 0.25 + 0.3 * prog(t, qR, qP, 'l'))
      // men coming down the line with loads
      WORK.forEach((p, i) => {
        const inn = prog(t, qM - 0.4 + i * 0.05, qM + 1.6 + i * 0.05, 'o'), home = i % 2 ? lerp(120, 600, p.jit) : lerp(1340, 1900, p.jit), from = i % 2 ? -900 : 2900
        const x = lerp(from, home, inn) + Math.sin(t * 0.7 + i) * 26
        turban(c, x, 596 + 0, p.h * 0.5, { walk: t * 5 * p.sp + p.ph, stride: inn < 1 ? 1 : 0.5, face: i % 2 ? 1 : -1, bulk: p.bulk, arm: i % 3 === 0 ? 0.3 + 0.2 * Math.sin(t * 6 + i) : 0 })
      })
      // the camps, strung out
      const ca = prog(t, qC - 0.2, qC + 0.5)
      if (ca > 0) {
        c.save(); c.globalAlpha = ca
        const y = 330; c.strokeStyle = C.ink; c.lineWidth = 3
        for (let i = 0; i < 26; i++) { const x = -260 + i * 96, p2 = clamp(ca * 2 - i / 26); if (p2 <= 0) continue; c.fillStyle = C.ink; c.beginPath(); c.moveTo(x - 24, y); c.lineTo(x, y - 34 * p2); c.lineTo(x + 24, y); c.closePath(); c.fill() }
        c.beginPath(); c.moveTo(-270, y + 30); c.lineTo(2190, y + 30); c.moveTo(-270, y + 14); c.lineTo(-270, y + 46); c.moveTo(2190, y + 14); c.lineTo(2190, y + 46); c.stroke()
        c.fillStyle = C.paper; c.fillRect(760, y + 6, 400, 50); text(c, '8 miles of camps', 960, y + 46, F.bodyI(46), C.ink)
        c.restore()
      }
      c.restore()
      text(c, 'The bridge over the Tsavo River', W / 2, 110, F.headI(64, 700), C.ink, { alpha: prog(t, qR + 0.3, qR + 1) * (1 - prog(t, qM - 0.3, qM + 0.3)) })
      text(c, 'Several thousand men, most of them from India', W / 2, 110, F.headI(56, 700), C.ink, { alpha: prog(t, qM + 0.2, qM + 0.9) * (1 - prog(t, qC - 0.4, qC)) })
      fade(c, prog(t, qP - 0.2, qP + 0.25), '238,226,200'); finish(c, t, false); return false
    }
    // the engineer
    const z = 1 + 0.04 * prog(t, qP, S.out, 'l')
    c.save(); cam(c, W / 2, H / 2, z)
    c.strokeStyle = C.ink; c.lineWidth = 4; c.beginPath(); c.arc(560, 520, 400, 0, 7); c.stroke(); c.lineWidth = 1.5; c.beginPath(); c.arc(560, 520, 384, 0, 7); c.stroke()
    hatch(c, k => k.arc(560, 520, 384, 0, 7), { gap: 7, alpha: 0.3, angle: -0.5, box: [160, 120, 800, 800] })
    const wx = track(t, [[qP, -160], [qP + 1.4, 560, 'o']])
    c.save(); c.beginPath(); c.rect(0, 0, W, 905); c.clip(); patterson(c, wx, 900, 600, { walk: t * 5, stride: 1 - prog(t, qP + 0.9, qP + 1.4), aim: -1.25, arm: 0.12 }); c.restore()
    c.strokeStyle = C.ink; c.lineWidth = 5; c.beginPath(); c.moveTo(120, 902); c.lineTo(1000, 902); c.stroke()
    text(c, 'THE MAN IN CHARGE', 1380, 330, F.sc(40), C.red, { track: 8, alpha: prog(t, qP + 0.3, qP + 1) })
    rule(c, 1090, 1670, 356, C.ink, prog(t, qP + 0.5, qP + 1.3))
    typeset(c, 'John Henry', 1380, 500, F.head(120, 900), C.ink, prog(t, qP + 1.0, qP + 1.7))
    typeset(c, 'Patterson', 1380, 640, F.head(140, 900), C.ink, prog(t, qP + 1.5, qP + 2.2))
    rule(c, 1090, 1670, 690, C.ink, prog(t, qP + 1.8, qP + 2.5))
    text(c, 'engineer · three weeks at Tsavo', 1380, 780, F.bodyI(50), C.ink2, { alpha: prog(t, qW, qW + 0.6) })
    c.restore()
    fade(c, 1 - prog(t, qP + 0.25, qP + 0.6), '238,226,200'); finish(c, t, false); return false
  }

  // =============================== 3. the devils ===============================
  const CAMP = [[520, 1.0], [860, 1.15], [1220, 1.05], [1560, 0.95]]
  function s3(c, t, q, S) {
    const qB = q('both males'), qNo = q('neither one'), qNot = q('and they did not'), qCame = q('they came at night') - 0.35, qPull = q('and pulled men'), qFought = q('the men fought'), qFen = q('they built fences'), qJump = q('the lions jumped'), qCrawl = q('or crawled'), qFire = q('they kept fires'), qTin = q('they banged'), qNoth = q('nothing worked'), qAfter = q('after a while') - 0.35, qDev = q('they said these'), qWhen = q('and when one'), qBew = q('beware brothers')
    if (t < qCame + 0.3) {
      // two on the ridge
      const z = 1 + 0.05 * prog(t, S.vis, qCame, 'l')
      c.save(); cam(c, W / 2, H / 2, z)
      night(c, t, { moon: [1380, 330, 190] })
      glow(c, 1380, 330, 900, N.blue, 0.2)
      c.fillStyle = INK; c.beginPath(); c.moveTo(-100, 830); for (let x = -100; x <= W + 100; x += 60) c.lineTo(x, 790 - 60 * Math.sin((x + 300) * 0.0016) + 8 * noise(x * 0.01, 2)); c.lineTo(W + 100, H + 50); c.lineTo(-100, H + 50); c.closePath(); c.fill()
      const ry = x => 790 - 60 * Math.sin((x + 300) * 0.0016)
      const x1 = track(t, [[S.vis, 200], [qNot + 1.5, 1250, 'l']]), x2 = x1 - 620
      acacia(c, 1760, ry(1760) + 6, 1.5, INK, 2)
      for (const [x, k] of [[x2, 0], [x1, 1]]) lion(c, x, ry(x) + 6, 3.0, { walk: x * 0.03 + k * 2, stride: 1, col: INK, eye: true, tail: t * 2 + k, head: 0.08 + 0.05 * Math.sin(t * 1.3 + k) })
      c.restore()
      text(c, 'TWO LIONS', 380, 190, F.head(100, 900), C.paper, { align: 'left', track: 8, alpha: prog(t, S.start - 0.1, S.start + 0.4), shadow: '#000' })
      typeset(c, 'both male · both big', 384, 262, F.bodyI(54), C.paper2, prog(t, qB, qB + 1.0), { align: 'left', shadow: '#000' })
      typeset(c, 'no manes', 384, 330, F.bodyI(54), C.gold2, prog(t, qNo + 0.3, qNo + 0.9), { align: 'left', shadow: '#000' })
      fade(c, prog(t, qCame - 0.1, qCame + 0.3)); finish(c, t, true); return true
    }
    if (t < qAfter + 0.3) {
      // the camp and everything that didn't work
      const gy = 840
      const z = track(t, [[qCame, 1.5], [qFought, 1.22, 'sine'], [qNoth + 2, 1.12, 'l']])
      c.save(); cam(c, track(t, [[qCame, 1150], [qFought, 1000, 'sine']]), track(t, [[qCame, 700], [qFought, 660, 'sine']]), z)
      plain(c, t, { moon: [260, 170, 50], hy: 690, trees: 5, seed: 9 })
      const fenceP = prog(t, qFen - 0.1, qFen + 1.3, 'o')
      // lion one comes through the tents and takes a tent's light
      const dark1 = prog(t, qPull + 0.2, qPull + 0.5)
      const fires = prog(t, qFire - 0.1, qFire + 0.5), dim = 1 - 0.45 * prog(t, qNoth, qNoth + 1.2)
      if (fenceP > 0) { c.save(); c.beginPath(); c.rect(240, 0, 1560 * fenceP, H); c.clip(); thorn(c, 250, 1790, gy - 104, 76, '#070910', 12); c.restore() }
      CAMP.forEach(([x, s], i) => tent(c, x, gy - 90, s * 1.15, { col: INK, lit: (i === 1 ? 1 - dark1 : (i === 2 ? 1 - prog(t, qJump + 1.0, qJump + 1.3) : 0.9)) * (0.8 + 0.2 * noise(t * 6 + i, i)) }))
      if (fires > 0) for (const fx of [690, 1040, 1390]) fire(c, fx, gy - 70, 1.25, t, fires * dim)
      // men with tins
      const tins = prog(t, qTin - 0.2, qTin + 0.3) * (1 - prog(t, qAfter - 0.5, qAfter))
      if (tins > 0) for (const [mx, f] of [[600, 1], [1130, -1], [1480, 1]]) { c.save(); c.globalAlpha = tins; const up = 0.35 + 0.3 * Math.sin(t * 16 + mx); turban(c, mx, gy - 60, 190, { col: INK, face: f, arm: up }); c.strokeStyle = `rgba(240,200,104,${0.8 * Math.max(0, Math.sin(t * 16 + mx))})`; c.lineWidth = 4; for (const a of [-0.6, 0, 0.6]) { c.beginPath(); c.moveTo(mx + f * (70 + 0), gy - 210 + a * 30); c.lineTo(mx + f * 104, gy - 216 + a * 46); c.stroke() } c.restore() }
      // the thorn fence across the front
      if (fenceP > 0) { c.save(); c.beginPath(); c.rect(1880 - 1760 * fenceP, 0, 1760 * fenceP + 200, H); c.clip(); thorn(c, 120, 1900, gy + 40, 110, INK, 8); c.restore() }
      // lion one: before the fence, slipping in between the tents
      const l1 = track(t, [[qCame, 2300], [qPull + 0.3, 1010, 'sine'], [qPull + 1.3, 1010, 'l'], [qFought + 0.8, 2400, 'i']])
      if (t < qFought + 0.9) lion(c, l1, gy - 60, 2.0, { face: t < qPull + 1.0 ? -1 : 1, walk: l1 * 0.04, stride: (t < qPull + 0.3 || t > qPull + 1.3) ? 1 : 0, crouch: 0.6, eye: true, col: INK })
      // over the fence
      const jp = prog(t, qJump - 0.25, qJump + 0.85, 'l')
      if (jp > 0 && jp < 1) { const jx = lerp(2050, 1250, jp), jy = gy + 46 - Math.sin(jp * Math.PI) * 330; lion(c, jx, jy, 2.3, { face: -1, leap: Math.sin(jp * Math.PI), rot: (jp - 0.5) * 0.9, eye: true, col: INK, mouth: 0.6 }) }
      if (jp >= 1 && t < qCrawl + 0.2) lion(c, 1250 - 200 * prog(t, qJump + 0.85, qCrawl + 0.2), gy - 50, 2.0, { face: -1, walk: t * 9, stride: 1, crouch: 0.4, eye: true, col: INK })
      // or under it
      const cp = prog(t, qCrawl - 0.1, qCrawl + 1.7, 'l')
      if (cp > 0 && cp < 1) lion(c, lerp(-200, 520, cp), gy + 70, 2.4, { face: 1, walk: cp * 22, stride: 0.7, crouch: 1, eye: true, col: INK, head: 0.3 })
      // nothing worked: the eyes outside the light
      const ev = prog(t, qNoth - 0.1, qNoth + 0.7)
      if (ev > 0) { eyes(c, 250, 800, 2.2, ev); eyes(c, 1760, 820, 2.4, ev * (Math.sin(t * 1.3) > -0.9 ? 1 : 0.1)) }
      c.restore()
      const lab = (s, a, b) => text(c, s, W / 2, 130, F.headI(70, 700), C.paper, { alpha: prog(t, a, a + 0.4) * (1 - prog(t, b - 0.35, b)), shadow: '#000', blur: 30 })
      lab('Fences of thorn', qFen + 0.2, qFire - 0.1); lab('Fires all night', qFire + 0.1, qTin - 0.05); lab('Banging on oil tins', qTin + 0.1, qNoth - 0.1)
      text(c, 'Nothing worked.', W / 2, 150, F.head(110, 900), C.red2, { alpha: prog(t, qNoth, qNoth + 0.3) * (1 - prog(t, qAfter - 0.3, qAfter + 0.2)), shadow: '#000', blur: 40 })
      fade(c, 1 - prog(t, qCame + 0.3, qCame + 0.8) + prog(t, qAfter - 0.1, qAfter + 0.3)); finish(c, t, true); return true
    }
    // devils in the shape of lions
    const z = 1 + 0.07 * prog(t, qAfter, S.out, 'l')
    c.save(); cam(c, W / 2, H / 2 - 20, z)
    const g = c.createRadialGradient(960, 900, 60, 960, 900, 1300); g.addColorStop(0, '#6a2a14'); g.addColorStop(0.5, '#2a1210'); g.addColorStop(1, '#07060a'); c.fillStyle = g; c.fillRect(-100, -100, W + 200, H + 200)
    // the shadows the fire throws: far bigger than the animals
    const grow = prog(t, qDev - 0.3, qDev + 2.2, 'o'), fl = 1 + 0.04 * noise(t * 7, 1)
    ghost(c, 0.55 * prog(t, qAfter + 0.4, qDev + 0.5), (o) => {
      lion(o, 560, 1010, (4.6 + 2.0 * grow) * fl, { col: '#040305', walk: t * 0.6, stride: 0.2, eye: true, head: -0.1 }); lion(o, 1500, 1020, (4.2 + 2.0 * grow) * fl, { col: '#040305', face: -1, walk: t * 0.5 + 2, stride: 0.2, eye: true, head: -0.1, mouth: grow })
    })
    c.fillStyle = '#050406'; c.fillRect(-100, 930, W + 200, 300)
    fire(c, 960, 940, 2.2, t, 1)
    // men close around the fire
    crowd(9, 31, { h: 250, ladies: 0 }).forEach((p, i) => turban(c, 520 + i * 110 + (i > 4 ? 60 : -60), 990 + (i % 2) * 30, p.h, { col: '#050406', face: i < 5 ? 1 : -1, lean: (i < 5 ? 1 : -1) * 0.06 + 0.02 * Math.sin(t * 2 + i), bulk: p.bulk }))
    c.restore()
    text(c, 'Devils, in the shape of lions', W / 2, 140, F.headI(76, 700), C.paper, { alpha: prog(t, qDev + 0.4, qDev + 1.1) * (1 - prog(t, qWhen - 0.2, qWhen + 0.3)), shadow: '#000', blur: 30 })
    const ba = prog(t, qBew - 0.2, qBew + 0.4)
    if (ba > 0) { text(c, '“Khabar dar, bhaieon,', W / 2, 150, F.headI(84, 700), C.gold2, { alpha: ba, shadow: '#000', blur: 30 }); text(c, 'shaitan ata!”', W / 2, 250, F.headI(84, 700), C.gold2, { alpha: prog(t, qBew + 0.5, qBew + 1.0), shadow: '#000', blur: 30 }) }
    fade(c, 1 - prog(t, qAfter + 0.3, qAfter + 0.8)); finish(c, t, true); return true
  }

  window.SCENES = [s1, s2, s3]
  window.TS = { cam, fade, plain, bridge, INK, WORK }
})()
