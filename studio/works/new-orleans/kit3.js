// kit3.js: cut-paper pieces for the Battle of New Orleans film, on top of lib.js: soldiers, cannon, a mud wall,
// fog, horses, ships, cypress. Americans are ink, the British are the one red, fire is the one gold.
(function () {
  const { clamp, lerp, rng, noise, mix } = K
  const { W, H, C, layer, person, glow, text, F } = L
  const RED = '#b8402e', INK = '#12100e', GY = 800

  // ---------- sky and ground: d = 0 (night) .. 1 (day); hy = where the ground starts on screen ----------
  function sky(c, d, hy) {
    const g = c.createLinearGradient(0, 0, 0, hy); g.addColorStop(0, mix('#10151f', '#a9b0ae', d)); g.addColorStop(1, mix('#39414d', '#e4dbc2', d)); c.fillStyle = g; c.fillRect(0, 0, W, hy + 1)
    const g2 = c.createLinearGradient(0, hy, 0, H); g2.addColorStop(0, mix('#1d201d', '#958c72', d)); g2.addColorStop(1, mix('#0c0d0c', '#5e5847', d)); c.fillStyle = g2; c.fillRect(0, hy, W, H - hy)
  }
  // view(c, {cx, cy, s, d}, draw): sky, then the world drawn through a camera
  function view(c, o, draw) {
    const s = o.s || 1, cy = o.cy ?? 560, hy = H / 2 + (GY - cy) * s
    sky(c, o.d ?? 1, hy)
    c.save(); c.translate(W / 2, H / 2); c.scale(s, s); c.translate(-o.cx, -cy); draw(); c.restore()
  }
  function stubble(c, x0, x1, d = 1, seed = 5) {
    const r = rng(seed); c.save(); c.strokeStyle = mix('#0a0b0a', '#4d4738', d); c.lineWidth = 3; c.lineCap = 'round'
    for (let x = x0; x < x1; x += 34) { const px = x + r() * 30, py = GY + 14 + r() * 170, l = 8 + r() * 12; c.beginPath(); c.moveTo(px, py); c.lineTo(px + (r() - 0.5) * 8, py - l); c.stroke() }
    c.restore()
  }
  const blob = () => layer('fogblob', 256, 256, (x) => { const g = x.createRadialGradient(128, 128, 0, 128, 128, 128); g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.5, 'rgba(255,255,255,0.45)'); g.addColorStop(1, 'rgba(255,255,255,0)'); x.fillStyle = g; x.fillRect(0, 0, 256, 256) })
  const tint = {}
  function fogTile(col) { if (!tint[col]) { const cv = document.createElement('canvas'); cv.width = cv.height = 256; const x = cv.getContext('2d'); x.drawImage(blob(), 0, 0); x.globalCompositeOperation = 'source-in'; x.fillStyle = col; x.fillRect(0, 0, 256, 256); tint[col] = cv } return tint[col] }
  // fog in screen space: a = how thick; o: y0, y1, col, n, seed, drift
  function fog(c, t, a, o = {}) {
    if (a <= 0) return
    const { y0 = 380, y1 = 980, col = '#d9d6c8', n = 26, seed = 8, drift = 14, x0 = -300, x1 = W + 300 } = o, r = rng(seed), tile = fogTile(col)
    c.save()
    for (let i = 0; i < n; i++) {
      const w = 700 + r() * 900, h = 200 + r() * 260, span = x1 - x0 + w
      const x = x0 - w + ((r() * span + t * drift * (0.4 + r())) % span), y = lerp(y0, y1, r()) - h / 2
      c.globalAlpha = clamp(a * (0.35 + 0.4 * r())); c.drawImage(tile, x, y, w, h)
    }
    c.restore()
  }
  function smoke(c, x, y, r, a, seed = 1, col = '#ece7da') {
    if (a <= 0) return; const q = rng(seed * 13 + 1), tile = fogTile(col); c.save()
    for (let i = 0; i < 6; i++) { const rr = r * (1.1 + 1.1 * q()), px = x + (q() - 0.5) * r * 2.2, py = y + (q() - 0.5) * r * 0.9; c.globalAlpha = clamp(a * (0.5 + 0.5 * q())); c.drawImage(tile, px - rr * 1.3, py - rr * 0.8, rr * 2.6, rr * 1.6) }
    c.restore()
  }
  // a muzzle flash pointing along +x * dir
  function flash(c, x, y, s, a, dir = 1) {
    if (a <= 0) return
    glow(c, x + 30 * s * dir, y, 260 * s, '246,199,112', 0.7 * a)
    c.save(); c.translate(x, y); c.scale(s * dir, s); c.globalAlpha *= clamp(a); c.fillStyle = C.gold2
    c.beginPath(); c.moveTo(0, -5); c.lineTo(46, -22); c.lineTo(34, -7); c.lineTo(96, 0); c.lineTo(34, 7); c.lineTo(46, 22); c.lineTo(0, 5); c.closePath(); c.fill()
    c.fillStyle = '#fff3cf'; c.beginPath(); c.ellipse(20, 0, 22, 6, 0, 0, 7); c.fill(); c.restore()
  }

  // ---------- soldiers ----------
  // kind: brit|reg (shako), mil (brimmed hat), city (top hat), sailor (cap), pirate (kerchief), high (bonnet and feather), officer (bicorne)
  // pose: march (musket on the shoulder), aim, stand (musket grounded), load, none.  down: 0 standing .. 1 on the ground
  const HAT = { brit: 'shako', reg: 'shako', mil: 'brim', city: 'top', sailor: 'cap', pirate: 'kerchief', high: 'bonnet', officer: 'bicorne', none: 'bare' }
  function hat(c, kind) {
    if (kind === 'shako') { c.beginPath(); c.moveTo(-5.5, -96); c.lineTo(-6.5, -112); c.lineTo(9.5, -112); c.lineTo(8.8, -96); c.closePath(); c.fill(); c.fillRect(6, -98.5, 9, 2.4); c.beginPath(); c.ellipse(5, -115.5, 2.6, 4.2, 0, 0, 7); c.fill() }
    else if (kind === 'brim') { c.beginPath(); c.ellipse(1.5, -97, 8, 6, 0, Math.PI, 0); c.fill(); c.beginPath(); c.roundRect(-13, -98.4, 30, 2.8, 1.4); c.fill() }
    else if (kind === 'bicorne') { c.beginPath(); c.moveTo(-14, -95.5); c.quadraticCurveTo(1, -119, 17, -95.5); c.quadraticCurveTo(1, -101, -14, -95.5); c.closePath(); c.fill() }
    else if (kind === 'bonnet') { c.beginPath(); c.ellipse(1, -98, 9.5, 5.2, 0, 0, 7); c.fill(); c.beginPath(); c.ellipse(-3, -108, 3.6, 9, -0.25, 0, 7); c.fill() }
    else if (kind === 'kerchief') { c.beginPath(); c.ellipse(1.5, -93.5, 7.9, 6.4, 0, Math.PI, 0); c.fill(); c.beginPath(); c.moveTo(-5, -95); c.lineTo(-14, -89); c.lineTo(-5, -90); c.closePath(); c.fill() }
  }
  function soldier(c, x, y, h, o = {}) {
    const kind = o.kind || 'brit', col = o.col || (kind === 'brit' || kind === 'high' ? RED : INK), face = o.face || 1, pose = o.pose || 'march', dn = clamp(o.down || 0)
    const hk = HAT[kind], lib = hk === 'top' || hk === 'cap' ? hk : 'none'
    const arm = pose === 'aim' ? 0.56 : pose === 'march' ? 0.2 : pose === 'load' ? 0.3 : pose === 'up' ? 1.15 : (o.arm || 0)
    const gun = pose === 'aim' ? -0.03 + (o.kick || 0) : pose === 'march' ? -1.2 : pose === 'load' ? -1.45 : -1.52
    const hold = (pose === 'none' || pose === 'up' || o.gun === false) ? null : (q) => { q.save(); q.translate(0, 30); q.rotate(gun + arm * 2.5); q.fillStyle = col; q.fillRect(pose === 'aim' ? -22 : -34, -2, 62, 4); q.fillRect(pose === 'aim' ? -34 : -46, -3, 16, 7.5); q.fillRect(pose === 'aim' ? 40 : 28, -0.9, 20, 1.8); q.restore() }
    c.save(); c.translate(x, y)
    if (dn > 0) { c.rotate(-face * dn * 1.5); c.translate(0, dn * 4 * h / 100) }
    person(c, 0, 0, h, { hat: lib, bulk: o.bulk || 1, walk: o.walk, stride: o.stride, lean: o.lean, face, col, arm, hold, belly: o.belly })
    if (lib === 'none' && hk !== 'bare') { const s = h / 100, st = o.stride ?? 0, bob = -Math.abs(Math.cos(o.walk || 0)) * 1.6 * st; c.scale(s * face, s); c.translate(0, bob); c.rotate(o.lean || 0); c.fillStyle = col; hat(c, hk) }
    c.restore()
  }
  // a field gun facing +x*face; (x, y) is the ground under the wheel
  function cannon(c, x, y, s, o = {}) {
    const col = o.col || INK, face = o.face || 1
    c.save(); c.translate(x - (o.rec || 0) * 26 * s * face, y); c.scale(s * face, s); c.fillStyle = col; c.strokeStyle = col; c.lineCap = 'round'
    c.lineWidth = 9; c.beginPath(); c.moveTo(-4, -30); c.lineTo(-92, -2); c.stroke()
    c.save(); c.translate(0, -34); c.rotate(-(o.elev ?? 0.06)); c.beginPath(); c.moveTo(-34, -11); c.lineTo(78, -7.5); c.lineTo(78, -9.5); c.lineTo(84, -9.5); c.lineTo(84, 9.5); c.lineTo(78, 9.5); c.lineTo(78, 7.5); c.lineTo(-34, 11); c.closePath(); c.fill(); c.beginPath(); c.arc(-36, 0, 11, 0, 7); c.fill(); c.beginPath(); c.arc(-50, 0, 4.5, 0, 7); c.fill(); c.restore()
    c.lineWidth = 6; c.beginPath(); c.arc(0, -30, 27, 0, 7); c.stroke(); c.lineWidth = 3.4
    c.save(); c.translate(0, -30); c.rotate((o.rec || 0) * -0.8); for (let k = 0; k < 6; k++) { c.rotate(Math.PI / 6); c.beginPath(); c.moveTo(-27, 0); c.lineTo(27, 0); c.stroke() } c.restore()
    c.beginPath(); c.arc(0, -30, 6, 0, 7); c.fill(); c.restore()
  }
  // the mud wall in cross-section, the ditch on its +x side. (x, y) = ground at the foot of the wall's face
  function wall(c, x, y, h, o = {}) {
    const col = o.col || INK, p = clamp(o.p ?? 1), hh = h * p
    c.save(); c.fillStyle = col
    c.beginPath(); c.moveTo(x - 190, y + 4); c.lineTo(x - 150, y - hh * 0.38); c.lineTo(x - 104, y - hh * 0.38); c.quadraticCurveTo(x - 92, y - hh * 1.0, x - 60, y - hh); c.lineTo(x - 26, y - hh); c.quadraticCurveTo(x - 4, y - hh * 0.6, x + 8, y + 4); c.closePath(); c.fill()
    c.beginPath(); c.moveTo(x + 4, y); c.lineTo(x + 30, y + 58); c.lineTo(x + 150, y + 58); c.lineTo(x + 176, y); c.closePath(); c.fill()
    if (o.water) { c.fillStyle = o.water; c.fillRect(x + 28, y + 40, 124, 18) }
    c.restore()
  }
  function cypress(c, x, y, s, col = INK, seed = 1) {
    const r = rng(seed * 19 + 3); c.save(); c.translate(x, y); c.scale(s, s); c.fillStyle = col; c.strokeStyle = col; c.lineCap = 'round'
    c.beginPath(); c.moveTo(-34, 0); c.quadraticCurveTo(-10, -30, -9, -120); c.lineTo(-6, -330); c.lineTo(6, -330); c.lineTo(9, -120); c.quadraticCurveTo(10, -30, 34, 0); c.closePath(); c.fill()
    for (let i = 0; i < 9; i++) { const yy = -210 - (i % 5) * 30 - r() * 14, w = 62 + r() * 56; c.beginPath(); c.ellipse((r() - 0.5) * 150, yy, w, 24 + r() * 12, 0, 0, 7); c.fill() } c.beginPath(); c.ellipse(0, -270, 96, 62, 0, 0, 7); c.fill()
    c.lineWidth = 3.5; for (let i = 0; i < 16; i++) { const mx = -120 + r() * 240, my = -220 - r() * 110, l = 40 + r() * 90; c.beginPath(); c.moveTo(mx, my); c.quadraticCurveTo(mx + 6, my + l * 0.5, mx - 2 + r() * 8, my + l); c.stroke() }
    c.restore()
  }
  // a horse, side on, facing +x*face; (x, y) ground under the middle. o: gait (phase), stride 0..1, gallop, rear (rad), rider(c) drawn at the saddle
  function hleg(c, hx, hy, fx, fy, bend, w) {
    const mx = (hx + fx) / 2, my = (hy + fy) / 2, dx = fx - hx, dy = fy - hy, d = Math.hypot(dx, dy) || 1, kx = mx + (-dy / d) * bend, ky = my + (dx / d) * bend
    c.lineWidth = w; c.beginPath(); c.moveTo(hx, hy); c.lineTo(kx, ky); c.stroke(); c.lineWidth = w * 0.6; c.beginPath(); c.moveTo(kx, ky); c.lineTo(fx, fy); c.stroke()
    c.beginPath(); c.moveTo(fx - 4.5, fy + 1); c.lineTo(fx - 2.5, fy - 6); c.lineTo(fx + 4, fy - 6); c.lineTo(fx + 6.5, fy + 1); c.closePath(); c.fill()
  }
  function horse(c, x, y, s, o = {}) {
    const col = o.col || INK, face = o.face || 1, ph = o.gait || 0, st = o.stride ?? 0, gal = o.gallop || 0
    c.save(); c.translate(x, y); c.scale(s * face, s); c.translate(-40, 0); c.rotate(-(o.rear || 0)); c.translate(40, 0)
    c.fillStyle = col; c.strokeStyle = col; c.lineCap = 'round'; c.lineJoin = 'round'
    const by = -92 - Math.abs(Math.sin(ph)) * 3 * st - gal * 4 * Math.sin(ph * 2)
    const foot = (off, base, hind) => { const a = ph + off, sw = -Math.cos(a) * (16 + gal * 26) * st, lift = Math.max(0, Math.sin(a)) * (10 + gal * 22) * st; return [base + sw, -lift] }
    let f = foot(Math.PI, 40, false); hleg(c, 40, by + 22, f[0], f[1], -5, 9)
    f = foot(Math.PI * 0.5, -44, true); hleg(c, -44, by + 20, f[0], f[1], 9, 11)
    c.lineWidth = 7; const ts = Math.sin(ph * 0.7) * 6 + gal * st * 10; c.beginPath(); c.moveTo(-60, by - 4); c.bezierCurveTo(-82 - ts, by - 2, -84 - ts, by + 34, -78 - ts * 1.5, by + 56); c.stroke()
    c.beginPath(); c.moveTo(-62, by + 4); c.bezierCurveTo(-64, by - 16, -34, by - 14, -6, by - 9); c.bezierCurveTo(16, by - 8, 34, by - 18, 50, by - 10)
    c.bezierCurveTo(60, by - 2, 58, by + 22, 46, by + 27); c.bezierCurveTo(22, by + 34, -22, by + 30, -44, by + 28); c.bezierCurveTo(-58, by + 26, -62, by + 16, -62, by + 4); c.closePath(); c.fill()
    c.save(); c.translate(46, by - 2); c.rotate((o.head || 0) - gal * st * 0.12)
    c.beginPath(); c.moveTo(-16, -8); c.bezierCurveTo(-2, -24, 6, -40, 12, -52); c.lineTo(30, -46); c.bezierCurveTo(27, -28, 24, -6, 8, 18); c.closePath(); c.fill()
    c.beginPath(); c.moveTo(10, -52); c.lineTo(15, -66); c.lineTo(21, -55); c.quadraticCurveTo(34, -52, 55, -31); c.quadraticCurveTo(60, -24, 54, -19); c.lineTo(47, -19); c.quadraticCurveTo(36, -30, 24, -30); c.closePath(); c.fill()
    c.restore()
    if (o.rider) { c.save(); c.translate(-8, by - 10); o.rider(c); c.restore() }
    f = foot(0, 44, false); hleg(c, 44, by + 22, f[0], f[1], -5, 10)
    f = foot(Math.PI * 1.5, -40, true); hleg(c, -42, by + 20, f[0], f[1], 10, 12.5)
    c.restore()
  }
  // a rider for horse(): sits at the saddle, in the horse's own units
  const rider = (kind, col, o = {}) => (c) => { c.rotate(o.lean || 0); soldier(c, 0, 46, 96, { kind, col, pose: o.pose || 'none', arm: o.arm, face: 1 }); c.fillStyle = col; c.save(); c.translate(4, 4); c.rotate(-0.25); c.fillRect(-5, -2, 10, 40); c.fillRect(-5, 36, 16, 5); c.restore() }
  // a three-masted ship, sailing toward +x*face; (x, y) is the waterline amidships
  function ship(c, x, y, s, o = {}) {
    const col = o.col || INK, face = o.face || 1
    c.save(); c.translate(x, y + Math.sin((o.t || 0) * 1.1 + x * 0.01) * 3 * s); c.rotate(Math.sin((o.t || 0) * 0.8 + x) * 0.012); c.scale(s * face, s); c.fillStyle = col; c.strokeStyle = col
    c.beginPath(); c.moveTo(-120, -26); c.lineTo(-112, 4); c.quadraticCurveTo(0, 16, 104, 2); c.lineTo(140, -30); c.lineTo(96, -22); c.lineTo(-96, -22); c.closePath(); c.fill()
    c.lineWidth = 4; c.beginPath(); c.moveTo(118, -26); c.lineTo(176, -44); c.stroke()
    for (const [mx, mh] of [[-70, 150], [0, 190], [66, 160]]) {
      c.lineWidth = 4; c.beginPath(); c.moveTo(mx, -22); c.lineTo(mx, -22 - mh); c.stroke()
      const n = mh > 170 ? 3 : 2; for (let k = 0; k < n; k++) { const sy = -40 - k * (mh - 30) / n, sh = (mh - 44) / n, sw = 52 - k * 9; c.beginPath(); c.moveTo(mx - sw, sy); c.quadraticCurveTo(mx + 12, sy - sh * 0.5, mx - sw + 6, sy - sh); c.lineTo(mx + sw - 6, sy - sh); c.quadraticCurveTo(mx + sw + 18, sy - sh * 0.5, mx + sw, sy); c.closePath(); c.fill() }
    }
    c.beginPath(); c.moveTo(66, -182); c.lineTo(168, -46); c.lineTo(84, -40); c.closePath(); c.fill()
    if (o.flag) { c.fillStyle = o.flag; c.fillRect(0, -232, 30, 16) }
    c.restore()
  }
  function ladder(c, x, y, len, rot, col = INK, lw = 5) {
    c.save(); c.translate(x, y); c.rotate(rot); c.strokeStyle = col; c.lineWidth = lw; c.beginPath(); c.moveTo(0, -11); c.lineTo(len, -11); c.moveTo(0, 11); c.lineTo(len, 11); for (let k = 14; k < len - 6; k += 24) { c.moveTo(k, -11); c.lineTo(k, 11) } c.stroke(); c.restore()
  }
  function bundle(c, x, y, s, col = INK) { c.save(); c.translate(x, y); c.scale(s, s); c.fillStyle = col; c.beginPath(); c.roundRect(-46, -26, 92, 26, 12); c.fill(); c.strokeStyle = C.paper3; c.lineWidth = 3; for (const k of [-24, 0, 24]) { c.beginPath(); c.moveTo(k, -25); c.lineTo(k, -1); c.stroke() } c.restore() }
  // a plain big house with a columned porch: the President's house
  function house(c, x, y, s, col = INK, win = null) {
    c.save(); c.translate(x, y); c.scale(s, s); c.fillStyle = col
    c.fillRect(-300, -170, 600, 170); c.fillRect(-312, -182, 624, 14); c.beginPath(); c.moveTo(-110, -182); c.lineTo(0, -236); c.lineTo(110, -182); c.closePath(); c.fill()
    for (const k of [-250, -190, 190, 250]) c.fillRect(k - 5, -206, 10, 26)
    if (win) { c.fillStyle = win; for (let r = 0; r < 2; r++) for (let k = 0; k < 11; k++) { const wx = -270 + k * 54; if (Math.abs(wx) < 100) continue; c.fillRect(wx - 11, -146 + r * 72, 22, r ? 40 : 46) } for (const k of [-66, -22, 22, 66]) c.fillRect(k - 9, -160, 18, 150) ; c.fillStyle = col; for (const k of [-88, -44, 0, 44, 88]) c.fillRect(k - 6, -170, 12, 170) }
    c.restore()
  }
  // ---------- the same people seen square on (from the front or the back: a flat shape can't tell) ----------
  function fhat(c, k) {
    if (k === 'shako') { c.beginPath(); c.moveTo(-7, -96); c.lineTo(-8, -112); c.lineTo(8, -112); c.lineTo(7, -96); c.closePath(); c.fill(); c.beginPath(); c.ellipse(0, -116, 2.6, 4.5, 0, 0, 7); c.fill() }
    else if (k === 'brim') { c.beginPath(); c.ellipse(0, -97, 8, 6, 0, Math.PI, 0); c.fill(); c.beginPath(); c.roundRect(-15, -98.4, 30, 2.8, 1.4); c.fill() }
    else if (k === 'bicorne') { c.beginPath(); c.moveTo(-19, -95); c.quadraticCurveTo(0, -121, 19, -95); c.quadraticCurveTo(0, -102, -19, -95); c.closePath(); c.fill() }
    else if (k === 'bonnet') { c.beginPath(); c.ellipse(0, -98, 10, 5, 0, 0, 7); c.fill(); c.beginPath(); c.ellipse(-5, -108, 3.4, 9, -0.2, 0, 7); c.fill() }
    else if (k === 'top') { c.fillRect(-7.5, -113, 15, 16); c.beginPath(); c.roundRect(-12, -98.6, 24, 2.6, 1.3); c.fill() }
    else if (k === 'cap') { c.beginPath(); c.ellipse(0, -96.5, 8.5, 4.6, 0, Math.PI, 0); c.fill(); c.fillRect(-9, -97.4, 18, 2) }
    else if (k === 'kerchief') { c.beginPath(); c.ellipse(0, -93.5, 7.9, 6.4, 0, Math.PI, 0); c.fill(); c.beginPath(); c.moveTo(6, -95.5); c.lineTo(15, -89); c.lineTo(6, -90); c.closePath(); c.fill() }
  }
  // o: kind, col, gun slope|rest|none, walk (phase), stride, down 0..1, side (which way he falls), arms 0..1 raised
  function front(c, x, y, h, o = {}) {
    const kind = o.kind || 'brit', col = o.col || (kind === 'brit' || kind === 'high' ? RED : INK), s = h / 100, dn = clamp(o.down || 0), st = o.stride ?? 0, ph = o.walk || 0, gun = o.gun || 'slope'
    c.save(); c.translate(x, y); c.scale(s, s); if (dn > 0) { c.rotate((o.side || 1) * dn * 1.5); c.translate(0, dn * 4) }
    c.fillStyle = col; c.strokeStyle = col; c.lineCap = 'round'
    const l1 = Math.max(0, Math.sin(ph)) * 7 * st, l2 = Math.max(0, -Math.sin(ph)) * 7 * st, bob = -Math.abs(Math.cos(ph)) * 1.8 * st
    c.fillRect(-9.5, -47 + bob, 8, 47 - l1 - bob); c.fillRect(1.5, -47 + bob, 8, 47 - l2 - bob); c.fillRect(-11, -l1 - 2.5, 10.5, 2.5); c.fillRect(0.5, -l2 - 2.5, 10.5, 2.5)
    c.translate(0, bob)
    c.beginPath(); c.moveTo(-13, -82); c.quadraticCurveTo(0, -87, 13, -82); c.lineTo(15, -38); c.lineTo(-15, -38); c.closePath(); c.fill()
    const up = o.arms || 0
    for (const sd of [-1, 1]) { c.save(); c.translate(sd * 14.5, -79); c.rotate(sd * (-0.08 - up * 2.7)); c.beginPath(); c.roundRect(-3.4, 0, 6.8, 35, 3.4); c.fill(); c.restore() }
    c.beginPath(); c.arc(0, -91, 7.2, 0, 7); c.fill(); fhat(c, HAT[kind])
    if (gun === 'slope') { c.lineWidth = 3.4; c.beginPath(); c.moveTo(-16, -44); c.lineTo(-5, -126); c.stroke(); c.lineWidth = 1.5; c.beginPath(); c.moveTo(-5, -126); c.lineTo(-2.6, -146); c.stroke() }
    else if (gun === 'rest') { c.lineWidth = 4; c.beginPath(); c.moveTo(-12, -76); c.lineTo(15, -55); c.stroke() }
    c.restore()
  }
  // the wall seen from the field: a long dark bank, its ditch in front; o.gaps = x of the gun openings
  function wallFront(c, x0, x1, y, h, o = {}) {
    const col = o.col || INK
    c.save(); c.fillStyle = col; c.beginPath(); c.moveTo(x0, y + 4)
    for (let x = x0; x <= x1; x += 24) { let top = y - h * (0.93 + 0.07 * noise(x * 0.013, 4)); for (const g of (o.gaps || [])) { const d = Math.abs(x - g); if (d < 34) top = y - h * 0.45 } c.lineTo(x, top) }
    c.lineTo(x1, y + 4); c.closePath(); c.fill()
    c.fillStyle = o.ditch || '#3b3a36'; c.fillRect(x0, y + 2, x1 - x0, h * 0.34)
    if (o.water) { c.fillStyle = o.water; c.fillRect(x0, y + h * 0.16, x1 - x0, h * 0.08) }
    c.fillStyle = col; for (const g of (o.gaps || [])) { c.beginPath(); c.arc(g, y - h * 0.62, h * 0.17 * (o.muz ?? 1), 0, 7); c.fill() }
    c.restore()
  }
  window.B = { RED, INK, GY, sky, view, stubble, fog, smoke, flash, soldier, front, wallFront, cannon, wall, cypress, horse, rider, ship, ladder, bundle, house }
})()
