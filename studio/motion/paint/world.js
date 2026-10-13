// paint/world.js: places and things for Style B. Trees, houses, hills, water, paper, maps, trains.
// Heavy repeated things (trees, houses at a distance) are cached as sprites so a frame stays fast.
(function (PK) {
  const { lerp, rng, ell, poly, smooth, shade, mixCol, vgrad, hgrad, rgrad, sprite, drawSprite, tuft, text } = PK

  // ---- trees: 'deodar' (tall Himalayan cedar), 'pine', 'oak' (broadleaf), 'palm', 'poplar'. Drawn from a cached sprite.
  function tree(c, x, y, h, kind = 'deodar', o = {}) {
    const haze = o.fade || 0, hc = o.hazeCol || '#b9b0a2', key = `tree:${kind}:${haze.toFixed(2)}:${hc}:${o.seed || 0}`
    const S = 400, s = sprite(key, 300, S, g => drawTree(g, 150, S, S * 0.96, kind, haze, hc, o.seed || 0))
    const k = h / (S * 0.96), sway = o.t ? Math.sin(o.t * 0.8 + x * 0.01) * 0.02 : 0
    drawSprite(c, s, x - 150 * k, y - S * k, k, k, sway)
  }
  function drawTree(g, x, y, h, kind, haze, hc, seed) {
    const col = v => haze ? mixCol(v, hc, haze) : v, r = rng(seed + 7)
    g.fillStyle = col('#3a2a1c'); g.fillRect(x - h * 0.02, y - h * 0.5, h * 0.04, h * 0.5)
    if (kind === 'deodar' || kind === 'pine') {
      const tiers = kind === 'deodar' ? 9 : 6
      for (let k = 0; k < tiers; k++) {
        const u = k / tiers, yy = y - h * 0.12 - u * h * 0.86, w = h * (kind === 'deodar' ? 0.3 : 0.22) * (1 - u * 0.85) * (0.85 + r() * 0.3)
        g.fillStyle = vgrad(g, yy - h * 0.08, yy + h * 0.04, col(shade('#2f4a3a', 0.12)), col('#2a4034'), col('#1c2c24'))
        g.beginPath(); g.moveTo(x - w, yy + h * 0.03); g.quadraticCurveTo(x - w * 0.3, yy - h * 0.02, x, yy - h * 0.09); g.quadraticCurveTo(x + w * 0.3, yy - h * 0.02, x + w, yy + h * 0.03); g.quadraticCurveTo(x, yy + h * 0.01, x - w, yy + h * 0.03); g.fill()
      }
    } else if (kind === 'oak' || kind === 'bush') {
      const top = kind === 'bush' ? y - h * 0.5 : y - h * 0.55, R = kind === 'bush' ? h * 0.45 : h * 0.32
      for (let k = 0; k < 9; k++) { const a = r() * Math.PI * 2, d = r() * R * 0.6; ell(g, x + Math.cos(a) * d * 1.3, top + Math.sin(a) * d * 0.8, R * (0.45 + r() * 0.25), R * (0.38 + r() * 0.2), 0, col(k < 4 ? '#24382a' : k < 7 ? '#2f4a34' : '#3d5a3c')) }
    } else if (kind === 'poplar') {
      g.fillStyle = vgrad(g, y - h, y, col('#4a6a3a'), col('#2a4024')); ell(g, x, y - h * 0.55, h * 0.12, h * 0.45, 0); g.fill()
    } else if (kind === 'palm') {
      g.strokeStyle = col('#5a4a32'); g.lineWidth = h * 0.035; g.beginPath(); g.moveTo(x, y); g.quadraticCurveTo(x + h * 0.08, y - h * 0.5, x + h * 0.04, y - h * 0.9); g.stroke()
      for (let k = 0; k < 7; k++) { const a = -Math.PI / 2 + (k - 3) * 0.45; g.strokeStyle = col('#2f5a34'); g.lineWidth = h * 0.03; g.beginPath(); g.moveTo(x + h * 0.04, y - h * 0.9); g.quadraticCurveTo(x + h * 0.04 + Math.cos(a) * h * 0.2, y - h * 0.9 + Math.sin(a) * h * 0.1 - h * 0.05, x + h * 0.04 + Math.cos(a) * h * 0.32, y - h * 0.9 + Math.sin(a) * h * 0.1 + h * 0.08); g.stroke() }
    }
  }
  // a forest band: many trees along a line, back rows hazier
  function forest(c, x0, x1, y, h, o = {}) {
    const r = rng(o.seed || 11), rows = o.rows || 2
    for (let row = rows - 1; row >= 0; row--) {
      const fade = (o.fade || 0) + row * 0.18
      for (let x = x0 + r() * 40; x < x1; x += h * (o.gap || 0.42) * (0.6 + r() * 0.9)) { const kind = o.kind || (r() < (o.mix ?? 0.25) ? 'oak' : 'deodar'); tree(c, x, y - row * h * 0.18 + r() * 14, h * (0.6 + r() * 0.55) * (1 - row * 0.15) * (kind === 'oak' ? 0.7 : 1), kind, { fade, hazeCol: o.hazeCol, seed: (r() * 4) | 0, t: o.t }) }
    }
  }

  // ---- mountains with snow (the Himalaya on the horizon)
  function snowPeaks(c, y, o = {}) {
    const r = rng(o.seed || 2), pts = [[-900, y + 300]]
    for (let x = -900; x <= 2900; x += 120 + r() * 120) { const big = r() > 0.45; pts.push([x, y - (big ? 120 + r() * (o.h || 260) : 40 + r() * 80)]) }
    pts.push([2900, y + 300])
    c.fillStyle = vgrad(c, y - 300, y + 200, o.top || '#c6cfda', o.bot || '#8796a8'); poly(c, pts); c.fill()
    c.save(); poly(c, pts); c.clip()
    // the shadowed (right-hand) face of every slope, then snow on the high ground
    for (let i = 1; i < pts.length - 2; i++) { const [ax, ay] = pts[i], [bx, by] = pts[i + 1]; if (by > ay) { c.fillStyle = 'rgba(40,50,70,0.22)'; c.beginPath(); c.moveTo(ax, ay); c.lineTo(bx, by); c.lineTo(bx + (bx - ax) * 0.2, by + 500); c.lineTo(ax, ay + 500); c.closePath(); c.fill() } }
    for (let i = 1; i < pts.length - 1; i++) { const [px, py] = pts[i]; if (py < y - 110) { const d = (y - 110 - py) * 0.6 + 30; c.fillStyle = 'rgba(248,250,255,0.85)'; c.beginPath(); c.moveTo(px, py); c.lineTo(px - d * 0.9, py + d); c.lineTo(px - d * 0.45, py + d * 0.75); c.lineTo(px - d * 0.1, py + d * 1.05); c.lineTo(px + d * 0.35, py + d * 0.7); c.lineTo(px + d * 0.8, py + d * 0.95); c.closePath(); c.fill(); c.fillStyle = 'rgba(150,170,200,0.35)'; c.beginPath(); c.moveTo(px, py); c.lineTo(px + d * 0.8, py + d * 0.95); c.lineTo(px + d * 0.35, py + d * 0.7); c.closePath(); c.fill() } }
    c.restore()
  }
  // terraced fields on a slope: curved strips stepping down
  function terraces(c, x0, y0, w, n, o = {}) {
    const step = o.step || 34, col = o.col || '#7d8a4a'
    for (let k = 0; k < n; k++) {
      const y = y0 + k * step, xs = x0 + k * (o.shift || 26), ww = w - k * (o.shrink || 30)
      c.fillStyle = vgrad(c, y - step, y + 4, shade(col, 0.12 - k * 0.02), shade(col, -0.05 - k * 0.02))
      c.beginPath(); c.moveTo(xs, y); c.quadraticCurveTo(xs + ww * 0.5, y - step * 0.6, xs + ww, y); c.lineTo(xs + ww, y + step * 0.2); c.quadraticCurveTo(xs + ww * 0.5, y - step * 0.35, xs, y + step * 0.2); c.closePath(); c.fill()
      c.strokeStyle = 'rgba(60,40,20,0.35)'; c.lineWidth = 3; c.beginPath(); c.moveTo(xs, y + step * 0.2); c.quadraticCurveTo(xs + ww * 0.5, y - step * 0.35, xs + ww, y + step * 0.2); c.stroke()
    }
  }
  // a Kumaon stone house with a slate roof (or 'dutch' brick gable, 'boston' brick block via other kits)
  function house(c, x, y, w, h, o = {}) {
    const col = o.col || '#b5a48a', roof = o.roof || '#5a5a62', r = rng((x * 7 + y) | 0)
    // stone walls with courses and a few picked-out stones
    c.fillStyle = hgrad(c, x, x + w, shade(col, 0.12), col, shade(col, -0.28)); c.fillRect(x, y - h, w, h)
    c.save(); c.beginPath(); c.rect(x, y - h, w, h); c.clip()
    c.strokeStyle = 'rgba(60,50,40,0.28)'; c.lineWidth = 1.5
    for (let k = 1; k < 9; k++) { const yy = y - h * k / 9; c.beginPath(); c.moveTo(x, yy); c.lineTo(x + w, yy); c.stroke(); for (let j = 0; j < 5; j++) { const xx = x + ((j + (k % 2) * 0.5) / 5) * w; c.beginPath(); c.moveTo(xx, yy); c.lineTo(xx, yy + h / 9); c.stroke() } }
    for (let k = 0; k < 8; k++) { c.fillStyle = `rgba(${r() > 0.5 ? '255,240,220' : '40,30,20'},0.12)`; c.fillRect(x + r() * w, y - r() * h, w * 0.12, h * 0.07) }
    c.fillStyle = 'rgba(0,0,0,0.25)'; c.fillRect(x, y - h, w, h * 0.12)
    c.restore()
    // wooden door and a small shuttered window, carved lintel
    const lit = o.lit
    c.fillStyle = '#4a3020'; c.fillRect(x + w * 0.16, y - h * 0.64, w * 0.22, h * 0.64)
    c.fillStyle = lit ? '#f2c46a' : '#2a1d14'; c.fillRect(x + w * 0.19, y - h * 0.6, w * 0.16, h * 0.6)
    c.fillStyle = '#5a3a24'; c.fillRect(x + w * 0.58, y - h * 0.72, w * 0.22, h * 0.26)
    c.fillStyle = lit ? '#f2c46a' : '#2a1d14'; c.fillRect(x + w * 0.61, y - h * 0.69, w * 0.16, h * 0.2)
    c.fillStyle = '#6a4a2a'; c.fillRect(x + w * 0.12, y - h * 0.7, w * 0.3, h * 0.06)
    // slate roof with overhang, courses of slate, a shadow under the eaves
    const ov = w * 0.14, peak = y - h - w * 0.32
    c.fillStyle = vgrad(c, peak, y - h, shade(roof, 0.18), roof, shade(roof, -0.2)); poly(c, [[x - ov, y - h + 4], [x + w * 0.5, peak], [x + w + ov, y - h + 4]]); c.fill()
    c.save(); poly(c, [[x - ov, y - h + 4], [x + w * 0.5, peak], [x + w + ov, y - h + 4]]); c.clip(); c.strokeStyle = 'rgba(20,20,26,0.3)'; c.lineWidth = 1.5
    for (let k = 1; k < 5; k++) { const yy = peak + (y - h - peak) * k / 5; c.beginPath(); c.moveTo(x - ov, yy); c.lineTo(x + w + ov, yy); c.stroke() } c.restore()
    c.strokeStyle = shade(roof, -0.35); c.lineWidth = 4; c.beginPath(); c.moveTo(x - ov, y - h + 4); c.lineTo(x + w * 0.5, peak); c.lineTo(x + w + ov, y - h + 4); c.stroke()
    if (lit) { c.fillStyle = rgrad(c, x + w * 0.27, y - h * 0.3, 2, w * 0.7, 'rgba(255,200,110,0.4)', 'rgba(255,200,110,0)'); c.fillRect(x - w * 0.4, y - h * 1.2, w * 1.4, h * 1.5) }
    if (o.smoke) { for (let k = 0; k < 6; k++) { const ph = ((o.smoke * 0.3 + k / 6) % 1); ell(c, x + w * 0.7 + ph * 40, peak - 10 - ph * 120, 10 + ph * 26, 8 + ph * 18, 0, `rgba(220,214,204,${0.4 * (1 - ph)})`) } }
  }
  // a river running across the floor of a valley
  function river(c, pts, w, t, o = {}) {
    c.lineCap = 'round'; c.lineJoin = 'round'
    c.strokeStyle = o.bank || '#6a5a44'; c.lineWidth = w + 18; c.beginPath(); c.moveTo(...pts[0]); for (const p of pts.slice(1)) c.lineTo(...p); c.stroke()
    c.strokeStyle = o.col || '#6f8a96'; c.lineWidth = w; c.stroke()
    c.strokeStyle = 'rgba(240,248,255,0.35)'; c.lineWidth = 2; c.setLineDash([18, 40]); c.lineDashOffset = -t * 60; c.stroke(); c.setLineDash([])
  }
  // brush: a dense clump of bushes and grass (where a tiger hides)
  function brush(c, x, y, w, h, t = 0, o = {}) {
    const r = rng(o.seed || 31)
    for (let k = 0; k < Math.max(3, w / 40); k++) ell(c, x + r() * w, y - h * 0.35 - r() * h * 0.3, h * (0.3 + r() * 0.25), h * (0.25 + r() * 0.2), 0, mixCol(['#24382a', '#2f4a34', '#3d5a3c'][k % 3], o.hazeCol || '#b9b0a2', o.fade || 0))
    for (let xx = x; xx < x + w; xx += 26 + r() * 30) tuft(c, xx, y, h * (0.6 + r() * 0.5), mixCol(r() > 0.5 ? '#3f5a33' : '#2c4224', o.hazeCol || '#b9b0a2', o.fade || 0), Math.sin(t * 1.4 + xx * 0.05) * 0.12 + (o.rustle || 0) * Math.sin(t * 30 + xx), 6, xx | 0)
  }
  // ---- paper: a sheet with lines of text (notices, letters, contracts, pamphlets), painted with a soft shadow
  function paper(c, x, y, w, h, lines = [], o = {}) {
    c.save(); c.translate(x, y); c.rotate(o.rot || 0)
    if (window.__vertical) { const m = c.getTransform(), k = Math.min(1, 580 / (w * Math.hypot(m.a, m.b))); c.scale(k, k) }
    c.fillStyle = 'rgba(0,0,0,0.3)'; c.fillRect(-w / 2 + 8, -h / 2 + 10, w, h)
    c.fillStyle = vgrad(c, -h / 2, h / 2, o.col || '#efe4c8', shade(o.col || '#efe4c8', -0.12)); c.fillRect(-w / 2, -h / 2, w, h)
    c.strokeStyle = 'rgba(120,90,50,0.35)'; c.lineWidth = 2; c.strokeRect(-w / 2 + 10, -h / 2 + 10, w - 20, h - 20)
    let yy = -h / 2 + (o.top || 50)
    for (const L of lines) { const [s, size = 30, col = '#3a2a1a', o2 = {}] = Array.isArray(L) ? L : [L]; if (s) text(c, s, 0, yy, size, col, Object.assign({ font: o.font || 'Playfair', weight: 700 }, o2)); yy += size * 1.35 }
    c.restore()
  }
  // a painted map: parchment, a coast or border line, places, and a path that draws itself (k 0..1)
  function map(c, x, y, w, h, o = {}) {
    c.save(); c.translate(x, y)
    c.fillStyle = 'rgba(0,0,0,0.35)'; c.fillRect(-w / 2 + 10, -h / 2 + 14, w, h)
    c.fillStyle = rgrad(c, 0, 0, 10, w * 0.7, '#efe2c2', '#d8c49a', '#b8a272'); c.fillRect(-w / 2, -h / 2, w, h)
    if (o.draw) o.draw(c, w, h)
    c.strokeStyle = 'rgba(90,60,30,0.4)'; c.lineWidth = 3; c.strokeRect(-w / 2 + 14, -h / 2 + 14, w - 28, h - 28)
    c.restore()
  }
  function pathLine(c, pts, k, col = '#8a2a1e', w = 6, dash = [16, 12]) {
    if (k <= 0) return
    const segs = []; let tot = 0; for (let i = 1; i < pts.length; i++) { const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); segs.push(d); tot += d }
    let left = tot * Math.min(1, k); c.strokeStyle = col; c.lineWidth = w; c.lineCap = 'round'; c.setLineDash(dash); c.beginPath(); c.moveTo(...pts[0])
    let end = pts[0]
    for (let i = 1; i < pts.length && left > 0; i++) { const d = segs[i - 1], u = Math.min(1, left / d); end = [lerp(pts[i - 1][0], pts[i][0], u), lerp(pts[i - 1][1], pts[i][1], u)]; c.lineTo(...end); left -= d }
    c.stroke(); c.setLineDash([]); return end
  }
  // ---- a steam train (Kumaon railway / 1900s), moving by x
  function train(c, x, y, s, t, o = {}) {
    c.save(); c.translate(x, y); c.scale(s * (o.f || 1), s)
    const body = '#1f2226', trim = '#7a2a22'
    // carriages
    for (let k = 1; k <= (o.cars ?? 3); k++) { const cx = -k * 300; c.fillStyle = hgrad(c, cx, cx + 280, shade('#5a2a22', 0.1), '#5a2a22', shade('#5a2a22', -0.3)); c.fillRect(cx, -150, 280, 110); c.fillStyle = '#e8d8a8'; for (let w = 0; w < 5; w++) c.fillRect(cx + 20 + w * 52, -130, 34, 36); c.fillStyle = '#2a1d14'; c.fillRect(cx - 10, -160, 300, 14); wheel(c, cx + 50, -24, 24, t); wheel(c, cx + 230, -24, 24, t) }
    // engine
    c.fillStyle = hgrad(c, 0, 0, body, body); c.fillStyle = vgrad(c, -180, -40, shade(body, 0.25), body); c.fillRect(0, -130, 210, 90)
    ell(c, 210, -85, 18, 45, 0, shade(body, 0.1)); c.fillRect(150, -200, 30, 70); c.fillRect(-10, -200, 80, 160); c.fillStyle = trim; c.fillRect(-10, -60, 230, 14)
    c.fillStyle = '#e8c87a'; c.fillRect(8, -178, 40, 30)
    for (const wx of [30, 100, 170]) wheel(c, wx, -32, 32, t, '#7a2a22')
    // smoke puffs drifting back
    for (let k = 0; k < 8; k++) { const ph = (t * 0.8 + k / 8) % 1; ell(c, 165 - ph * 420, -220 - ph * 160, 30 + ph * 70, 24 + ph * 50, 0, `rgba(220,214,204,${0.55 * (1 - ph)})`) }
    c.restore()
  }
  function wheel(c, x, y, r, t, col = '#2a2a2e') { ell(c, x, y, r, r, 0, col); c.strokeStyle = '#c8b890'; c.lineWidth = 2; for (let k = 0; k < 4; k++) { const a = t * 6 + k * Math.PI / 4; c.beginPath(); c.moveTo(x - Math.cos(a) * r * 0.85, y - Math.sin(a) * r * 0.85); c.lineTo(x + Math.cos(a) * r * 0.85, y + Math.sin(a) * r * 0.85); c.stroke() } }
  // a camera on a tripod (old plate camera)
  function camera(c, x, y, s) { c.save(); c.translate(x, y); c.scale(s, s); c.strokeStyle = '#3a2a1a'; c.lineWidth = 5; for (const dx of [-40, 0, 40]) { c.beginPath(); c.moveTo(0, -120); c.lineTo(dx, 0); c.stroke() } c.fillStyle = hgrad(c, -40, 40, '#6a4a2a', '#4a3018'); c.fillRect(-36, -170, 70, 52); c.fillStyle = '#1a1410'; c.fillRect(30, -158, 24, 28); ell(c, 54, -144, 10, 12, 0, '#3a4a5a'); c.restore() }
  // money and numbers that count up: count(c, x, y, from, to, k, size)
  function count(c, x, y, v, size = 120, col = '#f3e7d0', o = {}) { text(c, typeof v === 'number' ? Math.round(v).toLocaleString('en-US') : v, x, y, size, col, Object.assign({ weight: 800, shadow: 24 }, o)) }

  Object.assign(PK, { tree, forest, snowPeaks, terraces, house, river, brush, paper, map, pathLine, train, wheel, camera, count })
})(window.PK)
