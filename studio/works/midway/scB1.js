// scB1.js: scenes 0-5 of the Battle of Midway, Style B.
(function () {
  const { W, H, clamp, lerp, prog, keys, rng, ell, poly, shade, vgrad, hgrad, rgrad, layer, fog, sky, post, person, crowd, paper, map, pathLine, count, text, label, shake, flashes } = PK
  const { ocean, carrier, destroyer, battleship, fire, blast, splash, flak, plane, planeTop, carrierTop, basement, hangar, torpedo, bomb, seaChart, shotOf } = MWB
  const SC = window.SCENES = window.SCENES || []
  const dark = c => { c.fillStyle = vgrad(c, 0, H, '#24282c', '#101214'); c.fillRect(0, 0, W, H) }
  const word = (c, s, y, a, size = 54) => text(c, s, W / 2, y, size, '#f3e7d0', { italic: true, shadow: 16, alpha: a })
  // the Japanese carrier force on the horizon: four carriers and escorts
  function fleet(c, t, o = {}) {
    const ships = [[300, 760, 0.42, 'left'], [820, 800, 0.5, 'right'], [1360, 770, 0.45, 'left'], [1820, 820, 0.52, 'right']]
    destroyer(c, 100, 720, 0.3, t); destroyer(c, 1600, 700, 0.28, t); battleship(c, 1100, 700, 0.3, t)
    ships.forEach(([x, y, s, isl], i) => carrier(c, x, y, s, t, { jp: true, island: isl, fire: o.fires ? o.fires[i] : 0 }))
  }
  // the bridge of the flagship: a window band onto the sea, the admiral with binoculars
  function bridge(c, cam, t, o = {}) {
    ocean(c, cam, t, { tod: 'day', inner: c => { carrier(c, 1500, 820, 0.4, t, { jp: true, island: 'left' }); carrier(c, 400, 860, 0.36, t, { jp: true }) } })
    layer(c, cam, 1.15, c => {
      c.fillStyle = vgrad(c, -400, 1400, '#3a3c40', '#24262a'); c.fillRect(-900, -400, 3800, 520); c.fillRect(-900, 760, 3800, 900)
      for (let x = -800; x < 2900; x += 420) c.fillRect(x, 100, 40, 680)
      c.fillStyle = '#4a4c50'; c.fillRect(-900, 740, 3800, 30)
      person(c, o.x ?? 760, 1040, 1.05, { cos: 'nagumo', pose: o.bino ? { name: 'hold', at: [56, -300] } : { name: 'stand' }, holdFn: o.bino ? c => { c.fillStyle = '#1a1a1a'; c.fillRect(-14, -12, 28, 24); c.fillRect(-4, -26, 30, 22) } : null, face: { mood: o.mood || 'calm', look: o.look ?? 0.05 } })
    })
  }

  // ---------- 0: 10:20 a.m., winning
  SC[0] = (c, t, q, S) => {
    const sh = shotOf(t, [[0, 'wide'], [q('it is twenty past') - 0.3, 'bridge'], [q('around him are') - 0.3, 'fleet'], [q('for three hours') - 0.3, 'attack'], [q('and not one bomb') - 0.3, 'miss'], [q('he is winning') - 0.3, 'winning'], [q('in about five') - 0.3, 'above']])
    if (sh.name === 'wide' || sh.name === 'fleet') {
      const cam = sh.name === 'wide' ? keys(t, [[0, { x: 1100, y: 640, z: 1.35 }], [sh.t1, { x: 960, y: 640, z: 1.15 }]]) : keys(t, [[sh.t0, { x: 700, y: 680, z: 1.2 }], [sh.t1, { x: 1200, y: 680, z: 1.3 }]], 'l')
      ocean(c, cam, t, { tod: 'day', inner: c => fleet(c, t) })
      post(c, cam, { rays: 0.12, rayX: 900 })
      if (sh.name === 'wide') label(c, 'The Pacific  ·  June 4, 1942', W / 2, 110, prog(t, 0.3, 1) * (1 - prog(t, sh.t1 - 0.8, sh.t1 - 0.2)))
      if (sh.name === 'fleet') word(c, 'the four carriers that bombed Pearl Harbor', 150, prog(t, q('the same four'), q('the same four') + 0.4), 46)
    } else if (sh.name === 'bridge' || sh.name === 'winning') {
      const cam = keys(t, [[sh.t0, { x: 900, y: 600, z: 1.0 }], [sh.t1, { x: 920, y: 600, z: 1.08 }]])
      bridge(c, cam, t, { bino: sh.name === 'bridge', mood: sh.name === 'winning' ? 'happy' : 'calm' })
      post(c, cam, { rays: 0.1, rayX: 900 })
      if (sh.name === 'bridge') label(c, '10:20 a.m.', W / 2, 110, prog(t, q('twenty past ten'), q('twenty past ten') + 0.5))
    } else if (sh.name === 'attack' || sh.name === 'miss') {
      // torpedo planes skim in low through the flak; splashes all around, nothing hits
      const cam = keys(t, [[sh.t0, { x: 900, y: 700, z: 1.4 }], [sh.t1, { x: 1100, y: 700, z: 1.5 }]])
      const u = t - sh.t0
      ocean(c, cam, t, { tod: 'day', inner: c => {
        carrier(c, 1400, 820, 0.62, t, { jp: true, island: 'left' })
        flak(c, t, 200, 300, 1600, 350, 18, 7)
        for (let k = 0; k < 4; k++) { const x = lerp(-300, 1300, ((u * 0.12 + k * 0.22) % 1)), down = sh.name === 'miss' && k % 2 === 0 ? prog(((u * 0.12 + k * 0.22) % 1), 0.6, 0.9) : 0; plane(c, x, 880 - k * 40 + down * 140, 0.75, t, { kind: 'tbd', load: down ? null : 'torpedo', smoke: down > 0, ang: down * 0.4 }); if (down > 0.9) splash(c, x + 30, 1000, 1, (down - 0.9) * 8) }
        for (let k = 0; k < 6; k++) splash(c, 400 + k * 230, 960 + (k % 3) * 20, 0.8, ((u * 0.5 + k * 0.17) % 1))
        for (let k = 0; k < 2; k++) plane(c, lerp(1800, -200, ((u * 0.15 + k * 0.5) % 1)), 620 + k * 50, 0.6, t, { kind: 'zero', f: -1 })
      } })
      post(c, cam, { rays: 0.1 })
      if (sh.name === 'attack') word(c, 'wave after wave', 150, prog(t, q('wave after'), q('wave after') + 0.4))
      else word(c, 'not one hit', 150, prog(t, q('has hit'), q('has hit') + 0.3))
    } else {
      // look up: far above the clouds, specks catching the sun
      const cam = keys(t, [[sh.t0, { x: 960, y: 700, z: 1.0 }], [sh.t1, { x: 960, y: 300, z: 1.25 }]])
      ocean(c, cam, t, { tod: 'day', horizon: 900, inner: c => carrier(c, 960, 1000, 0.5, t, { jp: true }) })
      layer(c, cam, 0.3, c => { for (let k = 0; k < 14; k++) { const x = 700 + (k % 7) * 70 + Math.floor(k / 7) * 30, y = 120 + Math.floor(k / 7) * 40 + Math.sin(t + k) * 2; ell(c, x, y, 5, 2, 0, '#2a2e34'); if ((Math.floor(t * 3) + k) % 5 === 0) ell(c, x, y - 2, 4, 4, 0, 'rgba(255,255,240,0.9)') } })
      post(c, cam, { rays: 0.14, rayX: 800 })
      word(c, 'about five minutes', 980, prog(t, q('five minutes'), q('five minutes') + 0.4), 50)
    }
  }

  // ---------- 1: Yamamoto's plan
  function pacific(c, t, o = {}) {
    seaChart(c, t, (c, w, h) => {
      const isl = (x, y, n, s = 34, a = 1) => { ell(c, x, y, 14, 9, 0.3, `rgba(110,90,60,${a})`); text(c, n, x, y - 34, s, `rgba(58,40,24,${a})`, { italic: true }) }
      text(c, 'PACIFIC OCEAN', 0, -330, 46, 'rgba(50,70,90,0.6)', { weight: 800 })
      c.fillStyle = 'rgba(110,90,60,0.6)'; poly(c, [[-720, -300], [-560, -360], [-520, -180], [-600, 0], [-700, 60]]); c.fill(); text(c, 'JAPAN', -620, -120, 34, 'rgba(58,40,24,0.9)', { weight: 800 })
      if (o.conquest) { c.fillStyle = `rgba(170,40,30,${0.25 * o.conquest})`; c.beginPath(); c.ellipse(-520, 160, 380 * o.conquest, 260 * o.conquest, 0.3, 0, Math.PI * 2); c.fill() }
      isl(420, 160, 'Hawaii', 34); isl(60, -40, 'Midway', 38, o.midway ?? 1)
      if (o.dist) { const a = o.dist; c.strokeStyle = `rgba(122,34,26,${a})`; c.lineWidth = 4; c.setLineDash([12, 10]); c.beginPath(); c.moveTo(60, -40); c.lineTo(420, 160); c.stroke(); c.setLineDash([]); text(c, '1,300 miles', 280, 40, 34, `rgba(122,34,26,${a})`, { weight: 800, rot: 0.5 }) }
      if (o.jp) { const e = pathLine(c, [[-560, -160], [-300, -120], [-60, -70], [20, -50]], o.jp, '#8a2a1e', 7); if (e) ell(c, e[0], e[1], 12, 12, 0, '#8a2a1e') }
      if (o.us) { const e = pathLine(c, [[420, 160], [300, 40], [150, -110], [90, -130]], o.us, '#2a4a7a', 7); if (e) ell(c, e[0], e[1], 12, 12, 0, '#2a4a7a') }
      if (o.trap) { const a = o.trap; c.strokeStyle = `rgba(170,40,30,${a})`; c.lineWidth = 5; c.beginPath(); c.arc(60, -40, 120, 0, Math.PI * 2); c.stroke() }
    })
  }
  SC[1] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'conquest'], [q('but the admiral') - 0.3, 'harbor'], [q('his name was') - 0.3, 'yamamoto'], [q('he would attack') - 0.3, 'plan']])
    if (sh.name === 'conquest') { pacific(c, t, { conquest: prog(t, sh.t0 + 0.3, sh.t1 - 0.5, 'o'), midway: 0.3 }); post(c, { x: 960 }, { rays: false, vignette: 0.5 }); word(c, 'six months of victories', 990, prog(t, sh.t0 + 0.5, sh.t0 + 1), 44) }
    else if (sh.name === 'harbor') {
      // Pearl Harbor after the attack: battleships burning, and the carriers' piers empty
      const cam = keys(t, [[sh.t0, { x: 960, y: 640, z: 1.15 }], [sh.t1, { x: 1200, y: 660, z: 1.35 }]])
      ocean(c, cam, t, { tod: 'morning', clouds: 4, water: '#5a7a8a', inner: c => {
        PK.ridge(c, 41, 660, 80, 120, '#5a7a4a', '#3a5a32')
        battleship(c, 500, 830, 0.5, t); fire(c, 500, 800, 300, t, 0.6); battleship(c, 950, 860, 0.5, t); fire(c, 950, 830, 260, t, 0.5)
        c.fillStyle = '#6a6458'; c.fillRect(1250, 820, 600, 30); c.fillRect(1250, 850, 20, 60)
        text(c, 'carriers: away', 1550, 780, 40, '#f3e7d0', { italic: true, shadow: 14, alpha: prog(t, q('had not been in port'), q('had not been in port') + 0.4) })
      } })
      post(c, cam, { rays: 0.08, grade: 'rgba(120,80,60,0.2)' })
      label(c, 'Pearl Harbor, December 1941', W / 2, 110, prog(t, sh.t0 + 0.3, sh.t0 + 0.9) * (1 - prog(t, sh.t1 - 0.8, sh.t1 - 0.2)))
    } else if (sh.name === 'yamamoto') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 620, z: 1.1 }], [sh.t1, { x: 960, y: 620, z: 1.2 }]])
      ocean(c, cam, t, { tod: 'day', inner: c => battleship(c, 1400, 760, 0.4, t) })
      layer(c, cam, 1.1, c => { c.fillStyle = vgrad(c, 920, 1200, '#6a6a68', '#3a3a38'); c.fillRect(-900, 920, 3800, 600); person(c, 860, 1060, 1.2, { cos: 'yamamoto', pose: { name: 'stand' }, face: { mood: 'stern', look: 0.05 } }) })
      post(c, cam, { rays: 0.12 })
      label(c, 'Admiral Isoroku Yamamoto', W / 2, 110, prog(t, q('yamamoto'), q('yamamoto') + 0.5))
    } else {
      pacific(c, t, { dist: prog(t, q('1300 miles'), q('1300 miles') + 0.5), jp: prog(t, q('the americans would'), q('and when they did') + 1, 'io') * 0.7, us: prog(t, q('the americans would'), q('come out') + 1.2, 'io'), trap: prog(t, q('his carriers would'), q('his carriers would') + 0.6) })
      post(c, { x: 960 }, { rays: false, vignette: 0.5 })
    }
  }

  // ---------- 2: the codebreakers
  SC[2] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'basement'], [q('they could read') - 0.3, 'af'], [q('rochefort was sure') - 0.3, 'sure'], [q('so they set a trap') - 0.3, 'trap'], [q('within a day') - 0.3, 'reply']])
    if (sh.name === 'basement') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 680, z: 1.3 }], [sh.t1, { x: 1060, y: 680, z: 1.5 }]])
      basement(c, cam, t, { inner: c => { for (let k = 0; k < 3; k++) { const x = 300 + k * 420; person(c, x + 60, 1040, 0.85, { cos: k === 1 ? 'rochefort' : 'codebreaker', pose: { name: 'sit', hands: 'table', write: k !== 1, t: t + k }, face: { look: -0.3 } }); c.fillStyle = hgrad(c, x, x + 360, '#6a5a3a', '#4a3a22'); c.fillRect(x, 900, 340, 26); c.fillRect(x + 10, 926, 18, 130); c.fillRect(x + 312, 926, 18, 130); for (let j = 0; j < 6; j++) { c.fillStyle = '#e8dcb8'; c.save(); c.translate(x + 160 + j * 24, 894); c.rotate((j - 3) * 0.1); c.fillRect(-14, -4, 28, 8); c.restore() } } } })
      post(c, cam, { rays: false, vignette: 0.6 })
      if (t > q('their boss')) label(c, 'Commander Joseph Rochefort', W / 2, 110, prog(t, q('joseph rochefort'), q('joseph rochefort') + 0.5))
      else label(c, 'Station Hypo, Pearl Harbor', W / 2, 110, prog(t, sh.t0 + 0.6, sh.t0 + 1.2))
    } else if (sh.name === 'af') {
      dark(c)
      paper(c, 960, 520, 1000, 640, [['… attack … target …', 44, '#3a3a3a', { font: 'OldStandard' }], ['', 40], ['AF', 220, '#8a2a1e', { weight: 800, font: 'OldStandard', alpha: prog(t, q('two letters'), q('two letters') + 0.4) }]], { top: 100, col: '#ece6d8' })
      post(c, { x: 960 }, { rays: false, vignette: 0.55 })
    } else if (sh.name === 'sure') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 680, z: 1.6 }], [sh.t1, { x: 980, y: 680, z: 1.7 }]])
      basement(c, cam, t, { inner: c => { c.fillStyle = '#e8dcb8'; c.fillRect(1100, 400, 520, 360); c.strokeStyle = 'rgba(70,90,110,0.4)'; for (let k = 0; k < 6; k++) { c.beginPath(); c.moveTo(1100 + k * 90, 400); c.lineTo(1100 + k * 90, 760); c.stroke() } ell(c, 1300, 560, 14, 9, 0, '#6a5a3a'); text(c, 'Midway', 1300, 520, 30, '#3a2a1a', { italic: true }); c.strokeStyle = '#8a2a1e'; c.lineWidth = 4; c.beginPath(); c.arc(1300, 560, 50, 0, Math.PI * 2); c.stroke(); person(c, 900, 1060, 0.95, { cos: 'rochefort', pose: { name: 'point' }, target: [1300, 560], face: { mood: 'stern', talk: t } }) } })
      post(c, cam, { rays: false, vignette: 0.6 })
      word(c, 'Washington was not sure', 150, prog(t, q('washington was not'), q('washington was not') + 0.4))
    } else if (sh.name === 'trap') {
      // Midway: a sandy atoll with a radio mast, sending in plain English
      const cam = keys(t, [[sh.t0, { x: 960, y: 640, z: 1.2 }], [sh.t1, { x: 980, y: 640, z: 1.35 }]])
      ocean(c, cam, t, { tod: 'day', water: '#3a8aa0', inner: c => { c.fillStyle = vgrad(c, 780, 900, '#efe2c0', '#d8c69a'); ell(c, 960, 860, 700, 70, 0); c.fill(); ell(c, 960, 860, 760, 90, 0, 'rgba(160,220,220,0.35)'); for (let x = 400; x < 1500; x += 140) PK.tree(c, x, 850, 140, 'palm', { t }); c.strokeStyle = '#3a3a3a'; c.lineWidth = 6; c.beginPath(); c.moveTo(1200, 850); c.lineTo(1200, 500); c.stroke(); for (let k = 1; k < 4; k++) { const ph = (t * 0.8 + k / 3) % 1; c.strokeStyle = `rgba(255,255,255,${1 - ph})`; c.lineWidth = 3; c.beginPath(); c.arc(1200, 500, 30 + ph * 220, -Math.PI * 0.8, -Math.PI * 0.2); c.stroke() } } })
      post(c, cam, { rays: 0.12 })
      word(c, '“our fresh water plant has broken down”', 150, prog(t, q('fresh water'), q('fresh water') + 0.4), 50)
    } else {
      dark(c)
      paper(c, 960, 520, 1100, 600, [['intercepted', 36, '#5a5a5a', { italic: true }], ['', 30], ['AF IS SHORT', 96, '#3a3a3a', { weight: 800, font: 'OldStandard', alpha: prog(t, q('a f is short'), q('a f is short') + 0.4) }], ['OF WATER', 96, '#3a3a3a', { weight: 800, font: 'OldStandard', alpha: prog(t, q('of water'), q('of water') + 0.4) }]], { top: 100, col: '#ece6d8' })
      post(c, { x: 960 }, { rays: false, vignette: 0.55 })
    }
  }

  // ---------- 3: Nimitz, the Yorktown in three days
  SC[3] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'nimitz'], [q('a third the yorktown') - 0.3, 'dock'], [q('nimitz gave them') - 0.3, 'repair'], [q('she sailed') - 0.3, 'sail'], [q('three american carriers') - 0.3, 'chart']])
    if (sh.name === 'nimitz') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 680, z: 1.4 }], [sh.t1, { x: 980, y: 680, z: 1.55 }]])
      basement(c, cam, t, { inner: c => { c.fillStyle = '#c8d8e0'; c.fillRect(1050, 380, 640, 420); c.strokeStyle = 'rgba(40,60,80,0.4)'; for (let k = 0; k < 7; k++) { c.beginPath(); c.moveTo(1050 + k * 92, 380); c.lineTo(1050 + k * 92, 800); c.stroke() } for (let k = 0; k < 2; k++) ell(c, 1300 + k * 60, 600, 16, 7, 0, '#2a4a7a'); person(c, 860, 1060, 1.0, { cos: 'nimitz', pose: { name: 'point' }, target: [1320, 600], face: { mood: 'stern' } }) } })
      post(c, cam, { rays: false, vignette: 0.55 })
      label(c, 'Admiral Chester Nimitz', W / 2, 110, prog(t, q('chester nimitz'), q('chester nimitz') + 0.5))
      word(c, 'two carriers ready', 980, prog(t, q('he had two'), q('he had two') + 0.4), 44)
    } else if (sh.name === 'dock' || sh.name === 'repair') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 640, z: 1.25 }], [sh.t1, { x: 1000, y: 640, z: 1.4 }]])
      ocean(c, cam, t, { tod: 'day', clouds: 5, inner: c => {
        c.fillStyle = vgrad(c, 760, 1100, '#7a7670', '#4a4640'); c.fillRect(-900, 860, 3800, 600); c.fillStyle = '#5a5650'; c.fillRect(200, 760, 1500, 120)
        carrier(c, 960, 840, 0.95, t, { planes: 0 })
        c.fillStyle = '#1a1a1c'; ell(c, 820, 730, 90, 16, 0); c.fill()
        for (let x = 150; x < 1800; x += 220) { c.strokeStyle = '#3a3a3a'; c.lineWidth = 8; c.beginPath(); c.moveTo(x, 860); c.lineTo(x, 540); c.lineTo(x + 140, 540); c.stroke() }
        if (sh.name === 'repair') { for (let k = 0; k < 6; k++) { const wx = 520 + k * 150, ph = (t * 2 + k * 0.3) % 1; for (let j = 0; j < 8; j++) ell(c, wx + Math.cos(j + t * 8) * ph * 40, 720 + Math.sin(j * 1.3) * ph * 30 + ph * 40, 3, 3, 0, `rgba(255,${200 + j * 6},120,${1 - ph})`); person(c, wx, 726, 0.32, { cos: 'worker', pose: { name: 'crouch' }, noShadow: true }) } }
      } })
      post(c, cam, { rays: 0.1 })
      if (sh.name === 'dock') { label(c, 'USS Yorktown', W / 2, 110, prog(t, q('the yorktown'), q('the yorktown') + 0.5)); word(c, 'the yard said: months', 990, prog(t, q('needed months'), q('needed months') + 0.3), 44) }
      else { count(c, W / 2, 230, '3 days', 130) }
    } else if (sh.name === 'sail') {
      const cam = keys(t, [[sh.t0, { x: 800, y: 680, z: 1.2 }], [sh.t1, { x: 1200, y: 680, z: 1.3 }]], 'l')
      ocean(c, cam, t, { tod: 'day', inner: c => { carrier(c, lerp(500, 1500, prog(t, sh.t0, sh.t1)), 860, 0.85, t, { planes: 3 }); for (let k = 0; k < 4; k++) ell(c, lerp(500, 1500, prog(t, sh.t0, sh.t1)) - 700 - k * 80, 870, 60 + k * 14, 8, 0, 'rgba(240,248,255,0.45)') } })
      post(c, cam, { rays: 0.12 })
      word(c, 'repair crews still on board', 150, prog(t, q('repair crews'), q('repair crews') + 0.4))
    } else {
      seaChart(c, t, (c, w, h) => { ell(c, 60, 60, 14, 9, 0.3, 'rgba(110,90,60,1)'); text(c, 'Midway', 60, 26, 38, '#3a2a1a', { italic: true }); for (let k = 0; k < 3; k++) { const a = prog(t, sh.t0 + 0.3 + k * 0.3, sh.t0 + 0.8 + k * 0.3); ell(c, 220 + k * 50, -180 + k * 20, 16, 7, 0.1, `rgba(42,74,122,${a})`) } text(c, 'waiting at “Point Luck”', 260, -250, 32, `rgba(42,74,122,${prog(t, q('and waited'), q('and waited') + 0.4)})`, { italic: true, weight: 800 }); const jp = prog(t, q('the men setting'), sh.t1, 'io'); const e = pathLine(c, [[-600, -100], [-400, -60], [-200, -10]], jp, '#8a2a1e', 7); if (e) ell(c, e[0], e[1], 12, 12, 0, '#8a2a1e') })
      post(c, { x: 960 }, { rays: false, vignette: 0.5 })
    }
  }

  // ---------- 4: dawn, the strike on Midway, the order to switch to bombs
  SC[4] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'launch'], [q('he sent 108') - 0.3, 'strike'], [q('but the airfield') - 0.3, 'radio'], [q('nagumo had a second') - 0.3, 'hangar']])
    if (sh.name === 'launch') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 700, z: 1.35 }], [sh.t1, { x: 1060, y: 680, z: 1.45 }]])
      ocean(c, cam, t, { tod: 'morning', sun: [300, 560, 700, '255,200,150'], inner: c => { carrier(c, 1000, 860, 0.9, t, { jp: true, island: 'right' }); for (let k = 0; k < 4; k++) { const u = ((t - sh.t0) * 0.18 + k * 0.25) % 1; plane(c, lerp(420, 2200, u), 740 - u * 300, 0.55, t, { kind: 'zero', ang: -0.15 }) } } })
      post(c, cam, { rays: 0.18, rayX: 100, grade: 'rgba(220,140,100,0.18)' })
      label(c, '4:30 a.m.', W / 2, 110, prog(t, sh.t0 + 0.3, sh.t0 + 0.9) * (1 - prog(t, q('the man in command') - 0.3, q('the man in command'))))
      label(c, 'Admiral Chuichi Nagumo', W / 2, 110, prog(t, q('admiral nagumo'), q('admiral nagumo') + 0.5))
    } else if (sh.name === 'strike') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 640, z: 1.15 }], [sh.t1, { x: 980, y: 660, z: 1.3 }]])
      ocean(c, cam, t, { tod: 'morning', water: '#3a8aa0', inner: c => { c.fillStyle = vgrad(c, 780, 900, '#efe2c0', '#d8c69a'); ell(c, 960, 860, 700, 70, 0); c.fill(); for (let x = 400; x < 1500; x += 160) PK.tree(c, x, 850, 120, 'palm', { t }); for (let k = 0; k < 5; k++) { const u = ((t - sh.t0) * 0.6 + k * 0.2) % 1; blast(c, 500 + k * 220, 840, 0.6, u); if (u > 0.3) fire(c, 500 + k * 220, 840, 80, t, 0.4) } for (let k = 0; k < 12; k++) { const x = lerp(-300, 2200, ((t - sh.t0) * 0.06 + (k % 6) * 0.03) % 1); plane(c, x, 300 + (k % 3) * 40 + Math.floor(k / 6) * 60, 0.4, t, { kind: 'kate' }) } } })
      post(c, cam, { rays: 0.12, grade: 'rgba(200,140,100,0.12)' })
      count(c, W / 2, 200, '108 planes', 90)
    } else if (sh.name === 'radio') {
      dark(c)
      paper(c, 960, 520, 1100, 520, [['From the strike leader', 36, '#5a5a5a', { italic: true }], ['', 30], ['THERE IS NEED FOR', 72, '#3a3a3a', { weight: 800, font: 'OldStandard', alpha: prog(t, q('there is need'), q('there is need') + 0.4) }], ['A SECOND ATTACK', 72, '#3a3a3a', { weight: 800, font: 'OldStandard', alpha: prog(t, q('a second attack'), q('a second attack') + 0.4) }]], { top: 100, col: '#ece6d8' })
      post(c, { x: 960 }, { rays: false, vignette: 0.55 })
    } else {
      // the hangar deck: torpedoes coming off, bombs going on
      const cam = keys(t, [[sh.t0, { x: 960, y: 720, z: 1.4 }], [sh.t1, { x: 1060, y: 720, z: 1.55 }]])
      const swap = prog(t, q('take off the torpedoes'), q('below decks') + 2)
      hangar(c, cam, t, { inner: c => { for (let k = 0; k < 4; k++) { const x = 300 + k * 420; plane(c, x, 760, 1.0, t, { kind: 'kate', load: swap < 0.5 ? 'torpedo' : 'bomb' }); if (swap > 0.3) torpedo(c, x - 10, 960, 0.7); person(c, x - 120, 1010, 0.78, { cos: 'jpcrew', pose: { name: 'stand' }, face: { look: -0.2 } }); person(c, x + 130, 1010, 0.78, { cos: 'jpcrew', f: -1, pose: { name: 'hold', at: [50, -150] }, holdFn: c => bomb(c, 0, 0, 0.45) }) } } })
      post(c, cam, { rays: false, vignette: 0.6 })
      word(c, 'take off the torpedoes, load bombs', 150, prog(t, q('take off the torpedoes'), q('take off the torpedoes') + 0.4), 50)
    }
  }

  // ---------- 5: one of them looks like a carrier
  SC[5] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'scout'], [q('ten ships') - 0.3, 'msg'], [q('nagumo reversed') - 0.3, 'hangar'], [q('and now his first') - 0.3, 'circling'], [q('he could launch') - 0.3, 'choice']])
    if (sh.name === 'scout') {
      const cam = keys(t, [[sh.t0, { x: 900, y: 500, z: 1.4 }], [sh.t1, { x: 1100, y: 520, z: 1.5 }]], 'l')
      ocean(c, cam, t, { tod: 'day', horizon: 760, inner: c => { plane(c, lerp(400, 1400, prog(t, sh.t0, sh.t1)), 420, 0.9, t, { kind: 'scout' }); for (let k = 0; k < 5; k++) ell(c, 1500 + k * 60, 800, 14, 4, 0, '#3a4048') } })
      post(c, cam, { rays: 0.12 })
      word(c, 'a scout plane, half an hour late', 150, prog(t, q('one that had taken off'), q('one that had taken off') + 0.4), 46)
    } else if (sh.name === 'msg') {
      dark(c)
      paper(c, 960, 520, 1100, 560, [['TEN SHIPS', 84, '#3a3a3a', { weight: 800, font: 'OldStandard' }], ['TO THE EAST', 60, '#3a3a3a', { weight: 800, font: 'OldStandard', alpha: prog(t, q('to the east'), q('to the east') + 0.3) }], ['', 30], ['ONE APPEARS TO BE', 52, '#8a2a1e', { weight: 800, font: 'OldStandard', alpha: prog(t, q('one of them'), q('one of them') + 0.4) }], ['A CARRIER', 52, '#8a2a1e', { weight: 800, font: 'OldStandard', alpha: prog(t, q('looks like a carrier'), q('looks like a carrier') + 0.4) }]], { top: 90, col: '#ece6d8' })
      post(c, { x: 960 }, { rays: false, vignette: 0.55 })
    } else if (sh.name === 'hangar') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 720, z: 1.5 }], [sh.t1, { x: 1100, y: 720, z: 1.7 }]])
      hangar(c, cam, t, { inner: c => { for (let k = 0; k < 4; k++) { const x = 300 + k * 420; plane(c, x, 760, 1.0, t, { kind: 'kate', load: 'torpedo' }); bomb(c, x + 40, 980, 0.6); bomb(c, x + 120, 1000, 0.6); bomb(c, x + 80, 960, 0.6); person(c, x - 120, 1010, 0.78, { cos: 'jpcrew', pose: { name: 'stand' } }) } c.strokeStyle = '#1a1a1a'; c.lineWidth = 10; c.beginPath(); c.moveTo(-200, 1060); c.bezierCurveTo(600, 1000, 1200, 1100, 2200, 1040); c.stroke() } })
      post(c, cam, { rays: false, vignette: 0.6 })
      word(c, 'bombs stacked in the hangars', 150, prog(t, q('bombs were stacked'), q('bombs were stacked') + 0.4) * (1 - prog(t, q('fuel hoses') - 0.2, q('fuel hoses'))))
      word(c, 'fuel hoses across the decks', 150, prog(t, q('fuel hoses'), q('fuel hoses') + 0.4))
    } else if (sh.name === 'circling') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 640, z: 1.25 }], [sh.t1, { x: 1000, y: 640, z: 1.35 }]])
      ocean(c, cam, t, { tod: 'day', inner: c => { carrier(c, 1000, 860, 0.8, t, { jp: true, island: 'left' }); for (let k = 0; k < 8; k++) { const a = t * 0.4 + k * 0.785; plane(c, 1000 + Math.cos(a) * 700, 520 + Math.sin(a) * 120, 0.42, t, { kind: 'kate', f: Math.sin(a) > 0 ? -1 : 1 }) } } })
      post(c, cam, { rays: 0.12 })
      word(c, 'the first wave, low on fuel', 150, prog(t, q('low on gas'), q('low on gas') + 0.4))
    } else {
      const cam = keys(t, [[sh.t0, { x: 900, y: 600, z: 1.05 }], [sh.t1, { x: 900, y: 600, z: 1.15 }]])
      bridge(c, cam, t, { x: 760, mood: 'stern', look: -0.05 })
      post(c, cam, { rays: 0.1 })
      word(c, 'launch now, or land, arm, and strike once?', 150, prog(t, q('he could launch'), q('he could launch') + 0.4) * (1 - prog(t, q('he decided') - 0.2, q('he decided'))), 46)
      word(c, 'He decided to wait.', 150, prog(t, q('he decided'), q('he decided') + 0.4), 60)
    }
  }
})()
