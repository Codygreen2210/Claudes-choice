// How to draw a serpent dragon (advanced): an original Eastern dragon in graphite, recorded with timelapse.js.
// The body is geometry, not freehand: a spine curve, a width along it, and a cylinder wrapped around it.
// Scales, belly plates and spines are laid on that cylinder, so they narrow toward the edges and take
// light from the top left like a real round form would. Space is 1000 x 1300.
(function (root) {
  function build(TL) {
    // ---------------------------------------------------------------- helpers
    const curve = (P, n = 10, closed = false) => {
      const out = [], m = P.length, get = i => closed ? P[(i + m) % m] : P[Math.max(0, Math.min(m - 1, i))]
      for (let i = 0; i < (closed ? m : m - 1); i++) {
        const p0 = get(i - 1), p1 = get(i), p2 = get(i + 1), p3 = get(i + 2)
        for (let k = 0; k < n; k++) {
          const t = k / n, t2 = t * t, t3 = t2 * t
          out.push([0, 1].map(j => 0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3)))
        }
      }
      out.push(closed ? P[0] : P[m - 1]); return out
    }
    const circle = (cx, cy, r, a0 = -2.2, turns = 1.03, ry = r) => {
      const out = []; for (let i = 0; i <= 48; i++) { const a = a0 + turns * 2 * Math.PI * i / 48; out.push([cx + r * Math.cos(a), cy + ry * Math.sin(a)]) } return out
    }
    const add = (a, b, k = 1) => [a[0] + b[0] * k, a[1] + b[1] * k]
    const len = v => Math.hypot(v[0], v[1]), unit = v => { const l = len(v) || 1; return [v[0] / l, v[1] / l] }
    const perp = v => [v[1], -v[0]]                                  // left of travel, on screen (y down)
    const rot = (v, a) => [v[0] * Math.cos(a) - v[1] * Math.sin(a), v[0] * Math.sin(a) + v[1] * Math.cos(a)]
    // a polyline as a closed tube outline with a width at each point
    const tube = (P, W) => {
      const L = [], R = []
      P.forEach((p, i) => { const d = unit([P[Math.min(i + 1, P.length - 1)][0] - P[Math.max(i - 1, 0)][0], P[Math.min(i + 1, P.length - 1)][1] - P[Math.max(i - 1, 0)][1]]), n = perp(d), w = W(i / (P.length - 1)) / 2; L.push(add(p, n, w)); R.push(add(p, n, -w)) })
      return { left: L, right: R, poly: [...L, ...R.slice().reverse()] }
    }
    // a flame: two edges meeting in a curling tip
    const flame = (base, dir, length, width, curl) => {
      const d = unit(dir), n = perp(d), P = (a, b) => add(add(base, d, length * a), n, b)
      const bend = a => curl * Math.sin(Math.PI * a * 1.1)          // the S-bend of the centre line
      return curve([P(0, width / 2), P(0.3, width * 0.42 + bend(0.3)), P(0.6, width * 0.22 + bend(0.6)), P(0.86, width * 0.06 + bend(0.86)), P(1, curl * 0.2 - width * 0.12),
        P(0.8, bend(0.8) - width * 0.14), P(0.55, bend(0.55) - width * 0.3), P(0.28, bend(0.28) - width * 0.44), P(0, -width / 2)], 6)
    }

    // ---------------------------------------------------------------- the spine and body cylinder
    const SPINE_PTS = [[455, 335], [560, 272], [700, 252], [820, 318], [862, 458], [806, 598], [662, 682], [500, 722], [376, 804],
      [326, 934], [388, 1064], [540, 1124], [702, 1092], [806, 994], [826, 862], [768, 752], [700, 636], [648, 552], [640, 492], [672, 462]]
    const raw = curve(SPINE_PTS, 24)
    const SP = [raw[0]], S = [0]                                        // resample every 3 px of arc length
    { let acc = 0; for (let i = 1; i < raw.length; i++) { acc += len([raw[i][0] - raw[i - 1][0], raw[i][1] - raw[i - 1][1]]); if (acc - S[S.length - 1] >= 3) { SP.push(raw[i]); S.push(acc) } } }
    const LEN = S[S.length - 1]
    const idx = s => Math.max(0, Math.min(SP.length - 1, Math.round(s / LEN * (SP.length - 1))))
    const width = s => { const u = s / LEN; return 18 + 132 * Math.pow(1 - u, 0.8) * Math.min(1, 0.8 + u * 3) }
    const frame = s => {
      const i = idx(s), a = SP[Math.max(0, i - 2)], b = SP[Math.min(SP.length - 1, i + 2)]
      const t = unit([b[0] - a[0], b[1] - a[1]]); return { p: SP[i], t, n: perp(t), w: width(s) }
    }
    // a point on the cylinder: th in [-pi/2, pi/2], positive toward the back (dorsal), negative toward the belly
    const at = (s, th) => { const f = frame(s); return add(f.p, f.n, f.w / 2 * Math.sin(th)) }
    const edge = (s0, s1, th, step = 6) => { const o = []; for (let s = s0; s <= s1; s += step) o.push(at(s, th)); o.push(at(s1, th)); return o }
    const bodyPoly = (s0, s1) => [...edge(s0, s1, Math.PI / 2, 8), ...edge(s0, s1, -Math.PI / 2, 8).reverse()]
    // light from the top left, a little in front: how lit is the surface at (s, th)? 0 dark .. 1 lit
    const LIGHT = (() => { const v = [-0.5, -0.62, 0.6], l = Math.hypot(...v); return v.map(x => x / l) })()
    const lit = (s, th) => { const f = frame(s); return Math.max(0, (f.n[0] * LIGHT[0] + f.n[1] * LIGHT[1]) * Math.sin(th) + LIGHT[2] * Math.cos(th)) }

    // the tail's last stretch passes behind the upper coil
    const TAIL_S = LEN * 0.74
    const FRONT_BODY = bodyPoly(0, LEN * 0.6)
    const inTail = s => s > TAIL_S

    // ---------------------------------------------------------------- head (facing left)
    const H = {
      skull: [[432, 262], [400, 236], [360, 230], [328, 244], [310, 268]],
      snout: [[310, 268], [270, 284], [228, 300], [190, 316], [166, 328]],
      nose: [[166, 328], [154, 342], [160, 358], [178, 364]],
      upperLip: [[178, 364], [212, 370], [252, 378], [302, 386], [350, 394], [394, 404]],
      jaw: [[394, 404], [350, 432], [296, 460], [244, 480], [204, 486], [182, 474]],
      lowerLip: [[182, 474], [202, 458], [252, 442], [310, 422], [360, 410], [394, 404]],
      cheek: [[394, 404], [424, 380], [440, 348], [436, 300], [432, 262]],
      throat: [[350, 432], [410, 436], [462, 420], [500, 402]],
      brow: [[378, 282], [348, 270], [318, 278], [298, 292]],
      eye: [[306, 302], [330, 290], [356, 294], [374, 305], [352, 312], [326, 312]],
      nostril: [[180, 340], [192, 334], [200, 344], [188, 350]],
    }
    const HEAD_POLY = curve([...H.skull, ...H.snout.slice(1), ...H.nose.slice(1), ...H.upperLip.slice(1), ...H.jaw.slice(1),
      [300, 470], [400, 438], [462, 420], [478, 392], [452, 352], [440, 300]], 4, true)
    const JAW_POLY = curve([...H.jaw, ...H.lowerLip.slice(1, -1)], 5, true)
    const THROAT_POLY = curve([[350, 432], [410, 436], [462, 420], [478, 392], [424, 380], [394, 404]], 5, true)
    const SOCKET = curve([[378, 282], [348, 270], [318, 278], [298, 292], [306, 302], [330, 290], [356, 294], [374, 305]], 5, true)
    const CHEEK = [[372, 316], [420, 300], [436, 350], [420, 386], [392, 400], [360, 390]]
    const MOUTH = curve([...H.upperLip, ...H.lowerLip.slice().reverse().slice(1, -1)], 6, true)
    const fang = (base, dir, h, w) => { const d = unit(dir), n = perp(d); return [add(base, n, w / 2), add(add(base, d, h * 0.6), n, w * 0.2), add(base, d, h), add(base, n, -w / 2)] }
    const TEETH = [fang([204, 368], [-0.15, 1], 30, 13), fang([240, 374], [0, 1], 14, 8), fang([276, 380], [0, 1], 18, 9), fang([318, 388], [0.1, 1], 13, 7), fang([352, 394], [0, 1], 9, 6),
      fang([212, 463], [0.1, -1], 26, 12), fang([256, 447], [0, -1], 13, 8), fang([300, 430], [0, -1], 14, 8), fang([340, 418], [0, -1], 9, 6)].map(p => curve(p, 4, true))
    const TONGUE_C = curve([[372, 418], [300, 428], [220, 438], [150, 440], [118, 428]], 8)
    const TONGUE = tube(TONGUE_C, u => 16 * (1 - u * 0.7))
    const FORK = [[[118, 428], [96, 414]], [[120, 432], [100, 450]]]

    const HORN_A = curve([[416, 252], [460, 206], [520, 166], [582, 142], [626, 138]], 10)
    const HORN_B = curve([[378, 240], [400, 190], [440, 150], [484, 118], [510, 96]], 10)
    const hornA = tube(HORN_A, u => 26 * (1 - u) + 2), hornB = tube(HORN_B, u => 20 * (1 - u) + 2)
    const TINE = curve([[520, 166], [528, 124], [544, 98]], 6), tine = tube(TINE, u => 12 * (1 - u) + 1)

    const MANE = [
      flame([430, 256], [0.9, -0.6], 150, 56, -22), flame([438, 292], [1, -0.25], 176, 60, 20), flame([444, 334], [1, 0.05], 168, 58, -20),
      flame([446, 372], [1, 0.35], 150, 54, 18), flame([432, 404], [0.75, 0.8], 124, 46, -16), flame([404, 426], [0.3, 1], 96, 38, 14)]
    const BROW_SPIKES = [flame([372, 276], [0.55, -1], 44, 18, 6), flame([350, 270], [0.3, -1], 36, 16, -5), flame([392, 262], [0.8, -0.8], 40, 16, 6)]
    const BEARD = [flame([214, 482], [-0.2, 1], 72, 22, 8), flame([250, 474], [0, 1], 86, 24, -10), flame([290, 462], [0.1, 1], 70, 22, 10), flame([330, 446], [0.3, 1], 58, 20, -8)]
    const WHISKER_A = curve([[182, 338], [136, 362], [98, 430], [92, 540], [118, 640], [170, 704], [214, 716]], 14)
    const WHISKER_B = curve([[196, 352], [150, 392], [128, 470], [146, 560], [196, 614], [262, 636], [300, 628]], 14)

    // ---------------------------------------------------------------- legs
    // a leg from explicit joints: a heavy upper limb, a slimmer lower limb, four toes fanned around `hand`
    function leg(root, elbow, wrist, hand, spread, flip, thick) {
      const arm = curve([root, elbow, wrist], 10)
      const A = tube(arm, u => thick * (0.62 + 0.38 * Math.sin(Math.PI * Math.min(1, u * 1.7 + 0.2))) * (u < 0.5 ? 1 : 1 - (u - 0.5) * 0.9))
      const toes = [], claws = [], h = unit(hand)
      for (let k = 0; k < 4; k++) {
        const d = rot(h, (k - 1.5) * spread), base = add(wrist, d, thick * 0.12), knuckle = add(base, d, thick * 0.55)
        const tip = add(add(knuckle, d, thick * 0.5), perp(d), thick * 0.24 * flip)
        toes.push(tube(curve([base, add(add(base, d, thick * 0.22), perp(d), -2 * flip), knuckle], 4), u => thick * 0.3 * (1 - u * 0.35)))
        claws.push(curve([add(knuckle, perp(d), thick * 0.09), add(add(knuckle, d, thick * 0.26), perp(d), thick * 0.14 * flip), tip, add(add(knuckle, d, thick * 0.18), perp(d), -thick * 0.02 * flip), add(knuckle, perp(d), -thick * 0.08)], 5))
      }
      return { arm: A, toes, claws, root, elbow, wrist }
    }
    const LEG_F = leg([612, 318], [668, 424], [590, 478], [-0.85, 0.55], 0.4, -1, 62)
    const LEG_B = leg([470, 1146], [392, 1216], [460, 1262], [-1, 0.12], 0.36, -1, 58)
    const LEGS = [LEG_F, LEG_B]
    const LEG_POLYS = LEGS.flatMap(l => [l.arm.poly, ...l.toes.map(t => t.poly), ...l.claws])

    // things in front of the body: head, legs; the tail also hides behind the front coil
    const FRONT = [HEAD_POLY, ...LEG_POLYS, ...MANE]
    const bodyMask = s => inTail(s) ? [...FRONT, FRONT_BODY] : FRONT
    const EVERYTHING = [HEAD_POLY, ...LEG_POLYS, bodyPoly(0, LEN), ...MANE, hornA.poly, hornB.poly]

    // ---------------------------------------------------------------- the lesson
    const INK = '#232226', LEAD = '#2e2d33'
    const R = TL.recorder({ lift: 0.14, stepPause: 0.25, hand: 0.8, seed: 3 })
    let vs = 11; const vary = () => (vs = (vs * 16807) % 2147483647) / 2147483647 - 0.5   // scale-to-scale variation
    const g = (pts, o = {}) => R.ink(pts, { color: LEAD, width: 4.2, grain: 0.35, ...o })
    let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647 - 0.5
    const sketch = (pts, passes = 3, o = {}) => { for (let k = 0; k < passes; k++) { const dx = rnd() * 5, dy = rnd() * 5; R.pencil(pts.map(p => [p[0] + dx + rnd() * 1.5, p[1] + dy + rnd() * 1.5]), { speed: 650, alpha: 0.75, lift: 0.1, ...o }) } }

    R.step('The line of action', 'Start with one long S-curve. It is the dragon\'s spine and it sets the whole pose. Eastern dragons are serpents, so let the body coil back through itself.')
    R.pencil(curve(SPINE_PTS, 10), { width: 4 })

    R.step('Plan the thickness', 'Drop circles along the spine: widest behind the head, shrinking steadily toward the tail. This keeps the body from swelling and pinching by accident.')
    for (let s = 0; s < LEN * 0.97; s += width(s) * 0.9 + 20) { const f = frame(s); R.pencil(circle(f.p[0], f.p[1], f.w / 2), { lift: 0.08 }) }

    R.step('Wrap it into a tube', 'Connect the circles on both sides. Now the body reads as one long tube twisting in space. Where the tail goes behind the upper coil, keep drawing lightly through it.')
    R.pencil(edge(0, LEN, Math.PI / 2, 10)).pencil(edge(0, LEN, -Math.PI / 2, 10))

    R.step('Block in the head', 'A circle for the skull and a long tapering wedge for the snout. The snout runs about twice the length of the skull.')
    sketch(circle(374, 300, 72)); sketch([[330, 244], [166, 326], [178, 366], [394, 404]]); sketch([[300, 250], [300, 400]], 2); sketch([[166, 330], [440, 330]], 2)

    R.step('Open the jaw', 'The lower jaw hinges just below and behind the eye. Swing it down about 30 degrees. A wide-open mouth makes the dragon feel alive.')
    sketch([[420, 400], [184, 478]]); sketch(curve([[184, 478], [250, 440], [394, 404]], 6)); sketch(circle(410, 395, 18), 2); sketch([[394, 404], [470, 420], [500, 402]], 2)

    R.step('Rough in the legs', 'Three bends for each leg: shoulder, elbow, wrist. Then fan out four toes. Keep the legs short and heavy compared with the long body.')
    for (const l of LEGS) { sketch(curve([l.root, l.elbow, l.wrist], 6), 2, { width: 4 }); sketch(circle(l.root[0], l.root[1], 30), 2); sketch(circle(l.elbow[0], l.elbow[1], 22), 2); sketch(circle(l.wrist[0], l.wrist[1], 16), 2) }

    R.step('Ink the head', 'Go over the guides with a sharp, confident line. Press harder under the jaw and along the brow, where the form turns away from the light.')
    for (const k of ['skull', 'snout', 'nose', 'upperLip', 'jaw', 'lowerLip', 'cheek', 'throat']) g(curve(H[k], 8), { width: k === 'jaw' || k === 'throat' ? 5.2 : 4.4 })
    g(curve(H.nostril, 5, true), { width: 3.4 })
    for (let i = 0; i < 4; i++) g(curve([[250 + i * 32, 342], [256 + i * 32, 354], [250 + i * 32, 366]], 4), { width: 1.8, lift: 0.05 })   // lip wrinkles

    R.step('The eye', 'An almond shape tucked under a heavy brow ridge. A dark iris, a slit pupil and one small bright highlight are what make it look back at you.')
    g(curve(H.brow, 8), { width: 7 })
    g(curve(H.eye, 6, true), { width: 3.6 })
    R.fill(circle(338, 301, 10, 0, 1), { layer: 'deep', color: '#3a393f', width: 6, alpha: 0.9 })
    g([[338, 291], [340, 311]], { width: 3.4, color: '#0e0e10', layer: 'deep', hand: 0 })
    R.brush([[344, 297], [345, 298]], { layer: 'top', color: '#fbfaf6', width: 4.5, alpha: 1 })
    for (const b of BROW_SPIKES) g(b, { width: 2.6, lift: 0.05 })
    // small scales across the cheek and down the snout, following the head's surface
    for (let y = 318, row = 0; y < 392; y += 13, row++) for (let x = 376 + (row % 2) * 6; x < 440; x += 13) {
      const inside = (p, poly) => { let c = false; for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) { const a = poly[i], b = poly[j]; if ((a[1] > p[1]) !== (b[1] > p[1]) && p[0] < (b[0] - a[0]) * (p[1] - a[1]) / (b[1] - a[1]) + a[0]) c = !c } return c }
      if (inside([x, y], CHEEK)) g(curve([[x - 6, y - 3], [x, y + 4], [x + 6, y - 3]], 3), { width: 1.6, lift: 0.02 })
    }
    for (let i = 0; i < 7; i++) { const x = 200 + i * 17, y = 318 - i * 3.5; g(curve([[x - 7, y], [x, y - 7], [x + 7, y]], 3), { width: 1.8, lift: 0.03 }) }

    R.step('Fangs and tongue', 'Long fangs at the front, smaller teeth behind them. A forked tongue curls out past the lips. Draw the teeth now so the dark of the mouth can go around them later.')
    for (const t of TEETH) g(t, { width: 2.6, lift: 0.06 })
    g(curve(TONGUE.left, 1))
    g(curve(TONGUE.right, 1))
    for (const f of FORK) g(f, { width: 3 })

    R.step('Antler horns', 'Two horns sweep back from the top of the skull, with a small tine branching off. Rings around them show they are round, not flat cut-outs.')
    for (const h of [hornB, hornA, tine]) { g(h.left, { mask: h === hornB ? [hornA.poly, HEAD_POLY] : [HEAD_POLY] }); g(h.right, { mask: h === hornB ? [hornA.poly, HEAD_POLY] : [HEAD_POLY] }) }
    for (const [h, P] of [[hornA, HORN_A], [hornB, HORN_B]]) for (let i = 6; i < P.length - 8; i += 5) g(curve([h.left[i], add(P[i], unit([P[i + 1][0] - P[i][0], P[i + 1][1] - P[i][1]]), -3), h.right[i]], 3), { width: 1.8, lift: 0.04, mask: h === hornB ? [hornA.poly] : [] })

    R.step('The mane', 'Flame-shaped tufts of hair flow back from the jaw and neck. Let each one curl a little differently so they feel like they are moving.')
    for (const m of MANE) g(m, { width: 3.4, mask: [HEAD_POLY, hornA.poly] })
    for (const m of MANE) { const n = m.length, base = add(m[0], m[n - 1], 1).map(v => v / 2), tip = m[Math.floor(n / 2)]
      for (const k of [-0.25, 0, 0.25]) { const b = add(base, [m[0][0] - m[n - 1][0], m[0][1] - m[n - 1][1]], k), mid = add(add(b, tip, 1).map(v => v / 2), perp(unit([tip[0] - b[0], tip[1] - b[1]])), 10 * k * 4)
        g(curve([b, mid, add(tip, [b[0] - tip[0], b[1] - tip[1]], 0.18)], 6), { width: 1.4, lift: 0.03, mask: [HEAD_POLY, hornA.poly], alpha: 0.75 }) } }
    for (const b of BEARD) g(b, { width: 3, mask: [HEAD_POLY] })

    R.step('Whiskers', 'Two long whiskers trail from the snout. Draw each one in a single smooth pass. Stopping and restarting leaves a bump.')
    R.ink(WHISKER_A, { color: LEAD, width: 3.6, speed: 300 }).ink(WHISKER_B, { color: LEAD, width: 3.6, speed: 300 })

    R.step('Ink the body', 'Trace both edges of the tube. Where the tail slips behind the upper coil, the line stops at the edge in front. That overlap is what sells the depth.')
    // the outline swells where the body turns away from the light and thins where the light hits it
    for (const th of [Math.PI / 2, -Math.PI / 2]) for (const [a, b] of [[0, TAIL_S], [TAIL_S, LEN]]) g(edge(a, b, th, 5), { width: 6, mask: bodyMask(b), weight: u => 0.35 + 1.25 * Math.pow(1 - lit(a + (b - a) * u, th * 0.9), 1.3) })
    g(curve([at(LEN - 2, Math.PI / 2), add(frame(LEN).p, frame(LEN).t, 16), at(LEN - 2, -Math.PI / 2)], 6), { width: 4 })

    R.step('Belly plates', 'A band of wide plates runs down the underside, like a snake\'s belly. Space them evenly and let each line follow the curve of the body.')
    const BELLY_TH = -Math.PI / 2 * 0.52
    g(edge(0, TAIL_S, BELLY_TH, 5), { width: 3, mask: bodyMask(0) }).ink(edge(TAIL_S, LEN * 0.97, BELLY_TH, 5), { color: LEAD, width: 3, grain: 0.35, mask: bodyMask(LEN) })
    for (let s = 30; s < LEN * 0.96; s += Math.max(9, width(s) * 0.2)) g([at(s, -Math.PI / 2), at(s + 3, (BELLY_TH - Math.PI / 2) / 2), at(s, BELLY_TH)], { width: 2.2, lift: 0.03, mask: bodyMask(s) })

    R.step('Scales, row by row', 'Draw each scale as a small U, overlapping toward the tail like roof tiles. Near the edges they get narrower, because the body is curving away from you.')
    const SCALES = []
    for (let s = 34, col = 0; s < LEN * 0.965; col++) {
      const w = width(s), ds = Math.max(9, Math.min(28, w * 0.21))
      if (w < 34) break
      const dth = ds / (w / 2)
      for (let th = BELLY_TH + dth * 0.5 + (col % 2) * dth * 0.5; th < Math.PI / 2 - dth * 0.35; th += dth * (1 + 0.16 * vary())) {
        // no two scales alike: a little bigger or smaller, nudged, tipped, and one side of the U a bit fuller
        const f = frame(s), c = add(add(at(s, th), f.t, ds * 0.08 * vary()), f.n, ds * 0.08 * vary())
        const rt = ds * 0.5 * (1 + 0.22 * vary()), rn = ds * 0.5 * Math.max(0.2, Math.cos(th)) * (1 + 0.2 * vary())
        const tip = 0.25 * vary(), lop = 0.25 * vary(), ft = rot(f.t, tip), fn = rot(f.n, tip)
        const arc = []; for (let a = -Math.PI / 2; a <= Math.PI / 2 + 1e-6; a += Math.PI / 6) arc.push(add(add(c, ft, rt * Math.cos(a) * (0.95 + lop * Math.sin(a))), fn, rn * Math.sin(a)))
        SCALES.push({ s, th, arc, c, f, ds, rt, rn })
      }
      s += ds * 0.78 * (1 + 0.18 * vary())                         // rows aren't laid with a ruler either
    }
    const SCALE_END = SCALES.length ? SCALES[SCALES.length - 1].s + 10 : LEN
    for (const sc of SCALES) {
      const L = lit(sc.s, sc.th)
      if (L > 0.86 && vary() > 0.1) continue                                // lost edge: the light eats this one
      const arc = L > 0.7 ? sc.arc.slice(vary() > 0 ? 2 : 0, sc.arc.length - (vary() > 0 ? 2 : 0)) : sc.arc
      R.ink(arc, { color: LEAD, width: Math.max(1.1, sc.ds * (0.06 + 0.12 * (1 - L))), alpha: 0.55 + 0.45 * (1 - L), grain: 0.3, lift: 0.025, speed: 700, mask: bodyMask(sc.s) })
    }
    for (let s = SCALE_END; s < LEN - 8; s += 9) g(edge(s, s + 1, 0, 1).length ? [at(s, -1.45), at(s + 4, 0), at(s, 1.45)] : [], { width: 1.5, lift: 0.02, mask: bodyMask(s) })

    R.step('Spines down the back', 'A ridge of sharp fins runs along the back. Sweep each one toward the tail and shrink them as the body thins out.')
    const SPIKES = []
    for (let s = 70; s < LEN * 0.94; s += Math.max(18, width(s) * 0.42)) {
      const f = frame(s), h = f.w * 0.36, a = at(s - f.w * 0.16, Math.PI / 2), b = at(s + f.w * 0.2, Math.PI / 2)
      const tip = add(add(at(s, Math.PI / 2), f.n, h), f.t, h * 0.55)
      SPIKES.push({ s, poly: curve([a, add(add(a, f.n, h * 0.55), f.t, h * 0.05), tip, add(add(b, f.n, h * 0.2), f.t, -h * 0.05), b], 5), a, b, tip })
    }
    for (const sp of SPIKES) { g(sp.poly, { width: 3, lift: 0.05, mask: bodyMask(sp.s) }); g(curve([add(sp.a, sp.b, 1).map(x => x / 2), sp.tip], 3), { width: 1.4, lift: 0.02, mask: bodyMask(sp.s) }) }

    R.step('Legs and claws', 'Ink the legs, then add rings of small scales around them. Hook each claw to a needle-sharp point. The claws are the darkest, sharpest lines on the leg.')
    for (const l of LEGS) {
      g(l.arm.left, { width: 4.4 }); g(l.arm.right, { width: 4.4 })
      for (let i = 3; i < l.arm.left.length - 2; i += 2) for (const q of [0.2, 0.4, 0.6, 0.8]) {
        const a = l.arm.left[i], b = l.arm.right[i], c = add(a, [b[0] - a[0], b[1] - a[1]], q + (i % 4 ? 0.1 : 0)), d = unit([l.arm.left[i + 1][0] - a[0], l.arm.left[i + 1][1] - a[1]])
        g(curve([add(c, perp(d), 5), add(c, d, 5), add(c, perp(d), -5)], 3), { width: 1.3, lift: 0.015 }) }
      for (const t of l.toes) { g(t.left, { width: 3 }); g(t.right, { width: 3 }) }
      for (const c of l.claws) R.ink(c, { color: '#141316', width: 2.2, lift: 0.04 })
    }

    R.step('Flames around the coils', 'Wisps of flame curl up around the body. They sit behind it, so every flame tucks under the body\'s edge instead of crossing it.')
    const FLAMES = [flame([230, 1296], [-0.35, -1], 250, 110, 46), flame([400, 1300], [0.05, -1], 250, 120, -50), flame([610, 1300], [0.25, -1], 230, 110, 44),
      flame([820, 1290], [0.55, -1], 220, 100, -40), flame([150, 1120], [-0.8, -1], 190, 80, 34), flame([900, 820], [0.7, -1], 170, 70, -30)]
    const INNER = FLAMES.map(fl => { const n = fl.length, b = add(fl[0], fl[n - 1], 1).map(v => v / 2); return fl.filter((_, i) => i > 3 && i < n - 4).map(p => add(b, [p[0] - b[0], p[1] - b[1]], 0.62)) })
    FLAMES.forEach((fl, i) => { g(fl, { width: 3, color: '#3e3d43', mask: EVERYTHING }); g(INNER[i], { width: 1.8, color: '#57565c', mask: EVERYTHING }) })

    R.step('Erase the guides', 'Lift out the construction lines. The finished line work should hold up on its own before any shading goes in.')
    R.erase('guide', 3.6)

    R.step('The darkest dark: the mouth', 'Fill the inside of the mouth nearly black. It is the darkest value in the drawing, and every other tone is judged against it.')
    const MOUTH_MASK = [...TEETH, TONGUE.poly]
    R.fill(MOUTH, { layer: 'deep', color: '#18171b', width: 14, alpha: 0.95, mask: MOUTH_MASK, angle: -0.3 })
    R.hatch(TONGUE.poly, { layer: 'shade', color: '#58575d', spacing: 4, angle: 0.7, width: 1.4 })

    R.step('Shade the round form', 'The light comes from the top left. Smudge a soft band of shadow down the side of the body turned away from it, and keep the lit side clean.')
    // first a light wash of graphite over the whole body, so it reads as a solid form and not an outline on paper
    for (let s0 = 0; s0 < LEN - 10; s0 += 240) {
      const s1 = Math.min(LEN, s0 + 260)
      R.fill(bodyPoly(s0, s1), { layer: 'shade', color: '#8e8d92', width: 30, alpha: 0.32, soft: 5, angle: 0.9, mask: bodyMask(s1), lift: 0.05 })
    }
    for (const m of MANE) R.fill(m, { layer: 'shade', color: '#8e8d92', width: 18, alpha: 0.3, soft: 4, mask: [HEAD_POLY, hornA.poly] })
    R.fill(HEAD_POLY, { layer: 'shade', color: '#9a999e', width: 20, alpha: 0.26, soft: 4, angle: 0.5, mask: [MOUTH, ...MOUTH_MASK, SOCKET] })
    for (const h of [hornA, hornB]) R.fill(h.poly, { layer: 'shade', color: '#8e8d92', width: 10, alpha: 0.3, soft: 3, mask: [HEAD_POLY] })
    for (const l of LEGS) R.fill(l.arm.poly, { layer: 'shade', color: '#8e8d92', width: 20, alpha: 0.3, soft: 4 })
    const core = []                                   // the darkest line on the cylinder at each point along it
    for (let s = 0; s < LEN * 0.98; s += 14) {
      let best = 0, bl = 9; for (let th = -1.5; th <= 1.5; th += 0.1) { const v = lit(s, th); if (v < bl) { bl = v; best = th } }
      core.push([s, best])
    }
    for (let i = 0; i + 1 < core.length; i += 4) {
      const seg = core.slice(i, i + 6), s0 = seg[0][0]
      R.brush(seg.map(([s, th]) => at(s, th * 0.9)), { layer: 'shade', color: '#2f2e34', width: width(s0) * 0.6, alpha: 0.34, soft: 7, clip: bodyPoly(Math.max(0, s0 - 40), Math.min(LEN, s0 + 120)), mask: bodyMask(s0), lift: 0.03 })
    }
    FLAMES.forEach((fl, i) => { const n = fl.length
      R.fill(fl, { layer: 'shade', color: '#a3a2a7', width: 26, alpha: 0.35, soft: 10, angle: 1.3, mask: EVERYTHING })
      R.brush(fl.slice(0, Math.floor(n / 2)), { layer: 'shade', color: '#5f5e64', width: 30, alpha: 0.4, soft: 9, clip: fl, mask: EVERYTHING })
      R.brush(INNER[i], { layer: 'shade', color: '#9a999e', width: 18, alpha: 0.22, soft: 7, clip: fl, mask: EVERYTHING }) })
    for (const l of LEGS) { R.brush(l.arm.right, { layer: 'shade', color: '#2e2d33', width: 30, alpha: 0.45, soft: 6, clip: l.arm.poly }); for (const t of l.toes) R.brush(t.right, { layer: 'shade', color: '#2e2d33', width: 10, alpha: 0.4, soft: 2, clip: t.poly }) }
    R.hatch(JAW_POLY, { layer: 'shade', color: '#3d3c42', spacing: 4, angle: 0.9, width: 1.3 })
    R.hatch(THROAT_POLY, { layer: 'shade', color: '#3d3c42', spacing: 4.5, angle: 0.9, width: 1.3 })
    R.hatch(SOCKET, { layer: 'shade', color: '#2d2c31', spacing: 3, angle: -0.6, width: 1.2 })
    R.hatch(CHEEK, { layer: 'shade', color: '#6a696f', spacing: 6, angle: -0.9, width: 1.1 })
    R.brush(curve([[436, 300], [446, 352], [424, 394], [360, 424]], 6), { layer: 'shade', color: '#2d2c31', width: 34, alpha: 0.3, soft: 8, clip: HEAD_POLY, mask: [MOUTH] })
    R.brush(curve([[178, 360], [260, 376], [350, 394]], 6), { layer: 'shade', color: '#2d2c31', width: 14, alpha: 0.35, soft: 4, clip: HEAD_POLY, mask: [MOUTH] })

    R.step('Shade every scale', 'Darken the base of each scale, a little on the lit side and a lot on the shadow side. That small dark crescent is what makes each scale look raised.')
    for (const sc of SCALES) {
      const tone = 1 - lit(sc.s, sc.th)
      const inner = sc.arc.map(p => add(sc.c, [p[0] - sc.c[0], p[1] - sc.c[1]], 0.62))
      R.brush(inner.map(p => add(p, [vary(), vary()], sc.ds * 0.12)), { layer: 'shade', color: '#2e2d33', width: sc.ds * (0.34 + 0.14 * vary()), alpha: (0.16 + 0.62 * Math.pow(tone, 1.4)) * (1 + 0.3 * vary()), lift: 0.015, speed: 1500, mask: bodyMask(sc.s) })
    }
    for (const sp of SPIKES) R.hatch(sp.poly, { layer: 'shade', color: '#4a4950', spacing: 3.5, angle: 1.1, width: 1.1, mask: bodyMask(sp.s) })
    for (const h of [hornA, hornB]) R.hatch(h.poly, { layer: 'shade', color: '#55545a', spacing: 4, angle: -1.2, width: 1.2, mask: [HEAD_POLY] })
    for (const m of MANE) R.hatch(m, { layer: 'shade', color: '#6a696f', spacing: 6, angle: -0.5, width: 1.2, mask: [HEAD_POLY, hornA.poly] })

    R.step('Final darks and lifted lights', 'Deepen the shadow where the tail disappears behind the coil, then lift a few highlights with an eraser: the brow, the snout, the top of each coil.')
    for (const th of [Math.PI / 2, -Math.PI / 2]) R.brush(edge(TAIL_S, TAIL_S + 360, th * 0.8, 6), { layer: 'shade', color: '#1e1d21', width: 26, alpha: 0.35, soft: 6, clip: bodyPoly(TAIL_S, LEN), mask: bodyMask(LEN) })
    R.brush(edge(0, LEN * 0.6, -Math.PI / 2 * 0.9, 6), { layer: 'shade', color: '#232226', width: 16, alpha: 0.3, soft: 4, clip: FRONT_BODY, mask: [HEAD_POLY, ...LEG_POLYS] })
    const hi = (pts, w, a = 0.8) => R.brush(pts, { layer: 'top', color: '#f7f6f2', width: w, alpha: a, soft: 2 })
    hi(curve([[372, 250], [334, 256], [300, 276]], 5), 7); hi(curve([[282, 292], [224, 314], [186, 330]], 5), 5)
    for (const [a, b] of [[40, 380], [700, 1150], [1450, 1800]]) hi(edge(a, b, Math.PI / 2 * 0.35, 14), 8, 0.5)
    R.wait(0.5)
    return R
  }
  // Pacing: every step stays on screen long enough to read its caption (about 15 characters a second, plus a
  // beat), while long, repetitive steps like the scales run fast. Shared by the page and the sound.
  function timing(rec) {
    const ends = rec.steps.map((s, i) => (rec.steps[i + 1] ? rec.steps[i + 1].t : rec.duration) - s.t)
    const read = s => 1.6 + (s.title.length + s.note.length) / 15
    // hold at most 2.5 s on a caption; the rest of the reading time is spent drawing (slower if need be), so the
    // pencil keeps moving instead of the picture freezing while people read
    const speed = (s, i) => Math.max(0.3, ends[i] / Math.max(read(s) - 2.5, ends[i] / 14, 0.5))
    const holdStep = (s, i) => Math.min(2.5, Math.max(1.2, read(s) - ends[i] / speed(s, i)))
    return { speed, holdStep, intro: 3, outro: 4 }
  }
  const api = { build, timing }
  if (typeof module !== 'undefined' && module.exports) module.exports = api
  else root.SERPENT = api
})(typeof window !== 'undefined' ? window : globalThis)
