// scB.js: scenes 7-12 of Midway.
(function () {
  const { clamp, lerp, EZ, prog, bump, rng, noise, track } = K
  const { W, H, C, F, paper, finish, hatch, rr, text, typeset, rule, person, glow, tw } = L
  const { INK, RED, sea, puff, clouds, smokeCol, flame, burst, splash, carrier, destroyer, battleship, plane, planeTop, carrierTop, bomb, officer } = MW
  const { fade, zoom, fleet, flak, hangar, chart, arrow, midwayIsland, RV, DRED } = MWS
  const above = (c, t, drift = -60) => { const g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#536b7e'); g.addColorStop(1, '#2f4354'); c.fillStyle = g; c.fillRect(0, 0, W, H); c.save(); c.strokeStyle = 'rgba(235,240,240,0.14)'; c.lineWidth = 2; const r = rng(3); for (let i = 0; i < 120; i++) { const x = ((r() * (W + 200) + t * drift * 0.5) % (W + 200) + W + 200) % (W + 200) - 100, y = r() * H; c.beginPath(); c.moveTo(x, y); c.lineTo(x + 16, y); c.stroke() } c.restore() }
  const tally = (c, x0, y0, n, cols, gone, col, s = 0.62) => { for (let i = 0; i < n; i++) { const x = x0 + (i % cols) * 84 * s * 1.6, y = y0 + Math.floor(i / cols) * 70 * s * 1.6, g = clamp(gone(i)); planeTop(c, x, y, s, { col: g > 0.5 ? C.paper3 : col }); if (g > 0) { c.save(); c.globalAlpha = g; c.strokeStyle = C.red2; c.lineWidth = 5; c.beginPath(); c.moveTo(x - 26 * s * 1.4, y - 22 * s * 1.4); c.lineTo(x + 26 * s * 1.4, y + 22 * s * 1.4); c.stroke(); c.restore() } } }

  // =============================== 7. the torpedo planes ===============================
  function s7(c, t, q, S) {
    const qFirst = q('first from midway'), qMost = q('most of them were'), qThen = q('then came the planes') - 0.3, qTorp = q('the torpedo bombers found') - 0.4, qSlow = q('they were slow'), qDrop = q('to drop a torpedo'), q8 = q('torpedo squadron eight') - 0.4, qAll = q('all fifteen'), qOf = q('of thirty men') - 0.4, qYoung = q('a young pilot'), qTwo = q('two more squadrons') - 0.4, q41 = q('forty one torpedo') - 0.3, q34 = q('thirty four did not'), qNot = q('not one torpedo')
    if (t < qTorp + 0.3) {
      c.save(); zoom(c, 960, 560, 1.03 + 0.04 * prog(t, S.vis, qTorp, 'l'))
      sea(c, t, { hy: 620 }); clouds(c, t, { y0: 60, y1: 300, n: 9, a: 0.8 })
      fleet(c, t, { planes: 14, t0: S.vis, list: [0, 0, 0.02 * Math.sin(t), -0.02 * Math.sin(t * 0.8)] })
      for (let i = 0; i < 14; i++) { const t0 = S.vis + 0.6 + i * 1.15, p = (t - t0) / 3.4; if (p < 0 || p > 1) continue; const hit = i % 3 !== 2, x = lerp(2150, hit ? 1000 - (i % 4) * 90 : -250, p), big = i % 4 === 3, y = 260 + (i % 5) * 44 + (hit && p > 0.5 ? (p - 0.5) ** 2 * 2000 : 0); plane(c, x, y, big ? 1.2 : 0.75, { face: -1, col: INK, rot: hit && p > 0.5 ? -(p - 0.5) * 2.2 : 0, bomb: !hit, torp: big }); if (hit && p > 0.5) { puff(c, x + 50, y - 26, 30, 0.75, '#15161a', i); flame(c, x + 20, y, 0.5, t, 0.8) } if (hit && y > 640) splash(c, x, 700, 0.9, 0.3) }
      for (let i = 0; i < 22; i++) flak(c, 300 + RV[i] * 1400, 220 + RV[i + 20] * 240, S.vis + 0.8 + i * 0.7, t)
      for (let i = 0; i < 14; i++) splash(c, 200 + RV[i + 40] * 1500, 660 + RV[i + 60] * 240, 0.5 + RV[i + 80] * 0.7, (t - (S.vis + 1.6 + i * 1.0)) / 1.3)
      c.restore()
      text(c, 'from Midway', 360, 180, F.headI(70, 700), INK, { alpha: prog(t, qFirst, qFirst + 0.4) * (1 - prog(t, qThen - 0.3, qThen)) })
      text(c, 'from the carriers', 400, 180, F.headI(70, 700), INK, { alpha: prog(t, qThen, qThen + 0.4) })
      finish(c, t, false); return false
    }
    if (t < q8 + 0.3) {
      // the torpedo run: low, straight, into the guns
      sea(c, t, { hy: 500, drift: -5 }); clouds(c, t, { y0: 40, y1: 220, n: 8, a: 0.8 })
      carrier(c, 300, 520, 0.75, { jp: true, planes: 12 }); carrier(c, 760, 508, 0.5, { jp: true, planes: 12, col: '#a94a3a' })
      for (let i = 0; i < 40; i++) { const p = ((t * 1.4 + RV[i + 100] * 3) % 1), y0 = 520 + RV[i + 140] * 60; c.strokeStyle = C.gold2; c.lineWidth = 3; c.globalAlpha = 0.9 * (1 - p); c.beginPath(); const x = 360 + p * 1500, y = y0 + p * (140 + RV[i + 180] * 260); c.moveTo(x, y); c.lineTo(x + 40, y + 14); c.stroke() } c.globalAlpha = 1
      for (let i = 0; i < 5; i++) { const dn = t > qSlow + 1.5 + i * 1.3 ? clamp((t - qSlow - 1.5 - i * 1.3) / 1.2) : 0, x = 760 + i * 250 - (t - qTorp) * 46, y = 690 + (i % 2) * 70 + i * 16 + dn * dn * 160; plane(c, x, y, 1.5 + (i % 2) * 0.3, { face: -1, col: INK, torp: true, rot: -dn * 0.5 }); if (dn > 0) { puff(c, x + 110, y - 40, 50, 0.8 * (1 - dn * 0.4), '#15161a', i); flame(c, x + 60, y, 0.8, t + i, 1 - dn * 0.5) } }
      for (let i = 0; i < 3; i++) { const p = ((t - qSlow) * 0.3 + i / 3) % 1; plane(c, 500 + p * 1500, 120 + p * 520 + i * 40, 1.1, { col: RED, long: false, rot: 0.42 }) }
      typeset(c, 'low, slow, and straight', 1340, 170, F.headI(60, 700), C.paper, prog(t, qDrop + 0.6, qDrop + 2.0), { shadow: '#000' })
      fade(c, 1 - prog(t, qTorp + 0.3, qTorp + 0.6), '217,214,194'); finish(c, t, false); return false
    }
    if (t < qOf + 0.3) {
      paper(c, t)
      text(c, 'Torpedo Squadron Eight', W / 2, 190, F.headI(84, 700), C.ink, { alpha: prog(t, q8 + 0.3, q8 + 0.8) })
      tally(c, 430, 380, 15, 5, i => prog(t, qAll - 0.3 + i * 0.1, qAll - 0.1 + i * 0.1), C.ink, 1.7)
      text(c, '15 planes · 15 shot down', W / 2, 950, F.head(70, 900), C.red, { alpha: prog(t, qAll + 1.2, qAll + 1.7) })
      finish(c, t, false); return false
    }
    if (t < qTwo + 0.3) {
      // one man in the water
      sea(c, t, { hy: 420 }); clouds(c, t, { y0: 30, y1: 180, n: 8, a: 0.8 })
      fleet(c, t, { hy: 420, planes: 12, drift: 6, t0: S.vis })
      c.save(); c.translate(1200, 860); c.scale(1.7, 1.7); c.translate(-1200, -860)
      const bx = 1200 + Math.sin(t * 0.7) * 10, by = 860 + Math.sin(t * 1.3) * 8
      c.fillStyle = '#2f4354'; c.fillRect(0, by + 4, W, H); c.fillStyle = INK; c.beginPath(); c.arc(bx, by - 20, 26, 0, 7); c.fill(); c.fillRect(bx - 34, by - 2, 68, 30)
      c.save(); c.translate(bx - 10, by - 54); c.rotate(-0.12); c.fillStyle = '#1a1f29'; c.beginPath(); c.roundRect(-70, -16, 140, 30, 8); c.fill(); c.restore()
      c.strokeStyle = 'rgba(235,240,240,0.5)'; c.lineWidth = 4; c.beginPath(); c.ellipse(bx, by + 8, 90 + 6 * Math.sin(t * 2), 12, 0, 0, 7); c.stroke(); c.restore()
      typeset(c, 'Ensign George Gay', 520, 760, F.headI(72, 700), C.paper, prog(t, qYoung + 0.3, qYoung + 1.4), { shadow: '#000' })
      typeset(c, 'the only one of thirty to live', 520, 830, F.bodyI(50), C.paper2, prog(t, qYoung + 1.4, qYoung + 2.8), { shadow: '#000' })
      fade(c, 1 - prog(t, qOf + 0.3, qOf + 0.6), '238,226,200'); finish(c, t, false); return false
    }
    paper(c, t)
    text(c, 'torpedo planes from the carriers', W / 2, 170, F.headI(70, 700), C.ink, { alpha: prog(t, qTwo + 0.3, qTwo + 0.8) })
    const lost = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 20, 22, 23, 25, 27, 28, 29, 30, 31, 32, 34, 35, 36, 37, 39]
    tally(c, 180, 330, 41, 14, i => lost.includes(i) ? prog(t, q34 - 0.2 + lost.indexOf(i) * 0.04, q34 + lost.indexOf(i) * 0.04) : 0, C.ink, 0.88)
    text(c, '41 went in', 520, 870, F.head(84, 900), C.ink, { alpha: prog(t, q41, q41 + 0.4) })
    text(c, '34 did not come back', 1340, 870, F.head(84, 900), C.red, { alpha: prog(t, q34, q34 + 0.4) })
    typeset(c, 'not one torpedo hit', W / 2, 970, F.headI(64, 700), C.ink, prog(t, qNot - 0.1, qNot + 1.0))
    finish(c, t, false); return false
  }

  // =============================== 8. McClusky ===============================
  function gauge(c, x, y, r, v, a) { if (a <= 0) return; c.save(); c.globalAlpha = clamp(a); c.fillStyle = 'rgba(8,10,16,0.75)'; c.beginPath(); c.arc(x, y, r * 1.2, 0, 7); c.fill(); c.strokeStyle = C.paper; c.lineWidth = 6; c.beginPath(); c.arc(x, y, r, Math.PI * 0.8, Math.PI * 2.2); c.stroke(); c.strokeStyle = C.red2; c.lineWidth = 10; c.beginPath(); c.arc(x, y, r, Math.PI * 0.8, Math.PI * 1.02); c.stroke(); text(c, 'E', x - r * 0.72, y + r * 0.74, F.old(r * 0.36, true), C.red2); text(c, 'F', x + r * 0.72, y + r * 0.74, F.old(r * 0.36, true), C.paper); text(c, 'FUEL', x, y + r * 0.5, F.sc(r * 0.24), C.paper, { track: 4 }); const an = lerp(Math.PI * 0.8, Math.PI * 2.2, v); c.strokeStyle = C.paper; c.lineWidth = 7; c.lineCap = 'round'; c.beginPath(); c.moveTo(x, y); c.lineTo(x + Math.cos(an) * r * 0.82, y + Math.sin(an) * r * 0.82); c.stroke(); c.fillStyle = C.paper; c.beginPath(); c.arc(x, y, 9, 0, 7); c.fill(); c.restore() }
  function vee(c, x, y, n, s, rot, col = INK) { for (let i = 0; i < n; i++) { const row = Math.ceil(i / 2), side = i % 2 ? 1 : -1, dx = i ? side * row * 62 * s : 0, dy = row * 54 * s, cs = Math.cos(rot), sn = Math.sin(rot); planeTop(c, x + dx * cs - dy * sn, y + dx * sn + dy * cs, s, { col, rot }) } }
  function s8(c, t, q, S) {
    const qPull = q('they had pulled'), qHigh = q('and high above') - 0.4, qDive = q('dive bombers from'), qLead = q('their leader was'), qFlown = q('he had flown') - 0.3, qNoth = q('there was nothing'), qFuel = q('his planes were running') - 0.3, qWent = q('he went on'), qSaw = q('and then he saw') - 0.3, qOne = q('one japanese destroyer'), qSt = q('it had stayed behind'), qFol = q('mcclusky followed')
    if (t < qHigh + 0.3) {
      sea(c, t, { hy: 560 }); clouds(c, t, { y0: 40, y1: 240, n: 8, a: 0.8 })
      const sw = Math.sin(t * 0.9)
      carrier(c, 620 + sw * 40, 700, 1.25, { jp: true, planes: 13, list: 0.05 * sw }); carrier(c, 1400 - sw * 30, 610, 0.7, { jp: true, planes: 13, col: '#a94a3a', list: -0.05 * sw })
      c.strokeStyle = 'rgba(238,242,242,0.6)'; c.lineWidth = 4; c.beginPath(); c.moveTo(300, 704); c.quadraticCurveTo(100, 720 + sw * 30, -80, 700); c.stroke()
      for (let i = 0; i < 7; i++) { const p = ((t * 0.22 + i / 7) % 1); plane(c, -200 + p * 2400, 480 + (i % 3) * 36 + Math.sin(p * 6 + i) * 20, 0.9, { col: RED, long: false }) }
      typeset(c, 'the fighters, pulled down to the water', W / 2, 180, F.headI(64, 700), INK, prog(t, qPull - 0.2, qPull + 2.0))
      finish(c, t, false); return false
    }
    if (t < qSaw + 0.3) {
      above(c, t)
      clouds(c, t, { y0: 0, y1: H, n: 7, a: 0.55, drift: -90, seed: 9 })
      const bob = Math.sin(t * 0.8) * 8
      vee(c, 820, 400 + bob, 13, 1.25, 0)
      text(c, 'Lt. Cmdr. Wade McClusky', W / 2, 150, F.headI(72, 700), C.paper, { alpha: prog(t, qLead, qLead + 0.5) * (1 - prog(t, qFlown + 1.2, qFlown + 1.8)), shadow: '#000' })
      typeset(c, 'nothing but ocean', W / 2, 150, F.headI(84, 700), C.paper, prog(t, qNoth - 0.1, qNoth + 1.0), { shadow: '#000', alpha: 1 - prog(t, qFuel - 0.3, qFuel) })
      gauge(c, 1640, 800, 150, lerp(0.34, 0.16, prog(t, qFuel, qWent + 1)), prog(t, qFuel, qFuel + 0.4))
      fade(c, 1 - prog(t, qHigh + 0.3, qHigh + 0.7)); finish(c, t, false); return false
    }
    // the wake
    above(c, t)
    const dy = (t - qSaw) * 26, turn = prog(t, qFol - 0.2, qFol + 1.2, 'io')
    c.save(); c.translate(0, dy)
    const wx = 700, wy = 760; c.strokeStyle = 'rgba(240,244,244,0.75)'; c.lineCap = 'round'
    for (let k = 0; k < 40; k++) { const u = k / 40; c.lineWidth = 3 + u * 26; c.globalAlpha = 0.75 * (1 - u); c.beginPath(); c.moveTo(wx + u * 250, wy + u * 520); c.lineTo(wx + (u + 0.03) * 250, wy + (u + 0.03) * 520); c.stroke() } c.globalAlpha = 1
    c.save(); c.translate(wx - 6, wy - 16); c.rotate(-Math.PI / 2 - 0.45); c.scale(1.7, 1.7); c.fillStyle = RED; c.beginPath(); c.moveTo(-46, -8); c.lineTo(34, -8); c.lineTo(52, 0); c.lineTo(34, 8); c.lineTo(-46, 8); c.closePath(); c.fill(); c.restore()
    c.restore()
    clouds(c, t, { y0: 0, y1: H, n: 6, a: 0.45, drift: -90, seed: 9 })
    vee(c, lerp(1320, 1040, turn), lerp(420, 520, turn), 15, 1.0, lerp(0, -0.45, turn))
    text(c, 'one destroyer, running north', 560, 200, F.headI(64, 700), C.paper, { alpha: prog(t, qOne, qOne + 0.5), shadow: '#000' })
    fade(c, 1 - prog(t, qSaw + 0.3, qSaw + 0.7)); finish(c, t, false); return false
  }

  // =============================== 9. five minutes ===============================
  function diveLine(c, t, t0, n, from, to, o = {}) {
    // n planes following one another down a slanting line, each letting a bomb go near the bottom
    const hits = []
    for (let i = 0; i < n; i++) { const p = (t - t0 - i * (o.gap || 0.55)) / (o.dur || 2.6); if (p < 0 || p > 1.5) continue; const dir = to[0] < from[0] ? -1 : 1, ang = Math.atan2(to[1] - from[1], Math.abs(to[0] - from[0]))
      if (p < 0.72) { const x = lerp(from[0], to[0], p / 0.72 * 0.8), y = lerp(from[1], to[1], p / 0.72 * 0.8); plane(c, x, y, o.s || 1.1, { col: INK, face: dir, rot: ang * dir, flaps: true, bomb: true }) }
      else { const k = (p - 0.72) / 0.78, x0 = lerp(from[0], to[0], 0.8), y0 = lerp(from[1], to[1], 0.8); plane(c, x0 + dir * k * 900, y0 - k * 160 + k * k * 40, o.s || 1.1, { col: INK, face: dir, rot: -0.2 * dir * Math.min(1, k * 3) })
        const bk = clamp(k / 0.22); if (bk < 1) bomb(c, lerp(x0, to[0], bk), lerp(y0, to[1], bk), 1.2, ang + (dir < 0 ? Math.PI - 2 * ang : 0), INK) }
      hits.push(t0 + i * (o.gap || 0.55) + (o.dur || 2.6) * (0.72 + 0.78 * 0.22)) }
    return hits
  }
  function s9(c, t, q, S) {
    const qNo = q('there were no fighters'), qKaga = q('the carrier kaga') - 0.4, qFour = q('took four bombs'), qAk = q('the flagship akagi') - 0.4, qThru = q('it went through') - 0.2, qHang = q('into a hangar'), qSame = q('and at that same moment') - 0.4, qYork = q('they were from the yorktown'), qPut = q('they put three bombs'), qBy = q('by 1026') - 0.4, qTook = q('it had taken')
    const clockT = (s, a) => text(c, s, 1700, 130, F.head(90, 900), C.paper, { alpha: a, shadow: '#000', blur: 30 })
    if (t < qKaga + 0.3) {
      // rolling over, from above
      above(c, t)
      for (let i = 0; i < 4; i++) carrierTop(c, 520 + (i % 2) * 520 + (i > 1 ? 150 : 0), 620 + Math.floor(i / 2) * 230, 0.62, { jp: true, sun: true, rot: 0.1 })
      clouds(c, t, { y0: 0, y1: H, n: 6, a: 0.5, drift: -60, seed: 9 })
      for (let i = 0; i < 12; i++) { const p = clamp((t - S.start - 0.6 - i * 0.28) / 2.2), s = lerp(1.3, 0.34, p * p); planeTop(c, lerp(1350 - (i % 4) * 90, 760, p), lerp(250 + (i % 3) * 60, 640, p), s, { col: INK, rot: lerp(-2.2, -2.2 - 1.2, p) }) }
      clockT('10:22', prog(t, S.start - 0.2, S.start + 0.3))
      finish(c, t, false); return false
    }
    if (t < qAk + 0.3) {
      // Kaga
      sea(c, t, { hy: 640 }); clouds(c, t, { y0: 40, y1: 240, n: 8, a: 0.8 })
      c.save(); zoom(c, 960 + Math.sin(t * 40) * 6 * (bump(t, qFour - 0.1, 0.5) + bump(t, qFour + 0.6, 0.5)), 560, 1.02)
      const hits = [qKaga + 2.0, qKaga + 2.55, qKaga + 3.1, qKaga + 3.65], f = clamp(hits.filter(h => t > h).length / 3)
      carrier(c, 760, 800, 2.2, { jp: true, planes: 14, fire: f, t, fires: [[-150, 1], [-20, 1.2], [110, 1], [200, 0.8]].slice(0, hits.filter(h => t > h).length) })
      diveLine(c, t, qKaga + 0.2, 6, [1960, -80], [760, 700], { gap: 0.55, dur: 2.3, s: 1.3 })
      hits.forEach((h, i) => { burst(c, 430 + i * 190, 690, 120, bump(t, h, 0.5)) })
      c.restore()
      clockT('10:22', 1)
      text(c, 'KAGA', 300, 180, F.head(120, 900), C.red, { track: 12, alpha: prog(t, qKaga + 0.3, qKaga + 0.7) })
      fade(c, 1 - prog(t, qKaga + 0.3, qKaga + 0.6), '217,214,194'); finish(c, t, false); return false
    }
    if (t < qSame + 0.3) {
      // Akagi: one bomb, into the hangar
      const fall = prog(t, qAk + 0.6, qThru + 0.2, 'i'), boom = t > qThru + 0.2
      c.save(); zoom(c, 960 + (boom ? Math.sin(t * 40) * 8 * (1 - prog(t, qThru + 0.2, qThru + 1.4)) : 0), 540, 1 + 0.04 * prog(t, qAk, qSame, 'l'))
      hangar(c, t, { torp: 1, bomb: 0, stack: 1, hose: 1, crew: !boom || t < qThru + 0.5, fire: prog(t, qThru + 0.2, qHang + 1.4), fireAt: qThru + 0.2 })
      if (!boom) bomb(c, 980, lerp(-100, 300, fall), 2.6, Math.PI / 2, INK)
      burst(c, 980, 420, 240, bump(t, qThru + 0.2, 0.6))
      c.restore()
      text(c, 'AKAGI', 300, 150, F.head(110, 900), C.paper, { track: 12, alpha: prog(t, qAk + 0.3, qAk + 0.7), shadow: '#000' })
      text(c, 'one bomb', 1560, 150, F.headI(84, 700), C.gold2, { alpha: prog(t, qAk + 1.0, qAk + 1.4), shadow: '#000' })
      fade(c, 1 - prog(t, qAk + 0.3, qAk + 0.6), '217,214,194'); finish(c, t, false); return false
    }
    if (t < qBy + 0.3) {
      // Soryu, from the other side
      sea(c, t, { hy: 640 }); clouds(c, t, { y0: 40, y1: 240, n: 8, a: 0.8 })
      const hits = [qPut + 0.2, qPut + 0.75, qPut + 1.3], nh = hits.filter(h => t > h).length
      c.save(); zoom(c, 960 + Math.sin(t * 40) * 6 * bump(t, qPut + 0.2, 1.4), 560, 1.02)
      carrier(c, 1160, 800, 2.2, { jp: true, face: -1, planes: 14, fire: clamp(nh / 2), t, fires: [[-150, 1], [0, 1.2], [140, 1]].slice(0, nh), wind: 1 })
      diveLine(c, t, qPut - 1.9, 5, [-60, -80], [1160, 700], { gap: 0.55, dur: 2.3, s: 1.3 })
      hits.forEach((h, i) => burst(c, 900 + i * 220, 690, 120, bump(t, h, 0.5)))
      c.restore()
      clockT('10:25', 1)
      text(c, 'SORYU', 1560, 300, F.head(120, 900), C.red, { track: 12, alpha: prog(t, qPut - 0.2, qPut + 0.2) })
      typeset(c, 'a second group, from the Yorktown', 520, 180, F.headI(60, 700), INK, prog(t, qSame + 0.5, qYork + 1.2))
      fade(c, 1 - prog(t, qSame + 0.3, qSame + 0.6), '217,214,194'); finish(c, t, false); return false
    }
    c.save(); zoom(c, 960, 560, 1.0 + 0.05 * prog(t, qBy, S.out, 'l'))
    sea(c, t, { hy: 620, dusk: 0.15 }); clouds(c, t, { y0: 60, y1: 240, n: 6, a: 0.6 })
    fleet(c, t, { planes: 8, fire: [0, 1, 1, 1], drift: 3, t0: S.vis })
    c.restore()
    clockT('10:26', 1)
    text(c, 'five minutes', W / 2, 900, F.head(window.__vertical ? 76 : 150, 900), C.paper, { alpha: prog(t, qTook + 0.6, qTook + 1.1), shadow: '#000', blur: 50 })
    fade(c, 1 - prog(t, qBy + 0.3, qBy + 0.6), '217,214,194'); finish(c, t, false); return false
  }

  // =============================== 10. the last carrier ===============================
  function s10(c, t, q, S) {
    const qStr = q('she struck back') - 0.3, qHitY = q('and hit the yorktown'), qCrew = q('the crew patched') - 0.4, qTh = q('they thought they were'), qAgain = q('they hit her again') - 0.4, qStop = q('this time she stopped'), qAft = q('but that afternoon') - 0.4, q5 = q('at five oclock') - 0.3, q4 = q('four hits'), qYam = q('yamamoto was hundreds') - 0.4, qTurn = q('he turned the fleet')
    if (t < qHitY - 0.6) {
      sea(c, t, { hy: 640 }); clouds(c, t, { y0: 40, y1: 260, n: 8, a: 0.8 })
      carrier(c, 900, 800, 2.0, { jp: true, planes: 12 })
      for (let i = 0; i < 12; i++) { const t0 = qStr + 0.2 + i * 0.4, p = (t - t0) / 3; if (p <= 0 || p > 1) continue; plane(c, 1420 + p * 900, 700 - p * p * 420, 0.9 + p * 0.3, { col: RED, long: false, rot: -0.22 * Math.min(1, p * 3) }) }
      text(c, 'HIRYU', 380, 220, F.head(130, 900), C.red, { track: 12, alpha: prog(t, S.start + 1.0, S.start + 1.5) })
      typeset(c, 'the last one', 380, 300, F.bodyI(60), INK, prog(t, S.start + 1.6, S.start + 2.6))
      finish(c, t, false); return false
    }
    if (t < qAft + 0.3) {
      // the Yorktown: hit, patched, hit again
      sea(c, t, { hy: 640 }); clouds(c, t, { y0: 40, y1: 260, n: 8, a: 0.8 })
      const h1 = [qHitY + 0.3, qHitY + 0.8, qHitY + 1.3], smoke1 = clamp((t - qHitY - 0.3) / 0.6) * (1 - prog(t, qCrew + 1.0, qTh)), h2 = [qAgain + 1.3, qAgain + 1.9], st = prog(t, qAgain + 1.3, qStop + 0.8)
      const yx = 900 + (t - qHitY) * 10 * (1 - st)
      for (let i = 0; i < 5; i++) { const p = (t - (qHitY - 0.9) - i * 0.3) / 2.4; if (p > 0 && p < 1) plane(c, lerp(-200, 2200, p), 200 + i * 40 + Math.sin(p * 3.14) * 240, 1.0, { col: RED, long: false, gear: true, rot: Math.cos(p * 3.14) * 0.5 }) }
      for (let i = 0; i < 4; i++) { const p = (t - qAgain - i * 0.25) / 2.2; if (p > 0 && p < 1) plane(c, lerp(-200, 2300, p), 720 + i * 20, 1.1, { col: RED, long: false, torp: p < 0.45 }) }
      carrier(c, yx, 800, 2.0, { us: true, planes: 9, fire: 0, list: -0.1 * st })
      if (smoke1 > 0) { smokeCol(c, yx + 80, 640, t, 1.4, smoke1, '#17171c', -1); flame(c, yx + 60, 690, 1.6, t, smoke1) }
      if (st > 0) smokeCol(c, yx - 100, 660, t, 1.2, st * 0.8, '#17171c', -1)
      h1.forEach((h, i) => burst(c, yx - 150 + i * 160, 690, 110, bump(t, h, 0.5)))
      h2.forEach((h, i) => { splash(c, yx - 240 + i * 260, 806, 1.6, (t - h) / 1.4); burst(c, yx - 240 + i * 260, 790, 80, bump(t, h, 0.4)) })
      text(c, 'USS YORKTOWN', 430, 200, F.head(80, 900), INK, { track: 8, alpha: prog(t, qHitY - 0.3, qHitY + 0.2) })
      typeset(c, 'patched, and under way again', 480, 280, F.bodyI(54), INK, prog(t, qCrew + 0.8, qTh), { alpha: 1 - prog(t, qAgain, qAgain + 0.5) })
      fade(c, 1 - prog(t, qHitY - 0.6, qHitY - 0.2), '217,214,194'); finish(c, t, false); return false
    }
    if (t < qYam + 0.3) {
      sea(c, t, { hy: 640, dusk: 0.55 }); clouds(c, t, { y0: 40, y1: 260, n: 8, a: 0.6, col: '#f0c8a0' })
      const hits = [q5 + 2.3, q5 + 2.8, q5 + 3.3, q5 + 3.8], nh = hits.filter(h => t > h).length
      c.save(); zoom(c, 960 + Math.sin(t * 40) * 6 * bump(t, q5 + 2.3, 2), 560, 1.02)
      carrier(c, 760, 800, 2.2, { jp: true, planes: 6, fire: clamp(nh / 3), t, fires: [[-150, 1], [-20, 1.2], [110, 1], [200, 0.8]].slice(0, nh) })
      diveLine(c, t, q5 + 0.5, 6, [1960, -80], [760, 700], { gap: 0.5, dur: 2.3, s: 1.3 })
      hits.forEach((h, i) => burst(c, 430 + i * 190, 690, 120, bump(t, h, 0.5)))
      c.restore()
      text(c, '5:00 p.m.', 1620, 130, F.head(90, 900), C.paper, { alpha: prog(t, q5, q5 + 0.4), shadow: '#000', blur: 30 })
      text(c, 'HIRYU', 300, 180, F.head(120, 900), C.red, { track: 12, alpha: prog(t, qAft + 0.6, qAft + 1.0) })
      fade(c, 1 - prog(t, qAft + 0.3, qAft + 0.6), '217,214,194'); finish(c, t, false); return false
    }
    // Yamamoto turns for home
    sea(c, t, { hy: 640, dusk: 0.8, night: 0.35 }); clouds(c, t, { y0: 40, y1: 260, n: 6, a: 0.4, col: '#c9a890' })
    const tp = prog(t, qTurn - 0.2, qTurn + 1.0, 'io'), bx = lerp(1300, 700, prog(t, qTurn + 0.6, S.out, 'i')) + (1 - tp) * (t - qYam) * 12
    for (const [dx, dy, sc] of [[-520, -60, 1.0], [480, -80, 0.85], [0, 0, 2.0]]) { c.save(); c.translate(bx + dx, 760 + dy); c.scale(Math.max(0.12, Math.abs(1 - 2 * tp)), 1); battleship(c, 0, 0, sc, { col: '#7d2a1d', face: tp > 0.5 ? -1 : 1 }); c.restore() }
    typeset(c, 'Yamamoto turned for home', W / 2, 220, F.headI(72, 700), C.paper, prog(t, qTurn, qTurn + 1.6), { shadow: '#000' })
    fade(c, 1 - prog(t, qYam + 0.3, qYam + 0.7)); finish(c, t, true); return true
  }

  // =============================== 11. the count ===============================
  function s11(c, t, q, S) {
    const qCr = q('a heavy cruiser'), q250 = q('about 250 planes'), q3k = q('more than 3000'), qUS = q('the united states lost') - 0.3, qDe = q('one destroyer'), q150 = q('about 150 planes'), q307 = q('307 men'), qJap = q('in japan the newspapers') - 0.4, qW = q('the wounded were')
    if (t < qJap + 0.3) {
      paper(c, t)
      text(c, 'JAPAN', 500, 150, F.sc(60), C.red, { track: 16, alpha: prog(t, S.start - 0.2, S.start + 0.3) }); rule(c, 140, 860, 176, C.red, prog(t, S.start, S.start + 0.8))
      for (let i = 0; i < 4; i++) { const a = prog(t, S.start + 0.6 + i * 0.25, S.start + 0.9 + i * 0.25, 'back'); if (a > 0) carrier(c, 320 + (i % 2) * 380, 300 + Math.floor(i / 2) * 110, 0.6 * a, { jp: true }) }
      if (t > qCr - 0.2) destroyer(c, 500, 530, 1.1 * prog(t, qCr - 0.2, qCr + 0.2, 'back'), { col: RED })
      text(c, '248 planes', 500, 660, F.head(80, 900), C.red, { alpha: prog(t, q250 - 0.1, q250 + 0.3) })
      text(c, '3,057 men', 500, 780, F.head(96, 900), C.red, { alpha: prog(t, q3k - 0.1, q3k + 0.3) })
      c.fillStyle = C.red2; c.fillRect(140, 820, 720 * prog(t, q3k, q3k + 1.0, 'o'), 34)
      text(c, 'UNITED STATES', 1420, 150, F.sc(60), C.ink, { track: 16, alpha: prog(t, qUS, qUS + 0.4) }); rule(c, 1060, 1780, 176, C.ink, prog(t, qUS, qUS + 0.8))
      if (t > qUS + 0.5) carrier(c, 1420, 300, 0.6 * prog(t, qUS + 0.5, qUS + 0.9, 'back'), { us: true })
      if (t > qDe - 0.2) destroyer(c, 1420, 530, 0.7 * prog(t, qDe - 0.2, qDe + 0.2, 'back'), { col: C.ink })
      text(c, 'about 150 planes', 1420, 660, F.head(80, 900), C.ink, { alpha: prog(t, q150 - 0.1, q150 + 0.3) })
      text(c, '307 men', 1420, 780, F.head(96, 900), C.ink, { alpha: prog(t, q307 - 0.1, q307 + 0.3) })
      c.fillStyle = C.ink; c.fillRect(1060, 820, 72 * prog(t, q307, q307 + 0.6, 'o'), 34)
      finish(c, t, false); return false
    }
    paper(c, t, C.paper2)
    const a = prog(t, qJap + 0.3, qJap + 1.0, 'o')
    c.save(); c.translate(960, 450 + (1 - a) * 900); c.rotate(-0.03); c.scale(0.9, 0.9); c.fillStyle = 'rgba(60,40,20,0.25)'; c.fillRect(-412, -392, 840, 820); c.fillStyle = '#f4ead2'; c.fillRect(-420, -400, 840, 820); c.strokeStyle = C.ink; c.lineWidth = 3; c.strokeRect(-420, -400, 840, 820)
    text(c, 'TOKYO · JUNE 1942', 0, -330, F.sc(44), C.ink, { track: 10 }); rule(c, -380, 380, -306, C.ink, 1); text(c, 'GREAT', 0, -170, F.head(150, 900), C.red, { track: 8 }); text(c, 'VICTORY', 0, -30, F.head(150, 900), C.red, { track: 8 }); text(c, 'what the public was told', 0, 50, F.bodyI(46), C.ink2)
    c.strokeStyle = C.ink3; c.lineWidth = 2.5; for (let col = 0; col < 3; col++) for (let i = 0; i < 9; i++) { c.beginPath(); c.moveTo(-370 + col * 255, 120 + i * 30); c.lineTo(-370 + col * 255 + 225 - ((i * 7 + col * 3) % 5 === 0 ? 80 : 0), 120 + i * 30); c.stroke() }
    c.restore()
    typeset(c, 'the survivors were kept out of sight', W / 2, 920, F.headI(56, 700), C.ink, prog(t, qW + 0.6, qW + 2.2))
    finish(c, t, false); return false
  }

  // =============================== 12. small things ===============================
  const icon = {
    paw: (c) => { c.beginPath(); c.ellipse(0, 22, 40, 34, 0, 0, 7); c.fill(); for (const [x, y, r] of [[-46, -22, 17], [-17, -48, 18], [17, -48, 18], [46, -22, 17]]) { c.beginPath(); c.ellipse(x, y, r * 0.85, r, x * 0.006, 0, 7); c.fill() } },
    swords: (c) => { for (const s of [-1, 1]) { c.save(); c.rotate(s * 0.78); c.fillRect(-6, -84, 12, 126); c.beginPath(); c.moveTo(-6, -84); c.lineTo(0, -102); c.lineTo(6, -84); c.fill(); c.fillRect(-28, 36, 56, 10); c.fillRect(-5, 46, 10, 30); c.beginPath(); c.arc(0, 82, 9, 0, 7); c.fill(); c.restore() } },
    crash: (c) => { c.lineWidth = 11; c.lineJoin = 'round'; c.lineCap = 'round'; c.beginPath(); c.moveTo(-84, 20); c.lineTo(-44, -30); c.lineTo(-14, -8); c.lineTo(16, -64); c.lineTo(44, 44); c.lineTo(84, 70); c.stroke(); c.beginPath(); c.moveTo(84, 70); c.lineTo(52, 72); c.lineTo(76, 44); c.closePath(); c.fill(); c.stroke() },
  }
  function s12(c, t, q, S) {
    const qBut = q('but after midway'), qAnd = q('and it turned on') - 0.4, qCode = q('a code half'), qShip = q('a ship fixed'), qMen = q('men in old planes') - 0.2, qOne = q('and one pilot') - 0.4, qKept = q('and kept looking'), qNim = q('admiral nimitz said') - 0.4, qSub = q('subscribe') - 0.35, qAn = q('animal facts'), qBat = q('historys greatest'), qCol = q('worlds craziest')
    if (t < qAnd + 0.3) {
      sea(c, t, { hy: 640, dusk: 0.7 }); clouds(c, t, { y0: 40, y1: 260, n: 8, a: 0.6, col: '#f0c8a0' })
      carrier(c, 760 + (t - S.vis) * 14, 800, 1.9, { us: true, planes: 9 })
      for (let i = 0; i < 3; i++) { const p = ((t - S.vis) * 0.1 + i / 3) % 1; plane(c, 2200 - p * 1700, 260 + p * 380, 0.9, { col: INK, face: -1, gear: true, rot: -0.14 }) }
      typeset(c, 'three more years of war', W / 2, 180, F.headI(70, 700), INK, prog(t, S.start, S.start + 1.6))
      typeset(c, 'but Japan never had the upper hand at sea again', W / 2, 260, F.bodyI(52), '#2b3a4a', prog(t, qBut, qBut + 2.6))
      finish(c, t, false); return false
    }
    if (t < qOne + 0.3) {
      paper(c, t)
      const cell = (i, at, draw, label) => { const a = prog(t, at - 0.2, at + 0.3, 'o'); if (a <= 0) return; const x = 380 + i * 580; c.save(); c.globalAlpha = clamp(a); c.fillStyle = C.paper2; c.strokeStyle = C.ink; c.lineWidth = 4; c.beginPath(); c.roundRect(x - 240, 300, 480, 380, 10); c.fill(); c.stroke(); c.save(); c.beginPath(); c.rect(x - 236, 304, 472, 372); c.clip(); draw(x); c.restore(); c.restore(); text(c, label, x, 760, F.headI(50, 700), C.ink, { alpha: clamp(a) }) }
      cell(0, qCode, x => { for (let i = 0; i < 12; i++) text(c, i === 5 ? 'AF' : String(10000 + Math.floor(RV[i + 400] * 89999)), x - 150 + (i % 3) * 150, 390 + Math.floor(i / 3) * 76, F.old(38, i === 5), i === 5 ? C.red : C.ink3) }, 'a code, half broken')
      cell(1, qShip, x => { carrier(c, x, 600, 0.78, { us: true, col: C.ink }); for (let i = 0; i < 4; i++) { if (noise(t * 9 + i * 7, i) > 0) { glow(c, x - 150 + i * 90, 560, 60, '246,199,112', 0.8); c.fillStyle = C.gold; c.beginPath(); c.arc(x - 150 + i * 90, 560, 5, 0, 7); c.fill() } } }, 'a ship, fixed in three days')
      cell(2, qMen, x => { c.fillStyle = '#6e8597'; c.fillRect(x - 240, 580, 480, 110); plane(c, x + 20, 500, 2.2, { col: C.ink, face: -1, torp: true }) }, 'men in old planes')
      text(c, 'it turned on small things', W / 2, 190, F.headI(76, 700), C.ink, { alpha: prog(t, qAnd + 0.3, qAnd + 0.9) })
      finish(c, t, false); return false
    }
    if (t < qSub + 0.3) {
      // the one who kept looking
      const g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#536b7e'); g.addColorStop(1, '#2f4354'); c.fillStyle = g; c.fillRect(0, 0, W, H)
      c.save(); c.strokeStyle = 'rgba(235,240,240,0.14)'; c.lineWidth = 2; const r = rng(3); for (let i = 0; i < 120; i++) { const x = r() * W, y = ((r() * H + t * 40) % H); c.beginPath(); c.moveTo(x, y); c.lineTo(x + 16, y); c.stroke() } c.restore()
      clouds(c, t, { y0: 0, y1: H, n: 8, a: 0.55, drift: -30, seed: 9 })
      planeTop(c, 960, 520 + Math.sin(t * 0.8) * 8, 2.4, { col: INK })
      const np = prog(t, qNim + 0.6, qNim + 4.2)
      typeset(c, '“...decided the fate of our carrier task force', W / 2, 800, F.headI(52, 700), C.paper, clamp(np * 2), { shadow: '#000' })
      typeset(c, 'and our forces at Midway.”  — Admiral Nimitz', W / 2, 870, F.headI(52, 700), C.paper, clamp(np * 2 - 1), { shadow: '#000' })
      fade(c, 1 - prog(t, qOne + 0.3, qOne + 0.7), '238,226,200'); fade(c, prog(t, qSub - 0.1, qSub + 0.3)); finish(c, t, false); return false
    }
    c.fillStyle = '#0a0f18'; c.fillRect(0, 0, W, H); glow(c, W / 2, 480, 1000, '60,90,130', 0.18)
    const a = qSub + 0.3, z = 1 + 0.03 * prog(t, a, S.out, 'l')
    c.save(); zoom(c, W / 2, H / 2, z)
    c.save(); c.globalAlpha = prog(t, a, a + 0.6); plane(c, W / 2, 190, 1.5, { col: C.paper2, bomb: true }); c.restore()
    rule(c, 520, 1400, 250, C.paper3, prog(t, a, a + 0.8))
    text(c, 'SUBSCRIBE', W / 2, 400, F.head(150, 900), C.paper, { track: 16, alpha: prog(t, a + 0.1, a + 0.6) })
    text(c, 'and we’ll tell you more', W / 2, 470, F.bodyI(50), C.paper2, { alpha: prog(t, a + 0.6, a + 1.2) })
    const items = [['paw', 'Animal facts', qAn], ['swords', 'History’s greatest battles', qBat], ['crash', 'The world’s craziest financial collapses', qCol]]
    items.forEach(([ic, label, at], i) => {
      const p = prog(t, at - 0.1, at + 0.3, 'back'), x = 420 + i * 540; if (p <= 0) return
      c.save(); c.translate(x, 680); c.scale(p, p); c.strokeStyle = C.gold; c.lineWidth = 4; c.beginPath(); c.arc(0, 0, 120, 0, 7); c.stroke()
      c.fillStyle = i === 1 ? C.gold2 : C.paper; c.strokeStyle = i === 2 ? C.red2 : C.paper; if (i === 2) c.fillStyle = C.red2; icon[ic](c); c.restore()
      const ws = label.split(' '), l1 = ws.length > 3 ? ws.slice(0, 3).join(' ') : label, l2 = ws.length > 3 ? ws.slice(3).join(' ') : ''
      text(c, l1, x, 870, F.body(40), C.paper, { alpha: clamp(p) }); if (l2) text(c, l2, x, 918, F.body(40), C.paper, { alpha: clamp(p) })
    })
    c.restore()
    fade(c, 1 - prog(t, a, a + 0.4)); finish(c, t, true); return true
  }

  window.SCENES.push(s7, s8, s9, s10, s11, s12)
})()
