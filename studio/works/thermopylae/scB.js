// scB.js: scenes 8-13 of Thermopylae: the goat path, the choice, the last morning, the hill, after, the stone.
(function () {
  const { clamp, lerp, EZ, prog, bump, rng, noise, track, mix } = K
  const { W, H, C, F, paper, finish, hatch, text, typeset, rule, person, glow, tw, bank } = L
  const { view, smoke } = B
  const { INK, RED, GOLD, GY, hoplite, phalanx, persian, host, xerxes, cliffs, sea, stonewall, hill, oak, trireme, boatBridge, arrows, stuck, passMap, stele } = TH
  const { tent, fire, night, stars } = T2
  const { pass, seaFront, label, fade, WALLX, cam } = THA
  // a hooded man: Ephialtes
  function hooded(c, x, y, h, o = {}) {
    person(c, x, y, h, { hat: 'none', face: o.face || 1, col: o.col || INK, walk: o.walk, stride: o.stride, arm: o.arm || 0, lean: 0.08 })
    const s = h / 100; c.save(); c.translate(x, y); c.scale(s * (o.face || 1), s); c.fillStyle = o.col || INK
    c.beginPath(); c.moveTo(-10, -78); c.quadraticCurveTo(-13, -104, 2, -104); c.quadraticCurveTo(14, -103, 11, -86); c.lineTo(6, -84); c.quadraticCurveTo(6, -96, 0, -96); c.lineTo(-2, -78); c.closePath(); c.fill(); c.restore()
  }
  const NIGHT = { top: '#0b0e16', mid: '#18203a', low: '#232b45' }

  // =============================== 8. the goat path ===============================
  function s8(c, t, q, S) {
    const qHope = q('he was hoping') - 0.3, qPath = q('there was a path') - 0.3, qSent = q('xerxes sent the immortals') - 0.3, qKnew = q('leonidas knew') - 0.3, qDawn = q('just before dawn') - 0.3, qFeet = q('thousands of feet') - 0.2, qRan = q('the phocians ran') - 0.3, qLet = q('they let a few') - 0.3
    if (t < qPath) {
      night(c, t, NIGHT)
      c.fillStyle = '#07080c'; c.fillRect(0, 880, W, 200)
      tent(c, 1180, 890, 2.2, { lit: 1, col: '#07080c' })
      hooded(c, lerp(300, 820, prog(t, S.start, S.start + 2.6, 'o')), 890, 230, { walk: t * 5, stride: 1 - prog(t, S.start + 2.2, S.start + 2.6), col: '#07080c' })
      label(c, 'Ephialtes', W / 2, 180, prog(t, S.start + 2.4, S.start + 3.2), { col: C.paper, stroke: INK })
      if (t > qHope) { const r = rng(5); for (let k = 0; k < 12; k++) { const a = prog(t, qHope + 0.6 + k * 0.08, qHope + 0.9 + k * 0.08); c.fillStyle = C.gold2; c.globalAlpha = a; c.beginPath(); c.ellipse(1010 + r() * 120, 870 + r() * 16, 12, 5, 0, 0, 7); c.fill() } c.globalAlpha = 1 }
      finish(c, t, true); return true
    }
    if (t < qDawn) {
      paper(c, t)
      passMap(c, t, { wall: true, path: prog(t, qPath + 0.4, qPath + 3.6, 'io'), dot: t > qSent ? prog(t, qSent + 0.8, qDawn + 6, 'l') * 0.62 : 0 })
      text(c, 'the goat path', 960, 120, F.head(80, 900), C.red, { alpha: prog(t, qPath + 1, qPath + 1.8), stroke: C.paper, sw: 10 })
      text(c, 'the wall', 1060, 680, F.headI(44), INK, { alpha: 0.8, stroke: C.paper, sw: 6 })
      if (t > qSent) text(c, 'the Immortals, by night', 520, 440, F.headI(48), C.gold, { alpha: prog(t, qSent + 0.6, qSent + 1.4), stroke: C.paper, sw: 6 })
      if (t > qKnew) { const a = prog(t, qKnew + 1.0, qKnew + 1.8); c.fillStyle = INK; c.globalAlpha = a; for (let k = 0; k < 9; k++) { c.beginPath(); c.arc(1060 + (k % 3) * 18, 210 + Math.floor(k / 3) * 18, 7, 0, 7); c.fill() } c.globalAlpha = 1; text(c, '1,000 Phocians', 1080, 170, F.headI(46), INK, { alpha: a, stroke: C.paper, sw: 6 }) }
      finish(c, t, false); return false
    }
    // before dawn, in the oak woods: the Immortals file past the Phocians on their hill
    const dawn = prog(t, qDawn, S.end + 1, 'i')
    night(c, t, { top: mix('#0b0e16', '#3b3550', dawn), mid: mix('#18203a', '#a7766a', dawn), low: mix('#232b45', '#e2b98a', dawn) })
    c.save(); c.translate(0, 0)
    hill(c, 1500, 900, 900, 380, '#0a0b10')
    for (let k = 0; k < 10; k++) oak(c, 80 + k * 200 + (k % 2) * 60, 905 + (k % 3) * 12, 1.6 + (k % 3) * 0.3, '#0a0b10', k)
    c.fillStyle = '#07080c'; c.fillRect(0, 900, W, 200)
    for (let k = 0; k < 9; k++) hoplite(c, 1380 + k * 30, 900 - 260 * Math.sin(Math.PI * clamp((1380 + k * 30 - 1050) / 900)) + 10, 90, { face: -1, pose: t > qRan ? 'guard' : 'rest', col: '#0a0b10', cloak: false, t })
    const walk = (t - qDawn) * 70
    for (let k = 0; k < 18; k++) { const x = -200 + ((walk + k * 120) % 2400); persian(c, x, 935, 150, { kind: 'immortal', pose: 'stand', walk: t * 6 + k, stride: 0.9, col: '#05060a', t }) }
    c.restore()
    if (t > qLet) arrows(c, t, qLet + 0.6, { n: 14, waves: 2, every: 1.0, sx: 300, sw: 900, sy: 900, ex: 1350, ew: 300, ey: 700, top: 500, dur: 1.2, col: '#05060a' })
    if (t > qFeet - 0.3 && t < qRan) { const r = rng(Math.floor(t * 8)); c.fillStyle = 'rgba(200,170,120,0.5)'; for (let k = 0; k < 18; k++) { c.beginPath(); c.ellipse(r() * W, 920 + r() * 40, 7, 3, r() * 3, 0, 7); c.fill() } }
    label(c, 'Thousands of feet, in the fallen leaves', W / 2, 170, prog(t, qFeet, qFeet + 0.8) * (1 - prog(t, qRan - 0.4, qRan)), { col: C.paper, stroke: INK, font: F.headI(60, 700) })
    finish(c, t, true); return true
  }

  // =============================== 9. the choice ===============================
  function s9(c, t, q, S) {
    const qCouncil = q('the greeks held') - 0.3, qSent = q('leonidas sent them') - 0.3, qStay = q('he would stay'), q700 = q('700 men'), q400 = q('so did 400'), qHer = q('herodotus gives') - 0.3, qCity = q('its city')
    if (t < qHer) {
      paper(c, t, mix(C.paper, '#e7c99a', 0.5))
      c.strokeStyle = INK; c.lineWidth = 4; c.beginPath(); c.moveTo(0, 900); c.lineTo(W, 900); c.stroke()
      if (t < qCouncil) {
        hoplite(c, lerp(-100, 900, prog(t, S.start, S.start + 2.2, 'o')), 900, 220, { pose: 'march', walk: t * 9, stride: 1.2 * (1 - prog(t, S.start + 1.8, S.start + 2.2)), helm: true, shield: false, t })
        hoplite(c, 1180, 900, 250, { face: -1, pose: 'rest', cloak: true, t })
        label(c, 'Dawn, the third day', W / 2, 180, prog(t, S.start + 0.3, S.start + 1.1))
        finish(c, t, false); return false
      }
      // most go home; three groups stay
      const leave = prog(t, qSent, qSent + 3.2, 'i')
      const groups = [[-1, 300, true, qStay, 'SPARTA'], [-1, 700, false, q700, 'THESPIAE'], [-1, 400, false, q400, 'THEBES']]
      for (let k = 0; k < 16; k++) { const x = 260 + k * 92; hoplite(c, x - leave * 1400, 900, 170, { face: -1, pose: 'march', walk: t * 5 + k, stride: leave > 0 ? 0.9 : 0, t: t + k, col: mix(INK, '#8a7b66', leave) }) }
      groups.forEach(([f, n, cl, at, name], g) => {
        if (t < at - 0.3) return
        const a = prog(t, at - 0.3, at + 0.5)
        for (let k = 0; k < 4; k++) { c.save(); c.globalAlpha = a; hoplite(c, 1180 + g * 230 + k * 40, 900, 190 - g * 6, { face: -1, pose: 'rest', cloak: cl, t: t + k }); c.restore() }
        text(c, n.toLocaleString('en-US'), 1240 + g * 230, 440, F.head(80, 900), cl ? C.red : INK, { alpha: a })
        text(c, name, 1240 + g * 230, 490, F.sc(36), INK, { alpha: a })
      })
      finish(c, t, false); return false
    }
    // the oracle: the city, or the king
    paper(c, t, '#e8dcc0')
    smoke(c, 960, 640 - (t % 3) * 10, 180, 0.6, 2, '#bfb39a')
    hooded(c, 960, 900, 260, { face: -1 })
    c.strokeStyle = INK; c.lineWidth = 4; c.beginPath(); c.moveTo(0, 900); c.lineTo(W, 900); c.stroke()
    text(c, 'Its city.', 560, 420, F.head(96, 900), INK, { alpha: prog(t, qCity, qCity + 0.6) })
    text(c, 'Or its king.', 1360, 420, F.head(96, 900), C.red, { alpha: prog(t, qCity + 1.1, qCity + 1.7) })
    label(c, 'the oracle at Delphi', W / 2, 180, prog(t, qHer + 2.4, qHer + 3.2), { font: F.bodyI(52) })
    finish(c, t, false); return false
  }

  // =============================== 10. the last morning ===============================
  function s10(c, t, q, S) {
    const qOut = q('they marched out') - 0.3, qWhip = q('behind the persian lines') - 0.3, qSea = q('men were shoved') - 0.3, qSw = q('when the greek spears') - 0.3, qBro = q('two of xerxes') - 0.3, qFell = q('and then leonidas fell'), qBody = q('the fight over') - 0.3, qFour = q('four times')
    const adv = prog(t, S.start + 1, qWhip, 'io')
    const leoDown = prog(t, qFell + 0.4, qFell + 1.4, 'i')
    cam(c, { cx: track(t, [[S.start, 2400], [qWhip, 1900, 'io'], [qSea, 1750], [qSea + 3, 1750], [qFell, 2000, 'io']]), s: track(t, [[S.start, 1.1], [qWhip, 1.35, 'io'], [qFell, 1.8, 'io'], [qBody + 1, 1.4, 'io']]), d: 1 }, () => {
      pass(c, t, {})
      // officers with whips behind their own line
      for (let k = 0; k < 4; k++) persian(c, 1130 + k * 130, GY + 24, 128, { pose: 'whip', t: t + k * 0.6, shield: false, kind: 'mede' })
      host(c, 1560, GY + 30, 125, { n: 8, rows: 3, pose: 'charge', t, stride: 0.5, walk: t * 5, down: (i, k) => k === 0 && (i + Math.floor(t)) % 3 === 0 ? prog(t % 1, 0, 0.35) : 0 })
      // the two royal brothers: gold trim, they fall
      if (t > qBro - 1) for (let k = 0; k < 2; k++) { persian(c, 1820 + k * 60, GY + 44, 140, { pose: 'charge', down: prog(t, qBro + 1 + k * 0.7, qBro + 1.8 + k * 0.7, 'i'), col: INK }); c.fillStyle = GOLD; c.globalAlpha = 1 - prog(t, qBro + 1 + k * 0.7, qBro + 1.8 + k * 0.7); c.fillRect(1814 + k * 60, GY - 96, 14, 6); c.globalAlpha = 1 }
      const spears = t < qSw + 0.6
      phalanx(c, lerp(2420, 2050, adv), GY + 40, 130, { n: 7, ranks: 3, face: -1, cloak: true, t, thrust: spears ? 0.8 : 0.4, pose: spears ? undefined : 'none' })
      // Leonidas, front and centre
      hoplite(c, lerp(2420, 2050, adv) - 40, GY + 58, 150, { face: -1, pose: spears ? 'thrust' : 'none', thrust: 0.6 + 0.4 * Math.sin(t * 3), cloak: true, t, down: leoDown, arm: 0.7 })
      seaFront(c, t)
      // men pushed off the road into the sea
      if (t > qSea - 0.5) for (let k = 0; k < 6; k++) { const st = qSea + k * 0.55, p = clamp((t - st) / 1.4); if (p > 0) { c.save(); c.globalAlpha = 1 - prog(p, 0.7, 1); persian(c, 1500 + k * 70, GY + 70 + p * 120, 120, { down: 0.5 + p * 0.5, face: k % 2 ? 1 : -1, shield: false, spear: false }); c.restore() } }
    })
    if (t > qWhip && t < qSea) label(c, 'driven forward with whips', W / 2, 170, prog(t, qWhip + 0.6, qWhip + 1.2) * (1 - prog(t, qSea - 0.4, qSea)))
    if (t > qFell) label(c, 'Leonidas', W / 2, 170, prog(t, qFell + 0.8, qFell + 1.6) * (1 - prog(t, qBody - 0.3, qBody)), { font: F.head(90, 900), col: C.red })
    if (t > qFour) { const n = Math.min(4, 1 + Math.floor((t - qFour) / 0.7)); typeset(c, ['ONE', 'TWO', 'THREE', 'FOUR'][n - 1], W / 2, 190, F.head(100, 900), C.red, 1, { track: 10, stroke: C.paper, sw: 10 }) }
    finish(c, t, false); return false
  }

  // =============================== 11. the hill ===============================
  function s11(c, t, q, S) {
    const qPull = q('the last greeks') - 0.3, qTheb = q('the thebans walked') - 0.3, qRest = q('the rest fought') - 0.3, qBack = q('the persians did not') - 0.3, qShot = q('they stood back'), qNone = q('until no one')
    const HX = 3100
    const d = 1 - 0.5 * prog(t, qShot, S.end + 1)
    cam(c, { cx: track(t, [[S.start, 2700], [qPull, 3050, 'io']]), s: track(t, [[S.start, 1.1], [qPull + 2, 1.5, 'io'], [qBack, 1.05, 'io']]), d }, () => {
      pass(c, t, { d })
      hill(c, HX, GY + 6, 560, 210, mix('#1a1714', '#5a4a3a', d))
      if (t < qPull) {
        host(c, 3700, GY + 30, 120, { n: 7, rows: 3, face: -1, kind: 'immortal', pose: 'charge', t, walk: t * 6, stride: 0.9 })
        phalanx(c, 2400, GY + 40, 125, { n: 6, ranks: 2, face: -1, cloak: true, t, thrust: 0.5 })
      } else {
        const fall = prog(t, qShot + 1, qNone + 2.2)
        const R = rng(13); for (let k = 0; k < 16; k++) { const a = R(), x = HX - 170 + (k % 8) * 46, y = GY - 120 - Math.floor(k / 8) * 26 + Math.abs(x - HX) * 0.35; hoplite(c, x, y + 120, 100, { face: k % 2 ? 1 : -1, pose: t > qRest ? 'thrust' : 'guard', thrust: 0.5 + 0.5 * Math.sin(t * 4 + k), spear: t < qRest, cloak: k % 3 === 0, t: t + k, down: fall > a ? prog(fall, a, a + 0.15) : 0, col: mix('#100e0d', INK, d) }) }
        if (t > qTheb) for (let k = 0; k < 5; k++) { const p = prog(t, qTheb + 0.3, qTheb + 3.6); person(c, HX - 200 - p * 600 - k * 50, GY + 30, 110, { hat: 'none', face: -1, arm: 1.15, walk: t * 5 + k, stride: 0.8, col: mix('#100e0d', INK, d) }) }
        host(c, 2300, GY + 40, 115, { n: 9, rows: 2, kind: 'archer', pose: t > qShot - 0.2 ? 'bow' : 'stand', aim: 0.35, draw: 1, t, stride: 0, col: mix('#0c0b0c', INK, d) })
        host(c, 3900, GY + 40, 115, { n: 7, rows: 2, face: -1, kind: 'immortal', pose: 'stand', t, stride: 0, col: mix('#0c0b0c', INK, d) })
      }
      seaFront(c, t, { d })
      if (t > qShot) {
        arrows(c, t, qShot, { n: 60, waves: 8, every: 0.9, sx: 2000, sw: 600, sy: GY - 60, ex: HX - 200, ew: 400, ey: GY - 140, top: 300, dur: 1.4, col: '#0c0b0c', len: 30 })
        arrows(c, t, qShot + 0.4, { n: 40, waves: 8, every: 0.9, sx: 3800, sw: 400, sy: GY - 60, ex: HX - 200, ew: 400, ey: GY - 140, top: 300, dur: 1.4, col: '#0c0b0c', len: 30 })
        const r = rng(4); for (let k = 0; k < Math.floor(prog(t, qShot + 1, qNone + 2) * 70); k++) stuck(c, HX - 230 + r() * 460, GY - 30 - r() * 160 * (1 - Math.abs(r() - 0.5)), -1.2 - r() * 0.6, 26, '#0c0b0c')
      }
    })
    if (t > qTheb && t < qRest) label(c, 'the Thebans surrender', W / 2, 170, prog(t, qTheb + 0.6, qTheb + 1.2) * (1 - prog(t, qRest - 0.4, qRest)))
    if (t > qRest && t < qBack) label(c, 'daggers, hands, teeth', W / 2, 170, prog(t, qRest + 0.6, qRest + 1.2) * (1 - prog(t, qBack - 0.4, qBack)), { col: C.red })
    finish(c, t, d < 0.6); return d < 0.6
  }

  // =============================== 12. after ===============================
  function s12(c, t, q, S) {
    const qRoad = q('the road south') - 0.3, qBurn = q('and burned it'), qAth = q('but the athenians') - 0.3, qSal = q('a few weeks later') - 0.3, qHome = q('xerxes went home') - 0.3, qPla = q('at plataea'), q20 = q('herodotus says 20000') - 0.3, qEph = q('and ephialtes') - 0.3, qWord = q('in greek today') - 0.2
    if (t < qRoad) {
      // Xerxes' order, told by distance: the king's gold under the parasol, far off a bare pole on the hill at dusk
      paper(c, t, '#d9c39c')
      hill(c, 1300, 900, 900, 300, '#3a2f26'); c.fillStyle = INK; c.fillRect(1296, 600, 7, 160)
      xerxes(c, 420, 980, 1.2, { face: 1 })
      c.strokeStyle = INK; c.lineWidth = 4; c.beginPath(); c.moveTo(0, 980); c.lineTo(W, 980); c.stroke()
      finish(c, t, false); return false
    }
    if (t < qAth) {
      // Athens burns
      paper(c, t, '#2a1d17')
      glow(c, 960, 640, 900, '240,150,70', 0.55)
      c.fillStyle = '#1a1210'; c.beginPath(); c.moveTo(0, 900); c.bezierCurveTo(500, 900, 600, 640, 960, 640); c.bezierCurveTo(1320, 640, 1420, 900, 1920, 900); c.lineTo(1920, 1080); c.lineTo(0, 1080); c.closePath(); c.fill()
      bank(c, 960, 650, 520, 260, { cols: 8, fill: '#1a1210', col: '#1a1210' })
      if (t > qBurn - 0.8) for (let k = 0; k < 7; k++) fire(c, 720 + k * 80, 650, 1.3, t, prog(t, qBurn - 0.8 + k * 0.15, qBurn + 0.4 + k * 0.15))
      label(c, 'Athens', W / 2, 170, prog(t, qRoad + 1.4, qRoad + 2.2), { col: C.gold2, stroke: '#1a1210', font: F.head(90, 900) })
      finish(c, t, true); return true
    }
    if (t < qHome) {
      // the ships: the Athenians are already aboard; then Salamis
      view(c, { cx: 960, cy: 560, s: 1, d: 1 }, () => {
        sea(c, t, -300, 2300, 700, { col: '#6b7a80' })
        if (t < qSal) for (let k = 0; k < 5; k++) trireme(c, 300 + k * 330, 720 + (k % 2) * 40, 0.9, { t, face: 1, sail: 1 })
        else {
          const ram = prog(t, qSal + 2, qSal + 4, 'io')
          for (let k = 0; k < 4; k++) { const sink = prog(t, qSal + 3.6 + k * 0.5, qSal + 6 + k * 0.5); c.save(); c.translate(1500 + k * 140, 730 + k * 30 + sink * 90); c.rotate(sink * 0.35 * (k % 2 ? 1 : -1)); c.globalAlpha = 1 - sink * 0.8; trireme(c, 0, 0, 0.8, { t, face: -1, col: '#3a312a' }); c.restore() }
          for (let k = 0; k < 4; k++) trireme(c, lerp(200, 1240, ram) + k * 60 - k * 90 * (1 - ram), 740 + k * 30, 0.85, { t, face: 1, oarPh: k })
          sea(c, t + 3, -300, 2300, 860, { col: '#6b7a80', glint: 0.2 })
        }
      })
      if (t > qSal) label(c, 'Salamis', W / 2, 170, prog(t, qSal + 1, qSal + 1.8), { font: F.head(90, 900) })
      finish(c, t, false); return false
    }
    paper(c, t)
    if (t < q20) {
      xerxes(c, lerp(960, 2300, prog(t, qHome + 0.5, qHome + 3.5, 'i')), 960, 1.4, {})
      label(c, 'Plataea, 479 BC', W / 2, 200, prog(t, qPla, qPla + 0.8))
      finish(c, t, false); return false
    }
    if (t < qEph) {
      typeset(c, '20,000', W / 2, 520, F.head(220, 900), INK, prog(t, q20 + 0.6, q20 + 1.6), { track: 10 })
      text(c, 'Persian dead at the hot gates, says Herodotus', W / 2, 640, F.bodyI(52), C.red, { alpha: prog(t, q20 + 1.8, q20 + 2.6) })
      finish(c, t, false); return false
    }
    hooded(c, 960, 900, 300, { face: -1 })
    c.strokeStyle = INK; c.lineWidth = 4; c.beginPath(); c.moveTo(0, 900); c.lineTo(W, 900); c.stroke()
    if (t < qWord) label(c, 'a price on his head', W / 2, 200, prog(t, qEph + 1.4, qEph + 2.2), { col: C.gold })
    else { typeset(c, 'εφιάλτης', W / 2, 260, F.head(130, 800), INK, prog(t, qWord + 0.8, qWord + 2.0)); text(c, 'nightmare', W / 2, 340, F.bodyI(60), C.red, { alpha: prog(t, qWord + 2.2, qWord + 3) }) }
    finish(c, t, false); return false
  }

  // =============================== 13. the stone ===============================
  function s13(c, t, q, S) {
    const qGo = q('go tell the spartans') - 0.2, q1939 = q('in 1939') - 0.3, qFound = q('they found it'), qNever = q('it was never only') - 0.3, qDoor = q('it was about how long') - 0.3, qSub = q('subscribe') - 0.4
    paper(c, t)
    if (t < q1939) {
      hill(c, 960, 960, 1500, 260, '#8a7559')
      stele(c, 960, 900, 760, 520, ['GO TELL THE SPARTANS,', 'STRANGER PASSING BY,', 'THAT HERE, OBEYING', 'THEIR ORDERS, WE LIE.'], { p: prog(t, qGo, qGo + 6.2), font: F.sc(52), lh: 92 })
      finish(c, t, false); return false
    }
    if (t < qNever) {
      // the dig: a cut through the hill, the soil full of arrowheads
      c.fillStyle = '#9a8564'; c.fillRect(0, 520, W, 560)
      hatch(c, k => k.rect(0, 520, W, 560), { gap: 14, alpha: 0.15, angle: 0.1, box: [0, 520, W, 560] })
      const r = rng(1939), n = Math.floor(prog(t, qFound - 0.4, qFound + 2.6) * 90)
      for (let k = 0; k < 90; k++) { const x = 120 + r() * 1680, y = 580 + r() * 440, a = r() * 6.28; if (k >= n) continue; c.save(); c.translate(x, y); c.rotate(a); c.fillStyle = '#3a2a1c'; c.beginPath(); c.moveTo(16, 0); c.lineTo(-4, -6); c.lineTo(0, 0); c.lineTo(-4, 6); c.closePath(); c.fill(); c.restore() }
      label(c, '1939', W / 2, 240, prog(t, q1939 + 0.2, q1939 + 1), { font: F.head(130, 900) })
      text(c, 'Persian arrowheads, Kolonos hill', W / 2, 330, F.bodyI(52), C.red, { alpha: prog(t, qFound + 0.8, qFound + 1.6) })
      finish(c, t, false); return false
    }
    if (t < qSub) {
      // a few men holding a door, everyone behind them getting ready
      c.strokeStyle = INK; c.lineWidth = 4; c.beginPath(); c.moveTo(0, 900); c.lineTo(W, 900); c.stroke()
      stonewall(c, 760, 904, 70, 200, {})
      for (let k = 0; k < 4; k++) hoplite(c, 640 - k * 60, 900, 190, { face: -1, pose: 'guard', cloak: true, t })
      if (t > qDoor) for (let k = 0; k < 14; k++) { const a = prog(t, qDoor + 0.8 + k * 0.12, qDoor + 1.2 + k * 0.12); c.save(); c.globalAlpha = a; if (k < 6) bank(c, 1000 + k * 150, 900, 110, 120 + (k % 3) * 30, { cols: 3, fill: C.paper2 }); else person(c, 980 + (k - 6) * 110, 900, 120, { hat: 'none', walk: t * 4 + k, stride: 0.6, face: k % 2 ? 1 : -1 }); c.restore() }
      typeset(c, '300 + 700 + 400 + ...', W / 2, 220, F.head(90, 900), C.red, prog(t, qNever + 0.4, qNever + 1.6), { track: 6 })
      finish(c, t, false); return false
    }
    // the end card
    text(c, 'HISTORY UNFOLDZ', W / 2, 470, F.head(120, 900), INK, { alpha: prog(t, qSub, qSub + 0.8), track: 12 })
    rule(c, 560, 1360, 520, INK, prog(t, qSub + 0.3, qSub + 1.2))
    text(c, 'Subscribe', W / 2, 640, F.head(90, 900), C.red, { alpha: prog(t, qSub + 0.4, qSub + 1.2) })
    text(c, 'animal facts · history’s greatest battles · the craziest financial collapses', W / 2, 740, F.bodyI(44), INK, { alpha: prog(t, qSub + 2.2, qSub + 3.2) })
    finish(c, t, false); return false
  }

  window.SCENES.push(s8, s9, s10, s11, s12, s13)
})()
