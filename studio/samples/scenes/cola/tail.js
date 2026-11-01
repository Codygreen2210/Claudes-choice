
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
const ENV0 = new THREE.Color(0xd9cbb6);
function update(t, frame) {
  t = ((t % TOTAL) + TOTAL) % TOTAL;
  let g = guyAt(t); STATE = { b: g.b };
  scene.updateMatrixWorld(true);
  // him
  G.root.visible = g.show;
  RG.applyPose(g.pose, g.root);
  const yaw = g.root.yaw, f = fwdOf(yaw), r = rightOf(yaw);
  const ground = V(g.root.x, 0, g.root.z);
  for (const [S, sx] of [['R', 0.11], ['L', -0.11]]) {
    const fp = ground.clone().addScaledVector(r, sx).addScaledVector(f, S === 'R' ? 0.02 : -0.02);
    fp.y = ANKLEH; RG.foot(S, fp, fp.clone().add(V(0, 0.45, 0)).addScaledVector(f, 1), yawQ(yaw)); }
  G.root.updateMatrixWorld(true);
  // hands (targets read his body - the mouth - so build them now that this frame's pose is on)
  const list = [];
  if (g.show) { BODYNOW = surfNow(); const g2 = guyAt(t); g.hands = g2.hands; g.canC = g2.canC; g.canAx = g2.canAx; for (const h of g.hands) list.push(h); }
  for (const h of list) if (h.memAbs) h.memAbs += ':' + g.b;            // a hold never carries across a cut (chunks start each beat cold, so must a straight render)
  if (list.length) { RG.hands(list, 'b' + g.b, frame); LASTH = list; }
  for (const S of ['R', 'L']) if (!list.some(h => h.S === S)) delete RG.LAST['cost' + S];
  G.root.updateMatrixWorld(true); RG.untwist(); G.face(g.face); G.root.updateMatrixWorld(true);
  // the can: on the counter, in his hand (where the story puts it), or falling to the floor and rolling
  if (g.canMode === 'hand') { can.position.copy(g.canC); can.quaternion.copy(basisQ(new THREE.Vector3().crossVectors(g.canAx, Rt), g.canAx)).multiply(qAA(V(0, 1, 0), CANSPIN)); }
  else if (g.canMode === 'fall') { const s = g.fall, h0 = SHOW.y - 0.2, tf = Math.sqrt(2 * h0 / 9.8), p0 = SHOW.clone().add(V(0, -0.2, 0.04));
    if (s < tf) { can.position.copy(p0).add(V(0.15 * s, -4.9 * s * s, 0.05 * s)); can.quaternion.copy(qAA(Rt, -200 * s)); }
    else { const r = s - tf, roll = 1 - Math.exp(-r * 3); can.position.copy(p0).add(V(0.15 * tf + 0.18 * roll, -h0 + CANR, 0.05 * tf + 0.06 * roll)); can.quaternion.copy(qAA(V(0, 1, 0), 30)).multiply(qAA(V(0, 0, 1), 90)).multiply(qAA(V(0, 1, 0), 300 * roll)); }
    puddle.visible = s > tf; puddle.position.set(can.position.x + 0.04, 0.003, can.position.z); puddle.scale.setScalar(Math.max(0.01, 0.22 * smooth(tf, tf + 1.2, s))); }
  else { can.position.copy(CAN0); can.quaternion.copy(yawQ(CANYAW)); }
  if (g.canMode !== 'fall') puddle.visible = false;
    // fizz spraying out of the opening (beat 0)
  { let k = 0; if (g.fizzK > 0.01) { const top = can.localToWorld(V(0, CANH + 0.004, -0.008)), ax = V(0, 1, 0).applyQuaternion(can.quaternion);
      for (let i = 0; i < FIZZN; i++) { const a = ((t * (1.6 + hash1(i * 2.3)) + hash1(i * 5.1)) % 1), ang = hash1(i * 3.7) * 6.283;
        const sp = V(Math.cos(ang), 0, Math.sin(ang)).multiplyScalar(0.05 + 0.08 * hash1(i * 1.9));
        const p = top.clone().addScaledVector(ax, 0.16 * a * g.fizzK).addScaledVector(sp, a).add(V(0, -0.35 * a * a, 0));
        fizz.setMatrixAt(k++, _M.compose(p, _Q, _S.set(1, 1, 1).multiplyScalar((0.0025 + 0.003 * hash1(i)) * (1 - 0.5 * a) * g.fizzK))); } }
    fizz.count = k; fizz.instanceMatrix.needsUpdate = true; }
  // the sugar cubes drop onto the tower one by one (beat 1); the daily max line (beat 2)
  const cubesOn = g.b === 1 || g.b === 2;
  CUBES.forEach((c, i) => { const k = clamp(g.spoons * 10 - i, 0, 1), y = CUBE / 2 + i * CUBE; c.visible = cubesOn && k > 0.001;
    c.position.copy(TOWER).add(V(0.002 * Math.sin(i * 2.1), y + 0.12 * (1 - sm(k)) ** 2, 0.002 * Math.cos(i * 1.7))); c.rotation.y = 0.3 + 0.12 * Math.sin(i * 3.3); });
  limitBar.visible = limitTag.visible = cubesOn && g.limit > 0.01; limitM.opacity = g.limit * (0.75 + 0.25 * Math.sin(t * 12)); limitTag.material.opacity = g.limit;
  limitTag.position.copy(TOWER).add(V(0, 10 * CUBE + 0.03, 0)); cube10M.emissiveIntensity = 0.5 * g.limit * (0.6 + 0.4 * Math.sin(t * 12));
  if (g.b === 3 || g.b === 5) can.visible = false; else can.visible = true;
  // x-ray organs: sugar sparks in the blood, insulin from the pancreas, fat in the liver
  setXray(g.xr);
  { const c = wp(G.bones.spine2), up = V(0, 1, 0).applyQuaternion(wq(G.bones.spine2)), f2 = F, r2 = Rt; let n = Math.round(SUG.n * g.sugar);
    for (let i = 0; i < n; i++) { const a = ((t * (0.25 + 0.2 * hash1(i * 4.1)) + hash1(i * 2.7)) % 1), ang = hash1(i * 6.1) * 6.283, y = (hash1(i * 3.3) - 0.35) * 0.62 + 0.08 * Math.sin(6.283 * a);
      const rr = 0.09 * Math.sqrt(hash1(i * 8.3)) * (1 - 0.3 * Math.abs(y) / 0.4);
      const p = c.clone().addScaledVector(up, y).addScaledVector(r2, Math.cos(ang + a * 2) * rr * 1.5).addScaledVector(f2, Math.sin(ang + a * 2) * rr);
      SUG.p.set([p.x, p.y, p.z], i * 3); }
    SUG.m.geometry.setDrawRange(0, n); SUG.m.geometry.attributes.position.needsUpdate = true; SUG.m.visible = g.xr > 0.5;
    const pc = wp(panc); n = Math.round(INS.n * g.insulin);
    for (let i = 0; i < n; i++) { const a = ((t * (0.5 + 0.4 * hash1(i * 3.9)) + hash1(i * 1.3)) % 1), dir = V(hash1(i * 2.1) - 0.5, hash1(i * 5.7) - 0.3, hash1(i * 7.3) - 0.5).normalize();
      const p = pc.clone().addScaledVector(dir, 0.02 + 0.2 * a); INS.p.set([p.x, p.y, p.z], i * 3); }
    INS.m.geometry.setDrawRange(0, n); INS.m.geometry.attributes.position.needsUpdate = true; INS.m.visible = g.xr > 0.5;
    pancM.emissiveIntensity = 0.5 + 0.8 * g.insulin * (0.7 + 0.3 * Math.sin(t * 10));
    liverM.color.set(0x6a1a1a).lerp(new THREE.Color(0xb8902a), g.fat); liverM.emissive.set(0xc03a2a).lerp(new THREE.Color(0xffc030), g.fat); liver.scale.copy(LIVER0).multiplyScalar(1 + 0.18 * g.fat);
    fatDrops.forEach((m, i) => { const k = clamp(g.fat * 1.4 - hash1(i * 9.1) * 0.4, 0, 1); m.visible = k > 0.01; m.scale.setScalar(Math.max(0.01, k)); }); }
  // the tooth (beat 4): three sips wash cola over it; each one leaves more pits
  toothSet.visible = g.toothT >= 0; toothLight.intensity = g.toothT >= 0 ? 3 : 0;
  if (g.toothT >= 0) { const T0 = [0.15, 1.35, 2.55], lt = g.toothT; let cov = 0, done = 0;
    for (const s of T0) { const u = (lt - s) / 1.05; if (u >= 0 && u < 1) cov = u < 0.3 ? sm(u / 0.3) : u < 0.65 ? 1 : 1 - sm((u - 0.65) / 0.35); if (lt > s + 0.3) done += clamp((lt - s - 0.3) / 0.6, 0, 1); }
    wave.visible = cov > 0.005; wave.position.set(0, 0.05, 0); wave.scale.set(1, Math.max(0.001, 0.42 * cov), 1);      // a sip: the cola floods up over the teeth, then drains
    const pk = Math.round(done * 20) / 60; if (pk !== pitState) { drawPits(pk); pitState = pk; }
    let k = 0; if (cov > 0.2) for (let i = 0; i < BUBN; i++) { const a = ((lt * (0.8 + 0.7 * hash1(i * 2.2)) + hash1(i * 4.4)) % 1);
      bubs.setMatrixAt(k++, _M.compose(V((hash1(i * 6.6) - 0.5) * 1.4, 0.06 + a * 0.4 * cov, (hash1(i * 3.1) - 0.5) * 0.5 + 0.2), _Q, _S.set(1, 1, 1).multiplyScalar(0.006 + 0.01 * hash1(i)))); }
    bubs.count = k; bubs.instanceMatrix.needsUpdate = true; }
  // camera and room light (beat 6 goes to evening)
  const C = camAt(t, g); camera.position.copy(C.pos); camera.up.set(0, 1, 0); camera.lookAt(C.tgt); camera.fov = C.fov; camera.updateProjectionMatrix();
  sun.position.set(1.6, 3.4, 2.4).add(g.toothT >= 0 ? TOOTH : V(0, 0, 0)); sun.target.position.copy(g.toothT >= 0 ? TOOTH : V(0, 0, 0)); sun.target.updateMatrixWorld();
  const dim = g.toothT >= 0 ? 0.5 : 1; sun.intensity = 2.6 * dim; hemi.intensity = 0.85 * dim; scene.environmentIntensity = 0.35 * dim; scene.background = ENV0;
  return { beat: g.b, cut: g.cut };
}
G.reset(); G.root.updateMatrixWorld(true);
const ANKLEH = wp(G.bones.footR).y;

// ------------------------------------------------------------------ frame I/O (same contract as the other 3D Shorts)
const draw = () => { if (XRNEW) { renderer.render(scene, camera); XRNEW = false; } renderer.render(scene, camera); };
const gl = renderer.getContext(), px = new Uint8Array(W * H * 4);
let CUTF = false, LASTB = 0;
function segStart(t) { return B[beatAt(t)]; }   // where a hold starts cold
function stepTo(i) { const t = i / FPS, tt = ((t % TOTAL) + TOTAL) % TOTAL;
  if (i !== LASTF + 1) for (let j = Math.ceil(segStart(tt) * FPS - 1e-6) + Math.floor(t / TOTAL) * Math.round(TOTAL * FPS); j < i; j++) update(j / FPS, j);
  const r = update(t, i); CUTF = r.cut; LASTB = r.beat; LASTF = i; }
// the loop: beat 0's can hand starts where beat 7 ends
for (let i = Math.ceil(B[7] * FPS); i < Math.round(TOTAL * FPS); i++) update(i / FPS, i);
LOOPSEED.L = RG.LAST.armL.slice();
draw(); update(B[3] + 1.0, -50); draw(); update(B[4] + 0.5, -40); draw();     // warm-up: compile the x-ray and the tooth shaders now
for (const k of Object.keys(RG.MEM)) delete RG.MEM[k]; LASTF = -10;
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
window.dbg = { G, RG, wp, THREE, LOOPSEED, update, guyAt, renderer, scene, camera, setBN: () => { BODYNOW = surfNow(); }, F, Rt, UP, canHand, can };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS);
window.READY = true;
