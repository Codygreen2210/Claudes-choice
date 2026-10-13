// paint/core.js: the Style B toolkit (painted storybook look). Shared by every story film.
// Utilities, the parallax camera, haze, light rays, grain, vignette, cached depth-of-field blur.
// Everything draws in a 1920x1080 "world" frame; the camera picks the part we see.
window.PK = window.PK || {};
(function (PK) {
  const W = 1920, H = 1080
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v))
  const lerp = (a, b, k) => a + (b - a) * k
  const ease = {
    l: p => p, io: p => p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2,
    o: p => 1 - Math.pow(1 - p, 3), i: p => p * p * p, sine: p => -(Math.cos(Math.PI * p) - 1) / 2,
    back: p => { const c1 = 1.7, c3 = c1 + 1; return 1 + c3 * Math.pow(p - 1, 3) + c1 * Math.pow(p - 1, 2) }
  }
  const prog = (t, a, b, e = 'l') => ease[e](clamp((t - a) / (b - a || 1e-6)))
  // keys(t, [[t0, v0], [t1, v1], ...]) eased in-out between keys; values may be numbers or {x,y,z} objects
  function keys(t, ks, e = 'io') {
    const mix = (a, b, k) => typeof a === 'number' ? lerp(a, b, k) : Object.fromEntries(Object.keys(a).map(n => [n, lerp(a[n], b[n] ?? a[n], k)]))
    if (t <= ks[0][0]) return ks[0][1]
    for (let i = 0; i < ks.length - 1; i++) { const [ta, va] = ks[i], [tb, vb] = ks[i + 1]; if (t <= tb) return mix(va, vb, ease[e]((t - ta) / (tb - ta || 1e-6))) }
    return ks[ks.length - 1][1]
  }
  const rng = s => () => { s |= 0; s = s + 0x6D2B79F5 | 0; let t = Math.imul(s ^ s >>> 15, 1 | s); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296 }
  // colours
  const hex = h => { const n = parseInt(h.slice(1), 16); return [n >> 16 & 255, n >> 8 & 255, n & 255] }
  const rgb = a => `rgb(${a[0] | 0},${a[1] | 0},${a[2] | 0})`
  const mixCol = (a, b, k) => { if (k <= 0) return a; const A = hex(a), B = hex(b); return '#' + A.map((v, i) => Math.round(lerp(v, B[i], k)).toString(16).padStart(2, '0')).join('') }
  const shade = (a, k) => mixCol(a, k < 0 ? '#000000' : '#ffffff', Math.abs(k))
  function vgrad(c, y0, y1, ...stops) { const g = c.createLinearGradient(0, y0, 0, y1); stops.forEach((s, i) => g.addColorStop(i / (stops.length - 1), s)); return g }
  function hgrad(c, x0, x1, ...stops) { const g = c.createLinearGradient(x0, 0, x1, 0); stops.forEach((s, i) => g.addColorStop(i / (stops.length - 1), s)); return g }
  function rgrad(c, x, y, r0, r1, ...stops) { const g = c.createRadialGradient(x, y, r0, x, y, r1); stops.forEach((s, i) => g.addColorStop(i / (stops.length - 1), s)); return g }
  function poly(c, pts, fill, close = true) { c.beginPath(); c.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) c.lineTo(pts[i][0], pts[i][1]); if (close) c.closePath(); if (fill) { c.fillStyle = fill; c.fill() } }
  function smooth(c, pts, fill, close = true) {   // a closed curve through the points
    c.beginPath(); const n = pts.length
    const mid = (a, b) => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]
    let m = mid(pts[n - 1], pts[0]); c.moveTo(m[0], m[1])
    for (let i = 0; i < n; i++) { const p = pts[i], m2 = mid(p, pts[(i + 1) % n]); c.quadraticCurveTo(p[0], p[1], m2[0], m2[1]) }
    if (close) c.closePath(); if (fill) { c.fillStyle = fill; c.fill() }
  }
  function ell(c, x, y, rx, ry, rot, fill) { c.beginPath(); c.ellipse(x, y, Math.max(0.1, rx), Math.max(0.1, ry), rot || 0, 0, Math.PI * 2); if (fill) { c.fillStyle = fill; c.fill() } }

  // ---- camera: cam = {x, y, z} is the world point at the centre of the screen and the zoom.
  // layer(c, cam, depth, fn): depth 1 = the action plane; <1 farther (moves less), >1 nearer (moves more).
  function layer(c, cam, f, fn) {
    c.save(); const z = 1 + (cam.z - 1) * f
    c.translate(W / 2 + (cam.sx || 0) * f, H / 2 + (cam.sy || 0) * f); c.scale(z, z)
    c.translate(-(960 + (cam.x - 960) * f), -(540 + (cam.y - 540) * f))
    fn(c); c.restore()
  }
  // screen shake from a list of hit times
  function shake(t, hits, amp = 12, dur = 0.4) { let a = 0; for (const h of hits) if (t > h && t < h + dur) a += (1 - (t - h) / dur) * amp; return a ? [Math.sin(t * 91) * a, Math.cos(t * 77) * a] : [0, 0] }

  // ---- grain and blur caches
  let grain = null
  function grainTile() { if (grain) return grain; grain = document.createElement('canvas'); grain.width = grain.height = 256; const g = grain.getContext('2d'), im = g.createImageData(256, 256), r = rng(9); for (let i = 0; i < im.data.length; i += 4) { const v = r() * 255; im.data[i] = im.data[i + 1] = im.data[i + 2] = v; im.data[i + 3] = 26 } g.putImageData(im, 0, 0); return grain }
  const sprites = new Map()
  // sprite(key, w, h, draw, blur): draws once into an offscreen canvas (optionally blurred) and caches it
  function sprite(key, w, h, draw, blur = 0) {
    let s = sprites.get(key); if (s) return s
    const pad = blur * 3, cv = document.createElement('canvas'); cv.width = w + pad * 2; cv.height = h + pad * 2
    const g = cv.getContext('2d'); g.translate(pad, pad); draw(g)
    if (blur) { const cv2 = document.createElement('canvas'); cv2.width = cv.width; cv2.height = cv.height; const g2 = cv2.getContext('2d'); g2.filter = `blur(${blur}px)`; g2.drawImage(cv, 0, 0); s = { cv: cv2, pad } }
    else s = { cv, pad }
    sprites.set(key, s); return s
  }
  function drawSprite(c, s, x, y, sx = 1, sy = 1, skew = 0) { c.save(); c.translate(x, y); if (skew) c.transform(1, 0, skew, 1, 0, 0); c.scale(sx, sy); c.drawImage(s.cv, -s.pad, -s.pad); c.restore() }

  // ---- grass tufts (the workhorse for foregrounds and lips of banks)
  function tuft(c, x, y, h, col, sway = 0, n = 6, seed = 1) {
    const r = rng(seed); c.fillStyle = col
    for (let k = 0; k < n; k++) {
      const bx = x + (k - n / 2) * h * 0.13, hh = h * (0.6 + r() * 0.5), lean = (r() - 0.5) * h * 0.5 + sway * h * 0.4
      c.beginPath(); c.moveTo(bx - h * 0.05, y); c.quadraticCurveTo(bx + lean * 0.3, y - hh * 0.6, bx + lean, y - hh); c.quadraticCurveTo(bx + lean * 0.3 + h * 0.04, y - hh * 0.5, bx + h * 0.06, y); c.closePath(); c.fill()
    }
  }
  // foreground: a strip of big blurred grass (or other shapes) across the bottom, cached and swaying by skew
  function foreground(c, t, o = {}) {
    const col = o.col || '#0f160f', y = o.y || 1270, seed = o.seed || 44
    const s = sprite('fg:' + col + ':' + seed + ':' + (o.kind || 'grass'), 3400, 560, g => {
      const r = rng(seed)
      if (o.kind === 'leaves') { for (let k = 0; k < 40; k++) { g.fillStyle = col; g.save(); g.translate(r() * 3400, 300 + r() * 260); g.rotate(r() * 6); ell(g, 0, 0, 60 + r() * 50, 22 + r() * 12, 0, col); g.restore() } }
      else for (let x = 0; x < 3400; x += 170 + r() * 260) tuft(g, x, 560, 170 + r() * 170, col, 0, 5, x | 0)
    }, o.blur ?? 7)
    const sway = Math.sin(t * 0.9) * 0.03
    c.save(); c.globalAlpha *= o.alpha ?? 0.9; drawSprite(c, s, -740, y - 560, 1, 1, sway); c.restore()
  }

  // ---- distant ridges and haze
  function ridgePts(seed, y0, amp, step, x0 = -900, x1 = 2900, bottom = 1600) {
    const r = rng(seed), pts = [[x0, bottom]]
    for (let x = x0; x <= x1; x += step) pts.push([x, y0 + (r() - 0.5) * amp])
    pts.push([x1, bottom]); return pts
  }
  function ridge(c, seed, y0, amp, step, top, bot, o = {}) { smooth(c, ridgePts(seed, y0, amp, step, o.x0, o.x1, o.bottom), vgrad(c, y0 - amp, y0 + (o.depth || 360), top, bot)) }
  function fog(c, y, h, col = '236,214,186', a = 0.5) { c.fillStyle = vgrad(c, y - h, y + h * 0.3, `rgba(${col},0)`, `rgba(${col},${a})`, `rgba(${col},${a * 0.6})`); c.fillRect(-1200, y - h, 4400, h * 1.6) }
  function sky(c, top, bottom, o = {}) {
    c.fillStyle = vgrad(c, -400, o.horizon || 760, top, bottom); c.fillRect(-1400, -1200, 4800, 3400)
    if (o.sun) { const [x, y, r = 520, col = '255,226,170'] = o.sun; c.fillStyle = rgrad(c, x, y, 8, r, `rgba(${col},0.95)`, `rgba(${col},0.45)`, `rgba(${col},0)`); c.fillRect(x - r, y - r, r * 2, r * 2) }
    if (o.moon) { const [x, y] = o.moon; c.fillStyle = rgrad(c, x, y, 2, 160, 'rgba(230,236,255,0.5)', 'rgba(230,236,255,0)'); c.fillRect(x - 160, y - 160, 320, 320); ell(c, x, y, 34, 34, 0, '#eef0f4') }
    if (o.stars) { const r = rng(5); c.fillStyle = 'rgba(255,255,255,0.7)'; for (let k = 0; k < 160; k++) { ell(c, r() * 3400 - 700, r() * 700 - 200, 1 + r() * 1.4, 1 + r() * 1.4, 0) ; c.fill() } }
    if (o.clouds) { const r = rng(o.clouds); for (let k = 0; k < 9; k++) { const x = r() * 3600 - 800, y = 80 + r() * 300, w = 220 + r() * 300; c.fillStyle = `rgba(255,244,230,${0.18 + r() * 0.2})`; for (let j = 0; j < 5; j++) ell(c, x + j * w * 0.22, y + Math.sin(j * 2.1) * 16, w * 0.22, w * 0.09, 0), c.fill() } }
  }

  // ---- finishing: light rays, vignette, grain, darkness for night, warm or cold grade
  function post(c, cam, o = {}) {
    c.setTransform(1, 0, 0, 1, 0, 0)
    if (o.night) { c.fillStyle = `rgba(14,18,34,${o.night})`; c.fillRect(0, 0, W, H) }
    if (o.grade) { c.save(); c.globalCompositeOperation = 'soft-light'; c.fillStyle = o.grade; c.fillRect(0, 0, W, H); c.restore() }
    if (o.rays !== false && !o.night) {
      c.save(); c.globalCompositeOperation = 'screen'; const a = o.rays ?? 0.14
      for (let k = 0; k < 4; k++) { const x = (o.rayX ?? 300) + k * 260 - (cam.x - 960) * 0.4; c.fillStyle = hgrad(c, x, x + 500, `rgba(255,214,150,${a})`, 'rgba(255,214,150,0)'); c.beginPath(); c.moveTo(x, -50); c.lineTo(x + 90, -50); c.lineTo(x + 640, H); c.lineTo(x + 420, H); c.closePath(); c.fill() }
      c.restore()
    }
    c.fillStyle = rgrad(c, W / 2, H / 2, H * 0.35, H * 1.0, 'rgba(0,0,0,0)', `rgba(0,0,0,${o.vignette ?? 0.6})`); c.fillRect(0, 0, W, H)
    c.save(); c.globalCompositeOperation = 'overlay'; c.fillStyle = c.createPattern(grainTile(), 'repeat'); c.fillRect(0, 0, W, H); c.restore()
  }
  function flashes(c, t, hits, col = '255,240,200', a = 0.45, d = 0.25) { c.setTransform(1, 0, 0, 1, 0, 0); for (const h of hits) { const tt = t - h; if (tt > 0 && tt < d) { c.fillStyle = `rgba(${col},${(1 - tt / d) * a})`; c.fillRect(0, 0, W, H) } } }

  // ---- text painted into the world (signs, numbers, labels on paper)
  function text(c, s, x, y, size, col, o = {}) {
    c.save(); c.font = `${o.italic ? 'italic ' : ''}${o.weight || 600} ${size}px ${o.font || 'Playfair'}`; c.textAlign = o.align || 'center'; c.textBaseline = 'middle'
    if (window.__vertical && o.fitV !== false) { const w = c.measureText(s).width, m = c.getTransform(), sx = Math.hypot(m.a, m.b); if (w * sx > 560) { size = size * 560 / (w * sx); c.font = `${o.italic ? 'italic ' : ''}${o.weight || 600} ${size}px ${o.font || 'Playfair'}` } }
    c.globalAlpha *= o.alpha ?? 1; if (o.rot) { c.translate(x, y); c.rotate(o.rot); x = 0; y = 0 }
    if (o.shadow) { c.shadowColor = 'rgba(0,0,0,0.85)'; c.shadowBlur = o.shadow }
    if (o.stroke) { c.lineWidth = o.stroke; c.strokeStyle = o.strokeCol || '#16100b'; c.lineJoin = 'round'; c.strokeText(s, x, y) }
    c.fillStyle = col; c.fillText(s, x, y); c.restore()
  }
  // a title card painted on the picture (place names, dates, numbers): cream italic with a soft shadow
  function label(c, s, x, y, a, size = 54) { if (a <= 0 || window.__vertical || window.__nolabels) return; text(c, s, x, y, size, '#f3e7d0', { italic: true, alpha: a, shadow: 18 }) }

  Object.assign(PK, { W, H, clamp, lerp, ease, prog, keys, rng, hex, rgb, mixCol, shade, vgrad, hgrad, rgrad, poly, smooth, ell, layer, shake, sprite, drawSprite, tuft, foreground, ridgePts, ridge, fog, sky, post, flashes, text, label, grainTile })
})(window.PK)
