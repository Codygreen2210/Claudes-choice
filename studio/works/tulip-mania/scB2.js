// scB2.js: scenes 7-12 of Tulip Mania, Style B.
(function () {
  const { W, H, clamp, lerp, prog, keys, rng, ell, poly, shade, vgrad, hgrad, rgrad, layer, fog, sky, post, foreground, tuft, person, crowd, beast, birds, tree, forest, paper, map, pathLine, count, text, label, shake, flashes } = PK
  const { tulip, bulb, gable, street, canal, ship, windmill, tavern, table, polder, fields, chart, shotOf, BUYERS } = TUB
  const SC = window.SCENES = window.SCENES || []
  const darkBg = c => { c.fillStyle = vgrad(c, 0, H, '#3a2618', '#1a100a'); c.fillRect(0, 0, W, H) }
  const word = (c, s, y, a, size = 54) => text(c, s, W / 2, y, size, '#f3e7d0', { italic: true, shadow: 16, alpha: a })

  // ---------- 7: Haarlem, nobody bids
  SC[7] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'nobid'], [q('the news went') - 0.3, 'map'], [q('everyone holding a promise to buy') - 0.3, 'street'], [q('nobody has ever proved') - 0.3, 'chart'], [q('the alkmaar auction') - 0.3, 'alkmaar']])
    if (sh.name === 'nobid') {
      const cam = keys(t, [[sh.t0, { x: 1000, y: 700, z: 1.5 }], [q('and nobody bid'), { x: 1050, y: 700, z: 1.6 }], [sh.t1, { x: 1250, y: 680, z: 1.9 }]])
      const silent = t > q('and nobody bid')
      tavern(c, cam, t, { night: true, inner: c => {
        const r = rng(4); for (const row of [0, 1]) for (let k = 0; k < 6; k++) { const x = 330 + k * 220 + (row ? 70 : 0) + (r() - 0.5) * 30; person(c, x, row ? 960 : 880, row ? 0.92 : 0.74, { cos: BUYERS[(k + row * 2) % BUYERS.length], f: silent ? (k % 2 ? 1 : -1) : 1, pose: { name: 'stand' }, face: { mood: silent ? 'stern' : 'calm', look: silent ? -0.2 : 0.1 }, fade: row ? 0.05 : 0.3, hazeCol: '#3a2418' }) }
        person(c, 1600, 945, 0.92, { cos: 'dutchman3', f: -1, pose: { name: 'raise', k: 1 }, face: { mood: silent ? 'alarm' : 'calm', talk: silent ? 0 : t }, holdFn: c => paper(c, 0, -10, 90, 110, [], { rot: 0.05 }) })
        table(c, 200, 990, 1400, t, { candle: true })
      } })
      post(c, cam, { rays: false, night: 0.2, vignette: 0.7 })
      label(c, 'Haarlem, February 1637', W / 2, 110, prog(t, sh.t0 + 0.4, sh.t0 + 1) * (1 - prog(t, q('and nobody bid') - 0.4, q('and nobody bid'))))
      word(c, 'not at last week’s price', 180, prog(t, q('not at the price'), q('not at the price') + 0.3) * (1 - prog(t, q('not at half') - 0.2, q('not at half'))))
      word(c, 'not at half', 180, prog(t, q('not at half'), q('not at half') + 0.3))
    } else if (sh.name === 'map') {
      darkBg(c)
      const towns = [['Haarlem', -120, 60], ['Amsterdam', 60, 40], ['Alkmaar', -90, -220], ['Leiden', -220, 240], ['Utrecht', 260, 230], ['Enkhuizen', 120, -260], ['Hoorn', 40, -180]]
      const k = prog(t, sh.t0 + 0.3, sh.t1 - 0.3)
      map(c, W / 2, H / 2 - 20, 1300, 860, { draw: (c, w, h) => {
        c.fillStyle = 'rgba(90,120,140,0.35)'; c.beginPath(); c.moveTo(-650, -430); c.lineTo(-330, -430); c.bezierCurveTo(-260, -200, -330, 100, -360, 430); c.lineTo(-650, 430); c.closePath(); c.fill()
        c.beginPath(); c.moveTo(100, -430); c.bezierCurveTo(300, -300, 380, -120, 260, -40); c.bezierCurveTo(180, 0, 140, -60, 120, -160); c.lineTo(160, -430); c.fill()
        text(c, 'NORTH SEA', -520, -60, 30, 'rgba(50,70,90,0.7)', { italic: true, rot: -1.4 })
        towns.forEach(([n, x, y], i) => { const lit = k * towns.length > i; ell(c, x, y, lit ? 14 : 9, lit ? 14 : 9, 0, lit ? '#8a2a1e' : '#5a4030'); if (lit) ell(c, x, y, 34, 34, 0, 'rgba(138,42,30,0.2)'); text(c, n, x, y - 36, 30, '#3a2a1a', { italic: true }) })
      } })
      post(c, { x: 960 }, { rays: false, vignette: 0.5 })
    } else if (sh.name === 'street') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 620, z: 1.3 }], [sh.t1, { x: 1000, y: 620, z: 1.45 }]])
      layer(c, cam, 0.06, c => sky(c, '#6a7a8a', '#c8c0b0', { horizon: 600, clouds: 5 }))
      layer(c, cam, 0.85, c => street(c, -900, 3000, 760, { h: 320, seed: 17 }))
      layer(c, cam, 1, c => {
        c.fillStyle = vgrad(c, 760, 1200, '#8a7a66', '#4a4034'); c.fillRect(-900, 760, 3800, 600)
        const pairs = [[560, 'weaver', 'dutchman2'], [1120, 'baker', 'dutchman']]
        pairs.forEach(([x, a, b], i) => { person(c, x, 960, 0.75, { cos: a, pose: { name: 'point' }, target: [x + 400, 700], face: { mood: 'angry', mouth: 'shout', talk: t } }); person(c, x + 230, 960, 0.75, { cos: b, f: -1, pose: { name: 'hold', at: [60, -190] }, holdFn: c => paper(c, 0, 0, 70, 90, [], { rot: -0.1 }), face: { mood: 'alarm' } }) })
      })
      post(c, cam, { rays: 0.08, grade: 'rgba(60,60,80,0.2)' })
      word(c, 'buyers wanted out', 160, prog(t, q('wanted out'), q('wanted out') + 0.3) * (1 - prog(t, q('and everyone holding a promise to sell') - 0.2, q('and everyone holding a promise to sell'))))
      word(c, 'sellers wanted to be paid', 160, prog(t, q('wanted to be paid'), q('wanted to be paid') + 0.3))
    } else if (sh.name === 'chart') {
      darkBg(c)
      const pts = [0.05, 0.08, 0.12, 0.2, 0.32, 0.5, 0.72, 0.95, 0.4, 0.12, 0.06]
      chart(c, 960, 520, 1400, 760, pts, prog(t, sh.t0 + 0.4, sh.t1 - 0.6), { xlabels: [[0, 'autumn 1636'], [7, 'early Feb 1637'], [10, 'spring']], labels: [[7, '?']] })
      post(c, { x: 960 }, { rays: false, vignette: 0.6 })
      word(c, 'maybe the plague', 120, prog(t, q('maybe the plague'), q('maybe the plague') + 0.3) * (1 - prog(t, q('maybe the prices') - 0.2, q('maybe the prices'))), 46)
      word(c, 'maybe too high for the next buyer', 120, prog(t, q('maybe the prices'), q('maybe the prices') + 0.3), 46)
    } else {
      const cam = keys(t, [[sh.t0, { x: 1000, y: 700, z: 1.5 }], [sh.t1, { x: 1000, y: 690, z: 1.7 }]])
      tavern(c, cam, t, { inner: c => { const r = rng(3); for (const row of [0, 1]) for (let k = 0; k < 7; k++) { const x = 330 + k * 200 + (row ? 60 : 0), up = Math.sin(t * 2.2 + k * 1.7 + row) > 0.55; person(c, x, row ? 960 : 880, row ? 0.92 : 0.74, { cos: BUYERS[(k + row * 3) % BUYERS.length], f: x < 1000 ? 1 : -1, pose: up ? { name: 'raise', k: 1 } : { name: 'stand' }, face: { mood: 'happy' }, fade: row ? 0.05 : 0.3, hazeCol: '#3a2418' }) } table(c, 200, 990, 1400, t, { candle: true }) } })
      post(c, cam, { rays: false, vignette: 0.65, grade: 'rgba(160,140,120,0.35)' })
      label(c, 'Alkmaar, February 5', W / 2, 110, prog(t, sh.t0 + 0.3, sh.t0 + 0.9))
    }
  }

  // ---------- 8: who had to pay; the courts; torn paper
  SC[8] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'court'], [q('in the end') - 0.3, 'deal'], [q('the paper was torn') - 0.3, 'tear'], [q('and the tulips bloomed') - 0.3, 'bloom']])
    if (sh.name === 'court') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 700, z: 1.45 }], [sh.t1, { x: 960, y: 700, z: 1.6 }]])
      layer(c, cam, 0.9, c => {
        c.fillStyle = vgrad(c, -200, 1000, '#4a3424', '#2a1c12'); c.fillRect(-900, -400, 3800, 1600)
        for (let x = -800; x < 2900; x += 200) { c.fillStyle = 'rgba(0,0,0,0.2)'; c.fillRect(x, 200, 160, 500); c.strokeStyle = 'rgba(255,220,180,0.08)'; c.lineWidth = 3; c.strokeRect(x + 10, 210, 140, 480) }
        c.fillStyle = hgrad(c, 400, 1500, '#5a3a22', '#3a2414'); c.fillRect(400, 600, 1100, 220)
      })
      layer(c, cam, 1, c => {
        for (let k = 0; k < 3; k++) person(c, 640 + k * 320, 790, 0.85, { cos: 'judge17', pose: { name: 'sit', hands: 'table' }, face: { mood: 'stern' } })
        c.fillStyle = hgrad(c, 400, 1500, '#6a4428', '#3a2414'); c.fillRect(400, 720, 1100, 180); c.fillStyle = '#7a5434'; c.fillRect(390, 710, 1120, 16)
        c.fillStyle = vgrad(c, 860, 1200, '#3a2a1a', '#1a120a'); c.fillRect(-900, 860, 3800, 600)
        person(c, 420, 1060, 0.95, { cos: 'dutchman2', pose: { name: 'point' }, target: [900, 650], face: { mood: 'angry', talk: t } })
        person(c, 1520, 1060, 0.95, { cos: 'weaver', f: -1, pose: { name: 'stand' }, face: { mood: 'sad' } })
      })
      post(c, cam, { rays: false, vignette: 0.7 })
      word(c, 'gambling debts', 150, prog(t, q('gambling debts'), q('gambling debts') + 0.3))
    } else if (sh.name === 'deal') {
      darkBg(c)
      paper(c, 960, 520, 1100, 600, [['Haarlem, 1637', 40, '#5a4030', { italic: true }], ['', 20], ['Walk away from the deal', 56], ['by paying', 44], ['', 6], ['about 3.5%', 96, '#8a2a1e', { alpha: prog(t, q('about 3.5'), q('about 3.5') + 0.3) }]], { rot: -0.01, top: 90 })
      post(c, { x: 960 }, { rays: false, vignette: 0.6 })
    } else if (sh.name === 'tear') {
      darkBg(c)
      const k = prog(t, q('torn up') - 0.1, q('torn up') + 0.7, 'o')
      for (const s of [-1, 1]) { c.save(); c.translate(960 + s * k * 260, 520 + k * 120); c.rotate(s * k * 0.4); c.beginPath(); if (s < 0) { c.moveTo(-500, -320); c.lineTo(10, -320); c.lineTo(-20, -100); c.lineTo(20, 60); c.lineTo(-10, 320); c.lineTo(-500, 320) } else { c.moveTo(500, -320); c.lineTo(10, -320); c.lineTo(-20, -100); c.lineTo(20, 60); c.lineTo(-10, 320); c.lineTo(500, 320) } c.closePath(); c.clip(); paper(c, 0, 0, 1000, 640, [['I will sell you this bulb,', 52, '#3a2a1a', { italic: true }], ['at this price,', 52, '#3a2a1a', { italic: true }], ['when it comes out of the ground.', 52, '#3a2a1a', { italic: true }]], { top: 160 }); c.restore() }
      post(c, { x: 960 }, { rays: false, vignette: 0.6 })
    } else {
      const cam = keys(t, [[sh.t0, { x: 960, y: 600, z: 1.05 }], [sh.t1, { x: 1000, y: 620, z: 1.2 }]])
      fields(c, cam, t, {}); post(c, cam, { rays: 0.14 })
    }
  }

  // ---------- 9: the legend: preachers, the sailor and the onion, Mackay
  SC[9] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'preacher'], [q('one told of a sailor') - 0.3, 'sailor'], [q('and was thrown') - 0.3, 'jail'], [q('two hundred years later') - 0.3, 'mackay'], [q('it was called') - 0.3, 'book'], [q('he said the whole') - 0.3, 'mad'], [q('his book is where') - 0.3, 'book2']])
    if (sh.name === 'preacher') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 560, z: 1.2 }], [sh.t1, { x: 960, y: 560, z: 1.32 }]])
      layer(c, cam, 0.9, c => { c.fillStyle = vgrad(c, -200, 1100, '#e8e0d0', '#b8ae9c'); c.fillRect(-900, -400, 3800, 1600); for (let x = -600; x < 2900; x += 420) { c.fillStyle = '#d8d0c0'; c.fillRect(x, 100, 70, 800); c.fillStyle = vgrad(c, 120, 640, '#c8d0d8', '#a8b0b8'); c.beginPath(); c.moveTo(x + 140, 640); c.lineTo(x + 140, 260); c.arc(x + 230, 260, 90, Math.PI, 0); c.lineTo(x + 320, 640); c.fill() } })
      layer(c, cam, 1, c => {
        c.fillStyle = hgrad(c, 760, 1160, '#6a4428', '#3a2414'); c.fillRect(760, 620, 400, 300); c.fillRect(720, 600, 480, 30)
        person(c, 960, 640, 0.75, { cos: 'preacher', pose: { name: 'raise', k: 0.9 }, face: { mood: 'angry', mouth: 'shout', talk: t } })
        c.fillStyle = hgrad(c, 760, 1160, '#6a4428', '#3a2414'); c.fillRect(760, 650, 400, 300)
        c.fillStyle = vgrad(c, 900, 1200, '#5a4a3a', '#2a2018'); c.fillRect(-900, 940, 3800, 400)
        const r = rng(19); for (let k = 0; k < 8; k++) paper(c, 300 + r() * 1400, 1000 + r() * 60, 90, 120, [['', 1]], { rot: (r() - 0.5) * 0.8 })
      })
      post(c, cam, { rays: 0.1 })
      word(c, 'God punishing greed', 140, prog(t, q('god punishing'), q('god punishing') + 0.3))
    } else if (sh.name === 'sailor' || sh.name === 'jail') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 720, z: 1.8 }], [sh.t1, { x: 980, y: 720, z: 1.9 }]])
      tavern(c, cam, t, { fire: false, inner: c => {
        if (sh.name === 'sailor') { const bite = prog(t, q('ate a rare bulb'), q('thinking it was') + 0.5); person(c, 860, 930, 0.78, { cos: 'sailor17', pose: { name: 'hold', at: [44, -230] }, holdFn: c => { c.save(); c.beginPath(); c.rect(-60 + bite * 50, -80, 200, 160); c.clip(); bulb(c, 0, 10, 0.32); c.restore() }, face: { mood: 'happy', mouth: bite > 0 && bite < 1 ? 'open' : 'smile' } }); table(c, 600, 980, 700, t, { n: 1, pipes: 0 }); c.fillStyle = '#c8c0b0'; ell(c, 1100, 970, 60, 12, 0, '#c8c0b0'); ell(c, 1090, 960, 40, 10, 0, '#9aa8b0') }
        else { person(c, 960, 930, 0.78, { cos: 'sailor17', pose: { name: 'sit', hands: 'head' }, face: { mood: 'sad' } }); c.fillStyle = '#1a1410'; for (let x = 600; x < 1400; x += 60) c.fillRect(x, 300, 14, 700); c.fillRect(560, 300, 880, 18); c.fillRect(560, 650, 880, 14) }
      } })
      post(c, cam, { rays: false, vignette: 0.65, night: sh.name === 'jail' ? 0.3 : 0 })
      if (sh.name === 'sailor') word(c, 'he thought it was an onion', 150, prog(t, q('thinking it was'), q('thinking it was') + 0.3))
    } else if (sh.name === 'mackay') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 600, z: 1.4 }], [sh.t1, { x: 980, y: 600, z: 1.5 }]])
      layer(c, cam, 1, c => {
        c.fillStyle = vgrad(c, 0, 900, '#3a3a44', '#1a1a22'); c.fillRect(-400, -400, 2800, 1700)
        for (let x = 300; x < 1700; x += 40) { c.fillStyle = ['#6a2a22', '#2a3a5a', '#5a4a2a', '#3a5a3a'][(x / 40 | 0) % 4]; c.fillRect(x, 300 + (x % 3) * 6, 32, 140); c.fillRect(x, 480 + (x % 4) * 6, 32, 140) }
        c.fillStyle = '#2a1c12'; c.fillRect(280, 440, 1440, 14); c.fillRect(280, 620, 1440, 14)
        c.fillStyle = hgrad(c, 600, 1500, '#6a4428', '#4a2e1a'); c.fillRect(840, 975, 700, 30); c.fillRect(870, 1005, 24, 110); c.fillRect(1490, 1005, 24, 110)
        c.fillStyle = rgrad(c, 1330, 900, 4, 420, 'rgba(255,210,130,0.35)', 'rgba(255,210,130,0)'); c.fillRect(900, 400, 900, 800); ell(c, 1330, 925, 22, 44, 0, '#d8b85a'); ell(c, 1330, 895, 14, 20, 0, 'rgba(255,230,160,0.9)')
        person(c, 770, 1110, 0.95, { cos: 'mackay', pose: { name: 'sit', hands: 'table', write: true, t, seat: 92 }, face: { look: -0.3 } })
      })
      post(c, cam, { rays: false, vignette: 0.7 })
      label(c, 'Charles Mackay, 1841', W / 2, 110, prog(t, q('charles mackay'), q('charles mackay') + 0.5))
    } else if (sh.name === 'book' || sh.name === 'book2') {
      darkBg(c)
      const z = keys(t, [[sh.t0, 1], [sh.t1, 1.06]]); c.save(); c.translate(W / 2, H / 2); c.scale(z, z); c.translate(-W / 2, -H / 2)
      c.fillStyle = 'rgba(0,0,0,0.4)'; c.fillRect(720, 160, 520, 760); c.fillStyle = hgrad(c, 700, 1200, '#2a3a2a', '#3a4a36', '#1a2a1a'); c.fillRect(700, 140, 520, 760)
      c.strokeStyle = '#c9a24a'; c.lineWidth = 3; c.strokeRect(730, 170, 460, 700)
      text(c, 'Extraordinary', 960, 300, 46, '#e8cf8a', { weight: 800 }); text(c, 'Popular Delusions', 960, 360, 42, '#e8cf8a', { weight: 700 }); text(c, 'and the', 960, 420, 30, '#e8cf8a', { italic: true }); text(c, 'Madness of Crowds', 960, 480, 42, '#e8cf8a', { weight: 700 }); text(c, 'Charles Mackay', 960, 780, 32, '#e8cf8a', { italic: true }); text(c, '1841', 960, 830, 28, '#e8cf8a')
      c.restore(); post(c, { x: 960 }, { rays: false, vignette: 0.6 })
      if (sh.name === 'book') word(c, 'never out of print', 980, prog(t, q('it has never gone'), q('it has never gone') + 0.3), 44)
    } else {
      const cam = keys(t, [[sh.t0, { x: 960, y: 620, z: 1.15 }], [sh.t1, { x: 960, y: 620, z: 1.3 }]])
      layer(c, cam, 0.06, c => sky(c, '#5a5a6a', '#b8a890', { horizon: 600, clouds: 5 }))
      layer(c, cam, 0.85, c => street(c, -900, 3000, 760, { h: 320, seed: 21 }))
      layer(c, cam, 1, c => { c.fillStyle = vgrad(c, 760, 1200, '#8a7a66', '#4a4034'); c.fillRect(-900, 760, 3800, 600); const r = rng(22), men = []; for (let k = 0; k < 18; k++) men.push({ x: 100 + r() * 1700, z: r() - 0.5, cos: BUYERS[k % BUYERS.length], f: r() > 0.5 ? 1 : -1, pose: k % 3 ? { name: 'cheer', k: 1, t: t + k } : { name: 'sit', hands: 'head' }, face: { mood: k % 3 ? 'alarm' : 'sad', mouth: 'shout' } }); crowd(c, 960, men, { s: 0.55, zy: 60, fade: 0.25, haze: '#a8a090' }) })
      post(c, cam, { rays: 0.06, grade: 'rgba(120,80,60,0.25)' })
      word(c, '“the whole country had gone mad”', 150, prog(t, sh.t0 + 0.3, sh.t0 + 0.8), 48)
    }
  }

  // ---------- 10: the archives
  SC[10] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'archive'], [q('she could not find') - 0.3, 'nobody'], [q('the traders were') - 0.3, 'few'], [q('the dutch economy') - 0.3, 'harbor'], [q('the bubble was real') - 0.3, 'real']])
    if (sh.name === 'archive' || sh.name === 'nobody') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 600, z: 1.25 }], [sh.t1, { x: 980, y: 610, z: 1.4 }]])
      layer(c, cam, 1, c => {
        c.fillStyle = vgrad(c, 0, 900, '#4a4a52', '#2a2a32'); c.fillRect(-400, -400, 2800, 1700)
        for (let row = 0; row < 4; row++) for (let x = -300; x < 2300; x += 70) { c.fillStyle = ['#c8b898', '#a89878', '#d8c8a8'][(x / 70 + row) % 3 | 0]; c.fillRect(x, 120 + row * 190, 58, 150) }
        for (let row = 0; row < 5; row++) { c.fillStyle = '#2a1c12'; c.fillRect(-400, 270 + row * 190, 2800, 14) }
        c.fillStyle = hgrad(c, 600, 1500, '#6a4428', '#4a2e1a'); c.fillRect(700, 920, 900, 30)
        for (let k = 0; k < 5; k++) paper(c, 900 + k * 110, 908, 100, 20, [], { rot: (k - 2) * 0.05 })
        person(c, 640, 1100, 0.92, { cos: 'goldgar', pose: { name: 'sit', hands: 'table', seat: 92 }, face: { look: -0.25 } })
      })
      post(c, cam, { rays: false, vignette: 0.6 })
      label(c, 'Anne Goldgar, the Dutch archives', W / 2, 110, prog(t, q('anne goldgar'), q('anne goldgar') + 0.5) * (1 - prog(t, sh.t1 - 0.6, sh.t1)))
      if (sh.name === 'nobody') word(c, 'not one bankruptcy from tulips', 150, prog(t, sh.t0 + 0.3, sh.t0 + 0.8))
    } else if (sh.name === 'few') {
      darkBg(c)
      map(c, W / 2, H / 2 - 20, 1200, 860, { draw: (c, w, h) => { text(c, 'THE DUTCH REPUBLIC', 0, -330, 46, 'rgba(70,45,25,0.85)', { weight: 800 }); const r = rng(5); for (let k = 0; k < 600; k++) ell(c, (r() - 0.5) * 1000, (r() - 0.5) * 600 + 30, 3, 3, 0, 'rgba(90,70,40,0.35)'); const r2 = rng(9); for (let k = 0; k < 40; k++) ell(c, -120 + (r2() - 0.5) * 220, 40 + (r2() - 0.5) * 180, 5, 5, 0, `rgba(138,42,30,${prog(t, sh.t0 + 0.5, sh.t0 + 1.5)})`) } })
      post(c, { x: 960 }, { rays: false, vignette: 0.5 })
      word(c, 'a few hundred people, not the whole country', 990, prog(t, sh.t0 + 0.5, sh.t0 + 1), 42)
    } else if (sh.name === 'harbor') {
      const cam = keys(t, [[sh.t0, { x: 800, y: 560, z: 1.05 }], [sh.t1, { x: 1150, y: 560, z: 1.12 }]], 'l')
      layer(c, cam, 0.06, c => sky(c, '#86a2c2', '#efe6d4', { horizon: 700, clouds: 8, sun: [1400, 200, 520] }))
      layer(c, cam, 0.35, c => street(c, -900, 2900, 640, { h: 120, fade: 0.45, hazeCol: '#c8ccd0', seed: 9 }))
      layer(c, cam, 0.7, c => { c.fillStyle = vgrad(c, 640, 1100, '#6a8090', '#2a3a46'); c.fillRect(-1400, 640, 4800, 700); for (const [x, s] of [[100, 0.5], [500, 0.55], [900, 0.62], [1300, 0.55], [1700, 0.6], [2100, 0.5]]) ship(c, x, 760, s, t) })
      layer(c, cam, 1, c => { for (const [x, s] of [[300, 0.9], [1100, 1.0], [1800, 0.95]]) ship(c, x, 900, s, t, { f: x > 1000 ? -1 : 1 }) })
      post(c, cam, { rays: 0.12 })
      word(c, 'the Golden Age went on', 150, prog(t, q('the richest years'), q('the richest years') + 0.4))
    } else {
      darkBg(c)
      chart(c, 960, 520, 1400, 760, [0.05, 0.08, 0.12, 0.2, 0.32, 0.5, 0.72, 0.95, 0.4, 0.12, 0.06], 1, {})
      post(c, { x: 960 }, { rays: false, vignette: 0.6 })
      const L = [['The bubble was real.', 'the bubble was real'], ['The prices were real.', 'the prices were real'], ['The crash was real.', 'the crash was real']]
      L.forEach(([s, w], i) => text(c, s, W / 2, 150 + i * 70, 48, '#f3e7d0', { italic: true, shadow: 16, alpha: prog(t, q(w), q(w) + 0.3) }))
      word(c, 'But the ruin was mostly a story.', 990, prog(t, q('but the ruin'), q('but the ruin') + 0.4), 50)
    }
  }

  // ---------- 11: the shape of a bubble
  SC[11] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'shape'], [q('people said the same') - 0.3, 'again'], [q('and then one ordinary') - 0.3, 'chair']])
    if (sh.name === 'shape') {
      darkBg(c)
      const pts = [0.05, 0.07, 0.1, 0.16, 0.26, 0.42, 0.66, 0.94, 0.3, 0.08]
      chart(c, 960, 540, 1400, 760, pts, prog(t, q('something rare') - 0.3, q('only what the next') + 1.4), {})
      const L = [['something rare', 'something rare'], ['prices that only go up', 'prices that only'], ['buying a promise', 'people buying a promise'], ['the next buyer', 'only what the next']]
      L.forEach(([s, w], i) => text(c, s, 400 + i * 380, 150, 40, '#f3e7d0', { italic: true, shadow: 14, alpha: prog(t, q(w), q(w) + 0.3) }))
      post(c, { x: 960 }, { rays: false, vignette: 0.6 })
    } else if (sh.name === 'again') {
      darkBg(c)
      const B = [['railway shares, 1840s', 'railway shares'], ['stocks, 1929', 'stocks in 1929'], ['houses, 2006', 'houses in 2006']]
      B.forEach(([s, w], i) => { const a = prog(t, q(w) - 0.2, q(w) + 0.4); if (a <= 0) return; c.save(); c.globalAlpha = a; TUB.chart(c, 380 + i * 580, 560, 520, 420, [0.05, 0.1, 0.2, 0.4, 0.7, 0.95, 0.3, 0.1], a, {}); c.restore(); text(c, s, 380 + i * 580, 830, 34, '#f3e7d0', { italic: true, shadow: 14, alpha: a }) })
      post(c, { x: 960 }, { rays: false, vignette: 0.6 })
    } else {
      const cam = keys(t, [[sh.t0, { x: 960, y: 720, z: 1.6 }], [sh.t1, { x: 960, y: 740, z: 1.9 }]])
      tavern(c, cam, t, { inner: c => { c.fillStyle = '#4a2e1a'; c.fillRect(900, 760, 120, 20); c.fillRect(905, 780, 16, 160); c.fillRect(1000, 780, 16, 160); c.fillRect(1000, 600, 16, 180); table(c, 300, 960, 1300, t, { n: 1, pipes: 0 }) } })
      post(c, cam, { rays: false, vignette: 0.7 })
      word(c, 'the next buyer doesn’t come', 150, prog(t, q('doesnt come'), q('doesnt come') + 0.4))
    }
  }

  // ---------- 12: tulips today
  SC[12] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'fields'], [q('the striped ones') - 0.3, 'striped'], [q('and the semper') - 0.3, 'gone'], [q('the question in') - 0.3, 'tavern'], [q('subscribe') - 0.3, 'end']])
    if (sh.name === 'fields' || sh.name === 'end') {
      const cam = keys(t, [[sh.t0, { x: 900, y: 620, z: 1.05 }], [sh.t1, { x: 1100, y: 620, z: 1.15 }]], 'l')
      fields(c, cam, t, { millX: 1400 }); post(c, cam, { rays: 0.14 })
      if (sh.name === 'fields') { word(c, 'billions of bulbs a year', 150, prog(t, q('billions'), q('billions') + 0.4) * (1 - prog(t, q('you can buy') - 0.2, q('you can buy')))); word(c, 'less than a dollar each', 150, prog(t, q('less than a dollar'), q('less than a dollar') + 0.4)) }
      else { const a = prog(t, sh.t0 + 0.3, sh.t0 + 1); text(c, 'Subscribe', W / 2, 330, 96, '#f3e7d0', { weight: 800, alpha: a, shadow: 24 }); text(c, 'animal facts  ·  great battles  ·  financial collapses', W / 2, 430, 40, '#f3e7d0', { italic: true, alpha: prog(t, q('everything from'), q('everything from') + 0.6), shadow: 14 }) }
    } else if (sh.name === 'striped' || sh.name === 'gone') {
      c.fillStyle = rgrad(c, W / 2, H / 2, 50, 1100, '#3a3028', '#120e0a'); c.fillRect(0, 0, W, H)
      if (sh.name === 'striped') { tulip(c, 700, 1000, 2.6, { col: '#f4f0ea', flame: '#c8306a', sway: Math.sin(t) * 0.03 }); tulip(c, 1220, 1020, 2.3, { col: '#f2c23a', flame: '#c8302a', sway: Math.sin(t + 1) * 0.03 }); word(c, 'bred, not sick', 150, prog(t, sh.t0 + 0.3, sh.t0 + 0.8)) }
      else { const a = 1 - prog(t, q('not one is known'), q('not one is known') + 2.2); c.save(); c.globalAlpha = a; tulip(c, 960, 1030, 3.4, { col: '#f8f4ee', flame: '#9a1420', open: 0.5 }); c.restore(); word(c, 'Semper Augustus', 150, prog(t, sh.t0 + 0.3, sh.t0 + 0.8)) }
      post(c, { x: 960 }, { rays: false, vignette: 0.55 })
    } else {
      const cam = keys(t, [[sh.t0, { x: 1000, y: 700, z: 1.5 }], [sh.t1, { x: 1350, y: 680, z: 1.9 }]])
      tavern(c, cam, t, { night: true, inner: c => { for (const row of [0, 1]) for (let k = 0; k < 6; k++) { const x = 330 + k * 220 + (row ? 70 : 0); person(c, x, row ? 960 : 880, row ? 0.92 : 0.74, { cos: BUYERS[(k + row * 3) % BUYERS.length], f: x < 1000 ? 1 : -1, pose: { name: 'stand' }, face: { mood: 'calm', talk: t + k }, fade: row ? 0.05 : 0.3, hazeCol: '#3a2418' }) } person(c, 1600, 945, 0.92, { cos: 'auctioneer', f: -1, pose: { name: 'raise', k: 1 }, holdFn: c => paper(c, 0, -10, 90, 110, [], { rot: 0.05 }) }); table(c, 200, 990, 1400, t, { candle: true }) } })
      post(c, cam, { rays: false, vignette: 0.7, grade: 'rgba(255,170,90,0.12)' })
      word(c, 'who will buy it from me tomorrow?', 150, prog(t, q('who will buy'), q('who will buy') + 0.4), 54)
    }
  }
})()
