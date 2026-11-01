// "You just got the worst news of your life, and your chest feels like it's being crushed." - a 3D Short: broken heart syndrome (takotsubo).
//   brokenheart.html?w=1080&h=1920            (times from brokenheart/times.json; one shot per narration line)
// Beats: 0 the phone slips, his hand goes to his chest (hook) | 1 x-ray: his heart pounds | 2 x-ray: adrenaline floods it from the adrenal glands
//        3 the big heart: its bottom balloons out like an octopus pot | 4 it can't pump right | 5 call 911 | 6 it goes back to its shape (weeks) | 7 the message (loops)
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { loadGuy } from '/guy3d.js';

const Q = new URLSearchParams(location.search);
const W = +Q.get('w') || 720, H = +Q.get('h') || 1280;
const FPS = 30;
const TIMES = await (await fetch('/brokenheart/times.json')).json();
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
// ================================================================== BROKEN HEART SYNDROME
// ------------------------------------------------------------------ the living room (same home as always); his phone; the x-ray heart; a big heart up close (beats 3, 6)
const STANDP = V(0.2, 0, 0.4);                                     // where he stands, facing +z (the camera), the couch and window behind him
// his phone: a message on screen, then (beat 5) a 911 call
const phone = new THREE.Group(); scene.add(phone);
const phoneCanvas = document.createElement('canvas'); phoneCanvas.width = 480; phoneCanvas.height = 990;
const phoneTex = new THREE.CanvasTexture(phoneCanvas); phoneTex.colorSpace = THREE.SRGBColorSpace;
let phoneState = '';
function drawPhone(mode) { const g = phoneCanvas.getContext('2d'); g.setTransform(3, 0, 0, 3, 0, 0); g.fillStyle = mode === 'call' ? '#0c3a1c' : '#101418'; g.fillRect(0, 0, 160, 330); g.textAlign = 'center';
  if (mode === 'call') { g.fillStyle = '#fff'; g.font = 'bold 50px Arial'; g.fillText('911', 80, 110); g.font = 'bold 22px Arial'; g.fillText('CALLING', 80, 150); g.fillStyle = '#e8322a'; g.beginPath(); g.arc(80, 270, 26, 0, Math.PI * 2); g.fill(); }
  else { g.fillStyle = '#8a8f98'; g.font = '16px Arial'; g.fillText('Mom', 80, 40); g.fillStyle = '#2a2e36'; g.beginPath(); g.roundRect(10, 70, 140, 120, 16); g.fill();
    g.fillStyle = '#fff'; g.font = 'bold 19px Arial'; g.textAlign = 'left'; ['Call me now.', 'Something', 'terrible', 'happened.'].forEach((l, i) => g.fillText(l, 22, 102 + i * 24)); }
  phoneTex.needsUpdate = true; }
{ box(0.072, 0.152, 0.009, 0, 0, 0, mat(0x1c1d22, 0.3, 0.6), 0.004, phone); const s = new THREE.Mesh(new THREE.PlaneGeometry(0.064, 0.142), new THREE.MeshBasicMaterial({ map: phoneTex, toneMapped: false })); s.position.z = 0.0048; phone.add(s); }
drawPhone('msg');

// ------------------------------------------------------------------ x-ray: the glow body (same skeleton) with the heart and the adrenal glands
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
// the heart (to his left of centre) and the adrenal glands on top of the kidneys (they squirt the stress hormones)
const heartM = new THREE.MeshStandardMaterial({ color: 0x8a1a2a, emissive: 0xff2a3a, emissiveIntensity: 0.9, roughness: 0.4 });
const heart = new THREE.Group(); G.bones.chest.add(heart); heart.position.copy(toLocal(G.bones.chest, V(-0.025, 1.31, -0.04)));
const xLV = new THREE.Group();                                     // its bottom (the left ventricle's tip): balloons in beats 1-5
{ const hg = new THREE.Group(); heart.add(hg); hg.rotation.z = -0.45; hg.rotation.x = 0.2;
  for (const s of [-1, 1]) { const l = new THREE.Mesh(new THREE.SphereGeometry(0.03, 24, 16), heartM); l.position.set(s * 0.02, 0.012, 0); hg.add(l); }
  const pt = new THREE.Mesh(new THREE.ConeGeometry(0.043, 0.07, 24).rotateX(Math.PI), heartM); pt.position.y = -0.03; pt.scale.z = 0.75; hg.add(pt);
  hg.add(xLV); xLV.position.y = -0.045; const bl = new THREE.Mesh(new THREE.SphereGeometry(0.03, 24, 16), heartM); xLV.add(bl); xLV.scale.setScalar(0.01); }
const adrM = new THREE.MeshStandardMaterial({ color: 0xc89a2a, emissive: 0xffb020, emissiveIntensity: 0.6, roughness: 0.4 });
const ADR = []; for (const s of [-1, 1]) { const a = new THREE.Mesh(new THREE.ConeGeometry(0.025, 0.03, 12), adrM); G.bones.spine1.add(a); a.position.copy(toLocal(G.bones.spine1, V(s * 0.06, 1.12, 0.05))); ADR.push(a); }
const dotTex = canvasTex(64, 64, g => { const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.4, 'rgba(255,255,255,0.6)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); });
function dots(n, color, size) { const g = new THREE.BufferGeometry(); const p = new Float32Array(n * 3); g.setAttribute('position', new THREE.BufferAttribute(p, 3)); g.setDrawRange(0, 0);
  const m = new THREE.Points(g, new THREE.PointsMaterial({ color, size, map: dotTex, transparent: true, depthWrite: false, depthTest: false, blending: THREE.AdditiveBlending, toneMapped: false })); m.frustumCulled = false; m.renderOrder = 9; scene.add(m); return { m, p, n }; }
const ADRN = dots(260, 0xffc030, 0.024);
const ORGANS = [heart, ...ADR];
let XRON = false, XRNEW = false;
function setXray(k) { if ((k > 0.01) !== XRON) { XRON = k > 0.01; XRNEW = XRON; }   // the first draw after the ghost comes on comes out blank: draw() renders that frame twice
  for (const x of XRAY) x.visible = k > 0.01; xrayMat.emissiveIntensity = 0.45 * k;
  for (const o of NORMAL) o.visible = k < 0.6; for (const o of ORGANS) o.visible = k > 0.5; }

// ------------------------------------------------------------------ the big heart (a dark stage): its bottom balloons out; a clay octopus pot beside it for the shape
const HS = V(40, 0, 0);
const heartSet = new THREE.Group(); heartSet.position.copy(HS); scene.add(heartSet);
const hsLight = new THREE.PointLight(0xffe8e0, 0, 6, 1.2); hsLight.position.set(0.6, 1.0, 1.4); heartSet.add(hsLight);
heartSet.add(new THREE.Mesh(new THREE.SphereGeometry(5, 24, 12), new THREE.MeshBasicMaterial({ color: 0x14060a, side: THREE.BackSide })));
const bigM = new THREE.MeshStandardMaterial({ color: 0xa82030, emissive: 0x3a0610, emissiveIntensity: 0.4, roughness: 0.45 });
const vesM = new THREE.MeshStandardMaterial({ color: 0xc84a4a, roughness: 0.5 }), veinM = new THREE.MeshStandardMaterial({ color: 0x4a5ab0, roughness: 0.5 });
const BIG = new THREE.Group(); BIG.position.y = 1.0; heartSet.add(BIG);
// the left ventricle (main pumping chamber) is one soft mesh we reshape every frame: normal = a cone with a rounded point;
// ballooned = round wide bottom, tight narrow neck (the octopus pot). The bottom stops moving; only the neck still squeezes.
const LVG = new THREE.SphereGeometry(1, 72, 54), LV0 = LVG.attributes.position.array.slice();
const LVC = new Float32Array(LV0.length); LVG.setAttribute('color', new THREE.BufferAttribute(LVC, 3));
const bigLVM = bigM.clone(); bigLVM.color.set(0xffffff); bigLVM.vertexColors = true;
const bigLV = new THREE.Mesh(LVG, bigLVM);
const LVRED = new THREE.Color(0xa82030), LVSTUN = new THREE.Color(0xc87a86);
function shapeLV(bal, sq) { const P = LVG.attributes.position.array;
  for (let i = 0; i < P.length; i += 3) { const x = LV0[i], y = LV0[i + 1], z = LV0[i + 2], s = (y + 1) / 2;
    const kN = 0.5 + 0.5 * Math.pow(s, 0.55), kB = 1.3 - 0.72 * Math.pow(s, 1.4);
    const st = bal * (1 - Math.min(1, Math.max(0, (s - 0.2) / 0.45))); LVC[i] = LVRED.r + (LVSTUN.r - LVRED.r) * st; LVC[i + 1] = LVRED.g + (LVSTUN.g - LVRED.g) * st; LVC[i + 2] = LVRED.b + (LVSTUN.b - LVRED.b) * st;
    const k = (kN + (kB - kN) * bal) * (1 - 0.1 * sq * (s + (1 - s) * (1 - bal)));
    const yy = y < 0 ? y * (1.0 + 0.12 * (1 - bal) - 0.1 * bal) : y;      // the point pulls in as it rounds out
    P[i] = x * 0.2 * k; P[i + 1] = yy * 0.3; P[i + 2] = z * 0.18 * k; }
  LVG.attributes.position.needsUpdate = true; LVG.attributes.color.needsUpdate = true; LVG.computeVertexNormals(); }
shapeLV(0, 0);
{ const body = new THREE.Group(); BIG.add(body); body.rotation.z = 0.25; body.rotation.y = -0.25;
  body.add(bigLV); bigLV.position.set(0.05, -0.1, 0.0);
  const rv = new THREE.Mesh(new THREE.SphereGeometry(1, 40, 30), bigM); rv.scale.set(0.15, 0.24, 0.13); rv.position.set(-0.13, -0.02, 0.07); rv.rotation.z = -0.25; body.add(rv);   // right ventricle (stays normal)
  for (const [x, y, z, r] of [[-0.12, 0.2, -0.03, 0.12], [0.13, 0.22, -0.06, 0.11]]) { const s = new THREE.Mesh(new THREE.SphereGeometry(r, 32, 24), bigM); s.position.set(x, y, z); body.add(s); }   // the two upper chambers
  const ao = new THREE.Mesh(new THREE.TorusGeometry(0.085, 0.042, 14, 28, Math.PI * 1.15), vesM); ao.position.set(0.02, 0.33, -0.02); ao.rotation.z = 0.15; body.add(ao);
  const aoS = new THREE.Mesh(new THREE.CylinderGeometry(0.042, 0.045, 0.14, 16), vesM); aoS.position.set(0.1, 0.27, -0.02); body.add(aoS);
  const pa = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.045, 0.22, 16), veinM); pa.position.set(-0.14, 0.34, 0.03); pa.rotation.z = 0.25; body.add(pa); }
const potM = new THREE.MeshStandardMaterial({ color: 0x9a5a34, roughness: 0.85, side: THREE.DoubleSide });
const pot = new THREE.Group(); pot.position.set(0.42, 0.42, 0.05); heartSet.add(pot);
{ const prof = [[0, 0], [0.16, 0.01], [0.21, 0.12], [0.2, 0.26], [0.12, 0.36], [0.06, 0.42], [0.065, 0.48], [0.075, 0.5]].map(([x, y]) => new THREE.Vector2(x * 0.8, y * 0.8));
  const m = new THREE.Mesh(new THREE.LatheGeometry(prof, 40), potM); pot.add(m);
  const rope = new THREE.Mesh(new THREE.TorusGeometry(0.052, 0.008, 8, 24).rotateX(Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0xc8b088, roughness: 0.9 })); rope.position.y = 0.33; pot.add(rope); }   // wide round bottom, narrow neck: the shape the ballooned heart takes
const potTag = new THREE.Sprite(new THREE.SpriteMaterial({ map: canvasTex(512, 128, g => { g.fillStyle = 'rgba(10,10,14,0.75)'; g.beginPath(); g.roundRect(4, 4, 504, 120, 30); g.fill(); g.fillStyle = '#e8c8a0'; g.font = 'bold 52px sans-serif'; g.textAlign = 'center'; g.fillText('OCTOPUS POT', 256, 82); }), depthTest: false, toneMapped: false, transparent: true }));
potTag.scale.set(0.34, 0.085, 1); potTag.position.set(0.42, 0.34, 0.25); potTag.renderOrder = 10; heartSet.add(potTag);
const FLOW = dots(220, 0xff4a4a, 0.03);

// the phone up close (an insert in the corner of the frame): the message (beats 7, 0) and the 911 call (beat 5)
scene.add(camera);
const phone2 = new THREE.Group(); camera.add(phone2); phone2.visible = false;
{ box(0.072, 0.152, 0.009, 0, 0, 0, mat(0x1c1d22, 0.3, 0.6), 0.004, phone2); const s = new THREE.Mesh(new THREE.PlaneGeometry(0.064, 0.142), new THREE.MeshBasicMaterial({ map: phoneTex, toneMapped: false })); s.position.z = 0.0048; phone2.add(s);
  phone2.traverse(o => { if (o.isMesh) { o.renderOrder = 20; o.material = o.material.clone(); o.material.depthTest = false; } }); }

// ------------------------------------------------------------------ the story
const YAW = 180;                                                    // he faces +z (toward the camera)
const T_DROP = 0.4;                                                 // (fingers loosen first, from 0.05 s)                                                // beat 0: the phone slips out of his hand
const LOOPSEED = { R: null, L: null }; let CHESTSEED = null; const CSEED = {}; let CHESTOFF = 0.153;   // set at load from where his chest's skin is
// turn a hand frame (palm normal n, finger direction u) toward another without passing through zero (lerping u from down to up flipped the hand)
function frameSlerp(n0, u0, n1, u1, k) { const q = (n, u) => { const N = n.clone().normalize(), U = u.clone().addScaledVector(N, -u.dot(N)).normalize(), X = new THREE.Vector3().crossVectors(U, N);
    return new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(X, U, N)); };
  const r = q(n0, u0).slerp(q(n1, u1), k); return { n: V(0, 0, 1).applyQuaternion(r), u: V(0, 1, 0).applyQuaternion(r) }; }
const bez = (a, b, c, k) => a.clone().multiplyScalar((1 - k) * (1 - k)).addScaledVector(b, 2 * k * (1 - k)).addScaledVector(c, k * k);
function blinkAt(s) { const u = ((s + 40) % 3.7) / 0.16; return u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0; }
const F = fwdOf(YAW), Rt = rightOf(YAW), UP = V(0, 1, 0);
const STAND1 = { ...addPose(STAND, { spine1: [-4, 0, 0], neck: [6, 0, 0] }), armL: A(10, 14, 0, 22), armR: A(10, 14, 0, 22) };
const PH = { rot: 15, n: 0.0165, u: 0.0, w: 0.0, c: 40, th: 30, opp: 30 };   // the phone across his palm: fingers wrap its edge, thumb on the screen
function phoneHand(low = 0) { const hd = wp(G.bones.head), n = UP.clone().multiplyScalar(0.62).addScaledVector(F, -0.78).normalize(), u = F.clone().multiplyScalar(0.78).addScaledVector(UP, 0.62).normalize();
  return { S: 'L', p: hd.clone().addScaledVector(F, 0.27).addScaledVector(Rt, 0.04).add(V(0, -0.32 - low, 0)), n, u, c: PH.c, th: PH.th, opp: PH.opp, memAbs: 'phoneL', seed: A(40, 10, 0, 110, -40) }; }
// his right palm pressed flat on his chest, over his heart (his left side)
function chestHand(S = 'R', dy = 0) { const c = wp(G.bones.chest), q = wq(G.bones.chest), fw = V(0, 0, -1).applyQuaternion(q), up = V(0, 1, 0).applyQuaternion(q), lf = V(-1, 0, 0).applyQuaternion(q);
  const s = S === 'R' ? 1 : -1;
  return { S, p: c.clone().addScaledVector(fw, CHESTOFF).addScaledVector(up, 0.02 + dy).addScaledVector(lf, S === 'R' ? 0.05 : -0.02), n: fw.clone().negate(), u: up.clone().addScaledVector(lf, 0.5 * s).normalize(), c: 14 + 6 * (S === 'R' ? 1 : 0), th: 14, soft: 0.004, memAbs: 'chest' + S, seed: A(60, 10, 30, 125, -30) }; }

// the state at a time ----------------------------------------------
function guyAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  const face = { blink: blinkAt(lt + b * 1.3) };
  let pose = STAND1, root = { x: STANDP.x, y: 0.95, z: STANDP.z, yaw: YAW }, hands = [], show = true, cut = false;
  let ins = 0, phoneMode = 'hand', phoneScr = 'msg', fall = -1, xr = 0, pulse = 1, bpm = 80, adr = 0, balloon = 0, bigShot = false, pot = 0, flow = 0, pain = 0;
  if (b === 7) {                                                    // the message comes in; he reads it
    hands = [phoneHand()]; pose = addPose(STAND1, { neck: [-16, 0, 0], head: [-10, 0, 0] }); ins = smooth(0.5, 0.8, lt);
    const k = smooth(1.2, d, lt); Object.assign(face, { look: [0, -0.6], brow: 0.5 * k, fear: 0.3 * k, oh: 0.2 * k });
  } else if (b === 0) {                                             // the shock: the phone slips, his hand goes to his chest
    const grab = smooth(T_DROP - 0.1, T_DROP + 0.95, lt), rel = smooth(T_DROP + 0.05, T_DROP + 0.85, lt), loose = smooth(0.05, T_DROP, lt);
    ins = 1 - smooth(0.0, 0.3, lt); pain = smooth(0.2, 1.0, lt); bpm = 120;
    phoneMode = lt < T_DROP ? 'hand' : 'fall'; fall = lt - T_DROP;
    // right hand: from hanging at his side, up in an arc (out in front, not across his belly) to flat on his chest
    { const ch = chestHand('R'), fr = RG.handFK('R', STAND1.armR), mid = fr.p.clone().lerp(ch.p, 0.5).addScaledVector(F, 0.13);
      const fo = frameSlerp(fr.n, fr.u, ch.n, ch.u, grab); hands.push({ ...ch, p: bez(fr.p, mid, ch.p, grab), n: fo.n, u: fo.u, c: 8 + (ch.c - 8) * grab, th: 8 + (ch.th - 8) * grab,
        seed: STAND1.armR, seedIsPrev: lt < 0.5 / 30 }); }
    // left hand: the fingers open, the phone slides off forward; then the hand sinks back down to his side
    { const ph = phoneHand(), fl = RG.handFK('L', STAND1.armL), mid = ph.p.clone().lerp(fl.p, 0.5).addScaledVector(F, 0.06).addScaledVector(Rt, -0.12);   // out to his left side, not across his belly
      const fo = frameSlerp(ph.n, ph.u, fl.n, fl.u, rel), hl = { ...ph, p: bez(ph.p, mid, fl.p, rel), n: fo.n, u: fo.u,
        c: PH.c - (PH.c - 6) * loose, th: PH.th, opp: PH.opp };   // the thumb stays on the screen (opening it swung it through the phone)
      hands.push(LOOPSEED.L && lt < 0.5 / 30 ? { ...hl, seed: LOOPSEED.L, seedIsPrev: true } : hl); }
    pose = addPose(STAND1, { spine1: [10 * pain, 0, 0], spine2: [8 * pain, 0, 0], neck: [-16 * (1 - pain) - 6 * pain, 0, 0], head: [-10 * (1 - pain), 0, 0] }); root.y = 0.95 - 0.03 * pain;
    Object.assign(face, { fear: pain, brow: pain, squint: 0.6 * pain, jaw: 0.3 * pain, oh: 0.3 * pain, look: [0, -0.2] });
  } else if (b === 1 || b === 2) {                                  // x-ray: his heart pounds; (2) the adrenal glands flood it with adrenaline
    xr = 1; phoneMode = 'floor'; bpm = 130; pain = 1;
    if (b === 2) adr = smooth(0.2, 1.4, lt);
    hands = [CSEED[b] ? { ...chestHand('R'), seed: CSEED[b], seedIsPrev: true } : chestHand('R')]; pose = addPose(STAND1, { spine1: [10, 0, 0], spine2: [8, 0, 0], neck: [-6, 0, 0] }); root.y = 0.92;
  } else if (b === 3) {                                             // the big heart: its bottom balloons out like a pot
    show = false; bigShot = true; balloon = smooth(0.3, 2.2, lt); pot = smooth(2.0, 2.6, lt); bpm = 90; pulse = 0.5;
  } else if (b === 4) {                                             // it can't pump right: weak beats, slow flow; feels like a heart attack
    show = false; bigShot = true; balloon = 1; pot = 0; bpm = 70; pulse = 0.25; flow = 1;
  } else if (b === 5) {                                             // chest pain or trouble breathing: call 911
    phoneMode = 'hand'; phoneScr = 'call'; pain = 1; ins = smooth(0.15, 0.45, lt) * (1 - smooth(d - 0.3, d - 0.05, lt));
    hands = [phoneHand(), CHESTSEED ? { ...chestHand('R'), seed: CHESTSEED, seedIsPrev: true } : chestHand('R')];
    pose = addPose(STAND1, { spine1: [8, 0, 0], spine2: [6, 0, 0], neck: [-16, 0, 0], head: [-8, 0, 0] }); root.y = 0.93;
    Object.assign(face, { fear: 0.7, brow: 0.8, squint: 0.4, look: [0, -0.6] });
  } else if (b === 6) {                                             // most heal in weeks: the heart goes back to its shape; rarely, it kills
    show = false; bigShot = true; balloon = 1 - smooth(0.3, 2.4, lt); bpm = 75; pulse = 0.4 + 0.6 * smooth(0.3, 2.4, lt); flow = smooth(0.3, 2.4, lt);
  }
  const wb = 2 * Math.PI * Math.round(TOTAL / 2.6) / TOTAL;           // breathing (whole cycles over the loop)
  pose = addPose(pose, { spine1: [0.9 * Math.sin(wb * t), 0, 0], spine2: [0.6 * Math.sin(wb * t + 0.4), 0, 0], neck: [0.7 * Math.sin(wb * t + 1.1), 0, 0] });
  return { b, lt, d, pose, root, hands, show, cut, ins, phoneMode, phoneScr, fall, xr, pulse, bpm, adr, balloon, bigShot, pot, flow, pain, face };
}

// ------------------------------------------------------------------ cameras
const CAM7 = { pos: V(0.55, 1.55, 1.85), tgt: V(0.25, 1.3, 0.4), fov: 44 };       // in front of him (a little to his left, the phone side): his face, the phone, the room behind
function camAt(t, g) {
  const b = g.b, lt = g.lt, d = g.d, k = smooth(0, d, lt);
  if (b === 7) return { pos: CAM7.pos.clone().add(V(0.05 * (1 - k), 0, 0.12 * (1 - k))), tgt: CAM7.tgt, fov: CAM7.fov };
  if (b === 0) return { pos: CAM7.pos.clone().lerp(V(0.45, 1.56, 1.5), sm(Math.min(1, lt / 1.2))), tgt: CAM7.tgt.clone().lerp(V(0.18, 1.42, 0.4), sm(Math.min(1, lt / 1.2))), fov: 44 };
  if (b === 1 || b === 2) return { pos: V(0.38, 1.42, 1.5 - 0.12 * k), tgt: V(0.2, 1.3, 0.4), fov: 42 };
  if (b === 3) { const w = smooth(1.7, 2.7, lt);                   // close on the heart as it balloons, then pull back to show the pot beside it
    return { pos: HS.clone().add(V(0.03 + 0.14 * w, 1.0, 1.45 + 0.85 * w)), tgt: HS.clone().add(V(0.17 * w, 0.95, 0)), fov: 42 }; }
  if (b === 4 || b === 6) return { pos: HS.clone().add(V(0.04, 1.0, 1.55 - 0.12 * k)), tgt: HS.clone().add(V(0, 0.95, 0)), fov: 42 };
  if (b === 5) return { pos: V(0.5, 1.56, 1.5 + 0.1 * (1 - k)), tgt: V(0.3, 1.38, 0.4), fov: 44 };
  return CAM7;
}

// ------------------------------------------------------------------ the film look (AO, depth of field, rim light) and motion-capture life (look.js)
import { makeLook, loadIdle, idleAt, saccade } from '/look.js';
const LOOKON = new URLSearchParams(location.search).get('look') !== '0';
const IDLE = LOOKON ? await loadIdle('/mocap/idle_77_02.json') : null;
const LOOK = LOOKON ? makeLook(THREE, renderer, scene, camera, W, H, { overlays: [phone2] }) : null;
let LASTFOCUS = null, LASTXR = 0;

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
let PFLOOR = V(0.0, 0.0045, 0.75);                                  // where the dropped phone ends up (worked out at load from the fall)
let DROP0 = null, DROPQ = null;
// the dropped phone: slides off his open fingers (forward, a little up and out), tumbles, lands flat with a small bounce and slide
const FLATQ = new THREE.Quaternion().setFromEuler(new THREE.Euler(-Math.PI / 2, 0, 0.6));
function fallAt(s) { const v = F.clone().multiplyScalar(0.7).addScaledVector(Rt, -0.2).add(V(0, 0.2, 0)), yl = 0.0045;
  const tl = (v.y + Math.sqrt(v.y * v.y + 2 * 9.8 * (DROP0.y - yl))) / 9.8, sp = Math.min(s, tl);
  const p = DROP0.clone().addScaledVector(v, sp); p.y = DROP0.y + v.y * sp - 4.9 * sp * sp;
  const tum = q => DROPQ.clone().premultiply(new THREE.Quaternion().setFromAxisAngle(Rt, 7.5 * q));
  if (s < tl) return { p, q: tum(s) };
  const a = s - tl, vh = V(v.x, 0, v.z).normalize();
  p.addScaledVector(vh, 0.07 * (1 - Math.exp(-a * 9))); p.y = yl + 0.018 * Math.abs(Math.sin(a * 16)) * Math.exp(-a * 9);
  return { p, q: tum(tl).slerp(FLATQ, Math.min(1, a / 0.12)) }; }

function update(t, frame) {
  t = ((t % TOTAL) + TOTAL) % TOTAL;
  let g = guyAt(t); STATE = { b: g.b };
  scene.updateMatrixWorld(true);
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
  const list = [];
  if (g.show) { BODYNOW = surfNow(); const g2 = guyAt(t); g.hands = g2.hands; for (const h of g.hands) list.push(h); }
  for (const h of list) if (h.memAbs) h.memAbs += ':' + g.b;            // a hold never carries across a cut (chunks start each beat cold, so must a straight render)
  if (list.length) { RG.hands(list, 'b' + g.b, frame); LASTH = list; }
  for (const S of ['R', 'L']) if (!list.some(h => h.S === S)) delete RG.LAST['cost' + S];
  G.root.updateMatrixWorld(true); RG.untwist(); G.face(g.face); G.root.updateMatrixWorld(true);
  // the phone: in his left hand (across the palm), falling, or face up on the rug
  phone.visible = g.show || g.phoneMode === 'floor';
  const handPhone = () => propFromHand(phone, 'L', (o, pw, n, u, w) => { const ax = w.clone().multiplyScalar(Math.cos(PH.rot * D2R)).addScaledVector(u, Math.sin(PH.rot * D2R));
    o.quaternion.copy(basisQ(new THREE.Vector3().crossVectors(ax, n), ax)); o.position.copy(pw).addScaledVector(n, PH.n).addScaledVector(u, PH.u).addScaledVector(w, PH.w); });
  if (g.phoneMode === 'hand') { handPhone(); DROP0 = phone.position.clone(); DROPQ = phone.quaternion.clone(); }
  else if (g.phoneMode === 'fall') { if (!DROP0) { handPhone(); DROP0 = phone.position.clone(); DROPQ = phone.quaternion.clone(); }
    const f = fallAt(g.fall); phone.position.copy(f.p); phone.quaternion.copy(f.q); }
  else { phone.position.copy(PFLOOR); phone.quaternion.copy(FLATQ); }
  if (g.phoneScr !== phoneState) { drawPhone(g.phoneScr); phoneState = g.phoneScr; }
  // x-ray: the heart pounds; its bottom bulges; adrenaline pours up from the adrenal glands
  setXray(g.xr); const pz = Math.exp(-((((t * g.bpm / 60) % 1 - 0.05) / 0.07) ** 2));
  heart.scale.setScalar(1 + 0.12 * pz * g.pulse); heartM.emissiveIntensity = 0.7 + 0.9 * pz * g.pulse + 0.8 * g.adr * (0.6 + 0.4 * Math.sin(t * 20));
  xLV.scale.setScalar(Math.max(0.01, 0.9 * g.adr));
  adrM.emissiveIntensity = 0.6 + 1.2 * g.adr * (0.6 + 0.4 * Math.sin(t * 12));
  { const hp = wp(heart); let n = g.xr > 0.5 ? Math.round(ADRN.n * g.adr) : 0;
    for (let i = 0; i < n; i++) { const src = wp(ADR[i % 2]), a = ((t * (0.55 + 0.3 * hash1(i * 3.9)) + hash1(i * 1.3)) % 1);
      const p = src.clone().lerp(hp, a).add(V(vn1(t + i, 1) * 0.04, vn1(t + i, 2) * 0.03, vn1(t + i, 3) * 0.04).multiplyScalar(Math.sin(Math.PI * a))); ADRN.p.set([p.x, p.y, p.z], i * 3); }
    ADRN.m.geometry.setDrawRange(0, n); ADRN.m.geometry.attributes.position.needsUpdate = true; ADRN.m.visible = n > 0; }
  // the big heart
  heartSet.visible = g.bigShot; hsLight.intensity = g.bigShot ? 4 : 0;
  if (g.bigShot) { BIG.scale.setScalar(1 + 0.02 * pz * g.pulse); shapeLV(g.balloon, pz * g.pulse);
    pot.visible = g.pot > 0.01; pot.scale.setScalar(Math.max(0.01, g.pot)); potTag.visible = g.pot > 0.5; potTag.material.opacity = g.pot;
    let n = Math.round(FLOW.n * (g.b === 4 ? 0.5 : g.flow)); const c = BIG.localToWorld(V(0, 0.25, 0));
    for (let i = 0; i < n; i++) { const a = ((t * (g.b === 4 ? 0.12 : 0.45) * (0.6 + 0.4 * hash1(i * 2.1)) + hash1(i * 5.3)) % 1), ang = hash1(i * 7.7) * 6.283;
      const p = c.clone().add(V(Math.cos(ang) * 0.06, 0.05 + a * 0.6, Math.sin(ang) * 0.06)); FLOW.p.set([p.x, p.y, p.z], i * 3); }
    FLOW.m.geometry.setDrawRange(0, n); FLOW.m.geometry.attributes.position.needsUpdate = true; FLOW.m.visible = n > 0; } else FLOW.m.visible = false;
  // the phone insert, lower right, tipped a little
  phone2.visible = g.ins > 0.01; { const e = sm(g.ins); phone2.position.set(0.062, 0.055 + 0.3 * (1 - e), -0.4); phone2.rotation.set(-0.12, -0.18, 0.1); phone2.scale.setScalar(0.85); }
  // camera and light
  const C = camAt(t, g); LASTFOCUS = C.tgt.clone(); LASTXR = g.xr; camera.position.copy(C.pos); camera.up.set(0, 1, 0); camera.lookAt(C.tgt); camera.fov = C.fov; camera.updateProjectionMatrix();
  const dim = g.bigShot ? 0.4 : g.xr > 0.5 ? 0.35 : 1;
  sun.position.set(1.6, 3.4, 2.4).add(g.bigShot ? HS : V(0, 0, 0)); sun.target.position.copy(g.bigShot ? HS : V(0, 0, 0)); sun.target.updateMatrixWorld();
  sun.intensity = 2.6 * dim; hemi.intensity = 0.85 * dim; scene.environmentIntensity = 0.35 * dim; lamp.intensity = 6 * dim; scene.background = new THREE.Color(0xd9cbb6).multiplyScalar(dim);
  clockHands.s.rotation.z = -t * 6 * D2R; clockHands.m.rotation.z = -1.1; clockHands.h.rotation.z = -3.3;
  return { beat: g.b, cut: g.cut };
}
G.reset(); G.root.updateMatrixWorld(true);
const ANKLEH = wp(G.bones.footR).y;
// how far in front of the chest bone his shirt is, where the palm lies (the old guy: 0.153; other bodies differ)
{ SURF = surfNow(); const q = wq(G.bones.chest), fw = V(0, 0, -1).applyQuaternion(q), up = V(0, 1, 0).applyQuaternion(q), lf = V(-1, 0, 0).applyQuaternion(q);
  const p0 = wp(G.bones.chest).addScaledVector(up, 0.02).addScaledVector(lf, 0.05); let s = 0.05; while (s < 0.35 && bodyDepth(p0.clone().addScaledVector(fw, s)) > 0) s += 0.002;
  CHESTOFF = s + 0.005; window.CHESTS = s; SURF = null; }   // +5 mm: the old guy comes out at 0.153, as tuned

// ------------------------------------------------------------------ frame I/O (same contract as the other 3D Shorts)
const draw1 = () => LOOK ? LOOK.render(LASTFOCUS, { ao: LASTXR < 0.5, dof: LASTXR < 0.5 }) : renderer.render(scene, camera);
const draw = () => { if (XRNEW) { draw1(); XRNEW = false; } draw1(); };
const gl = renderer.getContext(), px = new Uint8Array(W * H * 4);
let CUTF = false, LASTB = 0;
function segStart(t) { return B[beatAt(t)]; }
function stepTo(i) { const t = i / FPS, tt = ((t % TOTAL) + TOTAL) % TOTAL;
  if (i !== LASTF + 1) for (let j = Math.ceil(segStart(tt) * FPS - 1e-6) + Math.floor(t / TOTAL) * Math.round(TOTAL * FPS); j < i; j++) update(j / FPS, j);
  const r = update(t, i); CUTF = r.cut; LASTB = r.beat; LASTF = i; }
for (let i = Math.ceil(B[7] * FPS); i < Math.round(TOTAL * FPS); i++) update(i / FPS, i);
LOOPSEED.L = RG.LAST.armL.slice();
for (const [b0, nb] of [[0, 1], [1, 2]]) { for (let i = Math.ceil(B[b0] * FPS); i < Math.ceil(B[b0 + 1] * FPS); i++) update(i / FPS, i); CSEED[nb] = RG.LAST.armR.slice();
  if (b0 === 0) { PFLOOR = fallAt(9).p; PFLOOR.y = 0.0045; DROP0 = null; } }   // where the phone came to rest: beats 1-2 show it there   // the hand on his chest carries on across the cuts
for (let i = Math.ceil(B[2] * FPS); i < Math.ceil(B[3] * FPS); i++) update(i / FPS, i); CHESTSEED = RG.LAST.armR.slice();   // beat 5's hand on his chest starts from where beat 2's ended
draw(); update(B[1] + 1.0, -50); draw(); update(B[3] + 1.0, -40); draw();     // warm-up: compile the x-ray and the big-heart shaders now
for (const k of Object.keys(RG.MEM)) delete RG.MEM[k]; LASTF = -10; DROP0 = null;
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
window.SCN = { THREE, scene, camera, G, stepTo, renderer, FPS, B, DUR, TOTAL, phone, phone2, home };   // for studio/blender/export_shot.mjs
