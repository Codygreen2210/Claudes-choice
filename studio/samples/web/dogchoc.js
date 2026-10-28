// "Your dog just ate chocolate. Here's what you do." - a 3D Short with a golden retriever built from shapes and the sculpted guy as his owner.
//   dogchoc.html?w=1080&h=1920            (times from dogchoc/times.json; one shot per narration line)
// Beats: 0 he's chewing a dark chocolate bar on the floor, tail wagging; his owner freezes in the back (hook) | 1 x-ray: the poison spreads, his body clears it slowly
//        2 x-ray: his heart races; cut: on his side, shaking (seizure) | 3 six to twelve hours: he looks fine on his bed, the clock runs
//        4 the lineup: baking, dark, milk, white, with danger bars | 5 one large dark bar next to a big golden | 6 the owner: wrapper in hand, phone at his ear
//        7 kneeling by him, a hand on his back (don't make him throw up) | 8 Halloween: nose in the candy bowl | 9 before: he sniffs the bar, dips to eat (loops)
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { loadGuy } from '/guy3d.js';

const Q = new URLSearchParams(location.search);
const W = +Q.get('w') || 720, H = +Q.get('h') || 1280;
const FPS = 30;
const TIMES = await (await fetch('/dogchoc/times.json')).json();
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
const GLSLN = `float hh(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); } float vn(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f*f*(3.0-2.0*f); return mix(mix(hh(i), hh(i+vec2(1,0)), u.x), mix(hh(i+vec2(0,1)), hh(i+vec2(1,1)), u.x), u.y); }`;

// ------------------------------------------------------------------ chocolate: a bar (bitten on the floor), the wrapper, crumbs; Halloween candy corner
const chocTex = canvasTex(256, 128, g => { g.fillStyle = '#3b2216'; g.fillRect(0, 0, 256, 128); for (let i = 0; i < 4; i++) for (let j = 0; j < 2; j++) { g.fillStyle = '#4a2c1c'; g.fillRect(8 + i * 62, 8 + j * 58, 54, 52); g.fillStyle = '#2c180f'; g.fillRect(8 + i * 62, 56 + j * 58, 54, 4); } });
function chocBar(color = 0x3b2216, bitten = false) { const g = new THREE.Group();
  const m = new THREE.MeshStandardMaterial({ color, map: color === 0x3b2216 ? chocTex : null, roughness: 0.45 });
  const L = bitten ? 0.1 : 0.16; const b = new THREE.Mesh(new THREE.BoxGeometry(L, 0.012, 0.07), m); b.position.set(bitten ? -0.03 : 0, 0.006, 0); b.castShadow = true; g.add(b);
  if (bitten) for (let i = 0; i < 4; i++) { const c = new THREE.Mesh(new THREE.DodecahedronGeometry(0.008 + 0.006 * hash1(i), 0), m); c.position.set(0.03 + 0.05 * hash1(i * 3), 0.006, -0.05 + 0.1 * hash1(i * 5)); g.add(c); }
  return g; }
const floorBar = chocBar(0x3b2216, true); scene.add(floorBar);
const wrapperTex = canvasTex(256, 128, g => { g.fillStyle = '#7a1e2a'; g.fillRect(0, 0, 256, 128); g.fillStyle = '#f1d27a'; g.fillRect(0, 50, 256, 28); g.fillStyle = '#2a120c'; g.font = 'bold 26px Arial'; g.fillText('DARK 70%', 60, 74); });
const wrapperFloor = new THREE.Mesh(new THREE.PlaneGeometry(0.2, 0.09), new THREE.MeshStandardMaterial({ map: wrapperTex, roughness: 0.4, metalness: 0.2, side: THREE.DoubleSide })); wrapperFloor.rotation.x = -Math.PI / 2; wrapperFloor.rotation.z = 0.5; scene.add(wrapperFloor);
const wrapperHand = new THREE.Mesh(new THREE.PlaneGeometry(0.16, 0.075), wrapperFloor.material); scene.add(wrapperHand);
const phone = new THREE.Group(); scene.add(phone);
{ box(0.072, 0.152, 0.009, 0, 0, 0, mat(0x1c1d22, 0.3, 0.6), 0.004, phone); const s = new THREE.Mesh(new THREE.PlaneGeometry(0.064, 0.142), new THREE.MeshBasicMaterial({ color: 0x2a6a3a, toneMapped: false })); s.position.z = 0.0048; phone.add(s); }
const dogBed = new THREE.Group(); dogBed.position.set(-0.55, 0, 0.75); scene.add(dogBed);
{ const r = new THREE.Mesh(new THREE.TorusGeometry(0.38, 0.1, 14, 32).rotateX(Math.PI / 2), mat(0x7a5a8a, 0.95)); r.position.y = 0.1; r.scale.set(1, 1, 0.8); r.castShadow = true; dogBed.add(r);
  const c = new THREE.Mesh(new THREE.CylinderGeometry(0.34, 0.34, 0.06, 32), mat(0x9a7aa8, 0.95)); c.scale.set(1, 1, 0.8); c.position.y = 0.04; dogBed.add(c); }
const halloween = new THREE.Group(); halloween.position.set(-0.9, 0, 0.3); scene.add(halloween);
{ const bowl = new THREE.Mesh(new THREE.SphereGeometry(0.2, 32, 16, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0xff7a1a, roughness: 0.5, side: THREE.DoubleSide })); bowl.position.y = 0.2; halloween.add(bowl);
  const cols = [0xd82a2a, 0xf2c230, 0x3a2216, 0x6a2ab0, 0xf28a1a, 0x2a8ad8];
  for (let i = 0; i < 26; i++) { const a = hash1(i * 3) * 6.28, r = 0.15 * Math.sqrt(hash1(i * 5)); const c = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.02, 0.025), mat(cols[i % 6], 0.4)); c.position.set(Math.cos(a) * r, 0.16 + 0.045 * hash1(i * 7), Math.sin(a) * r); c.rotation.set(hash1(i) * 3, hash1(i * 2) * 3, 0); halloween.add(c); }
  for (const [x, z, s] of [[0.45, -0.1, 1], [-0.4, 0.15, 0.8], [0.3, 0.35, 0.65]]) { const p = new THREE.Group(); p.position.set(x, 0, z); p.scale.setScalar(s); halloween.add(p);
    const body = new THREE.Mesh(new THREE.SphereGeometry(0.16, 24, 16), mat(0xf07a1a, 0.6)); body.scale.set(1.15, 0.85, 1.15); body.position.y = 0.14; body.castShadow = true; p.add(body);
    const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.025, 0.06, 8), mat(0x3a5a22, 0.8)); stem.position.y = 0.29; p.add(stem);
    for (const ex of [-0.05, 0.05]) { const e = new THREE.Mesh(new THREE.ConeGeometry(0.025, 0.035, 3).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ color: 0xffd060 })); e.position.set(ex, 0.17, 0.175); p.add(e); } }
  for (let i = 0; i < 6; i++) { const w = new THREE.Mesh(new THREE.PlaneGeometry(0.06, 0.03), new THREE.MeshStandardMaterial({ color: cols[i], roughness: 0.4, metalness: 0.3, side: THREE.DoubleSide })); w.rotation.x = -Math.PI / 2; w.rotation.z = i; w.position.set(-0.3 + 0.12 * i, 0.003, 0.3 + 0.1 * hash1(i)); halloween.add(w); } }
const halloweenLight = new THREE.PointLight(0xff8a2a, 0, 3, 1.5); halloweenLight.position.set(-0.9, 0.5, 0.6); scene.add(halloweenLight);

// ------------------------------------------------------------------ the chocolate lineup (beat 4): danger bars by how much of the poison each kind has (mg per ounce, Merck)
const CHOC = V(0, 0, -200);
const chocStage = new THREE.Group(); chocStage.position.copy(CHOC); scene.add(chocStage);
chocStage.add(new THREE.Mesh(new THREE.SphereGeometry(30, 32, 16), new THREE.MeshBasicMaterial({ color: 0x1a1414, side: THREE.BackSide })));
{ const l1 = new THREE.DirectionalLight(0xfff0e0, 2.4); l1.position.set(2, 4, 4); chocStage.add(l1); chocStage.add(l1.target); chocStage.add(new THREE.HemisphereLight(0xffe8d0, 0x302020, 0.6));
  box(3.2, 0.06, 1.0, 0, -0.03, 0, mat(0x2a2222, 0.7), 0, chocStage); }
const LINEUP = [['BAKING', 0x24120b, 440], ['DARK', 0x3b2216, 155], ['MILK', 0x7a4a2a, 64], ['WHITE', 0xf2e8d0, 1.1]].map(([name, col, mg], i) => {
  const x = -0.825 + i * 0.55, g = new THREE.Group(); g.position.set(x, 0, 0); chocStage.add(g);
  const bar = chocBar(col); bar.scale.setScalar(2.1); bar.rotation.y = 0.4; g.add(bar);
  const danger = new THREE.Mesh(new THREE.BoxGeometry(0.28, 1, 0.28), new THREE.MeshStandardMaterial({ color: 0xd8302a, emissive: 0x6a0a06, roughness: 0.5 })); danger.position.set(0, 0, -0.3); g.add(danger);
  const lab = canvasTex(256, 64, c => { c.fillStyle = '#fff'; c.font = 'bold 48px Arial'; c.textAlign = 'center'; c.fillText(name, 128, 48); });
  const lp = new THREE.Mesh(new THREE.PlaneGeometry(0.52, 0.13), new THREE.MeshBasicMaterial({ map: lab, transparent: true })); lp.position.set(0, 0.06, 0.38); lp.rotation.x = -0.6; g.add(lp);
  return { g, danger, mg }; });

// ------------------------------------------------------------------ the dog: a skinned golden retriever (char/dog.py), fur shells, forward = +z
const SPH = new THREE.SphereGeometry(1, 28, 20);
const DOGMESH = [], DOGSKIN = [];
const DOGDATA = await (await fetch('/char/dog.json')).json();
function makeDog() {                                            // the skinned golden retriever from char/dog.py, with fur shells
  const g = new THREE.Group(); scene.add(g); const body = new THREE.Group(); g.add(body);
  const bones = {}, list = [];
  for (const b of DOGDATA.bones) { const bone = new THREE.Bone(); bone.name = b.name; const h = V(...b.head), ph = b.parent ? V(...DOGDATA.bones.find(x => x.name === b.parent).head) : V(0, 0, 0);
    bone.position.copy(h.sub(ph)); bones[b.name] = bone; list.push(bone); (b.parent ? bones[b.parent] : body).add(bone); }
  g.updateMatrixWorld(true);
  const skel = new THREE.Skeleton(list);
  const furU = { uShell: { value: 0 } };
  const furMat = shell => { const m = new THREE.MeshPhysicalMaterial({ vertexColors: true, roughness: 0.85, sheen: 1, sheenRoughness: 0.45, sheenColor: new THREE.Color(0xc08a40) });
    m.onBeforeCompile = sh => { sh.uniforms.uShell = { value: shell };
      sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nuniform float uShell; varying vec3 vRest;')
        .replace('#include <begin_vertex>', '#include <begin_vertex>\nvRest = position;')
        .replace('#include <skinning_vertex>', '#include <skinning_vertex>\ntransformed += normalize(objectNormal) * uShell * 0.007;');
      sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nuniform float uShell; varying vec3 vRest;\nfloat h3(vec3 p){ p = fract(p * 0.3183099 + 0.1); p *= 17.0; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }')
        .replace('#include <color_fragment>', '#include <color_fragment>\n  { vec3 q = vRest * vec3(900.0, 420.0, 900.0); float s = h3(floor(q)); if (uShell > 0.0 && s < 0.2 + 0.75 * uShell) discard;\n    diffuseColor.rgb *= mix(0.8, 1.1, uShell) * (0.92 + 0.16 * h3(floor(vRest * 140.0))); }'); };
    m.customProgramCacheKey = () => 'fur' + shell; return m; };
  for (const md of DOGDATA.meshes) { const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(md.pos, 3)); geo.setAttribute('normal', new THREE.Float32BufferAttribute(md.nrm, 3));
    geo.setAttribute('color', new THREE.Float32BufferAttribute(md.col.map(c => Math.pow(c, 2.2)), 3)); geo.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(md.si, 4)); geo.setAttribute('skinWeight', new THREE.Float32BufferAttribute(md.sw, 4)); geo.setIndex(md.idx);
    const NS = md.name === 'body' ? 6 : 3;
    for (let k = 0; k <= NS; k++) { const m = new THREE.SkinnedMesh(geo, furMat(k / NS)); m.castShadow = k === 0; m.receiveShadow = k === 0; m.frustumCulled = false; body.add(m); m.bind(skel); (k === 0 ? DOGMESH : DOGSKIN).push(m); } }
  const eyeMat = new THREE.MeshStandardMaterial({ color: 0x1a0e08, roughness: 0.08 });
  for (const s of [-1, 1]) { const e = new THREE.Mesh(SPH, eyeMat); e.scale.set(0.016, 0.017, 0.012); e.position.copy(V(s * 0.048, 0.742, 0.5).sub(V(...DOGDATA.bones.find(x => x.name === 'head').head))); bones.head.add(e); DOGMESH.push(e);
    const hl = new THREE.Mesh(SPH, new THREE.MeshBasicMaterial({ color: 0xffffff })); hl.scale.setScalar(0.004); hl.position.copy(e.position).add(V(-s * 0.004, 0.006, 0.01)); bones.head.add(hl); DOGMESH.push(hl); }
  const tongue = new THREE.Mesh(SPH, mat(0xd8607a, 0.5)); tongue.scale.set(0.026, 0.007, 0.055); tongue.position.copy(V(0, 0.662, 0.585).sub(V(...DOGDATA.bones.find(x => x.name === 'jaw').head))); bones.jaw.add(tongue);
  const legs = {}; for (const S of ['R', 'L']) { legs['F' + S] = { hip: bones['F1' + S], knee: bones['F2' + S], paw: bones['F3' + S], back: 0 }; legs['B' + S] = { hip: bones['B1' + S], knee: bones['B2' + S], hock: bones['B3' + S], paw: bones['B4' + S], back: 1 }; }
  return { g, body, bones, neck: bones.neck, head: bones.head, jaw: bones.jaw, tongue, ears: [bones.earR, bones.earL], legs, tail: [1, 2, 3, 4, 5].map(i => bones['t' + i]), skel };
}
const DOG = makeDog();
// his x-ray body and organs: heart, stomach (with chocolate), liver, brain; blood loops; the poison spreading
const dogX = new THREE.MeshStandardMaterial({ color: 0x000000, emissive: 0x58b8ff, emissiveIntensity: 1, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending });
dogX.onBeforeCompile = sh => { sh.fragmentShader = sh.fragmentShader.replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\n  totalEmissiveRadiance *= 0.02 + 0.9 * pow(1.0 - abs(dot(normalize(normal), normalize(vViewPosition))), 2.2);'); };
const DOGX = DOGMESH.filter(o => o.isSkinnedMesh).map(o => { const x = new THREE.SkinnedMesh(o.geometry, dogX); x.frustumCulled = false; x.renderOrder = 5; x.visible = false; DOG.body.add(x); x.bind(DOG.skel, o.bindMatrix); return x; });
const orgM = (c, e, i = 0.9) => new THREE.MeshStandardMaterial({ color: c, emissive: e, emissiveIntensity: i, roughness: 0.45 });
const dHeartM = orgM(0x8a1a1a, 0xff2a2a), dStomM = orgM(0x8a4a5a, 0xff8aa0, 0.5), dLiverM = orgM(0x5a1a1a, 0xb83a2a, 0.6), dBrainM = orgM(0x9a5a7a, 0xff8ab8, 0.7);
const dHeart = new THREE.Mesh(SPH, dHeartM); dHeart.position.set(0.02, 0.43, 0.2); dHeart.scale.set(0.05, 0.065, 0.05); DOG.body.add(dHeart);
const dStom = new THREE.Mesh(SPH, dStomM); dStom.position.set(-0.03, 0.42, 0.02); dStom.scale.set(0.08, 0.07, 0.1); DOG.body.add(dStom);
const dLiver = new THREE.Mesh(SPH, dLiverM); dLiver.position.set(0.03, 0.45, 0.1); dLiver.scale.set(0.1, 0.05, 0.07); DOG.body.add(dLiver);
const dBrain = new THREE.Mesh(SPH, dBrainM); dBrain.position.copy(V(0, 0.735, 0.42).sub(V(...DOGDATA.bones.find(x => x.name === 'head').head))); dBrain.scale.set(0.06, 0.05, 0.07); DOG.head.add(dBrain);
const chunks = []; for (let i = 0; i < 6; i++) { const c = new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.012, 0.03), new THREE.MeshStandardMaterial({ color: 0x3b2216, emissive: 0x4a2a10, emissiveIntensity: 0.6 })); c.position.set(-0.03 + 0.04 * (hash1(i) - 0.5), 0.41 + 0.03 * (hash1(i * 3) - 0.5), 0.02 + 0.06 * (hash1(i * 5) - 0.5)); c.rotation.set(i, i * 2, 0); DOG.body.add(c); chunks.push(c); }
const DORG = [dHeart, dStom, dLiver, dBrain, ...chunks];
const poisonPts = (() => { const g = new THREE.BufferGeometry(); const p = new Float32Array(260 * 3); g.setAttribute('position', new THREE.BufferAttribute(p, 3)); const m = new THREE.Points(g, new THREE.PointsMaterial({ color: 0xffa040, size: 0.014, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending })); m.frustumCulled = false; m.renderOrder = 7; scene.add(m); return { m, p }; })();
const dogBlood = (() => { const g = new THREE.BufferGeometry(); const p = new Float32Array(200 * 3); g.setAttribute('position', new THREE.BufferAttribute(p, 3)); const m = new THREE.Points(g, new THREE.PointsMaterial({ color: 0xff4040, size: 0.012, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending })); m.frustumCulled = false; m.renderOrder = 6; scene.add(m); return { m, p }; })();
function setDogX(k) { for (const x of DOGX) x.visible = k > 0.01; dogX.emissiveIntensity = 1.1 * k; for (const o of DOGMESH) o.visible = k < 0.6; for (const o of DOGSKIN) o.visible = k < 0.6; DOG.tongue.visible = DOG.tongue.visible && k < 0.6; for (const o of DORG) o.visible = k > 0.5; poisonPts.m.visible = dogBlood.m.visible = k > 0.5; }
// the dog's pose: { x, z, yaw, h (body drop), pitch, roll, legs:{FR:[hip, knee], ...}, neck, head:[pitch, yaw, roll], jaw, ears, tail:[raise, wag], tongue, shake }
const DOGSTAND = { h: 0, pitch: 0, roll: 0, legs: { FR: [0, 0], FL: [0, 0], BR: [0, 0], BL: [0, 0] }, neck: 0, head: [0, 0, 0], jaw: 0, ears: 0, tail: [20, 0], tongue: 0, shake: 0 };
function applyDog(p) {
  const d = DOG; d.g.position.set(p.x, 0, p.z); d.g.rotation.set(0, p.yaw * D2R, 0);
  const sh = p.shake || 0;
  const sr = Math.sin(p.roll * D2R), cr = Math.cos(p.roll * D2R);            // roll about his spine (0.45 up), landing on his side with the spine 0.17 up
  d.body.position.set(0.45 * sr + 0.012 * sh * vn1(T_ * 30, 1), -p.h * (1 - Math.abs(sr)) + (0.17 - 0.45 * cr) * Math.abs(sr) + 0.01 * sh * vn1(T_ * 33, 2), 0); d.body.rotation.set(-p.pitch * D2R + 0.03 * sh * vn1(T_ * 28, 3), 0, p.roll * D2R + 0.04 * sh * vn1(T_ * 31, 4));
  for (const [k, L] of Object.entries(d.legs)) { const [a, b] = p.legs[k]; L.hip.rotation.set(a * D2R, 0, 0); L.knee.rotation.set(b * D2R, 0, 0);
    if (L.back) { L.hock.rotation.set(-b * 0.85 * D2R, 0, 0); L.paw.rotation.set((p.pitch - a - 0.15 * b) * D2R, 0, 0); } else L.paw.rotation.set((p.pitch - a - b) * D2R, 0, 0); }
  d.neck.rotation.set(p.neck * D2R, 0, 0); d.head.rotation.set(p.head[0] * D2R, p.head[1] * D2R, p.head[2] * D2R);
  d.jaw.rotation.set(p.jaw * 24 * D2R, 0, 0); d.tongue.visible = p.tongue > 0.05 && DOGMESH[0].visible; d.tongue.scale.z = 0.055 * (0.6 + 0.6 * p.tongue);
  d.ears.forEach((e, i) => e.rotation.set(0, 0, (i ? -1 : 1) * p.ears * D2R));
  d.tail.forEach((s, i) => s.rotation.set((i === 0 ? p.tail[0] : 6) * D2R, (p.tail[1] / 5) * D2R * (1 + i * 0.3), 0));
  d.g.updateMatrixWorld(true);
  if (p.ground !== false) { d.g.position.y -= dogLowest(); d.g.updateMatrixWorld(true); }    // rest him on the floor: nothing sinks in, nothing floats
}
const LOWV = new THREE.Vector3();
function dogLowest() { const m = DOGMESH[0], n = m.geometry.attributes.position.count; m.skeleton.update(); m.updateMatrixWorld(true); let lo = 1e9;
  for (let i = 0; i < n; i += 4) { m.getVertexPosition(i, LOWV); LOWV.applyMatrix4(m.matrixWorld); if (LOWV.y < lo) lo = LOWV.y; } return lo; }
let T_ = 0;
const mixDog = (a, b, k) => { const o = {}; for (const key of Object.keys(a)) { const x = a[key], y = b[key] ?? x; if (key === 'legs') { o.legs = {}; for (const l of Object.keys(x)) o.legs[l] = x[l].map((v, i) => lerp(v, y[l][i], k)); } else if (Array.isArray(x)) o[key] = x.map((v, i) => lerp(v, y[i], k)); else if (typeof x === 'number') o[key] = lerp(x, y, k); else o[key] = x; } return o; };
const DOGEAT = { ...DOGSTAND, h: 0.23, legs: { FR: [20, -110], FL: [20, -110], BR: [-85, 150], BL: [-85, 150] }, neck: 45, head: [30, 0, 0], tail: [70, 0] };   // lying down, chewing the bar between his paws
const DOGSPHINX = { ...DOGSTAND, h: 0.21, legs: { FR: [8, -95], FL: [8, -95], BR: [-75, 130], BL: [-75, 130] }, neck: -10, head: [8, 0, 0], tail: [70, 0] };
const DOGSIT = { ...DOGSTAND, h: 0.08, pitch: 32, legs: { FR: [32, 0], FL: [32, 0], BR: [-95, 140], BL: [-95, 140] }, neck: -15, head: [20, 0, 0], tail: [100, 0] };
const DOGSIDE = { ...DOGSTAND, h: 0, roll: 90, legs: { FR: [-20, 10], FL: [-20, 10], BR: [-10, -10], BL: [-10, -10] }, neck: -20, head: [15, 0, 0], tail: [80, 0] };
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
G.reset(); G.root.updateMatrixWorld(true);
const EAR_L = V(0.08, 1.64, 0.01).applyMatrix4(G.bones.head.matrixWorld.clone().invert());

// ------------------------------------------------------------------ the story
const DOGE = { x: 0.62, z: -0.1, yaw: 90 };                     // where he eats the bar (facing +x; the bar fell off the coffee table)
const BAR = V(1.04, 0, -0.1);
const LF = w => 2 * Math.PI * Math.round(w * TOTAL / (2 * Math.PI)) / TOTAL;   // a speed that repeats cleanly over the loop
const chewAt = t => 0.5 + 0.5 * Math.sin(t * LF(13));
const wagAt = (t, a = 1) => 32 * a * Math.sin(t * LF(11));
function dogAt(t) {
  const b = beatAt(t), lt = t - B[b], u = lt / DUR[b];
  const at = (p, pos) => ({ ...p, x: pos.x, z: pos.z, yaw: pos.yaw });
  const chew = (t, a = 1) => ({ ...DOGEAT, neck: 54 - 10 * a * chewAt(t), head: [36 - 8 * a * chewAt(t), 4 * Math.sin(t * LF(2.1)), 0], jaw: 0.8 * a * chewAt(t), tail: [60, wagAt(t, 0.7)], ears: 5 * Math.sin(t * LF(13)) });
  if (b === 9) { const k = smooth(DUR[9] - 0.9, DUR[9] - 0.05, lt);       // looks up at us, then dips back to the bar (loops into beat 0)
    const look = { ...DOGSPHINX, h: 0.23, legs: DOGEAT.legs, neck: -6, head: [4, 8 * Math.sin(lt * 1.3), 6], tail: [60, wagAt(t, 0.7)], ears: 3, jaw: 0.25, tongue: 0.6 };
    return { pose: at(mixDog(look, chew(t, k), smooth(0, 1, k)), DOGE), x: 0, show: true }; }
  if (b === 0) return { pose: at(chew(t), DOGE), x: 0, show: true };
  if (b === 1) return { pose: at({ ...DOGSTAND, neck: 10, head: [5, 0, 0], tail: [20, wagAt(t, 0.3)] }, DOGE), x: 1, show: true };
  if (b === 2) { if (u < CUT2) return { pose: at({ ...DOGSTAND, neck: 5, shake: 0.6 * smooth(0.1, 0.4, u), tail: [-10, 0], ears: -8 }, DOGE), x: 1, show: true, race: true };
    return { pose: at({ ...DOGSIDE, shake: 1.6, legs: { FR: [-20 + 18 * Math.sin(t * 18), 10], FL: [-20 + 18 * Math.sin(t * 18 + 1), 10], BR: [-10 + 15 * Math.sin(t * 17 + 2), -10], BL: [-10 + 15 * Math.sin(t * 17 + 3), -10] }, jaw: 0.4 + 0.2 * Math.sin(t * 20), tail: [60, 0] }, { x: 0.6, z: -0.1, yaw: 90 }), x: 0, show: true, race: true }; }
  if (b === 3) return { pose: at({ ...DOGSPHINX, jaw: 0.55, tongue: 1, neck: -12 + 3 * Math.sin(t * 7), head: [6, 10 * Math.sin(lt * 0.9), 0], tail: [70, wagAt(t, 0.8)] }, { x: dogBed.position.x, z: dogBed.position.z - 0.22, yaw: 0 }), x: 0, show: true };
  if (b === 5) return { pose: at({ ...DOGSIT, neck: -5, head: [28 + 4 * Math.sin(lt * 1.5), 12 * Math.sin(lt * 0.8), 8], tail: [100, wagAt(t, 0.4)], ears: 6 }, DOGE), x: 0, show: true };
  if (b === 6) return { pose: at({ ...DOGSPHINX, neck: -8, head: [4, -20, 0], tail: [70, 0], ears: -4 }, { x: 0.3, z: -0.35, yaw: -30 }), x: 0, show: true };
  if (b === 7) return { pose: at({ ...DOGSPHINX, neck: -6, head: [10, 25, 0], tail: [70, wagAt(t, 0.3)], ears: 0 }, DOGL), x: 0, show: true };
  if (b === 8) return { pose: at({ ...DOGSTAND, legs: { FR: [10, 0], FL: [10, 0], BR: [0, 0], BL: [0, 0] }, neck: 80 - 6 * chewAt(t), head: [45, 4 * Math.sin(lt * 3), 0], jaw: 0.35 * chewAt(t), tail: [30, wagAt(t)], ears: 6 * Math.sin(t * 9) }, { x: halloween.position.x - 0.5, z: halloween.position.z, yaw: 90 }), x: 0, show: true };
  return { show: false };
}
const CUT2 = 0.45;
const DOGL = { x: 0.35, z: 0.15, yaw: 90 };
// the owner (same guy): shocked in the back (beat 0), on the phone with the wrapper (6), kneeling with his hand on the dog (7)
const OWN0 = V(-0.45, 0, -1.1), OWN6 = V(-0.35, 0, 0.75), OWN7 = V(0.3, 0, 0.72);
function earW() { return EAR_L.clone().applyMatrix4(G.bones.head.matrixWorld); }
function ownerState(t) {
  const b = beatAt(t), lt = t - B[b], u = lt / DUR[b];
  if (b === 0 || b === 9) { const k = b === 9 ? 0 : smooth(0.2, 0.9, lt);   // beat 9: calm in the back, so the loop into beat 0 is seamless
    const pose = curl(curl(addPose(STAND, { armR: A(10 + 45 * k, 12 + 18 * k, 0, 20 + 70 * k, -30 * k), armL: A(10 + 45 * k, 12 + 18 * k, 0, 20 + 70 * k, -30 * k), neck: [-10 * k, 0, 0], spine1: [-4 * k, 0, 0] }), 'R', 26 - 20 * k), 'L', 26 - 20 * k);
    return { pose, root: { x: OWN0.x, y: 0.95, z: OWN0.z, yaw: -125 }, yaw: -125, feet: OWN0, hands: [], face: { fear: 0.8 * k, jaw: 0.5 * k, browIn: 0.5, blink: 0, oh: 0.4 * k }, show: true }; }
  if (b === 6) { const f = fwdOf(180), r = rightOf(180);
    const pose = addPose(STAND, { neck: [-14, 8, 0], head: [-6, 0, 4] });
    const phoneT = () => { const e = earW(); return { S: 'R', p: e.clone().addScaledVector(r, 0.03).addScaledVector(f, 0.03).add(V(0, -0.02, 0)), n: r.clone().negate(), u: V(0, 1, 0).addScaledVector(f, 0.35).normalize(), c: 45, seed: A(40, 40, 0, 140, 60) }; };
    const wrapT = () => { const c = wp(G.bones.chest); return { S: 'L', p: c.clone().addScaledVector(f, 0.3).addScaledVector(r, -0.12).add(V(0, -0.1, 0)), n: V(0, 0.55, 0).addScaledVector(f, -1).normalize(), u: V(0, 0.3, 0).addScaledVector(r, -1).normalize(), c: 40, seed: A(50, 10, 0, 100, 70) }; };
    return { pose, root: { x: OWN6.x, y: 0.95, z: OWN6.z, yaw: 180 }, yaw: 180, feet: OWN6, hands: [phoneT, wrapT], face: { fear: 0.5, browIn: 0.7, jaw: 0.2 + 0.25 * Math.max(0, Math.sin(lt * 7)), blink: blinkAt(lt) }, show: true }; }
  if (b === 7) { const backT = () => { const bk = DOG.body.localToWorld(V(0, 0.635, -0.05)); return { S: 'R', p: bk.add(V(0, 0.0, 0)), n: V(0, -1, 0), u: V(1, 0, -0.25).normalize(), c: 18, seed: A(55, 15, 0, 40, 30) }; };
    const pet = 0.03 * Math.sin(lt * 3);
    const pose = curl(curl(addPose(STAND, { spine1: [-8, 0, 0], spine2: [-6, 0, 0], neck: [-26, 10, 0], head: [-8, 0, 0], armL: A(22, 14, 0, 45, 20) }), 'R', 20), 'L', 22);
    return { pose, root: { x: OWN7.x, y: 0.5, z: OWN7.z, yaw: 0, tilt: -22 }, yaw: 0, kneel: true, hands: [() => { const h = backT(); h.p.add(V(pet, 0, 0)); return h; }], face: { browIn: 0.7, fear: 0.3, blink: blinkAt(lt), jaw: 0.15 }, show: true }; }
  return { show: false };
}
function blinkAt(s) { const u = ((s + 40) % 3.7) / 0.16; return u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0; }

// ------------------------------------------------------------------ cameras
function shakeV(t, a) { return V(vn1(t * 14, 1) * a * 0.5, vn1(t * 14, 2) * a, vn1(t * 14, 3) * a); }
function camAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b], u = lt / d;
  const hd = wp(DOG.head);
  if (b === 0 || b === 9) { const k = b === 0 ? smooth(0, DUR[0], lt) : 1 - smooth(DUR[9] - 1.0, DUR[9], lt);   // low by his face, the owner behind him
    return { pos: V(1.95 - 0.1 * k, 0.55, 1.0 - 0.08 * k), tgt: V(0.6, 0.55, -0.45), fov: 56 }; }
  if (b === 1) return { pos: V(2.15 - 0.15 * u, 0.72, 0.85 - 0.08 * u), tgt: V(0.62, 0.42, -0.1), fov: 50 };
  if (b === 2) { if (u < CUT2) return { pos: V(1.25 - 0.06 * u, 0.55, 0.55), tgt: V(0.76, 0.45, -0.1), fov: 38 };
    return { pos: V(1.55, 0.95, 0.55).add(shakeV(t, 0.01)), tgt: V(0.62, 0.12, -0.1), fov: 50 }; }
  if (b === 3) return { pos: V(dogBed.position.x + 0.2, 0.62, dogBed.position.z + 1.75 - 0.15 * u), tgt: V(dogBed.position.x, 0.95, dogBed.position.z - 1.5), fov: 52 };
  if (b === 4) return { pos: CHOC.clone().add(V(0.1 - 0.1 * u, 1.3, 4.4 - 0.15 * u)), tgt: CHOC.clone().add(V(0, 1.2, 0)), fov: 50 };
  if (b === 5) return { pos: V(1.95 - 0.1 * u, 0.6, 0.85), tgt: V(0.88, 0.45, -0.1), fov: 50 };
  if (b === 6) return { pos: V(-0.24 - 0.06 * u, 1.4, 2.5 - 0.15 * u), tgt: V(-0.3, 1.0, 0.3), fov: 50 };
  if (b === 7) return { pos: V(2.0 - 0.1 * u, 1.05, 0.0), tgt: V(0.4, 0.55, 0.45), fov: 50 };
  if (b === 8) { const hp = halloween.position; return { pos: hp.clone().add(V(0.3 - 0.08 * u, 0.8, 1.2 - 0.1 * u)), tgt: hp.clone().add(V(-0.3, 0.28, 0)), fov: 50 }; }
  return { pos: V(0, 1.5, 3), tgt: V(0, 0.5, 0), fov: 45 };
}

// ------------------------------------------------------------------ clipping: him vs the room, the floor, his own body and the dog; the dog vs the floor
const SOLIDS = [];
const sbox = (name, obj, min, max) => SOLIDS.push({ name, obj, box: new THREE.Box3(min, max) });
sbox('couch', couch, V(-1.1, 0, -0.45), V(1.1, 0.98, 0.45)); sbox('coffee table', table, V(-0.55, 0, -0.3), V(0.55, 0.45, 0.3)); sbox('counter', counter, V(-0.33, 0, -1.5), V(0.33, 0.95, 2.35));
const BODYPTS = { handR: 0.035, handL: 0.035, farmR: 0.035, farmL: 0.035, uarmR: 0.045, uarmL: 0.045, head: 0.09, chest: 0.12, hips: 0.1, shinR: 0.05, shinL: 0.05, footR: 0.04, footL: 0.04 };
function segDist(p, a, b) { const ab = b.clone().sub(a), t = clamp(p.clone().sub(a).dot(ab) / ab.lengthSq(), 0, 1); return p.distanceTo(a.clone().addScaledVector(ab, t)); }
const trunkDist = (Gx, p) => { const h = wp(Gx.bones.hips), c = wp(Gx.bones.chest), n = wp(Gx.bones.neck); return Math.min(segDist(p, h, c), segDist(p, c, n)); };
// the dog's real skinned surface (every 3rd vertex of the body) for clip checks: floor and his hands
const DOGSAMP = (() => { const m = DOGMESH[0], n = m.geometry.attributes.position.count, idx = []; for (let i = 0; i < n; i += 3) idx.push(i); return { m, idx, P: new Float32Array(idx.length * 3), N: new Float32Array(idx.length * 3), frame: -1 }; })();
function dogSurface() { const S = DOGSAMP, m = S.m, pa = m.geometry.attributes.position, na = m.geometry.attributes.normal, v = new THREE.Vector3(), w = new THREE.Vector3();
  m.skeleton.update(); m.updateMatrixWorld(true);
  S.idx.forEach((i, j) => { m.getVertexPosition(i, v); v.applyMatrix4(m.matrixWorld);
    w.fromBufferAttribute(pa, i).addScaledVector(w.clone().fromBufferAttribute(na, i), 0.01); m.applyBoneTransform(i, w); w.applyMatrix4(m.matrixWorld).sub(v).normalize();
    S.P.set([v.x, v.y, v.z], j * 3); S.N.set([w.x, w.y, w.z], j * 3); });
  return S; }
function insideDog(p, S) { let best = 1e9, bj = -1; for (let j = 0; j < S.idx.length; j++) { const dx = p.x - S.P[j * 3], dy = p.y - S.P[j * 3 + 1], dz = p.z - S.P[j * 3 + 2], d = dx * dx + dy * dy + dz * dz; if (d < best) { best = d; bj = j; } }
  if (best > 0.04 * 0.04) return -1; const j = bj; return -((p.x - S.P[j * 3]) * S.N[j * 3] + (p.y - S.P[j * 3 + 1]) * S.N[j * 3 + 1] + (p.z - S.P[j * 3 + 2]) * S.N[j * 3 + 2]); }
function clipScan() { const out = []; scene.updateMatrixWorld(true);
  if (G.root.visible) { const R = RG, Gx = G;
    const pts = Object.entries(BODYPTS).map(([n, r]) => [n, wp(Gx.bones[n]), r]);
    for (const S of ['R', 'L']) for (const f of ['index', 'middle', 'pinky', 'thumb']) pts.push([f + ' tip ' + S, R.tip(f, S), 0.008]);
    const headC = wp(Gx.bones.head).add(V(0, 0.09, 0).applyQuaternion(wq(Gx.bones.head)));
    const DS = DOG.g.visible && DOGMESH[0].visible ? dogSurface() : null;
    for (const [n, p, r] of pts) {
      if (DS && /^(hand|farm|index|middle|pinky|thumb)/.test(n)) { const dd = insideDog(p, DS) + r; if (dd > 0.012) out.push({ what: 'him ' + n, into: 'the dog', depth: +(dd * 100).toFixed(1) }); }
      if (p.y - r < -0.015) out.push({ what: 'him ' + n, into: 'floor', depth: +((-(p.y - r)) * 100).toFixed(1) });
      for (const S of SOLIDS) { if (!S.obj.visible) continue; const q = p.clone().applyMatrix4(S.obj.matrixWorld.clone().invert()), bx = S.box;
        const dx = Math.min(q.x - bx.min.x, bx.max.x - q.x), dy = Math.min(q.y - bx.min.y, bx.max.y - q.y), dz = Math.min(q.z - bx.min.z, bx.max.z - q.z);
        const dd = Math.min(dx, dy, dz) + r; if (dx > -r && dy > -r && dz > -r && dd > (S.name === 'the dog' ? 0.02 : 0.012)) out.push({ what: 'him ' + n, into: S.name, depth: +(dd * 100).toFixed(1) }); }
      if (/^(hand|farm|index|middle|pinky|thumb)/.test(n)) { const dT = trunkDist(Gx, p) - 0.11 - r; if (dT < -0.012) out.push({ what: 'him ' + n, into: 'own body', depth: +(-dT * 100).toFixed(1) });
        const dH = p.distanceTo(headC) - 0.1 - r; const phoneHand = guyCache && guyCache.phone && /R$/.test(n); if (dH < (phoneHand ? -0.045 : -0.03)) out.push({ what: 'him ' + n, into: 'own head', depth: +(-dH * 100).toFixed(1) }); } } }
  if (DOG.g.visible && DOGMESH[0].visible) { for (const [k, L] of Object.entries(DOG.legs)) { const p = wp(L.paw); if (p.y - 0.03 < -0.02) out.push({ what: 'dog paw ' + k, into: 'floor', depth: +((-(p.y - 0.03)) * 100).toFixed(1) }); }
    const S = dogSurface(); let lo = 1e9, at = 0; for (let j = 0; j < S.idx.length; j++) if (S.P[j * 3 + 1] < lo) { lo = S.P[j * 3 + 1]; at = j; }
    if (lo < -0.012) out.push({ what: 'dog ' + DOGDATA.bones[S.m.geometry.attributes.skinIndex.getX(S.idx[at])].name, into: 'floor', depth: +(-lo * 100).toFixed(1) });
    if (lo > 0.03) out.push({ what: 'dog body', into: 'the air (floating)', depth: +(lo * 100).toFixed(1) }); }
  return out; }

// ------------------------------------------------------------------ per-frame update
let LASTF = -10, guyCache = null;
function update(t, frame) {
  t = ((t % TOTAL) + TOTAL) % TOTAL; T_ = t;
  const b = beatAt(t), lt = t - B[b], d = DUR[b], u = lt / d;
  // ---- the dog
  const dg = dogAt(t); DOG.g.visible = dg.show;
  if (window.DOGTEST) { const P = window.DOGTEST; applyDog({ ...DOGSTAND, ...P, legs: { ...DOGSTAND.legs, ...(P.legs || {}) } }); setDogX(0); }
  else if (dg.show) { applyDog({ ...DOGSTAND, ...dg.pose, legs: { ...DOGSTAND.legs, ...(dg.pose.legs || {}) } }); }
  const xk = b === 1 ? 1 : b === 2 && u < CUT2 ? 1 : 0; setDogX(dg.show ? xk : 0);
  // inside him: the heart beats (races in beat 2), the poison leaves the stomach and spreads through his blood
  const race = dg.race ? 3.2 : 1.6, ph = (t * race) % 1, hb = Math.exp(-Math.pow((ph - 0.1) / 0.07, 2)) + 0.5 * Math.exp(-Math.pow((ph - 0.3) / 0.07, 2));
  dHeart.scale.set(0.05 * (1 + 0.18 * hb), 0.065 * (1 + 0.18 * hb), 0.05 * (1 + 0.18 * hb)); dHeartM.emissiveIntensity = 0.8 + 0.8 * hb;
  if (poisonPts.m.visible) { const spread = b === 1 ? smooth(0.1, 0.95, u) : 1, loops = [V(0, 0.42, 0.02), V(0, 0.45, 0.2), V(0, 0.72, 0.45), V(0, 0.5, 0.25), V(0.08, 0.1, 0.22), V(0, 0.42, 0.02), V(-0.08, 0.1, -0.27), V(0, 0.48, -0.3), V(0, 0.42, 0.02)];
    const along = s => { const n = loops.length - 1, x = (s % 1) * n, i = Math.floor(x), f = x - i; return loops[i].clone().lerp(loops[i + 1], f); };
    for (let i = 0; i < 260; i++) { const on = i / 260 < spread; const s = hash1(i * 3) + t * 0.25 * (race / 1.6); const p = on ? DOG.body.localToWorld(along(s).add(V((hash1(i) - 0.5) * 0.04, (hash1(i * 5) - 0.5) * 0.04, (hash1(i * 7) - 0.5) * 0.04))) : V(0, -99, 0); poisonPts.p.set([p.x, p.y, p.z], i * 3); }
    for (let i = 0; i < 200; i++) { const s = hash1(i * 11) + t * 0.25 * (race / 1.6); const p = DOG.body.localToWorld(along(s).add(V((hash1(i * 2) - 0.5) * 0.05, (hash1(i * 9) - 0.5) * 0.05, 0))); dogBlood.p.set([p.x, p.y, p.z], i * 3); }
    poisonPts.m.geometry.attributes.position.needsUpdate = dogBlood.m.geometry.attributes.position.needsUpdate = true; dLiverM.emissiveIntensity = 0.4 + 0.3 * Math.sin(t * 2); }
  // ---- the owner
  const o = ownerState(t); guyCache = { phone: b === 6 }; G.root.visible = o.show;
  if (o.show) { RG.applyPose(o.pose, o.root);
    if (o.feet) for (const [S, sx, sz] of [['R', 0.11, -0.02], ['L', -0.11, 0.02]]) { const f = o.feet.clone().addScaledVector(rightOf(o.yaw), sx).addScaledVector(fwdOf(o.yaw), -sz).add(V(0, 0.102, 0)); RG.foot(S, f, f.clone().add(V(0, 0.45, 0)).addScaledVector(fwdOf(o.yaw), 1), yawQ(o.yaw)); }
    if (o.kneel) for (const [S, s] of [['R', 1], ['L', -1]]) { const r = rightOf(o.yaw), f = fwdOf(o.yaw), hipJ = wp(G.bones['thigh' + S]);
      const knee = V(hipJ.x, 0.07, hipJ.z).addScaledVector(f, 0.06); const ankle = knee.clone().addScaledVector(f, -0.4).add(V(0, 0.03, 0)).addScaledVector(r, s * 0.02);
      RG.foot(S, ankle, knee.clone().addScaledVector(f, 0.6).add(V(0, 0.15, 0)), qAA(V(0, 0, 1), 180).multiply(yawQ(o.yaw)).multiply(qAA(V(1, 0, 0), -20))); }
    G.root.updateMatrixWorld(true);
    RG.hands(o.hands.map(h => h()), 'b' + b, frame); if (!o.hands.length) { delete RG.LAST.costR; delete RG.LAST.costL; }
    G.root.updateMatrixWorld(true); RG.untwist(); G.face(o.face); G.root.updateMatrixWorld(true); }
  else { delete RG.LAST.costR; delete RG.LAST.costL; }
  // props: the phone at his ear, the wrapper in his hand; the bar and wrapper on the floor
  phone.visible = o.show && b === 6; wrapperHand.visible = o.show && b === 6;
  if (phone.visible) { const q = wq(G.bones.handR), n = RG.HANDREST.R.n.clone().applyQuaternion(q), uu = RG.HANDREST.R.u.clone().applyQuaternion(q); phone.position.copy(RG.palmW('R')).addScaledVector(n, 0.012);
    const zA = n.clone(), yA = uu.clone().sub(zA.clone().multiplyScalar(uu.dot(zA))).normalize(), xA = new THREE.Vector3().crossVectors(yA, zA); phone.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(xA, yA, zA)); }
  if (wrapperHand.visible) { const q = wq(G.bones.handL), n = RG.HANDREST.L.n.clone().applyQuaternion(q), uu = RG.HANDREST.L.u.clone().applyQuaternion(q); wrapperHand.position.copy(RG.palmW('L')).addScaledVector(n, 0.012).addScaledVector(uu, 0.04);
    const zA = n.clone(), yA = uu.clone().sub(zA.clone().multiplyScalar(uu.dot(zA))).normalize(), xA = new THREE.Vector3().crossVectors(yA, zA); wrapperHand.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(xA, yA, zA)); }
  floorBar.visible = wrapperFloor.visible = b === 9 || b === 0 || b === 5; floorBar.position.copy(BAR); floorBar.rotation.y = 0.1; wrapperFloor.position.set(BAR.x + 0.12, 0.003, BAR.z + 0.14);
  floorBar.scale.setScalar(b === 5 ? 1.25 : 1);
  // ---- the lineup (beat 4): danger bars grow, scaled to the poison per ounce
  home.visible = b !== 4; chocStage.visible = b === 4;
  LINEUP.forEach((L, i) => { const k = smooth(0.08 + 0.12 * i, 0.4 + 0.12 * i, u); const h = Math.max(0.004, 1.7 * L.mg / 440 * k); L.danger.scale.y = h; L.danger.position.y = h / 2; L.danger.visible = b === 4; });
  // ---- the clock runs 6 to 12 hours in beat 3
  { const hrs = b === 3 ? lerp(0, 9, smooth(0, 1, u)) : 0; clockHands.m.rotation.z = -hrs * Math.PI * 2; clockHands.h.rotation.z = -(4 + hrs) / 12 * Math.PI * 2; clockHands.s.rotation.z = -t * 6; }
  halloween.visible = b === 8; halloweenLight.intensity = b === 8 ? 2.5 : 0; dogBed.visible = b === 3;
  // ---- camera and light
  const C = camAt(t); camera.position.copy(C.pos); camera.up.set(0, 1, 0); camera.lookAt(C.tgt); camera.fov = C.fov; camera.updateProjectionMatrix();
  const dim = 1 - 0.78 * (dg.show ? xk : 0);
  sun.position.set(1.6, 3.4, 2.4); sun.target.position.set(0, 0, 0); sun.target.updateMatrixWorld();
  sun.intensity = 2.6 * dim * (b === 8 ? 0.4 : 1); hemi.intensity = 0.85 * dim * (b === 8 ? 0.5 : 1); scene.environmentIntensity = 0.35 * dim; lamp.intensity = 6 * dim;
  scene.background = b === 4 ? new THREE.Color(0x1a1414) : new THREE.Color(0xd9cbb6).multiplyScalar(dim);
  return { beat: b, cut: b === 2 && u >= CUT2 && (u - CUT2) * d * FPS < 1 };
}

// ------------------------------------------------------------------ frame I/O (same contract as the other 3D Shorts)
const draw = () => renderer.render(scene, camera);
const gl = renderer.getContext(), px = new Uint8Array(W * H * 4);
let CUTF = false, LASTB = 0;
function stepTo(i) { const t = i / FPS, b = beatAt(((t % TOTAL) + TOTAL) % TOTAL);
  if (i !== LASTF + 1) for (let j = Math.max(Math.round(B[b] * FPS), i - 12); j < i; j++) update(j / FPS, j);
  const r = update(t, i); CUTF = r.cut; LASTB = r.beat; LASTF = i; }
window.renderAll = async (f0, f1) => { for (let i = f0; i < f1; i++) { stepTo(i); draw(); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); await fetch('/frame', { method: 'POST', body: px }); } return 'ok'; };
window.renderAtT = t => { const i = Math.round(t * FPS); stepTo(i);
  if (window.CAM && window.CAM.hand) { const hp = RG.palmW(window.CAM.hand); window.CAM.tgt = hp.toArray(); window.CAM.pos = hp.clone().add(V(...window.CAM.off)).toArray(); }
  if (window.CAM) { camera.position.set(...window.CAM.pos); camera.up.set(0, 1, 0); camera.lookAt(...window.CAM.tgt); camera.fov = window.CAM.fov || 42; camera.updateProjectionMatrix(); }
  draw(); return renderer.domElement.toDataURL('image/png'); };
window.rigReport = i => { stepTo(i); const t = i / FPS, iq = G.root.getWorldQuaternion(new THREE.Quaternion()).invert();
  const ang = G.root.visible ? { ...RG.LAST } : {}; delete ang.costR; delete ang.costL;
  return { t, beat: LASTB, ang, hips: G.root.visible ? wp(G.bones.hips).toArray() : [0, 0, 0], car: 0, show: G.root.visible || DOG.g.visible, cut: CUTF,
    thumbs: G.root.visible ? ['R', 'L'].map(S => wp(G.bones['index1' + S]).sub(wp(G.bones['pinky1' + S])).applyQuaternion(iq).toArray()) : null,
    forearms: G.root.visible ? ['R', 'L'].map(S => wp(G.bones['hand' + S]).sub(wp(G.bones['farm' + S])).normalize().applyQuaternion(iq).toArray()) : null,
    cost: G.root.visible ? [RG.LAST.costR ?? null, RG.LAST.costL ?? null] : [null, null], clip: clipScan() }; };
window.dbg = { G, RG, DOG, wp, THREE };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS);
window.READY = true;
