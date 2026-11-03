// Goliath (Six Flags Over Georgia), Oct 12, 2026: a rider ejected; how airtime and a lap bar work. Generic coaster, no park branding, no gore.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { loadGuy } from '/guy3d.js';

const Q = new URLSearchParams(location.search);
const W = +Q.get('w') || 720, H = +Q.get('h') || 1280;
const FPS = 30;
const TIMES = await (await fetch('/coaster/times.json')).json();
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
// ================================================================== A ROLLER COASTER AND ITS LAP BARS
// ------------------------------------------------------------------ set: a generic steel hypercoaster in a park, afternoon (no park branding)
home.visible = false; lamp.visible = false;
scene.background = new THREE.Color(0x9cc7ef); scene.fog = new THREE.Fog(0xb9d4ea, 160, 900); scene.environmentIntensity = 0.5;
hemi.color.set(0xd6e8ff); hemi.groundColor.set(0x5a6b3a); hemi.intensity = 0.95; sun.color.set(0xffefd6); sun.intensity = 3.0;
{ const S = sun.shadow.camera; S.left = -10; S.right = 10; S.top = 10; S.bottom = -10; S.near = 1; S.far = 200; S.updateProjectionMatrix(); }
// sky dome with a soft gradient
{ const sk = new THREE.Mesh(new THREE.SphereGeometry(1500, 32, 16), new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false, fog: false, uniforms: { uSet: { value: 0 } },
    vertexShader: 'varying vec3 d; void main(){ d = normalize(position); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }',
    fragmentShader: `uniform float uSet; varying vec3 d; void main(){ float h = clamp(d.y, 0., 1.); vec3 day = mix(vec3(.75,.86,.96), vec3(.32,.56,.88), pow(h, .6)); vec3 dusk = mix(vec3(1.,.62,.38), vec3(.25,.22,.42), pow(h, .5));
      gl_FragColor = vec4(mix(day, dusk, uSet), 1.);
      #include <colorspace_fragment>
    }` })); sk.renderOrder = -10; scene.add(sk); window.__SKY = sk; }
const SKYU = window.__SKY.material.uniforms;
const groundM = new THREE.MeshStandardMaterial({ map: canvasTex(1024, 1024, g => { g.fillStyle = '#5f8a3e'; g.fillRect(0, 0, 1024, 1024); for (let i = 0; i < 20000; i++) { g.fillStyle = `rgba(${40 + 40 * Math.random()},${90 + 60 * Math.random()},${30 + 30 * Math.random()},0.35)`; g.fillRect(Math.random() * 1024, Math.random() * 1024, 2, 3); } }), roughness: 1 });
groundM.map.wrapS = groundM.map.wrapT = THREE.RepeatWrapping; groundM.map.repeat.set(60, 60);
const ground = new THREE.Mesh(new THREE.PlaneGeometry(3000, 3000).rotateX(-Math.PI / 2), groundM); ground.receiveShadow = true; scene.add(ground);
for (let i = 0; i < 140; i++) { const x = (hash1(i * 1.3) - 0.5) * 700, z = -300 + (hash1(i * 2.7) - 0.5) * 700; if (x > -320 && x < 20 && z > -70 && z < 115) continue;
  const tr = new THREE.Group(); tr.position.set(x, 0, z); scene.add(tr); const h = 6 + 8 * hash1(i * 5);
  const tk = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.4, h * 0.4, 8), mat(0x5b4030, 0.9)); tk.position.y = h * 0.2; tr.add(tk);
  const cr = new THREE.Mesh(new THREE.SphereGeometry(h * 0.32, 12, 10), mat(new THREE.Color().setHSL(0.27 + 0.05 * hash1(i), 0.45, 0.25 + 0.1 * hash1(i * 3)), 0.9)); cr.position.y = h * 0.62; cr.scale.y = 1.2; tr.add(cr); }
// the layout, after the real ride (B&M hyper, 2006): 200 ft lift, 170 ft first drop, camelback + 175 ft drop, banked turnaround, camelback,
// 540-degree helix, camelback, horseshoe, three small hills, banked turn back to the station (metres; out of the station heading -z)
const LAYOUT = [[0, 2.2, 30], [0, 2.2, 0], [0, 2.2, -25], [-8, 2.6, -40], [-22, 4, -46], [-35, 9, -46], [-80, 35, -46], [-125, 59, -46], [-136, 61.5, -46], [-145, 59, -46], [-158, 40, -46], [-168, 16, -46], [-178, 6, -46], [-192, 22, -46], [-205, 44, -46], [-215, 55.5, -46], [-223, 55.5, -46], [-233, 44, -46], [-246, 22, -46], [-258, 4, -46], [-280, 7, -40], [-296, 11, -22], [-294, 13, 0], [-276, 15, 12], [-258, 26, 12], [-243, 41, 12], [-233, 42.5, 12], [-223, 41, 12], [-208, 24, 12], [-192, 5, 12], [-176, 12, 13], [-150, 21, 14], [-142.35, 20.42, 15.52], [-135.86, 19.83, 19.86], [-131.52, 19.25, 26.35], [-130, 18.67, 34], [-131.52, 18.08, 41.65], [-135.86, 17.5, 48.14], [-142.35, 16.92, 52.48], [-150, 16.33, 54], [-157.65, 15.75, 52.48], [-164.14, 15.17, 48.14], [-168.48, 14.58, 41.65], [-170, 14, 34], [-168.48, 13.42, 26.35], [-164.14, 12.83, 19.86], [-157.65, 12.25, 15.52], [-150, 11.67, 14], [-142.35, 11.08, 15.52], [-135.86, 10.5, 19.86], [-131.52, 9.92, 26.35], [-130, 9.33, 34], [-131.52, 8.75, 41.65], [-135.86, 8.17, 48.14], [-142.35, 7.58, 52.48], [-150, 7, 54], [-172, 7, 54], [-182, 20, 54], [-192, 36, 54], [-200, 37.5, 54], [-208, 36, 54], [-218, 20, 54], [-232, 5, 54], [-250, 6, 60], [-260, 8, 76], [-252, 9, 92], [-234, 8, 96], [-222, 18, 96], [-212, 25.5, 96], [-202, 18, 96], [-190, 6, 96], [-178, 15, 96], [-168, 19.5, 96], [-158, 15, 96], [-146, 6, 96], [-134, 13, 96], [-124, 16.5, 96], [-114, 13, 96], [-100, 6, 96], [-70, 6, 96], [-40, 7, 92], [-18, 6, 82], [-5, 3.5, 68], [0, 2.4, 50], [0, 2.2, 40]].map(p => V(...p));
const CURVE = new THREE.CatmullRomCurve3(LAYOUT, false, 'centripetal', 0.5); const LEN = CURVE.getLength();
const frameAt = s => { const u = clamp(s / LEN, 0, 1), p = CURVE.getPointAt(u), t = CURVE.getTangentAt(u).normalize(); const r = new THREE.Vector3().crossVectors(t, V(0, 1, 0)).normalize(); const up = new THREE.Vector3().crossVectors(r, t).normalize(); return { p, t, r, up }; };
const sNear = (x, y, z) => { let best = 0, bd = 1e9; const q = V(x, y, z); for (let s = 0; s < LEN; s += 0.5) { const d = frameAt(s).p.distanceToSquared(q); if (d < bd) { bd = d; best = s; } } return best; };
// rails (two running rails), the box spine under them, ties; turquoise track on grey supports (2025 repaint)
const trackM = mat(0x2fb7b0, 0.45, 0.35), supM = mat(0x9ea3a8, 0.6, 0.3);
{ const N = 1400, L = [], Rr = [], Sp = []; for (let i = 0; i <= N; i++) { const f = frameAt(LEN * i / N); L.push(f.p.clone().addScaledVector(f.r, -0.62)); Rr.push(f.p.clone().addScaledVector(f.r, 0.62)); Sp.push(f.p.clone().addScaledVector(f.up, -0.55)); }
  for (const [pts, r] of [[L, 0.08], [Rr, 0.08], [Sp, 0.32]]) { const m = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), N, r, 10), trackM); m.castShadow = m.receiveShadow = true; scene.add(m); }
  for (let s = 0; s < LEN; s += 1.6) { const f = frameAt(s), tie = new THREE.Mesh(new THREE.BoxGeometry(1.35, 0.1, 0.12), trackM); tie.position.copy(f.p).addScaledVector(f.up, -0.2); tie.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(f.r, f.up, f.t.clone().negate())); scene.add(tie);
    const web = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.4, 0.08), trackM); web.position.copy(f.p).addScaledVector(f.up, -0.4); web.quaternion.copy(tie.quaternion); scene.add(web); }
  for (let s = 40; s < LEN - 4; s += 9) { const f = frameAt(s); if (f.p.y < 3) continue; const top = f.p.clone().addScaledVector(f.up, -0.85), h = top.y;
    const col = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.42, h, 12), supM); col.position.set(top.x, h / 2, top.z); col.castShadow = true; scene.add(col);
    if (h > 18) { const rh = V(f.r.x, 0, f.r.z).normalize(); for (const sd of [-1, 1]) {   // splayed legs out to the sides of the track (never along it)
      const base = top.clone().addScaledVector(rh, sd * h * 0.24).setY(0), dir = top.clone().sub(base), len = dir.length();
      const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.3, len, 10), supM); leg.position.copy(base).addScaledVector(dir, 0.5); leg.quaternion.setFromUnitVectors(V(0, 1, 0), dir.normalize()); leg.castShadow = true; scene.add(leg); } } } }
// the station: platform, roof, gate, check lights
const station = new THREE.Group(); scene.add(station);
{ box(3.2, 1.2, 26, -2.9, 0.6, 0, mat(0x8d8f93, 0.8), 0, station); box(3.2, 1.2, 26, 2.9, 0.6, 0, mat(0x8d8f93, 0.8), 0, station);
  box(10, 0.25, 28, 0, 6.5, 0, mat(0x2f4a6a, 0.6), 0, station); for (const [x, z] of [[-4.4, -13], [4.4, -13], [-4.4, 13], [4.4, 13]]) box(0.3, 6.4, 0.3, x, 3.2, z, mat(0xdedede, 0.5), 0, station);
  for (let i = 0; i < 9; i++) box(0.05, 0.9, 0.05, -1.45, 1.65, -9 + i * 2.1, mat(0x9aa0a6, 0.4, 0.6), 0, station); }
const lights = []; for (const x of [-1.5, 1.5]) { const l = new THREE.Mesh(new THREE.SphereGeometry(0.09, 16, 10), new THREE.MeshBasicMaterial({ color: 0x1c3a1c, toneMapped: false })); l.position.set(x * 2.4, 2.4, -11); station.add(l); lights.push(l); }
const closedSign = new THREE.Mesh(new THREE.PlaneGeometry(2.2, 0.8), new THREE.MeshBasicMaterial({ map: canvasTex(512, 180, g => { g.fillStyle = '#b3141a'; g.fillRect(0, 0, 512, 180); g.fillStyle = '#fff'; g.font = 'bold 120px Arial'; g.fillText('CLOSED', 40, 135); }), toneMapped: false }));
closedSign.position.set(-3.6, 1.9, 13.4); closedSign.visible = false; station.add(closedSign);
const tape = new THREE.Mesh(new THREE.BoxGeometry(14, 0.06, 0.02), new THREE.MeshBasicMaterial({ color: 0xf2c21a, toneMapped: false })); tape.visible = false; scene.add(tape);
// the train: 9 cars x 4 seats (36), floorless, padded clamshell lap bars; riders: two MakeHuman men in the front car, simple figures elsewhere
const CARL = 2.15, cars = [], bars = [], belts = [];
const seatM = mat(0x17707a, 0.6), carM = mat(0xe8702a, 0.45, 0.3), padM = mat(0x1a8790, 0.65), metM = mat(0xb7bcc3, 0.35, 0.8);   // orange and teal trains, teal seats and restraints
for (let c = 0; c < 9; c++) { const car = new THREE.Group(); scene.add(car); cars.push(car);
  box(4.2, 0.35, 1.7, 0, 0.3, 0, carM, 0.08, car); car.userData.wallL = box(0.12, 0.3, 1.6, -2.05, 0.55, 0, carM, 0.04, car); box(0.12, 0.3, 1.6, 2.05, 0.55, 0, carM, 0.04, car);   // open-sided cars, low fenders
  for (const x of [-1.2, 1.2]) for (const z of [-0.65, 0.65]) { const w = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.16, 0.12, 14).rotateZ(Math.PI / 2), metM); w.position.set(x * 0.5, -0.05, z); car.add(w); }
  const cb = []; for (let k = 0; k < 4; k++) { const x = -1.5 + k; box(0.82, 0.12, 0.62, x, 0.88, 0.12, seatM, 0.05, car); box(0.3, 0.4, 0.4, x, 0.64, 0.15, carM, 0.04, car); box(0.82, 1.05, 0.14, x, 1.43, 0.46, seatM, 0.06, car); box(0.82, 0.32, 0.2, x, 2.08, 0.45, seatM, 0.08, car);   // seat top at 0.94
    // the clamshell lap bar: hinged at the front of the seat, a padded block that comes down over the thighs
    // B&M-style lap bar: the post rises from the floor between the rider's shins and swings back; the pad (kept level) lands on the thighs
    const hinge = new THREE.Group(); hinge.position.set(x, 0.5, -0.55); car.add(hinge);
    box(0.08, 0.743, 0.07, 0, 0.371, 0, padM, 0.02, hinge); const tip = new THREE.Group(); tip.position.set(0, 0.743, 0); hinge.add(tip);
    const pad = box(0.62, 0.13, 0.34, 0, 0.0, 0.14, padM, 0.06, tip); pad.rotation.x = -0.1; pad.castShadow = true; hinge.userData.tip = tip;
    hinge.rotation.x = -0.35; cb.push(hinge);
    const belt = new THREE.Group(); belt.position.set(x, 0.0, 0.0); car.add(belt); box(0.05, 0.16, 0.025, 0, 1.03, -0.02, mat(0x222222, 0.6), 0.005, belt); box(0.08, 0.06, 0.04, 0, 1.08, -0.04, metM, 0.01, belt); belt.visible = false; belts.push(belt);
    if (c > 0 || k === 0 || k === 3) { const fig = new THREE.Group(); fig.position.set(x, 0.95, 0.15); car.add(fig); if (c === 0 && k === 0) car.userData.fig0 = fig; const col = new THREE.Color().setHSL(hash1(c * 7 + k), 0.55, 0.45);
      const torso = new THREE.Mesh(new THREE.CapsuleGeometry(0.17, 0.42, 6, 12), mat(col, 0.8)); torso.position.set(0, 0.48, 0.12); fig.add(torso);
      const head = new THREE.Mesh(new THREE.SphereGeometry(0.11, 16, 12), mat(new THREE.Color().setHSL(0.07, 0.4, 0.3 + 0.35 * hash1(c + k * 3)), 0.6)); head.position.set(0, 0.98, 0.1); fig.add(head);
      const legs = new THREE.Mesh(new THREE.CapsuleGeometry(0.11, 0.42, 6, 10), mat(0x2b3a55, 0.8)); legs.rotation.x = Math.PI / 2; legs.position.set(0, 0.12, -0.2); fig.add(legs); } }
  bars.push(cb); }
// the two MakeHuman riders (front car, seats 2 and 3); K's shirt colour changes when he is the ride worker (station beat)
const K = await loadGuy(THREE, '/char/' + (Q.get('char') || window.CHARDEF || 'guy'), { fingers3: !!window.FINGERS3 }); scene.add(K.root); K.root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
const RK = makeRig(K, 'rider2');
function shirt(Gx, c) { const m = Gx.meshes.shirt; if (!m) return; if (!m.userData.own) { m.material = m.material.clone(); m.material.map = null; m.userData.own = true; } m.material.color.set(c); }
shirt(G, 0x2f6fd0); shirt(K, 0x3a3f46);
// x-ray: the near rider goes glassy so the gap between him and the seat, and the bar on his thighs, show
const XRAYM = new THREE.MeshBasicMaterial({ color: 0x7fd3ff, transparent: true, opacity: 0.18, depthWrite: false, side: THREE.DoubleSide, blending: THREE.AdditiveBlending });
const XRSAVE = new Map(); let XRON = false;
function xray(on) { if (XRON === on) return; XRON = on; G.root.traverse(o => { if (!o.isMesh) return; if (on) { XRSAVE.set(o, o.material); o.material = XRAYM; o.castShadow = false; } else { o.material = XRSAVE.get(o) || o.material; o.castShadow = true; } }); }
// arrows (body floats up / seat drops away / the bar holds down) and a contact glow where the bar meets the thighs
function arrowMesh(color) { const s = new THREE.Shape(); s.moveTo(-0.05, -0.32); s.lineTo(0.05, -0.32); s.lineTo(0.05, 0.08); s.lineTo(0.13, 0.08); s.lineTo(0, 0.25); s.lineTo(-0.13, 0.08); s.lineTo(-0.05, 0.08); s.closePath();
  return new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth: 0.04, bevelEnabled: false }), new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.92, depthTest: false, toneMapped: false })); }
const upArrow = arrowMesh(0x3ad27a), downArrow = arrowMesh(0xffb020), barArrow = arrowMesh(0xff4a3a); for (const a of [upArrow, downArrow, barArrow]) { a.renderOrder = 25; a.visible = false; scene.add(a); }
const glow = new THREE.Sprite(new THREE.SpriteMaterial({ map: canvasTex(128, 128, g => { const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64); gr.addColorStop(0, 'rgba(255,90,60,1)'); gr.addColorStop(1, 'rgba(255,0,0,0)'); g.fillStyle = gr; g.fillRect(0, 0, 128, 128); }), transparent: true, depthTest: false, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false }));
glow.scale.set(0.5, 0.5, 1); glow.renderOrder = 24; glow.visible = false; scene.add(glow);
// the locking ratchet on the front car's seat 2 hinge (shown in the close-up): a toothed wheel and a pawl
const ratchet = new THREE.Group(); { const sh = new THREE.Shape(); const n = 14; for (let i = 0; i < n * 2; i++) { const a = i / (n * 2) * Math.PI * 2, r = i % 2 ? 0.07 : 0.095; i ? sh.lineTo(Math.cos(a) * r, Math.sin(a) * r) : sh.moveTo(Math.cos(a) * r, Math.sin(a) * r); } sh.closePath();
  const wheel = new THREE.Mesh(new THREE.ExtrudeGeometry(sh, { depth: 0.03, bevelEnabled: false }).rotateY(Math.PI / 2), mat(0xd9a52b, 0.35, 0.8)); ratchet.add(wheel);
  const pawl = new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.03, 0.16), mat(0xc0c5cc, 0.3, 0.85)); pawl.position.set(0.0, 0.11, -0.06); pawl.rotation.x = 0.5; ratchet.add(pawl); ratchet.userData.wheel = wheel; ratchet.userData.pawl = pawl; }
ratchet.position.set(-0.5 - 0.08, 0.5, -0.55); ratchet.visible = false;
// readout
const hudC = document.createElement('canvas'); hudC.width = 520; hudC.height = 440; const hudT = new THREE.CanvasTexture(hudC); hudT.colorSpace = THREE.SRGBColorSpace;
const hud = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: hudT, transparent: true, depthTest: false, depthWrite: false, toneMapped: false })); hud.renderOrder = 30; camera.add(hud); scene.add(camera); hud.visible = false;
function drawHud(rows, flag, fcol = '#d9241b') { const g = hudC.getContext('2d'); g.clearRect(0, 0, 520, 440); g.beginPath(); g.roundRect(6, 6, 508, 428, 34); g.fillStyle = 'rgba(8,14,22,0.74)'; g.fill(); g.lineWidth = 4; g.strokeStyle = 'rgba(160,200,235,0.55)'; g.stroke();
  let y = 30; for (const [lab, val, col] of rows) { g.fillStyle = '#9fb6c8'; g.font = '600 34px Arial, Helvetica, sans-serif'; g.fillText(lab, 34, y + 38); g.fillStyle = col || '#fff'; g.font = 'bold 62px Arial, Helvetica, sans-serif'; g.fillText(val, 34, y + 102, 452); y += 120; }
  if (flag) { g.font = 'bold 52px Arial, Helvetica, sans-serif'; const fw = Math.min(460, g.measureText(flag).width + 40); g.beginPath(); g.roundRect(30, 340, fw, 76, 16); g.fillStyle = fcol; g.fill(); g.fillStyle = '#fff'; g.fillText(flag, 50, 397, fw - 40); }
  hudT.needsUpdate = true; }
function fitHud() { const d = camera.near * 1.6, h = 2 * d * Math.tan(camera.fov * D2R / 2), w = h * camera.aspect, gw = 0.4 * w, gh = gw * 440 / 520; hud.scale.set(gw, gh, 1); hud.position.set(w / 2 - gw / 2 - 0.035 * w, h / 2 - 0.165 * h - gh / 2, -d); }
cars[0].add(ratchet);
// ------------------------------------------------------------------ story: one shot per line
const CREST = sNear(-136, 61.5, -46), LIFT0 = sNear(-30, 7, -46), HILL1 = sNear(-219, 55.5, -46), STATION = sNear(0, 2.2, -4);
const HMAX = 62.5, vAt = s => s < CREST ? 2.4 : Math.max(3, 0.94 * Math.sqrt(2 * 9.81 * Math.max(0, HMAX - frameAt(s).p.y)));
function runFrom(s0, dt) { let s = s0; for (let k = 0; k < dt * 60; k++) s += vAt(s) / 60; return s; }   // the train's head moving along the track for dt seconds
const SEATX = [-1.5, -0.5, 0.5, 1.5];
const LOCK = 0.416, OPEN = -0.35;
// the riders' sitting pose (from the sled Short), hands resting on the lap bar
const SITR = curl(curl({ thighR: [84, 0, 6], thighL: [84, 0, -6], shinR: [-70, 0, 0], shinL: [-70, 0, 0], footR: [-4, 0, 0], footL: [-4, 0, 0], spine1: [2, 0, 0], neck: [0, 0, 0], armR: A(42, 20, 0, 70), armL: A(42, 20, 0, 70) }, 'R', 55), 'L', 55);
const HANDSUP = curl(curl({ ...SITR, armR: A(150, 25, 0, 20), armL: A(150, 25, 0, 20), neck: [-10, 0, 0] }, 'R', 10), 'L', 10);
const TUG = curl(curl({ ...SITR, spine1: [-6, 0, 0], armR: A(30, 15, 0, 95), armL: A(30, 15, 0, 95), neck: [12, 0, 0] }, 'R', 80), 'L', 80);
const WORKER = curl(curl({ ...STAND, spine1: [-14, 0, 0], armR: A(70, 10, 0, 30), armL: A(10, 8, 0, 18) }, 'R', 30), 'L', 30);
let CARF = [];
function placeTrain(sHead, barAng = LOCK) { CARF = [];
  cars.forEach((car, c) => { const f = frameAt(sHead - c * CARL); car.position.copy(f.p).addScaledVector(f.up, 0.15); car.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(f.r, f.up, f.t.clone().negate())); car.updateMatrixWorld(true); CARF.push(f);
    bars[c].forEach(h => { h.rotation.x = barAng; h.userData.tip.rotation.x = -barAng; }); }); }
function seatRoot(c, k, lift = 0) { const car = cars[c], f = CARF[c], p = car.localToWorld(V(SEATX[k], 1.05 + lift, 0.2)); const yaw = Math.atan2(-f.t.x, -f.t.z) / D2R, tilt = Math.asin(clamp(f.t.y, -1, 1)) / D2R; return { x: p.x, y: p.y, z: p.z, yaw, tilt }; }
function onboard(c, lp, lt_) { const car = cars[c]; return [car.localToWorld(lp.clone()), car.localToWorld(lt_.clone())]; }
function shot(t) { const nb = beatAt(t), lt = t - B[nb], dur = DUR[nb], u = lt / dur;
  hud.visible = false; for (const a of [upArrow, downArrow, barArrow]) a.visible = false; glow.visible = false; ratchet.visible = false; closedSign.visible = false; tape.visible = false; belts.forEach(b => { b.visible = false; });
  lights.forEach(l => l.material.color.set(0x1c3a1c)); cars[0].userData.wallL.visible = true; cars[0].userData.fig0.visible = true; bars[0][0].visible = true; const ARR = []; SKYU.uSet.value = 0; scene.background.set(0x9cc7ef); scene.fog.color.set(0xb9d4ea); sun.intensity = 3.0; sun.color.set(0xffefd6); hemi.intensity = 0.95; xray(false); shirt(K, 0x3a3f46);
  let pov = 0, sH = STATION, bar = LOCK, gpose = SITR, kpose = SITR, glift = 0, kroot = null, cp, ct, up = V(0, 1, 0), fov = 40, near = 0.05;
  switch (nb) {
    case 0: { // hook: on board, facing the riders, over an airtime hill at speed (frame one already moving)
      sH = runFrom(HILL1 - 22, lt * 0.8); placeTrain(sH); const air = smooth(-14, -2, sH - HILL1) * (1 - smooth(4, 16, sH - HILL1)); glift = 0.05 * air; gpose = mixPose(SITR, HANDSUP, 0.4 * air);
      [cp, ct] = onboard(0, V(0, 2.05, -2.4), V(0, 1.4, 0.8)); up = V(0, 1, 0).applyQuaternion(cars[0].quaternion); fov = 52;
      hud.visible = true; drawHud([['SPEED', Math.round(vAt(sH) * 2.237) + ' MPH', '#ffd23a']]); break; }
    case 1: { // the ride: climbing the lift hill, seen from the ground
      sH = LIFT0 + 20 + lt * 2.4; placeTrain(sH); const f = frameAt(sH - 9); ct = f.p.clone(); cp = ct.clone().addScaledVector(f.r, 36).addScaledVector(f.t, 6 - 6 * u).add(V(0, -7, 0)); fov = 44;
      hud.visible = true; drawHud([['OCT 12, 2026', 'GOLIATH'], ['HEIGHT', '200 FT']]); break; }
    case 2: { // over the top and down the first drop
      // first person: his view from the front car over the top of the lift and down the first drop
      sH = runFrom(CREST - 2.5, lt); placeTrain(sH); const f = frameAt(sH); pov = 27; cp = V(0, 0, 0); ct = V(0, 0, -1);
      hud.visible = true; drawHud([['HEIGHT', Math.max(0, Math.round(f.p.y * 3.28)) + ' FT'], ['SPEED', Math.round(vAt(sH) * 2.237) + ' MPH', '#ffd23a']]); break; }
    case 3: { // what happened: the ride stopped, tape across the foreground (no one shown hurt)
      sH = STATION; placeTrain(sH); cp = V(-150 + 1.5 * u, 1.6, -16); ct = V(-188, 13, -48); fov = 46;
      { const d = ct.clone().sub(cp).setY(0).normalize(); tape.visible = true; tape.position.copy(cp).addScaledVector(d, 6).setY(1.0); tape.rotation.y = Math.atan2(-d.x, -d.z) + Math.PI / 2; }
      hud.visible = true; drawHud([['4 KIDS', 'HURT', '#ffd23a'], ['THE RIDER', 'DIED', '#ff6a5c']]); break; }
    case 4: case 5: case 6: { // x-ray: sitting normally (4), then airtime over a hill (5, 6): he floats, the seat drops away, the bar holds him
      if (nb === 5) { // first person again: floating over a camelback hill, the lap bar on his thighs
        sH = runFrom(HILL1 - 42, lt * 0.85); placeTrain(sH); const air = smooth(-12, -2, sH - HILL1) * (1 - smooth(6, 16, sH - HILL1)); glift = 0.05 * air; gpose = mixPose(SITR, HANDSUP, 0.5 * air); pov = 30;
        cp = V(0, 0, 0); ct = V(0, 0, -1); hud.visible = true; drawHud([['AIRTIME', air > 0.4 ? 'YOU FLOAT' : 'OVER THE HILL', '#ffd23a'], ['SPEED', Math.round(vAt(sH) * 2.237) + ' MPH']]); break; }
      const air = nb === 4 ? 0 : 1; sH = nb === 4 ? STATION : HILL1 - 1 + 2 * u; placeTrain(sH); xray(true); glift = 0.055 * air;
      cars[0].userData.wallL.visible = false; cars[0].userData.fig0.visible = false; bars[0][0].visible = false; [cp, ct] = onboard(0, V(-4.6, 2.0, 0.3), V(-0.5, 1.32, 0.3)); up = V(0, 1, 0).applyQuaternion(cars[0].quaternion); fov = 31;
      if (air > 0.05) { const car = cars[0]; ARR.push([upArrow, car.localToWorld(V(-1.0, 1.55 + 0.1 * air, 0.12)), 1.0 * air, false], [downArrow, car.localToWorld(V(-1.0, 0.75 - 0.08 * air, 0.25)), 0.9 * air, true]); }
      if (nb === 6) { glow.visible = true; glow.position.copy(cars[0].localToWorld(V(-0.5, 1.15, -0.1))); glow.material.opacity = 0.6 + 0.3 * Math.sin(t * 6); ARR.push([barArrow, cars[0].localToWorld(V(-1.0, 1.6, -0.1)), 0.9, true]); }
      hud.visible = true; drawHud(nb === 4 ? [['YOUR WEIGHT', 'ON THE SEAT', '#2fbf71']] : [['PUSHING YOU DOWN', 'NOTHING', '#ff6a5c'], ['HOLDING YOU IN', 'THE LAP BAR', '#2fbf71']]); break; }
    case 7: { // the lap bar, locked over the thighs (close-up)
      sH = STATION; placeTrain(sH, lerp(OPEN, LOCK, sm(clamp(u * 2, 0, 1)))); [cp, ct] = onboard(0, V(-1.9, 1.9, -1.1), V(-0.5, 1.2, -0.1)); fov = 34;
      if (u > 0.45) ARR.push([barArrow, cars[0].localToWorld(V(-0.5, 1.5, -0.1)), 0.9, true]);
      hud.visible = true; drawHud([['LAP BAR', u < 0.5 ? 'CLOSING' : 'LOCKED', u < 0.5 ? '#ffd23a' : '#2fbf71']]); break; }
    case 8: { // the station check: the lights say every bar is locked, the worker pulls on each bar
      sH = STATION; placeTrain(sH); lights.forEach(l => l.material.color.set(u > 0.15 ? 0x37ff6a : 0x1c3a1c)); shirt(K, 0xf2b81c);
      const car = cars[0]; const wp_ = car.localToWorld(V(-1.95, 0.0, -0.75)); kroot = { x: wp_.x - 0.35, y: 0.95 + 1.2, z: wp_.z, yaw: -90 }; kpose = mixPose(WORKER, mixPose(WORKER, STAND, 0.5), 0.5 + 0.5 * Math.sin(lt * 3));
      cp = V(-6.5, 2.6, -11 + 2 * u); ct = car.localToWorld(V(-1.0, 1.3, 0)); fov = 36;
      hud.visible = true; drawHud([['LIGHTS', u > 0.15 ? 'ALL LOCKED' : 'CHECKING', u > 0.15 ? '#2fbf71' : '#ffd23a']], u > 0.45 ? 'HAND CHECK' : null, '#2f7d4a'); break; }
    case 9: { // the investigation: a part, a check, or both (the lock's ratchet close-up)
      sH = STATION; placeTrain(sH); ratchet.visible = true; ratchet.userData.wheel.rotation.x = 0.12 * Math.sin(lt * 2); [cp, ct] = onboard(0, V(-1.55, 0.85, -1.25), V(-0.58, 0.55, -0.55)); fov = 32; near = 0.02;
      hud.visible = true; drawHud([['A PART', 'FAILED?', '#ffd23a'], ['A CHECK', 'MISSED?', '#ffd23a']]); break; }
    case 10: { // no cause yet; the ride is closed
      sH = STATION; placeTrain(sH, OPEN); closedSign.visible = true; cp = V(-1, 2.0, 22); ct = V(-3.6, 1.8, 13.4); fov = 38;
      hud.visible = true; drawHud([['CAUSE', 'NOT FOUND YET', '#ffd23a'], ['THE RIDE', 'CLOSED', '#ff6a5c']]); break; }
    case 11: { // seat belts being added
      sH = STATION; placeTrain(sH); belts.forEach(b => { b.visible = true; }); [cp, ct] = onboard(0, V(-1.5, 2.0, -1.4), V(-0.5, 1.1, 0.0)); fov = 34;
      hud.visible = true; drawHud([['ADDING', 'SEAT BELTS', '#2fbf71'], ['SHUT', '9 COASTERS']]); break; }
    case 12: { // if the bar feels loose: don't ride (he tugs on it)
      sH = STATION; placeTrain(sH); gpose = TUG; glift = 0.01 * Math.max(0, Math.sin(lt * 4)); [cp, ct] = onboard(0, V(-2.2, 2.0, -1.8), V(-0.5, 1.5, 0.1)); fov = 34;
      hud.visible = true; drawHud([['BAR FEELS', 'LOOSE?', '#ffd23a'], ['THEN', "DON'T RIDE", '#ff6a5c']], 'TELL A WORKER', '#2f7d4a'); break; }
    case 13: { // dusk: the empty train in the station
      sH = STATION; placeTrain(sH); SKYU.uSet.value = 1; scene.background.set(0xd98a62); scene.fog.color.set(0xc98a70); sun.color.set(0xff9a5a); sun.intensity = 1.2; hemi.intensity = 0.45; cp = V(32 - 3 * u, 4, 44); ct = V(-60, 22, -30); fov = 40; break; }
  }
  // riders: G (seat 2) and K (seat 3) in the front car; K stands on the platform as the worker in the station check
  RG.applyPose(gpose, seatRoot(0, 1, glift)); RK.applyPose(kroot ? kpose : SITR, kroot || seatRoot(0, 2, glift));
  G.root.visible = K.root.visible = nb !== 13 && nb !== 3 && nb !== 1 && nb !== 2 ? true : nb === 1 || nb === 2;   // far shots keep them (tiny); the empty station at dusk and the incident shot don't
  if (nb === 13 || nb === 3 || nb === 10) G.root.visible = K.root.visible = false;
  G.root.updateMatrixWorld(true); K.root.updateMatrixWorld(true);
  if (pov) { // eye point just in front of his face, looking down the track and down 'pov' degrees (the bar and his legs in view)
    const q = cars[0].quaternion, fw = V(0, 0, -1).applyQuaternion(q); up = V(0, 1, 0).applyQuaternion(q); const hd = wp(G.bones.head);
    cp = hd.clone().addScaledVector(up, 0.11).addScaledVector(fw, 0.1); ct = cp.clone().addScaledVector(fw, 10).addScaledVector(up, -10 * Math.tan(pov * D2R)); fov = 80; near = 0.06; }
  if (window.CAMO) { const o = window.CAMO, c = cars[0]; if (o.hide) { c.userData.fig0.visible = false; bars[0][0].visible = false; c.userData.wallL.visible = false; } cp = c.localToWorld(V(...o.p)); ct = c.localToWorld(V(...o.t)); fov = o.fov || 30; near = 0.03; up = V(0, 1, 0).applyQuaternion(c.quaternion); }   // debug camera for clip checks
  camera.position.copy(cp); camera.up.copy(up); camera.lookAt(ct); camera.fov = fov; camera.near = near; camera.updateProjectionMatrix();
  // arrows face the camera (billboards); 'down' ones flipped
  for (const [a, p, s, dn] of ARR) { a.visible = true; a.position.copy(p); a.quaternion.copy(camera.quaternion); if (dn) a.quaternion.multiply(new THREE.Quaternion().setFromAxisAngle(V(0, 0, 1), Math.PI)); a.scale.setScalar(s); }
  return { b: nb, focus: ct }; }
// ------------------------------------------------------------------ look + frame I/O
import { makeLook } from '/look.js';
const LOOK = makeLook(THREE, renderer, scene, camera, W, H, { overlays: [hud, upArrow, downArrow, barArrow, glow], aperture: 0.0007, maxblur: 0.006, rim: 1.4, noAO: [window.__SKY] });
let FOC = V(0, 1, 0);
function update(t) { t = clamp(t, 0, TOTAL - 1e-3); const r = shot(t); fitHud();
  const at = cars[0].position.clone(); sun.position.copy(at).add(V(25, 45, 30)); sun.target.position.copy(at); sun.target.updateMatrixWorld(); FOC = r.focus; return r; }
function stepTo(i) { return update(i / FPS); }
const draw = () => LOOK.render(FOC, { ao: true, dof: true });
const gl = renderer.getContext(), px = new Uint8Array(W * H * 4);
window.renderAll = async (f0, f1) => { for (let i = f0; i < f1; i++) { stepTo(i); draw(); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); await fetch('/frame', { method: 'POST', body: px }); } return 'ok'; };
window.renderAtT = t => { stepTo(Math.round(t * FPS)); draw(); return renderer.domElement.toDataURL('image/png'); };
window.dbg = { THREE, scene, camera, G, K, RG, RK, shot, cars };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS); window.READY = true;
window.SCN = { THREE, scene, camera, stepTo, renderer, FPS, B, DUR, TOTAL };
