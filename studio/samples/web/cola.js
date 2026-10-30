// "You just cracked open your sixth can of cola today." - a 3D Short: what too much cola does (sugar, insulin, teeth, fat, potassium).
//   cola.html?w=1080&h=1920            (times from cola/times.json; one shot per narration line)
// Beats: 0 the can's just cracked, fizz sprays; he drinks (hook) | 1 ten spoons of sugar pop up next to it | 2 the daily max line: one can is past it
//        3 x-ray: blood sugar shoots up, the pancreas pumps out insulin | 4 a tooth up close: every sip washes acid over it, pits grow
//        5 x-ray: extra sugar stored as fat (the liver yellows) | 6 rare: low potassium, his arm goes weak, the can drops | 7 he grabs the next can (loops)
// The can is a made-up brand (no real logo).
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { loadGuy } from '/guy3d.js';

const Q = new URLSearchParams(location.search);
const W = +Q.get('w') || 720, H = +Q.get('h') || 1280;
const FPS = 30;
const TIMES = await (await fetch('/cola/times.json')).json();
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

// ------------------------------------------------------------------ the home: living room with a kitchen corner
const home = new THREE.Group(); scene.add(home);
const floorTex = canvasTex(1024, 1024, g => { for (let i = 0; i < 16; i++) { const c = 150 + 30 * Math.random(); g.fillStyle = `rgb(${c},${c * 0.72 | 0},${c * 0.5 | 0})`; g.fillRect(0, i * 64, 1024, 64);
  for (let k = 0; k < 40; k++) { g.strokeStyle = `rgba(80,50,30,${0.06 + Math.random() * 0.08})`; g.beginPath(); const y = i * 64 + Math.random() * 64; g.moveTo(0, y); g.bezierCurveTo(300, y + 6, 700, y - 6, 1024, y + 3); g.stroke(); }
  g.fillStyle = 'rgba(40,25,15,0.6)'; g.fillRect(0, i * 64, 1024, 2); for (let s = 0; s < 3; s++) g.fillRect(((i * 397 + s * 331) % 1024), i * 64, 2, 64); } });
floorTex.wrapS = floorTex.wrapT = THREE.RepeatWrapping; floorTex.repeat.set(4, 4);
const floor = new THREE.Mesh(new THREE.PlaneGeometry(12, 12).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ map: floorTex, roughness: 0.55 })); floor.receiveShadow = true; home.add(floor);
const rug = new THREE.Mesh(new THREE.PlaneGeometry(2.6, 3.4).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ map: canvasTex(256, 340, g => { g.fillStyle = '#8a3a34'; g.fillRect(0, 0, 256, 340); g.strokeStyle = '#e8d2a8'; g.lineWidth = 8; g.strokeRect(14, 14, 228, 312); g.strokeStyle = '#3a4a6a'; g.lineWidth = 5; g.strokeRect(30, 30, 196, 280); }), roughness: 0.95 }));
rug.position.set(0, 0.004, 0.1); rug.receiveShadow = true; home.add(rug);
const wallM = mat(0xe8dcc6, 0.9);
box(12, 3.2, 0.12, 0, 1.6, -3.26, wallM, 0, home); box(0.12, 3.2, 12, -3.06, 1.6, 0, mat(0xd9e2d6, 0.9), 0, home);
box(12, 0.12, 0.04, 0, 0.06, -3.19, mat(0xf4efe4, 0.6), 0, home);
// window (bright) in the back wall
{ const wtex = canvasTex(256, 256, g => { const gr = g.createLinearGradient(0, 0, 0, 256); gr.addColorStop(0, '#bfe0ff'); gr.addColorStop(0.65, '#e9f4ff'); gr.addColorStop(0.66, '#7fae6a'); gr.addColorStop(1, '#5f8e4c'); g.fillStyle = gr; g.fillRect(0, 0, 256, 256); });
  const wi = new THREE.Mesh(new THREE.PlaneGeometry(1.5, 1.3), new THREE.MeshBasicMaterial({ map: wtex, toneMapped: false })); wi.position.set(1.6, 1.65, -3.19); home.add(wi);
  for (const [w, h, x, y] of [[1.66, 0.08, 1.6, 2.32], [1.66, 0.08, 1.6, 0.98], [0.08, 1.4, 0.81, 1.65], [0.08, 1.4, 2.39, 1.65], [0.05, 1.3, 1.6, 1.65], [1.5, 0.05, 1.6, 1.65]]) box(w, h, 0.06, x, y, -3.17, mat(0xf6f2ea, 0.5), 0, home); }
// couch on the back wall, coffee table to the right, lamp, plant
const couch = new THREE.Group(); couch.position.set(-1.3, 0, -2.75); home.add(couch);
{ const cm = mat(0x41607a, 0.85); box(2.2, 0.42, 0.9, 0, 0.27, 0, cm, 0.06, couch); box(2.2, 0.55, 0.22, 0, 0.7, -0.34, cm, 0.08, couch); for (const x of [-1.05, 1.05]) box(0.22, 0.6, 0.9, x, 0.35, 0, cm, 0.08, couch);
  for (const x of [-0.5, 0.5]) box(0.95, 0.14, 0.7, x, 0.55, 0.05, mat(0x4d6f8a, 0.9), 0.06, couch); box(0.4, 0.38, 0.12, -0.7, 0.75, -0.18, mat(0xe8b04a, 0.9), 0.06, couch); }
{ const lb = box(0.04, 1.6, 0.04, 2.2, 0.8, -2.6, mat(0x2a2a2e, 0.4, 0.6), 0, home); const sh = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.24, 0.3, 20, 1, true), new THREE.MeshStandardMaterial({ color: 0xf2e6cc, emissive: 0xffd9a0, emissiveIntensity: 0.6, side: THREE.DoubleSide })); sh.position.set(2.2, 1.7, -2.6); home.add(sh); }
// kitchen corner on the left wall: counter, cabinets, fridge
const counter = new THREE.Group(); counter.position.set(-2.7, 0, -0.6); home.add(counter);
{ box(0.62, 0.9, 3.0, 0, 0.45, 0, mat(0xf1ece2, 0.6), 0.02, counter); box(0.66, 0.05, 3.04, 0.02, 0.92, 0, mat(0x3a3a40, 0.3), 0.01, counter);
  for (let i = 0; i < 4; i++) box(0.02, 0.7, 0.68, 0.32, 0.45, -1.1 + i * 0.73, mat(0xe6dfd2, 0.5), 0, counter);
  box(0.4, 0.7, 3.0, -0.1, 2.15, 0, mat(0xf1ece2, 0.6), 0.02, counter);
  box(0.7, 1.9, 0.75, 0, 0.95, 1.95, mat(0xdfe3e6, 0.3, 0.3), 0.04, counter); box(0.03, 0.5, 0.03, 0.36, 1.2, 1.7, mat(0x9aa0a6, 0.3, 0.8), 0, counter); }
// the wall clock (beat 4: time races)
const clock = new THREE.Group(); clock.position.set(-0.1, 2.25, -3.18); home.add(clock);
const clockHands = {};
{ const face = new THREE.Mesh(new THREE.CylinderGeometry(0.26, 0.26, 0.04, 40).rotateX(Math.PI / 2), mat(0xfaf6ee, 0.5)); clock.add(face);
  const rim = new THREE.Mesh(new THREE.TorusGeometry(0.26, 0.025, 10, 40), mat(0x2a2a2e, 0.4, 0.5)); clock.add(rim);
  for (let i = 0; i < 12; i++) { const tk = new THREE.Mesh(new THREE.BoxGeometry(0.012, i % 3 ? 0.03 : 0.05, 0.01), mat(0x222222)); const a = i / 12 * Math.PI * 2; tk.position.set(Math.sin(a) * 0.21, Math.cos(a) * 0.21, 0.025); tk.rotation.z = -a; clock.add(tk); }
  for (const [k, l, w, c] of [['h', 0.12, 0.018, 0x222222], ['m', 0.19, 0.012, 0x222222], ['s', 0.21, 0.005, 0xd02020]]) { const piv = new THREE.Group(); piv.position.z = 0.03 + (k === 's' ? 0.01 : 0); const hd = new THREE.Mesh(new THREE.BoxGeometry(w, l, 0.006), mat(c, 0.5)); hd.position.y = l / 2 - 0.02; piv.add(hd); clock.add(piv); clockHands[k] = piv; } }
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
// ================================================================== TOO MUCH COLA
// ------------------------------------------------------------------ the counter: the 6th can (to his left), five empties; ten spoons of sugar for beats 1-2
const TOPC = 0.945;                                                // counter top height
const STANDP = V(-2.03, 0, -0.62);                                 // where he stands (facing -x)
clock.visible = false;
const CANR = 0.033, CANH = 0.122;                                  // a 12 oz can
const canTex = canvasTex(256, 128, g => { const gr = g.createLinearGradient(0, 0, 0, 128); gr.addColorStop(0, '#e0141e'); gr.addColorStop(1, '#a00a12'); g.fillStyle = gr; g.fillRect(0, 0, 256, 128);
  g.fillStyle = 'rgba(255,255,255,0.85)'; for (let i = 0; i < 26; i++) { g.beginPath(); g.arc(150 + Math.random() * 100, 10 + Math.random() * 108, 2 + Math.random() * 5, 0, 6.28); g.fill(); }   // bubbles (no real brand's marks)
  g.font = 'bold 44px sans-serif'; g.fillStyle = '#ffffff'; g.textAlign = 'center'; g.fillText('COLA', 80, 62); g.font = 'bold 16px sans-serif'; g.fillText('CLASSIC FIZZ', 80, 92); });
const alu = mat(0xc8ccd2, 0.25, 0.9);
function makeCan(crushed = 0) { const g = new THREE.Group();
  const body = new THREE.Mesh(new THREE.CylinderGeometry(CANR, CANR, CANH - 0.016, 36, 1, true), new THREE.MeshStandardMaterial({ map: canTex, roughness: 0.3, metalness: 0.5 })); body.position.y = CANH / 2; g.add(body);
  for (const [y, r0, r1] of [[0.004, CANR * 0.82, CANR], [CANH - 0.004, CANR, CANR * 0.82]]) { const n = new THREE.Mesh(new THREE.CylinderGeometry(y > 0.1 ? r1 : r1, y > 0.1 ? r0 : r0, 0.008, 36), alu); n.position.y = y; g.add(n); }
  const lid = new THREE.Mesh(new THREE.CylinderGeometry(CANR * 0.8, CANR * 0.8, 0.003, 30), alu); lid.position.y = CANH; g.add(lid);
  const tab = new THREE.Mesh(new RoundedBoxGeometry(0.014, 0.002, 0.024, 1, 0.001), alu); tab.position.set(0, CANH + 0.003, 0.006); g.add(tab);
  const hole = new THREE.Mesh(new THREE.CircleGeometry(0.007, 16).rotateX(-Math.PI / 2), mat(0x111111, 0.6)); hole.position.set(0, CANH + 0.0018, -0.012); hole.scale.x = 1.3; g.add(hole);
  g.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  if (crushed) g.scale.set(1 + 0.15 * crushed, 1 - 0.3 * crushed, 1 - 0.1 * crushed);
  return g; }
const CAN0 = V(-2.43, TOPC, -0.24);                                  // the 6th can (to his left)
let CANYAW = -88, CANSPIN = 0;                                     // which way its label faces: on the counter (deg) / in his hand (rad)
const can = makeCan(); can.position.copy(CAN0); scene.add(can);
for (const [x, z, ry, side, cr] of [[-2.55, -1.0, 0.4, 0, 0.6], [-2.47, -1.1, 2.1, 0, 0], [-2.6, -0.87, 0, 1, 0.3], [-2.62, -1.2, 1.0, 0, 0.4], [-2.52, -1.28, 2.6, 1, 0]]) {
  const e = makeCan(cr); e.rotation.y = ry; if (side) { e.rotation.set(0, ry, Math.PI / 2); e.position.set(x, TOPC + CANR * 1.05, z); } else e.position.set(x, TOPC, z); scene.add(e); }
// fizz: tiny foam beads shooting out of the opening (beat 0, the can was just cracked) and the puddle when it's dropped (beat 6)
const fizzM = new THREE.MeshStandardMaterial({ color: 0xd8b48a, emissive: 0x3a2010, emissiveIntensity: 0.3, roughness: 0.3, transparent: true, opacity: 0.9 });
const FIZZN = 160, fizz = new THREE.InstancedMesh(new THREE.SphereGeometry(1, 8, 6), fizzM, FIZZN); fizz.frustumCulled = false; scene.add(fizz);
const puddle = new THREE.Mesh(new THREE.CircleGeometry(1, 40).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0x3a1a08, roughness: 0.05, metalness: 0.2, transparent: true, opacity: 0.85 })); puddle.position.y = 0.003; scene.add(puddle);
// ten sugar cubes (a teaspoon each) stacked into a tower beside the can; a red DAILY MAX line above the 9th
const CUBE = 0.02, TOWER = V(-2.515, TOPC, -0.18);
const sugarM = new THREE.MeshStandardMaterial({ map: canvasTex(64, 64, g => { g.fillStyle = '#f6f4ee'; g.fillRect(0, 0, 64, 64); for (let i = 0; i < 400; i++) { g.fillStyle = Math.random() < 0.5 ? '#ffffff' : '#d6d2c8'; g.fillRect(Math.random() * 64, Math.random() * 64, 2, 2); } }), roughness: 0.75 });
const cube10M = sugarM.clone(); cube10M.emissive = new THREE.Color(0xff2a20); cube10M.emissiveIntensity = 0;
const CUBES = []; for (let i = 0; i < 10; i++) { const c = new THREE.Mesh(new RoundedBoxGeometry(CUBE, CUBE, CUBE, 2, 0.002), i === 9 ? cube10M : sugarM); c.castShadow = true; c.receiveShadow = true; scene.add(c); CUBES.push(c); }
const limitM = new THREE.MeshBasicMaterial({ color: 0xff2a20, toneMapped: false, transparent: true });
const limitBar = new THREE.Mesh(new THREE.BoxGeometry(0.036, 0.004, 0.036), limitM); limitBar.position.copy(TOWER).add(V(0, 9 * CUBE + 0.001, 0)); scene.add(limitBar);
const limitTag = new THREE.Sprite(new THREE.SpriteMaterial({ map: canvasTex(512, 128, g => { g.fillStyle = 'rgba(200,20,20,0.92)'; g.beginPath(); g.roundRect(4, 4, 504, 120, 28); g.fill(); g.fillStyle = '#fff'; g.font = 'bold 60px sans-serif'; g.textAlign = 'center'; g.fillText('DAILY MAX', 256, 84); }), depthTest: false, toneMapped: false, transparent: true }));
limitTag.scale.set(0.09, 0.0225, 1); limitTag.renderOrder = 10; scene.add(limitTag);

// ------------------------------------------------------------------ x-ray: the glow body (same skeleton) with the stomach, pancreas and liver
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
const stomachM = organ(0x9a4a5a, 0xff7a90, 0.6), pancM = organ(0xb89a40, 0xffd060, 0.5), liverM = organ(0x6a1a1a, 0xc03a2a, 0.6);
const stomach = new THREE.Mesh(new THREE.SphereGeometry(0.05, 24, 16), stomachM); G.bones.spine2.add(stomach); stomach.scale.set(1.3, 0.9, 0.8); stomach.rotation.z = -0.5; stomach.position.copy(toLocal(G.bones.spine2, V(-0.05, 1.12, -0.04)));
const panc = new THREE.Mesh(new THREE.CapsuleGeometry(0.014, 0.1, 6, 12), pancM); G.bones.spine1.add(panc); panc.rotation.z = Math.PI / 2 - 0.2; panc.position.copy(toLocal(G.bones.spine1, V(-0.01, 1.06, -0.01)));
const liver = new THREE.Mesh(new THREE.SphereGeometry(0.07, 28, 18), liverM); G.bones.spine2.add(liver); liver.scale.set(1.35, 0.7, 0.9); liver.position.copy(toLocal(G.bones.spine2, V(0.06, 1.14, -0.03)));
const LIVER0 = liver.scale.clone();
// sugar in his blood (white sparks) and insulin (blue) from the pancreas; fat drops in the liver (yellow)
const dotTex = canvasTex(64, 64, g => { const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.4, 'rgba(255,255,255,0.6)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); });
function dots(n, color, size) { const g = new THREE.BufferGeometry(); const p = new Float32Array(n * 3); g.setAttribute('position', new THREE.BufferAttribute(p, 3)); g.setDrawRange(0, 0);
  const m = new THREE.Points(g, new THREE.PointsMaterial({ color, size, map: dotTex, transparent: true, depthWrite: false, depthTest: false, blending: THREE.AdditiveBlending, toneMapped: false })); m.frustumCulled = false; m.renderOrder = 9; scene.add(m); return { m, p, n }; }
const SUG = dots(320, 0xffffff, 0.022), INS = dots(120, 0x4aa8ff, 0.026);
const fatM = new THREE.MeshStandardMaterial({ color: 0xffd84a, emissive: 0xc09a10, emissiveIntensity: 0.6, roughness: 0.4 });
const fatDrops = []; for (let i = 0; i < 14; i++) { const m = new THREE.Mesh(new THREE.SphereGeometry(0.012 + 0.008 * hash1(i * 3.1), 12, 8), fatM); liver.add(m); m.position.set((hash1(i * 5.3) - 0.5) * 0.11, (hash1(i * 7.7) - 0.5) * 0.06, (hash1(i * 2.9) - 0.5) * 0.08); fatDrops.push(m); }
const ORGANS = [stomach, panc, liver];
let XRON = false, XRNEW = false;
function setXray(k) { if ((k > 0.01) !== XRON) { XRON = k > 0.01; XRNEW = XRON; }   // the first draw after the ghost comes on comes out blank: draw() renders that frame twice
  for (const x of XRAY) x.visible = k > 0.01; xrayMat.emissiveIntensity = 0.75 * k;
  for (const o of NORMAL) o.visible = k < 0.6; for (const o of ORGANS) o.visible = k > 0.5; }


// ------------------------------------------------------------------ a tooth up close (beat 4): every sip washes cola over it; acid eats pits into the enamel
const TOOTH = V(40, 0, 0);
const toothSet = new THREE.Group(); toothSet.position.copy(TOOTH); scene.add(toothSet);
const toothLight = new THREE.PointLight(0xffffff, 0, 4, 1.2); toothLight.position.set(0.25, 0.55, 0.6); toothSet.add(toothLight);
{ toothSet.add(new THREE.Mesh(new THREE.SphereGeometry(3, 32, 16), new THREE.MeshBasicMaterial({ color: 0x3a0a10, side: THREE.BackSide })));
  const gum = new THREE.Mesh(new RoundedBoxGeometry(1.4, 0.16, 0.5, 4, 0.07), new THREE.MeshStandardMaterial({ color: 0xd8607a, roughness: 0.5, emissive: 0x4a1020, emissiveIntensity: 0.3 })); gum.position.y = -0.02; toothSet.add(gum); }
const enamelTex = document.createElement('canvas'); enamelTex.width = 512; enamelTex.height = 512; const enamelMap = new THREE.CanvasTexture(enamelTex); enamelMap.colorSpace = THREE.SRGBColorSpace;
let pitState = -1;
function drawPits(k) { const g = enamelTex.getContext('2d'); g.fillStyle = '#f8f4ea'; g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 46; i++) { const a = clamp(k * 1.25 - hash1(i * 3.3) * 0.25, 0, 1); if (a <= 0) continue; const x = hash1(i * 5.1) * 512, y = 120 + hash1(i * 7.9) * 300, r = (4 + 16 * hash1(i * 2.2)) * a;
    const gr = g.createRadialGradient(x, y, 0, x, y, r); gr.addColorStop(0, 'rgba(90,60,30,0.95)'); gr.addColorStop(0.7, 'rgba(150,110,60,0.7)'); gr.addColorStop(1, 'rgba(200,170,120,0)'); g.fillStyle = gr; g.beginPath(); g.arc(x, y, r, 0, 6.28); g.fill(); }
  enamelMap.needsUpdate = true; }
drawPits(0);
const toothM = new THREE.MeshStandardMaterial({ map: enamelMap, roughness: 0.22, metalness: 0.02, color: 0xffffff, emissive: 0x6a6a66, emissiveIntensity: 0.45 });
const tooth = new THREE.Group(); toothSet.add(tooth); tooth.position.y = 0.0;
{ const prof = [[0.0, -0.02], [0.13, -0.02], [0.155, 0.05], [0.2, 0.17], [0.215, 0.26], [0.2, 0.31], [0.0, 0.31]].map(([x, y]) => new THREE.Vector2(x, y));
  const crown = new THREE.Mesh(new THREE.LatheGeometry(prof, 48), toothM); crown.scale.z = 0.85; tooth.add(crown);
  for (const [x, z] of [[-0.085, -0.07], [0.085, -0.07], [-0.085, 0.07], [0.085, 0.07]]) { const c = new THREE.Mesh(new THREE.SphereGeometry(0.105, 28, 18), toothM); c.scale.set(1, 0.55, 0.9); c.position.set(x, 0.31, z); tooth.add(c); } }
for (const x of [-0.48, 0.48]) { const t2 = tooth.clone(); t2.position.x = x; t2.scale.setScalar(0.9); toothSet.add(t2); }
const colaM = new THREE.MeshStandardMaterial({ color: 0x5a2a0e, emissive: 0x2a1004, roughness: 0.05, metalness: 0.1, transparent: true, opacity: 0.55, depthWrite: false });
const wave = new THREE.Mesh(new THREE.BoxGeometry(1.8, 1, 0.8).translate(0, 0.5, 0), colaM); wave.renderOrder = 6; toothSet.add(wave);
const BUBN = 90, bubs = new THREE.InstancedMesh(new THREE.SphereGeometry(1, 10, 8), new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xffe8d0, emissiveIntensity: 0.4, transparent: true, opacity: 0.8 }), BUBN); bubs.frustumCulled = false; bubs.renderOrder = 7; toothSet.add(bubs);
const _M = new THREE.Matrix4(), _Q = new THREE.Quaternion(), _S = V(1, 1, 1);

// ------------------------------------------------------------------ the story
const T_GRAB = 1.0;                                                // beat 7: reaches for the 6th can, holds it up in front of him (it gets cracked open at the loop)
const T_UP = 0.55, T_SIP = 1.5;                                    // beat 0: the fizz settles, the can goes up, he drinks
const T_DROP = 2.5;                                                // beat 6: his weak hand lets the can go
const LOOPSEED = { R: null, L: null };
function blinkAt(s) { const u = ((s + 40) % 3.7) / 0.16; return u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0; }
const F = fwdOf(90), Rt = rightOf(90), UP = V(0, 1, 0);           // his forward (-x), his right (-z), up
const STAND1 = { ...addPose(STAND, { spine1: [-4, 0, 0], neck: [6, 0, 0] }), armL: A(10, 14, 0, 22) };   // hands a little off the hips (a reach from there doesn't brush them)
// a can in his hand: palm on its side (left hand: palm to his right, so his knuckles face the camera), fingers around it; c = can bottom, axis = bottom -> top
const GRIP = 0.012;
function canHand(c, axis, S = 'L') { const s = S === 'R' ? 1 : -1;
  const n = Rt.clone().multiplyScalar(-s).addScaledVector(F, 0.25); n.addScaledVector(axis, -n.dot(axis)).normalize();
  const u = new THREE.Vector3().crossVectors(axis, n).multiplyScalar(-s).normalize();
  return { S, p: c.clone().addScaledVector(axis, CANH * 0.45).addScaledVector(n, -(CANR + GRIP)), n, u, c: 50, th: 42, opp: 40, memAbs: 'can' + S, seed: A(40, 15, 0, 80, 10) }; }
const tipAxis = th => UP.clone().multiplyScalar(Math.cos(th * D2R)).addScaledVector(F, -Math.sin(th * D2R));
function canAtMouth(th) { const ax = tipAxis(th), rim = RG.mouthW().addScaledVector(F, 0.016).add(V(0, 0.004, 0)).addScaledVector(Rt, 0.012); return { c: rim.clone().addScaledVector(ax, -CANH), ax }; }
const SHOW = V(-2.28, 1.2, -0.42);                                  // the can held up in front of his chest (bottom)
function counterHand(S, dz = 0) { const s = S === 'R' ? 1 : -1;
  return { S, p: V(-2.43, TOPC + 0.03, STANDP.z + s * -0.2 + dz), n: V(0, -1, 0), u: F.clone().addScaledVector(Rt, 0.25 * s).normalize(), c: 20, th: 20, memAbs: 'rest' + S, seed: A(35, 10, 0, 40, -60) }; }

// the state at a time ----------------------------------------------
function guyAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  const face = { blink: blinkAt(lt + b * 1.3) };
  let pose = STAND1, root = { x: STANDP.x, y: 0.95, z: STANDP.z, yaw: 90 }, hands = [], show = true, cut = false;
  let canMode = 'counter', canC = CAN0.clone(), canAx = UP.clone(), xr = 0, fizzK = 0, spoons = 0, limit = 0, sugar = 0, insulin = 0, fat = 0, toothT = -1, fall = -1, weak = 0;
  if (b === 7) {                                                    // he grabs the next can and holds it up
    const reach = smooth(0.0, T_GRAB, lt), lift = smooth(T_GRAB + 0.05, d - 0.35, lt);
    if (lt < T_GRAB) { canMode = 'counter'; const h = canHand(CAN0.clone(), UP.clone()); h.p.y += 0.14 * (1 - reach) ** 2; hands = [{ ...h, blend: reach, local: lt > 0.1 }]; }   // over the counter's edge, then down to the can   // local: the target arm can't flip to another shape mid-reach
    else { canMode = 'hand'; canC = CAN0.clone().lerp(SHOW, sm(lift)); canC.y += 0.08 * Math.sin(Math.PI * lift); hands = [canHand(canC, canAx)]; }
    const lean = Math.sin(Math.PI * smooth(0, T_GRAB + 0.6, lt)); pose = addPose(STAND1, { neck: [-10 + 4 * lift, 4, 0], head: [-6, 0, 0], spine1: [6 * lean, 0, 0], spine2: [4 * lean, 0, 0] }); Object.assign(face, { look: [0.1, -0.4] });
  } else if (b === 0) {                                             // it's just been cracked: fizz sprays out; up it goes, he drinks
    fizzK = 1 - smooth(0.25, 0.75, lt); canMode = 'hand';
    const up = smooth(T_UP, T_SIP, lt), tip = smooth(T_UP + 0.2, T_SIP + 0.3, lt), head = smooth(T_UP + 0.4, T_SIP + 0.2, lt);
    const m = canAtMouth(100 * tip + 20 * smooth(T_SIP, d, lt));
    canAx = UP.clone().lerp(m.ax, tip).normalize(); canC = SHOW.clone().lerp(m.c, sm(up));
    hands = [{ ...canHand(canC, canAx), ...(LOOPSEED.L ? { seed: LOOPSEED.L, seedIsPrev: true } : {}) }];
    pose = addPose(STAND1, { neck: [-6 * (1 - head) + 14 * head, 4 * (1 - head), 0], head: [-6 * (1 - head) + 12 * head, 0, 0], spine1: [-3 * head, 0, 0] });
    Object.assign(face, { look: [0.1, -0.4 * (1 - head)], brow: 0.3 * (1 - head), oh: 0.3 * fizzK });
  } else if (b === 1 || b === 2) {                                  // ten sugar cubes, one can's worth; then the daily max line
    show = false; spoons = b === 1 ? clamp((lt - 0.15) / 1.9, 0, 1) : 1; limit = b === 2 ? smooth(0.1, 0.5, lt) : 0;
  } else if (b === 3) {                                             // x-ray: blood sugar shoots up; the pancreas pumps out insulin; the sugar drops back
    xr = 1; sugar = smooth(0.1, 1.4, lt) * (1 - 0.75 * smooth(2.4, d, lt)); insulin = smooth(1.6, 2.2, lt);
    pose = addPose(STAND1, { neck: [-4, 0, 0] });
  } else if (b === 4) {                                             // the tooth up close
    show = false; toothT = lt;
  } else if (b === 5) {                                             // x-ray: the extra sugar is stored as fat (the liver turns yellow and swells)
    xr = 1; sugar = 0.6 * (1 - smooth(0.4, 2.2, lt)); fat = smooth(0.6, d - 0.6, lt);
    pose = addPose(STAND1, { neck: [-4, 0, 0] });
  } else if (b === 6) {                                             // rare: so little potassium his muscles go weak; the can slips; he braces on the counter
    weak = smooth(0.3, d, lt); const sag = smooth(0.3, T_DROP, lt);
    if (lt < T_DROP) { canMode = 'hand'; canC = SHOW.clone().add(V(0, -0.2 * sag, 0.04 * sag)); canAx = UP.clone().lerp(F.clone().multiplyScalar(-1), 0.25 * sag).normalize(); hands.push(canHand(canC, canAx)); }
    else { fall = lt - T_DROP; canMode = 'fall'; hands.push({ ...canHand(SHOW.clone().add(V(0, -0.2, 0.04)), UP.clone().lerp(F.clone().multiplyScalar(-1), 0.25).normalize()), c: 20, th: 20, blend: 1 - smooth(T_DROP, T_DROP + 0.6, lt) }); }
    hands.push(counterHand('R'));                                    // braced on the counter from the start of the shot
    pose = addPose(STAND1, { spine1: [8 * weak, 0, 0], spine2: [5 * weak, 0, 0], neck: [-10 * weak, -6 * weak, 0], head: [-6 * weak, 0, 0] });
    root = { x: STANDP.x, y: 0.95 - 0.04 * weak, z: STANDP.z, yaw: 90 };
    Object.assign(face, { squint: 0.4 * weak, brow: 0.6 * weak, jaw: 0.15 * weak, look: [0, -0.5] });
  }
  const wb = 2 * Math.PI * Math.round(TOTAL / 2.6) / TOTAL;           // breathing (whole cycles over the loop)
  pose = addPose(pose, { spine1: [0.9 * Math.sin(wb * t), 0, 0], spine2: [0.6 * Math.sin(wb * t + 0.4), 0, 0], neck: [0.7 * Math.sin(wb * t + 1.1), 0, 0] });
  return { b, lt, d, pose, root, hands, show, cut, canMode, canC, canAx, xr, fizzK, spoons, limit, sugar, insulin, fat, toothT, fall, weak, face };
}

// ------------------------------------------------------------------ cameras
function shakeV(t, a) { return V(vn1(t * 14, 1) * a * 0.5, vn1(t * 14, 2) * a, vn1(t * 14, 3) * a); }
const CAM7 = { pos: V(-2.8, 1.6, 0.5), tgt: V(-2.15, 1.3, -0.55), fov: 44 };     // at his front-left: his face, the can, the counter
function camAt(t, g) {
  const b = g.b, lt = g.lt, d = g.d, k = smooth(0, d, lt);
  if (b === 7) return { pos: CAM7.pos.clone().add(V(0.05 * (1 - k), 0.0, 0.1 * (1 - k))), tgt: CAM7.tgt, fov: CAM7.fov };
  if (b === 0) return { pos: CAM7.pos.clone().lerp(V(-2.72, 1.55, 0.28), k), tgt: CAM7.tgt.clone().lerp(V(-2.1, 1.38, -0.6), k), fov: 44 - 2 * k };
  if (b === 1) return { pos: V(-2.04, 1.17 + 0.02 * k, 0.26 - 0.05 * k), tgt: V(-2.47, 1.04 + 0.02 * k, -0.21), fov: 36 };
  if (b === 2) return { pos: V(-2.06, 1.2, 0.22 + 0.06 * k), tgt: V(-2.47, 1.07, -0.21), fov: 36 };
  if (b === 3) return { pos: V(-2.7, 1.28, 0.32 - 0.06 * k), tgt: V(-2.05, 1.13, -0.62), fov: 42 };
  if (b === 4) return { pos: TOOTH.clone().add(V(0.05 - 0.1 * k, 0.62 - 0.05 * k, 1.05 - 0.12 * k)), tgt: TOOTH.clone().add(V(0, 0.2, 0)), fov: 44 };
  if (b === 5) return { pos: V(-2.68, 1.2, 0.28 - 0.06 * k), tgt: V(-2.05, 1.08, -0.62), fov: 40 };
  if (b === 6) return { pos: V(-2.28, 1.3, 1.4), tgt: V(-2.15, 0.88, -0.5), fov: 54 };
  return CAM7;
}

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
