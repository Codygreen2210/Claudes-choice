
// ------------------------------------------------------------------ the story
const T_GRAB = 1.0;                                                // beat 7: reaches for the 6th can, holds it up in front of him (it gets cracked open at the loop)
const T_UP = 0.55, T_SIP = 1.5;                                    // beat 0: the fizz settles, the can goes up, he drinks
const T_DROP = 2.5;                                                // beat 6: his weak hand lets the can go
const LOOPSEED = { R: null, L: null };
function blinkAt(s) { const u = ((s + 40) % 3.7) / 0.16; return u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0; }
const F = fwdOf(90), Rt = rightOf(90), UP = V(0, 1, 0);           // his forward (-x), his right (-z), up
const STAND1 = { ...addPose(STAND, { spine1: [-4, 0, 0], neck: [6, 0, 0] }), armL: A(10, 14, 0, 22) };   // hands a little off the hips (a reach from there doesn't brush them)
// a can in his hand: palm on its side (left hand: palm to his right, so his knuckles face the camera), fingers around it; c = can bottom, axis = bottom -> top
const GRIP = 0.012;
function canHand(c, axis, S = 'L') { const s = S === 'R' ? 1 : -1;
  const n = Rt.clone().multiplyScalar(-s).addScaledVector(F, 0.25); n.addScaledVector(axis, -n.dot(axis)).normalize();
  const u = new THREE.Vector3().crossVectors(axis, n).multiplyScalar(-s).normalize();
  return { S, p: c.clone().addScaledVector(axis, CANH * 0.45).addScaledVector(n, -(CANR + GRIP)), n, u, c: 50, th: 42, opp: 40, memAbs: 'can' + S, seed: A(40, 15, 0, 80, 10) }; }
const tipAxis = th => UP.clone().multiplyScalar(Math.cos(th * D2R)).addScaledVector(F, -Math.sin(th * D2R));
function canAtMouth(th) { const ax = tipAxis(th), rim = RG.mouthW().addScaledVector(F, 0.016).add(V(0, 0.004, 0)).addScaledVector(Rt, 0.012); return { c: rim.clone().addScaledVector(ax, -CANH), ax }; }
const SHOW = V(-2.28, 1.2, -0.42);                                  // the can held up in front of his chest (bottom)
function counterHand(S, dz = 0) { const s = S === 'R' ? 1 : -1;
  return { S, p: V(-2.43, TOPC + 0.03, STANDP.z + s * -0.2 + dz), n: V(0, -1, 0), u: F.clone().addScaledVector(Rt, 0.25 * s).normalize(), c: 20, th: 20, memAbs: 'rest' + S, seed: A(35, 10, 0, 40, -60) }; }

// the state at a time ----------------------------------------------
function guyAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  const face = { blink: blinkAt(lt + b * 1.3) };
  let pose = STAND1, root = { x: STANDP.x, y: 0.95, z: STANDP.z, yaw: 90 }, hands = [], show = true, cut = false;
  let canMode = 'counter', canC = CAN0.clone(), canAx = UP.clone(), xr = 0, fizzK = 0, spoons = 0, limit = 0, sugar = 0, insulin = 0, fat = 0, toothT = -1, fall = -1, weak = 0;
  if (b === 7) {                                                    // he grabs the next can and holds it up
    const reach = smooth(0.0, T_GRAB, lt), lift = smooth(T_GRAB + 0.05, d - 0.35, lt);
    if (lt < T_GRAB) { canMode = 'counter'; const h = canHand(CAN0.clone(), UP.clone()); h.p.y += 0.14 * (1 - reach) ** 2; hands = [{ ...h, blend: reach, local: lt > 0.1 }]; }   // over the counter's edge, then down to the can   // local: the target arm can't flip to another shape mid-reach
    else { canMode = 'hand'; canC = CAN0.clone().lerp(SHOW, sm(lift)); canC.y += 0.08 * Math.sin(Math.PI * lift); hands = [canHand(canC, canAx)]; }
    const lean = Math.sin(Math.PI * smooth(0, T_GRAB + 0.6, lt)); pose = addPose(STAND1, { neck: [-10 + 4 * lift, 4, 0], head: [-6, 0, 0], spine1: [6 * lean, 0, 0], spine2: [4 * lean, 0, 0] }); Object.assign(face, { look: [0.1, -0.4] });
  } else if (b === 0) {                                             // it's just been cracked: fizz sprays out; up it goes, he drinks
    fizzK = 1 - smooth(0.25, 0.75, lt); canMode = 'hand';
    const up = smooth(T_UP, T_SIP, lt), tip = smooth(T_UP + 0.2, T_SIP + 0.3, lt), head = smooth(T_UP + 0.4, T_SIP + 0.2, lt);
    const m = canAtMouth(100 * tip + 20 * smooth(T_SIP, d, lt));
    canAx = UP.clone().lerp(m.ax, tip).normalize(); canC = SHOW.clone().lerp(m.c, sm(up));
    hands = [{ ...canHand(canC, canAx), ...(LOOPSEED.L ? { seed: LOOPSEED.L, seedIsPrev: true } : {}) }];
    pose = addPose(STAND1, { neck: [-6 * (1 - head) + 14 * head, 4 * (1 - head), 0], head: [-6 * (1 - head) + 12 * head, 0, 0], spine1: [-3 * head, 0, 0] });
    Object.assign(face, { look: [0.1, -0.4 * (1 - head)], brow: 0.3 * (1 - head), oh: 0.3 * fizzK });
  } else if (b === 1 || b === 2) {                                  // ten sugar cubes, one can's worth; then the daily max line
    show = false; spoons = b === 1 ? clamp((lt - 0.15) / 1.9, 0, 1) : 1; limit = b === 2 ? smooth(0.1, 0.5, lt) : 0;
  } else if (b === 3) {                                             // x-ray: blood sugar shoots up; the pancreas pumps out insulin; the sugar drops back
    xr = 1; sugar = smooth(0.1, 1.4, lt) * (1 - 0.75 * smooth(2.4, d, lt)); insulin = smooth(1.6, 2.2, lt);
    pose = addPose(STAND1, { neck: [-4, 0, 0] });
  } else if (b === 4) {                                             // the tooth up close
    show = false; toothT = lt;
  } else if (b === 5) {                                             // x-ray: the extra sugar is stored as fat (the liver turns yellow and swells)
    xr = 1; sugar = 0.6 * (1 - smooth(0.4, 2.2, lt)); fat = smooth(0.6, d - 0.6, lt);
    pose = addPose(STAND1, { neck: [-4, 0, 0] });
  } else if (b === 6) {                                             // rare: so little potassium his muscles go weak; the can slips; he braces on the counter
    weak = smooth(0.3, d, lt); const sag = smooth(0.3, T_DROP, lt);
    if (lt < T_DROP) { canMode = 'hand'; canC = SHOW.clone().add(V(0, -0.2 * sag, 0.04 * sag)); canAx = UP.clone().lerp(F.clone().multiplyScalar(-1), 0.25 * sag).normalize(); hands.push(canHand(canC, canAx)); }
    else { fall = lt - T_DROP; canMode = 'fall'; hands.push({ ...canHand(SHOW.clone().add(V(0, -0.2, 0.04)), UP.clone().lerp(F.clone().multiplyScalar(-1), 0.25).normalize()), c: 20, th: 20, blend: 1 - smooth(T_DROP, T_DROP + 0.6, lt) }); }
    hands.push(counterHand('R'));                                    // braced on the counter from the start of the shot
    pose = addPose(STAND1, { spine1: [8 * weak, 0, 0], spine2: [5 * weak, 0, 0], neck: [-10 * weak, -6 * weak, 0], head: [-6 * weak, 0, 0] });
    root = { x: STANDP.x, y: 0.95 - 0.04 * weak, z: STANDP.z, yaw: 90 };
    Object.assign(face, { squint: 0.4 * weak, brow: 0.6 * weak, jaw: 0.15 * weak, look: [0, -0.5] });
  }
  const wb = 2 * Math.PI * Math.round(TOTAL / 2.6) / TOTAL;           // breathing (whole cycles over the loop)
  pose = addPose(pose, { spine1: [0.9 * Math.sin(wb * t), 0, 0], spine2: [0.6 * Math.sin(wb * t + 0.4), 0, 0], neck: [0.7 * Math.sin(wb * t + 1.1), 0, 0] });
  return { b, lt, d, pose, root, hands, show, cut, canMode, canC, canAx, xr, fizzK, spoons, limit, sugar, insulin, fat, toothT, fall, weak, face };
}

// ------------------------------------------------------------------ cameras
function shakeV(t, a) { return V(vn1(t * 14, 1) * a * 0.5, vn1(t * 14, 2) * a, vn1(t * 14, 3) * a); }
const CAM7 = { pos: V(-2.8, 1.6, 0.5), tgt: V(-2.15, 1.3, -0.55), fov: 44 };     // at his front-left: his face, the can, the counter
function camAt(t, g) {
  const b = g.b, lt = g.lt, d = g.d, k = smooth(0, d, lt);
  if (b === 7) return { pos: CAM7.pos.clone().add(V(0.05 * (1 - k), 0.0, 0.1 * (1 - k))), tgt: CAM7.tgt, fov: CAM7.fov };
  if (b === 0) return { pos: CAM7.pos.clone().lerp(V(-2.72, 1.55, 0.28), k), tgt: CAM7.tgt.clone().lerp(V(-2.1, 1.38, -0.6), k), fov: 44 - 2 * k };
  if (b === 1) return { pos: V(-2.04, 1.17 + 0.02 * k, 0.26 - 0.05 * k), tgt: V(-2.47, 1.04 + 0.02 * k, -0.21), fov: 36 };
  if (b === 2) return { pos: V(-2.06, 1.2, 0.22 + 0.06 * k), tgt: V(-2.47, 1.07, -0.21), fov: 36 };
  if (b === 3) return { pos: V(-2.7, 1.28, 0.32 - 0.06 * k), tgt: V(-2.05, 1.13, -0.62), fov: 42 };
  if (b === 4) return { pos: TOOTH.clone().add(V(0.05 - 0.1 * k, 0.62 - 0.05 * k, 1.05 - 0.12 * k)), tgt: TOOTH.clone().add(V(0, 0.2, 0)), fov: 44 };
  if (b === 5) return { pos: V(-2.68, 1.2, 0.28 - 0.06 * k), tgt: V(-2.05, 1.08, -0.62), fov: 40 };
  if (b === 6) return { pos: V(-2.28, 1.3, 1.4), tgt: V(-2.15, 0.88, -0.5), fov: 54 };
  return CAM7;
}
