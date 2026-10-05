// clock.js: the cheetah's running clock. How many strides a second she takes at each moment of the film,
// keyed to the voice (cues.js). film.html draws from it; events.cjs uses the same clock for footfall sounds.
(function (root) {
  const C = root.CUES, cue = {}; C.cues.forEach(c => cue[c.id] = c)
  const STRIDE_PX = 1280                     // ground covered in one stride, in drawing units (stands for about 7 m)
  // [time, strides per second]; straight lines between
  const go = cue.go.t0 + 0.5
  const keys = [[0, 0], [go, 0], [go + 1.6, 3.3], [cue.slow.t0, 3.3], [cue.slow.t0 + 0.9, 0.45], [cue.stride.t0 + 1.0, 0.45], [cue.stride.t0 + 1.3, 0.2], [cue.air.t0 - 0.1, 0.2], [cue.air.t0, 0],   // one slow stride while it is measured
    [cue.inside.t0 - 0.2, 0], [cue.inside.t0 + 0.4, 0.55], [cue.claws.t0 - 0.2, 0.55], [cue.claws.t0 + 0.4, 0.3], [cue.turn.t0, 0.3],
    [cue.short.t0 - 0.3, 0.3], [cue.short.t0 + 0.2, 3.0], [cue.short.t0 + 2.6, 3.0], [cue.short.t0 + 5.2, 0], [C.dur + 10, 0]]
  function rate(t) { for (let i = 0; i < keys.length - 1; i++) if (t <= keys[i + 1][0]) { const [a, ra] = keys[i], [b, rb] = keys[i + 1]; return ra + (rb - ra) * (t - a) / (b - a || 1) } return 0 }
  const HZ = 240, N = Math.ceil((C.dur + 2) * HZ), table = new Float64Array(N + 1)
  for (let i = 1; i <= N; i++) table[i] = table[i - 1] + rate((i - 0.5) / HZ) / HZ
  const sm = p => p < 0 ? 0 : p > 1 ? 1 : p * p * (3 - 2 * p)
  // during "all four feet are off the ground" she is stepped by hand to the stretched pose, then the tucked pose
  const base = table[Math.round(cue.air.t0 * HZ)], f0 = base - Math.floor(base)
  const toStretch = ((0.30 - f0) % 1 + 1) % 1, half = cue.air.t0 + (cue.air.t1 - cue.air.t0) * 0.62
  const extra = t => toStretch * sm((t - cue.air.t0 - 1.6) / 0.7) + 0.52 * sm((t - half) / 0.7)
  function phase(t) { const x = Math.max(0, Math.min(N, t * HZ)), i = Math.floor(x), f = x - i; return table[i] + (table[Math.min(N, i + 1)] - table[i]) * f + extra(t) }
  // how much she is running at all (0 standing, 1 galloping), for blending the stand pose
  const run = t => Math.min(sm((t - go) / 0.5), 1 - sm((t - (cue.short.t0 + 4.4)) / 1.0))
  // footfalls: the phase at which each foot lands (hind, hind, fore, fore)
  const LANDS = [0.92, 0.99, 0.45, 0.52]
  function footfalls() {
    const out = []; let prev = phase(0)
    for (let i = 1; i <= C.dur * 120; i++) {
      const t = i / 120, p = phase(t)
      for (let k = 0; k < 4; k++) if (Math.floor(p - LANDS[k]) > Math.floor(prev - LANDS[k]) && run(t) > 0.5) out.push({ t: +t.toFixed(3), foot: k, rate: +(rate(t) || (p - prev) * 120).toFixed(2) })
      prev = p
    }
    return out
  }
  root.CLOCK = { cue, rate, phase, run, footfalls, STRIDE_PX, LANDS }
})(typeof window !== 'undefined' ? window : globalThis)
