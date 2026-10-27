// "You just died. Here's what happens to your body." - a 3D Short with the sculpted, skinned guy (regular 3D), the first 48 hours, no gore.
//   afterdeath.html?w=1080&h=1920            (times from afterdeath/times.json; one shot per narration line)
// Beats: 0 x-ray on his chest as he lies on the bed: the last heartbeat (hook) | 1 x-ray from above: blood stops, the brain dims
//        2 hearing may go last: sound rings reach his ear, a spot in his brain lights | 3 every muscle goes loose (head rolls, hands open, feet fall out)
//        4 thermal view: he cools, about 1.5 F an hour | 5 x-ray side view: blood sinks to his back (purple) | 6 stiffening creeps from jaw and eyelids down, 12 hours
//        7 a day later: the stiffness fades | 8 the fingertip up close: the skin shrinks back, the nail stays the same | 9 before: asleep, breathing; push into his chest (loops)
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { loadGuy } from '/guy3d.js';

const Q = new URLSearchParams(location.search);
const W = +Q.get('w') || 720, H = +Q.get('h') || 1280;
const FPS = 30;
const TIMES = await (await fetch('/afterdeath/times.json')).json();
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
const bed = new THREE.Group(); room.add(bed);
{ box(1.1, 0.28, 2.15, 0, 0.22, 0.05, mat(0x6b4a32, 0.6), 0.03, bed); box(1.15, 1.0, 0.08, 0, 0.5, -1.06, mat(0x5a3d28, 0.6), 0.03, bed);
  box(1.04, 0.2, 2.05, 0, MAT - 0.1, 0.05, mat(0xeae6dc, 0.85), 0.06, bed); box(1.06, 0.03, 2.07, 0, MAT - 0.012, 0.05, mat(0xc9d6e6, 0.9), 0.015, bed);
  box(0.62, 0.09, 0.38, 0, MAT + 0.03, -0.78, mat(0xf2f0ea, 0.9), 0.04, bed);
  box(1.06, 0.08, 0.5, 0, MAT + 0.03, 0.85, mat(0x3f5f8a, 0.9), 0.03, bed); }
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

// ------------------------------------------------------------------ the fingertip up close (beat 8): the skin shrinks back, the nail stays the same
const FT = V(0, 0, -200);
const ft = new THREE.Group(); ft.position.copy(FT); scene.add(ft);
ft.add(new THREE.Mesh(new THREE.SphereGeometry(30, 32, 16), new THREE.MeshBasicMaterial({ color: 0x1a1d24, side: THREE.BackSide })));
{ const l1 = new THREE.DirectionalLight(0xfff0e0, 2.6); l1.position.set(2, 4, 3); ft.add(l1); ft.add(l1.target); const l2 = new THREE.DirectionalLight(0x9ab8ff, 1.0); l2.position.set(-3, 1, -2); ft.add(l2); ft.add(l2.target); }
const fSkin = new THREE.Group(); ft.add(fSkin);
const skinM = new THREE.MeshPhysicalMaterial({ color: 0xd99a7c, roughness: 0.55, sheen: 0.2, sheenColor: new THREE.Color(0xffb099) });
{ const c = new THREE.Mesh(new THREE.CapsuleGeometry(0.5, 2.4, 12, 32).rotateZ(Math.PI / 2), skinM); c.scale.set(1, 0.82, 1); c.castShadow = true; fSkin.add(c);
  }
const nail = new THREE.Group(); ft.add(nail); nail.position.set(1.12, 0, 0);
{ const nm = new THREE.MeshPhysicalMaterial({ color: 0xf0c2b8, roughness: 0.2, clearcoat: 1, side: THREE.DoubleSide });
  const plate = new THREE.Mesh(new THREE.CylinderGeometry(0.43, 0.43, 1.15, 32, 1, true, Math.PI / 2 - 0.85, 1.7).rotateZ(Math.PI / 2), nm); nail.add(plate);
  const tipM = new THREE.MeshPhysicalMaterial({ color: 0xf8f4ec, roughness: 0.3, clearcoat: 0.8, side: THREE.DoubleSide }); const edge = new THREE.Mesh(new THREE.CylinderGeometry(0.432, 0.432, 0.16, 32, 1, true, Math.PI / 2 - 0.85, 1.7).rotateZ(Math.PI / 2), tipM); edge.position.x = 0.65; nail.add(edge); }
const ruler = new THREE.Group(); ft.add(ruler);
{ const rm = new THREE.MeshBasicMaterial({ color: 0xffd23f, toneMapped: false }); const bar = new THREE.Mesh(new THREE.BoxGeometry(1.15, 0.025, 0.025), rm); ruler.add(bar);
  for (const x of [-0.575, 0.575]) { const tk = new THREE.Mesh(new THREE.BoxGeometry(0.025, 0.16, 0.025), rm); tk.position.x = x; ruler.add(tk); } ruler.position.set(1.2, 0.62, 0.34); }

// ------------------------------------------------------------------ him
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

// ------------------------------------------------------------------ x-ray: a see-through glow body (same skeleton), organs inside
const xrayMat = new THREE.MeshStandardMaterial({ color: 0x000000, emissive: 0x58b8ff, emissiveIntensity: 1, transparent: true, opacity: 1, depthWrite: false, blending: THREE.AdditiveBlending, roughness: 1, metalness: 0 });
xrayMat.onBeforeCompile = sh => { sh.fragmentShader = sh.fragmentShader.replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\n  totalEmissiveRadiance *= 0.015 + 0.85 * pow(1.0 - abs(dot(normalize(normal), normalize(vViewPosition))), 2.4);'); };
const XRAY = [], NORMAL = [];
G.root.traverse(o => { if (!o.isMesh || o.userData.xray) return; NORMAL.push(o); });
const XSRC = Object.entries(G.meshes).filter(([n]) => !/^(hair|hairCards|sole)/.test(n)).map(([, m]) => m);   // the glow body: skin and clothes (no hair, no soles)
for (const o of XSRC) { let x; if (o.isSkinnedMesh) { x = new THREE.SkinnedMesh(o.geometry, xrayMat); x.bind(o.skeleton, o.bindMatrix); } else x = new THREE.Mesh(o.geometry, xrayMat);
  x.userData.xray = true; x.position.copy(o.position); x.quaternion.copy(o.quaternion); x.scale.copy(o.scale); x.frustumCulled = false; x.castShadow = false; x.renderOrder = 5; o.parent.add(x); XRAY.push(x); }
G.reset(); G.root.updateMatrixWorld(true);
const toLocal = (bone, p) => bone.worldToLocal(p.clone());
const organMat = (c, e) => new THREE.MeshStandardMaterial({ color: c, emissive: e, emissiveIntensity: 0.9, roughness: 0.45 });
const heartM = organMat(0x8a1a1a, 0xff2a2a), brainM = organMat(0x9a5a7a, 0xff8ab8), lungM = new THREE.MeshStandardMaterial({ color: 0x6a3a4a, emissive: 0xff7a9a, emissiveIntensity: 0.25, roughness: 0.6, transparent: true, opacity: 0.55, depthWrite: false });
const heart = new THREE.Group(); G.bones.chest.add(heart); heart.position.copy(toLocal(G.bones.chest, V(0.03, 1.265, -0.035)));
{ const g = new THREE.SphereGeometry(0.052, 28, 20); const p = g.attributes.position; for (let i = 0; i < p.count; i++) { const v = V(p.getX(i), p.getY(i), p.getZ(i)); const k = 1 + 0.25 * Math.max(0, -v.y / 0.052) - 0.12 * Math.max(0, v.y / 0.052); v.x *= k; v.z *= k; v.y *= 1.12; if (v.y < 0) v.x += 0.4 * v.y * 0.3; p.setXYZ(i, v.x, v.y, v.z); } g.computeVertexNormals();
  const h = new THREE.Mesh(g, heartM); h.rotation.z = 0.5; heart.add(h);
  const ao = new THREE.Mesh(new THREE.TorusGeometry(0.03, 0.012, 10, 20, Math.PI), heartM); ao.position.set(-0.01, 0.055, 0); ao.rotation.y = Math.PI / 2; heart.add(ao); }
const lungs = new THREE.Group(); G.bones.chest.add(lungs); lungs.position.copy(toLocal(G.bones.chest, V(0, 1.3, 0.0)));
for (const s of [-1, 1]) { const l = new THREE.Mesh(new THREE.SphereGeometry(0.075, 20, 16), lungM); l.scale.set(0.85, 1.55, 0.95); l.position.set(s * 0.085, 0.01, 0.01); lungs.add(l); }
const brain = new THREE.Group(); G.bones.head.add(brain); brain.position.copy(toLocal(G.bones.head, V(0, 1.685, 0.0)));
{ const g = new THREE.SphereGeometry(0.075, 48, 32); const p = g.attributes.position; for (let i = 0; i < p.count; i++) { const v = V(p.getX(i), p.getY(i), p.getZ(i)).normalize();
    const fold = 0.006 * Math.sin(v.x * 40 + Math.sin(v.y * 25) * 2) * Math.sin(v.z * 35 + v.y * 20) + (Math.abs(v.x) < 0.06 ? -0.006 : 0);
    v.multiplyScalar(0.075 + fold); v.y *= 0.82; v.z *= 1.18; p.setXYZ(i, v.x, v.y, v.z); } g.computeVertexNormals(); brain.add(new THREE.Mesh(g, brainM)); }
const ORGANS = [heart, lungs, brain];
const vessel = new THREE.Mesh(new THREE.CylinderGeometry(0.004, 0.004, 1, 8), organMat(0x8a1a1a, 0xff2a2a)); scene.add(vessel);
const bloodPts = (() => { const g = new THREE.BufferGeometry(); const p = new Float32Array(120 * 3); g.setAttribute('position', new THREE.BufferAttribute(p, 3)); const m = new THREE.Points(g, new THREE.PointsMaterial({ color: 0xff4040, size: 0.012, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending })); m.frustumCulled = false; m.renderOrder = 6; scene.add(m); return { m, p }; })();
function setXray(k) {                                          // 0 = normal, 1 = x-ray; in between: the glow comes on, then the skin goes
  for (const x of XRAY) x.visible = k > 0.01; xrayMat.emissiveIntensity = 1.1 * k;
  for (const o of NORMAL) o.visible = k < 0.6;
  for (const o of ORGANS) o.visible = k > 0.5; vessel.visible = bloodPts.m.visible = k > 0.5; }

// ------------------------------------------------------------------ clipping: both bodies vs the room, the floor, each other, and their own bodies
const SOLIDS = [];
const sbox = (name, obj, min, max) => SOLIDS.push({ name, obj, box: new THREE.Box3(min, max) });
sbox('nightstand', stand, V(-0.23, 0, -0.21), V(0.23, 0.55, 0.21));
const BODYPTS = { handR: 0.035, handL: 0.035, farmR: 0.035, farmL: 0.035, uarmR: 0.045, uarmL: 0.045, head: 0.09, chest: 0.12, hips: 0.1, shinR: 0.05, shinL: 0.05, footR: 0.04, footL: 0.04 };
function segDist(p, a, b) { const ab = b.clone().sub(a), t = clamp(p.clone().sub(a).dot(ab) / ab.lengthSq(), 0, 1); return p.distanceTo(a.clone().addScaledVector(ab, t)); }
const trunkDist = (Gx, p) => { const h = wp(Gx.bones.hips), c = wp(Gx.bones.chest), n = wp(Gx.bones.neck); return Math.min(segDist(p, h, c), segDist(p, c, n)); };
function clipOne(R, other, out, who) {
  const Gx = R.G; if (!Gx.root.visible) return;
  const pts = Object.entries(BODYPTS).map(([n, r]) => [n, wp(Gx.bones[n]), r]);
  for (const S of ['R', 'L']) for (const f of ['index', 'middle', 'pinky', 'thumb']) pts.push([f + ' tip ' + S, R.tip(f, S), 0.008]);
  const headC = wp(Gx.bones.head).add(V(0, 0.09, 0).applyQuaternion(wq(Gx.bones.head)));
  for (const [n, p, r] of pts) {
    if (p.y - r < GROUNDY - 0.015) out.push({ what: who + ' ' + n, into: 'the bed', depth: +((GROUNDY - (p.y - r)) * 100).toFixed(1) });
    for (const S of SOLIDS) { if (!S.obj.visible) continue; const q = p.clone().applyMatrix4(S.obj.matrixWorld.clone().invert()), bx = S.box;
      const dx = Math.min(q.x - bx.min.x, bx.max.x - q.x), dy = Math.min(q.y - bx.min.y, bx.max.y - q.y), dz = Math.min(q.z - bx.min.z, bx.max.z - q.z);
      const dd = Math.min(dx, dy, dz) + r; if (dx > -r && dy > -r && dz > -r && dd > 0.012) out.push({ what: who + ' ' + n, into: S.name, depth: +(dd * 100).toFixed(1) }); }
    if (/^(hand|farm|index|middle|pinky|thumb)/.test(n)) {
      const dT = trunkDist(Gx, p) - 0.11 - r; if (dT < -0.012) out.push({ what: who + ' ' + n, into: 'own body', depth: +(-dT * 100).toFixed(1) });
      const dH = p.distanceTo(headC) - 0.1 - r; if (dH < -0.03) out.push({ what: who + ' ' + n, into: 'own head', depth: +(-dH * 100).toFixed(1) }); }
    if (other && other.G.root.visible) {                        // into the other person's trunk or head (the hands on his chest rest on its surface)
      const dT = trunkDist(other.G, p) - 0.11 - r; if (dT < -0.015) out.push({ what: who + ' ' + n, into: 'the other body', depth: +(-dT * 100).toFixed(1) });
      const oh = wp(other.G.bones.head).add(V(0, 0.09, 0).applyQuaternion(wq(other.G.bones.head))); const dH = p.distanceTo(oh) - 0.1 - r; if (dH < -0.015) out.push({ what: who + ' ' + n, into: 'the other head', depth: +(-dH * 100).toFixed(1) }); }
  }
  const a = R.palmW('R'), c = R.palmW('L'); if (a.distanceTo(c) < 0.02) out.push({ what: who + ' palm R', into: 'palm L', depth: +((0.02 - a.distanceTo(c)) * 100).toFixed(1) });
}
function clipScan() { const out = []; scene.updateMatrixWorld(true); clipOne(RG, null, out, 'him'); return out; }

// more inside views: blood paths to the limbs, the settled blood (livor), the stiffening muscles (rigor), sound reaching the ear, a thermal look
const PATHS = [['brain', null], ['handR', 'handR'], ['handL', 'handL'], ['footR', 'footR'], ['footL', 'footL']];
const limbVessels = PATHS.slice(1).map(() => { const v = new THREE.Mesh(new THREE.CylinderGeometry(0.0035, 0.0035, 1, 8), organMat(0x8a1a1a, 0xff2a2a)); scene.add(v); return v; });
const limbBlood = (() => { const g = new THREE.BufferGeometry(); const p = new Float32Array(200 * 3); g.setAttribute('position', new THREE.BufferAttribute(p, 3)); const m = new THREE.Points(g, new THREE.PointsMaterial({ color: 0xff4040, size: 0.012, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending })); m.frustumCulled = false; m.renderOrder = 6; scene.add(m); return { m, p }; })();
const livorM = new THREE.MeshBasicMaterial({ color: 0xc850e8, transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending });
const LIVOR = [];
for (const [bn, sx, sy, sz, y] of [['hips', 0.16, 0.06, 0.13, 0.05], ['spine2', 0.15, 0.08, 0.12, 0.0], ['chest', 0.16, 0.1, 0.13, 0.05], ['thighR', 0.07, 0.18, 0.07, -0.2], ['thighL', 0.07, 0.18, 0.07, -0.2], ['shinR', 0.05, 0.17, 0.05, -0.2], ['shinL', 0.05, 0.17, 0.05, -0.2], ['uarmR', 0.045, 0.12, 0.045, -0.12], ['uarmL', 0.045, 0.12, 0.045, -0.12], ['head', 0.07, 0.07, 0.07, 0.08]]) {
  const b = G.bones[bn], m = new THREE.Mesh(new THREE.SphereGeometry(1, 20, 14), livorM); m.scale.set(sx, sy, sz * 0.6); m.position.set(0, y, 0.07); m.renderOrder = 6; b.add(m); LIVOR.push(m); }   // on his back side (rest +z), toward the bed
const rigorM = [];
const RIGOR = [['head', [0, -0.07, -0.05], 0.05, 0.0], ['head', [0, 0.07, -0.085], 0.035, 0.05], ['neck', [0, 0.05, 0], 0.06, 0.18], ['uarmR', [0, -0.14, 0], 0.06, 0.3], ['uarmL', [0, -0.14, 0], 0.06, 0.32], ['farmR', [0, -0.12, 0], 0.05, 0.42], ['farmL', [0, -0.12, 0], 0.05, 0.44],
  ['chest', [0, 0, -0.05], 0.12, 0.5], ['thighR', [0, -0.2, 0], 0.08, 0.6], ['thighL', [0, -0.2, 0], 0.08, 0.62], ['shinR', [0, -0.2, 0], 0.06, 0.72], ['shinL', [0, -0.2, 0], 0.06, 0.74]];
for (const [bn, p, r, t0] of RIGOR) { const m = new THREE.MeshBasicMaterial({ color: 0xff6a1a, transparent: true, opacity: 0, depthWrite: false, depthTest: false, toneMapped: false });
  const s = new THREE.Mesh(new THREE.SphereGeometry(r, 20, 14), m); if (/arm|thigh|shin/.test(bn)) s.scale.set(0.8, 2.2, 0.8); s.position.set(...p); s.renderOrder = 8; G.bones[bn].add(s); rigorM.push({ s, m, t0 }); }
G.reset(); G.root.updateMatrixWorld(true);
const EAR_L = V(0.08, 1.64, 0.01).applyMatrix4(G.bones.head.matrixWorld.clone().invert());        // his right ear (rest +x)
const hearSpot = new THREE.Mesh(new THREE.SphereGeometry(0.022, 16, 12), new THREE.MeshBasicMaterial({ color: 0x7ff0ff, transparent: true, opacity: 0, depthWrite: false, depthTest: false, blending: THREE.AdditiveBlending }));
hearSpot.position.set(0.045, -0.01, 0.005); hearSpot.renderOrder = 9; brain.add(hearSpot);
const rings = [0, 1, 2, 3, 4].map(() => { const r = new THREE.Mesh(new THREE.TorusGeometry(0.06, 0.004, 8, 40), new THREE.MeshBasicMaterial({ color: 0x9ff4ff, transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false })); r.renderOrder = 9; scene.add(r); return r; });
const thermMat = new THREE.MeshStandardMaterial({ color: 0x000000, emissive: 0xffaa33, roughness: 1, metalness: 0 });
const thermU = { uCore: { value: new THREE.Vector3() }, uK: { value: 0 } };
thermMat.onBeforeCompile = sh => { sh.uniforms.uCore = thermU.uCore; sh.uniforms.uK = thermU.uK;
  sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vWt;').replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvWt = (modelMatrix * vec4(transformed, 1.0)).xyz;');
  sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vWt; uniform vec3 uCore; uniform float uK;\nvec3 pal(float x){ x = clamp(x, 0.0, 1.0); vec3 a = vec3(1.0,0.97,0.7), b = vec3(1.0,0.62,0.12), c = vec3(0.9,0.15,0.12), d = vec3(0.5,0.06,0.5), e = vec3(0.1,0.1,0.55); return x < 0.25 ? mix(a,b,x/0.25) : x < 0.5 ? mix(b,c,(x-0.25)/0.25) : x < 0.75 ? mix(c,d,(x-0.5)/0.25) : mix(d,e,(x-0.75)/0.25); }')
    .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\n  { float d = distance(vWt, uCore); float heat = clamp(1.0 - d * 1.1, 0.0, 1.0); float f = pow(1.0 - abs(dot(normalize(normal), normalize(vViewPosition))), 1.6);\n    totalEmissiveRadiance = pal(1.0 - heat * (1.0 - 0.75 * uK) - 0.1 + 0.55 * uK + 0.25 * f); }'); };
const THERM = [];
for (const o of XSRC) { let x; if (o.isSkinnedMesh) { x = new THREE.SkinnedMesh(o.geometry, thermMat); x.bind(o.skeleton, o.bindMatrix); } else x = new THREE.Mesh(o.geometry, thermMat); x.userData.xray = true; x.frustumCulled = false; o.parent.add(x); THERM.push(x); x.visible = false; }
const thermColor = k => { const st = [[1.0, 0.95, 0.6], [1.0, 0.62, 0.12], [0.9, 0.18, 0.15], [0.55, 0.08, 0.5], [0.15, 0.12, 0.6]], x = clamp(k, 0, 1) * (st.length - 1), i = Math.min(st.length - 2, Math.floor(x)), f = x - i;
  return new THREE.Color(...st[i].map((v, j) => lerp(v, st[i + 1][j], f))); };

// ------------------------------------------------------------------ the story: he lies on his back on the bed the whole time (head toward -z)
const LIE = { x: 0, y: MAT + 0.13, z: 0.2 }, YAW = 180;
const qLieFoot = qAA(V(1, 0, 0), -90).multiply(yawQ(180));
const LYING = curl(curl({ armR: A(-8, 22, 0, 18, 30), armL: A(-8, 20, 0, 20, 30), neck: [-14, 0, 0], head: [-4, 0, 0], thighR: [4, 0, 4], thighL: [4, 0, -4], shinR: [-6, 0, 0], shinL: [-6, 0, 0] }, 'R', 34), 'L', 34);
function blinkAt(s) { const u = ((s + 40) % 3.7) / 0.16; return u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0; }
const STOP0 = 0.5;                                              // beat 0: the last heartbeat
function looseAt(t) { const b = beatAt(t), lt = t - B[b]; if (b === 9 || (b === 0)) return 0; if (b === 1 || b === 2) return 0.15; if (b === 3) return 0.15 + 0.85 * smooth(0.1, 0.85, lt / DUR[3]); return 1; }
function stiffAt(t) { const b = beatAt(t), lt = t - B[b]; if (b === 6) return lt / DUR[6]; if (b === 7) return 1 - smooth(0.3, 0.9, lt / DUR[7]); return 0; }
function guyState(t) {
  const b = beatAt(t), lt = t - B[b], u = lt / DUR[b];
  if (b === 8) return { show: false };
  const alive = b === 9 || (b === 0 && lt < STOP0), lo = looseAt(t), br = alive ? 0.5 + 0.5 * Math.sin(t * 2.4) : 0;
  const pose = addPose(LYING, { neck: [0, -24 * lo, 0], head: [0, -10 * lo, 0], spine2: [1.2 * br, 0, 0], chest: [1.2 * br, 0, 0],
    armR: A(-2 * lo, 6 * lo, 0, -10 * lo, 15 * lo), armL: A(-2 * lo, 6 * lo, 0, -10 * lo, 15 * lo) });
  curl(pose, 'R', lerp(34, 10, lo)); curl(pose, 'L', lerp(34, 12, lo));
  return { pose, root: { x: LIE.x, y: LIE.y, z: LIE.z, yaw: YAW, tilt: 90 }, footRoll: 28 * lo,
    face: { blink: alive ? (b === 9 ? 1 : 0.95) : 0.9, jaw: alive ? 0.02 : 0.08 + 0.3 * lo, look: [0, 0] }, heart: alive ? 'beat' : b === 0 && lt < STOP0 + 0.5 ? 'quiver' : 'still', show: true };
}

// ------------------------------------------------------------------ cameras (lying body: from above, screen-up toward his head, so he fills the tall frame)
function camAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b], u = lt / d;
  const ch = wp(G.bones.chest), hd = wp(G.bones.head), hp = wp(G.bones.hips);
  const UPH = V(0, 0, -1);
  if (b === 9 || b === 0) { const k = b === 9 ? 1 - smooth(DUR[9] - 1.1, DUR[9], lt) : smooth(0.8, 2.2, lt);
    const near = { p: ch.clone().add(V(0.02, 0.85, 0.05)), t: ch.clone().add(V(0.02, 0, -0.02)) }, far = { p: V(0.9, 2.1, 1.7), t: V(0, 0.6, -0.15) };
    return { pos: near.p.lerp(far.p, k), tgt: near.t.lerp(far.t, k), fov: lerp(40, 46, k), up: UPH.clone().lerp(V(0, 1, 0), k).normalize() }; }
  if (b === 1) return { pos: ch.clone().add(V(0.05, 2.1 - 0.4 * u, 0.25)), tgt: ch.clone().add(V(0, 0, 0.2)), fov: 46, up: UPH };
  if (b === 2) return { pos: hd.clone().add(V(-0.75 + 0.15 * u, 0.42, 0.35)), tgt: hd.clone().add(V(-0.05, 0.05, -0.02)), fov: 40 };
  if (b === 3) return { pos: V(0.95 - 0.1 * u, 1.55, 1.2), tgt: V(0, MAT + 0.1, -0.15), fov: 46 };
  if (b === 4) return { pos: ch.clone().add(V(0.02, 2.25 - 0.25 * u, 0.3)), tgt: ch.clone().add(V(0, 0, 0.25)), fov: 46, up: UPH };
  if (b === 5) return { pos: V(-1.2 + 0.15 * u, MAT + 0.5, 0.15), tgt: V(0, MAT + 0.08, -0.1), fov: 50 };
  if (b === 6) return { pos: V(1.0, 1.75, 1.05 - 0.15 * u), tgt: V(-0.05, MAT + 0.05, -0.2), fov: 50 };
  if (b === 7) return { pos: V(0.8 + 0.1 * u, 1.6, 1.25), tgt: V(-0.2, 0.9, -0.6), fov: 52 };
  return { pos: FT.clone().add(V(3.0 - 0.2 * u, 2.2 - 0.15 * u, 2.0 - 0.2 * u)), tgt: FT.clone().add(V(0.95, 0.3, 0)), fov: 40 };   // beat 8: the fingertip
}

// ------------------------------------------------------------------ per-frame update
let LASTF = -10, GROUNDY = MAT;
function update(t, frame) {
  t = ((t % TOTAL) + TOTAL) % TOTAL;
  const b = beatAt(t), lt = t - B[b], d = DUR[b], u = lt / d;
  const g = guyState(t); G.root.visible = g.show !== false;
  if (G.root.visible) {
    RG.applyPose(g.pose, g.root);
    for (const [S, sx] of [['R', -0.12], ['L', 0.12]]) { const f = V(sx * (1 + 0.3 * (g.footRoll / 28)), MAT + 0.102, LIE.z + 0.86);
      RG.foot(S, f, f.clone().add(V(0, 0.25, 0)), qAA(V(0, 0, 1), (S === 'R' ? 1 : -1) * g.footRoll).multiply(qLieFoot)); }
    G.root.updateMatrixWorld(true); delete RG.LAST.costR; delete RG.LAST.costL;
    RG.untwist(); G.face(g.face); G.root.updateMatrixWorld(true); }
  // ---- inside views
  const xk = b === 9 ? smooth(DUR[9] - 0.9, DUR[9] - 0.3, lt) : b === 0 ? 1 - smooth(0.9, 1.4, lt) : b === 1 || b === 2 || b === 5 ? 1 : 0;
  const th = b === 4;
  setXray(G.root.visible && !th ? xk : 0); for (const x of THERM) x.visible = th && G.root.visible; if (th) for (const o of NORMAL) o.visible = false;
  if (th) { thermU.uK.value = 0.6 * smooth(0, 1, u); thermU.uCore.value.copy(wp(G.bones.spine2)); thermMat.emissiveIntensity = 1; }
  const beatPh = t * 1.15, hb = Math.exp(-Math.pow(((beatPh % 1) - 0.1) / 0.06, 2)) + 0.5 * Math.exp(-Math.pow(((beatPh % 1) - 0.28) / 0.06, 2));
  heart.scale.setScalar(g.heart === 'beat' ? 1 + 0.16 * hb : g.heart === 'quiver' ? 1 + 0.02 * Math.sin(t * 90) : 1);
  heartM.emissiveIntensity = g.heart === 'still' ? 0.25 : g.heart === 'quiver' ? 0.5 : 0.9 + 0.6 * hb;
  const oxy = b === 9 || (b === 0 && lt < STOP0) ? 1 : b === 0 ? 1 - 0.35 * smooth(STOP0, DUR[0], lt) : b === 1 ? 0.65 - 0.55 * smooth(0.25, 0.85, u) : 0.1;
  brainM.emissive.setRGB(lerp(0.25, 1.0, oxy), lerp(0.3, 0.45, oxy), lerp(0.45, 0.62, oxy)); brainM.emissiveIntensity = 0.35 + 0.7 * oxy;
  lungs.scale.setScalar(1 + (g.heart === 'beat' ? 0.03 * Math.sin(t * 2.4) : 0));
  const flow = g.heart === 'beat' ? 1 : 0, stopK = b === 1 ? 1 - smooth(0, 0.45, u) : b === 0 && lt > STOP0 ? 1 - smooth(STOP0, STOP0 + 1.0, lt) : 0;
  const ends = () => { const a = wp(heart).add(V(0, 0.04, 0).applyQuaternion(wq(G.bones.chest))); return [a, wp(brain).add(V(0, -0.05, 0.02).applyQuaternion(wq(G.bones.head))), wp(G.bones.handR), wp(G.bones.handL), wp(G.bones.footR), wp(G.bones.footL)]; };
  if (vessel.visible && G.root.visible) { const E = ends(), a = E[0];
    const place = (v, c) => { v.position.copy(a).lerp(c, 0.5); v.scale.set(1, a.distanceTo(c), 1); v.quaternion.setFromUnitVectors(V(0, 1, 0), c.clone().sub(a).normalize()); };
    place(vessel, E[1]); limbVessels.forEach((v, i) => { v.visible = true; place(v, E[i + 2]); });
    const clockT = flow ? t * 0.9 : (b === 0 ? STOP0 + 0.9 * (lt - STOP0) * stopK : b === 1 ? 2 + 0.6 * lt * stopK : 3);
    const pp = bloodPts.p; for (let i = 0; i < 120; i++) { const s = ((i / 120) + clockT) % 1, q = a.clone().lerp(E[1], s); pp.set([q.x, q.y, q.z], i * 3); }
    const lp = limbBlood.p; for (let i = 0; i < 200; i++) { const k = i % 4, s = ((Math.floor(i / 4) / 50) + clockT * 0.7) % 1; let q = a.clone().lerp(E[k + 2], s);
      if (b === 5) { const sink = smooth(0.15, 0.85, u) * hash1(i * 3); q = q.clone().add(V(0, -0.1 * sink, 0)); } lp.set([q.x, q.y, q.z], i * 3); }
    bloodPts.m.geometry.attributes.position.needsUpdate = limbBlood.m.geometry.attributes.position.needsUpdate = true; limbBlood.m.visible = true;
    bloodPts.m.material.opacity = limbBlood.m.material.opacity = flow ? 1 : b === 5 ? 0.9 : 0.35 + 0.65 * stopK; }
  else { limbVessels.forEach(v => v.visible = false); limbBlood.m.visible = false; }
  livorM.opacity = b === 5 ? 0.9 * smooth(0.2, 0.9, u) : 0; if (b === 5) { limbVessels.forEach(v => v.visible = false); vessel.visible = false; }
  // ---- hearing (beat 2): sound rings travel to his ear; a spot in the brain lights up
  const earW = EAR_L.clone().applyMatrix4(G.bones.head.matrixWorld), src = earW.clone().add(V(-0.32, 0.3, -0.05));
  rings.forEach((r, i) => { const a = ((lt * 0.7 + i / 5) % 1); r.visible = b === 2; if (!r.visible) return; r.position.copy(src).lerp(earW, a); r.lookAt(earW); r.scale.setScalar(1.6 - 1.2 * a); r.material.opacity = 0.9 * Math.sin(Math.PI * a) * smooth(0.05, 0.2, u); });
  hearSpot.material.opacity = b === 2 ? (0.4 + 0.6 * Math.max(0, Math.sin(lt * 9))) * smooth(0.25, 0.4, u) : 0;
  // ---- stiffening (beats 6-7): glows creep from the jaw and eyelids down the body, then fade
  const sk = stiffAt(t); for (const r of rigorM) { const on = b === 6 ? smooth(r.t0 * 0.85, r.t0 * 0.85 + 0.12, sk) : b === 7 ? sk : 0; r.m.opacity = 0.6 * on * (0.85 + 0.15 * Math.sin(t * 6 + r.t0 * 9)); r.s.visible = on > 0.01 && G.root.visible; }
  // ---- the clock: hours pass in beats 6-7
  { const hrs = b === 6 ? lerp(1, 12, smooth(0, 1, u)) : b === 7 ? lerp(12, 24, smooth(0, 1, u)) : b < 6 ? 0.1 + t / 200 : 0.3;
    clockHands.m.rotation.z = -hrs * Math.PI * 2; clockHands.h.rotation.z = -(10 + hrs) / 12 * Math.PI * 2; }
  // ---- the fingertip (beat 8): the skin shrinks back; the nail stays the same length
  room.visible = b !== 8; ft.visible = b === 8;
  if (b === 8) { const k = smooth(0.25, 0.8, u); fSkin.scale.set(1 - 0.06 * k, 1 - 0.12 * k, 1 - 0.12 * k); fSkin.position.set(-0.2 * k, -0.04 * k, 0); ruler.visible = u > 0.15; }
  // ---- camera, light
  const C = camAt(t); camera.position.copy(C.pos); camera.up.copy(C.up || V(0, 1, 0)); camera.lookAt(C.tgt); camera.fov = C.fov; camera.updateProjectionMatrix();
  const dim = th ? 0.03 : 1 - 0.78 * (G.root.visible ? xk : 0);
  sun.position.set(1.4, 3.2, 1.6); sun.target.position.set(0, MAT, 0); sun.target.updateMatrixWorld();
  sun.intensity = 1.1 * dim; hemi.intensity = 0.55 * dim; scene.environmentIntensity = 0.3 * dim; lamp.intensity = 5 * dim;
  scene.background = b === 8 ? new THREE.Color(0x1a1d24) : th ? new THREE.Color(0x06081a) : new THREE.Color(0x2a3048).multiplyScalar(dim);
  clock.visible = !(G.root.visible && (xk > 0.3 || th));
  GROUNDY = MAT;
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
  if (window.CAM && window.CAM.hand) { const hp = RG.palmW(window.CAM.hand); window.CAM.tgt = hp.toArray(); window.CAM.pos = hp.clone().add(V(...window.CAM.off)).toArray(); }
  if (window.CAM) { camera.position.set(...window.CAM.pos); camera.up.set(0, 1, 0); camera.lookAt(...window.CAM.tgt); camera.fov = window.CAM.fov || 42; camera.updateProjectionMatrix(); }
  draw(); return renderer.domElement.toDataURL('image/png'); };
window.rigReport = i => { stepTo(i); const t = i / FPS, iq = G.root.getWorldQuaternion(new THREE.Quaternion()).invert();
  const ang = { ...RG.LAST }; delete ang.costR; delete ang.costL;
  return { t, beat: LASTB, ang, hips: wp(G.bones.hips).toArray(), car: 0, show: G.root.visible, cut: false,
    thumbs: ['R', 'L'].map(S => wp(G.bones['index1' + S]).sub(wp(G.bones['pinky1' + S])).applyQuaternion(iq).toArray()),
    forearms: ['R', 'L'].map(S => wp(G.bones['hand' + S]).sub(wp(G.bones['farm' + S])).normalize().applyQuaternion(iq).toArray()),
    cost: [null, null], clip: clipScan() }; };
window.dbg = { G, RG, wp, THREE };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS);
window.READY = true;
