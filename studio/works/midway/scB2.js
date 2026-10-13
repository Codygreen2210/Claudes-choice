// scB2.js: scenes 6-11 of the Battle of Midway, Style B.
(function () {
  const { W, H, clamp, lerp, prog, keys, rng, ell, poly, shade, vgrad, hgrad, rgrad, layer, fog, sky, post, person, crowd, paper, map, pathLine, count, text, label, shake, flashes } = PK
  const { ocean, carrier, destroyer, battleship, fire, blast, splash, flak, plane, planeTop, carrierTop, basement, hangar, torpedo, bomb, seaChart, shotOf } = MWB
  const SC = window.SCENES = window.SCENES || []
  const dark = c => { c.fillStyle = vgrad(c, 0, H, '#24282c', '#101214'); c.fillRect(0, 0, W, H) }
  const word = (c, s, y, a, size = 54) => text(c, s, W / 2, y, size, '#f3e7d0', { italic: true, shadow: 16, alpha: a })
  // seen from straight above, high up: ocean far below, clouds drifting past, the fleet as wakes
  function fromAbove(c, t, o = {}) {
    c.fillStyle = vgrad(c, 0, H, '#3a5a78', '#24405a'); c.fillRect(0, 0, W, H)
    const r = rng(o.seed || 4); c.strokeStyle = 'rgba(230,240,250,0.12)'; c.lineWidth = 2; for (let k = 0; k < 160; k++) { const x = r() * W, y = r() * H; c.beginPath(); c.moveTo(x, y); c.lineTo(x + 14, y); c.stroke() }
    if (o.inner) o.inner(c)
    for (let k = 0; k < 7; k++) { const x = ((r() * 2400 + t * (o.drift ?? 40)) % 2600) - 300, y = r() * H; c.fillStyle = 'rgba(255,255,255,0.55)'; for (let j = 0; j < 5; j++) { ell(c, x + j * 50, y + Math.sin(j) * 20, 80, 50, 0); c.fill() } }
  }

  // ---------- 6: the torpedo planes
  SC[6] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'midway'], [q('then came the planes') - 0.3, 'tbd'], [q('torpedo squadron eight') - 0.3, 'eight'], [q('of thirty men') - 0.3, 'gay'], [q('two more squadrons') - 0.3, 'count']])
    if (sh.name === 'midway') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 620, z: 1.2 }], [sh.t1, { x: 1060, y: 640, z: 1.35 }]])
      const u = t - sh.t0
      ocean(c, cam, t, { tod: 'day', inner: c => { carrier(c, 1300, 860, 0.7, t, { jp: true, island: 'left' }); flak(c, t, 300, 240, 1500, 400, 20, 9); for (let k = 0; k < 3; k++) plane(c, lerp(-200, 2200, ((u * 0.07 + k * 0.3) % 1)), 260 + k * 40, 0.5, t, { kind: 'b17' }); for (let k = 0; k < 6; k++) splash(c, 700 + k * 200, 900 + (k % 2) * 20, 0.9, ((u * 0.4 + k * 0.15) % 1)); plane(c, lerp(2000, 0, ((u * 0.12) % 1)), 640, 0.7, t, { kind: 'zero', f: -1 }); plane(c, lerp(1200, 1600, ((u * 0.2) % 1)), 560 + ((u * 0.2) % 1) * 300, 0.6, t, { kind: 'sbd', smoke: true, ang: 0.5 }) } })
      post(c, cam, { rays: 0.12 })
      const W2 = [['Marine pilots', 'marine pilots'], ['Army bombers', 'army bombers'], ['Six new torpedo planes', 'six brand new']]
      W2.forEach(([s, w]) => word(c, s, 150, prog(t, q(w), q(w) + 0.3) * (1 - prog(t, q(w) + 1.6, q(w) + 2))))
      word(c, 'nothing hit', 150, prog(t, q('and nothing hit'), q('and nothing hit') + 0.3))
    } else if (sh.name === 'tbd' || sh.name === 'eight') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 760, z: 1.6 }], [sh.t1, { x: 1100, y: 760, z: 1.7 }]])
      const u = t - sh.t0, lost = sh.name === 'eight' ? prog(t, q('all fifteen'), q('all fifteen') + 1.2) : 0
      ocean(c, cam, t, { tod: 'day', inner: c => { carrier(c, 1600, 840, 0.7, t, { jp: true, island: 'left' }); flak(c, t, 400, 500, 1600, 300, 26, 13); for (let k = 0; k < 5; k++) { const x = lerp(-200, 1300, ((u * 0.1 + k * 0.17) % 1)), hit = k < lost * 5; plane(c, x, 900 - k * 22 + (hit ? 60 : 0), 0.8, t, { kind: 'tbd', load: 'torpedo', smoke: hit, ang: hit ? 0.3 : 0 }) } for (let k = 0; k < 3; k++) plane(c, lerp(1800, 200, ((u * 0.18 + k * 0.33) % 1)), 760 + k * 30, 0.6, t, { kind: 'zero', f: -1 }) } })
      post(c, cam, { rays: 0.1 })
      if (sh.name === 'tbd') word(c, 'low and straight, into the guns', 150, prog(t, q('to drop a torpedo'), q('to drop a torpedo') + 0.4), 50)
      else { label(c, 'Torpedo Squadron Eight', W / 2, 110, prog(t, sh.t0 + 0.3, sh.t0 + 0.9)); if (t > q('fifteen planes')) count(c, W / 2, 240, Math.round(lerp(15, 0, lost)) + ' of 15', 110) }
    } else if (sh.name === 'gay') {
      // George Gay, in the water among the wreckage, watching the carriers
      const cam = keys(t, [[sh.t0, { x: 900, y: 860, z: 2.2 }], [sh.t1, { x: 960, y: 820, z: 1.7 }]])
      ocean(c, cam, t, { tod: 'day', inner: c => { carrier(c, 1500, 820, 0.5, t, { jp: true }); carrier(c, 300, 840, 0.45, t, { jp: true, island: 'left' }); c.fillStyle = '#4a4a44'; c.save(); c.translate(1050, 960); c.rotate(0.2); c.fillRect(-90, -10, 180, 20); c.restore(); ell(c, 820, 965, 46, 12, 0, '#8a7a5a'); ell(c, 820, 950, 16, 16, 0, '#dcae90'); c.fillStyle = '#5a3a22'; ell(c, 818, 940, 17, 10, 0); c.fill(); for (let k = 0; k < 5; k++) ell(c, 820 + Math.cos(t * 2 + k) * 60, 972, 30, 4, 0, 'rgba(240,248,255,0.5)') } })
      post(c, cam, { rays: 0.12 })
      word(c, 'of thirty men, one lived', 150, prog(t, q('of thirty men'), q('of thirty men') + 0.4) * (1 - prog(t, q('a young pilot') - 0.2, q('a young pilot'))))
      label(c, 'Ensign George Gay', W / 2, 110, prog(t, q('george gay'), q('george gay') + 0.5))
    } else {
      dark(c)
      const a = prog(t, q('forty one'), q('forty one') + 0.5), b = prog(t, q('thirty four'), q('thirty four') + 0.5)
      for (let k = 0; k < 41; k++) { const lost = k < 34 && b > 0, x = 420 + (k % 14) * 80, y = 360 + Math.floor(k / 14) * 120; c.save(); c.globalAlpha = a * (lost ? 1 - b * 0.75 : 1); plane(c, x, y, 0.35, 0, { kind: 'tbd' }); c.restore() }
      text(c, '41 torpedo planes', W / 2, 220, 60, '#f3e7d0', { weight: 800, alpha: a, shadow: 16 }); text(c, '34 did not come back', W / 2, 780, 56, '#c8483a', { weight: 800, alpha: b, shadow: 16 }); word(c, 'not one torpedo hit', 880, prog(t, q('not one torpedo'), q('not one torpedo') + 0.4), 48)
      post(c, { x: 960 }, { rays: false, vignette: 0.5 })
    }
  }

  // ---------- 7: McClusky, the empty ocean, the destroyer's wake
  SC[7] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'low'], [q('and high above') - 0.3, 'high'], [q('he had flown') - 0.3, 'empty'], [q('his planes were running') - 0.3, 'fuel'], [q('and then he saw') - 0.3, 'wake']])
    if (sh.name === 'low') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 760, z: 1.5 }], [sh.t1, { x: 1060, y: 740, z: 1.6 }]])
      const u = t - sh.t0
      ocean(c, cam, t, { tod: 'day', inner: c => { for (let k = 0; k < 3; k++) carrier(c, 300 + k * 650, 820 + (k % 2) * 30, 0.5, t, { jp: true, island: k % 2 ? 'left' : 'right', f: k % 2 ? -1 : 1 }); for (let k = 0; k < 6; k++) plane(c, lerp(-200, 2200, ((u * 0.12 + k * 0.16) % 1)), 900 - (k % 3) * 30, 0.5, t, { kind: 'zero' }) } })
      post(c, cam, { rays: 0.1 })
      word(c, 'the fighters pulled down to the water', 150, prog(t, q('they had pulled'), q('they had pulled') + 0.4), 48)
    } else if (sh.name === 'high' || sh.name === 'fuel') {
      // high above the clouds: a formation of dive bombers, and the leader's plane close
      const cam = keys(t, [[sh.t0, { x: 960, y: 600, z: 1.0 }], [sh.t1, { x: 1000, y: 600, z: 1.1 }]])
      layer(c, cam, 0.05, c => sky(c, '#3a6a9a', '#a8c4dc', { horizon: 900, clouds: 0, sun: [1600, 140, 500] }))
      layer(c, cam, 0.4, c => { MWB.cloudDeck(c, 820) })
      layer(c, cam, 1, c => { for (let k = 0; k < 9; k++) plane(c, 300 + (k % 3) * 160 + Math.floor(k / 3) * 360, 300 + (k % 3) * 60 + Math.sin(t + k) * 6, 0.4, t, { kind: 'sbd', load: 'bomb' }); plane(c, 1200, 600 + Math.sin(t) * 8, 1.4, t, { kind: 'sbd', load: 'bomb' }) })
      post(c, cam, { rays: 0.16, rayX: 1100 })
      if (sh.name === 'high') label(c, 'Lt. Cmdr. Wade McClusky, USS Enterprise', W / 2, 110, prog(t, q('wade mcclusky'), q('wade mcclusky') + 0.5))
      else { const g = lerp(0.5, 0.2, prog(t, sh.t0, sh.t1)); c.save(); c.translate(W - 260, H - 300); ell(c, 0, 0, 150, 150, 0, '#1a1a1a'); c.strokeStyle = '#e8e4d8'; c.lineWidth = 4; c.beginPath(); c.arc(0, 0, 130, Math.PI, 0); c.stroke(); text(c, 'E', -120, 30, 30, '#e8e4d8', { weight: 800 }); text(c, 'F', 120, 30, 30, '#e8e4d8', { weight: 800 }); c.rotate(Math.PI + g * Math.PI); c.strokeStyle = '#c8483a'; c.lineWidth = 6; c.beginPath(); c.moveTo(0, 0); c.lineTo(110, 0); c.stroke(); c.restore(); word(c, 'going on meant some would not make it home', 150, prog(t, q('going on meant'), q('going on meant') + 0.4), 44); word(c, 'He went on.', 250, prog(t, q('he went on'), q('he went on') + 0.3), 60) }
    } else if (sh.name === 'empty') {
      fromAbove(c, t, {})
      post(c, { x: 960 }, { rays: false, vignette: 0.6 })
      word(c, 'nothing there but ocean', 150, prog(t, q('nothing there'), q('nothing there') + 0.4))
    } else {
      const k = prog(t, sh.t0, sh.t1)
      fromAbove(c, t, { drift: 20, inner: c => { c.save(); c.translate(W / 2, H / 2); c.scale(lerp(0.8, 1.2, k), lerp(0.8, 1.2, k)); c.translate(-W / 2, -H / 2); const x = 760 + k * 120, y = 640 - k * 280; for (let j = 0; j < 30; j++) ell(c, x - 6, y + 40 + j * 22, 10 + j * 2, 14, 0, `rgba(245,250,255,${0.7 - j * 0.02})`); c.fillStyle = '#5a5a60'; poly(c, [[x, y - 50], [x + 14, y - 20], [x + 12, y + 40], [x - 12, y + 40], [x - 14, y - 20]]); c.fill(); c.restore() } })
      post(c, { x: 960 }, { rays: false, vignette: 0.6 })
      word(c, 'one destroyer, alone, running north', 150, prog(t, q('one japanese destroyer'), q('one japanese destroyer') + 0.4) * (1 - prog(t, q('mcclusky followed') - 0.3, q('mcclusky followed'))), 48)
      word(c, 'McClusky followed it.', 150, prog(t, q('mcclusky followed'), q('mcclusky followed') + 0.3), 56)
    }
  }

  // ---------- 8: five minutes
  SC[8] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'roll'], [q('there were no fighters') - 0.3, 'dive'], [q('the carrier kaga') - 0.3, 'kaga'], [q('the flagship akagi') - 0.3, 'akagi'], [q('and at that same') - 0.3, 'yorktown'], [q('they put three') - 0.3, 'soryu'], [q('by 1026') - 0.3, 'burning'], [q('twenty minutes later') - 0.3, 'abandon'], [q('it had taken') - 0.3, 'five']])
    const hits = [q('took four') + 0.2, q('took four') + 0.6, q('took one') + 0.2, q('three bombs into') + 0.3, q('three bombs into') + 0.7]
    if (sh.name === 'roll') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 600, z: 1.1 }], [sh.t1, { x: 1000, y: 620, z: 1.3 }]])
      layer(c, cam, 0.05, c => sky(c, '#3a6a9a', '#a8c4dc', { horizon: 900, clouds: 0, sun: [1600, 140, 500] }))
      layer(c, cam, 0.4, c => { MWB.cloudDeck(c, 860) })
      layer(c, cam, 1, c => { for (let k = 0; k < 6; k++) { const roll = prog(t, q('rolled over') + k * 0.25, q('rolled over') + k * 0.25 + 0.8); plane(c, 500 + k * 180 + roll * 60, 400 + k * 30 + roll * roll * 400, 0.7, t, { kind: 'sbd', load: 'bomb', ang: roll * 1.3 }) } })
      post(c, cam, { rays: 0.16, rayX: 1100 })
      label(c, '10:22 a.m.', W / 2, 110, prog(t, sh.t0 + 0.2, sh.t0 + 0.8))
    } else if (sh.name === 'dive' || sh.name === 'kaga' || sh.name === 'akagi' || sh.name === 'soryu') {
      // straight down at a flight deck with its red circle, growing as they dive
      const k = prog(t, sh.t0, sh.t1)
      const [sx, sy] = shake(t, hits, 16);
      fromAbove(c, t, { drift: 120, inner: c => {
        c.save(); c.translate(W / 2 + sx, H / 2 + sy); const z = lerp(0.6, 1.25, k); c.scale(z, z); c.translate(-W / 2, -H / 2)
        carrierTop(c, 960, 540, 0.8, t, { rot: -0.25 + (sh.name === 'akagi' ? 0.5 : sh.name === 'soryu' ? -0.4 : 0) })
        hits.forEach((h, i) => { const u = (t - h) / 1.4; if (u > 0) { const hx = 760 + i * 90 - (sh.name === 'kaga' ? 0 : 100), hy = 520 + (i % 2) * 30; blast(c, hx, hy, 0.9, u); if (u > 0.3) { ell(c, hx, hy, 60, 50, 0, 'rgba(40,30,24,0.7)'); fire(c, hx, hy, 80, t, 0.3) } } })
        c.restore()
        for (let j = 0; j < 3; j++) { const pu = ((t - sh.t0) * 0.6 + j * 0.33) % 1; planeTop(c, lerp(200, 1700, pu), lerp(900, 200, pu), 0.6 + pu * 0.4, -0.6) }
      } })
      post(c, { x: 960 }, { rays: false, vignette: 0.6 })
      flashes(c, t, hits, '255,230,180', 0.5)
      if (sh.name === 'dive') word(c, 'no fighters up high to stop them', 150, prog(t, sh.t0 + 0.2, sh.t0 + 0.7), 48)
      if (sh.name === 'kaga') label(c, 'Kaga', W / 2, 110, prog(t, q('kaga'), q('kaga') + 0.4))
      if (sh.name === 'akagi') { label(c, 'Akagi, the flagship', W / 2, 110, prog(t, q('akagi'), q('akagi') + 0.4)); word(c, 'into a hangar full of fueled planes and bombs', 990, prog(t, q('into a hangar'), q('into a hangar') + 0.4), 44) }
      if (sh.name === 'soryu') label(c, 'Soryu', W / 2, 110, prog(t, q('the soryu'), q('the soryu') + 0.4))
    } else if (sh.name === 'yorktown') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 600, z: 1.1 }], [sh.t1, { x: 1000, y: 620, z: 1.25 }]])
      layer(c, cam, 0.05, c => sky(c, '#3a6a9a', '#a8c4dc', { horizon: 900, clouds: 0, sun: [400, 140, 500] }))
      layer(c, cam, 0.4, c => { MWB.cloudDeck(c, 860) })
      layer(c, cam, 1, c => { for (let k = 0; k < 8; k++) plane(c, lerp(1900, 900, prog(t, sh.t0, sh.t1)) + k * 120, 300 + (k % 3) * 70, 0.55, t, { kind: 'sbd', load: 'bomb', f: -1 }) })
      post(c, cam, { rays: 0.16, rayX: 300 })
      word(c, 'by pure chance, a second group: from the Yorktown', 150, prog(t, q('by pure chance'), q('by pure chance') + 0.4), 44)
    } else if (sh.name === 'burning' || sh.name === 'abandon') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 660, z: 1.15 }], [sh.t1, { x: 1000, y: 660, z: 1.3 }]])
      ocean(c, cam, t, { tod: 'day', clouds: 4, inner: c => {
        carrier(c, 300, 780, 0.42, t, { jp: true, island: 'left', fire: 1 }); carrier(c, 900, 820, 0.5, t, { jp: true, fire: 1 }); carrier(c, 1500, 790, 0.45, t, { jp: true, island: 'left', fire: 1 }); carrier(c, 2100, 720, 0.3, t, { jp: true })
        if (sh.name === 'abandon') { const u = prog(t, sh.t0, sh.t1); c.fillStyle = '#3a3a3a'; c.fillRect(980 + u * 300, 900, 80, 16); person(c, 1010 + u * 300, 902, 0.2, { cos: 'nagumo', noShadow: true }) }
      } })
      post(c, cam, { rays: 0.06, grade: 'rgba(200,100,60,0.2)' })
      label(c, '10:26 a.m.', W / 2, 110, prog(t, sh.t0 + 0.2, sh.t0 + 0.8) * (1 - prog(t, sh.t1 - 0.6, sh.t1)))
      if (sh.name === 'abandon') word(c, 'Nagumo abandoned his flagship', 150, prog(t, q('nagumo abandoned'), q('nagumo abandoned') + 0.4))
    } else {
      dark(c)
      count(c, W / 2, 470, 'about 5 minutes', 150)
      post(c, { x: 960 }, { rays: false, vignette: 0.5 })
    }
  }

  // ---------- 9: the Hiryu strikes back; the Yorktown; the Hiryu; Yamamoto turns for home
  SC[9] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'hiryu'], [q('her planes followed') - 0.3, 'yorktown'], [q('the crew patched') - 0.3, 'patch'], [q('they hit her again') - 0.3, 'torpedo'], [q('but that afternoon') - 0.3, 'found'], [q('yamamoto was') - 0.3, 'turn']])
    if (sh.name === 'hiryu') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 660, z: 1.25 }], [sh.t1, { x: 1000, y: 660, z: 1.35 }]])
      ocean(c, cam, t, { tod: 'day', inner: c => { carrier(c, 960, 840, 0.85, t, { jp: true, island: 'left' }); for (let k = 0; k < 6; k++) { const u = ((t - sh.t0) * 0.2 + k * 0.17) % 1; plane(c, lerp(700, 2200, u), 760 - u * 400, 0.5, t, { kind: 'kate', ang: -0.2 }) } } })
      post(c, cam, { rays: 0.12 })
      label(c, 'Hiryu, the last carrier', W / 2, 110, prog(t, q('the hiryu'), q('the hiryu') + 0.4))
    } else if (sh.name === 'yorktown' || sh.name === 'patch' || sh.name === 'torpedo') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 680, z: 1.3 }], [sh.t1, { x: 1000, y: 680, z: 1.4 }]])
      const hitT = sh.name === 'yorktown' ? [q('three bombs') + 0.3, q('three bombs') + 0.8, q('three bombs') + 1.2] : sh.name === 'torpedo' ? [q('with torpedoes') + 0.3, q('with torpedoes') + 0.9] : []
      const [sx, sy] = shake(t, hitT, 12); cam.sx = sx; cam.sy = sy
      ocean(c, cam, t, { tod: 'day', inner: c => { carrier(c, 960, 850, 0.95, t, { fire: sh.name === 'patch' ? 0.25 : sh.name === 'torpedo' ? 0.6 : prog(t, hitT[0], hitT[0] + 1) * 0.7 }); hitT.forEach((h, i) => { blast(c, 700 + i * 260, 760, 0.6, (t - h) / 1.2); if (sh.name === 'torpedo') splash(c, 700 + i * 260, 860, 1.4, (t - h) / 1.4) }); flak(c, t, 200, 250, 1500, 350, 16, 21); for (let k = 0; k < 4; k++) { const u = ((t - sh.t0) * 0.2 + k * 0.25) % 1; plane(c, lerp(-200, 2100, u), sh.name === 'torpedo' ? 880 - k * 20 : 420 + k * 40, 0.55, t, { kind: 'kate', load: sh.name === 'torpedo' ? 'torpedo' : 'bomb' }) } } })
      post(c, cam, { rays: 0.1 })
      flashes(c, t, hitT, '255,230,180', 0.35)
      label(c, 'USS Yorktown', W / 2, 110, prog(t, q('the yorktown'), q('the yorktown') + 0.4) * (1 - prog(t, sh.t1 - 0.6, sh.t1)))
      if (sh.name === 'patch') word(c, 'they thought it was a different ship', 150, prog(t, q('they thought'), q('they thought') + 0.4), 48)
      if (sh.name === 'torpedo') word(c, 'This time, she stopped.', 150, prog(t, q('this time she'), q('this time she') + 0.3), 56)
    } else if (sh.name === 'found') {
      const k = prog(t, q('the dive bombers came'), sh.t1)
      if (t < q('at five')) { const cam = { x: 960, y: 660, z: 1.3 }; ocean(c, cam, t, { tod: 'dusk', sun: [300, 520, 700, '255,190,130'], inner: c => carrier(c, 960, 840, 0.85, t, { jp: true, island: 'left' }) }); post(c, cam, { rays: 0.16, rayX: 200, grade: 'rgba(200,120,80,0.2)' }) }
      else { const hits = [q('four hits') + 0.0, q('four hits') + 0.3, q('four hits') + 0.6, q('four hits') + 0.9]; fromAbove(c, t, { drift: 100, inner: c => { c.save(); c.translate(W / 2, H / 2); const z = lerp(0.7, 1.15, k); c.scale(z, z); c.translate(-W / 2, -H / 2); carrierTop(c, 960, 540, 0.8, t, { rot: 0.2 }); hits.forEach((h, i) => { const u = (t - h) / 1.4; if (u > 0) { blast(c, 760 + i * 120, 530, 0.9, u); if (u > 0.3) fire(c, 760 + i * 120, 530, 80, t, 0.3) } }); c.restore() } }); c.fillStyle = 'rgba(200,110,60,0.18)'; c.fillRect(0, 0, W, H); flashes(c, t, hits, '255,230,180', 0.4); post(c, { x: 960 }, { rays: false, vignette: 0.6 }) }
      label(c, '5 p.m.', W / 2, 110, prog(t, q('at five'), q('at five') + 0.4))
      if (t > q('four hits')) word(c, 'four hits', 150, prog(t, q('four hits'), q('four hits') + 0.3))
    } else {
      seaChart(c, t, (c, w, h) => { ell(c, 260, 120, 14, 9, 0.3, 'rgba(110,90,60,1)'); text(c, 'Midway', 260, 86, 38, '#3a2a1a', { italic: true }); const back = prog(t, q('he turned the fleet'), sh.t1 - 0.2, 'io'); const x = lerp(-300, -600, back); battleship(c, x, -40, 0.12, t); text(c, 'Yamamoto, with his battleships', x, -110, 30, '#3a2a1a', { italic: true }); text(c, 'hundreds of miles behind', x, 10, 26, '#5a4030', { italic: true }); if (back > 0) pathLine(c, [[-300, -40], [x, -40]], 1, '#8a2a1e', 6) })
      post(c, { x: 960 }, { rays: false, vignette: 0.5 })
    }
  }

  // ---------- 10: the count
  SC[10] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'count'], [q('in japan') - 0.3, 'papers'], [q('the wounded') - 0.3, 'wounded']])
    if (sh.name === 'count') {
      dark(c)
      const a = prog(t, sh.t0 + 0.2, sh.t0 + 0.8), b = prog(t, q('the united states lost'), q('the united states lost') + 0.6)
      text(c, 'JAPAN', 560, 200, 54, '#f3e7d0', { weight: 800, alpha: a }); text(c, 'UNITED STATES', 1360, 200, 54, '#f3e7d0', { weight: 800, alpha: b })
      ;[['4 carriers', 'four aircraft'], ['1 heavy cruiser', 'a heavy cruiser'], ['≈ 250 planes', 'about 250'], ['3,000+ men', 'more than 3000']].forEach(([s, w], i) => text(c, s, 560, 320 + i * 110, 52, '#c8483a', { weight: 800, alpha: prog(t, q(w), q(w) + 0.3), shadow: 12 }))
      ;[['1 carrier', 'one carrier'], ['1 destroyer', 'one destroyer'], ['≈ 150 planes', 'about 150'], ['307 men', '307 men']].forEach(([s, w], i) => text(c, s, 1360, 320 + i * 110, 52, '#f3e7d0', { weight: 800, alpha: prog(t, q(w), q(w) + 0.3), shadow: 12 }))
      c.fillStyle = 'rgba(243,231,208,0.3)'; c.fillRect(958, 160, 4, 700)
      post(c, { x: 960 }, { rays: false, vignette: 0.5 })
    } else if (sh.name === 'papers') {
      dark(c)
      c.save(); c.translate(W / 2, 540); c.rotate(-0.02); c.fillStyle = 'rgba(0,0,0,0.35)'; c.fillRect(-360, -460, 740, 960); c.fillStyle = vgrad(c, -470, 470, '#ece4d0', '#d4c8ae'); c.fillRect(-370, -470, 740, 940); for (let col = 0; col < 8; col++) for (let k = 0; k < 22; k++) { c.fillStyle = 'rgba(40,36,30,0.55)'; c.fillRect(300 - col * 80, -380 + k * 36, 14, 26) } c.fillStyle = '#1a1814'; c.fillRect(-330, -420, 220, 300); c.restore()
      word(c, 'told: a great victory', 150, prog(t, q('a great victory'), q('a great victory') + 0.4))
      post(c, { x: 960 }, { rays: false, vignette: 0.5 })
    } else {
      const cam = keys(t, [[sh.t0, { x: 960, y: 680, z: 1.4 }], [sh.t1, { x: 960, y: 700, z: 1.55 }]])
      basement(c, cam, t, { inner: c => { for (let k = 0; k < 3; k++) { c.fillStyle = '#e8e4dc'; c.fillRect(300 + k * 480, 880, 380, 40); c.fillStyle = '#8a8a90'; c.fillRect(300 + k * 480, 920, 12, 120); c.fillRect(668 + k * 480, 920, 12, 120); ell(c, 360 + k * 480, 868, 22, 20, 0, '#d8a888') } c.fillStyle = '#4a3a2a'; c.fillRect(1700, 420, 200, 500) } })
      post(c, cam, { rays: false, vignette: 0.7 })
      word(c, 'kept away from their families', 150, prog(t, q('kept away'), q('kept away') + 0.4))
    }
  }

  // ---------- 11: small things
  SC[11] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'sea'], [q('and it turned') - 0.3, 'code'], [q('a ship fixed') - 0.3, 'ship'], [q('men in old planes') - 0.3, 'planes'], [q('and one pilot') - 0.3, 'pilot'], [q('admiral nimitz said') - 0.3, 'quote'], [q('subscribe') - 0.3, 'end']])
    if (sh.name === 'sea' || sh.name === 'end') {
      const cam = keys(t, [[sh.t0, { x: 900, y: 640, z: 1.15 }], [sh.t1, { x: 1100, y: 640, z: 1.05 }]], 'l')
      ocean(c, cam, t, { tod: 'dusk', sun: [960, 560, 800, '255,190,130'], inner: c => { carrier(c, 1300, 820, 0.45, t, {}); destroyer(c, 600, 800, 0.3, t) } })
      post(c, cam, { rays: 0.18, rayX: 700, grade: 'rgba(200,120,80,0.18)' })
      if (sh.name === 'sea') word(c, 'Japan never had the upper hand at sea again', 150, prog(t, q('but after midway'), q('but after midway') + 0.4), 46)
      else { const a = prog(t, sh.t0 + 0.3, sh.t0 + 1); text(c, 'Subscribe', W / 2, 330, 96, '#f3e7d0', { weight: 800, alpha: a, shadow: 24 }); text(c, 'animal facts  ·  great battles  ·  financial collapses', W / 2, 430, 40, '#f3e7d0', { italic: true, alpha: prog(t, q('everything from'), q('everything from') + 0.6), shadow: 14 }) }
    } else if (sh.name === 'code') { dark(c); paper(c, 960, 520, 900, 520, [['AF', 200, '#8a2a1e', { weight: 800, font: 'OldStandard' }], ['a code, half broken', 46, '#3a2a1a', { italic: true }]], { top: 150, col: '#ece6d8' }); post(c, { x: 960 }, { rays: false, vignette: 0.55 }) }
    else if (sh.name === 'ship') { const cam = { x: 960, y: 680, z: 1.3 }; ocean(c, cam, t, { tod: 'day', inner: c => carrier(c, 960, 850, 0.95, t, {}) }); post(c, cam, { rays: 0.12 }); word(c, 'a ship, fixed in three days', 150, prog(t, sh.t0 + 0.2, sh.t0 + 0.6)) }
    else if (sh.name === 'planes') { const cam = { x: 960, y: 760, z: 1.5 }; ocean(c, cam, t, { tod: 'day', inner: c => { for (let k = 0; k < 4; k++) plane(c, lerp(-200, 2100, (((t - sh.t0) * 0.1 + k * 0.25) % 1)), 880 - k * 26, 0.8, t, { kind: 'tbd', load: 'torpedo' }) } }); post(c, cam, { rays: 0.1 }); word(c, 'men in old planes', 150, prog(t, sh.t0 + 0.2, sh.t0 + 0.6)) }
    else if (sh.name === 'pilot') { const cam = { x: 1000, y: 600, z: 1.1 }; layer(c, cam, 0.05, c => sky(c, '#3a6a9a', '#a8c4dc', { horizon: 900, clouds: 0, sun: [1600, 140, 500] })); layer(c, cam, 0.4, c => { MWB.cloudDeck(c, 820) }); layer(c, cam, 1, c => plane(c, 1000, 560 + Math.sin(t) * 8, 1.6, t, { kind: 'sbd', load: 'bomb' })); post(c, cam, { rays: 0.16, rayX: 1100 }); word(c, 'one pilot who should have turned back', 150, prog(t, sh.t0 + 0.2, sh.t0 + 0.6), 48) }
    else { dark(c); paper(c, 960, 520, 1300, 520, [['McClusky’s decision', 60, '#3a2a1a', { italic: true }], ['“decided the fate', 60, '#3a2a1a', { italic: true }], ['of our carrier task force”', 60, '#3a2a1a', { italic: true }], ['', 16], ['Admiral Chester Nimitz', 32, '#5a4030']], { top: 110, rot: -0.01 }); post(c, { x: 960 }, { rays: false, vignette: 0.55 }) }
  }
})()
