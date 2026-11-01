const PH = { rot: 15, n: 0.0165, u: 0.0, w: 0.0, c: 40, th: 30, opp: 30 };   // the phone in his hand: angle of its long side off the palm's width, offsets, finger curl
window.PH = PH;

// ------------------------------------------------------------------ the story
const STANDP = V(-1.45, 0, 2.05);                                   // where he stands: by the truck's back left corner, facing the back wall (-z)
const YAW = 0;
const LOOPSEED = { R: null, L: null };
function blinkAt(s) { const u = ((s + 40) % 3.7) / 0.16; return u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0; }
const F = fwdOf(YAW), Rt = rightOf(YAW), UP = V(0, 1, 0);         // his forward (-z), his right (+x, the truck side), up
const STAND1 = { ...addPose(STAND, { spine1: [-4, 0, 0], neck: [6, 0, 0] }), armL: A(10, 14, 0, 22), armR: A(10, 14, 0, 22) };
// his phone in the left hand, screen toward his face
function phoneHand() { const hd = wp(G.bones.head), n = UP.clone().multiplyScalar(0.62).addScaledVector(F, -0.78).normalize(), u = F.clone().multiplyScalar(0.78).addScaledVector(UP, 0.62).normalize();
  return { S: 'L', p: hd.clone().addScaledVector(F, 0.27).addScaledVector(Rt, 0.04).add(V(0, -0.32, 0)), n, u, c: PH.c, th: PH.th, opp: PH.opp, memAbs: 'phoneL', seed: A(40, 10, 0, 110, -40) }; }
// his left palm on his forehead (headache)
function browHand() { const hd = wp(G.bones.head), q = wq(G.bones.head), fwdH = V(0, 0, -1).applyQuaternion(q), upH = V(0, 1, 0).applyQuaternion(q);
  return { S: 'L', p: hd.clone().addScaledVector(fwdH, 0.14).addScaledVector(upH, 0.06), n: fwdH.clone().negate(), u: Rt.clone().addScaledVector(upH, 0.3).normalize(), c: 18, th: 15, soft: 0.012, memAbs: 'browL', seed: A(110, 20, 20, 135, -20) }; }
// his right hand catching himself on the truck's bed rail (top 1.25, its side at x = -0.98)
function railHand(dz = 0) { return { S: 'R', p: V(-0.99, 1.265, STANDP.z - 0.12 + dz), n: V(0, -1, 0), u: F.clone().addScaledVector(Rt, 0.4).normalize(), c: 45, th: 30, memAbs: 'railR', seed: A(40, 30, 0, 50, -40) }; }

// the state at a time ----------------------------------------------
function guyAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  const face = { blink: blinkAt(lt + b * 1.3) };
  let pose = STAND1, root = { x: STANDP.x, y: 0.95, z: STANDP.z, yaw: YAW }, hands = [], show = true, cut = false;
  let ex = 1, fill = 0, xr = 0, phoneOn = false, phoneScroll = 0, vesT = -1, starve = 0, sick = 0, vig = 0, black = 0, door = 0, alarmOn = false, alarmShot = false, crank = -1, sway = 0, redX = 0;
  if (b === 7 || b === 0) {                                         // 7: he's just started it and stands scrolling while it warms up; 0: the garage fills
    phoneOn = true; phoneScroll = (b === 7 ? lt : DUR[7] + lt) * 50;
    hands = [b === 0 && LOOPSEED.L ? { ...phoneHand(), seed: LOOPSEED.L, seedIsPrev: true } : phoneHand()];
    pose = addPose(STAND1, { neck: [-16, 0, 0], head: [-10, 0, 0] }); Object.assign(face, { look: [0, -0.6] });
    if (b === 7) { crank = lt; ex = smooth(0.3, 1.2, lt) * 0.6; fill = 0; } else { ex = 0.6 + 0.4 * smooth(0, d, lt); fill = 0.25 * smooth(0, d, lt); }
  } else if (b === 1) {                                             // the exhaust up close at the pipe: you can't see it or smell it
    ex = 0.45; fill = 0.15; phoneOn = true; phoneScroll = (DUR[7] + DUR[0] + lt) * 50; hands = [phoneHand()];
    pose = addPose(STAND1, { neck: [-16, 0, 0], head: [-10, 0, 0] }); Object.assign(face, { look: [0, -0.6] });
  } else if (b === 2) {                                             // inside his blood: the CO pushes the oxygen off the red cells
    show = false; vesT = lt; ex = 0;
  } else if (b === 3) {                                             // x-ray: his brain and heart go dim
    xr = 1; starve = smooth(0.2, d, lt); ex = 1; fill = 0.4;
    pose = addPose(STAND1, { neck: [-4, 0, 0] });
  } else if (b === 4) {                                             // headache, dizzy, sick: hand to his forehead, swaying
    ex = 1; fill = 0.5 + 0.1 * smooth(0, d, lt); sick = smooth(0, d, lt); sway = sick;
    hands = [{ ...browHand(), blend: smooth(0.15, 1.0, lt) }];
    pose = addPose(STAND1, { neck: [6 * sick, 4 * Math.sin(lt * 2.2) * sick, 3 * Math.sin(lt * 1.7) * sick], head: [4, 0, 0], spine1: [3 * Math.sin(lt * 1.6) * sick, 0, 2 * Math.sin(lt * 1.3) * sick] });
    Object.assign(face, { squint: 0.6 * sick, brow: 0.7 * sick, jaw: 0.1, look: [0, -0.2] });
  } else if (b === 5) {                                             // confused, weak: he catches himself on the truck; it all goes dark
    ex = 1; fill = 0.65; sick = 1; sway = 1; const k = smooth(0, 1.2, lt);
    { const h = railHand(); h.p.y += 0.12 * (1 - k) ** 2; h.p.x -= 0.08 * (1 - k); hands = [{ ...h, blend: k }]; }     // comes over the rail and down onto it
    pose = addPose(STAND1, { spine1: [10 * k, 0, 6 * k], spine2: [6 * k, 0, 4 * k], neck: [-10 * k + 4 * Math.sin(lt * 2), 6 * Math.sin(lt * 1.4), 0], head: [-6 * k, 0, 4 * k] });
    root = { x: STANDP.x + 0.08 * k, y: 0.95 - 0.05 * k, z: STANDP.z, yaw: YAW + 8 * k };
    vig = smooth(0.4, d - 0.25, lt) * (1 - 0.06 * Math.max(0, Math.sin(lt * 7.5))); black = smooth(d - 0.45, d - 0.05, lt);      // the edges go dark in waves (each heartbeat), then black
    Object.assign(face, { squint: 0.4, brow: 0.5, jaw: 0.25, look: [0.2, -0.3], blink: lt > d - 1.0 ? smooth(d - 1.0, d - 0.4, lt) : 0 });
  } else if (b === 6) {                                             // the door wide open is still not safe; then the alarm: get out
    show = false; ex = 1; door = 1; fill = 0.25;
    cut = lt >= 2.2 && lt - 2.2 < 1 / 30 + 1e-6;
    if (lt < 2.2) redX = smooth(0.7, 1.0, lt); else { alarmShot = true; alarmOn = Math.floor((lt - 2.2) / 0.25) % 2 === 0; }
  }
  const wb = 2 * Math.PI * Math.round(TOTAL / 2.6) / TOTAL;           // breathing (whole cycles over the loop)
  pose = addPose(pose, { spine1: [0.9 * Math.sin(wb * t), 0, 0], spine2: [0.6 * Math.sin(wb * t + 0.4), 0, 0], neck: [0.7 * Math.sin(wb * t + 1.1), 0, 0] });
  return { b, lt, d, pose, root, hands, show, cut, ex, fill, xr, phoneOn, phoneScroll, vesT, starve, sick, vig, black, door, alarmOn, alarmShot, crank, sway, redX, face };
}

// ------------------------------------------------------------------ cameras
function shakeV(t, a) { return V(vn1(t * 14, 1) * a * 0.5, vn1(t * 14, 2) * a, vn1(t * 14, 3) * a); }
const CAM7 = { pos: V(-2.55, 1.8, 0.15), tgt: V(-1.15, 0.95, 2.6), fov: 52 };      // at his front-left by the shelves: his face, the truck's back end, the pipe, the shut door behind him
function camAt(t, g) {
  const b = g.b, lt = g.lt, d = g.d, k = smooth(0, d, lt);
  if (b === 7) return { pos: CAM7.pos.clone().add(V(0.05 * (1 - k), 0.05 * (1 - k), -0.1 * (1 - k))), tgt: CAM7.tgt, fov: CAM7.fov };
  if (b === 0) return { pos: CAM7.pos.clone().lerp(V(-2.4, 1.72, 0.5), k), tgt: CAM7.tgt.clone().lerp(V(-1.2, 0.95, 2.6), k), fov: 52 - 4 * k };
  if (b === 1) return { pos: TPIPE.clone().add(V(-0.55, 0.32, -1.05 + 0.15 * k)), tgt: TPIPE.clone().add(V(-0.35, 0.18, 0.15)), fov: 42 };
  if (b === 2) return { pos: VES.clone().add(V(0.05, 0.08, 1.6 - 0.5 * k)), tgt: VES.clone().add(V(0, 0, -1.0)), fov: 55 };
  if (b === 3) return { pos: V(-1.75, 1.55, 1.2 - 0.1 * k), tgt: V(-1.45, 1.42, 2.05), fov: 46 };
  if (b === 4) { const r = 2.5 * Math.sin(lt * 1.7) * g.sick; return { pos: V(-1.85, 1.62, 1.15).add(shakeV(t * 0.3, 0.02 * g.sick)), tgt: V(-1.45, 1.5, 2.05), fov: 42, roll: r }; }
  if (b === 5) { const r = 5 * Math.sin(lt * 1.4) * g.sick; return { pos: V(-2.05, 1.55, 0.85).add(shakeV(t * 0.3, 0.03)), tgt: V(-1.3, 1.2, 2.1), fov: 48 + 6 * k, roll: r }; }
  if (b === 6) { if (!g.alarmShot) return { pos: V(0.9, 1.7, 7.2 - 0.4 * smooth(0, 2.2, lt)), tgt: V(-0.2, 1.0, 2.0), fov: 50 };
    return { pos: V(GW0 + 0.75, 1.58, 2.6), tgt: V(GW0, 1.55, 2.6), fov: 40 }; }
  return CAM7;
}
