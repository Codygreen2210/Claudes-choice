// scB.js: scenes 8-14 of The Serum Run.
(function () {
  const { clamp, lerp, EZ, prog, bump, rng, noise, track, mix } = K
  const { W, H, C, F, paper, finish, hatch, rr, text, typeset, rule, person, glow, tw, block, coin } = L
  const { INK, SN, dog, parka, kneel, sled, team, spruce, cabin, biplane, snowland, snowfall, alaska, proj, PL, onRoute, route } = SR
  const { fade, zoom, trail, nome, shore, lostScene, relayMap, dot, RM, RED, vial, thermo } = SRS

  // =============================== 8. Seppala and Togo ===============================
  const BAY = { cx: -161.55, cy: 64.52, k: 1150, x: 960, y: 560 }
  function s8(c, t, q, S) {
    const qLeo = q('leonhard seppala'), qLead = q('his lead dog') - 0.3, qSmall = q('togo was small'), q12 = q('twelve years old'), qPup = q('as a pup') - 0.4, qJump = q('togo jumped'), qRan = q('and ran miles'), qKept = q('seppala kept') - 0.3, qLeft = q('they left nome') - 0.4, q170 = q('170 miles out'), qSer = q('the serum the serum') - 0.4, qTook = q('seppala took it'), qAr = q('around the bay') - 0.4, qAc = q('or straight across'), qSh = q('across was twenty'), qCr = q('already cracking'), qWent = q('he went across')
    if (t < qPup + 0.3) {
      snowland(c, t, { hy: 760, dawn: 0.75, stars: 0 })
      for (let i = 0; i < 8; i++) spruce(c, 40 + i * 270, 768, 0.6 + (i % 3) * 0.12, '#59627f', i)
      const cx = lerp(820, 1180, prog(t, qLead - 0.2, qLead + 1.2, 'io')), z = lerp(1.0, 1.45, prog(t, qLead - 0.2, qLead + 1.2, 'io'))
      c.save(); zoom(c, cx, 640, z)
      sled(c, 180, 880, 1.4, { load: null }); for (let k = 0; k < 5; k++) dog(c, 460 + k * 120, 880, 1.4, { head: k % 2 ? 0.3 : 0 })
      c.strokeStyle = INK; c.lineWidth = 3; c.beginPath(); c.moveTo(350, 852); c.lineTo(1160, 836); c.stroke()
      parka(c, 150, 882, 170, {})
      dog(c, 1240, 880, 1.16, { sit: t > qSmall ? 0 : 0, head: -0.1 })
      c.restore()
      typeset(c, 'Leonhard Seppala', 520, 230, F.headI(84, 700), C.ink, prog(t, qLeo - 0.2, qLeo + 1.0))
      text(c, 'TOGO', 1420, 300, F.head(130, 900), C.ink, { track: 16, alpha: prog(t, qLead + 0.8, qLead + 1.3) })
      typeset(c, 'small for a sled dog · 12 years old', 1420, 370, F.bodyI(50), C.red, prog(t, qSmall, q12 + 0.8))
      finish(c, t, false); return false
    }
    if (t < qLeft + 0.3) {
      // the pup and the window
      snowland(c, t, { hy: 760, dawn: 0.6, stars: 0 })
      c.fillStyle = INK; c.fillRect(-20, 300, 760, 560); c.fillStyle = '#d5dcec'; c.fillRect(-20, 288, 780, 16)
      const jp = prog(t, qJump - 0.1, qJump + 0.7, 'l'), broke = t > qJump + 0.12
      c.fillStyle = broke ? mix(INK, '#5b6889', 0.5) : C.gold2; c.fillRect(420, 470, 190, 170); glow(c, 515, 555, 260, '246,199,112', broke ? 0.15 : 0.4); c.fillStyle = INK; c.fillRect(511, 470, 8, 170); c.fillRect(420, 551, 190, 8)
      if (broke) { const r = rng(5); for (let i = 0; i < 14; i++) { const a = clamp((t - qJump - 0.12) / 0.9), ang = -0.9 + r() * 1.6, sp = 160 + r() * 260; c.save(); c.translate(610 + Math.cos(ang) * sp * a, 560 + Math.sin(ang) * sp * a + 300 * a * a); c.rotate(r() * 6 + a * 4); c.globalAlpha = 1 - a; c.fillStyle = '#eef2fa'; c.beginPath(); c.moveTo(-9, -6); c.lineTo(11, 0); c.lineTo(-5, 9); c.closePath(); c.fill(); c.restore() } }
      const px = t < qJump - 0.1 ? 500 : t < qJump + 0.7 ? lerp(520, 900, jp) : 900 + (t - qJump - 0.7) * 420
      const py = t < qJump + 0.7 ? 640 - Math.sin(jp * Math.PI) * 120 + jp * 220 : 860
      if (t > qJump - 0.1 && px < 2200) dog(c, px, py, 0.82, { run: t < qJump + 0.7 ? 1.2 : px * 0.06, stride: 1 })
      if (t > qKept - 0.2) { const a = prog(t, qKept - 0.2, qKept + 0.3); fade(c, a * 0.001); c.save(); c.globalAlpha = a; parka(c, 1380, 862, 210, { face: -1 }); dog(c, 1200, 862, 0.82, { sit: 1 }); c.restore() }
      fade(c, 1 - prog(t, qPup + 0.3, qPup + 0.7), '238,226,200'); finish(c, t, false); return false
    }
    if (t < qSer + 0.3) {
      paper(c, t); c.save(); zoom(c, 600, 540, 1.5 + 0.06 * prog(t, qLeft, qSer, 'l'))
      const sp = prog(t, qLeft + 0.3, q170 + 1.4, 'io'), meet = 0.795
      hatch(c, k => k.rect(0, 0, W, H), { gap: 14, alpha: 0.14, angle: 0, box: [0, 0, W, H], wob: 3 }); alaska(c, RM, { fill: C.paper2 })
      route(c, RM, 0, 1, C.ink3, 4, [3, 12]); route(c, RM, 0, lerp(0.62, meet, sp), RED, 7)
      route(c, RM, lerp(1, meet, sp), 1, C.ink, 7)
      dot(c, RM, 'nome', C.ink, 12, 'Nome', { dy: 52, dx: -30, px: 34 })
      for (const p of [lerp(0.62, meet, sp), lerp(1, meet, sp)]) { const [x, y] = proj(RM, onRoute(p)); c.fillStyle = p < meet + 0.001 && p === lerp(0.62, meet, sp) ? RED : C.ink; c.strokeStyle = C.ink; c.lineWidth = 3; c.beginPath(); c.arc(x, y, 11, 0, 7); c.fill(); c.stroke() }
      const b = proj(RM, [-163.4, 63.75]); text(c, 'Bering Sea', b[0], b[1], F.bodyI(34), C.ink2)
      c.restore()
      text(c, 'the serum', 1500, 420, F.headI(64, 700), RED, { alpha: prog(t, qLeft + 0.6, qLeft + 1.1) }); text(c, 'Seppala and Togo', 420, 330, F.headI(64, 700), C.ink, { alpha: prog(t, qLeft + 0.2, qLeft + 0.7) })
      text(c, '170 miles', 420, 410, F.head(84, 900), C.ink, { alpha: prog(t, q170 - 0.1, q170 + 0.3) })
      finish(c, t, false); return false
    }
    if (t < qAr + 0.3) {
      // the meeting, in a storm
      trail(c, t, { team: false, bliz: 0.75, wind: -480, speed: 0, off: 0, trees: false, stars: 0 })
      const ap = prog(t, qSer, qSer + 1.6, 'o'), gy = 836, turned = t > qTook + 0.5
      team(c, lerp(-900, -60, ap), gy, 1.15, { n: 5, stride: ap < 1 ? 1 : 0, run: t * 9, load: t < qTook ? RED : null })
      c.save(); c.translate(W, 0); c.scale(-1, 1); team(c, lerp(-900, -40, ap), gy + 16, 1.15, { n: 6, stride: ap < 1 ? 1 : 0, run: t * 9 + 1, load: t < qTook ? null : RED }); c.restore()
      snowfall(c, t, 0.9, -620, 5); B.fog(c, t, 0.35, { col: '#9aa6c4', y0: 300, y1: 1000, drift: 140, n: 18 })
      typeset(c, '“The serum! The serum! I have it here!”', W / 2, 250, F.headI(72, 700), C.paper, prog(t, qSer + 0.3, qSer + 2.4), { shadow: '#000' })
      fade(c, 1 - prog(t, qSer + 0.3, qSer + 0.7)); finish(c, t, true); return true
    }
    // the choice: around the bay, or across the ice
    paper(c, t); c.save(); zoom(c, 960, 540, 1 + 0.04 * prog(t, qAr, S.out, 'l'))
    c.fillStyle = '#dfe5ee'; c.fillRect(0, 0, W, H); alaska(c, BAY, { fill: C.paper2, lw: 5 })
    const A = proj(BAY, PL.shaktoolik), Z = proj(BAY, PL.isaacs), top = proj(BAY, [-160.95, 64.78])
    // cracks in the ice
    c.save(); c.strokeStyle = C.ink3; c.lineWidth = 3; const r = rng(4), cr = prog(t, qCr - 0.4, qCr + 0.6)
    for (let i = 0; i < 9; i++) { const k = (i + 0.5) / 9; if (k > cr * 1.1) break; const x = lerp(A[0], Z[0], k), y = lerp(A[1], Z[1], k); c.beginPath(); c.moveTo(x - 40 + r() * 20, y - 70 - r() * 40); c.lineTo(x + r() * 30, y - 10); c.lineTo(x - 20 + r() * 40, y + 60 + r() * 50); c.stroke() } c.restore()
    const ar = prog(t, qAr, qAr + 1.3, 'io'), ac = prog(t, qAc, qAc + 1.0, 'io'), went = prog(t, qWent - 0.2, qWent + 0.5)
    c.save(); c.globalAlpha = lerp(1, 0.3, went); c.strokeStyle = C.ink; c.lineWidth = 9; c.setLineDash([16, 12]); c.lineCap = 'round'; c.beginPath(); c.moveTo(A[0] + 10, A[1] - 6)
    for (let k = 0; k <= ar; k += 0.02) { const x = (1 - k) * (1 - k) * (A[0] + 10) + 2 * k * (1 - k) * (top[0] + 240) + k * k * Z[0], y = (1 - k) * (1 - k) * (A[1] - 6) + 2 * k * (1 - k) * (top[1] - 250) + k * k * Z[1]; c.lineTo(x, y) } c.stroke(); c.restore()
    c.save(); c.strokeStyle = RED; c.lineWidth = lerp(9, 16, went); c.lineCap = 'round'; c.beginPath(); c.moveTo(A[0], A[1]); c.lineTo(lerp(A[0], Z[0], ac), lerp(A[1], Z[1], ac)); c.stroke(); c.restore()
    for (const [P, lab, al] of [[A, 'Shaktoolik', 'left'], [Z, 'Isaac’s Point', 'right']]) { c.fillStyle = C.ink; c.beginPath(); c.arc(P[0], P[1], 13, 0, 7); c.fill(); text(c, lab, P[0] + (al === 'left' ? 26 : -26), P[1] + 50, F.bodyI(40), C.ink, { align: al }) }
    text(c, 'around the bay', top[0] - 60, top[1] + 150, F.headI(54, 700), C.ink, { alpha: ar * lerp(1, 0.3, went) })
    text(c, 'across the ice', (A[0] + Z[0]) / 2 - 190, (A[1] + Z[1]) / 2 + 150, F.headI(60, 700), RED, { alpha: ac })
    text(c, '20 miles shorter', (A[0] + Z[0]) / 2 - 190, (A[1] + Z[1]) / 2 + 215, F.bodyI(46), C.ink, { alpha: prog(t, qSh, qSh + 0.5) })
    text(c, 'Norton Sound', 420, 900, F.sc(54), C.ink3, { track: 14 })
    c.restore(); finish(c, t, false); return false
  }

  // =============================== 9. the ice ===============================
  const MILES = [52, 31, 28, 26, 34, 24, 30, 30, 28, 24, 18, 30, 36, 40, 34, 40, 0.5, 261, 25, 53]
  function s9(c, t, q, S) {
    const qCould = q('seppala could not'), qSo = q('so he left it') - 0.3, qOld = q('and the old dog'), qIn = q('and brought them in'), qSl = q('they slept') - 0.4, qBeh = q('behind them') - 0.4, qBroke = q('broke up'), qThen = q('then togo led') - 0.4, qBy = q('by the time') - 0.4, q261 = q('261 miles'), qNo = q('no one else')
    if (t < qSl + 0.3) {
      const lit = prog(t, qIn - 0.6, qIn + 0.8)
      trail(c, t, { n: 7, bliz: 0.62, wind: -700, speed: 300, ice: true, stars: 0, tx: 100, s: 1.5,
        after: (k, off, gy) => { const lx = 100 + (185 + 6 * 88) * 1.5; k.save(); k.strokeStyle = 'rgba(236,240,250,0.55)'; k.lineWidth = 4; k.setLineDash([4, 22]); k.lineCap = 'round'; k.globalAlpha = prog(t, qOld - 0.2, qOld + 0.6) * (1 - lit); k.beginPath(); k.moveTo(lx + 70, gy - 8); k.lineTo(W + 40, gy - 8); k.stroke(); k.restore()
          if (lit > 0) { const x = lerp(2500, 1640, prog(t, qIn - 0.6, qSl + 0.3, 'o')); cabin(k, x, gy - 50, 1.0, { t, lit }) } } })
      text(c, 'wind chill  −85°F', W / 2, 220, F.head(100, 900), C.paper, { alpha: prog(t, S.start + 1.2, S.start + 1.7) * (1 - prog(t, qSo - 0.4, qSo)), shadow: '#000', blur: 30 })
      text(c, 'TOGO', 1500, 640, F.head(70, 900), C.paper, { track: 10, alpha: prog(t, qSo, qSo + 0.4) * (1 - prog(t, qIn - 0.5, qIn)), shadow: '#000' })
      finish(c, t, true); return true
    }
    if (t < qThen + 0.3) {
      // morning: the ice they crossed, breaking up
      const dw = 0.55, hy = 620, br = prog(t, qBroke - 0.3, qThen, 'o')
      snowland(c, t, { hy, dawn: dw, stars: 0, hills: false })
      c.fillStyle = '#16203c'; c.fillRect(0, hy + 40, W, H)
      const r = rng(12); for (let i = 0; i < 16; i++) { const x0 = (i % 8) * 250 + r() * 60 - 40, y0 = hy + 60 + Math.floor(i / 8) * 190 + r() * 40, w = 230 + r() * 60, h = 150 + r() * 40, dx = (r() - 0.3) * 260 * br, dy = (r() - 0.2) * 70 * br; c.save(); c.translate(x0 + dx + w / 2, y0 + dy + h / 2); c.rotate((r() - 0.5) * 0.3 * br); c.fillStyle = mix('#b4bfd6', '#e9e3d6', dw); c.beginPath(); c.moveTo(-w / 2, -h / 2 + 12); c.lineTo(-w / 6, -h / 2); c.lineTo(w / 2, -h / 2 + 18); c.lineTo(w / 2 - 14, h / 2 - 8); c.lineTo(0, h / 2); c.lineTo(-w / 2 + 10, h / 2 - 16); c.closePath(); c.fill(); c.restore() }
      c.fillStyle = mix('#b4bfd6', '#e9e3d6', dw); c.fillRect(0, hy, W, 44)
      team(c, lerp(900, 1500, prog(t, qSl, qThen, 'l')), hy + 30, 0.5, { n: 7, run: t * 9, load: RED })
      for (let i = 0; i < 5; i++) spruce(c, 1500 + i * 110, hy + 8, 0.34, '#59627f', i)
      snowfall(c, t, 0.3, -420, 3)
      fade(c, 1 - prog(t, qSl + 0.3, qSl + 0.7)); finish(c, t, false); return false
    }
    if (t < qBy + 0.3) {
      // the mountain
      const dw = 0.5; snowland(c, t, { hy: 1200, dawn: dw, stars: 0, hills: false })
      c.fillStyle = mix('#8f9bb8', '#d8d4cc', dw); c.beginPath(); c.moveTo(-50, 1100); c.lineTo(500, 760); c.lineTo(1250, 330); c.lineTo(1500, 300); c.lineTo(1970, 560); c.lineTo(1970, 1100); c.closePath(); c.fill()
      c.fillStyle = mix('#5b6889', '#a7a9b8', dw); c.beginPath(); c.moveTo(1500, 300); c.lineTo(1970, 560); c.lineTo(1970, 1100); c.lineTo(1300, 1100); c.closePath(); c.fill()
      const p = prog(t, qThen, qBy + 0.3, 'l'), x = lerp(60, 620, p), y = 1100 - (x + 50) / 550 * 340 + (x > 500 ? 0 : 0)
      c.save(); c.translate(x, lerp(1040, 700, p)); c.rotate(-0.52); team(c, 0, 0, 0.8, { n: 7, run: t * 7, load: RED }); c.restore()
      snowfall(c, t, 0.45, -520, 3)
      text(c, '5,000 feet of climbing', 500, 230, F.headI(66, 700), C.ink, { alpha: prog(t, qThen + 0.8, qThen + 1.3), stroke: '#e9e3d6', sw: 8 })
      fade(c, 1 - prog(t, qThen + 0.3, qThen + 0.6), '233,227,214'); finish(c, t, false); return false
    }
    paper(c, t)
    text(c, 'miles run by each team', 640, 420, F.headI(64, 700), C.ink, { alpha: prog(t, qBy + 0.3, qBy + 0.8) })
    const bx = 220, bw = 74, base = 860
    c.strokeStyle = C.ink; c.lineWidth = 4; c.beginPath(); c.moveTo(bx - 20, base); c.lineTo(bx + 20 * bw + 20, base); c.stroke()
    MILES.forEach((m, i) => { const a = prog(t, qBy + 0.4 + i * 0.06, qBy + 0.9 + i * 0.06, 'o') * (i === 17 ? prog(t, q261 - 0.6, q261 + 0.3, 'o') : 1), h = m * 2.4 * a; c.fillStyle = i === 17 ? RED : C.ink; c.fillRect(bx + i * bw + 8, base - h, bw - 16, h) })
    text(c, '261', bx + 17.5 * bw, base - 261 * 2.4 - 24, F.head(84, 900), RED, { alpha: prog(t, q261, q261 + 0.3) })
    text(c, 'Seppala and Togo', bx + 17 * bw - 16, base - 261 * 2.4 + 50, F.headI(50, 700), C.ink, { alpha: prog(t, q261 + 0.2, q261 + 0.7), align: 'right' })
    text(c, 'counting the run out from Nome to meet the relay', W / 2, 950, F.bodyI(40), C.ink2, { alpha: prog(t, qNo, qNo + 0.6) })
    finish(c, t, false); return false
  }

  // =============================== 10. the last driver ===============================
  function s10(c, t, q, S) {
    const qDoc = q('the doctor sent word') - 0.3, qStop = q('stop wait'), qMsg = q('the message never') - 0.3, qName = q('his name was') - 0.4, qBalto = q('his lead dog was'), qLeft = q('he left at ten') - 0.4, qSee = q('he could not see'), qFound = q('balto found'), qGust = q('then a gust') - 0.3, qThrew = q('and threw it'), qSet = q('and when he set') - 0.3, qGone = q('was gone'), qTook = q('he took off') - 0.3, qHand = q('and his hand closed'), qMetal = q('on metal')
    if (t < qName + 0.3) {
      // the wire: the order to stop, lost in the storm
      trail(c, t, { team: false, bliz: 0.95, wind: -900, speed: 0, off: 0, stars: 0, trees: false })
      const snap = prog(t, qMsg + 0.2, qMsg + 0.9, 'i')
      c.strokeStyle = INK; c.fillStyle = INK; c.lineCap = 'round'
      for (const [x, k] of [[300, 0], [960, 1], [1620, 0]]) { c.save(); c.translate(x, 860); c.rotate(k ? snap * 0.9 : 0); c.fillRect(-9, -520, 18, 520); c.fillRect(-90, -500, 180, 12); c.fillRect(-70, -450, 140, 10); c.restore() }
      c.lineWidth = 3; const sag = (x0, x1, y, cut) => { c.beginPath(); c.moveTo(x0, y); c.quadraticCurveTo((x0 + x1) / 2, y + 60, x1, y); c.stroke() }
      sag(-40, 300, 362); if (snap < 0.05) { sag(300, 960, 362); sag(960, 1620, 362) } else { c.beginPath(); c.moveTo(300, 362); c.quadraticCurveTo(360, 620 * snap + 362 * (1 - snap), 420 + 60 * Math.sin(t * 6), 362 + 420 * snap); c.stroke(); c.beginPath(); c.moveTo(1620, 362); c.quadraticCurveTo(1560, 620 * snap + 362 * (1 - snap), 1500 + 60 * Math.sin(t * 5), 362 + 420 * snap); c.stroke() }
      sag(1620, 1960, 362)
      const mp = prog(t, qStop - 0.3, qMsg + 0.2), fly = prog(t, qMsg + 0.2, qMsg + 1.6, 'i')
      if (mp > 0 && fly < 1) { c.save(); c.translate(lerp(400, 960, mp) - fly * 1500, 300 - fly * 200 + Math.sin(fly * 9) * 60); c.rotate(-fly * 3); c.fillStyle = '#f4ead2'; c.fillRect(-150, -46, 300, 92); text(c, 'STOP · WAIT', 0, 16, F.old(40, true), C.red, { track: 3 }); c.restore() }
      snowfall(c, t, 1, -900, 5); B.fog(c, t, 0.42, { col: '#9aa6c4', y0: 200, y1: 1000, drift: 200, n: 22 })
      text(c, 'winds of 80 miles an hour', W / 2, 180, F.headI(72, 700), C.paper, { alpha: prog(t, S.start + 1.2, S.start + 1.8) * (1 - prog(t, qDoc - 0.3, qDoc)), shadow: '#000' })
      finish(c, t, true); return true
    }
    if (t < qGust + 0.3) {
      const go = prog(t, qLeft, qLeft + 1.4, 'io'), white = prog(t, qSee - 0.2, qSee + 1.0) * (1 - 0.0)
      trail(c, t, { n: 7, bliz: 0.8 + 0.2 * white, wind: 760, speed: 250 * go, off: 250 * Math.max(0, t - qLeft) * (go < 1 ? go * 0.5 : 1), stars: 0, tx: 150, trees: false,
        before: (k, off) => { if (off < 1400) cabin(k, 420 - off, 800, 1.25, { t, lit: 1 }) } })
      if (white > 0) { c.save(); c.globalAlpha = white * 0.7; c.fillStyle = '#aab4cf'; c.fillRect(0, 0, W, H); c.restore(); dog(c, 150 + (185 + 6 * 88) * 1.6, 850, 1.6, { run: 250 * Math.max(0, t - qLeft) * 0.042 + 2.4, stride: 1 }); snowfall(c, t, 1, 900, 9) }
      typeset(c, 'Gunnar Kaasen', W / 2, 200, F.headI(84, 700), C.paper, prog(t, qName + 0.5, qName + 1.4), { shadow: '#000', alpha: 1 - prog(t, qLeft - 0.3, qLeft) })
      text(c, 'BALTO', 1380, 620, F.head(80, 900), C.paper, { track: 12, alpha: prog(t, qBalto + 0.6, qBalto + 1.0) * (1 - prog(t, qLeft - 0.3, qLeft)) + prog(t, qFound - 0.1, qFound + 0.3) * (1 - prog(t, qGust - 0.3, qGust)), shadow: '#000' })
      fade(c, 1 - prog(t, qName + 0.3, qName + 0.7)); finish(c, t, true); return true
    }
    // the sled goes over; the callback to the opening
    const tip = prog(t, qThrew - 0.2, qThrew + 0.3, 'i') * (1 - prog(t, qSet, qSet + 0.8, 'io')), dig = prog(t, qTook + 0.8, qTook + 1.2), found = prog(t, qMetal - 0.3, qMetal + 0.3)
    const z = 1.0 + 0.12 * prog(t, qTook, S.out, 'io')
    c.save(); zoom(c, lerp(900, 1100, prog(t, qTook, S.out, 'io')), 600, z)
    lostScene(c, t, { tip: t < qSet + 0.8 ? Math.max(tip, t > qThrew + 0.3 && t < qSet ? 1 : tip) : 0, dig, found, ghost: 0 })
    c.restore()
    if (t < qTook + 0.8) { c.save(); c.restore() }
    snowfall(c, t, 0.9, 700, 3); B.fog(c, t, 0.3, { col: '#9aa6c4', y0: 300, y1: 1000, drift: -140, n: 18 })
    fade(c, 1 - prog(t, qGust + 0.3, qGust + 0.6)); finish(c, t, true); return true
  }

  // =============================== 11. Front Street ===============================
  function s11(c, t, q, S) {
    const qThought = q('he thought'), qWake = q('kaasen did not wake') - 0.4, q530 = q('at 530') - 0.4, qPull = q('balto pulled'), qStiff = q('kaasen was so stiff') - 0.3, qUn = q('the doctor unwrapped') - 0.4, qNot = q('not a single'), q674 = q('six hundred and seventy') - 0.4, q5 = q('in 5')
    if (t < q530 + 0.3) {
      const off = 300 * (t - S.vis)
      trail(c, t, { n: 7, bliz: 0.55, wind: 520, speed: 300, stars: 0.3, tx: 150, trees: false, before: (k) => { const x = 2300 - off * 0.72; cabin(k, x, 800, 1.3, { t, lit: 0, smoke: 0.3 }); sled(k, x - 330, 806, 1.1, { load: null }); for (let i = 0; i < 4; i++) dog(k, x - 520 - i * 90, 806, 1.05, { lie: 1, head: 1 }) } })
      typeset(c, 'the next driver was asleep', W / 2, 220, F.headI(70, 700), C.paper, prog(t, S.start + 0.6, S.start + 1.8), { shadow: '#000', alpha: 1 - prog(t, q530 - 0.4, q530) })
      finish(c, t, true); return true
    }
    if (t < qUn + 0.3) {
      const dw = 0.18 + 0.2 * prog(t, q530, qUn), ar = prog(t, q530 + 0.3, qPull + 2.2, 'o')
      c.save(); zoom(c, 960, 580, 1.06); shore(c, t, { hy: 700, dawn: dw, stars: 0.6 }); nome(c, t, { gy: 706, lit: 0.08 + 0.8 * prog(t, qPull + 1.5, qUn), smoke: 0.5 })
      c.restore()
      team(c, lerp(-1100, 420, ar), 880, 1.2, { n: 7, run: t * 9, stride: ar < 1 ? 1 : 0, load: RED })
      const pp = prog(t, qStiff - 0.3, qUn); for (let i = 0; i < 6; i++) { const a = clamp(pp * 6 - i * 0.7); if (a > 0) person(c, lerp(2100, 1500 + i * 0, a) - i * -70 + 0, 884 + (i % 2) * 8, 150 + (i % 3) * 10, { hat: ['cap', 'bowler', 'none', 'cap', 'none', 'bowler'][i], lady: i % 3 === 2, col: INK, face: -1, walk: t * 6 + i, stride: a < 1 ? 1 : 0 }) }
      snowfall(c, t, 0.3, 300, 3)
      text(c, 'Front Street, Nome', W / 2, 190, F.headI(76, 700), C.paper, { alpha: prog(t, qPull + 0.6, qPull + 1.2), shadow: '#000' })
      typeset(c, '5:30 a.m. · February 2', W / 2, 262, F.bodyI(54), C.gold2, prog(t, q530 + 0.4, q530 + 1.6), { shadow: '#000' })
      fade(c, 1 - prog(t, q530 + 0.3, q530 + 0.7)); finish(c, t, true); return true
    }
    if (t < q674 + 0.3) {
      c.fillStyle = '#0b0c12'; c.fillRect(0, 0, W, H); glow(c, 960, 520, 900, '246,199,112', 0.32)
      const n = 11; for (let i = 0; i < n; i++) { const a = prog(t, qUn + 0.6 + i * 0.12, qUn + 0.9 + i * 0.12, 'back'); vial(c, 960 + (i - (n - 1) / 2) * 120, 520, 2.3 * a, C.gold2, clamp(a)) }
      text(c, 'not a single vial broken', W / 2, 860, F.headI(76, 700), C.paper, { alpha: prog(t, qNot + 0.2, qNot + 0.8) })
      fade(c, 1 - prog(t, qUn + 0.3, qUn + 0.6)); finish(c, t, true); return true
    }
    c.save(); zoom(c, 960, 580, 1.06 + 0.04 * prog(t, q674, S.out, 'l')); shore(c, t, { hy: 700, dawn: 0.75, stars: 0 }); nome(c, t, { gy: 706, lit: 0.9, smoke: 1 }); c.restore()
    text(c, '674 MILES', W / 2, 250, F.head(170, 900), C.ink, { track: 10, alpha: prog(t, q674 + 0.3, q674 + 0.8) })
    text(c, 'in 5½ days', W / 2, 400, F.headI(110, 700), C.red, { alpha: prog(t, q5 - 0.1, q5 + 0.4) })
    fade(c, 1 - prog(t, q674 + 0.3, q674 + 0.7), '233,227,214'); finish(c, t, false); return false
  }

  // =============================== 12. after ===============================
  function medal(c, x, y, s) { c.save(); c.translate(x, y); c.scale(s, s); c.fillStyle = C.red; c.beginPath(); c.moveTo(-14, -56); c.lineTo(14, -56); c.lineTo(8, -14); c.lineTo(-8, -14); c.closePath(); c.fill(); c.fillStyle = C.gold; c.strokeStyle = C.ink; c.lineWidth = 3; c.beginPath(); c.arc(0, 8, 24, 0, 7); c.fill(); c.stroke(); c.restore() }
  function s12(c, t, q, S) {
    const qOff = q('the official count') - 0.4, q57 = q('between five and'), qBel = q('the doctor believed') - 0.3, qEv = q('every driver got') - 0.4, qLet = q('and a letter'), qSec = q('a second shipment') - 0.4, qThat = q('that one came')
    if (t < qEv + 0.3) {
      c.save(); zoom(c, 960, 580, 1.06 + 0.05 * prog(t, S.vis, qEv, 'l')); shore(c, t, { hy: 700, dawn: 0.85, stars: 0 }); nome(c, t, { gy: 706, lit: 1, smoke: 1 }); c.restore()
      text(c, 'the epidemic was stopped', W / 2, 250, F.headI(84, 700), C.ink, { alpha: prog(t, S.start + 1.6, S.start + 2.2) * (1 - prog(t, qOff - 0.3, qOff)) })
      text(c, '5 to 7 dead in Nome', W / 2, 250, F.head(100, 900), C.ink, { alpha: prog(t, q57 - 0.3, q57 + 0.3) })
      typeset(c, 'likely more in the camps outside town', W / 2, 340, F.bodyI(56), C.red, prog(t, qBel + 0.6, qBel + 2.2))
      finish(c, t, false); return false
    }
    if (t < qSec + 0.3) {
      paper(c, t)
      for (let i = 0; i < 20; i++) { const a = prog(t, qEv + 0.4 + i * 0.07, qEv + 0.7 + i * 0.07, 'back'); if (a > 0) medal(c, 300 + (i % 10) * 147, 400 + Math.floor(i / 10) * 230, 1.7 * a) }
      text(c, 'a gold medal for every driver', W / 2, 220, F.headI(72, 700), C.ink, { alpha: prog(t, qEv + 0.3, qEv + 0.8) })
      typeset(c, 'and a letter from President Coolidge', W / 2, 900, F.bodyI(56), C.ink2, prog(t, qLet - 0.1, qLet + 1.2))
      finish(c, t, false); return false
    }
    trail(c, t, { n: 7, bliz: 0.06, speed: 300, dawn: 0.8, stars: 0, wind: -60 })
    fade(c, 1 - prog(t, qSec + 0.3, qSec + 0.7), '233,227,214'); finish(c, t, false); return false
  }

  // =============================== 13. Balto and Togo ===============================
  function statue(c, x, y, s, col) {
    c.save(); c.translate(x, y); c.scale(s, s); c.fillStyle = '#17161a'; c.beginPath(); c.moveTo(-170, 0); c.lineTo(-150, -70); c.lineTo(-90, -120); c.lineTo(20, -136); c.lineTo(110, -110); c.lineTo(160, -50); c.lineTo(180, 0); c.closePath(); c.fill(); c.restore()
    dog(c, x - 10 * s, y - 130 * s, 2.3 * s, { col, head: -0.12 })
  }
  function s13(c, t, q, S) {
    const qBef = q('before the year') - 0.4, qStat = q('a bronze statue'), qThen = q('then the country') - 0.4, qEnd = q('he ended up'), qCh = q('the children of cleveland') - 0.4, qRaised = q('raised the money'), qHome = q('and brought him'), qTogo = q('and togo') - 0.4, qFive = q('togo ran five'), qRet = q('he retired') - 0.4, qSaid = q('seppala said')
    if (t < qBef + 0.3) {
      paper(c, t, C.paper2)
      c.save(); c.translate(960, 520 + (1 - prog(t, S.vis + 0.2, S.vis + 0.9, 'o')) * 900); c.rotate(-0.03); c.fillStyle = 'rgba(60,40,20,0.25)'; c.fillRect(-412, -392, 840, 820); c.fillStyle = '#f4ead2'; c.fillRect(-420, -400, 840, 820); c.strokeStyle = C.ink; c.lineWidth = 3; c.strokeRect(-420, -400, 840, 820)
      text(c, 'THE DAILY NEWS', 0, -330, F.sc(44), C.ink, { track: 10 }); rule(c, -380, 380, -306, C.ink, 1); text(c, 'BALTO', 0, -150, F.head(190, 900), C.ink, { track: 8 }); text(c, 'the dog that saved Nome', 0, -80, F.bodyI(50), C.red)
      dog(c, 0, 250, 3.4, { col: C.ink }); c.strokeStyle = C.ink; c.lineWidth = 3; c.beginPath(); c.moveTo(-300, 252); c.lineTo(300, 252); c.stroke()
      c.strokeStyle = C.ink3; c.lineWidth = 2.5; for (let i = 0; i < 4; i++) { c.beginPath(); c.moveTo(-360, 300 + i * 28); c.lineTo(360 - (i === 3 ? 200 : 0), 300 + i * 28); c.stroke() }
      c.restore(); finish(c, t, false); return false
    }
    if (t < qThen + 0.3) {
      // Central Park
      const g = c.createLinearGradient(0, 0, 0, 800); g.addColorStop(0, '#9fb0c4'); g.addColorStop(1, '#e9dcc0'); c.fillStyle = g; c.fillRect(0, 0, W, H)
      const r = rng(21); for (let i = 0; i < 16; i++) block(c, i * 130 - 40, 720, 110 + r() * 30, 220 + r() * 300, { fill: '#7f8ba0' })
      c.fillStyle = '#6b6658'; c.beginPath(); for (let i = 0; i < 14; i++) c.ellipse(i * 160, 720 + (i % 2) * 14, 130, 90, 0, 0, 7); c.fill()
      c.fillStyle = '#4a463c'; c.fillRect(0, 780, W, 300)
      const z = 1 + 0.06 * prog(t, qBef, qThen, 'l'); c.save(); zoom(c, 960, 600, z)
      statue(c, 960, 860, 1.5, '#7a5a22'); glow(c, 960, 560, 420, '246,199,112', 0.2 * prog(t, qStat, qStat + 0.6))
      for (const [x, o] of [[430, { lady: true }], [560, { hat: 'cap', h: 150 }], [1420, { hat: 'bowler', face: -1 }], [1540, { lady: true, face: -1 }], [1650, { hat: 'cap', h: 140, face: -1 }]]) person(c, x, 880, o.h || 250, { col: '#15171c', ...o })
      c.restore()
      text(c, 'Central Park, New York', W / 2, 170, F.headI(76, 700), C.ink, { alpha: prog(t, qStat - 0.4, qStat + 0.2), stroke: '#e9dcc0', sw: 8 })
      typeset(c, 'December 1925', W / 2, 240, F.bodyI(52), C.red, prog(t, qStat + 0.3, qStat + 1.2))
      fade(c, 1 - prog(t, qBef + 0.3, qBef + 0.7), '233,227,214'); finish(c, t, false); return false
    }
    if (t < qCh + 0.3) {
      // the sideshow
      c.fillStyle = '#08080b'; c.fillRect(0, 0, W, H); c.fillStyle = '#050506'; c.fillRect(0, 820, W, 260)
      c.save(); c.globalAlpha = 0.34; c.fillStyle = '#f0c868'; c.beginPath(); c.moveTo(1460, 0); c.lineTo(1660, 0); c.lineTo(1240, 1080); c.lineTo(560, 1080); c.closePath(); c.fill(); c.restore()
      c.strokeStyle = '#2a2a30'; c.lineWidth = 12; for (let i = 0; i < 13; i++) { c.beginPath(); c.moveTo(60 + i * 150, 0); c.lineTo(60 + i * 150, 820); c.stroke() }
      c.strokeStyle = '#3a3a40'; c.lineWidth = 5; c.setLineDash([14, 8]); c.beginPath(); c.moveTo(980, 760); c.quadraticCurveTo(1180, 840, 1390, 500); c.stroke(); c.setLineDash([]); c.fillStyle = '#3a3a40'; c.beginPath(); c.arc(1390, 500, 14, 0, 7); c.fill()
      dog(c, 960, 822, 3.0, { col: '#050506', lie: 1, head: 1 })
      typeset(c, 'a dime sideshow, Los Angeles', W / 2, 200, F.headI(66, 700), C.paper3, prog(t, qEnd + 0.4, qEnd + 1.8))
      fade(c, 1 - prog(t, qThen + 0.3, qThen + 0.8)); finish(c, t, true); return true
    }
    if (t < qTogo + 0.3) {
      paper(c, t); const gy = 820; c.strokeStyle = C.ink; c.lineWidth = 5; c.beginPath(); c.moveTo(0, gy); c.lineTo(W, gy); c.stroke(); hatch(c, k => k.rect(0, gy + 2, W, 260), { gap: 9, alpha: 0.25, angle: 0.03, box: [0, gy, W, 260] })
      for (let i = 0; i < 9; i++) { const up = 0.5 + 0.5 * Math.sin(t * 5 + i); person(c, 160 + i * 130, gy, 190 + (i % 3) * 30, { hat: i % 3 ? 'cap' : 'none', lady: i % 4 === 1, col: C.ink, arm: 0.9 * prog(t, qRaised - 0.4, qRaised + 0.2) + 0.1 * up }) }
      const rp = prog(t, qRaised - 0.4, qHome); for (let i = 0; i < 18; i++) { const a = clamp(rp * 3 - i * 0.1); if (a > 0 && a < 1) coin(c, 200 + (i * 61) % 1000, gy - 220 - a * 300, 16, 1 - a * 0.6) }
      const dp = prog(t, qHome - 0.3, qTogo, 'o'); dog(c, lerp(2200, 1480, dp), gy, 2.6, { col: C.ink, face: -1, run: dp * 30, stride: dp < 1 ? 1 : 0 })
      text(c, 'Cleveland, 1927', W / 2, 200, F.headI(84, 700), C.ink, { alpha: prog(t, qCh + 0.5, qCh + 1.0) })
      finish(c, t, false); return false
    }
    if (t < qRet + 0.3) {
      paper(c, t); const base = 880
      c.strokeStyle = C.ink; c.lineWidth = 4; c.beginPath(); c.moveTo(380, base); c.lineTo(1540, base); c.stroke()
      const a = prog(t, qFive - 0.2, qFive + 1.2, 'o')
      c.fillStyle = C.red2; c.fillRect(560, base - 261 * 2.3 * a, 260, 261 * 2.3 * a); c.fillStyle = C.ink; c.fillRect(1100, base - 53 * 2.3 * a, 260, 53 * 2.3 * a)
      text(c, 'TOGO', 690, base + 70, F.head(64, 900), C.red, { track: 6 }); text(c, 'BALTO', 1230, base + 70, F.head(64, 900), C.ink, { track: 6 })
      text(c, '261 miles', 690, base - 261 * 2.3 - 26, F.head(60, 900), C.red, { alpha: clamp(a * 2 - 1) }); text(c, '53 miles', 1230, base - 53 * 2.3 - 26, F.head(60, 900), C.ink, { alpha: clamp(a * 2 - 1) })
      finish(c, t, false); return false
    }
    // by the stove
    c.fillStyle = '#100d0b'; c.fillRect(0, 0, W, H); c.fillStyle = '#0a0807'; c.fillRect(0, 840, W, 240)
    glow(c, 500, 700, 800, '246,150,60', 0.35 * (0.9 + 0.1 * noise(t * 5, 1)))
    c.fillStyle = '#050404'; c.fillRect(400, 560, 200, 280); c.fillRect(470, 200, 44, 360); c.fillRect(380, 548, 240, 20); c.fillStyle = C.gold2; c.fillRect(440, 640, 120, 90); c.fillStyle = '#050404'; for (let i = 0; i < 5; i++) c.fillRect(452 + i * 24, 640, 8, 90)
    person(c, 1240, 842, 330, { hat: 'none', col: '#050404', seated: true, face: -1, bulk: 1.1 }); c.fillStyle = '#050404'; c.fillRect(1230, 700, 150, 16); c.fillRect(1360, 560, 16, 282); c.fillRect(1236, 700, 14, 142)
    dog(c, 860, 844, 2.5, { col: '#050404', lie: 1, face: -1 })
    typeset(c, 'Togo lived to be sixteen', W / 2, 200, F.headI(72, 700), C.paper2, prog(t, qRet + 0.9, qRet + 2.0), { shadow: '#000' })
    fade(c, 1 - prog(t, qRet + 0.3, qRet + 0.7)); finish(c, t, true); return true
  }

  // =============================== 14. the three words ===============================
  const icon = {
    paw: (c) => { c.beginPath(); c.ellipse(0, 22, 40, 34, 0, 0, 7); c.fill(); for (const [x, y, r] of [[-46, -22, 17], [-17, -48, 18], [17, -48, 18], [46, -22, 17]]) { c.beginPath(); c.ellipse(x, y, r * 0.85, r, x * 0.006, 0, 7); c.fill() } },
    swords: (c) => { for (const s of [-1, 1]) { c.save(); c.rotate(s * 0.78); c.fillRect(-6, -84, 12, 126); c.beginPath(); c.moveTo(-6, -84); c.lineTo(0, -102); c.lineTo(6, -84); c.fill(); c.fillRect(-28, 36, 56, 10); c.fillRect(-5, 46, 10, 30); c.beginPath(); c.arc(0, 82, 9, 0, 7); c.fill(); c.restore() } },
    crash: (c) => { c.lineWidth = 11; c.lineJoin = 'round'; c.lineCap = 'round'; c.beginPath(); c.moveTo(-84, 20); c.lineTo(-44, -30); c.lineTo(-14, -8); c.lineTo(16, -64); c.lineTo(44, 44); c.lineTo(84, 70); c.stroke(); c.beginPath(); c.moveTo(84, 70); c.lineTo(52, 72); c.lineTo(76, 44); c.closePath(); c.fill(); c.stroke() },
  }
  function s14(c, t, q, S) {
    const qB = q('balto is in'), qT = q('togo is in'), qSt = q('and the statue') - 0.4, qUn = q('under it are'), qE = q('endurance'), qFi = q('fidelity'), qI = q('intelligence'), qSub = q('subscribe') - 0.35, qAn = q('animal facts'), qBat = q('historys greatest'), qCol = q('worlds craziest')
    if (t < qSt + 0.3) {
      c.fillStyle = '#0d0e14'; c.fillRect(0, 0, W, H); c.fillStyle = '#08090d'; c.fillRect(0, 860, W, 220)
      ;[[560, 'BALTO', 'Cleveland', qB], [1360, 'TOGO', 'Alaska', qT]].forEach(([x, nm, pl, at], i) => {
        const a = prog(t, at - 0.3, at + 0.3); if (a <= 0) return; c.save(); c.globalAlpha = a
        glow(c, x, 560, 520, '246,199,112', 0.3); c.fillStyle = '#e9dcc0'; c.fillRect(x - 260, 380, 520, 400); c.fillStyle = '#17161a'; c.fillRect(x - 280, 780, 560, 90); c.strokeStyle = '#17161a'; c.lineWidth = 12; c.strokeRect(x - 260, 380, 520, 400)
        dog(c, x, 772, i ? 2.5 : 2.9, { col: '#17161a', face: i ? -1 : 1 })
        text(c, nm, x, 842, F.sc(40), C.gold2, { track: 10 }); text(c, pl, x, 320, F.headI(64, 700), C.paper); c.restore()
      })
      finish(c, t, true); return true
    }
    if (t < qSub + 0.3) {
      const g = c.createLinearGradient(0, 0, 0, 800); g.addColorStop(0, '#1b2238'); g.addColorStop(1, '#6b5a50'); c.fillStyle = g; c.fillRect(0, 0, W, H)
      const r = rng(21); for (let i = 0; i < 16; i++) block(c, i * 130 - 40, 760, 110 + r() * 30, 220 + r() * 300, { fill: '#141826', win: C.gold2, dens: 0.3 })
      c.fillStyle = '#0c0f12'; c.beginPath(); for (let i = 0; i < 14; i++) c.ellipse(i * 160, 770 + (i % 2) * 14, 130, 90, 0, 0, 7); c.fill(); c.fillRect(0, 800, W, 300)
      const z = 1 + 0.08 * prog(t, qSt, qSub, 'l'); c.save(); zoom(c, 960, 620, z); statue(c, 520, 900, 1.6, '#0a0b0e'); c.restore()
      { const g2 = c.createLinearGradient(700, 0, 1100, 0); g2.addColorStop(0, 'rgba(8,9,14,0)'); g2.addColorStop(1, 'rgba(8,9,14,0.82)'); c.fillStyle = g2; c.fillRect(700, 0, 1220, H) }
      ;[['ENDURANCE', qE], ['FIDELITY', qFi], ['INTELLIGENCE', qI]].forEach(([w, at], i) => text(c, w, 1320, 420 + i * 130, F.head(96, 900), C.gold2, { track: 12, alpha: prog(t, at - 0.1, at + 0.4), shadow: '#000', blur: 30 }))
      fade(c, 1 - prog(t, qSt + 0.3, qSt + 0.7) + prog(t, qSub - 0.1, qSub + 0.3)); finish(c, t, true); return true
    }
    c.fillStyle = '#0a0c14'; c.fillRect(0, 0, W, H); glow(c, W / 2, 480, 1000, '60,80,150', 0.18)
    const a = qSub + 0.3, z = 1 + 0.03 * prog(t, a, S.out, 'l')
    c.save(); zoom(c, W / 2, H / 2, z)
    c.save(); c.globalAlpha = prog(t, a, a + 0.6); dog(c, W / 2, 232, 1.9, { col: C.paper2, run: t * 8, stride: 1 }); c.restore()
    rule(c, 520, 1400, 250, C.paper3, prog(t, a, a + 0.8))
    text(c, 'SUBSCRIBE', W / 2, 400, F.head(150, 900), C.paper, { track: 16, alpha: prog(t, a + 0.1, a + 0.6) })
    text(c, 'and we’ll tell you more', W / 2, 470, F.bodyI(50), C.paper2, { alpha: prog(t, a + 0.6, a + 1.2) })
    const items = [['paw', 'Animal facts', qAn], ['swords', 'History’s greatest battles', qBat], ['crash', 'The world’s craziest financial collapses', qCol]]
    items.forEach(([ic, label, at], i) => {
      const p = prog(t, at - 0.1, at + 0.3, 'back'), x = 420 + i * 540; if (p <= 0) return
      c.save(); c.translate(x, 680); c.scale(p, p); c.strokeStyle = C.gold; c.lineWidth = 4; c.beginPath(); c.arc(0, 0, 120, 0, 7); c.stroke()
      c.fillStyle = i === 0 ? C.gold2 : C.paper; c.strokeStyle = i === 2 ? C.red2 : C.paper; if (i === 2) c.fillStyle = C.red2; icon[ic](c); c.restore()
      const ws = label.split(' '), l1 = ws.length > 3 ? ws.slice(0, 3).join(' ') : label, l2 = ws.length > 3 ? ws.slice(3).join(' ') : ''
      text(c, l1, x, 870, F.body(40), C.paper, { alpha: clamp(p) }); if (l2) text(c, l2, x, 918, F.body(40), C.paper, { alpha: clamp(p) })
    })
    c.restore()
    fade(c, 1 - prog(t, a, a + 0.4)); finish(c, t, true); return true
  }

  window.SCENES.push(s8, s9, s10, s11, s12, s13, s14)
})()
