// kit7.js: cut-paper pieces for the Champawat Tiger film, on top of lib.js, kit2.js and kit3.js.
// Paper and ink. The tigress is the one gold (with ink stripes); the one red is the count, and the broken teeth.
(function () {
  const { clamp, lerp, rng, noise, mix, prog } = K
  const { W, H, C, person, glow, text, F, hatch, layer } = L
  const { lion, lionDown, eyes } = T2
  const INK = C.ink, RED = '#a8321f', GOLD = '#c98a2e', GY = 860

  // ---------- the tigress: the lion figure in gold, with ink stripes laid over only where she is ----------
  const off = document.createElement('canvas'); off.width = 900; off.height = 600; const ox = off.getContext('2d')
  function tiger(c, x, y, s, o = {}) {
    const k = 3.2                                                       // drawn at a fixed size, then scaled into place
    ox.setTransform(1, 0, 0, 1, 0, 0); ox.clearRect(0, 0, 900, 600); ox.globalCompositeOperation = 'source-over'
    const draw = o.down ? lionDown : lion
    draw(ox, 450, 470, k, { ...o, face: 1, col: o.col || GOLD, eye: o.eye })
    ox.globalCompositeOperation = 'source-atop'; ox.strokeStyle = o.stripe || '#1a120a'; ox.lineCap = 'round'
    const r = rng(o.seed || 7)
    for (let i = 0; i < 30; i++) { const sx = 140 + i * 20 + r() * 8, w = 5 + r() * 7; ox.lineWidth = w; ox.beginPath(); ox.moveTo(sx + 10, 170); ox.quadraticCurveTo(sx - 10 + r() * 20, 280, sx + (r() - 0.5) * 24, 330 + r() * 70); ox.stroke() }
    ox.globalCompositeOperation = 'source-over'
    if (o.eye) { ox.fillStyle = T2.N.eye }
    c.save(); c.translate(x, y); c.scale((s / k) * (o.face || 1), s / k); c.drawImage(off, -450, -470); c.restore()
  }

  // ---------- the hills ----------
  // ridges: bands of hills, far to near, the far ones paler. d: 0 night .. 1 day
  function ridges(c, t, o = {}) {
    const d = o.d ?? 1, cols = [mix('#1a1d26', '#c9bc9c', d), mix('#14171e', '#a9997a', d), mix('#0e1015', '#857457', d), mix('#08090c', '#5f523d', d)]
    const sky = c.createLinearGradient(0, 0, 0, H); sky.addColorStop(0, mix('#0b0e16', '#e9dcc0', d)); sky.addColorStop(1, mix('#1d2433', '#f3e6c8', d)); c.fillStyle = sky; c.fillRect(0, 0, W, H)
    if (o.snow) { c.fillStyle = mix('#3b4255', '#f6efe0', d); c.beginPath(); c.moveTo(0, 360); for (let x = 0; x <= W; x += 80) c.lineTo(x, 200 + Math.abs(Math.sin(x * 0.006 + 1)) * 140); c.lineTo(W, 360); c.closePath(); c.fill() }
    cols.forEach((col, k) => { const base = 360 + k * 120, amp = 90 + k * 30; c.fillStyle = col; c.beginPath(); c.moveTo(-10, H); c.lineTo(-10, base); for (let x = -10; x <= W + 10; x += 40) c.lineTo(x, base - amp * (0.5 + 0.5 * noise(x * 0.003 + k * 4 + (o.seed || 0), k + 2))); c.lineTo(W + 10, H); c.closePath(); c.fill() })
  }
  // terraced fields on a slope: thin stepped lines
  function terraces(c, x, y, w, h, col = 'rgba(30,24,16,0.35)') { c.save(); c.strokeStyle = col; c.lineWidth = 3; for (let k = 0; k < 8; k++) { const yy = y + k * h / 8; c.beginPath(); c.moveTo(x + k * 12, yy); c.quadraticCurveTo(x + w / 2, yy - 18, x + w - k * 12, yy); c.stroke() } c.restore() }
  // a hill house: stone walls, a slate roof
  function house(c, x, y, s, o = {}) {
    c.save(); c.translate(x, y); c.scale(s, s); c.fillStyle = o.col || INK
    c.fillRect(-60, -70, 120, 70); c.beginPath(); c.moveTo(-74, -66); c.lineTo(0, -120); c.lineTo(74, -66); c.closePath(); c.fill()
    c.fillStyle = o.lit ? `rgba(246,199,112,${o.lit})` : (o.door || '#3a2c20'); c.fillRect(-14, -46, 28, 46); c.fillRect(26, -50, 16, 16)
    c.restore()
  }
  // a deodar: a tall dark cone of layered boughs
  function deodar(c, x, y, s, col = INK, seed = 1) {
    const r = rng(seed); c.save(); c.translate(x, y); c.scale(s, s); c.fillStyle = col; c.fillRect(-5, -40, 10, 40)
    for (let k = 0; k < 7; k++) { const yy = -40 - k * 34, w = 80 - k * 10 + r() * 10; c.beginPath(); c.moveTo(-w, yy); c.quadraticCurveTo(0, yy - 30, w, yy); c.lineTo(w * 0.6, yy - 10); c.quadraticCurveTo(0, yy - 60, -w * 0.6, yy - 10); c.closePath(); c.fill() }
    c.restore()
  }
  function forest(c, x0, x1, y, s, o = {}) { const r = rng(o.seed || 3); for (let x = x0; x < x1; x += 70 * s) deodar(c, x + r() * 40 * s, y + r() * 20 * s, s * (0.8 + r() * 0.5), o.col || INK, Math.floor(r() * 99)) }

  // ---------- people of the hills ----------
  // a villager: wrapped head, a shawl. lady: a woman with a load of grass or wood on her head (load 0..1)
  function villager(c, x, y, h, o = {}) {
    const face = o.face || 1, col = o.col || INK, s = h / 100
    if (o.lady) {
      c.save(); c.translate(x, y); c.scale(s * face, s); c.fillStyle = col
      c.beginPath(); c.moveTo(-9, -80); c.quadraticCurveTo(-13, -60, -7, -56); c.quadraticCurveTo(-20, -20, -19, 0); c.lineTo(19, 0); c.quadraticCurveTo(18, -24, 7, -56); c.quadraticCurveTo(13, -62, 9, -80); c.closePath(); c.fill()
      c.beginPath(); c.arc(1, -88, 7, 0, 7); c.fill()
      c.beginPath(); c.moveTo(-8, -92); c.quadraticCurveTo(1, -102, 10, -92); c.quadraticCurveTo(14, -76, 12, -60); c.lineTo(-14, -58); c.quadraticCurveTo(-16, -80, -8, -92); c.closePath(); c.fill()
      if (o.load) { c.beginPath(); c.ellipse(1, -104, 26 * o.load, 8 * o.load, 0, 0, 7); c.fill(); c.lineWidth = 2.4; c.strokeStyle = col; for (let k = -3; k <= 3; k++) { c.beginPath(); c.moveTo(1 + k * 6, -104); c.lineTo(1 + k * 8, -104 - 16 * o.load); c.stroke() } }
      c.restore(); return
    }
    person(c, x, y, h, { hat: 'none', face, col, walk: o.walk, stride: o.stride, arm: o.arm, hold: o.hold, lean: o.lean, bulk: o.bulk })
    c.save(); c.translate(x, y); c.scale(s * face, s); const bob = -Math.abs(Math.cos(o.walk || 0)) * 1.6 * (o.stride ?? 0); c.translate(0, bob); c.fillStyle = col
    c.beginPath(); c.ellipse(1, -96, 9.5, 6.5, 0, Math.PI, 0); c.fill(); c.beginPath(); c.ellipse(1, -97, 8, 4, 0.2, 0, 7); c.fill()
    c.restore()
  }
  // a man with a drum hung at his waist, beating it
  function drummer(c, x, y, h, t, o = {}) {
    const hit = Math.abs(Math.sin(t * 6 + (o.ph || 0)))
    villager(c, x, y, h, { ...o, arm: 0.35 + hit * 0.3 })
    const s = h / 100; c.save(); c.translate(x, y); c.scale(s * (o.face || 1), s); c.fillStyle = o.col || INK; c.beginPath(); c.ellipse(14, -48, 11, 13, 0, 0, 7); c.fill(); c.restore()
  }
  // Jim Corbett: a soft felt hat, a rifle. aim 0..1
  function corbett(c, x, y, h, o = {}) {
    const face = o.face || 1, col = o.col || INK, aim = o.aim || 0, s = h / 100
    const arm = lerp(o.arm ?? 0.18, 0.58, aim)
    const hold = (q) => { q.save(); q.translate(0, 30); q.rotate(arm * 2.5 + lerp(-1.3, -0.02, aim) + (o.kick || 0)); q.fillStyle = col; q.fillRect(-26, -2, 66, 4); q.fillRect(-36, -3.5, 16, 8); q.fillRect(40, -1, 14, 2); q.restore() }
    person(c, x, y, h, { hat: 'none', face, col, walk: o.walk, stride: o.stride, arm, hold, lean: o.lean || aim * 0.05, bulk: 1.0 })
    c.save(); c.translate(x, y); c.scale(s * face, s); const bob = -Math.abs(Math.cos(o.walk || 0)) * 1.6 * (o.stride ?? 0); c.translate(0, bob); c.rotate(o.lean || aim * 0.05); c.fillStyle = col
    c.beginPath(); c.ellipse(1.5, -96, 8, 6, 0, Math.PI, 0); c.fill(); c.beginPath(); c.roundRect(-11, -97.5, 26, 2.8, 1.4); c.fill()
    c.restore()
  }
  // a Nepalese soldier of the time: a round cap, a rifle on the shoulder
  function sepoy(c, x, y, h, o = {}) { B.soldier(c, x, y, h, { kind: 'sailor', col: o.col || INK, face: o.face || 1, pose: 'march', walk: o.walk, stride: o.stride }) }

  // ---------- the gorge ----------
  // the Champa gorge in section: steep walls left and right, a stony floor, brush. o: d (light)
  function gorge(c, t, o = {}) {
    const d = o.d ?? 1
    c.fillStyle = mix('#1d2433', '#efe2c4', d); c.fillRect(0, 0, W, H)
    c.fillStyle = mix('#0e1015', '#8a7759', d); c.beginPath(); c.moveTo(0, 0); c.lineTo(620, 0); c.bezierCurveTo(560, 300, 700, 600, 620, 900); c.lineTo(0, 1080); c.closePath(); c.fill()
    c.beginPath(); c.moveTo(W, 0); c.lineTo(1300, 0); c.bezierCurveTo(1380, 300, 1240, 600, 1320, 900); c.lineTo(W, 1080); c.closePath(); c.fill()
    hatch(c, k => { k.rect(0, 0, 700, H); k.rect(1240, 0, 680, H) }, { gap: 11, alpha: 0.2, angle: 1.2 })
    c.fillStyle = mix('#13110f', '#b19a74', d); c.fillRect(0, 900, W, 180)
    const r = rng(12); c.fillStyle = mix('#08090c', '#5f523d', d); for (let k = 0; k < 30; k++) { c.beginPath(); c.ellipse(r() * W, 910 + r() * 160, 12 + r() * 30, 6 + r() * 10, 0, 0, 7); c.fill() }
  }
  // brush: a band of spiky scrub
  function brush(c, x0, x1, y, h, col = INK, seed = 2) { T2.thorn(c, x0, x1, y, h, col, seed) }

  // ---------- the skull and the teeth ----------
  function skull(c, x, y, s, o = {}) {
    c.save(); c.translate(x, y); c.scale(s, s); c.fillStyle = o.col || '#e9dfc8'; c.strokeStyle = INK; c.lineWidth = 4
    c.beginPath(); c.moveTo(-220, -40); c.bezierCurveTo(-200, -170, 40, -190, 160, -90); c.lineTo(240, -60); c.lineTo(250, 0); c.lineTo(-60, 20); c.bezierCurveTo(-160, 30, -230, 20, -220, -40); c.closePath(); c.fill(); c.stroke()
    c.fillStyle = INK; c.beginPath(); c.ellipse(60, -80, 46, 34, 0.2, 0, 7); c.fill(); c.beginPath(); c.ellipse(-90, -30, 60, 40, 0, 0, 7); c.globalAlpha = 0.5; c.fill(); c.globalAlpha = 1
    // the jaw
    const jo = o.jaw || 0.15; c.save(); c.translate(-60, 20); c.rotate(jo); c.fillStyle = o.col || '#e9dfc8'; c.beginPath(); c.moveTo(-150, 0); c.lineTo(310, 0); c.lineTo(300, 50); c.bezierCurveTo(100, 80, -100, 80, -150, 40); c.closePath(); c.fill(); c.stroke()
    // lower canine: broken to the gum
    c.fillStyle = o.hl ? RED : '#e9dfc8'; c.beginPath(); c.moveTo(250, 0); c.lineTo(262, -14); c.lineTo(276, -12); c.lineTo(282, 0); c.closePath(); c.fill(); c.stroke(); c.restore()
    // upper canine: snapped in half
    c.fillStyle = o.hl ? RED : '#e9dfc8'; c.beginPath(); c.moveTo(196, 0); c.lineTo(204, 40); c.lineTo(214, 34); c.lineTo(222, 44); c.lineTo(230, 0); c.closePath(); c.fill(); c.stroke()
    // a whole canine behind it, the way it should look
    if (o.ghost) { c.globalAlpha = 0.25; c.fillStyle = '#e9dfc8'; c.beginPath(); c.moveTo(196, 0); c.quadraticCurveTo(206, 60, 214, 96); c.quadraticCurveTo(226, 60, 230, 0); c.closePath(); c.fill(); c.stroke(); c.globalAlpha = 1 }
    c.restore()
  }
  // a stone marker by a road
  function marker(c, x, y, s) { c.save(); c.translate(x, y); c.scale(s, s); c.fillStyle = '#cfc4a8'; c.fillRect(-90, -150, 180, 150); c.beginPath(); c.arc(0, -150, 90, Math.PI, 0); c.fill(); c.strokeStyle = INK; c.lineWidth = 3; c.strokeRect(-90, -150, 180, 150); for (let k = 0; k < 5; k++) c.fillRect(-60, -170 + k * 26, 120, 4); c.restore() }
  // a plate camera on a tripod
  function camera(c, x, y, s) { c.save(); c.translate(x, y); c.scale(s, s); c.strokeStyle = INK; c.lineWidth = 5; for (const dx of [-40, 0, 40]) { c.beginPath(); c.moveTo(0, -120); c.lineTo(dx, 0); c.stroke() } c.fillStyle = INK; c.fillRect(-36, -170, 60, 50); c.fillRect(24, -160, 30, 30); c.restore() }

  window.CW = { INK, RED, GOLD, GY, tiger, ridges, terraces, house, deodar, forest, villager, drummer, corbett, sepoy, gorge, brush, skull, marker, camera }
})()
