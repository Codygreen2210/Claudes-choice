// scC.js: scenes 7-9. The second lion, the count, and where they are now.
(function () {
  const { clamp, lerp, EZ, prog, bump, rng, noise, track } = K
  const { W, H, C, F, layer, paper, finish, hatch, rr, text, typeset, rule, person, crowd, glow, tw, key } = L
  const { ghost, N, lion, lionDown, eyes, night, ground, acacia, thorn, tent, fire, train, rails, patterson, turban } = T2
  const { cam, fade, plain, bridge, INK, WORK, calendar } = TS
  const PAPERF = '238,226,200'

  // =============================== 7. the second lion ===============================
  function rifle(c, x, y, s, col) { c.save(); c.translate(x, y); c.scale(s, s); c.rotate(-0.12); c.fillStyle = col; c.fillRect(-90, -4, 150, 8); c.beginPath(); c.moveTo(-90, -6); c.lineTo(-150, 6); c.lineTo(-146, 22); c.lineTo(-88, 8); c.closePath(); c.fill(); c.fillRect(-70, 4, 8, 16); c.restore() }
  function s7(c, t, q, S) {
    const q20 = q('it took twenty'), q3 = q('three rifles'), q9 = q('and nine shots'), q6 = q('six of them'), q29 = q('on the twenty') - 0.35, qWrote = q('patterson wrote'), qStill = q('still trying'), qBack = q('the men came back') - 0.4, qFeb = q('the bridge was')
    if (t < q29 + 0.3) {
      const z = 1 + 0.05 * prog(t, S.vis, q29, 'l')
      c.save(); cam(c, W / 2, H / 2, z)
      night(c, t, { moon: [420, 300, 150] }); glow(c, 420, 300, 800, N.blue, 0.2)
      c.fillStyle = INK; c.beginPath(); c.moveTo(-100, 860); for (let x = -100; x <= W + 100; x += 60) c.lineTo(x, 820 - 50 * Math.sin((x + 900) * 0.0015)); c.lineTo(W + 100, H + 50); c.lineTo(-100, H + 50); c.closePath(); c.fill()
      const lx = track(t, [[S.vis, 150], [q29, 760, 'l']]); lion(c, lx, 826 - 50 * Math.sin((lx + 900) * 0.0015), 2.8, { walk: lx * 0.03, stride: 1, eye: true, col: INK, tail: t * 2, head: 0.1 })
      c.restore()
      text(c, 'ONE LEFT', 1360, 200, F.head(110, 900), C.paper, { track: 10, alpha: prog(t, S.start - 0.1, S.start + 0.4), shadow: '#000', blur: 30 })
      c.save(); c.translate(-190, 0)
      // twenty days
      const d = prog(t, q20, q3 - 0.1)
      for (let i = 0; i < 20; i++) { const on = clamp(d * 20 - i); c.fillStyle = `rgba(238,226,200,${0.18 + 0.82 * on})`; rr(c, 1060 + (i % 10) * 62, 270 + Math.floor(i / 10) * 62, 50, 50, 4); c.fill() }
      text(c, '20 more days', 1700, 340, F.bodyI(46), C.paper2, { alpha: prog(t, q20 + 0.3, q20 + 0.8), align: 'left', shadow: '#000' })
      for (let i = 0; i < 3; i++) { const a = prog(t, q3 + i * 0.18, q3 + 0.3 + i * 0.18, 'back'); if (a > 0) { c.save(); c.globalAlpha = clamp(a); rifle(c, 1260 + i * 200, 470 + i * 6, 0.9, C.paper); c.restore() } }
      text(c, '3 rifles', 1700, 486, F.bodyI(46), C.paper2, { alpha: prog(t, q3 + 0.3, q3 + 0.8), align: 'left', shadow: '#000' })
      for (let i = 0; i < 9; i++) { const a = prog(t, q9 + i * 0.07, q9 + 0.2 + i * 0.07, 'back'); if (a <= 0) continue; const hit = i < 6 ? prog(t, q6 + i * 0.08, q6 + 0.2 + i * 0.08) : 0; c.save(); c.translate(1090 + i * 66, 590); c.scale(clamp(a), clamp(a)); c.strokeStyle = C.paper; c.lineWidth = 4; c.beginPath(); c.arc(0, 0, 22, 0, 7); c.stroke(); if (hit > 0) { c.fillStyle = C.red2; c.globalAlpha = hit; c.beginPath(); c.arc(0, 0, 22, 0, 7); c.fill() } c.restore() }
      text(c, t > q6 ? '9 shots · 6 hit' : '9 shots', 1700, 604, F.bodyI(46), C.paper2, { alpha: prog(t, q9 + 0.5, q9 + 1.0), align: 'left', shadow: '#000' })
      c.restore()
      fade(c, prog(t, q29 - 0.1, q29 + 0.3)); finish(c, t, true); return true
    }
    if (t < qBack + 0.3) {
      // it goes down, still fighting
      const z = 1.05 + 0.1 * prog(t, q29, qBack, 'l')
      c.save(); cam(c, 1000, 600, z)
      plain(c, t, { moon: [1560, 190, 56], hy: 700, trees: 3, seed: 31 })
      acacia(c, 330, 880, 1.7, INK, 8)
      const still = prog(t, qStill + 1.0, qStill + 2.6)
      // the fallen branch
      c.strokeStyle = INK; c.lineWidth = 16; c.lineCap = 'round'; c.beginPath(); c.moveTo(1150, 846); c.quadraticCurveTo(1300, 800, 1480, 860); c.stroke(); c.lineWidth = 8; c.beginPath(); c.moveTo(1330, 818); c.lineTo(1380, 760); c.moveTo(1400, 834); c.lineTo(1470, 800); c.stroke()
      const gnaw = (1 - still) * 0.16 * Math.sin(t * 9) * prog(t, qWrote, qWrote + 0.6)
      lionDown(c, 1010, 880, 3.2, { col: INK, head: -0.1 + gnaw })
      if (still < 1) eyes(c, 1166, 834, 0.0001, 0)
      c.fillStyle = `rgba(255,215,106,${1 - still})`; c.beginPath(); c.ellipse(1163, 826, 7, 4.5, 0.2, 0, 7); c.fill()
      c.restore()
      calendar(c, 250, 250, 'DECEMBER', 29, '1898', prog(t, q29 + 0.4, q29 + 0.9) * (1 - prog(t, qBack - 0.4, qBack)), 0.9)
      text(c, '...still trying to get to him', W / 2 + 120, 190, F.headI(64, 700), C.paper, { alpha: prog(t, qStill, qStill + 0.5) * (1 - prog(t, qBack - 0.4, qBack)), shadow: '#000', blur: 30 })
      fade(c, 1 - prog(t, q29 + 0.3, q29 + 0.8) + prog(t, qBack - 0.1, qBack + 0.3)); finish(c, t, true); return true
    }
    // the men come back, the bridge is finished
    paper(c, t)
    const build = 0.55 + 1.45 * prog(t, qBack + 0.3, qFeb + 1.2, 'io')
    const z = 0.84 + 0.05 * prog(t, qBack, S.out, 'l')
    c.save(); cam(c, 960, 640, z)
    bridge(c, t, build)
    WORK.slice(0, 22).forEach((p, i) => { const inn = prog(t, qBack + 0.3 + i * 0.04, qBack + 1.6 + i * 0.04, 'o'), home = i % 2 ? lerp(60, 600, p.jit) : lerp(1340, 1900, p.jit); turban(c, lerp(i % 2 ? -900 : 2900, home, inn), 596, p.h * 0.5, { walk: t * 5 * p.sp + p.ph, stride: inn < 1 ? 1 : 0.4, face: i % 2 ? 1 : -1, bulk: p.bulk, arm: i % 3 === 0 ? 0.3 + 0.2 * Math.sin(t * 6 + i) : 0 }) })
    if (build >= 2) { const tx = lerp(-700, 2100, prog(t, qFeb + 1.2, S.out + 1.5, 'l')); train(c, tx, 597, 1.0, t, { wagons: 3, roll: tx * 0.03, speed: 0.5 }) }
    c.restore()
    text(c, 'The men came back.', W / 2, 120, F.headI(70, 700), C.ink, { alpha: prog(t, qBack + 0.4, qBack + 0.9) * (1 - prog(t, qFeb - 0.2, qFeb + 0.2)) })
    text(c, 'FEBRUARY 1899', W / 2, 110, F.head(90, 900), C.ink, { track: 10, alpha: prog(t, qFeb + 0.2, qFeb + 0.7) }); text(c, 'the bridge is finished', W / 2, 176, F.bodyI(52), C.red, { alpha: prog(t, qFeb + 0.6, qFeb + 1.1) })
    fade(c, 1 - prog(t, qBack + 0.3, qBack + 0.7)); finish(c, t, false); return false
  }

  // =============================== 8. the count ===============================
  function card(c, x, y, w, h, rot = 0, fill = C.paper) { c.save(); c.translate(x, y); c.rotate(rot); c.fillStyle = 'rgba(0,0,0,0.2)'; c.fillRect(-w / 2 + 10, -h / 2 + 12, w, h); c.fillStyle = fill; c.strokeStyle = C.ink; c.lineWidth = 4; c.fillRect(-w / 2, -h / 2, w, h); c.strokeRect(-w / 2, -h / 2, w, h); c.lineWidth = 1.5; c.strokeRect(-w / 2 + 12, -h / 2 + 12, w - 24, h - 24) }
  function s8(c, t, q, S) {
    const qRail = q('the railways records'), q28 = q('say 28'), qPat = q('patterson years later'), q135 = q('said 135'), qCent = q('for a century') - 0.35, q2009 = q('then in 2009'), qWhat = q('what an animal'), qBones = q('in its bones'), qHair = q('and in its hair'), qBoth = q('they tested'), qAns = q('their answer') - 0.35, q35 = q('about 35'), q11 = q('one lion ate'), q24 = q('the other'), qOnly = q('though that only'), qNot = q('not everyone')
    paper(c, t)
    if (t < qCent + 0.3) {
      const z = 1 + 0.04 * prog(t, S.vis, qCent, 'l')
      c.save(); cam(c, W / 2, H / 2, z)
      text(c, 'How many?', W / 2, 170, F.headI(110, 700), C.ink, { alpha: prog(t, S.start, S.start + 0.5) })
      const a1 = prog(t, qRail - 0.2, qRail + 0.4, 'back'), a2 = prog(t, qPat - 0.2, qPat + 0.4, 'back')
      if (a1 > 0) { c.save(); c.translate(540, 600); c.scale(clamp(a1), clamp(a1)); card(c, 0, 0, 560, 620, -0.03); text(c, 'UGANDA RAILWAY', 0, -220, F.sc(40), C.ink, { track: 5 }); text(c, 'the company’s records', 0, -170, F.bodyI(36), C.ink2); rule(c, -200, 200, -140, C.ink); text(c, '28', 0, 120, F.head(330, 900), C.ink, { alpha: prog(t, q28 - 0.1, q28 + 0.3) }); c.restore(); c.restore() }
      if (a2 > 0) { c.save(); c.translate(1380, 600); c.scale(clamp(a2), clamp(a2)); card(c, 0, 0, 560, 620, 0.03, '#5a2a1e'); text(c, 'J. H. PATTERSON', 0, -220, F.sc(40), C.gold2, { track: 5 }); text(c, 'years later', 0, -170, F.bodyI(36), C.paper2); c.strokeStyle = C.gold; c.lineWidth = 3; c.beginPath(); c.moveTo(-200, -140); c.lineTo(200, -140); c.stroke(); text(c, '135', 0, 120, F.head(280, 900), C.gold2, { alpha: prog(t, q135 - 0.1, q135 + 0.3) }); c.restore(); c.restore() }
      c.restore()
      fade(c, prog(t, qCent - 0.1, qCent + 0.3), PAPERF); finish(c, t, false); return false
    }
    if (t < qAns + 0.3) {
      // asking the lions
      const z = 1 + 0.04 * prog(t, qCent, qAns, 'l')
      c.save(); cam(c, W / 2, H / 2, z)
      text(c, '2009', 330, 230, F.head(150, 900), C.red, { alpha: prog(t, q2009, q2009 + 0.4) })
      text(c, 'a way to ask the lions', 330, 300, F.bodyI(46), C.ink2, { alpha: prog(t, q2009 + 0.6, q2009 + 1.1) })
      lion(c, 560, 860, 3.6, { col: C.ink, tail: t * 1.2, head: 0.05 })
      c.strokeStyle = C.ink; c.lineWidth = 5; c.beginPath(); c.moveTo(120, 862); c.lineTo(1000, 862); c.stroke()
      // bone and hair, called out
      const ba = prog(t, qBones - 0.2, qBones + 0.3), ha = prog(t, qHair - 0.2, qHair + 0.3)
      const call = (x0, y0, x1, y1, label, a, k) => { if (a <= 0) return; c.save(); c.globalAlpha = a; c.strokeStyle = C.red; c.lineWidth = 4; c.beginPath(); c.arc(x0, y0, 26 + 4 * Math.sin(t * 5 + k), 0, 7); c.stroke(); c.beginPath(); c.moveTo(x0 + 22, y0 - 14); c.lineTo(x1, y1); c.stroke()
        c.fillStyle = C.paper; c.strokeStyle = C.ink; rr(c, x1, y1 - 80, 620, 160, 6); c.fill(); c.stroke(); text(c, label, x1 + 30, y1 - 30, F.sc(34), C.ink, { align: 'left', track: 4 })
        // its signature: a row of bars that settle
        const r = rng(k * 9 + 2); for (let i = 0; i < 22; i++) { const target = 0.2 + 0.8 * Math.abs(Math.sin(i * (k ? 0.9 : 0.6) + k)), settle = prog(t, (k ? qHair : qBones) + 0.2 + i * 0.03, (k ? qHair : qBones) + 0.9 + i * 0.03, 'o'), hgt = 70 * lerp(r(), target, settle); c.fillStyle = i % 5 === 2 ? C.red : C.ink; c.fillRect(x1 + 30 + i * 25, y1 + 60 - hgt, 16, hgt) }
        c.restore() }
      call(650, 800, 1080, 470, 'BONE', ba, 0); call(420, 620, 1080, 700, 'HAIR', ha, 1)
      text(c, 'What it ate leaves a chemical signature', 1390, 300, F.headI(50, 700), C.ink, { alpha: prog(t, qWhat + 0.4, qWhat + 1.0) })
      c.restore()
      fade(c, 1 - prog(t, qCent + 0.3, qCent + 0.7) + prog(t, qAns - 0.1, qAns + 0.3), PAPERF); finish(c, t, false); return false
    }
    // the answer, as people
    const z = 1 + 0.04 * prog(t, qAns, S.out, 'l')
    c.save(); cam(c, W / 2, H / 2 + 10, z)
    const fig = (x, y, col, a, dashed) => { c.save(); c.globalAlpha = a; if (dashed) { c.strokeStyle = col; c.lineWidth = 2.5; c.setLineDash([5, 5]); c.beginPath(); c.arc(x, y - 92, 9, 0, 7); c.stroke(); c.strokeRect(x - 12, y - 80, 24, 78) } else person(c, x, y, 104, { hat: 'none', col }); c.restore() }
    for (let i = 0; i < 35; i++) {
      const gx = 330 + (i % 12) * 62, gy = 430 + Math.floor(i / 12) * 140
      const first = i < 11, on = first ? prog(t, q11 - 0.2 + i * 0.05, q11 + 0.1 + i * 0.05) : prog(t, q24 - 0.2 + (i - 11) * 0.03, q24 + 0.1 + (i - 11) * 0.03)
      const base = prog(t, q35 - 0.3 + i * 0.015, q35 + i * 0.015)
      fig(gx, gy, on > 0 ? (first ? C.red : C.ink) : C.ink3, base * (on > 0 ? 1 : 0.55))
    }
    // the ones nobody can count
    const more = prog(t, qOnly, qNot + 1.2)
    for (let i = 0; i < 26; i++) { const a = clamp(more * 26 - i); if (a > 0) fig(1130 + (i % 9) * 62, 430 + Math.floor(i / 9) * 140, C.ink2, a * 0.8, true) }
    text(c, 'about 35 people', 670, 300, F.head(110, 900), C.ink, { alpha: prog(t, q35 - 0.2, q35 + 0.3) })
    text(c, 'one lion: about 11', 330, 830, F.bodyI(46), C.red, { align: 'left', alpha: prog(t, q11 + 0.2, q11 + 0.7) })
    text(c, 'the other: about 24', 330, 890, F.bodyI(46), C.ink, { align: 'left', alpha: prog(t, q24 + 0.2, q24 + 0.7) })
    text(c, 'Eaten. Not everyone killed.', 1400, 820, F.headI(52, 700), C.ink2, { alpha: prog(t, qOnly + 0.3, qOnly + 0.9) })
    text(c, 'the study allows for as many as 72', 1400, 884, F.bodyI(40), C.ink2, { alpha: prog(t, qNot + 0.3, qNot + 0.9) })
    c.restore()
    fade(c, 1 - prog(t, qAns + 0.3, qAns + 0.7), PAPERF); finish(c, t, false); return false
  }

  // =============================== 9. why, brothers, Chicago ===============================
  function antelope(c, x, y, s, o = {}) {
    const col = o.col || C.ink; c.save(); c.translate(x, y); c.scale(s * (o.face || 1), s); c.fillStyle = col; c.strokeStyle = col; c.lineCap = 'round'
    if (o.dash) { c.setLineDash([6, 6]); c.lineWidth = 2.5; c.beginPath(); c.ellipse(0, -56, 44, 20, 0, 0, 7); c.stroke(); c.beginPath(); c.moveTo(34, -64); c.lineTo(54, -96); c.stroke(); c.beginPath(); c.ellipse(60, -102, 11, 7, -0.3, 0, 7); c.stroke(); for (const lx of [-30, -18, 22, 32]) { c.beginPath(); c.moveTo(lx, -40); c.lineTo(lx, 0); c.stroke() } c.restore(); return }
    c.beginPath(); c.ellipse(0, -56, 44, 20, 0, 0, 7); c.fill()
    c.lineWidth = 13; c.beginPath(); c.moveTo(34, -62); c.lineTo(54, -96); c.stroke()
    c.beginPath(); c.ellipse(60, -102, 12, 7.5, -0.3, 0, 7); c.fill()
    c.lineWidth = 3; c.beginPath(); c.moveTo(54, -108); c.quadraticCurveTo(46, -136, 58, -150); c.moveTo(60, -108); c.quadraticCurveTo(58, -134, 72, -146); c.stroke()
    c.lineWidth = 6; const sw = Math.sin(o.walk || 0) * 8; for (const [lx, k] of [[-30, 1], [-18, -1], [22, -1], [32, 1]]) { c.beginPath(); c.moveTo(lx, -42); c.lineTo(lx + sw * k, 0); c.stroke() }
    c.lineWidth = 4; c.beginPath(); c.moveTo(-42, -60); c.lineTo(-52, -34); c.stroke()
    c.restore()
  }
  const icon = {
    paw: (c) => { c.beginPath(); c.ellipse(0, 22, 40, 34, 0, 0, 7); c.fill(); for (const [x, y, r] of [[-46, -22, 17], [-17, -48, 18], [17, -48, 18], [46, -22, 17]]) { c.beginPath(); c.ellipse(x, y, r * 0.85, r, x * 0.006, 0, 7); c.fill() } },
    swords: (c) => { for (const s of [-1, 1]) { c.save(); c.rotate(s * 0.78); c.fillRect(-6, -84, 12, 126); c.beginPath(); c.moveTo(-6, -84); c.lineTo(0, -102); c.lineTo(6, -84); c.fill(); c.fillRect(-28, 36, 56, 10); c.fillRect(-5, 46, 10, 30); c.beginPath(); c.arc(0, 82, 9, 0, 7); c.fill(); c.restore() } },
    crash: (c) => { c.lineWidth = 11; c.lineJoin = 'round'; c.lineCap = 'round'; c.beginPath(); c.moveTo(-84, 20); c.lineTo(-44, -30); c.lineTo(-14, -8); c.lineTo(16, -64); c.lineTo(44, 44); c.lineTo(84, 70); c.stroke(); c.beginPath(); c.moveTo(84, 70); c.lineTo(52, 72); c.lineTo(76, 44); c.closePath(); c.fill(); c.stroke() },
  }
  // a pelt laid flat on a floor, seen at a low angle
  function rug(c, x, y, s, col) { c.save(); c.translate(x, y); c.scale(s, s * 0.34); c.fillStyle = col; c.beginPath(); c.ellipse(0, 0, 150, 70, 0, 0, 7); c.fill(); for (const [lx, ly, a] of [[-120, -70, -0.7], [-120, 70, 0.7], [110, -70, 0.7], [110, 70, -0.7]]) { c.save(); c.translate(lx, ly); c.rotate(a); c.beginPath(); c.ellipse(0, 0, 70, 22, 0, 0, 7); c.fill(); c.restore() } c.beginPath(); c.ellipse(190, 0, 52, 46, 0, 0, 7); c.fill(); c.beginPath(); c.ellipse(170, -44, 16, 16, 0, 0, 7); c.ellipse(170, 44, 16, 16, 0, 0, 7); c.fill(); c.beginPath(); c.moveTo(-150, 0); c.quadraticCurveTo(-230, 20, -280, -10); c.lineWidth = 16; c.strokeStyle = col; c.lineCap = 'round'; c.stroke(); c.restore() }
  function s9(c, t, q, S) {
    const qNobody = q('nobody knows'), qPlague = q('a cattle plague'), qTooth = q('and one of the lions') - 0.35, qRoot = q('at the root'), qFor = q('for a lion'), qSleep = q('a sleeping man') - 0.45, qOne = q('one more thing') - 0.4, q24 = q('in 2024'), qHairs = q('pulled old hairs'), qDNA = q('and read the dna'), qTwo = q('the two maneaters') - 0.4, qBro = q('were brothers'), qHow = q('and how could') - 0.4, qExist = q('because they still'), qRugs = q('patterson kept'), q25 = q('for 25 years'), qSold = q('then he sold'), q5k = q('for 5000'), qChi = q('theyre in chicago') - 0.45, qDisp = q('on display'), qWalk = q('you can walk'), qSub = q('subscribe') - 0.35, qAn = q('animal facts'), qBat = q('historys greatest'), qCol = q('worlds craziest')
    if (t < qTooth + 0.3) {
      // the prey that died
      paper(c, t)
      const z = 1 + 0.04 * prog(t, S.vis, qTooth, 'l')
      c.save(); cam(c, W / 2, H / 2, z)
      text(c, 'Why?', W / 2, 190, F.headI(130, 700), C.ink, { alpha: prog(t, S.start, S.start + 0.4) * (1 - prog(t, qPlague - 0.3, qPlague + 0.2)) })
      text(c, 'Nobody knows for sure.', W / 2, 280, F.bodyI(56), C.ink2, { alpha: prog(t, qNobody, qNobody + 0.5) * (1 - prog(t, qPlague - 0.3, qPlague + 0.2)) })
      c.strokeStyle = C.ink; c.lineWidth = 5; c.beginPath(); c.moveTo(100, 800); c.lineTo(1820, 800); c.stroke(); hatch(c, k => k.rect(100, 803, 1720, 200), { gap: 10, alpha: 0.2, angle: 0.02, box: [100, 800, 1720, 200] })
      const r = rng(88)
      for (let i = 0; i < 8; i++) { const x = 260 + i * 205 + r() * 30, s = 1.7 + r() * 0.5, gone = prog(t, qPlague + 0.3 + ((i * 3) % 8) * 0.22, qPlague + 0.8 + ((i * 3) % 8) * 0.22), keep = i === 2
        if (keep || gone < 1) { c.save(); c.globalAlpha = keep ? 1 : 1 - gone; antelope(c, x, 800, s, { face: i % 3 === 0 ? -1 : 1, walk: t * 2 + i }); c.restore() }
        if (!keep && gone > 0) { c.save(); c.globalAlpha = gone * 0.7; antelope(c, x, 800, s, { face: i % 3 === 0 ? -1 : 1, dash: true, col: C.ink3 }); c.restore() } }
      text(c, 'A cattle plague in the 1890s', W / 2, 190, F.headI(70, 700), C.ink, { alpha: prog(t, qPlague + 0.2, qPlague + 0.8) }); text(c, 'wiped out much of their prey', W / 2, 262, F.bodyI(52), C.red, { alpha: prog(t, qPlague + 1.0, qPlague + 1.6) })
      c.restore()
      fade(c, prog(t, qTooth - 0.1, qTooth + 0.3), PAPERF); finish(c, t, false); return false
    }
    if (t < qSleep + 0.3) {
      // the tooth
      paper(c, t, C.paper2)
      const z = 1 + 0.06 * prog(t, qTooth, qSleep, 'l')
      c.save(); cam(c, W / 2 + 40, H / 2, z)
      c.save(); c.beginPath(); c.rect(-200, -200, W + 400, H + 400); c.clip(); lion(c, 150, 1180, 9, { col: C.ink, mouth: 1, head: -0.12 }); c.restore()
      // one canine, and what was wrong at its root
      const tx = 748, ty = 652
      c.fillStyle = C.paper; c.strokeStyle = C.ink; c.lineWidth = 3; c.beginPath(); c.moveTo(tx - 15, ty); c.lineTo(tx + 15, ty); c.lineTo(tx + 2, ty + 66); c.closePath(); c.fill(); c.stroke()
      const pa = prog(t, qRoot - 0.3, qRoot + 0.3)
      if (pa > 0) { glow(c, tx, ty - 10, 170, '184,64,46', 0.6 * pa * (0.7 + 0.3 * Math.sin(t * 6))); c.fillStyle = C.red2; c.globalAlpha = pa; c.beginPath(); c.arc(tx, ty - 10, 20 + 4 * Math.sin(t * 6), 0, 7); c.fill(); c.globalAlpha = 1 }
      c.restore()
      text(c, 'An infection at the root of a tooth', 1330, 250, F.headI(62, 700), C.ink, { alpha: prog(t, qRoot - 0.1, qRoot + 0.5) }); text(c, 'found in a 2017 study', 1330, 320, F.bodyI(46), C.ink2, { alpha: prog(t, qRoot + 0.6, qRoot + 1.1) })
      text(c, 'Big prey: hard.', 1400, 800, F.head(76, 900), C.ink, { alpha: prog(t, qFor + 0.4, qFor + 0.9) })
      fade(c, 1 - prog(t, qTooth + 0.3, qTooth + 0.7), PAPERF); fade(c, prog(t, qSleep - 0.1, qSleep + 0.3)); finish(c, t, false); return false
    }
    if (t < qOne + 0.3) {
      // a sleeping man is easy
      const z = 1.1 + 0.1 * prog(t, qSleep, qOne, 'l')
      c.save(); cam(c, 960, 640, z)
      plain(c, t, { moon: [1500, 200, 54], hy: 700, trees: 3, seed: 44 })
      tent(c, 960, 840, 1.6, { col: INK, lit: 0.85 + 0.15 * noise(t * 6, 2) })
      eyes(c, 330, 790, 2.2, prog(t, qSleep + 0.9, qSleep + 1.5))
      c.restore()
      fade(c, 1 - prog(t, qSleep + 0.3, qSleep + 0.7) + prog(t, qOne - 0.1, qOne + 0.3)); finish(c, t, true); return true
    }
    if (t < qHow + 0.3) {
      // hair in a tooth, DNA, brothers
      paper(c, t)
      const z = 1 + 0.04 * prog(t, qOne, qHow, 'l')
      c.save(); cam(c, W / 2, H / 2, z)
      const bro = prog(t, qTwo, qTwo + 0.6)
      c.save(); c.globalAlpha = 1 - bro
      text(c, '2024', 330, 230, F.head(150, 900), C.red, { alpha: prog(t, q24, q24 + 0.4) })
      // a broken tooth with hairs packed in the cavity
      c.save(); c.translate(520, 620); c.fillStyle = C.paper2; c.strokeStyle = C.ink; c.lineWidth = 6; c.beginPath(); c.moveTo(-110, -170); c.quadraticCurveTo(0, -210, 110, -170); c.quadraticCurveTo(90, 60, 20, 230); c.lineTo(-10, 100); c.lineTo(-40, 170); c.quadraticCurveTo(-100, 40, -110, -170); c.closePath(); c.fill(); c.stroke()
      c.fillStyle = C.ink; c.beginPath(); c.ellipse(4, -40, 46, 70, 0.1, 0, 7); c.fill()
      const hp = prog(t, qHairs - 0.2, qHairs + 1.2)
      c.strokeStyle = C.gold; c.lineWidth = 3.5; const r = rng(5); for (let i = 0; i < 9; i++) { const a0 = r() * 6.28, out = hp * (140 + r() * 120), sx = 4 + Math.cos(a0) * 20, sy = -40 + Math.sin(a0) * 30; c.beginPath(); c.moveTo(sx, sy); c.quadraticCurveTo(sx + 60 + out * 0.4, sy - 60 - out * 0.3 + i * 8, sx + 140 + out, sy - 150 + i * 34); c.stroke() }
      c.restore()
      text(c, 'old hairs, from cavities in their teeth', 560, 930, F.bodyI(44), C.ink2, { alpha: prog(t, qHairs, qHairs + 0.6) })
      // the double helix
      const da = prog(t, qDNA - 0.4, qDNA + 0.4)
      if (da > 0) { c.save(); c.globalAlpha *= da; for (let i = 0; i < 44; i++) { const x = 1000 + i * 17, ph = i * 0.42 + t * 1.6, y1 = 540 + Math.sin(ph) * 90, y2 = 540 - Math.sin(ph) * 90; if (i % 2 === 0) { c.strokeStyle = 'rgba(26,21,18,0.4)'; c.lineWidth = 3; c.beginPath(); c.moveTo(x, y1); c.lineTo(x, y2); c.stroke() } c.fillStyle = Math.cos(ph) > 0 ? C.red : C.ink; c.beginPath(); c.arc(x, y1, 8, 0, 7); c.fill(); c.fillStyle = Math.cos(ph) > 0 ? C.ink : C.red; c.beginPath(); c.arc(x, y2, 8, 0, 7); c.fill() } text(c, 'DNA', 1370, 760, F.head(90, 900), C.ink, { track: 12 }); c.restore() }
      c.restore()
      if (bro > 0) { c.save(); c.globalAlpha = bro; c.strokeStyle = C.ink; c.lineWidth = 5; c.beginPath(); c.moveTo(160, 842); c.lineTo(1760, 842); c.stroke()
        c.restore(); ghost(c, bro, (o) => { lion(o, 640, 840, 3.3, { col: C.ink, tail: t * 1.5, head: 0.12 + 0.05 * Math.sin(t * 1.4) }); lion(o, 1290, 840, 3.1, { col: C.ink, face: -1, tail: t * 1.5 + 2, head: 0.16 + 0.05 * Math.sin(t * 1.4 + 1) }) }); c.save(); c.globalAlpha = bro
        text(c, 'BROTHERS', W / 2, 250, F.head(170, 900), C.red, { track: 16, alpha: prog(t, qBro - 0.1, qBro + 0.3) }); c.restore() }
      c.restore()
      fade(c, 1 - prog(t, qOne + 0.3, qOne + 0.7) + prog(t, qHow - 0.1, qHow + 0.3), PAPERF); finish(c, t, false); return false
    }
    if (t < qChi + 0.3) {
      // rugs for twenty five years, then a price
      const g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#3a2518'); g.addColorStop(0.7, '#2a1a12'); g.addColorStop(1, '#170e0a'); c.fillStyle = g; c.fillRect(0, 0, W, H)
      const z = 1 + 0.06 * prog(t, qHow, qChi, 'l')
      c.save(); cam(c, W / 2, H / 2 + 30, z)
      hatch(c, k => k.rect(-100, -100, W + 200, 800), { gap: 34, alpha: 0.35, angle: Math.PI / 2, col: '#4a3222', lw: 3, box: [-100, -100, W + 200, 800] })
      c.fillStyle = '#20140e'; c.fillRect(-100, 700, W + 200, 500); c.strokeStyle = '#4a3222'; c.lineWidth = 4; c.beginPath(); c.moveTo(-100, 700); c.lineTo(W + 100, 700); c.stroke()
      // fireplace
      c.fillStyle = '#120b08'; c.fillRect(1380, 320, 380, 380); c.fillStyle = '#4a3528'; c.fillRect(1350, 290, 440, 40); c.fillStyle = '#050303'; rr(c, 1450, 440, 240, 260, [110, 110, 0, 0]); c.fill()
      fire(c, 1570, 700, 1.5, t, 0.9)
      // armchair and its owner
      c.fillStyle = '#0c0706'; rr(c, 250, 380, 250, 330, [60, 60, 10, 10]); c.fill(); rr(c, 250, 560, 330, 150, 20); c.fill(); c.fillRect(270, 700, 20, 50); c.fillRect(540, 700, 20, 50)
      person(c, 400, 716, 300, { hat: 'none', col: '#0c0706', seated: true, mous: true })
      const ra = prog(t, qExist + 0.2, qRugs + 0.4)
      c.save(); c.globalAlpha = ra; rug(c, 800, 850, 1.5, '#b08a50'); rug(c, 1120, 960, 1.6, '#a37c44'); c.restore()
      c.restore()
      text(c, 'Because they still exist.', W / 2, 150, F.headI(72, 700), C.paper, { alpha: prog(t, qExist, qExist + 0.5) * (1 - prog(t, qRugs - 0.2, qRugs + 0.3)), shadow: '#000', blur: 30 })
      const yrs = Math.max(1, Math.round(25 * prog(t, qRugs + 0.4, q25 + 0.6, 'io')))
      text(c, yrs + (yrs === 1 ? ' year' : ' years') + ' as rugs', W / 2, 150, F.head(90, 900), C.paper, { alpha: prog(t, qRugs + 0.3, qRugs + 0.8) * (1 - prog(t, qSold - 0.2, qSold + 0.3)), shadow: '#000', blur: 30 })
      // the price tag
      const pa = prog(t, q5k - 0.4, q5k + 0.1, 'back')
      if (pa > 0) { c.save(); c.translate(W / 2, 210); c.rotate(0.06 * Math.sin(t * 2.2) * (1 - prog(t, q5k, q5k + 2))); c.scale(clamp(pa), clamp(pa)); c.fillStyle = C.paper; c.strokeStyle = C.ink; c.lineWidth = 5; c.beginPath(); c.moveTo(-330, -90); c.lineTo(270, -90); c.lineTo(350, 0); c.lineTo(270, 90); c.lineTo(-330, 90); c.closePath(); c.fill(); c.stroke(); c.fillStyle = '#2a1a12'; c.beginPath(); c.arc(286, 0, 13, 0, 7); c.fill(); text(c, '$5,000', -40, 34, F.head(120, 900), C.red); text(c, 'sold to a museum · 1924', -40, 140, F.bodyI(46), C.paper, { shadow: '#000' }); c.restore() }
      fade(c, 1 - prog(t, qHow + 0.3, qHow + 0.8) + prog(t, qChi - 0.1, qChi + 0.3)); finish(c, t, true); return true
    }
    if (t < qSub + 0.3) {
      // the glass case
      const g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#0d1018'); g.addColorStop(1, '#1b1e28'); c.fillStyle = g; c.fillRect(0, 0, W, H)
      const z = 1 + 0.1 * prog(t, qChi, qSub, 'l')
      c.save(); cam(c, W / 2, H / 2 + 20, z)
      c.fillStyle = '#07080c'; c.fillRect(-200, 880, W + 400, 400)
      // lit case
      glow(c, 960, 520, 900, '250,225,170', 0.42)
      c.fillStyle = '#e9dcbc'; c.fillRect(420, 250, 1080, 600)
      const gg = c.createLinearGradient(0, 250, 0, 850); gg.addColorStop(0, 'rgba(200,170,110,0.0)'); gg.addColorStop(1, 'rgba(160,120,70,0.55)'); c.fillStyle = gg; c.fillRect(420, 250, 1080, 600)
      c.fillStyle = '#6b5334'; c.beginPath(); c.moveTo(420, 850); c.lineTo(420, 760); for (let x = 420; x <= 1500; x += 60) c.lineTo(x, 760 - 24 * noise(x * 0.01, 7) - (x > 900 && x < 1300 ? 40 : 0)); c.lineTo(1500, 850); c.closePath(); c.fill()
      c.save(); c.globalAlpha = 0.5; acacia(c, 560, 770, 1.1, '#6b5334', 4); c.restore()
      lion(c, 760, 742, 2.6, { col: '#1a1410', head: -0.05 }); lion(c, 1160, 716, 2.4, { col: '#1a1410', face: -1, crouch: 0.9, walk: 0.9, stride: 0.6 })
      c.strokeStyle = '#07080c'; c.lineWidth = 22; c.strokeRect(420, 250, 1080, 600); c.lineWidth = 8; c.beginPath(); c.moveTo(960, 250); c.lineTo(960, 850); c.stroke()
      c.strokeStyle = 'rgba(255,255,255,0.10)'; c.lineWidth = 60; c.beginPath(); c.moveTo(560, 250); c.lineTo(470, 850); c.moveTo(1140, 250); c.lineTo(1050, 850); c.stroke()
      c.fillStyle = '#07080c'; c.fillRect(380, 850, 1160, 40)
      // the plaque
      c.fillStyle = C.gold; rr(c, 700, 900, 520, 70, 4); c.fill(); text(c, 'THE MAN-EATERS OF TSAVO', 960, 946, F.sc(28), '#1a1410', { track: 2 })
      // people walking up
      const wp = prog(t, qWalk - 1.2, qSub, 'o')
      person(c, lerp(-100, 520, wp), 1060, 420, { hat: 'none', col: '#040507', walk: t * 4.5, stride: 1 - wp, lady: false, bulk: 1.1 })
      person(c, lerp(-260, 400, wp), 1070, 260, { hat: 'cap', col: '#040507', walk: t * 6, stride: 1 - wp, arm: 0.45 * prog(t, qWalk + 0.4, qWalk + 0.9) })
      person(c, lerp(2200, 1500, wp), 1070, 400, { lady: true, col: '#040507', face: -1 })
      c.restore()
      text(c, 'CHICAGO', W / 2, 130, F.head(110, 900), C.paper, { track: 22, alpha: prog(t, qChi + 0.4, qChi + 0.9), shadow: '#000', blur: 30 })
      text(c, 'the Field Museum', W / 2, 200, F.bodyI(56), C.gold2, { alpha: prog(t, qDisp, qDisp + 0.5), shadow: '#000' })
      fade(c, 1 - prog(t, qChi + 0.3, qChi + 0.8) + prog(t, qSub - 0.1, qSub + 0.3)); finish(c, t, true); return true
    }
    // end card
    c.fillStyle = '#0a0c14'; c.fillRect(0, 0, W, H)
    glow(c, W / 2, 480, 1000, '60,80,150', 0.18)
    const a = qSub + 0.3, z = 1 + 0.03 * prog(t, a, S.out, 'l')
    c.save(); cam(c, W / 2, H / 2, z)
    eyes(c, W / 2, 170, 2.2, prog(t, a, a + 0.6) * (Math.sin(t * 0.8) > -0.95 ? 1 : 0.1))
    rule(c, 520, 1400, 250, C.paper3, prog(t, a, a + 0.8))
    text(c, 'SUBSCRIBE', W / 2, 400, F.head(150, 900), C.paper, { track: 16, alpha: prog(t, a + 0.1, a + 0.6) })
    text(c, 'and we’ll tell you more', W / 2, 470, F.bodyI(50), C.paper2, { alpha: prog(t, a + 0.6, a + 1.2) })
    const items = [['paw', 'Animal facts', qAn], ['swords', 'History’s greatest battles', qBat], ['crash', 'The world’s craziest financial collapses', qCol]]
    items.forEach(([ic, label, at], i) => {
      const p = prog(t, at - 0.1, at + 0.3, 'back'), x = 420 + i * 540
      if (p <= 0) return
      c.save(); c.translate(x, 680); c.scale(p, p); c.strokeStyle = C.gold; c.lineWidth = 4; c.beginPath(); c.arc(0, 0, 120, 0, 7); c.stroke()
      c.fillStyle = i === 0 ? C.gold2 : C.paper; c.strokeStyle = i === 2 ? C.red2 : C.paper; if (i === 2) c.fillStyle = C.red2; icon[ic](c); c.restore()
      const ws = label.split(' '), l1 = ws.length > 3 ? ws.slice(0, 3).join(' ') : label, l2 = ws.length > 3 ? ws.slice(3).join(' ') : ''
      text(c, l1, x, 870, F.body(40), C.paper, { alpha: clamp(p) }); if (l2) text(c, l2, x, 918, F.body(40), C.paper, { alpha: clamp(p) })
    })
    c.restore()
    fade(c, 1 - prog(t, a, a + 0.4)); finish(c, t, true); return true
  }

  window.SCENES.push(s7, s8, s9)
})()
