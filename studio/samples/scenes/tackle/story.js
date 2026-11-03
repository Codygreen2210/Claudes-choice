// ------------------------------------------------------------------ story: one shot per line
const C = V(0, 0, -36);                                      // where they met: inside the box, in front of the goal
function run(ph, lean = -10) { const s = Math.sin(ph), c = Math.cos(ph);
  return curl(curl({ spine1: [lean, 0, 0], chest: [-4, 0, 0], neck: [8, 0, 0], thighR: [22 + 48 * s, 0, 0], thighL: [22 - 48 * s, 0, 0],
    shinR: [-28 - 70 * Math.max(0, -s) - 15 * Math.max(0, c), 0, 0], shinL: [-28 - 70 * Math.max(0, s) - 15 * Math.max(0, -c), 0, 0], footR: [8 * s, 0, 0], footL: [-8 * s, 0, 0],
    armR: A(8 - 48 * s, 14, 0, 88), armL: A(8 + 48 * s, 14, 0, 88) }, 'R', 55), 'L', 55); }
const bob = ph => 0.95 + 0.035 * Math.abs(Math.cos(ph));
// the keeper's leap to clear it (knee up, arms out) and the forward knocked back, then down
const LEAP = curl(curl({ spine1: [-14, 0, 0], chest: [-8, 0, 0], neck: [10, 0, 0], thighR: [105, 0, 0], shinR: [-95, 0, 0], thighL: [-12, 0, 0], shinL: [-40, 0, 0], armR: A(120, 35, 0, 25), armL: A(115, 40, 0, 30) }, 'R', 20), 'L', 20);
const HIT = curl(curl({ spine1: [18, 0, 0], chest: [14, 0, 0], neck: [20, 0, 0], head: [18, 0, 0], thighR: [30, 0, 0], shinR: [-40, 0, 0], thighL: [-10, 0, 0], shinL: [-25, 0, 0], armR: A(60, 55, 0, 30), armL: A(55, 60, 0, 35) }, 'R', 15), 'L', 15);
const DOWN = curl(curl({ spine1: [4, 0, 0], neck: [6, 0, 0], head: [0, 0, 8], thighR: [8, 0, 6], shinR: [-12, 0, 0], thighL: [4, 0, -4], shinL: [-6, 0, 0], armR: A(-5, 30, 0, 20), armL: A(-5, 25, 0, 25), footR: [20, 0, 0], footL: [22, 0, 0] }, 'R', 10), 'L', 10);
const HANDSHEAD = curl(curl({ ...STAND, neck: [18, 0, 0], head: [12, 0, 0], armR: A(155, 35, 10, 125), armL: A(155, 35, 10, 125) }, 'R', 20), 'L', 20);
const HIPS = { ...STAND, armR: A(10, 35, 40, 100, 0, 0, 0), armL: A(10, 35, 40, 100, 0, 0, 0) };
function ballAt(t0, t1, t, p0, p1, h) { const u = clamp((t - t0) / (t1 - t0), 0, 1); return p0.clone().lerp(p1, u).add(V(0, h * 4 * u * (1 - u), 0)); }
// each shot sets both men, the ball, the camera, the readout; returns the focus point
const MAP = { 0: 0, 1: 1, 2: 3, 3: 5, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 7, 10: 8, 11: 9, 12: 6, 13: 12 };   // the script's lines -> the shot each one uses
const XRL = [4, 5, 6, 7, 8];                                   // x-ray explainer lines (frozen at the moment of the hit)
let KCUR = 0, KC = 0.4;
function shot(t) { const nb = beatAt(t), lt = t - B[nb], dur = DUR[nb], XRB = XRL.includes(nb); let u = XRB ? 0 : lt / dur; const b = MAP[nb];
  let xr = XRB;
  out.visible = false; card.visible = false; hud.visible = false; G.root.visible = K.root.visible = true; ball.visible = true; sun.intensity = 3.2;
  let fpos, fpose, kpos, kpose, cp, ct, fov = 34, near = 0.05;
  switch (b) {
    case 0: case 5: { // the collision (0: frozen moment, camera round it; 5: slow motion, side on)
      let k = b === 0 ? 0.41 + 0.02 * u : clamp((u - 0.03) / 0.55, 0, 1); const kc = KC;      // kc: the moment of contact
      if (nb === 3 && k > kc + 0.01) { k = kc + 0.01; xr = true; }                             // line 3: at the hit, freeze and go into the x-ray
      KCUR = k;
      const pre = clamp(k / kc, 0, 1), post = clamp((k - kc) / (1 - kc), 0, 1);
      const ph = (b === 0 ? 2.2 : 1.6 + lt * 3.2);
      fpose = post > 0 ? mixPose(HIT, DOWN, sm(clamp((post - 0.35) / 0.65, 0, 1))) : mixPose(run(ph), HIT, sm(clamp((pre - 0.8) / 0.2, 0, 1)));
      const fall = sm(clamp((post - 0.25) / 0.75, 0, 1));
      fpos = { x: C.x, y: lerp(bob(ph), 0.16, fall), z: C.z + 1.6 * (1 - pre) - 0.9 * post, yaw: 0, tilt: lerp(post > 0 ? 25 * sm(Math.min(1, post * 4)) : -8, 88, fall) };
      kpose = mixPose(run(ph + 1.3), LEAP, sm(clamp((pre - 0.5) / 0.5, 0, 1))); kpose = post > 0 ? mixPose(LEAP, mixPose(STAND, LEAP, 0.3), sm(post)) : kpose;
      kpos = { x: C.x + 0.15, y: 0.95 + 0.38 * Math.sin(Math.PI * clamp((k - 0.25) / 0.45, 0, 1)), z: C.z - 0.95 - 3.2 * (1 - pre) + 0.4 * post, yaw: 180, tilt: -12 * clamp(k * 2, 0, 1) };
      ball.position.copy(C).add(V(0.4 + 2.5 * post, 2.3 + 1.2 * post - 1.5 * post * post, -0.6 - 3 * post));
      if (b === 0) { const a = lerp(-30, 45, u) * D2R; cp = V(C.x + Math.sin(a) * 6.2, 1.5, C.z - 0.5 + Math.cos(a) * 6.2); ct = V(C.x, 1.25, C.z - 0.5); }
      else { const push = xr ? sm(clamp((u - 0.6) / 0.4, 0, 1)) : 0; cp = V(C.x + lerp(6.5, 2.4, push), lerp(1.3, 1.5, push), C.z - 0.5 + lerp(0, 1.4, push)); ct = V(C.x, lerp(1.1, 1.35, push), C.z - 0.5); }
      break; }
    case 1: { // who he was: the stand-in in white, centre circle
      fpose = STAND; fpos = { x: 0, y: 0.95, z: 0, yaw: 25 }; kpose = STAND; kpos = { x: 6, y: 0.95, z: -30, yaw: 180 }; K.root.visible = false;
      ball.position.set(0.5, 0.11, -0.6); cp = V(1.8 - 0.4 * u, 1.55, -3.6 + 0.8 * u); ct = V(0, 1.3, 0); fov = 32;
      hud.visible = true; drawHud([['TENERIFE', 'FORWARD'], ['AGE', '30']]); break; }
    case 2: { // the stadium, stoppage time
      const ph = t * 4; fpose = run(ph); fpos = { x: 4, y: bob(ph), z: -6 - u * 4, yaw: 10 }; kpose = STAND; kpos = { x: 0, y: 0.95, z: -50, yaw: 180 };
      ball.position.set(3, 0.11, -12 - u * 5); cp = V(-40, 26, 30 - 10 * u); ct = V(0, 0, -20); fov = 40;
      hud.visible = true; drawHud([['TENERIFE 2-2 ANDORRA', ''], ['STOPPAGE TIME', "90+7'", '#ffd23a']]); break; }
    case 3: { // the long ball over the top; he chases it
      const ph = 1.6 + t * 9; fpose = run(ph); const z = lerp(-18, -31, u); fpos = { x: 0.4, y: bob(ph), z, yaw: 0 }; kpose = STAND; kpos = { x: 0, y: 0.95, z: -50.5, yaw: 180 };
      ball.position.copy(ballAt(0, dur * 1.15, lt, V(0.6, 1.2, 8), V(0.4, 2.2, -36.6), 18)); cp = V(7.8, 1.7, z + 0.6); ct = V(0.4, 1.4, z - 0.9); fov = 40; break; }
    case 4: { // the keeper runs off his line to clear it
      const ph = 0.4 + t * 9; kpose = run(ph); const z = lerp(-50.5, -40, u); kpos = { x: 0.15, y: bob(ph), z, yaw: 180 };
      const ph2 = 1.6 + t * 9; fpose = run(ph2); fpos = { x: 0.4, y: bob(ph2), z: lerp(-31, -34.4, u), yaw: 0 };
      ball.position.copy(ballAt(-1, 1.6 * dur, lt, V(0.5, 8, -26), V(0.4, 2.2, -36.6), 2)); cp = V(-5, 1.4, z - 6); ct = V(0.2, 1.3, z + 3); fov = 40; break; }
    case 6: { // he lies still; the keeper, hands on his head
      fpose = DOWN; fpos = { x: C.x, y: 0.16, z: C.z - 0.9, yaw: 0, tilt: 88 }; kpose = HANDSHEAD; kpos = { x: C.x + 2.2, y: 0.95, z: C.z - 3.0, yaw: 200 };
      ball.position.set(C.x + 6, 0.11, C.z - 8); const a = lerp(0.3, 0.6, u); cp = V(C.x + Math.sin(a) * 15, 9 - 2 * u, C.z + Math.cos(a) * 15); ct = V(C.x, 0.4, C.z - 1.5); fov = 30; break; }
    case 7: { // the red card; the match is called off
      fpose = DOWN; fpos = { x: C.x, y: 0.16, z: C.z - 0.9, yaw: 0, tilt: 88 }; kpose = mixPose(STAND, HANDSHEAD, 0.25); kpos = { x: C.x + 3.5, y: 0.95, z: C.z - 4.5, yaw: 220 };
      card.visible = true; card.position.set(C.x + 2.4, 1.75 + 0.15 * sm(Math.min(1, u * 3)), C.z - 5.4); card.lookAt(C.x + 12, 1.8, C.z + 4); ball.visible = false;
      cp = V(C.x + 9, 2.2, C.z + 1.5); ct = V(C.x + 2.8, 1.5, C.z - 4.6); fov = 32;
      hud.visible = true; drawHud([['KEEPER', 'SENT OFF', '#ff6a5c'], ['MATCH', 'CALLED OFF']], 'RED CARD'); break; }
    case 8: case 9: { // the ambulance; then the hospital
      G.root.visible = K.root.visible = false; ball.visible = false; out.visible = true; sun.intensity = 0.6;
      if (b === 8) { const z = 120 - (lt + 0) * 22; amb.position.set(-3.5, 0, z); amb.rotation.y = 0; cp = V(5, 3.2, z + 14).add(out.position); ct = V(-3.5, 1.5, z - 4).add(out.position); fov = 40;
        hud.visible = true; drawHud([['ON THE WAY', 'HEART STOPPED', '#ff6a5c'], ['PARAMEDICS', 'BROUGHT HIM BACK', '#2fbf71']]); }
      else { amb.position.set(-12, 0, -190); amb.rotation.y = 0.6; cp = V(18, 6, -150 - 6 * u).add(out.position); ct = V(-25, 9, -205).add(out.position); fov = 40;
        hud.visible = true; drawHud([['AT FIRST', 'SERIOUS, STABLE', '#ffd23a'], ['THEN', u < 0.45 ? '...' : 'GOT WORSE', '#ff6a5c']]); }
      fpose = STAND; fpos = { x: 0, y: -50, z: 0 }; kpose = STAND; kpos = { x: 2, y: -50, z: 0 }; break; }
    default: { // 10-12: the empty pitch at night, the ball on the spot
      G.root.visible = K.root.visible = false; fpose = STAND; fpos = { x: 0, y: -50, z: 0 }; kpose = STAND; kpos = { x: 2, y: -50, z: 0 };
      ball.position.set(0, 0.11, b === 12 ? 0 : C.z - 2); sun.intensity = b === 12 ? lerp(3.2, 1.0, u) : 3.2;
      if (b === 10) { cp = V(-6 + 2 * u, 1.2, C.z + 5); ct = V(0, 0.4, C.z - 2); hud.visible = true; drawHud([['TUESDAY', 'HE DIED'], ['CAUSE', 'NOT RELEASED', '#ffd23a']]); }
      else if (b === 11) { cp = V(-50, 22, 20 - 8 * u); ct = V(0, 0, -10); fov = 42; hud.visible = true; drawHud([['TENERIFE', 'HEARTBROKEN'], ['ANDORRA', 'DEVASTATED']]); }
      else { cp = V(0.9 - 0.3 * u, 0.5 + 0.1 * u, 2.4 - 0.8 * u); ct = V(0, 0.15, 0); fov = 30; }
    } }
  RG.applyPose(fpose, fpos); RK.applyPose(kpose, kpos); G.root.updateMatrixWorld(true); K.root.updateMatrixWorld(true);
  // contact: around the hit, slide the keeper so his right knee really meets the front of the forward's chest (it stopped short before)
  if (b === 0 || b === 5) { const w = smooth(KC - 0.15, KC - 0.02, KCUR) * (1 - smooth(KC + 0.3, KC + 0.55, KCUR));
    if (w > 0) { const chestF = wp(G.bones.chest).add(V(0, -0.05, -0.15)), knee = wp(K.bones.shinR); K.root.position.add(chestF.sub(knee).multiplyScalar(w)); K.root.updateMatrixWorld(true); } }
  xray(xr); impact.visible = xr && (nb === 3 || nb === 4); if (impact.visible) { const f = 0.5 + 0.5 * Math.sin(t * 6); impact.children.forEach(g => { g.material.opacity = 0.55 + 0.35 * f; }); impact.children[0].position.copy(wp(G.bones.chest).add(V(0, -0.05, -0.15))); impact.children[1].position.copy(wp(G.bones.head).add(V(0, 0.08, -0.1))); }
  // the explainers: x-ray close-ups of the chest (heart) and the head (brain), frozen at the moment of the hit
  heart.scale.copy(HEARTS); brain.position.copy(BRAINP); brain.scale.copy(BRAINS); brain.material.emissive.set(0x401018);
  if (XRB) { const U = lt / dur; ball.visible = false;
    if (nb === 4) { cp = V(C.x + 3.4, 1.45, C.z + 1.6); ct = V(C.x - 0.1, 1.3, C.z - 0.3); fov = 34; }
    else if (nb === 5 || nb === 6) { K.root.visible = false; const hp = wp(heart); cp = hp.clone().add(V(0.75, 0.12, -1.25)); ct = hp.clone().add(V(0, 0.08, 0)); fov = 30; near = 0.02;
      const vf = nb === 6 || U > 0.55; heart.scale.multiplyScalar(vf ? 1 + 0.025 * Math.sin(lt * 53) + 0.02 * Math.sin(lt * 31) : 1 + 0.09 * Math.max(0, Math.sin(lt * 7.5)) ** 6);
      hud.visible = true; drawHudECG('HEART', vf ? (nb === 6 ? 'NO PULSE' : 'OUT OF RHYTHM') : 'BEATING', vf ? '#ff6a5c' : '#2fbf71', vf ? 'vf' : 'beat', lt, nb === 6 ? 'NEEDS A SHOCK' : null); }
    else { K.root.visible = false; const bp = wp(brain); cp = bp.clone().add(V(0.95, 0.02, -0.25)); ct = bp.clone().add(V(0, -0.05, 0)); fov = 28; near = 0.02;
      if (nb === 7) { const j = Math.exp(-lt * 1.8) * Math.sin(lt * 9); brain.position.z += 0.012 * j; brain.position.y += 0.004 * j; }
      else { const sw = 1 + 0.12 * sm(clamp(U * 1.3, 0, 1)); brain.scale.multiplyScalar(sw); brain.material.emissive.setRGB(0.25 + 0.5 * sm(U), 0.05, 0.08); }
      hud.visible = true; drawHud([['BRAIN', nb === 7 ? 'HITS THE SKULL' : 'SWELLING', '#ff6a5c'], ['PRESSURE', nb === 7 ? 'NORMAL' : 'RISING', nb === 7 ? '#ffffff' : '#ff6a5c']]); }
    camera.position.copy(cp); camera.up.set(0, 1, 0); camera.lookAt(ct); camera.fov = fov; camera.near = near; camera.updateProjectionMatrix(); return { b: nb, focus: ct }; }
  if (nb === 12) { hud.visible = true; drawHud([['1. CALL', 'FOR HELP'], ['2. START', 'CPR', '#2fbf71']], 'GET THE AED'); }
  if (nb === 3 && xr) { hud.visible = true; drawHud([['HIT', 'CHEST', '#ff6a5c'], ['AND', 'HEAD', '#ff6a5c']]); }
  camera.position.copy(cp); camera.up.set(0, 1, 0); camera.lookAt(ct); camera.fov = fov; camera.near = near; camera.updateProjectionMatrix();
  return { b, focus: ct }; }
