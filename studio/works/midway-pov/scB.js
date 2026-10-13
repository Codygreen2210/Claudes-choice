// scB.js: the rest of Midway, through their eyes: Yamamoto's map table (1), Rochefort's desk (2), the dry dock (3),
// Nagumo's morning (4), the Yorktown's gunner (9), and the cost (10).
(function () {
  const { W, H, clamp, lerp, prog, keys, rng, ell, poly, shade, vgrad, hgrad, rgrad, post, text, label, shake, flashes, count, paper, pathLine, person } = PK
  const { carrier, destroyer, battleship, fire, blast, splash, flak, plane, planeTop, carrierTop, hangar, torpedo, bomb, seaChart, shotOf } = MWB
  const { view, high, low, down, sbd, scope, bridgeWin, tracers } = POV
  const SC = window.SCENES = window.SCENES || []
  const tag = (c, s, a) => label(c, s, W / 2, 230, a, 46)
  const word = (c, s, y, a, size = 54) => text(c, s, W / 2, y, size, '#f3e7d0', { italic: true, shadow: 16, alpha: a })
  const dark = c => { c.fillStyle = vgrad(c, 0, H, '#24282c', '#101214'); c.fillRect(0, 0, W, H) }
  const scr = (c, fn) => { c.save(); c.setTransform(1, 0, 0, 1, 0, 0); fn(c); c.restore() }
  const push = (c, z, x = W / 2, y = H / 2) => { c.translate(W / 2, H / 2); c.scale(z, z); c.translate(-x, -y) }
  const io = k => k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2
  // a desk seen from the chair: wood, a pool of lamp light, the edge of the desk at the bottom
  function desk(c, t, o = {}) {
    c.fillStyle = vgrad(c, 0, H, o.wood || '#4a3424', shade(o.wood || '#4a3424', -0.35)); c.fillRect(-400, -400, W + 800, H + 800)
    c.strokeStyle = 'rgba(20,12,6,0.25)'; c.lineWidth = 2; for (let y = -380; y < H + 380; y += 34) { c.beginPath(); c.moveTo(-400, y); c.bezierCurveTo(400, y + 8, 1200, y - 8, W + 400, y + 4); c.stroke() }
    if (o.inner) o.inner(c)
  }
  const lamp = (c, x = 900, y = 420, r = 900, a = 0.35) => scr(c, c => { c.fillStyle = rgrad(c, x, y, 40, r, `rgba(255,226,170,${a})`, 'rgba(255,226,170,0)'); c.fillRect(0, 0, W, H); c.fillStyle = rgrad(c, x, y, r * 0.6, r * 1.6, 'rgba(0,0,0,0)', 'rgba(0,0,0,0.6)'); c.fillRect(0, 0, W, H) })
  // a code sheet: rows of five-figure groups
  function codeSheet(c, x, y, w, h, rot, seed, o = {}) {
    c.save(); c.translate(x, y); c.rotate(rot); paper(c, 0, 0, w, h, [], { col: o.col || '#ece4cc' })
    const r = rng(seed); c.fillStyle = 'rgba(40,34,28,0.75)'; c.font = `600 ${o.size || 22}px OldStandard`; c.textAlign = 'left'
    for (let row = 0; row < Math.floor((h - 80) / 34); row++) { let s = ''; for (let g = 0; g < Math.floor((w - 80) / 110); g++) s += String(Math.floor(r() * 90000) + 10000) + '  '; c.fillText(s, -w / 2 + 40, -h / 2 + 60 + row * 34) }
    c.restore()
  }
  // the bridge window onto the sea, carriers around, planes on the deck below; o.inner adds to the world
  function bridgeView(c, t, o = {}) {
    view(c, { pitch: Math.sin(t * 0.4) * 8, yaw: o.yaw || 0, z: o.z || 1 }, c => low(c, t, { H0: 420, speed: 20, inner: (c, H0) => {
      if (o.sky) o.sky(c, H0)
      carrier(c, 1600, H0 + 70, 0.28, t, { jp: true, island: 'left' }); carrier(c, 250, H0 + 60, 0.22, t, { jp: true })
      c.fillStyle = vgrad(c, 740, 1100, '#a07e54', '#7a5c3a'); poly(c, [[-200, 1100], [300, 740], [1700, 740], [2200, 1100]]); c.fill()
      c.strokeStyle = 'rgba(255,255,255,0.6)'; c.lineWidth = 6; c.beginPath(); c.moveTo(1000, 740); c.lineTo(1060, 1100); c.stroke()
      if (o.inner) o.inner(c, H0)
    } }))
    bridgeWin(c, t)
  }
  // a radio message handed to you: a slip of paper, typed
  function message(c, t, t0, head, lines, o = {}) {
    dark(c); const a = prog(t, t0, t0 + 0.5, 'o'), y = lerp(700, 0, a)
    c.save(); c.translate(0, y); c.rotate(-0.015)
    paper(c, 960, 520, 1300, 560, [[head, 34, '#6a4a2a', { italic: true }], ['', 20], ...lines.map(L => [L[0], L[1] || 58, L[2] || '#2a1e14', { font: 'OldStandard', weight: 700, alpha: L[3] ?? 1 }])], { top: 90, col: '#ebe2c6', font: 'OldStandard' })
    c.restore(); post(c, { x: 960 }, { rays: false, vignette: 0.6 })
  }

  // ---------- 1: Yamamoto's map table
  SC[1] = (c, t, q, S) => {
    const k = prog(t, S.vis, S.out)
    const cam = keys(t, [[S.vis, { z: 1.25, x: 760, y: 520 }], [q('the american aircraft') - 0.5, { z: 1.4, x: 1300, y: 600 }], [q('so you draw') - 0.3, { z: 1.15, x: 960, y: 520 }], [q('about two hundred') - 0.3, { z: 1.25, x: 760, y: 500 }], [S.out, { z: 1.35, x: 1100, y: 520 }]])
    c.save(); push(c, cam.z, cam.x, cam.y)
    seaChart(c, t, (c, w, h) => {
      // land: Japan on the left, Hawaii on the right, Midway a speck between
      c.fillStyle = 'rgba(120,96,62,0.9)'; ell(c, -640, -200, 60, 200, 0.5); c.fill(); ell(c, -600, 60, 40, 90, 0.2); c.fill()
      for (const [x, y, r] of [[560, 150, 22], [530, 130, 12], [600, 175, 16]]) { ell(c, x, y, r, r * 0.7, 0.3); c.fill() }
      ell(c, 160, -10, 9, 6, 0); c.fill()
      text(c, 'Japan', -640, 210, 34, '#3a2a1a', { italic: true }); text(c, 'Hawaii', 570, 220, 32, '#3a2a1a', { italic: true })
      const pa = prog(t, q('you planned the attack'), q('you planned the attack') + 0.8)
      if (pa > 0) { text(c, 'Pearl Harbor', 560, 90, 30, '#8a2a1e', { italic: true, alpha: pa }); c.strokeStyle = `rgba(138,42,30,${pa})`; c.lineWidth = 6; c.beginPath(); c.moveTo(535, 120); c.lineTo(585, 170); c.moveTo(585, 120); c.lineTo(535, 170); c.stroke() }
      const ca = prog(t, q('the american aircraft'), q('the american aircraft') + 0.8) * (1 - prog(t, q('so you draw'), q('so you draw') + 1))
      if (ca > 0) { for (let j = 0; j < 3; j++) { c.globalAlpha = ca; c.fillStyle = '#2a4a7a'; c.fillRect(640 + j * 60, 40 - j * 30, 44, 12); c.globalAlpha = 1 } text(c, 'not in port', 700, -40, 30, '#2a4a7a', { italic: true, alpha: ca }) }
      const pl = prog(t, q('so you draw'), q('so you draw') + 2.5, 'io')
      if (pl > 0) { pathLine(c, [[-560, -80], [-200, -60], [140, -14]], pl, '#8a2a1e', 6); text(c, 'Midway', 160, -50, 36, '#3a2a1a', { italic: true, weight: 800, alpha: prog(t, q('called midway'), q('called midway') + 0.4) }) }
      const out = prog(t, q('attack it'), q('attack it') + 2, 'io'); if (out > 0) pathLine(c, [[540, 120], [360, 60], [190, 4]], out, '#2a4a7a', 5)
      const fl = prog(t, q('about two hundred'), q('about two hundred') + 3)
      if (fl > 0) { const r = rng(8); for (let j = 0; j < 90; j++) { const p = r(), x = lerp(-560, 60, p) + (r() - 0.5) * 60, y = lerp(-80, -30, p) + (r() - 0.5) * 70; if (r() < fl * 1.1) ell(c, x, y, 5, 3, 0, 'rgba(138,42,30,0.85)') } }
      const fc = prog(t, q('your four carriers'), q('your four carriers') + 0.8)
      if (fc > 0) for (let j = 0; j < 4; j++) { c.globalAlpha = fc; c.fillStyle = '#8a2a1e'; c.fillRect(40 + (j % 2) * 56, -150 + Math.floor(j / 2) * 34, 46, 14); c.globalAlpha = 1 }
      if (fc > 0) text(c, '4 carriers, waiting', 70, -200, 30, '#8a2a1e', { italic: true, alpha: fc })
    })
    c.restore()
    // the approval slip on the corner of the table
    const ap = prog(t, q('your own staff'), q('your own staff') + 0.6, 'o') * (1 - prog(t, q('about two hundred') - 0.3, q('about two hundred') + 0.3))
    if (ap > 0) { c.save(); c.globalAlpha = ap; paper(c, 1500, lerp(1300, 820, ap), 520, 300, [['Operation MI', 40, '#2a1e14', { font: 'OldStandard' }], ['approved', 46, '#8a2a1e', { italic: true, alpha: prog(t, q('they give in'), q('they give in') + 0.4) }]], { top: 80, rot: 0.06 }); c.restore() }
    lamp(c, 760, 380, 1100, 0.25)
    post(c, { x: 960 }, { rays: false, vignette: 0.55 })
    tag(c, 'Adm. Isoroku Yamamoto  ·  six months after Pearl Harbor', prog(t, S.vis + 0.6, S.vis + 1.2) * (1 - prog(t, q('you planned') + 1.5, q('you planned') + 2)))
  }

  // ---------- 2: Rochefort's desk in the basement
  SC[2] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'desk'], [q('two letters') - 0.3, 'af'], [q('so you set') - 0.3, 'trap'], [q('a day later') - 0.3, 'reply']])
    if (sh.name === 'desk' || sh.name === 'af') {
      const af = sh.name === 'af', k = prog(t, sh.t0, sh.t1)
      const cam = af ? { z: lerp(1.6, 1.8, k), x: 980, y: 500 } : keys(t, [[sh.t0, { z: 1.1, x: 900, y: 560 }], [sh.t1, { z: 1.3, x: 1040, y: 520 }]])
      c.save(); push(c, cam.z, cam.x, cam.y)
      desk(c, t, { inner: c => {
        codeSheet(c, 620, 420, 760, 560, -0.06, 3); codeSheet(c, 1340, 600, 760, 600, 0.05, 7); codeSheet(c, 980, 500, 700, 520, -0.01, 11, { col: '#f2ead4' })
        // the two letters, circled
        const a = prog(t, q('you even know'), q('you even know') + 0.6); if (a > 0) { text(c, 'AF', 1000, 560, 72, '#8a2a1e', { font: 'OldStandard', weight: 800, alpha: a }); c.strokeStyle = `rgba(138,42,30,${a})`; c.lineWidth = 5; c.beginPath(); c.ellipse(1000, 560, 80 * prog(t, q('two letters'), q('two letters') + 0.6) + 1, 52, -0.1, 0, Math.PI * 2 * prog(t, q('two letters'), q('two letters') + 0.8)); c.stroke() }
        const m = prog(t, q('you are sure'), q('you are sure') + 0.5); if (m > 0) text(c, '= Midway ?', 1180, 640, 46, '#8a2a1e', { italic: true, alpha: m })
        ell(c, 330, 860, 80, 80, 0, '#d8d0c0'); ell(c, 330, 860, 62, 62, 0, '#3a2414'); c.strokeStyle = '#c8c0b0'; c.lineWidth = 14; c.beginPath(); c.arc(420, 860, 34, -1.2, 1.2); c.stroke()
        c.save(); c.translate(1280, 860); c.rotate(-0.6); c.fillStyle = '#c8a24a'; c.fillRect(-160, -7, 320, 14); c.fillStyle = '#2a2a2a'; poly(c, [[160, -7], [190, 0], [160, 7]]); c.fill(); c.restore()
      } })
      c.restore()
      lamp(c, 900, 360, 1000, 0.3)
      post(c, { x: 960 }, { rays: false, vignette: 0.55 })
      tag(c, 'Cmdr. Joseph Rochefort  ·  Station Hypo, Pearl Harbor', prog(t, S.vis + 0.4, S.vis + 1) * (1 - prog(t, q('your team has') - 0.4, q('your team has'))))
    } else if (sh.name === 'trap') {
      message(c, t, q('midway is told') - 0.2, 'Midway  ·  in plain English', [['FRESH WATER', 66], ['DISTILLATION PLANT', 66], ['BROKEN DOWN', 66, '#8a2a1e']])
      if (t < q('midway is told') - 0.2) { dark(c); word(c, 'a trap', 520, prog(t, q('so you set'), q('so you set') + 0.4), 72) }
    } else {
      message(c, t, sh.t0, 'Japanese report, decoded', [['AF', 140, '#8a2a1e'], ['IS SHORT OF WATER', 70, '#2a1e14', prog(t, q('is short'), q('is short') + 0.5)]])
    }
  }

  // ---------- 3: the dry dock
  SC[3] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'harbor'], [q('you are one of') - 0.3, 'dock'], [q('when she sails') - 0.3, 'sail'], [q('three american carriers') - 0.3, 'wait']])
    if (sh.name === 'harbor' || sh.name === 'sail') {
      const k = prog(t, sh.t0, sh.t1), sail = sh.name === 'sail'
      view(c, { z: 1.15, yaw: lerp(-40, 40, k) }, c => low(c, t, { H0: 520, speed: 4, inner: (c, H0) => {
        c.fillStyle = 'rgba(70,80,70,0.8)'; poly(c, [[-1600, H0], [-200, H0 - 60], [300, H0 - 20], [800, H0 - 70], [1500, H0 - 30], [3400, H0]]); c.fill()
        carrier(c, sail ? lerp(900, 1500, k) : lerp(400, 900, k), H0 + 90, 0.5, t, { fire: sail ? 0 : 0.12, planes: 0 })
        if (sail) { const r = rng(4); for (let j = 0; j < 14; j++) { const x = lerp(900, 1500, k) - 260 + r() * 520, f = Math.abs(Math.sin(t * 9 + j)); ell(c, x, H0 + 30 - r() * 10, 3 + f * 4, 3 + f * 4, 0, `rgba(255,220,140,${0.5 + 0.5 * f})`) } }
      } }))
      scr(c, c => { c.fillStyle = vgrad(c, 900, H, '#2a2a28', '#141412'); poly(c, [[0, 940], [W, 900], [W, H], [0, H]]); c.fill() })
      post(c, { x: 960 }, sail ? { rays: 0.18, rayX: 600, grade: 'rgba(230,160,100,0.18)', vignette: 0.55 } : { rays: false, night: 0.25, vignette: 0.6 })
      if (!sail) { tag(c, 'Pearl Harbor  ·  May 27, 1942', prog(t, q('you are one of') - 6, q('you are one of') - 5.5)); word(c, 'He has 2 carriers ready.', 150, prog(t, q('what he doesnt'), q('what he doesnt') + 0.4) * (1 - prog(t, sh.t1 - 0.5, sh.t1)), 46) }
      else tag(c, 'USS Yorktown sails, May 30', prog(t, sh.t0 + 0.3, sh.t0 + 0.8))
    } else if (sh.name === 'dock') {
      // the dock floor, looking up at her hull: scaffolds, floodlights, the welders' sparks
      const k = prog(t, sh.t0, sh.t1)
      c.fillStyle = vgrad(c, 0, H, '#141820', '#24282c'); c.fillRect(0, 0, W, H)
      c.save(); push(c, lerp(1.0, 1.12, k), lerp(900, 1020, k), 520)
      c.fillStyle = hgrad(c, 0, W, '#3a4248', '#56606a', '#3a4248'); c.beginPath(); c.moveTo(-200, -200); c.lineTo(W + 200, -200); c.lineTo(W + 200, 520); c.quadraticCurveTo(960, 720, -200, 520); c.closePath(); c.fill()
      c.strokeStyle = 'rgba(20,24,28,0.5)'; c.lineWidth = 2; for (let y = -100; y < 600; y += 60) { c.beginPath(); c.moveTo(-200, y); c.quadraticCurveTo(960, y + 120 * (y / 600), W + 200, y); c.stroke() }
      c.fillStyle = 'rgba(10,10,10,0.85)'; ell(c, 1180, 260, 160, 90, 0.2); c.fill(); c.strokeStyle = '#6a3a1a'; c.lineWidth = 4; for (let j = 0; j < 6; j++) { c.beginPath(); c.moveTo(1060 + j * 40, 200); c.lineTo(1080 + j * 40, 330); c.stroke() }
      c.strokeStyle = '#6a5a40'; c.lineWidth = 8; for (let x = 0; x < W; x += 220) { c.beginPath(); c.moveTo(x, 1100); c.lineTo(x + 40, 300); c.stroke() } for (let y = 420; y < 1100; y += 160) { c.beginPath(); c.moveTo(-100, y); c.lineTo(W + 100, y - 40); c.stroke() }
      for (const [x, y] of [[1130, 290], [1250, 230], [700, 420], [1500, 380]]) { const r = rng(Math.floor(t * 12) + x); for (let j = 0; j < 22; j++) { const a = r() * Math.PI * 0.9 + 0.1, d = r() * 160, g = r() * 40; ell(c, x + Math.cos(a) * d, y + Math.sin(a) * d + g * g * 0.05, 3, 3, 0, `rgba(255,${200 + r() * 55},${120 + r() * 80},${1 - d / 170})`) } c.fillStyle = rgrad(c, x, y, 2, 120, 'rgba(255,240,200,0.7)', 'rgba(255,240,200,0)'); c.fillRect(x - 120, y - 120, 240, 240) }
      for (let j = 0; j < 5; j++) person(c, 300 + j * 330, 1040, 0.6, { cos: 'worker', pose: { name: j % 2 ? 'hold' : 'stand', at: [40, -260] }, f: j % 2 ? 1 : -1 })
      c.restore()
      for (const x of [200, 1700]) scr(c, c => { c.fillStyle = rgrad(c, x, 60, 10, 700, 'rgba(255,248,220,0.35)', 'rgba(255,248,220,0)'); c.fillRect(0, 0, W, H) })
      post(c, { x: 960 }, { rays: false, vignette: 0.6 })
      const gone = 1 - prog(t, q('about 1400') - 0.6, q('about 1400') - 0.1), d90 = prog(t, q('ninety days'), q('ninety days') + 0.4) * gone, d3 = prog(t, q('nimitz gives you'), q('nimitz gives you') + 0.4) * gone
      if (d90 > 0) { count(c, W / 2, 200, '90 days', 110, '#f3e7d0', { alpha: d90 * (1 - d3 * 0.6) }); if (d3 > 0) { c.save(); c.strokeStyle = '#c8483a'; c.lineWidth = 10; c.beginPath(); c.moveTo(760, 200); c.lineTo(lerp(760, 1160, d3), 200); c.stroke(); c.restore(); count(c, W / 2, 330, '3 days', 130, '#e86a50', { alpha: d3 }) } }
      tag(c, 'about 1,400 men, around the clock', prog(t, q('about 1400'), q('about 1400') + 0.4))
    } else {
      seaChart(c, t, (c, w, h) => {
        c.fillStyle = 'rgba(120,96,62,0.9)'; ell(c, -40, 60, 12, 8, 0); c.fill(); text(c, 'Midway', -40, 100, 36, '#3a2a1a', { italic: true })
        const a = prog(t, sh.t0, sh.t0 + 1.5, 'io'); for (let j = 0; j < 3; j++) { c.fillStyle = '#2a4a7a'; c.fillRect(lerp(600, 260, a) + j * 50, lerp(200, -80, a) - j * 26, 44, 12) }
        pathLine(c, [[640, 220], [260, -80]], a, '#2a4a7a', 4); text(c, 'waiting, north of Midway', 330, -140, 30, '#2a4a7a', { italic: true, alpha: a })
        const b = prog(t, q('japan has no idea'), q('japan has no idea') + 1.2); for (let j = 0; j < 4; j++) { c.fillStyle = '#8a2a1e'; c.fillRect(lerp(-700, -560, b) + (j % 2) * 56, -260 + Math.floor(j / 2) * 34, 46, 14) }
        if (b > 0) text(c, '?', -420, -240, 70, '#8a2a1e', { weight: 800, alpha: b })
      })
      post(c, { x: 960 }, { rays: false, vignette: 0.5 })
    }
  }

  // ---------- 4: Nagumo's morning
  SC[4] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'dawn'], [q('at seven') - 0.3, 'radio'], [q('your second wave') - 0.3, 'hangar'], [q('then a scout') - 0.3, 'scout'], [q('you reverse') - 0.3, 'swap'], [q('and your planes') - 0.3, 'land']])
    if (sh.name === 'dawn' || sh.name === 'land') {
      const dawn = sh.name === 'dawn', u = t - sh.t0
      bridgeView(c, t, { yaw: dawn ? lerp(-60, 40, prog(t, sh.t0, sh.t1)) : 0, inner: (c, H0) => {
        if (dawn) for (let j = 0; j < 8; j++) { const p = ((u * 0.12 + j * 0.125) % 1); plane(c, lerp(1500, -300, p), lerp(840, H0 - 220, p * p), lerp(0.7, 0.2, p), t, { kind: j % 3 ? 'kate' : 'zero', f: -1, ang: 0.15 * p }) }
        else for (let j = 0; j < 4; j++) { const p = ((u * 0.1 + j * 0.25) % 1); plane(c, lerp(2200, 700, p), lerp(H0 - 120, 830, p), lerp(0.25, 0.75, p), t, { kind: 'kate', f: -1, ang: 0.08 }) }
      } })
      post(c, { x: 960 }, dawn ? { rays: 0.14, rayX: 1300, night: 0.25, grade: 'rgba(240,160,110,0.25)', vignette: 0.6 } : { rays: 0.08, rayX: 1300, vignette: 0.55 })
      if (dawn) { tag(c, 'June 4, 1942  ·  4:30 a.m.', prog(t, S.vis + 0.3, S.vis + 0.9) * (1 - prog(t, q('you are admiral') - 0.3, q('you are admiral')))); tag(c, 'Vice Adm. Chuichi Nagumo  ·  aboard Akagi', prog(t, q('you are admiral'), q('you are admiral') + 0.5) * (1 - prog(t, q('you send'), q('you send') + 0.4))); if (t > q('you send')) count(c, W / 2, 230, Math.round(108 * prog(t, q('you send'), q('you send') + 2)) + ' planes', 92) }
      else word(c, 'land them first', 230, prog(t, q('you decide'), q('you decide') + 0.4), 58)
    } else if (sh.name === 'radio') {
      message(c, t, sh.t0, '7:00 a.m.  ·  from the Midway strike leader', [['THERE IS NEED', 70], ['FOR A SECOND ATTACK', 70, '#8a2a1e', prog(t, q('there is need'), q('there is need') + 0.5)]])
    } else if (sh.name === 'scout') {
      message(c, t, q('sends a message') - 0.2, 'from scout plane No. 4, launched half an hour late', [['10 SHIPS, TO THE EAST', 64], ['ONE APPEARS TO BE', 58, '#2a1e14', prog(t, q('and one of them'), q('and one of them') + 0.4)], ['A CARRIER', 80, '#8a2a1e', prog(t, q('to be a carrier'), q('to be a carrier') + 0.4)]])
      if (t < q('sends a message') - 0.2) { dark(c); word(c, 'a scout, half an hour late', 520, prog(t, sh.t0 + 0.2, sh.t0 + 0.6), 56) }
    } else {
      // the hangar deck: torpedoes coming off, bombs going on; then the order reversed, everything stacked in the open
      const swap = sh.name === 'swap', k = prog(t, sh.t0, sh.t1), [sx, sy] = shake(t, swap ? [sh.t0 + 0.6] : [], 8)
      const cam = { x: lerp(900, 1050, k), y: 640, z: 1.3, sx, sy }
      hangar(c, cam, t, { inner: c => {
        const off = swap ? 0 : prog(t, q('take off the torpedoes'), q('take off the torpedoes') + 3)
        for (let j = 0; j < 4; j++) { const x = 200 + j * 440; plane(c, x + 120, 860, 1.0, 0, { kind: 'kate', f: -1 }); c.save(); c.globalAlpha = swap ? 1 : 1 - off; torpedo(c, x + 90, 900, 0.9); c.restore(); if (!swap) { c.save(); c.globalAlpha = off; bomb(c, x + 100, 905, 0.6); c.restore() } }
        if (swap) { for (let j = 0; j < 9; j++) bomb(c, 120 + j * 170, 1010 - (j % 2) * 30, 0.55); c.strokeStyle = '#1a1a1a'; c.lineWidth = 8; c.beginPath(); c.moveTo(-200, 960); c.bezierCurveTo(400, 1040, 900, 940, 1500, 1020); c.bezierCurveTo(1800, 1060, 2200, 980, 2600, 1000); c.stroke() }
        for (let j = 0; j < 6; j++) person(c, 120 + j * 330 + Math.sin(t * 2 + j) * 30, 1000, 0.75, { cos: 'jpcrew', pose: { name: j % 2 ? 'carry' : 'crouch' }, f: j % 2 ? 1 : -1 })
      } })
      post(c, { x: 960 }, { rays: false, vignette: 0.6 })
      if (!swap) word(c, 'torpedoes off, bombs on', 150, prog(t, q('take off the'), q('take off the') + 0.4), 50)
      else word(c, 'bombs off, torpedoes back on', 150, prog(t, sh.t0 + 0.2, sh.t0 + 0.6), 50)
      if (swap) word(c, 'everything out in the open', 250, prog(t, q('no time'), q('no time') + 0.4), 44)
    }
  }

  // ---------- 9: the Yorktown's gunner
  function ringSight(c) { scr(c, c => { c.strokeStyle = 'rgba(20,20,20,0.85)'; c.lineWidth = 4; for (const r of [70, 170, 280]) { c.beginPath(); c.arc(960, 500, r, 0, Math.PI * 2); c.stroke() } c.lineWidth = 3; c.beginPath(); c.moveTo(680, 500); c.lineTo(1240, 500); c.moveTo(960, 220); c.lineTo(960, 780); c.stroke(); ell(c, 960, 500, 6, 6, 0, '#c8402e')
    c.fillStyle = hgrad(c, 1100, 1700, '#1a1c1e', '#3a3e42'); poly(c, [[1180, 1100], [1060, 760], [1100, 750], [1300, 1100]]); c.fill(); poly(c, [[1400, 1100], [1120, 770], [1160, 762], [1540, 1100]]); c.fill(); c.fillStyle = '#2a2e32'; c.fillRect(1100, 900, 700, 200) }) }
  SC[9] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'guns'], [q('three bombs hit') - 0.2, 'hits'], [q('your crew patches') - 0.3, 'patch'], [q('this time its') - 0.3, 'torp'], [q('the yorktown stops') - 0.3, 'list'], [q('even then') - 0.3, 'sub'], [q('but that afternoon') - 0.3, 'found']])
    const u = t - sh.t0
    if (sh.name === 'guns') {
      view(c, { pitch: -380, z: 1.1, yaw: Math.sin(t * 0.7) * 40 }, c => low(c, t, { H0: 520, speed: 6, inner: (c, H0) => {
        for (let j = 0; j < 4; j++) { const p = ((u * 0.12 + j * 0.25) % 1); plane(c, lerp(700 + j * 160, 960, p), lerp(-500, 380, p), lerp(0.25, 1.1, p), t, { kind: 'kate', load: 'bomb', ang: 1.2 }) }
        flak(c, t, 500, -400, 900, 800, 18, 31)
      } }))
      tracers(c, t, 1300, 1100, 12, 5)
      ringSight(c)
      post(c, { x: 960 }, { rays: 0.1, rayX: 1300, vignette: 0.5 })
      tag(c, 'USS Yorktown  ·  just after noon', prog(t, q('the carrier hiryus'), q('the carrier hiryus') + 0.5))
    } else if (sh.name === 'hits' || sh.name === 'patch') {
      const hitT = sh.name === 'hits' ? [q('three bombs hit') + 0.3, q('three bombs hit') + 0.9, q('three bombs hit') + 1.5] : [], [sx, sy] = shake(t, hitT, 18)
      view(c, { pitch: 40 + sy, yaw: sx, z: 1.05 }, c => low(c, t, { H0: 380, speed: 4, inner: (c, H0) => {
        c.fillStyle = vgrad(c, H0, 1200, '#8a8478', '#5a564e'); poly(c, [[-600, 1300], [700, H0 + 20], [1300, H0 + 20], [2500, 1300]]); c.fill()
        c.strokeStyle = 'rgba(40,36,30,0.35)'; c.lineWidth = 2; for (let j = -10; j <= 10; j++) { c.beginPath(); c.moveTo(1000 + j * 28, H0 + 20); c.lineTo(1000 + j * 190, 1300); c.stroke() }
        hitT.forEach((h, i) => { blast(c, 760 + i * 260, 600 + i * 60, 1.0, (t - h) / 1.3) })
        const sm = sh.name === 'hits' ? prog(t, hitT[0], hitT[0] + 2) : 1 - prog(t, sh.t0, sh.t1) * 0.7; if (sm > 0) fire(c, 1000, 620, 500, t, 0.6 * sm)
        if (sh.name === 'patch') { c.fillStyle = '#a89878'; for (let j = 0; j < 5; j++) c.fillRect(860 + j * 60, 660, 50, 14 * prog(t, sh.t0 + j * 0.6, sh.t0 + j * 0.6 + 0.5)); for (let j = 0; j < 6; j++) person(c, 700 + j * 120, 720 + (j % 2) * 30, 0.5, { cos: 'worker', pose: { name: j % 2 ? 'carry' : 'crouch' }, f: j % 2 ? 1 : -1 }) }
      } }))
      post(c, { x: 960 }, { rays: 0.06, vignette: 0.55, grade: 'rgba(200,110,60,0.15)' })
      flashes(c, t, hitT, '255,230,180', 0.5)
      if (sh.name === 'patch') word(c, 'patched, and moving again', 150, prog(t, sh.t0 + 0.3, sh.t0 + 0.8), 50)
    } else if (sh.name === 'torp') {
      const h1 = q('two of them') + 0.4, h2 = h1 + 1.0, [sx, sy] = shake(t, [h1, h2], 20)
      view(c, { pitch: 120 + sy, yaw: sx }, c => low(c, t, { H0: 360, speed: 3, inner: (c, H0) => {
        for (const [x0, h] of [[500, h1], [1500, h2]]) { const p = prog(t, sh.t0, h); for (let j = 0; j < 30; j++) { const pp = clamp(p - j * 0.02); if (pp <= 0) continue; ell(c, lerp(x0, 960, pp), lerp(H0 + 20, 1050, pp), lerp(4, 40, pp), lerp(1, 8, pp), 0, `rgba(245,250,255,${0.6 - j * 0.018})`) } splash(c, 960 + (x0 - 960) * 0.1, 1000, 3.2, (t - h) / 1.6) }
        for (let j = 0; j < 4; j++) { const p = ((u * 0.15 + j * 0.25) % 1); plane(c, lerp(-200, 2100, p), H0 - 20 - j * 8, 0.35, t, { kind: 'kate', load: j < 2 ? null : 'torpedo' }) }
        flak(c, t, 200, H0 - 260, 1500, 220, 14, 41)
      } }))
      post(c, { x: 960 }, { rays: 0.06, vignette: 0.55 })
      flashes(c, t, [h1, h2], '255,240,220', 0.6)
    } else if (sh.name === 'list' || sh.name === 'sub') {
      const dusk = sh.name === 'sub', k = prog(t, sh.t0, sh.t1)
      view(c, { roll: dusk ? 0 : -0.22 * prog(t, sh.t0, sh.t0 + 3, 'io'), z: 1.05 }, c => low(c, t, { H0: 470, speed: 2, inner: (c, H0) => {
        if (dusk) { c.save(); c.translate(960, H0 + 60); c.rotate(-0.12); carrier(c, 0, 0, 0.55, t, { planes: 0 }); c.restore(); destroyer(c, 1600, H0 + 30, 0.2, t) }
        else { for (let j = 0; j < 7; j++) ell(c, 300 + j * 210, H0 + 120 + Math.sin(t + j) * 6, 10, 6, 0, '#e8a040'); destroyer(c, 1400, H0 + 40, 0.3, t) }
      } }))
      post(c, { x: 960 }, dusk ? { rays: 0.18, rayX: 500, grade: 'rgba(220,130,80,0.25)', vignette: 0.6 } : { rays: 0.06, vignette: 0.55 })
      if (!dusk) word(c, 'abandon ship', 150, prog(t, q('you are told'), q('you are told') + 0.4))
      else tag(c, 'sunk by a Japanese submarine, June 7', prog(t, q('it takes a'), q('it takes a') + 0.5))
    } else {
      // 5 p.m.: the Hiryu, through a dive bomber's sight
      const k = prog(t, sh.t0, sh.t1), hits = [0, 0.3, 0.6, 0.9].map(d => q('four hits') + d), [sx, sy] = shake(t, hits, 10)
      down(c, t, { k: 0.2 + k * 0.6, rot: 0.3 - k * 0.2, dx: sx, dy: sy, inner: c => { carrierTop(c, 0, 0, 0.5, t, { rot: 0 }); hits.forEach((h, i) => { const uu = (t - h) / 1.4; if (uu > 0) { blast(c, -200 + i * 130, 0, 0.6, uu); if (uu > 0.3) fire(c, -200 + i * 130, 0, 60, t, 0.25) } }) } })
      scope(c, t)
      scr(c, c => { c.fillStyle = 'rgba(220,120,60,0.15)'; c.fillRect(0, 0, W, H) })
      post(c, { x: 960 }, { rays: false, vignette: 0.45 })
      flashes(c, t, hits, '255,230,180', 0.4)
      tag(c, '5 p.m.  ·  the Hiryu', prog(t, q('at five'), q('at five') + 0.4))
    }
  }

  // ---------- 10: the cost, and why
  SC[10] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'turn'], [q('japan lost') - 0.3, 'count'], [q('in japan') - 0.3, 'papers'], [q('the war went on') - 0.3, 'sea'], [q('a code half') - 0.3, 'code'], [q('a ship fixed') - 0.3, 'ship'], [q('men in old') - 0.3, 'planes'], [q('and one pilot') - 0.3, 'pilot'], [q('admiral nimitz') - 0.3, 'quote'], [q('subscribe') - 0.3, 'end']])
    if (sh.name === 'turn') {
      seaChart(c, t, (c, w, h) => { ell(c, 260, 120, 14, 9, 0.3, 'rgba(110,90,60,1)'); text(c, 'Midway', 260, 86, 38, '#3a2a1a', { italic: true }); const back = prog(t, q('he turns the fleet'), sh.t1 - 0.2, 'io'); const x = lerp(-300, -600, back); battleship(c, x, -40, 0.12, t); text(c, 'Yamamoto, with his battleships', x, -110, 30, '#3a2a1a', { italic: true }); text(c, 'hundreds of miles behind', x, 10, 26, '#5a4030', { italic: true }); if (back > 0) pathLine(c, [[-300, -40], [x, -40]], 1, '#8a2a1e', 6) })
      post(c, { x: 960 }, { rays: false, vignette: 0.5 })
    } else if (sh.name === 'count') {
      dark(c)
      const a = prog(t, sh.t0 + 0.2, sh.t0 + 0.8), b = prog(t, q('the united states lost'), q('the united states lost') + 0.6)
      text(c, 'JAPAN', 560, 200, 54, '#f3e7d0', { weight: 800, alpha: a }); text(c, 'UNITED STATES', 1360, 200, 54, '#f3e7d0', { weight: 800, alpha: b })
      ;[['4 carriers', 'four aircraft'], ['1 heavy cruiser', 'a heavy cruiser'], ['≈ 250 planes', 'about 250'], ['3,000+ men', 'more than 3000']].forEach(([s, w], i) => text(c, s, 560, 320 + i * 110, 52, '#c8483a', { weight: 800, alpha: prog(t, q(w), q(w) + 0.3), shadow: 12 }))
      ;[['1 carrier', 'lost the yorktown'], ['1 destroyer', 'a destroyer'], ['≈ 150 planes', 'about 150'], ['307 men', '307 men']].forEach(([s, w], i) => text(c, s, 1360, 320 + i * 110, 52, '#f3e7d0', { weight: 800, alpha: prog(t, q(w), q(w) + 0.3), shadow: 12 }))
      c.fillStyle = 'rgba(243,231,208,0.3)'; c.fillRect(958, 160, 4, 700)
      post(c, { x: 960 }, { rays: false, vignette: 0.5 })
    } else if (sh.name === 'papers') {
      dark(c)
      c.save(); c.translate(W / 2, 540); c.rotate(-0.02); c.fillStyle = 'rgba(0,0,0,0.35)'; c.fillRect(-360, -460, 740, 960); c.fillStyle = vgrad(c, -470, 470, '#ece4d0', '#d4c8ae'); c.fillRect(-370, -470, 740, 940); for (let col = 0; col < 8; col++) for (let k = 0; k < 22; k++) { c.fillStyle = 'rgba(40,36,30,0.55)'; c.fillRect(300 - col * 80, -380 + k * 36, 14, 26) } c.fillStyle = '#1a1814'; c.fillRect(-330, -420, 220, 300); c.restore()
      word(c, 'told: a great victory', 150, prog(t, q('a great victory'), q('a great victory') + 0.4) * (1 - prog(t, q('the wounded') - 0.3, q('the wounded'))))
      word(c, 'the wounded, kept out of sight', 150, prog(t, q('the wounded'), q('the wounded') + 0.4))
      post(c, { x: 960 }, { rays: false, vignette: 0.5 })
    } else if (sh.name === 'sea' || sh.name === 'end' || sh.name === 'ship') {
      const cam = keys(t, [[sh.t0, { x: 900, y: 640, z: 1.15 }], [sh.t1, { x: 1100, y: 640, z: 1.05 }]], 'l')
      MWB.ocean(c, cam, t, { tod: 'dusk', sun: [960, 560, 800, '255,190,130'], inner: c => { carrier(c, 1300, 820, sh.name === 'ship' ? 0.8 : 0.45, t, {}); destroyer(c, 600, 800, 0.3, t) } })
      post(c, { x: 960 }, { rays: 0.18, rayX: 700, grade: 'rgba(200,120,80,0.18)' })
      if (sh.name === 'sea') word(c, 'Japan never had the upper hand at sea again', 150, prog(t, q('but after midway'), q('but after midway') + 0.4), 46)
      else if (sh.name === 'ship') word(c, 'a ship, fixed in three days', 150, prog(t, sh.t0 + 0.2, sh.t0 + 0.6))
      else { const a = prog(t, sh.t0 + 0.3, sh.t0 + 1); text(c, 'Subscribe', W / 2, 330, 96, '#f3e7d0', { weight: 800, alpha: a, shadow: 24 }); text(c, 'animal facts  ·  great battles  ·  financial collapses', W / 2, 430, 40, '#f3e7d0', { italic: true, alpha: prog(t, q('everything from'), q('everything from') + 0.6), shadow: 14 }) }
    } else if (sh.name === 'code') { dark(c); paper(c, 960, 520, 900, 520, [['AF', 200, '#8a2a1e', { weight: 800, font: 'OldStandard' }], ['a code, half broken', 46, '#3a2a1a', { italic: true }]], { top: 150, col: '#ece6d8' }); post(c, { x: 960 }, { rays: false, vignette: 0.55 }) }
    else if (sh.name === 'planes') { const u = t - sh.t0; view(c, { z: 1 }, c => low(c, t, { H0: 440, speed: 120, inner: (c, H0) => { for (let k = 0; k < 4; k++) plane(c, lerp(-200, 2100, ((u * 0.1 + k * 0.25) % 1)), H0 + 40 + k * 26, 0.7, t, { kind: 'tbd', load: 'torpedo' }) } })); post(c, { x: 960 }, { rays: 0.1 }); word(c, 'men in old planes', 150, prog(t, sh.t0 + 0.2, sh.t0 + 0.6)) }
    else if (sh.name === 'pilot') { view(c, { roll: Math.sin(t * 0.5) * 0.03, pitch: -20 }, c => high(c, t, { sun: [1500, 120], speed: 300 })); sbd(c, t, { fuel: 0.15 }); post(c, { x: 960 }, { rays: 0.14, rayX: 1100, vignette: 0.5 }); word(c, 'and kept looking', 230, prog(t, q('and kept looking'), q('and kept looking') + 0.4), 58) }
    else { dark(c); paper(c, 960, 520, 1300, 520, [['McClusky’s decision', 60, '#3a2a1a', { italic: true }], ['“decided the fate', 60, '#3a2a1a', { italic: true }], ['of our carrier task force”', 60, '#3a2a1a', { italic: true }], ['', 16], ['Admiral Chester Nimitz', 32, '#5a4030']], { top: 110, rot: -0.01 }); post(c, { x: 960 }, { rays: false, vignette: 0.55 }) }
  }
})()
