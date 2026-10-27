// "Your heart just stopped. Here's what happens to your body." - a 3D Short with the sculpted, skinned guy (regular 3D) and a helper.
//   heartstop.html?w=1080&h=1920            (times from heartstop/times.json; one shot per narration line)
// Beats: 0 x-ray on his chest: the heart stops; pull back, the mug drops, his knees go (hook) | 1 x-ray: he falls, blood stops, the brain dims
//        2 on the floor: he gasps (not real breathing) | 3 brain cells going dark | 4 the clock runs: 8-10 minutes
//        5 the twist: someone kneels beside him, shakes his shoulder, hands to his chest | 6 CPR: hard and fast, 2 inches deep
//        7 x-ray: each push sends blood to his brain; then the AED: "clear", the shock | 8 he's alive, breathing
//        9 earlier: at home with his coffee, the camera pushes into his chest (loops into beat 0)
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { loadGuy } from '/guy3d.js';

const Q = new URLSearchParams(location.search);
const W = +Q.get('w') || 720, H = +Q.get('h') || 1280;
const FPS = 30;
const TIMES = await (await fetch('/heartstop/times.json')).json();
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
const table = new THREE.Group(); table.position.set(1.75, 0, -0.8); home.add(table);
{ box(1.1, 0.06, 0.6, 0, 0.42, 0, mat(0x7a5236, 0.5), 0.02, table); for (const [x, z] of [[-0.5, -0.25], [0.5, -0.25], [-0.5, 0.25], [0.5, 0.25]]) box(0.05, 0.4, 0.05, x, 0.2, z, mat(0x5a3a26, 0.6), 0, table);
  box(0.25, 0.04, 0.18, 0.2, 0.47, 0.05, mat(0x2a2e3a, 0.3), 0.01, table); const pl = new THREE.Mesh(new THREE.SphereGeometry(0.14, 16, 12), mat(0x3f7a3a, 0.8)); pl.position.set(-0.3, 0.6, 0); table.add(pl); box(0.14, 0.14, 0.14, -0.3, 0.51, 0, mat(0xd8d2c4, 0.5), 0.02, table); }
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
// the mug (in his right hand), its pieces and the spilled coffee
const mug = new THREE.Group(); scene.add(mug);
{ const mm = mat(0xc8402c, 0.45); const body = new THREE.Mesh(new THREE.CylinderGeometry(0.042, 0.038, 0.1, 22, 1, true), new THREE.MeshStandardMaterial({ color: 0xc8402c, roughness: 0.45, side: THREE.DoubleSide })); mug.add(body);
  const bot = new THREE.Mesh(new THREE.CircleGeometry(0.038, 22).rotateX(Math.PI / 2), mm); bot.position.y = -0.05; mug.add(bot);
  const cof = new THREE.Mesh(new THREE.CircleGeometry(0.039, 22).rotateX(-Math.PI / 2), mat(0x3a2214, 0.2)); cof.position.y = 0.03; mug.add(cof);
  const handle = new THREE.Mesh(new THREE.TorusGeometry(0.026, 0.008, 8, 16, Math.PI), mm); handle.rotation.z = -Math.PI / 2; handle.position.x = 0.042; mug.add(handle); }
const shards = new THREE.InstancedMesh(new THREE.TetrahedronGeometry(0.02, 0), mat(0xc8402c, 0.45), 14); shards.castShadow = true; scene.add(shards);
const puddle = new THREE.Mesh(new THREE.CircleGeometry(0.22, 32).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0x3a2214, roughness: 0.1, transparent: true, opacity: 0.9 })); puddle.position.y = 0.006; scene.add(puddle);
const drops = (() => { const g = new THREE.BufferGeometry(); const p = new Float32Array(60 * 3); g.setAttribute('position', new THREE.BufferAttribute(p, 3)); const m = new THREE.Points(g, new THREE.PointsMaterial({ color: 0x4a2a18, size: 0.025 })); m.frustumCulled = false; scene.add(m); return { m, p }; })();
// the AED (beat 7): a box on the floor, two pads on his chest, wires
const aed = new THREE.Group(); scene.add(aed);
{ box(0.32, 0.1, 0.26, 0, 0.05, 0, mat(0x2fae4a, 0.5), 0.03, aed); box(0.12, 0.012, 0.08, -0.05, 0.106, 0, mat(0x111418, 0.3), 0, aed);
  const lab = canvasTex(128, 64, g => { g.fillStyle = '#2fae4a'; g.fillRect(0, 0, 128, 64); g.fillStyle = '#fff'; g.font = 'bold 34px Arial'; g.textAlign = 'center'; g.fillText('AED', 64, 44); });
  const lp = new THREE.Mesh(new THREE.PlaneGeometry(0.12, 0.06), new THREE.MeshBasicMaterial({ map: lab })); lp.rotation.x = -Math.PI / 2; lp.position.set(0.09, 0.103, 0); aed.add(lp);
  const btn = new THREE.Mesh(new THREE.CylinderGeometry(0.022, 0.022, 0.012, 16), new THREE.MeshStandardMaterial({ color: 0xff6a10, emissive: 0xff4a00, emissiveIntensity: 0 })); btn.position.set(-0.05, 0.11, 0.08); btn.name = 'btn'; aed.add(btn); }
const pads = [0, 1].map(() => { const p = new THREE.Mesh(new RoundedBoxGeometry(0.13, 0.008, 0.1, 2, 0.003), mat(0xf4f4f0, 0.6)); scene.add(p); return p; });
const wires = [0, 1].map(() => { const w = new THREE.Mesh(new THREE.CylinderGeometry(0.004, 0.004, 1, 6), mat(0x222222, 0.6)); scene.add(w); return w; });
const zap = new THREE.PointLight(0xbfe4ff, 0, 4, 1.5); scene.add(zap);

// ------------------------------------------------------------------ the brain cells (beat 3): neurons in the dark, going out one by one
const NEUR = V(0, 0, -200);
const neur = new THREE.Group(); neur.position.copy(NEUR); scene.add(neur);
neur.add(new THREE.Mesh(new THREE.SphereGeometry(30, 32, 16), new THREE.MeshBasicMaterial({ color: 0x07091a, side: THREE.BackSide })));
const NEURONS = [];
{ for (let i = 0; i < 26; i++) { const g = new THREE.Group(); const a = hash1(i * 3) * 6.28, r = 0.6 + 3.2 * hash1(i * 5);
    g.position.set(Math.cos(a) * r, -2 + 4 * hash1(i * 7), -1.5 - 6 * hash1(i * 11)); neur.add(g);
    const m = new THREE.MeshStandardMaterial({ color: 0x1a1030, emissive: 0xff5ab4, emissiveIntensity: 2.0, roughness: 0.5 });
    const soma = new THREE.Mesh(new THREE.SphereGeometry(0.16, 20, 14), m); soma.scale.set(1, 0.85, 1.1); g.add(soma);
    for (let k = 0; k < 6; k++) { const pts = [V(0, 0, 0)]; let d = V(hash1(i * 13 + k) - 0.5, hash1(i * 17 + k) - 0.5, hash1(i * 19 + k) - 0.5).normalize(), p = V(0, 0, 0);
      for (let s = 0; s < 5; s++) { d.add(V(hash1(i + k * 7 + s) - 0.5, hash1(i * 3 + k + s * 5) - 0.5, hash1(i * 7 + k * 3 + s) - 0.5).multiplyScalar(0.7)).normalize(); p = p.clone().addScaledVector(d, 0.25 + (k === 0 ? 0.35 : 0)); pts.push(p); }
      const tube = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 24, k === 0 ? 0.028 : 0.018, 6), m); g.add(tube); }
    NEURONS.push({ g, m, t0: 0.12 + 0.8 * hash1(i * 23) }); }
  const l = new THREE.PointLight(0xc070ff, 8, 20, 1.5); l.position.set(0, 2, 2); neur.add(l); }
const sparks = (() => { const g = new THREE.BufferGeometry(); const p = new Float32Array(300 * 3); g.setAttribute('position', new THREE.BufferAttribute(p, 3)); const m = new THREE.Points(g, new THREE.PointsMaterial({ color: 0xffa0e0, size: 0.04, transparent: true, opacity: 0.9, blending: THREE.AdditiveBlending, depthWrite: false })); m.frustumCulled = false; scene.add(m); return { m, p }; })();

// ------------------------------------------------------------------ the two people
const G = await loadGuy(THREE, '/char/guy', {});                                         // him (teal shirt)
const Hm = await loadGuy(THREE, '/char/guy', { materials: { shirt: new THREE.MeshPhysicalMaterial({ color: 0xd8432e, roughness: 0.85, sheen: 0.6, sheenColor: new THREE.Color(0xff9a80) }),
  jeans: new THREE.MeshStandardMaterial({ color: 0x3a3d48, roughness: 0.9 }), hair: new THREE.MeshStandardMaterial({ color: 0x1e1612, roughness: 0.6 }), skin: new THREE.MeshPhysicalMaterial({ color: 0xb87a5c, roughness: 0.55, sheen: 0.15, sheenColor: new THREE.Color(0xffb099) }) } });   // the helper
for (const g of [G, Hm]) { scene.add(g.root); g.root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } }); }
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
const RG = makeRig(G, 'him'), RH = makeRig(Hm, 'helper');
// his chest gives under the pushes: the chest bone moves toward his back, its children (neck, collarbones) move back out, so only the ribcage dips
function compress(d) { const c = G.bones.chest; c.position.copy(G.REST.chest.pos).add(V(0, 0, d)); for (const n of ['neck', 'clavR', 'clavL']) G.bones[n].position.copy(G.REST[n].pos).add(V(0, 0, -d)); }

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
const vessel = new THREE.Mesh(new THREE.CylinderGeometry(0.008, 0.008, 1, 8), organMat(0x8a1a1a, 0xff2a2a)); scene.add(vessel);
const bloodPts = (() => { const g = new THREE.BufferGeometry(); const p = new Float32Array(120 * 3); g.setAttribute('position', new THREE.BufferAttribute(p, 3)); const m = new THREE.Points(g, new THREE.PointsMaterial({ color: 0xff4040, size: 0.012, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending })); m.frustumCulled = false; m.renderOrder = 6; scene.add(m); return { m, p }; })();
function setXray(k) {                                          // 0 = normal, 1 = x-ray; in between: the glow comes on, then the skin goes
  for (const x of XRAY) x.visible = k > 0.01; xrayMat.emissiveIntensity = 1.1 * k;
  for (const o of NORMAL) o.visible = k < 0.6;
  for (const o of ORGANS) o.visible = k > 0.5; vessel.visible = bloodPts.m.visible = k > 0.5; }

// ------------------------------------------------------------------ the story
const P0 = V(0, 0, 0.6), YAW = 180;                           // where he stands (facing the camera, +z); he falls backward (toward -z)
const LIE = { x: 0, y: 0.13, z: 0.18 };                         // hips when lying on his back (head toward -z)
const qLieFoot = qAA(V(1, 0, 0), -90).multiply(yawQ(180));     // toes up
const sipAt = s => { const ph = ((s % 3.4) + 3.4) % 3.4; return smooth(1.2, 1.65, ph) * (1 - smooth(2.05, 2.45, ph)); };
function mugHand(s, loopIn = false) { const sip = sipAt(s); const x0 = P0.x, z0 = P0.z;
  return { S: 'R', p: V(x0 - 0.17, 1.15, z0 + 0.26).lerp(V(x0 - 0.09, 1.46, z0 + 0.2), sip), n: V(1, 0, 0.2).normalize(), u: V(0, 0.2, 1).normalize(), c: 68, seed: loopIn && LOOPSEED ? LOOPSEED : A(35, 15, -20, 95, 60), seedIsPrev: loopIn && !!LOOPSEED }; }
let LOOPSEED = null;
function blinkAt(s) { const u = ((s + 40) % 3.7) / 0.16; return u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0; }
const STOP0 = 0.4, DROP = 1.4, BUCK = 2.2;                     // beat 0: the heart stops, the mug slips, the knees go
const FALL0 = 0.0, FALLT = 1.25;                               // beat 1: the fall (local times)
const LYING = curl(curl({ armR: A(-8, 26, 0, 14, 20), armL: A(-8, 24, 0, 18, 20), neck: [4, 14, 0], head: [2, 10, 0], thighR: [4, 0, 4], thighL: [4, 0, -4], shinR: [-6, 0, 0], shinL: [-6, 0, 0] }, 'R', 30), 'L', 30);
function standingGuy(t, s, buck, stopped) {                    // s: his clock for the sip; buck 0..1: knees going
  const pose = addPose(STAND, { neck: [-3 + 2 * Math.sin(s * 1.3) * (1 - stopped) + 8 * sipAt(s) * (1 - stopped) - 18 * buck, 6 * buck, 4 * buck], head: [6 * sipAt(s) * (1 - stopped) - 10 * buck, 0, 6 * buck],
    spine1: [-6 * buck, 0, 3 * buck], spine2: [-4 * buck, 0, 0], armL: A(6 + 8 * stopped, 10 + 6 * stopped, 0, 16 + 10 * stopped) });
  return { pose, root: { x: P0.x, y: 0.95 - 0.16 * buck, z: P0.z, yaw: YAW, roll: 4 * buck }, feet: 'stand' };
}
// the fall: hips path, tilt (back), legs and arms keyed; feet stay planted, then slide out along the floor
function fallGuy(f) {                                           // f: seconds since the fall began (0 .. FALLT, then lying)
  const u = clamp(f / FALLT, 0, 1);
  const hk = [[0, 0.79, P0.z], [0.35, 0.52, P0.z - 0.05], [0.75, 0.2, 0.32], [1, LIE.y, LIE.z]];
  let hy = hk[0][1], hz = hk[0][2]; for (let i = 0; i < 3; i++) if (u >= hk[i][0]) { const k = sm(clamp((u - hk[i][0]) / (hk[i + 1][0] - hk[i][0]), 0, 1)); hy = lerp(hk[i][1], hk[i + 1][1], k); hz = lerp(hk[i][2], hk[i + 1][2], k); }
  const tilt = 90 * sm(clamp((u - 0.18) / 0.82, 0, 1)) ** 1.3;
  const pose = keyed([[0, standingGuy(0, 0, 1, 1).pose],
    [0.35 * FALLT, curl(curl(addPose(STAND, { neck: [-10, 10, 0], head: [-4, 8, 0], spine1: [-4, 0, 0], armR: A(25, 35, 0, 45), armL: A(25, 32, 0, 40) }), 'R', 20), 'L', 20)],
    [0.8 * FALLT, curl(curl(addPose(STAND, { neck: [10, 14, 0], head: [6, 10, 0], armR: A(10, 30, 0, 30, 10), armL: A(10, 28, 0, 30, 10) }), 'R', 26), 'L', 26)],
    [FALLT, LYING]], f);
  const fz = lerp(P0.z + 0.02, LIE.z + 0.86, smooth(0.32, 0.95, u)), fy = 0.102;
  const fq = new THREE.Quaternion().slerpQuaternions(yawQ(180), qLieFoot, smooth(0.4, 1, u));
  return { pose, root: { x: 0, y: hy, z: hz, yaw: YAW, tilt, roll: 4 * (1 - u) }, feet: 'fall', footZ: fz, footY: fy, footQ: fq, kneeUp: 1 - smooth(0.6, 1, u) };
}
function lyingGuy(t, opt = {}) {                                // opt: gasp (0..1), breathe (0..1), wake (0..1), jolt
  const g = opt.gasp || 0, br = opt.breathe || 0, j = opt.jolt || 0;
  const pose = addPose(LYING, { neck: [-10 * g - 3 * j - 6 * (opt.turn || 0), -18 * (opt.turn || 0), 0], head: [-3 * g, 0, 0], spine2: [1.5 * g + 1 * br, 0, 0], chest: [1 * g + 1 * br, 0, 0], armR: A(0, 4 * j, 0, 10 * j), armL: A(0, 4 * j, 0, 10 * j) });
  return { pose, root: { x: LIE.x, y: LIE.y + 0.015 * j + (opt.lift || 0), z: LIE.z, yaw: YAW, tilt: 90 }, feet: 'lie', footZ: LIE.z + 0.86, footY: 0.102, footQ: qLieFoot, kneeUp: 0 };
}
// the helper: kneels on his right side (x < 0), facing +x
const HYAW = -90, HX = -0.34;
function sternum() { const c = wp(G.bones.chest), s2 = wp(G.bones.spine2), up = V(0, 0, -1).applyQuaternion(wq(G.bones.chest));    // his front (rest -z), toward the ceiling when he lies
  return c.clone().lerp(s2, 0.35).addScaledVector(up, 0.115); }
function helperAt(b, lt, push) {                                // push: 0..1 how far down this push is
  const near = b === 5 ? smooth(0.45, 0.85, lt / DUR[5]) : b === 8 ? 0 : 1;
  const lean = b === 5 ? lerp(-52, -32, near) : b === 8 ? -52 : b === 7 && lt / DUR[7] > CUT7 ? -8 : -34 - 4 * push;
  const pose = curl(curl(addPose(STAND, { spine1: [-6, 0, 0], spine2: [-4, 0, 0], neck: [-28 + (b === 8 ? 16 : 0), 0, 0], head: [-10, 0, 0], thighR: [0, 0, 0], thighL: [0, 0, 0] }), 'R', 20), 'L', 20);
  const st = sternum().z;
  return { pose, root: { x: lerp(HX - 0.16, HX, near) - 0.02 * push, y: 0.5 - 0.012 * push, z: st, yaw: HYAW, tilt: lean } };
}
function helperFeet(root) { for (const [S, s] of [['R', 1], ['L', -1]]) {               // knees on the floor beside him, shins flat behind, tops of the feet down
  const r = rightOf(HYAW), f = fwdOf(HYAW), hipJ = wp(Hm.bones['thigh' + S]);
  const knee = V(hipJ.x + 0.06, 0.07, root.z + s * 0.11);
  const ankle = knee.clone().addScaledVector(f, -0.4).add(V(0, 0.03, 0)).addScaledVector(r, s * 0.02);
  RH.foot(S, ankle, knee.clone().addScaledVector(f, 0.6).add(V(0, 0.15, 0)), qAA(V(0, 0, 1), 180).multiply(yawQ(HYAW)).multiply(qAA(V(1, 0, 0), -20))); } }
const CUT7 = 0.5;                                               // beat 7: x-ray pushes, then the cut to the AED shock
const SHOCK = 0.72;                                             // beat 7: when the shock goes (fraction of the beat)
function guyState(t) {
  const b = beatAt(t), lt = t - B[b], u = lt / DUR[b];
  if (b === 9) return { ...standingGuy(t, lt + 0.2, 0, 0), hands: [mugHand(lt + 0.2)], face: { smile: 0.35, blink: blinkAt(lt) }, heart: 'beat', mugIn: true };
  if (b === 0) { const stopped = smooth(STOP0, STOP0 + 0.6, lt), buck = smooth(BUCK, DUR[0], lt), drop = smooth(DROP, DROP + 0.5, lt);
    const st = standingGuy(t, DUR[9] + 0.2 + lt, buck, stopped);
    return { ...st, hands: lt < DROP ? [mugHand(DUR[9] + 0.2 + lt, true)] : [], dropArm: drop, face: { blink: 0.25 + 0.5 * stopped, jaw: 0.25 * stopped, look: [0, 0.35 * stopped], fear: 0.2 * stopped }, heart: lt < STOP0 ? 'beat' : lt < STOP0 + 0.6 ? 'quiver' : 'still', mugIn: lt < DROP }; }
  if (b === 1) { if (lt < FALL0) return { ...standingGuy(t, 0, 1, 1), hands: [], face: { blink: 0.8, jaw: 0.3 }, heart: 'still' };
    return { ...fallGuy(lt - FALL0), hands: [], face: { blink: 0.85, jaw: 0.35 }, heart: 'still' }; }
  if (b === 2) { const gs = Math.max(0, Math.sin((lt - 0.3) * Math.PI / 1.1)) ** 2 * (lt > 0.3 ? 1 : 0); return { ...lyingGuy(t, { gasp: gs }), hands: [], face: { blink: 0.9, jaw: 0.25 + 0.6 * gs, oh: 0.3 * gs }, heart: 'still' }; }
  if (b === 3) return { show: false };
  if (b === 4) return { ...lyingGuy(t), hands: [], face: { blink: 0.92, jaw: 0.25 }, heart: 'still' };
  if (b === 5 || b === 6) return { ...lyingGuy(t, { lift: 0.035 }), hands: [], face: { blink: 0.92, jaw: 0.25 }, heart: 'still' };
  if (b === 7) { const j = u > SHOCK ? Math.exp(-(lt - SHOCK * DUR[7]) * 9) * Math.sin(Math.min(Math.PI, (lt - SHOCK * DUR[7]) * 20)) : 0;
    return { ...lyingGuy(t, { jolt: j, lift: u < CUT7 ? 0.035 : 0 }), hands: [], face: { blink: 0.92, jaw: 0.25 }, heart: u > SHOCK + 0.08 ? 'beat' : 'pumped' }; }
  if (b === 8) { const wake = smooth(0.0, 0.3, u); return { ...lyingGuy(t, { breathe: 0.5 + 0.5 * Math.sin(lt * 3.2), turn: smooth(0.2, 0.5, u) }), hands: [], face: { blink: lerp(0.9, blinkAt(lt), wake), jaw: 0.15, look: [-0.3 * smooth(0.2, 0.5, u), 0.1] }, heart: 'beat' }; }
  return { show: false };
}
const PUSH_HZ = 110 / 60;
function pushAt(b, lt) { if (b === 6 || (b === 7 && lt / DUR[7] < CUT7) || (b === 5 && lt / DUR[5] > 0.92)) { const ph = (b === 6 ? lt : b === 7 ? DUR[6] + lt : 0) * PUSH_HZ; return b === 5 ? 0 : Math.pow(Math.max(0, Math.sin(Math.PI * (ph % 1))), 1.5); } return 0; }
function helperState(t) {
  const b = beatAt(t), lt = t - B[b], u = lt / DUR[b];
  if (!(b >= 5 && b <= 8)) return { show: false };
  const push = pushAt(b, lt);
  const st = helperAt(b, lt, push);
  let hands = [], face = { browIn: 0.6, fear: 0.3, blink: blinkAt(lt + 1), jaw: 0.1 };
  const S0 = sternum(), up = V(0, 1, 0), across = V(1, 0, 0);
  const chestR = { S: 'R', p: S0.clone().add(V(0, 0.012, 0)), n: up.clone().negate().addScaledVector(across, 0.3).normalize(), u: across.clone().add(V(0, 0.22, -0.2)).normalize(), c: -12, th: 10, seed: A(55, 10, 10, 8, 30) };
  const chestL = { S: 'L', p: S0.clone().add(V(0.035, 0.05, 0.005)), n: up.clone().negate(), u: across.clone().add(V(0, 0, 0.15)).normalize(), c: 60, th: 20, seed: A(55, 10, -10, 8, 30) };
  const shoulder = () => { const sh = wp(G.bones.uarmR).add(V(-0.02, 0.075, 0.03)); return { S: 'L', p: sh, n: V(-0.4, -1, 0).normalize(), u: V(0.75, 0, -0.65).normalize(), c: 4, seed: A(60, 15, 0, 40, 20) }; };   // his right shoulder, with her left hand
  const restR = () => ({ S: 'R', p: wp(Hm.bones.hips).addScaledVector(fwdOf(HYAW), 0.25).addScaledVector(rightOf(HYAW), 0.18).add(V(0, 0.02, 0)), n: V(0, -1, 0), u: fwdOf(HYAW), c: 30, seed: A(40, 15, 0, 60, 30) });
  if (b === 5) { const k = smooth(0.55, 0.9, u); const sh = shoulder(), r0 = restR(); const shake = 0.015 * Math.sin(lt * 14) * (1 - smooth(0.4, 0.55, u));
    hands = [{ ...sh, p: sh.p.clone().lerp(chestL.p, k).add(V(0, 0.06 * Math.sin(Math.PI * k), shake)), n: sh.n.clone().lerp(chestL.n, k).normalize(), u: sh.u.clone().lerp(chestL.u, k).normalize(), c: lerp(4, 55, k) },
             { ...r0, p: r0.p.clone().lerp(chestR.p, k).add(V(0, 0.08 * Math.sin(Math.PI * k), 0)), u: r0.u.clone().lerp(chestR.u, k).normalize(), c: lerp(30, -12, k) }];
    face = { browIn: 0.7, fear: 0.6, jaw: 0.35 + 0.25 * Math.max(0, Math.sin(lt * 6)) * (1 - k), blink: 0 }; }
  else if (b === 6 || (b === 7 && u < CUT7)) { hands = [chestR, chestL]; face = { browIn: 0.6, fear: 0.2, jaw: 0.2 + 0.15 * push, blink: 0, squint: 0.2 }; }
  else if (b === 7) { const clr = smooth(CUT7, CUT7 + 0.08, u); st.pose.armR = A(lerp(55, 45, clr), lerp(30, 55, clr), 0, 95, -40); st.pose.armL = A(lerp(55, 45, clr), lerp(30, 55, clr), 0, 95, -40); curl(st.pose, 'R', 6); curl(st.pose, 'L', 6);
    face = { browIn: 0.5, fear: 0.5, jaw: 0.4, blink: 0 }; }
  else if (b === 8) { hands = [shoulder()]; st.pose.armR = A(-5, 22, 0, 75, 30); face = { smile: 0.6 * smooth(0.25, 0.5, u), browIn: 0.3, blink: blinkAt(lt), jaw: 0.1 }; }
  return { ...st, hands, face, push, show: true };
}

// ------------------------------------------------------------------ cameras
function shakeV(t, a) { return V(vn1(t * 14, 1) * a * 0.5, vn1(t * 14, 2) * a, vn1(t * 14, 3) * a); }
function camAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b], u = lt / d;
  const chestW = wp(G.bones.chest);
  if (b === 9 || b === 0) {                                     // beat 9 pushes in to his chest; beat 0 pulls back from it
    const k = b === 9 ? 1 - smooth(DUR[9] - 1.1, DUR[9], lt) : smooth(0.75, 2.0, lt);   // 1 = medium shot, 0 = on his chest
    const near = { p: V(0.05, 1.32, 1.65), t: V(0.03, 1.3, 0.55) }, far = { p: V(0.55, 1.35, 3.2), t: V(-0.05, 1.0, 0.4) };
    return { pos: near.p.clone().lerp(far.p, k), tgt: near.t.clone().lerp(far.t, k), fov: lerp(40, 46, k) }; }
  if (b === 1) { const k = smooth(0.4, 0.9, u); return { pos: V(lerp(2.5, 1.35, k), lerp(1.05, 0.95, k), lerp(0.55, -0.05, k)), tgt: V(0, lerp(0.75 - 0.4 * smooth(0.1, 0.5, u), 0.2, k), lerp(0.2, -0.25, k)), fov: 52 }; }
  if (b === 2) { const h = wp(G.bones.head); return { pos: h.clone().add(V(0.38, 0.62 - 0.06 * u, 0.3)), tgt: h.clone().add(V(0, 0.02, 0.1)), fov: 42 }; }
  if (b === 3) return { pos: NEUR.clone().add(V(0.3 * Math.sin(u * 2), 0.1, 3.2 - 2.2 * u)), tgt: NEUR.clone().add(V(0, 0, -4)), fov: 50 };
  if (b === 4) return { pos: V(1.7 - 0.2 * u, 2.3, 2.6 - 0.2 * u), tgt: V(-0.1, 0.9, -1.3), fov: 50 };
  if (b === 5) return { pos: V(1.15 - 0.1 * u, 1.05, 0.35), tgt: V(-0.25, 0.48, -0.25), fov: 48 };
  if (b === 6) return { pos: V(0.95 - 0.1 * u, 0.82, 0.5 - 0.05 * u), tgt: V(-0.15, 0.42, -0.2), fov: 46 };
  if (b === 7) { if (u < CUT7) return { pos: V(0.75, 1.15, 0.1), tgt: V(-0.05, 0.28, -0.35), fov: 46 };
    const shk = u > SHOCK ? 0.04 * Math.exp(-(lt - SHOCK * d) * 6) : 0; return { pos: V(0.95, 1.55, 1.25).add(shakeV(t, shk)), tgt: V(-0.12, 0.25, -0.3), fov: 48 }; }
  if (b === 8) return { pos: V(0.95, 1.05 - 0.08 * u, -0.6), tgt: V(-0.2, 0.28, -0.4), fov: 46 };
  return { pos: V(0, 1.5, 3), tgt: V(0, 1, 0), fov: 45 };
}

// ------------------------------------------------------------------ clipping: both bodies vs the room, the floor, each other, and their own bodies
const SOLIDS = [];
const sbox = (name, obj, min, max) => SOLIDS.push({ name, obj, box: new THREE.Box3(min, max) });
sbox('couch', couch, V(-1.1, 0, -0.45), V(1.1, 0.98, 0.45)); sbox('coffee table', table, V(-0.55, 0, -0.3), V(0.55, 0.45, 0.3)); sbox('counter', counter, V(-0.33, 0, -1.5), V(0.33, 0.95, 2.35));
sbox('aed', aed, V(-0.16, 0, -0.13), V(0.16, 0.11, 0.13));
const BODYPTS = { handR: 0.035, handL: 0.035, farmR: 0.035, farmL: 0.035, uarmR: 0.045, uarmL: 0.045, head: 0.09, chest: 0.12, hips: 0.1, shinR: 0.05, shinL: 0.05, footR: 0.04, footL: 0.04 };
function segDist(p, a, b) { const ab = b.clone().sub(a), t = clamp(p.clone().sub(a).dot(ab) / ab.lengthSq(), 0, 1); return p.distanceTo(a.clone().addScaledVector(ab, t)); }
const trunkDist = (Gx, p) => { const h = wp(Gx.bones.hips), c = wp(Gx.bones.chest), n = wp(Gx.bones.neck); return Math.min(segDist(p, h, c), segDist(p, c, n)); };
function clipOne(R, other, out, who) {
  const Gx = R.G; if (!Gx.root.visible) return;
  const pts = Object.entries(BODYPTS).map(([n, r]) => [n, wp(Gx.bones[n]), r]);
  for (const S of ['R', 'L']) for (const f of ['index', 'middle', 'pinky', 'thumb']) pts.push([f + ' tip ' + S, R.tip(f, S), 0.008]);
  const headC = wp(Gx.bones.head).add(V(0, 0.09, 0).applyQuaternion(wq(Gx.bones.head)));
  for (const [n, p, r] of pts) {
    if (p.y - r < -0.015) out.push({ what: who + ' ' + n, into: 'floor', depth: +((-(p.y - r)) * 100).toFixed(1) });
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
function clipScan() { const out = []; scene.updateMatrixWorld(true); clipOne(RG, RH, out, 'him'); clipOne(RH, RG, out, 'helper');
  if (mug.visible && G.root.visible && guyCache && guyCache.mugIn) { const dT = trunkDist(G, mug.position) - 0.11 - 0.04; if (dT < -0.012) out.push({ what: 'mug', into: 'his body', depth: +(-dT * 100).toFixed(1) }); }
  return out; }

// ------------------------------------------------------------------ per-frame update
let LASTF = -10, guyCache = null, DROPP = null;
function update(t, frame) {
  t = ((t % TOTAL) + TOTAL) % TOTAL;
  const b = beatAt(t), lt = t - B[b], d = DUR[b], u = lt / d;
  // ---- him
  const g = guyState(t); guyCache = g;
  G.root.visible = g.show !== false;
  if (G.root.visible) {
    RG.applyPose(g.pose, g.root);
    const push = pushAt(b, lt); compress(0.042 * push * (b >= 5 ? 1 : 0)); G.root.updateMatrixWorld(true);
    if (g.feet === 'stand') for (const [S, sx] of [['R', 0.11], ['L', -0.11]]) { const f = P0.clone().addScaledVector(rightOf(YAW), sx).add(V(0, 0.102, 0)); RG.foot(S, f, f.clone().add(V(0, 0.45, 0)).addScaledVector(fwdOf(YAW), 1), yawQ(YAW)); }
    else if (g.feet) for (const [S, sx] of [['R', 0.12], ['L', -0.12]]) { const f = V(sx * (g.feet === 'lie' ? -1 : -1), g.footY, g.footZ); f.x = -sx;
      RG.foot(S, f, f.clone().add(V(0, 0.6 * (g.kneeUp ?? 0) + 0.25, 0)).add(V(0, 0, 0.4 * (g.kneeUp ?? 0))), g.footQ); }
    G.root.updateMatrixWorld(true);
    RG.hands(g.hands, 'b' + b, frame); if (!g.hands.length) { delete RG.LAST.costR; delete RG.LAST.costL; }
    if (g.dropArm !== undefined && !g.hands.length) { const a = (RG.MEM['b0R'] || {}).a || A(35, 15, -20, 95, 60); const k = g.dropArm; const hang = [6, 8, 0, 16, 0, 0, 0], arm = a.map((v, i) => lerp(v, hang[i], k)); RG.setArm('R', arm); RG.LAST.armR = arm; }
    G.root.updateMatrixWorld(true); RG.untwist(); G.face(g.face); G.root.updateMatrixWorld(true);
  }
  // ---- the helper
  const h = helperState(t); Hm.root.visible = h.show;
  if (h.show) { RH.applyPose(h.pose, h.root); helperFeet(h.root); Hm.root.updateMatrixWorld(true);
    RH.hands(h.hands, 'h' + b + (b === 7 ? (u < CUT7 ? 'a' : 'b') : ''), frame); if (!h.hands.length) { delete RH.LAST.costR; delete RH.LAST.costL; }
    Hm.root.updateMatrixWorld(true); RH.untwist(); Hm.face(h.face); Hm.root.updateMatrixWorld(true); }
  // ---- x-ray, the heart, blood, the brain's color
  const xk = b === 9 ? smooth(DUR[9] - 0.9, DUR[9] - 0.3, lt) : b === 0 ? 1 - smooth(0.85, 1.35, lt) : b === 1 ? smooth(0.0, 0.25, lt) : b === 7 && u < CUT7 ? 1 : 0;
  setXray(G.root.visible ? xk : 0); clock.visible = !(G.root.visible && xk > 0.3);     // the wall clock would glow through him
  const beatPh = t * 1.25, hb = Math.exp(-Math.pow(((beatPh % 1) - 0.1) / 0.06, 2)) + 0.5 * Math.exp(-Math.pow(((beatPh % 1) - 0.28) / 0.06, 2));
  const hs = g.heart === 'beat' ? 1 + 0.16 * hb : g.heart === 'quiver' ? 1 + 0.02 * Math.sin(t * 90) : g.heart === 'pumped' ? 1 - 0.18 * pushAt(b, lt) : 1;
  heart.scale.setScalar(hs); heartM.emissiveIntensity = g.heart === 'still' ? 0.25 : g.heart === 'quiver' ? 0.5 : 0.9 + 0.6 * (g.heart === 'beat' ? hb : pushAt(b, lt));
  const oxy = b === 9 || (b === 0 && lt < STOP0) ? 1 : b === 0 ? 1 - 0.3 * smooth(STOP0, DUR[0], lt) : b === 1 ? 0.7 - 0.6 * smooth(0.3, DUR[1] - 0.5, lt) : b === 7 ? 0.25 + 0.4 * smooth(0, CUT7 * DUR[7], lt) : 0.1;
  brainM.emissive.setRGB(lerp(0.25, 1.0, oxy), lerp(0.3, 0.45, oxy), lerp(0.45, 0.62, oxy)); brainM.emissiveIntensity = 0.35 + 0.7 * oxy;
  lungs.scale.setScalar(1 + (g.heart === 'beat' ? 0.03 * Math.sin(t * 2.2) : 0));
  if (vessel.visible) { const a = wp(heart).add(V(0, 0.04, 0).applyQuaternion(wq(G.bones.chest))), c = wp(brain).add(V(0, -0.05, 0.02).applyQuaternion(wq(G.bones.head)));
    vessel.position.copy(a).lerp(c, 0.5); vessel.scale.set(1, a.distanceTo(c), 1); vessel.quaternion.setFromUnitVectors(V(0, 1, 0), c.clone().sub(a).normalize());
    const flow = g.heart === 'beat' ? 1 : g.heart === 'pumped' ? 0.6 : 0, spd = g.heart === 'beat' ? 0.9 : 0.5;
    const pp = bloodPts.p; for (let i = 0; i < 120; i++) { const s = ((i / 120) + (b === 1 ? (FALL0 * spd) * (1 - smooth(0, 0.4, lt)) : t * spd * flow)) % 1, q = a.clone().lerp(c, s); q.add(V((hash1(i) - 0.5) * 0.01, (hash1(i * 3) - 0.5) * 0.01, (hash1(i * 7) - 0.5) * 0.01)); pp.set([q.x, q.y, q.z], i * 3); }
    bloodPts.m.geometry.attributes.position.needsUpdate = true; bloodPts.m.material.opacity = 0.25 + 0.75 * (flow > 0 ? 1 : b === 1 ? 1 - smooth(0, 1.2, lt) : 0.15); }
  // ---- the mug: in his hand, then it slips (beat 0), breaks, and the pieces lie by his feet
  const inHand = g.mugIn && G.root.visible; mug.visible = b === 9 || b === 0 || b === 1 || b === 2 || b === 4 || b === 5 || b === 6 || b === 7 || b === 8;
  if (inHand) { const hbn = G.bones.handR, q = wq(hbn), n = RG.HANDREST.R.n.clone().applyQuaternion(q), pc = RG.palmW('R');
    mug.position.copy(pc).addScaledVector(n, 0.05); mug.rotation.set(-0.7 * (b === 9 ? sipAt(lt + 0.2) : 0), Math.PI / 2, 0); DROPP = mug.position.clone(); }
  const fallT = b === 0 ? lt - DROP : b >= 1 && b <= 8 ? 9 : -1, FLOORT = 0.42;
  if (!inHand && fallT >= 0) { const p0 = DROPP || V(-0.12, 1.15, 0.86), ft = Math.min(fallT, FLOORT);
    mug.position.copy(p0).add(V(0.05 * ft, -4.9 * ft * ft * (0.8 / (4.9 * FLOORT * FLOORT)) * 1.3, 0.12 * ft)); mug.rotation.set(2.5 * ft, Math.PI / 2, 1.5 * ft); mug.visible = fallT < FLOORT; }
  shards.visible = puddle.visible = fallT >= FLOORT; if (shards.visible) { const base = (DROPP || V(-0.12, 1.15, 0.86)).clone().setY(0.0), a = Math.min(fallT - FLOORT, 0.5), m4 = new THREE.Matrix4();
    for (let i = 0; i < 14; i++) { const th = hash1(i * 3) * 6.283, r = (0.05 + 0.3 * hash1(i * 5)) * (1 - Math.exp(-a * 8)); const y = Math.max(0.01, 0.12 * Math.sin(Math.min(Math.PI, a * 9)) * hash1(i * 7));
      m4.compose(base.clone().add(V(0.05 + Math.cos(th) * r, y, 0.15 + Math.sin(th) * r)), new THREE.Quaternion().setFromEuler(new THREE.Euler(i, i * 2, a * 6)), V(1, 1, 1).multiplyScalar(0.6 + hash1(i * 9))); shards.setMatrixAt(i, m4); }
    shards.instanceMatrix.needsUpdate = true; puddle.position.set(base.x + 0.05, 0.006, base.z + 0.15); puddle.scale.setScalar(0.2 + 0.8 * smooth(0, 0.6, fallT - FLOORT)); }
  { const sp = fallT - FLOORT; drops.m.visible = sp > 0 && sp < 0.5; if (drops.m.visible) { const base = (DROPP || V(0, 0, 0)).clone().setY(0); for (let i = 0; i < 60; i++) { const th = hash1(i * 11) * 6.283, v = 0.6 + hash1(i * 13); drops.p.set([base.x + 0.05 + Math.cos(th) * v * sp, Math.max(0.005, 0.02 + 1.6 * sp * hash1(i * 17) - 4.9 * sp * sp), base.z + 0.15 + Math.sin(th) * v * sp], i * 3); } drops.m.geometry.attributes.position.needsUpdate = true; } }
  // ---- the AED and the shock (beat 7, after the cut; it stays in beat 8)
  const aedOn = (b === 7 && u >= CUT7) || b === 8; aed.visible = aedOn; pads.forEach(p => p.visible = aedOn); wires.forEach(w => w.visible = aedOn);
  if (aedOn) { aed.position.set(0.48, 0, -0.55); aed.rotation.y = 0.3;
    const up = V(0, 0, -1).applyQuaternion(wq(G.bones.chest)), c = wp(G.bones.chest);
    const spots = [c.clone().add(V(-0.08, 0, -0.1)).addScaledVector(up, 0.128), c.clone().add(V(0.12, 0, 0.06)).addScaledVector(up, 0.1).add(V(0.03, -0.035, 0))];
    spots.forEach((s, i) => { pads[i].position.copy(s); pads[i].quaternion.setFromUnitVectors(V(0, 1, 0), i ? V(0.5, 1, 0).normalize() : up); pads[i].rotateY(i ? 0.3 : -0.4);
      const a2 = aed.position.clone().add(V(-0.1, 0.1, 0.05)), w = wires[i]; w.position.copy(a2).lerp(s, 0.5); w.scale.set(1, a2.distanceTo(s), 1); w.quaternion.setFromUnitVectors(V(0, 1, 0), s.clone().sub(a2).normalize()); });
    const sk = b === 7 ? Math.max(0, 1 - Math.abs(lt - SHOCK * d) / 0.08) : 0; zap.position.copy(c).add(V(0, 0.3, 0)); zap.intensity = 25 * sk;
    aed.getObjectByName('btn').material.emissiveIntensity = b === 7 ? 1.5 * (0.5 + 0.5 * Math.sin(lt * 18)) * (u < SHOCK ? 1 : 0.2) : 0; } else zap.intensity = 0;
  // ---- the clock: time runs in beat 4 (8 to 10 minutes)
  { const mins = b <= 0 || b === 9 ? 0.1 + t / 60 : b === 4 ? lerp(1.5, 10.5, smooth(0, 1, u)) : b < 4 ? 1.2 + (t - B[1]) / 20 : 11 + (t - B[5]) / 30;
    clockHands.m.rotation.z = -mins / 60 * Math.PI * 2; clockHands.h.rotation.z = -(10 + mins / 60) / 12 * Math.PI * 2; clockHands.s.rotation.z = -mins * Math.PI * 2; }
  // ---- the brain cells (beat 3): bright, firing, then going dark one by one
  neur.visible = b === 3; home.visible = b !== 3;
  if (b === 3) { for (const n of NEURONS) { const off = smooth(n.t0, n.t0 + 0.12, u); const fl = off > 0 && off < 1 ? (Math.sin(t * 60 + n.t0 * 50) > 0 ? 1 : 0.3) : 1;
      n.m.emissive.setRGB(lerp(1.0, 0.15, off), lerp(0.35, 0.15, off), lerp(0.7, 0.2, off)); n.m.emissiveIntensity = lerp(2.0, 0.15, off) * fl; n.g.rotation.y = 0.2 * Math.sin(t * 0.3 + n.t0 * 9); }
    for (let i = 0; i < 300; i++) { const n = NEURONS[i % NEURONS.length], a = ((t * 0.8 + hash1(i)) % 1); const alive = u < n.t0;
      const q = n.g.position.clone().add(V(Math.cos(i) * a * 0.9, Math.sin(i * 1.7) * a * 0.9, Math.sin(i * 2.3) * a * 0.9)); sparks.p.set(alive ? [NEUR.x + q.x, NEUR.y + q.y, NEUR.z + q.z] : [0, -999, 0], i * 3); }
    sparks.m.geometry.attributes.position.needsUpdate = true; } sparks.m.visible = b === 3;
  // ---- camera and light
  const C = camAt(t); camera.position.copy(C.pos); camera.up.set(0, 1, 0); camera.lookAt(C.tgt); camera.fov = C.fov; camera.updateProjectionMatrix();
  scene.background = b === 3 ? new THREE.Color(0x07091a) : new THREE.Color(0xd9cbb6);
  const sweep = b === 4 ? u : 0;                                 // beat 4: the window light swings as time passes
  sun.position.set(1.6 - 1.5 * sweep, 3.4 - 0.6 * sweep, -1.2 + 3.6); sun.target.position.set(0, 0, 0); sun.target.updateMatrixWorld();
  const dim = 1 - 0.78 * (G.root.visible ? xk : 0);            // the room goes dim while we look through him, so the glow reads
  sun.intensity = b === 3 ? 0 : (2.6 - 0.6 * sweep) * dim; hemi.intensity = b === 3 ? 0.1 : 0.85 * dim; scene.environmentIntensity = 0.35 * dim; lamp.intensity = 6 * dim;
  scene.background = b === 3 ? new THREE.Color(0x07091a) : new THREE.Color(0xd9cbb6).multiplyScalar(dim);
  return { beat: b, cut: (b === 7 && Math.abs(u - CUT7) * d * FPS < 0.999 && u >= CUT7) };
}

// ------------------------------------------------------------------ frame I/O (same contract as the other 3D Shorts)
const draw = () => renderer.render(scene, camera);
const gl = renderer.getContext(), px = new Uint8Array(W * H * 4);
let CUTF = false, LASTB = 0;
function stepTo(i) { const t = i / FPS, b = beatAt(((t % TOTAL) + TOTAL) % TOTAL);
  if (i !== LASTF + 1) for (let j = Math.max(Math.round(B[b] * FPS), i - 12); j < i; j++) update(j / FPS, j);
  const r = update(t, i); CUTF = r.cut; LASTB = r.beat; LASTF = i; }
// warm the loop: solve beat 9's mug hold once so beat 0 picks up the same arm
{ const f0 = Math.round(B[9] * FPS), f1 = Math.round(TOTAL * FPS); for (let i = f0; i < f1; i++) update(i / FPS, i); LOOPSEED = RG.MEM['b9R'].a.slice(); RG.MEM['b0R'] = { frame: -5, a: LOOPSEED.slice() }; LASTF = -10; }
window.renderAll = async (f0, f1) => { for (let i = f0; i < f1; i++) { stepTo(i); draw(); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); await fetch('/frame', { method: 'POST', body: px }); } return 'ok'; };
window.renderAtT = t => { const i = Math.round(t * FPS); stepTo(i);
  if (window.CAM && window.CAM.hand) { const R = window.CAM.who === 'helper' ? RH : RG, hp = R.palmW(window.CAM.hand); window.CAM.tgt = hp.toArray(); window.CAM.pos = hp.clone().add(V(...window.CAM.off)).toArray(); }
  if (window.CAM) { camera.position.set(...window.CAM.pos); camera.up.set(0, 1, 0); camera.lookAt(...window.CAM.tgt); camera.fov = window.CAM.fov || 42; camera.updateProjectionMatrix(); }
  draw(); return renderer.domElement.toDataURL('image/png'); };
window.rigReport = i => { stepTo(i); const t = i / FPS, iq = G.root.getWorldQuaternion(new THREE.Quaternion()).invert();
  const ang = { ...RG.LAST }; if (Hm.root.visible) for (const [k, v] of Object.entries(RH.LAST)) if (Array.isArray(v)) ang['H.' + k] = v; delete ang.costR; delete ang.costL;
  const cost = [Math.max(RG.LAST.costR ?? -1, Hm.root.visible ? RH.LAST.costR ?? -1 : -1), Math.max(RG.LAST.costL ?? -1, Hm.root.visible ? RH.LAST.costL ?? -1 : -1)].map(c => c < 0 ? null : c);
  return { t, beat: LASTB, ang, hips: wp(G.bones.hips).toArray(), car: 0, show: G.root.visible || Hm.root.visible, cut: CUTF,
    thumbs: ['R', 'L'].map(S => wp(G.bones['index1' + S]).sub(wp(G.bones['pinky1' + S])).applyQuaternion(iq).toArray()),
    forearms: ['R', 'L'].map(S => wp(G.bones['hand' + S]).sub(wp(G.bones['farm' + S])).normalize().applyQuaternion(iq).toArray()),
    cost, clip: clipScan() }; };
window.dbg = { G, Hm, RG, RH, wp, sternum, THREE, hh: (i, k) => { stepTo(i); const h = helperState(i / FPS).hands[k]; const f = RH.handFK(h.S, RH.LAST['arm' + h.S]); return { S: h.S, d: +f.p.distanceTo(h.p).toFixed(3), n: +f.n.dot(h.n).toFixed(2), u: h.u ? +f.u.dot(h.u).toFixed(2) : null, a: RH.LAST['arm' + h.S].map(Math.round), sh: wp(Hm.bones.uarmL).toArray().map(v => +v.toFixed(2)), tg: h.p.toArray().map(v => +v.toFixed(2)) }; } };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS);
window.READY = true;
