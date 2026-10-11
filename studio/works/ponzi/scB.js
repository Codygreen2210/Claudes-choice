// scB.js: scenes 8-13 of Ponzi.
(function () {
  const { clamp, lerp, EZ, prog, bump, rng, noise, track } = K
  const { W, H, C, F, paper, finish, hatch, rr, text, typeset, rule, person, crowd, glow, tw, bank, block, clock, coin, money } = L
  const { ponzi, cop, liner, car, coupon, stamp, bills, pawn, bars, palm, page } = PZ
  const { fade, zoom, ground, street, queue, flow, RV, QUEUE } = PZS

  // =============================== 8. the arithmetic ===============================
  function s8(c, t, q, S) {
    const qNot = q('he was not earning') - 0.3, qEv = q('and every new investor'), qSay = q('say 100 people') - 0.4, qHas = q('he has 10000'), qOwes = q('in 45 days he owes') - 0.3, qMiss = q('the missing 5000') - 0.3, qNow = q('and now he owes'), qSo = q('so to pay them') - 0.4, qHole = q('the hole got deeper'), qSch = q('a scheme like that') - 0.4, qEnds = q('it ends when')
    paper(c, t)
    if (t < qSay + 0.3) {
      text(c, 'where the payouts came from', W / 2, 190, F.headI(72, 700), C.ink, { alpha: prog(t, S.start, S.start + 0.5) })
      ponzi(c, 960, 800, 330, { arm: 0.4 })
      for (let i = 0; i < 10; i++) pawn(c, 300 + (i % 5) * 84, 520 + Math.floor(i / 5) * 120, 2.0, t > qNot + 1 ? 1 : 0)
      for (let i = 0; i < 15; i++) pawn(c, 1260 + (i % 5) * 84, 460 + Math.floor(i / 5) * 120, 2.0, t > qEv ? 2 : 0)
      text(c, 'old investors: paid', 470, 800, F.bodyI(46), C.gold, { alpha: prog(t, qNot + 1, qNot + 1.5) }); text(c, 'new investors: owed 50% more', 1430, 860, F.bodyI(46), C.red, { alpha: prog(t, qEv, qEv + 0.5) })
      if (t > qNot) { flow(c, 1230, 600, 1020, 600, t, 7, 0.5, 13); flow(c, 900, 600, 700, 600, t + 0.4, 7, 0.5, 13) }
      text(c, 'earnings: $0', 960, 330, F.head(84, 900), C.red, { alpha: prog(t, qNot, qNot + 0.4) })
      finish(c, t, false); return false
    }
    if (t < qSo + 0.3) {
      // one round, in round numbers
      const base = 840, sc = 0.036, h10 = 10000 * sc, h15 = 15000 * sc
      for (let i = 0; i < 100; i++) { const a = prog(t, qSay + 0.4 + i * 0.008, qSay + 0.6 + i * 0.008); if (a > 0) pawn(c, 150 + (i % 20) * 30, 330 + Math.floor(i / 20) * 46, 0.72, 0) }
      text(c, '100 people × $100', 440, 250, F.headI(52, 700), C.ink, { alpha: prog(t, qSay + 0.4, qSay + 0.9) })
      c.strokeStyle = C.ink; c.lineWidth = 4; c.beginPath(); c.moveTo(880, base); c.lineTo(1760, base); c.stroke()
      const a1 = prog(t, qHas - 0.3, qHas + 0.5, 'o'); c.fillStyle = C.gold; c.fillRect(980, base - h10 * a1, 260, h10 * a1); c.strokeStyle = C.ink; c.strokeRect(980, base - h10 * a1, 260, h10 * a1)
      text(c, 'has', 1110, base + 64, F.headI(54, 700), C.ink, { alpha: a1 }); text(c, '$10,000', 1110, base - h10 - 24, F.head(60, 900), C.ink, { alpha: clamp(a1 * 2 - 1) })
      const a2 = prog(t, qOwes + 0.5, qOwes + 1.4, 'o'); c.save(); c.strokeStyle = C.red2; c.lineWidth = 8; c.setLineDash([18, 12]); c.strokeRect(1400, base - h15 * a2, 260, h15 * a2); c.restore()
      text(c, 'owes', 1530, base + 64, F.headI(54, 700), C.red, { alpha: a2 }); text(c, '$15,000', 1530, base - h15 - 24, F.head(60, 900), C.red, { alpha: clamp(a2 * 2 - 1) })
      const a3 = prog(t, qMiss, qMiss + 0.6); if (a3 > 0) { c.save(); c.globalAlpha = a3; c.fillStyle = C.red2; c.fillRect(1400, base - h15, 260, h15 - h10); c.restore(); text(c, 'missing', 1530, base - h10 - (h15 - h10) / 2 - 6, F.headI(40, 700), C.paper, { alpha: a3 }); text(c, '$5,000', 1530, base - h10 - (h15 - h10) / 2 + 44, F.head(52, 900), C.paper, { alpha: a3 }) }
      const a4 = prog(t, qNow - 0.2, qNow + 0.6); for (let i = 0; i < 50; i++) { const a = clamp(a4 * 3 - i * 0.04); if (a > 0) pawn(c, 150 + (i % 20) * 30, 600 + Math.floor(i / 20) * 46, 0.72, 2) }
      text(c, '50 new people... each owed 50% too', 440, 790, F.bodyI(42), C.red, { alpha: prog(t, qNow, qNow + 0.5) })
      finish(c, t, false); return false
    }
    if (t < qSch + 0.3) {
      // round after round: what he has, what he owes
      const base = 860, n = 7, p = prog(t, qSo + 0.4, qHole + 1.8, 'l') * n
      c.strokeStyle = C.ink; c.lineWidth = 4; c.beginPath(); c.moveTo(200, base); c.lineTo(1720, base); c.stroke()
      for (let k = 0; k < n; k++) { const a = clamp(p - k); if (a <= 0) continue; const has = 60 * Math.pow(1.38, k), owes = has * 1.5 + k * 22, x = 300 + k * 200; c.fillStyle = C.gold; c.fillRect(x - 70, base - has * a, 64, has * a); c.fillStyle = C.red2; c.fillRect(x + 6, base - owes * a, 64, owes * a); text(c, 'day ' + (45 * (k + 1)), x, base + 54, F.bodyI(34), C.ink, { alpha: a }) }
      text(c, 'has', 420, 250, F.headI(64, 700), C.gold); text(c, 'owes', 640, 250, F.headI(64, 700), C.red)
      typeset(c, 'the hole got deeper every day', 600, 400, F.headI(60, 700), C.ink, prog(t, qHole - 0.1, qHole + 1.4))
      finish(c, t, false); return false
    }
    // it ends when you run out of people
    const rows = Math.floor(lerp(1, 9, prog(t, qSch + 0.3, qEnds + 0.4, 'l')))
    for (let r = 0; r <= rows; r++) { const n = Math.min(40, Math.round(Math.pow(1.6, r))), y = 180 + r * 86, last = r === 9 || (r === rows && rows >= 8 && t > qEnds); for (let i = 0; i < n; i++) pawn(c, 960 + (i - (n - 1) / 2) * Math.min(80, 1700 / n), y, Math.min(1.5, 34 / Math.max(8, n) * 2.0 + 0.5), r >= 8 ? 3 : r === rows ? 0 : 1) }
    text(c, 'it ends when', 400, 250, F.headI(64, 700), C.red, { alpha: prog(t, qEnds, qEnds + 0.5) }); text(c, 'you run out of people', 400, 330, F.headI(64, 700), C.red, { alpha: prog(t, qEnds + 0.4, qEnds + 0.9) })
    finish(c, t, false); return false
  }

  // =============================== 9. the Post ===============================
  function s9(c, t, q, S) {
    const qTwo = q('two days later') - 0.4, qBar = q('a financial writer named') - 0.4, qAr = q('did the arithmetic'), qCrowd = q('the crowd came back') - 0.4, qWant = q('this time they wanted'), qPaid = q('and ponzi paid') - 0.3, q2m = q('2 million in three'), qSm = q('smiling the whole'), qFew = q('for a few days') - 0.3
    if (t < qCrowd + 0.3) {
      paper(c, t, C.paper2)
      const second = prog(t, qTwo, qTwo + 0.8, 'io')
      page(c, lerp(960, 520, second), 540, 0.98, -0.03, { date: 'Saturday, July 24, 1920', head: ['DOUBLES THE MONEY', 'WITHIN THREE MONTHS'], hpx: 62, sub: '50 per cent interest paid in 45 days by Ponzi' })
      if (second > 0) page(c, lerp(2500, 1400, second), 540, 0.98, 0.03, { date: 'Monday, July 26, 1920', head: ['QUESTIONS THE', 'MOTIVE BEHIND', 'PONZI SCHEME'], hpx: 62, hcol: C.red, draw: (k, y0) => { const a = prog(t, qAr - 0.2, qAr + 0.6); if (a > 0) { k.save(); k.globalAlpha = a; k.fillStyle = '#f4ead2'; k.fillRect(-380, y0 + 40, 760, 330); text(k, 'coupons needed: 160,000,000', 0, y0 + 130, F.old(44, true), C.ink); text(k, 'coupons in existence: 27,000', 0, y0 + 220, F.old(44, true), C.red); text(k, '— C. W. Barron', 0, y0 + 310, F.bodyI(40), C.ink2); k.restore() } } })
      finish(c, t, false); return false
    }
    // the run on School Street
    paper(c, t)
    const calm = prog(t, qFew, qFew + 1.5), ang = (prog(t, qWant - 0.2, qWant + 0.4) * (1 - prog(t, qSm, qSm + 2.0))) 
    const cx = track(t, [[qCrowd, 2400], [qPaid, 3700, 'io']])
    c.save(); zoom(c, cx, 580, 1.15); street(c, t); queue(c, t, { cash: 0, angry: ang, x0: 1400, x1: 3780, n: 30 })
    ponzi(c, 3900, 800, 196, { face: -1, arm: 0.5 })
    if (t > qPaid) flow(c, 3880, 660, 3600, 660, t, 9, 0.7, 12)
    if (t > qSm) for (let i = 0; i < 6; i++) { const x = 3000 + i * 130, a = prog(t, qSm + 0.4 + i * 0.2, qSm + 0.7 + i * 0.2, 'back'); if (a <= 0) continue; c.save(); c.translate(x, 560); c.scale(a, a); c.fillStyle = C.ink; if (i % 2) { c.fillRect(-12, -14, 24, 26); c.strokeStyle = C.ink; c.lineWidth = 4; c.beginPath(); c.arc(14, -1, 8, -1.3, 1.3); c.stroke() } else { c.beginPath(); c.arc(0, 0, 16, 0, 7); c.fill(); c.fillStyle = C.paper; c.beginPath(); c.arc(0, 0, 6, 0, 7); c.fill() } c.restore() }
    c.restore()
    const m = prog(t, q2m - 0.3, q2m + 1.2, 'o')
    { const pa = prog(t, q2m - 0.4, q2m); if (pa > 0) { c.save(); c.globalAlpha = 0.92 * pa; c.fillStyle = C.paper; c.fillRect(100, 84, 850, 300); c.globalAlpha = pa; c.strokeStyle = C.ink; c.lineWidth = 3; c.strokeRect(100, 84, 850, 300); c.restore() } }
    text(c, money(2000000 * m), 520, 200, F.head(120, 900), C.ink, { alpha: prog(t, q2m - 0.3, q2m), stroke: C.paper, sw: 10 }); text(c, 'paid out in three days', 520, 280, F.headI(56, 700), C.ink, { alpha: prog(t, q2m + 0.8, q2m + 1.3), stroke: C.paper, sw: 8 })
    typeset(c, 'coffee and doughnuts for the line', 520, 348, F.bodyI(50), C.red, prog(t, q('coffee and doughnuts') - 0.2, q('coffee and doughnuts') + 1.6), { stroke: C.paper, sw: 8 })
    finish(c, t, false); return false
  }

  // =============================== 10. the fall ===============================
  function s10(c, t, q, S) {
    const qHead = q('the headline said') - 0.4, qAug = q('on august 11') - 0.4, qMug = q('a mug shot') - 0.2, qAft = q('that afternoon') - 0.4, qWith = q('within two days') - 0.4, q86 = q('he was charged')
    if (t < qHead + 0.3) {
      paper(c, t); const gy = 860; ground(c, gy)
      c.fillStyle = C.ink; c.fillRect(1100, gy - 230, 560, 20); c.fillRect(1130, gy - 210, 18, 210); c.fillRect(1612, gy - 210, 18, 210)
      for (let i = 0; i < 5; i++) { c.fillStyle = '#f4ead2'; c.strokeStyle = C.ink; c.lineWidth = 3; c.save(); c.translate(1220 + i * 90, gy - 246); c.rotate(-0.1 + i * 0.05); c.fillRect(-40, -8, 80, 12); c.strokeRect(-40, -8, 80, 12); c.restore() }
      const px = track(t, [[S.vis, 1380], [S.start + 3.2, 1380], [qHead, 300, 'i']])
      person(c, px, gy, 320, { hat: 'bowler', col: C.ink, face: -1, walk: px * 0.04, stride: t > S.start + 3.2 ? 1 : 0, arm: 0.35, hold: k => { k.fillStyle = '#f4ead2'; k.strokeStyle = C.ink; k.lineWidth = 1.5; k.fillRect(-10, 22, 30, 22); k.strokeRect(-10, 22, 30, 22) } })
      typeset(c, 'William McMasters, his publicist', 620, 200, F.headI(60, 700), C.ink, prog(t, S.start + 0.5, S.start + 2.2))
      finish(c, t, false); return false
    }
    if (t < qAug + 0.3) {
      paper(c, t, C.paper2)
      page(c, 960, 540 + (1 - prog(t, qHead + 0.3, qHead + 0.9, 'o')) * 900, 1.0, -0.02, { date: 'Monday, August 2, 1920', head: ['DECLARES PONZI', 'IS NOW HOPELESSLY', 'INSOLVENT'], hpx: 66, hcol: C.red })
      finish(c, t, false); return false
    }
    if (t < qAft + 0.3) {
      // the mug shot
      c.fillStyle = '#17130f'; c.fillRect(0, 0, W, H)
      const a = prog(t, qMug - 0.2, qMug + 0.4, 'o')
      c.save(); c.translate(960, 540); c.rotate(-0.02); c.scale(0.9 + 0.1 * a, 0.9 + 0.1 * a); c.globalAlpha = a; c.fillStyle = '#d9cdb0'; c.fillRect(-520, -330, 1040, 660); c.strokeStyle = '#17130f'; c.lineWidth = 4; c.strokeRect(-500, -310, 1000, 620); c.beginPath(); c.moveTo(0, -310); c.lineTo(0, 190); c.stroke(); c.beginPath(); c.moveTo(-500, 190); c.lineTo(500, 190); c.stroke()
      // front and profile: a head and shoulders, no face
      c.fillStyle = '#17130f'; c.beginPath(); c.ellipse(-250, -80, 78, 96, 0, 0, 7); c.fill(); c.beginPath(); c.moveTo(-420, 190); c.quadraticCurveTo(-420, 40, -250, 30); c.quadraticCurveTo(-80, 40, -80, 190); c.closePath(); c.fill()
      c.beginPath(); c.ellipse(240, -80, 84, 96, 0, 0, 7); c.fill(); c.beginPath(); c.moveTo(316, -90); c.lineTo(350, -56); c.lineTo(318, -40); c.closePath(); c.fill(); c.beginPath(); c.moveTo(110, 190); c.quadraticCurveTo(100, 40, 240, 30); c.quadraticCurveTo(400, 44, 410, 190); c.closePath(); c.fill()
      text(c, 'Montreal', -250, 262, F.old(48, true), '#17130f', { track: 4 }); text(c, 'forgery · 1908', 250, 262, F.old(44, true), '#17130f', { track: 2 })
      c.restore()
      text(c, 'the Boston Post, August 11', W / 2, 110, F.headI(56, 700), C.paper2, { alpha: prog(t, qAug + 0.5, qAug + 1.0) })
      finish(c, t, true); return true
    }
    if (t < qWith + 0.3) {
      paper(c, t); const gy = 860; ground(c, gy)
      bank(c, 960, gy, 800, 640, { cols: 6, sign: 'HANOVER TRUST CO.', signPx: 44, fill: C.paper2 })
      const a = prog(t, qAft + 0.8, qAft + 1.1, 'back'); if (a > 0) { c.save(); c.translate(960, gy - 345); c.rotate(-0.06); c.scale(a, a); c.fillStyle = '#f4ead2'; c.fillRect(-300, -80, 600, 160); c.strokeStyle = C.red; c.lineWidth = 10; c.strokeRect(-300, -80, 600, 160); text(c, 'CLOSED', 0, 20, F.head(110, 900), C.red, { track: 10 }); text(c, 'by order of the Bank Commissioner', 0, 62, F.bodyI(30), C.ink); c.restore() }
      cop(c, 700, gy, 260, {}); cop(c, 1220, gy, 260, { face: -1 })
      finish(c, t, false); return false
    }
    paper(c, t); const gy = 860; ground(c, gy)
    for (let i = 0; i < 8; i++) { c.fillStyle = C.paper3; c.strokeStyle = C.ink; c.lineWidth = 4; c.fillRect(1180 + i * 0, 0, 0, 0) }
    bank(c, 1450, gy, 700, 640, { cols: 6, sign: 'UNITED STATES COURT', signPx: 40, fill: C.paper2 })
    const px = track(t, [[qWith, 200], [q86, 1050, 'o']]); ponzi(c, px, gy, 260, { walk: px * 0.04, stride: t < q86 - 0.1 ? 0.9 : 0 })
    cop(c, px - 150, gy, 300, { walk: px * 0.04, stride: t < q86 - 0.1 ? 0.9 : 0 })
    text(c, '86 counts of mail fraud', 620, 220, F.head(84, 900), C.red, { alpha: prog(t, q86 + 0.6, q86 + 1.0) })
    typeset(c, 'August 1920', 620, 300, F.bodyI(56), C.ink, prog(t, qWith + 0.5, qWith + 1.5))
    finish(c, t, false); return false
  }

  // =============================== 11. the bill ===============================
  function s11(c, t, q, S) {
    const qToday = q('in todays money') - 0.3, q6 = q('six banks') - 0.4, qPeople = q('the people who trusted') - 0.4, q30 = q('less than 30 cents'), qWhole = q('the whole thing') - 0.4
    paper(c, t)
    if (t < q6 + 0.3) {
      const m = prog(t, S.start + 0.6, S.start + 2.0, 'o')
      text(c, money(20000000 * m), W / 2, 460, F.head(230, 900), C.red, { alpha: prog(t, S.start + 0.4, S.start + 0.8) }); text(c, 'lost', W / 2, 580, F.headI(90, 700), C.ink, { alpha: prog(t, S.start + 1.8, S.start + 2.2) })
      typeset(c, 'more than $300 million in today’s money', W / 2, 760, F.bodyI(64), C.ink2, prog(t, qToday, qToday + 1.8))
      finish(c, t, false); return false
    }
    if (t < qPeople + 0.3) {
      const gy = 840; ground(c, gy)
      for (let i = 0; i < 6; i++) { const f = prog(t, q6 + 0.5 + i * 0.3, q6 + 1.2 + i * 0.3, 'i'); c.save(); c.translate(210 + i * 300 + 130, gy); c.rotate(f * 0.5); c.translate(-(210 + i * 300 + 130), -gy); bank(c, 210 + i * 300, gy, 240, 420, { cols: 4, fill: C.paper2, sign: i === 0 ? 'HANOVER TRUST' : 'BANK', signPx: 20, track: 0, signCol: f > 0.3 ? C.red : C.ink }); c.restore() }
      text(c, 'six banks failed', W / 2, 220, F.head(110, 900), C.ink, { alpha: prog(t, q6 + 0.3, q6 + 0.7) })
      finish(c, t, false); return false
    }
    if (t < qWhole + 0.3) {
      // thirty cents on the dollar
      const a = prog(t, q30 - 0.6, q30 + 0.6, 'o')
      c.fillStyle = C.paper3; c.strokeStyle = C.ink; c.lineWidth = 8; c.beginPath(); c.arc(700, 540, 300, 0, 7); c.fill(); c.stroke()
      c.fillStyle = C.gold; c.beginPath(); c.moveTo(700, 540); c.arc(700, 540, 296, -Math.PI / 2, -Math.PI / 2 + a * 0.29 * Math.PI * 2); c.closePath(); c.fill(); c.strokeStyle = C.ink; c.lineWidth = 4; c.stroke()
      text(c, '$1', 620, 660, F.head(190, 900), C.ink3, { alpha: 0.6 })
      text(c, 'less than 30¢', 1400, 480, F.head(110, 900), C.ink, { alpha: prog(t, q30, q30 + 0.4) }); text(c, 'back on every dollar', 1400, 570, F.headI(60, 700), C.ink, { alpha: prog(t, q30 + 0.5, q30 + 1.0) })
      finish(c, t, false); return false
    }
    // eight months
    const months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG'], p = prog(t, qWhole + 0.4, qWhole + 3.4, 'l')
    months.forEach((m, i) => { const a = clamp(p * 8 - i), x = 240 + i * 206; c.fillStyle = i === 7 ? C.red2 : C.gold; c.globalAlpha = a; c.fillRect(x - 90, 440, 180, 180); c.globalAlpha = 1; c.strokeStyle = C.ink; c.lineWidth = 4; c.strokeRect(x - 90, 440, 180, 180); text(c, m, x, 556, F.head(64, 900), C.ink, { alpha: 0.35 + 0.65 * a }) })
    text(c, '1920', W / 2, 330, F.head(130, 900), C.ink); text(c, 'first investor to handcuffs: about eight months', W / 2, 780, F.headI(60, 700), C.ink, { alpha: prog(t, qWhole + 2.6, qWhole + 3.2) })
    finish(c, t, false); return false
  }

  // =============================== 12. the rest of his life ===============================
  function s12(c, t, q, S) {
    const qState = q('then to state prison') - 0.3, qThief = q('a common and notorious'), qBail = q('in between out on bail') - 0.4, qSw = q('and sold swampland'), q34 = q('in 1934') - 0.4, qRose = q('his wife rose') - 0.4, qDied = q('he died in 1949') - 0.4, q75 = q('he left 75') - 0.3
    if (t < qBail + 0.3) {
      c.fillStyle = '#17130f'; c.fillRect(0, 0, W, H); glow(c, 960, 500, 700, '201,151,58', 0.14)
      ponzi(c, 960, 900, 430, { col: '#050404', cane: false, gold: false })
      bars(c, 60, W - 60, 0, H, 1, '#050404', 150, 30)
      text(c, 'federal prison · 5 years', W / 2, 150, F.headI(64, 700), C.paper2, { alpha: prog(t, S.start + 0.4, S.start + 0.9) * (1 - prog(t, qState, qState + 0.4)), shadow: '#000' })
      text(c, 'state prison · 7 to 9 years', W / 2, 150, F.headI(64, 700), C.paper2, { alpha: prog(t, qState + 0.3, qState + 0.8), shadow: '#000' })
      typeset(c, '“a common and notorious thief”', W / 2, 400, F.headI(64, 700), C.gold2, prog(t, qThief - 0.2, qThief + 1.6), { shadow: '#000' })
      finish(c, t, true); return true
    }
    if (t < q34 + 0.3) {
      paper(c, t); const gy = 800
      c.fillStyle = C.paper3; c.fillRect(0, gy, W, 300); hatch(c, k => k.rect(0, gy, W, 300), { gap: 11, alpha: 0.35, angle: 0, box: [0, gy, W, 300], wob: 4 }); c.strokeStyle = C.ink; c.lineWidth = 4; c.beginPath(); c.moveTo(0, gy); c.lineTo(W, gy); c.stroke()
      for (const [x, s] of [[200, 1.5], [520, 1.1], [1700, 1.6], [1420, 1.0]]) palm(c, x, gy + 10, s)
      c.strokeStyle = C.ink; c.lineWidth = 4; const r = rng(4); for (let i = 0; i < 60; i++) { const x = r() * W, y = gy + 20 + r() * 200; c.beginPath(); c.moveTo(x, y); c.lineTo(x - 6, y - 26 - r() * 20); c.moveTo(x + 5, y); c.lineTo(x + 12, y - 22 - r() * 20); c.stroke() }
      const sa = prog(t, qSw - 0.2, qSw + 0.4, 'o'); c.save(); c.translate(960, gy + 30 + (1 - sa) * 500); c.fillStyle = C.ink; c.fillRect(-10, -260, 20, 300); c.fillStyle = '#f4ead2'; c.strokeStyle = C.ink; c.lineWidth = 5; c.fillRect(-290, -470, 580, 230); c.strokeRect(-290, -470, 580, 230); text(c, 'LAND FOR SALE', 0, -390, F.head(60, 900), C.ink, { track: 4 }); text(c, '200% in 60 days', 0, -300, F.headI(60, 700), C.red); c.restore()
      ponzi(c, 1280, gy + 14, 240, { face: -1, arm: 0.5 })
      text(c, 'Florida, 1925', 330, 170, F.headI(72, 700), C.ink, { alpha: prog(t, qBail + 0.5, qBail + 1.0) })
      typeset(c, 'some of it under water', 1500, 170, F.bodyI(52), C.red, prog(t, qSw + 0.8, qSw + 2.0))
      finish(c, t, false); return false
    }
    if (t < qDied + 0.3) {
      paper(c, t); const hy = 660; c.strokeStyle = C.ink; c.lineWidth = 4; c.beginPath(); c.moveTo(0, hy); c.lineTo(W, hy); c.stroke(); hatch(c, k => k.rect(0, hy + 2, W, 500), { gap: 13, alpha: 0.3, angle: 0, box: [0, hy, W, 500], wob: 3 })
      const r = rng(9); for (let i = 0; i < 9; i++) block(c, -40 + i * 86, hy, 76, 120 + r() * 220, { fill: C.ink2 })
      const lx = track(t, [[q34, 620], [qDied, 1900, 'i']]); liner(c, lx, hy + 30, 1.3, { t })
      text(c, 'deported, 1934', 1300, 200, F.head(90, 900), C.ink, { alpha: prog(t, q34 + 0.3, q34 + 0.7) })
      if (t > qRose) { const a = prog(t, qRose, qRose + 0.5); c.save(); c.globalAlpha = a; person(c, 420 - (t - qRose) * 14, hy + 240, 300, { lady: true, col: C.ink, face: -1 }); c.restore(); typeset(c, 'Rose divorced him in 1937', 840, 922, F.headI(48, 700), C.ink, prog(t, qRose + 1.6, qRose + 3.0), { stroke: C.paper, sw: 8 }) }
      finish(c, t, false); return false
    }
    // Rio
    c.fillStyle = '#17130f'; c.fillRect(0, 0, W, H); c.fillStyle = '#0e0b09'; c.fillRect(0, 820, W, 260)
    c.fillStyle = '#d9cdb0'; c.fillRect(1250, 200, 300, 380); c.fillStyle = '#17130f'; c.fillRect(1394, 200, 12, 380); c.fillRect(1250, 380, 300, 12); glow(c, 1400, 390, 700, '217,205,176', 0.16)
    c.fillStyle = '#050404'; c.fillRect(440, 760, 640, 22); c.fillRect(430, 660, 20, 160); c.fillRect(1070, 700, 20, 120); c.beginPath(); c.moveTo(470, 760); c.bezierCurveTo(520, 690, 900, 700, 1060, 760); c.closePath(); c.fill(); c.beginPath(); c.arc(510, 726, 30, 0, 7); c.fill()
    text(c, 'Rio de Janeiro, 1949', 560, 200, F.headI(72, 700), C.paper2, { alpha: prog(t, qDied + 0.6, qDied + 1.1), shadow: '#000' })
    for (let i = 0; i < 3; i++) { const a = prog(t, q75 + 0.2 + i * 0.2, q75 + 0.5 + i * 0.2, 'back'); if (a > 0) coin(c, 1500 + i * 70, 800, 26 * a, 1) }
    text(c, '$75', 1570, 720, F.head(130, 900), C.gold2, { alpha: prog(t, q75, q75 + 0.4), shadow: '#000' })
    fade(c, 1 - prog(t, qDied + 0.3, qDied + 0.7)); finish(c, t, true); return true
  }

  // =============================== 13. the question ===============================
  const icon = {
    paw: (c) => { c.beginPath(); c.ellipse(0, 22, 40, 34, 0, 0, 7); c.fill(); for (const [x, y, r] of [[-46, -22, 17], [-17, -48, 18], [17, -48, 18], [46, -22, 17]]) { c.beginPath(); c.ellipse(x, y, r * 0.85, r, x * 0.006, 0, 7); c.fill() } },
    swords: (c) => { for (const s of [-1, 1]) { c.save(); c.rotate(s * 0.78); c.fillRect(-6, -84, 12, 126); c.beginPath(); c.moveTo(-6, -84); c.lineTo(0, -102); c.lineTo(6, -84); c.fill(); c.fillRect(-28, 36, 56, 10); c.fillRect(-5, 46, 10, 30); c.beginPath(); c.arc(0, 82, 9, 0, 7); c.fill(); c.restore() } },
    crash: (c) => { c.lineWidth = 11; c.lineJoin = 'round'; c.lineCap = 'round'; c.beginPath(); c.moveTo(-84, 20); c.lineTo(-44, -30); c.lineTo(-14, -8); c.lineTo(16, -64); c.lineTo(44, 44); c.lineTo(84, 70); c.stroke(); c.beginPath(); c.moveTo(84, 70); c.lineTo(52, 72); c.lineTo(76, 44); c.closePath(); c.fill(); c.stroke() },
  }
  function s13(c, t, q, S) {
    const qBut = q('but it has carried') - 0.4, qExp = q('he explained it') - 0.4, qMy = q('my business was simple'), qRob = q('robbing peter'), qSo = q('so when somebody') - 0.4, qWhere = q('where is the money'), qSub = q('subscribe') - 0.35, qAn = q('animal facts'), qBat = q('historys greatest'), qCol = q('worlds craziest')
    if (t < qBut + 0.3) {
      paper(c, t); const gy = 840; ground(c, gy)
      bank(c, 960, gy, 620, 520, { cols: 6, sign: 'BANCO ZAROSSI', signPx: 34, fill: C.paper2 })
      ponzi(c, 420, gy, 260, { cane: false, gold: false })
      text(c, 'Montreal, 1907', 400, 190, F.headI(70, 700), C.ink, { alpha: prog(t, S.start + 0.5, S.start + 1.0) })
      typeset(c, 'where he learned it', 1500, 190, F.bodyI(56), C.red, prog(t, S.start + 2.2, S.start + 3.4))
      finish(c, t, false); return false
    }
    if (t < qExp + 0.3) {
      paper(c, t)
      text(c, 'PONZI SCHEME', W / 2, 400, F.head(170, 900), C.ink, { track: 10, alpha: prog(t, qBut + 0.3, qBut + 0.8) }); rule(c, 420, 1500, 450, C.ink, prog(t, qBut + 0.5, qBut + 1.4))
      typeset(c, 'noun. Paying the old investors with the new investors’ money.', W / 2, 560, F.bodyI(54), C.ink2, prog(t, qBut + 1.2, qBut + 3.6))
      text(c, 'in the dictionary for a hundred years', W / 2, 760, F.headI(56, 700), C.red, { alpha: prog(t, qBut + 3.2, qBut + 3.8) })
      finish(c, t, false); return false
    }
    if (t < qSo + 0.3) {
      paper(c, t); const gy = 860; ground(c, gy)
      person(c, 430, gy, 330, { hat: 'bowler', col: C.ink }); person(c, 1500, gy, 330, { hat: 'cap', col: C.ink, face: -1, arm: 0.4 })
      ponzi(c, 960, gy, 300, { arm: 0.5 })
      text(c, 'Peter', 430, gy + 80, F.headI(56, 700), C.ink); text(c, 'Paul', 1500, gy + 80, F.headI(56, 700), C.ink)
      if (t > qRob - 0.3) { flow(c, 500, 600, 900, 600, t, 6, 0.5, 15); flow(c, 1020, 600, 1420, 600, t + 0.3, 6, 0.5, 15) }
      typeset(c, '“My business was simple. It was the old game', W / 2, 190, F.headI(56, 700), C.ink, prog(t, qMy - 0.2, qMy + 2.2))
      typeset(c, 'of robbing Peter to pay Paul.”  — Charles Ponzi', W / 2, 262, F.headI(56, 700), C.ink, prog(t, qRob - 0.5, qRob + 2.0))
      finish(c, t, false); return false
    }
    if (t < qSub + 0.3) {
      paper(c, t)
      c.save(); c.translate(560, 520); c.rotate(-0.04); c.fillStyle = 'rgba(60,40,20,0.22)'; c.fillRect(-352, -392, 720, 800); c.fillStyle = '#f4ead2'; c.fillRect(-360, -400, 720, 800); c.strokeStyle = C.ink; c.lineWidth = 4; c.strokeRect(-360, -400, 720, 800)
      text(c, 'YOUR MONEY', 0, -300, F.sc(50), C.ink, { track: 10 }); rule(c, -280, 280, -270, C.ink, 1); text(c, '50%', 0, -70, F.head(230, 900), C.gold, { stroke: C.ink, sw: 5 }); text(c, 'in 45 days', 0, 20, F.headI(76, 700), C.ink); text(c, 'DOUBLED', 0, 190, F.head(110, 900), C.ink, { track: 6 }); text(c, 'in 90 days', 0, 270, F.headI(64, 700), C.ink); c.restore()
      typeset(c, 'Where is the', 1340, 430, F.head(120, 900), C.ink, prog(t, qWhere - 0.1, qWhere + 0.6))
      typeset(c, 'money', 1340, 570, F.head(150, 900), C.gold, prog(t, qWhere + 0.4, qWhere + 0.8), { stroke: C.ink, sw: 5 })
      typeset(c, 'coming from?', 1340, 700, F.head(120, 900), C.ink, prog(t, qWhere + 0.7, qWhere + 1.4))
      fade(c, prog(t, qSub - 0.1, qSub + 0.3)); finish(c, t, false); return false
    }
    c.fillStyle = '#12100c'; c.fillRect(0, 0, W, H); glow(c, W / 2, 480, 1000, '150,110,50', 0.14)
    const a = qSub + 0.3, z = 1 + 0.03 * prog(t, a, S.out, 'l')
    c.save(); zoom(c, W / 2, H / 2, z)
    c.save(); c.globalAlpha = prog(t, a, a + 0.6); for (let i = 0; i < 3; i++) coin(c, W / 2 - 60 + i * 60, 200 - (i === 1 ? 14 : 0), 26, 1); c.restore()
    rule(c, 520, 1400, 250, C.paper3, prog(t, a, a + 0.8))
    text(c, 'SUBSCRIBE', W / 2, 400, F.head(150, 900), C.paper, { track: 16, alpha: prog(t, a + 0.1, a + 0.6) })
    text(c, 'and we’ll tell you more', W / 2, 470, F.bodyI(50), C.paper2, { alpha: prog(t, a + 0.6, a + 1.2) })
    const items = [['paw', 'Animal facts', qAn], ['swords', 'History’s greatest battles', qBat], ['crash', 'The world’s craziest financial collapses', qCol]]
    items.forEach(([ic, label, at], i) => {
      const p = prog(t, at - 0.1, at + 0.3, 'back'), x = 420 + i * 540; if (p <= 0) return
      c.save(); c.translate(x, 680); c.scale(p, p); c.strokeStyle = C.gold; c.lineWidth = 4; c.beginPath(); c.arc(0, 0, 120, 0, 7); c.stroke()
      c.fillStyle = C.paper; c.strokeStyle = i === 2 ? C.gold2 : C.paper; if (i === 2) c.fillStyle = C.gold2; icon[ic](c); c.restore()
      const ws = label.split(' '), l1 = ws.length > 3 ? ws.slice(0, 3).join(' ') : label, l2 = ws.length > 3 ? ws.slice(3).join(' ') : ''
      text(c, l1, x, 870, F.body(40), C.paper, { alpha: clamp(p) }); if (l2) text(c, l2, x, 918, F.body(40), C.paper, { alpha: clamp(p) })
    })
    c.restore()
    fade(c, 1 - prog(t, a, a + 0.4)); finish(c, t, true); return true
  }

  window.SCENES.push(s8, s9, s10, s11, s12, s13)
})()
