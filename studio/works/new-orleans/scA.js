// scA.js: scenes 1-5 of The Battle of New Orleans. Each scene is draw(c, t, q, S) -> true if the picture is dark.
// Staging rule for the whole film: Americans on the left in ink, the British on the right in red.
(function () {
  const { clamp, lerp, EZ, prog, bump, rng, noise, track, mix } = K
  const { W, H, C, F, paper, finish, hatch, rr, text, typeset, rule, person, glow, tw } = L
  const { RED, INK, GY, view, stubble, fog, smoke, flash, soldier, front, wallFront, cannon, wall, cypress, horse, rider, ship, ladder, bundle, house } = B
  function flame(c, x, y, s, t, k = 1) { glow(c, x, y - 20 * s, 240 * s * k, '246,150,60', 0.5 * k); for (let i = 0; i < 6; i++) { const fx = x + (i - 2.5) * 9 * s, fh = (40 + ((i * 37) % 46)) * s * k * (0.7 + 0.3 * noise(t * 4 + i * 5, i)), sw = noise(t * 3 + i, 4) * 8 * s; c.fillStyle = i % 2 ? 'rgba(200,80,40,0.95)' : 'rgba(240,200,104,0.95)'; c.beginPath(); c.moveTo(fx - 9 * s, y); c.quadraticCurveTo(fx - 6 * s + sw, y - fh * 0.6, fx + sw, y - fh); c.quadraticCurveTo(fx + 7 * s + sw * 0.4, y - fh * 0.5, fx + 9 * s, y); c.closePath(); c.fill() } }
  const fire = flame
  const fade = (c, a, col = '8,9,11') => { if (a > 0) { c.fillStyle = `rgba(${col},${clamp(a)})`; c.fillRect(0, 0, W, H) } }
  const fogCol = d => mix('#4b535d', '#dcd8c9', d)

  // ---------- the line seen from the field ----------
  const KINDS = ['reg', 'mil', 'mil', 'sailor', 'city', 'mil', 'pirate', 'reg', 'mil', 'none', 'city', 'mil', 'reg', 'sailor', 'mil', 'none']
  const GAPS = [300, 960, 1620]
  const MEN = (() => { const r = rng(1815), out = []; for (let x = -420; x < 2360; x += 44) { if (GAPS.some(g => Math.abs(x - g) < 62)) continue; out.push({ x: x + (r() - 0.5) * 12, kind: KINDS[Math.floor(r() * KINDS.length)], h: 84 + r() * 12, ph: r() * 6.28, f: r() }) } return out })()
  // o: fire(m) -> 0..1 flash for a man, gun(k) -> 0..1 flash for a cannon, men (0..1 how many are up), smokeA
  function lineF(c, t, o = {}) {
    const wy = 830
    MEN.forEach((m, i) => { if (m.f > (o.men ?? 1)) return; front(c, m.x, wy + 8, m.h, { kind: m.kind, gun: 'rest', col: INK }) })
    wallFront(c, -600, 2520, wy, 54, { gaps: GAPS, ditch: o.ditch || '#2c2b28', water: o.water, muz: o.muz })
    if (o.fire) MEN.forEach((m, i) => { const a = o.fire(m, i); if (a > 0) { glow(c, m.x + 10, wy - 50, 90, '246,199,112', 0.8 * a); c.fillStyle = `rgba(255,236,170,${a})`; c.beginPath(); c.arc(m.x + 12, wy - 50, 9 * a + 3, 0, 7); c.fill() } })
    if (o.gun) GAPS.forEach((g, k) => { const a = o.gun(k); if (a > 0) { glow(c, g, wy - 34, 330, '246,199,112', 0.9 * a); c.fillStyle = `rgba(255,236,170,${a})`; c.beginPath(); c.arc(g, wy - 34, 34 * a + 6, 0, 7); c.fill() } })
  }

  // =============================== 1. fog ===============================
  function s1(c, t, q, S) {
    const qSug = q('a sugar field'), qJ = q('its just before') - 0.35, qS = q('somewhere out') - 0.3, qM = q('many of them'), qF = q('in front of them') - 0.4, qA = q('and an army'), qW = q('and the war') - 0.3, qO = q('is already over')
    if (t < qJ + 0.35) {
      view(c, { cx: 960 + 30 * prog(t, 0, qJ, 'l'), cy: 560, s: 1.05, d: 0.14 }, () => { stubble(c, -200, 2200, 0.14); cypress(c, 1650, GY + 6, 1.0, '#0b0d0e', 2); cypress(c, 1830, GY + 8, 0.8, '#0b0d0e', 3); cypress(c, 180, GY + 6, 0.7, '#0b0d0e', 5) })
      fog(c, t, 0.7, { col: fogCol(0.14), y0: 520, y1: 980 })
      const a0 = S.start - 0.3
      text(c, 'JANUARY 8, 1815', W / 2, 400, F.head(150, 900), C.paper, { track: 14, alpha: prog(t, a0, a0 + 1.0), shadow: '#000', blur: 40 })
      rule(c, 560, 1360, 446, C.paper3, prog(t, a0 + 0.4, a0 + 1.4))
      typeset(c, 'a sugar field, five miles below New Orleans', W / 2, 526, F.bodyI(56), C.paper2, prog(t, qSug - 0.2, qSug + 1.6), { shadow: '#000' })
      fade(c, prog(t, qJ - 0.1, qJ + 0.35)); finish(c, t, true); return true
    }
    if (t < qF + 0.35) {
      const d = 0.17 + 0.05 * prog(t, qJ, qF)
      const cx = track(t, [[qJ, 660], [qS, 720, 'sine'], [qM + 0.6, 2900, 'io'], [qF + 0.4, 3020, 'l']])
      view(c, { cx, cy: 600, s: 1.2, d }, () => {
        stubble(c, -300, 4400, d)
        cypress(c, 60, GY + 6, 1.0, '#0d0f10', 4)
        soldier(c, 460, GY + 4, 186, { kind: 'reg', pose: 'stand', col: INK }); soldier(c, 372, GY + 4, 178, { kind: 'city', pose: 'stand', col: INK })
        soldier(c, 632, GY - 44, 190, { kind: 'mil', pose: 'stand', col: INK, lean: 0.04 * Math.sin(t * 0.7) })
        wall(c, 760, GY, 118, { col: INK, water: '#39414d' })
        // the British, forming up
        for (let r = 0; r < 2; r++) for (let i = 0; i < 15; i++) {
          const k = i + r * 15, arr = prog(t, qS + 0.4 + i * 0.1, qM - 0.2 + i * 0.1, 'o'), x = 2420 + i * 84 + r * 42 + (1 - arr) * 1000
          soldier(c, x, GY + 2 + r * 13, 184 + r * 5, { kind: 'brit', col: C.red, face: -1, pose: arr < 1 ? 'march' : 'stand', walk: x * 0.07, stride: arr < 1 ? 1 : 0 })
        }
        horse(c, 2330, GY + 30, 2.1, { col: INK, face: -1, gait: t * 0.6, stride: 0.05, head: 0.1 * Math.sin(t * 0.8), rider: rider('officer', C.red) })
      })
      fog(c, t, 0.8 - 0.14 * prog(t, qM, qF), { col: fogCol(d), y0: 330, y1: 1000, n: 30 })
      fade(c, 1 - prog(t, qJ + 0.35, qJ + 0.9) + prog(t, qF - 0.1, qF + 0.35)); finish(c, t, true); return true
    }
    const d = 0.3
    view(c, { cx: 960 + 40 * prog(t, qF, S.out, 'l'), cy: track(t, [[qF, 905], [qA, 850, 'sine'], [S.out, 835, 'l']]), s: 1.75 + 0.12 * prog(t, qF, S.out, 'l'), d }, () => { stubble(c, -300, 2400, d, 9); lineF(c, t, { water: '#59616c', men: prog(t, qA - 1.2, qA + 0.6) * 1.05 }) })
    fog(c, t, 0.3 + 0.25 * prog(t, qW, qO), { col: fogCol(d), y0: 500, y1: 1000 })
    const tp = prog(t, qO - 0.2, qO + 0.6)
    if (tp > 0) {
      fade(c, tp * 0.66)
      rule(c, 420, 1500, 330, C.paper3, prog(t, qO - 0.2, qO + 0.7))
      text(c, 'THE BATTLE OF', W / 2, 480, F.head(120, 900), C.paper, { track: 16, alpha: prog(t, qO - 0.1, qO + 0.5) })
      text(c, 'NEW ORLEANS', W / 2, 670, F.head(170, 900), C.red2, { track: 14, alpha: prog(t, qO + 0.2, qO + 0.8) })
      rule(c, 420, 1500, 740, C.paper3, prog(t, qO + 0.2, qO + 1.1))
    }
    fade(c, 1 - prog(t, qF + 0.35, qF + 0.9)); finish(c, t, true); return true
  }

  // =============================== 2. why New Orleans ===============================
  const RIV = [[1010, -40], [960, 90], [1050, 200], [930, 310], [1000, 420], [1090, 500], [1010, 590], [1130, 680], [1260, 740], [1400, 850]]
  const along = (p) => { const f = clamp(p) * (RIV.length - 1), i = Math.min(RIV.length - 2, Math.floor(f)), k = f - i; return [lerp(RIV[i][0], RIV[i + 1][0], k), lerp(RIV[i][1], RIV[i + 1][1], k)] }
  function s2(c, t, q, S) {
    const qNot = q('it had not gone'), qSum = q('the summer before') - 0.35, qBurn = q('and burned'), qNow = q('now they wanted') - 0.4, qWho = q('whoever held'), qEv = q('and everything that'), qSent = q('so they sent') - 0.4, qArmy = q('and an army'), qGen = q('and a general') - 0.3
    paper(c, t)
    if (t < qSum + 0.3) {
      // two lines, firing across the page
      const gy = 760
      text(c, 'THE WAR OF 1812', W / 2, 230, F.head(110, 900), C.ink, { track: 12, alpha: prog(t, S.vis + 0.3, S.vis + 1.0) }); rule(c, 560, 1360, 270, C.ink, prog(t, S.vis + 0.5, S.vis + 1.4))
      typeset(c, 'two and a half years', W / 2, 350, F.bodyI(54), C.ink2, prog(t, q('for two and') - 0.2, q('for two and') + 1.0))
      c.strokeStyle = C.ink; c.lineWidth = 5; c.beginPath(); c.moveTo(0, gy); c.lineTo(W, gy); c.stroke(); hatch(c, k => k.rect(0, gy + 2, W, 320), { gap: 9, alpha: 0.25, angle: 0.03, box: [0, gy, W, 320] })
      for (let i = 0; i < 6; i++) {
        const fa = bump(t, S.start + 0.8 + ((i * 0.73) % 2.9) + Math.floor((t - S.start) / 3.2) * 3.2, 0.16), fb = bump(t, S.start + 1.6 + ((i * 1.31) % 2.9) + Math.floor((t - S.start) / 3.2) * 3.2, 0.16)
        const gone = t > qNot + 0.2 + i * 0.35 && i % 2 === 0
        soldier(c, 250 + i * 86, gy, 230, { kind: 'reg', pose: 'aim', kick: -fa * 0.12, down: gone ? prog(t, qNot + 0.2 + i * 0.35, qNot + 0.7 + i * 0.35, 'i') : 0 }); if (!gone) flash(c, 250 + i * 86 + 150, gy - 172, 0.9, fa)
        soldier(c, 1670 - i * 86, gy, 230, { kind: 'brit', pose: 'aim', face: -1, kick: -fb * 0.12 }); flash(c, 1670 - i * 86 - 150, gy - 172, 0.9, fb, -1)
      }
      finish(c, t, false); return false
    }
    if (t < qNow + 0.3) {
      const gy = 800, b = prog(t, qBurn, qBurn + 1.6)
      c.strokeStyle = C.ink; c.lineWidth = 5; c.beginPath(); c.moveTo(0, gy); c.lineTo(W, gy); c.stroke(); hatch(c, k => k.rect(0, gy + 2, W, 280), { gap: 9, alpha: 0.25, angle: 0.03, box: [0, gy, W, 280] })
      if (b > 0) { for (let i = 0; i < 9; i++) { const a = ((t * 0.22 + i / 9) % 1); c.fillStyle = `rgba(58,48,42,${0.42 * (1 - a) * b})`; c.beginPath(); c.arc(700 + (i % 3) * 110 - a * 260, 330 - a * 330 + Math.sin(a * 5 + i) * 20, 50 + a * 120, 0, 7); c.fill() } }
      house(c, 780, gy, 1.55, C.ink, b > 0 ? mix(C.paper2, C.gold2, b) : C.paper2)
      if (b > 0) for (const [fx, fy, k] of [[420, 540, 1.0], [620, 520, 1.2], [960, 520, 1.3], [1130, 545, 0.9], [780, 440, 1.5]]) fire(c, fx, fy, 1.3 * k, t + fx, b * (0.8 + 0.2 * noise(t * 3, fx)))
      for (let i = 0; i < 9; i++) { const x = track(t, [[qSum, 2100 + i * 96], [qBurn + 0.3, 1330 + i * 70, 'o']]); soldier(c, x, gy, 220, { kind: 'brit', face: -1, pose: 'march', walk: x * 0.06, stride: t < qBurn + 0.2 ? 1 : 0 }) }
      text(c, 'Washington, August 1814', W / 2, 160, F.bodyI(58), C.ink2, { alpha: prog(t, qSum + 0.4, qSum + 1.0) })
      finish(c, t, false); return false
    }
    if (t < qSent + 0.3) {
      // the map: the river and its mouth
      const z = 1 + 0.05 * prog(t, qNow, qSent, 'l')
      c.save(); c.translate(W / 2, H / 2); c.scale(z, z); c.translate(-W / 2, -H / 2)
      const sea = k => { k.moveTo(-100, 800); k.bezierCurveTo(300, 700, 600, 800, 900, 740); k.bezierCurveTo(1100, 700, 1200, 820, 1340, 800); k.lineTo(1420, 880); k.lineTo(1470, 800); k.bezierCurveTo(1600, 720, 1800, 760, 2100, 700); k.lineTo(2100, 1200); k.lineTo(-100, 1200); k.closePath() }
      c.fillStyle = C.paper2; c.beginPath(); sea(c); c.fill(); hatch(c, sea, { gap: 12, alpha: 0.3, angle: 0, box: [-100, 600, 2200, 600], wob: 2 }); c.strokeStyle = C.ink; c.lineWidth = 4; c.beginPath(); sea(c); c.stroke()
      c.strokeStyle = C.ink; c.lineWidth = 16; c.lineJoin = 'round'; c.lineCap = 'round'; c.beginPath(); RIV.forEach(([x, y], i) => i ? c.lineTo(x, y) : c.moveTo(x, y)); c.stroke()
      c.strokeStyle = C.paper2; c.lineWidth = 9; c.beginPath(); RIV.forEach(([x, y], i) => i ? c.lineTo(x, y) : c.moveTo(x, y)); c.stroke()
      text(c, 'MISSISSIPPI', 800, 250, F.sc(34), C.ink2, { track: 10, alpha: prog(t, qWho, qWho + 0.6) }); text(c, 'Gulf of Mexico', 520, 930, F.bodyI(50), C.ink2)
      const [nx, ny] = along(0.74), pa = prog(t, qNow + 0.2, qNow + 0.6, 'back')
      c.fillStyle = C.gold; c.strokeStyle = C.ink; c.lineWidth = 5; c.beginPath(); c.arc(nx, ny, 22 * pa, 0, 7); c.fill(); c.stroke(); glow(c, nx, ny, 160 * pa, '201,151,58', 0.35 + 0.1 * Math.sin(t * 3))
      text(c, 'NEW ORLEANS', nx + 60, ny - 26, F.head(64, 900), C.ink, { align: 'left', track: 4, alpha: prog(t, qNow + 0.3, qNow + 0.8) })
      if (t > qEv - 0.6) for (let i = 0; i < 9; i++) { const p = ((t - qEv) * 0.11 + i / 9) % 1; if ((t - qEv + 0.6) * 0.11 + 0.07 < (1 - i / 9) && p > i / 9) continue; const [bx, by] = along(p), a = Math.min(1, p * 8, (1 - p) * 8); c.save(); c.globalAlpha = a; c.fillStyle = C.ink; c.translate(bx, by); c.beginPath(); c.roundRect(-13, -7, 26, 14, 4); c.fill(); c.fillStyle = C.gold; c.fillRect(-6, -4, 12, 8); c.restore() }
      c.restore(); finish(c, t, false); return false
    }
    if (t < qGen + 0.3) {
      const hy = 640
      c.strokeStyle = C.ink; c.lineWidth = 4; c.beginPath(); c.moveTo(0, hy); c.lineTo(W, hy); c.stroke()
      hatch(c, k => k.rect(0, hy + 2, W, 500), { gap: 13, alpha: 0.3, angle: 0, box: [0, hy, W, 500], wob: 3 })
      const sh = [[1500, 560, 0.7, 0], [1150, 590, 0.9, 0], [1700, 640, 1.2, 0.3], [820, 660, 1.3, 0], [1320, 760, 1.9, 0.5], [500, 800, 2.2, 1.0]]
      sh.forEach(([x, y, s, dl], i) => { const xx = x + 900 * (1 - prog(t, qSent - 0.2 + dl * 0.5 + (i > 2 ? (qArmy - qSent) * 0.5 : 0), qSent + 3.4 + dl, 'o')) - (t - qSent) * 9 * s; ship(c, xx, y + s * 20, s, { face: -1, t, col: C.ink, flag: RED }) })
      finish(c, t, false); return false
    }
    const gy = 800
    c.strokeStyle = C.ink; c.lineWidth = 5; c.beginPath(); c.moveTo(0, gy); c.lineTo(W, gy); c.stroke(); hatch(c, k => k.rect(0, gy + 2, W, 280), { gap: 9, alpha: 0.25, angle: 0.03, box: [0, gy, W, 280] })
    const hx = track(t, [[qGen, 1500], [qGen + 2.2, 1010, 'o']])
    horse(c, hx, gy, 3.3, { face: -1, gait: hx * 0.03, stride: t < qGen + 2.1 ? 0.9 : 0, head: 0.06 * Math.sin(t * 1.3), rider: rider('officer', RED) })
    const qP = q('edward pakenham')
    typeset(c, 'Major General Sir Edward Pakenham', W / 2, 210, F.headI(70, 700), C.ink, prog(t, qP - 0.3, qP + 1.2))
    finish(c, t, false); return false
  }

  // =============================== 3. Jackson's army ===============================
  const GROUPS = [['reg', 'A few regulars', 'a few regular'], ['sailor', 'Sailors and Marines', 'sailors and marines'], ['mil', 'Tennessee and Kentucky militia', 'militia from'], ['city', 'Shopkeepers and lawyers', 'shopkeepers'], ['reg', 'Two battalions of free Black men', 'two battalions'], ['none', 'A company of Choctaw', 'a company of choctaw'], ['pirate', 'Lafitte’s pirates', 'and the pirates']]
  function s3(c, t, q, S) {
    const qThin = q('jackson was thin'), qNo = q('and he had no') - 0.3, qBuilt = q('so he built') - 0.3, qGun = q('some of them without'), q5 = q('about five thousand') - 0.4, qNever = q('who had never')
    paper(c, t)
    const gy = 800, pull = prog(t, q5, q5 + 1.2, 'io'), z = lerp(1, 0.86, pull)
    c.save(); c.translate(W / 2, 560); c.scale(z, z); c.translate(-W / 2, -560)
    c.strokeStyle = C.ink; c.lineWidth = 5; c.beginPath(); c.moveTo(-400, gy); c.lineTo(W + 400, gy); c.stroke(); hatch(c, k => k.rect(-400, gy + 2, W + 800, 400), { gap: 9, alpha: 0.25, angle: 0.03, box: [-400, gy, W + 800, 400] })
    const jx = track(t, [[qNo, 960], [qBuilt + 1.2, 210, 'io']]), jh = track(t, [[qNo, 420], [qBuilt + 1.2, 300, 'io']])
    soldier(c, jx, gy, jh, { kind: 'officer', col: C.ink, pose: 'none', bulk: 0.8, walk: jx * 0.04, stride: (t > qNo + 0.1 && t < qBuilt + 1.2) ? 0.7 : 0, face: t > qNo + 0.1 && t < qBuilt + 1.1 ? -1 : 1, arm: 0.5 * prog(t, qBuilt + 1.2, qBuilt + 1.7) * (1 - prog(t, q5 - 1, q5)) })
    const la = prog(t, S.start + 0.6, S.start + 1.4)
    text(c, 'Andrew Jackson', jx, gy + 70, F.headI(lerp(64, 40, prog(t, qNo, qBuilt + 1.2)), 700), C.ink, { alpha: la })
    GROUPS.forEach(([kind, label, cue], g) => {
      const at = q(cue) - 0.25, p = prog(t, at, at + 1.1, 'o'); if (p <= 0) return
      const sx = 470 + g * 205
      for (let k = 0; k < 3; k++) {
        const x = sx + (k - 1) * 52 + (1 - p) * (900 + g * 40), nog = kind === 'mil' && k === 2
        if (kind === 'pirate' && k === 2) { cannon(c, x + 26, gy, 1.5, { col: C.ink }); continue }
        soldier(c, x, gy, 214 + ((g * 7 + k * 13) % 5) * 5, { kind, col: C.ink, pose: nog ? 'none' : 'stand', walk: x * 0.06, stride: p < 1 ? 1 : 0, face: p < 1 ? -1 : 1, bulk: 0.95 + ((g + k) % 3) * 0.08 })
        if (nog) { const a = prog(t, qGun, qGun + 0.4) * (1 - prog(t, q5 - 0.6, q5)); if (a > 0) { c.save(); c.globalAlpha = a; c.strokeStyle = C.red2; c.lineWidth = 4; c.setLineDash([8, 7]); c.beginPath(); c.moveTo(x + 34, gy - 20); c.lineTo(x + 50, gy - 250); c.stroke(); c.restore() } }
      }
      const ws = label.split(' '), half = Math.ceil(ws.length / 2), l1 = ws.length > 2 ? ws.slice(0, half).join(' ') : label, l2 = ws.length > 2 ? ws.slice(half).join(' ') : ''
      text(c, l1, sx, gy + 60, F.body(27), C.ink, { alpha: clamp(p * 2 - 1) }); if (l2) text(c, l2, sx, gy + 94, F.body(27), C.ink, { alpha: clamp(p * 2 - 1) })
    })
    c.restore()
    text(c, 'about 5,000 men', W / 2, 220, F.head(130, 900), C.ink, { track: 6, alpha: prog(t, q5 + 0.2, q5 + 0.8) })
    typeset(c, 'who had never fought together', W / 2, 310, F.bodyI(60), C.red, prog(t, qNever - 0.2, qNever + 1.2))
    finish(c, t, false); return false
  }

  // =============================== the plan of the ground ===============================
  function arrow(c, pts, p, col, lw = 12) {
    p = clamp(p); if (p <= 0) return
    let L = 0; const seg = []; for (let i = 1; i < pts.length; i++) { const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); seg.push(d); L += d }
    let left = L * p, ex = pts[0][0], ey = pts[0][1], ang = 0
    c.save(); c.strokeStyle = col; c.fillStyle = col; c.lineWidth = lw; c.lineJoin = 'round'; c.lineCap = 'butt'; c.beginPath(); c.moveTo(pts[0][0], pts[0][1])
    for (let i = 1; i < pts.length && left > 0; i++) { const k = Math.min(1, left / seg[i - 1]); ex = lerp(pts[i - 1][0], pts[i][0], k); ey = lerp(pts[i - 1][1], pts[i][1], k); ang = Math.atan2(pts[i][1] - pts[i - 1][1], pts[i][0] - pts[i - 1][0]); c.lineTo(ex, ey); left -= seg[i - 1] }
    c.stroke(); c.translate(ex, ey); c.rotate(ang); c.beginPath(); c.moveTo(lw * 2.2, 0); c.lineTo(-lw * 0.6, -lw * 1.7); c.lineTo(-lw * 0.6, lw * 1.7); c.closePath(); c.fill(); c.restore()
  }
  function cross(c, x, y, r, a) { if (a <= 0) return; c.save(); c.globalAlpha = clamp(a); c.strokeStyle = C.ink; c.lineWidth = 10; c.lineCap = 'round'; c.beginPath(); c.moveTo(x - r, y - r); c.lineTo(x - r + 2 * r * clamp(a * 2), y - r + 2 * r * clamp(a * 2)); if (a > 0.5) { c.moveTo(x + r, y - r); c.lineTo(x + r - 2 * r * clamp(a * 2 - 1), y - r + 2 * r * clamp(a * 2 - 1)) } c.stroke(); c.restore() }
  // o: canal, river, swamp, brace, around, brit, guns, a1, a2, b1, lad, dim (each 0..1)
  function plan(c, t, o = {}) {
    const X = 620
    // swamp
    c.fillStyle = C.paper3; c.fillRect(0, 110, W, 180); hatch(c, k => k.rect(0, 110, W, 180), { gap: 8, alpha: 0.28, angle: 0.5, box: [0, 110, W, 180] })
    const r = rng(31); for (let i = 0; i < 30; i++) cypress(c, 30 + i * 66 + r() * 30, 250 + r() * 34, 0.26 + r() * 0.1, C.ink2, i)
    c.strokeStyle = C.ink; c.lineWidth = 4; c.beginPath(); c.moveTo(0, 290); c.lineTo(W, 290); c.stroke()
    // river and the far bank
    c.fillStyle = C.paper3; c.fillRect(0, 830, W, 260)
    c.fillStyle = C.paper2; c.fillRect(0, 700, W, 130); c.strokeStyle = C.ink2; c.lineWidth = 2.5; for (let i = 0; i < 5; i++) { c.beginPath(); for (let x = 0; x <= W; x += 24) { const y = 716 + i * 25 + Math.sin(x * 0.02 + t * 1.2 + i * 2) * 4; x ? c.lineTo(x, y) : c.moveTo(x, y) } c.stroke() }
    c.strokeStyle = C.ink; c.lineWidth = 4; c.beginPath(); c.moveTo(0, 700); c.lineTo(W, 700); c.moveTo(0, 830); c.lineTo(W, 830); c.stroke()
    text(c, 'CYPRESS SWAMP', 1380, 180, F.sc(40), C.ink, { track: 10, alpha: o.swamp ?? 1, stroke: C.paper3, sw: 10 })
    text(c, 'MISSISSIPPI RIVER', 270, 782, F.sc(40), C.ink, { track: 10, alpha: o.river ?? 1, stroke: C.paper2, sw: 10 })
    // the canal and the wall behind it
    const cp = clamp(o.canal ?? 1), y1 = lerp(700, 290, cp)
    if (cp > 0) {
      c.strokeStyle = C.ink3; c.lineWidth = 7; c.beginPath(); c.moveTo(X + 22, 700); c.lineTo(X + 22, y1); c.stroke()
      const wp = clamp(o.wall ?? 0); if (wp > 0) { c.strokeStyle = C.ink; c.lineWidth = 16; c.beginPath(); c.moveTo(X, 700); c.lineTo(X, lerp(700, 290, wp)); c.stroke(); for (let y = 320; y < 690; y += 30) if (y > lerp(700, 290, wp)) { c.fillStyle = C.ink; c.fillRect(X - 34, y, 12, 12) } }
      c.save(); c.translate(X + 62, 500); c.rotate(-Math.PI / 2); text(c, 'the old canal', 0, 0, F.bodyI(38), C.ink2, { alpha: cp * (1 - clamp(o.lad ?? 0)) }); c.restore()
    }
    const bp = clamp(o.brace ?? 0)
    if (bp > 0) { c.save(); c.globalAlpha = bp; c.strokeStyle = C.ink; c.lineWidth = 3; c.beginPath(); c.moveTo(X - 80, 296); c.lineTo(X - 100, 296); c.lineTo(X - 100, 694); c.lineTo(X - 80, 694); c.stroke(); c.translate(X - 124, 495); c.rotate(-Math.PI / 2); text(c, 'less than a mile', 0, 0, F.headI(44, 700), C.ink); c.restore() }
    const ar = clamp(o.around ?? 0)
    if (ar > 0) { arrow(c, [[1300, 420], [900, 380], [760, 320]], ar * 1.2, C.red2, 10); arrow(c, [[1300, 560], [900, 620], [760, 672]], ar * 1.2 - 0.2, C.red2, 10); cross(c, 720, 304, 26, ar * 2 - 1); cross(c, 720, 688, 26, ar * 2 - 1.2) }
    const br = clamp(o.brit ?? 0)
    if (br > 0) { c.save(); c.globalAlpha = br; c.fillStyle = C.red2; for (const y of [330, 450, 570]) c.fillRect(1500, y, 70, 100); c.restore(); text(c, 'the British', 1600, 492, F.bodyI(42), C.red, { alpha: br, align: 'left' }) }
    const gp = clamp(o.guns ?? 0)
    if (gp > 0) { c.save(); c.globalAlpha = gp; for (const gx of [420, 520, 620]) cannon(c, gx, 905, 0.62, { col: C.ink, elev: 1.1 - 1.4 * clamp(o.turn ?? 0) * 0 }); c.restore(); text(c, 'American guns', 520, 950, F.bodyI(36), C.ink, { alpha: gp }) }
    const dim = clamp(o.dim ?? 0)
    c.save(); c.globalAlpha = lerp(1, 0.3, dim)
    arrow(c, [[1490, 690], [1320, 770], [1060, 872], [720, 880]], o.a1 ?? 0, C.red2, 13)
    arrow(c, [[540, 850], [540, 600], [590, 520]], o.a2 ?? 0, C.red2, 13)
    for (const y of [380, 500, 620]) arrow(c, [[1480, y], [720, y]], o.b1 ?? 0, C.red2, 16)
    const lp = clamp(o.lad ?? 0); if (lp > 0) { c.globalAlpha *= lp; for (const y of [360, 480, 600]) { ladder(c, X + 44, y + 22, 60, Math.PI, C.red, 4); ladder(c, X + 44, y - 22, 60, Math.PI, C.red, 4) } }
    c.restore()
    if (dim > 0) { cross(c, 1060, 850, 44, o.x1 ?? 0); cross(c, 540, 660, 40, o.x2 ?? 0); cross(c, 1080, 500, 60, o.x3 ?? 0) }
  }

  // =============================== 4. the wall ===============================
  function s4(c, t, q, S) {
    const qCan = q('an old canal'), qRiv = q('from the river'), qSw = q('to a cypress'), qLess = q('less than a mile'), qNo = q('and no way'), qBeh = q('behind that ditch') - 0.4, qEn = q('enslaved men'), qTwo = q('for two weeks'), qGun = q('with cannon'), qSt = q('then they stood') - 0.4, qWait = q('and waited')
    if (t < qBeh + 0.3) {
      paper(c, t)
      text(c, 'the ground Jackson picked', W / 2, 74, F.headI(52, 700), C.ink, { alpha: prog(t, S.vis + 0.3, S.vis + 0.9) })
      plan(c, t, { canal: prog(t, qCan, qCan + 1.4, 'io'), river: prog(t, qRiv, qRiv + 0.5), swamp: prog(t, qSw, qSw + 0.5), brace: prog(t, qLess - 0.1, qLess + 0.5), around: prog(t, qNo - 0.2, qNo + 1.6), brit: prog(t, qNo - 0.5, qNo) })
      finish(c, t, false); return false
    }
    if (t < qGun - 0.3) {
      const p = track(t, [[qBeh, 0.3], [qTwo, 0.6, 'l'], [qGun - 0.3, 1, 'l']]), d = 1
      view(c, { cx: 700 + 40 * prog(t, qBeh, qGun, 'l'), cy: 600, s: 1.3, d }, () => {
        stubble(c, 900, 2400, d)
        wall(c, 760, GY, 124, { col: INK, p, water: '#b9b39c' })
        // men digging
        const dig = (x, y, ph, face, kind) => { const a = 0.5 + 0.5 * Math.sin(t * 3.2 + ph); person(c, x, y, 190, { hat: 'none', col: INK, face, lean: 0.07 + 0.1 * a, arm: 0.12 + 0.3 * a, hold: (k) => { k.save(); k.translate(0, 30); k.rotate(-0.5 + a * 0.5); k.fillStyle = INK; k.fillRect(-3, -40, 6, 78); k.beginPath(); k.moveTo(-9, 36); k.lineTo(9, 36); k.lineTo(7, 58); k.lineTo(-7, 58); k.closePath(); k.fill(); k.restore() } }) }
        dig(850, GY + 58, 0, -1); dig(930, GY + 58, 2.1, -1); dig(452, GY + 4, 1.0, 1); dig(366, GY + 4, 3.3, 1)
        for (let i = 0; i < 4; i++) { const a = ((t * 0.8 + i * 0.25) % 1); c.fillStyle = INK; c.beginPath(); c.arc(lerp(850, 730, a), GY + 10 - Math.sin(a * Math.PI) * (130 + 60 * p) - 50 * a * p, 7, 0, 7); c.fill() }
        cypress(c, -60, GY + 8, 1.1, INK, 4)
      })
      finish(c, t, false); return false
    }
    const d = track(t, [[qGun, 0.95], [qSt, 0.8, 'l'], [S.out, 0.34, 'l']])
    view(c, { cx: 960, cy: 870, s: 1.45 + 0.1 * prog(t, qGun, S.out, 'l'), d }, () => { stubble(c, -300, 2400, d, 9); lineF(c, t, { water: mix('#39414d', '#b9b39c', d), muz: prog(t, qGun - 0.1, qGun + 0.8, 'back'), men: prog(t, qSt - 0.2, qSt + 1.6) * 1.05 }) })
    fog(c, t, 0.25 * prog(t, qWait, S.out), { col: fogCol(d), y0: 600, y1: 1000 })
    finish(c, t, false); return d < 0.5
  }

  // =============================== 5. the plan, and what became of it ===============================
  function s5(c, t, q, S) {
    const qOne = q('one force would'), qTake = q('take the american'), qTurn = q('and turn them'), qMain = q('then the main army'), qFill = q('fill the ditch'), qLad = q('throw ladders'), qNone = q('almost none') - 0.3, qBoat = q('the boats got stuck') - 0.4, qLate = q('and the river force'), qReg = q('and the regiment') - 0.4, qPast = q('marched right past'), qBy = q('by the time') - 0.4, qCh = q('pakenham had a choice'), qCall = q('call it off'), qGo = q('or go anyway'), qFire = q('he fired')
    if (t < qBoat + 0.3) {
      paper(c, t)
      text(c, 'Pakenham’s plan', W / 2, 74, F.headI(52, 700), C.red, { alpha: prog(t, S.vis + 0.3, S.vis + 0.9) * (1 - prog(t, qNone, qNone + 0.4)) })
      text(c, 'almost none of it happened', W / 2, 74, F.headI(52, 700), C.ink, { alpha: prog(t, qNone + 0.2, qNone + 0.7) })
      plan(c, t, { wall: 1, brit: 1, guns: prog(t, qTake - 0.4, qTake + 0.2), a1: prog(t, qOne + 0.3, qTake + 1.0, 'io'), a2: prog(t, qTurn, qTurn + 1.0, 'io'), b1: prog(t, qMain + 0.4, qFill + 0.4, 'io'), lad: prog(t, qFill, qLad + 0.6), dim: prog(t, qNone, qNone + 0.6), x1: prog(t, qNone + 0.1, qNone + 0.6), x2: prog(t, qNone + 0.4, qNone + 0.9), x3: prog(t, qNone + 0.7, qNone + 1.2) })
      finish(c, t, false); return false
    }
    if (t < qReg + 0.3) {
      // the boats, stuck in the cut
      const d = 0.1
      view(c, { cx: 960 + 30 * prog(t, qBoat, qReg, 'l'), cy: 620, s: 1.15, d }, () => {
        c.fillStyle = '#0a0b0b'; c.beginPath(); c.moveTo(-300, GY + 2); c.lineTo(560, GY + 2); c.lineTo(640, GY + 120); c.lineTo(1500, GY + 120); c.lineTo(1580, GY + 2); c.lineTo(2400, GY + 2); c.lineTo(2400, 1400); c.lineTo(-300, 1400); c.closePath(); c.fill()
        c.fillStyle = '#39414d'; c.fillRect(1180, GY + 96, 330, 24)
        const tug = Math.max(0, Math.sin(t * 2.2)) ** 2
        for (const [bx, rot] of [[900, 0.07], [1240, -0.04]]) { c.save(); c.translate(bx + tug * 5, GY + 112); c.rotate(rot); c.fillStyle = '#2b2620'; c.beginPath(); c.moveTo(-170, -40); c.lineTo(170, -40); c.quadraticCurveTo(160, 6, 110, 8); c.lineTo(-120, 8); c.quadraticCurveTo(-160, 4, -170, -40); c.closePath(); c.fill(); c.restore() }
        c.strokeStyle = C.red; c.lineWidth = 4; c.beginPath(); c.moveTo(735 + tug * 5, GY + 74); c.lineTo(450, GY - 96); c.stroke()
        for (let i = 0; i < 5; i++) soldier(c, 240 + i * 70 - tug * 8, GY + 4, 186, { kind: 'brit', col: C.red, pose: 'none', face: -1, lean: 0.13 + tug * 0.05, arm: -0.3, walk: 0.9 + i * 0.5, stride: 0.9 })
        for (let i = 0; i < 4; i++) soldier(c, 1090 + i * 66 - tug * 5, GY + 116, 180, { kind: 'brit', col: C.red, pose: 'none', face: -1, lean: 0.13 + tug * 0.05, arm: 0.55, walk: 0.9 + i * 0.6, stride: 0.8 })
      })
      typeset(c, 'hours late', W / 2, 250, F.headI(110, 700), C.paper2, prog(t, qLate + 0.6, qLate + 1.6), { shadow: '#000' })
      fade(c, 1 - prog(t, qBoat + 0.3, qBoat + 0.7)); finish(c, t, true); return true
    }
    if (t < qBy + 0.3) {
      const d = 0.16
      view(c, { cx: track(t, [[qReg, 1500], [qBy, 1180, 'sine']]), cy: 610, s: 1.2, d }, () => {
        stubble(c, -300, 3000, d)
        for (let i = 0; i < 12; i++) { const x = 2500 + i * 92 - (t - qReg) * 250; soldier(c, x, GY + 6, 190, { kind: 'brit', col: C.red, face: -1, pose: 'march', walk: x * 0.07, stride: 1 }) }
        // the ladders and the bundles of cane, left where they lay
        c.fillStyle = INK; c.beginPath(); c.moveTo(1500, GY + 6); c.quadraticCurveTo(1640, GY - 70, 1780, GY - 60); c.lineTo(1830, GY + 6); c.closePath(); c.fill()
        const hl = prog(t, qPast, qPast + 0.6)
        for (let k = 0; k < 4; k++) ladder(c, 1820 - k * 10, GY - 6 - k * 26, 300, Math.PI + 0.04 * (k % 2 ? 1 : -1), mix(INK, '#c9973a', hl * 0.9), 7)
        for (const [bx, by] of [[1880, GY + 6], [1960, GY + 6], [1920, GY - 22], [2040, GY + 6]]) bundle(c, bx, by, 1.2, mix(INK, '#8a6a2c', hl * 0.8))
        if (hl > 0) glow(c, 1700, GY - 50, 420, '201,151,58', 0.16 * hl)
      })
      fog(c, t, 0.4, { col: fogCol(d), y0: 500, y1: 1000 })
      fade(c, 1 - prog(t, qReg + 0.3, qReg + 0.7)); finish(c, t, true); return true
    }
    const d = lerp(0.2, 0.34, prog(t, qBy, qFire))
    const rp = prog(t, qFire + 0.5, qFire + 2.4, 'o'), rx = 1650 - 560 * rp, ry = GY - 120 - 880 * rp + 240 * rp * rp
    view(c, { cx: 1180, cy: lerp(580, 470, prog(t, qFire + 0.4, qFire + 2.4, 'io')), s: lerp(1.3, 1.05, prog(t, qFire + 0.4, qFire + 2.4, 'io')), d }, () => {
      stubble(c, -300, 3000, d)
      for (let i = 0; i < 9; i++) soldier(c, 1700 + i * 88, GY + 4, 184, { kind: 'brit', col: C.red, face: -1, pose: 'stand' })
      const turn = prog(t, qCall, qCall + 0.6) * (1 - prog(t, qGo, qGo + 0.5))
      horse(c, 1240, GY + 20, 2.7, { col: INK, face: -1, gait: t * 0.5, stride: 0.04, head: 0.18 * turn + 0.05 * Math.sin(t), rider: rider('officer', C.red, { lean: -0.1 * turn, arm: 0.5 * prog(t, qFire - 0.2, qFire + 0.3), pose: 'none' }) })
      if (rp > 0 && rp < 1) { c.save(); c.strokeStyle = C.gold2; c.lineCap = 'round'; for (let k = 0; k < 26; k++) { const p0 = rp - k * 0.012, p1 = p0 - 0.012; if (p1 < 0) break; c.globalAlpha = (1 - k / 26) * 0.9; c.lineWidth = 9 * (1 - k / 30); c.beginPath(); c.moveTo(1650 - 560 * p0, GY - 120 - 880 * p0 + 240 * p0 * p0); c.lineTo(1650 - 560 * p1, GY - 120 - 880 * p1 + 240 * p1 * p1); c.stroke() } c.restore(); glow(c, rx, ry, 300, '246,199,112', 0.8) }
      const bp = prog(t, qFire + 2.4, qFire + 3.6); if (bp > 0 && bp < 1) { glow(c, rx, ry, 600 * (0.4 + bp), '246,199,112', 0.9 * (1 - bp)); c.save(); c.strokeStyle = C.gold2; c.lineWidth = 4; c.globalAlpha = 1 - bp; for (let k = 0; k < 14; k++) { const a = k / 14 * 6.28, r0 = 30 + 170 * bp; c.beginPath(); c.moveTo(rx + Math.cos(a) * r0 * 0.5, ry + Math.sin(a) * r0 * 0.5 + 60 * bp * bp); c.lineTo(rx + Math.cos(a) * r0, ry + Math.sin(a) * r0 + 90 * bp * bp); c.stroke() } c.restore() }
    })
    fog(c, t, 0.5, { col: fogCol(d), y0: 520, y1: 1000 })
    fade(c, 1 - prog(t, qBy + 0.3, qBy + 0.7)); finish(c, t, true); return true
  }

  window.SCENES = [s1, s2, s3, s4, s5]
  window.NO = { flame, fade, fogCol, lineF, MEN, GAPS, plan, arrow }
})()
