// scB1.js: scenes 0-6 of The Champawat Tiger, Style B. Each scene: (c, t, q, S) draws the whole frame.
(function () {
  const { W, H, clamp, lerp, prog, keys, rng, ell, poly, shade, vgrad, hgrad, rgrad, layer, fog, post, foreground, tuft, person, crowd, beast, birds, tree, forest, terraces, house, river, brush, paper, map, pathLine, train, camera, count, text, label, shake, flashes } = PK
  const { hills, village, ground, gorge, CREST, shotOf, muzzle } = CWB
  const SC = window.SCENES = window.SCENES || []
  const hz = '#b9b0a2'

  // ---------- 0: the beat (cold open: drums on the ridge, one man below, something in the brush)
  SC[0] = (c, t, q, S) => {
    const sh = shotOf(t, [[0, 'wide'], [q('up on the ridge') - 0.3, 'ridge'], [q('down on the floor') - 0.3, 'man'], [q('the noise is meant') - 0.3, 'brush'], [q('by the time this day') - 0.3, 'pull']])
    let cam
    if (sh.name === 'wide') cam = keys(t, [[0, { x: 700, y: 560, z: 1.0 }], [sh.t1, { x: 760, y: 580, z: 1.12 }]])
    else if (sh.name === 'ridge') cam = keys(t, [[sh.t0, { x: -300, y: 300, z: 2.6 }], [sh.t1, { x: 500, y: 360, z: 2.6 }]], 'l')
    else if (sh.name === 'man') cam = keys(t, [[sh.t0, { x: 640, y: 760, z: 2.1 }], [sh.t1, { x: 700, y: 760, z: 2.3 }]])
    else if (sh.name === 'brush') cam = keys(t, [[sh.t0, { x: 1560, y: 820, z: 2.5 }], [sh.t1, { x: 1600, y: 830, z: 3.1 }]])
    else cam = keys(t, [[sh.t0, { x: 900, y: 600, z: 1.6 }], [sh.t1, { x: 760, y: 560, z: 0.98 }]])
    gorge(c, cam, t, { rustle: sh.name === 'brush' ? 0.25 : 0.05, inner: c => {
      person(c, 640, 905, 0.62, { cos: 'corbett', pose: { name: 'standAim', k: 0.15 }, target: [1500, 840], face: { mood: 'stern' } })
      if (sh.name === 'brush') { const a = prog(t, q('something that has been'), q('something that has been') + 1.2); for (const ex of [1580, 1606]) { ell(c, ex, 820, 7, 4, 0, `rgba(240,210,90,${a})`); ell(c, ex, 820, 20, 12, 0, `rgba(240,210,90,${a * 0.2})`) } }
    } })
    layer(c, cam, 1.35, c => foreground(c, t, { y: 1250 }))
    post(c, cam, { rays: 0.12, rayX: 600 })
    label(c, 'Champa gorge, Kumaon  ·  May 12, 1907', W / 2, 110, prog(t, 0.6, 1.4) * (1 - prog(t, q('up on the ridge') - 1, q('up on the ridge') - 0.3)))
  }

  // ---------- 1: the hills of Kumaon, life by the forest, then fear
  SC[1] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'pano'], [q('tigers and leopards') - 0.3, 'village'], [q('every day women') - 0.3, 'women'], [q('but by 1907') - 0.3, 'empty'], [q('and at night') - 0.3, 'night']])
    if (sh.name === 'pano' || sh.name === 'village' || sh.name === 'empty') {
      const cam = sh.name === 'pano' ? keys(t, [[sh.t0, { x: 500, y: 520, z: 1.05 }], [sh.t1, { x: 1300, y: 560, z: 1.15 }]], 'l') : sh.name === 'village' ? keys(t, [[sh.t0, { x: 900, y: 700, z: 1.6 }], [sh.t1, { x: 1000, y: 700, z: 1.75 }]]) : keys(t, [[sh.t0, { x: 700, y: 720, z: 1.7 }], [sh.t1, { x: 820, y: 700, z: 1.55 }]])
      const tod = sh.name === 'empty' ? 'dusk' : 'day'
      hills(c, cam, t, { tod })
      village(c, cam, t, { tod })
      layer(c, cam, 1, c => {
        if (sh.name === 'village') {
          person(c, 640, 880, 0.42, { cos: 'villager', pose: { name: 'walk', d: (t - sh.t0) * 40 * 0.42 + 0 }, f: 1 })
          person(c, 1180, 870, 0.42, { cos: 'villagewoman', pose: { name: 'carry', item: 'bundle' } })
          beast(c, 900, 880, 0.32, { kind: 'cow', t, pose: { name: 'stand' } }); beast(c, 1420, 875, 0.3, { kind: 'cow', t, f: -1, pose: { name: 'stand' } })
          person(c, 360, 860, 0.38, { cos: 'villager2', pose: { name: 'crouch' }, f: 1 })
        }
        if (sh.name === 'empty') { // shut doors, an untended field going to weeds
          const r = rng(4); for (let x = 200; x < 1700; x += 30 + r() * 30) tuft(c, x, 860 + r() * 30, 50 + r() * 40, '#5a6a3a', Math.sin(t + x) * 0.1, 5, x | 0)
        }
      })
      if (sh.name === 'pano') label(c, 'Kumaon, at the foot of the Himalayas', W / 2, 110, prog(t, sh.t0 + 0.5, sh.t0 + 1.3) * (1 - prog(t, sh.t1 - 1, sh.t1 - 0.3)))
      post(c, cam, { rays: tod === 'dusk' ? 0.16 : 0.1, rayX: tod === 'dusk' ? 200 : 900, grade: tod === 'dusk' ? 'rgba(120,60,90,0.2)' : null })
    } else if (sh.name === 'women') {
      const cam = keys(t, [[sh.t0, { x: 900, y: 640, z: 1.25 }], [sh.t1, { x: 1060, y: 640, z: 1.3 }]])
      hills(c, cam, t, { tod: 'day' })
      layer(c, cam, 0.8, c => { forest(c, -600, 2600, 740, 210, { seed: 14, fade: 0.15, hazeCol: '#a9b5b5', t }) })
      layer(c, cam, 1, c => {
        ground(c, 900, { col: '#6a6a3e', seed: 3 })
        poly(c, [[-600, 960], [400, 930], [1200, 915], [2600, 900], [2600, 980], [1200, 990], [400, 1010], [-600, 1040]], 'rgba(150,120,80,0.55)')
        const d = (t - sh.t0) * 60
        person(c, 860 + d, 935, 0.62, { cos: 'villagewoman', pose: { name: 'walk', d, item: 'bundle' } })
        person(c, 680 + d, 945, 0.5, { cos: 'girl', pose: { name: 'walk', d: d + 20 } })
        person(c, 500 + d, 950, 0.62, { cos: 'villagewoman', pose: { name: 'walk', d: d + 40, item: 'bundle' } })
        beast(c, 1500, 905, 0.42, { kind: 'cow', t, f: -1, pose: { name: 'stand' } })
      })
      layer(c, cam, 1.35, c => foreground(c, t))
      post(c, cam, { rays: 0.14, rayX: 700 })
    } else {
      // night: lit windows and drums in the doorways
      const cam = keys(t, [[sh.t0, { x: 900, y: 700, z: 1.5 }], [sh.t1, { x: 820, y: 740, z: 1.9 }]])
      hills(c, cam, t, { tod: 'night' })
      village(c, cam, t, { tod: 'night', litAll: true, inner: c => {
        person(c, 490, 806, 0.3, { cos: 'villager', pose: { name: 'drum', t, bpm: 96 }, fade: 0.3, hazeCol: '#1a2234' })
        person(c, 1430, 776, 0.3, { cos: 'villager3', pose: { name: 'drum', t: t + 0.3, bpm: 96 }, fade: 0.3, hazeCol: '#1a2234', f: -1 })
      } })
      post(c, cam, { night: 0.15, vignette: 0.75 })
    }
  }

  // ---------- 2: Nepal, the army, the Sarda river (map drawn true: Nepal to the east of Kumaon, she was driven west into India)
  function nepalMap(c, t, q, k, o = {}) {
    map(c, W / 2, H / 2 - 20, 1500, 860, { draw: (c, w, h) => {
      // the Sarda (Kali) river is the border: India (Kumaon) to the west/left, Nepal to the east/right
      c.strokeStyle = '#5a7a8a'; c.lineWidth = 9; c.lineCap = 'round'; c.beginPath(); c.moveTo(-60, -h / 2 + 30); c.bezierCurveTo(-20, -160, -110, 40, -40, 180); c.bezierCurveTo(0, 280, -70, 340, -50, h / 2 - 30); c.stroke()
      text(c, 'Sarda River', -150, 250, 30, '#3a5a6a', { italic: true, rot: -1.2 })
      text(c, 'NEPAL', 380, -260, 64, 'rgba(70,45,25,0.85)', { weight: 800 }); text(c, 'KUMAON, INDIA', -420, -260, 54, 'rgba(70,45,25,0.85)', { weight: 800 })
      const dot = (x, y, s, al = 1) => { ell(c, x, y, 9, 9, 0, `rgba(122,34,26,${al})`); text(c, s, x, y - 34, 32, `rgba(58,40,24,${al})`, { italic: true }) }
      dot(260, 60, 'Rupal'); dot(-420, 40, 'Champawat', prog(t, o.showC || 1e9, (o.showC || 1e9) + 0.6))
      for (let m = 0; m < 9; m++) { const x = -640 + (m % 3) * 90 + rng(m)() * 40, y = -120 + Math.floor(m / 3) * 110; c.fillStyle = 'rgba(90,70,40,0.35)'; c.beginPath(); c.moveTo(x, y); c.lineTo(x + 30, y - 46); c.lineTo(x + 60, y); c.fill() }
      if (k > 0) pathLine(c, [[260, 60], [180, 90], [60, 70], [-40, 100], [-160, 80], [-300, 60], [-420, 40]], k, '#8a2a1e', 7)
      if (o.n200) { const a = prog(t, o.n200, o.n200 + 0.5); text(c, '≈ 200', 280, 160, 80, `rgba(138,42,30,${a})`, { weight: 800 }); text(c, 'killed in Nepal', 280, 225, 32, `rgba(58,40,24,${a})`, { italic: true }) }
    } })
  }
  SC[2] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'map'], [q('hunters went after') - 0.3, 'hunters'], [q('finally the government') - 0.3, 'army'], [q('across the sarda') - 0.6, 'river'], [q('most accounts say') - 0.3, 'map2']])
    if (sh.name === 'map' || sh.name === 'map2') {
      c.fillStyle = '#1a140e'; c.fillRect(0, 0, W, H)
      const z = keys(t, [[sh.t0, 1.0], [sh.t1, 1.06]])
      c.save(); c.translate(W / 2, H / 2); c.scale(z, z); c.translate(-W / 2, -H / 2)
      nepalMap(c, t, q, sh.name === 'map2' ? prog(t, sh.t0, q('they had only moved') + 0.6, 'io') : 0, { n200: sh.name === 'map2' ? q('about 200') : 0, showC: sh.name === 'map2' ? q('they had only moved') : 0 })
      c.restore(); post(c, { x: 960 }, { rays: false, vignette: 0.5 })
    } else if (sh.name === 'hunters') {
      const cam = keys(t, [[sh.t0, { x: 900, y: 660, z: 1.4 }], [sh.t1, { x: 1000, y: 660, z: 1.5 }]])
      hills(c, cam, t, { tod: 'day', seed: 3 })
      layer(c, cam, 0.8, c => forest(c, -600, 2600, 760, 224, { seed: 17, fade: 0.12, hazeCol: '#a9b5b5', t }))
      layer(c, cam, 1, c => {
        ground(c, 900, { col: '#5e5a3a', seed: 6 })
        const d = (t - sh.t0) * 50
        person(c, 500 + d, 915, 0.58, { cos: 'sepoy', pose: { name: 'walk', d, item: 'rifle' } })
        person(c, 300 + d, 925, 0.58, { cos: 'villager3', pose: { name: 'walk', d: d + 30, item: 'rifle' } })
        brush(c, 1350, 920, 420, 200, t, { seed: 44 })
        beast(c, 1560, 905, 0.5, { kind: 'tiger', f: -1, t, pose: { name: 'crouch', k: 0.8 }, look: 0.1 })
        brush(c, 1420, 940, 380, 120, t, { seed: 45 })
      })
      layer(c, cam, 1.35, c => foreground(c, t))
      post(c, cam, { rays: 0.12 })
    } else if (sh.name === 'army') {
      const cam = keys(t, [[sh.t0, { x: 1100, y: 640, z: 1.15 }], [sh.t1, { x: 800, y: 660, z: 1.3 }]])
      hills(c, cam, t, { tod: 'day', seed: 5 })
      layer(c, cam, 0.85, c => forest(c, -800, 2800, 750, 210, { seed: 18, fade: 0.1, hazeCol: '#a9b5b5', t }))
      layer(c, cam, 1, c => {
        ground(c, 880, { col: '#5e5a3a', seed: 7 })
        const d = (t - sh.t0) * -45
        const men = []; for (let k = 0; k < 16; k++) men.push({ x: 300 + k * 120 + d + (k % 2) * 40, z: (k % 3) * 0.45 - 0.4, cos: 'sepoy', f: -1, pose: { name: 'walk', d: -d + k * 13, item: 'rifle' } })
        crowd(c, 900, men, { s: 0.5, zy: 60, fade: 0.3, haze: '#a9b5b5' })
      })
      layer(c, cam, 1.35, c => foreground(c, t))
      post(c, cam, { rays: 0.1 })
      label(c, 'The Nepalese army', W / 2, 110, prog(t, sh.t0 + 0.5, sh.t0 + 1.2) * (1 - prog(t, sh.t1 - 0.8, sh.t1 - 0.2)))
    } else {
      // she crosses the river at a run, from Nepal (right) into India (left)
      const cam = keys(t, [[sh.t0, { x: 1100, y: 760, z: 1.6 }], [sh.t1, { x: 700, y: 760, z: 1.6 }]])
      hills(c, cam, t, { tod: 'dusk', seed: 6 })
      layer(c, cam, 0.85, c => forest(c, -800, 2800, 760, 182, { seed: 19, fade: 0.2, hazeCol: '#a9a2a0' }))
      layer(c, cam, 1, c => {
        ground(c, 860, { col: '#5a4e38', seed: 8, grass: false })
        c.fillStyle = vgrad(c, 880, 1000, '#7f98a2', '#5f7a88'); c.fillRect(-900, 880, 4000, 120)
        c.strokeStyle = 'rgba(240,248,255,0.35)'; c.lineWidth = 2; for (let k = 0; k < 14; k++) { const x = ((k * 230 - t * 60) % 3200) - 700; c.beginPath(); c.moveTo(x, 900 + (k % 4) * 22); c.lineTo(x + 80, 900 + (k % 4) * 22); c.stroke() }
        const x = lerp(1700, 200, prog(t, sh.t0, sh.t1 - 0.2))
        beast(c, x, 950, 0.62, { kind: 'tiger', f: -1, t, pose: { name: 'run', d: (1700 - x) } })
        for (let k = 0; k < 4; k++) ell(c, x + 80 + k * 50, 945, 30 + k * 10, 8, 0, `rgba(240,248,255,${0.4 - k * 0.08})`)
      })
      post(c, cam, { rays: 0.14, rayX: 200, grade: 'rgba(120,60,90,0.18)' })
    }
  }

  // ---------- 3: how she hunted: across the valley, by day, the count, the reward
  function kumaonMap(c, t, k, o = {}) {
    map(c, W / 2, H / 2 - 20, 1500, 860, { draw: (c, w, h) => {
      const r = rng(31); c.fillStyle = 'rgba(90,70,40,0.3)'
      for (let m = 0; m < 26; m++) { const x = -640 + r() * 1280, y = -330 + r() * 640; c.beginPath(); c.moveTo(x, y); c.lineTo(x + 34, y - 52); c.lineTo(x + 68, y); c.fill() }
      const V = [[-520, -180], [-80, 200], [380, -120], [-300, 260], [480, 220], [60, -260], [-560, 120]]
      V.forEach(([x, y]) => house(c, x - 16, y + 8, 32, 22, { col: '#9a8a6a', roof: '#5a4a3a' }))
      if (k > 0) { let pts = [V[0]]; for (let i = 1; i < V.length; i++) pts.push(V[i]); const end = pathLine(c, pts, k, '#8a2a1e', 6); if (end) ell(c, end[0], end[1], 11, 11, 0, '#8a2a1e') }
      if (o.miles) { const a = prog(t, o.miles, o.miles + 0.5); text(c, '20 miles in a night', 0, 340, 54, `rgba(122,34,26,${a})`, { weight: 800, italic: true }) }
    } })
  }
  SC[3] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'map'], [q('most tigers that hunt') - 0.3, 'day'], [q('and most of the people') - 0.3, 'grass'], [q('every death was counted') - 0.3, 'count'], [q('the government put') - 0.3, 'reward'], [q('hunters came') - 0.3, 'hunters']])
    if (sh.name === 'map') {
      c.fillStyle = '#1a140e'; c.fillRect(0, 0, W, H)
      kumaonMap(c, t, prog(t, q('a village would lose'), sh.t1 - 0.4, 'io'), { miles: q('20 miles') })
      post(c, { x: 960 }, { rays: false, vignette: 0.5 })
    } else if (sh.name === 'day') {
      // broad daylight: high sun, the tigress moving low through tall grass above a village path
      const cam = keys(t, [[sh.t0, { x: 800, y: 700, z: 1.5 }], [sh.t1, { x: 1050, y: 720, z: 1.7 }]])
      hills(c, cam, t, { tod: 'noon' })
      layer(c, cam, 0.8, c => forest(c, -800, 2800, 720, 196, { seed: 22, fade: 0.12, hazeCol: '#a9b5b5' }))
      layer(c, cam, 1, c => {
        ground(c, 880, { col: '#7a7044', seed: 9 })
        const r = rng(12); for (let x = -600; x < 2600; x += 26) tuft(c, x, 880 + r() * 20, 120 + r() * 60, r() > 0.5 ? '#8a8a4a' : '#6f7a40', Math.sin(t * 1.2 + x * 0.02) * 0.1, 5, x | 0)
        const x = lerp(400, 1300, prog(t, sh.t0, sh.t1))
        beast(c, x, 905, 0.55, { kind: 'tiger', t, pose: { name: 'stalk', d: x - 400 }, look: 0.25 })
        const r2 = rng(13); for (let xx = -600; xx < 2600; xx += 30) tuft(c, xx, 925 + r2() * 20, 80 + r2() * 50, r2() > 0.5 ? '#9a9a52' : '#7a8446', Math.sin(t * 1.2 + xx * 0.02) * 0.1, 5, (xx | 0) + 3)
      })
      layer(c, cam, 1.35, c => foreground(c, t, { col: '#3a4220' }))
      post(c, cam, { rays: 0.2, rayX: 700 })
    } else if (sh.name === 'grass') {
      // women cutting grass on the slope, close to home; the grass beyond them moves (nothing more is shown)
      const cam = keys(t, [[sh.t0, { x: 900, y: 700, z: 1.45 }], [sh.t1, { x: 950, y: 690, z: 1.55 }]])
      hills(c, cam, t, { tod: 'day' })
      village(c, cam, t, { tod: 'day' })
      layer(c, cam, 1, c => {
        ground(c, 920, { col: '#7a7044', seed: 10 })
        person(c, 700, 935, 0.55, { cos: 'villagewoman', pose: { name: 'crouch' } })
        person(c, 950, 930, 0.5, { cos: 'girl', pose: { name: 'crouch' }, f: -1 })
        const r = rng(14); for (let x = 1200; x < 2200; x += 26) tuft(c, x, 930 + r() * 10, 130 + r() * 60, '#7a8446', Math.sin(t * 1.2 + x * 0.02) * 0.1 + (x > 1450 && x < 1650 ? Math.sin(t * 9 + x) * 0.25 : 0), 5, x | 0)
      })
      layer(c, cam, 1.35, c => foreground(c, t, { col: '#2a3218' }))
      post(c, cam, { rays: 0.12 })
    } else if (sh.name === 'count' || sh.name === 'hunters') {
      const cam = keys(t, [[sh.t0, { x: 900, y: 600, z: 1.1 }], [sh.t1, { x: 1000, y: 600, z: 1.2 }]])
      hills(c, cam, t, { tod: 'dusk' })
      village(c, cam, t, { tod: 'dusk' })
      if (sh.name === 'hunters') layer(c, cam, 1, c => { const d = (t - sh.t0) * 50; for (let k = 0; k < 4; k++) person(c, 300 + k * 140 + d, 900, 0.42, { cos: k % 2 ? 'corbett' : 'sepoy', pose: { name: 'walk', d: d + k * 20, item: 'rifle' }, fade: 0.1 }) })
      post(c, cam, { rays: 0.16, rayX: 200, grade: 'rgba(120,60,90,0.2)' })
      // the count, over the hills
      let n
      if (sh.name === 'count') n = Math.round(lerp(200, 240, prog(t, sh.t0, sh.t1)))
      else { const a = q('200'), b = q('300'), d2 = q('400'); n = t < a ? 200 : t < b ? 200 : t < d2 ? 300 : 400 }
      count(c, W / 2, 420, n, 190, '#f3e7d0'); text(c, 'people killed', W / 2, 540, 46, '#f3e7d0', { italic: true, shadow: 16 })
    } else {
      // the reward notice nailed to a post
      const cam = keys(t, [[sh.t0, { x: 960, y: 540, z: 1.0 }], [sh.t1, { x: 960, y: 520, z: 1.1 }]])
      hills(c, cam, t, { tod: 'day' })
      layer(c, cam, 1, c => {
        ground(c, 960, { col: '#6a5a3e' })
        c.fillStyle = hgrad(c, 900, 1020, '#7a5a3a', '#4a3420'); c.fillRect(910, 200, 100, 800)
        paper(c, 960, 520, 560, 640, [['REWARD', 76, '#7a221a'], ['', 20], ['For the destruction of', 32], ['the man-eating tigress', 32], ['of the Champawat district', 32], ['', 20], ['Government of the', 28], ['United Provinces', 28]], { rot: -0.03, top: 90 })
      })
      post(c, cam, { rays: 0.14 })
    }
  }

  // ---------- 4: why: the teeth
  function teeth(c, t, k) {
    // a painted study of a tiger skull, side view: the right upper canine snapped in half, the lower one worn to the root
    c.save(); c.setTransform(1, 0, 0, 1, 0, 0)
    c.fillStyle = rgrad(c, 960, 520, 60, 1100, '#3a2a1c', '#120e0a'); c.fillRect(0, 0, W, H)
    c.translate(W / 2 - 40, 540); const bone = rgrad(c, -150, -200, 40, 900, '#f2e8d2', '#d8c8a4', '#9a8a68')
    c.fillStyle = bone; c.beginPath(); c.moveTo(-640, 10); c.bezierCurveTo(-660, -180, -520, -330, -260, -350); c.bezierCurveTo(-60, -360, 160, -300, 330, -190); c.bezierCurveTo(430, -130, 520, -90, 600, -40); c.bezierCurveTo(640, -10, 630, 40, 590, 60); c.lineTo(300, 70); c.lineTo(-560, 80); c.closePath(); c.fill()
    ell(c, 60, -170, 120, 92, -0.2, 'rgba(60,44,28,0.85)')
    ell(c, 470, -60, 40, 26, -0.3, 'rgba(60,44,28,0.75)')
    c.strokeStyle = 'rgba(120,100,70,0.6)'; c.lineWidth = 6; c.beginPath(); c.moveTo(-420, -40); c.bezierCurveTo(-200, -80, 0, -60, 120, -40); c.stroke()
    ell(c, -330, -110, 150, 70, 0.1, 'rgba(80,60,40,0.4)')
    c.fillStyle = bone; c.beginPath(); c.moveTo(-600, 120); c.lineTo(540, 110); c.bezierCurveTo(600, 130, 590, 180, 520, 200); c.bezierCurveTo(200, 280, -300, 290, -560, 250); c.bezierCurveTo(-680, 230, -700, 140, -600, 120); c.closePath(); c.fill()
    for (let i = 0; i < 5; i++) { poly(c, [[-260 + i * 70, 72], [-230 + i * 70, 112], [-200 + i * 70, 72]], '#efe6d0'); poly(c, [[-250 + i * 70, 116], [-220 + i * 70, 84], [-190 + i * 70, 116]], '#e6dcc4') }
    for (let i = 0; i < 3; i++) poly(c, [[470 + i * 26, 64], [480 + i * 26, 92], [490 + i * 26, 64]], '#efe6d0')
    poly(c, [[340, 60], [420, 60], [404, 150], [356, 160]], '#f4ecd8'); c.strokeStyle = '#6a5a40'; c.lineWidth = 2; c.stroke()
    c.strokeStyle = `rgba(150,40,30,${0.6 + k * 0.4})`; c.lineWidth = 4; c.beginPath(); c.moveTo(352, 160); c.lineTo(370, 148); c.lineTo(384, 158); c.lineTo(406, 148); c.stroke()
    c.setLineDash([10, 10]); c.strokeStyle = 'rgba(244,236,216,0.35)'; c.lineWidth = 3; c.beginPath(); c.moveTo(356, 160); c.lineTo(378, 260); c.lineTo(404, 150); c.stroke(); c.setLineDash([])
    poly(c, [[280, 112], [340, 112], [334, 92], [286, 94]], '#ded2b6'); c.strokeStyle = '#6a5a40'; c.lineWidth = 2; c.stroke()
    c.setLineDash([10, 10]); c.strokeStyle = 'rgba(244,236,216,0.35)'; c.lineWidth = 3; c.beginPath(); c.moveTo(286, 94); c.lineTo(310, 0); c.lineTo(334, 92); c.stroke(); c.setLineDash([])
    if (k > 0) { c.strokeStyle = `rgba(170,40,30,${k})`; c.lineWidth = 6; ell(c, 345, 125, 130, 110, 0); c.stroke() }
    c.restore()
  }
  SC.__teeth = teeth
  SC[4] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'chase'], [q('the answer to why') - 0.3, 'teeth'], [q('most likely') - 0.3, 'shot'], [q('she could no longer') - 0.3, 'watch']])
    if (sh.name === 'chase') {
      const cam = { x: 820 + (t - sh.t0) * 255, y: 760, z: 1.6 }
      hills(c, cam, t, { tod: 'day', seed: 4 })
      layer(c, cam, 0.8, c => forest(c, -800, 9000, 740, 196, { seed: 23, fade: 0.14, hazeCol: '#a9b5b5' }))
      layer(c, cam, 1, c => {
        ground(c, 900, { col: '#7a7044', seed: 11, x1: 5200 })
        const u = t - sh.t0, dx = u * 260
        beast(c, 900 + dx, 940, 0.5, { kind: 'deer', t, pose: { name: 'run', d: dx * 1.05 } })
        beast(c, 520 + dx * 1.02, 950, 0.55, { kind: 'tiger', t, pose: { name: 'run', d: dx } })
      })
      layer(c, cam, 1.35, c => foreground(c, t))
      post(c, cam, { rays: 0.12 })
    } else if (sh.name === 'teeth') {
      teeth(c, t, prog(t, q('were broken'), q('were broken') + 0.6))
      const z = keys(t, [[sh.t0, 1], [sh.t1, 1.08]])
      post(c, { x: 960 }, { rays: false, vignette: 0.7 })
      text(c, 'one in half', 1340, 260, 44, '#f3e7d0', { italic: true, alpha: prog(t, q('one in half'), q('one in half') + 0.4), shadow: 14 })
      text(c, 'one to the bone', 1340, 840, 44, '#f3e7d0', { italic: true, alpha: prog(t, q('the other right down'), q('the other right down') + 0.4), shadow: 14 })
    } else if (sh.name === 'shot') {
      // years before: a hunter's shot at a younger tigress (sepia)
      const cam = keys(t, [[sh.t0, { x: 960, y: 700, z: 1.5 }], [sh.t1, { x: 1000, y: 700, z: 1.55 }]])
      hills(c, cam, t, { tod: 'day', seed: 7 })
      layer(c, cam, 0.8, c => forest(c, -800, 3000, 750, 196, { seed: 24, fade: 0.14, hazeCol: '#a9b5b5' }))
      const fire = q('had shot her') + 0.2
      let m = [0, 0]
      layer(c, cam, 1, c => {
        ground(c, 900, { col: '#6a6040', seed: 13 })
        const o = person(c, 560, 910, 0.6, { cos: 'sepoy', pose: { name: 'standAim', k: 1 }, target: [1360, 830] }); m = o.muzzle
        beast(c, 1380, 910, 0.55, { kind: 'tiger', f: -1, t, pose: { name: t > fire ? 'run' : 'stand', d: (t - fire) * 300 }, mouth: t > fire && t < fire + 0.6 ? 1 : 0 })
        muzzle(c, t, m, [fire])
      })
      post(c, cam, { rays: 0.1, grade: 'rgba(140,100,50,0.45)' })
      label(c, 'Years before', W / 2, 110, prog(t, sh.t0 + 0.3, sh.t0 + 1) * (1 - prog(t, sh.t1 - 0.8, sh.t1 - 0.2)))
    } else {
      const cam = keys(t, [[sh.t0, { x: 1100, y: 760, z: 1.9 }], [sh.t1, { x: 1150, y: 770, z: 2.3 }]])
      hills(c, cam, t, { tod: 'dusk' })
      layer(c, cam, 0.85, c => forest(c, -800, 3000, 760, 196, { seed: 25, fade: 0.2, hazeCol: '#a9a2a0' }))
      layer(c, cam, 1, c => {
        ground(c, 900, { col: '#5a5038', seed: 14 })
        const r = rng(16); for (let x = 600; x < 2000; x += 24) tuft(c, x, 905 + r() * 10, 120 + r() * 50, '#5a6a32', Math.sin(t * 1.2 + x * 0.02) * 0.1, 5, x | 0)
        beast(c, 1160, 930, 0.6, { kind: 'tiger', f: -1, t, pose: { name: 'crouch', k: 0.7 }, look: 0.05 })
        const r2 = rng(17); for (let x = 800; x < 1700; x += 24) tuft(c, x, 940 + r2() * 10, 70 + r2() * 30, '#4a5a2a', Math.sin(t * 1.2 + x * 0.02) * 0.1, 5, (x | 0) + 1)
      })
      post(c, cam, { rays: 0.14, rayX: 200, grade: 'rgba(120,60,90,0.2)' })
    }
  }

  // ---------- 5: Jim Corbett
  SC[5] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'portrait'], [q('he had been born') - 0.3, 'nainital'], [q('he could read') - 0.3, 'tracks'], [q('he knew the alarm') - 0.3, 'alarm'], [q('he had a job') - 0.3, 'train'], [q('when the government asked') - 0.3, 'terms']])
    if (sh.name === 'portrait') {
      const cam = keys(t, [[sh.t0, { x: 900, y: 600, z: 2.0 }], [sh.t1, { x: 930, y: 590, z: 2.2 }]])
      hills(c, cam, t, { tod: 'day' })
      layer(c, cam, 0.85, c => forest(c, -800, 3000, 760, 210, { seed: 26, fade: 0.25, hazeCol: '#a9b5b5' }))
      layer(c, cam, 1, c => { ground(c, 900); person(c, 900, 905, 0.95, { cos: 'corbett', pose: { name: 'stand', item: 'rifle' }, face: { mood: 'calm', look: 0.05 } }) })
      layer(c, cam, 1.4, c => foreground(c, t))
      post(c, cam, { rays: 0.12 })
      label(c, 'Jim Corbett, 31', W / 2, 110, prog(t, sh.t0 + 0.6, sh.t0 + 1.3) * (1 - prog(t, sh.t1 - 0.8, sh.t1 - 0.2)))
    } else if (sh.name === 'nainital') {
      const cam = keys(t, [[sh.t0, { x: 900, y: 620, z: 1.15 }], [sh.t1, { x: 1000, y: 640, z: 1.3 }]])
      hills(c, cam, t, { tod: 'day', seed: 2 })
      layer(c, cam, 0.7, c => {
        c.fillStyle = vgrad(c, 760, 900, '#7f98a2', '#5f7a88'); ell(c, 960, 820, 900, 90, 0); c.fill()
        const r = rng(3); for (let k = 0; k < 14; k++) house(c, 150 + k * 120 + r() * 40, 760 - (k % 3) * 40, 60, 46, { col: '#d8cfc0', roof: '#7a3a2a' })
        forest(c, -600, 2600, 720, 154, { seed: 27, fade: 0.2, hazeCol: '#a9b5b5' })
      })
      layer(c, cam, 1, c => { ground(c, 920, { col: '#5e6a3a' }); const d = (t - sh.t0) * 40; person(c, 500 + d, 930, 0.5, { cos: 'corbettboy', pose: { name: 'walk', d } }) })
      layer(c, cam, 1.4, c => foreground(c, t))
      post(c, cam, { rays: 0.14 })
      label(c, 'Nainital', W / 2, 110, prog(t, sh.t0 + 0.6, sh.t0 + 1.3) * (1 - prog(t, sh.t1 - 0.8, sh.t1 - 0.2)))
    } else if (sh.name === 'tracks') {
      // close on the mud: pug marks, and his hand
      const cam = keys(t, [[sh.t0, { x: 960, y: 760, z: 1.8 }], [sh.t1, { x: 1000, y: 760, z: 2.0 }]])
      hills(c, cam, t, { tod: 'day', seed: 8 })
      layer(c, cam, 1, c => {
        ground(c, 840, { col: '#6a5636', grass: false })
        for (let k = 0; k < 5; k++) { const x = 760 + k * 150, y = 900 + (k % 2) * 40; ell(c, x, y, 26, 20, 0, 'rgba(40,28,16,0.6)'); for (let j = 0; j < 4; j++) ell(c, x - 24 + j * 16, y - 30 + Math.abs(j - 1.5) * 4, 7, 9, 0, 'rgba(40,28,16,0.55)') }
        person(c, 640, 860, 0.85, { cos: 'corbett', pose: { name: 'kneel' }, face: { look: -0.5 } })
      })
      post(c, cam, { rays: 0.12 })
    } else if (sh.name === 'alarm') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 640, z: 1.4 }], [sh.t1, { x: 980, y: 620, z: 1.5 }]])
      hills(c, cam, t, { tod: 'day', seed: 9 })
      layer(c, cam, 0.8, c => forest(c, -800, 3000, 760, 224, { seed: 28, fade: 0.1, hazeCol: '#a9b5b5', t }))
      layer(c, cam, 1, c => {
        ground(c, 900, { col: '#5e5a3a', seed: 15 })
        const u = t - sh.t0
        birds(c, u, 600, 320 - u * 30, 9, { seed: 4, vx: 160 })
        beast(c, 1400 - u * 30, 915, 0.5, { kind: 'deer', f: -1, t, pose: { name: 'stand' }, look: -0.3 })
        person(c, 600, 915, 0.62, { cos: 'corbett', pose: { name: 'stand', item: 'rifle' }, face: { look: 0.3, mood: 'stern' } })
      })
      layer(c, cam, 1.35, c => foreground(c, t))
      post(c, cam, { rays: 0.14 })
    } else if (sh.name === 'train') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 640, z: 1.2 }], [sh.t1, { x: 960, y: 640, z: 1.25 }]])
      hills(c, cam, t, { tod: 'day', seed: 10 })
      layer(c, cam, 1, c => {
        ground(c, 880, { col: '#6a5a3e', grass: false })
        c.fillStyle = '#4a3a2a'; c.fillRect(-900, 860, 4000, 14); c.fillStyle = '#2a2420'; for (let x = -900; x < 3000; x += 40) c.fillRect(x, 872, 22, 10)
        train(c, lerp(-300, 2600, prog(t, sh.t0, sh.t1)), 870, 0.9, t, { cars: 4 })
        person(c, 1500, 940, 0.62, { cos: 'corbett', pose: { name: 'stand' }, f: -1 })
      })
      post(c, cam, { rays: 0.12 })
    } else {
      const cam = keys(t, [[sh.t0, { x: 960, y: 560, z: 1.0 }], [sh.t1, { x: 960, y: 540, z: 1.06 }]])
      c.fillStyle = vgrad(c, 0, H, '#3a2a1c', '#1a120c'); c.fillRect(0, 0, W, H)
      layer(c, cam, 1, c => {
        c.fillStyle = hgrad(c, 0, W, '#5a4028', '#7a5636', '#4a3020'); c.fillRect(-200, 700, 2400, 500)
        const a1 = prog(t, q('the reward on her head had'), q('the reward on her head had') + 0.5), a2 = prog(t, q('and every other hunter'), q('and every other hunter') + 0.5)
        paper(c, 960, 500, 1300, 640, [['Two conditions', 76, '#3a2a1a'], ['', 20], [a1 > 0 ? '1.  The reward is cancelled.' : '', 58, '#3a2a1a', { alpha: a1 }], ['', 10], [a2 > 0 ? '2.  Every other hunter is called off.' : '', 58, '#3a2a1a', { alpha: a2 }]], { rot: 0.01, top: 110 })
      })
      post(c, cam, { rays: false, vignette: 0.6 })
    }
  }

  // ---------- 6: the search, village to village; Champawat; word from Phungar
  SC[6] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'walk'], [q('weeks went by') - 0.3, 'weeks'], [q('in each village') - 0.3, 'point'], [q('then he reached') - 0.3, 'tahsildar'], [q('and word came') - 0.3, 'runner']])
    if (sh.name === 'walk' || sh.name === 'weeks') {
      const weeks = sh.name === 'weeks', u = t - sh.t0
      const tod = weeks ? (['day', 'dusk', 'night', 'dawn', 'day', 'dusk'][Math.floor(u / 0.6) % 6]) : 'day'
      const cam = { x: 900 + u * 60, y: 640, z: 1.35 }
      hills(c, cam, t, { tod, seed: 1 })
      village(c, cam, t, { tod })
      layer(c, cam, 1, c => { ground(c, 900, { col: tod === 'night' ? '#2a2a20' : '#6a5a3e', seed: 16 }); const d = u * 60 + (weeks ? 600 : 0); person(c, 700 + u * 60, 915, 0.6, { cos: 'corbett', pose: { name: 'walk', d, item: 'rifle' } }) })
      layer(c, cam, 1.35, c => foreground(c, t))
      post(c, cam, { rays: tod === 'day' ? 0.12 : false, night: tod === 'night' ? 0.2 : 0, grade: tod === 'dusk' ? 'rgba(120,60,90,0.2)' : null })
      if (weeks) label(c, 'Weeks', W / 2, 110, prog(t, sh.t0 + 0.2, sh.t0 + 0.6) * (1 - prog(t, sh.t1 - 0.5, sh.t1)))
    } else if (sh.name === 'point') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 700, z: 1.7 }], [sh.t1, { x: 1000, y: 690, z: 1.85 }]])
      hills(c, cam, t, { tod: 'day', seed: 3 })
      village(c, cam, t, { tod: 'day' })
      layer(c, cam, 1, c => {
        ground(c, 900, { col: '#6a5a3e', seed: 17 })
        person(c, 1080, 910, 0.62, { cos: 'villager3', pose: { name: 'point' }, target: [1700, 760], f: 1, face: { talk: t } })
        person(c, 800, 915, 0.64, { cos: 'corbett', pose: { name: 'stand', item: 'rifle' }, face: { look: 0.1 } })
        person(c, 1300, 905, 0.55, { cos: 'villagewoman', pose: { name: 'stand' }, f: -1 })
      })
      layer(c, cam, 1.35, c => foreground(c, t))
      post(c, cam, { rays: 0.12 })
    } else if (sh.name === 'tahsildar') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 640, z: 1.5 }], [sh.t1, { x: 960, y: 660, z: 1.7 }]])
      hills(c, cam, t, { tod: 'day', seed: 4 })
      village(c, cam, t, { tod: 'day', houses: [[300, 800, 220, 150], [700, 790, 260, 170], [1250, 780, 240, 160], [1600, 800, 220, 140]] })
      layer(c, cam, 1, c => {
        ground(c, 900, { col: '#7a6a4a', seed: 18 })
        person(c, 820, 915, 0.66, { cos: 'corbett', pose: { name: 'stand', item: 'rifle' }, face: { talk: t > q('and met') ? t : 0 } })
        person(c, 1100, 912, 0.66, { cos: 'tahsildar', pose: { name: 'stand' }, f: -1, face: { mood: 'calm' } })
      })
      layer(c, cam, 1.35, c => foreground(c, t))
      post(c, cam, { rays: 0.12 })
      label(c, 'Champawat', W / 2, 110, prog(t, sh.t0 + 0.4, sh.t0 + 1) * (1 - prog(t, sh.t1 - 0.8, sh.t1 - 0.2)))
    } else {
      const cam = keys(t, [[sh.t0, { x: 900, y: 660, z: 1.5 }], [sh.t1, { x: 1000, y: 660, z: 1.6 }]])
      hills(c, cam, t, { tod: 'dusk', seed: 5 })
      village(c, cam, t, { tod: 'dusk' })
      layer(c, cam, 1, c => {
        ground(c, 900, { col: '#6a5a3e', seed: 19 })
        const x = lerp(300, 900, prog(t, sh.t0, sh.t1 - 0.5))
        person(c, x, 915, 0.62, { cos: 'villager', pose: { name: 'run', d: x - 300 }, face: { mood: 'alarm' } })
        person(c, 1150, 912, 0.64, { cos: 'corbett', pose: { name: 'stand', item: 'rifle' }, f: -1 })
        person(c, 1320, 912, 0.64, { cos: 'tahsildar', pose: { name: 'stand' }, f: -1 })
      })
      layer(c, cam, 1.35, c => foreground(c, t))
      post(c, cam, { rays: 0.16, rayX: 200, grade: 'rgba(120,60,90,0.2)' })
      label(c, 'Phungar', W / 2, 110, prog(t, q('phungar'), q('phungar') + 0.6))
    }
  }
})()
