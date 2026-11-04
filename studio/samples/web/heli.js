// Two helicopters collide landing at Pheriche, Nepal (Nov 3, 2026); why blade strikes are deadly. Generic AS350-type models, no logos, no people shown hurt.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { loadGuy } from '/guy3d.js';

const Q = new URLSearchParams(location.search);
const W = +Q.get('w') || 720, H = +Q.get('h') || 1280;
const FPS = 30;
const TIMES = await (await fetch('/heli/times.json')).json();
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
// ================================================================== A HIMALAYAN HELIPAD
// ------------------------------------------------------------------ set: a high Himalayan valley (Pheriche-like), a stone-ringed helipad, two generic AS350-type helicopters (no logos)
home.visible = false; lamp.visible = false; G.root.visible = false;
camera.far = 9000; camera.updateProjectionMatrix();
scene.background = new THREE.Color(0x9ec4ea); scene.fog = new THREE.Fog(0xc4d6e8, 900, 7000); scene.environmentIntensity = 0.35;
hemi.color.set(0xdbe8ff); hemi.groundColor.set(0x8a8478); hemi.intensity = 0.6; sun.color.set(0xfff2de); sun.intensity = 2.8; sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.04;
{ const S = sun.shadow.camera; S.left = -18; S.right = 18; S.top = 18; S.bottom = -18; S.near = 1; S.far = 300; S.updateProjectionMatrix(); }
// sky dome that rides with the camera (inside the far plane), day or dusk
const SKY = new THREE.Mesh(new THREE.SphereGeometry(8000, 32, 16), new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false, fog: false, uniforms: { uSet: { value: 0 } },
  vertexShader: 'varying vec3 d; void main(){ d = normalize(position); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }',
  fragmentShader: `uniform float uSet; varying vec3 d; void main(){ float h = clamp(d.y, 0., 1.); vec3 day = mix(vec3(.78,.87,.96), vec3(.20,.42,.80), pow(h, .5)); vec3 dusk = mix(vec3(1.,.66,.5), vec3(.22,.2,.42), pow(h, .45));
    gl_FragColor = vec4(mix(day, dusk, uSet), 1.);
    #include <colorspace_fragment>
  }` })); SKY.renderOrder = -10; SKY.frustumCulled = false; scene.add(SKY); window.__SKY = SKY;
const SKYU = SKY.material.uniforms;
// terrain: a flat glacial valley floor running north (-z, to base camp) and south (+z, to Lukla), steep rock walls, snow peaks
function n2(x, z) { const xi = Math.floor(x), zi = Math.floor(z), xf = x - xi, zf = z - zi, h = (a, b) => hash1(a * 157.1 + b * 311.7);
  const u = xf * xf * (3 - 2 * xf), v = zf * zf * (3 - 2 * zf); return lerp(lerp(h(xi, zi), h(xi + 1, zi), u), lerp(h(xi, zi + 1), h(xi + 1, zi + 1), u), v); }
function fbm(x, z) { let s = 0, a = 0.5, f = 1; for (let i = 0; i < 5; i++) { s += a * n2(x * f, z * f); f *= 2.03; a *= 0.5; } return s; }
const valleyX = z => 60 * Math.sin(z / 900);
function HT(x, z) { const d = Math.abs(x - valleyX(z)); const wall = smooth(130, 900, d), r = fbm(x / 420, z / 420);
  let h = wall * (500 + 1300 * r) + smooth(700, 2600, d) * 900 * fbm(x / 900 + 7, z / 900);
  for (const [px, pz, ph, pr] of [[-1500, -2600, 1900, 800], [1700, -1200, 1700, 700], [-1300, 900, 1500, 650], [1500, 2400, 1700, 800], [300, -4200, 2200, 1200]]) h += ph * Math.exp(-((x - px) ** 2 + (z - pz) ** 2) / (pr * pr));
  return h + (1 - wall) * 1.2 * (fbm(x / 30, z / 30) - 0.5); }
{ const g = new THREE.PlaneGeometry(14000, 14000, 360, 360).rotateX(-Math.PI / 2), P = g.attributes.position, col = [];
  for (let i = 0; i < P.count; i++) { const x = P.getX(i), z = P.getZ(i); let y = HT(x, z); if (Math.abs(x) < 40 && Math.abs(z) < 40) y = Math.min(y, 0.3 * smooth(25, 40, Math.max(Math.abs(x), Math.abs(z)))); P.setY(i, y); }
  g.computeVertexNormals(); const N = g.attributes.normal;
  for (let i = 0; i < P.count; i++) { const y = P.getY(i), ny = N.getY(i), x = P.getX(i), z = P.getZ(i), k = fbm(x / 25, z / 25);
    const rock = [0.3 + 0.12 * k, 0.26 + 0.1 * k, 0.23 + 0.08 * k], grass = [0.88 + 0.05 * k, 0.87 + 0.05 * k, 0.85 + 0.04 * k], snow = [0.9, 0.92, 0.96];
    let c = y < 40 ? grass : rock; if (ny > 0.62 + 0.15 * k) c = snow; if (y > 1700) c = ny > 0.5 ? snow : [0.45, 0.43, 0.42]; const cc = new THREE.Color().setRGB(c[0], c[1], c[2], THREE.SRGBColorSpace); col.push(cc.r, cc.g, cc.b); }
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  const t = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.95 })); t.receiveShadow = true; scene.add(t); }
// snow patches and stones scattered on the valley floor near the pad
for (let i = 0; i < 160; i++) { const x = (hash1(i * 3.1) - 0.5) * 220, z = (hash1(i * 7.3) - 0.5) * 300; if (Math.abs(x) < 16 && Math.abs(z) < 16) continue;
  if (Math.abs(x) < 60 && Math.abs(z) < 60) continue; const s = new THREE.Mesh(new THREE.CircleGeometry(0.6 + 1.6 * hash1(i), 14).rotateX(-Math.PI / 2), mat(0xf2f5fa, 0.9)); s.position.set(x, 0.32 + 0.002 * i, z); s.scale.z = 0.6 + 0.8 * hash1(i * 9); s.receiveShadow = true; scene.add(s); }
for (let i = 0; i < 120; i++) { const x = (hash1(i * 5.9) - 0.5) * 200, z = (hash1(i * 2.3) - 0.5) * 260; if (Math.abs(x) < 15 && Math.abs(z) < 15) continue;
  const r = new THREE.Mesh(new THREE.DodecahedronGeometry(0.3 + 0.9 * hash1(i * 4), 0), mat(0x6f6a66, 0.95)); r.position.set(x, 0.3, z); r.rotation.set(i, i * 2, i * 3); r.castShadow = true; scene.add(r); }
// the helipad: flat ground, a ring of white stones, a painted H
{ const pad = new THREE.Mesh(new THREE.CircleGeometry(11, 48).rotateX(-Math.PI / 2), mat(0xd6d2ca, 0.95)); pad.position.y = 0.31; pad.receiveShadow = true; scene.add(pad);
  for (let i = 0; i < 40; i++) { const a = i / 40 * Math.PI * 2, st = new THREE.Mesh(new THREE.DodecahedronGeometry(0.28, 0), mat(0xf4f4f0, 0.8)); st.position.set(Math.cos(a) * 11, 0.4, Math.sin(a) * 11); st.castShadow = true; scene.add(st); }
  const hm = mat(0xf4f4f0, 0.8); for (const [w, d, x, z] of [[0.9, 6, -1.8, 0], [0.9, 6, 1.8, 0], [2.7, 0.9, 0, 0]]) { const p = new THREE.Mesh(new THREE.BoxGeometry(w, 0.04, d), hm); p.position.set(x, 0.33, z); p.receiveShadow = true; scene.add(p); } }
// a windsock and a line of prayer flags between two poles
const sockM = mat(0xff6a1a, 0.7); box(0.1, 5, 0.1, 13, 2.8, -6, mat(0xcccccc, 0.5), 0); const sock = new THREE.Mesh(new THREE.ConeGeometry(0.35, 2.2, 14, 1, true).rotateZ(Math.PI / 2), sockM); sock.position.set(14.1, 5.1, -6); scene.add(sock);
const flags = [];
{ const a = V(-26, 4.5, 12), b = V(-15, 3.6, 20); box(0.12, 4.5, 0.12, a.x, 2.4, a.z, mat(0x7a5a3a, 0.9), 0); box(0.12, 3.6, 0.12, b.x, 1.9, b.z, mat(0x7a5a3a, 0.9), 0);
  const cols = [0x2a5bd7, 0xf4f4f0, 0xd62a2a, 0x2aa04a, 0xf2c21a]; for (let i = 0; i < 20; i++) { const u = (i + 0.5) / 20, p = a.clone().lerp(b, u); p.y -= 0.9 * Math.sin(Math.PI * u);
    const f = new THREE.Mesh(new THREE.PlaneGeometry(0.32, 0.38), new THREE.MeshStandardMaterial({ color: cols[i % 5], roughness: 0.8, side: THREE.DoubleSide })); f.position.copy(p).add(V(0, -0.2, 0)); f.lookAt(f.position.clone().add(V(-0.6, 0, 1))); scene.add(f); flags.push(f); }
  const rope = []; for (let i = 0; i <= 24; i++) { const u = i / 24, p = a.clone().lerp(b, u); p.y -= 0.9 * Math.sin(Math.PI * u); rope.push(p); }
  scene.add(new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(rope), 40, 0.015, 5), mat(0xd8d0c0, 0.9))); }
// stone lodges with coloured tin roofs (the village), along the east side of the floor
for (let i = 0; i < 14; i++) { const x = 34 + 22 * hash1(i * 1.7) + (i % 2) * 14, z = -70 + i * 11 + 4 * hash1(i * 3), w = 7 + 4 * hash1(i * 5), d = 5 + 3 * hash1(i * 8), h = 2.6 + 1.2 * hash1(i * 4);
  const L = new THREE.Group(); L.position.set(x, 0.3, z); L.rotation.y = 0.1 * (hash1(i) - 0.5); scene.add(L);
  box(w, h, d, 0, h / 2, 0, mat(new THREE.Color().setHSL(0.08, 0.08, 0.55 + 0.12 * hash1(i * 6)), 0.95), 0.05, L).castShadow = true;
  const roof = new THREE.Mesh(new THREE.CylinderGeometry(0.01, d * 0.62, w * 1.05, 4, 1).rotateZ(Math.PI / 2).rotateX(Math.PI / 4), mat([0x2b5fb3, 0x2f8a4a, 0xb53a2a, 0x2a7f9a][i % 4], 0.55, 0.35)); roof.scale.set(1, 0.42, 1); roof.position.y = h + d * 0.2; roof.castShadow = true; L.add(roof);
  for (let k = -1; k <= 1; k += 2) box(0.9, 0.9, 0.05, k * w * 0.25, h * 0.55, d / 2 + 0.02, mat(0x2a3440, 0.3), 0, L); }
// low stone walls (yak pens)
for (let i = 0; i < 6; i++) box(14, 0.9, 0.6, 30 + 8 * hash1(i), 0.75, -40 + i * 16, mat(0x7a756e, 0.95), 0.1).castShadow = true;
// ---- the helicopter: Airbus AS350 B3 / H125 at real size (fuselage 10.93 m nose to tail rotor, main rotor 10.69 m, 3 blades turning clockwise from above,
// tail rotor 1.86 m on the LEFT of the fin, rotor head 3.34 m up, skids 2.2 m apart). Root at the skid bottoms, nose to -z. No logos or names.
const glassM = new THREE.MeshStandardMaterial({ color: 0x24333f, roughness: 0.06, metalness: 0.5, transparent: true, opacity: 0.9 });
const bladeM = mat(0x26282c, 0.5, 0.3), darkM = mat(0x34373c, 0.6, 0.4), skidM = mat(0xa7adb5, 0.35, 0.75);
const ROTOR_Y = 3.15, ROTOR_R = 5.345;
// fuselage cross-sections (z, half width, bottom y, top y), measured off AS350 side and top views
const SECT = [[-2.62, 0.04, 1.28, 1.36], [-2.5, 0.42, 0.95, 1.72], [-2.3, 0.66, 0.8, 1.98], [-2.0, 0.82, 0.72, 2.16], [-1.6, 0.9, 0.68, 2.27], [-1.0, 0.935, 0.66, 2.33],
  [-0.2, 0.935, 0.66, 2.34], [0.6, 0.92, 0.68, 2.33], [1.2, 0.86, 0.76, 2.3], [1.7, 0.66, 0.98, 2.22], [2.15, 0.42, 1.28, 2.12], [2.6, 0.31, 1.45, 2.04]];
function loftHeli(paintM, lowM) { const NA = 36, P = [], cols = [], idxP = [], idxL = [], idxG = [];
  const pt = (s, a) => { const [z, hw, yb, yt] = s, c = Math.cos(a), sn = Math.sin(a), e = 2 / 2.7; return V(hw * Math.sign(c) * Math.abs(c) ** e, (yb + yt) / 2 + (yt - yb) / 2 * Math.sign(sn) * Math.abs(sn) ** e, z); };
  for (const s of SECT) for (let i = 0; i <= NA; i++) P.push(pt(s, i / NA * Math.PI * 2));
  for (let k = 0; k < SECT.length - 1; k++) for (let i = 0; i < NA; i++) { const a = k * (NA + 1) + i, b = a + 1, c = a + NA + 1, d = c + 1;
    const m = P[a].clone().add(P[b]).add(P[c]).add(P[d]).multiplyScalar(0.25);
    const ax = Math.abs(m.x), glass = (m.z < -1.05 && m.y > 0.9 && !(m.y > 2.2 && m.z > -1.6)) || (ax > 0.7 && m.y > 1.42 && m.y < 2.12 && ((m.z > -0.95 && m.z < -0.12) || (m.z > 0.05 && m.z < 1.05)));
    const low = !glass && m.y < 1.05 && m.z > -1.4;
    (glass ? idxG : low ? idxL : idxP).push(a, c, b, b, c, d); }
  const g = new THREE.BufferGeometry(); g.setFromPoints(P); const all = [...idxP, ...idxL, ...idxG]; g.setIndex(all);
  g.addGroup(0, idxP.length, 0); g.addGroup(idxP.length, idxL.length, 1); g.addGroup(idxP.length + idxL.length, idxG.length, 2); g.computeVertexNormals();
  const m = new THREE.Mesh(g, [paintM, lowM, glassM]); m.castShadow = true; return m; }
function makeHeli(bodyC, lowC, boomC) { const h = new THREE.Group(); scene.add(h); const bodyM = mat(bodyC, 0.32, 0.25), lowM = mat(lowC, 0.4, 0.25), boomM = mat(boomC, 0.35, 0.25), U = h.userData;
  const body = new THREE.Group(); h.add(body); U.body = body; U.win = new THREE.Object3D();
  body.add(loftHeli(bodyM, lowM));
  // door frames: thin dark lines between the side windows
  for (const s of [-1, 1]) for (const z of [-0.98, -0.03, 1.08]) box(0.03, 0.75, 0.05, s * 0.935, 1.78, z, darkM, 0, body);
  // engine and main gearbox fairing (the 'doghouse'), air intake grilles, exhaust on the right side
  const cowl = box(1.18, 0.5, 2.9, 0, 2.52, 0.75, bodyM, 0.22, body); cowl.castShadow = true;
  box(1.0, 0.32, 0.9, 0, 2.86, 0.2, bodyM, 0.15, body); for (const s of [-1, 1]) box(0.02, 0.22, 0.6, s * 0.6, 2.55, 0.9, darkM, 0, body);
  const ex = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.18, 0.5, 14).rotateZ(Math.PI / 2 - 0.4), darkM); ex.position.set(0.55, 2.55, 2.05); body.add(ex);
  // tail boom (tapered, slightly rising), horizontal stabiliser with end fins, the upper and lower fins, tail skid
  { const z0 = 2.5, z1 = 7.55, dz = z1 - z0, bm = new THREE.Mesh(new THREE.CylinderGeometry(0.15, 0.31, dz, 18).rotateX(Math.PI / 2), boomM); bm.position.set(0, 1.78, (z0 + z1) / 2); bm.rotation.x = -0.03; bm.castShadow = true; body.add(bm); }
  box(2.1, 0.06, 0.55, 0, 1.86, 6.15, boomM, 0.02, body); for (const s of [-1, 1]) box(0.05, 0.5, 0.42, s * 1.05, 1.9, 6.18, boomM, 0.02, body);
  { const sh = new THREE.Shape(); sh.moveTo(0, 0); sh.lineTo(0.75, 0); sh.lineTo(1.05, 1.25); sh.lineTo(0.62, 1.25); sh.closePath();
    const fin = new THREE.Mesh(new THREE.ExtrudeGeometry(sh, { depth: 0.08, bevelEnabled: false }).rotateY(-Math.PI / 2), boomM); fin.position.set(0.04, 1.86, 7.0); fin.castShadow = true; body.add(fin);
    const lo = new THREE.Shape(); lo.moveTo(0, 0); lo.lineTo(0.7, 0); lo.lineTo(0.85, -0.55); lo.lineTo(0.5, -0.55); lo.closePath();
    const vf = new THREE.Mesh(new THREE.ExtrudeGeometry(lo, { depth: 0.07, bevelEnabled: false }).rotateY(-Math.PI / 2), boomM); vf.position.set(0.035, 1.8, 7.0); body.add(vf);
    const ts = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 0.6, 6).rotateX(0.9), skidM); ts.position.set(0, 1.12, 7.65); body.add(ts); }
  // tail rotor: 2 blades, 1.86 m across, on the left side of the fin
  const trot = new THREE.Group(); trot.position.set(-0.16, 2.3, 7.72); body.add(trot); U.trot = trot; box(0.12, 0.12, 0.12, 0, 0, 0, darkM, 0.03, trot);
  for (let k = 0; k < 2; k++) { const b = box(0.03, 1.86, 0.15, -0.04, 0, 0, bladeM, 0, trot); b.rotation.x = k * Math.PI / 2; }
  // skids: two long tubes with upturned toes, two curved cross tubes up to the belly
  for (const s of [-1, 1]) { const pts = [V(s * 1.1, 0.42, -2.25), V(s * 1.1, 0.12, -1.95), V(s * 1.1, 0.04, -1.6), V(s * 1.1, 0.04, 1.35), V(s * 1.1, 0.07, 1.55)];
    const sk = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 24, 0.045, 8), skidM); sk.castShadow = true; h.add(sk);
    for (const z of [-0.95, 0.75]) { const ct = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3([V(s * 1.1, 0.04, z), V(s * 1.04, 0.45, z), V(s * 0.78, 0.72, z)]), 10, 0.05, 8), skidM); ct.castShadow = true; h.add(ct); } }
  for (const z of [-0.95, 0.75]) box(1.56, 0.08, 0.1, 0, 0.72, z, skidM, 0.03, h);
  // main rotor: mast, Starflex hub, three blades (clockwise from above), a faint blur disc
  const mast = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.12, 0.3, 12), darkM); mast.position.set(0, 3.02, 0); body.add(mast);
  const rot = new THREE.Group(); rot.position.set(0, ROTOR_Y, 0); body.add(rot); U.rot = rot;
  const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.36, 0.1, 3), darkM); rot.add(hub); box(0.14, 0.24, 0.14, 0, 0.12, 0, darkM, 0.04, rot); U.blades = [];
  for (let k = 0; k < 3; k++) { const arm = new THREE.Group(); arm.rotation.y = k * Math.PI * 2 / 3; rot.add(arm);
    box(0.4, 0.09, 0.2, 0.42, 0, 0, darkM, 0.03, arm); const b = box(ROTOR_R - 0.6, 0.045, 0.35, (ROTOR_R + 0.6) / 2, -0.02, 0, bladeM, 0, arm); b.castShadow = true;
    const cap = box(0.3, 0.047, 0.35, ROTOR_R - 0.15, -0.02, 0, mat(0xe8e8e8, 0.5), 0, arm); arm.userData.full = [b, cap];
    const stub = box(1.3, 0.045, 0.35, 1.25, -0.02, 0, bladeM, 0, arm); stub.visible = false; arm.userData.stub = stub; U.blades.push(arm); }
  const disc = new THREE.Mesh(new THREE.CircleGeometry(ROTOR_R, 64).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ color: 0x202428, transparent: true, opacity: 0.12, depthWrite: false })); disc.position.y = -0.02; rot.add(disc); U.disc = disc;
  return h; }
// paint from the webcam video: one red, one white with a blue lower band and blue tail boom. Which company flew which is not reported; red = cargo (A) is a guess.
const HA = makeHeli(0xc23a22, 0x3a2622, 0xc23a22), HB = makeHeli(0xe9ecef, 0x1c3f8f, 0x1c3f8f);    // A: cargo from Lukla; B: from base camp with two trekkers
// debris: rotor blade pieces, small body bits and window glass (no people are ever shown)
const bitM = [mat(0x2a2c30, 0.5, 0.3), mat(0xc23a22, 0.4), mat(0xe9ecef, 0.4), mat(0x1c3f8f, 0.4)], glassBitM = new THREE.MeshStandardMaterial({ color: 0xbfe4ff, roughness: 0.05, metalness: 0.2, transparent: true, opacity: 0.8 });
const DEB = [];
function addDeb(geo, m, t0, p0, v0, spin) { const o = new THREE.Mesh(geo, m); o.castShadow = true; o.visible = false; scene.add(o); DEB.push({ o, t0, p0, v0, spin }); }
// snow / dust puffs
const puffTex = canvasTex(128, 128, g => { const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64); gr.addColorStop(0, 'rgba(255,255,255,0.9)'); gr.addColorStop(0.5, 'rgba(240,240,240,0.45)'); gr.addColorStop(1, 'rgba(230,230,230,0)'); g.fillStyle = gr; g.fillRect(0, 0, 128, 128); });
const PUFF = []; function addPuff(t0, p, r, life) { const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: puffTex, transparent: true, depthWrite: false, color: 0xf3f1ec })); s.visible = false; scene.add(s); PUFF.push({ s, t0, p, r, life }); }
// overlays for the explainers: rotor rings seen from above, path arrows, radio rings, the tower and its range, the tape
const ringA = new THREE.Mesh(new THREE.RingGeometry(ROTOR_R - 0.25, ROTOR_R, 64).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ color: 0xffd23a, transparent: true, opacity: 0.9, depthTest: false, toneMapped: false })),
  ringB = ringA.clone(); ringB.material = ringA.material.clone(); for (const r of [ringA, ringB]) { r.renderOrder = 22; r.visible = false; scene.add(r); }
function flatArrow(color) { const s = new THREE.Shape(); s.moveTo(-0.6, 0); s.lineTo(0.6, 0); s.lineTo(0.6, 6); s.lineTo(1.6, 6); s.lineTo(0, 9); s.lineTo(-1.6, 6); s.lineTo(-0.6, 6); s.closePath();
  const m = new THREE.Mesh(new THREE.ShapeGeometry(s).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.85, depthTest: false, toneMapped: false, side: THREE.DoubleSide })); m.renderOrder = 21; m.visible = false; scene.add(m); return m; }
const arrA = flatArrow(0xff4a3a), arrB = flatArrow(0xe8eef4);
const ringTex = canvasTex(256, 256, g => { g.strokeStyle = 'rgba(120,220,255,1)'; g.lineWidth = 14; g.beginPath(); g.arc(128, 128, 110, 0, Math.PI * 2); g.stroke(); });
const RINGS = []; for (let i = 0; i < 8; i++) { const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: ringTex, transparent: true, depthTest: false, depthWrite: false, toneMapped: false })); s.renderOrder = 23; s.visible = false; scene.add(s); RINGS.push(s); }
const qTex = canvasTex(256, 256, g => { g.fillStyle = '#ffd23a'; g.beginPath(); g.arc(128, 128, 110, 0, Math.PI * 2); g.fill(); g.fillStyle = '#1a1a1a'; g.font = 'bold 190px Arial'; g.textAlign = 'center'; g.fillText('?', 128, 195); });
const QS = [0, 1].map(() => { const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: qTex, transparent: true, depthTest: false, toneMapped: false })); s.renderOrder = 24; s.visible = false; scene.add(s); return s; });
const TOWER = new THREE.Group(); { const z = 2600, x = valleyX(z) + 40; TOWER.position.set(x, 0, z); scene.add(TOWER);
  box(6, 26, 6, 0, 13, 0, mat(0xdedad2, 0.7), 0.3, TOWER); box(10, 5, 10, 0, 28, 0, glassM, 0.4, TOWER); box(11, 0.8, 11, 0, 31, 0, mat(0xb8b2a8, 0.6), 0.2, TOWER); }
const RANGE = new THREE.Mesh(new THREE.SphereGeometry(1900, 48, 24, 0, Math.PI * 2, 0, Math.PI / 2), new THREE.MeshBasicMaterial({ color: 0x46b4ff, transparent: true, opacity: 0.16, depthWrite: false, side: THREE.DoubleSide, toneMapped: false }));
RANGE.position.copy(TOWER.position); RANGE.visible = false; scene.add(RANGE);
const pin = new THREE.Sprite(new THREE.SpriteMaterial({ map: canvasTex(256, 256, g => { g.fillStyle = '#ff4a3a'; g.beginPath(); g.arc(128, 100, 80, Math.PI, 0); g.lineTo(128, 250); g.closePath(); g.fill(); g.fillStyle = '#fff'; g.beginPath(); g.arc(128, 100, 34, 0, Math.PI * 2); g.fill(); }), depthTest: false, toneMapped: false })); pin.renderOrder = 25; pin.visible = false; scene.add(pin);
const tape = new THREE.Mesh(new THREE.BoxGeometry(16, 0.08, 0.02), new THREE.MeshBasicMaterial({ color: 0xf2c21a, toneMapped: false })); tape.visible = false; scene.add(tape);
const tipTrail = new THREE.Mesh(new THREE.TorusGeometry(ROTOR_R - 0.1, 0.07, 6, 64, Math.PI * 0.9).rotateX(Math.PI / 2), new THREE.MeshBasicMaterial({ color: 0xffb020, transparent: true, opacity: 0.85, toneMapped: false, depthWrite: false })); tipTrail.visible = false; scene.add(tipTrail);
const pole = new THREE.Group(); box(0.14, 3.2, 0.14, 0, 1.6, 0, mat(0x7a5a3a, 0.9), 0, pole); pole.visible = false; scene.add(pole);
const poleTop = new THREE.Group(); box(0.14, 1.1, 0.14, 0, 0.55, 0, mat(0x7a5a3a, 0.9), 0, poleTop); const flagTop = box(0.6, 0.4, 0.04, 0.3, 0.9, 0, mat(0xff6a1a, 0.7), 0, poleTop); poleTop.visible = false; scene.add(poleTop);
const bladePiece = box(ROTOR_R - 1.9, 0.045, 0.35, 0, 0, 0, bladeM, 0); bladePiece.visible = false;
// readout
const hudC = document.createElement('canvas'); hudC.width = 520; hudC.height = 440; const hudT = new THREE.CanvasTexture(hudC); hudT.colorSpace = THREE.SRGBColorSpace;
const hud = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: hudT, transparent: true, depthTest: false, depthWrite: false, toneMapped: false })); hud.renderOrder = 30; camera.add(hud); scene.add(camera); hud.visible = false;
function drawHud(rows, flag, fcol = '#d9241b') { const g = hudC.getContext('2d'); g.clearRect(0, 0, 520, 440); g.beginPath(); g.roundRect(6, 6, 508, 428, 34); g.fillStyle = 'rgba(8,14,22,0.74)'; g.fill(); g.lineWidth = 4; g.strokeStyle = 'rgba(160,200,235,0.55)'; g.stroke();
  let y = 30; for (const [lab, val, col] of rows) { g.fillStyle = '#9fb6c8'; g.font = '600 34px Arial, Helvetica, sans-serif'; g.fillText(lab, 34, y + 38); g.fillStyle = col || '#fff'; g.font = 'bold 62px Arial, Helvetica, sans-serif'; g.fillText(val, 34, y + 102, 452); y += 120; }
  if (flag) { g.font = 'bold 52px Arial, Helvetica, sans-serif'; const fw = Math.min(460, g.measureText(flag).width + 40); g.beginPath(); g.roundRect(30, 340, fw, 76, 16); g.fillStyle = fcol; g.fill(); g.fillStyle = '#fff'; g.fillText(flag, 50, 397, fw - 40); }
  hudT.needsUpdate = true; }
function fitHud() { const d = camera.near * 1.6, h = 2 * d * Math.tan(camera.fov * D2R / 2), w = h * camera.aspect, gw = 0.4 * w, gh = gw * 440 / 520; hud.scale.set(gw, gh, 1); hud.position.set(w / 2 - gw / 2 - 0.035 * w, h / 2 - 0.165 * h - gh / 2, -d); }
// ------------------------------------------------------------------ story: one shot per line
const G0 = 0.3, OM = -9.0;                                  // ground level at the pad; rotor turn rate on screen (rad/s, clockwise from above, slowed so the blades read)
for (const h of [HA, HB]) h.rotation.order = 'YXZ';
function setHeli(h, p, yaw, pitch = 0, roll = 0, ang = 0, blades = true) { h.visible = true; h.position.copy(p); h.rotation.set(pitch, yaw, roll); const U = h.userData;
  U.rot.rotation.y = ang; U.trot.rotation.x = ang * 5.3; U.blades.forEach(b => { b.visible = blades; b.userData.full.forEach(m => { m.visible = true; }); b.userData.stub.visible = false; }); U.disc.visible = blades; U.win.visible = true; }
// From the webcam video (USA Today still): both low over the snow, side-on to each other. A (red, cargo from Lukla) hovers about 2 m up,
// nose turned toward the camera-left; B (white with a blue tail, trekkers from base camp) hovers lower, side-on, and drifts sideways toward A
// until its blades reach A's cabin. tc < 0 = seconds before the strike. Far back in time each is still flying in (A from the south, B from the north).
const A_HOV = V(1.5, G0 + 2.0, -3.5), A_YAW = 2.5, B_YAW = -Math.PI / 2;
function stateA(tc) { if (tc < 0) { const s = -tc, far = Math.max(0, s - 3);
    return { p: V(A_HOV.x, A_HOV.y + 0.25 * Math.min(s, 3) + 7 * far + 0.6 * far * far, A_HOV.z + 22 * far + 2 * far * far), yaw: lerp(A_YAW, 0, smooth(3, 6, s)), pitch: 0.05 * Math.sin(s * 2.1), roll: 0.03 * Math.sin(s * 1.7), ang: OM * tc, bl: true }; }
  const roll = 80 * D2R * sm(clamp((tc - 0.65) / 0.8, 0, 1)), y = Math.max(G0 + 0.95 * Math.abs(Math.sin(roll)), A_HOV.y - 4.9 * tc * tc);
  return { p: V(A_HOV.x + 1.2 * sm(clamp(tc / 1.4, 0, 1)), y, A_HOV.z - 0.8 * sm(clamp(tc / 1.4, 0, 1))), yaw: A_YAW + 230 * D2R * sm(clamp(tc / 1.6, 0, 1)), pitch: 0, roll, ang: OM * Math.min(tc, 0.9), bl: tc < 0.9 }; }
function stateB(tc) { if (tc < 0) { const s = -tc, far = Math.max(0, s - 3.5);
    return { p: V(-2 - 3.0 * Math.min(s, 3.5) - 4 * far, G0 + 1.25 + 0.1 * Math.min(s, 3.5) + 7 * far + 0.6 * far * far, -22 * far - 2 * far * far), yaw: lerp(B_YAW, -Math.PI, smooth(3.5, 6.5, s)),
      pitch: -0.02, roll: -6 * D2R * (1 - smooth(2.5, 3.5, s)), ang: 3 * Math.PI / 4 + OM * tc, bl: true }; }
  const roll = -74 * D2R * sm(clamp((tc - 0.35) / 0.8, 0, 1)), y = Math.max(G0 + 0.9 * Math.abs(Math.sin(roll)), G0 + 1.25 - 4.9 * tc * tc);
  return { p: V(-2 + 1.6 * sm(clamp(tc / 1.1, 0, 1)), y, 0.6 * sm(clamp(tc / 1.1, 0, 1))), yaw: B_YAW - 35 * D2R * sm(clamp(tc / 1.2, 0, 1)), pitch: 0, roll, ang: 3 * Math.PI / 4, bl: false }; }
const hubOf = (st, h) => { const q = new THREE.Quaternion().setFromEuler(new THREE.Euler(st.pitch, st.yaw, st.roll, 'YXZ')); return st.p.clone().add(V(0, ROTOR_Y, 0).applyQuaternion(q)); };
// debris, set up once from the states above: B's blades break on A's cabin, A's glass and a few panels in their own paint, A's blades break when it rolls
{ const r = i => hash1(i * 13.37);
  const sb = stateB(0), hb = hubOf(sb); for (let k = 0; k < 3; k++) { const a = sb.ang + k * Math.PI * 2 / 3, q = new THREE.Quaternion().setFromEuler(new THREE.Euler(sb.pitch, sb.yaw, sb.roll, 'YXZ'));
    const dir = V(Math.cos(a), 0, -Math.sin(a)).applyQuaternion(q), tan = V(0, 1, 0).cross(dir);
    addDeb(new THREE.BoxGeometry(2.6, 0.05, 0.34), bitM[0], 0, hb.clone().addScaledVector(dir, 3.6), tan.multiplyScalar(13).add(dir.clone().multiplyScalar(5)).add(V(0, 3 + 2 * r(k), 0)), V(3 + 4 * r(k + 9), 9 + 6 * r(k + 3), 2));
    addDeb(new THREE.BoxGeometry(1.2, 0.05, 0.34), bitM[0], 0.02, hb.clone().addScaledVector(dir, 1.5), V(r(k + 30) - 0.5, 0.6, r(k + 40) - 0.5).multiplyScalar(5), V(5, 8, 3)); }
  const hit = V(1.1, G0 + 3.8, -3.1);
  for (let i = 0; i < 22; i++) addDeb(new THREE.BoxGeometry(0.08 + 0.14 * r(i), 0.015, 0.07 + 0.12 * r(i + 5)), glassBitM, 0.01 * r(i + 2), hit.clone().add(V((r(i + 7) - 0.5) * 1.0, (r(i + 8) - 0.5) * 0.6, (r(i + 9) - 0.5) * 1.0)), V(2 + 6 * r(i + 11), 1 + 4 * r(i + 12), -(1 + 5 * r(i + 13))), V(9 * r(i), 12 * r(i + 1), 7));
  for (let i = 0; i < 8; i++) addDeb(new THREE.BoxGeometry(0.2 + 0.3 * r(i + 50), 0.03, 0.15 + 0.25 * r(i + 52)), bitM[i % 2 ? 2 : 1], 0.02, hit.clone(), V(1 + 7 * r(i + 53), 2 + 4 * r(i + 54), -(r(i + 55)) * 7), V(6, 8, 5));
  const sa = stateA(0.9), ha = hubOf(sa); for (let k = 0; k < 3; k++) { const a = sa.ang + k * 2.1, dir = V(Math.cos(a), 0.3 * (r(k + 70) - 0.5), -Math.sin(a)).normalize();
    addDeb(new THREE.BoxGeometry(2.2, 0.05, 0.34), bitM[0], 0.9, ha.clone().addScaledVector(dir, 2.6), dir.clone().multiplyScalar(8).add(V(0, 4, 0)), V(4, 10, 3)); }
  // snow thrown up where each one hits the ground
  for (let i = 0; i < 12; i++) addPuff(0.42 + 0.04 * r(i + 80), V(-1.2 + (r(i + 81) - 0.5) * 6, G0 + 0.5, 0.2 + (r(i + 82) - 0.5) * 4), 3 + 3 * r(i + 83), 3.5);
  for (let i = 0; i < 16; i++) addPuff(0.65 + 0.08 * r(i + 90), V(2.6 + (r(i + 91) - 0.5) * 7, G0 + 0.5, -4.2 + (r(i + 92) - 0.5) * 6), 3.5 + 3.5 * r(i + 93), 4); }
function crash(tc, show = true) { const a = stateA(tc), b = stateB(tc);
  setHeli(HA, a.p, a.yaw, a.pitch, a.roll, a.ang, a.bl); setHeli(HB, b.p, b.yaw, b.pitch, b.roll, b.ang, tc < 0); 
  for (const d of DEB) { const dt = tc - d.t0; d.o.visible = show && dt >= 0; if (!d.o.visible) continue;
    const vy = d.v0.y, y0 = d.p0.y - G0 - 0.04, tl = (vy + Math.sqrt(vy * vy + 2 * 9.81 * Math.max(0, y0))) / 9.81, te = Math.min(dt, tl);
    d.o.position.copy(d.p0).addScaledVector(d.v0, te); d.o.position.y = d.p0.y + vy * te - 4.905 * te * te; if (dt > tl) { d.o.position.y = G0 + 0.04; d.o.position.addScaledVector(V(d.v0.x, 0, d.v0.z), 0.06 * (1 - Math.exp(-(dt - tl) * 4))); }
    d.o.rotation.set(d.spin.x * te, d.spin.y * te, d.spin.z * te); if (dt > tl) d.o.rotation.x = d.o.rotation.z = 0; }
  for (const p of PUFF) { const dt = tc - p.t0; p.s.visible = show && dt >= 0 && dt < p.life; if (!p.s.visible) continue; const k = dt / p.life;
    p.s.position.copy(p.p).add(V(0, 1.2 * k + 0.6, 0)); p.s.scale.setScalar(p.r * (0.4 + 1.1 * Math.sqrt(k))); p.s.material.opacity = 0.85 * (1 - k) * smooth(0, 0.08, dt); } }
function clearCrash() { for (const d of DEB) d.o.visible = false; for (const p of PUFF) p.s.visible = false; }
function shot(t) { const nb = beatAt(t), lt = t - B[nb], dur = DUR[nb], u = lt / dur;
  hud.visible = false; for (const o of [ringA, ringB, arrA, arrB, RANGE, pin, tape, tipTrail, pole, poleTop, bladePiece, ...RINGS, ...QS]) o.visible = false; arrB.scale.setScalar(1); HA.visible = HB.visible = false; clearCrash(); flagTop.visible = true;
  SKYU.uSet.value = 0; scene.background.set(0x9ec4ea); scene.fog.color.set(0xc4d6e8); scene.fog.near = 900; scene.fog.far = 7000; sun.color.set(0xfff2de); sun.intensity = 2.8; hemi.intensity = 0.6;
  let cp, ct, up = V(0, 1, 0), fov = 44, near = 0.1; camera.far = 9000;
  for (let i = 0; i < flags.length; i++) flags[i].rotation.z = 0.15 * Math.sin(t * 5 + i);
  sock.rotation.y = 0.15 * Math.sin(t * 2);
  const idle = (h, p, yaw = 0, pitch = 0) => setHeli(h, p, yaw, pitch, 0, OM * t, true);
  switch (nb) {
    case 0: { // hook: the webcam's view across the snow: B slides in from the left, side-on, into A hovering on the right; the strike at the end
      const tc = -1.0 + lt; crash(tc); cp = V(-1.5 + 0.6 * u, G0 + 2.0, 36); ct = V(-1.5, G0 + 3.0, -2); fov = 40;
      hud.visible = true; drawHud([['HEIGHT', Math.max(1, Math.round((stateB(Math.min(tc, 0)).p.y - G0) * 3.28)) + ' FT', '#ffd23a']], tc > 0 ? 'BLADES HIT' : null); break; }
    case 1: { // Pheriche from the air: the village, the pad, the peaks; both helicopters far off, still coming
      crash(-15 + lt, false); cp = V(240 - 50 * u, 120 - 15 * u, 300 - 70 * u); ct = V(10, 60, -400); fov = 50; near = 1;
      hud.visible = true; drawHud([['NOV 3, 2026', 'PHERICHE'], ['HEIGHT', '13,780 FT']]); break; }
    case 2: { // the two flights: A up the valley from Lukla with cargo, then B down from base camp with two trekkers
      const half = dur * 0.5; near = 0.5; fov = 46;
      if (lt < half) { const z = 1500 - 45 * lt, p = V(valleyX(z) + 10, 80, z); idle(HA, p, 0, -6 * D2R); cp = p.clone().add(V(-20 + 3 * u, 3, 11)); ct = p.clone().add(V(0, 1.2, -3));
        hud.visible = true; drawHud([['FROM', 'LUKLA'], ['CARRYING', 'CARGO', '#ff8a7a']]); }
      else { const z = -1500 + 45 * (lt - half), p = V(valleyX(z) - 10, 85, z); idle(HB, p, Math.PI, -6 * D2R); cp = p.clone().add(V(20 - 3 * u, 3, -11)); ct = p.clone().add(V(0, 1.2, 3));
        hud.visible = true; drawHud([['FROM', 'BASE CAMP'], ['CARRYING', '2 TREKKERS', '#7fb0ff']]); }
      break; }
    case 3: { // from straight above: same pad, same time, opposite sides; the rotor circles turn red when they overlap
      const tc = -3.6 + lt * 0.85; crash(tc, false); cp = V(0.01, 62, 1.5); ct = V(0, 0, 1.5); up = V(0, 0, -1); fov = 46; near = 1;
      const a = stateA(tc), b = stateB(tc), ha = hubOf(a), hb = hubOf(b), over = ha.distanceTo(hb) < 2 * ROTOR_R;
      for (const [r, h] of [[ringA, ha], [ringB, hb]]) { r.visible = true; r.position.copy(h); r.material.color.set(over ? 0xff3b2e : 0xffd23a); }
      arrB.visible = true; arrB.position.copy(stateB(tc).p).setY(G0 + 0.1).add(V(-4.5, 0, 3.2)); arrB.rotation.y = -Math.PI / 2; arrB.scale.setScalar(0.6); arrB.material.opacity = 0.85 * (1 - smooth(0.75, 0.95, u));
      hud.visible = true; drawHud([['ONE DRIFTED', 'SIDEWAYS', '#ffd23a']], over ? 'TOO CLOSE' : null); break; }
    case 4: { // slow motion: B's blades sweep into A's cabin a few feet off the ground; the blades break apart, both drop
      const tc = -0.75 + lt * 0.62; crash(tc); cp = V(10.5 - 1.0 * u, G0 + 3.6, 10.5 - 1.0 * u); ct = V(-0.3, G0 + 3.3, -1.8); fov = 46;
      hud.visible = true; drawHud([['OFF THE GROUND', 'ABOUT 8 FT', '#ffd23a'], ['SPEED', 'SLOWED DOWN']], tc > 0 ? 'BLADES HIT' : null); break; }
    case 5: { // after: both on their sides in the snow, the snow cloud settling (no people shown)
      const tc = 1.8 + lt; crash(tc); cp = V(20 + 5 * u, G0 + 7 + 1.5 * u, 19 + 4 * u); ct = V(0, G0 + 1.5, 1.5); fov = 40;
      hud.visible = true; drawHud([['KILLED', '1 TREKKER', '#ff6a5c'], ['HURT', '3 PEOPLE', '#ffd23a']], 'BOTH PILOTS HURT', '#7a4a1a'); break; }
    case 6: { // explainer: one helicopter idling on the pad, rotor turning
      idle(HA, V(0, G0, 0)); const a = -2.3 + 0.5 * u; cp = V(Math.sin(a) * 13, G0 + 1.4, Math.cos(a) * 13); ct = V(0, G0 + 2.6, 0); fov = 44;
      hud.visible = true; drawHud([['ROTOR', 'SPINNING', '#ffd23a']]); break; }
    case 7: { // from above: the rotor turning (shown slowed down)
      setHeli(HA, V(0, G0, 0), 0, 0, 0, -3.2 * t, true); HA.userData.disc.visible = true; cp = V(0.01, G0 + 17 - 2 * u, 0.6); ct = V(0, G0, 0.6); up = V(0, 0, -1); fov = 48;
      hud.visible = true; drawHud([['SPINS', 'NEARLY 400', '#ffd23a'], ['', 'TIMES A MINUTE']], 'SHOWN SLOWED', '#2a5a8a'); break; }
    case 8: { // the tips: nearly 500 mph (shown slowed); one touch on a pole: the outer blade snaps off and the pole top breaks away
      const th = 0.6, w = -2.6, thit = 0.45,   // the FIRST blade to reach the pole breaks (the one before it passed it just before the shot starts)
      ang = th + w * (lt - thit), hit = lt >= thit, k = lt - thit;
      setHeli(HA, V(0, G0, 0), 0, 0, 0, ang, true); HA.userData.disc.visible = false;
      const hub = V(0, G0 + ROTOR_Y, 0), d0 = V(Math.cos(th), 0, -Math.sin(th)), vt = V(-Math.sin(th), 0, -Math.cos(th)).multiplyScalar(w);
      tipTrail.visible = true; tipTrail.position.copy(hub); tipTrail.rotation.y = ang + Math.PI * 0.9; tipTrail.material.opacity = hit ? 0.85 * (1 - smooth(0, 0.3, k)) : 0.85;
      const base = V(0, G0 - 0.3, 0).addScaledVector(d0, 4.6); pole.visible = poleTop.visible = true; pole.position.copy(base); poleTop.position.copy(base).add(V(0, 3.2, 0)); poleTop.rotation.set(0, 0, 0);
      if (hit) { const a0 = HA.userData.blades[0]; a0.userData.full.forEach(m => { m.visible = false; }); a0.userData.stub.visible = true;
        bladePiece.visible = true; const tk = Math.min(k, 1.2); bladePiece.position.copy(hub).addScaledVector(d0, 3.55).addScaledVector(vt.clone().multiplyScalar(0.9), tk).add(V(0, 1.2 * tk - 4.9 * tk * tk, 0)); bladePiece.position.y = Math.max(G0 + 0.05, bladePiece.position.y);
        bladePiece.rotation.set(0, th + 3.2 * w * tk, 2.5 * tk);
        const pk = Math.min(k, 1.0); poleTop.position.add(vt.clone().normalize().multiplyScalar(4.5 * pk)).add(V(0, 1.5 * pk - 4.9 * pk * pk, 0)); poleTop.position.y = Math.max(G0, poleTop.position.y); poleTop.rotation.set(-2.2 * pk, 0, 1.4 * pk); }
      cp = base.clone().add(V(-2.6 + 0.4 * u, 4.4, -7.5)); ct = base.clone().add(V(0.6, 3.0, 2.2)); fov = 50;
      hud.visible = true; drawHud([['BLADE TIPS', 'NEARLY 500 MPH', '#ffd23a'], ['', 'SHOWN SLOWED']], hit ? 'ONE TOUCH' : null); break; }
    case 9: { // the map from above: the nearest control tower's range never reaches Pheriche; the pilots call each other by radio
      crash(-12 + lt, false); RANGE.visible = true; pin.visible = true; pin.position.set(0, 150, 0); pin.scale.setScalar(260);
      cp = V(150, 9000, 1250); ct = V(0, 0, 1250); up = V(0, 0, -1); fov = 26; near = 20; camera.far = 25000; scene.fog.near = 20000; scene.fog.far = 30000;
      for (let i = 0; i < 4; i++) { const k = ((lt * 0.8 + i * 0.25) % 1); const s = RINGS[i]; s.visible = true; s.position.set(0, 160, 0); s.scale.setScalar(150 + 650 * k); s.material.opacity = 1 - k; }
      hud.visible = true; drawHud([['CONTROL TOWER', 'OUT OF RANGE', '#ff6a5c'], ['PILOTS TALK', 'BY RADIO', '#7fd3ff']]); break; }
    case 10: { // early report: a mix-up between the two pilots (radio rings, question marks)
      const tc = -3.8 + lt * 0.5; crash(tc, false); cp = V(48, 72, 0.5); ct = V(0, 12, 0.5); up = V(0, 0, -1); fov = 50; near = 0.5;
      const ha = hubOf(stateA(tc)), hb = hubOf(stateB(tc));
      for (let i = 0; i < 6; i++) { const k = ((lt * 1.1 + (i % 3) / 3) % 1), s = RINGS[i]; s.visible = true; s.position.copy(i < 3 ? ha : hb).add(V(0, 1, 0)); s.scale.setScalar(3 + 20 * k); s.material.opacity = 0.9 * (1 - k); }
      QS[0].visible = QS[1].visible = u > 0.3; QS[0].position.copy(ha).add(V(0, 6, 0)); QS[1].position.copy(hb).add(V(0, 6, 0)); for (const q of QS) q.scale.setScalar(7 * smooth(0.3, 0.42, u));
      hud.visible = true; drawHud([['EARLY REPORT', 'PILOT MIX-UP', '#ffd23a']], 'NOT FINAL', '#2a5a8a'); break; }
    case 11: { // still under investigation: tape across the foreground, the wrecks behind
      crash(5); cp = V(19 - 1.5 * u, G0 + 1.8, 15 - u); ct = V(0, G0 + 1.4, 1.5); fov = 38;
      { const d = ct.clone().sub(cp).setY(0).normalize(); tape.visible = true; tape.position.copy(cp).addScaledVector(d, 5).setY(G0 + 1.0); tape.rotation.y = Math.atan2(-d.x, -d.z); }
      hud.visible = true; drawHud([['CAUSE', 'UNDER', '#ffd23a'], ['', 'INVESTIGATION', '#ffd23a']]); break; }
    case 12: { // no roads: a helicopter lifting off the pad and heading down the valley; another one far off
      const k = sm(clamp(u * 1.2, 0, 1)); idle(HA, V(0, G0 + 7 * k * k, 9 * k * k), Math.PI, -7 * D2R * k);
      idle(HB, V(-40, 170, -700 + 140 * u), Math.PI, -5 * D2R); cp = V(-6, G0 + 2.4, 31); ct = V(0, G0 + 4.5, 0); fov = 46;
      hud.visible = true; drawHud([['ROADS', 'NONE', '#ff6a5c'], ['WAY IN OR OUT', 'HELICOPTER', '#2fbf71']]); break; }
    case 13: { // dusk over the empty pad and the peaks
      SKYU.uSet.value = 1; scene.background.set(0xd98a62); scene.fog.color.set(0xc9958a); sun.color.set(0xff9a5a); sun.intensity = 1.6; hemi.intensity = 0.5; scene.fog.near = 3000; scene.fog.far = 14000;
      cp = V(-8, G0 + 3, 30 - 3 * u); ct = V(20, 420, -3000); fov = 50; near = 0.5; flagTop.visible = false; break; }
  }
  SKY.position.copy(cp);
  camera.position.copy(cp); camera.up.copy(up); camera.lookAt(ct); camera.fov = fov; camera.near = near; camera.updateProjectionMatrix();
  return { b: nb, focus: nb === 9 ? V(0, 0, 1250) : nb === 13 ? V(0, G0, 0) : ct }; }
// ------------------------------------------------------------------ look + frame I/O
import { makeLook } from '/look.js';
const LOOK = makeLook(THREE, renderer, scene, camera, W, H, { overlays: [hud, ringA, ringB, arrA, arrB, pin, ...RINGS, ...QS], aperture: 0.0005, maxblur: 0.005, rim: false, noAO: [window.__SKY, RANGE, ...PUFF.map(p => p.s)] });
let FOC = V(0, 1, 0), WIDE = false;
function update(t) { t = clamp(t, 0, TOTAL - 1e-3); const r = shot(t); fitHud();
  const at = r.focus; sun.position.copy(at).add(V(35, 60, 25)); sun.target.position.copy(at); sun.target.updateMatrixWorld(); FOC = r.focus; WIDE = [1, 2, 9, 13].includes(r.b); return r; }
function stepTo(i) { return update(i / FPS); }
const draw = () => LOOK.render(FOC, { ao: !WIDE, dof: !WIDE });
const gl = renderer.getContext(), px = new Uint8Array(W * H * 4);
window.renderAll = async (f0, f1) => { for (let i = f0; i < f1; i++) { stepTo(i); draw(); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); await fetch('/frame', { method: 'POST', body: px }); } return 'ok'; };
window.renderAtT = t => { stepTo(Math.round(t * FPS)); draw(); return renderer.domElement.toDataURL('image/png'); };
window.dbg = { THREE, scene, camera, G, shot, HA, HB };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS); window.READY = true;
window.SCN = { THREE, scene, camera, stepTo, renderer, FPS, B, DUR, TOTAL };
