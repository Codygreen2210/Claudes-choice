// scB2.js: scenes 7-12 of The Champawat Tiger, Style B.
(function () {
  const { W, H, clamp, lerp, prog, keys, rng, ell, poly, shade, vgrad, hgrad, rgrad, layer, fog, post, foreground, tuft, person, crowd, beast, birds, tree, forest, house, river, brush, paper, map, pathLine, train, camera, count, text, label, shake, flashes } = PK
  const { hills, village, ground, gorge, CREST, ravine, ravineLip, R, shotOf, muzzle } = CWB
  const SC = window.SCENES = window.SCENES || []

  // ---------- 7: Premka Devi; the ravine at Phungar
  SC[7] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'girl'], [q('she did not come back') - 0.2, 'gone'], [q('corbett picked up') - 0.3, 'trail'], [q('it went down') - 0.3, 'ravineWide'], [q('a little earth') - 0.25, 'earth'], [q('she was right there') - 0.3, 'tiger'], [q('he swung') - 0.3, 'fire'], [q('she disappeared') + 0.1, 'gone2'], [q('it was getting dark') - 0.3, 'dark'], [q('he went back') - 0.3, 'back']])
    const qKnelt = q('and as he knelt'), qWatched = q('being watched'), qEarth = q('a little earth'), qHead = q('above his head'), qThere = q('she was right there'), qClose = q('close enough'), qSwung = q('he swung'), qUp = q('rifle up'), qF1 = q('fired twice') + 0.05, qF2 = q('fired twice') + 0.4, qGone = q('she disappeared')
    if (sh.name === 'girl' || sh.name === 'gone') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 650, z: 1.35 }], [sh.t1, { x: 1060, y: 640, z: 1.45 }]])
      hills(c, cam, t, { tod: 'day', seed: 6 })
      layer(c, cam, 0.85, c => forest(c, -800, 3000, 770, 230, { seed: 31, fade: 0.1, hazeCol: '#a9b5b5', t }))
      layer(c, cam, 1, c => {
        ground(c, 900, { col: '#5e5a3a', seed: 20 })
        poly(c, [[-600, 960], [600, 930], [1400, 905], [2200, 880], [2200, 920], [1400, 950], [600, 985], [-600, 1030]], 'rgba(150,120,80,0.5)')
        if (sh.name === 'girl') { const d = (t - sh.t0) * 55; person(c, 600 + d, 940, 0.55, { cos: 'girl', pose: { name: 'walk', d } }) }
        else { // the path, empty; a few sticks of firewood dropped on it
          c.strokeStyle = '#6a4a2a'; c.lineWidth = 7; c.lineCap = 'round'; for (let k = 0; k < 4; k++) { c.beginPath(); c.moveTo(1240 + k * 14, 930 - k * 3); c.lineTo(1320 + k * 10, 922 + k * 4); c.stroke() }
        }
      })
      layer(c, cam, 1.35, c => foreground(c, t))
      post(c, cam, { rays: 0.14 })
      return
    }
    if (sh.name === 'trail') {
      const u = t - sh.t0, cam = { x: 700 + u * 70, y: 660, z: 1.5 }
      hills(c, cam, t, { tod: 'dusk', seed: 6 })
      layer(c, cam, 0.85, c => forest(c, -800, 3000, 780, 237, { seed: 32, fade: 0.15, hazeCol: '#a9a2a0', t }))
      layer(c, cam, 1, c => { ground(c, 900, { col: '#4e4a32', seed: 21 }); for (let k = 0; k < 8; k++) ell(c, 600 + k * 140, 930 + (k % 2) * 16, 14, 9, 0, 'rgba(40,28,16,0.5)'); person(c, 500 + u * 70, 920, 0.62, { cos: 'corbett', pose: { name: 'walk', d: u * 70 + 0, item: 'rifle' }, face: { look: -0.25 } }) })
      layer(c, cam, 1.35, c => foreground(c, t))
      post(c, cam, { rays: 0.16, rayX: 200, grade: 'rgba(120,60,90,0.18)' })
      return
    }
    // the ravine shots share one world
    let cam
    if (sh.name === 'ravineWide') cam = keys(t, [[sh.t0, { x: 1080, y: 700, z: 1.35 }], [sh.t1, { x: 1090, y: 700, z: 1.55 }]])
    else if (sh.name === 'earth') cam = keys(t, [[sh.t0, { x: 1110, y: 660, z: 2.0 }], [sh.t1, { x: 1130, y: 590, z: 2.1 }]])
    else if (sh.name === 'tiger') cam = keys(t, [[sh.t0, { x: 1130, y: 640, z: 1.55 }], [qClose, { x: 1150, y: 600, z: 1.65 }], [sh.t1, { x: 1180, y: 540, z: 1.95 }]])
    else if (sh.name === 'fire') cam = { x: 1120, y: 680, z: lerp(1.45, 1.55, prog(t, sh.t0, sh.t1)) }
    else if (sh.name === 'gone2') cam = keys(t, [[sh.t0, { x: 1140, y: 660, z: 1.6 }], [sh.t1, { x: 1160, y: 640, z: 1.7 }]])
    else if (sh.name === 'dark') cam = keys(t, [[sh.t0, { x: 1100, y: 640, z: 1.4 }], [sh.t1, { x: 1060, y: 620, z: 1.2 }]])
    else cam = null
    if (cam) {
      const [sx, sy] = shake(t, [qF1, qF2], 14); cam.sx = sx; cam.sy = sy
      const aim = prog(t, qSwung, qUp + 0.2, 'io'), look = Math.max(prog(t, qHead - 0.7, qHead + 0.4, 'io'), aim)
      const alarm = prog(t, qEarth + 0.3, qEarth + 0.8), retreat = prog(t, qGone, qGone + 0.7, 'io'), recoil = prog(t, qF1, qF1 + 0.15) * (1 - retreat)
      const dart = t > qWatched - 0.6 && t < qEarth ? Math.sin((t - qWatched + 0.6) * 4.2) : 0
      const dark = prog(t, q('it was getting dark') - 0.3, q('it was getting dark') + 2.5)
      let m = null
      ravine(c, cam, t, { tod: 'dusk', inner: c => {
        // the tigress: crouched on top of the bank, front paws planted at the edge, looking down at him
        if (t > qThere - 0.6 && retreat < 1) {
          c.save(); c.beginPath(); c.rect(1000, -600, 1800, R.LIPY + 600 + 2); c.clip()
          beast(c, 1300 + retreat * 160, R.LIPY + 2 + retreat * 120 + recoil * 8, 0.62, { kind: 'tiger', f: -1, t, pose: { name: 'crouch', k: 0.85 }, look: 0.55 - recoil * 0.4, mouth: Math.max(prog(t, qClose, qClose + 0.6) * 0.6, prog(t, qSwung, qSwung + 0.3)), alpha: prog(t, qThere - 0.6, qThere) })
          c.restore()
        }
        ravineLip(c, t, prog(t, qGone, qGone + 0.3) * (1 - prog(t, qGone + 2, qGone + 3)) * 0.6)
        const o = person(c, 1060, R.GY + 6, 1.18, { cos: 'corbett', pose: { name: 'kneelAim', k: aim, lean: alarm * 0.04 * (1 - aim) }, target: [1225, 430], face: { look, mood: alarm > 0.5 ? 'alarm' : 'stern', dart } })
        m = o.muzzle
        // falling earth: crumbs drop off the lip, bounce off his hat and fall to the ground
        if (t > qEarth - 0.3 && t < qThere + 2) { const r = rng(7); c.fillStyle = '#4a3422'; for (let k = 0; k < 28; k++) { const t0 = qEarth - 0.25 + k * 0.075 + r() * 0.08, rad = 2.5 + r() * 3.5, x0 = R.LX + 2 + r() * 26, vx = -(25 + r() * 45); if (t < t0) continue
          const hat = o.hat, tt = t - t0, yHit = hat[1] - 8, tHit = Math.sqrt(Math.max(0, (yHit - R.LIPY - 16) / 850)), xHit = x0 + vx * tHit
          let x, y; if (tt < tHit || Math.abs(xHit - hat[0]) > 34) { x = x0 + vx * tt; y = Math.min(R.GY + 12, R.LIPY + 16 + 850 * tt * tt) } else { const u = tt - tHit, side = xHit > hat[0] ? 1 : -1; x = xHit + side * 110 * u; y = Math.min(R.GY + 12, yHit - 120 * u + 850 * u * u) }
          ell(c, x, y, rad, rad, 0) } }
        if (m) muzzle(c, t, m, [qF1, qF2])
      } })
      layer(c, cam, 1.35, c => foreground(c, t))
      post(c, cam, { rays: 0.14 * (1 - dark), rayX: 300, night: dark * 0.45, vignette: 0.6 + dark * 0.2 })
      flashes(c, t, [qF1, qF2])
      return
    }
    // back to the village at dusk
    const cam2 = keys(t, [[sh.t0, { x: 900, y: 680, z: 1.4 }], [sh.t1, { x: 980, y: 680, z: 1.5 }]])
    hills(c, cam2, t, { tod: 'night', seed: 6 })
    village(c, cam2, t, { tod: 'night', litAll: true })
    layer(c, cam2, 1, c => { const d = (t - sh.t0) * 50; person(c, 500 + d, 900, 0.5, { cos: 'corbett', pose: { name: 'walk', d, item: 'rifle' }, fade: 0.3, hazeCol: '#1a2234' }) })
    post(c, cam2, { night: 0.15 })
  }

  // ---------- 8: the plan
  function gorgeMap(c, t, k, o = {}) {
    map(c, W / 2, H / 2 - 20, 1500, 860, { draw: (c, w, h) => {
      // the ridge (hatched) along the top, the gorge floor and river below, Corbett's place marked
      c.fillStyle = 'rgba(110,80,40,0.25)'; c.beginPath(); c.moveTo(-660, -300); c.bezierCurveTo(-200, -360, 200, -260, 660, -320); c.lineTo(660, -60); c.bezierCurveTo(200, 0, -200, -80, -660, -40); c.closePath(); c.fill()
      c.strokeStyle = 'rgba(90,60,30,0.28)'; c.lineWidth = 2; for (let x = -640; x < 640; x += 60) { c.beginPath(); c.moveTo(x, -300 + Math.sin(x * 0.01) * 20); c.lineTo(x + 10, -110 + Math.sin(x * 0.01) * 20); c.stroke() }
      c.strokeStyle = '#5a7a8a'; c.lineWidth = 10; c.beginPath(); c.moveTo(-660, 200); c.bezierCurveTo(-200, 160, 200, 260, 660, 210); c.stroke()
      text(c, 'Champa river', 380, 270, 30, '#3a5a6a', { italic: true })
      // the line of men on the ridge, moving down as k grows
      for (let i = 0; i < 26; i++) { const x = -600 + i * 48, y = -280 + Math.sin(x * 0.01) * 20 + k * 150; ell(c, x, y, 7, 7, 0, '#3a2a1a') }
      if (o.tiger) { const a = prog(t, o.tiger, o.tiger + 0.5); ell(c, -60, 90 + k * 30, 16, 10, 0, `rgba(217,116,28,${a})`); text(c, 'tigress', -60, 50 + k * 30, 30, `rgba(58,40,24,${a})`, { italic: true }) }
      if (o.corbett) { const a = prog(t, o.corbett, o.corbett + 0.5); c.strokeStyle = `rgba(138,42,30,${a})`; c.lineWidth = 7; c.beginPath(); c.moveTo(-90, 140); c.lineTo(-40, 180); c.moveTo(-40, 140); c.lineTo(-90, 180); c.stroke(); text(c, 'Corbett', -65, 230, 34, `rgba(138,42,30,${a})`, { weight: 800 }) }
      if (o.arrow) { const a = prog(t, o.arrow, o.arrow + 0.5); pathLine(c, [[-60, 90], [-62, 140]], a, '#8a2a1e', 5, [8, 8]) }
    } })
  }
  SC[8] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'dawn'], [q('she was resting') - 0.3, 'rest'], [q('the tahsildar went') - 0.3, 'men'], [q('they would spread') - 0.3, 'map']])
    if (sh.name === 'dawn') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 680, z: 1.6 }], [sh.t1, { x: 980, y: 670, z: 1.75 }]])
      hills(c, cam, t, { tod: 'dawn' }); village(c, cam, t, { tod: 'dawn' })
      layer(c, cam, 1, c => { ground(c, 900, { col: '#6a5a3e', seed: 22 }); person(c, 860, 915, 0.66, { cos: 'corbett', pose: { name: 'point' }, target: [1500, 600], face: { talk: t } }); person(c, 1120, 912, 0.66, { cos: 'tahsildar', pose: { name: 'stand' }, f: -1 }) })
      layer(c, cam, 1.35, c => foreground(c, t))
      post(c, cam, { rays: 0.18, rayX: 100, grade: 'rgba(200,120,100,0.15)' })
    } else if (sh.name === 'rest') {
      const cam = keys(t, [[sh.t0, { x: 1560, y: 820, z: 2.2 }], [sh.t1, { x: 1580, y: 830, z: 2.4 }]])
      gorge(c, cam, t, { beaters: false, inner: c => { beast(c, 1560, 905, 0.55, { kind: 'tiger', f: -1, t, pose: { name: 'lie' } }); brush(c, 1380, 925, 440, 110, t, { seed: 41 }) } })
      post(c, cam, { rays: 0.12 })
      label(c, 'The Champa gorge', W / 2, 110, prog(t, sh.t0 + 0.3, sh.t0 + 1) * (1 - prog(t, sh.t1 - 0.8, sh.t1 - 0.2)))
    } else if (sh.name === 'men') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 640, z: 1.25 }], [sh.t1, { x: 1000, y: 660, z: 1.4 }]])
      hills(c, cam, t, { tod: 'day' }); village(c, cam, t, { tod: 'day' })
      layer(c, cam, 1, c => {
        ground(c, 880, { col: '#6a5a3e', seed: 23 })
        const r = rng(9), men = []; for (let k = 0; k < 30; k++) men.push({ x: 120 + r() * 1700, z: r() * 1.2 - 0.6, cos: ['villager', 'villager2', 'villager3'][k % 3], f: r() > 0.5 ? 1 : -1, pose: k % 4 === 0 ? { name: 'drum', t: t + k, bpm: 90 } : { name: 'stand', crouch: 0 } })
        crowd(c, 900, men, { s: 0.42, zy: 70, fade: 0.3 })
        person(c, 960, 990, 0.6, { cos: 'tahsildar', pose: { name: 'raise', k: 0.8 }, face: { mouth: 'shout' } })
      })
      layer(c, cam, 1.35, c => foreground(c, t))
      post(c, cam, { rays: 0.12 })
      count(c, W / 2, 230, Math.round(lerp(0, 298, prog(t, q('gathered every man'), q('298 of them') + 0.4, 'o'))), 150)
      text(c, 'men', W / 2, 330, 46, '#f3e7d0', { italic: true, shadow: 16, alpha: prog(t, q('298 of them'), q('298 of them') + 0.4) })
    } else {
      c.fillStyle = '#1a140e'; c.fillRect(0, 0, W, H)
      gorgeMap(c, t, prog(t, q('and walk down'), q('a tiger driven') + 0.5, 'io'), { tiger: q('a tiger driven'), corbett: q('corbett would be'), arrow: q('moves away') })
      post(c, { x: 960 }, { rays: false, vignette: 0.5 })
    }
  }

  // ---------- 9: the shot
  SC[9] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'drums'], [q('for a long time') - 0.3, 'wait'], [q('then she came out') - 0.3, 'out'], [q('corbett fired') - 0.3, 'fire'], [q('the tahsildar had a gun') - 0.3, 'swap'], [q('she was 20 feet') - 0.3, 'last'], [q('it was over') - 0.2, 'over']])
    const qF1 = q('corbett fired') + 0.35, qF2 = q('he fired again') + 0.4, qClick = q('then his rifle was empty') + 0.3, qF3 = q('when he fired the last') + 0.5
    if (sh.name === 'drums') {
      const cam = keys(t, [[sh.t0, { x: -200, y: 330, z: 2.8 }], [sh.t1, { x: 400, y: 380, z: 2.6 }]], 'l')
      gorge(c, cam, t, {}); post(c, cam, { rays: 0.12 })
      label(c, 'Noon', W / 2, 110, prog(t, sh.t0 + 0.3, sh.t0 + 0.9) * (1 - prog(t, sh.t1 - 0.6, sh.t1 - 0.1)))
      return
    }
    let cam
    if (sh.name === 'wait') cam = keys(t, [[sh.t0, { x: 900, y: 700, z: 1.4 }], [sh.t1, { x: 900, y: 720, z: 1.6 }]])
    else if (sh.name === 'out') cam = keys(t, [[sh.t0, { x: 1300, y: 760, z: 1.7 }], [sh.t1, { x: 1150, y: 760, z: 1.6 }]])
    else if (sh.name === 'fire') cam = keys(t, [[sh.t0, { x: 1000, y: 740, z: 1.35 }], [sh.t1, { x: 950, y: 740, z: 1.45 }]])
    else if (sh.name === 'swap') cam = keys(t, [[sh.t0, { x: 700, y: 740, z: 1.5 }], [sh.t1, { x: 850, y: 740, z: 1.5 }]])
    else if (sh.name === 'last') cam = keys(t, [[sh.t0, { x: 980, y: 760, z: 2.0 }], [sh.t1, { x: 1000, y: 760, z: 2.3 }]])
    else cam = keys(t, [[sh.t0, { x: 1000, y: 700, z: 1.7 }], [sh.t1, { x: 980, y: 650, z: 1.3 }]])
    const [sx, sy] = shake(t, [qF1, qF2, qF3], 12); cam.sx = sx; cam.sy = sy
    // where she is: out of the brush at 'out', hit and turning at F1, coming on, hit at F2, crouched 20 ft away, down at F3
    const tOut = q('then she came out')
    let tx = 1560, pose = { name: 'stand' }, tf = -1, mouth = 0, alpha = 1
    if (t < tOut) { alpha = 0 }
    else if (t < qF1) { tx = lerp(1560, 1380, prog(t, tOut, qF1)); pose = { name: 'walk', d: (1560 - tx) } }
    else if (t < qF2) { const u = prog(t, qF1, qF2); tx = lerp(1380, 1260, u); pose = u < 0.3 ? { name: 'stand' } : { name: 'walk', d: 200 + (1380 - tx) }; mouth = u < 0.3 ? 1 : 0.3 }
    else if (t < qF3) { const u = prog(t, qF2, qF3); tx = lerp(1260, 1200, u); pose = u < 0.2 ? { name: 'stand' } : { name: 'crouch', k: 0.8 }; mouth = u < 0.2 ? 1 : 0.5 }
    else { tx = 1200; pose = { name: 'dead' } }
    const swapT = q('corbett took it'), runBack = prog(t, swapT - 0.4, swapT + 1.6)
    let m = null
    gorge(c, cam, t, { rustle: t > tOut - 1 && t < tOut + 0.6 ? 0.4 : 0.03, inner: c => {
      const aimK = sh.name === 'wait' ? 0.15 : sh.name === 'out' ? prog(t, tOut, tOut + 0.8) : 1
      const cx = sh.name === 'swap' ? lerp(640, 520, Math.sin(Math.PI * runBack)) : 640
      if (t >= tOut) beast(c, tx, 905, 0.55, { kind: 'tiger', f: tf, t, pose, mouth, alpha: prog(t, tOut, tOut + 0.4) })
      person(c, 420, 905, 0.6, { cos: 'tahsildar', pose: { name: 'stand', item: runBack > 0.5 && sh.name !== 'swap' ? null : 'rifle' }, f: 1 })
      const empty = t > qClick && t < swapT
      const o = person(c, cx, 905, 0.62, { cos: 'corbett', pose: sh.name === 'swap' && runBack > 0.05 && runBack < 0.95 ? { name: 'run', d: (640 - cx) * 2 } : { name: 'standAim', k: empty ? 0.6 : aimK }, f: sh.name === 'swap' && runBack > 0.05 && runBack < 0.5 ? -1 : 1, target: [tx - 40, 860], face: { mood: 'stern' } })
      m = o.muzzle
      if (m) muzzle(c, t, m, [qF1, qF2, qF3])
    } })
    layer(c, cam, 1.35, c => foreground(c, t))
    post(c, cam, { rays: 0.12 })
    flashes(c, t, [qF1, qF2, qF3])
    if (sh.name === 'last') label(c, '20 feet', W / 2, 110, prog(t, q('20 feet'), q('20 feet') + 0.4) * (1 - prog(t, sh.t1 - 0.5, sh.t1)))
  }

  // ---------- 10: the men come down; the teeth; the count; the marker
  SC[10] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'down'], [q('corbett looked') - 0.3, 'teeth'], [q('nobody knows') - 0.3, 'count'], [q('today a small marker') - 0.3, 'marker']])
    if (sh.name === 'down') {
      const cam = keys(t, [[sh.t0, { x: 700, y: 560, z: 1.15 }], [sh.t1, { x: 900, y: 640, z: 1.3 }]])
      gorge(c, cam, t, { walk: prog(t, sh.t0, sh.t1) * 1.6, inner: c => { beast(c, 1200, 905, 0.55, { kind: 'tiger', f: -1, pose: { name: 'dead' } }); person(c, 900, 905, 0.62, { cos: 'corbett', pose: { name: 'stand', item: 'rifle' }, f: 1 }); person(c, 520, 905, 0.58, { cos: 'villager', pose: { name: 'stand' }, f: 1, face: { mood: 'alarm' } }); person(c, 430, 900, 0.56, { cos: 'villager3', pose: { name: 'stand' }, f: 1 }) } })
      post(c, cam, { rays: 0.12 })
    } else if (sh.name === 'teeth') {
      // the same study of the jaw as before
      const fn = window.SCENES.__teeth; if (fn) fn(c, t, 1)
      post(c, { x: 960 }, { rays: false, vignette: 0.7 })
    } else if (sh.name === 'count') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 560, z: 1.05 }], [sh.t1, { x: 1000, y: 560, z: 1.12 }]])
      hills(c, cam, t, { tod: 'dusk' }); village(c, cam, t, { tod: 'dusk' })
      post(c, cam, { rays: 0.16, rayX: 200, grade: 'rgba(120,60,90,0.2)' })
      const a = prog(t, q('is 436'), q('is 436') + 0.6)
      if (t > q('the estimate')) count(c, W / 2, 420, Math.round(lerp(300, 436, prog(t, q('the estimate'), q('is 436') + 0.3, 'o'))), 230); else count(c, W / 2, 420, '?', 230)
      text(c, 'the most killed by any single tiger on record', W / 2, 560, 44, '#f3e7d0', { italic: true, shadow: 16, alpha: prog(t, q('it is still listed'), q('it is still listed') + 0.6) })
    } else {
      const cam = keys(t, [[sh.t0, { x: 960, y: 640, z: 1.4 }], [sh.t1, { x: 980, y: 640, z: 1.6 }]])
      hills(c, cam, t, { tod: 'day', seed: 12 })
      layer(c, cam, 1, c => {
        ground(c, 880, { col: '#6a6040', seed: 24 })
        c.fillStyle = vgrad(c, 900, 1000, '#5a5650', '#3a3632'); poly(c, [[-900, 900], [2900, 900], [2900, 980], [-900, 1000]]); c.fill()
        c.fillStyle = hgrad(c, 1000, 1160, '#d8d0c0', '#a8a090', '#7a7266'); c.fillRect(1000, 720, 150, 190); poly(c, [[990, 720], [1075, 680], [1160, 720]], '#b8b0a0')
        text(c, '1907', 1075, 790, 34, '#4a4038', { weight: 800 })
      })
      layer(c, cam, 1.35, c => foreground(c, t))
      post(c, cam, { rays: 0.12 })
      label(c, 'Near Lohaghat', W / 2, 110, prog(t, q('lohaghat'), q('lohaghat') + 0.6))
    }
  }

  // ---------- 11: after: the railway, the camera, the books, Kenya, the park
  SC[11] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'train'], [q('but over the next') - 0.3, 'map'], [q('he traded') - 0.3, 'camera'], [q('he wrote books') - 0.3, 'desk'], [q('in 1944') - 0.3, 'book'], [q('in 1947') - 0.3, 'kenya'], [q('after he died') - 0.3, 'park']])
    if (sh.name === 'train') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 640, z: 1.2 }], [sh.t1, { x: 980, y: 640, z: 1.25 }]])
      hills(c, cam, t, { tod: 'day', seed: 10 })
      layer(c, cam, 1, c => { ground(c, 880, { col: '#6a5a3e', grass: false }); c.fillStyle = '#4a3a2a'; c.fillRect(-900, 860, 4000, 14); c.fillStyle = '#2a2420'; for (let x = -900; x < 3000; x += 40) c.fillRect(x, 872, 22, 10); train(c, lerp(2600, -400, prog(t, sh.t0, sh.t1)), 870, 0.9, t, { f: -1, cars: 3 }); person(c, 500, 940, 0.62, { cos: 'corbett', pose: { name: 'stand' } }) })
      post(c, cam, { rays: 0.12 })
    } else if (sh.name === 'map') {
      c.fillStyle = '#1a140e'; c.fillRect(0, 0, W, H)
      const n = Math.floor(prog(t, sh.t0, sh.t1) * 12)
      map(c, W / 2, H / 2 - 20, 1500, 860, { draw: (c, w, h) => { const r = rng(52); text(c, 'KUMAON', 0, -330, 56, 'rgba(70,45,25,0.85)', { weight: 800 }); for (let k = 0; k < 12; k++) { const x = -600 + r() * 1200, y = -260 + r() * 560; if (k < n) { ell(c, x, y, 10, 10, 0, '#8a2a1e'); text(c, ['1907', '1910', '1918', '1925', '1926', '1929', '1930', '1932', '1933', '1937', '1938', '1938'][k], x, y - 30, 26, '#3a2a1a', { italic: true }) } } } })
      post(c, { x: 960 }, { rays: false, vignette: 0.5 })
    } else if (sh.name === 'camera') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 680, z: 1.45 }], [sh.t1, { x: 1000, y: 680, z: 1.55 }]])
      hills(c, cam, t, { tod: 'day', seed: 11 })
      layer(c, cam, 0.85, c => forest(c, -800, 3000, 780, 237, { seed: 33, fade: 0.1, hazeCol: '#a9b5b5', t }))
      layer(c, cam, 1, c => { ground(c, 900, { col: '#5e5a3a', seed: 25 }); camera(c, 760, 920, 0.9); person(c, 640, 915, 0.62, { cos: 'corbett', pose: { name: 'stand' }, face: { look: 0.05 } }); beast(c, 1400 - (t - sh.t0) * 40, 915, 0.5, { kind: 'tiger', f: -1, t, pose: { name: 'walk', d: (t - sh.t0) * 40 } }) })
      layer(c, cam, 1.35, c => foreground(c, t))
      post(c, cam, { rays: 0.16 })
    } else if (sh.name === 'desk') {
      const cam = keys(t, [[sh.t0, { x: 1060, y: 820, z: 1.6 }], [sh.t1, { x: 1080, y: 820, z: 1.7 }]])
      layer(c, cam, 1, c => {
        c.fillStyle = vgrad(c, 0, 900, '#4a3424', '#2a1c12'); c.fillRect(-400, -400, 2800, 1700)
        c.fillStyle = rgrad(c, 1100, 520, 10, 600, 'rgba(255,200,120,0.45)', 'rgba(255,200,120,0)'); c.fillRect(400, 0, 1400, 1100)
        c.fillStyle = hgrad(c, 600, 1500, '#6a4428', '#4a2e1a'); c.fillRect(830, 975, 700, 30); c.fillRect(860, 1005, 24, 110); c.fillRect(1480, 1005, 24, 110)
        paper(c, 940, 970, 160, 12, [], { col: '#efe4c8' })
        ell(c, 1330, 925, 26, 50, 0, '#d8b85a'); ell(c, 1330, 891, 16, 22, 0, 'rgba(255,230,160,0.9)')
        c.fillStyle = rgrad(c, 1330, 900, 4, 420, 'rgba(255,210,130,0.35)', 'rgba(255,210,130,0)'); c.fillRect(900, 400, 900, 800)
        person(c, 760, 1110, 0.95, { cos: 'corbett', pose: { name: 'sit', hands: 'table', write: true, t, seat: 92 }, face: { look: -0.3 } })
      })
      post(c, cam, { rays: false, vignette: 0.7 })
    } else if (sh.name === 'book') {
      c.fillStyle = vgrad(c, 0, H, '#3a2a1c', '#1a120c'); c.fillRect(0, 0, W, H)
      const z = keys(t, [[sh.t0, 1], [sh.t1, 1.06]])
      c.save(); c.translate(W / 2, H / 2); c.scale(z, z); c.translate(-W / 2, -H / 2)
      c.fillStyle = 'rgba(0,0,0,0.4)'; c.fillRect(740, 210, 470, 660)
      c.fillStyle = hgrad(c, 720, 1180, '#5a2a1e', '#7a3a26', '#4a2016'); c.fillRect(720, 190, 460, 650)
      c.strokeStyle = '#c9a24a'; c.lineWidth = 3; c.strokeRect(750, 220, 400, 590)
      text(c, 'Man-Eaters', 950, 380, 58, '#e8cf8a', { weight: 800 }); text(c, 'of Kumaon', 950, 450, 50, '#e8cf8a', { weight: 700, italic: true }); text(c, 'Jim Corbett', 950, 720, 36, '#e8cf8a')
      c.restore(); post(c, { x: 960 }, { rays: false, vignette: 0.6 })
      label(c, '1944', W / 2, 110, prog(t, sh.t0 + 0.2, sh.t0 + 0.8))
    } else if (sh.name === 'kenya') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 600, z: 1.1 }], [sh.t1, { x: 1000, y: 600, z: 1.2 }]])
      layer(c, cam, 0.06, c => PK.sky(c, '#7a5a7a', '#f0a868', { horizon: 760, sun: [960, 640, 700, '255,190,120'] }))
      layer(c, cam, 0.3, c => PK.ridge(c, 61, 720, 50, 200, '#6a5a6a', '#5a4a58'))
      layer(c, cam, 1, c => {
        c.fillStyle = vgrad(c, 760, 1100, '#8a6a3a', '#5a4024'); c.fillRect(-900, 780, 4000, 600)
        for (const [x, s] of [[300, 1], [1500, 1.3], [1900, 0.8]]) { c.save(); c.translate(x, 790); c.scale(s, s); c.strokeStyle = '#2a1c14'; c.lineWidth = 12; c.beginPath(); c.moveTo(0, 0); c.lineTo(0, -160); c.stroke(); ell(c, 0, -180, 160, 30, 0, '#2a2418'); ell(c, -40, -200, 100, 22, 0, '#2a2418'); c.restore() }
        person(c, 900, 800, 0.45, { cos: 'corbett', pose: { name: 'stand' }, fade: 0.2, hazeCol: '#5a4024' })
      })
      post(c, cam, { rays: 0.2, rayX: 600 })
      label(c, 'Kenya', W / 2, 110, prog(t, sh.t0 + 0.3, sh.t0 + 0.9) * (1 - prog(t, sh.t1 - 0.8, sh.t1 - 0.2)))
    } else {
      const cam = keys(t, [[sh.t0, { x: 960, y: 660, z: 1.3 }], [sh.t1, { x: 1000, y: 660, z: 1.45 }]])
      hills(c, cam, t, { tod: 'day', seed: 13 })
      layer(c, cam, 0.85, c => forest(c, -800, 3000, 780, 251, { seed: 34, fade: 0.08, hazeCol: '#a9b5b5', t }))
      layer(c, cam, 1, c => {
        ground(c, 900, { col: '#5e6a3a', seed: 26 })
        c.fillStyle = '#3a2a1a'; c.fillRect(560, 700, 18, 220); c.fillRect(940, 700, 18, 220)
        c.fillStyle = hgrad(c, 520, 1000, '#7a5a36', '#5a3e22'); c.fillRect(520, 620, 480, 120)
        text(c, 'CORBETT NATIONAL PARK', 760, 680, 40, '#efe2c2', { weight: 800 })
        beast(c, 1500 - (t - sh.t0) * 30, 930, 0.55, { kind: 'tiger', f: -1, t, pose: { name: 'walk', d: (t - sh.t0) * 30 } })
      })
      layer(c, cam, 1.35, c => foreground(c, t))
      post(c, cam, { rays: 0.16 })
    }
  }

  // ---------- 12: tigers today; subscribe
  SC[12] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'mother'], [q('and it is still true') - 0.3, 'old'], [q('corbett wrote that') - 0.3, 'nine'], [q('this one did not') - 0.3, 'her'], [q('subscribe') - 0.3, 'end']])
    if (sh.name === 'nine') {
      c.fillStyle = vgrad(c, 0, H, '#3a2a1c', '#1a120c'); c.fillRect(0, 0, W, H)
      paper(c, W / 2, 500, 1000, 520, [['Of every ten man-eaters,', 46, '#3a2a1a', { italic: true }], ['', 20], ['nine had been wounded,', 52], ['and the tenth was too old', 52], ['to hunt anything else.', 52], ['', 20], ['Jim Corbett', 32, '#5a4030', { italic: true }]], { top: 100, rot: -0.01 })
      post(c, { x: 960 }, { rays: false, vignette: 0.6 }); return
    }
    const u = t - sh.t0
    const cam = sh.name === 'end' ? keys(t, [[sh.t0, { x: 960, y: 640, z: 1.3 }], [sh.t1, { x: 960, y: 600, z: 1.1 }]]) : keys(t, [[sh.t0, { x: 900, y: 680, z: 1.4 }], [sh.t1, { x: 1000, y: 680, z: 1.55 }]])
    const tod = sh.name === 'her' || sh.name === 'end' ? 'dusk' : 'day'
    hills(c, cam, t, { tod, seed: 14 })
    layer(c, cam, 0.85, c => forest(c, -800, 3000, 780, 251, { seed: 35, fade: 0.12, hazeCol: '#a9b5b5', t }))
    layer(c, cam, 1, c => {
      ground(c, 900, { col: '#5e6a3a', seed: 27 })
      if (sh.name === 'mother') { const d = u * 50; beast(c, 600 + d, 930, 0.6, { kind: 'tiger', t, pose: { name: 'walk', d } }); beast(c, 380 + d, 935, 0.3, { kind: 'tiger', t, pose: { name: 'walk', d: d * 1.6 } }); beast(c, 250 + d, 940, 0.28, { kind: 'tiger', t, pose: { name: 'walk', d: d * 1.6 + 30 } }) }
      if (sh.name === 'old') beast(c, 1000, 930, 0.62, { kind: 'tiger', t, pose: { name: 'lie' }, fade: 0.15 })
      if (sh.name === 'her') { const r = rng(18); for (let x = 600; x < 1500; x += 24) tuft(c, x, 935 + r() * 10, 110 + r() * 40, '#5a6a32', Math.sin(t * 1.2 + x * 0.02) * 0.1, 5, x | 0); beast(c, 1000, 950, 0.62, { kind: 'tiger', t, pose: { name: 'stand' }, look: 0 }) }
      if (sh.name === 'end') beast(c, 1000 + u * 60, 940, 0.55, { kind: 'tiger', t, pose: { name: 'walk', d: u * 60 } })
    })
    layer(c, cam, 1.35, c => foreground(c, t))
    post(c, cam, { rays: tod === 'dusk' ? 0.18 : 0.14, rayX: tod === 'dusk' ? 200 : 700, grade: tod === 'dusk' ? 'rgba(120,60,90,0.18)' : null })
    if (sh.name === 'mother') { count(c, W / 2, 230, 'Over 3,000', 110); text(c, 'wild tigers in India', W / 2, 320, 44, '#f3e7d0', { italic: true, shadow: 16, alpha: prog(t, q('over 3000'), q('over 3000') + 0.5) }) }
    if (sh.name === 'end') { const a = prog(t, sh.t0 + 0.3, sh.t0 + 1); text(c, 'Subscribe', W / 2, 330, 96, '#f3e7d0', { weight: 800, alpha: a, shadow: 24 }); text(c, 'animal facts  ·  great battles  ·  financial collapses', W / 2, 430, 40, '#f3e7d0', { italic: true, alpha: prog(t, q('everything from'), q('everything from') + 0.6), shadow: 14 }) }
  }
})()
