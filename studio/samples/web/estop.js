// "The Earth stops spinning for one second" - STYLE SAMPLE (painterly: a moving oil painting)
//   estop.html?w=720&h=1280            4.6 s: an equator street at golden hour; at 1.3 s the ground stops and everything loose keeps
//   going east at 1,000 mph (shown slowed down). The 3D render goes through a Kuwahara paint pass + paint edges + canvas + grade.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { loadGuy } from '/guy3d.js';

const Q = new URLSearchParams(location.search);
const W = +Q.get('w') || 720, H = +Q.get('h') || 1280;
const FPS = 30, TOTAL = 4.6, TS = 1.3;                         // TS: the moment the ground stops
const clamp = (x, a, b) => Math.min(Math.max(x, a), b);
const sm = t => t * t * (3 - 2 * t);
const smooth = (a, b, x) => sm(clamp((x - a) / (b - a), 0, 1));
const lerp = (a, b, u) => a + (b - a) * u;
const D2R = Math.PI / 180;
function hash1(n) { const s = Math.sin(n * 127.1) * 43758.5453; return s - Math.floor(s); }
function vn1(x, seed) { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return lerp(hash1(i + seed * 17.3), hash1(i + 1 + seed * 17.3), u) * 2 - 1; }
const V = (x, y, z) => new THREE.Vector3(x, y, z);
function canvasTex(w, h, draw) { const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), c); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t; }

// ------------------------------------------------------------------ renderer, golden-hour sky and light (the sun low in the west, -x)
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(W, H);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05; renderer.outputColorSpace = THREE.SRGBColorSpace;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(40, W / H, 0.05, 900);
const SUNDIR = V(-0.75, 0.32, 0.35).normalize();
const skyU = { uSun: { value: SUNDIR }, uT: { value: 0 }, uStreak: { value: 0 } };
const skyMat = new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false, uniforms: skyU,
  vertexShader: 'varying vec3 vD; void main(){ vD = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
  fragmentShader: `varying vec3 vD; uniform vec3 uSun; uniform float uT, uStreak;
    float hh(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
    float vn(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f*f*(3.0-2.0*f); return mix(mix(hh(i), hh(i+vec2(1,0)), u.x), mix(hh(i+vec2(0,1)), hh(i+vec2(1,1)), u.x), u.y); }
    void main(){ float h = clamp(vD.y, -0.1, 1.0);
      vec3 c = mix(vec3(1.0, 0.62, 0.36), vec3(0.98, 0.78, 0.55), smoothstep(0.0, 0.12, h)); c = mix(c, vec3(0.42, 0.56, 0.86), smoothstep(0.1, 0.6, h));
      float s = max(dot(normalize(vD), uSun), 0.0); c += vec3(1.0, 0.75, 0.4) * (pow(s, 6.0) * 0.5 + pow(s, 400.0) * 3.0);
      vec2 cp = vec2(atan(vD.x, -vD.z) * 3.0 - uStreak * 2.5, vD.y * 9.0);                     // clouds (they streak east when it stops)
      float cl = vn(cp * vec2(1.0 / (1.0 + uStreak * 6.0), 1.0) + vec2(uT * 0.02, 0.0)) * 0.65 + vn(cp * 2.3) * 0.35;
      c = mix(c, mix(vec3(1.0, 0.85, 0.7), vec3(1.0, 0.6, 0.45), 1.0 - smoothstep(0.05, 0.4, h)), smoothstep(0.55, 0.75, cl) * smoothstep(0.02, 0.15, h) * 0.85);
      gl_FragColor = vec4(pow(c, vec3(2.2)), 1.0); }` });
const sky = new THREE.Mesh(new THREE.SphereGeometry(800, 48, 24), skyMat); scene.add(sky);
{ const pm = new THREE.PMREMGenerator(renderer); const es = new THREE.Scene(); es.add(new THREE.Mesh(new THREE.SphereGeometry(10, 32, 16), skyMat));
  scene.environment = pm.fromScene(es, 0.03).texture; scene.environmentIntensity = 0.35; }
scene.add(new THREE.HemisphereLight(0x8fa6e0, 0x3a3060, 0.65));           // cool blue-violet fill: painted shadows against the warm sun
const sun = new THREE.DirectionalLight(0xffbe7a, 4.4); sun.position.copy(SUNDIR).multiplyScalar(40); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
{ const S = sun.shadow.camera; S.left = -16; S.right = 16; S.top = 14; S.bottom = -6; S.near = 1; S.far = 120; sun.shadow.bias = -0.0005; sun.shadow.normalBias = 0.03; }
scene.add(sun); scene.add(sun.target);

// ------------------------------------------------------------------ the street (runs east-west along x; he stands on the near sidewalk, z = 1.5)
const mat = (c, r = 0.8, m = 0) => new THREE.MeshStandardMaterial({ color: c, roughness: r, metalness: m });
const box = (w, h, d, x, y, z, m, r = 0, parent = scene) => { const o = new THREE.Mesh(r > 0 ? new RoundedBoxGeometry(w, h, d, 2, Math.min(r, 0.4 * Math.min(w, h, d))) : new THREE.BoxGeometry(w, h, d), m); o.position.set(x, y, z); o.castShadow = true; o.receiveShadow = true; parent.add(o); return o; };
box(200, 0.1, 6, 0, -0.05, -3, mat(0x3a3640, 0.95));                                   // road
box(200, 0.18, 4, 0, 0.04, 2.0, mat(0xcbb79e, 0.9));                                   // near sidewalk
box(200, 0.18, 3, 0, 0.04, -7.5, mat(0xc2ac92, 0.9));                                  // far sidewalk
box(400, 0.1, 400, 0, -0.12, -100, mat(0x6d7a52, 1));
for (let i = -20; i <= 20; i++) box(1.6, 0.012, 0.16, i * 4, 0.006, -3, mat(0xf2e3b8, 0.8));   // centre line dashes
// facades on the far side: pastel colonial fronts with windows, shutters, balconies, awnings
const FAC = [0xe98b6d, 0x5fb3a8, 0xf0c35e, 0x9fc98a, 0xd9787f, 0x6f9fd8, 0xf2a65a, 0xb48ad6];
const awnings = [];
for (let i = 0; i < 12; i++) {
  const w = 5 + 2 * hash1(i * 3), h = 6 + 6 * hash1(i * 7), x = -30 + i * 5.4, col = FAC[i % FAC.length];
  const tex = canvasTex(256, 384, g => { g.fillStyle = '#' + col.toString(16).padStart(6, '0'); g.fillRect(0, 0, 256, 384);
    for (let r = 0; r < 4; r++) for (let c = 0; c < 3; c++) { const x0 = 30 + c * 75, y0 = 30 + r * 90; g.fillStyle = '#2a2730'; g.fillRect(x0, y0, 44, 60);
      g.fillStyle = '#4d6b5a'; g.fillRect(x0 - 12, y0, 10, 60); g.fillRect(x0 + 46, y0, 10, 60); g.fillStyle = 'rgba(255,240,210,0.85)'; g.fillRect(x0 - 6, y0 + 62, 56, 5); } });
  const f = box(w, h, 4, x, h / 2, -11, new THREE.MeshStandardMaterial({ map: tex, roughness: 0.9 }));
  box(w + 0.2, 0.35, 4.2, x, h + 0.17, -11, mat(0xf3e6d0, 0.8));
  const aw = new THREE.Group(); aw.position.set(x, 2.8, -9.0); scene.add(aw); box(w * 0.8, 0.06, 1.3, 0, 0, 0.65, mat([0xc23b3b, 0x2f6fae, 0x3b8a4a, 0xe0a030][i % 4], 0.8), 0, aw).rotation.x = 0.28; awnings.push({ g: aw, i });
}
// near-side buildings west of him, so the street is a canyon running into the sunset
for (let i = 0; i < 6; i++) { const w = 5 + 2 * hash1(i * 13), h = 7 + 5 * hash1(i * 17), x = -9 - i * 5.6, col = FAC[(i + 3) % FAC.length];
  box(w, h, 4, x, h / 2, 7.2, mat(col, 0.9)); box(w + 0.2, 0.35, 4.2, x, h + 0.17, 7.2, mat(0xf3e6d0, 0.8));
  for (let r = 0; r < 3; r++) for (let c = 0; c < 2; c++) box(0.9, 1.2, 0.05, x - w / 4 + c * w / 2, 2.2 + r * 2.2, 5.18, mat(0x2a2730, 0.4)); }
// palm trees (trunk = a bent tube, fronds = arched leaves); they whip east when it stops
function palm(x, z, s) { const g = new THREE.Group(); g.position.set(x, 0.1, z); scene.add(g);
  const pts = []; for (let i = 0; i <= 8; i++) { const u = i / 8; pts.push(V(0.35 * Math.sin(u * 1.4) * s, u * 6.5 * s, 0)); }
  const trunk = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 24, 0.16 * s, 8), mat(0x8a6a4a, 0.95)); trunk.castShadow = true; g.add(trunk);
  const crown = new THREE.Group(); crown.position.copy(pts[8]); g.add(crown); const fronds = [];
  for (let k = 0; k < 9; k++) { const a = k / 9 * Math.PI * 2, f = new THREE.Group(); f.rotation.y = a; crown.add(f);
    const sh = new THREE.Shape(); sh.moveTo(0, 0); sh.quadraticCurveTo(1.2 * s, 0.35 * s, 2.6 * s, -0.6 * s); sh.quadraticCurveTo(1.2 * s, 0.05 * s, 0, 0);
    const leaf = new THREE.Mesh(new THREE.ShapeGeometry(sh, 10), new THREE.MeshStandardMaterial({ color: 0x3f7a3a, roughness: 0.8, side: THREE.DoubleSide })); leaf.rotation.x = -Math.PI / 2 + 0.25; leaf.castShadow = true; f.add(leaf); fronds.push({ f, a, k }); }
  return { g, crown, fronds, x }; }
const palms = [palm(-6.5, 3.4, 1.0), palm(5.0, -7.9, 1.1), palm(-3.0, -7.7, 0.95), palm(-15, 3.3, 1.05)];
// a lamppost, a cafe table and chair next to him, a newspaper stand
box(0.12, 4.2, 0.12, -2.2, 2.1, 3.6, mat(0x2a2a2e, 0.5, 0.6)); box(0.6, 0.12, 0.25, -2.0, 4.2, 3.6, mat(0x2a2a2e, 0.5, 0.6));
const table = new THREE.Group(); table.position.set(1.4, 0.13, 2.2); scene.add(table);
{ const tm = mat(0xf1efe8, 0.4); const top = new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.42, 0.04, 28), tm); top.position.y = 0.74; top.castShadow = true; table.add(top);
  const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.72, 10), mat(0x2a2a2e, 0.5, 0.6)); leg.position.y = 0.37; table.add(leg); }
const chair = new THREE.Group(); chair.position.set(2.0, 0.13, 2.5); scene.add(chair);
{ const cm = mat(0x2f6fae, 0.6); box(0.42, 0.04, 0.42, 0, 0.45, 0, cm, 0.01, chair); box(0.42, 0.45, 0.04, 0, 0.7, 0.2, cm, 0.01, chair); for (const [x, z] of [[-0.18, -0.18], [0.18, -0.18], [-0.18, 0.18], [0.18, 0.18]]) box(0.03, 0.45, 0.03, x, 0.22, z, mat(0x222222, 0.5, 0.6), 0, chair); }
// two cars on the road (stylized)
function car(x, z, col) { const g = new THREE.Group(); g.position.set(x, 0, z); scene.add(g); const pm = new THREE.MeshPhysicalMaterial({ color: col, roughness: 0.35, clearcoat: 0.8 });
  box(3.8, 0.7, 1.7, 0, 0.6, 0, pm, 0.25, g); box(2.0, 0.6, 1.5, -0.2, 1.15, 0, new THREE.MeshPhysicalMaterial({ color: 0x24303a, roughness: 0.1, metalness: 0.3 }), 0.22, g);
  for (const [wx, wz] of [[-1.25, 0.8], [1.25, 0.8], [-1.25, -0.8], [1.25, -0.8]]) { const w = new THREE.Mesh(new THREE.CylinderGeometry(0.34, 0.34, 0.24, 18).rotateX(Math.PI / 2), mat(0x18181a, 0.7)); w.position.set(wx, 0.34, wz); w.castShadow = true; g.add(w); }
  return g; }
const cars = [car(-6, -1.6, 0x2f8f8a), car(6.5, -4.4, 0xe8c24a)];
// his coffee cup (rides in his right hand, then flies), the coffee as droplets
const cup = new THREE.Group(); scene.add(cup);
{ const c = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.036, 0.12, 18), mat(0xffffff, 0.6)); cup.add(c); const sl = new THREE.Mesh(new THREE.CylinderGeometry(0.047, 0.04, 0.05, 18, 1, true), mat(0x9a6a40, 0.9)); sl.position.y = -0.005; cup.add(sl);
  const lid = new THREE.Mesh(new THREE.CylinderGeometry(0.048, 0.048, 0.015, 18), mat(0x3a2a22, 0.5)); lid.position.y = 0.065; cup.add(lid); }
const softTex = canvasTex(64, 64, g => { const gr = g.createRadialGradient(32, 32, 0, 32, 32, 31); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.45, 'rgba(255,255,255,0.45)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); });
function cloud(n, size, color, op) { const g = new THREE.BufferGeometry(); const p = new Float32Array(n * 3); g.setAttribute('position', new THREE.BufferAttribute(p, 3));
  const m = new THREE.Points(g, new THREE.PointsMaterial({ map: softTex, color, size, transparent: true, depthWrite: false, opacity: op })); m.frustumCulled = false; scene.add(m); return { m, p, n }; }
function setCloud(c, fn) { let k = 0; for (let i = 0; i < c.n; i++) { const q = fn(i); if (q) { c.p.set([q.x, q.y, q.z], k * 3); k++; } } for (let i = k; i < c.n; i++) c.p.set([0, -999, 0], i * 3); c.m.geometry.attributes.position.needsUpdate = true; c.m.visible = k > 0; }
const NST = 90, streaks = new THREE.InstancedMesh(new THREE.PlaneGeometry(1, 0.025), new THREE.MeshBasicMaterial({ color: 0xffe6c4, transparent: true, opacity: 0.55, depthWrite: false, side: THREE.DoubleSide }), NST); streaks.frustumCulled = false; scene.add(streaks); streaks.visible = false;
const coffee = cloud(60, 0.06, 0x6a3f1e, 0.95), dust = cloud(300, 0.9, 0xd8b48a, 0.22), debris = cloud(240, 0.12, 0x6f5a3a, 0.9), leaves = cloud(120, 0.22, 0x4a8a3c, 0.95);

// ------------------------------------------------------------------ the guy
const G = await loadGuy(THREE, '/char/guy', {});
scene.add(G.root); G.root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
const HIP = V(0, 0.95, 0), HOME = V(0.3, 0.95 + 0.13, 1.5);
function untwistSafe() { for (const S of ['R', 'L']) { const ua = G.bones['uarm' + S], ut = G.bones['uarmTwist' + S]; ua.quaternion.multiply(ut.quaternion); ut.quaternion.identity(); } G.untwist(); }
// ------------------------------------------------------------------ rig: Euler joints + human arm angles (zero = hanging, palm to thigh, thumb forward)
const LIMITS = {
  spine1: [[-30, 20], [-20, 20], [-15, 15]], spine2: [[-30, 20], [-20, 20], [-15, 15]], chest: [[-25, 20], [-20, 20], [-15, 15]],
  neck: [[-35, 35], [-50, 50], [-20, 20]], head: [[-30, 30], [-40, 40], [-20, 20]],
  thighR: [[-30, 120], [-30, 30], [-25, 45]], thighL: [[-30, 120], [-30, 30], [-45, 25]],
  shinR: [[-150, 0], [-5, 5], [-5, 5]], shinL: [[-150, 0], [-5, 5], [-5, 5]],
  footR: [[-45, 30], [-15, 15], [-15, 15]], footL: [[-45, 30], [-15, 15], [-15, 15]],
};
const ARM_LIM = [[-50, 170], [-25, 170], [-60, 60], [0, 145], [-80, 80], [-65, 70], [-25, 25]];   // + wrist bend, wrist side bend
function softc(x, lo, hi, knee = 6) { if (x > hi - knee) return hi - knee + knee * Math.tanh((x - (hi - knee)) / knee); if (x < lo + knee) return lo + knee - knee * Math.tanh(((lo + knee) - x) / knee); return x; }
const FINGERS = ['index', 'middle', 'ring', 'pinky'];
function curl(p, S, c, th = c) { for (const f of FINGERS) { p[f + '1' + S] = [0, 0, (S === 'R' ? -1 : 1) * c * 0.9]; p[f + '2' + S] = [0, 0, (S === 'R' ? -1 : 1) * c]; } p['thumb1' + S] = [0, 0, (S === 'R' ? -1 : 1) * th * 0.4]; return p; }
const A = (fl, ab, ro, el, pr = 0, wf = 0, wd = 0) => [fl, ab, ro, el, pr, wf, wd];
const P = {
  stand: { armR: A(6, 8, 0, 16), armL: A(6, 8, 0, 16), neck: [2, 0, 0] },
  spray: { armR: A(40, 12, 0, 50), armL: A(8, 10, 0, 22), spine1: [-8, 0, 0], spine2: [-6, 6, 0], neck: [-22, 12, 0], head: [-10, 6, 0], thighR: [4, 0, 2], thighL: [2, 0, -2] },
  recoil: { armR: A(26, 14, 0, 60), armL: A(30, 10, 0, 80), spine1: [6, 0, 0], spine2: [4, -6, 0], neck: [12, -20, 0], head: [6, -10, 0] },
  cough: { armR: A(20, 12, 0, 40), armL: A(40, 10, 0, 100), spine1: [-18, 0, 0], spine2: [-14, 0, 0], chest: [-8, 0, 0], neck: [-14, 0, 0], head: [-6, 0, 0], thighR: [10, 0, 2], thighL: [10, 0, -2], shinR: [-14, 0, 0], shinL: [-14, 0, 0] },
  sniff: { armR: A(20, 10, 0, 50), armL: A(6, 10, 0, 20), spine1: [-10, 0, 0], spine2: [-8, 8, 0], neck: [-18, 16, 0], head: [-6, 8, 0] },
  shrug: { armR: A(18, 16, 0, 60, 30), armL: A(14, 22, 0, 80, 40), neck: [6, 0, 0], head: [4, 0, 0] },
  walk: { armR: A(8, 8, 0, 20), armL: A(8, 8, 0, 20), spine1: [-4, 0, 0], neck: [-4, 0, 0] },
};
for (const k of Object.keys(P)) { curl(P[k], 'R', 26); curl(P[k], 'L', 26); }
const BONES = Object.keys(G.bones);
const qTmp = new THREE.Quaternion(), eTmp = new THREE.Euler();
const ARM0 = A(4, 8, 0, 14);
function eul(p, n) { return p[n] || (n === 'armR' || n === 'armL' ? ARM0 : [0, 0, 0]); }
function mixPose(a, b, k) { const o = {}; for (const n of new Set([...Object.keys(a), ...Object.keys(b)])) { const x = eul(a, n), y = eul(b, n); o[n] = x.map((v, i) => lerp(v, y[i] ?? 0, k)); } return o; }
function addPose(a, d) { const o = { ...a }; for (const [n, v] of Object.entries(d)) { const x = eul(o, n); o[n] = x.map((w, i) => w + (v[i] || 0)); } return o; }
function keyed(keys, t) { if (t <= keys[0][0]) return keys[0][1]; for (let i = 0; i < keys.length - 1; i++) { const [t0, a] = keys[i], [t1, b] = keys[i + 1]; if (t <= t1) return mixPose(a, b, sm((t - t0) / (t1 - t0))); } return keys[keys.length - 1][1]; }
function flail(T, amp, hz, seed) { return amp * (0.65 * Math.sin(2 * Math.PI * hz * T + seed) + 0.35 * Math.sin(2 * Math.PI * hz * 1.73 * T + seed * 2.1)); }
G.reset();
const ARMREST = {}, HANDREST = {};
for (const S of ['R', 'L']) {
  const af = G.REST['farm' + S].axis.clone();
  ARMREST[S] = { s: S === 'R' ? 1 : -1, a0: G.REST['uarm' + S].axis.clone(), af, hinge: new THREE.Vector3().crossVectors(af, V(0, 0, -1)).normalize() };
  const h = G.man.hands[S]; HANDREST[S] = { u: V(...h.u), n: V(...h.n), w: V(...h.w) };
}
const qAA = (ax, deg) => new THREE.Quaternion().setFromAxisAngle(ax, deg * D2R);
function armQuats(S, a) {                                       // [flex, abd, rot, el, pro, wristFlex, wristSide] -> local rotations
  const R_ = ARMREST[S], h = HANDREST[S], [flex, abd, rot, el, pro, wf = 0, wd = 0] = a;
  const rv = V(flex, 0, R_.s * abd); const ang = rv.length();
  const d = ang > 1e-6 ? V(0, -1, 0).applyQuaternion(qAA(rv.clone().normalize(), ang)) : V(0, -1, 0);
  const Lu = new THREE.Quaternion().setFromUnitVectors(R_.a0, d).multiply(qAA(R_.a0, R_.s * rot));
  const Lf = qAA(R_.hinge, el).multiply(qAA(R_.af, R_.s * pro));
  const Lh = qAA(h.w, R_.s * wf).multiply(qAA(h.n, R_.s * wd));                 // wrist: bend toward the palm / side bend
  return { Lu, Lf, Lh };
}
function setArm(S, a) {
  const { Lu, Lf, Lh } = armQuats(S, a);
  G.bones['uarm' + S].quaternion.copy(Lu); G.bones['uarmTwist' + S].quaternion.identity();
  G.bones['farm' + S].quaternion.copy(Lf); G.bones['farmTwist' + S].quaternion.identity(); G.bones['hand' + S].quaternion.copy(Lh);
}
let LAST = {};
function applyPose(p, root) {
  const lim = {};
  for (const n of BONES) {
    if (/^(uarm|uarmTwist|farm|farmTwist|hand)[RL]$/.test(n)) continue;
    const b = G.bones[n]; let e = eul(p, n);
    if (LIMITS[n]) e = e.map((v, i) => softc(v, LIMITS[n][i][0], LIMITS[n][i][1]));
    lim[n] = e; b.position.copy(G.REST[n].pos); b.quaternion.copy(G.REST[n].q).multiply(qTmp.setFromEuler(eTmp.set(e[0] * D2R, e[1] * D2R, e[2] * D2R)));
  }
  for (const S of ['R', 'L']) { const a = eul(p, 'arm' + S).map((v, i) => softc(v, ARM_LIM[i][0], ARM_LIM[i][1], i === 3 ? 4 : 5)); lim['arm' + S] = a; setArm(S, a); }
  const R = new THREE.Quaternion().setFromEuler(new THREE.Euler((root.tilt || 0) * D2R, (root.yaw || 0) * D2R, (root.roll || 0) * D2R, 'YXZ'));
  const hipP = V(root.x ?? HOME.x, (root.y ?? HOME.y) - (root.s || 0), root.z ?? HOME.z);
  G.root.quaternion.copy(R); G.root.position.copy(hipP).sub(HIP.clone().applyQuaternion(R));
  G.root.updateMatrixWorld(true);
  LAST = lim;
}
// ------------------------------------------------------------------ hands on things: solved over real joint ranges (car-space targets)
// target: { S, p: palm point (car space), n: which way the palm faces (car space), w?: which way the little-finger side points, curl }
const PALM = S => HANDREST[S].u.clone().multiplyScalar(0.06).addScaledVector(HANDREST[S].n, 0.012);   // palm centre (hand-rest offset)
const _m = new THREE.Matrix4(), _q = new THREE.Quaternion();
function torsoInside(p) {                                       // depth of a car-space point inside his trunk (soft column)
  const c = G.bones.chest.getWorldPosition(new THREE.Vector3()).applyMatrix4(carInv()), sp = G.bones.spine1.getWorldPosition(new THREE.Vector3()).applyMatrix4(carInv());
  if (p.y > c.y + 0.22 || p.y < sp.y - 0.2) return 0;
  const ex = (p.x - c.x) / 0.17, ez = (p.z - c.z) / 0.13; const r = Math.hypot(ex, ez); return r < 1 ? (1 - r) * 0.13 : 0;
}
let _carInv = new THREE.Matrix4(); const carInv = () => _carInv;   // identity here: targets are in room space
function handFK(S, a) {                                         // car-space palm point, palm normal, little-finger direction
  setArm(S, a); const hb = G.bones['hand' + S];
  G.bones['uarm' + S].updateMatrixWorld(true);
  const M = _m.copy(_carInv).multiply(hb.matrixWorld); const qh = _q.setFromRotationMatrix(M);   // bones rest unrotated: bone-local axes = rest axes
  return { p: PALM(S).applyMatrix4(M), n: HANDREST[S].n.clone().applyQuaternion(qh), w: HANDREST[S].w.clone().applyQuaternion(qh), u: HANDREST[S].u.clone().applyQuaternion(qh),
    el: G.bones['farm' + S].getWorldPosition(new THREE.Vector3()).applyMatrix4(_carInv),
    sh: G.bones['uarm' + S].getWorldPosition(new THREE.Vector3()).applyMatrix4(_carInv) };
}
const MEM = {};
function solveHand(tg, key, frame) {
  const S = tg.S;
  const cost = a => { const f = handFK(S, a);
    let c = f.p.distanceToSquared(tg.p) / (0.006 * 0.006);
    if (tg.n) c += (1 - f.n.dot(tg.n)) * 40;
    if (tg.w) c += (1 - f.w.dot(tg.w)) * 25;
    if (tg.u) c += (1 - f.u.dot(tg.u)) * 25;
    for (let i = 0; i < 7; i++) { const [lo, hi] = ARM_LIM[i], mid = [20, 15, 0, 60, 0, 0, 0][i]; c += 0.6 * ((a[i] - mid) / (hi - lo)) ** 2; }
    const ins = torsoInside(f.el) + torsoInside(f.el.clone().lerp(f.p, 0.5)); c += (ins / 0.01) ** 2;
    if (f.el.y > f.sh.y + 0.08) c += ((f.el.y - f.sh.y - 0.08) / 0.02) ** 2;
    if (prev) for (let i = 0; i < 7; i++) c += ((a[i] - prev[i]) / 3) ** 2;
    if (typeof handExtra === 'function') c += handExtra(S, f);           // the scene's solids (seats, armrests): keep the arm out of them
    return c; };
  const m = MEM[key]; const prev = m && m.frame === frame - 1 ? m.a : null;
  const COLD = [A(40, 15, 0, 80, 0), A(60, 25, 20, 60, 40), A(30, 40, -20, 100, -30), A(80, 10, 0, 110, 60), A(50, 30, 30, 40, 70), A(20, 20, -30, 120, -60), A(60, 10, -10, 100, 75), A(40, 20, 10, 90, -75)];
  const seeds = prev ? [prev] : COLD;
  let best = null;
  for (const s0 of seeds) {
    let a = s0.map((v, i) => clamp(v, ARM_LIM[i][0], ARM_LIM[i][1])), ca = cost(a);
    for (let step = prev ? 4 : 16; step >= 0.25; step /= 2) { let imp = true, g = 0;
      while (imp && g++ < 10) { imp = false; for (let i = 0; i < 7; i++) for (const sg of [1, -1]) { const b = a.slice(); b[i] = clamp(b[i] + sg * step, ARM_LIM[i][0], ARM_LIM[i][1]); const cb = cost(b); if (cb < ca - 1e-9) { a = b; ca = cb; imp = true; } } } }
    if (!best || ca < best.c) best = { a, c: ca };
  }
  if (prev && best.c > 20) {                                     // warm start stuck (the target turned the hand past what small steps reach): try the cold seeds too
    for (const s0 of COLD) { let a = s0.map((v, i) => clamp(v, ARM_LIM[i][0], ARM_LIM[i][1])), ca = cost(a);
      for (let step = 16; step >= 0.25; step /= 2) { let imp = true, g = 0;
        while (imp && g++ < 10) { imp = false; for (let i = 0; i < 7; i++) for (const sg of [1, -1]) { const b = a.slice(); b[i] = clamp(b[i] + sg * step, ARM_LIM[i][0], ARM_LIM[i][1]); const cb = cost(b); if (cb < ca - 1e-9) { a = b; ca = cb; imp = true; } } } }
      if (ca < best.c) best = { a, c: ca }; } }
  MEM[key] = { frame, a: best.a }; return best;
}


// ------------------------------------------------------------------ the story of the sample shot
const SLOW = 400;                                               // shown slowed down 400x: 1,000 mph (447 m/s) -> 1.1 m/s on screen
const VEL = 447 / SLOW;
const yawQ = deg => new THREE.Quaternion().setFromAxisAngle(V(0, 1, 0), deg * D2R);
const go = t => Math.max(0, t - TS) * VEL * smooth(TS, TS + 0.12, t);      // how far a loose thing has moved east since the stop
const FEET = { R: V(HOME.x - 0.11, 0.232, HOME.z + 0.02), L: V(HOME.x + 0.11, 0.232, HOME.z - 0.02) };
function guyAt(t) {
  const k = smooth(TS, TS + 0.35, t), a = Math.max(0, t - TS);
  let pose = addPose(P.stand, { neck: [-4 + 6 * Math.sin(t * 1.3), 0, 0] }), root = { yaw: 180 }, face = { smile: 0.35 * (1 - k), blink: 0 };
  const sip = smooth(0.1, 0.55, t) * (1 - smooth(0.85, 1.2, t));
  let hands = [{ S: 'R', p: V(HOME.x - 0.17, 1.28, HOME.z + 0.26).lerp(V(HOME.x - 0.06, 1.55, HOME.z + 0.2), sip), n: V(1, 0, 0.2).normalize(), u: V(0, 0.2, 1).normalize(), c: 68 }];
  pose = addPose(pose, { neck: [8 * sip, 0, 0], head: [6 * sip, 0, 0] });
  if (t > TS) {                                                 // the ground stops under him: he pitches east and flies, flailing
    const fl = (amp, hz, s) => flail(a, amp, hz, s) * k;
    pose = addPose(P.stand, { armR: [70 * k + fl(30, 1.6, 1), 60 * k + fl(25, 1.3, 2), 0, 40 * k + fl(30, 1.9, 3), 0], armL: [90 * k + fl(30, 1.4, 4), 80 * k + fl(25, 1.7, 5), 0, 30 * k + fl(30, 1.5, 6), 0],
      thighR: [20 * k + fl(25, 1.2, 7), 0, -10 * k], thighL: [-15 * k + fl(25, 1.1, 8), 0, 20 * k], shinR: [-40 * k + fl(20, 1.3, 9), 0, 0], shinL: [-20 * k + fl(20, 1.4, 10), 0, 0],
      spine1: [-10 * k, 0, 8 * k], neck: [10 * k, -20 * k, 0], head: [6 * k, -10 * k, 0] });
    root = { yaw: 180 - 25 * k, roll: -(70 * smooth(TS, TS + 0.6, t) + 40 * a), x: HOME.x + go(t), y: HOME.y + 0.45 * smooth(TS + 0.05, TS + 0.6, t) + 0.15 * Math.sin(a * 2.2) * k };
    hands = [];
    face = { fear: 1 * k, jaw: 0.75 * k, browIn: 0.3 * k, blink: 0, look: [0.3, 0.1] };
  }
  return { pose, root, face, hands, feet: t <= TS + 0.06 };
}
function camAt(t) {                                              // low in the street east of him, looking west into the sunset: everything launched east comes at us
  const u = smooth(TS, TS + 0.6, t), a = Math.max(0, t - TS);
  const hp = G.bones.hips.getWorldPosition(new THREE.Vector3());
  const pos = V(3.9 - 0.3 * (t / TS) * (1 - u), 1.35, 2.7).add(V(0.85 * a + 0.3 * u, 0.12 * u, 0.15 * a));
  const tgt = V(-2.2, 1.45, 1.05).lerp(hp.clone().add(V(-2.6, 0.35, -0.2)), u * 0.85);
  const sh = Math.exp(-a * 2.5) * (t > TS ? 1 : 0) * 0.07;
  pos.add(V(vn1(t * 14, 1) * sh * 0.5, vn1(t * 14, 2) * sh, vn1(t * 14, 3) * sh));
  return { pos, tgt, fov: lerp(48, 54, u) };
}

// ------------------------------------------------------------------ update
let LASTF = -10;
function update(t, frame) {
  const g = guyAt(t), a = Math.max(0, t - TS), k = smooth(TS, TS + 0.25, t);
  applyPose(g.pose, { ...g.root, x: g.root.x ?? HOME.x, y: g.root.y ?? HOME.y, z: HOME.z });
  if (g.feet) for (const S of ['R', 'L']) G.legIK(S, FEET[S], FEET[S].clone().add(V(0, 0.45, 1.0)), yawQ(180));
  G.root.updateMatrixWorld(true);
  for (const h of g.hands) { const sol = solveHand(h, 'h' + h.S, frame); setArm(h.S, sol.a);
    const pp = {}; curl(pp, h.S, h.c ?? 30); for (const [n, e] of Object.entries(pp)) G.bones[n].quaternion.copy(G.REST[n].q).multiply(qTmp.setFromEuler(eTmp.set(e[0] * D2R, e[1] * D2R, e[2] * D2R))); }
  G.root.updateMatrixWorld(true); untwistSafe(); G.face(g.face); G.root.updateMatrixWorld(true);
  // the cup: in his hand, then it keeps going (with a little spin) while the coffee sprays out of it
  const hb = G.bones.handR; hb.updateMatrixWorld(true);
  if (t <= TS) { const q = hb.getWorldQuaternion(new THREE.Quaternion()); cup.position.copy(PALM('R').applyMatrix4(hb.matrixWorld)).addScaledVector(HANDREST.R.n.clone().applyQuaternion(q), 0.05); cup.rotation.set(0, 0, 0); CUP0 = cup.position.clone(); }
  else { cup.position.copy(CUP0).add(V(go(t) * 1.04, 0.25 * smooth(TS, TS + 0.8, t) - 0.08 * a * a, 0.1 * a)); cup.rotation.set(0.4 * a, 0, -2.2 * a); }
  setCloud(coffee, i => { if (t <= TS + 0.05) return null; const f = hash1(i) , age = a * (0.3 + 0.7 * f); return cup.position.clone().add(V(-0.15 - 0.6 * age * f, 0.08 + 0.3 * age - 0.25 * age * age * f, (hash1(i * 3) - 0.5) * 0.25 * age)); });
  // cars slide east and tip; the table and chair tumble; awnings tear and flutter
  cars.forEach((c, i) => { c.position.x = [-6, 6.5][i] + go(t) * (0.98 + 0.03 * i); c.rotation.z = -0.55 * smooth(TS + 0.1, TS + 1.4, t) * (i ? 0.7 : 1) - 0.25 * a * a * (i ? 0.3 : 0.5); c.position.y = 0.4 * smooth(TS + 0.2, TS + 1.2, t) * (i ? 0.6 : 1); });
  table.position.x = 1.4 + go(t) * 1.02; table.rotation.z = -1.4 * smooth(TS, TS + 0.9, t) - 1.2 * a; table.position.y = 0.13 + 0.3 * smooth(TS, TS + 0.6, t);
  chair.position.x = 2.0 + go(t) * 1.0; chair.rotation.set(0.6 * a, 0.4 * a, -2.0 * a); chair.position.y = 0.13 + 0.45 * smooth(TS, TS + 0.5, t);
  for (const aw of awnings) { const loose = aw.i % 4 === 1; aw.g.rotation.x = -0.25 * k + 0.06 * Math.sin(t * 30 + aw.i) * k; aw.g.rotation.z = loose ? -1.2 * a : -0.12 * k; aw.g.position.x = (-30 + aw.i * 5.4) + (loose ? go(t) * 0.95 : 0); aw.g.position.y = 2.8 + (loose ? 0.6 * smooth(0, 0.5, a) : 0); }
  // palms whip east; fronds tear off and fly
  for (const p of palms) { p.g.rotation.z = -0.55 * smooth(TS, TS + 0.5, t) - 0.04 * Math.sin(t * 22) * k;
    for (const f of p.fronds) { const off = f.k % 2 === 0 && t > TS + 0.15 + 0.05 * f.k; f.f.rotation.z = off ? 0 : -0.8 * k; f.f.visible = !off; } }
  setCloud(leaves, i => { if (t <= TS + 0.15) return null; const p = palms[i % 4], age = a - 0.05 * (i % 9); if (age < 0) return null;
    return V(p.x + 0.6 + go(t) * (0.8 + 0.4 * hash1(i)), 6.0 + (hash1(i * 2) - 0.5) * 2 - 0.4 * age, 3.2 + (hash1(i * 5) - 0.5) * 3); });
  // dust and grit: the air moves too; long streams of it pour east off the street
  dust.m.visible = false;
  streaks.visible = t > TS; if (streaks.visible) { const m4 = new THREE.Matrix4(); for (let i = 0; i < NST; i++) { const len = 0.6 + 1.6 * hash1(i * 5);
      const x = ((-14 + 30 * hash1(i * 3) + go(t) * (1.0 + 0.6 * hash1(i * 7)) + 40) % 40) - 14; m4.compose(V(x, 0.3 + 3.2 * hash1(i * 11), -7 + 13 * hash1(i * 13)), new THREE.Quaternion(), V(len * smooth(0, 0.4, a), 1, 1)); streaks.setMatrixAt(i, m4); }
    streaks.instanceMatrix.needsUpdate = true; }
  setCloud(debris, i => { if (t <= TS) return null; return V(-10 + 22 * hash1(i * 3) + go(t) * (0.7 + 0.6 * hash1(i * 5)), 0.15 + 1.6 * hash1(i * 7) * smooth(0, 0.6, a), -6 + 9 * hash1(i * 11)); });
  skyU.uT.value = t; skyU.uStreak.value = smooth(TS, TS + 1.2, t) * (1 + a);
  const C = camAt(t); camera.position.copy(C.pos); camera.lookAt(C.tgt); camera.fov = C.fov; camera.updateProjectionMatrix();
}
let CUP0 = V(0, 0, 0);

// ------------------------------------------------------------------ the painting pass: Kuwahara (paint blobs) -> paint edges, canvas, grade
const RAD = Math.max(3, Math.round(7 * W / 720));        // on the half-size image: about 10 px brush blobs at full size
const Kuwahara = { uniforms: { tDiffuse: { value: null }, uRes: { value: new THREE.Vector2(W, H) } },
  vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
  fragmentShader: `#define R ${RAD}
    uniform sampler2D tDiffuse; uniform vec2 uRes; varying vec2 vUv;
    void main(){ vec2 px = 1.0 / uRes; vec3 m0 = vec3(0), m1 = vec3(0), m2 = vec3(0), m3 = vec3(0), s0 = vec3(0), s1 = vec3(0), s2 = vec3(0), s3 = vec3(0);
      for (int j = -R; j <= 0; j++) for (int i = -R; i <= 0; i++) { vec3 c = texture2D(tDiffuse, vUv + vec2(i, j) * px).rgb; m0 += c; s0 += c * c; }
      for (int j = -R; j <= 0; j++) for (int i = 0; i <= R; i++) { vec3 c = texture2D(tDiffuse, vUv + vec2(i, j) * px).rgb; m1 += c; s1 += c * c; }
      for (int j = 0; j <= R; j++) for (int i = 0; i <= R; i++) { vec3 c = texture2D(tDiffuse, vUv + vec2(i, j) * px).rgb; m2 += c; s2 += c * c; }
      for (int j = 0; j <= R; j++) for (int i = -R; i <= 0; i++) { vec3 c = texture2D(tDiffuse, vUv + vec2(i, j) * px).rgb; m3 += c; s3 += c * c; }
      float n = float((R + 1) * (R + 1)); float best = 1e9; vec3 col = vec3(0);
      m0 /= n; s0 = abs(s0 / n - m0 * m0); float v = s0.r + s0.g + s0.b; if (v < best) { best = v; col = m0; }
      m1 /= n; s1 = abs(s1 / n - m1 * m1); v = s1.r + s1.g + s1.b; if (v < best) { best = v; col = m1; }
      m2 /= n; s2 = abs(s2 / n - m2 * m2); v = s2.r + s2.g + s2.b; if (v < best) { best = v; col = m2; }
      m3 /= n; s3 = abs(s3 / n - m3 * m3); v = s3.r + s3.g + s3.b; if (v < best) { best = v; col = m3; }
      gl_FragColor = vec4(col, 1.0); }` };
const Paint = { uniforms: { tDiffuse: { value: null }, uRes: { value: new THREE.Vector2(W, H) }, uT: { value: 0 } },
  vertexShader: Kuwahara.vertexShader,
  fragmentShader: `uniform sampler2D tDiffuse; uniform vec2 uRes; uniform float uT; varying vec2 vUv;
    float hh(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
    float vn(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f*f*(3.0-2.0*f); return mix(mix(hh(i), hh(i+vec2(1,0)), u.x), mix(hh(i+vec2(0,1)), hh(i+vec2(1,1)), u.x), u.y); }
    float L(vec2 o){ return dot(texture2D(tDiffuse, vUv + o / uRes).rgb, vec3(0.299, 0.587, 0.114)); }
    void main(){ vec3 c = texture2D(tDiffuse, vUv).rgb;
      float gx = L(vec2(1,0)) - L(vec2(-1,0)) + 0.5 * (L(vec2(1,1)) - L(vec2(-1,1)) + L(vec2(1,-1)) - L(vec2(-1,-1)));
      float gy = L(vec2(0,1)) - L(vec2(0,-1)) + 0.5 * (L(vec2(1,1)) - L(vec2(1,-1)) + L(vec2(-1,1)) - L(vec2(-1,-1)));
      float e = smoothstep(0.06, 0.22, length(vec2(gx, gy)));
      c = mix(c, c * vec3(0.55, 0.45, 0.42), e * 0.55);                                   // dark paint edges
      vec2 P = vUv * uRes; float hold = floor(uT * 8.0);                                   // canvas weave + brush streaks (stroke pattern changes 8x a second, like hand-painted frames)
      float weave = 0.5 + 0.25 * sin(P.x * 1.9) * sin(P.y * 1.9) + 0.25 * hh(floor(P * 0.5));
      float stroke = vn(vec2(P.x * 0.045 + P.y * 0.02, P.y * 0.012 - P.x * 0.008) + hold * 3.1) * 0.6 + vn(P * vec2(0.09, 0.03) + hold) * 0.4;
      c *= 0.93 + 0.07 * weave; c *= 0.94 + 0.12 * stroke;
      float l = dot(c, vec3(0.299, 0.587, 0.114)); c = mix(vec3(l), c, 1.18);           // a bit more color
      c = mix(vec3(0.11, 0.07, 0.05), vec3(1.0), c) ;                                    // warm brown in the darks, like an oil ground showing through
      vec2 d = vUv - 0.5; c *= 1.0 - 0.35 * dot(d * vec2(1.2, 0.9), d * vec2(1.2, 0.9));
      gl_FragColor = vec4(c, 1.0); }` };
const composer = new EffectComposer(renderer, new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: 4 }));
composer.setPixelRatio(1); composer.setSize(W, H); composer.renderToScreen = false;
composer.addPass(new RenderPass(scene, camera)); composer.addPass(new OutputPass());
const HW = Math.round(W / 2), HH = Math.round(H / 2);
const rtHalf = new THREE.WebGLRenderTarget(HW, HH, { type: THREE.HalfFloatType, minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter });
const quadCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1), quadGeo = new THREE.PlaneGeometry(2, 2);
const kuwMat = new THREE.ShaderMaterial({ ...Kuwahara, uniforms: { tDiffuse: { value: null }, uRes: { value: new THREE.Vector2(HW, HH) } }, depthTest: false, depthWrite: false });
const paintMat = new THREE.ShaderMaterial({ uniforms: { tPaint: { value: null }, tFull: { value: null }, uRes: { value: new THREE.Vector2(W, H) }, uT: { value: 0 } }, depthTest: false, depthWrite: false,
  vertexShader: Kuwahara.vertexShader,
  fragmentShader: `uniform sampler2D tPaint, tFull; uniform vec2 uRes; uniform float uT; varying vec2 vUv;
    float hh(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
    float vn(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f*f*(3.0-2.0*f); return mix(mix(hh(i), hh(i+vec2(1,0)), u.x), mix(hh(i+vec2(0,1)), hh(i+vec2(1,1)), u.x), u.y); }
    float Lp(vec2 o){ return dot(texture2D(tPaint, vUv + o / uRes).rgb, vec3(0.299, 0.587, 0.114)); }
    float Lf(vec2 o){ return dot(texture2D(tFull, vUv + o / uRes).rgb, vec3(0.299, 0.587, 0.114)); }
    float Lq(vec2 P){ return dot(texture2D(tPaint, P / uRes).rgb, vec3(0.299, 0.587, 0.114)); }
    vec2 flow(vec2 P){ vec2 g = vec2(Lq(P + vec2(5, 0)) - Lq(P - vec2(5, 0)), Lq(P + vec2(0, 5)) - Lq(P - vec2(0, 5)));
      float gl = length(g), ang = 6.2832 * (vn(P * 0.0028 + 3.0) * 1.3 + vn(P * 0.008) * 0.35);
      vec2 sw = vec2(cos(ang), sin(ang)), al = gl > 1e-4 ? vec2(-g.y, g.x) / gl : sw;
      if (dot(al, sw) < 0.0) al = -al;
      return normalize(mix(sw, al, smoothstep(0.01, 0.06, gl))); }
    void main(){
      vec3 c = texture2D(tPaint, vUv).rgb;
      // brush strokes: fine grain smeared along a flow field (line integral convolution). The flow follows the forms where there are edges,
      // and swirls slowly in the open areas (sky, road) like a Van Gogh sky.
      vec2 P = vUv * uRes; float hold = floor(uT * 8.0);                                   // the strokes re-paint 8x a second, like a hand-painted film
      float lic = 0.0, wsum = 0.0; vec2 q = P, q2 = P;
      for (int s = 0; s < 9; s++) {
        float w = 1.0 - float(s) / 9.0;
        lic += hh(floor(q * 0.55) + hold * 13.0) * w + hh(floor(q2 * 0.55) + hold * 13.0) * w; wsum += 2.0 * w;
        vec2 f1 = flow(q), f2 = flow(q2); q += f1 * 1.6; q2 -= f2 * 1.6; }
      lic = (lic / wsum - 0.5) * 3.2;                                                       // streak contrast
      float strokes = clamp(0.5 + lic, 0.0, 1.0);
      c *= 0.92 + 0.16 * strokes;
      c += vec3(1.0, 0.93, 0.8) * smoothstep(0.75, 1.0, strokes) * 0.03;                   // a little light on the paint ridges
      // dark paint edges where the full-res image has strong edges (thin, warm, not black)
      float ex = Lf(vec2(1,0)) - Lf(vec2(-1,0)), ey = Lf(vec2(0,1)) - Lf(vec2(0,-1));
      c = mix(c, c * vec3(0.5, 0.38, 0.32), smoothstep(0.08, 0.3, length(vec2(ex, ey))) * 0.5);
      // canvas weave and impasto light
      float weave = 0.5 + 0.25 * sin(P.x * 1.7) * sin(P.y * 1.7) + 0.25 * hh(floor(P * 0.5));
      c *= 0.9 + 0.1 * weave; c += 0.035 * smoothstep(0.6, 1.0, strokes) * vec3(1.0, 0.95, 0.85);
      float l = dot(c, vec3(0.299, 0.587, 0.114)); c = mix(vec3(l), c, 1.22);
      c = mix(vec3(0.13, 0.08, 0.06), vec3(1.0, 0.98, 0.94), c);                         // warm umber ground in the darks, a creamy top
      vec2 d = vUv - 0.5; c *= 1.0 - 0.45 * dot(d * vec2(1.1, 0.85), d * vec2(1.1, 0.85));
      gl_FragColor = vec4(clamp(c, 0.0, 1.0), 1.0); }` });
const kuwQuad = new THREE.Mesh(quadGeo, kuwMat), paintQuad = new THREE.Mesh(quadGeo, paintMat);
const PAINT = Q.get('paint') !== '0';
const outCopy = new THREE.Mesh(quadGeo, new THREE.ShaderMaterial({ uniforms: { t: { value: null } }, vertexShader: Kuwahara.vertexShader, fragmentShader: 'uniform sampler2D t; varying vec2 vUv; void main(){ gl_FragColor = texture2D(t, vUv); }', depthTest: false }));
const draw = t => { composer.render(); const src = composer.readBuffer.texture;
  if (!PAINT) { outCopy.material.uniforms.t.value = src; renderer.setRenderTarget(null); renderer.render(outCopy, quadCam); return; }
  kuwMat.uniforms.tDiffuse.value = src; renderer.setRenderTarget(rtHalf); renderer.render(kuwQuad, quadCam);
  paintMat.uniforms.tPaint.value = rtHalf.texture; paintMat.uniforms.tFull.value = src; paintMat.uniforms.uT.value = t; renderer.setRenderTarget(null); renderer.render(paintQuad, quadCam); };

// ------------------------------------------------------------------ frame I/O
const gl = renderer.getContext(), px = new Uint8Array(W * H * 4);
function stepTo(i) { if (i !== LASTF + 1) for (let j = Math.max(0, i - 12); j < i; j++) update(j / FPS, j); update(i / FPS, i); LASTF = i; }
window.renderAll = async (f0, f1) => { for (let i = f0; i < f1; i++) { stepTo(i); draw(i / FPS); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); await fetch('/frame', { method: 'POST', body: px }); } return 'ok'; };
window.renderAtT = t => { const i = Math.round(t * FPS); stepTo(i); draw(t); return renderer.domElement.toDataURL('image/png'); };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS);
window.READY = true;
