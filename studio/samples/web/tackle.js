// Jesus de Miguel (CD Tenerife), Nov 2, 2026: the collision with Andorra's keeper in stoppage time, and what happened after. Stand-in figures, generic kits, no crests.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { loadGuy } from '/guy3d.js';

const Q = new URLSearchParams(location.search);
const W = +Q.get('w') || 720, H = +Q.get('h') || 1280;
const FPS = 30;
const TIMES = await (await fetch('/tackle/times.json')).json();
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
// ================================================================== A COLLISION ON THE PITCH
// ------------------------------------------------------------------ set: a floodlit stadium at night, two stand-in players (no crests, no likenesses)
home.visible = false; lamp.visible = false;
scene.background = new THREE.Color(0x05080f); scene.environmentIntensity = 0.25; scene.fog = new THREE.Fog(0x0a0f1a, 120, 420);
hemi.color.set(0x8fa4c8); hemi.groundColor.set(0x1c2a14); hemi.intensity = 0.55;
sun.color.set(0xf4f6ff); sun.intensity = 3.2; sun.position.set(30, 60, 20);
{ const S = sun.shadow.camera; S.left = -14; S.right = 14; S.top = 14; S.bottom = -14; S.near = 1; S.far = 160; S.updateProjectionMatrix(); }
// the pitch: mown stripes, white lines (penalty box at the -z end), a goal
const PW = 68, PL = 105, GOALZ = -PL / 2;
const pitchTex = canvasTex(1024, 2048, g => { for (let i = 0; i < 20; i++) { g.fillStyle = i % 2 ? '#2f6f2c' : '#367a31'; g.fillRect(0, i * 2048 / 20, 1024, 2048 / 20 + 1); }
  for (let k = 0; k < 9000; k++) { g.fillStyle = `rgba(${20 + 30 * Math.random()},${60 + 50 * Math.random()},${20 + 20 * Math.random()},0.25)`; g.fillRect(Math.random() * 1024, Math.random() * 2048, 2, 3); }
  const X = x => (x / PW + 0.5) * 1024, Z = z => (z / PL + 0.5) * 2048; g.strokeStyle = 'rgba(245,245,240,0.92)'; g.lineWidth = 0.12 / PW * 1024 * 1.6;
  g.strokeRect(X(-PW / 2 + 0.5), Z(-PL / 2 + 0.5), X(PW / 2 - 0.5) - X(-PW / 2 + 0.5), Z(PL / 2 - 0.5) - Z(-PL / 2 + 0.5));
  g.beginPath(); g.moveTo(X(-PW / 2), Z(0)); g.lineTo(X(PW / 2), Z(0)); g.stroke(); g.beginPath(); g.arc(X(0), Z(0), 9.15 / PW * 1024, 0, 7); g.stroke();
  for (const sz of [-1, 1]) { const e = sz * (PL / 2 - 0.5); g.strokeRect(X(-20.16), sz < 0 ? Z(e) : Z(e - 16.5), X(20.16) - X(-20.16), Z(16.5) - Z(0)); g.strokeRect(X(-9.16), sz < 0 ? Z(e) : Z(e - 5.5), X(9.16) - X(-9.16), Z(5.5) - Z(0));
    g.beginPath(); g.arc(X(0), Z(e - sz * 11), 3, 0, 7); g.fillStyle = '#fff'; g.fill(); } });
const pitch = new THREE.Mesh(new THREE.PlaneGeometry(PW + 8, PL + 8).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ map: pitchTex, roughness: 0.92 }));
pitch.receiveShadow = true; scene.add(pitch); pitchTex.repeat.set(1, 1);
{ const surround = new THREE.Mesh(new THREE.PlaneGeometry(PW + 40, PL + 40).rotateX(-Math.PI / 2), mat(0x24452a, 0.95)); surround.position.y = -0.01; scene.add(surround); }
const goal = new THREE.Group(); goal.position.set(0, 0, GOALZ + 0.5); scene.add(goal);
{ const pm = mat(0xf4f4f0, 0.35); const post = (x) => { const p = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 2.44, 12), pm); p.position.set(x, 1.22, 0); p.castShadow = true; goal.add(p); };
  post(-3.66); post(3.66); const bar = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 7.44, 12).rotateZ(Math.PI / 2), pm); bar.position.set(0, 2.44, 0); goal.add(bar);
  const net = new THREE.Mesh(new THREE.BoxGeometry(7.32, 2.44, 2.0), new THREE.MeshBasicMaterial({ color: 0xe8e8e8, wireframe: true, transparent: true, opacity: 0.25 })); net.position.set(0, 1.22, -1.0); goal.add(net); }
// stands with a crowd (instanced), four floodlight towers
const stands = new THREE.Group(); scene.add(stands);   // rows step outward from the touchline (they were pulled into the pitch once)
{ const sm = mat(0x1b1f28, 0.9); const crowd = []; const add = (w, d, x, z, ry) => { for (let r = 0; r < 14; r++) { const st = box(w, 0.5, 0.9, 0, 0.6 + r * 0.55, 0, sm, 0, stands); st.position.set(x, 0.6 + r * 0.55, z); st.rotation.y = ry;
      const dir = V(Math.sin(ry), 0, Math.cos(ry)); st.position.addScaledVector(dir, r * 0.85); for (let k = 0; k < w; k += 0.55) crowd.push(st.position.clone().add(V(Math.cos(ry), 0, -Math.sin(ry)).multiplyScalar(k - w / 2)).add(V(0, 0.45, 0))); } };
  add(PL + 10, 0, PW / 2 + 7, 0, Math.PI / 2); add(PL + 10, 0, -PW / 2 - 7, 0, -Math.PI / 2); add(PW + 10, 0, 0, -PL / 2 - 7, Math.PI); add(PW + 10, 0, 0, PL / 2 + 7, 0);
  const cm = new THREE.InstancedMesh(new THREE.BoxGeometry(0.42, 0.55, 0.3), new THREE.MeshStandardMaterial({ roughness: 0.8 }), crowd.length); const m4 = new THREE.Matrix4();
  crowd.forEach((p, i) => { m4.makeTranslation(p.x, p.y, p.z); cm.setMatrixAt(i, m4); cm.setColorAt(i, new THREE.Color().setHSL(hash1(i * 1.3), 0.4 * hash1(i * 2.1), 0.15 + 0.35 * hash1(i * 3.7))); }); stands.add(cm); }
for (const [x, z] of [[-48, -66], [48, -66], [-48, 66], [48, 66]]) { const t = box(1.2, 42, 1.2, x, 21, z, mat(0x2a2e36, 0.6, 0.4), 0, scene);
  const panel = new THREE.Mesh(new THREE.PlaneGeometry(9, 4), new THREE.MeshBasicMaterial({ color: 0xffffff, toneMapped: false })); panel.position.set(x * 0.97, 43, z * 0.97); panel.lookAt(0, 0, 0); scene.add(panel);
  const glow = new THREE.Sprite(new THREE.SpriteMaterial({ map: canvasTex(128, 128, g => { const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64); gr.addColorStop(0, 'rgba(255,255,255,0.9)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 128, 128); }), transparent: true, depthWrite: false, toneMapped: false }));
  glow.scale.set(14, 14, 1); glow.position.copy(panel.position); scene.add(glow); }
for (const [x, z] of [[-40, -55], [40, -55], [-40, 55], [40, 55]]) { const fl = new THREE.SpotLight(0xf2f5ff, 900, 160, 0.8, 0.5, 1.4); fl.position.set(x, 40, z); fl.target.position.set(0, 0, z * 0.3); scene.add(fl, fl.target); }
// the ball
const ball = new THREE.Mesh(new THREE.IcosahedronGeometry(0.11, 2), new THREE.MeshStandardMaterial({ map: canvasTex(256, 128, g => { g.fillStyle = '#f6f6f2'; g.fillRect(0, 0, 256, 128); g.fillStyle = '#1c1c22'; for (let r = 0; r < 4; r++) for (let c = 0; c < 8; c++) { const x = c * 32 + (r % 2) * 16 + 8, y = r * 32 + 16; g.beginPath(); for (let k = 0; k < 5; k++) { const a = k / 5 * Math.PI * 2 - Math.PI / 2; g.lineTo(x + Math.cos(a) * 7, y + Math.sin(a) * 7); } g.fill(); } }), roughness: 0.5, flatShading: false }));
ball.castShadow = true; scene.add(ball);
// kits: the forward in white, the keeper in green with black trousers (both generic)
function kit(Gx, shirt, pants) { for (const [n, c] of [['shirt', shirt], ['jeans', pants]]) { const m = Gx.meshes[n]; if (!m) continue; m.material = m.material.clone(); m.material.map = null; m.material.color.set(c); m.material.roughness = 0.75; m.material.needsUpdate = true; }
  for (const n of ['shoeR', 'shoeL']) { const m = Gx.meshes[n]; if (!m) continue; m.material = m.material.clone(); m.material.map = null; m.material.color.set(0x15161a); m.material.needsUpdate = true; } }
// kits: Tenerife white shirt + blue shorts; the Andorra keeper wore black (match photos)
kit(G, 0xf6f6f2, 0x1f3f9a);
const K = await loadGuy(THREE, '/char/' + (Q.get('char') || window.CHARDEF || 'guy'), { fingers3: !!window.FINGERS3 }); scene.add(K.root); K.root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
kit(K, 0x17181b, 0x0e0f11); const RK = makeRig(K, 'keeper');
// the red card, the ambulance, the hospital (outside the stadium, along +x)
const card = new THREE.Mesh(new THREE.PlaneGeometry(0.075, 0.11), new THREE.MeshStandardMaterial({ color: 0xe0161c, emissive: 0x500000, side: THREE.DoubleSide, roughness: 0.4 })); card.scale.setScalar(6); card.visible = false; scene.add(card);
const out = new THREE.Group(); out.position.set(260, 0, 0); scene.add(out); out.visible = false;
{ const road = new THREE.Mesh(new THREE.PlaneGeometry(14, 600).rotateX(-Math.PI / 2), mat(0x24262b, 0.85)); road.position.y = 0.02; road.receiveShadow = true; out.add(road);
  for (let z = -300; z < 300; z += 9) box(0.18, 0.02, 3, 0, 0.035, z, mat(0xd8d8d0, 0.6), 0, out);
  const gr = new THREE.Mesh(new THREE.PlaneGeometry(400, 600).rotateX(-Math.PI / 2), mat(0x1d2a1a, 1)); out.add(gr);
  for (let i = 0; i < 18; i++) { const lp = box(0.2, 7, 0.2, 8.5, 3.5, -270 + i * 32, mat(0x30343b, 0.6, 0.5), 0, out); const bulb = new THREE.PointLight(0xffd59a, 25, 22, 1.6); bulb.position.set(7.5, 7, -270 + i * 32); out.add(bulb); }
  const hosp = new THREE.Group(); hosp.position.set(-30, 0, -210); out.add(hosp); box(46, 22, 26, 0, 11, 0, mat(0xd9d6cf, 0.8), 0, hosp);
  for (let r = 0; r < 5; r++) for (let c = 0; c < 10; c++) { const w = new THREE.Mesh(new THREE.PlaneGeometry(2.2, 1.6), new THREE.MeshBasicMaterial({ color: hash1(r * 10 + c) < 0.65 ? 0xffe6b0 : 0x1a2230, toneMapped: false })); w.position.set(-20 + c * 4.4, 3 + r * 4, 13.05); hosp.add(w); }
  const sign = new THREE.Mesh(new THREE.PlaneGeometry(14, 2.6), new THREE.MeshBasicMaterial({ map: canvasTex(512, 96, g => { g.fillStyle = '#c4161c'; g.fillRect(0, 0, 512, 96); g.fillStyle = '#fff'; g.font = 'bold 60px Arial'; g.fillText('EMERGENCY', 70, 70); }), toneMapped: false })); sign.position.set(0, 19.5, 13.1); hosp.add(sign); }
const amb = new THREE.Group(); out.add(amb);
{ const wm = mat(0xf2f2ee, 0.45, 0.1); box(2.1, 2.5, 5.6, 0, 1.75, 0.4, wm, 0.15, amb); box(2.1, 1.7, 1.6, 0, 1.35, -2.9, wm, 0.15, amb);
  box(2.12, 0.3, 7.2, 0, 1.4, -0.4, mat(0xd7261e, 0.5), 0, amb); box(2.0, 0.8, 0.05, 0, 1.8, -3.72, mat(0x0d1218, 0.2, 0.3), 0, amb);
  for (const [x, z] of [[-1, -2.6], [1, -2.6], [-1, 2.2], [1, 2.2]]) { const wh = new THREE.Mesh(new THREE.CylinderGeometry(0.45, 0.45, 0.3, 20).rotateZ(Math.PI / 2), mat(0x111111, 0.8)); wh.position.set(x, 0.45, z); amb.add(wh); }
  for (const x of [-0.7, 0.7]) { const b = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.15, 0.3), new THREE.MeshBasicMaterial({ color: 0x3a6dff, toneMapped: false })); b.position.set(x, 3.08, -0.6); amb.add(b); }
  const hl = new THREE.SpotLight(0xfff2d8, 120, 60, 0.5, 0.5, 1.5); hl.position.set(0, 1.2, -3.8); hl.target.position.set(0, 0, -30); amb.add(hl, hl.target); }
// readout (same look as the plane Shorts)
const hudC = document.createElement('canvas'); hudC.width = 520; hudC.height = 440; const hudT = new THREE.CanvasTexture(hudC); hudT.colorSpace = THREE.SRGBColorSpace;
const hud = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: hudT, transparent: true, depthTest: false, depthWrite: false, toneMapped: false })); hud.renderOrder = 30; camera.add(hud); scene.add(camera); hud.visible = false;
function drawHud(rows, flag) { const g = hudC.getContext('2d'); g.clearRect(0, 0, 520, 440); g.beginPath(); g.roundRect(6, 6, 508, 428, 34); g.fillStyle = 'rgba(8,14,22,0.74)'; g.fill(); g.lineWidth = 4; g.strokeStyle = 'rgba(160,200,235,0.55)'; g.stroke();
  let y = 30; for (const [lab, val, col] of rows) { g.fillStyle = '#9fb6c8'; g.font = '600 34px Arial, Helvetica, sans-serif'; g.fillText(lab, 34, y + 38); g.fillStyle = col || '#fff'; g.font = 'bold 62px Arial, Helvetica, sans-serif'; g.fillText(val, 34, y + 102, 452); y += 120; }
  if (flag) { g.font = 'bold 52px Arial, Helvetica, sans-serif'; const fw = Math.min(460, g.measureText(flag).width + 40); g.beginPath(); g.roundRect(30, 340, fw, 76, 16); g.fillStyle = '#d9241b'; g.fill(); g.fillStyle = '#fff'; g.fillText(flag, 50, 397, fw - 40); }
  hudT.needsUpdate = true; }
function fitHud() { const d = camera.near * 1.6, h = 2 * d * Math.tan(camera.fov * D2R / 2), w = h * camera.aspect, gw = 0.4 * w, gh = gw * 440 / 520; hud.scale.set(gw, gh, 1); hud.position.set(w / 2 - gw / 2 - 0.035 * w, h / 2 - 0.165 * h - gh / 2, -d); }
// ------------------------------------------------------------------ x-ray view: the forward's body goes glassy, a heart and a brain inside (explainer beats)
const XRAYM = new THREE.MeshBasicMaterial({ color: 0x7fd3ff, transparent: true, opacity: 0.16, depthWrite: false, side: THREE.DoubleSide, blending: THREE.AdditiveBlending });
const XRSAVE = new Map(); let XRON = false;
G.reset(); G.root.updateMatrixWorld(true);
// the heart: two ventricles tapering to an apex (pointing down, forward and to his left), two atria, the aorta arching back, the pulmonary trunk
// and the vena cava (blue, as in diagrams), coronary vessels over the front. Built in metres, ~13 cm tall.
const heart = new THREE.Group();
{ const meat = new THREE.MeshPhysicalMaterial({ color: 0x9a1822, roughness: 0.38, clearcoat: 0.8, clearcoatRoughness: 0.25, emissive: 0x2a0306 });
  const meat2 = meat.clone(); meat2.color.set(0x7d1620); const art = new THREE.MeshPhysicalMaterial({ color: 0xc23a3c, roughness: 0.35, clearcoat: 0.7 }); const vein = new THREE.MeshPhysicalMaterial({ color: 0x3756a8, roughness: 0.4, clearcoat: 0.6 });
  const fat = new THREE.MeshStandardMaterial({ color: 0xd9b25e, roughness: 0.6 }), cor = new THREE.MeshStandardMaterial({ color: 0xd8463a, roughness: 0.4 });
  const vg = new THREE.SphereGeometry(0.05, 40, 28), pa = vg.attributes.position;
  for (let i = 0; i < pa.count; i++) { let x = pa.getX(i), y = pa.getY(i), z = pa.getZ(i); const k = y < 0 ? 1 + (y / 0.05) * 0.62 : 1 - (y / 0.05) * 0.1; pa.setXYZ(i, x * k, y * 1.35, z * k * 0.85); } vg.computeVertexNormals();
  const vent = new THREE.Mesh(vg, meat); heart.add(vent);
  const rv = new THREE.Mesh(new THREE.SphereGeometry(0.034, 28, 20), meat); rv.scale.set(1, 1.3, 0.75); rv.position.set(0.02, -0.005, -0.018); heart.add(rv);
  for (const [x, z, c] of [[0.028, 0.012, meat2], [-0.026, 0.02, meat2]]) { const at = new THREE.Mesh(new THREE.SphereGeometry(0.026, 24, 16), c); at.position.set(x, 0.05, z); at.scale.set(1, 0.85, 1); heart.add(at); }
  const tube = (pts, r, m) => { const t = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts.map(p => V(...p))), 40, r, 14), m); heart.add(t); return t; };
  tube([[0.002, 0.04, 0.0], [0.0, 0.1, 0.0], [-0.02, 0.128, 0.02], [-0.04, 0.115, 0.038], [-0.046, 0.07, 0.045]], 0.013, art);            // aorta, arching back and down
  for (const [x, y, z] of [[0.004, 0.13, 0.008], [-0.012, 0.135, 0.018], [-0.026, 0.13, 0.026]]) tube([[x, y - 0.012, z], [x * 1.4, y + 0.02, z]], 0.0045, art);   // its branches
  tube([[-0.012, 0.035, -0.03], [-0.016, 0.085, -0.022], [-0.02, 0.105, -0.005]], 0.012, vein);                                              // pulmonary trunk
  tube([[-0.02, 0.105, -0.005], [-0.05, 0.11, 0.0]], 0.008, vein); tube([[-0.02, 0.105, -0.005], [0.01, 0.112, 0.012]], 0.008, vein);
  tube([[0.034, 0.05, 0.016], [0.035, 0.1, 0.014], [0.034, 0.14, 0.01]], 0.01, vein);                                                      // superior vena cava
  tube([[0.01, 0.03, -0.042], [-0.008, -0.01, -0.044], [-0.02, -0.045, -0.032], [-0.022, -0.068, -0.014]], 0.0035, fat);                   // front groove with its vessel
  tube([[0.01, 0.03, -0.044], [-0.008, -0.01, -0.046], [-0.02, -0.045, -0.034], [-0.022, -0.068, -0.016]], 0.002, cor);
  tube([[0.03, 0.025, -0.02], [0.044, -0.01, -0.005], [0.03, -0.045, 0.012]], 0.0022, cor); tube([[-0.03, 0.02, -0.03], [-0.045, -0.015, -0.01], [-0.04, -0.05, 0.01]], 0.0022, cor);
  heart.rotation.set(0.35, 0.3, -0.45); }
heart.position.copy(wp(G.bones.chest).add(V(-0.02, -0.035, -0.035))); scene.add(heart); G.bones.chest.attach(heart); heart.visible = false;
const HEARTS = heart.scale.clone();
const brain = new THREE.Mesh(new THREE.SphereGeometry(1, 40, 24), new THREE.MeshStandardMaterial({ color: 0xf0a6b4, emissive: 0x401018, emissiveIntensity: 0.6, roughness: 0.6 }));
{ const pa = brain.geometry.attributes.position; for (let i = 0; i < pa.count; i++) { const x = pa.getX(i), y = pa.getY(i), z = pa.getZ(i), f = 1 + 0.04 * Math.sin(x * 23 + z * 17) * Math.sin(y * 19 + x * 7); pa.setXYZ(i, x * f, y * f, z * f); } brain.geometry.computeVertexNormals(); }
brain.scale.set(0.068, 0.056, 0.083); brain.position.copy(wp(G.bones.head).add(V(0, 0.085, 0.0))); scene.add(brain); G.bones.head.attach(brain); brain.visible = false;
const BRAINP = brain.position.clone(), BRAINS = brain.scale.clone();
const XRSKIP = new Set(); heart.traverse(o => XRSKIP.add(o)); XRSKIP.add(brain);
function xray(on) { if (XRON === on) return; XRON = on; G.root.traverse(o => { if (!o.isMesh || XRSKIP.has(o)) return; if (on) { XRSAVE.set(o, o.material); o.material = XRAYM; o.castShadow = false; } else { o.material = XRSAVE.get(o) || o.material; o.castShadow = true; } }); heart.visible = brain.visible = on; }
// heart-rhythm line for the readout: 'beat' (normal), 'vf' (quivering), 'flat' (none)
function drawECG(g, mode, t, x0, y0, w, h) { g.strokeStyle = mode === 'beat' ? '#2fbf71' : '#ff5a4f'; g.lineWidth = 6; g.lineJoin = 'round'; g.beginPath();
  for (let i = 0; i <= 120; i++) { const x = x0 + w * i / 120, s = t * 1.6 + i / 120 * 2.2; let y;
    if (mode === 'beat') { const ph = s % 1; y = ph > 0.42 && ph < 0.47 ? -1 : ph > 0.47 && ph < 0.5 ? 0.35 : ph > 0.6 && ph < 0.72 ? -0.18 * Math.sin((ph - 0.6) / 0.12 * Math.PI) : 0; }
    else if (mode === 'vf') y = 0.45 * Math.sin(s * 37 + Math.sin(s * 11) * 2) + 0.25 * Math.sin(s * 23.7 + 1.3);
    else y = 0.02 * Math.sin(s * 9);
    const yy = y0 + h / 2 + y * h * 0.45; i ? g.lineTo(x, yy) : g.moveTo(x, yy); } g.stroke(); }
function drawHudECG(title, val, col, mode, t, flag) { drawHud([[title, val, col]], flag); const g = hudC.getContext('2d'); drawECG(g, mode, t, 34, 170, 452, 150); hudT.needsUpdate = true; }
// impact marks for the x-ray at the hit: red glows on the chest and the head
const impact = new THREE.Group(); scene.add(impact); impact.visible = false;
{ const tex = canvasTex(128, 128, g => { const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64); gr.addColorStop(0, 'rgba(255,80,60,1)'); gr.addColorStop(0.4, 'rgba(255,40,30,0.5)'); gr.addColorStop(1, 'rgba(255,0,0,0)'); g.fillStyle = gr; g.fillRect(0, 0, 128, 128); });
  for (const s of [0.32, 0.26]) { const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthWrite: false, depthTest: false, toneMapped: false, blending: THREE.AdditiveBlending })); sp.scale.set(s, s, 1); sp.renderOrder = 20; impact.add(sp); } }
// ------------------------------------------------------------------ story: one shot per line
const C = V(0, 0, -36);                                      // where they met: inside the box, in front of the goal
function run(ph, lean = -10) { const s = Math.sin(ph), c = Math.cos(ph);
  return curl(curl({ spine1: [lean, 0, 0], chest: [-4, 0, 0], neck: [8, 0, 0], thighR: [22 + 48 * s, 0, 0], thighL: [22 - 48 * s, 0, 0],
    shinR: [-28 - 70 * Math.max(0, -s) - 15 * Math.max(0, c), 0, 0], shinL: [-28 - 70 * Math.max(0, s) - 15 * Math.max(0, -c), 0, 0], footR: [8 * s, 0, 0], footL: [-8 * s, 0, 0],
    armR: A(8 - 48 * s, 14, 0, 88), armL: A(8 + 48 * s, 14, 0, 88) }, 'R', 55), 'L', 55); }
const bob = ph => 0.95 + 0.035 * Math.abs(Math.cos(ph));
// the keeper's leap to clear it (knee up, arms out) and the forward knocked back, then down
const LEAP = curl(curl({ spine1: [-14, 0, 0], chest: [-8, 0, 0], neck: [10, 0, 0], thighR: [105, 0, 0], shinR: [-95, 0, 0], thighL: [-12, 0, 0], shinL: [-40, 0, 0], armR: A(120, 35, 0, 25), armL: A(115, 40, 0, 30) }, 'R', 20), 'L', 20);
const HIT = curl(curl({ spine1: [18, 0, 0], chest: [14, 0, 0], neck: [20, 0, 0], head: [18, 0, 0], thighR: [30, 0, 0], shinR: [-40, 0, 0], thighL: [-10, 0, 0], shinL: [-25, 0, 0], armR: A(60, 55, 0, 30), armL: A(55, 60, 0, 35) }, 'R', 15), 'L', 15);
const DOWN = curl(curl({ spine1: [4, 0, 0], neck: [6, 0, 0], head: [0, 0, 8], thighR: [8, 0, 6], shinR: [-12, 0, 0], thighL: [4, 0, -4], shinL: [-6, 0, 0], armR: A(-5, 30, 0, 20), armL: A(-5, 25, 0, 25), footR: [20, 0, 0], footL: [22, 0, 0] }, 'R', 10), 'L', 10);
const HANDSHEAD = curl(curl({ ...STAND, neck: [18, 0, 0], head: [12, 0, 0], armR: A(155, 35, 10, 125), armL: A(155, 35, 10, 125) }, 'R', 20), 'L', 20);
const HIPS = { ...STAND, armR: A(10, 35, 40, 100, 0, 0, 0), armL: A(10, 35, 40, 100, 0, 0, 0) };
function ballAt(t0, t1, t, p0, p1, h) { const u = clamp((t - t0) / (t1 - t0), 0, 1); return p0.clone().lerp(p1, u).add(V(0, h * 4 * u * (1 - u), 0)); }
// each shot sets both men, the ball, the camera, the readout; returns the focus point
const MAP = { 0: 0, 1: 1, 2: 3, 3: 5, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 7, 10: 8, 11: 9, 12: 6, 13: 12 };   // the script's lines -> the shot each one uses
const XRL = [4, 5, 6, 7, 8];                                   // x-ray explainer lines (frozen at the moment of the hit)
let KCUR = 0, KC = 0.4;
function shot(t) { const nb = beatAt(t), lt = t - B[nb], dur = DUR[nb], XRB = XRL.includes(nb); let u = XRB ? 0 : lt / dur; const b = MAP[nb];
  let xr = XRB;
  out.visible = false; card.visible = false; hud.visible = false; G.root.visible = K.root.visible = true; ball.visible = true; sun.intensity = 3.2;
  let fpos, fpose, kpos, kpose, cp, ct, fov = 34, near = 0.05;
  switch (b) {
    case 0: case 5: { // the collision (0: frozen moment, camera round it; 5: slow motion, side on)
      let k = b === 0 ? 0.41 + 0.02 * u : clamp((u - 0.03) / 0.55, 0, 1); const kc = KC;      // kc: the moment of contact
      if (nb === 3 && k > kc + 0.01) { k = kc + 0.01; xr = true; }                             // line 3: at the hit, freeze and go into the x-ray
      KCUR = k;
      const pre = clamp(k / kc, 0, 1), post = clamp((k - kc) / (1 - kc), 0, 1);
      const ph = (b === 0 ? 2.2 : 1.6 + lt * 3.2);
      fpose = post > 0 ? mixPose(HIT, DOWN, sm(clamp((post - 0.35) / 0.65, 0, 1))) : mixPose(run(ph), HIT, sm(clamp((pre - 0.8) / 0.2, 0, 1)));
      const fall = sm(clamp((post - 0.25) / 0.75, 0, 1));
      fpos = { x: C.x, y: lerp(bob(ph), 0.16, fall), z: C.z + 1.6 * (1 - pre) - 0.9 * post, yaw: 0, tilt: lerp(post > 0 ? 25 * sm(Math.min(1, post * 4)) : -8, 88, fall) };
      kpose = mixPose(run(ph + 1.3), LEAP, sm(clamp((pre - 0.5) / 0.5, 0, 1))); kpose = post > 0 ? mixPose(LEAP, mixPose(STAND, LEAP, 0.3), sm(post)) : kpose;
      kpos = { x: C.x + 0.15, y: 0.95 + 0.38 * Math.sin(Math.PI * clamp((k - 0.25) / 0.45, 0, 1)), z: C.z - 0.95 - 3.2 * (1 - pre) + 0.4 * post, yaw: 180, tilt: -12 * clamp(k * 2, 0, 1) };
      ball.position.copy(C).add(V(0.4 + 2.5 * post, 2.3 + 1.2 * post - 1.5 * post * post, -0.6 - 3 * post));
      if (b === 0) { const a = lerp(-30, 45, u) * D2R; cp = V(C.x + Math.sin(a) * 6.2, 1.5, C.z - 0.5 + Math.cos(a) * 6.2); ct = V(C.x, 1.25, C.z - 0.5); }
      else { const push = xr ? sm(clamp((u - 0.6) / 0.4, 0, 1)) : 0; cp = V(C.x + lerp(6.5, 2.4, push), lerp(1.3, 1.5, push), C.z - 0.5 + lerp(0, 1.4, push)); ct = V(C.x, lerp(1.1, 1.35, push), C.z - 0.5); }
      break; }
    case 1: { // who he was: the stand-in in white, centre circle
      fpose = STAND; fpos = { x: 0, y: 0.95, z: 0, yaw: 25 }; kpose = STAND; kpos = { x: 6, y: 0.95, z: -30, yaw: 180 }; K.root.visible = false;
      ball.position.set(0.5, 0.11, -0.6); cp = V(1.8 - 0.4 * u, 1.55, -3.6 + 0.8 * u); ct = V(0, 1.3, 0); fov = 32;
      hud.visible = true; drawHud([['TENERIFE', 'FORWARD'], ['AGE', '30']]); break; }
    case 2: { // the stadium, stoppage time
      const ph = t * 4; fpose = run(ph); fpos = { x: 4, y: bob(ph), z: -6 - u * 4, yaw: 10 }; kpose = STAND; kpos = { x: 0, y: 0.95, z: -50, yaw: 180 };
      ball.position.set(3, 0.11, -12 - u * 5); cp = V(-40, 26, 30 - 10 * u); ct = V(0, 0, -20); fov = 40;
      hud.visible = true; drawHud([['TENERIFE 2-2 ANDORRA', ''], ['STOPPAGE TIME', "90+7'", '#ffd23a']]); break; }
    case 3: { // the long ball over the top; he chases it
      const ph = 1.6 + t * 9; fpose = run(ph); const z = lerp(-18, -31, u); fpos = { x: 0.4, y: bob(ph), z, yaw: 0 }; kpose = STAND; kpos = { x: 0, y: 0.95, z: -50.5, yaw: 180 };
      ball.position.copy(ballAt(0, dur * 1.15, lt, V(0.6, 1.2, 8), V(0.4, 2.2, -36.6), 18)); cp = V(7.8, 1.7, z + 0.6); ct = V(0.4, 1.4, z - 0.9); fov = 40; break; }
    case 4: { // the keeper runs off his line to clear it
      const ph = 0.4 + t * 9; kpose = run(ph); const z = lerp(-50.5, -40, u); kpos = { x: 0.15, y: bob(ph), z, yaw: 180 };
      const ph2 = 1.6 + t * 9; fpose = run(ph2); fpos = { x: 0.4, y: bob(ph2), z: lerp(-31, -34.4, u), yaw: 0 };
      ball.position.copy(ballAt(-1, 1.6 * dur, lt, V(0.5, 8, -26), V(0.4, 2.2, -36.6), 2)); cp = V(-5, 1.4, z - 6); ct = V(0.2, 1.3, z + 3); fov = 40; break; }
    case 6: { // he lies still; the keeper, hands on his head
      fpose = DOWN; fpos = { x: C.x, y: 0.16, z: C.z - 0.9, yaw: 0, tilt: 88 }; kpose = HANDSHEAD; kpos = { x: C.x + 2.2, y: 0.95, z: C.z - 3.0, yaw: 200 };
      ball.position.set(C.x + 6, 0.11, C.z - 8); const a = lerp(0.3, 0.6, u); cp = V(C.x + Math.sin(a) * 15, 9 - 2 * u, C.z + Math.cos(a) * 15); ct = V(C.x, 0.4, C.z - 1.5); fov = 30; break; }
    case 7: { // the red card; the match is called off
      fpose = DOWN; fpos = { x: C.x, y: 0.16, z: C.z - 0.9, yaw: 0, tilt: 88 }; kpose = mixPose(STAND, HANDSHEAD, 0.25); kpos = { x: C.x + 3.5, y: 0.95, z: C.z - 4.5, yaw: 220 };
      card.visible = true; card.position.set(C.x + 2.4, 1.75 + 0.15 * sm(Math.min(1, u * 3)), C.z - 5.4); card.lookAt(C.x + 12, 1.8, C.z + 4); ball.visible = false;
      cp = V(C.x + 9, 2.2, C.z + 1.5); ct = V(C.x + 2.8, 1.5, C.z - 4.6); fov = 32;
      hud.visible = true; drawHud([['KEEPER', 'SENT OFF', '#ff6a5c'], ['MATCH', 'CALLED OFF']], 'RED CARD'); break; }
    case 8: case 9: { // the ambulance; then the hospital
      G.root.visible = K.root.visible = false; ball.visible = false; out.visible = true; sun.intensity = 0.6;
      if (b === 8) { const z = 120 - (lt + 0) * 22; amb.position.set(-3.5, 0, z); amb.rotation.y = 0; cp = V(5, 3.2, z + 14).add(out.position); ct = V(-3.5, 1.5, z - 4).add(out.position); fov = 40;
        hud.visible = true; drawHud([['ON THE WAY', 'HEART STOPPED', '#ff6a5c'], ['PARAMEDICS', 'BROUGHT HIM BACK', '#2fbf71']]); }
      else { amb.position.set(-12, 0, -190); amb.rotation.y = 0.6; cp = V(18, 6, -150 - 6 * u).add(out.position); ct = V(-25, 9, -205).add(out.position); fov = 40;
        hud.visible = true; drawHud([['AT FIRST', 'SERIOUS, STABLE', '#ffd23a'], ['THEN', u < 0.45 ? '...' : 'GOT WORSE', '#ff6a5c']]); }
      fpose = STAND; fpos = { x: 0, y: -50, z: 0 }; kpose = STAND; kpos = { x: 2, y: -50, z: 0 }; break; }
    default: { // 10-12: the empty pitch at night, the ball on the spot
      G.root.visible = K.root.visible = false; fpose = STAND; fpos = { x: 0, y: -50, z: 0 }; kpose = STAND; kpos = { x: 2, y: -50, z: 0 };
      ball.position.set(0, 0.11, b === 12 ? 0 : C.z - 2); sun.intensity = b === 12 ? lerp(3.2, 1.0, u) : 3.2;
      if (b === 10) { cp = V(-6 + 2 * u, 1.2, C.z + 5); ct = V(0, 0.4, C.z - 2); hud.visible = true; drawHud([['TUESDAY', 'HE DIED'], ['CAUSE', 'NOT RELEASED', '#ffd23a']]); }
      else if (b === 11) { cp = V(-50, 22, 20 - 8 * u); ct = V(0, 0, -10); fov = 42; hud.visible = true; drawHud([['TENERIFE', 'HEARTBROKEN'], ['ANDORRA', 'DEVASTATED']]); }
      else { cp = V(0.9 - 0.3 * u, 0.5 + 0.1 * u, 2.4 - 0.8 * u); ct = V(0, 0.15, 0); fov = 30; }
    } }
  RG.applyPose(fpose, fpos); RK.applyPose(kpose, kpos); G.root.updateMatrixWorld(true); K.root.updateMatrixWorld(true);
  // contact: around the hit, slide the keeper so his right knee really meets the front of the forward's chest (it stopped short before)
  if (b === 0 || b === 5) { const w = smooth(KC - 0.15, KC - 0.02, KCUR) * (1 - smooth(KC + 0.3, KC + 0.55, KCUR));
    if (w > 0) { const chestF = wp(G.bones.chest).add(V(0, -0.05, -0.15)), knee = wp(K.bones.shinR); K.root.position.add(chestF.sub(knee).multiplyScalar(w)); K.root.updateMatrixWorld(true); } }
  xray(xr); impact.visible = xr && (nb === 3 || nb === 4); if (impact.visible) { const f = 0.5 + 0.5 * Math.sin(t * 6); impact.children.forEach(g => { g.material.opacity = 0.55 + 0.35 * f; }); impact.children[0].position.copy(wp(G.bones.chest).add(V(0, -0.05, -0.15))); impact.children[1].position.copy(wp(G.bones.head).add(V(0, 0.08, -0.1))); }
  // the explainers: x-ray close-ups of the chest (heart) and the head (brain), frozen at the moment of the hit
  heart.scale.copy(HEARTS); brain.position.copy(BRAINP); brain.scale.copy(BRAINS); brain.material.emissive.set(0x401018);
  if (XRB) { const U = lt / dur; ball.visible = false;
    if (nb === 4) { cp = V(C.x + 3.4, 1.45, C.z + 1.6); ct = V(C.x - 0.1, 1.3, C.z - 0.3); fov = 34; }
    else if (nb === 5 || nb === 6) { K.root.visible = false; const hp = wp(heart); cp = hp.clone().add(V(0.75, 0.12, -1.25)); ct = hp.clone().add(V(0, 0.08, 0)); fov = 30; near = 0.02;
      const vf = nb === 6 || U > 0.55; heart.scale.multiplyScalar(vf ? 1 + 0.025 * Math.sin(lt * 53) + 0.02 * Math.sin(lt * 31) : 1 + 0.09 * Math.max(0, Math.sin(lt * 7.5)) ** 6);
      hud.visible = true; drawHudECG('HEART', vf ? (nb === 6 ? 'NO PULSE' : 'OUT OF RHYTHM') : 'BEATING', vf ? '#ff6a5c' : '#2fbf71', vf ? 'vf' : 'beat', lt, nb === 6 ? 'NEEDS A SHOCK' : null); }
    else { K.root.visible = false; const bp = wp(brain); cp = bp.clone().add(V(0.95, 0.02, -0.25)); ct = bp.clone().add(V(0, -0.05, 0)); fov = 28; near = 0.02;
      if (nb === 7) { const j = Math.exp(-lt * 1.8) * Math.sin(lt * 9); brain.position.z += 0.012 * j; brain.position.y += 0.004 * j; }
      else { const sw = 1 + 0.12 * sm(clamp(U * 1.3, 0, 1)); brain.scale.multiplyScalar(sw); brain.material.emissive.setRGB(0.25 + 0.5 * sm(U), 0.05, 0.08); }
      hud.visible = true; drawHud([['BRAIN', nb === 7 ? 'HITS THE SKULL' : 'SWELLING', '#ff6a5c'], ['PRESSURE', nb === 7 ? 'NORMAL' : 'RISING', nb === 7 ? '#ffffff' : '#ff6a5c']]); }
    camera.position.copy(cp); camera.up.set(0, 1, 0); camera.lookAt(ct); camera.fov = fov; camera.near = near; camera.updateProjectionMatrix(); return { b: nb, focus: ct }; }
  if (nb === 12) { hud.visible = true; drawHud([['1. CALL', 'FOR HELP'], ['2. START', 'CPR', '#2fbf71']], 'GET THE AED'); }
  if (nb === 3 && xr) { hud.visible = true; drawHud([['HIT', 'CHEST', '#ff6a5c'], ['AND', 'HEAD', '#ff6a5c']]); }
  camera.position.copy(cp); camera.up.set(0, 1, 0); camera.lookAt(ct); camera.fov = fov; camera.near = near; camera.updateProjectionMatrix();
  return { b, focus: ct }; }
// ------------------------------------------------------------------ look + frame I/O
import { makeLook } from '/look.js';
const LOOK = makeLook(THREE, renderer, scene, camera, W, H, { overlays: [hud], aperture: 0.0008, maxblur: 0.006, rim: 1.8 });
let FOC = V(0, 1, 0);
function update(t) { t = clamp(t, 0, TOTAL - 1e-3); const r = shot(t); fitHud();
  const at = out.visible ? amb.position.clone().add(out.position) : (G.root.visible ? wp(G.bones.hips) : V(0, 0, 0));
  sun.position.copy(at).add(V(20, 45, 18)); sun.target.position.copy(at); sun.target.updateMatrixWorld(); FOC = r.focus; return r; }
function stepTo(i) { return update(i / FPS); }
const draw = () => LOOK.render(FOC, { ao: true, dof: true });
const gl = renderer.getContext(), px = new Uint8Array(W * H * 4);
window.renderAll = async (f0, f1) => { for (let i = f0; i < f1; i++) { stepTo(i); draw(); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); await fetch('/frame', { method: 'POST', body: px }); } return 'ok'; };
window.renderAtT = t => { stepTo(Math.round(t * FPS)); draw(); return renderer.domElement.toDataURL('image/png'); };
window.dbg = { THREE, scene, camera, G, K, RG, RK, shot };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS); window.READY = true;
window.SCN = { THREE, scene, camera, stepTo, renderer, FPS, B, DUR, TOTAL };
