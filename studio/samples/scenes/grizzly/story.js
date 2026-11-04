// ------------------------------------------------------------------ story: one shot per line (yaw 0 faces -z for the hikers and the bear)
const CALM = curl(curl({ ...STAND, armR: A(22, 28, 0, 25), armL: A(22, 28, 0, 25), neck: [4, 0, 0] }, 'R', 20), 'L', 20);
const SPRAYP = curl(curl({ ...STAND, spine1: [-4, 0, 0], armR: A(82, 6, 0, 8), armL: A(30, 20, 0, 60), neck: [2, 0, 0] }, 'R', 85), 'L', 30);
const PRONE = curl(curl({ ...STAND, thighR: [0, 0, 22], thighL: [0, 0, -22], neck: [20, 0, 0], armR: A(120, 85, 0, 160), armL: A(120, 85, 0, 160) }, 'R', 40), 'L', 40);
const LOOKP = curl(curl({ ...STAND, armR: A(8, 10, 0, 15), armL: A(8, 10, 0, 15), neck: [-4, 0, 0] }, 'R', 25), 'L', 25);
const ST = (x, z, yaw = 0) => ({ x, y: 0.95, z, yaw });   // root yaw is in DEGREES; 0 faces up the trail (-z), toward the bear
function clouds(nozzle, d, age0, on, fade = 1) { CLOUD.forEach((s, i) => { const age = age0 - i * 0.025; s.visible = on && age > 0 && age < 2.2; if (!s.visible) return; const k = Math.min(age, 0.7);
    s.position.copy(nozzle).addScaledVector(d, 9 * k - 5 * k * k).add(V(0.4 * (hash1(i) - 0.5) * age * 2, 0.25 * age + 0.3 * (hash1(i + 5) - 0.5) * age, 0.4 * (hash1(i + 9) - 0.5) * age * 2));
    s.scale.setScalar(0.1 + 1.25 * Math.sqrt(age)); s.material.opacity = 0.85 * (1 - age / 2.2) * fade; }); }
function shot(t) { const nb = beatAt(t), lt = t - B[nb], dur = DUR[nb], u = lt / dur;
  hud.visible = false; for (const o of [...ARS, XM, SIGN, TAPE, TRAP, PACKG, PACKK, SPRAYG, SPRAYK, ...CLOUD]) o.visible = false; BEAR.visible = false; G.root.visible = K.root.visible = false;
  SKYU.uSet.value = 0; scene.background.set(0xaabccb); scene.fog.color.set(0xb2c0cb); scene.fog.near = 60; scene.fog.far = 1500; sun.color.set(0xfff0dc); sun.intensity = 1.6; hemi.intensity = 1.1;
  let cp, ct, up = V(0, 1, 0), fov = 42, near = 0.05, gp = null, gr = null, kp = null, kr = null; const ARR = []; camera.far = 6000;
  switch (nb) {
    case 0: { // hook: a grizzly charging straight down the trail at the camera
      const z = -24 + 5.6 * lt; setBear(V(trailX(z), 0, z), Math.PI, lt * 9.5, 1, -0.1, 0.4); cp = V(0.35, 0.55, 0.8); ct = V(trailX(z), 0.95, z); fov = 40;
      hud.visible = true; drawHud([['GRIZZLY', 'CHARGING', '#ffd23a']]); break; }
    case 1: { // the Bella Coola valley from the air: river, forest, steep mountains
      cp = V(220 - 40 * u, 380 - 30 * u, 700 - 120 * u); ct = V(-260, 60, -700); fov = 50; near = 1; scene.fog.near = 2500; scene.fog.far = 9000;
      hud.visible = true; drawHud([['OCT 31, 2026', 'BELLA COOLA'], ['WHERE', 'B.C., CANADA']]); break; }
    case 2: { // the trail: a short walk from home, quiet, empty
      const z = 34 - 2.2 * lt; cp = V(trailX(z) + 0.15, 1.6, z); ct = V(trailX(z - 12), 1.3, z - 12); fov = 50;
      hud.visible = true; drawHud([['FROM HOME', '5 MINUTES', '#ffd23a']]); break; }
    case 3: { // closed: the sign, tape across the trail, a culvert trap set for the bear
      SIGN.visible = TAPE.visible = TRAP.visible = true; SIGN.position.set(trailX(20) + 1.6, 0, 20.4); SIGN.rotation.y = 0.15; TAPE.position.set(trailX(19.6), 1.0, 19.6); TRAP.position.set(trailX(13) + 4.2, 0, 13); TRAP.rotation.y = 0.5;
      cp = V(trailX(29) + 0.9 - 0.3 * u, 1.55, 29 - 1.2 * u); ct = V(trailX(17) + 1.6, 1.0, 17); fov = 44;
      hud.visible = true; drawHud([['THE BEAR', 'NOT CAUGHT YET', '#ff6a5c']], 'TRAPS SET', '#2a5a8a'); break; }
    case 4: { // a hiker on the trail; a grizzly ahead, up on its toes, looking at him
      gp = LOOKP; gr = ST(0, 0); setBear(V(trailX(-22), 0, -22), Math.PI, t * 1.5, 0.05, -0.25 + 0.1 * Math.sin(t * 2), 0, 0.6); cp = V(0.75, 1.8, 2.4); ct = V(trailX(-22) - 0.6, 1.0, -22); fov = 36;
      hud.visible = true; drawHud([['GRIZZLY', '70 FT AWAY', '#ffd23a']]); break; }
    case 5: { // don't run: it's as fast as a racehorse (it sprints across behind him; he stays put)
      gp = CALM; gr = ST(0, 0); const x = -30 + 15 * lt; setBear(V(x, 0, -9), -Math.PI / 2, lt * 11, 1, -0.05); cp = V(2.6, 1.55, 4.6); ct = V(0, 1.1, -5); fov = 50;
      hud.visible = true; drawHud([['TOP SPEED', 'ABOUT 35 MPH', '#ffd23a']], "DON'T RUN"); break; }
    case 6: { // the bluff charge: it rushes in, stops short, and swings away; he stands still, hands low, talking
      gp = CALM; gr = ST(0, 0); const k = sm(clamp(u / 0.6, 0, 1)), z = -22 + 16.5 * k, amp = 1 - smooth(0.45, 0.62, u), turn = smooth(0.7, 1, u);
      setBear(V(trailX(z) + 2.5 * turn, 0, z - 1.2 * turn), Math.PI + 1.6 * turn, lt * 9.5, Math.max(amp, 0.35 * turn), -0.1 + 0.25 * (1 - amp) * (1 - turn), 0.3 * (1 - amp)); cp = V(1.2, 1.6, 3.6); ct = V(0, 1.0, -5); fov = 48;
      hud.visible = true; drawHud([['MOST CHARGES', 'ARE BLUFFS', '#ffd23a']], 'STAND STILL', '#2f7d4a'); break; }
    case 7: { // bear spray: aimed at its face; the cloud stops it
      gp = SPRAYP; gr = ST(0, 0); const z = -13 + 6.5 * sm(clamp(u / 0.55, 0, 1)), stop = smooth(0.55, 0.8, u);
      setBear(V(trailX(z), 0, z), Math.PI + 0.5 * stop, lt * 6, 0.55 * (1 - stop), -0.1 + 0.35 * stop, 0.2, stop); cp = V(1.2, 1.65, 3.4); ct = V(0, 1.0, -5); fov = 46;
      hud.visible = true; drawHud([['BEAR SPRAY', 'AT ITS FACE', '#ff8a3a']]); break; }
    case 8: { // it turns and runs off into the trees; the cloud hangs
      gp = SPRAYP; gr = ST(0, 0); const k = sm(clamp(u / 0.35, 0, 1)), z = -6.5 - 22 * smooth(0.2, 1, u); setBear(V(trailX(z) + 2.5 * k, 0, z), Math.PI + Math.PI * k, lt * 9, 0.4 + 0.6 * k, 0.1); cp = V(-1.3, 1.8, 3.8); ct = V(0.3, 1.0, -8); fov = 48;
      hud.visible = true; drawHud([['STOPPED GRIZZLIES', '9 IN 10', '#2fbf71']], 'ONE BIG STUDY', '#2a5a8a'); break; }
    case 9: { // play dead: flat on the stomach, pack on, hands behind the neck; the bear stands over, sniffing (it never touches him on screen)
      gp = PRONE; gr = { x: 0, y: 0.17, z: 0, yaw: 0, tilt: -90 }; setBear(V(1.9, 0, -1.6), Math.PI / 2 + 0.6, t * 2, 0.05, 0.35, 0, 1); cp = V(5.6 - 0.4 * u, 3.3, 1.8 - 0.3 * u); ct = V(0.7, 0.5, -0.9); fov = 46;
      hud.visible = true; drawHud([['PLAY DEAD', 'ON YOUR STOMACH', '#ffd23a'], ['KEEP ON', 'PACK + HANDS ON NECK']]); break; }
    case 10: { // from above: legs spread so it can't flip him; still until it leaves
      gp = PRONE; gr = { x: 0, y: 0.17, z: 0, yaw: 0, tilt: -90 }; const z = -2.5 - 9 * smooth(0.15, 1, u); setBear(V(2.2, 0, z), 0, lt * 6, 0.6, 0.05); cp = V(0.01, 6.8, 0.7); ct = V(0, 0, 0.7); up = V(0, 0, -1); fov = 46;
      hud.visible = true; drawHud([['LEGS', 'SPREAD WIDE', '#2fbf71']], 'STAY STILL', '#2f7d4a'); break; }
    case 11: { // still attacking? fight back, hit the face (the bear alone, close up)
      setBear(V(0, 0, -4.2), Math.PI, t * 3, 0.1, -0.15 + 0.08 * Math.sin(t * 4), 0.5 + 0.3 * Math.sin(t * 5)); cp = V(1.1, 1.35, 0.6); ct = V(0, 0.95, -3.0); fov = 36;
      BEAR.updateMatrixWorld(true); const hp = V(0, 0, 0).applyMatrix4(BEAR.userData.head.matrixWorld); ARR.push([ARS[0], hp.clone().add(V(-0.75, 0.05, 0.2)), 0.8, -Math.PI / 2], [ARS[1], hp.clone().add(V(0.75, 0.05, 0.2)), 0.8, Math.PI / 2]);
      hud.visible = true; drawHud([['STILL ATTACKING?', 'FIGHT BACK', '#ff6a5c']], 'HIT THE FACE'); break; }
    case 12: { // walk in groups, make noise, spray on the hip
      gp = LOOKP; gr = ST(trailX(-1) - 0.45, -1, 180); kp = LOOKP; kr = ST(trailX(-1) + 0.5, -1.4, 180); cp = V(0.3, 1.55, 4.8 - 0.8 * u); ct = V(0, 1.25, -1); fov = 44;
      hud.visible = true; drawHud([['HIKE IN', 'GROUPS', '#2fbf71'], ['MAKE', 'NOISE', '#2fbf71']], 'SPRAY ON YOUR HIP', '#2f7d4a'); break; }
    case 13: { // dusk on the empty trail
      SKYU.uSet.value = 1; scene.background.set(0xc98a6a); scene.fog.color.set(0x9a7a72); sun.color.set(0xff9a5a); sun.intensity = 0.7; hemi.intensity = 0.55;
      cp = V(trailX(10) + 0.2, 1.2, 10 - 1.5 * u); ct = V(trailX(-20), 3.0, -20); fov = 48; break; }
  }
  if (gp) { G.root.visible = true; RG.applyPose(gp, gr); G.root.updateMatrixWorld(true); placePack(PACKG, G); }
  if (kp) { K.root.visible = true; RK.applyPose(kp, kr); K.root.updateMatrixWorld(true); placePack(PACKK, K); sprayOnHip(SPRAYK, K); }
  if (gp === SPRAYP) { const s = sprayInHand(SPRAYG, G); clouds(s.p, s.d, nb === 7 ? lt - 0.35 * dur : lt + DUR[7] * 0.65, true, nb === 8 ? 1 - u : 1); }
  else if (gp && nb !== 9 && nb !== 10) sprayOnHip(SPRAYG, G);
  SKY.position.copy(cp); camera.position.copy(cp); camera.up.copy(up); camera.lookAt(ct); camera.fov = fov; camera.near = near; camera.updateProjectionMatrix();
  for (const [a, p, s, rz] of ARR) { a.visible = true; a.position.copy(p); a.quaternion.copy(camera.quaternion).multiply(new THREE.Quaternion().setFromAxisAngle(V(0, 0, 1), rz)); a.scale.setScalar(s); }
  if (nb === 10) { for (const [a, s] of [[ARS[2], 1], [ARS[3], -1]]) { a.visible = true; const ft = wp(G.bones['foot' + (s > 0 ? 'R' : 'L')] || G.bones.hips); a.position.copy(ft).add(V(0.35 * s, 0.3, 0)); a.quaternion.copy(camera.quaternion).multiply(new THREE.Quaternion().setFromAxisAngle(V(0, 0, 1), -s * Math.PI / 2)); a.scale.setScalar(0.8); } }
  return { b: nb, focus: ct }; }
