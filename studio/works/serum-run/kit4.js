// kit4.js: cut-paper pieces for the serum run film: sled dogs, sleds, parkas, spruce, cabins, snow, a map of Alaska.
(function () {
  const { clamp, lerp, rng, noise, mix } = K
  const { W, H, C, layer, person, glow, text, F } = L
  const INK = '#06070b', SN = { sky0: '#0a0f20', sky1: '#1b2747', sky2: '#3a4b76', snow0: '#b4bfd6', snow1: '#5b6889', far: '#141d38' }

  // ---------- sled dog, side on, facing +x. (x, y) = ground under the middle; s = px per unit (body about 80 units long) ----------
  // o: run (phase), stride 0..1 (0 = standing), sit, lie, head (rad, + down), tail 'curl'|'out', col, face
  function dleg(c, hx, hy, fx, fy, bend, w) {
    const mx = (hx + fx) / 2, my = (hy + fy) / 2, dx = fx - hx, dy = fy - hy, d = Math.hypot(dx, dy) || 1, kx = mx + (-dy / d) * bend, ky = my + (dx / d) * bend
    c.lineWidth = w; c.beginPath(); c.moveTo(hx, hy); c.lineTo(kx, ky); c.stroke(); c.lineWidth = w * 0.7; c.beginPath(); c.moveTo(kx, ky); c.lineTo(fx, fy); c.stroke()
    c.beginPath(); c.ellipse(fx + 2.5, fy - 1.6, 4.6, 2.6, 0, 0, 7); c.fill()
  }
  function dhead(c, x, y, rot) {
    c.save(); c.translate(x, y); c.rotate(rot)
    c.beginPath(); c.ellipse(0, 0, 9.2, 8.2, 0, 0, 7); c.fill()                                             // skull
    c.beginPath(); c.moveTo(2, -6.5); c.lineTo(18, -1.5); c.quadraticCurveTo(20.5, 1.5, 18, 4.2); c.lineTo(2, 7.5); c.closePath(); c.fill()     // muzzle
    c.beginPath(); c.moveTo(-8.5, -3); c.lineTo(-7.5, -16); c.lineTo(-0.5, -7.2); c.closePath(); c.fill()         // ears: small, upright, set back
    c.beginPath(); c.moveTo(-3.5, -6.5); c.lineTo(-0.5, -17); c.lineTo(4.5, -6.6); c.closePath(); c.fill()
    c.restore()
  }
  function dog(c, x, y, s, o = {}) {
    const col = o.col || INK, face = o.face || 1, ph = o.run || 0, st = o.stride ?? 0
    c.save(); c.translate(x, y); c.scale(s * face, s); c.fillStyle = col; c.strokeStyle = col; c.lineCap = 'round'; c.lineJoin = 'round'
    if (o.sit) {
      c.beginPath(); c.moveTo(-26, 0); c.bezierCurveTo(-34, -16, -24, -32, -4, -46); c.bezierCurveTo(4, -52, 16, -50, 18, -40); c.bezierCurveTo(19, -28, 12, -14, 2, 0); c.closePath(); c.fill()       // back, chest, haunch
      c.beginPath(); c.ellipse(-12, -11, 17, 12, 0.2, 0, 7); c.fill(); c.lineWidth = 6; c.beginPath(); c.moveTo(-14, -3); c.lineTo(6, -2.5); c.stroke()
      c.lineWidth = 6; c.beginPath(); c.moveTo(12, -38); c.lineTo(15, -3); c.stroke(); c.beginPath(); c.ellipse(18, -2, 5, 2.6, 0, 0, 7); c.fill()
      c.beginPath(); c.moveTo(-2, -46); c.lineTo(10, -62); c.lineTo(22, -52); c.lineTo(17, -38); c.closePath(); c.fill(); dhead(c, 17, -61, (o.head || 0) - 0.05)
      c.lineWidth = 7; c.beginPath(); c.moveTo(-26, -4); c.bezierCurveTo(-40, -4, -46, -12, -40, -20); c.stroke()
      c.restore(); return
    }
    if (o.lie) {
      c.beginPath(); c.moveTo(-36, 0); c.bezierCurveTo(-42, -16, -24, -24, 0, -24); c.bezierCurveTo(20, -24, 30, -16, 30, 0); c.closePath(); c.fill()
      c.lineWidth = 6.5; c.beginPath(); c.moveTo(22, -4); c.lineTo(46, -3); c.stroke(); c.beginPath(); c.moveTo(-24, -3); c.lineTo(-6, -2.5); c.stroke()
      c.beginPath(); c.moveTo(14, -22); c.lineTo(28, -34); c.lineTo(36, -22); c.lineTo(28, -8); c.closePath(); c.fill(); dhead(c, 32, -27 + (o.head ? 14 : 0), o.head ? 0.5 : 0.1)
      c.lineWidth = 7; c.beginPath(); c.moveTo(-36, -6); c.bezierCurveTo(-50, -6, -52, 0, -40, -1); c.stroke()
      c.restore(); return
    }
    const by = -44 - Math.sin(ph * 2) * 1.8 * st, ext = st                                   // back line; ext = how stretched out
    const foot = (off, base) => { const a = ph + off, sw = -Math.cos(a) * 21 * st, lift = Math.max(0, Math.sin(a)) * 12 * st; return [base + sw, -lift] }
    let f = foot(Math.PI * 0.9, 20); dleg(c, 19, by + 12, f[0], f[1], -2.5, 5.5); f = foot(Math.PI * 0.4, -25); dleg(c, -24, by + 10, f[0], f[1], 8, 6.5)
    // tail: a sickle over the back when standing, streaming when running
    c.lineWidth = 7.5
    if ((o.tail || (st > 0.3 ? 'out' : 'curl')) === 'curl') { c.beginPath(); c.moveTo(-30, by + 2); c.bezierCurveTo(-42, by - 6, -40, by - 20, -27, by - 20); c.stroke() }
    else { const tw = Math.sin(ph) * 2.5; c.beginPath(); c.moveTo(-30, by + 2); c.bezierCurveTo(-40, by - 2 + tw, -48, by + tw, -56, by + 6 + tw); c.stroke() }
    // body: deep chest, tucked belly
    c.beginPath(); c.moveTo(-32, by + 6); c.bezierCurveTo(-34, by - 5, -20, by - 4, -4, by - 3); c.bezierCurveTo(8, by - 3, 18, by - 6, 25, by - 2)
    c.bezierCurveTo(31, by + 3, 30, by + 16, 22, by + 19); c.bezierCurveTo(10, by + 21, -6, by + 12, -20, by + 13); c.bezierCurveTo(-30, by + 14, -32, by + 12, -32, by + 6); c.closePath(); c.fill()
    // short thick neck, head carried just above the back; lower and forward at a run
    const hx = 35 + ext * 5, hy = by - 13 + ext * 9
    c.beginPath(); c.moveTo(10, by - 4); c.lineTo(hx - 6, hy - 6.5); c.lineTo(hx + 3, hy + 7); c.lineTo(22, by + 14); c.closePath(); c.fill()
    dhead(c, hx, hy, (o.head || 0) + ext * 0.12)
    f = foot(0, 22); dleg(c, 21, by + 12, f[0], f[1], -2.5, 6.5); f = foot(Math.PI * 1.5, -22); dleg(c, -22, by + 10, f[0], f[1], 9, 7.5)
    c.restore()
  }
  // a hooded parka figure (x, y = feet)
  function parka(c, x, y, h, o = {}) {
    const col = o.col || INK, face = o.face || 1
    person(c, x, y, h, { hat: 'none', bulk: 1.28, ...o, col })
    const s = h / 100, st = o.stride ?? 0, bob = -Math.abs(Math.cos(o.walk || 0)) * 1.6 * st
    c.save(); c.translate(x, y); c.scale(s * face, s); c.translate(0, bob); c.rotate(o.lean || 0); c.fillStyle = col
    c.beginPath(); c.ellipse(0.5, -91, 10.5, 10.5, 0, 0, 7); c.fill(); c.beginPath(); c.moveTo(-10, -86); c.quadraticCurveTo(-13, -76, -9, -72); c.lineTo(9, -74); c.closePath(); c.fill()
    c.restore()
  }
  // a man on his knees, digging (x, y = ground under the knees), facing +x
  function kneel(c, x, y, s, o = {}) {
    const col = o.col || INK, face = o.face || 1, d = o.dig || 0
    c.save(); c.translate(x, y); c.scale(s * face, s); c.fillStyle = col; c.strokeStyle = col; c.lineCap = 'round'
    c.lineWidth = 12; c.beginPath(); c.moveTo(-34, -6); c.lineTo(0, -6); c.stroke(); c.beginPath(); c.moveTo(-2, -6); c.lineTo(-22, -34); c.stroke()
    c.beginPath(); c.ellipse(-37, -5, 8, 5, 0, 0, 7); c.fill()
    c.save(); c.translate(-20, -34); c.rotate(0.95 + d * 0.08); c.beginPath(); c.roundRect(-15, -52, 30, 56, 13); c.fill(); c.beginPath(); c.ellipse(0, -62, 11.5, 11.5, 0, 0, 7); c.fill()
    c.lineWidth = 8.5; c.beginPath(); c.moveTo(4, -40); c.lineTo(22 + d * 6, -30 - d * 8); c.lineTo(34 + d * 4, -56 + d * 10); c.stroke(); c.restore()
    c.restore()
  }
  // a basket sled facing +x; (x, y) = snow under the back of the runners. o: load (colour of the package or null), tip 0..1 (on its side)
  function sled(c, x, y, s, o = {}) {
    const col = o.col || INK
    c.save(); c.translate(x, y); c.scale(s * (o.face || 1), s); c.rotate(-(o.tip || 0) * 1.35); c.strokeStyle = col; c.fillStyle = col; c.lineCap = 'round'; c.lineJoin = 'round'
    c.lineWidth = 5; c.beginPath(); c.moveTo(-14, 0); c.lineTo(104, 0); c.quadraticCurveTo(122, -2, 126, -20); c.stroke()
    c.lineWidth = 4; c.beginPath(); c.moveTo(4, -22); c.lineTo(108, -22); c.lineTo(124, -18); c.stroke()
    for (const k of [6, 40, 74, 104]) { c.beginPath(); c.moveTo(k, 0); c.lineTo(k, -22); c.stroke() }
    c.lineWidth = 5; c.beginPath(); c.moveTo(6, -22); c.lineTo(-4, -58); c.lineTo(-12, -60); c.stroke(); c.lineWidth = 3; c.beginPath(); c.moveTo(-2, -52); c.lineTo(60, -22); c.stroke()
    if (o.load !== null) { c.fillStyle = col; c.beginPath(); c.roundRect(18, -42, 70, 21, 8); c.fill(); if (o.load) { c.fillStyle = o.load; c.beginPath(); c.roundRect(40, -50, 34, 14, 6); c.fill() } }
    c.restore()
  }
  // a whole team: sled, driver, gangline and n dogs. (x, y) = snow under the sled's back. o: n, run (phase), stride, driver (false to leave him off), load, lead {col}
  function team(c, x, y, s, o = {}) {
    const n = o.n ?? 7, ph = o.run || 0, st = o.stride ?? 1, col = o.col || INK, gap = 88
    const lx = x + (185 + (n - 1) * gap) * s
    c.save(); c.strokeStyle = col; c.lineWidth = 2.2 * s; c.beginPath(); c.moveTo(x + 124 * s, y - 20 * s); c.lineTo(lx - 20 * s, y - 36 * s); c.stroke(); c.restore()
    for (let k = 0; k < n - 1; k++) dog(c, x + (185 + k * gap) * s, y, s, { col, run: ph + k * 1.7, stride: st })
    dog(c, lx, y, s * (o.leadScale || 1), { col: o.leadCol || col, run: ph + 2.4, stride: st })
    sled(c, x, y, s, { col, load: o.load })
    if (o.driver !== false) parka(c, x - 12 * s, y, 104 * s, { col, arm: 0.42, walk: ph * (o.jog ? 1 : 0), stride: o.jog ? 1 : 0, lean: 0.06 })
    return lx
  }
  function spruce(c, x, y, s, col = INK, seed = 1) {
    const r = rng(seed * 29 + 1); c.save(); c.translate(x, y); c.scale(s, s); c.fillStyle = col
    c.fillRect(-4, -30, 8, 32); c.beginPath(); c.moveTo(0, -210 - r() * 30)
    const n = 7; for (let i = 1; i <= n; i++) { const yy = -200 + i * 26, w = 10 + i * 8 + r() * 8; c.lineTo(w, yy + 4); c.lineTo(w * 0.45, yy - 2) }
    for (let i = n; i >= 1; i--) { const yy = -200 + i * 26, w = 10 + i * 8 + r() * 8; c.lineTo(-w * 0.45, yy - 2); c.lineTo(-w, yy + 4) }
    c.closePath(); c.fill(); c.restore()
  }
  // a log roadhouse; (x, y) = ground centre. o: lit 0..1, smoke 0..1, t
  function cabin(c, x, y, s, o = {}) {
    const col = o.col || INK, lit = o.lit ?? 1
    c.save(); c.translate(x, y); c.scale(s, s)
    if (lit > 0) glow(c, -30, -46, 190, '246,199,112', 0.42 * lit)
    c.fillStyle = col; c.fillRect(-120, -88, 240, 90); c.beginPath(); c.moveTo(-138, -86); c.lineTo(0, -146); c.lineTo(138, -86); c.closePath(); c.fill(); c.fillRect(56, -150, 20, 40)
    c.fillStyle = o.snow || '#d5dcec'; c.beginPath(); c.moveTo(-138, -86); c.lineTo(0, -146); c.lineTo(138, -86); c.lineTo(122, -90); c.lineTo(0, -134); c.lineTo(-122, -90); c.closePath(); c.fill(); c.fillRect(54, -156, 24, 7)
    c.fillStyle = lit > 0 ? mix('#1a1410', '#f0c868', lit) : '#12141c'; c.fillRect(-62, -66, 44, 38); c.fillStyle = col; c.fillRect(-42, -66, 4, 38); c.fillRect(-62, -49, 44, 4)
    c.fillStyle = '#020203'; c.fillRect(38, -70, 40, 72)
    const sm = o.smoke ?? 1; if (sm > 0) for (let i = 0; i < 7; i++) { const a = (((o.t || 0) * 0.25 + i / 7) % 1); c.fillStyle = `rgba(190,198,216,${0.3 * (1 - a) * sm})`; c.beginPath(); c.arc(66 + a * 110 + Math.sin(a * 5 + i) * 10, -160 - a * 150, 10 + a * 34, 0, 7); c.fill() }
    c.restore()
  }
  // an open-cockpit biplane, facing +x
  function biplane(c, x, y, s, o = {}) {
    const col = o.col || INK
    c.save(); c.translate(x, y); c.scale(s, s); c.rotate(o.rot || 0); c.fillStyle = col; c.strokeStyle = col; c.lineCap = 'round'
    c.beginPath(); c.moveTo(70, -8); c.quadraticCurveTo(84, 0, 70, 10); c.lineTo(-20, 12); c.lineTo(-92, 2); c.lineTo(-92, -4); c.lineTo(-18, -12); c.closePath(); c.fill()
    c.beginPath(); c.moveTo(-74, -2); c.lineTo(-98, -34); c.lineTo(-84, -34); c.lineTo(-62, -4); c.closePath(); c.fill(); c.fillRect(-104, -4, 34, 5)
    if (o.wings !== false) { c.lineWidth = 7; c.beginPath(); c.moveTo(-4, -42); c.lineTo(62, -42); c.moveTo(-10, 14); c.lineTo(56, 14); c.stroke(); c.lineWidth = 2.5; for (const k of [4, 28, 50]) { c.beginPath(); c.moveTo(k, -42); c.lineTo(k - 4, 14); c.stroke() } }
    c.lineWidth = 4; c.beginPath(); c.moveTo(34, 12); c.lineTo(26, 34); c.moveTo(46, 12); c.lineTo(54, 34); c.stroke(); c.beginPath(); c.arc(40, 36, 11, 0, 7); c.fill()
    c.lineWidth = 5; c.beginPath(); c.moveTo(82, -30); c.lineTo(82, 30); c.stroke(); c.beginPath(); c.arc(8, -14, 7, Math.PI, 0); c.fill()
    c.restore()
  }
  // ---------- weather and ground ----------
  const stars = () => layer('stars2', W, H, (x) => { const r = rng(404); for (let i = 0; i < 420; i++) { const a = 0.25 + r() * 0.7; x.fillStyle = `rgba(232,236,245,${a})`; x.beginPath(); x.arc(r() * W, r() * H * 0.7, r() < 0.06 ? 2.4 : 1 + r() * 1.1, 0, 7); x.fill() } })
  // sky + far hills + snow. o: hy (snow line), stars 0..1, moon [x, y, r], dawn 0..1, hills
  function snowland(c, t, o = {}) {
    const hy = o.hy ?? 760, dw = o.dawn || 0
    const g = c.createLinearGradient(0, 0, 0, hy); g.addColorStop(0, mix(SN.sky0, '#5a6a8e', dw)); g.addColorStop(0.7, mix(SN.sky1, '#b9a9a0', dw)); g.addColorStop(1, mix(SN.sky2, '#f0cfa0', dw)); c.fillStyle = g; c.fillRect(-300, 0, W + 600, hy + 2); c.fillStyle = mix(SN.sky0, '#5a6a8e', dw); c.fillRect(-300, -400, W + 600, 401)
    if ((o.stars ?? 1) > 0 && dw < 0.9) { c.save(); c.globalAlpha = (o.stars ?? 1) * (1 - dw); c.drawImage(stars(), 0, 0); c.restore() }
    if (o.moon) { const [mx, my, mr] = o.moon; glow(c, mx, my, mr * 6, '200,210,240', 0.3); c.fillStyle = '#eef0f4'; c.beginPath(); c.arc(mx, my, mr, 0, 7); c.fill() }
    if (o.hills !== false) { const off = o.scroll || 0; c.fillStyle = mix(SN.far, '#6f7896', dw); c.beginPath(); c.moveTo(0, hy + 4); for (let x = 0; x <= W; x += 40) c.lineTo(x, hy - 40 - 60 * noise((x + off * 0.15) * 0.0019 + (o.seed || 0), 3) - 30 * noise((x + off * 0.15) * 0.007, 5)); c.lineTo(W, hy + 4); c.closePath(); c.fill() }
    const g2 = c.createLinearGradient(0, hy, 0, H); g2.addColorStop(0, mix(SN.snow0, '#f1ead9', dw)); g2.addColorStop(1, mix(SN.snow1, '#a7a9b8', dw)); c.fillStyle = g2; c.fillRect(-300, hy, W + 600, H - hy); c.fillStyle = mix(SN.snow1, '#a7a9b8', dw); c.fillRect(-300, H - 1, W + 600, 300)
  }
  // falling / driven snow in screen space. a = amount 0..1, wind = px/s sideways (negative blows left)
  function snowfall(c, t, a, wind = -200, seed = 3) {
    if (a <= 0) return; const r = rng(seed), n = Math.floor(520 * a); c.save(); c.strokeStyle = '#eef2fa'; c.lineCap = 'round'
    for (let i = 0; i < n; i++) {
      const z = 0.4 + r() * 0.9, vx = wind * z * (0.7 + r() * 0.6), vy = (90 + r() * 120) * z, x0 = r() * (W + 800) - 400, y0 = r() * (H + 200)
      const x = ((x0 + vx * t) % (W + 800) + (W + 800)) % (W + 800) - 400, y = (y0 + vy * t) % (H + 200) - 100, l = 0.035
      c.globalAlpha = 0.25 + 0.6 * r(); c.lineWidth = 1.4 + 2.6 * z * r(); c.beginPath(); c.moveTo(x, y); c.lineTo(x - vx * l, y - vy * l); c.stroke()
    }
    c.restore()
  }
  // ---------- Alaska ----------
  const AK = [[-130, 55], [-131.5, 55.3], [-133, 56.5], [-135, 58], [-137, 58.5], [-139.5, 59.8], [-141.5, 60], [-144, 60], [-146, 61], [-148, 60.8], [-149.6, 61.3], [-150.3, 61], [-151.6, 59.3], [-152.6, 60], [-153.5, 59.5], [-154, 58.5], [-156, 57.5], [-158, 56.5], [-160, 55.6], [-162.5, 54.9], [-164.8, 54.4], [-164, 55.4], [-161.5, 56.6], [-159.5, 57.9], [-157.4, 58.7], [-158.8, 58.6], [-160.5, 58.8], [-162, 59.2], [-162, 60], [-164.5, 60.3], [-165.3, 61.5], [-166, 62.2], [-164.8, 63], [-163, 63.2], [-161.1, 63.6], [-160.8, 63.9], [-161.1, 64.4], [-160.9, 64.8], [-162.4, 64.55], [-163, 64.6], [-164.2, 64.55], [-165.4, 64.5], [-166.6, 64.8], [-168, 65.6], [-166.5, 66.2], [-164, 66.6], [-163, 66.1], [-162, 66.9], [-163.5, 67.2], [-165, 68.2], [-166.2, 68.9], [-163.5, 69.5], [-162, 70.3], [-158, 70.9], [-156.5, 71.3], [-152, 70.8], [-148, 70.4], [-144, 70], [-141, 69.6], [-141, 60.3], [-139, 60.1], [-137, 59.1], [-135, 59.6], [-133.6, 58.5], [-131.6, 56.8], [-130, 56]]
  const PL = { nome: [-165.4, 64.5], nenana: [-149.1, 64.56], anchorage: [-149.9, 61.2], tanana: [-152.1, 65.17], ruby: [-155.5, 64.74], nulato: [-158.1, 64.72], kaltag: [-158.72, 64.33], unalakleet: [-160.8, 63.88], shaktoolik: [-161.15, 64.35], isaacs: [-161.9, 64.55], golovin: [-163.03, 64.54], bluff: [-163.75, 64.57], seattle: [-122.3, 47.6] }
  const ROUTE = ['nenana', 'tanana', 'ruby', 'nulato', 'kaltag', 'unalakleet', 'shaktoolik', 'isaacs', 'golovin', 'bluff', 'nome']
  // m = {cx (lon), cy (lat), k (px per degree of latitude), x, y (screen centre)}
  const proj = (m, [lon, lat]) => [m.x + (lon - m.cx) * m.k * 0.44, m.y - (lat - m.cy) * m.k]
  function alaska(c, m, o = {}) {
    c.save(); c.beginPath(); AK.forEach((p, i) => { const [x, y] = proj(m, p); i ? c.lineTo(x, y) : c.moveTo(x, y) }); c.closePath()
    c.fillStyle = o.fill || C.paper2; c.fill(); c.strokeStyle = o.line || C.ink; c.lineWidth = o.lw || 4; c.lineJoin = 'round'; c.stroke(); c.restore()
  }
  // point along the relay route, p = 0 (Nenana) .. 1 (Nome)
  const LEN = (() => { const d = [0]; for (let i = 1; i < ROUTE.length; i++) { const a = PL[ROUTE[i - 1]], b = PL[ROUTE[i]]; d.push(d[i - 1] + Math.hypot((b[0] - a[0]) * 0.44, b[1] - a[1])) } return d })()
  function onRoute(p) { const L2 = LEN[LEN.length - 1] * clamp(p); let i = 1; while (i < LEN.length - 1 && LEN[i] < L2) i++; const k = (L2 - LEN[i - 1]) / (LEN[i] - LEN[i - 1]), a = PL[ROUTE[i - 1]], b = PL[ROUTE[i]]; return [lerp(a[0], b[0], k), lerp(a[1], b[1], k)] }
  function route(c, m, p0, p1, col, lw = 6, dash) {
    c.save(); c.strokeStyle = col; c.lineWidth = lw; c.lineCap = 'round'; c.lineJoin = 'round'; if (dash) c.setLineDash(dash); c.beginPath()
    for (let p = p0; p <= p1 + 1e-6; p += 0.005) { const [x, y] = proj(m, onRoute(p)); p === p0 ? c.moveTo(x, y) : c.lineTo(x, y) } c.stroke(); c.restore()
  }
  window.SR = { INK, SN, dog, parka, kneel, sled, team, spruce, cabin, biplane, snowland, snowfall, alaska, proj, PL, onRoute, route }
})()
