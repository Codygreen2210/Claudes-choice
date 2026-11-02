// "You just got strapped to a rocket sled. Here's what happens next." - a 3D Short on the MakeHuman man (the 1954 Sonic Wind run).
//   sled_mh.html?w=1080&h=1920            (times from sled/times.json; one shot per narration line)
// Beats: 0 ignition (hook) | 1 onboard: nine rockets slam him back | 2 tracking: 632 mph | 3 drone: the desert blurs | 4 SLOW MOTION: the scoop hits the water
//        5 onboard: the 1.4 s stop | 6 REPLAY: 46 G bullet-time | 7 the eye: vessels burst, it goes dark | 8 1954 newsreel, then a car seat belt clicks | 9 back at the start line (loops)
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { loadGuy } from '/guy3d.js';

const Q = new URLSearchParams(location.search);
const W = +Q.get('w') || 720, H = +Q.get('h') || 1280;
const FPS = 30;
const TIMES = await (await fetch('/sled/times.json')).json();
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
const G = await loadGuy(THREE, '/char/' + (Q.get('char') || window.CHARDEF || 'guy'), { fingers3: !!window.FINGERS3 });      // ?char=mh or window.CHARDEF: the MakeHuman man
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
function curl(p, S, c, th = c) { for (const f of FINGERS) { p[f + '1' + S] = [0, 0, (S === 'R' ? -1 : 1) * c * 0.9]; p[f + '2' + S] = [0, 0, (S === 'R' ? -1 : 1) * c]; } p['thumb1' + S] = [0, 0, (S === 'R' ? -1 : 1) * th * 0.4]; for (const f of FINGERS) p[f + '3' + S] = [0, 0, (S === 'R' ? -1 : 1) * c * 0.7]; return p; }
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
    for (const [n, e] of Object.entries(pp)) if (Gx.bones[n]) Gx.bones[n].quaternion.copy(Gx.REST[n].q).multiply(qTmp.setFromEuler(eTmp.set(e[0] * D2R, e[1] * D2R, e[2] * D2R))); };
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
  R.tip = (f, S) => { if (Gx.fingers3 && Gx.bones[f + '3' + S]) return Gx.tailW(f + '3' + S); const b2 = Gx.bones[f + '2' + S]; return wp(b2).add(TIPSEG[f + S].clone().applyQuaternion(wq(b2))); };
  return R;
}
const RG = makeRig(G, 'him');
G.reset(); G.root.updateMatrixWorld(true);
const EAR_L = V(0.08, 1.64, 0.01).applyMatrix4(G.bones.head.matrixWorld.clone().invert());
// ================================================================== THE ROCKET SLED
// ------------------------------------------------------------------ the desert test track (the room is hidden). The sled stays at the origin and the world
// slides past it (distance D in metres), so nothing ever gets far from the origin at 632 mph.
home.visible = false;
const SEATTOP = 0.74, RAIL = 0.62;
const SKYG = new THREE.Group(); scene.add(SKYG);                    // rides with the camera
{ const g = new THREE.SphereGeometry(200, 32, 20), c = new Float32Array(g.attributes.position.count * 3), lo = new THREE.Color(0xf2e8d8), hi = new THREE.Color(0x4e86c8);
  for (let i = 0; i < g.attributes.position.count; i++) { const y = g.attributes.position.getY(i) / 200, k = Math.pow(clamp(y * 3.2, 0, 1), 0.55), col = lo.clone().lerp(hi, k); c.set([col.r, col.g, col.b], i * 3); }
  g.setAttribute('color', new THREE.BufferAttribute(c, 3));
  SKYG.add(new THREE.Mesh(g, new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.BackSide, depthWrite: false, fog: false }))); }
// far mountains (static, so the near world reads as the thing moving)
const MTN = new THREE.Group(); scene.add(MTN);
{ const mm = new THREE.MeshStandardMaterial({ color: 0x8a7e72, roughness: 1 });
  for (let i = 0; i < 60; i++) { const a = i / 60 * Math.PI * 2, r = 150 + 25 * hash1(i * 3.1), h = 8 + 22 * Math.pow(hash1(i * 7.7), 1.5);
    const m = new THREE.Mesh(new THREE.ConeGeometry(14 + 14 * hash1(i), h, 6), mm); m.position.set(Math.cos(a) * r, h / 2 - 1, Math.sin(a) * r); m.rotation.y = hash1(i * 2) * 3; MTN.add(m); } }
// the ground: gypsum sand plus the track's ties, drawn in the shader from the distance D, and averaged along the run over one frame's travel
// (so at full speed it smears into streaks instead of strobing)
const GU = { uD: { value: 0 }, uStep: { value: 0 } };
const groundM = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.95 });
groundM.onBeforeCompile = sh => { Object.assign(sh.uniforms, GU);
  sh.vertexShader = 'varying vec3 vWp;\n' + sh.vertexShader.replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\n vWp = (modelMatrix * vec4(transformed, 1.0)).xyz;');
  sh.fragmentShader = 'varying vec3 vWp; uniform float uD, uStep;\n' + GLSLN + `
    vec3 sandAt(vec2 p){ float n = vn(p * 1.7) * 0.5 + vn(p * 6.0) * 0.3 + vn(p * 23.0) * 0.2;
      vec3 c = mix(vec3(0.66, 0.58, 0.47), vec3(0.86, 0.79, 0.67), n);
      float onTrack = step(abs(p.x), 0.82);
      float tie = step(fract(p.y / 0.9), 0.2) * onTrack;
      c = mix(c, vec3(0.32, 0.24, 0.17), tie * 0.9);
      c = mix(c, vec3(0.58, 0.52, 0.45), onTrack * (1.0 - tie) * 0.55);
      return c; }
  ` + sh.fragmentShader.replace('#include <map_fragment>', `#include <map_fragment>
    { vec3 acc = vec3(0.0); for (int i = 0; i < 10; i++) { float f = float(i) / 9.0; acc += sandAt(vec2(vWp.x, -vWp.z + uD + f * uStep)); }
      diffuseColor.rgb *= acc / 10.0; }`); };
const ground = new THREE.Mesh(new THREE.PlaneGeometry(700, 700, 1, 1).rotateX(-Math.PI / 2), groundM); ground.receiveShadow = true; scene.add(ground);
// rails (smooth steel: they look the same at any speed)
const railM = new THREE.MeshStandardMaterial({ color: 0x8a8c90, roughness: 0.3, metalness: 0.85 });
for (const x of [-RAIL, RAIL]) { const r = new THREE.Mesh(new THREE.BoxGeometry(0.07, 0.12, 700), railM); r.position.set(x, 0.06, 0); r.receiveShadow = r.castShadow = true; scene.add(r); }
// poles beside the track every 30 m (they stretch into streaks at speed)
const POLES = []; const poleM = new THREE.MeshStandardMaterial({ color: 0x5a4636, roughness: 0.9 });
for (let i = 0; i < 16; i++) { const p = new THREE.Mesh(new THREE.BoxGeometry(0.16, 4.5, 0.16), poleM); p.castShadow = true; scene.add(p);
  const arm = new THREE.Mesh(new THREE.BoxGeometry(1.2, 0.1, 0.1), poleM); arm.position.y = 2.0; p.add(arm); POLES.push({ p, k: i, x: (i % 2 ? -1 : 1) * 3.6 }); }

// ------------------------------------------------------------------ the sled: a steel frame on rail slippers, the seat and straps, nine rockets behind, the scoop underneath
const sled = new THREE.Group(); scene.add(sled);
const steel = new THREE.MeshStandardMaterial({ color: 0xb8bcc2, roughness: 0.35, metalness: 0.8 }), redP = new THREE.MeshStandardMaterial({ color: 0xc8302a, roughness: 0.45, metalness: 0.2 });
const darkM = mat(0x22252a, 0.5, 0.4), seatM = mat(0x3a2e24, 0.8);
for (const x of [-RAIL, RAIL]) { box(0.14, 0.1, 2.4, x, 0.17, -0.25, darkM, 0.02, sled); box(0.06, 0.5, 0.06, x, 0.42, 0.6, steel, 0, sled); box(0.06, 0.5, 0.06, x, 0.42, -1.0, steel, 0, sled); }
// the deck, with a foot well cut in front of the seat (his shins hang down into it, onto the footrest)
const DECK = [box(1.36, 0.08, 1.55, 0, 0.66, -0.625, redP, 0.02, sled)];
for (const x of [-0.49, 0.49]) DECK.push(box(0.38, 0.08, 0.75, x, 0.66, 0.525, redP, 0.02, sled));
DECK.push(box(1.36, 0.08, 0.12, 0, 0.66, 0.96, redP, 0.02, sled));
for (const x of [-0.31, 0.31]) box(0.02, 0.4, 0.75, x, 0.44, 0.525, steel, 0, sled);      // the well's side walls
box(0.56, 0.06, 0.5, 0, SEATTOP - 0.03, 0.02, seatM, 0.02, sled);                       // seat pan
box(0.56, 0.78, 0.07, 0, SEATTOP + 0.39, -0.24, seatM, 0.02, sled);                     // backrest
box(0.3, 0.26, 0.08, 0, SEATTOP + 0.9, -0.24, seatM, 0.03, sled);                       // headrest
box(0.58, 0.04, 0.36, 0, 0.3, 0.5, steel, 0.01, sled);                                  // footrest plate down in the well (its height is set at load from his feet)
const footrest = sled.children[sled.children.length - 1];
for (const x of [-0.31, 0.31]) box(0.05, 0.5, 0.05, x, SEATTOP + 0.2, -0.22, steel, 0, sled);
// armrests beside the seat: his forearms are strapped down to them (the 1954 riders' arms were strapped; placed at load from his arms)
const ARMS = {}; const armPadM = new THREE.MeshStandardMaterial({ color: 0x2c2420, roughness: 0.75 });
for (const S of ['R', 'L']) { const g = new THREE.Group(); sled.add(g); box(0.11, 0.045, 0.42, 0, -0.0225, 0, armPadM, 0.015, g); g.userData.post = box(0.035, 1, 0.035, 0, -0.5, -0.12, steel, 0, g); ARMS[S] = g; }
// the rocket pack: a 3 x 3 block of tubes behind the seat, nozzles facing back
const pack = new THREE.Group(); pack.position.set(0, 1.0, -1.05); sled.add(pack);
box(0.98, 0.98, 0.2, 0, 0, 0.5, redP, 0.03, pack);
const NOZ = [];
for (let r = 0; r < 3; r++) for (let c = 0; c < 3; c++) { const x = (c - 1) * 0.3, y = (r - 1) * 0.3;
  const tube = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 0.9, 20).rotateX(Math.PI / 2), steel); tube.position.set(x, y, 0); tube.castShadow = true; pack.add(tube);
  const nz = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.13, 0.16, 20, 1, true).rotateX(Math.PI / 2), darkM); nz.material = darkM.clone(); nz.material.side = THREE.DoubleSide; nz.position.set(x, y, -0.52); pack.add(nz);
  NOZ.push(V(x, y + 1.0, -1.05 - 0.6)); }
// the scoop: a blade under the front that drops into the water pools
const scoop = box(0.36, 0.22, 0.08, 0, 0.12, 0.95, steel, 0.01, sled); scoop.rotation.x = 0.5;
// his flight helmet: a full shell over the crown, sides and back, open at the face, goggles pushed up on the front.
// Built in rest space (his face looks along +z at rest), then moved into the head bone's frame.
const helmet = new THREE.Group();
{ G.reset(); G.root.updateMatrixWorld(true); const hb = G.bones.head;
  const E = wp(G.bones.eyeR).add(wp(G.bones.eyeL)).multiplyScalar(0.5), fd = E.clone().sub(V(...G.man.headC)).setY(0).normalize();   // measured: where his eyes look at rest
  const hc = E.clone().addScaledVector(fd, -0.075).add(V(0, 0.022, 0));
  const shellM = new THREE.MeshStandardMaterial({ color: 0xdedbd0, roughness: 0.35, metalness: 0.05, side: THREE.DoubleSide });
  const R0 = 0.132, TC = Math.PI * 0.3, OPEN = 1.75;
  const crown = new THREE.Mesh(new THREE.SphereGeometry(R0, 40, 12, 0, Math.PI * 2, 0, TC), shellM); helmet.add(crown);
  const sides = new THREE.Mesh(new THREE.SphereGeometry(R0, 40, 18, Math.PI * 0.5 + OPEN / 2, Math.PI * 2 - OPEN, TC, Math.PI * 0.64 - TC), shellM); helmet.add(sides);   // the gap is centred on +z (the face)
  // the visor, down: a dark tinted shield over the whole face opening (his face doesn't show through it)
  const visorM = new THREE.MeshStandardMaterial({ color: 0x0c0e12, roughness: 0.06, metalness: 0.7, side: THREE.DoubleSide });
  const visor = new THREE.Mesh(new THREE.SphereGeometry(R0 * 1.015, 32, 16, Math.PI * 0.5 - OPEN / 2 - 0.06, OPEN + 0.12, TC - 0.06, Math.PI * 0.8 - TC + 0.06), visorM); helmet.add(visor);   // down past the chin
  helmet.children.forEach(o => o.scale.set(1.0, 1.05, 1.1));
  helmet.rotation.y = Math.atan2(fd.x, fd.z);   // turn the opening (built on +z) to face his eyes
  helmet.position.copy(hc); hb.updateMatrixWorld(true); const inv = hb.matrixWorld.clone().invert(); helmet.applyMatrix4(inv); hb.add(helmet); helmet.traverse(o => { if (o.isMesh) o.castShadow = true; }); }
// his flight suit: an olive coverall (the shirt and trousers recoloured, the arm skin painted as sleeves), leather gloves, black boots
{ const OLIVE = 0x5c5e3c;
  for (const n of ['shirt', 'jeans']) { const m = G.meshes[n]; if (!m) continue; m.material = m.material.clone(); m.material.map = null; m.material.color.set(OLIVE); m.material.roughness = 0.9; m.material.needsUpdate = true; }
  for (const n of ['shoeR', 'shoeL']) { const m = G.meshes[n]; if (!m) continue; m.material = m.material.clone(); m.material.map = null; m.material.color.set(0x1e1b18); m.material.roughness = 0.45; m.material.needsUpdate = true; }
  const sk = G.meshes.skin_head, ga = sk.geometry.attributes, names = sk.skeleton.bones.map(b => b.name), a = new Float32Array(ga.position.count * 2);
  G.reset(); G.root.updateMatrixWorld(true); const WR = {}; for (const S of ['R', 'L']) { const wr = wp(G.bones['hand' + S]), el = wp(G.bones['farm' + S]); WR[S] = { wr, d: wr.clone().sub(el).normalize() }; }
  const _p = V(0, 0, 0);
  for (let i = 0; i < ga.position.count; i++) { let hd = 0, arm = 0, side = null; for (let k = 0; k < 4; k++) { const w = ga.skinWeight.getComponent(i, k), n = names[ga.skinIndex.getComponent(i, k)];
      if (/^(head|neck|jaw|brow|eye|lid|lip|cheek|nose|ear)/.test(n)) hd += w; if (/^(farm|hand|index|middle|ring|pinky|thumb)/.test(n)) { arm += w; side = n.slice(-1); } }
    let gl = 0; if (arm > 0.3 && side && WR[side]) { _p.set(ga.position.getX(i), ga.position.getY(i), ga.position.getZ(i)).applyMatrix4(sk.matrixWorld);
      gl = clamp((_p.clone().sub(WR[side].wr).dot(WR[side].d) + 0.035) / 0.03, 0, 1); }   // the glove from 3.5 cm up the forearm: a straight cuff line round the wrist
    a[i * 2] = gl; a[i * 2 + 1] = hd; }   // how much glove / balaclava each vertex is: blended weights give a clean edge line (the main-bone pick made a jagged cuff)
  sk.geometry.setAttribute('aSuit', new THREE.BufferAttribute(a, 2));
  const m = sk.material, old = m.onBeforeCompile, oldKey = m.customProgramCacheKey ? m.customProgramCacheKey.bind(m) : () => '';
  m.onBeforeCompile = (sh, r) => { if (old) old.call(m, sh, r);
    sh.vertexShader = 'attribute vec2 aSuit; varying vec2 vSuit;\n' + sh.vertexShader.replace('#include <begin_vertex>', '#include <begin_vertex>\n vSuit = aSuit;');
    sh.fragmentShader = 'varying vec2 vSuit;\n' + sh.fragmentShader
      .replace('#include <map_fragment>', `#include <map_fragment>
        { float gl = smoothstep(0.45, 0.55, vSuit.x), hd = smoothstep(0.35, 0.6, vSuit.y), cuff = smoothstep(0.2, 0.3, vSuit.x) * (1.0 - smoothstep(0.42, 0.47, vSuit.x));   // linear colours: olive suit, leather glove (a dark cuff band), balaclava
          vec3 c = mix(vec3(0.107, 0.112, 0.045), vec3(0.05, 0.028, 0.014), gl); c = mix(c, vec3(0.03, 0.018, 0.01), cuff); diffuseColor.rgb = mix(c, vec3(0.018, 0.018, 0.02), hd); }`)
      .replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\n roughnessFactor = mix(mix(0.9, 0.55, smoothstep(0.42, 0.5, vSuit.x)), 0.95, smoothstep(0.42, 0.5, vSuit.y));'); };
  m.customProgramCacheKey = () => oldKey() + '|suit'; m.needsUpdate = true; }
for (const n of ['hair', 'hairCards', 'brows', 'lashes', 'eyeR', 'eyeL', 'teeth', 'tongue']) if (G.meshes[n]) G.meshes[n].visible = false;   // all under the helmet and visor
// the harness: two shoulder straps and a lap belt, riding the chest and hips bones
const strapM = new THREE.MeshStandardMaterial({ color: 0x24252a, roughness: 0.8 });   // dark webbing (olive straps vanished on the olive suit)
const STRAPS = [];
function strapBand(bone, a, b, w = 0.045) { const g = new THREE.Mesh(new THREE.BoxGeometry(w, 1, 0.012), strapM); g.castShadow = true; scene.add(g); STRAPS.push({ g, bone, a, b }); }

// ------------------------------------------------------------------ fire, smoke, water
const dotTex = canvasTex(64, 64, g => { const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.45, 'rgba(255,255,255,0.55)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); });
function pts(n, color, size, blend = THREE.AdditiveBlending, depthTest = true) { const g = new THREE.BufferGeometry(); const p = new Float32Array(n * 3); g.setAttribute('position', new THREE.BufferAttribute(p, 3)); g.setDrawRange(0, 0);
  const m = new THREE.Points(g, new THREE.PointsMaterial({ color, size, map: dotTex, transparent: true, depthWrite: false, depthTest, blending: blend, toneMapped: blend !== THREE.AdditiveBlending })); m.frustumCulled = false; m.renderOrder = 8; scene.add(m); return { m, p, n }; }
const flameM = new THREE.MeshBasicMaterial({ color: 0xffb24a, transparent: true, opacity: 0.9, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false });
const coreM = new THREE.MeshBasicMaterial({ color: 0xfff4d0, transparent: true, opacity: 1, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false });
const FLAMES = NOZ.map(p => { const g = new THREE.Group(); g.position.copy(p); sled.add(g);
  const o = new THREE.Mesh(new THREE.ConeGeometry(0.12, 1, 18, 1, true).rotateX(-Math.PI / 2).translate(0, 0, -0.5), flameM); g.add(o);
  const c = new THREE.Mesh(new THREE.ConeGeometry(0.06, 0.6, 14, 1, true).rotateX(-Math.PI / 2).translate(0, 0, -0.3), coreM); g.add(c); return g; });
const fireLight = new THREE.PointLight(0xffa040, 0, 9, 1.4); fireLight.position.set(0, 1.0, -1.9); sled.add(fireLight);
const SMOKE = pts(1400, 0xbab2a6, 0.55, THREE.NormalBlending); SMOKE.m.material.opacity = 0.55;
const SPRAY = pts(1400, 0xe8f4ff, 0.12, THREE.NormalBlending); SPRAY.m.material.opacity = 1;
const MIST = pts(470, 0xffffff, 1.5, THREE.NormalBlending); MIST.m.material.opacity = 0.45;
const DUST = pts(900, 0x8a7a64, 1.6, THREE.NormalBlending); DUST.m.material.opacity = 0.55;   // darker than the sand, or it vanishes against it   // dust thrown up off the track behind the sled
const BURST = pts(500, 0xff7a1a, 1.2, THREE.NormalBlending); BURST.m.material.toneMapped = false;   // solid fire: additive washed out against the bright sky                                                    // the ignition fireball, billowing out round the sled
const BSMOKE = pts(500, 0xc8c0b4, 1.3, THREE.NormalBlending); BSMOKE.m.material.opacity = 0.5;
// the water brake: shallow troughs between the rails, one after another
const POOLS = []; const poolWater = new THREE.MeshStandardMaterial({ color: 0x5a8aa8, roughness: 0.1, metalness: 0.1, transparent: true, opacity: 0.85 });
for (let k = 0; k < 9; k++) { const g = new THREE.Group(); scene.add(g);
  box(0.9, 0.12, 0.08, 0, 0.06, -0.9, mat(0x9a948a, 0.9), 0, g); box(0.9, 0.12, 0.08, 0, 0.06, 0.9, mat(0x9a948a, 0.9), 0, g);
  const w = new THREE.Mesh(new THREE.PlaneGeometry(0.86, 1.76).rotateX(-Math.PI / 2), poolWater); w.position.y = 0.1; g.add(w); POOLS.push(g); }

// ------------------------------------------------------------------ the eye up close (beat 7): blood vessels burst, then the dark closes in from the edges
const EY = V(600, 0, 0);
const eyeSet = new THREE.Group(); eyeSet.position.copy(EY); scene.add(eyeSet);
eyeSet.add(new THREE.Mesh(new THREE.SphereGeometry(8, 24, 12), new THREE.MeshBasicMaterial({ color: 0x120608, side: THREE.BackSide })));
const scleraTex = canvasTex(1024, 512, g => { g.fillStyle = '#f2ece4'; g.fillRect(0, 0, 1024, 512);
  for (let i = 0; i < 40; i++) { g.strokeStyle = `rgba(200,80,80,${0.12 + 0.12 * hash1(i)})`; g.lineWidth = 1 + 2 * hash1(i * 3); let x = 512 + (hash1(i * 5) - 0.5) * 900, y = hash1(i * 7) < 0.5 ? 40 : 470; g.beginPath(); g.moveTo(x, y);
    for (let k = 0; k < 10; k++) { x += (hash1(i * 11 + k) - 0.5) * 60; y += (y < 256 ? 1 : -1) * 18; g.lineTo(x, y); } g.stroke(); }
  const ix = 256, iy = 256; const gr = g.createRadialGradient(ix, iy, 10, ix, iy, 110); gr.addColorStop(0, '#0a0a0a'); gr.addColorStop(0.32, '#0a0a0a'); gr.addColorStop(0.34, '#3a6a4a'); gr.addColorStop(0.8, '#5a8a5a'); gr.addColorStop(1, '#2a3a2a');
  g.fillStyle = gr; g.beginPath(); g.ellipse(ix, iy, 110, 110, 0, 0, 7); g.fill(); });
const veinTex = canvasTex(1024, 512, g => { g.clearRect(0, 0, 1024, 512);
  for (let i = 0; i < 90; i++) { g.strokeStyle = `rgba(190,10,20,${0.5 + 0.4 * hash1(i)})`; g.lineWidth = 2 + 5 * hash1(i * 3); let x = 256 + (hash1(i * 5) - 0.5) * 900, y = hash1(i * 7) < 0.5 ? 20 : 490; g.beginPath(); g.moveTo(x, y);
    for (let k = 0; k < 14; k++) { x += (hash1(i * 13 + k) - 0.5) * 70; y += (y < 256 ? 1 : -1) * (12 + 8 * hash1(i + k)); g.lineTo(x, y); } g.stroke(); }
  for (let i = 0; i < 14; i++) { const x = 256 + (hash1(i * 17) - 0.5) * 700, y = 60 + hash1(i * 19) * 390; if (Math.hypot(x - 256, y - 256) < 130) continue; const gr = g.createRadialGradient(x, y, 0, x, y, 70); gr.addColorStop(0, 'rgba(170,0,10,0.85)'); gr.addColorStop(1, 'rgba(170,0,10,0)'); g.fillStyle = gr; g.fillRect(x - 70, y - 70, 140, 140); } });
const eyeball = new THREE.Mesh(new THREE.SphereGeometry(1, 64, 48), new THREE.MeshStandardMaterial({ map: scleraTex, roughness: 0.15 })); eyeSet.add(eyeball);
const veins = new THREE.Mesh(new THREE.SphereGeometry(1.003, 64, 48), new THREE.MeshStandardMaterial({ map: veinTex, transparent: true, opacity: 0, roughness: 0.2, depthWrite: false })); eyeball.add(veins);
const iris = new THREE.Mesh(new THREE.CircleGeometry(0.42, 48), new THREE.MeshStandardMaterial({ map: canvasTex(256, 256, g => { const gr = g.createRadialGradient(128, 128, 20, 128, 128, 128); gr.addColorStop(0, '#050505'); gr.addColorStop(0.36, '#050505'); gr.addColorStop(0.38, '#2a5a3a'); gr.addColorStop(0.8, '#4a8a5a'); gr.addColorStop(1, '#1a2a1a'); g.fillStyle = gr; g.fillRect(0, 0, 256, 256);
  for (let i = 0; i < 60; i++) { const a = i / 60 * 6.283; g.strokeStyle = 'rgba(160,200,140,0.25)'; g.beginPath(); g.moveTo(128 + Math.cos(a) * 50, 128 + Math.sin(a) * 50); g.lineTo(128 + Math.cos(a) * 124, 128 + Math.sin(a) * 124); g.stroke(); } }), roughness: 0.1 }));
iris.position.z = 1.008; eyeball.add(iris);   // in front of the sclera (at 0.985 the white sphere covered the pupil), turning with the eyeball
const eyeLight = new THREE.PointLight(0xfff0e0, 0, 10, 1.2); eyeLight.position.set(1.5, 1.6, 3); eyeSet.add(eyeLight);

// ------------------------------------------------------------------ the seat belt today (beat 8, second half): a car seat, the belt slides across, the buckle clicks in
const BT = V(-600, 0, 0);
const beltSet = new THREE.Group(); beltSet.position.copy(BT); scene.add(beltSet);
beltSet.add(new THREE.Mesh(new THREE.SphereGeometry(8, 24, 12), new THREE.MeshBasicMaterial({ color: 0x1a1c22, side: THREE.BackSide })));
const fabric = canvasTex(256, 256, g => { g.fillStyle = '#16171c'; g.fillRect(0, 0, 256, 256); for (let y = 0; y < 256; y += 4) { g.fillStyle = 'rgba(255,255,255,0.04)'; g.fillRect(0, y, 256, 1); } });
fabric.wrapS = fabric.wrapT = THREE.RepeatWrapping; fabric.repeat.set(3, 3);
{ const fm = new THREE.MeshStandardMaterial({ map: fabric, roughness: 0.95 });   // a car seat: cushioned back, bolsters, headrest on two posts, the door and window beside it
  box(0.95, 1.3, 0.22, 0, 0.55, -0.25, fm, 0.1, beltSet); for (const x of [-0.5, 0.5]) box(0.16, 1.1, 0.32, x, 0.5, -0.15, fm, 0.07, beltSet);
  box(0.55, 0.32, 0.18, 0, 1.55, -0.25, fm, 0.08, beltSet); for (const x of [-0.12, 0.12]) box(0.025, 0.2, 0.025, x, 1.3, -0.25, mat(0xb0b4ba, 0.3, 0.8), 0, beltSet);
  box(0.08, 2.4, 0.4, -0.95, 0.6, -0.1, mat(0x2a2c30, 0.6), 0.02, beltSet);
  const win = new THREE.Mesh(new THREE.PlaneGeometry(1.0, 0.8), new THREE.MeshBasicMaterial({ color: 0x9cc4e8, toneMapped: false })); win.position.set(-0.9, 1.45, -0.6); win.rotation.y = 0.5; beltSet.add(win); }
const webbing = canvasTex(64, 256, g => { g.fillStyle = '#6a6a72'; g.fillRect(0, 0, 64, 256); for (let x = 0; x < 64; x += 3) { g.fillStyle = 'rgba(0,0,0,0.18)'; g.fillRect(x, 0, 1, 256); } });
const belt = new THREE.Mesh(new THREE.BoxGeometry(0.12, 1.6, 0.01), new THREE.MeshStandardMaterial({ map: webbing, roughness: 0.8 })); beltSet.add(belt);
const tongue = new THREE.Group(); beltSet.add(tongue);
box(0.14, 0.12, 0.02, 0, 0, 0, mat(0xc8ccd2, 0.25, 0.9), 0.005, tongue); box(0.07, 0.1, 0.012, 0, -0.1, 0, mat(0xc8ccd2, 0.25, 0.9), 0.003, tongue);
const latch = new THREE.Group(); latch.position.set(0.42, -0.1, 0.02); beltSet.add(latch);
box(0.16, 0.26, 0.09, 0, 0, 0, mat(0x111216, 0.5), 0.02, latch); box(0.12, 0.07, 0.025, 0, 0.06, 0.05, new THREE.MeshStandardMaterial({ color: 0xe0281e, emissive: 0x501008, roughness: 0.4 }), 0.008, latch);
const beltLight = new THREE.PointLight(0xfff2e0, 0, 8, 1.0); beltLight.position.set(0.5, 0.8, 1.4); beltSet.add(beltLight);

// ------------------------------------------------------------------ the gauge: speed (mph) and g, stuck to the camera so it stays sharp (drawn after the film look)
scene.add(camera);
const gaugeC = document.createElement('canvas'); gaugeC.width = 512; gaugeC.height = 600;
const gaugeT = new THREE.CanvasTexture(gaugeC); gaugeT.colorSpace = THREE.SRGBColorSpace;
const gauge = new THREE.Mesh(new THREE.PlaneGeometry(0.066, 0.0773), new THREE.MeshBasicMaterial({ map: gaugeT, transparent: true, depthTest: false, depthWrite: false, toneMapped: false }));
gauge.renderOrder = 30; camera.add(gauge); gauge.position.set(0.034, 0.048, -0.2); gauge.visible = false;
let GSHOWN = '';
function drawGauge(mph, gs, label) { const key = Math.round(mph) + '|' + gs.toFixed(1) + '|' + label; if (key === GSHOWN) return; GSHOWN = key;
  const g = gaugeC.getContext('2d'); g.clearRect(0, 0, 512, 600); const cx = 256, cy = 256, R = 220, a0 = Math.PI * 0.75, a1 = Math.PI * 2.25, MAX = 700;
  g.fillStyle = 'rgba(8,10,14,0.82)'; g.beginPath(); g.arc(cx, cy, R + 22, 0, 7); g.fill();
  g.lineWidth = 26; g.strokeStyle = 'rgba(255,255,255,0.12)'; g.beginPath(); g.arc(cx, cy, R - 20, a0, a1); g.stroke();
  const am = a0 + (a1 - a0) * Math.min(1, mph / MAX); g.strokeStyle = mph > 600 ? '#ff4030' : '#ffd23a'; g.beginPath(); g.arc(cx, cy, R - 20, a0, am); g.stroke();
  g.fillStyle = '#ffffff'; g.font = 'bold 26px Arial'; g.textAlign = 'center';
  for (let v = 0; v <= MAX; v += 100) { const a = a0 + (a1 - a0) * v / MAX; g.save(); g.translate(cx + Math.cos(a) * (R - 60), cy + Math.sin(a) * (R - 60)); g.fillText(v, 0, 9); g.restore(); }
  g.strokeStyle = '#ffffff'; g.lineWidth = 8; g.beginPath(); g.moveTo(cx, cy); g.lineTo(cx + Math.cos(am) * (R - 36), cy + Math.sin(am) * (R - 36)); g.stroke();
  g.fillStyle = '#ffffff'; g.beginPath(); g.arc(cx, cy, 14, 0, 7); g.fill();
  g.font = 'bold 92px Arial'; g.lineWidth = 10; g.strokeStyle = 'rgba(0,0,0,0.8)'; g.strokeText(Math.round(mph), cx, cy + 128); g.fillText(Math.round(mph), cx, cy + 128);
  g.font = 'bold 34px Arial'; g.fillStyle = '#c8ccd4'; g.fillText('MPH', cx, cy + 168);
  g.fillStyle = 'rgba(8,10,14,0.82)'; g.beginPath(); g.roundRect(96, 506, 320, 84, 20); g.fill();
  g.font = 'bold 62px Arial'; g.fillStyle = gs >= 20 ? '#ff4030' : '#7fe0ff'; g.fillText(label || (gs.toFixed(gs < 10 ? 1 : 0) + ' G'), cx, 570);
  gaugeT.needsUpdate = true; }
// the dark that closes in from the edges (a full-frame shader plane; never a shrinking ring)
const darkM2 = new THREE.ShaderMaterial({ uniforms: { uR: { value: 2 }, uA: { value: 0 } }, transparent: true, depthTest: false, depthWrite: false,
  vertexShader: 'varying vec2 vU; void main(){ vU = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
  fragmentShader: 'uniform float uR, uA; varying vec2 vU; void main(){ vec2 p = (vU - 0.5) * vec2(1.0, 1.78); float d = length(p); float k = smoothstep(uR - 0.18, uR + 0.02, d); gl_FragColor = vec4(0.0, 0.0, 0.0, max(k, uA)); }' });
const darkPlane = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), darkM2); darkPlane.renderOrder = 25; camera.add(darkPlane); darkPlane.position.set(0, 0, -0.1); darkPlane.visible = false;
// ------------------------------------------------------------------ the run, in real seconds T from ignition (Dec 10, 1954: nine rockets, 632 mph, water brake, stopped in 1.4 s, 46.2 g peak)
const VMAX = 632, TBURN = 5.0, TB = 5.6, TSTOP = 1.4, GPEAK = 46.2, MPH = 0.44704;
const brakeS = u => u <= 0 ? 0 : u >= 1 ? 1 : u * u * u * (u * (6 * u - 15) + 10);   // smootherstep: the stop builds, peaks mid-way, eases out
function vAt(T) { if (T <= 0) return 0; if (T < TBURN) return VMAX * Math.pow(T / TBURN, 1.15);
  if (T < TB) return VMAX - 2 * (T - TBURN); const v0 = VMAX - 2 * (TB - TBURN); return v0 * (1 - brakeS((T - TB) / TSTOP)); }
// distance (m) by integrating the speed once at load
const DT_ = 0.001, DTAB = [0]; for (let i = 1; i <= 12000; i++) DTAB.push(DTAB[i - 1] + 0.5 * (vAt((i - 1) * DT_) + vAt(i * DT_)) * MPH * DT_);
const distAt = T => T <= 0 ? 0 : T >= 12 ? DTAB[12000] : (() => { const x = T / DT_, i = Math.floor(x); return DTAB[i] + (DTAB[i + 1] - DTAB[i]) * (x - i); })();
// g on his body: + = thrown forward (braking), - = pressed back (rockets). The braking curve is scaled so its peak reads the recorded 46.2 g.
const accAt = T => (vAt(T + 0.002) - vAt(T - 0.002)) / 0.004 * MPH / 9.81;
let GSCALE = 1; { let pk = 0; for (let T = TB; T < TB + TSTOP; T += 0.002) pk = Math.max(pk, -accAt(T)); GSCALE = GPEAK / pk; }
const gAt = T => { const a = accAt(T); return a < 0 ? -a * GSCALE : -Math.min(12, a * 2.0) * smooth(-0.05, 0.6, T); };   // the rocket push builds over the first half second (no pop at ignition)   // the rockets pushed about 12 g (Smithsonian caption)

// each beat's slice of the run (story time T against the beat's own clock); beats 4-6 are slow motion, 6 is a replay of the peak
const T0 = 0.12;                                                     // frame one is already 0.12 s into the ignition (the fireball is out), and the countdown in beat 9 lands on it
const SLICE = [[T0, 0.6], [0.6, 2.2], [2.2, 5.0], [5.0, 5.6], [5.6, 5.75], [5.75, 7.0], [TB + 0.6, TB + 0.82], null, [9, 9], null];
function storyT(b, lt, d) { if (b === 9) return T0 - (d - lt); const s = SLICE[b]; if (!s) return 9; return s[0] + (s[1] - s[0]) * clamp(lt / d, 0, 1); }
const SLOWMO = { 4: true, 6: true };

// ------------------------------------------------------------------ him in the seat
const YAW = 180;                                                    // he faces +z, the way the sled runs
const F = fwdOf(YAW), Rt = rightOf(YAW), UP = V(0, 1, 0);
function blinkAt(s) { const u = ((s + 40) % 3.7) / 0.16; return u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0; }
const SIT = { thighR: [86, 0, 4], thighL: [86, 0, -4], shinR: [-78, 0, 0], shinL: [-78, 0, 0], footR: [-6, 0, 0], footL: [-6, 0, 0], spine1: [2, 0, 0], spine2: [0, 0, 0], neck: [-2, 0, 0],
  armR: A(14, 16, 0, 36, 0), armL: A(14, 16, 0, 36, 0) };
const SITPOSE = addPose(curl(curl({ ...SIT }, 'R', 70), 'L', 70), { thumb1R: [-40, 0, 0], thumb1L: [-40, 0, 0] });   // hands low by his hips in fists, gripping the seat edge
let HIPY = SEATTOP + 0.1;                                           // set at load so his seat rests on the seat pan

function guyAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  const T = storyT(b, lt, d), gz = (b === 7 || b === 8 && lt > d * 0.55) ? 0 : gAt(T);
  const fwd = Math.max(0, gz) / GPEAK, back = Math.max(0, -gz) / 12;
  const face = { blink: blinkAt(lt + b * 1.3) * (1 - Math.min(1, (fwd + back) * 3)) };
  const show = b !== 7 && !(b === 8 && lt > d * 0.55);
  // thrown into the straps when braking (the torso can only go so far), pressed into the seat by the rockets
  let pose = addPose(SITPOSE, {
    spine1: [-16 * fwd + 3 * back, 0, 0], spine2: [-12 * fwd + 2 * back, 0, 0], chest: [-6 * fwd, 0, 0],   // negative x bends him forward on this rig
    neck: [-26 * fwd + 10 * back, 0, 0], head: [-14 * fwd + 6 * back, 0, 0],
    armR: [26 * fwd - 6 * back, 6 * fwd, 0, -26 * fwd + 6 * back, 0], armL: [26 * fwd - 6 * back, 6 * fwd, 0, -26 * fwd + 6 * back, 0] });
  const brace = b === 9 ? smooth(0, Math.min(1.2, d * 0.4), lt) : b === 0 ? 1 - smooth(0, 0.5, lt) : 0;   // he braces for the countdown; it carries into frame one so the loop matches
  pose = addPose(pose, { neck: [4 * brace, 0, 0], head: [-3 * brace, 0, 0] });
  if (b === 8 && show) { const k = smooth(0.4, d * 0.5, lt); pose = addPose(SITPOSE, { spine1: [-14 * (1 - k), 0, 0], neck: [-28 * (1 - k), 0, 0], head: [-10 * (1 - k), 0, 0] }); }   // slumped, then he lifts his head
  const strain = Math.min(1, fwd * 1.6 + back * 1.2);
  Object.assign(face, { pain: 0.15 * strain, press: 1.0 * back, frown: 1.0 * back, jaw: 0.45 * fwd, oh: 0.7 * fwd, browIn: 0.8 * strain, squint: 0.4 * strain + 0.9 * back + 0.25 * brace, brow: 0.4 * brace + 0.2 * strain,
    fear: Math.max(0.35 * brace, b === 0 ? 0.35 + 0.5 * smooth(0, 0.4, lt) : 0.35 * strain), blink: b === 8 && show ? Math.max(face.blink, 0.6 * (1 - smooth(0.6, d * 0.45, lt))) : face.blink });
  const root = { x: 0, y: HIPY, z: 0.035 * fwd - 0.01 * back, yaw: YAW };
  const shake = b === 7 ? 0 : Math.min(1, vAt(T) / VMAX) * 0.5 + (T > 0 && T < 0.5 ? 1 - T / 0.5 : 0) + Math.min(1, fwd * 1.5);
  return { b, lt, d, T, gz, pose, root, face, show, shake };
}

// ------------------------------------------------------------------ cameras: every beat moves (push, orbit, track, roll); whips between some beats
const CAM0 = { pos: V(1.35, 0.95, 2.7), tgt: V(-0.1, 1.15, -0.4), fov: 46 };     // low front 3/4: his face, and the ignition fireball billowing out round the sled
function camAt(t, g) {
  const b = g.b, lt = g.lt, d = g.d, k = smooth(0, d, lt), e = sm(clamp(lt / d, 0, 1));
  if (b === 0) { const kk = smooth(0, d, lt); return { pos: CAM0.pos.clone().lerp(V(0.8, 1.15, 1.9), kk), tgt: CAM0.tgt.clone().lerp(V(0, 1.25, -0.1), kk), fov: CAM0.fov, roll: -5 * kk }; }
  if (b === 9) { const kk = smooth(d - 1.6, d, lt); return { pos: V(-1.6, 1.8, 3.6).lerp(CAM0.pos, kk), tgt: V(0, 1.0, -0.4).lerp(CAM0.tgt, kk), fov: lerp(44, CAM0.fov, kk), roll: 0 }; }   // lands exactly on frame one's camera
  if (b === 1) return { pos: V(0.12, 1.55, 1.0 - 0.15 * e), tgt: V(0, 1.3, -0.4), fov: 50, roll: 8 };                      // onboard, on the windscreen frame, looking back at him
  if (b === 2) { const a = lerp(-20, 55, e) * D2R; return { pos: V(Math.sin(a) * 3.2 + 0.2, 0.45, Math.cos(a) * 3.2), tgt: V(0, 0.95, -0.2), fov: 42, roll: -6 }; }   // swing round low beside the rails
  if (b === 3) return { pos: V(3.6 - 1 * e, 3.2 - 0.6 * e, 4.6 - 1.4 * e), tgt: V(0, 0.9, -1.8), fov: 44, roll: 0 };              // drone: high, ahead, looking back at the sled and its smoke
  if (b === 4) return { pos: V(0.85, 0.4, 3.2 - 0.4 * e), tgt: V(0.3, 0.45, 0.9), fov: 46, roll: 3 };   // ahead of the sled, low: the scoop bites the water, he's above it                         // at the rails, ahead of the scoop
  if (b === 5) return { pos: V(0.45, 1.8, 1.7), tgt: V(0, 1.05, 0.05), fov: 48, roll: -6 };                              // onboard again: he's thrown at the camera
  if (b === 6) { const a = lerp(20, 95, e) * D2R; return { pos: V(Math.sin(a) * 2.4, 1.3, Math.cos(a) * 2.4), tgt: V(0, 1.1, 0.05), fov: 40, roll: 0 }; }       // bullet-time orbit at the peak
  if (b === 7) return { pos: EY.clone().add(V(0.05, 0.05, 3.9 - 0.9 * e)), tgt: EY.clone(), fov: 40, roll: 0 };
  if (b === 8) { if (lt < d * 0.55) return { pos: V(1.6 - 0.3 * e, 1.6, 2.4 - 0.3 * e), tgt: V(0, 1.1, 0), fov: 42, roll: 0 };
    return { pos: BT.clone().add(V(0.35, 0.75, 3.0 - 0.6 * e)), tgt: BT.clone().add(V(0.05, 0.45, 0)), fov: 44, roll: 0 }; }
  return CAM0;
}
// whip pans: the last 0.12 s of a beat swings away, the first 0.12 s of the next swings in (with a directional blur)
const WHIPS = { 2: 1, 3: -1, 5: 1, 6: -1 };                          // beat -> direction of the whip out of it
function whipAt(t) { const b = beatAt(t), lt = t - B[b], d = DUR[b], W_ = 0.12;
  if (WHIPS[b] && lt > d - W_) return WHIPS[b] * sm((lt - (d - W_)) / W_);
  if (WHIPS[b - 1] && lt < W_) return -WHIPS[b - 1] * (1 - sm(lt / W_));
  return 0; }
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
