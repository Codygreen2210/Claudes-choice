// ------------------------------------------------------------------ the film look, plus a speed pass: zoom blur, whip blur, and the 1954 newsreel grade
import { makeLook, loadIdle, idleAt, saccade } from '/look.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
const LOOKON = new URLSearchParams(location.search).get('look') !== '0';
const IDLE = LOOKON ? await loadIdle('/mocap/idle_77_02.json') : null;
const LOOK = LOOKON ? makeLook(THREE, renderer, scene, camera, W, H, { overlays: [gauge, darkPlane], noAO: [SKYG] }) : null;
const FX = new ShaderPass({ uniforms: { tDiffuse: { value: null }, uRad: { value: 0 }, uDir: { value: new THREE.Vector2() }, uGray: { value: 0 }, uT: { value: 0 }, uAsp: { value: W / H } },
  vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
  fragmentShader: `uniform sampler2D tDiffuse; uniform float uRad, uGray, uT, uAsp; uniform vec2 uDir; varying vec2 vUv;
    float hh(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
    void main(){ vec2 c = vUv - 0.5; vec4 acc = vec4(0.0); float wsum = 0.0;
      for (int i = 0; i < 14; i++) { float f = float(i) / 13.0, w = 1.0 - 0.5 * f; vec2 uv = vUv - c * uRad * f * smoothstep(0.05, 0.45, length(c * vec2(1.0, 1.0 / uAsp))) - uDir * f; acc += texture2D(tDiffuse, uv) * w; wsum += w; }
      vec4 col = acc / wsum;
      if (uGray > 0.0) { float l = dot(col.rgb, vec3(0.3, 0.59, 0.11)); vec3 g = vec3(l) * vec3(1.04, 1.0, 0.92);
        float gr = hh(vUv * 900.0 + uT * 37.0) - 0.5; g += gr * 0.09; g *= 1.0 - 0.55 * pow(length(c) * 1.25, 2.2); g *= 0.97 + 0.03 * sin(uT * 12.566);
        col.rgb = mix(col.rgb, g, uGray); }
      gl_FragColor = col; }` });
if (LOOK) LOOK.comp.insertPass(FX, LOOK.comp.passes.length - 1);
let LASTFOCUS = null, LASTRIM = true;

// ------------------------------------------------------------------ clipping: him vs the seat, the backrest, the footrest, and his own body
const SOLIDS = [];
const sbox = (name, obj, min, max) => SOLIDS.push({ name, obj, box: new THREE.Box3(min, max) });
sbox('seat pan', sled, V(-0.28, SEATTOP - 0.06, -0.23), V(0.28, SEATTOP - 0.005, 0.27)); sbox('backrest', sled, V(-0.28, SEATTOP, -0.275), V(0.28, SEATTOP + 0.78, -0.205));
sbox('headrest', sled, V(-0.15, SEATTOP + 0.77, -0.28), V(0.15, SEATTOP + 1.03, -0.2));
const BODYPTS = { handR: 0.025, handL: 0.025, farmR: 0.035, farmL: 0.035, uarmR: 0.045, uarmL: 0.045, head: 0.09, chest: 0.12, hips: 0.1, shinR: 0.05, shinL: 0.05, footR: 0.04, footL: 0.04, thighR: 0.06, thighL: 0.06 };
const BODYSURF = (() => { const keep = new Set(['hips', 'spine1', 'spine2', 'chest', 'neck', 'head', 'jaw', 'clavR', 'clavL', 'browR', 'browL']), out = [];
  for (const [mn, step] of [['skin_head', 10], ['shirt', 2], ['jeans', 5]]) { const m = G.meshes[mn]; if (!m) continue; const ga = m.geometry.attributes, names = m.skeleton.bones.map(b => b.name);
    for (let i = 0; i < ga.position.count; i += step) { let bw = -1, bi = 0; for (let k = 0; k < 4; k++) { const w = ga.skinWeight.getComponent(i, k); if (w > bw) { bw = w; bi = ga.skinIndex.getComponent(i, k); } }
      if (keep.has(names[bi])) out.push([m, i, names[bi]]); } }
  return out; })();
let SURF = null;
function surfNow() { const n = BODYSURF.length, P = new Float32Array(n * 3), N = new Float32Array(n * 3);
  for (let j = 0; j < n; j++) { const [m, i] = BODYSURF[j], ga = m.geometry.attributes;
    const a = V(ga.position.getX(i), ga.position.getY(i), ga.position.getZ(i)), b = V(0, 0, 0);
    m.applyBoneTransform(i, a); b.set(ga.position.getX(i) + ga.normal.getX(i) * 0.01, ga.position.getY(i) + ga.normal.getY(i) * 0.01, ga.position.getZ(i) + ga.normal.getZ(i) * 0.01);
    const sw = m.geometry.attributes.position; const save = [sw.getX(i), sw.getY(i), sw.getZ(i)]; sw.setXYZ(i, b.x, b.y, b.z); m.applyBoneTransform(i, b); sw.setXYZ(i, ...save);
    a.applyMatrix4(m.matrixWorld); b.applyMatrix4(m.matrixWorld); b.sub(a).normalize();
    P.set([a.x, a.y, a.z], j * 3); N.set([b.x, b.y, b.z], j * 3); }
  return { P, N, n }; }
function nearDepth(p, P, N, each) { const bd = [1e9, 1e9, 1e9, 1e9], bj = [-1, -1, -1, -1];
  each(j => { const dx = p.x - P[j * 3], dy = p.y - P[j * 3 + 1], dz = p.z - P[j * 3 + 2], d = dx * dx + dy * dy + dz * dz;
    if (d < bd[3]) { let q = 3; while (q > 0 && d < bd[q - 1]) { bd[q] = bd[q - 1]; bj[q] = bj[q - 1]; q--; } bd[q] = d; bj[q] = j; } });
  let sw = 0, sd = 0; for (let q = 0; q < 4; q++) { const j = bj[q]; if (j < 0) continue; const w = 1 / (Math.sqrt(bd[q]) + 0.004);
    sd += w * -((p.x - P[j * 3]) * N[j * 3] + (p.y - P[j * 3 + 1]) * N[j * 3 + 1] + (p.z - P[j * 3 + 2]) * N[j * 3 + 2]); sw += w; }
  return sw ? sd / sw : -1; }
function bodyDepth(p) { const { P, N, n } = SURF; return nearDepth(p, P, N, f => { for (let j = 0; j < n; j++) f(j); }); }
function clipScan() { const out = []; scene.updateMatrixWorld(true);
  if (!G.root.visible) return out;
  const pts = Object.entries(BODYPTS).map(([n, r]) => [n, n.startsWith('thigh') ? wp(G.bones[n]).lerp(wp(G.bones['shin' + n.slice(-1)]), 0.5) : wp(G.bones[n]), r]);
  for (const S of ['R', 'L']) for (const f of ['index', 'middle', 'pinky', 'thumb']) pts.push([f + ' tip ' + S, RG.tip(f, S), 0.008]);
  for (const [n, p, r] of pts) {
    for (const S of SOLIDS) { if (!S.obj.visible) continue; const q = p.clone().applyMatrix4(S.obj.matrixWorld.clone().invert()), bx = S.box;
      const dx = Math.min(q.x - bx.min.x, bx.max.x - q.x), dy = Math.min(q.y - bx.min.y, bx.max.y - q.y), dz = Math.min(q.z - bx.min.z, bx.max.z - q.z);
      const dd = Math.min(dx, dy, dz) + r; if (dx > -r && dy > -r && dz > -r && dd > 0.012) out.push({ what: 'him ' + n, into: S.name, depth: +(dd * 100).toFixed(1) }); }
    if (/^(hand|farm|index|middle|pinky|thumb)/.test(n)) { if (!SURF) SURF = surfNow();
      const dB = bodyDepth(p) + r; if (dB > 0.012) out.push({ what: 'him ' + n, into: 'own body', depth: +(dB * 100).toFixed(1) }); } }
  SURF = null;
  return out; }

// ------------------------------------------------------------------ straps, measured off his body at load
let CHESTOFF = 0.16, HIPOFF = 0.15;
function segTo(m, a, b, nrm) { const d = b.clone().sub(a), L = d.length(); m.position.copy(a).add(b).multiplyScalar(0.5); m.scale.set(1, L, 1);   // a flat band: its face toward nrm (no twist)
  const Y = d.normalize(); if (!nrm) { m.quaternion.setFromUnitVectors(V(0, 1, 0), Y); return; } const Z = nrm.clone().addScaledVector(Y, -nrm.dot(Y)).normalize(), X = new THREE.Vector3().crossVectors(Y, Z);
  m.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(X, Y, Z)); }
const STR = [0, 1, 2, 3, 4].map(() => { const m = new THREE.Mesh(new THREE.BoxGeometry(0.05, 1, 0.012), strapM); m.castShadow = true; scene.add(m); return m; });
const buckle = box(0.08, 0.07, 0.02, 0, 0, 0, mat(0xc8ccd2, 0.25, 0.9), 0.005, scene);
function placeStraps() { const q = wq(G.bones.chest), fw = V(0, 0, -1).applyQuaternion(q), up = V(0, 1, 0).applyQuaternion(q), lf = V(-1, 0, 0).applyQuaternion(q);
  const c = wp(G.bones.chest), h = wp(G.bones.hips), qh = wq(G.bones.hips), hf = V(0, 0, -1).applyQuaternion(qh), hl = V(-1, 0, 0).applyQuaternion(qh);
  const lap = h.clone().addScaledVector(hf, HIPOFF).add(V(0, -0.02, 0));
  for (const [i, s] of [[0, 1], [1, -1]]) { const sh = c.clone().addScaledVector(up, 0.2).addScaledVector(lf, 0.09 * s).addScaledVector(fw, -0.02);
    const fr = c.clone().addScaledVector(fw, CHESTOFF).addScaledVector(lf, 0.07 * s).addScaledVector(up, 0.02);
    segTo(STR[i * 2], sh, fr, fw.clone().add(up).normalize()); segTo(STR[i * 2 + 1], fr, lap.clone().addScaledVector(hl, 0.02 * s), fw); }
  segTo(STR[4], lap.clone().addScaledVector(hl, 0.2), lap.clone().addScaledVector(hl, -0.2), hf); STR[4].scale.x = 1.3;
  buckle.position.copy(lap).addScaledVector(hf, 0.012); buckle.quaternion.copy(qh); }

function SMOKE_B(p, i) { if (i < BSMOKE.n) BSMOKE.p.set([p.x * 1.15, p.y + 0.15, p.z - 0.2], i * 3); }
// ------------------------------------------------------------------ per-frame update
const DB = distAt(TB), FPSDT = 1 / FPS;
const STAGE_TRACK = [ground, ...POLES.map(p => p.p), sled, MTN, SKYG, SMOKE.m, ...POOLS, ...STR, buckle];
scene.children.filter(o => o.isMesh && o.geometry && o.geometry.parameters && o.geometry.parameters.depth === 700).forEach(o => STAGE_TRACK.push(o));   // the rails
function placeHUD(fov) { const d = 0.2, h = 2 * d * Math.tan(fov * D2R / 2), w = h * W / H, gw = 0.36 * w, gh = gw * 600 / 512;
  gauge.scale.set(gw / 0.066, gh / 0.0773, 1); gauge.position.set(w / 2 - gw / 2 - 0.035 * w, h / 2 - 0.2 * h - gh / 2, -d);
  const dd = 0.1, hh = 2 * dd * Math.tan(fov * D2R / 2); darkPlane.scale.set(hh * W / H * 1.02, hh * 1.02, 1); darkPlane.position.set(0, 0, -dd); }
function update(t, frame) {
  t = ((t % TOTAL) + TOTAL) % TOTAL;
  const g = guyAt(t), T = g.T, b = g.b;
  G.root.visible = g.show;
  if (g.show && IDLE) { const L = idleAt(IDLE, t, TOTAL); const k = 0.6;   // seated: only the chest, neck and head take the real-person life
    g.pose = addPose(g.pose, { spine2: L.chest.map(v => v * k), neck: L.neck.map(v => v * k), head: L.head.map(v => v * k) });
    const sc = saccade(t, TOTAL, hash1), lk = g.face.look || [0, 0]; g.face = { ...g.face, look: [lk[0] + sc[0] * 0.7, lk[1] + sc[1] * 0.7] }; }
  RG.applyPose(g.pose, g.root);
  G.root.updateMatrixWorld(true); delete RG.LAST.costR; delete RG.LAST.costL;
  RG.untwist(); G.face(g.face); G.root.updateMatrixWorld(true);
  const track = g.show || (b === 8);
  const inEye = b === 7, inBelt = b === 8 && g.lt > g.d * 0.55;
  for (const o of STAGE_TRACK) o.visible = !(inEye || inBelt);
  eyeSet.visible = inEye; beltSet.visible = inBelt;
  // the world slides past; one frame's travel smears the ground (in story time, so slow motion is crisp)
  const D = distAt(T), v = vAt(T), sl = SLICE[b], rate = sl ? (sl[1] - sl[0]) / g.d : 1, step = v * MPH * rate * FPSDT;
  GU.uD.value = D; GU.uStep.value = step;
  for (const P of POLES) { const z = ((P.k * 30 - D) % 480 + 480) % 480 - 200; P.p.position.set(P.x, 2.25, z); P.p.scale.set(1, 1, 1 + Math.min(step, 2.5) / 0.16); P.p.visible = P.p.visible && b !== 3 && P.p.position.distanceTo(camAt(t, g).pos) > 5; }   // a streak, capped (uncapped it stretched into a 9 m slab)
  for (let k = 0; k < POOLS.length; k++) { const z = DB + 1.0 + k * 15 - D; POOLS[k].position.set(0, 0, z); POOLS[k].visible = POOLS[k].visible && T > TB - 1.5 && z > -40 && z < 60; }
  // the rockets: they light at T = 0 (beat 9 counts down to it, so the loop lands on the ignition frame), burn 5 s, then die
  const ign = T < TBURN ? smooth(-0.15, 0.35, T) : 1 - smooth(TBURN, TBURN + 0.4, T);
  FLAMES.forEach((f, i) => { const fl = 1 + 0.18 * Math.sin(T * 90 + i * 1.7) + 0.1 * Math.sin(T * 211 + i * 3.1); f.visible = ign > 0.01 && !(inEye || inBelt); f.scale.set(1 + 0.3 * ign, 1 + 0.3 * ign, Math.max(0.01, ign * fl * (1.4 + 0.6 * Math.min(1, v / 200)))); });
  fireLight.intensity = 7 * ign;
  // the ignition burst: fire and smoke rolling out sideways and up from the back of the sled in the first second (same at T = 0 from either side of the loop)
  { let n = 0, m2 = 0; if (T > -0.05 && T < 1.6 && !(inEye || inBelt)) for (let j = 0; j < BURST.n; j++) { const a = hash1(j * 1.7) * Math.PI * 2, e2 = hash1(j * 2.9), tb = T + 0.05 - 0.25 * hash1(j * 4.3); if (tb < 0) continue;
      const r = (0.4 + 2.2 * e2) * (1 - Math.exp(-tb * 14)), back = D - distAt(Math.max(0, T - tb));
      const p = V(Math.cos(a) * r * 1.3, 0.7 + Math.abs(Math.sin(a)) * r * 0.75 + 1.2 * tb, -1.5 - 0.45 * r * hash1(j * 5.5) - back); if (p.y < 0.05) continue;
      if (tb < 0.7) { BURST.p.set([p.x, p.y, p.z], n * 3); n++; } SMOKE_B(p, m2++); } BURST.m.geometry.setDrawRange(0, n); BURST.m.geometry.attributes.position.needsUpdate = true;
    BURST.m.material.opacity = 0.95 * (1 - smooth(0.45, 1.0, T)); BSMOKE.m.geometry.setDrawRange(0, Math.min(m2, BSMOKE.n)); BSMOKE.m.geometry.attributes.position.needsUpdate = true; }
  // smoke: puffs left behind where the sled was when they came out of the nozzles
  { let n = 0; const per = Math.floor(SMOKE.n / NOZ.length);
    if (!(inEye || inBelt)) for (let i = 0; i < NOZ.length; i++) for (let j = 0; j < per; j++) { const age = j / per * 2.6 + hash1(i * 31 + j) * 0.01, Te = T - age;
      if (Te < 0 || Te > TBURN + 0.15) continue; const r = V(hash1(i * 7 + j * 1.3) - 0.5, hash1(i * 3 + j * 2.1) - 0.5, hash1(i * 5 + j * 0.7) - 0.5);
      const p = NOZ[i].clone().add(V(0, 0, -(D - distAt(Te)) - 2.5 * age)).add(r.multiplyScalar(0.25 + 1.4 * age)).add(V(0, 0.5 * age, 0)); if (p.z < -260) continue;
      SMOKE.p.set([p.x, p.y, p.z], n * 3); n++; }
    SMOKE.m.geometry.setDrawRange(0, n); SMOKE.m.geometry.attributes.position.needsUpdate = true; }
  // dust off the track: it stays where it was thrown up, so at speed it trails out behind as a long plume
  { let n = 0; if (!(inEye || inBelt) && T > 0.3) for (let j = 0; j < DUST.n; j++) { const age = 1.6 * (j / DUST.n) ** 2, Te = T - age;   // packed near the sled, thinning out far behind if (Te < 0.3) continue; const ve = vAt(Te); if (ve < 60) continue;
      const s = hash1(j * 2.3) < 0.5 ? -1 : 1, p = V(s * (0.75 + 9 * Math.sqrt(age) * hash1(j * 3.7)), 0.2 + 5 * Math.sqrt(age) * hash1(j * 5.9), -1.2 - (D - distAt(Te)) - 2 * age * hash1(j * 7.1));
      DUST.p.set([p.x, p.y, p.z], n * 3); n++; } DUST.m.geometry.setDrawRange(0, n); DUST.m.geometry.attributes.position.needsUpdate = true; }
  // water off the scoop: thrown up and out, left behind as the sled runs on (slow motion shows each drop)
  { let n = 0, m2 = 0; if (T > TB && !(inEye || inBelt) && b !== 8) for (let j = 0; j < SPRAY.n; j++) { const Te = TB + (T - TB) * (j / SPRAY.n), age = T - Te; if (Te > TB + TSTOP) continue;
      const vr = vAt(Te) * MPH, s = hash1(j * 1.9) < 0.5 ? -1 : 1, up = (0.05 + 0.1 * hash1(j * 3.3)) * vr, side = s * (0.03 + 0.09 * hash1(j * 5.1)) * vr;
      const p = V(side * age * 0.5 + s * 0.15, 0.12 + up * age - 4.9 * age * age, 0.95 - (D - distAt(Te)) + 0.02 * vr * age); if (p.y < 0) continue;
      SPRAY.p.set([p.x, p.y, p.z], n * 3); n++; if (j % 3 === 0 && m2 < MIST.n) { MIST.p.set([p.x * 1.2, p.y * 1.1, p.z], m2 * 3); m2++; } }
    SPRAY.m.geometry.setDrawRange(0, n); SPRAY.m.geometry.attributes.position.needsUpdate = true; MIST.m.geometry.setDrawRange(0, m2); MIST.m.geometry.attributes.position.needsUpdate = true; }
  // the harness rides his body
  if (g.show) placeStraps();
  // the eye: vessels burst red, then the dark closes in from the edges
  eyeLight.intensity = inEye ? 30 : 0;
  if (inEye) { veins.material.opacity = smooth(0.25, g.d * 0.55, g.lt); eyeball.rotation.y = 0.05 * Math.sin(g.lt * 9) * smooth(0.2, 0.6, g.lt); }
  darkPlane.visible = inEye; darkM2.uniforms.uR.value = 1.25 * (1 - smooth(g.d * 0.45, g.d * 0.95, g.lt)); darkM2.uniforms.uA.value = inEye ? smooth(g.d - 0.22, g.d - 0.02, g.lt) : 0;
  // today's seat belt: it slides across and the buckle clicks into the latch
  beltLight.intensity = inBelt ? 16 : 0;
  if (inBelt) { const u = (g.lt - g.d * 0.55) / (g.d * 0.45), k = smooth(0.05, 0.7, u), tp = V(-0.55, 0.75, 0.02).lerp(V(0.42, 0.08, 0.03), k);
    tongue.position.copy(tp).add(V(0, -0.05 * smooth(0.66, 0.74, u), 0)); tongue.rotation.z = -0.6 * (1 - k);
    segTo(belt, V(-0.75, 1.15, 0.0), tp.clone().add(V(0, 0.06, -0.005))); latch.position.y = -0.1 - 0.008 * Math.exp(-(((u - 0.72) / 0.03) ** 2)); }
  // the gauge (speed and g), on through the run and the countdown
  const gaugeOn = !(inEye || inBelt) && b !== 8 && b !== 3;
  gauge.visible = gaugeOn; if (gaugeOn) drawGauge(v, Math.abs(g.gz), T < 0 ? 'READY' : '');
  // lights: hard desert sun
  sun.visible = !(inEye || inBelt); sun.intensity = 2.5; sun.position.set(6, 12, 5); sun.target.position.set(0, 0, 0); sun.target.updateMatrixWorld();
  { const S = sun.shadow.camera; if (S.left !== -4) { S.left = -4; S.right = 4; S.top = 4; S.bottom = -4; S.updateProjectionMatrix(); } }
  hemi.intensity = 0.6; hemi.color.set(0xdfe8ff); hemi.groundColor.set(0xb8a890); lamp.intensity = 0; scene.environmentIntensity = 0.3; scene.background = null; scene.fog = null;
  // camera: shot, shake, whip, roll
  const C = camAt(t, g), sh = g.shake * 0.012;
  const wv = k => Math.sin(2 * Math.PI * Math.round(k * TOTAL / (2 * Math.PI)) * t / TOTAL);   // shake waves that repeat exactly over the loop (no jump at the seam)
  const pos = C.pos.clone().add(V(sh * wv(73), sh * wv(59), sh * 0.5 * wv(67)));
  camera.position.copy(pos); camera.up.set(0, 1, 0); camera.lookAt(C.tgt); camera.fov = C.fov; camera.updateProjectionMatrix();
  const wh = whipAt(t); camera.rotateY(-wh * 40 * D2R); camera.rotateZ((C.roll || 0) * D2R);
  LASTFOCUS = C.tgt.clone(); LASTRIM = g.show;
  SKYG.position.copy(camera.position); placeHUD(C.fov);
  // the speed pass: zoom blur while it's fast (never in slow motion), a sideways smear in a whip, gray for the 1954 newsreel
  FX.uniforms.uRad.value = SLOWMO[b] || inEye || inBelt ? 0 : 0.05 * Math.min(1, v / VMAX) * (b === 3 ? 0.3 : 1);
  FX.uniforms.uDir.value.set(wh * 0.07, 0); FX.uniforms.uGray.value = b === 8 && !inBelt ? 1 : 0; FX.uniforms.uT.value = t;
  return { beat: b, cut: false };
}
G.reset(); G.root.updateMatrixWorld(true);
// seat him: rest his seat on the seat pan and his feet on the footrest; find his chest and hip fronts for the straps
{ RG.applyPose(SITPOSE, { x: 0, y: 1.0, z: 0, yaw: YAW }); G.root.updateMatrixWorld(true); SURF = surfNow();
  let lo = 1e9; for (let j = 0; j < SURF.n; j++) { const [, , bn] = BODYSURF[j]; if (bn !== 'hips') continue; const y = SURF.P[j * 3 + 1], z = SURF.P[j * 3 + 2]; if (Math.abs(z) < 0.12) lo = Math.min(lo, y); }
  HIPY = 1.0 - (lo - SEATTOP) + 0.004;
  RG.applyPose(SITPOSE, { x: 0, y: HIPY, z: 0, yaw: YAW }); G.root.updateMatrixWorld(true); SURF = surfNow();
  const fy = Math.min(wp(G.bones.footR).y, wp(G.bones.footL).y) - 0.075, fz = (wp(G.bones.footR).z + wp(G.bones.footL).z) / 2;
  footrest.position.set(0, fy - 0.025, fz + 0.04);
  const q = wq(G.bones.chest), fw = V(0, 0, -1).applyQuaternion(q), up = V(0, 1, 0).applyQuaternion(q); const p0 = wp(G.bones.chest).addScaledVector(up, 0.02);
  let s = 0.05; while (s < 0.35 && bodyDepth(p0.clone().addScaledVector(fw, s)) > 0) s += 0.002; CHESTOFF = s + 0.008;
  const qh = wq(G.bones.hips), hf = V(0, 0, -1).applyQuaternion(qh), h0 = wp(G.bones.hips); s = 0.05; while (s < 0.35 && bodyDepth(h0.clone().addScaledVector(hf, s)) > 0) s += 0.002; HIPOFF = s + 0.01;
  window.SEATFIT = { HIPY, lo, fy, CHESTOFF, HIPOFF }; SURF = null; }
sbox('footrest', footrest, V(-0.31, -0.025, -0.15), V(0.31, 0.025, 0.15));

// ------------------------------------------------------------------ frame I/O (same contract as the other 3D Shorts)
const draw = () => LOOK ? LOOK.render(LASTFOCUS, { ao: true, dof: true, rim: LASTRIM }) : renderer.render(scene, camera);
const gl = renderer.getContext(), px = new Uint8Array(W * H * 4);
let CUTF = false, LASTB = 0, LASTF = -10;
function stepTo(i) { const t = i / FPS; const r = update(t, i); CUTF = r.cut; LASTB = r.beat; LASTF = i; }
for (const tt of [B[4] + 1, B[7] + 1, B[8] + DUR[8] * 0.3, B[8] + DUR[8] * 0.8, 0.1]) { update(tt, -50); draw(); }     // warm-up: compile every stage's shaders now
window.renderAll = async (f0, f1) => { for (let i = f0; i < f1; i++) { stepTo(i); draw(); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); await fetch('/frame', { method: 'POST', body: px }); } return 'ok'; };
window.renderAtT = t => { const i = Math.round(t * FPS); stepTo(i);
  if (window.CAM && window.CAM.hand) { const hp = RG.palmW(window.CAM.hand); window.CAM.tgt = hp.toArray(); window.CAM.pos = hp.clone().add(V(...window.CAM.off)).toArray(); }
  if (window.CAM) { camera.position.set(...window.CAM.pos); camera.up.set(0, 1, 0); camera.lookAt(...window.CAM.tgt); camera.fov = window.CAM.fov || 42; camera.updateProjectionMatrix(); SKYG.position.copy(camera.position); }
  draw(); return renderer.domElement.toDataURL('image/png'); };
window.rigReport = i => { stepTo(i); const t = i / FPS, iq = G.root.getWorldQuaternion(new THREE.Quaternion()).invert();
  const ang = { ...RG.LAST }; delete ang.costR; delete ang.costL;
  return { t, beat: LASTB, ang, hips: wp(G.bones.hips).toArray(), car: 0, show: G.root.visible, cut: CUTF,
    thumbs: ['R', 'L'].map(S => wp(G.bones['index1' + S]).sub(wp(G.bones['pinky1' + S])).applyQuaternion(iq).toArray()),
    forearms: ['R', 'L'].map(S => wp(G.bones['hand' + S]).sub(wp(G.bones['farm' + S])).normalize().applyQuaternion(iq).toArray()),
    cost: [null, null], clip: clipScan() }; };
window.dbg = { G, RG, wp, THREE, update, guyAt, renderer, scene, camera, F, Rt, UP, vAt, gAt, distAt };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS);
window.READY = true;
window.SCN = { THREE, scene, camera, G, stepTo, renderer, FPS, B, DUR, TOTAL };   // for studio/blender/export_shot.mjs
