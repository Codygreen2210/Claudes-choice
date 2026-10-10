// kit2.js: the Tsavo film's own cut-paper pieces, on top of lib.js: lions, tents, thorn, trees, a train, night.
(function () {
  const { clamp, lerp, rng, noise } = K
  const { W, H, C, layer, person, glow, hatch, text, F } = L
  const N = { sky0: '#0a0f20', sky1: '#1d2a4c', sky2: '#3d4e7a', ground: '#06070b', moon: '#efe6cc', eye: '#ffd76a', fire: '246,150,60', blue: '120,140,190' }

  // ---------- lion ----------
  // Side view, facing +x. (x, y) is the ground under the middle of the body; s = pixels per unit (body ~100 units long).
  // o: walk (phase), stride 0..1, crouch 0..1, head (rad, + is down), tail (phase), eye, mouth 0..1, leap 0..1, col, face
  function leg(c, hx, hy, fx, fy, bend, w) {
    // two bones from hip (hx,hy) to foot (fx,fy); the joint is pushed sideways by `bend`
    const mx = (hx + fx) / 2, my = (hy + fy) / 2, dx = fx - hx, dy = fy - hy, d = Math.hypot(dx, dy) || 1
    const kx = mx + (-dy / d) * bend, ky = my + (dx / d) * bend
    c.lineWidth = w; c.beginPath(); c.moveTo(hx, hy); c.lineTo(kx, ky); c.stroke()
    c.lineWidth = w * 0.72; c.beginPath(); c.moveTo(kx, ky); c.lineTo(fx, fy); c.stroke()
    c.beginPath(); c.ellipse(fx + 3, fy - 1.5, 6.5, 3.4, 0, 0, 7); c.fill()
  }
  function lion(c, x, y, s, o = {}) {
    const face = o.face || 1, col = o.col || '#07080c', ph = o.walk || 0, st = o.stride ?? 0, cr = o.crouch || 0, lp = o.leap || 0
    c.save(); c.translate(x, y); c.scale(s * face, s); c.rotate(-lp * 0.5 + (o.rot || 0))
    c.fillStyle = col; c.strokeStyle = col; c.lineCap = 'round'; c.lineJoin = 'round'
    const drop = cr * 15 + Math.abs(Math.sin(ph)) * 1.2 * st            // the body sinks when it stalks
    const by = -64 + drop
    const foot = (off, base, hind) => {
      if (lp > 0) return [base + (hind ? -34 : 38) * lp, by + 46 - (hind ? 6 : 18) * lp]           // legs thrown out in a jump
      const a = ph + off, sw = Math.cos(a) * 15 * st, lift = Math.max(0, Math.sin(a)) * 8 * st
      return [base + sw + cr * (hind ? -4 : 6), -lift]
    }
    // far legs
    c.save(); c.globalAlpha *= 0.82
    let f = foot(Math.PI, 26, false); leg(c, 24, by + 16, f[0], f[1], -3 - cr * 7, 9)
    f = foot(Math.PI * 0.5, -34, true); leg(c, -36, by + 14, f[0], f[1], 9 + cr * 8, 10.5)
    c.restore()
    // tail
    const ts = Math.sin((o.tail ?? ph * 0.5) ) * 7
    c.lineWidth = 5; c.beginPath(); c.moveTo(-47, by + 6); c.bezierCurveTo(-66, by + 4 + ts * 0.3, -70, by + 30 + ts, -84, by + 34 + ts * 1.4 - cr * 8); c.stroke()
    c.beginPath(); c.ellipse(-87, by + 35 + ts * 1.4 - cr * 8, 6, 3.6, -0.5, 0, 7); c.fill()
    // body: rump, back, shoulder, chest, belly
    c.beginPath(); c.moveTo(-50, by + 8)
    c.bezierCurveTo(-52, by - 6, -30, by - 6, -8, by - 2)
    c.bezierCurveTo(8, by - 1, 20, by - 8, 34, by - 4)
    c.bezierCurveTo(44, by, 44, by + 20, 34, by + 25)
    c.bezierCurveTo(14, by + 28, -18, by + 19, -34, by + 22)
    c.bezierCurveTo(-46, by + 23, -50, by + 18, -50, by + 8); c.closePath(); c.fill()
    // neck and head
    const ha = (o.head || 0) + cr * 0.35
    c.save(); c.translate(34, by + 4); c.rotate(ha)
    c.beginPath(); c.moveTo(-8, -8); c.bezierCurveTo(4, -16, 14, -14, 20, -12); c.lineTo(22, 14); c.bezierCurveTo(10, 20, -2, 22, -10, 18); c.closePath(); c.fill()   // neck
    c.beginPath(); c.ellipse(22, -2, 13, 11.5, 0, 0, 7); c.fill()                                                // skull
    c.beginPath(); c.moveTo(26, -9); c.bezierCurveTo(34, -9, 40, -6, 41, -1); c.lineTo(41, 4 - (o.mouth || 0) * 1); c.lineTo(28, 6); c.closePath(); c.fill()   // muzzle
    const mo = o.mouth || 0
    c.save(); c.translate(26, 5); c.rotate(mo * 0.5); c.beginPath(); c.moveTo(-2, -1); c.lineTo(14, 0); c.bezierCurveTo(13, 6, 4, 8, -4, 6); c.closePath(); c.fill(); c.restore()   // jaw
    c.beginPath(); c.ellipse(15, -12.5, 4.6, 5, -0.3, 0, 7); c.fill()                                             // ear
    if (o.eye) { c.fillStyle = N.eye; c.beginPath(); c.ellipse(28, -4.5, 2.6, 1.7, 0.2, 0, 7); c.fill(); c.fillStyle = col }
    c.restore()
    // near legs
    f = foot(0, 28, false); leg(c, 26, by + 16, f[0], f[1], -3 - cr * 7, 10)
    f = foot(Math.PI * 1.5, -30, true); leg(c, -34, by + 14, f[0], f[1], 10 + cr * 8, 12)
    c.restore()
  }
  // a lion lying on its side, head toward +x (dead, or chewing at something)
  function lionDown(c, x, y, s, o = {}) {
    const col = o.col || '#07080c'
    c.save(); c.translate(x, y); c.scale(s * (o.face || 1), s); c.fillStyle = col; c.strokeStyle = col; c.lineCap = 'round'
    c.beginPath(); c.moveTo(-52, 0); c.bezierCurveTo(-56, -22, -20, -30, 10, -26); c.bezierCurveTo(30, -24, 40, -14, 38, 0); c.closePath(); c.fill()
    c.save(); c.translate(36, -10); c.rotate(o.head || 0.2); c.beginPath(); c.ellipse(10, -2, 13, 11, 0, 0, 7); c.fill(); c.beginPath(); c.moveTo(14, -8); c.lineTo(29, -3); c.lineTo(29, 3); c.lineTo(14, 6); c.closePath(); c.fill(); c.beginPath(); c.ellipse(3, -12, 4.5, 5, -0.3, 0, 7); c.fill(); c.restore()
    c.lineWidth = 9; for (const [a, b, e, g] of [[20, -4, 44, 4], [10, -2, 30, 6], [-36, -4, -16, 8], [-44, -2, -30, 10]]) { c.beginPath(); c.moveTo(a, b); c.lineTo(e, g); c.stroke() }
    c.lineWidth = 5; c.beginPath(); c.moveTo(-52, -6); c.bezierCurveTo(-72, -10, -80, 0, -92, -2); c.stroke()
    c.restore()
  }
  // just the eyes, for a lion you can't see
  function eyes(c, x, y, s, a = 1, face = 1) {
    c.save(); c.globalAlpha *= a; glow(c, x, y, 60 * s, '255,215,106', 0.35 * a); c.fillStyle = N.eye
    for (const dx of [-9, 9]) { c.beginPath(); c.ellipse(x + dx * s, y, 4.2 * s, 2.6 * s, dx * 0.02 * face, 0, 7); c.fill() }
    c.fillStyle = '#050505'; for (const dx of [-9, 9]) { c.beginPath(); c.ellipse(x + dx * s, y, 1.2 * s, 2.4 * s, 0, 0, 7); c.fill() }
    c.restore()
  }

  // ---------- the place ----------
  const stars = () => layer('stars', W, H, (x) => { const r = rng(404); for (let i = 0; i < 520; i++) { const a = 0.25 + r() * 0.7, sz = r() < 0.06 ? 2.6 : 1 + r() * 1.2; x.fillStyle = `rgba(232,226,205,${a})`; x.beginPath(); x.arc(r() * W, r() * H * 0.78, sz, 0, 7); x.fill() } })
  function night(c, t, o = {}) {
    const g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, o.top || N.sky0); g.addColorStop(0.62, o.mid || N.sky1); g.addColorStop(1, o.low || N.sky2); c.fillStyle = g; c.fillRect(-600, 0, W + 1200, H); c.fillStyle = o.top || N.sky0; c.fillRect(-600, -600, W + 1200, 601)
    c.drawImage(stars(), 0, 0)
    // a few stars breathe
    const r = rng(9); for (let i = 0; i < 26; i++) { const sx = r() * W, sy = r() * H * 0.6, tw = 0.5 + 0.5 * Math.sin(t * (1 + r() * 2) + i); c.fillStyle = `rgba(240,232,210,${0.5 * tw})`; c.beginPath(); c.arc(sx, sy, 2.4, 0, 7); c.fill() }
    if (o.moon) { const [mx, my, mr] = o.moon; glow(c, mx, my, mr * 6, '200,210,240', 0.3); c.fillStyle = N.moon; c.beginPath(); c.arc(mx, my, mr, 0, 7); c.fill(); c.fillStyle = 'rgba(120,120,110,0.25)'; for (const [dx, dy, rr] of [[-0.3, -0.2, 0.22], [0.25, 0.3, 0.16], [0.1, -0.4, 0.1]]) { c.beginPath(); c.arc(mx + dx * mr, my + dy * mr, rr * mr, 0, 7); c.fill() } }
  }
  function ground(c, y, col = N.ground, seed = 3, bump = 10) {
    c.fillStyle = col; c.beginPath(); c.moveTo(-50, H + 50); c.lineTo(-50, y)
    for (let x = -50; x <= W + 50; x += 40) c.lineTo(x, y + noise(x * 0.004 + seed, seed) * bump)
    c.lineTo(W + 50, H + 50); c.closePath(); c.fill()
  }
  // flat-topped thorn tree
  function acacia(c, x, y, s, col = N.ground, seed = 1) {
    const r = rng(seed * 77 + 5); c.save(); c.translate(x, y); c.scale(s, s); c.fillStyle = col; c.strokeStyle = col; c.lineCap = 'round'
    c.lineWidth = 9; c.beginPath(); c.moveTo(0, 0); c.quadraticCurveTo(-6, -60, 4, -110); c.stroke()
    c.lineWidth = 5; for (const [a, b, e, g] of [[4, -100, -70, -150], [4, -105, 80, -152], [0, -80, -40, -140], [3, -90, 40, -146]]) { c.beginPath(); c.moveTo(a, b); c.quadraticCurveTo((a + e) / 2, b - 10, e, g); c.stroke() }
    c.beginPath(); for (let i = 0; i < 9; i++) { const cx = -100 + i * 26 + r() * 10; c.ellipse(cx, -158 - r() * 10, 30 + r() * 14, 11 + r() * 6, 0, 0, 7) } c.fill()
    c.restore()
  }
  // thorn scrub / a boma: a spiky band from x0 to x1
  function thorn(c, x0, x1, y, h, col = N.ground, seed = 2) {
    const r = rng(seed * 31 + 7); c.save(); c.strokeStyle = col; c.fillStyle = col; c.lineCap = 'round'
    c.beginPath(); c.moveTo(x0, y + 6); for (let x = x0; x <= x1; x += 14) c.lineTo(x, y - h * (0.45 + 0.4 * r())); c.lineTo(x1, y + 6); c.closePath(); c.fill()
    c.lineWidth = 3; for (let x = x0; x <= x1; x += 9) { const a = -Math.PI / 2 + (r() - 0.5) * 1.5, l = h * (0.6 + r() * 0.7); c.beginPath(); c.moveTo(x, y - h * 0.3); c.lineTo(x + Math.cos(a) * l, y - h * 0.3 + Math.sin(a) * l); c.stroke() }
    c.restore()
  }
  function tent(c, x, y, s, o = {}) {
    const col = o.col || '#0a0b10'; c.save(); c.translate(x, y); c.scale(s, s)
    if (o.lit) { glow(c, 0, -40, 190, N.fire, 0.5 * o.lit); c.fillStyle = `rgba(240,170,80,${0.55 * o.lit})` } else c.fillStyle = col
    c.beginPath(); c.moveTo(-110, 0); c.lineTo(-6, -118); c.lineTo(6, -118); c.lineTo(110, 0); c.closePath(); c.fill()
    c.strokeStyle = col; c.lineWidth = 6; c.lineJoin = 'round'; c.beginPath(); c.moveTo(-110, 0); c.lineTo(-6, -118); c.lineTo(6, -118); c.lineTo(110, 0); c.stroke()
    c.lineWidth = 3; c.beginPath(); c.moveTo(-6, -118); c.lineTo(-150, 6); c.moveTo(6, -118); c.lineTo(150, 6); c.stroke()
    // the open door: a dark wedge
    c.fillStyle = o.door || '#020203'; c.beginPath(); c.moveTo(0, -100); c.lineTo(34 * (o.open ?? 1), 0); c.lineTo(-34 * (o.open ?? 1), 0); c.closePath(); c.fill()
    c.restore()
  }
  function fire(c, x, y, s, t, k = 1) {
    glow(c, x, y - 20 * s, 300 * s * k, N.fire, 0.55 * k * (0.85 + 0.15 * noise(t * 6, x)))
    const r = rng(Math.round(x) + 3)
    for (let i = 0; i < 6; i++) { const fx = x + (i - 2.5) * 9 * s, fh = (38 + r() * 46) * s * k * (0.7 + 0.3 * noise(t * 4 + i * 5, i)), sw = noise(t * 3 + i, 4) * 8 * s
      c.fillStyle = i % 2 ? 'rgba(246,150,60,0.95)' : 'rgba(252,208,110,0.95)'; c.beginPath(); c.moveTo(fx - 9 * s, y); c.quadraticCurveTo(fx - 6 * s + sw, y - fh * 0.6, fx + sw, y - fh); c.quadraticCurveTo(fx + 7 * s + sw * 0.4, y - fh * 0.5, fx + 9 * s, y); c.closePath(); c.fill() }
    c.strokeStyle = '#06070b'; c.lineWidth = 7 * s; c.lineCap = 'round'; c.beginPath(); c.moveTo(x - 30 * s, y + 3); c.lineTo(x + 26 * s, y - 7 * s); c.moveTo(x - 24 * s, y - 7 * s); c.lineTo(x + 30 * s, y + 3); c.stroke()
  }
  // a small tank engine and wagons, facing +x; (x, y) is the rail under the front buffer
  function train(c, x, y, s, t, o = {}) {
    const col = o.col || C.ink, n = o.wagons ?? 3
    c.save(); c.translate(x, y); c.scale(s, s); c.fillStyle = col; c.strokeStyle = col
    const wheel = (wx, r) => { c.beginPath(); c.arc(wx, -r, r, 0, 7); c.fill(); c.save(); c.translate(wx, -r); c.rotate((o.roll ?? t * 4)); c.strokeStyle = o.spoke || C.paper2; c.lineWidth = 2.5; for (let k = 0; k < 4; k++) { c.rotate(Math.PI / 4); c.beginPath(); c.moveTo(-r * 0.8, 0); c.lineTo(r * 0.8, 0); c.stroke() } c.restore() }
    // engine
    c.fillRect(-250, -128, 70, 96); c.fillRect(-180, -100, 160, 66); c.fillRect(-262, -40, 262, 14)
    c.fillRect(-60, -150, 22, 52); c.fillRect(-66, -158, 34, 10); c.beginPath(); c.arc(-118, -100, 15, Math.PI, 0); c.fill()
    c.beginPath(); c.moveTo(0, -30); c.lineTo(36, -4); c.lineTo(0, -4); c.closePath(); c.fill()
    c.fillStyle = o.win || C.paper2; c.fillRect(-238, -116, 30, 30); c.fillStyle = col
    wheel(-40, 20); wheel(-104, 28); wheel(-170, 28); wheel(-232, 20)
    for (let i = 0; i < n; i++) { const wx = -300 - i * 230; c.fillRect(wx - 200, -96, 200, 66); c.fillRect(wx - 210, -34, 220, 10); wheel(wx - 40, 18); wheel(wx - 160, 18); c.fillRect(wx, -40, 30, 5); if (o.riders) for (let k = 0; k < 4; k++) person(c, wx - 170 + k * 46, -96, 78, { hat: k % 2 ? 'none' : 'cap', col, seated: false }) }
    // smoke
    const sm = o.smoke ?? 1
    if (sm > 0) for (let i = 0; i < 9; i++) { const a = ((t * 0.5 + i / 9) % 1), px = -49 - a * 260 - (o.speed || 0) * a * 200, py = -160 - a * 150 - Math.sin(a * 6 + i) * 12; c.fillStyle = `rgba(60,48,42,${0.5 * (1 - a) * sm})`; c.beginPath(); c.arc(px, py, 14 + a * 46, 0, 7); c.fill() }
    c.restore()
  }
  function rails(c, x0, x1, y, col = C.ink) { c.save(); c.strokeStyle = col; c.lineWidth = 5; c.beginPath(); c.moveTo(x0, y); c.lineTo(x1, y); c.stroke(); c.lineWidth = 6; for (let x = x0 + 10; x < x1; x += 34) { c.beginPath(); c.moveTo(x, y + 2); c.lineTo(x, y + 12); c.stroke() } c.restore() }
  // the engineer: pith helmet, rifle
  function patterson(c, x, y, h, o = {}) {
    const col = o.col || C.ink
    person(c, x, y, h, { hat: 'none', bulk: 1.0, mous: true, ...o, col, hold: o.rifle === false ? null : (q) => { q.save(); q.translate(0, 30); q.rotate(o.aim ?? -1.2); q.fillStyle = col; q.fillRect(-10, -2.2, 62, 4.4); q.fillRect(-22, -3, 16, 7); q.restore() } })
    const s = h / 100, face = o.face || 1
    c.save(); c.translate(x, y); c.scale(s * face, s); c.rotate(o.lean || 0); c.fillStyle = col
    if (o.seated) c.translate(0, 0)
    c.beginPath(); c.ellipse(1.5, -97, 9, 7.5, 0, Math.PI, 0); c.fill(); c.beginPath(); c.ellipse(1.5, -96.6, 13.5, 2.6, -0.06, 0, 7); c.fill()
    c.restore()
  }
  function turban(c, x, y, h, o = {}) {      // a workman
    person(c, x, y, h, { ...o, hat: 'none' })
    const s = h / 100, face = o.face || 1, st = o.stride ?? 0, bob = -Math.abs(Math.cos(o.walk || 0)) * 1.6 * st
    c.save(); c.translate(x, y); c.scale(s * face, s); c.translate(0, bob); c.rotate(o.lean || 0); c.fillStyle = o.col || C.ink; c.beginPath(); c.ellipse(1, -97, 9.5, 6.5, -0.1, 0, 7); c.fill(); c.restore()
  }
  // draw something as one flat shape at part strength (so overlapping limbs don't show through each other)
  let _off = null
  function ghost(c, alpha, draw) {
    if (!_off) { _off = document.createElement('canvas'); _off.width = W; _off.height = H }
    const o = _off.getContext('2d'); o.setTransform(1, 0, 0, 1, 0, 0); o.clearRect(0, 0, W, H); o.setTransform(c.getTransform()); draw(o)
    c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.globalAlpha = alpha; c.drawImage(_off, 0, 0); c.restore()
  }
  window.T2 = { stars, ghost, N, lion, lionDown, eyes, night, ground, acacia, thorn, tent, fire, train, rails, patterson, turban }
})()
