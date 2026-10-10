// scenesA.js: scenes 1-4. Each scene is draw(c, t, q, S) -> true if the picture is dark.
// t is film time; q('some words') is the film time those words are spoken in this scene.
(function () {
  const { clamp, lerp, EZ, prog, bump, rng, noise, track } = K
  const { W, H, C, F, layer, paper, finish, hatch, rr, text, typeset, rule, person, crowd, morgan, bank, block, clock, key, coin, glow, money, tw } = L
  const cam = (c, cx, cy, s) => { c.translate(W / 2, H / 2); c.scale(s, s); c.translate(-cx, -cy) }

  // ---------- the library, used by scenes 1 and 6 ----------
  const LW = 2700
  const DOOR = { x: 2250, w: 250, top: 330, floor: 900 }
  function libraryBG() {
    return layer('library', LW, H, (c) => {
      const r = rng(1907)
      c.fillStyle = '#2b1d15'; c.fillRect(0, 0, LW, H)
      // three tiers of books
      const cols = ['#4a2a1a', '#5a2219', '#33302a', '#5c4322', '#27312f', '#632d1d', '#3d2a20', '#4d3a2a']
      for (const [y0, y1] of [[70, 250], [290, 470], [510, 690]]) {
        c.fillStyle = '#120c09'; c.fillRect(0, y0 - 8, LW, y1 - y0 + 16)
        let x = 10
        while (x < LW - 10) {
          if (x > 660 && x < 1040 && y0 > 400) { x = 1040; continue }           // fireplace
          if (x > DOOR.x - 60 && x < DOOR.x + DOOR.w + 60 && y0 > 250) { x = DOOR.x + DOOR.w + 60; continue }
          const bw = 11 + r() * 15, bh = (y1 - y0) * (0.72 + r() * 0.26), tilt = r() < 0.04 ? 0.12 : 0
          c.save(); c.translate(x, y1); c.rotate(tilt); c.fillStyle = cols[Math.floor(r() * cols.length)]; c.fillRect(0, -bh, bw - 1.5, bh)
          if (r() < 0.45) { c.fillStyle = 'rgba(201,151,58,0.5)'; c.fillRect(1, -bh * 0.8, bw - 3.5, 2); c.fillRect(1, -bh * 0.25, bw - 3.5, 2) }
          c.restore(); x += bw + (r() < 0.03 ? 22 : 0)
        }
        c.fillStyle = '#3a2416'; c.fillRect(0, y1, LW, 12)
        for (let px = 0; px < LW; px += 330) { c.fillStyle = '#3a2416'; c.fillRect(px, y0 - 12, 16, y1 - y0 + 24) }
      }
      // gallery rail
      c.strokeStyle = 'rgba(201,151,58,0.35)'; c.lineWidth = 3; c.beginPath(); c.moveTo(0, 268); c.lineTo(LW, 268); c.stroke()
      // fireplace
      c.fillStyle = '#35281f'; c.fillRect(650, 420, 400, 480); c.fillStyle = '#44352a'; c.fillRect(630, 400, 440, 34)
      c.fillStyle = '#0a0706'; rr(c, 720, 500, 260, 400, [120, 120, 0, 0]); c.fill()
      hatch(c, q => q.rect(650, 434, 400, 466), { gap: 6, alpha: 0.35, col: '#1a120d', box: [650, 434, 400, 466] })
      // the door
      c.fillStyle = '#1a110b'; c.fillRect(DOOR.x - 26, DOOR.top - 26, DOOR.w + 52, DOOR.floor - DOOR.top + 26)
      c.fillStyle = '#4a2f1c'; c.fillRect(DOOR.x, DOOR.top, DOOR.w, DOOR.floor - DOOR.top)
      c.strokeStyle = '#2a190e'; c.lineWidth = 5
      for (const [px, py, pw, ph] of [[26, 30, 86, 200], [138, 30, 86, 200], [26, 258, 86, 280], [138, 258, 86, 280]]) c.strokeRect(DOOR.x + px, DOOR.top + py, pw, ph)
      c.beginPath(); c.moveTo(DOOR.x + DOOR.w / 2, DOOR.top); c.lineTo(DOOR.x + DOOR.w / 2, DOOR.floor); c.stroke()
      hatch(c, q => q.rect(DOOR.x, DOOR.top, DOOR.w, 570), { gap: 5, alpha: 0.22, angle: Math.PI / 2, col: '#1a0f08', box: [DOOR.x, DOOR.top, DOOR.w, 570] })
      // floor and rug
      c.fillStyle = '#1b120d'; c.fillRect(0, 900, LW, 180)
      c.fillStyle = '#4d1a14'; c.beginPath(); c.moveTo(260, 940); c.lineTo(2050, 940); c.lineTo(2200, 1080); c.lineTo(110, 1080); c.closePath(); c.fill()
      hatch(c, q => { q.moveTo(260, 940); q.lineTo(2050, 940); q.lineTo(2200, 1080); q.lineTo(110, 1080); q.closePath() }, { gap: 9, alpha: 0.3, col: '#c9973a', angle: 0.5, box: [110, 940, 2100, 140] })
      // dark falls off toward the ceiling
      const g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, 'rgba(5,4,6,0.62)'); g.addColorStop(0.5, 'rgba(5,4,6,0.10)'); g.addColorStop(1, 'rgba(5,4,6,0.30)')
      c.fillStyle = g; c.fillRect(0, 0, LW, H)
    })
  }
  const BANKERS = (() => {
    const r = rng(33), out = []
    for (let i = 0; i < 46; i++) {
      const row = i % 3
      out.push({ x: 120 + (i / 46) * 1960 + (r() - 0.5) * 70, y: 935 + row * 52 + r() * 14, h: 300 + row * 46 + r() * 30, hat: r() < 0.55 ? 'none' : (r() < 0.5 ? 'top' : 'bowler'), bulk: 0.95 + r() * 0.45, face: r() < 0.5 ? 1 : -1, ph: r() * 6.28, sp: 0.25 + r() * 0.3, seated: row === 0 && r() < 0.45, belly: r() < 0.4 ? 4 : 0, mous: r() < 0.5 })
    }
    return out.sort((a, b) => a.y - b.y)
  })()
  function fire(c, t, k = 1) {
    const r = rng(5)
    for (let i = 0; i < 9; i++) {
      const fx = 770 + i * 20 + r() * 8, fh = (150 + r() * 170) * k * (0.75 + 0.25 * noise(t * 3.1 + i * 7, i)), sway = noise(t * 2.3 + i, 9) * 14
      c.fillStyle = i % 2 ? 'rgba(246,160,60,0.9)' : 'rgba(250,205,110,0.9)'
      c.beginPath(); c.moveTo(fx - 16, 900); c.quadraticCurveTo(fx - 10 + sway, 900 - fh * 0.6, fx + sway, 900 - fh); c.quadraticCurveTo(fx + 12 + sway * 0.4, 900 - fh * 0.5, fx + 16, 900); c.closePath(); c.fill()
    }
  }
  // the library as one picture: camX is the left edge of the view in library coordinates
  function library(c, t, camX, o = {}) {
    const fl = 0.8 + 0.2 * noise(t * 5.2, 1), k = o.fire ?? 1
    c.save(); c.translate(-camX, 0)
    c.drawImage(libraryBG(), 0, 0)
    fire(c, t, k)
    glow(c, 850, 760, 1000, '246,170,80', 0.58 * fl * k)
    glow(c, 1700, 300, 700, '246,199,112', 0.30)
    glow(c, 330, 300, 620, '246,199,112', 0.24)
    glow(c, 2380, 420, 520, '246,199,112', 0.22)
    if (o.behind) o.behind(c)
    for (const b of BANKERS) {
      if (o.skip && o.skip(b)) continue
      const sway = 0.035 * Math.sin(t * b.sp + b.ph) + (o.slump || 0) * (b.face * 0.05)
      const bx = b.x + (o.dx ? o.dx(b) : 0), dir = Math.sign(850 - bx) || 1, near = clamp(1 - Math.abs(bx - 850) / 1100)
      person(c, bx + dir * 4, b.y - 2, b.h, { ...b, lean: sway, col: `rgba(246,${150 + 40 * near},${70 + 30 * near},${(0.16 + 0.5 * near) * fl * (0.4 + 0.6 * k)})` })
      person(c, bx, b.y, b.h, { ...b, lean: sway, col: '#0b0807', walk: o.walk ? o.walk(b) : 0, stride: o.stride ? o.stride(b) : 0 })
    }
    if (o.front) o.front(c)
    c.restore()
  }

  // =============================== 1. the locked door ===============================
  function s1(c, t, q, S) {
    const qSun = q('a sunday'), qLib = q('in a private library') - 0.35, qHund = q('more than a hundred'), qDoor = q('and the door'), qLocked = q('locked'), qMan = q('the man who owns') - 0.3, qKey = q('has the key'), qNob = q('and nobodys'), qSave = q('until they save')
    if (t < qLib + 0.5) {
      // the clock
      const g = c.createLinearGradient(0, 0, W, H); g.addColorStop(0, '#231710'); g.addColorStop(1, '#0c0908'); c.fillStyle = g; c.fillRect(0, 0, W, H)
      const z = 1 + 0.07 * prog(t, 0, qLib + 0.5, 'sine')
      c.save(); cam(c, 960, 540, z); c.translate(170, 20)
      glow(c, 1260, 480, 760, '246,190,100', 0.34 + 0.03 * noise(t * 5, 2))
      // case
      c.fillStyle = '#0b0807'; rr(c, 900, 150, 720, 860, [360, 360, 14, 14]); c.fill()
      c.strokeStyle = 'rgba(201,151,58,0.6)'; c.lineWidth = 4; rr(c, 922, 172, 676, 816, [338, 338, 8, 8]); c.stroke()
      c.fillStyle = '#0b0807'; c.fillRect(840, 1000, 840, 80)
      const hrs = 2 + (55.4 + t / 60 * 1.0) / 60
      clock(c, 1260, 500, 270, hrs, { col: '#15100d', face: '#e9dcc0', rim: C.gold, pin: C.red })
      // pendulum: one swing a second
      const a = 0.2 * Math.sin(Math.PI * t)
      c.save(); c.translate(1260, 800); c.rotate(a); c.strokeStyle = C.gold; c.lineWidth = 5; c.beginPath(); c.moveTo(0, 0); c.lineTo(0, 150); c.stroke(); c.fillStyle = C.gold; c.beginPath(); c.arc(0, 165, 30, 0, 7); c.fill(); c.strokeStyle = '#7a5a1c'; c.lineWidth = 2; c.beginPath(); c.arc(0, 165, 20, 0, 7); c.stroke(); c.restore()
      c.restore()
      // dateline
      const a0 = S.start - 0.2
      text(c, 'NEW YORK CITY', 150, 430, F.sc(34), C.gold, { align: 'left', track: 8, alpha: prog(t, a0, a0 + 0.8) })
      rule(c, 150, 700, 452, C.paper3, prog(t, a0 + 0.2, a0 + 1.2))
      typeset(c, 'Almost three', 150, 560, F.head(96, 800), C.paper, prog(t, a0 + 0.2, a0 + 1.1), { align: 'left' })
      typeset(c, 'in the morning.', 150, 660, F.head(96, 800), C.paper, prog(t, a0 + 0.9, a0 + 1.9), { align: 'left' })
      typeset(c, 'Sunday, November 3, 1907', 152, 740, F.bodyI(46), C.paper2, prog(t, qSun, qSun + 1.3), { align: 'left' })
      if (t > qLib) { c.fillStyle = `rgba(8,6,6,${prog(t, qLib, qLib + 0.5)})`; c.fillRect(0, 0, W, H) }
    } else if (t < qMan + 0.25) {
      // the room, panning toward the door
      const camX = track(t, [[qLib, 60], [qDoor - 0.2, 1080, 'sine'], [qLocked + 0.4, LW - W - 120, 'io'], [qMan + 1, LW - W - 90, 'l']])
      const jig = bump(t, qLocked - 0.05, 0.22) + bump(t, qLocked + 0.28, 0.22) + bump(t, qLocked + 0.62, 0.2)
      library(c, t, camX, {
        slump: 1,
        front: (c) => {
          // the man trying the handle
          const hx = DOOR.x + DOOR.w / 2 - 22, hy = 640
          person(c, DOOR.x - 20 + jig * 3, 915, 360, { hat: 'bowler', col: '#0b0807', face: 1, arm: 0.36 + jig * 0.03, bulk: 1.1 })
          c.save(); c.translate(hx, hy); c.rotate(jig * 0.45); c.fillStyle = C.gold; rr(c, -30, -6, 38, 12, 6); c.fill(); c.beginPath(); c.arc(0, 0, 11, 0, 7); c.fill(); c.restore()
          c.fillStyle = '#0a0705'; c.beginPath(); c.arc(hx, hy + 40, 6, 0, 7); c.fill(); c.fillRect(hx - 3, hy + 40, 6, 16)
          if (jig > 0.05) { c.strokeStyle = `rgba(240,200,104,${jig * 0.8})`; c.lineWidth = 3; for (const a of [-0.9, -0.3, 0.3]) { c.beginPath(); c.moveTo(hx + Math.cos(a) * 26, hy - 20 + Math.sin(a) * 26); c.lineTo(hx + Math.cos(a) * 44, hy - 20 + Math.sin(a) * 44); c.stroke() } }
        },
      })
      text(c, 'about 120 bankers and trust men', 120, 150, F.bodyI(40), C.paper2, { align: 'left', alpha: prog(t, qHund, qHund + 0.6) * (1 - prog(t, qDoor - 0.6, qDoor)), shadow: '#000' })
      const lk = prog(t, qLocked, qLocked + 0.25) * (1 - prog(t, qMan - 0.3, qMan + 0.1))
      if (lk > 0) text(c, 'LOCKED.', 1180, 250, F.head(120, 900), C.paper, { alpha: lk, track: 10, shadow: '#000', blur: 30 })
      c.fillStyle = `rgba(8,6,6,${1 - prog(t, qLib + 0.5, qLib + 1.1) + prog(t, qMan - 0.1, qMan + 0.25)})`; c.fillRect(0, 0, W, H)
    } else if (t < qNob + 0.9) {
      // the key going into the pocket
      c.fillStyle = '#1c130e'; c.fillRect(0, 0, W, H)
      const z = 1.02 + 0.06 * prog(t, qMan, qNob + 0.9, 'sine')
      c.save(); cam(c, W / 2, H / 2 + 20, z)
      // a waistcoat, filling the frame: pinstripe, buttons, the watch chain
      hatch(c, k => k.rect(-100, -100, W + 200, H + 200), { gap: 26, alpha: 0.5, angle: Math.PI / 2 + 0.03, col: '#3a2a1f', lw: 2, box: [-100, -100, W + 200, H + 200] })
      glow(c, 1500, 300, 1100, '246,170,80', 0.20 + 0.02 * noise(t * 5, 3))
      c.strokeStyle = '#0c0807'; c.lineWidth = 10; c.beginPath(); c.moveTo(560, -50); c.quadraticCurveTo(520, 540, 590, 1150); c.stroke()
      for (let i = 0; i < 4; i++) { const by = 110 + i * 300, bx = 545 + Math.sin(i) * 6; c.fillStyle = '#0c0807'; c.beginPath(); c.arc(bx, by, 30, 0, 7); c.fill(); c.fillStyle = '#4a382b'; c.beginPath(); c.arc(bx, by, 24, 0, 7); c.fill(); c.fillStyle = '#0c0807'; for (const [ox, oy] of [[-7, -7], [7, -7], [-7, 7], [7, 7]]) { c.beginPath(); c.arc(bx + ox, by + oy, 3.4, 0, 7); c.fill() } }
      c.strokeStyle = C.gold; c.lineWidth = 9; c.lineCap = 'round'; c.beginPath(); c.moveTo(548, 410); c.quadraticCurveTo(700, 690 + 8 * Math.sin(t * 2), 880, 648); c.stroke()
      c.strokeStyle = 'rgba(240,200,104,0.5)'; c.lineWidth = 3; c.beginPath(); c.moveTo(548, 404); c.quadraticCurveTo(700, 682 + 8 * Math.sin(t * 2), 880, 642); c.stroke()
      // key and hand come down; the pocket's front lip is drawn over them
      const py = 640, kp = prog(t, qKey - 0.3, qKey + 1.5, 'io')
      const ky = lerp(120, 610, kp), kx = 1090 + 14 * Math.sin(kp * 3)
      c.save(); c.beginPath(); c.rect(0, -200, W, py + 200); c.clip()
      key(c, kx, ky, 2.5, Math.PI / 2 + 0.05 * Math.sin(t * 2.4), C.gold2)
      // thumb and finger pinching the bow, cuff and sleeve running off the top
      c.save(); c.translate(kx, ky); c.rotate(0.16)
      c.fillStyle = '#0c0807'; rr(c, -120, -760, 250, 560, 40); c.fill()
      c.fillStyle = '#eadfc6'; c.fillRect(-126, -230, 262, 46)
      c.fillStyle = '#b08a68'; rr(c, -96, -190, 200, 150, 50); c.fill(); rr(c, -70, -70, 56, 92, 26); c.fill(); rr(c, 20, -76, 60, 104, 28); c.fill()
      c.restore()
      c.restore()
      // pocket
      c.fillStyle = '#120c09'; c.beginPath(); c.moveTo(880, py - 8); c.quadraticCurveTo(1100, py + 26, 1330, py - 14); c.lineTo(1330, py + 16); c.quadraticCurveTo(1100, py + 56, 880, py + 22); c.closePath(); c.fill()
      c.strokeStyle = '#5a4434'; c.lineWidth = 5; c.beginPath(); c.moveTo(880, py + 22); c.quadraticCurveTo(1100, py + 56, 1330, py + 16); c.stroke()
      const gl = bump(t, qKey + 0.2, 0.8)
      if (gl > 0) glow(c, kx, ky + 120, 320, '255,230,160', 0.55 * gl)
      c.restore()
      c.fillStyle = `rgba(8,6,6,${clamp(1 - prog(t, qMan + 0.25, qMan + 0.7) + prog(t, qNob + 0.5, qNob + 0.9))})`; c.fillRect(0, 0, W, H)
    } else {
      // title
      c.fillStyle = '#0e0b0a'; c.fillRect(0, 0, W, H)
      const a = qNob + 0.9, z = 1 + 0.035 * prog(t, a, S.end + 1, 'l')
      glow(c, W / 2, 500, 900, '147,41,28', 0.16)
      c.save(); cam(c, W / 2, H / 2, z)
      key(c, W / 2 - 62, 250, 1.05, 0, C.gold); c.globalAlpha = 1
      rule(c, 420, 1500, 350, C.paper3, prog(t, a, a + 0.9))
      text(c, 'THE PANIC', W / 2, 520, F.head(170, 900), C.paper, { track: 14, alpha: prog(t, a + 0.1, a + 0.7) })
      text(c, 'OF 1907', W / 2, 690, F.head(170, 900), C.red2, { track: 14, alpha: prog(t, a + 0.5, a + 1.1) })
      rule(c, 420, 1500, 760, C.paper3, prog(t, a + 0.4, a + 1.3))
      typeset(c, 'The night one man locked the bankers in', W / 2, 850, F.bodyI(54), C.paper2, prog(t, qSave - 0.3, qSave + 1.4))
      c.restore()
      c.fillStyle = `rgba(8,6,6,${1 - prog(t, a, a + 0.4)})`; c.fillRect(0, 0, W, H)
    }
    finish(c, t, true); return true
  }

  // =============================== 2. no central bank ===============================
  const WALK2 = crowd(9, 21, { h: 150 })
  const STREET = [{ x: 250, sign: 'FIRST NATIONAL' }, { x: 610, sign: 'MERCHANTS BANK' }, { x: 1310, sign: 'FARMERS BANK' }, { x: 1670, sign: 'SAVINGS BANK' }]
  function street(c, t, o = {}) {
    const gy = 770
    // far skyline
    c.save(); c.globalAlpha = 0.22
    const r = rng(8); for (let x = -40; x < W; x += 90 + r() * 60) block(c, x, gy, 70 + r() * 70, 180 + r() * 330, { fill: C.ink3 })
    c.restore()
    for (const b of STREET) bank(c, b.x, gy, 290, 330, { sign: b.sign, signPx: 22, cols: 4 })
    c.strokeStyle = C.ink; c.lineWidth = 4; c.beginPath(); c.moveTo(0, gy); c.lineTo(W, gy); c.stroke()
    hatch(c, q => q.rect(0, gy + 2, W, 150), { gap: 8, alpha: 0.22, angle: 0.03, box: [0, gy, W, 150] })
    if (o.mid) o.mid(c, gy)
    for (const p of WALK2) {
      const dir = p.i % 2 ? 1 : -1, sp = 46 * p.sp, span = W + 300
      const x = ((p.jit * span + dir * t * sp) % span + span) % span - 150
      person(c, x, gy + 40 + p.jit2 * 70, p.h * 1.0, { hat: p.hat, lady: p.lady, walk: t * 5.2 * p.sp + p.ph, stride: 1, face: dir, bulk: p.bulk })
    }
  }
  function coinPanel(c, x, y, title, n, pFill, big, sub, a) {
    c.save(); c.globalAlpha = a
    c.fillStyle = C.paper; c.strokeStyle = C.ink; c.lineWidth = 4; rr(c, x - 330, y - 330, 660, 760, 6); c.fill(); c.stroke()
    c.lineWidth = 1.5; rr(c, x - 318, y - 318, 636, 736, 3); c.stroke()
    text(c, title, x, y - 262, F.sc(44), C.ink, { track: 4 })
    rule(c, x - 250, x + 250, y - 240, C.ink)
    for (let i = 0; i < 100; i++) {
      const gx = x - 207 + (i % 10) * 46, gy = y - 190 + Math.floor(i / 10) * 46
      const on = i < n ? clamp(pFill * n - i) : 0
      coin(c, gx, gy, 17, on)
    }
    text(c, big, x, y + 370, F.head(110, 900), C.red, { alpha: clamp(pFill * 1.5 - 0.5) })
    text(c, sub, x, y + 414, F.bodyI(30), C.ink2)
    c.restore()
  }
  function s2(c, t, q, S) {
    const qNoFed = q('there was no federal'), qNone = q('no central bank'), qShort = q('if a bank ran'), qCall = q('nobody to call'), qTrust = q('and a newer kind') - 0.25, qNat = q('a regular national') - 0.3, qQuarter = q('about a quarter'), qTrusts = q('the trusts'), qNick = q('about a nickel')
    paper(c, t)
    if (t < qNat + 0.4) {
      const z = track(t, [[S.vis, 1.0], [qNoFed, 1.05, 'sine'], [qNone + 1.2, 1.16, 'io'], [qShort, 1.16, 'l'], [qCall + 1, 1.2, 'io'], [qTrust, 1.2, 'l'], [qTrust + 1.2, 1.9, 'io'], [qNat + 0.4, 2.0, 'l']])
      const cx = track(t, [[S.vis, 960], [qNone + 1.2, 960, 'io'], [qShort + 0.6, 800, 'io'], [qTrust, 800, 'l'], [qTrust + 1.2, 1310, 'io'], [qNat + 0.4, 1310, 'l']])
      const cy = track(t, [[S.vis, 520], [qTrust, 540, 'l'], [qTrust + 1.2, 610, 'io'], [qNat + 0.4, 610, 'l']])
      c.save(); cam(c, cx, cy, z)
      text(c, 'AMERICA, 1907', 960, 150, F.sc(46), C.ink, { track: 12, alpha: 1 - prog(t, qNone, qNone + 1) })
      rule(c, 720, 1200, 172, C.ink, prog(t, S.vis + 0.2, S.vis + 1.2) * (1 - prog(t, qNone, qNone + 1)))
      street(c, t, {
        mid: (c, gy) => {
          // the lot where a central bank would stand
          const a = prog(t, qNoFed - 0.2, qNoFed + 0.6)
          if (a > 0) {
            c.save(); c.globalAlpha = a
            bank(c, 960, gy, 330, 420, { dash: true, dashT: t, cols: 6, col: C.ink2 })
            text(c, 'FEDERAL RESERVE', 960, gy - 450, F.sc(34), C.ink2, { track: 4 })
            c.restore()
          }
          const st = prog(t, qNone + 0.15, qNone + 0.4, 'o5')
          if (st > 0) {
            c.save(); c.translate(960, gy - 190); c.rotate(-0.13); c.scale(2.2 - 1.2 * st, 2.2 - 1.2 * st); c.globalAlpha = st * 0.92
            c.strokeStyle = C.red; c.lineWidth = 7; rr(c, -215, -62, 430, 124, 8); c.stroke(); c.lineWidth = 2; rr(c, -202, -49, 404, 98, 4); c.stroke()
            text(c, 'DID NOT EXIST', 0, 24, F.head(52, 900), C.red, { track: 4 }); c.restore()
          }
          // a bank running short
          const drain = prog(t, qShort + 0.2, qCall)
          const ca = prog(t, qShort - 0.1, qShort + 0.3) * (1 - prog(t, qTrust - 0.4, qTrust))
          if (ca > 0) {
            c.save(); c.globalAlpha = ca
            text(c, 'CASH', 610, gy - 440, F.sc(26), C.ink, { track: 5 })
            for (let i = 0; i < 8; i++) coin(c, 610 - 133 + i * 38, gy - 400, 15, clamp((1 - drain) * 8 - (7 - i)))
            // the wire that goes nowhere
            const wp = prog(t, qCall - 0.5, qCall + 0.5, 'o')
            if (wp > 0) {
              const ex = lerp(700, 850, wp), sw = Math.sin(t * 2.6) * 10 * prog(t, qCall + 0.4, qCall + 0.8)
              c.strokeStyle = C.red; c.lineWidth = 3.5; c.beginPath(); c.moveTo(700, gy - 300); c.quadraticCurveTo(780, gy - 330, ex, gy - 300); if (wp >= 1) c.quadraticCurveTo(ex + 22, gy - 280, ex + 8 + sw, gy - 236); c.stroke()
              text(c, '?', ex + 40, gy - 318, F.head(64, 900), C.red, { alpha: prog(t, qCall + 0.3, qCall + 0.6) })
            }
            c.restore()
          }
          // the trust company steps forward
          const ta = prog(t, qTrust, qTrust + 0.8)
          if (ta > 0) { c.save(); c.globalAlpha = ta; c.fillStyle = C.paper; c.fillRect(1175, gy - 262, 270, 34); text(c, 'TRUST COMPANY', 1310, gy - 236, F.sc(27), C.red, { track: 3 }); c.strokeStyle = C.red; c.lineWidth = 4; c.setLineDash([]); c.strokeRect(1150, gy - 348, 320, 352); c.restore() }
        },
      })
      c.restore()
      if (t > qNat) { c.fillStyle = C.paper; c.globalAlpha = prog(t, qNat, qNat + 0.4); c.fillRect(0, 0, W, H); c.globalAlpha = 1 }
    }
    if (t >= qNat) {
      const a = prog(t, qNat + 0.2, qNat + 0.8), z = 1 + 0.03 * prog(t, qNat, S.end + 1, 'l')
      c.save(); cam(c, W / 2, H / 2 + 6, z)
      text(c, 'Cash kept on hand for every dollar deposited', W / 2, 96, F.bodyI(44), C.ink, { alpha: a })
      coinPanel(c, 560, 520, 'NATIONAL BANK', 25, prog(t, qQuarter - 0.5, qQuarter + 1.3, 'o'), 'about 25¢', '', a)
      const b = prog(t, qTrusts - 0.3, qTrusts + 0.3)
      coinPanel(c, 1360, 520, 'TRUST COMPANY', 5, prog(t, qNick - 0.1, qNick + 0.5, 'o'), 'about 5¢', '', a * b)
      c.restore()
    }
    finish(c, t, false); return false
  }

  // =============================== 3. the copper corner ===============================
  const PX = { x0: 620, x1: 1700, y0: 860, top: 300 }, py = v => PX.y0 - v * (PX.y0 - PX.top) / 65
  const PATH = (() => {
    // Monday 39 -> 52, Tuesday up to nearly 60 then 30 at the close, Wednesday 10
    const keys = [[0, 39], [0.30, 52], [0.33, 52.5], [0.50, 59.5], [0.64, 30], [0.67, 29], [1, 10]]
    const pts = [], r = rng(60)
    for (let i = 0; i <= 240; i++) {
      const u = i / 240; let v = keys[keys.length - 1][1]
      for (let k = 0; k < keys.length - 1; k++) if (u <= keys[k + 1][0]) { const p = (u - keys[k][0]) / (keys[k + 1][0] - keys[k][0]); v = lerp(keys[k][1], keys[k + 1][1], p); break }
      const near = Math.min(...keys.map(k => Math.abs(k[0] - u)))
      pts.push([lerp(PX.x0, PX.x1, u), py(v + (r() - 0.5) * 2.6 * clamp(near * 30))])
    }
    return pts
  })()
  const BANKS3 = [0, 1, 2, 3]
  function s3(c, t, q, S) {
    const qBro = q('two brothers'), qMon = q('on monday'), q52 = q('to 52'), qTue = q('on tuesday'), q60 = q('almost 60'), q30 = q('closed at 30'), qWed = q('by wednesday'), q10 = q('it was 10'), qDead = q('the scheme was dead') - 0.2, qWhich = q('which banks')
    paper(c, t)
    // how far along the line we are
    const u = track(t, [[qMon - 0.2, 0], [q52 + 0.5, 0.31, 'io'], [qTue, 0.33, 'l'], [q60 + 0.4, 0.5, 'o'], [q30 - 0.15, 0.5, 'l'], [q30 + 0.55, 0.65, 'i'], [qWed, 0.67, 'l'], [q10 + 0.5, 1, 'io']])
    const shrink = prog(t, qDead, qDead + 1.1, 'io')
    const z = lerp(1 + 0.03 * prog(t, S.vis, qDead, 'l'), 0.6, shrink)
    c.save(); cam(c, lerp(W / 2, 1640, shrink), lerp(H / 2, 520, shrink), z)
    // masthead
    const ha = prog(t, S.vis + 0.2, S.vis + 0.9) * (1 - shrink)
    text(c, 'UNITED COPPER', 1160, 150, F.head(84, 900), C.ink, { track: 8, alpha: ha })
    text(c, 'price of one share, October 1907', 1160, 205, F.bodyI(38), C.ink2, { alpha: ha })
    // axes
    const aa = prog(t, qBro, qBro + 0.8)
    c.save(); c.globalAlpha = aa
    c.strokeStyle = C.ink; c.lineWidth = 4; c.beginPath(); c.moveTo(PX.x0, PX.top - 10); c.lineTo(PX.x0, PX.y0); c.lineTo(PX.x1 + 20, PX.y0); c.stroke()
    for (const v of [10, 20, 30, 40, 50, 60]) { c.strokeStyle = 'rgba(26,21,18,0.16)'; c.lineWidth = 1.5; c.beginPath(); c.moveTo(PX.x0, py(v)); c.lineTo(PX.x1 + 20, py(v)); c.stroke(); text(c, '$' + v, PX.x0 - 18, py(v) + 11, F.old(30), C.ink2, { align: 'right' }) }
    const days = [['MONDAY', 'Oct. 14', 0, 0.33], ['TUESDAY', 'Oct. 15', 0.33, 0.67], ['WEDNESDAY', 'Oct. 16', 0.67, 1]]
    for (const [d, dt, a, b] of days) {
      const xa = lerp(PX.x0, PX.x1, a), xb = lerp(PX.x0, PX.x1, b), on = u >= a - 0.001 ? 1 : 0.3
      if (a > 0) { c.strokeStyle = 'rgba(26,21,18,0.4)'; c.setLineDash([6, 8]); c.lineWidth = 2; c.beginPath(); c.moveTo(xa, PX.top); c.lineTo(xa, PX.y0); c.stroke(); c.setLineDash([]) }
      text(c, d, (xa + xb) / 2, PX.y0 + 50, F.sc(32), C.ink, { track: 4, alpha: on }); text(c, dt, (xa + xb) / 2, PX.y0 + 88, F.bodyI(28), C.ink2, { alpha: on })
    }
    c.restore()
    // the line
    const n = Math.floor(u * 240)
    if (n > 0) {
      c.strokeStyle = C.red; c.lineWidth = 6; c.lineJoin = 'round'; c.lineCap = 'round'; c.beginPath(); c.moveTo(PATH[0][0], PATH[0][1])
      for (let i = 1; i <= n; i++) c.lineTo(PATH[i][0], PATH[i][1]); c.stroke()
      const [hx, hy] = PATH[n]; c.fillStyle = C.red; c.beginPath(); c.arc(hx, hy, 11 + 3 * Math.sin(t * 9), 0, 7); c.fill()
      hatch(c, k => { k.moveTo(PATH[0][0], PX.y0); for (let i = 0; i <= n; i++) k.lineTo(PATH[i][0], PATH[i][1]); k.lineTo(hx, PX.y0); k.closePath() }, { gap: 9, alpha: 0.22, col: C.red, angle: -0.8, box: [PX.x0, PX.top, PX.x1 - PX.x0, PX.y0 - PX.top] })
    }
    const tag = (uu, v, s, at, dx, dy) => { const p = prog(t, at, at + 0.25, 'back'); if (p <= 0) return; const x = lerp(PX.x0, PX.x1, uu) + dx, y = py(v) + dy; c.save(); c.translate(x, y); c.scale(p, p); c.fillStyle = C.ink; const w = tw(c, s, F.head(44, 800)) + 36; rr(c, -w / 2, -40, w, 58, 6); c.fill(); text(c, s, 0, 4, F.head(44, 800), C.paper); c.restore() }
    tag(0, 39, '$39', qMon + 0.4, 70, -52); tag(0.31, 52, '$52', q52 + 0.3, -10, -52); tag(0.5, 59.5, 'nearly $60', q60 + 0.3, 0, -54); tag(0.65, 30, '$30', q30 + 0.5, 78, 6); tag(1, 10, '$10', q10 + 0.5, -40, -56)
    // the brothers, riding it up and coming down with it
    const mood = track(t, [[qBro, 0], [q52, 0.6, 'io'], [q60, 1, 'io'], [q30, -0.5, 'i'], [q10 + 0.6, -1, 'io']])
    const ba = prog(t, qBro - 0.2, qBro + 0.5)
    c.save(); c.globalAlpha = ba
    for (const [bx, k, hh] of [[250, 0, 350], [420, 1, 330]]) {
      const hop = Math.max(0, mood) * Math.abs(Math.sin(t * 6 + k * 1.5)) * 16
      person(c, bx, PX.y0 - hop, hh, { hat: mood < -0.3 ? 'none' : 'top', arm: Math.max(0, mood) * 0.55, lean: mood < 0 ? -mood * 0.16 * (k ? 1 : 0.7) : 0, mous: true, bulk: 1.15, cane: k === 0 })
      if (mood < -0.3) { const f = prog(t, q30, q30 + 1.2, 'i'); c.save(); c.translate(bx + 30 + f * 90, PX.y0 - hh * 1.08 + f * f * hh * 1.05); c.rotate(f * 2.2); c.fillStyle = C.ink; c.fillRect(-22, -34, 44, 34); c.fillRect(-32, -2, 64, 7); c.restore() }
    }
    text(c, 'the Heinze brothers', 335, PX.y0 + 60, F.bodyI(34), C.ink2)
    c.restore()
    c.strokeStyle = C.ink; c.lineWidth = 4; c.beginPath(); c.moveTo(80, PX.y0); c.lineTo(PX.x0, PX.y0); c.stroke()
    // which banks were tied to them
    if (shrink > 0) {
      const gy = PX.y0
      c.save(); c.globalAlpha = shrink
      c.strokeStyle = C.ink; c.lineWidth = 4; c.beginPath(); c.moveTo(PX.x1, gy); c.lineTo(3400, gy); c.stroke()
      BANKS3.forEach((k, i) => {
        const bx = 2000 + i * 345
        bank(c, bx, gy, 300, 370, { cols: 4, sign: 'BANK', signPx: 26 })
        const tp = prog(t, qWhich - 0.3 + i * 0.22, qWhich + 0.5 + i * 0.22, 'o')
        if (tp > 0) {
          c.strokeStyle = C.red; c.lineWidth = 4.5; c.beginPath()
          const sx = 420, sy = gy - 190, ex = lerp(sx, bx, tp), sag = 400 + 75 * i + 12 * Math.sin(t * 2 + i)
          c.moveTo(sx, sy); c.quadraticCurveTo((sx + ex) / 2, gy + sag, ex, lerp(sy, gy - 120, tp)); c.stroke()
        }
        const qp = prog(t, qWhich + 0.6 + i * 0.22, qWhich + 0.85 + i * 0.22, 'back')
        if (qp > 0) { c.save(); c.translate(bx, gy - 400); c.scale(qp, qp); text(c, '?', 0, 0, F.head(150, 900), C.red); c.restore() }
      })
      c.restore()
    }
    c.restore()
    const da = prog(t, qDead + 0.9, qDead + 1.5)
    if (da > 0) { text(c, 'Which banks were tied to those men?', W / 2, 150, F.headI(64, 700), C.ink, { alpha: prog(t, qWhich - 0.2, qWhich + 0.6) }) }
    finish(c, t, false); return false
  }

  // =============================== 4. the run ===============================
  const TRUSTS = [{ x: 960, sign: 'KNICKERBOCKER TRUST CO.' }, { x: 2500, sign: 'TRUST CO. OF AMERICA' }, { x: 4040, sign: 'TRUST COMPANY' }]
  const RUN = crowd(64, 44, { h: 215, ladies: 0.22 })
  function s4(c, t, q, S) {
    const qMorn = q('on the morning'), qCrowd = q('the crowd came'), qKept = q('and kept coming'), q3h = q('in under three hours'), q8 = q('about 8 million'), qNoon = q('a little after noon'), qShut = q('it shut its doors') + 0.35, qFear = q('now the fear') - 0.3, qAny = q('so could anybody'), qLines = q('so the lines moved'), qNext = q('to the next trust'), qNext2 = q('and the next')
    paper(c, t)
    const gy = 850
    // camera: on the Knickerbocker, then back, then down the street
    const z = track(t, [[S.vis, 0.92], [qShut, 1.0, 'l'], [qFear, 1.0, 'l'], [qFear + 1.6, 0.62, 'io'], [S.end + 1, 0.6, 'l']])
    const cx = track(t, [[S.vis, 960], [qFear + 1.6, 960, 'l'], [qLines, 1100, 'io'], [qNext + 0.9, 2500, 'io'], [qNext2, 2560, 'l'], [qNext2 + 1.5, 4040, 'io'], [S.end + 1, 4100, 'l']])
    const cy = track(t, [[S.vis, 520], [qFear, 520, 'l'], [qFear + 1.6, 470, 'io']])
    c.save(); cam(c, cx, cy, z)
    // backdrop blocks
    c.save(); c.globalAlpha = 0.2; const r = rng(18); for (let x = -1400; x < 5800; x += 110 + r() * 80) block(c, x, gy, 90 + r() * 90, 300 + r() * 560, { fill: C.ink3 }); c.restore()
    const shut = prog(t, qShut, qShut + 0.3, 'i')
    TRUSTS.forEach((b, i) => {
      bank(c, b.x, gy, 1000, 640, { cols: 6, sign: b.sign, signPx: 46, track: 4, lw: 4 })
      // doors
      const dw = 150, dh = 250, sh = i === 0 ? shut : 0
      c.fillStyle = C.ink; c.fillRect(b.x - dw / 2, gy - 64 - dh, dw, dh)
      c.fillStyle = '#5a3a22'; c.fillRect(b.x - dw / 2, gy - 64 - dh, dw / 2 * sh, dh); c.fillRect(b.x + dw / 2 - dw / 2 * sh, gy - 64 - dh, dw / 2 * sh, dh)
      if (i === 0 && sh >= 1) {
        const dp = prog(t, qShut + 0.3, qShut + 0.8, 'bounce'), sw = Math.sin(t * 3) * 0.02 * (1 - prog(t, qShut + 0.8, qShut + 3))
        c.save(); c.translate(b.x, gy - 64 - dh + 20); c.rotate(sw); c.translate(0, lerp(-200, 70, dp)); c.fillStyle = C.paper; c.strokeStyle = C.red; c.lineWidth = 5; rr(c, -150, -40, 300, 86, 4); c.fill(); c.stroke()
        text(c, 'PAYMENTS', 0, -4, F.head(30, 900), C.red, { track: 5 }); text(c, 'SUSPENDED', 0, 32, F.head(30, 900), C.red, { track: 5 }); c.restore()
      }
    })
    c.strokeStyle = C.ink; c.lineWidth = 5; c.beginPath(); c.moveTo(-1500, gy); c.lineTo(6000, gy); c.stroke()
    hatch(c, k => k.rect(-1500, gy + 3, 7500, 400), { gap: 10, alpha: 0.2, angle: 0.02, box: [-1500, gy, 7500, 400] })
    // the crowd. Phase 1: streaming to the Knickerbocker door. Phase 2: surging to the next trusts.
    const arrive = prog(t, qCrowd - 0.6, qKept + 2.5)
    const m1 = prog(t, qLines - 0.2, qNext + 1.2), m2 = prog(t, qNext2 - 0.3, qNext2 + 2.2)
    const people = RUN.map(p => {
      const side = p.i % 2 ? 1 : -1
      const lane = gy + 26 + (p.i % 5) * 34 + p.jit2 * 12
      // queue slot: packed outward from the door
      const slot = 70 + Math.floor(p.i / 2) * 44 + p.jit * 26
      const enter = clamp(arrive * 1.5 - (p.i / RUN.length) * 0.9)
      let x = TRUSTS[0].x + side * lerp(slot + 1500, slot, EZ.o(enter)), moving = enter > 0 && enter < 1 ? 1 : 0, face = -side
      // before the doors shut, people at the head go in and others take their place: a slow shuffle
      if (t < qShut && enter >= 1) { x -= side * ((t * 26 + p.jit * 44) % 44); moving = 0.5 }
      // after the fear spreads, most of them run for the next trust
      const goes = p.jit2 < 0.85
      if (goes && m1 > 0) {
        const d1 = clamp(m1 * 1.6 - p.jit * 0.6), tx = TRUSTS[1].x + side * (slot * 0.9)
        x = lerp(x, tx, EZ.io(d1)); if (d1 > 0 && d1 < 1) { moving = 1.5; face = 1 } else if (d1 >= 1) face = -side
        if (p.jit2 < 0.6 && m2 > 0) { const d2 = clamp(m2 * 1.6 - p.jit * 0.6), tx2 = TRUSTS[2].x + side * (slot * 0.8); x = lerp(tx, tx2, EZ.io(d2)); if (d2 > 0 && d2 < 1) { moving = 1.5; face = 1 } else if (d2 >= 1) face = -side }
      }
      const jostle = (t > qShut ? 1 : 0.3) * 4 * noise(t * 2.2 + p.i, p.i)
      return { p, x: x + jostle, y: lane, moving, face }
    }).sort((a, b) => a.y - b.y)
    for (const { p, x, y, moving, face } of people) {
      const angry = t > qShut && moving < 1 && p.i % 4 === 0 ? 0.35 + 0.15 * Math.sin(t * 7 + p.ph) : 0
      person(c, x, y, p.h, { hat: p.hat, lady: p.lady, walk: t * (moving > 1 ? 9 : 6) * p.sp + p.ph, stride: clamp(moving), face, bulk: p.bulk, belly: p.belly, arm: angry, lean: moving > 1 ? 0.12 : 0 })
    }
    c.restore()
    // the clock and the till, kept on screen while the bank is open
    const hud = prog(t, qMorn, qMorn + 0.6) * (1 - prog(t, qFear, qFear + 0.6))
    if (hud > 0) {
      c.save(); c.globalAlpha = hud
      const hrs = track(t, [[qMorn, 9.0], [q3h, 9.4, 'l'], [q8 + 0.8, 11.9, 'io'], [qShut, 12.15, 'l']])
      c.fillStyle = C.paper; c.strokeStyle = C.ink; c.lineWidth = 4; rr(c, 60, 50, 560, 190, 6); c.fill(); c.stroke()
      clock(c, 160, 145, 68, hrs, { plain: false })
      text(c, 'TUESDAY', 260, 122, F.sc(34), C.ink, { align: 'left', track: 4 }); text(c, 'October 22, 1907', 260, 170, F.bodyI(38), C.ink2, { align: 'left' })
      const paid = 8e6 * prog(t, q3h, q8 + 0.9, 'io')
      c.fillStyle = C.ink; rr(c, 1240, 50, 620, 190, 6); c.fill()
      text(c, 'PAID OUT TO DEPOSITORS', 1550, 104, F.sc(30), C.paper2, { track: 4 })
      text(c, paid < 7.99e6 ? money(Math.round(paid / 1000) * 1000) : 'about $8,000,000', 1550, 196, F.head(paid < 7.99e6 ? 76 : 58, 800), C.gold2)
      c.restore()
    }
    const fa = prog(t, qAny - 0.3, qAny + 0.4) * (1 - prog(t, qLines + 1.2, qLines + 1.8))
    if (fa > 0) text(c, 'If the Knickerbocker could fall, so could anybody.', W / 2, 170, F.headI(62, 700), C.red, { alpha: fa })
    finish(c, t, false); return false
  }

  window.SCENES = [s1, s2, s3, s4]
  window.LIB = { library, LW, DOOR, cam, street, STREET }
})()
