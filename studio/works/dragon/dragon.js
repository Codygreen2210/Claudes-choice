// How to draw a dragon: the drawing, recorded stroke by stroke with timelapse.js.
// An original dragon (a sitting, friendly western dragon), built the way drawing tutorials teach it:
// simple shapes, a line of action, the forms, then ink, colour and light. Space is 1000 x 1000.
// Works in the browser (window.DRAGON) and in Node (require), so the sound can be timed to the same strokes.
(function (root) {
  function build(TL) {
    // ---------------------------------------------------------------- geometry helpers
    const curve = (P, n = 10, closed = false) => {            // Catmull-Rom through the points
      const out = [], m = P.length, get = i => closed ? P[(i + m) % m] : P[Math.max(0, Math.min(m - 1, i))]
      const segs = closed ? m : m - 1
      for (let i = 0; i < segs; i++) {
        const p0 = get(i - 1), p1 = get(i), p2 = get(i + 1), p3 = get(i + 2)
        for (let k = 0; k < n; k++) {
          const t = k / n, t2 = t * t, t3 = t2 * t
          out.push([0, 1].map(j => 0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3)))
        }
      }
      out.push(closed ? P[0] : P[m - 1])
      return out
    }
    const circle = (cx, cy, r, a0 = -2.2, turns = 1.04, ry = r) => {
      const out = [], N = 48
      for (let i = 0; i <= N; i++) { const a = a0 + turns * 2 * Math.PI * i / N; out.push([cx + r * Math.cos(a), cy + ry * Math.sin(a)]) }
      return out
    }
    const slice = (P, a, b) => P.slice(a, b + 1)

    // ---------------------------------------------------------------- the forms
    // silhouette of head + neck + body + tail, clockwise from the top of the head
    const HEAD_TOP = [[600, 200], [660, 172], [722, 188], [785, 214], [846, 240]]
    const SNOUT = [[846, 240], [864, 272], [848, 300]]
    const JAW = [[848, 300], [792, 312], [746, 336], [706, 362]]
    const NECK_FRONT = [[706, 362], [662, 410], [634, 470], [628, 540], [604, 620], [562, 682], [492, 742], [420, 792], [338, 802]]
    const TAIL_IN = [[338, 802], [272, 782], [236, 830], [246, 886], [312, 924], [440, 940], [594, 934]]
    const TAIL_OUT = [[594, 934], [420, 976], [268, 970], [164, 914], [134, 820], [170, 720]]
    const BACK = [[170, 720], [230, 632], [300, 542], [390, 432], [480, 372], [546, 322], [588, 256], [600, 200]]
    const OUTLINE = [HEAD_TOP, SNOUT, JAW, NECK_FRONT, TAIL_IN, TAIL_OUT, BACK]
    const BODY = OUTLINE.flatMap((p, i) => (i ? p.slice(1) : p))
    const BODY_C = curve(BODY, 4, true)

    const BELLY = [...NECK_FRONT.slice(0, 7), [452, 700], [518, 642], [556, 582], [574, 522], [586, 462], [620, 412], [670, 372]]
    const FRONT_LEG = [[578, 592], [622, 642], [628, 730], [648, 790], [694, 810], [694, 832], [590, 832], [580, 800], [560, 722], [520, 652]]
    const BACK_LEG = [[300, 622], [382, 598], [452, 650], [466, 732], [456, 800], [470, 836], [506, 850], [506, 868], [400, 868], [406, 840], [410, 792], [360, 772], [300, 722]]
    const WING = [[396, 438], [362, 300], [382, 170], [272, 100], [160, 66], [180, 170], [120, 300], [176, 318], [200, 402], [256, 398], [300, 452], [304, 530]]
    const FAR_WING = [[452, 380], [470, 210], [566, 140], [540, 250], [512, 372]]
    const HORN1 = [[636, 194], [584, 136], [516, 100], [566, 164], [598, 214]]
    const HORN2 = [[690, 180], [650, 112], [598, 68], [626, 132], [652, 186]]
    const TAIL_TIP = [[566, 914], [648, 900], [616, 962], [572, 956]]
    const EYE = [[692, 236], [716, 222], [742, 232], [718, 250]]

    // spikes along the back, shrinking toward the tail
    const backC = curve(BACK, 10)
    const spikes = []
    for (let i = 8; i < backC.length - 6; i += 7) {
      const a = backC[i - 3], b = backC[i + 3], mid = backC[i]
      const dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy)
      const h = 18 + 22 * (i / backC.length)                    // bigger near the head
      const nx = dy / l, ny = -dx / l                          // outward (up and back)
      spikes.push([a, [mid[0] + nx * h - dx / l * 6, mid[1] + ny * h - dy / l * 6], b])
    }

    // palette: teal dragon, warm belly, coral wings, on warm paper with a soft sun behind
    const C = { body: '#1fa58f', bodyD: '#136560', belly: '#f5d38c', bellyD: '#cfa96e', wing: '#f06a42', wingD: '#b8402b',
      horn: '#f1e6cc', hornD: '#c9b58f', eye: '#f2b233', shadow: '#d8cdb9', sun: '#f8cf86', ink: '#1d1b22' }

    // ---------------------------------------------------------------- the lesson
    const R = TL.recorder({ lift: 0.2, stepPause: 0.3 })

    R.step('Start with three circles', 'head, chest and hips')
    R.pencil(circle(690, 252, 76)).pencil(circle(560, 540, 122)).pencil(circle(352, 700, 112))

    R.step('Add a line of action', 'one easy curve from nose to tail')
    R.pencil(curve([[850, 270], [690, 252], [600, 380], [560, 540], [352, 700], [170, 850], [300, 955], [594, 934]], 12), { width: 4 })

    R.step('Block in the head', 'a box for the snout, then the horns')
    R.pencil([[748, 212], [856, 240], [856, 302], [748, 330]])
    R.pencil(curve(HORN1, 6)).pencil(curve(HORN2, 6))

    R.step('Wrap the body', 'join the circles, let the tail taper')
    R.pencil(curve(NECK_FRONT, 8)).pencil(curve(BACK.slice().reverse(), 8)).pencil(curve([...TAIL_IN.slice(1), ...TAIL_OUT.slice(1)], 8))

    R.step('Add the legs', 'ovals for the joints, then the paws')
    R.pencil(circle(600, 700, 50, -2, 1.02, 70)).pencil([[620, 760], [640, 820], [694, 822]])
    R.pencil(circle(386, 700, 72)).pencil([[440, 760], [460, 845], [506, 858]])

    R.step('Build the wing', 'bones first, like a big hand')
    R.pencil([[396, 438], [362, 300], [382, 170], [160, 66]], { width: 4 })
    R.pencil([[382, 170], [120, 300]], { width: 4 }).pencil([[382, 170], [200, 402]], { width: 4 }).pencil([[382, 170], [300, 452]], { width: 4 })
    R.pencil(curve([[470, 380], [470, 210], [566, 140]], 6))

    R.step('Ink the final lines', 'go over what you want to keep')
    for (const part of OUTLINE) R.ink(curve(part, 8))
    R.ink(curve(HORN1, 6)).ink(curve(HORN2, 6))
    R.ink(curve(slice(BELLY, 7, 13), 8), { width: 5 })
    for (let i = 1; i < 7; i++) R.ink([BELLY[i], BELLY[13 - i]], { width: 3 })       // belly plates
    R.ink(curve(FRONT_LEG.slice(1, 9), 6)).ink(curve(BACK_LEG.slice(1), 6))
    R.ink(curve(slice(WING, 0, 11), 6)).ink([[382, 170], [120, 300]], { width: 4 }).ink([[382, 170], [200, 402]], { width: 4 }).ink([[382, 170], [300, 452]], { width: 4 })
    R.ink(curve(FAR_WING.slice(0, 4), 6), { width: 5 })
    for (const s of spikes) R.ink(s, { width: 5 })
    R.ink(curve(TAIL_TIP, 5, true))
    R.ink(curve(EYE, 6, true), { width: 5 }).ink([[716, 226], [716, 246]], { width: 7 })
    R.ink([[832, 256], [840, 262]], { width: 6 })                                            // nostril
    R.ink(curve([[850, 292], [800, 300], [760, 318]], 6), { width: 4 })                       // smile

    R.step('Erase the guides', 'the ink does the talking now')
    R.erase('guide', 1.4)

    R.step('Lay in base colours', 'big flat areas first')
    R.fill(circle(470, 520, 380), { layer: 'bg', color: C.sun, width: 90, alpha: 0.8 })
    R.fill(circle(440, 905, 330, 0, 1, 40), { layer: 'bg', color: C.shadow, width: 40, angle: 0 })
    R.fill(FAR_WING, { color: C.wingD, width: 30 })
    R.fill(WING, { color: C.wing })
    R.fill(BODY_C, { color: C.body, width: 56 })
    R.fill(BACK_LEG, { color: C.body, width: 36 }).fill(FRONT_LEG, { color: C.body, width: 30 })
    R.fill(BELLY, { color: C.belly, width: 30 })
    R.fill(HORN1, { color: C.horn, width: 16 }).fill(HORN2, { color: C.horn, width: 16 })
    for (const s of spikes) R.fill(s, { color: C.horn, width: 10 })
    R.fill(TAIL_TIP, { color: C.wing, width: 16 })
    R.fill(EYE, { color: C.eye, width: 10 })

    R.step('Paint the shadows', 'light comes from the top right')
    const shade = (pts, color, clip, w = 34, alpha = 0.55) => R.brush(curve(pts, 8), { layer: 'shade', color, clip, width: w, alpha })
    shade([[300, 560], [230, 650], [175, 740], [150, 840], [190, 920], [300, 960]], C.bodyD, BODY_C, 50)
    shade([[560, 330], [470, 390], [380, 470]], C.bodyD, BODY_C, 40)
    shade([[700, 350], [650, 400], [640, 440]], C.bodyD, BODY_C, 26)
    shade([[470, 700], [540, 660], [590, 600], [610, 520]], C.bellyD, BELLY, 26)
    shade([[330, 650], [320, 720], [370, 770]], C.bodyD, BACK_LEG, 34)
    shade([[560, 700], [580, 790], [600, 830]], C.bodyD, FRONT_LEG, 26)
    shade([[360, 300], [300, 380], [300, 450]], C.wingD, WING, 44)
    shade([[330, 180], [220, 200], [180, 280]], C.wingD, WING, 30, 0.4)
    shade([[590, 130], [610, 190]], C.hornD, HORN1, 14)
    shade([[630, 110], [650, 170]], C.hornD, HORN2, 14)

    R.step('Finish with highlights', 'a few bright touches make it pop')
    const hi = (pts, w, a = 0.85, color = '#fffaf0') => R.brush(pts, { layer: 'top', color, width: w, alpha: a })
    hi([[724, 229], [726, 231]], 7, 1)                                                              // eye glint
    hi(curve([[640, 196], [690, 186], [740, 200]], 6), 9, 0.6)
    hi(curve([[520, 350], [450, 400], [390, 460]], 6), 10, 0.45)
    hi(curve([[800, 232], [836, 248]], 4), 7, 0.6)
    hi(curve([[330, 150], [230, 110]], 4), 8, 0.5)
    hi(curve([[620, 150], [590, 118]], 4), 6, 0.7)
    R.wait(0.4)
    return R
  }
  const api = { build }
  if (typeof module !== 'undefined' && module.exports) module.exports = api
  else root.DRAGON = api
})(typeof window !== 'undefined' ? window : globalThis)
