// ------------------------------------------------------------------ the film look, plus a speed pass: zoom blur, whip blur, and the 1954 newsreel grade
import { makeLook, loadIdle, idleAt, saccade } from '/look.js';
import { makeContact } from '/contact.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
const LOOKON = new URLSearchParams(location.search).get('look') !== '0';
const IDLE = LOOKON ? await loadIdle('/mocap/idle_77_02.json') : null;
const LOOK = LOOKON ? makeLook(THREE, renderer, scene, camera, W, H, { overlays: [gauge, darkPlane], noAO: [SKYG] }) : null; window.__LOOK = LOOK; window.__FOCUS = () => LASTFOCUS;
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

let BODYNOW = null, LASTH = [];
window.costParts = (i) => { stepTo(i); return LASTH.map(h => { const a = RG.LAST['arm' + h.S], f = RG.handFK(h.S, a); const cc = RG.contactCost(h)();
  return h.S + (h.free ? ' FREE' : '') + ' pos ' + (f.p.distanceTo(h.p) * 100).toFixed(1) + 'cm n ' + (h.n ? f.n.dot(h.n).toFixed(2) : '-') + ' w ' + (h.w ? f.w.dot(h.w).toFixed(2) : '-') + ' u ' + (h.u ? f.u.dot(h.u).toFixed(2) : '-') + ' contact ' + cc.toFixed(1) + ' extra ' + (h.extra ? h.extra(f).toFixed(1) : '-') + ' arm ' + a.map(v => v.toFixed(0)).join(','); }).join(' | '); };
const TIPS = ['index', 'middle', 'pinky', 'thumb'];
RG.contactCost = h => { const S = h.S, c0 = h.p, near = [];
  if (BODYNOW) { const { P, n } = BODYNOW; for (let j = 0; j < n; j++) { const dx = P[j * 3] - c0.x, dy = P[j * 3 + 1] - c0.y, dz = P[j * 3 + 2] - c0.z; if (dx * dx + dy * dy + dz * dz < 0.3 * 0.3) near.push(j); } }
  const NP = new Float32Array(near.length * 3), NN = new Float32Array(near.length * 3); near.forEach((j, k) => { for (let a = 0; a < 3; a++) { NP[k * 3 + a] = BODYNOW.P[j * 3 + a]; NN[k * 3 + a] = BODYNOW.N[j * 3 + a]; } });
  const solids = SOLIDS.filter(sd => sd.obj.visible && !/^(seat|backrest|headrest)/.test(sd.name)).map(sd => ({ inv: sd.obj.matrixWorld.clone().invert(), box: sd.box }));
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
    const top = c.clone().addScaledVector(fw, CHESTOFF * 0.85).addScaledVector(lf, 0.075 * s).addScaledVector(up, 0.15);   // runs up the front to the collarbone (the over-the-shoulder piece showed as a black block)
    segTo(STR[i * 2], top, fr, fw); segTo(STR[i * 2 + 1], fr, lap.clone().addScaledVector(hl, 0.02 * s), fw); }
  segTo(STR[4], lap.clone().addScaledVector(hl, 0.2), lap.clone().addScaledVector(hl, -0.2), hf); STR[4].scale.x = 1.3;
  buckle.position.copy(lap).addScaledVector(hf, 0.012); buckle.quaternion.copy(qh); }

function SMOKE_B(p, i) { if (i < BSMOKE.n) BSMOKE.p.set([p.x * 1.15, p.y + 0.15, p.z - 0.2], i * 3); }
// his hands on the grab bars: palm down on top, fingers over the outside of the bar, thumb on the inside (a held bar has something on both sides)
const LOOPSEED = { R: null, L: null };   // beat 9's last arm: frame one starts from it, so the loop lands on the same arm (a cold solve picked another branch: 107 deg seam)
const STRAPS2 = { R: [], L: [] };
function placeArmStraps() { }   // the straps ride the forearm bones (parented at load), nothing to do per frame
// the rig's hold only bends the thumb's base (thumb1); its tip joint stayed straight and stuck out along the pad. Finish the thumb here.
const THUMB = { R: { yaw: 0, tip: 0 }, L: { yaw: 0, tip: 0 } };
function thumbPose(S) { const sg = S === 'R' ? -1 : 1, t1 = G.bones['thumb1' + S], t2 = G.bones['thumb2' + S];
  t1.quaternion.multiply(qTmp.setFromEuler(eTmp.set(0, THUMB[S].yaw * D2R, 0))); t2.quaternion.copy(G.REST['thumb2' + S].q).multiply(qTmp.setFromEuler(eTmp.set(0, 0, sg * THUMB[S].tip * D2R))); }
const FIST = { R: null, L: null }, FISTPOSE = { R: { c: 105, th: 60, opp: 50 }, L: { c: 105, th: 60, opp: 50 } };      // where each fist sits on its armrest (set at load from his arm)
function gripHands(b, lt = 1) { return ['R', 'L'].map(S => {
  const top = ARMS[S].position.y, z0 = ARMS[S].position.z - 0.24, z1 = ARMS[S].position.z + 0.24;
  const tgt = FIST[S] ? FIST[S].clone() : null;
  const extra = f => { let c = 0; if (tgt) c += (f.p.distanceTo(tgt) / 0.0012) ** 2 + (1 - f.n.dot(V(0, -1, 0))) * 900 + (1 - f.u.dot(V(0, 0, 1))) * 600;   // strapped: the fist doesn't drift on the pad (it dipped 2 mm into it and lifted 6 mm off it under the g-forces)
    for (const k of [0, 0.35, 0.7]) { const p = f.el.clone().lerp(f.p, k); if (p.z > z0 && p.z < z1) c += (Math.max(0, top + 0.036 - p.y) / 0.002) ** 2; } return c; };   // elbow and forearm stay on top of the pad (they sank 2 cm into it in the slam)
  const h = { S, p: FIST[S] ? FIST[S].clone() : V(0, 0.9, 0.3), n: V(0, -1, 0), u: V(0, 0, 1), c: FISTPOSE[S].c, th: FISTPOSE[S].th, opp: FISTPOSE[S].opp, extra, memAbs: 'arm' + S + ':' + b, seed: A(10, 8, 0, 85, -60) };
  return b === 0 && lt < 0.5 / FPS && LOOPSEED[S] ? { ...h, seed: LOOPSEED[S], seedIsPrev: true } : h; }); }
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
  G.root.updateMatrixWorld(true);
  if (g.show) { BODYNOW = surfNow(); const list = gripHands(b, g.lt); RG.hands(list, 'b' + b, frame); LASTH = list; for (const S of ['R', 'L']) thumbPose(S); G.root.updateMatrixWorld(true); placeArmStraps(); }
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
  { let n = 0; if (!(inEye || inBelt) && T > 0.3) for (let j = 0; j < DUST.n; j++) { const age = 1.6 * (j / DUST.n) ** 2, Te = T - age; if (Te < 0.3) continue; const ve = vAt(Te); if (ve < 60) continue;   // packed near the sled, thinning out far behind
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
  footrest.position.set(0, fy - 0.02, Math.min(0.68, fz + 0.04));
  const q = wq(G.bones.chest), fw = V(0, 0, -1).applyQuaternion(q), up = V(0, 1, 0).applyQuaternion(q); const p0 = wp(G.bones.chest).addScaledVector(up, 0.02);
  let s = 0.05; while (s < 0.35 && bodyDepth(p0.clone().addScaledVector(fw, s)) > 0) s += 0.002; CHESTOFF = s + 0.008;
  const qh = wq(G.bones.hips), hf = V(0, 0, -1).applyQuaternion(qh), h0 = wp(G.bones.hips); s = 0.05; while (s < 0.35 && bodyDepth(h0.clone().addScaledVector(hf, s)) > 0) s += 0.002; HIPOFF = s + 0.01;
  window.SEATFIT = { HIPY, lo, fy, CHESTOFF, HIPOFF }; SURF = null; }
{ // his arms on the armrests: elbows at his sides, forearms forward, fists palm-down at the front; the armrests and straps are fitted to his skin
  RG.applyPose(SITPOSE, { x: 0, y: HIPY, z: 0, yaw: YAW }); G.root.updateMatrixWorld(true);
  for (const S of ['R', 'L']) { const el = wp(G.bones['farm' + S]); FIST[S] = V(el.x * 0.92, el.y + 0.0, el.z + 0.27); }
  for (const k of Object.keys(RG.MEM)) delete RG.MEM[k]; BODYNOW = surfNow(); RG.hands(gripHands(-1), 'fit', -100); G.root.updateMatrixWorld(true);
  const m = G.meshes.skin_head, ga = m.geometry.attributes, names = m.skeleton.bones.map(b => b.name), _v = V(0, 0, 0);
  const dom = i => { let bw = -1, bi = 0; for (let k = 0; k < 4; k++) { const wt = ga.skinWeight.getComponent(i, k); if (wt > bw) { bw = wt; bi = ga.skinIndex.getComponent(i, k); } } return names[bi]; };
  for (const S of ['R', 'L']) { const el = wp(G.bones['farm' + S]), wr = wp(G.bones['hand' + S]), ax = wr.clone().sub(el), L = ax.length(); ax.normalize();
    const P = []; for (let i = 0; i < ga.position.count; i++) if (new RegExp('^farm(Twist)?' + S + '$').test(dom(i))) { _v.set(ga.position.getX(i), ga.position.getY(i), ga.position.getZ(i)); m.applyBoneTransform(i, _v); P.push(_v.clone().applyMatrix4(m.matrixWorld)); }
    // the armrest pad: its top just under the forearm's underside, running from the elbow to the fist
    const mid = P.filter(p => { const t = p.clone().sub(el).dot(ax) / L; return t > 0.3 && t < 0.92; });   // the forearm's underside, not the elbow's bump (the pad sat 3 cm low)
    const low = Math.min(...mid.map(p => p.y)), cx = mid.reduce((a, p) => a + p.x, 0) / mid.length;
    ARMS[S].position.set(cx, low - 0.003, (el.z + FIST[S].z) / 2 + 0.03); ARMS[S].children[0].scale.z = 1.15; const post = ARMS[S].userData.post; post.scale.y = (low - 0.004) - 0.7; post.position.y = -post.scale.y / 2 - 0.045;
    // two straps round the forearm (near the elbow and at the wrist), sized to the forearm there in two directions + 4 mm
    const fb = G.bones['farm' + S], inv = fb.matrixWorld.clone().invert(), axL = ax.clone().transformDirection(inv).normalize();
    const e1 = new THREE.Vector3(0, 1, 0).transformDirection(inv); e1.addScaledVector(axL, -e1.dot(axL)).normalize(); const e2 = new THREE.Vector3().crossVectors(axL, e1);
    const elL = el.clone().applyMatrix4(inv), PL = P.map(p => p.clone().applyMatrix4(inv)), LL = wr.clone().applyMatrix4(inv).sub(elL).length();
    STRAPS2[S] = [0.38, 0.8].map(t => { const c0 = elL.clone().addScaledVector(axL, t * LL), near = PL.filter(p => Math.abs(p.clone().sub(c0).dot(axL)) < 0.015);
      const r1 = Math.max(...near.map(p => Math.abs(p.clone().sub(c0).dot(e1)))) + 0.004, r2 = Math.max(...near.map(p => Math.abs(p.clone().sub(c0).dot(e2)))) + 0.004;
      const c = near.reduce((a, p) => a.add(p), V(0, 0, 0)).multiplyScalar(1 / near.length); c.addScaledVector(axL, -c.clone().sub(c0).dot(axL));   // the forearm's middle there
      const ring = new THREE.Mesh(new THREE.TorusGeometry(1, 0.008, 8, 40), strapM); ring.scale.set(r1, r2, 1);
      ring.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(e1, e2, axL)); ring.position.copy(c); fb.add(ring); ring.castShadow = true;
      const tab = new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.018, 0.026), mat(0xb8bcc2, 0.3, 0.8)); tab.position.set(r1 + 0.004, 0, 0); ring.add(tab); tab.scale.set(1 / r1, 1 / r2, 1);   // the buckle
      return ring; }); }
  for (const k of Object.keys(RG.MEM)) delete RG.MEM[k]; BODYNOW = null; G.reset(); G.root.updateMatrixWorld(true); }
// contact check on his hand skin (contact.js): each fist rests on its armrest; the seat, backrest and deck must never be entered
const CT = makeContact(THREE, G);
for (const S of ['R', 'L']) { const p = ARMS[S].children[0]; p.geometry.computeBoundingBox(); const bb = p.geometry.boundingBox; CT.prop('armrest ' + S, p, { type: 'box', min: bb.min.toArray(), max: bb.max.toArray() }); }
CT.prop('seat pan', sled, { type: 'box', min: [-0.28, SEATTOP - 0.06, -0.23], max: [0.28, SEATTOP - 0.005, 0.27] });
CT.prop('backrest', sled, { type: 'box', min: [-0.28, SEATTOP, -0.275], max: [0.28, SEATTOP + 0.78, -0.205] });
DECK.forEach((d, i) => { d.geometry.computeBoundingBox(); CT.prop('deck ' + i, d, { type: 'box', min: d.geometry.boundingBox.min.toArray(), max: d.geometry.boundingBox.max.toArray() }); });
const HOLDS = [{ S: 'R', prop: 'armrest R', mode: 'rest' }, { S: 'L', prop: 'armrest L', mode: 'rest' }];
window.contactSelfTest = () => CT.selfTest(HOLDS);
// the fist fit takes ~28 s (half the load): saved to sled/fit.json once (node savefit.mjs sled_mh.html sled/fit.json) and loaded after.
// Delete fit.json after changing the arms, armrests or fist; a stale fit still can't slip through: the contact check judges every frame.
const FITJ = await fetch('/sled/fit.json').then(r => r.ok ? r.json() : null).catch(() => null);
if (FITJ && FITJ.v === 'fist-v1') { for (const S of ['R', 'L']) { FISTPOSE[S] = FITJ[S].pose; THUMB[S] = FITJ[S].thumb; FIST[S].y = FITJ[S].y; } window.FISTFIT = 'from fit.json'; }
else { // fit each fist to its pad with the contact checker: a thumb pose that stays out of the pad, then the fist lowered until its knuckles sit on it
  const solve = () => { for (const k of Object.keys(RG.MEM)) delete RG.MEM[k]; RG.applyPose(SITPOSE, { x: 0, y: HIPY, z: 0, yaw: YAW }); G.root.updateMatrixWorld(true);
    BODYNOW = surfNow(); RG.hands(gripHands(-1), 'fit', -100); for (const S of ['R', 'L']) thumbPose(S); G.root.updateMatrixWorld(true); };
  const fit = {};
  const others = r => Math.min(...['index', 'middle', 'ring', 'pinky', 'palm'].map(k => r.gaps[k] ?? 1));
  for (const S of ['R', 'L']) { const name = 'armrest ' + S; let best = null;
    for (let round = 0; round < 3; round++) {                       // alternate: the thumb pose at this height, then the height for that thumb
      best = null;
      for (const th of [0, 20, 40, 60]) for (const opp of [-20, 10, 40, 70]) { FISTPOSE[S] = { c: 105, th, opp }; THUMB[S] = { yaw: 0, tip: 0 }; solve();
        const base = G.bones['thumb1' + S].quaternion.clone();
        for (const yaw of [-30, -15, 0, 15, 30]) for (const tip of [0, 20, 40, 60, 80]) { G.bones['thumb1' + S].quaternion.copy(base); THUMB[S] = { yaw, tip }; thumbPose(S); G.root.updateMatrixWorld(true);
          const r = CT.probe(S, name); if (r.nIn > 0) continue; const tg = (r.gaps.thumb ?? 1) - others(r);
          const im = wp(G.bones['index2' + S]).lerp(RG.tip('index', S), 0.5), tuck = RG.tip('thumb', S).distanceTo(im);   // a fist's thumb lies across the index finger's middle segment
          const sc = Math.max(0, 0.006 - tg) * 10 + Math.abs(tuck - 0.014) * 4; if (!best || sc < best.sc) best = { sc, th, opp, yaw, tip, tuck }; } }
      if (!best) { FIST[S].y += 0.004; continue; }
      FISTPOSE[S] = { c: 105, th: best.th, opp: best.opp }; THUMB[S] = { yaw: best.yaw, tip: best.tip };
      for (let it = 0; it < 4; it++) { solve(); const r = CT.probe(S, name); if (r.nIn > 0) { FIST[S].y += r.worst + 0.002; continue; } const g = Math.min(others(r), (r.gaps.thumb ?? 1) - 0.004);
        if (Math.abs(g - 0.0025) < 0.0007) break; FIST[S].y -= g - 0.0025; } }   // the lowest point of the fist 2.5 mm above the pad (motion margin)
    if (!best) throw new Error('fist fit: no thumb pose stays out of the pad');
    solve(); const r = CT.probe(S, name); fit[S] = { th: best.th, opp: best.opp, yaw: best.yaw, tip: best.tip, tuckMM: +(best.tuck * 1000).toFixed(1), fistY: +FIST[S].y.toFixed(4), gaps: Object.fromEntries(Object.entries(r.gaps).map(([k, v]) => [k, +(v * 1000).toFixed(1)])), inPts: r.nIn }; }
  window.FISTFIT = fit; for (const k of Object.keys(RG.MEM)) delete RG.MEM[k]; BODYNOW = null; G.reset(); G.root.updateMatrixWorld(true); }
window.FITSAVE = { v: 'fist-v1', ...Object.fromEntries(['R', 'L'].map(S => [S, { pose: FISTPOSE[S], thumb: THUMB[S], y: FIST[S].y }])) };
sbox('footrest', footrest, V(-0.29, -0.02, -0.18), V(0.29, 0.02, 0.18));
for (const S of ['R', 'L']) sbox('armrest ' + S, ARMS[S], V(-0.055, -0.045, -0.24), V(0.055, 0, 0.24));
DECK.forEach((d, i) => { d.geometry.computeBoundingBox(); const bb = d.geometry.boundingBox; sbox('deck ' + i, d, bb.min.clone(), bb.max.clone()); });   // real bounds (a RoundedBoxGeometry's width/height/depth fields read 1)   // so the rig check catches legs through the deck

// ------------------------------------------------------------------ frame I/O (same contract as the other 3D Shorts)
const draw = () => LOOK ? LOOK.render(LASTFOCUS, { ao: true, dof: true, rim: LASTRIM }) : renderer.render(scene, camera);
const gl = renderer.getContext(), px = new Uint8Array(W * H * 4);
let CUTF = false, LASTB = 0, LASTF = -10;
function stepTo(i) { const t = i / FPS, tt = ((t % TOTAL) + TOTAL) % TOTAL;
  if (i !== LASTF + 1) for (let j = Math.ceil(B[beatAt(tt)] * FPS - 1e-6) + Math.floor(t / TOTAL) * Math.round(TOTAL * FPS); j < i; j++) update(j / FPS, j);   // a chunk starts each beat cold, like a straight run does
  const r = update(t, i); CUTF = r.cut; LASTB = r.beat; LASTF = i; }
for (let i = Math.ceil(B[9] * FPS); i < Math.round(TOTAL * FPS); i++) update(i / FPS, i);   // run beat 9 to its end once: its last arm seeds frame one
LOOPSEED.R = RG.LAST.armR.slice(); LOOPSEED.L = RG.LAST.armL.slice(); for (const k of Object.keys(RG.MEM)) delete RG.MEM[k];
for (const tt of [B[4] + 1, B[7] + 1, B[8] + DUR[8] * 0.3, B[8] + DUR[8] * 0.8, 0.1]) { update(tt, -50); draw(); }     // warm-up: compile every stage's shaders now
for (const k of Object.keys(RG.MEM)) delete RG.MEM[k]; LASTF = -10;
window.renderAll = async (f0, f1) => { for (let i = f0; i < f1; i++) { stepTo(i); draw(); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); await fetch('/frame', { method: 'POST', body: px }); } return 'ok'; };
window.renderAtT = t => { const i = Math.round(t * FPS); stepTo(i);
  if (window.CAM && window.CAM.hand) { const hp = RG.palmW(window.CAM.hand); window.CAM.tgt = hp.toArray(); window.CAM.pos = hp.clone().add(V(...window.CAM.off)).toArray(); }
  if (window.CAM) { camera.position.set(...window.CAM.pos); camera.up.set(0, 1, 0); camera.lookAt(...window.CAM.tgt); camera.fov = window.CAM.fov || 42; camera.updateProjectionMatrix(); SKYG.position.copy(camera.position); if (window.CAM.nohud) { gauge.visible = false; darkPlane.visible = false; FX.uniforms.uRad.value = 0; FX.uniforms.uDir.value.set(0, 0); } }
  draw(); return renderer.domElement.toDataURL('image/png'); };
window.rigReport = i => { stepTo(i); const t = i / FPS, iq = G.root.getWorldQuaternion(new THREE.Quaternion()).invert();
  const ang = { ...RG.LAST }; delete ang.costR; delete ang.costL;
  return { t, beat: LASTB, ang, hips: wp(G.bones.hips).toArray(), car: 0, show: G.root.visible, cut: CUTF,
    thumbs: ['R', 'L'].map(S => wp(G.bones['index1' + S]).sub(wp(G.bones['pinky1' + S])).applyQuaternion(iq).toArray()),
    forearms: ['R', 'L'].map(S => wp(G.bones['hand' + S]).sub(wp(G.bones['farm' + S])).normalize().applyQuaternion(iq).toArray()),
    cost: [RG.LAST.costR ?? null, RG.LAST.costL ?? null], clip: clipScan(), contacts: G.root.visible ? CT.report(HOLDS) : [] }; };
window.dbg = { G, RG, wp, THREE, update, guyAt, renderer, scene, camera, F, Rt, UP, vAt, gAt, distAt };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS);
window.READY = true;
window.SCN = { THREE, scene, camera, G, stepTo, renderer, FPS, B, DUR, TOTAL };   // for studio/blender/export_shot.mjs
