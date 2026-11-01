
// ------------------------------------------------------------------ the story
const YAW = -90;                                                    // he faces +x (the TV)
const F = fwdOf(YAW), Rt = rightOf(YAW), UP = V(0, 1, 0);
const LOOPSEED = { R: null }, SEED9 = { R: null };
const bez = (a, b, c, k) => a.clone().multiplyScalar((1 - k) * (1 - k)).addScaledVector(b, 2 * k * (1 - k)).addScaledVector(c, k * k);
function blinkAt(s) { const u = ((s + 40) % 3.7) / 0.16; return u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0; }
const STAND1 = { ...addPose(STAND, { spine1: [-3, 0, 0], neck: [4, 0, 0] }), armL: A(8, 12, 0, 20), armR: A(8, 12, 0, 20) };
// the grip (right hand, phone upright, screen to his face): fingers flat up its back, the bottom in his palm, thumb round the near edge.
// c/th/opp/n/u are set at load by a search against his real hand skin (the thumb went through the phone on the last phone Short)
const PH = { rot: 90, n: 0.014, u: 0.05, w: 0.0, c: 10, th: 20, opp: 20 };
const ARMPH = A(45, 25, 0, 125, 60);
function phoneHand(tilt = 0) { const hd = wp(G.bones.head);
  const n0 = F.clone().multiplyScalar(-0.96).addScaledVector(UP, 0.28).normalize(), u0 = UP.clone().addScaledVector(n0, -UP.dot(n0)).normalize();
  const u = u0.clone().applyQuaternion(qAA(n0, tilt));
  return { S: 'R', p: hd.clone().addScaledVector(F, 0.31).addScaledVector(Rt, 0.07).add(V(0, -0.23, 0)), n: n0, u, c: PH.c, th: PH.th, opp: PH.opp, memAbs: 'phoneR', seed: ARMPH }; }
// a step: the foot lifts a little on the way (k 0..1)
const stepK = (lt, a, b) => smooth(a, b, lt);
const lift = (lt, a, b) => { const u = clamp((lt - a) / (b - a), 0, 1); return 0.045 * Math.sin(Math.PI * u); };
const BACK = 0.28;
function tvOnAt(s) { return (s * 3.4) % 1 < 0.5 ? 1 : 0; }           // beat 6, slow motion: the screen blinks on and off

// the state at a time ----------------------------------------------
function guyAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  const face = { blink: blinkAt(lt + b * 1.3), brow: 0.45, squint: 0.15, look: [0.05, -0.05] };
  let pose = STAND1, hands = [], show = true, cut = false, set = 'room';
  let wave = 1, bars = 0, tilt = 0, offR = 0, offL = 0, liftR = 0, liftL = 0, macro = 0, tvOn = 1, slowmo = 0;
  let reveal = 0, rays = 0, scan = -1, gslide = 0, gth = 0, gbayer = 0, tagB = 0, tagD = 0;
  if (b === 0) {                                                    // he films the TV: the phone screen crawls with rainbow waves
  } else if (b === 1) {                                             // into the TV: a grid of tiny glowing dots
    macro = 1; show = false;
  } else if (b === 2) {                                             // the camera's grid of squares that catch light
    show = false; set = 'sensor'; reveal = smooth(0.3, 2.0, lt); rays = 1;
  } else if (b === 3) {                                             // two grids, one a bit off: they drift in and out of line
    show = false; set = 'grid'; gslide = smooth(0.1, 1.0, lt); gth = 8 * smooth(1.0, 2.6, lt);
  } else if (b === 4) {                                             // lined up = bright, off = dark
    show = false; set = 'grid'; gslide = 1; gth = 8 + 0.3 * Math.sin(lt * 1.3); tagB = smooth(0.15, 0.45, lt); tagD = smooth(0.7, 1.0, lt);
  } else if (b === 5) {                                             // each square sees one color: the stripes turn rainbow
    show = false; set = 'grid'; gslide = 1; gth = 8 + 2.0 * smooth(0.3, d, lt) + 0.3 * Math.sin(1.3 * (lt + DUR[4])); gbayer = smooth(0.2, 1.1, lt);
  } else if (b === 6) {                                             // dark bars: the screen flashes on and off (slow motion)
    bars = smooth(0.1, 0.8, lt); wave = 1 - 0.6 * smooth(0.1, 0.8, lt); if (lt >= 1.6) { cut = lt - 1.6 < 1 / 30; slowmo = 1; tvOn = tvOnAt(lt - 1.6); }
    Object.assign(face, { brow: 0.7, squint: 0.1 });
  } else if (b === 7) {                                             // the camera reads one row at a time
    show = false; set = 'sensor'; reveal = 1; scan = lt;
  } else if (b === 8) {                                             // tilt the phone, step back: the waves fade
    bars = 0.35; tilt = 12 * smooth(0.1, 0.7, lt); wave = 1 - smooth(0.5, 2.0, lt);
    offR = BACK * stepK(lt, 0.7, 1.15); liftR = lift(lt, 0.7, 1.15); offL = BACK * stepK(lt, 1.05, 1.5); liftL = lift(lt, 1.05, 1.5);
    Object.assign(face, { brow: 0.45 - 0.3 * smooth(1.2, 2.0, lt), smile: 0.45 * smooth(1.2, 2.0, lt) });
  } else if (b === 9) {                                             // the title; he steps back in and the waves come back (loops into beat 0)
    bars = 0.35 * (1 - smooth(1.4, 3.4, lt)); tilt = 12 * (1 - smooth(1.0, 1.8, lt)); wave = smooth(2.4, 4.6, lt);
    offL = BACK * (1 - stepK(lt, 1.5, 1.95)); liftL = lift(lt, 1.5, 1.95); offR = BACK * (1 - stepK(lt, 1.9, 2.35)); liftR = lift(lt, 1.9, 2.35);
    cut = lt >= 1.4 && lt - 1.4 < 1 / 30; const sm9 = 1 - smooth(2.6, 4.2, lt); Object.assign(face, { brow: 0.45 - 0.3 * sm9, smile: 0.5 * sm9 });
  }
  const back = 0.5 * (offR + offL), root = { x: STANDP.x - F.x * back, y: 0.95 - 0.006 * (liftR + liftL) / 0.045, z: STANDP.z - F.z * back, yaw: YAW };
  if (show) hands = [phoneHand(tilt)];
  if (show && b === 0 && LOOPSEED.R && lt < 0.5 / 30) hands = [{ ...hands[0], seed: LOOPSEED.R, seedIsPrev: true }];
  if (show && b === 9 && SEED9.R && lt < 0.5 / 30) hands = [{ ...hands[0], seed: SEED9.R, seedIsPrev: true }];
  const wb = 2 * Math.PI * Math.round(TOTAL / 2.6) / TOTAL;           // breathing (whole cycles over the loop)
  pose = addPose(pose, { spine1: [0.9 * Math.sin(wb * t), 0, 0], spine2: [0.6 * Math.sin(wb * t + 0.4), 0, 0], neck: [0.7 * Math.sin(wb * t + 1.1), 0, 0] });
  return { b, lt, d, pose, root, hands, show, cut, face, set, wave, bars, tilt, offR, offL, liftR, liftL, macro, tvOn, slowmo, reveal, rays, scan, gslide, gth, gbayer, tagB, tagD };
}

// ------------------------------------------------------------------ cameras
const OTS0 = { pos: V(0.8, 1.8, 0.36), tgt: V(1.75, 1.36, 0.0), fov: 40 };   // over his right shoulder: the phone screen and the real TV behind it
const OTS1 = { pos: V(0.86, 1.77, 0.32), tgt: V(1.72, 1.36, 0.0), fov: 38 };
const backV = g => F.clone().multiplyScalar(-0.5 * (g.offR + g.offL));
function camAt(t, g) {
  const b = g.b, lt = g.lt, d = g.d, k = smooth(0, d, lt);
  if (b === 0) return { pos: OTS0.pos.clone().lerp(OTS1.pos, sm(k)), tgt: OTS0.tgt.clone().lerp(OTS1.tgt, sm(k)), fov: lerp(OTS0.fov, OTS1.fov, sm(k)), focus: 'phone' };
  if (b === 1) { const P1 = V(TVP.x - 0.012, 1.262, 0.035), P0 = V(1.75, 1.36, 0.12), u = smooth(0.0, d - 0.15, lt), dd = 1.46 * Math.pow(0.0065 / 1.46, u);
    const dir = P1.clone().sub(P0).normalize(); return { pos: P1.clone().addScaledVector(dir, -dd), tgt: P1.clone().addScaledVector(dir, 0.2), fov: 40, near: Math.max(0.002, Math.min(0.03, dd * 0.25)), focus: P1 }; }
  if (b === 2) return { pos: SS.clone().add(V(0.42 - 0.2 * k, 1.5 - 0.08 * k, 1.25 - 0.25 * k)), tgt: SS.clone().add(V(0, 1.2, 0)), fov: 40 };
  if (b === 3 || b === 4 || b === 5) { const kk = b === 3 ? 0.15 * k : b === 4 ? 0.15 + 0.1 * k : 0.25 + 0.75 * k;
    return { pos: GS.clone().add(V(0.06 - 0.04 * kk, 1.2, 3.0 + 0.6 * kk)), tgt: GS.clone().add(V(0.06 - 0.04 * kk, 1.2, 0)), fov: 40 }; }
  if (b === 6) { if (lt < 1.6) { const u = smooth(0, 1.6, lt); return { pos: OTS1.pos.clone().lerp(V(1.12, 1.6, 0.23), u), tgt: OTS1.tgt.clone().lerp(V(1.6, 1.42, 0.06), u), fov: 36, focus: 'phone' }; }
    const u = smooth(1.6, d, lt); return { pos: V(0.42 + 0.08 * u, 1.78, -0.62 + 0.05 * u), tgt: V(2.55, 1.32, 0.08), fov: 42 }; }
  if (b === 7) return { pos: SS.clone().add(V(0.1 - 0.1 * k, 1.6, 2.5 - 0.12 * k)), tgt: SS.clone().add(V(0, 1.6, 0)), fov: 42 };
  if (b === 8) { const bv = backV(g); return { pos: OTS1.pos.clone().add(bv).add(V(-0.12 * k, 0.02 * k, 0.06 * k)), tgt: OTS1.tgt.clone().add(bv.multiplyScalar(0.5)), fov: 40, focus: 'phone' }; }
  if (b === 9) { if (lt < 1.4) { const u = smooth(0, 1.4, lt); return { pos: V(2.5, 1.62, 0.32 - 0.06 * u), tgt: V(1.15, 1.52, 0.02), fov: 34 + 2 * u }; }
    const u = smooth(1.4, d, lt), bv = backV(g), s = OTS1.pos.clone().add(V(-0.12, 0.02, 0.06)).add(bv);
    return { pos: s.lerp(OTS0.pos, u), tgt: OTS1.tgt.clone().add(bv.multiplyScalar(0.5)).lerp(OTS0.tgt, u), fov: lerp(40, OTS0.fov, u), focus: 'phone' }; }
  return OTS0;
}
