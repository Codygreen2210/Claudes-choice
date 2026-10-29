// "Your pan just caught fire, so you grab a cup of water." - a 3D Short: water on a grease fire, and the right way (burner off, lid on).
//   grease.html?w=1080&h=1920            (times from grease/times.json; one shot per narration line)
// Beats: 0 pan on fire; he looks up from his phone, grabs the cup (hook) | 1 throws it; cutaway: the water sinks under the oil
//        2 cutaway: it boils and blasts into steam (1,700x) | 3 the fireball; he jumps back | 4 rewind; burner off, lid slid on
//        5 cutaway: no air, flames die; hands off | 6 too big: flames up the cabinets, he's gone | 7 on his phone, the oil smokes, catches (loops)
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { loadGuy } from '/guy3d.js';

const Q = new URLSearchParams(location.search);
const W = +Q.get('w') || 720, H = +Q.get('h') || 1280;
const FPS = 30;
const TIMES = await (await fetch('/grease/times.json')).json();
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
// ================================================================== GREASE FIRE
// ------------------------------------------------------------------ the stove top in the counter, the pan, the oil, a cup of water, a lid, his phone
renderer.localClippingEnabled = true;
const TOPC = 0.945;                                                // counter top height
const STOVE = V(-2.6, TOPC, -0.6);                                 // cooktop centre (black glass in the counter)
const PAN = V(-2.56, TOPC + 0.006, -0.5);                          // pan centre, on the front-left burner (his left is +z)
const PANR = 0.125, PANH = 0.055, OILH = 0.03;
const CUP0 = V(-2.47, TOPC, -0.93);                                // the cup of water, on the counter to his right
const LID0 = V(-2.46, TOPC + 0.004, -0.21);                        // the pot lid, flat on the counter to his left
const KNOB = V(-2.4, TOPC + 0.004, -0.5);                         // the pan burner's knob, on the counter top in front of the burners (tilted toward him)
const KAX = V(0.6, 0.8, 0).normalize();                           // knob axis: up and toward him
const STANDP = V(-2.03, 0, -0.62);                                 // where he stands (facing -x)
const CUTP = new THREE.Plane(V(0, 0, -1), PAN.z);                  // cutaway: keeps the half of the pan away from the camera (z < PAN.z)
const steel = new THREE.MeshStandardMaterial({ color: 0x9aa0a8, roughness: 0.3, metalness: 0.9, side: THREE.DoubleSide });
const panDark = new THREE.MeshStandardMaterial({ color: 0x2a2a2e, roughness: 0.45, metalness: 0.6, side: THREE.DoubleSide });
const cooktop = new THREE.Group(); scene.add(cooktop);
{ const glass = new THREE.Mesh(new RoundedBoxGeometry(0.5, 0.012, 0.6, 2, 0.004), new THREE.MeshStandardMaterial({ color: 0x0c0c0e, roughness: 0.12, metalness: 0.2 }));
  glass.position.set(STOVE.x, TOPC - 0.003, STOVE.z); glass.receiveShadow = true; cooktop.add(glass);
  for (const [dx, dz, r] of [[0.06, 0.1, 0.1], [0.06, -0.15, 0.085], [-0.12, 0.13, 0.08], [-0.12, -0.12, 0.09]]) {
    const ring = new THREE.Mesh(new THREE.TorusGeometry(r, 0.004, 6, 48).rotateX(Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0x3a3a3e, roughness: 0.6 }));
    ring.position.set(STOVE.x + dx, TOPC + 0.004, STOVE.z + dz); cooktop.add(ring); } }
// the hot coil under the pan glows red while the burner is on
const coilM = new THREE.MeshStandardMaterial({ color: 0x2a0a06, emissive: 0xff3a10, emissiveIntensity: 1.2, roughness: 0.6 });
const coil = new THREE.Mesh(new THREE.TorusGeometry(0.075, 0.006, 6, 48).rotateX(Math.PI / 2), coilM); coil.position.set(PAN.x, TOPC + 0.004, PAN.z); scene.add(coil);
// knobs on the counter front (the pan's knob turns)
const knobs = [];
{ const strip = new THREE.Mesh(new RoundedBoxGeometry(0.05, 0.012, 0.6, 2, 0.004), new THREE.MeshStandardMaterial({ color: 0x18181a, roughness: 0.3, metalness: 0.2 })); strip.position.set(KNOB.x, TOPC + 0.002, -0.6); scene.add(strip); }
for (const dz of [0.1, -0.15, 0.25, -0.3]) { const k = new THREE.Group(); k.position.set(KNOB.x, KNOB.y, -0.6 + dz); k.quaternion.setFromUnitVectors(V(1, 0, 0), KAX); scene.add(k);
  const spin = new THREE.Group(); k.add(spin); k.userData.spin = spin;
  const b = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.023, 0.024, 24).rotateZ(Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0x1c1c20, roughness: 0.35, metalness: 0.3 })); b.position.x = 0.012; spin.add(b);
  const ridge = new THREE.Mesh(new THREE.BoxGeometry(0.008, 0.034, 0.007), new THREE.MeshStandardMaterial({ color: 0xd8d8dc, roughness: 0.4 })); ridge.position.x = 0.025; spin.add(ridge); knobs.push(k); }
const panKnob = knobs[0];                                          // z = -0.5 (the pan's burner)
// the pan: lathe body, handle to his right (-z), oil inside
const pan = new THREE.Group(); pan.position.copy(PAN); scene.add(pan);
const panBody = new THREE.Mesh(new THREE.LatheGeometry([V(0, 0, 0), V(PANR - 0.012, 0, 0), V(PANR - 0.002, 0.008, 0), V(PANR + 0.004, PANH, 0), V(PANR + 0.007, PANH + 0.003, 0)].map(v => new THREE.Vector2(v.x, v.y)), 56), panDark);
panBody.castShadow = true; pan.add(panBody);
const panHandle = new THREE.Mesh(new RoundedBoxGeometry(0.03, 0.018, 0.17, 2, 0.008), new THREE.MeshStandardMaterial({ color: 0x1a1a1c, roughness: 0.5 }));
panHandle.position.set(0, PANH - 0.008, -(PANR + 0.085)); panHandle.rotation.x = -0.12; pan.add(panHandle);
const oilM = new THREE.MeshStandardMaterial({ color: 0xc89a2a, emissive: 0x5a2a00, emissiveIntensity: 0.3, roughness: 0.08, metalness: 0.1, transparent: true, opacity: 0.82, side: THREE.DoubleSide });
const oil = new THREE.Mesh(new THREE.CylinderGeometry(PANR - 0.01, PANR - 0.012, OILH, 48), oilM); oil.position.y = 0.004 + OILH / 2; pan.add(oil);
// the cut faces (cutaway only): the oil as a see-through gold slab, the pan floor and walls as dark strips
const cutFaces = new THREE.Group(); cutFaces.position.copy(PAN); scene.add(cutFaces); cutFaces.visible = false;
{ const oc = new THREE.Mesh(new THREE.PlaneGeometry(2 * (PANR - 0.01), OILH), new THREE.MeshStandardMaterial({ color: 0xd8a432, emissive: 0x6a3a00, emissiveIntensity: 0.5, roughness: 0.3, transparent: true, opacity: 0.55, depthWrite: false, side: THREE.DoubleSide }));
  oc.position.set(0, 0.004 + OILH / 2, 0.0005); cutFaces.add(oc);
  const dm = new THREE.MeshStandardMaterial({ color: 0x3a3a40, roughness: 0.4, metalness: 0.5, side: THREE.DoubleSide });
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(2 * PANR, 0.004), dm); fl.position.set(0, 0.002, 0.0006); cutFaces.add(fl);
  for (const sx of [-1, 1]) { const wl = new THREE.Mesh(new THREE.PlaneGeometry(0.004, PANH), dm); wl.position.set(sx * (PANR + 0.002), PANH / 2, 0.0006); wl.rotation.z = -sx * 0.07; cutFaces.add(wl); } }
// water: the blob that flies from the cup, then sinks under the oil (cutaway), then flashes to steam
const waterM = new THREE.MeshPhysicalMaterial({ color: 0x5fb4ff, emissive: 0x0a3a80, emissiveIntensity: 0.35, roughness: 0.05, transmission: 0.3, transparent: true, opacity: 0.85 });
const water = new THREE.Mesh(new THREE.SphereGeometry(1, 28, 20), waterM); scene.add(water);
const steamM = new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xe8f2ff, emissiveIntensity: 0.7, roughness: 0.9, transparent: true, opacity: 0.9, depthWrite: false });
const steamBall = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 24), steamM); scene.add(steamBall);
const bubbles = new THREE.Group(); scene.add(bubbles);
for (let i = 0; i < 14; i++) bubbles.add(new THREE.Mesh(new THREE.SphereGeometry(1, 12, 8), steamM));
// the cup (glass) with water in it
const cup = new THREE.Group(); scene.add(cup);
const CUPR = 0.036, CUPH = 0.11;
{ const g = new THREE.Mesh(new THREE.CylinderGeometry(CUPR, CUPR * 0.88, CUPH, 28, 1, true), new THREE.MeshPhysicalMaterial({ color: 0xdff2fa, roughness: 0.05, transmission: 0.5, transparent: true, opacity: 0.4, side: THREE.DoubleSide }));
  g.position.y = CUPH / 2; cup.add(g);
  const bot = new THREE.Mesh(new THREE.CylinderGeometry(CUPR * 0.88, CUPR * 0.88, 0.008, 28), new THREE.MeshPhysicalMaterial({ color: 0xdff2fa, roughness: 0.05, transparent: true, opacity: 0.5 })); bot.position.y = 0.004; cup.add(bot); }
const cupWater = new THREE.Mesh(new THREE.CylinderGeometry(CUPR * 0.94, CUPR * 0.86, CUPH * 0.7, 28), waterM); cupWater.position.y = CUPH * 0.36; cup.add(cupWater);
// the lid: a steel dome with a black knob
const lid = new THREE.Group(); scene.add(lid);
const LIDR = PANR + 0.012;
{ const dome = new THREE.Mesh(new THREE.SphereGeometry(LIDR / Math.sin(0.5), 48, 12, 0, Math.PI * 2, 0, 0.5), steel); dome.position.y = -LIDR / Math.tan(0.5); dome.castShadow = true; lid.add(dome);
  const rim = new THREE.Mesh(new THREE.TorusGeometry(LIDR, 0.004, 6, 48).rotateX(Math.PI / 2), steel); lid.add(rim);
  const kn = new THREE.Mesh(new RoundedBoxGeometry(0.05, 0.022, 0.026, 2, 0.008), new THREE.MeshStandardMaterial({ color: 0x1a1a1c, roughness: 0.5 })); kn.position.y = LIDR * (1 - Math.cos(0.5)) / Math.sin(0.5) + 0.016; lid.add(kn);
  const post = new THREE.Mesh(new THREE.CylinderGeometry(0.006, 0.006, 0.014, 10), steel); post.position.y = kn.position.y - 0.012; lid.add(post); }
const LIDKNOBY = LIDR * (1 - Math.cos(0.5)) / Math.sin(0.5) + 0.016;    // knob centre above the rim
// his phone (scrolling a feed while the pan heats)
const phone = new THREE.Group(); scene.add(phone);
const phoneCanvas = document.createElement('canvas'); phoneCanvas.width = 160; phoneCanvas.height = 330;
const phoneTex = new THREE.CanvasTexture(phoneCanvas); phoneTex.colorSpace = THREE.SRGBColorSpace;
function drawPhone(scroll) { const g = phoneCanvas.getContext('2d'); g.fillStyle = '#111418'; g.fillRect(0, 0, 160, 330);
  for (let i = -1; i < 5; i++) { const y = i * 96 - (scroll % 96); g.fillStyle = ['#e85a4a', '#4a9ae8', '#f2c14a', '#6ad08a', '#b06ae8'][(i + Math.floor(scroll / 96) + 50) % 5]; g.fillRect(10, y + 8, 140, 64); g.fillStyle = '#3a3f48'; g.fillRect(10, y + 78, 90, 8); }
  phoneTex.needsUpdate = true; }
{ box(0.072, 0.152, 0.009, 0, 0, 0, mat(0x1c1d22, 0.3, 0.6), 0.004, phone); const s = new THREE.Mesh(new THREE.PlaneGeometry(0.064, 0.142), new THREE.MeshBasicMaterial({ map: phoneTex, toneMapped: false })); s.position.z = 0.0048; phone.add(s); }
drawPhone(0); let phoneState = -1;

// ------------------------------------------------------------------ fire and smoke: camera-facing puffs, placed from time alone (any frame renders the same)
const FIREN = 900, SMOKEN = 400;
function puffs(n, frag, blending) {
  const geo = new THREE.InstancedBufferGeometry().copy(new THREE.PlaneGeometry(1, 1)); geo.instanceCount = 0;
  const P = new Float32Array(n * 4), O = new Float32Array(n * 4), aP = new THREE.InstancedBufferAttribute(P, 4), aO = new THREE.InstancedBufferAttribute(O, 4);
  aP.setUsage(THREE.DynamicDrawUsage); aO.setUsage(THREE.DynamicDrawUsage); geo.setAttribute('aP', aP); geo.setAttribute('aO', aO);
  const m = new THREE.ShaderMaterial({ uniforms: { uT: { value: 0 }, uGain: { value: 1 } }, transparent: true, depthWrite: false, blending, clipping: true,
    vertexShader: `#include <clipping_planes_pars_vertex>
      attribute vec4 aP, aO; varying vec2 vUv; varying vec4 vO;
      void main(){ vec3 c = aP.xyz; vec3 R = vec3(viewMatrix[0][0], viewMatrix[1][0], viewMatrix[2][0]), U = vec3(viewMatrix[0][1], viewMatrix[1][1], viewMatrix[2][1]);
        float a = aO.w * 6.2831; vec2 p = mat2(cos(a), -sin(a), sin(a), cos(a)) * position.xy; vec3 w = c + (R * p.x + U * p.y) * aP.w;
        vUv = uv; vO = aO; vec4 mvPosition = viewMatrix * vec4(w, 1.0);
        #include <clipping_planes_vertex>
        gl_Position = projectionMatrix * mvPosition; }`,
    fragmentShader: `#include <clipping_planes_pars_fragment>
      uniform float uT, uGain; ${GLSLN} varying vec2 vUv; varying vec4 vO;
      void main(){
        #include <clipping_planes_fragment>
        ${frag} }` });
  const mesh = new THREE.Mesh(geo, m); mesh.frustumCulled = false; mesh.renderOrder = 6; scene.add(mesh);
  let k = 0;
  return { mesh, m, begin() { k = 0; }, add(p, size, heat, alpha, seed) { if (k >= n || alpha < 0.004) return; P.set([p.x, p.y, p.z, size], k * 4); O.set([heat, alpha, 0, seed], k * 4); k++; },
    end() { geo.instanceCount = k; aP.needsUpdate = true; aO.needsUpdate = true; } };
}
// flame: hot white-yellow core to orange to deep red, ragged noisy edge; additive
const FIRE = puffs(FIREN, `vec2 p = vUv * 2.0 - 1.0; float s = vO.w * 17.0;
  float n = vn(p * 2.5 + vec2(s, s * 0.7) - vec2(0.0, uT * 4.0)) * 0.65 + vn(p * 6.0 + s * 3.0 - vec2(0.0, uT * 7.0)) * 0.35;
  float r = length(p * vec2(1.0, 0.85)) + (n - 0.5) * 0.75;
  float m = 1.0 - smoothstep(0.25, 0.95, r); if (m < 0.01) discard;
  float h = vO.x * (0.75 + 0.5 * n) * (1.0 - 0.45 * smoothstep(0.0, 1.0, r));
  vec3 col = mix(vec3(0.55, 0.06, 0.01), vec3(1.0, 0.42, 0.06), smoothstep(0.1, 0.55, h));
  col = mix(col, vec3(1.0, 0.86, 0.45), smoothstep(0.55, 0.95, h));
  gl_FragColor = vec4(col * m * vO.y * 1.1 * uGain, 1.0);`, THREE.AdditiveBlending);
// smoke: soft grey, darker at the core
const SMOKE = puffs(SMOKEN, `vec2 p = vUv * 2.0 - 1.0; float s = vO.w * 13.0;
  float n = vn(p * 2.0 + s - vec2(0.0, uT * 0.8)) * 0.6 + vn(p * 5.0 - s * 2.0) * 0.4;
  float r = dot(p, p) + (n - 0.5) * 0.8; float a = (1.0 - smoothstep(0.25, 0.95, r)) * vO.y; if (a < 0.004) discard;
  vec3 col = mix(vec3(0.16, 0.15, 0.15), vec3(0.42, 0.4, 0.38), vO.x) * (0.8 + 0.4 * n);
  gl_FragColor = vec4(col, a);`, THREE.NormalBlending);
FIRE.mesh.renderOrder = 7;
const fireLight = new THREE.PointLight(0xff7a2a, 0, 6, 1.7); scene.add(fireLight);

// pan fire: level 0..1 (0.35 = a pan just caught, 1 = flames to his chest, 2.5 = up the cabinets); squash 0..1 pushes it down under a lid
function panFire(t, level, squash = 0) {
  if (level < 0.01) return;
  const n = Math.round(160 * Math.min(1.6, level));
  const H = (0.12 + 0.42 * level) * (1 - 0.92 * squash), R0 = PANR * 0.85;
  for (let i = 0; i < n; i++) { const sp = 1.3 + 0.9 * hash1(i * 7.1), a = ((t * sp + hash1(i * 3.3)) % 1 + 1) % 1;   // age 0..1
    const ang = hash1(i * 5.7) * Math.PI * 2, rr = Math.sqrt(hash1(i * 9.1)) * R0 * (1 - 0.55 * a);
    const w = vn1(t * 2.3 + i * 0.37, 3) * 0.035 * a * level, w2 = vn1(t * 2.1 + i * 0.53, 5) * 0.035 * a * level;
    const p = V(PAN.x + Math.cos(ang) * rr + w, PAN.y + 0.022 + a * H, PAN.z + Math.sin(ang) * rr + w2);
    const size = (0.05 + 0.06 * level) * (1 - 0.55 * a) * (0.7 + 0.6 * hash1(i * 2.9)) * (1 - 0.5 * squash);
    FIRE.add(p, size, 1 - a * 0.9, Math.sin(Math.PI * Math.min(1, a * 1.15)) ** 0.6 * Math.min(1, level * 2.2), hash1(i * 4.4)); }
}
// the fireball: s = seconds since the water hit (0..), out = 0..1 how far it got (rewind plays it backward)
function fireball(s, t, frac = 1) {
  if (s < 0) return;
  for (let i = 0; i < Math.round(340 * frac); i++) { const d0 = hash1(i * 3.7), ang = hash1(i * 6.1) * Math.PI * 2;
    const delay = 0.05 * hash1(i * 8.3), u = Math.max(0, s - delay); if (u <= 0) continue;
    const dir = V(Math.cos(ang) * (0.35 + 0.65 * d0), 1.5 + 1.2 * hash1(i * 2.2), Math.sin(ang) * (0.35 + 0.65 * d0)).normalize();
    const reach = (0.5 + 0.7 * hash1(i * 5.3)) * (1 - Math.exp(-u * 3.2));
    const p = PAN.clone().addScaledVector(dir, reach).add(V(0, 0.25 * u * u, 0));
    p.y = Math.min(p.y, 2.0 - 0.1 * hash1(i));                     // the cabinets (bottom 1.8) and the ceiling spread it out
    if (p.y > 1.75) { p.x += (p.y - 1.75) * 0.4; }
    const life = 1.3 + 1.0 * hash1(i * 7.7), a = u / life; if (a > 1) continue;
    const size = (0.12 + 0.35 * Math.sqrt(a)) * (0.7 + 0.6 * hash1(i * 4.9));
    FIRE.add(p, size * 0.85, 1 - 0.85 * a, 0.36 * Math.sin(Math.PI * Math.min(1, a * 1.3 + 0.1)) ** 0.5 * (1 - a * 0.4), hash1(i * 1.3));
    if (a > 0.45 && i % 3 === 0) SMOKE.add(p.clone().add(V(0, 0.15 * (a - 0.45), 0)), size * 1.3, 0.2, 0.5 * (a - 0.45) * (1 - a) * 4, hash1(i * 2.6)); }
}
// smoke curling off hot oil (before it catches) or after the lid goes on
function panSmoke(t, k, top = 0) {
  if (k < 0.01) return;
  for (let i = 0; i < 60; i++) { const a = ((t * (0.35 + 0.2 * hash1(i * 3.1)) + hash1(i * 1.9)) % 1 + 1) % 1, ang = hash1(i * 5.1) * Math.PI * 2, rr = Math.sqrt(hash1(i * 7.3)) * PANR * 0.8;
    const p = V(PAN.x + Math.cos(ang) * rr + vn1(t * 0.9 + i, 2) * 0.06 * a, PAN.y + 0.03 + top + a * 0.55, PAN.z + Math.sin(ang) * rr + vn1(t * 0.8 + i, 4) * 0.06 * a);
    SMOKE.add(p, 0.05 + 0.18 * a, 0.75, Math.sin(Math.PI * a) * 0.45 * k, hash1(i * 6.6)); }
}

// ------------------------------------------------------------------ the story
const T_REACH = 0.95, T_LIFT = 1.6;                               // beat 0: reaches for the cup / lifts it toward the pan
const T_THROW = 0.18, T_HIT = 0.5, T_CUT1 = 0.82;                 // beat 1: throws, the water hits the oil, cut to the cutaway
const T_FLASH = 1.55;                                             // beat 2: the water flashes to steam
const T_RW = 0.0;                                                 // beat 4: (no rewind: a straight cut to the right way)
const T_KNOB = 0.75, T_LID = 1.25;                                // beat 4: hand on the knob / lid slides over
const T_OUT = 0.35;                                               // beat 5: flames die under the lid
const T_IGNITE = DUR[7] - 0.35;                                   // beat 7: the pan catches (the loop goes on into beat 0)
const LOOPSEED = { R: null, L: null };
function blinkAt(s) { const u = ((s + 40) % 3.7) / 0.16; return u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0; }
const F = fwdOf(90), Rt = rightOf(90), UP = V(0, 1, 0);           // his forward (-x), his right (-z), up
const STAND1 = addPose(STAND, { spine1: [-4, 0, 0], neck: [6, 0, 0] });
const TILT = (v, deg) => v.clone().applyAxisAngle(F, deg * D2R);   // roll a direction about his forward axis

// hand builders ------------------------------------------------------
// the cup in his right hand: palm on its side, thumb side up, cup axis along -w; tilt rolls it toward his left (the pan)
const CUPGRIP = 0.012;
function cupHand(c, tilt = 0) { const n0 = Rt.clone().negate().addScaledVector(F, 0.25).normalize(), up = UP.clone();
  const n = TILT(n0, -tilt), axis = TILT(up, -tilt), u = new THREE.Vector3().crossVectors(axis, n).negate().normalize();
  return { S: 'R', p: c.clone().addScaledVector(axis, CUPH * 0.45).addScaledVector(n, -(CUPR + CUPGRIP)), n, u, c: 48, th: 40, opp: 40, memAbs: 'cupR', seed: A(40, 15, 0, 80, 10) }; }
// his phone in the left hand, screen toward his face
function phoneHand() { const hd = wp(G.bones.head), n = UP.clone().multiplyScalar(0.62).addScaledVector(F, -0.78).normalize(), u = F.clone().multiplyScalar(0.78).addScaledVector(UP, 0.62).normalize();
  return { S: 'L', p: hd.clone().addScaledVector(F, 0.27).addScaledVector(Rt, 0.04).add(V(0, -0.32, 0)), n, u, c: 30, th: 35, memAbs: 'phoneL', seed: A(40, 10, 0, 110, -40) }; }
// pinching the pan's knob (index on top of it, finger down and forward); roll = how far it's turned (deg)
let KSUP = -58;
function knobHand(roll = 0) {                                     // palm over the knob like a jar lid, fingers around it; turning it = rolling the forearm
  const face = KNOB.clone().addScaledVector(KAX, 0.026), u0 = Rt.clone().negate().addScaledVector(KAX, Rt.dot(KAX)).normalize();   // fingers toward his left (easy on the wrist)
  const u = u0.applyAxisAngle(KAX, roll * D2R), n = KAX.clone().negate().applyAxisAngle(u, -KSUP * D2R);   // a little supinated (thumb side up)
  return { S: 'R', p: face.clone().addScaledVector(KAX, 0.03).addScaledVector(u, -0.03), u, n, c: 58, th: 60, opp: 35, memAbs: 'knobR', seed: A(40, 10, 0, 70, 60, 20) }; }
// the lid in his left hand, gripping its knob from above; c = lid centre
function lidHand(c) { const kn = c.clone().add(V(0, LIDKNOBY + 0.012, 0));
  return { S: 'L', p: kn.clone().add(V(0, 0.028, 0)), n: V(0, -1, 0), u: F.clone().addScaledVector(Rt, -0.25).normalize(), c: 62, th: 55, memAbs: 'lidL', seed: A(45, 20, 0, 70, -60) }; }
// shielding his face from the blast: palms out toward the fire
function shieldHands(k) { const hd = wp(G.bones.head);
  return ['R', 'L'].map(S => { const s = S === 'R' ? 1 : -1;
    return { S, p: hd.clone().addScaledVector(F, 0.24).addScaledVector(Rt, 0.07 * s).add(V(0, -0.05, 0)), n: F.clone().addScaledVector(UP, 0.2).normalize(), u: UP.clone().addScaledVector(F, -0.2).normalize(), c: 18, th: 15, seed: A(100, 20, 30, 120, 40) }; }); }
function counterRestR() { return { S: 'R', p: V(-2.42, TOPC + 0.03, STANDP.z - 0.16), n: V(0, -1, 0), u: F.clone().addScaledVector(Rt, 0.25).normalize(), c: 20, th: 20, memAbs: 'restR', seed: A(35, 10, 0, 40, -60) }; }
let LIDREL = null, CUPREL = null;

// the state at a time ----------------------------------------------
function guyAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  const face = { blink: blinkAt(lt + b * 1.3) };
  let pose = STAND1, root = { x: STANDP.x, y: 0.95, z: STANDP.z, yaw: 90 }, hands = [], show = true, cut = false;
  let fire = 0, fireSquash = 0, ball = -1, smoke = 0, burner = 1, knobTurn = 0, cutaway = false, lidAt = LID0.clone(), lidTilt = 0, lidIn = false;
  let cupMode = 'counter', cupTilt = 0, waterK = -1, steamK = 0, phoneOn = false, phoneScroll = 0, blast = 0, stepBack = 0;
  if (b === 7 || b === 0) {                                         // 7: on his phone while the oil heats, it catches; 0: he looks up and grabs the cup
    phoneOn = true; phoneScroll = (b === 7 ? DUR[0] - DUR[7] + lt : DUR[0] + lt) * 60;   // the feed keeps scrolling across the loop
    if (b === 7) { smoke = smooth(0, T_IGNITE, lt); fire = 0.35 * smooth(T_IGNITE - 0.05, d, lt);
      hands = [phoneHand()]; pose = addPose(STAND1, { neck: [-16, 0, 0], head: [-10, 0, 0] });
      Object.assign(face, { look: [0, -0.6] });
    } else {
      fire = 0.35 + 0.35 * smooth(0, d, lt); smoke = 1 - smooth(0, 0.6, lt) * 0.5;
      const look = smooth(0.2, 0.55, lt);                          // he looks up from the phone at the pan, scared
      pose = addPose(STAND1, { neck: [-16 * (1 - look) - 8 * look, 14 * look, 0], head: [-10 * (1 - look) - 4 * look, 6 * look, 0], spine1: [4 * look, 0, 0] });
      Object.assign(face, { look: [0.3 * look, -0.6 * (1 - look)], fear: look, brow: look, oh: 0.4 * look, jaw: 0.25 * look });
      hands = [{ ...phoneHand(), ...(LOOPSEED.L ? { seed: LOOPSEED.L, seedIsPrev: true } : {}) }];
      const reach = smooth(T_REACH - 0.6, T_REACH + 0.1, lt), lift = smooth(T_LIFT - 0.1, d, lt);
      if (lt > T_REACH - 0.6) {                                   // right hand to the cup, then lifts it up beside the pan
        cupMode = lt > T_REACH + 0.1 ? 'hand' : 'counter';
        const c = CUP0.clone().lerp(PAN.clone().add(V(0.13, 0.17, -0.18)), lift);
        hands.push({ ...cupHand(c, 0), blend: reach }); }
    }
  } else if (b === 1 || b === 2) {
    fire = 0.7;
    if (b === 1 && lt < T_CUT1) {                                  // throws: the cup tips toward the pan; the water flies in
      cupMode = 'hand'; cupTilt = 82 * smooth(T_THROW - 0.12, T_HIT + 0.08, lt);
      const c = PAN.clone().add(V(0.13, 0.17, -0.18)).lerp(PAN.clone().add(V(0.08, 0.2, -0.1)), smooth(0, T_HIT, lt));
      hands = [cupHand(c, cupTilt), phoneHand()]; waterK = clamp((lt - T_THROW) / (T_HIT - T_THROW), 0, 1);
      pose = addPose(STAND1, { neck: [4, 18, 0], spine1: [8, 0, 0] }); Object.assign(face, { fear: 0.6, brow: 0.6, jaw: 0.2 });
    } else {                                                       // cutaway: the water sinks under the oil; then (beat 2) boils and blasts into steam
      show = false; cutaway = true; cut = b === 1 && lt >= T_CUT1 && lt - T_CUT1 < 1 / 30 + 1e-6; cupMode = 'hand';
      fire = 0.22;
      if (b === 1) waterK = 1 + smooth(T_CUT1 + 0.15, d - 0.2, lt);  // 1..2 = sinking to the bottom
      else { waterK = 2; steamK = smooth(T_FLASH, T_FLASH + 0.9, lt); fire = 0.22 + 0.3 * smooth(T_FLASH + 0.3, d, lt); }
    }
  } else if (b === 3) {                                             // the fireball; he jumps back, shields his face
    fire = 1.1; ball = lt + 0.12; cupMode = 'hand';
    const k = smooth(0.0, 0.35, lt); stepBack = 0.22 * k; blast = Math.exp(-lt * 2.5);
    pose = addPose(STAND1, { spine1: [10 * k, 0, 0], spine2: [8 * k, 0, 0], neck: [6 * k, -20 * k, 0], head: [4 * k, -10 * k, 0] });
    root = { x: STANDP.x + stepBack, y: 0.95 - 0.02 * k, z: STANDP.z, yaw: 90 };
    hands = shieldHands(k).map(h => ({ ...h, blend: k, from: h.S === 'R' ? cupHand(PAN.clone().add(V(0.08, 0.2, -0.1)), 82) : phoneHand() }));
    Object.assign(face, { fear: 1, brow: 1, squint: 0.9 * k, jaw: 0.35, blink: 0, look: [0.4, 0] });
  } else if (b === 4) {
    if (T_RW > 0 && lt < T_RW) {                                                // rewind: beat 3 then the throw play backward fast
      const g3 = guyAt(B[3] + DUR[3] * (1 - lt / T_RW) - 0.001); return { ...g3, b, lt, d, rewind: true, cut: lt < 0.02 }; }
    fire = 0.7;                                                     // the right way: knob off, slide the lid on
    const kOn = smooth(0.1, T_KNOB, lt), turn = smooth(T_KNOB, T_KNOB + 0.35, lt); knobTurn = turn; burner = 1 - turn;
    const slide = smooth(T_LID, T_LID + 0.9, lt), lift = Math.sin(Math.PI * slide) * 0.07;
    lidAt = LID0.clone().lerp(PAN.clone().add(V(0, PANH, 0)), slide).add(V(0, lift, 0)); lidTilt = -10 * Math.sin(Math.PI * slide); lidIn = slide > 0.999;
    fireSquash = smooth(T_LID + 0.75, T_LID + 1.1, lt);
    const rest = smooth(T_KNOB + 0.45, T_KNOB + 0.95, lt);           // burner off: his right hand comes back to rest flat on the counter edge
    hands = [{ ...knobHand(-55 + 45 * turn), blend: kOn }, { ...lidHand(lidAt), blend: smooth(T_RW, T_LID, lt) }];   // his right hand stays on the knob
    pose = addPose(STAND1, { spine1: [-6, 0, 0], neck: [8, 10, 0] }); Object.assign(face, { fear: 0.3, brow: 0.5, look: [0.2, -0.4] });
  } else if (b === 5) {                                             // lid on: the flames die (cutaway through the lid), then he steps back
    lidAt = PAN.clone().add(V(0, PANH, 0)); lidIn = true; burner = 0; knobTurn = 1;
    fire = 0.7 * (1 - smooth(T_OUT, T_OUT + 1.0, lt)); fireSquash = 1; smoke = 0.6 * smooth(T_OUT + 0.6, d, lt);
    cutaway = lt < 1.55; show = !cutaway; cut = lt >= 1.55 && lt - 1.55 < 1 / 30 + 1e-6;   // the first frame back from the cutaway is a cut
    const off = smooth(1.55, 2.2, lt);
    hands = [{ ...lidHand(lidAt), blend: 1 - off }]; stepBack = 0.12 * off; root = { x: STANDP.x + stepBack, y: 0.95, z: STANDP.z, yaw: 90 };
    pose = addPose(STAND1, { neck: [10, 6, 0] }); Object.assign(face, { brow: 0.2, look: [0.1, -0.4] });
  } else if (b === 6) {                                             // too big: flames up the cabinets; he's gone (out the door, calling)
    show = false; fire = 2.6; smoke = 1; lidAt = LID0.clone();
  }
  const wb = 2 * Math.PI * Math.round(TOTAL / 2.6) / TOTAL;           // breathing (whole cycles over the loop)
  pose = addPose(pose, { spine1: [0.9 * Math.sin(wb * t), 0, 0], spine2: [0.6 * Math.sin(wb * t + 0.4), 0, 0], neck: [0.7 * Math.sin(wb * t + 1.1), 0, 0] });
  return { b, lt, d, pose, root, hands, show, cut, fire, fireSquash, ball, smoke, burner, knobTurn, cutaway, lidAt, lidTilt, lidIn, cupMode, cupTilt, waterK, steamK, phoneOn, phoneScroll, blast, stepBack, face };
}

// ------------------------------------------------------------------ cameras
function shakeV(t, a) { return V(vn1(t * 14, 1) * a * 0.5, vn1(t * 14, 2) * a, vn1(t * 14, 3) * a); }
const CAM7 = { pos: V(-2.74, 1.76, 0.78), tgt: V(-2.25, 1.3, -0.6), fov: 46 };     // high over the counter at his front-left: his face up top, the pan and the fire below
function camAt(t, g) {
  const b = g.b, lt = g.lt, d = g.d;
  if (g.rewind) return camAt(B[3] + DUR[3] * (1 - lt / T_RW) - 0.001, { ...g, b: 3, lt: DUR[3] * (1 - lt / T_RW) - 0.001, rewind: false });
  if (b === 7) { const k = smooth(0, d, lt); return { pos: CAM7.pos.clone().add(V(0.08 * (1 - k), 0.02 * (1 - k), 0.12 * (1 - k))), tgt: CAM7.tgt, fov: CAM7.fov }; }
  if (b === 0) { const k = smooth(0, d, lt); return { pos: CAM7.pos.clone().lerp(V(-2.72, 1.72, 0.62), k), tgt: CAM7.tgt.clone().lerp(V(-2.3, 1.25, -0.6), k), fov: 46 - 2 * k }; }
  if (b === 1 && !g.cutaway) return { pos: V(-2.72, 1.72, 0.62), tgt: V(-2.32, 1.24, -0.58), fov: 44 };
  if ((b === 1 || b === 2) && g.cutaway) {                          // side-on at the cut pan
    const k = b === 1 ? 0 : smooth(0, d, lt), k1 = b === 1 ? smooth(T_CUT1, d, lt) : 1;
    const pos = PAN.clone().add(V(0.0, 0.05 + 0.08 * k, 0.72 - 0.1 * k1 + 0.12 * k)), tgt = PAN.clone().add(V(0, 0.04 + 0.1 * k, 0));
    return { pos: pos.add(shakeV(t, b === 2 && lt > T_FLASH ? 0.004 * Math.exp(-(lt - T_FLASH) * 3) : 0)), tgt, fov: 38 }; }
  if (b === 3) return { pos: V(-2.72, 1.72, 1.0).add(shakeV(t, 0.03 * Math.exp(-lt * 2.2))), tgt: V(-2.3, 1.38, -0.62), fov: 50 };
  if (b === 4) return { pos: V(-2.74, 1.74, 0.62), tgt: V(-2.32, 1.18, -0.58), fov: 44 };
  if (b === 5) { if (g.cutaway) return { pos: PAN.clone().add(V(0.0, 0.09, 0.7)), tgt: PAN.clone().add(V(0, 0.07, 0)), fov: 38 };
    return { pos: V(-2.74, 1.76, 0.78), tgt: V(-2.25, 1.3, -0.6), fov: 46 }; }
  if (b === 6) { const k = smooth(0, d, lt); return { pos: V(-0.55 + 0.1 * k, 1.55, 1.3 - 0.1 * k), tgt: V(-2.45, 1.35, -0.6), fov: 48 }; }
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
const CLIP = [CUTP];
function propFromHand(obj, S, build) { const q = wq(G.bones['hand' + S]), h = RG.HANDREST[S];
  const n = h.n.clone().applyQuaternion(q), w = h.w.clone().applyQuaternion(q), u = h.u.clone().applyQuaternion(q); build(obj, RG.palmW(S), n, u, w); }
const basisQ = (x, y) => { const X = x.clone().normalize(), Y = y.clone().addScaledVector(X, -y.dot(X)).normalize(), Z = new THREE.Vector3().crossVectors(X, Y); return new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(X, Y, Z)); };
function update(t, frame) {
  t = ((t % TOTAL) + TOTAL) % TOTAL;
  const g = guyAt(t); STATE = { b: g.b };
  // the lid sits where the story puts it (his hand follows it)
  lid.position.copy(g.lidAt); lid.quaternion.copy(qAA(F, g.lidTilt)); lid.visible = !(g.cutaway && !g.lidIn);
  scene.updateMatrixWorld(true);
  // him
  G.root.visible = g.show;
  RG.applyPose(g.pose, g.root);
  const yaw = g.root.yaw, f = fwdOf(yaw), r = rightOf(yaw);
  const ground = V(g.root.x, 0, g.root.z);
  for (const [S, sx] of [['R', 0.11], ['L', -0.11]]) {
    const back = g.stepBack * (S === 'R' ? 1 : 0.6);                // the right foot steps back first
    const fp = ground.clone().addScaledVector(r, sx).addScaledVector(f, (S === 'R' ? 0.02 : -0.02) - back * 0.3);
    fp.y = ANKLEH; RG.foot(S, fp, fp.clone().add(V(0, 0.45, 0)).addScaledVector(f, 1), yawQ(yaw)); }
  G.root.updateMatrixWorld(true);
  // hands (targets read his body, so build them now that this frame's pose is on)
  const list = [];
  if (g.show) { BODYNOW = surfNow(); const g2 = guyAt(t); g.hands = g2.hands;
    for (const h of g.hands) { if (h.point) { const tipT = h.tip; h.extra = () => RG.tip('index', 'R').distanceToSquared(tipT) / (0.005 * 0.005); } list.push(h); } }
  if (list.length) { RG.hands(list, 'b' + g.b + (g.rewind ? 'r' : ''), frame); LASTH = list; }
  for (const S of ['R', 'L']) if (!list.some(h => h.S === S)) delete RG.LAST['cost' + S];
  G.root.updateMatrixWorld(true); RG.untwist(); G.face(g.face); G.root.updateMatrixWorld(true);
  // the cup: on the counter, or in his right hand (thumb side up = cup up)
  if (g.cupMode === 'hand' && g.show) propFromHand(cup, 'R', (o, pw, n, u, w) => { const ax = w.clone().negate(); o.quaternion.copy(basisQ(n, ax).multiply(qAA(V(0, 0, 1), 0)));
      o.quaternion.copy(basisQ(new THREE.Vector3().crossVectors(ax, n), ax)); o.position.copy(pw).addScaledVector(n, CUPR + CUPGRIP).addScaledVector(ax, -CUPH * 0.45); });
  else { cup.position.copy(CUP0); cup.quaternion.identity(); }
  cup.visible = !g.cutaway; cupWater.visible = g.waterK < 0 && (g.b === 0 || g.b >= 4);
  // his phone: in his left hand (screen to him) or face down on the counter
  if (g.show && (g.phoneOn || g.b === 1 || g.b === 3)) propFromHand(phone, 'L', (o, pw, n, u, w) => { o.quaternion.copy(basisQ(new THREE.Vector3().crossVectors(u, n), u)); o.position.copy(pw).addScaledVector(n, 0.02).addScaledVector(u, 0.015); });
  else { phone.position.set(-2.5, TOPC + 0.005, 0.25); phone.quaternion.copy(qAA(V(1, 0, 0), 90)); }
  const ps = Math.floor(g.phoneScroll); if (ps !== phoneState) { drawPhone(g.phoneScroll); phoneState = ps; }
  // the knob, the coil
  panKnob.userData.spin.rotation.x = g.knobTurn * 45 * D2R; coilM.emissiveIntensity = 1.2 * g.burner; coilM.emissive.setRGB(1, 0.23 * g.burner, 0.06 * g.burner);
  // cutaway: the pan, the oil and the lid lose their near half
  for (const m of [panDark, oilM, steel]) { const want = g.cutaway ? CLIP : null; if (m.clippingPlanes !== want) { m.clippingPlanes = want; m.needsUpdate = true; } }
  panHandle.visible = !g.cutaway; cutFaces.visible = g.cutaway;
  // the water: flies from the cup into the oil (0..1), sinks to the bottom (1..2), boils and flashes to steam (steamK)
  water.visible = g.waterK >= 0 && g.steamK < 0.6; steamBall.visible = g.steamK > 0.001; bubbles.visible = g.waterK >= 2 && g.steamK < 0.5;
  if (water.visible) { const top = PAN.clone().add(V(0, 0.004 + OILH - 0.004, 0)), bot = PAN.clone().add(V(0, 0.004 + 0.009, 0));
    if (g.waterK < 1) { const m0 = cup.localToWorld(V(0, CUPH, 0)), k = g.waterK; water.position.copy(m0).lerp(top, k); water.position.y += 0.06 * Math.sin(Math.PI * k); water.scale.set(0.018, 0.024 + 0.01 * k, 0.018); }
    else { const k = sm(Math.min(1, g.waterK - 1)); water.position.copy(top).lerp(bot, k); water.position.z -= 0.006; water.scale.set(0.013 + 0.003 * k, 0.009, 0.013 + 0.003 * k);
      if (g.steamK > 0) water.scale.multiplyScalar(1 - g.steamK); } }
  if (bubbles.visible) bubbles.children.forEach((bb, i) => { const a = ((g.lt * (1.5 + hash1(i)) + hash1(i * 3)) % 1), ang = hash1(i * 7) * 6.28;
    bb.position.set(PAN.x + Math.cos(ang) * 0.02 * (1 + a), PAN.y + 0.012 + a * OILH, PAN.z + Math.sin(ang) * 0.02 * (1 + a) * 0.3 - 0.004); bb.scale.setScalar(0.003 + 0.004 * a * Math.min(1, g.lt / 0.5) * (g.b === 2 ? 1 : 0)); });
  if (steamBall.visible) { const k = g.steamK; steamBall.position.set(PAN.x, PAN.y + 0.012 + 0.05 * k, PAN.z - 0.006); steamBall.scale.set(0.01 + 0.07 * k, 0.01 + 0.06 * k, 0.01 + 0.03 * k); steamM.opacity = 0.9 - 0.35 * smooth(0.75, 1, k); }
  oil.scale.y = 1; oil.position.y = 0.004 + OILH / 2 + (g.steamK > 0 ? 0.02 * Math.sin(Math.PI * Math.min(1, g.steamK * 1.5)) : 0);
  // fire, smoke and the light they throw
  FIRE.begin(); SMOKE.begin(); FIRE.m.uniforms.uT.value = t; SMOKE.m.uniforms.uT.value = t; FIRE.m.uniforms.uGain.value = g.cutaway ? 0.45 : 1;
  if (g.b === 6) {                                                  // too big: it has climbed the cabinets
    panFire(t, 1.6); for (let i = 0; i < 220; i++) { const a = ((t * (0.9 + 0.5 * hash1(i * 2.1)) + hash1(i * 1.7)) % 1), z = -0.6 + (hash1(i * 4.3) - 0.5) * 1.1;
      const p = V(-2.62 + (hash1(i * 6.7) - 0.5) * 0.3, TOPC + 0.1 + a * 1.4, z + vn1(t * 1.3 + i, 6) * 0.08); p.x += Math.max(0, p.y - 1.75) * 0.5;
      FIRE.add(p, 0.12 + 0.18 * (1 - a), 1 - a * 0.85, Math.sin(Math.PI * a) ** 0.6 * 0.9, hash1(i * 3.9)); }
    for (let i = 0; i < 120; i++) { const a = ((t * 0.3 + hash1(i * 2.3)) % 1); SMOKE.add(V(-2.5 + (hash1(i * 5.1) - 0.5) * 0.8 + a * 0.6, 1.9 + 0.3 * hash1(i * 8.1), -0.6 + (hash1(i * 6.2) - 0.5) * 2.2 + a * 0.4), 0.35 + 0.3 * a, 0.15, 0.6 * Math.sin(Math.PI * a), hash1(i * 7.4)); } }
  else panFire(t, g.fire, g.fireSquash);
  if (g.ball >= 0) fireball(g.ball, t);
  if (g.b === 2 && g.lt > T_FLASH + 0.1) { const s0 = (g.lt - T_FLASH - 0.1) * 0.5;          // in the cutaway: burning drops of oil flung up by the steam (slow motion)
    for (let i = 0; i < 46; i++) { const ang = hash1(i * 3.1) * Math.PI - Math.PI / 2, sp = 0.25 + 0.35 * hash1(i * 5.9), u = s0 - 0.08 * hash1(i * 7.7); if (u <= 0) continue;
      const p = PAN.clone().add(V(Math.sin(ang) * sp * u, 0.03 + Math.cos(ang) * 0.6 * sp * u * 2.2 - 1.2 * u * u, -0.01));
      FIRE.add(p, 0.012 + 0.02 * Math.min(1, u * 3), 0.9, 0.8 * Math.max(0, 1 - u * 0.8), hash1(i * 2.7)); } }
  panSmoke(t, g.smoke, g.lidIn ? 0.05 : 0);
  FIRE.end(); SMOKE.end();
  const fl = (g.b === 6 ? 2.2 : g.fire * (1 - 0.8 * g.fireSquash)) + (g.ball >= 0 ? 6 * Math.exp(-g.ball * 1.5) : 0);
  fireLight.position.copy(PAN).add(V(0.15, 0.35, 0)); fireLight.intensity = 3.2 * fl * (0.85 + 0.15 * vn1(t * 12, 9));
  // camera and room light
  const C = camAt(t, g); camera.position.copy(C.pos); camera.up.set(0, 1, 0); camera.lookAt(C.tgt); camera.fov = C.fov; camera.updateProjectionMatrix();
  const dim = g.cutaway ? 0.45 : 1;
  sun.position.set(1.6, 3.4, 2.4); sun.target.position.set(0, 0, 0); sun.target.updateMatrixWorld();
  sun.intensity = 2.6 * dim; hemi.intensity = 0.85 * dim; scene.environmentIntensity = 0.35 * dim; lamp.intensity = 6 * dim;
  scene.background = new THREE.Color(0xd9cbb6).multiplyScalar(dim);
  clockHands.s.rotation.z = -t * 6 * D2R; clockHands.m.rotation.z = -1.1; clockHands.h.rotation.z = -3.3;
  return { beat: g.b, cut: g.cut };
}
G.reset(); G.root.updateMatrixWorld(true);
const ANKLEH = wp(G.bones.footR).y;

// ------------------------------------------------------------------ frame I/O (same contract as the other 3D Shorts)
const draw = () => renderer.render(scene, camera);
const gl = renderer.getContext(), px = new Uint8Array(W * H * 4);
let CUTF = false, LASTB = 0;
function segStart(t) { const b = beatAt(t), lt = t - B[b];             // where a hold starts cold (a jump replays from there, so chunks match a straight render)
  if (b === 1 && lt < T_CUT1) return B[0];
  if (b === 5) return B[4] + T_RW;
  return B[b]; }
function stepTo(i) { const t = i / FPS, tt = ((t % TOTAL) + TOTAL) % TOTAL;
  if (i !== LASTF + 1) for (let j = Math.ceil(segStart(tt) * FPS - 1e-6) + Math.floor(t / TOTAL) * Math.round(TOTAL * FPS); j < i; j++) update(j / FPS, j);
  const r = update(t, i); CUTF = r.cut; LASTB = r.beat; LASTF = i; }
// the loop: beat 0's phone hand starts where beat 7 ends
for (let i = Math.ceil(B[7] * FPS); i < Math.round(TOTAL * FPS); i++) update(i / FPS, i);
LOOPSEED.L = RG.LAST.armL.slice();
draw();
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
window.dbg = { G, RG, wp, THREE, LOOPSEED, update, guyAt, renderer, scene, camera, setBN: () => { BODYNOW = surfNow(); }, KNOB, KAX, F, Rt, UP };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS);
window.READY = true;
