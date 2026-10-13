// sample.js: one moment from the Champawat film (the ravine at Phungar) drawn in two candidate styles.
// A = bright cartoon (thick outlines, big heads, flat colour, layered depth)
// B = painted storybook (realistic proportions, light and shadow, haze, depth of field)
(function () {
  const ST = window.STYLE || 'A', A = ST === 'A'
  const cv = document.getElementById('cv'), ctx = cv.getContext('2d'), W = 1920, H = 1080
  const T0 = 283.0, DUR = 16.4
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v))
  const lerp = (a, b, k) => a + (b - a) * k
  const io = p => p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2
  const prog = (t, a, b, e) => { const p = clamp((t - a) / (b - a)); return e ? io(p) : p }
  const keys = (t, ks) => { if (t <= ks[0][0]) return ks[0][1]; for (let i = 0; i < ks.length - 1; i++) { const [ta, va] = ks[i], [tb, vb] = ks[i + 1]; if (t <= tb) return lerp(va, vb, io((t - ta) / (tb - ta))) } return ks[ks.length - 1][1] }
  const rng = s => () => { s |= 0; s = s + 0x6D2B79F5 | 0; let t = Math.imul(s ^ s >>> 15, 1 | s); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296 }

  // ---- narration words (film time) -> captions
  const WORDS = [[283.25,'And'],[283.4,'as'],[283.4,'he'],[283.55,'knelt'],[283.85,'there,'],[284.15,'he'],[284.48,'had'],[284.68,'the'],[284.88,'feeling'],[285.28,'he'],[285.43,'was'],[285.63,'being'],[285.93,'watched.'],
    [287.26,'A'],[287.36,'little'],[287.7,'earth'],[288.0,'trickled'],[288.43,'down'],[288.68,'the'],[288.87,'bank'],[289.12,'above'],[289.41,'his'],[289.6,'head.'],
    [290.87,'She'],[291.07,'was'],[291.27,'right'],[291.58,'there.'],[291.88,'Above'],[292.19,'him.'],[292.88,'Close'],[293.18,'enough'],[293.54,'to'],[293.69,'touch.'],
    [294.54,'He'],[294.71,'swung'],[295.06,'his'],[295.28,'rifle'],[295.62,'up'],[295.79,'and'],[296.02,'fired'],[296.36,'twice.'],[296.7,'She'],[296.93,'disappeared'],[298.09,'into'],[298.38,'the'],[298.6,'brush.']]
  const CAPS = [[0, 4], [4, 13], [13, 23], [23, 27], [27, 29], [29, 33], [33, 41], [41, 46]].map(([a, b]) => ({ s: WORDS[a][0] - T0, e: (WORDS[b] ? WORDS[b][0] : 299.3) - T0 - 0.05, text: WORDS.slice(a, b).map(w => w[1]).join(' ') }))
  CAPS[0].s = 0

  // ---- palette per style
  const P = A ? {
    sky0: '#ffcf86', sky1: '#ff9a6a', far: '#9a86c4', far2: '#7c6aa9', mid: '#4f8a5b', mid2: '#3d7049', slope: '#8a5f3c', ground: '#9b7449', groundD: '#7d5a36',
    bank: '#a8774a', bankD: '#86592f', strata: '#6e4826', lip: '#5c9a45', lipD: '#3f7a32', fg: '#24452a', ink: '#1d130d',
    skin: '#f2b98f', skinD: '#d9946a', shirt: '#d8c08a', shirtD: '#b39a62', pants: '#6b4f35', pantsD: '#523b26', boot: '#3a2a1e', hat: '#8a6a45', hatD: '#6a4f31', band: '#3a2a1e',
    wood: '#8b4f27', steel: '#3b3b44', tig: '#f28a1e', tigD: '#d06a10', tigW: '#fff4e2', stripe: '#1d130d', eye: '#ffe55c'
  } : {
    sky0: '#f0c28e', sky1: '#6f7f94', far: '#7d8ea3', far2: '#62748a', mid: '#3e5a55', mid2: '#2e4743', slope: '#4a3a2c', ground: '#5a4632', groundD: '#3b2d20',
    bank: '#6b5139', bankD: '#3f2f21', strata: '#2f2217', lip: '#3f5a33', lipD: '#26391f', fg: '#0f160f', ink: '#16100b',
    skin: '#c99273', skinD: '#8f5f45', shirt: '#a8946a', shirtD: '#6e5f40', pants: '#4c3a2a', pantsD: '#2e2318', boot: '#21180f', hat: '#6e563b', hatD: '#43331f', band: '#21180f',
    wood: '#6a3c1e', steel: '#2a2a30', tig: '#d9741c', tigD: '#8c430c', tigW: '#efe2cc', stripe: '#140d08', eye: '#e9d24a'
  }
  const OL = A ? 5 : 0                      // outline width (world px)

  // ---- world layout
  const GY = 930, LIPY = 500, CX = 1060, LX = 1110           // ravine floor, top of bank, Corbett's x
  const TX = 1215, TY = LIPY - 6                 // tigress, on the lip
  const AIM = { x: TX - 10, y: TY - 70 }         // her head

  // ---- timing (local seconds)
  const q = { watched: 2.93, earth: 4.55, head: 6.6, there: 7.87, above: 8.88, close: 9.88, swung: 11.71, up: 12.62, fire1: 13.05, fire2: 13.4, gone: 13.95, brush: 15.6 }
  const SHOTS = [0, 4.2, 7.75, 11.45, 14.05, DUR]

  function camAt(t) {
    if (t < SHOTS[1]) return { x: keys(t, [[0, 1080], [4.2, 1090]]), y: keys(t, [[0, 700], [4.2, 700]]), z: keys(t, [[0, 1.35], [4.2, 1.55]]) }
    if (t < SHOTS[2]) return { x: keys(t, [[4.2, 1110], [6.6, 1120], [7.75, 1130]]), y: keys(t, [[4.2, 660], [6.6, 630], [7.75, 590]]), z: keys(t, [[4.2, 2.0], [7.75, 2.1]]) }
    if (t < SHOTS[3]) return { x: keys(t, [[7.75, 1130], [9.7, 1150], [11.45, 1180]]), y: keys(t, [[7.75, 640], [9.7, 600], [11.45, 540]]), z: keys(t, [[7.75, 1.55], [9.7, 1.65], [11.45, 1.95]]) }
    if (t < SHOTS[4]) return { x: 1120, y: 680, z: keys(t, [[11.45, 1.45], [14.05, 1.55]]) }
    return { x: keys(t, [[14.05, 1140], [DUR, 1160]]), y: keys(t, [[14.05, 660], [DUR, 640]]), z: keys(t, [[14.05, 1.6], [DUR, 1.7]]) }
  }
  function shake(t) { let a = 0; for (const f of [q.fire1, q.fire2]) if (t > f && t < f + 0.4) a += (1 - (t - f) / 0.4) * 14; return a ? [Math.sin(t * 91) * a, Math.cos(t * 77) * a] : [0, 0] }
  function layer(c, cam, f, fn) {
    c.save(); const z = 1 + (cam.z - 1) * f
    c.translate(W / 2 + cam.sx, H / 2 + cam.sy); c.scale(z, z); c.translate(-(960 + (cam.x - 960) * f), -(540 + (cam.y - 540) * f))
    fn(c); c.restore()
  }

  // ---- noise texture for the painted style
  let grain = null
  function makeGrain() { grain = document.createElement('canvas'); grain.width = grain.height = 256; const g = grain.getContext('2d'), im = g.createImageData(256, 256), r = rng(9); for (let i = 0; i < im.data.length; i += 4) { const v = r() * 255; im.data[i] = im.data[i + 1] = im.data[i + 2] = v; im.data[i + 3] = 22 } g.putImageData(im, 0, 0) }

  // ---- shape helpers
  function shape(c, pts, fill, opt = {}) {
    c.beginPath(); c.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) c.lineTo(pts[i][0], pts[i][1]); if (opt.close !== false) c.closePath()
    c.fillStyle = fill; c.fill(); if (OL && opt.ol !== false) { c.lineWidth = opt.lw || OL; c.strokeStyle = P.ink; c.lineJoin = 'round'; c.stroke() }
  }
  function ridge(seed, y0, amp, step, x0 = -600, x1 = 2600) { const r = rng(seed), pts = [[x0, 1400]]; let y = y0; for (let x = x0; x <= x1; x += step) { y = y0 + (r() - 0.5) * amp; pts.push([x, y]) } pts.push([x1, 1400]); return pts }
  function vgrad(c, y0, y1, a, b) { const g = c.createLinearGradient(0, y0, 0, y1); g.addColorStop(0, a); g.addColorStop(1, b); return g }
  function pine(c, x, y, h, col) {
    c.fillStyle = col; c.beginPath(); c.moveTo(x, y - h)
    for (let k = 0; k < 4; k++) { const yy = y - h + (k + 1) * h / 4, w = h * (0.16 + k * 0.07); c.lineTo(x + w, yy); c.lineTo(x + w * 0.45, yy - h * 0.02) }
    c.lineTo(x + h * 0.04, y); c.lineTo(x - h * 0.04, y)
    for (let k = 3; k >= 0; k--) { const yy = y - h + (k + 1) * h / 4, w = h * (0.16 + k * 0.07); c.lineTo(x - w * 0.45, yy - h * 0.02); c.lineTo(x - w, yy) }
    c.closePath(); c.fill(); if (OL) { c.lineWidth = 3; c.strokeStyle = P.ink; c.stroke() }
  }
  function tuft(c, x, y, h, col, sway, n = 6, seed = 1) {
    const r = rng(seed); c.fillStyle = col
    for (let k = 0; k < n; k++) { const bx = x + (k - n / 2) * h * 0.13, hh = h * (0.6 + r() * 0.5), lean = (r() - 0.5) * h * 0.5 + sway * h * 0.4
      c.beginPath(); c.moveTo(bx - h * 0.05, y); c.quadraticCurveTo(bx + lean * 0.3, y - hh * 0.6, bx + lean, y - hh); c.quadraticCurveTo(bx + lean * 0.3 + h * 0.04, y - hh * 0.5, bx + h * 0.06, y); c.closePath(); c.fill()
      if (OL) { c.lineWidth = 2.5; c.strokeStyle = P.ink; c.stroke() } }
  }

  // ---- background layers
  function sky(c) {
    c.fillStyle = vgrad(c, -200, 900, P.sky0, P.sky1); c.fillRect(-1000, -800, 4000, 2600)
    if (A) { c.fillStyle = '#fff1b8'; c.beginPath(); c.arc(520, 210, 70, 0, 7); c.fill(); c.globalAlpha = 0.35; c.beginPath(); c.arc(520, 210, 110, 0, 7); c.fill(); c.globalAlpha = 1 }
    else { const g = c.createRadialGradient(480, 240, 10, 480, 240, 520); g.addColorStop(0, 'rgba(255,226,170,0.95)'); g.addColorStop(0.15, 'rgba(255,205,140,0.5)'); g.addColorStop(1, 'rgba(255,190,120,0)'); c.fillStyle = g; c.fillRect(-100, -300, 1200, 1100) }
  }
  function far(c) {
    shape(c, ridge(3, 430, 120, 140), A ? P.far : vgrad(c, 300, 700, P.far, '#9aa7b6'), { lw: 4 })
    shape(c, ridge(5, 540, 90, 110), A ? P.far2 : vgrad(c, 420, 800, P.far2, '#8392a3'), { lw: 4 })
    if (!A) { c.fillStyle = vgrad(c, 480, 700, 'rgba(236,214,186,0)', 'rgba(236,214,186,0.55)'); c.fillRect(-1000, 400, 4000, 500) }
  }
  function mid(c) {
    shape(c, ridge(8, 650, 60, 90), A ? P.mid : vgrad(c, 560, 900, P.mid, '#4d6460'), { lw: 4 })
    const r = rng(12); for (let x = -500; x < 2500; x += 46 + r() * 50) pine(c, x, 650 + (r() - 0.5) * 40, 110 + r() * 90, A ? P.mid2 : 'rgba(40,62,58,0.95)')
    if (!A) { c.fillStyle = vgrad(c, 600, 840, 'rgba(220,200,170,0)', 'rgba(220,200,170,0.45)'); c.fillRect(-1000, 560, 4000, 400) }
  }
  function ravine(c, t) {
    // far (left) wall of the ravine
    shape(c, [[-700, 700], [-100, 720], [300, 780], [560, 840], [700, 1500], [-700, 1500]], A ? P.slope : vgrad(c, 700, 1000, '#5b4836', P.slope), { lw: 4 })
    // floor
    shape(c, [[-700, GY - 20], [400, GY - 30], [1300, GY - 10], [2600, GY], [2600, 1600], [-700, 1600]], A ? P.ground : vgrad(c, GY - 40, 1150, P.ground, P.groundD), { lw: 4 })
    if (A) { c.fillStyle = P.groundD; for (const [x, w] of [[300, 70], [620, 40], [1060, 60], [1500, 90]]) { c.beginPath(); c.ellipse(x, GY + 40, w, 9, 0, 0, 7); c.fill() } }
    // floor brush
    const r = rng(21); for (let x = -400; x < 1150; x += 60 + r() * 90) if (Math.abs(x - CX) > 260) tuft(c, x, GY + 6 + r() * 30, 70 + r() * 60, A ? P.lipD : '#33452a', Math.sin(t * 1.3 + x) * 0.15, 7, x | 0)
  }
  const BANK = [[1150, 1300], [1165, 1000], [1185, 880], [1190, 780], [1165, 660], [1130, 580], [LX, LIPY + 22], [LX + 12, LIPY + 4], [2600, LIPY - 14], [2600, 1300]]
  function bank(c) {
    shape(c, BANK, A ? P.bank : (() => { const g = c.createLinearGradient(1150, 0, 1700, 0); g.addColorStop(0, '#7b5d40'); g.addColorStop(0.12, P.bank); g.addColorStop(1, P.bankD); return g })(), { lw: 5 })
    // strata and roots
    c.strokeStyle = P.strata; c.lineWidth = A ? 4 : 3; c.lineCap = 'round'
    for (const [y, x0, x1] of [[590, 1150, 1700], [650, 1180, 1900], [700, 1215, 1560], [800, 1200, 2000], [900, 1185, 1700], [1010, 1170, 2100]]) { c.beginPath(); c.moveTo(x0, y); c.bezierCurveTo(x0 + 120, y - 14, x1 - 200, y + 16, x1, y + 2); c.globalAlpha = A ? 0.8 : 0.5; c.stroke() }
    c.globalAlpha = 1; c.lineWidth = A ? 5 : 3
    for (const [x, y, l] of [[1300, LIPY + 6, 90], [1460, LIPY + 2, 70], [1620, LIPY, 120]]) { c.beginPath(); c.moveTo(x, y); c.bezierCurveTo(x - 10, y + l * 0.4, x + 25, y + l * 0.7, x + 5, y + l); c.stroke() }
    if (!A) { // light from the low sun on the bank's edge, deep shade at its foot
      c.save(); c.beginPath(); c.moveTo(BANK[0][0], BANK[0][1]); for (const p of BANK) c.lineTo(p[0], p[1]); c.closePath(); c.clip()
      c.fillStyle = vgrad(c, LIPY, GY + 40, 'rgba(255,200,140,0.18)', 'rgba(10,8,6,0.45)'); c.fillRect(1100, LIPY - 40, 1600, 800)
      c.globalCompositeOperation = 'overlay'; c.fillStyle = c.createPattern(grain, 'repeat'); c.fillRect(1100, 300, 1600, 1000); c.restore()
    }
  }
  function lipGrass(c, t, rustle) {
    shape(c, [[LX - 6, LIPY + 12], [LX + 12, LIPY - 8], [2600, LIPY - 30], [2600, LIPY + 10], [1900, LIPY + 22], [1500, LIPY + 18]], A ? P.lip : P.lip, { lw: 4 })
    const r = rng(33); for (let x = LX + 10; x < 2400; x += 40 + r() * 50) { const near = Math.exp(-Math.pow((x - TX) / 160, 2)); tuft(c, x, LIPY + 8, 60 + r() * 50, A ? (r() > 0.5 ? P.lip : P.lipD) : (r() > 0.5 ? '#3f5a33' : '#2c4224'), Math.sin(t * 1.5 + x * 0.1) * 0.12 + rustle * near * Math.sin(t * 40 + x), 6, x | 0) }
  }
  function foreground(c, t) {
    const r = rng(44)
    for (let x = -700; x < 2700; x += 120 + r() * 160) {
      const h = 260 + r() * 220; tuft(c, x, 1240, h, A ? P.fg : P.fg, Math.sin(t * 0.9 + x) * 0.08, 6, x | 0)
    }
  }

  // ---- 2-bone IK: returns the middle joint; bend picks which side
  function ik(a, b, L1, L2, pick) {
    let dx = b[0] - a[0], dy = b[1] - a[1], d = Math.hypot(dx, dy); d = Math.min(d, L1 + L2 - 0.01); d = Math.max(d, Math.abs(L1 - L2) + 0.01)
    const base = Math.atan2(dy, dx), off = Math.acos(clamp((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d), -1, 1))
    const j1 = [a[0] + L1 * Math.cos(base + off), a[1] + L1 * Math.sin(base + off)], j2 = [a[0] + L1 * Math.cos(base - off), a[1] + L1 * Math.sin(base - off)]
    return pick(j1, j2) ? j1 : j2
  }
  function limb(c, pts, w, col, dark) {
    c.lineCap = 'round'; c.lineJoin = 'round'
    const path = () => { c.beginPath(); c.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) c.lineTo(pts[i][0], pts[i][1]) }
    if (OL) { path(); c.lineWidth = w + OL * 2; c.strokeStyle = P.ink; c.stroke() }
    path(); c.lineWidth = w; c.strokeStyle = col; c.stroke()
    if (!A) { c.save(); c.translate(-w * 0.18, -w * 0.12); path(); c.lineWidth = w * 0.3; c.strokeStyle = 'rgba(255,235,200,0.22)'; c.stroke(); c.restore() }
  }

  // ---- Jim Corbett: kneeling, facing right. o.aim 0..1 swings the rifle from his knee up to her head.
  const PR = A ? { hr: 44, tor: 92, th: 56, sh: 54, ua: 44, fa: 42, rl: 150, tw: 64, lw: 26, aw: 20 } : { hr: 23, tor: 118, th: 86, sh: 84, ua: 64, fa: 60, rl: 175, tw: 72, lw: 22, aw: 17 }
  function corbett(c, x, s, o) {
    const p = PR, k = o.aim
    c.save(); c.translate(x, GY + 6); c.scale(s, s)
    // shadow
    c.fillStyle = 'rgba(0,0,0,0.28)'; c.beginPath(); c.ellipse(-10, 0, p.th * 1.7, 10, 0, 0, 7); c.fill()
    const hip = [-0.05 * p.th, -p.th * 0.97]
    const bFoot = [hip[0] - 0.12 * p.th - p.sh, -6], bKnee = ik(hip, bFoot, p.th, p.sh, (a, b) => a[1] > b[1])
    const fFoot = [hip[0] + p.th * 0.95, -4], fKnee = ik(hip, fFoot, p.th, p.sh, (a, b) => a[1] < b[1])
    const lean = lerp(0.14, -0.06, k) + o.flinch * 0.05
    const neck = [hip[0] + Math.sin(lean) * p.tor, hip[1] - Math.cos(lean) * p.tor]
    const sh = [lerp(hip[0], neck[0], 0.86), lerp(hip[1], neck[1], 0.86) + 4]
    // rifle: from resting across his knee to the shoulder, pointed at her
    const tgt = [(AIM.x - x) / s, (AIM.y - GY - 6) / s]
    const aimA = Math.atan2(tgt[1] - sh[1], tgt[0] - sh[0]), restA = -0.32
    const ang = lerp(restA, aimA, k) + o.kick * -0.12
    const butt = [lerp(hip[0] - p.rl * 0.12, sh[0] - 4, k) - o.kick * 8 * Math.cos(ang), lerp(hip[1] - 2, sh[1] + 2, k) - o.kick * 8 * Math.sin(ang)]
    const dir = [Math.cos(ang), Math.sin(ang)], along = d => [butt[0] + dir[0] * d, butt[1] + dir[1] * d]
    const rearH = along(p.rl * 0.24), frontH = along(p.rl * 0.56), muzzle = along(p.rl)
    const shFar = [sh[0] + 6, sh[1] - 3]
    const fElb = ik(shFar, frontH, p.ua, p.fa, (a, b) => a[1] > b[1]), rElb = ik(sh, rearH, p.ua, p.fa, (a, b) => a[1] > b[1])
    // far leg, far arm
    limb(c, [hip, bKnee, bFoot], p.lw, P.pantsD, P.ink); boot(c, bFoot, -1, p)
    limb(c, [shFar, fElb, frontH], p.aw, P.shirtD, P.ink); hand(c, frontH, p)
    // near leg
    limb(c, [hip, fKnee, fFoot], p.lw, P.pants, P.pantsD); boot(c, fFoot, 1, p)
    // torso
    const ux = (neck[0] - hip[0]) / p.tor, uy = (neck[1] - hip[1]) / p.tor, nx = -uy, ny = ux
    const tw = p.tw
    const torso = [[hip[0] - nx * tw * 0.42, hip[1] - ny * tw * 0.42], [hip[0] + nx * tw * 0.42, hip[1] + ny * tw * 0.42], [neck[0] + nx * tw * 0.5, neck[1] + ny * tw * 0.5], [neck[0] - nx * tw * 0.5, neck[1] - ny * tw * 0.5]]
    c.beginPath(); c.moveTo(...torso[0]); c.lineTo(...torso[1]); c.quadraticCurveTo(hip[0] + nx * tw * 0.62 + ux * 40, hip[1] + ny * tw * 0.62 + uy * 40, ...torso[2]); c.quadraticCurveTo(neck[0] + ux * 10, neck[1] + uy * 10, ...torso[3]); c.quadraticCurveTo(hip[0] - nx * tw * 0.6 + ux * 40, hip[1] - ny * tw * 0.6 + uy * 40, ...torso[0]); c.closePath()
    if (A) { c.fillStyle = P.shirt; c.fill(); c.lineWidth = OL; c.strokeStyle = P.ink; c.stroke() }
    else { const g = c.createLinearGradient(hip[0] - 40, 0, hip[0] + 40, 0); g.addColorStop(0, '#c5b386'); g.addColorStop(0.5, P.shirt); g.addColorStop(1, P.shirtD); c.fillStyle = g; c.fill() }
    // belt and pocket
    c.strokeStyle = A ? P.band : '#2a1f14'; c.lineWidth = A ? 9 : 7; c.beginPath(); c.moveTo(hip[0] - nx * tw * 0.45 + ux * 12, hip[1] - ny * tw * 0.45 + uy * 12); c.lineTo(hip[0] + nx * tw * 0.45 + ux * 12, hip[1] + ny * tw * 0.45 + uy * 12); c.stroke()
    // head
    head(c, neck, lean, o, p)
    // rifle
    c.lineCap = 'round'
    if (OL) { c.strokeStyle = P.ink; c.lineWidth = 15; c.beginPath(); c.moveTo(...butt); c.lineTo(...muzzle); c.stroke() }
    c.strokeStyle = P.wood; c.lineWidth = A ? 10 : 8; c.beginPath(); c.moveTo(...butt); c.lineTo(...along(p.rl * 0.62)); c.stroke()
    c.strokeStyle = P.steel; c.lineWidth = A ? 5 : 4; c.beginPath(); c.moveTo(...along(p.rl * 0.3)); c.lineTo(...muzzle); c.stroke()
    // near arm
    limb(c, [sh, rElb, rearH], p.aw, P.shirt, P.shirtD); hand(c, rearH, p)
    c.restore()
    return { muzzle: [x + muzzle[0] * s, GY + 6 + muzzle[1] * s], hat: [x + neck[0] * s, GY + 6 + (neck[1] - p.hr * 2.1) * s] }
  }
  function boot(c, f, side, p) { c.fillStyle = P.boot; c.beginPath(); c.ellipse(f[0] + side * 8, f[1] - 4, p.lw * 0.75, p.lw * 0.42, 0, 0, 7); c.fill(); if (OL) { c.lineWidth = OL; c.strokeStyle = P.ink; c.stroke() } }
  function hand(c, h, p) { c.fillStyle = P.skin; c.beginPath(); c.arc(h[0], h[1], p.aw * 0.62, 0, 7); c.fill(); if (OL) { c.lineWidth = OL * 0.8; c.strokeStyle = P.ink; c.stroke() } }
  function head(c, neck, lean, o, p) {
    const r = p.hr, look = o.look                      // look: 0 ahead .. 1 straight up at her
    const tilt = lean - look * 0.55
    c.save(); c.translate(neck[0], neck[1]); c.rotate(tilt)
    // neck
    c.fillStyle = P.skinD; c.fillRect(-r * 0.25, -r * 0.5, r * 0.5, r * 0.6)
    c.translate(0, -r * 0.95)
    if (A) {
      c.fillStyle = P.skin; c.beginPath(); c.ellipse(0, 0, r * 0.92, r, 0, 0, 7); c.fill(); c.lineWidth = OL; c.strokeStyle = P.ink; c.stroke()
      // ear, nose
      c.beginPath(); c.ellipse(-r * 0.45, r * 0.05, r * 0.16, r * 0.22, 0, 0, 7); c.fillStyle = P.skinD; c.fill(); c.stroke()
      c.beginPath(); c.ellipse(r * 0.86, r * 0.12, r * 0.2, r * 0.17, 0, 0, 7); c.fillStyle = P.skin; c.fill(); c.stroke()
      // eyes: big whites, pupils that move, brows that rise
      const wide = 1 + o.alarm * 0.35, px = 0.08 + o.dart * 0.18, py = -look * 0.18
      for (const [ex, sz] of [[r * 0.28, 1], [r * 0.62, 0.82]]) {
        c.beginPath(); c.ellipse(ex, -r * 0.12, r * 0.17 * sz, r * 0.24 * sz * wide, 0, 0, 7); c.fillStyle = '#fff'; c.fill(); c.lineWidth = 3; c.stroke()
        c.beginPath(); c.arc(ex + r * px * sz, -r * 0.12 + r * py, r * 0.085 * sz, 0, 7); c.fillStyle = P.ink; c.fill()
        c.lineWidth = 5; c.beginPath(); c.moveTo(ex - r * 0.16 * sz, -r * (0.42 + o.alarm * 0.12)); c.lineTo(ex + r * 0.16 * sz, -r * (0.44 + o.alarm * 0.08) + (1 - o.alarm) * r * 0.05); c.stroke()
      }
      // moustache, mouth
      c.fillStyle = '#4a3020'; c.beginPath(); c.ellipse(r * 0.6, r * 0.38, r * 0.3, r * 0.1, -0.1, 0, 7); c.fill(); c.lineWidth = 3; c.stroke()
      c.beginPath(); c.lineWidth = 4; if (o.alarm > 0.5) { c.ellipse(r * 0.55, r * 0.6, r * 0.07, r * 0.1, 0, 0, 7); c.fillStyle = '#3a1a14'; c.fill() } else { c.moveTo(r * 0.42, r * 0.6); c.lineTo(r * 0.66, r * 0.58); c.stroke() }
    } else {
      const g = c.createRadialGradient(r * 0.3, -r * 0.3, r * 0.1, 0, 0, r * 1.1); g.addColorStop(0, '#dba889'); g.addColorStop(0.6, P.skin); g.addColorStop(1, P.skinD)
      c.fillStyle = g; c.beginPath(); c.moveTo(-r * 0.8, -r * 0.3); c.quadraticCurveTo(-r * 0.7, -r * 1.05, r * 0.2, -r * 0.98); c.quadraticCurveTo(r * 0.9, -r * 0.8, r * 0.92, -r * 0.1); c.lineTo(r * 1.12, r * 0.2); c.lineTo(r * 0.92, r * 0.32); c.quadraticCurveTo(r * 0.95, r * 0.75, r * 0.55, r * 0.95); c.quadraticCurveTo(-r * 0.2, r * 1.05, -r * 0.6, r * 0.55); c.closePath(); c.fill()
      c.fillStyle = P.skinD; c.beginPath(); c.ellipse(-r * 0.35, r * 0.05, r * 0.14, r * 0.22, 0, 0, 7); c.fill()
      c.fillStyle = '#1b120c'; c.beginPath(); c.ellipse(r * 0.55 + o.dart * r * 0.06, -r * 0.12 - look * r * 0.06, r * 0.09, r * 0.1 * (1 + o.alarm * 0.4), 0, 0, 7); c.fill()
      c.fillStyle = 'rgba(255,255,255,0.8)'; c.beginPath(); c.arc(r * 0.58, -r * 0.16, r * 0.03, 0, 7); c.fill()
      c.strokeStyle = '#3a2618'; c.lineWidth = 2.5; c.beginPath(); c.moveTo(r * 0.38, -r * (0.33 + o.alarm * 0.08)); c.lineTo(r * 0.72, -r * (0.32 + o.alarm * 0.04)); c.stroke()
      c.fillStyle = '#3b2617'; c.beginPath(); c.ellipse(r * 0.72, r * 0.42, r * 0.3, r * 0.1, -0.15, 0, 7); c.fill()
      c.fillStyle = 'rgba(255,190,140,0.35)'; c.beginPath(); c.ellipse(r * 0.6, -r * 0.5, r * 0.25, r * 0.14, 0.3, 0, 7); c.fill()
    }
    // hat: crown and a wide brim
    const hy = A ? -r * 0.62 : -r * 0.7
    c.fillStyle = A ? P.hat : vgrad(c, hy - r * 0.9, hy, '#86694a', P.hat)
    c.beginPath(); c.moveTo(-r * 0.7, hy); c.quadraticCurveTo(-r * 0.75, hy - r * 0.95, 0, hy - r * 0.95); c.quadraticCurveTo(r * 0.75, hy - r * 0.95, r * 0.72, hy); c.closePath(); c.fill(); if (OL) { c.lineWidth = OL; c.strokeStyle = P.ink; c.stroke() }
    c.fillStyle = P.band; c.fillRect(-r * 0.71, hy - r * 0.22, r * 1.42, r * 0.2)
    c.fillStyle = A ? P.hatD : P.hatD; c.beginPath(); c.ellipse(r * 0.05, hy, r * 1.32, r * 0.2, 0, 0, 7); c.fill(); if (OL) { c.lineWidth = OL; c.stroke() }
    c.restore()
  }

  // ---- the tigress on the lip, looking down at him. o.retreat 0..1 pulls her back behind the edge.
  function tigress(c, t, o) {
    const s = A ? 1.0 : 1.0, sink = o.retreat * 260 + o.recoil * 26
    c.save()
    c.beginPath(); c.rect(1100, -500, 1600, LIPY + 4 + 500); c.clip()      // only what is above the lip shows
    c.translate(TX, TY + sink); c.scale(s, s)
    const breathe = Math.sin(t * 2.2) * 2
    // shoulders and back, going away from us up the slope
    c.fillStyle = A ? P.tig : vgrad(c, -140, 40, '#e48a32', P.tigD)
    c.beginPath(); c.ellipse(70, -40 + breathe, 150, 78, -0.12, 0, 7); c.fill(); if (OL) { c.lineWidth = OL; c.strokeStyle = P.ink; c.stroke() }
    c.save(); c.clip(); c.strokeStyle = P.stripe; c.lineCap = 'round'
    for (let k = 0; k < 7; k++) { const x = -20 + k * 34; c.lineWidth = A ? 12 : 9; c.beginPath(); c.moveTo(x, -120); c.quadraticCurveTo(x + 18, -70, x - 4, -30 + (k % 2) * 12); c.stroke() }
    c.restore()
    // head
    c.save(); c.translate(-36, -66 + breathe * 0.5); c.rotate(-0.12 - o.recoil * 0.25)
    const R = 66
    // ears
    for (const ex of [-44, 40]) { c.beginPath(); c.ellipse(ex, -R * 0.82, A ? 20 : 14, A ? 22 : 15, 0, 0, 7); c.fillStyle = A ? P.tig : P.tigD; c.fill(); if (OL) { c.lineWidth = OL; c.strokeStyle = P.ink; c.stroke() } c.beginPath(); c.ellipse(ex, -R * 0.8, A ? 10 : 6, A ? 12 : 7, 0, 0, 7); c.fillStyle = P.tigW; c.fill() }
    // cheek ruff + head
    c.beginPath(); c.moveTo(-R * 1.1, R * 0.05); c.lineTo(-R * 0.82, -R * 0.55); c.quadraticCurveTo(0, -R * 1.05, R * 0.82, -R * 0.55); c.lineTo(R * 1.1, R * 0.05); c.lineTo(R * 0.86, R * 0.42); c.quadraticCurveTo(0, R * 0.95, -R * 0.86, R * 0.42); c.closePath()
    c.fillStyle = A ? P.tig : (() => { const g = c.createRadialGradient(-10, -20, 6, 0, 0, R * 1.2); g.addColorStop(0, '#f09a3e'); g.addColorStop(1, P.tigD); return g })(); c.fill(); if (OL) { c.lineWidth = OL; c.strokeStyle = P.ink; c.stroke() }
    c.save(); c.clip()
    c.fillStyle = P.tigW; for (const sx of [-1, 1]) { c.beginPath(); c.moveTo(sx * R * 1.1, R * 0.05); c.lineTo(sx * R * 0.45, R * 0.0); c.quadraticCurveTo(sx * R * 0.4, R * 0.6, sx * R * 0.86, R * 0.42); c.closePath(); c.fill() }
    c.strokeStyle = P.stripe; c.lineCap = 'round'; c.lineWidth = A ? 7 : 5
    for (const [a, b, cc] of [[[-12, -R * 0.95], [-6, -R * 0.62], [-14, -R * 0.45]], [[12, -R * 0.95], [6, -R * 0.62], [14, -R * 0.45]], [[-32, -R * 0.8], [-24, -R * 0.62], [-34, -R * 0.5]], [[32, -R * 0.8], [24, -R * 0.62], [34, -R * 0.5]]]) { c.beginPath(); c.moveTo(...a); c.quadraticCurveTo(...b, ...cc); c.stroke() }
    for (const sx of [-1, 1]) for (let k = 0; k < 3; k++) { c.beginPath(); c.moveTo(sx * R * 1.1, -R * 0.1 + k * 16); c.lineTo(sx * R * 0.72, -R * 0.02 + k * 14); c.stroke() }
    c.restore()
    // muzzle, nose, mouth
    c.fillStyle = P.tigW; c.beginPath(); c.ellipse(-14, R * 0.32, 22, 18, 0, 0, 7); c.ellipse(14, R * 0.32, 22, 18, 0, 0, 7); c.fill(); if (OL) { c.lineWidth = 3; c.strokeStyle = P.ink; c.stroke() }
    c.fillStyle = A ? '#c4586a' : '#6b2f2f'; c.beginPath(); c.moveTo(-14, R * 0.12); c.lineTo(14, R * 0.12); c.lineTo(0, R * 0.28); c.closePath(); c.fill(); if (OL) { c.lineWidth = 3; c.stroke() }
    if (o.snarl > 0.05) { c.fillStyle = '#3a1210'; c.beginPath(); c.ellipse(0, R * 0.55, 20 * o.snarl, 13 * o.snarl, 0, 0, 7); c.fill(); c.fillStyle = '#fff'; for (const sx of [-1, 1]) { c.beginPath(); c.moveTo(sx * 10 * o.snarl, R * 0.46); c.lineTo(sx * 6 * o.snarl, R * 0.46 + 12 * o.snarl); c.lineTo(sx * 2 * o.snarl, R * 0.46); c.fill() } }
    // eyes: looking down and left at him
    for (const ex of [-26, 26]) {
      c.fillStyle = P.eye; c.beginPath(); c.ellipse(ex, -R * 0.2, A ? 13 : 11, (A ? 10 : 6.5) * (1 - o.narrow * 0.4), A ? 0 : Math.sign(ex) * 0.25, 0, 7); c.fill(); if (OL) { c.lineWidth = 3; c.strokeStyle = P.ink; c.stroke() }
      c.fillStyle = '#100a06'; c.beginPath(); c.ellipse(ex - 4, -R * 0.16, 3, 8 * (1 - o.narrow * 0.4), 0, 0, 7); c.fill()
      c.strokeStyle = P.stripe; c.lineWidth = A ? 6 : 4; c.beginPath(); c.moveTo(ex - Math.sign(ex) * 16, -R * 0.36 + o.narrow * 4); c.lineTo(ex + Math.sign(ex) * 14, -R * 0.42); c.stroke()
      if (!A) { const g = c.createRadialGradient(ex, -R * 0.2, 1, ex, -R * 0.2, 30); g.addColorStop(0, 'rgba(255,230,120,0.35)'); g.addColorStop(1, 'rgba(255,230,120,0)'); c.fillStyle = g; c.fillRect(ex - 30, -R * 0.2 - 30, 60, 60) }
    }
    c.restore()
    c.restore()
    // paws hang over the edge (not clipped) unless she has pulled back
    if (o.retreat < 0.3) { c.save(); c.globalAlpha = 1 - o.retreat / 0.3; c.translate(TX, TY + o.recoil * 10)
      for (const px of [-92, 6]) { c.fillStyle = A ? P.tig : vgrad(c, -10, 40, '#e08a3a', P.tigD); c.beginPath(); c.ellipse(px, 14, 30, 22, 0.2, 0, 7); c.fill(); if (OL) { c.lineWidth = OL; c.strokeStyle = P.ink; c.stroke() }
        c.strokeStyle = P.ink; c.lineWidth = 3; for (const tx of [-8, 4, 16]) { c.beginPath(); c.moveTo(px + tx, 24); c.lineTo(px + tx, 34); c.stroke() } }
      c.restore() }
  }

  // ---- falling earth, gun smoke, flash
  // where his hat brim is at time tau (same maths as corbett() and head())
  function brimAt(tau) {
    const p = PR, o = state(tau), sc = A ? 1.32 : 1.18, r = p.hr
    const hip = [-0.05 * p.th, -p.th * 0.97], lean = lerp(0.14, -0.06, o.aim) + o.flinch * 0.05
    const neck = [hip[0] + Math.sin(lean) * p.tor, hip[1] - Math.cos(lean) * p.tor]
    const tilt = lean - o.look * 0.55, cs = Math.cos(tilt), sn = Math.sin(tilt), rot = (x, y) => [x * cs - y * sn, x * sn + y * cs]
    const hc = rot(0, -r * 0.95), hy = A ? -r * 0.62 : -r * 0.7, b = rot(r * 0.05, hy - r * 0.2)
    return { x: CX + (neck[0] + hc[0] + b[0]) * sc, y: GY + 6 + (neck[1] + hc[1] + b[1]) * sc, hw: r * 1.32 * sc, cr: r * sc, tilt }
  }
  // falling earth: crumbs drop off the lip, hit the brim, bounce and roll off it, and settle on the ground
  const DIRT = (() => { const r = rng(7), out = []
    for (let k = 0; k < 30; k++) out.push({ t0: q.earth - 0.25 + k * 0.075 + r() * 0.08, x: LX + 2 + r() * 26, y: LIPY + 16 + r() * 20, vx: -(25 + r() * 45), vy: 20 + r() * 40, rad: 2.5 + r() * 3.5 })
    return out })()
  function dirtPos(d, t) {
    const dt = 1 / 120; let x = d.x, y = d.y, vx = d.vx, vy = d.vy, rest = false
    for (let tau = d.t0; tau < t; tau += dt) {
      if (rest) break
      vy += 1700 * dt; const nx = x + vx * dt, ny = y + vy * dt
      const b = brimAt(tau), u = nx - b.x
      if (Math.abs(u) < b.hw) {                              // over the brim: its top surface, following the tilt
        const cw = b.cr * 0.72, dome = Math.abs(u) < cw ? b.cr * 0.78 * Math.sqrt(1 - (u / cw) ** 2) : 0
        const top = b.y + u * Math.tan(b.tilt) - dome - d.rad
        if (y <= top + 2 && ny >= top) { y = top; vy = -Math.abs(vy) * 0.28; vx = vx * 0.6 + Math.sign(u || 1) * 90 + Math.sin(b.tilt) * 140; x = nx; continue }
      }
      x = nx; y = ny
      if (y >= GY + 12) { y = GY + 12; rest = true }
    }
    return [x, y]
  }
  function earth(c, t) {
    if (t < q.earth - 0.3 || t > SHOTS[3]) return
    c.fillStyle = A ? '#6b4a2a' : '#4a3422'
    for (const d of DIRT) { if (t < d.t0) continue; const [x, y] = dirtPos(d, t); c.beginPath(); c.arc(x, y, d.rad, 0, 7); c.fill() }
  }
  function smoke(c, t, m) {
    for (const f of [q.fire1, q.fire2]) { const tt = t - f; if (tt < 0 || tt > 3.2) continue
      for (let k = 0; k < 6; k++) { const r = 10 + tt * 26 + k * 5, a = (1 - tt / 3.2) * 0.3; c.fillStyle = `rgba(${A ? '240,236,226' : '200,196,186'},${a})`; c.beginPath(); c.arc(m[0] + tt * 30 + k * 10, m[1] - tt * 40 - k * 8, r, 0, 7); c.fill() } }
  }
  function flash(c, t, m) {
    for (const f of [q.fire1, q.fire2]) { const tt = t - f; if (tt < 0 || tt > 0.12) continue
      const a = 1 - tt / 0.12; c.save(); c.translate(...m); c.fillStyle = `rgba(255,236,160,${a})`; c.beginPath()
      for (let k = 0; k < 14; k++) { const ang = k / 14 * Math.PI * 2, rr = k % 2 ? 26 : 80; c.lineTo(Math.cos(ang) * rr, Math.sin(ang) * rr) } c.closePath(); c.fill(); c.restore() }
  }

  // ---- the frame
  function state(t) {
    return {
      aim: prog(t, q.swung, q.up + 0.2, 'io'),
      look: Math.max(prog(t, q.head - 0.7, q.head + 0.4, 'io'), prog(t, q.swung, q.up, 'io')) * (t > q.swung ? 1 : (t < q.there ? 1 : 1)),
      alarm: prog(t, q.earth + 0.3, q.earth + 0.8),
      dart: t > q.watched - 0.6 && t < q.earth ? Math.sin((t - q.watched + 0.6) * 4.2) : 0,
      flinch: prog(t, q.earth, q.earth + 0.3) * (1 - prog(t, q.swung, q.swung + 0.3)),
      kick: Math.max(0, 1 - Math.abs(t - q.fire1 - 0.04) / 0.12) + Math.max(0, 1 - Math.abs(t - q.fire2 - 0.04) / 0.12),
    }
  }
  window.__seek = t => {
    const c = ctx; c.setTransform(1, 0, 0, 1, 0, 0); c.globalAlpha = 1
    const cam = camAt(t); [cam.sx, cam.sy] = shake(t)
    const ts = {
      retreat: prog(t, q.gone, q.gone + 0.7, 'io'), recoil: Math.min(1, prog(t, q.fire1, q.fire1 + 0.15)) * (1 - prog(t, q.gone, q.gone + 0.5)),
      snarl: Math.max(prog(t, q.close, q.close + 0.6) * 0.8, prog(t, q.swung, q.swung + 0.3)), narrow: prog(t, q.close - 0.3, q.close + 0.4)
    }
    const cs = state(t)
    layer(c, cam, 0.08, sky); layer(c, cam, 0.3, far); layer(c, cam, 0.55, mid)
    let m = [0, 0], hatAt = [CX, 600]
    layer(c, cam, 1, c => {
      ravine(c, t); bank(c)
      tigress(c, t, ts); lipGrass(c, t, prog(t, q.gone, q.gone + 0.3) * (1 - prog(t, q.brush + 0.4, DUR)) * 0.6)
      const r = corbett(c, CX, A ? 1.32 : 1.18, cs); m = r.muzzle; hatAt = r.hat
      earth(c, t); smoke(c, t, m); flash(c, t, m)
    })
    layer(c, cam, 1.35, c => { if (!A) c.filter = 'blur(7px)'; foreground(c, t); c.filter = 'none' })
    // light: rays and vignette (painted), flash light
    if (!A) {
      c.save(); c.globalCompositeOperation = 'screen'
      for (let k = 0; k < 4; k++) { const x = 300 + k * 260 - (cam.x - 960) * 0.4, g = c.createLinearGradient(x, 0, x + 500, H); g.addColorStop(0, 'rgba(255,214,150,0.16)'); g.addColorStop(1, 'rgba(255,214,150,0)'); c.fillStyle = g; c.beginPath(); c.moveTo(x, -50); c.lineTo(x + 90, -50); c.lineTo(x + 640, H); c.lineTo(x + 420, H); c.closePath(); c.fill() }
      c.restore()
      const v = c.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 1.0); v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(0,0,0,0.6)'); c.fillStyle = v; c.fillRect(0, 0, W, H)
      c.globalCompositeOperation = 'overlay'; c.fillStyle = c.createPattern(grain, 'repeat'); c.fillRect(0, 0, W, H); c.globalCompositeOperation = 'source-over'
    } else { const v = c.createRadialGradient(W / 2, H / 2, H * 0.5, W / 2, H / 2, H * 1.1); v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(40,10,20,0.35)'); c.fillStyle = v; c.fillRect(0, 0, W, H) }
    for (const f of [q.fire1, q.fire2]) { const tt = t - f; if (tt > 0 && tt < 0.25) { c.fillStyle = `rgba(255,240,200,${(1 - tt / 0.25) * 0.45})`; c.fillRect(0, 0, W, H) } }
    // caption
    const k = CAPS.find(k => t >= k.s && t <= k.e)
    if (k) { const a = prog(t, k.s, k.s + 0.1) * (1 - prog(t, k.e - 0.1, k.e)); c.globalAlpha = a
      c.font = A ? '800 54px Playfair' : 'italic 600 50px Playfair'; c.textAlign = 'center'; c.textBaseline = 'middle'
      if (A) { c.lineWidth = 12; c.strokeStyle = '#1d130d'; c.lineJoin = 'round'; c.strokeText(k.text, W / 2, 990); c.fillStyle = '#fff'; c.fillText(k.text, W / 2, 990) }
      else { c.shadowColor = 'rgba(0,0,0,0.9)'; c.shadowBlur = 18; c.fillStyle = '#f3e7d0'; c.fillText(k.text, W / 2, 990); c.shadowBlur = 0 }
      c.globalAlpha = 1 }
    // cuts are hard cuts; label the style in the corner
    c.font = '700 30px Playfair'; c.textAlign = 'left'; c.fillStyle = 'rgba(255,255,255,0.85)'; c.fillText(A ? 'Style A: cartoon' : 'Style B: painted', 40, 56)
  }
  window.__duration = DUR
  window.__init = async () => { makeGrain(); await document.fonts.load('800 40px Playfair'); await document.fonts.load('italic 600 40px Playfair') }
})()
