// plan.js: when the real machine runs during the story video. Times come from the voice (cues.js).
// Used by film.html (pictures) and events.cjs (sound), so both follow the same marbles.
(function (root) {
  const C = root.CUES, cue = {}; C.cues.forEach(c => cue[c.id] = c)
  const q = t => Math.ceil(t * 2) / 2                 // start machines on the half-second so bounces sit on the beat
  const A = root.LAYOUT.A, DROP = root.LAYOUT.dropX
  // the first try: these five lines, with the bounce at 0.86. Each marble rings one line and misses the rest.
  const OLD = { dropX: 300, rest: 0.86, lines: [
    { x1: 210, y1: 330, x2: 470, y2: 400 }, { x1: 560, y1: 620, x2: 830, y2: 560 }, { x1: 260, y1: 860, x2: 560, y2: 930 },
    { x1: 640, y1: 1130, x2: 800, y2: 1090 }, { x1: 330, y1: 1330, x2: 520, y2: 1370 } ] }
  const m1 = q(cue.built.t0 + 0.4), f = q(cue.bouncy.t0 + 1.2), m1b = q(cue.fix.t0 + 3.2), m2 = q(cue.honest.t0)
  const r = cue.rule.t0
  const sims = {
    // building it: four lines go up while the tools are named, then the long one, the short one, and the last
    m1: { t0: m1, dropX: DROP, births: [1, cue.fail.t0 - 4.2 - m1], adds: [m1 + 0.4, m1 + 2.0, m1 + 3.6, m1 + 5.2, r + 0.2, r + 2.6, r + 5.0].map((t, i) => ({ t, line: A[i] })) },
    fail: { t0: f, dropX: OLD.dropX, rest: OLD.rest, births: [0, cue.onenote.t1 - 0.3 - f], adds: OLD.lines.map(line => ({ t: f - 1, line })) },
    // after the fix: the search drops the seven lines in quickly, then it plays
    m1b: { t0: m1b, dropX: DROP, births: [0, cue.video.t0 - 1.2 - m1b], adds: A.map((line, i) => ({ t: m1b - 1.75 + i * 0.25, line })) },
    m2: { t0: m2, dropX: DROP, births: [0, cue.bye.t1 + 1.0 - m2], adds: A.map((line, i) => ({ t: m2 - 0.9 + i * 0.12, line })) },
  }
  const cache = {}
  // run one machine up to global time t; returns { sim, hits } with hit times in global seconds
  function at(Sim, id, t) {
    const d = sims[id]
    let c = cache[id]
    if (!c || c.sim.time + d.t0 > t + 1e-9) {
      const hits = []
      const sim = Sim.create({ H: 1560, dropX: d.dropX, interval: 1, rest: d.rest, onHit: e => hits.push({ t: e.t + d.t0, k: e.line.k, midi: e.midi, vel: e.vel, x: e.x, y: e.y }) })
      d.adds.forEach((a, k) => { if (a.t <= d.t0) sim.lines.push(Object.assign({ k }, a.line)) })
      c = cache[id] = { sim, hits, ai: d.adds.filter(a => a.t <= d.t0).length }
    }
    const sim = c.sim
    while (sim.time + d.t0 + Sim.DT / 2 < t) {
      while (c.ai < d.adds.length && d.adds[c.ai].t <= sim.time + d.t0 + 1e-9) { sim.lines.push(Object.assign({ k: c.ai }, d.adds[c.ai].line)); c.ai++ }
      sim.paused = !(sim.time >= d.births[0] - 1e-9 && sim.time <= d.births[1] + 1e-9)
      Sim.tick(sim)
    }
    return c
  }
  root.PLAN = { cue, sims, at, dur: Math.max(C.dur, Math.ceil(m2 + sims.m2.births[1] + 6.5)), quiet: [cue.hear.t0 - 0.15, cue.senses.t0 - 0.2] }
})(typeof window !== 'undefined' ? window : globalThis)
