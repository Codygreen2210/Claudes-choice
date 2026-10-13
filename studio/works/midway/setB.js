// setB.js: the Battle of Midway in Style B (painted). The open ocean, carriers, planes, smoke and fire.
window.MWB = (function () {
  const { W, H, clamp, lerp, prog, keys, rng, ell, poly, smooth, shade, mixCol, vgrad, hgrad, rgrad, layer, ridge, fog, sky, post, person, crowd, paper, text, tree } = PK
  PK.costume('nagumo', { skin: '#d8a888', shirt: '#2a2a30', pants: '#2a2a30', coat: '#2a2a30', boot: '#0e0c0a', hat: 'navy', hatCol: '#2a2a30', buttons: '#d8b85a', collar: 'stand', hair: '#4a4a4a', moustache: '#3a3a3a' })
  PK.costume('yamamoto', { skin: '#d8a888', shirt: '#ecebe4', pants: '#ecebe4', coat: '#ecebe4', boot: '#0e0c0a', hat: 'navy', hatCol: '#ecebe4', buttons: '#d8b85a', collar: 'stand', hair: '#5a5a5a' })
  PK.costume('rochefort', { skin: '#dcae90', shirt: '#e8e2d4', pants: '#4a4a52', boot: '#14110e', hat: null, collar: 'tie', tie: '#2a2a3a', hair: '#6a6a6a', robe: '#8a2a2a', coat: '#8a2a2a' })
  PK.costume('nimitz', { skin: '#e2b49a', shirt: '#b5a27a', pants: '#b5a27a', boot: '#3a2a1a', hat: 'navy', hatCol: '#b5a27a', collar: 'tie', tie: '#5a4a32', hair: '#e8e4dc' })
  PK.costume('worker', { skin: '#dcae90', shirt: '#5a6a7a', pants: '#3a4450', boot: '#2a2018', hat: 'cap', hatCol: '#5a5a5a', hair: '#5a3c22' })
  PK.costume('jpcrew', { skin: '#d8a888', shirt: '#c8c2b0', pants: '#5a5a48', boot: '#2a2420', hat: 'cap', hatCol: '#e8e4d8', hair: '#14110e' })
  const SEA = { day: ['#7a9cbc', '#dfe6e8'], morning: ['#8aa6c4', '#f2dcc0'], noon: ['#7a9cbc', '#e8ecec'], dusk: ['#5a6a8a', '#f0b880'] }
  // the open ocean: sky, horizon haze, rolling water with highlights; o.tod picks the light
  function ocean(c, cam, t, o = {}) {
    const [a, b] = SEA[o.tod || 'day']
    layer(c, cam, 0.04, c => sky(c, a, b, { horizon: o.horizon || 620, clouds: o.clouds ?? 9, sun: o.sun || [1500, 160, 520] }))
    layer(c, cam, 0.15, c => { const r = rng(5); for (let k = 0; k < 6; k++) { const x = r() * 3200 - 600, y = 360 + r() * 160; c.fillStyle = 'rgba(255,255,255,0.55)'; for (let j = 0; j < 6; j++) { ell(c, x + j * 60, y - Math.sin(j) * 30, 90, 46, 0); c.fill() } c.fillStyle = 'rgba(160,170,190,0.35)'; ell(c, x + 150, y + 30, 220, 26, 0); c.fill() } })
    layer(c, cam, 0.5, c => { c.fillStyle = vgrad(c, (o.horizon || 620), 1300, o.water || '#4a6a88', '#1a2a3e'); c.fillRect(-2000, (o.horizon || 620), 6000, 1400); fog(c, (o.horizon || 620) + 10, 60, '230,236,240', 0.55) })
    layer(c, cam, 1, c => { const r = rng(8); c.strokeStyle = 'rgba(230,240,250,0.18)'; c.lineWidth = 2; for (let k = 0; k < 120; k++) { const y = (o.horizon || 620) + 20 + r() * 700, w = 20 + (y - 600) * 0.15, x = ((r() * 3600 + t * (10 + y * 0.02)) % 3800) - 900; c.beginPath(); c.moveTo(x, y); c.quadraticCurveTo(x + w / 2, y - 3, x + w, y); c.stroke() } if (o.inner) o.inner(c) })
  }
  // a carrier seen from the side. o.jp: Japanese (deck stripes, rising sun on the bow flag), o.fire 0..1, o.island 'left'|'right'
  function carrier(c, x, y, s, t, o = {}) {
    c.save(); c.translate(x, y + Math.sin(t * 0.8 + x) * 2); c.scale(s * (o.f || 1), s)
    const hull = o.jp ? '#4e5054' : '#5a6672', deck = o.jp ? '#a07e54' : '#8a8478'
    // wake and bow wave
    c.fillStyle = 'rgba(240,248,255,0.55)'; for (let k = 0; k < 10; k++) ell(c, -640 - k * 80, 18 + k * 2, 70 + k * 16, 9 + k, 0)
    for (let k = 0; k < 5; k++) ell(c, 640 - k * 30, 14 + Math.sin(t * 3 + k) * 2, 50 - k * 6, 8, 0, 'rgba(250,252,255,0.7)')
    // hull: the bow rises; boot-topping at the waterline
    c.fillStyle = hgrad(c, -640, 680, shade(hull, 0.12), hull, shade(hull, -0.28)); c.beginPath(); c.moveTo(-630, -50); c.lineTo(520, -64); c.quadraticCurveTo(640, -80, 690, -104); c.quadraticCurveTo(660, -20, 600, 20); c.lineTo(-600, 20); c.quadraticCurveTo(-640, 0, -630, -50); c.closePath(); c.fill()
    c.fillStyle = '#6a2a24'; c.beginPath(); c.moveTo(-605, 8); c.lineTo(612, 8); c.lineTo(600, 20); c.lineTo(-600, 20); c.closePath(); c.fill()
    // the open hangar sides under the flight deck
    c.fillStyle = shade(hull, -0.18); c.fillRect(-610, -104, 1190, 46)
    c.fillStyle = 'rgba(20,20,24,0.8)'; for (let k = -560; k < 540; k += 70) c.fillRect(k, -98, 46, 30)
    c.fillStyle = 'rgba(255,255,255,0.12)'; c.fillRect(-610, -60, 1190, 3)
    // flight deck: a long slab overhanging bow and stern, on thin supports
    c.fillStyle = shade(hull, -0.3); c.fillRect(-680, -120, 1390, 8); c.fillStyle = deck; c.fillRect(-680, -128, 1390, 10)
    c.strokeStyle = shade(hull, -0.3); c.lineWidth = 6; for (const sx of [-660, -620, 660, 690]) { c.beginPath(); c.moveTo(sx, -112); c.lineTo(sx + (sx > 0 ? -30 : 30), -64); c.stroke() }
    // island and funnel
    const ix = o.island === 'left' ? -220 : 200
    c.fillStyle = hgrad(c, ix - 50, ix + 60, shade(hull, 0.22), hull, shade(hull, -0.2)); c.fillRect(ix - 34, -230, 70, 102); c.fillRect(ix - 52, -262, 104, 36)
    c.fillStyle = 'rgba(180,200,210,0.6)'; c.fillRect(ix - 46, -254, 92, 10)
    c.strokeStyle = shade(hull, -0.35); c.lineWidth = 6; c.beginPath(); c.moveTo(ix, -262); c.lineTo(ix, -350); c.moveTo(ix - 30, -320); c.lineTo(ix + 30, -320); c.stroke()
    if (o.jp) { c.fillStyle = '#2e3034'; c.beginPath(); c.moveTo(ix + 130, -64); c.quadraticCurveTo(ix + 190, -60, ix + 200, -10); c.lineTo(ix + 160, -10); c.quadraticCurveTo(ix + 150, -40, ix + 110, -50); c.closePath(); c.fill() }
    else { c.fillStyle = shade(hull, -0.1); c.fillRect(ix + 40, -236, 60, 108); c.fillStyle = '#2a2a2e'; c.fillRect(ix + 40, -244, 60, 12) }
    // planes parked at the stern
    for (let k = 0; k < (o.planes ?? 6); k++) { const px = -600 + k * 80; ell(c, px, -134, 30, 6, 0, o.jp ? '#c8c4b0' : '#6a7a8a'); c.fillStyle = o.jp ? '#b8b4a0' : '#5a6a7a'; c.fillRect(px - 4, -146, 8, 10) }
    if (o.fire) fire(c, 0, -130, 1200 * o.fire, t, o.fire)
    c.restore()
  }
  // a destroyer, small and fast, with a long white wake
  function destroyer(c, x, y, s, t, o = {}) {
    c.save(); c.translate(x, y); c.scale(s * (o.f || 1), s)
    c.fillStyle = 'rgba(240,248,255,0.6)'; for (let k = 0; k < 14; k++) ell(c, -280 - k * 70, 6 + k * 1.5, 50 + k * 12, 8 + k, 0)
    c.fillStyle = hgrad(c, -260, 300, '#6a6a70', '#4a4a50'); poly(c, [[-260, -30], [300, -30], [240, 14], [-240, 14]]); c.fill()
    c.fillStyle = '#5a5a60'; c.fillRect(-80, -80, 120, 50); c.fillRect(60, -70, 40, 40); c.fillRect(-200, -60, 40, 30); c.fillStyle = '#3a3a40'; c.fillRect(-20, -120, 30, 40)
    c.restore()
  }
  function battleship(c, x, y, s, t) { c.save(); c.translate(x, y); c.scale(s, s); c.fillStyle = hgrad(c, -600, 600, '#5a5c60', '#3a3c40'); poly(c, [[-620, -50], [650, -50], [560, 30], [-560, 30]]); c.fill(); c.fillStyle = '#4a4c50'; poly(c, [[-80, -50], [-40, -260], [60, -260], [100, -50]]); c.fill(); c.fillRect(-400, -90, 160, 40); c.fillRect(260, -90, 160, 40); c.strokeStyle = '#3a3c40'; c.lineWidth = 10; c.beginPath(); c.moveTo(-240, -80); c.lineTo(-120, -86); c.moveTo(420, -80); c.lineTo(540, -86); c.stroke(); c.restore() }
  // fire and smoke on a burning ship
  function fire(c, x, y, w, t, k = 1) {
    const r = rng(11)
    for (let i = 0; i < 9; i++) { const fx = x + (r() - 0.5) * w, ph = (t * 0.25 + r()) % 1; for (let j = 0; j < 6; j++) { const pp = (ph + j / 6) % 1; ell(c, fx + pp * 160 + Math.sin(t + j) * 10, y - pp * 700 * k, (40 + pp * 140) * k, (34 + pp * 110) * k, 0, `rgba(${40 + pp * 30},${36 + pp * 30},${34 + pp * 30},${0.75 * (1 - pp)})`) } }
    for (let i = 0; i < 14; i++) { const fx = x + (r() - 0.5) * w, fl = Math.abs(Math.sin(t * 9 + i * 1.7)); ell(c, fx, y - 20 - fl * 50 * k, 30 * k, (50 + fl * 40) * k, 0, `rgba(255,${120 + fl * 80},40,${0.85})`); ell(c, fx, y - 10, 18 * k, 26 * k, 0, 'rgba(255,230,140,0.9)') }
  }
  function blast(c, x, y, s, u) { if (u <= 0 || u >= 1) return; c.save(); c.translate(x, y); c.scale(s, s); const r = 60 + u * 260; c.fillStyle = `rgba(255,${220 - u * 120},${120 - u * 100},${1 - u})`; ell(c, 0, 0, r, r * 0.8, 0); c.fill(); c.fillStyle = `rgba(255,250,220,${(1 - u) * 0.9})`; ell(c, 0, 0, r * 0.5, r * 0.4, 0); c.fill(); for (let k = 0; k < 10; k++) { const a = k / 10 * Math.PI * 2; c.strokeStyle = `rgba(60,50,40,${1 - u})`; c.lineWidth = 6; c.beginPath(); c.moveTo(Math.cos(a) * r * 0.6, Math.sin(a) * r * 0.5); c.lineTo(Math.cos(a) * r * 1.3, Math.sin(a) * r * 1.1 - u * 60); c.stroke() } c.restore() }
  function splash(c, x, y, s, u) { if (u <= 0 || u >= 1) return; c.save(); c.translate(x, y); c.scale(s, s); const h = Math.sin(Math.PI * Math.min(1, u * 1.4)) * 220, a = 1 - u
    c.fillStyle = `rgba(245,250,255,${a * 0.85})`; c.beginPath(); c.moveTo(-26, 0); c.quadraticCurveTo(-30, -h * 0.6, -8, -h); c.quadraticCurveTo(0, -h - 20, 8, -h); c.quadraticCurveTo(30, -h * 0.6, 26, 0); c.closePath(); c.fill()
    for (let k = 0; k < 10; k++) { const ang = -Math.PI / 2 + (k - 4.5) * 0.25, d = h * 0.9 + k * 6; ell(c, Math.cos(ang) * d * 0.4, -h * 0.7 + Math.sin(ang) * -d * 0.2 + u * 60, 5, 5, 0, `rgba(245,250,255,${a * 0.7})`) }
    ell(c, 0, 0, 70 * (0.6 + u), 10, 0, `rgba(240,248,255,${a * 0.6})`); c.restore() }
  function flak(c, t, x0, y0, w, h, n = 10, seed = 3) { const r = rng(seed); for (let k = 0; k < n; k++) { const ph = (t * 0.7 + r()) % 1, x = x0 + r() * w, y = y0 + r() * h; ell(c, x, y, 8 + ph * 34, 8 + ph * 30, 0, `rgba(40,36,34,${0.7 * (1 - ph)})`); if (ph < 0.1) ell(c, x, y, 14, 14, 0, 'rgba(255,220,140,0.9)') } }
  // planes, side view. kind: 'sbd' dive bomber, 'tbd' torpedo plane, 'zero', 'b17', 'kate', 'scout'. o.ang pitch, o.f facing
  function plane(c, x, y, s, t, o = {}) {
    const kind = o.kind || 'sbd', jp = kind === 'zero' || kind === 'kate' || kind === 'scout'
    const body = { sbd: '#5a6a7a', tbd: '#6a7a6a', zero: '#c8c4b0', b17: '#8a8a7a', kate: '#4a5a3a', scout: '#c8c4b0' }[kind], belly = jp ? shade(body, 0.1) : '#c8ccd0'
    c.save(); c.translate(x, y); c.scale(s * (o.f || 1), s); c.rotate(o.ang || 0)
    const L = kind === 'b17' ? 300 : 150
    c.fillStyle = vgrad(c, -24, 24, shade(body, 0.2), body, belly); c.beginPath(); c.moveTo(L * 0.62, -10); c.quadraticCurveTo(L * 0.7, 0, L * 0.62, 12); c.lineTo(-L * 0.6, 6); c.lineTo(-L * 0.64, -6); c.closePath(); c.fill()
    c.fillStyle = shade(body, -0.15); poly(c, [[-L * 0.5, -6], [-L * 0.66, -40], [-L * 0.56, -40], [-L * 0.38, -6]]); c.fill()
    c.fillStyle = shade(body, -0.1); poly(c, [[-L * 0.55, 2], [-L * 0.75, 10], [-L * 0.45, 8]]); c.fill()
    c.fillStyle = vgrad(c, -4, 14, shade(body, 0.1), shade(body, -0.25)); poly(c, [[L * 0.2, 2], [L * 0.32, 4], [-L * 0.05, 18], [-L * 0.16, 16]]); c.fill()
    c.fillStyle = 'rgba(170,200,220,0.85)'; c.beginPath(); c.moveTo(L * 0.3, -10); c.quadraticCurveTo(L * 0.1, -30, -L * (kind === 'tbd' ? 0.3 : 0.12), -10); c.fill()
    if (kind === 'b17') for (const ex of [0.15, 0.3]) ell(c, L * ex, 14, 14, 10, 0, '#4a4a40')
    c.fillStyle = '#2a2a2a'; c.fillRect(L * 0.66, -4, 8, 8); const pr = Math.sin(t * 60) * 22; c.fillStyle = 'rgba(40,40,40,0.4)'; ell(c, L * 0.7, 0, 3, 24, 0); c.fill(); c.strokeStyle = '#1a1a1a'; c.lineWidth = 3; c.beginPath(); c.moveTo(L * 0.7, -pr); c.lineTo(L * 0.7, pr); c.stroke()
    if (jp) ell(c, -L * 0.25, 0, 9, 9, 0, '#c8202a')
    else { c.fillStyle = '#1e2a5a'; ell(c, -L * 0.25, 0, 10, 10, 0); c.fill(); c.fillStyle = '#f2f2f2'; c.beginPath(); for (let k = 0; k < 5; k++) { const a = -Math.PI / 2 + k * 4 * Math.PI / 5; c.lineTo(-L * 0.25 + Math.cos(a) * 8, Math.sin(a) * 8) } c.fill() }
    if (o.load === 'torpedo') { c.fillStyle = '#4a4a4a'; c.fillRect(-L * 0.1, 18, L * 0.5, 7); ell(c, L * 0.4, 21, 6, 4, 0, '#4a4a4a') }
    if (o.load === 'bomb') ell(c, L * 0.05, 20, 18, 7, 0, '#3a3a3a')
    if (o.smoke) for (let k = 0; k < 8; k++) ell(c, -L * 0.6 - k * 30, -Math.sin(t * 3 + k) * 6, 10 + k * 5, 8 + k * 4, 0, `rgba(40,36,34,${0.6 - k * 0.07})`)
    c.restore()
  }
  // planes seen from above (formations, the dive)
  function planeTop(c, x, y, s, ang, o = {}) {
    c.save(); c.translate(x, y); c.rotate(ang); c.scale(s, s)
    const col = o.col || '#5a6a7a'
    c.fillStyle = col; poly(c, [[60, 0], [40, -8], [-50, -6], [-60, 0], [-50, 6], [40, 8]]); c.fill()
    poly(c, [[20, -10], [0, -90], [-14, -90], [-10, -10], [-10, 10], [-14, 90], [0, 90], [20, 10]]); c.fill()
    poly(c, [[-44, -4], [-54, -30], [-62, -30], [-58, 0], [-62, 30], [-54, 30], [-44, 4]]); c.fill()
    if (o.jp) { ell(c, 4, -60, 9, 9, 0, '#c8202a'); ell(c, 4, 60, 9, 9, 0, '#c8202a') }
    else { for (const wy of [-60, 60]) { ell(c, 4, wy, 10, 10, 0, '#1e2a5a'); c.fillStyle = '#f2f2f2'; c.beginPath(); for (let k = 0; k < 5; k++) { const a = -Math.PI / 2 + k * 4 * Math.PI / 5; c.lineTo(4 + Math.cos(a) * 8, wy + Math.sin(a) * 8) } c.fill() } }
    c.restore()
  }
  // a Japanese carrier seen from directly above: the flight deck with its painted red circle
  function carrierTop(c, x, y, s, t, o = {}) {
    c.save(); c.translate(x, y); c.rotate(o.rot || 0); c.scale(s, s)
    c.fillStyle = 'rgba(240,248,255,0.5)'; for (let k = 0; k < 12; k++) ell(c, -700 - k * 70, 0, 40 + k * 10, 60 + k * 8, 0)
    c.fillStyle = hgrad(c, 0, 0, '#4a4c50', '#4a4c50'); c.fillStyle = '#4a4c50'; poly(c, [[700, 0], [600, -110], [-680, -100], [-700, 0], [-680, 100], [600, 110]]); c.fill()
    c.fillStyle = vgrad(c, -90, 90, '#b08a5a', '#8a6a42'); c.fillRect(-660, -88, 1280, 176)
    c.strokeStyle = 'rgba(60,40,20,0.3)'; c.lineWidth = 2; for (let k = -80; k <= 80; k += 16) { c.beginPath(); c.moveTo(-660, k); c.lineTo(620, k); c.stroke() }
    c.strokeStyle = 'rgba(255,255,255,0.7)'; c.lineWidth = 8; c.beginPath(); c.moveTo(-660, 0); c.lineTo(620, 0); c.stroke()
    ell(c, 420, 0, 60, 60, 0, '#c8202a')
    c.fillStyle = '#3a3c40'; c.fillRect(-40, -150, 120, 60)
    for (let k = 0; k < (o.planes ?? 8); k++) planeTop(c, -560 + (k % 4) * 70, -40 + Math.floor(k / 4) * 80, 0.35, 0, { col: '#c8c4b0', jp: true })
    c.restore()
  }
  // inside: the codebreakers' basement (desks, cards, a machine), a Japanese carrier's hangar deck
  function basement(c, cam, t, o = {}) {
    layer(c, cam, 0.9, c => { c.fillStyle = vgrad(c, -200, 1000, '#4a4e48', '#2a2c28'); c.fillRect(-900, -400, 3800, 1700); c.strokeStyle = 'rgba(0,0,0,0.25)'; c.lineWidth = 2; for (let y = -400; y < 1000; y += 40) { c.beginPath(); c.moveTo(-900, y); c.lineTo(2900, y); c.stroke() } for (const lx of [500, 1400]) { c.fillStyle = '#1a1a18'; c.fillRect(lx - 2, -400, 4, 520); ell(c, lx, 130, 40, 20, 0, '#c8c8a0'); c.fillStyle = rgrad(c, lx, 200, 10, 600, 'rgba(255,240,180,0.25)', 'rgba(255,240,180,0)'); c.fillRect(lx - 600, 100, 1200, 900) } c.fillStyle = hgrad(c, 1500, 1800, '#6a6a60', '#4a4a44'); c.fillRect(1500, 520, 300, 400); for (let k = 0; k < 8; k++) ell(c, 1540 + (k % 4) * 70, 560 + Math.floor(k / 4) * 50, 10, 10, 0, k % 3 ? '#c8a24a' : '#8a2a1e') })
    layer(c, cam, 1, c => { c.fillStyle = vgrad(c, 900, 1200, '#3a3a36', '#1a1a18'); c.fillRect(-900, 900, 3800, 600); if (o.inner) o.inner(c) })
  }
  function hangar(c, cam, t, o = {}) {
    layer(c, cam, 0.9, c => { c.fillStyle = vgrad(c, -200, 1000, '#3a3a3c', '#1a1a1c'); c.fillRect(-900, -400, 3800, 1700); for (let x = -800; x < 2900; x += 240) { c.fillStyle = '#2a2a2c'; c.fillRect(x, -400, 40, 1400) } c.fillStyle = '#2a2a2c'; c.fillRect(-900, 100, 3800, 50); for (let x = -700; x < 2900; x += 600) { ell(c, x, 180, 30, 14, 0, '#d8d0a0'); c.fillStyle = rgrad(c, x, 220, 10, 500, 'rgba(255,230,160,0.25)', 'rgba(255,230,160,0)'); c.fillRect(x - 500, 150, 1000, 900) } })
    layer(c, cam, 1, c => { c.fillStyle = vgrad(c, 880, 1200, '#5a5048', '#2a2420'); c.fillRect(-900, 880, 3800, 600); if (o.inner) o.inner(c) })
  }
  function torpedo(c, x, y, s) { c.save(); c.translate(x, y); c.scale(s, s); c.fillStyle = hgrad(c, -120, 120, '#6a6a6a', '#3a3a3a'); c.fillRect(-120, -12, 230, 24); ell(c, 110, 0, 20, 12, 0, '#5a5a5a'); poly(c, [[-120, -12], [-150, -26], [-150, 26], [-120, 12]], '#3a3a3a'); c.restore() }
  function bomb(c, x, y, s) { c.save(); c.translate(x, y); c.scale(s, s); ell(c, 0, 0, 60, 22, 0, '#3a3a36'); poly(c, [[-60, 0], [-90, -24], [-90, 24]], '#2a2a26'); c.fillStyle = '#c8a24a'; c.fillRect(20, -22, 6, 44); c.restore() }
  // a sea chart with the island, Hawaii, and fleets
  function seaChart(c, t, draw) { c.fillStyle = '#14110e'; c.fillRect(0, 0, W, H); PK.map(c, W / 2, H / 2 - 20, 1500, 860, { draw: (c, w, h) => { c.fillStyle = 'rgba(90,120,150,0.22)'; c.fillRect(-w / 2 + 20, -h / 2 + 20, w - 40, h - 40); c.strokeStyle = 'rgba(70,90,110,0.25)'; c.lineWidth = 1.5; for (let x = -700; x < 700; x += 100) { c.beginPath(); c.moveTo(x, -h / 2 + 20); c.lineTo(x, h / 2 - 20); c.stroke() } for (let y = -400; y < 400; y += 100) { c.beginPath(); c.moveTo(-w / 2 + 20, y); c.lineTo(w / 2 - 20, y); c.stroke() } draw(c, w, h) } }) }
  // the top of a cloud deck seen from above it: a soft white floor with rolling puffs along its edge
  function cloudDeck(c, y) { c.fillStyle = vgrad(c, y - 40, y + 400, '#f6f8fa', '#d8dee4', '#b8c4cc'); c.fillRect(-1400, y, 4800, 700); const r = rng(17); for (let k = 0; k < 70; k++) { const x = r() * 4400 - 1200, w = 80 + r() * 160; ell(c, x, y + r() * 30, w, w * 0.45, 0, `rgba(255,255,255,${0.75 + r() * 0.25})`); ell(c, x + w * 0.2, y + 20 + r() * 20, w * 0.7, w * 0.25, 0, 'rgba(190,200,210,0.35)') } }
  const shotOf = (t, list) => { let s = list[0]; for (const L of list) if (t >= L[0]) s = L; const i = list.indexOf(s), t1 = (list[i + 1] || [1e9])[0]; return { name: s[1], t0: s[0], t1, u: clamp((t - s[0]) / (t1 - s[0])) } }
  return { cloudDeck, ocean, carrier, destroyer, battleship, fire, blast, splash, flak, plane, planeTop, carrierTop, basement, hangar, torpedo, bomb, seaChart, shotOf }
})()
window.PRELOAD = () => Promise.all([document.fonts.load('800 40px OldStandard'), document.fonts.load('40px OldStandard')])
