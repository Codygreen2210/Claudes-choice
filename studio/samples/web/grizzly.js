// Grizzly attack near Bella Coola, B.C. (Oct 31, 2026): what to do if a grizzly charges. No attack on a person is shown.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { loadGuy } from '/guy3d.js';

const Q = new URLSearchParams(location.search);
const W = +Q.get('w') || 720, H = +Q.get('h') || 1280;
const FPS = 30;
const TIMES = await (await fetch('/grizzly/times.json')).json();
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
// ================================================================== A B.C. TRAIL AND A GRIZZLY
// ------------------------------------------------------------------ set: a coastal B.C. valley in late fall: a dirt trail through tall conifers, steep mountains, overcast light
home.visible = false; lamp.visible = false;
camera.far = 6000; camera.updateProjectionMatrix();
scene.background = new THREE.Color(0xaabccb); scene.fog = new THREE.Fog(0xb2c0cb, 60, 1500); scene.environmentIntensity = 0.4;
hemi.color.set(0xdbe6f0); hemi.groundColor.set(0x4a4a32); hemi.intensity = 1.1; sun.color.set(0xfff0dc); sun.intensity = 1.6; sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.03;
{ const S = sun.shadow.camera; S.left = -14; S.right = 14; S.top = 14; S.bottom = -14; S.near = 1; S.far = 200; S.updateProjectionMatrix(); }
const SKY = new THREE.Mesh(new THREE.SphereGeometry(5000, 32, 16), new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false, fog: false, uniforms: { uSet: { value: 0 } },
  vertexShader: 'varying vec3 d; void main(){ d = normalize(position); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }',
  fragmentShader: `uniform float uSet; varying vec3 d; void main(){ float h = clamp(d.y, 0., 1.); vec3 day = mix(vec3(.72,.78,.83), vec3(.5,.6,.7), pow(h, .6)); vec3 dusk = mix(vec3(.95,.62,.45), vec3(.22,.22,.38), pow(h, .5));
    gl_FragColor = vec4(mix(day, dusk, uSet), 1.);
    #include <colorspace_fragment>
  }` })); SKY.renderOrder = -10; SKY.frustumCulled = false; scene.add(SKY); window.__SKY = SKY;
const SKYU = SKY.material.uniforms;
function n2(x, z) { const xi = Math.floor(x), zi = Math.floor(z), xf = x - xi, zf = z - zi, h = (a, b) => hash1(a * 157.1 + b * 311.7);
  const u = xf * xf * (3 - 2 * xf), v = zf * zf * (3 - 2 * zf); return lerp(lerp(h(xi, zi), h(xi + 1, zi), u), lerp(h(xi, zi + 1), h(xi + 1, zi + 1), u), v); }
function fbm(x, z) { let s = 0, a = 0.5, f = 1; for (let i = 0; i < 5; i++) { s += a * n2(x * f, z * f); f *= 2.03; a *= 0.5; } return s; }
// the valley runs along z; floor about 600 m wide; steep walls up to ~1.6 km with snow on top (Bella Coola valley)
function HT(x, z) { const d = Math.abs(x + 300), wall = smooth(320, 1100, d); return wall * (900 + 900 * fbm(x / 500, z / 500)) + (1 - wall) * 0.6 * (fbm(x / 20, z / 20) - 0.5); }
{ const g = new THREE.PlaneGeometry(9000, 9000, 300, 300).rotateX(-Math.PI / 2), P = g.attributes.position, col = [];
  for (let i = 0; i < P.count; i++) { const x = P.getX(i), z = P.getZ(i); let y = HT(x, z); if (Math.abs(x) < 60 && Math.abs(z) < 120) y = Math.min(y, 0.0); P.setY(i, y); }
  g.computeVertexNormals(); const N = g.attributes.normal;
  for (let i = 0; i < P.count; i++) { const y = P.getY(i), ny = N.getY(i), k = fbm(P.getX(i) / 40, P.getZ(i) / 40);
    let c = y < 30 ? [0.22 + 0.08 * k, 0.27 + 0.08 * k, 0.15] : (y < 700 ? [0.14 + 0.05 * k, 0.22 + 0.06 * k, 0.13] : [0.42, 0.42, 0.42]); if (y > 1150 + 200 * k && ny > 0.45) c = [0.9, 0.92, 0.95];
    const cc = new THREE.Color().setRGB(c[0], c[1], c[2], THREE.SRGBColorSpace); col.push(cc.r, cc.g, cc.b); }
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  const t = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 1 })); t.receiveShadow = true; scene.add(t); }
// the river (wide, grey-green) down the middle of the valley, away from the trail
{ const r = new THREE.Mesh(new THREE.PlaneGeometry(70, 9000).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0x6f8a86, roughness: 0.2, metalness: 0.1 })); r.position.set(-300, 0.15, 0); scene.add(r); }
// the trail: packed dirt, a gentle S along z through the trees
const trailX = z => 1.6 * Math.sin(z / 14);
{ const pts = [], N = 160; const g = new THREE.BufferGeometry(), pos = [], idx = [];
  for (let i = 0; i <= N; i++) { const z = 60 - i * 1.2, x = trailX(z), w = 0.85 + 0.15 * Math.sin(i * 0.7); pos.push(x - w, 0.03, z, x + w, 0.03, z); if (i) { const a = (i - 1) * 2; idx.push(a, a + 1, a + 2, a + 1, a + 3, a + 2); } }
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setIndex(idx); g.computeVertexNormals();
  const m = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ map: canvasTex(256, 256, c => { c.fillStyle = '#6b5640'; c.fillRect(0, 0, 256, 256); for (let i = 0; i < 4000; i++) { c.fillStyle = `rgba(${60 + 50 * Math.random()},${45 + 40 * Math.random()},${30 + 30 * Math.random()},0.5)`; c.fillRect(Math.random() * 256, Math.random() * 256, 2, 2); } }), roughness: 1 }));
  m.receiveShadow = true; scene.add(m); }
// conifers (instanced): trunk + three stacked cones; thick near the trail, a forest across the valley floor for the air shot
const TREES = [];
{ const R = [], trunkG = new THREE.CylinderGeometry(0.18, 0.32, 1, 7), coneG = new THREE.ConeGeometry(1, 1, 9);
  for (let i = 0; i < 2600; i++) { const near = i < 900; const x = near ? (hash1(i * 1.1) - 0.5) * 120 : -600 + hash1(i * 2.3) * 700, z = near ? 60 - hash1(i * 3.7) * 170 : (hash1(i * 5.1) - 0.5) * 2400;
    if (Math.abs(x - trailX(z)) < 3.2 + 2 * hash1(i * 7)) continue; if (Math.abs(x + 300) < 45) continue; R.push([x, z, 14 + 16 * hash1(i * 9), hash1(i * 11)]); }
  const n = R.length, trunk = new THREE.InstancedMesh(trunkG, mat(0x4a3526, 0.95), n), cones = new THREE.InstancedMesh(coneG, mat(0x1f3b26, 0.9), n * 3), M = new THREE.Matrix4(), q = new THREE.Quaternion(), col = new THREE.Color();
  R.forEach(([x, z, h, k], i) => { M.compose(V(x, h * 0.25, z), q, V(1 + k * 0.3, h * 0.5, 1 + k * 0.3)); trunk.setMatrixAt(i, M);
    for (let j = 0; j < 3; j++) { const w = (2.6 + 1.2 * k) * (1 - j * 0.24), y0 = h * (0.3 + j * 0.22); M.compose(V(x, y0 + h * 0.2, z), q, V(w, h * 0.42, w)); cones.setMatrixAt(i * 3 + j, M);
      col.setHSL(0.36 + 0.04 * k, 0.35, 0.13 + 0.06 * k + j * 0.01); cones.setColorAt(i * 3 + j, col); } TREES.push([x, z]); });
  trunk.castShadow = cones.castShadow = true; trunk.receiveShadow = cones.receiveShadow = true; scene.add(trunk, cones); }
// undergrowth: ferns and salal (low green clumps), mossy logs, a few rocks
for (let i = 0; i < 260; i++) { const z = 50 - hash1(i * 2.9) * 120, x = trailX(z) + (hash1(i * 4.3) > 0.5 ? 1 : -1) * (2.2 + 7 * hash1(i * 6.1));
  const b = new THREE.Mesh(new THREE.DodecahedronGeometry(0.22 + 0.3 * hash1(i), 1), mat(new THREE.Color().setHSL(0.29 + 0.05 * hash1(i * 3), 0.5, 0.1 + 0.05 * hash1(i * 5)), 0.95)); b.position.set(x, 0.15, z); b.scale.set(1.3, 0.55, 1.1); b.castShadow = true; scene.add(b); }
for (let i = 0; i < 10; i++) { const z = 40 - i * 11, x = trailX(z) + (i % 2 ? 5 : -5); const l = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.35, 7, 10).rotateZ(Math.PI / 2), mat(0x4b5a32, 0.95)); l.position.set(x, 0.3, z); l.rotation.y = i; l.castShadow = true; scene.add(l); }
// ---- the grizzly: one smooth skinned body (signed-distance shape meshed with surface nets) under 14 shells of fur.
// ~2 m long, ~1.05 m at the shoulder hump, dished face, small round ears, darker legs, grizzled (pale-tipped) back, long pale front claws. Nose to -z, root on the ground.
const BEAR = new THREE.Group(); scene.add(BEAR);
{ const U = BEAR.userData;
  const elli = (p, c, r) => { const x = (p.x - c[0]) / r[0], y = (p.y - c[1]) / r[1], z = (p.z - c[2]) / r[2], k0 = Math.hypot(x, y, z), k1 = Math.hypot(x / r[0], y / r[1], z / r[2]); return k0 * (k0 - 1) / Math.max(k1, 1e-6); };
  const cone = (p, a, b, ra, rb) => { const bax = b[0] - a[0], bay = b[1] - a[1], baz = b[2] - a[2], pax = p.x - a[0], pay = p.y - a[1], paz = p.z - a[2];
    const t = clamp((pax * bax + pay * bay + paz * baz) / (bax * bax + bay * bay + baz * baz), 0, 1); return Math.hypot(pax - bax * t, pay - bay * t, paz - baz * t) - (ra + (rb - ra) * t); };
  const smin = (a, b, k) => { const h = Math.max(k - Math.abs(a - b), 0) / k; return Math.min(a, b) - h * h * k * 0.25; };
  const smax = (a, b, k) => -smin(-a, -b, k);
  const FS = [-0.25, 0.25], LEG = s => ({ sh: [0.26 * s, 0.88, -0.5], el: [0.25 * s, 0.46, -0.44], wr: [0.24 * s, 0.13, -0.5], ptip: [0.24 * s, 0.05, -0.68], hp: [0.25 * s, 0.86, 0.6], kn: [0.27 * s, 0.5, 0.5], an: [0.25 * s, 0.14, 0.62], ftip: [0.25 * s, 0.05, 0.4] });
  const LL = [LEG(-1), LEG(1)];
  function sdf(p) {
    let d = elli(p, [0, 0.86, 0.05], [0.46, 0.45, 0.86]);
    d = smin(d, elli(p, [0, 1.13, -0.42], [0.37, 0.3, 0.44]), 0.14);          // shoulder hump (a grizzly's mark)
    d = smin(d, elli(p, [0, 0.86, 0.62], [0.44, 0.46, 0.46]), 0.14);          // rump
    d = smin(d, elli(p, [0, 0.64, 0.1], [0.37, 0.24, 0.62]), 0.12);           // belly
    d = smin(d, elli(p, [0, 0.93, -0.84], [0.27, 0.28, 0.36]), 0.12);         // neck
    d = smin(d, elli(p, [0, 0.93, -1.12], [0.235, 0.215, 0.25]), 0.09);       // skull
    for (const s of [-1, 1]) d = smin(d, elli(p, [0.13 * s, 0.87, -1.13], [0.12, 0.12, 0.14]), 0.06);   // cheek ruff
    d = smin(d, cone(p, [0, 0.89, -1.2], [0, 0.835, -1.49], 0.105, 0.07), 0.06);                      // muzzle
    d = smax(d, -elli(p, [0, 1.005, -1.33], [0.12, 0.05, 0.1]), 0.04);                                // the dished face between brow and muzzle
    for (const s of [-1, 1]) d = smin(d, elli(p, [0.155 * s, 1.12, -1.03], [0.065, 0.06, 0.035]), 0.03);   // ears
    for (const L of LL) { d = smin(d, cone(p, L.sh, L.el, 0.16, 0.12), 0.1); d = smin(d, cone(p, L.el, L.wr, 0.12, 0.1), 0.05); d = smin(d, elli(p, [L.wr[0], 0.06, -0.58], [0.12, 0.065, 0.17]), 0.06);
      d = smin(d, cone(p, L.hp, L.kn, 0.19, 0.13), 0.1); d = smin(d, cone(p, L.kn, L.an, 0.12, 0.1), 0.05); d = smin(d, elli(p, [L.an[0], 0.055, 0.55], [0.11, 0.055, 0.2]), 0.06); }
    d = smin(d, elli(p, [0, 0.86, 1.04], [0.06, 0.08, 0.06]), 0.04);          // tail stub
    return Math.max(d, -p.y); }
  // surface nets
  const h = 0.022, x0 = -0.62, y0 = -0.03, z0 = -1.6, nx = Math.ceil(1.24 / h) + 1, ny = Math.ceil(1.4 / h) + 1, nz = Math.ceil(2.8 / h) + 1;
  const F = new Float32Array(nx * ny * nz), id = (i, j, k) => i + nx * (j + ny * k), q = V(0, 0, 0);
  for (let k = 0; k < nz; k++) for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) F[id(i, j, k)] = sdf(q.set(x0 + i * h, y0 + j * h, z0 + k * h));
  const VI = new Int32Array(nx * ny * nz).fill(-1), pos = [], E = [[0, 1], [2, 3], [4, 5], [6, 7], [0, 2], [1, 3], [4, 6], [5, 7], [0, 4], [1, 5], [2, 6], [3, 7]];
  for (let k = 0; k < nz - 1; k++) for (let j = 0; j < ny - 1; j++) for (let i = 0; i < nx - 1; i++) { const c = [], cp_ = [];
    for (let m = 0; m < 8; m++) { const a = i + (m & 1), b = j + ((m >> 1) & 1), e = k + ((m >> 2) & 1); c.push(F[id(a, b, e)]); cp_.push([a, b, e]); }
    let neg = 0; for (const v of c) if (v < 0) neg++; if (neg === 0 || neg === 8) continue;
    let sx = 0, sy = 0, sz = 0, n = 0; for (const [a, b] of E) { if ((c[a] < 0) === (c[b] < 0)) continue; const t = c[a] / (c[a] - c[b]); sx += cp_[a][0] + t * (cp_[b][0] - cp_[a][0]); sy += cp_[a][1] + t * (cp_[b][1] - cp_[a][1]); sz += cp_[a][2] + t * (cp_[b][2] - cp_[a][2]); n++; }
    VI[id(i, j, k)] = pos.length / 3; pos.push(x0 + sx / n * h, y0 + sy / n * h, z0 + sz / n * h); }
  const idx = [], quad = (a, b, c, d, flip) => { if (a < 0 || b < 0 || c < 0 || d < 0) return; flip ? idx.push(a, c, b, a, d, c) : idx.push(a, b, c, a, c, d); };
  for (let k = 1; k < nz - 1; k++) for (let j = 1; j < ny - 1; j++) for (let i = 1; i < nx - 1; i++) { const s0 = F[id(i, j, k)] < 0;
    if (s0 !== (F[id(i + 1, j, k)] < 0)) quad(VI[id(i, j - 1, k - 1)], VI[id(i, j, k - 1)], VI[id(i, j, k)], VI[id(i, j - 1, k)], !s0);
    if (s0 !== (F[id(i, j + 1, k)] < 0)) quad(VI[id(i - 1, j, k - 1)], VI[id(i - 1, j, k)], VI[id(i, j, k)], VI[id(i, j, k - 1)], !s0);
    if (s0 !== (F[id(i, j, k + 1)] < 0)) quad(VI[id(i - 1, j - 1, k)], VI[id(i, j - 1, k)], VI[id(i, j, k)], VI[id(i - 1, j, k)], !s0); }
  const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); geo.setIndex(idx);
  // normals from the field (smooth), and a winding check against them
  const nrm = new Float32Array(pos.length), e = 0.004;
  for (let v = 0; v < pos.length; v += 3) { q.set(pos[v], pos[v + 1], pos[v + 2]); const gx = sdf(V(q.x + e, q.y, q.z)) - sdf(V(q.x - e, q.y, q.z)), gy = sdf(V(q.x, q.y + e, q.z)) - sdf(V(q.x, q.y - e, q.z)), gz = sdf(V(q.x, q.y, q.z + e)) - sdf(V(q.x, q.y, q.z - e)), l = Math.hypot(gx, gy, gz) || 1; nrm[v] = gx / l; nrm[v + 1] = gy / l; nrm[v + 2] = gz / l; }
  { const ia = geo.index.array, A = V(0, 0, 0), Bv = V(0, 0, 0), Cv = V(0, 0, 0); let agree = 0; for (let t = 0; t < ia.length; t += 3) { A.fromArray(pos, ia[t] * 3); Bv.fromArray(pos, ia[t + 1] * 3); Cv.fromArray(pos, ia[t + 2] * 3); const fn = Bv.sub(A).cross(Cv.sub(A)); agree += Math.sign(fn.x * nrm[ia[t] * 3] + fn.y * nrm[ia[t] * 3 + 1] + fn.z * nrm[ia[t] * 3 + 2]); }
    if (agree < 0) for (let t = 0; t < ia.length; t += 3) { const tmp = ia[t + 1]; ia[t + 1] = ia[t + 2]; ia[t + 2] = tmp; } }
  geo.setAttribute('normal', new THREE.BufferAttribute(nrm, 3));
  // colour by region: dark legs and muzzle tip, brown body, pale-tipped hump and shoulders, lighter face
  const col = [], cc = new THREE.Color(), BROWN = [0.36, 0.25, 0.15], DARK = [0.2, 0.135, 0.085], PALE = [0.62, 0.5, 0.36], FACE = [0.45, 0.33, 0.22];
  for (let v = 0; v < pos.length; v += 3) { const x = pos[v], y = pos[v + 1], z = pos[v + 2], k = fbm(x * 9 + 3, z * 9 + y * 7);
    let c = BROWN.slice(); const legk = 1 - smooth(0.42, 0.62, y); c = c.map((a, i) => lerp(a, DARK[i], legk));
    const hump = smooth(0.95, 1.2, y) * (1 - smooth(-0.2, 0.3, z)); c = c.map((a, i) => lerp(a, PALE[i], 0.75 * hump));
    const face = smooth(-0.98, -1.08, z); c = c.map((a, i) => lerp(a, FACE[i], face)); const tip = smooth(-1.38, -1.47, z); c = c.map((a, i) => lerp(a, DARK[i], tip));
    c = c.map(a => a * (0.85 + 0.3 * k)); cc.setRGB(c[0], c[1], c[2], THREE.SRGBColorSpace); col.push(cc.r, cc.g, cc.b); }
  geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  { const fl = []; for (let v = 0; v < pos.length; v += 3) { const y = pos[v + 1], z = pos[v + 2]; let f = 1 - 0.7 * smooth(-1.0, -1.16, z) * smooth(0.7, 0.8, y); f = Math.min(f, 1 - 0.85 * smooth(-1.3, -1.38, z)); f *= 1 - 0.5 * (1 - smooth(0.04, 0.14, y)); fl.push(f); }
    geo.setAttribute('aFur', new THREE.Float32BufferAttribute(fl, 1)); }   // short fur on the face, almost none on the muzzle and nose, short on the paws
  // skeleton
  const bone = (par, w) => { const b = new THREE.Bone(); const pw = par.userData.w || [0, 0, 0]; b.position.set(w[0] - pw[0], w[1] - pw[1], w[2] - pw[2]); b.userData.w = w; par.add(b); return b; };
  const rootB = new THREE.Bone(); rootB.userData.w = [0, 0, 0]; const spine = bone(rootB, [0, 0.86, 0]), neck = bone(spine, [0, 0.93, -0.74]), head = bone(neck, [0, 0.93, -1.05]);
  const legsB = LL.map(L => { const sh = bone(spine, L.sh), el = bone(sh, L.el), wr = bone(el, L.wr), hp = bone(spine, L.hp), kn = bone(hp, L.kn), an = bone(kn, L.an); return { sh, el, wr, hp, kn, an }; });
  const bones = []; rootB.traverse(b => bones.push(b)); const bi = b => bones.indexOf(b);
  const SEG = [[[0, 0.86, -0.6], [0, 0.86, 0.8], 0.44, spine], [[0, 1.0, -0.45], [0, 1.08, -0.3], 0.34, spine], [[0, 0.93, -0.7], [0, 0.93, -0.95], 0.27, neck], [[0, 0.93, -1.02], [0, 0.84, -1.47], 0.2, head]];
  LL.forEach((L, s) => { const B_ = legsB[s]; SEG.push([L.sh, L.el, 0.15, B_.sh], [L.el, L.wr, 0.11, B_.el], [L.wr, [L.wr[0], 0.05, -0.72], 0.1, B_.wr], [L.hp, L.kn, 0.18, B_.hp], [L.kn, L.an, 0.11, B_.kn], [L.an, [L.an[0], 0.05, 0.38], 0.1, B_.an]); });
  const si = [], sw = [];
  for (let v = 0; v < pos.length; v += 3) { q.set(pos[v], pos[v + 1], pos[v + 2]); const ws = SEG.map(([a, b, r, bn]) => { const dd = Math.max(0.01, cone(q, a, b, 0, 0) - r * 0.55); return [bi(bn), 1 / dd ** 4]; });
    const acc = {}; for (const [i, w] of ws) acc[i] = (acc[i] || 0) + w; const top = Object.entries(acc).sort((x, y) => y[1] - x[1]).slice(0, 4); const tot = top.reduce((s, x) => s + x[1], 0);
    for (let m = 0; m < 4; m++) { si.push(top[m] ? +top[m][0] : 0); sw.push(top[m] ? top[m][1] / tot : 0); } }
  geo.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(si, 4)); geo.setAttribute('skinWeight', new THREE.Float32BufferAttribute(sw, 4));
  const skel = new THREE.Skeleton(bones);
  // fur: the base skin, then shells pushed out along the normal; each shell keeps only the strands taller than it (3D noise on the rest position, so strands stay put)
  const NSH = 14, FUR = 0.045, furMat = k => { const m = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 1, side: k ? THREE.DoubleSide : THREE.FrontSide });
    m.onBeforeCompile = sh => { sh.uniforms.uK = { value: k };
      sh.vertexShader = 'uniform float uK; attribute float aFur; varying vec3 vRest;\n' + sh.vertexShader.replace('#include <skinning_vertex>', `#include <skinning_vertex>
        vRest = position; transformed += normalize(objectNormal) * ${FUR.toFixed(3)} * uK * aFur; transformed.y -= ${(FUR * 0.35).toFixed(3)} * uK * uK * aFur;`);
      sh.fragmentShader = 'uniform float uK; varying vec3 vRest;\nfloat hh(vec3 p){ return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453); }\n' + sh.fragmentShader.replace('#include <color_fragment>', `#include <color_fragment>
        { vec3 cell = floor(vRest * 320.0); float n = hh(cell), n2 = hh(cell + 17.0); if (uK > 0.0 && n < uK * 0.8 + 0.04) discard;
          diffuseColor.rgb *= mix(0.7, 1.05, uK) * (0.93 + 0.14 * n2); diffuseColor.rgb = mix(diffuseColor.rgb, diffuseColor.rgb * 1.35 + 0.04, smoothstep(0.7, 1.0, uK) * 0.35); }`); };
    m.customProgramCacheKey = () => 'bearfur' + k; return m; };
  const base = new THREE.SkinnedMesh(geo, furMat(0)); base.add(rootB); base.bind(skel); base.castShadow = true; base.receiveShadow = true; base.frustumCulled = false; BEAR.add(base);
  for (let s = 1; s <= NSH; s++) { const m = new THREE.SkinnedMesh(geo, furMat(s / NSH)); m.bind(skel, base.matrixWorld); m.frustumCulled = false; m.receiveShadow = true; BEAR.add(m); U['shell' + s] = m; }
  // nose leather, eyes, claws (on the bones)
  const att = (b, mesh, w) => { mesh.position.set(w[0] - b.userData.w[0], w[1] - b.userData.w[1], w[2] - b.userData.w[2]); b.add(mesh); return mesh; };
  { const n = new THREE.Mesh(new THREE.SphereGeometry(1, 20, 14), mat(0x141110, 0.35)); n.scale.set(0.058, 0.04, 0.035); att(head, n, [0, 0.858, -1.475]); }
  for (const s of [-1, 1]) { const e = new THREE.Mesh(new THREE.SphereGeometry(0.024, 14, 10), new THREE.MeshStandardMaterial({ color: 0x0a0706, roughness: 0.1, metalness: 0.2 })); att(head, e, [0.092 * s, 0.982, -1.305]); }
  LL.forEach((L, s) => { for (let c = -2; c <= 2; c++) { const cl = new THREE.Mesh(new THREE.ConeGeometry(0.013, 0.11, 6).rotateX(-Math.PI / 2 - 0.35), mat(0xcfc3a5, 0.45)); att(legsB[s].wr, cl, [L.wr[0] + c * 0.042, 0.035, -0.75 + Math.abs(c) * 0.02]); } });
  U.spine = spine; U.neck = neck; U.head = head; U.legs = legsB; U.rest = {}; rootB.traverse(b => { U.rest[b.uuid] = b.position.clone(); }); }
// pose the bear: position, heading, gait phase (radians) and stride (0 = standing, 1 = full gallop), head pitch, mouth (unused: the jaw stays closed), sniff
function setBear(p, yaw, ph = 0, amp = 0, headP = 0, mouth = 0, sniff = 0) { const U = BEAR.userData; BEAR.visible = true; BEAR.position.copy(p); BEAR.rotation.set(0, yaw, 0);
  U.spine.position.y = U.rest[U.spine.uuid].y + 0.06 * amp * Math.abs(Math.sin(ph)); U.spine.rotation.x = 0.07 * amp * Math.sin(ph + 1);
  U.legs.forEach((L, s) => { for (const [up, lo, ft, front, off] of [[L.sh, L.el, L.wr, 1, s ? 0.4 : 0], [L.hp, L.kn, L.an, 0, s ? Math.PI + 0.4 : Math.PI]]) {
    const a = 0.7 * amp * Math.sin(ph + off), b = (front ? 0.9 : -0.8) * amp * Math.max(0, Math.sin(ph + off + 1.2)); up.rotation.x = a; lo.rotation.x = b; ft.rotation.x = -(a + b) * 0.7; } });
  U.neck.rotation.x = 0.5 * headP + 0.12; U.head.rotation.x = 0.5 * headP + 0.08 * amp * Math.sin(ph * 2) + sniff * 0.15 * Math.sin(ph * 3); U.head.rotation.y = sniff * 0.3 * Math.sin(ph * 0.8); }
// ---- the hikers: rain jackets (shirt recoloured, arm skin painted as sleeves to the wrist), jeans, boots; a backpack; bear spray
const K = await loadGuy(THREE, '/char/' + (Q.get('char') || window.CHARDEF || 'guy'), { fingers3: !!window.FINGERS3 }); scene.add(K.root); K.root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
const RK = makeRig(K, 'hiker2');
function jacket(Gx, hex) { const lin = new THREE.Color(hex);
  const sh = Gx.meshes.shirt; if (sh) { sh.material = sh.material.clone(); sh.material.map = null; sh.material.color.set(hex); sh.material.roughness = 0.6; sh.material.needsUpdate = true; }
  for (const n of ['shoeR', 'shoeL']) { const m = Gx.meshes[n]; if (!m) continue; m.material = m.material.clone(); m.material.map = null; m.material.color.set(0x3a2a1c); m.material.roughness = 0.6; m.material.needsUpdate = true; }
  const sk = Gx.meshes.skin_head, ga = sk.geometry.attributes, names = sk.skeleton.bones.map(b => b.name), a = new Float32Array(ga.position.count * 2);
  Gx.reset(); Gx.root.updateMatrixWorld(true); const WR = {}; for (const S of ['R', 'L']) { const wr = wp(Gx.bones['hand' + S]), el = wp(Gx.bones['farm' + S]); WR[S] = { wr, d: wr.clone().sub(el).normalize() }; }
  const _p = V(0, 0, 0);
  for (let i = 0; i < ga.position.count; i++) { let arm = 0, side = null; for (let k = 0; k < 4; k++) { const w = ga.skinWeight.getComponent(i, k), n = names[ga.skinIndex.getComponent(i, k)];
      if (/^(uarm|uarmTwist|farm|farmTwist)/.test(n)) { arm += w; side = n.slice(-1); } }
    let sl = 0; if (arm > 0.3 && side && WR[side]) { _p.set(ga.position.getX(i), ga.position.getY(i), ga.position.getZ(i)).applyMatrix4(sk.matrixWorld); sl = clamp((-_p.clone().sub(WR[side].wr).dot(WR[side].d) - 0.02) / 0.02, 0, 1); }
    a[i * 2] = sl; }
  sk.geometry.setAttribute('aSuit', new THREE.BufferAttribute(a, 2));
  const m = sk.material = sk.material.clone(), old = m.onBeforeCompile, oldKey = m.customProgramCacheKey ? m.customProgramCacheKey.bind(m) : () => '';
  m.onBeforeCompile = (s, r) => { if (old) old.call(m, s, r);
    s.vertexShader = 'attribute vec2 aSuit; varying vec2 vSuit;\n' + s.vertexShader.replace('#include <begin_vertex>', '#include <begin_vertex>\n vSuit = aSuit;');
    s.fragmentShader = 'varying vec2 vSuit;\n' + s.fragmentShader.replace('#include <map_fragment>', `#include <map_fragment>
      diffuseColor.rgb = mix(diffuseColor.rgb, vec3(${lin.r.toFixed(4)}, ${lin.g.toFixed(4)}, ${lin.b.toFixed(4)}), smoothstep(0.45, 0.55, vSuit.x));`)
      .replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\n roughnessFactor = mix(roughnessFactor, 0.6, smoothstep(0.45, 0.55, vSuit.x));'); };
  m.customProgramCacheKey = () => oldKey() + '|jacket' + hex; m.needsUpdate = true; }
jacket(G, 0x9a2d22); jacket(K, 0x2c5a44);
function makePack(c) { const p = new THREE.Group(); scene.add(p); box(0.36, 0.48, 0.2, 0, 0, 0, mat(c, 0.8), 0.06, p).castShadow = true; box(0.3, 0.2, 0.06, 0, -0.08, 0.12, mat(new THREE.Color(c).multiplyScalar(0.7), 0.8), 0.03, p);
  for (const s of [-1, 1]) box(0.05, 0.4, 0.04, s * 0.12, 0.02, -0.12, mat(0x222222, 0.8), 0.01, p); return p; }
const PACKG = makePack(0x37474f), PACKK = makePack(0x6a4a2a);
function placePack(pk, Gx) { const ch = wp(Gx.bones.chest), q = Gx.root.quaternion; pk.position.copy(ch).add(V(0, -0.1, 0.19).applyQuaternion(q)); pk.quaternion.copy(q); pk.visible = true; }
function makeSpray() { const s = new THREE.Group(); scene.add(s); const c = new THREE.Mesh(new THREE.CylinderGeometry(0.032, 0.032, 0.2, 16), mat(0xe8641c, 0.5)); s.add(c);
  box(0.05, 0.05, 0.05, 0, 0.12, 0, mat(0x1b1b1b, 0.5), 0.01, s); box(0.02, 0.025, 0.04, 0, 0.12, -0.04, mat(0x1b1b1b, 0.5), 0, s); box(0.012, 0.05, 0.03, 0, 0.07, -0.05, mat(0x1b1b1b, 0.5), 0, s); return s; }
const SPRAYG = makeSpray(), SPRAYK = makeSpray();
// the spray can in the right hand, nozzle along the forearm; or on the hip belt
function sprayInHand(sp, Gx) { const h = wp(Gx.bones.handR), f = wp(Gx.bones.farmR), d = h.clone().sub(f).normalize(); sp.position.copy(h).addScaledVector(d, 0.05);
  sp.quaternion.setFromUnitVectors(V(0, 1, 0), d); sp.visible = true; return { p: h.clone().addScaledVector(d, 0.18), d }; }
function sprayOnHip(sp, Gx) { const q = Gx.root.quaternion, hp = wp(Gx.bones.thighR || Gx.bones.hips); sp.position.copy(hp).add(V(0.12, 0.08, 0).applyQuaternion(q)); sp.quaternion.copy(q); sp.visible = true; }
// the pepper cloud: soft orange puffs from the nozzle
const cloudTex = canvasTex(128, 128, g => { const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64); gr.addColorStop(0, 'rgba(255,150,60,0.9)'); gr.addColorStop(0.5, 'rgba(240,120,50,0.45)'); gr.addColorStop(1, 'rgba(230,110,40,0)'); g.fillStyle = gr; g.fillRect(0, 0, 128, 128); });
const CLOUD = []; for (let i = 0; i < 40; i++) { const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: cloudTex, transparent: true, depthWrite: false })); s.visible = false; scene.add(s); CLOUD.push(s); }
// the closed trail: a sign, tape, and a culvert bear trap on its trailer
const signM = new THREE.MeshBasicMaterial({ map: canvasTex(512, 300, g => { g.fillStyle = '#f2c21a'; g.fillRect(0, 0, 512, 300); g.fillStyle = '#111'; g.fillRect(14, 14, 484, 272); g.fillStyle = '#f2c21a'; g.fillRect(24, 24, 464, 252); g.fillStyle = '#111'; g.font = 'bold 92px Arial'; g.textAlign = 'center'; g.fillText('AREA', 256, 128); g.fillText('CLOSED', 256, 228); }), toneMapped: false });
const SIGN = new THREE.Group(); { const b = new THREE.Mesh(new THREE.PlaneGeometry(1.1, 0.65), signM); b.position.y = 1.35; SIGN.add(b); for (const s of [-1, 1]) box(0.07, 1.4, 0.07, s * 0.45, 0.7, -0.03, mat(0x6b5a44, 0.9), 0, SIGN); } scene.add(SIGN);
const TAPE = new THREE.Mesh(new THREE.BoxGeometry(5, 0.07, 0.01), new THREE.MeshBasicMaterial({ color: 0xf2c21a, toneMapped: false })); scene.add(TAPE);
const TRAP = new THREE.Group(); { const tm = mat(0xaab0b6, 0.4, 0.7); const c = new THREE.Mesh(new THREE.CylinderGeometry(0.65, 0.65, 2.6, 24, 1, true).rotateX(Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0xaab0b6, roughness: 0.45, metalness: 0.7, side: THREE.DoubleSide })); c.position.y = 1.15; c.castShadow = true; TRAP.add(c);
  const end = new THREE.Mesh(new THREE.CircleGeometry(0.65, 24), tm); end.position.set(0, 1.15, 1.3); TRAP.add(end); box(0.06, 1.4, 0.06, 0, 1.15, -1.32, mat(0x555a60, 0.5, 0.6), 0, TRAP); for (let i = 0; i < 9; i++) { const h = new THREE.Mesh(new THREE.CircleGeometry(0.05, 10), mat(0x111111, 0.8)); h.position.set(0.651, 1.0 + 0.3 * (i % 3), -0.9 + 0.45 * Math.floor(i / 3)); h.rotation.y = Math.PI / 2; TRAP.add(h); }
  for (const s of [-1, 1]) { const w = new THREE.Mesh(new THREE.CylinderGeometry(0.33, 0.33, 0.2, 18).rotateZ(Math.PI / 2), mat(0x1b1b1b, 0.8)); w.position.set(s * 0.78, 0.33, 0.3); TRAP.add(w); }
  box(0.08, 0.08, 1.4, 0, 0.45, -1.8, mat(0x555a60, 0.5, 0.6), 0, TRAP); } scene.add(TRAP);
// arrows and the readout
function arrowMesh(color) { const s = new THREE.Shape(); s.moveTo(-0.05, -0.32); s.lineTo(0.05, -0.32); s.lineTo(0.05, 0.08); s.lineTo(0.13, 0.08); s.lineTo(0, 0.25); s.lineTo(-0.13, 0.08); s.lineTo(-0.05, 0.08); s.closePath();
  const m = new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth: 0.04, bevelEnabled: false }), new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.92, depthTest: false, toneMapped: false })); m.renderOrder = 25; m.visible = false; scene.add(m); return m; }
const ARS = [arrowMesh(0xff4a3a), arrowMesh(0xff4a3a), arrowMesh(0x3ad27a), arrowMesh(0x3ad27a)];
const XM = new THREE.Sprite(new THREE.SpriteMaterial({ map: canvasTex(256, 256, g => { g.strokeStyle = '#ff3b2e'; g.lineWidth = 34; g.lineCap = 'round'; g.beginPath(); g.moveTo(50, 50); g.lineTo(206, 206); g.moveTo(206, 50); g.lineTo(50, 206); g.stroke(); }), depthTest: false, toneMapped: false })); XM.renderOrder = 26; XM.visible = false; scene.add(XM);
const hudC = document.createElement('canvas'); hudC.width = 520; hudC.height = 440; const hudT = new THREE.CanvasTexture(hudC); hudT.colorSpace = THREE.SRGBColorSpace;
const hud = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: hudT, transparent: true, depthTest: false, depthWrite: false, toneMapped: false })); hud.renderOrder = 30; camera.add(hud); scene.add(camera); hud.visible = false;
function drawHud(rows, flag, fcol = '#d9241b') { const g = hudC.getContext('2d'); g.clearRect(0, 0, 520, 440); g.beginPath(); g.roundRect(6, 6, 508, 428, 34); g.fillStyle = 'rgba(8,14,22,0.74)'; g.fill(); g.lineWidth = 4; g.strokeStyle = 'rgba(160,200,235,0.55)'; g.stroke();
  let y = 30; for (const [lab, val, col] of rows) { g.fillStyle = '#9fb6c8'; g.font = '600 34px Arial, Helvetica, sans-serif'; g.fillText(lab, 34, y + 38); g.fillStyle = col || '#fff'; g.font = 'bold 62px Arial, Helvetica, sans-serif'; g.fillText(val, 34, y + 102, 452); y += 120; }
  if (flag) { g.font = 'bold 52px Arial, Helvetica, sans-serif'; const fw = Math.min(460, g.measureText(flag).width + 40); g.beginPath(); g.roundRect(30, 340, fw, 76, 16); g.fillStyle = fcol; g.fill(); g.fillStyle = '#fff'; g.fillText(flag, 50, 397, fw - 40); }
  hudT.needsUpdate = true; }
function fitHud() { const d = camera.near * 1.6, h = 2 * d * Math.tan(camera.fov * D2R / 2), w = h * camera.aspect, gw = 0.4 * w, gh = gw * 440 / 520; hud.scale.set(gw, gh, 1); hud.position.set(w / 2 - gw / 2 - 0.035 * w, h / 2 - 0.165 * h - gh / 2, -d); }
// ------------------------------------------------------------------ story: one shot per line (yaw 0 faces -z for the hikers and the bear)
const CALM = curl(curl({ ...STAND, armR: A(22, 28, 0, 25), armL: A(22, 28, 0, 25), neck: [4, 0, 0] }, 'R', 20), 'L', 20);
const SPRAYP = curl(curl({ ...STAND, spine1: [-4, 0, 0], armR: A(82, 6, 0, 8), armL: A(30, 20, 0, 60), neck: [2, 0, 0] }, 'R', 85), 'L', 30);
const PRONE = curl(curl({ ...STAND, thighR: [0, 0, 22], thighL: [0, 0, -22], neck: [20, 0, 0], armR: A(120, 85, 0, 160), armL: A(120, 85, 0, 160) }, 'R', 40), 'L', 40);
const LOOKP = curl(curl({ ...STAND, armR: A(8, 10, 0, 15), armL: A(8, 10, 0, 15), neck: [-4, 0, 0] }, 'R', 25), 'L', 25);
const ST = (x, z, yaw = 0) => ({ x, y: 0.95, z, yaw });   // root yaw is in DEGREES; 0 faces up the trail (-z), toward the bear
function clouds(nozzle, d, age0, on, fade = 1) { CLOUD.forEach((s, i) => { const age = age0 - i * 0.025; s.visible = on && age > 0 && age < 2.2; if (!s.visible) return; const k = Math.min(age, 0.7);
    s.position.copy(nozzle).addScaledVector(d, 9 * k - 5 * k * k).add(V(0.4 * (hash1(i) - 0.5) * age * 2, 0.25 * age + 0.3 * (hash1(i + 5) - 0.5) * age, 0.4 * (hash1(i + 9) - 0.5) * age * 2));
    s.scale.setScalar(0.1 + 1.25 * Math.sqrt(age)); s.material.opacity = 0.85 * (1 - age / 2.2) * fade; }); }
function shot(t) { const nb = beatAt(t), lt = t - B[nb], dur = DUR[nb], u = lt / dur;
  hud.visible = false; for (const o of [...ARS, XM, SIGN, TAPE, TRAP, PACKG, PACKK, SPRAYG, SPRAYK, ...CLOUD]) o.visible = false; BEAR.visible = false; G.root.visible = K.root.visible = false;
  SKYU.uSet.value = 0; scene.background.set(0xaabccb); scene.fog.color.set(0xb2c0cb); scene.fog.near = 60; scene.fog.far = 1500; sun.color.set(0xfff0dc); sun.intensity = 1.6; hemi.intensity = 1.1;
  let cp, ct, up = V(0, 1, 0), fov = 42, near = 0.05, gp = null, gr = null, kp = null, kr = null; const ARR = []; camera.far = 6000;
  switch (nb) {
    case 0: { // hook: a grizzly charging straight down the trail at the camera
      const z = -24 + 5.6 * lt; setBear(V(trailX(z), 0, z), Math.PI, lt * 9.5, 1, -0.1, 0.4); cp = V(0.35, 0.55, 0.8); ct = V(trailX(z), 0.95, z); fov = 40;
      hud.visible = true; drawHud([['GRIZZLY', 'CHARGING', '#ffd23a']]); break; }
    case 1: { // the Bella Coola valley from the air: river, forest, steep mountains
      cp = V(220 - 40 * u, 380 - 30 * u, 700 - 120 * u); ct = V(-260, 60, -700); fov = 50; near = 1; scene.fog.near = 2500; scene.fog.far = 9000;
      hud.visible = true; drawHud([['OCT 31, 2026', 'BELLA COOLA'], ['WHERE', 'B.C., CANADA']]); break; }
    case 2: { // the trail: a short walk from home, quiet, empty
      const z = 34 - 2.2 * lt; cp = V(trailX(z) + 0.15, 1.6, z); ct = V(trailX(z - 12), 1.3, z - 12); fov = 50;
      hud.visible = true; drawHud([['FROM HOME', '5 MINUTES', '#ffd23a']]); break; }
    case 3: { // closed: the sign, tape across the trail, a culvert trap set for the bear
      SIGN.visible = TAPE.visible = TRAP.visible = true; SIGN.position.set(trailX(20) + 1.6, 0, 20.4); SIGN.rotation.y = 0.15; TAPE.position.set(trailX(19.6), 1.0, 19.6); TRAP.position.set(trailX(13) + 4.2, 0, 13); TRAP.rotation.y = 0.5;
      cp = V(trailX(29) + 0.9 - 0.3 * u, 1.55, 29 - 1.2 * u); ct = V(trailX(17) + 1.6, 1.0, 17); fov = 44;
      hud.visible = true; drawHud([['THE BEAR', 'NOT CAUGHT YET', '#ff6a5c']], 'TRAPS SET', '#2a5a8a'); break; }
    case 4: { // a hiker on the trail; a grizzly ahead, up on its toes, looking at him
      gp = LOOKP; gr = ST(0, 0); setBear(V(trailX(-22), 0, -22), Math.PI, t * 1.5, 0.05, -0.25 + 0.1 * Math.sin(t * 2), 0, 0.6); cp = V(0.75, 1.8, 2.4); ct = V(trailX(-22) - 0.6, 1.0, -22); fov = 36;
      hud.visible = true; drawHud([['GRIZZLY', '70 FT AWAY', '#ffd23a']]); break; }
    case 5: { // don't run: it's as fast as a racehorse (it sprints across behind him; he stays put)
      gp = CALM; gr = ST(0, 0); const x = -30 + 15 * lt; setBear(V(x, 0, -9), -Math.PI / 2, lt * 11, 1, -0.05); cp = V(2.6, 1.55, 4.6); ct = V(0, 1.1, -5); fov = 50;
      hud.visible = true; drawHud([['TOP SPEED', 'ABOUT 35 MPH', '#ffd23a']], "DON'T RUN"); break; }
    case 6: { // the bluff charge: it rushes in, stops short, and swings away; he stands still, hands low, talking
      gp = CALM; gr = ST(0, 0); const k = sm(clamp(u / 0.6, 0, 1)), z = -22 + 16.5 * k, amp = 1 - smooth(0.45, 0.62, u), turn = smooth(0.7, 1, u);
      setBear(V(trailX(z) + 2.5 * turn, 0, z - 1.2 * turn), Math.PI + 1.6 * turn, lt * 9.5, Math.max(amp, 0.35 * turn), -0.1 + 0.25 * (1 - amp) * (1 - turn), 0.3 * (1 - amp)); cp = V(1.2, 1.6, 3.6); ct = V(0, 1.0, -5); fov = 48;
      hud.visible = true; drawHud([['MOST CHARGES', 'ARE BLUFFS', '#ffd23a']], 'STAND STILL', '#2f7d4a'); break; }
    case 7: { // bear spray: aimed at its face; the cloud stops it
      gp = SPRAYP; gr = ST(0, 0); const z = -13 + 6.5 * sm(clamp(u / 0.55, 0, 1)), stop = smooth(0.55, 0.8, u);
      setBear(V(trailX(z), 0, z), Math.PI + 0.5 * stop, lt * 6, 0.55 * (1 - stop), -0.1 + 0.35 * stop, 0.2, stop); cp = V(1.2, 1.65, 3.4); ct = V(0, 1.0, -5); fov = 46;
      hud.visible = true; drawHud([['BEAR SPRAY', 'AT ITS FACE', '#ff8a3a']]); break; }
    case 8: { // it turns and runs off into the trees; the cloud hangs
      gp = SPRAYP; gr = ST(0, 0); const k = sm(clamp(u / 0.35, 0, 1)), z = -6.5 - 22 * smooth(0.2, 1, u); setBear(V(trailX(z) + 2.5 * k, 0, z), Math.PI + Math.PI * k, lt * 9, 0.4 + 0.6 * k, 0.1); cp = V(-1.3, 1.8, 3.8); ct = V(0.3, 1.0, -8); fov = 48;
      hud.visible = true; drawHud([['STOPPED GRIZZLIES', '9 IN 10', '#2fbf71']], 'ONE BIG STUDY', '#2a5a8a'); break; }
    case 9: { // play dead: flat on the stomach, pack on, hands behind the neck; the bear stands over, sniffing (it never touches him on screen)
      gp = PRONE; gr = { x: 0, y: 0.17, z: 0, yaw: 0, tilt: -90 }; setBear(V(1.9, 0, -1.6), Math.PI / 2 + 0.6, t * 2, 0.05, 0.35, 0, 1); cp = V(5.6 - 0.4 * u, 3.3, 1.8 - 0.3 * u); ct = V(0.7, 0.5, -0.9); fov = 46;
      hud.visible = true; drawHud([['PLAY DEAD', 'ON YOUR STOMACH', '#ffd23a'], ['KEEP ON', 'PACK + HANDS ON NECK']]); break; }
    case 10: { // from above: legs spread so it can't flip him; still until it leaves
      gp = PRONE; gr = { x: 0, y: 0.17, z: 0, yaw: 0, tilt: -90 }; const z = -2.5 - 9 * smooth(0.15, 1, u); setBear(V(2.2, 0, z), 0, lt * 6, 0.6, 0.05); cp = V(0.01, 6.8, 0.7); ct = V(0, 0, 0.7); up = V(0, 0, -1); fov = 46;
      hud.visible = true; drawHud([['LEGS', 'SPREAD WIDE', '#2fbf71']], 'STAY STILL', '#2f7d4a'); break; }
    case 11: { // still attacking? fight back, hit the face (the bear alone, close up)
      setBear(V(0, 0, -4.2), Math.PI, t * 3, 0.1, -0.15 + 0.08 * Math.sin(t * 4), 0.5 + 0.3 * Math.sin(t * 5)); cp = V(1.1, 1.35, 0.6); ct = V(0, 0.95, -3.0); fov = 36;
      BEAR.updateMatrixWorld(true); const hp = V(0, 0, 0).applyMatrix4(BEAR.userData.head.matrixWorld); ARR.push([ARS[0], hp.clone().add(V(-0.75, 0.05, 0.2)), 0.8, -Math.PI / 2], [ARS[1], hp.clone().add(V(0.75, 0.05, 0.2)), 0.8, Math.PI / 2]);
      hud.visible = true; drawHud([['STILL ATTACKING?', 'FIGHT BACK', '#ff6a5c']], 'HIT THE FACE'); break; }
    case 12: { // walk in groups, make noise, spray on the hip
      gp = LOOKP; gr = ST(trailX(-1) - 0.45, -1, 180); kp = LOOKP; kr = ST(trailX(-1) + 0.5, -1.4, 180); cp = V(0.3, 1.55, 4.8 - 0.8 * u); ct = V(0, 1.25, -1); fov = 44;
      hud.visible = true; drawHud([['HIKE IN', 'GROUPS', '#2fbf71'], ['MAKE', 'NOISE', '#2fbf71']], 'SPRAY ON YOUR HIP', '#2f7d4a'); break; }
    case 13: { // dusk on the empty trail
      SKYU.uSet.value = 1; scene.background.set(0xc98a6a); scene.fog.color.set(0x9a7a72); sun.color.set(0xff9a5a); sun.intensity = 0.7; hemi.intensity = 0.55;
      cp = V(trailX(10) + 0.2, 1.2, 10 - 1.5 * u); ct = V(trailX(-20), 3.0, -20); fov = 48; break; }
  }
  if (gp) { G.root.visible = true; RG.applyPose(gp, gr); G.root.updateMatrixWorld(true); placePack(PACKG, G); }
  if (kp) { K.root.visible = true; RK.applyPose(kp, kr); K.root.updateMatrixWorld(true); placePack(PACKK, K); sprayOnHip(SPRAYK, K); }
  if (gp === SPRAYP) { const s = sprayInHand(SPRAYG, G); clouds(s.p, s.d, nb === 7 ? lt - 0.35 * dur : lt + DUR[7] * 0.65, true, nb === 8 ? 1 - u : 1); }
  else if (gp && nb !== 9 && nb !== 10) sprayOnHip(SPRAYG, G);
  SKY.position.copy(cp); camera.position.copy(cp); camera.up.copy(up); camera.lookAt(ct); camera.fov = fov; camera.near = near; camera.updateProjectionMatrix();
  for (const [a, p, s, rz] of ARR) { a.visible = true; a.position.copy(p); a.quaternion.copy(camera.quaternion).multiply(new THREE.Quaternion().setFromAxisAngle(V(0, 0, 1), rz)); a.scale.setScalar(s); }
  if (nb === 10) { for (const [a, s] of [[ARS[2], 1], [ARS[3], -1]]) { a.visible = true; const ft = wp(G.bones['foot' + (s > 0 ? 'R' : 'L')] || G.bones.hips); a.position.copy(ft).add(V(0.35 * s, 0.3, 0)); a.quaternion.copy(camera.quaternion).multiply(new THREE.Quaternion().setFromAxisAngle(V(0, 0, 1), -s * Math.PI / 2)); a.scale.setScalar(0.8); } }
  return { b: nb, focus: ct }; }
// ------------------------------------------------------------------ look + frame I/O
import { makeLook } from '/look.js';
const LOOK = makeLook(THREE, renderer, scene, camera, W, H, { overlays: [hud, ...ARS, XM], aperture: 0.0005, maxblur: 0.005, rim: false, noAO: [window.__SKY, ...CLOUD] });
let FOC = V(0, 1, 0), WIDE = false;
function update(t) { t = clamp(t, 0, TOTAL - 1e-3); const r = shot(t); fitHud();
  const at = r.focus; sun.position.copy(at).add(V(25, 50, 20)); sun.target.position.copy(at); sun.target.updateMatrixWorld(); FOC = r.focus; WIDE = [1].includes(r.b); return r; }
function stepTo(i) { return update(i / FPS); }
const draw = () => LOOK.render(FOC, { ao: !WIDE, dof: !WIDE });
const gl = renderer.getContext(), px = new Uint8Array(W * H * 4);
window.renderAll = async (f0, f1) => { for (let i = f0; i < f1; i++) { stepTo(i); draw(); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); await fetch('/frame', { method: 'POST', body: px }); } return 'ok'; };
window.renderAtT = t => { stepTo(Math.round(t * FPS)); draw(); return renderer.domElement.toDataURL('image/png'); };
window.dbg = { THREE, scene, camera, G, K, shot, BEAR, setBear };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS); window.READY = true;
window.SCN = { THREE, scene, camera, stepTo, renderer, FPS, B, DUR, TOTAL };
