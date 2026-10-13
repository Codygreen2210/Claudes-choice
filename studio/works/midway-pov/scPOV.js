// scPOV.js: the Midway POV sample. Four scenes, each seen through someone's eyes.
(function () {
  const { W, H, clamp, lerp, prog, keys, rng, ell, poly, shade, vgrad, hgrad, rgrad, post, text, label, shake, flashes, count } = PK
  const { carrier, destroyer, fire, blast, splash, flak, plane, planeTop, carrierTop, shotOf } = MWB
  const { view, high, below, wakeTop, low, waterline, down, sbd, tbd, binoc, scope, bridgeWin, rear, gforce, tracers, gauge } = POV
  const SC = window.SCENES = window.SCENES || []
  const tag = (c, s, a) => label(c, s, W / 2, 230, a, 46)
  const io = k => k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2

  // ---------- 0: McClusky's cockpit, twenty thousand feet
  SC[0] = (c, t, q, S) => {
    const sh = shotOf(t, [[0, 'fwd'], [q('your fuel needle') - 0.2, 'fuel'], [q('about thirty') - 0.3, 'side'], [q('the enemy fleet') - 0.3, 'downE'], [q('then you see it') - 0.2, 'wake']])
    if (sh.name === 'fwd') {
      const v = { roll: Math.sin(t * 0.5) * 0.03, pitch: -20 + Math.sin(t * 0.8) * 6, z: 1 }
      view(c, v, c => high(c, t, { sun: [1500, 120], speed: 300 }))
      sbd(c, t, { fuel: 0.27 })
      post(c, { x: 960 }, { rays: 0.1, rayX: 1100, vignette: 0.5 })
      tag(c, 'Lt. Cmdr. Wade McClusky  ·  19,000 ft', prog(t, 3.0, 3.6) * (1 - prog(t, sh.t1 - 0.5, sh.t1)))
    } else if (sh.name === 'fuel') {
      // eyes drop to the panel: the fuel gauge fills the frame
      const k = prog(t, sh.t0, sh.t0 + 1.2, 'io')
      c.fillStyle = vgrad(c, 0, H, '#2e3238', '#121416'); c.fillRect(0, 0, W, H)
      c.save(); c.translate(W / 2, H / 2); const z = lerp(1.6, 2.1, prog(t, sh.t0, sh.t1)); c.scale(z, z); c.translate(-W / 2, -H / 2)
      gauge(c, 560, 540, 150, 0.62, { label: 'ALT' }); gauge(c, 1060, 560, 190, 0.23 + Math.sin(t * 3) * 0.01 - k * 0.02, { label: 'FUEL', red: 0.22 })
      c.restore()
      post(c, { x: 960 }, { rays: false, vignette: 0.75 })
      text(c, 'turn back', 1230, 860, 52, '#e86a50', { italic: true, shadow: 14, alpha: prog(t, q('turn back'), q('turn back') + 0.4) })
    } else if (sh.name === 'side') {
      // look left out of the canopy: the squadron stacked behind you in the sun
      const v = { roll: -0.06 + Math.sin(t * 0.6) * 0.02, pitch: -40 }
      view(c, v, c => { high(c, t, { speed: 300, sun: [400, 100] }); for (let k = 0; k < 9; k++) { const x = 1500 - k * 170 - (k % 3) * 40, y = 330 + k * 34 + Math.sin(t * 1.3 + k) * 6, s = 1.3 - k * 0.11; plane(c, x, y, s, t, { kind: 'sbd', load: 'bomb' }) } })
      c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.fillStyle = vgrad(c, 0, H, '#3c444c', '#2a3036'); poly(c, [[1700, -20], [1820, -20], [1960, 1100], [1800, 1100]]); c.fill(); c.fillRect(-20, 920, W + 40, 200); c.fillStyle = 'rgba(255,255,255,0.08)'; c.fillRect(-20, 920, W + 40, 5); c.restore()
      post(c, { x: 960 }, { rays: 0.14, rayX: 200, vignette: 0.5 })
      tag(c, 'about 30 dive bombers behind you', prog(t, q('about thirty'), q('about thirty') + 0.4) * (1 - prog(t, sh.t1 - 0.5, sh.t1)))
    } else {
      // look down over the side: empty sea through broken cloud; then a thin white line
      const k = prog(t, sh.t0, sh.t1)
      const wake = sh.name === 'wake'
      const bank = wake ? prog(t, q('you follow it'), q('you follow it') + 1.6, 'io') : 0
      const v = { roll: 0.1 + bank * 0.35, yaw: bank * 160, pitch: 0, z: wake ? lerp(1.0, 1.9, prog(t, q('one thin white'), q('a japanese destroyer') + 1, 'io')) : 1 }
      view(c, v, c => below(c, t, { drift: 40, inner: wake ? c => wakeTop(c, 1100, 520, 1.1, -1.25, t) : null }))
      c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.fillStyle = vgrad(c, 780, H, '#3c444c', '#1e2328'); c.beginPath(); c.moveTo(-20, 1100); c.lineTo(-20, 780); c.quadraticCurveTo(500, 900, 980, 1100); c.closePath(); c.fill()
      c.fillStyle = vgrad(c, 700, 900, '#5a6a7a', '#3a4652'); poly(c, [[1300, 1100], [1980, 760], [1980, 1100]]); c.fill(); c.restore()
      post(c, { x: 960 }, { rays: false, vignette: 0.55 })
      if (wake) tag(c, 'a destroyer, racing north', prog(t, q('a japanese destroyer'), q('a japanese destroyer') + 0.4) * (1 - prog(t, q('you follow it') - 0.2, q('you follow it'))))
      else tag(c, 'nothing but ocean', prog(t, q('nothing below'), q('nothing below') + 0.4))
    }
  }

  // ---------- 1: Nagumo's bridge and binoculars
  SC[1] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'bridge'], [q('all morning') - 0.3, 'binoc'], [q('your fighters are all') - 0.3, 'low'], [q('nobody is watching') - 0.3, 'sky']])
    const u = t - S.vis
    if (sh.name === 'bridge' || sh.name === 'low') {
      const v = { pitch: Math.sin(t * 0.4) * 8, yaw: sh.name === 'low' ? lerp(-60, 80, prog(t, sh.t0, sh.t1)) : lerp(0, -40, prog(t, sh.t0, sh.t1)) }
      view(c, v, c => low(c, t, { H0: 420, speed: 20, inner: (c, H0) => {
        carrier(c, 1600, H0 + 70, 0.28, t, { jp: true, island: 'left' }); carrier(c, 250, H0 + 60, 0.22, t, { jp: true })
        // the flight deck below the window: Zeros warming up, crew
        c.fillStyle = vgrad(c, 740, 1100, '#a07e54', '#7a5c3a'); poly(c, [[-200, 1100], [300, 740], [1700, 740], [2200, 1100]]); c.fill()
        c.strokeStyle = 'rgba(255,255,255,0.6)'; c.lineWidth = 6; c.beginPath(); c.moveTo(1000, 740); c.lineTo(1060, 1100); c.stroke()
        if (sh.name === 'bridge') for (let k = 0; k < 4; k++) plane(c, 560 + k * 300, 860 + k * 12, 0.7 + k * 0.08, t, { kind: 'zero' })
        if (sh.name === 'low') for (let k = 0; k < 5; k++) { const p = ((u * 0.12 + k * 0.2) % 1); plane(c, lerp(-200, 2200, p), H0 + 30 + k * 8, 0.3, t, { kind: 'zero' }) }
      } }))
      bridgeWin(c, t)
      post(c, { x: 960 }, { rays: 0.08, rayX: 1300, vignette: 0.55 })
      if (sh.name === 'bridge') tag(c, 'Vice Adm. Chuichi Nagumo  ·  aboard Akagi', prog(t, q('admiral nagumo'), q('admiral nagumo') + 0.5) * (1 - prog(t, sh.t1 - 0.5, sh.t1)))
      else tag(c, 'the fighters, all down low', prog(t, q('down low'), q('down low') + 0.4))
    } else if (sh.name === 'binoc') {
      const k = prog(t, sh.t0, sh.t1), hitT = [q('knocked them') + 0.2, q('one after another') + 0.1, q('one after another') + 0.8]
      view(c, { z: 2.4, pitch: -10, yaw: lerp(-80, 120, k) }, c => low(c, t, { H0: 470, speed: 10, inner: (c, H0) => {
        flak(c, t, 300, H0 - 160, 1300, 120, 10, 9)
        for (let j = 0; j < 4; j++) { const p = ((u * 0.05 + j * 0.25) % 1), hit = hitT[j] && t > hitT[j]; plane(c, lerp(1700, 200, p), H0 + 12 - j * 6 + (hit ? (t - hitT[j]) * 20 : 0), 0.32, t, { kind: 'tbd', load: 'torpedo', f: -1, smoke: hit, ang: hit ? -0.4 : 0 }) }
        for (let j = 0; j < 3; j++) plane(c, lerp(1900, 300, ((u * 0.09 + j * 0.33) % 1)), H0 - 30 - j * 14, 0.26, t, { kind: 'zero', f: -1 })
        hitT.forEach((h, i) => splash(c, 700 + i * 260, H0 + 20, 0.5, (t - h - 0.5) / 1.4))
        if (t > q('not one torpedo') - 0.4) { const w = prog(t, q('not one torpedo') - 0.4, q('not one torpedo') + 2.5); for (let j = 0; j < 20; j++) ell(c, lerp(500, 1500, w) - j * 30, H0 + 60 + j * 0.6, 26, 3, 0, `rgba(245,250,255,${0.7 - j * 0.03})`) }
      } }))
      binoc(c, t)
      post(c, { x: 960 }, { rays: false, vignette: 0.3 })
      tag(c, 'not one torpedo has hit', prog(t, q('not one torpedo'), q('not one torpedo') + 0.4))
    } else {
      // tilt up: an empty blue sky... and, high in the sun, glints
      const k = prog(t, sh.t0, sh.t0 + 1.4, 'io')
      view(c, { z: 2.2, pitch: lerp(-10, -700, k) }, c => low(c, t, { H0: 470, speed: 10, inner: (c, H0) => {} }))
      c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.fillStyle = rgrad(c, 1300, 300, 10, 700, 'rgba(255,244,220,0.85)', 'rgba(255,240,210,0.25)', 'rgba(255,240,210,0)'); c.fillRect(0, 0, W, H)
      const g = prog(t, q('the sky') + 0.4, q('the sky') + 1.2); for (let j = 0; j < 9; j++) { const x = 1080 + j * 46 + Math.sin(t + j) * 2, y = 360 + (j % 3) * 22 - j * 6, tw = 0.5 + 0.5 * Math.sin(t * 9 + j * 2); c.globalAlpha = g; planeTop(c, x, y, 0.12, 0.3, { col: '#2a323a' }); c.globalAlpha = 1; ell(c, x, y, 12 * tw, 12 * tw, 0, `rgba(255,255,255,${0.7 * g * tw})`) } c.restore()
      binoc(c, t)
      post(c, { x: 960 }, { rays: false, vignette: 0.3 })
    }
  }

  // ---------- 2: George Gay, low and straight into the guns, then the sea
  SC[2] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'run'], [q('every plane in') - 0.1, 'hit'], [q('yours too') + 0.15, 'water']])
    if (sh.name === 'run' || sh.name === 'hit') {
      const u = t - S.vis, k = prog(t, S.vis, q('yours too') + 0.15)
      const hit = sh.name === 'hit' ? prog(t, sh.t0, sh.t1) : 0
      const [sx, sy] = shake(t, [q('right into') + 0.2, q('the guns') + 0.1, sh.name === 'hit' ? q('every plane') + 0.3 : 1e9, sh.name === 'hit' ? q('yours too') - 0.4 : 1e9], 18)
      const v = { roll: Math.sin(t * 1.7) * 0.02 + hit * hit * 0.9, pitch: -hit * hit * 260 + sy, yaw: sx }
      view(c, v, c => low(c, t, { H0: 440, speed: 140, inner: (c, H0) => {
        const s = lerp(0.35, 1.25, k * k), cx = 1000 - k * 60
        carrier(c, cx, H0 + 30 + s * 30, s, t, { jp: true, island: 'left' })
        flak(c, t, 200, H0 - 340, 1500, 300, 12, 13)
        for (let j = 0; j < 8; j++) splash(c, 300 + j * 190, H0 + 60 + (j % 3) * 50, 0.8, ((u * 0.5 + j * 0.13) % 1))
        tracers(c, t, cx - 100 * s, H0 - 40 * s, 10, 7)
        for (let j = 0; j < 2; j++) { const p = ((u * 0.15 + j * 0.5) % 1); plane(c, lerp(-100, 900, p), H0 + 40 + j * 20, 0.5, t, { kind: 'tbd', load: 'torpedo', smoke: j === 0 && u > 6, ang: j === 0 && u > 6 ? 0.2 : 0 }) }
        plane(c, lerp(1900, 200, ((u * 0.2) % 1)), H0 - 140, 0.55, t, { kind: 'zero', f: -1 })
      } }))
      tbd(c, t, { cracks: hit > 0.25 ? 1 : 0 })
      if (hit > 0) { c.save(); c.setTransform(1, 0, 0, 1, 0, 0); for (let j = 0; j < 10; j++) ell(c, 1500 - j * 60 + Math.sin(t * 4 + j) * 20, 600 - j * 30, 90 + j * 30, 70 + j * 24, 0, `rgba(30,26,24,${0.55 * hit})`); c.fillStyle = `rgba(240,248,255,${prog(t, sh.t1 - 0.25, sh.t1)})`; c.fillRect(0, 0, W, H); c.restore() }
      post(c, { x: 960 }, { rays: 0.06, vignette: 0.5 })
      flashes(c, t, [q('right into') + 0.2, q('every plane') + 0.3], '255,230,180', 0.4)
      tag(c, 'Ensign George Gay  ·  Torpedo Squadron Eight', prog(t, q('george gay'), q('george gay') + 0.5) * (1 - prog(t, q('to drop'), q('to drop') + 0.4)))
    } else {
      // in the water: waves in your face, the carriers on the horizon; then you look up
      const look = prog(t, q('you look up') - 0.3, q('you look up') + 0.9, 'io')
      view(c, { pitch: -look * 620, roll: Math.sin(t * 0.9) * 0.04 }, c => waterline(c, t, { H0: 600, sky: (c, H0) => {
        const g = prog(t, q('look up') + 0.2, q('look up') + 0.9); for (let j = 0; j < 12; j++) { const x = 760 + j * 46 + Math.sin(t + j) * 3, y = H0 - 760 + (j % 4) * 20, tw = 0.5 + 0.5 * Math.sin(t * 8 + j); ell(c, x, y, 4, 1.6, 0, `rgba(30,40,50,${0.85 * g})`); ell(c, x, y, 8 * tw, 8 * tw, 0, `rgba(255,255,255,${0.5 * g * tw})`) }
      }, inner: (c, H0) => {
        carrier(c, 1450, H0 + 6, 0.24, t, { jp: true, island: 'left' }); carrier(c, 520, H0 + 4, 0.2, t, { jp: true }); destroyer(c, 1020, H0 + 2, 0.12, t)
        c.save(); c.translate(1180, H0 + 120 + Math.sin(t * 1.4) * 10); c.rotate(0.15 + Math.sin(t) * 0.05); c.fillStyle = '#4a4a44'; c.fillRect(-140, -12, 280, 24); c.restore()
        ell(c, 640, H0 + 150 + Math.sin(t * 1.2 + 1) * 12, 70, 18, 0.1, '#8a7a5a')
      } }))
      post(c, { x: 960 }, { rays: 0.1, rayX: 900, vignette: 0.55 })
      tag(c, 'of 30 men, one alive', prog(t, q('of thirty men'), q('of thirty men') + 0.4) * (1 - prog(t, q('you float') - 0.3, q('you float'))))
    }
  }

  // ---------- 3: the dive, through McClusky's sight
  SC[3] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'fwd'], [q('you roll over') - 0.1, 'roll'], [q('it grows in') - 0.4, 'sight'], [q('release') + 0.15, 'pull'], [q('you look back') - 0.2, 'back'], [q('but one of them') - 0.3, 'away']])
    const rel = q('release') + 0.15
    if (sh.name === 'fwd') {
      view(c, { roll: Math.sin(t * 0.5) * 0.03, pitch: 60 }, c => high(c, t, { speed: 300, sun: [1500, 120], ships: [{ x: -900, z: 5200 }, { x: 300, z: 6200 }, { x: 1600, z: 5600 }] }))
      sbd(c, t, { fuel: 0.2 })
      post(c, { x: 960 }, { rays: 0.1, rayX: 1100, vignette: 0.5 })
      tag(c, '10:22 a.m.', prog(t, q('it is'), q('it is') + 0.4))
    } else if (sh.name === 'roll') {
      // roll inverted and pull the nose down: the horizon spins and slides away, then the deck below
      const k = prog(t, sh.t0, sh.t0 + 2.2)
      if (k < 1) {
        view(c, { roll: io(clamp(k * 1.4)) * Math.PI, pitch: -io(clamp((k - 0.35) / 0.65)) * 1100 + 60 }, c => high(c, t, { speed: 300, sun: [1500, 120], ships: [{ x: -900, z: 5200 }, { x: 300, z: 6200 }, { x: 1600, z: 5600 }] }))
        c.save(); c.translate(W / 2, H / 2); c.rotate(io(clamp(k * 1.4)) * 0.12); c.translate(-W / 2, -H / 2); sbd(c, t, { fuel: 0.2 }); c.restore()
        if (k > 0.8) { c.fillStyle = `rgba(36,64,90,${(k - 0.8) / 0.2})`; c.fillRect(0, 0, W, H) }
      } else {
        const d = prog(t, sh.t0 + 2.2, sh.t1)
        down(c, t, { k: d * 0.3, rot: 0.6 - d * 0.2, inner: c => carrierTop(c, 0, 0, 0.5, t, { rot: 0 }) })
        scope(c, t, { a: prog(t, sh.t0 + 2.2, sh.t0 + 2.8) })
        tag(c, 'a big red circle', prog(t, q('big red circle'), q('big red circle') + 0.4) * (1 - prog(t, sh.t1 - 0.4, sh.t1)))
      }
      post(c, { x: 960 }, { rays: false, vignette: 0.5 })
    } else if (sh.name === 'sight') {
      const k = prog(t, sh.t0, sh.t1), [sx, sy] = shake(t, [q('fuel hoses'), q('bombs'), q('all out') + 0.2], 10)
      down(c, t, { k: 0.3 + k * 0.7, rot: 0.48 - k * 0.15, dx: sx, dy: sy, rush: 0.9, inner: c => {
        carrierTop(c, 0, 0, 0.5, t, { rot: 0, planes: 8 })
        // fuel hoses snaking across the deck, bombs stacked by the planes
        c.strokeStyle = '#1a1a1a'; c.lineWidth = 3; c.beginPath(); c.moveTo(-300, -30); c.bezierCurveTo(-200, 20, -120, -40, 0, 20); c.bezierCurveTo(80, 50, 140, -10, 220, 30); c.stroke()
        for (let j = 0; j < 6; j++) { c.save(); c.translate(-260 + j * 26, 40); c.scale(0.18, 0.18); MWB.bomb(c, 0, 0, 1); c.restore() }
        flak(c, t, -500, -300, 1000, 600, 12, 19)
      } })
      scope(c, t)
      // altitude unwinding
      const alt = Math.round(lerp(14000, 2000, k) / 100) * 100
      text(c, alt.toLocaleString('en-US') + ' ft', 1640, 900, 44, '#f3e7d0', { weight: 700, shadow: 12 })
      post(c, { x: 960 }, { rays: false, vignette: 0.4 })
      flashes(c, t, [q('fuel hoses'), q('all out') + 0.2], '255,220,160', 0.25)
    } else if (sh.name === 'pull') {
      // the bomb drops away; pull out hard: the deck slides down out of view, the sea and horizon come up, grey-out at the edges
      const k = prog(t, sh.t0, sh.t1)
      if (k < 0.32) {
        const b = k / 0.32
        down(c, t, { z: 2.6, rot: 0.33, inner: c => carrierTop(c, 0, 0, 0.5, t, { rot: 0, planes: 8 }) })
        c.save(); c.translate(W / 2, H / 2 + 60 * b); c.scale(lerp(1.4, 0.3, b), lerp(1.4, 0.3, b)); c.rotate(Math.PI / 2); MWB.bomb(c, 0, 0, 1); c.restore()
        scope(c, t)
      } else {
        const p = io(prog(k, 0.32, 1))
        view(c, { pitch: lerp(-900, 40, p), roll: lerp(0.4, 0.05, p) }, c => low(c, t, { H0: 440, speed: 160, inner: (c, H0) => {
          const u = (t - rel - 1.0) / 1.6; carrier(c, 900, H0 + 300, 1.2, t, { jp: true, island: 'left', fire: clamp((t - rel - 1.2) / 2) })
          blast(c, 860, H0 + 140, 1.4, u)
        } }))
        sbd(c, t, { fuel: 0.15 }); gforce(c, Math.sin(Math.PI * clamp(prog(k, 0.32, 0.9))) * 0.9)
      }
      post(c, { x: 960 }, { rays: false, vignette: 0.5 })
      flashes(c, t, [rel + 1.1], '255,230,180', 0.55)
    } else if (sh.name === 'back') {
      // look back over the tail: the carrier you hit, and two more, burning
      const k = prog(t, sh.t0, sh.t1), [sx, sy] = shake(t, [q('in about five') + 0.4, q('in about five') + 2.4], 8)
      view(c, { pitch: -20 + sy, yaw: sx, roll: Math.sin(t * 0.7) * 0.03, z: lerp(1.05, 1.15, k) }, c => low(c, t, { H0: 460, speed: -40, inner: (c, H0) => {
        carrier(c, 1500, H0 + 40, 0.32, t, { jp: true, fire: 1 }); carrier(c, 380, H0 + 30, 0.26, t, { jp: true, island: 'left', fire: prog(t, q('in about five') + 0.4, q('in about five') + 2) })
        carrier(c, 960, H0 + 90, 0.62, t, { jp: true, island: 'left', fire: 1 }); fire(c, 960, H0 - 10, 300, t, 1)
      } }))
      rear(c, t)
      post(c, { x: 960 }, { rays: 0.06, grade: 'rgba(200,100,60,0.22)', vignette: 0.5 })
      if (t > q('in about five')) count(c, W / 2, 200, 'about 5 minutes', 92)
    } else {
      // the one that got away: the Hiryu, far off under the clouds, turning her planes into the wind
      const k = prog(t, sh.t0, sh.t1)
      view(c, { pitch: -10, yaw: lerp(-40, 60, k), z: lerp(1.0, 1.25, k) }, c => low(c, t, { H0: 470, speed: 6, inner: (c, H0) => {
        c.fillStyle = vgrad(c, H0 - 330, H0 - 40, 'rgba(90,100,112,0)', 'rgba(90,100,112,0.45)', 'rgba(90,100,112,0)'); c.fillRect(-1600, H0 - 330, 5200, 290)
        carrier(c, 1250, H0 + 30, 0.3, t, { jp: true, island: 'left' })
        for (let j = 0; j < 5; j++) { const p = prog(t, q('and it was coming') - 0.4 + j * 0.35, q('and it was coming') + 3 + j * 0.35); if (p > 0) plane(c, lerp(1250, 1900, p), H0 - p * 260, 0.2, t, { kind: 'kate', ang: -0.25 }) }
        for (let j = 0; j < 3; j++) { carrier(c, -100 + j * 260, H0 + 10, 0.12, t, { jp: true, planes: 0 }); fire(c, -100 + j * 260, H0 + 4, 80, t, 0.3) }
      } }))
      post(c, { x: 960 }, { rays: 0.12, rayX: 900, grade: 'rgba(120,130,160,0.2)', vignette: 0.6 })
      tag(c, 'Hiryu', prog(t, q('got away'), q('got away') + 0.4))
    }
  }
})()
