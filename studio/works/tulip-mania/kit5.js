// kit5.js: cut-paper pieces for the Tulip Mania film, on top of lib.js and kit3.js.
// Ink figures on paper. The one red is the flame in a broken tulip; the one gold is money.
(function () {
  const { clamp, lerp, rng, noise, mix, prog } = K
  const { W, H, C, person, glow, text, F, hatch, layer } = L
  const INK = C.ink, RED = '#a8321f', GOLD = C.gold

  // ---------- people of 1637: wide brim hat, a ruff at the neck, a short cape ----------
  function dutchman(c, x, y, h, o = {}) {
    const face = o.face || 1, col = o.col || INK, s = h / 100
    person(c, x, y, h, { hat: 'none', face, col, walk: o.walk, stride: o.stride, arm: o.arm, armRot: o.armRot, hold: o.hold, seated: o.seated, bulk: o.bulk || 1.05, belly: o.belly, lean: o.lean })
    const st = o.stride ?? 0, bob = -Math.abs(Math.cos(o.walk || 0)) * 1.6 * st
    c.save(); c.translate(x, y); c.scale(s * face, s); c.translate(0, bob); c.rotate(o.lean || 0); c.fillStyle = col
    // the hat: a tall crown and a wide brim
    c.beginPath(); c.moveTo(-6, -97); c.lineTo(-5, -108); c.quadraticCurveTo(2, -111, 9, -108); c.lineTo(10, -97); c.closePath(); c.fill()
    c.beginPath(); c.ellipse(2, -97, 16, 3.2, -0.04, 0, 7); c.fill()
    // the ruff: a pale disc under the chin
    c.fillStyle = o.ruff || C.paper; c.beginPath(); c.ellipse(1.5, -82.5, 10, 3.6, 0, 0, 7); c.fill()
    c.strokeStyle = col; c.lineWidth = 0.8; for (let k = -8; k <= 8; k += 3) { c.beginPath(); c.moveTo(1.5 + k, -85.5); c.lineTo(1.5 + k * 1.1, -79.5); c.stroke() }
    if (o.cape) { c.fillStyle = col; c.beginPath(); c.moveTo(-11, -80); c.quadraticCurveTo(-20, -60, -16, -44); c.lineTo(-6, -46); c.closePath(); c.fill() }
    c.restore()
  }
  function goodwife(c, x, y, h, o = {}) {
    person(c, x, y, h, { lady: true, col: o.col || INK, face: o.face || 1 })
    const s = h / 100; c.save(); c.translate(x, y); c.scale(s * (o.face || 1), s)
    c.fillStyle = C.paper; c.beginPath(); c.ellipse(1, -95, 9, 6, 0, Math.PI, 0); c.fill(); c.beginPath(); c.ellipse(1, -81, 10, 3.4, 0, 0, 7); c.fill(); c.restore()
  }

  // ---------- the flower ----------
  // tulip: (x, y) where the stem meets the ground; s scale (1 = about 260 px tall). o: col (petal), broken (flames 0..1), open 0..1, sway
  function tulip(c, x, y, s, o = {}) {
    const t = o.t || 0, sw = (o.sway ?? 1) * Math.sin(t * 1.3 + x * 0.01) * 0.04, col = o.col || C.ink, bl = o.broken || 0, op = o.open ?? 0.3
    c.save(); c.translate(x, y); c.scale(s, s); c.rotate(sw)
    c.strokeStyle = o.stem || INK; c.lineWidth = 6; c.lineCap = 'round'; c.beginPath(); c.moveTo(0, 0); c.quadraticCurveTo(6, -110, 0, -190); c.stroke()
    c.fillStyle = o.stem || INK
    c.beginPath(); c.moveTo(0, -10); c.quadraticCurveTo(-58, -60, -38, -150); c.quadraticCurveTo(-26, -80, 2, -40); c.closePath(); c.fill()
    c.beginPath(); c.moveTo(2, -20); c.quadraticCurveTo(54, -70, 46, -128); c.quadraticCurveTo(28, -78, 0, -55); c.closePath(); c.fill()
    // the cup: three petals, opening a little
    c.translate(0, -190)
    const cup = (k) => { const a = (k - 1) * (0.32 + op * 0.3); c.save(); c.rotate(a); c.beginPath(); c.moveTo(-4, 6); c.bezierCurveTo(-38, -10, -34, -70, 0, -86); c.bezierCurveTo(34, -70, 38, -10, 4, 6); c.closePath(); c.restore() }
    for (const k of [0, 2, 1]) {
      cup(k); c.fillStyle = bl > 0 ? (o.ground || '#f1e7d2') : col; c.fill()
      if (bl > 0) {
        c.save(); cup(k); c.clip(); c.fillStyle = o.flame || RED; c.globalAlpha = bl
        const r = rng((o.seed || 1) * 7 + k)
        for (let f = 0; f < 6; f++) { const fx = -26 + f * 10 + r() * 4, wd = 3 + r() * 5; c.beginPath(); c.moveTo(fx, 8); c.quadraticCurveTo(fx - 6 + r() * 12, -40, fx + (r() - 0.5) * 8, -86); c.lineTo(fx + wd, -86); c.quadraticCurveTo(fx + wd - 6 + r() * 12, -40, fx + wd, 8); c.closePath(); c.fill() }
        c.restore()
        cup(k); c.strokeStyle = INK; c.lineWidth = 2.5; c.stroke()
      }
    }
    c.restore()
  }
  // a bulb with roots, (x, y) at its base
  function bulb(c, x, y, s, o = {}) {
    c.save(); c.translate(x, y); c.scale(s, s); c.fillStyle = o.col || '#8a6a44'; c.strokeStyle = INK
    c.beginPath(); c.moveTo(0, -120); c.bezierCurveTo(14, -100, 62, -70, 54, -26); c.bezierCurveTo(48, 4, -48, 4, -54, -26); c.bezierCurveTo(-62, -70, -14, -100, 0, -120); c.closePath(); c.fill()
    c.lineWidth = 2.5; c.globalAlpha = 0.5; for (const k of [-24, 0, 24]) { c.beginPath(); c.moveTo(k * 0.3, -112); c.quadraticCurveTo(k * 1.6, -50, k, 0); c.stroke() } c.globalAlpha = 1
    c.lineWidth = 2; for (let k = 0; k < 9; k++) { const rx = -24 + k * 6; c.beginPath(); c.moveTo(rx, 0); c.quadraticCurveTo(rx + (k - 4) * 3, 14, rx + (k - 4) * 5, 26 + (k % 3) * 6); c.stroke() }
    if (o.label) text(c, o.label, 0, 70, F.headI(30, 700), INK)
    c.restore()
  }

  // ---------- canal houses: stepped gables in a row; (x0, y) ground at the left ----------
  function gables(c, x0, y, n, o = {}) {
    const r = rng(o.seed || 16), col = o.col || INK, win = o.win || C.paper2
    let x = x0
    for (let k = 0; k < n; k++) {
      const w = 140 + r() * 60, h = 300 + r() * 160, steps = 3 + Math.floor(r() * 2), st = w / (steps * 2 + 2)
      const sw = w / 2 / (steps + 1), sh = 34, L = [[x, y], [x, y - h]]
      for (let i = 0; i < steps; i++) { L.push([x + sw * i, y - h - sh * (i + 1)]); L.push([x + sw * (i + 1), y - h - sh * (i + 1)]) }
      L.push([x + w / 2 - sw * 0.6, y - h - sh * (steps + 1.4)])
      c.fillStyle = col; c.beginPath(); L.forEach(([px, py], k) => k ? c.lineTo(px, py) : c.moveTo(px, py))
      for (let k = L.length - 1; k >= 0; k--) c.lineTo(2 * x + w - L[k][0], L[k][1]); c.closePath(); c.fill()
      c.fillStyle = typeof win === 'function' ? win(k) : win
      for (let fy = 0; fy < 3; fy++) for (let fx = 0; fx < 2; fx++) c.fillRect(x + w * (0.22 + fx * 0.36), y - h + 30 + fy * (h - 90) / 3, w * 0.2, (h - 90) / 3 * 0.55)
      x += w + 6
    }
  }
  // water in a canal: a strip with ripple lines
  function canal(c, t, x0, x1, y, h, o = {}) {
    c.save(); c.fillStyle = o.col || '#6b7a80'; c.fillRect(x0, y, x1 - x0, h)
    c.strokeStyle = 'rgba(238,226,200,0.3)'; c.lineWidth = 2; const r = rng(3)
    for (let k = 0; k < 40; k++) { const yy = y + 8 + r() * (h - 16), xx = x0 + ((r() * (x1 - x0) + t * 12) % (x1 - x0)); c.beginPath(); c.moveTo(xx, yy); c.lineTo(xx + 30 + r() * 40, yy); c.stroke() }
    c.restore()
  }

  // ---------- the tavern back room ----------
  function tavern(c, t, o = {}) {
    c.fillStyle = mix('#2b211a', '#b9a07a', o.light ?? 0.6); c.fillRect(0, 0, W, H)
    c.fillStyle = mix('#1a140f', '#7d6648', o.light ?? 0.6); for (let k = 0; k < 5; k++) c.fillRect(k * 430 - 40, 0, 46, 760)
    c.fillRect(0, 120, W, 34); c.fillRect(0, 760, W, 320)
    // a window with leaded panes
    c.fillStyle = 'rgba(236,224,190,0.65)'; c.fillRect(1500, 220, 220, 300); c.strokeStyle = mix('#1a140f', '#7d6648', o.light ?? 0.6); c.lineWidth = 4
    for (let k = 1; k < 4; k++) { c.beginPath(); c.moveTo(1500 + k * 55, 220); c.lineTo(1500 + k * 55, 520); c.stroke() } for (let k = 1; k < 5; k++) { c.beginPath(); c.moveTo(1500, 220 + k * 60); c.lineTo(1720, 220 + k * 60); c.stroke() }
    if (o.candles !== false) for (const [x, y] of [[520, 700], [1250, 700]]) { glow(c, x, y - 40, 260, '246,199,112', 0.45 + 0.05 * noise(t * 5, x)); c.fillStyle = C.paper; c.fillRect(x - 6, y - 40, 12, 40); c.fillStyle = C.gold2; c.beginPath(); c.ellipse(x, y - 50 + noise(t * 7, x) * 2, 5, 10, 0, 0, 7); c.fill() }
  }
  function table(c, x, y, w, col = INK) { c.fillStyle = col; c.fillRect(x - w / 2, y - 10, w, 16); c.fillRect(x - w / 2 + 20, y, 14, 120); c.fillRect(x + w / 2 - 34, y, 14, 120) }
  function glass(c, x, y, s = 1, col = INK) { c.save(); c.translate(x, y); c.scale(s, s); c.fillStyle = col; c.beginPath(); c.moveTo(-14, -44); c.lineTo(14, -44); c.lineTo(5, -14); c.lineTo(2, 0); c.lineTo(10, 2); c.lineTo(-10, 2); c.lineTo(-2, 0); c.lineTo(-5, -14); c.closePath(); c.fill(); c.fillStyle = RED; c.globalAlpha = 0.85; c.beginPath(); c.moveTo(-11, -36); c.lineTo(11, -36); c.lineTo(5, -18); c.lineTo(-5, -18); c.closePath(); c.fill(); c.restore() }

  // ---------- paper: the promise ----------
  function note(c, x, y, s, o = {}) {
    c.save(); c.translate(x, y); c.rotate(o.rot || 0); c.scale(s, s)
    if (o.half) { c.beginPath(); const sg = o.half === 'left' ? -1 : 1; c.moveTo(-10, -110); for (let i = 0; i < 10; i++) c.lineTo(-10 + (i % 2 ? 12 : -12), -100 + i * 22); c.lineTo(-10, 120); c.lineTo(400 * sg, 120); c.lineTo(400 * sg, -120); c.closePath(); c.clip() }
    c.fillStyle = o.col || '#f3ead6'; c.fillRect(-150, -95, 300, 190); c.strokeStyle = INK; c.lineWidth = 2; c.strokeRect(-150, -95, 300, 190)
    c.globalAlpha = 0.7; c.lineWidth = 2.2; const r = rng(o.seed || 5)
    for (let k = 0; k < 6; k++) { c.beginPath(); let px = -128; c.moveTo(px, -60 + k * 24); while (px < 120 - (k === 5 ? 120 : 0)) { px += 10 + r() * 8; c.lineTo(px, -60 + k * 24 + (r() - 0.5) * 5) } c.stroke() }
    c.globalAlpha = 1; if (o.name) text(c, o.name, 0, -66, F.headI(26, 700), INK)
    if (o.price) text(c, o.price, 60, 76, F.head(30, 800), GOLD)
    c.fillStyle = RED; c.beginPath(); c.arc(-110, 66, 16, 0, 7); c.fill()
    c.restore()
  }
  // a price line drawn across a chart; pts: [[0..1 x, 0..1 y]], p: how much is drawn
  function chart(c, x, y, w, h, pts, p, o = {}) {
    c.save(); c.strokeStyle = INK; c.lineWidth = 3; c.beginPath(); c.moveTo(x, y - h); c.lineTo(x, y); c.lineTo(x + w, y); c.stroke()
    const n = Math.max(2, Math.floor(clamp(p) * (pts.length - 1)) + 1), fr = clamp(p) * (pts.length - 1) - (n - 2)
    c.strokeStyle = o.col || RED; c.lineWidth = o.lw || 8; c.lineJoin = 'round'; c.beginPath(); c.moveTo(x + pts[0][0] * w, y - pts[0][1] * h)
    for (let k = 1; k < n; k++) { const a = pts[k - 1], b = pts[k], f = k === n - 1 ? clamp(fr) : 1; c.lineTo(x + lerp(a[0], b[0], f) * w, y - lerp(a[1], b[1], f) * h) }
    c.stroke(); c.restore()
  }

  // ---------- farm goods for the pamphlet ----------
  function beast(c, x, y, s, kind, col = INK) {
    c.save(); c.translate(x, y); c.scale(s, s); c.fillStyle = col
    const legs = (xs, l) => xs.forEach(lx => c.fillRect(lx, -l, 7, l))
    if (kind === 'ox') { c.beginPath(); c.ellipse(0, -70, 70, 34, 0, 0, 7); c.fill(); legs([-55, -38, 34, 50], 44); c.beginPath(); c.ellipse(78, -80, 22, 16, 0.3, 0, 7); c.fill(); c.fillRect(72, -104, 4, 14); c.fillRect(86, -102, 4, 12); c.fillRect(-74, -78, 6, 40) }
    if (kind === 'pig') { c.beginPath(); c.ellipse(0, -40, 48, 28, 0, 0, 7); c.fill(); legs([-34, -20, 18, 30], 18); c.beginPath(); c.ellipse(50, -44, 16, 14, 0, 0, 7); c.fill(); c.fillRect(62, -46, 10, 9); c.beginPath(); c.arc(-50, -48, 7, 0, 5); c.lineWidth = 3; c.strokeStyle = col; c.stroke() }
    if (kind === 'sheep') { for (let k = 0; k < 7; k++) { c.beginPath(); c.arc(-30 + k * 10, -48 + (k % 2) * 8, 18, 0, 7); c.fill() } legs([-26, -14, 14, 26], 28); c.beginPath(); c.ellipse(46, -54, 12, 9, 0.4, 0, 7); c.fill() }
    if (kind === 'sack') { c.beginPath(); c.moveTo(-30, 0); c.quadraticCurveTo(-40, -50, -14, -70); c.lineTo(-18, -84); c.lineTo(18, -84); c.lineTo(14, -70); c.quadraticCurveTo(40, -50, 30, 0); c.closePath(); c.fill() }
    if (kind === 'barrel') { c.beginPath(); c.moveTo(-26, 0); c.quadraticCurveTo(-36, -40, -26, -80); c.lineTo(26, -80); c.quadraticCurveTo(36, -40, 26, 0); c.closePath(); c.fill(); c.fillStyle = C.paper3; c.fillRect(-32, -60, 64, 4); c.fillRect(-32, -22, 64, 4) }
    if (kind === 'cheese') { c.beginPath(); c.ellipse(0, -18, 42, 14, 0, 0, 7); c.fill(); c.fillRect(-42, -34, 84, 18); c.fillStyle = GOLD; c.beginPath(); c.ellipse(0, -34, 42, 14, 0, 0, 7); c.fill() }
    if (kind === 'bed') { c.fillRect(-70, -40, 140, 20); c.fillRect(-70, -90, 12, 90); c.fillRect(58, -64, 12, 64); c.fillStyle = C.paper2; c.fillRect(-58, -54, 116, 14) }
    if (kind === 'coat') { c.beginPath(); c.moveTo(-30, -90); c.lineTo(30, -90); c.lineTo(46, 0); c.lineTo(-46, 0); c.closePath(); c.fill(); c.fillRect(-52, -88, 14, 54); c.fillRect(38, -88, 14, 54) }
    if (kind === 'cup') { c.fillStyle = '#9aa3a6'; c.beginPath(); c.moveTo(-24, -70); c.lineTo(24, -70); c.lineTo(10, -30); c.lineTo(6, -6); c.lineTo(18, 0); c.lineTo(-18, 0); c.lineTo(-6, -6); c.lineTo(-10, -30); c.closePath(); c.fill() }
    c.restore()
  }
  // a coin stack in gold
  function guilders(c, x, y, n, s = 1) { c.save(); c.fillStyle = GOLD; c.strokeStyle = '#7a5a20'; c.lineWidth = 1.5; for (let k = 0; k < n; k++) { c.beginPath(); c.ellipse(x, y - k * 7 * s, 26 * s, 8 * s, 0, 0, 7); c.fill(); c.stroke() } c.restore() }
  // a book standing open
  function book(c, x, y, s, o = {}) { c.save(); c.translate(x, y); c.scale(s, s); c.fillStyle = INK; c.fillRect(-130, -180, 260, 190); c.fillStyle = '#f1e7d2'; c.fillRect(-122, -172, 118, 174); c.fillRect(4, -172, 118, 174); if (o.title) { o.title.forEach((l, i) => text(c, l, -63, -130 + i * 26, F.head(13, 800), INK)) } c.restore() }

  window.TU = { INK, RED, GOLD, dutchman, goodwife, tulip, bulb, gables, canal, tavern, table, glass, note, chart, beast, guilders, book }
})()
