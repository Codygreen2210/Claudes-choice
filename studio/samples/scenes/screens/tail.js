
// ------------------------------------------------------------------ the film look (AO, depth of field, rim light) and motion-capture life (look.js)
import { makeLook, loadIdle, idleAt, saccade } from '/look.js';
const LOOKON = new URLSearchParams(location.search).get('look') !== '0';
const IDLE = LOOKON ? await loadIdle('/mocap/idle_77_02.json') : null;
const LOOK = LOOKON ? makeLook(THREE, renderer, scene, camera, W, H, { overlays: [] }) : null;
let LASTFOCUS = null, LASTROOM = true;

// ------------------------------------------------------------------ clipping: him vs the room and his own body; his hand vs the phone
const SOLIDS = [];
const sbox = (name, obj, min, max) => SOLIDS.push({ name, obj, box: new THREE.Box3(min, max) });
sbox('couch', couch, V(-1.1, 0, -0.45), V(1.1, 0.98, 0.45)); sbox('counter', counter, V(-0.33, 0, -1.5), V(0.33, 0.95, 2.35)); sbox('console', home, V(2.79, 0, -0.75), V(3.24, 0.5, 0.75));
const BODYPTS = { handR: 0.025, handL: 0.025, farmR: 0.035, farmL: 0.035, uarmR: 0.045, uarmL: 0.045, head: 0.09, chest: 0.12, hips: 0.1, shinR: 0.05, shinL: 0.05, footR: 0.04, footL: 0.04, thighR: 0.06, thighL: 0.06 };
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
let BODYNOW = null, LASTH = [];
window.costParts = (i) => { stepTo(i); return LASTH.map(h => { const a = RG.LAST['arm' + h.S], f = RG.handFK(h.S, a); const cc = RG.contactCost(h)();
  return h.S + ' pos ' + (f.p.distanceTo(h.p) * 100).toFixed(1) + 'cm n ' + (h.n ? f.n.dot(h.n).toFixed(2) : '-') + ' u ' + (h.u ? f.u.dot(h.u).toFixed(2) : '-') + ' contact ' + cc.toFixed(1) + ' arm ' + a.map(v => v.toFixed(0)).join(','); }).join(' | '); };
const TIPS = ['index', 'middle', 'pinky', 'thumb'];
RG.contactCost = h => { const S = h.S, c0 = h.p, near = [];
  if (BODYNOW) { const { P, n } = BODYNOW; for (let j = 0; j < n; j++) { const dx = P[j * 3] - c0.x, dy = P[j * 3 + 1] - c0.y, dz = P[j * 3 + 2] - c0.z; if (dx * dx + dy * dy + dz * dz < 0.3 * 0.3) near.push(j); } }
  const NP = new Float32Array(near.length * 3), NN = new Float32Array(near.length * 3); near.forEach((j, k) => { for (let a = 0; a < 3; a++) { NP[k * 3 + a] = BODYNOW.P[j * 3 + a]; NN[k * 3 + a] = BODYNOW.N[j * 3 + a]; } });
  const depthB = p => near.length ? nearDepth(p, NP, NN, f => { for (let k = 0; k < near.length; k++) f(k); }) : -1;
  return () => { let c = 0; const pts = TIPS.map(f => [RG.tip(f, S), 0.008]); pts.push([RG.palmW(S), 0.004]); const el = wp(G.bones['farm' + S]);
    for (const [p, r] of pts) { const d = depthB(p) + r - 0.003; if (d > 0) c += (d / 0.002) ** 2; }
    { const d = depthB(el) + 0.03 - 0.003; if (d > 0) c += (d / 0.003) ** 2; }
    return c; }; };
let STATE = null;

// ------------------------------------------------------------------ the grip: his real hand skin vs the phone (fixes the thumb going through it)
const HANDV = (() => { const m = G.meshes.skin_head, ga = m.geometry.attributes, names = m.skeleton.bones.map(b => b.name), out = { all: [], tip: {}, palm: [] };
  const fing = ['thumb', 'index', 'middle', 'ring', 'pinky'];
  for (let i = 0; i < ga.position.count; i++) { let bw = -1, bi = 0; for (let k = 0; k < 4; k++) { const w = ga.skinWeight.getComponent(i, k); if (w > bw) { bw = w; bi = ga.skinIndex.getComponent(i, k); } }
    const nm = names[bi]; if (!/R$/.test(nm)) continue;
    const f = fing.find(x => nm.startsWith(x)); if (f) { out.all.push(i); if (/2R$/.test(nm)) (out.tip[f] = out.tip[f] || []).push(i); } else if (nm === 'handR') { out.all.push(i); out.palm.push(i); } }
  out.sub = out.all.filter((_, k) => k % 2 === 0); return out; })();
const _v = new THREE.Vector3(), _inv = new THREE.Matrix4();
function handSkinIn(list, toLocal) { const m = G.meshes.skin_head, ga = m.geometry.attributes, out = [];
  for (const i of list) { _v.set(ga.position.getX(i), ga.position.getY(i), ga.position.getZ(i)); m.applyBoneTransform(i, _v); _v.applyMatrix4(m.matrixWorld).applyMatrix4(toLocal); out.push(_v.clone()); } return out; }
const boxDepth = (q, b) => Math.min(q.x - b.min.x, b.max.x - q.x, q.y - b.min.y, b.max.y - q.y, q.z - b.min.z, b.max.z - q.z);   // > 0 inside
const boxDist = (q, b) => { const dx = Math.max(b.min.x - q.x, 0, q.x - b.max.x), dy = Math.max(b.min.y - q.y, 0, q.y - b.max.y), dz = Math.max(b.min.z - q.z, 0, q.z - b.max.z); return Math.hypot(dx, dy, dz); };
function setFingers(S, c, th, opp) { const pp = {}; curl(pp, S, c, th); if (opp) pp['thumb1' + S][0] = -opp;
  for (const [n, e] of Object.entries(pp)) G.bones[n].quaternion.copy(G.REST[n].q).multiply(qTmp.setFromEuler(eTmp.set(e[0] * D2R, e[1] * D2R, e[2] * D2R))); }
function phoneFromHand(o) { propFromHand(o, 'R', (ob, pw, n, u, w) => { const pq = qAA(w, PH.pitch || 0), n2 = n.clone().applyQuaternion(pq), u2 = u.clone().applyQuaternion(pq);   // pitch: leans its top back onto the fingertips
  const ax = w.clone().multiplyScalar(Math.cos(PH.rot * D2R)).addScaledVector(u2, Math.sin(PH.rot * D2R));
  ob.quaternion.copy(basisQ(new THREE.Vector3().crossVectors(ax, n2), ax)); ob.position.copy(pw).addScaledVector(n, PH.n).addScaledVector(u, PH.u).addScaledVector(w, PH.w); }); }
function gripScore(margin = 0.001) { phone.updateMatrixWorld(true); _inv.copy(phone.matrixWorld).invert(); G.root.updateMatrixWorld(true);
  const pts = handSkinIn(HANDV.sub, _inv); let pen = 0, worst = 0; for (const q of pts) { const d = boxDepth(q, PHONEBOX) + margin; if (d > 0) { pen += d * d; worst = Math.max(worst, d - margin); } }
  let touch = 0; const dmin = {};
  for (const f of ['thumb', 'index', 'middle', 'ring']) { const tp = handSkinIn(HANDV.tip[f] || [], _inv); let dm = 1; for (const q of tp) dm = Math.min(dm, boxDist(q, PHONEBOX)); dmin[f] = dm; touch += Math.max(0, dm - 0.002) ** 2; }
  // the fingers lie on the BACK of the phone (local z < 0): their pads, not their sides
  for (const f of ['index', 'middle', 'ring']) { const tp = handSkinIn(HANDV.tip[f] || [], _inv); let zb = 1; for (const q of tp) if (Math.abs(q.x) < 0.04 && Math.abs(q.y) < 0.08) zb = Math.min(zb, Math.abs(q.z - PHONEBOX.min.z)); touch += Math.max(0, zb - 0.003) ** 2; }
  { const pp = handSkinIn(HANDV.palm.filter((_, k) => k % 3 === 0), _inv); let dm = 1; for (const q of pp) dm = Math.min(dm, boxDist(q, PHONEBOX)); touch += Math.max(0, dm - 0.006) ** 2; }
  return { s: pen * 1e6 + touch * 1e4, pen, worst, touch, dmin }; }
function fitGrip() { G.reset(); RG.applyPose(STAND1, { x: STANDP.x, y: 0.95, z: STANDP.z, yaw: YAW }); RG.setArm('R', ARMPH); G.root.updateMatrixWorld(true);
  // 1. fingers nearly flat; the phone's back lies on the finger pads, centred on the middle finger, its bottom in the palm
  PH.c = 12; setFingers('R', PH.c, 30, 20); G.root.updateMatrixWorld(true);
  const q = wq(G.bones.handR), h = RG.HANDREST.R, n = h.n.clone().applyQuaternion(q), u = h.u.clone().applyQuaternion(q), w = h.w.clone().applyQuaternion(q), pw = RG.palmW('R');
  const m = G.meshes.skin_head, ga = m.geometry.attributes, names = m.skeleton.bones.map(b => b.name);
  const loc = i => { _v.set(ga.position.getX(i), ga.position.getY(i), ga.position.getZ(i)); m.applyBoneTransform(i, _v); _v.applyMatrix4(m.matrixWorld).sub(pw); return [_v.dot(n), _v.dot(u), _v.dot(w)]; };
  const dom = i => { let bw = -1, bi = 0; for (let k = 0; k < 4; k++) { const wt = ga.skinWeight.getComponent(i, k); if (wt > bw) { bw = wt; bi = ga.skinIndex.getComponent(i, k); } } return names[bi]; };
  const pads = [], mid = [], palm = [];
  for (const i of HANDV.all) { const nm = dom(i), L = loc(i); if (/^(index|middle|ring)[12]R$/.test(nm)) pads.push(L); if (/^middle[12]R$/.test(nm)) mid.push(L); if (nm === 'handR') palm.push(L); }
  const top = pads.reduce((a, L) => Math.max(a, L[0]), -1);                       // the finger pads' front surface (along the palm normal)
  const wC = mid.reduce((a, L) => a + L[2], 0) / mid.length, uTip = pads.reduce((a, L) => Math.max(a, L[1]), -1);
  PH.n = top + 0.0045 + 0.001; PH.w = wC; PH.u = Math.min(uTip - 0.06, 0.07);         // the phone's top a little past the fingertips, so the lens shows
  // lean it (pitch about the knuckle axis) and pull it in until it just clears the palm's heel: keep the lean that leaves the fingertips closest
  const n0 = PH.n; let bp = null;
  for (const pitch of [0, 4, 8, 12, 16, 20, 24, -4, -8, -12]) { PH.pitch = pitch; PH.n = n0 - 0.012; phoneFromHand(phone); let r = gripScore(), guard = 0;
    while (r.pen > 0 && guard++ < 40) { PH.n += 0.001; phoneFromHand(phone); r = gripScore(); }
    const gap = r.dmin.index + r.dmin.middle + r.dmin.ring; if (!bp || gap < bp.gap) bp = { pitch, n: PH.n, gap }; }
  PH.pitch = bp.pitch; PH.n = bp.n; phoneFromHand(phone);
  // 2. the thumb: round to the near edge, touching it, not inside
  let best = null;
  for (const th of [0, 10, 20, 30, 40, 50]) for (const opp of [0, 10, 20, 30, 40, 50, 60]) { setFingers('R', PH.c, th, opp); G.root.updateMatrixWorld(true);
    const rr = gripScore(); const s = rr.pen * 1e6 + Math.max(0, rr.dmin.thumb - 0.002) ** 2 * 1e4; if (!best || s < best.s) best = { s, th, opp, ...rr }; }
  PH.th = best.th; PH.opp = best.opp; window.GRIP = { ...best, pitch: PH.pitch, n: PH.n, u: PH.u, w: PH.w, c: PH.c, top, uTip, wC }; G.reset(); }

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
  if (phone.visible) { const r = gripScore(0); if (r.worst > 0.0015) out.push({ what: 'his right hand skin', into: 'phone', depth: +(r.worst * 100).toFixed(1) }); }
  return out; }

// ------------------------------------------------------------------ per-frame update
let LASTF = -10;
function propFromHand(obj, S, build) { const q = wq(G.bones['hand' + S]), h = RG.HANDREST[S];
  const n = h.n.clone().applyQuaternion(q), w = h.w.clone().applyQuaternion(q), u = h.u.clone().applyQuaternion(q); build(obj, RG.palmW(S), n, u, w); }
const basisQ = (x, y) => { const X = x.clone().normalize(), Y = y.clone().addScaledVector(X, -y.dot(X)).normalize(), Z = new THREE.Vector3().crossVectors(X, Y); return new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(X, Y, Z)); };
const ROWT = 1.6, onAt = s => ((s * 1.9) % 1 < 0.5 ? 1 : 0);        // beat 7: one sweep of the rows takes 1.6 s; the TV blinks ~3 times per sweep
const _c = new THREE.Color();
function update(t, frame) {
  t = ((t % TOTAL) + TOTAL) % TOTAL;
  let g = guyAt(t); STATE = { b: g.b };
  const room = g.set === 'room';
  home.visible = room; sensorSet.visible = g.set === 'sensor'; gridSet.visible = g.set === 'grid';
  scene.updateMatrixWorld(true);
  G.root.visible = g.show && room;
  if (G.root.visible && IDLE) { const L = idleAt(IDLE, t, TOTAL);
    g.pose = addPose(g.pose, { spine1: L.back, spine2: L.chest, neck: L.neck, head: L.head }); g.root = { ...g.root, x: g.root.x + L.dx, z: g.root.z + L.dz, yaw: g.root.yaw + L.yaw };
    const sc = saccade(t, TOTAL, hash1), lk = g.face.look || [0, 0]; g.face = { ...g.face, look: [lk[0] + sc[0], lk[1] + sc[1]] }; }
  RG.applyPose(g.pose, g.root);
  for (const [S, sx, off, lf] of [['R', 0.11, g.offR, g.liftR], ['L', -0.11, g.offL, g.liftL]]) {
    const fp = V(STANDP.x, 0, STANDP.z).addScaledVector(Rt, sx).addScaledVector(F, (S === 'R' ? 0.02 : -0.02) - off);
    fp.y = ANKLEH + lf; RG.foot(S, fp, fp.clone().add(V(0, 0.45, 0)).addScaledVector(F, 1), yawQ(YAW)); }
  G.root.updateMatrixWorld(true);
  const list = [];
  if (G.root.visible) { BODYNOW = surfNow(); const g2 = guyAt(t); g.hands = g2.hands; for (const h of g.hands) list.push(h); }
  for (const h of list) if (h.memAbs) h.memAbs += ':' + g.b;
  if (list.length) { RG.hands(list, 'b' + g.b, frame); LASTH = list; }
  for (const S of ['R', 'L']) if (!list.some(h => h.S === S)) delete RG.LAST['cost' + S];
  G.root.updateMatrixWorld(true); RG.untwist(); G.face(g.face); G.root.updateMatrixWorld(true);
  // the phone in his right hand; its screen shows what its camera sees
  phone.visible = G.root.visible;
  if (phone.visible) { phoneFromHand(phone); phone.updateMatrixWorld(true); phU.flip.value = V(0, 1, 0).applyQuaternion(phone.quaternion).y < 0 ? 1 : 0; }
  phU.t.value = t; phU.wave.value = g.wave; phU.bars.value = g.bars; phU.th.value = 0.5 + (g.tilt * 2.2) * D2R + 0.06 * Math.sin(t * 2 * Math.PI * Math.round(TOTAL / 6) / TOTAL);
  // the TV
  tvU.macro.value = g.macro; tvU.on.value = g.tvOn; tvU.bright.value = 1.25;
  tvLight.intensity = room ? (g.slowmo ? 2.2 * g.tvOn : 0.9) : 0; slowTag.visible = room && g.slowmo > 0;
  // the sensor: squares light up with the picture (beat 2); rows are read top to bottom while the TV blinks (beat 7)
  if (g.set === 'sensor') {
    const sweeps = g.scan >= 0 ? Math.floor(g.scan / ROWT) : 0, ph = g.scan >= 0 ? (g.scan % ROWT) / ROWT : -1;
    for (let i = 0; i < NS * NS; i++) { const r = Math.floor(i / NS), cc = i % NS;
      let k = 0; if (g.scan < 0) k = clamp((g.reveal * 1.25 - (r + cc) / (2 * NS)) / 0.12, 0, 1);
      else { const rr = (r + 0.5) / NS, tRead = (rr <= ph ? sweeps : sweeps - 1) * ROWT + rr * ROWT; k = tRead < 0 ? 0 : onAt(tRead); }
      glow.setColorAt(i, _c.copy(PICPX[i]).multiplyScalar(1.5 * k)); }
    glow.instanceColor.needsUpdate = true;
    scanBar.visible = g.scan >= 0; if (g.scan >= 0) scanBar.position.y = (NS * SITE) / 2 - ph * NS * SITE;
    miniTV.visible = onTag.visible = offTag.visible = g.scan >= 0; const on = onAt(Math.max(0, g.scan)); miniU.on.value = on; onTag.visible = g.scan >= 0 && on > 0.5; offTag.visible = g.scan >= 0 && on < 0.5;
    const n = g.rays ? RAYS.n : 0, cz = SC.clone().add(SS);
    for (let i = 0; i < n; i++) { const a = (t * (0.9 + 0.4 * hash1(i * 3.3)) + hash1(i * 7.1)) % 1, j = Math.floor(hash1(i * 1.7) * NS * NS), sp = sitePos(j);
      RAYS.p.set([cz.x + sp.x * (0.4 + 0.6 * a), cz.y + sp.y * (0.4 + 0.6 * a), cz.z + 0.9 * (1 - a) + 0.01], i * 3); }
    RAYS.m.geometry.setDrawRange(0, n); RAYS.m.geometry.attributes.position.needsUpdate = true; RAYS.m.visible = n > 0;
  } else RAYS.m.visible = false;
  // the two grids
  if (g.set === 'grid') { grU.t.value = t; grU.th.value = g.gth * D2R; grU.slide.value = g.gslide; grU.bayer.value = g.gbayer;
    const Dm = (GW / grU.N.value) / (2 * Math.sin(Math.max(1, g.gth) * D2R / 2));
    brightRing.position.set(0, 1.2, 0.03); brightTag.position.set(0, 1.2 + 0.15, 0.05); darkRing.position.set(Dm / 2, 1.2, 0.03); darkTag.position.set(Dm / 2 - 0.05, 1.2 - 0.15, 0.05);   // in line at the centre; half a square off at D/2
    for (const [o, k] of [[brightTag, g.tagB], [brightRing, g.tagB], [darkTag, g.tagD], [darkRing, g.tagD]]) { o.material.opacity = k; o.visible = k > 0.01; } }
  // camera and light
  const C = camAt(t, g); camera.position.copy(C.pos); camera.up.set(0, 1, 0); camera.lookAt(C.tgt); camera.fov = C.fov; camera.near = C.near ?? 0.03; camera.updateProjectionMatrix();
  LASTFOCUS = C.focus === 'phone' ? phone.getWorldPosition(new THREE.Vector3()) : (C.focus || C.tgt).clone(); LASTROOM = room && g.macro < 0.5;
  const dim = room ? 1 : 0.12;
  sun.position.set(1.0, 3.4, 2.6); sun.target.position.set(1.6, 0, 0); sun.target.updateMatrixWorld();
  sun.intensity = 2.4 * dim; hemi.intensity = 0.85 * dim; scene.environmentIntensity = 0.35 * dim; lamp.intensity = 6 * dim; scene.background = new THREE.Color(0xd9cbb6).multiplyScalar(dim);
  ssLight.intensity = g.set === 'sensor' ? 3 : 0;
  clockHands.s.rotation.z = -t * 6 * D2R; clockHands.m.rotation.z = -1.1; clockHands.h.rotation.z = -3.3;
  return { beat: g.b, cut: g.cut };
}
G.reset(); G.root.updateMatrixWorld(true);
const ANKLEH = wp(G.bones.footR).y;
fitGrip();

// ------------------------------------------------------------------ frame I/O (same contract as the other 3D Shorts)
const draw1 = () => LOOK ? LOOK.render(LASTFOCUS, { ao: LASTROOM, dof: LASTROOM }) : renderer.render(scene, camera);
const draw = () => draw1();
const gl = renderer.getContext(), px = new Uint8Array(W * H * 4);
let CUTF = false, LASTB = 0;
function segStart(t) { return B[beatAt(t)]; }
function stepTo(i) { const t = i / FPS, tt = ((t % TOTAL) + TOTAL) % TOTAL;
  if (i !== LASTF + 1) for (let j = Math.ceil(segStart(tt) * FPS - 1e-6) + Math.floor(t / TOTAL) * Math.round(TOTAL * FPS); j < i; j++) update(j / FPS, j);
  const r = update(t, i); CUTF = r.cut; LASTB = r.beat; LASTF = i; }
// seeds: the hold carries on across the beat 8 -> 9 cut and the loop (9 -> 0); chunks start each beat cold, so a straight run must too
for (let i = Math.ceil(B[8] * FPS); i < Math.ceil(B[9] * FPS); i++) update(i / FPS, i); SEED9.R = RG.LAST.armR.slice();
for (let i = Math.ceil(B[9] * FPS); i < Math.round(TOTAL * FPS); i++) update(i / FPS, i); LOOPSEED.R = RG.LAST.armR.slice();
draw(); update(B[2] + 1.0, -50); draw(); update(B[3] + 1.0, -40); draw(); update(B[1] + 1.0, -30); draw();     // warm-up: compile every set's shaders now
for (const k of Object.keys(RG.MEM)) delete RG.MEM[k]; LASTF = -10;
window.renderAll = async (f0, f1) => { for (let i = f0; i < f1; i++) { stepTo(i); draw(); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); await fetch('/frame', { method: 'POST', body: px }); } return 'ok'; };
window.renderAtT = t => { const i = Math.round(t * FPS); stepTo(i);
  if (window.CAM && window.CAM.hand) { const hp = RG.palmW(window.CAM.hand); window.CAM.tgt = hp.toArray(); window.CAM.pos = hp.clone().add(V(...window.CAM.off)).toArray(); }
  if (window.CAM) { camera.position.set(...window.CAM.pos); camera.up.set(0, 1, 0); camera.lookAt(...window.CAM.tgt); camera.fov = window.CAM.fov || 42; camera.near = 0.01; camera.updateProjectionMatrix(); }
  draw(); return renderer.domElement.toDataURL('image/png'); };
window.rigReport = i => { stepTo(i); const t = i / FPS, iq = G.root.getWorldQuaternion(new THREE.Quaternion()).invert();
  const ang = { ...RG.LAST }; delete ang.costR; delete ang.costL;
  return { t, beat: LASTB, ang, hips: wp(G.bones.hips).toArray(), car: 0, show: G.root.visible, cut: CUTF,
    thumbs: ['R', 'L'].map(S => wp(G.bones['index1' + S]).sub(wp(G.bones['pinky1' + S])).applyQuaternion(iq).toArray()),
    forearms: ['R', 'L'].map(S => wp(G.bones['hand' + S]).sub(wp(G.bones['farm' + S])).normalize().applyQuaternion(iq).toArray()),
    cost: [RG.LAST.costR ?? null, RG.LAST.costL ?? null], clip: clipScan() }; };
window.dbg = { G, RG, wp, THREE, update, guyAt, renderer, scene, camera, setBN: () => { BODYNOW = surfNow(); }, F, Rt, UP, PH, gripScore, phone, HANDV };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS);
window.READY = true;
window.SCN = { THREE, scene, camera, G, stepTo, renderer, FPS, B, DUR, TOTAL, phone, home };
