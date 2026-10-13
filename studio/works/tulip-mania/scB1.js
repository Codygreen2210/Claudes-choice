// scB1.js: scenes 0-6 of Tulip Mania, Style B.
(function () {
  const { W, H, clamp, lerp, prog, keys, rng, ell, poly, shade, vgrad, hgrad, rgrad, layer, fog, sky, post, foreground, tuft, person, crowd, beast, birds, tree, forest, paper, map, pathLine, count, text, label, shake, flashes } = PK
  const { tulip, bulb, gable, street, canal, ship, windmill, tavern, table, polder, fields, chart, shotOf, BUYERS } = TUB
  const SC = window.SCENES = window.SCENES || []

  // a room full of bidders behind a table; hands go up as the price climbs
  function bidders(c, t, o = {}) {
    // two rows of buyers: a back row (smaller, hazier) and a front row, with hands going up as the price climbs
    const r = rng(o.seed || 3), n = o.n || 16
    for (const row of [0, 1]) for (let k = 0; k < n / 2; k++) {
      const x = 330 + k * (1250 / (n / 2 - 1)) + (row ? 60 : 0) + (r() - 0.5) * 40, up = o.bid ? Math.sin(t * 2.2 + k * 1.7 + row * 2) > 0.55 : false
      person(c, x, row ? 960 : 880, row ? 0.92 : 0.74, { cos: BUYERS[(k + row * 3) % BUYERS.length], f: x < 1000 ? 1 : -1, pose: up ? { name: 'raise', k: 1 } : { name: 'stand' }, face: { mood: o.mood || (up ? 'happy' : 'calm'), look: 0.1, talk: o.talk ? t + k : 0 }, fade: row ? 0.05 : 0.3, hazeCol: '#3a2418' })
    }
  }
  function auctioneer(c, x, t, o = {}) { return person(c, x, 940, 0.92, { cos: 'auctioneer', f: o.f || -1, pose: o.hammer ? { name: 'raise', k: o.hammer } : { name: 'raise', k: 1 }, face: { talk: o.talk ? t : 0, mood: 'calm' }, holdFn: o.hold }) }
  const priceTag = (c, v, x, y, size = 120) => { count(c, x, y, v, size); text(c, 'guilders', x, y + size * 0.72, size * 0.36, '#f3e7d0', { italic: true, shadow: 14 }) }

  // ---------- 0: Alkmaar, the auction
  SC[0] = (c, t, q, S) => {
    const sh = shotOf(t, [[0, 'room'], [q('on it is the name') - 0.3, 'paper'], [q('it is a bulb') - 0.3, 'garden'], [q('the bidding starts') - 0.3, 'bid'], [q('when the hammer') - 0.3, 'hammer'], [q('a good craftsman') - 0.3, 'craftsman'], [q('what nobody in that room') - 0.3, 'room2'], [q('in a town 20 miles') - 0.3, 'haarlem']])
    const paperFn = c => { paper(c, 0, -10, 120, 150, [['', 1], ['1 bulb', 22, '#3a2a1a']], { top: 60, rot: 0.05 }); tulip(c, 0, 10, 0.12, { col: '#f4f0ea', flame: '#a01e28' }) }
    if (sh.name === 'room' || sh.name === 'bid' || sh.name === 'room2') {
      const cam = sh.name === 'room' ? keys(t, [[0, { x: 1000, y: 700, z: 1.45 }], [sh.t1, { x: 1150, y: 700, z: 1.6 }]]) : sh.name === 'bid' ? keys(t, [[sh.t0, { x: 900, y: 700, z: 1.6 }], [sh.t1, { x: 1150, y: 700, z: 1.8 }]]) : keys(t, [[sh.t0, { x: 1000, y: 700, z: 1.6 }], [sh.t1, { x: 1000, y: 680, z: 1.4 }]])
      tavern(c, cam, t, { inner: c => {
        bidders(c, t, { bid: sh.name === 'bid', talk: sh.name !== 'room2' })
        auctioneer(c, 1500, t, { talk: true, hold: paperFn })
        table(c, 200, 990, 1400, t, { candle: true })
      } })
      post(c, cam, { rays: false, vignette: 0.65, grade: 'rgba(255,170,90,0.12)' })
      if (sh.name === 'room') label(c, 'Alkmaar, Holland  ·  February 5, 1637', W / 2, 110, prog(t, 0.5, 1.2) * (1 - prog(t, sh.t1 - 1, sh.t1 - 0.3)))
      if (sh.name === 'bid') { const v = Math.round(lerp(1000, 4800, prog(t, sh.t0 + 0.5, sh.t1, 'i')) / 50) * 50; priceTag(c, v, W / 2, 200, 130) }
    } else if (sh.name === 'paper') {
      c.fillStyle = vgrad(c, 0, H, '#3a2618', '#1a100a'); c.fillRect(0, 0, W, H)
      const z = keys(t, [[sh.t0, 1], [sh.t1, 1.06]]); c.save(); c.translate(W / 2, H / 2); c.scale(z, z); c.translate(-W / 2, -H / 2)
      paper(c, 960, 520, 620, 760, [['Lot', 40, '#5a4030', { italic: true }], ['One tulip bulb', 56], ['', 220], ['in the ground,', 36, '#5a4030', { italic: true }], ['outside the town', 36, '#5a4030', { italic: true }]], { rot: -0.02, top: 90 })
      tulip(c, 960, 690, 0.95, { col: '#f4f0ea', flame: '#a01e28', open: 0.5 })
      c.restore(); post(c, { x: 960 }, { rays: false, vignette: 0.6 })
    } else if (sh.name === 'garden') {
      // a winter garden outside town, and below it, in the earth, the bulb
      const cam = keys(t, [[sh.t0, { x: 960, y: 520, z: 1.0 }], [sh.t1, { x: 960, y: 700, z: 1.3 }]])
      polder(c, cam, t, { top: '#9aa8b8', bot: '#e0dcd4', clouds: 5, sun: [1500, 200, 400, '240,240,230'] })
      layer(c, cam, 1, c => {
        c.fillStyle = vgrad(c, 760, 1100, '#5a4a38', '#2a2018'); c.fillRect(-900, 770, 3800, 800)
        c.fillStyle = '#e8e8ec'; poly(c, [[-900, 780], [2900, 770], [2900, 800], [-900, 806]]); c.fill()
        c.strokeStyle = '#4a3a2a'; c.lineWidth = 8; for (let x = 200; x < 1800; x += 90) { c.beginPath(); c.moveTo(x, 790); c.lineTo(x, 700); c.stroke() } c.beginPath(); c.moveTo(150, 720); c.lineTo(1850, 720); c.stroke()
        c.strokeStyle = 'rgba(200,180,150,0.15)'; for (let k = 0; k < 8; k++) { c.beginPath(); c.moveTo(-900, 840 + k * 40); c.lineTo(2900, 840 + k * 40); c.stroke() }
        bulb(c, 960, 960, 0.75)
      })
      post(c, cam, { rays: 0.08, vignette: 0.6 })
    } else if (sh.name === 'hammer') {
      const cam = keys(t, [[sh.t0, { x: 1400, y: 680, z: 2.0 }], [sh.t1, { x: 1400, y: 680, z: 2.15 }]])
      const hit = q('comes down') + 0.25
      const [sx, sy] = shake(t, [hit], 10); cam.sx = sx; cam.sy = sy
      tavern(c, cam, t, { inner: c => { bidders(c, t, {}); auctioneer(c, 1500, t, { hammer: t < hit ? lerp(1, 0.2, prog(t, hit - 0.35, hit)) : 0.2, hold: c => { c.fillStyle = '#4a2a14'; c.fillRect(-8, -50, 16, 60); c.fillRect(-26, -64, 52, 26) } }); table(c, 200, 990, 1400, t, { candle: true }) } })
      post(c, cam, { rays: false, vignette: 0.65, grade: 'rgba(255,170,90,0.12)' })
      if (t > hit) priceTag(c, 'over 5,000', W / 2, 220, 120)
    } else if (sh.name === 'craftsman') {
      const cam = keys(t, [[sh.t0, { x: 900, y: 720, z: 1.8 }], [sh.t1, { x: 920, y: 720, z: 1.9 }]])
      tavern(c, cam, t, { fire: false, winX: 1300, inner: c => {
        c.fillStyle = hgrad(c, 700, 1400, '#7a5636', '#5a3a22'); c.fillRect(700, 820, 700, 30); c.fillRect(730, 850, 24, 120); c.fillRect(1350, 850, 24, 120)
        for (let k = 0; k < 4; k++) { c.fillStyle = '#8a6a4a'; c.fillRect(800 + k * 120, 790, 80, 30) }
        person(c, 620, 970, 0.72, { cos: 'weaver', pose: { name: 'stand' }, face: { look: -0.2 } })
      } })
      post(c, cam, { rays: false, vignette: 0.6 })
      priceTag(c, 300, W / 2, 210, 120); text(c, 'a year, for a good craftsman', W / 2, 330, 40, '#f3e7d0', { italic: true, shadow: 14, alpha: prog(t, sh.t0 + 0.4, sh.t0 + 1) })
    } else {
      // two days earlier, twenty miles away: a room in Haarlem, nearly empty
      const cam = keys(t, [[sh.t0, { x: 960, y: 700, z: 1.4 }], [sh.t1, { x: 1000, y: 700, z: 1.65 }]])
      tavern(c, cam, t, { night: true, fire: false, inner: c => { person(c, 1300, 940, 0.9, { cos: 'dutchman3', f: -1, pose: { name: 'raise', k: 0.9 }, face: { mood: 'sad' }, holdFn: c => paper(c, 0, -10, 90, 110, [], { rot: 0.05 }) }); person(c, 640, 940, 0.88, { cos: 'dutchman', f: 1, pose: { name: 'stand' }, face: { mood: 'stern' } }); table(c, 300, 980, 1300, t, { candle: true, n: 2, pipes: 0 }) } })
      post(c, cam, { rays: false, night: 0.35, vignette: 0.75 })
      label(c, 'Haarlem, two days before', W / 2, 110, prog(t, sh.t0 + 0.3, sh.t0 + 1))
    }
  }

  // ---------- 1: the richest place on earth
  SC[1] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'harbor'], [q('amsterdam had') - 0.3, 'bourse'], [q('its merchants were') - 0.3, 'canal'], [q('and for the first time') - 0.3, 'people']])
    if (sh.name === 'harbor') {
      const cam = keys(t, [[sh.t0, { x: 800, y: 560, z: 1.05 }], [sh.t1, { x: 1150, y: 560, z: 1.12 }]], 'l')
      layer(c, cam, 0.06, c => sky(c, '#86a2c2', '#efe6d4', { horizon: 700, clouds: 8, sun: [1400, 200, 520] }))
      layer(c, cam, 0.35, c => { street(c, -900, 2900, 640, { h: 120, fade: 0.45, hazeCol: '#c8ccd0', seed: 9 }) })
      layer(c, cam, 0.7, c => { c.fillStyle = vgrad(c, 640, 1100, '#6a8090', '#2a3a46'); c.fillRect(-1400, 640, 4800, 700); for (const [x, s] of [[100, 0.5], [700, 0.62], [1300, 0.55], [1900, 0.6]]) ship(c, x, 760, s, t) })
      layer(c, cam, 1, c => { for (const [x, s] of [[400, 0.9], [1500, 1.0]]) ship(c, x, 900, s, t, { f: x > 1000 ? -1 : 1 }); c.fillStyle = 'rgba(240,248,255,0.25)'; for (let k = 0; k < 40; k++) c.fillRect(((k * 137 - t * 30) % 3200) - 700, 930 + (k % 7) * 20, 60, 3) })
      post(c, cam, { rays: 0.12 })
      const lab = (s, at) => { const a = prog(t, q(at), q(at) + 0.4) * (1 - prog(t, q(at) + 2.2, q(at) + 2.6)); text(c, s, W / 2, 140, 52, '#f3e7d0', { italic: true, alpha: a, shadow: 18 }) }
      lab('spice from the East Indies', 'spice from the east'); lab('grain from the Baltic', 'grain from the baltic'); lab('furs from the New World', 'and furs')
    } else if (sh.name === 'bourse') {
      // the exchange: a courtyard with arcades, merchants in black
      const cam = keys(t, [[sh.t0, { x: 960, y: 600, z: 1.15 }], [sh.t1, { x: 980, y: 620, z: 1.3 }]])
      layer(c, cam, 0.06, c => sky(c, '#86a2c2', '#efe6d4', { horizon: 600, clouds: 3 }))
      layer(c, cam, 0.8, c => {
        c.fillStyle = hgrad(c, -400, 2400, '#9a7a5a', '#b8987a', '#8a6a4a'); c.fillRect(-600, 260, 3200, 700)
        for (let x = -500; x < 2500; x += 180) { c.fillStyle = '#3a2a1e'; c.beginPath(); c.moveTo(x, 900); c.lineTo(x, 560); c.arc(x + 70, 560, 70, Math.PI, 0); c.lineTo(x + 140, 900); c.fill(); c.fillStyle = '#d8c8a8'; c.fillRect(x + 140, 480, 40, 420) }
        c.fillStyle = '#7a5a3a'; c.fillRect(-600, 380, 3200, 40); for (let x = -500; x < 2500; x += 90) { c.fillStyle = '#f2eadc'; c.fillRect(x, 290, 50, 70) }
        c.fillStyle = '#5a4a3a'; c.fillRect(850, 60, 220, 220); poly(c, [[830, 60], [960, -60], [1090, 60]], '#3a2a1e')
      })
      layer(c, cam, 1, c => { c.fillStyle = vgrad(c, 900, 1200, '#a89a84', '#6a5e4e'); c.fillRect(-900, 900, 3800, 500); const r = rng(14), men = []; for (let k = 0; k < 20; k++) men.push({ x: 100 + r() * 1700, z: r() - 0.5, cos: ['dutchman', 'dutchman2', 'dutchman3'][k % 3], f: r() > 0.5 ? 1 : -1, pose: k % 4 === 0 ? { name: 'point' } : { name: 'stand' }, face: { talk: t + k } }); crowd(c, 940, men, { s: 0.5, zy: 60, fade: 0.25, haze: '#c8b8a0' }) })
      post(c, cam, { rays: 0.1 })
      label(c, 'The Amsterdam exchange', W / 2, 110, prog(t, sh.t0 + 0.4, sh.t0 + 1) * (1 - prog(t, sh.t1 - 0.8, sh.t1 - 0.2)))
    } else if (sh.name === 'canal') {
      const cam = keys(t, [[sh.t0, { x: 700, y: 560, z: 1.1 }], [sh.t1, { x: 1200, y: 560, z: 1.18 }]], 'l')
      layer(c, cam, 0.06, c => sky(c, '#86a2c2', '#efe6d4', { horizon: 600, clouds: 6, sun: [1500, 150, 500] }))
      layer(c, cam, 0.85, c => { street(c, -900, 3000, 720, { h: 300, seed: 4 }); for (let x = -800; x < 2900; x += 260) tree(c, x, 760, 200, 'oak', { seed: x % 3, t }) })
      layer(c, cam, 1, c => { canal(c, 760, 400, t); c.fillStyle = 'rgba(0,0,0,0.12)'; c.fillRect(-900, 760, 3800, 40) })
      post(c, cam, { rays: 0.12 })
    } else {
      // ordinary people with a little money: each steps up as they're named
      const cam = keys(t, [[sh.t0, { x: 960, y: 640, z: 1.3 }], [sh.t1, { x: 960, y: 640, z: 1.38 }]])
      layer(c, cam, 0.06, c => sky(c, '#86a2c2', '#efe6d4', { horizon: 600, clouds: 6 }))
      layer(c, cam, 0.8, c => street(c, -900, 3000, 760, { h: 320, seed: 6 }))
      layer(c, cam, 1, c => {
        c.fillStyle = vgrad(c, 780, 1200, '#8a7a66', '#4a4034'); c.fillRect(-900, 780, 3800, 600)
        c.strokeStyle = 'rgba(0,0,0,0.15)'; for (let x = -900; x < 2900; x += 40) { c.beginPath(); c.moveTo(x, 780); c.lineTo(x - 80, 1200); c.stroke() }
        const P = [['weaver', 'weavers'], ['baker', 'bakers'], ['dutchman2', 'innkeepers'], ['dutchman3', 'glassmakers']]
        P.forEach(([cos, w], i) => { const a = prog(t, q(w) - 0.2, q(w) + 0.3); if (a > 0) person(c, 500 + i * 300, 1000 + (1 - a) * 20, 0.95, { cos, pose: { name: 'stand' }, alpha: a, face: { mood: 'happy' } }) })
        if (t > q('people who wanted')) person(c, 1660, 1000, 0.95, { cos: 'dutchwoman', f: -1, pose: { name: 'stand' }, face: { mood: 'happy' }, alpha: prog(t, q('people who wanted'), q('people who wanted') + 0.4) })
      })
      post(c, cam, { rays: 0.12 })
      const nm = [['Weavers', 'weavers'], ['Bakers', 'bakers'], ['Innkeepers', 'innkeepers'], ['Glassmakers', 'glassmakers']]
      nm.forEach(([s, w], i) => text(c, s, (500 + i * 300 - 960) * 1.38 + 960, 380, 44, '#f3e7d0', { italic: true, shadow: 14, alpha: prog(t, q(w), q(w) + 0.3) }))
    }
  }

  // ---------- 2: where tulips came from; Clusius; the thieves
  SC[2] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'wild'], [q('and the ottoman') - 0.3, 'palace'], [q('even the name') - 0.3, 'turban'], [q('in 1593') - 0.3, 'leiden'], [q('so people climbed') - 0.3, 'thieves'], [q('within a few years') - 0.3, 'fields']])
    if (sh.name === 'wild') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 620, z: 1.1 }], [sh.t1, { x: 1000, y: 680, z: 1.4 }]])
      layer(c, cam, 0.06, c => sky(c, '#8aa0c0', '#f0e2c8', { horizon: 700, clouds: 3, sun: [1500, 180, 500] }))
      layer(c, cam, 0.12, c => PK.snowPeaks(c, 520, { h: 200, seed: 7 }))
      layer(c, cam, 0.4, c => PK.ridge(c, 12, 680, 90, 120, '#9a8a6a', '#7a6a4a'))
      layer(c, cam, 1, c => { c.fillStyle = vgrad(c, 800, 1200, '#a89a6a', '#6a5a3a'); c.fillRect(-900, 820, 3800, 600); const r = rng(21); for (let k = 0; k < 40; k++) { const x = -200 + r() * 2400, y = 860 + r() * 220; tulip(c, x, y, 0.35 + (y - 860) / 900, { col: ['#d8342a', '#e8702a', '#f2c23a'][k % 3], sway: Math.sin(t + k) * 0.1, open: 0.8 }) } })
      post(c, cam, { rays: 0.14 })
      label(c, 'The mountains of Central Asia', W / 2, 110, prog(t, sh.t0 + 0.4, sh.t0 + 1) * (1 - prog(t, sh.t1 - 0.8, sh.t1 - 0.2)))
    } else if (sh.name === 'palace') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 580, z: 1.1 }], [sh.t1, { x: 1000, y: 600, z: 1.25 }]])
      layer(c, cam, 0.06, c => sky(c, '#7a9ac0', '#f2dcc0', { horizon: 700, clouds: 2, sun: [400, 300, 600, '255,210,160'] }))
      layer(c, cam, 0.6, c => {
        c.fillStyle = hgrad(c, 300, 1600, '#e8dcc8', '#c8b8a0'); c.fillRect(300, 420, 1300, 360)
        ell(c, 950, 420, 300, 230, 0, '#b8c0c8'); c.fillStyle = '#c8b8a0'; c.fillRect(640, 420, 620, 60)
        for (const [x, d] of [[500, 160], [1400, 160]]) { ell(c, x, 420, d * 0.6, d * 0.5, 0, '#b8c0c8') }
        for (const x of [200, 1700]) { c.fillStyle = '#e8dcc8'; c.fillRect(x - 22, 120, 44, 660); poly(c, [[x - 26, 120], [x, 30], [x + 26, 120]], '#8a9aa8'); c.fillRect(x - 34, 300, 68, 14) }
        for (let x = 380; x < 1560; x += 110) { c.fillStyle = '#4a3a3a'; c.beginPath(); c.moveTo(x, 780); c.lineTo(x, 640); c.arc(x + 35, 640, 35, Math.PI, 0); c.lineTo(x + 70, 780); c.fill() }
      })
      layer(c, cam, 1, c => {
        c.fillStyle = vgrad(c, 800, 1200, '#6a8a4a', '#3a5a2a'); c.fillRect(-900, 800, 3800, 600)
        for (let row = 0; row < 5; row++) for (let x = -300; x < 2300; x += 60) tulip(c, x + (row % 2) * 30, 830 + row * 50, 0.24 + row * 0.07, { col: ['#c8302a', '#e8702a', '#f2c23a', '#c8306a'][(row + (x / 60 | 0)) % 4], sway: Math.sin(t + x) * 0.06 })
        person(c, 980, 1010, 0.7, { cos: 'sultan', pose: { name: 'stand' }, face: { mood: 'happy', look: -0.3 } })
      })
      post(c, cam, { rays: 0.16, rayX: 200 })
      label(c, 'An Ottoman palace garden', W / 2, 110, prog(t, sh.t0 + 0.4, sh.t0 + 1) * (1 - prog(t, sh.t1 - 0.8, sh.t1 - 0.2)))
    } else if (sh.name === 'turban') {
      c.fillStyle = vgrad(c, 0, H, '#3a2a22', '#1a120e'); c.fillRect(0, 0, W, H)
      const k = prog(t, sh.t0 + 0.5, sh.t0 + 1.5)
      c.save(); c.translate(620, 620); c.scale(2.6, 2.6); c.fillStyle = vgrad(c, -60, 30, '#fbf6ec', '#d8ccb8'); ell(c, 0, -10, 70, 46, 0); c.fill(); c.strokeStyle = '#b8ac98'; c.lineWidth = 3; for (let j = 0; j < 4; j++) { c.beginPath(); c.ellipse(0, -10 + j * 8 - 12, 64, 26, -0.3 + j * 0.15, Math.PI * 1.05, Math.PI * 1.95); c.stroke() } ell(c, 0, -52, 20, 16, 0, '#c8302a'); c.restore()
      tulip(c, 1300, 900, 2.0, { col: '#c8302a', open: 0.35 })
      post(c, { x: 960 }, { rays: false, vignette: 0.6 })
      text(c, 'tülbend', 620, 860, 50, '#f3e7d0', { italic: true, shadow: 14, alpha: k }); text(c, 'turban', 620, 920, 34, '#f3e7d0', { italic: true, alpha: k })
    } else if (sh.name === 'leiden') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 620, z: 1.25 }], [sh.t1, { x: 1000, y: 640, z: 1.4 }]])
      polder(c, cam, t, { mill: false })
      layer(c, cam, 0.8, c => { street(c, -900, 3000, 720, { h: 260, seed: 12 }) })
      layer(c, cam, 1, c => {
        c.fillStyle = vgrad(c, 760, 1200, '#5a6a3a', '#3a4a26'); c.fillRect(-900, 760, 3800, 600)
        for (let row = 0; row < 3; row++) for (let x = 300; x < 1700; x += 70) tulip(c, x + row * 20, 820 + row * 70, 0.3 + row * 0.08, { col: ['#c8302a', '#f2c23a', '#f4f0ea'][(row + (x / 70 | 0)) % 3], sway: Math.sin(t + x) * 0.06 })
        person(c, 760, 1000, 0.72, { cos: 'clusius', pose: { name: 'stand' }, face: { look: -0.3 } })
      })
      post(c, cam, { rays: 0.12 })
      label(c, 'Leiden, 1593', W / 2, 110, prog(t, q('in 1593'), q('in 1593') + 0.6) * (1 - prog(t, sh.t1 - 0.8, sh.t1 - 0.2)))
      if (t > q('carolus clusius')) text(c, 'Carolus Clusius', 760 - (cam.x - 960) * 1.4, 300, 40, '#f3e7d0', { italic: true, shadow: 14, alpha: prog(t, q('carolus clusius'), q('carolus clusius') + 0.5) })
    } else if (sh.name === 'thieves') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 600, z: 1.35 }], [sh.t1, { x: 980, y: 600, z: 1.45 }]])
      layer(c, cam, 0.06, c => sky(c, '#0c1222', '#24324a', { horizon: 700, moon: [1500, 200], stars: true, clouds: 0 }))
      layer(c, cam, 0.7, c => street(c, -900, 3000, 620, { h: 220, seed: 13, lit: true }))
      layer(c, cam, 1, c => {
        c.fillStyle = vgrad(c, 380, 900, '#5a4a40', '#3a2e28'); c.fillRect(-900, 420, 3800, 480); c.strokeStyle = 'rgba(0,0,0,0.3)'; c.lineWidth = 2; for (let y = 420; y < 900; y += 26) { c.beginPath(); c.moveTo(-900, y); c.lineTo(2900, y); c.stroke() }
        c.fillStyle = '#2a201a'; c.fillRect(-900, 400, 3800, 24)
        c.fillStyle = vgrad(c, 900, 1200, '#2a2a20', '#14140e'); c.fillRect(-900, 900, 3800, 400)
        const u = prog(t, sh.t0, sh.t1)
        person(c, 860, lerp(900, 420, clamp(u * 1.6)), 0.66, { cos: 'sailor17', pose: { name: 'cheer', k: 0.8, t }, fade: 0.4, hazeCol: '#1a2234' })
        person(c, 1100, 420, 0.66, { cos: 'dutchman3', pose: u > 0.5 ? { name: 'walk', d: u * 200 } : { name: 'crouch' }, fade: 0.4, hazeCol: '#1a2234', holdFn: null })
        if (u > 0.4) bulb(c, 1180, 300, 0.2)
      })
      post(c, cam, { night: 0.25, vignette: 0.8 })
    } else {
      const cam = keys(t, [[sh.t0, { x: 960, y: 600, z: 1.05 }], [sh.t1, { x: 1000, y: 620, z: 1.2 }]])
      fields(c, cam, t, {})
      post(c, cam, { rays: 0.14 })
    }
  }

  // ---------- 3: broken tulips, the virus, Semper Augustus
  SC[3] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'plain'], [q('but every so often') - 0.3, 'broken'], [q('nobody knew it then') - 0.3, 'virus'], [q('so the most beautiful') - 0.3, 'rare'], [q('the most famous') - 0.3, 'semper'], [q('in 1623') - 0.3, 'offer']])
    const dark = c => { c.fillStyle = rgrad(c, W / 2, H / 2, 50, 1100, '#3a3028', '#120e0a'); c.fillRect(0, 0, W, H) }
    if (sh.name === 'plain') {
      dark(c)
      ;[['#d8342a', 'red'], ['#f2c23a', 'yellow'], ['#f4f0ea', 'white']].forEach(([col, w], i) => { const a = prog(t, q(w) - 0.2, q(w) + 0.3); if (a > 0) { c.save(); c.globalAlpha = a; tulip(c, 560 + i * 400, 960, 2.2, { col, sway: Math.sin(t + i) * 0.05, open: 0.5 }); c.restore() } })
      post(c, { x: 960 }, { rays: false, vignette: 0.55 })
    } else if (sh.name === 'broken' || sh.name === 'semper') {
      dark(c)
      const z = keys(t, [[sh.t0, 1], [sh.t1, 1.12]]); c.save(); c.translate(W / 2, H / 2); c.scale(z, z); c.translate(-W / 2, -H / 2)
      if (sh.name === 'broken') { tulip(c, 760, 1080, 2.5, { col: '#f2c23a', flame: '#a8281e', open: 0.55, sway: Math.sin(t) * 0.03 }); tulip(c, 1250, 1100, 2.1, { col: '#f4f0ea', flame: '#6a2a8a', open: 0.5, sway: Math.sin(t + 1) * 0.03 }) }
      else { tulip(c, 960, 1100, 2.7, { col: '#f8f4ee', flame: '#9a1420', open: 0.5, sway: Math.sin(t) * 0.03 }) }
      c.restore()
      post(c, { x: 960 }, { rays: false, vignette: 0.55 })
      if (sh.name === 'broken') text(c, 'broken tulips', W / 2, 150, 60, '#f3e7d0', { italic: true, shadow: 18, alpha: prog(t, q('broken tulips'), q('broken tulips') + 0.4) })
      else text(c, 'Semper Augustus', W / 2, 150, 70, '#f3e7d0', { italic: true, weight: 700, shadow: 18, alpha: prog(t, q('semper augustus'), q('semper augustus') + 0.5) })
    } else if (sh.name === 'virus') {
      // macro: a leaf, and tiny aphids walking on it
      c.fillStyle = vgrad(c, 0, H, '#2a3a22', '#101a0c'); c.fillRect(0, 0, W, H)
      const z = keys(t, [[sh.t0, 1], [sh.t1, 1.1]]); c.save(); c.translate(W / 2, H / 2); c.scale(z, z); c.translate(-W / 2, -H / 2)
      c.fillStyle = vgrad(c, 200, 900, '#6aa04a', '#2f5a2a'); c.beginPath(); c.moveTo(-100, 1000); c.quadraticCurveTo(700, 200, 2000, 100); c.quadraticCurveTo(900, 600, -100, 1100); c.fill()
      c.strokeStyle = 'rgba(200,240,170,0.35)'; c.lineWidth = 6; c.beginPath(); c.moveTo(-100, 1050); c.quadraticCurveTo(800, 420, 2000, 110); c.stroke()
      const r = rng(4); for (let k = 0; k < 9; k++) { const u = (r() + (t - sh.t0) * 0.02) % 1, x = lerp(200, 1700, u), y = lerp(870, 330, u) + (r() - 0.5) * 80; c.save(); c.translate(x, y); c.rotate(-0.35); ell(c, 0, 0, 22, 14, 0, '#9ac86a'); ell(c, 18, 0, 8, 7, 0, '#7aa84a'); c.strokeStyle = '#5a7a3a'; c.lineWidth = 2; for (let j = -1; j <= 1; j++) { const st = Math.sin(t * 14 + k + j) * 4; c.beginPath(); c.moveTo(j * 8, 8); c.lineTo(j * 8 + st, 20); c.moveTo(j * 8, -8); c.lineTo(j * 8 - st, -20); c.stroke() } c.restore() }
      c.restore(); post(c, { x: 960 }, { rays: false, vignette: 0.6 })
      text(c, 'a virus, carried by aphids', W / 2, 150, 54, '#f3e7d0', { italic: true, shadow: 18, alpha: prog(t, q('a virus'), q('a virus') + 0.4) })
    } else if (sh.name === 'rare') {
      dark(c)
      for (let k = 0; k < 7; k++) { const plain = k !== 3; bulb(c, 360 + k * 200, 700, plain ? 0.75 : 0.42) }
      tulip(c, 360 + 3 * 200, 600, 0.9, { col: '#f8f4ee', flame: '#9a1420' })
      post(c, { x: 960 }, { rays: false, vignette: 0.55 })
    } else {
      // 1623: an offer of 12,000 guilders for ten, refused
      const cam = keys(t, [[sh.t0, { x: 960, y: 700, z: 1.8 }], [sh.t1, { x: 960, y: 700, z: 1.95 }]])
      tavern(c, cam, t, { fire: true, fireX: 200, inner: c => {
        person(c, 760, 930, 0.75, { cos: 'dutchman2', pose: { name: 'hold', at: [60, -190] }, holdFn: c => { ell(c, 0, 0, 34, 28, 0, '#8a6a3a'); c.fillStyle = '#e8c860'; for (let k = 0; k < 5; k++) ell(c, -18 + k * 9, -24, 8, 4, 0, '#e8c860') }, face: { talk: t, mood: 'happy' } })
        person(c, 1180, 930, 0.75, { cos: 'dutchman', f: -1, pose: { name: 'stand' }, face: { mood: 'stern', tilt: Math.sin(t * 6) * 0.08 * prog(t, q('the owner said no'), q('the owner said no') + 0.2) } })
      } })
      post(c, cam, { rays: false, vignette: 0.65, grade: 'rgba(255,170,90,0.12)' })
      label(c, '1623', W / 2, 110, prog(t, sh.t0 + 0.2, sh.t0 + 0.8))
      priceTag(c, '12,000', W / 2, 240, 110); text(c, 'for ten bulbs', W / 2, 370, 40, '#f3e7d0', { italic: true, shadow: 14 })
    }
  }

  // ---------- 4: the wind trade
  SC[4] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'bloom'], [q('the rest of the year') - 0.3, 'ground'], [q('so by the winter') - 0.3, 'note'], [q('the deals were made') - 0.3, 'tavern'], [q('the buyer often') - 0.3, 'empty'], [q('the dutch had a name') - 0.3, 'wind']])
    if (sh.name === 'bloom') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 640, z: 1.3 }], [sh.t1, { x: 980, y: 660, z: 1.4 }]])
      polder(c, cam, t, {})
      layer(c, cam, 1, c => { c.fillStyle = vgrad(c, 760, 1200, '#5a4a32', '#3a2e20'); c.fillRect(-900, 760, 3800, 600); const g = prog(t, sh.t0, sh.t0 + 2.2) * (1 - prog(t, sh.t1 - 1.2, sh.t1)); for (let row = 0; row < 4; row++) for (let x = 200; x < 1800; x += 80) tulip(c, x + row * 30, 820 + row * 70, (0.3 + row * 0.08) * Math.max(0.05, g), { col: '#d8342a', open: g }) })
      post(c, cam, { rays: 0.12 })
      text(c, 'about a week', W / 2, 170, 56, '#f3e7d0', { italic: true, shadow: 16, alpha: prog(t, q('about a week'), q('about a week') + 0.4) })
    } else if (sh.name === 'ground') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 520, z: 1.0 }], [sh.t1, { x: 960, y: 700, z: 1.35 }]])
      polder(c, cam, t, { top: '#9aa8b8', bot: '#e0dcd4' })
      layer(c, cam, 1, c => { c.fillStyle = vgrad(c, 760, 1200, '#5a4a38', '#2a2018'); c.fillRect(-900, 770, 3800, 800); c.strokeStyle = 'rgba(200,180,150,0.15)'; for (let k = 0; k < 8; k++) { c.beginPath(); c.moveTo(-900, 840 + k * 40); c.lineTo(2900, 840 + k * 40); c.stroke() } for (let k = 0; k < 5; k++) bulb(c, 560 + k * 200, 960, 0.4) })
      post(c, cam, { rays: 0.08 })
    } else if (sh.name === 'note') {
      c.fillStyle = vgrad(c, 0, H, '#3a2618', '#1a100a'); c.fillRect(0, 0, W, H)
      const k = prog(t, q('a slip of paper'), q('when it comes out') + 0.6)
      paper(c, 960, 520, 1200, 640, [['I will sell you this bulb,', 58, '#3a2a1a', { italic: true, alpha: prog(k, 0, 0.3) }], ['at this price,', 58, '#3a2a1a', { italic: true, alpha: prog(k, 0.3, 0.6) }], ['when it comes out of the ground.', 58, '#3a2a1a', { italic: true, alpha: prog(k, 0.6, 0.9) }], ['', 30], ['signed,', 32, '#5a4030', { italic: true, alpha: prog(k, 0.9, 1) }]], { rot: -0.015, top: 130 })
      post(c, { x: 960 }, { rays: false, vignette: 0.6 })
      text(c, 'trading promises', W / 2, 120, 56, '#f3e7d0', { italic: true, shadow: 16, alpha: prog(t, q('they were trading promises'), q('they were trading promises') + 0.4) * (1 - prog(t, q('a slip of paper') - 0.2, q('a slip of paper'))) })
    } else if (sh.name === 'tavern' || sh.name === 'empty') {
      const cam = sh.name === 'tavern' ? keys(t, [[sh.t0, { x: 900, y: 700, z: 1.5 }], [sh.t1, { x: 1100, y: 700, z: 1.65 }]]) : keys(t, [[sh.t0, { x: 960, y: 700, z: 1.75 }], [sh.t1, { x: 960, y: 700, z: 1.9 }]])
      tavern(c, cam, t, { night: true, inner: c => {
        if (sh.name === 'tavern') { bidders(c, t, { talk: true, n: 12, seed: 8 }); table(c, 200, 960, 1500, t, { candle: true, n: 9 }) }
        else { person(c, 780, 930, 0.78, { cos: 'weaver', pose: { name: 'stand', wide: 20 }, face: { mood: 'happy', talk: t } }); person(c, 1150, 930, 0.78, { cos: 'baker', f: -1, pose: { name: 'stand', wide: 20 }, face: { mood: 'happy' } }); table(c, 500, 1000, 900, t, { candle: true, n: 3 }) }
      } })
      post(c, cam, { rays: false, vignette: 0.65, grade: 'rgba(255,170,90,0.15)' })
      if (sh.name === 'tavern') text(c, 'colleges', W / 2, 150, 56, '#f3e7d0', { italic: true, shadow: 16, alpha: prog(t, q('groups called colleges'), q('groups called colleges') + 0.4) })
      if (sh.name === 'empty') { text(c, 'no money yet', 760 - (cam.x - 960) * 1.6, 230, 44, '#f3e7d0', { italic: true, shadow: 14, alpha: prog(t, q('had no money'), q('had no money') + 0.4) }); text(c, 'no bulb yet', 1160, 230, 44, '#f3e7d0', { italic: true, shadow: 14, alpha: prog(t, q('had no bulb'), q('had no bulb') + 0.4) }) }
    } else {
      // the wind trade: papers lift off a table and blow away
      const cam = { x: 960, y: 560, z: 1.0 }
      polder(c, cam, t, { clouds: 9 })
      layer(c, cam, 1, c => { c.fillStyle = vgrad(c, 760, 1200, '#6a7a4a', '#3a4a2a'); c.fillRect(-900, 760, 3800, 600); const r = rng(6); for (let k = 0; k < 16; k++) { const u = clamp((t - sh.t0) * 0.35 - k * 0.04), x = 400 + r() * 300 + u * 1800, y = 800 - u * 500 + Math.sin(t * 3 + k) * 40; paper(c, x, y, 80, 100, [], { rot: Math.sin(t * 2 + k) * 0.8 + u * 4 }) } })
      post(c, cam, { rays: 0.14 })
      text(c, 'the wind trade', W / 2, 200, 78, '#f3e7d0', { italic: true, weight: 700, shadow: 20, alpha: prog(t, q('the wind trade'), q('the wind trade') + 0.4) })
    }
  }

  // ---------- 5: prices only go up; the plague; the paper passed on
  SC[5] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'chart'], [q('that winter a plague') - 0.3, 'plague'], [q('some historians') - 0.3, 'bet'], [q('it was no longer') - 0.3, 'chain']])
    if (sh.name === 'chart') {
      c.fillStyle = vgrad(c, 0, H, '#3a2618', '#1a100a'); c.fillRect(0, 0, W, H)
      const pts = [0.05, 0.07, 0.09, 0.12, 0.17, 0.24, 0.34, 0.47, 0.62, 0.8, 0.96]
      chart(c, 960, 520, 1400, 760, pts, prog(t, sh.t0 + 0.4, sh.t1 - 0.4), { xlabels: [[0, 'Nov 1636'], [5, 'Dec'], [10, 'Jan 1637']], labels: [[5, 'bought'], [10, 'sold for twice as much']] })
      post(c, { x: 960 }, { rays: false, vignette: 0.6 })
      if (t > q('even the plainest')) text(c, 'plain bulbs: up more than ten times', W / 2, 120, 50, '#f3e7d0', { italic: true, shadow: 16, alpha: prog(t, q('even the plainest'), q('even the plainest') + 0.5) })
    } else if (sh.name === 'plague') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 600, z: 1.25 }], [sh.t1, { x: 1000, y: 610, z: 1.4 }]])
      layer(c, cam, 0.06, c => sky(c, '#3a3a48', '#8a7a6a', { horizon: 600, clouds: 0 }))
      layer(c, cam, 0.85, c => street(c, -900, 3000, 760, { h: 320, seed: 15, fade: 0.25, hazeCol: '#5a5048' }))
      layer(c, cam, 1, c => { c.fillStyle = vgrad(c, 760, 1200, '#5a5048', '#2a241e'); c.fillRect(-900, 760, 3800, 600); c.strokeStyle = '#e8e0d0'; c.lineWidth = 6; c.beginPath(); c.moveTo(1180, 520); c.lineTo(1240, 600); c.moveTo(1240, 520); c.lineTo(1180, 600); c.stroke(); person(c, 700 + (t - sh.t0) * 30, 930, 0.6, { cos: 'preacher', pose: { name: 'walk', d: (t - sh.t0) * 30 }, fade: 0.3, hazeCol: '#3a3430', face: { mood: 'sad' } }) })
      layer(c, cam, 1.3, c => fog(c, 960, 260, '180,170,160', 0.5))
      post(c, cam, { rays: false, vignette: 0.75, grade: 'rgba(60,60,80,0.3)' })
      label(c, 'Haarlem', W / 2, 110, prog(t, q('haarlem'), q('haarlem') + 0.5))
    } else if (sh.name === 'bet') {
      const cam = keys(t, [[sh.t0, { x: 900, y: 700, z: 1.6 }], [sh.t1, { x: 1100, y: 700, z: 1.8 }]])
      tavern(c, cam, t, { night: true, inner: c => { bidders(c, t, { bid: true, talk: true, seed: 11 }); table(c, 200, 960, 1500, t, { candle: true, n: 10 }) } })
      post(c, cam, { rays: false, vignette: 0.7, grade: 'rgba(255,150,80,0.16)' })
    } else {
      // a paper passed from hand to hand, each price a little higher
      const cam = keys(t, [[sh.t0, { x: 500, y: 720, z: 1.7 }], [sh.t1, { x: 1500, y: 720, z: 1.7 }]], 'l')
      tavern(c, cam, t, { night: true, fire: false, inner: c => {
        const n = 7; for (let k = 0; k < n; k++) person(c, 200 + k * 250, 960, 0.85, { cos: BUYERS[k % BUYERS.length], f: 1, pose: { name: 'hold', at: [70, -180] }, face: { mood: 'happy' } })
        const u = prog(t, sh.t0 + 0.4, sh.t1 - 0.5) * (n - 1), i = Math.floor(u), f = u - i, x = 200 + (i + f) * 250 + 60, y = 960 - 0.85 * 180 - Math.sin(Math.PI * f) * 60
        paper(c, x, y, 70, 90, [], { rot: 0.1 })
        text(c, Math.round(1000 * Math.pow(1.25, i + f)).toLocaleString('en-US'), x, y - 110, 40, '#f3e7d0', { weight: 800, shadow: 14 })
      } })
      post(c, cam, { rays: false, vignette: 0.7, grade: 'rgba(255,150,80,0.12)' })
    }
  }

  // ---------- 6: what one bulb was worth (each thing arrives as it's named)
  const GOODS = [['two loads of wheat', 'sacks'], ['four of rye', 'sacks2'], ['four fat oxen', 'ox'], ['eight fat pigs', 'pig'], ['twelve fat sheep', 'sheep'], ['two barrels of wine', 'wine'], ['four barrels of beer', 'beer'], ['two of butter', 'butter'], ['1000 pounds of cheese', 'cheese'], ['a bed', 'bed'], ['a suit of clothes', 'suit'], ['and a silver drinking', 'cup']]
  function good(c, kind, x, y, t) {
    if (kind === 'sacks' || kind === 'sacks2') for (let k = 0; k < 2; k++) { const col = kind === 'sacks' ? '#d8c08a' : '#b8a070'; ell(c, x + k * 70 - 35, y - 50, 40, 55, 0, col); c.fillStyle = shade(col, -0.2); c.fillRect(x + k * 70 - 50, y - 108, 30, 14) }
    else if (kind === 'ox') beast(c, x, y, 0.42, { kind: 'ox', t, pose: { name: 'stand' } })
    else if (kind === 'pig') { beast(c, x - 30, y, 0.4, { kind: 'pig', t }); beast(c, x + 40, y + 10, 0.4, { kind: 'pig', t, f: -1 }) }
    else if (kind === 'sheep') { beast(c, x - 30, y, 0.42, { kind: 'sheep', t }); beast(c, x + 40, y + 12, 0.42, { kind: 'sheep', t, f: -1 }) }
    else if (kind === 'wine' || kind === 'beer') for (let k = 0; k < 2; k++) { const bx = x + k * 70 - 35; c.fillStyle = hgrad(c, bx - 30, bx + 30, '#8a5a32', '#6a3c1e', '#4a2812'); ell(c, bx, y - 50, 32, 50, 0); c.fill(); c.strokeStyle = '#3a3a3a'; c.lineWidth = 4; for (const yy of [-80, -20]) { c.beginPath(); c.moveTo(bx - 30, y + yy); c.lineTo(bx + 30, y + yy); c.stroke() } if (kind === 'wine') ell(c, bx, y - 50, 7, 7, 0, '#6a1a22') }
    else if (kind === 'butter') { c.fillStyle = hgrad(c, x - 40, x + 40, '#d8d0c0', '#a89a88'); c.fillRect(x - 40, y - 70, 80, 70); ell(c, x, y - 70, 40, 10, 0, '#f2e090') }
    else if (kind === 'cheese') for (let k = 0; k < 3; k++) { const cy = y - 20 - k * 36; c.fillStyle = vgrad(c, cy - 18, cy + 18, '#f2c84a', '#c8962a'); ell(c, x, cy, 60, 18, 0); c.fill(); c.fillRect(x - 60, cy - 18, 120, 18); ell(c, x, cy - 18, 60, 16, 0, '#f6d870') }
    else if (kind === 'bed') { c.fillStyle = '#5a3a22'; c.fillRect(x - 90, y - 130, 14, 130); c.fillRect(x + 76, y - 90, 14, 90); c.fillStyle = '#e8e0d0'; c.fillRect(x - 80, y - 70, 160, 34); c.fillStyle = '#8a3a2a'; c.fillRect(x - 40, y - 76, 120, 30); c.fillStyle = '#5a3a22'; c.fillRect(x - 90, y - 36, 180, 12) }
    else if (kind === 'suit') { c.fillStyle = '#3a2a22'; poly(c, [[x - 40, y - 150], [x + 40, y - 150], [x + 55, y - 40], [x - 55, y - 40]]); c.fill(); c.fillStyle = '#f2eee4'; poly(c, [[x - 24, y - 150], [x + 24, y - 150], [x + 30, y - 130], [x - 30, y - 130]]); c.fill(); c.strokeStyle = '#3a2a1a'; c.lineWidth = 4; c.beginPath(); c.moveTo(x, y - 150); c.lineTo(x, y); c.stroke() }
    else if (kind === 'cup') { c.fillStyle = hgrad(c, x - 30, x + 30, '#f0f0f4', '#a8a8b0', '#6a6a72'); poly(c, [[x - 30, y - 110], [x + 30, y - 110], [x + 16, y - 50], [x - 16, y - 50]]); c.fill(); c.fillRect(x - 5, y - 50, 10, 34); ell(c, x, y - 14, 26, 8, 0, '#a8a8b0'); ell(c, x - 8, y - 96, 6, 12, 0, 'rgba(255,255,255,0.8)') }
  }
  SC[6] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'pamphlet'], [q('two loads of wheat') - 0.3, 'goods'], [q('all of that') - 0.3, 'bulb']])
    if (sh.name === 'pamphlet') {
      c.fillStyle = vgrad(c, 0, H, '#3a2618', '#1a100a'); c.fillRect(0, 0, W, H)
      paper(c, 960, 540, 700, 860, [['A list', 56, '#3a2a1a', { italic: true }], ['of what was given', 40, '#3a2a1a', { italic: true }], ['for one bulb', 40, '#3a2a1a', { italic: true }], ['', 40], ['wheat · rye · oxen', 32, '#5a4030'], ['pigs · sheep · wine', 32, '#5a4030'], ['beer · butter · cheese', 32, '#5a4030'], ['a bed · a suit · a cup', 32, '#5a4030']], { rot: 0.02, top: 110 })
      post(c, { x: 960 }, { rays: false, vignette: 0.6 }); return
    }
    const cam = sh.name === 'goods' ? { x: 960, y: 760, z: lerp(1.3, 1.2, prog(t, sh.t0, sh.t1)) } : keys(t, [[sh.t0, { x: 960, y: 760, z: 1.2 }], [sh.t1, { x: 960, y: 900, z: 2.0 }]])
    polder(c, cam, t, { clouds: 6 })
    layer(c, cam, 1, c => {
      c.fillStyle = vgrad(c, 760, 1200, '#7a7a4a', '#4a4a2a'); c.fillRect(-1400, 760, 4800, 800)
      GOODS.forEach(([w, kind], i) => { const a = prog(t, q(w) - 0.1, q(w) + 0.25); if (a <= 0) return; const col = i % 6, row = Math.floor(i / 6), x = 300 + col * 265 + (row ? 120 : 0), y = 830 + row * 120; c.save(); c.globalAlpha = a; c.translate(x, y + (1 - a) * -40); c.scale(1.25 + row * 0.15, 1.25 + row * 0.15); good(c, kind, 0, 0, t); c.restore() })
      // the one bulb, on its own little cushion, in front
      c.fillStyle = vgrad(c, 1050, 1110, '#8a2a2a', '#5a1a1a'); ell(c, 960, 1110, 110, 30, 0); c.fill(); bulb(c, 960, 1090, 0.62)
    })
    post(c, cam, { rays: 0.12 })
    const g = GOODS.find(([w]) => t >= q(w) - 0.1 && t < q(w) + 1.2)
    if (g && sh.name === 'goods') text(c, g[0][0].toUpperCase() + g[0].slice(1).replace('1000', '1,000').replace('and a silver drinking', 'a silver drinking cup'), W / 2, 140, 54, '#f3e7d0', { italic: true, shadow: 16 })
    if (sh.name === 'bulb') text(c, 'for one bulb', W / 2, 160, 64, '#f3e7d0', { italic: true, weight: 700, shadow: 18, alpha: prog(t, q('for one bulb'), q('for one bulb') + 0.4) })
  }
})()
