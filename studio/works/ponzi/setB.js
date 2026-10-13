// setB.js: the places of the Ponzi story in Style B (painted). Boston 1920: School Street, offices, banks, newspapers.
window.POB = (function () {
  const { W, H, clamp, lerp, prog, keys, rng, ell, poly, smooth, shade, mixCol, vgrad, hgrad, rgrad, layer, ridge, fog, sky, post, person, crowd, paper, text, tree } = PK
  PK.costume('shopkeeper', { skin: '#d8a888', shirt: '#ece6d8', pants: '#4a4440', vest: '#3a3a3a', boot: '#1a1410', hat: 'bowler', hatCol: '#2a2420', collar: 'tie', tie: '#5a2a22', hair: '#4a3020', moustache: '#4a3020', apron: null })
  PK.costume('barron', { skin: '#e0b096', shirt: '#ece6d8', pants: '#2a2a30', coat: '#2a2a30', boot: '#14110e', hat: null, collar: 'tie', tie: '#14110e', hair: '#e8e4dc', beard: '#e8e4dc', moustache: '#e8e4dc', build: 1.25 })
  PK.costume('rose', { skin: '#e8bca0', shirt: '#6a3a4a', skirt: '#5a2e3a', boot: '#14110e', hat: 'cloche', hatCol: '#2a1a24', hair: '#2a1a14', build: 0.88, height: 0.92 })
  PK.costume('ponziY', { skin: '#d4a07e', shirt: '#d8d0c0', pants: '#4a4440', boot: '#2a2018', hat: 'cap', hatCol: '#3a3430', hair: '#1d1712', moustache: '#1d1712', height: 0.92 })
  PK.costume('waiter', { skin: '#d4a07e', shirt: '#f2eee4', pants: '#14110e', vest: '#14110e', boot: '#0e0c0a', hat: null, collar: 'tie', tie: '#14110e', hair: '#1d1712', moustache: '#1d1712', height: 0.92, apron: null })
  PK.costume('ponziP', { skin: '#d4a07e', shirt: '#8a8478', pants: '#8a8478', boot: '#2a2420', hat: null, hair: '#1d1712', moustache: '#1d1712', stripes: true, height: 0.92 })
  PK.costume('teller', { skin: '#dcae90', shirt: '#ece6d8', pants: '#3a3a40', vest: '#3a3a40', boot: '#14110e', hat: null, collar: 'tie', tie: '#2a2a3a', hair: '#3a2a1e', glasses: true })
  const LINE = ['clerk', 'maid', 'shopkeeper', 'police', 'lady', 'suit', 'reporter', 'clerk', 'maid', 'police']

  // a Boston brick office block, 1920: tall windows, a cornice, a shop front at street level
  function block(c, x, y, w, h, o = {}) {
    const r = rng((x * 5 + y) | 0), col = o.col || ['#7a3e2c', '#8a4a34', '#6a4434', '#9a7a5a', '#8a5a40'][(r() * 5) | 0]
    c.fillStyle = hgrad(c, x, x + w, shade(col, 0.1), col, shade(col, -0.25)); c.fillRect(x, y - h, w, h)
    c.fillStyle = shade(col, -0.35); c.fillRect(x - 8, y - h - 16, w + 16, 20); c.fillStyle = shade(col, 0.2); c.fillRect(x - 8, y - h - 22, w + 16, 6)
    const cols = Math.max(2, Math.round(w / 70)), rows = Math.max(2, Math.round((h - 130) / 80))
    for (let rr = 0; rr < rows; rr++) for (let cc = 0; cc < cols; cc++) { const ww = w / cols * 0.5, wh = 50, wx = x + (cc + 0.25) * w / cols, wy = y - h + 30 + rr * 80; c.fillStyle = '#e8dcc0'; c.fillRect(wx - 4, wy - 4, ww + 8, wh + 10); c.fillStyle = o.lit && r() > 0.5 ? '#f2c46a' : vgrad(c, wy, wy + wh, '#5a6a7a', '#2a3440'); c.fillRect(wx, wy, ww, wh); c.fillStyle = '#e8dcc0'; c.fillRect(wx, wy + wh / 2 - 1, ww, 3) }
    // shop front with an awning
    c.fillStyle = '#2a2420'; c.fillRect(x, y - 120, w, 120); c.fillStyle = vgrad(c, y - 110, y - 10, '#7a8a8a', '#3a4446'); c.fillRect(x + 12, y - 110, w - 24, 80)
    if (o.awning) { const aw = o.awning; for (let k = 0; k < w; k += 30) { c.fillStyle = (k / 30) % 2 ? aw : '#efe6d4'; poly(c, [[x + k, y - 135], [x + k + 30, y - 135], [x + k + 36, y - 105], [x + k + 6, y - 105]], null); c.fill() } }
    if (o.sign) { c.fillStyle = '#1a1814'; c.fillRect(x + 10, y - h + (o.signY || h - 160), w - 20, 44); text(c, o.sign, x + w / 2, y - h + (o.signY || h - 160) + 22, o.signSize || 24, '#e8cf8a', { weight: 800 }) }
  }
  function schoolStreet(c, cam, t, o = {}) {
    layer(c, cam, 0.06, c => sky(c, o.night ? '#0e1424' : '#8aa6c2', o.night ? '#2a3a54' : '#efe4cc', { horizon: 600, clouds: o.night ? 0 : 6, sun: o.night ? null : [1600, 120, 520] }))
    layer(c, cam, 0.45, c => { const r = rng(4); let x = -900; while (x < 2900) { const w = 160 + r() * 120, h = 360 + r() * 260; block(c, x, 700, w, h, { col: mixCol(['#7a3e2c', '#8a4a34', '#9a7a5a'][(r() * 3) | 0], '#b8b8c0', 0.45) }); x += w + 6 } })
    layer(c, cam, 0.8, c => {
      const signs = o.signs ?? { 2: 'SECURITIES EXCHANGE CO.' }
      let x = -900, k = 0; const r = rng(9)
      while (x < 3000) { const w = 260 + r() * 140, h = 520 + r() * 220; block(c, x, 820, w, h, { awning: ['#7a2a22', '#2a4a3a', '#3a3a6a'][k % 3], sign: signs[k], signY: h - 200, signSize: 26, lit: o.night }); x += w + 4; k++ }
      // street, tram rails, sidewalk
      c.fillStyle = vgrad(c, 820, 1100, '#6a6660', '#3a3632'); c.fillRect(-1400, 820, 4800, 600)
      c.fillStyle = '#9a948a'; c.fillRect(-1400, 820, 4800, 40); c.fillStyle = 'rgba(0,0,0,0.25)'; c.fillRect(-1400, 858, 4800, 6)
      c.strokeStyle = 'rgba(200,200,200,0.35)'; c.lineWidth = 3; for (const y of [960, 985]) { c.beginPath(); c.moveTo(-1400, y); c.lineTo(3400, y); c.stroke() }
      for (let lx = -700; lx < 2900; lx += 520) { c.fillStyle = '#1a1814'; c.fillRect(lx, 560, 8, 280); ell(c, lx + 4, 552, 14, 18, 0, o.night ? '#f2d080' : '#3a3a3a') }
    })
    layer(c, cam, 1, c => { if (o.inner) o.inner(c) })
  }
  // a 1920 touring car (Locomobile-like), moving by x
  function car(c, x, y, s, t, o = {}) {
    c.save(); c.translate(x, y); c.scale(s * (o.f || 1), s)
    const col = o.col || '#1a2a3a'
    c.fillStyle = hgrad(c, -200, 200, shade(col, 0.25), col, shade(col, -0.3)); c.beginPath(); c.moveTo(-220, -50); c.lineTo(-210, -110); c.lineTo(-40, -110); c.lineTo(-20, -150); c.lineTo(60, -150); c.lineTo(70, -110); c.lineTo(200, -100); c.quadraticCurveTo(230, -90, 230, -60); c.lineTo(230, -40); c.lineTo(-220, -40); c.closePath(); c.fill()
    c.fillStyle = '#c8c0a8'; c.fillRect(150, -112, 70, 50); c.strokeStyle = '#2a2a2a'; c.lineWidth = 2; for (let k = 0; k < 6; k++) { c.beginPath(); c.moveTo(156 + k * 11, -110); c.lineTo(156 + k * 11, -64); c.stroke() }
    c.strokeStyle = '#2a2420'; c.lineWidth = 4; c.beginPath(); c.moveTo(-30, -150); c.lineTo(-60, -220); c.lineTo(-200, -220); c.lineTo(-210, -110); c.stroke()
    ell(c, 225, -90, 14, 14, 0, '#f2e8c0')
    for (const wx of [-150, 150]) { ell(c, wx, -36, 46, 46, 0, '#14110e'); ell(c, wx, -36, 30, 30, 0, '#d8d0b8'); c.strokeStyle = '#6a6458'; c.lineWidth = 3; for (let k = 0; k < 8; k++) { const a = (o.d || 0) / 46 + k * Math.PI / 4; c.beginPath(); c.moveTo(wx, -36); c.lineTo(wx + Math.cos(a) * 28, -36 + Math.sin(a) * 28); c.stroke() } }
    c.fillStyle = '#14110e'; c.fillRect(-210, -60, 420, 8)
    c.restore()
  }
  // an office interior: panelled walls, a frosted door, desks, filing cabinets
  function office(c, cam, t, o = {}) {
    layer(c, cam, 0.9, c => {
      c.fillStyle = vgrad(c, -200, 1000, o.wall || '#5a4a3a', '#3a2e22'); c.fillRect(-900, -400, 3800, 1700)
      c.fillStyle = 'rgba(0,0,0,0.15)'; c.fillRect(-900, 560, 3800, 420); for (let x = -880; x < 2900; x += 160) { c.strokeStyle = 'rgba(255,230,190,0.08)'; c.lineWidth = 3; c.strokeRect(x, 600, 140, 320) }
      if (o.window !== false) { const wx = o.winX ?? 1300; c.fillStyle = '#1a140e'; c.fillRect(wx - 10, 150, 420, 400); c.fillStyle = o.night ? '#1a2440' : vgrad(c, 160, 540, '#c8d4dc', '#8a9aa8'); c.fillRect(wx, 160, 400, 380); c.strokeStyle = '#1a140e'; c.lineWidth = 8; c.beginPath(); c.moveTo(wx + 200, 160); c.lineTo(wx + 200, 540); c.moveTo(wx, 350); c.lineTo(wx + 400, 350); c.stroke(); if (!o.night) { c.save(); c.beginPath(); c.rect(wx, 160, 400, 380); c.clip(); const r = rng(3); for (let k = 0; k < 4; k++) block(c, wx + k * 110 - 20, 600, 90, 260 + r() * 80, { col: '#8a8a90' }); c.restore() } }
      if (o.door) { c.fillStyle = '#4a3420'; c.fillRect(300, 300, 240, 560); c.fillStyle = 'rgba(220,226,220,0.75)'; c.fillRect(330, 330, 180, 240); [].concat(o.door).forEach((L, i, A) => text(c, L, 420, 450 + (i - (A.length - 1) / 2) * 30, 22, '#2a2420', { weight: 800 })) }
      for (const fx of o.cabinets || [-300, -120]) { c.fillStyle = hgrad(c, fx, fx + 150, '#5a4a3a', '#3a2e22'); c.fillRect(fx, 520, 150, 400); for (let k = 0; k < 4; k++) { c.strokeStyle = 'rgba(0,0,0,0.4)'; c.lineWidth = 2; c.strokeRect(fx + 12, 540 + k * 96, 126, 84); ell(c, fx + 75, 580 + k * 96, 10, 4, 0, '#c8b890') } }
    })
    layer(c, cam, 1, c => { c.fillStyle = vgrad(c, 900, 1200, '#5a4030', '#2a1c12'); c.fillRect(-900, 900, 3800, 600); c.strokeStyle = 'rgba(0,0,0,0.2)'; c.lineWidth = 2; for (let x = -900; x < 2900; x += 60) { c.beginPath(); c.moveTo(x, 900); c.lineTo(x - 120, 1200); c.stroke() } if (o.inner) o.inner(c) })
  }
  function desk(c, x, y, w, o = {}) { c.fillStyle = vgrad(c, y, y + 30, '#6a4428', '#3a2414'); c.fillRect(x, y, w, 30); c.fillStyle = hgrad(c, x, x + w, '#5a3a22', '#3a2414'); c.fillRect(x + 10, y + 30, w * 0.36, 130); c.fillRect(x + w - 30, y + 30, 20, 130); if (o.lamp) { c.fillStyle = '#2a4a2a'; c.beginPath(); c.moveTo(x + w - 120, y - 70); c.lineTo(x + w - 50, y - 70); c.lineTo(x + w - 60, y - 50); c.lineTo(x + w - 110, y - 50); c.fill(); c.fillStyle = '#c8b890'; c.fillRect(x + w - 88, y - 50, 6, 50); c.fillStyle = rgrad(c, x + w - 85, y - 40, 4, 260, 'rgba(255,220,140,0.3)', 'rgba(255,220,140,0)'); c.fillRect(x + w - 345, y - 300, 520, 520) } }
  // money: a bundle of bills, and stacks
  function bills(c, x, y, s, o = {}) { c.save(); c.translate(x, y); c.scale(s, s); c.rotate(o.rot || 0); for (let k = 0; k < (o.n || 3); k++) { c.fillStyle = vgrad(c, -30, 30, '#b8c8a0', '#8aa078'); c.fillRect(-60 + k * 3, -30 - k * 5, 120, 60); c.strokeStyle = 'rgba(40,70,40,0.6)'; c.lineWidth = 2; c.strokeRect(-54 + k * 3, -24 - k * 5, 108, 48); ell(c, k * 3, -k * 5, 14, 18, 0, 'rgba(40,70,40,0.4)') } c.fillStyle = '#c8a87a'; c.fillRect(-10, -50, 20, 70); c.restore() }
  function cashPile(c, x, y, n, s = 1) { const r = rng(n + 7); for (let k = 0; k < n; k++) bills(c, x + (r() - 0.5) * 260 * s, y - (r() * 120 + k * 4) * s, 0.7 * s, { rot: (r() - 0.5) * 0.8, n: 2 }) }
  // a newspaper front page
  function newspaper(c, x, y, s, head, o = {}) {
    if (window.__vertical) s = Math.min(s, 0.74)
    c.save(); c.translate(x, y); c.scale(s, s); c.rotate(o.rot || 0)
    c.fillStyle = 'rgba(0,0,0,0.35)'; c.fillRect(-370, -470, 760, 980)
    c.fillStyle = vgrad(c, -480, 480, '#ece4d0', '#d4c8ae'); c.fillRect(-380, -480, 760, 960)
    text(c, 'THE BOSTON POST', 0, -420, 56, '#1a1814', { weight: 800, font: 'OldStandard' }); c.fillStyle = '#1a1814'; c.fillRect(-350, -380, 700, 4); c.fillRect(-350, -372, 700, 2)
    text(c, o.date || 'BOSTON, 1920', 0, -352, 18, '#3a3430', { font: 'OldStandard' })
    head.forEach((h, i) => text(c, h, 0, -290 + i * 70, o.headSize || 54, '#1a1814', { weight: 800, font: 'OldStandard' }))
    const top = -290 + head.length * 70
    if (o.photo) { c.fillStyle = '#3a3430'; c.fillRect(-150, top, 300, 340); if (o.photoFn) { c.save(); c.beginPath(); c.rect(-150, top, 300, 340); c.clip(); o.photoFn(c, 0, top + 170); c.restore() } }
    c.fillStyle = 'rgba(40,36,30,0.45)'; for (let col = 0; col < 3; col++) for (let k = 0; k < 18; k++) { const cx = -340 + col * 236; if (o.photo && col === 1 && k < 13) continue; c.fillRect(cx, top + 20 + k * 22, 210 - (k % 4) * 14, 6) }
    c.restore()
  }
  // the international reply coupon
  function coupon(c, x, y, s, o = {}) {
    c.save(); c.translate(x, y); c.scale(s, s); c.rotate(o.rot || 0)
    c.fillStyle = 'rgba(0,0,0,0.3)'; c.fillRect(-180, -110, 370, 230)
    c.fillStyle = vgrad(c, -120, 120, '#e8e0f0', '#c8c0d8'); c.fillRect(-190, -120, 380, 240)
    c.strokeStyle = '#5a4a7a'; c.lineWidth = 3; c.strokeRect(-176, -106, 352, 212); c.lineWidth = 1.5; c.strokeRect(-166, -96, 332, 192)
    text(c, 'UNION POSTALE UNIVERSELLE', 0, -64, 18, '#3a2a5a', { weight: 800 }); text(c, 'COUPON-RÉPONSE', 0, -30, 30, '#3a2a5a', { weight: 800 }); text(c, 'INTERNATIONAL', 0, 4, 22, '#3a2a5a', { weight: 700 })
    ell(c, 0, 60, 40, 30, 0, 'rgba(90,70,120,0.25)')
    c.restore()
  }
  function stamp(c, x, y, s, col = '#8a2a2a') { c.save(); c.translate(x, y); c.scale(s, s); c.fillStyle = '#f2ece0'; c.fillRect(-36, -44, 72, 88); c.fillStyle = col; c.fillRect(-28, -36, 56, 72); ell(c, 0, -4, 16, 20, 0, 'rgba(255,255,255,0.4)'); text(c, '2¢', 0, 26, 14, '#f2ece0', { weight: 800 }); c.restore() }
  // a 1900s steamship at the dock
  function steamship(c, x, y, s, t) { c.save(); c.translate(x, y + Math.sin(t) * 2); c.scale(s, s); c.fillStyle = hgrad(c, -500, 500, '#1a1a1e', '#2a2a30'); c.beginPath(); c.moveTo(-520, -120); c.lineTo(520, -120); c.lineTo(470, 20); c.lineTo(-480, 20); c.closePath(); c.fill(); c.fillStyle = '#8a2a22'; c.fillRect(-490, -10, 960, 22); c.fillStyle = '#ece6d8'; c.fillRect(-380, -220, 700, 100); for (let k = 0; k < 14; k++) ell(c, -350 + k * 50, -170, 9, 9, 0, '#2a3440'); for (const fx of [-180, 60]) { c.fillStyle = '#c8a24a'; c.fillRect(fx, -380, 70, 160); c.fillStyle = '#14110e'; c.fillRect(fx, -390, 70, 24); for (let k = 0; k < 5; k++) { const ph = (t * 0.4 + k / 5) % 1; ell(c, fx + 35 - ph * 200, -420 - ph * 160, 30 + ph * 60, 24 + ph * 40, 0, `rgba(80,76,72,${0.5 * (1 - ph)})`) } } c.restore() }
  function mansion(c, x, y, s) { c.save(); c.translate(x, y); c.scale(s, s); c.fillStyle = hgrad(c, -400, 400, '#f2ece0', '#d8d0c0', '#b8b0a0'); c.fillRect(-400, -360, 800, 360); c.fillStyle = vgrad(c, -520, -360, '#5a5a62', '#3a3a42'); poly(c, [[-440, -360], [0, -520], [440, -360]]); c.fill(); for (let k = 0; k < 6; k++) { c.fillStyle = '#e8e2d6'; c.fillRect(-300 + k * 120, -330, 24, 330) } for (let r2 = 0; r2 < 2; r2++) for (let k = 0; k < 5; k++) { c.fillStyle = '#2a3440'; c.fillRect(-250 + k * 120, -300 + r2 * 150, 50, 90) } c.fillStyle = '#4a3020'; c.fillRect(-40, -140, 80, 140); c.restore() }
  // the pyramid: each row owed by the one below it
  function pyramid(c, x, y, rows, k, o = {}) {
    for (let r2 = 0; r2 < rows; r2++) { const n = Math.round(Math.pow(1.5, r2) * 2), a = clamp(k * rows - r2); if (a <= 0) continue; for (let i = 0; i < Math.min(n, 60); i++) { const px = x + (i - (Math.min(n, 60) - 1) / 2) * Math.max(6, 60 - r2 * 6), py = y + r2 * 70; ell(c, px, py, Math.max(4, 16 - r2), Math.max(4, 16 - r2), 0, `rgba(${r2 === rows - 1 && o.red ? '170,40,30' : '243,231,208'},${a})`) } }
  }
  const shotOf = (t, list) => { let s = list[0]; for (const L of list) if (t >= L[0]) s = L; const i = list.indexOf(s), t1 = (list[i + 1] || [1e9])[0]; return { name: s[1], t0: s[0], t1, u: clamp((t - s[0]) / (t1 - s[0])) } }
  return { block, schoolStreet, car, office, desk, bills, cashPile, newspaper, coupon, stamp, steamship, mansion, pyramid, shotOf, LINE }
})()
window.PRELOAD = () => Promise.all([document.fonts.load('800 40px OldStandard'), document.fonts.load('40px OldStandard')])
