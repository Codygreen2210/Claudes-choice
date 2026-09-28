// art.js: the drawing and animation kit for studio pages. Load after kit.js; everything hangs off window.A.
//
// COLOUR (OKLCH: perceptual lightness, chroma, hue; equal steps look equal, unlike HSL)
//   A.oklch(L, C, h, a)            -> css colour string (out-of-gamut colours are pulled in by lowering chroma)
//   A.harmony(h, scheme)           -> hues for 'mono' | 'analogous' | 'complementary' | 'split' | 'triadic' | 'tetradic'
//   A.palette(h, scheme, opts)     -> { bg, ink, mid, accent, colors[] } with a planned value structure (60/30/10)
//   A.ramp(h, C, n, L0, L1)        -> n colours stepping evenly in lightness
// MOTION (the principles, as functions of time, so pages stay pure __seek(t))
//   A.spring(dt, {from, to, k, zeta, v0})   damped spring, closed form. dt = time since release.
//   A.follow(driver, t, {k, zeta, dt})      secondary motion: a value that chases driver(t) on a spring (drag, follow-through)
//   A.anticipate(p, amt)            easing that pulls back first, then goes (anticipation)
//   A.stagger(i, n, spread, curve)  start offsets for n things so a move ripples through them (overlapping action)
//   A.squash(vx, vy, amt)           {sx, sy, angle}: stretch along the direction of travel, keeping area
//   A.arc(p, x0, y0, x1, y1, lift)  point on an arc between two points
// DRAWING (canvas 2D)
//   A.spline(ctx, pts, closed)      smooth Catmull-Rom path through points
//   A.blob(ctx, cx, cy, r, seed, t, wobble)   organic closed shape that can breathe over time
//   A.brush(ctx, pts, {width, color, bristles, seed, dry})   a painted stroke: tapered, bristled, a little dry at the edges
//   A.grain(ctx, W, H, amt, seed)   paper/film grain over everything
//   A.glow(ctx, x, y, r, color, a)  soft radial light
(function () {
  // ---------------------------------------------------------------- colour
  const toLin = c => c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4
  const toSrgb = c => c <= 0.0031308 ? 12.92 * c : 1.055 * c ** (1 / 2.4) - 0.055
  function oklabToLinear(L, a, b) {
    const l_ = L + 0.3963377774 * a + 0.2158037573 * b, m_ = L - 0.1055613458 * a - 0.0638541728 * b, s_ = L - 0.0894841775 * a - 1.2914855480 * b
    const l = l_ ** 3, m = m_ ** 3, s = s_ ** 3
    return [4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s, -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s]
  }
  function oklchToRgb(L, C, h) {
    // reduce chroma until the colour fits sRGB (keeps lightness and hue, which is what the eye cares about most)
    for (let c = C; c >= 0; c -= 0.005) {
      const r = oklabToLinear(L, c * Math.cos(h * Math.PI / 180), c * Math.sin(h * Math.PI / 180))
      if (r.every(v => v >= -0.0005 && v <= 1.0005)) return r.map(v => Math.round(toSrgb(Math.min(1, Math.max(0, v))) * 255))
    }
    const g = Math.round(toSrgb(Math.min(1, Math.max(0, L ** 3))) * 255); return [g, g, g]
  }
  const oklch = (L, C, h, a = 1) => { const [r, g, b] = oklchToRgb(L, C, h); return a >= 1 ? `rgb(${r},${g},${b})` : `rgba(${r},${g},${b},${a})` }
  const SCHEMES = { mono: [0], analogous: [-30, 0, 30], complementary: [0, 180], split: [0, 150, 210], triadic: [0, 120, 240], tetradic: [0, 90, 180, 270] }
  const harmony = (h, scheme = 'analogous') => SCHEMES[scheme].map(d => (h + d + 360) % 360)
  const ramp = (h, C, n, L0 = 0.2, L1 = 0.92) => Array.from({ length: n }, (_, i) => oklch(L0 + (L1 - L0) * i / Math.max(1, n - 1), C, h))
  // A planned palette: one dominant value family (bg, ~60%), a secondary (mid, ~30%), a small loud accent (~10%).
  function palette(h, scheme = 'split', { dark = true, chroma = 0.12 } = {}) {
    const hs = harmony(h, scheme)
    const acc = hs[hs.length > 1 ? 1 : 0]
    return {
      bg: dark ? oklch(0.17, 0.03, h) : oklch(0.95, 0.02, h),
      bg2: dark ? oklch(0.23, 0.05, h) : oklch(0.88, 0.03, h),
      mid: dark ? oklch(0.45, chroma * 0.7, hs[0]) : oklch(0.62, chroma * 0.7, hs[0]),
      ink: dark ? oklch(0.93, 0.02, h) : oklch(0.22, 0.03, h),
      accent: oklch(0.74, Math.max(chroma, 0.16), acc),
      colors: hs.map((hh, i) => oklch(dark ? 0.62 : 0.55, chroma, hh)), hues: hs,
    }
  }

  // ---------------------------------------------------------------- motion
  // Damped spring from `from` to `to`, released dt seconds ago with velocity v0. k: stiffness (1/s^2), zeta: damping ratio.
  function spring(dt, { from = 0, to = 1, k = 170, zeta = 0.5, v0 = 0 } = {}) {
    if (dt <= 0) return from
    const w = Math.sqrt(k), x0 = from - to
    if (zeta < 1) {
      const wd = w * Math.sqrt(1 - zeta * zeta)
      return to + Math.exp(-zeta * w * dt) * (x0 * Math.cos(wd * dt) + ((v0 + zeta * w * x0) / wd) * Math.sin(wd * dt))
    }
    return to + Math.exp(-w * dt) * (x0 + (v0 + w * x0) * dt)                      // critically damped
  }
  // A value that chases driver(t) on a spring. Simulated from 0 with a fixed step and cached, so it is still
  // a pure function of t (renders are repeatable and can be split across workers).
  const _cache = new Map()
  function follow(driver, t, { k = 60, zeta = 0.35, dt = 1 / 240, key = 'f' } = {}) {
    let c = _cache.get(key)
    if (!c || c.driver !== driver) { c = { driver, xs: [driver(0)], vs: [0] }; _cache.set(key, c) }
    const need = Math.ceil(t / dt)
    for (let i = c.xs.length; i <= need; i++) {
      const x = c.xs[i - 1], v = c.vs[i - 1], target = driver(i * dt)
      const a = k * (target - x) - 2 * zeta * Math.sqrt(k) * v
      const v2 = v + a * dt; c.vs.push(v2); c.xs.push(x + v2 * dt)
    }
    return c.xs[Math.max(0, Math.min(need, c.xs.length - 1))]
  }
  // anticipation: dip back by amt (fraction of the move) during the first ~30%, then an ease-out to the target
  // anticipation: ease back to -amt over the first `wind` of the time, then release forward to 1 with an
  // ease-out (the snap). Continuous in position; the release is meant to be quick.
  const anticipate = (p, amt = 0.12, wind = 0.3) => {
    p = Math.min(1, Math.max(0, p))
    if (p < wind) return -amt * Math.sin(Math.PI / 2 * (p / wind))
    const q = (p - wind) / (1 - wind)
    return -amt + (1 + amt) * (1 - (1 - q) ** 3)
  }
  const stagger = (i, n, spread = 0.3, curve = x => x) => spread * curve(n <= 1 ? 0 : i / (n - 1))
  function squash(vx, vy, amt = 0.0006) {
    const sp = Math.hypot(vx, vy), s = 1 + Math.min(0.6, sp * amt)
    return { sx: s, sy: 1 / s, angle: Math.atan2(vy, vx) }
  }
  const arc = (p, x0, y0, x1, y1, lift = 0.25) => {
    const mx = (x0 + x1) / 2, my = (y0 + y1) / 2, dx = x1 - x0, dy = y1 - y0, L = Math.hypot(dx, dy) || 1
    const cx = mx + (dy / L) * L * lift, cy = my - (dx / L) * L * lift          // control point off to one side
    const u = 1 - p; return [u * u * x0 + 2 * u * p * cx + p * p * x1, u * u * y0 + 2 * u * p * cy + p * p * y1]
  }

  // ---------------------------------------------------------------- drawing
  function spline(ctx, pts, closed = false, tension = 0.5) {
    const n = pts.length; if (n < 2) return
    const P = i => closed ? pts[(i + n) % n] : pts[Math.max(0, Math.min(n - 1, i))]
    ctx.moveTo(pts[0][0], pts[0][1])
    const last = closed ? n : n - 1
    for (let i = 0; i < last; i++) {
      const p0 = P(i - 1), p1 = P(i), p2 = P(i + 1), p3 = P(i + 2)
      ctx.bezierCurveTo(p1[0] + (p2[0] - p0[0]) * tension / 3, p1[1] + (p2[1] - p0[1]) * tension / 3,
        p2[0] - (p3[0] - p1[0]) * tension / 3, p2[1] - (p3[1] - p1[1]) * tension / 3, p2[0], p2[1])
    }
    if (closed) ctx.closePath()
  }
  function blob(ctx, cx, cy, r, seed = 1, t = 0, wobble = 0.18, n = 9) {
    const pts = []
    for (let i = 0; i < n; i++) {
      const a = i / n * Math.PI * 2
      const rr = r * (1 + wobble * K.noise(Math.cos(a) * 1.3 + seed * 7.1 + t * 0.35, Math.sin(a) * 1.3 + seed * 3.7))
      pts.push([cx + Math.cos(a) * rr, cy + Math.sin(a) * rr])
    }
    ctx.beginPath(); spline(ctx, pts, true)
  }
  // A painted stroke: many thin bristles following the path, tapering at both ends, each slightly offset and
  // a little dry (broken) toward the edges of the brush.
  function brush(ctx, pts, { width = 20, color = '#000', bristles = 14, seed = 1, dry = 0.35, alpha = 0.9 } = {}) {
    if (pts.length < 2) return
    const R = K.rng(seed)
    // resample along the path
    const seg = []; let total = 0
    for (let i = 1; i < pts.length; i++) { const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); seg.push(d); total += d }
    const N = Math.max(8, Math.round(total / 3)), path = []
    for (let k = 0; k <= N; k++) {
      let s = total * k / N, i = 0
      while (i < seg.length - 1 && s > seg[i]) { s -= seg[i]; i++ }
      const p = Math.min(1, s / (seg[i] || 1)), a = pts[i], b = pts[i + 1]
      path.push([a[0] + (b[0] - a[0]) * p, a[1] + (b[1] - a[1]) * p])
    }
    ctx.save(); ctx.strokeStyle = color; ctx.lineCap = 'round'
    for (let j = 0; j < bristles; j++) {
      const off = (j / (bristles - 1) - 0.5) * 2               // -1 .. 1 across the brush
      const edge = Math.abs(off)
      ctx.globalAlpha = alpha * (0.35 + 0.65 * (1 - edge * 0.8)) * (0.7 + 0.3 * R())
      ctx.lineWidth = Math.max(0.6, width / bristles * (1.2 + R()))
      ctx.beginPath()
      let drawing = false
      for (let k = 0; k <= N; k++) {
        const u = k / N, taper = Math.sin(Math.PI * Math.min(1, u * 1.15)) ** 0.6
        const [x, y] = path[k], [x2, y2] = path[Math.min(N, k + 1)], [x1, y1] = path[Math.max(0, k - 1)]
        const nx = -(y2 - y1), ny = x2 - x1, nl = Math.hypot(nx, ny) || 1
        const o = off * width / 2 * taper + (R() - 0.5) * 0.8
        const gap = R() < dry * edge * edge * 0.6                 // dry brush: edges break up
        if (gap) { drawing = false; continue }
        const px = x + nx / nl * o, py = y + ny / nl * o
        if (!drawing) { ctx.moveTo(px, py); drawing = true } else ctx.lineTo(px, py)
      }
      ctx.stroke()
    }
    ctx.restore()
  }
  const _grain = {}
  function grain(ctx, W, H, amt = 0.06, seed = 3) {
    const key = `${W}x${H}:${seed}`
    if (!_grain[key]) {
      const c = document.createElement('canvas'); c.width = Math.ceil(W / 2); c.height = Math.ceil(H / 2)
      const g = c.getContext('2d'), img = g.createImageData(c.width, c.height), R = K.rng(seed)
      for (let i = 0; i < img.data.length; i += 4) { const v = 128 + (R() - 0.5) * 255; img.data[i] = img.data[i + 1] = img.data[i + 2] = v; img.data[i + 3] = 255 }
      g.putImageData(img, 0, 0); _grain[key] = c
    }
    ctx.save(); ctx.globalAlpha = amt; ctx.globalCompositeOperation = 'overlay'; ctx.drawImage(_grain[key], 0, 0, W, H); ctx.restore()
  }
  function glow(ctx, x, y, r, color, a = 1) {
    const g = ctx.createRadialGradient(x, y, 0, x, y, r)
    g.addColorStop(0, color); g.addColorStop(1, 'rgba(0,0,0,0)')
    ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = g; ctx.fillRect(x - r, y - r, 2 * r, 2 * r); ctx.restore()
  }
  window.A = { oklch, harmony, ramp, palette, spring, follow, anticipate, stagger, squash, arc, spline, blob, brush, grain, glow }
})()
