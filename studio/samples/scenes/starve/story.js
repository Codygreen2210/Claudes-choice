
// ------------------------------------------------------------------ the story
const STANDP = V(0.15, 0, 0.3), STREAMP = V(0.1, 0, STREAMZ + 0.75);   // lost in the clearing / at the stream bank (he faces -z)
const YAW = 0;
const LOOPSEED = { R: null, L: null };
function blinkAt(s) { const u = ((s + 40) % 3.7) / 0.16; return u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0; }
const F = fwdOf(YAW), Rt = rightOf(YAW), UP = V(0, 1, 0);
const STAND1 = { ...addPose(STAND, { spine1: [-4, 0, 0], neck: [6, 0, 0] }), armL: A(10, 14, 0, 22), armR: A(10, 14, 0, 22) };
// the bottle in his left hand: palm on its side (palm to his right), fingers around it; c = bottom, axis = bottom -> top
const GRIP = 0.012;
function bottleHand(c, axis) { const n = Rt.clone().addScaledVector(F, 0.25); n.addScaledVector(axis, -n.dot(axis)).normalize();
  const u = new THREE.Vector3().crossVectors(axis, n).normalize();
  return { S: 'L', p: c.clone().addScaledVector(axis, BTH * 0.42).addScaledVector(n, -(BTR + GRIP)), n, u, c: 50, th: 42, opp: 40, memAbs: 'bottleL', seed: A(40, 15, 0, 80, 10) }; }
const tipAxis = th => UP.clone().multiplyScalar(Math.cos(th * D2R)).addScaledVector(F, -Math.sin(th * D2R));
function atMouth(th) { const ax = tipAxis(th), rim = RG.mouthW().addScaledVector(F, 0.014).add(V(0, 0.004, 0)).addScaledVector(Rt, 0.01); return { c: rim.clone().addScaledVector(ax, -BTH), ax }; }
const tipSide = th => UP.clone().multiplyScalar(Math.cos(th * D2R)).addScaledVector(Rt, Math.sin(th * D2R));   // tipped over sideways (shaking it out)

// the state at a time ----------------------------------------------
function guyAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  const face = { blink: blinkAt(lt + b * 1.3) };
  let pose = STAND1, root = { x: STANDP.x, y: 0.95, z: STANDP.z, yaw: YAW }, hands = [], show = true, cut = false;
  let night = 0.15, bc = null, bax = UP.clone(), bfill = 0, dropT = -1, xr = 0, kidK = 0, sugarK = 0, fatK = 0, fuel = 0, muscK = 0, weak = 0, tally = 0, tallyShot = false, stream = false;
  if (b === 7 || b === 0) {                                         // lost: he looks around; then he turns the empty bottle over and shakes it - one drop
    night = 0.45;
    const look = b === 7 ? Math.sin(lt / d * 2 * Math.PI) : 0;      // one look left and right, back to centre at the loop
    if (b === 7) { bc = V(-0.08, 1.05, -0.3).add(STANDP); bax = UP.clone();
      pose = addPose(STAND1, { neck: [-2, 26 * look, 0], head: [0, 12 * look, 0] }); Object.assign(face, { look: [0.4 * look, 0], brow: 0.6, fear: 0.4 }); }
    else { const up = smooth(0.0, 1.0, lt), head = smooth(0.3, 1.0, lt), shake = lt > 1.0 && lt < 2.4 ? Math.sin((lt - 1.0) * 15) * smooth(1.0, 1.2, lt) * (1 - smooth(2.2, 2.4, lt)) : 0;
      const m = atMouth(140 + 4 * shake); m.c.addScaledVector(m.ax, -0.06);                   // upside down over his open mouth, a few cm up: shaking out the last drop
      bax = UP.clone().lerp(m.ax, up).normalize(); bc = V(-0.08, 1.05, -0.3).add(STANDP).lerp(m.c, sm(up)).add(V(0, 0.012 * shake, 0)); dropT = lt - 1.6;
      pose = addPose(STAND1, { neck: [16 * head, 0, 0], head: [14 * head, 0, 0], spine1: [-4 * head, 0, 0] }); Object.assign(face, { look: [0, 0.5 * head], brow: 0.7, fear: 0.4, oh: 0.6 * head, jaw: 0.4 * head }); }
    hands = [b === 0 && LOOPSEED.L ? { ...bottleHand(bc, bax), seed: LOOPSEED.L, seedIsPrev: true } : bottleHand(bc, bax)];
  } else if (b === 1) {                                             // three days: day and night race past; he wilts
    const k = smooth(0, d, lt); night = 0.5 - 0.5 * Math.cos(lt / d * 3 * 2 * Math.PI);   // three nights
    weak = k; bc = V(-0.14, 0.88 - 0.03 * k, -0.14).add(STANDP); hands = [bottleHand(bc, bax)];
    pose = addPose(STAND1, { spine1: [10 * k, 0, 0], spine2: [6 * k, 0, 0], neck: [-10 * k, 0, 0], head: [-6 * k, 0, 0] }); root.y = 0.95 - 0.03 * k;
    Object.assign(face, { squint: 0.4 * k, brow: 0.5 * k, jaw: 0.15 * k, look: [0, -0.3 * k] });
  } else if (b === 2) {                                             // x-ray: the kidneys can't clear the waste; it all dims
    xr = 1; kidK = smooth(0.3, d - 0.5, lt); weak = 1; night = 0.2;
    pose = addPose(STAND1, { spine1: [10, 0, 0], spine2: [6, 0, 0], neck: [-10, 0, 0] });
  } else if (b === 3) {                                             // the stream: he fills the bottle and drinks
    root = { x: STREAMP.x, y: 0.95, z: STREAMP.z, yaw: YAW }; stream = true; night = 0.1; bfill = 0.85;
    const up = smooth(0.1, 0.9, lt), tip = smooth(0.4, 1.2, lt), head = smooth(0.6, 1.2, lt), m = atMouth(105 * tip);
    bax = UP.clone().lerp(m.ax, tip).normalize(); bc = V(-0.08, 1.05, -0.3).add(STREAMP).lerp(m.c, sm(up)); hands = [bottleHand(bc, bax)];
    pose = addPose(STAND1, { neck: [14 * head, 0, 0], head: [12 * head, 0, 0], spine1: [-3 * head, 0, 0] });
  } else if (b === 4) {                                             // x-ray: the sugar in the liver runs out (day 1), then the fat starts to burn
    xr = 1; sugarK = 1 - smooth(0.2, 1.6, lt); fatK = smooth(1.4, d, lt); fuel = smooth(1.3, 1.8, lt);
  } else if (b === 5) {                                             // x-ray: then the muscle; he gets weaker
    xr = 1; fatK = 1; muscK = smooth(0.2, d - 0.3, lt); fuel = 1; weak = muscK;
    pose = addPose(STAND1, { spine1: [8 * weak, 0, 0], spine2: [6 * weak, 0, 0], neck: [-8 * weak, 0, 0] }); root.y = 0.95 - 0.03 * weak;
  } else if (b === 6) {                                             // with water: weeks, up to about two months (a tally on a tree)
    show = false; tallyShot = true; tally = Math.round(60 * smooth(0.2, d - 0.3, lt)); night = 0.15;
  }
  const wb = 2 * Math.PI * Math.round(TOTAL / 2.6) / TOTAL;           // breathing (whole cycles over the loop)
  pose = addPose(pose, { spine1: [0.9 * Math.sin(wb * t), 0, 0], spine2: [0.6 * Math.sin(wb * t + 0.4), 0, 0], neck: [0.7 * Math.sin(wb * t + 1.1), 0, 0] });
  return { b, lt, d, pose, root, hands, show, cut, night, bc, bax, bfill, dropT, xr, kidK, sugarK, fatK, fuel, muscK, weak, tally, tallyShot, stream, face };
}

// ------------------------------------------------------------------ cameras
const CAM7 = { pos: V(-0.75, 1.62, -1.25), tgt: V(0.05, 1.25, 0.3), fov: 46 };      // in front of him, a little to his left (his left hand holds the bottle: knuckles to us): his face, the bottle, dark trees behind
function camAt(t, g) {
  const b = g.b, lt = g.lt, d = g.d, k = smooth(0, d, lt);
  if (b === 7) return { pos: CAM7.pos.clone().add(V(-0.06 * (1 - k), 0, -0.1 * (1 - k))), tgt: CAM7.tgt, fov: CAM7.fov };
  if (b === 0) return { pos: CAM7.pos.clone().lerp(V(-0.25, 1.62, -1.25), sm(Math.min(1, lt / 0.8))), tgt: CAM7.tgt.clone().lerp(V(0.08, 1.48, 0.3), sm(Math.min(1, lt / 0.8))), fov: 46 };
  if (b === 1) return { pos: V(-1.4, 1.9, -2.2).lerp(V(-1.2, 1.6, -1.9), k), tgt: V(0.1, 1.0, 0.3), fov: 48 };
  if (b === 2) return { pos: V(-0.3, 1.3, -0.75), tgt: V(0.15, 1.08, 0.3), fov: 44 };
  if (b === 3) return { pos: V(-0.75, 1.4, STREAMZ - 0.45), tgt: V(0.12, 1.15, STREAMP.z), fov: 48 };
  if (b === 4 || b === 5) return { pos: V(-0.3, 1.25, -0.85 + 0.05 * k), tgt: V(0.15, 1.08, 0.3), fov: 46 };
  if (b === 6) return { pos: TALLY.clone().add(V(-0.15, 1.25, 1.9 - 0.3 * k)), tgt: TALLY.clone().add(V(0, 1.12, 0)), fov: 40 };
  return CAM7;
}
