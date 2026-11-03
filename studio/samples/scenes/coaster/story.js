// ------------------------------------------------------------------ story: one shot per line
const CREST = sNear(-136, 61.5, -46), LIFT0 = sNear(-30, 7, -46), HILL1 = sNear(-219, 55.5, -46), STATION = sNear(0, 2.2, -4);
const HMAX = 62.5, vAt = s => s < CREST ? 2.4 : Math.max(3, 0.94 * Math.sqrt(2 * 9.81 * Math.max(0, HMAX - frameAt(s).p.y)));
function runFrom(s0, dt) { let s = s0; for (let k = 0; k < dt * 60; k++) s += vAt(s) / 60; return s; }   // the train's head moving along the track for dt seconds
const SEATX = [-1.5, -0.5, 0.5, 1.5];
const LOCK = 0.416, OPEN = -0.35;
// the riders' sitting pose (from the sled Short), hands resting on the lap bar
const SITR = curl(curl({ thighR: [84, 0, 6], thighL: [84, 0, -6], shinR: [-70, 0, 0], shinL: [-70, 0, 0], footR: [-4, 0, 0], footL: [-4, 0, 0], spine1: [2, 0, 0], neck: [0, 0, 0], armR: A(42, 20, 0, 70), armL: A(42, 20, 0, 70) }, 'R', 55), 'L', 55);
const HANDSUP = curl(curl({ ...SITR, armR: A(150, 25, 0, 20), armL: A(150, 25, 0, 20), neck: [-10, 0, 0] }, 'R', 10), 'L', 10);
const TUG = curl(curl({ ...SITR, spine1: [-6, 0, 0], armR: A(30, 15, 0, 95), armL: A(30, 15, 0, 95), neck: [12, 0, 0] }, 'R', 80), 'L', 80);
const WORKER = curl(curl({ ...STAND, spine1: [-14, 0, 0], armR: A(70, 10, 0, 30), armL: A(10, 8, 0, 18) }, 'R', 30), 'L', 30);
let CARF = [];
function placeTrain(sHead, barAng = LOCK) { CARF = [];
  cars.forEach((car, c) => { const f = frameAt(sHead - c * CARL); car.position.copy(f.p).addScaledVector(f.up, 0.15); car.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(f.r, f.up, f.t.clone().negate())); car.updateMatrixWorld(true); CARF.push(f);
    bars[c].forEach(h => { h.rotation.x = barAng; h.userData.tip.rotation.x = -barAng; }); }); }
function seatRoot(c, k, lift = 0) { const car = cars[c], f = CARF[c], p = car.localToWorld(V(SEATX[k], 1.05 + lift, 0.2)); const yaw = Math.atan2(-f.t.x, -f.t.z) / D2R, tilt = Math.asin(clamp(f.t.y, -1, 1)) / D2R; return { x: p.x, y: p.y, z: p.z, yaw, tilt }; }
function onboard(c, lp, lt_) { const car = cars[c]; return [car.localToWorld(lp.clone()), car.localToWorld(lt_.clone())]; }
function shot(t) { const nb = beatAt(t), lt = t - B[nb], dur = DUR[nb], u = lt / dur;
  hud.visible = false; for (const a of [upArrow, downArrow, barArrow]) a.visible = false; glow.visible = false; ratchet.visible = false; closedSign.visible = false; tape.visible = false; belts.forEach(b => { b.visible = false; });
  lights.forEach(l => l.material.color.set(0x1c3a1c)); cars[0].userData.wallL.visible = true; cars[0].userData.fig0.visible = true; bars[0][0].visible = true; const ARR = []; SKYU.uSet.value = 0; scene.background.set(0x9cc7ef); scene.fog.color.set(0xb9d4ea); sun.intensity = 3.0; sun.color.set(0xffefd6); hemi.intensity = 0.95; xray(false); shirt(K, 0x3a3f46);
  let pov = 0, sH = STATION, bar = LOCK, gpose = SITR, kpose = SITR, glift = 0, kroot = null, cp, ct, up = V(0, 1, 0), fov = 40, near = 0.05;
  switch (nb) {
    case 0: { // hook: on board, facing the riders, over an airtime hill at speed (frame one already moving)
      sH = runFrom(HILL1 - 22, lt * 0.8); placeTrain(sH); const air = smooth(-14, -2, sH - HILL1) * (1 - smooth(4, 16, sH - HILL1)); glift = 0.05 * air; gpose = mixPose(SITR, HANDSUP, 0.4 * air);
      [cp, ct] = onboard(0, V(0, 2.05, -2.4), V(0, 1.4, 0.8)); up = V(0, 1, 0).applyQuaternion(cars[0].quaternion); fov = 52;
      hud.visible = true; drawHud([['SPEED', Math.round(vAt(sH) * 2.237) + ' MPH', '#ffd23a']]); break; }
    case 1: { // the ride: climbing the lift hill, seen from the ground
      sH = LIFT0 + 20 + lt * 2.4; placeTrain(sH); const f = frameAt(sH - 9); ct = f.p.clone(); cp = ct.clone().addScaledVector(f.r, 36).addScaledVector(f.t, 6 - 6 * u).add(V(0, -7, 0)); fov = 44;
      hud.visible = true; drawHud([['OCT 12, 2026', 'GOLIATH'], ['HEIGHT', '200 FT']]); break; }
    case 2: { // over the top and down the first drop
      // first person: his view from the front car over the top of the lift and down the first drop
      sH = runFrom(CREST - 2.5, lt); placeTrain(sH); const f = frameAt(sH); pov = 27; cp = V(0, 0, 0); ct = V(0, 0, -1);
      hud.visible = true; drawHud([['HEIGHT', Math.max(0, Math.round(f.p.y * 3.28)) + ' FT'], ['SPEED', Math.round(vAt(sH) * 2.237) + ' MPH', '#ffd23a']]); break; }
    case 3: { // what happened: the ride stopped, tape across the foreground (no one shown hurt)
      sH = STATION; placeTrain(sH); cp = V(-150 + 1.5 * u, 1.6, -16); ct = V(-188, 13, -48); fov = 46;
      { const d = ct.clone().sub(cp).setY(0).normalize(); tape.visible = true; tape.position.copy(cp).addScaledVector(d, 6).setY(1.0); tape.rotation.y = Math.atan2(-d.x, -d.z) + Math.PI / 2; }
      hud.visible = true; drawHud([['4 KIDS', 'HURT', '#ffd23a'], ['THE RIDER', 'DIED', '#ff6a5c']]); break; }
    case 4: case 5: case 6: { // x-ray: sitting normally (4), then airtime over a hill (5, 6): he floats, the seat drops away, the bar holds him
      if (nb === 5) { // first person again: floating over a camelback hill, the lap bar on his thighs
        sH = runFrom(HILL1 - 42, lt * 0.85); placeTrain(sH); const air = smooth(-12, -2, sH - HILL1) * (1 - smooth(6, 16, sH - HILL1)); glift = 0.05 * air; gpose = mixPose(SITR, HANDSUP, 0.5 * air); pov = 30;
        cp = V(0, 0, 0); ct = V(0, 0, -1); hud.visible = true; drawHud([['AIRTIME', air > 0.4 ? 'YOU FLOAT' : 'OVER THE HILL', '#ffd23a'], ['SPEED', Math.round(vAt(sH) * 2.237) + ' MPH']]); break; }
      const air = nb === 4 ? 0 : 1; sH = nb === 4 ? STATION : HILL1 - 1 + 2 * u; placeTrain(sH); xray(true); glift = 0.055 * air;
      cars[0].userData.wallL.visible = false; cars[0].userData.fig0.visible = false; bars[0][0].visible = false; [cp, ct] = onboard(0, V(-4.6, 2.0, 0.3), V(-0.5, 1.32, 0.3)); up = V(0, 1, 0).applyQuaternion(cars[0].quaternion); fov = 31;
      if (air > 0.05) { const car = cars[0]; ARR.push([upArrow, car.localToWorld(V(-1.0, 1.55 + 0.1 * air, 0.12)), 1.0 * air, false], [downArrow, car.localToWorld(V(-1.0, 0.75 - 0.08 * air, 0.25)), 0.9 * air, true]); }
      if (nb === 6) { glow.visible = true; glow.position.copy(cars[0].localToWorld(V(-0.5, 1.15, -0.1))); glow.material.opacity = 0.6 + 0.3 * Math.sin(t * 6); ARR.push([barArrow, cars[0].localToWorld(V(-1.0, 1.6, -0.1)), 0.9, true]); }
      hud.visible = true; drawHud(nb === 4 ? [['YOUR WEIGHT', 'ON THE SEAT', '#2fbf71']] : [['PUSHING YOU DOWN', 'NOTHING', '#ff6a5c'], ['HOLDING YOU IN', 'THE LAP BAR', '#2fbf71']]); break; }
    case 7: { // the lap bar, locked over the thighs (close-up)
      sH = STATION; placeTrain(sH, lerp(OPEN, LOCK, sm(clamp(u * 2, 0, 1)))); [cp, ct] = onboard(0, V(-1.9, 1.9, -1.1), V(-0.5, 1.2, -0.1)); fov = 34;
      if (u > 0.45) ARR.push([barArrow, cars[0].localToWorld(V(-0.5, 1.5, -0.1)), 0.9, true]);
      hud.visible = true; drawHud([['LAP BAR', u < 0.5 ? 'CLOSING' : 'LOCKED', u < 0.5 ? '#ffd23a' : '#2fbf71']]); break; }
    case 8: { // the station check: the lights say every bar is locked, the worker pulls on each bar
      sH = STATION; placeTrain(sH); lights.forEach(l => l.material.color.set(u > 0.15 ? 0x37ff6a : 0x1c3a1c)); shirt(K, 0xf2b81c);
      const car = cars[0]; const wp_ = car.localToWorld(V(-1.95, 0.0, -0.75)); kroot = { x: wp_.x - 0.35, y: 0.95 + 1.2, z: wp_.z, yaw: -90 }; kpose = mixPose(WORKER, mixPose(WORKER, STAND, 0.5), 0.5 + 0.5 * Math.sin(lt * 3));
      cp = V(-6.5, 2.6, -11 + 2 * u); ct = car.localToWorld(V(-1.0, 1.3, 0)); fov = 36;
      hud.visible = true; drawHud([['LIGHTS', u > 0.15 ? 'ALL LOCKED' : 'CHECKING', u > 0.15 ? '#2fbf71' : '#ffd23a']], u > 0.45 ? 'HAND CHECK' : null, '#2f7d4a'); break; }
    case 9: { // the investigation: a part, a check, or both (the lock's ratchet close-up)
      sH = STATION; placeTrain(sH); ratchet.visible = true; ratchet.userData.wheel.rotation.x = 0.12 * Math.sin(lt * 2); [cp, ct] = onboard(0, V(-1.55, 0.85, -1.25), V(-0.58, 0.55, -0.55)); fov = 32; near = 0.02;
      hud.visible = true; drawHud([['A PART', 'FAILED?', '#ffd23a'], ['A CHECK', 'MISSED?', '#ffd23a']]); break; }
    case 10: { // no cause yet; the ride is closed
      sH = STATION; placeTrain(sH, OPEN); closedSign.visible = true; cp = V(-1, 2.0, 22); ct = V(-3.6, 1.8, 13.4); fov = 38;
      hud.visible = true; drawHud([['CAUSE', 'NOT FOUND YET', '#ffd23a'], ['THE RIDE', 'CLOSED', '#ff6a5c']]); break; }
    case 11: { // seat belts being added
      sH = STATION; placeTrain(sH); belts.forEach(b => { b.visible = true; }); [cp, ct] = onboard(0, V(-1.5, 2.0, -1.4), V(-0.5, 1.1, 0.0)); fov = 34;
      hud.visible = true; drawHud([['ADDING', 'SEAT BELTS', '#2fbf71'], ['SHUT DOWN', '9 SIMILAR COASTERS']]); break; }
    case 12: { // if the bar feels loose: don't ride (he tugs on it)
      sH = STATION; placeTrain(sH); gpose = TUG; glift = 0.01 * Math.max(0, Math.sin(lt * 4)); [cp, ct] = onboard(0, V(-2.2, 2.0, -1.8), V(-0.5, 1.5, 0.1)); fov = 34;
      hud.visible = true; drawHud([['BAR FEELS', 'LOOSE?', '#ffd23a'], ['THEN', "DON'T RIDE", '#ff6a5c']], 'TELL A WORKER', '#2f7d4a'); break; }
    case 13: { // dusk: the empty train in the station
      sH = STATION; placeTrain(sH); SKYU.uSet.value = 1; scene.background.set(0xd98a62); scene.fog.color.set(0xc98a70); sun.color.set(0xff9a5a); sun.intensity = 1.2; hemi.intensity = 0.45; cp = V(32 - 3 * u, 4, 44); ct = V(-60, 22, -30); fov = 40; break; }
  }
  // riders: G (seat 2) and K (seat 3) in the front car; K stands on the platform as the worker in the station check
  RG.applyPose(gpose, seatRoot(0, 1, glift)); RK.applyPose(kroot ? kpose : SITR, kroot || seatRoot(0, 2, glift));
  G.root.visible = K.root.visible = nb !== 13 && nb !== 3 && nb !== 1 && nb !== 2 ? true : nb === 1 || nb === 2;   // far shots keep them (tiny); the empty station at dusk and the incident shot don't
  if (nb === 13 || nb === 3 || nb === 10) G.root.visible = K.root.visible = false;
  G.root.updateMatrixWorld(true); K.root.updateMatrixWorld(true);
  if (pov) { // eye point just in front of his face, looking down the track and down 'pov' degrees (the bar and his legs in view)
    const q = cars[0].quaternion, fw = V(0, 0, -1).applyQuaternion(q); up = V(0, 1, 0).applyQuaternion(q); const hd = wp(G.bones.head);
    cp = hd.clone().addScaledVector(up, 0.11).addScaledVector(fw, 0.1); ct = cp.clone().addScaledVector(fw, 10).addScaledVector(up, -10 * Math.tan(pov * D2R)); fov = 80; near = 0.06; }
  if (window.CAMO) { const o = window.CAMO, c = cars[0]; if (o.hide) { c.userData.fig0.visible = false; bars[0][0].visible = false; c.userData.wallL.visible = false; } cp = c.localToWorld(V(...o.p)); ct = c.localToWorld(V(...o.t)); fov = o.fov || 30; near = 0.03; up = V(0, 1, 0).applyQuaternion(c.quaternion); }   // debug camera for clip checks
  camera.position.copy(cp); camera.up.copy(up); camera.lookAt(ct); camera.fov = fov; camera.near = near; camera.updateProjectionMatrix();
  // arrows face the camera (billboards); 'down' ones flipped
  for (const [a, p, s, dn] of ARR) { a.visible = true; a.position.copy(p); a.quaternion.copy(camera.quaternion); if (dn) a.quaternion.multiply(new THREE.Quaternion().setFromAxisAngle(V(0, 0, 1), Math.PI)); a.scale.setScalar(s); }
  return { b: nb, focus: ct }; }
