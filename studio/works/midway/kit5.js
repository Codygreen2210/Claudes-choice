// kit5.js: cut-paper pieces for the Midway film: carriers, aircraft seen from the side and from above, a destroyer,
// sea and cloud, fire and smoke. Japanese ships and planes are the one red; American ones are ink; fire is the one gold.
(function () {
  const { clamp, lerp, rng, noise } = K
  const hx = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16)), mix = (a, b, p) => { const A = hx(a), B = hx(b); return '#' + A.map((v, i) => Math.round(v + (B[i] - v) * p).toString(16).padStart(2, '0')).join('') }
  const { W, H, C, layer, person, glow, text, F } = L
  const INK = '#10141c', RED = '#b8402e', SEA = { sky0: '#8fa3b6', sky1: '#d9d6c2', sea0: '#6e8597', sea1: '#2f4354' }

  // ---------- sky and sea. o: hy (horizon), dusk 0..1, night 0..1 ----------
  function sea(c, t, o = {}) {
    const hy = o.hy ?? 620, dk = o.dusk || 0, nt = o.night || 0
    const top = mix(mix(SEA.sky0, '#51506a', dk), '#0b1020', nt), hor = mix(mix(SEA.sky1, '#e9b98a', dk), '#27324e', nt)
    const g = c.createLinearGradient(0, 0, 0, hy); g.addColorStop(0, top); g.addColorStop(1, hor); c.fillStyle = g; c.fillRect(-400, -400, W + 800, hy + 401)
    const s0 = mix(mix(SEA.sea0, '#6b6a78', dk), '#141d33', nt), s1 = mix(mix(SEA.sea1, '#2b2d40', dk), '#070b16', nt)
    const g2 = c.createLinearGradient(0, hy, 0, H); g2.addColorStop(0, s0); g2.addColorStop(1, s1); c.fillStyle = g2; c.fillRect(-400, hy, W + 800, H - hy + 400)
    // swell: short pale strokes, denser toward the horizon
    c.save(); c.strokeStyle = `rgba(235,240,240,${0.2 * (1 - nt * 0.6)})`; c.lineCap = 'round'; const r = rng(o.seed || 6)
    for (let i = 0; i < 150; i++) { const d = r() ** 1.8, y = hy + 8 + d * (H - hy), w = 20 + d * 90, x = ((r() * (W + 400) + t * (10 + d * 50) * (o.drift ?? 1)) % (W + 400)) - 200; c.lineWidth = 1.5 + d * 3; c.beginPath(); c.moveTo(x, y); c.quadraticCurveTo(x + w / 2, y - 3 - d * 4, x + w, y); c.stroke() }
    c.restore()
  }
  const blob = () => layer('mwblob', 256, 256, (x) => { const g = x.createRadialGradient(128, 128, 0, 128, 128, 128); g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.55, 'rgba(255,255,255,0.5)'); g.addColorStop(1, 'rgba(255,255,255,0)'); x.fillStyle = g; x.fillRect(0, 0, 256, 256) })
  const tints = {}
  function tile(col) { if (!tints[col]) { const cv = document.createElement('canvas'); cv.width = cv.height = 256; const x = cv.getContext('2d'); x.drawImage(blob(), 0, 0); x.globalCompositeOperation = 'source-in'; x.fillStyle = col; x.fillRect(0, 0, 256, 256); tints[col] = cv } return tints[col] }
  function puff(c, x, y, r, a, col = '#f1efe6', seed = 1, flat = 0.6) { if (a <= 0) return; const q = rng(seed * 13 + 1), tl = tile(col); c.save(); for (let i = 0; i < 6; i++) { const rr = r * (0.9 + 1.0 * q()), px = x + (q() - 0.5) * r * 2.2, py = y + (q() - 0.5) * r * flat; c.globalAlpha = clamp(a * (0.5 + 0.5 * q())); c.drawImage(tl, px - rr * 1.3, py - rr * 0.8, rr * 2.6, rr * 1.6) } c.restore() }
  // a deck of scattered cloud across the frame (screen space). o: y0, y1, n, a, drift, col
  function clouds(c, t, o = {}) { const { y0 = 120, y1 = 420, n = 12, a = 0.8, drift = 12, col = '#f1efe6', seed = 4 } = o, r = rng(seed); for (let i = 0; i < n; i++) { const w = 260 + r() * 420, x = ((r() * (W + 900) + t * drift * (0.5 + r())) % (W + 900)) - 450, y = lerp(y0, y1, r()); puff(c, x, y, w * 0.32, a * (0.6 + 0.4 * r()), col, i + seed * 7, 0.35) } }
  // a column of smoke rising from (x, y) and leaning downwind. k = how big, a = how thick
  function smokeCol(c, x, y, t, k = 1, a = 1, col = '#1b1b20', wind = 1) { if (a <= 0) return; for (let i = 0; i < 12; i++) { const u = (((t * 0.16 + i / 12) % 1) + 1) % 1; puff(c, x + u * u * 520 * k * wind + Math.sin(u * 6 + i) * 14 * k, y - u * 380 * k, (22 + u * 95) * k, a * (1 - u * 0.8), col, i + 3, 0.9) } }
  function flame(c, x, y, s, t, k = 1) { if (k <= 0) return; glow(c, x, y - 20 * s, 170 * s * k, '246,150,60', 0.32 * k); for (let i = 0; i < 7; i++) { const fx = x + (i - 3) * 10 * s, fh = (44 + ((i * 37) % 50)) * s * k * (0.7 + 0.3 * noise(t * 4 + i * 5, i + x * 0.01)), sw = noise(t * 3 + i, 4) * 9 * s; c.fillStyle = i % 2 ? 'rgba(214,92,40,0.96)' : 'rgba(244,206,110,0.96)'; c.beginPath(); c.moveTo(fx - 10 * s, y); c.quadraticCurveTo(fx - 6 * s + sw, y - fh * 0.6, fx + sw, y - fh); c.quadraticCurveTo(fx + 7 * s + sw * 0.4, y - fh * 0.5, fx + 10 * s, y); c.closePath(); c.fill() } }
  function burst(c, x, y, r, a) { if (a <= 0) return; glow(c, x, y, r * 3.2, '246,199,112', 0.9 * a); c.save(); c.globalAlpha = clamp(a); c.fillStyle = '#fff1c4'; c.beginPath(); for (let k = 0; k < 16; k++) { const an = k / 16 * 6.283, rr = r * (k % 2 ? 0.5 : 1); c.lineTo(x + Math.cos(an) * rr, y + Math.sin(an) * rr) } c.closePath(); c.fill(); c.restore() }
  function splash(c, x, y, s, p, col = '#eef2f2') { if (p <= 0 || p >= 1) return; c.save(); c.fillStyle = col; c.globalAlpha = 1 - p * p; const h = Math.sin(p * Math.PI) * 150 * s; c.beginPath(); c.moveTo(x - 26 * s, y); c.quadraticCurveTo(x - 10 * s, y - h, x, y - h * 1.1); c.quadraticCurveTo(x + 10 * s, y - h, x + 26 * s, y); c.closePath(); c.fill(); c.restore() }

  // ---------- aircraft carrier, side on, bow toward +x*face. (x, y) = waterline amidships; length about 520*s ----------
  // o: jp (Japanese: flat deck, tiny island, funnel bent down the side) | us (big island and stack), col, planes (n on deck), fire 0..1, list (rad), t
  function carrier(c, x, y, s, o = {}) {
    const jp = o.jp, col = o.col || (jp ? RED : INK), face = o.face || 1
    c.save(); c.translate(x, y); c.rotate(o.list || 0); c.scale(s * face, s); c.fillStyle = col; c.strokeStyle = col
    // hull
    c.beginPath(); c.moveTo(-250, -26); c.lineTo(-240, 4); c.lineTo(226, 4); c.lineTo(262, -30); c.lineTo(250, -34); c.lineTo(-250, -34); c.closePath(); c.fill()
    // flight deck: one long plank, overhanging at both ends, on thin supports
    c.fillRect(-268, -52, 540, 9); for (const k of [-258, -236, 240, 258]) c.fillRect(k, -46, 4, 16); c.fillRect(-210, -44, 420, 12)
    if (jp) { c.fillRect(40, -70, 26, 19); c.fillRect(50, -92, 3, 24); c.fillRect(42, -84, 20, 2.5); c.beginPath(); c.moveTo(-10, -40); c.quadraticCurveTo(0, -18, 24, -16); c.lineTo(24, -6); c.quadraticCurveTo(-12, -8, -24, -40); c.closePath(); c.fill() }
    else { c.fillRect(20, -88, 92, 38); c.fillRect(44, -116, 40, 30); c.fillRect(30, -98, 22, 12); c.fillRect(92, -140, 4, 54); c.fillRect(78, -128, 32, 3); c.fillRect(26, -128, 3, 42) }
    const n = o.planes || 0; for (let i = 0; i < n; i++) { const px = -230 + i * 30; if (px > 0 && px < 120) continue; c.beginPath(); c.ellipse(px, -57, 10, 3.2, 0, 0, 7); c.fill(); c.fillRect(px - 10, -64, 2.5, 8); c.fillRect(px - 2, -59, 12, 2) }
    c.restore()
    const f = o.fire || 0
    if (f > 0) { const t = o.t || 0; for (const [dx, k] of (o.fires || [[-120, 1], [10, 1.2], [140, 0.9]])) { const fx = x + dx * s * face, fy = y - 52 * s; smokeCol(c, fx, fy - 20 * s, t + Math.abs(dx) * 0.01, 0.5 * s * k * (0.6 + 0.4 * f), 0.62 * f, '#17171c', o.wind ?? -1); flame(c, fx, fy, 1.15 * s * k, t + dx, f) } }
  }
  function destroyer(c, x, y, s, o = {}) {
    const col = o.col || RED, face = o.face || 1
    c.save(); c.translate(x, y); c.scale(s * face, s); c.fillStyle = col
    c.beginPath(); c.moveTo(-150, -14); c.lineTo(-142, 4); c.lineTo(132, 4); c.lineTo(160, -20); c.lineTo(60, -18); c.lineTo(60, -12); c.lineTo(-150, -12); c.closePath(); c.fill()
    c.fillRect(40, -42, 34, 26); c.fillRect(52, -70, 3, 30); c.fillRect(-4, -40, 16, 28); c.fillRect(-42, -36, 16, 24); c.fillRect(96, -27, 26, 5); c.fillRect(-110, -21, 26, 5); c.fillRect(88, -30, 12, 12); c.fillRect(-100, -24, 12, 12)
    c.restore()
  }
  // a battleship, side on, bow toward +x*face: long low hull, gun turrets fore and aft, a tall stepped tower, two funnels
  function battleship(c, x, y, s, o = {}) {
    const col = o.col || RED, face = o.face || 1
    c.save(); c.translate(x, y); c.rotate(o.list || 0); c.scale(s * face, s); c.fillStyle = col; c.strokeStyle = col; c.lineCap = 'butt'
    c.beginPath(); c.moveTo(-214, -15); c.lineTo(-200, 6); c.lineTo(188, 6); c.lineTo(226, -24); c.lineTo(150, -17); c.lineTo(-214, -17); c.closePath(); c.fill()
    const turret = (tx, ty, dir) => { c.beginPath(); c.moveTo(tx - 20, ty); c.lineTo(tx - 16, ty - 13); c.lineTo(tx + 16, ty - 13); c.lineTo(tx + 20, ty); c.closePath(); c.fill(); c.lineWidth = 3.4; c.beginPath(); c.moveTo(tx + dir * 12, ty - 9); c.lineTo(tx + dir * 62, ty - 15); c.stroke() }
    turret(128, -17, 1); c.fillRect(74, -30, 40, 14); turret(92, -30, 1); c.fillRect(-116, -30, 40, 14); turret(-96, -30, -1); turret(-140, -17, -1)
    let w = 46, yy = -17; for (let k = 0; k < 6; k++) { c.fillRect(30 - w / 2, yy - 19, w, 19); yy -= 19; w -= 5 } c.fillRect(27, yy - 34, 6, 34); c.fillRect(14, yy - 20, 32, 3)
    c.beginPath(); c.moveTo(-22, -17); c.lineTo(-26, -74); c.lineTo(-4, -74); c.lineTo(2, -17); c.closePath(); c.fill(); c.beginPath(); c.moveTo(-52, -17); c.lineTo(-55, -62); c.lineTo(-38, -62); c.lineTo(-34, -17); c.closePath(); c.fill()
    c.lineWidth = 3; c.beginPath(); c.moveTo(-70, -17); c.lineTo(-66, -98); c.moveTo(-62, -17); c.lineTo(-66, -98); c.stroke(); c.fillRect(-78, -84, 24, 3)
    c.restore()
  }
  // ---------- aircraft from the side, nose toward +x. (x, y) = centre. o: col, rot (rad, + nose down), torp, float, flaps, gear, prop (t) ----------
  function plane(c, x, y, s, o = {}) {
    const col = o.col || INK
    c.save(); c.translate(x, y); c.rotate(o.rot || 0); c.scale(s * (o.face || 1), s); c.fillStyle = col; c.strokeStyle = col; c.lineCap = 'round'
    // fuselage: long and lean, a blunt radial cowl at the nose, tapering to the tail
    c.beginPath(); c.moveTo(60, -8); c.lineTo(63, -3); c.lineTo(63, 4); c.lineTo(60, 9); c.lineTo(40, 11); c.quadraticCurveTo(-10, 12, -70, 2); c.lineTo(-70, -2); c.quadraticCurveTo(-30, -7, 14, -9); c.closePath(); c.fill()
    c.beginPath(); c.moveTo(63, -2); c.lineTo(70, 0.5); c.lineTo(63, 3); c.closePath(); c.fill()
    // a low, long canopy
    c.beginPath(); c.moveTo(30, -8.5); c.quadraticCurveTo(24, -16.5, 12, -16.5); c.lineTo(o.long === false ? 4 : -12, -15.5); c.quadraticCurveTo(o.long === false ? -6 : -22, -13, o.long === false ? -10 : -27, -6.5); c.closePath(); c.fill()
    // tall fin, tailplane
    c.beginPath(); c.moveTo(-48, -3); c.lineTo(-62, -27); c.quadraticCurveTo(-69, -29, -72, -22); c.lineTo(-70, 0); c.closePath(); c.fill()
    c.beginPath(); c.moveTo(-52, -1); c.lineTo(-74, 4.5); c.lineTo(-64, 5.5); c.lineTo(-48, 2); c.closePath(); c.fill()
    // the near wing, swept back and down toward us
    c.beginPath(); c.moveTo(34, 6); c.lineTo(8, 6); c.lineTo(-14, 22); c.quadraticCurveTo(-12, 26, -4, 25); c.closePath(); c.fill()
    if (o.flaps) { c.save(); c.globalAlpha *= 0.9; c.beginPath(); c.moveTo(6, 8); c.lineTo(-14, 22); c.lineTo(-24, 14); c.closePath(); c.fill(); c.restore() }
    if (o.gear) { c.lineWidth = 3.5; c.beginPath(); c.moveTo(22, 10); c.lineTo(24, 26); c.stroke(); c.beginPath(); c.ellipse(24, 28, 7.5, 5, 0, 0, 7); c.fill() }
    if (o.float) { c.lineWidth = 3; c.beginPath(); c.moveTo(30, 10); c.lineTo(26, 28); c.moveTo(4, 10); c.lineTo(8, 28); c.stroke(); c.beginPath(); c.moveTo(-34, 28); c.lineTo(52, 28); c.quadraticCurveTo(66, 31, 52, 38); c.lineTo(-28, 37); c.closePath(); c.fill() }
    if (o.torp) { c.beginPath(); c.roundRect(-30, 14, 80, 6.5, 3.2); c.fill(); c.fillRect(-35, 12, 5, 10.5) }
    if (o.bomb) { c.beginPath(); c.ellipse(18, 15, 13, 4.2, 0, 0, 7); c.fill() }
    // the propeller as a blurred disc seen edge on
    c.save(); c.globalAlpha *= 0.5; c.fillRect(66, -23, 2.6, 47); c.restore()
    c.restore()
  }
  // aircraft from directly above, nose toward -y (up the screen) unless rot. A cross that can only be an aeroplane.
  function planeTop(c, x, y, s, o = {}) {
    const col = o.col || INK
    c.save(); c.translate(x, y); c.rotate(o.rot || 0); c.scale(s, s); c.fillStyle = col
    c.beginPath(); c.ellipse(0, 2, 6.5, 30, 0, 0, 7); c.fill()
    c.beginPath(); c.moveTo(-40, -3); c.quadraticCurveTo(-42, -10, -34, -12); c.lineTo(34, -12); c.quadraticCurveTo(42, -10, 40, -3); c.lineTo(8, 4); c.lineTo(-8, 4); c.closePath(); c.fill()
    c.beginPath(); c.moveTo(-15, 24); c.lineTo(15, 24); c.lineTo(12, 31); c.lineTo(-12, 31); c.closePath(); c.fill()
    if (o.disc) { c.strokeStyle = o.disc; c.lineWidth = 2; c.beginPath(); c.arc(-24, -6, 5, 0, 7); c.stroke(); c.beginPath(); c.arc(24, -6, 5, 0, 7); c.stroke() }
    c.restore()
  }
  // a carrier from directly above, bow toward +x
  function carrierTop(c, x, y, s, o = {}) {
    const col = o.col || RED
    c.save(); c.translate(x, y); c.rotate(o.rot || 0); c.scale(s, s)
    if (o.wake !== false) { c.strokeStyle = 'rgba(238,242,242,0.6)'; c.lineWidth = 5; c.beginPath(); c.moveTo(-130, -8); c.lineTo(-330, -34); c.moveTo(-130, 8); c.lineTo(-330, 34); c.stroke(); c.fillStyle = 'rgba(238,242,242,0.35)'; c.beginPath(); c.moveTo(-130, -8); c.lineTo(-300, 0); c.lineTo(-130, 8); c.closePath(); c.fill() }
    c.fillStyle = col; c.beginPath(); c.roundRect(-140, -17, 280, 34, 5); c.fill(); c.fillStyle = o.deck || 'rgba(238,226,200,0.55)'; c.fillRect(-120, -1.5, 240, 3); c.fillStyle = col; c.fillRect(20, o.jp ? 17 : -25, 36, 8)
    if (o.sun) { c.fillStyle = '#f4ead2'; c.beginPath(); c.arc(108, 0, 12, 0, 7); c.fill(); c.fillStyle = col; c.beginPath(); c.arc(108, 0, 7, 0, 7); c.fill() }
    c.restore()
    if (o.fire > 0) { burst(c, x, y, 18 * s * o.fire, 0.5 * o.fire); puff(c, x - 60 * s, y - 20 * s, 70 * s, 0.8 * o.fire, '#17171c', 5) }
  }
  function bomb(c, x, y, s, rot, col = INK) { c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s); c.fillStyle = col; c.beginPath(); c.ellipse(0, 0, 16, 5.5, 0, 0, 7); c.fill(); c.beginPath(); c.moveTo(-12, 0); c.lineTo(-24, -8); c.lineTo(-20, 0); c.lineTo(-24, 8); c.closePath(); c.fill(); c.restore() }
  // a naval officer: the person from the first kit, in a peaked cap
  function officer(c, x, y, h, o = {}) { person(c, x, y, h, { hat: 'cap', bulk: 1.05, ...o, col: o.col || INK }) }
  window.MW = { INK, RED, SEA, sea, puff, clouds, smokeCol, flame, burst, splash, carrier, destroyer, battleship, plane, planeTop, carrierTop, bomb, officer }
})()
