// Jack Campbell (Detroit Lions), Nov 1, 2026: the tackle at the Lions 25, why a neck hit means the backboard, and the good news. Colours and numbers only, no logos.
//   campbell_mh.html?w=1080&h=1920   (times from campbell/times.json; one shot per narration line)
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { loadGuy } from '/guy3d.js';

const Q = new URLSearchParams(location.search);
const W = +Q.get('w') || 720, H = +Q.get('h') || 1280;
const FPS = 30;
const TIMES = await (await fetch('/campbell/times.json')).json();
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
// ================================================================== THE TACKLE AT THE 25
// ------------------------------------------------------------------ set: Ford Field (indoors, afternoon game), the Lions' 25, three players in full pads (colours and numbers only, no logos)
home.visible = false; lamp.visible = false;
scene.background = new THREE.Color(0x1a1d24); scene.environmentIntensity = 0.45; scene.fog = new THREE.Fog(0x22262e, 90, 260);
hemi.color.set(0xe8eef8); hemi.groundColor.set(0x2c4a26); hemi.intensity = 0.6;
sun.color.set(0xfff8ee); sun.intensity = 2.6;
{ const S = sun.shadow.camera; S.left = -9; S.right = 9; S.top = 9; S.bottom = -9; S.near = 1; S.far = 120; S.updateProjectionMatrix(); }
// the field, in metres: x across (sideline to sideline), z along. The Lions' goal line is at -z, so the Vikings drive toward -z.
const YD = 0.9144, FW = 160 / 3 * YD, GL = 50 * YD, EZ = 10 * YD;
const zOf = (side, yd) => side === 'DET' ? -GL + yd * YD : GL - yd * YD;     // a yard line by its name: DET 25 = 25 yards out from the Lions' goal line
const SPOT = V(1.1, 0, zOf('DET', 25));                                         // where Hockenson went down: the Lions 25, between the hashes (short middle)
const HASHX = FW / 2 - (70 * 12 + 9) * 0.0254;                                  // NFL hashes: 70 ft 9 in in from each sideline (18 ft 6 in apart)
const HONOLULU = 0x0076b6, LSILVER = 0xa5acaf, VPURPLE = 0x4f2683, VGOLD = 0xffc62f;
// turf: green with 5-yard mow bands; fine grain from world position in the shader
const turfTex = canvasTex(512, 2048, g => { const N = 24; for (let i = 0; i < N; i++) { g.fillStyle = i % 2 ? '#18421a' : '#1c4a1e'; g.fillRect(0, i * 2048 / N, 512, 2048 / N + 1); }
  for (let k = 0; k < 14000; k++) { g.fillStyle = `rgba(${18 + 30 * Math.random()},${55 + 50 * Math.random()},${18 + 20 * Math.random()},0.22)`; g.fillRect(Math.random() * 512, Math.random() * 2048, 1.5, 2.5); } });
const turfM = new THREE.MeshStandardMaterial({ map: turfTex, roughness: 0.95 });
turfM.onBeforeCompile = sh => { sh.vertexShader = 'varying vec3 vWP;\n' + sh.vertexShader.replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\n vWP = (modelMatrix * vec4(transformed, 1.0)).xyz;');
  sh.fragmentShader = 'varying vec3 vWP;\nfloat th(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }\n' + sh.fragmentShader
    .replace('#include <map_fragment>', `#include <map_fragment>
      { float g1 = th(floor(vWP.xz * 260.0)), g2 = th(floor(vWP.xz * 45.0) + 7.0); float fd = clamp(1.0 - length(fwidth(vWP.xz)) * 90.0, 0.0, 1.0);
        diffuseColor.rgb *= 1.0 + fd * (0.22 * (g1 - 0.5) + 0.1 * (g2 - 0.5)); }`); };
turfM.customProgramCacheKey = () => 'turf';
const field = new THREE.Mesh(new THREE.PlaneGeometry(FW + 14, 2 * GL + 2 * EZ + 14).rotateX(-Math.PI / 2), turfM); field.receiveShadow = true; scene.add(field);
turfTex.wrapS = turfTex.wrapT = THREE.RepeatWrapping; turfTex.repeat.set(1, (2 * GL + 2 * EZ + 14) / (24 * 5 * YD));
// lines are their own thin planes (crisp at any distance): sidelines and end lines (6 ft border), goal lines, every 5 yards, the yard ticks and hashes
const lineM = new THREE.MeshStandardMaterial({ color: 0xf2f2ee, roughness: 0.8, polygonOffset: true, polygonOffsetFactor: -2 });
const LINES = new THREE.Group(); scene.add(LINES);
const strip = (x0, z0, x1, z1, y = 0.004, m = lineM) => { const w = Math.abs(x1 - x0), d = Math.abs(z1 - z0); const s = new THREE.Mesh(new THREE.PlaneGeometry(w, d).rotateX(-Math.PI / 2), m); s.position.set((x0 + x1) / 2, y, (z0 + z1) / 2); s.receiveShadow = true; LINES.add(s); return s; };
const W4 = 4 * 0.0254;
strip(-FW / 2 - 1.83, -GL - EZ - 1.83, -FW / 2, GL + EZ + 1.83); strip(FW / 2, -GL - EZ - 1.83, FW / 2 + 1.83, GL + EZ + 1.83);
strip(-FW / 2, -GL - EZ - 1.83, FW / 2, -GL - EZ); strip(-FW / 2, GL + EZ, FW / 2, GL + EZ + 1.83);
for (let yd = 0; yd <= 100; yd += 5) { const z = -GL + yd * YD, w = yd % 100 === 0 ? 8 * 0.0254 : W4; strip(-FW / 2, z - w / 2, FW / 2, z + w / 2); }
{ const tick = new THREE.InstancedMesh(new THREE.PlaneGeometry(W4, 0.61).rotateX(-Math.PI / 2), lineM, 99 * 4); const m4 = new THREE.Matrix4(); let n = 0;
  for (let yd = 1; yd < 100; yd++) { if (yd % 5 === 0) continue; const z = -GL + yd * YD;
    for (const x of [-FW / 2 + 0.15 + 0.305, FW / 2 - 0.15 - 0.305, -HASHX, HASHX]) { m4.makeTranslation(x, 0.004, z); m4.multiply(new THREE.Matrix4().makeRotationY(Math.PI / 2)); tick.setMatrixAt(n++, m4); } }
  tick.count = n; tick.receiveShadow = true; LINES.add(tick); }
// end zones in Honolulu blue (plain: no wordmarks)
const ezM = new THREE.MeshStandardMaterial({ color: HONOLULU, roughness: 0.9, polygonOffset: true, polygonOffsetFactor: -1 });
for (const s of [-1, 1]) strip(-FW / 2, s < 0 ? -GL - EZ : GL, FW / 2, s < 0 ? -GL : GL + EZ, 0.003, ezM);
// yard numbers: 6 ft tall, tops 12 yards in from each sideline, bottoms toward the sideline, arrows pointing to the nearer goal
const numTex = {}; const digitTex = d => numTex[d] || (numTex[d] = canvasTex(128, 192, g => { g.fillStyle = '#f2f2ee'; g.font = 'bold 190px Arial, Helvetica, sans-serif'; g.textAlign = 'center'; g.textBaseline = 'alphabetic'; g.fillText(d, 64, 180); }));
const arrowTex = canvasTex(64, 64, g => { g.fillStyle = '#f2f2ee'; g.beginPath(); g.moveTo(4, 32); g.lineTo(60, 8); g.lineTo(60, 56); g.fill(); });
for (let yd = 10; yd <= 90; yd += 10) { const z = -GL + yd * YD, label = String(yd <= 50 ? yd : 100 - yd);
  for (const side of [-1, 1]) { const xc = side * (FW / 2 - 12 * YD + 1.83 / 2);   // centre of the 6-ft tall number band
    [...label].forEach((d, i) => { const p = new THREE.Mesh(new THREE.PlaneGeometry(1.22, 1.83).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ map: digitTex(d), transparent: true, roughness: 0.85, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -3 }));
      // the reader stands at the near sideline: the number's bottom faces that sideline
      p.rotation.y = side > 0 ? -Math.PI / 2 : Math.PI / 2; const off = (i - (label.length - 1) / 2) * 1.35; p.position.set(xc, 0.005, z + (side > 0 ? -off : off)); p.receiveShadow = true; LINES.add(p); });
    if (yd !== 50) { const toward = yd < 50 ? -1 : 1, a = new THREE.Mesh(new THREE.PlaneGeometry(0.45, 0.45).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ map: arrowTex, transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -3 }));
      a.rotation.y = toward < 0 ? Math.PI / 2 : -Math.PI / 2; a.position.set(xc + side * 0.55, 0.005, z + toward * (1.35 * (label.length) / 2 + 0.55)); LINES.add(a); } } }
// goalposts at the end lines (yellow)
for (const s of [-1, 1]) { const gp = new THREE.Group(); gp.position.set(0, 0, s * (GL + EZ + 1.83)); scene.add(gp); const ym = mat(0xf5d21e, 0.4, 0.2);
  const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 3.05, 12), ym); pole.position.y = 1.52; gp.add(pole);
  const arm = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, 1.8, 12).rotateX(Math.PI / 2), ym); arm.position.set(0, 3.05, -s * 0.9); gp.add(arm);
  const bar = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 5.64, 12).rotateZ(Math.PI / 2), ym); bar.position.set(0, 3.05, -s * 1.8); gp.add(bar);
  for (const x of [-2.82, 2.82]) { const up = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 9.1, 10), ym); up.position.set(x, 3.05 + 4.55, -s * 1.8); gp.add(up); } }
// the stands (a domed stadium): rows stepping back from the field on all four sides, an instanced crowd (blue and silver, some purple), the roof
const stands = new THREE.Group(); scene.add(stands);
{ const sm = mat(0x2a2e36, 0.9); const crowd = []; const LEN = 2 * GL + 2 * EZ;
  const add = (w, x, z, ry) => { for (let r = 0; r < 26; r++) { const st = box(w, 0.42, 0.8, 0, 0, 0, sm, 0, stands); const dir = V(Math.sin(ry), 0, Math.cos(ry));
      st.position.set(x, 1.2 + r * 0.42, z).addScaledVector(dir, r * 0.82); st.rotation.y = ry;
      for (let k = 0; k < w; k += 0.52) crowd.push(st.position.clone().add(V(Math.cos(ry), 0, -Math.sin(ry)).multiplyScalar(k - w / 2)).add(V(0, 0.48, 0))); } };
  add(LEN + 12, FW / 2 + 9, 0, Math.PI / 2); add(LEN + 12, -FW / 2 - 9, 0, -Math.PI / 2); add(FW + 18, 0, -LEN / 2 - 8, Math.PI); add(FW + 18, 0, LEN / 2 + 8, 0);
  const cm = new THREE.InstancedMesh(new THREE.BoxGeometry(0.4, 0.62, 0.3), new THREE.MeshStandardMaterial({ roughness: 0.8 }), crowd.length); const m4 = new THREE.Matrix4();
  const PAL = [0x0076b6, 0x0076b6, 0x0a5c90, 0xb0b7bb, 0xe8e8e4, 0x1b1d22, 0x4f2683, 0x7a1f2a, 0x3a4048];
  crowd.forEach((p, i) => { m4.makeTranslation(p.x, p.y + 0.06 * hash1(i * 9.1), p.z); cm.setMatrixAt(i, m4); const c = new THREE.Color(PAL[Math.floor(hash1(i * 1.7) * PAL.length)]); c.multiplyScalar(0.55 + 0.5 * hash1(i * 3.3)); cm.setColorAt(i, c); });
  stands.add(cm);
  const wall = mat(0x0a6aa6, 0.75); box(FW + 6, 1.4, 0.3, 0, 0.7, -LEN / 2 - 5, wall, 0, stands); box(FW + 6, 1.4, 0.3, 0, 0.7, LEN / 2 + 5, wall, 0, stands);   // padded walls in Honolulu blue (match photos)
  box(0.3, 1.4, LEN + 10, -FW / 2 - 7.5, 0.7, 0, wall, 0, stands); box(0.3, 1.4, LEN + 10, FW / 2 + 7.5, 0.7, 0, wall, 0, stands);
  // the roof: a dark lid with rows of lights, and a lit band of suite windows on the sides
  const roof = new THREE.Mesh(new THREE.PlaneGeometry(260, 300).rotateX(Math.PI / 2), mat(0x2a2d33, 0.9)); roof.position.y = 58; stands.add(roof);
  const lightM = new THREE.MeshBasicMaterial({ color: 0xffffff, toneMapped: false });
  for (let i = -6; i <= 6; i++) for (const x of [-30, -15, 0, 15, 30]) { const l = new THREE.Mesh(new THREE.PlaneGeometry(2.4, 0.8).rotateX(Math.PI / 2), lightM); l.position.set(x, 57.8, i * 14); stands.add(l); }
  for (const s of [-1, 1]) { const band = new THREE.Mesh(new THREE.PlaneGeometry(LEN + 20, 2.2), new THREE.MeshBasicMaterial({ color: 0xffe6b8, toneMapped: false })); band.position.set(s * (FW / 2 + 31), 14.5, 0); band.rotation.y = -s * Math.PI / 2; stands.add(band); } }
for (const [x, z] of [[-20, -40], [20, -40], [-20, 0], [20, 0], [-20, 40], [20, 40]]) { const fl = new THREE.SpotLight(0xf6f8ff, 380, 120, 0.9, 0.6, 1.3); fl.position.set(x, 52, z); fl.target.position.set(x * 0.4, 0, z); scene.add(fl, fl.target); }

// ------------------------------------------------------------------ the players: the MakeHuman man three times (Campbell #46 and O'Neill #66 in the Lions' silver Rivalries set; Hockenson #87 in all purple)
const K_H = await loadGuy(THREE, '/char/' + (Q.get('char') || window.CHARDEF || 'guy'), { fingers3: !!window.FINGERS3 }); scene.add(K_H.root);
const K_O = await loadGuy(THREE, '/char/' + (Q.get('char') || window.CHARDEF || 'guy'), { fingers3: !!window.FINGERS3 }); scene.add(K_O.root);
for (const g of [K_H, K_O]) g.root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
const RH = makeRig(K_H, 'hock'), RO = makeRig(K_O, 'oneill');
// kit colours (linear values go to shaders; THREE.Color does the sRGB conversion)
const KITS = {
  // from the game photos (Nov 1): Lions silver jersey and pants, dark slanted numbers with a blue outline, a black-and-blue stripe on the shoulder and down the lower thigh,
  // black socks and cleats, bare hands, Honolulu blue helmet with a black centre stripe and a black facemask. Vikings all purple, white numbers with gold trim,
  // gold-and-white shoulder stripes, white gloves and white cleats, a dark facemask.
  DET: { jersey: 0xb7bcc0, pants: 0xb3b8bc, sock: 0x151619, shoe: 0x151619, glove: null, helmet: HONOLULU, stripe: 0x111214, mask: 0x141518, num: '#2b2e33', numLine: '#0a84d0', name: '#2b2e33', italic: true, cap: [0x141518, HONOLULU], pantStripe: [0x141518, HONOLULU] },
  MIN: { jersey: VPURPLE, pants: VPURPLE, sock: VPURPLE, shoe: 0xeeeeea, glove: 0xf2f2ee, helmet: VPURPLE, stripe: null, mask: 0x2b2238, num: '#ffffff', numLine: '#ffc62f', name: '#ffffff', italic: false, cap: [VGOLD, 0xffffff], pantStripe: null },
};
// the jersey number, drawn once per player (front and back of the pads; small on the shoulder caps)
function nameTex(nm, K) { return canvasTex(1024, 160, g => { g.clearRect(0, 0, 1024, 160); g.font = '800 120px "Inter Display", "Liberation Sans", sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillStyle = K.name; g.fillText(nm, 512, 84, 980); }); }
function numberTex(n, K) { return canvasTex(512, 384, g => { g.clearRect(0, 0, 512, 384); g.save(); g.translate(256, 200); if (K.italic) g.transform(1, 0, -0.22, 1, 0, 0);
  g.font = '900 330px "Inter Display", "Liberation Sans", sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.lineJoin = 'round';
  g.lineWidth = 26; g.strokeStyle = K.numLine; g.strokeText(String(n), 0, 0); g.fillStyle = K.num; g.fillText(String(n), 0, 0); g.restore(); }); }
const lin = c => new THREE.Color(c);
const PLAYERS = [];
function suitUp(Gx, team, number, name, tattoo = false) { const K = KITS[team]; Gx.reset(); Gx.root.position.set(0, 0, 0); Gx.root.quaternion.identity(); Gx.root.updateMatrixWorld(true);
  const P = { G: Gx, team, number, K };
  for (const [n, c, r] of [['shirt', K.jersey, 0.62], ['jeans', K.pants, 0.6], ['shoeR', K.shoe, 0.45], ['shoeL', K.shoe, 0.45]]) { const m = Gx.meshes[n]; if (!m) continue;
    m.material = m.material.clone(); m.material.map = null; m.material.color.set(c); m.material.roughness = r; if (n === 'shirt' && team === 'DET') { m.material.metalness = 0.05; } m.material.needsUpdate = true; }
  for (const n of ['hair', 'hairCards']) if (Gx.meshes[n]) Gx.meshes[n].visible = false;   // under the helmet
  // pants: socks below the knee (game pants stop just under it), the Lions' blue-and-black stripe down the lower half of the outer leg
  const KNEEY = wp(Gx.bones.shinL).y, LEGX = Math.abs(wp(Gx.bones.thighL).x);
  { const jm = Gx.meshes.jeans.material, prev = jm.onBeforeCompile, prevKey = jm.customProgramCacheKey ? jm.customProgramCacheKey.bind(jm) : () => '';
    const U = { uSock: { value: lin(K.sock) }, uS1: { value: lin(K.pantStripe ? K.pantStripe[0] : K.pants) }, uS2: { value: lin(K.pantStripe ? K.pantStripe[1] : K.pants) } };
    jm.onBeforeCompile = (sh, r) => { if (prev) prev.call(jm, sh, r); Object.assign(sh.uniforms, U);
      sh.vertexShader = 'varying vec3 vRestK;\n' + sh.vertexShader.replace('#include <begin_vertex>', '#include <begin_vertex>\n vRestK = position;');
      sh.fragmentShader = 'varying vec3 vRestK; uniform vec3 uSock, uS1, uS2;\n' + sh.fragmentShader.replace('#include <map_fragment>', `#include <map_fragment>
        { float y = vRestK.y; float sock = 1.0 - smoothstep(${(KNEEY - 0.055).toFixed(4)}, ${(KNEEY - 0.045).toFixed(4)}, y);
          float out_ = abs(vRestK.x) - ${LEGX.toFixed(4)};   // how far out from the middle of the leg (the stripe runs down the outside)
          float band = smoothstep(${(KNEEY - 0.04).toFixed(4)}, ${(KNEEY - 0.03).toFixed(4)}, y) * (1.0 - smoothstep(${(KNEEY + 0.19).toFixed(4)}, ${(KNEEY + 0.2).toFixed(4)}, y));
          float s1 = band * smoothstep(0.040, 0.046, out_), s2 = band * smoothstep(0.056, 0.062, out_);
          ${K.pantStripe ? 'diffuseColor.rgb = mix(diffuseColor.rgb, uS1, s1); diffuseColor.rgb = mix(diffuseColor.rgb, uS2, s2);' : ''}
          float cuff = (1.0 - sock) * (1.0 - smoothstep(${(KNEEY - 0.045).toFixed(4)}, ${(KNEEY - 0.03).toFixed(4)}, y));
          diffuseColor.rgb = mix(diffuseColor.rgb * (1.0 - 0.25 * cuff), uSock, sock); }`); };
    jm.customProgramCacheKey = () => prevKey() + '|kit' + (K.pantStripe ? 's' : ''); jm.needsUpdate = true; }
  // gloves painted on the hand skin (from 3 cm up the forearm), so nothing can poke through
  { const sk = Gx.meshes.skin_head, ga = sk.geometry.attributes, names = sk.skeleton.bones.map(b => b.name), a = new Float32Array(ga.position.count);
    const WR = {}; for (const S of ['R', 'L']) { const wr = wp(Gx.bones['hand' + S]), el = wp(Gx.bones['farm' + S]); WR[S] = { wr, d: wr.clone().sub(el).normalize() }; }
    const _p = V(0, 0, 0);
    for (let i = 0; i < ga.position.count; i++) { let arm = 0, side = null; for (let k = 0; k < 4; k++) { const w = ga.skinWeight.getComponent(i, k), n = names[ga.skinIndex.getComponent(i, k)];
        if (/^(farm|hand|index|middle|ring|pinky|thumb)/.test(n)) { arm += w; side = n.slice(-1); } }
      let gl = 0; if (arm > 0.3 && side && WR[side]) { _p.set(ga.position.getX(i), ga.position.getY(i), ga.position.getZ(i)); gl = clamp((_p.clone().sub(WR[side].wr).dot(WR[side].d) + 0.03) / 0.02, 0, 1); }
      if (!K.glove) gl = 0;
      if (tattoo && arm > 0.5 && side === 'R') { _p.set(ga.position.getX(i), ga.position.getY(i), ga.position.getZ(i)); const el = wp(Gx.bones.farmR), along = _p.clone().sub(el).dot(WR.R.d), L = WR.R.wr.distanceTo(el);
        if (along > 0.02 && along < L - 0.04) gl = -1; }   // his right forearm: a sleeve tattoo (from the photos)
      a[i] = gl; }
    sk.geometry.setAttribute('aGlove', new THREE.BufferAttribute(a, 1));
    const m = sk.material = sk.material.clone(), old = m.onBeforeCompile, oldKey = m.customProgramCacheKey ? m.customProgramCacheKey.bind(m) : () => '';
    const U = { uGlove: { value: lin(K.glove) } };
    m.onBeforeCompile = (sh, r) => { if (old) old.call(m, sh, r); Object.assign(sh.uniforms, U);
      sh.vertexShader = 'attribute float aGlove; varying float vGlove; varying vec3 vTP;\n' + sh.vertexShader.replace('#include <begin_vertex>', '#include <begin_vertex>\n vGlove = aGlove; vTP = position;');
      sh.fragmentShader = 'varying float vGlove; varying vec3 vTP; uniform vec3 uGlove;\nfloat tH(vec3 p){ p = fract(p * 0.3183099 + 0.1); p *= 17.0; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }\nfloat tN(vec3 x){ vec3 i = floor(x), f = fract(x); f = f*f*(3.0-2.0*f); return mix(mix(mix(tH(i), tH(i+vec3(1,0,0)), f.x), mix(tH(i+vec3(0,1,0)), tH(i+vec3(1,1,0)), f.x), f.y), mix(mix(tH(i+vec3(0,0,1)), tH(i+vec3(1,0,1)), f.x), mix(tH(i+vec3(0,1,1)), tH(i+vec3(1,1,1)), f.x), f.y), f.z); }\n' + sh.fragmentShader
        .replace('#include <map_fragment>', `#include <map_fragment>
          { float gl = smoothstep(0.4, 0.6, vGlove); diffuseColor.rgb = mix(diffuseColor.rgb, uGlove, gl);
            float tt = smoothstep(-0.4, -0.6, vGlove); float n = tN(vTP * 90.0) * 0.6 + tN(vTP * 210.0) * 0.4; float ink = smoothstep(0.42, 0.5, n) * (1.0 - smoothstep(0.6, 0.68, n)) + 0.55 * smoothstep(0.66, 0.72, n);
            diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.03, 0.035, 0.045), tt * clamp(ink, 0.0, 1.0) * 0.85); }`)
        .replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\n roughnessFactor = mix(roughnessFactor, 0.6, smoothstep(0.4, 0.6, vGlove));'); };
    m.customProgramCacheKey = () => oldKey() + '|glove'; m.needsUpdate = true; }
  // the helmet: a shell over the crown, sides and back with a face opening, a centre stripe (Lions), a facemask cage. Built with the opening on +z, then turned to his eyes.
  { const hb = Gx.bones.head, helmet = new THREE.Group();
    const E = wp(Gx.bones.eyeR).add(wp(Gx.bones.eyeL)).multiplyScalar(0.5), fd = E.clone().sub(V(...Gx.man.headC)).setY(0).normalize();
    const hc = E.clone().addScaledVector(fd, -0.07).add(V(0, 0.03, 0)), R0 = 0.142;
    const keep = d => { const az = Math.atan2(d.x, d.z), el = Math.asin(clamp(d.y, -1, 1)), A_ = Math.abs(az);
      const bottom = A_ < 1.6 ? lerp(-0.86, -0.66, sm(clamp((A_ - 0.75) / 0.85, 0, 1))) : lerp(-0.62, -0.42, sm(clamp((A_ - 1.6) / 1.2, 0, 1)));   // jaw guards come down low, the back stops at the skull base
      if (el < bottom) return false;
      if (A_ < 0.78 && el < 0.06) return false;                         // the face opening (up to the brow)
      return true; };
    const shellGeo = (r, filter) => { const sg = new THREE.SphereGeometry(r, 96, 64), pos = sg.attributes.position, idx = sg.index.array, out = [];
      for (let f = 0; f < idx.length; f += 3) { const c = V(0, 0, 0); for (let k = 0; k < 3; k++) c.add(V(pos.getX(idx[f + k]), pos.getY(idx[f + k]), pos.getZ(idx[f + k]))); c.normalize(); if (filter(c)) out.push(idx[f], idx[f + 1], idx[f + 2]); }
      sg.setIndex(out); return sg; };
    const shellM = new THREE.MeshPhysicalMaterial({ color: new THREE.Color(K.helmet).multiplyScalar(team === 'DET' ? 0.82 : 1), roughness: 0.22, clearcoat: 1, clearcoatRoughness: 0.08, metalness: team === 'DET' ? 0.25 : 0.1, side: THREE.DoubleSide });
    const shell = new THREE.Mesh(shellGeo(R0, keep), shellM); shell.scale.set(1.0, 1.06, 1.13); helmet.add(shell);
    const liner = new THREE.Mesh(shellGeo(R0 * 0.93, keep), mat(0x1a1b1e, 0.9)); liner.scale.copy(shell.scale); helmet.add(liner);   // pads inside
    if (K.stripe !== null) { const st = new THREE.Mesh(shellGeo(R0 * 1.004, d => keep(d) && Math.abs(d.x) < 0.07 && d.y > -0.35), new THREE.MeshPhysicalMaterial({ color: K.stripe, roughness: 0.35, clearcoat: 1, side: THREE.DoubleSide })); st.scale.copy(shell.scale); helmet.add(st); }
    // facemask: three bars across and a centre bar, curving back to the jaw guards (round tubes)
    const maskM = new THREE.MeshStandardMaterial({ color: K.mask, roughness: 0.4, metalness: 0.3 });
    const arc = (y, rz, a0, rxz) => { const pts = []; for (let i = 0; i <= 24; i++) { const a = lerp(-a0, a0, i / 24); pts.push(V(Math.sin(a) * rxz, y, Math.cos(a) * rz)); } return pts; };
    const bar = pts => { const t = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 48, 0.0055, 8), maskM); t.castShadow = true; helmet.add(t); };
    const sx = shell.scale;
    for (const [y, rz, a0] of [[-0.012, 0.172, 0.86], [-0.06, 0.178, 0.8], [-0.105, 0.165, 0.74]]) bar(arc(y, rz * sx.z / 1.13, a0, R0 * 1.02));
    bar([V(0, 0.0, R0 * sx.z * 0.98), V(0, -0.012, 0.172 * sx.z / 1.13), V(0, -0.06, 0.178 * sx.z / 1.13), V(0, -0.105, 0.165 * sx.z / 1.13)]);
    for (const s of [-1, 1]) bar([V(s * Math.sin(0.5) * R0 * 1.02, -0.012, Math.cos(0.5) * 0.172 * sx.z / 1.13), V(s * Math.sin(0.48) * R0 * 1.02, -0.06, Math.cos(0.48) * 0.178 * sx.z / 1.13), V(s * Math.sin(0.44) * R0 * 1.02, -0.105, Math.cos(0.44) * 0.165 * sx.z / 1.13)]);
    // chin strap and cup (white)
    const cup = new THREE.Mesh(new THREE.SphereGeometry(0.03, 16, 10, 0, Math.PI * 2, 0, Math.PI * 0.55), mat(0xf0f0ea, 0.4)); cup.rotation.x = Math.PI * 0.62; cup.scale.set(1.3, 1, 0.8); cup.position.set(0, -0.168, 0.062); cup.visible = false; helmet.add(cup);
    helmet.rotation.y = Math.atan2(fd.x, fd.z); helmet.position.copy(hc); hb.updateMatrixWorld(true); helmet.applyMatrix4(hb.matrixWorld.clone().invert()); hb.add(helmet);
    helmet.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } }); P.helmet = helmet; P.helmetShell = shell; }
  // shoulder pads under the jersey: the jersey itself is pushed out over the chest, back and shoulders (3-6 cm, thinning to nothing at the edges) in its
  // rest pose, so it stays one skinned cloth that bends with him (a rigid shell crumpled and gapped when his arms went up). The numbers, the name on the
  // back and the shoulder stripes are painted on it in rest-pose space.
  { const sh = Gx.meshes.shirt, g0 = sh.geometry, ga = g0.attributes, names = sh.skeleton.bones.map(b => b.name), N = ga.position.count;
    const chestY = wp(Gx.bones.chest).y, neckY = wp(Gx.bones.neck).y, shY = wp(Gx.bones.uarmR).y, yLow = chestY - 0.07, shX = Math.abs(wp(Gx.bones.uarmR).x);
    const pos = ga.position.clone(), rest = ga.position.clone(), nrm = ga.normal, rn = ga.normal.clone();
    for (let i = 0; i < N; i++) { let c = 0; for (let k = 0; k < 4; k++) { const n = names[ga.skinIndex.getComponent(i, k)]; if (/^(chest|clav|neck|spine2)/.test(n)) c += ga.skinWeight.getComponent(i, k); }
      const y = ga.position.getY(i), x = ga.position.getX(i);
      const t = sm(clamp((c - 0.25) / 0.45, 0, 1)) * sm(clamp((y - yLow) / 0.08, 0, 1)) * (1 - 0.35 * sm(clamp((Math.abs(x) - shX + 0.02) / 0.06, 0, 1)));
      const capn = sm(clamp((Math.abs(x) - shX + 0.12) / 0.1, 0, 1)) * sm(clamp((y - shY + 0.08) / 0.08, 0, 1));   // the shoulder caps
      const collar = 1 - sm(clamp((y - neckY + 0.1) / 0.07, 0, 1)) * (1 - capn);   // the neckline stays snug (pushed out it opened a gap round his neck)
      const off = (0.03 + 0.028 * capn) * t * collar, up = (0.01 + 0.025 * capn) * t * collar * sm(clamp((y - chestY) / 0.12, 0, 1)), outx = 0.025 * capn * t * Math.sign(x);
      pos.setXYZ(i, x + nrm.getX(i) * off + outx, y + nrm.getY(i) * off + up, ga.position.getZ(i) + nrm.getZ(i) * off); }
    g0.setAttribute('position', pos); g0.setAttribute('aRest', rest); g0.setAttribute('aRN', rn); g0.computeVertexNormals(); g0.computeBoundingSphere();
    const numT = numberTex(number, K), nmT = nameTex(name, K), cb = wp(Gx.bones.chest);
    const pm = sh.material, prev = pm.onBeforeCompile, prevKey = pm.customProgramCacheKey ? pm.customProgramCacheKey.bind(pm) : () => '';
    pm.roughness = 0.62; if (pm.isMeshPhysicalMaterial) { pm.sheen = 0.3; pm.sheenColor = new THREE.Color(0xffffff); }
    const U = { uNum: { value: numT }, uName: { value: nmT }, uC1: { value: lin(K.cap ? K.cap[0] : K.jersey) }, uC2: { value: lin(K.cap ? K.cap[1] : K.jersey) } };
    pm.onBeforeCompile = (s, r) => { if (prev) prev.call(pm, s, r); Object.assign(s.uniforms, U);
      s.vertexShader = 'attribute vec3 aRest; attribute vec3 aRN; varying vec3 vR; varying vec3 vRN;\n' + s.vertexShader.replace('#include <begin_vertex>', '#include <begin_vertex>\n vR = aRest; vRN = aRN;');
      s.fragmentShader = 'varying vec3 vR; varying vec3 vRN; uniform sampler2D uNum, uName; uniform vec3 uC1, uC2;\n' + s.fragmentShader.replace('#include <map_fragment>', `#include <map_fragment>
        { vec3 n = normalize(vRN); float cx = ${cb.x.toFixed(4)};
          ${K.cap ? `float ax = abs(vR.x), top_ = smoothstep(${(shY - 0.07).toFixed(4)}, ${(shY - 0.045).toFixed(4)}, vR.y) * smoothstep(0.35, 0.6, n.y);   // two stripes over the top of each shoulder, front to back
          float s1 = top_ * smoothstep(${(shX - 0.075).toFixed(4)}, ${(shX - 0.07).toFixed(4)}, ax) * (1.0 - smoothstep(${(shX - 0.045).toFixed(4)}, ${(shX - 0.04).toFixed(4)}, ax));
          float s2 = top_ * smoothstep(${(shX - 0.038).toFixed(4)}, ${(shX - 0.033).toFixed(4)}, ax) * (1.0 - smoothstep(${(shX - 0.022).toFixed(4)}, ${(shX - 0.017).toFixed(4)}, ax));
          diffuseColor.rgb = mix(diffuseColor.rgb, uC1, s1); diffuseColor.rgb = mix(diffuseColor.rgb, uC2, s2);` : ''}
          // numbers on the front and back (22 cm tall, under the collar); at rest he faces -z
          vec2 uv; float front = smoothstep(0.25, 0.45, -n.z), back = smoothstep(0.25, 0.45, n.z);
          float W = 0.30, H = 0.225, top = ${(neckY - 0.07).toFixed(4)};
          float tp = back > 0.0 ? top - 0.085 : top;
          uv = vec2((vR.x - cx) / W * (back > 0.0 ? 1.0 : -1.0) + 0.5, 1.0 - (tp - vR.y) / H * 0.82 - 0.09);
          vec4 nc = texture2D(uNum, uv); float inside = step(0.0, uv.x) * step(uv.x, 1.0) * step(0.0, uv.y) * step(uv.y, 1.0);
          float a = nc.a * inside * max(front, back); diffuseColor.rgb = mix(diffuseColor.rgb, nc.rgb, a);
          vec2 uvn = vec2((vR.x - cx) / 0.34 + 0.5, (vR.y - (tp + 0.012)) / 0.055); vec4 nn = texture2D(uName, uvn);   // the name across the upper back, above the number
          float inn = step(0.0, uvn.x) * step(uvn.x, 1.0) * step(0.0, uvn.y) * step(uvn.y, 1.0); diffuseColor.rgb = mix(diffuseColor.rgb, nn.rgb, nn.a * inn * back); }`); };
    pm.customProgramCacheKey = () => prevKey() + '|jersey' + team; pm.needsUpdate = true; P.pads = sh; }
  PLAYERS.push(P); return P; }
const CAMP = suitUp(G, 'DET', 46, 'CAMPBELL'), ONEIL = suitUp(K_O, 'DET', 66, "O'NEILL"), HOCK = suitUp(K_H, 'MIN', 87, 'HOCKENSON', true);
G.reset(); G.root.updateMatrixWorld(true);
// the football: a prolate spheroid, brown leather, white laces
const ball = new THREE.Group(); scene.add(ball);
{ const g = new THREE.SphereGeometry(1, 40, 24); g.scale(0.085, 0.085, 0.142); const pa = g.attributes.position;
  for (let i = 0; i < pa.count; i++) { const z = pa.getZ(i) / 0.142, k = Math.pow(1 - z * z, 0.12); pa.setX(i, pa.getX(i) * k); pa.setY(i, pa.getY(i) * k); } g.computeVertexNormals();
  const bm = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ color: 0x6a3418, roughness: 0.55 })); bm.castShadow = true; ball.add(bm);
  for (let i = -3; i <= 4; i++) { const l = box(0.028, 0.006, 0.006, 0, 0.083, i * 0.012, mat(0xf4f0e6, 0.6), 0, ball); }
  box(0.004, 0.006, 0.1, 0, 0.083, 0.005, mat(0xf4f0e6, 0.6), 0, ball); }
// readout (same look as the other news Shorts)
const hudC = document.createElement('canvas'); hudC.width = 520; hudC.height = 440; const hudT = new THREE.CanvasTexture(hudC); hudT.colorSpace = THREE.SRGBColorSpace;
const hud = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: hudT, transparent: true, depthTest: false, depthWrite: false, toneMapped: false })); hud.renderOrder = 30; camera.add(hud); scene.add(camera); hud.visible = false;
function drawHud(rows, flag) { const g = hudC.getContext('2d'); g.clearRect(0, 0, 520, 440); g.beginPath(); g.roundRect(6, 6, 508, 428, 34); g.fillStyle = 'rgba(8,14,22,0.74)'; g.fill(); g.lineWidth = 4; g.strokeStyle = 'rgba(160,200,235,0.55)'; g.stroke();
  let y = 30; for (const [lab, val, col] of rows) { g.fillStyle = '#9fb6c8'; g.font = '600 34px Arial, Helvetica, sans-serif'; g.fillText(lab, 34, y + 38); g.fillStyle = col || '#fff'; g.font = 'bold 62px Arial, Helvetica, sans-serif'; g.fillText(val, 34, y + 102, 452); y += 120; }
  if (flag) { g.font = 'bold 52px Arial, Helvetica, sans-serif'; const fw = Math.min(460, g.measureText(flag).width + 40); g.beginPath(); g.roundRect(30, 340, fw, 76, 16); g.fillStyle = flag.startsWith('+') ? '#1f9d55' : '#d9241b'; g.fill(); g.fillStyle = '#fff'; g.fillText(flag.replace(/^\+/, ''), 50, 397, fw - 40); }
  hudT.needsUpdate = true; }
function fitHud() { const d = camera.near * 1.6, h = 2 * d * Math.tan(camera.fov * D2R / 2), w = h * camera.aspect, gw = 0.4 * w, gh = gw * 440 / 520; hud.scale.set(gw, gh, 1); hud.position.set(w / 2 - gw / 2 - 0.035 * w, h / 2 - 0.165 * h - gh / 2, -d); }
// ------------------------------------------------------------------ x-ray: his body goes glassy; neck bones (C1-C7 and the top of the back), the spinal cord, nerve signals
const XRAYM = new THREE.MeshBasicMaterial({ color: 0x7fd3ff, transparent: true, opacity: 0.13, depthWrite: false, side: THREE.DoubleSide, blending: THREE.AdditiveBlending });
const XRSAVE = new Map(); let XRON = false;
const boneM = new THREE.MeshStandardMaterial({ color: 0xf1ead8, roughness: 0.45, emissive: 0x3a3428, emissiveIntensity: 0.6 });
const cordM = new THREE.MeshStandardMaterial({ color: 0xffd36a, roughness: 0.4, emissive: 0xffa21a, emissiveIntensity: 0.9 });
const SPINE = new THREE.Group(); scene.add(SPINE); SPINE.visible = false;
const VERTS = [];
function vertebra(s) { const g = new THREE.Group();
  const body = new THREE.Mesh(new THREE.CylinderGeometry(0.0115 * s, 0.012 * s, 0.013, 20), boneM); body.position.z = 0.012 * s; g.add(body);             // the round body in front
  const ring = new THREE.Mesh(new THREE.TorusGeometry(0.0095 * s, 0.0032 * s, 8, 24).rotateX(Math.PI / 2), boneM); ring.position.z = -0.006 * s; g.add(ring);   // the arch round the cord
  const spin = new THREE.Mesh(new THREE.ConeGeometry(0.004 * s, 0.022 * s, 8).rotateX(-Math.PI / 2 - 0.4), boneM); spin.position.set(0, -0.004, -0.022 * s); g.add(spin);  // the spike at the back
  for (const x of [-1, 1]) { const tp = new THREE.Mesh(new THREE.CapsuleGeometry(0.0028 * s, 0.012 * s, 4, 8).rotateZ(Math.PI / 2), boneM); tp.position.set(x * 0.017 * s, 0, -0.004 * s); g.add(tp); }   // side wings
  SPINE.add(g); return g; }
for (let i = 0; i < 11; i++) VERTS.push(vertebra(i < 7 ? 1.0 + i * 0.05 : 1.4 + (i - 7) * 0.06));   // C1..C7 then T1..T4 (bigger going down)
const skull = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 20), new THREE.MeshStandardMaterial({ color: 0xf1ead8, roughness: 0.5, transparent: true, opacity: 0.35, emissive: 0x3a3428, emissiveIntensity: 0.4, depthWrite: false }));
skull.scale.set(0.072, 0.085, 0.095); SPINE.add(skull);
const brainX = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 20), new THREE.MeshStandardMaterial({ color: 0xf0a6b4, emissive: 0x401018, emissiveIntensity: 0.6, roughness: 0.6 }));
{ const pa = brainX.geometry.attributes.position; for (let i = 0; i < pa.count; i++) { const x = pa.getX(i), y = pa.getY(i), z = pa.getZ(i), f = 1 + 0.04 * Math.sin(x * 23 + z * 17) * Math.sin(y * 19 + x * 7); pa.setXYZ(i, x * f, y * f, z * f); } brainX.geometry.computeVertexNormals(); }
brainX.scale.set(0.06, 0.05, 0.075); SPINE.add(brainX);
let cord = null; const pinchGlow = new THREE.Sprite(new THREE.SpriteMaterial({ map: canvasTex(128, 128, g => { const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64); gr.addColorStop(0, 'rgba(255,70,50,1)'); gr.addColorStop(0.45, 'rgba(255,40,30,0.45)'); gr.addColorStop(1, 'rgba(255,0,0,0)'); g.fillStyle = gr; g.fillRect(0, 0, 128, 128); }), transparent: true, depthWrite: false, depthTest: false, toneMapped: false, blending: THREE.AdditiveBlending }));
pinchGlow.renderOrder = 22; SPINE.add(pinchGlow);
// nerve signals: dots running out along paths (brain -> cord -> arms and legs)
const NSIG = 900; const sigG = new THREE.BufferGeometry(); const sigP = new Float32Array(NSIG * 3), sigC = new Float32Array(NSIG * 3);
sigG.setAttribute('position', new THREE.BufferAttribute(sigP, 3)); sigG.setAttribute('color', new THREE.BufferAttribute(sigC, 3));
const dotTex = canvasTex(64, 64, g => { const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.45, 'rgba(255,255,255,0.5)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); });
// the dots are tiny glowing beads (an instanced mesh: point sprites don't draw at size on this renderer)
const SIG = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1, 1), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, depthWrite: false, depthTest: false, blending: THREE.AdditiveBlending, toneMapped: false }), NSIG);
SIG.frustumCulled = false; SIG.renderOrder = 24; scene.add(SIG); SIG.visible = false; const _m4 = new THREE.Matrix4(), _c = new THREE.Color();
for (let i = 0; i < NSIG; i++) SIG.setColorAt(i, _c.setRGB(0, 0, 0));
const nerveM = new THREE.LineBasicMaterial({ color: 0xffc04a, transparent: true, opacity: 0.55, depthTest: false, blending: THREE.AdditiveBlending, toneMapped: false });
const NERVES = []; for (let i = 0; i < 5; i++) { const l = new THREE.Line(new THREE.BufferGeometry().setFromPoints(Array.from({ length: 40 }, () => V(0, 0, 0))), nerveM.clone()); l.renderOrder = 23; l.frustumCulled = false; scene.add(l); l.visible = false; NERVES.push(l); }
const XRSKIP = new Set([SPINE]);
function xray(on) { if (XRON === on) return; XRON = on; G.root.traverse(o => { if (!o.isMesh || XRSKIP.has(o)) return; if (on) { XRSAVE.set(o, o.material); o.material = XRAYM; o.castShadow = false; } else { o.material = XRSAVE.get(o) || o.material; o.castShadow = true; } }); SPINE.visible = on; }
// the neck curve: from the top of the chest to the base of the skull, bending the way his neck and head bones bend; a point a little behind it is the cord
function neckCurve() { const c = G.bones.chest, n = G.bones.neck, h = G.bones.head;
  const q0 = wq(c), qn = wq(n), qh = wq(h), up0 = V(0, 1, 0).applyQuaternion(qn), uph = V(0, 1, 0).applyQuaternion(qh);
  const p0 = wp(n).addScaledVector(V(0, 1, 0).applyQuaternion(q0), -0.075), p3 = wp(h).addScaledVector(uph, 0.01), L = p0.distanceTo(p3);
  const back = qq => FWD.clone().applyQuaternion(qq).multiplyScalar(-1);
  return { curve: new THREE.CubicBezierCurve3(p0, p0.clone().addScaledVector(up0, L * 0.4), p3.clone().addScaledVector(uph, -L * 0.4), p3), back0: back(qn), backh: back(qh), q0, qn, qh }; }
let FWD = V(0, 0, 1);   // his facing at rest (set from the eyes below)
{ G.reset(); G.root.updateMatrixWorld(true); const E = wp(G.bones.eyeR).add(wp(G.bones.eyeL)).multiplyScalar(0.5); FWD = E.sub(V(...G.man.headC)).setY(0).normalize(); }
const CORD = { pinch: 0, k: 0.55 };
function placeSpine() { const N = neckCurve(), cv = N.curve; const tmpQ = new THREE.Quaternion();
  const PTS = []; for (let i = 0; i <= 30; i++) { const u = i / 30, p = cv.getPoint(u), t = cv.getTangent(u).normalize(), b = N.back0.clone().lerp(N.backh, u).normalize(); PTS.push({ p, t, b }); }
  // C1 at the top (u = 1) down to C7 (u ~ 0.1), then T1..T4 below the curve along the chest
  for (let i = 0; i < 11; i++) { const v = VERTS[i]; let p, t, b;
    if (i < 7) { const u = 1 - (i + 0.5) / 7.3; p = cv.getPoint(u); t = cv.getTangent(u).normalize(); b = N.back0.clone().lerp(N.backh, u).normalize(); }
    else { const up = V(0, 1, 0).applyQuaternion(N.q0); p = cv.getPoint(0).addScaledVector(up, -0.024 * (i - 6)); t = up; b = FWD.clone().applyQuaternion(N.q0).multiplyScalar(-1); }
    const z = b.clone().multiplyScalar(-1); const x = new THREE.Vector3().crossVectors(t, z).normalize(); const zz = new THREE.Vector3().crossVectors(x, t);
    v.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(x, t, zz)); v.position.copy(p).addScaledVector(b, -0.006); }
  skull.position.copy(wp(G.bones.head)).add(V(0, 0.075, 0).applyQuaternion(N.qh)).addScaledVector(FWD.clone().applyQuaternion(N.qh), 0.015); skull.quaternion.copy(N.qh);
  brainX.position.copy(skull.position).add(V(0, 0.012, 0).applyQuaternion(N.qh)); brainX.quaternion.copy(N.qh);
  // the cord: through the arches, from the brain down past T4; squeezed at the pinch point
  const cp = [brainX.position.clone()]; for (let i = 0; i <= 30; i++) { const u = 1 - i / 30; cp.push(cv.getPoint(u).addScaledVector(N.back0.clone().lerp(N.backh, u).normalize(), 0.0)); }
  const up0 = V(0, 1, 0).applyQuaternion(N.q0); for (let k = 1; k <= 4; k++) cp.push(cv.getPoint(0).addScaledVector(up0, -0.024 * k));
  const curve = new THREE.CatmullRomCurve3(cp); if (cord) { SPINE.remove(cord); cord.geometry.dispose(); }
  const tg = new THREE.TubeGeometry(curve, 80, 0.0058, 10); const pa = tg.attributes.position, nb = 11;
  if (CORD.pinch > 0) for (let i = 0; i < pa.count; i++) { const seg = Math.floor(i / nb) / 80, d = Math.abs(seg - CORD.k), s = 1 - 0.6 * CORD.pinch * Math.exp(-(d * d) / 0.0012);   // squeeze the tube toward its own centre near the pinch
      const c = curve.getPoint(Math.min(1, Math.floor(i / nb) / 80)); pa.setXYZ(i, c.x + (pa.getX(i) - c.x) * s, c.y + (pa.getY(i) - c.y) * s, c.z + (pa.getZ(i) - c.z) * s); }
  tg.computeVertexNormals(); cord = new THREE.Mesh(tg, cordM); cord.renderOrder = 21; SPINE.add(cord); cordM.emissive.setRGB(1, lerp(0.63, 0.15, CORD.pinch), lerp(0.1, 0.05, CORD.pinch));
  pinchGlow.position.copy(curve.getPoint(CORD.k)); pinchGlow.scale.setScalar(0.09 * CORD.pinch); pinchGlow.visible = CORD.pinch > 0.02;
  return { curve }; }
// signal paths for this frame: the cord, then out to each hand and foot
function nervePaths(curve) { const top = curve.getPoints(30), base = top[top.length - 1];
  const arm = S => [base, wp(G.bones['clav' + S]), wp(G.bones['uarm' + S]), wp(G.bones['farm' + S]), wp(G.bones['hand' + S]), R_tip(S)];
  const leg = S => [base, wp(G.bones.spine2), wp(G.bones.spine1), wp(G.bones.hips), wp(G.bones['thigh' + S]), wp(G.bones['shin' + S]), wp(G.bones['foot' + S])];
  return { cord: top, armR: arm('R'), armL: arm('L'), legR: leg('R'), legL: leg('L') }; }
const R_tip = S => RG.tip('middle', S);
// fill the dots: `alive(path, u)` says how bright a dot is at that point along that path (0 = no signal)
function drawSignals(paths, t, alive) { let n = 0; const keys = ['cord', 'armR', 'armL', 'legR', 'legL'];
  keys.forEach((k, ki) => { const c = new THREE.CatmullRomCurve3(paths[k].map(p => p.clone()), false, 'centripetal'); const ln = NERVES[ki];
    const pts = c.getPoints(39); ln.geometry.setFromPoints(pts); ln.visible = true; ln.material.opacity = 0.18 + 0.4 * alive(k, 0.5);
    const per = k === 'cord' ? 14 : 22; for (let j = 0; j < per && n < NSIG; j++) { const u = ((j / per) + t * (k === 'cord' ? 0.55 : 0.45)) % 1, a = alive(k, u); const p = c.getPoint(u);
      const sz = 0.017 * (0.5 + 0.5 * a); _m4.makeScale(sz, sz, sz).setPosition(p); SIG.setMatrixAt(n, _m4); SIG.setColorAt(n, a > 0.5 ? _c.setRGB(0.25 * a, 1.0 * a, 0.75 * a) : _c.setRGB(a, a * 0.75, a * 0.2)); n++; } });
  for (let i = n; i < NSIG; i++) { _m4.makeScale(0, 0, 0); SIG.setMatrixAt(i, _m4); } SIG.instanceMatrix.needsUpdate = true; SIG.instanceColor.needsUpdate = true; SIG.count = NSIG; SIG.visible = true; }

// ------------------------------------------------------------------ the backboard, the trainer, the medical cart
const board = new THREE.Group(); scene.add(board); board.visible = false;
{ const om = mat(0xf27a12, 0.5); box(0.42, 0.045, 1.85, 0, 0.0225, 0, om, 0.02, board);
  for (const z of [-0.78, -0.4, 0.05, 0.42, 0.75]) box(0.5, 0.016, 0.07, 0, 0.32, z, mat(0x111216, 0.8), 0.006, board);   // straps (raised to his body height below)
  for (const x of [-1, 1]) box(0.09, 0.12, 0.16, x * 0.15, 0.1, -0.83, mat(0xd8241c, 0.6), 0.02, board); }               // head blocks
const BSTRAPS = board.children.slice(1, 6);
const TR = await loadGuy(THREE, '/char/' + (Q.get('char') || window.CHARDEF || 'guy'), { fingers3: !!window.FINGERS3 }); scene.add(TR.root); TR.root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
for (const [n, c] of [['shirt', 0x15171c], ['jeans', 0x8a7a5c], ['shoeR', 0x1a1a1c], ['shoeL', 0x1a1a1c]]) { const m = TR.meshes[n]; if (!m) continue; m.material = m.material.clone(); m.material.map = null; m.material.color.set(c); m.material.needsUpdate = true; }
const RT = makeRig(TR, 'trainer'); TR.root.visible = false;
const cart = new THREE.Group(); scene.add(cart); cart.visible = false;
{ const wm = mat(0xeeeeea, 0.45, 0.05), dk = mat(0x1d1f24, 0.7);
  box(1.25, 0.32, 3.4, 0, 0.48, 0, wm, 0.06, cart); box(1.25, 0.9, 0.12, 0, 1.0, -0.95, dk, 0.03, cart);                // body, seat back (the flat deck behind it carries the board)
  box(1.1, 0.14, 0.5, 0, 0.72, -1.25, dk, 0.04, cart); box(1.3, 0.06, 0.9, 0, 2.0, -1.2, wm, 0.03, cart);               // seat, roof
  for (const x of [-0.6, 0.6]) box(0.05, 1.3, 0.05, x, 1.35, -1.6, dk, 0, cart);
  for (const [x, z] of [[-0.62, -1.15], [0.62, -1.15], [-0.62, 1.1], [0.62, 1.1]]) { const wh = new THREE.Mesh(new THREE.CylinderGeometry(0.24, 0.24, 0.18, 20).rotateZ(Math.PI / 2), dk); wh.position.set(x, 0.24, z); cart.add(wh); }
  box(0.5, 0.06, 0.06, 0, 1.0, -1.2, dk, 0, cart); }
const CARTDECK = 0.64;
// straps across him: each one laid over the top of his body at its spot on the board (from his capsules)
function strapsOn(Px) { board.updateMatrixWorld(true); const inv = board.matrixWorld.clone().invert(), cs = caps(Px).filter(c => c.part !== 'arm');
  for (const st of BSTRAPS) { let top = 0.12; for (const c of cs) for (let k = 0; k <= 20; k++) { const p = c.a.clone().lerp(c.b, k / 20).applyMatrix4(inv); if (Math.abs(p.z - st.position.z) < 0.05 && Math.abs(p.x) < 0.25) top = Math.max(top, p.y + c.r); } st.position.y = top + 0.004; } }   // the flatbed top, where the board rides

// ------------------------------------------------------------------ poses (this rig: negative spine x bends forward)
function run(ph, lean = -12) { const s = Math.sin(ph), c = Math.cos(ph);
  return curl(curl({ spine1: [lean, 0, 0], chest: [-4, 0, 0], neck: [10, 0, 0], thighR: [24 + 46 * s, 0, 0], thighL: [24 - 46 * s, 0, 0],
    shinR: [-30 - 70 * Math.max(0, -s) - 15 * Math.max(0, c), 0, 0], shinL: [-30 - 70 * Math.max(0, s) - 15 * Math.max(0, -c), 0, 0], footR: [8 * s, 0, 0], footL: [-8 * s, 0, 0],
    armR: A(10 - 46 * s, 16, 0, 90), armL: A(10 + 46 * s, 16, 0, 90) }, 'R', 55), 'L', 55); }
const bob = ph => 0.93 + 0.035 * Math.abs(Math.cos(ph));
// Hockenson: the catch (hands up in front), then the ball tucked in his right arm
const CATCH = curl(curl({ spine1: [-8, 0, 0], neck: [6, 0, 0], thighR: [30, 0, 0], shinR: [-40, 0, 0], thighL: [5, 0, 0], shinL: [-25, 0, 0], armR: A(95, 18, 0, 35, 40), armL: A(95, 18, 0, 35, 40) }, 'R', 25), 'L', 25);
const carry = ph => { const p = run(ph, -16); p.armR = A(20, 12, 30, 112, 70); p.handR = [0, 0, 0]; return curl(p, 'R', 60); };
// the tackle: Campbell wraps high from the front and twists him down; O'Neill hits low from the side
const WRAP = curl(curl({ spine1: [-26, 0, 0], spine2: [-10, 0, 0], chest: [-6, 0, 0], neck: [18, 0, 0], head: [8, 0, 0], thighR: [55, 0, 0], shinR: [-60, 0, 0], thighL: [20, 0, 0], shinL: [-50, 0, 0],
  armR: A(85, 25, 10, 80, 20), armL: A(85, 25, 10, 80, 20) }, 'R', 45), 'L', 45);
const LOW = curl(curl({ spine1: [-30, 0, 0], spine2: [-14, 0, 0], chest: [-8, 0, 0], neck: [22, 0, 0], head: [10, 0, 0], thighR: [70, 0, 0], shinR: [-80, 0, 0], thighL: [35, 0, 0], shinL: [-70, 0, 0],
  armR: A(70, 30, 0, 60), armL: A(70, 30, 0, 60) }, 'R', 45), 'L', 45);
const HIT_H = curl(curl({ spine1: [10, 8, 0], chest: [6, 0, 0], neck: [-6, 0, 0], thighR: [20, 0, 0], shinR: [-35, 0, 0], thighL: [-5, 0, 0], shinL: [-20, 0, 0], armR: A(20, 12, 30, 112, 70), armL: A(40, 50, 0, 40) }, 'R', 60), 'L', 30);
// on the ground: Campbell face down and still (arms at his sides, head turned a little); Hockenson on his side; O'Neill getting up
const PRONE = curl(curl({ spine1: [2, 0, 0], neck: [10, 22, 0], head: [4, 20, 0], thighR: [4, 0, 4], shinR: [-14, 0, 0], thighL: [2, 0, -3], shinL: [-8, 0, 0], footR: [30, 0, 0], footL: [28, 0, 0],
  armR: A(-8, 16, 0, 20), armL: A(-8, 14, 0, 24) }, 'R', 25), 'L', 25);   // face down and still, arms at his sides
const SIDE = curl(curl({ spine1: [-10, 0, 6], thighR: [40, 0, 0], shinR: [-60, 0, 0], thighL: [20, 0, 0], shinL: [-40, 0, 0], armR: A(30, 12, 30, 100, 70), armL: A(40, 40, 0, 30) }, 'R', 50), 'L', 25);
const KNEEL = curl(curl({ spine1: [-8, 0, 0], neck: [26, 0, 0], head: [10, 0, 0], thighR: [85, 0, 0], shinR: [-88, 0, 0], footR: [0, 0, 0], thighL: [-6, 0, 0], shinL: [-100, 0, 0], footL: [-30, 0, 0],
  armR: A(28, 10, 0, 60), armL: A(10, 10, 0, 20) }, 'R', 30), 'L', 30);
const SUPINE = curl(curl({ neck: [0, 0, 0], head: [0, 0, 0], armR: A(-4, 8, 0, 8), armL: A(-4, 8, 0, 8), footR: [10, 0, 0], footL: [10, 0, 0] }, 'R', 18), 'L', 18);
const READY = curl(curl({ spine1: [-14, 0, 0], neck: [16, 0, 0], thighR: [32, 0, 6], shinR: [-48, 0, 0], thighL: [32, 0, -6], shinL: [-48, 0, 0], footR: [14, 0, 0], footL: [14, 0, 0], armR: A(30, 22, 0, 70), armL: A(30, 22, 0, 70) }, 'R', 40), 'L', 40);
// the hit, from the game photos: Hockenson bent over the ball; Campbell low at his right hip from the front, back flat, head up and turned, legs driving back;
// O'Neill low at his left hip from the side. (Root tilt pitches the whole body; positive thigh brings a leg forward.)
const H_HIT = curl(curl({ spine1: [-28, 4, 0], spine2: [-14, 0, 0], chest: [-8, 0, 0], neck: [10, 0, 0], head: [-12, 0, 0], thighR: [22, 0, 4], shinR: [-55, 0, 0], footR: [6, 0, 0], thighL: [46, 0, -4], shinL: [-52, 0, 0], footL: [-4, 0, 0],
  armR: A(40, 10, 30, 120, 60), armL: A(-28, 40, 0, 55) }, 'R', 60), 'L', 40);   // used with the root pitched 24 deg forward: bent low over the two of them
const H_FALL = curl(curl({ spine1: [-30, 6, 0], spine2: [-14, 0, 0], chest: [-8, 0, 0], neck: [16, 0, 0], head: [0, 0, 0], thighR: [10, 0, 6], shinR: [-25, 0, 0], footR: [30, 0, 0], thighL: [24, 0, -6], shinL: [-35, 0, 0], footL: [30, 0, 0],
  armR: A(40, 10, 30, 120, 60), armL: A(80, 45, 0, 40) }, 'R', 60), 'L', 30);
// Campbell (body flat, head pressed into his left hip, near knee almost down, far leg driving back)
const C_HIT = curl(curl({ spine1: [-6, 0, 0], spine2: [-6, 0, 0], chest: [-4, 0, 0], neck: [22, -8, 0], head: [8, -12, 0], thighR: [52, 0, 8], shinR: [-48, 0, 0], footR: [24, 0, 0], thighL: [30, 0, -4], shinL: [-34, 0, 0], footL: [30, 0, 0],
  armR: A(80, 20, 0, 70), armL: A(80, 30, 0, 70) }, 'R', 50), 'L', 50);
const C_FALL = curl(curl({ spine1: [-2, 0, 0], spine2: [-2, 0, 0], neck: [8, -16, 0], head: [4, -18, 0], thighR: [20, 0, 6], shinR: [-40, 0, 0], footR: [35, 0, 0], thighL: [4, 0, -4], shinL: [-25, 0, 0], footL: [35, 0, 0],
  armR: A(-8, 16, 0, 20), armL: A(-8, 14, 0, 24) }, 'R', 25), 'L', 25);   // he lands face first, arms limp at his sides
// O'Neill (leaning in high, head at his right shoulder, wide driving legs)
const O_HIT = curl(curl({ spine1: [-12, 0, 0], spine2: [-8, 0, 0], chest: [-4, 0, 0], neck: [24, 0, 0], head: [6, 12, 0], thighR: [52, 0, 8], shinR: [-62, 0, 0], footR: [6, 0, 0], thighL: [-12, 0, -8], shinL: [-30, 0, 0], footL: [28, 0, 0],
  armR: A(75, 25, 0, 75), armL: A(75, 25, 0, 75) }, 'R', 50), 'L', 50);
const O_DOWN = curl(curl({ spine1: [-20, 0, 0], spine2: [-8, 0, 0], neck: [24, 0, 0], head: [8, 0, 0], thighR: [70, 0, 6], shinR: [-120, 0, 0], footR: [-20, 0, 0], thighL: [60, 0, -6], shinL: [-120, 0, 0], footL: [-20, 0, 0],
  armR: A(60, 25, 0, 60), armL: A(60, 25, 0, 60) }, 'R', 40), 'L', 40);
const HIPS = { ...STAND, armR: A(10, 35, 40, 100), armL: A(10, 35, 40, 100) };
// ------------------------------------------------------------------ body capsules (with the pads and the helmet): the clip check, the ground, and the contact solve
function segDist(p1, q1, p2, q2) { const d1 = q1.clone().sub(p1), d2 = q2.clone().sub(p2), r = p1.clone().sub(p2), a = d1.dot(d1), e = d2.dot(d2), f = d2.dot(r);
  let s_, t_; if (a < 1e-9 && e < 1e-9) { s_ = t_ = 0; } else if (a < 1e-9) { s_ = 0; t_ = clamp(f / e, 0, 1); } else { const c = d1.dot(r); if (e < 1e-9) { t_ = 0; s_ = clamp(-c / a, 0, 1); } else { const b = d1.dot(d2), den = a * e - b * b;
    s_ = den > 1e-9 ? clamp((b * f - c * e) / den, 0, 1) : 0; t_ = (b * s_ + f) / e; if (t_ < 0) { t_ = 0; s_ = clamp(-c / a, 0, 1); } else if (t_ > 1) { t_ = 1; s_ = clamp((b - c) / a, 0, 1); } } }
  const c1 = p1.clone().addScaledVector(d1, s_), c2 = p2.clone().addScaledVector(d2, t_); return { d: c1.distanceTo(c2), c1, c2 }; }
function caps(Px) { const Gx = Px.G, b = n => wp(Gx.bones[n]);
  const N = b('neck'), C = b('chest'), S = b('spine1'), Hp = b('hips'), lat = b('uarmR').sub(b('uarmL')).normalize(), latH = b('thighR').sub(b('thighL')).normalize(), out = [];
  const cap = (a, c, r, part) => out.push({ a, b: c, r, part });
  for (const s of [-1, 1]) { cap(N.clone().lerp(C, 0.3).addScaledVector(lat, s * 0.085), S.clone().addScaledVector(lat, s * 0.075), 0.13, 'torso'); cap(S.clone().addScaledVector(lat, s * 0.07), Hp.clone().addScaledVector(latH, s * 0.065), 0.12, 'torso'); }
  for (const S_ of ['R', 'L']) { const u = b('uarm' + S_); cap(u, u, 0.095, 'pad'); }
  const hc = wp(Px.helmet), hf = V(0, 0, 1).applyQuaternion(wq(Px.helmet)); cap(hc, hc.clone().addScaledVector(hf, 0.04), 0.15, 'helmet');   // the shell and the facemask out front cap(N, b('head'), 0.06, 'neck');
  for (const S_ of ['R', 'L']) { cap(b('thigh' + S_).addScaledVector(latH, 0), b('shin' + S_), 0.08, 'leg'); cap(b('shin' + S_), b('foot' + S_), 0.055, 'leg'); cap(b('foot' + S_), Gx.tailW('foot' + S_), 0.045, 'foot');
    const ap = Px === HOCK && S_ === 'R' ? 'barm' : 'arm';   // his ball arm is locked to his chest: the body push treats it as body
    cap(b('uarm' + S_), b('farm' + S_), 0.052, ap); cap(b('farm' + S_), b('hand' + S_), 0.042, ap); cap(b('hand' + S_), Gx.tailW('middle2' + S_), 0.032, ap); }
  return out; }
const ARMP = new Set(['arm']);
// the deepest overlap between two players' capsules (arms left out with skipArms: arms are fixed by the hand solve, not by moving the body)
function overlap(A, B, skipArms = true) { const ca = caps(A), cb = caps(B); let best = { depth: 0 };
  for (const x of ca) { if (skipArms && ARMP.has(x.part)) continue; for (const y of cb) { if (skipArms && ARMP.has(y.part)) continue;
    const r = segDist(x.a, x.b, y.a, y.b), dep = x.r + y.r - r.d; if (dep > best.depth) best = { depth: dep, n: r.c1.clone().sub(r.c2).normalize(), x: x.part, y: y.part }; } }
  return best; }
// every overlap deeper than tol, arms included: the report the rig check reads
function clipList(list, tol = 0.006) { const out = [];
  for (let i = 0; i < list.length; i++) for (let j = i + 1; j < list.length; j++) { const A = list[i], B = list[j]; if (!A.G.root.visible || !B.G.root.visible) continue; const ca = caps(A), cb = caps(B);
    for (const x of ca) for (const y of cb) { const r = segDist(x.a, x.b, y.a, y.b), dep = x.r + y.r - r.d; if (dep > tol) out.push(`${A.number}:${x.part} in ${B.number}:${y.part} ${(dep * 100).toFixed(1)}cm`); } }
  for (const P of list) { if (!P.G.root.visible) continue; const cs = caps(P);   // his own arms through his own helmet or pads, his helmet into his own pads (head down)
    const hel = cs.find(c => c.part === 'helmet'); cs.filter(c => c.part === 'arm' || c.part === 'barm').forEach((x, j) => { const a0 = j % 3 === 0 ? x.a.clone().lerp(x.b, 0.3) : x.a;   // the top of the upper arm sits by the helmet at the shoulder: test from 30% down
      const r = segDist(a0, x.b, hel.a, hel.b); if (x.r + hel.r - r.d > 0.02) out.push(`${P.number}: arm in own helmet`); });
    const g = lowestOf(P); if (g < -0.008) out.push(`${P.number}: under the turf ${(g * 100).toFixed(1)}cm`); }
  return out; }
function lowestOf(Px) { let lo = 1e9; for (const c of caps(Px)) lo = Math.min(lo, Math.min(c.a.y, c.b.y) - c.r); return lo; }
const lowest = lowestOf;
// the hand solve pays for an arm inside someone else's body (their torso, pads, helmet, legs)
const OTHERS = new Map();
function armCost(R_) { return () => f => { const others = OTHERS.get(R_) || []; if (!others.length) return 0; let c = 0;
  const pts = []; for (let k = 0; k <= 3; k++) pts.push([f.sh.clone().lerp(f.el, k / 3), 0.05]); for (let k = 1; k <= 3; k++) pts.push([f.el.clone().lerp(f.p, k / 3), 0.042]);
  for (const [p, r] of pts) for (const y of others) { const d = segDist(p, p, y.a, y.b).d - (r + y.r); if (d < 0.004) c += ((d - 0.004) / 0.002) ** 2; }   // keep 4 mm clear; 1 cm in costs ~40 a point
  return c; }; }
// ------------------------------------------------------------------ the play, in real seconds from the catch (tau = 0), laid out from the game photos:
// Hockenson catches at the Lions 30 and turns upfield with the ball in his right arm; Campbell comes in low from his front-right and hits his right hip,
// O'Neill comes in low from his left; Hockenson pitches forward over them and lands on Campbell's upper back; Campbell stays face down at the 25.
const TC = 0.75, TDOWN = 1.6;
const ZC = zOf('DET', 30), ZHIT = zOf('DET', 27), ZDOWN = SPOT.z, HX = SPOT.x + 0.2;
const QB = V(-0.6, 1.9, zOf('DET', 42));
const yawOfDir = d => Math.atan2(-d.x, -d.z) / D2R;               // fwdOf(yaw) = (-sin, 0, -cos)
const DIRC = V(0.9, 0, 0.35).normalize(), YAWC = yawOfDir(DIRC);    // Campbell's line into him: from his front-left (photos: Campbell at his left hip)
const DIRO = V(-1, 0, -0.15).normalize(), YAWO = yawOfDir(DIRO);    // O'Neill's: from his right, a little behind (photos: O'Neill high at his right shoulder)
const HHIT = V(HX, 0, ZHIT);
function play(tau) { const o = {};
  // Hockenson
  if (tau < 0) { const ph = 1.2 + tau * 9.5; o.h = { pose: mixPose(run(ph), CATCH, smooth(-0.35, 0, tau)), pos: { x: HX + 0.2, y: bob(ph), z: ZC - tau * 6.2, yaw: lerp(0, -8, smooth(-0.6, 0, tau)) }, plant: false }; }
  else if (tau < TC) { const ph = 1.2 + tau * 9.5, k = smooth(TC - 0.32, TC - 0.04, tau);
    o.h = { pose: mixPose(mixPose(CATCH, carry(ph), smooth(0, 0.3, tau)), H_HIT, k), pos: { x: lerp(HX + 0.2, HX, tau / TC), y: lerp(bob(ph), 0.84, k), z: lerp(ZC, ZHIT, tau / TC), yaw: lerp(-8, 0, smooth(0, TC, tau)), tilt: -24 * k }, plant: k > 0.5 }; }
  else { const k = smooth(TC, TDOWN, tau);
    o.h = { pose: mixPose(H_HIT, H_FALL, smooth(TC, TC + 0.5, tau)), pos: { x: HX - 0.3 * k, y: lerp(0.84, 0.42, k), z: ZHIT - 0.45 * k, yaw: 14 * k, tilt: lerp(-24, -62, smooth(TC + 0.05, TDOWN, tau)), roll: 18 * k }, plant: false }; }
  o.ball = tau < 0 ? { free: true, k: clamp(1 + tau / 0.9, 0, 1) } : { free: false, k: smooth(0, 0.3, tau) };
  // Campbell: runs in on his line, gets low (back flat), hits; then goes down flat on his front, still driving
  const CPOS = HHIT.clone().addScaledVector(DIRC, -0.95);
  if (tau < TC) { const u = clamp((tau + 1.6) / (TC + 1.6), 0, 1), ph = 0.3 + tau * 8.5, k = smooth(TC - 0.4, TC - 0.02, tau), p = HHIT.clone().addScaledVector(DIRC, -lerp(4.6, 0.95, sm(u))).add(V(0, 0, -0.8 * (1 - u)));
    o.c = { pose: mixPose(tau < -0.8 ? READY : mixPose(READY, run(ph, -18), smooth(-0.8, -0.45, tau)), C_HIT, k), pos: { x: p.x, y: lerp(0.9, 0.66, k), z: p.z, yaw: YAWC, tilt: -64 * k }, plant: 'feet', wrap: smooth(TC - 0.42, TC - 0.1, tau) }; }
  else { const k = smooth(TC, TDOWN, tau), p = CPOS.clone().addScaledVector(DIRC, 0.22 * k);
    const fall = clamp((tau - TC) / (TDOWN - TC - 0.25), 0, 1);   // dropping under gravity to his front
    o.c = { pose: mixPose(C_HIT, C_FALL, k), pos: { x: p.x, y: lerp(0.66, 0.2, fall * fall), z: p.z, yaw: YAWC, tilt: lerp(-72, -87, smooth(0, 1, fall)) }, plant: false, wrap: 1 - smooth(TC + 0.02, TC + 0.32, tau) }; }
  // O'Neill: chasing from behind the quarterback, low into his left hip, then down to his knees holding on
  const OPOS = HHIT.clone().addScaledVector(DIRO, -0.6);
  if (tau < TC) { const u = clamp((tau + 1.6) / (TC + 1.6), 0, 1), ph = 2.0 + tau * 9.5, k = smooth(TC - 0.4, TC - 0.02, tau), from = HHIT.clone().add(V(3.2, 0, 3.4)), p = from.lerp(OPOS, sm(u));
    o.o = { pose: mixPose(run(ph, -18), O_HIT, k), pos: { x: p.x, y: lerp(0.92, 0.86, k), z: p.z, yaw: lerp(140, YAWO, smooth(-0.6, TC - 0.1, tau)), tilt: -26 * k }, plant: true, wrap: smooth(TC - 0.4, TC - 0.1, tau) }; }
  else { const k = smooth(TC, TDOWN, tau), p = OPOS.clone().add(V(-0.24 * k, 0, -0.36 * k));   // he goes down with him, still holding on
    o.o = { pose: mixPose(O_HIT, O_DOWN, k), pos: { x: p.x, y: lerp(0.86, 0.6, k), z: p.z, yaw: YAWO + 10 * k, tilt: lerp(-26, -30, k) }, plant: true, wrap: 1 }; }
  return o; }
// Hockenson's body frame (from his bones): right, up, forward
function frameOf(Px) { const Gx = Px.G, lat = wp(Gx.bones.uarmR).sub(wp(Gx.bones.uarmL)).normalize(), up = wp(Gx.bones.neck).sub(wp(Gx.bones.spine1)).normalize(), fwd = new THREE.Vector3().crossVectors(up, lat).normalize();
  return { lat, up, fwd, chest: wp(Gx.bones.chest), waist: wp(Gx.bones.spine1) }; }
function tuck(Px) { const F = frameOf(Px), c = F.chest.clone().addScaledVector(F.fwd, 0.2).addScaledVector(F.lat, 0.1).addScaledVector(F.up, -0.13);
  const ax = F.fwd.clone().multiplyScalar(0.85).addScaledVector(F.up, 0.3).addScaledVector(F.lat, -0.2).normalize(); return { c, ax, F }; }
// put a player down: pose, then plant him on the turf (lowest point on the ground) or just keep him out of it
function place(Px, R_, s) { if (!s) { Px.G.root.visible = false; return; } Px.G.root.visible = true; R_.applyPose(s.pose, s.pos); R_.untwist(); Px.G.root.updateMatrixWorld(true); ground(Px, s.plant !== false); }
function ground(Px, plant) { const lo = lowestOf(Px); let dy = 0;
  if (plant === 'feet') { let f = 1e9; for (const c of caps(Px)) if (c.part === 'foot') f = Math.min(f, Math.min(c.a.y, c.b.y) - c.r); dy = Math.max(0.002 - f, 0.002 - lo); }   // feet on the turf, nothing under it
  else if (plant || lo < 0.002) dy = 0.002 - lo;
  if (dy) { Px.G.root.position.y += dy; Px.G.root.updateMatrixWorld(true); } }
// push movers out of the bodies they overlap (arms are left to the hand solve); `flat` keeps a planted player's feet down (sideways push only)
function resolve(pairs, iters = 10) { for (let it = 0; it < iters; it++) { let worst = 0;
  for (const [A, B, flat, arms, wA = 1, flatB = true] of pairs) { if (!A.G.root.visible || !B.G.root.visible) continue; const ov = overlap(A, B, !arms); if (ov.depth <= 0.001) continue; worst = Math.max(worst, ov.depth);
    // A moves wA of the way out along the overlap normal, B the rest the other way (a flat mover only slides sideways)
    for (const [P, w, sg, fl] of [[A, wA, 1, flat], [B, 1 - wA, -1, flatB]]) { if (w <= 1e-4) continue; const d = ov.n.clone().multiplyScalar(sg);
      if (fl) { d.y = 0; if (d.lengthSq() < 1e-6) continue; d.normalize(); const c = Math.max(0.2, Math.abs(ov.n.dot(d))); P.G.root.position.addScaledVector(d, w * (ov.depth + 0.002) / c); }
      else P.G.root.position.addScaledVector(d, w * (ov.depth + 0.002)); P.G.root.updateMatrixWorld(true); } }
  if (worst < 0.002) break; } }
// the hands: wraps round Hockenson's hips (targets on his body frame, palms toward him), every arm kept out of the other bodies
const HANDS = (R_, list, key, frame) => { R_.hands(list, key, frame); R_.untwist(); R_.G.root.updateMatrixWorld(true); };
for (const R_ of [RG, RH, RO, RT]) R_.contactCost = armCost(R_);
const LASTT = {};
const ownHelmet = P => caps(P).filter(x => x.part === 'helmet');
// a hand target on the outside of a body: start at `c`, walk out along `dir` until the hand (radius 3.5 cm + 5 mm) clears every capsule of `body`
function outside(body, c, dir, gap = 0.04) { const cs = caps(body), d = dir.clone().normalize(); for (let r = 0.05; r < 0.6; r += 0.005) { const p = c.clone().addScaledVector(d, r);
    if (cs.every(y => segDist(p, p, y.a, y.b).d > y.r + gap)) return p; } return c.clone().addScaledVector(d, 0.6); }
const around = (F, a) => F.fwd.clone().setY(0).normalize().multiplyScalar(Math.cos(a * D2R)).addScaledVector(F.lat.clone().setY(0).normalize(), Math.sin(a * D2R));   // 0 = his front, 90 = his right, -90 = his left
function wrapTargets(F, who) { const hp = wp(HOCK.G.bones.hips).addScaledVector(F.up, 0.04), ch = F.chest.clone().addScaledVector(F.up, 0.06);
  if (who === 'c') return [{ S: 'L', p: outside(HOCK, hp.clone().add(V(0, -0.08, 0)), around(F, -30)), c: 45 }, { S: 'R', p: outside(HOCK, hp, around(F, -125)), c: 45 }];   // round his hips: near arm in front of his left hip, far arm behind it
  return [{ S: 'R', p: outside(HOCK, ch.clone().addScaledVector(F.up, 0.08), around(F, 60)), c: 45 }, { S: 'L', p: outside(HOCK, ch, around(F, 160)), c: 45 }]; }   // over his right shoulder, and round his back
// bodies apart along fixed directions, by bisection (so the result changes smoothly with play time): Campbell backs off along his run line while
// they stand, Hockenson rides up onto him as they go down (a blend between); O'Neill backs off along his own line from both of them
function pushOut(movers, clear) { const save = movers.map(([P]) => P.G.root.position.clone()), at = s => { movers.forEach(([P, d], i) => { P.G.root.position.copy(save[i]).addScaledVector(d, s); P.G.root.updateMatrixWorld(true); }); };
  if (clear()) return; let lo = 0, hi = 0.05; at(hi); while (!clear() && hi < 1.6) { lo = hi; hi *= 2; at(hi); }
  for (let k = 0; k < 18; k++) { const m = (lo + hi) / 2; at(m); if (clear()) hi = m; else lo = m; } at(hi); }
const apart = (A, B, tol = 0.001) => overlap(A, B).depth <= tol;
function separatePlay(tau) { const wf = smooth(TC - 0.02, TC + 0.3, tau), back = DIRC.clone().negate();
  pushOut([[CAMP, back.clone().multiplyScalar(1 - wf)], [HOCK, V(0, wf, 0)]], () => apart(CAMP, HOCK));
  pushOut([[ONEIL, DIRO.clone().negate()]], () => apart(ONEIL, HOCK) && apart(ONEIL, CAMP)); }
// arm solve without history (the same answer whatever frame came before, so render chunks match): coordinate descent from a fixed seed over human joint
// limits, paying for a missed target, a turned palm, distance from an anchor pose, and any point of the arm inside another body (or his own torso / helmet)
function contactPts(f) { const pts = []; for (let k = 1; k <= 6; k++) pts.push([f.sh.clone().lerp(f.el, k / 6), 0.053]); for (let k = 1; k <= 6; k++) pts.push([f.el.clone().lerp(f.p, k / 6), 0.044]); for (const k of [0.025, 0.05, 0.075, 0.1]) pts.push([f.p.clone().addScaledVector(f.u, k), 0.032]); return pts; }   // the fingers too
let CALLN = 0, WARM_IN = null, WARM_OUT = {}, CALLK = {}; const FING = {};
function armSolve(R_, S, o) { const others = o.others || [], key = R_.tag + S + ':' + (o.p ? 'p' : 'n') + (o.n ? 'n' : '') + ':' + (o.ascale || 0) + ':' + (o.steps ? o.steps[0] : 16) + ':' + (CALLK[R_.tag + S] = (CALLK[R_.tag + S] || 0) + 1);
  const cost = a => { const f = R_.handFK(S, a); let c = 0;
    if (o.p) c += f.p.distanceToSquared(o.p) / (0.008 * 0.008);
    if (o.n) c += (1 - f.n.dot(o.n)) * 30; if (o.u) c += (1 - f.u.dot(o.u)) * 20;
    if (o.anchor) for (let i = 0; i < 7; i++) c += ((a[i] - o.anchor[i]) / (o.ascale || 3)) ** 2;
    for (let i = 0; i < 7; i++) { const [lo, hi] = ARM_LIM[i], mid = [20, 15, 0, 60, 0, 0, 0][i]; c += 0.6 * ((a[i] - mid) / (hi - lo)) ** 2; }
    const wr = wp(R_.G.bones['hand' + S]), tip = R_.G.tailW('middle2' + S);   // the arm as the same capsules the clip report uses
    for (const [p0, p1, r] of [[f.sh, f.el, 0.052], [f.el, wr, 0.042], [wr, tip, 0.032]]) for (const y of others) { const d = segDist(p0, p1, y.a, y.b).d - (r + y.r); if (d < 0.008) c += ((d - 0.008) / 0.002) ** 2; }   // keep 8 mm clear
    return c; };
  const sd0 = WARM_IN && WARM_IN[key] ? WARM_IN[key] : o.seed;   // warm start from the same solve one step earlier (table build only)
  let a = sd0.map((v, i) => clamp(v, ARM_LIM[i][0], ARM_LIM[i][1])), ca = cost(a);
  if (WARM_IN && WARM_IN[key]) { const b0 = o.seed.map((v, i) => clamp(v, ARM_LIM[i][0], ARM_LIM[i][1])), cb0 = cost(b0); if (cb0 < ca - 25) { a = b0; ca = cb0; } }
  for (const step of o.steps || [16, 8, 4, 2, 1, 0.5]) { let imp = true, g = 0; while (imp && g++ < 12) { imp = false; for (let i = 0; i < 7; i++) for (const sg of [1, -1]) { const b = a.slice(); b[i] = clamp(b[i] + sg * step, ARM_LIM[i][0], ARM_LIM[i][1]); const cb = cost(b); if (cb < ca - 1e-9) { a = b; ca = cb; imp = true; } } } }
  WARM_OUT[key] = a; R_.setArm(S, a); R_.LAST['arm' + S] = a; const f = R_.handFK(S, a); return { a, c: ca, miss: o.p ? f.p.distanceTo(o.p) : 0 }; }
const ownBody = P => caps(P).filter(x => x.part === 'helmet' || x.part === 'torso');
const BODYOF = P => caps(P);
const SEEDS = {};
const CANDS = [A(150, 30, 0, 40), A(120, 60, 30, 60), A(160, 10, -30, 30), A(100, 40, 60, 90), A(140, 20, 40, 70), A(90, 20, 0, 100), A(130, 45, -40, 50), A(70, 50, 30, 80)];
function fingersAll(R_, S, c) { FING[R_.tag + S] = c; const pp = {}; curl(pp, S, c); for (const [n, e] of Object.entries(pp)) if (R_.G.bones[n]) R_.G.bones[n].quaternion.copy(R_.G.REST[n].q).multiply(qTmp.setFromEuler(eTmp.set(e[0] * D2R, e[1] * D2R, e[2] * D2R))); }
function stagePlayRaw(o, tau, frame) { CALLN = 0; WARM_OUT = {}; CALLK = {}; for (const R_ of [RG, RO, RH]) for (const S of ['R', 'L']) FING[R_.tag + S] = null;
  place(HOCK, RH, o.h); place(CAMP, RG, o.c); place(ONEIL, RO, o.o);
  const falling = tau > TC + 0.05;
  separatePlay(tau);
  for (const [P, s] of [[HOCK, o.h], [CAMP, o.c], [ONEIL, o.o]]) ground(P, s.plant !== false);
  // Hockenson's right hand: the ball comes from his hands into the tuck under his right arm
  const T = tuck(HOCK), bk = o.ball;
  if (!bk.free) { const handsMid = wp(HOCK.G.bones.handR).lerp(wp(HOCK.G.bones.handL), 0.5).addScaledVector(T.F.fwd, 0.07), c = handsMid.lerp(T.c, bk.k);
    ball.position.copy(c); ball.quaternion.setFromUnitVectors(V(0, 0, 1), T.ax);
    if (bk.k > 0.02) { const p = c.clone().addScaledVector(T.ax, 0.07).addScaledVector(T.F.up, 0.05), pose = RH.LAST.armR.slice();
      const r = armSolve(RH, 'R', { p, n: c.clone().sub(p).normalize(), u: T.ax.clone(), seed: SEEDS.hR || pose, others: [...caps(CAMP), ...caps(ONEIL)].filter(x => x.part !== 'arm').concat(ownHelmet(HOCK)) });
      const bl = pose.map((v, i) => lerp(v, r.a[i], bk.k)); RH.setArm('R', bl); RH.LAST.armR = bl; fingersAll(RH, 'R', lerp(60, 55, bk.k)); } }
  else { const q = QB.clone().lerp(wp(HOCK.G.bones.handR).lerp(wp(HOCK.G.bones.handL), 0.5).addScaledVector(frameOf(HOCK).fwd, 0.07), bk.k).add(V(0, 2.0 * Math.sin(Math.PI * bk.k), 0)); ball.position.copy(q); ball.quaternion.setFromUnitVectors(V(0, 0, 1), V(0.1, -0.15, 1).normalize()); }
  // the defenders' wraps (targets just outside his body), blended in from their running arms; then every arm nudged out of every body
  const F = frameOf(HOCK);
  for (const [P, R_, s, who, oth, pass] of [[CAMP, RG, o.c, 'c', [HOCK, ONEIL], 1], [ONEIL, RO, o.o, 'o', [HOCK, CAMP], 1], [CAMP, RG, o.c, 'c', [HOCK, ONEIL], 2]]) {
    const others = oth.flatMap(q => BODYOF(q)).concat(ownHelmet(P)), tg = s.wrap > 0.01 ? wrapTargets(F, who) : null; if (tg) LASTT[who] = tg;
    for (const S of ['R', 'L']) { const pose = pass === 1 ? (s.pose['arm' + S] || ARM0).slice() : R_.LAST['arm' + S].slice(); let a = pose;
      if (tg && tau > TC && s.wrap < 0.999) {   // letting go: the hand travels from the hold to where the pose puts it, the arm eased from the hold arm to the pose arm
        const h = tg.find(x => x.S === S), k = sm(1 - s.wrap), sd = SEEDS[who + S] || pose, anc = sd.map((v, i) => lerp(v, pose[i], k));
        const pp = R_.handFK(S, pose).p, away = h.p.clone().sub(wp(HOCK.G.bones.spine1)).setY(0).normalize();
        const tgt = h.p.clone().lerp(pp, k).addScaledVector(away, 0.25 * Math.sin(Math.PI * k)).add(V(0, 0.1 * Math.sin(Math.PI * k), 0));
        a = armSolve(R_, S, { p: tgt, seed: anc, others, anchor: anc, ascale: 12 }).a; fingersAll(R_, S, lerp(25, 45, s.wrap)); }
      else if (tg) { const h = tg.find(x => x.S === S), r = armSolve(R_, S, { p: h.p, seed: pass === 1 ? (SEEDS[who + S] || pose) : R_.LAST['arm' + S], others, anchor: SEEDS[who + S] || pose, ascale: 40 });
        a = pass === 1 ? pose.map((v, i) => lerp(v, r.a[i], s.wrap)) : r.a; fingersAll(R_, S, lerp(50, 45, s.wrap)); }
      armSolve(R_, S, { seed: a, anchor: a, ascale: falling ? 30 : 10, others, steps: [16, 8, 4, 2, 1, 0.5] }); } }
  // Hockenson's free arm last: kept out of everyone
  armSolve(RH, 'L', { seed: RH.LAST.armL, anchor: RH.LAST.armL, ascale: 10, others: [...caps(CAMP), ...caps(ONEIL)].concat(ownHelmet(HOCK)), steps: [16, 8, 4, 2, 1, 0.5] });
  // one more pass over every arm against everyone (each arm moved last sees the others' final arms)
  for (const [P, R_, oth] of [[CAMP, RG, [HOCK, ONEIL]], [ONEIL, RO, [HOCK, CAMP]], [HOCK, RH, [CAMP, ONEIL]]]) { const others = oth.flatMap(q => caps(q)).concat(ownHelmet(P));
    for (const S of ['R', 'L']) { if (P === HOCK && S === 'R' && !bk.free && bk.k > 0.5) continue; const a = R_.LAST['arm' + S].slice(); armSolve(R_, S, { seed: a, anchor: a, ascale: 10, others, steps: [16, 8, 4, 2, 1, 0.5] }); } }
  for (const R_ of [RG, RO, RH]) { R_.untwist(); R_.G.root.updateMatrixWorld(true); }
  for (let k = 0; k < 3; k++) { for (const [P, s] of [[HOCK, o.h], [CAMP, o.c], [ONEIL, o.o]]) ground(P, false); separatePlay(tau); } }
// the play's arms are solved once at load, in order along a fine grid of play time (each step warm-started from the one before), and every frame
// reads the table (bodies, arms, fingers, ball) and blends between grid steps: no solving at render time, so any chunk of frames comes out the
// same as a straight run, and the solver can't flip between answers from one frame to the next.
const TAU0 = -1.7, TAU1 = TDOWN + 0.15, DTAU = 1 / 120; let TAB = null;
function snap() { const S_ = p => ({ pos: p.G.root.position.clone(), q: p.G.root.quaternion.clone() }); const r = {};
  for (const [nm, P, R_] of [['c', CAMP, RG], ['o', ONEIL, RO], ['h', HOCK, RH]]) r[nm] = { ...S_(P), R: R_.LAST.armR.slice(), L: R_.LAST.armL.slice(), fR: FING[R_.tag + 'R'], fL: FING[R_.tag + 'L'] };
  r.ball = { pos: ball.position.clone(), q: ball.quaternion.clone() }; return r; }
function buildTable() { TAB = []; WARM_IN = null; const n = Math.ceil((TAU1 - TAU0) / DTAU);
  for (let k = 0; k <= n; k++) { const tau = TAU0 + k * DTAU; stagePlayRaw(play(tau), tau, -1); WARM_IN = WARM_OUT; TAB.push(snap()); } WARM_IN = null; }
function stagePlay(o, tau, frame) { if (!TAB || tau < TAU0 || tau > TAU1) return stagePlayRaw(o, tau, frame);
  const x = (tau - TAU0) / DTAU, i = Math.min(TAB.length - 2, Math.floor(x)), f = x - i, A_ = TAB[i], B_ = TAB[i + 1];
  place(HOCK, RH, o.h); place(CAMP, RG, o.c); place(ONEIL, RO, o.o);
  for (const [nm, P, R_] of [['c', CAMP, RG], ['o', ONEIL, RO], ['h', HOCK, RH]]) { const a = A_[nm], b = B_[nm];
    P.G.root.position.copy(a.pos).lerp(b.pos, f); P.G.root.quaternion.copy(a.q).slerp(b.q, f); P.G.root.updateMatrixWorld(true);
    for (const S of ['R', 'L']) { const arm = a[S].map((v, j) => lerp(v, b[S][j], f)); R_.setArm(S, arm); R_.LAST['arm' + S] = arm; const fa = a['f' + S], fb = b['f' + S]; if (fa != null && fb != null) fingersAll(R_, S, lerp(fa, fb, f)); }
    R_.untwist(); P.G.root.updateMatrixWorld(true); }
  ball.position.copy(A_.ball.pos).lerp(B_.ball.pos, f); ball.quaternion.copy(A_.ball.q).slerp(B_.ball.q, f); }
// seeds: solved once at load from a fixed moment (the hit), from several starting arms, so every frame starts its solve from the same good arm
function makeSeeds() { const tau = TC - 0.03, o = play(tau); place(HOCK, RH, o.h); place(CAMP, RG, o.c); place(ONEIL, RO, o.o);
  resolve([[CAMP, HOCK, true], [ONEIL, HOCK, true], [ONEIL, CAMP, true]]); for (const [P, s] of [[HOCK, o.h], [CAMP, o.c], [ONEIL, o.o]]) ground(P, s.plant !== false);
  const T = tuck(HOCK), c = T.c, p = c.clone().addScaledVector(T.ax, 0.07).addScaledVector(T.F.up, 0.05); let best = null;
  for (const sd of [RH.LAST.armR, ...CANDS]) { const r = armSolve(RH, 'R', { p, n: c.clone().sub(p).normalize(), u: T.ax.clone(), seed: sd, others: ownHelmet(HOCK) }); if (!best || r.c < best.c) best = r; } SEEDS.hR = best.a; RH.setArm('R', best.a);
  const F = frameOf(HOCK);
  for (const [P, R_, who, oth] of [[CAMP, RG, 'c', [HOCK, ONEIL]], [ONEIL, RO, 'o', [HOCK, CAMP]]]) { const tg = wrapTargets(F, who), others = oth.flatMap(q => BODYOF(q)).concat(ownHelmet(P));
    for (const h of tg) { let b = null; for (const sd of [R_.LAST['arm' + h.S], ...CANDS]) { const r = armSolve(R_, h.S, { p: h.p, seed: sd, others }); if (!b || r.c < b.c) b = r; } SEEDS[who + h.S] = b.a; R_.setArm(h.S, b.a); } }
  return SEEDS; }
const FWD_H = () => frameOf(HOCK).fwd;
// ------------------------------------------------------------------ story: one shot per line
const XRL = [6, 7, 8, 12];
const SLOW0 = [TC - 0.08, TC + 0.02];       // the hook: almost frozen at the hit
function shot(t) { const nb = beatAt(t), lt = t - B[nb], dur = DUR[nb], u = lt / dur;
  hud.visible = false; board.visible = false; cart.visible = false; TR.root.visible = false; SIG.visible = false; NERVES.forEach(l => l.visible = false); CORD.pinch = 0;
  for (const P of PLAYERS) P.G.root.visible = true; ball.visible = true;
  let cp, ct, fov = 34, near = 0.05, xr = false, roll = 0;
  const ST = { c: null, h: null, o: null };
  // the hook camera: from the photo side (his front and Campbell's back, O'Neill on the left), swinging slowly
  const camHook = (lt0) => { const a = (lerp(172, 150, lt0 / DUR[0])) * D2R, c = V(HX - 0.1, 0.9, ZHIT - 0.05); return { cp: V(c.x + Math.sin(a) * 4.2, 1.2, c.z + Math.cos(a) * 4.2), ct: c }; };
  switch (nb) {
    case 0: case 13: { // the hit: nearly frozen, the camera circling (13 runs the play in real time and lands on frame one)
      let tau, cam;
      if (nb === 0) { tau = lerp(SLOW0[0], SLOW0[1], u); cam = camHook(lt); }
      else { const left = dur - lt; tau = SLOW0[0] - left * 0.85; const h = camHook(0), k = smooth(0, dur * 0.85, lt);
        cam = { cp: V(SPOT.x - 9, 6, ZC + 9).lerp(h.cp, k), ct: V(SPOT.x, 0.9, ZC - 1).lerp(h.ct, k) };
        hud.visible = lt < dur * 0.6; drawHud([['GET WELL', 'SOON', '#2fbf71'], ['#46', 'JACK CAMPBELL']]); }
      ST.play = play(tau); ST.tau = tau; cp = cam.cp; ct = cam.ct; fov = 32; break; }
    case 1: { // who he is: Campbell, ready, at the 25 before the snap; push in
      ST.c = { pose: READY, pos: { x: SPOT.x - 0.5, y: 0.84, z: ZDOWN - 2.6, yaw: 180 } }; ST.h = null; ST.o = null; ball.visible = false;
      const c = V(SPOT.x - 0.5, 1.25, ZDOWN - 2.6); cp = V(c.x + lerp(1.6, 1.0, u), lerp(1.45, 1.35, u), c.z + lerp(3.6, 2.4, u)); ct = c.clone(); fov = 34;
      hud.visible = true; drawHud([['LIONS #46', 'CAMPBELL'], ['ALL-PRO', 'LINEBACKER', '#ffd23a']]); break; }
    case 2: { // Ford Field, the 4th quarter, the snap: a high broadcast view as the play starts (the three players in it)
      const tau = lerp(-1.6, -0.9, u); ST.play = play(tau); ST.tau = tau;
      cp = V(SPOT.x - 14 + 3 * u, 10 - u, ZC - 13 + 2 * u); ct = V(SPOT.x + 0.5, 0.6, ZC - 0.5); fov = 30;
      hud.visible = true; drawHud([['4TH QUARTER', 'LIONS 12-7'], ['3RD & 15', 'AT DET 35', '#ffd23a']]); break; }
    case 3: { // the short pass over the middle: real time, the camera tracking him
      const tau = lerp(-1.5, 0.5, u), o = play(tau); ST.play = o; ST.tau = tau;
      const hz = o.h.pos.z; cp = V(HX + 3.6, 1.55, hz + 3.4); ct = V(HX + 0.1, 1.0, hz - 0.6); fov = 36; break; }
    case 4: { // SLOW MOTION from the side: the hit and the twist down
      const tau = lerp(TC - 0.2, TDOWN + 0.05, smooth(0.02, 0.97, u)); ST.play = play(tau); ST.tau = tau;
      const c = V(HX + 0.3, lerp(0.85, 0.4, smooth(TC, TDOWN, tau)), lerp(ZHIT, ZHIT - 0.4, smooth(TC, TDOWN, tau)));
      const a = lerp(205, 160, u) * D2R; cp = V(c.x + Math.sin(a) * 4.4, lerp(1.15, 0.95, u), c.z + Math.cos(a) * 4.4); ct = c; fov = 32; roll = lerp(-3, 3, u); break; }
    case 5: { // face down, not moving; the others get up around him (overhead, slow)
      const o = play(TDOWN); ST.c = { pose: PRONE, pos: { ...o.c.pos, tilt: -87 }, plant: false };
      const hp = o.h.pos, ku = smooth(0.2, 0.9, u); ST.h = { pose: mixPose(SIDE, KNEEL, ku), pos: { x: hp.x + 0.8, y: lerp(0.3, 0.6, ku), z: hp.z - 0.1, yaw: lerp(-60, 60, ku), roll: lerp(-80, 0, smooth(0.15, 0.8, u)) }, plant: ku > 0.6 };
      ST.o = { pose: mixPose(KNEEL, STAND, smooth(0.1, 0.8, u)), pos: { x: o.o.pos.x - 0.3, y: lerp(0.6, 0.95, smooth(0.1, 0.8, u)), z: o.o.pos.z + 0.6, yaw: -60 } };
      ST.res = [[HOCK, CAMP, false], [ONEIL, CAMP, true], [ONEIL, HOCK, true]];
      placeBallLater = { free: true, p: V(SPOT.x + 0.9, 0.09, ZDOWN + 0.7) };
      const c = V(o.c.pos.x, 0.2, o.c.pos.z), a = lerp(0.2, 0.45, u); cp = V(c.x + Math.sin(a) * 2.6, lerp(5.6, 4.6, u), c.z + Math.cos(a) * 2.6); ct = c; fov = 34; break; }
    case 6: case 7: case 8: case 12: { // x-ray explainers: he stands in his pads, see-through; the neck, the cord, the signals
      xr = true; ST.c = { pose: STAND, pos: { x: SPOT.x, y: 0.95, z: ZDOWN, yaw: 90 } }; ST.h = null; ST.o = null; ball.visible = false;
      if (nb === 8) { const b = smooth(0.08, 0.45, u); ST.c.pose = addPose(STAND, { neck: [-34 * b, 0, 0], head: [-28 * b, 0, 0], spine2: [-10 * b, 0, 0] }); CORD.pinch = smooth(0.3, 0.55, u); }
      break; }
    case 9: { // the board: on his back, strapped down, a trainer holding his head still
      ST.c = { pose: SUPINE, pos: { x: SPOT.x + 0.6, y: 0.2, z: ZDOWN - 1.2, yaw: 180, tilt: 90 }, plant: false }; ST.h = null; ST.o = null; ball.visible = false; board.visible = true;
      ST.tr = true; const c = V(SPOT.x + 0.6, 0.35, ZDOWN - 1.95); cp = V(c.x + lerp(1.9, 1.5, u), lerp(1.05, 0.9, u), c.z + lerp(0.9, 0.6, u)); ct = c; fov = 34; break; }
    case 10: case 11: { // both teams take a knee; the cart takes him off the field toward the tunnel
      ball.visible = false; cart.visible = true; board.visible = true;
      const drive = nb === 10 ? smooth(0.55, 1.0, u) * 0.18 : 0.18 + 0.82 * smooth(0, 1, u);
      const cz = lerp(ZDOWN - 1.2, -GL - EZ - 4, drive), cx = lerp(SPOT.x + 0.6, -FW / 2 - 4, sm(drive));
      ST.cart = { x: cx, z: cz, yaw: Math.atan2(-(lerp(SPOT.x + 0.6, -FW / 2 - 4, sm(Math.min(1, drive + 0.02))) - cx), -1) / D2R };
      ST.c = { pose: SUPINE, onCart: true }; ST.h = { pose: KNEEL, pos: { x: SPOT.x + 1.0, y: 0.6, z: ZDOWN + 1.6, yaw: 165 } }; ST.o = { pose: KNEEL, pos: { x: SPOT.x - 0.35, y: 0.6, z: ZDOWN + 0.3, yaw: -165 } };
      if (nb === 10) { cp = V(SPOT.x + 0.3, lerp(1.3, 1.7, u), ZDOWN + 6.6 - 0.8 * u); ct = V(SPOT.x + 0.4, 0.7, ZDOWN - 0.4); fov = 38; hud.visible = u > 0.45; drawHud([['GAME STOPPED', '~10 MIN'], ['BOTH TEAMS', 'TOOK A KNEE', '#ffd23a']]); }
      else { cp = V(SPOT.x - 6, 4.5, ZDOWN + 8 - 4 * u); ct = V(cx, 0.8, cz); fov = 36; hud.visible = true; drawHud([['LEFT', 'ALERT, BREATHING', '#2fbf71'], ['FINAL', 'LIONS 19-15']]); }
      break; }
  }
  // pose everyone
  if (ST.play) stagePlay(ST.play, ST.tau, Math.round(t * FPS));
  else { place(CAMP, RG, ST.c && !ST.c.onCart ? ST.c : null); place(HOCK, RH, ST.h); place(ONEIL, RO, ST.o); if (ST.res) for (let k = 0; k < 3; k++) { resolve(ST.res, 16); for (const P of [CAMP, HOCK, ONEIL]) if (P.G.root.visible) ground(P, false); } }
  if (ST.cart) { cart.position.set(ST.cart.x, 0, ST.cart.z); cart.rotation.y = ST.cart.yaw * D2R; cart.updateMatrixWorld(true);
    board.position.copy(V(0, CARTDECK, 0.6).applyMatrix4(cart.matrixWorld)); board.rotation.y = cart.rotation.y; board.updateMatrixWorld(true);
    const bc = V(0, 0.24, 0.05).applyMatrix4(board.matrixWorld); CAMP.G.root.visible = true;
    RG.applyPose(SUPINE, { x: bc.x, y: bc.y, z: bc.z, yaw: cart.rotation.y / D2R + 180, tilt: 90 }); RG.untwist(); G.root.updateMatrixWorld(true); }
  if (ST.tr) { board.position.set(SPOT.x + 0.6, 0, ZDOWN - 1.2 + 0.05); board.rotation.y = 0; board.updateMatrixWorld(true);
    // the trainer kneels at his head, both hands flat on the sides of the helmet
    TR.root.visible = true; const hc = wp(CAMP.helmet); RT.applyPose(TR_KNEEL, { x: hc.x, y: 0.6, z: hc.z - 0.62, yaw: 180 }); TR.root.updateMatrixWorld(true);
    { const lo = lowestOfG(TR); TR.root.position.y += 0.002 - lo; TR.root.updateMatrixWorld(true); }
    const side = V(1, 0, 0), others = caps(CAMP);
    for (const [S, sg] of [['R', -1], ['L', 1]]) { const p = outside(CAMP, hc.clone(), side.clone().multiplyScalar(sg), 0.035), n = side.clone().multiplyScalar(-sg);
      if (!TRSEED[S]) { let b = null; for (const sd of [RT.LAST['arm' + S], ...CANDS]) { const r = armSolve(RT, S, { p, n, seed: sd, others }); if (!b || r.c < b.c) b = r; } TRSEED[S] = b.a; }
      armSolve(RT, S, { p, n, seed: TRSEED[S], others }); fingersAll(RT, S, 12); }
    RT.untwist(); TR.root.updateMatrixWorld(true); }
  if (board.visible && CAMP.G.root.visible) strapsOn(CAMP);
  if (ball.visible && !ST.play && placeBallLater) { ball.position.copy(placeBallLater.p); ball.quaternion.identity(); } placeBallLater = null;
  G.face({ blink: nb === 5 || nb === 9 || nb === 10 || nb === 11 ? 0.85 : 0 });
  // x-ray close-ups
  xray(xr);
  if (xr) { const N = placeSpine(); const neckP = wp(G.bones.neck);
    if (nb === 6) { cp = neckP.clone().add(V(lerp(0.75, 0.55, u), lerp(0.12, 0.08, u), lerp(0.55, 0.35, u))); ct = neckP.clone().add(V(0, 0.06, 0)); fov = 30; near = 0.02;
      hud.visible = true; drawHud([['NECK BONES', '7', '#ffffff'], ['INSIDE', 'SPINAL CORD', '#ffd23a']]); }
    else if (nb === 7 || nb === 12) { const hip = wp(G.bones.hips); cp = hip.clone().add(V(lerp(3.3, 2.9, u), 0.35, lerp(1.0, 0.7, u))); ct = hip.clone().add(V(0, 0.05, 0)); fov = 34; near = 0.03;
      const paths = nervePaths(N.curve);
      if (nb === 7) drawSignals(paths, lt, () => 1);
      else { drawSignals(paths, lt, (k) => k.startsWith('leg') || k === 'cord' ? 1 : 0.6); hud.visible = true; drawHud([['LOWER BODY', 'FULL MOVEMENT', '#2fbf71'], ['UPPER BODY', 'GETTING BETTER', '#ffd23a']]); } }
    else { cp = neckP.clone().add(V(0.72, 0.02, 0.32)); ct = neckP.clone().add(V(0, 0.02, 0.04)); fov = 32; near = 0.02;
      const paths = nervePaths(N.curve); const pinch = CORD.pinch;
      drawSignals(paths, lt, (k, uu) => k === 'cord' ? (uu < CORD.k * 0.9 ? 1 : 1 - pinch) : 1 - pinch);
      hud.visible = u > 0.3; drawHud([['NECK', 'BENT TOO FAR', '#ff6a5c'], ['SIGNALS', pinch > 0.6 ? 'BLOCKED' : 'SQUEEZED', '#ff6a5c']]); }
    HOCK.G.root.visible = ONEIL.G.root.visible = false; }
  if (CAMQ) { const [w, bn, d, f] = CAMQ.split(':'), P = { C: CAMP, H: HOCK, O: ONEIL }[w], bp = wp(P.G.bones[bn]), dd = d.split(',').map(Number);
    ct = bp; cp = bp.clone().add(V(dd[0], dd[1], dd[2])); fov = +f || 30; near = 0.01; roll = 0; }
  camera.position.copy(cp); camera.up.set(Math.sin(roll * D2R), Math.cos(roll * D2R), 0); camera.lookAt(ct); camera.fov = fov; camera.near = near; camera.updateProjectionMatrix();
  return { b: nb, focus: ct }; }
let placeBallLater = null; const TRSEED = {};
const TR_KNEEL = curl(curl({ spine1: [-28, 0, 0], spine2: [-14, 0, 0], chest: [-8, 0, 0], neck: [20, 0, 0], head: [16, 0, 0], thighR: [80, 0, 8], shinR: [-95, 0, 0], footR: [0, 0, 0], thighL: [-4, 0, -6], shinL: [-100, 0, 0], footL: [-30, 0, 0] }, 'R', 12), 'L', 12);
// trainer: lowest point from his bones (he has no kit capsules)
function lowestOfG(Gx) { let lo = 1e9; for (const n of ['shinR', 'shinL', 'footR', 'footL', 'hips']) lo = Math.min(lo, wp(Gx.bones[n]).y - 0.06); return lo; } const CAMQ = Q.get('cam');
// ------------------------------------------------------------------ look + frame I/O
import { makeLook } from '/look.js';
const LOOK = makeLook(THREE, renderer, scene, camera, W, H, { overlays: [hud], aperture: 0.0008, maxblur: 0.006, rim: 1.6 });
let FOC = V(0, 1, 0), XRNOW = false;
function update(t) { t = clamp(t, 0, TOTAL - 1e-3); const r = shot(t); fitHud(); XRNOW = XRON; renderer.toneMappingExposure = XRON ? 0.42 : 1.05;   // the room goes dim behind the x-ray so the glow and the signals read
  const at = cart.visible ? cart.position.clone() : wp(G.bones.hips);
  sun.position.copy(at).add(V(8, 40, 14)); sun.target.position.copy(at); sun.target.updateMatrixWorld(); FOC = r.focus; return r; }
function stepTo(i) { return update(i / FPS); }
const draw = () => LOOK.render(FOC, { ao: !XRNOW, dof: !XRNOW });
const gl = renderer.getContext(), px = new Uint8Array(W * H * 4);
window.renderAll = async (f0, f1) => { for (let i = f0; i < f1; i++) { stepTo(i); draw(); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); await fetch('/frame', { method: 'POST', body: px }); } return 'ok'; };
window.renderAtT = t => { stepTo(Math.round(t * FPS)); draw(); return renderer.domElement.toDataURL('image/png'); };
// rig report for jointjerk: Campbell's joints, and any body point under the turf
window.rigReport = i => { const r = stepTo(i); const ang = {}; for (const [k, v] of Object.entries(RG.LAST)) if (Array.isArray(v)) ang[k] = v;
  const clip = []; for (const [nm, P] of [['C', CAMP], ['H', HOCK], ['O', ONEIL]]) if (P.G.root.visible) { const lo = lowest(P); if (lo < -0.01) clip.push(nm + ' under turf ' + lo.toFixed(3)); }
  return { b: r.b, ang, clip }; };
window.dbg = { THREE, scene, camera, G, RG, RH, RO, PLAYERS, shot, play, SIG, sigP, NERVES, stagePlayRaw, clipList, getTAB: () => TAB, TAU0, DTAU, place, draw, caps, segDist, contactPts, armSolve, ownHelmet, CAMP, HOCK, ONEIL, C_HIT, O_HIT, H_HIT, STAND, V, wp,
  report: i => { const st = stepTo(i); const r = x => x == null ? null : +x.toFixed(1), v = p => p.toArray().map(x => +x.toFixed(3));
    return { costs: { cL: r(RG.LAST.costL), cR: r(RG.LAST.costR), oL: r(RO.LAST.costL), oR: r(RO.LAST.costR), hR: r(RH.LAST.costR) }, clip: clipList(PLAYERS), cHelmet: v(wp(CAMP.helmet)), hWaist: v(wp(HOCK.G.bones.spine1)), cHips: v(wp(G.bones.hips)), cArmL: RG.LAST.armL, cArmR: RG.LAST.armR, miss: Object.fromEntries(Object.entries(LASTT).flatMap(([w, l]) => l.map(h => [w + h.S, +((w === 'c' ? RG : RO).palmW(h.S).distanceTo(h.p) * 100).toFixed(1)]))), shC: v(wp(G.bones.uarmR)), tgt: v(LASTT.c[1].p) }; } };
makeSeeds(); if (Q.get("table") === "1") buildTable();
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS); window.READY = true;
window.SCN = { THREE, scene, camera, stepTo, renderer, FPS, B, DUR, TOTAL };
