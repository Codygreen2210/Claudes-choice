// ------------------------------------------------------------------ the run, in real seconds T from ignition (Dec 10, 1954: nine rockets, 632 mph, water brake, stopped in 1.4 s, 46.2 g peak)
const VMAX = 632, TBURN = 5.0, TB = 5.6, TSTOP = 1.4, GPEAK = 46.2, MPH = 0.44704;
const brakeS = u => u <= 0 ? 0 : u >= 1 ? 1 : u * u * u * (u * (6 * u - 15) + 10);   // smootherstep: the stop builds, peaks mid-way, eases out
function vAt(T) { if (T <= 0) return 0; if (T < TBURN) return VMAX * Math.pow(T / TBURN, 1.15);
  if (T < TB) return VMAX - 2 * (T - TBURN); const v0 = VMAX - 2 * (TB - TBURN); return v0 * (1 - brakeS((T - TB) / TSTOP)); }
// distance (m) by integrating the speed once at load
const DT_ = 0.001, DTAB = [0]; for (let i = 1; i <= 12000; i++) DTAB.push(DTAB[i - 1] + 0.5 * (vAt((i - 1) * DT_) + vAt(i * DT_)) * MPH * DT_);
const distAt = T => T <= 0 ? 0 : T >= 12 ? DTAB[12000] : (() => { const x = T / DT_, i = Math.floor(x); return DTAB[i] + (DTAB[i + 1] - DTAB[i]) * (x - i); })();
// g on his body: + = thrown forward (braking), - = pressed back (rockets). The braking curve is scaled so its peak reads the recorded 46.2 g.
const accAt = T => (vAt(T + 0.002) - vAt(T - 0.002)) / 0.004 * MPH / 9.81;
let GSCALE = 1; { let pk = 0; for (let T = TB; T < TB + TSTOP; T += 0.002) pk = Math.max(pk, -accAt(T)); GSCALE = GPEAK / pk; }
const gAt = T => { const a = accAt(T); return a < 0 ? -a * GSCALE : -Math.min(12, a * 2.0) * smooth(-0.05, 0.6, T); };   // the rocket push builds over the first half second (no pop at ignition)   // the rockets pushed about 12 g (Smithsonian caption)

// each beat's slice of the run (story time T against the beat's own clock); beats 4-6 are slow motion, 6 is a replay of the peak
const T0 = 0.12;                                                     // frame one is already 0.12 s into the ignition (the fireball is out), and the countdown in beat 9 lands on it
const SLICE = [[T0, 0.6], [0.6, 2.2], [2.2, 5.0], [5.0, 5.6], [5.6, 5.75], [5.75, 7.0], [TB + 0.6, TB + 0.82], null, [9, 9], null];
function storyT(b, lt, d) { if (b === 9) return T0 - (d - lt); const s = SLICE[b]; if (!s) return 9; return s[0] + (s[1] - s[0]) * clamp(lt / d, 0, 1); }
const SLOWMO = { 4: true, 6: true };

// ------------------------------------------------------------------ him in the seat
const YAW = 180;                                                    // he faces +z, the way the sled runs
const F = fwdOf(YAW), Rt = rightOf(YAW), UP = V(0, 1, 0);
function blinkAt(s) { const u = ((s + 40) % 3.7) / 0.16; return u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0; }
const SIT = { thighR: [86, 0, 4], thighL: [86, 0, -4], shinR: [-78, 0, 0], shinL: [-78, 0, 0], footR: [-6, 0, 0], footL: [-6, 0, 0], spine1: [2, 0, 0], spine2: [0, 0, 0], neck: [-2, 0, 0],
  armR: A(14, 16, 0, 36, 0), armL: A(14, 16, 0, 36, 0) };
const SITPOSE = addPose(curl(curl({ ...SIT }, 'R', 70), 'L', 70), { thumb1R: [-40, 0, 0], thumb1L: [-40, 0, 0] });   // hands low by his hips in fists, gripping the seat edge
let HIPY = SEATTOP + 0.1;                                           // set at load so his seat rests on the seat pan

function guyAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  const T = storyT(b, lt, d), gz = (b === 7 || b === 8 && lt > d * 0.55) ? 0 : gAt(T);
  const fwd = Math.max(0, gz) / GPEAK, back = Math.max(0, -gz) / 12;
  const face = { blink: blinkAt(lt + b * 1.3) * (1 - Math.min(1, (fwd + back) * 3)) };
  const show = b !== 7 && !(b === 8 && lt > d * 0.55);
  // thrown into the straps when braking (the torso can only go so far), pressed into the seat by the rockets
  let pose = addPose(SITPOSE, {
    spine1: [-16 * fwd + 3 * back, 0, 0], spine2: [-12 * fwd + 2 * back, 0, 0], chest: [-6 * fwd, 0, 0],   // negative x bends him forward on this rig
    neck: [-26 * fwd + 10 * back, 0, 0], head: [-14 * fwd + 6 * back, 0, 0],
    armR: [26 * fwd - 6 * back, 6 * fwd, 0, -26 * fwd + 6 * back, 0], armL: [26 * fwd - 6 * back, 6 * fwd, 0, -26 * fwd + 6 * back, 0] });
  const brace = b === 9 ? smooth(0, Math.min(1.2, d * 0.4), lt) : b === 0 ? 1 - smooth(0, 0.5, lt) : 0;   // he braces for the countdown; it carries into frame one so the loop matches
  pose = addPose(pose, { neck: [4 * brace, 0, 0], head: [-3 * brace, 0, 0] });
  if (b === 8 && show) { const k = smooth(0.4, d * 0.5, lt); pose = addPose(SITPOSE, { spine1: [-14 * (1 - k), 0, 0], neck: [-28 * (1 - k), 0, 0], head: [-10 * (1 - k), 0, 0] }); }   // slumped, then he lifts his head
  const strain = Math.min(1, fwd * 1.6 + back * 1.2);
  Object.assign(face, { pain: 0.15 * strain, press: 1.0 * back, frown: 1.0 * back, jaw: 0.45 * fwd, oh: 0.7 * fwd, browIn: 0.8 * strain, squint: 0.4 * strain + 0.9 * back + 0.25 * brace, brow: 0.4 * brace + 0.2 * strain,
    fear: Math.max(0.35 * brace, b === 0 ? 0.35 + 0.5 * smooth(0, 0.4, lt) : 0.35 * strain), blink: b === 8 && show ? Math.max(face.blink, 0.6 * (1 - smooth(0.6, d * 0.45, lt))) : face.blink });
  const root = { x: 0, y: HIPY, z: 0.035 * fwd - 0.01 * back, yaw: YAW };
  const shake = b === 7 ? 0 : Math.min(1, vAt(T) / VMAX) * 0.5 + (T > 0 && T < 0.5 ? 1 - T / 0.5 : 0) + Math.min(1, fwd * 1.5);
  return { b, lt, d, T, gz, pose, root, face, show, shake };
}

// ------------------------------------------------------------------ cameras: every beat moves (push, orbit, track, roll); whips between some beats
const CAM0 = { pos: V(1.35, 0.95, 2.7), tgt: V(-0.1, 1.15, -0.4), fov: 46 };     // low front 3/4: his face, and the ignition fireball billowing out round the sled
function camAt(t, g) {
  const b = g.b, lt = g.lt, d = g.d, k = smooth(0, d, lt), e = sm(clamp(lt / d, 0, 1));
  if (b === 0) { const kk = smooth(0, d, lt); return { pos: CAM0.pos.clone().lerp(V(0.8, 1.15, 1.9), kk), tgt: CAM0.tgt.clone().lerp(V(0, 1.25, -0.1), kk), fov: CAM0.fov, roll: -5 * kk }; }
  if (b === 9) { const kk = smooth(d - 1.6, d, lt); return { pos: V(-1.6, 1.8, 3.6).lerp(CAM0.pos, kk), tgt: V(0, 1.0, -0.4).lerp(CAM0.tgt, kk), fov: lerp(44, CAM0.fov, kk), roll: 0 }; }   // lands exactly on frame one's camera
  if (b === 1) return { pos: V(0.12, 1.55, 1.0 - 0.15 * e), tgt: V(0, 1.3, -0.4), fov: 50, roll: 8 };                      // onboard, on the windscreen frame, looking back at him
  if (b === 2) { const a = lerp(-20, 55, e) * D2R; return { pos: V(Math.sin(a) * 3.2 + 0.2, 0.45, Math.cos(a) * 3.2), tgt: V(0, 0.95, -0.2), fov: 42, roll: -6 }; }   // swing round low beside the rails
  if (b === 3) return { pos: V(3.6 - 1 * e, 3.2 - 0.6 * e, 4.6 - 1.4 * e), tgt: V(0, 0.9, -1.8), fov: 44, roll: 0 };              // drone: high, ahead, looking back at the sled and its smoke
  if (b === 4) return { pos: V(0.85, 0.4, 3.2 - 0.4 * e), tgt: V(0.3, 0.45, 0.9), fov: 46, roll: 3 };   // ahead of the sled, low: the scoop bites the water, he's above it                         // at the rails, ahead of the scoop
  if (b === 5) return { pos: V(0.45, 1.8, 1.7), tgt: V(0, 1.05, 0.05), fov: 48, roll: -6 };                              // onboard again: he's thrown at the camera
  if (b === 6) { const a = lerp(20, 95, e) * D2R; return { pos: V(Math.sin(a) * 2.4, 1.3, Math.cos(a) * 2.4), tgt: V(0, 1.1, 0.05), fov: 40, roll: 0 }; }       // bullet-time orbit at the peak
  if (b === 7) return { pos: EY.clone().add(V(0.05, 0.05, 3.9 - 0.9 * e)), tgt: EY.clone(), fov: 40, roll: 0 };
  if (b === 8) { if (lt < d * 0.55) return { pos: V(1.6 - 0.3 * e, 1.6, 2.4 - 0.3 * e), tgt: V(0, 1.1, 0), fov: 42, roll: 0 };
    return { pos: BT.clone().add(V(0.35, 0.75, 3.0 - 0.6 * e)), tgt: BT.clone().add(V(0.05, 0.45, 0)), fov: 44, roll: 0 }; }
  return CAM0;
}
// whip pans: the last 0.12 s of a beat swings away, the first 0.12 s of the next swings in (with a directional blur)
const WHIPS = { 2: 1, 3: -1, 5: 1, 6: -1 };                          // beat -> direction of the whip out of it
function whipAt(t) { const b = beatAt(t), lt = t - B[b], d = DUR[b], W_ = 0.12;
  if (WHIPS[b] && lt > d - W_) return WHIPS[b] * sm((lt - (d - W_)) / W_);
  if (WHIPS[b - 1] && lt < W_) return -WHIPS[b - 1] * (1 - sm(lt / W_));
  return 0; }
