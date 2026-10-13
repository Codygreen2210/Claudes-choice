// setB.js: the places of Tulip Mania in Style B (painted). Dutch towns, a tavern back room, gardens, tulips.
window.TUB = (function () {
  const { W, H, clamp, lerp, prog, keys, rng, ell, poly, smooth, shade, mixCol, vgrad, hgrad, rgrad, layer, ridge, fog, sky, post, foreground, tuft, person, crowd, beast, birds, tree, forest, paper, text, sprite, drawSprite } = PK
  PK.costume('auctioneer', { skin: '#e0b096', shirt: '#3a2a22', pants: '#2a2220', coat: '#4a2a22', boot: '#1a1410', hat: 'brim', hatCol: '#1a1410', collar: 'falling', hair: '#c8b8a0', beard: '#c8b8a0', moustache: '#c8b8a0' })
  PK.costume('clusius', { skin: '#e2b49a', shirt: '#2a2422', pants: '#2a2422', coat: '#2a2422', boot: '#1a1410', hat: 'cap', hatCol: '#1a1410', collar: 'ruff', hair: '#e0dcd4', beard: '#e0dcd4', moustache: '#e0dcd4' })
  PK.costume('preacher', { skin: '#e0b096', shirt: '#14110e', pants: '#14110e', coat: '#14110e', boot: '#0e0c0a', hat: 'capotain', hatCol: '#14110e', collar: 'falling', hair: '#5a4030' })
  PK.costume('sailor17', { skin: '#d4a07e', shirt: '#c8bca0', pants: '#4a5a6a', boot: '#3a2a1a', hat: 'cap', hatCol: '#8a2a22', hair: '#5a3c22', beard: '#5a3c22' })
  PK.costume('mackay', { skin: '#e2b49a', shirt: '#ece6d8', pants: '#2e2a28', coat: '#2e2a28', boot: '#14110e', hat: null, collar: 'tie', tie: '#14110e', hair: '#6a4a30', beard: '#6a4a30' })
  PK.costume('goldgar', { skin: '#e2b49a', shirt: '#5a6a7a', skirt: '#3a3a44', boot: '#14110e', hat: null, hair: '#8a6a4a', glasses: true, build: 0.9, height: 0.95 })
  PK.costume('baker', { skin: '#e0b096', shirt: '#ece6d8', pants: '#5a4a3a', boot: '#3a2a1a', hat: 'cap', hatCol: '#ece6d8', apron: '#f2ede2', hair: '#8a6a4a', moustache: '#8a6a4a' })
  PK.costume('weaver', { skin: '#d6a084', shirt: '#6a5a3a', pants: '#4a3a2a', coat: '#5a4a32', boot: '#2a2018', hat: 'brim', hatCol: '#4a3a2a', collar: 'falling', hair: '#3a2a1e' })
  PK.costume('judge17', { skin: '#e0b096', shirt: '#14110e', pants: '#14110e', coat: '#14110e', boot: '#0e0c0a', hat: 'brim', hatCol: '#14110e', collar: 'ruff', hair: '#d8d4cc', beard: '#d8d4cc' })

  const BUYERS = ['dutchman', 'dutchman2', 'dutchman3', 'weaver', 'baker', 'dutchwoman']

  // ---- tulips and bulbs
  // tulip(c, x, y, s, o): o.col petal colour, o.flame (streak colour) for a 'broken' tulip, o.open 0..1, o.sway
  function tulip(c, x, y, s, o = {}) {
    const col = o.col || '#c8302a', fl = o.flame, sw = o.sway || 0, open = o.open ?? 0.6
    c.save(); c.translate(x, y); c.scale(s, s)
    c.strokeStyle = '#3e6a32'; c.lineWidth = 7; c.lineCap = 'round'; c.beginPath(); c.moveTo(0, 0); c.quadraticCurveTo(sw * 30, -110, sw * 40, -220); c.stroke()
    c.fillStyle = vgrad(c, -150, 0, '#4f8a3e', '#2f5a2a')
    c.beginPath(); c.moveTo(0, -10); c.quadraticCurveTo(-70, -80, -40, -170); c.quadraticCurveTo(-20, -90, 6, -30); c.fill()
    c.beginPath(); c.moveTo(4, -20); c.quadraticCurveTo(70, -60, 56, -140); c.quadraticCurveTo(30, -70, 0, -40); c.fill()
    c.translate(sw * 40, -220)
    const petal = (dx, w, h, shadeK) => {
      c.beginPath(); c.moveTo(dx - w * 0.6, 0); c.bezierCurveTo(dx - w * (0.9 + open * 0.3), -h * 0.5, dx - w * 0.4, -h * 1.05, dx, -h); c.bezierCurveTo(dx + w * 0.4, -h * 1.05, dx + w * (0.9 + open * 0.3), -h * 0.5, dx + w * 0.6, 0); c.quadraticCurveTo(dx, h * 0.25, dx - w * 0.6, 0); c.closePath()
      c.fillStyle = vgrad(c, -h, h * 0.2, shade(col, 0.18 + shadeK), col, shade(col, -0.3 + shadeK)); c.fill()
      if (fl) { c.save(); c.clip(); c.strokeStyle = fl; c.lineCap = 'round'; for (let k = -2; k <= 2; k++) { c.lineWidth = 5 + Math.abs(k) * 1.5; c.beginPath(); c.moveTo(dx + k * w * 0.18, h * 0.1); c.bezierCurveTo(dx + k * w * 0.3, -h * 0.4, dx + k * w * 0.12 + 4, -h * 0.7, dx + k * w * 0.2, -h * 0.98); c.stroke() } c.restore() }
    }
    petal(-16, 34, 92, -0.12); petal(16, 34, 92, -0.12); petal(0, 40, 104, 0.05)
    c.restore()
  }
  function bulb(c, x, y, s, o = {}) {
    c.save(); c.translate(x, y); c.scale(s, s)
    c.fillStyle = rgrad(c, -20, -40, 6, 110, '#e8c89a', '#b8885a', '#6a4a2a'); c.beginPath(); c.moveTo(0, -120); c.bezierCurveTo(30, -80, 90, -60, 80, 0); c.bezierCurveTo(70, 50, -70, 50, -80, 0); c.bezierCurveTo(-90, -60, -30, -80, 0, -120); c.fill()
    c.strokeStyle = 'rgba(90,60,30,0.5)'; c.lineWidth = 2; for (const k of [-0.5, 0, 0.5]) { c.beginPath(); c.moveTo(0, -116); c.quadraticCurveTo(k * 110, -40, k * 60, 36); c.stroke() }
    c.strokeStyle = '#d8c8a8'; c.lineWidth = 2; for (let k = -3; k <= 3; k++) { c.beginPath(); c.moveTo(k * 12, 38); c.quadraticCurveTo(k * 16, 60, k * 20 + 6, 74); c.stroke() }
    c.restore()
  }
  // ---- Dutch gabled houses along a street or canal
  function gable(c, x, y, w, h, o = {}) {
    const r = rng((x * 3 + y) | 0), brick = o.col || ['#8a3a26', '#7a4430', '#9a5a3a', '#6a3a2a', '#8a5040'][(r() * 5) | 0]
    const top = o.kind || ['step', 'bell', 'neck', 'step'][(r() * 4) | 0]
    c.fillStyle = hgrad(c, x, x + w, shade(brick, 0.1), brick, shade(brick, -0.25))
    c.beginPath(); c.moveTo(x, y); c.lineTo(x, y - h)
    if (top === 'step') { const n = 4, sw = w / (2 * n + 1); for (let k = 0; k < n; k++) { c.lineTo(x + sw * k, y - h - sw * k * 1.3); c.lineTo(x + sw * (k + 1), y - h - sw * k * 1.3) } c.lineTo(x + w / 2 - sw / 2, y - h - sw * n * 1.3); c.lineTo(x + w / 2 + sw / 2, y - h - sw * n * 1.3); for (let k = n - 1; k >= 0; k--) { c.lineTo(x + w - sw * (k + 1), y - h - sw * k * 1.3); c.lineTo(x + w - sw * k, y - h - sw * k * 1.3) } }
    else if (top === 'bell') { c.bezierCurveTo(x, y - h - w * 0.2, x + w * 0.3, y - h - w * 0.3, x + w * 0.35, y - h - w * 0.6); c.quadraticCurveTo(x + w / 2, y - h - w * 0.75, x + w * 0.65, y - h - w * 0.6); c.bezierCurveTo(x + w * 0.7, y - h - w * 0.3, x + w, y - h - w * 0.2, x + w, y - h) }
    else { c.lineTo(x + w * 0.2, y - h); c.quadraticCurveTo(x + w * 0.28, y - h - w * 0.2, x + w * 0.3, y - h - w * 0.55); c.lineTo(x + w * 0.7, y - h - w * 0.55); c.quadraticCurveTo(x + w * 0.72, y - h - w * 0.2, x + w * 0.8, y - h); c.lineTo(x + w, y - h) }
    c.lineTo(x + w, y); c.closePath(); c.fill()
    c.save(); c.clip(); c.strokeStyle = 'rgba(240,220,200,0.1)'; c.lineWidth = 1; for (let yy = y; yy > y - h - w; yy -= 8) { c.beginPath(); c.moveTo(x, yy); c.lineTo(x + w, yy); c.stroke() } c.restore()
    // white stone bands, windows with white frames and small panes
    c.fillStyle = 'rgba(240,232,214,0.85)'; for (let k = 1; k < 4; k++) c.fillRect(x, y - h * k / 4 - 4, w, 5)
    const cols = w > 130 ? 3 : 2, rows = Math.max(2, Math.round(h / 90))
    for (let rr = 0; rr < rows; rr++) for (let cc = 0; cc < cols; cc++) {
      const ww = w / (cols * 1.9), wh = h / rows * 0.55, wx = x + (cc + 0.5) * w / cols - ww / 2, wy = y - h + rr * h / rows + h / rows * 0.2
      if (rr === rows - 1 && cc === 0) { c.fillStyle = '#3a2418'; c.fillRect(wx, wy, ww, h / rows * 0.78); c.fillStyle = '#e8dcc0'; c.fillRect(wx - 4, wy - 6, ww + 8, 6); continue }
      c.fillStyle = '#f2eadc'; c.fillRect(wx - 4, wy - 4, ww + 8, wh + 8)
      c.fillStyle = o.lit && r() > 0.4 ? '#f2c46a' : vgrad(c, wy, wy + wh, '#5a6a7a', '#2a3440'); c.fillRect(wx, wy, ww, wh)
      c.strokeStyle = '#f2eadc'; c.lineWidth = 2; c.beginPath(); c.moveTo(wx + ww / 2, wy); c.lineTo(wx + ww / 2, wy + wh); c.moveTo(wx, wy + wh / 2); c.lineTo(wx + ww, wy + wh / 2); c.stroke()
    }
    c.fillStyle = '#3a2a1a'; c.fillRect(x + w / 2 - 3, y - h - w * 0.35, 6, 26)
  }
  function street(c, x0, x1, y, o = {}) {
    const r = rng(o.seed || 3); let x = x0
    while (x < x1) { const w = 110 + r() * 70, h = (o.h || 220) + r() * 90; gable(c, x, y, w, h, { lit: o.lit, col: o.fade ? mixCol(['#8a3a26', '#7a4430', '#9a5a3a'][(r() * 3) | 0], o.hazeCol || '#c8c0b4', o.fade) : null }); x += w + 2 }
  }
  // ---- a canal: water with ripples and the houses' colours broken up in it
  function canal(c, y, h, t, o = {}) {
    c.fillStyle = vgrad(c, y, y + h, o.top || '#5a7080', o.bot || '#2a3a46'); c.fillRect(-1400, y, 4800, h)
    const r = rng(7); for (let k = 0; k < 90; k++) { const xx = r() * 3600 - 800, yy = y + 8 + r() * h * 0.9, w = 30 + r() * 120; c.fillStyle = `rgba(${['200,120,90', '240,230,210', '150,170,190', '120,60,40'][k % 4]},${0.12 + r() * 0.15})`; c.fillRect(xx + Math.sin(t * 1.4 + k) * 8, yy, w, 3 + r() * 3) }
    c.fillStyle = '#6a6458'; c.fillRect(-1400, y - 10, 4800, 14)
  }
  // a Dutch sailing ship (fluyt)
  function ship(c, x, y, s, t, o = {}) {
    c.save(); c.translate(x, y + Math.sin(t * 1.2 + x) * 3); c.scale(s * (o.f || 1), s); c.rotate(Math.sin(t * 0.9 + x) * 0.02)
    c.fillStyle = hgrad(c, -200, 220, '#4a3020', '#6a4428', '#3a2414'); c.beginPath(); c.moveTo(-220, -60); c.quadraticCurveTo(-180, 30, -40, 40); c.lineTo(160, 40); c.quadraticCurveTo(230, 20, 250, -40); c.lineTo(180, -50); c.lineTo(-150, -60); c.lineTo(-170, -120); c.lineTo(-230, -120); c.closePath(); c.fill()
    c.fillStyle = '#c9a24a'; c.fillRect(-200, -40, 420, 6)
    c.strokeStyle = '#2a1a10'; c.lineWidth = 6; for (const mx of [-110, 30, 150]) { c.beginPath(); c.moveTo(mx, -55); c.lineTo(mx, mx === 30 ? -420 : -340); c.stroke() }
    for (const [mx, top, w] of [[-110, -330, 120], [30, -410, 150], [150, -330, 110]]) for (let k = 0; k < 2; k++) { const yy = top + k * 130, ww = w - k * 10; c.fillStyle = vgrad(c, yy, yy + 110, '#f0e8d8', '#cfc4ae'); c.beginPath(); c.moveTo(mx - ww / 2, yy); c.quadraticCurveTo(mx + Math.sin(t + k) * 4, yy + 20, mx + ww / 2, yy); c.lineTo(mx + ww / 2 - 6, yy + 110); c.quadraticCurveTo(mx + 20, yy + 130, mx - ww / 2 + 6, yy + 110); c.closePath(); c.fill() }
    c.fillStyle = '#c03a2a'; c.fillRect(30, -440, 40, 10); c.fillStyle = '#f2eee4'; c.fillRect(30, -430, 40, 10); c.fillStyle = '#2a4a8a'; c.fillRect(30, -420, 40, 10)
    c.restore()
  }
  function windmill(c, x, y, s, t) {
    c.save(); c.translate(x, y); c.scale(s, s)
    c.fillStyle = hgrad(c, -60, 60, '#6a5a4a', '#4a3a2a'); poly(c, [[-70, 0], [-45, -260], [45, -260], [70, 0]]); c.fill()
    c.fillStyle = '#3a2a1e'; poly(c, [[-55, -255], [0, -320], [55, -255]]); c.fill()
    c.translate(0, -270); c.rotate(t * 0.6)
    for (let k = 0; k < 4; k++) { c.rotate(Math.PI / 2); c.fillStyle = 'rgba(230,220,200,0.9)'; c.fillRect(6, -14, 220, 28); c.strokeStyle = '#3a2a1e'; c.lineWidth = 3; c.strokeRect(6, -14, 220, 28); c.beginPath(); for (let j = 1; j < 6; j++) { c.moveTo(6 + j * 36, -14); c.lineTo(6 + j * 36, 14) } c.stroke() }
    ell(c, 0, 0, 12, 12, 0, '#2a1a10'); c.restore()
  }
  // ---- the tavern back room: plank walls, beams, a leaded window, a fire, a long table with glasses
  function tavern(c, cam, t, o = {}) {
    layer(c, cam, 0.85, c => {
      c.fillStyle = vgrad(c, -200, 1100, '#3a2618', '#2a1a10'); c.fillRect(-900, -400, 3800, 1700)
      c.strokeStyle = 'rgba(0,0,0,0.25)'; c.lineWidth = 3; for (let x = -900; x < 2900; x += 70) { c.beginPath(); c.moveTo(x, -400); c.lineTo(x, 1300); c.stroke() }
      // leaded window with daylight (or night)
      const wx = o.winX ?? 1380
      c.fillStyle = '#1a120a'; c.fillRect(wx - 10, 140, 340, 420)
      c.fillStyle = o.night ? vgrad(c, 150, 550, '#1a2440', '#2a3a5a') : vgrad(c, 150, 550, '#e8e4d0', '#b8c0c0'); c.fillRect(wx, 150, 320, 400)
      c.strokeStyle = '#2a2018'; c.lineWidth = 3; for (let k = 1; k < 8; k++) { c.beginPath(); c.moveTo(wx + k * 40, 150); c.lineTo(wx + k * 40 - 400, 550); c.moveTo(wx + k * 40 - 320, 150); c.lineTo(wx + k * 40 + 80, 550); c.stroke() }
      c.strokeStyle = '#1a120a'; c.lineWidth = 12; c.strokeRect(wx, 150, 320, 400); c.beginPath(); c.moveTo(wx + 160, 150); c.lineTo(wx + 160, 550); c.stroke()
      // shelves with jugs and pewter
      c.fillStyle = '#4a3020'; c.fillRect(200, 300, 520, 16); c.fillRect(200, 450, 520, 16)
      const jug = (x, y, col, h) => { c.fillStyle = hgrad(c, x - 22, x + 22, shade(col, 0.2), col, shade(col, -0.35)); c.beginPath(); c.moveTo(x - 10, y - h); c.lineTo(x + 10, y - h); c.quadraticCurveTo(x + 26, y - h * 0.55, x + 18, y); c.lineTo(x - 18, y); c.quadraticCurveTo(x - 26, y - h * 0.55, x - 10, y - h); c.fill(); c.strokeStyle = shade(col, -0.3); c.lineWidth = 4; c.beginPath(); c.arc(x + 22, y - h * 0.6, 10, -1.4, 1.4); c.stroke() }
      for (let k = 0; k < 7; k++) { const jx = 230 + k * 70; jug(jx, 300, ['#8a7a6a', '#b8b0a0', '#6a4a30'][k % 3], 56 + (k % 2) * 10); if (k % 2) { c.fillStyle = '#b8b8c0'; c.fillRect(jx - 14, 410, 28, 40) } else jug(jx, 450, ['#5a4a3a', '#a8a090', '#8a5a3a'][k % 3], 48) }
      // fireplace
      if (o.fire !== false) { const fx = o.fireX ?? -300; c.fillStyle = '#5a4a3a'; c.fillRect(fx - 160, 360, 320, 460); c.fillStyle = '#140c08'; c.fillRect(fx - 110, 480, 220, 340); for (let k = 0; k < 6; k++) { const ph = (t * 3 + k * 0.7) % 1; ell(c, fx - 60 + k * 24, 780 - ph * 80, 20 * (1 - ph), 40 * (1 - ph), 0, `rgba(255,${150 + k * 15},60,${0.8 * (1 - ph)})`) } c.fillStyle = rgrad(c, fx, 740, 10, 700, 'rgba(255,150,60,0.35)', 'rgba(255,150,60,0)'); c.fillRect(fx - 700, 100, 1400, 1000) }
      // beams
      c.fillStyle = '#1e140c'; c.fillRect(-900, 60, 3800, 46); for (let x = -800; x < 2900; x += 520) c.fillRect(x, 60, 40, 1000)
    })
    layer(c, cam, 1, c => {
      c.fillStyle = vgrad(c, 860, 1200, '#4a3424', '#2a1c12'); c.fillRect(-900, 860, 3800, 600)
      c.strokeStyle = 'rgba(0,0,0,0.25)'; c.lineWidth = 2; for (let y = 880; y < 1200; y += 34) { c.beginPath(); c.moveTo(-900, y); c.lineTo(2900, y); c.stroke() }
      if (o.inner) o.inner(c)
    })
    // window light falling into the room
    if (!o.night) layer(c, cam, 0.95, c => { c.save(); c.globalCompositeOperation = 'screen'; c.fillStyle = hgrad(c, 1100, 1700, 'rgba(255,236,190,0)', 'rgba(255,236,190,0.16)', 'rgba(255,236,190,0)'); poly(c, [[(o.winX ?? 1380), 150], [(o.winX ?? 1380) + 320, 150], [(o.winX ?? 1380) + 100, 1100], [(o.winX ?? 1380) - 500, 1100]]); c.fill(); c.restore() })
  }
  // the long table in front, with glasses and a jug (drawn after the people behind it)
  function table(c, x, y, w, t, o = {}) {
    c.fillStyle = vgrad(c, y - 10, y + 40, '#6a4428', '#3a2414'); c.fillRect(x, y, w, 36); c.fillStyle = '#2a1a10'; c.fillRect(x + 20, y + 36, 26, 200); c.fillRect(x + w - 46, y + 36, 26, 200)
    const r = rng(o.seed || 5)
    for (let k = 0; k < (o.n ?? 6); k++) { const gx = x + 60 + r() * (w - 120); c.fillStyle = 'rgba(220,230,220,0.5)'; c.fillRect(gx - 9, y - 40, 18, 40); c.fillStyle = 'rgba(150,30,40,0.75)'; c.fillRect(gx - 8, y - 22, 16, 20) }
    for (let k = 0; k < (o.pipes ?? 2); k++) { const px = x + 100 + r() * (w - 200); c.strokeStyle = '#e8e0d0'; c.lineWidth = 4; c.beginPath(); c.moveTo(px, y - 3); c.lineTo(px + 60, y - 6); c.stroke(); ell(c, px + 64, y - 12, 8, 8, 0, '#e8e0d0') }
    if (o.candle) { c.fillStyle = '#f0e8d0'; c.fillRect(x + w * 0.5 - 8, y - 70, 16, 70); ell(c, x + w * 0.5, y - 84, 8, 14 + Math.sin(t * 9) * 2, 0, '#ffd890'); c.fillStyle = rgrad(c, x + w * 0.5, y - 84, 4, 300, 'rgba(255,210,130,0.3)', 'rgba(255,210,130,0)'); c.fillRect(x + w * 0.5 - 300, y - 384, 600, 600) }
  }
  // ---- outdoor Holland: sky, flat land, a windmill
  function polder(c, cam, t, o = {}) {
    layer(c, cam, 0.06, c => sky(c, o.top || '#8aa4c0', o.bot || '#e8e0d0', { horizon: 720, clouds: o.clouds ?? 7, sun: o.sun || [1500, 160, 520] }))
    layer(c, cam, 0.3, c => { c.fillStyle = vgrad(c, 700, 760, '#7a8a6a', '#6a7a5a'); c.fillRect(-1400, 700, 4800, 120); forest(c, -900, 2900, 712, 60, { kind: 'poplar', fade: 0.35, hazeCol: '#c8ccc4', gap: 0.9, rows: 1 }); if (o.mill !== false) windmill(c, o.millX ?? 300, 712, 0.3, t) })
  }
  function fields(c, cam, t, o = {}) {
    polder(c, cam, t, o)
    layer(c, cam, 0.7, c => {
      const cols = ['#d8342a', '#f2c23a', '#f4f0ea', '#c8306a', '#e8702a', '#9a3aa0']
      for (let k = 0; k < 9; k++) { const y0 = 740 + k * 26 * (1 + k * 0.3), y1 = y0 + 22 * (1 + k * 0.32); c.fillStyle = k % 2 ? '#4a6a32' : cols[k % cols.length]; poly(c, [[-1400, y0], [3400, y0 - 20], [3400, y1 - 20], [-1400, y1]]); c.fill() }
    })
  }
  // ---- charts on paper: a price line that draws itself (k 0..1); pts are 0..1 values
  function chart(c, x, y, w, h, pts, k, o = {}) {
    c.save(); c.translate(x, y)
    c.fillStyle = 'rgba(0,0,0,0.3)'; c.fillRect(-w / 2 + 10, -h / 2 + 12, w, h)
    c.fillStyle = vgrad(c, -h / 2, h / 2, '#efe4c8', '#ddd0b0'); c.fillRect(-w / 2, -h / 2, w, h)
    c.strokeStyle = 'rgba(120,90,50,0.3)'; c.lineWidth = 1.5; for (let i = 1; i < 6; i++) { c.beginPath(); c.moveTo(-w / 2 + 60, -h / 2 + i * h / 6); c.lineTo(w / 2 - 30, -h / 2 + i * h / 6); c.stroke() }
    c.strokeStyle = '#3a2a1a'; c.lineWidth = 3; c.beginPath(); c.moveTo(-w / 2 + 60, -h / 2 + 30); c.lineTo(-w / 2 + 60, h / 2 - 50); c.lineTo(w / 2 - 30, h / 2 - 50); c.stroke()
    const px = i => -w / 2 + 60 + (w - 90) * i / (pts.length - 1), py = v => h / 2 - 50 - (h - 90) * v
    const n = (pts.length - 1) * clamp(k), whole = Math.floor(n)
    c.strokeStyle = o.col || '#8a2a1e'; c.lineWidth = 6; c.lineJoin = 'round'; c.beginPath(); c.moveTo(px(0), py(pts[0]))
    for (let i = 1; i <= whole; i++) c.lineTo(px(i), py(pts[i]))
    if (whole < pts.length - 1) { const f = n - whole; c.lineTo(lerp(px(whole), px(whole + 1), f), lerp(py(pts[whole]), py(pts[whole + 1]), f)) }
    c.stroke()
    if (o.labels) o.labels.forEach(([i, s]) => { if (i <= n + 0.01) text(c, s, px(i), py(pts[i]) - 30, 26, '#3a2a1a', { italic: true }) })
    if (o.xlabels) o.xlabels.forEach(([i, s]) => text(c, s, px(i), h / 2 - 24, 24, '#3a2a1a'))
    c.restore()
  }
  const shotOf = (t, list) => { let s = list[0]; for (const L of list) if (t >= L[0]) s = L; const i = list.indexOf(s), t1 = (list[i + 1] || [1e9])[0]; return { name: s[1], t0: s[0], t1, u: clamp((t - s[0]) / (t1 - s[0])) } }
  return { tulip, bulb, gable, street, canal, ship, windmill, tavern, table, polder, fields, chart, shotOf, BUYERS }
})()
