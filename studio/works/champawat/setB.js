// setB.js: the places of The Champawat Tiger in Style B (painted). Kumaon hills, villages, the gorge, the ravine.
window.CWB = (function () {
  const { W, H, clamp, lerp, prog, keys, rng, ell, poly, smooth, shade, mixCol, vgrad, hgrad, rgrad, layer, ridge, fog, sky, post, foreground, tuft, person, crowd, beast, birds, tree, forest, snowPeaks, terraces, house, river, brush, paper, text } = PK
  PK.costume('corbettboy', { shirt: '#b8a882', pants: '#5a4a3a', hat: 'cap', hatCol: '#6a5a44', hair: '#5a3c22', height: 0.8, build: 0.85 })
  PK.costume('tahsildar', { skin: '#a8725a', shirt: '#ece4d0', pants: '#ece4d0', coat: '#4a3a2e', boot: '#21180f', hat: 'turban', hatCol: '#f0ead8', moustache: '#2a2018', hair: '#2a2018' })
  PK.costume('girl', { skin: '#a8725a', shirt: '#b5442e', skirt: '#8a3424', boot: '#6b4a32', hat: 'veil', hatCol: '#d8843a', hair: '#1d140d', build: 0.85, height: 0.86 })

  const SKY = {
    day: ['#93aac2', '#e8dcc4', { sun: [1560, 170, 520] }], dusk: ['#6f7f94', '#f0c28e', { sun: [420, 260, 620] }],
    noon: ['#8fa6be', '#efe4cc', { sun: [980, 60, 700, '255,240,200'] }], night: ['#0c1222', '#24324a', { moon: [1460, 180], stars: true }],
    dawn: ['#a99ab8', '#f2d2b0', { sun: [300, 520, 600, '255,210,170'] }]
  }
  // the hills behind everything: sky, snow peaks, far ridges in blue haze, nearer forested ridge
  function hills(c, cam, t, o = {}) {
    const tod = o.tod || 'day', [a, b, so] = SKY[tod], night = tod === 'night'
    layer(c, cam, 0.06, c => sky(c, a, b, Object.assign({ horizon: 700, clouds: o.clouds ?? 4 }, so)))
    if (o.peaks !== false) layer(c, cam, 0.12, c => { snowPeaks(c, 520 + (o.dy || 0), { h: 190, top: night ? '#3a4660' : '#c6cfda', bot: night ? '#202a40' : '#8796a8', seed: o.seed || 2 }); if (!night) fog(c, 560 + (o.dy || 0), 160, '230,226,220', 0.35) })
    layer(c, cam, 0.22, c => { ridge(c, 4 + (o.seed || 0), 560 + (o.dy || 0), 120, 150, night ? '#26324a' : '#7d8ea3', night ? '#1a2234' : '#9aa7b6'); if (!night) fog(c, 640 + (o.dy || 0), 120, '236,222,200', 0.5) })
    layer(c, cam, 0.4, c => { ridge(c, 8 + (o.seed || 0), 650 + (o.dy || 0), 90, 110, night ? '#1a2a2a' : '#4d6460', night ? '#121c1c' : '#3e5a55'); forest(c, -700, 2700, 690 + (o.dy || 0), 120, { fade: night ? 0.55 : 0.32, hazeCol: night ? '#1a2234' : '#a9b5b5', rows: 1, seed: 3 }); if (!night) fog(c, 740 + (o.dy || 0), 120, '226,214,190', 0.45) })
  }
  // a hillside village: terraces, stone houses, a path; lit windows at night
  function village(c, cam, t, o = {}) {
    const night = o.tod === 'night', fade = night ? 0.25 : 0
    layer(c, cam, 0.7, c => {
      ridge(c, 21, 760, 70, 160, night ? '#2a2e22' : '#6f7a46', night ? '#1a1e16' : '#4a5a32', { depth: 400 })
      terraces(c, -300, 800, 1300, 7, { col: night ? '#3a4228' : '#8a9a52', step: 40, shift: 30, shrink: 40 })
      terraces(c, 1100, 760, 1200, 8, { col: night ? '#3a4228' : '#7f9050', step: 38, shift: -24, shrink: 30 })
      const hs = o.houses || [[300, 800, 150, 100], [560, 780, 130, 90], [1240, 770, 140, 96], [1500, 800, 160, 104], [820, 820, 120, 84]]
      hs.forEach(([x, y, w, h], i) => house(c, x, y, w, h, { lit: night && (o.litAll || i % 2 === 0), col: night ? '#5a5248' : '#b5a48a', roof: night ? '#2a2a32' : '#5a5a62' }))
      forest(c, -500, 100, 830, 260, { seed: 5, fade, hazeCol: '#1a2234', t }); forest(c, 1750, 2500, 830, 260, { seed: 6, fade, hazeCol: '#1a2234', t })
      if (o.inner) o.inner(c)
    })
  }
  // the ground plane where people stand (y = gy): earth, a few stones, grass
  function ground(c, gy, o = {}) {
    const col = o.col || '#6a5a3e'
    c.fillStyle = vgrad(c, gy - 30, gy + 300, shade(col, 0.08), col, shade(col, -0.35)); c.fillRect(-3000, gy - 10, 12000, 1400)
    const r = rng(o.seed || 4), x1 = o.x1 || 2700; for (let k = 0; k < 18 * (x1 + 700) / 3400; k++) ell(c, r() * (x1 + 700) - 700, gy + 20 + r() * 160, 20 + r() * 50, 6 + r() * 8, 0, 'rgba(40,30,20,0.25)')
    if (o.grass !== false) for (let x = -700; x < x1; x += 50 + r() * 90) tuft(c, x, gy + 4 + r() * 50, 40 + r() * 50, r() > 0.5 ? '#4a5a32' : '#3a4a28', 0, 6, x | 0)
  }
  // ---- the Champa gorge: the steep ridge on the left with the line of beaters along its crest, the floor below
  const CREST = x => 300 + (x + 300) * 0.16 + Math.sin(x * 0.006) * 24
  function gorge(c, cam, t, o = {}) {
    hills(c, cam, t, { tod: 'noon', dy: -40 })
    layer(c, cam, 0.75, c => {   // the far (right) side of the gorge, forest
      ridge(c, 30, 640, 60, 180, '#4a5a3a', '#344228', { depth: 500 })
      forest(c, 1000, 2600, 700, 220, { seed: 9, fade: 0.2, hazeCol: '#a9b5a0' })
    })
    layer(c, cam, 1, c => {
      // the ridge slope on the left
      const pts = [[-900, 1400]]; for (let x = -900; x <= 1150; x += 50) pts.push([x, CREST(x)]); pts.push([1150, CREST(1150)], [1480, 900], [1480, 1400])
      c.fillStyle = hgrad(c, -400, 1500, '#6a5a3a', '#5a4a30', '#3a301e'); poly(c, pts); c.fill()
      c.save(); poly(c, pts); c.clip(); const r = rng(8)
      c.fillStyle = vgrad(c, 300, 900, 'rgba(255,220,170,0.16)', 'rgba(0,0,0,0)', 'rgba(0,0,0,0.25)'); c.fillRect(-900, 200, 2400, 800)
      c.strokeStyle = 'rgba(40,30,18,0.35)'; c.lineWidth = 3
      for (let k = 0; k < 9; k++) { const y0 = 420 + k * 56; c.beginPath(); c.moveTo(-900, y0 + 80); c.bezierCurveTo(-300, y0 + 20, 400, y0 + 90, 1200, y0 + 40); c.stroke() }
      for (let k = 0; k < 30; k++) { const x = r() * 2000 - 800, y = CREST(x) + 50 + r() * 560, w = 16 + r() * 40; ell(c, x, y, w, w * 0.55, 0, 'rgba(120,110,96,0.8)'); ell(c, x - w * 0.25, y - w * 0.2, w * 0.5, w * 0.22, 0, 'rgba(255,240,220,0.18)') }
      for (let k = 0; k < 40; k++) { const x = r() * 2200 - 800, y = CREST(x) + 60 + r() * 600; tuft(c, x, y, 40 + r() * 40, '#3a4a28', 0, 5, k) }
      for (let k = 0; k < 14; k++) { const x = r() * 1800 - 700; tree(c, x, CREST(x) + 140 + r() * 400, 160 + r() * 80, 'oak', { seed: k % 3 }) }
      c.restore()
      // the beaters along the crest
      if (o.beaters !== false) {
        const n = o.n || 46, walk = o.walk || 0
        for (let k = 0; k < n; k++) { const x = -800 + k * (1950 / n) + walk * 120, y = CREST(x) + walk * 140, hit = Math.sin(t * 7 + k * 1.3)
          person(c, x, y + 4, 0.26, { cos: ['villager', 'villager2', 'villager3'][k % 3], pose: k % 3 === 0 ? { name: 'drum', t: t + k * 0.3, bpm: 140 } : k % 3 === 1 ? { name: 'shout' } : { name: 'cheer', k: 0.6 + hit * 0.4, t: t + k }, face: { mouth: 'shout' }, fade: 0.2 }) }
      }
      // the gorge floor and the river
      ground(c, 900, { col: '#7a6a4a', seed: 12 })
      river(c, [[-900, 1010], [300, 980], [900, 1000], [1600, 970], [2800, 990]], 46, t, { col: '#7f98a2', bank: '#5a4a34' })
      for (const [x, y, r2] of [[160, 930, 46], [700, 920, 34], [1880, 935, 58], [2200, 925, 40]]) { ell(c, x, y, r2 * 1.4, r2 * 0.8, 0, '#8a8478'); ell(c, x - r2 * 0.3, y - r2 * 0.3, r2 * 0.6, r2 * 0.3, 0, 'rgba(255,240,220,0.25)') }
      if (o.brush !== false) brush(c, 1350, 905, 520, 170, t, { rustle: o.rustle || 0, seed: 40 })
      if (o.inner) o.inner(c)
    })
  }
  // ---- the ravine at Phungar (the moment from the style sample): bank with an overhang, tigress on the lip
  const R = { GY: 930, LIPY: 500, LX: 1110 }
  function ravine(c, cam, t, o = {}) {
    hills(c, cam, t, { tod: o.tod || 'dusk', dy: 20 })
    layer(c, cam, 1, c => {
      poly(c, [[-700, 700], [-100, 720], [300, 780], [560, 840], [700, 1500], [-700, 1500]], vgrad(c, 700, 1000, '#5b4836', '#4a3a2c'))
      poly(c, [[-700, R.GY - 20], [400, R.GY - 30], [1300, R.GY - 10], [2600, R.GY], [2600, 1600], [-700, 1600]], vgrad(c, R.GY - 40, 1150, '#5a4632', '#3b2d20'))
      const r = rng(21); for (let x = -400; x < 1000; x += 60 + r() * 90) tuft(c, x, R.GY + 6 + r() * 30, 70 + r() * 60, '#33452a', Math.sin(t * 1.3 + x) * 0.15, 7, x | 0)
      const BANK = [[1150, 1300], [1165, 1000], [1185, 880], [1190, 780], [1165, 660], [1130, 580], [R.LX, R.LIPY + 22], [R.LX + 12, R.LIPY + 4], [2600, R.LIPY - 14], [2600, 1300]]
      poly(c, BANK, hgrad(c, 1150, 1700, '#7b5d40', '#6b5139', '#3f2f21'))
      c.save(); poly(c, BANK); c.clip()
      c.strokeStyle = '#2f2217'; c.lineWidth = 3; c.globalAlpha = 0.5
      for (const [y, x0, x1] of [[590, 1150, 1700], [650, 1180, 1900], [700, 1215, 1560], [800, 1200, 2000], [900, 1185, 1700], [1010, 1170, 2100]]) { c.beginPath(); c.moveTo(x0, y); c.bezierCurveTo(x0 + 120, y - 14, x1 - 200, y + 16, x1, y + 2); c.stroke() }
      c.globalAlpha = 1; c.fillStyle = vgrad(c, R.LIPY, R.GY + 40, 'rgba(255,200,140,0.18)', 'rgba(10,8,6,0.45)'); c.fillRect(1100, R.LIPY - 40, 1600, 800)
      c.restore()
      if (o.inner) o.inner(c)
    })
  }
  function ravineLip(c, t, rustle = 0) {
    poly(c, [[R.LX - 6, R.LIPY + 12], [R.LX + 12, R.LIPY - 8], [2600, R.LIPY - 30], [2600, R.LIPY + 10], [1900, R.LIPY + 22], [1500, R.LIPY + 18]], '#3f5a33')
    const r = rng(33); for (let x = R.LX + 10; x < 2400; x += 40 + r() * 50) { const near = Math.exp(-Math.pow((x - 1230) / 160, 2)); tuft(c, x, R.LIPY + 8, 50 + r() * 40, r() > 0.5 ? '#3f5a33' : '#2c4224', Math.sin(t * 1.5 + x * 0.1) * 0.12 + rustle * near * Math.sin(t * 40 + x), 6, x | 0) }
  }
  // ---- small helpers
  const shotOf = (t, list) => { let s = list[0]; for (const L of list) if (t >= L[0]) s = L; const i = list.indexOf(s), t1 = (list[i + 1] || [1e9])[0]; return { name: s[1], t0: s[0], t1, u: clamp((t - s[0]) / (t1 - s[0])) } }
  function muzzle(c, t, m, hits) { for (const f of hits) { const tt = t - f; if (tt > 0 && tt < 0.12) { const a = 1 - tt / 0.12; c.save(); c.translate(...m); c.fillStyle = `rgba(255,236,160,${a})`; c.beginPath(); for (let k = 0; k < 14; k++) { const ang = k / 14 * Math.PI * 2, rr = k % 2 ? 26 : 80; c.lineTo(Math.cos(ang) * rr, Math.sin(ang) * rr) } c.closePath(); c.fill(); c.restore() } if (tt > 0 && tt < 3) for (let k = 0; k < 5; k++) ell(c, m[0] + tt * 24 + k * 8, m[1] - tt * 30 - k * 6, 5 + tt * 14 + k * 3, 5 + tt * 14 + k * 3, 0, `rgba(210,206,196,${(1 - tt / 3) * 0.28})`) } }
  return { hills, village, ground, gorge, CREST, ravine, ravineLip, R, shotOf, muzzle, SKY }
})()
