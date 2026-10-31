// "You just got lost in the woods with no food and no water." - a 3D Short: how long you can last without water, then without food.
//   starve.html?w=1080&h=1920            (times from starve/times.json; one shot per narration line)
// Beats: 0 he shakes his empty bottle: one drop (hook) | 1 three days and nights race past; he wilts | 2 x-ray: the kidneys fail, it all dims
//        3 the stream: he fills the bottle and drinks | 4 x-ray: the liver's sugar runs out, the fat burns | 5 x-ray: then the muscle
//        6 a tally carved on a tree: weeks, up to about two months | 7 lost, looking around (loops)
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { loadGuy } from '/guy3d.js';

const Q = new URLSearchParams(location.search);
const W = +Q.get('w') || 720, H = +Q.get('h') || 1280;
const FPS = 30;
const TIMES = await (await fetch('/starve/times.json')).json();
const B = TIMES.starts, DUR = TIMES.durs, TOTAL = TIMES.total;
const beatAt = t => { let i = 0; for (let k = 0; k < B.length; k++) if (t >= B[k]) i = k; return i; };
const clamp = (x, a, b) => Math.min(Math.max(x, a), b);
const sm = t => t * t * (3 - 2 * t);
const smooth = (a, b, x) => sm(clamp((x - a) / (b - a), 0, 1));
const lerp = (a, b, u) => a + (b - a) * u;
const D2R = Math.PI / 180;
function hash1(n) { const s = Math.sin(n * 127.1) * 43758.5453; return s - Math.floor(s); }
function vn1(x, seed) { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return lerp(hash1(i + seed * 17.3), hash1(i + 1 + seed * 17.3), u) * 2 - 1; }
const V = (x, y, z) => new THREE.Vector3(x, y, z);
function canvasTex(w, h, draw) { const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), c); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t; }
const qAA = (ax, deg) => new THREE.Quaternion().setFromAxisAngle(ax, deg * D2R);
const yawQ = deg => qAA(V(0, 1, 0), deg);
const fwdOf = yaw => V(-Math.sin(yaw * D2R), 0, -Math.cos(yaw * D2R));          // the way he faces (yaw 0 = -z)
const rightOf = yaw => V(Math.cos(yaw * D2R), 0, -Math.sin(yaw * D2R));         // his right
const wp = o => o.getWorldPosition(new THREE.Vector3()), wq = o => o.getWorldQuaternion(new THREE.Quaternion());

// ------------------------------------------------------------------ renderer, light
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(W, H);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05; renderer.outputColorSpace = THREE.SRGBColorSpace;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(45, W / H, 0.03, 300);
const ENVC = new THREE.Color(0xd9cbb6);
{ const pm = new THREE.PMREMGenerator(renderer); const es = new THREE.Scene(); es.background = ENVC; es.add(new THREE.HemisphereLight(0xfff2e0, 0x6a5040, 1));
  scene.environment = pm.fromScene(es, 0.04).texture; scene.environmentIntensity = 0.35; }
const hemi = new THREE.HemisphereLight(0xfff0dd, 0x6b5a48, 0.85); scene.add(hemi);
const sun = new THREE.DirectionalLight(0xffe3bf, 2.6); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
{ const S = sun.shadow.camera; S.left = -5; S.right = 5; S.top = 5; S.bottom = -5; S.near = 0.5; S.far = 30; sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.02; }
scene.add(sun); scene.add(sun.target);
const lamp = new THREE.PointLight(0xffc98a, 6, 9, 1.6); lamp.position.set(2.2, 1.9, -2.4); lamp.castShadow = false; scene.add(lamp);
const mat = (c, r = 0.8, m = 0) => new THREE.MeshStandardMaterial({ color: c, roughness: r, metalness: m });
const box = (w, h, d, x, y, z, m, r = 0, parent = scene) => { const o = new THREE.Mesh(r > 0 ? new RoundedBoxGeometry(w, h, d, 2, Math.min(r, 0.4 * Math.min(w, h, d))) : new THREE.BoxGeometry(w, h, d), m); o.position.set(x, y, z); o.castShadow = true; o.receiveShadow = true; parent.add(o); return o; };

const GLSLN = `float hh(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); } float vn(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f*f*(3.0-2.0*f); return mix(mix(hh(i), hh(i+vec2(1,0)), u.x), mix(hh(i+vec2(0,1)), hh(i+vec2(1,1)), u.x), u.y); }`;
// ------------------------------------------------------------------ the owner (same guy as always)
const G = await loadGuy(THREE, '/char/guy', {});
scene.add(G.root); G.root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
const HIP = V(0, 0.95, 0);
const LIMITS = {
  spine1: [[-30, 20], [-20, 20], [-15, 15]], spine2: [[-30, 20], [-20, 20], [-15, 15]], chest: [[-25, 20], [-20, 20], [-15, 15]],
  neck: [[-35, 35], [-50, 50], [-20, 20]], head: [[-30, 30], [-40, 40], [-20, 20]],
  thighR: [[-30, 120], [-30, 30], [-25, 45]], thighL: [[-30, 120], [-30, 30], [-45, 25]],
  shinR: [[-150, 0], [-5, 5], [-5, 5]], shinL: [[-150, 0], [-5, 5], [-5, 5]],
  footR: [[-45, 30], [-15, 15], [-15, 15]], footL: [[-45, 30], [-15, 15], [-15, 15]],
};
const ARM_LIM = [[-50, 170], [-25, 170], [-60, 60], [0, 145], [-80, 80], [-65, 70], [-25, 25]];
function softc(x, lo, hi, knee = 6) { if (x > hi - knee) return hi - knee + knee * Math.tanh((x - (hi - knee)) / knee); if (x < lo + knee) return lo + knee - knee * Math.tanh(((lo + knee) - x) / knee); return x; }
const FINGERS = ['index', 'middle', 'ring', 'pinky'];
function curl(p, S, c, th = c) { for (const f of FINGERS) { p[f + '1' + S] = [0, 0, (S === 'R' ? -1 : 1) * c * 0.9]; p[f + '2' + S] = [0, 0, (S === 'R' ? -1 : 1) * c]; } p['thumb1' + S] = [0, 0, (S === 'R' ? -1 : 1) * th * 0.4]; return p; }
const A = (fl, ab, ro, el, pr = 0, wf = 0, wd = 0) => [fl, ab, ro, el, pr, wf, wd];
const ARM0 = A(4, 8, 0, 14);
function eul(p, n) { return p[n] || (n === 'armR' || n === 'armL' ? ARM0 : [0, 0, 0]); }
function mixPose(a, b, k) { const o = {}; for (const n of new Set([...Object.keys(a), ...Object.keys(b)])) { const x = eul(a, n), y = eul(b, n); o[n] = x.map((v, i) => lerp(v, y[i] ?? 0, k)); } return o; }
function addPose(a, d) { const o = { ...a }; for (const [n, v] of Object.entries(d)) { const x = eul(o, n); o[n] = x.map((w, i) => w + (v[i] || 0)); } return o; }
function keyed(keys, t) { if (t <= keys[0][0]) return keys[0][1]; for (let i = 0; i < keys.length - 1; i++) { const [t0, a] = keys[i], [t1, b] = keys[i + 1]; if (t <= t1) return mixPose(a, b, sm((t - t0) / (t1 - t0))); } return keys[keys.length - 1][1]; }
const STAND = curl(curl({ armR: A(6, 8, 0, 16), armL: A(6, 8, 0, 16), neck: [2, 0, 0] }, 'R', 26), 'L', 26);
const qTmp = new THREE.Quaternion(), eTmp = new THREE.Euler();
// one rig per person (the same body plan): pose, arm angles, hand solve, feet, body-relative points
function makeRig(Gx, tag) {
  const BONES = Object.keys(Gx.bones); Gx.reset();
  const ARMREST = {}, HANDREST = {};
  for (const S of ['R', 'L']) { const af = Gx.REST['farm' + S].axis.clone();
    ARMREST[S] = { s: S === 'R' ? 1 : -1, a0: Gx.REST['uarm' + S].axis.clone(), af, hinge: new THREE.Vector3().crossVectors(af, V(0, 0, -1)).normalize() };
    const h = Gx.man.hands[S]; HANDREST[S] = { u: V(...h.u), n: V(...h.n), w: V(...h.w) }; }
  function armQuats(S, a) { const R_ = ARMREST[S], h = HANDREST[S], [flex, abd, rot, el, pro, wf = 0, wd = 0] = a;
    const rv = V(flex, 0, R_.s * abd); const ang = rv.length();
    const d = ang > 1e-6 ? V(0, -1, 0).applyQuaternion(qAA(rv.clone().normalize(), ang)) : V(0, -1, 0);
    return { Lu: new THREE.Quaternion().setFromUnitVectors(R_.a0, d).multiply(qAA(R_.a0, R_.s * rot)), Lf: qAA(R_.hinge, el).multiply(qAA(R_.af, R_.s * pro)), Lh: qAA(h.w, R_.s * wf).multiply(qAA(h.n, R_.s * wd)) }; }
  function setArm(S, a) { const { Lu, Lf, Lh } = armQuats(S, a);
    Gx.bones['uarm' + S].quaternion.copy(Lu); Gx.bones['uarmTwist' + S].quaternion.identity(); Gx.bones['farm' + S].quaternion.copy(Lf); Gx.bones['farmTwist' + S].quaternion.identity(); Gx.bones['hand' + S].quaternion.copy(Lh); }
  const R = { G: Gx, tag, LAST: {}, HANDREST, setArm };
  R.applyPose = (p, root) => { const lim = {};
    for (const n of BONES) { if (/^(uarm|uarmTwist|farm|farmTwist|hand)[RL]$/.test(n)) continue;
      const b = Gx.bones[n]; let e = eul(p, n); if (LIMITS[n]) e = e.map((v, i) => softc(v, LIMITS[n][i][0], LIMITS[n][i][1]));
      lim[n] = e; b.position.copy(Gx.REST[n].pos); b.quaternion.copy(Gx.REST[n].q).multiply(qTmp.setFromEuler(eTmp.set(e[0] * D2R, e[1] * D2R, e[2] * D2R))); }
    for (const S of ['R', 'L']) { const a = eul(p, 'arm' + S).map((v, i) => softc(v, ARM_LIM[i][0], ARM_LIM[i][1], i === 3 ? 4 : 5)); lim['arm' + S] = a; setArm(S, a); }
    const q = new THREE.Quaternion().setFromEuler(new THREE.Euler((root.tilt || 0) * D2R, (root.yaw || 0) * D2R, (root.roll || 0) * D2R, 'YXZ'));
    Gx.root.quaternion.copy(q); Gx.root.position.copy(V(root.x, root.y, root.z)).sub(HIP.clone().applyQuaternion(q)); Gx.root.updateMatrixWorld(true);
    R.LAST = lim; };
  R.PALM = S => HANDREST[S].u.clone().multiplyScalar(0.06).addScaledVector(HANDREST[S].n, 0.012);
  R.palmW = S => R.PALM(S).applyMatrix4(Gx.bones['hand' + S].matrixWorld);
  function torsoInside(p) { const c = wp(Gx.bones.chest), sp = wp(Gx.bones.spine1), iq = wq(Gx.bones.chest).invert(), d = p.clone().sub(c).applyQuaternion(iq);
    if (d.y > 0.22 || p.clone().sub(sp).applyQuaternion(iq).y < -0.2) return 0; const r = Math.hypot(d.x / 0.17, d.z / 0.13); return r < 1 ? (1 - r) * 0.13 : 0; }
  const _m = new THREE.Matrix4(), _q = new THREE.Quaternion();
  function handFK(S, a) { setArm(S, a); const hb = Gx.bones['hand' + S]; Gx.bones['uarm' + S].updateMatrixWorld(true);
    const M = _m.copy(hb.matrixWorld); const qh = _q.setFromRotationMatrix(M);
    return { p: R.PALM(S).applyMatrix4(M), n: HANDREST[S].n.clone().applyQuaternion(qh), w: HANDREST[S].w.clone().applyQuaternion(qh), u: HANDREST[S].u.clone().applyQuaternion(qh), el: wp(Gx.bones['farm' + S]), sh: wp(Gx.bones['uarm' + S]) }; }
  R.handFK = handFK;
  const MEM = {}; R.MEM = MEM;
  R.solveHand = (tg, key, frame) => { const S = tg.S;
    const cost = a => { const f = handFK(S, a);
      let c = tg.free ? 0 : f.p.distanceToSquared(tg.p) / (0.006 * 0.006);      // free: only the extra cost places the hand (a tool tip, say)
      if (tg.anchor) for (let i = 0; i < 7; i++) c += ((a[i] - tg.anchor[i]) / 2) ** 2;
      if (tg.n) c += (1 - f.n.dot(tg.n)) * 40; if (tg.w) c += (1 - f.w.dot(tg.w)) * 25; if (tg.u) c += (1 - f.u.dot(tg.u)) * 25;
      for (let i = 0; i < 7; i++) { const [lo, hi] = ARM_LIM[i], mid = [20, 15, 0, 60, 0, 0, 0][i]; c += 0.6 * ((a[i] - mid) / (hi - lo)) ** 2; }
      const ins = torsoInside(f.el) + torsoInside(f.el.clone().lerp(f.p, 0.5)); c += (ins / 0.01) ** 2;
      if (prev) for (let i = 0; i < 7; i++) c += ((a[i] - prev[i]) / 3) ** 2;
      if (tg.extra) c += tg.extra(f);
      return c; };
    const m = MEM[key]; let prev = m && m.frame === frame - 1 ? m.a : (tg.seedIsPrev && tg.seed ? tg.seed : null);
    const COLD = [A(40, 15, 0, 80, 0), A(60, 25, 20, 60, 40), A(30, 40, -20, 100, -30), A(80, 10, 0, 110, 60), A(50, 30, 30, 40, 70), A(20, 20, -30, 120, -60), A(60, 10, -10, 100, 75), A(40, 20, 10, 90, -75)];
    const descend = (s0, big) => { let a = s0.map((v, i) => clamp(v, ARM_LIM[i][0], ARM_LIM[i][1])), ca = cost(a);
      for (let step = big; step >= 0.25; step /= 2) { let imp = true, g = 0;
        while (imp && g++ < 10) { imp = false; for (let i = 0; i < 7; i++) for (const sg of [1, -1]) { const b = a.slice(); b[i] = clamp(b[i] + sg * step, ARM_LIM[i][0], ARM_LIM[i][1]); const cb = cost(b); if (cb < ca - 1e-9) { a = b; ca = cb; imp = true; } } } }
      return { a, c: ca }; };
    let best = null;
    if (!prev && tg.seed) { const r = descend(tg.seed, 8); if (r.c < 8) best = r; }
    if (!best) for (const s0 of prev ? [prev] : (tg.seed ? [tg.seed, ...COLD] : COLD)) { const r = descend(s0, prev ? 4 : 16); if (!best || r.c < best.c) best = r; }
    if (!prev) for (let r = 0; r < 4; r++) { const p2 = descend(best.a, 6 / (r + 1)); if (p2.c < best.c - 1e-6) best = p2; else break; }   // a cold start: polish (coordinate descent stalls in long valleys)
    if (prev && best.c > 20 && !tg.local) for (const s0 of (tg.seed ? [tg.seed, ...COLD] : COLD)) { const r = descend(s0, 16); if (r.c < best.c) best = r; }
    MEM[key] = { frame, a: best.a }; const pv = prev; prev = null; best.miss = cost(best.a); prev = pv; return best; };
  const fingers = h => { const pp = {}; curl(pp, h.S, h.c ?? 30, h.th); if (h.opp) pp['thumb1' + h.S][0] = -h.opp; if (h.point) { pp['index1' + h.S] = [0, 0, -5]; pp['index2' + h.S] = [0, 0, -5]; }
    for (const [n, e] of Object.entries(pp)) Gx.bones[n].quaternion.copy(Gx.REST[n].q).multiply(qTmp.setFromEuler(eTmp.set(e[0] * D2R, e[1] * D2R, e[2] * D2R))); };
  const withContact = h => { if (!R.contactCost) return h; const cc = R.contactCost(h), ex = h.extra; return { ...h, extra: ex ? f => ex(f) + cc(f) : cc }; };
  R.hands = (list, key, frame) => { for (const h0 of list) { const h = withContact(h0);
      let posed; if (h.from) { fingers(h.from); posed = R.solveHand(withContact(h.from), key + (h.from.mem || 'from' + h.S), frame).a; } else posed = (R.LAST['arm' + h.S] || ARM0).slice();
      fingers(h); const sol = R.solveHand(h, h.memAbs || key + (h.mem || h.S), frame);
      const bl = h.blend ?? 1; let a = sol.a, c = sol.miss;
      if (h.blend !== undefined || h.from) {                    // moving from one hold (or the pose) to another: joint angles ease across, and a small
        const al = posed.map((v, i) => lerp(v, sol.a[i], bl));   // nudge (anchored to that eased arm) keeps the hand, fingers and elbow out of his body
        const fc = h.from ? (h.from.c ?? 30) : 26, ft = h.from ? (h.from.th ?? fc) : 26;
        fingers({ S: h.S, c: lerp(fc, h.c ?? 30, bl), th: lerp(ft, h.th ?? (h.c ?? 30), bl), point: h.point && bl > 0.5 });
        const ns = R.solveHand(withContact({ S: h.S, free: true, soft: h.soft, p: handFK(h.S, al).p, anchor: al, seed: al, seedIsPrev: true, local: true }), key + 'nudge' + h.S, -99);
        a = ns.a; if (bl < 0.999) c = null; }                    // on the way there it isn't holding anything yet (the clip check covers the path)
      setArm(h.S, a); R.LAST['arm' + h.S] = a; R.LAST['cost' + h.S] = c; } };
  R.untwist = () => { for (const S of ['R', 'L']) { const ua = Gx.bones['uarm' + S], ut = Gx.bones['uarmTwist' + S]; ua.quaternion.multiply(ut.quaternion); ut.quaternion.identity(); } Gx.untwist(); };
  R.foot = (S, f, pole, q) => Gx.legIK(S, f, pole, q);
  Gx.reset(); Gx.root.updateMatrixWorld(true);
  const ML = V(0, Gx.man.mouthY, Gx.man.mouthZ ?? -0.105).applyMatrix4(Gx.bones.head.matrixWorld.clone().invert());
  R.mouthW = () => ML.clone().applyMatrix4(Gx.bones.head.matrixWorld);
  const TIPSEG = {}; for (const S of ['R', 'L']) for (const f of ['index', 'middle', 'pinky', 'thumb']) { const b1 = Gx.bones[f + '1' + S], b2 = Gx.bones[f + '2' + S]; TIPSEG[f + S] = wp(b2).sub(wp(b1)).multiplyScalar(0.95).applyQuaternion(wq(b2).invert()); }
  R.tip = (f, S) => { const b2 = Gx.bones[f + '2' + S]; return wp(b2).add(TIPSEG[f + S].clone().applyQuaternion(wq(b2))); };
  return R;
}
const RG = makeRig(G, 'him');
G.reset(); G.root.updateMatrixWorld(true);
const EAR_L = V(0.08, 1.64, 0.01).applyMatrix4(G.bones.head.matrixWorld.clone().invert());
// ================================================================== SURVIVING WITHOUT FOOD AND WATER
// ------------------------------------------------------------------ the woods: leaf litter, trees all around, a stream, a few rocks; the sky goes day -> night (beat 1)
scene.remove(lamp);
const DAY = new THREE.Color(0x9cc6e6), NIGHT = new THREE.Color(0x0b1226);
const STREAMZ = -2.3;
const woods = new THREE.Group(); scene.add(woods);
const leafTex = canvasTex(512, 512, g => { g.fillStyle = '#5a4a2e'; g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 2600; i++) { const c = ['#7a5a2a', '#9a6a2a', '#5a3a1a', '#6a7a3a', '#8a4a1a', '#4a3a22'][i % 6]; g.fillStyle = c; g.save(); g.translate(Math.random() * 512, Math.random() * 512); g.rotate(Math.random() * 6.28); g.beginPath(); g.ellipse(0, 0, 4 + Math.random() * 6, 2 + Math.random() * 3, 0, 0, 6.28); g.fill(); g.restore(); } });
leafTex.wrapS = leafTex.wrapT = THREE.RepeatWrapping; leafTex.repeat.set(10, 10);
const ground = new THREE.Mesh(new THREE.PlaneGeometry(40, 40).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ map: leafTex, roughness: 0.95 })); ground.receiveShadow = true; woods.add(ground);
const barkTex = canvasTex(128, 512, g => { g.fillStyle = '#4a3a2c'; g.fillRect(0, 0, 128, 512); for (let i = 0; i < 70; i++) { g.strokeStyle = `rgba(${20 + Math.random() * 30 | 0},${15 + Math.random() * 20 | 0},10,0.7)`; g.lineWidth = 2 + Math.random() * 4; g.beginPath(); const x = Math.random() * 128; g.moveTo(x, 0); g.bezierCurveTo(x + 10, 170, x - 10, 340, x + 4, 512); g.stroke(); } });
barkTex.wrapS = barkTex.wrapT = THREE.RepeatWrapping;
const barkM = new THREE.MeshStandardMaterial({ map: barkTex, roughness: 0.95 }), leavesM = [0x2f5a2a, 0x3a6a30, 0x274a24].map(c => mat(c, 0.9));
function tree(x, z, h, r, low = 1.4) { const t = new THREE.Mesh(new THREE.CylinderGeometry(r * 0.6, r, h, 12), barkM); t.position.set(x, h / 2, z); t.castShadow = true; t.receiveShadow = true; woods.add(t);
  const n = 4; for (let k = 0; k < n; k++) { const y = low + (h - low) * k / (n - 1), w = (1.5 - 1.1 * k / (n - 1)) * (0.8 + 0.4 * hash1(x * 3 + k)); const c = new THREE.Mesh(new THREE.ConeGeometry(w, 1.7, 10), leavesM[(k + Math.round(x * 3)) % 3]); c.position.set(x, y + 0.6, z); c.castShadow = true; woods.add(c); } return t; }   // a pine: skirts of needles from low down
for (let i = 0; i < 70; i++) { const a = hash1(i * 3.1) * 6.283, d = 3.4 + 10 * hash1(i * 7.3); const x = Math.cos(a) * d, z = Math.sin(a) * d - 0.8;   // a clearing around him and the stream bank
  if (Math.abs(z - STREAMZ) < 1.0 && Math.abs(x) < 7) continue; tree(x, z, 5 + 3 * hash1(i * 5.5), 0.14 + 0.1 * hash1(i * 2.9)); }
for (let i = 0; i < 40; i++) { const a = hash1(i * 9.7) * 6.283, d = 2.6 + 8 * hash1(i * 1.9); const b = new THREE.Mesh(new THREE.IcosahedronGeometry(0.35 + 0.35 * hash1(i * 4.1), 1), leavesM[i % 3]);   // undergrowth
  b.position.set(Math.cos(a) * d, 0.2, Math.sin(a) * d - 0.8); if (Math.abs(b.position.z - STREAMZ) < 0.7) continue; b.scale.y = 0.6; b.castShadow = true; woods.add(b); }
for (let i = 0; i < 14; i++) { const r = new THREE.Mesh(new THREE.IcosahedronGeometry(0.15 + 0.2 * hash1(i * 4.4), 1), mat(0x7a7a72, 0.9)); r.position.set((hash1(i * 6.1) - 0.5) * 9, 0.05, -1.6 - hash1(i * 2.3) * 1.6); r.scale.y = 0.6; r.castShadow = true; woods.add(r); }
// the stream (z about -2.3): flowing water across the clearing
const waterTex = canvasTex(256, 256, g => { g.fillStyle = '#2a5a7a'; g.fillRect(0, 0, 256, 256); for (let i = 0; i < 160; i++) { g.strokeStyle = `rgba(200,230,255,${0.15 + Math.random() * 0.3})`; g.lineWidth = 1 + Math.random() * 2; g.beginPath(); const y = Math.random() * 256, x = Math.random() * 256; g.moveTo(x, y); g.lineTo(x + 20 + Math.random() * 40, y + (Math.random() - 0.5) * 4); g.stroke(); } });
waterTex.wrapS = waterTex.wrapT = THREE.RepeatWrapping; waterTex.repeat.set(6, 1);
const stream = new THREE.Mesh(new THREE.PlaneGeometry(14, 0.9).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ map: waterTex, roughness: 0.08, metalness: 0.2, color: 0xb0d8f0, emissive: 0x0a2030, emissiveIntensity: 0.4 })); stream.position.set(0, 0.012, STREAMZ); woods.add(stream);
// the tally tree (beat 6): one mark a day, carved in groups of five
const TALLY = V(1.7, 0, -1.4);
const tallyTree = tree(TALLY.x, TALLY.z, 6.0, 0.32, 2.6);
const tallyCanvas = document.createElement('canvas'); tallyCanvas.width = 512; tallyCanvas.height = 768; const tallyTex = new THREE.CanvasTexture(tallyCanvas); tallyTex.colorSpace = THREE.SRGBColorSpace;
let tallyState = -1;
function drawTally(n) { const g = tallyCanvas.getContext('2d'); g.clearRect(0, 0, 512, 768); g.strokeStyle = '#e8d6b0'; g.lineCap = 'round'; g.lineWidth = 9;
  for (let i = 0; i < n; i++) { const grp = Math.floor(i / 5), k = i % 5, gx = 40 + (grp % 4) * 115, gy = 190 + Math.floor(grp / 4) * 130;
    g.beginPath(); if (k < 4) { g.moveTo(gx + k * 20, gy); g.lineTo(gx + k * 20 + 3, gy + 85); } else { g.moveTo(gx - 10, gy + 70); g.lineTo(gx + 85, gy + 12); } g.stroke(); }
  tallyTex.needsUpdate = true; }
drawTally(0);
{ const pl = new THREE.Mesh(new THREE.CylinderGeometry(0.288, 0.3, 0.9, 24, 1, true, -0.95, 1.9), new THREE.MeshStandardMaterial({ map: tallyTex, transparent: true, roughness: 0.9, depthWrite: false })); pl.position.set(TALLY.x, 1.1, TALLY.z); pl.rotation.y = 0; woods.add(pl); }
const tallyLight = new THREE.PointLight(0xffe8c8, 0, 3, 1.5); tallyLight.position.copy(TALLY).add(V(0.3, 1.4, 0.9)); scene.add(tallyLight);
const moon = new THREE.Mesh(new THREE.SphereGeometry(0.6, 20, 12), new THREE.MeshBasicMaterial({ color: 0xf0f0e0 })); moon.position.set(-4, 9, -14); scene.add(moon);

// ------------------------------------------------------------------ his water bottle (empty, then filled at the stream)
const BTR = 0.034, BTH = 0.2;
const bottle = new THREE.Group(); scene.add(bottle);
{ const plastic = new THREE.MeshPhysicalMaterial({ color: 0xdff0ff, roughness: 0.08, transparent: true, opacity: 0.35, side: THREE.DoubleSide, depthWrite: false });
  const prof = [[0, 0], [BTR, 0.004], [BTR, 0.15], [0.016, 0.185], [0.014, 0.2]].map(([x, y]) => new THREE.Vector2(x, y));
  const shell = new THREE.Mesh(new THREE.LatheGeometry(prof, 28), plastic); bottle.add(shell);
  const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.016, 0.016, 0.018, 16), mat(0x2a6ad0, 0.4)); cap.position.y = 0.208; bottle.add(cap);
  const label = new THREE.Mesh(new THREE.CylinderGeometry(BTR + 0.001, BTR + 0.001, 0.05, 28, 1, true), mat(0x3a9ad8, 0.5)); label.position.y = 0.08; bottle.add(label); }
const bwM = new THREE.MeshStandardMaterial({ color: 0x7ac0ff, emissive: 0x1a4a7a, emissiveIntensity: 0.4, roughness: 0.05, transparent: true, opacity: 0.6 });
const bwater = new THREE.Mesh(new THREE.CylinderGeometry(BTR - 0.003, BTR - 0.003, 1, 24).translate(0, 0.5, 0), bwM); bwater.position.y = 0.005; bottle.add(bwater);
const drop = new THREE.Mesh(new THREE.SphereGeometry(0.008, 12, 8), bwM); drop.scale.y = 1.4; scene.add(drop);

// ------------------------------------------------------------------ x-ray: the glow body (same skeleton) with the kidneys, liver, heart, fat and muscle
const xrayMat = new THREE.MeshStandardMaterial({ color: 0x000000, emissive: 0x58b8ff, emissiveIntensity: 1, transparent: true, opacity: 1, depthWrite: false, blending: THREE.AdditiveBlending, roughness: 1, metalness: 0 });
xrayMat.onBeforeCompile = sh => { sh.fragmentShader = sh.fragmentShader.replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\n  totalEmissiveRadiance *= 0.015 + 0.85 * pow(1.0 - abs(dot(normalize(normal), normalize(vViewPosition))), 2.4);'); };
const XRAY = [], NORMAL = [];
G.root.traverse(o => { if (!o.isMesh || o.userData.xray) return; NORMAL.push(o); });
for (const o of Object.entries(G.meshes).filter(([n]) => !/^(hair|hairCards|sole)/.test(n)).map(([, m]) => m)) {
  let x; if (o.isSkinnedMesh) { x = new THREE.SkinnedMesh(o.geometry, xrayMat); x.bind(o.skeleton, o.bindMatrix); } else x = new THREE.Mesh(o.geometry, xrayMat);
  x.userData.xray = true; x.position.copy(o.position); x.quaternion.copy(o.quaternion); x.scale.copy(o.scale); x.frustumCulled = false; x.castShadow = false; x.renderOrder = 5; o.parent.add(x); XRAY.push(x); }
G.reset(); G.root.updateMatrixWorld(true);
const toLocal = (bone, p) => bone.worldToLocal(p.clone());
const HC = V(...G.man.headC);
// the heart: two lobes and a point, slightly to his left of centre; it squeezes with each beat
// the organs (in his rest pose: he faces -z, his left is -x)
const organ = (c, e, k = 0.8, op = 0.85) => new THREE.MeshStandardMaterial({ color: c, emissive: e, emissiveIntensity: k, roughness: 0.45, transparent: true, opacity: op });
// (rest pose: he faces -z, his left is -x)
const kidM = organ(0x7a2a2a, 0xff5a4a, 0.7), liverM = organ(0x6a1a1a, 0xc03a2a, 0.6), heartM = organ(0x8a1a2a, 0xff2a3a, 0.9, 1);
const KID = []; for (const s of [-1, 1]) { const k = new THREE.Mesh(new THREE.SphereGeometry(0.045, 20, 14), kidM); k.scale.set(0.6, 1.0, 0.5); G.bones.spine1.add(k); k.position.copy(toLocal(G.bones.spine1, V(s * 0.06, 1.06, 0.05))); KID.push(k); }
const liver = new THREE.Mesh(new THREE.SphereGeometry(0.07, 28, 18), liverM); G.bones.spine2.add(liver); liver.scale.set(1.35, 0.7, 0.9); liver.position.copy(toLocal(G.bones.spine2, V(0.06, 1.14, -0.03)));
const heart = new THREE.Group(); G.bones.chest.add(heart); heart.position.copy(toLocal(G.bones.chest, V(-0.025, 1.31, -0.04)));
{ const hg = new THREE.Group(); heart.add(hg); hg.rotation.z = -0.45; hg.rotation.x = 0.2;
  for (const s of [-1, 1]) { const l = new THREE.Mesh(new THREE.SphereGeometry(0.03, 24, 16), heartM); l.position.set(s * 0.02, 0.012, 0); hg.add(l); }
  const pt = new THREE.Mesh(new THREE.ConeGeometry(0.043, 0.07, 24).rotateX(Math.PI), heartM); pt.position.y = -0.03; pt.scale.z = 0.75; hg.add(pt); }
// fat: a soft yellow layer around his belly (beat 4 burns it down); muscle: red bands on his upper arms and thighs (beat 5 wastes them)
const fatM = organ(0xffd84a, 0xc09a10, 0.5, 0.5); fatM.depthWrite = false;
const fat = new THREE.Mesh(new THREE.SphereGeometry(0.16, 32, 20), fatM); G.bones.spine1.add(fat); fat.scale.set(1.0, 0.75, 0.85); fat.position.copy(toLocal(G.bones.spine1, V(0, 1.02, -0.01)));
const FAT0 = fat.scale.clone();
const muscM = organ(0xb02a2a, 0xff4a3a, 0.7, 0.8);
const MUSC = []; for (const [bn, len, r] of [['uarmR', 0.2, 0.034], ['uarmL', 0.2, 0.034], ['thighR', 0.3, 0.05], ['thighL', 0.3, 0.05]]) {
  const b = G.bones[bn], c = bn.startsWith('thigh') ? 'shin' + bn.slice(-1) : 'farm' + bn.slice(-1), a = wp(b), e = wp(G.bones[c]);
  const m = new THREE.Mesh(new THREE.CapsuleGeometry(r, len, 6, 14), muscM); const mid = a.clone().lerp(e, 0.5); b.add(m); m.position.copy(toLocal(b, mid));
  const dirL = e.clone().sub(a).normalize().applyQuaternion(wq(b).invert()); m.quaternion.setFromUnitVectors(V(0, 1, 0), dirL); MUSC.push(m); }
const dotTex = canvasTex(64, 64, g => { const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.4, 'rgba(255,255,255,0.6)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); });
function dots(n, color, size) { const g = new THREE.BufferGeometry(); const p = new Float32Array(n * 3); g.setAttribute('position', new THREE.BufferAttribute(p, 3)); g.setDrawRange(0, 0);
  const m = new THREE.Points(g, new THREE.PointsMaterial({ color, size, map: dotTex, transparent: true, depthWrite: false, depthTest: false, blending: THREE.AdditiveBlending, toneMapped: false })); m.frustumCulled = false; m.renderOrder = 9; scene.add(m); return { m, p, n }; }
const SUG = dots(200, 0xffffff, 0.022), FUEL = dots(200, 0xffc040, 0.024), WASTE = dots(160, 0x9a7a3a, 0.02);
const ORGANS = [...KID, liver, heart, fat, ...MUSC];
let XRON = false, XRNEW = false;
function setXray(k) { if ((k > 0.01) !== XRON) { XRON = k > 0.01; XRNEW = XRON; }   // the first draw after the ghost comes on comes out blank: draw() renders that frame twice
  for (const x of XRAY) x.visible = k > 0.01; xrayMat.emissiveIntensity = 0.75 * k;
  for (const o of NORMAL) o.visible = k < 0.6; for (const o of ORGANS) o.visible = k > 0.5; }

// ------------------------------------------------------------------ the story
const STANDP = V(0.15, 0, 0.3), STREAMP = V(0.1, 0, STREAMZ + 0.75);   // lost in the clearing / at the stream bank (he faces -z)
const YAW = 0;
const LOOPSEED = { R: null, L: null };
function blinkAt(s) { const u = ((s + 40) % 3.7) / 0.16; return u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0; }
const F = fwdOf(YAW), Rt = rightOf(YAW), UP = V(0, 1, 0);
const STAND1 = { ...addPose(STAND, { spine1: [-4, 0, 0], neck: [6, 0, 0] }), armL: A(10, 14, 0, 22), armR: A(10, 14, 0, 22) };
// the bottle in his left hand: palm on its side (palm to his right), fingers around it; c = bottom, axis = bottom -> top
const GRIP = 0.012;
function bottleHand(c, axis) { const n = Rt.clone().addScaledVector(F, 0.25); n.addScaledVector(axis, -n.dot(axis)).normalize();
  const u = new THREE.Vector3().crossVectors(axis, n).normalize();
  return { S: 'L', p: c.clone().addScaledVector(axis, BTH * 0.42).addScaledVector(n, -(BTR + GRIP)), n, u, c: 50, th: 42, opp: 40, memAbs: 'bottleL', seed: A(40, 15, 0, 80, 10) }; }
const tipAxis = th => UP.clone().multiplyScalar(Math.cos(th * D2R)).addScaledVector(F, -Math.sin(th * D2R));
function atMouth(th) { const ax = tipAxis(th), rim = RG.mouthW().addScaledVector(F, 0.014).add(V(0, 0.004, 0)).addScaledVector(Rt, 0.01); return { c: rim.clone().addScaledVector(ax, -BTH), ax }; }
const tipSide = th => UP.clone().multiplyScalar(Math.cos(th * D2R)).addScaledVector(Rt, Math.sin(th * D2R));   // tipped over sideways (shaking it out)

// the state at a time ----------------------------------------------
function guyAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  const face = { blink: blinkAt(lt + b * 1.3) };
  let pose = STAND1, root = { x: STANDP.x, y: 0.95, z: STANDP.z, yaw: YAW }, hands = [], show = true, cut = false;
  let night = 0.15, bc = null, bax = UP.clone(), bfill = 0, dropT = -1, xr = 0, kidK = 0, sugarK = 0, fatK = 0, fuel = 0, muscK = 0, weak = 0, tally = 0, tallyShot = false, stream = false;
  if (b === 7 || b === 0) {                                         // lost: he looks around; then he turns the empty bottle over and shakes it - one drop
    night = 0.45;
    const look = b === 7 ? Math.sin(lt / d * 2 * Math.PI) : 0;      // one look left and right, back to centre at the loop
    if (b === 7) { bc = V(-0.08, 1.05, -0.3).add(STANDP); bax = UP.clone();
      pose = addPose(STAND1, { neck: [-2, 26 * look, 0], head: [0, 12 * look, 0] }); Object.assign(face, { look: [0.4 * look, 0], brow: 0.6, fear: 0.4 }); }
    else { const up = smooth(0.0, 1.0, lt), head = smooth(0.3, 1.0, lt), shake = lt > 1.0 && lt < 2.4 ? Math.sin((lt - 1.0) * 15) * smooth(1.0, 1.2, lt) * (1 - smooth(2.2, 2.4, lt)) : 0;
      const m = atMouth(140 + 4 * shake); m.c.addScaledVector(m.ax, -0.06);                   // upside down over his open mouth, a few cm up: shaking out the last drop
      bax = UP.clone().lerp(m.ax, up).normalize(); bc = V(-0.08, 1.05, -0.3).add(STANDP).lerp(m.c, sm(up)).add(V(0, 0.012 * shake, 0)); dropT = lt - 1.6;
      pose = addPose(STAND1, { neck: [16 * head, 0, 0], head: [14 * head, 0, 0], spine1: [-4 * head, 0, 0] }); Object.assign(face, { look: [0, 0.5 * head], brow: 0.7, fear: 0.4, oh: 0.6 * head, jaw: 0.4 * head }); }
    hands = [b === 0 && LOOPSEED.L ? { ...bottleHand(bc, bax), seed: LOOPSEED.L, seedIsPrev: true } : bottleHand(bc, bax)];
  } else if (b === 1) {                                             // three days: day and night race past; he wilts
    const k = smooth(0, d, lt); night = 0.5 - 0.5 * Math.cos(lt / d * 3 * 2 * Math.PI);   // three nights
    weak = k; bc = V(-0.14, 0.88 - 0.03 * k, -0.14).add(STANDP); hands = [bottleHand(bc, bax)];
    pose = addPose(STAND1, { spine1: [10 * k, 0, 0], spine2: [6 * k, 0, 0], neck: [-10 * k, 0, 0], head: [-6 * k, 0, 0] }); root.y = 0.95 - 0.03 * k;
    Object.assign(face, { squint: 0.4 * k, brow: 0.5 * k, jaw: 0.15 * k, look: [0, -0.3 * k] });
  } else if (b === 2) {                                             // x-ray: the kidneys can't clear the waste; it all dims
    xr = 1; kidK = smooth(0.3, d - 0.5, lt); weak = 1; night = 0.2;
    pose = addPose(STAND1, { spine1: [10, 0, 0], spine2: [6, 0, 0], neck: [-10, 0, 0] });
  } else if (b === 3) {                                             // the stream: he fills the bottle and drinks
    root = { x: STREAMP.x, y: 0.95, z: STREAMP.z, yaw: YAW }; stream = true; night = 0.1; bfill = 0.85;
    const up = smooth(0.1, 0.9, lt), tip = smooth(0.4, 1.2, lt), head = smooth(0.6, 1.2, lt), m = atMouth(105 * tip);
    bax = UP.clone().lerp(m.ax, tip).normalize(); bc = V(-0.08, 1.05, -0.3).add(STREAMP).lerp(m.c, sm(up)); hands = [bottleHand(bc, bax)];
    pose = addPose(STAND1, { neck: [14 * head, 0, 0], head: [12 * head, 0, 0], spine1: [-3 * head, 0, 0] });
  } else if (b === 4) {                                             // x-ray: the sugar in the liver runs out (day 1), then the fat starts to burn
    xr = 1; sugarK = 1 - smooth(0.2, 1.6, lt); fatK = smooth(1.4, d, lt); fuel = smooth(1.3, 1.8, lt);
  } else if (b === 5) {                                             // x-ray: then the muscle; he gets weaker
    xr = 1; fatK = 1; muscK = smooth(0.2, d - 0.3, lt); fuel = 1; weak = muscK;
    pose = addPose(STAND1, { spine1: [8 * weak, 0, 0], spine2: [6 * weak, 0, 0], neck: [-8 * weak, 0, 0] }); root.y = 0.95 - 0.03 * weak;
  } else if (b === 6) {                                             // with water: weeks, up to about two months (a tally on a tree)
    show = false; tallyShot = true; tally = Math.round(60 * smooth(0.2, d - 0.3, lt)); night = 0.15;
  }
  const wb = 2 * Math.PI * Math.round(TOTAL / 2.6) / TOTAL;           // breathing (whole cycles over the loop)
  pose = addPose(pose, { spine1: [0.9 * Math.sin(wb * t), 0, 0], spine2: [0.6 * Math.sin(wb * t + 0.4), 0, 0], neck: [0.7 * Math.sin(wb * t + 1.1), 0, 0] });
  return { b, lt, d, pose, root, hands, show, cut, night, bc, bax, bfill, dropT, xr, kidK, sugarK, fatK, fuel, muscK, weak, tally, tallyShot, stream, face };
}

// ------------------------------------------------------------------ cameras
const CAM7 = { pos: V(-0.75, 1.62, -1.25), tgt: V(0.05, 1.25, 0.3), fov: 46 };      // in front of him, a little to his left (his left hand holds the bottle: knuckles to us): his face, the bottle, dark trees behind
function camAt(t, g) {
  const b = g.b, lt = g.lt, d = g.d, k = smooth(0, d, lt);
  if (b === 7) return { pos: CAM7.pos.clone().add(V(-0.06 * (1 - k), 0, -0.1 * (1 - k))), tgt: CAM7.tgt, fov: CAM7.fov };
  if (b === 0) return { pos: CAM7.pos.clone().lerp(V(-0.25, 1.62, -1.25), sm(Math.min(1, lt / 0.8))), tgt: CAM7.tgt.clone().lerp(V(0.08, 1.48, 0.3), sm(Math.min(1, lt / 0.8))), fov: 46 };
  if (b === 1) return { pos: V(-1.4, 1.9, -2.2).lerp(V(-1.2, 1.6, -1.9), k), tgt: V(0.1, 1.0, 0.3), fov: 48 };
  if (b === 2) return { pos: V(-0.3, 1.3, -0.75), tgt: V(0.15, 1.08, 0.3), fov: 44 };
  if (b === 3) return { pos: V(-0.75, 1.4, STREAMZ - 0.45), tgt: V(0.12, 1.15, STREAMP.z), fov: 48 };
  if (b === 4 || b === 5) return { pos: V(-0.3, 1.25, -0.85 + 0.05 * k), tgt: V(0.15, 1.08, 0.3), fov: 46 };
  if (b === 6) return { pos: TALLY.clone().add(V(-0.15, 1.25, 1.9 - 0.3 * k)), tgt: TALLY.clone().add(V(0, 1.12, 0)), fov: 40 };
  return CAM7;
}

// ------------------------------------------------------------------ clipping: him vs the floor and his own body
const SOLIDS = [];
const sbox = (name, obj, min, max) => SOLIDS.push({ name, obj, box: new THREE.Box3(min, max) });

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
const basisQ = (x, y) => { const X = x.clone().normalize(), Y = y.clone().addScaledVector(X, -y.dot(X)).normalize(), Z = new THREE.Vector3().crossVectors(X, Y); return new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(X, Y, Z)); };
function update(t, frame) {
  t = ((t % TOTAL) + TOTAL) % TOTAL;
  let g = guyAt(t); STATE = { b: g.b };
  scene.updateMatrixWorld(true);
  G.root.visible = g.show;
  RG.applyPose(g.pose, g.root);
  const yaw = g.root.yaw, f = fwdOf(yaw), r = rightOf(yaw);
  for (const [S, sx] of [['R', 0.11], ['L', -0.11]]) {
    const fp = V(g.root.x, 0, g.root.z).addScaledVector(r, sx).addScaledVector(f, S === 'R' ? 0.02 : -0.02);
    fp.y = ANKLEH; RG.foot(S, fp, fp.clone().add(V(0, 0.45, 0)).addScaledVector(f, 1), yawQ(yaw)); }
  G.root.updateMatrixWorld(true);
  const list = [];
  if (g.show) { BODYNOW = surfNow(); const g2 = guyAt(t); g.hands = g2.hands; g.bc = g2.bc; g.bax = g2.bax; for (const h of g.hands) list.push(h); }
  for (const h of list) if (h.memAbs) h.memAbs += ':' + g.b;            // a hold never carries across a cut (chunks start each beat cold, so must a straight render)
  if (list.length) { RG.hands(list, 'b' + g.b, frame); LASTH = list; }
  for (const S of ['R', 'L']) if (!list.some(h => h.S === S)) delete RG.LAST['cost' + S];
  G.root.updateMatrixWorld(true); RG.untwist(); G.face(g.face); G.root.updateMatrixWorld(true);
  // the bottle: where the story puts it (his hand holds it there); the last drop falling out
  bottle.visible = g.show && !!g.bc && g.xr < 0.5;
  if (bottle.visible) { bottle.position.copy(g.bc); bottle.quaternion.copy(basisQ(new THREE.Vector3().crossVectors(g.bax, Rt).lengthSq() > 1e-4 ? new THREE.Vector3().crossVectors(g.bax, F) : Rt, g.bax)); }
  bwater.visible = g.bfill > 0.01; bwater.scale.y = Math.max(0.001, g.bfill * 0.18);
  drop.visible = g.dropT >= 0 && g.dropT < 0.6 && bottle.visible;
  if (drop.visible) { const mouth = bottle.localToWorld(V(0, 0.21, 0)), lips = RG.mouthW(); drop.position.copy(mouth).lerp(lips, Math.min(1, g.dropT / 0.2)); drop.visible = g.dropT < 0.2; }
  // x-ray organs
  setXray(g.xr);
  kidM.emissiveIntensity = 0.7 * (1 - 0.85 * g.kidK); kidM.color.set(0x7a2a2a).lerp(new THREE.Color(0x3a3a3a), g.kidK); heartM.emissiveIntensity = 0.9 * (1 - 0.6 * g.kidK) * (g.b === 2 ? 1 : 1);
  { const pz = Math.exp(-((((t * (75 + 40 * g.kidK) / 60) % 1 - 0.05) / 0.06) ** 2)); heart.scale.setScalar(1 + 0.1 * pz * (1 - 0.5 * g.kidK)); }
  fat.scale.copy(FAT0).multiplyScalar(Math.max(0.2, 1 - 0.55 * g.fatK)); fatM.emissiveIntensity = 0.5 + 0.6 * g.fuel * (g.b === 4 ? 1 : 0.4) * (0.7 + 0.3 * Math.sin(t * 9));
  MUSC.forEach((m, i) => { m.scale.set(1 - 0.5 * g.muscK, 1, 1 - 0.5 * g.muscK); }); muscM.emissiveIntensity = 0.7 + 0.6 * g.muscK * (0.6 + 0.4 * Math.sin(t * 8));
  { // sugar sparks leaving the liver (beat 4, first part); orange fuel flowing from the fat (beat 4 on) and from the muscles (beat 5); brown waste piling in the blood (beat 2)
    const lv = wp(liver), fc = wp(fat), sp = wp(G.bones.spine2), up = V(0, 1, 0);
    let n = g.xr > 0.5 ? Math.round(SUG.n * g.sugarK) : 0;
    for (let i = 0; i < n; i++) { const a = ((t * (0.4 + 0.3 * hash1(i * 4.1)) + hash1(i * 2.7)) % 1), dir = V(hash1(i * 6.1) - 0.5, hash1(i * 3.3) - 0.3, hash1(i * 8.3) - 0.5).normalize();
      const p = lv.clone().addScaledVector(dir, 0.04 + 0.25 * a); SUG.p.set([p.x, p.y, p.z], i * 3); }
    SUG.m.geometry.setDrawRange(0, n); SUG.m.geometry.attributes.position.needsUpdate = true; SUG.m.visible = n > 0;
    n = g.xr > 0.5 ? Math.round(FUEL.n * g.fuel) : 0;
    for (let i = 0; i < n; i++) { const fromM = g.b === 5 && i % 2 === 0, src = fromM ? wp(MUSC[i % 4]) : fc, a = ((t * (0.5 + 0.3 * hash1(i * 3.9)) + hash1(i * 1.3)) % 1);
      const p = src.clone().lerp(sp.clone().add(V(0, 0.12, 0)), a).add(V(vn1(t + i, 1) * 0.03, vn1(t + i, 2) * 0.03, vn1(t + i, 3) * 0.03)); FUEL.p.set([p.x, p.y, p.z], i * 3); }
    FUEL.m.geometry.setDrawRange(0, n); FUEL.m.geometry.attributes.position.needsUpdate = true; FUEL.m.visible = n > 0;
    n = g.xr > 0.5 ? Math.round(WASTE.n * g.kidK) : 0;
    for (let i = 0; i < n; i++) { const a = ((t * (0.15 + 0.1 * hash1(i * 4.1)) + hash1(i * 2.7)) % 1), ang = hash1(i * 6.1) * 6.283, y = (hash1(i * 3.3) - 0.4) * 0.6;
      const p = sp.clone().addScaledVector(up, y).add(V(Math.cos(ang + a) * 0.12, 0, Math.sin(ang + a) * 0.08)); WASTE.p.set([p.x, p.y, p.z], i * 3); }
    WASTE.m.geometry.setDrawRange(0, n); WASTE.m.geometry.attributes.position.needsUpdate = true; WASTE.m.visible = n > 0; }
  // the tally on the tree
  if (g.tally !== tallyState) { drawTally(g.tally); tallyState = g.tally; }
  waterTex.offset.x = -t * 0.35;
  // camera, sky and light
  const C = camAt(t, g); camera.position.copy(C.pos); camera.up.set(0, 1, 0); camera.lookAt(C.tgt); camera.fov = C.fov; camera.updateProjectionMatrix();
  const nt = g.night; scene.background = DAY.clone().lerp(NIGHT, nt); scene.fog = new THREE.Fog(scene.background, 7, 22);
  sun.position.set(3, 8, 4); sun.target.position.set(0, 0, 0); sun.target.updateMatrixWorld();
  sun.intensity = 2.4 * (1 - 0.85 * nt); sun.color.set(0xffe8c8).lerp(new THREE.Color(0x8aa0ff), nt); hemi.intensity = 0.8 * (1 - 0.6 * nt); scene.environmentIntensity = 0.3 * (1 - 0.5 * nt);
  moon.visible = nt > 0.3; tallyLight.intensity = g.tallyShot ? 4 : 0;
  return { beat: g.b, cut: g.cut };
}
G.reset(); G.root.updateMatrixWorld(true);
const ANKLEH = wp(G.bones.footR).y;

// ------------------------------------------------------------------ frame I/O (same contract as the other 3D Shorts)
const draw = () => { if (XRNEW) { renderer.render(scene, camera); XRNEW = false; } renderer.render(scene, camera); };
const gl = renderer.getContext(), px = new Uint8Array(W * H * 4);
let CUTF = false, LASTB = 0;
function segStart(t) { return B[beatAt(t)]; }                      // every hold starts cold at its beat (a jump replays from there)
function stepTo(i) { const t = i / FPS, tt = ((t % TOTAL) + TOTAL) % TOTAL;
  if (i !== LASTF + 1) for (let j = Math.ceil(segStart(tt) * FPS - 1e-6) + Math.floor(t / TOTAL) * Math.round(TOTAL * FPS); j < i; j++) update(j / FPS, j);
  const r = update(t, i); CUTF = r.cut; LASTB = r.beat; LASTF = i; }
// the loop: beat 0's bottle hand starts where beat 7 ends
for (let i = Math.ceil(B[7] * FPS); i < Math.round(TOTAL * FPS); i++) update(i / FPS, i);
LOOPSEED.L = RG.LAST.armL.slice();
draw(); update(B[4] + 1.5, -50); draw();     // warm-up: compile the x-ray shaders now
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
window.dbg = { G, RG, wp, THREE, LOOPSEED, update, guyAt, renderer, scene, camera, setBN: () => { BODYNOW = surfNow(); }, F, Rt, UP };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS);
window.READY = true;
