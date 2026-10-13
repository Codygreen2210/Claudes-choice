// pov.js: first-person camera for Midway. Worlds seen from a seat (high above the clouds, low over the water,
// at the waterline, straight down a dive) and the frames we see them through (SBD and TBD cockpits, binoculars,
// the dive bomber's telescope sight, the bridge window, the rear canopy).
window.POV = (function () {
  const { W, H, clamp, lerp, prog, rng, ell, poly, shade, vgrad, hgrad, rgrad, text } = PK
  const F = 900                                   // focal length for the perspective worlds
  // look through a seat: roll (radians), pitch (px, + looks down), yaw (px, + looks right), zoom
  function view(c, v, fn) { c.save(); c.translate(W / 2, H / 2); c.rotate(v.roll || 0); c.scale(v.z || 1, v.z || 1); c.translate(-W / 2 - (v.yaw || 0), -H / 2 - (v.pitch || 0)); fn(c); c.restore() }
  const proj = (wx, wz, H0, alt, camX = 0) => [960 + (wx - camX) * F / wz, H0 + alt * F / wz, F / wz]

  // ---- high above: a deep sky, the sea far below with broken cloud between. o.speed, o.wake {x,z}, o.ships [{x,z,fire,top}]
  function high(c, t, o = {}) {
    const H0 = o.H0 ?? 470, alt = 300, calt = 140
    c.fillStyle = vgrad(c, H0 - 1400, H0, '#14365c', '#2e5f8e', '#a9c6dc'); c.fillRect(-1600, H0 - 2600, 5200, 2600)
    if (o.sun) { const [x, y] = o.sun; c.fillStyle = rgrad(c, x, y, 6, 520, 'rgba(255,240,210,0.95)', 'rgba(255,230,190,0.35)', 'rgba(255,230,190,0)'); c.fillRect(x - 520, y - 520, 1040, 1040) }
    c.fillStyle = vgrad(c, H0, H0 + 1300, '#8fa9bc', '#4a6d8c', '#23405e'); c.fillRect(-1600, H0, 5200, 2400)
    const r = rng(o.seed || 21), sp = o.speed ?? 260, Z0 = 900, Z1 = 14000
    const puffs = []
    for (let k = 0; k < 90; k++) { const wx = (r() - 0.5) * 16000, z0 = Z0 + r() * (Z1 - Z0), w = 0.6 + r() * 1.1; let z = z0 - t * sp; z = Z0 + (((z - Z0) % (Z1 - Z0)) + (Z1 - Z0)) % (Z1 - Z0); puffs.push([wx, z, w]) }
    // things on the sea
    const sea = []
    if (o.wake) sea.push(['wake', o.wake]); (o.ships || []).forEach(s => sea.push(['ship', s]))
    puffs.sort((a, b) => b[1] - a[1])
    // shadows first, then far things, then clouds near-to-far order reversed (far first)
    for (const [wx, z, w] of puffs) { const [x, y, s] = proj(wx, z, H0, alt); ell(c, x + 40 * s, y, 520 * s * w, 60 * s * w, 0, 'rgba(20,40,60,0.12)') }
    sea.forEach(([kind, s]) => { if (kind === 'wake') wakeAt(c, s, t, H0, alt); else shipAt(c, s, t, H0, alt) })
    for (const [wx, z, w] of puffs) {
      const [x, y, s] = proj(wx, z, H0, alt - calt), a = clamp((Z1 - z) / 3000) * clamp((z - Z0) / 200)
      c.globalAlpha = a; const R = 480 * s * w; ell(c, x, y + 10 * s * w, R * 1.05, R * 0.14, 0, 'rgba(150,165,182,0.45)'); for (let j = 0; j < 7; j++) { const bx = x + (j - 3) * R * 0.28, by = y - Math.abs(Math.sin(j * 1.7)) * R * 0.1, br = R * (0.2 + 0.1 * Math.abs(Math.sin(j * 2.3))); c.save(); c.translate(bx, by); c.scale(1, 0.42); c.fillStyle = rgrad(c, 0, 0, br * 0.15, br, 'rgba(255,255,255,0.97)', 'rgba(238,243,248,0.8)', 'rgba(238,243,248,0)'); c.fillRect(-br, -br, br * 2, br * 2); c.restore() } c.globalAlpha = 1
    }
    c.fillStyle = vgrad(c, H0 - 60, H0 + 60, 'rgba(210,225,235,0)', 'rgba(210,225,235,0.75)', 'rgba(210,225,235,0)'); c.fillRect(-1600, H0 - 60, 5200, 120)
  }
  function wakeAt(c, s, t, H0, alt) {
    for (let k = 0; k < 40; k++) { const z = s.z + k * 60, [x, y, sc] = proj(s.x - k * (s.dx || 0), z, H0, alt); ell(c, x, y, (10 + k * 1.6) * sc * 9, 3 * sc * 9, 0, `rgba(245,250,255,${0.85 - k * 0.02})`) }
    const [x, y, sc] = proj(s.x, s.z - 30, H0, alt); ell(c, x, y, 26 * sc * 9, 6 * sc * 9, 0, '#3a3c42'); ell(c, x, y - 2 * sc * 9, 10 * sc * 9, 4 * sc * 9, 0, '#5a5c62')
  }
  function shipAt(c, s, t, H0, alt) {
    const [x, y, sc] = proj(s.x, s.z, H0, alt); c.save(); c.translate(x, y); c.scale(sc * 0.9, sc * 0.9 * Math.min(1, alt / s.z * 3)); MWB.carrierTop(c, 0, 0, 1, t, { rot: s.rot || 0, planes: 6 })
    c.restore()
    if (s.fire) { c.save(); c.translate(x, y); c.scale(sc * 2.2, sc * 2.2); MWB.fire(c, 0, 0, 260, t, 0.5 * s.fire); c.restore() }
  }

  // ---- low over the water: the sea rushing under, the horizon close. o.inner(c, H0) draws ships and planes in screen space
  function low(c, t, o = {}) {
    const H0 = o.H0 ?? 450, alt = 34
    c.fillStyle = vgrad(c, H0 - 1200, H0, '#4a78a2', '#9cbcd4', '#e2e8ea'); c.fillRect(-1600, H0 - 2400, 5200, 2400)
    const r = rng(5)
    for (let k = 0; k < 8; k++) { const x = r() * 3600 - 800, y = H0 - 120 - r() * 380, w = 200 + r() * 260; for (let j = 0; j < 5; j++) ell(c, x + j * w * 0.25, y + Math.sin(j * 2) * 14, w * 0.25, w * 0.1, 0, 'rgba(255,250,244,0.5)') }
    c.fillStyle = vgrad(c, H0, H0 + 900, '#6a8aa4', '#33546e', '#162a3c'); c.fillRect(-1600, H0, 5200, 2400)
    c.fillStyle = vgrad(c, H0 - 30, H0 + 40, 'rgba(225,232,236,0)', 'rgba(225,232,236,0.8)', 'rgba(225,232,236,0)'); c.fillRect(-1600, H0 - 30, 5200, 70)
    const sp = o.speed ?? 90
    for (let k = 0; k < 260; k++) {
      const wx = (r() - 0.5) * 3000, z0 = 20 + r() * 2000; let z = z0 - t * sp; z = 20 + ((((z - 20) % 2000) + 2000) % 2000)
      const [x, y, s] = proj(wx, z, H0, alt); const L = Math.min(140, 40 * s), a = clamp(0.06 + s * 0.08, 0, 0.3); c.strokeStyle = `rgba(225,238,248,${a})`; c.lineWidth = Math.min(4, Math.max(1, s * 1.2)); c.beginPath(); c.moveTo(x - L, y); c.quadraticCurveTo(x, y - Math.min(8, 2 * s), x + L, y); c.stroke()
    }
    if (o.inner) o.inner(c, H0)
  }

  // ---- at the waterline: waves in the face, the fleet small on the horizon. o.H0 bobs; o.inner(c, H0) draws far things
  function waterline(c, t, o = {}) {
    const H0 = (o.H0 ?? 560) + Math.sin(t * 1.1) * 26 + Math.sin(t * 0.47) * 14
    c.fillStyle = vgrad(c, H0 - 1400, H0, '#3a6890', '#8eb2cc', '#dfe6e8'); c.fillRect(-1600, H0 - 2600, 5200, 2600)
    if (o.sky) o.sky(c, H0)
    c.fillStyle = vgrad(c, H0, H0 + 600, '#5a7a94', '#2a4a62', '#132638'); c.fillRect(-1600, H0, 5200, 2000)
    if (o.inner) o.inner(c, H0)
    // swells: rows of crests, the near ones tall and dark
    for (let row = 0; row < 7; row++) {
      const yb = H0 + 30 + row * row * 16, amp = 6 + row * row * 3.2, ph = t * (0.8 + row * 0.12) + row * 1.7, col = shade('#2a4a62', -0.05 * row)
      c.fillStyle = col; c.beginPath(); c.moveTo(-200, H + 200)
      for (let x = -200; x <= W + 200; x += 20) c.lineTo(x, yb - amp * (0.5 + 0.5 * Math.sin(x / (120 + row * 40) + ph)) - amp * 0.4 * Math.sin(x / 47 + ph * 1.3))
      c.lineTo(W + 200, H + 200); c.closePath(); c.fill()
      c.strokeStyle = `rgba(230,240,248,${0.18 + row * 0.03})`; c.lineWidth = 1 + row * 0.6; c.beginPath()
      for (let x = -200; x <= W + 200; x += 20) { const y = yb - amp * (0.5 + 0.5 * Math.sin(x / (120 + row * 40) + ph)) - amp * 0.4 * Math.sin(x / 47 + ph * 1.3); x === -200 ? c.moveTo(x, y) : c.lineTo(x, y) }
      c.stroke()
    }
    return H0
  }

  // ---- straight down a dive: the sea, a carrier's deck in the middle, clouds rushing outward. k 0..1 grows the deck
  function down(c, t, o = {}) {
    const k = o.k ?? 0
    c.fillStyle = rgrad(c, W / 2, H / 2, 100, 1300, '#3e6280', '#24405a'); c.fillRect(0, 0, W, H)
    const r = rng(o.seed || 4); c.strokeStyle = 'rgba(230,240,250,0.12)'; c.lineWidth = 2
    const z = o.z ?? lerp(0.6, 2.6, k * k)
    c.save(); c.translate(W / 2 + (o.dx || 0), H / 2 + (o.dy || 0)); c.rotate(o.rot || 0); c.scale(z, z)
    for (let n = 0; n < 220; n++) { const x = (r() - 0.5) * 4000, y = (r() - 0.5) * 3000; c.beginPath(); c.moveTo(x, y); c.lineTo(x + 18, y); c.stroke() }
    if (o.inner) o.inner(c)
    c.restore()
    // clouds streaming outward past the lens
    for (let n = 0; n < 14; n++) {
      const ang = r() * Math.PI * 2, ph = ((t * (o.rush ?? 0.5)) + r()) % 1, d = 80 + ph * ph * 1400, s = 0.3 + ph * 2.4
      const cx = W / 2 + Math.cos(ang) * d, cy = H / 2 + Math.sin(ang) * d * 0.7, br = 70 * s, al = 0.35 * Math.sin(Math.PI * ph) * (o.clouds ?? 1); c.fillStyle = rgrad(c, cx, cy, br * 0.1, br, `rgba(250,252,255,${al})`, 'rgba(250,252,255,0)'); c.fillRect(cx - br, cy - br, br * 2, br * 2)
    }
  }

  function below(c, t, o = {}) {
    c.fillStyle = vgrad(c, -200, H + 200, '#456a88', '#2c4c68'); c.fillRect(-1600, -1600, 5200, 4400)
    const r = rng(o.seed || 12); c.strokeStyle = 'rgba(230,240,250,0.10)'; c.lineWidth = 1.5
    for (let k = 0; k < 400; k++) { const x = r() * 4400 - 1200, y = r() * 3200 - 1000; c.beginPath(); c.moveTo(x, y); c.lineTo(x + 8, y); c.stroke() }
    if (o.inner) o.inner(c)
    const drift = (o.drift ?? 30) * t
    for (const [lay, n, sz, a] of [[0.6, 26, 0.6, 0.75], [1.0, 14, 1.2, 0.9]]) for (let k = 0; k < n; k++) {
      const x = ((r() * 4800 + drift * lay) % 4800) - 1400, y = r() * 2600 - 700, w = (120 + r() * 220) * sz
      ell(c, x + 90 * lay, y + 70 * lay, w, w * 0.6, 0.3, 'rgba(10,25,40,0.18)')
      for (let j = 0; j < 9; j++) { const bx = x + (j - 4) * w * 0.2 + Math.sin(j * 2.7) * w * 0.15, by = y + Math.sin(j * 1.9) * w * 0.22, br = w * (0.22 + 0.12 * Math.abs(Math.sin(j * 1.3))); c.fillStyle = rgrad(c, bx, by, br * 0.2, br, `rgba(252,253,255,${a})`, `rgba(240,245,250,${a * 0.7})`, 'rgba(240,245,250,0)'); c.fillRect(bx - br, by - br, br * 2, br * 2) }
      ell(c, x + w * 0.2, y + w * 0.25, w * 0.9, w * 0.2, 0, 'rgba(170,185,200,0.35)')
    }
  }
  // a destroyer seen from above with its long wake
  function wakeTop(c, x, y, s, ang, t) { c.save(); c.translate(x, y); c.rotate(ang); c.scale(s, s)
    for (let k = 0; k < 60; k++) { const sp = 6 + k * 1.6; ell(c, -20 - k * 22, -sp, 14, 5, 0.1, `rgba(245,250,255,${0.8 - k * 0.012})`); ell(c, -20 - k * 22, sp, 14, 5, -0.1, `rgba(245,250,255,${0.8 - k * 0.012})`); ell(c, -20 - k * 22, 0, 16, 3, 0, `rgba(245,250,255,${0.5 - k * 0.008})`) }
    c.fillStyle = '#4a4c52'; poly(c, [[44, 0], [24, -8], [-30, -7], [-34, 0], [-30, 7], [24, 8]]); c.fill(); c.fillStyle = '#6a6c72'; c.fillRect(-6, -4, 14, 8); c.restore() }
  // ===================== the frames we look through (screen space)
  const steel = '#2a3036', steel2 = '#3c444c'
  function gauge(c, x, y, r, val, o = {}) {
    ell(c, x, y, r + 6, r + 6, 0, '#121416'); ell(c, x, y, r, r, 0, '#1a1c1e')
    c.strokeStyle = 'rgba(230,226,210,0.8)'; c.lineWidth = 2
    for (let k = 0; k <= 10; k++) { const a = Math.PI * 0.75 + k / 10 * Math.PI * 1.5; c.beginPath(); c.moveTo(x + Math.cos(a) * r * 0.78, y + Math.sin(a) * r * 0.78); c.lineTo(x + Math.cos(a) * r * 0.92, y + Math.sin(a) * r * 0.92); c.stroke() }
    if (o.red) { c.strokeStyle = '#c8402e'; c.lineWidth = r * 0.12; c.beginPath(); c.arc(x, y, r * 0.84, Math.PI * 0.75, Math.PI * 0.75 + Math.PI * 1.5 * o.red); c.stroke() }
    if (o.label) text(c, o.label, x, y + r * 0.42, r * 0.26, 'rgba(230,226,210,0.85)', { weight: 700 })
    const a = Math.PI * 0.75 + clamp(val) * Math.PI * 1.5
    c.strokeStyle = '#f0e8c8'; c.lineWidth = Math.max(2, r * 0.07); c.lineCap = 'round'; c.beginPath(); c.moveTo(x, y); c.lineTo(x + Math.cos(a) * r * 0.8, y + Math.sin(a) * r * 0.8); c.stroke(); c.lineCap = 'butt'
    ell(c, x, y, r * 0.09, r * 0.09, 0, '#2a2a2a')
    ell(c, x - r * 0.3, y - r * 0.4, r * 0.5, r * 0.22, -0.4, 'rgba(255,255,255,0.07)')
  }
  // the SBD Dauntless: windscreen posts, the long telescope sight through the glass, the cowling, the panel
  function sbd(c, t, o = {}) {
    c.save(); c.setTransform(1, 0, 0, 1, 0, 0)
    const bob = Math.sin(t * 1.3) * 3, fuel = o.fuel ?? 0.3
    c.translate(0, bob)
    // propeller disc and cowling ahead
    c.fillStyle = vgrad(c, 700, 860, '#4a5866', '#2a343e'); c.beginPath(); c.moveTo(560, 900); c.quadraticCurveTo(960, 690, 1360, 900); c.closePath(); c.fill()
    c.fillStyle = 'rgba(255,255,255,0.08)'; c.beginPath(); c.moveTo(700, 860); c.quadraticCurveTo(960, 720, 1220, 860); c.quadraticCurveTo(960, 750, 700, 860); c.fill()
    c.save(); c.globalAlpha = 0.16; for (let k = 0; k < 3; k++) { const a = t * 47 + k * 2.1; c.strokeStyle = '#101010'; c.lineWidth = 50; c.beginPath(); c.moveTo(960, 760); c.lineTo(960 + Math.cos(a) * 520, 760 + Math.sin(a) * 520); c.stroke() } c.restore()
    c.fillStyle = 'rgba(30,30,30,0.08)'; ell(c, 960, 760, 540, 540, 0); c.fill()
    // the telescope sight: a tube from the panel up through the windscreen
    c.fillStyle = hgrad(c, 930, 990, '#1a1e22', '#4a525a', '#1a1e22'); c.fillRect(934, 470, 52, 420); ell(c, 960, 470, 30, 12, 0, '#0e1012'); ell(c, 960, 470, 18, 7, 0, 'rgba(140,180,200,0.6)')
    c.fillStyle = '#20262c'; c.fillRect(920, 610, 80, 26); c.fillRect(920, 760, 80, 26)
    // windscreen frame: centre panel edges, side posts, the top bow
    c.fillStyle = vgrad(c, 0, H, steel2, steel); poly(c, [[-40, 1100], [260, 1100], [520, 120], [470, 90]]); c.fill(); poly(c, [[1960, 1100], [1660, 1100], [1400, 120], [1450, 90]]); c.fill()
    c.fillStyle = steel; c.beginPath(); c.moveTo(-100, -100); c.lineTo(2020, -100); c.lineTo(2020, 60); c.quadraticCurveTo(960, 170, -100, 60); c.closePath(); c.fill()
    c.strokeStyle = 'rgba(20,24,28,0.9)'; c.lineWidth = 10; c.beginPath(); c.moveTo(700, 840); c.lineTo(760, 150); c.moveTo(1220, 840); c.lineTo(1160, 150); c.stroke()
    c.strokeStyle = 'rgba(255,255,255,0.10)'; c.lineWidth = 3; c.beginPath(); c.moveTo(520, 130); c.lineTo(270, 1080); c.moveTo(1400, 130); c.lineTo(1650, 1080); c.stroke()
    // glare on the glass
    c.fillStyle = 'rgba(255,255,255,0.05)'; poly(c, [[780, 160], [900, 160], [760, 820], [700, 820]]); c.fill()
    // the instrument panel
    c.fillStyle = vgrad(c, 860, 1080, '#2e3238', '#16181c'); c.beginPath(); c.moveTo(-60, 1140); c.lineTo(-60, 930); c.quadraticCurveTo(960, 820, 1980, 930); c.lineTo(1980, 1140); c.closePath(); c.fill()
    c.fillStyle = 'rgba(255,255,255,0.06)'; c.beginPath(); c.moveTo(-60, 930); c.quadraticCurveTo(960, 820, 1980, 930); c.lineTo(1980, 940); c.quadraticCurveTo(960, 832, -60, 940); c.fill()
    gauge(c, 560, 990, 58, 0.62 + Math.sin(t * 0.7) * 0.01, { label: 'ALT' }); gauge(c, 740, 960, 50, 0.45, { label: 'SPEED' }); gauge(c, 1180, 960, 50, 0.5 + Math.sin(t * 2) * 0.01, { label: 'RPM' })
    gauge(c, 1370, 995, 60, fuel + Math.sin(t * 3) * 0.008, { label: 'FUEL', red: 0.22 })
    c.restore()
  }
  // the TBD Devastator: a long greenhouse canopy, many frames, a low panel
  function tbd(c, t, o = {}) {
    c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.translate(0, Math.sin(t * 2.3) * 4)
    c.fillStyle = vgrad(c, 740, 900, '#56645a', '#303a32'); c.beginPath(); c.moveTo(600, 920); c.quadraticCurveTo(960, 760, 1320, 920); c.closePath(); c.fill()
    c.save(); c.globalAlpha = 0.14; for (let k = 0; k < 3; k++) { const a = t * 47 + k * 2.1; c.strokeStyle = '#101010'; c.lineWidth = 46; c.beginPath(); c.moveTo(960, 800); c.lineTo(960 + Math.cos(a) * 480, 800 + Math.sin(a) * 480); c.stroke() } c.restore()
    const fr = '#3a4640'
    c.fillStyle = fr; poly(c, [[-40, 1100], [220, 1100], [480, 80], [430, 60]]); c.fill(); poly(c, [[1960, 1100], [1700, 1100], [1440, 80], [1490, 60]]); c.fill()
    c.beginPath(); c.moveTo(-100, -100); c.lineTo(2020, -100); c.lineTo(2020, 40); c.quadraticCurveTo(960, 150, -100, 40); c.closePath(); c.fill()
    c.strokeStyle = fr; c.lineWidth = 12; c.beginPath(); c.moveTo(330, 260); c.quadraticCurveTo(960, 200, 1590, 260); c.stroke()
    c.fillStyle = vgrad(c, 880, 1080, '#3a4440', '#1a1e1c'); c.beginPath(); c.moveTo(-60, 1140); c.lineTo(-60, 960); c.quadraticCurveTo(960, 870, 1980, 960); c.lineTo(1980, 1140); c.closePath(); c.fill()
    gauge(c, 620, 1010, 52, 0.25, { label: 'ALT' }); gauge(c, 800, 990, 46, 0.7 + Math.sin(t * 5) * 0.03, { label: 'SPEED' }); gauge(c, 1300, 1000, 52, 0.55, { label: 'RPM' })
    if (o.cracks) { c.strokeStyle = `rgba(255,255,255,${0.5 * o.cracks})`; c.lineWidth = 2; const r = rng(9); for (const [cx, cy] of [[1230, 300], [640, 640]]) for (let k = 0; k < 9; k++) { const a = r() * 6.28, d = 60 + r() * 160; c.beginPath(); c.moveTo(cx, cy); c.lineTo(cx + Math.cos(a) * d * o.cracks, cy + Math.sin(a) * d * o.cracks); c.stroke() } }
    c.restore()
  }
  // binoculars: two round fields, black around them, a soft edge
  let bm = null
  function binoc(c, t, o = {}) {
    const jx = Math.sin(t * 7.1) * 3 + Math.sin(t * 2.3) * 5, jy = Math.cos(t * 5.3) * 3, R = 440, cx = 960 + jx, cy = 540 + jy, d = 300
    if (!bm) { bm = document.createElement('canvas'); bm.width = W + 200; bm.height = H + 200; const m = bm.getContext('2d'); m.fillStyle = '#050505'; m.fillRect(0, 0, bm.width, bm.height); m.globalCompositeOperation = 'destination-out'
      for (const x of [W / 2 + 100 - d, W / 2 + 100 + d]) { m.fillStyle = rgrad(m, x, H / 2 + 100, R * 0.8, R, 'rgba(0,0,0,1)', 'rgba(0,0,0,0)'); m.beginPath(); m.arc(x, H / 2 + 100, R, 0, Math.PI * 2); m.fill() } }
    c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.drawImage(bm, cx - W / 2 - 100, cy - H / 2 - 100); c.restore()
  }
  // the dive bomber's telescope sight: a small round field, a ring and crosshair, the cockpit blurred dark around it
  function scope(c, t, o = {}) {
    c.save(); c.setTransform(1, 0, 0, 1, 0, 0)
    const R = o.R ?? 420, cx = 960, cy = 540, a = o.a ?? 1
    c.globalAlpha = a
    c.fillStyle = 'rgba(8,10,12,0.96)'; c.beginPath(); c.rect(-10, -10, W + 20, H + 20); c.arc(cx, cy, R, 0, Math.PI * 2); c.fill('evenodd')
    c.fillStyle = rgrad(c, cx, cy, R * 0.75, R, 'rgba(8,10,12,0)', 'rgba(8,10,12,0.85)'); c.beginPath(); c.arc(cx, cy, R + 1, 0, Math.PI * 2); c.fill()
    c.strokeStyle = 'rgba(20,20,20,0.8)'; c.lineWidth = 3; c.beginPath(); c.moveTo(cx - R, cy); c.lineTo(cx - 40, cy); c.moveTo(cx + 40, cy); c.lineTo(cx + R, cy); c.moveTo(cx, cy - R); c.lineTo(cx, cy - 40); c.moveTo(cx, cy + 40); c.lineTo(cx, cy + R); c.stroke()
    c.beginPath(); c.arc(cx, cy, R * 0.45, 0, Math.PI * 2); c.stroke(); ell(c, cx, cy, 5, 5, 0, 'rgba(200,40,30,0.9)')
    c.restore()
  }
  // the bridge window: heavy steel frame, glass, a sill
  function bridgeWin(c, t) {
    c.save(); c.setTransform(1, 0, 0, 1, 0, 0)
    c.fillStyle = vgrad(c, 0, 160, '#22262a', '#30353a'); c.fillRect(0, 0, W, 140)
    c.fillStyle = vgrad(c, 880, 1080, '#3a3f44', '#1a1d20'); c.fillRect(0, 880, W, 200); c.fillStyle = 'rgba(255,255,255,0.08)'; c.fillRect(0, 880, W, 6)
    for (const x of [0, 620, 1300, 1920]) { c.fillStyle = hgrad(c, x - 50, x + 50, '#1a1d20', '#3a3f44', '#1a1d20'); c.fillRect(x - 46, 0, 92, 900) }
    c.fillStyle = 'rgba(255,255,255,0.04)'; poly(c, [[200, 140], [380, 140], [160, 880], [40, 880]]); c.fill(); poly(c, [[900, 140], [1000, 140], [880, 880], [800, 880]]); c.fill()
    c.restore()
  }
  // looking back over the tail: the rear canopy, the gunner's twin guns, the fin
  function rear(c, t) {
    c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.translate(0, Math.sin(t * 1.7) * 4)
    c.fillStyle = vgrad(c, 760, 1080, '#4a5866', '#262e36'); c.beginPath(); c.moveTo(500, 1100); c.lineTo(860, 800); c.lineTo(1060, 800); c.lineTo(1420, 1100); c.closePath(); c.fill()
        c.strokeStyle = '#16181a'; c.lineCap = 'round'; c.lineWidth = 16; c.beginPath(); c.moveTo(1240, 1100); c.lineTo(1520, 720); c.moveTo(1300, 1100); c.lineTo(1580, 730); c.stroke(); c.lineCap = 'butt'; c.strokeStyle = 'rgba(255,255,255,0.12)'; c.lineWidth = 3; c.beginPath(); c.moveTo(1246, 1090); c.lineTo(1516, 726); c.stroke(); ell(c, 1250, 1060, 110, 70, -0.6, '#24282c')
    c.fillStyle = steel; poly(c, [[-40, 1100], [180, 1100], [420, 0], [360, -20]]); c.fill(); poly(c, [[1960, 1100], [1740, 1100], [1500, 0], [1560, -20]]); c.fill()
    c.beginPath(); c.moveTo(-100, -100); c.lineTo(2020, -100); c.lineTo(2020, 30); c.quadraticCurveTo(960, 130, -100, 30); c.closePath(); c.fill()
    c.restore()
  }
  // G-force grey-out at the edges when pulling out
  function gforce(c, k) { if (k <= 0) return; c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.fillStyle = rgrad(c, W / 2, H / 2, H * (0.7 - 0.45 * k), H * 1.1, 'rgba(10,10,12,0)', `rgba(10,10,12,${0.95 * k})`); c.fillRect(0, 0, W, H); c.restore() }
  // tracer streaks coming at the lens from a point
  function tracers(c, t, x0, y0, n = 8, seed = 3) { const r = rng(seed); for (let k = 0; k < n; k++) { const ph = (t * (1.2 + r()) + r()) % 1, ang = (r() - 0.5) * 1.6 + Math.PI / 2 * (r() < 0.5 ? 1 : -1) * 0.2, d = ph * ph * 1400, ex = x0 + Math.cos(ang) * d * (r() < 0.5 ? -1 : 1), ey = y0 + Math.sin(ang) * d * 0.5 + d * 0.2; c.strokeStyle = `rgba(255,${200 + r() * 40},120,${0.9 * (1 - ph * 0.5)})`; c.lineWidth = 2 + ph * 6; c.beginPath(); c.moveTo(lerp(x0, ex, 0.7), lerp(y0, ey, 0.7)); c.lineTo(ex, ey); c.stroke() } }
  return { view, proj, high, below, wakeTop, low, waterline, down, sbd, tbd, binoc, scope, bridgeWin, rear, gforce, tracers, gauge }
})()
