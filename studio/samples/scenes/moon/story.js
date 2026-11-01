// ------------------------------------------------------------------ the story
const YAW = 180;                                                    // he faces +z (the shore and the camera); the sea and the moon are behind him
const F = fwdOf(YAW), Rt = rightOf(YAW), UP = V(0, 1, 0);
function blinkAt(s) { const u = ((s + 40) % 3.7) / 0.16; return u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0; }
const STAND1 = { ...addPose(STAND, { spine1: [-3, 0, 0], neck: [4, 0, 0] }), armL: A(8, 12, 0, 20), armR: A(8, 12, 0, 20) };
// looking back over his right shoulder and up at the moon; his right hand comes up a little ("what?")
const BACK = { ...addPose(STAND1, { spine2: [0, -14, 0], chest: [0, -10, 0], neck: [16, -42, 0], head: [18, -24, 0] }), armR: A(28, 22, 10, 75, 30), armL: A(14, 18, 0, 30) };
const TURN0 = mixPose(STAND1, BACK, 0.4);                           // frame one: already turning (so the loop's end lands here too)
// in the dark: hands a little out, looking around
const DARK = { ...addPose(STAND1, { spine2: [-2, 6, 0], neck: [6, 10, 0], head: [4, 8, 0] }), armR: A(22, 26, 0, 40, 20), armL: A(22, 26, 0, 40, 20) };
const WL_HI = -0.5, WL_LO = -0.95;                                  // the sea at high tide, and after the tide sinks

// the state at a time ----------------------------------------------
function guyAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  const face = { blink: blinkAt(lt + b * 1.3) };
  let pose = STAND1, root = { x: STANDP.x, y: 0.95, z: STANDP.z, yaw: YAW }, hands = [], show = true, cut = false;
  let stage = 'dock', moon = 0, wl = WL_LO, lant = 1, bob = 0, stars = 1, shake = 0;
  let pop = 0, phot = -1, tideK = 0, tilt = 23.5, pull = 0, spin = 0, ret = 0;
  if (b === 0) {                                                    // the moon blinks out; he spins round to look
    const off = smooth(0.0, 0.7, lt), fl = lt < 0.7 ? 0.5 + 0.5 * Math.cos(lt * 15.7) : 0;   // starts dimming on frame one (motion from the first frame)   // a flicker and a half at 2.5 a second (whole-scene light: stays under 3 flashes a second), then gone
    moon = (1 - off) * (0.35 + 0.65 * fl); wl = WL_HI; bob = 1; shake = smooth(0.15, 0.4, lt) * (1 - smooth(0.6, 1.3, lt));
    const k = smooth(0.0, 0.9, lt); pose = mixPose(TURN0, BACK, k);
    Object.assign(face, { fear: 0.2 + 0.7 * smooth(0.3, 1.0, lt), brow: 0.9 * smooth(0.2, 0.8, lt), oh: 0.5 * smooth(0.35, 0.9, lt), look: [-0.3, 0.6] });
  } else if (b === 1) {                                             // space: the moon pops, but its last light is still on the way
    show = false; stage = 'space'; pop = lt; phot = lt; spin = lt;
  } else if (b === 2) {                                             // the tide sinks down the pilings
    wl = WL_HI + (WL_LO - WL_HI) * smooth(0.2, d - 0.2, lt); pose = BACK; Object.assign(face, { fear: 0.7, brow: 0.7, look: [-0.3, 0.6] });
  } else if (b === 3) {                                             // space: the Sun still pulls a smaller tide
    show = false; stage = 'space'; tideK = 1 - 0.54 * smooth(0.6, 2.4, lt); pull = smooth(0.5, 1.2, lt); spin = 3 + lt;
  } else if (b === 4) {                                             // the dark: 125x darker than a full moon night
    lant = 0.55; const k = smooth(0, 0.8, lt); pose = mixPose(BACK, DARK, k);
    pose = addPose(pose, { neck: [0, 26 * Math.sin(lt * 1.6) * smooth(0.6, 1.4, lt), 0] });
    Object.assign(face, { fear: 0.6, brow: 0.8, squint: 0.4, look: [0.5 * Math.sin(lt * 2.1), 0.1] });
  } else if (b === 5) {                                             // the hatchlings head for the street light, not the sea
    show = false; stage = 'beach';
  } else if (b === 6) {                                             // the reef: the corals wait to let their eggs go
    show = false; stage = 'reef'; stars = 0;
  } else if (b === 7) {                                             // space: over millions of years the tilt swings to 85 degrees
    show = false; stage = 'space'; tilt = 23.5 + (85 - 23.5) * smooth(0.5, 3.0, lt); spin = 6 + 0.5 * lt;
  } else if (b === 8) {                                             // tipped over, one side hardly ever sees the Sun
    show = false; stage = 'space'; tilt = 85; spin = 8 + 0.8 * lt;
  } else if (b === 9) {                                             // back on the dark dock; at the end the moon comes back (the loop)
    lant = 0.55 + 0.45 * smooth(d - 0.9, d, lt); ret = smooth(d - 0.9, d, lt);
    moon = ret; wl = WL_LO + (WL_HI - WL_LO) * ret; bob = ret;
    pose = mixPose(mixPose(BACK, DARK, 1 - smooth(0, 0.6, lt) * 0), TURN0, smooth(d - 1.0, d - 0.05, lt));
    pose = addPose(pose, { neck: [0, 18 * Math.sin(lt * 1.3) * (1 - smooth(d - 1.2, d - 0.6, lt)), 0] });
    const e = smooth(d - 1.0, d - 0.05, lt);
    Object.assign(face, { fear: 0.6 * (1 - e) + 0.2 * e, brow: 0.8 * (1 - e), look: [-0.3 * e, 0.6 * e] });
  }
  const wb = 2 * Math.PI * Math.round(TOTAL / 2.6) / TOTAL;           // breathing (whole cycles over the loop)
  pose = addPose(pose, { spine1: [0.9 * Math.sin(wb * t), 0, 0], spine2: [0.6 * Math.sin(wb * t + 0.4), 0, 0], neck: [0.7 * Math.sin(wb * t + 1.1), 0, 0] });
  return { b, lt, d, pose, root, hands, show, cut, face, stage, moon, wl, lant, bob, stars, shake, pop, phot, tideK, tilt, pull, spin, ret };
}

// ------------------------------------------------------------------ cameras
const CAM0 = { pos: V(0.42, 1.05, 0.95), tgt: V(0.02, 1.95, -3.6), fov: 46 };   // low, in front of him: his face, the moon behind and above his head
function camAt(t, g) {
  const b = g.b, lt = g.lt, d = g.d, k = smooth(0, d, lt);
  const S = V(0, 0, 0); if (g.shake) S.set(0.012 * Math.sin(t * 61) * g.shake, 0.01 * Math.sin(t * 47 + 1) * g.shake, 0);
  if (b === 0) return { pos: CAM0.pos.clone().add(V(0, 0, -0.12 * k)).add(S), tgt: CAM0.tgt, fov: CAM0.fov };
  if (b === 9) { const e = smooth(d - 1.0, d, lt), pos = V(0.3, 1.45, 0.75).lerp(CAM0.pos, e), tgt = V(0, 1.55, -1.5).lerp(CAM0.tgt, e); return { pos, tgt, fov: 44 + 2 * e }; }
  if (b === 2) return { pos: V(5.2, 0.4 - 0.1 * k, -1.75), tgt: V(0.7, 0.05, -1.9), fov: 52 };
  if (b === 4) return { pos: V(0.25, 1.5, -0.3 - 0.15 * k), tgt: V(0, 1.6, -1.5), fov: 42 };
  if (b === 1) return { pos: SP.clone().add(V(0.7 + 0.1 * k, 1.2, 7.8 - 0.5 * k)), tgt: SP.clone().add(V(0.15, 1.0, -0.4)), fov: 42 };
  if (b === 3) return { pos: SP.clone().add(V(0, 0.2, 6.6 - 0.4 * k)), tgt: SP.clone().add(V(-0.2, 0.05, 0)), fov: 44 };
  if (b === 7) return { pos: SP.clone().add(V(0, 0.25, 5.6 - 0.4 * k)), tgt: SP.clone().add(V(0, 0.4, 0)), fov: 44 };
  if (b === 8) return { pos: SP.clone().add(V(1.0, 0.3, 5.0 - 0.4 * k)), tgt: SP.clone().add(V(0, 0, 0)), fov: 44 };
  if (b === 5) return { pos: BE.clone().add(V(-0.08, 0.34, -1.75 + 0.15 * k)), tgt: BE.clone().add(V(-0.05, 0.12, 2.0)), fov: 48 };
  if (b === 6) return { pos: RF.clone().add(V(0.3, 0.5, 1.8 - 0.3 * k)), tgt: RF.clone().add(V(0, 0.35, 0)), fov: 46 };
  return CAM0;
}
