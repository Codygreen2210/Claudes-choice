// scA.js: scenes 1-7 of The Serum Run. Each scene is draw(c, t, q, S) -> true if the picture is dark.
// The serum is the one red thing in the film; lamplight and windows are the one gold.
(function () {
  const { clamp, lerp, EZ, prog, bump, rng, noise, track, mix } = K
  const { W, H, C, F, paper, finish, hatch, rr, text, typeset, rule, person, glow, tw, block, coin } = L
  const { INK, SN, dog, parka, kneel, sled, team, spruce, cabin, biplane, snowland, snowfall, alaska, proj, PL, onRoute, route } = SR
  const fade = (c, a, col = '6,8,14') => { if (a > 0) { c.fillStyle = `rgba(${col},${clamp(a)})`; c.fillRect(0, 0, W, H) } }
  const zoom = (c, cx, cy, s) => { c.translate(W / 2, H / 2); c.scale(s, s); c.translate(-cx, -cy) }
  const RED = C.red2

  // ---------- the trail: a team running through snow country. The ground scrolls; the team holds its place. ----------
  // o: hy, speed, n, bliz 0..1, wind, trees, ice, dawn, tx, s, load, jog, moon, stride, driver, before(c, off), after(c, off), stars
  function trail(c, t, o = {}) {
    const hy = o.hy ?? 720, sp = o.speed ?? 260, off = (o.off ?? t * sp), s = o.s || 1.6, gy = hy + 130
    snowland(c, t, { hy, scroll: off, dawn: o.dawn, moon: o.moon, stars: o.stars ?? (1 - (o.bliz || 0)), seed: o.seed, hills: !o.ice })
    if (o.ice) { c.save(); c.strokeStyle = 'rgba(20,30,60,0.5)'; c.lineWidth = 3; const r = rng(51); for (let i = 0; i < 16; i++) { const wx = i * 330 + r() * 200, x = ((wx - off) % 5280 + 5280) % 5280 - 400, y = hy + 20 + r() * 300; c.beginPath(); c.moveTo(x, y); c.lineTo(x + 90 + r() * 120, y + 14 - r() * 28); c.lineTo(x + 200 + r() * 160, y + 6 + r() * 30); c.stroke() } c.restore() }
    if (o.trees !== false && !o.ice) { const r = rng(17 + (o.seed || 0)); for (let i = 0; i < 26; i++) { const wx = i * 170 + r() * 120, x = ((wx - off * 0.45) % 4420 + 4420) % 4420 - 300; spruce(c, x, hy + 6, 0.5 + r() * 0.35, mix('#0c1330', '#59627f', o.dawn || 0), i) } }
    if (o.before) o.before(c, off)
    // the track the runners leave
    c.save(); c.strokeStyle = 'rgba(40,52,90,0.35)'; c.lineWidth = 5; c.beginPath(); c.moveTo(-50, gy + 2); c.lineTo((o.tx ?? 150), gy + 2); c.stroke(); c.restore()
    if (o.team !== false) team(c, o.tx ?? 150, gy, s, { n: o.n ?? 7, run: off * 0.042, stride: o.stride ?? 1, load: o.load === undefined ? RED : o.load, jog: o.jog, driver: o.driver, col: INK })
    if (o.after) o.after(c, off, gy)
    if (o.trees !== false && !o.ice) { const r = rng(91 + (o.seed || 0)); for (let i = 0; i < 7; i++) { const wx = i * 760 + r() * 400, x = ((wx - off * 1.5) % 5320 + 5320) % 5320 - 500; spruce(c, x, H + 60, 2.4 + r() * 0.8, '#03040a', i + 40) } }
    snowfall(c, t, o.bliz ?? 0.12, o.wind ?? -260, 3)
    if ((o.bliz || 0) > 0.5) { B.fog(c, t, (o.bliz - 0.5) * 1.1, { col: '#9aa6c4', y0: 300, y1: 1000, drift: 120, n: 20 }) }
  }

  // ---------- Nome: a row of false fronts on a frozen shore. lit = share of windows lit, red = share of houses with sickness ----------
  const TOWN = (() => { const r = rng(1925), out = []; let x = 130; for (let i = 0; i < 15; i++) { const w = 90 + r() * 70, h = 90 + r() * 70, kind = i === 6 ? 'church' : (r() < 0.45 ? 'front' : 'house'); out.push({ x, w, h, kind, v: r(), v2: r() }); x += w + 14 + r() * 26 } return out })()
  function nome(c, t, o = {}) {
    const gy = o.gy ?? 700, lit = o.lit ?? 0.4, red = o.red ?? 0
    TOWN.forEach((b, i) => {
      c.fillStyle = INK
      if (b.kind === 'church') { c.fillRect(b.x, gy - b.h, b.w, b.h); c.beginPath(); c.moveTo(b.x - 6, gy - b.h); c.lineTo(b.x + b.w / 2, gy - b.h - 50); c.lineTo(b.x + b.w + 6, gy - b.h); c.fill(); c.fillRect(b.x + b.w / 2 - 14, gy - b.h - 96, 28, 70); c.beginPath(); c.moveTo(b.x + b.w / 2 - 18, gy - b.h - 96); c.lineTo(b.x + b.w / 2, gy - b.h - 150); c.lineTo(b.x + b.w / 2 + 18, gy - b.h - 96); c.fill(); c.fillRect(b.x + b.w / 2 - 2, gy - b.h - 172, 4, 26); c.fillRect(b.x + b.w / 2 - 9, gy - b.h - 164, 18, 4) }
      else if (b.kind === 'front') { c.fillRect(b.x, gy - b.h, b.w, b.h); c.fillRect(b.x - 4, gy - b.h - 22, b.w + 8, 24) }
      else { c.fillRect(b.x, gy - b.h * 0.72, b.w, b.h * 0.72); c.beginPath(); c.moveTo(b.x - 8, gy - b.h * 0.72); c.lineTo(b.x + b.w / 2, gy - b.h); c.lineTo(b.x + b.w + 8, gy - b.h * 0.72); c.fill(); c.fillRect(b.x + b.w * 0.7, gy - b.h - 8, 12, 30) }
      // snow on the roofs
      c.fillStyle = '#d5dcec'; if (b.kind === 'front') c.fillRect(b.x - 4, gy - b.h - 27, b.w + 8, 6); else if (b.kind === 'house') { c.beginPath(); c.moveTo(b.x - 8, gy - b.h * 0.72); c.lineTo(b.x + b.w / 2, gy - b.h); c.lineTo(b.x + b.w + 8, gy - b.h * 0.72); c.lineTo(b.x + b.w - 4, gy - b.h * 0.72 - 3); c.lineTo(b.x + b.w / 2, gy - b.h + 9); c.lineTo(b.x + 4, gy - b.h * 0.72 - 3); c.closePath(); c.fill() }
      const on = b.v < lit, sick = b.v2 < red
      if (on || sick) { const wy = gy - Math.min(b.h * 0.5, 62); c.fillStyle = sick ? RED : C.gold2; glow(c, b.x + b.w * 0.3 + 11, wy + 13, 60, sick ? '184,64,46' : '246,199,112', 0.35); c.fillRect(b.x + b.w * 0.3, wy, 22, 26); if (b.w > 120) c.fillRect(b.x + b.w * 0.62, wy, 22, 26) }
      if (o.smoke && b.kind !== 'church' && b.v > 0.3) for (let k = 0; k < 5; k++) { const a = ((t * 0.2 + k / 5 + b.v) % 1); c.fillStyle = `rgba(200,206,222,${0.22 * (1 - a) * o.smoke})`; c.beginPath(); c.arc(b.x + b.w * 0.74 + a * 60, gy - b.h - 20 - a * 110, 8 + a * 26, 0, 7); c.fill() }
    })
  }
  function shore(c, t, o = {}) {
    const hy = o.hy ?? 700
    snowland(c, t, { hy, dawn: o.dawn, moon: o.moon, stars: o.stars, hills: false })
    // the frozen sea: pressure ridges
    c.save(); c.strokeStyle = 'rgba(30,42,80,0.45)'; c.lineWidth = 3; const r = rng(8); for (let i = 0; i < 22; i++) { const x = r() * W, y = hy + 70 + r() * 300; c.beginPath(); c.moveTo(x, y); c.lineTo(x + 60 + r() * 120, y - 8 + r() * 16); c.lineTo(x + 150 + r() * 160, y + r() * 14); c.stroke() } c.restore()
  }

  // =============================== 1. the drift ===============================
  function lostScene(c, t, o = {}) {
    // the tipped sled, the tangled dogs, the man on his knees. o: dig 0..1 (digging), found 0..1, bliz
    const gy = 850
    snowland(c, t, { hy: 740, stars: 0, hills: false })
    c.fillStyle = '#8f9bb8'; c.beginPath(); c.moveTo(900, gy + 30); c.quadraticCurveTo(1250, gy - 90, 1700, gy + 10); c.lineTo(1700, gy + 60); c.lineTo(900, gy + 60); c.closePath(); c.fill()
    c.save(); c.strokeStyle = INK; c.lineWidth = 3; c.beginPath(); c.moveTo(520, gy - 24); c.bezierCurveTo(430, gy - 60, 380, gy + 10, 300, gy - 30); c.bezierCurveTo(240, gy - 50, 200, gy - 10, 150, gy - 34); c.stroke(); c.restore()
    dog(c, 120, gy, 1.5, { face: -1, head: 0.2 }); dog(c, 250, gy + 6, 1.5, { lie: 1 }); dog(c, 380, gy, 1.5, { sit: 1, face: -1 }); dog(c, 30, gy + 10, 1.45, { lie: 1, face: -1 }); dog(c, 480, gy + 4, 1.5, { face: 1, head: 0.5 })
    sled(c, 640, gy, 1.7, { tip: o.tip ?? 1, load: null })
    const fd = o.found || 0
    if (fd > 0) { glow(c, 1236, gy - 20, 240 * fd, '184,64,46', 0.5 * fd); c.fillStyle = RED; c.save(); c.translate(1236, gy - 16); c.rotate(-0.2); c.beginPath(); c.roundRect(-34, -13, 68, 26, 11); c.fill(); c.restore() }
    else if (o.ghost) { c.save(); c.globalAlpha = o.ghost; c.strokeStyle = RED; c.lineWidth = 3; c.setLineDash([8, 7]); c.translate(1236, gy - 16); c.rotate(-0.2); c.beginPath(); c.roundRect(-34, -13, 68, 26, 11); c.stroke(); c.restore() }
    kneel(c, 1130, gy + 4, 2.3, { dig: (o.dig ?? 1) * Math.sin(t * 7) * (1 - fd) })
    if ((o.dig ?? 1) > 0 && fd < 1) for (let i = 0; i < 6; i++) { const a = ((t * 1.6 + i / 6) % 1); c.fillStyle = `rgba(230,236,248,${(1 - a) * 0.9})`; c.beginPath(); c.arc(1240 + a * 90 + i * 6, gy - 30 - Math.sin(a * Math.PI) * 70, 5 - a * 2, 0, 7); c.fill() }
  }
  function s1(c, t, q, S) {
    const qM = q('its the middle') - 0.35, qSl = q('his sled is on'), qG = q('he has pulled'), qSo = q('somewhere in that'), qC = q('it has come'), qIf = q('and if he cant') - 0.2, qCh = q('children are')
    if (t < qM + 0.35) {
      trail(c, t, { team: false, bliz: 0.7, wind: -520, speed: 0, off: 0 })
      const a0 = S.start - 0.3
      text(c, 'FEBRUARY 1, 1925', W / 2, 400, F.head(140, 900), C.paper, { track: 12, alpha: prog(t, a0, a0 + 1.0), shadow: '#000', blur: 40 })
      rule(c, 560, 1360, 446, C.paper3, prog(t, a0 + 0.4, a0 + 1.4))
      typeset(c, 'the coast of Alaska', W / 2, 526, F.bodyI(60), C.paper2, prog(t, a0 + 2.4, a0 + 3.6), { shadow: '#000' })
      fade(c, prog(t, qM - 0.1, qM + 0.35)); finish(c, t, true); return true
    }
    const z = 1.0 + 0.1 * prog(t, qM, S.out, 'l')
    c.save(); zoom(c, lerp(900, 1040, prog(t, qM, S.out, 'sine')), 600, z)
    lostScene(c, t, { ghost: prog(t, qSo, qSo + 0.6) * (0.5 + 0.3 * Math.sin(t * 4)) })
    c.restore()
    snowfall(c, t, 0.85, -620, 3); B.fog(c, t, 0.3, { col: '#9aa6c4', y0: 300, y1: 1000, drift: 140, n: 18 })
    const tp = prog(t, qCh - 0.1, qCh + 0.6)
    if (tp > 0) {
      fade(c, tp * 0.7)
      rule(c, 420, 1500, 350, C.paper3, prog(t, qCh - 0.1, qCh + 0.8))
      text(c, 'THE SERUM RUN', W / 2, 560, F.head(170, 900), C.paper, { track: 12, alpha: prog(t, qCh, qCh + 0.6) })
      text(c, 'Nome, Alaska · 1925', W / 2, 660, F.bodyI(60), RED, { alpha: prog(t, qCh + 0.5, qCh + 1.1) })
      rule(c, 420, 1500, 720, C.paper3, prog(t, qCh + 0.3, qCh + 1.2))
    }
    fade(c, 1 - prog(t, qM + 0.35, qM + 0.9)); finish(c, t, true); return true
  }

  // =============================== 2. Nome ===============================
  function nope(c, x, y, a, label, draw) {
    if (a <= 0) return; c.save(); c.globalAlpha = clamp(a); c.translate(x, y); c.strokeStyle = C.paper; c.fillStyle = C.paper; c.lineWidth = 5; c.lineCap = 'round'; draw(c)
    c.strokeStyle = RED; c.lineWidth = 9; const p = clamp(a * 2 - 1); c.beginPath(); c.moveTo(-70, -60); c.lineTo(-70 + 140 * p, -60 + 120 * p); c.stroke(); c.restore()
    text(c, label, x, y + 120, F.bodyI(44), C.paper, { alpha: clamp(a), shadow: '#000' })
  }
  function s2(c, t, q, S) {
    const qOld = q('an old gold rush'), qEv = q('every winter') - 0.3, qRoad = q('no road'), qRail = q('no railroad'), qShip = q('no ships'), qWin = q('and in the winter') - 0.4, qName = q('his name was'), qNur = q('he had four nurses')
    if (t < qWin + 0.3) {
      const z = 1.12 - 0.12 * prog(t, S.vis, qEv, 'o')
      c.save(); zoom(c, 960, 560, z + 0.03 * prog(t, qEv, qWin, 'l'))
      shore(c, t, { hy: 700, moon: [1560, 190, 54] }); nome(c, t, { gy: 706, lit: 0.55, smoke: 1 })
      c.restore()
      snowfall(c, t, 0.14, -90, 6)
      text(c, 'NOME', W / 2, 250, F.head(190, 900), C.paper, { track: 40, alpha: prog(t, S.start - 0.2, S.start + 0.6) * (1 - prog(t, qRoad - 0.5, qRoad)), shadow: '#000', blur: 40 })
      typeset(c, 'about 1,400 people, on the Bering Sea', W / 2, 340, F.bodyI(54), C.paper2, prog(t, qOld + 0.3, qOld + 1.8) , { shadow: '#000', alpha: 1 - prog(t, qRoad - 0.5, qRoad) })
      nope(c, 520, 240, prog(t, qRoad - 0.1, qRoad + 0.6), 'no road', k => { k.beginPath(); k.moveTo(-60, 50); k.lineTo(-12, -50); k.moveTo(60, 50); k.lineTo(12, -50); k.stroke(); k.setLineDash([14, 12]); k.beginPath(); k.moveTo(0, 50); k.lineTo(0, -50); k.stroke(); k.setLineDash([]) })
      nope(c, 960, 240, prog(t, qRail - 0.1, qRail + 0.6), 'no railroad', k => { k.beginPath(); k.moveTo(-70, -12); k.lineTo(70, -12); k.moveTo(-70, 16); k.lineTo(70, 16); for (let i = -60; i <= 60; i += 24) { k.moveTo(i, -26); k.lineTo(i, 30) } k.stroke() })
      nope(c, 1400, 240, prog(t, qShip - 0.1, qShip + 0.6), 'no ships, November to July', k => { B.ship(k, 0, 44, 0.42, { col: C.paper }) })
      finish(c, t, true); return true
    }
    // the doctor
    c.save(); zoom(c, 760, 600, 1.5 + 0.08 * prog(t, qWin, S.out, 'l'))
    shore(c, t, { hy: 700, stars: 0.6 }); nome(c, t, { gy: 706, lit: 0.3 })
    c.fillStyle = INK; c.fillRect(560, 520, 330, 190); c.beginPath(); c.moveTo(540, 522); c.lineTo(725, 440); c.lineTo(910, 522); c.fill(); c.fillStyle = '#d5dcec'; c.beginPath(); c.moveTo(540, 522); c.lineTo(725, 440); c.lineTo(910, 522); c.lineTo(890, 518); c.lineTo(725, 454); c.lineTo(560, 518); c.closePath(); c.fill()
    glow(c, 640, 600, 220, '246,199,112', 0.4); c.fillStyle = C.gold2; c.fillRect(600, 566, 70, 70); c.fillRect(780, 566, 70, 70); c.fillStyle = INK; c.fillRect(632, 566, 6, 70); c.fillRect(600, 598, 70, 6); c.fillRect(812, 566, 6, 70); c.fillRect(780, 598, 70, 6)
    c.fillStyle = '#020203'; c.fillRect(700, 600, 50, 110)
    person(c, 760, 800, 230, { hat: 'bowler', col: INK, bulk: 1.1, face: -1, hold: k => { k.fillStyle = INK; k.fillRect(-12, 32, 24, 18); k.fillRect(-5, 27, 10, 6) } })
    const nu = prog(t, qNur - 0.2, qNur + 1.0)
    for (let i = 0; i < 4; i++) if (nu > i / 4) person(c, 880 + i * 80, 806, 200 + (i % 2) * 10, { lady: true, col: INK, face: -1 })
    c.restore()
    snowfall(c, t, 0.14, -90, 6)
    typeset(c, 'Dr. Curtis Welch', W / 2, 190, F.headI(84, 700), C.paper, prog(t, qName - 0.1, qName + 1.0), { shadow: '#000' })
    typeset(c, 'the only doctor in Nome', W / 2, 262, F.bodyI(50), C.paper2, prog(t, qName + 0.9, qName + 1.9), { shadow: '#000' })
    fade(c, 1 - prog(t, qWin + 0.3, qWin + 0.7)); finish(c, t, true); return true
  }

  // =============================== 3. the outbreak ===============================
  function bed(c, x, y, lit) {
    c.fillStyle = INK; c.fillRect(x - 130, y - 40, 260, 14); c.fillRect(x - 136, y - 96, 12, 96); c.fillRect(x + 124, y - 70, 12, 70)
    c.beginPath(); c.moveTo(x - 110, y - 40); c.bezierCurveTo(x - 90, y - 78, x + 60, y - 70, x + 120, y - 40); c.closePath(); c.fill(); c.beginPath(); c.arc(x - 92, y - 58, 15, 0, 7); c.fill()
    // the candle on the stand
    c.fillRect(x + 170, y - 60, 40, 60); c.fillStyle = C.paper2; c.fillRect(x + 184, y - 96, 12, 36)
    if (lit > 0) { glow(c, x + 190, y - 108, 620 * lit, '246,199,112', 0.75 * lit); c.fillStyle = C.gold2; c.beginPath(); c.ellipse(x + 190, y - 108, 6 * lit, 13 * lit, 0, 0, 7); c.fill() }
    else { c.strokeStyle = 'rgba(200,206,222,0.4)'; c.lineWidth = 2; c.beginPath(); c.moveTo(x + 190, y - 98); c.quadraticCurveTo(x + 200, y - 130, x + 186, y - 160); c.stroke() }
  }
  function vial(c, x, y, s, col, a = 1) { c.save(); c.globalAlpha *= a; c.translate(x, y); c.scale(s, s); c.fillStyle = col; c.beginPath(); c.roundRect(-13, -50, 26, 86, 9); c.fill(); c.fillStyle = INK; c.fillRect(-9, -64, 18, 16); c.restore() }
  function s3(c, t, q, S) {
    const qBoy = q('then in the middle'), qDied = q('boy died'), qGirl = q('the next day') - 0.2, qKnew = q('welch knew') - 0.4, qDip = q('diphtheria'), qCl = q('it closes') - 0.2, qCure = q('there was a cure') - 0.4, qExp = q('had expired'), qTel = q('so he sent') - 0.4, qEpi = q('an epidemic is almost')
    if (t < qKnew + 0.3) {
      c.fillStyle = '#1b1d2a'; c.fillRect(0, 0, W, H); c.fillStyle = '#10121a'; c.fillRect(0, 800, W, 280)
      const l1 = 1 - prog(t, qDied + 0.3, qDied + 1.2), l2 = prog(t, qGirl - 1.2, qGirl - 0.4) * (1 - prog(t, q('7yearold') + 0.9, q('7yearold') + 1.8))
      const z = 1 + 0.06 * prog(t, S.vis, qKnew, 'l'); c.save(); zoom(c, 960, 560, z)
      bed(c, 520, 800, l1 * (0.9 + 0.1 * noise(t * 6, 1))); if (t > qGirl - 1.3) bed(c, 1240, 800, l2 * (0.9 + 0.1 * noise(t * 6, 2)))
      person(c, 250, 800, 330, { hat: 'none', col: INK, bulk: 1.1, lean: 0.12, arm: 0.12 })
      c.restore()
      finish(c, t, true); return true
    }
    if (t < qCure + 0.3) {
      shore(c, t, { hy: 700, stars: 0.5 })
      c.save(); zoom(c, 960, 600, 1.05); nome(c, t, { gy: 706, lit: 0.25, red: prog(t, qCl, qCure - 0.5) * 0.7 }); c.restore()
      snowfall(c, t, 0.14, -90, 6)
      text(c, 'DIPHTHERIA', W / 2, 300, F.head(190, 900), RED, { track: 10, alpha: prog(t, qDip - 0.1, qDip + 0.4), shadow: '#000', blur: 40 })
      fade(c, 1 - prog(t, qKnew + 0.3, qKnew + 0.7)); finish(c, t, true); return true
    }
    if (t < qTel + 0.3) {
      c.fillStyle = '#0b0c12'; c.fillRect(0, 0, W, H)
      const ex = prog(t, qExp - 0.1, qExp + 0.6)
      glow(c, 960, 500, 620, '246,199,112', 0.4 * (1 - ex))
      vial(c, 960, 520, 4.2, mix(C.gold2, '#565a66', ex), prog(t, qCure + 0.3, qCure + 0.8))
      text(c, 'antitoxin', 960, 880, F.headI(80, 700), C.paper, { alpha: prog(t, qCure + 0.6, qCure + 1.1) })
      if (ex > 0) { c.save(); c.translate(960, 520); c.rotate(-0.18); c.globalAlpha = ex; c.strokeStyle = RED; c.lineWidth = 8; c.strokeRect(-240, -60, 480, 120); text(c, 'EXPIRED', 0, 38, F.head(100, 900), RED, { track: 10 }); c.restore() }
      fade(c, 1 - prog(t, qCure + 0.3, qCure + 0.6)); finish(c, t, true); return true
    }
    paper(c, t, C.paper2)
    c.save(); c.translate(960, 500); c.rotate(-0.012); c.fillStyle = 'rgba(60,40,20,0.25)'; c.fillRect(-690, -250, 1400, 520); c.fillStyle = '#f4ead2'; c.fillRect(-700, -260, 1400, 520); c.strokeStyle = C.ink; c.lineWidth = 3; c.strokeRect(-700, -260, 1400, 520)
    text(c, 'RADIO TELEGRAM', -660, -200, F.sc(40), C.ink, { align: 'left', track: 8 }); text(c, 'Nome, Alaska · January 22, 1925', 660, -200, F.bodyI(38), C.ink2, { align: 'right' }); rule(c, -660, 660, -176, C.ink, 1)
    const lines = ['AN EPIDEMIC OF DIPHTHERIA IS ALMOST', 'INEVITABLE HERE  STOP  I AM IN URGENT', 'NEED OF ONE MILLION UNITS OF', 'DIPHTHERIA ANTITOXIN  STOP'], tot = lines.join('').length, p = prog(t, qEpi - 0.2, S.end - 0.4); let done = 0
    lines.forEach((ln, i) => { const lp = clamp((p * tot - done) / ln.length); typeset(c, ln, -640, -80 + i * 82, F.old(56, true), i >= 2 ? C.red : C.ink, lp, { align: 'left', track: 3 }); done += ln.length })
    text(c, 'WELCH', 640, 230, F.old(44, true), C.ink, { align: 'right', alpha: prog(t, S.end - 0.4, S.end), track: 4 })
    c.restore(); finish(c, t, false); return false
  }

  // =============================== 4. the map ===============================
  const MAP = { cx: -151, cy: 62.8, k: 56, x: 1020, y: 560 }
  function dot(c, m, name, col, r = 13, label, lo = {}) { const [x, y] = proj(m, PL[name]); c.fillStyle = col; c.strokeStyle = C.ink; c.lineWidth = 4; c.beginPath(); c.arc(x, y, r, 0, 7); c.fill(); c.stroke(); if (label) text(c, label, x + (lo.dx ?? 22), y + (lo.dy ?? 12), F.headI(lo.px || 44, 700), C.ink, { align: lo.align || 'left', alpha: lo.a ?? 1, stroke: C.paper, sw: 8 }) }
  function rail(c, m, p) { const a = proj(m, PL.anchorage), b = proj(m, [-150, 62.9]), d = proj(m, PL.nenana), pts = [a, b, d]; c.save(); c.strokeStyle = C.ink; c.lineWidth = 7; c.beginPath(); const L1 = Math.hypot(b[0] - a[0], b[1] - a[1]), L2 = Math.hypot(d[0] - b[0], d[1] - b[1]), l = (L1 + L2) * clamp(p); c.moveTo(a[0], a[1]); if (l <= L1) c.lineTo(lerp(a[0], b[0], l / L1), lerp(a[1], b[1], l / L1)); else { c.lineTo(b[0], b[1]); c.lineTo(lerp(b[0], d[0], (l - L1) / L2), lerp(b[1], d[1], (l - L1) / L2)) } c.stroke(); c.strokeStyle = C.paper; c.lineWidth = 3; c.setLineDash([10, 10]); c.stroke(); c.restore() }
  function s4(c, t, q, S) {
    const qF = q('they found'), qU = q('300000 units'), qTr = q('a train could'), qSt = q('and there the tracks'), qEnd = q('from the end'), q674 = q('674 miles'), qPl = q('there were three') - 0.4, qAll = q('all three had'), qPc = q('were in pieces'), qLeft = q('that left') - 0.4, qDog = q('by dog')
    paper(c, t)
    if (t < qPl + 0.3 ) {
      const z = 1 + 0.04 * prog(t, S.vis, qPl, 'l'); c.save(); zoom(c, 960, 540, z)
      hatch(c, k => k.rect(0, 0, W, H), { gap: 14, alpha: 0.16, angle: 0, box: [0, 0, W, H], wob: 3 })
      alaska(c, MAP, { fill: C.paper2 })
      text(c, 'ALASKA', proj(MAP, [-153, 67.5])[0], proj(MAP, [-153, 67.5])[1], F.sc(60), C.ink3, { track: 26 })
      const rp = prog(t, qEnd - 0.2, q674 + 0.6, 'io'); if (rp > 0) route(c, MAP, 0, rp, RED, 7, [3, 14])
      rail(c, MAP, prog(t, qTr, qSt, 'io'))
      dot(c, MAP, 'nome', RED, 14 + 3 * Math.sin(t * 4), 'Nome', { dx: -24, dy: -22, align: 'right' })
      if (t > qF - 0.2) dot(c, MAP, 'anchorage', C.gold, 14 * prog(t, qF - 0.2, qF + 0.2, 'back'), 'Anchorage', { a: prog(t, qF, qF + 0.4), dy: 44, dx: -20 })
      if (t > qSt - 0.3) dot(c, MAP, 'nenana', C.ink, 11, 'Nenana', { a: prog(t, qSt - 0.3, qSt + 0.2), dy: -16 })
      c.restore()
      text(c, '300,000 units', 1580, 640, F.head(72, 900), C.ink, { alpha: prog(t, qU - 0.1, qU + 0.4) * (1 - prog(t, qEnd - 0.4, qEnd)) })
      text(c, 'end of the rails', 1560, 330, F.bodyI(46), C.ink2, { alpha: prog(t, qSt, qSt + 0.5) * (1 - prog(t, q674 - 0.5, q674)) })
      text(c, '674 miles', 330, 170, F.head(120, 900), RED, { alpha: prog(t, q674 - 0.1, q674 + 0.4) })
      finish(c, t, false); return false
    }
    if (t < qLeft + 0.3) {
      const gy = 760; c.strokeStyle = C.ink; c.lineWidth = 5; c.beginPath(); c.moveTo(0, gy); c.lineTo(W, gy); c.stroke(); hatch(c, k => k.rect(0, gy + 2, W, 320), { gap: 9, alpha: 0.25, angle: 0.03, box: [0, gy, W, 320] })
      const br = prog(t, qPc - 0.3, qPc + 0.7, 'io')
      for (let i = 0; i < 3; i++) {
        const x = 360 + i * 600, a = prog(t, qPl + 0.3 + i * 0.25, qPl + 0.7 + i * 0.25, 'o'); if (a <= 0) continue
        c.save(); c.globalAlpha = a; biplane(c, x, gy - 84, 2.2, { col: C.ink, wings: br < 0.3 })
        if (br >= 0.3) { c.strokeStyle = C.ink; c.lineWidth = 15; c.lineCap = 'round'; const d = (br - 0.3) / 0.7; c.beginPath(); c.moveTo(x - 150, gy - 12 - (1 - d) * 150); c.lineTo(x + 0, gy - 12 - (1 - d) * 150); c.moveTo(x + 60, gy - 30 - (1 - d) * 60); c.lineTo(x + 200, gy - 30 - (1 - d) * 60 + 18); c.stroke() }
        c.restore()
      }
      text(c, 'three airplanes in Alaska', W / 2, 250, F.headI(76, 700), C.ink, { alpha: prog(t, qPl + 0.4, qPl + 1.0) })
      typeset(c, 'open cockpits · taken apart for the winter', W / 2, 330, F.bodyI(52), C.red, prog(t, qAll, qPc + 0.8))
      finish(c, t, false); return false
    }
    const gy = 800; c.strokeStyle = C.ink; c.lineWidth = 5; c.beginPath(); c.moveTo(0, gy); c.lineTo(W, gy); c.stroke(); hatch(c, k => k.rect(0, gy + 2, W, 280), { gap: 9, alpha: 0.25, angle: 0.03, box: [0, gy, W, 280] })
    const dp = prog(t, qDog - 0.3, qDog + 0.3, 'o')
    dog(c, lerp(-300, 960, prog(t, qLeft + 0.2, qDog + 0.2, 'o')), gy, 6.2, { col: C.ink, run: t * 7, stride: 1 - dp })
    finish(c, t, false); return false
  }

  // =============================== 5. the relay ===============================
  const RM = { cx: -157.3, cy: 64.6, k: 118, x: 960, y: 540 }
  function relayMap(c, t, o = {}) {
    // the trail from Nenana to Nome up close. o: stops (0..1 how many of the 20 show), at (0..1 where the serum is), done (route drawn to)
    hatch(c, k => k.rect(0, 0, W, H), { gap: 14, alpha: 0.14, angle: 0, box: [0, 0, W, H], wob: 3 })
    alaska(c, RM, { fill: C.paper2 })
    route(c, RM, 0, 1, C.ink3, 5, [3, 13])
    if ((o.at ?? 0) > 0) route(c, RM, 0, o.at, RED, 8)
    const n = 20; for (let i = 0; i <= n; i++) { if (i / n > (o.stops ?? 1)) break; const [x, y] = proj(RM, onRoute(i / n)); c.fillStyle = (o.at ?? 0) >= i / n - 0.001 ? RED : C.ink; c.beginPath(); c.arc(x, y, 9, 0, 7); c.fill() }
    dot(c, RM, 'nenana', C.ink, 13, 'Nenana', { dy: -24, dx: -20 }); dot(c, RM, 'nome', RED, 15, 'Nome', { dy: 60, dx: -40 })
    if (o.at != null && o.at > 0 && o.at < 1) { const [x, y] = proj(RM, onRoute(o.at)); glow(c, x, y, 70, '184,64,46', 0.5); c.fillStyle = RED; c.strokeStyle = C.ink; c.lineWidth = 4; c.beginPath(); c.arc(x, y, 15, 0, 7); c.fill(); c.stroke() }
    if (o.labels) { const [x, y] = proj(RM, [-155, 65.2]); text(c, 'Yukon River', x, y - 40, F.bodyI(40), C.ink2); const b = proj(RM, [-163.2, 63.6]); text(c, 'Bering Sea', b[0], b[1], F.bodyI(44), C.ink2) }
  }
  function cylinder(c, x, y, s, open) {
    c.save(); c.translate(x, y); c.scale(s, s); c.rotate(-0.08)
    c.fillStyle = INK; c.beginPath(); c.roundRect(-150, -52, 300, 104, 40); c.fill()
    if (open > 0) { c.save(); c.globalAlpha = open; c.fillStyle = '#20222c'; c.beginPath(); c.roundRect(-120, -38, 240, 76, 26); c.fill(); for (let i = 0; i < 9; i++) vial(c, -96 + i * 24, 2, 0.62, C.gold2); c.restore() }
    c.fillStyle = RED; c.beginPath(); c.roundRect(-150, -52, 300 * (1 - open * 0.72), 104, 40); c.fill()
    c.fillStyle = INK; c.beginPath(); c.roundRect(-158, -58, 30, 116, 12); c.fill(); if (open < 0.2) { c.beginPath(); c.roundRect(128, -58, 30, 116, 12); c.fill(); c.fillRect(-60, -54, 10, 108); c.fillRect(50, -54, 10, 108) }
    c.strokeStyle = '#3a3d4a'; c.lineWidth = 4; c.beginPath(); c.roundRect(-150, -52, 300, 104, 40); c.stroke()
    c.restore()
  }
  function s5(c, t, q, S) {
    const qFig = q('the doctor figured'), q6 = q('about six days'), qNot = q('so they did not') - 0.4, qTw = q('they sent twenty'), qDr = q('twenty drivers'), qEach = q('each one would'), qDay = q('day and night'), qPk = q('the package was') - 0.4, qVi = q('packed with glass'), qStop = q('at every stop') - 0.4, qIn = q('carry it inside'), qMany = q('many of them') - 0.4
    if (t < qPk + 0.3) {
      paper(c, t); const z = 1 + 0.04 * prog(t, S.vis, qPk, 'l'); c.save(); zoom(c, 960, 540, z)
      relayMap(c, t, { stops: prog(t, qTw, qDr + 2.4), at: t > qEach ? prog(t, qEach, qPk, 'l') * 0.62 : 0, labels: true }); c.restore()
      text(c, 'by mail team: weeks', 520, 880, F.headI(60, 700), C.ink, { alpha: prog(t, S.start, S.start + 0.5) * (1 - prog(t, qNot - 0.4, qNot)) })
      text(c, 'the serum would last: about 6 days', 620, 950, F.headI(60, 700), C.red, { alpha: prog(t, q6 - 0.6, q6) * (1 - prog(t, qNot - 0.4, qNot)) })
      text(c, '20 drivers · about 150 dogs', 560, 900, F.head(70, 900), C.ink, { alpha: prog(t, qDr, qDr + 0.5), stroke: C.paper, sw: 10 })
      typeset(c, 'day and night', 560, 980, F.bodyI(56), C.red, prog(t, qDay - 0.1, qDay + 0.8))
      finish(c, t, false); return false
    }
    if (t < qStop + 0.3) {
      c.fillStyle = '#0b0c12'; c.fillRect(0, 0, W, H); glow(c, 960, 520, 800, '184,64,46', 0.16)
      cylinder(c, 960, 520, 2.6 + 0.1 * prog(t, qPk, qStop, 'l'), prog(t, qVi - 0.2, qVi + 0.6, 'io') * (1 - prog(t, q('and wrapped') - 0.1, q('and wrapped') + 0.6, 'io')))
      text(c, 'about 20 pounds', W / 2, 900, F.bodyI(56), C.paper2, { alpha: prog(t, qPk + 0.6, qPk + 1.2) })
      fade(c, 1 - prog(t, qPk + 0.3, qPk + 0.6)); finish(c, t, true); return true
    }
    if (t < qMany + 0.3) {
      // a stop on the trail: the package goes in by the stove
      snowland(c, t, { hy: 740, moon: [300, 180, 46] })
      for (let i = 0; i < 9; i++) spruce(c, 80 + i * 230 + (i % 3) * 40, 748, 0.7 + (i % 3) * 0.14, '#0c1330', i)
      cabin(c, 1380, 850, 1.7, { t, lit: 1 })
      team(c, 120, 850, 1.3, { n: 6, stride: 0, load: null, driver: false })
      const wp = prog(t, qStop + 0.4, qIn + 1.2, 'io'), px = lerp(420, 1470, wp)
      if (wp < 1) parka(c, px, 852, 150, { walk: px * 0.05, stride: 1, arm: 0.3, hold: k => { k.fillStyle = RED; k.beginPath(); k.roundRect(-8, 22, 30, 15, 6); k.fill() } })
      snowfall(c, t, 0.2, -160, 3)
      fade(c, 1 - prog(t, qStop + 0.3, qStop + 0.7)); finish(c, t, true); return true
    }
    trail(c, t, { n: 7, bliz: 0.14, moon: [1500, 200, 50], speed: 300 })
    fade(c, 1 - prog(t, qMany + 0.3, qMany + 0.7)); finish(c, t, true); return true
  }

  // =============================== 6. the first driver ===============================
  function thermo(c, x, y, v, a) {
    // v: degrees F (negative). The scale runs 0 at the top to -70 at the bottom
    if (a <= 0) return; c.save(); c.globalAlpha = clamp(a); const h = 420, f = clamp(-v / 70)
    c.fillStyle = 'rgba(8,10,18,0.7)'; c.beginPath(); c.roundRect(x - 90, y - 60, 250, h + 150, 12); c.fill()
    c.fillStyle = C.paper; c.beginPath(); c.roundRect(x - 13, y - 20, 26, h + 30, 13); c.fill(); c.beginPath(); c.arc(x, y + h + 26, 30, 0, 7); c.fill()
    c.fillStyle = RED; c.beginPath(); c.arc(x, y + h + 26, 21, 0, 7); c.fill(); c.fillRect(x - 6, y + f * h, 12, h * (1 - f) + 12)
    c.fillStyle = C.paper; for (let d = 0; d <= 70; d += 10) { const yy = y + d / 70 * h; c.fillRect(x + 20, yy - 2, d % 20 ? 12 : 22, 4); if (d % 20 === 0) text(c, d ? '−' + d : '0', x + 54, yy + 12, F.old(32, true), C.paper, { align: 'left' }) }
    c.restore()
  }
  function s6(c, t, q, S) {
    const qFirst = q('the first driver'), qTie = q('he tied') - 0.4, qOut = q('and went out'), q50 = q('it was fifty') - 0.3, q62 = q('it dropped to'), qRan = q('he ran beside'), qIn = q('when he came in') - 0.4, qNext = q('the next mans') - 0.4, qPour = q('they had to pour')
    if (t < qTie + 0.3) {
      snowland(c, t, { hy: 760, moon: [1600, 170, 44] })
      for (let i = 0; i < 7; i++) spruce(c, 60 + i * 300, 768, 0.7 + (i % 3) * 0.14, '#0c1330', i)
      T2.rails(c, -50, W + 50, 838, INK)
      const tx = track(t, [[S.vis, -500], [S.start + 3.2, 1150, 'o']]); T2.train(c, tx, 838, 1.25, t, { col: INK, wagons: 2, spoke: '#3a4664', win: C.gold2, roll: tx * 0.03, smoke: 1 })
      c.fillStyle = INK; c.fillRect(1330, 640, 12, 200); glow(c, 1336, 630, 220, '246,199,112', 0.5); c.fillStyle = C.gold2; c.beginPath(); c.arc(1336, 630, 13, 0, 7); c.fill()
      team(c, 1380, 930, 1.05, { n: 5, stride: 0, load: null, driver: false }); parka(c, 1340, 934, 130, { face: -1 })
      snowfall(c, t, 0.2, -120, 3)
      text(c, 'Nenana · January 27', W / 2, 200, F.headI(76, 700), C.paper, { alpha: prog(t, S.start, S.start + 0.6), shadow: '#000' })
      typeset(c, '“Wild Bill” Shannon', W / 2, 280, F.bodyI(56), C.paper2, prog(t, qFirst + 0.6, qFirst + 1.7), { shadow: '#000' })
      finish(c, t, true); return true
    }
    if (t < qIn + 0.3) {
      const going = prog(t, qOut - 0.3, qOut + 1.0, 'io')
      trail(c, t, { n: 6, bliz: 0.18, speed: 320 * going, off: 320 * Math.max(0, t - qOut + 0.3) * (going < 1 ? going * 0.5 : 1), ice: true, jog: t > qRan - 0.3, tx: 150, moon: [1300, 170, 44], stars: 1 })
      const v = track(t, [[q50, -30], [q50 + 0.8, -50, 'o'], [q62, -50], [q62 + 1.2, -62, 'o']])
      thermo(c, 1640, 250, v, prog(t, q50 - 0.2, q50 + 0.3))
      text(c, Math.round(v) + '°F', 1676, 150, F.head(64, 900), C.paper, { alpha: prog(t, q50 - 0.2, q50 + 0.3) })
      fade(c, 1 - prog(t, qTie + 0.3, qTie + 0.7)); finish(c, t, true); return true
    }
    // the roadhouse: he comes in; the next man goes out
    snowland(c, t, { hy: 740, stars: 1 })
    for (let i = 0; i < 9; i++) spruce(c, 80 + i * 230 + (i % 3) * 40, 748, 0.7 + (i % 3) * 0.14, '#0c1330', i + 7)
    cabin(c, 1420, 850, 1.7, { t, lit: 1 })
    const second = t > qNext
    if (!second) { dog(c, 760, 852, 1.3, { lie: 1, head: 1 }); dog(c, 610, 856, 1.3, { lie: 1, head: 1 }); dog(c, 470, 852, 1.3, { lie: 1, head: 1, face: -1 }); dog(c, 900, 852, 1.3, { head: 0.5 }); dog(c, 1010, 852, 1.3, { sit: 1 }); sled(c, 200, 852, 1.3, { load: null }); parka(c, 1130, 852, 150, { lean: 0.1 }) }
    else {
      team(c, 300, 852, 1.3, { n: 6, stride: 0, load: RED, driver: true }); parka(c, 220, 854, 140, { arm: 0.5 })
      const st = prog(t, qPour, qPour + 0.5); for (let i = 0; i < 8; i++) { const a = ((t * 0.7 + i / 8) % 1); c.fillStyle = `rgba(236,240,250,${0.5 * (1 - a) * st})`; c.beginPath(); c.arc(290 + Math.sin(a * 6 + i) * 16, 740 - a * 150, 10 + a * 30, 0, 7); c.fill() }
    }
    snowfall(c, t, 0.2, -160, 3)
    fade(c, 1 - prog(t, qIn + 0.3, qIn + 0.7) + (t > qNext - 0.3 && t < qNext + 0.3 ? 1 - Math.abs(t - qNext) / 0.3 : 0)); finish(c, t, true); return true
  }

  // =============================== 7. hand to hand ===============================
  function s7(c, t, q, S) {
    const q30 = q('thirty miles'), q28 = q('twenty eight'), q40 = q('forty'), qOne = q('one driver') - 0.4, qSo = q('so he put'), qNome = q('in nome the town') - 0.4, qSch = q('schools closed'), qDoc = q('the doctor counted')
    if (t < qOne + 0.3) {
      paper(c, t); const p = lerp(0.1, 0.5, prog(t, S.vis, qOne, 'l'))
      c.save(); zoom(c, 960, 540, 1.04); relayMap(c, t, { at: p, labels: true }); c.restore()
      ;[['30 miles', q30], ['28 miles', q28], ['40 miles', q40]].forEach(([s, at], i) => text(c, s, 1180 + i * 250, 250 + i * 70, F.head(60, 900), C.ink, { alpha: prog(t, at - 0.1, at + 0.2), stroke: C.paper, sw: 10 }))
      finish(c, t, false); return false
    }
    if (t < qNome + 0.3) {
      trail(c, t, { n: 6, bliz: 0.2, speed: 150, tx: 60, stars: 1, moon: [400, 190, 46], after: (k, off, gy) => { const lx = 60 + (185 + 6 * 88) * 1.6 + 90; if (t > qSo - 0.2) { parka(k, lx, gy, 168, { walk: off * 0.06, stride: 1, lean: 0.16, arm: -0.2 }); k.strokeStyle = INK; k.lineWidth = 3; k.beginPath(); k.moveTo(lx - 12, gy - 110); k.lineTo(lx - 110, gy - 60); k.stroke() } } })
      typeset(c, 'Charlie Evans', W / 2, 220, F.headI(76, 700), C.paper, prog(t, qOne + 0.5, qOne + 1.4), { shadow: '#000' })
      fade(c, 1 - prog(t, qOne + 0.3, qOne + 0.7)); finish(c, t, true); return true
    }
    c.save(); zoom(c, 960, 560, 1.06 + 0.04 * prog(t, qNome, S.out, 'l')); shore(c, t, { hy: 700, stars: 0.5 }); nome(c, t, { gy: 706, lit: 0.2, red: 0.5 }); c.restore()
    snowfall(c, t, 0.3, -140, 6)
    text(c, 'QUARANTINE', W / 2, 260, F.head(150, 900), C.paper, { track: 16, alpha: prog(t, qNome + 0.5, qNome + 1.0), shadow: '#000', blur: 40 })
    typeset(c, 'more than 20 cases', W / 2, 350, F.bodyI(64), RED, prog(t, qDoc + 0.8, qDoc + 2.0), { shadow: '#000' })
    fade(c, 1 - prog(t, qNome + 0.3, qNome + 0.7)); finish(c, t, true); return true
  }

  window.SCENES = [s1, s2, s3, s4, s5, s6, s7]
  window.SRS = { fade, zoom, trail, nome, shore, lostScene, relayMap, dot, RM, RED, vial, thermo }
})()
