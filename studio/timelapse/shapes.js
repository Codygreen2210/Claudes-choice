// shapes.js: geometry helpers shared by drawings (browser: window.SH, Node: require).
// Everything works on points [x, y] in whatever space a drawing uses.
(function (root) {
  const add = (a, b, k = 1) => [a[0] + b[0] * k, a[1] + b[1] * k]
  const sub = (a, b) => [a[0] - b[0], a[1] - b[1]]
  const mix = (a, b, u) => [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u]
  const len = v => Math.hypot(v[0], v[1])
  const unit = v => { const l = len(v) || 1; return [v[0] / l, v[1] / l] }
  const perp = v => [v[1], -v[0]]
  const rot = (v, a) => [v[0] * Math.cos(a) - v[1] * Math.sin(a), v[0] * Math.sin(a) + v[1] * Math.cos(a)]

  // Catmull-Rom through the points
  function curve(P, n = 10, closed = false) {
    const out = [], m = P.length, get = i => closed ? P[(i + m) % m] : P[Math.max(0, Math.min(m - 1, i))]
    if (m < 2) return P.slice()
    for (let i = 0; i < (closed ? m : m - 1); i++) {
      const p0 = get(i - 1), p1 = get(i), p2 = get(i + 1), p3 = get(i + 2)
      for (let k = 0; k < n; k++) {
        const t = k / n, t2 = t * t, t3 = t2 * t
        out.push([0, 1].map(j => 0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3)))
      }
    }
    out.push(closed ? P[0] : P[m - 1]); return out
  }
  const circle = (c, r, a0 = 0, turns = 1, ry = r, n = 40) => { const o = []; for (let i = 0; i <= n; i++) { const a = a0 + turns * 2 * Math.PI * i / n; o.push([c[0] + r * Math.cos(a), c[1] + ry * Math.sin(a)]) } return o }

  // resample a path to n evenly spaced points
  function resample(P, n) {
    const d = [0]; for (let i = 1; i < P.length; i++) d.push(d[i - 1] + len(sub(P[i], P[i - 1])))
    const L = d[d.length - 1], out = []
    for (let k = 0, i = 0; k < n; k++) {
      const s = L * k / (n - 1)
      while (i < d.length - 2 && d[i + 1] < s) i++
      const u = (s - d[i]) / ((d[i + 1] - d[i]) || 1); out.push(mix(P[i], P[i + 1] || P[i], Math.min(1, u)))
    }
    return out
  }
  const pathLen = P => P.reduce((a, p, i) => i ? a + len(sub(p, P[i - 1])) : 0, 0)

  // a tube around a path, width given as a function of u (0..1 along it). Returns both edges and the outline.
  function tube(P, W, n) {
    const Q = n ? resample(P, n) : P, L = [], R = [], N = []
    Q.forEach((p, i) => {
      const a = Q[Math.max(0, i - 1)], b = Q[Math.min(Q.length - 1, i + 1)], nn = perp(unit(sub(b, a))), w = W(i / (Q.length - 1)) / 2
      L.push(add(p, nn, w)); R.push(add(p, nn, -w)); N.push(nn)
    })
    return { mid: Q, left: L, right: R, normals: N, poly: [...L, ...R.slice().reverse()] }
  }
  // Hand-drawn repeats are never evenly spaced: every ring, strand or plate gets its own spacing, start and length.
  // Seeded per call, so a drawing always comes out the same.
  let calls = 0
  const jitterer = () => rng(9173 + 7919 * ++calls)
  // lines across a tube from one edge to the other, bowed a little toward `bow` of the width (cross-contours)
  function across(T, count, bow = 0.12, from = 0, to = 1, jitter = 0.4) {
    const out = [], n = T.mid.length, R = jitterer()
    for (let k = 0; k < count; k++) {
      const i = Math.max(0, Math.min(n - 1, Math.round((from + (to - from) * (k + 0.5 + jitter * (R() - 0.5)) / count) * (n - 1))))
      const a = T.left[i], b = T.right[i], w = len(sub(a, b)), t = unit(sub(T.mid[Math.min(n - 1, i + 1)], T.mid[Math.max(0, i - 1)]))
      out.push(curve([a, add(mix(a, b, 0.5), t, w * bow), b], 5))
    }
    return out
  }
  // lines along a tube, between its edges (hair strands, grain, ridges)
  function along(T, count, from = 0, to = 1, taper = true, jitter = 0.6) {
    const out = [], n = T.mid.length, R = jitterer()
    for (let k = 0; k < count; k++) {
      const v = (k + 1 + jitter * (R() - 0.5)) / (count + 1)
      const i0 = Math.round((from + (to - from) * 0.25 * R() * jitter) * (n - 1)), i1 = Math.round((to - (to - from) * 0.3 * R() * jitter) * (n - 1)), line = []
      for (let i = i0; i <= i1; i++) line.push(mix(T.left[i], T.right[i], taper ? 0.5 + (v - 0.5) * (1 - 0.6 * i / (n - 1)) : v))
      out.push(line)
    }
    return out
  }
  // a flowing lock of hair or flame: a tapering S-curve from base, curling at the tip
  function lock(base, dir, length, width, bend, curl = 0) {
    const d = unit(dir), n = perp(d), P = (a, b) => add(add(base, d, length * a), n, b)
    const spine = [P(0, 0), P(0.22, bend * 0.55), P(0.45, bend * 0.75), P(0.68, bend * 0.25), P(0.86, -bend * 0.2 + curl * 0.4), P(0.97, curl), add(P(1, curl * 1.3), n, curl * 0.25)]
    return tube(curve(spine, 8), u => width * Math.pow(1 - u, 0.8) + 0.8, 30)
  }
  // an affine placement: local coords -> drawing space
  const place = ({ x = 0, y = 0, s = 1, r = 0, flip = false } = {}) => p => {
    const q = rot([p[0] * s * (flip ? -1 : 1), p[1] * s], r); return [x + q[0], y + q[1]]
  }
  const inside = (p, poly) => { let c = false; for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) { const a = poly[i], b = poly[j]; if ((a[1] > p[1]) !== (b[1] > p[1]) && p[0] < (b[0] - a[0]) * (p[1] - a[1]) / (b[1] - a[1]) + a[0]) c = !c } return c }
  const rng = seed => () => ((seed = (seed * 16807) % 2147483647) - 1) / 2147483646

  // Packed cells (Voronoi): each point gets the region closer to it than to any neighbour. Reptile scales pack
  // like this, sharing edges, which is why they read as skin and not as bubbles.
  function clipHalf(poly, p, q) {                         // keep the side of the bisector of p-q that holds p
    const mx = (p[0] + q[0]) / 2, my = (p[1] + q[1]) / 2, nx = q[0] - p[0], ny = q[1] - p[1]
    const side = v => (v[0] - mx) * nx + (v[1] - my) * ny, out = []
    for (let i = 0; i < poly.length; i++) {
      const a = poly[i], b = poly[(i + 1) % poly.length], sa = side(a), sb = side(b)
      if (sa <= 0) out.push(a)
      if ((sa <= 0) !== (sb <= 0)) { const t = sa / (sa - sb); out.push([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]) }
    }
    return out
  }
  function cells(points, reach = 60) {
    return points.map((p, i) => {
      let poly = [[p[0] - reach, p[1] - reach], [p[0] + reach, p[1] - reach], [p[0] + reach, p[1] + reach], [p[0] - reach, p[1] + reach]]
      const near = points.map((q, j) => [j, (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2]).filter(([j]) => j !== i).sort((a, b) => a[1] - b[1]).slice(0, 12)
      for (const [j] of near) poly = clipHalf(poly, p, points[j])
      return poly
    })
  }
  // shrink a polygon toward its centre and round its corners: a scale with a crease around it
  const inset = (poly, k) => { const c = poly.reduce((a, p) => [a[0] + p[0] / poly.length, a[1] + p[1] / poly.length], [0, 0]); return { c, poly: curve(poly.map(p => mix(c, p, k)), 3, true) } }

  const SH = { cells, inset, add, sub, mix, len, unit, perp, rot, curve, circle, resample, pathLen, tube, across, along, lock, place, inside, rng }
  if (typeof module !== 'undefined' && module.exports) module.exports = SH
  else root.SH = SH
})(typeof window !== 'undefined' ? window : globalThis)
