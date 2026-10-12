// scA.js: scenes 1-7 of The Champawat Tiger. Each scene is draw(c, t, q, S) -> true if the picture is dark.
// Paper and ink; the tigress is the one gold; the count and the broken teeth are the one red.
(function () {
  const { clamp, lerp, EZ, prog, bump, rng, noise, track, mix } = K
  const { W, H, C, F, paper, finish, hatch, text, typeset, rule, person, glow, tw } = L
  const { night, eyes } = T2
  const { INK, RED, GOLD, tiger, ridges, terraces, house, deodar, forest, villager, drummer, corbett, sepoy, gorge, brush, skull, marker, camera } = CW
  const label = (c, s, x, y, a, o = {}) => window.__vertical ? null : text(c, s, x, y, o.font || F.headI(64, 700), o.col || INK, { alpha: a, stroke: o.stroke ?? C.paper, sw: 8, ...o })
  const ground = (c, y, col = INK) => { c.strokeStyle = col; c.lineWidth = 4; c.beginPath(); c.moveTo(0, y); c.lineTo(W, y); c.stroke() }
  const zoom = (c, cx, cy, s) => { c.translate(W / 2, H / 2); c.scale(s, s); c.translate(-cx, -cy) }
  // the line of beaters on the ridge: tiny figures along a slope
  function beaters(c, t, x0, x1, y0, y1, n, o = {}) { for (let k = 0; k < n; k++) { const u = k / (n - 1), x = lerp(x0, x1, u), y = lerp(y0, y1, u) + Math.sin(u * 9) * 10; drummer(c, x, y, o.h || 46, t, { ph: k * 0.7, col: o.col || INK, face: o.face || 1 }) } }
  // a village on a slope, with terraces and houses
  function village(c, t, o = {}) {
    ridges(c, t, { d: o.d ?? 1, snow: true, seed: o.seed || 0 })
    terraces(c, 200, 700, 900, 260, mix('rgba(0,0,0,0.3)', 'rgba(30,24,16,0.35)', 1))
    const r = rng(o.seed || 3); for (let k = 0; k < 7; k++) house(c, 260 + k * 230 + r() * 40, 760 + (k % 2) * 40, 0.9, { col: mix('#07080c', INK, o.d ?? 1), lit: o.lit ? 0.7 : 0 })
    forest(c, -40, W + 40, 1000, 1.0, { col: mix('#050607', '#2a2219', o.d ?? 1), seed: 5 })
  }

  // =============================== 1. the beat ===============================
  function s1(c, t, q, S) {
    const qRidge = q('up on the ridge') - 0.3, qFloor = q('down on the floor') - 0.3, qNoise = q('the noise is meant'), qSome = q('something that has been') - 0.3, qRec = q('by the time this day')
    if (t < qFloor) {
      gorge(c, t, { d: 1 })
      beaters(c, t, 40, 620, 200, 520, 12); beaters(c, t, 1300, 1880, 520, 200, 12)
      label(c, 'May 12, 1907', W / 2, 140, prog(t, 0.4, 1.2), { font: F.head(80, 900) })
      text(c, 'Kumaon, northern India', W / 2, 210, F.bodyI(48), C.red, { alpha: prog(t, 1.0, 1.8), stroke: C.paper, sw: 6 })
      finish(c, t, false); return false
    }
    if (t < qSome) {
      gorge(c, t, { d: 1 })
      beaters(c, t, 40, 620, 200, 520, 12); beaters(c, t, 1300, 1880, 520, 200, 12)
      brush(c, 640, 1280, 905, 70, '#3a2e22', 4)
      corbett(c, 960, 1010, 260, { aim: 0.2 })
      finish(c, t, false); return false
    }
    // something in the brush: eyes, the shape of her, gold among the stripes of grass
    gorge(c, t, { d: 0.75 })
    brush(c, 0, W, 1000, 220, '#2a2219', 9)
    const a = prog(t, qSome + 0.6, qSome + 2.0)
    c.save(); c.globalAlpha = a; tiger(c, 900 + Math.sin(t * 0.6) * 20, 1040, 3.0, { crouch: 0.8, head: 0.15, walk: t * 1.2, stride: 0.2, eye: true }); c.restore()
    brush(c, 0, W, 1080, 140, '#1c160f', 3)
    if (t > qRec) typeset(c, '436', W / 2, 260, F.head(160, 900), C.red, prog(t, qRec + 3.0, qRec + 3.8), { stroke: C.paper, sw: 12 })
    finish(c, t, false); return false
  }

  // =============================== 2. Kumaon ===============================
  function s2(c, t, q, S) {
    const qSteep = q('steep slopes') - 0.3, qLife = q('life here depended') - 0.3, qBy = q('but by 1907') - 0.3, qFields = q('the fields went') - 0.3, qNight = q('and at night') - 0.3
    if (t < qBy) {
      village(c, t, {})
      if (t > qLife) for (let k = 0; k < 4; k++) { const p = ((t - qLife) * 0.06 + k * 0.25) % 1; villager(c, lerp(300, 1500, p), 980, 150, { lady: true, load: 1 }) }
      label(c, 'Kumaon, in the Himalayan foothills', W / 2, 150, prog(t, S.start, S.start + 0.8))
      finish(c, t, false); return false
    }
    if (t < qNight) {
      village(c, t, { d: 0.75 })
      if (t > qFields) { c.fillStyle = 'rgba(20,16,12,0.25)'; c.fillRect(0, 0, W, H) }
      label(c, 'nobody goes into the forest', W / 2, 150, prog(t, qBy + 0.8, qBy + 1.6), { col: C.red })
      finish(c, t, false); return false
    }
    village(c, t, { d: 0.05, lit: true })
    for (let k = 0; k < 4; k++) drummer(c, 320 + k * 420, 1000, 170, t, { col: '#05060a', ph: k })
    finish(c, t, true); return true
  }

  // =============================== 3. Nepal ===============================
  function s3(c, t, q, S) {
    const qRupal = q('a tigress began') - 0.3, qHunt = q('hunters went after') - 0.3, qArmy = q('finally the government') - 0.3, qSweep = q('hundreds of soldiers') - 0.3, qMost = q('most accounts say') - 0.3, qMoved = q('the army had not')
    if (t < qArmy) {
      ridges(c, t, { d: 1, snow: true, seed: 7 })
      forest(c, -40, W + 40, 1000, 1.1, { col: '#2a2219', seed: 8 })
      if (t > qHunt) for (let k = 0; k < 3; k++) corbett(c, 500 + k * 300, 1000, 200, { col: '#3a2e22', walk: t * 4 + k, stride: 0.8, face: 1 })
      label(c, 'Nepal, near Rupal', W / 2, 150, prog(t, qRupal + 0.4, qRupal + 1.2))
      finish(c, t, false); return false
    }
    if (t < qMost) {
      // the army's sweep: a long line of soldiers driving east, a gold shape running ahead of them
      ridges(c, t, { d: 1, seed: 7 })
      const p = prog(t, qSweep, qMost, 'l')
      for (let k = 0; k < 16; k++) sepoy(c, -200 + k * 60 + p * 700, 960 + (k % 3) * 18, 140, { walk: t * 6 + k, stride: 0.9 })
      tiger(c, 900 + p * 1100, 990, 1.6, { walk: t * 7, stride: 1, gallop: 1 })
      c.fillStyle = '#6b7a80'; c.fillRect(1500, 1000, 420, 80)
      text(c, 'Sarda River', 1700, 1060, F.sc(40), C.paper)
      label(c, 'NEPAL', 300, 200, prog(t, qSweep, qSweep + 0.6), { font: F.sc(70) }); label(c, 'INDIA', 1650, 200, prog(t, qSweep + 1.6, qSweep + 2.2), { font: F.sc(70) })
      finish(c, t, false); return false
    }
    paper(c, t)
    typeset(c, '~200', W / 2, 500, F.head(220, 900), C.red, prog(t, qMost + 1.6, qMost + 2.6), { track: 8 })
    text(c, 'killed in Nepal, by most accounts', W / 2, 600, F.bodyI(52), INK, { alpha: prog(t, qMost + 2.6, qMost + 3.2) })
    if (t > qMoved) text(c, 'They only moved her.', W / 2, 800, F.head(70, 900), INK, { alpha: prog(t, qMoved + 1.6, qMoved + 2.4) })
    finish(c, t, false); return false
  }

  // =============================== 4. how she hunted ===============================
  function s4(c, t, q, S) {
    const q20 = q('she could cover') - 0.3, qDay = q('most tigers that hunt') - 0.3, qWomen = q('and most of the people') - 0.3, qReward = q('the government put') - 0.3, qCount = q('every death was counted') - 0.3, q200 = q('200')
    if (t < qDay) {
      // a map of the valley: villages as dots, a gold path of a night's travel
      paper(c, t)
      const V = [[300, 700], [520, 420], [760, 640], [980, 360], [1200, 720], [1420, 460], [1640, 640]]
      c.fillStyle = '#b6a27a'; for (let k = 0; k < 40; k++) { const x = (k % 10) * 200 + 60, y = 200 + Math.floor(k / 10) * 200; c.beginPath(); c.moveTo(x - 60, y + 40); c.lineTo(x, y - 30); c.lineTo(x + 60, y + 40); c.closePath(); c.fill() }
      V.forEach(([x, y], k) => { c.fillStyle = INK; c.beginPath(); c.arc(x, y, 14, 0, 7); c.fill() })
      const p = prog(t, q20 + 0.4, qDay, 'io'), n = Math.floor(p * (V.length - 1))
      c.strokeStyle = GOLD; c.lineWidth = 8; c.setLineDash([16, 10]); c.beginPath(); c.moveTo(...V[0]); for (let k = 1; k <= n; k++) c.lineTo(...V[k]); if (n < V.length - 1) { const f = p * (V.length - 1) - n; c.lineTo(lerp(V[n][0], V[n + 1][0], f), lerp(V[n][1], V[n + 1][1], f)) } c.stroke(); c.setLineDash([])
      label(c, '20 miles in a night', W / 2, 150, prog(t, q20 + 0.6, q20 + 1.4), { font: F.head(80, 900) })
      finish(c, t, false); return false
    }
    if (t < qReward) {
      ridges(c, t, { d: 1, seed: 2 })
      c.fillStyle = C.gold2; c.beginPath(); c.arc(1500, 200, 70, 0, 7); c.fill()
      brush(c, 0, W, 1000, 160, '#2a2219', 6)
      villager(c, 760, 990, 230, { lady: true, load: prog(t, qWomen, qWomen + 1) })
      c.save(); c.globalAlpha = 0.9; tiger(c, 1300, 1010, 1.6, { crouch: 0.9, head: 0.2, walk: t * 0.8, stride: 0.15 }); c.restore()
      brush(c, 0, W, 1080, 120, '#1c160f', 8)
      label(c, 'in broad daylight', W / 2, 160, prog(t, qDay + 2.4, qDay + 3.2))
      finish(c, t, false); return false
    }
    paper(c, t)
    if (t < q200 - 0.6) {
      // the reward notice, and hunters who never got near her
      c.fillStyle = '#f3ead6'; c.fillRect(660, 220, 600, 420); c.strokeStyle = INK; c.lineWidth = 3; c.strokeRect(660, 220, 600, 420)
      text(c, 'REWARD', W / 2, 330, F.head(90, 900), C.red); text(c, 'for the man-eater', W / 2, 400, F.bodyI(48), INK); for (let k = 0; k < 5; k++) c.fillRect(720, 450 + k * 30, 480, 4)
      ground(c, 940); for (let k = 0; k < 4; k++) corbett(c, 360 + k * 400, 940, 210, { face: k % 2 ? -1 : 1, walk: t * 3 + k, stride: 0.6 })
      finish(c, t, false); return false
    }
    // the count
    const n = Math.floor(lerp(0, 400, prog(t, q200 - 0.6, q200 + 2.6, 'l')) / 100) * 100
    typeset(c, n ? String(n) : '', W / 2, 600, F.head(260, 900), C.red, 1, { track: 10 })
    const r = rng(6); for (let k = 0; k < Math.floor(n / 4); k++) { c.fillStyle = INK; c.fillRect(160 + (k % 50) * 32, 760 + Math.floor(k / 50) * 30, 4, 20) }
    finish(c, t, false); return false
  }

  // =============================== 5. why ===============================
  function s5(c, t, q, S) {
    const qHealthy = q('a healthy tiger') - 0.3, qAns = q('the answer to why') - 0.3, qTwo = q('two of her big teeth') - 0.3, qShot = q('most likely') - 0.3, qCould = q('she could no longer') - 0.3, qPeople = q('people were slower')
    if (t < qAns) {
      ridges(c, t, { d: 1, seed: 4 })
      if (t > qHealthy) { const p = prog(t, qHealthy, qAns, 'l'); tiger(c, lerp(-200, 1200, p), 1000, 1.8, { walk: t * 9, stride: 1, gallop: 1 }); for (let k = 0; k < 3; k++) { const x = lerp(200, 1500, p) + k * 120, y = 990; c.fillStyle = '#3a2e22'; c.beginPath(); c.ellipse(x, y - 60, 46, 22, 0, 0, 7); c.fill(); c.fillRect(x - 36, y - 46, 6, 46); c.fillRect(x + 30, y - 46, 6, 46); c.beginPath(); c.ellipse(x + 50, y - 80, 14, 10, -0.4, 0, 7); c.fill(); c.fillRect(x + 50, y - 110, 3, 26) } }
      label(c, 'Tigers do not normally hunt people.', W / 2, 160, prog(t, S.start, S.start + 0.8))
      finish(c, t, false); return false
    }
    paper(c, t, '#e8dcc0')
    skull(c, 900, 600, 1.6, { hl: t > qTwo + 1, ghost: t > qTwo + 3 })
    if (t > qTwo) { text(c, 'snapped in half', 1300, 860, F.headI(48), C.red, { alpha: prog(t, qTwo + 2.6, qTwo + 3.2), align: 'left' }); text(c, 'broken to the bone', 1300, 930, F.headI(48), C.red, { alpha: prog(t, qTwo + 4.0, qTwo + 4.6), align: 'left' }) }
    if (t > qShot) label(c, 'an old gunshot wound', W / 2, 140, prog(t, qShot + 0.6, qShot + 1.4))
    if (t > qPeople) text(c, 'People were slower. And easier.', W / 2, 1000, F.head(64, 900), INK, { alpha: prog(t, qPeople, qPeople + 0.8) })
    finish(c, t, false); return false
  }

  // =============================== 6. Corbett ===============================
  function s6(c, t, q, S) {
    const qBorn = q('he was 31') - 0.3, qRead = q('he could read tracks') - 0.3, qJob = q('he had a job') - 0.3, qCond = q('when the government asked') - 0.3, qReward = q('the reward on her head') - 0.3, qPaid = q('he did not want to be paid')
    if (t < qJob) {
      ridges(c, t, { d: 1, seed: 9 })
      forest(c, -40, W + 40, 1000, 1.0, { col: '#2a2219', seed: 2 })
      corbett(c, 900, 1000, 320, { arm: 0.15, face: 1 })
      label(c, 'Jim Corbett', W / 2, 150, prog(t, S.start + 0.4, S.start + 1.2), { font: F.head(90, 900) })
      text(c, 'born in Nainital, 1875', W / 2, 220, F.bodyI(48), C.red, { alpha: prog(t, qBorn + 1.0, qBorn + 1.8), stroke: C.paper, sw: 6 })
      if (t > qRead) { const r = rng(4); for (let k = 0; k < 6; k++) { const a = prog(t, qRead + 0.4 + k * 0.3, qRead + 0.8 + k * 0.3); c.fillStyle = `rgba(26,21,18,${a})`; const px = 1200 + k * 90, py = 990 - (k % 2) * 30; for (const [dx, dy, rr] of [[0, 0, 12], [-12, -16, 5], [-4, -20, 5], [6, -20, 5], [13, -15, 5]]) { c.beginPath(); c.arc(px + dx, py + dy, rr, 0, 7); c.fill() } } }
      finish(c, t, false); return false
    }
    if (t < qCond) {
      paper(c, t); ground(c, 900)
      T2.train(c, lerp(-600, 1000, prog(t, qJob - 0.4, qCond, 'o')), 900, 1.2, t, {})
      label(c, 'the railway', W / 2, 160, prog(t, qJob + 0.6, qJob + 1.4))
      finish(c, t, false); return false
    }
    paper(c, t)
    text(c, 'Two conditions', W / 2, 230, F.head(90, 900), INK, { alpha: prog(t, qCond + 1.6, qCond + 2.4) })
    typeset(c, '1. Cancel the reward.', W / 2, 470, F.head(80, 900), C.red, prog(t, qReward, qReward + 1.2))
    typeset(c, '2. Call off every other hunter.', W / 2, 620, F.head(80, 900), C.red, prog(t, qReward + 2.6, qReward + 3.8))
    finish(c, t, false); return false
  }

  // =============================== 7. the search ===============================
  function s7(c, t, q, S) {
    const qLate = q('he was always too late') - 0.3, qWeeks = q('weeks went by') - 0.3, qCham = q('then he reached') - 0.3, qPhun = q('and word came')
    ridges(c, t, { d: 1, seed: 11 })
    const p = (t - S.start) * 0.05
    for (let k = 0; k < 4; k++) house(c, 300 + k * 450 - (p * 600 % 450), 960, 0.9, {})
    forest(c, -40, W + 40, 1040, 0.9, { col: '#2a2219', seed: 6 })
    corbett(c, 820, 1000, 260, { walk: t * 4, stride: 0.8, face: 1 })
    if (t > qCham) villager(c, 1000, 1000, 250, { face: 1, walk: t * 4 + 1, stride: 0.8, col: '#2a2219' })
    label(c, t > qCham ? 'Champawat, and the tahsildar' : 'village to village', W / 2, 150, t > qCham ? prog(t, qCham + 0.8, qCham + 1.6) : prog(t, S.start, S.start + 0.8))
    if (t > qPhun) label(c, 'Phungar', W / 2, 240, prog(t, qPhun + 1.6, qPhun + 2.4), { col: C.red, font: F.head(80, 900) })
    finish(c, t, false); return false
  }

  window.SCENES = [s1, s2, s3, s4, s5, s6, s7]
  window.CWA = { label, ground, zoom, beaters, village }
})()
