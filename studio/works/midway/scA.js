// scA.js: scenes 1-6 of Midway. Each scene is draw(c, t, q, S) -> true if the picture is dark.
// Japanese ships and planes are red, American ones are ink, fire is gold. The Americans come from the right.
(function () {
  const { clamp, lerp, EZ, prog, bump, rng, noise, track } = K
  const { W, H, C, F, paper, finish, hatch, rr, text, typeset, rule, person, glow, tw } = L
  const { INK, RED, sea, puff, clouds, smokeCol, flame, burst, splash, carrier, destroyer, battleship, plane, planeTop, carrierTop, bomb, officer } = MW
  const fade = (c, a, col = '8,10,16') => { if (a > 0) { c.fillStyle = `rgba(${col},${clamp(a)})`; c.fillRect(0, 0, W, H) } }
  const zoom = (c, cx, cy, s) => { c.translate(W / 2, H / 2); c.scale(s, s); c.translate(-cx, -cy) }
  const R = rng(1942), RV = Array.from({ length: 500 }, () => R())
  const DRED = '#8f2c1e'
  // a black flak burst that swells and thins
  const flak = (c, x, y, t0, t, s = 1) => { const p = (t - t0) / 1.6; if (p > 0 && p < 1) puff(c, x, y, (18 + 40 * p) * s, 0.75 * (1 - p), '#15161a', Math.round(x + y), 0.9) }
  // the four carriers in formation, steaming toward +x. o: fire [0..1 x4], planes, t, hy
  function fleet(c, t, o = {}) {
    const hy = o.hy ?? 620, f = o.fire || [0, 0, 0, 0], off = (o.drift ?? 14) * (t - (o.t0 || 0))
    const pos = [[1280, hy + 8, 0.5], [560, hy + 22, 0.62], [1130, hy + 150, 1.05], [330, hy + 250, 1.35]]
    pos.forEach(([x, y, s], i) => {
      const xx = x + off * s * 0.4 + (o.dx ? o.dx[i] || 0 : 0)
      c.save(); c.strokeStyle = 'rgba(238,242,242,0.5)'; c.lineWidth = 3 * s; c.beginPath(); c.moveTo(xx - 250 * s, y + 3 * s); c.lineTo(xx - 520 * s, y + 5 * s); c.stroke(); c.restore()
      carrier(c, xx, y, s, { jp: true, planes: o.planes ?? 13, fire: f[i], t, col: i < 2 ? '#a94a3a' : RED, list: o.list ? o.list[i] || 0 : 0 })
    })
    return pos
  }

  // =============================== 1. twenty past ten ===============================
  function s1(c, t, q, S) {
    const qT = q('it is twenty past') - 0.35, qAr = q('around him are four') - 0.3, qSame = q('the same four'), qFor = q('for three hours') - 0.3, qNot = q('and not one bomb'), qWin = q('he is winning') - 0.2, qIn = q('in about five minutes'), qThree = q('three of those four')
    if (t < qT + 0.35) {
      sea(c, t, { hy: 640 }); clouds(c, t, { y0: 90, y1: 330, n: 9, a: 0.8 })
      const a0 = S.start - 0.3
      text(c, 'JUNE 4, 1942', W / 2, 400, F.head(160, 900), INK, { track: 12, alpha: prog(t, a0, a0 + 1.0) })
      rule(c, 560, 1360, 446, INK, prog(t, a0 + 0.4, a0 + 1.4))
      typeset(c, 'the middle of the Pacific Ocean', W / 2, 526, F.bodyI(60), '#2b3a4a', prog(t, a0 + 2.2, a0 + 3.6))
      fade(c, prog(t, qT - 0.1, qT + 0.35), '217,214,194'); finish(c, t, false); return false
    }
    if (t < qAr + 0.3) {
      // the admiral on his bridge
      sea(c, t, { hy: 700 }); clouds(c, t, { y0: 60, y1: 260, n: 8, a: 0.8 })
      c.save(); zoom(c, 1150 - 40 * prog(t, qT, qAr, 'l'), 560, 1.0 + 0.05 * prog(t, qT, qAr, 'l'))
      carrier(c, 900, 760, 5.2, { jp: true, planes: 11 })
      officer(c, 1178, 398, 168, { col: DRED, hold: k => { k.fillStyle = DRED; k.fillRect(-9, 4, 18, 9) }, arm: 0.72 })
      c.restore()
      text(c, '10:20 a.m.', 360, 240, F.head(110, 900), INK, { alpha: prog(t, qT + 0.2, qT + 0.7) })
      fade(c, 1 - prog(t, qT + 0.35, qT + 0.8), '217,214,194'); finish(c, t, false); return false
    }
    const z = 1.0 + 0.06 * prog(t, qAr, S.out, 'l')
    c.save(); zoom(c, 960, 560, z)
    sea(c, t, { hy: 620 }); clouds(c, t, { y0: 60, y1: 300, n: 9, a: 0.8 })
    fleet(c, t, { planes: 14 })
    // American planes come in; everything misses
    if (t > qFor - 0.5) {
      for (let i = 0; i < 9; i++) { const t0 = qFor + i * 1.05, p = (t - t0) / 3.2; if (p < 0 || p > 1) continue; const hit = i % 3 === 1, x = lerp(2100, hit ? 900 + i * 40 : -200, p), y = 300 + (i % 4) * 46 + (hit && p > 0.55 ? (p - 0.55) ** 2 * 1700 : 0); plane(c, x, y, 0.75, { face: -1, col: INK, rot: hit && p > 0.55 ? -(p - 0.55) * 2 : 0, bomb: !hit }); if (hit && p > 0.55) puff(c, x + 40, y - 20, 26, 0.7, '#15161a', i) }
      for (let i = 0; i < 16; i++) flak(c, 500 + RV[i] * 1200, 240 + RV[i + 20] * 220, qFor + 0.3 + i * 0.62, t)
      for (let i = 0; i < 12; i++) splash(c, 240 + RV[i + 40] * 1400, 660 + RV[i + 60] * 230, 0.5 + RV[i + 80] * 0.7, (t - (qFor + 0.9 + i * 0.75)) / 1.3)
    }
    c.restore()
    const tp = prog(t, qThree - 0.1, qThree + 0.6)
    if (tp > 0) {
      fade(c, tp * 0.72)
      rule(c, 420, 1500, 330, C.paper3, prog(t, qThree - 0.1, qThree + 0.8))
      text(c, 'MIDWAY', W / 2, 560, F.head(260, 900), C.paper, { track: 30, alpha: prog(t, qThree, qThree + 0.6) })
      text(c, 'June 4, 1942', W / 2, 680, F.bodyI(64), C.red2, { alpha: prog(t, qThree + 0.5, qThree + 1.1) })
      rule(c, 420, 1500, 740, C.paper3, prog(t, qThree + 0.3, qThree + 1.2))
    }
    fade(c, 1 - prog(t, qAr + 0.3, qAr + 0.7), '217,214,194'); finish(c, t, false); return tp > 0.5
  }

  // =============================== the chart of the Pacific ===============================
  const PT = { japan: [330, 330], pearl: [1420, 610], midway: [1090, 480], wake: [760, 560], phil: [200, 660], aleut: [1120, 170] }
  function chart(c, t, o = {}) {
    hatch(c, k => k.rect(0, 0, W, H), { gap: 14, alpha: 0.16, angle: 0, box: [0, 0, W, H], wob: 3 })
    // Asia at the left edge, Japan, America at the right edge
    c.fillStyle = C.paper3; c.strokeStyle = C.ink; c.lineWidth = 4
    c.beginPath(); c.moveTo(-20, -20); c.lineTo(250, -20); c.bezierCurveTo(200, 120, 260, 220, 170, 330); c.bezierCurveTo(90, 430, 150, 560, 60, 640); c.lineTo(-20, 700); c.closePath(); c.fill(); c.stroke()
    c.beginPath(); c.moveTo(1940, -20); c.lineTo(1800, -20); c.bezierCurveTo(1760, 160, 1830, 330, 1850, 480); c.bezierCurveTo(1870, 600, 1900, 660, 1940, 720); c.closePath(); c.fill(); c.stroke()
    c.fillStyle = o.jcol || RED; for (const [x, y, w, h, r] of [[352, 250, 22, 62, -0.5], [330, 340, 26, 90, 0.35], [286, 430, 22, 44, 0.9]]) { c.beginPath(); c.ellipse(x, y, w, h, r, 0, 7); c.fill() }
    text(c, 'JAPAN', 420, 300, F.sc(40), C.ink, { align: 'left', track: 8 }); text(c, 'PACIFIC OCEAN', 960, 900, F.sc(50), C.ink3, { track: 30 })
    const tide = clamp(o.tide ?? 0)
    if (tide > 0) { c.save(); c.globalAlpha = 0.5; hatch(c, k => { k.ellipse(380, 560, 560 * tide, 430 * tide, 0.2, 0, 7) }, { gap: 9, alpha: 0.9, angle: 0.7, col: RED, lw: 2.5, box: [-200, 100, 1300, 900] }); c.restore() }
    const dot = (p, col, lab, a = 1, dx = 22, dy = 12, al = 'left') => { if (a <= 0) return; c.save(); c.globalAlpha = clamp(a); c.fillStyle = col; c.strokeStyle = C.ink; c.lineWidth = 4; c.beginPath(); c.arc(p[0], p[1], 13, 0, 7); c.fill(); c.stroke(); c.restore(); if (lab) text(c, lab, p[0] + dx, p[1] + dy, F.headI(44, 700), C.ink, { align: al, alpha: clamp(a), stroke: C.paper, sw: 8 }) }
    dot(PT.pearl, C.ink, 'Pearl Harbor', o.pearl ?? 1, 22, 46)
    dot(PT.midway, C.gold, 'Midway', o.midway ?? 0, -10, 62, 'center')
  }
  function arrow(c, pts, p, col, lw = 12, dash) {
    p = clamp(p); if (p <= 0) return
    let Lt = 0; const seg = []; for (let i = 1; i < pts.length; i++) { const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); seg.push(d); Lt += d }
    let left = Lt * p, ex = pts[0][0], ey = pts[0][1], ang = 0
    c.save(); c.strokeStyle = col; c.fillStyle = col; c.lineWidth = lw; c.lineJoin = 'round'; if (dash) c.setLineDash(dash); c.beginPath(); c.moveTo(pts[0][0], pts[0][1])
    for (let i = 1; i < pts.length && left > 0; i++) { const k = Math.min(1, left / seg[i - 1]); ex = lerp(pts[i - 1][0], pts[i][0], k); ey = lerp(pts[i - 1][1], pts[i][1], k); ang = Math.atan2(pts[i][1] - pts[i - 1][1], pts[i][0] - pts[i - 1][0]); c.lineTo(ex, ey); left -= seg[i - 1] }
    c.stroke(); c.setLineDash([]); c.translate(ex, ey); c.rotate(ang); c.beginPath(); c.moveTo(lw * 2.2, 0); c.lineTo(-lw * 0.6, -lw * 1.7); c.lineTo(-lw * 0.6, lw * 1.7); c.closePath(); c.fill(); c.restore()
  }

  // =============================== 2. the plan ===============================
  function s2(c, t, q, S) {
    const qAdm = q('but the admiral who') - 0.4, qAm = q('the american aircraft carriers') - 0.3, qLong = q('and as long as'), qName = q('his name was yamamoto') - 0.4, qHe = q('he would attack') - 0.3, q13 = q('1300 miles'), qAms = q('the americans would have'), qWhen = q('and when they did')
    if (t < qAdm + 0.3) {
      paper(c, t); chart(c, t, { tide: prog(t, S.vis + 0.5, qAdm, 'o') })
      text(c, 'six months', 1100, 260, F.head(110, 900), C.ink, { alpha: prog(t, S.start, S.start + 0.5) })
      finish(c, t, false); return false
    }
    if (t < qName + 0.3) {
      // Pearl Harbor: the battleships hit, the carriers not there
      sea(c, t, { hy: 640, dusk: 0.3 })
      c.fillStyle = '#3d4a4f'; c.beginPath(); c.moveTo(-20, 646); for (let x = -20; x <= W + 20; x += 60) c.lineTo(x, 600 - 40 * noise(x * 0.004, 2) - 20); c.lineTo(W + 20, 646); c.closePath(); c.fill()
      for (const [x, li, k] of [[380, 0.07, 1], [1080, -0.05, 0.8]]) { battleship(c, x, 700, 1.5 * k + 0.2, { col: INK, list: li, face: k === 1 ? 1 : -1 }); smokeCol(c, x, 600, t + x, 0.9 * k, 0.7, '#17171c', 1); flame(c, x - 30, 640, 1.2, t, 0.7) }
      const ab = prog(t, qAm, qAm + 0.6)
      for (let i = 0; i < 3; i++) { c.save(); c.globalAlpha = ab * (0.7 + 0.2 * Math.sin(t * 3 + i)); c.strokeStyle = C.paper; c.lineWidth = 4; c.setLineDash([14, 10]); c.strokeRect(1200 + i * 30, 760 + i * 70, 560, 54); c.restore() }
      text(c, 'Pearl Harbor · December 7, 1941', W / 2, 150, F.headI(72, 700), INK, { alpha: prog(t, qAdm + 0.3, qAdm + 0.9), stroke: '#d9d6c2', sw: 8 })
      typeset(c, 'the carriers were not in port', 1480, 720, F.bodyI(52), C.paper, prog(t, qAm + 0.2, qAm + 1.5), { shadow: '#000' })
      fade(c, 1 - prog(t, qAdm + 0.3, qAdm + 0.7), '238,226,200'); finish(c, t, false); return false
    }
    paper(c, t)
    const z = lerp(1, 1.5, prog(t, qHe, qHe + 1.4, 'io'))
    c.save(); zoom(c, lerp(960, 1200, prog(t, qHe, qHe + 1.4, 'io')), lerp(540, 520, prog(t, qHe, qHe + 1.4, 'io')), z)
    chart(c, t, { tide: 1, midway: prog(t, qHe + 0.6, qHe + 1.0) })
    c.save(); c.strokeStyle = C.ink; c.lineWidth = 3; c.setLineDash([8, 8]); const lp = prog(t, q13 - 0.5, q13 + 0.3); c.beginPath(); c.moveTo(PT.midway[0] + 16, PT.midway[1] + 8); c.lineTo(lerp(PT.midway[0] + 16, PT.pearl[0] - 16, lp), lerp(PT.midway[1] + 8, PT.pearl[1] - 8, lp)); c.stroke(); c.restore()
    text(c, '1,300 miles', 1300, 590, F.headI(34, 700), C.ink, { alpha: prog(t, q13, q13 + 0.3), stroke: C.paper, sw: 6 })
    arrow(c, [[460, 360], [800, 380], [1050, 462]], prog(t, qHe + 1.0, q13, 'io'), RED, 10)
    arrow(c, [[PT.pearl[0] - 10, PT.pearl[1] - 30], [1330, 500], [1160, 470]], prog(t, qAms, qAms + 1.2, 'io'), C.ink, 9)
    const wa = prog(t, qWhen - 0.2, qWhen + 0.4); for (let i = 0; i < 4; i++) carrierTop(c, 900 + (i % 2) * 90, 330 + Math.floor(i / 2) * 44 + (i % 2) * 14, 0.24 * wa, { jp: true, rot: 0.45, wake: false })
    arrow(c, [[1000, 372], [1100, 420], [1180, 452]], prog(t, qWhen + 0.4, qWhen + 1.2, 'io'), RED, 8)
    c.restore()
    typeset(c, 'Admiral Isoroku Yamamoto', W / 2, 960 - 60, F.headI(60, 700), C.red, prog(t, qName + 0.6, qName + 1.6), { alpha: 1 - prog(t, qHe + 0.6, qHe + 1.0) })
    finish(c, t, false); return false
  }

  // =============================== 3. the basement ===============================
  const GROUPS = Array.from({ length: 84 }, (_, i) => String(10000 + Math.floor(RV[i + 100] * 89999)))
  const WORDS = { 9: 'ATTACK', 17: 'FLEET', 26: 'JUNE', 31: 'CARRIERS', 44: 'AF', 52: 'OCCUPY', 63: 'STRIKE', 70: 'FORCE' }
  function desks(c, t) {
    c.fillStyle = '#12110f'; c.fillRect(0, 0, W, H); c.fillStyle = '#0a0908'; c.fillRect(0, 820, W, 260)
    for (const [x, k] of [[380, 0], [960, 1], [1540, 2]]) {
      glow(c, x, 560, 520, '246,199,112', 0.42 * (0.94 + 0.06 * noise(t * 5, k)))
      c.fillStyle = '#050505'; c.fillRect(x - 3, 0, 6, 380); c.beginPath(); c.moveTo(x - 70, 430); c.lineTo(x - 30, 380); c.lineTo(x + 30, 380); c.lineTo(x + 70, 430); c.closePath(); c.fill(); c.fillStyle = C.gold2; c.beginPath(); c.ellipse(x, 432, 62, 9, 0, 0, 7); c.fill()
      c.fillStyle = '#050505'; c.fillRect(x - 210, 700, 420, 18); c.fillRect(x - 196, 718, 14, 104); c.fillRect(x + 182, 718, 14, 104)
      c.fillStyle = C.paper2; for (let i = 0; i < 4; i++) { c.save(); c.translate(x - 140 + i * 78, 694); c.rotate(-0.1 + i * 0.07); c.fillRect(-30, -4, 60, 7); c.restore() }
      person(c, x - 40 + k * 30, 824, 300, { hat: 'none', col: '#050505', seated: true, face: k === 1 ? -1 : 1, lean: 0.08 })
    }
  }
  function s3(c, t, q, S) {
    const qIn = q('in a basement') - 0.3, qBoss = q('their boss was'), qRead = q('they could read') - 0.4, qKnew = q('and they knew the target'), qAF = q('a f'), qSure = q('rochefort was sure') - 0.3, qWash = q('washington was not'), qTrap = q('so they set a trap') - 0.4, qTold = q('midway was told'), qPlain = q('in plain english'), qWithin = q('within a day') - 0.4, qShort = q('a f is short')
    if (t < qRead + 0.3) {
      c.save(); zoom(c, 960, 540, 1.04 + 0.05 * prog(t, S.vis, qRead, 'l')); desks(c, t); c.restore()
      typeset(c, 'Station Hypo · Pearl Harbor', W / 2, 160, F.headI(70, 700), C.paper, prog(t, qIn + 0.4, qIn + 1.8), { shadow: '#000' })
      typeset(c, 'Commander Joseph Rochefort', W / 2, 236, F.bodyI(52), C.gold2, prog(t, qBoss + 0.5, qBoss + 1.7), { shadow: '#000' })
      finish(c, t, true); return true
    }
    if (t < qTrap + 0.3) {
      // the code: five-digit groups, a few of them giving way
      c.fillStyle = '#12110f'; c.fillRect(0, 0, W, H); glow(c, 960, 520, 1000, '246,199,112', 0.16)
      const af = prog(t, qAF - 0.2, qAF + 0.3), big = prog(t, qAF - 0.2, qAF + 0.5, 'o')
      GROUPS.forEach((g, i) => {
        const x = 160 + (i % 12) * 146, y = 190 + Math.floor(i / 12) * 104, w = WORDS[i], rv = prog(t, qRead + 0.4 + (i % 9) * 0.3, qRead + 0.8 + (i % 9) * 0.3)
        const fl = Math.floor(t * 8 + i) % 10
        if (w && rv > 0 && (w !== 'AF' || t > qKnew)) text(c, w, x, y, F.old(40, true), w === 'AF' ? C.red2 : C.gold2, { alpha: (1 - big * 0.8) })
        else text(c, w && rv <= 0 ? g.slice(0, 4) + fl : g, x, y, F.old(40), C.paper3, { alpha: 0.5 * (1 - big * 0.8) })
      })
      if (af > 0) { text(c, 'AF', 760, 640, F.head(420, 900), C.red2, { alpha: af, track: 20, shadow: '#000', blur: 60 }) }
      const sure = prog(t, qSure, qSure + 0.5)
      text(c, '= Midway', 1380, 560, F.headI(110, 700), C.paper, { alpha: sure, shadow: '#000' })
      text(c, '?', 1700, 600, F.head(260, 900), C.gold2, { alpha: prog(t, qWash - 0.1, qWash + 0.3), shadow: '#000' })
      fade(c, 1 - prog(t, qRead + 0.3, qRead + 0.6)); finish(c, t, true); return true
    }
    if (t < qWithin + 0.3) {
      // Midway sends, in the clear
      sea(c, t, { hy: 700, dusk: 0.25 }); clouds(c, t, { y0: 60, y1: 260, n: 7, a: 0.7 })
      c.fillStyle = '#d9cfae'; c.beginPath(); c.moveTo(300, 706); c.quadraticCurveTo(960, 640, 1620, 706); c.closePath(); c.fill()
      c.fillStyle = INK; c.fillRect(700, 620, 150, 54); c.fillRect(880, 632, 90, 42); c.fillRect(1100, 610, 200, 64); c.beginPath(); c.moveTo(1100, 610); c.quadraticCurveTo(1200, 560, 1300, 610); c.fill()
      c.fillRect(1004, 380, 8, 296); c.strokeStyle = INK; c.lineWidth = 3; c.beginPath(); c.moveTo(1008, 384); c.lineTo(940, 676); c.moveTo(1008, 384); c.lineTo(1076, 676); c.stroke()
      const on = t > qTold + 0.6
      if (on) for (let i = 0; i < 4; i++) { const a = ((t * 0.7 + i / 4) % 1); c.save(); c.globalAlpha = (1 - a) * 0.9; c.strokeStyle = C.gold; c.lineWidth = 5; c.beginPath(); c.arc(1008, 384, 40 + a * 300, -2.3, -0.84); c.stroke(); c.restore() }
      text(c, 'Midway', 520, 800, F.headI(64, 700), C.paper, { shadow: '#000' })
      const msg = 'FRESH WATER PLANT HAS BROKEN DOWN', mp = prog(t, qPlain - 0.6, qWithin - 0.3)
      c.save(); c.globalAlpha = prog(t, qTold + 0.4, qTold + 0.8); c.fillStyle = '#f4ead2'; c.fillRect(310, 150, 1300, 150); c.strokeStyle = C.ink; c.lineWidth = 3; c.strokeRect(310, 150, 1300, 150); c.restore()
      typeset(c, msg, 350, 250, F.old(58, true), C.ink, mp, { align: 'left', track: 3 })
      text(c, 'sent in plain English', 1590, 190, F.bodyI(32), C.ink2, { align: 'right', alpha: prog(t, qPlain, qPlain + 0.4) })
      fade(c, 1 - prog(t, qTrap + 0.3, qTrap + 0.7)); finish(c, t, false); return false
    }
    c.fillStyle = '#12110f'; c.fillRect(0, 0, W, H); glow(c, 960, 520, 1000, '246,199,112', 0.2)
    const dp = prog(t, qShort - 0.2, qShort + 1.6)
    const src = ['48213', '90177', '35562', '71940', '26308'], out = ['AF', 'IS', 'SHORT', 'OF', 'WATER']
    src.forEach((g, i) => { const k = clamp(dp * 5 - i), x = 360 + i * 300; text(c, g, x, 440, F.old(64), C.paper3, { alpha: 0.7 * prog(t, qWithin + 0.4 + i * 0.12, qWithin + 0.7 + i * 0.12) }); if (k > 0) { c.save(); c.globalAlpha = clamp(k); c.strokeStyle = C.gold; c.lineWidth = 3; c.beginPath(); c.moveTo(x, 470); c.lineTo(x, 540); c.stroke(); c.restore(); text(c, out[i], x, 630, F.head(i === 0 ? 120 : 84, 900), i === 0 ? C.red2 : C.gold2, { alpha: clamp(k) }) } })
    text(c, 'Japanese naval message, intercepted', W / 2, 260, F.bodyI(46), C.paper2, { alpha: prog(t, qWithin + 0.3, qWithin + 0.9) })
    text(c, 'AF = MIDWAY', W / 2, 860, F.head(110, 900), C.paper, { track: 10, alpha: prog(t, qShort + 1.8, qShort + 2.3) })
    fade(c, 1 - prog(t, qWithin + 0.3, qWithin + 0.6)); finish(c, t, true); return true
  }

  // =============================== 4. three days ===============================
  function dock(c, t, o = {}) {
    // the Yorktown in dry dock. o: sparks 0..1
    const g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#3a4a60'); g.addColorStop(1, '#7c8796'); c.fillStyle = g; c.fillRect(0, 0, W, H)
    c.fillStyle = '#0c0f15'; c.fillRect(0, 820, W, 260); c.fillRect(0, 560, 150, 300); c.fillRect(W - 150, 560, 150, 300)
    for (let i = 0; i < 5; i++) { c.fillRect(200 + i * 340, 780, 60, 50) }
    carrier(c, 960, 770, 3.0, { us: true, col: '#0a0d13' })
    // staging and a crane
    c.strokeStyle = '#0a0d13'; c.lineWidth = 5; for (let i = 0; i < 9; i++) { const x = 330 + i * 150; c.beginPath(); c.moveTo(x, 820); c.lineTo(x, 640); c.stroke() } c.beginPath(); c.moveTo(330, 700); c.lineTo(1530, 700); c.stroke()
    c.lineWidth = 10; c.beginPath(); c.moveTo(1700, 820); c.lineTo(1700, 240); c.lineTo(1260, 300); c.stroke(); c.lineWidth = 3; c.beginPath(); c.moveTo(1700, 240); c.lineTo(1760, 400); c.moveTo(1300, 296); c.lineTo(1300, 520); c.stroke()
    const sp = o.sparks ?? 1
    for (let i = 0; i < 9; i++) { const x = 380 + RV[i + 200] * 1100, y = 640 + RV[i + 220] * 150, on = noise(t * 9 + i * 7, i) > 0.1 ? 1 : 0; if (!on || sp <= 0) continue; glow(c, x, y, 130, '246,199,112', 0.7 * sp); c.fillStyle = '#fff1c4'; c.beginPath(); c.arc(x, y, 6, 0, 7); c.fill(); c.strokeStyle = C.gold2; c.lineWidth = 2; for (let k = 0; k < 6; k++) { const a = RV[(i * 7 + k + Math.floor(t * 12)) % 500] * 6.28, l = 20 + RV[(i + k * 3 + Math.floor(t * 12)) % 500] * 50; c.beginPath(); c.moveTo(x, y); c.lineTo(x + Math.cos(a) * l, y + Math.abs(Math.sin(a)) * l); c.stroke() } }
    for (let i = 0; i < 12; i++) person(c, 300 + i * 118 + RV[i + 240] * 40, i % 3 === 0 ? 700 : 822, 74, { hat: 'cap', col: '#06080c', face: i % 2 ? 1 : -1, arm: 0.3 + 0.3 * Math.sin(t * 6 + i) })
  }
  function s4(c, t, q, S) {
    const qWhat = q('what he did not have') - 0.3, qTwo = q('he had two carriers') - 0.4, qThird = q('a third the yorktown'), qYard = q('the repair yard') - 0.4, qMo = q('she needed months'), qGave = q('nimitz gave them') - 0.2, q3 = q('three days'), qSail = q('she sailed') - 0.4, qThree = q('three american carriers') - 0.4, qMen = q('the men setting')
    if (t < qTwo + 0.3) {
      sea(c, t, { hy: 700, dusk: 0.2 }); clouds(c, t, { y0: 60, y1: 280, n: 8, a: 0.8 })
      c.fillStyle = '#0c0f15'; c.fillRect(0, 780, W, 300); c.fillRect(0, 760, 1100, 30)
      officer(c, 700, 762, 420, { col: INK }); for (const x of [820, 900]) c.fillRect(x, 700, 12, 64)
      typeset(c, 'Admiral Chester Nimitz', 1300, 300, F.headI(76, 700), INK, prog(t, S.start + 0.8, S.start + 2.0))
      typeset(c, 'he knew where · he knew about when', 1300, 380, F.bodyI(50), '#2b3a4a', prog(t, S.start + 2.4, qWhat))
      finish(c, t, false); return false
    }
    if (t < qYard + 0.3) {
      sea(c, t, { hy: 640, dusk: 0.2 }); clouds(c, t, { y0: 60, y1: 280, n: 8, a: 0.8 })
      carrier(c, 420, 690, 0.9, { us: true, planes: 8 }); carrier(c, 1060, 730, 1.1, { us: true, planes: 8 })
      const ar = prog(t, qThird - 0.4, qThird + 2.6, 'o'), yx = lerp(2500, 1480, ar)
      carrier(c, yx, 870, 1.5, { us: true, list: 0.035, fire: 0 }); smokeCol(c, yx - 60, 780, t, 0.9, 0.6, '#17171c', 1)
      text(c, '2 ready', 740, 560, F.head(70, 900), INK, { alpha: prog(t, qTwo + 0.5, qTwo + 0.9) })
      typeset(c, 'USS Yorktown', 1380, 480, F.headI(76, 700), INK, prog(t, qThird + 0.2, qThird + 1.2))
      fade(c, 1 - prog(t, qTwo + 0.3, qTwo + 0.7), '217,214,194'); finish(c, t, false); return false
    }
    if (t < qThree + 0.3) {
      const sail = prog(t, qSail, qThree, 'i')
      c.save(); zoom(c, 960 + sail * 200, 540, 1 + 0.04 * prog(t, qYard, qSail, 'l')); dock(c, t, { sparks: 1 }); c.restore()
      const mo = prog(t, qMo - 0.2, qMo + 0.3), gv = prog(t, q3 - 0.2, q3 + 0.3)
      text(c, 'months', 520, 250, F.head(150, 900), C.paper2, { alpha: mo * lerp(1, 0.45, gv), shadow: '#000' })
      if (gv > 0) { c.save(); c.strokeStyle = C.red2; c.lineWidth = 12; c.beginPath(); c.moveTo(250, 200); c.lineTo(250 + 540 * gv, 200); c.stroke(); c.restore() }
      text(c, '3 days', 1320, 250, F.head(190, 900), C.gold2, { alpha: gv, shadow: '#000', blur: 30 })
      fade(c, 1 - prog(t, qYard + 0.3, qYard + 0.7) + prog(t, qThree - 0.3, qThree + 0.3)); finish(c, t, true); return true
    }
    // the trap, on the chart
    paper(c, t); hatch(c, k => k.rect(0, 0, W, H), { gap: 14, alpha: 0.16, angle: 0, box: [0, 0, W, H], wob: 3 })
    const M = [960, 640]
    c.fillStyle = C.gold; c.strokeStyle = C.ink; c.lineWidth = 4; c.beginPath(); c.ellipse(M[0], M[1], 46, 30, 0, 0, 7); c.stroke(); c.beginPath(); c.arc(M[0] + 20, M[1] + 16, 12, 0, 7); c.fill(); c.stroke(); c.beginPath(); c.arc(M[0] - 4, M[1] + 22, 8, 0, 7); c.fill(); c.stroke()
    text(c, 'Midway', M[0], M[1] + 96, F.headI(54, 700), C.ink)
    const ap = prog(t, qThree + 0.4, qThree + 2.4, 'o')
    for (let i = 0; i < 3; i++) carrierTop(c, lerp(2100, 1380 + i * 70, ap), lerp(700, 330 + i * 64, ap), 0.5, { col: C.ink, rot: Math.PI + 0.5, deck: 'rgba(238,226,200,0.5)' })
    const jp = prog(t, qMen - 0.4, S.out, 'l')
    for (let i = 0; i < 4; i++) carrierTop(c, lerp(-200, 420, jp) + (i % 2) * 110, lerp(160, 330, jp) + Math.floor(i / 2) * 60 + (i % 2) * 20, 0.5, { jp: true, rot: 0.38, sun: true })
    text(c, 'American carriers', 1500, 260, F.headI(52, 700), C.ink, { alpha: ap })
    text(c, 'the Japanese carriers', 420, 120, F.headI(52, 700), C.red, { alpha: prog(t, qMen - 0.2, qMen + 0.4) })
    finish(c, t, false); return false
  }

  // =============================== the hangar deck, cut open ===============================
  // o: torp 0..1 (torpedoes slung), bomb 0..1 (bombs slung), stack 0..1 (loose ordnance left lying), hose 0..1, crew, hit {x, a}, fire 0..1
  function hangar(c, t, o = {}) {
    c.fillStyle = '#2a3440'; c.fillRect(0, 0, W, H); c.fillStyle = RED; c.fillRect(-20, 250, W + 40, 40); c.fillRect(-20, 250, W + 40, 620); c.fillStyle = '#17110f'; c.fillRect(60, 300, W - 120, 470)
    c.fillStyle = '#0d0908'; c.fillRect(60, 770, W - 120, 16); for (let x = 330; x < W - 100; x += 380) { c.fillStyle = RED; c.fillRect(x, 300, 22, 470) }
    c.fillStyle = '#6e8597'; c.fillRect(-20, 870, W + 40, 300)
    for (let i = 0; i < 11; i++) { c.fillStyle = '#a94a3a'; c.beginPath(); c.ellipse(120 + i * 170, 240, 30, 9, 0, 0, 7); c.fill(); c.fillRect(120 + i * 170 - 30, 222, 7, 22); c.fillRect(120 + i * 170 - 6, 234, 36, 5) }
    const PL2 = [240, 640, 1040, 1440]
    PL2.forEach((x, i) => {
      plane(c, x + 40, 650, 2.3, { col: '#c85440', gear: true })
      const tp = clamp((o.torp ?? 0) * 1.3 - i * 0.08), bp = clamp((o.bomb ?? 0) * 1.3 - i * 0.08)
      c.fillStyle = C.paper2
      if (tp > 0) { const yy = lerp(744, 692, tp); c.beginPath(); c.roundRect(x - 40, yy, 200, 16, 8); c.fill(); c.fillRect(x - 52, yy - 5, 12, 26) }
      if (bp > 0) { const yy = lerp(748, 694, bp); c.beginPath(); c.ellipse(x + 70, yy + 6, 44, 13, 0, 0, 7); c.fill(); c.beginPath(); c.moveTo(x + 30, yy + 6); c.lineTo(x + 8, yy - 8); c.lineTo(x + 8, yy + 20); c.closePath(); c.fill() }
    })
    const st = clamp(o.stack ?? 0)
    for (let i = 0; i < Math.floor(st * 16); i++) { const x = 1700 - (i % 5) * 62 - Math.floor(i / 5) * 20, y = 756 - Math.floor(i / 5) * 26; c.fillStyle = C.paper2; c.beginPath(); c.ellipse(x, y, 30, 11, 0, 0, 7); c.fill() }
    for (let i = 0; i < Math.floor(st * 5); i++) { c.fillStyle = C.paper2; c.beginPath(); c.roundRect(150 + i * 14, 752 - i * 0, 150, 13, 6); c.fill() }
    const hs = clamp(o.hose ?? 0); if (hs > 0) { c.save(); c.strokeStyle = '#d9a86a'; c.lineWidth = 7; c.globalAlpha = hs; c.beginPath(); c.moveTo(80, 764); for (let x = 80; x < 80 + 1700 * hs; x += 30) c.lineTo(x, 764 + Math.sin(x * 0.03) * 5); c.stroke(); c.restore() }
    if (o.crew !== false) for (let i = 0; i < 9; i++) { const x = 150 + i * 200 + Math.sin(t * 1.3 + i * 2) * 60; person(c, x, 772, 110, { hat: 'cap', col: '#5d1d14', walk: t * 7 + i, stride: 0.9, face: Math.cos(t * 1.3 + i * 2) > 0 ? 1 : -1, arm: 0.4 }) }
    const f = clamp(o.fire ?? 0)
    if (f > 0) { for (let i = 0; i < 9; i++) flame(c, 160 + i * 200, 770, 2.6 * f, t + i, f); c.save(); c.globalCompositeOperation = 'lighter'; c.fillStyle = `rgba(246,150,60,${0.35 * f})`; c.fillRect(60, 300, W - 120, 470); c.restore(); for (let i = 0; i < 6; i++) burst(c, 200 + RV[i + 300] * 1500, 420 + RV[i + 320] * 300, 90, bump(t, (o.fireAt || 0) + i * 0.33, 0.5)) }
  }

  // =============================== 5. the first order ===============================
  function midwayIsland(c, t, o = {}) {
    sea(c, t, { hy: 700, dusk: o.dusk ?? 0.5 }); clouds(c, t, { y0: 60, y1: 260, n: 7, a: 0.7, col: '#f1dcc0' })
    c.fillStyle = '#d9cfae'; c.beginPath(); c.moveTo(200, 706); c.quadraticCurveTo(960, 640, 1720, 706); c.closePath(); c.fill()
    c.fillStyle = INK; c.fillRect(560, 620, 170, 56); c.fillRect(800, 634, 90, 42); c.fillRect(1060, 610, 220, 66); c.beginPath(); c.moveTo(1060, 610); c.quadraticCurveTo(1170, 556, 1280, 610); c.fill(); c.fillRect(1400, 600, 20, 78); c.fillRect(1380, 590, 60, 16)
  }
  function s5(c, t, q, S) {
    const qMan = q('the man in command') - 0.3, q108 = q('he sent 108') - 0.4, qHit = q('they hit it hard') - 0.4, qBut = q('but the airfield'), qNeed = q('there is need'), qSec = q('nagumo had a second') - 0.4, qArmed = q('armed with torpedoes'), qFar = q('and as far as he knew'), qSo = q('so he gave the order') - 0.3, qOff = q('take off the torpedoes'), qLoad = q('load bombs'), qBelow = q('below decks')
    if (t < q108 + 0.3) {
      sea(c, t, { hy: 640, dusk: 0.75 }); clouds(c, t, { y0: 60, y1: 300, n: 8, a: 0.6, col: '#f0c8a0' })
      c.save(); zoom(c, 960, 560, 1.08); fleet(c, t, { planes: 14, drift: 22, t0: S.vis })
      for (let i = 0; i < 12; i++) { const t0 = S.start + 1.2 + i * 0.5, p = (t - t0) / 3; if (p <= 0 || p > 1) continue; plane(c, 1420 + p * 900, 800 - 44 - p * p * 420, 0.7 + p * 0.3, { col: RED, long: false, rot: -0.22 * Math.min(1, p * 3) }) }
      c.restore()
      text(c, '4:30 a.m.', 330, 220, F.head(120, 900), INK, { alpha: prog(t, S.start, S.start + 0.5) })
      typeset(c, 'Admiral Chuichi Nagumo', W / 2, 950 - 40, F.headI(64, 700), C.paper, prog(t, qMan + 0.5, qMan + 1.6), { shadow: '#000' })
      finish(c, t, false); return false
    }
    if (t < qHit + 0.3) {
      // 108 planes, seen from above
      const g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#536b7e'); g.addColorStop(1, '#2f4354'); c.fillStyle = g; c.fillRect(0, 0, W, H)
      clouds(c, t, { y0: 0, y1: H, n: 9, a: 0.5, drift: -70, seed: 9 })
      const adv = (t - q108) * 110
      for (let i = 0; i < 108; i++) { const grp = Math.floor(i / 9), k = i % 9, row = Math.floor(k / 2 + 0.5), side = k % 2 ? 1 : -1, gx = (grp % 4) * 470 - 200 + Math.floor(grp / 4) * 150, gy = Math.floor(grp / 4) * 330 + 180; planeTop(c, gx + adv - row * 46 + 300, gy + (k ? side * row * 40 : 0), 0.8, { col: RED, rot: Math.PI / 2, disc: '#f4ead2' }) }
      text(c, '108 planes', W / 2, 560, F.head(190, 900), C.paper, { alpha: prog(t, q108 + 0.5, q108 + 0.9), shadow: '#000', blur: 40 })
      fade(c, 1 - prog(t, q108 + 0.3, q108 + 0.6)); finish(c, t, false); return false
    }
    if (t < qSec + 0.3) {
      midwayIsland(c, t, { dusk: 0.5 })
      for (let i = 0; i < 9; i++) { const t0 = qHit + 0.6 + i * 0.5, x = 520 + RV[i + 340] * 900; burst(c, x, 660, 70, bump(t, t0, 0.5)); if (t > t0) { smokeCol(c, x, 650, t - t0 + i, 0.7, 0.6 * Math.min(1, (t - t0)), '#17171c', 1); flame(c, x, 676, 0.9, t + i, 0.7) } }
      for (let i = 0; i < 8; i++) { const p = ((t - qHit) * 0.22 + i / 8) % 1; plane(c, 2200 - p * 2600, 180 + (i % 3) * 70, 0.6, { col: RED, face: -1, long: false }) }
      const mp = prog(t, qNeed - 0.2, qNeed + 1.4)
      c.save(); c.globalAlpha = prog(t, qNeed - 0.5, qNeed - 0.1); c.fillStyle = '#f4ead2'; c.fillRect(330, 830, 1260, 120); c.strokeStyle = C.ink; c.lineWidth = 3; c.strokeRect(330, 830, 1260, 120); c.restore()
      typeset(c, 'THERE IS NEED FOR A SECOND ATTACK', 370, 912, F.old(54, true), C.red, mp, { align: 'left', track: 3 })
      fade(c, 1 - prog(t, qHit + 0.3, qHit + 0.6)); finish(c, t, false); return false
    }
    const off = prog(t, qOff, qOff + 1.6, 'io'), on = prog(t, qLoad, qLoad + 1.8, 'io')
    c.save(); zoom(c, 960, 540, 1 + 0.03 * prog(t, qSec, S.out, 'l')); hangar(c, t, { torp: 1 - off, bomb: on, stack: off * 0.3 }); c.restore()
    text(c, 'the second wave: armed to sink ships', W / 2, 150, F.headI(60, 700), C.paper, { alpha: prog(t, qArmed - 0.6, qArmed) * (1 - prog(t, qSo - 0.3, qSo)), shadow: '#000' })
    text(c, 'torpedoes off', 620, 150, F.head(84, 900), C.paper, { alpha: prog(t, qOff - 0.1, qOff + 0.3), shadow: '#000' })
    text(c, 'bombs on', 1320, 150, F.head(84, 900), C.gold2, { alpha: prog(t, qLoad - 0.1, qLoad + 0.3), shadow: '#000' })
    fade(c, 1 - prog(t, qSec + 0.3, qSec + 0.6)); finish(c, t, false); return false
  }

  // =============================== 6. the second order ===============================
  function s6(c, t, q, S) {
    const qTen = q('ten ships'), qLit = q('and a little later') - 0.3, qOne = q('one of them looks'), qRev = q('nagumo reversed') - 0.4, qOffB = q('take off the bombs'), qPut = q('put the torpedoes back'), qNo = q('there was no time'), qSt = q('bombs were stacked'), qHose = q('fuel hoses'), qNow = q('and now his first wave') - 0.4, qCould = q('he could launch') - 0.4, qOr = q('or he could land'), qWait = q('he decided to wait')
    if (t < qRev + 0.3) {
      // the scout, above the cloud
      const g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#8fa3b6'); g.addColorStop(1, '#d9d6c2'); c.fillStyle = g; c.fillRect(0, 0, W, H)
      c.fillStyle = '#6e8597'; c.fillRect(0, 760, W, 320)
      for (let i = 0; i < 6; i++) { const x = 1150 + i * 110 + (t - S.vis) * 6; c.fillStyle = INK; if (i === 2) { c.fillRect(x - 40, 748, 80, 8); c.fillRect(x - 4, 734, 16, 14) } else { c.fillRect(x - 18, 750, 36, 6); c.fillRect(x - 3, 742, 8, 8) } }
      clouds(c, t, { y0: 520, y1: 720, n: 10, a: 0.9, drift: -40 })
      plane(c, 520 + 60 * Math.sin(t * 0.5), 330 + 16 * Math.sin(t * 0.9), 2.6, { col: RED, float: true })
      const b = (s, y, at, t1, col) => { c.save(); c.globalAlpha = prog(t, at - 0.4, at - 0.1); c.fillStyle = '#f4ead2'; c.fillRect(980, y - 70, 860, 100); c.strokeStyle = C.ink; c.lineWidth = 3; c.strokeRect(980, y - 70, 860, 100); c.restore(); typeset(c, s, 1010, y, F.old(46, true), col, prog(t, at - 0.1, t1), { align: 'left', track: 2 }) }
      b('TEN SHIPS · TO THE EAST', 220, qTen, qTen + 1.4, C.ink); b('ONE LOOKS LIKE A CARRIER', 340, qOne, qOne + 1.6, C.red)
      finish(c, t, false); return false
    }
    if (t < qNow + 0.3) {
      const off = prog(t, qOffB, qOffB + 1.5, 'io'), on = prog(t, qPut, qPut + 1.8, 'io')
      c.save(); zoom(c, 960, 540, 1 + 0.03 * prog(t, qRev, qNow, 'l')); hangar(c, t, { torp: on, bomb: 1 - off, stack: 0.3 + 0.7 * prog(t, qOffB + 0.5, qSt + 1.2), hose: prog(t, qHose - 0.2, qHose + 1.2) }); c.restore()
      text(c, 'bombs off', 620, 150, F.head(84, 900), C.gold2, { alpha: prog(t, qOffB - 0.1, qOffB + 0.3) * (1 - prog(t, qNo - 0.4, qNo)), shadow: '#000' })
      text(c, 'torpedoes back on', 1320, 150, F.head(84, 900), C.paper, { alpha: prog(t, qPut - 0.1, qPut + 0.3) * (1 - prog(t, qNo - 0.4, qNo)), shadow: '#000' })
      typeset(c, 'nothing put away', W / 2, 150, F.headI(84, 700), C.gold2, prog(t, qNo, qSt + 0.8), { shadow: '#000' })
      fade(c, 1 - prog(t, qRev + 0.3, qRev + 0.6)); finish(c, t, false); return false
    }
    if (t < qCould + 0.3) {
      // the first wave, home and circling
      const g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#536b7e'); g.addColorStop(1, '#2f4354'); c.fillStyle = g; c.fillRect(0, 0, W, H)
      carrierTop(c, 960, 560, 2.4, { jp: true, sun: true })
      for (let i = 0; i < 16; i++) { const a = t * 0.5 + i / 16 * 6.283, rx = 720 + (i % 3) * 60, ry = 380 + (i % 3) * 40; planeTop(c, 960 + Math.cos(a) * rx, 560 + Math.sin(a) * ry, 0.8, { col: '#d4614a', rot: a + Math.PI, disc: '#f4ead2' }) }
      clouds(c, t, { y0: 0, y1: H, n: 6, a: 0.4, drift: -50, seed: 9 })
      typeset(c, 'low on fuel · nowhere to land', W / 2, 150, F.headI(70, 700), C.paper, prog(t, qNow + 1.4, qNow + 3.0), { shadow: '#000' })
      fade(c, 1 - prog(t, qNow + 0.3, qNow + 0.6)); finish(c, t, false); return false
    }
    sea(c, t, { hy: 700 }); clouds(c, t, { y0: 60, y1: 260, n: 8, a: 0.8 })
    c.save(); zoom(c, 1150, 560, 1.04); carrier(c, 900, 760, 5.2, { jp: true, planes: 11 }); officer(c, 1178, 398, 168, { col: DRED }); c.restore()
    const w = prog(t, qWait - 0.2, qWait + 0.4)
    text(c, 'launch now', 420, 220, F.headI(84, 700), INK, { alpha: prog(t, qCould + 0.5, qCould + 0.9) * lerp(1, 0.3, w) })
    text(c, 'or wait · one clean blow', 500, 320, F.headI(84, 700), w > 0.5 ? C.red : INK, { alpha: prog(t, qOr - 0.1, qOr + 0.4) })
    fade(c, 1 - prog(t, qCould + 0.3, qCould + 0.6), '217,214,194'); finish(c, t, false); return false
  }

  window.SCENES = [s1, s2, s3, s4, s5, s6]
  window.MWS = { fade, zoom, fleet, flak, hangar, chart, arrow, midwayIsland, RV, DRED }
})()
