// "You just finished your fourth energy drink, and your heart is pounding." - a 3D Short: what too much caffeine does, and how long it stays.
//   energy.html?w=1080&h=1920            (times from energy/times.json; one shot per narration line)
// Beats: 0 he chugs the 4th can; x-ray: his heart pounding (hook) | 1 the can up close: up to 300 mg | 2 a tube fills can by can past the 400 mg limit
//        3 inside the brain: caffeine sits in the "tired" receptors, the signal bounces off | 4 racing heart, then his shaking hand
//        5 an electric storm in his brain (1,200 mg fast) | 6 five hours go by: the tube drains to half | 7 he grabs the next can (loops)
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { loadGuy } from '/guy3d.js';

const Q = new URLSearchParams(location.search);
const W = +Q.get('w') || 720, H = +Q.get('h') || 1280;
const FPS = 30;
const TIMES = await (await fetch('/energy/times.json')).json();
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
// ================================================================== ENERGY DRINKS
// ------------------------------------------------------------------ the counter: four cans (three empty), a measuring tube for the caffeine; the clock moves near the counter
const TOPC = 0.945;                                                // counter top height
const STANDP = V(-2.03, 0, -0.62);                                 // where he stands (facing -x)
clock.position.set(-2.63, TOPC + 0.095, 0.03); clock.scale.setScalar(0.3); clock.rotation.y = 0.45;   // a kitchen clock standing on the counter
const CANR = 0.033, CANH = 0.157;
const canTex = canvasTex(256, 160, g => { const gr = g.createLinearGradient(0, 0, 0, 160); gr.addColorStop(0, '#16224a'); gr.addColorStop(1, '#0a1230'); g.fillStyle = gr; g.fillRect(0, 0, 256, 160);
  g.fillStyle = '#7dff3a'; g.beginPath(); g.moveTo(150, 10); g.lineTo(108, 84); g.lineTo(134, 84); g.lineTo(104, 152); g.lineTo(170, 66); g.lineTo(142, 66); g.lineTo(172, 10); g.closePath(); g.fill();
  g.font = 'bold 40px sans-serif'; g.fillStyle = '#ffffff'; g.textAlign = 'center'; g.save(); g.translate(64, 80); g.rotate(-Math.PI / 2); g.fillText('ZAPP', 0, 14); g.restore();
  g.font = 'bold 15px sans-serif'; g.fillStyle = '#7dff3a'; g.save(); g.translate(222, 80); g.rotate(-Math.PI / 2); g.fillText('300MG CAFFEINE', 0, 6); g.restore(); });
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
const CAN0 = V(-2.43, TOPC, -0.38);                               // the 4th can (to his left)
let CANYAW = 70, CANSPIN = 0;                                       // which way its label faces: on the counter (deg) / in his hand (rad)
const can = makeCan(); can.position.copy(CAN0); scene.add(can);
for (const [x, z, ry, side, cr] of [[-2.52, -0.95, 0.4, 0, 0.6], [-2.46, -1.05, 2.1, 0, 0], [-2.58, -0.82, 0, 1, 0.3]]) {
  const e = makeCan(cr); e.rotation.y = ry; if (side) { e.rotation.set(0, 0.3, Math.PI / 2); e.position.set(x + 0.02, TOPC + CANR * 1.1, z); } else e.position.set(x, TOPC, z); scene.add(e); }
// the measuring tube: a clear cylinder with ticks every 300 mg, a red LIMIT line at 400; green caffeine fills it
const TUBE = V(-2.56, TOPC, -0.2), TUBER = 0.055, TUBEH = 0.46, MG2H = 0.36 / 1200;
const tube = new THREE.Group(); tube.position.copy(TUBE); scene.add(tube);
const tubeTex = canvasTex(200, 1000, g => { g.clearRect(0, 0, 200, 1000);           // the arc it wraps is about 1:5 (wide:tall)
  const yOf = mg => 1000 - (0.012 + mg * MG2H) / TUBEH * 1000;
  g.textAlign = 'left'; for (const mg of [300, 600, 900, 1200]) { const y = yOf(mg); g.fillStyle = '#ffffff'; g.fillRect(8, y - 3, 34, 6); g.font = 'bold 30px sans-serif'; g.fillText(mg + ' MG', 50, y + 11); }
  const y4 = yOf(400); g.fillStyle = '#ff2a20'; g.fillRect(0, y4 - 5, 200, 10); g.font = 'bold 30px sans-serif'; g.fillText('LIMIT 400', 40, y4 - 14); });
{ const glassT = new THREE.Mesh(new THREE.CylinderGeometry(TUBER, TUBER, TUBEH, 40, 1, true), new THREE.MeshPhysicalMaterial({ color: 0xe8f4ff, roughness: 0.05, transparent: true, opacity: 0.22, side: THREE.DoubleSide, depthWrite: false }));
  glassT.position.y = TUBEH / 2; tube.add(glassT);
  const marks = new THREE.Mesh(new THREE.CylinderGeometry(TUBER + 0.001, TUBER + 0.001, TUBEH, 40, 1, true, -Math.PI / 2 - 0.8, 1.6), new THREE.MeshBasicMaterial({ map: tubeTex, transparent: true, depthWrite: false, toneMapped: false }));
  marks.position.y = TUBEH / 2; marks.renderOrder = 4; tube.add(marks);
  const base = new THREE.Mesh(new THREE.CylinderGeometry(TUBER + 0.02, TUBER + 0.025, 0.012, 40), mat(0x2a2a30, 0.4)); base.position.y = 0.006; tube.add(base); }
const fillM = new THREE.MeshStandardMaterial({ color: 0x7dff3a, emissive: 0x3aa010, emissiveIntensity: 0.6, roughness: 0.15, transparent: true, opacity: 0.85 });
const fill = new THREE.Mesh(new THREE.CylinderGeometry(TUBER - 0.004, TUBER - 0.004, 1, 36).translate(0, 0.5, 0), fillM); fill.position.y = 0.012; tube.add(fill);
tube.rotation.y = Math.PI / 2 + 0.35;                              // the ticks face the camera (front-left of him)
// the evening light through the window (beat 6: five hours go by)
const dusk = new THREE.Color(0xff9a50);

// ------------------------------------------------------------------ x-ray: the glow body (same skeleton) with the heart and the brain
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
const heartM = new THREE.MeshStandardMaterial({ color: 0x8a1a2a, emissive: 0xff2a3a, emissiveIntensity: 0.9, roughness: 0.4 });
const heart = new THREE.Group(); G.bones.chest.add(heart); heart.position.copy(toLocal(G.bones.chest, V(-0.025, 1.31, -0.04)));
{ const hg = new THREE.Group(); heart.add(hg); hg.rotation.z = -0.45; hg.rotation.x = 0.2;
  for (const s of [-1, 1]) { const l = new THREE.Mesh(new THREE.SphereGeometry(0.03, 24, 16), heartM); l.position.set(s * 0.02, 0.012, 0); hg.add(l); }
  const pt = new THREE.Mesh(new THREE.ConeGeometry(0.043, 0.07, 24).rotateX(Math.PI), heartM); pt.position.y = -0.03; pt.scale.z = 0.75; hg.add(pt);
  const ao = new THREE.Mesh(new THREE.TorusGeometry(0.02, 0.008, 8, 16, Math.PI), heartM); ao.position.set(0.0, 0.045, 0); hg.add(ao); }
const heartGlow = new THREE.PointLight(0xff3040, 0, 0.6, 2); heart.add(heartGlow);
// the brain (beat 5: electric storm)
const brainM = new THREE.MeshStandardMaterial({ color: 0x9a5a7a, emissive: 0xff8ab8, emissiveIntensity: 0.6, roughness: 0.45 });
const brain = new THREE.Group(); G.bones.head.add(brain); brain.position.copy(toLocal(G.bones.head, HC.clone().add(V(0, 0.035, 0.012)))); brain.scale.setScalar(0.86);
{ const g = new THREE.SphereGeometry(0.072, 48, 32); const p = g.attributes.position; for (let i = 0; i < p.count; i++) { const v = V(p.getX(i), p.getY(i), p.getZ(i)).normalize();
    const fold = 0.0035 * Math.sin(v.x * 40 + Math.sin(v.y * 25) * 2) * Math.sin(v.z * 35 + v.y * 20) + (Math.abs(v.x) < 0.06 ? -0.006 : 0);
    v.multiplyScalar(0.072 + fold); v.y *= 0.82; v.z *= 1.18; p.setXYZ(i, v.x, v.y, v.z); } g.computeVertexNormals(); brain.add(new THREE.Mesh(g, brainM)); }
// lightning in the brain: jagged glowing tubes, rebuilt from time alone
const boltM = new THREE.MeshBasicMaterial({ color: 0xfff6b0, toneMapped: false, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, depthTest: false });
const bolts = []; for (let i = 0; i < 7; i++) { const m = new THREE.Mesh(new THREE.BufferGeometry(), boltM); m.renderOrder = 9; m.frustumCulled = false; brain.add(m); bolts.push(m); }
function setBolts(t, k) { bolts.forEach((m, i) => { const on = k > 0.01 && hash1(Math.floor(t * 12) * 7.1 + i * 3.3) < 0.85 * k; m.visible = on; if (!on) return;
    const sd = Math.floor(t * 12) * 13.7 + i * 5.1, a = V(hash1(sd) - 0.5, hash1(sd + 1) - 0.5, hash1(sd + 2) - 0.5).normalize().multiplyScalar(0.06), b = V(hash1(sd + 3) - 0.5, hash1(sd + 4) - 0.5, hash1(sd + 5) - 0.5).normalize().multiplyScalar(0.06);
    const pts = []; for (let j = 0; j <= 8; j++) { const u = j / 8, p = a.clone().lerp(b, u); if (j > 0 && j < 8) p.add(V(hash1(sd + j * 1.7) - 0.5, hash1(sd + j * 2.3) - 0.5, hash1(sd + j * 3.1) - 0.5).multiplyScalar(0.03)); p.multiplyScalar(1.1); pts.push(p); }
    m.geometry.dispose(); m.geometry = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 24, 0.0028, 5, false); }); }
const ORGANS = [heart, brain];
let XRON = false, XRNEW = false;
function setXray(k) { if ((k > 0.01) !== XRON) { XRON = k > 0.01; XRNEW = XRON; }   // the first draw after the ghost comes on comes out blank: draw() renders that frame twice
  for (const x of XRAY) x.visible = k > 0.01; xrayMat.emissiveIntensity = 0.75 * k;
  for (const o of NORMAL) o.visible = k < 0.6; for (const o of ORGANS) o.visible = k > 0.5; }

// ------------------------------------------------------------------ inside the brain (beat 3): a nerve cell's surface with receptors; caffeine sits in them, the "tired" signal bounces off
const CELL = V(40, 0, 0);
const cellSet = new THREE.Group(); cellSet.position.copy(CELL); scene.add(cellSet);
const cellLight = new THREE.PointLight(0xffd8e8, 0, 6, 1.2); cellLight.position.set(0.3, 1.2, 0.8); cellSet.add(cellLight);
{ const bg = new THREE.Mesh(new THREE.SphereGeometry(4, 32, 16), new THREE.MeshBasicMaterial({ color: 0x2a0a22, side: THREE.BackSide })); cellSet.add(bg);
  const memTex = canvasTex(512, 512, g => { g.fillStyle = '#d87aa0'; g.fillRect(0, 0, 512, 512); for (let i = 0; i < 260; i++) { g.fillStyle = `rgba(${150 + Math.random() * 60 | 0},60,110,0.35)`; g.beginPath(); g.arc(Math.random() * 512, Math.random() * 512, 6 + Math.random() * 14, 0, 6.28); g.fill(); } });
  const memG = new THREE.PlaneGeometry(3, 3, 60, 60).rotateX(-Math.PI / 2); const p = memG.attributes.position; for (let i = 0; i < p.count; i++) { const x = p.getX(i), z = p.getZ(i); p.setY(i, -0.12 * (x * x + z * z) + 0.02 * Math.sin(x * 9) * Math.sin(z * 7)); } memG.computeVertexNormals();
  const mem = new THREE.Mesh(memG, new THREE.MeshStandardMaterial({ map: memTex, roughness: 0.6, emissive: 0x401028, emissiveIntensity: 0.4 })); cellSet.add(mem); }
const RECS = [V(-0.16, 0, 0.07), V(0, 0, -0.08), V(0.16, 0, 0.07)];
const recM = new THREE.MeshStandardMaterial({ color: 0x8a4ad0, emissive: 0x4a1a90, emissiveIntensity: 0.5, roughness: 0.4 });
for (const r of RECS) { r.y = -0.12 * (r.x * r.x + r.z * r.z); const g = new THREE.Group(); g.position.copy(r); cellSet.add(g);
  for (let k = 0; k < 4; k++) { const a = k / 4 * Math.PI * 2 + 0.4, arm = new THREE.Mesh(new THREE.CapsuleGeometry(0.018, 0.07, 6, 12), recM); arm.position.set(Math.cos(a) * 0.05, 0.045, Math.sin(a) * 0.05); arm.rotation.set(Math.sin(a) * 0.35, 0, -Math.cos(a) * 0.35); g.add(arm); } }
const cafM = new THREE.MeshStandardMaterial({ color: 0xff8a20, emissive: 0xc04a00, emissiveIntensity: 0.6, roughness: 0.35, flatShading: true });
const adeM = new THREE.MeshStandardMaterial({ color: 0x4aa8ff, emissive: 0x1a5ac0, emissiveIntensity: 0.6, roughness: 0.3 });
const cafs = RECS.map(() => { const m = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, 0.03, 6), cafM); cellSet.add(m); return m; });
const ades = RECS.map(() => { const m = new THREE.Mesh(new THREE.IcosahedronGeometry(0.04, 2), adeM); cellSet.add(m); return m; });
function tag(text, color, w = 0.34) { const c = canvasTex(512, 128, g => { g.fillStyle = 'rgba(10,10,14,0.75)'; g.beginPath(); g.roundRect(4, 4, 504, 120, 30); g.fill(); g.fillStyle = color; g.font = 'bold 64px sans-serif'; g.textAlign = 'center'; g.fillText(text, 256, 86); });
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: c, depthTest: false, toneMapped: false })); s.scale.set(w, w / 4, 1); s.renderOrder = 10; cellSet.add(s); return s; }
const tagCaf = tag('CAFFEINE', '#ffb060', 0.26), tagAde = tag('"TIRED" SIGNAL', '#8ac8ff', 0.32);

// ------------------------------------------------------------------ the story
const T_GRAB = 0.7, T_LIFT = 1.1, T_SIP = 2.45;                    // beat 7: reaches for the 4th can, lifts it, starts to drink (loops into beat 0)
const T_DOWN = 1.25, T_SET = 2.2, T_XR = 1.85;                     // beat 0: lowers the can, sets it down; the x-ray comes on
const T_SHAKE = 1.75;                                              // beat 4: cut from the racing heart to his shaking hand
const LOOPSEED = { R: null, L: null };
function blinkAt(s) { const u = ((s + 40) % 3.7) / 0.16; return u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0; }
const F = fwdOf(90), Rt = rightOf(90), UP = V(0, 1, 0);           // his forward (-x), his right (-z), up
const STAND1 = addPose(STAND, { spine1: [-4, 0, 0], neck: [6, 0, 0] });
// a can in his hand: palm on its side (left hand: palm to his right, so his knuckles face the camera), fingers around it; c = can bottom, axis = bottom -> top
const GRIP = 0.012;
function canHand(c, axis, S = 'L') { const s = S === 'R' ? 1 : -1;
  const n = Rt.clone().multiplyScalar(-s).addScaledVector(F, 0.25); n.addScaledVector(axis, -n.dot(axis)).normalize();
  const u = new THREE.Vector3().crossVectors(axis, n).multiplyScalar(-s).normalize();
  return { S, p: c.clone().addScaledVector(axis, CANH * 0.42).addScaledVector(n, -(CANR + GRIP)), n, u, c: 50, th: 42, opp: 40, memAbs: 'can' + S, seed: A(40, 15, 0, 80, 10) }; }
// the can's axis tipped back toward his face by th degrees (0 = upright)
const tipAxis = th => UP.clone().multiplyScalar(Math.cos(th * D2R)).addScaledVector(F, -Math.sin(th * D2R));
// the can at his mouth: the rim on his lips
function canAtMouth(th) { const ax = tipAxis(th), rim = RG.mouthW().addScaledVector(F, 0.016).add(V(0, 0.004, 0)).addScaledVector(Rt, 0.012); return { c: rim.clone().addScaledVector(ax, -CANH), ax }; }
// hands flat on the counter edge (bracing)
function counterHand(S, dz = 0) { const s = S === 'R' ? 1 : -1;
  return { S, p: V(-2.43, TOPC + 0.03, STANDP.z + s * -0.2 + dz), n: V(0, -1, 0), u: F.clone().addScaledVector(Rt, 0.25 * s).normalize(), c: 20, th: 20, memAbs: 'rest' + S, seed: A(35, 10, 0, 40, -60) }; }
function pulse(t, bpm) { const ph = (t * bpm / 60) % 1; return Math.exp(-(((ph - 0.05) / 0.06) ** 2)) + 0.55 * Math.exp(-(((ph - 0.28) / 0.06) ** 2)); }

// the state at a time ----------------------------------------------
function guyAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  const face = { blink: blinkAt(lt + b * 1.3) };
  let pose = STAND1, root = { x: STANDP.x, y: 0.95, z: STANDP.z, yaw: 90 }, hands = [], show = true, cut = false;
  let canMode = 'counter', canC = CAN0.clone(), canAx = UP.clone(), xr = 0, bpm = 80, beatK = 0.08, mg = 0, dim = 0, clockT = 0, bolt = 0, cell = false, tremor = 0, wide = false;
  if (b === 7) {                                                    // he grabs the 4th can and starts to drink
    const reach = smooth(T_GRAB - 0.68, T_GRAB, lt), lift = smooth(T_GRAB + 0.05, T_SIP, lt), tip = smooth(T_LIFT, T_SIP + 0.25, lt);
    const head = smooth(T_LIFT + 0.4, d, lt);
    pose = addPose(STAND1, { neck: [-10 * (1 - head) + 14 * head, 0, 0], head: [-6 * (1 - head) + 12 * head, 0, 0], spine1: [-3 * head, 0, 0] });
    if (lt > T_GRAB - 0.68) { canMode = lt > T_GRAB ? 'hand' : 'counter';
      const m = canAtMouth(100 * tip), up = CAN0.clone().add(V(0.12, 0.25, 0.05));
      canAx = UP.clone().lerp(m.ax, tip).normalize(); canC = lift < 0.5 ? CAN0.clone().lerp(up, lift * 2) : up.lerp(m.c, sm((lift - 0.5) * 2));
      hands = [{ ...canHand(canC, canAx), blend: reach }]; }
    Object.assign(face, { look: [0.1, -0.3 * (1 - head)] });
  } else if (b === 0) {                                             // chugging; down it goes; heart pounding (x-ray)
    const head = 1 - smooth(T_DOWN, T_DOWN + 0.5, lt), down = smooth(T_DOWN, T_SET, lt), off = smooth(T_SET, T_SET + 0.75, lt);
    pose = addPose(STAND1, { neck: [14 * head - 4 * (1 - head), 0, 0], head: [12 * head, 0, 0], spine1: [-3 * head, 0, 0] });
    const m = canAtMouth(100 + 30 * smooth(0, T_DOWN, lt)), set = CAN0.clone();
    canAx = m.ax.clone().lerp(UP, down).normalize(); canC = m.c.clone().lerp(set, sm(down)); canMode = off > 0.5 ? 'counter' : 'hand'; if (off > 0.5) { canC = set; canAx = UP.clone(); }
    hands = [{ ...canHand(canC, canAx), ...(LOOPSEED.L ? { seed: LOOPSEED.L, seedIsPrev: true } : {}), blend: 1 - off }];
    xr = smooth(T_XR, T_XR + 0.25, lt); bpm = 150; beatK = 0.16;
    Object.assign(face, { look: [0.1, 0], brow: 0.4 * off, oh: 0.3 * off, fear: 0.3 * off });
  } else if (b === 1) {                                             // the can up close: up to 300 mg
    show = true;
  } else if (b === 2) {                                             // the tube fills can by can: past the 400 mg limit, to 1,200
    mg = 300 * (smooth(0.35, 0.75, lt) + smooth(1.05, 1.45, lt) + smooth(1.75, 2.15, lt) + smooth(2.45, 2.85, lt));
    Object.assign(face, { look: [0.3, -0.2] });
  } else if (b === 3) {                                             // inside the brain
    show = false; cell = true;
  } else if (b === 4) {                                             // racing heart (x-ray), then his shaking hand
    const shake = lt >= T_SHAKE; cut = lt >= T_SHAKE && lt - T_SHAKE < 1 / 30 + 1e-6;
    xr = shake ? 0 : 1; bpm = 175; beatK = 0.2; tremor = shake ? 1 : 0.4;
    canMode = 'hand'; canAx = UP.clone(); canC = V(-2.3, 1.08, STANDP.z + 0.16);
    const tr = V(vn1(t * 9, 1), vn1(t * 9, 2), vn1(t * 9, 3)).multiplyScalar(0.006 * tremor); canC.add(tr);
    hands = [canHand(canC, canAx)]; pose = addPose(STAND1, { neck: [-12, 0, 0], head: [-8, 0, 0] });
    Object.assign(face, { look: [0.0, -0.5], brow: 0.6, fear: 0.4, jaw: 0.1 });
  } else if (b === 5) {                                             // too much, too fast: an electric storm in his brain; he braces on the counter
    xr = 1; bpm = 180; beatK = 0.2; bolt = smooth(0.3, 0.8, lt); mg = 1200;
    const k = smooth(0, 0.5, lt);
    pose = addPose(STAND1, { spine1: [10 * k, 0, 0], spine2: [6 * k, 0, 0], neck: [-14 * k, 6 * Math.sin(lt * 3), 0], head: [-6 * k, 0, 0] });
    hands = [counterHand('R'), counterHand('L')].map(h => ({ ...h, blend: smooth(0, 1.15, lt) }));
    Object.assign(face, { squint: 0.7, brow: 0.8, fear: 0.6, jaw: 0.2 });
  } else if (b === 6) {                                             // five hours go by: the clock spins, the light goes orange, the tube drains to half
    wide = true; const k = smooth(0.2, d - 0.3, lt); clockT = k; dim = k; mg = 1200 - 600 * k;
    hands = [counterHand('R'), counterHand('L')].map(h => ({ ...h, blend: 1 }));
    pose = addPose(STAND1, { spine1: [6, 0, 0], neck: [-6, 0, 0] }); Object.assign(face, { look: [0.0, 0.1], brow: 0.3 + 0.3 * k, squint: 0.3 * k, blink: 0 });
  }
  const wb = 2 * Math.PI * Math.round(TOTAL / 2.6) / TOTAL;           // breathing (whole cycles over the loop)
  pose = addPose(pose, { spine1: [0.9 * Math.sin(wb * t), 0, 0], spine2: [0.6 * Math.sin(wb * t + 0.4), 0, 0], neck: [0.7 * Math.sin(wb * t + 1.1), 0, 0] });
  return { b, lt, d, pose, root, hands, show, cut, canMode, canC, canAx, xr, bpm, beatK, mg, dim, clockT, bolt, cell, tremor, wide, face };
}

// ------------------------------------------------------------------ cameras
function shakeV(t, a) { return V(vn1(t * 14, 1) * a * 0.5, vn1(t * 14, 2) * a, vn1(t * 14, 3) * a); }
const CAM7 = { pos: V(-2.78, 1.62, 0.42), tgt: V(-2.12, 1.32, -0.6), fov: 44 };     // at his front-left: his face, the can, the counter
function camAt(t, g) {
  const b = g.b, lt = g.lt, d = g.d, k = smooth(0, d, lt);
  if (b === 7) return { pos: CAM7.pos.clone().add(V(0.06 * (1 - k), 0.0, 0.12 * (1 - k))), tgt: CAM7.tgt, fov: CAM7.fov };
  if (b === 0) { const x = smooth(T_XR - 0.1, T_XR + 0.5, lt);
    return { pos: CAM7.pos.clone().lerp(V(-2.7, 1.5, 0.2), x), tgt: CAM7.tgt.clone().lerp(V(-2.05, 1.3, -0.6), x), fov: 44 - 4 * x }; }
  if (b === 1) { const a = 0.55 - 0.35 * k, r = 0.42 - 0.05 * k; return { pos: CAN0.clone().add(V(Math.sin(a) * r, 0.11, Math.cos(a) * r)), tgt: CAN0.clone().add(V(0, 0.085, 0)), fov: 34 }; }
  if (b === 2) return { pos: TUBE.clone().add(V(0.3 - 0.03 * k, 0.37, 0.6 - 0.06 * k)), tgt: TUBE.clone().add(V(0.02, 0.3, 0)), fov: 42 };
  if (b === 3) return { pos: CELL.clone().add(V(0.04 - 0.08 * k, 0.72 - 0.06 * k, 1.0 - 0.1 * k)), tgt: CELL.clone().add(V(0, 0.08, 0)), fov: 45 };
  if (b === 4) { if (lt < T_SHAKE) return { pos: V(-2.62, 1.42, 0.05), tgt: V(-2.05, 1.25, -0.62), fov: 38 };
    return { pos: g.canC.clone().add(V(-0.28, 0.06, 0.34)), tgt: g.canC.clone().add(V(0, 0.07, 0)), fov: 38 }; }
  if (b === 5) return { pos: V(-2.5, 1.68, -0.1).add(shakeV(t, 0.004)), tgt: V(-2.06, 1.58, -0.6), fov: 34 };
  if (b === 6) return { pos: V(-2.88, 1.56, 1.02), tgt: V(-2.3, 1.22, -0.42), fov: 44 };
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
  if (list.length) { RG.hands(list, 'b' + g.b, frame); LASTH = list; }
  for (const S of ['R', 'L']) if (!list.some(h => h.S === S)) delete RG.LAST['cost' + S];
  G.root.updateMatrixWorld(true); RG.untwist(); G.face(g.face); G.root.updateMatrixWorld(true);
  // the can: on the counter, or where the story puts it (his hand holds it there)
  if (g.canMode === 'hand') { can.position.copy(g.canC); can.quaternion.copy(basisQ(new THREE.Vector3().crossVectors(g.canAx, Rt), g.canAx)).multiply(qAA(V(0, 1, 0), CANSPIN)); }
  else { can.position.copy(CAN0); can.quaternion.copy(yawQ(CANYAW)); }
  // x-ray, heart, brain storm
  setXray(g.xr); const pz = pulse(t, g.bpm); heart.scale.setScalar(1 + g.beatK * pz); heartM.emissiveIntensity = 0.7 + 0.9 * pz; heartGlow.intensity = g.xr > 0.5 ? 0.6 * pz : 0;
  brainM.emissiveIntensity = 0.6 + 0.8 * g.bolt * hash1(Math.floor(t * 12)); setBolts(t, g.bolt);
  // the tube
  tube.visible = g.b === 2 || g.b === 6; clock.visible = g.b === 6; fill.scale.y = Math.max(0.0005, g.mg * MG2H); fillM.emissiveIntensity = 0.6 + (g.mg > 400 && g.b === 2 ? 0.5 * pulse(t, 120) : 0);
  // inside the brain (beat 3): caffeine drops into the receptors, the blue "tired" signal comes down and bounces off
  cellSet.visible = g.cell; cellLight.intensity = g.cell ? 3 : 0;
  if (g.cell) { const lt = g.lt;
    RECS.forEach((rc, i) => { const s = smooth(0.15 + 0.18 * i, 0.75 + 0.18 * i, lt), top = rc.clone().add(V(0, 0.075, 0));
      cafs[i].position.copy(top.clone().add(V(0.25 * (1 - s) * (i % 2 ? 1 : -1), 0.6 * (1 - s), 0.1 * (1 - s)))); cafs[i].rotation.set(0.3 * (1 - s), lt * 0.5 * (1 - s) + i, 0);
      const a0 = 1.3 + 0.25 * i, u = clamp((lt - a0) / 0.9, 0, 1), hit = 0.5;     // comes down 0..0.5, bounces away 0.5..1
      const pa = top.clone().add(V(0.06, 0.34, 0.12)), ph = top.clone().add(V(0, 0.06, 0)), pb = top.clone().add(V(0.13 * (i - 1 || 1), 0.3, 0.22));
      ades[i].position.copy(u < hit ? pa.clone().lerp(ph, sm(u / hit)) : ph.clone().lerp(pb, sm((u - hit) / (1 - hit))).add(V(0, 0.12 * Math.sin(Math.PI * (u - hit) / (1 - hit)), 0)));
      ades[i].visible = lt > a0 - 0.05; ades[i].scale.setScalar(u > hit ? 1 + 0.15 * Math.exp(-(u - hit) * 20) : 1); });
    tagCaf.position.copy(RECS[1]).add(V(0, 0.2, -0.02)); tagCaf.material.opacity = smooth(0.6, 0.9, lt);
    tagAde.position.set(0, 0.42, 0.08); tagAde.material.opacity = smooth(1.3, 1.6, lt); }
  // camera and room light (beat 6 goes to evening)
  const C = camAt(t, g); camera.position.copy(C.pos); camera.up.set(0, 1, 0); camera.lookAt(C.tgt); camera.fov = C.fov; camera.updateProjectionMatrix();
  const dk = g.dim;
  sun.position.set(1.6, 3.4 - 1.6 * dk, 2.4); sun.target.position.set(0, 0, 0); sun.target.updateMatrixWorld();
  sun.color.set(0xffe3bf).lerp(dusk, dk); sun.intensity = 2.6 * (1 - 0.55 * dk); hemi.intensity = 0.85 * (1 - 0.5 * dk); lamp.intensity = 6 * (1 + 0.3 * dk); scene.environmentIntensity = 0.35 * (1 - 0.4 * dk);
  scene.background = ENV0.clone().multiplyScalar(1 - 0.5 * dk);
  clockHands.s.rotation.z = -t * 6 * D2R; clockHands.s.visible = g.clockT < 0.001; clockHands.m.rotation.z = -1.1 - g.clockT * 5 * 2 * Math.PI; clockHands.h.rotation.z = -3.3 - g.clockT * 5 / 12 * 2 * Math.PI;
  return { beat: g.b, cut: g.cut };
}
G.reset(); G.root.updateMatrixWorld(true);
const ANKLEH = wp(G.bones.footR).y;

// ------------------------------------------------------------------ frame I/O (same contract as the other 3D Shorts)
const draw = () => { if (XRNEW) { renderer.render(scene, camera); XRNEW = false; } renderer.render(scene, camera); };
const gl = renderer.getContext(), px = new Uint8Array(W * H * 4);
let CUTF = false, LASTB = 0;
function segStart(t) { const b = beatAt(t), lt = t - B[b]; if (b === 4 && lt >= T_SHAKE) return B[4] + T_SHAKE; return B[b]; }   // where a hold starts cold
function stepTo(i) { const t = i / FPS, tt = ((t % TOTAL) + TOTAL) % TOTAL;
  if (i !== LASTF + 1) for (let j = Math.ceil(segStart(tt) * FPS - 1e-6) + Math.floor(t / TOTAL) * Math.round(TOTAL * FPS); j < i; j++) update(j / FPS, j);
  const r = update(t, i); CUTF = r.cut; LASTB = r.beat; LASTF = i; }
// the loop: beat 0's can hand starts where beat 7 ends
for (let i = Math.ceil(B[7] * FPS); i < Math.round(TOTAL * FPS); i++) update(i / FPS, i);
LOOPSEED.L = RG.LAST.armL.slice();
draw(); update(B[4] + 0.5, -50); draw(); update(B[3] + 0.5, -40); draw();     // warm-up: compile the x-ray and the brain-cell shaders now
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
