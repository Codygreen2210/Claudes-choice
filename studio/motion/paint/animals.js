// paint/animals.js: four-legged animals for Style B. Feet are solved onto the ground line (y = 0),
// so paws and hooves sit ON the ground, never through it.
// beast(c, x, groundY, scale, o): o = { kind: 'tiger'|'deer'|'cow'|'buffalo'|'pig'|'sheep'|'ox', f, pose, look, mouth, fade }
// pose: { name: 'stand'|'walk'|'run'|'stalk'|'crouch'|'leap'|'lie'|'dead', d (distance moved, world px), k (0..1) }
(function (PK) {
  const { clamp, lerp, ell, shade, vgrad, hgrad, rgrad, mixCol, ik } = PK
  const KINDS = {
    tiger: { len: 250, sh: 92, hp: 90, uf: 50, lf: 48, uh: 58, lh: 54, depth: 70, head: 40, neck: 34, tail: 150, coat: '#d9741c', top: '#e8923a', belly: '#efe2cc', stripes: true, paw: 13, legW: 22 },
    deer: { len: 190, sh: 108, hp: 112, uf: 56, lf: 60, uh: 62, lh: 64, depth: 54, head: 22, neck: 56, tail: 20, coat: '#8a5a36', top: '#9a6a42', belly: '#d8c4a4', antlers: true, paw: 6, legW: 12, hoof: true },
    cow: { len: 230, sh: 118, hp: 120, uf: 58, lf: 58, uh: 64, lh: 60, depth: 90, head: 30, neck: 34, tail: 90, coat: '#e8e0d0', top: '#f2ece0', belly: '#d8cfbe', patches: '#3a2a20', paw: 9, legW: 18, hoof: true, horns: 'short' },
    ox: { len: 250, sh: 124, hp: 124, uf: 60, lf: 60, uh: 66, lh: 62, depth: 100, head: 32, neck: 34, tail: 90, coat: '#7a4a2a', top: '#8a5a36', belly: '#6a4024', paw: 10, legW: 20, hoof: true, horns: 'long' },
    buffalo: { len: 250, sh: 116, hp: 116, uf: 56, lf: 56, uh: 62, lh: 58, depth: 100, head: 32, neck: 30, tail: 80, coat: '#3a3430', top: '#4a4440', belly: '#2e2a26', paw: 10, legW: 20, hoof: true, horns: 'sweep' },
    pig: { len: 170, sh: 64, hp: 64, uf: 32, lf: 32, uh: 34, lh: 32, depth: 70, head: 26, neck: 18, tail: 20, coat: '#e8b0a0', top: '#f0c0b0', belly: '#d89a8a', paw: 7, legW: 13, hoof: true, snout: true },
    sheep: { len: 160, sh: 74, hp: 74, uf: 36, lf: 38, uh: 38, lh: 40, depth: 70, head: 20, neck: 28, tail: 20, coat: '#ece6d8', top: '#f6f2e8', belly: '#d8d0c0', wool: true, paw: 6, legW: 10, hoof: true, legCol: '#2a2420' },
  }

  function beast(c, x, gy, s, o = {}) {
    const K = KINDS[o.kind || 'tiger'], f = o.f || 1, p = Object.assign({ name: 'stand' }, o.pose || {})
    const fade = o.fade || 0, hz = o.hazeCol || '#b9b0a2', col = v => fade ? mixCol(v, hz, fade) : v
    c.save(); c.translate(x, gy); c.scale(s * f, s)
    if (o.alpha != null) c.globalAlpha *= o.alpha
    const L = K.len / 2
    // body height and tilt by pose
    let lower = 0, pitch = 0, air = 0, stride = K.len * 0.16, liftF = 0.3, stance = 0.62, gait = [0, 0.5, 0.25, 0.75] // RF, LF, RH, LH
    if (p.name === 'stalk') { lower = 24; stride *= 0.8; liftF = 0.22 }
    if (p.name === 'run') { stride *= 2.1; stance = 0.4; liftF = 0.45; gait = [0, 0.1, 0.5, 0.6] }
    if (p.name === 'crouch') lower = K.sh * 0.42 * (p.k ?? 1)
    if (p.name === 'leap') { const k = p.k ?? 0.5; air = Math.sin(Math.PI * k) * K.sh * 1.6; pitch = lerp(-0.35, 0.3, k) }
    if (p.name === 'lie' || p.name === 'dead') { lying(c, K, o, col, p.name === 'dead'); c.restore(); return }
    const ph = ((p.d || 0) / s / (4 * stride) + (p.phase || 0)) % 1
    const moving = p.name === 'walk' || p.name === 'run' || p.name === 'stalk'
    const bob = moving ? Math.cos(ph * Math.PI * 4) * (p.name === 'run' ? 8 : 3) : Math.sin((o.t || 0) * 2.2) * 1.5
    const shoulder = [L * 0.72, -K.sh - (K.uf + K.lf - K.sh) * 0 + lower * 0.8 + bob - air]
    const hipJ = [-L * 0.72, -K.hp + lower + bob - air]
    // rotate body by pitch around centre
    const rot = (pt) => { const cs = Math.cos(pitch), sn = Math.sin(pitch), cx = 0, cy = (shoulder[1] + hipJ[1]) / 2; return [cx + (pt[0] - cx) * cs - (pt[1] - cy) * sn, cy + (pt[0] - cx) * sn + (pt[1] - cy) * cs] }
    const sJ = rot(shoulder), hJ = rot(hipJ)
    const footAt = (q, base) => {
      if (!moving) return [base, 0]
      q = (q % 1 + 1) % 1; if (q < stance) return [base + stride - (q / stance) * 2 * stride, 0]
      const u = (q - stance) / (1 - stance); return [base - stride + u * 2 * stride, -K.lf * liftF * Math.sin(Math.PI * u)]
    }
    let feet = [footAt(ph + gait[0], sJ[0] + 6), footAt(ph + gait[1], sJ[0] - 4), footAt(ph + gait[2], hJ[0] - 4), footAt(ph + gait[3], hJ[0] + 8)]
    if (p.name === 'crouch') feet = [[sJ[0] + 30, 0], [sJ[0] + 16, 0], [hJ[0] + 18, 0], [hJ[0] + 30, 0]]
    if (p.name === 'leap') { const k = p.k ?? 0.5; feet = [[sJ[0] + 60 * (1 - k) + 40, sJ[1] + K.uf + K.lf * 0.6], [sJ[0] + 50, sJ[1] + K.uf + K.lf * 0.5], [hJ[0] - 70, hJ[1] + K.uh + K.lh * 0.7], [hJ[0] - 60, hJ[1] + K.uh + K.lh * 0.6]] }
    if (p.name === 'rear') { /* not used */ }
    // feet never below the ground
    feet = feet.map(ft => [ft[0], Math.min(0, ft[1])])
    const legCol = K.legCol ? col(K.legCol) : col(K.coat)
    const drawLeg = (top, foot, U, Lo, hind, near) => {
      const hint = hind ? [top[0] - 40, (top[1] + foot[1]) / 2] : [top[0] + 10, (top[1] + foot[1]) / 2 + 10]
      const footUp = [foot[0], foot[1] - K.paw * 0.9]
      const knee = ik(top, footUp, U, Lo, hint)
      c.lineCap = 'round'; c.lineJoin = 'round'; c.strokeStyle = near ? legCol : shade(legCol, -0.25); c.lineWidth = K.legW
      c.beginPath(); c.moveTo(top[0], top[1]); c.lineTo(knee[0], knee[1]); c.lineTo(footUp[0], footUp[1]); c.stroke()
      if (K.stripes) { c.strokeStyle = 'rgba(20,13,8,0.75)'; c.lineWidth = 4; for (const k of [0.35, 0.6]) { const px = lerp(knee[0], footUp[0], k), py = lerp(knee[1], footUp[1], k); c.beginPath(); c.moveTo(px - 9, py); c.lineTo(px + 8, py - 3); c.stroke() } }
      // paw / hoof resting on the ground
      if (K.hoof) ell(c, foot[0] + 3, foot[1] - K.paw * 0.6, K.paw * 1.1, K.paw * 0.6, 0, col('#2a2018'))
      else { ell(c, foot[0] + 6, foot[1] - K.paw * 0.75, K.paw * 1.35, K.paw * 0.78, 0, near ? col(K.coat) : col(shade(K.coat, -0.25))); c.strokeStyle = 'rgba(20,13,8,0.5)'; c.lineWidth = 1.5; for (const tx of [2, 8, 14]) { c.beginPath(); c.moveTo(foot[0] + tx, foot[1] - 4); c.lineTo(foot[0] + tx, foot[1] - 1); c.stroke() } }
    }
    // far legs
    drawLeg([sJ[0] - 4, sJ[1] + 10], feet[1], K.uf, K.lf, false, false)
    drawLeg([hJ[0] + 4, hJ[1] + 10], feet[3], K.uh, K.lh, true, false)
    // tail
    const tw = Math.sin((o.t || 0) * 1.6) * 0.3
    c.strokeStyle = col(K.coat); c.lineWidth = K.kind === 'tiger' ? 10 : 7; c.lineCap = 'round'
    const t0 = [hJ[0] - 20, hJ[1] - 6]
    c.beginPath(); c.moveTo(...t0); c.bezierCurveTo(t0[0] - K.tail * 0.4, t0[1] + 20, t0[0] - K.tail * 0.7, t0[1] + 60 + tw * 40, t0[0] - K.tail * 0.9, t0[1] + 10 + tw * 60); c.lineWidth = K.stripes ? 11 : 7; c.stroke()
    if (K.stripes) { c.strokeStyle = '#140d08'; c.lineWidth = 12; c.setLineDash([8, 14]); c.stroke(); c.setLineDash([]) ; ell(c, t0[0] - K.tail * 0.9, t0[1] + 10 + tw * 60, 8, 8, 0, '#140d08') }
    // body
    const bodyPath = () => {
      c.beginPath()
      const top = Math.min(sJ[1], hJ[1]) - K.depth * 0.25
      c.moveTo(hJ[0] - 24, hJ[1] + 6)
      c.bezierCurveTo(hJ[0] - 30, hJ[1] - K.depth * 0.55, hJ[0] + 40, top - 6, 0, top)
      c.bezierCurveTo(sJ[0] - 50, top - 4, sJ[0] + 10, sJ[1] - K.depth * 0.6, sJ[0] + 34, sJ[1] - K.depth * 0.2)
      c.bezierCurveTo(sJ[0] + 50, sJ[1] + K.depth * 0.3, sJ[0] + 10, sJ[1] + K.depth * 0.62, sJ[0] - 20, sJ[1] + K.depth * 0.55)
      c.bezierCurveTo(sJ[0] - 80, sJ[1] + K.depth * 0.66, hJ[0] + 60, hJ[1] + K.depth * 0.62, hJ[0] + 10, hJ[1] + K.depth * 0.5)
      c.bezierCurveTo(hJ[0] - 20, hJ[1] + K.depth * 0.45, hJ[0] - 30, hJ[1] + 30, hJ[0] - 24, hJ[1] + 6)
      c.closePath()
    }
    bodyPath()
    const yTop = Math.min(sJ[1], hJ[1]) - K.depth * 0.3, yBot = Math.max(sJ[1], hJ[1]) + K.depth * 0.66
    c.fillStyle = vgrad(c, yTop, yBot, col(K.top), col(K.coat), col(shade(K.coat, -0.15)), col(K.belly)); c.fill()
    c.save(); bodyPath(); c.clip()
    if (K.stripes) { c.strokeStyle = col('#140d08'); c.lineCap = 'round'; for (let k = 0; k < 11; k++) { const sx = hJ[0] - 10 + k * ((sJ[0] - hJ[0] + 10) / 11), wv = (k % 3) * 6; c.lineWidth = 7 + (k % 2) * 3; c.beginPath(); c.moveTo(sx, yTop - 4); c.quadraticCurveTo(sx + 14, yTop + K.depth * 0.35, sx - 4 + wv, yTop + K.depth * (0.62 + (k % 2) * 0.14)); c.stroke() } }
    if (K.patches) { for (const [px, py, r] of [[-40, -10, 30], [40, 4, 22], [-80, 20, 18]]) ell(c, px, (sJ[1] + hJ[1]) / 2 + py, r, r * 0.8, 0.4, col(K.patches)) }
    if (K.wool) { c.fillStyle = col('#fbf8f0'); for (let k = 0; k < 26; k++) { ell(c, hJ[0] + (k % 9) * 24 - 10, yTop + 14 + Math.floor(k / 9) * 18, 14, 11, 0); c.fill() } }
    c.fillStyle = 'rgba(255,230,190,0.16)'; c.fillRect(hJ[0] - 40, yTop, sJ[0] - hJ[0] + 80, 16)
    c.restore()
    // near legs
    drawLeg([hJ[0] + 10, hJ[1] + 16], feet[2], K.uh, K.lh, true, true)
    drawLeg([sJ[0] + 4, sJ[1] + 16], feet[0], K.uf, K.lf, false, true)
    // neck and head
    const look = o.look ?? (p.name === 'stalk' ? 0.25 : p.name === 'crouch' ? 0.15 : 0)
    const hx = sJ[0] + K.neck * 0.9 + 20, hy = sJ[1] - K.depth * 0.28 + look * 46 - (o.roar ? 18 : 0)
    head(c, K, hx, hy, o, col)
    c.restore()
    return { head: [x + hx * s * f, gy + hy * s] }
  }

  function head(c, K, hx, hy, o, col) {
    const R = K.head, open = o.mouth ?? (o.roar ? 1 : 0)
    c.save(); c.translate(hx, hy); c.rotate((o.headTilt || 0) - (o.roar ? 0.35 : 0))
    if (K.stripes) {
      // tiger: rounded head with cheek ruff, white muzzle, amber eye
      ell(c, -R * 0.6, -R * 0.72, R * 0.26, R * 0.3, -0.3, col('#c96a1e')); ell(c, -R * 0.6, -R * 0.7, R * 0.13, R * 0.16, -0.3, col('#efe2cc'))
      c.beginPath(); c.moveTo(-R * 1.0, R * 0.2); c.quadraticCurveTo(-R * 1.1, -R * 0.9, 0, -R * 0.82); c.quadraticCurveTo(R * 0.9, -R * 0.7, R * 1.15, -R * 0.05); c.lineTo(R * 1.3, R * 0.25); c.quadraticCurveTo(R * 1.0, R * 0.7, R * 0.3, R * 0.75); c.quadraticCurveTo(-R * 0.6, R * 0.95, -R * 1.0, R * 0.2); c.closePath()
      c.fillStyle = rgrad(c, R * 0.2, -R * 0.3, 4, R * 1.4, col('#f09a3e'), col('#d9741c'), col('#8c430c')); c.fill()
      c.save(); c.clip(); c.fillStyle = col('#efe2cc'); ell(c, R * 0.85, R * 0.45, R * 0.6, R * 0.38, 0); c.fill(); ell(c, -R * 0.4, R * 0.55, R * 0.55, R * 0.35, 0.3); c.fill()
      c.strokeStyle = col('#140d08'); c.lineCap = 'round'; c.lineWidth = 4
      for (const [a, b, cc] of [[[-R * 0.1, -R * 0.8], [0, -R * 0.55], [-R * 0.12, -R * 0.38]], [[R * 0.25, -R * 0.74], [R * 0.3, -R * 0.55], [R * 0.2, -R * 0.42]], [[-R * 0.5, -R * 0.55], [-R * 0.35, -R * 0.4], [-R * 0.55, -R * 0.25]], [[-R * 0.8, 0], [-R * 0.55, R * 0.05], [-R * 0.75, R * 0.2]], [[-R * 0.7, R * 0.35], [-R * 0.5, R * 0.35], [-R * 0.65, R * 0.5]]]) { c.beginPath(); c.moveTo(...a); c.quadraticCurveTo(...b, ...cc); c.stroke() }
      c.restore()
      ell(c, R * 1.22, R * 0.12, R * 0.14, R * 0.1, 0, col('#5a2a2a'))
      if (open > 0.05) { c.fillStyle = '#2a0e0c'; c.beginPath(); c.moveTo(R * 0.4, R * 0.45); c.quadraticCurveTo(R * 0.9, R * (0.5 + open * 0.6), R * 1.25, R * 0.42); c.lineTo(R * 1.2, R * 0.3); c.closePath(); c.fill(); c.fillStyle = '#f4efe4'; c.beginPath(); c.moveTo(R * 1.05, R * 0.34); c.lineTo(R * 1.0, R * (0.34 + open * 0.3)); c.lineTo(R * 0.95, R * 0.34); c.fill() }
      else { c.strokeStyle = '#2a1410'; c.lineWidth = 2; c.beginPath(); c.moveTo(R * 0.5, R * 0.45); c.quadraticCurveTo(R * 0.9, R * 0.55, R * 1.2, R * 0.3); c.stroke() }
      ell(c, R * 0.42, -R * 0.25, R * 0.17, R * 0.11, -0.15, '#e9d24a'); ell(c, R * 0.46, -R * 0.24, R * 0.05, R * 0.09, 0, '#140d08')
      c.strokeStyle = '#140d08'; c.lineWidth = 3; c.beginPath(); c.moveTo(R * 0.2, -R * (0.42 - (o.narrow || 0) * 0.08)); c.lineTo(R * 0.62, -R * 0.42); c.stroke()
      c.fillStyle = rgrad(c, R * 0.44, -R * 0.25, 1, R * 0.45, 'rgba(255,230,120,0.25)', 'rgba(255,230,120,0)'); c.fillRect(-R, -R, R * 2.5, R * 2)
    } else {
      // hoofed animals: a long head
      c.fillStyle = vgrad(c, -R, R, col(K.top), col(K.coat), col(shade(K.coat, -0.2)))
      c.beginPath(); c.moveTo(-R * 0.9, -R * 0.4); c.quadraticCurveTo(-R * 0.4, -R * 1.0, R * 0.6, -R * 0.5); c.quadraticCurveTo(R * 1.8, -R * 0.1, R * 1.9, R * 0.35); c.quadraticCurveTo(R * 1.5, R * 0.75, R * 0.6, R * 0.6); c.quadraticCurveTo(-R * 0.6, R * 0.6, -R * 0.9, -R * 0.4); c.fill()
      if (K.snout) ell(c, R * 1.85, R * 0.2, R * 0.28, R * 0.3, 0, col('#d88a7a'))
      ell(c, -R * 0.4, -R * 0.8, R * 0.18, R * 0.4, -0.6, col(shade(K.coat, -0.1)))
      ell(c, R * 0.35, -R * 0.2, R * 0.1, R * 0.1, 0, '#140d08')
      if (K.antlers) { c.strokeStyle = col('#5a3a20'); c.lineWidth = 4; c.lineCap = 'round'; c.beginPath(); c.moveTo(-R * 0.1, -R * 0.8); c.lineTo(-R * 0.5, -R * 2.6); c.moveTo(-R * 0.35, -R * 1.8); c.lineTo(R * 0.3, -R * 2.4); c.moveTo(-R * 0.45, -R * 2.3); c.lineTo(-R * 1.1, -R * 2.8); c.stroke() }
      if (K.horns) { c.strokeStyle = col('#e8dcc0'); c.lineWidth = K.horns === 'short' ? 5 : 8; c.lineCap = 'round'; c.beginPath(); c.moveTo(-R * 0.2, -R * 0.8); if (K.horns === 'sweep') c.quadraticCurveTo(-R * 1.6, -R * 1.2, -R * 1.4, R * 0.1); else if (K.horns === 'long') c.quadraticCurveTo(-R * 0.6, -R * 2.0, R * 0.4, -R * 2.0); else c.quadraticCurveTo(-R * 0.4, -R * 1.3, R * 0.1, -R * 1.3); c.stroke() }
    }
    c.restore()
  }

  function lying(c, K, o, col, dead) {
    // resting on the ground: legs folded under (lie) or out to the side (dead), body flat on y = 0
    const L = K.len / 2, dy = dead ? -K.depth * 0.42 : -K.depth * 0.55
    c.fillStyle = vgrad(c, dy - K.depth * 0.5, 0, col(K.top), col(K.coat), col(K.belly))
    c.beginPath(); c.ellipse(0, dy, L * 1.05, K.depth * (dead ? 0.42 : 0.55), 0, 0, Math.PI * 2); c.fill()
    if (K.stripes) { c.save(); c.beginPath(); c.ellipse(0, dy, L * 1.05, K.depth * 0.55, 0, 0, Math.PI * 2); c.clip(); c.strokeStyle = col('#140d08'); c.lineCap = 'round'; for (let k = 0; k < 11; k++) { const sx = -L + k * L * 0.2; c.lineWidth = 7; c.beginPath(); c.moveTo(sx, dy - K.depth * 0.6); c.quadraticCurveTo(sx + 12, dy - 6, sx - 4, dy + K.depth * 0.2); c.stroke() } c.restore() }
    c.strokeStyle = col(K.coat); c.lineWidth = K.legW; c.lineCap = 'round'
    if (dead) { for (const lx of [L * 0.6, L * 0.85, -L * 0.6, -L * 0.85]) { c.beginPath(); c.moveTo(lx, dy + 6); c.lineTo(lx + 40, -K.legW * 0.5); c.stroke() } }
    else { for (const lx of [L * 0.7, L * 0.95]) { c.beginPath(); c.moveTo(lx, -K.legW * 0.5); c.lineTo(lx + 60, -K.legW * 0.5); c.stroke() } }
    c.lineWidth = K.stripes ? 11 : 7; c.beginPath(); c.moveTo(-L, dy + 10); c.quadraticCurveTo(-L - 80, -6, -L - 140, -8); c.stroke()
    head(c, K, L * 1.05 + 10, dead ? -K.head * 0.7 : dy - K.depth * 0.25, Object.assign({}, o, { headTilt: dead ? 0.3 : 0 }), col)
  }

  // birds: a small flock flapping across
  function birds(c, t, x0, y0, n = 7, o = {}) {
    const r = PK.rng(o.seed || 3); c.strokeStyle = o.col || 'rgba(30,26,22,0.8)'; c.lineWidth = 2.5; c.lineCap = 'round'
    for (let k = 0; k < n; k++) { const x = x0 + (o.vx ?? 120) * t + r() * 300, y = y0 + r() * 120 + Math.sin(t * 2 + k) * 8, w = 10 + r() * 8, fl = Math.sin(t * 12 + k * 1.7) * w * 0.6
      c.beginPath(); c.moveTo(x - w, y - fl); c.quadraticCurveTo(x - w * 0.4, y - 2, x, y); c.quadraticCurveTo(x + w * 0.4, y - 2, x + w, y - fl); c.stroke() }
  }

  Object.assign(PK, { beast, birds, KINDS })
})(window.PK)
