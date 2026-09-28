// claw.js: a dragon's forefoot built from anatomy, in a grip. Local space: the wrist at (0, 0), the forearm coming
// down from the upper right, the fingers reaching forward (to the left) and curling down around nothing. y down.
// CLAW.make(SH, placement, opts) maps it into the drawing and returns what it hides plus one function per stage.
(function (root) {
  function make(SH, where, { seed = 1, reach = 1, grip = 1, under = [] } = {}) {
    const { add, sub, mix, unit, perp, rot, curve, tube, across, along, resample } = SH
    const M = SH.place(where), m = P => P.map(M), S = where.s, R = SH.rng(seed * 97 + 3), v = () => R() - 0.5

    // ---------------------------------------------------------------- the forearm
    // forearm, wrist and hand are one form: the muscle swells below the elbow, narrows to the wrist, then widens into the palm
    const WRIST_U = 0.74
    const ARM = tube(curve([[210, -250], [150, -170], [72, -82], [16, -22], [-34, -4], [-70, 0]], 10),
      u => u < WRIST_U ? 62 + 30 * Math.sin(Math.PI * Math.min(1, u / WRIST_U * 1.25)) * (1 - 0.5 * Math.min(1, Math.max(0, (u - 0.35) / 0.3)) ** 2) - 8 * u / WRIST_U
                       : 50 + 50 * Math.sin(Math.PI / 2 * Math.min(1, (u - WRIST_U) / (1 - WRIST_U) * 1.3)), 70)
    const ELBOW_CREASE = [0.18, 0.26].map(u => { const i = Math.round(u * (ARM.mid.length - 1)); return curve([ARM.left[i], add(mix(ARM.left[i], ARM.right[i], 0.5), unit(sub(ARM.mid[i + 1], ARM.mid[i - 1])), 6), ARM.right[i]], 4) })
    const SPUR = curve([[36, -34], [60, -44], [92, -44], [66, -30], [44, -18]], 4, true)   // a spur on the back of the wrist

    // ---------------------------------------------------------------- hand and fingers
    // A finger is one continuous form, not stacked segments: a smooth spine through its joints, a width that
    // tapers from the palm, and a swelling at each knuckle. Positive bends curl it down (into a grip).
    function finger(base, dir, lens, w0, bends) {
      let d = unit(dir), p = base
      const joints = [base], dirs = [d]
      lens.forEach((L, i) => { p = add(p, d, L * reach); joints.push(p); d = rot(d, -bends[i] * grip); dirs.push(d) })
      const spine = curve(joints, 8), total = SH.pathLen(spine)
      const ju = []; { let acc = 0; lens.forEach(L => { acc += L * reach; ju.push(acc / total) }) }
      const T = tube(spine, u => w0 * (1 - 0.42 * u) * (1 + 0.16 * Math.max(0, ...ju.slice(0, -1).map(j => 1 - Math.abs(u - j) / 0.08))), 48)
      // the talon grows from the end, continuing the curl hard; keel along it, a sheath (cuticle) at its root
      // the talon hooks the same way its own finger curls (the thumb curls the other way from the rest)
      const tw = w0 * 0.6, TL = w0 * 2.4 * reach, c = -0.95 * grip * Math.sign(bends.reduce((a, b) => a + b, 0))
      let n = perp(d); { const ch = sub(rot(d, c), d); if (n[0] * ch[0] + n[1] * ch[1] > 0) n = [-n[0], -n[1]] }   // n points to the outside of the hook
      const tip = add(p, rot(d, c), TL)
      const back = [add(p, n, tw / 2), add(add(p, rot(d, c * 0.25), TL * 0.45), n, tw * 0.42), add(add(p, rot(d, c * 0.65), TL * 0.82), n, tw * 0.12), tip]
      const belly = [tip, add(add(p, rot(d, c * 0.8), TL * 0.6), n, -tw * 0.08), add(add(p, rot(d, c * 0.35), TL * 0.28), n, -tw * 0.42), add(p, n, -tw / 2)]
      const talon = { back: curve(back, 6), belly: curve(belly, 6), poly: curve([...back, ...belly.slice(1)], 6),
        keel: curve([add(p, n, tw * 0.08), add(add(p, rot(d, c * 0.3), TL * 0.4), n, tw * 0.16), add(add(p, rot(d, c * 0.7), TL * 0.78), n, tw * 0.04)], 5),
        sheath: curve([add(add(p, d, -4), n, tw * 0.55), add(add(p, d, 3), n, 0), add(add(p, d, -4), n, -tw * 0.55)], 4) }
      // the top of a finger is the outside of its curl; the tube's left/right depends on which way it points
      const bendDir = sub(dirs[1], dirs[0]), leftInner = (T.normals[0][0] * bendDir[0] + T.normals[0][1] * bendDir[1]) > 0
      const top = leftInner ? T.right : T.left, bot = leftInner ? T.left : T.right
      return { T, top, bot, joints, ju, dirs, talon, w0, polys: [T.poly, talon.poly], segs: [{ T }] }
    }
    // fingers reach forward and curl down; the thumb comes round underneath the other way
    const F = [
      finger([-62, -38], [-1, -0.3], [50, 40, 30], 30, [0.45, 0.55, 0.5]),
      finger([-74, -6], [-1, 0], [58, 46, 34], 34, [0.5, 0.6, 0.55]),
      finger([-64, 28], [-1, 0.32], [52, 42, 30], 31, [0.5, 0.6, 0.55]),
      finger([-18, 26], [-0.75, 1], [36, 28], 28, [-0.3, -0.4]),
    ]
    // the palm grows out of the wrist and fans to the finger roots
    const wi = Math.round(WRIST_U * (ARM.mid.length - 1))
    const PALM = [...ARM.left.slice(wi), ...ARM.right.slice(wi).reverse()]
    const WRIST = curve([ARM.left[wi], add(mix(ARM.left[wi], ARM.right[wi], 0.5), [-8, 2]), ARM.right[wi]], 5)
    const KNUCKLES = curve([add(F[0].joints[0], [14, 4]), add(F[1].joints[0], [16, 2]), add(F[2].joints[0], [14, -2])], 6)
    // the order they sit in, far to near: the first finger is furthest away
    const ORDER = [0, 1, 3, 2]
    const hides = i => { const k = ORDER.indexOf(i); return ORDER.slice(k + 1).flatMap(j => F[j].polys) }
    const ALL = [ARM.poly, PALM, ...F.flatMap(f => f.polys)]

    // ---------------------------------------------------------------- scales
    // forearm: packed scales, big plates down its front (outer) edge, small ones behind
    const pebbles = (poly, size, sd, sizeAt = () => 1) => {
      const Rr = SH.rng(sd), pts = [], xs = poly.map(p => p[0]), ys = poly.map(p => p[1])
      for (let y = Math.min(...ys) - size, row = 0; y < Math.max(...ys) + size; row++, y += size * 0.86) {
        for (let x = Math.min(...xs) - size + (row % 2) * size / 2; x < Math.max(...xs) + size;) { const k = sizeAt([x, y]); pts.push([x + size * k * 0.55 * (Rr() - 0.5), y + size * k * 0.55 * (Rr() - 0.5)]); x += size * k * (0.85 + 0.3 * Rr()) }
      }
      return SH.cells(pts, size * 1.6).map((cell, i) => ({ cell, c: pts[i] })).filter(o => o.cell.length > 2 && SH.inside(o.c, poly)).map(o => ({ c: o.c, blob: SH.inset(o.cell, 0.82).poly }))
    }
    const LIGHT = unit([-0.6, -0.8]), armLit = (ARM.normals[20][0] * LIGHT[0] + ARM.normals[20][1] * LIGHT[1]) > 0
    const ARM_SHADOW = armLit ? ARM.right : ARM.left, ARM_LIGHT = armLit ? ARM.left : ARM.right
    const ARM_SCALES = pebbles([...ARM.left.slice(0, wi + 1), ...ARM.right.slice(0, wi + 1).reverse()], 14, seed + 5, p => 0.8 + 0.5 * Math.min(1, Math.max(0, (p[0] - p[1] * 0.3) / 180)))
    const PALM_SCALES = pebbles(PALM, 12, seed + 9)
    const PLATES = across(ARM, 9, 0.22, 0.3, 0.95).map(c => c.slice(0, Math.ceil(c.length * 0.45)))   // big scutes on the leading edge

    // ---------------------------------------------------------------- drawing
    const LEAD = '#2e2d33'
    const ink = (Rec, P, o = {}) => Rec.ink(m(P), { color: LEAD, width: 3, grain: Math.min(0.65, 1.3 / Math.max(1, o.width ?? 3)), ...o })
    const inkAt = (Rec, P, o = {}) => ink(Rec, P, { ...o, width: (o.width ?? 3) * S })
    const hidesArm = F.flatMap(f => f.polys)                 // the fingers sit in front of the arm-and-hand form
    const armMask = () => [...hidesArm.map(m), ...under]         // and the arm's root emerges from under the body
    return {
      FRONT: [...(() => {
        // the arm hides what's behind it only from where each of its edges comes out from under the body; the edges
        // cross the body's outline at a slant, so each side gets its own exit point
        const exit = E => { const i = E.findIndex(p => !under.some(u => SH.inside(M(p), u))); return i < 0 ? E.length - 1 : i }
        const iL = exit(ARM.left), iR = exit(ARM.right)
        return [[...ARM.left.slice(iL), ...ARM.right.slice(iR).reverse()].map(M)]
      })(), ...[PALM, ...F.flatMap(f => f.polys)].map(m)], place: M, local: { ARM, PALM, F },
      root: M(ARM.mid[0]),
      construct(Rec) {
        Rec.pencil(m(curve(ARM.mid, 1)), { speed: 650 })
        Rec.pencil(m(SH.circle([0, 0], 30, 0, 1.03)), { speed: 650 })
        for (const f of F) Rec.pencil(m([...f.joints, f.talon.back.at(-1)]), { speed: 650 })
        for (const f of F) for (const j of f.joints.slice(0, -1)) Rec.pencil(m(SH.circle(j, 9, 0, 1.03)), { speed: 700, lift: 0.04 })
      },
      ink(Rec) {
        const mk = { mask: armMask() }
        inkAt(Rec, ARM.left, { width: 3.4, ...mk, weight: u => 0.8 + 0.4 * u }); inkAt(Rec, ARM.right, { width: 4.2, ...mk, weight: u => 1.2 - 0.3 * u })
        inkAt(Rec, curve([ARM.left.at(-1), add(ARM.mid.at(-1), [-10, 0]), ARM.right.at(-1)], 6), { width: 3, ...mk })
        for (const c of ELBOW_CREASE) inkAt(Rec, c, { width: 1.8, clip: m(ARM.poly), ...mk })
        inkAt(Rec, WRIST, { width: 1.8, alpha: 0.8, mask: F.flatMap(f => f.polys).map(m) })
        inkAt(Rec, KNUCKLES, { width: 1.8, alpha: 0.8, mask: F.flatMap(f => f.polys).map(m) })
        for (const i of ORDER) {
          const f = F[i], hm = { mask: hides(i).map(m) }
          const T = f.T, fm = { mask: [...hm.mask, m(f.talon.poly)] }, top = f.top, bot = f.bot
          inkAt(Rec, top, { width: 2.8, ...fm, weight: u => 1.1 - 0.4 * u }); inkAt(Rec, bot, { width: 3.8, ...fm, weight: u => 1.2 - 0.3 * u })
          // scutes: overlapping plates across the top of the finger, shrinking toward the tip
          const nS = 11
          for (let k = 0; k < nS; k++) {
            const u = 0.06 + 0.88 * k / nS, ii = Math.round(u * (T.mid.length - 1)), a = top[ii], b = bot[ii], dd = unit(sub(T.mid[Math.min(T.mid.length - 1, ii + 1)], T.mid[Math.max(0, ii - 1)]))
            inkAt(Rec, curve([add(a, dd, -2), add(mix(a, b, 0.3), dd, 5), add(mix(a, b, 0.6), dd, 2)], 4), { width: 1.6 - 0.6 * u, lift: 0.012, ...fm })
          }
          // the lateral line: plates on top, fine granular scales down the side
          inkAt(Rec, T.mid.map((p, k) => mix(top[k], bot[k], 0.6)).slice(2, -3), { width: 1.2, alpha: 0.75, ...fm })
          for (let k = 3; k < T.mid.length - 5; k += 2) for (const q of [0.72, 0.86]) { const c = mix(top[k + (q > 0.8 ? 1 : 0)], bot[k + (q > 0.8 ? 1 : 0)], q); inkAt(Rec, SH.circle(c, 2.6 * (1 - 0.4 * k / T.mid.length), 0, 1, 2.2, 8), { width: 0.9, alpha: 0.55, hand: 0.2, lift: 0.006, speed: 500, ...fm }) }
          // joints: a crease across the top, and a pad bulging underneath
          f.ju.slice(0, -1).forEach(u => {
            const ii = Math.round(u * (T.mid.length - 1)), a = top[ii], b = bot[ii], dd = unit(sub(T.mid[ii + 1], T.mid[ii - 1]))
            inkAt(Rec, curve([a, add(mix(a, b, 0.4), dd, 6), mix(a, b, 0.62)], 4), { width: 2, lift: 0.015, ...fm })
            const out = unit(sub(bot[ii], T.mid[ii]))
            inkAt(Rec, curve([bot[Math.max(0, ii - 5)], add(bot[ii], out, 5), bot[Math.min(T.mid.length - 1, ii + 5)]], 4), { width: 2.4, lift: 0.015, ...fm })
          })
          const t = f.talon
          inkAt(Rec, t.sheath, { width: 1.8, ...hm })
          inkAt(Rec, t.back, { width: 2.8, color: '#1b1a1e', ...hm, weight: u => 1 - 0.6 * u })
          inkAt(Rec, t.belly, { width: 3.4, color: '#1b1a1e', ...hm, weight: u => 0.4 + 0.8 * u })
          inkAt(Rec, t.keel, { width: 1.2, alpha: 0.7, ...hm })
        }
        for (const sc of ARM_SCALES) inkAt(Rec, sc.blob, { clip: m(ARM.poly), width: 1.1, alpha: 0.75, hand: 0.3, lift: 0.01, speed: 800, mask: armMask(), weight: u => 0.35 + 1.1 * Math.max(0, Math.sin(2 * Math.PI * u - 0.6)) })
        for (const sc of PALM_SCALES) inkAt(Rec, sc.blob, { clip: m(PALM), width: 1, alpha: 0.7, hand: 0.3, lift: 0.01, speed: 800, mask: F.flatMap(f => f.polys).map(m) })
      },
      shade(Rec) {
        const sh = (P, o) => Rec.brush(m(P), { layer: 'shade', color: '#2d2c31', ...o })
        Rec.fill(m(ARM.poly), { layer: 'shade', color: '#a2a1a6', width: 20, alpha: 0.25, soft: 4, mask: armMask() })
        sh(ARM_SHADOW, { width: 30 * S, alpha: 0.5, soft: 8, clip: m(ARM.poly), mask: armMask() })
        for (const sc of ARM_SCALES) Rec.brush(m(sc.blob.slice(3, 10).map(p => mix(p, sc.c, 0.25))), { layer: 'shade', color: '#3a393f', width: 4 * S, alpha: 0.3, soft: 1.3, lift: 0.01, speed: 1400, mask: armMask() })
        Rec.brush(m(ARM_SHADOW.slice(wi - 6)), { layer: 'shade', color: '#2d2c31', width: 26 * S, alpha: 0.45, soft: 7, clip: m(ARM.poly), mask: F.flatMap(f => f.polys).map(m) })
        for (const i of ORDER) {
          const f = F[i], hm = hides(i).map(m)
          Rec.fill(m([...f.T.left.slice(4), ...f.T.right.slice(4).reverse()]), { layer: 'shade', color: '#9c9ba0', width: 10, alpha: 0.3, soft: 3, mask: hm })
          sh(f.bot, { width: 14 * S, alpha: 0.55, soft: 3, clip: m(f.T.poly), mask: hm })
          for (const u of f.ju.slice(0, -1)) { const ii = Math.round(u * (f.T.mid.length - 1)); sh([f.T.left[ii], f.T.right[ii]], { width: 7 * S, alpha: 0.3, soft: 3, clip: m(f.T.poly), mask: hm }) }
          // a cast shadow where each finger sits over the next
          sh(f.bot.map(p => add(p, [4, 6])), { width: 10 * S, alpha: 0.3, soft: 5, mask: [...f.polys.map(m)] })
          // talon: dark keratin, lighter toward the root, the underside darkest
          Rec.fill(m(f.talon.poly), { layer: 'deep', color: '#3a393f', width: 6, alpha: 0.85, mask: hm, hand: 0 })
          Rec.brush(m(f.talon.belly), { layer: 'deep', color: '#141316', width: 7 * S, alpha: 0.85, soft: 2, clip: m(f.talon.poly), mask: hm })
        }
      },
      darks(Rec) {
        Rec.brush(m(curve([F[0].joints[0], F[1].joints[0], F[2].joints[0]].map(p => add(p, [10, 0])), 5)), { layer: 'shade', color: '#2d2c31', width: 22 * S, alpha: 0.35, soft: 8 })
        // the deepest darks: the crease where the thumb tucks under, and between the fingers at the palm
        const between = [[-60, -30], [-84, -6], [-72, 26], [-18, 36]]
        for (let k = 0; k < 3; k++) Rec.brush(m([mix(between[k], between[k + 1], 0.3), mix(between[k], between[k + 1], 0.7)]), { layer: 'deep', color: '#1b1a1e', width: 7 * S, alpha: 0.6, soft: 3 })
      },
      highlights(Rec) {
        for (const i of ORDER) {
          const f = F[i], t = f.talon
          Rec.brush(m(t.back.slice(1, -3).map((p, k) => mix(p, t.keel[Math.min(t.keel.length - 1, k)], 0.35))), { layer: 'top', color: '#f2f1ed', width: 1.8 * S, alpha: 0.55, soft: 1, hand: 0, mask: hides(i).map(m) })
          Rec.brush(m(f.top.slice(3, -6).map((p, k) => mix(p, f.T.mid[k + 3], 0.35))), { layer: 'top', color: '#f2f1ed', width: 2.4 * S, alpha: 0.45, soft: 1, hand: 0, mask: hides(i).map(m) })
        }
        Rec.brush(m(ARM_LIGHT.slice(8, 40).map((p, k) => mix(p, ARM.mid[k + 8], 0.3))), { layer: 'top', color: '#f2f1ed', width: 4 * S, alpha: 0.35, soft: 2, hand: 0, mask: armMask() })
      },
    }
  }
  const api = { make }
  if (typeof module !== 'undefined' && module.exports) module.exports = api
  else root.CLAW = api
})(typeof window !== 'undefined' ? window : globalThis)
