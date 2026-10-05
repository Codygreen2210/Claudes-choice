// sim.js: the Marble Tune Machine's physics. One file, used by the page (index.html), by the
// episode video (video/film.html) and by node (video/events.mjs), so all three play the same marbles.
//
// World units: the play area is 1000 wide and H tall (H follows the screen's shape; 1700 by default).
// Time moves in fixed steps, so the same lines always give the same tune.
(function (root) {
  const DT = 1 / 240
  const R = 13            // marble radius
  const G = 2600          // gravity, units / s^2
  const REST = 0.62       // bounce kept on a hit
  const VMAX = 2600
  // C major pentatonic, low to high. Long line = low note, short line = high note.
  const SCALE = [60, 62, 64, 67, 69, 72, 74, 76, 79, 81, 84, 86, 88, 91, 93, 96]
  const NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
  const LMIN = 70, LMAX = 620

  const len = l => Math.hypot(l.x2 - l.x1, l.y2 - l.y1)
  function noteIndex(l) {
    const p = Math.max(0, Math.min(1, (len(l) - LMIN) / (LMAX - LMIN)))
    return Math.round((1 - p) * (SCALE.length - 1))
  }
  const midi = l => SCALE[noteIndex(l)]
  const noteName = m => NAMES[m % 12] + (Math.floor(m / 12) - 1)
  const freq = m => 440 * Math.pow(2, (m - 69) / 12)
  // hue for a note: low notes warm, high notes cool
  const hue = l => 28 + noteIndex(l) / (SCALE.length - 1) * 200

  function create(opts) {
    opts = opts || {}
    const s = {
      H: opts.H || 1700,
      lines: (opts.lines || []).map(l => Object.assign({}, l)),
      dropX: opts.dropX == null ? 500 : opts.dropX,
      interval: opts.interval || 0.5,   // seconds between marbles
      marbles: [], time: 0, step: 0, nextDrop: 0, dropped: 0,
      onHit: opts.onHit || null,
      rest: opts.rest || REST,          // bounce kept on a hit (the first try used 0.86: too bouncy)
    }
    return s
  }

  // advance one fixed step; calls s.onHit({t, line, index, midi, vel, x, y}) for each bounce
  function tick(s) {
    const stepsPerDrop = Math.round(s.interval / DT)
    if (s.step % stepsPerDrop === 0 && !s.paused) {
      s.marbles.push({ x: s.dropX, y: -R, vx: 0, vy: 0, born: s.time, last: -1, lastT: -1, id: s.dropped++ })
    }
    for (let i = s.marbles.length - 1; i >= 0; i--) {
      const m = s.marbles[i]
      m.vy += G * DT
      const sp = Math.hypot(m.vx, m.vy)
      if (sp > VMAX) { m.vx *= VMAX / sp; m.vy *= VMAX / sp }
      m.x += m.vx * DT; m.y += m.vy * DT
      for (let k = 0; k < s.lines.length; k++) {
        const l = s.lines[k]
        const dx = l.x2 - l.x1, dy = l.y2 - l.y1, L2 = dx * dx + dy * dy
        if (L2 < 1) continue
        let u = ((m.x - l.x1) * dx + (m.y - l.y1) * dy) / L2
        u = u < 0 ? 0 : u > 1 ? 1 : u
        const px = l.x1 + dx * u, py = l.y1 + dy * u
        let nx = m.x - px, ny = m.y - py
        const d = Math.hypot(nx, ny)
        if (d >= R || d === 0) continue
        nx /= d; ny /= d
        const vn = m.vx * nx + m.vy * ny
        m.x = px + nx * R; m.y = py + ny * R
        if (vn >= 0) continue
        m.vx -= (1 + s.rest) * vn * nx; m.vy -= (1 + s.rest) * vn * ny
        // a note only for a real knock, and not twice in a row on the same line within 60 ms
        if (-vn > 140 && !(m.last === k && s.time - m.lastT < 0.06)) {
          m.last = k; m.lastT = s.time
          l.hitT = s.time
          if (s.onHit) s.onHit({ t: s.time, line: l, index: k, midi: midi(l), vel: Math.min(1, -vn / 1500), x: px, y: py, marble: m.id })
        }
      }
      if (m.y > s.H + 60 || m.x < -80 || m.x > 1080 || s.time - m.born > 14) s.marbles.splice(i, 1)
    }
    s.step++; s.time = s.step * DT
  }

  function advance(s, toTime) { while (s.time + DT / 2 < toTime) tick(s) }

  // lines <-> a short string for share links: "x1,y1,x2,y2;..." rounded to whole units, then the drop x
  function encode(s) {
    return Math.round(s.dropX) + '|' + s.lines.map(l => [l.x1, l.y1, l.x2, l.y2].map(Math.round).join(',')).join(';')
  }
  function decode(str) {
    try {
      const [d, rest] = str.split('|')
      const dropX = Number(d)
      if (!isFinite(dropX)) return null
      const lines = (rest || '').split(';').filter(Boolean).slice(0, 40).map(p => {
        const [x1, y1, x2, y2] = p.split(',').map(Number)
        return { x1, y1, x2, y2 }
      }).filter(l => [l.x1, l.y1, l.x2, l.y2].every(isFinite))
      return { dropX: Math.max(40, Math.min(960, dropX)), lines }
    } catch (e) { return null }
  }

  const api = { DT, R, G, SCALE, LMIN, LMAX, len, noteIndex, midi, noteName, freq, hue, create, tick, advance, encode, decode }
  if (typeof module !== 'undefined' && module.exports) module.exports = api
  else root.Sim = api
})(typeof window !== 'undefined' ? window : globalThis)
