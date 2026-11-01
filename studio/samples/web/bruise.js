// "You just slammed your leg into the coffee table, and by tomorrow it's purple." - a 3D Short: why you bruise so easily.
//   bruise.html?w=1080&h=1920            (times from bruise/times.json; one shot per narration line)
// Beats: 0 his shin hits the table; next day it's purple (hook) | 1 in the skin: the hit breaks tiny vessels, blood leaks | 2 the trapped blood: red, then blue and purple
//        3 days on his shin: green, yellow, gone | 4 why so easily? | 5 older skin: thinner, less padding | 6 aspirin, blood thinners; see a doctor | 7 reading his phone (loops)
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { loadGuy } from '/guy3d.js';

const Q = new URLSearchParams(location.search);
const W = +Q.get('w') || 720, H = +Q.get('h') || 1280;
const FPS = 30;
const TIMES = await (await fetch('/bruise/times.json')).json();
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
// ================================================================== WHY YOU BRUISE

// ------------------------------------------------------------------ the room: he stands by a coffee table (beats 7, 0, 3, 4, 6); his jeans are shorts today
const STANDP = V(0.35, 0, -0.35);                                   // where he stands (he faces +z, the back wall behind him)
G.reset(); G.root.updateMatrixWorld(true);
const KNEEY = wp(G.bones.shinL).y, HEMY = KNEEY + 0.07;
// shorts: the jeans below the hem draw as bare skin; up to five bruises painted on the skin (rest-pose positions)
const BU = { uBS: { value: [0, 1, 2, 3, 4].map(() => new THREE.Vector4(0, -5, 0, 0.03)) }, uBC: { value: [0, 1, 2, 3, 4].map(() => new THREE.Color(0x5a2a5a)) },
  uBA: { value: [0, 0, 0, 0, 0] }, uSkin: { value: new THREE.Color(0xd99a7c) } };
{ const jm = G.meshes.jeans.material, prev = jm.onBeforeCompile, prevKey = jm.customProgramCacheKey ? jm.customProgramCacheKey.bind(jm) : () => '';
  jm.onBeforeCompile = (sh, r) => { prev.call(jm, sh, r); Object.assign(sh.uniforms, BU);
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nuniform vec4 uBS[5]; uniform vec3 uBC[5]; uniform float uBA[5]; uniform vec3 uSkin;')
      .replace('dH_denim = h * fade; }', `dH_denim = h * fade; }
  { float leg = 1.0 - smoothstep(${(HEMY - 0.003).toFixed(4)}, ${(HEMY + 0.003).toFixed(4)}, vRestD.y);
    float cuff = (1.0 - leg) * (1.0 - smoothstep(${(HEMY + 0.028).toFixed(4)}, ${(HEMY + 0.032).toFixed(4)}, vRestD.y)); diffuseColor.rgb *= 1.0 - 0.18 * cuff;
    vec3 c = uSkin * (1.0 + 0.05 * (nG(vRestD * 140.0) - 0.5));
    for (int i = 0; i < 5; i++) { float d = length((vRestD - uBS[i].xyz) / vec3(1.0, 1.35, 1.0)) / uBS[i].w; float n = nG(vRestD * 70.0 + float(i) * 3.1);
      float a = uBA[i] * (1.0 - smoothstep(0.3, 1.0, d + 0.35 * (n - 0.5))); c = mix(c, uBC[i] * (0.85 + 0.3 * n), clamp(a, 0.0, 1.0)); }
    diffuseColor.rgb = mix(diffuseColor.rgb, c, leg); dH_denim *= 1.0 - leg; }`); };
  jm.customProgramCacheKey = () => prevKey() + '|shorts'; jm.needsUpdate = true; }
// the main bruise: the front of his left shin; find the skin vertex there (to aim the camera at it as he moves)
const JG = G.meshes.jeans.geometry.attributes.position;
const BRV = (() => { const sx = wp(G.bones.shinL).x, yc = KNEEY - 0.13; let best = -1, bz = 1e9;
  for (let i = 0; i < JG.count; i++) { const x = JG.getX(i), y = JG.getY(i), z = JG.getZ(i); if (Math.abs(y - yc) < 0.012 && Math.abs(x - sx) < 0.03 && z < bz) { bz = z; best = i; } } return best; })();
const BR0 = V(JG.getX(BRV), JG.getY(BRV), JG.getZ(BRV));
BU.uBS.value[0].set(BR0.x, BR0.y, BR0.z, 0.045);
// more bruises (beats 4 and 6): the other shin, his left knee, his right calf side
{ const sxR = wp(G.bones.shinR).x; const near = (xc, yc, pick) => { let best = 0, bv = 1e9; for (let i = 0; i < JG.count; i++) { const x = JG.getX(i), y = JG.getY(i), z = JG.getZ(i); if (Math.abs(y - yc) < 0.012 && Math.abs(x - xc) < 0.04) { const s = pick(x, z); if (s < bv) { bv = s; best = i; } } } return V(JG.getX(best), JG.getY(best), JG.getZ(best)); };
  const a = near(sxR, KNEEY - 0.2, (x, z) => z), b = near(wp(G.bones.shinL).x, KNEEY - 0.01, (x, z) => z), c = near(sxR, KNEEY - 0.08, (x, z) => -x + 0.5 * z), d = near(wp(G.bones.shinL).x, KNEEY - 0.27, (x, z) => -x);
  BU.uBS.value[1].set(a.x, a.y, a.z, 0.035); BU.uBS.value[2].set(b.x, b.y, b.z, 0.03); BU.uBS.value[3].set(c.x, c.y, c.z, 0.04); BU.uBS.value[4].set(d.x, d.y, d.z, 0.03); }
function bruiseW() { const m = G.meshes.jeans, a = BR0.clone(); m.applyBoneTransform(BRV, a); return a.applyMatrix4(m.matrixWorld); }
const BCOL = { red: new THREE.Color(0xa01c26), blue: new THREE.Color(0x3a3a8a), purple: new THREE.Color(0x5a2660), green: new THREE.Color(0x7d9040), yellow: new THREE.Color(0xc8a848) };
function bruiseCol(k) {                                             // 0 fresh red .. 1 blue .. 2 purple .. 3 green .. 4 yellow
  const st = [BCOL.red, BCOL.blue, BCOL.purple, BCOL.green, BCOL.yellow], i = Math.min(3, Math.floor(k)), f = k - i; return st[i].clone().lerp(st[i + 1], Math.min(1, f)); }

// the coffee table (placed in the tail so its edge is right where his shin swings)
const woodM = new THREE.MeshStandardMaterial({ map: canvasTex(512, 256, g => { g.fillStyle = '#7a4a2a'; g.fillRect(0, 0, 512, 256); for (let i = 0; i < 70; i++) { g.strokeStyle = `rgba(${40 + Math.random() * 30},20,10,${0.15 + Math.random() * 0.2})`; g.lineWidth = 1 + Math.random() * 2; g.beginPath(); const y = Math.random() * 256; g.moveTo(0, y); g.bezierCurveTo(170, y + 8 * Math.random() - 4, 340, y - 6, 512, y + 4 * Math.random()); g.stroke(); } }), roughness: 0.45 });
const TOPY = 0.42;
const ctable = new THREE.Group(); home.add(ctable);
box(1.0, 0.045, 0.55, 0, TOPY - 0.0225, 0.275, woodM, 0.012, ctable);
for (const [x, z] of [[-0.45, 0.05], [0.45, 0.05], [-0.45, 0.5], [0.45, 0.5]]) box(0.05, TOPY - 0.045, 0.05, x, (TOPY - 0.045) / 2, z, woodM, 0.01, ctable);
box(0.92, 0.025, 0.47, 0, 0.12, 0.275, woodM, 0.008, ctable);                 // the shelf below
// on the table: a mug, a remote; and (beat 6) two pill bottles
{ const mug = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.036, 0.095, 24), mat(0xe8e2d4, 0.4)); mug.position.set(-0.3, TOPY + 0.0475, 0.33); ctable.add(mug);
  box(0.05, 0.02, 0.17, 0.25, TOPY + 0.01, 0.38, mat(0x222226, 0.5), 0.006, ctable); }
const bottleT = (txt, sub, col) => canvasTex(512, 256, g => { g.fillStyle = '#f4f2ec'; g.fillRect(0, 0, 512, 256); g.fillStyle = col; g.fillRect(0, 36, 512, 120); g.fillStyle = '#fff'; g.font = 'bold 54px sans-serif'; g.textAlign = 'center'; g.fillText(txt, 256, 122); g.fillStyle = '#333'; g.font = 'bold 36px sans-serif'; g.fillText(sub, 256, 208); });
const PILLS = new THREE.Group(); ctable.add(PILLS); PILLS.visible = false;
for (const [x, z, txt, sub, col, h] of [[0.02, 0.2, 'ASPIRIN', '325 mg TABLETS', '#c8202a', 0.11], [0.17, 0.25, 'BLOOD', 'THINNER', '#2a5ab0', 0.13]]) {
  const b = new THREE.Mesh(new THREE.CylinderGeometry(0.034, 0.034, h, 32, 1, true), new THREE.MeshStandardMaterial({ map: bottleT(txt, sub, col), roughness: 0.5 })); b.position.set(x, TOPY + h / 2, z); b.rotation.y = -2.46; PILLS.add(b);
  const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.037, 0.037, 0.025, 32), mat(0xf6f6f2, 0.4)); cap.position.set(x, TOPY + h + 0.0125, z); PILLS.add(cap);
  const bot = new THREE.Mesh(new THREE.CircleGeometry(0.034, 24).rotateX(Math.PI / 2), mat(0xf4f2ec, 0.5)); bot.position.set(x, TOPY + 0.001, z); PILLS.add(bot);
  if (x < 0.1) for (let j = 0; j < 4; j++) { const p = new THREE.Mesh(new THREE.SphereGeometry(0.008, 12, 8), mat(0xf8f6f0, 0.5)); p.scale.y = 0.45; p.position.set(-0.06 + j * 0.022, TOPY + 0.004, 0.13 + (j % 2) * 0.02); PILLS.add(p); } }

// his phone (beats 7 and 0: he walks into the table reading it)
const phone = new THREE.Group(); scene.add(phone);
const phoneCanvas = document.createElement('canvas'); phoneCanvas.width = 360; phoneCanvas.height = 760;
const phoneTex = new THREE.CanvasTexture(phoneCanvas); phoneTex.colorSpace = THREE.SRGBColorSpace;
{ const pg = phoneCanvas.getContext('2d'); pg.fillStyle = '#101418'; pg.fillRect(0, 0, 360, 760);
  for (let i = 0; i < 6; i++) { pg.fillStyle = ['#2a3a4a', '#3a2a3a', '#2a4a3a'][i % 3]; pg.fillRect(20, 40 + i * 120, 320, 100); pg.fillStyle = '#c8d0d8'; pg.fillRect(34, 60 + i * 120, 200, 14); pg.fillRect(34, 86 + i * 120, 150, 10); } phoneTex.needsUpdate = true; }
{ const body = new THREE.Mesh(new THREE.BoxGeometry(0.072, 0.15, 0.008), mat(0x1a1a1e, 0.35, 0.4)); phone.add(body);
  const scr = new THREE.Mesh(new THREE.PlaneGeometry(0.066, 0.142), new THREE.MeshBasicMaterial({ map: phoneTex, toneMapped: false })); scr.position.z = 0.0041; phone.add(scr); }

// ------------------------------------------------------------------ the skin up close (a dark stage): skin, the layer under it, fat, muscle; tiny blood vessels
const MS = V(40, 0, 0);
const skinSet = new THREE.Group(); skinSet.position.copy(MS); scene.add(skinSet);
const msLight = new THREE.PointLight(0xfff0e8, 0, 6, 1.2); msLight.position.set(0.5, 1.9, 1.4); skinSet.add(msLight);
const msFill = new THREE.PointLight(0xffd8c8, 0, 5, 1.2); msFill.position.set(-0.8, 1.2, 1.2); skinSet.add(msFill);
skinSet.add(new THREE.Mesh(new THREE.SphereGeometry(5, 24, 12), new THREE.MeshBasicMaterial({ color: 0x120a0c, side: THREE.BackSide })));
const SKTOP = 1.25, SKW = 1.0, SKD = 0.6;                            // top of the skin; width (x), depth (z); the cut face is at z = +SKD/2
const LAY = new THREE.Group(); skinSet.add(LAY);
const layM = (c, r = 0.7) => new THREE.MeshStandardMaterial({ color: c, roughness: r });
const EPI = new THREE.Mesh(new THREE.BoxGeometry(SKW, 1, SKD), layM(0xd99a7c, 0.55)); LAY.add(EPI);
const DER = new THREE.Mesh(new THREE.BoxGeometry(SKW, 1, SKD), layM(0xe6908a)); LAY.add(DER);
const FAT = new THREE.Mesh(new THREE.BoxGeometry(SKW, 1, SKD), layM(0xf0cf72, 0.6)); LAY.add(FAT);
const MUS = new THREE.Mesh(new THREE.BoxGeometry(SKW, 0.8, SKD), new THREE.MeshStandardMaterial({ map: canvasTex(256, 128, g => { g.fillStyle = '#8a2228'; g.fillRect(0, 0, 256, 128); for (let i = 0; i < 26; i++) { g.strokeStyle = `rgba(${170 + Math.random() * 40},60,60,0.5)`; g.lineWidth = 2; g.beginPath(); const y = i * 5 + Math.random() * 3; g.moveTo(0, y); g.lineTo(256, y + 2); g.stroke(); } }), roughness: 0.6 })); LAY.add(MUS);
const FATB = []; for (let i = 0; i < 9; i++) { const s = new THREE.Mesh(new THREE.SphereGeometry(0.06, 20, 14), layM(0xf6dc86, 0.5)); s.userData.x = -0.44 + i * 0.11; s.userData.r = hash1(i * 4.1); LAY.add(s); FATB.push(s); }
// the vessels: tubes running across, lying in the cut face; the one under the hit has a middle piece that breaks
const vesM2 = new THREE.MeshStandardMaterial({ color: 0xc81e2a, emissive: 0x400408, roughness: 0.4 }), veinM2 = new THREE.MeshStandardMaterial({ color: 0x5a4aa8, roughness: 0.4 });
const VES = [];
for (const [fy, r, m, ph] of [[0.25, 0.011, vesM2, 0.3], [0.55, 0.016, vesM2, 1.7], [0.8, 0.022, veinM2, 2.9]]) {         // fy: depth as a fraction of the under-layer
  const parts = []; for (const [x0, x1] of [[-0.5, -0.06], [-0.06, 0.06], [0.06, 0.5]]) {
    const pts = []; for (let j = 0; j <= 12; j++) { const x = x0 + (x1 - x0) * j / 12; pts.push(V(x, 0.012 * Math.sin(x * 9 + ph), 0)); }
    const t = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 24, r, 10), m); LAY.add(t); parts.push(t); }
  VES.push({ fy, r, parts }); }
// leaked blood: a stain spreading in the cut face, the same spot seen through the skin on top, and drops
const poolM = new THREE.MeshBasicMaterial({ color: 0xa01c26, transparent: true, opacity: 0, depthWrite: false });
poolM.alphaMap = canvasTex(256, 256, g => { const gr = g.createRadialGradient(128, 128, 30, 128, 128, 128); gr.addColorStop(0, '#fff'); gr.addColorStop(0.7, '#ddd'); gr.addColorStop(1, '#000'); g.fillStyle = gr; g.fillRect(0, 0, 256, 256); });
const POOL = new THREE.Mesh(new THREE.CircleGeometry(1, 48), poolM); POOL.renderOrder = 3; LAY.add(POOL);
const topM = new THREE.MeshStandardMaterial({ color: 0xa01c26, transparent: true, opacity: 0, depthWrite: false, roughness: 0.6, map: canvasTex(256, 256, g => { const gr = g.createRadialGradient(128, 128, 10, 128, 128, 128); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.55, 'rgba(255,255,255,0.8)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 256, 256); }) });
topM.alphaMap = topM.map; const TOPSPOT = new THREE.Mesh(new THREE.PlaneGeometry(0.5, 0.36).rotateX(-Math.PI / 2), topM); TOPSPOT.position.set(0, SKTOP + 0.0015, 0.06); TOPSPOT.renderOrder = 3; skinSet.add(TOPSPOT);
const BLOOD = (() => { const g = new THREE.BufferGeometry(), n = 160, p = new Float32Array(n * 3); g.setAttribute('position', new THREE.BufferAttribute(p, 3)); g.setDrawRange(0, 0);
  const m = new THREE.Points(g, new THREE.PointsMaterial({ color: 0xb01828, size: 0.028, map: dotTex0(), transparent: true, depthWrite: false, toneMapped: false })); m.frustumCulled = false; m.renderOrder = 4; scene.add(m); return { m, p, n }; })();
function dotTex0() { return canvasTex(64, 64, g => { const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.5, 'rgba(255,255,255,0.9)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); }); }
// the hit: a table edge comes down on the skin
const EDGE = new THREE.Mesh(new RoundedBoxGeometry(0.34, 0.16, SKD + 0.1, 3, 0.03), woodM); skinSet.add(EDGE);
// layer thickness (beat 5: older skin is thinner, less padding)
function setLayers(thin) { const e = 0.04 * (1 - 0.4 * thin), d = 0.22 * (1 - 0.55 * thin), f = 0.26 * (1 - 0.65 * thin); let y = SKTOP;
  EPI.scale.y = e; EPI.position.y = y - e / 2; y -= e; DER.scale.y = d; DER.position.y = y - d / 2; const dTop = y; y -= d;
  FAT.scale.y = f; FAT.position.y = y - f / 2; for (const s of FATB) { s.position.set(s.userData.x, y - f * (0.3 + 0.4 * s.userData.r), SKD / 2 - 0.045); s.scale.set(1, Math.max(0.2, f / 0.26), 1); } y -= f;
  MUS.position.y = y - 0.4;
  for (const v of VES) for (const p of v.parts) p.position.set(0, dTop - d * v.fy, SKD / 2 - 0.004);
  return { dTop, d }; }
let LAYNOW = setLayers(0);
let XRNEW = false;

// ------------------------------------------------------------------ the story
const YAW = 180;                                                    // he faces +z (the back wall behind him)
const T_HIT = 0.42;                                                 // beat 0: his shin hits the table edge
const LOOPSEED = { R: null, L: null };
function blinkAt(s) { const u = ((s + 40) % 3.7) / 0.16; return u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0; }
const F = fwdOf(YAW), Rt = rightOf(YAW), UP = V(0, 1, 0);
const STAND1 = { ...addPose(STAND, { spine1: [-4, 0, 0], neck: [6, 0, 0] }), armL: A(10, 14, 0, 22), armR: A(10, 14, 0, 22) };
const PH = { rot: 15, n: 0.0165, u: 0.0, w: 0.0, c: 40, th: 30, opp: 30 };   // the phone across his palm: fingers wrap its edge, thumb on the screen
function phoneHand() { const hd = wp(G.bones.head), n = UP.clone().multiplyScalar(0.62).addScaledVector(F, -0.78).normalize(), u = F.clone().multiplyScalar(0.78).addScaledVector(UP, 0.62).normalize();
  return { S: 'L', p: hd.clone().addScaledVector(F, 0.27).addScaledVector(Rt, 0.04).add(V(0, -0.32, 0)), n, u, c: PH.c, th: PH.th, opp: PH.opp, memAbs: 'phoneL', seed: A(40, 10, 0, 110, -40) }; }
const NOB = [0, 0, 0, 0, 0];

// the state at a time ----------------------------------------------
function guyAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  const face = { blink: blinkAt(lt + b * 1.3) };
  let pose = STAND1, root = { x: STANDP.x, y: 0.95, z: STANDP.z, yaw: YAW }, hands = [], show = true, cut = false;
  let step = 0, lift = 0, bA = NOB.slice(), bK = [2, 3, 1, 4, 2], bR = 1, macro = false, hit = -1, burst = false, leak = 0, poolK = 0, thin = 0, topK = 0, pills = false, shake = 0, phoneOn = true;
  if (b === 7 || b === 0) {                                         // reading his phone as he walks; (0) his shin slams the table edge
    hands = [b === 0 && LOOPSEED.L ? { ...phoneHand(), seed: LOOPSEED.L, seedIsPrev: true } : phoneHand()];
    pose = addPose(STAND1, { neck: [-16, 0, 0], head: [-10, 0, 0] }); Object.assign(face, { look: [0, -0.6] });
    if (b === 0) {
      step = lt < T_HIT ? sm(lt / T_HIT) * 0.85 : 0.85 - 0.45 * smooth(T_HIT, T_HIT + 0.25, lt) - 0.4 * smooth(1.7, 2.2, lt);
      lift = smooth(T_HIT + 0.1, T_HIT + 0.45, lt) * (1 - smooth(1.6, 2.1, lt));      // the hurt leg comes up off the floor
      shake = lt > T_HIT ? Math.exp(-(lt - T_HIT) * 7) : 0;
      const ow = smooth(T_HIT, T_HIT + 0.15, lt) * (1 - 0.6 * smooth(1.8, 2.6, lt));
      pose = addPose(STAND1, { neck: [-16 * (1 - ow) - 26 * ow, 0, 0], head: [-10 * (1 - ow) - 8 * ow, 0, 0], spine1: [10 * ow, 0, 0], spine2: [8 * ow, 0, 0] });
      Object.assign(face, { look: [0, -0.6 + 0.2 * ow], squint: 0.9 * ow, brow: ow, jaw: 0.35 * ow, fear: 0.5 * ow });
      bA[0] = smooth(2.2, 3.3, lt); bK[0] = 2; root.y = 0.95 - 0.02 * lift; root.z = STANDP.z + 0.05 * step;
    }
  } else if (b === 1 || b === 2 || b === 5) {                        // up close in the skin
    show = false; macro = true; phoneOn = false;
    if (b === 1) { hit = lt; burst = lt > 0.36; leak = smooth(0.36, d - 0.2, lt); poolK = 0; }
    if (b === 2) { hit = 99; burst = true; leak = 1; poolK = 2 * smooth(0.6, d - 0.3, lt); topK = smooth(0.0, 0.6, lt); }
    if (b === 5) { thin = smooth(0.2, 1.8, lt); hit = lt - 1.75; burst = lt > 2.11; leak = smooth(2.11, d, lt); poolK = 0; }
  } else if (b === 3) {                                             // days go by on his shin: green, yellow, gone
    phoneOn = false; bA[0] = 1 - smooth(0.62 * d, d - 0.25, lt); bK[0] = 3 + smooth(0.15 * d, 0.55 * d, lt);
    pose = addPose(STAND1, { neck: [-10, 0, 0] });
  } else if (b === 4) {                                             // why do some people bruise so easily? he looks down at bruises all over his legs
    phoneOn = false; bA = [1, 0.9, 0.85, 0.9, 0.8]; bK = [2, 3.4, 1, 4, 2.3];
    const k = smooth(0.1, 0.8, lt); pose = addPose(STAND1, { neck: [-24 * k, 6 * k, 0], head: [-14 * k, 0, 6 * k], spine1: [6 * k, 0, 0] });
    Object.assign(face, { look: [0, -0.7 * k], brow: 0.8 * k, oh: 0.25 * k });
  } else if (b === 6) {                                             // aspirin and blood thinners (pills on the table); big bruises for no reason: see a doctor
    phoneOn = false; pills = lt < 2.2; cut = lt >= 2.2 && lt - 2.2 < 1 / 30 + 1e-6;
    if (!pills) { bA = [1, 1, 0.9, 1, 0.9]; bK = [2, 1.2, 2.4, 1.6, 2]; bR = 1.7; }
    pose = addPose(STAND1, { neck: [-8, 0, 0] }); Object.assign(face, { brow: 0.5 });
  }
  const wb = 2 * Math.PI * Math.round(TOTAL / 2.6) / TOTAL;           // breathing (whole cycles over the loop)
  pose = addPose(pose, { spine1: [0.9 * Math.sin(wb * t), 0, 0], spine2: [0.6 * Math.sin(wb * t + 0.4), 0, 0], neck: [0.7 * Math.sin(wb * t + 1.1), 0, 0] });
  return { b, lt, d, pose, root, hands, show, cut, step, lift, bA, bK, bR, macro, hit, burst, leak, poolK, thin, topK, pills, shake, phoneOn, face };
}

// ------------------------------------------------------------------ cameras (his left side is +x: the camera stays there, the kitchen wall behind him)
function shakeV(t, a) { return V(vn1(t * 14, 1) * a * 0.5, vn1(t * 14, 2) * a, vn1(t * 14, 3) * a); }
const CAM7 = { pos: STANDP.clone().add(V(1.75, 1.45, 1.55)), tgt: STANDP.clone().add(V(0.05, 0.92, 0.3)), fov: 50 };
function camAt(t, g) {
  const b = g.b, lt = g.lt, d = g.d, k = smooth(0, d, lt);
  if (b === 7) return { pos: CAM7.pos.clone().add(V(0.08 * (1 - k), 0.05 * (1 - k), 0.08 * (1 - k))), tgt: CAM7.tgt, fov: CAM7.fov };
  if (b === 0) { const a = sm(Math.min(1, lt / 0.4)), z = smooth(2.0, 3.0, lt), bw = bruiseW();
    const p1 = STANDP.clone().add(V(1.35, 0.72, 0.3)), t1 = STANDP.clone().add(V(0.1, 0.55, 0.22));
    const p2 = bw.clone().add(V(0.32, 0.1, 0.3)), t2 = bw.clone();
    return { pos: CAM7.pos.clone().lerp(p1, a).lerp(p2, z).add(shakeV(t, 0.025 * g.shake)), tgt: CAM7.tgt.clone().lerp(t1, a).lerp(t2, z), fov: CAM7.fov - 4 * a - 6 * z }; }
  if (b === 3) { const bw = bruiseW(); return { pos: bw.clone().add(V(0.3 - 0.04 * k, 0.12, 0.28 - 0.04 * k)), tgt: bw, fov: 40 }; }
  if (b === 4) return { pos: STANDP.clone().add(V(1.3, 1.35, 1.65 - 0.1 * k)), tgt: STANDP.clone().add(V(0.0, 0.88, 0.2)), fov: 50 };
  if (b === 6) { if (g.pills) return { pos: ctable.localToWorld(V(0.4, TOPY + 0.24, 0.66 + 0.03 * lt)), tgt: ctable.localToWorld(V(0.09, TOPY + 0.025, 0.22)), fov: 38 };
    return { pos: STANDP.clone().add(V(0.85, 0.65, 1.2)), tgt: STANDP.clone().add(V(0.0, 0.38, 0.1)), fov: 46 }; }
  // up close in the skin
  if (b === 1) return { pos: MS.clone().add(V(0.1, SKTOP - 0.05, 1.35 - 0.1 * k)).add(shakeV(t, 0.02 * (g.hit > 0.35 ? Math.exp(-(g.hit - 0.35) * 6) : 0))), tgt: MS.clone().add(V(0, SKTOP - 0.2, 0)), fov: 44 };
  if (b === 2) { const u = smooth(0, 1.4, lt); return { pos: MS.clone().add(V(0.1, SKTOP - 0.05 + 0.75 * u, 1.25 - 0.15 * u)), tgt: MS.clone().add(V(0, SKTOP - 0.2 + 0.08 * u, 0)), fov: 44 }; }
  if (b === 5) return { pos: MS.clone().add(V(-0.1, SKTOP - 0.1, 1.35 - 0.1 * k)), tgt: MS.clone().add(V(0, SKTOP - 0.25, 0)), fov: 44 };
  return CAM7;
}

// ------------------------------------------------------------------ clipping: him vs the room, the counter, the floor and his own body
const SOLIDS = [];
const sbox = (name, obj, min, max) => SOLIDS.push({ name, obj, box: new THREE.Box3(min, max) });
sbox('couch', couch, V(-1.1, 0, -0.45), V(1.1, 0.98, 0.45)); sbox('counter', counter, V(-0.33, 0, -1.5), V(0.33, 0.95, 2.35)); sbox('ctable', ctable, V(-0.5, 0, 0), V(0.5, TOPY, 0.55));
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
const BR_R = BU.uBS.value.map(v => v.w);
function update(t, frame) {
  t = ((t % TOTAL) + TOTAL) % TOTAL;
  let g = guyAt(t); STATE = { b: g.b };
  scene.updateMatrixWorld(true);
  G.root.visible = g.show;
  RG.applyPose(g.pose, g.root);
  const yaw = g.root.yaw, f = fwdOf(yaw), r = rightOf(yaw);
  for (const [S, sx] of [['R', 0.11], ['L', -0.11]]) {
    const fp = V(STANDP.x, 0, STANDP.z).addScaledVector(r, sx).addScaledVector(f, S === 'R' ? 0.02 : -0.02); fp.y = ANKLEH;
    let fq = yawQ(yaw);
    if (S === 'L') { fp.addScaledVector(f, 0.3 * g.step - 0.1 * g.lift); fp.y += 0.06 * Math.sin(Math.PI * Math.min(1, g.step)) + 0.2 * g.lift; fq = qAA(r, -25 * g.lift).multiply(fq); }
    RG.foot(S, fp, fp.clone().add(V(0, 0.45, 0)).addScaledVector(f, 1), fq); }
  G.root.updateMatrixWorld(true);
  const list = [];
  if (g.show) { BODYNOW = surfNow(); const g2 = guyAt(t); g.hands = g2.hands; for (const h of g.hands) list.push(h); }
  for (const h of list) if (h.memAbs) h.memAbs += ':' + g.b;            // a hold never carries across a cut
  if (list.length) { RG.hands(list, 'b' + g.b, frame); LASTH = list; }
  for (const S of ['R', 'L']) if (!list.some(h => h.S === S)) delete RG.LAST['cost' + S];
  G.root.updateMatrixWorld(true); RG.untwist(); G.face(g.face); G.root.updateMatrixWorld(true);
  // the phone in his left hand, across the palm
  phone.visible = g.show && g.phoneOn;
  if (phone.visible) propFromHand(phone, 'L', (o, pw, n, u, w) => { const ax = w.clone().multiplyScalar(Math.cos(PH.rot * D2R)).addScaledVector(u, Math.sin(PH.rot * D2R));
    o.quaternion.copy(basisQ(new THREE.Vector3().crossVectors(ax, n), ax)); o.position.copy(pw).addScaledVector(n, PH.n).addScaledVector(u, PH.u).addScaledVector(w, PH.w); });
  // bruises on his legs
  for (let i = 0; i < 5; i++) { BU.uBA.value[i] = g.bA[i]; BU.uBC.value[i].copy(bruiseCol(g.bK[i])); BU.uBS.value[i].w = BR_R[i] * (i === 0 ? 1 : g.bR); }
  PILLS.visible = g.pills;
  // up close in the skin
  skinSet.visible = g.macro; msLight.intensity = g.macro ? 5 : 0; msFill.intensity = g.macro ? 1.5 : 0;
  if (g.macro) { const L = setLayers(g.thin);
    let ey = 3; const h = g.hit; if (h >= 0 && h < 5) { ey = h < 0.35 ? 0.6 * (1 - sm(h / 0.35)) : h < 0.55 ? -0.01 * Math.sin(Math.PI * (h - 0.35) / 0.2) : 1.0 * sm(Math.min(1, (h - 0.55) / 0.7)); }
    EDGE.position.set(0, SKTOP + 0.08 + ey, 0.0); EDGE.visible = ey < 1.5;
    for (const v of VES.slice(0, 2)) v.parts[1].visible = !g.burst;
    const col = bruiseCol(g.poolK), py = L.dTop - L.d * 0.42, lk = Math.pow(g.leak, 0.7);
    POOL.position.set(0, py, SKD / 2 + 0.003); POOL.scale.set(Math.max(0.001, 0.3 * lk), Math.max(0.001, Math.min(0.5 * L.d, 0.1) * lk), 1); poolM.opacity = 0.8 * Math.min(1, g.leak * 1.5); poolM.color.copy(col);
    topM.opacity = 0.85 * g.topK * g.leak; topM.color.copy(col.clone().lerp(new THREE.Color(0xd99a7c), 0.2));
    const n = Math.round(BLOOD.n * Math.min(1, g.leak * 1.25)); BLOOD.m.material.color.copy(col);
    for (let i = 0; i < n; i++) { const v = VES[i % 2], sy = L.dTop - L.d * v.fy, side = i % 4 < 2 ? -1 : 1, q = sm(clamp((g.leak - 0.75 * i / BLOOD.n) / 0.25, 0, 1));
      const a = hash1(i * 3.3) * 6.283, rr = Math.sqrt(hash1(i * 7.1)), dst = V(Math.cos(a) * 0.28 * rr, py + Math.sin(a) * Math.min(0.5 * L.d, 0.1) * 0.9 * rr, 0);
      const p = V(0.06 * side, sy, 0).lerp(dst, q); p.z = SKD / 2 + 0.012; p.add(MS); BLOOD.p.set([p.x, p.y, p.z], i * 3); }
    BLOOD.m.geometry.setDrawRange(0, n); BLOOD.m.geometry.attributes.position.needsUpdate = true; BLOOD.m.visible = n > 0; } else BLOOD.m.visible = false;
  // camera and light
  const C = camAt(t, g); camera.position.copy(C.pos); camera.up.set(0, 1, 0); camera.lookAt(C.tgt); camera.fov = C.fov; camera.updateProjectionMatrix();
  const dim = g.macro ? 0.3 : 1;
  sun.intensity = 2.6 * dim; hemi.intensity = 0.85 * dim; scene.environmentIntensity = 0.35 * dim; lamp.intensity = 6 * dim;
  clockHands.s.rotation.z = -t * 6 * D2R; clockHands.m.rotation.z = -1.1; clockHands.h.rotation.z = -3.3;
  return { beat: g.b, cut: g.cut };
}
G.reset(); G.root.updateMatrixWorld(true);
const ANKLEH = wp(G.bones.footR).y;

// put the table where his shin is at the moment of the hit: its near top edge just touching the front of his left shin
{ G.reset(); const yc = TOPY - 0.012, sx = wp(G.bones.shinL).x; let best = -1, bz = -1e9;
  for (let i = 0; i < JG.count; i++) { const x = JG.getX(i), y = JG.getY(i), z = JG.getZ(i); if (Math.abs(y - yc) < 0.015 && Math.abs(x - sx) < 0.05 && -z > bz) { bz = -z; best = i; } }   // the front (rest pose faces -z)
  update(B[0] + T_HIT, -90); const m = G.meshes.jeans, a = V(JG.getX(best), JG.getY(best), JG.getZ(best)); m.applyBoneTransform(best, a); a.applyMatrix4(m.matrixWorld);
  ctable.position.set(a.x - 0.38, 0, a.z + 0.004); ctable.updateMatrixWorld(true); window.SHINHIT = a.toArray(); }

// ------------------------------------------------------------------ frame I/O (same contract as the other 3D Shorts)
const draw = () => { if (XRNEW) { renderer.render(scene, camera); XRNEW = false; } renderer.render(scene, camera); };
const gl = renderer.getContext(), px = new Uint8Array(W * H * 4);
let CUTF = false, LASTB = 0;
function segStart(t) { return B[beatAt(t)]; }
function stepTo(i) { const t = i / FPS, tt = ((t % TOTAL) + TOTAL) % TOTAL;
  if (i !== LASTF + 1) for (let j = Math.ceil(segStart(tt) * FPS - 1e-6) + Math.floor(t / TOTAL) * Math.round(TOTAL * FPS); j < i; j++) update(j / FPS, j);
  const r = update(t, i); CUTF = r.cut; LASTB = r.beat; LASTF = i; }
for (let i = Math.ceil(B[7] * FPS); i < Math.round(TOTAL * FPS); i++) update(i / FPS, i);
LOOPSEED.L = RG.LAST.armL.slice();
draw(); update(B[1] + 1.0, -50); draw(); update(B[6] + 0.5, -40); draw();     // warm-up: compile the skin close-up and the pills now
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
