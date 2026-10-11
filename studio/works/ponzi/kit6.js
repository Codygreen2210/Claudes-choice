// kit6.js: cut-paper pieces for the Ponzi film, on top of lib.js: the man himself, a liner, a 1920 touring car,
// coupons and stamps, bills and coin, people as counters, prison bars, a palm. Money is the one gold; debt is the one red.
(function () {
  const { clamp, lerp, rng, noise } = K
  const { W, H, C, F, layer, person, glow, text, rr, hatch, coin } = L
  const INK = C.ink
  // Charles Ponzi: a small, dapper man. Straw boater, cane, a handkerchief of gold. (x, y) = feet
  function ponzi(c, x, y, h, o = {}) {
    const col = o.col || INK, face = o.face || 1, s = h / 100, st = o.stride ?? 0, bob = -Math.abs(Math.cos(o.walk || 0)) * 1.6 * st
    person(c, x, y, h, { hat: 'none', bulk: 0.92, cane: o.cane !== false, ...o, col })
    c.save(); c.translate(x, y); c.scale(s * face, s); c.translate(0, bob); c.rotate(o.lean || 0); c.fillStyle = col
    c.fillRect(-6.5, -105, 16, 9); c.beginPath(); c.roundRect(-13, -97.6, 29, 2.8, 1.4); c.fill()                      // the boater: flat crown, flat brim
    if (o.gold !== false) { c.fillStyle = C.gold; c.beginPath(); c.moveTo(3, -76); c.lineTo(9, -78); c.lineTo(8, -71); c.closePath(); c.fill() }
    c.restore()
  }
  // a Boston policeman: tall rounded helmet, long coat
  function cop(c, x, y, h, o = {}) {
    const col = o.col || INK, face = o.face || 1, s = h / 100
    person(c, x, y, h, { hat: 'none', bulk: 1.15, belly: 2, ...o, col })
    c.save(); c.translate(x, y); c.scale(s * face, s); c.fillStyle = col; c.beginPath(); c.moveTo(-7, -96); c.quadraticCurveTo(-7, -112, 2, -113); c.quadraticCurveTo(11, -112, 11, -96); c.closePath(); c.fill(); c.fillRect(-9, -97.5, 23, 2.4); c.fillRect(0.5, -117, 3, 5)
    c.fillStyle = o.badge || C.gold; c.beginPath(); c.arc(7, -70, 2.6, 0, 7); c.fill(); c.restore()
  }
  // an ocean liner, bow toward +x*face. (x, y) = waterline amidships
  function liner(c, x, y, s, o = {}) {
    const col = o.col || INK, face = o.face || 1, t = o.t || 0
    c.save(); c.translate(x, y + Math.sin(t * 1.1) * 3 * s); c.scale(s * face, s); c.fillStyle = col; c.strokeStyle = col
    c.beginPath(); c.moveTo(-230, -34); c.lineTo(-214, 6); c.lineTo(214, 6); c.lineTo(250, -40); c.lineTo(200, -34); c.closePath(); c.fill()
    c.fillRect(-170, -58, 330, 26); c.fillRect(-130, -78, 250, 22)
    for (const fx of [-70, 30]) { c.beginPath(); c.moveTo(fx - 16, -78); c.lineTo(fx - 20, -140); c.lineTo(fx + 12, -140); c.lineTo(fx + 16, -78); c.closePath(); c.fill(); c.fillStyle = o.band || C.red; c.fillRect(fx - 19.4, -132, 31, 10); c.fillStyle = col }
    c.lineWidth = 3; c.beginPath(); c.moveTo(-190, -34); c.lineTo(-190, -150); c.moveTo(180, -40); c.lineTo(180, -150); c.stroke()
    c.fillStyle = o.port || C.paper2; for (let i = 0; i < 14; i++) c.fillRect(-156 + i * 22, -50, 8, 8)
    c.restore()
    if (o.smoke !== 0) for (const fx of [-70, 30]) for (let i = 0; i < 7; i++) { const a = ((t * 0.3 + i / 7) % 1); B.smoke(c, x + (fx - 4) * s * face - a * 300 * s * face, y - 150 * s - a * 120 * s, (16 + a * 46) * s, 0.5 * (1 - a), i + 2, '#3a302a') }
  }
  // a 1920 touring car, nose toward +x*face: long hood, upright windscreen, folded top, two big spoked wheels, running board
  function car(c, x, y, s, o = {}) {
    const col = o.col || INK, face = o.face || 1
    c.save(); c.translate(x, y); c.scale(s * face, s); c.fillStyle = col; c.strokeStyle = col; c.lineCap = 'round'
    c.beginPath(); c.moveTo(-150, -40); c.lineTo(-150, -84); c.quadraticCurveTo(-148, -92, -138, -92); c.lineTo(20, -92); c.lineTo(34, -84); c.lineTo(150, -80); c.quadraticCurveTo(160, -78, 160, -66); c.lineTo(160, -40); c.closePath(); c.fill()        // body and hood
    c.fillRect(160, -74, 12, 34); c.fillRect(-172, -48, 350, 9)                                                                                            // radiator, running board
    c.beginPath(); c.ellipse(-158, -98, 22, 10, -0.2, 0, 7); c.fill()                                  // folded top
    c.lineWidth = 5; c.beginPath(); c.moveTo(22, -92); c.lineTo(10, -140); c.stroke(); c.lineWidth = 3; c.beginPath(); c.moveTo(-40, -92); c.lineTo(-40, -110); c.stroke()
    c.beginPath(); c.arc(-64, -96, 12, 0, 7); c.fill(); if (o.driver) { c.beginPath(); c.arc(-18, -112, 11, 0, 7); c.fill(); c.fillRect(-28, -104, 20, 14); c.fillRect(-31, -126, 26, 5); c.fillRect(-26, -134, 16, 9) }
    for (const wx of [-104, 108]) { c.beginPath(); c.arc(wx, -34, 36, Math.PI, 0); c.lineTo(wx + 46, -40); c.lineTo(wx - 46, -40); c.closePath(); c.fill(); c.fillStyle = o.bg || C.paper; c.beginPath(); c.arc(wx, -30, 30, 0, 7); c.fill(); c.fillStyle = col; c.lineWidth = 7; c.beginPath(); c.arc(wx, -30, 27, 0, 7); c.stroke(); c.lineWidth = 2.6; c.save(); c.translate(wx, -30); c.rotate(o.roll || 0); for (let k = 0; k < 6; k++) { c.rotate(Math.PI / 6); c.beginPath(); c.moveTo(-27, 0); c.lineTo(27, 0); c.stroke() } c.restore(); c.beginPath(); c.arc(wx, -30, 6, 0, 7); c.fill() }
    c.fillStyle = C.gold2; c.beginPath(); c.arc(176, -78, 7, 0, 7); c.fill()
    c.restore()
  }
  // an international reply coupon: a small engraved slip. (x, y) = centre
  function coupon(c, x, y, s, rot = 0, o = {}) {
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    c.fillStyle = 'rgba(60,40,20,0.22)'; c.fillRect(-146, -88, 300, 190); c.fillStyle = o.fill || '#f4ead2'; c.fillRect(-150, -95, 300, 190); c.strokeStyle = INK; c.lineWidth = 3; c.strokeRect(-150, -95, 300, 190); c.lineWidth = 1.2; c.strokeRect(-141, -86, 282, 172)
    text(c, 'COUPON-RÉPONSE', 0, -46, F.sc(25), INK, { track: 3 }); text(c, 'INTERNATIONAL', 0, -18, F.sc(25), INK, { track: 3 })
    c.strokeStyle = INK; c.lineWidth = 2; c.beginPath(); c.arc(0, 34, 30, 0, 7); c.stroke(); c.beginPath(); c.arc(0, 34, 22, 0, 7); c.stroke(); text(c, 'UPU', 0, 41, F.old(15, true), INK)
    for (const sx of [-100, 100]) { c.beginPath(); c.arc(sx, 34, 20, 0, 7); c.stroke(); for (let k = 0; k < 8; k++) { const a = k / 8 * 6.283; c.beginPath(); c.moveTo(sx + Math.cos(a) * 8, 34 + Math.sin(a) * 8); c.lineTo(sx + Math.cos(a) * 18, 34 + Math.sin(a) * 18); c.stroke() } }
    c.restore()
  }
  function stamp(c, x, y, s, rot = 0, col = C.red) {
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s); c.fillStyle = '#f4ead2'; c.fillRect(-34, -42, 68, 84)
    c.fillStyle = C.paper3; for (let i = 0; i < 7; i++) { c.beginPath(); c.arc(-30 + i * 10, -42, 3, 0, 7); c.arc(-30 + i * 10, 42, 3, 0, 7); c.fill() } for (let i = 0; i < 8; i++) { c.beginPath(); c.arc(-34, -36 + i * 10.4, 3, 0, 7); c.arc(34, -36 + i * 10.4, 3, 0, 7); c.fill() }
    c.fillStyle = col; c.fillRect(-26, -34, 52, 68); c.fillStyle = '#f4ead2'; c.beginPath(); c.ellipse(0, -4, 15, 20, 0, 0, 7); c.fill(); c.fillStyle = col; c.beginPath(); c.arc(1, -9, 7, 0, 7); c.fill(); c.beginPath(); c.moveTo(-10, 12); c.quadraticCurveTo(0, -4, 11, 12); c.closePath(); c.fill()
    text(c, '2¢', 0, 31, F.old(13, true), '#f4ead2'); c.restore()
  }
  // a banded stack of banknotes, n high. (x, y) = bottom centre
  function bills(c, x, y, n, s = 1, col = C.gold) {
    c.save(); c.translate(x, y); c.scale(s, s)
    for (let i = 0; i < n; i++) { const yy = -i * 13; c.fillStyle = col; c.fillRect(-46, yy - 12, 92, 11); c.fillStyle = INK; c.fillRect(-46, yy - 1.5, 92, 1.5); c.fillRect(-8, yy - 12, 16, 11) }
    c.restore()
  }
  // a person as a counter: head and shoulders, for diagrams. state: 0 ink, 1 gold (paid), 2 red (owed), 3 dashed (not there)
  function pawn(c, x, y, s, state = 0) {
    c.save(); c.translate(x, y); c.scale(s, s)
    const col = state === 1 ? C.gold : state === 2 ? C.red2 : INK
    if (state === 3) { c.strokeStyle = C.ink3; c.lineWidth = 2.5; c.setLineDash([5, 5]); c.beginPath(); c.arc(0, -30, 10, 0, 7); c.stroke(); c.beginPath(); c.moveTo(-15, 0); c.quadraticCurveTo(-15, -20, 0, -20); c.quadraticCurveTo(15, -20, 15, 0); c.closePath(); c.stroke() }
    else { c.fillStyle = col; c.beginPath(); c.arc(0, -30, 10, 0, 7); c.fill(); c.beginPath(); c.moveTo(-15, 0); c.quadraticCurveTo(-15, -20, 0, -20); c.quadraticCurveTo(15, -20, 15, 0); c.closePath(); c.fill() }
    c.restore()
  }
  function bars(c, x0, x1, y0, y1, p = 1, col = INK, gap = 70, lw = 16) { c.save(); c.fillStyle = col; for (let x = x0; x <= x1; x += gap) c.fillRect(x - lw / 2, y0 - (1 - clamp(p)) * (y1 - y0 + 40), lw, y1 - y0); c.fillRect(x0 - 30, y0 - (1 - clamp(p)) * (y1 - y0 + 40) + (y1 - y0) * 0.5, x1 - x0 + 60, lw); c.restore() }
  function palm(c, x, y, s, col = INK) {
    c.save(); c.translate(x, y); c.scale(s, s); c.strokeStyle = col; c.fillStyle = col; c.lineCap = 'round'; c.lineWidth = 11; c.beginPath(); c.moveTo(0, 0); c.quadraticCurveTo(14, -90, -6, -190); c.stroke()
    for (const [a, l] of [[-2.9, 90], [-2.4, 100], [-1.9, 86], [-1.2, 86], [-0.7, 100], [-0.2, 92], [-1.55, 70]]) { c.beginPath(); c.moveTo(-6, -190); const ex = -6 + Math.cos(a) * l, ey = -190 + Math.sin(a) * l + 40; c.quadraticCurveTo(-6 + Math.cos(a) * l * 0.6, -190 + Math.sin(a) * l * 0.9 - 14, ex, ey); c.quadraticCurveTo(-6 + Math.cos(a) * l * 0.5, -190 + Math.sin(a) * l * 0.5 + 8, -6, -190); c.fill() }
    c.restore()
  }
  // a newspaper front page. (x, y) = centre
  function page(c, x, y, s, rot, o = {}) {
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s); c.fillStyle = 'rgba(60,40,20,0.25)'; c.fillRect(-412, -392, 840, 820); c.fillStyle = '#f4ead2'; c.fillRect(-420, -400, 840, 820); c.strokeStyle = INK; c.lineWidth = 3; c.strokeRect(-420, -400, 840, 820)
    text(c, o.name || 'THE BOSTON POST', 0, -322, F.head(64, 900), INK, { track: 4 }); c.lineWidth = 3; c.beginPath(); c.moveTo(-380, -300); c.lineTo(380, -300); c.stroke(); c.lineWidth = 1; c.beginPath(); c.moveTo(-380, -293); c.lineTo(380, -293); c.stroke()
    text(c, o.date || '', 0, -264, F.bodyI(28), C.ink2)
    const hs = o.head || []; hs.forEach((h, i) => text(c, h, 0, -180 + i * (o.hpx || 72) * 1.08, F.head(o.hpx || 72, 900), o.hcol || INK, { track: 1 }))
    const y0 = -180 + hs.length * (o.hpx || 72) * 1.08 - 20; if (o.sub) text(c, o.sub, 0, y0 + 10, F.bodyI(38), C.ink2)
    c.strokeStyle = C.ink3; c.lineWidth = 2.5; for (let col = 0; col < 3; col++) for (let yy = y0 + 60; yy < 380; yy += 28) { const i = Math.round(yy / 28); c.beginPath(); c.moveTo(-370 + col * 255, yy); c.lineTo(-370 + col * 255 + 225 - ((i * 7 + col * 3) % 5 === 0 ? 80 : 0), yy); c.stroke() }
    if (o.draw) o.draw(c, y0)
    c.restore()
  }
  window.PZ = { ponzi, cop, liner, car, coupon, stamp, bills, pawn, bars, palm, page }
})()
