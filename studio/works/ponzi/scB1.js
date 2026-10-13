// scB1.js: scenes 0-6 of the Ponzi story, Style B.
(function () {
  const { W, H, clamp, lerp, prog, keys, rng, ell, poly, shade, vgrad, hgrad, rgrad, layer, fog, sky, post, foreground, person, crowd, paper, map, pathLine, count, text, label, shake, flashes, tree, mixCol } = PK
  const { block, schoolStreet, car, office, desk, bills, cashPile, newspaper, coupon, stamp, steamship, mansion, pyramid, shotOf, LINE } = POB
  const SC = window.SCENES = window.SCENES || []
  const dark = c => { c.fillStyle = vgrad(c, 0, H, '#2e2a26', '#14110e'); c.fillRect(0, 0, W, H) }
  const word = (c, s, y, a, size = 54) => text(c, s, W / 2, y, size, '#f3e7d0', { italic: true, shadow: 16, alpha: a })
  // the line of people on School Street; o.k shuffles them forward; o.cash shows money in hand
  function theLine(c, t, o = {}) {
    const n = o.n || 16, r = rng(o.seed || 5), step = o.step ?? 0
    for (let k = n - 1; k >= 0; k--) { const x = (o.x0 ?? 300) + k * (o.gap || 105) - step, cos = o.cos ? o.cos(k) : LINE[k % LINE.length]
      person(c, x, 880 + (k % 2) * 6, o.s || 0.6, { cos, f: -1, pose: o.cash ? { name: 'hold', at: [44, -150] } : { name: 'stand' }, holdFn: o.cash ? c => bills(c, 0, 0, 0.32, { n: 2 }) : null, face: { mood: o.mood || 'happy', talk: o.talk ? t + k : 0, look: 0.05 }, fade: o.fade || 0 }) }
  }

  // ---------- 0: the line on School Street
  SC[0] = (c, t, q, S) => {
    const sh = shotOf(t, [[0, 'street'], [q('clerks') - 0.25, 'faces'], [q('every one of them') - 0.3, 'cash'], [q('they are waiting') - 0.3, 'door'], [q('he is taking in') - 0.3, 'count'], [q('he has not made') - 0.3, 'empty'], [q('and in three weeks') - 0.3, 'end']])
    if (sh.name === 'street' || sh.name === 'end') {
      const cam = sh.name === 'street' ? keys(t, [[0, { x: 600, y: 600, z: 1.15 }], [sh.t1, { x: 900, y: 620, z: 1.3 }]]) : keys(t, [[sh.t0, { x: 960, y: 600, z: 1.3 }], [sh.t1, { x: 960, y: 560, z: 1.05 }]])
      schoolStreet(c, cam, t, { inner: c => { theLine(c, t, { n: 22, x0: 380, gap: 95, step: (t * 4) % 95, s: 0.58 }); car(c, lerp(-400, 2600, ((t * 0.08) % 1)), 1010, 0.7, t, { d: t * 300, col: '#2a1a14' }) } })
      layer(c, cam, 1.3, c => { c.fillStyle = 'rgba(0,0,0,0)'; })
      post(c, cam, { rays: 0.12, rayX: 900 })
      if (sh.name === 'street') label(c, 'School Street, Boston  ·  July 1920', W / 2, 110, prog(t, 0.4, 1.1) * (1 - prog(t, sh.t1 - 0.8, sh.t1 - 0.2)))
    } else if (sh.name === 'faces') {
      const keysW = ['clerks', 'maids', 'shopkeepers', 'policemen']
      const idx = Math.max(0, keysW.findLastIndex(w => t >= q(w) - 0.25)), cosOf = ['clerk', 'maid', 'shopkeeper', 'police'][idx]
      const cam = { x: 700 + idx * 220, y: 690, z: 2.2 }
      schoolStreet(c, cam, t, { inner: c => theLine(c, t, { n: 12, x0: 480, gap: 220, s: 0.78, cos: k => ['clerk', 'maid', 'shopkeeper', 'police'][k % 4] }) })
      post(c, cam, { rays: 0.12 })
      word(c, ['Clerks', 'Maids', 'Shopkeepers', 'Policemen in uniform'][idx], 150, prog(t, q(keysW[idx]) - 0.2, q(keysW[idx]) + 0.1))
    } else if (sh.name === 'cash') {
      const cam = keys(t, [[sh.t0, { x: 900, y: 720, z: 2.4 }], [sh.t1, { x: 1100, y: 720, z: 2.6 }]], 'l')
      schoolStreet(c, cam, t, { inner: c => theLine(c, t, { n: 12, x0: 480, gap: 160, s: 0.78, cash: true }) })
      post(c, cam, { rays: 0.1 })
      word(c, 'their savings', 150, prog(t, q('their savings'), q('their savings') + 0.3) * (1 - prog(t, q('their mortgage') - 0.2, q('their mortgage'))))
      word(c, 'their mortgage money', 150, prog(t, q('their mortgage'), q('their mortgage') + 0.3))
    } else if (sh.name === 'door') {
      // through the door: the small man in the good suit, at a desk, smiling
      const cam = keys(t, [[sh.t0, { x: 960, y: 640, z: 1.45 }], [sh.t1, { x: 980, y: 650, z: 1.6 }]])
      office(c, cam, t, { door: ['SECURITIES', 'EXCHANGE CO.'], inner: c => { person(c, 1240, 1010, 0.92, { cos: 'ponzi', pose: { name: 'sit', hands: 'table' }, face: { mood: 'happy', talk: t } }); desk(c, 1080, 900, 520, { lamp: true }); cashPile(c, 1340, 890, 6, 0.8); person(c, 640, 1040, 0.92, { cos: 'maid', pose: { name: 'hold', at: [50, -150] }, holdFn: c => bills(c, 0, 0, 0.36, { n: 2 }), face: { mood: 'happy' } }) } })
      post(c, cam, { rays: false, vignette: 0.6 })
      word(c, 'double your money in 90 days', 150, prog(t, q('promised to double'), q('promised to double') + 0.4))
    } else if (sh.name === 'count') {
      dark(c)
      const v = Math.round(lerp(0, 250000, prog(t, sh.t0 + 0.2, sh.t1 - 0.6, 'o')) / 1000) * 1000
      cashPile(c, W / 2, 900, Math.round(prog(t, sh.t0, sh.t1) * 26) + 2, 1.6)
      count(c, W / 2, 360, '$' + v.toLocaleString('en-US'), 150); word(c, 'a day', 470, prog(t, sh.t0 + 0.5, sh.t0 + 1), 50)
      post(c, { x: 960 }, { rays: false, vignette: 0.6 })
    } else {
      // the empty ledger: nothing invested
      dark(c)
      paper(c, 960, 520, 1100, 700, [['Investments', 60, '#3a2a1a', { italic: true }], ['', 30], ['—', 60, '#8a2a1e'], ['', 10], ['none', 70, '#8a2a1e', { weight: 800 }]], { top: 120, rot: -0.01 })
      post(c, { x: 960 }, { rays: false, vignette: 0.6 })
    }
  }

  // ---------- 1: Carlo Ponzi, the boat, $2.50, dishes
  SC[1] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'italy'], [q('he came to america') - 0.3, 'boat'], [q('he walked off') - 0.3, 'dock'], [q('he washed dishes') - 0.3, 'dishes']])
    if (sh.name === 'italy') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 620, z: 1.2 }], [sh.t1, { x: 1000, y: 630, z: 1.35 }]])
      layer(c, cam, 0.06, c => sky(c, '#88a4c4', '#f2dcc0', { horizon: 700, clouds: 3, sun: [400, 260, 600, '255,210,160'] }))
      layer(c, cam, 0.3, c => PK.ridge(c, 31, 640, 90, 140, '#8a9a7a', '#6a7a5a'))
      layer(c, cam, 0.7, c => { const r = rng(2); for (let k = 0; k < 9; k++) { const x = 100 + k * 200, y = 800 - (k % 3) * 30; c.fillStyle = hgrad(c, x, x + 170, '#e8d0a8', '#c8a878'); c.fillRect(x, y - 150, 170, 150); poly(c, [[x - 10, y - 150], [x + 85, y - 200], [x + 180, y - 150]], '#a8523a'); c.fillStyle = '#4a3a2a'; c.fillRect(x + 30, y - 110, 30, 50); c.fillRect(x + 110, y - 110, 30, 50) } for (let x = -400; x < 2400; x += 220) tree(c, x, 820, 260, 'poplar', { seed: 1 }) })
      layer(c, cam, 1, c => { c.fillStyle = vgrad(c, 820, 1200, '#b89a6a', '#7a6040'); c.fillRect(-900, 820, 3800, 600); person(c, 900, 960, 0.7, { cos: 'ponziY', pose: { name: 'stand' }, face: { mood: 'happy' } }) })
      post(c, cam, { rays: 0.16, rayX: 200 })
      label(c, 'Italy, 1882', W / 2, 110, prog(t, sh.t0 + 0.4, sh.t0 + 1) * (1 - prog(t, sh.t1 - 0.8, sh.t1 - 0.2)))
      text(c, 'Carlo Ponzi', 900 + (900 - cam.x) * 0.35, 380, 44, '#f3e7d0', { italic: true, shadow: 14, alpha: prog(t, sh.t0 + 0.8, sh.t0 + 1.4) })
    } else if (sh.name === 'boat') {
      // gambling on the ship's deck: cards on a crate, his coins gone
      const cam = keys(t, [[sh.t0, { x: 960, y: 640, z: 1.6 }], [sh.t1, { x: 980, y: 650, z: 1.75 }]])
      layer(c, cam, 0.06, c => sky(c, '#5a6a80', '#c8c0b0', { horizon: 700, clouds: 6 }))
      layer(c, cam, 0.3, c => { c.fillStyle = vgrad(c, 700, 1000, '#4a5a6a', '#2a3440'); c.fillRect(-1400, 700, 4800, 600) })
      layer(c, cam, 1, c => {
        c.fillStyle = vgrad(c, 820, 1200, '#8a7458', '#5a4a36'); c.fillRect(-900, 820, 3800, 600); c.fillStyle = '#3a3028'; c.fillRect(-900, 600, 3800, 22); for (let x = -900; x < 2900; x += 80) c.fillRect(x, 600, 10, 230)
        c.fillStyle = hgrad(c, 820, 1100, '#7a5a36', '#5a3e22'); c.fillRect(820, 870, 280, 120)
        for (let k = 0; k < 5; k++) { c.fillStyle = '#f2eee4'; c.save(); c.translate(870 + k * 40, 866); c.rotate((k - 2) * 0.15); c.fillRect(-14, -20, 28, 40); c.restore() }
        person(c, 720, 990, 0.85, { cos: 'ponziY', pose: { name: 'sit', hands: 'head' }, face: { mood: 'sad' } })
        person(c, 1220, 990, 0.85, { cos: 'jpsailor', f: -1, pose: { name: 'sit', hands: 'hold' }, face: { mood: 'happy' } })
      })
      post(c, cam, { rays: 0.06, grade: 'rgba(60,70,90,0.2)' })
      word(c, 'he gambled away his savings', 150, prog(t, q('he gambled'), q('he gambled') + 0.4))
    } else if (sh.name === 'dock') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 600, z: 1.15 }], [sh.t1, { x: 900, y: 640, z: 1.45 }]])
      layer(c, cam, 0.06, c => sky(c, '#8aa0b8', '#e8e0d0', { horizon: 700, clouds: 6 }))
      layer(c, cam, 0.5, c => { const r = rng(3); let x = -900; while (x < 2900) { const w = 140 + r() * 100; block(c, x, 640, w, 200 + r() * 160, { col: mixCol('#8a6a5a', '#c8c8c8', 0.4) }); x += w + 6 } })
      layer(c, cam, 0.8, c => { c.fillStyle = vgrad(c, 660, 1000, '#5a6a78', '#2a3440'); c.fillRect(-1400, 660, 4800, 500); steamship(c, 1300, 800, 0.9, t) })
      layer(c, cam, 1, c => { c.fillStyle = vgrad(c, 860, 1200, '#6a5a48', '#3a3024'); c.fillRect(-900, 860, 3800, 600); const d = (t - sh.t0) * 50; person(c, 600 + d, 990, 0.8, { cos: 'ponziY', pose: { name: 'walk', d }, face: { mood: 'happy' } }) })
      post(c, cam, { rays: 0.1 })
      label(c, 'Boston, 1903', W / 2, 110, prog(t, sh.t0 + 0.3, sh.t0 + 0.9) * (1 - prog(t, sh.t1 - 0.8, sh.t1 - 0.2)))
      count(c, W / 2, 300, '$2.50', 130); word(c, '…and a million dollars in hopes', 410, prog(t, q('and a million'), q('and a million') + 0.4), 46)
    } else {
      // a restaurant kitchen: dishes, then the dining room with an apron, then the door
      const cam = keys(t, [[sh.t0, { x: 900, y: 660, z: 1.6 }], [sh.t1, { x: 1100, y: 660, z: 1.7 }]], 'l')
      office(c, cam, t, { wall: '#c8bca0', window: false, cabinets: [], inner: c => {
        c.fillStyle = hgrad(c, 500, 1000, '#8a8a90', '#5a5a62'); c.fillRect(500, 860, 520, 40); c.fillRect(520, 900, 20, 120)
        for (let k = 0; k < 6; k++) ell(c, 600 + k * 50, 850 - k * 6, 40, 10, 0, '#f2f0ea')
        const fired = t > q('he got fired')
        person(c, fired ? lerp(760, 1700, prog(t, q('he got fired'), q('he got fired') + 1.6)) : t > q('he waited tables') ? 1300 : 760, 1010, 0.85, { cos: 'waiter', f: fired ? 1 : -1, pose: fired ? { name: 'walk', d: t * 60 } : t > q('he waited tables') ? { name: 'hold', at: [60, -180] } : { name: 'stand' }, holdFn: c => ell(c, 0, 0, 50, 10, 0, '#f2f0ea'), face: { mood: fired ? 'sad' : 'calm' } })
      } })
      post(c, cam, { rays: false, vignette: 0.6 })
      word(c, 'fired for shortchanging the customers', 150, prog(t, q('he got fired'), q('he got fired') + 0.4), 46)
    }
  }

  // ---------- 2: Montreal, the bank that paid the old with the new
  SC[2] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'bank'], [q('ponzi worked out') - 0.3, 'trick'], [q('the bank collapsed') - 0.3, 'collapse'], [q('ponzi broke again') - 0.3, 'prison'], [q('but he had seen') - 0.3, 'seen']])
    const bankRoom = (cam, inner) => office(c, cam, t, { wall: '#5a4a3a', door: null, cabinets: [], inner: c => {
      c.fillStyle = hgrad(c, 300, 1700, '#5a3a22', '#3a2414'); c.fillRect(300, 780, 1400, 140); c.fillStyle = '#6a4428'; c.fillRect(290, 770, 1420, 14)
      c.strokeStyle = '#c8a24a'; c.lineWidth = 4; for (let x = 320; x < 1690; x += 40) { c.beginPath(); c.moveTo(x, 560); c.lineTo(x, 770); c.stroke() } c.beginPath(); c.moveTo(300, 560); c.lineTo(1700, 560); c.stroke()
      for (const x of [560, 1100, 1500]) person(c, x, 880, 0.7, { cos: 'teller', f: 1, pose: { name: 'stand' }, face: { mood: 'calm' } })
      c.fillStyle = hgrad(c, 300, 1700, '#5a3a22', '#3a2414'); c.fillRect(300, 780, 1400, 140)
      inner && inner(c)
    } })
    if (sh.name === 'bank' || sh.name === 'collapse') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 640, z: 1.2 }], [sh.t1, { x: 1000, y: 650, z: 1.35 }]])
      bankRoom(cam, c => { const r = rng(6); const n = sh.name === 'bank' ? 9 : 14; for (let k = 0; k < n; k++) person(c, 200 + k * 140 + r() * 30, 1060, 0.85, { cos: ['clerk', 'maid', 'shopkeeper', 'lady', 'suit'][k % 5], f: 1, pose: sh.name === 'collapse' ? { name: 'cheer', k: 0.7, t: t + k } : { name: 'stand' }, face: { mood: sh.name === 'collapse' ? 'angry' : 'calm', mouth: sh.name === 'collapse' ? 'shout' : null } }) })
      post(c, cam, { rays: false, vignette: 0.6 })
      if (sh.name === 'bank') { label(c, 'Montreal, 1907', W / 2, 110, prog(t, sh.t0 + 0.4, sh.t0 + 1) * (1 - prog(t, q('the bank was famous') - 0.4, q('the bank was famous')))); count(c, W / 2, 280, '6%', 140); word(c, 'double what anybody else paid', 390, prog(t, q('double what'), q('double what') + 0.4), 46) }
      else word(c, 'the owner ran for Mexico', 150, prog(t, q('the owner ran'), q('the owner ran') + 0.4))
    } else if (sh.name === 'trick') {
      dark(c)
      // two rows of depositors: money from the new row flows up to pay the old row
      const k = prog(t, q('it was paying'), q('money') + 0.8)
      for (let i = 0; i < 5; i++) { person(c, 520 + i * 220, 480, 0.75, { cos: ['clerk', 'maid', 'shopkeeper', 'lady', 'suit'][i], pose: { name: 'stand' }, face: { mood: 'happy' } }); person(c, 420 + i * 260, 960, 0.8, { cos: ['suit', 'lady', 'clerk', 'maid', 'shopkeeper'][i], pose: { name: 'hold', at: [44, -150] }, holdFn: c => bills(c, 0, 0, 0.32, { n: 1 }) }) }
      for (let i = 0; i < 5; i++) { const x0 = 460 + i * 260, x1 = 540 + i * 220, u = clamp(k * 1.4 - i * 0.1); if (u > 0) { bills(c, lerp(x0, x1, u), lerp(800, 380, u), 0.4, { n: 1 }); c.strokeStyle = 'rgba(243,231,208,0.4)'; c.lineWidth = 3; c.setLineDash([10, 10]); c.beginPath(); c.moveTo(x0, 800); c.lineTo(lerp(x0, x1, u), lerp(800, 380, u)); c.stroke(); c.setLineDash([]) } }
      text(c, 'old depositors', W / 2, 130, 44, '#f3e7d0', { italic: true, shadow: 14 }); text(c, 'new depositors', W / 2, 1010, 44, '#f3e7d0', { italic: true, shadow: 14 })
      post(c, { x: 960 }, { rays: false, vignette: 0.55 })
    } else if (sh.name === 'prison') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 640, z: 1.5 }], [sh.t1, { x: 980, y: 640, z: 1.6 }]])
      office(c, cam, t, { wall: '#5a5a58', window: false, cabinets: [], inner: c => { person(c, 960, 1010, 0.92, { cos: 'ponziP', pose: { name: 'sit', hands: 'head' }, face: { mood: 'sad' } }); c.fillStyle = '#1a1814'; for (let x = 500; x < 1460; x += 64) c.fillRect(x, 160, 16, 900); c.fillRect(460, 160, 1040, 20); c.fillRect(460, 620, 1040, 16) } })
      post(c, cam, { rays: false, vignette: 0.75, night: 0.15 })
      word(c, 'three years, Canada', 150, prog(t, q('three years'), q('three years') + 0.4) * (1 - prog(t, q('then two more') - 0.2, q('then two more'))))
      word(c, 'two more, Atlanta', 150, prog(t, q('then two more'), q('then two more') + 0.4))
    } else {
      const cam = keys(t, [[sh.t0, { x: 960, y: 640, z: 1.9 }], [sh.t1, { x: 960, y: 640, z: 2.2 }]])
      bankRoom(cam, c => person(c, 960, 1060, 0.85, { cos: 'ponziY', pose: { name: 'stand' }, face: { mood: 'stern', look: 0.1 } }))
      post(c, cam, { rays: false, vignette: 0.7, grade: 'rgba(120,80,60,0.25)' })
    }
  }

  // ---------- 3: the coupon
  SC[3] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'office'], [q('then a letter came') - 0.3, 'letter'], [q('you could buy one') - 0.3, 'how'], [q('ponzi noticed') - 0.3, 'map'], [q('on paper it was') - 0.3, 'profit']])
    if (sh.name === 'office' || sh.name === 'letter') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 660, z: 1.5 }], [sh.t1, { x: 1000, y: 680, z: 1.7 }]])
      office(c, cam, t, { inner: c => { person(c, 1120, 1010, 0.92, { cos: 'ponzi', pose: sh.name === 'letter' ? { name: 'sit', hands: 'hold' } : { name: 'sit', hands: 'table' }, holdFn: sh.name === 'letter' ? c => paper(c, 0, 0, 120, 90, [], { rot: -0.1 }) : null, face: { mood: sh.name === 'letter' ? 'alarm' : 'sad', look: -0.1 } }); desk(c, 960, 900, 520, { lamp: true }) } })
      post(c, cam, { rays: false, vignette: 0.6 })
      if (sh.name === 'office') { label(c, 'Boston, 1919', W / 2, 110, prog(t, sh.t0 + 0.4, sh.t0 + 1) * (1 - prog(t, sh.t1 - 0.8, sh.t1 - 0.2))); word(c, 'no bank would lend him a dime', 200, prog(t, q('no bank'), q('no bank') + 0.4)) }
      else word(c, 'a letter from Spain', 150, prog(t, sh.t0 + 0.3, sh.t0 + 0.8))
    } else if (sh.name === 'how') {
      dark(c)
      coupon(c, W / 2, 480, 2.2 * keys(t, [[sh.t0, 0.95], [sh.t1, 1.05]]), { rot: -0.03 })
      const a = prog(t, q('could trade it for stamps'), q('could trade it for stamps') + 0.5)
      for (let k = 0; k < 4; k++) { c.save(); c.globalAlpha = a; stamp(c, 560 + k * 270, 900, 1.2, ['#8a2a2a', '#2a4a8a', '#3a6a3a', '#8a6a2a'][k]); c.restore() }
      post(c, { x: 960 }, { rays: false, vignette: 0.55 })
      word(c, 'an international reply coupon', 140, prog(t, sh.t0 + 0.2, sh.t0 + 0.8), 46)
    } else if (sh.name === 'map') {
      dark(c)
      map(c, W / 2, H / 2 - 20, 1500, 860, { draw: (c, w, h) => {
        c.fillStyle = 'rgba(90,120,140,0.3)'; c.fillRect(-300, -h / 2 + 20, 380, h - 40)
        text(c, 'ATLANTIC', -110, 0, 40, 'rgba(50,70,90,0.6)', { italic: true, rot: -1.5 })
        text(c, 'BOSTON', -520, -60, 44, 'rgba(70,45,25,0.85)', { weight: 800 }); text(c, 'ITALY', 450, 120, 44, 'rgba(70,45,25,0.85)', { weight: 800 })
        ell(c, -520, 0, 12, 12, 0, '#8a2a1e'); ell(c, 450, 170, 12, 12, 0, '#8a2a1e')
        const k = prog(t, q('a coupon bought'), q('several times as much') + 0.6)
        const end = pathLine(c, [[450, 170], [200, 40], [-100, -40], [-520, 0]], k, '#8a2a1e', 6); if (end) coupon(c, end[0], end[1] - 60, 0.4)
        text(c, 'pennies', 450, 240, 40, `rgba(138,42,30,${prog(t, q('for pennies'), q('for pennies') + 0.4)})`, { weight: 800, italic: true })
        text(c, 'stamps worth several times as much', -420, 80, 32, `rgba(138,42,30,${prog(t, q('several times'), q('several times') + 0.4)})`, { weight: 800, italic: true })
      } })
      post(c, { x: 960 }, { rays: false, vignette: 0.5 })
      word(c, 'the war had wrecked Europe’s money', 990, prog(t, q('the war had'), q('the war had') + 0.4) * (1 - prog(t, q('a coupon bought') - 0.2, q('a coupon bought'))), 42)
    } else {
      dark(c)
      count(c, W / 2, 440, '400%', 220); word(c, 'on paper', 260, prog(t, sh.t0 + 0.2, sh.t0 + 0.6)); word(c, 'and perfectly legal', 640, prog(t, q('perfectly legal'), q('perfectly legal') + 0.4))
      post(c, { x: 960 }, { rays: false, vignette: 0.55 })
    }
  }

  // ---------- 4: one problem; the offer
  SC[4] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'problem'], [q('to cover what') - 0.3, 'numbers'], [q('in january 1920') - 0.3, 'opening'], [q('and he made an offer') - 0.3, 'offer'], [q('the banks were paying') - 0.3, 'banks']])
    if (sh.name === 'problem') {
      dark(c)
      for (let k = 0; k < 5; k++) coupon(c, 420 + k * 270, 520 + (k % 2) * 40, 0.75, { rot: (k - 2) * 0.08 })
      word(c, 'a few cents each', 200, prog(t, q('worth a few cents'), q('worth a few cents') + 0.4) * (1 - prog(t, q('the post office') - 0.2, q('the post office'))))
      word(c, 'stamps, not cash', 200, prog(t, q('for stamps not cash'), q('for stamps not cash') + 0.4) * (1 - prog(t, q('and there were hardly') - 0.2, q('and there were hardly'))))
      word(c, 'and hardly any of them', 200, prog(t, q('and there were hardly'), q('and there were hardly') + 0.4))
      post(c, { x: 960 }, { rays: false, vignette: 0.55 })
    } else if (sh.name === 'numbers') {
      dark(c); word(c, 'to cover what he would end up promising', 150, prog(t, sh.t0 + 0.2, sh.t0 + 0.7) * (1 - prog(t, q('he needed 160') - 0.3, q('he needed 160'))), 46)
      const a = prog(t, q('he needed 160'), q('he needed 160') + 0.6), b = prog(t, q('there were about'), q('there were about') + 0.6)
      c.fillStyle = `rgba(170,40,30,${a})`; c.fillRect(300, 300, 1320 * a, 120); text(c, '160,000,000 coupons needed', 960, 270, 44, '#f3e7d0', { italic: true, shadow: 14, alpha: a })
      c.fillStyle = `rgba(243,231,208,${b})`; c.fillRect(300, 700, Math.max(3, 1320 * 27000 / 160000000), 120); text(c, 'about 27,000 in the whole world', 960, 660, 44, '#f3e7d0', { italic: true, shadow: 14, alpha: b })
      text(c, '(the thin line)', 960, 870, 30, '#f3e7d0', { italic: true, alpha: b * 0.8 })
      post(c, { x: 960 }, { rays: false, vignette: 0.55 })
    } else if (sh.name === 'opening') {
      const cam = keys(t, [[sh.t0, { x: 900, y: 600, z: 1.25 }], [sh.t1, { x: 1000, y: 620, z: 1.45 }]])
      schoolStreet(c, cam, t, { night: false, inner: c => person(c, 1050, 880, 0.62, { cos: 'ponzi', pose: { name: 'wave', t }, face: { mood: 'happy' } }) })
      post(c, cam, { rays: 0.1, grade: 'rgba(160,180,220,0.15)' })
      label(c, 'January 1920', W / 2, 110, prog(t, sh.t0 + 0.3, sh.t0 + 0.9))
    } else if (sh.name === 'offer') {
      dark(c)
      paper(c, 960, 520, 1100, 760, [['Securities Exchange Company', 40, '#3a2a1a', { italic: true }], ['', 30], ['50% interest', 92, '#8a2a1e', { weight: 800 }], ['in 45 days', 56], ['', 30], ['or double your money', 52, '#3a2a1a', { alpha: prog(t, q('or double'), q('or double') + 0.4) }], ['in 90 days', 52, '#3a2a1a', { alpha: prog(t, q('or double'), q('or double') + 0.4) }]], { top: 110, rot: 0.01 })
      post(c, { x: 960 }, { rays: false, vignette: 0.55 })
    } else {
      dark(c)
      text(c, '5%', 560, 460, 200, '#f3e7d0', { weight: 800, shadow: 20 }); text(c, 'a year, at the bank', 560, 600, 40, '#f3e7d0', { italic: true, alpha: prog(t, q('a year'), q('a year') + 0.4) })
      text(c, '50%', 1360, 460, 200, '#c8483a', { weight: 800, shadow: 20 }); text(c, 'in 45 days, Ponzi', 1360, 600, 40, '#f3e7d0', { italic: true })
      post(c, { x: 960 }, { rays: false, vignette: 0.55 })
    }
  }

  // ---------- 5: it grows
  SC[5] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'eighteen'], [q('he paid them with') - 0.3, 'chain'], [q('and those first') - 0.3, 'tell'], [q('by march') - 0.3, 'grow'], [q('by july') - 0.3, 'clerks'], [q('three out of four') - 0.3, 'police']])
    if (sh.name === 'eighteen') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 660, z: 1.35 }], [sh.t1, { x: 980, y: 660, z: 1.45 }]])
      office(c, cam, t, { inner: c => { desk(c, 1100, 900, 520, { lamp: true }); person(c, 1300, 1010, 0.9, { cos: 'ponzi', pose: { name: 'sit', hands: 'table' }, face: { mood: 'happy', talk: t } }); for (let k = 0; k < 6; k++) person(c, 200 + k * 140, 1040, 0.8, { cos: LINE[k], f: 1, pose: t > q('he paid them') - 6 && t > q('in full') ? { name: 'cheer', k: 0.8, t: t + k } : { name: 'hold', at: [44, -150] }, holdFn: c => bills(c, 0, 0, 0.32, { n: 1 }), face: { mood: 'happy' } }) } })
      post(c, cam, { rays: false, vignette: 0.6 })
      count(c, W / 2, 240, t < q('45 days later') ? '18 people · $1,800' : 'paid in full, with interest', 70)
    } else if (sh.name === 'chain') {
      dark(c)
      pyramid(c, W / 2, 300, 4, prog(t, sh.t0 + 0.3, sh.t1 - 0.3))
      text(c, 'paid', W / 2, 220, 40, '#f3e7d0', { italic: true, shadow: 14 }); text(c, 'with the money of the people who came next', W / 2, 620, 40, '#f3e7d0', { italic: true, shadow: 14, alpha: prog(t, sh.t0 + 0.8, sh.t0 + 1.4) })
      post(c, { x: 960 }, { rays: false, vignette: 0.55 })
    } else if (sh.name === 'tell') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 640, z: 1.6 }], [sh.t1, { x: 960, y: 640, z: 1.4 }]])
      schoolStreet(c, cam, t, { inner: c => { const pairs = [[500, 'clerk', 'maid'], [1000, 'shopkeeper', 'lady'], [1500, 'police', 'suit']]; pairs.forEach(([x, a, b]) => { person(c, x, 880, 0.65, { cos: a, pose: { name: 'point' }, target: [x + 300, 600], face: { mood: 'happy', talk: t } }); person(c, x + 170, 880, 0.65, { cos: b, f: -1, pose: { name: 'stand' }, face: { mood: 'alarm' } }) }) } })
      post(c, cam, { rays: 0.1 })
      word(c, 'they told everyone they knew', 150, prog(t, q('they told'), q('they told') + 0.4))
    } else if (sh.name === 'grow') {
      dark(c)
      const steps = [['march', '$25,000', 0.1], ['may', '$420,000', 0.3], ['june', '$2,500,000', 1]]
      const cur = steps.filter(s => t >= q('by ' + s[0])).pop() || steps[0]
      steps.forEach(([m, v, f], i) => { const a = prog(t, q('by ' + m), q('by ' + m) + 0.4); c.fillStyle = `rgba(${i === 2 ? '200,72,58' : '243,231,208'},${a})`; const hgt = 600 * Math.pow(f, 0.6); c.fillRect(460 + i * 380, 900 - hgt * a, 220, hgt * a); text(c, m[0].toUpperCase() + m.slice(1), 570 + i * 380, 950, 40, '#f3e7d0', { italic: true, alpha: a }); text(c, v, 570 + i * 380, 860 - hgt * a, 46, '#f3e7d0', { weight: 800, alpha: a, shadow: 14 }) })
      post(c, { x: 960 }, { rays: false, vignette: 0.55 })
    } else if (sh.name === 'clerks') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 660, z: 1.4 }], [sh.t1, { x: 1000, y: 660, z: 1.6 }]])
      office(c, cam, t, { inner: c => { for (let k = 0; k < 3; k++) { desk(c, 260 + k * 520, 900, 420); person(c, 360 + k * 520, 1010, 0.85, { cos: 'clerk', pose: { name: 'sit', hands: 'table', write: true, t: t + k }, face: { mood: 'alarm', look: -0.3 } }); cashPile(c, 520 + k * 520, 890, 10 + Math.round(prog(t, sh.t0, sh.t1) * 10), 0.8) } } })
      post(c, cam, { rays: false, vignette: 0.6 })
      word(c, 'they let it ride', 150, prog(t, q('let it ride'), q('let it ride') + 0.4))
    } else {
      const cam = keys(t, [[sh.t0, { x: 960, y: 700, z: 1.7 }], [sh.t1, { x: 960, y: 700, z: 1.85 }]])
      schoolStreet(c, cam, t, { inner: c => { for (let k = 0; k < 4; k++) person(c, 640 + k * 210, 880, 0.75, { cos: k === 3 ? 'clerk' : 'police', f: -1, pose: k === 3 ? { name: 'stand' } : { name: 'hold', at: [44, -150] }, holdFn: c => bills(c, 0, 0, 0.32, { n: 1 }), face: { mood: 'happy' } }) } })
      post(c, cam, { rays: 0.1 })
      word(c, '3 out of 4 Boston policemen', 150, prog(t, sh.t0 + 0.3, sh.t0 + 0.8))
    }
  }

  // ---------- 6: the high life
  SC[6] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'mansion'], [q('he bought a custom') - 0.3, 'car'], [q('and he bought control') - 0.3, 'bank'], [q('when a financial writer') - 0.3, 'court'], [q('when he walked') - 0.3, 'cheer']])
    if (sh.name === 'mansion') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 600, z: 1.1 }], [sh.t1, { x: 960, y: 620, z: 1.25 }]])
      layer(c, cam, 0.06, c => sky(c, '#88a8c8', '#f0e4cc', { horizon: 700, clouds: 6, sun: [1500, 160, 520] }))
      layer(c, cam, 0.5, c => PK.forest(c, -800, 2800, 700, 200, { kind: 'oak', fade: 0.25, hazeCol: '#c8ccc4' }))
      layer(c, cam, 1, c => { c.fillStyle = vgrad(c, 760, 1200, '#6a8a4a', '#3a5a2a'); c.fillRect(-900, 760, 3800, 600); mansion(c, 960, 800, 1.1); c.fillStyle = '#c8bca0'; poly(c, [[920, 800], [1000, 800], [1200, 1100], [720, 1100]]); c.fill() })
      post(c, cam, { rays: 0.14 })
      label(c, 'Lexington, Massachusetts', W / 2, 110, prog(t, sh.t0 + 0.3, sh.t0 + 0.9) * (1 - prog(t, sh.t1 - 0.8, sh.t1 - 0.2)))
    } else if (sh.name === 'car') {
      const cam = keys(t, [[sh.t0, { x: 900, y: 760, z: 1.6 }], [sh.t1, { x: 1100, y: 760, z: 1.7 }]], 'l')
      schoolStreet(c, cam, t, { inner: c => { const x = lerp(400, 1400, prog(t, sh.t0, sh.t1)); car(c, x, 1010, 1.15, t, { d: x * 2, col: '#2a3a5a' }); person(c, x + 20, 900, 0.5, { cos: 'ponzi', pose: { name: 'sit' }, face: { mood: 'happy' }, noShadow: true }) } })
      post(c, cam, { rays: 0.12 })
      word(c, 'a custom Locomobile', 150, prog(t, q('locomobile'), q('locomobile') + 0.4))
    } else if (sh.name === 'bank') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 560, z: 1.15 }], [sh.t1, { x: 960, y: 580, z: 1.3 }]])
      layer(c, cam, 0.06, c => sky(c, '#88a8c8', '#f0e4cc', { horizon: 600, clouds: 4 }))
      layer(c, cam, 1, c => { block(c, 360, 900, 1200, 760, { col: '#b8ae9c', sign: 'HANOVER TRUST COMPANY', signY: 90, signSize: 44 }); for (let k = 0; k < 6; k++) { c.fillStyle = hgrad(c, 0, 0, '#e8e2d6', '#c8c0b0'); c.fillStyle = '#e8e2d6'; c.fillRect(420 + k * 210, 380, 50, 400) } c.fillStyle = vgrad(c, 900, 1200, '#8a847a', '#4a4640'); c.fillRect(-900, 900, 3800, 600); person(c, 960, 1000, 0.75, { cos: 'ponzi', pose: { name: 'stand' }, face: { mood: 'happy' } }) })
      post(c, cam, { rays: 0.1 })
      word(c, 'the bank that turned him down', 160, prog(t, q('the same bank'), q('the same bank') + 0.4))
    } else if (sh.name === 'court') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 700, z: 1.45 }], [sh.t1, { x: 960, y: 700, z: 1.6 }]])
      office(c, cam, t, { wall: '#4a3424', window: false, cabinets: [], inner: c => { c.fillStyle = hgrad(c, 700, 1220, '#6a4428', '#3a2414'); c.fillRect(700, 720, 520, 180); person(c, 960, 800, 0.8, { cos: 'judge', pose: { name: 'sit', hands: 'table' }, face: { mood: 'stern' } }); c.fillStyle = hgrad(c, 700, 1220, '#6a4428', '#3a2414'); c.fillRect(700, 720, 520, 180); person(c, 420, 1060, 0.9, { cos: 'ponzi', pose: t > q('and won') ? { name: 'cheer', k: 1, t } : { name: 'point' }, target: [1500, 800], face: { mood: 'happy' } }); person(c, 1500, 1060, 0.9, { cos: 'reporter', f: -1, pose: { name: 'stand' }, face: { mood: 'sad' } }) } })
      post(c, cam, { rays: false, vignette: 0.65 })
      if (t > q('and won')) { count(c, W / 2, 220, '$500,000', 100); word(c, 'for libel', 320, prog(t, q('half a million'), q('half a million') + 0.4), 44) }
    } else {
      const cam = keys(t, [[sh.t0, { x: 960, y: 660, z: 1.4 }], [sh.t1, { x: 1060, y: 660, z: 1.55 }]], 'l')
      schoolStreet(c, cam, t, { inner: c => { const r = rng(4); for (let k = 0; k < 14; k++) person(c, 200 + k * 120, 880 + (k % 2) * 8, 0.6, { cos: LINE[k % LINE.length], f: k < 7 ? 1 : -1, pose: { name: 'cheer', k: 1, t: t + k * 0.7 }, face: { mood: 'happy', mouth: 'shout' } }); person(c, 960 + (t - sh.t0) * 30, 960, 0.72, { cos: 'ponzi', pose: { name: 'walk', d: (t - sh.t0) * 30 }, face: { mood: 'happy' } }) } })
      post(c, cam, { rays: 0.12 })
    }
  }
})()
