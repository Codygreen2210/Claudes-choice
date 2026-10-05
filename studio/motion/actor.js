// actor.js: pose-to-pose character animation, with the animators' principles built into how one pose becomes the next.
// Works in the browser (window.Actor) and in node (module.exports).
//
// You give it a rig (the character's numbers and how each one behaves) and a list of beats (when to hit which pose).
// It gives back a pure function of time, so pages stay __seek(t)-driven and renders stay repeatable.
//
//   const act = Actor.perform(rig, beats, opts)
//   const p = act(t)            // every number of the character at time t
//
// rig:   { name: { v: start value, lag: seconds this part trails the beat (negative = it leads),
//                  alive: size of the tiny drift that keeps a held pose from going dead } }
// beat:  { t, pose: { name: value, ... },
//          dur:    seconds the move takes (default 0.45)
//          antic:  0..1, how much it pulls back the other way first (anticipation)
//          settle: 0..1, how much it overshoots and settles (0 = arrives and stops softly)
//          hop:    { x: 'x', y: 'y', lift } a jump: straight-line travel in x, a thrown arc in y
//          only:   skip the lags for this beat (everything hits together: an impact) }
// opts:  { plain: true } turns every principle off (ease in and out, all parts together): the "before" to compare with.
//
// What it does between poses, and which principle each is:
//   anticipation       a small move the wrong way before the real one
//   slow in, slow out  every move eases; the settle is a damped spring, not a stop
//   follow-through     the spring passes the pose and comes back
//   overlapping action each part starts on its own lag: eyes lead, the body goes, arms and loose bits trail
//   arcs               hops travel on a thrown arc; Actor.squash() gives stretch along the path and squash on landing
//   moving hold        held poses keep a little life
(function (root) {
  const clamp = (x, a = 0, b = 1) => x < a ? a : x > b ? b : x
  const hash = x => { const s = Math.sin(x * 127.1) * 43758.5453; return (s - Math.floor(s)) * 2 - 1 }
  const sm = p => p * p * (3 - 2 * p)
  const noise = x => { const i = Math.floor(x), f = x - i; return hash(i) + (hash(i + 1) - hash(i)) * sm(f) }
  const io = p => p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2
  // step response of a damped spring, time in units of the move's length: 0 at u=0, settles on 1
  function settleCurve(u, o) {
    if (u <= 0) return 0
    // slow in: time itself starts gently, so the move gathers speed over a few frames instead of leaving at once
    // (the motion critic called the first version a jolt: it reached full speed in under 3 frames)
    u = u < 1 ? Math.pow(u, 1.45) : 1 + 1.45 * (u - 1)
    const k = 5.6, w = o * 10
    if (w < 0.05) return 1 - Math.exp(-k * u) * (1 + k * u)
    return 1 - Math.exp(-k * u) * (Math.cos(w * u) + (k / w) * Math.sin(w * u))
  }
  function perform(rig, beats, opts = {}) {
    const plain = !!opts.plain, names = Object.keys(rig)
    const list = {}
    names.forEach(n => list[n] = [])
    beats.slice().sort((a, b) => a.t - b.t).forEach(b => {
      for (const n of Object.keys(b.pose || {})) {
        if (!(n in rig)) throw new Error('actor: beat sets "' + n + '", which is not in the rig')
        const lag = plain || b.only ? 0 : (rig[n].lag || 0)
        list[n].push({ t0: b.t + lag, to: b.pose[n], dur: b.dur || 0.45, antic: plain ? 0 : (b.antic || 0), settle: plain ? 0 : (b.settle == null ? 0.35 : b.settle), hop: b.hop || null })
      }
    })
    function value(n, t, upto) {
      const L = list[n]; let i = (upto == null ? L.length : upto) - 1
      while (i >= 0 && L[i].t0 > t) i--
      if (i < 0) return rig[n].v
      const m = L[i], a = value(n, m.t0, i), d = m.to - a, u = (t - m.t0) / m.dur
      if (m.hop && (n === m.hop.x || n === m.hop.y)) return a + d * clamp(u)                 // thrown: constant travel, no easing
      if (plain) return a + d * io(clamp(u))
      const fa = m.antic > 0 ? 0.3 : 0
      if (u < fa) return a - d * 0.22 * m.antic * Math.sin(Math.PI / 2 * (u / fa))
      const from = a - d * 0.22 * m.antic
      return from + (m.to - from) * settleCurve((u - fa) / (1 - fa), m.settle)
    }
    const hops = beats.filter(b => b.hop)
    return function at(t) {
      const p = {}
      for (const n of names) {
        p[n] = value(n, t)
        if (!plain && rig[n].alive) p[n] += rig[n].alive * noise(t * 0.55 + n.length * 17.3 + n.charCodeAt(0))
      }
      p.air = 0
      for (const h of hops) { const u = (t - h.t) / (h.dur || 0.45); if (u > 0 && u < 1) { p[h.hop.y] -= h.hop.lift * 4 * u * (1 - u); p.air = 1 } }
      return p
    }
  }
  // stretch along the direction of travel, keeping volume. Give it the act, the time, and the two position names.
  // Returns { sx, sy, angle }: scale sy along the path (angle), sx across it.
  function squash(act, t, xn = 'x', yn = 'y', amt = 0.00028, max = 1.3) {
    const h = 1 / 120, a = act(t - h), b = act(t + h), vx = (b[xn] - a[xn]) / (2 * h), vy = (b[yn] - a[yn]) / (2 * h), sp = Math.hypot(vx, vy)
    const s = Math.min(max, 1 + sp * amt)
    return { sy: s, sx: 1 / s, angle: sp > 40 ? Math.atan2(vy, vx) - Math.PI / 2 : 0, speed: sp }
  }
  // when to blink: a little before each big look, and now and then while holding. Returns 0 (open) .. 1 (shut).
  function blink(beats, t, lookName = 'lookX', every = 3.4) {
    let c = 1e9
    for (const b of beats) if (b.pose && lookName in b.pose) c = Math.min(c, Math.abs(t - (b.t - 0.02)))
    const k = Math.floor(t / every), tk = k * every + 1.3 + hash(k) * 0.6
    c = Math.min(c, Math.abs(t - tk))
    return c < 0.045 ? 1 : c < 0.09 ? 0.5 : 0
  }
  const api = { perform, squash, blink, settleCurve }
  if (typeof module !== 'undefined' && module.exports) module.exports = api
  root.Actor = api
})(typeof window !== 'undefined' ? window : globalThis)
