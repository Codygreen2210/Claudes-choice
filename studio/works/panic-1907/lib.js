// lib.js: the drawing kit for the Panic of 1907 film. An engraved-newspaper look:
// paper, ink, hatching, one red and one gold. Everything is a pure function of time.
(function () {
  const { clamp, lerp, EZ, prog, rng, noise, fbm } = K
  const W = 1920, H = 1080
  const C = {
    paper: '#eee2c8', paper2: '#dccba6', paper3: '#c8b48a', ink: '#1a1512', ink2: '#3a302a', ink3: '#6b5d50',
    red: '#93291c', red2: '#b8402e', gold: '#c9973a', gold2: '#f0c868', night: '#10141d', night2: '#1c2333', night3: '#2c3650',
    lamp: '#f6c770', dawn: '#f3d9a4',
  }
  const F = {
    head: (px, w = 800) => `${w} ${px}px Playfair`,
    headI: (px, w = 600) => `italic ${w} ${px}px Playfair`,
    body: px => `${px}px Fell`, bodyI: px => `italic ${px}px Fell`, sc: px => `${px}px FellSC`,
    old: (px, b) => `${b ? 'bold ' : ''}${px}px OldStandard`,
  }

  // ---------- caches ----------
  const cache = {}
  function layer(name, w, h, draw) {
    if (!cache[name]) { const cv = document.createElement('canvas'); cv.width = w; cv.height = h; draw(cv.getContext('2d'), w, h); cache[name] = cv }
    return cache[name]
  }
  // grain: a tile of noise, laid over everything
  function grainTile(seed, dark) {
    return layer('grain' + seed + dark, 512, 512, (c, w, h) => {
      const im = c.createImageData(w, h), r = rng(seed)
      for (let i = 0; i < w * h; i++) {
        const v = r(), f = r() < 0.004 ? 1 : 0
        const a = dark ? (v * 26 + f * 60) : (v * 22 + f * 50)
        const g = dark ? 255 : 30
        im.data[i * 4] = g; im.data[i * 4 + 1] = g * 0.95; im.data[i * 4 + 2] = g * 0.85; im.data[i * 4 + 3] = a
      }
      c.putImageData(im, 0, 0)
    })
  }
  function grain(c, t, dark) {
    const k = Math.floor(t * 12)          // film grain moves on twos-and-a-half; still pictures breathe
    const tile = grainTile(1 + (k % 4), dark)
    c.save(); c.globalAlpha = dark ? 0.36 : 0.5
    const ox = (k * 97) % 512, oy = (k * 57) % 512
    for (let y = -oy; y < H; y += 512) for (let x = -ox; x < W; x += 512) c.drawImage(tile, x, y)
    c.restore()
  }
  function vignette(c, strength = 0.55, col = '0,0,0') {
    const g = c.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 1.05)
    g.addColorStop(0, `rgba(${col},0)`); g.addColorStop(1, `rgba(${col},${strength})`)
    c.fillStyle = g; c.fillRect(0, 0, W, H)
  }
  function paper(c, t, tone = C.paper) {
    c.fillStyle = tone; c.fillRect(0, 0, W, H)
    c.drawImage(layer('fibres', W, H, (x, w, h) => {
      const r = rng(77)
      for (let i = 0; i < 2600; i++) {
        const px = r() * w, py = r() * h, l = 6 + r() * 26, a = r() * Math.PI
        x.strokeStyle = r() < 0.5 ? 'rgba(120,96,60,0.07)' : 'rgba(255,250,235,0.10)'; x.lineWidth = 0.6 + r()
        x.beginPath(); x.moveTo(px, py); x.lineTo(px + Math.cos(a) * l, py + Math.sin(a) * l); x.stroke()
      }
      for (let i = 0; i < 26; i++) {
        const g = x.createRadialGradient(r() * w, r() * h, 0, r() * w, r() * h, 240 + r() * 380)
        g.addColorStop(0, 'rgba(150,120,70,0.07)'); g.addColorStop(1, 'rgba(150,120,70,0)')
        x.fillStyle = g; x.fillRect(0, 0, w, h)
      }
    }), 0, 0)
  }
  function finish(c, t, dark) {
    grain(c, t, dark)
    vignette(c, dark ? 0.62 : 0.3, dark ? '0,0,0' : '70,50,20')
    // a breath of gate flicker
    const fl = 0.018 * noise(t * 9.3, 3)
    c.fillStyle = fl > 0 ? `rgba(255,240,210,${fl})` : `rgba(0,0,0,${-fl})`; c.fillRect(0, 0, W, H)
  }

  // ---------- marks ----------
  // hatch: engraver's parallel lines inside a clip path
  function hatch(c, pathFn, o = {}) {
    const { angle = -0.6, gap = 7, col = C.ink, alpha = 0.35, lw = 1.3, box = [0, 0, W, H], wob = 0 } = o
    c.save(); c.beginPath(); pathFn(c); c.clip()
    c.strokeStyle = col; c.globalAlpha *= alpha; c.lineWidth = lw
    const [bx, by, bw, bh] = box, cx = bx + bw / 2, cy = by + bh / 2, R = Math.hypot(bw, bh) / 2 + 4
    c.translate(cx, cy); c.rotate(angle)
    c.beginPath()
    for (let y = -R; y <= R; y += gap) { c.moveTo(-R, y + wob * Math.sin(y)); c.lineTo(R, y + wob * Math.cos(y * 1.3)) }
    c.stroke(); c.restore()
  }
  const rr = (c, x, y, w, h, r) => { c.beginPath(); c.roundRect(x, y, w, h, r) }
  function text(c, s, x, y, font, col, o = {}) {
    c.save(); c.font = font; c.fillStyle = col; c.textAlign = o.align || 'center'; c.textBaseline = o.base || 'alphabetic'
    if (o.track) c.letterSpacing = o.track + 'px'
    if (o.alpha != null) c.globalAlpha *= o.alpha
    if (o.shadow) { c.shadowColor = o.shadow; c.shadowBlur = o.blur ?? 12 }
    if (o.stroke) { c.lineJoin = 'round'; c.lineWidth = o.sw || 6; c.strokeStyle = o.stroke; c.strokeText(s, x, y) }
    c.fillText(s, x, y); c.restore()
  }
  const tw = (c, s, font, track) => { c.save(); c.font = font; if (track) c.letterSpacing = track + 'px'; const w = c.measureText(s).width; c.restore(); return w }
  // text that sets itself letter by letter, like type going down
  function typeset(c, s, x, y, font, col, p, o = {}) {
    const n = Math.ceil(s.length * clamp(p)); if (n <= 0) return
    const full = tw(c, s, font, o.track)
    const x0 = (o.align || 'center') === 'center' ? x - full / 2 : (o.align === 'right' ? x - full : x)
    text(c, s.slice(0, n), x0, y, font, col, { ...o, align: 'left' })
  }
  // a ruled double line, the newspaper kind
  function rule(c, x0, x1, y, col = C.ink, p = 1) {
    const xm = (x0 + x1) / 2, hw = (x1 - x0) / 2 * EZ.o(clamp(p))
    c.save(); c.strokeStyle = col; c.lineWidth = 3; c.beginPath(); c.moveTo(xm - hw, y); c.lineTo(xm + hw, y); c.stroke()
    c.lineWidth = 1; c.beginPath(); c.moveTo(xm - hw, y + 6); c.lineTo(xm + hw, y + 6); c.stroke(); c.restore()
  }

  // ---------- people ----------
  // A cut-paper figure. (x, y) is where the feet meet the ground; h is height in pixels.
  // o: hat bowler|top|cap|lady|none, walk (phase), stride 0..1, lean (rad), face +1/-1, bulk, col, arm (0..1 raised), cane, chain
  function person(c, x, y, h, o = {}) {
    const s = h / 100, face = o.face || 1, bulk = o.bulk || 1, col = o.col || C.ink
    const ph = o.walk || 0, st = o.stride ?? 0, sw = Math.sin(ph) * 11 * st, bob = -Math.abs(Math.cos(ph)) * 1.6 * st
    c.save(); c.translate(x, y); c.scale(s * face, s); c.fillStyle = col; c.strokeStyle = col
    if (o.lady) {
      c.translate(0, bob); c.rotate(o.lean || 0)
      c.beginPath(); c.moveTo(-9, -80); c.quadraticCurveTo(-13, -60, -7, -56); c.quadraticCurveTo(-20, -20, -19 + sw * 0.2, 0); c.lineTo(19 + sw * 0.2, 0)
      c.quadraticCurveTo(18, -24, 7, -56); c.quadraticCurveTo(13, -62, 9, -80); c.closePath(); c.fill()
      c.beginPath(); c.arc(1, -88, 7, 0, 7); c.fill()
      c.beginPath(); c.ellipse(1, -94, 16, 3.6, -0.08, 0, 7); c.fill()
      c.beginPath(); c.ellipse(0, -97, 8, 5, 0, Math.PI, 0); c.fill()
      c.restore(); return
    }
    // legs
    const leg = (dx, swing) => { c.beginPath(); c.moveTo(dx - 4.5, -46); c.lineTo(dx + 4.5, -46); c.lineTo(dx + swing + 4, 0); c.lineTo(dx + swing + 9, 0); c.lineTo(dx + swing + 9, 2.5); c.lineTo(dx + swing - 3.5, 2.5); c.closePath(); c.fill() }
    if (!o.seated) { leg(-4, sw); leg(4, -sw) }
    else { c.fillRect(-6, -46, 26, 9); c.fillRect(13, -46, 8, 46); c.fillRect(13, -2.5, 14, 2.5) }
    c.translate(0, bob); c.rotate(o.lean || 0)
    // coat
    const b = bulk
    c.beginPath(); c.moveTo(-11 * b, -82); c.quadraticCurveTo(0, -87, 11 * b, -82)
    c.quadraticCurveTo(15 * b + (o.belly || 0), -62, 13 * b + (o.belly || 0) * 0.8, -36); c.lineTo(-14 * b, -36); c.quadraticCurveTo(-15 * b, -62, -11 * b, -82); c.closePath(); c.fill()
    // arm
    const ar = o.arm || 0
    c.save(); c.translate(6 * b, -78); c.rotate(-sw * 0.03 - ar * 2.5 + (o.armRot || 0)); c.beginPath(); c.roundRect(-3.6, 0, 7.2, 34, 3.5); c.fill()
    if (o.hold) o.hold(c)
    c.restore()
    // head + nose
    c.beginPath(); c.arc(1.5, -91, 7.2, 0, 7); c.fill()
    c.beginPath(); c.moveTo(7, -93); c.lineTo(11 + (o.nose || 0), -89.5); c.lineTo(7, -88); c.fill()
    if (o.mous) { c.beginPath(); c.ellipse(8, -86.5, 4.5, 2.2, 0.3, 0, 7); c.fill() }
    // hat
    const hat = o.hat || 'bowler'
    if (hat === 'bowler') { c.beginPath(); c.ellipse(1.5, -96.5, 8, 6.5, 0, Math.PI, 0); c.fill(); c.beginPath(); c.roundRect(-9.5, -97.5, 23, 2.6, 1.3); c.fill() }
    else if (hat === 'top') { c.beginPath(); c.moveTo(-6, -97); c.lineTo(-6.8, -113); c.lineTo(9.8, -113); c.lineTo(9, -97); c.closePath(); c.fill(); c.beginPath(); c.roundRect(-10.5, -98.5, 24, 2.6, 1.3); c.fill() }
    else if (hat === 'cap') { c.beginPath(); c.ellipse(1, -96.5, 8.5, 4.5, 0, Math.PI, 0); c.fill(); c.beginPath(); c.roundRect(3, -97.5, 11, 2.2, 1); c.fill() }
    if (o.cane) { c.save(); c.lineWidth = 2.2; c.lineCap = 'round'; c.beginPath(); c.moveTo(17 * b, -46); c.lineTo(22 * b + sw * 0.3, -bob); c.stroke(); c.restore() }
    if (o.chain) { c.save(); c.strokeStyle = C.gold; c.lineWidth = 1.5; c.beginPath(); c.moveTo(2, -60); c.quadraticCurveTo(9 * b, -50, 13 * b, -59); c.stroke(); c.restore() }
    c.restore()
  }
  const HATS = ['bowler', 'bowler', 'bowler', 'top', 'cap', 'cap', 'bowler']
  // a repeatable crowd: n people with their own gait, size and hat
  function crowd(n, seed, o = {}) {
    const r = rng(seed), out = []
    for (let i = 0; i < n; i++) {
      const lady = r() < (o.ladies ?? 0.2)
      out.push({ i, lady, hat: HATS[Math.floor(r() * HATS.length)], h: (o.h || 150) * (0.9 + r() * 0.2), bulk: 0.9 + r() * 0.35, ph: r() * 6.28, sp: 0.85 + r() * 0.3, jit: r(), jit2: r(), belly: r() < 0.3 ? 3 : 0 })
    }
    return out
  }
  // J. P. Morgan: big man, top hat, cane, the nose, a gold watch chain
  function morgan(c, x, y, h, o = {}) {
    person(c, x, y, h, { hat: o.hat === false ? 'none' : 'top', bulk: 1.5, belly: 6, nose: 2.5, mous: true, cane: o.cane !== false, chain: true, ...o })
  }

  // ---------- buildings ----------
  // A bank front: steps, columns, pediment, a sign. (x, y) is the ground centre.
  function bank(c, x, y, w, h, o = {}) {
    const col = o.col || C.ink, fill = o.fill || C.paper2, n = o.cols || 4, p = o.p ?? 1
    c.save(); c.translate(x, y)
    if (o.dash) { c.setLineDash([10, 9]); c.lineDashOffset = -(o.dashT || 0) * 20 }
    c.lineWidth = o.lw || 3; c.strokeStyle = col; c.lineJoin = 'round'
    const stepH = h * 0.1, ped = h * 0.2, ent = h * 0.09, colH = h - stepH - ped - ent
    const body = q => { q.rect(-w / 2, -h + ped, w, h - ped) }
    if (!o.dash) {
      c.fillStyle = fill; c.beginPath(); c.moveTo(-w / 2 - 8, -h + ped); c.lineTo(0, -h); c.lineTo(w / 2 + 8, -h + ped); c.closePath(); c.fill()
      c.fillRect(-w / 2, -h + ped, w, h - ped)
      hatch(c, q => { q.rect(-w / 2, -stepH - colH, w, colH) }, { gap: 5, alpha: 0.55, angle: Math.PI / 2 - 0.02, box: [-w / 2, -stepH - colH, w, colH], col })
      // dark doorway
      c.fillStyle = col; rr(c, -w * 0.07, -stepH - colH * 0.62, w * 0.14, colH * 0.62, [w * 0.07, w * 0.07, 0, 0]); c.fill()
    }
    // steps
    for (let i = 0; i < 3; i++) { c.beginPath(); c.rect(-w / 2 - 14 + i * 5, -stepH + i * stepH / 3, w + 28 - i * 10, stepH / 3); if (!o.dash) { c.fillStyle = fill; c.fill() } c.stroke() }
    // columns
    const cw = w / (n * 2.6)
    for (let i = 0; i < n; i++) {
      const cx = -w / 2 + (i + 0.5) * w / n
      c.beginPath(); c.rect(cx - cw / 2, -stepH - colH, cw, colH); if (!o.dash) { c.fillStyle = fill; c.fill() } c.stroke()
      c.beginPath(); c.rect(cx - cw * 0.72, -stepH - colH, cw * 1.44, 7); c.rect(cx - cw * 0.72, -stepH - 7, cw * 1.44, 7); if (!o.dash) { c.fillStyle = fill; c.fill() } c.stroke()
      if (!o.dash) { c.save(); c.globalAlpha = 0.5; c.lineWidth = 1; for (let k = 1; k < 4; k++) { c.beginPath(); c.moveTo(cx - cw / 2 + k * cw / 4, -stepH - colH + 9); c.lineTo(cx - cw / 2 + k * cw / 4, -stepH - 9); c.stroke() } c.restore() }
    }
    // entablature + pediment
    c.beginPath(); c.rect(-w / 2 - 6, -stepH - colH - ent, w + 12, ent); if (!o.dash) { c.fillStyle = fill; c.fill() } c.stroke()
    c.beginPath(); c.moveTo(-w / 2 - 12, -h + ped); c.lineTo(0, -h); c.lineTo(w / 2 + 12, -h + ped); c.closePath(); c.stroke()
    c.setLineDash([])
    if (o.sign) text(c, o.sign, 0, -stepH - colH - ent * 0.26, F.sc(Math.min(ent * 0.72, o.signPx || 99)), o.signCol || col, { track: o.track ?? 2 })
    if (o.lit) { c.save(); c.globalCompositeOperation = 'multiply'; c.restore() }
    c.restore()
  }
  // a plain city block for skylines
  function block(c, x, y, w, h, o = {}) {
    c.save(); c.fillStyle = o.fill || C.ink2; c.fillRect(x, y - h, w, h)
    if (o.win) { c.fillStyle = o.win; const r = rng(Math.round(x * 3 + h)); for (let yy = y - h + 12; yy < y - 14; yy += 22) for (let xx = x + 8; xx < x + w - 10; xx += 16) if (r() < (o.dens ?? 0.35)) c.fillRect(xx, yy, 7, 11) }
    c.restore()
  }

  // ---------- things ----------
  function clock(c, x, y, r, hours, o = {}) {   // hours: 2.93 = 2:56
    const col = o.col || C.ink, face = o.face || C.paper
    c.save(); c.translate(x, y)
    c.fillStyle = col; c.beginPath(); c.arc(0, 0, r * 1.12, 0, 7); c.fill()
    if (o.rim) { c.strokeStyle = o.rim; c.lineWidth = r * 0.035; c.beginPath(); c.arc(0, 0, r * 1.06, 0, 7); c.stroke() }
    c.fillStyle = face; c.beginPath(); c.arc(0, 0, r, 0, 7); c.fill()
    const R = ['XII', 'I', 'II', 'III', 'IIII', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI']
    for (let i = 0; i < 60; i++) { const a = i * Math.PI / 30; c.strokeStyle = col; c.lineWidth = i % 5 ? r * 0.008 : r * 0.022; c.beginPath(); c.moveTo(Math.sin(a) * r * 0.93, -Math.cos(a) * r * 0.93); c.lineTo(Math.sin(a) * r * (i % 5 ? 0.89 : 0.86), -Math.cos(a) * r * (i % 5 ? 0.89 : 0.86)); c.stroke() }
    if (!o.plain) for (let i = 0; i < 12; i++) { const a = i * Math.PI / 6; c.save(); c.translate(Math.sin(a) * r * 0.72, -Math.cos(a) * r * 0.72); c.rotate(a); text(c, R[i], 0, r * 0.06, F.old(r * 0.17, true), col); c.restore() }
    const hand = (a, len, wd) => { c.save(); c.rotate(a); c.fillStyle = col; c.beginPath(); c.moveTo(-wd, r * 0.1); c.lineTo(-wd * 0.3, -len); c.lineTo(wd * 0.3, -len); c.lineTo(wd, r * 0.1); c.closePath(); c.fill(); c.restore() }
    hand((hours % 12) / 12 * Math.PI * 2, r * 0.5, r * 0.045)
    hand((hours % 1) * Math.PI * 2, r * 0.8, r * 0.03)
    c.fillStyle = o.pin || C.red; c.beginPath(); c.arc(0, 0, r * 0.05, 0, 7); c.fill()
    c.restore()
  }
  function key(c, x, y, s, rot, col = C.gold) {
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s); c.strokeStyle = col; c.fillStyle = col; c.lineWidth = 7; c.lineCap = 'round'
    c.beginPath(); c.arc(0, 0, 20, 0, 7); c.stroke(); c.beginPath(); c.arc(0, 0, 8, 0, 7); c.stroke()
    c.beginPath(); c.moveTo(22, 0); c.lineTo(96, 0); c.stroke()
    c.fillRect(74, 0, 8, 20); c.fillRect(88, 0, 8, 26); c.fillRect(60, -2, 5, 6)
    c.restore()
  }
  function coin(c, x, y, r, on, col = C.gold) {
    c.save(); c.lineWidth = Math.max(1.5, r * 0.12)
    if (on > 0) { c.globalAlpha *= on; c.fillStyle = col; c.beginPath(); c.arc(x, y, r, 0, 7); c.fill(); c.strokeStyle = C.ink; c.stroke(); c.globalAlpha /= on || 1; c.strokeStyle = 'rgba(26,21,18,0.5)'; c.lineWidth = 1; c.beginPath(); c.arc(x, y, r * 0.66, 0, 7); c.stroke() }
    else { c.strokeStyle = C.ink3; c.globalAlpha *= 0.55; c.setLineDash([3, 4]); c.beginPath(); c.arc(x, y, r, 0, 7); c.stroke() }
    c.restore()
  }
  // a warm pool of light on a dark scene
  function glow(c, x, y, r, col = '246,199,112', a = 0.5) {
    const g = c.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, `rgba(${col},${a})`); g.addColorStop(0.5, `rgba(${col},${a * 0.3})`); g.addColorStop(1, `rgba(${col},0)`)
    c.save(); c.globalCompositeOperation = 'lighter'; c.fillStyle = g; c.fillRect(x - r, y - r, r * 2, r * 2); c.restore()
  }
  const money = n => '$' + Math.round(n).toLocaleString('en-US')

  window.L = { W, H, C, F, layer, grain, vignette, paper, finish, hatch, rr, text, tw, typeset, rule, person, crowd, morgan, bank, block, clock, key, coin, glow, money }
})()
