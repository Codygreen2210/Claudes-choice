// scA.js: scenes 1-7 of Tulip Mania. Each scene is draw(c, t, q, S) -> true if the picture is dark.
// Paper and ink. The broken tulip's flames are the one red; money is the one gold.
(function () {
  const { clamp, lerp, EZ, prog, bump, rng, noise, track, mix } = K
  const { W, H, C, F, paper, finish, hatch, text, typeset, rule, person, glow, tw, bank, layer } = L
  const { ship, smoke } = B
  const { INK, RED, GOLD, dutchman, goodwife, tulip, bulb, gables, canal, tavern, table, glass, note, chart, beast, guilders, book } = TU
  const { night, turban } = T2
  const fade = (c, a, col = '12,10,8') => { if (a > 0) { c.fillStyle = `rgba(${col},${clamp(a)})`; c.fillRect(0, 0, W, H) } }
  const label = (c, s, x, y, a, o = {}) => window.__vertical ? null : text(c, s, x, y, o.font || F.headI(64, 700), o.col || INK, { alpha: a, stroke: o.stroke ?? C.paper, sw: 8, ...o })
  const ground = (c, y, col = INK) => { c.strokeStyle = col; c.lineWidth = 4; c.beginPath(); c.moveTo(0, y); c.lineTo(W, y); c.stroke() }
  const zoom = (c, cx, cy, s) => { c.translate(W / 2, H / 2); c.scale(s, s); c.translate(-cx, -cy) }
  // the soil in section: a bulb sleeping under a garden
  function soil(c, t, o = {}) {
    paper(c, t); c.fillStyle = '#6e5538'; c.fillRect(0, 560, W, 520)
    hatch(c, k => k.rect(0, 560, W, 520), { gap: 12, alpha: 0.2, angle: 0.2, box: [0, 560, W, 520] })
    const r = rng(4); c.fillStyle = 'rgba(30,22,14,0.35)'; for (let k = 0; k < 80; k++) { c.beginPath(); c.ellipse(r() * W, 600 + r() * 460, 3 + r() * 6, 2 + r() * 3, r() * 3, 0, 7); c.fill() }
    bulb(c, o.x ?? 960, o.y ?? 860, o.s ?? 1.6, { col: '#b48a5a' })
    c.fillStyle = INK; for (let k = 0; k < 14; k++) { const x = 60 + k * 140; c.fillRect(x, 520, 4, 40); c.beginPath(); c.ellipse(x + 2, 522, 14, 5, 0, 0, 7); c.fill() }
  }
  // the auction room: a crowd seen from behind, the auctioneer up front with a paper
  const ROOM = (() => { const r = rng(1637), out = []; for (let k = 0; k < 16; k++) out.push({ x: 120 + (k % 8) * 175 + r() * 40, row: Math.floor(k / 8), h: 230 + r() * 30, ph: r() * 6 }); return out })()
  function room(c, t, o = {}) {
    tavern(c, t, { light: o.light ?? 0.6 })
    const bid = o.bid || (() => 0)
    if (o.auctioneer !== false) {
      table(c, 1500, 820, 360, mix('#140f0b', INK, 0.5))
      dutchman(c, 1520, 820, 300, { face: -1, arm: 1.05 + 0.04 * Math.sin(t * 3), hold: (k) => { k.save(); k.translate(0, 36); k.rotate(2.6); k.fillStyle = '#f3ead6'; k.fillRect(-18, -26, 36, 46); k.restore() } })
    }
    ROOM.forEach((p, k) => { if (o.empty && k % 3) return; const raised = bid(k); dutchman(c, p.x, 1000 + p.row * 70, p.h + p.row * 40, { face: 1, col: mix(INK, '#3a2c20', p.row ? 0 : 0.3), arm: raised ? 1.2 : 0.05 + 0.03 * Math.sin(t + p.ph) }) })
  }

  // =============================== 1. Alkmaar ===============================
  function s1(c, t, q, S) {
    const qCrowd = q('a crowd is packed') - 0.3, qName = q('on it is'), qBulb = q('not a flower') - 0.3, qBid = q('the bidding starts') - 0.3, qHam = q('when the hammer') - 0.2, qSold = q('has sold for'), qCraft = q('a good craftsman') - 0.3, qNobody = q('what nobody') - 0.3, qStop = q('the buyers stopped')
    if (t < qBulb) {
      room(c, t, {})
      if (t > qName - 0.2) { const a = prog(t, qName - 0.2, qName + 0.6, 'o'); c.save(); c.globalAlpha = a; note(c, 1180, 330, 1.2 + 0.1 * a, { name: 'Admirael van Enchuysen', rot: -0.04 }); c.restore() }
      label(c, 'Alkmaar, Holland', 330, 150, prog(t, 0.5, 1.3), { align: 'left', col: C.paper, stroke: INK })
      text(c, 'February 5, 1637', 332, 214, F.bodyI(48), C.gold2, { align: 'left', alpha: prog(t, 1.0, 1.8), stroke: INK, sw: 6 })
      finish(c, t, false); return false
    }
    if (t < qBid) {
      soil(c, t)
      label(c, 'a bulb, still in the ground', W / 2, 200, prog(t, qBulb + 1.4, qBulb + 2.2))
      finish(c, t, false); return false
    }
    if (t < qCraft) {
      const p = prog(t, qBid + 0.6, qSold + 0.4, 'i'), price = Math.round(lerp(400, 5200, p) / 50) * 50
      room(c, t, { bid: (k) => t > qBid + 0.6 && t < qHam + 0.4 && ((k * 7 + Math.floor(t * 3)) % 5 === 0) })
      typeset(c, price.toLocaleString('en-US') + ' guilders', W / 2, 260, F.head(120, 900), C.gold2, 1, { stroke: INK, sw: 12 })
      if (t > qHam) { const a = bump(t, qHam + 0.3, 0.5); c.fillStyle = `rgba(255,248,230,${a * 0.5})`; c.fillRect(0, 0, W, H) }
      finish(c, t, false); return false
    }
    if (t < qNobody) {
      paper(c, t); ground(c, 860)
      dutchman(c, 420, 860, 300, { arm: 0.5 }); table(c, 600, 760, 220)
      guilders(c, 620, 750, 6)
      text(c, '300', 620, 560, F.head(90, 900), INK, { alpha: prog(t, qCraft + 0.6, qCraft + 1.2) }); text(c, 'a year', 620, 620, F.bodyI(44), INK, { alpha: prog(t, qCraft + 0.8, qCraft + 1.4) })
      const n = Math.floor(prog(t, qCraft + 1.6, qCraft + 3.6) * 17); for (let k = 0; k < 17; k++) if (k < n) guilders(c, 1100 + (k % 6) * 70, 860 - Math.floor(k / 6) * 120, 14)
      text(c, '5,200', 1270, 400, F.head(90, 900), GOLD, { alpha: prog(t, qCraft + 2.2, qCraft + 2.8) }); text(c, 'one bulb', 1270, 460, F.bodyI(44), INK, { alpha: prog(t, qCraft + 2.4, qCraft + 3.0) })
      finish(c, t, false); return false
    }
    // two days earlier, twenty miles away: an empty room
    room(c, t, { light: 0.35, empty: true, bid: () => 0 })
    label(c, 'Haarlem, two days earlier', W / 2, 170, prog(t, qNobody + 2.4, qNobody + 3.2), { col: C.paper, stroke: INK })
    finish(c, t, true); return true
  }

  // =============================== 2. the richest place on earth ===============================
  function s2(c, t, q, S) {
    const qShips = q('its ships traded') - 0.3, qAms = q('amsterdam had') - 0.3, qOrd = q('and for the first time') - 0.3, qWeav = q('weavers'), qLook = q('people who wanted') - 0.3
    paper(c, t)
    if (t < qOrd) {
      const pan = prog(t, S.start - 0.5, qOrd, 'io')
      c.save(); c.translate(-pan * 600, 0)
      gables(c, -100, 760, 14, { seed: 21 })
      canal(c, t, -200, 3200, 760, 320, {})
      for (let k = 0; k < 3; k++) ship(c, 700 + k * 700 + ((t * 18) % 200), 900, 0.85, { t, col: INK })
      c.restore()
      if (t > qShips) { ['spice', 'grain', 'furs'].forEach((s, k) => label(c, s, 480 + k * 480, 170, prog(t, qShips + 1.2 + k * 1.2, qShips + 1.8 + k * 1.2) * (1 - prog(t, qAms - 0.5, qAms)), { font: F.headI(66, 700) })) }
      if (t > qAms) label(c, 'the Amsterdam exchange', W / 2, 170, prog(t, qAms + 0.4, qAms + 1.2) * 1, { font: F.head(70, 900) })
      label(c, 'the Dutch Republic, 1630s', W / 2, 170, prog(t, S.start, S.start + 0.8) * (1 - prog(t, qShips - 0.3, qShips)))
      finish(c, t, false); return false
    }
    ground(c, 880)
    if (t < qLook) {
      const jobs = ['Weavers', 'Bakers', 'Innkeepers', 'Glassmakers']
      for (let k = 0; k < 4; k++) {
        const a = t < qWeav ? 1 : prog(t, qWeav + k * 0.55 - 0.3, qWeav + k * 0.55)
        const x = 330 + k * 420; if (k === 1) goodwife(c, x, 880, 290, {}); else dutchman(c, x, 880, 300, { arm: 0.1 })
        text(c, jobs[k], x, 560, F.headI(56, 700), INK, { alpha: t < qWeav ? 0 : a })
        guilders(c, x + 80, 880, 3)
      }
      finish(c, t, false); return false
    }
    // wanting to look like they had made it: a vase with one red tulip in a fine room
    dutchman(c, 700, 880, 340, { face: 1, arm: 0.45, cape: true })
    c.fillStyle = INK; c.fillRect(1040, 700, 240, 180); c.fillStyle = '#3a312a'; c.beginPath(); c.moveTo(1110, 700); c.quadraticCurveTo(1100, 610, 1160, 600); c.quadraticCurveTo(1220, 610, 1210, 700); c.closePath(); c.fill()
    tulip(c, 1160, 612, 0.95, { broken: 1, t, seed: 5 })
    finish(c, t, false); return false
  }

  // =============================== 3. where tulips came from ===============================
  function s3(c, t, q, S) {
    const qWild = q('it grew wild') - 0.3, qSult = q('and the ottoman'), qName = q('even the name') - 0.3, q1593 = q('in 1593') - 0.3, qSteal = q('he would not sell') - 0.3, qNight = q('so people climbed'), qAll = q('within a few years') - 0.3
    if (t < qName) {
      paper(c, t)
      if (t < qSult) {
        c.fillStyle = '#b6a27a'; c.beginPath(); c.moveTo(0, 820); for (let x = 0; x <= W; x += 120) c.lineTo(x, 380 + Math.abs(Math.sin(x * 0.004)) * 260 + (x % 240) * 0.2); c.lineTo(W, 820); c.closePath(); c.fill()
        for (let k = 0; k < 9; k++) tulip(c, 200 + k * 190, 900, 0.55, { col: k % 2 ? '#b8402e' : C.gold, t, open: 0.5 })
        label(c, 'the mountains of Central Asia', W / 2, 160, prog(t, qWild + 0.4, qWild + 1.2))
      } else {
        // a sultan's garden: domes, and rows of tulips tended by gardeners
        c.fillStyle = INK; c.beginPath(); c.arc(960, 520, 170, Math.PI, 0); c.fill(); c.fillRect(780, 520, 360, 180); c.fillRect(640, 300, 26, 400); c.fillRect(1254, 300, 26, 400); c.beginPath(); c.moveTo(636, 300); c.lineTo(653, 230); c.lineTo(670, 300); c.fill(); c.beginPath(); c.moveTo(1250, 300); c.lineTo(1267, 230); c.lineTo(1284, 300); c.fill()
        ground(c, 900)
        for (let k = 0; k < 12; k++) tulip(c, 120 + k * 150, 900, 0.5, { col: '#b8402e', t })
        for (let k = 0; k < 3; k++) turban(c, 380 + k * 600, 900, 220, {})
        label(c, 'the Ottoman sultans', W / 2, 160, prog(t, qSult + 0.3, qSult + 1.1))
      }
      finish(c, t, false); return false
    }
    if (t < q1593) {
      paper(c, t)
      tulip(c, 700, 900, 1.6, { col: '#b8402e', t, open: 0.15 })
      turban(c, 1250, 900, 380, {})
      text(c, 'tülbend', W / 2 + 140, 320, F.head(110, 900), INK, { alpha: prog(t, qName + 1.6, qName + 2.4) })
      text(c, '“turban”', W / 2 + 140, 400, F.bodyI(56), C.red, { alpha: prog(t, qName + 2.4, qName + 3.2) })
      finish(c, t, false); return false
    }
    if (t < qNight) {
      paper(c, t); ground(c, 880)
      c.fillStyle = '#5a4a3a'; c.fillRect(0, 700, 260, 180); c.fillRect(1660, 700, 260, 180)
      for (let k = 0; k < 7; k++) tulip(c, 420 + k * 170, 880, 0.6, { col: k % 3 ? '#b8402e' : C.gold, t })
      dutchman(c, 760, 880, 280, { face: 1, arm: 0.35, lean: 0.25 })
      label(c, 'Carolus Clusius, Leiden, 1593', W / 2, 160, prog(t, q1593 + 0.6, q1593 + 1.4))
      finish(c, t, false); return false
    }
    if (t < qAll) {
      night(c, t, { top: '#0b0e16', mid: '#18203a', low: '#232b45' })
      c.fillStyle = '#07080c'; c.fillRect(0, 880, W, 200); c.fillRect(0, 560, W, 330)
      for (let k = 0; k < 3; k++) { const p = prog(t, qNight + 0.3 + k * 0.5, qNight + 2.4 + k * 0.5, 'io'); dutchman(c, 500 + k * 280, lerp(880, 560, p), 220, { col: '#07080c', arm: 1.1 - p * 0.6, lean: -0.1 }) }
      finish(c, t, true); return true
    }
    // all over Holland: a field to the horizon
    paper(c, t)
    for (let row = 0; row < 7; row++) { const y = 560 + row * 80, s = 0.18 + row * 0.08, gap = 70 + row * 26; for (let x = -40; x < W + 40; x += gap) tulip(c, x + (row % 2) * gap / 2, y, s, { col: ['#b8402e', C.gold, '#f1e7d2', '#b8402e'][row % 4], t, sway: 0.5 }) }
    finish(c, t, false); return false
  }

  // =============================== 4. broken tulips ===============================
  function s4(c, t, q, S) {
    const qBut = q('but every so often') - 0.3, qCalled = q('the dutch called them'), qVirus = q('nobody knew it then') - 0.3, qRare = q('so the most beautiful') - 0.3, qSemp = q('the most famous') - 0.3, q1623 = q('in 1623'), qNo = q('the owner said no')
    paper(c, t); ground(c, 900)
    if (t < qVirus) {
      const cols = ['#b8402e', C.gold, '#f1e7d2', '#b8402e', C.gold]
      cols.forEach((col, k) => tulip(c, 360 + k * 300, 900, 1.15, { col, t, broken: k === 2 ? prog(t, qBut + 0.6, qBut + 2.6) : 0, seed: k }))
      if (t > qCalled) label(c, 'a broken tulip', 960, 200, prog(t, qCalled + 0.3, qCalled + 1))
      finish(c, t, false); return false
    }
    if (t < qSemp) {
      // the virus: insects drift from a sick bulb to the next; the broken flower droops a little
      tulip(c, 760, 900, 1.15, { broken: 1, t, seed: 2, sway: 0.4 }); tulip(c, 1160, 900, 1.0, { col: '#b8402e', t })
      const r = rng(8); c.fillStyle = INK; for (let k = 0; k < 18; k++) { const p = ((t * 0.3 + r()) % 1), x = lerp(760, 1160, p) + Math.sin(t * 3 + k) * 20, y = 560 - Math.sin(p * Math.PI) * 140 + r() * 60; c.beginPath(); c.ellipse(x, y, 4, 3, 0, 0, 7); c.fill() }
      label(c, 'a virus, carried by insects', W / 2, 180, prog(t, qVirus + 2.4, qVirus + 3.2))
      if (t > qRare) label(c, 'the rarest, and the hardest to breed', W / 2, 260, prog(t, qRare + 0.4, qRare + 1.2), { col: C.red })
      finish(c, t, false); return false
    }
    tulip(c, 960, 960, 2.0, { broken: 1, t, seed: 11, flame: '#9c2416', open: 0.2 })
    label(c, 'Semper Augustus', W / 2, 150, prog(t, qSemp + 0.6, qSemp + 1.4), { font: F.head(96, 900) })
    if (t > q1623) { typeset(c, '12,000 guilders', 420, 520, F.head(70, 900), GOLD, prog(t, q1623 + 1.2, q1623 + 2.4)); text(c, 'for ten bulbs', 420, 580, F.bodyI(44), INK, { alpha: prog(t, q1623 + 2.2, q1623 + 2.8) }) }
    if (t > qNo) typeset(c, 'No.', 1500, 560, F.head(150, 900), C.red, prog(t, qNo + 0.6, qNo + 1.0))
    finish(c, t, false); return false
  }

  // =============================== 5. the wind trade ===============================
  function s5(c, t, q, S) {
    const qRest = q('the rest of the year') - 0.3, qWinter = q('so by the winter') - 0.3, qProm = q('they were trading promises') - 0.2, qTav = q('the deals were made') - 0.3, qCol = q('each tavern had') - 0.3, qNo = q('the buyer often') - 0.3, qWind = q('the dutch had a name')
    if (t < qWinter) {
      if (t < qRest) {
        paper(c, t); ground(c, 900)
        const months = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']
        months.forEach((m, k) => { const x = 300 + k * 120, on = k === 3; c.fillStyle = on ? '#b8402e' : C.paper2; c.fillRect(x - 50, 300, 100, 60); text(c, m, x, 345, F.head(40, 800), on ? C.paper : INK) })
        tulip(c, 660, 900, 1.2, { col: '#b8402e', t, open: 0.6 })
        label(c, 'about one week in spring', 660, 240, prog(t, S.start + 1.4, S.start + 2.2), { font: F.headI(52, 700) })
      } else soil(c, t, { x: 960, y: 900 })
      finish(c, t, false); return false
    }
    if (t < qTav) {
      paper(c, t)
      note(c, 960, 560, 2.2 * (0.9 + 0.1 * prog(t, qProm, qProm + 1, 'o')), { name: 'I will sell you this bulb', price: 'at this price', rot: -0.03 })
      label(c, 'Winter, 1636', W / 2, 150, prog(t, qWinter, qWinter + 0.8))
      finish(c, t, false); return false
    }
    if (t < qWind) {
      tavern(c, t, { light: 0.55 }); table(c, 960, 800, 620, '#140f0b')
      dutchman(c, 640, 1000, 330, { face: 1, arm: 0.6 }); dutchman(c, 1280, 1000, 330, { face: -1, arm: 0.6 })
      glass(c, 860, 790, 1.4); glass(c, 1060, 790, 1.4)
      if (t > qNo) { note(c, 960, 640, 0.8, { rot: 0.05 }); text(c, 'no money yet', 640, 420, F.headI(48), C.paper, { alpha: prog(t, qNo + 0.4, qNo + 1), stroke: INK, sw: 6 }); text(c, 'no bulb yet', 1280, 420, F.headI(48), C.paper, { alpha: prog(t, qNo + 2.6, qNo + 3.2), stroke: INK, sw: 6 }) }
      if (t > qCol && t < qNo) label(c, 'the “colleges”: wine money on every deal', W / 2, 170, prog(t, qCol + 1.2, qCol + 2), { col: C.paper, stroke: INK })
      finish(c, t, false); return false
    }
    // the wind trade: papers carried off on the wind
    paper(c, t)
    const r = rng(2); c.strokeStyle = 'rgba(26,21,18,0.25)'; c.lineWidth = 3; for (let k = 0; k < 20; k++) { const y = 200 + r() * 700, x = ((t * 400 + r() * W) % (W + 400)) - 200; c.beginPath(); c.moveTo(x, y); c.quadraticCurveTo(x + 80, y - 20, x + 200, y); c.stroke() }
    for (let k = 0; k < 7; k++) { const x = ((t * 260 + k * 320) % (W + 400)) - 200, y = 300 + Math.sin(t * 2 + k) * 120 + k * 60; note(c, x, y, 0.45, { rot: Math.sin(t * 3 + k) * 0.5, seed: k }) }
    typeset(c, 'windhandel', W / 2, 520, F.head(130, 900), INK, prog(t, qWind + 1.6, qWind + 2.6), { stroke: C.paper, sw: 12 })
    text(c, 'the wind trade', W / 2, 600, F.bodyI(56), C.red, { alpha: prog(t, qWind + 2.6, qWind + 3.2), stroke: C.paper, sw: 8 })
    finish(c, t, false); return false
  }

  // =============================== 6. the prices go up ===============================
  const RISE = [[0, 0.05], [0.15, 0.08], [0.3, 0.14], [0.45, 0.24], [0.6, 0.42], [0.75, 0.66], [0.9, 0.9]]
  function s6(c, t, q, S) {
    const qTwice = q('a bulb bought') - 0.3, qPlain = q('even the plainest') - 0.3, qPlague = q('that winter, a plague') - 0.3, qRisk = q('some historians') - 0.3, qNot = q('it was no longer') - 0.3, qPaper = q('they only needed') - 0.3
    if (t < qPlague) {
      paper(c, t)
      chart(c, 360, 900, 1200, 640, RISE, prog(t, S.start, qPlague, 'l'))
      text(c, 'price', 330, 240, F.headI(40), INK, { align: 'right' }); text(c, 'Dec 1636', 400, 950, F.body(36), INK); text(c, 'Feb 1637', 1520, 950, F.body(36), INK)
      if (t > qTwice) typeset(c, '× 2', 1300, 400, F.head(110, 900), C.red, prog(t, qTwice + 2.2, qTwice + 2.8))
      if (t > qPlain) typeset(c, '× 10', 1300, 540, F.head(110, 900), C.red, prog(t, qPlain + 2.8, qPlain + 3.4))
      finish(c, t, false); return false
    }
    if (t < qNot) {
      // the plague in Haarlem: a dark street, one lamp, doors shut
      paper(c, t, '#2a221c'); gables(c, -40, 900, 10, { col: '#100c09', win: (k) => (k % 3 === 1 ? 'rgba(246,199,112,0.55)' : '#201812'), seed: 9 })
      c.fillStyle = '#0b0807'; c.fillRect(0, 900, W, 180)
      label(c, 'Haarlem, 1636', W / 2, 160, prog(t, qPlague + 0.4, qPlague + 1.2), { col: C.paper, stroke: INK })
      finish(c, t, true); return true
    }
    // the paper goes hand to hand, and nobody looks at the flower
    paper(c, t); ground(c, 880)
    const n = 6, p = (t - qNot) * 0.6
    for (let k = 0; k < n; k++) dutchman(c, 260 + k * 280, 880, 280, { face: 1, arm: 0.55 })
    const at = p % (n - 1), k0 = Math.floor(at), f = at - k0
    note(c, 260 + (k0 + f) * 280 + 60, 640 - Math.sin(f * Math.PI) * 60, 0.45, { rot: 0.1 * Math.sin(t * 2) })
    if (t > qPaper) { const pr = 1000 + Math.floor((t - qPaper) * 3) * 150; text(c, pr.toLocaleString('en-US') + ' g.', W / 2, 260, F.head(90, 900), GOLD, { stroke: INK, sw: 6 }) }
    finish(c, t, false); return false
  }

  // =============================== 7. the pamphlet ===============================
  const GOODS = [['sack', 'wheat'], ['sack', 'rye'], ['ox', 'oxen'], ['pig', 'pigs'], ['sheep', 'sheep'], ['barrel', 'wine'], ['barrel', 'beer'], ['barrel', 'butter'], ['cheese', 'cheese'], ['bed', 'a bed'], ['coat', 'clothes'], ['cup', 'a silver cup']]
  function s7(c, t, q, S) {
    const cues = ['two loads of wheat', 'four of rye', 'four fat oxen', 'eight fat pigs', 'twelve fat sheep', 'two barrels of wine', 'four barrels of beer', 'two of butter', '1000 pounds of cheese', 'a bed', 'a suit of clothes', 'and a silver'].map(s => q(s))
    const qAll = q('all of that') - 0.3
    paper(c, t)
    if (t < qAll) {
      label(c, 'what one bulb was worth, 1637', W / 2, 140, prog(t, S.start, S.start + 0.8), { font: F.headI(56, 700) })
      GOODS.forEach(([kind, name], k) => {
        const a = prog(t, cues[k] - 0.1, cues[k] + 0.35, 'o'), x = 240 + (k % 6) * 290, y = 520 + Math.floor(k / 6) * 330
        if (a <= 0) return; c.save(); c.globalAlpha = a; beast(c, x, y, 1.05 * (0.9 + 0.1 * a), kind); c.restore()
        text(c, name, x, y + 60, F.headI(40, 700), INK, { alpha: a })
      })
      finish(c, t, false); return false
    }
    // the balance: everything on one side, one bulb on the other
    const tilt = 0
    c.strokeStyle = INK; c.lineWidth = 10; c.beginPath(); c.moveTo(960, 900); c.lineTo(960, 380); c.stroke(); c.beginPath(); c.moveTo(400, 380 + tilt); c.lineTo(1520, 380 - tilt); c.stroke()
    c.lineWidth = 3; for (const x of [400, 1520]) { c.beginPath(); c.moveTo(x, 380); c.lineTo(x - 140, 620); c.moveTo(x, 380); c.lineTo(x + 140, 620); c.stroke(); c.fillStyle = INK; c.fillRect(x - 170, 620, 340, 14) }
    GOODS.slice(0, 9).forEach(([kind], k) => beast(c, 290 + (k % 3) * 100, 615 - Math.floor(k / 3) * 60, 0.45, kind))
    bulb(c, 1520, 615, 0.75, { col: '#b48a5a' })
    c.fillStyle = INK; c.fillRect(860, 900, 200, 20)
    finish(c, t, false); return false
  }

  window.SCENES = [s1, s2, s3, s4, s5, s6, s7]
  window.TUA = { fade, label, ground, zoom, soil, room, RISE }
})()
