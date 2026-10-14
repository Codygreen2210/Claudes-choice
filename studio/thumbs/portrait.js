// portrait.js: big painted Style B close-ups for thumbnails (head and shoulders, three-quarter view).
// The films stay first-person POV; this character exists only on the thumbnail.
// portrait(c, cx, cy, R, o): R = head radius in px. o = {
//   skin, hair, mood: 'fierce'|'shock'|'grin'|'dread', look: [-1..1, -1..1] eye direction,
//   hat: null|'pilot'|'fedora'|'navy'|'turban', hatCol, goggles: bool, coat, collar, tie,
//   moustache, beard, rim: '#ff9a40' (light from the action side), rimSide: 1 right / -1 left }
(function () {
  const TAU = Math.PI * 2
  function hex(h) { h = h.replace('#', ''); return [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16)) }
  function mix(a, b, t) { const A = hex(a), B = hex(b); return '#' + A.map((v, i) => Math.round(v + (B[i] - v) * t).toString(16).padStart(2, '0')).join('') }
  const lit = (c, t) => mix(c, '#ffffff', t), drk = (c, t) => mix(c, '#000000', t)
  function rg(c, x, y, r0, r1, stops) { const g = c.createRadialGradient(x, y, r0, x, y, r1); stops.forEach((s, i) => g.addColorStop(i / (stops.length - 1), s)); return g }
  function lg(c, x0, y0, x1, y1, stops) { const g = c.createLinearGradient(x0, y0, x1, y1); stops.forEach((s, i) => g.addColorStop(i / (stops.length - 1), s)); return g }
  function E(c, x, y, rx, ry, rot, fill) { c.beginPath(); c.ellipse(x, y, Math.abs(rx), Math.abs(ry), rot || 0, 0, TAU); if (fill) { c.fillStyle = fill; c.fill() } }

  function shoulders(c, R, o) {
    const coat = o.coat || '#5a3f28'
    c.fillStyle = lg(c, -R * 2, 0, R * 2, 0, [drk(coat, 0.35), coat, lit(coat, 0.12), drk(coat, 0.3)])
    c.beginPath(); c.moveTo(-R * 2.6, R * 3.2); c.quadraticCurveTo(-R * 2.3, R * 1.45, -R * 0.55, R * 1.2)
    c.lineTo(R * 0.6, R * 1.2); c.quadraticCurveTo(R * 2.4, R * 1.4, R * 2.7, R * 3.2); c.closePath(); c.fill()
    // neck
    c.fillStyle = lg(c, 0, R * 0.6, 0, R * 1.4, [drk(o.skin, 0.35), drk(o.skin, 0.15)])
    c.beginPath(); c.moveTo(-R * 0.42, R * 0.55); c.lineTo(-R * 0.48, R * 1.35); c.lineTo(R * 0.5, R * 1.35); c.lineTo(R * 0.46, R * 0.55); c.fill()
    // collar: fur (pilot), shirt points, or turned-up coat
    const col = o.collar || 'shirt'
    if (col === 'ruff') { for (let i = 0; i < 30; i++) { const a = -0.1 + i / 29 * (Math.PI + 0.2), x = Math.cos(a) * R * 0.95, y = R * 1.25 - Math.sin(a) * R * 0.28; E(c, x, y, R * 0.2, R * 0.16, a, i % 2 ? '#f6f2ea' : '#d9d2c4') } }
    else if (col === 'fur') { for (let i = 0; i < 26; i++) { const a = -0.15 + i / 25 * (Math.PI + 0.3), x = Math.cos(a) * R * 1.05, y = R * 1.32 - Math.sin(a) * R * 0.32; E(c, x, y, R * 0.22, R * 0.15, a, i % 2 ? '#d8c4a0' : '#bfa47c') } }
    else if (col === 'shirt') { c.fillStyle = o.shirt || '#ece4d2'; c.beginPath(); c.moveTo(-R * 0.55, R * 1.15); c.lineTo(0, R * 1.75); c.lineTo(R * 0.6, R * 1.15); c.lineTo(R * 0.35, R * 1.05); c.lineTo(0, R * 1.45); c.lineTo(-R * 0.3, R * 1.05); c.closePath(); c.fill()
      if (o.tie) { c.fillStyle = o.tie; c.beginPath(); c.moveTo(-R * 0.1, R * 1.45); c.lineTo(R * 0.1, R * 1.45); c.lineTo(R * 0.18, R * 2.6); c.lineTo(0, R * 2.8); c.lineTo(-R * 0.18, R * 2.6); c.fill() } }
    // lapels shadow line
    c.strokeStyle = drk(coat, 0.45); c.lineWidth = R * 0.04; c.beginPath(); c.moveTo(-R * 0.55, R * 1.2); c.lineTo(-R * 0.1, R * 2.9); c.moveTo(R * 0.6, R * 1.2); c.lineTo(R * 0.15, R * 2.9); c.stroke()
  }

  function hatBack(c, R, o) {
    if (o.hat === 'pilot') { // leather helmet wraps the skull and ears
      const h = o.hatCol || '#6b4528'
      c.fillStyle = rg(c, -R * 0.2, -R * 0.6, R * 0.1, R * 1.4, [lit(h, 0.15), h, drk(h, 0.45)])
      c.beginPath(); c.moveTo(-R * 1.02, R * 0.1); c.quadraticCurveTo(-R * 1.15, -R * 1.25, 0, -R * 1.22); c.quadraticCurveTo(R * 1.12, -R * 1.2, R * 1.02, -R * 0.05)
      c.lineTo(R * 0.95, R * 0.75); c.lineTo(R * 0.7, R * 0.8); c.lineTo(R * 0.72, -R * 0.2); c.quadraticCurveTo(0, -R * 0.75, -R * 0.75, -R * 0.2); c.lineTo(-R * 0.72, R * 0.8); c.lineTo(-R * 0.98, R * 0.75); c.closePath(); c.fill()
    } else if (o.hair) { c.fillStyle = o.hair; E(c, -R * 0.05, -R * 0.35, R * 0.98, R * 0.85, 0) ; c.fill() }
  }

  function face(c, R, o) {
    const s = o.skin, rimSide = o.rimSide || 1
    // ears
    E(c, -R * 0.8, R * 0.02, R * 0.16, R * 0.26, 0.2, drk(s, 0.12)); E(c, R * 0.82, R * 0.02, R * 0.12, R * 0.24, -0.2, drk(s, 0.2))
    // head shape: slightly turned to the viewer's right (three-quarter)
    c.fillStyle = rg(c, -R * 0.25 * rimSide, -R * 0.35, R * 0.1, R * 1.25, [lit(s, 0.18), s, drk(s, 0.32)])
    c.beginPath(); c.moveTo(-R * 0.76, -R * 0.35); c.quadraticCurveTo(-R * 0.8, -R * 1.04, 0, -R * 1.04); c.quadraticCurveTo(R * 0.8, -R * 1.02, R * 0.78, -R * 0.3)
    c.quadraticCurveTo(R * 0.8, R * 0.3, R * 0.6, R * 0.72); c.quadraticCurveTo(R * 0.4, R * 1.02, 0, R * 1.08); c.quadraticCurveTo(-R * 0.42, R * 1.02, -R * 0.62, R * 0.7)
    c.quadraticCurveTo(-R * 0.8, R * 0.3, -R * 0.76, -R * 0.35); c.closePath(); c.fill()
    // rim light along the action side
    if (o.rim) { c.save(); c.clip(); c.fillStyle = lg(c, rimSide * R * 0.95, 0, rimSide * R * 0.45, 0, [o.rim + 'cc', o.rim + '00']); c.fillRect(-R * 1.2, -R * 1.2, R * 2.4, R * 2.4); c.restore() }
    // cheek and jaw shading
    c.save(); c.clip()
    for (const sd of [-1, 1]) { c.fillStyle = rg(c, sd * R * 0.62, R * 0.3, 0, R * 0.42, [drk(s, 0.28) + '99', drk(s, 0.28) + '00']); c.fillRect(-R * 1.2, -R * 1.2, R * 2.4, R * 2.4) }
    c.fillStyle = rg(c, 0, -R * 0.62, 0, R * 0.5, [lit(s, 0.25) + '88', lit(s, 0.25) + '00']); c.fillRect(-R * 1.2, -R * 1.2, R * 2.4, R * 2.4)
    if (o.stubble) { c.fillStyle = lg(c, 0, R * 0.25, 0, R * 1.05, ['rgba(45,32,26,0)', 'rgba(45,32,26,0.28)']); c.fillRect(-R * 1.2, R * 0.25, R * 2.4, R * 1) }
    c.restore()
  }

  function eyes(c, R, o) {
    const mood = o.mood || 'fierce', lk = o.look || [0, 0]
    const open = { fierce: 0.62, shock: 1.15, grin: 0.55, dread: 0.95 }[mood]
    for (const side of [-1, 1]) {
      const x = side * R * 0.34, y = -R * 0.12, w = R * 0.24, h = R * 0.16 * open
      // socket shadow
      E(c, x, y - R * 0.02, w * 1.35, h * 1.6 + R * 0.05, 0, 'rgba(60,30,20,0.18)')
      // white
      c.save(); c.beginPath(); c.moveTo(x - w, y); c.quadraticCurveTo(x, y - h * 2, x + w, y); c.quadraticCurveTo(x, y + h * 1.4, x - w, y); c.closePath()
      c.fillStyle = '#f2ece2'; c.fill(); c.clip()
      const ix = x + lk[0] * w * 0.45, iy = y + lk[1] * h * 0.4
      E(c, ix, iy, R * 0.095, R * 0.095, 0, o.iris || '#4a6a8a'); E(c, ix, iy, R * 0.05, R * 0.05, 0, '#120c08')
      E(c, ix + R * 0.03, iy - R * 0.035, R * 0.024, R * 0.024, 0, '#ffffff')
      c.fillStyle = 'rgba(80,50,40,0.35)'; c.fillRect(x - w, y - h * 2, w * 2, h * 0.7) // lid shadow
      c.restore()
      // upper lid line
      c.strokeStyle = '#2a1810'; c.lineWidth = R * 0.035; c.lineCap = 'round'
      c.beginPath(); c.moveTo(x - w * 1.05, y + R * 0.01); c.quadraticCurveTo(x, y - h * 2.05, x + w * 1.05, y); c.stroke()
      // brows by mood: inner end (toward nose) and outer end heights
      const b = { fierce: [-0.22, -0.36], shock: [-0.5, -0.46], grin: [-0.34, -0.42], dread: [-0.46, -0.32] }[mood]
      const inner = x - side * w * 0.9, outer = x + side * w * 1.15
      c.strokeStyle = o.brow || o.hair || '#2b1d12'; c.lineWidth = R * 0.08
      c.beginPath(); c.moveTo(inner, R * b[0] - R * 0.02); c.quadraticCurveTo((inner + outer) / 2, R * Math.min(b[0], b[1]) - R * 0.06, outer, R * b[1]); c.stroke()
    }
    if (o.mood === 'fierce') { c.strokeStyle = 'rgba(60,30,20,0.35)'; c.lineWidth = R * 0.02; c.beginPath(); c.moveTo(-R * 0.05, -R * 0.3); c.lineTo(-R * 0.03, -R * 0.18); c.moveTo(R * 0.05, -R * 0.3); c.lineTo(R * 0.03, -R * 0.18); c.stroke() }
  }

  function nose(c, R, o) {
    const s = o.skin
    c.fillStyle = drk(s, 0.22); c.beginPath(); c.moveTo(R * 0.02, -R * 0.1); c.quadraticCurveTo(R * 0.12, R * 0.2, R * 0.16, R * 0.32); c.quadraticCurveTo(R * 0.02, R * 0.4, -R * 0.12, R * 0.32); c.quadraticCurveTo(-R * 0.02, R * 0.3, R * 0.06, R * 0.22); c.quadraticCurveTo(R * 0.02, R * 0.05, -R * 0.02, -R * 0.1); c.fill()
    E(c, R * 0.0, R * 0.22, R * 0.07, R * 0.05, 0, lit(s, 0.25) + 'aa')
  }

  function mouth(c, R, o) {
    const mood = o.mood || 'fierce', y = R * 0.6
    if (o.moustache) E(c, 0, R * 0.47, R * (o.mw || 0.3), R * (o.mh || 0.09), 0, o.moustache)
    c.lineCap = 'round'
    if (mood === 'fierce') { // gritted teeth
      c.fillStyle = '#3a1612'; c.beginPath(); c.moveTo(-R * 0.3, y - R * 0.02); c.quadraticCurveTo(0, y - R * 0.1, R * 0.3, y - R * 0.02); c.quadraticCurveTo(0, y + R * 0.2, -R * 0.3, y - R * 0.02); c.fill()
      c.fillStyle = '#efe6d6'; c.beginPath(); c.moveTo(-R * 0.25, y - R * 0.03); c.quadraticCurveTo(0, y - R * 0.08, R * 0.25, y - R * 0.03); c.lineTo(R * 0.23, y + R * 0.07); c.quadraticCurveTo(0, y + R * 0.11, -R * 0.23, y + R * 0.07); c.closePath(); c.fill()
      c.strokeStyle = 'rgba(60,40,30,0.7)'; c.lineWidth = R * 0.012; c.beginPath(); c.moveTo(-R * 0.24, y + R * 0.025); c.quadraticCurveTo(0, y + R * 0.01, R * 0.24, y + R * 0.025); c.stroke()
      c.strokeStyle = 'rgba(80,60,50,0.6)'; c.lineWidth = R * 0.012; for (let k = -3; k <= 3; k++) { c.beginPath(); c.moveTo(k * R * 0.07, y - R * 0.05); c.lineTo(k * R * 0.07, y + R * 0.09); c.stroke() }
    } else if (mood === 'shock' || mood === 'dread') {
      const oh = mood === 'shock' ? 0.17 : 0.1
      E(c, 0, y + R * 0.04, R * 0.13, R * oh, 0, '#2a0e0a'); E(c, 0, y - R * oh * 0.6, R * 0.09, R * 0.03, 0, '#efe6d6')
    } else { // grin: one side up, teeth showing
      c.fillStyle = '#3a1612'; c.beginPath(); c.moveTo(-R * 0.28, y - R * 0.02); c.quadraticCurveTo(0, y + R * 0.2, R * 0.32, y - R * 0.1); c.quadraticCurveTo(0, y + R * 0.02, -R * 0.28, y - R * 0.02); c.fill()
      c.fillStyle = '#efe6d6'; c.beginPath(); c.moveTo(-R * 0.22, y - R * 0.005); c.quadraticCurveTo(0, y + R * 0.06, R * 0.26, y - R * 0.07); c.lineTo(R * 0.24, y - R * 0.03); c.quadraticCurveTo(0, y + R * 0.1, -R * 0.2, y + R * 0.02); c.fill()
      c.strokeStyle = 'rgba(60,30,20,0.4)'; c.lineWidth = R * 0.02; c.beginPath(); c.moveTo(R * 0.36, y - R * 0.18); c.quadraticCurveTo(R * 0.42, y - R * 0.05, R * 0.34, y + R * 0.04); c.stroke()
    }
    if (o.beard) { c.fillStyle = o.beard; c.beginPath(); c.moveTo(-R * 0.62, R * 0.35); c.quadraticCurveTo(-R * 0.55, R * 1.2, 0, R * 1.25); c.quadraticCurveTo(R * 0.58, R * 1.2, R * 0.62, R * 0.35); c.quadraticCurveTo(R * 0.35, R * 0.85, 0, R * 0.82); c.quadraticCurveTo(-R * 0.35, R * 0.85, -R * 0.62, R * 0.35); c.fill() }
  }

  function hatFront(c, R, o) {
    const h = o.hatCol || '#6b4528'
    if (o.hat === 'pilot') {
      // brow band of the helmet and the strap
      c.fillStyle = lg(c, 0, -R * 0.95, 0, -R * 0.5, [lit(h, 0.1), drk(h, 0.2)])
      c.beginPath(); c.moveTo(-R * 0.86, -R * 0.38); c.quadraticCurveTo(-R * 0.9, -R * 1.18, 0, -R * 1.18); c.quadraticCurveTo(R * 0.9, -R * 1.18, R * 0.86, -R * 0.38); c.quadraticCurveTo(0, -R * 0.7, -R * 0.86, -R * 0.38); c.fill()
      c.strokeStyle = drk(h, 0.5); c.lineWidth = R * 0.025; c.beginPath(); c.moveTo(0, -R * 1.18); c.lineTo(0, -R * 0.72); c.stroke()
      c.strokeStyle = drk(h, 0.35); c.lineWidth = R * 0.07; c.beginPath(); c.moveTo(-R * 0.72, R * 0.6); c.quadraticCurveTo(-R * 0.5, R * 1.02, -R * 0.1, R * 1.06); c.stroke()
      if (o.goggles) for (const side of [-1, 1]) { // pushed up on the forehead
        const gx = side * R * 0.36, gy = -R * 0.78
        E(c, gx, gy, R * 0.25, R * 0.19, 0, '#3a3028'); E(c, gx, gy, R * 0.19, R * 0.14, 0, rg(c, gx - R * 0.06, gy - R * 0.05, R * 0.02, R * 0.2, ['#cfe4f0', '#6a8ca8', '#2a3a4a']))
        E(c, gx - R * 0.07, gy - R * 0.05, R * 0.05, R * 0.025, -0.4, 'rgba(255,255,255,0.75)')
      }
    } else if (o.hat === 'fedora') {
      c.fillStyle = lg(c, 0, -R * 1.7, 0, -R * 0.6, [lit(h, 0.15), h]); c.beginPath(); c.moveTo(-R * 0.82, -R * 0.62); c.quadraticCurveTo(-R * 0.9, -R * 1.65, 0, -R * 1.55); c.quadraticCurveTo(R * 0.9, -R * 1.65, R * 0.82, -R * 0.62); c.closePath(); c.fill()
      c.fillStyle = '#14110e'; c.fillRect(-R * 0.82, -R * 0.86, R * 1.64, R * 0.2)
      E(c, 0, -R * 0.62, R * 1.45, R * 0.2, -0.04, drk(h, 0.3))
    } else if (o.hat === 'navy') {
      c.fillStyle = lg(c, 0, -R * 1.5, 0, -R * 0.7, ['#f4f0e6', '#d8d2c4']); E(c, 0, -R * 1.02, R * 1.05, R * 0.32, 0); c.fill()
      c.fillStyle = '#16181e'; c.fillRect(-R * 0.85, -R * 0.98, R * 1.7, R * 0.28)
      c.fillStyle = '#0c0d10'; c.beginPath(); c.moveTo(-R * 0.82, -R * 0.7); c.quadraticCurveTo(0, -R * 0.4, R * 0.82, -R * 0.7); c.lineTo(R * 0.82, -R * 0.78); c.lineTo(-R * 0.82, -R * 0.78); c.fill()
      E(c, 0, -R * 0.86, R * 0.13, R * 0.1, 0, '#d8b85a')
    } else if (o.hat === 'capotain' || o.hat === 'brim') {
      const tall = o.hat === 'capotain' ? 1.25 : 0.62, top = -R * 0.72 - R * tall
      c.fillStyle = lg(c, -R, 0, R, 0, [drk(h, 0.25), lit(h, 0.12), drk(h, 0.35)]); c.beginPath(); c.moveTo(-R * 0.8, -R * 0.7); c.lineTo(-R * 0.62, top + R * 0.05); c.quadraticCurveTo(0, top - R * 0.12, R * 0.62, top + R * 0.05); c.lineTo(R * 0.8, -R * 0.7); c.closePath(); c.fill()
      if (o.hat === 'brim') { c.strokeStyle = drk(h, 0.4); c.lineWidth = R * 0.04; c.beginPath(); c.moveTo(-R * 0.15, top); c.quadraticCurveTo(0, top + R * 0.25, R * 0.15, top); c.stroke() }
      c.fillStyle = o.band || '#1a120c'; c.fillRect(-R * 0.79, -R * 0.92, R * 1.58, R * 0.18)
      E(c, 0, -R * 0.72, R * (o.hat === 'brim' ? 1.55 : 1.35), R * 0.2, -0.03, drk(h, 0.35))
    } else if (o.hat === 'turban') {
      c.fillStyle = rg(c, -R * 0.2, -R * 1.1, R * 0.1, R * 1.2, [lit(h, 0.2), h, drk(h, 0.35)]); E(c, 0, -R * 0.95, R * 1.05, R * 0.55, 0); c.fill()
      c.strokeStyle = drk(h, 0.3); c.lineWidth = R * 0.035; for (let k = 0; k < 4; k++) { c.beginPath(); c.ellipse(0, -R * 0.95 + (k - 1.5) * R * 0.14, R * 0.98, R * 0.3, -0.2 + k * 0.12, Math.PI * 1.05, Math.PI * 1.95); c.stroke() }
    } else if (o.hair) {
      c.fillStyle = o.hair; c.beginPath(); c.moveTo(-R * 0.86, -R * 0.25); c.quadraticCurveTo(-R * 0.95, -R * 1.15, R * 0.05, -R * 1.12); c.quadraticCurveTo(R * 0.95, -R * 1.1, R * 0.86, -R * 0.3); c.quadraticCurveTo(R * 0.6, -R * 0.85, R * 0.1, -R * 0.82); c.quadraticCurveTo(-R * 0.55, -R * 0.82, -R * 0.86, -R * 0.25); c.fill()
    }
  }

  function portrait(c, cx, cy, R, o) {
    c.save(); c.translate(cx, cy); c.rotate(o.tilt || 0)
    shoulders(c, R, o); hatBack(c, R, o); face(c, R, o); eyes(c, R, o); nose(c, R, o); mouth(c, R, o); hatFront(c, R, o)
    c.restore()
  }
  window.portrait = portrait
})()
