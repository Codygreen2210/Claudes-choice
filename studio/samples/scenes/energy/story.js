
// ------------------------------------------------------------------ the story
const T_GRAB = 0.7, T_LIFT = 1.1, T_SIP = 2.45;                    // beat 7: reaches for the 4th can, lifts it, starts to drink (loops into beat 0)
const T_DOWN = 1.25, T_SET = 2.2, T_XR = 1.85;                     // beat 0: lowers the can, sets it down; the x-ray comes on
const T_SHAKE = 1.75;                                              // beat 4: cut from the racing heart to his shaking hand
const LOOPSEED = { R: null, L: null };
function blinkAt(s) { const u = ((s + 40) % 3.7) / 0.16; return u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0; }
const F = fwdOf(90), Rt = rightOf(90), UP = V(0, 1, 0);           // his forward (-x), his right (-z), up
const STAND1 = addPose(STAND, { spine1: [-4, 0, 0], neck: [6, 0, 0] });
// a can in his hand: palm on its side (left hand: palm to his right, so his knuckles face the camera), fingers around it; c = can bottom, axis = bottom -> top
const GRIP = 0.012;
function canHand(c, axis, S = 'L') { const s = S === 'R' ? 1 : -1;
  const n = Rt.clone().multiplyScalar(-s).addScaledVector(F, 0.25); n.addScaledVector(axis, -n.dot(axis)).normalize();
  const u = new THREE.Vector3().crossVectors(axis, n).multiplyScalar(-s).normalize();
  return { S, p: c.clone().addScaledVector(axis, CANH * 0.42).addScaledVector(n, -(CANR + GRIP)), n, u, c: 50, th: 42, opp: 40, memAbs: 'can' + S, seed: A(40, 15, 0, 80, 10) }; }
// the can's axis tipped back toward his face by th degrees (0 = upright)
const tipAxis = th => UP.clone().multiplyScalar(Math.cos(th * D2R)).addScaledVector(F, -Math.sin(th * D2R));
// the can at his mouth: the rim on his lips
function canAtMouth(th) { const ax = tipAxis(th), rim = RG.mouthW().addScaledVector(F, 0.016).add(V(0, 0.004, 0)).addScaledVector(Rt, 0.012); return { c: rim.clone().addScaledVector(ax, -CANH), ax }; }
// hands flat on the counter edge (bracing)
function counterHand(S, dz = 0) { const s = S === 'R' ? 1 : -1;
  return { S, p: V(-2.43, TOPC + 0.03, STANDP.z + s * -0.2 + dz), n: V(0, -1, 0), u: F.clone().addScaledVector(Rt, 0.25 * s).normalize(), c: 20, th: 20, memAbs: 'rest' + S, seed: A(35, 10, 0, 40, -60) }; }
function pulse(t, bpm) { const ph = (t * bpm / 60) % 1; return Math.exp(-(((ph - 0.05) / 0.06) ** 2)) + 0.55 * Math.exp(-(((ph - 0.28) / 0.06) ** 2)); }

// the state at a time ----------------------------------------------
function guyAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  const face = { blink: blinkAt(lt + b * 1.3) };
  let pose = STAND1, root = { x: STANDP.x, y: 0.95, z: STANDP.z, yaw: 90 }, hands = [], show = true, cut = false;
  let canMode = 'counter', canC = CAN0.clone(), canAx = UP.clone(), xr = 0, bpm = 80, beatK = 0.08, mg = 0, dim = 0, clockT = 0, bolt = 0, cell = false, tremor = 0, wide = false;
  if (b === 7) {                                                    // he grabs the 4th can and starts to drink
    const reach = smooth(T_GRAB - 0.68, T_GRAB, lt), lift = smooth(T_GRAB + 0.05, T_SIP, lt), tip = smooth(T_LIFT, T_SIP + 0.25, lt);
    const head = smooth(T_LIFT + 0.4, d, lt);
    pose = addPose(STAND1, { neck: [-10 * (1 - head) + 14 * head, 0, 0], head: [-6 * (1 - head) + 12 * head, 0, 0], spine1: [-3 * head, 0, 0] });
    if (lt > T_GRAB - 0.68) { canMode = lt > T_GRAB ? 'hand' : 'counter';
      const m = canAtMouth(100 * tip), up = CAN0.clone().add(V(0.12, 0.25, 0.05));
      canAx = UP.clone().lerp(m.ax, tip).normalize(); canC = lift < 0.5 ? CAN0.clone().lerp(up, lift * 2) : up.lerp(m.c, sm((lift - 0.5) * 2));
      hands = [{ ...canHand(canC, canAx), blend: reach }]; }
    Object.assign(face, { look: [0.1, -0.3 * (1 - head)] });
  } else if (b === 0) {                                             // chugging; down it goes; heart pounding (x-ray)
    const head = 1 - smooth(T_DOWN, T_DOWN + 0.5, lt), down = smooth(T_DOWN, T_SET, lt), off = smooth(T_SET, T_SET + 0.75, lt);
    pose = addPose(STAND1, { neck: [14 * head - 4 * (1 - head), 0, 0], head: [12 * head, 0, 0], spine1: [-3 * head, 0, 0] });
    const m = canAtMouth(100 + 30 * smooth(0, T_DOWN, lt)), set = CAN0.clone();
    canAx = m.ax.clone().lerp(UP, down).normalize(); canC = m.c.clone().lerp(set, sm(down)); canMode = off > 0.5 ? 'counter' : 'hand'; if (off > 0.5) { canC = set; canAx = UP.clone(); }
    hands = [{ ...canHand(canC, canAx), ...(LOOPSEED.L ? { seed: LOOPSEED.L, seedIsPrev: true } : {}), blend: 1 - off }];
    xr = smooth(T_XR, T_XR + 0.25, lt); bpm = 150; beatK = 0.16;
    Object.assign(face, { look: [0.1, 0], brow: 0.4 * off, oh: 0.3 * off, fear: 0.3 * off });
  } else if (b === 1) {                                             // the can up close: up to 300 mg
    show = true;
  } else if (b === 2) {                                             // the tube fills can by can: past the 400 mg limit, to 1,200
    mg = 300 * (smooth(0.35, 0.75, lt) + smooth(1.05, 1.45, lt) + smooth(1.75, 2.15, lt) + smooth(2.45, 2.85, lt));
    Object.assign(face, { look: [0.3, -0.2] });
  } else if (b === 3) {                                             // inside the brain
    show = false; cell = true;
  } else if (b === 4) {                                             // racing heart (x-ray), then his shaking hand
    const shake = lt >= T_SHAKE; cut = lt >= T_SHAKE && lt - T_SHAKE < 1 / 30 + 1e-6;
    xr = shake ? 0 : 1; bpm = 175; beatK = 0.2; tremor = shake ? 1 : 0.4;
    canMode = 'hand'; canAx = UP.clone(); canC = V(-2.3, 1.08, STANDP.z + 0.16);
    const tr = V(vn1(t * 9, 1), vn1(t * 9, 2), vn1(t * 9, 3)).multiplyScalar(0.006 * tremor); canC.add(tr);
    hands = [canHand(canC, canAx)]; pose = addPose(STAND1, { neck: [-12, 0, 0], head: [-8, 0, 0] });
    Object.assign(face, { look: [0.0, -0.5], brow: 0.6, fear: 0.4, jaw: 0.1 });
  } else if (b === 5) {                                             // too much, too fast: an electric storm in his brain; he braces on the counter
    xr = 1; bpm = 180; beatK = 0.2; bolt = smooth(0.3, 0.8, lt); mg = 1200;
    const k = smooth(0, 0.5, lt);
    pose = addPose(STAND1, { spine1: [10 * k, 0, 0], spine2: [6 * k, 0, 0], neck: [-14 * k, 6 * Math.sin(lt * 3), 0], head: [-6 * k, 0, 0] });
    hands = [counterHand('R'), counterHand('L')].map(h => ({ ...h, blend: smooth(0, 1.15, lt) }));
    Object.assign(face, { squint: 0.7, brow: 0.8, fear: 0.6, jaw: 0.2 });
  } else if (b === 6) {                                             // five hours go by: the clock spins, the light goes orange, the tube drains to half
    wide = true; const k = smooth(0.2, d - 0.3, lt); clockT = k; dim = k; mg = 1200 - 600 * k;
    hands = [counterHand('R'), counterHand('L')].map(h => ({ ...h, blend: 1 }));
    pose = addPose(STAND1, { spine1: [6, 0, 0], neck: [-6, 0, 0] }); Object.assign(face, { look: [0.0, 0.1], brow: 0.3 + 0.3 * k, squint: 0.3 * k, blink: 0 });
  }
  const wb = 2 * Math.PI * Math.round(TOTAL / 2.6) / TOTAL;           // breathing (whole cycles over the loop)
  pose = addPose(pose, { spine1: [0.9 * Math.sin(wb * t), 0, 0], spine2: [0.6 * Math.sin(wb * t + 0.4), 0, 0], neck: [0.7 * Math.sin(wb * t + 1.1), 0, 0] });
  return { b, lt, d, pose, root, hands, show, cut, canMode, canC, canAx, xr, bpm, beatK, mg, dim, clockT, bolt, cell, tremor, wide, face };
}

// ------------------------------------------------------------------ cameras
function shakeV(t, a) { return V(vn1(t * 14, 1) * a * 0.5, vn1(t * 14, 2) * a, vn1(t * 14, 3) * a); }
const CAM7 = { pos: V(-2.78, 1.62, 0.42), tgt: V(-2.12, 1.32, -0.6), fov: 44 };     // at his front-left: his face, the can, the counter
function camAt(t, g) {
  const b = g.b, lt = g.lt, d = g.d, k = smooth(0, d, lt);
  if (b === 7) return { pos: CAM7.pos.clone().add(V(0.06 * (1 - k), 0.0, 0.12 * (1 - k))), tgt: CAM7.tgt, fov: CAM7.fov };
  if (b === 0) { const x = smooth(T_XR - 0.1, T_XR + 0.5, lt);
    return { pos: CAM7.pos.clone().lerp(V(-2.7, 1.5, 0.2), x), tgt: CAM7.tgt.clone().lerp(V(-2.05, 1.3, -0.6), x), fov: 44 - 4 * x }; }
  if (b === 1) { const a = 0.55 - 0.35 * k, r = 0.42 - 0.05 * k; return { pos: CAN0.clone().add(V(Math.sin(a) * r, 0.11, Math.cos(a) * r)), tgt: CAN0.clone().add(V(0, 0.085, 0)), fov: 34 }; }
  if (b === 2) return { pos: TUBE.clone().add(V(0.3 - 0.03 * k, 0.37, 0.6 - 0.06 * k)), tgt: TUBE.clone().add(V(0.02, 0.3, 0)), fov: 42 };
  if (b === 3) return { pos: CELL.clone().add(V(0.04 - 0.08 * k, 0.72 - 0.06 * k, 1.0 - 0.1 * k)), tgt: CELL.clone().add(V(0, 0.08, 0)), fov: 45 };
  if (b === 4) { if (lt < T_SHAKE) return { pos: V(-2.62, 1.42, 0.05), tgt: V(-2.05, 1.25, -0.62), fov: 38 };
    return { pos: g.canC.clone().add(V(-0.28, 0.06, 0.34)), tgt: g.canC.clone().add(V(0, 0.07, 0)), fov: 38 }; }
  if (b === 5) return { pos: V(-2.5, 1.68, -0.1).add(shakeV(t, 0.004)), tgt: V(-2.06, 1.58, -0.6), fov: 34 };
  if (b === 6) return { pos: V(-2.88, 1.56, 1.02), tgt: V(-2.3, 1.22, -0.42), fov: 44 };
  return CAM7;
}
