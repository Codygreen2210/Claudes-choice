// "You just started choking, and you're home alone." - a 3D Short: the self-Heimlich over a chair back.
//   choke.html?w=1080&h=1920            (times from choke/times.json; one shot per narration line)
// Beats: 0 bite of steak, hands to his throat, jumps up (hook) | 1 x-ray: the bite in his windpipe | 2 blue lips; x-ray brain dims
//        3 taps 9-1-1; fist above the navel | 4 fist + hand: in and up; cut: bent over the end chair | 5 thrust: it pops out, he gasps
//        6 x-ray: a finger pushes it deeper (red X) | 7 sits back down, pushes the plate away, picks up the fork (loops)
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { loadGuy } from '/guy3d.js';

const Q = new URLSearchParams(location.search);
const W = +Q.get('w') || 720, H = +Q.get('h') || 1280;
const FPS = 30;
const TIMES = await (await fetch('/choke/times.json')).json();
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
// ================================================================== CHOKING ALONE
// ------------------------------------------------------------------ the dining table, two chairs, plate, steak, fork, phone
const T = V(0.3, 0, -0.9);                                       // table centre; top 1.3 (x) by 0.8 (z), 0.76 high
const TOPY = 0.76;
const wood = mat(0x8a5a36, 0.55), woodD = mat(0x6a4226, 0.6);
const dtable = new THREE.Group(); dtable.position.copy(T); home.add(dtable);
{ box(1.3, 0.045, 0.8, 0, TOPY - 0.0225, 0, wood, 0.012, dtable); box(1.2, 0.08, 0.7, 0, TOPY - 0.085, 0, woodD, 0.01, dtable);
  for (const [x, z] of [[-0.6, -0.35], [0.6, -0.35], [-0.6, 0.35], [0.6, 0.35]]) box(0.055, TOPY - 0.045, 0.055, x, (TOPY - 0.045) / 2, z, woodD, 0.01, dtable);
  const cloth = new THREE.Mesh(new THREE.PlaneGeometry(0.42, 0.32).rotateX(-Math.PI / 2), mat(0xc8d6e8, 0.9)); cloth.position.set(0, TOPY + 0.001, -0.22); cloth.receiveShadow = true; dtable.add(cloth); }
function makeChair(backTop = 0.98) {                             // seat 0.46 high; the back is on the chair's +z side (local), seat faces -z
  const g = new THREE.Group();
  box(0.44, 0.04, 0.42, 0, 0.44, 0, wood, 0.012, g);
  for (const [x, z] of [[-0.19, -0.18], [0.19, -0.18], [-0.19, 0.18], [0.19, 0.18]]) box(0.04, 0.44, 0.04, x, 0.22, z, woodD, 0.008, g);
  for (const x of [-0.19, 0.19]) box(0.04, backTop - 0.44, 0.04, x, 0.44 + (backTop - 0.44) / 2, 0.19, woodD, 0.008, g);
  box(0.44, 0.07, 0.045, 0, backTop - 0.035, 0.19, wood, 0.015, g);       // the top rail (what he leans over)
  box(0.38, 0.05, 0.03, 0, 0.7, 0.19, woodD, 0.01, g);
  return g; }
const C1 = makeChair(); home.add(C1);                            // his chair: behind the table, he faces +z
const C1Z0 = T.z - 0.68, C1Z1 = T.z - 1.02;                      // tucked in / pushed back after he jumps up
C1.rotation.y = Math.PI;                                          // seat faces +z (back toward the wall)
const C2 = makeChair(); home.add(C2);                             // the end chair he uses for the thrusts: seat faces the table (-x), back toward +x
C2.position.set(T.x + 0.97, 0, T.z); C2.rotation.y = Math.PI / 2;
const C2TOP = V(T.x + 0.97 + 0.19, 0.98, T.z);                   // centre of its top rail (world)
// plate, steak, the bite on the fork, knife, glass of water
const PLATE1 = V(T.x - 0.04, TOPY, T.z - 0.2), PLATE0 = V(T.x - 0.04, TOPY, T.z - 0.27);   // beat 7 pushes it from PLATE0 to PLATE1
const plate = new THREE.Group(); scene.add(plate);
{ const p = new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.1, 0.018, 40), mat(0xf6f3ee, 0.25)); p.position.y = 0.009; p.castShadow = p.receiveShadow = true; plate.add(p);
  const st = new THREE.Mesh(new RoundedBoxGeometry(0.14, 0.022, 0.1, 3, 0.009), new THREE.MeshStandardMaterial({ map: canvasTex(128, 96, g => { g.fillStyle = '#5a2f1c'; g.fillRect(0, 0, 128, 96); g.strokeStyle = '#2a140a'; g.lineWidth = 6; for (let i = 0; i < 6; i++) { g.beginPath(); g.moveTo(10 + i * 22, 0); g.lineTo(i * 22 - 20, 96); g.stroke(); } }), roughness: 0.6 }));
  st.position.set(-0.01, 0.03, 0.0); st.castShadow = true; plate.add(st);
  const cut = new THREE.Mesh(new RoundedBoxGeometry(0.03, 0.022, 0.1, 2, 0.006), new THREE.MeshStandardMaterial({ color: 0xa8483a, roughness: 0.5 })); cut.position.set(0.065, 0.03, 0); plate.add(cut);   // pink inside where it's cut
  const veg = new THREE.Mesh(new THREE.SphereGeometry(0.03, 12, 8), mat(0x3f8a3a, 0.7)); veg.scale.set(1.2, 0.5, 1); veg.position.set(-0.05, 0.024, 0.06); plate.add(veg); }
const knifeT = new THREE.Group(); scene.add(knifeT);
{ box(0.012, 0.006, 0.12, 0, 0.003, 0, mat(0xd8dde2, 0.2, 0.9), 0.002, knifeT); box(0.016, 0.012, 0.09, 0, 0.006, 0.1, mat(0x2a1c14, 0.5), 0.004, knifeT); }
knifeT.position.copy(PLATE1).add(V(-0.17, 0.0, 0.02)); knifeT.rotation.y = 0.15;
const glass = new THREE.Mesh(new THREE.CylinderGeometry(0.033, 0.03, 0.12, 24, 1, true), new THREE.MeshPhysicalMaterial({ color: 0xd8eaf2, roughness: 0.05, transmission: 0.6, transparent: true, opacity: 0.45, side: THREE.DoubleSide }));
glass.position.set(T.x + 0.26, TOPY + 0.06, T.z - 0.25); scene.add(glass);
// the fork (held in his right hand; axis +x = handle -> tines) and the bite on it
const fork = new THREE.Group(); scene.add(fork);
const steel = mat(0xd8dde2, 0.18, 0.95);
{ box(0.11, 0.006, 0.012, -0.02, 0, 0, steel, 0.003, fork); box(0.03, 0.004, 0.02, 0.05, 0, 0, steel, 0.002, fork);
  for (let i = 0; i < 4; i++) box(0.035, 0.003, 0.003, 0.08, 0, -0.0075 + i * 0.005, steel, 0, fork); }
const BITE = new THREE.Mesh(new RoundedBoxGeometry(0.024, 0.018, 0.022, 2, 0.006), new THREE.MeshStandardMaterial({ color: 0x5a2f1c, roughness: 0.6 }));
BITE.position.set(0.085, 0.009, 0); fork.add(BITE);
const FORK_TIP = V(0.09, 0, 0);
// the phone, flat on the table to his left of the plate (his right hand is closer to it: he faces +z, his right is -x)
const PHONE_AT = V(T.x - 0.27, TOPY + 0.0045, T.z - 0.33);
const phone = new THREE.Group(); scene.add(phone); phone.position.copy(PHONE_AT); phone.rotation.set(-Math.PI / 2, 0, 0);   // screen up, reads the right way for us (he's across the table)
let phoneTexState = -1;
const phoneCanvas = document.createElement('canvas'); phoneCanvas.width = 160; phoneCanvas.height = 330;
const phoneTex = new THREE.CanvasTexture(phoneCanvas); phoneTex.colorSpace = THREE.SRGBColorSpace;
function drawPhone(digits, calling) { const g = phoneCanvas.getContext('2d'); g.fillStyle = calling ? '#0c3a1c' : '#101418'; g.fillRect(0, 0, 160, 330);
  g.fillStyle = '#fff'; g.textAlign = 'center'; g.font = 'bold 44px Arial'; g.fillText(digits, 80, 70);
  if (calling) { g.font = 'bold 22px Arial'; g.fillText('CALLING', 80, 110); g.fillStyle = '#e8322a'; g.beginPath(); g.arc(80, 270, 26, 0, Math.PI * 2); g.fill(); }
  else { g.font = 'bold 26px Arial'; for (let r = 0; r < 4; r++) for (let c = 0; c < 3; c++) { const k = r < 3 ? String(r * 3 + c + 1) : ['*', '0', '#'][c]; g.fillStyle = '#2a3038'; g.beginPath(); g.arc(30 + c * 50, 130 + r * 48, 20, 0, Math.PI * 2); g.fill(); g.fillStyle = '#fff'; g.fillText(k, 30 + c * 50, 139 + r * 48); }
    g.fillStyle = '#2ac24a'; g.beginPath(); g.arc(80, 318, 0, 0, 1); g.fill(); }
  phoneTex.needsUpdate = true; }
{ box(0.072, 0.152, 0.009, 0, 0, 0, mat(0x1c1d22, 0.3, 0.6), 0.004, phone); const s = new THREE.Mesh(new THREE.PlaneGeometry(0.064, 0.142), new THREE.MeshBasicMaterial({ map: phoneTex, toneMapped: false })); s.position.z = 0.0048; phone.add(s); }
drawPhone('', false);
// the 9-1-1 keys in the phone's own space (canvas 160x330 over 0.064 x 0.142 m)
const KEYPOS = d => { const i = d === '0' ? 10 : +d - 1, r = Math.floor(i / 3), c = i % 3; return V((30 + c * 50) / 160 * 0.064 - 0.032, 0.071 - (130 + r * 48) / 330 * 0.142, 0.006); };

// ------------------------------------------------------------------ his skin: blue-gray when no air gets in (lips most)
const BLUE = { value: 0 };
for (const k of ['skin', 'face']) { const m = G.mat[k]; if (!m.userData.patches) continue;
  m.userData.patches.push(['cyan', sh => { sh.uniforms.uBlue = BLUE;
    sh.fragmentShader = sh.fragmentShader.replace('void main() {', 'uniform float uBlue;\nvoid main() {');
    if (sh.fragmentShader.includes('lip * 0.9);')) sh.fragmentShader = sh.fragmentShader.replace('lip * 0.9);', 'lip * 0.9);\n  diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.36, 0.42, 0.58), lip * uBlue * 0.85);');
    sh.fragmentShader = sh.fragmentShader.replace('#include <color_fragment>', '#include <color_fragment>\n  diffuseColor.rgb = mix(diffuseColor.rgb, diffuseColor.rgb * vec3(0.78, 0.84, 0.98), uBlue * 0.7);'); }]);
  m.needsUpdate = true; }

// ------------------------------------------------------------------ x-ray: a see-through glow body (same skeleton) with the airway, the stuck bite, lungs, brain
const xrayMat = new THREE.MeshStandardMaterial({ color: 0x000000, emissive: 0x58b8ff, emissiveIntensity: 1, transparent: true, opacity: 1, depthWrite: false, blending: THREE.AdditiveBlending, roughness: 1, metalness: 0 });
xrayMat.onBeforeCompile = sh => { sh.fragmentShader = sh.fragmentShader.replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\n  totalEmissiveRadiance *= 0.015 + 0.85 * pow(1.0 - abs(dot(normalize(normal), normalize(vViewPosition))), 2.4);'); };
const XRAY = [], NORMAL = [];
G.root.traverse(o => { if (!o.isMesh || o.userData.xray) return; NORMAL.push(o); });
for (const o of Object.entries(G.meshes).filter(([n]) => !/^(hair|hairCards|sole)/.test(n)).map(([, m]) => m)) {
  let x; if (o.isSkinnedMesh) { x = new THREE.SkinnedMesh(o.geometry, xrayMat); x.bind(o.skeleton, o.bindMatrix); } else x = new THREE.Mesh(o.geometry, xrayMat);
  x.userData.xray = true; x.position.copy(o.position); x.quaternion.copy(o.quaternion); x.scale.copy(o.scale); x.frustumCulled = false; x.castShadow = false; x.renderOrder = 5; o.parent.add(x); XRAY.push(x); }
G.reset(); G.root.updateMatrixWorld(true);
const toLocal = (bone, p) => bone.worldToLocal(p.clone());
const organMat = (c, e, k = 0.9) => new THREE.MeshStandardMaterial({ color: c, emissive: e, emissiveIntensity: k, roughness: 0.45 });
const HC = V(...G.man.headC);
// the windpipe: from behind the Adam's apple down into the chest, where it splits; the food pipe sits just behind it
const tubeTo = (bone, pts, r, m) => { const c = new THREE.CatmullRomCurve3(pts.map(p => toLocal(bone, p))); const t = new THREE.Mesh(new THREE.TubeGeometry(c, 24, r, 14, false), m); bone.add(t); return t; };
const airM = new THREE.MeshStandardMaterial({ color: 0x6a8a9a, emissive: 0x9fe0ff, emissiveIntensity: 0.55, roughness: 0.4, transparent: true, opacity: 0.6, depthWrite: false });
const foodM = new THREE.MeshStandardMaterial({ color: 0x8a5a5a, emissive: 0xff9a8a, emissiveIntensity: 0.3, roughness: 0.5, transparent: true, opacity: 0.45, depthWrite: false });
const trachea = tubeTo(G.bones.neck, [HC.clone().add(V(0, -0.105, -0.045)), V(0, 1.5, -0.035), V(0, 1.44, -0.025)], 0.0105, airM);
const tracheaLo = tubeTo(G.bones.chest, [V(0, 1.44, -0.025), V(0, 1.38, -0.015), V(0, 1.33, -0.005)], 0.0105, airM);
for (const s of [-1, 1]) tubeTo(G.bones.chest, [V(0, 1.33, -0.005), V(0.03 * s, 1.31, 0), V(0.06 * s, 1.29, 0.01)], 0.007, airM);
const gullet = tubeTo(G.bones.neck, [HC.clone().add(V(0, -0.09, -0.02)), V(0, 1.5, -0.012), V(0, 1.42, -0.005)], 0.008, foodM);
const throatTop = tubeTo(G.bones.head, [HC.clone().add(V(0, -0.06, -0.085)), HC.clone().add(V(0, -0.075, -0.06)), HC.clone().add(V(0, -0.1, -0.04))], 0.011, airM);   // mouth -> throat
const lungM = new THREE.MeshStandardMaterial({ color: 0x6a3a4a, emissive: 0xff7a9a, emissiveIntensity: 0.3, roughness: 0.6, transparent: true, opacity: 0.5, depthWrite: false });
const lungs = new THREE.Group(); G.bones.chest.add(lungs); lungs.position.copy(toLocal(G.bones.chest, V(0, 1.27, 0.0)));
for (const s of [-1, 1]) { const l = new THREE.Mesh(new THREE.SphereGeometry(0.075, 20, 16), lungM); l.scale.set(0.85, 1.45, 0.95); l.position.set(s * 0.085, 0, 0.01); lungs.add(l); }
const brainM = organMat(0x9a5a7a, 0xff8ab8, 0.6);
const brain = new THREE.Group(); G.bones.head.add(brain); brain.position.copy(toLocal(G.bones.head, HC.clone().add(V(0, 0.09, 0.03)))); brain.scale.setScalar(0.86);
{ const g = new THREE.SphereGeometry(0.072, 48, 32); const p = g.attributes.position; for (let i = 0; i < p.count; i++) { const v = V(p.getX(i), p.getY(i), p.getZ(i)).normalize();
    const fold = 0.0035 * Math.sin(v.x * 40 + Math.sin(v.y * 25) * 2) * Math.sin(v.z * 35 + v.y * 20) + (Math.abs(v.x) < 0.06 ? -0.006 : 0);
    v.multiplyScalar(0.072 + fold); v.y *= 0.82; v.z *= 1.18; p.setXYZ(i, v.x, v.y, v.z); } g.computeVertexNormals(); brain.add(new THREE.Mesh(g, brainM)); }
// the stuck bite: lodged in the windpipe just below the voice box (it rides with his neck)
const STUCK0 = V(0, 1.475, -0.033), STUCK1 = V(0, 1.425, -0.024);   // where it sticks / where a finger pushes it
const stuck = new THREE.Mesh(new RoundedBoxGeometry(0.026, 0.02, 0.022, 2, 0.007), new THREE.MeshStandardMaterial({ color: 0x8a4a2a, emissive: 0xff7a2a, emissiveIntensity: 0.8, roughness: 0.6 }));
G.bones.neck.add(stuck); stuck.position.copy(toLocal(G.bones.neck, STUCK0)); stuck.renderOrder = 7;
const STUCKL0 = stuck.position.clone(), STUCKL1 = toLocal(G.bones.neck, STUCK1);
// air (blue dots) running down the windpipe: they pile up above the bite
const airPts = (() => { const g = new THREE.BufferGeometry(); const p = new Float32Array(90 * 3); g.setAttribute('position', new THREE.BufferAttribute(p, 3));
  const m = new THREE.Points(g, new THREE.PointsMaterial({ color: 0x9fe8ff, size: 0.006, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending })); m.frustumCulled = false; m.renderOrder = 8; scene.add(m); return { m, p }; })();
// a red X over the throat for "don't" (beat 6)
const redX = new THREE.Group(); scene.add(redX);
for (const a of [1, -1]) { const b = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.016, 0.006), new THREE.MeshBasicMaterial({ color: 0xff2a20, toneMapped: false, transparent: true })); b.rotation.z = a * Math.PI / 4; redX.add(b); }
redX.renderOrder = 9;
const ORGANS = [trachea, tracheaLo, gullet, throatTop, lungs, brain, stuck];
let XRON = false, XRNEW = false;
function setXray(k) { if ((k > 0.01) !== XRON) { XRON = k > 0.01; XRNEW = XRON; }   // the first draw after the ghost comes on comes out blank: draw() renders that frame twice
  for (const x of XRAY) x.visible = k > 0.01; xrayMat.emissiveIntensity = 1.1 * k;
  for (const o of NORMAL) o.visible = k < 0.6; for (const o of ORGANS) o.visible = k > 0.5; tracheaLo.parent.children.forEach(c => { if (c.isMesh && c.material === airM) c.visible = k > 0.5; }); airPts.m.visible = k > 0.5; }
// the flying bite (beat 5): leaves his mouth, lands on the table
const flyBite = new THREE.Mesh(BITE.geometry, BITE.material); flyBite.castShadow = true; flyBite.scale.setScalar(1.6); scene.add(flyBite);

// ------------------------------------------------------------------ the story
const STANDP = V(T.x, 0, C1Z0 - 0.1);                           // where he stands after jumping up (facing +z)
const SEATH = 0.575;                                              // hip height sitting
const THRUSTP = V(C2TOP.x + 0.36, 0, T.z);                        // where he stands for the chair thrusts (facing -x)
const LF = w => 2 * Math.PI * Math.round(w * TOTAL / (2 * Math.PI)) / TOTAL;
// key times
const T_BITE = 0.42, T_CHOKE = 0.95, T_UP0 = 1.55, T_UP1 = 2.55;  // beat 0 (local)
const T_TAP = 0.62, T_FIST = 1.95;                                // beat 3 (local): taps 9-1-1, then makes the fist
const T_CHAIR = 1.45;                                             // beat 4 (local): cut to the chair
const T_POP = 0.45;                                               // beat 5 (local): the bite flies out
const T_SIT = 0;                                                  // beat 7 starts seated
const LIPS2 = 1.55;                                               // beat 2: face (blue lips) -> x-ray brain
function blinkAt(s) { const u = ((s + 40) % 3.7) / 0.16; return u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0; }
const SIT = curl(curl({ armR: A(25, 8, 0, 70, 30), armL: A(20, 10, 0, 75, 20), spine1: [-4, 0, 0], neck: [-6, 0, 0], head: [-4, 0, 0] }, 'R', 30), 'L', 22);
// hand targets ------------------------------------------------------
const f0 = fwdOf(180), r0 = rightOf(180), UP = V(0, 1, 0);
function forkHand(k) {                                            // k 0 = fork resting over the plate, 1 = the bite at his lips
  const mouth = RG.mouthW(), plateP = PLATE1.clone().add(V(0.02, 0.06, -0.06));
  const tipAt = plateP.clone().lerp(mouth.clone().addScaledVector(f0, 0.012).add(V(0, -0.006, 0)), k);
  // fist grip: the handle lies across his curled fingers, the tines come out past his thumb (-w). The solve places the TINE TIP (and the fork's
  // direction); the palm faces down at the plate and toward him at his mouth, so his knuckles face the camera when he eats.
  const kk = sm(k), up = V(0, 1, 0).addScaledVector(r0, -0.45).addScaledVector(f0, -0.3).normalize(), down = V(0, -0.5, 0).addScaledVector(f0, 0.6).addScaledVector(r0, -0.6).normalize();
  const dir = down.clone().lerp(up, kk).normalize();                                            // handle -> tines
  const nWant = V(0, -1, 0).lerp(f0.clone().negate(), kk).normalize();
  const extra = fk => { const tip = fk.p.clone().addScaledVector(fk.u, FORKGRIP.u).addScaledVector(fk.n, FORKGRIP.n).addScaledVector(fk.w, -(FORK_TIP.x - FORKGRIP.x));
    return tip.distanceToSquared(tipAt) / (0.006 * 0.006) + 20 * (1 + fk.w.dot(dir)) + 8 * (1 - fk.n.dot(nWant)); };
  const p = tipAt.clone().addScaledVector(dir, -0.11);
  return { S: 'R', fork: true, free: true, p, extra, c: 70, th: 60, seed: A(30, 10, 0, 100, 40) };
}
const FORKGRIP = { u: 0.028, n: 0.021, x: 0.0 };                  // the handle point (fork x) sits this far out from his palm point: along his fingers (u) and off the palm (n)
function restL(k = 1) { const pa = PLATE1;              // k 1 = flat on the table left of the plate; 0 = pushing the plate rim
  return { S: 'L', p: pa.clone().add(V(0.17, 0.035, 0)).addScaledVector(f0, -0.12), n: V(0, -1, 0), u: f0.clone(), c: 20, th: 20, seed: A(30, 10, 0, 80, 20) }; }
function throatHands() { const nk = wp(G.bones.neck).add(V(0, 0.03, 0)), q = wq(G.bones.neck), f = f0.clone(), r = r0.clone();
  return [{ S: 'R', p: nk.clone().addScaledVector(r, 0.052).addScaledVector(f, 0.03), n: r.clone().negate().addScaledVector(f, -0.35).normalize(), u: f.clone().negate().addScaledVector(UP, 0.35).normalize(), c: 22, th: 20, seed: A(40, 45, 0, 135, 40) },
          { S: 'L', p: nk.clone().addScaledVector(r, -0.052).addScaledVector(f, 0.03), n: r.clone().addScaledVector(f, -0.35).normalize(), u: f.clone().negate().addScaledVector(UP, 0.35).normalize(), c: 22, th: 20, seed: A(40, 45, 0, 135, 40) }]
    .map(h => ({ ...h, p: outside(h.p, h.n.clone().negate(), 0.011) })); }
function bellyPt() { const sp = wp(G.bones.spine1), q = wq(G.bones.spine1); return sp.add(V(0, 0.05, 0).applyQuaternion(q)).addScaledVector(V(0, 0, -1).applyQuaternion(q).negate().multiplyScalar(-1), 0); }
function fistHands(push) {                                        // right fist, thumb side on his belly just above the navel; left hand cupped over it; push = in and up
  const sp = wp(G.bones.spine1), f = fwdOf(GUYYAW), r = rightOf(GUYYAW);
  const S0 = outside(sp.clone().add(V(0, 0.035, 0)), f, 0.0, 0.32);                            // the belly surface there
  const pR = S0.clone().addScaledVector(f, 0.042 - 0.008 * push).add(V(0, 0.015 * push, 0));
  return [{ S: 'R', p: pR, w: f.clone().addScaledVector(UP, -0.4).normalize(), u: r.clone().negate().addScaledVector(UP, -0.12).normalize(), c: 95, th: 60, soft: 0.012, memAbs: 'fistR', seed: A(30, 60, -60, 120, -80, 10, 0) },
          { S: 'L', p: pR.clone().addScaledVector(f, 0.05).addScaledVector(r, -0.03), n: f.clone().negate(), u: r.clone().addScaledVector(UP, -0.25).normalize(), c: 70, th: 40, opp: 55, soft: 0.012, memAbs: 'fistL', seed: A(30, 20, 0, 115, 50) }]; }
function railHands(lift = 0) { const f = fwdOf(GUYYAW), r = rightOf(GUYYAW);                // both hands gripping the chair's top rail, either side of his belly
  return ['R', 'L'].map((S, i) => { const s = S === 'R' ? 1 : -1;
    return { S, memAbs: 'rail' + S, p: C2TOP.clone().add(V(0, 0.01 + 0.09 * lift, 0)).add(V(0, 0, -s * 0.17)).addScaledVector(f, 0.008 - 0.06 * lift), n: V(0, -1, 0), u: f.clone().addScaledVector(UP, -0.2).normalize(), c: 55, th: 40, seed: A(70, 15, 0, 60, 70) }; }); }
function tapHand(k, digit, digit2 = digit, m = 0) {              // index finger on a key; k 0 = above, 1 = touching; m slides it toward digit2 (lifted)
  const key = phone.localToWorld(KEYPOS(digit)).lerp(phone.localToWorld(KEYPOS(digit2)), m).add(V(0, 0.03 * (1 - k), 0));
  const uu = f0.clone().addScaledVector(UP, -0.9).normalize(), nn = V(0, -1, 0).addScaledVector(uu, uu.y).normalize();   // finger down and forward, palm down (no free roll)
  return { S: 'R', tip: key, p: key.clone().addScaledVector(uu, -0.095), c: 75, th: 50, point: true, u: uu, n: nn, seed: A(45, 10, 0, 90, 60) }; }
function mouthFinger(k) {                                         // beat 6: index finger into his mouth (what NOT to do)
  const m = RG.mouthW(), f = f0; const tip = m.clone().addScaledVector(f, 0.03 - 0.06 * k);
  const uu = f.clone().negate().addScaledVector(UP, 0.35).normalize();
  return { S: 'R', tip, p: tip.clone().addScaledVector(uu, -0.095), c: 85, th: 55, point: true, u: uu, seed: A(45, 20, 0, 130, 60) }; }
let GUYYAW = 180;
const LOOPSEED = { R: null, L: null };
// the state at a time ----------------------------------------------
function guyAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b], u = lt / d;
  const face = { blink: blinkAt(lt + b * 1.3) };
  let pose = SIT, root = { x: T.x, y: SEATH, z: C1Z0 + 0.06, yaw: 180 }, feet = 'sit', hands = [], chairZ = C1Z0, plateAt = PLATE1, x = 0, blue = 0, fork = 'hand', cut = false, phoneDigits = '', calling = false, fly = -1, stuckK = 0, inChair = false, air = 0;
  const rise = k => { const st = STANDP; root = { x: lerp(T.x, st.x, k), y: lerp(SEATH, 0.95, sm(k)) - 0.04 * Math.sin(Math.PI * k), z: lerp(C1Z0 + 0.06, st.z, k), yaw: 180 }; feet = k > 0.999 ? 'stand' : 'sitstand'; };
  if (b === 0 || b === 7) {
    if (b === 7) {                                                // sits back down (cut), shaky; pushes the plate away; picks the fork up again
      plateAt = PLATE0.clone().lerp(PLATE1, smooth(0.15, 0.75, lt));
      const kF = smooth(0.85, d, lt);                             // fork starts rising for the next bite (beat 0 carries on)
      const push = { S: 'L', mem: 'pushL', p: plateAt.clone().add(V(0.1, 0.035, 0)).addScaledVector(f0, -0.14), n: V(0, -1, 0), u: f0.clone().addScaledVector(r0, 0.25).normalize(), c: 20, th: 20, seed: A(30, 10, 0, 80, 20) };
      const kS = smooth(0.8, 1.35, lt);
      hands = [forkHand(0.18 * kF), kS > 0.001 ? { ...restL(1), blend: kS, from: push } : push];
      const sh = 1.5 * Math.sin(lt * 31) * (1 - smooth(0.6, d, lt));
      pose = addPose(SIT, { spine1: [-2, 0, 0], neck: [-4 + sh * 0.5, 0, 0], head: [-2, sh, 0] });
      Object.assign(face, { browIn: 0.5 * (1 - smooth(0.5, d, lt)), jaw: 0.25 * (1 - smooth(0.3, 1.0, lt)), oh: 0.2 * (1 - smooth(0.3, 1.0, lt)), look: [0, -0.35] });
      cut = lt < 0.04;
    } else {
      const kM = smooth(0.0, T_BITE, lt) * (1 - smooth(T_BITE + 0.15, T_BITE + 0.5, lt));   // fork up to the lips, bite, back down
      const choke = smooth(T_CHOKE - 0.05, T_CHOKE + 0.15, lt);
      const kFork = 0.18 + 0.82 * smooth(0, T_BITE, lt) - 0.6 * smooth(T_BITE + 0.15, T_BITE + 0.5, lt);
      const toThroat = smooth(T_CHOKE + 0.05, T_CHOKE + 0.7, lt);
      const ls = S => LOOPSEED[S] ? { seed: LOOPSEED[S], seedIsPrev: true } : {};
      const fk = { ...forkHand(kFork), ...ls('R'), mem: 'forkR' }, rl = { ...restL(1), ...ls('L'), mem: 'restL' };
      hands = toThroat > 0.001 ? throatHands().map((h, i) => ({ ...h, blend: toThroat, from: i ? rl : fk })) : [fk, rl];
      fork = lt < T_CHOKE + 0.12 ? 'hand' : 'drop';                // he lets go of the fork as his hands fly up
      const k = smooth(T_UP0, T_UP1, lt); rise(k);
      chairZ = lerp(C1Z0, C1Z1, smooth(T_UP0, T_UP0 + 0.5, lt));
      pose = mixPose(SIT, addPose(STAND, { spine1: [-4, 0, 0], neck: [10, 0, 0], head: [8, 0, 0] }), k);
      pose = addPose(pose, { neck: [12 * choke, 0, 0], head: [6 * choke, 0, 0] });
      const chew = Math.max(0, Math.sin((lt - T_BITE) * 14)) * smooth(T_BITE, T_BITE + 0.1, lt) * (1 - choke);
      Object.assign(face, { jaw: 0.45 * smooth(T_BITE - 0.22, T_BITE - 0.05, lt) * (1 - smooth(T_BITE, T_BITE + 0.08, lt)) + 0.15 * chew + 0.55 * choke, fear: choke, brow: 0.9 * choke, oh: 0.35 * choke, look: [0, -0.35 * (1 - choke)] });
      if (choke > 0) face.blink = 0;
      blue = 0.1 * smooth(T_CHOKE, d, lt);
    }
  } else if (b >= 1 && b <= 3 || b === 6) {
    feet = 'stand'; chairZ = C1Z1; root = { x: STANDP.x, y: 0.95, z: STANDP.z, yaw: 180 };
    pose = addPose(STAND, { spine1: [-4, 0, 0], neck: [10, 0, 0], head: [8, 0, 0] });
    const gag = 0.5 + 0.5 * Math.sin(lt * 9);
    if (b === 1) { hands = throatHands(); x = smooth(0.05, 0.35, lt); air = 1; Object.assign(face, { fear: 1, brow: 1, jaw: 0.4 + 0.25 * gag, oh: 0.3 * gag, blink: 0 }); blue = 0.15 + 0.15 * u;
      pose = addPose(pose, { spine1: [-6 * gag, 0, 0], neck: [6 * gag, 0, 0] }); }
    if (b === 2) { hands = throatHands(); cut = Math.abs(lt - LIPS2) < 0.02; x = lt < LIPS2 ? 0 : 1; air = 1; blue = 0.3 + 0.7 * smooth(0.0, 1.4, lt);
      Object.assign(face, { fear: 0.9, browIn: 0.8, jaw: 0.35 + 0.15 * gag, oh: 0.2, squint: 0.3, blink: 0 }); }
    if (b === 3) { blue = 1;
      if (lt < T_FIST) {                                           // taps 9, 1, 1 then the call goes through
        const taps = [T_TAP, T_TAP + 0.5, T_TAP + 1.0]; let digit = '9', digit2 = '9', m = 0, k = 0, n = 0;
        taps.forEach((t0, i) => { if (lt > t0 - 0.12) { digit = digit2 = '911'[i]; m = 0; k = Math.sin(Math.PI * clamp((lt - (t0 - 0.12)) / 0.24, 0, 1)); }
          if (i < 2 && lt > t0 + 0.12) { digit2 = '911'[i + 1]; m = smooth(t0 + 0.12, t0 + 0.38, lt); } if (lt > t0) n = i + 1; });
        phoneDigits = '911'.slice(0, n); calling = lt > T_TAP + 1.18;
        const reach = smooth(0, 0.5, lt);
        hands = [{ ...tapHand(k, digit, digit2, m), blend: reach, from: throatHands()[0] }, throatHands()[1]];
        pose = addPose(pose, { spine1: [-14 * reach, 0, 0], spine2: [-10 * reach, 0, 0], neck: [-26 * reach, 0, 0], head: [-6 * reach, 0, 0] });
        Object.assign(face, { fear: 0.8, browIn: 1, jaw: 0.3, blink: 0, look: [0, -0.8 * reach] });
      } else { phoneDigits = '911'; calling = true; GUYYAW = 180;
        hands = fistHands(0); cut = Math.abs(lt - T_FIST) < 0.02;
        pose = addPose(pose, { spine1: [-6, 0, 0], neck: [-10, 0, 0] });
        Object.assign(face, { fear: 0.7, browIn: 1, jaw: 0.3, blink: 0, look: [0, -0.6] }); }
    }
    if (b === 6) {                                                 // what NOT to do: a finger into the throat pushes the bite deeper
      const k = smooth(0.35, 1.0, lt); x = lt < 1.2 ? 0 : 1; cut = Math.abs(lt - 1.2) < 0.02; air = 1; blue = 0.6;
      hands = [{ ...mouthFinger(k), blend: smooth(0.0, 0.6, lt) }]; stuckK = smooth(1.35, 2.0, lt);
      Object.assign(face, { fear: 0.8, jaw: 0.5, oh: 0.3, blink: 0 }); }
  } else if (b === 4 || b === 5) {
    if (b === 4 && lt < T_CHAIR) {                                 // fist + hand over it: in and up
      feet = 'stand'; chairZ = C1Z1; root = { x: STANDP.x, y: 0.95, z: STANDP.z, yaw: 180 }; GUYYAW = 180; blue = 1;
      const push = Math.max(0, Math.sin(Math.PI * 2 * (lt - 0.35) / 0.6)) * smooth(0.3, 0.45, lt);
      pose = addPose(STAND, { spine1: [-8 - 6 * push, 0, 0], spine2: [-4 * push, 0, 0], neck: [-10, 0, 0] });
      hands = fistHands(push); Object.assign(face, { fear: 0.6, browIn: 1, pain: 0.5 * push, press: 0.5, blink: 0, look: [0, -0.6] });
    } else {                                                       // bent over the end chair's top rail; thrusts
      GUYYAW = 90; feet = 'stand'; inChair = true; chairZ = C1Z1; cut = b === 4 && Math.abs(lt - T_CHAIR) < 0.02;
      const s = b === 4 ? lt - T_CHAIR : lt + (DUR[4] - T_CHAIR);  // thrusts at s = 1.2 and 2.6 (the second one pops it out)
      const th = (c0) => Math.exp(-(((s - c0) / 0.11) ** 2));
      const thr = th(1.2) + th(DUR[4] - T_CHAIR + T_POP);
      const popped = b === 5 && lt > T_POP;
      const upk = popped ? smooth(T_POP + 0.15, T_POP + 1.2, lt) : 0;     // after: straightens up, gasping
      const bend = smooth(0, 0.5, s) * (1 - 0.75 * upk);
      pose = addPose(STAND, { spine1: [-30 * bend - 8 * thr, 0, 0], spine2: [-26 * bend - 6 * thr, 0, 0], chest: [-12 * bend, 0, 0], neck: [24 * bend, 0, 0], head: [10 * bend, 0, 0], thighR: [14 * bend, 0, 0], thighL: [14 * bend, 0, 0] });
      root = { x: THRUSTP.x + 0.06 * bend + 0.02 * thr, y: 0.95 - 0.07 * bend - 0.05 * thr, z: THRUSTP.z, yaw: 90 };
      hands = upk > 0.95 ? [] : railHands(smooth(0.0, 0.3, upk)).map(h => ({ ...h, blend: 1 - smooth(0.2, 0.95, upk) }));
      if (upk > 0) pose = addPose(pose, { armR: [4 * upk, 8 * upk, 0, 10 * upk], armL: [4 * upk, 8 * upk, 0, 10 * upk] });
      blue = popped ? 1 - smooth(T_POP + 0.2, DUR[5], lt) : 1;
      fly = popped ? (lt - T_POP) : -1; stuckK = 0;
      Object.assign(face, { fear: popped ? 0.3 * (1 - upk) : 0.6, browIn: popped ? 0.4 : 1, pain: popped ? 0 : 0.4 + 0.5 * thr, jaw: popped ? 0.65 * Math.exp(-(lt - T_POP) * 1.2) + 0.2 : 0.3 + 0.4 * thr, oh: popped ? 0.5 * Math.exp(-(lt - T_POP)) : 0.3 * thr, blink: 0, look: [0, popped ? 0.2 : -0.5] });
    }
  }
  return { b, lt, d, u, pose, root, feet, hands, chairZ, plateAt, x, blue, fork, cut, phoneDigits, calling, fly, stuckK, inChair, air, face };
}

// ------------------------------------------------------------------ cameras
function shakeV(t, a) { return V(vn1(t * 14, 1) * a * 0.5, vn1(t * 14, 2) * a, vn1(t * 14, 3) * a); }
const CAM0 = { pos: V(T.x + 0.16, 1.32, -0.12), tgt: V(T.x - 0.02, 1.12, C1Z0), fov: 40 };     // seated, chest-up across the table (frame one and the loop)
function camAt(t, g) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b], u = lt / d;
  const hd = wp(G.bones.head), nk = wp(G.bones.neck);
  if (b === 0) { const k = smooth(T_UP0, T_UP1 + 0.2, lt);      // follows him up as he jumps out of the chair
    return { pos: CAM0.pos.clone().add(V(0, 0.32 * k, -0.25 * k)).add(shakeV(t, 0.006 * smooth(T_CHOKE, T_CHOKE + 0.2, lt))), tgt: CAM0.tgt.clone().lerp(V(STANDP.x, 1.42, STANDP.z), k), fov: 40 + 6 * k }; }
  if (b === 7) return { pos: CAM0.pos.clone().add(V(0.05 * (1 - u), 0.03 * (1 - u), 0.06 * (1 - u))), tgt: CAM0.tgt.clone(), fov: CAM0.fov };
  if (b === 1) return { pos: nk.clone().add(V(0.06, 0.04, 0.62 - 0.08 * u)), tgt: nk.clone().add(V(0, 0.03, 0)), fov: 36 };
  if (b === 2) { if (lt < LIPS2) return { pos: hd.clone().add(V(0.06, 0.04, 0.55 - 0.08 * u)), tgt: hd.clone().add(V(0, 0.0, 0)), fov: 32 };
    return { pos: hd.clone().add(V(0.12, 0.02, 0.62 - 0.05 * u)), tgt: hd.clone().add(V(0, 0.01, 0)), fov: 36 }; }
  if (b === 3) { if (lt < T_FIST) return { pos: PHONE_AT.clone().add(V(0.32, 0.55, 0.62)), tgt: PHONE_AT.clone().add(V(0.05, 0.18, -0.12)), fov: 46 };
    const bl = wp(G.bones.spine1); return { pos: bl.clone().add(V(-0.5, 0.3, 1.55 - 0.08 * (lt - T_FIST))), tgt: bl.clone().add(V(0, 0.2, 0.1)), fov: 40 }; }
  if (b === 4 && lt < T_CHAIR) { const bl = wp(G.bones.spine1); return { pos: bl.clone().add(V(-0.42, 0.2, 1.15)), tgt: bl.clone().add(V(0, 0.12, 0.1)), fov: 38 }; }
  if (b === 4 || b === 5) {                                        // side on: belly on the rail, the bite flies out over the table end
    const thrustCam = { pos: V(C2TOP.x + 0.12, 1.12, T.z + 1.75), tgt: V(C2TOP.x - 0.05, 1.0, T.z), fov: 46 };
    if (b === 5) { const k = smooth(T_POP + 0.3, T_POP + 1.2, lt); thrustCam.tgt.lerp(nk.clone().add(V(-0.08, 0.06, 0)), k); thrustCam.pos.lerp(nk.clone().add(V(-0.35, 0.1, 1.15)), k); }
    if (b === 5) thrustCam.pos.add(shakeV(t, 0.01 * Math.exp(-Math.max(0, lt - T_POP) * 4) * (lt > T_POP ? 1 : 0)));
    return thrustCam; }
  if (b === 6) return { pos: nk.clone().add(V(-0.5, 0.1, 0.42)), tgt: nk.clone().add(V(0, 0.06, 0.04)), fov: 38 };
  return { pos: V(0, 1.5, 3), tgt: V(0, 0.5, 0), fov: 45 };
}

// ------------------------------------------------------------------ clipping: him vs the room, the furniture, the floor and his own body
const SOLIDS = [];
const sbox = (name, obj, min, max) => SOLIDS.push({ name, obj, box: new THREE.Box3(min, max) });
sbox('couch', couch, V(-1.1, 0, -0.45), V(1.1, 0.98, 0.45)); sbox('counter', counter, V(-0.33, 0, -1.5), V(0.33, 0.95, 2.35));
sbox('table top', dtable, V(-0.65, TOPY - 0.13, -0.4), V(0.65, TOPY, 0.4));
for (const [x, z] of [[-0.6, -0.35], [0.6, -0.35], [-0.6, 0.35], [0.6, 0.35]]) sbox('table leg', dtable, V(x - 0.03, 0, z - 0.03), V(x + 0.03, TOPY, z + 0.03));
for (const [nm, ch] of [['his chair', C1], ['end chair', C2]]) { sbox(nm + ' seat', ch, V(-0.22, 0.42, -0.21), V(0.22, 0.46, 0.21)); sbox(nm + ' top rail', ch, V(-0.22, 0.91, 0.1675), V(0.22, 0.98, 0.2125)); sbox(nm + ' cross rail', ch, V(-0.19, 0.675, 0.175), V(0.19, 0.725, 0.205));
  for (const x of [-0.19, 0.19]) sbox(nm + ' back post', ch, V(x - 0.02, 0.46, 0.17), V(x + 0.02, 0.98, 0.21)); }
const BODYPTS = { handR: 0.025, handL: 0.025, farmR: 0.035, farmL: 0.035, uarmR: 0.045, uarmL: 0.045, head: 0.09, chest: 0.12, hips: 0.1, shinR: 0.05, shinL: 0.05, footR: 0.04, footL: 0.04, thighR: 0.06, thighL: 0.06 };
function segDist(p, a, b) { const ab = b.clone().sub(a), t = clamp(p.clone().sub(a).dot(ab) / ab.lengthSq(), 0, 1); return p.distanceTo(a.clone().addScaledVector(ab, t)); }
const trunkDist = p => { const h = wp(G.bones.hips), c = wp(G.bones.chest), n = wp(G.bones.neck), hd = wp(G.bones.head);   // depth into his trunk or neck, given as 'distance from a 0.11 core'
  return Math.min(segDist(p, h, c), segDist(p, c, n) + 0.02, segDist(p, n, hd) + 0.055); };
// his own body surface (head, neck, torso; not the arms): skinned sample points with outward normals. A hand point is 'into own body'
// when its nearest surface point has it on the inside (depth along that point's normal). Rebuilt once per frame.
const BODYSURF = (() => { const keep = new Set(['hips', 'spine1', 'spine2', 'chest', 'neck', 'head', 'jaw', 'clavR', 'clavL', 'browR', 'browL']), out = [];
  for (const [mn, step] of [['skin_head', 10], ['shirt', 2], ['jeans', 5]]) { const m = G.meshes[mn]; if (!m) continue; const ga = m.geometry.attributes, names = m.skeleton.bones.map(b => b.name);
    for (let i = 0; i < ga.position.count; i += step) { let bw = -1, bi = 0; for (let k = 0; k < 4; k++) { const w = ga.skinWeight.getComponent(i, k); if (w > bw) { bw = w; bi = ga.skinIndex.getComponent(i, k); } }
      if (keep.has(names[bi])) out.push([m, i]); } }
  return out; })();
let SURF = null, SURFF = -1;
const _v = new THREE.Vector3(), _w = new THREE.Vector3();
function surfNow() { const n = BODYSURF.length, P = new Float32Array(n * 3), N = new Float32Array(n * 3);
  for (let j = 0; j < n; j++) { const [m, i] = BODYSURF[j], ga = m.geometry.attributes;
    const a = V(ga.position.getX(i), ga.position.getY(i), ga.position.getZ(i)), b = a.clone().add(V(ga.normal.getX(i), ga.normal.getY(i), ga.normal.getZ(i)).multiplyScalar(0.01));
    m.applyBoneTransform(i, a); b.set(ga.position.getX(i) + ga.normal.getX(i) * 0.01, ga.position.getY(i) + ga.normal.getY(i) * 0.01, ga.position.getZ(i) + ga.normal.getZ(i) * 0.01);
    // the normal tip is skinned with the same vertex weights
    const sw = m.geometry.attributes.position; const save = [sw.getX(i), sw.getY(i), sw.getZ(i)]; sw.setXYZ(i, b.x, b.y, b.z); m.applyBoneTransform(i, b); sw.setXYZ(i, ...save);
    a.applyMatrix4(m.matrixWorld); b.applyMatrix4(m.matrixWorld); b.sub(a).normalize();
    P.set([a.x, a.y, a.z], j * 3); N.set([b.x, b.y, b.z], j * 3); }
  return { P, N, n }; }
function bodyDepth(p) { let bd = 1e9, bj = 0; const { P, N, n } = SURF;
  for (let j = 0; j < n; j++) { const dx = p.x - P[j * 3], dy = p.y - P[j * 3 + 1], dz = p.z - P[j * 3 + 2], d = dx * dx + dy * dy + dz * dz; if (d < bd) { bd = d; bj = j; } }
  return -((p.x - P[bj * 3]) * N[bj * 3] + (p.y - P[bj * 3 + 1]) * N[bj * 3 + 1] + (p.z - P[bj * 3 + 2]) * N[bj * 3 + 2]); }   // > 0 = inside
let BODYNOW = null, LASTH = [];
function depthAll(p) { const { P, N, n } = BODYNOW; let bd = 1e9, bj = 0; for (let j = 0; j < n; j++) { const dx = p.x - P[j * 3], dy = p.y - P[j * 3 + 1], dz = p.z - P[j * 3 + 2], d = dx * dx + dy * dy + dz * dz; if (d < bd) { bd = d; bj = j; } }
  return -((p.x - P[bj * 3]) * N[bj * 3] + (p.y - P[bj * 3 + 1]) * N[bj * 3 + 1] + (p.z - P[bj * 3 + 2]) * N[bj * 3 + 2]); }
function outside(p, dir, gap, reach = 0.15) {                  // the point on the line p + s*dir (0 <= s <= reach) that sits gap outside his skin, found from the outside in
  const q = p.clone().addScaledVector(dir, reach); if (!BODYNOW) return p.clone();
  for (let k = 0; k * 0.003 < reach; k++) { if (depthAll(q.clone().addScaledVector(dir, -0.003)) > -gap) return q; q.addScaledVector(dir, -0.003); } return q; }
window.costParts = (i) => { stepTo(i); return LASTH.map(h => { const a = RG.LAST['arm' + h.S], f = RG.handFK(h.S, a); const cc = RG.contactCost(h)();
  return h.S + (h.free ? ' FREE' : '') + ' pos ' + (f.p.distanceTo(h.p) * 100).toFixed(1) + 'cm n ' + (h.n ? f.n.dot(h.n).toFixed(2) : '-') + ' w ' + (h.w ? f.w.dot(h.w).toFixed(2) : '-') + ' u ' + (h.u ? f.u.dot(h.u).toFixed(2) : '-') + ' contact ' + cc.toFixed(1) + ' extra ' + (h.extra ? h.extra(f).toFixed(1) : '-') + ' arm ' + a.map(v => v.toFixed(0)).join(','); }).join(' | '); };
const TIPS = ['index', 'middle', 'pinky', 'thumb'];
RG.contactCost = h => { const S = h.S, c0 = h.p, near = [];
  if (BODYNOW) { const { P, N, n } = BODYNOW; for (let j = 0; j < n; j++) { const dx = P[j * 3] - c0.x, dy = P[j * 3 + 1] - c0.y, dz = P[j * 3 + 2] - c0.z; if (dx * dx + dy * dy + dz * dz < 0.3 * 0.3) near.push(j); } }
  const NP = new Float32Array(near.length * 3), NN = new Float32Array(near.length * 3); near.forEach((j, k) => { for (let a = 0; a < 3; a++) { NP[k * 3 + a] = BODYNOW.P[j * 3 + a]; NN[k * 3 + a] = BODYNOW.N[j * 3 + a]; } });
  const solids = SOLIDS.filter(sd => sd.obj.visible && !/^(couch|counter)/.test(sd.name)).map(sd => ({ inv: sd.obj.matrixWorld.clone().invert(), box: sd.box }));
  const CS = 0.025, cell = (x, y, z) => (Math.floor(x / CS) + 512) * 1048576 + (Math.floor(y / CS) + 512) * 1024 + (Math.floor(z / CS) + 512), GRID = new Map();
  for (let k = 0; k < near.length; k++) { const key = cell(NP[k * 3], NP[k * 3 + 1], NP[k * 3 + 2]); let a = GRID.get(key); if (!a) GRID.set(key, a = []); a.push(k); }
  const depthB = p => { if (!near.length) return -1; let bd = 1e9, bj = -1; const cx = Math.floor(p.x / CS), cy = Math.floor(p.y / CS), cz = Math.floor(p.z / CS);
    for (let i = -1; i <= 1; i++) for (let j = -1; j <= 1; j++) for (let l = -1; l <= 1; l++) { const a = GRID.get((cx + i + 512) * 1048576 + (cy + j + 512) * 1024 + (cz + l + 512)); if (a) for (const k of a) { const dx = p.x - NP[k * 3], dy = p.y - NP[k * 3 + 1], dz = p.z - NP[k * 3 + 2], d = dx * dx + dy * dy + dz * dz; if (d < bd) { bd = d; bj = k; } } }
    if (bj < 0) for (let k = 0; k < near.length; k++) { const dx = p.x - NP[k * 3], dy = p.y - NP[k * 3 + 1], dz = p.z - NP[k * 3 + 2], d = dx * dx + dy * dy + dz * dz; if (d < bd) { bd = d; bj = k; } }
    return -((p.x - NP[bj * 3]) * NN[bj * 3] + (p.y - NP[bj * 3 + 1]) * NN[bj * 3 + 1] + (p.z - NP[bj * 3 + 2]) * NN[bj * 3 + 2]); };
  const depthS = p => { let m = -1; for (const sd of solids) { const q = p.clone().applyMatrix4(sd.inv), b = sd.box; m = Math.max(m, Math.min(q.x - b.min.x, b.max.x - q.x, q.y - b.min.y, b.max.y - q.y, q.z - b.min.z, b.max.z - q.z)); } return m; };
  return () => { let c = 0; const pts = TIPS.map(f => [RG.tip(f, S), 0.008]); pts.push([RG.palmW(S), 0.004]); const el = wp(G.bones['farm' + S]);
    if (h.point && S === 'R' && STATE && STATE.b === 6) pts.shift();                                  // beat 6: the index goes in his mouth on purpose
    const soft = h.soft || 0; for (const [p, r] of pts) { const d = Math.max(depthB(p) - soft, depthS(p)) + r - 0.003; if (d > 0) c += (d / 0.002) ** 2; }
    { const d = depthB(el) + 0.03 - 0.003; if (d > 0) c += (d / 0.003) ** 2; }
    { const d = depthB(wp(G.bones['hand' + S])) + 0.024 - 0.003 - soft; if (d > 0) c += (d / 0.002) ** 2; }
    return c; }; };
let STATE = null;
function clipScan() { const out = []; scene.updateMatrixWorld(true);
  if (!G.root.visible) return out;
  const pts = Object.entries(BODYPTS).map(([n, r]) => [n, n.startsWith('thigh') ? wp(G.bones[n]).lerp(wp(G.bones['shin' + n.slice(-1)]), 0.5) : wp(G.bones[n]), r]);
  for (const S of ['R', 'L']) for (const f of ['index', 'middle', 'pinky', 'thumb']) pts.push([f + ' tip ' + S, RG.tip(f, S), 0.008]);
  pts.push(['fork tip', fork.localToWorld(FORK_TIP.clone()), 0.004]);
  const headC = wp(G.bones.head).add(V(0, 0.09, 0).applyQuaternion(wq(G.bones.head)));
  const st = STATE || {};
  for (const [n, p, r] of pts) {
    if (n === 'fork tip' && !fork.visible) continue;
    if (p.y - r < -0.015) out.push({ what: 'him ' + n, into: 'floor', depth: +((-(p.y - r)) * 100).toFixed(1) });
    for (const S of SOLIDS) { if (!S.obj.visible) continue; const q = p.clone().applyMatrix4(S.obj.matrixWorld.clone().invert()), bx = S.box;
      if (st.b === 0 || st.b === 7) { if (S.name.startsWith('his chair seat') && /^(hips|thigh)/.test(n)) continue; }        // sitting on it
      if (n === 'fork tip' && S.name === 'table top') continue;
      const dx = Math.min(q.x - bx.min.x, bx.max.x - q.x), dy = Math.min(q.y - bx.min.y, bx.max.y - q.y), dz = Math.min(q.z - bx.min.z, bx.max.z - q.z);
      const dd = Math.min(dx, dy, dz) + r; if (dx > -r && dy > -r && dz > -r && dd > 0.012) out.push({ what: 'him ' + n, into: S.name, depth: +(dd * 100).toFixed(1) }); }
    if (/^(hand|farm|index|middle|pinky|thumb)/.test(n)) { if (!SURF) SURF = surfNow();
      if (st.b === 6 && /^index tip R/.test(n)) continue;                                                   // the finger in his mouth is the point of beat 6
      const dB = bodyDepth(p) + r; if (dB > (st.soft ? 0.024 : 0.012)) out.push({ what: 'him ' + n, into: 'own body', depth: +(dB * 100).toFixed(1) }); } }
  SURF = null;
  return out; }

// ------------------------------------------------------------------ per-frame update
let LASTF = -10;
const RAILQ = new THREE.Quaternion();
function placeFork() {                                            // the fork rides in his right hand: handle across the palm, tines out past the index side (-w)
  const q = wq(G.bones.handR), h = RG.HANDREST.R, n = h.n.clone().applyQuaternion(q), w = h.w.clone().applyQuaternion(q);
  const x = w.clone().negate(), y = n.clone().sub(x.clone().multiplyScalar(n.dot(x))).normalize(), z = new THREE.Vector3().crossVectors(x, y);
  fork.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(x, y, z));
  const u = h.u.clone().applyQuaternion(q);
  fork.position.copy(RG.palmW('R')).addScaledVector(u, FORKGRIP.u).addScaledVector(n, FORKGRIP.n).addScaledVector(x, -FORKGRIP.x);
}
function update(t, frame) {
  t = ((t % TOTAL) + TOTAL) % TOTAL;
  const g = guyAt(t); STATE = { b: g.b, throat: g.hands.length && g.hands[0] && g.hands[0].n && (g.b <= 2 || (g.b === 3 && g.lt < T_FIST)) };
  // furniture
  C1.position.set(T.x, 0, g.chairZ); C2.visible = true;
  plate.position.copy(g.plateAt);
  // him
  RG.applyPose(g.pose, g.root);
  const yaw = g.root.yaw, f = fwdOf(yaw), r = rightOf(yaw);
  if (g.feet === 'stand' || g.feet === 'sitstand' || g.feet === 'sit') {
    const ground = V(g.root.x, 0, g.root.z);
    for (const [S, sx] of [['R', 0.11], ['L', -0.11]]) {
      let fp;
      if (g.feet === 'sit') fp = ground.clone().addScaledVector(f, 0.44).addScaledVector(r, sx * 1.05);
      else if (g.feet === 'sitstand') { const st = V(STANDP.x, 0, STANDP.z); const k = clamp((g.root.y - SEATH) / (0.95 - SEATH), 0, 1);
        fp = V(T.x, 0, C1Z0 + 0.06).addScaledVector(fwdOf(180), 0.44).lerp(st.clone().addScaledVector(fwdOf(180), 0.04), smooth(0.45, 1, k)).addScaledVector(r, sx * 1.05); }
      else fp = ground.clone().addScaledVector(r, sx).addScaledVector(f, (g.inChair ? -0.06 : 0) + (S === 'R' ? 0.02 : -0.02));
      fp.y = ANKLEH;
      RG.foot(S, fp, fp.clone().add(V(0, 0.45, 0)).addScaledVector(f, 1), yawQ(yaw)); }
  }
  G.root.updateMatrixWorld(true);
  // hands (targets read his body, so build them again now that this frame's pose is on)
  BODYNOW = surfNow(); g.hands = guyAt(t).hands; STATE.soft = g.hands.some(h => h.soft);
  const list = [];
  for (const h of g.hands) {
    if (h.point) { const tipT = h.tip; h.extra = () => RG.tip('index', 'R').distanceToSquared(tipT) / (0.005 * 0.005); }
    list.push(h); }
  if (list.length) {
    const key = 'b' + g.b + (g.b === 3 && g.lt >= T_FIST ? 'f' : '') + (g.b === 4 && g.lt >= T_CHAIR || g.b === 5 ? 'c' : '') + (g.b === 2 && g.lt >= LIPS2 ? 'x' : '');
    RG.hands(list, key, frame); LASTH = list;
  } else { delete RG.LAST.costR; delete RG.LAST.costL; }
  for (const S of ['R', 'L']) if (!g.hands.some(h => h.S === S)) { delete RG.LAST['cost' + S]; }
  G.root.updateMatrixWorld(true); RG.untwist(); G.face(g.face); G.root.updateMatrixWorld(true);
  // the fork
  fork.visible = true; BITE.visible = g.b === 7 && g.lt > 0.85 || (g.b === 0 && g.lt < T_BITE + 0.05);
  const forkRestP = g.plateAt.clone().add(V(0.12, 0.012, 0.03)), forkRestQ = yawQ(200);
  if (g.fork === 'hand') placeFork();
  else if (g.fork === 'drop' && FORKREL) { const s = clamp((g.lt - T_CHOKE - 0.12) / 0.3, 0, 1);      // falls onto the table by the plate
    fork.position.copy(FORKREL.p).lerp(forkRestP, s); fork.position.y = lerp(FORKREL.p.y, forkRestP.y, s * s) + 0.03 * Math.sin(Math.PI * s) * (1 - s);
    fork.quaternion.copy(FORKREL.q).slerp(forkRestQ, Math.min(1, s * 1.15)); }
  else { fork.position.copy(forkRestP); fork.quaternion.copy(forkRestQ); }
  if (g.b >= 1 && g.b <= 6) { fork.position.copy(PLATE1).add(V(0.12, 0.012, 0.03)); fork.quaternion.copy(yawQ(200)); }
  // phone screen
  const ps = g.phoneDigits + (g.calling ? '!' : ''); if (ps !== phoneTexState) { drawPhone(g.phoneDigits, g.calling); phoneTexState = ps; }
  // x-ray, air, the stuck bite
  setXray(g.x); BLUE.value = g.blue;
  stuck.position.copy(STUCKL0).lerp(STUCKL1, g.stuckK);
  if (airPts.m.visible) { const top = wp(G.bones.head).add(V(0, -0.05, 0.0)).addScaledVector(f, 0.07), block = stuck.getWorldPosition(new THREE.Vector3());
    for (let i = 0; i < 90; i++) { const s = (hash1(i * 3) + t * 0.9) % 1, p = top.clone().lerp(block.clone().add(V(0, 0.016, 0)), Math.min(s * 1.25, 1)).add(V((hash1(i) - 0.5) * 0.012, 0, (hash1(i * 5) - 0.5) * 0.012)); airPts.p.set([p.x, p.y, p.z], i * 3); }
    airPts.m.geometry.attributes.position.needsUpdate = true; }
  brain.visible = brain.visible && g.b === 2;
  brainM.emissiveIntensity = g.b === 2 ? 0.9 * (1 - 0.8 * smooth(LIPS2, g.d, g.lt)) * (0.75 + 0.25 * Math.sin(t * 9)) : 0.9;
  redX.visible = g.b === 6 && g.lt > 1.6; if (redX.visible) { const nk = wp(G.bones.neck); redX.position.copy(nk).add(V(0.05, 0.02, 0.08)); redX.lookAt(camera.position); redX.scale.setScalar(Math.min(1, (g.lt - 1.6) / 0.15)); }
  // the bite flying out (beat 5): from his mouth forward over the table end, lands on the table
  flyBite.visible = g.fly >= 0;
  if (flyBite.visible) { const m0 = FLY0 || RG.mouthW(); const s = Math.min(g.fly, 0.5) / 0.5, dir = fwdOf(90);
    const land = V(T.x + 0.45, TOPY + 0.011, T.z + 0.12);
    const p = m0.clone().lerp(land, s); p.y = lerp(m0.y, land.y, s) + 0.28 * Math.sin(Math.PI * s) * (1 - s * 0.3); flyBite.position.copy(p); flyBite.rotation.set(g.fly * 14, g.fly * 9, 0);
    if (g.fly >= 0.5) { flyBite.position.copy(land); flyBite.rotation.set(0, 0.4, 0); } }
  if (g.b === 5 && g.lt < T_POP + 0.02) FLY0 = RG.mouthW();
  // camera and light
  const C = camAt(t, g); camera.position.copy(C.pos); camera.up.set(0, 1, 0); camera.lookAt(C.tgt); camera.fov = C.fov; camera.updateProjectionMatrix();
  const dim = 1 - 0.8 * g.x;
  sun.position.set(1.6, 3.4, 2.4); sun.target.position.set(0, 0, 0); sun.target.updateMatrixWorld();
  sun.intensity = 2.6 * dim; hemi.intensity = 0.85 * dim; scene.environmentIntensity = 0.35 * dim; lamp.intensity = 6 * dim;
  scene.background = new THREE.Color(0xd9cbb6).multiplyScalar(dim);
  // the wall clock behind him just keeps time
  clockHands.s.rotation.z = -t * 6 * D2R * 60 / 60; clockHands.m.rotation.z = -1.1; clockHands.h.rotation.z = -3.3;
  return { beat: g.b, cut: g.cut };
}
let FLY0 = null, FORKREL = null;
// measure the fork reach (palm point -> tine tip) and the ankle height once
G.reset(); G.root.updateMatrixWorld(true);
const ANKLEH = wp(G.bones.footR).y;


// ------------------------------------------------------------------ frame I/O (same contract as the other 3D Shorts)
const draw = () => { if (XRNEW) { renderer.render(scene, camera); XRNEW = false; } renderer.render(scene, camera); };
const gl = renderer.getContext(), px = new Uint8Array(W * H * 4);
let CUTF = false, LASTB = 0;
function stepTo(i) { const t = i / FPS, b = beatAt(((t % TOTAL) + TOTAL) % TOTAL);
  if (i !== LASTF + 1) { const tt = ((t % TOTAL) + TOTAL) % TOTAL, lt = tt - B[b];   // not the next frame: replay its whole hold from where that hold starts cold,
    const seg = b === 4 && lt < T_CHAIR ? B[3] + T_FIST : b === 5 || b === 4 ? B[4] + T_CHAIR : b === 3 && lt >= T_FIST ? B[3] + T_FIST : B[b];   // so a chunked render matches a straight one
    for (let j = Math.ceil(seg * FPS - 1e-6) + Math.floor(t / TOTAL) * Math.round(TOTAL * FPS); j < i; j++) update(j / FPS, j); }
  const r = update(t, i); CUTF = r.cut; LASTB = r.beat; LASTF = i; }
for (let i = Math.ceil(B[7] * FPS); i < Math.round(TOTAL * FPS); i++) update(i / FPS, i);
{ const LS = { R: RG.LAST.armR.slice(), L: RG.LAST.armL.slice() }; LOOPSEED.R = LS.R; LOOPSEED.L = LS.L;
  for (let i = 0; i <= Math.floor((T_CHOKE + 0.12) * FPS); i++) stepTo(i);                  // where the fork is when he lets go (it falls from there)
  FORKREL = { p: fork.position.clone(), q: fork.quaternion.clone() };
  for (let i = Math.ceil(B[7] * FPS); i < Math.round(TOTAL * FPS); i++) update(i / FPS, i); }
LOOPSEED.R = RG.LAST.armR.slice(); LOOPSEED.L = RG.LAST.armL.slice();
draw(); stepTo(Math.round((B[1] + 1) * FPS)); draw();            // warm-up: compile the normal and the x-ray shaders now (a ghost first drawn later came out blank)
for (const k of Object.keys(RG.MEM)) delete RG.MEM[k]; LASTF = -10;
window.renderAll = async (f0, f1) => { for (let i = f0; i < f1; i++) { stepTo(i); draw(); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); await fetch('/frame', { method: 'POST', body: px }); } return 'ok'; };
window.renderAtT = t => { const i = Math.round(t * FPS); stepTo(i);
  if (window.CAM && window.CAM.hand) { const hp = RG.palmW(window.CAM.hand); window.CAM.tgt = hp.toArray(); window.CAM.pos = hp.clone().add(V(...window.CAM.off)).toArray(); }
  if (window.CAM) { camera.position.set(...window.CAM.pos); camera.up.set(0, 1, 0); camera.lookAt(...window.CAM.tgt); camera.fov = window.CAM.fov || 42; camera.updateProjectionMatrix(); }
  draw(); return renderer.domElement.toDataURL('image/png'); };
window.rigReport = i => { stepTo(i); const t = i / FPS, iq = G.root.getWorldQuaternion(new THREE.Quaternion()).invert();
  const ang = { ...RG.LAST }; delete ang.costR; delete ang.costL;
  return { t, beat: LASTB, ang, hips: wp(G.bones.hips).toArray(), car: 0, show: true, cut: CUTF,
    thumbs: ['R', 'L'].map(S => wp(G.bones['index1' + S]).sub(wp(G.bones['pinky1' + S])).applyQuaternion(iq).toArray()),
    forearms: ['R', 'L'].map(S => wp(G.bones['hand' + S]).sub(wp(G.bones['farm' + S])).normalize().applyQuaternion(iq).toArray()),
    cost: [RG.LAST.costR ?? null, RG.LAST.costL ?? null], clip: clipScan() }; };
window.dbg = { outside, depthAll, fistHands, setBN: () => { BODYNOW = surfNow(); },  G, RG, wp, THREE, fork, LOOPSEED, XRAY, setXray, update, guyAt, forkHand, xrayMat, renderer, scene, camera };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS);
window.READY = true;
