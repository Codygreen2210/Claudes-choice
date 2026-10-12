// scB.js: scenes 8-13 of The Champawat Tiger: Phungar, the plan, the shot, the count, after, today.
(function () {
  const { clamp, lerp, EZ, prog, bump, rng, noise, track, mix } = K
  const { W, H, C, F, paper, finish, hatch, text, typeset, rule, person, glow, tw } = L
  const { night, eyes } = T2
  const { INK, RED, GOLD, tiger, ridges, terraces, house, deodar, forest, villager, drummer, corbett, sepoy, gorge, brush, skull, marker, camera } = CW
  const { label, ground, zoom, beaters, village } = CWA

  // =============================== 8. Phungar ===============================
  function s8(c, t, q, S) {
    const qTrail = q('corbett picked up') - 0.3, qRav = q('it went down') - 0.3, qFound = q('he found what') - 0.3, qEarth = q('a little earth') - 0.3, qThere = q('she was right there'), qFire = q('he swung his rifle'), qDark = q('it was getting dark') - 0.3
    if (t < qTrail) {
      village(c, t, { seed: 12 })
      villager(c, lerp(700, 1500, prog(t, S.start, qTrail, 'l')), 980, 200, { lady: true, load: 1 })
      label(c, 'Premka Devi, 16', W / 2, 150, prog(t, S.start + 1.6, S.start + 2.4))
      finish(c, t, false); return false
    }
    if (t < qFound) {
      ridges(c, t, { d: 0.85, seed: 13 }); forest(c, -40, W + 40, 1060, 1.3, { col: '#1c160f', seed: 9 })
      brush(c, 0, W, 1080, 200, '#140f0b', 5)
      corbett(c, lerp(300, 1100, prog(t, qTrail, qFound, 'l')), 1010, 240, { walk: t * 3, stride: 0.6, lean: 0.12, aim: 0.2 })
      finish(c, t, false); return false
    }
    // the ravine: Corbett kneels; the bank above him; earth trickles; then gold above
    gorge(c, t, { d: 0.6 })
    const up = prog(t, qThere - 0.2, qThere + 0.4)
    corbett(c, 900, 1000, 230, { lean: 0.35 * (1 - up), aim: up, kick: bump(t, qFire + 1.0, 0.25) * -0.3 + bump(t, qFire + 1.5, 0.25) * -0.3 })
    if (t > qEarth) { const r = rng(3); c.fillStyle = '#3a2e22'; for (let k = 0; k < 14; k++) { const tt = (t - qEarth - k * 0.12); if (tt > 0) { c.beginPath(); c.arc(1180 + r() * 40, 420 + tt * 500 % 560, 4, 0, 7); c.fill() } } }
    if (t > qThere - 0.4 && t < qFire + 1.2) { c.save(); c.globalAlpha = prog(t, qThere - 0.4, qThere); tiger(c, 1240, 440, 1.7, { face: -1, crouch: 0.9, head: 0.4, eye: true }); c.restore() }
    if (t > qFire + 1.0 && t < qFire + 2.4) { const a = bump(t, qFire + 1.0, 0.18) + bump(t, qFire + 1.5, 0.18); glow(c, 1020, 760, 240, '246,199,112', a) }
    if (t > qDark) { c.fillStyle = `rgba(10,10,14,${prog(t, qDark, qDark + 3) * 0.7})`; c.fillRect(0, 0, W, H) }
    const dk = t > qDark + 1.5; finish(c, t, dk); return dk
  }

  // =============================== 9. the plan ===============================
  function s9(c, t, q, S) {
    const qRest = q('she would not have gone') - 0.3, qTah = q('the tahsildar went') - 0.3, q298 = q('298 of them'), qSpread = q('they would spread out') - 0.3, qDriven = q('a tiger driven')
    paper(c, t)
    // the plan drawn as a section through the gorge
    c.fillStyle = '#b6a27a'; c.beginPath(); c.moveTo(0, 300); c.bezierCurveTo(500, 320, 700, 800, 960, 860); c.bezierCurveTo(1220, 800, 1420, 320, 1920, 300); c.lineTo(1920, 1080); c.lineTo(0, 1080); c.closePath(); c.fill()
    c.fillStyle = '#6b7a80'; c.fillRect(860, 850, 200, 20)
    label(c, 'the Champa gorge', W / 2, 160, prog(t, qRest + 1.2, qRest + 2))
    if (t > qRest) { c.save(); c.globalAlpha = prog(t, qRest + 2.4, qRest + 3); tiger(c, 760, 760, 0.9, { crouch: 0.3 }); c.restore() }
    const men = Math.floor(lerp(0, 60, prog(t, qTah + 0.6, q298 + 0.8)))
    for (let k = 0; k < men; k++) { const u = k / 59, side = k % 2, x = side ? lerp(1920, 1300, u) : lerp(0, 620, u), y = side ? lerp(300, 520, u) : lerp(300, 520, u); villager(c, x, y - 4, 40, { face: side ? -1 : 1 }) }
    if (t > q298 - 0.3) typeset(c, '298', W / 2, 280, F.head(130, 900), C.red, prog(t, q298 - 0.3, q298 + 0.5), { stroke: C.paper, sw: 10 })
    if (t > qSpread) { const a = prog(t, qSpread + 1.4, qSpread + 2.2); c.strokeStyle = C.red; c.globalAlpha = a; c.lineWidth = 6; c.setLineDash([16, 12]); c.beginPath(); c.moveTo(300, 440); c.quadraticCurveTo(600, 700, 820, 820); c.moveTo(1620, 440); c.quadraticCurveTo(1320, 700, 1100, 820); c.stroke(); c.setLineDash([]); c.globalAlpha = 1 }
    if (t > qDriven) { corbett(c, 1000, 862, 90, { aim: 0.3 }); text(c, 'Corbett', 1000, 950, F.headI(40), INK, { alpha: prog(t, qDriven + 2.4, qDriven + 3) }) }
    finish(c, t, false); return false
  }

  // =============================== 10. the shot ===============================
  function s10(c, t, q, S) {
    const qLong = q('for a long time') - 0.3, qOut = q('then she came out'), qF1 = q('corbett fired'), qF2 = q('he fired again'), qEmpty = q('then his rifle was empty'), qTah = q('the tahsildar had a gun') - 0.2, qLast = q('she was 20 feet away'), qOver = q('it was over')
    gorge(c, t, { d: 1 })
    beaters(c, t, 40, 620, 200, 520, 12); beaters(c, t, 1300, 1880, 520, 200, 12)
    brush(c, 0, 760, 905, 90, '#3a2e22', 4)
    const run = prog(t, qOut, qF1 + 0.2, 'l'), adv = prog(t, qTah + 1.4, qLast + 0.6, 'l'), down = prog(t, qLast + 1.2, qLast + 2.0, 'i')
    const tx = lerp(420, 760, run) + lerp(0, 300, adv), hitk = bump(t, qF1 + 0.6, 0.35) + bump(t, qF2 + 0.6, 0.35)
    if (t > qOut - 0.4) { if (down < 1) tiger(c, tx, 1000, 2.2, { walk: t * 6, stride: run < 1 || adv > 0 ? 0.9 : 0.2, head: -0.1 + hitk * 0.3, rot: down * 0.3 }); else tiger(c, tx + 60, 1010, 2.2, { down: true }) }
    const cx = lerp(1360, 1230, prog(t, qTah + 0.8, qLast, 'io'))
    corbett(c, cx, 1010, 290, { face: -1, aim: t > qF1 - 0.6 && t < qEmpty + 0.4 ? 1 : t > qLast - 0.8 ? 1 : 0.2, walk: t * 4, stride: t > qTah + 0.8 && t < qLast - 0.8 ? 0.8 : 0, kick: (bump(t, qF1 + 0.5, 0.2) + bump(t, qF2 + 0.5, 0.2) + bump(t, qLast + 0.8, 0.2)) * -0.35 })
    if (t > qTah && t < qLast) villager(c, 1560, 1010, 260, { face: -1, arm: 0.6 })
    for (const at of [qF1 + 0.5, qF2 + 0.5, qLast + 0.8]) { const a = bump(t, at, 0.2); if (a > 0) glow(c, cx - 140, 880, 260, '246,199,112', a) }
    if (t > qOver) { c.fillStyle = `rgba(240,228,204,${prog(t, qOver, qOver + 1.2) * 0.35})`; c.fillRect(0, 0, W, H) }
    finish(c, t, false); return false
  }

  // =============================== 11. the count ===============================
  function s11(c, t, q, S) {
    const qLook = q('corbett looked at') - 0.3, qNobody = q('nobody knows exactly') - 0.3, q436 = q('is 436'), qRec = q('it is still listed') - 0.3, qMark = q('today a small marker') - 0.3
    if (t < qNobody) {
      gorge(c, t, { d: 1 })
      tiger(c, 900, 1010, 2.2, { down: true })
      for (let k = 0; k < 7; k++) villager(c, 300 + k * 90 + (k > 3 ? 900 : 0), 1010, 210, { face: k > 3 ? -1 : 1 })
      corbett(c, 1150, 1010, 250, { face: -1, lean: 0.3 })
      finish(c, t, false); return false
    }
    if (t < qMark) {
      paper(c, t)
      const n = Math.round(lerp(0, 436, prog(t, q436 - 1.6, q436 + 0.2, 'o')))
      typeset(c, n ? String(n) : '?', W / 2, 560, F.head(300, 900), C.red, 1, { track: 10 })
      text(c, 'the most people killed by a single tiger on record', W / 2, 700, F.bodyI(52), INK, { alpha: prog(t, qRec + 0.4, qRec + 1.2) })
      finish(c, t, false); return false
    }
    ridges(c, t, { d: 1, seed: 21 })
    c.fillStyle = '#5f523d'; c.fillRect(0, 960, W, 120); c.fillStyle = '#3a312a'; c.fillRect(0, 980, W, 30)
    marker(c, 960, 960, 1.2)
    label(c, 'near Lohaghat', W / 2, 150, prog(t, qMark + 1.4, qMark + 2.2))
    finish(c, t, false); return false
  }

  // =============================== 12. after ===============================
  function s12(c, t, q, S) {
    const qOver = q('but over the next') - 0.3, qChanged = q('and slowly') - 0.3, qBook = q('in 1944') - 0.3, qCam = q('he traded his rifle') - 0.3, qPark = q('after he died') - 0.3
    if (t < qBook) {
      if (t < qOver) { paper(c, t); ground(c, 900); T2.train(c, lerp(-400, 900, prog(t, S.start, qOver, 'o')), 900, 1.2, t, {}); finish(c, t, false); return false }
      ridges(c, t, { d: 1, seed: 30 + Math.floor((t - qOver) / 2.5) }); forest(c, -40, W + 40, 1040, 1.0, { col: '#2a2219', seed: 3 + Math.floor((t - qOver) / 2.5) })
      corbett(c, 900, 1000, 280, { walk: t * 4, stride: 0.8 })
      label(c, '30 years in the hills', W / 2, 150, prog(t, qOver + 0.6, qOver + 1.4) * (1 - prog(t, qChanged - 0.3, qChanged)))
      finish(c, t, false); return false
    }
    if (t < qCam) {
      paper(c, t)
      c.fillStyle = INK; c.fillRect(760, 300, 400, 520); c.fillStyle = C.paper2; c.fillRect(780, 320, 360, 480)
      text(c, 'MAN-EATERS', 960, 480, F.head(56, 900), INK); text(c, 'OF KUMAON', 960, 550, F.head(56, 900), INK); text(c, 'Jim Corbett', 960, 680, F.headI(40), C.red); text(c, '1944', 960, 740, F.body(36), INK)
      finish(c, t, false); return false
    }
    ridges(c, t, { d: 1, seed: 40 })
    forest(c, -40, W + 40, 1040, 1.0, { col: '#2a2219', seed: 12 })
    camera(c, 760, 1000, 1.4); corbett(c, 640, 1000, 260, { arm: 0.5 })
    tiger(c, lerp(1500, 1350, prog(t, qCam, qCam + 6, 'o')), 1000, 1.5, { face: -1, walk: t * 2, stride: 0.4 })
    if (t > qPark) label(c, 'Corbett National Park', W / 2, 150, prog(t, qPark + 1.6, qPark + 2.4), { font: F.head(80, 900) })
    finish(c, t, false); return false
  }

  // =============================== 13. today ===============================
  function s13(c, t, q, S) {
    const qTrue = q('and it is still true') - 0.3, qWrote = q('corbett wrote') - 0.3, qNot = q('this one did not') - 0.3, qBullet = q('somebodys bullet') - 0.3, qSub = q('subscribe') - 0.4
    if (t < qTrue) {
      ridges(c, t, { d: 1, seed: 50 })
      for (let k = 0; k < 3; k++) tiger(c, 400 + k * 520, 1000 - (k % 2) * 40, 1.2 + (k % 2) * 0.2, { walk: t * 3 + k, stride: 0.5, seed: k + 2 })
      typeset(c, '3,000+', W / 2, 260, F.head(130, 900), INK, prog(t, S.start + 4, S.start + 5), { stroke: C.paper, sw: 10 })
      text(c, 'wild tigers in India', W / 2, 330, F.bodyI(50), C.red, { alpha: prog(t, S.start + 5, S.start + 5.6) })
      finish(c, t, false); return false
    }
    paper(c, t, '#e8dcc0')
    if (t < qBullet) {
      skull(c, 900, 600, 1.4, { hl: true })
      if (t > qWrote) { typeset(c, '9 out of 10: wounded', W / 2, 920, F.head(70, 900), C.red, prog(t, qWrote + 1.6, qWrote + 2.6)); text(c, 'the tenth: too old', W / 2, 1000, F.headI(52), INK, { alpha: prog(t, qWrote + 3.4, qWrote + 4) }) }
      finish(c, t, false); return false
    }
    if (t < qSub) {
      tiger(c, 960, 860, 2.4, { face: -1, walk: 0, stride: 0, head: 0.1 })
      text(c, 'Somebody’s bullet made that choice for her.', W / 2, 220, F.headI(62, 700), INK, { alpha: prog(t, qBullet + 0.6, qBullet + 1.4) })
      finish(c, t, false); return false
    }
    text(c, 'HISTORY UNFOLDZ', W / 2, 470, F.head(120, 900), INK, { alpha: prog(t, qSub, qSub + 0.8), track: 12 })
    rule(c, 560, 1360, 520, INK, prog(t, qSub + 0.3, qSub + 1.2))
    text(c, 'Subscribe', W / 2, 640, F.head(90, 900), C.red, { alpha: prog(t, qSub + 0.4, qSub + 1.2) })
    text(c, 'animal facts · history’s greatest battles · the craziest financial collapses', W / 2, 740, F.bodyI(44), INK, { alpha: prog(t, qSub + 2.2, qSub + 3.2) })
    finish(c, t, false); return false
  }

  window.SCENES.push(s8, s9, s10, s11, s12, s13)
})()
