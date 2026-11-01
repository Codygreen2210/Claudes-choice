// ------------------------------------------------------------------ the film look (AO, depth of field, rim light) and motion-capture life (look.js)
import { makeLook, loadIdle, idleAt, saccade } from '/look.js';
const LOOKON = new URLSearchParams(location.search).get('look') !== '0';
const IDLE = LOOKON ? await loadIdle('/mocap/idle_77_02.json') : null;
const LOOK = LOOKON ? makeLook(THREE, renderer, scene, camera, W, H, { overlays: [], noAO: [SKY] }) : null;
let LASTFOCUS = null, LASTRIM = true;   // the rim light only when he's in the shot (aimed across the sea it glared off the water)

// ------------------------------------------------------------------ clipping: him vs the dock's props, the dock top and his own body
const SOLIDS = [];
const sbox = (name, obj, min, max) => SOLIDS.push({ name, obj, box: new THREE.Box3(min, max) });
sbox('lantern', lantern, V(-0.09, 0, -0.09), V(0.09, 0.27, 0.09)); sbox('post', post, V(-0.08, -0.53, -0.08), V(0.08, 0.53, 0.08));
const BODYPTS = { handR: 0.025, handL: 0.025, farmR: 0.035, farmL: 0.035, uarmR: 0.045, uarmL: 0.045, head: 0.09, chest: 0.12, hips: 0.1, shinR: 0.05, shinL: 0.05, footR: 0.04, footL: 0.04, thighR: 0.06, thighL: 0.06 };
// his own body surface (head, neck, torso; not the arms): skinned sample points with outward normals, rebuilt each frame
const BODYSURF = (() => { const keep = new Set(['hips', 'spine1', 'spine2', 'chest', 'neck', 'head', 'jaw', 'clavR', 'clavL', 'browR', 'browL']), out = [];
  for (const [mn, step] of [['skin_head', 10], ['shirt', 2], ['jeans', 5]]) { const m = G.meshes[mn]; if (!m) continue; const ga = m.geometry.attributes, names = m.skeleton.bones.map(b => b.name);
    for (let i = 0; i < ga.position.count; i += step) { let bw = -1, bi = 0; for (let k = 0; k < 4; k++) { const w = ga.skinWeight.getComponent(i, k); if (w > bw) { bw = w; bi = ga.skinIndex.getComponent(i, k); } }
      if (keep.has(names[bi])) out.push([m, i]); } }
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
    if (p.y - r < -0.015) out.push({ what: 'him ' + n, into: 'dock', depth: +((-(p.y - r)) * 100).toFixed(1) });
    for (const S of SOLIDS) { if (!S.obj.visible) continue; const q = p.clone().applyMatrix4(S.obj.matrixWorld.clone().invert()), bx = S.box;
      const dx = Math.min(q.x - bx.min.x, bx.max.x - q.x), dy = Math.min(q.y - bx.min.y, bx.max.y - q.y), dz = Math.min(q.z - bx.min.z, bx.max.z - q.z);
      const dd = Math.min(dx, dy, dz) + r; if (dx > -r && dy > -r && dz > -r && dd > 0.012) out.push({ what: 'him ' + n, into: S.name, depth: +(dd * 100).toFixed(1) }); }
    if (/^(hand|farm|index|middle|pinky|thumb)/.test(n)) { if (!SURF) SURF = surfNow();
      const dB = bodyDepth(p) + r; if (dB > 0.012) out.push({ what: 'him ' + n, into: 'own body', depth: +(dB * 100).toFixed(1) }); } }
  SURF = null;
  return out; }

// ------------------------------------------------------------------ per-frame update
let LASTF = -10;
const RODDIR = RODTIP.clone().sub(ROD0).normalize();
const seaH = (x, z, t) => { let h = 0; for (const w of WAVES) h += w.a * Math.sin((w.d.x * x + w.d.z * z) * w.kx - t * w.w); return h; };   // same waves as the shader
const BLACK = new THREE.Color(0x000000), REEFBG = new THREE.Color(0x03101c), DOCKFOG = new THREE.FogExp2(0x0a1424, 0.012), REEFFOG = new THREE.FogExp2(0x062038, 0.11), BEACHFOG = new THREE.FogExp2(0x0a1220, 0.02);
const STAGES = { dock: [dock, sea, glit, fishLine, bobber, shore], space: [space], beach: [beach], reef: [reef] };
function update(t, frame) {
  t = ((t % TOTAL) + TOTAL) % TOTAL;
  const g = guyAt(t);
  G.root.visible = g.show;
  if (g.show && IDLE) { const L = idleAt(IDLE, t, TOTAL);          // a real person's small sways and head moves, on top of the story pose
    g.pose = addPose(g.pose, { spine1: L.back, spine2: L.chest, neck: L.neck, head: L.head }); g.root = { ...g.root, x: g.root.x + L.dx, z: g.root.z + L.dz, yaw: g.root.yaw + L.yaw };
    const sc = saccade(t, TOTAL, hash1), lk = g.face.look || [0, 0]; g.face = { ...g.face, look: [lk[0] + sc[0], lk[1] + sc[1]] }; }
  RG.applyPose(g.pose, g.root);
  const yaw = g.root.yaw, f = fwdOf(yaw), r = rightOf(yaw);
  for (const [S, sx] of [['R', 0.11], ['L', -0.11]]) {
    const fp = V(STANDP.x, 0, STANDP.z).addScaledVector(r, sx).addScaledVector(f, S === 'R' ? 0.02 : -0.02);
    fp.y = ANKLEH; RG.foot(S, fp, fp.clone().add(V(0, 0.45, 0)).addScaledVector(f, 1), yawQ(yaw)); }
  G.root.updateMatrixWorld(true);
  delete RG.LAST.costR; delete RG.LAST.costL;
  RG.untwist(); G.face(g.face); G.root.updateMatrixWorld(true);
  // which stage
  for (const [k, list] of Object.entries(STAGES)) for (const o of list) o.visible = g.stage === k;
  const dockOn = g.stage === 'dock';
  // the sky, the moon and its light
  skyMat.visible = g.stage === 'dock' || g.stage === 'beach'; STARS.uniforms.uT.value = 2 * Math.PI * 9 * t / TOTAL;
  STARS.uniforms.uK.value = g.stage === 'reef' ? 0 : g.stage === 'dock' ? 0.45 + 0.55 * (1 - g.moon) : g.stage === 'beach' ? 0.8 : 1;
  skyMoon.visible = dockOn && g.moon > 0.004; skyMoon.material.opacity = g.moon; moonGlow.visible = skyMoon.visible; moonGlow.material.opacity = 0.75 * g.moon;
  moonLight.intensity = dockOn ? 1.7 * g.moon : 0; moonLight.target.position.copy(STANDP); moonLight.position.copy(STANDP).addScaledVector(MD, 20); moonLight.target.updateMatrixWorld();
  sun.visible = false; lamp.intensity = 0; scene.environmentIntensity = 0.06;
  hemi.color.set(0x8aa0d0); hemi.groundColor.set(0x101418);
  hemi.intensity = g.stage === 'dock' ? (g.b === 2 ? 0.45 : 0.1 + 0.32 * g.moon) : g.stage === 'space' ? 0.16 : g.stage === 'beach' ? 0.3 : 0.25;
  lanternLight.intensity = dockOn ? 2.4 * g.lant : 0; lanternGlass.emissiveIntensity = 2.2 * g.lant;
  // the sea and the tide
  sea.position.y = g.wl; sea.material.userData.uT.value = t; beachSea.material.userData.uT.value = t; surf.material.userData.uT.value = t;
  for (const f of FOAM) { f.position.y = g.wl + 0.012 + seaH(f.position.x, f.position.z, t); }
  glit.material.opacity = g.moon; glit.visible = dockOn && g.moon > 0.004;
  // the bobber rides the waves; in beat 0 it jerks under once; the line runs from the rod tip
  { const bp = BOB.clone(); bp.y = g.wl + 0.02 + seaH(bp.x, bp.z, t);
    if (g.b === 0) bp.y -= 0.07 * Math.exp(-(((g.lt - 0.3) / 0.12) ** 2));
    bobber.position.copy(bp); bobber.rotation.z = 0.25 * Math.sin(2 * Math.PI * 12 * t / TOTAL);
    const tipBend = g.b === 0 ? 0.05 * Math.exp(-(((g.lt - 0.32) / 0.14) ** 2)) : 0;
    const tip = ROD0.clone().addScaledVector(RODDIR, RODLEN).add(V(0, -tipBend, 0)); rod.quaternion.setFromUnitVectors(UP, tip.clone().sub(ROD0).normalize());
    lineG.setFromPoints([tip, bp.clone().add(V(0, 0.04, 0))]); }
  // space
  if (g.stage === 'space') {
    earth.rotation.set(0, 0, -g.tilt * D2R); earthBall.rotation.y = g.spin * 0.35;
    axis.visible = g.b === 7 || g.b === 8; upRef.visible = g.b === 7; tiltTag.visible = g.b === 7;
    if (g.b === 7) { drawTilt(Math.round(g.tilt)); tiltTag.position.set(0, 1.62, 0.3); }
    // the moon (beat 1): there, a white pop, gone; its last light keeps travelling to Earth
    const vanish = 0.35, travel = 1.6;
    smoon.visible = g.b === 1 && g.pop < vanish; smoon.scale.setScalar(1 + 0.25 * smooth(vanish - 0.12, vanish, g.pop));
    popRing.visible = g.b === 1 && g.pop > vanish && g.pop < vanish + 0.7; { const k = (g.pop - vanish) / 0.7; popRing.scale.setScalar(1 + 3 * k); popRing.material.opacity = 0.9 * (1 - k); popRing.lookAt(camera.position); }
    { const src = SP.clone().add(SMOON), dst = SP.clone().add(SMOON.clone().normalize().multiplyScalar(1.02)); let n = 0;
      if (g.b === 1) for (let i = 0; i < PHOT.n; i++) { const e = vanish - 2.2 * i / PHOT.n, s = (g.phot - e) / travel; if (s < 0 || s > 1) continue;
        const p = src.clone().lerp(dst, s).add(V(0.025 * Math.sin(i * 2.7), 0.025 * Math.cos(i * 1.9), 0)); PHOT.p.set([p.x, p.y, p.z], n * 3); n++; }
      PHOT.m.geometry.setDrawRange(0, n); PHOT.m.geometry.attributes.position.needsUpdate = true; PHOT.m.visible = n > 0; }
    earthShine.intensity = g.b === 1 ? 2.2 * (1 - smooth(vanish + travel - 0.15, vanish + travel + 0.25, g.pop)) : 0; earthShine.position.copy(SMOON.clone().normalize().multiplyScalar(2.2));
    // the tide (beat 3): the ocean's bulge points at the Moon and the Sun; with the Moon gone it shrinks to the Sun's part
    tide.visible = g.b === 3; if (tide.visible) { const a = 0.2 * g.tideK + 0.02; tide.scale.set(1.02 + a, 1.02 - a * 0.3, 1.02 - a * 0.3); tide.quaternion.identity(); }   // drawn side to side across the tall frame, toward the Sun glow on the left
    { let n = 0; if (g.b === 3) { const sd = V(-1, 0, 0);
        for (let i = 0; i < PULL.n && n < Math.round(PULL.n * g.pull); i++) { const a = (t * 0.5 + hash1(i * 3.1)) % 1, side = i % 2 ? 1 : -1, sp = V(hash1(i * 5.2) - 0.5, hash1(i * 7.3) - 0.5, hash1(i * 1.7) - 0.5).multiplyScalar(0.9);
          const p = SP.clone().add(sd.clone().multiplyScalar(side * (1.05 + 0.5 * a))).add(sp.addScaledVector(sd, -sp.dot(sd)).multiplyScalar(1 - a)); PULL.p.set([p.x, p.y, p.z], n * 3); n++; } }
      PULL.m.geometry.setDrawRange(0, n); PULL.m.geometry.attributes.position.needsUpdate = true; PULL.m.visible = n > 0; }
    spaceSun.intensity = 4; sunBall.visible = false; sunGlow.visible = false; sunEdge.visible = g.b === 3; sunEdge.material.opacity = 0.9;
  } else { spaceSun.intensity = 0; PHOT.m.visible = false; PULL.m.visible = false; earthShine.intensity = 0; }
  // the beach: the hatchlings dig out, then crawl toward the street light (inland), away from the dark sea
  streetLight.intensity = g.stage === 'beach' ? 26 : 0;
  if (g.stage === 'beach') for (const T of TURT) { const a = g.lt - T.delay, up = smooth(0, 0.35, a), dir = V(Math.sin(T.ang * 1.1), 0, 1).normalize();
    const p = T.start.clone().addScaledVector(dir, Math.max(0, a - 0.3) * T.sp * 1.5); p.y = -0.045 + 0.05 * up + 0.004 * Math.abs(Math.sin(a * 9 + T.ph));
    T.g.position.copy(p); T.g.rotation.y = Math.atan2(dir.x, dir.z) + 0.15 * Math.sin(a * 9 + T.ph); T.g.visible = a > -0.05;
    for (const [pv, s, front] of T.fl) { const w = Math.sin(a * 9 + T.ph + (s > 0 ? 0 : Math.PI) + (front ? 0 : Math.PI / 2)); pv.rotation.y = (front ? 0.6 : 0.35) * s * w; pv.rotation.z = (front ? 0.25 : 0.1) * s * Math.max(0, w); } }
  // the reef: the egg bundles pulse at the coral tips but never let go; specks drift
  reefLight.intensity = g.stage === 'reef' ? 40 : 0;
  { let n = 0; if (g.stage === 'reef') { for (const E of EGGS) E.e.material.emissiveIntensity = 0.5 + 0.4 * Math.sin(g.lt * 3 + E.ph);
      for (let i = 0; i < SNOW.n; i++) { const p = RF.clone().add(V((hash1(i) - 0.5) * 6, ((hash1(i * 2.3) + 0.08 * g.lt) % 1) * 3, (hash1(i * 4.1) - 0.5) * 6 - 0.5)); SNOW.p.set([p.x, p.y, p.z], n * 3); n++; } }
    SNOW.m.geometry.setDrawRange(0, n); SNOW.m.geometry.attributes.position.needsUpdate = true; SNOW.m.visible = n > 0; }
  // fog and background
  scene.fog = g.stage === 'reef' ? REEFFOG : g.stage === 'dock' ? DOCKFOG : g.stage === 'beach' ? BEACHFOG : null;
  scene.background = g.stage === 'reef' ? REEFBG : BLACK;
  // camera; the sky rides with it
  const C = camAt(t, g); LASTFOCUS = C.tgt.clone(); LASTRIM = g.show && g.b !== 2; camera.position.copy(C.pos); camera.up.set(0, 1, 0); camera.lookAt(C.tgt); camera.fov = C.fov; camera.updateProjectionMatrix();
  SKY.position.copy(camera.position); SKY.visible = g.stage !== 'reef';
  { const h = V(MD.x, 0, MD.z).normalize(); glit.position.set(camera.position.x + h.x * 33, g.wl + 0.03, camera.position.z + h.z * 33); glit.rotation.set(-Math.PI / 2, 0, Math.atan2(-h.x, -h.z)); }
  return { beat: g.b, cut: g.cut };
}
G.reset(); G.root.updateMatrixWorld(true);
const ANKLEH = wp(G.bones.footR).y;

// ------------------------------------------------------------------ frame I/O (same contract as the other 3D Shorts)
const draw = () => LOOK ? LOOK.render(LASTFOCUS, { ao: true, dof: true, rim: LASTRIM }) : renderer.render(scene, camera);
const gl = renderer.getContext(), px = new Uint8Array(W * H * 4);
let CUTF = false, LASTB = 0;
function stepTo(i) { const t = i / FPS; const r = update(t, i); CUTF = r.cut; LASTB = r.beat; LASTF = i; }
for (const tt of [B[1] + 0.5, B[3] + 1, B[5] + 1, B[6] + 1, 0.1]) { update(tt, -50); draw(); }     // warm-up: compile every stage's shaders now
LASTF = -10;
window.renderAll = async (f0, f1) => { for (let i = f0; i < f1; i++) { stepTo(i); draw(); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); await fetch('/frame', { method: 'POST', body: px }); } return 'ok'; };
window.renderAtT = t => { const i = Math.round(t * FPS); stepTo(i);
  if (window.CAM && window.CAM.hand) { const hp = RG.palmW(window.CAM.hand); window.CAM.tgt = hp.toArray(); window.CAM.pos = hp.clone().add(V(...window.CAM.off)).toArray(); }
  if (window.CAM) { camera.position.set(...window.CAM.pos); camera.up.set(0, 1, 0); camera.lookAt(...window.CAM.tgt); camera.fov = window.CAM.fov || 42; camera.updateProjectionMatrix(); SKY.position.copy(camera.position); }
  draw(); return renderer.domElement.toDataURL('image/png'); };
window.rigReport = i => { stepTo(i); const t = i / FPS, iq = G.root.getWorldQuaternion(new THREE.Quaternion()).invert();
  const ang = { ...RG.LAST }; delete ang.costR; delete ang.costL;
  return { t, beat: LASTB, ang, hips: wp(G.bones.hips).toArray(), car: 0, show: G.root.visible, cut: CUTF,
    thumbs: ['R', 'L'].map(S => wp(G.bones['index1' + S]).sub(wp(G.bones['pinky1' + S])).applyQuaternion(iq).toArray()),
    forearms: ['R', 'L'].map(S => wp(G.bones['hand' + S]).sub(wp(G.bones['farm' + S])).normalize().applyQuaternion(iq).toArray()),
    cost: [null, null], clip: clipScan() }; };
window.dbg = { G, RG, wp, THREE, update, guyAt, renderer, scene, camera, F, Rt, UP };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS);
window.READY = true;
window.SCN = { THREE, scene, camera, G, stepTo, renderer, FPS, B, DUR, TOTAL };   // for studio/blender/export_shot.mjs
