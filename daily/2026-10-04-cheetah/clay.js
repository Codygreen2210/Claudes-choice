// clay.js: the clay-and-yarn drawing kit, lifted from the Marble Tune story film so other films can use it.
// Load after kit.js. The page must define these globals before drawing: g (2D context), TS (time snapped to
// poses), BOIL (counter that shifts clay edges between poses), F(weight, px) (font string), and CUES.mouth for lump().
const { clamp, lerp, noise, EZ } = K
function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296 } }
function speckle(w, h, n, cols, size, hairs) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; const x = c.getContext('2d'), r = rng(w * 7 + n)
  for (let i = 0; i < n; i++) {
    const col = cols[i % cols.length]; x.fillStyle = `rgba(${col[0]},${col[1]},${col[2]},${col[3]})`
    const px = r() * w, py = r() * h
    if (hairs) { x.save(); x.translate(px, py); x.rotate(r() * 6.28); x.fillRect(0, 0, 2 + r() * 5, 0.8); x.restore() } else x.fillRect(px, py, r() * size, r() * size)
  }
  return c
}

// ------------------------------------------------------------------ clay
function blob(cx, cy, rx, ry, seed, amp = 0.05, n = 18) {
  const pts = []
  for (let i = 0; i < n; i++) {
    const a = i / n * Math.PI * 2, k = 1 + amp * noise(seed * 3.1 + i * 0.9, BOIL * 0.83 + seed)
    pts.push([cx + Math.cos(a) * rx * k, cy + Math.sin(a) * ry * k])
  }
  return pts
}
function slab(x, y, w, h, r, seed, amp = 2.2) {      // rounded rectangle with hand-pressed edges
  const pts = [], add = (px, py, i) => pts.push([px + amp * noise(seed + i * 0.7, BOIL * 0.83), py + amp * noise(seed + 40 + i * 0.7, BOIL * 0.83)])
  const corners = [[x + w - r, y + r, -Math.PI / 2], [x + w - r, y + h - r, 0], [x + r, y + h - r, Math.PI / 2], [x + r, y + r, Math.PI]]
  let i = 0
  corners.forEach(([cx, cy, a0], c) => {
    for (let k = 0; k <= 5; k++) { const a = a0 + k / 5 * Math.PI / 2; add(cx + Math.cos(a) * r, cy + Math.sin(a) * r, i++) }
    const [nx, ny, na] = corners[(c + 1) % 4], ex = cx + Math.cos(a0 + Math.PI / 2) * r, ey = cy + Math.sin(a0 + Math.PI / 2) * r
    const sx = nx + Math.cos(na) * r, sy = ny + Math.sin(na) * r, steps = Math.max(1, Math.round(Math.hypot(sx - ex, sy - ey) / 60))
    for (let k = 1; k < steps; k++) add(lerp(ex, sx, k / steps), lerp(ey, sy, k / steps), i++)
  })
  return pts
}
function trace(pts) {
  g.beginPath()
  const n = pts.length, m = i => [(pts[i][0] + pts[(i + 1) % n][0]) / 2, (pts[i][1] + pts[(i + 1) % n][1]) / 2]
  const s = m(n - 1); g.moveTo(s[0], s[1])
  for (let i = 0; i < n; i++) { const e = m(i); g.quadraticCurveTo(pts[i][0], pts[i][1], e[0], e[1]) }
  g.closePath()
}
// col = [hue, saturation, lightness]
function clay(pts, col, o = {}) {
  let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9
  for (const p of pts) { x0 = Math.min(x0, p[0]); y0 = Math.min(y0, p[1]); x1 = Math.max(x1, p[0]); y1 = Math.max(y1, p[1]) }
  const w = x1 - x0, h = y1 - y0, [hh, ss, ll] = col, a = o.alpha == null ? 1 : o.alpha
  g.save(); g.globalAlpha *= a
  if (o.shadow !== false) {
    g.save(); g.shadowColor = 'rgba(52,30,10,0.38)'; g.shadowBlur = o.lift ? 34 : 20; g.shadowOffsetX = 5; g.shadowOffsetY = o.lift ? 20 : 11
    trace(pts); g.fillStyle = `hsl(${hh},${ss}%,${ll}%)`; g.fill(); g.restore()
  }
  trace(pts); g.save(); g.clip()
  const gr = g.createRadialGradient(x0 + w * 0.3, y0 + h * 0.22, 4, x0 + w * 0.5, y0 + h * 0.55, Math.max(w, h) * 0.85)
  gr.addColorStop(0, `hsl(${hh},${ss}%,${Math.min(96, ll + 11)}%)`); gr.addColorStop(0.55, `hsl(${hh},${ss}%,${ll}%)`); gr.addColorStop(1, `hsl(${hh},${ss + 4}%,${Math.max(6, ll - 15)}%)`)
  g.fillStyle = gr; g.fillRect(x0 - 4, y0 - 4, w + 8, h + 8)
  // thumb marks: a few soft dents and ridges that stay put on the piece
  const r = rng(Math.round(o.seed || w * 13 + h * 7))
  for (let i = 0; i < Math.max(3, Math.round(w * h / 9000)); i++) {
    const px = x0 + r() * w, py = y0 + r() * h, rr = 10 + r() * Math.min(w, h) * 0.22, a0 = r() * 6.28
    g.lineWidth = 1.6 + r() * 2.2
    g.strokeStyle = 'rgba(255,255,255,0.10)'; g.beginPath(); g.arc(px, py, rr, a0, a0 + 0.9 + r()); g.stroke()
    g.strokeStyle = 'rgba(40,20,5,0.09)'; g.beginPath(); g.arc(px + 2, py + 3, rr, a0, a0 + 0.9 + r()); g.stroke()
  }
  g.restore()
  trace(pts); g.lineWidth = 2; g.strokeStyle = `hsla(${hh},${ss}%,${Math.max(5, ll - 26)}%,0.35)`; g.stroke()
  g.restore()
}
const C = { cream: [42, 55, 88], terra: [16, 66, 56], teal: [176, 46, 44], mustard: [43, 82, 56], brick: [6, 62, 50], navy: [226, 40, 26], green: [140, 40, 46], plum: [300, 26, 42], wood: [28, 44, 36], white: [45, 30, 94], dark: [24, 30, 16], sky: [205, 60, 60] }
function ball(x, y, r, col, seed) { clay(blob(x, y, r, r, seed, 0.04, 12), col, { seed }) }
// a clay tag with words pressed on it. Returns its width.
function tag(text, x, y, o = {}) {
  const size = (o.size || 38) * 1.2, s = o.s == null ? 1 : o.s; if (s <= 0.01) return 0
  g.font = F(o.weight || 700, size)
  const tw = g.measureText(text).width, w = tw + size * 1.3, h = size * 1.9, rot = (o.rot || 0) + 0.012 * noise(x * 0.01, BOIL * 0.83 + y)
  g.save(); g.translate(x, y); g.rotate(rot); g.scale(s, 2 - Math.max(s, 1) * 1 + (s < 1 ? s - 1 : 0) + 0)   // overshoot squashes a touch
  clay(slab(o.left ? 0 : -w / 2, -h / 2, w, h, Math.min(h / 2, 26), (o.seed || x + y)), o.col || C.cream, { seed: o.seed || x + y })
  g.font = F(o.weight || 700, size); g.textAlign = o.left ? 'left' : 'center'; g.textBaseline = 'middle'
  const ink = o.ink || ((o.col || C.cream)[2] > 52 ? '#3a2412' : '#fff6e2')
  g.fillStyle = 'rgba(255,255,255,0.18)'; g.fillText(text, (o.left ? size * 0.65 : 0) + 1, 3)
  g.fillStyle = ink; g.fillText(text, o.left ? size * 0.65 : 0, 1)
  g.restore()
  return w
}

// ------------------------------------------------------------------ yarn
// A strand from (x1,y1) to (x2,y2): twisted plies, loose fibres, a pin at each end. s = pop scale, twang = seconds since hit.
function yarn(x1, y1, x2, y2, hue, o = {}) {
  const s = o.s == null ? 1 : o.s; if (s <= 0.02) return
  const cx = (x1 + x2) / 2, cy = (y1 + y2) / 2
  x1 = cx + (x1 - cx) * s; y1 = cy + (y1 - cy) * s; x2 = cx + (x2 - cx) * s; y2 = cy + (y2 - cy) * s
  const dx = x2 - x1, dy = y2 - y1, L = Math.hypot(dx, dy) || 1, ux = dx / L, uy = dy / L, nx = -uy, ny = ux
  const th = (o.th || 15) * Math.min(1, s + 0.2), n = Math.max(4, Math.ceil(L / 9)), seed = o.seed || Math.round(x1 + y1 * 3)
  const tw = o.twang == null || o.twang > 0.8 ? 0 : 9 * Math.exp(-o.twang * 5) * Math.sin(o.twang * 46)
  const pts = []
  for (let i = 0; i <= n; i++) {
    const u = i / n, off = Math.sin(u * Math.PI) * (tw + 2.5 * noise(seed, BOIL * 0.83)) + 1.6 * noise(seed + i * 0.45, BOIL * 0.83 + 9)
    pts.push([x1 + dx * u + nx * off, y1 + dy * u + ny * off])
  }
  const path = () => { g.beginPath(); g.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) g.lineTo(pts[i][0], pts[i][1]) }
  const lit = o.lit || 0, a = o.alpha == null ? 1 : o.alpha
  g.save(); g.globalAlpha *= a; g.lineCap = 'round'; g.lineJoin = 'round'
  g.save(); g.shadowColor = 'rgba(0,0,10,0.45)'; g.shadowBlur = 10; g.shadowOffsetX = 3; g.shadowOffsetY = 8
  path(); g.strokeStyle = `hsl(${hue},62%,${44 + lit * 18}%)`; g.lineWidth = th; g.stroke(); g.restore()
  // plies: short slanted strokes, dark then light, give the twist
  for (let i = 0; i < pts.length - 1; i++) {
    const [px, py] = pts[i], k = th * 0.46
    g.strokeStyle = i % 2 ? `hsla(${hue},70%,${64 + lit * 16}%,0.9)` : `hsla(${hue},60%,${32 + lit * 14}%,0.85)`
    g.lineWidth = th * 0.2
    g.beginPath(); g.moveTo(px + nx * k - ux * k * 0.7, py + ny * k - uy * k * 0.7); g.lineTo(px - nx * k + ux * k * 0.7, py - ny * k + uy * k * 0.7); g.stroke()
  }
  // loose fibres
  const r = rng(seed); g.lineWidth = 1.1
  for (let i = 0; i < L / 7; i++) {
    const u = r(), side = r() < 0.5 ? -1 : 1, p = pts[Math.min(n, Math.round(u * n))], len = 4 + r() * 8, lean = (r() - 0.5) * 1.6
    g.strokeStyle = `hsla(${hue},65%,${60 + r() * 20}%,${0.35 + r() * 0.4})`
    g.beginPath(); g.moveTo(p[0] + nx * side * th * 0.42, p[1] + ny * side * th * 0.42)
    g.lineTo(p[0] + nx * side * (th * 0.42 + len) + ux * lean * len, p[1] + ny * side * (th * 0.42 + len) + uy * lean * len); g.stroke()
  }
  g.restore()
  if (o.pins !== false) { g.save(); g.globalAlpha *= a; ball(pts[0][0], pts[0][1], th * 0.62, C.cream, seed + 1); ball(pts[n][0], pts[n][1], th * 0.62, C.cream, seed + 2); g.restore() }
}

// ------------------------------------------------------------------ the character: a lump of clay with eyes
function lump(x, y, sc, o = {}) {
  if (sc <= 0.01) return
  const fi = Math.min(CUES.mouth.length - 1, Math.max(0, Math.floor(TS * 24)))
  const m = o.mute ? 0 : Math.max(CUES.mouth[fi], CUES.mouth[Math.min(CUES.mouth.length - 1, fi + 1)])
  const breathe = 0.02 * Math.sin(TS * 2.1), talk = m * 0.05
  g.save(); g.translate(x, y); g.scale(sc * (1 - talk * 0.5 + (o.squash || 0)), sc * (1 + breathe + talk - (o.squash || 0)))
  // soft ground shadow
  g.fillStyle = 'rgba(52,30,10,0.22)'; g.beginPath(); g.ellipse(6, 112, 120, 20, 0, 0, 6.283); g.fill()
  const body = blob(0, 10, 122, 104, 7, 0.06, 20)
  body.forEach(p => { if (p[1] > 60) p[1] = 60 + (p[1] - 60) * 0.72 })           // flat-ish bottom: it sits
  clay(body, C.terra, { seed: 77 })
  const lx = clamp(o.lookX || 0, -1, 1) * 9, ly = clamp(o.lookY || 0, -1, 1) * 7
  const blink = (Math.floor(TS * 12) % 46) < 2 || o.shut
  for (const sx of [-42, 42]) {
    if (blink) { g.strokeStyle = '#4a2413'; g.lineWidth = 7; g.lineCap = 'round'; g.beginPath(); g.moveTo(sx - 20, -22); g.quadraticCurveTo(sx, -12, sx + 20, -22); g.stroke(); continue }
    clay(blob(sx, -22, 29, 31, 20 + sx, 0.04, 12), C.white, { seed: 30 + sx, shadow: false })
    g.fillStyle = '#2a1a12'; g.beginPath(); g.arc(sx + lx, -20 + ly, 12.5, 0, 6.283); g.fill()
    g.fillStyle = 'rgba(255,255,255,0.85)'; g.beginPath(); g.arc(sx + lx - 4, -25 + ly, 3.6, 0, 6.283); g.fill()
  }
  if (o.worry) { g.strokeStyle = '#7b3a1f'; g.lineWidth = 7; g.lineCap = 'round'; for (const sx of [-1, 1]) { g.beginPath(); g.moveTo(sx * 66, -66); g.lineTo(sx * 24, -58 - 12); g.stroke() } }
  // mouth: opens with the voice
  g.fillStyle = '#4a1d12'; g.beginPath()
  if (m > 0.08) g.ellipse(0, 36, 20 + m * 6, 4 + m * 19, 0, 0, 6.283)
  else if (o.worry) { g.ellipse(0, 40, 16, 4, 0, 0, 6.283) }
  else { g.moveTo(-22, 32); g.quadraticCurveTo(0, 50, 22, 32); g.quadraticCurveTo(0, 42, -22, 32) }
  g.fill()
  g.restore()
}

