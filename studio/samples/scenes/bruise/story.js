
// ------------------------------------------------------------------ the story
const YAW = 180;                                                    // he faces +z (the back wall behind him)
const T_HIT = 0.42;                                                 // beat 0: his shin hits the table edge
const LOOPSEED = { R: null, L: null };
function blinkAt(s) { const u = ((s + 40) % 3.7) / 0.16; return u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0; }
const F = fwdOf(YAW), Rt = rightOf(YAW), UP = V(0, 1, 0);
const STAND1 = { ...addPose(STAND, { spine1: [-4, 0, 0], neck: [6, 0, 0] }), armL: A(10, 14, 0, 22), armR: A(10, 14, 0, 22) };
const PH = { rot: 15, n: 0.0165, u: 0.0, w: 0.0, c: 40, th: 30, opp: 30 };   // the phone across his palm: fingers wrap its edge, thumb on the screen
function phoneHand() { const hd = wp(G.bones.head), n = UP.clone().multiplyScalar(0.62).addScaledVector(F, -0.78).normalize(), u = F.clone().multiplyScalar(0.78).addScaledVector(UP, 0.62).normalize();
  return { S: 'L', p: hd.clone().addScaledVector(F, 0.27).addScaledVector(Rt, 0.04).add(V(0, -0.32, 0)), n, u, c: PH.c, th: PH.th, opp: PH.opp, memAbs: 'phoneL', seed: A(40, 10, 0, 110, -40) }; }
const NOB = [0, 0, 0, 0, 0];

// the state at a time ----------------------------------------------
function guyAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  const face = { blink: blinkAt(lt + b * 1.3) };
  let pose = STAND1, root = { x: STANDP.x, y: 0.95, z: STANDP.z, yaw: YAW }, hands = [], show = true, cut = false;
  let step = 0, lift = 0, bA = NOB.slice(), bK = [2, 3, 1, 4, 2], bR = 1, macro = false, hit = -1, burst = false, leak = 0, poolK = 0, thin = 0, topK = 0, pills = false, shake = 0, phoneOn = true;
  if (b === 7 || b === 0) {                                         // reading his phone as he walks; (0) his shin slams the table edge
    hands = [b === 0 && LOOPSEED.L ? { ...phoneHand(), seed: LOOPSEED.L, seedIsPrev: true } : phoneHand()];
    pose = addPose(STAND1, { neck: [-16, 0, 0], head: [-10, 0, 0] }); Object.assign(face, { look: [0, -0.6] });
    if (b === 0) {
      step = lt < T_HIT ? sm(lt / T_HIT) * 0.85 : 0.85 - 0.45 * smooth(T_HIT, T_HIT + 0.25, lt) - 0.4 * smooth(1.7, 2.2, lt);
      lift = smooth(T_HIT + 0.1, T_HIT + 0.45, lt) * (1 - smooth(1.6, 2.1, lt));      // the hurt leg comes up off the floor
      shake = lt > T_HIT ? Math.exp(-(lt - T_HIT) * 7) : 0;
      const ow = smooth(T_HIT, T_HIT + 0.15, lt) * (1 - 0.6 * smooth(1.8, 2.6, lt));
      pose = addPose(STAND1, { neck: [-16 * (1 - ow) - 26 * ow, 0, 0], head: [-10 * (1 - ow) - 8 * ow, 0, 0], spine1: [10 * ow, 0, 0], spine2: [8 * ow, 0, 0] });
      Object.assign(face, { look: [0, -0.6 + 0.2 * ow], squint: 0.9 * ow, brow: ow, jaw: 0.35 * ow, fear: 0.5 * ow });
      bA[0] = smooth(2.2, 3.3, lt); bK[0] = 2; root.y = 0.95 - 0.02 * lift; root.z = STANDP.z + 0.05 * step;
    }
  } else if (b === 1 || b === 2 || b === 5) {                        // up close in the skin
    show = false; macro = true; phoneOn = false;
    if (b === 1) { hit = lt; burst = lt > 0.36; leak = smooth(0.36, d - 0.2, lt); poolK = 0; }
    if (b === 2) { hit = 99; burst = true; leak = 1; poolK = 2 * smooth(0.6, d - 0.3, lt); topK = smooth(0.0, 0.6, lt); }
    if (b === 5) { thin = smooth(0.2, 1.8, lt); hit = lt - 1.75; burst = lt > 2.11; leak = smooth(2.11, d, lt); poolK = 0; }
  } else if (b === 3) {                                             // days go by on his shin: green, yellow, gone
    phoneOn = false; bA[0] = 1 - smooth(0.62 * d, d - 0.25, lt); bK[0] = 3 + smooth(0.15 * d, 0.55 * d, lt);
    pose = addPose(STAND1, { neck: [-10, 0, 0] });
  } else if (b === 4) {                                             // why do some people bruise so easily? he looks down at bruises all over his legs
    phoneOn = false; bA = [1, 0.9, 0.85, 0.9, 0.8]; bK = [2, 3.4, 1, 4, 2.3];
    const k = smooth(0.1, 0.8, lt); pose = addPose(STAND1, { neck: [-24 * k, 6 * k, 0], head: [-14 * k, 0, 6 * k], spine1: [6 * k, 0, 0] });
    Object.assign(face, { look: [0, -0.7 * k], brow: 0.8 * k, oh: 0.25 * k });
  } else if (b === 6) {                                             // aspirin and blood thinners (pills on the table); big bruises for no reason: see a doctor
    phoneOn = false; pills = lt < 2.2; cut = lt >= 2.2 && lt - 2.2 < 1 / 30 + 1e-6;
    if (!pills) { bA = [1, 1, 0.9, 1, 0.9]; bK = [2, 1.2, 2.4, 1.6, 2]; bR = 1.7; }
    pose = addPose(STAND1, { neck: [-8, 0, 0] }); Object.assign(face, { brow: 0.5 });
  }
  const wb = 2 * Math.PI * Math.round(TOTAL / 2.6) / TOTAL;           // breathing (whole cycles over the loop)
  pose = addPose(pose, { spine1: [0.9 * Math.sin(wb * t), 0, 0], spine2: [0.6 * Math.sin(wb * t + 0.4), 0, 0], neck: [0.7 * Math.sin(wb * t + 1.1), 0, 0] });
  return { b, lt, d, pose, root, hands, show, cut, step, lift, bA, bK, bR, macro, hit, burst, leak, poolK, thin, topK, pills, shake, phoneOn, face };
}

// ------------------------------------------------------------------ cameras (his left side is +x: the camera stays there, the kitchen wall behind him)
function shakeV(t, a) { return V(vn1(t * 14, 1) * a * 0.5, vn1(t * 14, 2) * a, vn1(t * 14, 3) * a); }
const CAM7 = { pos: STANDP.clone().add(V(1.75, 1.45, 1.55)), tgt: STANDP.clone().add(V(0.05, 0.92, 0.3)), fov: 50 };
function camAt(t, g) {
  const b = g.b, lt = g.lt, d = g.d, k = smooth(0, d, lt);
  if (b === 7) return { pos: CAM7.pos.clone().add(V(0.08 * (1 - k), 0.05 * (1 - k), 0.08 * (1 - k))), tgt: CAM7.tgt, fov: CAM7.fov };
  if (b === 0) { const a = sm(Math.min(1, lt / 0.4)), z = smooth(2.0, 3.0, lt), bw = bruiseW();
    const p1 = STANDP.clone().add(V(1.35, 0.72, 0.3)), t1 = STANDP.clone().add(V(0.1, 0.55, 0.22));
    const p2 = bw.clone().add(V(0.32, 0.1, 0.3)), t2 = bw.clone();
    return { pos: CAM7.pos.clone().lerp(p1, a).lerp(p2, z).add(shakeV(t, 0.025 * g.shake)), tgt: CAM7.tgt.clone().lerp(t1, a).lerp(t2, z), fov: CAM7.fov - 4 * a - 6 * z }; }
  if (b === 3) { const bw = bruiseW(); return { pos: bw.clone().add(V(0.3 - 0.04 * k, 0.12, 0.28 - 0.04 * k)), tgt: bw, fov: 40 }; }
  if (b === 4) return { pos: STANDP.clone().add(V(1.3, 1.35, 1.65 - 0.1 * k)), tgt: STANDP.clone().add(V(0.0, 0.88, 0.2)), fov: 50 };
  if (b === 6) { if (g.pills) return { pos: ctable.localToWorld(V(0.4, TOPY + 0.24, 0.66 + 0.03 * lt)), tgt: ctable.localToWorld(V(0.09, TOPY + 0.025, 0.22)), fov: 38 };
    return { pos: STANDP.clone().add(V(0.85, 0.65, 1.2)), tgt: STANDP.clone().add(V(0.0, 0.38, 0.1)), fov: 46 }; }
  // up close in the skin
  if (b === 1) return { pos: MS.clone().add(V(0.1, SKTOP - 0.05, 1.35 - 0.1 * k)).add(shakeV(t, 0.02 * (g.hit > 0.35 ? Math.exp(-(g.hit - 0.35) * 6) : 0))), tgt: MS.clone().add(V(0, SKTOP - 0.2, 0)), fov: 44 };
  if (b === 2) { const u = smooth(0, 1.4, lt); return { pos: MS.clone().add(V(0.1, SKTOP - 0.05 + 0.75 * u, 1.25 - 0.15 * u)), tgt: MS.clone().add(V(0, SKTOP - 0.2 + 0.08 * u, 0)), fov: 44 }; }
  if (b === 5) return { pos: MS.clone().add(V(-0.1, SKTOP - 0.1, 1.35 - 0.1 * k)), tgt: MS.clone().add(V(0, SKTOP - 0.25, 0)), fov: 44 };
  return CAM7;
}
