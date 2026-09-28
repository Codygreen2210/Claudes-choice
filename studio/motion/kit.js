// kit.js: small, dependency-free helpers for time-driven animation pages rendered by render.mjs.
// Include with <script src="../motion/kit.js"></script> (adjust the path). Everything hangs off window.K.
//
// The rule: nothing animates on its own clock. Write a pure function of time,
//   window.__seek = t => { ...set every style from t... }
// and the renderer calls it for every frame.
(function () {
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x))
  const lerp = (a, b, p) => a + (b - a) * p
  const EZ = {
    l: p => p,
    i: p => p * p * p, o: p => 1 - Math.pow(1 - p, 3), io: p => p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2,
    o5: p => 1 - Math.pow(1 - p, 5), i5: p => p ** 5,
    sine: p => -(Math.cos(Math.PI * p) - 1) / 2,
    back: p => { const c1 = 1.9, c3 = c1 + 1; return 1 + c3 * Math.pow(p - 1, 3) + c1 * Math.pow(p - 1, 2) },
    elastic: p => p === 0 || p === 1 ? p : Math.pow(2, -10 * p) * Math.sin((p * 10 - 0.75) * (2 * Math.PI) / 3) + 1,
    bounce: p => { const n = 7.5625, d = 2.75; if (p < 1 / d) return n * p * p; if (p < 2 / d) return n * (p -= 1.5 / d) * p + .75; if (p < 2.5 / d) return n * (p -= 2.25 / d) * p + .9375; return n * (p -= 2.625 / d) * p + .984375 },
  }
  // progress of t through [a, b], eased
  const prog = (t, a, b, e = 'l') => EZ[e](clamp((t - a) / (b - a)))
  // a smooth 0 -> 1 -> 0 pulse starting at a, lasting d
  const bump = (t, a, d) => (t < a || t > a + d) ? 0 : Math.sin(Math.PI * (t - a) / d)
  // keyframes: [[t0, v0], [t1, v1, 'ease'], ...]; values may be numbers or arrays
  function track(t, keys) {
    if (t <= keys[0][0]) return keys[0][1]
    for (let i = 0; i < keys.length - 1; i++) {
      const [ta, va] = keys[i], [tb, vb, e] = keys[i + 1]
      if (t <= tb) {
        const p = EZ[e || 'io']((t - ta) / (tb - ta))
        return Array.isArray(va) ? va.map((v, k) => v + (vb[k] - v) * p) : va + (vb - va) * p
      }
    }
    return keys[keys.length - 1][1]
  }
  // deterministic random (same seed, same film)
  function rng(seed = 1) {
    let a = seed >>> 0
    return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296 }
  }
  // smooth value noise, 1D and 2D, in [-1, 1]
  const hash = (x, y = 0) => { const s = Math.sin(x * 127.1 + y * 311.7) * 43758.5453; return (s - Math.floor(s)) * 2 - 1 }
  const sm = p => p * p * (3 - 2 * p)
  function noise(x, y = 0) {
    const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi
    const a = hash(xi, yi), b = hash(xi + 1, yi), c = hash(xi, yi + 1), d = hash(xi + 1, yi + 1)
    return lerp(lerp(a, b, sm(xf)), lerp(c, d, sm(xf)), sm(yf))
  }
  const fbm = (x, y = 0, oct = 4) => { let v = 0, amp = 0.5, f = 1; for (let i = 0; i < oct; i++) { v += amp * noise(x * f, y * f); f *= 2; amp *= 0.5 } return v }
  // colour
  const hex = h => { h = h.replace('#', ''); return [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16)) }
  const mix = (c1, c2, p) => { const a = typeof c1 === 'string' ? hex(c1) : c1, b = typeof c2 === 'string' ? hex(c2) : c2; return `rgb(${a.map((v, i) => Math.round(lerp(v, b[i], p))).join(',')})` }
  const hsl = (h, s, l, a = 1) => `hsla(${h},${s}%,${l}%,${a})`
  // shrink an element's font until it fits a width
  function fit(el, max) { let fs = parseFloat(getComputedStyle(el).fontSize); while (el.scrollWidth > max && fs > 8) { fs -= 1; el.style.fontSize = fs + 'px' } }
  // beat helpers: time of beat k at bpm (with offset), and phase within the current beat
  const beatAt = (k, bpm, t0 = 0) => t0 + k * 60 / bpm
  const beatPhase = (t, bpm, t0 = 0) => { const b = (t - t0) * bpm / 60; return b - Math.floor(b) }
  // explore.py passes a variation's settings in the URL hash as JSON: page.html#{"hue":210,"speed":1.4}
  // K.genome({hue: 0, speed: 1}) returns the defaults overridden by whatever the hash carries.
  function genome(defaults = {}) {
    try { const h = decodeURIComponent(location.hash.slice(1)); return Object.assign({}, defaults, h ? JSON.parse(h) : {}) } catch (e) { return Object.assign({}, defaults) }
  }
  window.K = { clamp, lerp, EZ, prog, bump, track, rng, noise, fbm, hex, mix, hsl, fit, beatAt, beatPhase, genome }
})()
