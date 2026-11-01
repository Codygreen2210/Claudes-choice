
// ------------------------------------------------------------------ the story
const YAW = 180;                                                    // he faces +z (toward the camera)
const T_DROP = 0.4;                                                 // (fingers loosen first, from 0.05 s)                                                // beat 0: the phone slips out of his hand
const LOOPSEED = { R: null, L: null }; let CHESTSEED = null; const CSEED = {}; let CHESTOFF = 0.153;   // set at load from where his chest's skin is
// turn a hand frame (palm normal n, finger direction u) toward another without passing through zero (lerping u from down to up flipped the hand)
function frameSlerp(n0, u0, n1, u1, k) { const q = (n, u) => { const N = n.clone().normalize(), U = u.clone().addScaledVector(N, -u.dot(N)).normalize(), X = new THREE.Vector3().crossVectors(U, N);
    return new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(X, U, N)); };
  const r = q(n0, u0).slerp(q(n1, u1), k); return { n: V(0, 0, 1).applyQuaternion(r), u: V(0, 1, 0).applyQuaternion(r) }; }
const bez = (a, b, c, k) => a.clone().multiplyScalar((1 - k) * (1 - k)).addScaledVector(b, 2 * k * (1 - k)).addScaledVector(c, k * k);
function blinkAt(s) { const u = ((s + 40) % 3.7) / 0.16; return u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0; }
const F = fwdOf(YAW), Rt = rightOf(YAW), UP = V(0, 1, 0);
const STAND1 = { ...addPose(STAND, { spine1: [-4, 0, 0], neck: [6, 0, 0] }), armL: A(10, 14, 0, 22), armR: A(10, 14, 0, 22) };
const PH = { rot: 15, n: 0.0165, u: 0.0, w: 0.0, c: 40, th: 30, opp: 30 };   // the phone across his palm: fingers wrap its edge, thumb on the screen
function phoneHand(low = 0) { const hd = wp(G.bones.head), n = UP.clone().multiplyScalar(0.62).addScaledVector(F, -0.78).normalize(), u = F.clone().multiplyScalar(0.78).addScaledVector(UP, 0.62).normalize();
  return { S: 'L', p: hd.clone().addScaledVector(F, 0.27).addScaledVector(Rt, 0.04).add(V(0, -0.32 - low, 0)), n, u, c: PH.c, th: PH.th, opp: PH.opp, memAbs: 'phoneL', seed: A(40, 10, 0, 110, -40) }; }
// his right palm pressed flat on his chest, over his heart (his left side)
function chestHand(S = 'R', dy = 0) { const c = wp(G.bones.chest), q = wq(G.bones.chest), fw = V(0, 0, -1).applyQuaternion(q), up = V(0, 1, 0).applyQuaternion(q), lf = V(-1, 0, 0).applyQuaternion(q);
  const s = S === 'R' ? 1 : -1;
  return { S, p: c.clone().addScaledVector(fw, CHESTOFF).addScaledVector(up, 0.02 + dy).addScaledVector(lf, S === 'R' ? 0.05 : -0.02), n: fw.clone().negate(), u: up.clone().addScaledVector(lf, 0.5 * s).normalize(), c: 14 + 6 * (S === 'R' ? 1 : 0), th: 14, soft: 0.004, memAbs: 'chest' + S, seed: A(60, 10, 30, 125, -30) }; }

// the state at a time ----------------------------------------------
function guyAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  const face = { blink: blinkAt(lt + b * 1.3) };
  let pose = STAND1, root = { x: STANDP.x, y: 0.95, z: STANDP.z, yaw: YAW }, hands = [], show = true, cut = false;
  let ins = 0, phoneMode = 'hand', phoneScr = 'msg', fall = -1, xr = 0, pulse = 1, bpm = 80, adr = 0, balloon = 0, bigShot = false, pot = 0, flow = 0, pain = 0;
  if (b === 7) {                                                    // the message comes in; he reads it
    hands = [phoneHand()]; pose = addPose(STAND1, { neck: [-16, 0, 0], head: [-10, 0, 0] }); ins = smooth(0.5, 0.8, lt);
    const k = smooth(1.2, d, lt); Object.assign(face, { look: [0, -0.6], brow: 0.5 * k, fear: 0.3 * k, oh: 0.2 * k });
  } else if (b === 0) {                                             // the shock: the phone slips, his hand goes to his chest
    const grab = smooth(T_DROP - 0.1, T_DROP + 0.95, lt), rel = smooth(T_DROP + 0.05, T_DROP + 0.85, lt), loose = smooth(0.05, T_DROP, lt);
    ins = 1 - smooth(0.0, 0.3, lt); pain = smooth(0.2, 1.0, lt); bpm = 120;
    phoneMode = lt < T_DROP ? 'hand' : 'fall'; fall = lt - T_DROP;
    // right hand: from hanging at his side, up in an arc (out in front, not across his belly) to flat on his chest
    { const ch = chestHand('R'), fr = RG.handFK('R', STAND1.armR), mid = fr.p.clone().lerp(ch.p, 0.5).addScaledVector(F, 0.13);
      const fo = frameSlerp(fr.n, fr.u, ch.n, ch.u, grab); hands.push({ ...ch, p: bez(fr.p, mid, ch.p, grab), n: fo.n, u: fo.u, c: 8 + (ch.c - 8) * grab, th: 8 + (ch.th - 8) * grab,
        seed: STAND1.armR, seedIsPrev: lt < 0.5 / 30 }); }
    // left hand: the fingers open, the phone slides off forward; then the hand sinks back down to his side
    { const ph = phoneHand(), fl = RG.handFK('L', STAND1.armL), mid = ph.p.clone().lerp(fl.p, 0.5).addScaledVector(F, 0.06).addScaledVector(Rt, -0.12);   // out to his left side, not across his belly
      const fo = frameSlerp(ph.n, ph.u, fl.n, fl.u, rel), hl = { ...ph, p: bez(ph.p, mid, fl.p, rel), n: fo.n, u: fo.u,
        c: PH.c - (PH.c - 6) * loose, th: PH.th, opp: PH.opp };   // the thumb stays on the screen (opening it swung it through the phone)
      hands.push(LOOPSEED.L && lt < 0.5 / 30 ? { ...hl, seed: LOOPSEED.L, seedIsPrev: true } : hl); }
    pose = addPose(STAND1, { spine1: [10 * pain, 0, 0], spine2: [8 * pain, 0, 0], neck: [-16 * (1 - pain) - 6 * pain, 0, 0], head: [-10 * (1 - pain), 0, 0] }); root.y = 0.95 - 0.03 * pain;
    Object.assign(face, { fear: pain, brow: pain, squint: 0.6 * pain, jaw: 0.3 * pain, oh: 0.3 * pain, look: [0, -0.2] });
  } else if (b === 1 || b === 2) {                                  // x-ray: his heart pounds; (2) the adrenal glands flood it with adrenaline
    xr = 1; phoneMode = 'floor'; bpm = 130; pain = 1;
    if (b === 2) adr = smooth(0.2, 1.4, lt);
    hands = [CSEED[b] ? { ...chestHand('R'), seed: CSEED[b], seedIsPrev: true } : chestHand('R')]; pose = addPose(STAND1, { spine1: [10, 0, 0], spine2: [8, 0, 0], neck: [-6, 0, 0] }); root.y = 0.92;
  } else if (b === 3) {                                             // the big heart: its bottom balloons out like a pot
    show = false; bigShot = true; balloon = smooth(0.3, 2.2, lt); pot = smooth(2.0, 2.6, lt); bpm = 90; pulse = 0.5;
  } else if (b === 4) {                                             // it can't pump right: weak beats, slow flow; feels like a heart attack
    show = false; bigShot = true; balloon = 1; pot = 0; bpm = 70; pulse = 0.25; flow = 1;
  } else if (b === 5) {                                             // chest pain or trouble breathing: call 911
    phoneMode = 'hand'; phoneScr = 'call'; pain = 1; ins = smooth(0.15, 0.45, lt) * (1 - smooth(d - 0.3, d - 0.05, lt));
    hands = [phoneHand(), CHESTSEED ? { ...chestHand('R'), seed: CHESTSEED, seedIsPrev: true } : chestHand('R')];
    pose = addPose(STAND1, { spine1: [8, 0, 0], spine2: [6, 0, 0], neck: [-16, 0, 0], head: [-8, 0, 0] }); root.y = 0.93;
    Object.assign(face, { fear: 0.7, brow: 0.8, squint: 0.4, look: [0, -0.6] });
  } else if (b === 6) {                                             // most heal in weeks: the heart goes back to its shape; rarely, it kills
    show = false; bigShot = true; balloon = 1 - smooth(0.3, 2.4, lt); bpm = 75; pulse = 0.4 + 0.6 * smooth(0.3, 2.4, lt); flow = smooth(0.3, 2.4, lt);
  }
  const wb = 2 * Math.PI * Math.round(TOTAL / 2.6) / TOTAL;           // breathing (whole cycles over the loop)
  pose = addPose(pose, { spine1: [0.9 * Math.sin(wb * t), 0, 0], spine2: [0.6 * Math.sin(wb * t + 0.4), 0, 0], neck: [0.7 * Math.sin(wb * t + 1.1), 0, 0] });
  return { b, lt, d, pose, root, hands, show, cut, ins, phoneMode, phoneScr, fall, xr, pulse, bpm, adr, balloon, bigShot, pot, flow, pain, face };
}

// ------------------------------------------------------------------ cameras
const CAM7 = { pos: V(0.55, 1.55, 1.85), tgt: V(0.25, 1.3, 0.4), fov: 44 };       // in front of him (a little to his left, the phone side): his face, the phone, the room behind
function camAt(t, g) {
  const b = g.b, lt = g.lt, d = g.d, k = smooth(0, d, lt);
  if (b === 7) return { pos: CAM7.pos.clone().add(V(0.05 * (1 - k), 0, 0.12 * (1 - k))), tgt: CAM7.tgt, fov: CAM7.fov };
  if (b === 0) return { pos: CAM7.pos.clone().lerp(V(0.45, 1.56, 1.5), sm(Math.min(1, lt / 1.2))), tgt: CAM7.tgt.clone().lerp(V(0.18, 1.42, 0.4), sm(Math.min(1, lt / 1.2))), fov: 44 };
  if (b === 1 || b === 2) return { pos: V(0.38, 1.42, 1.5 - 0.12 * k), tgt: V(0.2, 1.3, 0.4), fov: 42 };
  if (b === 3) { const w = smooth(1.7, 2.7, lt);                   // close on the heart as it balloons, then pull back to show the pot beside it
    return { pos: HS.clone().add(V(0.03 + 0.14 * w, 1.0, 1.45 + 0.85 * w)), tgt: HS.clone().add(V(0.17 * w, 0.95, 0)), fov: 42 }; }
  if (b === 4 || b === 6) return { pos: HS.clone().add(V(0.04, 1.0, 1.55 - 0.12 * k)), tgt: HS.clone().add(V(0, 0.95, 0)), fov: 42 };
  if (b === 5) return { pos: V(0.5, 1.56, 1.5 + 0.1 * (1 - k)), tgt: V(0.3, 1.38, 0.4), fov: 44 };
  return CAM7;
}
