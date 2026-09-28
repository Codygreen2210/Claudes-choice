// timelapse.js: draw by recording strokes, then replay the drawing as a speed-paint video.
//
// Two halves:
//   1. The recorder. A drawing is made with a few tools, and every stroke is stored as data: tool, layer,
//      colour, width, and points [x, y, pressure, t] where t is when the pen reached that point. Time comes
//      from a simple hand model: the pen moves at the tool's speed, slows into corners, and lifts between
//      strokes. The recording is plain JSON (rec.toJSON()), so it can be saved, inspected and replayed.
//   2. The player. TL.player(canvas, rec, opts) gives a __seek(t)-style draw(t) that shows the drawing as it
//      stood at recorded time t, with the stroke in progress drawn up to the pen and a pencil at the tip.
//      TL.timeline(rec, opts) maps video time to drawing time: a speed-up, plus holds on each step's caption
//      and on the finished piece.
//
// Tools:
//   pencil  thin, grainy graphite for construction guides (layer 'guide' by default)
//   ink     smooth tapered line whose width follows pressure (layer 'line')
//   brush   a flat paint stroke with soft edges (layer 'color'); give it a clip region to stay inside
//   fill    paints a region with back-and-forth brush strokes, the way a person actually fills an area
//   erase   fades a whole layer out over its duration (used to clear the guides after inking)
//
// Layers are drawn bottom to top in the order given by opts.layers (default: color, shade, line, guide, top).
// Coordinates are whatever space the drawing uses; the player maps it into a box on the canvas.
(function (root) {
  const hyp = (a, b) => Math.hypot(b[0] - a[0], b[1] - a[1])

  // ---------------------------------------------------------------- recorder
  const TOOLS = {
    pencil: { speed: 900, layer: 'guide', width: 3, color: '#7a8fb0' },
    ink: { speed: 650, layer: 'line', width: 7, color: '#1d1b22' },
    brush: { speed: 1100, layer: 'color', width: 40, color: '#888' },
    fill: { speed: 2600, layer: 'color', width: 46, color: '#888' },
    erase: { layer: 'guide' },
  }

  // Resample a path so points are evenly spaced, then give each a pressure and a time.
  // Pressure rises from 0.25 at touch-down, holds, and falls at lift-off: that is where the taper comes from.
  function timePath(pts, speed, t0, step = 6) {
    const out = []
    if (pts.length === 1) return [[pts[0][0], pts[0][1], 1, t0]]
    const seg = []; let total = 0
    for (let i = 1; i < pts.length; i++) { const d = hyp(pts[i - 1], pts[i]); seg.push(d); total += d }
    const N = Math.max(2, Math.ceil(total / step))
    let i = 0, acc = 0
    for (let k = 0; k <= N; k++) {
      let s = total * k / N
      while (i < seg.length - 1 && s > acc + seg[i]) { acc += seg[i]; i++ }
      const p = seg[i] ? (s - acc) / seg[i] : 0, a = pts[i], b = pts[i + 1]
      out.push([a[0] + (b[0] - a[0]) * p, a[1] + (b[1] - a[1]) * p])
    }
    // speed: a hand accelerates off the paper and slows at corners and at the end
    let t = t0
    for (let k = 0; k <= N; k++) {
      const u = k / N
      const pressure = Math.min(1, 0.25 + 3 * u) * Math.min(1, 0.25 + 3 * (1 - u))
      if (k > 0) {
        const d = hyp(out[k - 1], out[k])
        let turn = 0
        if (k < N) {
          const a = [out[k][0] - out[k - 1][0], out[k][1] - out[k - 1][1]], b = [out[k + 1][0] - out[k][0], out[k + 1][1] - out[k][1]]
          const la = Math.hypot(...a) || 1, lb = Math.hypot(...b) || 1
          turn = 1 - (a[0] * b[0] + a[1] * b[1]) / (la * lb)       // 0 straight, 2 reversal
        }
        const ramp = 0.45 + 0.55 * Math.sin(Math.PI * Math.min(1, u * 1.1))
        t += d / (speed * ramp / (1 + 1.5 * turn))
      }
      out[k].push(pressure, t)
    }
    return out
  }

  // Straight lines at an angle across a polygon, `spacing` apart, each trimmed to the polygon.
  function lanes(region, spacing, angle) {
    const c = Math.cos(angle), s = Math.sin(angle)
    const rot = ([x, y]) => [x * c + y * s, -x * s + y * c], unrot = ([u, v]) => [u * c - v * s, u * s + v * c]
    const r = region.map(rot), out = []
    const v0 = Math.min(...r.map(p => p[1])), v1 = Math.max(...r.map(p => p[1]))
    for (let v = v0 + spacing / 2, k = 0; v < v1; v += spacing, k++) {
      const xs = []
      for (let i = 0; i < r.length; i++) {
        const a = r[i], b = r[(i + 1) % r.length]
        if ((a[1] <= v) !== (b[1] <= v)) xs.push(a[0] + (v - a[1]) / (b[1] - a[1]) * (b[0] - a[0]))
      }
      xs.sort((a, b) => a - b)
      for (let i = 0; i + 1 < xs.length; i += 2) out.push(k % 2 ? [unrot([xs[i + 1], v]), unrot([xs[i], v])] : [unrot([xs[i], v]), unrot([xs[i + 1], v])])
    }
    return out
  }

  // Hatching lanes with a hand: each line's own spacing, angle and length.
  function jitterLanes(region, spacing, angle, amt, R) {
    const out = []
    for (const base of lanes(region, spacing * 0.5, angle)) {
      if (R() < 0.5) continue                                             // uneven spacing: keep about half the fine lanes
      const [a, b] = base, dx = b[0] - a[0], dy = b[1] - a[1], tw = (R() - 0.5) * 0.12 * amt
      const s0 = 0.12 * amt * R(), s1 = 1 - 0.18 * amt * R()                  // start late, stop early
      const mid = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2], c = Math.cos(tw), sn = Math.sin(tw)
      const P = u => { const x = a[0] + dx * u - mid[0], y = a[1] + dy * u - mid[1]; return [mid[0] + x * c - y * sn, mid[1] + x * sn + y * c] }
      out.push([P(s0), P(s1)])
    }
    return out
  }

  // Back-and-forth strokes covering a polygon's bounding box, angled, spaced by the brush width.
  function scribble(region, width, angle = -0.5) {
    const c = Math.cos(angle), s = Math.sin(angle)
    const rot = ([x, y]) => [x * c + y * s, -x * s + y * c], unrot = ([u, v]) => [u * c - v * s, u * s + v * c]
    const r = region.map(rot)
    const u0 = Math.min(...r.map(p => p[0])), u1 = Math.max(...r.map(p => p[0]))
    const v0 = Math.min(...r.map(p => p[1])), v1 = Math.max(...r.map(p => p[1]))
    const lanes = []
    for (let v = v0 + width * 0.35, k = 0; v < v1 + width * 0.35; v += width * 0.7, k++) {
      // clip the lane to the polygon so the brush only travels where paint goes
      const xs = []
      for (let i = 0; i < r.length; i++) {
        const a = r[i], b = r[(i + 1) % r.length]
        if ((a[1] <= v) !== (b[1] <= v)) xs.push(a[0] + (v - a[1]) / (b[1] - a[1]) * (b[0] - a[0]))
      }
      if (xs.length < 2) continue
      const lo = Math.min(...xs) - width * 0.3, hi = Math.max(...xs) + width * 0.3
      lanes.push(k % 2 ? [[hi, v], [lo, v]] : [[lo, v], [hi, v]])
    }
    // join lanes into one zigzag so it is drawn as a single continuous gesture
    const path = []
    for (const l of lanes) path.push(unrot(l[0]), unrot(l[1]))
    return path.length ? path : [unrot([u0, v0])]
  }

  // ---------------------------------------------------------------- the hand
  // A person never draws the same line twice. With hand > 0, pencil and ink strokes get:
  //   overshoot   the line runs a few px past where it was meant to start and stop
  //   wobble      a slow drift and a small tremor across the line
  //   pressure    each stroke has its own weight, and the weight wavers along it
  //   breaks      long lines sometimes lift for a moment (lost edges)
  //   restating   some long ink lines get a second, lighter pass that doesn't quite match
  // It is seeded per stroke, so the same drawing always comes out the same.
  const rng = seed => () => ((seed = (seed * 16807) % 2147483647) - 1) / 2147483646
  function handPath(pts, amt, R) {
    if (pts.length < 2 || amt <= 0) return pts
    const out = pts.map(p => [p[0], p[1]])
    const dir = (a, b) => { const dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1; return [dx / l, dy / l] }
    const o0 = amt * (1 + 6 * R()) * (R() < 0.6 ? 1 : 0), o1 = amt * (1 + 7 * R()) * (R() < 0.7 ? 1 : 0)
    const d0 = dir(out[1], out[0]), d1 = dir(out[out.length - 2], out[out.length - 1])
    out.unshift([out[0][0] + d0[0] * o0, out[0][1] + d0[1] * o0])
    out.push([out[out.length - 1][0] + d1[0] * o1, out[out.length - 1][1] + d1[1] * o1])
    return out
  }
  function handWobble(timed, amt, R) {
    // perpendicular offset: a slow drift plus a finer tremor, measured along the line's length. Both are smooth
    // random noise, not sine waves: a sine is itself a perfect repeat, which is exactly what a hand never does.
    const noise = (step, R) => { const k = []; return x => { const i = Math.floor(x / step), u = x / step - i; while (k.length <= i + 1) k.push(R() * 2 - 1); const e = u * u * (3 - 2 * u); return k[i] + (k[i + 1] - k[i]) * e } }
    const drift = noise(50 + 80 * R(), R), tremor = noise(7 + 7 * R(), R), weight = noise(30 + 40 * R(), R)
    const a1 = amt * (0.8 + 1.8 * R()), a2 = amt * 0.5, peak = 0.72 + 0.4 * R()
    let s = 0
    for (let i = 0; i < timed.length; i++) {
      const a = timed[Math.max(0, i - 1)], b = timed[Math.min(timed.length - 1, i + 1)]
      if (i > 0) s += Math.hypot(timed[i][0] - timed[i - 1][0], timed[i][1] - timed[i - 1][1])
      const dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1
      const off = a1 * drift(s) + a2 * tremor(s)
      timed[i][0] += -dy / l * off; timed[i][1] += dx / l * off
      timed[i][2] *= peak * (1 + 0.3 * amt * weight(s))
    }
    // a lost edge: long lines sometimes lift for a moment
    if (s > 140 && R() < 0.45 * amt) {
      const at = 0.25 + 0.5 * R(), span = (6 + 10 * R()) / s
      for (const p of timed) { const u = timed.indexOf(p) / (timed.length - 1); if (Math.abs(u - at) < span / 2) p[2] = -1 }
    }
    return timed
  }

  function recorder({ lift = 0.18, stepPause = 0.4, hand = 0, seed = 1 } = {}) {
    const strokes = [], steps = []
    let t = 0, id = 0
    const add = (tool, pts, o = {}) => {
      const T = { ...TOOLS[tool], ...o }
      const start = t + (strokes.length ? (o.lift ?? lift) : 0)
      const amt = (tool === 'ink' || tool === 'pencil') ? (o.hand ?? hand) : 0
      const R = rng(seed * 7919 + id * 104729 + 17)
      if (amt > 0) pts = handPath(pts, amt, R)
      let timed = timePath(pts, T.speed, start, tool === 'fill' ? 12 : 6)
      if (amt > 0) timed = handWobble(timed, amt, R)
      // weight: a pressure curve along the stroke (0..1 of its length), e.g. heavy in shadow, light in the light
      if (o.weight) timed.forEach((p, i) => { if (p[2] >= 0) p[2] *= o.weight(i / Math.max(1, timed.length - 1)) })
      const st = { id: id++, tool, layer: T.layer, color: T.color, width: T.width, alpha: o.alpha ?? 1,
        clip: o.clip || null, mask: o.mask || null, soft: o.soft || 0, grain: o.grain ?? (tool === 'pencil' ? 1 : 0), pts: timed, t0: start, t1: timed[timed.length - 1][3], step: steps.length - 1 }
      strokes.push(st); t = st.t1
      const len = timed.reduce((acc, p, i) => i ? acc + Math.hypot(p[0] - timed[i - 1][0], p[1] - timed[i - 1][1]) : 0, 0)
      if (tool === 'ink' && amt > 0 && !o.restate && len > 90 && R() < 0.3 * amt) {
        const a = Math.floor(timed.length * 0.1 * R()), b = Math.ceil(timed.length * (0.55 + 0.4 * R()))
        const shift = amt * (1 + 1.5 * R()), part = timed.slice(a, b).map(p => [p[0] + shift, p[1] + shift * 0.6])
        if (part.length > 1) add(tool, part, { ...o, restate: true, alpha: (o.alpha ?? 1) * 0.4, width: (o.width ?? T.width) * 0.7, lift: 0.04 })
      }
      return st
    }
    const rec = {
      strokes, steps,
      get duration() { return t },
      step(title, note = '') { t += steps.length ? stepPause : 0; steps.push({ i: steps.length, title, note, t }); return rec },
      pencil(pts, o) { add('pencil', pts, o); return rec },
      ink(pts, o) { add('ink', pts, o); return rec },
      brush(pts, o) { add('brush', pts, o); return rec },
      // fill a polygon region: the scribble is clipped to the region so edges stay clean
      fill(region, o = {}) { add('fill', scribble(region, o.width ?? TOOLS.fill.width, o.angle), { ...o, clip: region }); return rec },
      // parallel pencil lines across a region, each its own quick stroke (shading by hatching)
      // With a hand, hatching is uneven the way a person's is: spacing wanders, the angle drifts a little, lines
      // start and stop short of the edge, and some come out lighter.
      hatch(region, o = {}) {
        const amt = o.hand ?? hand, R = rng(seed * 31 + id * 7 + 5), sp = o.spacing ?? 8
        const ls = amt > 0 ? jitterLanes(region, sp, o.angle ?? -0.8, amt, R) : lanes(region, sp, o.angle ?? -0.8)
        for (const l of ls) add(o.tool || 'ink', l, { lift: 0.02, width: 1.6, ...o, alpha: (o.alpha ?? 1) * (amt > 0 ? 0.65 + 0.35 * R() : 1), clip: region })
        return rec
      },
      erase(layer, dur = 1.2) {
        const start = t + lift
        strokes.push({ id: id++, tool: 'erase', layer, pts: [], t0: start, t1: start + dur, step: steps.length - 1 })
        t = start + dur; return rec
      },
      wait(s) { t += s; return rec },
      toJSON() { return { version: 1, duration: t, steps, strokes } },
    }
    return rec
  }

  // Load a saved recording back into the same shape the recorder produces.
  const load = json => ({ ...json, get duration() { return json.duration }, toJSON: () => json })

  // ---------------------------------------------------------------- timeline: video time -> drawing time
  // speed: drawing seconds per video second. holdStep: video seconds to pause on each new step's caption.
  // intro / outro: seconds before the first stroke and after the last (the finished piece holds).
  function timeline(rec, { speed = 4, holdStep = 1.0, intro = 2.5, outro = 3 } = {}) {
    const marks = []                                      // [videoT, drawT] knots, piecewise linear
    let v = intro
    marks.push([0, 0], [v, 0])
    let prev = 0
    const sp = i => typeof speed === 'function' ? speed(rec.steps[i], i) : speed
    const hold = i => typeof holdStep === 'function' ? holdStep(rec.steps[i], i) : holdStep
    rec.steps.forEach((s, i) => {
      if (i > 0) { v += (s.t - prev) / sp(i - 1); marks.push([v, s.t]) }
      v += hold(i); marks.push([v, s.t]); prev = s.t
    })
    v += (rec.duration - prev) / sp(rec.steps.length - 1); marks.push([v, rec.duration])
    v += outro; marks.push([v, rec.duration])
    const draw = vt => {
      if (vt <= 0) return 0
      for (let i = 1; i < marks.length; i++) {
        const [a, x] = marks[i - 1], [b, y] = marks[i]
        if (vt <= b) return b === a ? y : x + (y - x) * (vt - a) / (b - a)
      }
      return rec.duration
    }
    // which step is showing, and how long into its caption hold we are (for fading captions)
    const stepAt = vt => {
      const dt = draw(vt); let cur = null
      for (const s of rec.steps) if (s.t <= dt + 1e-9) cur = s
      return cur
    }
    // the first video time at which the drawing reaches drawing-time dt (for syncing sound to strokes)
    const videoTimeOf = dt => {
      // skip the intro knot pair; a hold (flat segment) is reached at its start, not its end
      for (let i = 2; i < marks.length; i++) {
        const [a, x] = marks[i - 1], [b, y] = marks[i]
        if (x <= dt && dt <= y) return y === x ? a : a + (b - a) * (dt - x) / (y - x)
      }
      return v - outro
    }
    return { duration: v, draw, stepAt, videoTimeOf, marks, intro, outro }
  }

  // ---------------------------------------------------------------- player
  // Strokes finished before time t are baked once onto per-layer canvases; only the live stroke is redrawn
  // each frame. Going backwards in time rebuilds the bake, so any frame can be drawn in any order.
  function player(canvas, rec, { box = [0, 0, canvas.width, canvas.height], space = [1000, 1000],
    layers = ['color', 'shade', 'line', 'guide', 'top'], paper = '#f4efe4', pencilTip = true, tooth = 0, overTooth = ['deep', 'top'] } = {}) {
    // paper tooth: graphite catches only the raised grain of the paper, so dark marks break up at a fine scale.
    // One fixed texture (seeded), lightened over the drawing, so it never shimmers from frame to frame.
    let toothTex = null
    if (tooth > 0) {
      // grain clumps about 2 px across: made at half size and scaled up smoothly
      const small = document.createElement('canvas'); small.width = Math.ceil(canvas.width / 2); small.height = Math.ceil(canvas.height / 2)
      const tg = small.getContext('2d'), img = tg.createImageData(small.width, small.height), R = rng(4242)
      const pc = paper.match(/[0-9a-f]{2}/gi).map(h => parseInt(h, 16))
      for (let i = 0; i < img.data.length; i += 4) {
        const v = R(), a = v > 0.72 ? (v - 0.72) / 0.28 : 0                   // only some grains stand proud
        img.data[i] = pc[0]; img.data[i + 1] = pc[1]; img.data[i + 2] = pc[2]; img.data[i + 3] = 255 * tooth * a
      }
      tg.putImageData(img, 0, 0)
      toothTex = document.createElement('canvas'); toothTex.width = canvas.width; toothTex.height = canvas.height
      const big = toothTex.getContext('2d'); big.imageSmoothingEnabled = true; big.drawImage(small, 0, 0, canvas.width, canvas.height)
    }
    const [bx, by, bw, bh] = box, k = Math.min(bw / space[0], bh / space[1])
    const ox = bx + (bw - space[0] * k) / 2, oy = by + (bh - space[1] * k) / 2
    const X = p => ox + p[0] * k, Y = p => oy + p[1] * k
    const L = {}
    for (const name of layers) { const c = document.createElement('canvas'); c.width = canvas.width; c.height = canvas.height; L[name] = { c, g: c.getContext('2d'), alpha: 1 } }
    const g = canvas.getContext('2d')
    let baked = 0, bakedT = -1

    function clipTo(ctx, region) { ctx.beginPath(); region.forEach((p, i) => i ? ctx.lineTo(X(p), Y(p)) : ctx.moveTo(X(p), Y(p))); ctx.closePath(); ctx.clip() }

    // draw points pts[0..n) plus a final interpolated point, onto ctx
    function paint(ctx, st, pts) {
      if (pts.length < 1) return
      ctx.save()
      if (st.clip) clipTo(ctx, st.clip)
      // masks: regions the stroke must stay out of (things in front of it). One clip per mask, so overlaps stay masked.
      if (st.mask) for (const m of st.mask) {
        ctx.beginPath(); ctx.rect(0, 0, ctx.canvas.width, ctx.canvas.height)
        m.forEach((p, i) => i ? ctx.lineTo(X(p), Y(p)) : ctx.moveTo(X(p), Y(p))); ctx.closePath(); ctx.clip('evenodd')
      }
      if (st.soft) ctx.filter = `blur(${st.soft * k}px)`
      ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.strokeStyle = st.color; ctx.fillStyle = st.color
      if (st.tool === 'ink' || st.tool === 'pencil') {
        // pressure-width segments; pencil adds grain by breaking alpha along the line
        for (let i = 1; i < pts.length; i++) {
          const a = pts[i - 1], b = pts[i]
          if (a[2] < 0 || b[2] < 0) continue                               // the pen lifted here
          ctx.lineWidth = Math.max(0.6, st.width * k * (st.tool === 'ink' ? 0.2 + 0.8 * (a[2] + b[2]) / 2 : 1))
          ctx.globalAlpha = st.alpha * (1 - (st.grain ?? 0) * (0.45 - 0.35 * (((i * 7919 + st.id * 31) % 13) / 13)))
          ctx.beginPath(); ctx.moveTo(X(a), Y(a)); ctx.lineTo(X(b), Y(b)); ctx.stroke()
        }
        if (pts.length === 1) { ctx.globalAlpha = st.alpha; ctx.beginPath(); ctx.arc(X(pts[0]), Y(pts[0]), st.width * k / 2, 0, 7); ctx.fill() }
      } else {
        // brush / fill: one wide soft stroke, a core and a lighter halo so overlaps build up like paint
        const path = () => { ctx.beginPath(); pts.forEach((p, i) => i ? ctx.lineTo(X(p), Y(p)) : ctx.moveTo(X(p), Y(p))) }
        ctx.globalAlpha = st.alpha * 0.45; ctx.lineWidth = st.width * k * 1.15; path(); ctx.stroke()
        ctx.globalAlpha = st.alpha * 0.9; ctx.lineWidth = st.width * k * 0.8; path(); ctx.stroke()
      }
      ctx.restore()
    }

    const upTo = (st, t) => {
      const out = []
      for (let i = 0; i < st.pts.length; i++) {
        const p = st.pts[i]
        if (p[3] <= t) { out.push(p); continue }
        if (i > 0) { const a = st.pts[i - 1], u = (t - a[3]) / (p[3] - a[3]); out.push([a[0] + (p[0] - a[0]) * u, a[1] + (p[1] - a[1]) * u, a[2], t]) }
        break
      }
      return out
    }

    function reset() {
      for (const n in L) { L[n].g.clearRect(0, 0, canvas.width, canvas.height); L[n].alpha = 1 }
      baked = 0; bakedT = -1
    }

    function draw(t) {
      if (t < bakedT) reset()
      const S = rec.strokes
      // bake every stroke that is finished by t
      while (baked < S.length && S[baked].t1 <= t) {
        const st = S[baked]
        if (st.tool === 'erase') { L[st.layer].alpha = 0 } else paint(L[st.layer].g, st, st.pts)
        baked++
      }
      bakedT = t
      g.save(); g.setTransform(1, 0, 0, 1, 0, 0)
      g.fillStyle = paper; g.fillRect(0, 0, canvas.width, canvas.height)
      // the live stroke, if any, goes on top of its own layer
      const live = baked < S.length && S[baked].t0 <= t ? S[baked] : null
      let livePts = null, eraseA = null
      if (live && live.tool === 'erase') eraseA = 1 - (t - live.t0) / (live.t1 - live.t0)
      else if (live) livePts = upTo(live, t)
      let toothDone = false
      for (const name of layers) {
        // layers listed in overTooth sit above the paper grain (graphite packed hard enough to fill it)
        if (toothTex && !toothDone && overTooth.includes(name)) { g.drawImage(toothTex, 0, 0); toothDone = true }
        const a = live && live.tool === 'erase' && live.layer === name ? eraseA : L[name].alpha
        if (a > 0) { g.globalAlpha = a; g.drawImage(L[name].c, 0, 0); g.globalAlpha = 1 }
        if (livePts && live.layer === name) paint(g, live, livePts)
      }
      if (toothTex && !toothDone) g.drawImage(toothTex, 0, 0)
      g.restore()
      // where the pen is: during a stroke, at its tip; between strokes, gliding to the next start
      let tip = null
      if (livePts && livePts.length) tip = livePts[livePts.length - 1]
      else if (!live) {
        const prev = S[baked - 1], next = S[baked]
        const a = prev && prev.pts.length ? prev.pts[prev.pts.length - 1] : null, b = next && next.pts.length ? next.pts[0] : null
        if (a && b) { const u = Math.min(1, Math.max(0, (t - prev.t1) / Math.max(1e-6, next.t0 - prev.t1))); const e = u * u * (3 - 2 * u); tip = [a[0] + (b[0] - a[0]) * e, a[1] + (b[1] - a[1]) * e, 0] }
      }
      return { tip: tip ? [X(tip), Y(tip), tip[2]] : null, tool: live ? live.tool : (S[baked] || S[baked - 1] || {}).tool, color: live ? live.color : (S[baked] || {}).color }
    }

    // a pencil drawn at the tip, leaning like a right hand holds it
    function drawPen(state, tool) {
      if (!pencilTip || !state.tip || tool === 'erase') return
      const [x, y, p] = state.tip, s = canvas.width / 1080
      g.save(); g.translate(x, y - (1 - p) * 6 * s); g.rotate(-0.6)
      const len = 260 * s, w = 26 * s
      g.shadowColor = 'rgba(0,0,0,0.18)'; g.shadowBlur = 18 * s; g.shadowOffsetX = 10 * s; g.shadowOffsetY = 14 * s
      const body = tool === 'ink' ? '#2b2b33' : tool === 'pencil' ? '#e8b440' : '#c9824a'
      g.fillStyle = body; g.fillRect(-w / 2, -len, w, len - 40 * s)
      g.shadowColor = 'transparent'
      g.fillStyle = tool === 'pencil' ? '#efd3a8' : '#d8d2c8'
      g.beginPath(); g.moveTo(-w / 2, -40 * s); g.lineTo(w / 2, -40 * s); g.lineTo(0, 0); g.closePath(); g.fill()
      g.fillStyle = tool === 'pencil' ? '#555' : state.color || '#222'
      g.beginPath(); g.moveTo(-w / 6, -13 * s); g.lineTo(w / 6, -13 * s); g.lineTo(0, 0); g.closePath(); g.fill()
      g.restore()
    }

    return { draw: t => { const st = draw(t); drawPen(st, st.tool); return st }, reset, map: p => [X(p), Y(p)], scale: k }
  }

  const TL = { recorder, load, timeline, player, TOOLS, _timePath: timePath, _scribble: scribble, _lanes: lanes }
  if (typeof module !== 'undefined' && module.exports) module.exports = TL
  else root.TL = TL
})(typeof window !== 'undefined' ? window : globalThis)
