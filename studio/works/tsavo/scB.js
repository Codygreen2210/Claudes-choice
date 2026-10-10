// scB.js: scenes 4-6. The trap, the strike, the platform.
(function () {
  const { clamp, lerp, EZ, prog, bump, rng, noise, track } = K
  const { W, H, C, F, layer, paper, finish, hatch, rr, text, typeset, rule, person, crowd, glow, tw, clock } = L
  const { ghost, N, lion, lionDown, eyes, night, ground, acacia, thorn, tent, fire, train, rails, patterson, turban } = T2
  const { cam, fade, plain, bridge, INK, WORK } = TS

  // =============================== 4. the trap ===============================
  // the trap in cutaway: men's end on the left behind bars, the lion's end on the right with a drop door
  function trap(c, x, y, o = {}) {
    const col = o.col || INK, w = 760, h = 300, door = o.door ?? 0, lit = o.lit ?? 0
    c.save(); c.translate(x, y)
    if (lit) { c.fillStyle = `rgba(240,170,80,${0.30 * lit})`; c.fillRect(-w / 2, -h, w, h); glow(c, -w / 2 + 120, -h + 70, 330, N.fire, 0.6 * lit) }
    c.fillStyle = col; c.strokeStyle = col
    c.fillRect(-w / 2 - 14, -h - 26, w + 28, 26); c.fillRect(-w / 2 - 14, 0, w + 28, 22); c.fillRect(-w / 2 - 14, -h, 22, h)      // roof, floor, back wall (sleepers)
    for (let i = 0; i < 12; i++) c.fillRect(-w / 2 - 14 + i * 66, -h - 40, 46, 16)
    // bars between the two rooms
    for (let i = 0; i < 6; i++) c.fillRect(-w / 2 + 236 + (i % 2) * 14, -h, 6, h)
    for (let i = 0; i < 4; i++) c.fillRect(-w / 2 + 232, -h + 40 + i * 70, 28, 6)
    // the drop door at the right end: rails, one of which can be shot away
    const dy = -h * (1 - door)
    for (let i = 0; i < 6; i++) { if (o.broken != null && (i === 2 || i === 3)) continue; c.fillRect(w / 2 - 12, dy - h + 8 + i * 50, 18, 34) }
    c.fillRect(w / 2 - 14, dy - h, 22, 8); c.fillRect(w / 2 - 14, -h - 60, 6, 60); c.fillRect(w / 2 + 2, -h - 60, 6, 60)
    if (o.broken != null && o.broken < 1) { c.save(); c.translate(w / 2 + o.broken * 300, dy - h / 2 - 30 + o.broken * o.broken * 340); c.rotate(o.broken * 6); c.fillRect(-9, -42, 18, 84); c.restore() }
    c.restore()
  }
  function s4(c, t, q, S) {
    const qTree = q('he sat up in trees'), qElse = q('the lions struck'), qSo = q('so he built') - 0.35, qSl = q('railway sleepers'), qDoor = q('with a door'), qBait = q('and for bait'), qSol = q('two soldiers'), qWork = q('it worked') - 0.35, qIn = q('a lion walked in'), qFell = q('the door fell'), qFace = q('and the two soldiers'), qFroze = q('froze'), qFired = q('when they finally'), q20 = q('more than twenty'), qScr = q('they barely'), qHit = q('but they did'), qBar = q('one bar blew'), qOut = q('and the lion walked')
    if (t < qSo + 0.3) {
      // up a tree, and the lions somewhere else
      const z = 1 + 0.05 * prog(t, S.vis, qSo, 'l')
      c.save(); cam(c, W / 2 + 60 * prog(t, qElse - 0.5, qSo, 'io'), H / 2, z)
      plain(c, t, { moon: [1500, 190, 60], hy: 760, trees: 3, seed: 14 })
      // the big tree with a man in it
      c.save(); c.translate(430, 900); c.fillStyle = INK; c.strokeStyle = INK; c.lineCap = 'round'
      c.lineWidth = 46; c.beginPath(); c.moveTo(0, 0); c.quadraticCurveTo(-30, -260, 20, -480); c.stroke()
      c.lineWidth = 24; for (const [a, b, e, g] of [[16, -430, -330, -640], [18, -450, 400, -650], [0, -340, 250, -470], [6, -380, -220, -520]]) { c.beginPath(); c.moveTo(a, b); c.quadraticCurveTo((a + e) / 2, b - 20, e, g); c.stroke() }
      const r = rng(41); c.beginPath(); for (let i = 0; i < 16; i++) c.ellipse(-430 + i * 58 + r() * 20, -690 - r() * 40, 110 + r() * 40, 40 + r() * 16, 0, 0, 7); c.fill()
      c.restore()
      patterson(c, 640, 450, 210, { col: INK, seated: true, aim: -1.45 + 0.03 * Math.sin(t * 0.8), arm: 0.25, lean: 0.03 * Math.sin(t * 0.6) })
      // nights going by
      const nights = Math.floor(prog(t, qTree, qElse) * 4)
      for (let i = 0; i < 4; i++) { c.fillStyle = i <= nights ? C.paper : 'rgba(238,226,200,0.25)'; c.beginPath(); c.arc(1040 + i * 50, 420, 14, 0, 7); c.fill(); c.fillStyle = '#1d2a4c'; if (i <= nights) { c.beginPath(); c.arc(1047 + i * 50, 415, 13, 0, 7); c.fill() } }
      // the far camp, where it actually happens
      const far = prog(t, qElse - 0.2, qElse + 0.4)
      for (const [x, k] of [[1500, 0], [1600, 1], [1700, 0]]) { tent(c, x, 772, 0.42, { col: INK, lit: k ? 1 - prog(t, qElse + 0.5, qElse + 0.8) : 0.8 }) }
      if (far > 0) { lion(c, lerp(2000, 1650, prog(t, qElse - 0.2, qElse + 0.7, 'o')), 780, 0.8, { face: -1, walk: t * 9, stride: 1, crouch: 0.5, col: INK, eye: true }); eyes(c, 1790, 740, 0.9, prog(t, qElse + 0.8, qElse + 1.2)) }
      c.restore()
      text(c, 'Night after night', 1120, 350, F.headI(64, 700), C.paper, { alpha: prog(t, qTree + 0.6, qTree + 1.2) * (1 - prog(t, qElse - 0.2, qElse + 0.2)), shadow: '#000', blur: 30 })
      text(c, 'They struck somewhere else.', 1220, 350, F.headI(64, 700), C.red2, { alpha: prog(t, qElse + 0.2, qElse + 0.7), shadow: '#000', blur: 30 })
      fade(c, prog(t, qSo - 0.1, qSo + 0.3)); finish(c, t, true); return true
    }
    if (t < qWork + 0.3) {
      // the plan, on paper
      paper(c, t)
      const z = 1 + 0.04 * prog(t, qSo, qWork, 'l')
      c.save(); cam(c, W / 2, H / 2 + 10, z)
      text(c, 'THE TRAP', W / 2, 150, F.head(90, 900), C.ink, { track: 14, alpha: prog(t, qSo + 0.3, qSo + 0.8) }); rule(c, 700, 1220, 180, C.ink, prog(t, qSo + 0.4, qSo + 1.2))
      const dp = prog(t, qSl - 0.3, qSl + 1.6, 'io')
      c.save(); c.beginPath(); c.rect(500, 0, 920 * dp, H); c.clip(); trap(c, 960, 800, { col: C.ink, door: 0 }); c.restore()
      const lab = (s, x, y, lx, ly, at) => { const a = prog(t, at, at + 0.4); if (a <= 0) return; c.save(); c.globalAlpha = a; c.strokeStyle = C.red; c.lineWidth = 3; c.beginPath(); c.moveTo(x, y); c.lineTo(lx, ly); c.stroke(); c.fillStyle = C.red; c.beginPath(); c.arc(lx, ly, 6, 0, 7); c.fill(); text(c, s, x, y - 14, F.bodyI(44), C.red, {}); c.restore() }
      lab('railway sleepers and rails', 620, 330, 700, 470, qSl + 0.2)
      lab('a door that drops shut', 1500, 330, 1350, 480, qDoor + 0.2)
      lab('iron bars', 1130, 600, 836, 650, qBait + 0.9)
      // the bait
      const ba = prog(t, qSol - 0.4, qSol + 0.3)
      if (ba > 0) { c.save(); c.globalAlpha = ba; for (const dx of [0, 96]) turban(c, 640 + dx, 800, 250, { col: C.ink, arm: 0.2 }); text(c, 'two soldiers, as bait', 560, 900, F.bodyI(44), C.ink, {}); c.restore() }
      // the door, showing how it falls
      const dd = 0.5 + 0.5 * Math.sin(t * 2.2)
      if (t > qDoor) { c.save(); c.globalAlpha = 0.35; c.fillStyle = C.red; c.fillRect(1326, 800 - 300 * (1 - 0) - 300 + 300 * dd * 0 , 0, 0); c.restore(); c.strokeStyle = C.red; c.lineWidth = 4; c.setLineDash([10, 8]); c.beginPath(); c.moveTo(1400, 430); c.lineTo(1400, 430 + 280 * dd); c.stroke(); c.setLineDash([]); c.fillStyle = C.red; c.beginPath(); c.moveTo(1388, 430 + 280 * dd); c.lineTo(1412, 430 + 280 * dd); c.lineTo(1400, 452 + 280 * dd); c.closePath(); c.fill() }
      c.strokeStyle = C.ink; c.lineWidth = 5; c.beginPath(); c.moveTo(300, 824); c.lineTo(1620, 824); c.stroke()
      c.restore()
      fade(c, 1 - prog(t, qSo + 0.3, qSo + 0.7) + 0, '238,226,200'); fade(c, prog(t, qWork - 0.1, qWork + 0.3)); finish(c, t, false); return false
    }
    // the night it worked
    const gy = 880
    const z = track(t, [[qWork, 1.0], [qFace, 1.12, 'sine'], [qFroze + 1.2, 1.3, 'io'], [qFired, 1.12, 'io'], [S.out, 1.06, 'l']])
    c.save(); cam(c, track(t, [[qWork, 1000], [qFace, 960, 'sine'], [qFroze + 1.2, 820, 'io'], [qFired, 960, 'io'], [qOut, 1040, 'io']]), track(t, [[qWork, 600], [qFroze + 1.2, 680, 'io'], [qFired, 620, 'io']]), z)
    plain(c, t, { moon: [300, 170, 50], hy: 760, trees: 3, seed: 21 })
    thorn(c, -300, 520, gy + 4, 70, INK, 6); thorn(c, 1420, 2300, gy + 4, 64, INK, 7)
    const door = prog(t, qFell - 0.05, qFell + 0.13, 'i'), broke = t > qBar ? prog(t, qBar, qBar + 0.9, 'l') : null
    const fear = t > qFace ? (0.5 + 0.5 * Math.sin(t * 34)) * (1 - prog(t, qFired, qFired + 0.3)) : 0
    trap(c, 960, gy, { col: INK, lit: 0.9 + 0.1 * noise(t * 6, 2), door, broken: broke })
    // the two soldiers
    for (const [dx, k] of [[0, 0], [86, 1]]) turban(c, 650 + dx + fear * (k ? -3 : 3), gy, 240, { col: INK, arm: t > qFired ? 0.42 : 0.16, lean: -0.05 * prog(t, qFace, qFroze) })
    // their shots
    const firing = t > qFired + 0.2 && t < qBar + 0.1
    if (firing) { const k = Math.floor((t - qFired) * 5.0); if (((t - qFired) * 5.0) % 1 < 0.28) { const fx = 760 + (k % 2) * 60, fy = gy - 200 + (k % 3) * 14; glow(c, fx, fy, 110, '255,220,150', 0.55); c.strokeStyle = 'rgba(255,225,160,0.8)'; c.lineWidth = 3; c.beginPath(); c.moveTo(fx + 20, fy); c.lineTo(fx + 520 + (k * 73 % 190), fy - 110 + (k * 131 % 260)); c.stroke() } }
    // the lion: in, trapped, raging, out
    const lx = track(t, [[qWork, 2300], [qIn - 0.2, 1700, 'sine'], [qFell - 0.1, 1140, 'sine'], [qBar + 0.6, 1140, 'l'], [qOut + 0.3, 1300, 'io'], [qOut + 2.6, 2600, 'i']])
    const rage = t > qFell + 0.2 && t < qBar + 0.5 ? 1 : 0, lunge = rage * Math.max(0, Math.sin(t * 7)) * 46
    const outside = t > qOut
    lion(c, lx - (rage ? lunge : 0), gy, 2.2, { face: outside ? 1 : -1, walk: lx * 0.04, stride: (t < qFell - 0.1 || outside) ? 1 : 0, crouch: outside ? 0.2 : 0.35 + rage * 0.2, eye: true, col: INK, mouth: rage * (0.4 + 0.6 * Math.max(0, Math.sin(t * 7))), head: rage ? -0.15 : 0 })
    c.restore()
    const cnt = Math.min(20, Math.floor(prog(t, qFired + 0.2, q20 + 1.4) * 21))
    if (t > qFired + 0.2) text(c, cnt >= 20 ? 'more than 20 shots' : cnt + ' shots', 1500, 170, F.head(76, 900), C.paper, { alpha: 1 - prog(t, qHit + 1.5, qBar), shadow: '#000', blur: 30 })
    text(c, 'It worked.', W / 2, 170, F.head(110, 900), C.paper, { alpha: prog(t, qWork + 0.35, qWork + 0.6) * (1 - prog(t, qIn - 0.2, qIn + 0.2)), shadow: '#000', blur: 40 })
    text(c, 'One bar.', 500, 170, F.head(90, 900), C.red2, { alpha: prog(t, qBar, qBar + 0.3), shadow: '#000', blur: 40 })
    fade(c, 1 - prog(t, qWork + 0.3, qWork + 0.7)); finish(c, t, true); return true
  }

  // =============================== 5. the strike ===============================
  function calendar(c, x, y, mon, day, sub, a = 1, s = 1) {
    c.save(); c.translate(x, y); c.scale(s, s); c.globalAlpha *= a
    c.fillStyle = 'rgba(0,0,0,0.22)'; c.fillRect(-132, -152, 280, 330); c.fillStyle = C.paper; c.strokeStyle = C.ink; c.lineWidth = 4; c.fillRect(-140, -160, 280, 330); c.strokeRect(-140, -160, 280, 330)
    c.fillStyle = C.red; c.fillRect(-140, -160, 280, 74); text(c, mon, 0, -108, F.sc(34), C.paper, { track: 3 })
    text(c, String(day), 0, 86, F.head(170, 900), C.ink); text(c, sub, 0, 146, F.old(38, true), C.ink2, { track: 8 })
    c.restore()
  }
  function s5(c, t, q, S) {
    const qFirst = q('on the first'), qTools = q('they put down'), qHund = q('hundreds of them') - 0.2, qLying = q('by lying down'), qClimb = q('then they climbed') - 0.2, qLeft = q('and left'), qStop = q('the railway stopped') - 0.35, q3 = q('for about three'), qTwo = q('because of two')
    paper(c, t)
    const ry = 700
    if (t < qStop + 0.3) {
      const z = track(t, [[S.vis, 1.04], [qHund, 1.0, 'sine'], [qLeft + 1, 0.94, 'l']])
      c.save(); cam(c, track(t, [[S.vis, 900], [qHund, 960, 'sine'], [qLeft, 1040, 'io']]), 560, z)
      // far scrub
      c.save(); c.globalAlpha = 0.25; for (let i = 0; i < 7; i++) acacia(c, -200 + i * 420 + (i % 2) * 120, ry - 30, 0.9 + (i % 3) * 0.3, C.ink3, i + 3); c.restore()
      c.strokeStyle = C.ink; c.lineWidth = 5; c.beginPath(); c.moveTo(-600, ry + 14); c.lineTo(2800, ry + 14); c.stroke()
      hatch(c, k => k.rect(-600, ry + 16, 3400, 500), { gap: 10, alpha: 0.2, angle: 0.02, box: [-600, ry, 3400, 500] })
      rails(c, -600, 2800, ry)
      // the train: comes in, brakes for the men on the line, takes them away
      const tx = track(t, [[qHund - 0.6, -700], [qLying + 1.0, 900, 'o'], [qLeft - 0.2, 900, 'l'], [qStop + 0.4, 3600, 'i']])
      const moving = t < qLying + 1.0 || t > qLeft - 0.2
      const board = prog(t, qClimb, qLeft - 0.3)
      // men: drop tools, lie on the rails, then board
      WORK.slice(0, 26).forEach((p, i) => {
        const down = prog(t, qHund + i * 0.04, qHund + 0.8 + i * 0.04, 'io'), up = clamp(board * 1.6 - (i / 26) * 0.6)
        const home = 300 + i * 52 + p.jit * 30, lie = 1040 + (i % 13) * 62 + p.jit2 * 20
        if (up >= 1) return
        const x = lerp(lerp(home, lie, down), tx - 420 - (i % 6) * 90, EZ.io(up)), lying = down * (1 - clamp(up * 3))
        c.save(); c.translate(x, ry + 6 + (i % 2) * 20 * (1 - lying)); c.rotate(-Math.PI / 2 * lying * (i % 2 ? 1 : -1)); turban(c, 0, lying * 16, p.h * 0.62, { walk: t * 7 * p.sp + p.ph, stride: (down > 0 && down < 1) || (up > 0 && up < 1) ? 1 : 0, face: 1, bulk: p.bulk }); c.restore()
        // the tool they dropped
        const tp = prog(t, qTools + i * 0.03, qTools + 0.5 + i * 0.03, 'bounce')
        if (i % 3 === 0) { c.save(); c.translate(home + 40, ry + 30); c.rotate(-0.9 + 0.9 * tp + 1.4 * tp); c.strokeStyle = C.ink; c.lineWidth = 5; c.beginPath(); c.moveTo(0, 0); c.lineTo(0, -70); c.stroke(); c.fillStyle = C.ink; c.fillRect(-14, -84, 28, 16); c.restore() }
      })
      train(c, tx, ry, 1.15, t, { wagons: 4, riders: board > 0.6, roll: tx * 0.03, smoke: 1, speed: moving ? 0.6 : 0 })
      c.restore()
      calendar(c, 250, 250, 'DECEMBER', 1, '1898', prog(t, qFirst - 0.2, qFirst + 0.3) * (1 - prog(t, qStop - 0.4, qStop)))
      text(c, 'Hundreds of men stopped the next train', 1100, 180, F.headI(60, 700), C.ink, { alpha: prog(t, qHund + 0.3, qHund + 0.9) * (1 - prog(t, qStop - 0.4, qStop)) })
      fade(c, prog(t, qStop - 0.1, qStop + 0.3), '238,226,200'); finish(c, t, false); return false
    }
    // the works, silent
    const z = 0.86 + 0.05 * prog(t, qStop, S.out, 'l')
    c.save(); cam(c, 960, 640, z)
    bridge(c, t, 0.55)
    // abandoned tools, and two shapes watching from the far bank
    for (const x of [200, 330, 470, 1500, 1700]) { c.save(); c.translate(x, 598); c.rotate(1.3); c.strokeStyle = C.ink; c.lineWidth = 5; c.beginPath(); c.moveTo(0, 0); c.lineTo(0, -64); c.stroke(); c.fillStyle = C.ink; c.fillRect(-12, -76, 24, 14); c.restore() }
    const la = prog(t, qTwo - 0.3, qTwo + 0.6)
    if (la > 0) { c.save(); c.globalAlpha = la; lion(c, 1560, 598, 1.5, { face: -1, col: C.ink, tail: t * 2 }); lion(c, 1820, 598, 1.4, { face: -1, col: C.ink, tail: t * 2 + 1, head: 0.2 }); c.restore() }
    c.restore()
    text(c, 'WORK STOPPED', W / 2, 150, F.head(110, 900), C.ink, { track: 10, alpha: prog(t, qStop + 0.3, qStop + 0.7) })
    text(c, 'for about three weeks', W / 2, 228, F.bodyI(60), C.red, { alpha: prog(t, q3, q3 + 0.5) })
    fade(c, 1 - prog(t, qStop + 0.3, qStop + 0.7), '238,226,200'); finish(c, t, false); return false
  }

  // =============================== 6. the platform ===============================
  function machan(c, x, y, h, wob = 0) {
    c.save(); c.translate(x, y); c.strokeStyle = INK; c.fillStyle = INK; c.lineCap = 'round'; c.lineWidth = 11
    for (const [bx, tx2] of [[-150, -34], [-60, -12], [70, 14], [160, 36]]) { c.beginPath(); c.moveTo(bx, 0); c.lineTo(tx2 + wob * 60, -h); c.stroke() }
    c.lineWidth = 6; c.beginPath(); c.moveTo(-104, -h * 0.4); c.lineTo(104 + wob * 20, -h * 0.4 - 14); c.moveTo(-72 + wob * 30, -h * 0.72); c.lineTo(76 + wob * 40, -h * 0.72 + 12); c.stroke()
    c.save(); c.translate(wob * 60, -h); c.rotate(wob * 0.12); c.fillRect(-120, -10, 240, 16); c.restore()
    c.restore()
  }
  function s6(c, t, q, S) {
    const qNinth = q('on the ninth'), qDonk = q('he found a donkey'), qKnew = q('he knew'), qSo = q('so he built') - 0.3, qFour = q('four poles'), q12 = q('twelve feet'), qDusk = q('and at dusk') - 0.3, qCame = q('the lion came') - 0.4, qBut = q('but it didnt'), qNot = q('it had noticed'), qTwo = q('for about two hours') - 0.2, qCl = q('closer'), qCl2 = q('and closer'), qRick = q('four rickety'), qMid = q('near midnight') - 0.3, qShot = q('and fired') + 0.45, qMorn = q('in the morning') - 0.4, q98 = q('nine feet'), q8 = q('it took eight')
    const gy = 880, px = 900
    if (t < qMorn + 0.3) {
      // dusk into night on one stage
      const dusk = prog(t, qDusk - 1, qCame + 1.5, 'io')                 // 0 = late day, 1 = night
      const day = t < qSo ? 1 : 1 - dusk
      const mix3 = (a, b, p) => K.mix(a, b, p)
      const z = track(t, [[S.vis, 1.0], [qSo, 1.06, 'sine'], [qDusk, 1.0, 'io'], [qTwo, 1.1, 'sine'], [qRick + 1.5, 1.3, 'io'], [qMid, 1.12, 'io'], [qMorn, 1.06, 'l']])
      c.save(); cam(c, track(t, [[S.vis, 960], [qTwo, 960, 'l'], [qRick + 1.5, 900, 'io'], [qMid, 960, 'io']]), track(t, [[S.vis, 560], [qTwo, 560, 'l'], [qRick + 1.5, 470, 'io'], [qMid, 560, 'io']]), z)
      // sky
      const g = c.createLinearGradient(0, 0, 0, gy); g.addColorStop(0, mix3('#0a0f20', '#4a4a78', day)); g.addColorStop(0.6, mix3('#1d2a4c', '#c9785a', day)); g.addColorStop(1, mix3('#3d4e7a', '#f0b070', day)); c.fillStyle = g; c.fillRect(-600, -400, W + 1200, gy + 400)
      if (day < 0.6) { c.save(); c.globalAlpha = 1 - day / 0.6; const mp = prog(t, qCame, qMid + 1, 'l'); const mx = lerp(1500, 420, mp), my = 300 - Math.sin(mp * Math.PI) * 170; c.drawImage(T2.stars(), 0, 0); glow(c, mx, my, 330, '200,210,240', 0.3); c.fillStyle = N.moon; c.beginPath(); c.arc(mx, my, 50, 0, 7); c.fill(); c.restore() }
      if (day > 0.2) { glow(c, 1500, gy - 20, 700, '255,200,140', 0.5 * day); c.fillStyle = `rgba(255,230,190,${day})`; c.beginPath(); c.arc(1500, gy + 10 + 120 * dusk, 70, 0, 7); c.fill() }
      // ridge and ground
      c.fillStyle = mix3('#1a2542', '#5a3a3a', day); c.beginPath(); c.moveTo(-600, gy - 60); for (let x = -600; x <= W + 600; x += 60) c.lineTo(x, gy - 90 - 30 * noise(x * 0.0016, 5)); c.lineTo(W + 600, gy); c.lineTo(-600, gy); c.closePath(); c.fill()
      const gg = c.createLinearGradient(0, gy, 0, H + 200); gg.addColorStop(0, mix3('#42537f', '#8a5a44', day)); gg.addColorStop(1, mix3('#161d34', '#2a1a16', day)); c.fillStyle = gg; c.fillRect(-600, gy - 2, W + 1200, 500)
      acacia(c, 250, gy, 1.5, INK, 3); acacia(c, 1640, gy - 40, 0.9, '#0d1326', 6); thorn(c, -300, 260, gy + 30, 70, INK, 4); thorn(c, 1500, 2300, gy + 40, 76, INK, 9)
      // the donkey it left
      c.save(); c.translate(px + 270, gy); c.fillStyle = INK; c.strokeStyle = INK; c.lineCap = 'round'
      c.beginPath(); c.ellipse(0, -22, 86, 26, 0.03, 0, 7); c.fill()                                      // body on its side
      c.lineWidth = 16; c.beginPath(); c.moveTo(70, -26); c.lineTo(118, -12); c.stroke()                  // neck
      c.beginPath(); c.ellipse(136, -8, 30, 13, 0.25, 0, 7); c.fill()                                     // head
      c.lineWidth = 7; c.beginPath(); c.moveTo(118, -18); c.lineTo(104, -50); c.moveTo(128, -18); c.lineTo(124, -52); c.stroke()   // ears
      c.lineWidth = 9; for (const [a, e] of [[-58, -70], [-40, -44], [40, 26], [56, 64]]) { c.beginPath(); c.moveTo(a, -34); c.lineTo(e, -74); c.stroke() }   // stiff legs
      c.restore()
      // the platform going up
      const build = prog(t, qSo + 0.2, q12 + 0.6, 'o')
      const circ = prog(t, qTwo, qMid, 'l'), rad = lerp(560, 250, prog(t, qTwo, qRick + 1, 'io'))
      const ang = t > qNot ? (t - qNot) * 0.9 + 1.2 : 0
      const lzx = px + Math.cos(ang) * rad * 1.5, depth = Math.sin(ang)        // depth > 0: in front
      const near = t > qNot && t < qShot ? clamp(1 - rad / 560) : 0
      const wob = (t > qRick - 0.3 && t < qShot) ? 0.5 * Math.sin(t * 11) * near * bump(t, qRick - 0.3, 3.2) : 0
      const lionAt = (front) => {
        if (t < qCame || t > qShot + 2.5) return
        let x, y2, s, face, st = 1, cr = 0.35, a = 1
        if (t < qNot) { x = track(t, [[qCame, 2500], [qBut + 0.6, 1560, 'sine'], [qNot + 0.3, 1500, 'l']]); y2 = gy + 30; s = 2.0; face = -1; st = t < qBut + 0.6 ? 1 : 0; if (!front) return }
        else if (t < qShot) { if ((depth > 0) !== front) return; x = lzx; y2 = gy + 34 + depth * 46; s = 1.9 + depth * 0.45; face = Math.cos(ang + Math.PI / 2) * (1) > 0 ? -1 : 1; face = -Math.sign(Math.sin(ang)) || 1; face = depth > 0 ? -1 : 1; a = depth > 0 ? 1 : 0.75 }
        else { if (!front) return; x = lerp(lzx, lzx + 1400, prog(t, qShot, qShot + 1.6, 'i')); y2 = gy + 40; s = 2.1; face = 1; cr = 0 }
        c.save(); c.globalAlpha = a; lion(c, x, y2, s, { face, walk: x * 0.04, stride: st, crouch: cr, eye: true, col: depth > 0 || t < qNot || t > qShot ? INK : '#0a0e1c', head: t < qNot && t > qBut + 0.8 ? -0.5 * prog(t, qNot - 0.6, qNot) : 0 }); c.restore()
      }
      lionAt(false)
      if (build > 0) { c.save(); c.beginPath(); c.rect(px - 300, gy - 520 * build - 40, 600, 520 * build + 60); c.clip(); machan(c, px, gy, 420, wob); c.restore() }
      if (t > qDusk + 0.4 || t > qNinth && false) { const up = prog(t, qDusk + 0.3, qDusk + 1.6, 'io'); patterson(c, px + wob * 60 - 20, lerp(gy, gy - 430, up), 200, { col: INK, seated: up >= 1, aim: up >= 1 ? -1.5 + (t > qMid ? 0.25 * prog(t, qMid, qShot - 0.4) : 0.04 * Math.sin(t)) : -1.2, arm: up >= 1 ? 0.3 : 0.1, face: (t > qNot && t < qShot ? (depth > 0 ? (lzx > px ? 1 : -1) : (lzx > px ? 1 : -1)) : 1) }) }
      else if (t > qNinth) { const wx = track(t, [[qNinth, -200], [qDonk + 0.6, px - 240, 'o']]); patterson(c, wx, gy + 10, 230, { col: INK, walk: t * 5, stride: t < qDonk + 0.6 ? 1 : 0, aim: -1.2, arm: 0.1 }) }
      lionAt(true)
      // 12 feet
      const da = prog(t, q12, q12 + 0.4) * (1 - prog(t, qDusk - 0.4, qDusk))
      if (da > 0) { c.save(); c.globalAlpha = da; c.strokeStyle = C.paper; c.lineWidth = 3; c.beginPath(); c.moveTo(px - 230, gy); c.lineTo(px - 230, gy - 420); c.moveTo(px - 246, gy); c.lineTo(px - 214, gy); c.moveTo(px - 246, gy - 420); c.lineTo(px - 214, gy - 420); c.stroke(); text(c, '12 ft', px - 300, gy - 196, F.bodyI(46), C.paper, { shadow: '#000' }); c.restore() }
      // the shot
      const fl = bump(t, qShot, 0.16)
      if (fl > 0) { glow(c, px + 90, gy - 470, 420, '255,230,170', 0.9 * fl); c.strokeStyle = `rgba(255,235,180,${fl})`; c.lineWidth = 4; c.beginPath(); c.moveTo(px + 70, gy - 470); c.lineTo(lzx, gy - 40); c.stroke() }
      c.restore()
      calendar(c, 230, 240, 'DECEMBER', 9, '1898', prog(t, qNinth - 0.2, qNinth + 0.3) * (1 - prog(t, qSo - 0.3, qSo + 0.2)), 0.9)
      // two hours going by
      const ha = prog(t, qTwo, qTwo + 0.5) * (1 - prog(t, qMid - 0.4, qMid))
      if (ha > 0) { c.save(); c.globalAlpha = ha; clock(c, 1700, 200, 96, 21.9 + 2.0 * circ, { col: '#0a0d18', face: '#d8cfb6', rim: C.gold }); c.restore() }
      text(c, 'It had noticed him.', 520, 330, F.headI(80, 700), C.paper, { alpha: prog(t, qNot, qNot + 0.4) * (1 - prog(t, qTwo - 0.3, qTwo + 0.2)), shadow: '#000', blur: 30 })
      text(c, 'Closer.', 420, 190, F.head(100, 900), C.paper, { alpha: prog(t, qCl, qCl + 0.25) * (1 - prog(t, qRick - 0.3, qRick)), shadow: '#000', blur: 30 }); text(c, 'And closer.', 520, 300, F.head(100, 900), C.red2, { alpha: prog(t, qCl2, qCl2 + 0.25) * (1 - prog(t, qRick - 0.3, qRick)), shadow: '#000', blur: 30 })
      fade(c, bump(t, qShot + 0.5, 3.0) * 0.55 + prog(t, qMorn - 0.2, qMorn + 0.3)); finish(c, t, day < 0.5); return day < 0.5
    }
    // morning
    const g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#9db0c6'); g.addColorStop(0.6, '#efd6a6'); g.addColorStop(1, '#f1b877'); c.fillStyle = g; c.fillRect(0, 0, W, H)
    const p = prog(t, qMorn, S.out, 'l')
    glow(c, 1500, 760, 800, '255,236,190', 0.7); c.fillStyle = '#fff3d0'; c.beginPath(); c.arc(1500, 760 - 60 * p, 70, 0, 7); c.fill()
    c.save(); cam(c, W / 2, H / 2, 1.0 + 0.04 * p)
    c.fillStyle = '#5d5560'; c.beginPath(); c.moveTo(-200, 800); for (let x = -200; x <= W + 200; x += 60) c.lineTo(x, 780 - 30 * noise(x * 0.0016, 5)); c.lineTo(W + 200, 900); c.lineTo(-200, 900); c.closePath(); c.fill()
    c.fillStyle = '#17120f'; c.fillRect(-200, 870, W + 400, 400); acacia(c, 250, 872, 1.5, '#17120f', 3)
    const carry = prog(t, q8 - 0.3, q8 + 0.4), cx = lerp(1050, 760, prog(t, q8, S.out + 1, 'l'))
    if (carry < 1) { c.save(); c.globalAlpha = 1 - carry; lionDown(c, 1050, 876, 3.0, { col: '#17120f' }); c.restore() }
    // the tape
    const ma = prog(t, q98 - 0.2, q98 + 0.6) * (1 - carry)
    if (ma > 0) { c.save(); c.globalAlpha = ma; const x0 = 1050 - 92 * 3 * 1, x1 = 1050 + 66 * 3; const xe = lerp(x0, x1, prog(t, q98 - 0.2, q98 + 0.8, 'io')); c.strokeStyle = C.red; c.lineWidth = 5; c.beginPath(); c.moveTo(x0, 690); c.lineTo(xe, 690); c.moveTo(x0, 670); c.lineTo(x0, 710); c.moveTo(xe, 670); c.lineTo(xe, 710); c.stroke(); text(c, '9 ft 8 in', (x0 + x1) / 2, 650, F.head(84, 900), C.red, { alpha: prog(t, q98 + 0.4, q98 + 0.9) }); c.restore() }
    if (carry > 0) { c.save(); c.globalAlpha = carry
      c.strokeStyle = '#17120f'; c.lineWidth = 9; c.beginPath(); c.moveTo(cx - 430, 640); c.lineTo(cx + 430, 640); c.stroke()
      c.save(); c.translate(cx, 700); c.scale(1, -1); lionDown(c, 0, 0, 2.6, { col: '#17120f', head: -0.5 }); c.restore()
      for (let i = 0; i < 8; i++) { const x = cx - 420 + i * 120; turban(c, x, 880 + (i % 2) * 8, 250, { col: '#17120f', face: -1, walk: t * 5 + i, stride: 0.8, arm: 0.72 }) }
      c.restore() }
    c.restore()
    text(c, 'The first man-eater', W / 2, 150, F.headI(72, 700), '#17120f', { alpha: prog(t, qMorn + 0.5, qMorn + 1.1) })
    text(c, 'Eight men to carry it', W / 2, 230, F.bodyI(52), '#17120f', { alpha: prog(t, q8 + 0.3, q8 + 0.9) })
    fade(c, 1 - prog(t, qMorn + 0.3, qMorn + 0.8)); finish(c, t, false); return false
  }

  window.SCENES.push(s4, s5, s6)
  window.TS.calendar = calendar; window.TS.machan = machan
})()
