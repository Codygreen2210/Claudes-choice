// scA.js: scenes 1-7 of Ponzi. Each scene is draw(c, t, q, S) -> true if the picture is dark.
// Paper and ink throughout. Money is the one gold; what is owed is the one red.
(function () {
  const { clamp, lerp, EZ, prog, bump, rng, noise, track } = K
  const { W, H, C, F, paper, finish, hatch, rr, text, typeset, rule, person, crowd, glow, tw, bank, block, clock, coin, money } = L
  const { ponzi, cop, liner, car, coupon, stamp, bills, pawn, bars, palm, page } = PZ
  const fade = (c, a, col = '12,10,8') => { if (a > 0) { c.fillStyle = `rgba(${col},${clamp(a)})`; c.fillRect(0, 0, W, H) } }
  const zoom = (c, cx, cy, s) => { c.translate(W / 2, H / 2); c.scale(s, s); c.translate(-cx, -cy) }
  const R = rng(1920), RV = Array.from({ length: 600 }, () => R())
  const ground = (c, gy, x0 = -400, x1 = W + 400) => { c.strokeStyle = C.ink; c.lineWidth = 5; c.beginPath(); c.moveTo(x0, gy); c.lineTo(x1, gy); c.stroke(); hatch(c, k => k.rect(x0, gy + 2, x1 - x0, 400), { gap: 9, alpha: 0.25, angle: 0.03, box: [x0, gy, x1 - x0, 400] }) }
  // a plain wooden chair under a seated figure: same (x, y, h, face) as the person sitting on it
  function chair(c, x, y, h, face = 1, col = C.ink) { const k = h / 100; c.save(); c.translate(x, y); c.scale(k * face, k); c.fillStyle = col; c.fillRect(-17, -37.5, 32, 3.2); c.fillRect(-17, -80, 3.4, 80); c.fillRect(9, -37, 3, 37); c.restore() }
  const QUEUE = crowd(46, 1920, { h: 230, ladies: 0.28 })
  // School Street: a row of fronts, the office at the far right end. Drawn in a world about 4400 wide.
  function street(c, t, o = {}) {
    const gy = 800; const r = rng(27)
    for (let i = 0; i < 16; i++) { const x = -200 + i * 290, w = 250 + r() * 30, h = 420 + r() * 220; block(c, x, gy, w, h, { fill: C.paper3, win: C.paper2, dens: 0.6 }); c.strokeStyle = C.ink; c.lineWidth = 3; c.strokeRect(x, gy - h, w, h); c.fillStyle = C.ink; c.fillRect(x + w * 0.38, gy - 130, w * 0.24, 130); c.fillRect(x, gy - 150, w, 8) }
    bank(c, 4040, gy, 520, 560, { cols: 4, sign: 'SECURITIES EXCHANGE CO.', signPx: 30, track: 1, fill: C.paper2 })
    ground(c, gy, -400, 4800)
  }
  function queue(c, t, o = {}) {
    // the line, facing +x, shuffling. o: x0, x1, cash 0..1, angry 0..1, n
    const gy = 800, n = o.n || 40, x0 = o.x0 ?? 200, x1 = o.x1 ?? 3760
    for (let i = 0; i < n; i++) {
      const p = QUEUE[i % QUEUE.length], x = lerp(x0, x1, i / (n - 1)) + Math.sin(t * 0.8 + i) * 8, sh = Math.max(0, Math.sin(t * 1.3 - i * 0.5))
      const isCop = i % 9 === 4, cash = (o.cash ?? 1) > 0, ang = (o.angry || 0) * (0.5 + 0.5 * Math.sin(t * 6 + i * 2))
      const opt = { col: C.ink, walk: t * 2 + i, stride: 0.25 * sh, face: 1, arm: p.lady ? 0 : 0.3 + ang * 0.7, hold: cash && !p.lady ? (k) => { k.fillStyle = C.gold; k.fillRect(-6, 26, 22, 13) } : null }
      if (isCop) cop(c, x, gy, p.h * 1.08, opt); else person(c, x, gy, p.h, { ...opt, hat: p.hat, lady: p.lady, bulk: p.bulk, belly: p.belly })
      if (cash && p.lady) { c.fillStyle = C.gold; c.fillRect(x + 12, gy - p.h * 0.55, 20, 12) }
    }
  }

  // =============================== 1. School Street ===============================
  function s1(c, t, q, S) {
    const qLine = q('there is a line') - 0.35, qCl = q('clerks'), qEv = q('every one of them') - 0.3, qThey = q('they are waiting'), qSmall = q('a small man'), qHe = q('he is taking in') - 0.4, qNot = q('he has not made'), qAnd = q('and in three weeks') - 0.2, qName = q('his name is going')
    paper(c, t)
    if (t < qLine + 0.35) {
      const a0 = S.start - 0.3
      text(c, 'BOSTON', W / 2, 430, F.head(230, 900), C.ink, { track: 40, alpha: prog(t, a0, a0 + 0.9) }); rule(c, 520, 1400, 480, C.ink, prog(t, a0 + 0.4, a0 + 1.4))
      typeset(c, 'July, 1920', W / 2, 570, F.bodyI(72), C.red, prog(t, a0 + 1.0, a0 + 2.0))
      finish(c, t, false); return false
    }
    if (t < qHe + 0.3) {
      const cx = track(t, [[qLine, 900], [qThey, 2600, 'sine'], [qSmall + 1.0, 3900, 'io']]), z = track(t, [[qLine, 0.92], [qThey, 0.92], [qSmall + 1.0, 1.35, 'io']])
      c.save(); zoom(c, cx, lerp(560, 600, prog(t, qThey, qSmall + 1)), z); street(c, t); queue(c, t, { cash: prog(t, qEv - 0.3, qEv + 0.2) })
      ponzi(c, 3900, 800, 196, { face: -1, arm: 0.4 + 0.1 * Math.sin(t * 2), cane: true })
      c.restore()
      text(c, 'School Street', 300, 150, F.headI(70, 700), C.ink, { alpha: prog(t, qLine + 0.4, qLine + 0.9) * (1 - prog(t, qThey, qThey + 0.5)), stroke: C.paper, sw: 8 })
      finish(c, t, false); return false
    }
    // the money
    const gy = 860; ground(c, gy)
    ponzi(c, 420, gy, 360, { arm: 0.45 })
    const n = Math.floor(22 * prog(t, qHe + 0.3, qNot, 'o')); for (let i = 0; i < n; i++) bills(c, 760 + (i % 8) * 130, gy - 4, 3 + ((i * 7) % 6) + Math.floor(i / 8) * 4, 1.2)
    text(c, '$250,000 a day', 1180, 230, F.head(130, 900), C.ink, { alpha: prog(t, qHe + 0.6, qHe + 1.1) })
    typeset(c, 'investments made: none', 1180, 320, F.bodyI(64), C.red, prog(t, qNot - 0.1, qNot + 1.2))
    const tp = prog(t, qName - 0.2, qName + 0.5)
    if (tp > 0) { fade(c, tp * 0.94); rule(c, 420, 1500, 330, C.paper3, prog(t, qName - 0.2, qName + 0.7)); text(c, 'PONZI', W / 2, 580, F.head(300, 900), C.paper, { track: 30, alpha: prog(t, qName - 0.1, qName + 0.5) }); text(c, 'Boston, 1920', W / 2, 690, F.bodyI(64), C.red2, { alpha: prog(t, qName + 0.5, qName + 1.1) }); rule(c, 420, 1500, 750, C.paper3, prog(t, qName + 0.3, qName + 1.2)) }
    fade(c, 1 - prog(t, qHe + 0.3, qHe + 0.6), '238,226,200'); finish(c, t, false); return tp > 0.5
  }

  // =============================== 2. $2.50 ===============================
  function s2(c, t, q, S) {
    const qCame = q('he came to america') - 0.3, qGam = q('and he gambled'), qWalk = q('he walked off') - 0.4, q250 = q('250'), qMil = q('and a million'), qWash = q('he washed dishes') - 0.4, qWait = q('he waited tables'), qFired = q('he got fired')
    paper(c, t)
    if (t < qWalk + 0.3) {
      // the crossing
      const hy = 660; c.strokeStyle = C.ink; c.lineWidth = 4; c.beginPath(); c.moveTo(0, hy); c.lineTo(W, hy); c.stroke(); hatch(c, k => k.rect(0, hy + 2, W, 500), { gap: 13, alpha: 0.3, angle: 0, box: [0, hy, W, 500], wob: 3 })
      const lx = track(t, [[S.vis, 2300], [qWalk, 700, 'l']]); liner(c, lx, hy + 30, 1.5, { face: -1, t })
      text(c, 'Italy, 1882', 360, 200, F.headI(84, 700), C.ink, { alpha: prog(t, S.start, S.start + 0.5) * (1 - prog(t, qCame - 0.3, qCame)) })
      text(c, 'to America, 1903', 440, 200, F.headI(84, 700), C.ink, { alpha: prog(t, qCame, qCame + 0.5) })
      if (t > qGam - 0.2) for (let i = 0; i < 14; i++) { const p = (t - qGam - i * 0.16) / 1.6; if (p < 0 || p > 1) continue; coin(c, lx - 120 + i * 20 - p * 60, hy - 120 + p * p * 260 - Math.sin(p * 3.14) * 120, 15, 1 - p * 0.3) }
      if (t > qGam) for (let i = 0; i < 5; i++) { const p = clamp((t - qGam - i * 0.2) / 1.4); c.save(); c.translate(lx - 40 + i * 50 + p * 60 * (i - 2), hy - 220 - Math.sin(p * 3.14) * 150 + p * 60); c.rotate(p * 5 + i); c.globalAlpha = 1 - p * p; c.fillStyle = '#f4ead2'; c.strokeStyle = C.ink; c.lineWidth = 3; c.fillRect(-20, -28, 40, 56); c.strokeRect(-20, -28, 40, 56); c.fillStyle = i % 2 ? C.red : C.ink; c.beginPath(); c.arc(0, 0, 8, 0, 7); c.fill(); c.restore() }
      finish(c, t, false); return false
    }
    if (t < qWash + 0.3) {
      const gy = 820; ground(c, gy)
      c.fillStyle = C.ink; c.fillRect(-20, gy - 60, 700, 62); for (let i = 0; i < 5; i++) c.fillRect(60 + i * 140, gy - 60, 22, 200)
      const px = track(t, [[qWalk, 200], [q250, 1040, 'o']]); ponzi(c, px, gy, 330, { walk: px * 0.03, stride: t < q250 - 0.1 ? 0.9 : 0, cane: false, gold: false })
      for (let i = 0; i < 3; i++) { const a = prog(t, q250 - 0.1 + i * 0.18, q250 + 0.2 + i * 0.18, 'back'); if (a > 0) coin(c, 1330 + i * 110, 420, (i === 2 ? 26 : 40) * a, 1) }
      text(c, '$2.50', 1440, 620, F.head(190, 900), C.ink, { alpha: prog(t, q250, q250 + 0.4) })
      typeset(c, '“...and a million dollars in hopes.”', 1300, 250, F.headI(64, 700), C.gold, prog(t, qMil, qMil + 1.6), { stroke: C.paper, sw: 6 })
      text(c, 'Boston, 1903', 300, 200, F.headI(70, 700), C.ink, { alpha: prog(t, qWalk + 0.4, qWalk + 0.9) })
      finish(c, t, false); return false
    }
    const gy = 820; ground(c, gy)
    // the dishes, then the tables
    const tb = prog(t, qWait - 0.3, qWait + 0.4, 'io')
    c.save(); c.translate(-tb * 1100, 0)
    c.fillStyle = C.ink; c.fillRect(300, gy - 190, 560, 190); for (let i = 0; i < 9; i++) { c.fillStyle = C.paper2; c.strokeStyle = C.ink; c.lineWidth = 3; c.beginPath(); c.ellipse(700, gy - 200 - i * 13, 76, 9, 0, 0, 7); c.fill(); c.stroke() }
    ponzi(c, 460, gy - 0, 320, { cane: false, gold: false, arm: 0.35 + 0.15 * Math.sin(t * 6), lean: 0.1 })
    c.restore()
    c.save(); c.translate((1 - tb) * 1500, 0)
    c.fillStyle = C.ink; c.fillRect(1180, gy - 150, 340, 14); c.fillRect(1340, gy - 150, 14, 150); c.fillRect(1280, gy - 8, 140, 8)
    chair(c, 1620, gy, 300, -1)
    person(c, 1620, gy, 300, { hat: 'bowler', seated: true, face: -1, bulk: 1.3, belly: 5 })
    ponzi(c, 1020, gy, 320, { cane: false, gold: false, arm: 0.5, hold: k => { k.fillStyle = C.ink; k.beginPath(); k.save(); k.translate(0, 33); k.rotate(1.25); k.ellipse(4, -3, 24, 2.6, 0, 0, 7); k.fill(); k.restore() } })
    const sc = prog(t, qFired - 0.4, qFired + 0.1); if (sc > 0) coin(c, lerp(1180, 1040, sc), gy - 180 - Math.sin(sc * 3.14) * 60, 18, 1)
    c.restore()
    if (t > qFired) { c.save(); c.translate(960, 300); c.rotate(-0.12); const a = prog(t, qFired + 0.1, qFired + 0.3, 'back'); c.scale(a, a); c.strokeStyle = C.red; c.lineWidth = 10; c.strokeRect(-250, -80, 500, 160); text(c, 'FIRED', 0, 50, F.head(150, 900), C.red, { track: 16 }); c.restore() }
    finish(c, t, false); return false
  }

  // =============================== 3. Montreal ===============================
  function flow(c, x0, y0, x1, y1, t, n = 8, speed = 0.6, r = 13) { for (let i = 0; i < n; i++) { const p = ((t * speed + i / n) % 1); coin(c, lerp(x0, x1, p), lerp(y0, y1, p) - Math.sin(p * Math.PI) * 90, r, 1) } }
  function s3(c, t, q, S) {
    const qFam = q('the bank was famous') - 0.4, qDbl = q('double what'), qWork = q('ponzi worked out') - 0.4, qPay = q('it was paying'), qCol = q('the bank collapsed') - 0.4, qRan = q('the owner ran'), qBroke = q('ponzi broke again') - 0.4, qForg = q('forged a check'), q3 = q('and did three years'), q2 = q('then two more') - 0.3, qSeen = q('but he had seen') - 0.4, qIn = q('from the inside')
    if (t < qWork + 0.3) {
      paper(c, t); const gy = 840; ground(c, gy)
      bank(c, 960, gy, 760, 600, { cols: 6, sign: 'BANCO ZAROSSI', signPx: 40, fill: C.paper2 })
      text(c, 'Montreal, 1907', 330, 170, F.headI(76, 700), C.ink, { alpha: prog(t, S.start, S.start + 0.5) })
      const a = prog(t, qFam + 0.8, qFam + 1.2, 'back'); if (a > 0) { c.save(); c.translate(1560, 330); c.scale(a, a); c.fillStyle = C.gold; c.strokeStyle = C.ink; c.lineWidth = 6; c.beginPath(); c.arc(0, 0, 130, 0, 7); c.fill(); c.stroke(); text(c, '6%', 0, 44, F.head(130, 900), C.ink); c.restore() }
      typeset(c, 'everyone else: 3%', 1560, 540, F.bodyI(50), C.ink2, prog(t, qDbl - 0.1, qDbl + 1.0))
      const cr = crowd(8, 5, { h: 220, ladies: 0.2 }); cr.forEach((p, i) => person(c, 360 + i * 36 - 300 + ((t * 30 + i * 40) % 300), gy, p.h, { hat: p.hat, lady: p.lady, col: C.ink, walk: t * 5 + i, stride: 0.8 }))
      finish(c, t, false); return false
    }
    if (t < qCol + 0.3) {
      // how the six percent was paid
      paper(c, t)
      text(c, 'old depositors', 420, 300, F.headI(64, 700), C.ink); text(c, 'new depositors', 1500, 300, F.headI(64, 700), C.ink)
      for (let i = 0; i < 8; i++) pawn(c, 250 + (i % 4) * 110, 470 + Math.floor(i / 4) * 130, 2.2, t > qPay + 0.8 ? 1 : 0)
      for (let i = 0; i < 12; i++) pawn(c, 1280 + (i % 4) * 110, 470 + Math.floor(i / 4) * 130, 2.2, 0)
      if (t > qPay - 0.2) { flow(c, 1260, 520, 700, 520, t - qPay, 9, 0.5, 16); c.strokeStyle = C.ink; c.lineWidth = 6; c.setLineDash([14, 12]); c.beginPath(); c.moveTo(1240, 610); c.lineTo(720, 610); c.stroke(); c.setLineDash([]); c.beginPath(); c.moveTo(720, 610); c.lineTo(752, 592); c.lineTo(752, 628); c.closePath(); c.fillStyle = C.ink; c.fill() }
      typeset(c, '“interest”', 980, 700, F.headI(70, 700), C.red, prog(t, qPay + 0.6, qPay + 1.4))
      text(c, 'no profits anywhere in the picture', W / 2, 900, F.bodyI(52), C.ink2, { alpha: prog(t, qPay + 2.0, qPay + 2.6) })
      finish(c, t, false); return false
    }
    if (t < qBroke + 0.3) {
      paper(c, t); const gy = 840; ground(c, gy)
      const fall = prog(t, qCol + 0.4, qCol + 1.6, 'i')
      c.save(); c.translate(960, gy); c.rotate(fall * 0.09); c.translate(-960, -gy + fall * 40); bank(c, 960, gy, 760, 600, { cols: 6, sign: 'BANCO ZAROSSI', signPx: 40, fill: C.paper2, signCol: C.red }); c.restore()
      c.strokeStyle = C.ink; c.lineWidth = 5; c.beginPath(); c.moveTo(900, gy - 590); c.lineTo(940, gy - 420); c.lineTo(900, gy - 300); c.lineTo(960, gy - 160); c.lineTo(930, gy); c.stroke()
      const rx = track(t, [[qRan - 0.2, 1000], [qRan + 3.0, 2300, 'i']]); if (t > qRan - 0.2) { person(c, rx, gy, 250, { hat: 'top', bulk: 1.4, belly: 5, walk: rx * 0.05, stride: 1, col: C.ink, arm: 0.3, hold: k => { k.fillStyle = C.gold; k.beginPath(); k.ellipse(8, 40, 20, 24, 0, 0, 7); k.fill(); k.fillStyle = C.ink; k.fillRect(2, 14, 12, 6) } }); text(c, 'to Mexico →', 1560, 300, F.headI(64, 700), C.ink, { alpha: prog(t, qRan + 0.6, qRan + 1.1) }) }
      finish(c, t, false); return false
    }
    if (t < qSeen + 0.3) {
      paper(c, t, C.paper2)
      // the check, then the bars
      c.save(); c.translate(960, 480); c.rotate(-0.03); c.fillStyle = 'rgba(60,40,20,0.22)'; c.fillRect(-560, -210, 1140, 440); c.fillStyle = '#f4ead2'; c.fillRect(-570, -220, 1140, 440); c.strokeStyle = C.ink; c.lineWidth = 3; c.strokeRect(-570, -220, 1140, 440); c.lineWidth = 1.2; c.strokeRect(-556, -206, 1112, 412)
      text(c, 'CANADIAN WAREHOUSING CO.', -520, -140, F.sc(40), C.ink, { align: 'left', track: 6 }); text(c, 'Montreal, 1908', 520, -140, F.bodyI(36), C.ink2, { align: 'right' })
      text(c, 'Pay to the order of', -520, -40, F.bodyI(40), C.ink2, { align: 'left' }); typeset(c, 'Charles Ponzi', -180, -40, F.headI(56, 700), C.ink, prog(t, qBroke + 0.8, qForg), { align: 'left' })
      text(c, '$423.58', 520, -30, F.head(70, 900), C.ink, { align: 'right', alpha: prog(t, qForg - 0.6, qForg - 0.2) })
      c.strokeStyle = C.ink; c.lineWidth = 2; c.beginPath(); c.moveTo(60, 130); c.lineTo(520, 130); c.stroke()
      const sp = prog(t, qForg - 0.1, qForg + 1.3); c.strokeStyle = C.red; c.lineWidth = 5; c.lineCap = 'round'; c.beginPath(); for (let k = 0; k <= Math.floor(60 * sp); k++) { const u = k / 60, x = 80 + u * 420, y = 110 - Math.sin(u * 22) * 22 * (1 - u * 0.5) - (u < 0.1 ? 30 : 0); k ? c.lineTo(x, y) : c.moveTo(x, y) } c.stroke()
      text(c, 'a forged signature', 290, 180, F.bodyI(30), C.red, { alpha: prog(t, qForg + 1.0, qForg + 1.5) })
      c.restore()
      const b1 = prog(t, q3 - 0.5, q3 - 0.1, 'i'); if (b1 > 0) { bars(c, 60, W - 60, 0, H, b1, C.ink, 150, 30); text(c, t > q2 + 0.4 ? 'Atlanta · 2 more years' : 'Montreal · 3 years', W / 2, 905, F.head(84, 900), C.paper, { alpha: prog(t, q3, q3 + 0.4), stroke: C.ink, sw: 14 }) }
      finish(c, t, false); return false
    }
    // what he took away with him
    c.fillStyle = '#17130f'; c.fillRect(0, 0, W, H); glow(c, 960, 520, 800, '201,151,58', 0.2 * prog(t, qSeen + 0.5, qIn))
    ponzi(c, 420, 900, 420, { col: '#050404', cane: false, gold: false, seated: true })
    c.fillStyle = '#050404'; c.fillRect(250, 745, 380, 18); c.fillRect(262, 745, 14, 158); c.fillRect(604, 745, 14, 158)
    const a = prog(t, qSeen + 0.6, qIn + 0.4)
    c.save(); c.globalAlpha = a; for (let i = 0; i < 6; i++) pawn(c, 1000 + (i % 3) * 90, 420 + Math.floor(i / 3) * 110, 1.8, 1); for (let i = 0; i < 9; i++) pawn(c, 1420 + (i % 3) * 90, 360 + Math.floor(i / 3) * 110, 1.8, 0); c.restore()
    if (a > 0.5) flow(c, 1400, 470, 1260, 470, t, 5, 0.5, 12)
    bars(c, 60, W - 60, 0, H, 1, '#050404', 150, 30)
    finish(c, t, true); return true
  }

  // =============================== 4. the coupon ===============================
  function s4(c, t, q, S) {
    const q37 = q('he was 37'), qLet = q('then a letter') - 0.4, qIns = q('inside it was') - 0.2, qYou = q('you could buy') - 0.4, qNot = q('ponzi noticed') - 0.4, qWar = q('the war had wrecked'), qCp = q('a coupon bought'), qBuy = q('buy them there') - 0.2, qCash = q('cash them here'), qOn = q('on paper') - 0.3, qLegal = q('and it was perfectly')
    paper(c, t)
    if (t < qIns + 0.3) {
      const gy = 840; ground(c, gy)
      c.fillStyle = C.ink; c.fillRect(760, gy - 210, 620, 20); c.fillRect(790, gy - 190, 18, 190); c.fillRect(1330, gy - 190, 18, 190)
      chair(c, 1500, gy, 340, -1); ponzi(c, 1500, gy, 340, { face: -1, seated: true, cane: false })
      const ep = prog(t, qLet, qLet + 1.0, 'o'); if (ep > 0) { c.save(); c.translate(lerp(-200, 1000, ep), gy - 240 - Math.sin(ep * 3.14) * 160); c.rotate((1 - ep) * -1.2 + 0.05); c.fillStyle = '#f4ead2'; c.strokeStyle = C.ink; c.lineWidth = 4; c.fillRect(-90, -56, 180, 112); c.strokeRect(-90, -56, 180, 112); c.beginPath(); c.moveTo(-90, -56); c.lineTo(0, 10); c.lineTo(90, -56); c.stroke(); stamp(c, 60, -26, 0.4, 0); c.restore() }
      text(c, 'Boston, 1919', 320, 190, F.headI(76, 700), C.ink, { alpha: prog(t, S.start, S.start + 0.5) })
      typeset(c, '27 School Street', 330, 270, F.bodyI(52), C.ink2, prog(t, S.start + 1.6, S.start + 2.8))
      typeset(c, 'from Spain', 1000, gy - 420, F.headI(60, 700), C.red, prog(t, qLet + 0.9, qLet + 1.6))
      finish(c, t, false); return false
    }
    if (t < qNot + 0.3) {
      const z = 1 + 0.08 * prog(t, qIns, qNot, 'l'), ex = prog(t, qYou + 1.6, qYou + 2.6, 'io')
      coupon(c, lerp(960, 560, ex), 500, 2.6 * z * lerp(1, 0.6, ex), -0.04)
      if (ex > 0) { c.save(); c.globalAlpha = ex; c.strokeStyle = C.ink; c.lineWidth = 8; c.beginPath(); c.moveTo(900, 500); c.lineTo(1120, 500); c.stroke(); c.fillStyle = C.ink; c.beginPath(); c.moveTo(1150, 500); c.lineTo(1114, 478); c.lineTo(1114, 522); c.closePath(); c.fill(); for (let i = 0; i < 3; i++) stamp(c, 1300 + i * 150, 500, 1.7, -0.08 + i * 0.08); c.restore() }
      text(c, 'an international reply coupon', W / 2, 150, F.headI(70, 700), C.ink, { alpha: prog(t, qIns + 0.6, qIns + 1.1) })
      typeset(c, 'bought in one country · traded for stamps in another', W / 2, 900, F.bodyI(52), C.ink2, prog(t, qYou + 0.4, qYou + 3.4))
      finish(c, t, false); return false
    }
    // buy there, cash here
    hatch(c, k => k.rect(700, 200, 520, 640), { gap: 13, alpha: 0.28, angle: 0, box: [700, 200, 520, 640], wob: 3 })
    text(c, 'ITALY', 350, 250, F.sc(64), C.ink, { track: 14 }); text(c, 'BOSTON', 1570, 250, F.sc(64), C.ink, { track: 14 }); text(c, 'the Atlantic', 960, 880, F.bodyI(44), C.ink3)
    const b = prog(t, qCp - 0.3, qCp + 0.5), cx = track(t, [[qBuy + 0.4, 350], [qCash, 1570, 'io']])
    if (b > 0) coin(c, 350, 380, 34 * b, 1)
    text(c, 'costs: one coin', 350, 470, F.bodyI(44), C.ink, { alpha: b })
    coupon(c, cx, 610, 0.95, -0.04 + Math.sin(t * 2) * 0.01)
    const cs = prog(t, qCash + 0.2, qCash + 1.0); for (let i = 0; i < 4; i++) { const a = prog(t, qCash + 0.2 + i * 0.15, qCash + 0.5 + i * 0.15, 'back'); if (a > 0) coin(c, 1440 + i * 86, 380, 34 * a, 1) }
    text(c, 'worth: several', 1570, 470, F.bodyI(44), C.ink, { alpha: cs })
    text(c, '400%', W / 2, 520, F.head(250, 900), C.gold, { alpha: prog(t, qOn + 0.5, qOn + 0.9), stroke: C.paper, sw: 16 })
    if (t > qLegal) { c.save(); c.translate(960, 720); c.rotate(-0.08); const a = prog(t, qLegal + 0.6, qLegal + 0.85, 'back'); c.scale(a, a); c.strokeStyle = C.ink; c.lineWidth = 8; c.strokeRect(-430, -70, 860, 140); text(c, 'PERFECTLY LEGAL', 0, 30, F.head(70, 900), C.ink, { track: 8 }); c.restore() }
    finish(c, t, false); return false
  }

  // =============================== 5. the offer ===============================
  function s5(c, t, q, S) {
    const qCant = q('it could not be done'), qThese = q('these were coupons') - 0.3, qHard = q('and there were hardly'), qCover = q('to cover what') - 0.4, q160 = q('160 million'), qWorld = q('in the whole world') - 0.2, q27 = q('27000'), qDid = q('ponzi did not wait') - 0.4, qJan = q('in january 1920'), qOffer = q('and he made an offer'), q50 = q('50 interest') - 0.2, qDbl = q('or double your money'), qBanks = q('the banks were paying') - 0.2
    paper(c, t)
    if (t < qCover + 0.3) {
      text(c, 'one problem', W / 2, 260, F.head(150, 900), C.ink, { alpha: prog(t, S.start - 0.2, S.start + 0.3) * (1 - prog(t, qThese - 0.3, qThese)) })
      typeset(c, 'it could not be done', W / 2, 380, F.headI(84, 700), C.red, prog(t, qCant - 0.1, qCant + 1.0), { alpha: 1 - prog(t, qThese - 0.3, qThese) })
      if (t > qThese - 0.3) {
        const a = prog(t, qThese - 0.3, qThese + 0.3)
        c.save(); c.globalAlpha = a; coupon(c, 520, 480, 1.5, -0.04); coin(c, 520, 760, 26, 1); coin(c, 590, 764, 26, 1); text(c, 'worth a few cents', 520, 860, F.bodyI(48), C.ink)
        c.strokeStyle = C.ink; c.lineWidth = 8; c.beginPath(); c.moveTo(860, 480); c.lineTo(1080, 480); c.stroke(); c.fillStyle = C.ink; c.beginPath(); c.moveTo(1110, 480); c.lineTo(1074, 458); c.lineTo(1074, 502); c.closePath(); c.fill()
        for (let i = 0; i < 3; i++) stamp(c, 1280 + i * 140, 480, 1.6, -0.08 + i * 0.08); text(c, 'stamps, not cash', 1420, 660, F.headI(60, 700), C.red, { alpha: prog(t, q('not cash') - 0.6, q('not cash')) }); c.restore()
      }
      finish(c, t, false); return false
    }
    if (t < qDid + 0.3) {
      text(c, 'coupons he would need', 560, 200, F.headI(60, 700), C.ink, { alpha: prog(t, qCover + 0.3, qCover + 0.8) })
      const n = prog(t, q160 - 0.6, q160 + 0.5, 'o'); text(c, Math.round(160 * n) + ',000,000', 560, 330, F.head(120, 900), C.red, { alpha: prog(t, q160 - 0.6, q160 - 0.3) })
      c.fillStyle = C.red2; c.fillRect(160, 400, 800 * n, 440)
      text(c, 'coupons that existed', 1440, 200, F.headI(60, 700), C.ink, { alpha: prog(t, qWorld, qWorld + 0.4) })
      text(c, '27,000', 1440, 330, F.head(120, 900), C.ink, { alpha: prog(t, q27 - 0.2, q27 + 0.2) })
      const d = prog(t, q27 - 0.1, q27 + 0.4, 'back'); if (d > 0) { c.fillStyle = C.ink; c.fillRect(1436, 620, 8 * d, 8 * d); c.strokeStyle = C.ink; c.lineWidth = 3; c.beginPath(); c.arc(1440, 624, 60, 0, 7); c.stroke(); text(c, 'to the same scale', 1440, 740, F.bodyI(40), C.ink2, { alpha: clamp(d) }) }
      finish(c, t, false); return false
    }
    // the office, the offer
    const gy = 880; ground(c, gy)
    bank(c, 470, gy, 620, 620, { cols: 4, sign: 'SECURITIES EXCHANGE CO.', signPx: 34, track: 1, fill: C.paper2 })
    ponzi(c, 880, gy, 280, { arm: 0.6 * prog(t, qOffer - 0.2, qOffer + 0.4) })
    text(c, 'January 1920', 470, 190, F.headI(64, 700), C.ink, { alpha: prog(t, qJan, qJan + 0.4) })
    const pa = prog(t, qOffer + 0.3, qOffer + 0.9, 'o')
    if (pa > 0) { c.save(); c.translate(1400, 520 + (1 - pa) * 800); c.rotate(0.02); c.fillStyle = 'rgba(60,40,20,0.22)'; c.fillRect(-352, -392, 720, 800); c.fillStyle = '#f4ead2'; c.fillRect(-360, -400, 720, 800); c.strokeStyle = C.ink; c.lineWidth = 4; c.strokeRect(-360, -400, 720, 800); c.lineWidth = 1.5; c.strokeRect(-344, -384, 688, 768)
      text(c, 'YOUR MONEY', 0, -300, F.sc(50), C.ink, { track: 10 }); rule(c, -280, 280, -270, C.ink, 1)
      text(c, '50%', 0, -70, F.head(230, 900), C.gold, { alpha: prog(t, q50, q50 + 0.3), stroke: C.ink, sw: 5 }); text(c, 'in 45 days', 0, 20, F.headI(76, 700), C.ink, { alpha: prog(t, q50 + 0.5, q50 + 0.9) })
      text(c, 'DOUBLED', 0, 190, F.head(110, 900), C.ink, { track: 6, alpha: prog(t, qDbl, qDbl + 0.3) }); text(c, 'in 90 days', 0, 270, F.headI(64, 700), C.ink, { alpha: prog(t, qDbl + 0.5, qDbl + 0.9) })
      c.restore() }
    typeset(c, 'the banks: 5% a year', 470, 950, F.headI(54, 700), C.red, prog(t, qBanks, qBanks + 1.4), { stroke: C.paper, sw: 8 })
    finish(c, t, false); return false
  }

  // =============================== 6. it works ===============================
  function s6(c, t, q, S) {
    const q45 = q('45 days later') - 0.4, qFull = q('in full'), qPaid = q('he paid them with') - 0.4, qThose = q('and those first') - 0.4, qTold = q('they told everyone'), qMar = q('by march') - 0.4, qMay = q('by may'), qJun = q('by june'), qJul = q('by july') - 0.3, qMany = q('and many of his') - 0.4, qRide = q('they let it ride'), qCops = q('three out of four') - 0.4
    paper(c, t)
    if (t < qMar + 0.3) {
      // the first eighteen, paid with the next ones' money, and the word spreading
      const grid18 = (i) => [260 + (i % 6) * 84, 430 + Math.floor(i / 6) * 110]
      text(c, 'the first 18', 470, 300, F.headI(64, 700), C.ink, { alpha: prog(t, S.start, S.start + 0.4) }); text(c, '$1,800', 470, 830, F.head(90, 900), C.ink, { alpha: prog(t, S.start + 1.8, S.start + 2.2) })
      for (let i = 0; i < 18; i++) { const [x, y] = grid18(i); pawn(c, x, y, 1.9, t > qFull + i * 0.03 ? 1 : 0) }
      ponzi(c, 960, 740, 300, { arm: 0.5 })
      const nx = prog(t, qPaid - 0.2, qPaid + 0.6)
      if (nx > 0) { c.save(); c.globalAlpha = nx; text(c, 'the next ones', 1470, 300, F.headI(64, 700), C.ink); for (let i = 0; i < 30; i++) pawn(c, 1200 + (i % 6) * 84 + 60, 430 + Math.floor(i / 6) * 96, 1.7, 0); c.restore(); flow(c, 1230, 620, 1010, 560, t, 7, 0.5, 13) }
      if (t > q45) flow(c, 910, 560, 720, 560, t + 0.3, 7, 0.5, 13)
      const sp = prog(t, qTold - 0.4, qMar, 'o')
      if (sp > 0) { c.save(); c.globalAlpha = 0.8; c.strokeStyle = C.gold; c.lineWidth = 3; for (let i = 0; i < 18; i++) { const [x, y] = grid18(i); for (let k = 0; k < 3; k++) { const a = -2.2 + k * 0.5 + RV[i * 3 + k] * 0.4, l = (120 + RV[i + k * 7] * 180) * sp; c.beginPath(); c.moveTo(x, y - 40); c.lineTo(x + Math.cos(a) * l, y - 40 + Math.sin(a) * l); c.stroke(); if (sp > 0.6) pawn(c, x + Math.cos(a) * l, y - 40 + Math.sin(a) * l, 0.9, 0) } } c.restore() }
      finish(c, t, false); return false
    }
    if (t < qJul + 0.3) {
      // the months
      const base = 860, M = [['March', 25000, qMar + 0.4], ['May', 420000, qMay], ['June', 2500000, qJun]]
      c.strokeStyle = C.ink; c.lineWidth = 4; c.beginPath(); c.moveTo(260, base); c.lineTo(1660, base); c.stroke()
      M.forEach(([m, v, at], i) => { const a = prog(t, at - 0.1, at + 0.8, 'o'), h = Math.max(6, v / 2500000 * 600) * a, x = 420 + i * 420; c.fillStyle = C.gold; c.fillRect(x - 110, base - h, 220, h); c.strokeStyle = C.ink; c.lineWidth = 4; c.strokeRect(x - 110, base - h, 220, h); text(c, m, x, base + 70, F.headI(56, 700), C.ink, { alpha: clamp(a * 3) }); text(c, money(v * a), x, base - h - 26, F.head(64, 900), C.ink, { alpha: clamp(a * 3) }) })
      text(c, 'money taken in, 1920', 560, 170, F.headI(60, 700), C.ink, { alpha: prog(t, qMar + 0.3, qMar + 0.8) })
      finish(c, t, false); return false
    }
    if (t < qCops + 0.3) {
      const gy = 880; ground(c, gy)
      const n = Math.floor(lerp(8, 44, prog(t, qJul, qMany + 2, 'l'))); for (let i = 0; i < n; i++) bills(c, 300 + (i % 11) * 122, gy - 4, 3 + ((i * 7) % 5) + Math.floor(i / 11) * 5, 1.25)
      for (let i = 0; i < 4; i++) person(c, 240 + i * 440 + Math.sin(t * 1.5 + i * 2) * 80, gy, 250, { hat: 'none', col: C.ink, walk: t * 8 + i, stride: 1, face: Math.cos(t * 1.5 + i * 2) > 0 ? 1 : -1, arm: 0.45, hold: k => { k.fillStyle = C.gold; k.fillRect(-10, 24, 28, 16) } })
      text(c, 'July: $250,000 a day', W / 2, 180, F.head(84, 900), C.ink, { alpha: prog(t, qJul + 0.4, qJul + 0.9) * (1 - prog(t, qMany, qMany + 0.4)), stroke: C.paper, sw: 10 })
      typeset(c, '“let it ride”', W / 2, 180, F.headI(110, 700), C.red, prog(t, qRide - 0.5, qRide + 0.5), { stroke: C.paper, sw: 10 })
      finish(c, t, false); return false
    }
    const gy = 860; ground(c, gy)
    for (let i = 0; i < 4; i++) { const a = prog(t, qCops + 0.3 + i * 0.2, qCops + 0.6 + i * 0.2, 'o'); if (a > 0) cop(c, 500 + i * 300, gy + (1 - a) * 400, 420, { badge: i < 3 ? C.gold : C.ink3, hold: i < 3 ? k => { k.fillStyle = C.gold; k.fillRect(-8, 26, 24, 14) } : null, arm: i < 3 ? 0.35 : 0 }) }
    text(c, '3 out of 4 Boston policemen', W / 2, 190, F.headI(76, 700), C.ink, { alpha: prog(t, qCops + 0.6, qCops + 1.1) })
    finish(c, t, false); return false
  }

  // =============================== 7. the good life ===============================
  function s7(c, t, q, S) {
    const qCar = q('he bought a custom') - 0.4, qBank = q('and he bought control') - 0.4, qSame = q('the same bank'), qLib = q('when a financial writer') - 0.4, qWon = q('and won'), qWalk = q('when he walked') - 0.4
    paper(c, t)
    if (t < qBank + 0.3) {
      const gy = 840; ground(c, gy)
      B.house(c, 620, gy, 1.5, C.ink, C.paper2); for (const x of [120, 1130]) { c.fillStyle = C.ink; c.fillRect(x - 8, gy - 150, 16, 150); c.beginPath(); c.ellipse(x, gy - 230, 90, 120, 0, 0, 7); c.fill() }
      const cx = track(t, [[qCar, 2500], [qCar + 2.2, 1500, 'o']]); if (t > qCar) car(c, cx, gy, 1.7, { face: -1, driver: true, roll: cx * 0.02 })
      text(c, 'Lexington, Massachusetts', 620, 170, F.headI(64, 700), C.ink, { alpha: prog(t, S.start + 0.5, S.start + 1.0) })
      finish(c, t, false); return false
    }
    if (t < qLib + 0.3) {
      const gy = 860; ground(c, gy)
      bank(c, 960, gy, 800, 640, { cols: 6, sign: 'HANOVER TRUST CO.', signPx: 44, fill: C.paper2 })
      ponzi(c, 960, gy - 640, 150, { arm: 0.9 * prog(t, qBank + 0.8, qBank + 1.3) })
      ;['the bank that', 'turned him down', 'in 1919'].forEach((ln, i) => text(c, ln, 285, 430 + i * 78, F.headI(58, 700), C.red, { alpha: prog(t, qSame - 0.1 + i * 0.5, qSame + 0.3 + i * 0.5) }))
      finish(c, t, false); return false
    }
    if (t < qWalk + 0.3) {
      paper(c, t, C.paper2)
      page(c, 620, 540, 0.95, -0.03, { name: 'THE EVENING NEWS', head: ['“IMPOSSIBLE,”', 'SAYS WRITER'], hpx: 76 })
      const a = prog(t, qWon - 0.1, qWon + 0.2, 'back'); if (a > 0) { c.save(); c.translate(620, 560); c.rotate(-0.16); c.scale(a, a); c.strokeStyle = C.red; c.lineWidth = 12; c.strokeRect(-400, -90, 800, 180); text(c, 'SUED FOR LIBEL', 0, 34, F.head(76, 900), C.red, { track: 6 }); c.restore() }
      const m = prog(t, qWon + 0.5, qWon + 1.3, 'o'); text(c, money(500000 * m), 1400, 480, F.head(130, 900), C.gold, { alpha: prog(t, qWon + 0.5, qWon + 0.8), stroke: C.ink, sw: 5 }); text(c, 'awarded to Ponzi', 1400, 570, F.headI(60, 700), C.ink, { alpha: prog(t, qWon + 1.2, qWon + 1.7) })
      finish(c, t, false); return false
    }
    // he walks the street; the crowd is in front of us, backs to the camera, arms up
    const gy = 700; ground(c, gy)
    const px = track(t, [[qWalk, 300], [S.out, 1500, 'l']]); ponzi(c, px, gy, 330, { walk: px * 0.03, stride: 0.9, arm: 0.9 })
    const cr = crowd(24, 77, { h: 330, ladies: 0.25 }); cr.forEach((p, i) => { const up = 0.6 + 0.4 * Math.sin(t * 6 + p.ph); person(c, 20 + i * 82, 1150 - up * 16 + (i % 3) * 14, p.h * 1.05, { hat: p.hat, lady: p.lady, bulk: p.bulk * 1.1, col: '#0d0a08', face: i % 2 ? 1 : -1, arm: p.lady ? 0 : 1.0 + 0.1 * Math.sin(t * 7 + p.ph) }) })
    finish(c, t, false); return false
  }

  window.SCENES = [s1, s2, s3, s4, s5, s6, s7]
  window.PZS = { fade, zoom, ground, street, queue, flow, RV, QUEUE }
})()
