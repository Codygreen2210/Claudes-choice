// kit4.js: cut-paper pieces for the Thermopylae film, on top of lib.js and kit3.js.
// Greeks are ink with the one red (Spartan cloaks); the Persian king, his gold and fire are the one gold.
(function () {
  const { clamp, lerp, rng, noise, mix, prog } = K
  const { W, H, C, person, glow, text, F, hatch } = L
  const INK = C.ink, RED = '#a8321f', GOLD = C.gold, GY = 800

  // ---------- Greeks ----------
  // hoplite: (x, y) feet on the ground, h height. o: face, walk, stride, pose guard|thrust|march|comb|rest|none,
  // thrust 0..1, cloak (bool, red), helm (bool), down 0..1, col, shield (bool)
  function hoplite(c, x, y, h, o = {}) {
    const face = o.face || 1, col = o.col || INK, pose = o.pose || 'guard', dn = clamp(o.down || 0), s = h / 100
    const ar = pose === 'guard' || pose === 'thrust' ? 0.95 : pose === 'comb' ? 1.12 + 0.06 * Math.sin((o.t || 0) * 5) : pose === 'march' ? 0.08 : pose === 'rest' ? 0.12 : (o.arm || 0)
    const th = pose === 'thrust' ? (o.thrust || 0) : 0
    c.save(); c.translate(x, y)
    if (dn > 0) { c.rotate(-face * dn * 1.5); c.translate(0, dn * 4 * s) }
    // cloak behind
    if (o.cloak) {
      c.save(); c.scale(s * face, s); c.fillStyle = o.cloakCol || RED
      const fl = Math.sin((o.walk || 0) * 1.0 + (o.t || 0) * 1.7) * 3 + (o.stride || 0) * 5
      c.beginPath(); c.moveTo(-9, -84); c.quadraticCurveTo(-24 - fl, -50, -22 - fl * 1.6, -18); c.lineTo(-6, -22); c.quadraticCurveTo(-4, -60, 4, -82); c.closePath(); c.fill(); c.restore()
    }
    const hold = pose === 'comb' ? (q) => { q.save(); q.translate(0, 34); q.fillStyle = col; q.fillRect(-2, -3, 10, 5); q.restore() }
      : (pose === 'none' || o.spear === false) ? null : (q) => {
        const ang = pose === 'march' ? -1.5 : pose === 'rest' ? -1.42 : 0.12 - th * 0.08
        q.save(); q.translate(0, 31); q.rotate(ar * 2.5 + ang); q.translate(th * 26, 0); q.fillStyle = col
        const back = pose === 'march' || pose === 'rest' ? -36 : -58, fwd = pose === 'march' || pose === 'rest' ? 150 : 92
        q.fillRect(back, -1.3, fwd - back, 2.6)
        q.beginPath(); q.moveTo(fwd, -3.2); q.lineTo(fwd + 13, 0); q.lineTo(fwd, 3.2); q.closePath(); q.fill()
        q.fillRect(back - 6, -1.8, 7, 3.6); q.restore()
      }
    person(c, 0, 0, h, { hat: 'none', walk: o.walk, stride: o.stride, face, col, arm: ar, hold, lean: o.lean || (pose === 'guard' || pose === 'thrust' ? 0.06 : 0), bulk: 1.08 })
    // hair, helmet, shield, drawn in the body's frame
    c.scale(s * face, s)
    const st = o.stride ?? 0, bob = -Math.abs(Math.cos(o.walk || 0)) * 1.6 * st
    c.translate(0, bob); c.rotate(o.lean || (pose === 'guard' || pose === 'thrust' ? 0.06 : 0)); c.fillStyle = col
    if (o.helm === false) {
      c.beginPath(); c.moveTo(-6, -97); c.quadraticCurveTo(-12, -88, -11, -74); c.lineTo(-4, -76); c.quadraticCurveTo(-3, -88, 2, -97); c.closePath(); c.fill()
      c.beginPath(); c.ellipse(0, -96, 8, 4.4, -0.2, Math.PI, 0); c.fill()
    } else {
      // a Corinthian helmet: dome, cheek guards, nose guard, and the horsehair crest
      c.beginPath(); c.moveTo(-7.5, -86); c.quadraticCurveTo(-8.5, -101, 2, -100.5); c.quadraticCurveTo(10.5, -100, 10, -90); c.lineTo(8.6, -84.5); c.lineTo(5, -84); c.lineTo(5.5, -89); c.lineTo(2.5, -89); c.lineTo(2, -83); c.lineTo(-7.5, -83); c.closePath(); c.fill()
      c.beginPath(); c.moveTo(-9, -100); c.quadraticCurveTo(1, -116, 13, -103); c.quadraticCurveTo(15, -101, 12, -100); c.quadraticCurveTo(1, -110, -7, -96); c.quadraticCurveTo(-16, -92, -17, -83); c.quadraticCurveTo(-14, -94, -9, -100); c.closePath(); c.fill()
    }
    if (o.shield !== false && pose !== 'comb') {
      // the round shield on the far arm, rim catching a little light
      const sx = pose === 'march' || pose === 'rest' ? 3 : 13, sy = pose === 'march' || pose === 'rest' ? -56 : -62
      c.beginPath(); c.arc(sx, sy, 21, 0, 7); c.fill()
      c.strokeStyle = o.rim || 'rgba(238,226,200,0.32)'; c.lineWidth = 1.6; c.beginPath(); c.arc(sx, sy, 18.5, 0, 7); c.stroke()
      if (o.mark) { c.strokeStyle = o.rim || 'rgba(238,226,200,0.32)'; c.lineWidth = 2.2; c.beginPath(); c.moveTo(sx - 7, sy + 8); c.lineTo(sx, sy - 9); c.lineTo(sx + 7, sy + 8); c.stroke() }
    }
    c.restore()
  }
  // a phalanx: ranks of hoplites with their shields overlapping. (x, y) front-rank centre, n per rank, ranks deep.
  function phalanx(c, x, y, h, o = {}) {
    const n = o.n || 8, ranks = o.ranks || 3, face = o.face || 1, gap = h * (o.gap ?? 0.3), t = o.t || 0, r = rng(o.seed || 3)
    const jit = Array.from({ length: n * ranks }, () => r())
    for (let k = ranks - 1; k >= 0; k--) for (let i = 0; i < n; i++) {
      const j = jit[k * n + i], hx = x + (i - (n - 1) / 2) * gap - face * k * h * 0.08 + Math.sin(t * 1.4 + j * 6) * 1.5, hy = y - k * h * 0.07
      const shade = k === 0 ? (o.col || INK) : mix(o.col || INK, o.back || '#4a3e33', 0.25 * k)
      const thr = o.thrust ? clamp(0.5 + 0.5 * Math.sin(t * (2.2 + j) + j * 9)) * o.thrust : 0
      hoplite(c, hx, hy, h * (0.97 + 0.06 * j), { face, pose: o.pose || (thr ? 'thrust' : 'guard'), thrust: thr, cloak: o.cloak, col: shade, walk: o.walk != null ? o.walk + j * 0.3 : 0, stride: o.stride, t: t + j * 3, down: (o.down && o.down(i, k)) || 0 })
    }
  }

  // ---------- Persians ----------
  // kind: mede (soft cap, wicker shield, short spear), immortal (same, with the gold butt on the spear), archer (bow), rider
  function persian(c, x, y, h, o = {}) {
    const face = o.face || 1, col = o.col || INK, kind = o.kind || 'mede', pose = o.pose || 'stand', dn = clamp(o.down || 0), s = h / 100
    const ar = pose === 'charge' ? 0.62 : pose === 'bow' ? 0.72 + (o.aim || 0) : pose === 'flee' ? 0.9 : pose === 'whip' ? 0.9 + 0.35 * Math.sin((o.t || 0) * 7) : 0.1
    const hold = pose === 'bow' ? (q) => {
      q.save(); q.translate(0, 33); q.rotate(ar * 2.5 - 1.57 * 0 + (o.aim ? -o.aim * 0.4 : 0)); q.strokeStyle = col; q.lineWidth = 2.6; q.beginPath(); q.arc(-2, 0, 22, -1.25, 1.25); q.stroke()
      q.lineWidth = 0.9; q.beginPath(); q.moveTo(-2 + 22 * Math.cos(-1.25), 22 * Math.sin(-1.25)); q.lineTo(-14 - (o.draw || 0) * 10, 0); q.lineTo(-2 + 22 * Math.cos(1.25), 22 * Math.sin(1.25)); q.stroke(); q.restore()
    } : pose === 'whip' ? (q) => { q.save(); q.translate(0, 32); q.strokeStyle = col; q.lineWidth = 1.6; q.beginPath(); q.moveTo(0, 0); q.quadraticCurveTo(30, -10 + 20 * Math.sin((o.t || 0) * 7), 52, 16); q.stroke(); q.restore() }
      : (q) => {
        const ang = pose === 'charge' ? 0.08 : pose === 'flee' ? -2.6 : -1.5
        q.save(); q.translate(0, 31); q.rotate(ar * 2.5 + ang); q.fillStyle = col; q.fillRect(-26, -1.2, 92, 2.4)
        q.beginPath(); q.moveTo(66, -2.8); q.lineTo(76, 0); q.lineTo(66, 2.8); q.closePath(); q.fill()
        if (kind === 'immortal') { q.fillStyle = GOLD; q.beginPath(); q.arc(-28, 0, 4.2, 0, 7); q.fill() }
        q.restore()
      }
    const held = o.spear === false && pose !== 'bow' && pose !== 'whip' ? null : hold
    c.save(); c.translate(x, y)
    if (dn > 0) { c.rotate(-face * dn * 1.5); c.translate(0, dn * 4 * s) }
    // the long coat flares below the knee
    c.save(); c.scale(s * face, s); c.fillStyle = col
    const ph = o.walk || 0, st = o.stride ?? 0
    c.beginPath(); c.moveTo(-13, -40); c.quadraticCurveTo(-18 - st * 4 * Math.sin(ph), -24, -16, -18); c.lineTo(16, -18); c.quadraticCurveTo(17 + st * 3 * Math.sin(ph), -26, 13, -40); c.closePath(); c.fill(); c.restore()
    person(c, 0, 0, h, { hat: 'none', walk: o.walk, stride: o.stride, face, col, arm: ar, hold: held, lean: o.lean || (pose === 'charge' ? 0.12 : pose === 'flee' ? -0.1 : 0), bulk: 1.02 })
    c.scale(s * face, s); const bob = -Math.abs(Math.cos(ph)) * 1.6 * st; c.translate(0, bob); c.rotate(o.lean || (pose === 'charge' ? 0.12 : pose === 'flee' ? -0.1 : 0)); c.fillStyle = col
    // the soft felt cap, with flaps down over the cheeks and neck
    c.beginPath(); c.moveTo(-8, -84); c.quadraticCurveTo(-10, -100, 0, -102); c.quadraticCurveTo(8, -104, 10, -97); c.quadraticCurveTo(13, -101, 12, -104); c.quadraticCurveTo(15, -98, 9.5, -92); c.lineTo(9, -88); c.lineTo(5, -89); c.lineTo(4, -80); c.lineTo(-9, -78); c.closePath(); c.fill()
    // a beard, the one thing that tells them from a Greek at a glance
    c.beginPath(); c.moveTo(4, -86); c.quadraticCurveTo(10, -84, 8, -77); c.quadraticCurveTo(4, -78, 2, -82); c.closePath(); c.fill()
    if (kind !== 'archer' && pose !== 'flee' && o.shield !== false) {
      // the tall wicker shield: a rounded oblong with weave lines
      const sx = pose === 'charge' ? 13 : 8
      c.beginPath(); c.roundRect(sx - 9, -86, 18, 50, 6); c.fill()
      c.strokeStyle = 'rgba(238,226,200,0.22)'; c.lineWidth = 1; for (let k = 0; k < 6; k++) { c.beginPath(); c.moveTo(sx - 7, -80 + k * 8); c.lineTo(sx + 7, -80 + k * 8); c.stroke() }
    }
    if (kind === 'archer') { c.fillStyle = col; c.beginPath(); c.roundRect(-14, -78, 6, 26, 2); c.fill(); c.fillRect(-14, -84, 1.4, 7); c.fillRect(-11, -85, 1.4, 8) }    // the quiver
    c.restore()
  }
  // a mass of Persians: rows coming on. o: n, rows, face, kind, pose, walk(t), stride, spread, seed, down(i,k)
  function host(c, x, y, h, o = {}) {
    const n = o.n || 10, rows = o.rows || 3, face = o.face || 1, gap = h * (o.gap ?? 0.34), r = rng(o.seed || 7), t = o.t || 0
    const J = Array.from({ length: n * rows * 3 }, () => r())
    for (let k = rows - 1; k >= 0; k--) for (let i = 0; i < n; i++) {
      const j = J[(k * n + i) * 3], j2 = J[(k * n + i) * 3 + 1]
      const px = x + (i - (n - 1) / 2) * gap + (j - 0.5) * gap * 0.5 - face * k * h * 0.12, py = y - k * h * 0.08
      const shade = mix(o.col || INK, o.back || '#5a4c3e', Math.min(0.75, 0.22 * k))
      persian(c, px, py, h * (0.94 + 0.1 * j2) * (1 - 0.04 * k), { face, kind: o.kind, pose: o.pose || 'charge', walk: (o.walk ?? t * 6) + j * 6, stride: o.stride ?? 0.9, col: shade, t: t + j * 4, down: (o.down && o.down(i, k)) || 0, aim: o.aim, draw: o.draw })
    }
  }

  // ---------- the king ----------
  // Xerxes on his throne under a parasol, all gold. stand 0..1 = how far he has risen out of it.
  function xerxes(c, x, y, s, o = {}) {
    const st = clamp(o.stand || 0), col = o.col || GOLD
    c.save(); c.translate(x, y); c.scale(s * (o.face || 1), s); c.fillStyle = col; c.strokeStyle = col
    // the dais and the throne
    c.fillRect(-90, -16, 180, 16); c.fillRect(-70, -30, 140, 14)
    c.fillRect(-46, -170, 10, 140); c.beginPath(); c.arc(-41, -176, 8, 0, 7); c.fill()
    c.fillRect(-46, -92, 70, 9); c.fillRect(14, -92, 8, 62); c.fillRect(-42, -32, 8, 6)
    // the parasol, held up on a staff behind
    c.lineWidth = 4; c.beginPath(); c.moveTo(-60, -30); c.lineTo(-60, -310); c.stroke()
    c.beginPath(); c.moveTo(-160, -268); c.quadraticCurveTo(-60, -340, 40, -268); c.quadraticCurveTo(-60, -286, -160, -268); c.closePath(); c.fill()
    for (let k = 0; k < 7; k++) { c.beginPath(); c.arc(-150 + k * 31.6, -267, 5, 0, Math.PI); c.fill() }
    // the king: seated, then rising
    const by = -92 - st * 46
    c.save(); c.translate(-14, by + 92)
    if (st < 0.5) person(c, 0, -30 + st * 40, 140, { seated: true, hat: 'none', col, arm: 0.35 + st * 0.8, bulk: 1.15, mous: true })
    else person(c, 6, -30 + 40 * 0.5 + (st - 0.5) * 20, 150, { hat: 'none', col, arm: 0.3 + st * 0.9, bulk: 1.15, mous: true, lean: -0.08 * st })
    c.restore()
    // the crown: a tall fluted cylinder with points (head sits at ~ y -127 * 1.4 above the seat)
    const hy = by + 92 - 30 + (st < 0.5 ? st * 40 : 20 + (st - 0.5) * 20) - 1.4 * (st < 0.5 ? 97 : 104)
    const hx = -14 + (st < 0.5 ? 2 : 8)
    c.beginPath(); c.moveTo(hx - 9, hy + 4); c.lineTo(hx - 10, hy - 18); for (let k = 0; k < 5; k++) { c.lineTo(hx - 10 + k * 5 + 2.5, hy - 24); c.lineTo(hx - 10 + k * 5 + 5, hy - 18) } c.lineTo(hx + 12, hy + 4); c.closePath(); c.fill()
    c.restore()
  }

  // ---------- land and sea ----------
  // side view of the pass: cliffs behind, the road, the sea in front. d: 0 night .. 1 day; warm: 0..1 dusk tint
  function cliffs(c, x0, x1, o = {}) {
    const r = rng(o.seed || 11), top = o.top ?? 120, col = o.col || '#9b8b6c'
    c.save(); c.fillStyle = col; c.beginPath(); c.moveTo(x0, GY + 2)
    for (let x = x0; x <= x1; x += 60) c.lineTo(x, top + (noise(x * 0.004, 5) * 0.5 + 0.5) * 260 + r() * 22)
    c.lineTo(x1, GY + 2); c.closePath(); c.fill()
    hatch(c, k => { k.beginPath(); k.moveTo(x0, GY); for (let x = x0; x <= x1; x += 60) k.lineTo(x, top + 120 + (noise(x * 0.004, 5) * 0.5 + 0.5) * 260); k.lineTo(x1, GY); k.closePath() }, { gap: 10, alpha: 0.18, angle: 1.1, box: [x0, top, x1 - x0, GY - top] })
    c.restore()
  }
  function sea(c, t, x0, x1, y0, o = {}) {
    const col = o.col || '#5b6a72', glint = o.glint ?? 0.5
    c.save(); c.fillStyle = col; c.fillRect(x0, y0, x1 - x0, 900)
    c.strokeStyle = o.line || 'rgba(238,226,200,0.28)'; c.lineWidth = 2.2; c.lineCap = 'round'; const r = rng(o.seed || 4)
    for (let k = 0; k < 70; k++) { const y = y0 + 14 + r() * 300, x = x0 + ((r() * (x1 - x0) + t * (8 + r() * 10)) % (x1 - x0)), l = 30 + r() * 70; c.globalAlpha = 0.4 + 0.6 * r(); c.beginPath(); c.moveTo(x, y); c.quadraticCurveTo(x + l / 2, y - 4, x + l, y); c.stroke() }
    if (glint) { c.globalAlpha = glint; c.fillStyle = C.gold2; for (let k = 0; k < 18; k++) { const x = x0 + r() * (x1 - x0), y = y0 + 20 + r() * 120, a = 0.5 + 0.5 * Math.sin(t * 2 + k); c.globalAlpha = glint * a; c.fillRect(x, y, 14, 2) } }
    c.restore()
  }
  // the rebuilt wall across the pass: dry stone, waist to head high. (x, y) ground at its middle, w wide, h high
  function stonewall(c, x, y, w, h, o = {}) {
    const col = o.col || '#3a312a', r = rng(o.seed || 21), p = clamp(o.p ?? 1)
    c.save(); c.fillStyle = col; c.beginPath(); c.moveTo(x - w / 2, y); c.lineTo(x - w / 2 + 6, y - h * p); c.lineTo(x + w / 2 - 6, y - h * p); c.lineTo(x + w / 2, y); c.closePath(); c.fill()
    c.strokeStyle = o.joint || 'rgba(238,226,200,0.22)'; c.lineWidth = 1.6
    for (let row = 0; row * 22 < h * p; row++) { const yy = y - row * 22; c.beginPath(); c.moveTo(x - w / 2 + 4, yy); c.lineTo(x + w / 2 - 4, yy); c.stroke(); for (let k = 0; k < w / 40; k++) { const xx = x - w / 2 + ((k + (row % 2) * 0.5) * 40) + r() * 8; if (xx < x + w / 2 - 6) { c.beginPath(); c.moveTo(xx, yy); c.lineTo(xx, yy - 22); c.stroke() } } }
    c.restore()
  }
  // a low round hill: the last stand
  function hill(c, x, y, w, h, col = '#2d2620') { c.save(); c.fillStyle = col; c.beginPath(); c.moveTo(x - w / 2, y + 2); c.bezierCurveTo(x - w * 0.3, y - h, x + w * 0.3, y - h, x + w / 2, y + 2); c.closePath(); c.fill(); c.restore() }
  // oak trees on the mountain path
  function oak(c, x, y, s, col = INK, seed = 1) {
    const r = rng(seed * 13 + 2); c.save(); c.translate(x, y); c.scale(s, s); c.fillStyle = col
    c.beginPath(); c.moveTo(-8, 0); c.lineTo(-5, -70); c.lineTo(5, -70); c.lineTo(9, 0); c.closePath(); c.fill()
    for (let k = 0; k < 8; k++) { c.beginPath(); c.ellipse((r() - 0.5) * 90, -96 - r() * 50, 34 + r() * 18, 26 + r() * 12, 0, 0, 7); c.fill() } c.restore()
  }

  // ---------- ships ----------
  // a trireme, rowing toward +x*face: long low hull, the ram, three banks of oars, one square sail (furled unless sail)
  function trireme(c, x, y, s, o = {}) {
    const col = o.col || INK, face = o.face || 1, t = o.t || 0
    c.save(); c.translate(x, y + Math.sin(t * 1.1 + x * 0.01) * 2 * s); c.scale(s * face, s); c.fillStyle = col; c.strokeStyle = col
    c.beginPath(); c.moveTo(-150, -22); c.quadraticCurveTo(-160, -50, -138, -60); c.quadraticCurveTo(-148, -40, -130, -26); c.lineTo(120, -26); c.lineTo(150, -14); c.lineTo(170, -6); c.lineTo(146, -2); c.lineTo(132, 4); c.lineTo(-140, 4); c.closePath(); c.fill()
    c.fillRect(-120, -36, 230, 10)
    c.lineWidth = 2; for (let k = 0; k < 24; k++) { const ox = -120 + k * 10, a = 0.6 + 0.35 * Math.sin(t * 3.2 + (o.oarPh || 0)); c.beginPath(); c.moveTo(ox, -8); c.lineTo(ox - 16 * Math.cos(a) * 0.6, 26 * Math.sin(a) + 4); c.stroke() }
    if (o.sail) { c.fillRect(-4, -150, 5, 124); c.beginPath(); c.moveTo(-50, -140); c.quadraticCurveTo(0, -120 - 10 * o.sail, 50, -140); c.lineTo(52, -62); c.quadraticCurveTo(0, -50, -48, -62); c.closePath(); c.fill() }
    
    c.restore()
  }
  // the bridge of boats: ships side by side across a strait, a road laid over their decks
  function boatBridge(c, x0, x1, y, s, o = {}) {
    const n = Math.floor((x1 - x0) / (60 * s)), t = o.t || 0, col = o.col || INK
    c.save(); c.fillStyle = col
    for (let k = 0; k < n; k++) { const xx = x0 + k * 60 * s, yy = y + Math.sin(t * 1.3 + k * 0.6) * 3 * s; c.beginPath(); c.ellipse(xx, yy, 34 * s, 10 * s, 0, 0, Math.PI); c.fill(); c.fillRect(xx - 1.5 * s, yy - 40 * s, 3 * s, 40 * s) }
    c.fillRect(x0 - 30 * s, y - 14 * s, x1 - x0 + 30 * s, 8 * s)
    c.strokeStyle = col; c.lineWidth = 2.5 * s; c.beginPath(); c.moveTo(x0 - 30 * s, y - 36 * s); for (let k = 0; k < n; k++) c.quadraticCurveTo(x0 + k * 60 * s - 30 * s, y - 28 * s, x0 + k * 60 * s, y - 38 * s); c.stroke()
    c.restore()
  }

  // ---------- arrows ----------
  // a storm of arrows: each flies a shallow arc from (sx, sy) to (ex, ey) across a span of time; draws streaks with fletching.
  function arrows(c, t, t0, o = {}) {
    const n = o.n || 160, r = rng(o.seed || 31), dur = o.dur || 1.6, col = o.col || INK, every = o.every ?? 2.6, waves = o.waves || 6
    c.save(); c.strokeStyle = col; c.fillStyle = col; c.lineCap = 'round'
    for (let w = 0; w < waves; w++) for (let k = 0; k < n; k++) {
      const st = t0 + w * every + r() * 0.8, p = (t - st) / dur; if (p < 0 || p > 1) { r(); r(); r(); r(); continue }
      const sx = (o.sx ?? -200) + r() * (o.sw ?? 400), sy = (o.sy ?? 900) + r() * 80, ex = (o.ex ?? 1400) + r() * (o.ew ?? 700), ey = (o.ey ?? 820) + r() * 60, top = o.top ?? 80
      const px = lerp(sx, ex, p), py = lerp(sy, ey, p) - Math.sin(p * Math.PI) * (sy - top) * 0.9
      const dx = (ex - sx) / dur, dy = (ey - sy) / dur - Math.cos(p * Math.PI) * Math.PI * (sy - top) * 0.9 / dur, a = Math.atan2(dy, dx), l = o.len || 26
      c.globalAlpha = (o.alpha ?? 0.85) * clamp(Math.min(p * 6, (1 - p) * 6))
      c.lineWidth = o.lw || 1.8; c.beginPath(); c.moveTo(px - Math.cos(a) * l, py - Math.sin(a) * l); c.lineTo(px, py); c.stroke()
    }
    c.restore()
  }
  // an arrow stuck in something: shaft and fletching at angle a
  function stuck(c, x, y, a, l = 28, col = INK) { c.save(); c.translate(x, y); c.rotate(a); c.strokeStyle = col; c.lineWidth = 1.8; c.beginPath(); c.moveTo(0, 0); c.lineTo(-l, 0); c.stroke(); c.fillStyle = col; c.beginPath(); c.moveTo(-l, 0); c.lineTo(-l - 7, -4); c.lineTo(-l + 3, 0); c.lineTo(-l - 7, 4); c.closePath(); c.fill(); c.restore() }

  // ---------- paper map of the pass ----------
  // mountains top-left, the gulf below, the road between, the wall, the goat path (p 0..1 how much of it is drawn)
  function passMap(c, t, o = {}) {
    const ink = INK
    c.save()
    // the sea
    c.fillStyle = '#c9c0a6'; c.beginPath(); c.moveTo(0, 690); c.bezierCurveTo(500, 640, 760, 600, 960, 610); c.bezierCurveTo(1180, 620, 1500, 660, 1920, 700); c.lineTo(1920, 1080); c.lineTo(0, 1080); c.closePath(); c.fill()
    c.strokeStyle = 'rgba(26,21,18,0.28)'; c.lineWidth = 1.6; const r = rng(8)
    for (let k = 0; k < 60; k++) { const x = r() * 1920, y = 700 + r() * 360 + Math.sin(t + k) * 2; c.beginPath(); c.moveTo(x, y); c.quadraticCurveTo(x + 18, y - 5, x + 36, y); c.stroke() }
    // the mountains: ridges of hatched peaks
    c.fillStyle = '#b6a27a'; c.beginPath(); c.moveTo(0, 0); c.lineTo(1920, 0); c.lineTo(1920, 560); c.bezierCurveTo(1500, 530, 1180, 560, 980, 545); c.bezierCurveTo(760, 530, 420, 560, 0, 600); c.closePath(); c.fill()
    for (let k = 0; k < 46; k++) { const x = (k % 12) * 170 + (k > 11 ? 60 : 0) + r() * 50, y = 120 + Math.floor(k / 12) * 110 + r() * 40; c.fillStyle = 'rgba(26,21,18,0.55)'; c.beginPath(); c.moveTo(x - 50, y + 40); c.lineTo(x, y - 30); c.lineTo(x + 50, y + 40); c.lineTo(x + 30, y + 40); c.lineTo(x, y); c.lineTo(x - 30, y + 40); c.closePath(); c.fill() }
    // the road, squeezed at the middle gate
    c.strokeStyle = ink; c.lineWidth = 4; c.setLineDash([]); c.beginPath(); c.moveTo(0, 630); c.bezierCurveTo(500, 600, 760, 572, 960, 576); c.bezierCurveTo(1180, 580, 1500, 610, 1920, 640); c.stroke()
    if (o.wall) { c.lineWidth = 9; c.strokeStyle = ink; c.beginPath(); c.moveTo(1010, 544); c.lineTo(1006, 612); c.stroke() }
    // the goat path: up over the mountain from the Persian side and down behind the wall
    const pp = clamp(o.path || 0)
    if (pp > 0) {
      const pts = []; for (let k = 0; k <= 60; k++) { const u = k / 60; pts.push([lerp(420, 1500, u) + Math.sin(u * 9) * 40, 600 - Math.sin(u * Math.PI) * 420 + Math.sin(u * 17) * 14]) }
      c.strokeStyle = RED; c.lineWidth = 5; c.setLineDash([14, 10]); c.lineDashOffset = -t * 20; c.beginPath(); const m = Math.max(1, Math.floor(pp * 60)); c.moveTo(...pts[0]); for (let k = 1; k <= m; k++) c.lineTo(...pts[k]); c.stroke(); c.setLineDash([])
      if (o.dot) { const k = Math.min(60, Math.floor(clamp(o.dot) * 60)); c.fillStyle = RED; c.beginPath(); c.arc(pts[k][0], pts[k][1], 11, 0, 7); c.fill() }
    }
    c.restore()
  }

  // a stone slab with words cut into it
  function stele(c, x, y, w, h, lines, o = {}) {
    c.save(); c.fillStyle = o.col || '#d6c9aa'; c.beginPath(); c.moveTo(x - w / 2, y); c.lineTo(x - w / 2 + 10, y - h); c.lineTo(x + w / 2 - 10, y - h); c.lineTo(x + w / 2, y); c.closePath(); c.fill()
    hatch(c, k => k.rect(x - w / 2, y - h, w, h), { gap: 12, alpha: 0.08, angle: 0.3, box: [x - w / 2, y - h, w, h] })
    const p = clamp(o.p ?? 1), all = lines.join('\n').length; let used = 0
    lines.forEach((s, i) => { const n = Math.max(0, Math.min(s.length, Math.ceil(p * all) - used)); used += s.length + 1; if (n > 0) text(c, s.slice(0, n), x - tw2(c, s, o.font) / 2, y - h + 110 + i * (o.lh || 70), o.font || F.sc(48), INK, { align: 'left', alpha: 0.9 }) })
    c.restore()
  }
  const tw2 = (c, s, font) => { c.save(); c.font = font || F.sc(48); const w = c.measureText(s).width; c.restore(); return w }

  window.TH = { INK, RED, GOLD, GY, hoplite, phalanx, persian, host, xerxes, cliffs, sea, stonewall, hill, oak, trireme, boatBridge, arrows, stuck, passMap, stele }
})()
