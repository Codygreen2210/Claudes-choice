// scB.js: scenes 8-13 of Tulip Mania: the crash, who pays, the legend, the records, the shape, the flower.
(function () {
  const { clamp, lerp, EZ, prog, bump, rng, noise, track, mix } = K
  const { W, H, C, F, paper, finish, hatch, text, typeset, rule, person, glow, tw, bank } = L
  const { ship } = B
  const { INK, RED, GOLD, dutchman, goodwife, tulip, bulb, gables, canal, tavern, table, glass, note, chart, beast, guilders, book } = TU
  const { fade, label, ground, zoom, soil, room, RISE } = TUA
  const BUBBLE = [...TU_RISE(), [0.93, 0.95], [0.97, 0.45], [1.0, 0.12]]
  function TU_RISE() { return [[0, 0.05], [0.12, 0.08], [0.25, 0.14], [0.38, 0.24], [0.52, 0.42], [0.66, 0.66], [0.8, 0.88]] }
  const TOWNS = [['Haarlem', 760, 520], ['Amsterdam', 1010, 560], ['Leiden', 640, 700], ['Alkmaar', 820, 320], ['Utrecht', 1160, 760], ['Enkhuizen', 1120, 300], ['Rotterdam', 700, 860]]

  // =============================== 8. the crash ===============================
  function s8(c, t, q, S) {
    const qNobody = q('and nobody bid'), qHalf = q('not at the price') - 0.2, qNews = q('the news went') - 0.3, qSell = q('and everyone holding a promise to sell') - 0.3, qWhy = q('nobody has ever proved') - 0.3, qAlk = q('the alkmaar auction') - 0.3
    if (t < qNews) {
      room(c, t, { light: t > qNobody ? 0.4 : 0.6, empty: t > qNobody, bid: () => 0 })
      label(c, 'Haarlem, February 1637', W / 2, 160, prog(t, S.start + 1.0, S.start + 1.8) * (1 - prog(t, qNobody - 0.4, qNobody)), { col: C.paper, stroke: INK })
      if (t > qNobody) { const p = clamp((t - qNobody) / 3); typeset(c, (t > qHalf + 1.4 ? '2,500' : '5,000') + ' g.?', W / 2, 300, F.head(110, 900), GOLD, 1, { stroke: INK, sw: 10 }); if (t > qHalf + 1.4) { c.strokeStyle = C.red; c.lineWidth = 10; c.beginPath(); c.moveTo(700, 270); c.lineTo(700 + 520 * prog(t, qHalf + 2.0, qHalf + 2.6), 270); c.stroke() } }
      finish(c, t, true); return true
    }
    if (t < qWhy) {
      paper(c, t)
      // the news spreads town to town
      TOWNS.forEach(([n, x, y], k) => { const a = prog(t, qNews + 0.3 + k * 0.4, qNews + 0.7 + k * 0.4); c.fillStyle = a > 0.5 ? C.red : INK; c.beginPath(); c.arc(x, y, 12 + 10 * a, 0, 7); c.fill(); text(c, n, x + 28, y + 12, F.sc(38), INK, { align: 'left' }); if (k) { const [, px, py] = TOWNS[k - 1]; c.strokeStyle = C.red; c.globalAlpha = a; c.lineWidth = 3; c.setLineDash([10, 8]); c.beginPath(); c.moveTo(px, py); c.lineTo(x, y); c.stroke(); c.setLineDash([]); c.globalAlpha = 1 } })
      if (t > qSell - 2.5) { dutchman(c, 1540, 900, 260, { face: -1, arm: 0.6 }); dutchman(c, 1820, 900, 260, { face: -1, arm: 0.8, lean: -0.15 }); note(c, 1640, 640, 0.5, { rot: Math.sin(t * 6) * 0.1 }) }
      finish(c, t, false); return false
    }
    if (t < qAlk) {
      paper(c, t)
      chart(c, 360, 900, 1200, 640, BUBBLE, 1)
      text(c, 'the plague?', 1100, 300, F.headI(56), INK, { alpha: prog(t, qWhy + 3.0, qWhy + 3.6) }); text(c, 'too high for the next buyer?', 1100, 380, F.headI(56), INK, { alpha: prog(t, qWhy + 4.2, qWhy + 4.8) })
      finish(c, t, false); return false
    }
    room(c, t, { bid: (k) => ((k * 7 + Math.floor(t * 3)) % 5 === 0) })
    label(c, 'Alkmaar: one of the last good days', W / 2, 160, prog(t, qAlk + 0.6, qAlk + 1.4), { col: C.paper, stroke: INK })
    finish(c, t, false); return false
  }

  // =============================== 9. who pays ===============================
  function s9(c, t, q, S) {
    const qCourt = q('sellers took buyers') - 0.3, qGamb = q('to the judges'), qTowns = q('in the end') - 0.3, qHaar = q('in haarlem') - 0.3, qTorn = q('the paper was torn') - 0.3, qBloom = q('and the tulips bloomed')
    paper(c, t)
    if (t < qTowns) {
      // the court: judges high behind a bench
      c.fillStyle = INK; c.fillRect(560, 520, 800, 260); c.fillRect(540, 500, 840, 26)
      for (let k = 0; k < 3; k++) dutchman(c, 760 + k * 200, 560, 230, { face: 1, cape: true })
      c.fillStyle = INK; c.fillRect(560, 520, 800, 260)
      ground(c, 940); dutchman(c, 420, 940, 260, { face: 1, arm: 0.7, hold: (k) => { k.save(); k.translate(0, 36); k.fillStyle = '#f3ead6'; k.fillRect(-16, -22, 32, 40); k.restore() } }); dutchman(c, 1500, 940, 260, { face: -1, arm: 0.2 })
      if (t > qGamb) typeset(c, 'gambling debts', W / 2, 300, F.head(100, 900), C.red, prog(t, qGamb + 1.6, qGamb + 2.4))
      label(c, 'the Court of Holland', W / 2, 160, prog(t, qCourt + 0.6, qCourt + 1.4) * (1 - prog(t, qGamb, qGamb + 0.4)))
      finish(c, t, false); return false
    }
    if (t < qTorn) {
      note(c, 960, 520, 2.0, { name: 'Semper Augustus', price: '5,500 g.' })
      if (t > qHaar) { c.fillStyle = 'rgba(240,226,200,0.9)'; c.fillRect(560, 760, 800, 150); typeset(c, 'pay 3.5%, and walk away', W / 2, 860, F.head(76, 900), GOLD, prog(t, qHaar + 3.2, qHaar + 4.4), { stroke: INK, sw: 6 }) }
      label(c, 'Haarlem, 1638', W / 2, 150, prog(t, qHaar + 0.4, qHaar + 1.2))
      finish(c, t, false); return false
    }
    if (t < qBloom) { const p = prog(t, qTorn + 0.4, qTorn + 1.6, 'o'); c.save(); c.translate(-p * 200, 0); c.rotate(-p * 0.1); note(c, 960, 520, 2.0, { name: 'Semper Augustus', price: '5,500 g.', half: 'left' }); c.restore(); c.save(); c.translate(p * 200, 40 * p); c.rotate(p * 0.12); note(c, 960, 520, 2.0, { name: 'Semper Augustus', price: '5,500 g.', half: 'right' }); c.restore(); finish(c, t, false); return false }
    for (let row = 0; row < 6; row++) { const y = 600 + row * 90, s = 0.22 + row * 0.1, gap = 80 + row * 30; for (let x = -40; x < W + 40; x += gap) tulip(c, x + (row % 2) * gap / 2, y, s * prog(t, qBloom - 0.2 + row * 0.15, qBloom + 1 + row * 0.15, 'o'), { col: ['#b8402e', C.gold, '#f1e7d2'][row % 3], t, sway: 0.6, open: 0.6 }) }
    label(c, 'spring, 1637', W / 2, 160, prog(t, qBloom + 1, qBloom + 1.8))
    finish(c, t, false); return false
  }

  // =============================== 10. the legend ===============================
  function s10(c, t, q, S) {
    const qPreach = q('preachers wrote') - 0.3, qSailor = q('one told of') - 0.3, qMack = q('two hundred years later') - 0.3, qCalled = q('it was called') - 0.3, qMad = q('he said the whole') - 0.3, qBook = q('his book is') - 0.3
    paper(c, t); ground(c, 900)
    if (t < qSailor) {
      c.fillStyle = INK; c.fillRect(760, 640, 260, 260); c.beginPath(); c.moveTo(740, 640); c.lineTo(1040, 640); c.lineTo(1010, 610); c.lineTo(770, 610); c.closePath(); c.fill()
      dutchman(c, 900, 640, 260, { arm: 1.1 + 0.15 * Math.sin(t * 3), face: 1 })
      for (let k = 0; k < 6; k++) { const p = ((t - qPreach) * 0.3 + k / 6) % 1; if (t > qPreach) { c.save(); c.translate(lerp(1100, 1800, p), 300 + Math.sin(k * 2 + t) * 200 + p * 200); c.rotate(Math.sin(t * 2 + k)); c.fillStyle = '#f3ead6'; c.fillRect(-50, -66, 100, 132); c.strokeStyle = INK; c.lineWidth = 2; c.strokeRect(-50, -66, 100, 132); for (let l = 0; l < 6; l++) c.fillRect(-36, -46 + l * 18, 72, 3); c.restore() } }
      label(c, 'the pamphlets', W / 2, 160, prog(t, qPreach + 0.6, qPreach + 1.4))
      finish(c, t, false); return false
    }
    if (t < qMack) {
      person(c, 820, 900, 280, { hat: 'cap', arm: 0.75, face: 1 }); bulb(c, 1010, 680, 0.4, { col: '#b48a5a' })
      text(c, '“an onion”', 1200, 520, F.headI(64), INK, { alpha: prog(t, qSailor + 1.4, qSailor + 2.0) })
      text(c, 'a story nobody has ever found proof of', W / 2, 1000, F.bodyI(40), C.red, { alpha: prog(t, qSailor + 3.2, qSailor + 4.0) })
      finish(c, t, false); return false
    }
    book(c, 960, 860, 2.2, { title: t > qCalled ? ['EXTRAORDINARY', 'POPULAR', 'DELUSIONS', 'AND THE', 'MADNESS', 'OF CROWDS'] : null })
    label(c, 'Charles Mackay, 1841', W / 2, 160, prog(t, qMack + 0.6, qMack + 1.4))
    if (t > qMad) text(c, '“the whole country gone mad”', W / 2, 260, F.headI(60, 700), C.red, { alpha: prog(t, qMad + 0.6, qMad + 1.2) * (1 - prog(t, qBook - 0.3, qBook)) })
    finish(c, t, false); return false
  }

  // =============================== 11. what the records show ===============================
  function s11(c, t, q, S) {
    const qFind = q('she could not find') - 0.3, qFew = q('the traders were') - 0.3, qEcon = q('the dutch economy') - 0.3, qReal = q('the bubble was real') - 0.3, qStory = q('but the ruin')
    paper(c, t)
    if (t < qFew) {
      ground(c, 900)
      for (let k = 0; k < 5; k++) { c.fillStyle = INK; c.fillRect(120 + k * 300, 220, 14, 680); for (let s = 0; s < 6; s++) for (let b = 0; b < 9; b++) { c.fillStyle = (b + s + k) % 3 ? '#5a4632' : '#3a2c20'; c.fillRect(140 + k * 300 + b * 28, 250 + s * 108, 22, 92) } }
      c.fillStyle = 'rgba(238,226,200,0.85)'; c.fillRect(560, 560, 800, 340)
      table(c, 960, 780, 520); goodwife(c, 760, 900, 280, { face: 1 }); book(c, 1020, 770, 0.6, {})
      if (t > qFind) typeset(c, 'bankruptcies found: 0', W / 2, 180, F.head(80, 900), C.red, prog(t, qFind + 1.6, qFind + 2.6), { stroke: C.paper, sw: 10 })
      label(c, 'Anne Goldgar, the Dutch archives', W / 2, 180, prog(t, S.start + 1.4, S.start + 2.2) * (1 - prog(t, qFind + 1.2, qFind + 1.6)))
      finish(c, t, false); return false
    }
    if (t < qEcon) {
      const r = rng(5); for (let k = 0; k < 600; k++) { const x = 160 + r() * 1600, y = 300 + r() * 620, hit = k < 30; c.fillStyle = hit ? C.red : 'rgba(26,21,18,0.35)'; c.beginPath(); c.arc(x, y, hit ? 9 : 5, 0, 7); c.fill() }
      label(c, 'a few hundred traders, not a whole country', W / 2, 180, prog(t, qFew + 0.8, qFew + 1.6))
      finish(c, t, false); return false
    }
    if (t < qReal) {
      const p = prog(t, qEcon, qReal, 'io'); c.save(); c.translate(-p * 400, 0); gables(c, -100, 760, 16, { seed: 4 }); canal(c, t, -200, 3000, 760, 320); for (let k = 0; k < 4; k++) ship(c, 400 + k * 600, 900, 0.8, { t, col: INK }); c.restore()
      label(c, 'the Golden Age goes on', W / 2, 170, prog(t, qEcon + 1.4, qEcon + 2.2))
      finish(c, t, false); return false
    }
    ;['the bubble', 'the prices', 'the crash'].forEach((s, k) => { text(c, s, 560 + k * 400, 460, F.headI(56), INK, { alpha: prog(t, qReal + k * 1.0, qReal + 0.6 + k * 1.0) }); text(c, 'real', 560 + k * 400, 540, F.head(64, 900), INK, { alpha: prog(t, qReal + 0.3 + k * 1.0, qReal + 0.9 + k * 1.0) }) })
    if (t > qStory) { text(c, 'the ruin', W / 2, 760, F.headI(70), INK, { alpha: prog(t, qStory, qStory + 0.6) }); text(c, 'mostly a story', W / 2, 850, F.head(80, 900), C.red, { alpha: prog(t, qStory + 1.2, qStory + 1.8) }) }
    finish(c, t, false); return false
  }

  // =============================== 12. the shape ===============================
  function s12(c, t, q, S) {
    const qShape = q('because it was the first') - 0.3, qRare = q('something rare') - 0.2, qBuy = q('buyers who dont care') - 0.3, qSame = q('people said the same') - 0.3, qDoesnt = q('and then one ordinary')
    paper(c, t)
    if (t < qSame) {
      chart(c, 360, 900, 1200, 640, BUBBLE, t < qBuy ? prog(t, qShape, qBuy, 'l') * 0.86 : t < qDoesnt ? 0.86 : 0.86 + 0.14 * prog(t, qDoesnt, qDoesnt + 1.6))
      const notes = [['something rare', 460, 820, qRare], ['prices that only go up', 760, 640, qRare + 1.4], ['a promise, not the thing', 1060, 470, qRare + 3.4], ['the next buyer', 1300, 300, qBuy + 0.6]]
      notes.forEach(([s, x, y, at]) => text(c, s, x, y, F.headI(44, 700), INK, { alpha: prog(t, at, at + 0.6), stroke: C.paper, sw: 6 }))
      finish(c, t, false); return false
    }
    if (t < qDoesnt) {
      ;[['Railway shares, 1840s', 360], ['Stocks, 1929', 960], ['Houses, 2006', 1560]].forEach(([s, x], k) => { const a = prog(t, qSame + 0.8 + k * 1.6, qSame + 1.6 + k * 1.6); c.save(); c.globalAlpha = a; chart(c, x - 240, 760, 480, 380, BUBBLE, 1, { lw: 6 }); c.restore(); text(c, s, x, 830, F.headI(44, 700), INK, { alpha: a }) })
      finish(c, t, false); return false
    }
    room(c, t, { light: 0.35, empty: true, bid: () => 0 })
    finish(c, t, true); return true
  }

  // =============================== 13. the flower ===============================
  function s13(c, t, q, S) {
    const qStriped = q('the striped ones') - 0.3, qGone = q('and the semper augustus') - 0.3, qQ = q('the question in that tavern') - 0.3, qWho = q('it was who will buy'), qSub = q('subscribe') - 0.4
    paper(c, t)
    if (t < qStriped) {
      // fields today: bands of colour to the horizon
      const cols = ['#b8402e', C.gold, '#f1e7d2', '#b8402e', '#8a2a1e', C.gold]
      for (let k = 0; k < 6; k++) { c.fillStyle = cols[k]; c.beginPath(); c.moveTo(960 - 30 * (k + 1), 420); c.lineTo(960 - 30 * k, 420); c.lineTo(-400 + k * 500, 1080); c.lineTo(-900 + k * 500, 1080); c.closePath(); c.fill() }
      c.fillStyle = INK; c.fillRect(0, 410, W, 14)
      text(c, 'less than $1 a bulb', W / 2, 240, F.head(80, 900), INK, { alpha: prog(t, S.start + 3.2, S.start + 4), stroke: C.paper, sw: 10 })
      finish(c, t, false); return false
    }
    if (t < qQ) {
      ground(c, 900)
      tulip(c, 760, 900, 1.3, { broken: 1, t, seed: 4, flame: '#b8402e' })
      if (t > qGone) { const a = prog(t, qGone + 1, qGone + 3.5); c.save(); c.globalAlpha = 1 - a * 0.85; tulip(c, 1180, 900, 1.5, { broken: 1, t, seed: 11, flame: '#9c2416' }); c.restore(); text(c, 'Semper Augustus', 1180, 300, F.head(64, 900), INK, { alpha: prog(t, qGone + 0.4, qGone + 1) }); text(c, 'none known to survive', 1180, 360, F.bodyI(44), C.red, { alpha: prog(t, qGone + 3, qGone + 3.6) }) }
      else text(c, 'bred, not sick', 760, 300, F.headI(56), INK, { alpha: prog(t, qStriped + 0.6, qStriped + 1.2) })
      finish(c, t, false); return false
    }
    if (t < qSub) {
      room(c, t, { light: 0.45 })
      text(c, 'What is it worth?', W / 2, 260, F.headI(70, 700), C.paper, { alpha: prog(t, qQ + 1.2, qQ + 2) * (1 - prog(t, qWho - 0.4, qWho)), stroke: INK, sw: 8 })
      typeset(c, 'Who will buy it from me tomorrow?', W / 2, 260, F.head(76, 900), C.gold2, prog(t, qWho, qWho + 1.6), { stroke: INK, sw: 10 })
      finish(c, t, true); return true
    }
    text(c, 'HISTORY UNFOLDZ', W / 2, 470, F.head(120, 900), INK, { alpha: prog(t, qSub, qSub + 0.8), track: 12 })
    rule(c, 560, 1360, 520, INK, prog(t, qSub + 0.3, qSub + 1.2))
    text(c, 'Subscribe', W / 2, 640, F.head(90, 900), C.red, { alpha: prog(t, qSub + 0.4, qSub + 1.2) })
    text(c, 'animal facts · history’s greatest battles · the craziest financial collapses', W / 2, 740, F.bodyI(44), INK, { alpha: prog(t, qSub + 2.2, qSub + 3.2) })
    finish(c, t, false); return false
  }

  window.SCENES.push(s8, s9, s10, s11, s12, s13)
})()
