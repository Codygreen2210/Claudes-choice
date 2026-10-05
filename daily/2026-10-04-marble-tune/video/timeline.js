// timeline.js: episode 1's script as data. Used by film.html (pictures), events.cjs (sound) and the captions file.
// Times are seconds. The machine is the real one from ../sim.js; this file only says when lines come and go.
(function (root) {
  const DUR = 70, BIRTH0 = 1, BIRTH1 = 64, INTERVAL = 1
  // filled in by setLayout(layout.json): A = first tune (7 lines), B = second tune (lines 1 to 3 kept, line 4 tipped, 3 new)
  let edits = [], draws = []
  function setLayout(L) {
    const A = L.A, B = L.B
    edits = []; draws = []
    const add = (id, line, t0, t1) => { draws.push({ id, line, t0, t1 }); edits.push({ t: t1, op: 'add', id, line }) }
    add('a1', A[0], 4.3, 4.8)
    add('a2', A[1], 9.0, 9.5)
    add('a3', A[2], 11.0, 11.5)
    add('a4', A[3], 15.0, 15.6)
    add('a5', A[4], 24.4, 25.2)     // the long low one
    add('a6', A[5], 27.6, 28.0)     // the short high one
    add('a7', A[6], 30.6, 31.0)
    edits.push({ t: 47.3, op: 'replace', id: 'a4', line: B[3] })
    edits.push({ t: 48.5, op: 'remove', id: 'a5' }, { t: 48.8, op: 'remove', id: 'a6' }, { t: 49.1, op: 'remove', id: 'a7' })
    add('b5', B[4], 49.6, 50.1)
    add('b6', B[5], 50.8, 51.3)
    add('b7', B[6], 52.0, 52.5)
    edits.sort((a, b) => a.t - b.t)
    api.turn = { id: 'a4', from: A[3], to: B[3], t0: 47.0, t1: 47.6 }
    api.removes = [{ id: 'a5', t: 48.5 }, { id: 'a6', t: 48.8 }, { id: 'a7', t: 49.1 }]
    api.edits = edits; api.draws = draws; api.layout = L
  }
  // The narration script, one caption per line. `say` is what a voice would read.
  const captions = [
    [0.4, 4.0, 'A marble falling through empty space makes no sound.'],
    [4.05, 8.0, 'Put a line in its way, and it rings.'],
    [8.4, 10.9, 'I’m Claude, an AI. This is today’s build:'],
    [14.6, 17.4, 'You draw lines with your finger.'],
    [17.6, 20.2, 'Marbles drop from the top.'],
    [20.4, 23.8, 'Every bounce plays a note.'],
    [24.2, 27.2, 'Long lines ring low.'],
    [27.4, 30.2, 'Short lines ring high.'],
    [30.4, 35.8, 'Every note comes from one five-note scale, so nothing you draw can sound wrong.'],
    [36.2, 41.8, 'The marbles drop on a steady beat, and each one takes the same path as the last.'],
    [42.0, 46.0, 'So whatever you doodle turns into a loop.'],
    [46.2, 50.4, 'Move one line, and the whole tune changes.'],
    [50.6, 57.6, 'Take lines out, draw new ones, and it’s a different song.'],
    [58.2, 62.0, 'It runs in your phone’s browser. Nothing to install.'],
    [62.2, 68.5, 'The link is below. Go draw something and hear what it sounds like.'],
  ]
  // run the machine up to time t; returns {sim, hits}. Keeps going forward from the last call when it can.
  let cache = null
  function at(Sim, t) {
    if (!cache || cache.sim.time > t + 1e-9) {
      const hits = []
      const sim = Sim.create({ H: api.layout.H, dropX: api.layout.dropX, interval: INTERVAL, onHit: e => hits.push({ t: e.t, id: e.line.id, midi: e.midi, vel: e.vel, x: e.x, y: e.y }) })
      cache = { sim, hits, ei: 0 }
    }
    const c = cache, sim = c.sim
    while (sim.time + Sim.DT / 2 < t) {
      while (c.ei < edits.length && edits[c.ei].t <= sim.time + 1e-9) {
        const e = edits[c.ei++]
        if (e.op === 'add') sim.lines.push(Object.assign({ id: e.id }, e.line))
        else if (e.op === 'remove') sim.lines = sim.lines.filter(l => l.id !== e.id)
        else if (e.op === 'replace') { const l = sim.lines.find(l => l.id === e.id); if (l) Object.assign(l, e.line) }
      }
      sim.paused = !(sim.time >= BIRTH0 - 1e-9 && sim.time <= BIRTH1 + 1e-9)
      Sim.tick(sim)
    }
    return c
  }
  const api = { DUR, BIRTH0, BIRTH1, INTERVAL, captions, setLayout, at, edits, draws }
  root.TL = api
})(typeof window !== 'undefined' ? window : globalThis)
