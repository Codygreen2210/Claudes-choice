// "The Earth stops spinning for one second" - a 3D Short in a painterly style (a moving oil painting)
//   estop.html?w=1080&h=1920            (times from estop/times.json; one shot per narration line)
// Beats: 0 the launch, close (hook) | 1 the painted Earth from space, the equator glowing, 1,000 mph | 2 the calm street: he sips his coffee
//        3 the ground stops, he doesn't (low side view) | 4 flying east faster than sound (vapor cone) over the town
//        5 the street tears loose: cars, palms, houses | 6 a wall of wind over the town | 7 a tsunami hits the coast
//        8 the North Pole: he sips his coffee, fine | 9 the calm street, the stop at the very end (loops into the launch)
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { loadGuy } from '/guy3d.js';

const Q = new URLSearchParams(location.search);
const W = +Q.get('w') || 720, H = +Q.get('h') || 1280;
const FPS = 30;
const TIMES = await (await fetch('/estop/times.json')).json();
const B = TIMES.starts, DUR = TIMES.durs, TOTAL = TIMES.total;
const beatAt = t => { let i = 0; for (let k = 0; k < B.length; k++) if (t >= B[k]) i = k; return i; };
const TS = 1.3;                                                 // street time when the ground stops (each street beat maps its own time onto street time)
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
const skyU = { uSun: { value: SUNDIR }, uT: { value: 0 }, uStreak: { value: 0 }, uPolar: { value: 0 }, uDust: { value: 0 } };
const skyMat = new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false, uniforms: skyU,
  vertexShader: 'varying vec3 vD; void main(){ vD = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
  fragmentShader: `varying vec3 vD; uniform vec3 uSun; uniform float uT, uStreak, uPolar, uDust;
    float hh(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
    float vn(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f*f*(3.0-2.0*f); return mix(mix(hh(i), hh(i+vec2(1,0)), u.x), mix(hh(i+vec2(0,1)), hh(i+vec2(1,1)), u.x), u.y); }
    void main(){ float h = clamp(vD.y, -0.1, 1.0);
      vec3 c = mix(vec3(1.0, 0.62, 0.36), vec3(0.98, 0.78, 0.55), smoothstep(0.0, 0.12, h)); c = mix(c, vec3(0.42, 0.56, 0.86), smoothstep(0.1, 0.6, h));
      float s = max(dot(normalize(vD), uSun), 0.0); c += vec3(1.0, 0.75, 0.4) * (pow(s, 6.0) * 0.5 + pow(s, 400.0) * 3.0);
      vec2 cp = vec2(atan(vD.x, -vD.z) * 3.0 - uStreak * 2.5, vD.y * 9.0);                     // clouds (they streak east when it stops)
      float cl = vn(cp * vec2(1.0 / (1.0 + uStreak * 6.0), 1.0) + vec2(uT * 0.02, 0.0)) * 0.65 + vn(cp * 2.3) * 0.35;
      c = mix(c, mix(vec3(1.0, 0.85, 0.7), vec3(1.0, 0.6, 0.45), 1.0 - smoothstep(0.05, 0.4, h)), smoothstep(0.55, 0.75, cl) * smoothstep(0.02, 0.15, h) * 0.85);
      c = mix(c, vec3(0.78, 0.6, 0.42), uDust * (1.0 - smoothstep(0.0, 0.5, h)));                      // dust-choked low sky (the wind beat)
      if (uPolar > 0.0) { vec3 pc = mix(vec3(0.55, 0.7, 0.9), vec3(0.06, 0.1, 0.25), smoothstep(0.0, 0.6, h));           // polar twilight
        float band = sin(atan(vD.x, -vD.z) * 3.0 + vn(vec2(atan(vD.x, -vD.z) * 4.0, uT * 0.3)) * 3.0) * 0.5 + 0.5;
        float aur = smoothstep(0.15, 0.3, h) * (1.0 - smoothstep(0.35, 0.75, h)) * smoothstep(0.4, 0.95, band) * (0.6 + 0.4 * vn(vec2(vD.x * 20.0, uT * 0.5)));
        pc += vec3(0.2, 1.0, 0.55) * aur * 0.8 + vec3(0.6, 0.3, 0.9) * aur * smoothstep(0.3, 0.6, h) * 0.4; c = mix(c, pc, uPolar); }
      gl_FragColor = vec4(pow(c, vec3(2.2)), 1.0); }` });
const sky = new THREE.Mesh(new THREE.SphereGeometry(800, 48, 24), skyMat); sky.frustumCulled = false; scene.add(sky);   // follows the camera (stages are far apart)
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
// two small wooden houses on the near side, east of him
const houses = [];
for (const [x, col] of [[11, 0xf1d9a8], [18.5, 0xa9d6c9]]) { const g = new THREE.Group(); g.position.set(x, 0.13, 7.0); scene.add(g);
  box(5, 3.2, 4.4, 0, 1.6, 0, mat(col, 0.85), 0.05, g);
  const roof = new THREE.Mesh(new THREE.ConeGeometry(3.9, 1.8, 4, 1).rotateY(Math.PI / 4), mat(0xb8513a, 0.8)); roof.scale.set(1, 1, 0.82); roof.position.y = 4.1; roof.castShadow = true; g.add(roof);
  box(0.9, 1.9, 0.08, -0.8, 0.95, -2.22, mat(0x6a4a32, 0.8), 0, g); box(1.0, 0.9, 0.06, 1.2, 1.9, -2.22, mat(0x2a3440, 0.3), 0, g);
  const slab = box(5.6, 0.14, 5.0, x, 0.07, 7.0, mat(0x9a9188, 0.9)); houses.push({ g, x, slab }); }
// the town around the street (seen from the air): blocks of colored buildings, cross streets
const town = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 1, 1), new THREE.MeshStandardMaterial({ roughness: 0.9 }), 700); town.castShadow = true; town.receiveShadow = true;
{ const m4 = new THREE.Matrix4(); let k = 0;
  for (let gx = -150; gx <= 150; gx += 14) for (let gz = -140; gz <= 140; gz += 14) { if (Math.abs(gz) < 26 && Math.abs(gx) < 60) continue; if (k >= 700) break;
    for (let q = 0; q < 2 && k < 700; q++) { const w = 4 + 5 * hash1(gx * 3 + gz + q), h2 = 3 + 9 * hash1(gx + gz * 7 + q), d = 4 + 5 * hash1(gx * 5 - gz + q);
      m4.compose(V(gx + (q ? 3.5 : -3) + hash1(gx + q) * 2, h2 / 2, gz + (hash1(gz + q) - 0.5) * 4), new THREE.Quaternion(), V(w, h2, d)); town.setMatrixAt(k, m4);
      town.setColorAt(k, new THREE.Color(FAC[(k * 7 + q) % FAC.length])); k++; } }
  town.count = k; scene.add(town); }
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
const table = new THREE.Group(); table.position.set(1.4, 0.13, 3.05); scene.add(table);
{ const tm = mat(0xf1efe8, 0.4); const top = new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.42, 0.04, 28), tm); top.position.y = 0.74; top.castShadow = true; table.add(top);
  const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.72, 10), mat(0x2a2a2e, 0.5, 0.6)); leg.position.y = 0.37; table.add(leg); }
const chair = new THREE.Group(); chair.position.set(2.2, 0.13, 3.55); scene.add(chair);
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

// ------------------------------------------------------------------ stages away from the street: the Earth from space, the coast, the North Pole
// (each is a group far from the others; the sky sphere follows the camera, and each stage sets its own sky look)
const SPACE = V(0, 0, -4000), COAST = V(4000, 0, 0), POLE = V(-4000, 0, 0);
// --- the painted Earth (beat 1): land / ocean / ice from noise, a cloud shell, an atmosphere rim, the glowing equator with arrows running east
const space = new THREE.Group(); space.position.copy(SPACE); scene.add(space);
const starTex = canvasTex(1024, 1024, g => { g.fillStyle = '#05060d'; g.fillRect(0, 0, 1024, 1024); for (let i = 0; i < 900; i++) { const r = Math.random() < 0.06 ? 1.6 : 0.8; g.fillStyle = `rgba(255,${230 + Math.random() * 25 | 0},${200 + Math.random() * 55 | 0},${0.4 + Math.random() * 0.6})`; g.beginPath(); g.arc(Math.random() * 1024, Math.random() * 1024, r, 0, 6.3); g.fill(); } });
const stars = new THREE.Mesh(new THREE.SphereGeometry(300, 32, 16), new THREE.MeshBasicMaterial({ map: starTex, side: THREE.BackSide, toneMapped: false })); space.add(stars);
const ER = 6;
const earthU = { uRot: { value: 0 }, uSun: { value: V(-0.85, 0.3, 0.45).normalize() } };
const earth = new THREE.Mesh(new THREE.SphereGeometry(ER, 96, 64), new THREE.ShaderMaterial({ uniforms: earthU,
  vertexShader: 'varying vec3 vN, vP; void main(){ vN = normalize(mat3(modelMatrix) * normal); vP = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
  fragmentShader: `varying vec3 vN, vP; uniform float uRot; uniform vec3 uSun;
    float hh(vec3 p){ p = fract(p * 0.3183099 + 0.1); p *= 17.0; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }
    float n3(vec3 x){ vec3 i = floor(x), f = fract(x); f = f * f * (3.0 - 2.0 * f);
      return mix(mix(mix(hh(i), hh(i + vec3(1,0,0)), f.x), mix(hh(i + vec3(0,1,0)), hh(i + vec3(1,1,0)), f.x), f.y), mix(mix(hh(i + vec3(0,0,1)), hh(i + vec3(1,0,1)), f.x), mix(hh(i + vec3(0,1,1)), hh(i + vec3(1,1,1)), f.x), f.y), f.z); }
    float fbm(vec3 p){ float a = 0.5, s = 0.0; for (int i = 0; i < 5; i++) { s += a * n3(p); p *= 2.03; a *= 0.5; } return s; }
    void main(){ float c = cos(uRot), s = sin(uRot); vec3 p = normalize(vP); p = vec3(c * p.x + s * p.z, p.y, -s * p.x + c * p.z);
      float land = fbm(p * 2.2 + 3.0), lat = abs(p.y);
      vec3 ocean = mix(vec3(0.05, 0.22, 0.45), vec3(0.08, 0.38, 0.58), fbm(p * 6.0));
      vec3 ground = mix(vec3(0.22, 0.45, 0.18), vec3(0.62, 0.5, 0.3), smoothstep(0.55, 0.75, fbm(p * 5.0 + 9.0)));
      vec3 col = mix(ocean, ground, smoothstep(0.52, 0.55, land));
      col = mix(col, vec3(0.95, 0.97, 1.0), smoothstep(0.78, 0.86, lat + 0.06 * fbm(p * 8.0)));
      float eq = 1.0 - smoothstep(0.004, 0.018, abs(p.y));                                   // the equator, glowing gold
      float dash = step(0.5, fract(atan(p.z, p.x) * 6.0 / 6.2832 * 4.0 - uRot * 1.5));
      col = mix(col, vec3(1.0, 0.8, 0.3), eq * (0.6 + 0.4 * dash));
      float l = max(dot(vN, uSun), 0.0); col *= 0.18 + 1.1 * l; col += vec3(1.0, 0.85, 0.3) * eq * 0.6;
      gl_FragColor = vec4(pow(col, vec3(1.0 / 1.4)), 1.0); }` }));
space.add(earth);
const cloudsE = new THREE.Mesh(new THREE.SphereGeometry(ER * 1.015, 64, 48), new THREE.ShaderMaterial({ uniforms: earthU, transparent: true, depthWrite: false,
  vertexShader: 'varying vec3 vN, vP; void main(){ vN = normalize(mat3(modelMatrix) * normal); vP = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
  fragmentShader: `varying vec3 vN, vP; uniform float uRot; uniform vec3 uSun;
    float hh(vec3 p){ p = fract(p * 0.3183099 + 0.1); p *= 17.0; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }
    float n3(vec3 x){ vec3 i = floor(x), f = fract(x); f = f * f * (3.0 - 2.0 * f);
      return mix(mix(mix(hh(i), hh(i + vec3(1,0,0)), f.x), mix(hh(i + vec3(0,1,0)), hh(i + vec3(1,1,0)), f.x), f.y), mix(mix(hh(i + vec3(0,0,1)), hh(i + vec3(1,0,1)), f.x), mix(hh(i + vec3(0,1,1)), hh(i + vec3(1,1,1)), f.x), f.y), f.z); }
    void main(){ float r = uRot * 1.15, c = cos(r), s = sin(r); vec3 p = normalize(vP); p = vec3(c * p.x + s * p.z, p.y, -s * p.x + c * p.z);
      float k = n3(p * 4.0) * 0.6 + n3(p * 9.0) * 0.4; float a = smoothstep(0.55, 0.75, k) * 0.85;
      float l = max(dot(vN, uSun), 0.0); gl_FragColor = vec4(vec3(1.0) * (0.25 + 0.9 * l), a); }` }));
space.add(cloudsE);
const atmo = new THREE.Mesh(new THREE.SphereGeometry(ER * 1.035, 64, 48), new THREE.ShaderMaterial({ transparent: true, depthWrite: false, side: THREE.BackSide, blending: THREE.AdditiveBlending,
  vertexShader: 'varying vec3 vN, vV; void main(){ vN = normalize(normalMatrix * normal); vec4 mv = modelViewMatrix * vec4(position, 1.0); vV = normalize(-mv.xyz); gl_Position = projectionMatrix * mv; }',
  fragmentShader: 'varying vec3 vN, vV; void main(){ float f = pow(1.0 - abs(dot(vN, vV)), 2.5); gl_FragColor = vec4(vec3(0.35, 0.6, 1.0) * f * 1.6, f); }' }));
space.add(atmo);
const pin = new THREE.Group();                                   // a pin on the equator where he stands
{ const pm = new THREE.MeshStandardMaterial({ color: 0xe8392f, roughness: 0.4, emissive: 0x5a0a06 }); const head = new THREE.Mesh(new THREE.SphereGeometry(0.32, 20, 14), pm); head.position.y = 1.1; pin.add(head);
  const st = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.02, 1.1, 8), new THREE.MeshStandardMaterial({ color: 0xdddddd, metalness: 0.8, roughness: 0.3 })); st.position.y = 0.55; pin.add(st); }
pin.rotation.x = Math.PI / 2; pin.position.set(0, 0, ER); earth.add(pin);              // stands on the equator, facing out
{ const l = new THREE.DirectionalLight(0xfff2e0, 2.5); l.position.set(-30, 15, 50); space.add(l); space.add(l.target); }

// --- the coast (beat 7): a sea, a beach town on the east shore, and the wall of water coming in from the west
const coast = new THREE.Group(); coast.position.copy(COAST); scene.add(coast);
const seaU = { uT: { value: 0 }, uWave: { value: -200 }, uH: { value: 0 }, uOff: { value: -160 } };
const sea = new THREE.Mesh(new THREE.PlaneGeometry(600, 300, 300, 120).rotateX(-Math.PI / 2), new THREE.ShaderMaterial({ uniforms: seaU,
  vertexShader: `uniform float uT, uWave, uH, uOff; varying float vF; varying vec3 vW;
    void main(){ vec3 p = position; float d = p.x - uWave;                                      // the wave front moves toward +x (east)
      float w = uH * exp(-d * d / (2.0 * 16.0 * 16.0)) * (d < 0.0 ? 1.0 : exp(-d * d / 60.0));    // steep face on the east side
      float chop = 0.25 * sin(p.x * 0.35 + uT * 1.7) * sin(p.z * 0.27 - uT * 1.3) + 0.15 * sin(p.x * 0.9 - uT * 2.4);
      float land = smoothstep(-25.0, -2.0, p.x + uOff);                                      // the shore: still water sits below the sand
      p.y = w + chop * (1.0 - land) - 1.2 * land * (1.0 - smoothstep(0.5, 3.0, w)); vF = clamp(w / max(uH, 0.001), 0.0, 1.0); vW = (modelMatrix * vec4(p, 1.0)).xyz;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0); }`,
  fragmentShader: `varying float vF; varying vec3 vW; uniform float uT;
    float hh(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
    float vn(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f*f*(3.0-2.0*f); return mix(mix(hh(i), hh(i+vec2(1,0)), u.x), mix(hh(i+vec2(0,1)), hh(i+vec2(1,1)), u.x), u.y); }
    void main(){ vec3 deep = vec3(0.04, 0.2, 0.32), lit = vec3(0.15, 0.5, 0.55); vec3 c = mix(deep, lit, vF * 0.8 + 0.2 * vn(vW.xz * 0.2 + uT * 0.3));
      float foam = smoothstep(0.55, 0.9, vF) * smoothstep(0.35, 0.65, vn(vW.xz * 0.8 + vec2(uT * 2.0, 0.0))) + smoothstep(0.85, 0.98, vF);
      c = mix(c, vec3(0.95, 0.97, 0.95), clamp(foam, 0.0, 1.0));
      gl_FragColor = vec4(pow(c, vec3(1.0 / 1.2)), 1.0); }` }));
sea.position.set(-160, 0, 0); coast.add(sea);
const beach = new THREE.Mesh(new THREE.PlaneGeometry(200, 300).rotateX(-Math.PI / 2), mat(0xe2c99a, 0.95)); beach.position.set(100, 0.05, 0); beach.receiveShadow = true; coast.add(beach);
const coastTown = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 1, 1), new THREE.MeshStandardMaterial({ roughness: 0.9 }), 60); coast.add(coastTown);
{ const m4 = new THREE.Matrix4(); for (let i = 0; i < 60; i++) { const w = 4 + 3 * hash1(i), h2 = 3 + 6 * hash1(i * 3); m4.compose(V(30 + (i % 6) * 9 + hash1(i * 5) * 3, h2 / 2, -60 + Math.floor(i / 6) * 13), new THREE.Quaternion(), V(w, h2, w)); coastTown.setMatrixAt(i, m4); coastTown.setColorAt(i, new THREE.Color(FAC[i % FAC.length])); } }
const coastPalms = []; for (let i = 0; i < 7; i++) { const p = palm(COAST.x + 18 + (i % 2) * 4, -40 + i * 12, 1.1); coastPalms.push(p); }
const spray = cloud(400, 2.6, 0xf2f5f2, 0.55);

// --- the North Pole (beat 8): flat sea ice with ridges, the striped pole, a polar bear, an aurora
const pole = new THREE.Group(); pole.position.copy(POLE); scene.add(pole);
const ice = new THREE.Mesh(new THREE.PlaneGeometry(800, 800, 80, 80).rotateX(-Math.PI / 2), mat(0xe8f1f8, 0.6));
{ const p = ice.geometry.attributes.position; for (let i = 0; i < p.count; i++) { const x = p.getX(i), z = p.getZ(i); p.setY(i, 0.35 * Math.max(0, Math.sin(x * 0.11 + z * 0.05) - 0.75) * 6 * (Math.hypot(x, z) > 8 ? 1 : 0)); } ice.geometry.computeVertexNormals(); }
ice.receiveShadow = true; pole.add(ice);
{ const stripes = canvasTex(64, 512, g => { for (let i = 0; i < 16; i++) { g.fillStyle = i % 2 ? '#ffffff' : '#d7262c'; g.fillRect(0, i * 32, 64, 32); } });
  const pl = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 2.4, 16), new THREE.MeshStandardMaterial({ map: stripes, roughness: 0.5 })); pl.position.set(-1.3, 1.2, -0.8); pl.castShadow = true; pole.add(pl);
  const sign = canvasTex(512, 160, g => { g.fillStyle = '#1d3b6e'; g.fillRect(0, 0, 512, 160); g.fillStyle = '#fff'; g.font = 'bold 74px Inter, Arial'; g.textAlign = 'center'; g.fillText('NORTH POLE', 256, 108); });
  const sg2 = new THREE.Mesh(new THREE.PlaneGeometry(1.2, 0.38), new THREE.MeshStandardMaterial({ map: sign, roughness: 0.6 })); sg2.position.set(-1.3, 2.1, -0.72); pole.add(sg2); }
const bear = new THREE.Group(); bear.position.set(3.2, 0, -3.5); bear.rotation.y = -0.9; pole.add(bear);
{ const bm = mat(0xf3eee2, 0.9), dk = mat(0x111111, 0.4);
  const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.55, 1.3, 6, 16).rotateZ(Math.PI / 2), bm); body.position.y = 1.0; body.castShadow = true; bear.add(body);
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.36, 20, 14), bm); head.scale.set(1.25, 0.9, 0.9); head.position.set(1.25, 1.25, 0); head.castShadow = true; bear.add(head);
  const nose = new THREE.Mesh(new THREE.SphereGeometry(0.07, 10, 8), dk); nose.position.set(1.68, 1.22, 0); bear.add(nose);
  for (const s of [-1, 1]) { const ear = new THREE.Mesh(new THREE.SphereGeometry(0.09, 10, 8), bm); ear.position.set(1.1, 1.55, 0.2 * s); bear.add(ear);
    const eye = new THREE.Mesh(new THREE.SphereGeometry(0.035, 8, 6), dk); eye.position.set(1.55, 1.35, 0.13 * s); bear.add(eye); }
  for (const [x, z] of [[-0.6, 0.3], [-0.6, -0.3], [0.6, 0.3], [0.6, -0.3]]) { const l = new THREE.Mesh(new THREE.CylinderGeometry(0.17, 0.15, 0.8, 12), bm); l.position.set(x, 0.4, z); l.castShadow = true; bear.add(l); } }
const snow = cloud(500, 0.05, 0xffffff, 0.85);

// --- the flight (beat 4): a vapor cone around him (the air tearing as he passes the speed of sound)
const cone = new THREE.Mesh(new THREE.ConeGeometry(1.0, 2.4, 40, 1, true), new THREE.ShaderMaterial({ transparent: true, depthWrite: false, side: THREE.DoubleSide, uniforms: { uT: { value: 0 }, uA: { value: 0 } },
  vertexShader: 'varying vec2 vU; void main(){ vU = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
  fragmentShader: `varying vec2 vU; uniform float uT, uA;
    float hh(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
    void main(){ float edge = smoothstep(0.0, 0.25, vU.y) * (1.0 - smoothstep(0.55, 1.0, vU.y)); float n = hh(floor(vec2(vU.x * 60.0, vU.y * 20.0 - uT * 30.0)));
      gl_FragColor = vec4(vec3(1.0), edge * (0.45 + 0.35 * n) * uA); }` }));
cone.rotation.z = -Math.PI / 2; scene.add(cone); cone.visible = false;                   // its tip points east (+x)

// --- the wind wall (beat 6): a rolling cloud of dust and torn-off roofs
const windDust = cloud(1100, 17.0, 0x5e4430, 0.55);
const roofs = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 1, 1), mat(0xb8513a, 0.8), 18); roofs.castShadow = true; scene.add(roofs); roofs.visible = false;
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
  const seeds = prev ? [prev] : (tg.seed ? [tg.seed, ...COLD] : COLD);        // a target may carry a known-good seed for its first frame
  let best = null;
  for (const s0 of seeds) {
    let a = s0.map((v, i) => clamp(v, ARM_LIM[i][0], ARM_LIM[i][1])), ca = cost(a);
    for (let step = prev ? 4 : 16; step >= 0.25; step /= 2) { let imp = true, g = 0;
      while (imp && g++ < 10) { imp = false; for (let i = 0; i < 7; i++) for (const sg of [1, -1]) { const b = a.slice(); b[i] = clamp(b[i] + sg * step, ARM_LIM[i][0], ARM_LIM[i][1]); const cb = cost(b); if (cb < ca - 1e-9) { a = b; ca = cb; imp = true; } } } }
    if (!best || ca < best.c) best = { a, c: ca };
  }
  if (prev && best.c > 20) {                                     // warm start stuck (the target turned the hand past what small steps reach): try the cold seeds too
    for (const s0 of (tg.seed ? [tg.seed, ...COLD] : COLD)) { let a = s0.map((v, i) => clamp(v, ARM_LIM[i][0], ARM_LIM[i][1])), ca = cost(a);
      for (let step = 16; step >= 0.25; step /= 2) { let imp = true, g = 0;
        while (imp && g++ < 10) { imp = false; for (let i = 0; i < 7; i++) for (const sg of [1, -1]) { const b = a.slice(); b[i] = clamp(b[i] + sg * step, ARM_LIM[i][0], ARM_LIM[i][1]); const cb = cost(b); if (cb < ca - 1e-9) { a = b; ca = cb; imp = true; } } } }
      if (ca < best.c) best = { a, c: ca }; } }
  MEM[key] = { frame, a: best.a }; return best;
}


// ------------------------------------------------------------------ the story
const SLOW = 400;                                               // the street beats are shown slowed down 400x: 1,000 mph (447 m/s) -> 1.1 m/s
const VEL = 447 / SLOW;
const yawQ = deg => new THREE.Quaternion().setFromAxisAngle(V(0, 1, 0), deg * D2R);
const go = s => Math.max(0, s - TS) * VEL * smooth(TS, TS + 0.12, s);      // how far a loose thing has moved east since the stop (street time s)
const FEET = { R: V(HOME.x - 0.11, 0.232, HOME.z + 0.02), L: V(HOME.x + 0.11, 0.232, HOME.z - 0.02) };
// every street beat maps its own clock onto one street clock s (the stop is at s = TS); beat 9 ends exactly where beat 0 starts (the loop)
function streetS(t) { const b = beatAt(t), lt = t - B[b];
  if (b === 9) return TS + 0.25 - (DUR[9] - lt);
  if (b === 0) return TS + 0.25 + lt;
  if (b === 2) return -20 + lt;
  if (b === 3) return TS - 0.95 + lt;
  if (b === 5) return TS + 2.3 + lt;
  return null; }
const sipAt = s => { const ph = ((s - TS) % 3.2 + 3.2 + 100) % 3.2; return smooth(1.3, 1.75, ph) * (1 - smooth(2.15, 2.5, ph)); };
function cupHand(s, x0 = HOME.x, z0 = HOME.z, dy = 0) { const sip = sipAt(s);
  return { S: 'R', seed: CUPARM, p: V(x0 - 0.17, 1.28 + dy, z0 + 0.26).lerp(V(x0 - 0.09, 1.61 + dy, z0 + 0.18), sip), n: V(1, 0, 0.2).normalize(), u: V(0, 0.2, 1).normalize(), c: 68 }; }
function flyPose(k, a) {                                         // thrown east: arms and legs flung out, flailing (arms kept clear of his body)
  const fl = (amp, hz, sd) => flail(a, amp, hz, sd) * k;
  return addPose(P.stand, { armR: [70 * k + fl(30, 1.6, 1), 62 * k + fl(20, 1.3, 2), 0, 40 * k + fl(30, 1.9, 3), 0], armL: [90 * k + fl(30, 1.4, 4), 80 * k + fl(20, 1.7, 5), 0, 30 * k + fl(30, 1.5, 6), 0],
    thighR: [20 * k + fl(25, 1.2, 7), 0, -10 * k], thighL: [-15 * k + fl(25, 1.1, 8), 0, 20 * k], shinR: [-40 * k + fl(20, 1.3, 9), 0, 0], shinL: [-20 * k + fl(20, 1.4, 10), 0, 0],
    spine1: [-10 * k, 0, 8 * k], neck: [10 * k, -20 * k, 0], head: [6 * k, -10 * k, 0] }); }
function guyStreet(s) {
  const k = smooth(TS, TS + 0.35, s), a = Math.max(0, s - TS), sip = sipAt(s);
  if (s <= TS) return { pose: addPose(P.stand, { neck: [-4 + 6 * Math.sin(s * 1.3) + 8 * sip, 0, 0], head: [6 * sip, 0, 0] }), root: { yaw: 180 }, face: { smile: 0.35, blink: blinkAt(s) }, hands: [cupHand(s)], feet: true };
  const pose = flyPose(k, a); if (CUPARM) pose.armR = CUPARM.map((v, i) => lerp(v, pose.armR[i] ?? 0, k));   // the arm that held the cup blends into the flail
  return { pose, root: { yaw: 180 - 25 * k, roll: -(70 * smooth(TS, TS + 0.6, s) + 40 * a), x: HOME.x + go(s), y: HOME.y + 0.45 * smooth(TS + 0.05, TS + 0.6, s) + 0.15 * Math.sin(a * 2.2) * k },
    face: { fear: k, jaw: 0.75 * k, browIn: 0.3 * k, blink: 0, look: [0.3, 0.1] }, hands: [], feet: s <= TS + 0.06 }; }
function blinkAt(s) { const u = ((s + 40) % 3.7) / 0.16; return u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0; }
let CUPARM = null;                                              // the cup-holding arm, solved once (a warm seed for first frames, and the start of the flail blend)
const FLY0 = V(-60, 24, 1.5), FLYV = 60, ROLL4 = 90;         // beat 4: flying head-first east (roll +90 lays him flat, head toward +x)                       // the flight over the town (beat 4): real-ish speed, the town rushing past below
function guyAt(t) {
  const b = beatAt(t), lt = t - B[b], s = streetS(t);
  if (s !== null) return { ...guyStreet(s), show: true };
  if (b === 4) return { pose: addPose(flyPose(0.55, lt + 3), { neck: [-25, 0, 0] }), root: { yaw: 180, roll: ROLL4 + 6 * Math.sin(lt * 2.1), tilt: 8 * Math.sin(lt * 1.3), x: FLY0.x + FLYV * lt, y: FLY0.y + 0.3 * Math.sin(lt * 3), z: FLY0.z }, face: { fear: 1, jaw: 0.8, browIn: 0.3, blink: 0 }, hands: [], feet: false, show: true };
  if (b === 8) { const sp = lt + 0.6; return { pose: addPose(P.stand, { neck: [-2 + 8 * sipAt(sp - 0.4 + TS), -10, 0], head: [6 * sipAt(sp - 0.4 + TS), 0, 0] }), root: { x: POLE.x + HOME.x, y: HOME.y - 0.13, z: POLE.z + HOME.z, yaw: 180 }, face: { smile: 0.5, blink: blinkAt(lt) },
    hands: [cupHand(sp - 0.4 + TS, POLE.x + HOME.x, POLE.z + HOME.z, -0.13)], feet: true, poleFeet: true, show: true }; }
  return { pose: P.stand, root: {}, face: {}, hands: [], feet: false, show: false };
}

// ------------------------------------------------------------------ cameras
function shakeV(t, a) { return V(vn1(t * 14, 1) * a * 0.5, vn1(t * 14, 2) * a, vn1(t * 14, 3) * a); }
function camStreet(s) {                                          // the hook camera: low in the street east of him, looking west into the sunset
  const u = smooth(TS, TS + 0.6, s), a = Math.max(0, s - TS), hp = G.bones.hips.getWorldPosition(new THREE.Vector3());
  const pos = V(3.9 - 0.3 * clamp((s + 1.7) / (TS + 1.7), 0, 1) * (1 - u), 1.35, 2.7).add(V(0.85 * a + 0.3 * u, 0.12 * u, 0.15 * a));
  const tgt = V(-2.2, 1.45, 1.05).lerp(hp.clone().add(V(-2.6, 0.35, -0.2)), u * 0.85);
  return { pos: pos.add(shakeV(s, Math.exp(-a * 2.5) * (s > TS ? 1 : 0) * 0.07)), tgt, fov: lerp(48, 54, u) };
}
function camAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b], u = lt / d, s = streetS(t);
  const hp = G.bones.hips.getWorldPosition(new THREE.Vector3());
  if (b === 0 || b === 9) return camStreet(s);
  if (b === 2) return { pos: V(2.9 - 0.3 * u, 1.65, 6.4 - 0.5 * u), tgt: V(-0.4, 1.35, 1.0), fov: 42 };
  if (b === 3) { const k = smooth(TS, TS + 0.5, s); return { pos: V(-0.4 + 1.2 * k, 0.55 + 0.5 * k, 5.2).add(shakeV(t, 0.05 * k * Math.exp(-Math.max(0, s - TS) * 2))), tgt: V(0.35, 0.65, 1.5).lerp(hp.clone().add(V(0.6, 0, 0)), k), fov: 44 }; }
  if (b === 4) return { pos: hp.clone().add(V(-0.6 + 0.4 * u, -0.7, 3.6)), tgt: hp.clone().add(V(0.25, 0.15, 0)), fov: 46 };
  if (b === 5) return { pos: V(-8 + 2 * u, 9 - u, 16), tgt: V(9 + 3 * u, 1.5, 1), fov: 50 };
  if (b === 6) return { pos: V(9 - 1.2 * u, 2.1 + 0.3 * u, 1.6), tgt: V(-20, 6 + 3 * u, -0.5), fov: 56 };
  if (b === 7) return { pos: COAST.clone().add(V(48 - 4 * u, 9 + 2 * u, 30)), tgt: COAST.clone().add(V(-60, 6 + 8 * u, -10)), fov: 54 };
  if (b === 8) { const ang = 0.35 - 0.25 * u, c = POLE.clone().add(V(HOME.x, 1.1, HOME.z)); return { pos: c.clone().add(V(Math.sin(ang) * 5.2, 0.5, Math.cos(ang) * 5.2)), tgt: c.clone().add(V(0.35, 0.25, -0.5)), fov: 46 }; }
  return { pos: SPACE.clone().add(V(0, 0.6, 26 - 9 * sm(u))), tgt: SPACE.clone().add(V(0, 0.3 * u, 0)), fov: 40 };   // beat 1: the Earth
}

// ------------------------------------------------------------------ clipping: his body points vs every solid thing near him, and vs his own body
const SOLIDS = [];                                              // { name, obj (moves), box (local) }
const sbox = (name, obj, min, max) => SOLIDS.push({ name, obj, box: new THREE.Box3(min, max) });
cars.forEach((c, i) => sbox('car', c, V(-1.9, 0.25, -0.85), V(1.9, 1.45, 0.85)));
sbox('table', table, V(-0.42, 0.0, -0.42), V(0.42, 0.78, 0.42)); sbox('chair', chair, V(-0.22, 0, -0.22), V(0.22, 0.95, 0.22));
houses.forEach(h => sbox('house', h.g, V(-2.5, 0, -2.2), V(2.5, 5.0, 2.2)));
palms.forEach(p => sbox('palm trunk', p.g, V(-0.2, 0, -0.2), V(0.55, 6.5, 0.2)));
const BODYPTS = { handR: 0.035, handL: 0.035, farmR: 0.035, farmL: 0.035, uarmR: 0.045, uarmL: 0.045, head: 0.09, chest: 0.12, hips: 0.1, shinR: 0.05, shinL: 0.05, footR: 0.04, footL: 0.04 };
const TIPSEG = {}; G.reset(); G.root.updateMatrixWorld(true);
const wp = o => o.getWorldPosition(new THREE.Vector3()), wq = o => o.getWorldQuaternion(new THREE.Quaternion());
for (const S of ['R', 'L']) for (const f of ['index', 'middle', 'pinky', 'thumb']) { const b1 = G.bones[f + '1' + S], b2 = G.bones[f + '2' + S]; TIPSEG[f + S] = wp(b2).sub(wp(b1)).multiplyScalar(0.95).applyQuaternion(wq(b2).invert()); }
const tip = (f, S) => { const b2 = G.bones[f + '2' + S]; return wp(b2).add(TIPSEG[f + S].clone().applyQuaternion(wq(b2))); };
function segDist(p, a, b) { const ab = b.clone().sub(a), t = clamp(p.clone().sub(a).dot(ab) / ab.lengthSq(), 0, 1); return p.distanceTo(a.clone().addScaledVector(ab, t)); }
function clipScan(groundY) {
  const out = []; if (!G.root.visible) return out; scene.updateMatrixWorld(true);       // props move: their matrices must be current (the check doesn't render)
  const pts = Object.entries(BODYPTS).map(([n, r]) => [n, wp(G.bones[n]), r]);
  for (const S of ['R', 'L']) for (const f of ['index', 'middle', 'pinky', 'thumb']) pts.push([f + ' tip ' + S, tip(f, S), 0.008]);
  const hipP = wp(G.bones.hips), chestP = wp(G.bones.chest), neckP = wp(G.bones.neck), headC = wp(G.bones.head).add(V(0, 0.09, 0).applyQuaternion(wq(G.bones.head)));
  for (const [n, p, r] of pts) {
    if (groundY !== null && p.y - r < groundY - 0.015) out.push({ what: n, into: 'ground', depth: +((groundY - (p.y - r)) * 100).toFixed(1) });
    for (const S of SOLIDS) { if (!S.obj.visible) continue; const q = p.clone().applyMatrix4(S.obj.matrixWorld.clone().invert()), bx = S.box;
      const dx = Math.min(q.x - bx.min.x, bx.max.x - q.x), dy = Math.min(q.y - bx.min.y, bx.max.y - q.y), dz = Math.min(q.z - bx.min.z, bx.max.z - q.z);
      const dd = Math.min(dx, dy, dz) + r; if (dx > -r && dy > -r && dz > -r && dd > 0.012) out.push({ what: n, into: S.name, depth: +(dd * 100).toFixed(1) }); }
    if (/^(hand|farm|index|middle|pinky|thumb)/.test(n)) {        // his own body: hands and forearms must not go into his trunk or his head
      const dT = segDist(p, hipP, neckP) - 0.11 - r; if (dT < -0.012) out.push({ what: n, into: 'his own body', depth: +(-dT * 100).toFixed(1) });
      const dH = p.distanceTo(headC) - 0.1 - r; if (dH < -0.012 && !/R$/.test(n) || dH < -0.03) out.push({ what: n, into: 'his own head', depth: +(-dH * 100).toFixed(1) }); }
  }
  if (cup.visible && G.root.visible) { const dT = segDist(cup.position, hipP, neckP) - 0.11 - 0.05; if (dT < -0.012) out.push({ what: 'cup', into: 'his body', depth: +(-dT * 100).toFixed(1) }); }
  return out;
}

// the cup hold at the moment of the stop, solved warm over a few frames
{ applyPose(guyStreet(TS - 0.01).pose, { yaw: 180, x: HOME.x, y: HOME.y, z: HOME.z }); G.root.updateMatrixWorld(true);
  for (let j = 0; j < 8; j++) { const sol = solveHand(cupHand(TS - 0.01), 'cupInit', j); CUPARM = sol.a.slice(); } G.reset(); }

// ------------------------------------------------------------------ per-frame update
let LASTF = -10, CUP0 = V(0, 0, 0);
const street = [];                                              // the street set is 4 km from the other stages: beyond the camera's far plane, nothing to hide
function update(t, frame) {
  t = ((t % TOTAL) + TOTAL) % TOTAL;
  const b = beatAt(t), lt = t - B[b], d = DUR[b], s = streetS(t);
  const g = guyAt(t);
  // the guy
  applyPose(g.pose, { ...g.root, x: g.root.x ?? HOME.x, y: g.root.y ?? HOME.y, z: g.root.z ?? HOME.z });
  if (g.feet) { const off = g.poleFeet ? V(POLE.x, -0.13, POLE.z) : V(0, 0, 0); for (const S of ['R', 'L']) { const f = FEET[S].clone().add(off); G.legIK(S, f, f.clone().add(V(0, 0.45, 1.0)), yawQ(180)); } }
  G.root.updateMatrixWorld(true);
  // one hand solve per shot (keyed by beat): a cut must not drag the last shot's arm along
  for (const h of g.hands) { const sol = solveHand(h, 'h' + h.S + b, frame); setArm(h.S, sol.a); LAST['arm' + h.S] = sol.a; LAST['cost' + h.S] = sol.c;
    const pp = {}; curl(pp, h.S, h.c ?? 30); for (const [n, e] of Object.entries(pp)) G.bones[n].quaternion.copy(G.REST[n].q).multiply(qTmp.setFromEuler(eTmp.set(e[0] * D2R, e[1] * D2R, e[2] * D2R))); }
  G.root.updateMatrixWorld(true); untwistSafe(); G.face(g.face); G.root.visible = g.show; G.root.updateMatrixWorld(true);
  // the street (one clock for every street beat): props, palms, awnings, houses, debris
  const st = s ?? (b === 4 || b === 6 ? TS + 6 : -20), a = Math.max(0, st - TS), k = smooth(TS, TS + 0.25, st);
  const hb = G.bones.handR; hb.updateMatrixWorld(true);
  cup.visible = g.show || s !== null;
  if (g.hands.length) { const q = hb.getWorldQuaternion(new THREE.Quaternion()); cup.position.copy(PALM('R').applyMatrix4(hb.matrixWorld)).addScaledVector(HANDREST.R.n.clone().applyQuaternion(q), 0.05); cup.rotation.set(-0.7 * sipAt(b === 8 ? lt + 0.2 + TS : (s ?? 0)), 0, 0); if (b !== 8) CUP0 = cup.position.clone(); }
  else if (b === 4) { cup.position.copy(wp(G.bones.hips)).add(V(1.4 + 0.2 * Math.sin(lt * 2), 0.9, 0.5)); cup.rotation.set(0.4 * lt, 0, -2.2 * lt); }
  else { cup.position.copy(V(HOME.x - 0.12, 1.28, HOME.z + 0.31)).add(V(go(st) * 1.06 + 0.25 * smooth(TS, TS + 0.4, st), 0.25 * smooth(TS, TS + 0.8, st) - 0.08 * a * a, 0)); cup.rotation.set(0.4 * a, 0, -2.2 * a); }
  setCloud(coffee, i => { if (s === null || st <= TS + 0.05) return null; const f = hash1(i), age = a * (0.3 + 0.7 * f); return cup.position.clone().add(V(-0.15 - 0.6 * age * f, 0.08 + 0.3 * age - 0.25 * age * age * f, (hash1(i * 3) - 0.5) * 0.25 * age)); });
  cars.forEach((c, i) => { c.position.x = [-6, 6.5][i] + go(st) * (0.98 + 0.03 * i); c.rotation.z = -0.55 * smooth(TS + 0.1, TS + 1.4, st) * (i ? 0.7 : 1) - 0.25 * a * a * (i ? 0.3 : 0.5); c.position.y = 0.4 * smooth(TS + 0.2, TS + 1.2, st) * (i ? 0.6 : 1); });
  table.position.x = 1.4 + go(st) * 1.02; table.rotation.z = -1.4 * smooth(TS, TS + 0.9, st) - 1.2 * a; table.position.y = 0.13 + 0.3 * smooth(TS, TS + 0.6, st);
  chair.position.x = 2.2 + go(st) * 1.0; chair.rotation.set(0.6 * a, 0.4 * a, -2.0 * a); chair.position.y = 0.13 + 0.45 * smooth(TS, TS + 0.5, st);
  for (const aw of awnings) { const loose = aw.i % 4 === 1; aw.g.rotation.x = -0.25 * k + 0.06 * Math.sin(st * 30 + aw.i) * k - (loose ? 0.9 * smooth(0, 0.4, a) : 0); aw.g.rotation.z = loose ? -1.2 * a : -0.12 * k;
    aw.g.position.set((-30 + aw.i * 5.4) + (loose ? go(st) * 0.95 : 0), 2.8 + (loose ? 3.5 * smooth(0, 0.5, a) : 0), -9.0 + (loose ? 2.5 * smooth(0, 0.6, a) : 0)); }   // loose ones lift up and out, clear of the others
  houses.forEach((h, i) => { const lift = smooth(TS + 1.6 + 0.4 * i, TS + 3.0 + 0.4 * i, st); h.g.position.set(h.x + go(st) * 0.9 * lift, 0.13 + 1.6 * lift, 7.0); h.g.rotation.set(0.2 * lift, 0.3 * lift, -0.5 * lift); });
  for (const p of palms) { p.g.rotation.z = -0.55 * smooth(TS, TS + 0.5, st) - 0.04 * Math.sin(st * 22) * k;
    for (const f of p.fronds) { const off = f.k % 2 === 0 && st > TS + 0.15 + 0.05 * f.k; f.f.rotation.z = off ? 0 : -0.8 * k; f.f.visible = !off; } }
  setCloud(leaves, i => { if (st <= TS + 0.15) return null; const p = palms[i % 4], age = a - 0.05 * (i % 9); if (age < 0) return null;
    return V(p.x + 0.6 + go(st) * (0.8 + 0.4 * hash1(i)), 6.0 + (hash1(i * 2) - 0.5) * 2 - 0.4 * age, 3.2 + (hash1(i * 5) - 0.5) * 3); });
  dust.m.visible = false;
  streaks.visible = st > TS && s !== null; if (streaks.visible) { const m4 = new THREE.Matrix4(); for (let i = 0; i < NST; i++) { const len = 0.6 + 1.6 * hash1(i * 5);
      const x = ((-14 + 30 * hash1(i * 3) + go(st) * (1.0 + 0.6 * hash1(i * 7)) + 40) % 40) - 14; m4.compose(V(x, 0.3 + 3.2 * hash1(i * 11), -7 + 13 * hash1(i * 13)), new THREE.Quaternion(), V(len * smooth(0, 0.4, a), 1, 1)); streaks.setMatrixAt(i, m4); }
    streaks.instanceMatrix.needsUpdate = true; }
  setCloud(debris, i => { if (s === null || st <= TS) return null; return V(-10 + 22 * hash1(i * 3) + go(st) * (0.7 + 0.6 * hash1(i * 5)), 0.15 + 1.6 * hash1(i * 7) * smooth(0, 0.6, a), -6 + 9 * hash1(i * 11)); });
  // beat 4: the vapor cone around him; beat 6: the wall of wind rolling east over the town (dust and torn-off roofs)
  cone.visible = b === 4; if (cone.visible) { cone.position.copy(wp(G.bones.chest)).add(V(0.35, 0, 0)); cone.scale.set(0.95, 1.15, 0.95); cone.material.uniforms.uT.value = t; cone.material.uniforms.uA.value = 0.32 * smooth(0, 0.4, lt) * (0.75 + 0.25 * Math.sin(t * 40)); }
  const XW = -130 + 24 * lt;
  setCloud(windDust, i => { if (b !== 6) return null; const x = XW - 45 * hash1(i * 3) ** 0.7, y = 42 * hash1(i * 7) ** 1.4, z = -26 + 52 * hash1(i * 11);
    return V(x + 4 * Math.sin(t * 2 + i), y + 2 * Math.sin(t * 3 + i * 1.7), z); });
  roofs.visible = b === 6; if (roofs.visible) { const m4 = new THREE.Matrix4(); for (let i = 0; i < roofs.count; i++) { const x0 = -130 + 120 * hash1(i * 5), z0 = -16 + 32 * hash1(i * 9), tt = clamp((XW + 8 - x0) / 25, 0, 3);
      m4.compose(V(x0 + 18 * tt * tt, 7 + 9 * tt, z0 + (z0 > 0 ? 1 : -1) * 2 * tt), new THREE.Quaternion().setFromEuler(new THREE.Euler(tt * 2 + i, tt * 3, tt * 2.5)), V(5, 0.3, 4)); roofs.setMatrixAt(i, m4); } roofs.instanceMatrix.needsUpdate = true; }
  // beat 7: the tsunami: the wave grows as it comes ashore, spray off the top, the palms bend
  seaU.uT.value = t; seaU.uWave.value = b === 7 ? lerp(40, 175, lt / d) : -60; seaU.uH.value = b === 7 ? lerp(14, 28, smooth(0, d, lt)) : 0; seaU.uOff.value = sea.position.x;
  setCloud(spray, i => { if (b !== 7) return null; const xw = COAST.x + sea.position.x + seaU.uWave.value; return V(xw - 6 + 14 * hash1(i * 3), 0.85 * seaU.uH.value + 10 * hash1(i * 7) * hash1(i * 2), -120 + 240 * hash1(i * 11)); });
  coastPalms.forEach(p => { p.g.rotation.z = -0.25 * smooth(d * 0.5, d, lt) * (b === 7 ? 1 : 0) - 0.03 * Math.sin(t * 9); });
  // beat 8: the North Pole: light snow drifting, the bear ambling
  setCloud(snow, i => { if (b !== 8) return null; return POLE.clone().add(V(-6 + 12 * hash1(i * 3) + 0.4 * Math.sin(t * 0.7 + i), ((4 - t * 0.6 - 4 * hash1(i * 7)) % 4 + 4) % 4, -6 + 10 * hash1(i * 11))); });
  bear.position.set(3.2 - 0.25 * lt, 0, -3.5 + 0.12 * lt);
  // beat 1: the Earth turns east (the pin rides the ground on the equator)
  earth.rotation.y = -0.7 + 0.7 * (b === 1 ? lt / d : 1); cloudsE.rotation.y = earth.rotation.y * 1.1; earthU.uRot.value = 0;
  // the sky: follows the camera; sunset over the street, dusty in the wind beat, polar blue with an aurora at the Pole, hidden in space
  const C = camAt(t); camera.position.copy(C.pos); camera.lookAt(C.tgt); camera.fov = C.fov; camera.updateProjectionMatrix();
  sky.position.copy(camera.position); sky.visible = b !== 1; skyU.uT.value = t; skyU.uStreak.value = s !== null ? smooth(TS, TS + 1.2, st) * (1 + a) : b === 6 ? 2.5 : 0;
  skyU.uPolar.value = b === 8 ? 1 : 0; skyU.uDust.value = b === 6 ? 0.6 : 0;
  scene.background = b === 1 ? new THREE.Color(0x05060d) : null;
  const focus = b === 7 ? COAST.clone().add(V(10, 0, 0)) : b === 8 ? POLE.clone() : b === 1 ? SPACE.clone() : b === 6 ? V(0, 0, 0) : C.tgt.clone().setY(0);
  sun.target.position.copy(focus); sun.position.copy(focus).addScaledVector(SUNDIR, 60); sun.target.updateMatrixWorld();
  { const S = sun.shadow.camera, e = b === 6 || b === 7 ? 60 : 16; if (S.right !== e) { S.left = -e; S.right = e; S.top = e; S.bottom = -e * 0.4; S.updateProjectionMatrix(); } }
  sun.intensity = b === 1 ? 0 : b === 8 ? 1.6 : 4.4; sun.color.set(b === 8 ? 0xcfe0ff : 0xffbe7a);
  street.forEach(o => { o.visible = !(b === 1 || b === 7 || b === 8); });
  space.visible = b === 1; coast.visible = b === 7; pole.visible = b === 8; spray.m.visible = spray.m.visible && b === 7;
  for (const p of coastPalms) p.g.visible = b === 7;
  return { beat: b, groundY: g.show ? (b === 8 ? 0 : b === 4 ? null : 0.13) : null };
}
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


// ------------------------------------------------------------------ frame I/O and the rig report
const gl = renderer.getContext(), px = new Uint8Array(W * H * 4);
let GROUND = null;
function stepTo(i) { const t = i / FPS, b = beatAt(((t % TOTAL) + TOTAL) % TOTAL);
  if (i !== LASTF + 1) for (let j = Math.max(Math.round(B[b] * FPS), i - 12); j < i; j++) update(j / FPS, j);
  GROUND = update(t, i).groundY; LASTF = i; }
window.renderAll = async (f0, f1) => { for (let i = f0; i < f1; i++) { stepTo(i); draw(i / FPS); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); await fetch('/frame', { method: 'POST', body: px }); } return 'ok'; };
window.renderAtT = t => { const i = Math.round(t * FPS); stepTo(i); if (window.CAM) { camera.position.set(...window.CAM.pos); camera.up.set(0, 1, 0); camera.lookAt(...window.CAM.tgt); camera.fov = window.CAM.fov || 42; camera.updateProjectionMatrix(); sky.position.copy(camera.position); } draw(t); return renderer.domElement.toDataURL('image/png'); };
window.rigReport = i => { stepTo(i); const t = i / FPS, iq = G.root.getWorldQuaternion(new THREE.Quaternion()).invert();
  return { t, beat: beatAt(t), ang: LAST, hips: wp(G.bones.hips).toArray(), car: 0, show: G.root.visible,
    thumbs: ['R', 'L'].map(S => wp(G.bones['index1' + S]).sub(wp(G.bones['pinky1' + S])).applyQuaternion(iq).toArray()),
    forearms: ['R', 'L'].map(S => wp(G.bones['hand' + S]).sub(wp(G.bones['farm' + S])).normalize().applyQuaternion(iq).toArray()),
    cost: [LAST.costR ?? null, LAST.costL ?? null], clip: clipScan(GROUND) }; };
window.clipTest = (i, dz) => { stepTo(i); G.root.position.z += dz; G.root.updateMatrixWorld(true); const r = clipScan(GROUND); stepTo(i); return r; };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS);
window.READY = true;
