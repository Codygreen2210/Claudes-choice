
// ------------------------------------------------------------------ the film look (AO, depth of field, rim light) and motion-capture life (look.js)
import { makeLook, loadIdle, idleAt, saccade } from '/look.js';
const LOOKON = new URLSearchParams(location.search).get('look') !== '0';
const IDLE = LOOKON ? await loadIdle('/mocap/idle_77_02.json') : null;
const LOOK = LOOKON ? makeLook(THREE, renderer, scene, camera, W, H, { overlays: [phone2] }) : null;
let LASTFOCUS = null, LASTXR = 0;

// ------------------------------------------------------------------ clipping: him vs the room, the counter, the floor and his own body
const SOLIDS = [];
const sbox = (name, obj, min, max) => SOLIDS.push({ name, obj, box: new THREE.Box3(min, max) });
sbox('couch', couch, V(-1.1, 0, -0.45), V(1.1, 0.98, 0.45)); sbox('counter', counter, V(-0.33, 0, -1.5), V(0.33, 0.95, 2.35));
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
// depth inside his body (> 0 = inside), from the 4 nearest skin samples weighted by nearness (one sample flips sign in creases)
function nearDepth(p, P, N, each) { const bd = [1e9, 1e9, 1e9, 1e9], bj = [-1, -1, -1, -1];
  each(j => { const dx = p.x - P[j * 3], dy = p.y - P[j * 3 + 1], dz = p.z - P[j * 3 + 2], d = dx * dx + dy * dy + dz * dz;
    if (d < bd[3]) { let q = 3; while (q > 0 && d < bd[q - 1]) { bd[q] = bd[q - 1]; bj[q] = bj[q - 1]; q--; } bd[q] = d; bj[q] = j; } });
  let sw = 0, sd = 0; for (let q = 0; q < 4; q++) { const j = bj[q]; if (j < 0) continue; const w = 1 / (Math.sqrt(bd[q]) + 0.004);
    sd += w * -((p.x - P[j * 3]) * N[j * 3] + (p.y - P[j * 3 + 1]) * N[j * 3 + 1] + (p.z - P[j * 3 + 2]) * N[j * 3 + 2]); sw += w; }
  return sw ? sd / sw : -1; }
function bodyDepth(p) { const { P, N, n } = SURF; return nearDepth(p, P, N, f => { for (let j = 0; j < n; j++) f(j); }); }
let BODYNOW = null, LASTH = [];
window.costParts = (i) => { stepTo(i); return LASTH.map(h => { const a = RG.LAST['arm' + h.S], f = RG.handFK(h.S, a); const cc = RG.contactCost(h)();
  return h.S + (h.free ? ' FREE' : '') + ' pos ' + (f.p.distanceTo(h.p) * 100).toFixed(1) + 'cm n ' + (h.n ? f.n.dot(h.n).toFixed(2) : '-') + ' w ' + (h.w ? f.w.dot(h.w).toFixed(2) : '-') + ' u ' + (h.u ? f.u.dot(h.u).toFixed(2) : '-') + ' contact ' + cc.toFixed(1) + ' extra ' + (h.extra ? h.extra(f).toFixed(1) : '-') + ' arm ' + a.map(v => v.toFixed(0)).join(','); }).join(' | '); };
const TIPS = ['index', 'middle', 'pinky', 'thumb'];
RG.contactCost = h => { const S = h.S, c0 = h.p, near = [];
  if (BODYNOW) { const { P, n } = BODYNOW; for (let j = 0; j < n; j++) { const dx = P[j * 3] - c0.x, dy = P[j * 3 + 1] - c0.y, dz = P[j * 3 + 2] - c0.z; if (dx * dx + dy * dy + dz * dz < 0.3 * 0.3) near.push(j); } }
  const NP = new Float32Array(near.length * 3), NN = new Float32Array(near.length * 3); near.forEach((j, k) => { for (let a = 0; a < 3; a++) { NP[k * 3 + a] = BODYNOW.P[j * 3 + a]; NN[k * 3 + a] = BODYNOW.N[j * 3 + a]; } });
  const solids = SOLIDS.filter(sd => sd.obj.visible && !/^couch/.test(sd.name)).map(sd => ({ inv: sd.obj.matrixWorld.clone().invert(), box: sd.box }));
  const CS = 0.025, cell = (x, y, z) => (Math.floor(x / CS) + 512) * 1048576 + (Math.floor(y / CS) + 512) * 1024 + (Math.floor(z / CS) + 512), GRID = new Map();
  for (let k = 0; k < near.length; k++) { const key = cell(NP[k * 3], NP[k * 3 + 1], NP[k * 3 + 2]); let a = GRID.get(key); if (!a) GRID.set(key, a = []); a.push(k); }
  const depthB = p => { if (!near.length) return -1; const cx = Math.floor(p.x / CS), cy = Math.floor(p.y / CS), cz = Math.floor(p.z / CS); let any = false;
    const cells = []; for (let i = -1; i <= 1; i++) for (let j = -1; j <= 1; j++) for (let l = -1; l <= 1; l++) { const a = GRID.get((cx + i + 512) * 1048576 + (cy + j + 512) * 1024 + (cz + l + 512)); if (a) { cells.push(a); any = true; } }
    return any ? nearDepth(p, NP, NN, f => { for (const a of cells) for (const k of a) f(k); }) : nearDepth(p, NP, NN, f => { for (let k = 0; k < near.length; k++) f(k); }); };
  const depthS = p => { let m = -1; for (const sd of solids) { const q = p.clone().applyMatrix4(sd.inv), b = sd.box; m = Math.max(m, Math.min(q.x - b.min.x, b.max.x - q.x, q.y - b.min.y, b.max.y - q.y, q.z - b.min.z, b.max.z - q.z)); } return m; };
  return () => { let c = 0; const pts = TIPS.map(f => [RG.tip(f, S), 0.008]); pts.push([RG.palmW(S), 0.004]); const el = wp(G.bones['farm' + S]);
    const soft = h.soft || 0; for (const [p, r] of pts) { const d = Math.max(depthB(p) - soft, depthS(p)) + r - 0.003; if (d > 0) c += (d / 0.002) ** 2; }
    { const d = depthB(el) + 0.03 - 0.003; if (d > 0) c += (d / 0.003) ** 2; }
    { const wr = wp(G.bones['hand' + S]), d = Math.max(depthB(wr) - soft, depthS(wr)) + 0.024 - 0.003; if (d > 0) c += (d / 0.002) ** 2; }
    return c; }; };
let STATE = null;
function clipScan() { const out = []; scene.updateMatrixWorld(true);
  if (!G.root.visible) return out;
  const pts = Object.entries(BODYPTS).map(([n, r]) => [n, n.startsWith('thigh') ? wp(G.bones[n]).lerp(wp(G.bones['shin' + n.slice(-1)]), 0.5) : wp(G.bones[n]), r]);
  for (const S of ['R', 'L']) for (const f of ['index', 'middle', 'pinky', 'thumb']) pts.push([f + ' tip ' + S, RG.tip(f, S), 0.008]);
  for (const [n, p, r] of pts) {
    if (p.y - r < -0.015) out.push({ what: 'him ' + n, into: 'floor', depth: +((-(p.y - r)) * 100).toFixed(1) });
    for (const S of SOLIDS) { if (!S.obj.visible) continue; const q = p.clone().applyMatrix4(S.obj.matrixWorld.clone().invert()), bx = S.box;
      const dx = Math.min(q.x - bx.min.x, bx.max.x - q.x), dy = Math.min(q.y - bx.min.y, bx.max.y - q.y), dz = Math.min(q.z - bx.min.z, bx.max.z - q.z);
      const dd = Math.min(dx, dy, dz) + r; if (dx > -r && dy > -r && dz > -r && dd > 0.012) out.push({ what: 'him ' + n, into: S.name, depth: +(dd * 100).toFixed(1) }); }
    if (/^(hand|farm|index|middle|pinky|thumb)/.test(n)) { if (!SURF) SURF = surfNow();
      const dB = bodyDepth(p) + r; if (dB > 0.012) out.push({ what: 'him ' + n, into: 'own body', depth: +(dB * 100).toFixed(1) }); } }
  SURF = null;
  return out; }

// ------------------------------------------------------------------ per-frame update
let LASTF = -10;
function propFromHand(obj, S, build) { const q = wq(G.bones['hand' + S]), h = RG.HANDREST[S];
  const n = h.n.clone().applyQuaternion(q), w = h.w.clone().applyQuaternion(q), u = h.u.clone().applyQuaternion(q); build(obj, RG.palmW(S), n, u, w); }
const basisQ = (x, y) => { const X = x.clone().normalize(), Y = y.clone().addScaledVector(X, -y.dot(X)).normalize(), Z = new THREE.Vector3().crossVectors(X, Y); return new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(X, Y, Z)); };
let PFLOOR = V(0.0, 0.0045, 0.75);                                  // where the dropped phone ends up (worked out at load from the fall)
let DROP0 = null, DROPQ = null;
// the dropped phone: slides off his open fingers (forward, a little up and out), tumbles, lands flat with a small bounce and slide
const FLATQ = new THREE.Quaternion().setFromEuler(new THREE.Euler(-Math.PI / 2, 0, 0.6));
function fallAt(s) { const v = F.clone().multiplyScalar(0.7).addScaledVector(Rt, -0.2).add(V(0, 0.2, 0)), yl = 0.0045;
  const tl = (v.y + Math.sqrt(v.y * v.y + 2 * 9.8 * (DROP0.y - yl))) / 9.8, sp = Math.min(s, tl);
  const p = DROP0.clone().addScaledVector(v, sp); p.y = DROP0.y + v.y * sp - 4.9 * sp * sp;
  const tum = q => DROPQ.clone().premultiply(new THREE.Quaternion().setFromAxisAngle(Rt, 7.5 * q));
  if (s < tl) return { p, q: tum(s) };
  const a = s - tl, vh = V(v.x, 0, v.z).normalize();
  p.addScaledVector(vh, 0.07 * (1 - Math.exp(-a * 9))); p.y = yl + 0.018 * Math.abs(Math.sin(a * 16)) * Math.exp(-a * 9);
  return { p, q: tum(tl).slerp(FLATQ, Math.min(1, a / 0.12)) }; }

function update(t, frame) {
  t = ((t % TOTAL) + TOTAL) % TOTAL;
  let g = guyAt(t); STATE = { b: g.b };
  scene.updateMatrixWorld(true);
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
  const list = [];
  if (g.show) { BODYNOW = surfNow(); const g2 = guyAt(t); g.hands = g2.hands; for (const h of g.hands) list.push(h); }
  for (const h of list) if (h.memAbs) h.memAbs += ':' + g.b;            // a hold never carries across a cut (chunks start each beat cold, so must a straight render)
  if (list.length) { RG.hands(list, 'b' + g.b, frame); LASTH = list; }
  for (const S of ['R', 'L']) if (!list.some(h => h.S === S)) delete RG.LAST['cost' + S];
  G.root.updateMatrixWorld(true); RG.untwist(); G.face(g.face); G.root.updateMatrixWorld(true);
  // the phone: in his left hand (across the palm), falling, or face up on the rug
  phone.visible = g.show || g.phoneMode === 'floor';
  const handPhone = () => propFromHand(phone, 'L', (o, pw, n, u, w) => { const ax = w.clone().multiplyScalar(Math.cos(PH.rot * D2R)).addScaledVector(u, Math.sin(PH.rot * D2R));
    o.quaternion.copy(basisQ(new THREE.Vector3().crossVectors(ax, n), ax)); o.position.copy(pw).addScaledVector(n, PH.n).addScaledVector(u, PH.u).addScaledVector(w, PH.w); });
  if (g.phoneMode === 'hand') { handPhone(); DROP0 = phone.position.clone(); DROPQ = phone.quaternion.clone(); }
  else if (g.phoneMode === 'fall') { if (!DROP0) { handPhone(); DROP0 = phone.position.clone(); DROPQ = phone.quaternion.clone(); }
    const f = fallAt(g.fall); phone.position.copy(f.p); phone.quaternion.copy(f.q); }
  else { phone.position.copy(PFLOOR); phone.quaternion.copy(FLATQ); }
  if (g.phoneScr !== phoneState) { drawPhone(g.phoneScr); phoneState = g.phoneScr; }
  // x-ray: the heart pounds; its bottom bulges; adrenaline pours up from the adrenal glands
  setXray(g.xr); const pz = Math.exp(-((((t * g.bpm / 60) % 1 - 0.05) / 0.07) ** 2));
  heart.scale.setScalar(1 + 0.12 * pz * g.pulse); heartM.emissiveIntensity = 0.7 + 0.9 * pz * g.pulse + 0.8 * g.adr * (0.6 + 0.4 * Math.sin(t * 20));
  xLV.scale.setScalar(Math.max(0.01, 0.9 * g.adr));
  adrM.emissiveIntensity = 0.6 + 1.2 * g.adr * (0.6 + 0.4 * Math.sin(t * 12));
  { const hp = wp(heart); let n = g.xr > 0.5 ? Math.round(ADRN.n * g.adr) : 0;
    for (let i = 0; i < n; i++) { const src = wp(ADR[i % 2]), a = ((t * (0.55 + 0.3 * hash1(i * 3.9)) + hash1(i * 1.3)) % 1);
      const p = src.clone().lerp(hp, a).add(V(vn1(t + i, 1) * 0.04, vn1(t + i, 2) * 0.03, vn1(t + i, 3) * 0.04).multiplyScalar(Math.sin(Math.PI * a))); ADRN.p.set([p.x, p.y, p.z], i * 3); }
    ADRN.m.geometry.setDrawRange(0, n); ADRN.m.geometry.attributes.position.needsUpdate = true; ADRN.m.visible = n > 0; }
  // the big heart
  heartSet.visible = g.bigShot; hsLight.intensity = g.bigShot ? 4 : 0;
  if (g.bigShot) { BIG.scale.setScalar(1 + 0.02 * pz * g.pulse); shapeLV(g.balloon, pz * g.pulse);
    pot.visible = g.pot > 0.01; pot.scale.setScalar(Math.max(0.01, g.pot)); potTag.visible = g.pot > 0.5; potTag.material.opacity = g.pot;
    let n = Math.round(FLOW.n * (g.b === 4 ? 0.5 : g.flow)); const c = BIG.localToWorld(V(0, 0.25, 0));
    for (let i = 0; i < n; i++) { const a = ((t * (g.b === 4 ? 0.12 : 0.45) * (0.6 + 0.4 * hash1(i * 2.1)) + hash1(i * 5.3)) % 1), ang = hash1(i * 7.7) * 6.283;
      const p = c.clone().add(V(Math.cos(ang) * 0.06, 0.05 + a * 0.6, Math.sin(ang) * 0.06)); FLOW.p.set([p.x, p.y, p.z], i * 3); }
    FLOW.m.geometry.setDrawRange(0, n); FLOW.m.geometry.attributes.position.needsUpdate = true; FLOW.m.visible = n > 0; } else FLOW.m.visible = false;
  // the phone insert, lower right, tipped a little
  phone2.visible = g.ins > 0.01; { const e = sm(g.ins); phone2.position.set(0.062, 0.055 + 0.3 * (1 - e), -0.4); phone2.rotation.set(-0.12, -0.18, 0.1); phone2.scale.setScalar(0.85); }
  // camera and light
  const C = camAt(t, g); LASTFOCUS = C.tgt.clone(); LASTXR = g.xr; camera.position.copy(C.pos); camera.up.set(0, 1, 0); camera.lookAt(C.tgt); camera.fov = C.fov; camera.updateProjectionMatrix();
  const dim = g.bigShot ? 0.4 : g.xr > 0.5 ? 0.35 : 1;
  sun.position.set(1.6, 3.4, 2.4).add(g.bigShot ? HS : V(0, 0, 0)); sun.target.position.copy(g.bigShot ? HS : V(0, 0, 0)); sun.target.updateMatrixWorld();
  sun.intensity = 2.6 * dim; hemi.intensity = 0.85 * dim; scene.environmentIntensity = 0.35 * dim; lamp.intensity = 6 * dim; scene.background = new THREE.Color(0xd9cbb6).multiplyScalar(dim);
  clockHands.s.rotation.z = -t * 6 * D2R; clockHands.m.rotation.z = -1.1; clockHands.h.rotation.z = -3.3;
  return { beat: g.b, cut: g.cut };
}
G.reset(); G.root.updateMatrixWorld(true);
const ANKLEH = wp(G.bones.footR).y;
// how far in front of the chest bone his shirt is, where the palm lies (the old guy: 0.153; other bodies differ)
{ SURF = surfNow(); const q = wq(G.bones.chest), fw = V(0, 0, -1).applyQuaternion(q), up = V(0, 1, 0).applyQuaternion(q), lf = V(-1, 0, 0).applyQuaternion(q);
  const p0 = wp(G.bones.chest).addScaledVector(up, 0.02).addScaledVector(lf, 0.05); let s = 0.05; while (s < 0.35 && bodyDepth(p0.clone().addScaledVector(fw, s)) > 0) s += 0.002;
  CHESTOFF = s + 0.005; window.CHESTS = s; SURF = null; }   // +5 mm: the old guy comes out at 0.153, as tuned

// ------------------------------------------------------------------ frame I/O (same contract as the other 3D Shorts)
const draw1 = () => LOOK ? LOOK.render(LASTFOCUS, { ao: LASTXR < 0.5, dof: LASTXR < 0.5 }) : renderer.render(scene, camera);
const draw = () => { if (XRNEW) { draw1(); XRNEW = false; } draw1(); };
const gl = renderer.getContext(), px = new Uint8Array(W * H * 4);
let CUTF = false, LASTB = 0;
function segStart(t) { return B[beatAt(t)]; }
function stepTo(i) { const t = i / FPS, tt = ((t % TOTAL) + TOTAL) % TOTAL;
  if (i !== LASTF + 1) for (let j = Math.ceil(segStart(tt) * FPS - 1e-6) + Math.floor(t / TOTAL) * Math.round(TOTAL * FPS); j < i; j++) update(j / FPS, j);
  const r = update(t, i); CUTF = r.cut; LASTB = r.beat; LASTF = i; }
for (let i = Math.ceil(B[7] * FPS); i < Math.round(TOTAL * FPS); i++) update(i / FPS, i);
LOOPSEED.L = RG.LAST.armL.slice();
for (const [b0, nb] of [[0, 1], [1, 2]]) { for (let i = Math.ceil(B[b0] * FPS); i < Math.ceil(B[b0 + 1] * FPS); i++) update(i / FPS, i); CSEED[nb] = RG.LAST.armR.slice();
  if (b0 === 0) { PFLOOR = fallAt(9).p; PFLOOR.y = 0.0045; DROP0 = null; } }   // where the phone came to rest: beats 1-2 show it there   // the hand on his chest carries on across the cuts
for (let i = Math.ceil(B[2] * FPS); i < Math.ceil(B[3] * FPS); i++) update(i / FPS, i); CHESTSEED = RG.LAST.armR.slice();   // beat 5's hand on his chest starts from where beat 2's ended
draw(); update(B[1] + 1.0, -50); draw(); update(B[3] + 1.0, -40); draw();     // warm-up: compile the x-ray and the big-heart shaders now
for (const k of Object.keys(RG.MEM)) delete RG.MEM[k]; LASTF = -10; DROP0 = null;
window.renderAll = async (f0, f1) => { for (let i = f0; i < f1; i++) { stepTo(i); draw(); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); await fetch('/frame', { method: 'POST', body: px }); } return 'ok'; };
window.renderAtT = t => { const i = Math.round(t * FPS); stepTo(i);
  if (window.CAM && window.CAM.hand) { const hp = RG.palmW(window.CAM.hand); window.CAM.tgt = hp.toArray(); window.CAM.pos = hp.clone().add(V(...window.CAM.off)).toArray(); }
  if (window.CAM) { camera.position.set(...window.CAM.pos); camera.up.set(0, 1, 0); camera.lookAt(...window.CAM.tgt); camera.fov = window.CAM.fov || 42; camera.updateProjectionMatrix(); }
  draw(); return renderer.domElement.toDataURL('image/png'); };
window.rigReport = i => { stepTo(i); const t = i / FPS, iq = G.root.getWorldQuaternion(new THREE.Quaternion()).invert();
  const ang = { ...RG.LAST }; delete ang.costR; delete ang.costL;
  return { t, beat: LASTB, ang, hips: wp(G.bones.hips).toArray(), car: 0, show: G.root.visible, cut: CUTF,
    thumbs: ['R', 'L'].map(S => wp(G.bones['index1' + S]).sub(wp(G.bones['pinky1' + S])).applyQuaternion(iq).toArray()),
    forearms: ['R', 'L'].map(S => wp(G.bones['hand' + S]).sub(wp(G.bones['farm' + S])).normalize().applyQuaternion(iq).toArray()),
    cost: [RG.LAST.costR ?? null, RG.LAST.costL ?? null], clip: clipScan() }; };
window.dbg = { G, RG, wp, THREE, LOOPSEED, update, guyAt, renderer, scene, camera, setBN: () => { BODYNOW = surfNow(); }, F, Rt, UP };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS);
window.READY = true;
window.SCN = { THREE, scene, camera, G, stepTo, renderer, FPS, B, DUR, TOTAL, phone, phone2, home };   // for studio/blender/export_shot.mjs
