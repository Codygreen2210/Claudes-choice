// ------------------------------------------------------------------ story: one shot per line
const G0 = 0.3, OM = -9.0;                                  // ground level at the pad; rotor turn rate on screen (rad/s, clockwise from above, slowed so the blades read)
for (const h of [HA, HB]) h.rotation.order = 'YXZ';
function setHeli(h, p, yaw, pitch = 0, roll = 0, ang = 0, blades = true) { h.visible = true; h.position.copy(p); h.rotation.set(pitch, yaw, roll); const U = h.userData;
  U.rot.rotation.y = ang; U.trot.rotation.x = ang * 5.3; U.blades.forEach(b => { b.visible = blades; b.userData.full.forEach(m => { m.visible = true; }); b.userData.stub.visible = false; }); U.disc.visible = blades; U.win.visible = true; }
// From the webcam video (USA Today still): both low over the snow, side-on to each other. A (red, cargo from Lukla) hovers about 2 m up,
// nose turned toward the camera-left; B (white with a blue tail, trekkers from base camp) hovers lower, side-on, and drifts sideways toward A
// until its blades reach A's cabin. tc < 0 = seconds before the strike. Far back in time each is still flying in (A from the south, B from the north).
const A_HOV = V(1.5, G0 + 2.0, -3.5), A_YAW = 2.5, B_YAW = -Math.PI / 2;
function stateA(tc) { if (tc < 0) { const s = -tc, far = Math.max(0, s - 3);
    return { p: V(A_HOV.x, A_HOV.y + 0.25 * Math.min(s, 3) + 7 * far + 0.6 * far * far, A_HOV.z + 22 * far + 2 * far * far), yaw: lerp(A_YAW, 0, smooth(3, 6, s)), pitch: 0.05 * Math.sin(s * 2.1), roll: 0.03 * Math.sin(s * 1.7), ang: OM * tc, bl: true }; }
  const roll = 80 * D2R * sm(clamp((tc - 0.65) / 0.8, 0, 1)), y = Math.max(G0 + 0.95 * Math.abs(Math.sin(roll)), A_HOV.y - 4.9 * tc * tc);
  return { p: V(A_HOV.x + 1.2 * sm(clamp(tc / 1.4, 0, 1)), y, A_HOV.z - 0.8 * sm(clamp(tc / 1.4, 0, 1))), yaw: A_YAW + 230 * D2R * sm(clamp(tc / 1.6, 0, 1)), pitch: 0, roll, ang: OM * Math.min(tc, 0.9), bl: tc < 0.9 }; }
function stateB(tc) { if (tc < 0) { const s = -tc, far = Math.max(0, s - 3.5);
    return { p: V(-2 - 3.0 * Math.min(s, 3.5) - 4 * far, G0 + 1.25 + 0.1 * Math.min(s, 3.5) + 7 * far + 0.6 * far * far, -22 * far - 2 * far * far), yaw: lerp(B_YAW, -Math.PI, smooth(3.5, 6.5, s)),
      pitch: -0.02, roll: -6 * D2R * (1 - smooth(2.5, 3.5, s)), ang: 3 * Math.PI / 4 + OM * tc, bl: true }; }
  const roll = -74 * D2R * sm(clamp((tc - 0.35) / 0.8, 0, 1)), y = Math.max(G0 + 0.9 * Math.abs(Math.sin(roll)), G0 + 1.25 - 4.9 * tc * tc);
  return { p: V(-2 + 1.6 * sm(clamp(tc / 1.1, 0, 1)), y, 0.6 * sm(clamp(tc / 1.1, 0, 1))), yaw: B_YAW - 35 * D2R * sm(clamp(tc / 1.2, 0, 1)), pitch: 0, roll, ang: 3 * Math.PI / 4, bl: false }; }
const hubOf = (st, h) => { const q = new THREE.Quaternion().setFromEuler(new THREE.Euler(st.pitch, st.yaw, st.roll, 'YXZ')); return st.p.clone().add(V(0, ROTOR_Y, 0).applyQuaternion(q)); };
// debris, set up once from the states above: B's blades break on A's cabin, A's glass and a few panels in their own paint, A's blades break when it rolls
{ const r = i => hash1(i * 13.37);
  const sb = stateB(0), hb = hubOf(sb); for (let k = 0; k < 3; k++) { const a = sb.ang + k * Math.PI * 2 / 3, q = new THREE.Quaternion().setFromEuler(new THREE.Euler(sb.pitch, sb.yaw, sb.roll, 'YXZ'));
    const dir = V(Math.cos(a), 0, -Math.sin(a)).applyQuaternion(q), tan = V(0, 1, 0).cross(dir);
    addDeb(new THREE.BoxGeometry(2.6, 0.05, 0.34), bitM[0], 0, hb.clone().addScaledVector(dir, 3.6), tan.multiplyScalar(13).add(dir.clone().multiplyScalar(5)).add(V(0, 3 + 2 * r(k), 0)), V(3 + 4 * r(k + 9), 9 + 6 * r(k + 3), 2));
    addDeb(new THREE.BoxGeometry(1.2, 0.05, 0.34), bitM[0], 0.02, hb.clone().addScaledVector(dir, 1.5), V(r(k + 30) - 0.5, 0.6, r(k + 40) - 0.5).multiplyScalar(5), V(5, 8, 3)); }
  const hit = V(1.1, G0 + 3.8, -3.1);
  for (let i = 0; i < 22; i++) addDeb(new THREE.BoxGeometry(0.08 + 0.14 * r(i), 0.015, 0.07 + 0.12 * r(i + 5)), glassBitM, 0.01 * r(i + 2), hit.clone().add(V((r(i + 7) - 0.5) * 1.0, (r(i + 8) - 0.5) * 0.6, (r(i + 9) - 0.5) * 1.0)), V(2 + 6 * r(i + 11), 1 + 4 * r(i + 12), -(1 + 5 * r(i + 13))), V(9 * r(i), 12 * r(i + 1), 7));
  for (let i = 0; i < 8; i++) addDeb(new THREE.BoxGeometry(0.2 + 0.3 * r(i + 50), 0.03, 0.15 + 0.25 * r(i + 52)), bitM[i % 2 ? 2 : 1], 0.02, hit.clone(), V(1 + 7 * r(i + 53), 2 + 4 * r(i + 54), -(r(i + 55)) * 7), V(6, 8, 5));
  const sa = stateA(0.9), ha = hubOf(sa); for (let k = 0; k < 3; k++) { const a = sa.ang + k * 2.1, dir = V(Math.cos(a), 0.3 * (r(k + 70) - 0.5), -Math.sin(a)).normalize();
    addDeb(new THREE.BoxGeometry(2.2, 0.05, 0.34), bitM[0], 0.9, ha.clone().addScaledVector(dir, 2.6), dir.clone().multiplyScalar(8).add(V(0, 4, 0)), V(4, 10, 3)); }
  // snow thrown up where each one hits the ground
  for (let i = 0; i < 12; i++) addPuff(0.42 + 0.04 * r(i + 80), V(-1.2 + (r(i + 81) - 0.5) * 6, G0 + 0.5, 0.2 + (r(i + 82) - 0.5) * 4), 3 + 3 * r(i + 83), 3.5);
  for (let i = 0; i < 16; i++) addPuff(0.65 + 0.08 * r(i + 90), V(2.6 + (r(i + 91) - 0.5) * 7, G0 + 0.5, -4.2 + (r(i + 92) - 0.5) * 6), 3.5 + 3.5 * r(i + 93), 4); }
function crash(tc, show = true) { const a = stateA(tc), b = stateB(tc);
  setHeli(HA, a.p, a.yaw, a.pitch, a.roll, a.ang, a.bl); setHeli(HB, b.p, b.yaw, b.pitch, b.roll, b.ang, tc < 0); 
  for (const d of DEB) { const dt = tc - d.t0; d.o.visible = show && dt >= 0; if (!d.o.visible) continue;
    const vy = d.v0.y, y0 = d.p0.y - G0 - 0.04, tl = (vy + Math.sqrt(vy * vy + 2 * 9.81 * Math.max(0, y0))) / 9.81, te = Math.min(dt, tl);
    d.o.position.copy(d.p0).addScaledVector(d.v0, te); d.o.position.y = d.p0.y + vy * te - 4.905 * te * te; if (dt > tl) { d.o.position.y = G0 + 0.04; d.o.position.addScaledVector(V(d.v0.x, 0, d.v0.z), 0.06 * (1 - Math.exp(-(dt - tl) * 4))); }
    d.o.rotation.set(d.spin.x * te, d.spin.y * te, d.spin.z * te); if (dt > tl) d.o.rotation.x = d.o.rotation.z = 0; }
  for (const p of PUFF) { const dt = tc - p.t0; p.s.visible = show && dt >= 0 && dt < p.life; if (!p.s.visible) continue; const k = dt / p.life;
    p.s.position.copy(p.p).add(V(0, 1.2 * k + 0.6, 0)); p.s.scale.setScalar(p.r * (0.4 + 1.1 * Math.sqrt(k))); p.s.material.opacity = 0.85 * (1 - k) * smooth(0, 0.08, dt); } }
function clearCrash() { for (const d of DEB) d.o.visible = false; for (const p of PUFF) p.s.visible = false; }
function shot(t) { const nb = beatAt(t), lt = t - B[nb], dur = DUR[nb], u = lt / dur;
  hud.visible = false; for (const o of [ringA, ringB, arrA, arrB, RANGE, pin, tape, tipTrail, pole, poleTop, bladePiece, ...RINGS, ...QS]) o.visible = false; arrB.scale.setScalar(1); HA.visible = HB.visible = false; clearCrash(); flagTop.visible = true;
  SKYU.uSet.value = 0; scene.background.set(0x9ec4ea); scene.fog.color.set(0xc4d6e8); scene.fog.near = 900; scene.fog.far = 7000; sun.color.set(0xfff2de); sun.intensity = 2.8; hemi.intensity = 0.6;
  let cp, ct, up = V(0, 1, 0), fov = 44, near = 0.1; camera.far = 9000;
  for (let i = 0; i < flags.length; i++) flags[i].rotation.z = 0.15 * Math.sin(t * 5 + i);
  sock.rotation.y = 0.15 * Math.sin(t * 2);
  const idle = (h, p, yaw = 0, pitch = 0) => setHeli(h, p, yaw, pitch, 0, OM * t, true);
  switch (nb) {
    case 0: { // hook: the webcam's view across the snow: B slides in from the left, side-on, into A hovering on the right; the strike at the end
      const tc = -2.6 + lt; crash(tc); cp = V(-1.5 + 0.6 * u, G0 + 2.0, 36); ct = V(-1.5, G0 + 3.0, -2); fov = 40;
      hud.visible = true; drawHud([['HEIGHT', Math.max(1, Math.round((stateB(Math.min(tc, 0)).p.y - G0) * 3.28)) + ' FT', '#ffd23a']], tc > 0 ? 'BLADES HIT' : null); break; }
    case 1: { // Pheriche from the air: the village, the pad, the peaks; both helicopters far off, still coming
      crash(-15 + lt, false); cp = V(240 - 50 * u, 120 - 15 * u, 300 - 70 * u); ct = V(10, 60, -400); fov = 50; near = 1;
      hud.visible = true; drawHud([['NOV 3, 2026', 'PHERICHE'], ['HEIGHT', '13,780 FT']]); break; }
    case 2: { // the two flights: A up the valley from Lukla with cargo, then B down from base camp with two trekkers
      const half = dur * 0.5; near = 0.5; fov = 46;
      if (lt < half) { const z = 1500 - 45 * lt, p = V(valleyX(z) + 10, 80, z); idle(HA, p, 0, -6 * D2R); cp = p.clone().add(V(-20 + 3 * u, 3, 11)); ct = p.clone().add(V(0, 1.2, -3));
        hud.visible = true; drawHud([['FROM', 'LUKLA'], ['CARRYING', 'CARGO', '#ff8a7a']]); }
      else { const z = -1500 + 45 * (lt - half), p = V(valleyX(z) - 10, 85, z); idle(HB, p, Math.PI, -6 * D2R); cp = p.clone().add(V(20 - 3 * u, 3, -11)); ct = p.clone().add(V(0, 1.2, 3));
        hud.visible = true; drawHud([['FROM', 'BASE CAMP'], ['CARRYING', '2 TREKKERS', '#7fb0ff']]); }
      break; }
    case 3: { // from straight above: same pad, same time, opposite sides; the rotor circles turn red when they overlap
      const tc = -3.6 + lt * 0.85; crash(tc, false); cp = V(0.01, 62, 1.5); ct = V(0, 0, 1.5); up = V(0, 0, -1); fov = 46; near = 1;
      const a = stateA(tc), b = stateB(tc), ha = hubOf(a), hb = hubOf(b), over = ha.distanceTo(hb) < 2 * ROTOR_R;
      for (const [r, h] of [[ringA, ha], [ringB, hb]]) { r.visible = true; r.position.copy(h); r.material.color.set(over ? 0xff3b2e : 0xffd23a); }
      arrB.visible = true; arrB.position.copy(stateB(tc).p).setY(G0 + 0.1).add(V(-4.5, 0, 3.2)); arrB.rotation.y = -Math.PI / 2; arrB.scale.setScalar(0.6); arrB.material.opacity = 0.85 * (1 - smooth(0.75, 0.95, u));
      hud.visible = true; drawHud([['ONE DRIFTED', 'SIDEWAYS', '#ffd23a']], over ? 'TOO CLOSE' : null); break; }
    case 4: { // slow motion: B's blades sweep into A's cabin a few feet off the ground; the blades break apart, both drop
      const tc = -0.75 + lt * 0.62; crash(tc); cp = V(10.5 - 1.0 * u, G0 + 3.6, 10.5 - 1.0 * u); ct = V(-0.3, G0 + 3.3, -1.8); fov = 46;
      hud.visible = true; drawHud([['OFF THE GROUND', 'ABOUT 8 FT', '#ffd23a'], ['SPEED', 'SLOWED DOWN']], tc > 0 ? 'BLADES HIT' : null); break; }
    case 5: { // after: both on their sides in the snow, the snow cloud settling (no people shown)
      const tc = 1.8 + lt; crash(tc); cp = V(20 + 5 * u, G0 + 7 + 1.5 * u, 19 + 4 * u); ct = V(0, G0 + 1.5, 1.5); fov = 40;
      hud.visible = true; drawHud([['KILLED', '1 TREKKER', '#ff6a5c'], ['HURT', '3 PEOPLE', '#ffd23a']], 'BOTH PILOTS HURT', '#7a4a1a'); break; }
    case 6: { // explainer: one helicopter idling on the pad, rotor turning
      idle(HA, V(0, G0, 0)); const a = -2.3 + 0.5 * u; cp = V(Math.sin(a) * 13, G0 + 1.4, Math.cos(a) * 13); ct = V(0, G0 + 2.6, 0); fov = 44;
      hud.visible = true; drawHud([['ROTOR', 'SPINNING', '#ffd23a']]); break; }
    case 7: { // from above: the rotor turning (shown slowed down)
      setHeli(HA, V(0, G0, 0), 0, 0, 0, -3.2 * t, true); HA.userData.disc.visible = true; cp = V(0.01, G0 + 17 - 2 * u, 0.6); ct = V(0, G0, 0.6); up = V(0, 0, -1); fov = 48;
      hud.visible = true; drawHud([['SPINS', 'NEARLY 400', '#ffd23a'], ['', 'TIMES A MINUTE']], 'SHOWN SLOWED', '#2a5a8a'); break; }
    case 8: { // the tips: nearly 500 mph (shown slowed); one touch on a pole: the outer blade snaps off and the pole top breaks away
      const th = 0.6, w = -2.6, thit = dur * 0.5, ang = th + w * (lt - thit), hit = lt >= thit, k = lt - thit;
      setHeli(HA, V(0, G0, 0), 0, 0, 0, ang, true); HA.userData.disc.visible = false;
      const hub = V(0, G0 + ROTOR_Y, 0), d0 = V(Math.cos(th), 0, -Math.sin(th)), vt = V(-Math.sin(th), 0, -Math.cos(th)).multiplyScalar(w);
      tipTrail.visible = true; tipTrail.position.copy(hub); tipTrail.rotation.y = ang + Math.PI * 0.9; tipTrail.material.opacity = hit ? 0.85 * (1 - smooth(0, 0.3, k)) : 0.85;
      const base = V(0, G0 - 0.3, 0).addScaledVector(d0, 4.6); pole.visible = poleTop.visible = true; pole.position.copy(base); poleTop.position.copy(base).add(V(0, 3.2, 0)); poleTop.rotation.set(0, 0, 0);
      if (hit) { const a0 = HA.userData.blades[0]; a0.userData.full.forEach(m => { m.visible = false; }); a0.userData.stub.visible = true;
        bladePiece.visible = true; const tk = Math.min(k, 1.2); bladePiece.position.copy(hub).addScaledVector(d0, 3.55).addScaledVector(vt.clone().multiplyScalar(0.9), tk).add(V(0, 1.2 * tk - 4.9 * tk * tk, 0)); bladePiece.position.y = Math.max(G0 + 0.05, bladePiece.position.y);
        bladePiece.rotation.set(0, th + 3.2 * w * tk, 2.5 * tk);
        const pk = Math.min(k, 1.0); poleTop.position.add(vt.clone().normalize().multiplyScalar(4.5 * pk)).add(V(0, 1.5 * pk - 4.9 * pk * pk, 0)); poleTop.position.y = Math.max(G0, poleTop.position.y); poleTop.rotation.set(-2.2 * pk, 0, 1.4 * pk); }
      cp = base.clone().add(V(-2.6 + 0.4 * u, 4.4, -7.5)); ct = base.clone().add(V(0.6, 3.0, 2.2)); fov = 50;
      hud.visible = true; drawHud([['BLADE TIPS', 'NEARLY 500 MPH', '#ffd23a'], ['', 'SHOWN SLOWED']], hit ? 'ONE TOUCH' : null); break; }
    case 9: { // the map from above: the nearest control tower's range never reaches Pheriche; the pilots call each other by radio
      crash(-12 + lt, false); RANGE.visible = true; pin.visible = true; pin.position.set(0, 150, 0); pin.scale.setScalar(260);
      cp = V(150, 9000, 1250); ct = V(0, 0, 1250); up = V(0, 0, -1); fov = 26; near = 20; camera.far = 25000; scene.fog.near = 20000; scene.fog.far = 30000;
      for (let i = 0; i < 4; i++) { const k = ((lt * 0.8 + i * 0.25) % 1); const s = RINGS[i]; s.visible = true; s.position.set(0, 160, 0); s.scale.setScalar(150 + 650 * k); s.material.opacity = 1 - k; }
      hud.visible = true; drawHud([['CONTROL TOWER', 'OUT OF RANGE', '#ff6a5c'], ['PILOTS TALK', 'BY RADIO', '#7fd3ff']]); break; }
    case 10: { // early report: a mix-up between the two pilots (radio rings, question marks)
      const tc = -3.8 + lt * 0.5; crash(tc, false); cp = V(48, 72, 0.5); ct = V(0, 12, 0.5); up = V(0, 0, -1); fov = 50; near = 0.5;
      const ha = hubOf(stateA(tc)), hb = hubOf(stateB(tc));
      for (let i = 0; i < 6; i++) { const k = ((lt * 1.1 + (i % 3) / 3) % 1), s = RINGS[i]; s.visible = true; s.position.copy(i < 3 ? ha : hb).add(V(0, 1, 0)); s.scale.setScalar(3 + 20 * k); s.material.opacity = 0.9 * (1 - k); }
      QS[0].visible = QS[1].visible = u > 0.3; QS[0].position.copy(ha).add(V(0, 6, 0)); QS[1].position.copy(hb).add(V(0, 6, 0)); for (const q of QS) q.scale.setScalar(7 * smooth(0.3, 0.42, u));
      hud.visible = true; drawHud([['EARLY REPORT', 'PILOT MIX-UP', '#ffd23a']], 'NOT FINAL', '#2a5a8a'); break; }
    case 11: { // still under investigation: tape across the foreground, the wrecks behind
      crash(5); cp = V(19 - 1.5 * u, G0 + 1.8, 15 - u); ct = V(0, G0 + 1.4, 1.5); fov = 38;
      { const d = ct.clone().sub(cp).setY(0).normalize(); tape.visible = true; tape.position.copy(cp).addScaledVector(d, 5).setY(G0 + 1.0); tape.rotation.y = Math.atan2(-d.x, -d.z); }
      hud.visible = true; drawHud([['CAUSE', 'UNDER', '#ffd23a'], ['', 'INVESTIGATION', '#ffd23a']]); break; }
    case 12: { // no roads: a helicopter lifting off the pad and heading down the valley; another one far off
      const k = sm(clamp(u * 1.2, 0, 1)); idle(HA, V(0, G0 + 7 * k * k, 9 * k * k), Math.PI, -7 * D2R * k);
      idle(HB, V(-40, 170, -700 + 140 * u), Math.PI, -5 * D2R); cp = V(-6, G0 + 2.4, 31); ct = V(0, G0 + 4.5, 0); fov = 46;
      hud.visible = true; drawHud([['ROADS', 'NONE', '#ff6a5c'], ['WAY IN OR OUT', 'HELICOPTER', '#2fbf71']]); break; }
    case 13: { // dusk over the empty pad and the peaks
      SKYU.uSet.value = 1; scene.background.set(0xd98a62); scene.fog.color.set(0xc9958a); sun.color.set(0xff9a5a); sun.intensity = 1.6; hemi.intensity = 0.5; scene.fog.near = 3000; scene.fog.far = 14000;
      cp = V(-8, G0 + 3, 30 - 3 * u); ct = V(20, 420, -3000); fov = 50; near = 0.5; flagTop.visible = false; break; }
  }
  SKY.position.copy(cp);
  camera.position.copy(cp); camera.up.copy(up); camera.lookAt(ct); camera.fov = fov; camera.near = near; camera.updateProjectionMatrix();
  return { b: nb, focus: nb === 9 ? V(0, 0, 1250) : nb === 13 ? V(0, G0, 0) : ct }; }
