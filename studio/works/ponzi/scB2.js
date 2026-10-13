// scB2.js: scenes 7-12 of the Ponzi story, Style B.
(function () {
  const { W, H, clamp, lerp, prog, keys, rng, ell, poly, shade, vgrad, hgrad, rgrad, layer, fog, sky, post, person, crowd, paper, map, pathLine, count, text, label, shake, flashes, tree, mixCol } = PK
  const { block, schoolStreet, car, office, desk, bills, cashPile, newspaper, coupon, stamp, steamship, mansion, pyramid, shotOf, LINE } = POB
  const SC = window.SCENES = window.SCENES || []
  const dark = c => { c.fillStyle = vgrad(c, 0, H, '#2e2a26', '#14110e'); c.fillRect(0, 0, W, H) }
  const word = (c, s, y, a, size = 54) => text(c, s, W / 2, y, size, '#f3e7d0', { italic: true, shadow: 16, alpha: a })
  const theLine = (c, t, o = {}) => { const n = o.n || 16; for (let k = n - 1; k >= 0; k--) person(c, (o.x0 ?? 300) + k * (o.gap || 105) - (o.step || 0), 880 + (k % 2) * 6, o.s || 0.6, { cos: LINE[k % LINE.length], f: -1, pose: o.pose ? o.pose(k) : { name: 'stand' }, face: { mood: o.mood || 'happy', mouth: o.mouth, talk: o.talk ? t + k : 0 } }) }

  // ---------- 7: the arithmetic
  SC[7] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'nothing'], [q('say 100 people') - 0.3, 'sum'], [q('the missing') - 0.3, 'missing'], [q('so to pay them') - 0.3, 'pyramid'], [q('a scheme like that') - 0.3, 'end']])
    dark(c)
    if (sh.name === 'nothing') {
      cashPile(c, 700, 760, 6, 1.2); text(c, '→', 960, 620, 120, '#f3e7d0', { shadow: 16 }); cashPile(c, 1260, 760, 9, 1.2)
      word(c, 'every dollar paid out came from a new investor', 220, prog(t, q('so every dollar'), q('so every dollar') + 0.4), 44)
      word(c, '+50% owed to each', 960, prog(t, q('fifty percent more'), q('fifty percent more') + 0.4), 50)
    } else if (sh.name === 'sum' || sh.name === 'missing') {
      const a = prog(t, q('he has 10000'), q('he has 10000') + 0.4), b = prog(t, q('he owes them'), q('he owes them') + 0.4), m = prog(t, q('the missing'), q('the missing') + 0.4)
      text(c, '100 people × $100', 960, 220, 64, '#f3e7d0', { weight: 800, shadow: 16 })
      text(c, 'he has', 560, 420, 40, '#f3e7d0', { italic: true, alpha: a }); text(c, '$10,000', 560, 520, 100, '#f3e7d0', { weight: 800, alpha: a, shadow: 16 })
      text(c, 'in 45 days he owes', 1360, 420, 40, '#f3e7d0', { italic: true, alpha: b }); text(c, '$15,000', 1360, 520, 100, '#c8483a', { weight: 800, alpha: b, shadow: 16 })
      text(c, 'missing: $5,000', 960, 760, 84, '#c8483a', { weight: 800, alpha: m, shadow: 18 }); text(c, 'from somebody new, who is owed 50% too', 960, 860, 40, '#f3e7d0', { italic: true, alpha: prog(t, q('and now he owes'), q('and now he owes') + 0.4) })
    } else if (sh.name === 'pyramid') {
      pyramid(c, W / 2, 180, 9, prog(t, sh.t0 + 0.2, sh.t1 - 0.5), { red: true })
      word(c, 'the hole got deeper every day', 960, prog(t, q('the hole'), q('the hole') + 0.4), 48)
    } else {
      pyramid(c, W / 2, 180, 9, 1, { red: true })
      c.fillStyle = 'rgba(20,17,14,0.6)'; c.fillRect(0, 0, W, H)
      word(c, 'It ends when you run out of people.', 540, prog(t, q('it ends when'), q('it ends when') + 0.4), 64)
    }
    post(c, { x: 960 }, { rays: false, vignette: 0.55 })
  }

  // ---------- 8: the Boston Post, Barron, the run, coffee and doughnuts
  SC[8] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'post'], [q('two days later') - 0.3, 'questions'], [q('a financial writer') - 0.3, 'barron'], [q('the crowd came back') - 0.3, 'run'], [q('and ponzi paid them') - 0.3, 'pays']])
    if (sh.name === 'post' || sh.name === 'questions') {
      dark(c)
      const head = sh.name === 'post' ? ['DOUBLES THE MONEY', 'WITHIN THREE MONTHS'] : ['QUESTIONS RAISED', 'ABOUT PONZI’S PLAN']
      newspaper(c, W / 2, 560, keys(t, [[sh.t0, 0.95], [sh.t1, 1.02]]), head, { date: sh.name === 'post' ? 'JULY 24, 1920' : 'JULY 26, 1920', rot: -0.02 })
      post(c, { x: 960 }, { rays: false, vignette: 0.55 })
    } else if (sh.name === 'barron') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 700, z: 1.6 }], [sh.t1, { x: 980, y: 700, z: 1.75 }]])
      office(c, cam, t, { night: true, inner: c => { person(c, 1110, 1010, 0.92, { cos: 'barron', pose: { name: 'sit', hands: 'table', write: true, t }, face: { look: -0.3, mood: 'stern' } }); desk(c, 960, 900, 560, { lamp: true }); for (let k = 0; k < 4; k++) coupon(c, 1200 + k * 60, 890, 0.22, { rot: (k - 1.5) * 0.2 }) } })
      post(c, cam, { rays: false, vignette: 0.65 })
      label(c, 'Clarence Barron', W / 2, 110, prog(t, q('clarence barron'), q('clarence barron') + 0.5))
    } else if (sh.name === 'run') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 640, z: 1.3 }], [sh.t1, { x: 1060, y: 660, z: 1.5 }]])
      schoolStreet(c, cam, t, { inner: c => theLine(c, t, { n: 22, x0: 380, gap: 85, s: 0.6, mood: 'angry', mouth: 'shout', pose: k => k % 3 ? { name: 'cheer', k: 0.8, t: t + k } : { name: 'point' } }) })
      post(c, cam, { rays: 0.06, grade: 'rgba(60,60,80,0.2)' })
      word(c, 'this time, they wanted their money', 150, prog(t, q('this time'), q('this time') + 0.4))
    } else {
      const cam = keys(t, [[sh.t0, { x: 900, y: 700, z: 1.7 }], [sh.t1, { x: 1000, y: 700, z: 1.85 }]])
      schoolStreet(c, cam, t, { inner: c => { theLine(c, t, { n: 10, x0: 1000, gap: 120, s: 0.72, mood: 'happy' }); person(c, 860, 900, 0.75, { cos: 'ponzi', pose: { name: 'hold', at: [60, -170] }, holdFn: c => { ell(c, 0, 0, 16, 20, 0, '#f2ece0'); ell(c, 0, -14, 14, 5, 0, '#3a2414'); ell(c, 40, 6, 18, 18, 0, '#c8964a'); ell(c, 40, 6, 6, 6, 0, '#3a2414') }, face: { mood: 'happy', mouth: 'smile' } }) } })
      post(c, cam, { rays: 0.12 })
      count(c, W / 2, 210, '$2,000,000', 96); word(c, 'in three days', 310, prog(t, q('in three days'), q('in three days') + 0.3), 44)
      word(c, 'coffee and doughnuts for the line', 980, prog(t, q('coffee and'), q('coffee and') + 0.4), 42)
    }
  }

  // ---------- 9: the fall
  SC[9] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'publicist'], [q('the headline said') - 0.3, 'insolvent'], [q('on august 11') - 0.3, 'mugshot'], [q('that afternoon') - 0.3, 'shut'], [q('within two days') - 0.3, 'arrest']])
    if (sh.name === 'publicist') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 700, z: 1.5 }], [sh.t1, { x: 980, y: 700, z: 1.65 }]])
      office(c, cam, t, { night: true, inner: c => { person(c, 960, 1010, 0.9, { cos: 'reporter', pose: { name: 'sit', hands: 'table', write: true, t }, face: { mood: 'alarm', look: -0.3 } }); desk(c, 820, 900, 560, { lamp: true }); for (let k = 0; k < 4; k++) paper(c, 980 + k * 50, 890, 110, 22, [], { rot: (k - 1.5) * 0.08 }) } })
      post(c, cam, { rays: false, vignette: 0.65 })
      word(c, 'his own publicist went through the books', 150, prog(t, sh.t0 + 0.3, sh.t0 + 0.9), 46)
    } else if (sh.name === 'insolvent' || sh.name === 'mugshot') {
      dark(c)
      if (sh.name === 'insolvent') newspaper(c, W / 2, 560, keys(t, [[sh.t0, 0.95], [sh.t1, 1.02]]), ['PONZI HOPELESSLY', 'INSOLVENT'], { date: 'AUGUST 2, 1920', rot: 0.01, headSize: 62 })
      else newspaper(c, W / 2, 560, keys(t, [[sh.t0, 0.95], [sh.t1, 1.02]]), ['PONZI WAS JAILED', 'IN MONTREAL'], { date: 'AUGUST 11, 1920', rot: -0.015, photo: true, photoFn: (c, x, y) => { c.fillStyle = '#8a847a'; c.fillRect(x - 150, y - 170, 300, 340); PK.person(c, x, y + 330, 1.0, { cos: 'ponzi', pose: { name: 'stand' }, face: { mood: 'stern' }, noShadow: true, fade: 0.25, hazeCol: '#8a847a' }) } })
      post(c, { x: 960 }, { rays: false, vignette: 0.55 })
      if (sh.name === 'insolvent') word(c, 'millions in the hole', 1010, prog(t, q('millions of dollars'), q('millions of dollars') + 0.4), 44)
    } else if (sh.name === 'shut') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 560, z: 1.15 }], [sh.t1, { x: 960, y: 600, z: 1.35 }]])
      layer(c, cam, 0.06, c => sky(c, '#6a7a8a', '#c8c0b0', { horizon: 600, clouds: 5 }))
      layer(c, cam, 1, c => { block(c, 360, 900, 1200, 760, { col: '#b8ae9c', sign: 'HANOVER TRUST COMPANY', signY: 90, signSize: 44 }); c.fillStyle = '#e8e2d6'; for (let k = 0; k < 6; k++) c.fillRect(420 + k * 210, 380, 50, 400); c.fillStyle = vgrad(c, 900, 1200, '#8a847a', '#4a4640'); c.fillRect(-900, 900, 3800, 600); paper(c, 960, 640, 260, 200, [['CLOSED', 48, '#8a2a1e', { weight: 800 }], ['by order of', 22], ['the Commonwealth', 22]], { top: 50 }); person(c, 700, 1000, 0.72, { cos: 'police', pose: { name: 'stand' }, face: { mood: 'stern' } }); person(c, 1220, 1000, 0.72, { cos: 'police', f: -1, pose: { name: 'stand' }, face: { mood: 'stern' } }) })
      post(c, cam, { rays: 0.06, grade: 'rgba(60,60,80,0.2)' })
    } else {
      const cam = keys(t, [[sh.t0, { x: 960, y: 700, z: 1.6 }], [sh.t1, { x: 960, y: 700, z: 1.8 }]])
      office(c, cam, t, { wall: '#4a4a4c', window: false, cabinets: [], inner: c => { person(c, 820, 1040, 0.92, { cos: 'ponzi', pose: { name: 'hold', at: [30, -140] }, holdFn: c => { c.strokeStyle = '#c8c8d0'; c.lineWidth = 5; ell(c, -14, 0, 14, 12, 0); c.stroke(); ell(c, 18, 0, 14, 12, 0); c.stroke() }, face: { mood: 'sad', look: -0.2 } }); person(c, 1120, 1040, 0.92, { cos: 'police', f: -1, pose: { name: 'stand' }, face: { mood: 'stern' } }) } })
      post(c, cam, { rays: false, vignette: 0.7 })
      count(c, W / 2, 220, '86 counts', 100); word(c, 'of mail fraud', 320, prog(t, q('mail fraud'), q('mail fraud') + 0.3), 44)
    }
  }

  // ---------- 10: the bill
  SC[10] = (c, t, q, S) => {
    dark(c)
    const sh = shotOf(t, [[S.vis, 'lost'], [q('six banks') - 0.3, 'banks'], [q('the people who trusted') - 0.3, 'cents'], [q('the whole thing') - 0.3, 'months']])
    if (sh.name === 'lost') { count(c, W / 2, 420, '$20 million', 150); word(c, 'more than $300 million today', 560, prog(t, q('in todays money'), q('in todays money') + 0.4), 50) }
    else if (sh.name === 'banks') { for (let k = 0; k < 6; k++) { const a = prog(t, sh.t0 + 0.2 + k * 0.25, sh.t0 + 0.6 + k * 0.25), x = 300 + k * 265; c.save(); c.translate(x, 700); c.rotate(a * (k % 2 ? 0.3 : -0.3)); block(c, -100, 0, 200, 300, { col: '#b8ae9c' }); c.restore() } word(c, 'six banks went under', 200, prog(t, sh.t0 + 0.2, sh.t0 + 0.6)) }
    else if (sh.name === 'cents') { count(c, W / 2, 420, '30¢', 220); word(c, 'back, on every dollar', 590, prog(t, q('on the dollar'), q('on the dollar') + 0.4), 50) }
    else {
      const k = prog(t, sh.t0 + 0.4, sh.t1 - 0.6)
      c.strokeStyle = '#f3e7d0'; c.lineWidth = 6; c.beginPath(); c.moveTo(300, 560); c.lineTo(300 + 1320 * k, 560); c.stroke()
      ;['Dec 1919', 'Feb', 'Apr', 'Jun', 'Aug 1920'].forEach((m, i) => { const x = 300 + i * 330; if (k * 4 >= i) { ell(c, x, 560, 12, 12, 0, i === 4 ? '#c8483a' : '#f3e7d0'); text(c, m, x, 620, 36, '#f3e7d0', { italic: true }) } })
      word(c, 'about eight months', 400, prog(t, q('about eight months'), q('about eight months') + 0.4), 60)
    }
    post(c, { x: 960 }, { rays: false, vignette: 0.55 })
  }

  // ---------- 11: the rest of his life
  SC[11] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'prison'], [q('in between') - 0.3, 'florida'], [q('in 1934') - 0.3, 'deport'], [q('his wife rose') - 0.3, 'rose'], [q('he died in 1949') - 0.3, 'rio']])
    if (sh.name === 'prison') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 640, z: 1.5 }], [sh.t1, { x: 980, y: 640, z: 1.6 }]])
      office(c, cam, t, { wall: '#5a5a58', window: false, cabinets: [], inner: c => { person(c, 960, 1010, 0.92, { cos: 'ponziP', pose: { name: 'sit', hands: 'head' }, face: { mood: 'sad' } }); c.fillStyle = '#1a1814'; for (let x = 500; x < 1460; x += 64) c.fillRect(x, 160, 16, 900); c.fillRect(460, 160, 1040, 20); c.fillRect(460, 620, 1040, 16) } })
      post(c, cam, { rays: false, vignette: 0.75, night: 0.15 })
      word(c, '“a common and notorious thief”', 150, prog(t, q('a common'), q('a common') + 0.4), 50)
    } else if (sh.name === 'florida') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 640, z: 1.25 }], [sh.t1, { x: 1000, y: 650, z: 1.4 }]])
      layer(c, cam, 0.06, c => sky(c, '#7aa8c8', '#f2e4c0', { horizon: 700, clouds: 5, sun: [1500, 200, 520] }))
      layer(c, cam, 0.6, c => { for (let x = -600; x < 2600; x += 180) tree(c, x, 760, 260, 'palm', { seed: 1, t }) })
      layer(c, cam, 1, c => { c.fillStyle = vgrad(c, 760, 1200, '#5a6a3a', '#3a4a2a'); c.fillRect(-900, 760, 3800, 600); c.fillStyle = 'rgba(90,120,100,0.6)'; for (let k = 0; k < 6; k++) ell(c, 200 + k * 320, 880 + (k % 2) * 40, 140, 22, 0); paper(c, 1300, 820, 200, 120, [['LOTS FOR SALE', 22, '#3a2a1a', { weight: 800 }], ['200% in 60 days', 20, '#8a2a1e']], { top: 40 }); c.fillStyle = '#4a3420'; c.fillRect(1296, 880, 8, 120); person(c, 900, 960, 0.75, { cos: 'ponzi', pose: { name: 'point' }, target: [1500, 800], face: { mood: 'happy', talk: t } }) })
      post(c, cam, { rays: 0.16 })
      label(c, 'Florida', W / 2, 110, prog(t, q('florida'), q('florida') + 0.5) * (1 - prog(t, sh.t1 - 0.6, sh.t1)))
    } else if (sh.name === 'deport') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 600, z: 1.15 }], [sh.t1, { x: 1100, y: 620, z: 1.3 }]])
      layer(c, cam, 0.06, c => sky(c, '#6a7a8a', '#d8d0c0', { horizon: 700, clouds: 6 }))
      layer(c, cam, 0.8, c => { c.fillStyle = vgrad(c, 700, 1000, '#5a6a78', '#2a3440'); c.fillRect(-1400, 700, 4800, 600); steamship(c, lerp(1100, 1500, prog(t, sh.t0, sh.t1)), 840, 0.9, t) })
      layer(c, cam, 1, c => { c.fillStyle = vgrad(c, 900, 1200, '#6a5a48', '#3a3024'); c.fillRect(-900, 900, 3800, 600); person(c, 600, 1010, 0.75, { cos: 'ponzi', f: 1, pose: { name: 'stand' }, face: { mood: 'sad' } }) })
      post(c, cam, { rays: 0.08 })
      label(c, 'Deported, 1934', W / 2, 110, prog(t, sh.t0 + 0.3, sh.t0 + 0.9))
    } else if (sh.name === 'rose') {
      const cam = keys(t, [[sh.t0, { x: 960, y: 680, z: 1.6 }], [sh.t1, { x: 960, y: 680, z: 1.75 }]])
      office(c, cam, t, { wall: '#6a5a4a', cabinets: [], inner: c => { const gone = t > q('three years later'); person(c, gone ? lerp(1100, 1700, prog(t, q('she divorced'), q('she divorced') + 1.5)) : 1100, 1040, 0.9, { cos: 'rose', f: gone ? 1 : -1, pose: gone ? { name: 'walk', d: t * 50 } : { name: 'stand' }, face: { mood: 'sad' } }); person(c, 820, 1040, 0.9, { cos: 'ponzi', pose: { name: 'stand' }, face: { mood: 'sad' } }) } })
      post(c, cam, { rays: false, vignette: 0.65 })
      label(c, 'Rose Ponzi', W / 2, 110, prog(t, q('his wife rose'), q('his wife rose') + 0.5) * (1 - prog(t, q('three years later') - 0.4, q('three years later'))))
    } else {
      const cam = keys(t, [[sh.t0, { x: 960, y: 680, z: 1.5 }], [sh.t1, { x: 960, y: 700, z: 1.75 }]])
      office(c, cam, t, { wall: '#c8c4b8', cabinets: [], winX: 1250, inner: c => { c.fillStyle = '#e8e4dc'; c.fillRect(560, 880, 620, 40); c.fillStyle = '#8a8a90'; c.fillRect(560, 920, 14, 120); c.fillRect(1166, 920, 14, 120); c.fillRect(560, 760, 14, 120); ell(c, 680, 860, 70, 26, 0, '#f2f0ea'); c.fillStyle = '#d8d4cc'; c.fillRect(700, 850, 420, 40); ell(c, 650, 846, 24, 22, 0, '#d4a07e') } })
      post(c, cam, { rays: 0.08, vignette: 0.6 })
      label(c, 'Rio de Janeiro, 1949', W / 2, 110, prog(t, sh.t0 + 0.3, sh.t0 + 0.9) * (1 - prog(t, q('he left') - 0.4, q('he left'))))
      count(c, W / 2, 230, t > q('he left') ? '$75' : '', 120); word(c, 'just enough to bury him', 340, prog(t, q('just enough'), q('just enough') + 0.4), 44)
    }
  }

  // ---------- 12: one question
  SC[12] = (c, t, q, S) => {
    const sh = shotOf(t, [[S.vis, 'montreal'], [q('he explained it') - 0.3, 'quote'], [q('so when somebody') - 0.3, 'question'], [q('subscribe') - 0.3, 'end']])
    if (sh.name === 'montreal' || sh.name === 'end') {
      const cam = keys(t, [[sh.t0, { x: 900, y: 600, z: 1.25 }], [sh.t1, { x: 1100, y: 600, z: 1.1 }]], 'l')
      schoolStreet(c, cam, t, { inner: c => theLine(c, t, { n: 20, x0: 380, gap: 95, step: (t * 4) % 95, s: 0.58 }) })
      post(c, cam, { rays: 0.14, rayX: 900, grade: sh.name === 'end' ? 'rgba(200,120,80,0.15)' : null })
      if (sh.name === 'end') { const a = prog(t, sh.t0 + 0.3, sh.t0 + 1); text(c, 'Subscribe', W / 2, 330, 96, '#f3e7d0', { weight: 800, alpha: a, shadow: 24 }); text(c, 'animal facts  ·  great battles  ·  financial collapses', W / 2, 430, 40, '#f3e7d0', { italic: true, alpha: prog(t, q('everything from'), q('everything from') + 0.6), shadow: 14 }) }
      else word(c, 'it has carried his name for a hundred years', 150, prog(t, q('but it has carried'), q('but it has carried') + 0.4), 46)
    } else if (sh.name === 'quote') {
      dark(c)
      paper(c, 960, 520, 1300, 560, [['“My business was simple.', 62, '#3a2a1a', { italic: true }], ['It was the old game of', 62, '#3a2a1a', { italic: true }], ['robbing Peter to pay Paul.”', 62, '#3a2a1a', { italic: true }], ['', 20], ['Charles Ponzi', 34, '#5a4030']], { top: 120, rot: -0.01 })
      post(c, { x: 960 }, { rays: false, vignette: 0.55 })
    } else {
      dark(c)
      word(c, '50% in 45 days?', 340, prog(t, q('50 in 45'), q('50 in 45') + 0.4), 70)
      text(c, 'Where is the money coming from?', W / 2, 560, 80, '#f3e7d0', { weight: 800, shadow: 22, alpha: prog(t, q('where is the money'), q('where is the money') + 0.5) })
      post(c, { x: 960 }, { rays: false, vignette: 0.55 })
    }
  }
})()
