// head.js: the serpent dragon's head, built from anatomy. Local space: facing left, about 560 units from nose
// to the back of the skull, y down. HEAD.make(SH, placement) maps it into the drawing and returns the shapes other
// parts need (what the head hides) and one function per lesson step.
(function (root) {
  function make(SH, where) {
    const { add, sub, mix, unit, perp, rot, curve, circle, tube, across, along, lock, resample } = SH
    const M = SH.place(where), m = P => P.map(M), S = where.s

    // ---------------------------------------------------------------- the skull and jaw
    const SNOUT = [[40, 96], [90, 82], [160, 78], [230, 78], [290, 72], [330, 56]]
    const SKULL = [[330, 56], [370, 40], [420, 36], [470, 46], [520, 70], [556, 104]]
    const NOSE = [[40, 96], [20, 106], [6, 128], [4, 154], [14, 174], [36, 186]]
    const UPLIP = [[36, 186], [64, 198], [104, 202], [150, 204], [200, 206], [250, 212], [300, 220], [345, 230], [382, 244]]
    const LOLIP = [[382, 244], [330, 290], [270, 330], [205, 362], [150, 386], [110, 398]]
    const CHIN = [[110, 398], [98, 412], [104, 432], [126, 440]]
    const JAW = [[126, 440], [190, 442], [260, 430], [330, 406], [390, 372], [440, 342], [480, 320], [512, 304]]
    const BACK = [[556, 104], [572, 150], [568, 204], [546, 258], [512, 304]]
    const BROW = [[296, 112], [322, 98], [356, 92], [392, 96], [420, 108], [440, 124]]
    const CHEEKBONE = [[330, 168], [380, 176], [430, 186], [470, 210], [492, 240]]
    const CHEEK = [[384, 246], [426, 232], [472, 240], [506, 270]]
    const JAW_MUSCLE = [[392, 262], [440, 268], [488, 290], [506, 306]]
    const JAW_SIDE = [[372, 262], [300, 312], [226, 350], [160, 380], [136, 404]]
    const OUTLINE = curve([...SNOUT, ...SKULL.slice(1), ...BACK.slice(1), ...JAW.slice().reverse().slice(1), ...CHIN.slice().reverse().slice(1),
      ...LOLIP.slice().reverse().slice(1), ...UPLIP.slice().reverse().slice(1), ...NOSE.slice().reverse().slice(1, -1)], 4, true)

    // gums sit just inside the lips; the mouth is what lies between them
    const GUM_U = UPLIP.slice(1).map(p => add(p, [0, 11]))
    const GUM_L = LOLIP.slice(0, -1).map(p => add(p, [4, -10]))
    const MOUTH = curve([...UPLIP, ...LOLIP.slice(1)], 5, true)                  // the opening, lip to lip
    const MOUTH_IN = curve([...GUM_U, ...GUM_L.slice(1)], 4, true)

    // teeth: conical, a little curved back toward the throat; big fangs at the front of each jaw
    const tooth = (base, dir, h, w, lean = 0.2) => {
      const d = unit(dir), side = perp(d), back = [1, 0]
      const tip = add(add(base, d, h), back, h * lean)
      const L = [add(base, side, w / 2), add(add(add(base, d, h * 0.55), side, w * 0.33), back, h * lean * 0.35), tip]
      const R = [tip, add(add(add(base, d, h * 0.5), side, -w * 0.3), back, h * lean * 0.25), add(base, side, -w / 2)]
      return { base, tip, left: curve(L, 5), right: curve(R, 5), poly: curve([...L, ...R.slice(1)], 5) }
    }
    const onPath = (P, x) => { const Q = resample(P, 200); let best = Q[0]; for (const q of Q) if (Math.abs(q[0] - x) < Math.abs(best[0] - x)) best = q; return best }
    // near-side teeth, uneven the way real teeth are: a big fang, a gap, then a run that shrinks toward the hinge
    const TEETH_U = [[56, 30, 12], [84, 78, 24], [124, 30, 13], [158, 44, 17], [196, 38, 15], [232, 34, 14], [268, 28, 12], [302, 24, 11], [334, 18, 9], [360, 12, 7]]
      .map(([x, h, w]) => tooth(onPath(GUM_U, x), [0.06, 1], h, w, 0.2))
    const TEETH_L = [[122, 70, 22], [164, 30, 13], [202, 36, 14], [240, 30, 13], [278, 26, 11], [314, 20, 10], [344, 14, 8]]
      .map(([x, h, w]) => tooth(onPath(GUM_L, x), [0.18, -1], h, w, 0.14))
    // far-side teeth: seen across the mouth, set back and smaller, lighter so they sit behind the near ones
    const TEETH_FAR = [[104, 26, 11], [140, 34, 13], [178, 30, 12], [216, 28, 11], [254, 24, 10], [290, 20, 9]]
      .map(([x, h, w]) => tooth(add(onPath(GUM_U, x), [10, 12]), [0.06, 1], h, w, 0.2))
    const TEETH = [...TEETH_U, ...TEETH_L]

    const TONGUE = tube(curve([[344, 258], [284, 282], [218, 304], [160, 318], [110, 322], [66, 312], [36, 294]], 8), u => 36 * (1 - 0.55 * u), 44)
    const FORK = [curve([[36, 294], [20, 278], [8, 258]], 4), curve([[36, 294], [14, 298], [-4, 306]], 4)]

    // ---------------------------------------------------------------- eye
    const EYE_C = [362, 131]
    const LID_U = [[320, 135], [337, 113], [367, 104], [398, 113], [414, 132]]
    const LID_L = [[320, 138], [344, 156], [375, 160], [404, 147], [414, 132]]
    const EYEBALL = curve([...LID_U, ...LID_L.slice().reverse().slice(1, -1)], 6, true)
    const IRIS = circle(EYE_C, 18, 0, 1, 18, 36)
    const LID_FOLD = [[315, 127], [336, 98], [370, 89], [406, 98], [427, 122]]
    // a reptile eye: the iris fills the opening (no white), the pupil is a tapered vertical slit
    const PUPIL = curve([[EYE_C[0], EYE_C[1] - 25], [EYE_C[0] + 4.5, EYE_C[1] - 8], [EYE_C[0] + 5.5, EYE_C[1]], [EYE_C[0] + 4.5, EYE_C[1] + 8], [EYE_C[0], EYE_C[1] + 27],
      [EYE_C[0] - 4.5, EYE_C[1] + 8], [EYE_C[0] - 5.5, EYE_C[1]], [EYE_C[0] - 4.5, EYE_C[1] - 8]], 4, true)
    const LID_THICK_U = LID_U.map((p, i) => add(p, [0, i === 0 || i === LID_U.length - 1 ? 0 : -7]))
    const LID_THICK_L = LID_L.map((p, i) => add(p, [0, i === 0 || i === LID_L.length - 1 ? 0 : 5]))
    // the skin around the eye: packed scales, finest at the lids, growing outward, in their own ring so no other field doubles them
    const EYE_RING = circle([EYE_C[0] + 4, EYE_C[1] + 4], 96, 0, 1, 66, 48)
    const WRINKLES = []

    // ---------------------------------------------------------------- nose
    const NOSTRIL = curve([[26, 134], [36, 120], [52, 112], [68, 114], [58, 120], [44, 128], [34, 140]], 5, true)
    const NOSTRIL_HOLE = curve([[32, 132], [40, 122], [54, 115], [62, 116], [50, 123], [38, 134]], 5, true)
    const NOSE_RIDGE = curve([[22, 150], [40, 146], [66, 132], [84, 116], [96, 100]], 5)

    // ---------------------------------------------------------------- scales and plates
    const R = SH.rng(77), v = () => R() - 0.5
    const SCUTES = []                                            // raised plates along the top of the snout
    for (let x = 84; x < 300; x += 24 + 6 * v()) {
      const a = onPath(SNOUT, x), b = onPath(SNOUT, x + 22)
      SCUTES.push(curve([add(a, [0, 3]), add(mix(a, b, 0.5), [0, -6 - 2 * v()]), add(b, [0, 3])], 5))
    }
    const SNOUT_SIDE = [[70, 102], [160, 84], [240, 84], [300, 78], [322, 112], [312, 160], [330, 214], [220, 206], [110, 194], [72, 180], [96, 150]]
    const CHEEK_FIELD = [[412, 196], [482, 220], [502, 280], [436, 300], [398, 262]]
    const scalesIn = (poly, size, seed, keep = () => 1) => {                   // small overlapping scales filling a region, no two alike
      const Rr = SH.rng(seed), out = [], xs = poly.map(p => p[0]), ys = poly.map(p => p[1])
      for (let y = Math.min(...ys), row = 0; y < Math.max(...ys); y += size * 0.78, row++) {
        for (let x = Math.min(...xs) + (row % 2) * size / 2; x < Math.max(...xs); x += size * (0.9 + 0.2 * Rr())) {
          const c = [x + size * 0.15 * (Rr() - 0.5), y + size * 0.15 * (Rr() - 0.5)]
          if (!SH.inside(c, poly) || Rr() > keep(c)) continue
          const r = size * (0.42 + 0.1 * Rr())
          out.push({ c, k: keep(c), arc: curve([[c[0] - r, c[1] - r * 0.3], [c[0] - r * 0.3, c[1] + r * 0.55], [c[0] + r * 0.4, c[1] + r * 0.5], [c[0] + r, c[1] - r * 0.2]], 3) })
        }
      }
      return out
    }
    const edgeDist = (p, poly) => { let d = 1e9; const Q = resample([...poly, poly[0]], 120); for (const q of Q) d = Math.min(d, Math.hypot(q[0] - p[0], q[1] - p[1])); return d }
    function pebbles(poly, size, seed, sizeAt = () => 1, keep = () => 1) {
      // points on a jittered hex grid (spacing set by sizeAt), then packed cells around them, trimmed to the region
      const Rr = SH.rng(seed), pts = [], xs = poly.map(p => p[0]), ys = poly.map(p => p[1])
      for (let y = Math.min(...ys) - size, row = 0; y < Math.max(...ys) + size; row++) {
        const sy = size * sizeAt([Math.min(...xs), y])
        for (let x = Math.min(...xs) - size + (row % 2) * sy / 2; x < Math.max(...xs) + size;) {
          const sz = size * sizeAt([x, y]); pts.push([x + sz * 0.55 * (Rr() - 0.5), y + sz * 0.55 * (Rr() - 0.5)]); x += sz * (0.85 + 0.3 * Rr())
        }
        y += sy * 0.86
      }
      return SH.cells(pts, size * 1.4).map((cell, i) => ({ cell, c: pts[i] }))
        .filter(o => o.cell.length > 2 && SH.inside(o.c, poly))
        .map(o => { const sz = Math.sqrt(Math.abs(o.cell.reduce((a, p, k) => { const q = o.cell[(k + 1) % o.cell.length]; return a + p[0] * q[1] - q[0] * p[1] }, 0) / 2)); const ins = SH.inset(o.cell, 0.84); const e = Math.min(1, edgeDist(o.c, poly) / (size * 1.6)); return { c: o.c, k: keep(o.c) * e, size: sz, blob: ins.poly } })
    }
    // bigger plates up top and toward the eye, fine ones near the lip; faint where the light hits the top of the snout
    const SNOUT_SCALES = pebbles(SNOUT_SIDE, 18, 5, c => 0.7 + 0.55 * Math.max(0, 1 - (c[1] - 80) / 110) + 0.25 * (c[0] / 330), c => Math.min(1, 0.25 + 0.95 * (c[1] - 84) / 120))
    const CHEEK_FIELD2 = [[400, 170], [470, 190], [540, 150], [566, 210], [540, 262], [470, 250], [420, 230]]
    const CHEEK_SCALES = [...pebbles(CHEEK_FIELD, 14, 9, () => 1, () => 0.95), ...pebbles(CHEEK_FIELD2, 20, 19, c => 0.8 + 0.4 * (c[0] - 400) / 170, () => 0.85)]
    const SKULL_FIELD = [[392, 60], [440, 42], [500, 56], [548, 94], [566, 150], [540, 176], [470, 176], [430, 150], [440, 110], [404, 92]]
    const SKULL_SCALES = pebbles(SKULL_FIELD, 22, 41, c => 0.85 + 0.45 * (c[0] - 392) / 175, c => Math.min(1, 0.3 + 0.8 * (c[0] - 400) / 160))
    const EYE_SCALES = pebbles(EYE_RING, 16, 61, c => 0.45 + 0.75 * Math.min(1, Math.hypot((c[0] - EYE_C[0]) / 96, (c[1] - EYE_C[1]) / 66)), c => 0.9)
      .filter(sc => !SH.inside(sc.c, EYEBALL) && !(sc.c[1] < EYE_C[1] - 18 && Math.abs(sc.c[0] - EYE_C[0]) < 70))   // none on the eye, none under the brow ridge
    const HINGE_WRINKLES = [0, 1, 2, 3].map(i => curve([[388 + i * 6, 250 + i * 10], [410 + i * 8, 262 + i * 12], [430 + i * 10, 268 + i * 14]], 4))
    const JAW_FIELD = curve([...LOLIP.slice(1, -1).map(p => add(p, [0, 16])), [128, 420], ...JAW.slice(1, -1).map(p => add(p, [0, -22]))].length ? [[372, 262], [320, 304], [262, 340], [200, 370], [140, 398], [132, 418], [200, 422], [270, 408], [340, 382], [400, 348], [440, 322]] : [], 3, true)
    const JAW_SCALES = pebbles(JAW_FIELD, 16, 31, c => 0.8 + 0.4 * (c[0] - 130) / 310, c => Math.min(1, 0.4 + 0.7 * (c[1] - 262) / 150))
    const LABIALS = []                                          // the row of large scales that edge a reptile's lips
    for (const [P, dy] of [[UPLIP, -12], [LOLIP, 12]]) { const Q = resample(curve(P, 6), 20); for (let i = 1; i < Q.length - 1; i++) { const c = add(Q[i], [0, dy]), w = 11 + 3 * Math.sin(i); LABIALS.push(curve([add(Q[i - 1], [3, 0]), add(c, [-w * 0.6, dy * 0.2]), add(c, [w * 0.6, dy * 0.2]), add(Q[i + 1], [-3, 0])], 3)) } }
    const JAW_BAND = tube(curve(JAW, 6), () => 30, 40)                                  // plates under the jaw
    const THROAT_PLATES = across(JAW_BAND, 16, 0.25, 0.04, 0.96)

    // ---------------------------------------------------------------- horns, brows, fins
    const HORN_A = tube(curve([[440, 52], [480, 10], [530, -30], [590, -62], [650, -78], [700, -80]], 8), u => 36 * Math.pow(1 - u, 0.9) + 3, 60)
    const TINE = tube(curve([[560, -48], [572, -100], [592, -138], [618, -160]], 8), u => 17 * (1 - u) + 2, 30)
    const HORN_B = tube(curve([[398, 50], [428, 2], [468, -40], [518, -70], [560, -84]], 8), u => 28 * Math.pow(1 - u, 0.9) + 2, 50)
    const BROWS = [lock([344, 92], [0.1, -1], 64, 22, -14, 12), lock([372, 88], [0.35, -1], 86, 26, 16, -14), lock([398, 92], [0.6, -1], 104, 28, -18, 16), lock([420, 102], [0.85, -0.8], 118, 28, 20, -18), lock([436, 116], [1, -0.5], 124, 26, -18, 16)]
    const FINS = [[480, 236], [496, 262], [506, 290]].map((b, i) => {
      const d = unit([1, 0.35 + 0.25 * i]), n = perp(d), len = 70 - 10 * i
      const tip = add(b, d, len), poly = curve([add(b, n, 14), add(add(b, d, len * 0.5), n, 12), tip, add(add(b, d, len * 0.55), n, -2), add(b, n, -12)], 5)
      return { poly, ribs: [0.25, 0.5, 0.75].map(k => [add(b, n, 12 - 26 * k), add(tip, n, (0.5 - k) * 3)]) }
    })

    // ---------------------------------------------------------------- mane, beard, whiskers
    // A mass of hair like a flame: a wide root, an S-bend through the middle, and 2-3 tips that curl off it.
    // Returns the outline, the strands that follow its flow, and the spine.
    function mass(base, dir, length, width, bend, count = 3, seed = 1) {
      // a bundle of locks from one root, all flowing the same way (a shared S-bend is what makes hair read as hair),
      // fanned a little, different lengths, each ending in a clean point that curls with the flow
      const Rr = SH.rng(seed), d = unit(dir), n = perp(d), locks = []
      for (let k = 0; k < count; k++) {
        const v = count === 1 ? 0 : k / (count - 1) - 0.5
        const root = add(base, n, v * width * 0.55), dk = rot(d, v * 0.35)
        const L = length * (0.72 + 0.28 * Rr()) * (1 - Math.abs(v) * 0.3)
        locks.push(lock(root, dk, L, width / count * 1.5, bend * (0.85 + 0.3 * Rr()), -bend * (0.6 + 0.4 * Rr())))
      }
      return { locks, polys: locks.map(l => l.poly), poly: locks[0].poly }
    }
    // the mane streams back and a little up, every mass bending with the same rhythm
    // the mane streams back in one rhythm: every mass swings down, then lifts, then curls up at the tip
    const MANE = [
      mass([546, 118], [1, -0.55], 320, 96, 80, 4, 12), mass([562, 186], [1, -0.1], 340, 100, 86, 4, 13), mass([540, 262], [1, 0.3], 300, 92, 78, 4, 14),
      mass([524, 76], [0.8, -1], 250, 76, 64, 3, 11), mass([512, 300], [0.75, 0.75], 230, 70, 60, 3, 15), mass([566, 226], [1, 0.1], 240, 66, 70, 3, 16),
    ]
    const BEARD = [mass([160, 438], [0.55, 1], 120, 64, 22, 3, 21), mass([250, 430], [0.75, 1], 140, 70, 24, 3, 22), mass([344, 398], [0.95, 0.9], 130, 64, 22, 3, 23)]
    const WHISK_A = tube(curve([[58, 190], [18, 214], [-34, 252], [-62, 322], [-50, 420], [-12, 498], [40, 540], [84, 556]], 10), u => 12 * Math.pow(1 - u, 1.1) + 1.2, 80)
    const WHISK_B = tube(curve([[76, 194], [48, 236], [22, 296], [16, 372], [38, 440], [72, 476]], 10), u => 9 * Math.pow(1 - u, 1.1) + 1, 60)
    const NOSE_HAIRS = [0, 1, 2, 3].map(i => curve([[26 + i * 5, 178 + i * 3], [4 - i * 6, 190 + i * 8], [-14 - i * 8, 206 + i * 14]], 4))

    // ---------------------------------------------------------------- what the head hides (for the rest of the drawing)
    const FRONT = [m(OUTLINE), ...MANE.flatMap(l => l.polys.map(m)), ...BEARD.flatMap(l => l.polys.map(m)), m(HORN_A.poly), m(HORN_B.poly), m(TINE.poly), ...FINS.map(f => m(f.poly))]

    // ---------------------------------------------------------------- drawing it, step by step
    const LEAD = '#2e2d33'
    const ink = (Rec, P, o = {}) => Rec.ink(m(P), { color: LEAD, width: 4, grain: Math.min(0.65, 1.3 / Math.max(1, o.width ?? 4)), ...o })
    const pencil = (Rec, P, o = {}) => Rec.pencil(m(P), { speed: 650, ...o })
    const W = w => w                                                               // widths are in drawing units already
    const headMask = { mask: [] }
    const maneMask = i => [m(OUTLINE), ...MANE.slice(i + 1).flatMap(l => l.polys.map(m))]   // later masses sit in front

    return {
      FRONT, OUTLINE: m(OUTLINE), MOUTH: m(MOUTH), place: M, local: { OUTLINE, MOUTH, EYE_C },
      construct(Rec) {
        // the skull as a ball, the snout as a box, the jaw as a wedge, the eye on the line between them
        pencil(Rec, circle([450, 110], 100, 0, 1.03))
        pencil(Rec, [[20, 110], [330, 70], [340, 200], [30, 186], [20, 110]])
        pencil(Rec, [[382, 244], [100, 380], [110, 414], [470, 316]])
        pencil(Rec, [[20, 130], [560, 130]], { alpha: 0.6 }); pencil(Rec, circle(EYE_C, 30, 0, 1.03))
      },
      outline(Rec) {
        ink(Rec, curve(SNOUT, 8), { width: W(4.2), weight: u => 0.7 + 0.3 * u })
        ink(Rec, curve(SKULL, 8), { width: W(4), weight: u => 0.8 + 0.4 * u })
        ink(Rec, curve(NOSE, 6), { width: W(4.4), weight: u => 0.8 + 0.6 * u })
        ink(Rec, curve(UPLIP, 8), { width: W(4.6), weight: u => 1.2 - 0.4 * u })
        ink(Rec, curve(LOLIP, 8), { width: W(4.2) })
        ink(Rec, curve(CHIN, 5), { width: W(5) })
        ink(Rec, curve(JAW, 8), { width: W(5.4), weight: u => 1.3 - 0.4 * u })                        // heavy: the underside is in shadow
        ink(Rec, curve(BROW, 6), { width: W(6), weight: u => 0.6 + 0.8 * Math.sin(Math.PI * u) })
        ink(Rec, curve(CHEEKBONE, 6), { width: W(2.6), weight: u => 1 - 0.5 * u })
        ink(Rec, curve(CHEEK, 6), { width: W(2.4) })
        ink(Rec, curve(JAW_MUSCLE, 6), { width: W(2), weight: u => 0.5 + u })
        ink(Rec, curve(JAW_SIDE, 6), { width: W(1.8), weight: u => 1.2 - 0.6 * u, alpha: 0.8 })
        ink(Rec, curve([[40, 112], [58, 104], [82, 104]], 4), { width: W(2.2) })
      },
      nose(Rec) {
        ink(Rec, NOSTRIL, { width: W(3.2), weight: u => 0.6 + 0.8 * Math.sin(Math.PI * u) }); ink(Rec, NOSE_RIDGE, { width: W(2.4), weight: u => 1.2 - 0.6 * u })
        for (const h of NOSE_HAIRS) ink(Rec, h, { width: W(1.2), lift: 0.03 })
        for (const sc of SNOUT_SCALES) ink(Rec, sc.blob, { hand: 0.35, mask: [m(EYE_RING)], width: W(0.7 + 0.9 * sc.k), lift: 0.012, speed: 800, alpha: 0.2 + 0.7 * sc.k, weight: u => 0.35 + 1.1 * Math.max(0, Math.sin(2 * Math.PI * u - 0.6)) })
      },
      eye(Rec) {
        const around = { mask: [m(EYEBALL)] }
        for (const sc of EYE_SCALES) ink(Rec, sc.blob, { hand: 0.25, width: W(0.6 + 0.07 * sc.size), alpha: 0.85, lift: 0.01, speed: 700, ...around, weight: u => 0.35 + 1.1 * Math.max(0, Math.sin(2 * Math.PI * u - 0.6)) })
        ink(Rec, curve(LID_FOLD, 6), { width: W(3.2), weight: u => 0.4 + Math.sin(Math.PI * u), ...around })
        ink(Rec, curve(LID_THICK_U, 6), { width: W(2.2), ...around }); ink(Rec, curve(LID_THICK_L, 6), { width: W(1.8), ...around })
        ink(Rec, curve(LID_U, 6), { width: W(4.6), weight: u => 0.7 + 0.6 * Math.sin(Math.PI * u) })
        ink(Rec, curve(LID_L, 6), { width: W(2.8) })
        ink(Rec, PUPIL, { width: W(1.6), hand: 0, mask: [] })
        for (let k = 0; k < 44; k++) {                                                             // fibres radiating from the pupil
          const a = k / 44 * 2 * Math.PI + 0.08 * v(), r0 = 7 + 2 * Math.abs(Math.sin(a)), r1 = 40
          const p0 = add(EYE_C, [Math.cos(a) * r0, Math.sin(a) * r0 * 1.6]), p1 = add(EYE_C, [Math.cos(a) * r1, Math.sin(a) * r1])
          ink(Rec, [p0, add(mix(p0, p1, 0.5), [v() * 3, v() * 3]), p1], { width: W(0.8), lift: 0.008, alpha: 0.5, hand: 0.3, clip: m(EYEBALL), mask: [m(PUPIL)] })
        }
      },
      mouth(Rec) {
        ink(Rec, curve(GUM_U, 6), { width: W(2.2) }); ink(Rec, curve(GUM_L, 6), { width: W(2.2) })
        for (const t of TEETH_FAR) { const mk = { mask: TEETH.map(x => m(x.poly)) }; ink(Rec, t.left, { width: W(1.4), alpha: 0.55, lift: 0.03, ...mk }); ink(Rec, t.right, { width: W(1.6), alpha: 0.55, lift: 0.02, ...mk }) }
        for (const t of TEETH) { ink(Rec, t.left, { width: W(2), lift: 0.03 }); ink(Rec, t.right, { width: W(2.8), lift: 0.02 }); ink(Rec, [mix(t.base, t.tip, 0.15), mix(t.base, t.tip, 0.7)].map(p => add(p, [1.5, 0])), { width: W(0.8), alpha: 0.45, lift: 0.01, hand: 0.4 }) }
        const tm = { mask: TEETH.map(t => m(t.poly)) }
        ink(Rec, TONGUE.left, { width: W(2.6), ...tm }); ink(Rec, TONGUE.right, { width: W(3.2), ...tm })
        ink(Rec, curve(TONGUE.mid.slice(4, -4), 1), { width: W(1.4), alpha: 0.7, ...tm })
        for (const f of FORK) ink(Rec, f, { width: W(2.4) })
      },
      horns(Rec) {
        const mB = { mask: [m(HORN_A.poly), m(TINE.poly), m(OUTLINE)] }, mA = { mask: [m(OUTLINE)] }
        ink(Rec, HORN_B.left, { width: W(3), ...mB }); ink(Rec, HORN_B.right, { width: W(3.6), ...mB })
        ink(Rec, HORN_A.left, { width: W(3.4), ...mA }); ink(Rec, HORN_A.right, { width: W(4.4), ...mA })
        ink(Rec, TINE.left, { width: W(3), mask: [m(HORN_A.poly)] }); ink(Rec, TINE.right, { width: W(3.6), mask: [m(HORN_A.poly)] })
        // growth rings: arcs across each horn, heavier on the shadow (lower) side
        for (const [T, n, mk] of [[HORN_A, 16, mA], [HORN_B, 12, mB], [TINE, 7, { mask: [m(HORN_A.poly)] }]])
          for (const c of across(T, n, 0.18, 0.05, 0.85)) ink(Rec, c, { width: W(1.5), lift: 0.02, weight: u => 0.4 + 0.9 * u, ...mk })
        for (const g of along(HORN_A, 3, 0.05, 0.9)) ink(Rec, g, { width: W(0.9), alpha: 0.55, lift: 0.02, ...mA })
      },
      brows(Rec) {
        BROWS.forEach((b, i) => { const mk = { mask: [...BROWS.slice(i + 1).map(x => m(x.poly)), m(EYEBALL)] }; ink(Rec, b.left, { width: W(2.8), ...mk }); ink(Rec, b.right, { width: W(3.4), ...mk }); for (const s of along(b, 3, 0.03, 0.9)) ink(Rec, s, { width: W(1), alpha: 0.7, lift: 0.02, ...mk }) })
        for (const f of FINS) { ink(Rec, f.poly, { width: W(2.6), mask: [m(OUTLINE)] }); for (const r of f.ribs) ink(Rec, r, { width: W(1.2), mask: [m(OUTLINE)], lift: 0.02 }) }
      },
      mane(Rec) {
        const drawMass = (M_, mk, wt) => M_.locks.forEach((l, k) => {
          const mm = { mask: [...mk.mask, ...M_.locks.slice(k + 1).map(x => m(x.poly))] }
          ink(Rec, l.left, { width: W(2.4 * wt), ...mm }); ink(Rec, l.right, { width: W(3 * wt), ...mm })
          for (const st of along(l, 4, 0.03, 0.9)) ink(Rec, st, { width: W(1), alpha: 0.7, lift: 0.015, weight: u => 1.2 - 0.8 * u, ...mm })
        })
        MANE.forEach((l, i) => drawMass(l, { mask: maneMask(i) }, 1))
        BEARD.forEach((l, i) => drawMass(l, { mask: [m(OUTLINE), ...BEARD.slice(i + 1).flatMap(b => b.polys.map(m))] }, 0.9))
      },
      whiskers(Rec) {
        // one stroke each, pressed at the root and lifting off toward the tip, the way a whisker is really drawn
        for (const [T, w] of [[WHISK_A, 5.2], [WHISK_B, 4.2]]) Rec.ink(m(T.mid), { color: LEAD, width: w, speed: 320, grain: 0.3, weight: u => Math.max(0.12, 1 - 0.95 * Math.pow(u, 0.8)) })
      },
      jawDetail(Rec) {
        for (const c of THROAT_PLATES) ink(Rec, c, { width: W(1.6), lift: 0.02, mask: [m(MOUTH)] })
        for (const sc of JAW_SCALES) ink(Rec, sc.blob, { hand: 0.35, width: W(0.7 + 0.8 * sc.k), alpha: 0.25 + 0.65 * sc.k, lift: 0.012, speed: 800, weight: u => 0.35 + 1.1 * Math.max(0, Math.sin(2 * Math.PI * u - 0.6)) })
        for (const l of LABIALS) ink(Rec, l, { width: W(1.4), lift: 0.015, speed: 700, alpha: 0.85 })
        for (const sc of CHEEK_SCALES) ink(Rec, sc.blob, { hand: 0.35, mask: [m(EYE_RING)], width: W(0.7 + 0.8 * sc.k), alpha: 0.25 + 0.65 * sc.k, lift: 0.012, speed: 800, weight: u => 0.5 + 0.9 * Math.max(0, Math.sin(2 * Math.PI * u - 0.6)) })
        for (const sc of SKULL_SCALES) ink(Rec, sc.blob, { hand: 0.35, width: W(0.8 + 0.9 * sc.k), alpha: 0.25 + 0.65 * sc.k, lift: 0.012, speed: 800, mask: [...BROWS.map(b => m(b.poly)), m(HORN_A.poly), m(HORN_B.poly), m(EYE_RING)], weight: u => 0.35 + 1.1 * Math.max(0, Math.sin(2 * Math.PI * u - 0.6)) })
        for (const w of HINGE_WRINKLES) ink(Rec, w, { width: W(1.6), lift: 0.02, weight: u => 1.3 - u })
      },
      // ------------------------------------------------ tone and light
      shade(Rec) {
        const sh = (P, o) => Rec.brush(m(P), { layer: 'shade', color: '#2d2c31', ...o })
        const hatch = (P, o) => Rec.hatch(m(P), { layer: 'shade', color: '#3a393f', width: 1.2, ...o })
        Rec.fill(m(OUTLINE), { layer: 'shade', color: '#b3b2b6', width: 22, alpha: 0.18, soft: 4, angle: 0.5, mask: [m(MOUTH), m(EYEBALL)] })
        // the form: underside of the jaw, cheek hollow, under the brow, the side of the snout toward the lip
        hatch(curve([...JAW.slice(0, -1).map(p => add(p, [0, -18])), ...JAW.slice(0, -1).reverse()], 3, true), { spacing: 3.4, angle: 0.3, alpha: 0.6 })
        hatch([[390, 250], [440, 236], [498, 262], [510, 300], [440, 318], [392, 300]], { spacing: 3.6, angle: -1.0, alpha: 0.7 })
        hatch([[300, 112], [330, 100], [410, 100], [440, 124], [400, 120], [360, 108], [320, 118]], { spacing: 2.6, angle: -0.5 })
        hatch([[80, 170], [300, 196], [345, 222], [300, 214], [80, 186]], { spacing: 3.4, angle: 1.2, alpha: 0.6 })
        sh(curve([[330, 166], [400, 180], [470, 214]], 5), { width: 20 * S, alpha: 0.3, soft: 6 })
        const plane = (P, w, a, col = '#4a494f') => Rec.brush(m(curve(P, 6)), { layer: 'shade', color: col, width: w * S, alpha: a, soft: 12, clip: m(OUTLINE), mask: [m(MOUTH)] })
        plane([[70, 176], [180, 186], [300, 200], [360, 222]], 44, 0.3)            // side of the snout, darker toward the lip
        plane([[140, 420], [240, 414], [340, 384], [440, 336], [500, 306]], 54, 0.5) // the jaw's underside, turned from the light
        plane([[380, 290], [440, 300], [500, 290]], 60, 0.4)                       // under the cheekbone
        plane([[420, 70], [500, 90], [548, 130]], 40, 0.25)                        // back of the skull
        for (const sc of [...SNOUT_SCALES, ...CHEEK_SCALES, ...JAW_SCALES, ...SKULL_SCALES, ...EYE_SCALES]) Rec.brush(m(sc.blob.slice(3, 10).map(p => mix(p, sc.c, 0.25))), { layer: 'shade', color: '#3a393f', width: sc.size * 0.28 * S, alpha: 0.1 + 0.28 * (sc.k ?? 1), soft: 1.4, lift: 0.01, speed: 1400 })
        sh(curve([[120, 400], [240, 392], [360, 350], [470, 312]], 5), { width: 24 * S, alpha: 0.4, soft: 7 })
        // teeth: a shadow down the back of each, gums darker at the roots
        for (const t of TEETH) Rec.brush(m(t.right), { layer: 'shade', color: '#4a494f', width: 5 * S, alpha: 0.5, soft: 1.5, clip: m(t.poly) })
        hatch([...GUM_U, ...UPLIP.slice(1).reverse()], { spacing: 2.4, angle: 1.3, alpha: 0.9, mask: TEETH.map(t => m(t.poly)) })
        hatch([...GUM_L, ...LOLIP.slice(0, -1).reverse()], { spacing: 2.4, angle: -1.3, alpha: 0.9, mask: TEETH.map(t => m(t.poly)) })
        // tongue: rounded, with a wet groove
        Rec.fill(m(TONGUE.poly), { layer: 'shade', color: '#7d7c82', width: 10, alpha: 0.55, soft: 2, angle: 0.4 })
        Rec.brush(m(TONGUE.right), { layer: 'shade', color: '#2d2c31', width: 14 * S, alpha: 0.55, soft: 3, clip: m(TONGUE.poly) })
        // horns: round, so the shadow runs down the side away from the light
        for (const T of [HORN_A, HORN_B, TINE]) Rec.brush(m(T.right), { layer: 'shade', color: '#2d2c31', width: 14 * S, alpha: 0.5, soft: 4, clip: m(T.poly), mask: T === HORN_A ? [m(OUTLINE)] : [m(OUTLINE), m(HORN_A.poly)] })
        // mane: dark at the roots, lighter toward the tips
        MANE.forEach((M_, i) => M_.locks.forEach((l, k) => { const mk = [...maneMask(i), ...M_.locks.slice(k + 1).map(x => m(x.poly))]; Rec.brush(m(l.mid.slice(0, 14)), { layer: 'shade', color: '#3a393f', width: 26 * S, alpha: 0.45, soft: 6, clip: m(l.poly), mask: mk }); Rec.brush(m(l.right), { layer: 'shade', color: '#3a393f', width: 9 * S, alpha: 0.4, soft: 3, clip: m(l.poly), mask: mk }) }))
        BEARD.forEach(M_ => M_.locks.forEach(l => Rec.brush(m(l.mid.slice(0, 14)), { layer: 'shade', color: '#3a393f', width: 20 * S, alpha: 0.45, soft: 5, clip: m(l.poly), mask: [m(OUTLINE)] })))
      },
      darks(Rec) {
        // the darkest darks: throat, nostril, the eye's pupil and iris rim, the corner of the mouth
        // the roof of the mouth catches a little light near the front teeth; the throat is the black
        Rec.fill(m(MOUTH_IN), { layer: 'deep', color: '#161519', width: 12, alpha: 0.96, mask: [...TEETH.map(t => m(t.poly)), ...TEETH_FAR.map(t => m(t.poly)), m(TONGUE.poly)], angle: -0.3 })
        for (const t of TEETH_FAR) Rec.fill(m(t.poly), { layer: 'deep', color: '#8a898e', width: 5, alpha: 0.9, mask: TEETH.map(x => m(x.poly)) })
        Rec.brush(m(curve(GUM_U.slice(0, 5).map(p => add(p, [4, 18])), 5)), { layer: 'top', color: '#55545a', width: 22 * S, alpha: 0.5, soft: 8, clip: m(MOUTH_IN), mask: TEETH.map(t => m(t.poly)) })
        for (let k = 0; k < 5; k++) Rec.brush(m(curve([[120 + k * 40, 240 + k * 4], [150 + k * 40, 262 + k * 4], [176 + k * 40, 270 + k * 4]], 4)), { layer: 'top', color: '#4a494f', width: 3 * S, alpha: 0.6, soft: 1, clip: m(MOUTH_IN), mask: [...TEETH.map(t => m(t.poly)), m(TONGUE.poly)] })   // palate ridges
        Rec.fill(m(NOSTRIL_HOLE), { layer: 'deep', color: '#161519', width: 5, alpha: 0.95 })
        // iris: a mid tone, darker at the rim and under the upper lid's shadow; the pupil is the blackest mark on the head
        Rec.fill(m(EYEBALL), { layer: 'shade', color: '#8c8b90', width: 8, alpha: 0.75, mask: [m(PUPIL)] })
        Rec.brush(m(curve(EYEBALL.slice(0, Math.floor(EYEBALL.length * 0.55)), 1)), { layer: 'shade', color: '#2a292e', width: 16 * S, alpha: 0.65, soft: 5, clip: m(EYEBALL), mask: [m(PUPIL)] })
        Rec.brush(m(EYEBALL), { layer: 'shade', color: '#3a393f', width: 6 * S, alpha: 0.55, soft: 2, clip: m(EYEBALL) })
        for (const dx of [-2.5, 0, 2.5]) Rec.brush(m([[EYE_C[0] + dx * 0.3, EYE_C[1] - 22], [EYE_C[0] + dx, EYE_C[1]], [EYE_C[0] + dx * 0.3, EYE_C[1] + 24]]), { layer: 'deep', color: '#0b0b0d', width: 5 * S, alpha: 1, hand: 0, clip: m(PUPIL) })
        Rec.brush(m(curve(LID_FOLD.map(p => add(p, [0, 6])), 5)), { layer: 'shade', color: '#2d2c31', width: 16 * S, alpha: 0.45, soft: 5, mask: [m(EYEBALL)] })
        Rec.brush(m([[378, 242], [388, 246]]), { layer: 'deep', color: '#0e0e10', width: 9 * S, alpha: 0.9 })
        Rec.brush(m(curve(BROW.map(p => add(p, [0, 10])), 5)), { layer: 'deep', color: '#1d1c21', width: 7 * S, alpha: 0.55, soft: 2 })
      },
      highlights(Rec) {
        const hi = (P, w, a = 0.9) => Rec.brush(m(P), { layer: 'top', color: '#f8f7f3', width: w * S, alpha: a, soft: 1, hand: 0 })
        hi(curve([[344, 118], [350, 114], [356, 114]], 3), 6, 1); hi([[347, 125], [348, 125]], 3, 0.9); hi(curve([[372, 148], [384, 146]], 3), 3, 0.55)                               // eye glints
        hi(curve([[100, 108], [180, 98], [260, 92]], 5), 5, 0.6)                                             // snout ridge
        hi(curve([[330, 96], [360, 90], [392, 94]], 4), 4, 0.6)                                               // brow
        for (const t of TEETH) hi([mix(t.base, t.tip, 0.35), mix(t.base, t.tip, 0.8)].map(p => add(p, [-1.5, 0])), 2.4, 0.9)
        hi(curve(TONGUE.mid.slice(6, 30).map(p => add(p, [0, -4])), 1), 3, 0.55)
        hi(curve(HORN_A.mid.slice(4, 44).map((p, i) => mix(p, HORN_A.left[i + 4], 0.45)), 1), 3.5, 0.55)
        hi(curve([[370, 180], [420, 190]], 3), 4, 0.4)
      },
    }
  }
  const api = { make }
  if (typeof module !== 'undefined' && module.exports) module.exports = api
  else root.HEAD = api
})(typeof window !== 'undefined' ? window : globalThis)
