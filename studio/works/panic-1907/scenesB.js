// scenesB.js: scenes 5-7.
(function () {
  const { clamp, lerp, EZ, prog, bump, rng, noise, track } = K
  const { W, H, C, F, layer, paper, finish, hatch, rr, text, typeset, rule, person, crowd, morgan, bank, block, clock, key, coin, glow, money, tw } = L
  const { library, LW, DOOR, cam, street } = LIB
  const fade = (c, a, col = '8,6,6') => { if (a > 0) { c.fillStyle = `rgba(${col},${clamp(a)})`; c.fillRect(0, 0, W, H) } }
  const skyline = (c, gy, seed, a = 0.2, x0 = -200, x1 = W + 200) => { c.save(); c.globalAlpha = a; const r = rng(seed); for (let x = x0; x < x1; x += 100 + r() * 70) block(c, x, gy, 80 + r() * 80, 220 + r() * 460, { fill: C.ink3 }); c.restore() }

  // =============================== 5. one private citizen ===============================
  const PRES = crowd(14, 71, { h: 300, ladies: 0 })
  const CLERKS = [0, 1, 2]
  function exchange(c, t, o = {}) {
    const gy = 880
    skyline(c, gy, 52, 0.2)
    bank(c, 960, gy, 1180, 720, { cols: 6, sign: 'NEW YORK STOCK EXCHANGE', signPx: 50, track: 5, lw: 4 })
    c.fillStyle = C.ink; c.fillRect(880, gy - 330, 160, 258)
    // flag
    c.strokeStyle = C.ink; c.lineWidth = 5; c.beginPath(); c.moveTo(960, gy - 720); c.lineTo(960, gy - 900); c.stroke()
    c.fillStyle = C.red; c.beginPath(); c.moveTo(963, gy - 898)
    for (let i = 0; i <= 10; i++) c.lineTo(963 + i * 13, gy - 898 + Math.sin(t * 4 - i * 0.7) * 7 * i / 10)
    for (let i = 10; i >= 0; i--) c.lineTo(963 + i * 13, gy - 838 + Math.sin(t * 4 - i * 0.7 + 0.5) * 7 * i / 10)
    c.closePath(); c.fill()
    c.strokeStyle = C.ink; c.lineWidth = 5; c.beginPath(); c.moveTo(-200, gy); c.lineTo(W + 200, gy); c.stroke()
    hatch(c, k => k.rect(-200, gy + 3, W + 400, 300), { gap: 10, alpha: 0.2, angle: 0.02, box: [-200, gy, W + 400, 300] })
    if (o.front) o.front(c, gy)
  }
  function s5(c, t, q, S) {
    const qJP = q('j p morgan') , qSev = q('seventy years old'), qMen = q('he had his men') - 0.3, qOver = q('overnight'), qSound = q('when they told him') - 0.25, qThis = q('this is the place'), qNext = q('the next day') - 0.35, qPres = q('its president'), qClose = q('close early'), qCalled = q('morgan called in') - 0.3, q25 = q('he needed 25'), qTen = q('in ten minutes'), qBy = q('by sixteen minutes'), q236 = q('twentythree point six'), qStay = q('the exchange stayed') - 0.2
    if (t < qMen + 0.2) {
      paper(c, t)
      const z = 1 + 0.04 * prog(t, S.vis, qMen, 'l')
      c.save(); cam(c, W / 2, H / 2, z)
      // medallion
      c.save(); c.globalAlpha = prog(t, S.vis + 0.2, S.vis + 1)
      c.strokeStyle = C.ink; c.lineWidth = 4; c.beginPath(); c.arc(560, 520, 400, 0, 7); c.stroke(); c.lineWidth = 1.5; c.beginPath(); c.arc(560, 520, 384, 0, 7); c.stroke()
      hatch(c, k => k.arc(560, 520, 384, 0, 7), { gap: 7, alpha: 0.3, angle: -0.5 + 0.02 * Math.sin(t), box: [160, 120, 800, 800] })
      c.restore()
      const wx = track(t, [[S.vis, -160], [qJP - 0.1, 560, 'o']]), moving = t < qJP - 0.1 ? 1 : 0
      c.save(); c.beginPath(); c.rect(0, 0, W, 905); c.clip()
      morgan(c, wx, 900, 640, { walk: t * 4.6, stride: moving * (1 - prog(t, qJP - 0.6, qJP - 0.1)), lean: 0.01 * Math.sin(t * 1.3) })
      c.restore()
      c.strokeStyle = C.ink; c.lineWidth = 5; c.beginPath(); c.moveTo(120, 902); c.lineTo(1000, 902); c.stroke()
      text(c, 'ONE PRIVATE CITIZEN', 1380, 330, F.sc(40), C.red, { track: 8, alpha: prog(t, S.vis + 0.8, S.vis + 1.5) })
      rule(c, 1090, 1670, 356, C.ink, prog(t, qJP - 0.2, qJP + 0.6))
      typeset(c, 'J. Pierpont', 1380, 500, F.head(128, 900), C.ink, prog(t, qJP - 0.1, qJP + 0.5))
      typeset(c, 'Morgan', 1380, 650, F.head(160, 900), C.ink, prog(t, qJP + 0.3, qJP + 0.9))
      rule(c, 1090, 1670, 700, C.ink, prog(t, qJP + 0.5, qJP + 1.2))
      text(c, 'banker · age 70', 1380, 790, F.bodyI(60), C.ink2, { alpha: prog(t, qSev, qSev + 0.5) })
      c.restore()
      finish(c, t, false); return false
    }
    if (t < qSound + 0.2) {
      // the night audit
      const g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#0f1420'); g.addColorStop(1, '#1b1410'); c.fillStyle = g; c.fillRect(0, 0, W, H)
      const z = 1 + 0.05 * prog(t, qMen, qSound, 'l'), nt = prog(t, qMen, qSound + 0.2)
      c.save(); cam(c, W / 2 + 20, H / 2, z)
      // window: the moon crossing
      c.fillStyle = '#1f2a44'; rr(c, 1330, 130, 380, 430, [190, 190, 0, 0]); c.fill()
      c.save(); rr(c, 1330, 130, 380, 430, [190, 190, 0, 0]); c.clip()
      const mx = lerp(1360, 1690, nt), my = 300 - Math.sin(nt * Math.PI) * 120
      glow(c, mx, my, 220, '220,225,255', 0.4); c.fillStyle = '#eee8d5'; c.beginPath(); c.arc(mx, my, 34, 0, 7); c.fill()
      c.fillStyle = '#0d1220'; for (const [bx, bw, bh] of [[1330, 70, 150], [1410, 90, 230], [1510, 60, 120], [1580, 130, 190]]) c.fillRect(bx, 560 - bh, bw, bh)
      c.restore(); c.strokeStyle = '#0a0806'; c.lineWidth = 10; rr(c, 1330, 130, 380, 430, [190, 190, 0, 0]); c.stroke(); c.beginPath(); c.moveTo(1520, 130); c.lineTo(1520, 560); c.moveTo(1330, 360); c.lineTo(1710, 360); c.stroke()
      // wall clock
      clock(c, 330, 250, 100, 21.2 + nt * 8.3, { col: '#0a0806', face: '#d8cbae', rim: C.gold })
      // desk lamps and clerks
      for (const k of CLERKS) {
        const dx = 430 + k * 420, fl = 0.9 + 0.1 * noise(t * 6 + k * 3, k)
        glow(c, dx, 700, 420, '246,199,112', 0.42 * fl)
        // ledger
        c.fillStyle = '#e6d9bd'; c.beginPath(); c.moveTo(dx - 150, 800); c.lineTo(dx - 6, 790); c.lineTo(dx - 6, 846); c.lineTo(dx - 150, 856); c.closePath(); c.fill()
        c.beginPath(); c.moveTo(dx + 150, 800); c.lineTo(dx + 6, 790); c.lineTo(dx + 6, 846); c.lineTo(dx + 150, 856); c.closePath(); c.fill()
        c.strokeStyle = 'rgba(26,21,18,0.45)'; c.lineWidth = 1.5; for (let i = 0; i < 5; i++) { c.beginPath(); c.moveTo(dx - 138, 812 + i * 8); c.lineTo(dx - 18, 804 + i * 8); c.moveTo(dx + 18, 804 + i * 8); c.lineTo(dx + 138, 812 + i * 8); c.stroke() }
        // a page turning
        const ph = ((t * 0.75 + k * 0.37) % 1), fp = clamp(ph * 3)
        if (fp < 1) { const a = Math.PI * fp; c.fillStyle = '#f3e8cf'; c.beginPath(); c.moveTo(dx, 792); c.lineTo(dx + Math.cos(a) * 144, 800 - Math.sin(a) * 90); c.lineTo(dx + Math.cos(a) * 144, 852 - Math.sin(a) * 90); c.lineTo(dx, 846); c.closePath(); c.fill() }
        // lamp
        c.fillStyle = '#0a0806'; c.fillRect(dx + 170, 700, 8, 150); c.fillStyle = C.lamp; c.beginPath(); c.moveTo(dx + 140, 700); c.lineTo(dx + 208, 700); c.lineTo(dx + 192, 650); c.lineTo(dx + 156, 650); c.closePath(); c.fill()
        // clerk, bent over the page
        const nod = 0.05 * Math.sin(t * 1.4 + k * 2)
        person(c, dx - 20, 1010, 520, { hat: 'cap', col: '#0a0806', seated: true, lean: 0.2 + nod, bulk: 1.05, arm: 0.34 + 0.03 * Math.sin(t * 5 + k), face: 1 })
      }
      c.fillStyle = '#0a0806'; c.fillRect(120, 852, 1500, 34); c.fillRect(160, 886, 30, 200); c.fillRect(1560, 886, 30, 200)
      c.restore()
      text(c, 'THE BOOKS OF THE TRUST COMPANY OF AMERICA', W / 2, 96, F.sc(36), C.paper2, { track: 5, alpha: prog(t, qMen + 0.4, qMen + 1.2) })
      text(c, 'checked overnight', W / 2, 146, F.bodyI(38), C.gold2, { alpha: prog(t, qOver - 0.2, qOver + 0.4) })
      finish(c, t, true); return true
    }
    if (t < qNext + 0.2) {
      // the line
      paper(c, t)
      const z = 1 + 0.04 * prog(t, qSound, qNext, 'l')
      c.save(); cam(c, W / 2, H / 2, z)
      morgan(c, 330, 930, 600, { lean: 0.008 * Math.sin(t * 1.2), arm: 0.3 * prog(t, qThis, qThis + 0.4, 'o'), cane: true })
      c.strokeStyle = C.ink; c.lineWidth = 5; c.beginPath(); c.moveTo(80, 932); c.lineTo(620, 932); c.stroke()
      const lines = [['This', 'is', 'the', 'place'], ['to', 'stop', 'the', 'trouble,'], ['then.']], times = q.seq('this is the place', 9)
      text(c, '“', 700, 420, F.head(260, 900), C.red, { alpha: prog(t, qThis - 0.3, qThis) })
      let k = 0
      lines.forEach((ln, li) => {
        let x = 760; const y = 440 + li * 150, font = F.headI(124, 700)
        ln.forEach(w => { const a = prog(t, times[k] - 0.05, times[k] + 0.18, 'o'); text(c, w, x, y + (1 - a) * 18, font, li === 2 ? C.red : C.ink, { align: 'left', alpha: a }); x += tw(c, w + ' ', font); k++ })
      })
      const ea = prog(t, times[8] + 0.7, times[8] + 1.3)
      rule(c, 760, 1500, 800, C.ink, ea); text(c, 'J. P. Morgan, Wednesday, October 23, 1907', 760, 870, F.bodyI(42), C.ink2, { align: 'left', alpha: ea })
      c.restore()
      finish(c, t, false); return false
    }
    if (t < qCalled + 0.2) {
      // the Exchange, and the president on his way to Morgan
      paper(c, t)
      const z = track(t, [[qNext, 0.9], [qPres, 0.96, 'l'], [qCalled + 0.2, 1.06, 'l']])
      c.save(); cam(c, W / 2, 560, z)
      const run = prog(t, qPres - 0.2, qCalled + 0.3, 'l')
      exchange(c, t, {
        front: (c, gy) => {
          const idle = crowd(12, 91, { h: 210 })
          idle.forEach((p, i) => person(c, 120 + i * 150 + p.jit * 60, gy + 50 + (i % 3) * 36, p.h, { hat: p.hat, lady: p.lady, bulk: p.bulk, face: i % 2 ? 1 : -1, lean: 0.02 * Math.sin(t * 2 + i) }))
          if (run > 0) person(c, lerp(960, 2200, run), gy + 20, 250, { hat: 'top', walk: t * 11, stride: 1, lean: 0.14, bulk: 1.1, face: 1 })
        },
      })
      c.restore()
      c.save(); c.globalAlpha = prog(t, qNext + 0.3, qNext + 0.9)
      c.fillStyle = C.paper; c.strokeStyle = C.ink; c.lineWidth = 4; rr(c, 60, 50, 590, 190, 6); c.fill(); c.stroke()
      clock(c, 160, 145, 68, track(t, [[qNext, 13.2], [qPres + 0.8, 13.5, 'io'], [qCalled, 13.9, 'l']]))
      text(c, 'THURSDAY', 260, 122, F.sc(34), C.ink, { align: 'left', track: 4 }); text(c, 'October 24, 1907', 260, 170, F.bodyI(38), C.ink2, { align: 'left' })
      c.restore()
      const ca = prog(t, qClose - 0.2, qClose + 0.3)
      if (ca > 0) { c.save(); c.translate(1500, 150); c.rotate(-0.05); c.scale(2 - ca, 2 - ca); c.globalAlpha = ca; c.strokeStyle = C.red; c.lineWidth = 6; rr(c, -300, -58, 600, 116, 8); c.stroke(); text(c, 'CLOSING EARLY?', 0, 22, F.head(56, 900), C.red, { track: 4 }); c.restore() }
      finish(c, t, false); return false
    }
    if (t < qStay + 0.2) {
      // ten minutes
      paper(c, t, C.paper2)
      const z = 1 + 0.03 * prog(t, qCalled, qStay, 'l')
      c.save(); cam(c, W / 2, H / 2, z)
      const gy = 900
      c.strokeStyle = C.ink; c.lineWidth = 5; c.beginPath(); c.moveTo(0, gy); c.lineTo(W, gy); c.stroke()
      hatch(c, k => k.rect(0, gy + 3, W, 200), { gap: 9, alpha: 0.25, angle: 0.03, box: [0, gy, W, 200] })
      morgan(c, 250, gy, 500, { arm: 0.42 * prog(t, q25 - 0.3, q25 + 0.2, 'o') * (1 - prog(t, qBy, qBy + 0.6)), lean: 0.01 * Math.sin(t * 1.5) })
      const pledge = prog(t, qTen + 0.9, q236 + 0.3, 'io')
      PRES.forEach((p, i) => {
        const inn = prog(t, qCalled + 0.1 + i * 0.07, qCalled + 0.9 + i * 0.07, 'o'), mine = clamp(pledge * 14 - i)
        const x = lerp(2100, 560 + i * 92, inn), fwd = bump(clamp(mine), 0, 1) * 0
        person(c, x - mine * 12, gy + (i % 2) * 34, p.h, { hat: i % 3 === 0 ? 'top' : 'bowler', bulk: p.bulk, belly: p.belly, face: -1, walk: t * 7 + p.ph, stride: inn < 1 ? 1 : 0, arm: 0.5 * EZ.o(mine), mous: i % 2 === 0 })
      })
      c.restore()
      // the clock and the tally
      const hrs = track(t, [[qCalled, 13.97], [qTen, 14.0, 'l'], [q236 + 0.2, 14 + 16 / 60, 'io']])
      const ha = prog(t, qCalled + 0.4, qCalled + 1)
      c.save(); c.globalAlpha = ha
      clock(c, 250, 150, 96, hrs, { rim: C.gold })
      const bx = 520, bw = 1280, by = 150
      text(c, 'NEEDED: $25,000,000', bx + bw, by - 22, F.sc(34), C.red, { align: 'right', track: 3, alpha: prog(t, q25, q25 + 0.4) })
      text(c, 'IN TEN MINUTES', bx, by - 22, F.sc(34), C.ink, { align: 'left', track: 3, alpha: prog(t, qTen, qTen + 0.3) })
      c.strokeStyle = C.ink; c.lineWidth = 4; c.fillStyle = C.paper; rr(c, bx, by, bw, 74, 4); c.fill(); c.stroke()
      const fillW = bw * 23.6 / 25 * pledge
      c.fillStyle = C.gold; c.fillRect(bx + 3, by + 3, Math.max(0, fillW - 3), 68)
      hatch(c, k => k.rect(bx + 3, by + 3, Math.max(0, fillW - 3), 68), { gap: 7, alpha: 0.35, angle: -0.8, box: [bx, by, bw, 74] })
      for (let i = 1; i < 14; i++) { const x = bx + bw * 23.6 / 25 * i / 14; if (x < bx + fillW) { c.strokeStyle = 'rgba(26,21,18,0.5)'; c.lineWidth = 2; c.beginPath(); c.moveTo(x, by + 3); c.lineTo(x, by + 71); c.stroke() } }
      text(c, 'PLEDGED  ' + (pledge >= 1 ? '$23,600,000' : money(Math.round(23.6e6 * pledge / 1e5) * 1e5)), bx, by + 150, F.head(72, 900), C.ink, { align: 'left', alpha: prog(t, qTen + 0.7, qTen + 1.1) })
      text(c, 'by 2:16 p.m., from 14 bank presidents', bx, by + 204, F.bodyI(38), C.ink2, { align: 'left', alpha: prog(t, q236 + 0.3, q236 + 0.8) })
      c.restore()
      finish(c, t, false); return false
    }
    paper(c, t)
    const z = 0.94 + 0.05 * prog(t, qStay, S.out, 'l')
    c.save(); cam(c, W / 2, 560, z)
    exchange(c, t, {
      front: (c, gy) => {
        const tr = crowd(16, 93, { h: 210 })
        tr.forEach((p, i) => { const dir = i % 2 ? 1 : -1, span = W + 500, x = ((p.jit * span + dir * t * 80 * p.sp) % span + span) % span - 250; person(c, x, gy + 40 + (i % 4) * 30, p.h, { hat: p.hat, lady: p.lady, bulk: p.bulk, face: dir, walk: t * 6.5 * p.sp + p.ph, stride: 1 }) })
      },
    })
    c.restore()
    const ba = prog(t, qStay + 0.3, qStay + 0.7, 'back')
    if (ba > 0) { c.save(); c.translate(W / 2, 150); c.scale(ba, ba); const bw2 = tw(c, 'THE EXCHANGE STAYED OPEN', F.head(54, 900), 4) + 90; c.fillStyle = C.ink; rr(c, -bw2 / 2, -64, bw2, 128, 6); c.fill(); text(c, 'THE EXCHANGE STAYED OPEN', 2, 22, F.head(54, 900), C.gold2, { track: 4 }); c.restore() }
    finish(c, t, false); return false
  }

  // =============================== 6. back to the library ===============================
  const QUEUE6 = crowd(30, 66, { h: 220, ladies: 0.25 })
  const SIGS = (() => {       // five signatures, as scribbles
    const r = rng(1913), out = []
    for (let k = 0; k < 5; k++) {
      // a cursive scribble: loops that lean forward, with a tall capital now and then
      const pts = [], n = 54 + Math.floor(r() * 16), f = 0.85 + r() * 0.3, ph = r() * 6
      for (let i = 0; i < n; i++) { const cap = (i < 5 || Math.abs(i - n * 0.45) < 3) ? 2.4 : 1, amp = (13 + 9 * Math.sin(i * 0.31 + ph)) * cap; pts.push([i * 10.5 + 13 * Math.sin(i * f + ph), -amp * 0.85 * Math.sin(i * f + ph) - 8 + (i > n - 4 ? (i - n + 4) * 5 : 0)]) }
      out.push(pts)
    }
    return out
  })()
  function sig(c, pts, x, y, p, col = '#1c2440') {
    const n = pts.length * clamp(p); if (n <= 0) return null
    c.save(); c.strokeStyle = col; c.lineWidth = 4.2; c.lineCap = 'round'; c.lineJoin = 'round'; c.beginPath(); c.moveTo(x, y)
    let lx = x, ly = y
    for (let i = 0; i < Math.floor(n); i++) { const [px, py] = pts[i]; const nx = x + px, ny = y + py; c.quadraticCurveTo((lx + nx) / 2 + 4, ly, nx, ny); lx = nx; ly = ny }
    c.stroke(); c.restore(); return [lx, ly]
  }
  function s6(c, t, q, S) {
    const qBack = q('and that brings us back') - 0.2, qLib = q('to the library'), qPut = q('morgan put'), q25 = q('another 25 million'), qSave = q('to save each other'), qHeld = q('they held out') - 0.3, qAbout = q('at about a quarter') - 0.3, qSign = q('their leader signed'), qRest = q('then the rest'), qUnl = q('morgan unlocked') - 0.35, qWorst = q('and the worst') - 0.3
    if (t < qBack + 0.3) {
      // the runs go on
      paper(c, t, C.paper2)
      const gy = 850, z = 0.9 + 0.05 * prog(t, S.vis, qBack, 'l')
      c.save(); cam(c, 960 + 60 * prog(t, S.vis, qBack + 0.3, 'l'), 540, z)
      skyline(c, gy, 61, 0.22)
      bank(c, 1250, gy, 1000, 640, { cols: 6, sign: 'TRUST CO. OF AMERICA', signPx: 46, track: 4, lw: 4 })
      c.fillStyle = C.ink; c.fillRect(1175, gy - 314, 150, 250)
      c.strokeStyle = C.ink; c.lineWidth = 5; c.beginPath(); c.moveTo(-300, gy); c.lineTo(W + 400, gy); c.stroke()
      hatch(c, k => k.rect(-300, gy + 3, W + 700, 400), { gap: 10, alpha: 0.22, angle: 0.02, box: [-300, gy, W + 700, 400] })
      QUEUE6.forEach((p, i) => { const x = 1180 - i * 46 - ((t * 22) % 46) + p.jit * 10; person(c, x, gy + 40 + (i % 2) * 26 + Math.sin(i) * 6, p.h, { hat: p.hat, lady: p.lady, bulk: p.bulk, face: 1, walk: t * 5 + p.ph, stride: 0.45 }) })
      c.restore()
      text(c, 'The withdrawals went on for two more weeks', W / 2, 110, F.bodyI(46), C.ink, { alpha: prog(t, S.vis + 0.5, S.vis + 1.2) })
      finish(c, t, false); return false
    }
    if (t < qSign - 0.5) {
      // the room, the demand, the long night
      const night = prog(t, qHeld, qAbout + 0.6, 'io')
      const camX = track(t, [[qBack, 250], [qHeld, 520, 'sine'], [qSign, 640, 'l']])
      library(c, t, camX, {
        fire: 1 - 0.6 * night, slump: 1 + night,
        skip: b => b.x < 760,
        front: (c) => { morgan(c, 560, 990, 520, { col: '#0b0807', face: 1, arm: 0.34 * prog(t, q25 - 0.6, q25, 'o') * (1 - prog(t, qHeld - 0.3, qHeld + 0.3)), lean: 0.008 * Math.sin(t * 1.3), chain: true }) },
      })
      // the demand
      const da = prog(t, q25 - 0.3, q25 + 0.3) * (1 - prog(t, qHeld - 0.2, qHeld + 0.4))
      if (da > 0) { text(c, 'ANOTHER', W / 2, 210, F.sc(46), C.paper2, { track: 10, alpha: da, shadow: '#000' }); text(c, '$25,000,000', W / 2, 340, F.head(150, 900), C.gold2, { alpha: da, shadow: '#000', blur: 30 }); typeset(c, 'to save each other', W / 2, 420, F.bodyI(56), C.paper, prog(t, qSave - 0.1, qSave + 0.7), { shadow: '#000' }) }
      // the clock running through the night
      const ca = prog(t, qHeld, qHeld + 0.5) * (1 - prog(t, qSign - 1, qSign - 0.5))
      if (ca > 0) {
        const hrs = track(t, [[qHeld, 21], [qAbout + 0.8, 28.6, 'io'], [qSign, 28.75, 'l']])
        c.save(); c.globalAlpha = ca; glow(c, W / 2, 300, 420, '246,199,112', 0.25)
        clock(c, W / 2, 300, 190, hrs, { col: '#15100d', face: '#e9dcc0', rim: C.gold }); c.restore()
        text(c, 'about 4:45 a.m.', W / 2, 590, F.bodyI(52), C.paper, { alpha: prog(t, qAbout + 0.5, qAbout + 1) * ca, shadow: '#000' })
      }
      fade(c, 1 - prog(t, qBack + 0.3, qBack + 0.8) + prog(t, qSign - 0.9, qSign - 0.5))
      finish(c, t, true); return true
    }
    if (t < qUnl + 0.15) {
      // the paper
      const g = c.createRadialGradient(960, 480, 100, 960, 480, 1200); g.addColorStop(0, '#5a3c22'); g.addColorStop(1, '#120c09'); c.fillStyle = g; c.fillRect(0, 0, W, H)
      const z = 1 + 0.05 * prog(t, qSign - 0.5, qUnl, 'l')
      c.save(); cam(c, W / 2, H / 2, z); c.translate(W / 2, H / 2); c.rotate(-0.025); c.translate(-W / 2, -H / 2)
      c.fillStyle = 'rgba(0,0,0,0.4)'; c.fillRect(398, 78, 1150, 980); c.fillStyle = '#efe4c9'; c.fillRect(380, 60, 1150, 980)
      text(c, 'THE TRUST COMPANIES OF NEW YORK', 955, 170, F.sc(40), C.ink, { track: 5 }); rule(c, 520, 1390, 196, C.ink)
      text(c, '$25,000,000', 955, 310, F.head(100, 900), C.red)
      text(c, 'to be put up together', 955, 372, F.bodyI(40), C.ink2)
      const yy = [480, 575, 670, 765, 860], st = [qSign - 0.1, qRest, qRest + 0.35, qRest + 0.7, qRest + 1.05], du = [1.0, 0.55, 0.55, 0.55, 0.55]
      let pen = null
      yy.forEach((y, k) => {
        c.strokeStyle = 'rgba(26,21,18,0.5)'; c.lineWidth = 2; c.beginPath(); c.moveTo(560, y + 24); c.lineTo(1350, y + 24); c.stroke()
        const p = prog(t, st[k], st[k] + du[k]), end = sig(c, SIGS[k], 600 + k % 2 * 40, y + 14, p)
        if (p > 0 && p < 1 && end) pen = end
      })
      if (pen) { c.save(); c.translate(pen[0], pen[1]); c.rotate(-0.7); c.fillStyle = '#0b0807'; c.beginPath(); c.moveTo(0, 0); c.lineTo(10, -30); c.lineTo(26, -330); c.lineTo(-6, -330); c.lineTo(-10, -30); c.closePath(); c.fill(); c.fillStyle = C.gold; c.beginPath(); c.moveTo(0, 0); c.lineTo(8, -30); c.lineTo(-8, -30); c.closePath(); c.fill(); c.restore() }
      c.restore()
      glow(c, 1500, 200, 700, '246,199,112', 0.22 + 0.02 * noise(t * 6, 1))
      fade(c, 1 - prog(t, qSign - 0.5, qSign - 0.15) + prog(t, qUnl - 0.2, qUnl + 0.15))
      finish(c, t, true); return true
    }
    if (t < qWorst + 0.2) {
      // the door
      c.fillStyle = '#17100c'; c.fillRect(0, 0, W, H)
      const z = 1 + 0.06 * prog(t, qUnl, qWorst, 'l'), turn = prog(t, qUnl + 0.5, qUnl + 1.0, 'io'), open = prog(t, qUnl + 1.15, qUnl + 2.4, 'io')
      c.save(); cam(c, W / 2, H / 2, z)
      const dx = 620, dw = 680, dt = 60, df = 1020
      // dawn behind the door
      const g = c.createLinearGradient(0, dt, 0, df); g.addColorStop(0, '#9fb3c8'); g.addColorStop(0.6, '#f0cf9a'); g.addColorStop(1, '#f6b877'); c.fillStyle = g; c.fillRect(dx, dt, dw, df - dt)
      c.fillStyle = '#2a3340'; for (const [bx, bw, bh] of [[dx, 120, 330], [dx + 140, 90, 470], [dx + 250, 150, 280], [dx + 420, 100, 520], [dx + 540, 140, 360]]) c.fillRect(bx, df - 150 - bh, bw, bh)
      c.fillStyle = '#3a3026'; c.fillRect(dx, df - 150, dw, 150)
      // the door leaf, swinging on its left edge
      const lw = dw * (1 - open * 0.86)
      c.fillStyle = '#4a2f1c'; c.fillRect(dx, dt, lw, df - dt)
      c.save(); c.beginPath(); c.rect(dx, dt, lw, df - dt); c.clip(); c.strokeStyle = '#2a190e'; c.lineWidth = 8
      const sx = lw / dw; for (const [px, py, pw, ph] of [[70, 70, 230, 330], [380, 70, 230, 330], [70, 470, 230, 420], [380, 470, 230, 420]]) c.strokeRect(dx + px * sx, dt + py, pw * sx, ph)
      hatch(c, k => k.rect(dx, dt, lw, df - dt), { gap: 7, alpha: 0.22, angle: Math.PI / 2, col: '#1a0f08', box: [dx, dt, dw, df - dt] })
      // plate, keyhole, key
      const kx = dx + lw - 90 * sx, ky = 560
      c.fillStyle = C.gold; rr(c, kx - 34 * sx, ky - 90, 68 * sx, 180, 10); c.fill(); c.fillStyle = '#0a0705'; c.beginPath(); c.arc(kx, ky - 6, 13 * sx, 0, 7); c.fill(); c.fillRect(kx - 6 * sx, ky - 6, 12 * sx, 40)
      c.restore()
      const kin = prog(t, qUnl - 0.1, qUnl + 0.45, 'o')
      if (open < 0.25) { c.save(); c.globalAlpha = 1 - prog(open, 0.05, 0.25); c.translate(lerp(kx + 560, kx + 200, kin), ky - 6); c.scale(-1, 1 - 0.8 * turn); key(c, 0, 0, 2.1, 0, C.gold2); c.restore() }
      if (turn > 0 && turn < 1) glow(c, kx, ky, 200, '255,230,160', 0.5 * Math.sin(turn * Math.PI))
      // wall and light on the floor
      c.fillStyle = '#17100c'; c.fillRect(0, 0, dx, H); c.fillRect(dx + dw, 0, W, H); c.fillRect(0, 0, W, dt); c.fillStyle = '#100b08'; c.fillRect(0, df, W, 80)
      if (open > 0) { c.fillStyle = `rgba(246,205,140,${0.5 * open})`; c.beginPath(); c.moveTo(dx + lw, df); c.lineTo(dx + dw, df); c.lineTo(dx + dw + 520 * open, H + 200); c.lineTo(dx + lw - 300 * open, H + 200); c.closePath(); c.fill(); glow(c, dx + dw * 0.6, 500, 900, '246,205,140', 0.35 * open) }
      c.restore()
      fade(c, 1 - prog(t, qUnl + 0.15, qUnl + 0.5))
      finish(c, t, true); return true
    }
    // dawn
    const g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#93a8bf'); g.addColorStop(0.55, '#efd2a0'); g.addColorStop(1, '#f2b06a'); c.fillStyle = g; c.fillRect(0, 0, W, H)
    const p = prog(t, qWorst, S.out, 'l'), sy = lerp(900, 700, EZ.o(p))
    glow(c, 1300, sy, 900, '255,236,190', 0.7); c.fillStyle = '#fff3d0'; c.beginPath(); c.arc(1300, sy, 80, 0, 7); c.fill()
    c.save(); cam(c, W / 2 + 40 * p, H / 2, 1.04 - 0.04 * p)
    const r0 = rng(3); c.save(); c.globalAlpha = 0.45; for (let x = -100; x < W + 100; x += 90 + r0() * 90) block(c, x, 860, 80 + r0() * 90, 320 + r0() * 420, { fill: '#6d7688' }); c.restore()
    const r = rng(7); for (let x = -100; x < W + 100; x += 70 + r() * 70) block(c, x, 860, 60 + r() * 80, 140 + r() * 330, { fill: '#39404f', win: 'rgba(255,220,150,0.5)', dens: 0.12 })
    c.fillStyle = '#1b1612'; c.fillRect(-100, 860, W + 200, 300)
    crowd(18, 12, { h: 170, ladies: 0 }).forEach((b, i) => { const x = lerp(300 + i * 40, 2300, clamp(p * 1.25 - i * 0.03)); person(c, x, 880 + (i % 3) * 30, b.h, { hat: i % 2 ? 'top' : 'bowler', col: '#120e0c', walk: t * 5.5 * b.sp + b.ph, stride: 0.9, bulk: b.bulk, lean: 0.05 }) })
    c.restore()
    text(c, 'Sunday morning, November 3, 1907', W / 2, 140, F.bodyI(52), '#1b1612', { alpha: prog(t, qWorst + 0.4, qWorst + 1) })
    finish(c, t, false); return false
  }

  // =============================== 7. the turning point ===============================
  const STACK = [['NEW YORK CITY', 520, 150], ['THE STOCK EXCHANGE', 640, 170], ['THE BANKS', 560, 160], ['THE TRUSTS', 660, 170], ['THE RAILROADS', 500, 150], ['EVERYBODY’S SAVINGS', 700, 160]]
  function tower(c, t, bx, by, wob, hold) {
    // blocks from the bottom up; each sways a little more than the one beneath
    let y = by, lean = 0
    const order = [...STACK].reverse()
    order.forEach(([label, w, h], i) => {
      lean += wob * (0.012 + 0.006 * i) * Math.sin(t * 1.3 + i * 0.6)
      const x = bx + Math.sin(lean * (i + 1)) * 60 * (i + 1) / 2
      c.save(); c.translate(x, y); c.rotate(lean)
      c.fillStyle = C.paper2; c.strokeStyle = C.ink; c.lineWidth = 4; c.beginPath(); c.rect(-w / 2, -h, w, h); c.fill(); c.stroke()
      hatch(c, k => k.rect(-w / 2, -h, w, h), { gap: 8, alpha: 0.22, angle: -0.6 + i, box: [-w / 2, -h, w, h] })
      c.fillStyle = C.paper; c.fillRect(-w / 2 + 26, -h / 2 - 34, w - 52, 68); c.strokeRect(-w / 2 + 26, -h / 2 - 34, w - 52, 68)
      text(c, label, 0, -h / 2 + 15, F.sc(Math.min(40, (w - 80) / label.length * 1.75)), C.ink, { track: 3 })
      c.restore(); y -= h
    })
    return y
  }
  function leaf(c, x, y, month, day, year, a = 1, rot = 0) {
    c.save(); c.translate(x, y); c.rotate(rot); c.globalAlpha *= a
    c.fillStyle = 'rgba(0,0,0,0.25)'; c.fillRect(-196, -236, 410, 500); c.fillStyle = C.paper; c.strokeStyle = C.ink; c.lineWidth = 4; c.fillRect(-205, -250, 410, 500); c.strokeRect(-205, -250, 410, 500)
    c.fillStyle = C.red; c.fillRect(-205, -250, 410, 104); text(c, month, 0, -180, F.sc(54), C.paper, { track: 8 })
    text(c, String(day), 0, 120, F.head(260, 900), C.ink); text(c, String(year), 0, 212, F.old(60, true), C.ink2, { track: 10 })
    c.restore()
  }
  const icon = {
    paw: (c) => { c.beginPath(); c.ellipse(0, 22, 40, 34, 0, 0, 7); c.fill(); for (const [x, y, r] of [[-46, -22, 17], [-17, -48, 18], [17, -48, 18], [46, -22, 17]]) { c.beginPath(); c.ellipse(x, y, r * 0.85, r, x * 0.006, 0, 7); c.fill() } },
    swords: (c) => { for (const s of [-1, 1]) { c.save(); c.rotate(s * 0.78); c.fillRect(-6, -84, 12, 126); c.beginPath(); c.moveTo(-6, -84); c.lineTo(0, -102); c.lineTo(6, -84); c.fill(); c.fillRect(-28, 36, 56, 10); c.fillRect(-5, 46, 10, 30); c.beginPath(); c.arc(0, 82, 9, 0, 7); c.fill(); c.restore() } },
    crash: (c) => { c.lineWidth = 11; c.lineJoin = 'round'; c.lineCap = 'round'; c.beginPath(); c.moveTo(-84, 20); c.lineTo(-44, -30); c.lineTo(-14, -8); c.lineTo(16, -64); c.lineTo(44, 44); c.lineTo(84, 70); c.stroke(); c.beginPath(); c.moveTo(84, 70); c.lineTo(52, 72); c.lineTo(76, 44); c.closePath(); c.fill(); c.stroke() },
  }
  function s7(c, t, q, S) {
    const qClose = q('everybody understood'), qWhole = q('the whole financial') - 0.3, qOne = q('one seventyyearold man'), qDoor = q('and a locked door'), qWhat = q('so what happens'), qNot = q('when hes not there'), qDied = q('morgan died') - 0.4, qSame = q('that same year') - 0.3, qXmas = q('two days before'), qCong = q('congress passed'), qCentral = q('a central bank') - 0.35, qNever = q('never again'), qKey = q('to hold the key'), qWhether = q('whether its worked'), qStory = q('is a story'), qSub = q('subscribe') - 0.3, qAn = q('animal facts'), qBat = q('historys greatest'), qCol = q('worlds craziest')
    if (t < qDied + 0.2) {
      paper(c, t)
      // the camera starts at the top of the pile and comes down to the man under it
      const base = 1500, total = STACK.reduce((s, b) => s + b[2], 0)
      const cy = track(t, [[S.vis, base - total - 60], [qWhole, base - total + 160, 'sine'], [qOne + 0.5, base - 120, 'io'], [qDied, base - 150, 'l']])
      const z = track(t, [[S.vis, 1.0], [qWhole, 0.96, 'l'], [qOne + 0.5, 0.86, 'io'], [qDied, 0.84, 'l']])
      const gone = prog(t, qNot - 0.3, qNot + 0.8), wob = 0.5 + 2.2 * gone
      c.save(); cam(c, 960, cy, z)
      c.strokeStyle = C.ink; c.lineWidth = 5; c.beginPath(); c.moveTo(-300, base + 520); c.lineTo(W + 300, base + 520); c.stroke()
      hatch(c, k => k.rect(-300, base + 523, W + 600, 300), { gap: 10, alpha: 0.22, angle: 0.02, box: [-300, base + 520, W + 600, 300] })
      tower(c, t, 960, base, wob)
      // the man underneath
      c.save(); c.globalAlpha = 1 - gone
      morgan(c, 950, base + 520, 520, { arm: 1.02, cane: false, lean: 0.01 * Math.sin(t * 2) }); c.restore()
      if (gone > 0) { c.save(); c.globalAlpha = gone * 0.9; c.setLineDash([12, 10]); c.strokeStyle = C.red; c.lineWidth = 4; c.beginPath(); c.ellipse(955, base + 250, 130, 280, 0, 0, 7); c.stroke(); c.setLineDash([]); text(c, '?', 955, base + 320, F.head(240, 900), C.red); c.restore() }
      // the locked door beside him
      const da = prog(t, qDoor - 0.2, qDoor + 0.4)
      if (da > 0) { c.save(); c.globalAlpha = da * (1 - gone * 0.6); c.fillStyle = '#4a2f1c'; c.strokeStyle = C.ink; c.lineWidth = 5; c.fillRect(1420, base + 100, 240, 420); c.strokeRect(1420, base + 100, 240, 420); c.strokeRect(1446, base + 126, 188, 170); c.strokeRect(1446, base + 320, 188, 174); key(c, 1560, base + 300, 0.7, 0, C.gold2); c.restore() }
      c.restore()
      text(c, 'How close it had been', W / 2, 130, F.headI(84, 700), C.ink, { alpha: prog(t, qClose, qClose + 0.6) * (1 - prog(t, qWhole, qWhole + 0.6)) })
      text(c, 'What happens', 330, 430, F.headI(78, 700), C.red, { alpha: prog(t, qWhat, qWhat + 0.5) }); text(c, 'next time?', 330, 530, F.headI(78, 700), C.red, { alpha: prog(t, qWhat + 0.3, qWhat + 0.8) })
      finish(c, t, false); return false
    }
    if (t < qCentral + 0.2) {
      // two dates in 1913
      paper(c, t, C.paper2)
      const z = 1 + 0.04 * prog(t, qDied, qCentral, 'l')
      c.save(); cam(c, W / 2, H / 2, z)
      const flip = prog(t, qXmas - 0.2, qXmas + 0.5, 'io'), second = t > qSame
      // the hat and cane, set down
      const ha = 1 - prog(t, qSame, qSame + 0.7)
      if (ha > 0) { c.save(); c.globalAlpha = ha; c.fillStyle = C.ink; c.fillRect(1090, 520, 220, 250); rr(c, 1030, 760, 340, 26, 13); c.fill(); c.fillStyle = C.red; c.fillRect(1090, 716, 220, 30); c.strokeStyle = C.ink; c.lineWidth = 14; c.lineCap = 'round'; c.beginPath(); c.moveTo(1480, 790); c.lineTo(1560, 330); c.stroke(); c.beginPath(); c.arc(1596, 336, 36, Math.PI, 0); c.stroke(); c.lineWidth = 5; c.beginPath(); c.moveTo(900, 792); c.lineTo(1720, 792); c.stroke()
        text(c, 'J. Pierpont Morgan', 1300, 890, F.head(64, 800), C.ink); text(c, '1837 – 1913', 1300, 950, F.bodyI(46), C.ink2); c.restore() }
      if (!second) leaf(c, 520, 540, 'MARCH', 31, 1913, prog(t, qDied + 0.2, qDied + 0.7), -0.03)
      else {
        leaf(c, 520, 540, 'DECEMBER', 23, 1913, 1, -0.03)
        if (flip < 1) { c.save(); c.translate(520, 290); c.scale(1, 1 - flip); c.translate(-520, -290); leaf(c, 520, 540, 'MARCH', 31, 1913, 1, -0.03); c.restore() }
        // the Act
        const aa = prog(t, qCong - 0.3, qCong + 0.5, 'o')
        if (aa > 0) {
          c.save(); c.globalAlpha = aa; c.translate(1300, 560 + (1 - aa) * 60); c.rotate(0.02)
          c.fillStyle = 'rgba(0,0,0,0.25)'; c.fillRect(-388, -398, 800, 820); c.fillStyle = '#f1e7cf'; c.strokeStyle = C.ink; c.lineWidth = 4; c.fillRect(-400, -410, 800, 820); c.strokeRect(-400, -410, 800, 820); c.lineWidth = 1.5; c.strokeRect(-384, -394, 768, 788)
          text(c, 'SIXTY-THIRD CONGRESS', 0, -320, F.sc(34), C.ink2, { track: 6 }); rule(c, -260, 260, -296, C.ink)
          text(c, 'Federal', 0, -160, F.head(120, 900), C.ink); text(c, 'Reserve Act', 0, -40, F.head(120, 900), C.ink)
          for (let i = 0; i < 6; i++) { c.strokeStyle = 'rgba(26,21,18,0.35)'; c.lineWidth = 3; c.beginPath(); c.moveTo(-300, 40 + i * 34); c.lineTo(i === 5 ? 80 : 300, 40 + i * 34); c.stroke() }
          sig(c, SIGS[1], -280, 320, prog(t, qCong + 0.7, qCong + 1.6))
          const sp = prog(t, qCong + 1.2, qCong + 1.5, 'back'); if (sp > 0) { c.save(); c.translate(250, 300); c.scale(sp, sp); c.fillStyle = C.red; c.beginPath(); for (let i = 0; i < 32; i++) { const a = i / 32 * 6.283, rr2 = i % 2 ? 62 : 74; c.lineTo(Math.cos(a) * rr2, Math.sin(a) * rr2) } c.closePath(); c.fill(); c.strokeStyle = C.paper; c.lineWidth = 3; c.beginPath(); c.arc(0, 0, 44, 0, 7); c.stroke(); c.restore() }
          c.restore()
        }
      }
      c.restore()
      finish(c, t, false); return false
    }
    if (t < qSub + 0.2) {
      // the lot gets its building
      paper(c, t)
      const build = prog(t, qCentral + 0.2, qNever + 0.3, 'io'), wires = prog(t, qNever, qKey + 0.2, 'io')
      const z = track(t, [[qCentral, 1.0], [qKey + 1, 1.12, 'sine'], [qSub + 0.2, 1.18, 'l']])
      c.save(); cam(c, 960, track(t, [[qCentral, 520], [qSub, 470, 'sine']]), z)
      street(c, t, {
        mid: (c, gy) => {
          c.save(); c.globalAlpha = 1 - build; bank(c, 960, gy, 330, 420, { dash: true, dashT: t, cols: 6, col: C.ink2 }); c.restore()
          // rising from the ground up, like a print being inked
          c.save(); c.beginPath(); c.rect(700, gy - 440 * build - 4, 520, 440 * build + 10); c.clip()
          bank(c, 960, gy, 330, 420, { cols: 6, sign: 'FEDERAL RESERVE', signPx: 24, fill: C.paper, lw: 4 }); c.restore()
          if (build >= 1) { const kp = prog(t, qKey - 0.2, qKey + 0.5, 'back'); if (kp > 0) { c.save(); c.translate(960, gy - 372); c.scale(kp, kp); key(c, -30, 0, 0.5, 0, C.gold); c.restore() } }
          // lines out to every bank
          if (wires > 0) LIB.STREET.forEach((b, i) => { const p = clamp(wires * 1.6 - i * 0.15); if (p <= 0) return; c.strokeStyle = C.gold; c.lineWidth = 5; c.beginPath(); const sx = 960 + (b.x < 960 ? -150 : 150), sy = gy - 290; const ex = lerp(sx, b.x, p); c.moveTo(sx, sy); c.quadraticCurveTo((sx + ex) / 2, sy - 150 - 20 * Math.abs(i - 1.5), ex, lerp(sy, gy - 332, p)); c.stroke(); if (p >= 1) coin(c, b.x, gy - 362, 16, 1) })
        },
      })
      c.restore()
      text(c, 'DECEMBER 23, 1913', W / 2, 110, F.sc(44), C.ink, { track: 10, alpha: prog(t, qCentral + 0.3, qCentral + 1) * (1 - prog(t, qWhether - 0.3, qWhether + 0.2)) })
      text(c, '...a story for another day', W / 2, 120, F.headI(72, 700), C.red, { alpha: prog(t, qStory - 0.2, qStory + 0.5) })
      finish(c, t, false); return false
    }
    // end card
    c.fillStyle = '#0e0b0a'; c.fillRect(0, 0, W, H)
    glow(c, W / 2, 480, 1000, '147,41,28', 0.16)
    const a = qSub + 0.2, z = 1 + 0.03 * prog(t, a, S.out, 'l')
    c.save(); cam(c, W / 2, H / 2, z)
    key(c, W / 2 - 62, 170, 1.05, 0, C.gold)
    rule(c, 520, 1400, 250, C.paper3, prog(t, a, a + 0.8))
    text(c, 'SUBSCRIBE', W / 2, 400, F.head(150, 900), C.paper, { track: 16, alpha: prog(t, a + 0.1, a + 0.6) })
    text(c, 'and we’ll tell it', W / 2, 470, F.bodyI(50), C.paper2, { alpha: prog(t, a + 0.6, a + 1.2) })
    const items = [['paw', 'Animal facts', qAn], ['swords', 'History’s greatest battles', qBat], ['crash', 'The world’s craziest financial collapses', qCol]]
    items.forEach(([ic, label, at], i) => {
      const p = prog(t, at - 0.1, at + 0.3, 'back'), x = 420 + i * 540
      if (p <= 0) return
      c.save(); c.translate(x, 680); c.scale(p, p); c.strokeStyle = C.gold; c.lineWidth = 4; c.beginPath(); c.arc(0, 0, 120, 0, 7); c.stroke()
      c.fillStyle = i === 2 ? C.red2 : C.paper; c.strokeStyle = i === 2 ? C.red2 : C.paper; icon[ic](c); c.restore()
      const ws = label.split(' '), l1 = ws.length > 3 ? ws.slice(0, 3).join(' ') : label, l2 = ws.length > 3 ? ws.slice(3).join(' ') : ''
      text(c, l1, x, 870, F.body(40), C.paper, { alpha: clamp(p) }); if (l2) text(c, l2, x, 918, F.body(40), C.paper, { alpha: clamp(p) })
    })
    c.restore()
    fade(c, 1 - prog(t, a, a + 0.4))
    finish(c, t, true); return true
  }

  window.SCENES.push(s5, s6, s7)
})()
