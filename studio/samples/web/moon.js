// "You just watched the Moon vanish. Here's what happens next." - a 3D Short on the MakeHuman man.
//   moon_mh.html?w=1080&h=1920            (times from moon/times.json; one shot per narration line)
// Beats: 0 the dock at night, the moon blinks out (hook) | 1 space: its last light still on the way (1.3 s) | 2 the tide sinks down the pilings
//        3 space: the Sun still pulls a smaller tide | 4 the dark dock, 125x darker | 5 hatchling turtles crawl the wrong way | 6 the reef: corals wait
//        7 space: the tilt swings to 85 degrees | 8 the tipped Earth: one side hardly sees the Sun | 9 back on the dock; the moon comes back (loops)
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { loadGuy } from '/guy3d.js';

const Q = new URLSearchParams(location.search);
const W = +Q.get('w') || 720, H = +Q.get('h') || 1280;
const FPS = 30;
const TIMES = await (await fetch('/moon/times.json')).json();
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
const G = await loadGuy(THREE, '/char/' + (Q.get('char') || window.CHARDEF || 'guy'), {});      // ?char=mh or window.CHARDEF: the MakeHuman man
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
// ================================================================== THE MOON VANISHES
// ------------------------------------------------------------------ the night dock (the room is hidden); sky, stars and the moon ride with the camera
home.visible = false;
const STANDP = V(0, 0, -1.5);                                      // where he stands on the dock, facing +z (the shore, the camera); the sea and the moon behind him
const MD = V(-0.1, 0.5, -1).normalize();                            // the moon's direction (behind him, about 26 deg up)
const SKY = new THREE.Group(); scene.add(SKY);                      // moves with the camera, so the sky and the moon have no parallax
{ const g = new THREE.SphereGeometry(140, 32, 20), c = new Float32Array(g.attributes.position.count * 3), lo = new THREE.Color(0x1c2c4c), hi = new THREE.Color(0x03060f);
  for (let i = 0; i < g.attributes.position.count; i++) { const y = g.attributes.position.getY(i) / 140, k = Math.pow(clamp(y * 2.2, 0, 1), 0.6), col = lo.clone().lerp(hi, k); c.set([col.r, col.g, col.b], i * 3); }
  g.setAttribute('color', new THREE.BufferAttribute(c, 3));
  SKY.add(new THREE.Mesh(g, new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.BackSide, depthWrite: false, fog: false }))); }
const skyMat = SKY.children[0].material;
const STARS = (() => { const n = 1600, p = new Float32Array(n * 3), s = new Float32Array(n);
  for (let i = 0; i < n; i++) { const u = hash1(i * 1.7) * 2 - 1, a = hash1(i * 3.1 + 2) * Math.PI * 2, r = Math.sqrt(1 - u * u); p.set([Math.cos(a) * r * 130, u * 130, Math.sin(a) * r * 130], i * 3); s[i] = 0.4 + 1.6 * Math.pow(hash1(i * 5.3 + 1), 6); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(p, 3)); g.setAttribute('sz', new THREE.BufferAttribute(s, 1));
  const m = new THREE.ShaderMaterial({ uniforms: { uK: { value: 1 }, uT: { value: 0 }, uH: { value: H } }, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    vertexShader: 'attribute float sz; uniform float uT, uH; varying float vA; void main(){ vec4 mv = modelViewMatrix * vec4(position,1.0); gl_Position = projectionMatrix * mv;' +
      ' float tw = 0.75 + 0.25 * sin(uT + position.x * 1.3 + position.z); vA = tw * min(1.0, sz); gl_PointSize = max(1.5, sz * uH / 900.0 * 2.2); }',
    fragmentShader: 'uniform float uK; varying float vA; void main(){ float d = length(gl_PointCoord - 0.5); if (d > 0.5) discard; gl_FragColor = vec4(vec3(0.85,0.9,1.0), vA * uK * smoothstep(0.5, 0.1, d)); }' });
  const o = new THREE.Points(g, m); o.frustumCulled = false; o.renderOrder = -1; SKY.add(o); return m; })();
const moonTex = canvasTex(512, 512, g => { g.fillStyle = '#d8d6cc'; g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 9; i++) { g.fillStyle = 'rgba(120,118,112,0.35)'; g.beginPath(); g.ellipse(80 + hash1(i * 4.1) * 360, 80 + hash1(i * 2.7) * 360, 40 + hash1(i * 9.2) * 70, 30 + hash1(i * 6.6) * 50, hash1(i) * 3, 0, 7); g.fill(); }
  for (let i = 0; i < 140; i++) { const x = hash1(i * 7.7) * 512, y = hash1(i * 3.3 + 9) * 512, r = 2 + 18 * Math.pow(hash1(i * 1.9), 3);
    g.fillStyle = 'rgba(90,88,84,0.35)'; g.beginPath(); g.arc(x, y, r, 0, 7); g.fill(); g.strokeStyle = 'rgba(250,250,245,0.45)'; g.lineWidth = Math.max(1, r * 0.25); g.beginPath(); g.arc(x - r * 0.15, y - r * 0.15, r, 3.4, 5.6); g.stroke(); } });
const skyMoon = new THREE.Mesh(new THREE.SphereGeometry(5.4, 48, 32), new THREE.MeshBasicMaterial({ map: moonTex, transparent: true, fog: false, toneMapped: false }));
skyMoon.position.copy(MD).multiplyScalar(100); skyMoon.lookAt(0, 0, 0); SKY.add(skyMoon);
const glowTex = canvasTex(256, 256, g => { const gr = g.createRadialGradient(128, 128, 0, 128, 128, 128); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.25, 'rgba(255,255,255,0.35)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 256, 256); });
const moonGlow = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, color: 0xb8c8ff, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, fog: false, toneMapped: false }));
moonGlow.scale.setScalar(34); moonGlow.position.copy(MD).multiplyScalar(101); SKY.add(moonGlow);
const moonLight = new THREE.DirectionalLight(0xaabfff, 0); moonLight.position.copy(MD).multiplyScalar(20); scene.add(moonLight); scene.add(moonLight.target);
moonLight.castShadow = true; moonLight.shadow.mapSize.set(2048, 2048); { const S = moonLight.shadow.camera; S.left = -4; S.right = 4; S.top = 4; S.bottom = -4; S.near = 1; S.far = 40; moonLight.shadow.bias = -0.0004; moonLight.shadow.normalBias = 0.02; }

// the sea: one big plane with rolling waves (periods divide the video length, so the loop has no seam)
const WAVES = [[3, 0.035, V(0.8, 0, 0.6)], [5, 0.022, V(-0.4, 0, 1)], [8, 0.012, V(0.95, 0, -0.3)]].map(([k, a, d]) => ({ w: 2 * Math.PI * k / TOTAL * 4, a, d: d.normalize(), kx: 0.9 + 0.6 * k / 8 }));
function seaMat(color) { const m = new THREE.MeshStandardMaterial({ color, roughness: 0.18, metalness: 0.0 });
  m.userData.uT = { value: 0 };
  m.onBeforeCompile = sh => { sh.uniforms.uT = m.userData.uT;
    const W_ = WAVES.map(w => `vec4(${w.d.x.toFixed(3)}, ${w.d.z.toFixed(3)}, ${w.kx.toFixed(3)}, ${w.a.toFixed(3)})`), WS = WAVES.map(w => w.w.toFixed(5));
    sh.vertexShader = 'uniform float uT;\n' + sh.vertexShader.replace('#include <beginnormal_vertex>', `vec3 objectNormal = vec3(0.0, 0.0, 1.0); float hgt = 0.0; vec2 dh = vec2(0.0);
      { vec4 W[3]; W[0] = ${W_[0]}; W[1] = ${W_[1]}; W[2] = ${W_[2]}; float S[3]; S[0] = ${WS[0]}; S[1] = ${WS[1]}; S[2] = ${WS[2]};
        for (int i = 0; i < 3; i++) { float ph = dot(W[i].xy, vec2(position.x, -position.y)) * W[i].z - uT * S[i]; hgt += W[i].w * sin(ph); dh += W[i].w * W[i].z * cos(ph) * W[i].xy; } }
      objectNormal = normalize(vec3(-dh.x, dh.y, 1.0));`).replace('#include <begin_vertex>', 'vec3 transformed = vec3(position.x, position.y, position.z + hgt);'); };
  return m; }
const sea = new THREE.Mesh(new THREE.PlaneGeometry(400, 400, 220, 220).rotateX(0), seaMat(0x0e2238)); sea.material.roughness = 0.32; sea.rotation.x = -Math.PI / 2; sea.receiveShadow = true; scene.add(sea);
const glit = new THREE.Mesh(new THREE.PlaneGeometry(3.2, 60), new THREE.MeshBasicMaterial({ map: canvasTex(64, 512, g => { g.fillStyle = '#000'; g.fillRect(0, 0, 64, 512);
  for (let i = 0; i < 260; i++) { const y = hash1(i * 2.3) * 512, x = 32 + (hash1(i * 5.1) - 0.5) * 50 * (0.3 + y / 512); g.fillStyle = `rgba(230,236,255,${0.3 + 0.6 * hash1(i)})`; g.fillRect(x - 6, y, 4 + 10 * hash1(i * 3.7), 2); } }),
  transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false }));
glit.rotation.x = -Math.PI / 2; glit.renderOrder = 2; scene.add(glit);

// the dock: planks on pilings; a post with a rod holder at the sea end; a lantern
const wood = canvasTex(512, 128, g => { g.fillStyle = '#6a5038'; g.fillRect(0, 0, 512, 128); for (let i = 0; i < 70; i++) { g.strokeStyle = `rgba(${40 + 30 * hash1(i)},${28 + 20 * hash1(i * 2)},18,${0.25 + 0.3 * hash1(i * 3)})`; g.lineWidth = 1 + 2 * hash1(i * 5); const y = hash1(i * 7.3) * 128; g.beginPath(); g.moveTo(0, y); g.bezierCurveTo(170, y + 5 * (hash1(i * 9) - 0.5), 340, y - 4, 512, y + 3); g.stroke(); } });
wood.wrapS = wood.wrapT = THREE.RepeatWrapping;
const plankM = new THREE.MeshStandardMaterial({ map: wood, roughness: 0.85 }), postM = new THREE.MeshStandardMaterial({ color: 0x4a3626, roughness: 0.9 });
const dock = new THREE.Group(); scene.add(dock);
for (let z = -2.55; z < 4.5; z += 0.21) { const p = box(2.3, 0.05, 0.19, 0, -0.025, z, plankM, 0.008, dock); p.rotation.y = (hash1(z * 9) - 0.5) * 0.012; p.position.y -= 0.004 * hash1(z * 5); }
for (const x of [-1.05, 1.05]) box(0.12, 0.16, 7.1, x, -0.13, 0.95, postM, 0, dock);
// the pilings: wood with a wet band and barnacles below the high-tide line
const pileTex = canvasTex(128, 512, g => { const gr = g.createLinearGradient(0, 0, 0, 512); gr.addColorStop(0, '#5a4430'); gr.addColorStop(0.17, '#4a3a2a'); gr.addColorStop(0.2, '#1e2a22'); gr.addColorStop(1, '#14201a'); g.fillStyle = gr; g.fillRect(0, 0, 128, 512);
  for (let i = 0; i < 160; i++) { const y = 108 + hash1(i * 3.3) * 400, x = hash1(i * 7.1) * 128; g.fillStyle = `rgba(${200 + 40 * hash1(i)},${200 + 30 * hash1(i * 2)},190,0.8)`; g.beginPath(); g.arc(x, y, 2 + 4 * hash1(i * 5.5), 0, 7); g.fill(); }
  for (let i = 0; i < 40; i++) { g.strokeStyle = 'rgba(30,20,12,0.4)'; const x = hash1(i * 4.4) * 128; g.beginPath(); g.moveTo(x, 0); g.lineTo(x + 3, 512); g.stroke(); } });
const pileM = new THREE.MeshStandardMaterial({ map: pileTex, roughness: 0.9 });
const PILES = [];
const FOAM = [];   // a ring of foam where the sea meets each piling: shows the tide sinking at a glance
const foamM = new THREE.MeshBasicMaterial({ color: 0xcfe0f0, transparent: true, opacity: 0.7, depthWrite: false });
for (const z of [-2.45, -0.75, 0.95, 2.65]) for (const x of [-1.12, 1.12]) { const p = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.12, 3.2, 18), pileM); p.position.set(x, -1.5, z); p.castShadow = p.receiveShadow = true; dock.add(p); PILES.push(p);
  const f = new THREE.Mesh(new THREE.RingGeometry(0.12, 0.2, 28).rotateX(-Math.PI / 2), foamM); f.position.set(x, 0, z); dock.add(f); FOAM.push(f); }
const post = new THREE.Mesh(new THREE.CylinderGeometry(0.075, 0.08, 1.05, 14), postM); post.position.set(1.12, 0.5, -2.45); post.castShadow = true; dock.add(post);
const holder = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.3, 12), mat(0x22262c, 0.4, 0.6)); dock.add(holder);
const ROD0 = V(1.17, 0.72, -2.52), RODTIP = V(1.75, 2.55, -4.1);
holder.position.copy(ROD0).add(RODTIP.clone().sub(ROD0).normalize().multiplyScalar(0.05)); holder.quaternion.setFromUnitVectors(V(0, 1, 0), RODTIP.clone().sub(ROD0).normalize());
const rod = new THREE.Group(); dock.add(rod); rod.position.copy(ROD0);
const RODLEN = RODTIP.distanceTo(ROD0);
{ const m = new THREE.Mesh(new THREE.CylinderGeometry(0.006, 0.016, RODLEN, 10), mat(0x1a1c22, 0.35, 0.3)); m.position.y = RODLEN / 2; rod.add(m);
  const grip = new THREE.Mesh(new THREE.CylinderGeometry(0.022, 0.022, 0.32, 12), mat(0x2a2018, 0.9)); grip.position.y = 0.16; rod.add(grip);
  const reel = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.05, 16).rotateZ(Math.PI / 2), mat(0x8a8e96, 0.3, 0.8)); reel.position.set(0, 0.42, 0.04); rod.add(reel); }
rod.quaternion.setFromUnitVectors(V(0, 1, 0), RODTIP.clone().sub(ROD0).normalize());
const lineG = new THREE.BufferGeometry().setFromPoints([V(0, 0, 0), V(0, 0, 0)]);
const fishLine = new THREE.Line(lineG, new THREE.LineBasicMaterial({ color: 0xc8d0d8, transparent: true, opacity: 0.6 })); fishLine.frustumCulled = false; scene.add(fishLine);
const bobber = new THREE.Group(); scene.add(bobber);
{ const t = new THREE.Mesh(new THREE.SphereGeometry(0.045, 16, 10, 0, 7, 0, Math.PI / 2), mat(0xd02a22, 0.4)); bobber.add(t); const b = new THREE.Mesh(new THREE.SphereGeometry(0.045, 16, 10, 0, 7, Math.PI / 2, Math.PI / 2), mat(0xf2f2ee, 0.4)); bobber.add(b); }
const BOB = V(2.6, 0, -6.4);
const lantern = new THREE.Group(); lantern.position.set(-0.75, 0, -2.2); dock.add(lantern);
const lanternGlass = new THREE.MeshStandardMaterial({ color: 0xffe0a0, emissive: 0xffb050, emissiveIntensity: 2.2, roughness: 0.3, transparent: true, opacity: 0.9 });
{ box(0.16, 0.03, 0.16, 0, 0.015, 0, mat(0x2a2a2e, 0.4, 0.7), 0.005, lantern); box(0.13, 0.18, 0.13, 0, 0.12, 0, lanternGlass, 0.01, lantern); box(0.16, 0.03, 0.16, 0, 0.225, 0, mat(0x2a2a2e, 0.4, 0.7), 0.005, lantern);
  const hd = new THREE.Mesh(new THREE.TorusGeometry(0.05, 0.006, 6, 16, Math.PI), mat(0x2a2a2e, 0.4, 0.7)); hd.position.y = 0.24; lantern.add(hd); }
const lanternLight = new THREE.PointLight(0xffb868, 2.4, 6, 1.6); lanternLight.position.set(-0.75, 0.3, -2.2); scene.add(lanternLight);
// the shore behind the camera: a dark tree line far off, a few house lights (only seen in wide shots)
const shore = new THREE.Group(); scene.add(shore);
{ const tm = new THREE.MeshStandardMaterial({ color: 0x0a120e, roughness: 1 }); for (let i = 0; i < 40; i++) { const x = -60 + i * 3 + 2 * hash1(i), h = 4 + 5 * hash1(i * 3.1); const c = new THREE.Mesh(new THREE.ConeGeometry(1.8, h, 7), tm); c.position.set(x, h / 2 - 0.5, 40 + 6 * hash1(i * 7)); shore.add(c); } }

// ------------------------------------------------------------------ space stage (beats 1, 3, 7, 8): Earth, the Moon, the Sun, light on its way
const SP = V(600, 0, 0);
const space = new THREE.Group(); space.position.copy(SP); scene.add(space);
function nz2(x, y) { let v = 0, a = 0.5, f = 1; for (let o = 0; o < 5; o++) { v += a * (vn1(x * f + 10 * o, 3 + o) * 0.5 + vn1(y * f + 7 * o, 11 + o) * 0.5); a *= 0.5; f *= 2.1; } return v; }
const earthTex = canvasTex(1024, 512, g => { const im = g.createImageData(1024, 512);
  for (let y = 0; y < 512; y++) for (let x = 0; x < 1024; x++) { const lon = x / 1024 * 6.283, lat = (y / 512 - 0.5) * Math.PI;
    const px = Math.cos(lat) * Math.cos(lon) * 2.2, py = Math.cos(lat) * Math.sin(lon) * 2.2, pz = Math.sin(lat) * 2.2;
    const n = vn1(px * 1.1 + 3, 1) * 0.35 + vn1(py * 1.3 + pz, 2) * 0.35 + vn1(pz * 1.7 + px * 0.6, 4) * 0.3 + 0.18 * vn1(px * 4 + py * 3, 7);
    const land = n > 0.12, ice = Math.abs(lat) > 1.22 + 0.06 * vn1(lon * 3, 9), i = (y * 1024 + x) * 4;
    let c = land ? [60 + 50 * n, 135 + 40 * n, 60] : [22, 80 + 30 * (n + 0.5), 175 + 30 * (n + 0.5)];
    if (land && n > 0.32) c = [190, 165, 110]; if (ice) c = [235, 240, 245];
    im.data[i] = c[0]; im.data[i + 1] = c[1]; im.data[i + 2] = c[2]; im.data[i + 3] = 255; }
  g.putImageData(im, 0, 0); });
const earth = new THREE.Group(); space.add(earth);
const earthBall = new THREE.Mesh(new THREE.SphereGeometry(1, 96, 64), new THREE.MeshStandardMaterial({ map: earthTex, roughness: 0.75 })); earth.add(earthBall);
const atmo = new THREE.Mesh(new THREE.SphereGeometry(1.035, 64, 48), new THREE.MeshBasicMaterial({ color: 0x5aa0ff, transparent: true, opacity: 0.16, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.BackSide }));
earth.add(atmo);
const axisM = new THREE.MeshBasicMaterial({ color: 0xffe14a, toneMapped: false });
const axis = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.018, 3.4, 8), axisM); earth.add(axis);
const upRef = new THREE.Mesh(new THREE.CylinderGeometry(0.008, 0.008, 3.0, 8), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.45, toneMapped: false })); space.add(upRef);
const tiltTag = new THREE.Sprite(new THREE.SpriteMaterial({ map: (() => { const c = document.createElement('canvas'); c.width = 512; c.height = 256; const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.userData.c = c; return t; })(), depthTest: false, transparent: true, toneMapped: false }));
tiltTag.scale.set(1.0, 0.5, 1); tiltTag.renderOrder = 12; tiltTag.material.color.setScalar(2.4); space.add(tiltTag); let tiltShown = -1;   // color over 1: the output pass tone-maps everything, so a plain sprite came out dim
function drawTilt(d) { if (d === tiltShown) return; tiltShown = d; const c = tiltTag.material.map.userData.c, g = c.getContext('2d'); g.clearRect(0, 0, 512, 256);
  g.font = 'bold 170px Arial'; g.textAlign = 'center'; g.lineWidth = 18; g.strokeStyle = 'rgba(0,0,0,0.85)'; g.strokeText(d + '°', 256, 190); g.fillStyle = '#ffe14a'; g.fillText(d + '°', 256, 190); tiltTag.material.map.needsUpdate = true; }
const tideM = new THREE.MeshStandardMaterial({ color: 0x5ab4ff, emissive: 0x1a6ad0, emissiveIntensity: 0.9, transparent: true, opacity: 0.5, roughness: 0.2, depthWrite: false });
const tide = new THREE.Mesh(new THREE.SphereGeometry(1, 64, 48), tideM); space.add(tide);
const smoon = new THREE.Mesh(new THREE.SphereGeometry(0.27, 48, 32), new THREE.MeshStandardMaterial({ map: moonTex, roughness: 0.95 })); space.add(smoon);
const SMOON = V(0.35, 2.85, -0.8); smoon.position.copy(SMOON);
const popRing = new THREE.Mesh(new THREE.RingGeometry(0.3, 0.36, 48), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false, side: THREE.DoubleSide }));
space.add(popRing); popRing.position.copy(SMOON);
const sunBall = new THREE.Mesh(new THREE.SphereGeometry(3.5, 48, 32), new THREE.MeshBasicMaterial({ color: 0xfff2c0, toneMapped: false })); space.add(sunBall);
const sunGlow = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, color: 0xffc860, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false })); space.add(sunGlow);
const SUNPOS = V(-16, 5, 6); sunBall.position.copy(SUNPOS); sunGlow.position.copy(SUNPOS); sunGlow.scale.setScalar(34);
const sunEdge = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, color: 0xffc050, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false })); sunEdge.scale.setScalar(3.2); sunEdge.position.set(-2.1, 0.3, 0); space.add(sunEdge);
const spaceSun = new THREE.DirectionalLight(0xfff0d8, 0); spaceSun.position.copy(SP).add(SUNPOS); spaceSun.target.position.copy(SP); scene.add(spaceSun); scene.add(spaceSun.target);
const earthShine = new THREE.PointLight(0xc8d8ff, 0, 8, 1.2); space.add(earthShine);
// light on its way from the Moon to Earth: a packet of glowing dots along the line
const dotTex = canvasTex(64, 64, g => { const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.4, 'rgba(255,255,255,0.6)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); });
function dots(n, color, size, depthTest = false) { const g = new THREE.BufferGeometry(); const p = new Float32Array(n * 3); g.setAttribute('position', new THREE.BufferAttribute(p, 3)); g.setDrawRange(0, 0);
  const m = new THREE.Points(g, new THREE.PointsMaterial({ color, size, map: dotTex, transparent: true, depthWrite: false, depthTest, blending: THREE.AdditiveBlending, toneMapped: false })); m.frustumCulled = false; m.renderOrder = 9; scene.add(m); return { m, p, n }; }
const PHOT = dots(160, 0xfff4d0, 0.09, true);
const PULL = dots(240, 0xffd070, 0.06, true);                         // the Sun's pull on the sea (beat 3)

// ------------------------------------------------------------------ the beach (beat 5): a nest in the sand, hatchlings crawling toward a street light, the sea behind
const BE = V(0, 0, 600);
const beach = new THREE.Group(); beach.position.copy(BE); scene.add(beach);
const sandTex = canvasTex(512, 512, g => { g.fillStyle = '#8a7a5c'; g.fillRect(0, 0, 512, 512); for (let i = 0; i < 9000; i++) { const v = 100 + 60 * hash1(i * 1.3); g.fillStyle = `rgba(${v + 30},${v + 15},${v - 20},0.5)`; g.fillRect(hash1(i * 7.9) * 512, hash1(i * 3.1) * 512, 2, 2); } });
sandTex.wrapS = sandTex.wrapT = THREE.RepeatWrapping; sandTex.repeat.set(30, 30);
{ const sg = new THREE.PlaneGeometry(120, 120, 120, 120).rotateX(-Math.PI / 2); const P = sg.attributes.position;
  for (let i = 0; i < P.count; i++) { const x = P.getX(i), z = P.getZ(i); const fl = smooth(3, 6, Math.hypot(x, (z - 2) * 0.6)); P.setY(i, (z < -4 ? (z + 4) * 0.06 : 0) + fl * (0.04 * vn1(x * 1.3 + z * 0.7, 5) + 0.03 * vn1(x * 3.1, 8))); } sg.computeVertexNormals();
  const s = new THREE.Mesh(sg, new THREE.MeshStandardMaterial({ map: sandTex, color: 0x9a907c, roughness: 0.95 })); s.receiveShadow = true; beach.add(s); }
const beachSea = new THREE.Mesh(new THREE.PlaneGeometry(200, 100, 120, 60), seaMat(0x0c1c2c)); beachSea.rotation.x = -Math.PI / 2; beachSea.position.set(0, -0.32, -58); beach.add(beachSea);
const nest = new THREE.Mesh(new THREE.TorusGeometry(0.1, 0.03, 10, 24).rotateX(Math.PI / 2), new THREE.MeshStandardMaterial({ map: sandTex, roughness: 1 })); nest.position.set(0, 0.012, -1.0); beach.add(nest);
const hole = new THREE.Mesh(new THREE.CircleGeometry(0.1, 24).rotateX(-Math.PI / 2), mat(0x2a2016, 1)); hole.position.set(0, 0.006, -1.0); beach.add(hole);
const lampPole = new THREE.Group(); lampPole.position.set(1.8, 0, 9); beach.add(lampPole);
{ box(0.12, 2.8, 0.12, 0, 1.4, 0, mat(0x2a2c30, 0.5, 0.6), 0, lampPole); box(0.9, 0.08, 0.12, -0.42, 2.75, 0, mat(0x2a2c30, 0.5, 0.6), 0, lampPole);
  const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.13, 16, 10), new THREE.MeshBasicMaterial({ color: 0xfff0c8, toneMapped: false })); bulb.position.set(-0.8, 2.65, 0); lampPole.add(bulb);
  const gl_ = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, color: 0xffa040, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false })); gl_.scale.setScalar(1.3); gl_.position.copy(bulb.position); lampPole.add(gl_); }
const streetLight = new THREE.PointLight(0xffa850, 0, 40, 1.0); streetLight.position.set(1.0, 2.6, 609); scene.add(streetLight);
const scuteTex = canvasTex(256, 256, g => { g.fillStyle = '#3a3428'; g.fillRect(0, 0, 256, 256); g.strokeStyle = '#1a1712'; g.lineWidth = 6;
  for (let r = 0; r < 4; r++) for (let c = 0; c < 4; c++) { const x = 32 + c * 64 + (r % 2) * 32, y = 32 + r * 64; g.beginPath(); for (let k = 0; k < 6; k++) { const a = k / 6 * 6.283; g.lineTo(x + 34 * Math.cos(a), y + 34 * Math.sin(a)); } g.closePath(); g.stroke(); } });
const turtleM = new THREE.MeshStandardMaterial({ color: 0x2c2a26, roughness: 0.55 }), shellM = new THREE.MeshStandardMaterial({ map: scuteTex, roughness: 0.85 }), edgeM = new THREE.MeshStandardMaterial({ color: 0x3a3630, roughness: 0.7 });
const TURT = [];
for (let i = 0; i < 14; i++) { const t = new THREE.Group(); beach.add(t); t.scale.setScalar(1.6);
  const sh = new THREE.Mesh(new THREE.SphereGeometry(0.03, 24, 16), shellM); sh.scale.set(1, 0.38, 1.3); sh.position.y = 0.014; sh.castShadow = true; t.add(sh);
  const rim = new THREE.Mesh(new THREE.TorusGeometry(0.03, 0.0035, 6, 28).rotateX(Math.PI / 2), edgeM); rim.scale.set(1, 1, 1.3); rim.position.y = 0.012; t.add(rim);
  const hd = new THREE.Mesh(new THREE.SphereGeometry(0.0115, 14, 10), turtleM); hd.scale.set(1, 0.85, 1.25); hd.position.set(0, 0.016, 0.046); t.add(hd);
  for (const s of [-1, 1]) { const e = new THREE.Mesh(new THREE.SphereGeometry(0.0028, 8, 6), new THREE.MeshBasicMaterial({ color: 0x050505 })); e.position.set(s * 0.0075, 0.02, 0.052); t.add(e); }
  const fl = []; for (const [x, z, s, front] of [[0.026, 0.024, 1, true], [-0.026, 0.024, -1, true], [0.02, -0.03, 1, false], [-0.02, -0.03, -1, false]]) { const p = new THREE.Group(); p.position.set(x, 0.01, z); t.add(p);
    const f = new THREE.Mesh(new THREE.SphereGeometry(1, 12, 8), turtleM); f.scale.set(front ? 0.03 : 0.013, 0.003, front ? 0.011 : 0.008); f.position.set(s * (front ? 0.026 : 0.01), 0, front ? -0.008 : -0.004); f.rotation.y = s * (front ? 0.35 : 0.5); p.add(f);
    const ed = new THREE.Mesh(new THREE.SphereGeometry(1, 10, 6), edgeM); ed.scale.copy(f.scale).multiply(V(1.03, 0.6, 1.03)); ed.position.copy(f.position).add(V(0, -0.0012, 0)); ed.rotation.copy(f.rotation); p.add(ed); fl.push([p, s, front]); }
  const ang = (hash1(i * 4.2) - 0.5) * 1.3, r0 = 0.03 + 0.08 * hash1(i * 2.2);
  TURT.push({ g: t, fl, ang, start: V(Math.sin(ang * 2) * r0, 0.0, -1.0 + Math.cos(ang * 2) * r0), delay: 0.09 * i + 0.1 * hash1(i), sp: 0.22 + 0.08 * hash1(i * 6.1), ph: hash1(i * 9) * 6 }); }

// ------------------------------------------------------------------ the reef at night (beat 6): branching coral holding egg bundles that never let go
const RF = V(-600, 0, 0);
const reef = new THREE.Group(); reef.position.copy(RF); scene.add(reef);
{ const fl = new THREE.Mesh(new THREE.PlaneGeometry(60, 60, 60, 60).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ map: sandTex, color: 0x6a7a8a, roughness: 1 })); reef.add(fl);
  const P = fl.geometry.attributes.position; for (let i = 0; i < P.count; i++) P.setY(i, 0.15 * vn1(P.getX(i) * 0.5, 2) + 0.1 * vn1(P.getZ(i) * 0.7, 6)); fl.geometry.computeVertexNormals(); }
const EGGS = [];
const coralCols = [0xd8705a, 0xc85a8a, 0xe0a050, 0x9a6ad0, 0xd06070];
function branch(parent, p, dir, len, r, depth, col, seed) {
  const end = p.clone().addScaledVector(dir, len), m = new THREE.Mesh(new THREE.CylinderGeometry(r * 0.75, r, len, 8), new THREE.MeshStandardMaterial({ color: col, roughness: 0.7, emissive: col, emissiveIntensity: 0.05 }));
  m.position.copy(p).lerp(end, 0.5); m.quaternion.setFromUnitVectors(V(0, 1, 0), dir); parent.add(m);
  if (depth === 0) { const e = new THREE.Mesh(new THREE.SphereGeometry(r * 1.7, 10, 8), new THREE.MeshStandardMaterial({ color: 0xffc0d0, emissive: 0xff7aa0, emissiveIntensity: 0.6, roughness: 0.4 })); e.position.copy(end); parent.add(e); EGGS.push({ e, ph: hash1(seed) * 6.28 }); return; }
  for (let k = 0; k < 2 + (hash1(seed) > 0.6 ? 1 : 0); k++) { const s2 = seed * 3.7 + k * 1.9, nd = dir.clone().add(V(hash1(s2) - 0.5, 0.1, hash1(s2 + 1) - 0.5).multiplyScalar(1.9)).normalize();
    branch(parent, end, nd, len * 0.9, r * 0.74, depth - 1, col, s2); } }
for (let i = 0; i < 46; i++) { const a = hash1(i * 3.3) * 6.28, d = 0.25 + 2.4 * Math.sqrt(hash1(i * 5.7)), x = Math.cos(a) * d, z = Math.min(0.5, Math.sin(a) * d - 0.9);
  branch(reef, V(x, 0.05, z), V((hash1(i * 2.9) - 0.5) * 0.4, 1, (hash1(i * 4.9) - 0.5) * 0.4).normalize(), 0.1 + 0.08 * hash1(i), 0.032 + 0.014 * hash1(i * 8.8), 3, coralCols[i % coralCols.length], i + 1); }
branch(reef, V(0.12, 0.05, 0.55), V(0, 1, 0), 0.12, 0.035, 3, 0xe07060, 99);   // the hero coral, nearest the camera
for (let i = 0; i < 30; i++) { const b = new THREE.Mesh(new THREE.SphereGeometry(0.22 + 0.15 * hash1(i * 2.2), 24, 16), new THREE.MeshStandardMaterial({ color: 0x9a8a5a, roughness: 0.9 })); b.scale.y = 0.6;
  const a = hash1(i * 8.1) * 6.28, d = 1 + 3 * hash1(i * 1.1); b.position.set(Math.cos(a) * d, 0.08, Math.sin(a) * d - 1); reef.add(b); }
const reefLight = new THREE.PointLight(0x7ab0ff, 0, 14, 1.0); reefLight.position.set(-599.2, 2.6, 2.4); scene.add(reefLight);
const surf = new THREE.Mesh(new THREE.PlaneGeometry(80, 80, 120, 120), seaMat(0x1a3a5a)); surf.rotation.x = Math.PI / 2; surf.position.set(0, 5.2, 0); surf.material.side = THREE.DoubleSide; reef.add(surf);
const SNOW = dots(400, 0xc8dcff, 0.025, true);
// ------------------------------------------------------------------ the story
const YAW = 180;                                                    // he faces +z (the shore and the camera); the sea and the moon are behind him
const F = fwdOf(YAW), Rt = rightOf(YAW), UP = V(0, 1, 0);
function blinkAt(s) { const u = ((s + 40) % 3.7) / 0.16; return u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0; }
const STAND1 = { ...addPose(STAND, { spine1: [-3, 0, 0], neck: [4, 0, 0] }), armL: A(8, 12, 0, 20), armR: A(8, 12, 0, 20) };
// looking back over his right shoulder and up at the moon; his right hand comes up a little ("what?")
const BACK = { ...addPose(STAND1, { spine2: [0, -14, 0], chest: [0, -10, 0], neck: [16, -42, 0], head: [18, -24, 0] }), armR: A(28, 22, 10, 75, 30), armL: A(14, 18, 0, 30) };
const TURN0 = mixPose(STAND1, BACK, 0.4);                           // frame one: already turning (so the loop's end lands here too)
// in the dark: hands a little out, looking around
const DARK = { ...addPose(STAND1, { spine2: [-2, 6, 0], neck: [6, 10, 0], head: [4, 8, 0] }), armR: A(22, 26, 0, 40, 20), armL: A(22, 26, 0, 40, 20) };
const WL_HI = -0.5, WL_LO = -0.95;                                  // the sea at high tide, and after the tide sinks

// the state at a time ----------------------------------------------
function guyAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  const face = { blink: blinkAt(lt + b * 1.3) };
  let pose = STAND1, root = { x: STANDP.x, y: 0.95, z: STANDP.z, yaw: YAW }, hands = [], show = true, cut = false;
  let stage = 'dock', moon = 0, wl = WL_LO, lant = 1, bob = 0, stars = 1, shake = 0;
  let pop = 0, phot = -1, tideK = 0, tilt = 23.5, pull = 0, spin = 0, ret = 0;
  if (b === 0) {                                                    // the moon blinks out; he spins round to look
    const off = smooth(0.0, 0.7, lt), fl = lt < 0.7 ? 0.5 + 0.5 * Math.cos(lt * 15.7) : 0;   // starts dimming on frame one (motion from the first frame)   // a flicker and a half at 2.5 a second (whole-scene light: stays under 3 flashes a second), then gone
    moon = (1 - off) * (0.35 + 0.65 * fl); wl = WL_HI; bob = 1; shake = smooth(0.15, 0.4, lt) * (1 - smooth(0.6, 1.3, lt));
    const k = smooth(0.0, 0.9, lt); pose = mixPose(TURN0, BACK, k);
    Object.assign(face, { fear: 0.2 + 0.7 * smooth(0.3, 1.0, lt), brow: 0.9 * smooth(0.2, 0.8, lt), oh: 0.5 * smooth(0.35, 0.9, lt), look: [-0.3, 0.6] });
  } else if (b === 1) {                                             // space: the moon pops, but its last light is still on the way
    show = false; stage = 'space'; pop = lt; phot = lt; spin = lt;
  } else if (b === 2) {                                             // the tide sinks down the pilings
    wl = WL_HI + (WL_LO - WL_HI) * smooth(0.2, d - 0.2, lt); pose = BACK; Object.assign(face, { fear: 0.7, brow: 0.7, look: [-0.3, 0.6] });
  } else if (b === 3) {                                             // space: the Sun still pulls a smaller tide
    show = false; stage = 'space'; tideK = 1 - 0.54 * smooth(0.6, 2.4, lt); pull = smooth(0.5, 1.2, lt); spin = 3 + lt;
  } else if (b === 4) {                                             // the dark: 125x darker than a full moon night
    lant = 0.55; const k = smooth(0, 0.8, lt); pose = mixPose(BACK, DARK, k);
    pose = addPose(pose, { neck: [0, 26 * Math.sin(lt * 1.6) * smooth(0.6, 1.4, lt), 0] });
    Object.assign(face, { fear: 0.6, brow: 0.8, squint: 0.4, look: [0.5 * Math.sin(lt * 2.1), 0.1] });
  } else if (b === 5) {                                             // the hatchlings head for the street light, not the sea
    show = false; stage = 'beach';
  } else if (b === 6) {                                             // the reef: the corals wait to let their eggs go
    show = false; stage = 'reef'; stars = 0;
  } else if (b === 7) {                                             // space: over millions of years the tilt swings to 85 degrees
    show = false; stage = 'space'; tilt = 23.5 + (85 - 23.5) * smooth(0.5, 3.0, lt); spin = 6 + 0.5 * lt;
  } else if (b === 8) {                                             // tipped over, one side hardly ever sees the Sun
    show = false; stage = 'space'; tilt = 85; spin = 8 + 0.8 * lt;
  } else if (b === 9) {                                             // back on the dark dock; at the end the moon comes back (the loop)
    lant = 0.55 + 0.45 * smooth(d - 0.9, d, lt); ret = smooth(d - 0.9, d, lt);
    moon = ret; wl = WL_LO + (WL_HI - WL_LO) * ret; bob = ret;
    pose = mixPose(mixPose(BACK, DARK, 1 - smooth(0, 0.6, lt) * 0), TURN0, smooth(d - 1.0, d - 0.05, lt));
    pose = addPose(pose, { neck: [0, 18 * Math.sin(lt * 1.3) * (1 - smooth(d - 1.2, d - 0.6, lt)), 0] });
    const e = smooth(d - 1.0, d - 0.05, lt);
    Object.assign(face, { fear: 0.6 * (1 - e) + 0.2 * e, brow: 0.8 * (1 - e), look: [-0.3 * e, 0.6 * e] });
  }
  const wb = 2 * Math.PI * Math.round(TOTAL / 2.6) / TOTAL;           // breathing (whole cycles over the loop)
  pose = addPose(pose, { spine1: [0.9 * Math.sin(wb * t), 0, 0], spine2: [0.6 * Math.sin(wb * t + 0.4), 0, 0], neck: [0.7 * Math.sin(wb * t + 1.1), 0, 0] });
  return { b, lt, d, pose, root, hands, show, cut, face, stage, moon, wl, lant, bob, stars, shake, pop, phot, tideK, tilt, pull, spin, ret };
}

// ------------------------------------------------------------------ cameras
const CAM0 = { pos: V(0.42, 1.05, 0.95), tgt: V(0.02, 1.95, -3.6), fov: 46 };   // low, in front of him: his face, the moon behind and above his head
function camAt(t, g) {
  const b = g.b, lt = g.lt, d = g.d, k = smooth(0, d, lt);
  const S = V(0, 0, 0); if (g.shake) S.set(0.012 * Math.sin(t * 61) * g.shake, 0.01 * Math.sin(t * 47 + 1) * g.shake, 0);
  if (b === 0) return { pos: CAM0.pos.clone().add(V(0, 0, -0.12 * k)).add(S), tgt: CAM0.tgt, fov: CAM0.fov };
  if (b === 9) { const e = smooth(d - 1.0, d, lt), pos = V(0.3, 1.45, 0.75).lerp(CAM0.pos, e), tgt = V(0, 1.55, -1.5).lerp(CAM0.tgt, e); return { pos, tgt, fov: 44 + 2 * e }; }
  if (b === 2) return { pos: V(5.2, 0.4 - 0.1 * k, -1.75), tgt: V(0.7, 0.05, -1.9), fov: 52 };
  if (b === 4) return { pos: V(0.25, 1.5, -0.3 - 0.15 * k), tgt: V(0, 1.6, -1.5), fov: 42 };
  if (b === 1) return { pos: SP.clone().add(V(0.7 + 0.1 * k, 1.2, 7.8 - 0.5 * k)), tgt: SP.clone().add(V(0.15, 1.0, -0.4)), fov: 42 };
  if (b === 3) return { pos: SP.clone().add(V(0, 0.2, 6.6 - 0.4 * k)), tgt: SP.clone().add(V(-0.2, 0.05, 0)), fov: 44 };
  if (b === 7) return { pos: SP.clone().add(V(0, 0.25, 5.6 - 0.4 * k)), tgt: SP.clone().add(V(0, 0.4, 0)), fov: 44 };
  if (b === 8) return { pos: SP.clone().add(V(1.0, 0.3, 5.0 - 0.4 * k)), tgt: SP.clone().add(V(0, 0, 0)), fov: 44 };
  if (b === 5) return { pos: BE.clone().add(V(-0.08, 0.34, -1.75 + 0.15 * k)), tgt: BE.clone().add(V(-0.05, 0.12, 2.0)), fov: 48 };
  if (b === 6) return { pos: RF.clone().add(V(0.3, 0.5, 1.8 - 0.3 * k)), tgt: RF.clone().add(V(0, 0.35, 0)), fov: 46 };
  return CAM0;
}
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
