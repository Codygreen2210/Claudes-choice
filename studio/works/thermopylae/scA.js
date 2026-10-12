// scA.js: scenes 1-7 of Thermopylae. Each scene is draw(c, t, q, S) -> true if the picture is dark.
// Staging for the whole film: Persians come from the left in ink; the Greeks hold the right, ink with red cloaks.
// The Persian king and his gold are the one gold.
(function () {
  const { clamp, lerp, EZ, prog, bump, rng, noise, track, mix } = K
  const { W, H, C, F, paper, finish, hatch, text, typeset, rule, person, glow, tw, bank, layer } = L
  const { view, smoke, horse, fog } = B
  const { INK, RED, GOLD, GY, hoplite, phalanx, persian, host, xerxes, cliffs, sea, stonewall, hill, oak, trireme, boatBridge, arrows, stuck, passMap, stele } = TH
  const { tent, fire } = T2
  const fade = (c, a, col = '12,10,8') => { if (a > 0) { c.fillStyle = `rgba(${col},${clamp(a)})`; c.fillRect(0, 0, W, H) } }
  const label = (c, s, x, y, a, o = {}) => window.__vertical ? null : text(c, s, x, y, o.font || F.headI(64, 700), o.col || INK, { alpha: a, stroke: o.stroke ?? C.paper, sw: 8, ...o })

  // ---------- the pass, side on: cliffs behind, the road, the sea in front. Wall at x = WALLX ----------
  const WALLX = 2600
  const cam = (c, o, draw) => view(c, { ...o, cy: GY - 250 / o.s }, draw)
  function pass(c, t, o = {}) {
    const d = o.d ?? 1
    cliffs(c, -2600, 6200, { col: mix('#2a2a33', '#a8977a', d), top: 60 })
    // the road
    c.fillStyle = mix('#1d1b1c', '#b59f78', d); c.fillRect(-2600, GY, 8800, 90)
    if (o.wall !== false) stonewall(c, WALLX, GY + 4, 70, o.wallH || 120, { col: mix('#16151a', '#4a3e33', d), p: o.wallP ?? 1 })
    if (o.springs) for (let k = 0; k < 3; k++) smoke(c, 3100 + k * 260, GY - 40 - ((t * 30 + k * 40) % 120), 70, 0.35, k + 2, '#f3ece0')
  }
  function seaFront(c, t, o = {}) { sea(c, t, -2600, 6200, GY + 88, { col: mix('#151a22', '#6b7a80', o.d ?? 1), glint: (o.d ?? 1) * 0.5 }) }
  // the Persian host in the distance: a cached band of tiny figures with spears, as wide as it needs to be
  const army = () => layer('army', 3600, 420, (x) => {
    const r = rng(480)
    for (let row = 0; row < 14; row++) for (let i = 0; i < 150; i++) {
      const px = i * 24 + r() * 14 + (row % 2) * 10, py = 120 + row * 21, h = 38 + row * 2.4
      x.fillStyle = mix('#5c5045', INK, row / 13)
      x.save(); x.translate(px, py); x.scale(h / 100, h / 100); x.beginPath(); x.arc(0, -90, 8, 0, 7); x.fill(); x.fillRect(-10, -82, 20, 64); x.fillRect(-8, -18, 6, 18); x.fillRect(2, -18, 6, 18)
      x.fillRect(14, -150 - r() * 30, 3, 150); x.restore()
    }
  })

  // =============================== 1. the scout ===============================
  function s1(c, t, q, S) {
    const qWall = q('at the far end') - 0.3, qExp = q('he expects'), qInst = q('instead') - 0.3, qSee = q('they see him') - 0.2, qCount = q('he counts them') - 0.3, qBeh = q('behind that horseman') - 0.4, qFront = q('in front of him') - 0.4, qGate = q('through one narrow gate')
    // a. the horseman rides up the pass
    if (t < qInst) {
      const rx = track(t, [[0, 600], [qWall, 1500, 'l'], [qInst, 1900, 'o']])
      const cx = track(t, [[0, 900], [qWall + 0.2, 1500, 'io'], [qExp + 1.2, 2100, 'io']]), s = track(t, [[0, 0.62], [qWall + 0.2, 0.62], [qExp + 1.2, 0.75, 'io']])
      cam(c, { cx, s: s * 1.55, d: 1 }, () => {
        pass(c, t, {})
        for (let k = 0; k < 12; k++) hoplite(c, WALLX + 120 + k * 46, GY + 14 + (k % 3) * 8, 118, { face: -1, pose: k % 3 ? 'rest' : 'comb', helm: k % 3 !== 0, t: t + k, cloak: true, shield: k % 3 !== 0 })
        horse(c, rx, GY + 40, 1.1, { gait: t * 7, stride: rx < 1890 ? 0.8 : 0.1, rider: (k) => persian(k, 0, 46, 96, { pose: 'stand', shield: false, spear: false }) })
        seaFront(c, t)
      })
      label(c, 'Thermopylae', 300, 160, prog(t, 0.6, 1.4) * (1 - prog(t, qWall - 0.6, qWall)), { align: 'left' })
      text(c, 'Greece, 480 BC', 302, 224, F.bodyI(46), C.red, { align: 'left', alpha: prog(t, 1.0, 1.8) * (1 - prog(t, qWall - 0.6, qWall)) })
      finish(c, t, false); return false
    }
    // b. what he sees: men stretching, and combing their long hair
    if (t < qCount) {
      const turn = prog(t, qSee + 2.2, qSee + 2.8)
      cam(c, { cx: track(t, [[qInst, 2950], [qSee, 3000, 'io']]), s: 1.75, d: 1 }, () => {
        pass(c, t, {})
        const P = ['comb', 'none', 'comb', 'comb', 'none', 'comb', 'comb']
        P.forEach((p, k) => hoplite(c, WALLX + 160 + k * 90, GY + 16 + (k % 2) * 10, 150, { face: k === 3 && t > qSee ? -1 : (k % 2 ? 1 : -1), pose: p, helm: false, arm: p === 'none' ? 1.1 + 0.15 * Math.sin(t * 2 + k) : 0, t: t + k * 0.7, cloak: true, shield: false }))
        // the arms and shields stacked against the wall
        for (let k = 0; k < 6; k++) { c.fillStyle = INK; c.beginPath(); c.arc(WALLX + 60 + k * 26, GY - 20, 21, 0, 7); c.fill() }
        if (t > qSee - 0.5) horse(c, lerp(2300, 2200, turn), GY + 40, 1.1, { face: turn > 0.5 ? -1 : 1, gait: t * 5, stride: 0.2, rider: (k) => persian(k, 0, 46, 96, { pose: 'stand', shield: false, spear: false }) })
        seaFront(c, t)
      })
      finish(c, t, false); return false
    }
    // c. back to the king
    if (t < qBeh) {
      paper(c, t)
      xerxes(c, 1180, 900, 1.35, {})
      persian(c, lerp(500, 820, prog(t, qCount, qCount + 1.4, 'o')), 900, 190, { pose: 'stand', shield: false, spear: false, lean: 0.35 * prog(t, qCount + 1.5, qCount + 2.2), walk: t * 6, stride: 1 - prog(t, qCount + 1.2, qCount + 1.5) })
      c.strokeStyle = INK; c.lineWidth = 4; c.beginPath(); c.moveTo(0, 900); c.lineTo(W, 900); c.stroke()
      label(c, 'Xerxes, King of Persia', 1180, 140, prog(t, qCount + 1.2, qCount + 2), { col: C.gold, stroke: C.paper })
      finish(c, t, false); return false
    }
    // d. behind him, the army; in front, the gate
    const pull = prog(t, qBeh, qFront, 'io')
    view(c, { cx: track(t, [[qBeh, 1200], [qFront, 400, 'io'], [qGate, 2400, 'io']]), cy: track(t, [[qBeh, 640], [qFront, 300, 'io'], [qGate, 600, 'io']]), s: track(t, [[qBeh, 1.2], [qFront, 0.42, 'io'], [qGate, 0.8, 'io']]), d: 1 }, () => {
      pass(c, t, {})
      c.save(); c.globalAlpha = 0.95; c.drawImage(army(), -2500, GY - 380); c.drawImage(army(), -2500 + 3600 * 0.6, GY - 360, 3600 * 0.6, 420 * 0.95); c.restore()
      host(c, 1200, GY + 30, 110, { n: 7, rows: 2, pose: 'stand', walk: 0, stride: 0, seed: 4 })
      phalanx(c, WALLX + 260, GY + 40, 120, { n: 9, ranks: 2, face: -1, cloak: true, t })
      seaFront(c, t)
    })
    typeset(c, 'THREE DAYS', W / 2, 200, F.head(120, 900), C.red, prog(t, qFront + 1.6, qFront + 2.4), { track: 12, stroke: C.paper, sw: 10 })
    finish(c, t, false); return false
  }

  // =============================== 2. the empire ===============================
  function s2(c, t, q, S) {
    const qEmp = q('his empire runs') - 0.3, qTen = q('ten years earlier') - 0.3, qFin = q('xerxes has come') - 0.3, qCross = q('to cross from asia') - 0.3, qStorm = q('when a storm') - 0.3, qWhip = q('whipped'), qHer = q('the greek historian') - 0.3, qToday = q('historians today') - 0.2
    paper(c, t)
    if (t < qEmp) {
      xerxes(c, 960, 960, 1.6, {})
      typeset(c, '480 BC', W / 2, 170, F.head(110, 900), INK, prog(t, S.start - 0.2, S.start + 0.8), { track: 14 })
      label(c, 'Xerxes, King of Persia', W / 2, 250, prog(t, S.start + 1.6, S.start + 2.4), { col: C.gold })
      finish(c, t, false); return false
    }
    if (t < qTen) {
      // a banner of the empire, Egypt to India, with Greece a speck at the far left
      const p = prog(t, qEmp, qEmp + 2.6, 'io')
      c.fillStyle = C.gold; c.globalAlpha = 0.85; c.fillRect(360, 470, 1360 * p, 130); c.globalAlpha = 1
      const names = [['EGYPT', 520], ['BABYLON', 860], ['PERSIA', 1210], ['INDIA', 1560]]
      names.forEach(([s, x], k) => text(c, s, x, 552, F.head(46, 800), INK, { alpha: prog(t, qEmp + 0.4 + k * 0.5, qEmp + 0.9 + k * 0.5), track: 6 }))
      c.fillStyle = INK; c.fillRect(200, 470, 110, 130); text(c, 'GREECE', 255, 650, F.sc(40), C.red, { alpha: prog(t, qEmp + 2.6, qEmp + 3.2) })
      label(c, 'the largest empire the world had known', W / 2, 760, prog(t, qEmp + 2.8, qEmp + 3.6), { font: F.bodyI(52) })
      finish(c, t, false); return false
    }
    if (t < qFin) {
      // Marathon: a Greek line drives the Persians into the sea
      const p = prog(t, qTen + 1.5, qFin, 'io')
      view(c, { cx: 960, cy: 560, s: 0.9, d: 1 }, () => {
        c.fillStyle = '#b59f78'; c.fillRect(-600, GY, 3200, 90)
        host(c, 700 - p * 300, GY + 30, 120, { n: 8, rows: 2, face: -1, pose: 'flee', t, stride: 0.9 * p, walk: t * 7 })
        phalanx(c, 1300 - p * 280, GY + 40, 120, { n: 6, ranks: 2, face: -1, t, walk: t * 4, stride: 0.5 * p, thrust: 0.6 })
        sea(c, t, -600, 2600, GY + 88, { col: '#6b7a80' })
      })
      label(c, 'Marathon, 490 BC', W / 2, 170, prog(t, qTen + 1.2, qTen + 2))
      finish(c, t, false); return false
    }
    if (t < qCross) {
      xerxes(c, 960, 960, 1.6, { stand: 0.55 * prog(t, qFin, qFin + 0.8, 'o') })
      typeset(c, 'TO FINISH THE JOB', W / 2, 190, F.head(96, 900), C.red, prog(t, qFin + 0.3, qFin + 1.3), { track: 10 })
      finish(c, t, false); return false
    }
    if (t < qHer) {
      // the bridge of boats across the Hellespont; the storm; the sea whipped
      const storm = bump(t, qStorm, qWhip - qStorm + 0.6)
      view(c, { cx: 960, cy: 600, s: 1, d: 1 - 0.55 * storm }, () => {
        sea(c, t * (1 + 3 * storm), -400, 2400, 640, { col: mix('#6b7a80', '#2c3640', storm), glint: 0.4 * (1 - storm) })
        c.fillStyle = '#9b8b6c'; c.fillRect(-400, 560, 520, 120); c.fillRect(1800, 560, 520, 120)
        text(c, 'ASIA', 1980, 540, F.sc(44), INK); text(c, 'EUROPE', -80, 540, F.sc(44), INK)
        const built = t < qStorm + 0.8 ? 1 : t < qWhip ? 0 : prog(t, qWhip + 2.5, qHer)
        if (built > 0) { c.save(); c.globalAlpha = built; boatBridge(c, 140, 1800, 690, 1.0, { t }); c.restore() }
        if (built > 0.9) for (let k = 0; k < 26; k++) { const x = 1760 - ((t * 60 + k * 64) % 1640); person(c, x, 676, 34, { hat: 'none', walk: t * 8 + k, stride: 0.7, face: -1 }) }
        if (t > qWhip - 0.6) for (let k = 0; k < 3; k++) persian(c, 1900 + k * 90, 568, 130, { face: -1, pose: 'whip', t: t + k * 0.4, shield: false })
      })
      if (t > qWhip) { const n = Math.min(300, Math.floor(prog(t, qWhip, qHer - 0.4) * 300)); typeset(c, String(n), W / 2, 230, F.head(150, 900), C.red, 1, { track: 6 }); label(c, 'lashes, for the sea', W / 2, 300, prog(t, qWhip + 0.4, qWhip + 1.2), { font: F.bodyI(52) }) }
      finish(c, t, storm > 0.5); return storm > 0.5
    }
    // the numbers: what Herodotus said, and what historians think now
    typeset(c, 'Herodotus:', W / 2, 330, F.bodyI(60), INK, prog(t, qHer, qHer + 0.6))
    typeset(c, '2,641,610', W / 2, 500, F.head(170, 900), INK, prog(t, qHer + 1.2, qHer + 2.4), { track: 8 })
    if (t > qToday) {
      const st = prog(t, qToday, qToday + 0.6); c.strokeStyle = C.red; c.lineWidth = 12; c.beginPath(); c.moveTo(560, 450); c.lineTo(560 + 800 * st, 450); c.stroke()
      typeset(c, 'Today: about 100,000 to 200,000', W / 2, 700, F.head(76, 800), C.red, prog(t, qToday + 1.2, qToday + 2.4))
      label(c, 'still the biggest army in the world', W / 2, 800, prog(t, qToday + 4.0, qToday + 4.8), { font: F.bodyI(52) })
    }
    finish(c, t, false); return false
  }

  // =============================== 3. the Greeks ===============================
  const CITIES = [['ATHENS', 1180, 640], ['SPARTA', 760, 900], ['THEBES', 1060, 420], ['CORINTH', 880, 640], ['ARGOS', 760, 720], ['THESPIAE', 960, 390], ['PHOCIS', 820, 300], ['MEGARA', 1010, 590]]
  function s3(c, t, q, S) {
    const qGr = q('greece was not') - 0.3, qEarth = q('some of them') - 0.3, qSp = q('sparta had') - 0.3, qKing = q('so one of its') - 0.3, qLeo = q('his name was'), qPick = q('he picked') - 0.3, qMen = q('men whose') - 0.3, qWay = q('on the way north') - 0.3, q7 = q('they were about')
    if (t < qSp) {
      paper(c, t)
      CITIES.forEach(([n, x, y], k) => {
        const a = prog(t, S.start - 0.2 + k * 0.25, S.start + 0.3 + k * 0.25), gold = t > qEarth + 1.2 && (n === 'THEBES' || n === 'ARGOS') ? prog(t, qEarth + 1.2, qEarth + 2) : 0
        c.save(); c.globalAlpha = a; bank(c, x * 1.4 - 380, y * 1.05, 120, 100, { cols: 4, fill: mix(C.paper2, C.gold, gold), col: INK }); c.restore()
        text(c, n, x * 1.4 - 380, y * 1.05 + 40, F.sc(34), INK, { alpha: a })
      })
      // the quarrels: lines flaring between cities
      if (t > qGr) { const r = rng(Math.floor(t * 2)); c.strokeStyle = C.red; c.lineWidth = 4; c.setLineDash([12, 10]); for (let k = 0; k < 4; k++) { const a = CITIES[Math.floor(r() * 8)], b = CITIES[Math.floor(r() * 8)]; c.globalAlpha = 0.7 * (1 - prog(t, qEarth, qEarth + 0.5)); c.beginPath(); c.moveTo(a[1] * 1.4 - 380, a[2] * 1.05 - 60); c.lineTo(b[1] * 1.4 - 380, b[2] * 1.05 - 60); c.stroke() } c.setLineDash([]); c.globalAlpha = 1 }
      if (t > qEarth) label(c, 'earth and water', W / 2, 160, prog(t, qEarth + 2.2, qEarth + 3), { font: F.bodyI(60), col: C.gold })
      finish(c, t, false); return false
    }
    if (t < qKing) {
      paper(c, t)
      bank(c, W / 2, 760, 520, 400, { cols: 6, fill: C.paper2, col: INK })
      for (let k = 0; k < 10; k++) hoplite(c, 520 + k * 98 + (k > 4 ? 120 : 0), 980, 150, { pose: 'rest', cloak: true, t })
      label(c, 'Sparta', W / 2, 200, prog(t, qSp, qSp + 0.8), { font: F.head(90, 900) })
      text(c, 'a holy festival: the army may not march', W / 2, 280, F.bodyI(50), C.red, { alpha: prog(t, qSp + 3.2, qSp + 4) })
      finish(c, t, false); return false
    }
    if (t < qWay) {
      paper(c, t)
      c.strokeStyle = INK; c.lineWidth = 4; c.beginPath(); c.moveTo(0, 900); c.lineTo(W, 900); c.stroke()
      if (t < qPick) {
        hoplite(c, lerp(500, 960, prog(t, qKing, qLeo, 'o')), 900, 330, { pose: 'march', walk: t * 4, stride: 1 - prog(t, qLeo - 0.4, qLeo), cloak: true, t })
        label(c, 'Leonidas', W / 2, 220, prog(t, qLeo, qLeo + 0.8), { font: F.head(100, 900) })
        text(c, 'about sixty years old', W / 2, 300, F.bodyI(52), C.red, { alpha: prog(t, qLeo + 1.6, qLeo + 2.4) })
      } else {
        // the three hundred, each with a son at home; the boys stay as the men march away
        const go = prog(t, qMen, qMen + 3.5, 'i')
        for (let k = 0; k < 9; k++) {
          const x = 180 + k * 190
          person(c, x + 40, 900, 92, { hat: 'none', face: -1, col: C.ink2, arm: go > 0.2 ? 0.9 : 0 })
          hoplite(c, x + go * 2200, 900, 210, { pose: 'march', walk: t * 4 + k, stride: go > 0 ? 0.9 : 0, cloak: true, t: t + k })
        }
        typeset(c, '300', W / 2, 260, F.head(160, 900), C.red, prog(t, qPick, qPick + 0.8), { track: 10 })
        label(c, 'every one with a son at home', W / 2, 340, prog(t, qPick + 1.6, qPick + 2.4), { font: F.bodyI(52) })
      }
      finish(c, t, false); return false
    }
    // the column grows on the way north
    const n = Math.round(lerp(300, 7000, prog(t, qWay + 1.0, q7 + 0.5, 'io')))
    cam(c, { cx: track(t, [[qWay, 1100], [q7 + 2, 600, 'io']]), s: track(t, [[qWay, 1.3], [q7 + 2, 0.75, 'io']]), d: 1 }, () => {
      c.fillStyle = '#b59f78'; c.fillRect(-2000, GY, 6000, 90)
      const m = Math.round(lerp(8, 60, prog(t, qWay + 1.0, q7 + 0.5)))
      for (let k = 0; k < m; k++) hoplite(c, 1500 - k * 52 + ((t * 40) % 52), GY + 30 + (k % 3) * 10, 100, { pose: 'march', walk: t * 5 + k, stride: 0.9, cloak: k < 8, t: t + k })
    })
    typeset(c, n.toLocaleString('en-US'), W / 2, 230, F.head(150, 900), INK, 1, { track: 8 })
    finish(c, t, false); return false
  }

  // =============================== 4. the hot gates ===============================
  function s4(c, t, q, S) {
    const qOne = q('on one side') - 0.3, qBet = q('between them'), qNar = q('at its narrowest') - 0.3, qWall = q('the greeks rebuilt') - 0.3, qTight = q('in a space') - 0.3, qOnly = q('only the ones') - 0.2
    if (t < qTight) {
      paper(c, t)
      const z = track(t, [[S.start, 1.0], [qNar, 1.0], [qNar + 2, 1.7, 'io']])
      c.save(); c.translate(W / 2, H / 2); c.scale(z, z); c.translate(-lerp(960, 1000, prog(t, qNar, qNar + 2)), -lerp(540, 580, prog(t, qNar, qNar + 2)))
      passMap(c, t, { wall: t > qWall + 0.5 })
      for (let k = 0; k < 3; k++) smoke(c, 1060 + k * 50, 560 - ((t * 20 + k * 30) % 60), 22, 0.5, k + 3, '#f8f2e6')
      c.restore()
      label(c, 'Thermopylae', W / 2, 140, prog(t, S.start, S.start + 0.8), { font: F.head(96, 900) })
      text(c, '“the hot gates”', W / 2, 210, F.bodyI(56), C.red, { alpha: prog(t, S.start + 2.0, S.start + 2.8) })
      text(c, 'mountains', 400, 320, F.headI(54), INK, { alpha: prog(t, qOne + 0.5, qOne + 1.1) * (1 - prog(t, qNar, qNar + 0.5)), stroke: C.paper, sw: 8 })
      text(c, 'the sea', 1500, 900, F.headI(54), INK, { alpha: prog(t, qOne + 2.0, qOne + 2.6) * (1 - prog(t, qNar, qNar + 0.5)), stroke: C.paper, sw: 8 })
      text(c, 'the road south', 400, 700, F.headI(48), C.red, { alpha: prog(t, qBet + 0.5, qBet + 1.1) * (1 - prog(t, qNar, qNar + 0.5)), stroke: C.paper, sw: 8 })
      text(c, 'about 100 yards', W / 2, 980, F.head(64, 800), C.red, { alpha: prog(t, qNar + 1.5, qNar + 2.2) * (1 - prog(t, qWall, qWall + 0.4)), stroke: C.paper, sw: 8 })
      text(c, 'the wall', W / 2 + 120, 980, F.head(64, 800), INK, { alpha: prog(t, qWall + 0.8, qWall + 1.4), stroke: C.paper, sw: 8 })
      finish(c, t, false); return false
    }
    // in a space that tight, only the front rank can fight
    cam(c, { cx: 2100, s: 1.3, d: 1 }, () => {
      pass(c, t, { springs: true })
      host(c, 1550, GY + 30, 120, { n: 10, rows: 5, pose: 'charge', t, stride: 0.2, walk: t * 2 })
      phalanx(c, 2420, GY + 40, 125, { n: 6, ranks: 3, face: -1, cloak: true, t, thrust: 0.6 })
      seaFront(c, t)
    })
    if (t > qOnly - 0.2) { c.save(); c.globalAlpha = 0.55 * prog(t, qOnly - 0.2, qOnly + 0.4); c.fillStyle = '#efe6d2'; c.fillRect(0, 0, 760, H); c.restore() }
    label(c, 'only the front rank fights', W / 2, 170, prog(t, qOnly, qOnly + 0.8))
    finish(c, t, false); return false
  }

  // =============================== 5. the wait ===============================
  function s5(c, t, q, S) {
    const qSure = q('he was sure') - 0.3, qNot = q('they did not run'), qStory = q('a story told') - 0.3, qHand = q('hand over'), qLeo = q('and leonidas') - 0.2, qCome = q('come and take them'), qHer = q('herodotus tells') - 0.3, qSun = q('block out the sun'), qGood = q('a spartan named') - 0.2, qShade = q('then we will fight')
    if (t < qStory) {
      // four days and nights over the camp
      const day = clamp((t - S.start) / (qStory - S.start)) * 4, ph = day % 1, d = 0.5 + 0.5 * Math.cos(ph * Math.PI * 2 - Math.PI)
      cam(c, { cx: 1700, s: 0.85, d: 0.1 + 0.85 * d }, () => {
        pass(c, t, { d: 0.15 + 0.85 * d })
        for (let k = 0; k < 9; k++) tent(c, 300 + k * 190, GY + 20, 0.6, { col: mix('#0a0b10', '#3a312a', d), lit: (1 - d) * 0.8 })
        for (let k = 0; k < 5; k++) if (d < 0.5) fire(c, 400 + k * 330, GY + 40, 0.6, t, (0.5 - d) * 2)
        phalanx(c, WALLX + 220, GY + 40, 110, { n: 7, ranks: 2, face: -1, cloak: true, t, col: mix('#08090c', INK, d) })
        seaFront(c, t, { d: 0.15 + 0.85 * d })
      })
      typeset(c, 'DAY ' + Math.min(4, Math.floor(day) + 1), 180, 140, F.head(70, 900), d > 0.4 ? INK : C.paper, 1, { align: 'left', track: 8 })
      if (t > qNot) label(c, 'They did not run.', W / 2, 960, prog(t, qNot, qNot + 0.6), { font: F.head(70, 900), col: C.red })
      const dk = d < 0.4; finish(c, t, dk); return dk
    }
    paper(c, t)
    if (t < qHer) {
      typeset(c, '“Hand over your weapons.”', W / 2, 420, F.headI(84, 700), INK, prog(t, qHand, qHand + 1.2))
      typeset(c, '“Come and take them.”', W / 2, 640, F.head(110, 900), C.red, prog(t, qCome, qCome + 1.0))
      text(c, 'ΜΟΛΩΝ ΛΑΒΕ', W / 2, 760, F.sc(56), INK, { alpha: prog(t, qCome + 1.4, qCome + 2.2), track: 14 })
      text(c, 'as Plutarch tells it, centuries later', W / 2, 960, F.bodyI(40), C.ink3, { alpha: prog(t, qStory + 0.6, qStory + 1.4) })
      finish(c, t, false); return false
    }
    // the arrows that would block out the sun
    const dim = prog(t, qSun - 0.6, qSun + 1.2)
    cam(c, { cx: 2500, s: 1.2, d: 1 - 0.55 * dim }, () => {
      pass(c, t, { d: 1 - 0.55 * dim })
      c.fillStyle = C.gold2; c.globalAlpha = 1 - 0.6 * dim; c.beginPath(); c.arc(2300, 200, 70, 0, 7); c.fill(); c.globalAlpha = 1
      phalanx(c, WALLX + 220, GY + 40, 120, { n: 6, ranks: 2, face: -1, cloak: true, t })
      seaFront(c, t, { d: 1 - 0.55 * dim })
    })
    arrows(c, t, qSun - 1.2, { n: 220, waves: 6, every: 1.1, sx: -300, sw: 300, sy: 900, ex: 1700, ew: 600, ey: 900, top: 60, dur: 1.8 })
    label(c, '“Good. Then we will fight in the shade.”', W / 2, 980, prog(t, qShade, qShade + 1.2), { font: F.headI(66, 700) })
    text(c, 'Dieneces of Sparta', W / 2, 1040, F.bodyI(40), C.red, { alpha: prog(t, qGood + 0.6, qGood + 1.4), stroke: C.paper, sw: 6 })
    finish(c, t, false); return false
  }

  // =============================== 6. day one ===============================
  function s6(c, t, q, S) {
    const qWaves = q('they came up') - 0.3, qMet = q('the greeks met') - 0.3, qLong = q('their spears were'), qTrick = q('the spartans had') - 0.3, qCharge = q('and when the persians') - 0.3, qMede = q('the medes broke') - 0.3, qImm = q('the immortals'), qNo = q('they did no better') - 0.2, qThr = q('herodotus says that') - 0.3
    if (t < qWaves) {
      paper(c, t); xerxes(c, 960, 960, 1.5, { stand: 0.2 * bump(t, S.start + 1.5, 1.2) })
      label(c, 'Day five: the Medes go in', W / 2, 180, prog(t, S.start + 0.4, S.start + 1.2))
      finish(c, t, false); return false
    }
    if (t < qThr) {
      // the fight at the wall. Feigned retreat between qTrick and qMede; the Immortals after qImm.
      const back = t > qTrick + 1.0 && t < qMede ? bump(t, qTrick + 1.0, qMede - qTrick - 1.0) : 0, spin = t > qCharge + 2.4 && t < qMede
      const imm = t > qImm - 0.5
      cam(c, { cx: 2120 + back * 140, s: track(t, [[qWaves, 1.15], [qMet, 1.6, 'io'], [qMede, 1.6], [qImm, 1.3, 'io']]), d: 1 }, () => {
        pass(c, t, {})
        const push = imm ? 0 : clamp(0.3 * Math.sin(t * 1.3)), surge = back * 260
        host(c, 1880 + surge + push * 30, GY + 30, 125, { n: 8, rows: 4, pose: 'charge', t, kind: imm ? 'immortal' : 'mede', stride: 0.6 + back, walk: t * (6 + back * 4), seed: imm ? 9 : 7, down: (i, k) => k === 0 && (i + Math.floor(t * 0.8)) % 4 === 0 ? prog((t * 0.8) % 1, 0, 0.4) : 0 })
        phalanx(c, 2260 + back * 300, GY + 40, 130, { n: 6, ranks: 3, face: back > 0.05 && !spin ? 1 : -1, cloak: true, t, thrust: spin || back < 0.05 ? 0.8 : 0, pose: back > 0.05 && !spin ? 'rest' : undefined, walk: t * 6, stride: back > 0.05 ? 0.9 : 0 })
        for (let k = 0; k < 7; k++) persian(c, 2000 + k * 34, GY + 60 + (k % 3) * 8, 120, { down: 1, face: k % 2 ? 1 : -1, col: '#2a221c' })
        seaFront(c, t)
      })
      if (t > qLong - 0.2 && t < qTrick) label(c, 'longer spears, heavier armor', W / 2, 160, prog(t, qLong, qLong + 0.8) * (1 - prog(t, qTrick - 0.5, qTrick)))
      if (t > qTrick + 0.4 && t < qMede) label(c, 'the false retreat', W / 2, 160, prog(t, qTrick + 0.4, qTrick + 1.2) * (1 - prog(t, qMede - 0.5, qMede)), { col: C.red })
      if (imm) { label(c, 'the Immortals', W / 2, 160, prog(t, qImm, qImm + 0.8) * (1 - prog(t, qNo + 1.2, qNo + 1.8)), { col: C.gold }); text(c, '10,000', W / 2, 240, F.head(70, 900), INK, { alpha: prog(t, qImm + 0.8, qImm + 1.6) * (1 - prog(t, qNo + 1.2, qNo + 1.8)), stroke: C.paper, sw: 8 }) }
      finish(c, t, false); return false
    }
    // three times the king leapt up from his throne
    paper(c, t)
    const leaps = [qThr + 2.0, qThr + 3.6, qThr + 5.2], st = Math.max(...leaps.map(a => bump(t, a, 1.2)))
    xerxes(c, 960, 960, 1.6, { stand: st })
    const n = leaps.filter(a => t > a).length
    if (n) typeset(c, ['ONE', 'TWO', 'THREE'][n - 1], W / 2, 200, F.head(110, 900), C.red, 1, { track: 12 })
    finish(c, t, false); return false
  }

  // =============================== 7. day two ===============================
  function s7(c, t, q, S) {
    const qThought = q('he thought') - 0.3, qTurns = q('the greeks took turns') - 0.3, qSun = q('by sundown') - 0.3, qStuck = q('the biggest army') - 0.3
    const d = 1 - 0.75 * prog(t, qSun, qStuck + 2)
    if (t < qStuck) {
      const CITY = ['SPARTA', 'THESPIAE', 'CORINTH', 'ARCADIA', 'PHOCIS']
      const shift = Math.floor(clamp((t - qTurns) / (qSun - qTurns + 0.01)) * 4.99), sh = t > qTurns ? ((t - qTurns) / ((qSun - qTurns) / 5)) % 1 : 0
      cam(c, { cx: 2250, s: 1.45, d }, () => {
        pass(c, t, { d })
        host(c, 1900, GY + 30, 125, { n: 8, rows: 4, pose: 'charge', t, stride: 0.5, walk: t * 5, col: mix('#0e0d0f', INK, d) })
        if (t > qTurns) {
          const swap = clamp((sh - 0.75) * 4)
          phalanx(c, 2280 + swap * 300, GY + 40, 128, { n: 6, ranks: 2, face: -1, cloak: shift === 0, t, thrust: 0.7 * (1 - swap), col: mix('#0e0d0f', INK, d) })
          phalanx(c, 2580 - swap * 300, GY + 40, 128, { n: 6, ranks: 2, face: -1, cloak: shift === 4, t, col: mix('#0e0d0f', INK, d) })
        } else phalanx(c, 2280, GY + 40, 128, { n: 6, ranks: 3, face: -1, cloak: true, t, thrust: 0.7 })
        seaFront(c, t, { d })
      })
      if (t > qTurns) label(c, CITY[shift], W / 2, 170, prog(t, qTurns, qTurns + 0.6), { font: F.sc(70), col: d > 0.5 ? INK : C.paper, stroke: d > 0.5 ? C.paper : INK })
      else label(c, 'Day six', W / 2, 170, prog(t, S.start, S.start + 0.8))
      finish(c, t, d < 0.45); return d < 0.45
    }
    paper(c, t, mix(C.paper, '#c7a77a', 0.5)); xerxes(c, 960, 960, 1.6, { stand: 0 })
    label(c, 'stuck at a gate', W / 2, 180, prog(t, qStuck + 1.0, qStuck + 1.8), { col: C.red })
    finish(c, t, false); return false
  }

  window.SCENES = [s1, s2, s3, s4, s5, s6, s7]
  window.THA = { pass, seaFront, army, label, fade, WALLX, cam }
})()
