// How to draw a serpent dragon (advanced): an original Eastern dragon in graphite, recorded with timelapse.js.
// The body is geometry, not freehand: a spine curve, a width along it, and a cylinder wrapped around it.
// Scales, belly plates and spines are laid on that cylinder, so they narrow toward the edges and take
// light from the top left like a real round form would. Space is 1000 x 1300.
(function (root) {
  function build(TL) {
    const node = typeof module !== 'undefined' && module.exports
    const SH = node ? require('../../timelapse/shapes.js') : root.SH
    const HEADMOD = node ? require('./head.js') : root.HEAD
    const CLAWMOD = node ? require('./claw.js') : root.CLAW
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

    // ---------------------------------------------------------------- head and claws (their own studies: head.js, claw.js)
    // The head is the focal point, so it is big: its jaw hinge sits on the start of the neck.
    const HEAD = HEADMOD.make(SH, { x: 118, y: 196, s: 0.68 })
    // Two legs, each a forearm and a gripping hand; the arm's root sits on the belly
    const clawAt = (s, sc, seed) => { const b = at(s, -Math.PI / 2 * 0.1), r = [210 * sc, -250 * sc]; return CLAWMOD.make(SH, { x: b[0] - r[0], y: b[1] - r[1], s: sc }, { seed, under: [bodyPoly(Math.max(0, s - 200), s + 200)] }) }
    const CLAW_F = clawAt(LEN * 0.21, 0.62, 1), CLAW_B = clawAt(LEN * 0.535, 0.52, 2)   // the front claw reaches into the upper loop
    const CLAWS = [CLAW_F, CLAW_B]

    // what sits in front of the body: the head (mane and horns included), then the claws; the tail hides behind the front coil
    const FRONT = [...HEAD.FRONT, ...CLAW_F.FRONT, ...CLAW_B.FRONT]
    const bodyMask = s => inTail(s) ? [...FRONT, FRONT_BODY] : FRONT
    const EVERYTHING = [...FRONT, bodyPoly(0, LEN)]
    const behindHead = HEAD.FRONT

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

    R.step('Block in the head', 'The skull is a ball, the snout a long box about one and a half times as long, the jaw a wedge hinged below the eye. The eye sits on the line where snout meets skull.', { view: 'head' })
    HEAD.construct(R)

    R.step('Rough in the legs', 'Each leg is a chain: shoulder, elbow, wrist. The fingers are chains too, three joints each, curling down into a grip. A circle marks every joint so the bends stay honest.', { view: 'claws' })
    for (const c of CLAWS) c.construct(R)

    R.step('Ink the head', 'Press harder under the jaw and along the brow, where the form turns from the light. Keep the top of the snout light and thin: it faces the light.', { view: 'head' })
    HEAD.outline(R)

    R.step('Nostril and snout scales', 'Reptile scales pack together like cells, sharing edges. Draw them bigger on top, finer toward the lip, and lighter where the light hits.', { view: 'head' })
    HEAD.nose(R)

    R.step('The eye', 'A reptile iris fills the whole eye, so no white. A slit pupil, fibres radiating out from it, a thick upper lid, and tiny scales ringing the lids.', { view: 'eye' })
    HEAD.eye(R)

    R.step('Teeth and tongue', 'Teeth are cones leaning back toward the throat, uneven in size with a big fang up front. Teeth on the far side are smaller and lighter, which gives the mouth depth.', { view: 'head' })
    HEAD.mouth(R)

    R.step('Horns', 'Two horns sweep back, one with a tine. Rings wrap around them, heavier on the shadow side, so they read as round and not flat.', { view: 'head' })
    HEAD.horns(R)

    R.step('Brow and cheek fins', 'Tufts of hair over the eye make the brow heavy and fierce. Small ribbed fins flare off the back of the cheek.', { view: 'head' })
    HEAD.brows(R)

    R.step('The mane and beard', 'Hair moves in masses, not single strands. Give every lock the same S-shaped rhythm, sweeping back, then draw strands that follow each lock.', { view: 'head' })
    HEAD.mane(R)

    R.step('Jaw and cheek scales', 'A row of big lip scales edges the mouth. Plates run under the jaw, and a field of finer scales covers the cheek and skull.', { view: 'head' })
    HEAD.jawDetail(R)

    R.step('Whiskers', 'Two long whiskers trail from the snout. Draw each in one smooth pass, thick at the root and thin at the tip. Stopping and restarting leaves a bump.', { view: 'all' })
    HEAD.whiskers(R)

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

    R.step('The claws, finger by finger', 'Plates run across the top of each finger, a line runs down its side, and a pad bulges under every joint. Each talon grows from a sheath and hooks with the curl.', { view: 'claws' })
    for (const c of CLAWS) c.ink(R)

    R.step('Flames around the coils', 'Wisps of flame curl up around the body. They sit behind it, so every flame tucks under the body\'s edge instead of crossing it.')
    const FLAMES = [flame([230, 1296], [-0.35, -1], 250, 110, 46), flame([400, 1300], [0.05, -1], 250, 120, -50), flame([610, 1300], [0.25, -1], 230, 110, 44),
      flame([820, 1290], [0.55, -1], 220, 100, -40), flame([150, 1120], [-0.8, -1], 190, 80, 34), flame([900, 820], [0.7, -1], 170, 70, -30)]
    const INNER = FLAMES.map(fl => { const n = fl.length, b = add(fl[0], fl[n - 1], 1).map(v => v / 2); return fl.filter((_, i) => i > 3 && i < n - 4).map(p => add(b, [p[0] - b[0], p[1] - b[1]], 0.62)) })
    FLAMES.forEach((fl, i) => { g(fl, { width: 3, color: '#3e3d43', mask: EVERYTHING }); g(INNER[i], { width: 1.8, color: '#57565c', mask: EVERYTHING }) })

    R.step('Erase the guides', 'Lift out the construction lines. The finished line work should hold up on its own before any shading goes in.')
    R.erase('guide', 3.6)

    R.step('The darkest darks', 'Fill the throat, the pupil and the nostril nearly black. These are the darkest values in the drawing, and every other tone is judged against them.', { view: 'head' })
    HEAD.darks(R)
    for (const c of CLAWS) c.darks(R)

    R.step('Shade the round form', 'The light comes from the top left. Smudge a soft band of shadow down the side of the body turned away from it, and keep the lit side clean.')
    // first a light wash of graphite over the whole body, so it reads as a solid form and not an outline on paper
    for (let s0 = 0; s0 < LEN - 10; s0 += 240) {
      const s1 = Math.min(LEN, s0 + 260)
      R.fill(bodyPoly(s0, s1), { layer: 'shade', color: '#8e8d92', width: 30, alpha: 0.32, soft: 5, angle: 0.9, mask: bodyMask(s1), lift: 0.05 })
    }
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

    R.step('Model the head', 'Hatch the underside of the jaw and the hollow under the cheekbone, shade under every scale, and darken the roots of the mane where the hair bunches.', { view: 'head' })
    HEAD.shade(R)

    R.step('Model the claws', 'The underside of each finger turns from the light, so it goes darker. Talons are dark keratin, darkest underneath, with a thin bright line along the top.', { view: 'claws' })
    for (const c of CLAWS) c.shade(R)

    R.step('Shade every scale', 'Darken the base of each scale, a little on the lit side and a lot on the shadow side. That small dark crescent is what makes each scale look raised.')
    for (const sc of SCALES) {
      const tone = 1 - lit(sc.s, sc.th)
      const inner = sc.arc.map(p => add(sc.c, [p[0] - sc.c[0], p[1] - sc.c[1]], 0.62))
      R.brush(inner.map(p => add(p, [vary(), vary()], sc.ds * 0.12)), { layer: 'shade', color: '#2e2d33', width: sc.ds * (0.34 + 0.14 * vary()), alpha: (0.16 + 0.62 * Math.pow(tone, 1.4)) * (1 + 0.3 * vary()), lift: 0.015, speed: 1500, mask: bodyMask(sc.s) })
    }
    for (const sp of SPIKES) R.hatch(sp.poly, { layer: 'shade', color: '#4a4950', spacing: 3.5, angle: 1.1, width: 1.1, mask: bodyMask(sp.s) })

    R.step('Final darks and lifted lights', 'Deepen the shadow where the tail disappears behind the coil, then lift highlights with an eraser: the eye, the teeth, the talons and the top of each coil.', { view: 'all' })
    for (const th of [Math.PI / 2, -Math.PI / 2]) R.brush(edge(TAIL_S, TAIL_S + 360, th * 0.8, 6), { layer: 'shade', color: '#1e1d21', width: 26, alpha: 0.35, soft: 6, clip: bodyPoly(TAIL_S, LEN), mask: bodyMask(LEN) })
    R.brush(edge(0, LEN * 0.6, -Math.PI / 2 * 0.9, 6), { layer: 'shade', color: '#232226', width: 16, alpha: 0.3, soft: 4, clip: FRONT_BODY, mask: FRONT })
    const hi = (pts, w, a = 0.8) => R.brush(pts, { layer: 'top', color: '#f7f6f2', width: w, alpha: a, soft: 2 })
    HEAD.highlights(R)
    for (const c of CLAWS) c.highlights(R)
    for (const [a, b] of [[40, 380], [700, 1150], [1450, 1800]]) hi(edge(a, b, Math.PI / 2 * 0.35, 14), 8, 0.5)
    R.wait(0.5)
    // camera views, in drawing space: the page eases between them as the lesson moves from part to part
    const bounds = polys => { const P = polys.flat(); const xs = P.map(p => p[0]), ys = P.map(p => p[1]); return [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)] }
    const eye = HEAD.place(HEAD.local.EYE_C)
    R.views = { all: [0, 0, 1000, 1300], head: bounds([HEAD.OUTLINE]).map((v, i) => v + [-40, -60, 40, 40][i]),
      eye: [eye[0] - 150, eye[1] - 100, eye[0] + 150, eye[1] + 100], clawF: bounds(CLAW_F.FRONT).map((v, i) => v + [-30, -20, 30, 30][i]), clawB: bounds(CLAW_B.FRONT).map((v, i) => v + [-30, -20, 30, 30][i]) }
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
