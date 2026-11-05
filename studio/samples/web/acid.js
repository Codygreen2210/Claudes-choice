// "You wake up choking on your own stomach acid." - a 3D Short: can acid reflux kill you in your sleep? (the MakeHuman man, x-ray, no gore)
//   acid.html?w=1080&h=1920            (times from acid/times.json; one shot per narration line)
// Beats: 0 x-ray: acid surges up his throat, his voice box clamps, he jolts (hook) | 1 side x-ray: lying flat, the acid isn't held down
//        2 the valve at the top of his stomach, shut | 3 a big late meal: it slips open, acid creeps up | 4 it touches the voice box: he sits up gasping
//        5 it lets go, he lies back | 6 x-ray: acid drips into his lungs | 7 years of burns: the throat lining reddens | 8 asleep: very rare
//        9 blocks under the bed's head end, the acid slides back | 10-11 he rolls onto his left side; the clock: 3 hours | 12 see a doctor (loops)
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { loadGuy } from '/guy3d.js';
import { buildAnatomy } from '/anatomy.js';

const Q = new URLSearchParams(location.search);
const W = +Q.get('w') || 720, H = +Q.get('h') || 1280;
const FPS = 30;
const TIMES = await (await fetch('/acid/times.json')).json();
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
const mat = (c, r = 0.8, m = 0) => new THREE.MeshStandardMaterial({ color: c, roughness: r, metalness: m });
const box = (w, h, d, x, y, z, m, r = 0, parent = scene) => { const o = new THREE.Mesh(r > 0 ? new RoundedBoxGeometry(w, h, d, 2, Math.min(r, 0.4 * Math.min(w, h, d))) : new THREE.BoxGeometry(w, h, d), m); o.position.set(x, y, z); o.castShadow = true; o.receiveShadow = true; parent.add(o); return o; };

// ------------------------------------------------------------------ the bedroom at night
const room = new THREE.Group(); scene.add(room);
const floorTex = canvasTex(1024, 1024, g => { for (let i = 0; i < 16; i++) { const c = 130 + 30 * Math.random(); g.fillStyle = `rgb(${c},${c * 0.72 | 0},${c * 0.52 | 0})`; g.fillRect(0, i * 64, 1024, 64);
  g.fillStyle = 'rgba(40,25,15,0.6)'; g.fillRect(0, i * 64, 1024, 2); for (let s = 0; s < 3; s++) g.fillRect(((i * 397 + s * 331) % 1024), i * 64, 2, 64); } });
floorTex.wrapS = floorTex.wrapT = THREE.RepeatWrapping; floorTex.repeat.set(4, 4);
const floor = new THREE.Mesh(new THREE.PlaneGeometry(12, 12).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ map: floorTex, roughness: 0.6 })); floor.receiveShadow = true; room.add(floor);
box(12, 3.2, 0.12, 0, 1.6, -1.6, mat(0x5d6b86, 0.9), 0, room); box(0.12, 3.2, 12, 2.2, 1.6, 0, mat(0x55627c, 0.9), 0, room);
// the bed: frame, mattress (top at MAT), pillow, a folded blanket at the foot
const MAT = 0.55;
// the bed tilts as one piece with him (beat 9: blocks under its head end): an outer group at the pivot (the foot end's floor), an inner one back at the origin
const PIV = V(0, 0.08, 1.08), tiltRig = new THREE.Group(), tiltIn = new THREE.Group(); tiltRig.position.copy(PIV); tiltIn.position.copy(PIV).negate(); tiltRig.add(tiltIn); room.add(tiltRig);
const bed = new THREE.Group(); tiltIn.add(bed);
{ box(1.1, 0.28, 2.15, 0, 0.22, 0.05, mat(0x6b4a32, 0.6), 0.03, bed); box(1.15, 1.0, 0.08, 0, 0.5, -1.06, mat(0x5a3d28, 0.6), 0.03, bed);
  box(1.04, 0.2, 2.05, 0, MAT - 0.1, 0.05, mat(0xeae6dc, 0.85), 0.06, bed); box(1.06, 0.03, 2.07, 0, MAT - 0.012, 0.05, mat(0xc9d6e6, 0.9), 0.015, bed);
  box(0.62, 0.09, 0.38, 0, MAT + 0.03, -0.63, mat(0xf2f0ea, 0.9), 0.04, bed); }
const stand = new THREE.Group(); stand.position.set(-0.95, 0, -0.75); room.add(stand);
{ box(0.45, 0.5, 0.4, 0, 0.25, 0, mat(0x6b4a32, 0.6), 0.02, stand); box(0.14, 0.04, 0.14, 0, 0.52, 0, mat(0x2a2a2e, 0.4, 0.5), 0, stand);
  const sh = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.15, 0.18, 20, 1, true), new THREE.MeshStandardMaterial({ color: 0xf2e6cc, emissive: 0xffc070, emissiveIntensity: 0.9, side: THREE.DoubleSide })); sh.position.y = 0.78; stand.add(sh); box(0.02, 0.24, 0.02, 0, 0.64, 0, mat(0x2a2a2e), 0, stand); }
const lamp = new THREE.PointLight(0xffb870, 5, 6, 1.6); lamp.position.set(-0.95, 0.85, -0.75); scene.add(lamp);
{ const wtex = canvasTex(256, 256, g => { const gr = g.createLinearGradient(0, 0, 0, 256); gr.addColorStop(0, '#0b1430'); gr.addColorStop(1, '#25365e'); g.fillStyle = gr; g.fillRect(0, 0, 256, 256); for (let i = 0; i < 60; i++) { g.fillStyle = `rgba(255,255,240,${Math.random() * 0.8})`; g.fillRect(Math.random() * 256, Math.random() * 160, 2, 2); } g.fillStyle = '#f4f0dc'; g.beginPath(); g.arc(190, 60, 18, 0, 6.3); g.fill(); });
  const wi = new THREE.Mesh(new THREE.PlaneGeometry(1.0, 1.1), new THREE.MeshBasicMaterial({ map: wtex, toneMapped: false })); wi.position.set(0.9, 1.7, -1.53); room.add(wi);
  for (const [w, h, x, y] of [[1.12, 0.06, 0.9, 2.28], [1.12, 0.06, 0.9, 1.12], [0.06, 1.2, 0.34, 1.7], [0.06, 1.2, 1.46, 1.7], [0.04, 1.1, 0.9, 1.7]]) box(w, h, 0.05, x, y, -1.52, mat(0xe8e4dc, 0.5), 0, room); }
const clock = new THREE.Group(); clock.position.set(-0.75, 1.62, -1.53); room.add(clock);
const clockHands = {};
{ clock.add(new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.22, 0.04, 40).rotateX(Math.PI / 2), mat(0xfaf6ee, 0.5)));
  clock.add(new THREE.Mesh(new THREE.TorusGeometry(0.22, 0.02, 10, 40), mat(0x2a2a2e, 0.4, 0.5)));
  for (let i = 0; i < 12; i++) { const tk = new THREE.Mesh(new THREE.BoxGeometry(0.01, i % 3 ? 0.025 : 0.045, 0.01), mat(0x222222)); const a = i / 12 * Math.PI * 2; tk.position.set(Math.sin(a) * 0.18, Math.cos(a) * 0.18, 0.025); tk.rotation.z = -a; clock.add(tk); }
  for (const [k, l, w] of [['h', 0.1, 0.016], ['m', 0.16, 0.01]]) { const piv = new THREE.Group(); piv.position.z = 0.03; const hd = new THREE.Mesh(new THREE.BoxGeometry(w, l, 0.006), mat(0x222222, 0.5)); hd.position.y = l / 2 - 0.02; piv.add(hd); clock.add(piv); clockHands[k] = piv; } }


// ------------------------------------------------------------------ him
const G = await loadGuy(THREE, '/char/guy', { materials: { shirt: new THREE.MeshPhysicalMaterial({ color: 0x8c95a3, roughness: 0.9, sheen: 0.6, sheenRoughness: 0.7, sheenColor: new THREE.Color(0xc8d0dc), side: THREE.DoubleSide }) } });   // a soft grey sleep shirt
tiltIn.add(G.root); G.root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });

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
    const q = root.q ? root.q.clone() : new THREE.Quaternion().setFromEuler(new THREE.Euler((root.tilt || 0) * D2R, (root.yaw || 0) * D2R, (root.roll || 0) * D2R, 'YXZ'));
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
      let c = f.p.distanceToSquared(tg.p) / (0.006 * 0.006);
      if (tg.n) c += (1 - f.n.dot(tg.n)) * 40; if (tg.w) c += (1 - f.w.dot(tg.w)) * 25; if (tg.u) c += (1 - f.u.dot(tg.u)) * 25;
      for (let i = 0; i < 7; i++) { const [lo, hi] = ARM_LIM[i], mid = [20, 15, 0, 60, 0, 0, 0][i]; c += 0.6 * ((a[i] - mid) / (hi - lo)) ** 2; }
      const ins = torsoInside(f.el) + torsoInside(f.el.clone().lerp(f.p, 0.5)); c += (ins / 0.01) ** 2;
      if (prev) for (let i = 0; i < 7; i++) c += ((a[i] - prev[i]) / 3) ** 2;
      if (tg.extra) c += tg.extra(f);
      return c; };
    const m = MEM[key]; const prev = m && m.frame === frame - 1 ? m.a : (tg.seedIsPrev && tg.seed ? tg.seed : null);
    const COLD = [A(40, 15, 0, 80, 0), A(60, 25, 20, 60, 40), A(30, 40, -20, 100, -30), A(80, 10, 0, 110, 60), A(50, 30, 30, 40, 70), A(20, 20, -30, 120, -60), A(60, 10, -10, 100, 75), A(40, 20, 10, 90, -75)];
    const descend = (s0, big) => { let a = s0.map((v, i) => clamp(v, ARM_LIM[i][0], ARM_LIM[i][1])), ca = cost(a);
      for (let step = big; step >= 0.25; step /= 2) { let imp = true, g = 0;
        while (imp && g++ < 10) { imp = false; for (let i = 0; i < 7; i++) for (const sg of [1, -1]) { const b = a.slice(); b[i] = clamp(b[i] + sg * step, ARM_LIM[i][0], ARM_LIM[i][1]); const cb = cost(b); if (cb < ca - 1e-9) { a = b; ca = cb; imp = true; } } } }
      return { a, c: ca }; };
    let best = null;
    if (!prev && tg.seed) { const r = descend(tg.seed, 8); if (r.c < 8) best = r; }
    if (!best) for (const s0 of prev ? [prev] : (tg.seed ? [tg.seed, ...COLD] : COLD)) { const r = descend(s0, prev ? 4 : 16); if (!best || r.c < best.c) best = r; }
    if (prev && best.c > 20) for (const s0 of (tg.seed ? [tg.seed, ...COLD] : COLD)) { const r = descend(s0, 16); if (r.c < best.c) best = r; }
    MEM[key] = { frame, a: best.a }; return best; };
  R.hands = (list, key, frame) => { for (const h of list) { const sol = R.solveHand(h, key + h.S, frame); setArm(h.S, sol.a); R.LAST['arm' + h.S] = sol.a; R.LAST['cost' + h.S] = sol.c;
      const pp = {}; curl(pp, h.S, h.c ?? 30, h.th); for (const [n, e] of Object.entries(pp)) Gx.bones[n].quaternion.copy(Gx.REST[n].q).multiply(qTmp.setFromEuler(eTmp.set(e[0] * D2R, e[1] * D2R, e[2] * D2R))); } };
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

const rimX = (c, k) => { const m = new THREE.MeshStandardMaterial({ color: 0x000000, emissive: c, emissiveIntensity: k, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, roughness: 1 });
  m.onBeforeCompile = sh => { sh.fragmentShader = sh.fragmentShader.replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\n  totalEmissiveRadiance *= 0.02 + 0.9 * pow(1.0 - abs(dot(normalize(normal), normalize(vViewPosition))), 2.4);'); }; return m; };
// ------------------------------------------------------------------ x-ray: the detailed see-through body (anatomy.js): skeleton, airway, lungs, heart, gullet, valve, stomach
// skin-coloured plugs inside the shoulders (the head mesh is open where the arms join; the shirt hides it standing, not lying)
G.reset(); G.root.updateMatrixWorld(true);
for (const S of ['R', 'L']) for (const [x, y, z, r, bn] of [[0.13, 1.41, 0.0, 0.062, 'clav'], [0.075, 1.44, 0.0, 0.05, 'clav'], [0.19, 1.39, 0.0, 0.055, 'uarm']]) { const pl = new THREE.Mesh(new THREE.SphereGeometry(r, 20, 14), G.meshes.skin_head.material);
  const b = G.bones[bn + S]; pl.position.copy(b.worldToLocal(V((S === 'R' ? 1 : -1) * x, y, z).applyMatrix4(G.root.parent.matrixWorld))); b.add(pl); }
const NORMAL = []; G.root.traverse(o => { if (o.isMesh && !o.userData.xray) NORMAL.push(o); });
for (const n of ['shoeR', 'shoeL', 'soleR', 'soleL']) if (G.meshes[n]) { G.meshes[n].visible = false; G.meshes[n].userData.off = true; }   // no shoes in bed
const AN = buildAnatomy(THREE, G, { renderer });
// his legs in x-ray (a faint outline, they are under the covers)
const legX = rimX(0x58b8ff, 0.5);
const LEGX = []; { const o = G.meshes.jeans; if (o) { const x = new THREE.SkinnedMesh(o.geometry, legX); x.bind(o.skeleton, o.bindMatrix); x.position.copy(o.position); x.quaternion.copy(o.quaternion); x.scale.copy(o.scale);
  x.frustumCulled = false; x.renderOrder = 11; x.userData.xray = true; o.parent.add(x); LEGX.push(x); } }
G.reset(); G.root.position.set(0, 0, 0); G.root.quaternion.identity(); G.root.updateMatrixWorld(true);
const R0 = n => G.bones[n].getWorldPosition(new THREE.Vector3()).sub(tiltIn.getWorldPosition(new THREE.Vector3()));
const NECK0 = R0('neck'), CHEST0 = R0('chest'), SP20 = R0('spine2');
let XK = 0;
function setXray(k) { XK = k; const on = k > 0.5; for (const o of NORMAL) o.visible = !on && !o.userData.off; AN.setVisible(on); for (const x of LEGX) x.visible = on; }
G.reset(); G.root.updateMatrixWorld(true);

// ------------------------------------------------------------------ the blocks under the head end (beat 9 on), and a plate on the nightstand
const blocks = new THREE.Group(); room.add(blocks); for (const x of [-0.5, 0.5]) box(0.16, 0.23, 0.16, x, 0.115, -0.98, mat(0x8a6a4a, 0.7), 0.01, blocks);   // risers under the frame (its bottom is 8 cm off the floor, 15 cm more at the head end)
const TILT = Math.atan2(0.152, 2.08) / D2R;                          // six inches up at the head end: about 4 degrees

// ------------------------------------------------------------------ clipping: his hands into his own body or head, any of him into the bed
const BODYPTS = { handR: 0.035, handL: 0.035, farmR: 0.035, farmL: 0.035, uarmR: 0.045, uarmL: 0.045, chest: 0.12, hips: 0.1, shinR: 0.05, shinL: 0.05, footR: 0.04, footL: 0.04 };
function segDist(p, a, b) { const ab = b.clone().sub(a), t = clamp(p.clone().sub(a).dot(ab) / ab.lengthSq(), 0, 1); return p.distanceTo(a.clone().addScaledVector(ab, t)); }
const trunkDist = p => { const h = wp(G.bones.hips), c = wp(G.bones.chest), n = wp(G.bones.neck); return Math.min(segDist(p, h, c), segDist(p, c, n)); };
const headC = () => wp(G.bones.head).add(V(0, 0.09, 0).applyQuaternion(wq(G.bones.head)));
// the mattress top (and the pillow under his head) at a world point, following the bed's tilt
function supportAt(p) { const q = tiltIn.worldToLocal(p.clone()); let y = MAT; if (Math.abs(q.x) < 0.31 && q.z < -0.44 && q.z > -0.82) y = MAT + 0.075 - 0.02 * smooth(-0.49, -0.44, q.z);
  return tiltIn.localToWorld(V(q.x, y, q.z)).y + (q.y - tiltIn.worldToLocal(p.clone()).y); }
function bodyPts() { const pts = Object.entries(BODYPTS).map(([n, r]) => [n, wp(G.bones[n]), r]); pts.push(['head', headC(), 0.1]);
  for (const S of ['R', 'L']) for (const f of ['index', 'middle', 'pinky', 'thumb']) pts.push([f + ' tip ' + S, RG.tip(f, S), 0.008]); return pts; }
function clipScan() { const out = []; if (!G.root.visible) return out; scene.updateMatrixWorld(true); const hc = headC();
  for (const [n, p, r] of bodyPts()) { const sup = supportAt(p); if (p.y - r < sup - 0.015) out.push({ what: n, into: 'the bed', depth: +((sup - (p.y - r)) * 100).toFixed(1) });
    if (/^(hand|farm|index|middle|pinky|thumb)/.test(n)) { const dT = trunkDist(p) - 0.11 - r; if (dT < -0.012) out.push({ what: n, into: 'own body', depth: +(-dT * 100).toFixed(1) });
      const dH = p.distanceTo(hc) - 0.1 - r; if (dH < -0.03) out.push({ what: n, into: 'own head', depth: +(-dH * 100).toFixed(1) }); } }
  return out; }
// rest him on the bed: lift (or lower) the whole body so its lowest point touches the mattress or pillow
function settle() { G.root.updateMatrixWorld(true); let need = -1e9; for (const [n, p, r] of bodyPts()) { if (/tip|hand|head/.test(n)) continue; need = Math.max(need, supportAt(p) - (p.y - r)); }
  const up = tiltIn.worldToLocal(V(0, 1, 0).add(tiltIn.getWorldPosition(new THREE.Vector3()))).normalize(); G.root.position.addScaledVector(up, need + 0.004); G.root.updateMatrixWorld(true); }

// his head rests on the pillow: bend the neck (forward/back) until the back of his head just touches it
function headOnPillow(w = 1) { const nb = G.bones.neck, q0 = nb.quaternion.clone(); let a = 0;
  const gap = ang => { nb.quaternion.copy(q0).multiply(qAA(V(1, 0, 0), ang)); G.root.updateMatrixWorld(true); const hc = headC(); return (hc.y - 0.1) - supportAt(hc); };
  let g0 = gap(0); const g1 = gap(4), dg = (g1 - g0) / 4; if (Math.abs(dg) < 1e-5) { gap(0); return 0; }
  for (let it = 0; it < 8; it++) { a = clamp(a - g0 / dg, -20, 20); g0 = gap(a); if (Math.abs(g0) < 0.0002) break; }
  if (w < 1) gap(a * w); HEADA = a * w; return a; }
let HEADA = 0;
// ------------------------------------------------------------------ the covers: a quilted duvet draped over him (a height field over the bed, rebuilt every frame from his body), the sheet turned down at the top
const CBX = 0.535; let CZ0 = -0.29; const CZ1 = 1.08, CDROP = 0.3, CFOLD = 0.085;           // half-width of the bed top, top edge, foot end, how far the sides hang, the turned-down band
const CNX = 72, CNZ = 84;
const cS = i => lerp(-(CBX + CDROP), CBX + CDROP, i / (CNX - 1));
// the top edge dips at the middle (under his chin) and comes up over his shoulders, like covers pulled up
let CSH = 0.09; const cEdgeX = x => CZ0 - CSH * smooth(0.06, 0.2, Math.abs(x)), cEdge = i => cEdgeX(clamp(cS(i), -CBX, CBX));
const cW = (j, i) => { const e = cEdge(i); return j < 4 ? e + CFOLD * j / 3 : lerp(e + CFOLD, CZ1 + CDROP, (j - 3) / (CNZ - 4)); };
const quilt = canvasTex(1024, 1024, g => { g.fillStyle = '#5c7398'; g.fillRect(0, 0, 1024, 1024);
  for (let i = 0; i < 8; i++) for (let j = 0; j < 8; j++) { const gr = g.createRadialGradient(i * 128 + 64, j * 128 + 64, 8, i * 128 + 64, j * 128 + 64, 90); gr.addColorStop(0, 'rgba(255,255,255,0.10)'); gr.addColorStop(1, 'rgba(0,0,0,0.12)'); g.fillStyle = gr; g.fillRect(i * 128, j * 128, 128, 128); }
  g.strokeStyle = 'rgba(30,40,60,0.55)'; g.lineWidth = 3; g.setLineDash([10, 6]); for (let k = 0; k <= 8; k++) { g.beginPath(); g.moveTo(k * 128, 0); g.lineTo(k * 128, 1024); g.stroke(); g.beginPath(); g.moveTo(0, k * 128); g.lineTo(1024, k * 128); g.stroke(); }
  g.setLineDash([]); for (let n = 0; n < 9000; n++) { g.fillStyle = `rgba(${Math.random() < 0.5 ? '255,255,255' : '0,0,0'},0.05)`; g.fillRect(Math.random() * 1024, Math.random() * 1024, 2, 1); } });
quilt.wrapS = quilt.wrapT = THREE.RepeatWrapping; quilt.repeat.set(3, 4);
const duvetM = new THREE.MeshStandardMaterial({ map: quilt, roughness: 0.92, side: THREE.DoubleSide }), sheetM = new THREE.MeshStandardMaterial({ color: 0xeef0ee, roughness: 0.9, side: THREE.DoubleSide });
const coverGhost = rimX(0x58b8ff, 0.12); coverGhost.side = THREE.DoubleSide;
const covers = new THREE.Mesh(new THREE.BufferGeometry(), [sheetM, duvetM]); covers.castShadow = covers.receiveShadow = true; covers.frustumCulled = false; tiltIn.add(covers);
{ const pos = new Float32Array(CNX * CNZ * 3), uv = new Float32Array(CNX * CNZ * 2), idx = [];
  for (let j = 0; j < CNZ; j++) for (let i = 0; i < CNX; i++) { uv[(j * CNX + i) * 2] = cS(i) / 0.7; uv[(j * CNX + i) * 2 + 1] = -cW(j, i) / 0.7; }
  for (let j = 0; j < CNZ - 1; j++) for (let i = 0; i < CNX - 1; i++) { const a = j * CNX + i, b = a + 1, c = a + CNX, d = c + 1; idx.push(a, c, b, b, c, d); }
  const g = covers.geometry; g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('uv', new THREE.BufferAttribute(uv, 2)); g.setIndex(idx);
  const split = 3 * (CNX - 1) * 6; g.addGroup(0, split, 0); g.addGroup(split, idx.length - split, 1); }
// the rolled edge of the turned-down sheet
const lipM = sheetM; let lip = null;
// bone tips (tail end) in each bone's own frame, from the rest pose
const TAIL = {}; { G.reset(); G.root.updateMatrixWorld(true); for (const n of ['footR', 'footL', 'handR', 'handL']) { const b = G.bones[n]; TAIL[n] = b.userData.tail.clone().sub(b.userData.head).applyQuaternion(wq(b).invert()); } }
const tipOf = n => wp(G.bones[n]).add(TAIL[n].clone().applyQuaternion(wq(G.bones[n])));
function coverSpheres() { const S = [], L = p => tiltIn.worldToLocal(p.clone());
  const seg = (a, b, ra, rb, n) => { for (let k = 0; k <= n; k++) { const u = k / n; S.push([L(a.clone().lerp(b, u)), lerp(ra, rb, u)]); } };
  const hips = wp(G.bones.hips), sp1 = wp(G.bones.spine1), ch = wp(G.bones.chest), nk = wp(G.bones.neck);
  const rgt = wp(G.bones.uarmR).sub(wp(G.bones.uarmL)).normalize(), rgtH = wp(G.bones.thighR).sub(wp(G.bones.thighL)).normalize();
  for (let k = 0; k <= 8; k++) { const u = k / 8, c = u < 0.5 ? hips.clone().lerp(sp1, u * 2) : sp1.clone().lerp(ch, u * 2 - 1), r = rgtH.clone().lerp(rgt, u).normalize();
    for (const s of [-1, 1]) S.push([L(c.clone().addScaledVector(r, s * 0.07)), 0.112]); }
  seg(ch, nk, 0.11, 0.07, 3);
  for (const X of ['R', 'L']) { const th = wp(G.bones['thigh' + X]), kn = wp(G.bones['shin' + X]), an = wp(G.bones['foot' + X]), to = tipOf('foot' + X);
    seg(th, kn, 0.085, 0.06, 6); seg(kn, an, 0.058, 0.045, 6); seg(an, to, 0.05, 0.035, 3);
    const sh = wp(G.bones['uarm' + X]), el = wp(G.bones['farm' + X]), wr = wp(G.bones['hand' + X]), ht = tipOf('hand' + X);
    seg(sh, el, 0.052, 0.042, 4); seg(el, wr, 0.042, 0.032, 4); seg(wr, ht, 0.035, 0.025, 2); }
  return S; }
const CH = new Float32Array(CNX * CNZ), CRAW = new Float32Array(CNX * CNZ), CTMP = new Float32Array(CNX * CNZ);
// his actual skinned surface (shirt, jeans, arms, hands), every few vertices: the covers lie on it
const DRAPE_SRC = [['skin_head', 3], ['shirt', 2], ['jeans', 2], ['skin_armR', 3], ['skin_armL', 3], ['skin_handR', 2], ['skin_handL', 2]].filter(([n]) => G.meshes[n]).map(([n, k]) => [G.meshes[n], k]);
const _dv = new THREE.Vector3(), _dm = new THREE.Matrix4();
// the head mesh runs down over his upper chest: only that part (below the collar, rest height under 1.44 m) holds the covers up, never the chin
const HEADLOW = (() => { const p = G.meshes.skin_head.geometry.attributes.position, m = new Uint8Array(p.count); for (let v = 0; v < p.count; v++) m[v] = p.getY(v) < 1.44 ? 1 : 0; return m; })();
function drapeCovers(sitK = 0, sideK = 0) { CSH = 0.09 * (1 - smooth(0, 0.6, sideK)); const S = coverSpheres(), pad = 0.03, base = MAT + 0.028;
  // the top edge rides just under his collarbone, so when he curls up or rolls the covers slide with him instead of climbing over his face
  CZ0 = clamp(tiltIn.worldToLocal(wp(G.bones.neck)).z + 0.04 + 0.09 * sitK, -0.3, 0.12);
  { const UV = covers.geometry.attributes.uv.array; for (let j = 0; j < CNZ; j++) for (let i = 0; i < CNX; i++) { UV[(j * CNX + i) * 2] = cS(i) / 0.7; UV[(j * CNX + i) * 2 + 1] = -(cW(j, i) - CZ0) / 0.7; } covers.geometry.attributes.uv.needsUpdate = true; }
  const X = i => clamp(cS(i), -CBX, CBX), Z = (j, i) => clamp(cW(j, i), cEdge(i), CZ1);
  for (let j = 0; j < CNZ; j++) for (let i = 0; i < CNX; i++) { const x = X(i), z = Z(j, i); let h = base;
    for (const [c, r] of S) { const rr = r + pad, dx = x - c.x, dz = z - c.z, d2 = dx * dx + dz * dz; if (d2 < rr * rr) h = Math.max(h, c.y + Math.sqrt(rr * rr - d2)); }
    CRAW[j * CNX + i] = h; }
  const XS = [], ZS = new Float32Array(CNX * CNZ); for (let i = 0; i < CNX; i++) XS.push(X(i)); for (let j = 0; j < CNZ; j++) for (let i = 0; i < CNX; i++) ZS[j * CNX + i] = Z(j, i);
  const dXs = (2 * (CBX + CDROP)) / (CNX - 1), r = 0.034, r2 = r * r;
  tiltIn.updateMatrixWorld(true); const inv = tiltIn.matrixWorld.clone().invert();
  for (const [m, step] of DRAPE_SRC) { m.updateMatrixWorld(true); _dm.multiplyMatrices(inv, m.matrixWorld); const n = m.geometry.attributes.position.count;
    const isHead = m === G.meshes.skin_head, zmin = isHead ? CZ0 - CSH + 0.015 : CZ0 - CSH - r;
    for (let v = 0; v < n; v += step) { if (isHead && !HEADLOW[v]) continue; m.getVertexPosition(v, _dv); _dv.applyMatrix4(_dm); const x = _dv.x, y = _dv.y, z = _dv.z; if (z < zmin || y < base - 0.02) continue;
      const i0 = Math.max(0, Math.floor((x - r + CBX + CDROP) / dXs)), i1 = Math.min(CNX - 1, Math.ceil((x + r + CBX + CDROP) / dXs));
      if (isHead && z < cEdgeX(x) + 0.015) continue;
      for (let i = i0; i <= i1; i++) { const dx = XS[i] - x; for (let j = 0; j < CNZ; j++) { const dz = ZS[j * CNX + i] - z; if (dz > r) break; if (dz < -r) continue;
        const d2 = dx * dx + dz * dz; if (d2 < r2) { const h = y + 0.012 + Math.sqrt(r2 - d2) * 0.6, k = j * CNX + i; if (h > CRAW[k]) CRAW[k] = h; } } } } }
  CH.set(CRAW);
  // the cloth spans the gaps between high points (it can only fall so steeply), then softens
  const dX = (2 * (CBX + CDROP)) / (CNX - 1), slope = 0.8;
  for (let pass = 0; pass < 2; pass++) {
    for (let j = 0; j < CNZ; j++) { for (let i = 1; i < CNX; i++) { const k = j * CNX + i; CH[k] = Math.max(CH[k], CH[k - 1] - slope * Math.abs(X(i) - X(i - 1)) - 0.0005); }
      for (let i = CNX - 2; i >= 0; i--) { const k = j * CNX + i; CH[k] = Math.max(CH[k], CH[k + 1] - slope * Math.abs(X(i) - X(i + 1)) - 0.0005); } }
    for (let i = 0; i < CNX; i++) { for (let j = 1; j < CNZ; j++) { const k = j * CNX + i; CH[k] = Math.max(CH[k], CH[k - CNX] - slope * Math.abs(Z(j, i) - Z(j - 1, i)) - 0.0005); }
      for (let j = CNZ - 2; j >= 0; j--) { const k = j * CNX + i; CH[k] = Math.max(CH[k], CH[k + CNX] - slope * Math.abs(Z(j, i) - Z(j + 1, i)) - 0.0005); } } }
  for (let it = 0; it < 3; it++) { for (let j = 0; j < CNZ; j++) for (let i = 0; i < CNX; i++) { let s = 0, n = 0; for (let b = -1; b <= 1; b++) for (let a = -1; a <= 1; a++) { const ii = i + a, jj = j + b; if (ii < 0 || jj < 0 || ii >= CNX || jj >= CNZ) continue; s += CH[jj * CNX + ii]; n++; } CTMP[j * CNX + i] = s / n; }
    for (let k = 0; k < CH.length; k++) CH[k] = Math.max(CTMP[k], CRAW[k]); }
  const P = covers.geometry.attributes.position.array, edge = [];
  for (let j = 0; j < CNZ; j++) for (let i = 0; i < CNX; i++) { const s = cS(i), w = cW(j, i), ox = Math.max(0, Math.abs(s) - CBX), oz = Math.max(0, w - CZ1), o = Math.max(ox, oz), k = j * CNX + i;
    // over the edge of the mattress the cloth rolls round and hangs
    const roll = Math.min(o, 0.04), hang = Math.max(0, o - 0.04);
    const x = X(i) + Math.sign(s) * (ox > 0 ? 0.01 + Math.sin(Math.min(ox, 0.04) / 0.04 * Math.PI / 2) * 0.03 : 0), z = Z(j, i) + (oz > 0 ? 0.01 + Math.sin(Math.min(oz, 0.04) / 0.04 * Math.PI / 2) * 0.03 : 0);
    let y = CH[k] - (1 - Math.cos(roll / 0.04 * Math.PI / 2)) * 0.035 - hang * 1.1 + 0.006 * Math.sin(s * 37 + w * 11) * smooth(0, 0.06, hang);
    if (j < 4) y += 0.012 * (1 - j / 3);                                          // the turned-down band sits on the duvet
    P[k * 3] = x; P[k * 3 + 1] = Math.max(y, 0.3); P[k * 3 + 2] = z; if (j === 0 && Math.abs(s) <= CBX + 0.04) edge.push(V(x, P[k * 3 + 1] - 0.004, z - 0.004)); }
  covers.geometry.attributes.position.needsUpdate = true; covers.geometry.computeVertexNormals(); covers.geometry.computeBoundingSphere();
  if (lip) { lip.geometry.dispose(); } else { lip = new THREE.Mesh(new THREE.BufferGeometry(), lipM); lip.castShadow = lip.receiveShadow = true; lip.frustumCulled = false; tiltIn.add(lip); }
  lip.geometry = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(edge.filter((_, n) => n % 3 === 0 || n === edge.length - 1)), 64, 0.014, 10); }
// clipping check for the covers: every vertex of his clothes and skin under the duvet must stay below the duvet's actual surface (all vertices, not the drape's sample)
const CLIP_SRC = ['shirt', 'jeans', 'skin_armR', 'skin_armL', 'skin_handR', 'skin_handL', 'skin_head'].filter(n => G.meshes[n]).map(n => [n, G.meshes[n]]);
function coverY(x, z) { const P = covers.geometry.attributes.position.array, dX = (2 * (CBX + CDROP)) / (CNX - 1), fi = (x + CBX + CDROP) / dX, i = Math.floor(fi);
  if (i < 0 || i >= CNX - 1) return null; let j = -1; for (let k = 0; k < CNZ - 1; k++) if (P[(k * CNX + i) * 3 + 2] <= z && P[((k + 1) * CNX + i) * 3 + 2] > z) { j = k; break; } if (j < 0) return null;
  const a = j * CNX + i, b = a + 1, c = a + CNX, d = c + 1, xa = P[a * 3], xb = P[b * 3], za = P[a * 3 + 2], zc = P[c * 3 + 2];
  const u = (x - xa) / (xb - xa), v = (z - za) / (zc - za), y = k => P[k * 3 + 1];
  return u + v <= 1 ? y(a) + u * (y(b) - y(a)) + v * (y(c) - y(a)) : y(d) + (1 - u) * (y(c) - y(d)) + (1 - v) * (y(b) - y(d)); }
function coverClip() { const out = []; if (!covers.visible) return out; tiltIn.updateMatrixWorld(true); const inv = tiltIn.matrixWorld.clone().invert();
  for (const [n, m] of CLIP_SRC) { if (!m.visible) continue; m.updateMatrixWorld(true); _dm.multiplyMatrices(inv, m.matrixWorld); const cnt = m.geometry.attributes.position.count; let worst = 0, hits = 0;
    for (let v = 0; v < cnt; v++) { m.getVertexPosition(v, _dv); _dv.applyMatrix4(_dm); if (Math.abs(_dv.x) > CBX - 0.01 || _dv.z < cEdgeX(_dv.x) + 0.012 || _dv.z > CZ1 - 0.01) continue;
      const cy = coverY(_dv.x, _dv.z); if (cy === null) continue; const dd = _dv.y - cy; if (dd > 0.002) { hits++; worst = Math.max(worst, dd); } }
    if (hits) out.push({ what: n, into: 'through the covers', depth: +(worst * 100).toFixed(1), n: hits }); }
  return out; }
function setCoversXray(on) { covers.visible = lip.visible = !on; }

// ------------------------------------------------------------------ the story
const YAW = 180;
const LYING = curl(curl({ armR: A(-8, 22, 0, 18, 30), armL: A(-8, 20, 0, 20, 30), neck: [-14, 0, 0], head: [-4, 0, 0], thighR: [4, 0, 4], thighL: [4, 0, -4], shinR: [-6, 0, 0], shinL: [-6, 0, 0] }, 'R', 34), 'L', 34);
const qBack = new THREE.Quaternion().setFromEuler(new THREE.Euler(90 * D2R, YAW * D2R, 0, 'YXZ'));
// lying on his left side: the back pose turned a quarter around the bed's long axis (the sign that puts his left shoulder down, found once below)
let SIDE_SIGN = 1;
const qSideOf = k => qAA(V(0, 0, 1), SIDE_SIGN * 90 * k).multiply(qBack);
const SIDE = curl(curl({ armR: A(14, 6, 0, 24, 20), armL: A(60, 10, 0, 85, 0), neck: [4, 0, 0], head: [0, 0, 0], thighR: [48, 0, 4], thighL: [36, 0, -2], shinR: [-70, 0, 0], shinL: [-55, 0, 0], spine1: [-6, 0, 0] }, 'R', 30), 'L', 30);
{ RG.applyPose(LYING, { x: 0, y: 1, z: 0, q: qAA(V(0, 0, 1), 90).multiply(qBack) }); const lo = wp(G.bones.uarmL).y < wp(G.bones.uarmR).y; SIDE_SIGN = lo ? 1 : -1; }
// sitting up gasping (beat 4): the trunk comes up off the pillow, his right hand to his throat
const SIT = curl(curl({ ...LYING, spine1: [-12, 0, 0], spine2: [-14, 0, 0], chest: [-10, 0, 0], neck: [-26, 0, 0], head: [-8, 0, 0], armR: A(-4, 26, 0, 40, 30), armL: A(-4, 24, 0, 40, 30) }, 'R', 55), 'L', 55);   // gasping: head and shoulders curl up off the pillow, fists clench
function blinkAt(s) { const u = ((s + 40) % 3.7) / 0.16; return u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0; }
const JOLT0 = 1.15;                                                  // beat 0: the cords clamp, he jolts
// how far the acid has crept up the gullet (0 = in the stomach, 1 = at his voice box)
function acidAt(t) { const b = beatAt(t), lt = t - B[b], u = lt / DUR[b];
  if (b === 0) return lt < JOLT0 ? lerp(0.55, 1, smooth(0, JOLT0, lt)) : 1 - 0.7 * smooth(JOLT0 + 0.4, DUR[0], lt);
  if (b === 12) return lerp(0, 0.55, smooth(DUR[12] - 1.6, DUR[12], lt));
  if (b === 1) return 0.08 + 0.06 * Math.sin(lt * 3); if (b === 2) return 0; if (b === 3) return lerp(0, 0.75, smooth(0.25, 0.95, u)); if (b === 4) return lerp(0.75, 1, smooth(0, 0.35, u));
  if (b === 5) return 1 - smooth(0.1, 0.8, u); if (b === 6) return 1; if (b === 7) return 0.5; if (b === 9) return lerp(0.45, 0, smooth(0.55, 0.95, u)); return 0; }
// the state at a time
function guyState(t) {
  const b = beatAt(t), lt = t - B[b], u = lt / DUR[b];
  const br = 0.5 + 0.5 * Math.sin(t * 2.4);
  let pose = LYING, q = qBack, sideK = 0, sitK = 0, hand = 0, face = { blink: 1, jaw: 0.02 };
  if (b === 0) { const j = Math.exp(-Math.pow((lt - JOLT0 - 0.15) / 0.25, 2)); pose = addPose(LYING, { spine2: [-8 * j, 0, 0], chest: [-8 * j, 0, 0], neck: [14 * j, 0, 0], head: [6 * j, 0, 0] }); face = { blink: lerp(0.95, 0.1, smooth(JOLT0 - 0.1, JOLT0 + 0.1, lt)), jaw: 0.35 * j, fear: j, brow: j }; }
  if (b === 4) { sitK = smooth(0.25, 0.8, u); hand = smooth(0.3, 0.75, u); face = { blink: lerp(0.95, 0, smooth(0.2, 0.35, u)), jaw: 0.4 * sitK, fear: sitK, brow: sitK, look: [0, 0.2] }; }
  if (b === 5) { sitK = 1 - smooth(0.25, 0.95, u); hand = 1 - smooth(0.15, 0.6, u); face = { blink: lerp(0, 0.9, smooth(0.5, 0.95, u)), jaw: 0.25 * sitK, fear: 0.6 * sitK }; }
  if (b === 10) sideK = smooth(0.0, 0.75, lt); if (b === 11) sideK = 1;
  if (sitK > 0) pose = mixPose(LYING, SIT, sitK);
  if (sideK > 0) { pose = mixPose(LYING, SIDE, sideK); q = qSideOf(sideK); }
  pose = addPose(pose, { spine2: [1.2 * br, 0, 0], chest: [1.2 * br, 0, 0] });
  return { pose, q, sideK, sitK, hand, face };
}
// ------------------------------------------------------------------ cameras (lying body: from above, screen-up toward his head)
const UPH = V(0, 0, -1);
function camAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b], u = lt / d;
  const ch = wp(G.bones.chest), lar = AN.points.larynx(), les = AN.points.valve(), sto = AN.points.stomach(), mid = lar.clone().lerp(sto, 0.5);
  if (b === 0 || b === 12) { const k = b === 12 ? 1 - smooth(d - 1.7, d - 0.2, lt) : 0;   // above his throat and chest; beat 12 starts wide and comes back in
    const c0 = mid.clone().lerp(wp(G.bones.head), 0.25), near = { p: c0.clone().add(V(0.22 + 0.06 * (b === 0 ? u : 0), 0.95 - 0.08 * (b === 0 ? u : 0), 0.06)), t: c0 }, far = { p: V(1.0, 2.0, 1.8), t: V(0, 0.65, -0.1) };
    return { pos: near.p.lerp(far.p, k), tgt: near.t.lerp(far.t, k), fov: lerp(36, 46, k), up: UPH.clone().lerp(V(0, 1, 0), k).normalize() }; }
  if (b === 1) return { pos: mid.clone().add(V(0.55 - 0.05 * u, 0.95, 0.1)), tgt: mid.clone(), fov: 34, up: UPH };                     // from his left side (+x as he lies), above: the body flat
  if (b === 2 || b === 3) return { pos: les.clone().add(V(-0.06, 0.3 - 0.05 * u, 0.12 - 0.04 * (b === 3 ? 1 : u))), tgt: les.clone().add(V(0, 0, -0.04 * (b === 3 ? u : 0))), fov: 34, up: UPH };
  if (b === 4 || b === 5) { const h = wp(G.bones.head), c = wp(G.bones.chest).lerp(h, 0.5); return { pos: c.clone().add(V(0.75 - 0.06 * u, 0.42, 0.45)), tgt: c, fov: 40 }; }
  if (b === 6) return { pos: ch.clone().add(V(0.08, 0.72 - 0.08 * u, 0.06)), tgt: ch.clone().add(V(0, 0, -0.06)), fov: 38, up: UPH };
  if (b === 7) return { pos: mid.clone().add(V(0.06, 0.42 - 0.05 * u, 0.02)), tgt: mid.clone(), fov: 38, up: UPH };
  if (b === 8) return { pos: V(1.25 - 0.1 * u, 1.8, 1.6), tgt: V(0, 0.55, -0.15), fov: 46 };
  if (b === 9) { if (u < 0.5) return { pos: V(1.7, 1.05, -0.15 + 0.1 * u), tgt: V(0, 0.45, -0.7), fov: 44 };   // the blocks go in under the head end
    return { pos: mid.clone().add(V(0.55, 0.95, 0.1)), tgt: mid.clone(), fov: 34, up: UPH }; }   // x-ray from his left: the acid slides back down
  if (b === 10) return { pos: V(0.95, 1.85, 0.25), tgt: V(0, MAT + 0.15, -0.38), fov: 44 };   // from his left (+x): he rolls toward us onto his left side
  return { pos: clock.position.clone().add(V(0.2, -0.1, 0.9)), tgt: clock.position.clone(), fov: 40 };   // beat 11: the clock
}

// ------------------------------------------------------------------ per-frame update
let LASTF = -10;
const qLieFoot = qAA(V(1, 0, 0), -90).multiply(yawQ(180));
function update(t, frame) {
  t = ((t % TOTAL) + TOTAL) % TOTAL;
  const b = beatAt(t), lt = t - B[b], d = DUR[b], u = lt / d;
  // the bed's tilt: blocks under the head end from beat 9 through 11
  const tilt = b === 9 ? smooth(0.25, 0.45, u) : b === 10 || b === 11 ? 1 : 0;
  tiltRig.rotation.x = TILT * D2R * tilt; blocks.visible = b >= 9 && b <= 11; blocks.position.x = b === 9 ? 1.4 * (1 - smooth(0.05, 0.3, u)) : 0;
  tiltRig.updateMatrixWorld(true);
  const g = guyState(t);
  RG.applyPose(g.pose, { x: 0, y: MAT + 0.13, z: 0.2, q: g.q });
  settle(); { const w = 1 - smooth(0, 0.3, Math.max(g.sideK, g.sitK)); HEADA = 0; if (w > 0) headOnPillow(w); }
  if (g.sideK < 0.5) for (const [S, sx] of [['R', -0.12], ['L', 0.12]]) { const fl = V(sx, MAT + 0.102, 0.2 + 0.86), f = tiltIn.localToWorld(fl.clone()), pole = tiltIn.localToWorld(fl.clone().add(V(0, 0.25, 0)));
    RG.foot(S, f, pole, tiltRig.getWorldQuaternion(new THREE.Quaternion()).multiply(qLieFoot)); }
  G.root.updateMatrixWorld(true); delete RG.LAST.costR; delete RG.LAST.costL;
  RG.untwist(); G.face(g.face); G.root.updateMatrixWorld(true);
  drapeCovers(g.sitK, g.sideK);
  // ---- the x-ray and the acid
  const xk = b === 0 ? 1 : b === 12 ? smooth(d - 1.8, d - 1.2, lt) : b === 1 || b === 2 || b === 3 || b === 6 || b === 7 || b === 9 ? (b === 9 ? (u > 0.5 ? 1 : 0) : 1) : 0;
  setXray(xk); setCoversXray(xk > 0.5); AN.setAcidColumn(acidAt(t));
  const open = b === 2 ? 0 : b === 3 ? smooth(0.1, 0.35, u) : b === 4 ? 1 : b === 5 ? 1 - smooth(0.2, 0.8, u) : b === 0 ? 1 - smooth(JOLT0 + 0.3, DUR[0], lt) : b === 12 ? smooth(d - 1.8, d - 1.2, lt) : b === 6 || b === 7 ? 0.6 : 0;
  AN.setValve(open);
  const shut = b === 0 ? smooth(JOLT0 - 0.15, JOLT0, lt) * (1 - smooth(JOLT0 + 0.6, DUR[0], lt)) : b === 4 ? smooth(0.25, 0.35, u) : b === 5 ? 1 - smooth(0.2, 0.6, u) : 0;
  AN.setCords(shut); AN.setFlash(shut * (0.7 + 0.3 * Math.sin(t * 30)));
  AN.setAcidPool(b === 3 ? lerp(0.42, 0.55, smooth(0, 0.4, u)) : b === 11 ? 0.42 - 0.2 * smooth(0.2, 0.9, u) : 0.42);
  AN.dropsAt(lt, b === 6 && xk > 0.5);
  AN.setLungSores(b === 6 ? smooth(0.3, 0.9, u) : 0);
  AN.setBurns(b === 7 ? smooth(0.1, 0.8, u) : 0);
  AN.setRibs(b === 2 || b === 3 ? 0.3 : b === 7 ? 0.45 : 1);                 // close on the gullet and valve: the front of the ribcage fades so they read
  // ---- the clock: three hours go by in beat 11
  { const hrs = b === 11 ? lerp(0, 3, smooth(0.1, 0.9, u)) : 0; clockHands.m.rotation.z = -(0.5 + hrs) * Math.PI * 2; clockHands.h.rotation.z = -(7.5 + hrs) / 12 * Math.PI * 2; }
  // ---- camera, light
  const C = camAt(t); camera.position.copy(C.pos); camera.up.copy(C.up || V(0, 1, 0)); camera.lookAt(C.tgt); camera.fov = C.fov; camera.near = 0.02; camera.updateProjectionMatrix();
  const dim = 1 - 0.8 * xk;
  sun.position.set(1.4, 3.2, 1.6); sun.target.position.set(0, MAT, 0); sun.target.updateMatrixWorld();
  sun.intensity = 1.1 * dim; hemi.intensity = 0.55 * dim; scene.environmentIntensity = 0.3 * dim; lamp.intensity = 5 * dim;
  scene.background = new THREE.Color(0x2a3048).multiplyScalar(dim);
  clock.visible = !(xk > 0.3);
  return { beat: b, cut: false };
}

// ------------------------------------------------------------------ frame I/O (same contract as the other 3D Shorts)
const draw = () => renderer.render(scene, camera);
const gl = renderer.getContext(), px = new Uint8Array(W * H * 4);
let LASTB = 0;
function stepTo(i) { const t = i / FPS, b = beatAt(((t % TOTAL) + TOTAL) % TOTAL);
  if (i !== LASTF + 1) for (let j = Math.max(Math.round(B[b] * FPS), i - 12); j < i; j++) update(j / FPS, j);
  const r = update(t, i); LASTB = r.beat; LASTF = i; }
window.renderAll = async (f0, f1) => { for (let i = f0; i < f1; i++) { stepTo(i); draw(); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); await fetch('/frame', { method: 'POST', body: px }); } return 'ok'; };
window.renderAtT = t => { const i = Math.round(t * FPS); stepTo(i);
  if (window.CAM) { camera.position.set(...window.CAM.pos); camera.up.set(0, 1, 0); camera.lookAt(...window.CAM.tgt); camera.fov = window.CAM.fov || 42; camera.updateProjectionMatrix(); }
  draw(); return renderer.domElement.toDataURL('image/png'); };
window.rigReport = i => { stepTo(i); const t = i / FPS, iq = G.root.getWorldQuaternion(new THREE.Quaternion()).invert();
  const ang = { ...RG.LAST, neck: (RG.LAST.neck || [0, 0, 0]).map((v, i) => i ? v : v + HEADA) }; delete ang.costR; delete ang.costL;
  return { t, beat: LASTB, ang, hips: wp(G.bones.hips).toArray(), car: 0, show: G.root.visible, cut: false,
    thumbs: ['R', 'L'].map(S => wp(G.bones['index1' + S]).sub(wp(G.bones['pinky1' + S])).applyQuaternion(iq).toArray()),
    forearms: ['R', 'L'].map(S => wp(G.bones['hand' + S]).sub(wp(G.bones['farm' + S])).normalize().applyQuaternion(iq).toArray()),
    cost: [null, null], clip: [...clipScan(), ...coverClip()] }; };
window.dbg = { coverClip, G, RG, wp, THREE, guyState, acidAt, camera, camAt, beatAt, AN, NECK0, CHEST0, SP20, scene, renderer };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS);
window.READY = true;
