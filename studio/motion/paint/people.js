// paint/people.js: painted people for Style B. One rig, many costumes, faces with expressions.
// person(c, x, groundY, scale, o): o = { f: 1 right / -1 left, pose: {...}, cos: costume, face: {...}, fade, hazeCol }
// Coordinates inside the rig: origin on the ground under the hips, facing right, y up is negative.
(function (PK) {
  const { clamp, lerp, rng, mixCol, shade, vgrad, hgrad, rgrad, ell, poly } = PK
  const BASE = { hr: 23, tor: 118, th: 86, sh: 84, ua: 64, fa: 60, tw: 70, lw: 22, aw: 17 }

  // ---- 2-bone IK; the joint nearest the hint wins
  function ik(a, b, L1, L2, hint) {
    let dx = b[0] - a[0], dy = b[1] - a[1], d = Math.hypot(dx, dy)
    d = clamp(d, Math.abs(L1 - L2) + 0.01, L1 + L2 - 0.01)
    const base = Math.atan2(dy, dx), off = Math.acos(clamp((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d), -1, 1))
    const j1 = [a[0] + L1 * Math.cos(base + off), a[1] + L1 * Math.sin(base + off)], j2 = [a[0] + L1 * Math.cos(base - off), a[1] + L1 * Math.sin(base - off)]
    const d1 = Math.hypot(j1[0] - hint[0], j1[1] - hint[1]), d2 = Math.hypot(j2[0] - hint[0], j2[1] - hint[1])
    return d1 < d2 ? j1 : j2
  }
  // reach: if the target is out of reach, the hand stops at full stretch along the line
  function reach(a, b, L) { const dx = b[0] - a[0], dy = b[1] - a[1], d = Math.hypot(dx, dy); return d <= L ? b : [a[0] + dx / d * L, a[1] + dy / d * L] }

  // ---- poses. Each returns { hip, lean, bf, ff, hf, hn, look, hintF, hintN, item } in rig units
  function pose(P, o, tgt) {
    const leg = P.th + P.sh, stand = -leg * 0.985
    const p = Object.assign({ name: 'stand' }, o)
    const res = { lean: 0, look: 0, item: p.item }
    const shoulderOf = (hip, lean) => { const n = [hip[0] + Math.sin(lean) * P.tor, hip[1] - Math.cos(lean) * P.tor]; return [lerp(hip[0], n[0], 0.86), lerp(hip[1], n[1], 0.86) + 4] }
    const armDown = (sh, side) => [sh[0] + side * 3 + 2, sh[1] + P.ua + P.fa - 8]
    switch (p.name) {
      case 'walk': case 'run': {
        const run = p.name === 'run', L = p.stride || (run ? 62 : 38), lift = run ? P.sh * 0.5 : P.sh * 0.24, stanceF = run ? 0.36 : 0.5
        const ph = ((p.d || 0) / (4 * L) + (p.phase || 0)) % 1
        const footAt = q => { q = (q % 1 + 1) % 1; if (q < stanceF) return [L - (q / stanceF) * 2 * L, 0]; const u = (q - stanceF) / (1 - stanceF); return [-L + u * 2 * L, -lift * Math.sin(Math.PI * u)] }
        const lean = run ? 0.24 : 0.05
        const bob = run ? -Math.abs(Math.sin(ph * Math.PI * 2)) * 10 : Math.cos(ph * Math.PI * 4) * 3
        res.hip = [run ? 10 : 2, stand + (run ? 8 : 0) + bob]
        res.ff = footAt(ph); res.bf = footAt(ph + 0.5)
        res.lean = lean + (p.lean || 0)
        const sh = shoulderOf(res.hip, res.lean), sw = Math.sin(ph * Math.PI * 2)
        if (run) { res.hn = [sh[0] - sw * 34 + 18, sh[1] + 60 - Math.abs(sw) * 10]; res.hf = [sh[0] + sw * 34 + 18, sh[1] + 60 - Math.abs(sw) * 10]; res.hintN = res.hintF = [sh[0] - 40, sh[1] + 30] }
        else { res.hn = [sh[0] - sw * 30 + 6, sh[1] + P.ua + P.fa - 14 - Math.abs(sw) * 6]; res.hf = [sh[0] + sw * 30 + 8, sh[1] + P.ua + P.fa - 14 - Math.abs(sw) * 6] }
        if (p.item === 'rifle') { const ang = -2.25; res.rifle = { butt: [sh[0] + 46, sh[1] + 56], ang }; res.hn = [sh[0] + 46 + Math.cos(ang) * 30, sh[1] + 56 + Math.sin(ang) * 30] }
        if (p.item === 'bundle') { res.hn = [sh[0] + 30, sh[1] - 62]; res.hf = [sh[0] - 22, sh[1] - 62]; res.hintN = [sh[0] + 70, sh[1] - 20]; res.hintF = [sh[0] - 60, sh[1] - 20] }
        res.look = p.look || 0; break
      }
      case 'kneel': case 'kneelAim': {
        res.hip = [-0.05 * P.th, -P.th * 0.97]
        res.bf = [res.hip[0] - 0.12 * P.th - P.sh, -6]; res.ff = [res.hip[0] + P.th * 0.95, -4]
        const k = p.name === 'kneelAim' ? (p.k ?? 1) : 0
        res.lean = lerp(0.14, -0.06, k) + (p.lean || 0)
        const sh = shoulderOf(res.hip, res.lean)
        if (p.item === 'rifle' || p.name === 'kneelAim') rifleHands(res, sh, k, tgt, P)
        else { res.hn = [res.ff[0] - 4, res.ff[1] - P.sh - 6]; res.hf = [res.ff[0] + 6, res.ff[1] - P.sh - 2] }
        res.look = p.look ?? (k ? 0.45 * k : 0); break
      }
      case 'standAim': case 'point': case 'stand': case 'hold': case 'raise': case 'cheer': case 'shout': case 'drum': case 'carry': case 'wave': case 'salute': default: {
        const w = p.wide ?? 16
        res.hip = [0, stand + (p.crouch || 0) * 40]
        res.bf = [-w - (p.step || 0), 0]; res.ff = [w + (p.step || 0), 0]
        res.lean = p.lean || 0
        const sh = shoulderOf(res.hip, res.lean)
        res.hn = armDown(sh, 1); res.hf = armDown(sh, -1)
        res.look = p.look || 0
        if (p.item === 'rifle' && p.name === 'stand') { rifleHands(res, sh, 0, tgt, P); res.rifle.butt = [res.hip[0] - 6, res.hip[1] + 6]; res.rifle.ang = -0.9; const al = d => [res.rifle.butt[0] + Math.cos(-0.9) * d, res.rifle.butt[1] + Math.sin(-0.9) * d]; res.hn = al(40); res.hf = al(92) }
        if (p.name === 'standAim') { res.bf = [-34, 0]; res.ff = [30, 0]; rifleHands(res, sh, p.k ?? 1, tgt, P); res.look = p.look ?? 0.2 }
        if (p.name === 'point') { const k = p.k ?? 1, T = tgt || [300, -260]; const dir = Math.atan2(T[1] - sh[1], T[0] - sh[0]); res.hn = [lerp(res.hn[0], sh[0] + Math.cos(dir) * (P.ua + P.fa - 6), k), lerp(res.hn[1], sh[1] + Math.sin(dir) * (P.ua + P.fa - 6), k)]; res.hintN = [sh[0] + Math.cos(dir) * 40, sh[1] + 30] }
        if (p.name === 'hold') { const at = p.at || [50, stand - P.tor * 0.5]; const hp = at; res.hn = [hp[0] - 10, hp[1] + 6]; res.hf = [hp[0] + 12, hp[1]]; res.holdAt = hp }
        if (p.name === 'raise') { const k = p.k ?? 1; res.hn = [lerp(res.hn[0], sh[0] + 30, k), lerp(res.hn[1], sh[1] - P.ua - P.fa + 10, k)]; res.hintN = [sh[0] + 50, sh[1] - 30]; res.holdAt = res.hn }
        if (p.name === 'cheer') { const k = p.k ?? 1, wv = Math.sin((p.t || 0) * 9) * 10; res.hn = [lerp(res.hn[0], sh[0] + 36 + wv, k), lerp(res.hn[1], sh[1] - P.ua - P.fa + 18, k)]; res.hf = [lerp(res.hf[0], sh[0] - 20 - wv, k), lerp(res.hf[1], sh[1] - P.ua - P.fa + 18, k)]; res.hintN = [sh[0] + 70, sh[1] - 20]; res.hintF = [sh[0] - 60, sh[1] - 20] }
        if (p.name === 'wave') { const wv = Math.sin((p.t || 0) * 8) * 22; res.hn = [sh[0] + 40 + wv, sh[1] - P.ua - 10]; res.hintN = [sh[0] + 60, sh[1] + 10] }
        if (p.name === 'shout') { res.hn = [sh[0] + 34, sh[1] - 26]; res.hintN = [sh[0] + 30, sh[1] + 40]; res.lean += 0.06 }
        if (p.name === 'salute') { res.hn = [sh[0] + 26, sh[1] - 52]; res.hintN = [sh[0] + 64, sh[1] - 10] }
        if (p.name === 'carry') { res.hn = [sh[0] + 30, sh[1] - 62]; res.hf = [sh[0] - 22, sh[1] - 62]; res.hintN = [sh[0] + 70, sh[1] - 20]; res.hintF = [sh[0] - 60, sh[1] - 20] }
        if (p.name === 'drum') { const ph = (p.t || 0) * (p.bpm || 120) / 60, beat = Math.pow(Math.abs(Math.sin(ph * Math.PI)), 0.5); res.drumAt = [sh[0] + 50, sh[1] + 64]; res.hf = [sh[0] + 52, sh[1] + 44]; res.hn = [sh[0] + 40, sh[1] + 10 - beat * 30]; res.hintN = [sh[0] - 10, sh[1] + 40]; res.item = 'drum' }
        break
      }
      case 'sit': {
        const sy = -(p.seat ?? 88)
        res.hip = [0, sy]; res.lean = p.lean ?? 0.04
        res.ff = [P.th * 0.95 + 8, 0]; res.bf = [P.th * 0.85, 0]
        const sh = shoulderOf(res.hip, res.lean)
        if (p.hands === 'table') { res.hn = [sh[0] + 66, sh[1] + 66 + (p.write ? Math.sin((p.t || 0) * 14) * 4 : 0)]; res.hf = [sh[0] + 78, sh[1] + 70] }
        else if (p.hands === 'head') { res.hn = [sh[0] + 30, sh[1] - 20]; res.hf = [sh[0] + 40, sh[1] - 24]; res.lean = 0.5 }
        else if (p.hands === 'hold') { res.hn = [sh[0] + 52, sh[1] + 36]; res.hf = [sh[0] + 64, sh[1] + 30]; res.holdAt = [sh[0] + 60, sh[1] + 26] }
        else { res.hn = [sh[0] + 54, sh[1] + 86]; res.hf = [sh[0] + 64, sh[1] + 84] }
        res.look = p.look || 0; break
      }
      case 'crouch': {
        res.hip = [-12, -P.th * 0.75]; res.lean = 0.42; res.bf = [-34, 0]; res.ff = [26, 0]
        const sh = shoulderOf(res.hip, res.lean); res.hn = [sh[0] + 40, -10]; res.hf = [sh[0] + 50, -8]; res.look = p.look ?? 0.1; break
      }
      case 'lie': { res.lying = true; break }
    }
    return res
  }
  function rifleHands(res, sh, k, tgt, P) {
    const T = tgt || [300, -300]
    const aimA = Math.atan2(T[1] - sh[1], T[0] - sh[0]), restA = -0.32
    const ang = lerp(restA, aimA, k)
    const butt = [lerp(res.hip[0] - 20, sh[0] - 4, k), lerp(res.hip[1] - 2, sh[1] + 2, k)]
    res.rifle = { butt, ang }
    const along = d => [butt[0] + Math.cos(ang) * d, butt[1] + Math.sin(ang) * d]
    res.hn = along(42); res.hf = along(98)
  }

  // ---- costumes
  const COS = {}
  function costume(name, o) { COS[name] = Object.assign({ skin: '#c99273', shirt: '#a8946a', pants: '#4c3a2a', boot: '#21180f', hair: '#2b1d12', hat: null, hatCol: '#6e563b', collar: null, coat: null, skirt: null, belt: '#2a1f14', moustache: false, beard: false, build: 1, height: 1 }, o) }
  costume('corbett', { shirt: '#a8946a', pants: '#4c3a2a', hat: 'felt', hatCol: '#6e563b', moustache: '#3b2617', hair: '#3b2617' })
  costume('villager', { skin: '#a8725a', shirt: '#e6dcc6', pants: '#d8cdb5', boot: '#6b4a32', hat: 'turban', hatCol: '#e9e0cc', moustache: '#1d140d', hair: '#1d140d', dhoti: true })
  costume('villager2', { skin: '#9c6a50', shirt: '#b9a27c', pants: '#e2d6bd', boot: '#5e4330', hat: 'cap', hatCol: '#5a4a3a', moustache: '#1d140d', hair: '#1d140d', dhoti: true })
  costume('villager3', { skin: '#a46f55', shirt: '#7d6a55', pants: '#d6c9ad', boot: '#5e4330', hat: 'turban', hatCol: '#b5442e', hair: '#1d140d', dhoti: true, beard: '#2a2018' })
  costume('villagewoman', { skin: '#a8725a', shirt: '#9b3b2c', skirt: '#7a2e24', boot: '#6b4a32', hat: 'veil', hatCol: '#c96a3a', hair: '#1d140d', build: 0.9, height: 0.94 })
  costume('sepoy', { skin: '#a46f55', shirt: '#7c6b45', pants: '#6b5c3c', boot: '#2a1f14', hat: 'turban', hatCol: '#d7c9a6', moustache: '#1d140d', belt: '#3a2a18' })
  costume('official', { skin: '#a8725a', shirt: '#e8e0cc', pants: '#e8e0cc', coat: '#3a3a44', boot: '#21180f', hat: 'turban', hatCol: '#f0ead8', moustache: '#d8d0c0', hair: '#cfc8b8' })
  costume('dutchman', { skin: '#d9a88a', shirt: '#2a2622', pants: '#2a2622', coat: '#1f1c1a', boot: '#1a1410', hat: 'capotain', hatCol: '#1b1816', collar: 'falling', hair: '#5a3c22', moustache: '#5a3c22', beard: '#5a3c22' })
  costume('dutchman2', { skin: '#e0b096', shirt: '#4a3a2a', pants: '#3a2e22', coat: '#5a3a26', boot: '#1a1410', hat: 'brim', hatCol: '#2a221a', collar: 'ruff', hair: '#8a6a4a', moustache: '#8a6a4a' })
  costume('dutchman3', { skin: '#d6a084', shirt: '#6a2a22', pants: '#2c2420', coat: '#2e2a2a', boot: '#1a1410', hat: 'brim', hatCol: '#3a2a1e', collar: 'falling', hair: '#3a2a1e', beard: '#3a2a1e' })
  costume('dutchwoman', { skin: '#e2b49a', shirt: '#2b2a30', skirt: '#2b2a30', boot: '#1a1410', hat: 'bonnet', hatCol: '#f2ede2', collar: 'falling', hair: '#8a5a32', build: 0.9, height: 0.95 })
  costume('ponzi', { skin: '#d4a07e', shirt: '#f0ece2', pants: '#3a3a40', coat: '#3a3a40', boot: '#14110e', hat: 'boater', hatCol: '#e6cf8f', collar: 'tie', tie: '#7a1f22', hair: '#1d1712', moustache: '#1d1712', height: 0.92, cane: true })
  costume('clerk', { skin: '#dcae90', shirt: '#ece6d8', pants: '#4a4440', coat: '#5a5048', boot: '#1a1410', hat: 'cap', hatCol: '#4a4038', collar: 'tie', tie: '#2a3a5a', hair: '#5a3c22' })
  costume('suit', { skin: '#d8a888', shirt: '#ece6d8', pants: '#2e3036', coat: '#2e3036', boot: '#14110e', hat: 'fedora', hatCol: '#3a3430', collar: 'tie', tie: '#5a1f22', hair: '#3a2a1e' })
  costume('maid', { skin: '#e2b49a', shirt: '#2a2a32', skirt: '#2a2a32', boot: '#14110e', hat: 'bonnet', hatCol: '#f2ede2', apron: '#f2ede2', hair: '#6a4426', build: 0.9, height: 0.94 })
  costume('lady', { skin: '#e2b49a', shirt: '#6a4a5a', skirt: '#5a3a4a', boot: '#14110e', hat: 'cloche', hatCol: '#3a2a34', hair: '#3a2416', build: 0.9, height: 0.95 })
  costume('police', { skin: '#dcae90', shirt: '#1f2a44', pants: '#1f2a44', coat: '#1f2a44', boot: '#0e0c0a', hat: 'police', hatCol: '#1a2238', buttons: '#d8b85a', moustache: '#4a3020', hair: '#4a3020', belt: '#0e0c0a' })
  costume('reporter', { skin: '#d8a888', shirt: '#ece6d8', pants: '#5a5048', coat: null, boot: '#1a1410', hat: 'fedora', hatCol: '#6a5a48', collar: 'tie', tie: '#3a3a3a', hair: '#3a2a1e', vest: '#5a5048' })
  costume('usnavy', { skin: '#dcae90', shirt: '#e8e6e0', pants: '#e8e6e0', coat: null, boot: '#e8e6e0', hat: 'sailor', hatCol: '#f4f2ec', hair: '#5a3c22' })
  costume('usofficer', { skin: '#dcae90', shirt: '#2a3048', pants: '#2a3048', coat: '#2a3048', boot: '#0e0c0a', hat: 'navy', hatCol: '#2a3048', collar: 'tie', tie: '#0e0c0a', buttons: '#d8b85a', hair: '#8a8a8a' })
  costume('khaki', { skin: '#dcae90', shirt: '#b5a27a', pants: '#b5a27a', boot: '#3a2a1a', hat: 'navy', hatCol: '#b5a27a', collar: 'tie', tie: '#5a4a32', hair: '#5a3c22' })
  costume('codebreaker', { skin: '#dcae90', shirt: '#e8e2d4', pants: '#4a4a52', boot: '#14110e', hat: null, collar: 'tie', tie: '#2a2a3a', hair: '#6a6a6a', robe: '#8a2a2a', glasses: true })
  costume('pilot', { skin: '#dcae90', shirt: '#8a6a44', pants: '#6a5a40', boot: '#2a1a10', hat: 'pilot', hatCol: '#5a3a22', hair: '#5a3c22', vest: '#c9a24a' })
  costume('jpofficer', { skin: '#d8a888', shirt: '#ecebe4', pants: '#ecebe4', coat: '#ecebe4', boot: '#0e0c0a', hat: 'navy', hatCol: '#ecebe4', buttons: '#d8b85a', collar: 'stand', hair: '#14110e', moustache: '#14110e' })
  costume('jpsailor', { skin: '#d8a888', shirt: '#e6e2d6', pants: '#3a3a44', boot: '#14110e', hat: 'cap', hatCol: '#2a2a34', hair: '#14110e' })
  costume('judge', { skin: '#e0b096', shirt: '#14110e', pants: '#14110e', coat: '#14110e', boot: '#0e0c0a', hat: null, collar: 'falling', hair: '#d8d4cc', beard: '#d8d4cc' })
  costume('prisoner', { skin: '#d4a07e', shirt: '#8a8478', pants: '#8a8478', boot: '#2a2420', hat: null, hair: '#3a3430', moustache: '#3a3430', stripes: true, height: 0.92 })
  costume('sultan', { skin: '#c99273', shirt: '#6a1f2a', pants: '#2a2a5a', coat: '#c9a24a', boot: '#3a2a1a', hat: 'turban', hatCol: '#f4efe4', beard: '#1d140d', moustache: '#1d140d', plume: true })

  // haze: every colour leans toward the haze colour by `fade`
  const cache = new Map()
  function palette(cos, fade, haze) {
    if (!fade) return cos
    const key = (cos._n || '') + fade.toFixed(2) + haze; let p = cache.get(key); if (p) return p
    p = {}; for (const [k, v] of Object.entries(cos)) p[k] = typeof v === 'string' && v[0] === '#' ? mixCol(v, haze, fade) : v
    cache.set(key, p); return p
  }
  Object.entries(COS).forEach(([n, c]) => c._n = n)

  // ---- drawing pieces
  function limb(c, pts, w, col) {
    c.lineCap = 'round'; c.lineJoin = 'round'
    const path = () => { c.beginPath(); c.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) c.lineTo(pts[i][0], pts[i][1]) }
    path(); c.lineWidth = w; c.strokeStyle = col; c.stroke()
    c.save(); c.translate(-w * 0.16, -w * 0.12); path(); c.lineWidth = w * 0.28; c.strokeStyle = 'rgba(255,235,200,0.18)'; c.stroke(); c.restore()
  }
  function boot(c, f, side, P, col) { ell(c, f[0] + 9, f[1] - 5, P.lw * 0.78, P.lw * 0.4, 0, col) }
  function hand(c, h, P, col) { ell(c, h[0], h[1], P.aw * 0.6, P.aw * 0.6, 0, col) }

  function person(c, x, gy, s, o = {}) {
    const cos = palette(COS[o.cos] || o.cos || COS.corbett, o.fade || 0, o.hazeCol || '#b9b0a2')
    const P = Object.assign({}, BASE); const h = (cos.height || 1), b = (cos.build || 1)
    P.th *= h; P.sh *= h; P.tor *= h; P.ua *= h; P.fa *= h; P.tw *= b; P.lw *= b
    const f = o.f || 1
    const tgt = o.target ? [(o.target[0] - x) / s * f, (o.target[1] - gy) / s] : null
    const pz = pose(P, o.pose || {}, tgt)
    c.save(); c.translate(x, gy); c.scale(s * f, s)
    if (o.alpha != null) c.globalAlpha *= o.alpha
    // contact shadow
    if (!o.noShadow) ell(c, 0, 0, P.th * 1.15, 9, 0, `rgba(0,0,0,${0.28 * (1 - (o.fade || 0))})`)
    if (pz.lying) { lying(c, P, cos, o); c.restore(); return {} }
    const hip = pz.hip, lean = pz.lean
    const neck = [hip[0] + Math.sin(lean) * P.tor, hip[1] - Math.cos(lean) * P.tor]
    const sh = [lerp(hip[0], neck[0], 0.86), lerp(hip[1], neck[1], 0.86) + 4], shF = [sh[0] + 6, sh[1] - 3]
    const kneeHint = foot => [Math.max(hip[0], foot[0]) + 60, (hip[1] + foot[1]) / 2]
    const bK = ik(hip, pz.bf, P.th, P.sh, kneeHint(pz.bf)), fK = ik(hip, pz.ff, P.th, P.sh, kneeHint(pz.ff))
    const hf = reach(shF, pz.hf, P.ua + P.fa - 0.5), hn = reach(sh, pz.hn, P.ua + P.fa - 0.5)
    const eF = ik(shF, hf, P.ua, P.fa, pz.hintF || [shF[0] - 20, shF[1] + 70]), eN = ik(sh, hn, P.ua, P.fa, pz.hintN || [sh[0] - 20, sh[1] + 70])
    const skinD = shade(cos.skin, -0.25), shirtD = shade(cos.shirt, -0.3), pantsD = shade(cos.pants, -0.3)
    const sleeve = cos.coat || cos.shirt, sleeveD = shade(sleeve, -0.3)
    // far leg and far arm (in shade)
    if (!cos.skirt) { limb(c, [hip, bK, pz.bf], P.lw, cos.dhoti ? shade(cos.pants, -0.15) : pantsD) }
    boot(c, pz.bf, -1, P, shade(cos.boot, -0.2))
    if (cos.dhoti) { limb(c, [bK, pz.bf], P.lw * 0.62, skinD) }
    limb(c, [shF, eF, hf], P.aw, sleeveD); hand(c, hf, P, skinD)
    if (pz.rifle) rifle(c, pz.rifle, 'far')
    // near leg
    if (!cos.skirt) { limb(c, [hip, fK, pz.ff], P.lw, cos.pants); if (cos.dhoti) limb(c, [fK, pz.ff], P.lw * 0.62, cos.skin) }
    boot(c, pz.ff, 1, P, cos.boot)
    // skirt or long coat over the legs
    const ux = (neck[0] - hip[0]) / P.tor, uy = (neck[1] - hip[1]) / P.tor, nx = -uy, ny = ux, tw = P.tw
    if (cos.skirt) {
      const swing = (pz.ff[0] - pz.bf[0]) * 0.25
      const hemY = Math.max(pz.ff[1], pz.bf[1]) - 14, hemL = Math.min(pz.bf[0], pz.ff[0]) - 26, hemR = Math.max(pz.bf[0], pz.ff[0]) + 30
      c.fillStyle = hgrad(c, hemL, hemR, shade(cos.skirt, 0.08), cos.skirt, shade(cos.skirt, -0.3))
      c.beginPath(); c.moveTo(hip[0] - nx * tw * 0.45, hip[1] - ny * tw * 0.45 - 6); c.lineTo(hip[0] + nx * tw * 0.45, hip[1] + ny * tw * 0.45 - 6)
      c.quadraticCurveTo(hemR + 6, hip[1] * 0.4, hemR + swing * 0.3, hemY); c.quadraticCurveTo((hemL + hemR) / 2, hemY + 10, hemL + swing * 0.3, hemY); c.quadraticCurveTo(hemL - 4, hip[1] * 0.4, hip[0] - nx * tw * 0.45, hip[1] - ny * tw * 0.45 - 6); c.fill()
      if (cos.apron) { c.fillStyle = cos.apron; c.beginPath(); c.moveTo(hip[0] + 4, hip[1] - 4); c.lineTo(hip[0] + nx * tw * 0.4 + 6, hip[1] + ny * tw * 0.4); c.lineTo(hemR - 4 + swing * 0.3, hemY - 30); c.lineTo(hemR - 40, hemY - 24); c.closePath(); c.fill() }
    }
    if (cos.coat && !cos.skirt && o.pose?.name !== 'sit') {
      c.fillStyle = hgrad(c, hip[0] - 40, hip[0] + 40, shade(cos.coat, 0.08), cos.coat, shade(cos.coat, -0.3))
      const kb = lerp2(hip, bK, 0.8), kf = lerp2(hip, fK, 0.8)
      c.beginPath(); c.moveTo(hip[0] - nx * tw * 0.48 + ux * 10, hip[1] - ny * tw * 0.48 + uy * 10); c.lineTo(hip[0] + nx * tw * 0.5 + ux * 10, hip[1] + ny * tw * 0.5 + uy * 10)
      c.lineTo(Math.max(kf[0], kb[0]) + 14, Math.max(kf[1], kb[1]) + 6); c.lineTo(Math.min(kf[0], kb[0]) - 12, Math.max(kf[1], kb[1]) + 6); c.closePath(); c.fill()
    }
    function lerp2(a, b, k) { return [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k] }
    // torso
    const top = cos.coat || cos.shirt
    c.beginPath()
    const T0 = [hip[0] - nx * tw * 0.42, hip[1] - ny * tw * 0.42], T1 = [hip[0] + nx * tw * 0.42, hip[1] + ny * tw * 0.42], T2 = [neck[0] + nx * tw * 0.5, neck[1] + ny * tw * 0.5], T3 = [neck[0] - nx * tw * 0.5, neck[1] - ny * tw * 0.5]
    c.moveTo(...T0); c.lineTo(...T1); c.quadraticCurveTo(hip[0] + nx * tw * 0.62 + ux * 40, hip[1] + ny * tw * 0.62 + uy * 40, ...T2); c.quadraticCurveTo(neck[0] + ux * 10, neck[1] + uy * 10, ...T3); c.quadraticCurveTo(hip[0] - nx * tw * 0.6 + ux * 40, hip[1] - ny * tw * 0.6 + uy * 40, ...T0); c.closePath()
    c.fillStyle = hgrad(c, hip[0] - 40, hip[0] + 40, shade(top, 0.14), top, shade(top, -0.32)); c.fill()
    if (cos.stripes) { c.save(); c.clip(); c.strokeStyle = 'rgba(30,26,22,0.6)'; c.lineWidth = 8; for (let k = -6; k < 6; k++) { c.beginPath(); c.moveTo(hip[0] - 60, hip[1] + k * 22); c.lineTo(hip[0] + 60, hip[1] + k * 22 - 10); c.stroke() } c.restore() }
    if (cos.vest) { c.save(); c.clip(); c.fillStyle = cos.vest; c.fillRect(hip[0] - 10, neck[1], 60, P.tor + 10); c.restore() }
    if (cos.coat && cos.collar === 'tie') { // shirt front and tie
      c.fillStyle = cos.shirt; poly(c, [lerp2(neck, hip, 0.02).map((v, i) => v + (i ? 0 : 6)), [neck[0] + nx * 14 + 8, neck[1] + ny * 14], lerp2(neck, hip, 0.45).map((v, i) => v + (i ? 0 : 14))], cos.shirt)
    }
    if (cos.tie) { c.strokeStyle = cos.tie; c.lineWidth = 6; c.beginPath(); c.moveTo(neck[0] + 9, neck[1] + 8); c.lineTo(lerp(neck[0], hip[0], 0.4) + 12, lerp(neck[1], hip[1], 0.4)); c.stroke() }
    if (cos.buttons) { c.fillStyle = cos.buttons; for (let k = 1; k < 5; k++) { const p = lerp2(neck, hip, k * 0.18); ell(c, p[0] + nx * tw * 0.32, p[1] + ny * tw * 0.32, 2.6, 2.6, 0); c.fill() } }
    if (!cos.skirt && !cos.robe) { c.strokeStyle = cos.belt; c.lineWidth = 7; c.beginPath(); c.moveTo(hip[0] - nx * tw * 0.45 + ux * 12, hip[1] - ny * tw * 0.45 + uy * 12); c.lineTo(hip[0] + nx * tw * 0.45 + ux * 12, hip[1] + ny * tw * 0.45 + uy * 12); c.stroke() }
    if (cos.collar === 'ruff') { c.fillStyle = '#f4f0e6'; ell(c, neck[0] + 2, neck[1] + 4, 30, 11, lean, '#f4f0e6'); c.strokeStyle = 'rgba(120,110,100,0.5)'; c.lineWidth = 1.5; for (let k = -3; k <= 3; k++) { c.beginPath(); c.moveTo(neck[0] + k * 8, neck[1] - 4); c.lineTo(neck[0] + k * 8, neck[1] + 12); c.stroke() } }
    if (cos.collar === 'falling') { c.fillStyle = '#f2eee4'; poly(c, [[neck[0] - 20, neck[1] + 2], [neck[0] + 24, neck[1] + 2], [neck[0] + 30, neck[1] + 22], [neck[0] - 14, neck[1] + 24]], '#f2eee4') }
    if (cos.collar === 'stand') { c.fillStyle = shade(top, -0.1); c.fillRect(neck[0] - 12, neck[1] - 4, 26, 12) }
    if (cos.hat === 'veil') { c.fillStyle = hgrad(c, neck[0] - 40, neck[0] + 40, shade(cos.hatCol, 0.1), cos.hatCol, shade(cos.hatCol, -0.3)); c.beginPath(); c.moveTo(neck[0] - 30, neck[1] - 30); c.quadraticCurveTo(neck[0] - 50, neck[1] + 40, hip[0] - 34, lerp(neck[1], hip[1], 0.6)); c.lineTo(neck[0] + 4, neck[1] + 20); c.closePath(); c.fill() }
    // head
    head(c, neck, lean, pz, o.face || {}, P, cos)
    // items held in front
    if (pz.rifle) rifle(c, pz.rifle, 'near')
    if (pz.item === 'drum' && pz.drumAt) drum(c, pz.drumAt)
    if (pz.holdAt && o.holdFn) { c.save(); c.translate(pz.holdAt[0], pz.holdAt[1]); if (f < 0) c.scale(-1, 1); o.holdFn(c); c.restore() }
    if (pz.item === 'bundle') { const hd = [neck[0] + Math.sin(lean) * P.hr * 2, neck[1] - P.hr * 2.05]; c.save(); c.translate(hd[0], hd[1]); c.rotate(-0.06); for (let k = 0; k < 5; k++) { c.strokeStyle = shade('#6a4a2a', k % 2 ? -0.2 : 0.05); c.lineWidth = 8; c.lineCap = 'round'; c.beginPath(); c.moveTo(-52, -k * 6); c.lineTo(58, -k * 6.5 + 3); c.stroke() } c.restore() }
    // near arm
    limb(c, [sh, eN, hn], P.aw, sleeve); hand(c, hn, P, cos.skin)
    if (pz.item === 'drum') { c.strokeStyle = '#d8c8a0'; c.lineWidth = 4; c.lineCap = 'round'; c.beginPath(); c.moveTo(hn[0], hn[1]); c.lineTo(hn[0] + 26, hn[1] + 14); c.stroke() }
    if (cos.cane && o.pose?.name === 'walk') { c.strokeStyle = '#2a1d12'; c.lineWidth = 5; c.beginPath(); c.moveTo(hn[0], hn[1]); c.lineTo(hn[0] + 30, 0); c.stroke() }
    c.restore()
    // positions back in world space, for props and effects
    const W2 = p => [x + p[0] * s * f, gy + p[1] * s]
    const head0 = [neck[0], neck[1] - P.hr * 0.95]
    const out = { neck: W2(neck), head: W2(head0), hn: W2(hn), hf: W2(hf), hip: W2(hip), hat: W2([head0[0], head0[1] - P.hr * 0.9]) }
    if (pz.rifle) { const r = pz.rifle; out.muzzle = W2([r.butt[0] + Math.cos(r.ang) * 175, r.butt[1] + Math.sin(r.ang) * 175]) }
    return out
  }
  function rifle(c, r, part) {
    const along = d => [r.butt[0] + Math.cos(r.ang) * d, r.butt[1] + Math.sin(r.ang) * d]
    c.lineCap = 'round'
    if (part === 'near') {
      c.strokeStyle = '#6a3c1e'; c.lineWidth = 8; c.beginPath(); c.moveTo(...r.butt); c.lineTo(...along(108)); c.stroke()
      c.strokeStyle = '#2a2a30'; c.lineWidth = 4; c.beginPath(); c.moveTo(...along(52)); c.lineTo(...along(175)); c.stroke()
      c.strokeStyle = 'rgba(255,230,190,0.3)'; c.lineWidth = 1.5; c.beginPath(); c.moveTo(...along(60)); c.lineTo(...along(170)); c.stroke()
    }
  }
  function drum(c, at) { c.save(); c.translate(at[0], at[1]); c.fillStyle = hgrad(c, -30, 30, '#8a5a32', '#6a3c1e', '#3a2412'); c.fillRect(-26, -16, 52, 34); ell(c, 0, -16, 26, 7, 0, '#e8dcc0'); c.strokeStyle = '#d8c8a0'; c.lineWidth = 1.5; for (let k = -2; k <= 2; k++) { c.beginPath(); c.moveTo(k * 10, -12); c.lineTo(k * 10 + 6, 16); c.stroke() } c.restore() }

  function head(c, neck, lean, pz, fc, P, cos) {
    const r = P.hr, look = fc.look ?? pz.look ?? 0, mood = fc.mood || 'calm'
    const tilt = lean - look * 0.55 + (fc.tilt || 0)
    c.save(); c.translate(neck[0], neck[1]); c.rotate(tilt)
    c.fillStyle = shade(cos.skin, -0.25); c.fillRect(-r * 0.25, -r * 0.5, r * 0.5, r * 0.6)
    c.translate(0, -r * 0.95)
    // hair behind the head
    if (cos.hair && cos.hat !== 'turban' && cos.hat !== 'pilot') { c.fillStyle = cos.hair; ell(c, -r * 0.3, -r * 0.2, r * 0.75, r * 0.85, 0.2, cos.hair); if (cos.skirt && cos.hat !== 'veil') ell(c, -r * 0.8, r * 0.1, r * 0.35, r * 0.4, 0, cos.hair) }
    // face shape
    c.fillStyle = rgrad(c, r * 0.3, -r * 0.3, r * 0.1, r * 1.1, shade(cos.skin, 0.15), cos.skin, shade(cos.skin, -0.3))
    c.beginPath(); c.moveTo(-r * 0.8, -r * 0.3); c.quadraticCurveTo(-r * 0.7, -r * 1.05, r * 0.2, -r * 0.98); c.quadraticCurveTo(r * 0.9, -r * 0.8, r * 0.92, -r * 0.1); c.lineTo(r * 1.12, r * 0.2); c.lineTo(r * 0.92, r * 0.32); c.quadraticCurveTo(r * 0.95, r * 0.75, r * 0.55, r * 0.95); c.quadraticCurveTo(-r * 0.2, r * 1.05, -r * 0.6, r * 0.55); c.closePath(); c.fill()
    if (cos.hair && !cos.hat) { c.fillStyle = cos.hair; c.beginPath(); c.moveTo(-r * 0.85, -r * 0.1); c.quadraticCurveTo(-r * 0.8, -r * 1.15, r * 0.3, -r * 1.05); c.quadraticCurveTo(r * 0.8, -r * 0.95, r * 0.75, -r * 0.6); c.quadraticCurveTo(r * 0.2, -r * 0.8, -r * 0.4, -r * 0.5); c.closePath(); c.fill() }
    ell(c, -r * 0.35, r * 0.05, r * 0.14, r * 0.22, 0, shade(cos.skin, -0.25))
    // eye, brow
    const wide = mood === 'alarm' ? 1.4 : mood === 'happy' ? 0.7 : 1, dart = fc.dart || 0
    const ex = r * 0.55 + dart * r * 0.06, ey = -r * 0.12 - look * r * 0.06
    if (fc.closed) { c.strokeStyle = '#1b120c'; c.lineWidth = 2; c.beginPath(); c.moveTo(r * 0.45, -r * 0.1); c.lineTo(r * 0.66, -r * 0.08); c.stroke() }
    else {
      if (mood === 'alarm') ell(c, r * 0.55, -r * 0.12, r * 0.16, r * 0.16, 0, '#f0e8dc')
      ell(c, ex, ey, r * 0.09, r * 0.1 * wide, 0, '#1b120c'); ell(c, ex + r * 0.03, ey - r * 0.04, r * 0.03, r * 0.03, 0, 'rgba(255,255,255,0.8)')
    }
    if (cos.glasses) { c.strokeStyle = '#2a2420'; c.lineWidth = 2; ell(c, r * 0.56, -r * 0.12, r * 0.2, r * 0.17, 0); c.stroke(); c.beginPath(); c.moveTo(r * 0.36, -r * 0.14); c.lineTo(-r * 0.3, -r * 0.18); c.stroke() }
    const brow = { calm: [0.33, 0.32], alarm: [0.45, 0.4], angry: [0.24, 0.36], sad: [0.38, 0.27], happy: [0.36, 0.36], stern: [0.28, 0.33] }[mood] || [0.33, 0.32]
    c.strokeStyle = cos.hair || '#3a2618'; c.lineWidth = 3; c.lineCap = 'round'; c.beginPath(); c.moveTo(r * 0.38, -r * brow[1]); c.lineTo(r * 0.74, -r * brow[0]); c.stroke()
    // mouth
    const talk = fc.talk ? Math.abs(Math.sin(fc.talk * 11)) : 0, mo = fc.mouth || (mood === 'alarm' ? 'open' : mood === 'happy' ? 'smile' : 'line')
    if (mo === 'open' || mo === 'shout' || talk > 0.3) { const a = mo === 'shout' ? 1.4 : mo === 'open' ? 1 : talk; ell(c, r * 0.7, r * 0.6, r * 0.12, r * 0.13 * a, 0, '#3a1a14') }
    else if (mo === 'smile') { c.strokeStyle = '#4a2418'; c.lineWidth = 2.2; c.beginPath(); c.moveTo(r * 0.52, r * 0.56); c.quadraticCurveTo(r * 0.7, r * 0.72, r * 0.86, r * 0.52); c.stroke() }
    else if (mo === 'frown') { c.strokeStyle = '#4a2418'; c.lineWidth = 2.2; c.beginPath(); c.moveTo(r * 0.52, r * 0.68); c.quadraticCurveTo(r * 0.7, r * 0.56, r * 0.86, r * 0.66); c.stroke() }
    else { c.strokeStyle = '#4a2418'; c.lineWidth = 2; c.beginPath(); c.moveTo(r * 0.56, r * 0.62); c.lineTo(r * 0.84, r * 0.6); c.stroke() }
    if (cos.moustache) { ell(c, r * 0.72, r * 0.42, r * 0.3, r * 0.1, -0.15, cos.moustache) }
    if (cos.beard) { c.fillStyle = cos.beard; c.beginPath(); c.moveTo(-r * 0.3, r * 0.2); c.quadraticCurveTo(-r * 0.2, r * 1.2, r * 0.5, r * 1.15); c.quadraticCurveTo(r * 0.95, r * 0.95, r * 0.9, r * 0.5); c.lineTo(r * 0.55, r * 0.75); c.quadraticCurveTo(r * 0.1, r * 0.8, -r * 0.3, r * 0.2); c.fill() }
    ell(c, r * 0.6, -r * 0.5, r * 0.25, r * 0.14, 0.3, 'rgba(255,200,150,0.25)')
    hat(c, r, cos)
    c.restore()
  }
  function hat(c, r, cos) {
    const col = cos.hatCol, d = cos.hat ? shade(col, -0.3) : null
    switch (cos.hat) {
      case 'felt': { const hy = -r * 0.7; c.fillStyle = vgrad(c, hy - r * 0.9, hy, shade(col, 0.18), col); c.beginPath(); c.moveTo(-r * 0.7, hy); c.quadraticCurveTo(-r * 0.75, hy - r * 0.95, 0, hy - r * 0.95); c.quadraticCurveTo(r * 0.75, hy - r * 0.95, r * 0.72, hy); c.closePath(); c.fill(); c.fillStyle = '#21180f'; c.fillRect(-r * 0.71, hy - r * 0.22, r * 1.42, r * 0.2); ell(c, r * 0.05, hy, r * 1.32, r * 0.2, 0, d); break }
      case 'turban': { c.fillStyle = vgrad(c, -r * 1.5, -r * 0.3, shade(col, 0.15), col, d); ell(c, -r * 0.05, -r * 0.72, r * 0.98, r * 0.62, -0.05); c.fill(); c.strokeStyle = d; c.lineWidth = 2.5; for (let k = 0; k < 3; k++) { c.beginPath(); c.ellipse(-r * 0.05, -r * 0.72 + k * 8 - 8, r * 0.9, r * 0.32, -0.25 + k * 0.12, Math.PI * 1.05, Math.PI * 1.95); c.stroke() } if (cos.plume) { ell(c, r * 0.2, -r * 1.4, r * 0.1, r * 0.4, 0.2, '#f4efe4') } break }
      case 'cap': { c.fillStyle = vgrad(c, -r * 1.2, -r * 0.4, shade(col, 0.15), col); ell(c, -r * 0.05, -r * 0.62, r * 0.88, r * 0.42, 0); c.fill(); ell(c, r * 0.65, -r * 0.42, r * 0.5, r * 0.1, 0.1, d); break }
      case 'veil': { c.fillStyle = vgrad(c, -r * 1.3, r, shade(col, 0.15), col, d); c.beginPath(); c.moveTo(r * 0.55, -r * 0.95); c.quadraticCurveTo(-r * 0.2, -r * 1.45, -r * 1.0, -r * 0.6); c.quadraticCurveTo(-r * 1.3, r * 0.6, -r * 0.9, r * 1.4); c.lineTo(-r * 0.3, r * 1.2); c.quadraticCurveTo(-r * 0.7, 0, -r * 0.4, -r * 0.6); c.quadraticCurveTo(r * 0.1, -r * 0.95, r * 0.55, -r * 0.95); c.fill(); break }
      case 'capotain': { c.fillStyle = vgrad(c, -r * 2.6, -r * 0.6, shade(col, 0.2), col); c.beginPath(); c.moveTo(-r * 0.72, -r * 0.62); c.lineTo(-r * 0.5, -r * 2.2); c.quadraticCurveTo(0, -r * 2.35, r * 0.5, -r * 2.2); c.lineTo(r * 0.72, -r * 0.62); c.closePath(); c.fill(); c.fillStyle = '#5a4a2a'; c.fillRect(-r * 0.7, -r * 0.95, r * 1.4, r * 0.18); ell(c, 0, -r * 0.62, r * 1.3, r * 0.2, 0, d); break }
      case 'brim': { c.fillStyle = vgrad(c, -r * 1.7, -r * 0.6, shade(col, 0.2), col); c.beginPath(); c.moveTo(-r * 0.7, -r * 0.65); c.quadraticCurveTo(-r * 0.7, -r * 1.6, 0, -r * 1.6); c.quadraticCurveTo(r * 0.7, -r * 1.6, r * 0.7, -r * 0.65); c.closePath(); c.fill(); ell(c, 0, -r * 0.66, r * 1.55, r * 0.26, -0.06, d); break }
      case 'bonnet': { c.fillStyle = vgrad(c, -r * 1.2, r * 0.3, '#ffffff', col, shade(col, -0.15)); c.beginPath(); c.moveTo(r * 0.5, -r * 0.95); c.quadraticCurveTo(-r * 0.3, -r * 1.3, -r * 0.95, -r * 0.5); c.quadraticCurveTo(-r * 1.0, r * 0.2, -r * 0.55, r * 0.35); c.quadraticCurveTo(-r * 0.4, -r * 0.4, r * 0.15, -r * 0.75); c.closePath(); c.fill(); break }
      case 'boater': { c.fillStyle = vgrad(c, -r * 1.3, -r * 0.6, shade(col, 0.2), col); c.fillRect(-r * 0.68, -r * 1.28, r * 1.36, r * 0.62); c.fillStyle = '#2a1d3a'; c.fillRect(-r * 0.68, -r * 0.86, r * 1.36, r * 0.2); ell(c, 0, -r * 0.66, r * 1.3, r * 0.17, 0, shade(col, -0.15)); ell(c, 0, -r * 1.28, r * 0.68, r * 0.08, 0, shade(col, 0.25)); break }
      case 'bowler': case 'fedora': { c.fillStyle = vgrad(c, -r * 1.5, -r * 0.6, shade(col, 0.18), col); c.beginPath(); c.moveTo(-r * 0.7, -r * 0.66); c.quadraticCurveTo(-r * 0.75, -r * 1.5, 0, -r * 1.45); c.quadraticCurveTo(r * 0.75, -r * 1.5, r * 0.7, -r * 0.66); c.closePath(); c.fill(); if (cos.hat === 'fedora') { c.strokeStyle = d; c.lineWidth = 3; c.beginPath(); c.moveTo(-r * 0.2, -r * 1.45); c.lineTo(r * 0.1, -r * 1.2); c.stroke() } c.fillStyle = '#14110e'; c.fillRect(-r * 0.7, -r * 0.88, r * 1.4, r * 0.18); ell(c, r * 0.05, -r * 0.66, r * 1.15, r * 0.16, -0.05, d); break }
      case 'cloche': { c.fillStyle = vgrad(c, -r * 1.3, -r * 0.3, shade(col, 0.2), col); c.beginPath(); c.moveTo(-r * 0.95, -r * 0.2); c.quadraticCurveTo(-r * 0.9, -r * 1.4, r * 0.1, -r * 1.3); c.quadraticCurveTo(r * 0.95, -r * 1.2, r * 0.9, -r * 0.5); c.quadraticCurveTo(r * 0.2, -r * 0.7, -r * 0.95, -r * 0.2); c.fill(); break }
      case 'police': case 'navy': { c.fillStyle = vgrad(c, -r * 1.4, -r * 0.6, shade(col, 0.2), col); c.beginPath(); c.moveTo(-r * 0.75, -r * 0.72); c.quadraticCurveTo(-r * 0.9, -r * 1.25, 0, -r * 1.3); c.quadraticCurveTo(r * 1.0, -r * 1.3, r * 0.82, -r * 0.8); c.closePath(); c.fill(); c.fillStyle = cos.hat === 'navy' ? '#14110e' : '#0e0c0a'; c.fillRect(-r * 0.72, -r * 0.86, r * 1.5, r * 0.18); c.fillStyle = '#14110e'; c.beginPath(); c.moveTo(r * 0.4, -r * 0.7); c.quadraticCurveTo(r * 1.1, -r * 0.72, r * 1.15, -r * 0.5); c.lineTo(r * 0.4, -r * 0.6); c.fill(); ell(c, r * 0.35, -r * 0.94, r * 0.1, r * 0.1, 0, '#d8b85a'); break }
      case 'sailor': { c.fillStyle = vgrad(c, -r * 1.3, -r * 0.6, '#ffffff', col); c.beginPath(); c.moveTo(-r * 0.7, -r * 0.7); c.quadraticCurveTo(-r * 0.6, -r * 1.3, 0, -r * 1.25); c.quadraticCurveTo(r * 0.6, -r * 1.3, r * 0.7, -r * 0.7); c.closePath(); c.fill(); ell(c, 0, -r * 0.72, r * 0.85, r * 0.16, 0, shade(col, -0.08)); break }
      case 'pilot': { c.fillStyle = vgrad(c, -r * 1.2, r * 0.5, shade(col, 0.2), col, d); c.beginPath(); c.moveTo(r * 0.4, -r * 0.95); c.quadraticCurveTo(-r * 0.5, -r * 1.25, -r * 0.95, -r * 0.4); c.quadraticCurveTo(-r * 1.0, r * 0.4, -r * 0.5, r * 0.65); c.lineTo(-r * 0.2, r * 0.4); c.quadraticCurveTo(-r * 0.4, -r * 0.4, r * 0.45, -r * 0.6); c.closePath(); c.fill(); ell(c, r * 0.3, -r * 0.78, r * 0.26, r * 0.15, 0, '#6a8aa0'); c.strokeStyle = '#3a2a1a'; c.lineWidth = 3; c.stroke(); break }
    }
  }
  function lying(c, P, cos, o) {
    // a body lying on its side (for the wounded and the dead: shown small and covered where it matters)
    c.fillStyle = hgrad(c, -120, 120, shade(cos.shirt, 0.1), cos.shirt, shade(cos.shirt, -0.3))
    ell(c, 0, -18, 110, 22, 0); c.fill(); ell(c, 120, -20, 22, 20, 0, cos.skin); ell(c, -130, -12, 50, 13, 0, cos.pants)
  }

  // ---- a crowd: list of {x, s, cos, pose, f, face}, drawn back to front, the far ones hazier and smaller
  function crowd(c, gy, people, o = {}) {
    const sorted = people.slice().sort((a, b) => (a.z || 0) - (b.z || 0))
    for (const p of sorted) person(c, p.x, gy + (p.z || 0) * (o.zy ?? 60), (p.s || o.s || 0.8) * (1 + (p.z || 0) * (o.zs ?? 0.18)), { f: p.f, cos: p.cos, pose: p.pose, face: p.face, fade: (o.fade ?? 0.35) * (1 - (p.z || 0)), hazeCol: o.haze || '#b9b0a2', holdFn: p.holdFn })
  }

  Object.assign(PK, { ik, person, crowd, COS, costume, poseOf: pose, BODY: BASE })
})(window.PK)
