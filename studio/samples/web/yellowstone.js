// "Yellowstone just erupted. Here's what's going to happen." - a 3D Short with the sculpted, skinned guy (regular 3D, like the plane).
//   yellowstone.html?w=1080&h=1920            (times from yellowstone/times.json; one shot per narration line)
// Beats: 0 the selfie at the overlook, the blast behind him (hook) | 1 the wall of hot ash chasing him down the road
//        2 the map: the ash cloud spreads, even against the wind | 3 the town: ash falls like gray snow, piles up past his knees
//        4 rain on the ash, the roof across the street caves in | 5 he coughs; cut to the ash up close: jagged rock and glass
//        6 a jet in the ash cloud, the engine cut open: ash melts inside | 7 summer snow on the corn, he shivers
//        8 the twist: Old Faithful on a sunny day, he eats an ice cream | 9 the selfie before it happened; the blast at the very end (loops)
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { GTAOPass } from 'three/addons/postprocessing/GTAOPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { loadGuy } from '/guy3d.js';

const Q = new URLSearchParams(location.search);
const W = +Q.get('w') || 720, H = +Q.get('h') || 1280;
const FPS = 30;
const TIMES = await (await fetch('/yellowstone/times.json')).json();
const B = TIMES.starts, DUR = TIMES.durs, TOTAL = TIMES.total;
const beatAt = t => { let i = 0; for (let k = 0; k < B.length; k++) if (t >= B[k]) i = k; return i; };
const clamp = (x, a, b) => Math.min(Math.max(x, a), b);
const sm = t => t * t * (3 - 2 * t);
const smooth = (a, b, x) => sm(clamp((x - a) / (b - a), 0, 1));
const lerp = (a, b, u) => a + (b - a) * u;
const D2R = Math.PI / 180;
function hash1(n) { const s = Math.sin(n * 127.1) * 43758.5453; return s - Math.floor(s); }
function vn1(x, seed) { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return lerp(hash1(i + seed * 17.3), hash1(i + 1 + seed * 17.3), u) * 2 - 1; }
function h2(x, z) { const s = Math.sin(x * 127.1 + z * 311.7) * 43758.5453; return s - Math.floor(s); }
function vn2(x, z) { const ix = Math.floor(x), iz = Math.floor(z), fx = x - ix, fz = z - iz, ux = fx * fx * (3 - 2 * fx), uz = fz * fz * (3 - 2 * fz);
  return lerp(lerp(h2(ix, iz), h2(ix + 1, iz), ux), lerp(h2(ix, iz + 1), h2(ix + 1, iz + 1), ux), uz); }
function fbm2(x, z) { let a = 0.5, s = 0; for (let i = 0; i < 5; i++) { s += a * vn2(x, z); x = x * 2.03 + 17.1; z = z * 2.03 - 9.3; a *= 0.5; } return s / 0.97; }
const V = (x, y, z) => new THREE.Vector3(x, y, z);
function canvasTex(w, h, draw) { const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), c); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t; }
const GLSL_NOISE = `float hh(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
    float vn(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f*f*(3.0-2.0*f); return mix(mix(hh(i), hh(i+vec2(1,0)), u.x), mix(hh(i+vec2(0,1)), hh(i+vec2(1,1)), u.x), u.y); }`;

// ------------------------------------------------------------------ renderer, sky, light
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(W, H);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.0; renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.localClippingEnabled = true;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(45, W / H, 0.05, 4200);
scene.fog = new THREE.FogExp2(0xb9cde0, 0.0004);
const skyU = { uSun: { value: V(0.45, 0.55, 0.7).normalize() }, uT: { value: 0 }, uMurk: { value: 0 }, uMurkCol: { value: new THREE.Color(0x6e6560) }, uFlash: { value: 0 } };
const skyMat = new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false, uniforms: skyU,
  vertexShader: 'varying vec3 vD; void main(){ vD = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
  fragmentShader: `varying vec3 vD; uniform vec3 uSun, uMurkCol; uniform float uT, uMurk, uFlash; ${GLSL_NOISE}
    void main(){ float h = clamp(vD.y, -0.1, 1.0);
      vec3 c = mix(vec3(0.78, 0.86, 0.95), vec3(0.32, 0.55, 0.9), smoothstep(0.0, 0.55, h));
      float s = max(dot(normalize(vD), uSun), 0.0); c += vec3(1.0, 0.92, 0.75) * (pow(s, 8.0) * 0.25 + pow(s, 600.0) * 4.0);
      vec2 cp = vec2(atan(vD.x, -vD.z) * 3.0, vD.y * 8.0);
      float cl = vn(cp + vec2(uT * 0.01, 0.0)) * 0.65 + vn(cp * 2.3) * 0.35;
      c = mix(c, vec3(1.0, 0.99, 0.97), smoothstep(0.58, 0.78, cl) * smoothstep(0.03, 0.2, h) * 0.8);
      vec3 m = 1.7 * uMurkCol * (0.75 + 0.25 * smoothstep(0.0, 0.5, h)) * (0.85 + 0.3 * vn(cp * 1.7 + uT * 0.05));
      m += vec3(1.0, 0.85, 0.6) * pow(s, 30.0) * 0.25;                                   // a pale sun disc through the ash
      c = mix(c, m, uMurk);
      c += vec3(1.0, 0.55, 0.25) * uFlash * (0.4 + 0.6 * smoothstep(0.0, 0.3, 1.0 - h));
      gl_FragColor = vec4(c, 1.0); }` });
skyMat.fog = false;
const sky = new THREE.Mesh(new THREE.SphereGeometry(3500, 48, 24), skyMat); sky.frustumCulled = false; sky.renderOrder = -10; scene.add(sky);
{ const pm = new THREE.PMREMGenerator(renderer); const es = new THREE.Scene(); es.add(new THREE.Mesh(new THREE.SphereGeometry(10, 32, 16), skyMat));
  scene.environment = pm.fromScene(es, 0.03).texture; scene.environmentIntensity = 0.45; }
const hemi = new THREE.HemisphereLight(0xbcd4ff, 0x5a4a38, 0.75); scene.add(hemi);
const sun = new THREE.DirectionalLight(0xfff0dc, 3.4); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
{ const S = sun.shadow.camera; S.left = -14; S.right = 14; S.top = 14; S.bottom = -8; S.near = 1; S.far = 260; sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.03; }
scene.add(sun); scene.add(sun.target);
const SUNDIR = V(0.45, 0.55, 0.7).normalize();
const mat = (c, r = 0.8, m = 0) => new THREE.MeshStandardMaterial({ color: c, roughness: r, metalness: m });
const box = (w, h, d, x, y, z, m, r = 0, parent = scene) => { const o = new THREE.Mesh(r > 0 ? new RoundedBoxGeometry(w, h, d, 2, Math.min(r, 0.4 * Math.min(w, h, d))) : new THREE.BoxGeometry(w, h, d), m); o.position.set(x, y, z); o.castShadow = true; o.receiveShadow = true; parent.add(o); return o; };

// ------------------------------------------------------------------ puffs: lit, soft billboards (ash, steam, dust), sorted back to front every frame
const ALLPUFFS = [];
const SUNU = { value: SUNDIR.clone() }, FOGC = { value: new THREE.Color(0xb9cde0) }, FOGD = { value: 0.0004 };
function puffSystem(n, { sunCol = 0xfff0dc, amb = 0x8a8f9a, glow = 0xff6a1a, lit = 1 } = {}) {
  const geo = new THREE.InstancedBufferGeometry().copy(new THREE.PlaneGeometry(1, 1)); geo.instanceCount = 0;
  const P = new Float32Array(n * 4), C = new Float32Array(n * 3), O = new Float32Array(n * 3);
  const aP = new THREE.InstancedBufferAttribute(P, 4), aC = new THREE.InstancedBufferAttribute(C, 3), aO = new THREE.InstancedBufferAttribute(O, 3);
  for (const a of [aP, aC, aO]) a.setUsage(THREE.DynamicDrawUsage);
  geo.setAttribute('aP', aP); geo.setAttribute('aC', aC); geo.setAttribute('aO', aO);
  const U = { uSun: SUNU, uSunCol: { value: new THREE.Color(sunCol) }, uAmb: { value: new THREE.Color(amb) }, uGlowC: { value: new THREE.Color(glow) }, uFogC: FOGC, uFogD: FOGD, uLit: { value: lit } };
  const m = new THREE.ShaderMaterial({ uniforms: U, transparent: true, depthWrite: false,
    vertexShader: `attribute vec4 aP; attribute vec3 aC, aO; uniform float uFogD;
      varying vec2 vUv; varying vec3 vCol, vR, vU, vF; varying float vOp, vGlow, vSeed, vFog;
      void main(){ vec3 c = (modelMatrix * vec4(aP.xyz, 1.0)).xyz; float s = aP.w;
        vec3 R = vec3(viewMatrix[0][0], viewMatrix[1][0], viewMatrix[2][0]), U = vec3(viewMatrix[0][1], viewMatrix[1][1], viewMatrix[2][1]);
        float a = aO.z * 6.2831; vec2 p = mat2(cos(a), -sin(a), sin(a), cos(a)) * position.xy;
        vec3 w = c + (R * p.x + U * p.y) * s;
        vR = R; vU = U; vF = normalize(cameraPosition - c); vUv = uv; vCol = aC; vOp = aO.x; vGlow = aO.y; vSeed = aO.z;
        vec4 mv = viewMatrix * vec4(w, 1.0); vFog = 1.0 - exp(-uFogD * uFogD * dot(mv.xyz, mv.xyz));
        gl_Position = projectionMatrix * mv; }`,
    fragmentShader: `uniform vec3 uSun, uSunCol, uAmb, uGlowC, uFogC; uniform float uLit; ${GLSL_NOISE}
      varying vec2 vUv; varying vec3 vCol, vR, vU, vF; varying float vOp, vGlow, vSeed, vFog;
      void main(){ vec2 p = vUv * 2.0 - 1.0;
        float n = vn(p * 2.2 + vSeed * 37.0) * 0.6 + vn(p * 5.0 + vSeed * 11.0) * 0.3 + vn(p * 11.0 - vSeed * 5.0) * 0.1;
        float r2 = dot(p, p) + (n - 0.5) * 0.7;
        float a = (1.0 - smoothstep(0.35, 0.95, r2)) * vOp;
        if (a < 0.004) discard;
        float z = sqrt(max(0.05, 1.0 - min(1.0, dot(p, p))));
        vec3 N = normalize(vR * (p.x + (n - 0.5) * 0.8) + vU * (p.y + (n - 0.5) * 0.8) + vF * z);
        float l = clamp(dot(N, uSun) * 0.7 + 0.3, 0.0, 1.0);
        vec3 col = vCol * mix(vec3(1.0), uAmb + uSunCol * l, uLit) * (0.8 + 0.4 * n);
        col += uGlowC * vGlow * (0.5 + 0.8 * n) * (0.6 + 0.6 * clamp(-N.y, 0.0, 1.0));
        col = mix(col, uFogC, vFog);
        gl_FragColor = vec4(col, a); }` });
  m.fog = false;
  const mesh = new THREE.Mesh(geo, m); mesh.frustumCulled = false; scene.add(mesh);
  const buf = []; for (let i = 0; i < n; i++) buf.push({ x: 0, y: 0, z: 0, s: 0, r: 0, g: 0, b: 0, o: 0, gl: 0, sd: hash1(i * 7.7 + n), d: 0 });
  let k = 0;
  const sys = { mesh, U, n,
    begin() { k = 0; },
    add(x, y, z, s, r, g, b, o, gl = 0) { if (k >= n || o <= 0.003 || s <= 0) return; const q = buf[k]; q.x = x; q.y = y; q.z = z; q.s = s; q.r = r; q.g = g; q.b = b; q.o = o; q.gl = gl; q.sd = hash1(k * 7.7 + n); k++; },
    end() { const cp = camera.position; const list = buf.slice(0, k); for (const q of list) q.d = (q.x - cp.x) ** 2 + (q.y - cp.y) ** 2 + (q.z - cp.z) ** 2;
      list.sort((a, b) => b.d - a.d);
      list.forEach((q, i) => { P.set([q.x, q.y, q.z, q.s], i * 4); C.set([q.r, q.g, q.b], i * 3); O.set([q.o, q.gl, q.sd], i * 3); });
      geo.instanceCount = k; aP.needsUpdate = aC.needsUpdate = aO.needsUpdate = true; mesh.visible = k > 0; },
    count: () => k };
  ALLPUFFS.push(sys);
  return sys;
}
const softTex = canvasTex(64, 64, g => { const gr = g.createRadialGradient(32, 32, 0, 32, 32, 31); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.45, 'rgba(255,255,255,0.45)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); });
function cloud(n, size, color, op) { const g = new THREE.BufferGeometry(); const p = new Float32Array(n * 3); g.setAttribute('position', new THREE.BufferAttribute(p, 3));
  const m = new THREE.Points(g, new THREE.PointsMaterial({ map: softTex, color, size, transparent: true, depthWrite: false, opacity: op })); m.frustumCulled = false; scene.add(m); return { m, p, n }; }
function setCloud(c, fn) { let k = 0; for (let i = 0; i < c.n; i++) { const q = fn(i); if (q) { c.p.set([q.x, q.y, q.z], k * 3); k++; } } for (let i = k; i < c.n; i++) c.p.set([0, -9999, 0], i * 3); c.m.geometry.attributes.position.needsUpdate = true; c.m.visible = k > 0; }

// ------------------------------------------------------------------ the park (origin): a plateau with the overlook at its edge, the valley, far mountains
// The overlook: he stands at the origin; the cliff edge runs east-west just behind him (z ~ -6); the valley drops ~70 m;
// the vent is out in the valley at VENT; mountains ring the far side. The run road (beat 1) and the geyser basin (beat 8) are on the plateau.
const VENT = V(95, -62, -700);
const RX = 200, RZ0 = 300;                                       // the run: down the road along +z from (RX, 0, RZ0)
const GEY = V(-230, 0, 230);                                     // Old Faithful
function terrainH(x, z) {
  let plateau = 3.5 * (fbm2(x / 70, z / 70) - 0.5) + 45 * smooth(120, 900, Math.hypot(x, z)) * fbm2(x / 260 + 3, z / 260) ;
  let valley = -72 + 30 * (fbm2(x / 160, z / 160) - 0.5) + 16 * (fbm2(x / 50 + 7, z / 50) - 0.5);
  const dM = Math.hypot(x * 0.8, z + 450);
  const ridge = 1 - Math.abs(fbm2(x / 230 + 11, z / 230) * 2 - 1);
  valley += 230 * smooth(360, 950, dM) * (0.45 + 0.75 * ridge * ridge);
  const dv = Math.hypot(x - VENT.x, z - VENT.z); valley += 28 * smooth(160, 60, dv) - 34 * smooth(55, 20, dv);   // a low cone with a crater at the vent
  const edge = -6 + 3 * Math.sin(x * 0.045) + 5 * (fbm2(x / 35, 1.7) - 0.5);
  const k = smooth(edge - 16, edge - 1, z);
  let h = lerp(valley, plateau, k);
  h = lerp(h, 0, smooth(13, 6, Math.hypot(x, z * 1.4)) * k);                                  // the overlook: flat ground
  h = lerp(h, 0, smooth(16, 8, Math.abs(x - RX)) * smooth(80, 130, z) * k);                 // the road: flat
  h = lerp(h, 0, smooth(70, 40, Math.hypot(x - GEY.x, z - GEY.z)) * k);                     // the geyser basin: flat
  return h;
}
const park = new THREE.Group(); scene.add(park);
let terrain;
{ const N = 420, g = new THREE.PlaneGeometry(2, 2, N, N).rotateX(-Math.PI / 2), p = g.attributes.position;
  const warp = u => Math.sign(u) * 1700 * Math.abs(u) ** 2.1;
  for (let i = 0; i < p.count; i++) { const x = warp(p.getX(i)), z = warp(p.getZ(i)); p.setXYZ(i, x, terrainH(x, z), z); }
  g.computeVertexNormals();
  const nr = g.attributes.normal, col = new Float32Array(p.count * 3), c = new THREE.Color();
  for (let i = 0; i < p.count; i++) { const x = p.getX(i), y = p.getY(i), z = p.getZ(i), ny = nr.getY(i), n = fbm2(x / 9, z / 9);
    c.setRGB(0.24 + 0.08 * n, 0.27 + 0.1 * n, 0.14 + 0.04 * n);                                       // forest floor / meadow
    if (y < -40) c.lerp(new THREE.Color(0.32 + 0.1 * n, 0.36 + 0.08 * n, 0.17), 0.6);                  // valley meadows
    c.lerp(new THREE.Color(0.3 + 0.08 * n, 0.27 + 0.07 * n, 0.24 + 0.05 * n), smooth(0.85, 0.6, ny));    // rock on steep ground
    c.lerp(new THREE.Color(0.9, 0.92, 0.95), smooth(230, 280, y + 40 * (n - 0.5)) * smooth(0.55, 0.8, ny));   // snow up high
    const dg = Math.hypot(x - GEY.x, z - GEY.z); c.lerp(new THREE.Color(0.86, 0.83, 0.74), smooth(55, 25, dg + 10 * n));   // white sinter around the geyser
    c.lerp(new THREE.Color(0.36, 0.33, 0.28), smooth(5.5, 3, Math.hypot(x, z * 1.3) - 2 * n) * 0.8);  // a worn gravel pad at the overlook
    col.set([c.r, c.g, c.b], i * 3); }
  g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  terrain = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.95 })); terrain.receiveShadow = true; park.add(terrain); }
// pines: one merged geometry (trunk + three cones), instanced; denser near the overlook, along the road, around the valley
const pineGeo = (() => { const parts = [], cols = [];
  const add = (geo, color) => { const g = geo.toNonIndexed(); parts.push(g); const c = new THREE.Color(color); const a = new Float32Array(g.attributes.position.count * 3); for (let i = 0; i < a.length; i += 3) a.set([c.r, c.g, c.b], i); cols.push(a); };
  add(new THREE.CylinderGeometry(0.18, 0.28, 3.2, 6).translate(0, 1.6, 0), 0x4a3424);
  add(new THREE.ConeGeometry(2.4, 5.0, 8).translate(0, 4.6, 0), 0x1f3a22);
  add(new THREE.ConeGeometry(1.9, 4.2, 8).translate(0, 7.2, 0), 0x24432a);
  add(new THREE.ConeGeometry(1.3, 3.6, 8).translate(0, 9.6, 0), 0x2a4d30);
  const pa = [], na = [], ca = []; parts.forEach((g, i) => { pa.push(...g.attributes.position.array); na.push(...g.attributes.normal.array); ca.push(...cols[i]); });
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pa, 3)); g.setAttribute('normal', new THREE.Float32BufferAttribute(na, 3)); g.setAttribute('color', new THREE.Float32BufferAttribute(ca, 3)); return g; })();
const PINES = [];
{ let s = 1; const rnd = () => hash1(s++ * 1.731);
  const okAt = (x, z) => { const y = terrainH(x, z); if (y > 150) return null; if (Math.hypot(x, z * 1.4) < 14) return null; if (Math.abs(x - RX) < 9 && z > 60) return null; if (Math.hypot(x - GEY.x, z - GEY.z) < 62) return null;
    if (Math.hypot(x - VENT.x, z - VENT.z) < 120) return null;
    const e = 2, sl = Math.abs(terrainH(x + e, z) - terrainH(x - e, z)) + Math.abs(terrainH(x, z + e) - terrainH(x, z - e)); if (sl > 3.2) return null; return y; };
  const tryAdd = (x, z, sc) => { const y = okAt(x, z); if (y === null) return; PINES.push({ x, y, z, s: sc * (0.75 + 0.6 * rnd()), r: rnd() * 6.3 }); };
  for (let i = 0; i < 9000 && PINES.length < 6500; i++) { const a = rnd() * 6.283, r = 18 + 1300 * rnd() ** 1.8; tryAdd(Math.cos(a) * r, Math.sin(a) * r * 0.9 - 150, 1.0); }
  for (let i = 0; i < 2500 && PINES.length < 8600; i++) tryAdd(RX - 140 + 280 * rnd(), RZ0 - 260 + 420 * rnd(), 1.1);       // the forest along the road
  for (let i = 0; i < 600 && PINES.length < 9200; i++) { const a = rnd() * 6.283, r = 16 + 60 * rnd(); tryAdd(Math.cos(a) * r, Math.abs(Math.sin(a)) * r + 4, 1.0); } }
const pines = new THREE.InstancedMesh(pineGeo, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.9 }), PINES.length);
{ const m4 = new THREE.Matrix4(); PINES.forEach((p, i) => { m4.compose(V(p.x, p.y - 0.2, p.z), new THREE.Quaternion().setFromAxisAngle(V(0, 1, 0), p.r), V(p.s, p.s, p.s)); pines.setMatrixAt(i, m4); }); }
pines.castShadow = true; pines.receiveShadow = true; park.add(pines);
// the overlook: a log railing on the cliff edge behind him, a park sign, rocks
const wood = mat(0x7a5532, 0.85), woodDk = mat(0x5a3d24, 0.9);
const RAIL_Z = -2.2;
for (let x = -4; x <= 4; x += 2) box(0.16, 1.1, 0.16, x, 0.55, RAIL_Z, woodDk, 0.04, park);
for (const y of [0.55, 1.0]) { const r = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.07, 8.4, 10).rotateZ(Math.PI / 2), wood); r.position.set(0, y, RAIL_Z); r.castShadow = true; park.add(r); }
const signTex = canvasTex(512, 220, g => { g.fillStyle = '#5b3a22'; g.fillRect(0, 0, 512, 220); g.strokeStyle = '#e9d9b0'; g.lineWidth = 8; g.strokeRect(14, 14, 484, 192);
  g.fillStyle = '#efe2bd'; g.textAlign = 'center'; g.font = 'bold 70px Georgia, serif'; g.fillText('YELLOWSTONE', 256, 112); g.font = 'bold 34px Georgia, serif'; g.fillText('CALDERA OVERLOOK', 256, 168); });
const sign = new THREE.Group(); sign.position.set(3.6, 0, 1.6); sign.rotation.y = -0.5; park.add(sign);
{ box(1.7, 0.75, 0.1, 0, 1.25, 0, new THREE.MeshStandardMaterial({ map: signTex, roughness: 0.8 }), 0, sign); for (const x of [-0.7, 0.7]) box(0.12, 1.3, 0.12, x, 0.62, -0.08, woodDk, 0.03, sign); }
const rockGeo = new THREE.DodecahedronGeometry(1, 1); { const p = rockGeo.attributes.position; for (let i = 0; i < p.count; i++) { const v = V(p.getX(i), p.getY(i), p.getZ(i)); v.multiplyScalar(0.8 + 0.35 * h2(v.x * 3 + v.y, v.z * 3)); p.setXYZ(i, v.x, v.y, v.z); } rockGeo.computeVertexNormals(); }
for (const [x, z, s] of [[-4.6, -1.2, 0.9], [-5.6, 0.6, 0.6], [5.2, -1.0, 0.7], [-3.4, 2.8, 0.45], [6.2, 1.8, 1.1]]) { const r = new THREE.Mesh(rockGeo, mat(0x8a8178, 0.9)); r.position.set(x, s * 0.3, z); r.scale.set(s * 1.3, s * 0.8, s); r.castShadow = r.receiveShadow = true; park.add(r); }
// the run road (beat 1): asphalt with a yellow center line
{ const road = new THREE.Mesh(new THREE.PlaneGeometry(7, 700).rotateX(-Math.PI / 2), mat(0x3a3a3e, 0.92)); road.position.set(RX, 0.04, RZ0 + 50); road.receiveShadow = true; park.add(road);
  for (let z = -290; z < 400; z += 6) { const d = new THREE.Mesh(new THREE.PlaneGeometry(0.14, 3).rotateX(-Math.PI / 2), mat(0xe6c23a, 0.7)); d.position.set(RX, 0.05, RZ0 + z); park.add(d); } }
// Old Faithful (beat 8): a sinter mound, a boardwalk with a rail, the geyser column (steam puffs + water spray)
{ const mound = new THREE.Mesh(new THREE.SphereGeometry(9, 32, 12, 0, Math.PI * 2, 0, Math.PI / 2), mat(0xcfc6b0, 0.95)); mound.scale.y = 0.18; mound.position.copy(GEY); mound.receiveShadow = true; park.add(mound);
  const pool = new THREE.Mesh(new THREE.CircleGeometry(1.4, 24).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0x3fa6c4, roughness: 0.1, emissive: 0x0a2a33 })); pool.position.copy(GEY).add(V(0, 1.63, 0)); park.add(pool); }
const BW = GEY.clone().add(V(0, 0, 26));                         // the boardwalk runs east-west, 26 m south of the geyser
{ const bw = new THREE.Group(); bw.position.copy(BW); park.add(bw);
  box(40, 0.12, 2.4, 0, 0.4, 0, mat(0x8a6a48, 0.85), 0, bw);
  for (let x = -19.5; x <= 19.5; x += 0.6) box(0.05, 0.005, 2.38, x, 0.465, 0, mat(0x5e4630, 0.9), 0, bw);
  for (let x = -20; x <= 20; x += 2.5) { box(0.1, 0.9, 0.1, x, 0.85, -1.15, woodDk, 0.02, bw); box(0.1, 0.4, 0.1, x, 0.15, -1.15, woodDk, 0, bw); box(0.1, 0.4, 0.1, x, 0.15, 1.15, woodDk, 0, bw); }
  box(40, 0.08, 0.12, 0, 1.28, -1.15, wood, 0.02, bw); }
const BWY = 0.46;                                                // the deck surface height
// the eruption column, the pyroclastic flow, the geyser: puff systems
const colPuffs = puffSystem(1800, { amb: 0x7f8590, sunCol: 0xffecd6 });
const flowPuffs = puffSystem(1500, { amb: 0x7a7a80, sunCol: 0xffe6cc });
const geyPuffs = puffSystem(500, { amb: 0xb8c4d4, sunCol: 0xffffff });
const bombs = new THREE.InstancedMesh(new THREE.DodecahedronGeometry(1, 0), new THREE.MeshStandardMaterial({ color: 0x2a2220, emissive: 0xff5a10, emissiveIntensity: 1.6, roughness: 0.8 }), 40); bombs.frustumCulled = false; park.add(bombs);
const flash = new THREE.PointLight(0xff8a3a, 0, 3000, 1.2); flash.position.copy(VENT).add(V(0, 40, 0)); park.add(flash);
const spray = cloud(700, 0.35, 0xf4f8ff, 0.75);                  // geyser droplets

// ------------------------------------------------------------------ the map (beat 2): the lower 48 as a board, the umbrella cloud spreading from Yellowstone
const MAP = V(0, 0, 9000);
const mapG = new THREE.Group(); mapG.position.copy(MAP); scene.add(mapG);
const LL = (lon, lat) => [(lon + 98) * 0.9 * Math.cos(39 * D2R), (lat - 39) * 0.9];   // shape coords (x east, y north); north is -z once laid flat
const US = [[-124.7, 48.4], [-123.0, 49.0], [-95.2, 49.0], [-95.1, 49.4], [-94.6, 48.7], [-92.0, 48.4], [-89.6, 48.0], [-87.5, 47.4], [-84.6, 46.5], [-84.1, 46.0], [-83.4, 45.0],
  [-82.4, 43.0], [-83.1, 42.0], [-82.4, 41.7], [-79.0, 42.8], [-79.0, 43.3], [-76.5, 43.6], [-75.0, 44.9], [-71.5, 45.0], [-70.0, 46.7], [-69.2, 47.45], [-67.8, 47.1], [-67.0, 45.0],
  [-68.8, 44.4], [-70.2, 43.7], [-70.6, 42.7], [-70.0, 41.9], [-71.0, 41.5], [-73.9, 40.6], [-74.0, 40.0], [-74.9, 38.95], [-75.1, 38.8], [-76.0, 37.1], [-76.0, 36.9], [-75.5, 35.25],
  [-76.5, 34.7], [-77.9, 33.9], [-79.2, 33.2], [-80.9, 32.0], [-81.4, 30.5], [-80.6, 28.4], [-80.1, 26.7], [-80.4, 25.2], [-81.1, 25.1], [-81.8, 26.1], [-82.7, 27.8], [-82.7, 29.0],
  [-84.0, 30.1], [-85.4, 29.7], [-86.5, 30.4], [-88.0, 30.4], [-89.6, 30.2], [-89.4, 29.2], [-90.5, 29.1], [-92.0, 29.6], [-93.8, 29.7], [-94.8, 29.3], [-97.0, 27.8], [-97.4, 26.0],
  [-99.1, 26.4], [-99.5, 27.5], [-100.3, 28.6], [-101.4, 29.8], [-102.4, 29.8], [-103.1, 29.0], [-104.5, 29.6], [-106.5, 31.8], [-108.2, 31.8], [-108.2, 31.33], [-111.1, 31.33],
  [-114.8, 32.5], [-114.7, 32.7], [-117.1, 32.5], [-118.4, 33.8], [-120.6, 34.6], [-121.9, 36.5], [-122.5, 37.8], [-123.8, 39.8], [-124.4, 40.4], [-124.2, 42.0], [-124.5, 43.0],
  [-124.0, 46.2], [-124.1, 47.0]];
const LMICH = [[-87.8, 41.7], [-86.6, 42.1], [-86.2, 43.6], [-86.0, 45.0], [-85.0, 45.8], [-87.0, 45.8], [-87.6, 44.5], [-87.9, 43.0]];
{ const sh = new THREE.Shape(US.map(([a, b]) => new THREE.Vector2(...LL(a, b)))); sh.holes.push(new THREE.Path(LMICH.map(([a, b]) => new THREE.Vector2(...LL(a, b)))));
  const g = new THREE.ExtrudeGeometry(sh, { depth: 0.6, bevelEnabled: true, bevelThickness: 0.12, bevelSize: 0.12, bevelSegments: 2 }).rotateX(-Math.PI / 2);
  const tex = canvasTex(1024, 512, c => { const gr = c.createLinearGradient(0, 0, 1024, 0); gr.addColorStop(0, '#9a8a5c'); gr.addColorStop(0.35, '#b39a62'); gr.addColorStop(0.55, '#7ea456'); gr.addColorStop(1, '#5f9447'); c.fillStyle = gr; c.fillRect(0, 0, 1024, 512);
    for (let i = 0; i < 3000; i++) { c.fillStyle = `rgba(${Math.random() < 0.5 ? '40,60,30' : '230,220,180'},0.06)`; c.beginPath(); c.arc(Math.random() * 1024, Math.random() * 512, 3 + Math.random() * 10, 0, 6.3); c.fill(); } });
  g.computeBoundingBox(); const bb = g.boundingBox, uv = g.attributes.uv, p = g.attributes.position;
  for (let i = 0; i < p.count; i++) uv.setXY(i, (p.getX(i) - bb.min.x) / (bb.max.x - bb.min.x), (p.getZ(i) - bb.min.z) / (bb.max.z - bb.min.z));
  const land = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ map: tex, roughness: 0.9 })); land.castShadow = true; land.receiveShadow = true; mapG.add(land);
  const sea = new THREE.Mesh(new THREE.PlaneGeometry(200, 200), new THREE.MeshStandardMaterial({ color: 0x2d6aa0, roughness: 0.35, metalness: 0.1 })); sea.rotation.x = -Math.PI / 2; sea.position.y = -0.2; sea.receiveShadow = true; mapG.add(sea);
  // the Rockies: a chain of low peaks
  for (let i = 0; i < 60; i++) { const lat = 33 + 15 * hash1(i * 3), lon = -105.5 - 6 * hash1(i * 5) - (lat - 33) * 0.25; const [x, y] = LL(lon, lat);
    const pk = new THREE.Mesh(new THREE.ConeGeometry(0.5 + 0.4 * hash1(i * 7), 0.5 + 0.7 * hash1(i * 9), 5), mat(0x8c7a62, 0.9)); pk.position.set(x, 0.72 + 0.2, -y); pk.castShadow = true; mapG.add(pk); } }
const YS = (() => { const [x, y] = LL(-110.6, 44.5); return V(x, 0.72, -y); })();
const ysPin = new THREE.Group(); ysPin.position.copy(YS); ysPin.scale.setScalar(2.2); mapG.add(ysPin);
{ const head = new THREE.Mesh(new THREE.SphereGeometry(0.28, 18, 12), new THREE.MeshStandardMaterial({ color: 0xe8392f, emissive: 0x6a0c06, roughness: 0.4 })); head.position.y = 1.3; ysPin.add(head);
  const st = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.02, 1.3, 8), mat(0xdddddd, 0.3, 0.8)); st.position.y = 0.65; ysPin.add(st); }
const mapPuffs = puffSystem(1400, { amb: 0x80858e, sunCol: 0xfff2e2 });
const arrows = new THREE.InstancedMesh((() => { const s = new THREE.Shape(); s.moveTo(0, -0.12); s.lineTo(1.1, -0.12); s.lineTo(1.1, -0.32); s.lineTo(1.7, 0); s.lineTo(1.1, 0.32); s.lineTo(1.1, 0.12); s.lineTo(0, 0.12); s.lineTo(0, -0.12);
  return new THREE.ShapeGeometry(s).rotateX(-Math.PI / 2); })(), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.85, side: THREE.DoubleSide, depthWrite: false }), 24); arrows.frustumCulled = false; mapG.add(arrows);
const upwind = new THREE.Group(); mapG.add(upwind);                         // the red bracket: from Yellowstone, 900+ miles west
{ const rm = new THREE.MeshBasicMaterial({ color: 0xff3b2f, toneMapped: false }); const bar = new THREE.Mesh(new THREE.BoxGeometry(1, 0.08, 0.08), rm); bar.name = 'bar'; upwind.add(bar);
  for (const s of [0, 1]) { const tk = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.08, 0.7), rm); tk.name = 'tick' + s; upwind.add(tk); }
  const tipC = new THREE.Mesh(new THREE.ConeGeometry(0.22, 0.5, 12).rotateZ(Math.PI / 2), rm); tipC.name = 'tip'; upwind.add(tipC); }

// ------------------------------------------------------------------ the town (beats 3-5): a small-town street; ash falls and piles up; the house across the street
const TOWN = V(-9000, 0, 0);
const town = new THREE.Group(); town.position.copy(TOWN); scene.add(town);
box(240, 0.1, 9, 0, -0.05, 0, mat(0x3a3a3e, 0.95), 0, town);
box(240, 0.16, 3, 0, 0.03, 6, mat(0xb9b0a3, 0.9), 0, town); box(240, 0.16, 3, 0, 0.03, -6, mat(0xb9b0a3, 0.9), 0, town);
box(400, 0.1, 400, 0, -0.1, 0, mat(0x5a6a3e, 1), 0, town);
const HOUSECOL = [0xd8c7a0, 0x9fb8c9, 0xc98f7a, 0xe2d9c4, 0x8fa88a, 0xd6b25e];
function house(x, z, face, col, w = 8, d = 7, hW = 3) {                  // face: +1 -> front faces +z, -1 -> faces -z
  const g = new THREE.Group(); g.position.set(x, 0, z); g.rotation.y = face > 0 ? 0 : Math.PI; town.add(g);
  box(w, hW, d, 0, hW / 2, 0, mat(col, 0.85), 0.03, g);
  for (const wx of [-w * 0.3, w * 0.3]) { box(1.1, 1.2, 0.06, wx, 1.7, d / 2 + 0.02, mat(0x2a3440, 0.25), 0, g); box(1.3, 0.1, 0.12, wx, 1.05, d / 2 + 0.05, mat(0xf2efe6, 0.6), 0, g); }
  box(1.0, 2.0, 0.06, 0, 1.0, d / 2 + 0.02, mat(0x6a4a32, 0.7), 0, g);
  const roofM = mat(0x5a3a32, 0.85), ashM = mat(0x6f6a64, 0.98);
  const L = Math.hypot(d / 2 + 0.4, 2.0), a0 = Math.atan2(2.0, d / 2 + 0.4);
  const slabs = [];
  for (const s of [1, -1]) {                                      // each roof slab hinges at its eave
    const hinge = new THREE.Group(); hinge.position.set(0, hW, s * (d / 2 + 0.4)); g.add(hinge);
    const slab = new THREE.Group(); hinge.add(slab);
    const pieces = [];
    for (let k = 0; k < 3; k++) { const pw = (w + 0.8) / 3, piece = new THREE.Group(); piece.position.x = -(w + 0.8) / 2 + pw * (k + 0.5); slab.add(piece);
      box(pw - 0.02, 0.14, L, 0, 0, -s * L / 2, roofM, 0, piece); const ash = box(pw - 0.02, 0.01, L, 0, 0.08, -s * L / 2, ashM, 0, piece); ash.userData.ash = true; pieces.push({ piece, ash }); }
    hinge.rotation.x = s * a0; slabs.push({ hinge, s, pieces }); }
  const gable = new THREE.Shape(); gable.moveTo(-d / 2, 0); gable.lineTo(d / 2, 0); gable.lineTo(0, 2.0); gable.lineTo(-d / 2, 0);
  for (const sx of [-1, 1]) { const gb = new THREE.Mesh(new THREE.ShapeGeometry(gable), new THREE.MeshStandardMaterial({ color: col, roughness: 0.85, side: THREE.DoubleSide })); gb.rotation.y = Math.PI / 2; gb.position.set(sx * w / 2, hW, 0); gb.castShadow = true; g.add(gb); }
  return { g, slabs, a0, x, z, w, d, hW };
}
const HOUSES = [];
for (let i = 0; i < 9; i++) HOUSES.push(house(-44 + i * 11, -13, 1, HOUSECOL[i % 6]));
for (let i = 0; i < 9; i++) HOUSES.push(house(-44 + i * 11 + 5, 13, -1, HOUSECOL[(i + 3) % 6]));
const COLLAPSE = HOUSES[4];                                       // across the street from him (x = 0)
function car(x, z, col, ry = 0, parent = town) { const g = new THREE.Group(); g.position.set(x, 0, z); g.rotation.y = ry; parent.add(g); const pm = new THREE.MeshPhysicalMaterial({ color: col, roughness: 0.35, clearcoat: 0.8 });
  box(3.8, 0.7, 1.7, 0, 0.6, 0, pm, 0.25, g); box(2.0, 0.6, 1.5, -0.2, 1.15, 0, new THREE.MeshPhysicalMaterial({ color: 0x24303a, roughness: 0.1, metalness: 0.3 }), 0.22, g);
  for (const [wx, wz] of [[-1.25, 0.8], [1.25, 0.8], [-1.25, -0.8], [1.25, -0.8]]) { const w = new THREE.Mesh(new THREE.CylinderGeometry(0.34, 0.34, 0.24, 18).rotateX(Math.PI / 2), mat(0x18181a, 0.7)); w.position.set(wx, 0.34, wz); w.castShadow = true; g.add(w); }
  const cap = box(3.6, 0.01, 1.6, -0.1, 1.46, 0, mat(0x6f6a64, 0.98), 0.0, g); cap.userData.ash = true; g.userData.cap = cap; return g; }
const TCARS = [car(-7, -3.2, 0x2f6fae), car(6, 3.1, 0xc23b3b, Math.PI), car(14, -3.2, 0xe0b040), car(-16, 3.1, 0x3b8a4a, Math.PI)];
for (const [x, z] of [[-3, -5.4], [9, 5.4], [-20, -5.4]]) { box(0.12, 4, 0.12, x, 2, z, mat(0x2a2a2e, 0.5, 0.6), 0, town); box(0.7, 0.1, 0.25, x, 4, z + (z > 0 ? -0.3 : 0.3), mat(0x2a2a2e, 0.5, 0.6), 0, town); }
// the ash blanket: a bumpy surface that rises (time-lapse), and caps on roofs and cars
const ashU = { uT: { value: 0 }, uWet: { value: 0 } };
const ashMat = new THREE.MeshStandardMaterial({ color: 0x77726b, roughness: 0.98 });
ashMat.onBeforeCompile = sh => { sh.uniforms.uWet = ashU.uWet;
  sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vWa;').replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvWa = (modelMatrix * vec4(transformed, 1.0)).xyz;');
  sh.fragmentShader = sh.fragmentShader.replace('#include <common>', `#include <common>\nvarying vec3 vWa; uniform float uWet; ${GLSL_NOISE}`)
    .replace('#include <color_fragment>', `#include <color_fragment>
      { float n = vn(vWa.xz * 1.3) * 0.5 + vn(vWa.xz * 7.0) * 0.3 + hh(floor(vWa.xz * 60.0)) * 0.2; diffuseColor.rgb *= 0.82 + 0.3 * n; diffuseColor.rgb *= 1.0 - 0.45 * uWet; }`)
    .replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\nroughnessFactor = mix(roughnessFactor, 0.35, uWet);'); };
const ashGround = new THREE.Mesh(new THREE.PlaneGeometry(160, 90, 160, 90).rotateX(-Math.PI / 2), ashMat);
{ const p = ashGround.geometry.attributes.position; for (let i = 0; i < p.count; i++) { const x = p.getX(i), z = p.getZ(i); p.setY(i, 0.06 * (fbm2(x / 3, z / 3) - 0.5) + 0.1 * (fbm2(x / 11, z / 11) - 0.5)); } ashGround.geometry.computeVertexNormals(); }
ashGround.receiveShadow = true; town.add(ashGround);
const flakes = cloud(2400, 0.05, 0x8e8984, 0.9);
const rainS = new THREE.InstancedMesh(new THREE.PlaneGeometry(0.007, 0.4), new THREE.MeshBasicMaterial({ color: 0xaab4be, transparent: true, opacity: 0.28, depthWrite: false, side: THREE.DoubleSide }), 700); rainS.frustumCulled = false; scene.add(rainS); rainS.visible = false;
const dustPuffs = puffSystem(260, { amb: 0x6f6c6a, sunCol: 0x8a8580 });
const breath = puffSystem(40, { amb: 0xcfd6e0, sunCol: 0x9aa4b0 });

// ------------------------------------------------------------------ the ash up close (beat 5, second half): jagged shards of rock and glass, magnified
const SHARD = V(9000, 0, 9000);
const shardG = new THREE.Group(); shardG.position.copy(SHARD); scene.add(shardG);
const SHARDS = [];
{ const glassM = new THREE.MeshPhysicalMaterial({ color: 0xb8c4c8, roughness: 0.08, metalness: 0.0, clearcoat: 1, transparent: true, opacity: 0.72, flatShading: true, envMapIntensity: 1.4 });
  const rockM = new THREE.MeshStandardMaterial({ color: 0x5c5650, roughness: 0.75, flatShading: true });
  for (let i = 0; i < 26; i++) { const g = new THREE.OctahedronGeometry(1, 0).toNonIndexed(), p = g.attributes.position;
    const sx = 0.25 + 0.5 * hash1(i * 3), sy = 0.8 + 1.4 * hash1(i * 5), sz = 0.3 + 0.4 * hash1(i * 7);
    for (let k = 0; k < p.count; k++) { const key = Math.round(p.getX(k) * 7 + p.getY(k) * 13 + p.getZ(k) * 29); p.setXYZ(k, p.getX(k) * sx * (0.7 + 0.6 * hash1(key + i)), p.getY(k) * sy * (0.7 + 0.6 * hash1(key * 3 + i)), p.getZ(k) * sz * (0.7 + 0.6 * hash1(key * 5 + i))); }
    g.computeVertexNormals();
    const m = new THREE.Mesh(g, i % 3 === 0 ? rockM : glassM); const a = hash1(i * 11) * 6.28, r = 0.6 + 4 * hash1(i * 13);
    m.position.set(Math.cos(a) * r, -3 + 6 * hash1(i * 17), -2 - 9 * hash1(i * 19)); m.scale.setScalar(0.35 + 0.5 * hash1(i * 23)); m.castShadow = true; shardG.add(m);
    SHARDS.push({ m, p0: m.position.clone(), w: V(hash1(i * 29) - 0.5, hash1(i * 31) - 0.5, hash1(i * 37) - 0.5).multiplyScalar(1.4) }); }
  shardG.add(new THREE.Mesh(new THREE.SphereGeometry(40, 32, 16), new THREE.MeshBasicMaterial({ color: 0x14161a, side: THREE.BackSide })));
  const l1 = new THREE.DirectionalLight(0xfff0e0, 3.0); l1.position.set(4, 6, 5); shardG.add(l1); shardG.add(l1.target);
  const l2 = new THREE.DirectionalLight(0x7fb0ff, 2.0); l2.position.set(-6, -2, -3); shardG.add(l2); shardG.add(l2.target); }

// ------------------------------------------------------------------ the jet in the ash cloud (beat 6), the engine cut open
const JETS = V(9000, 0, 0);
const jetG = new THREE.Group(); jetG.position.copy(JETS); scene.add(jetG);
const R0 = 1.95;
const jet = new THREE.Group(); jetG.add(jet);
const livery = new THREE.MeshPhysicalMaterial({ color: 0xf4f5f7, roughness: 0.35, clearcoat: 0.6 }), blueM = new THREE.MeshPhysicalMaterial({ color: 0x1f4fa8, roughness: 0.4, clearcoat: 0.6 }),
  greyM = new THREE.MeshStandardMaterial({ color: 0x9aa1a8, metalness: 0.6, roughness: 0.4 }), darkM = new THREE.MeshStandardMaterial({ color: 0x16181c, roughness: 0.5 });
const ENG = V(-5.6, 0.95, -2.4);                                  // the left engine (jet space; nose toward -z)
const CUT = new THREE.Plane(V(-1, 0, 0), ENG.x);                  // removes the outer half of the left engine (x < ENG.x), so we see inside
{ const add = (geo, m, x, y, z, rx = 0, ry = 0, rz = 0) => { const o = new THREE.Mesh(geo, m); o.position.set(x, y, z); o.rotation.set(rx, ry, rz); o.castShadow = true; o.receiveShadow = true; jet.add(o); return o; };
  const cy = R0;
  add(new THREE.CylinderGeometry(R0, R0, 30, 48).rotateX(Math.PI / 2), livery, 0, cy, 0);
  add(new THREE.SphereGeometry(R0, 48, 24, 0, Math.PI * 2, 0, Math.PI / 2).rotateX(-Math.PI / 2), livery, 0, cy, -15).scale.set(1, 1, 1.6);
  add(new THREE.ConeGeometry(R0, 7, 48).rotateX(Math.PI / 2), livery, 0, cy + 0.6, 18.5).scale.set(1, 0.7, 1);
  add(new THREE.CylinderGeometry(R0 * 1.004, R0 * 1.004, 30, 48, 1, true, -0.35, 0.7).rotateX(Math.PI / 2), blueM, 0, cy, 0).rotation.z = Math.PI / 2;
  add(new THREE.CylinderGeometry(R0 * 1.004, R0 * 1.004, 30, 48, 1, true, -0.35, 0.7).rotateX(Math.PI / 2), blueM, 0, cy, 0).rotation.z = -Math.PI / 2;
  const wing = new THREE.Shape(); wing.moveTo(0, 0); wing.lineTo(17, 5.5); wing.lineTo(17, 7); wing.lineTo(0, 6); wing.lineTo(0, 0);
  for (const s of [-1, 1]) { const w = add(new THREE.ExtrudeGeometry(wing, { depth: 0.3, bevelEnabled: false }).rotateX(Math.PI / 2), livery, s * 1.0, cy - 0.7, -2.0); w.scale.set(s, 1, 1);
    const ht = new THREE.Shape(); ht.moveTo(0, 0); ht.lineTo(6, 2.6); ht.lineTo(6, 3.6); ht.lineTo(0, 3.4); ht.lineTo(0, 0);
    add(new THREE.ExtrudeGeometry(ht, { depth: 0.2, bevelEnabled: false }).rotateX(Math.PI / 2), livery, s * 0.5, cy + 0.9, 16.5).scale.set(s, 1, 1); }
  const vt = new THREE.Shape(); vt.moveTo(0, 0); vt.lineTo(5, 7); vt.lineTo(7.2, 7); vt.lineTo(6.5, 0); vt.lineTo(0, 0);
  add(new THREE.ExtrudeGeometry(vt, { depth: 0.3, bevelEnabled: false }), blueM, -0.15, cy + 1.6, 14.5, 0, -Math.PI / 2, 0);
  const wins = new THREE.InstancedMesh(new THREE.PlaneGeometry(0.25, 0.34), darkM, 80); const m4 = new THREE.Matrix4(); let k = 0;
  for (const s of [-1, 1]) for (let z = -11; z < 12 && k < 80; z += 0.79) { m4.compose(V(s * (R0 + 0.01), cy + 0.45, z), new THREE.Quaternion().setFromEuler(new THREE.Euler(0, s * Math.PI / 2, 0)), V(1, 1, 1)); wins.setMatrixAt(k++, m4); }
  wins.count = k; jet.add(wins);
  add(new THREE.PlaneGeometry(1.6, 0.6), darkM, 0, cy + 0.85, -16.4, -0.5, 0, 0);
  add(new THREE.CylinderGeometry(0.85, 0.78, 4.2, 28).rotateX(Math.PI / 2), greyM, 5.6, 0.95, -2.4);           // the right engine (whole)
  add(new THREE.CircleGeometry(0.78, 28), darkM, 5.6, 0.95, -4.52, 0, Math.PI); }
// the left engine: a nacelle shell clipped open, with the fan, compressor, the burner and the turbine inside
const ENGINE = { };
{ const eg = new THREE.Group(); eg.position.copy(ENG); jet.add(eg); ENGINE.g = eg;
  const shellM = new THREE.MeshStandardMaterial({ color: 0xc4cad0, metalness: 0.45, roughness: 0.4, side: THREE.DoubleSide });
  const OPEN0 = 330 * D2R, OPENL = 240 * D2R;                         // the shell is cut open on the outer side (facing -x), like a cutaway drawing
  const shell = new THREE.Mesh(new THREE.CylinderGeometry(0.85, 0.72, 4.2, 40, 1, true, OPEN0, OPENL).rotateX(Math.PI / 2), shellM); shell.castShadow = true; eg.add(shell);
  const cutEdge = new THREE.Mesh(new THREE.BoxGeometry(0.02, 1.7, 4.2), new THREE.MeshStandardMaterial({ color: 0xd84a2a, roughness: 0.6 })); cutEdge.visible = false; eg.add(cutEdge);
  const inner = new THREE.MeshStandardMaterial({ color: 0x8a9096, metalness: 0.5, roughness: 0.45 });
  const shaft = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, 3.8, 12).rotateX(Math.PI / 2), inner); eg.add(shaft);
  const spinner = new THREE.Mesh(new THREE.ConeGeometry(0.22, 0.45, 20).rotateX(-Math.PI / 2), mat(0x2a2c30, 0.4, 0.6)); spinner.position.z = -2.0; eg.add(spinner);
  const rotors = [];
  const bladeRing = (z, r0, r1, n, wdt, m) => { const g = new THREE.Group(); g.position.z = z; eg.add(g);
    for (let i = 0; i < n; i++) { const b = new THREE.Mesh(new THREE.BoxGeometry(wdt, r1 - r0, 0.04), m); b.position.y = (r0 + r1) / 2; const piv = new THREE.Group(); piv.rotation.z = i / n * Math.PI * 2; b.rotation.y = 0.35; piv.add(b); g.add(piv); }
    rotors.push(g); return g; };
  bladeRing(-1.75, 0.2, 0.78, 14, 0.13, mat(0x8a9098, 0.35, 0.7));                                  // the big fan
  for (let k = 0; k < 5; k++) bladeRing(-1.2 + k * 0.22, 0.12, 0.46 - k * 0.02, 16, 0.05, inner);    // the compressor stages
  const burner = new THREE.Mesh(new THREE.TorusGeometry(0.36, 0.12, 12, 32), new THREE.MeshStandardMaterial({ color: 0x3a2a20, emissive: 0xff6a1a, emissiveIntensity: 0, roughness: 0.6 })); burner.position.z = 0.15; eg.add(burner);
  const turbM = new THREE.MeshStandardMaterial({ color: 0x5a4a40, metalness: 0.6, roughness: 0.5, emissive: 0xff5010, emissiveIntensity: 0 });
  for (let k = 0; k < 3; k++) bladeRing(0.75 + k * 0.22, 0.12, 0.48, 16, 0.05, turbM);
  const core = new THREE.Mesh(new THREE.CylinderGeometry(0.52, 0.5, 2.6, 28, 1, true, OPEN0, OPENL).rotateX(Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0x9aa0a6, metalness: 0.4, roughness: 0.5, side: THREE.DoubleSide }));
  for (const th of [OPEN0, OPEN0 + OPENL]) { const ed = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.05, 4.2), new THREE.MeshStandardMaterial({ color: 0xd8402a, roughness: 0.6 })); ed.position.set(0.79 * Math.sin(th), -0.79 * Math.cos(th), 0); eg.add(ed); }
  { const py = new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.6, 2.6), greyM); py.position.set(0, 0.95, 0.3); eg.add(py); } core.position.z = 0.35; eg.add(core);
  const glowL = new THREE.PointLight(0xff7a2a, 0, 6, 2); glowL.position.z = 0.4; eg.add(glowL);
  ENGINE.rotors = rotors; ENGINE.burner = burner; ENGINE.turb = turbM; ENGINE.glow = glowL; }
const blobs = new THREE.InstancedMesh(new THREE.SphereGeometry(0.035, 10, 8), new THREE.MeshStandardMaterial({ color: 0x3a2a22, emissive: 0xff7a20, emissiveIntensity: 2.2, roughness: 0.3 }), 160); blobs.frustumCulled = false; ENGINE.g.add(blobs);
const ashIn = cloud(260, 0.05, 0x9a948c, 0.95);                 // ash grains streaming into the intake
const skyPuffs = puffSystem(900, { amb: 0x6e6862, sunCol: 0xb0a090 });
const exhaust = puffSystem(220, { amb: 0x3a3634, sunCol: 0x5a5450, glow: 0xff6a20 });

// ------------------------------------------------------------------ the farm (beat 7): a summer cornfield under an ash-gray sky, snowing
const FARM = V(0, 0, -9000);
const farm = new THREE.Group(); farm.position.copy(FARM); scene.add(farm);
const farmGround = new THREE.Mesh(new THREE.PlaneGeometry(600, 600).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0x5a4a34, roughness: 1 })); farmGround.receiveShadow = true; farm.add(farmGround);
const frostU = { uFrost: { value: 0 } };
const cornGeo = (() => { const parts = []; parts.push(new THREE.CylinderGeometry(0.025, 0.035, 2.2, 5).translate(0, 1.1, 0));
  for (let k = 0; k < 6; k++) { const s = new THREE.Shape(); s.moveTo(0, 0); s.quadraticCurveTo(0.35, 0.2, 0.8, -0.15); s.quadraticCurveTo(0.35, -0.02, 0, 0);
    const lg = new THREE.ShapeGeometry(s, 6); lg.rotateX(-Math.PI / 2 + 0.5); lg.rotateY(k * 2.4); lg.translate(0, 0.5 + k * 0.27, 0); parts.push(lg); }
  const pa = [], na = []; parts.forEach(g => { const q = g.toNonIndexed(); pa.push(...q.attributes.position.array); na.push(...q.attributes.normal.array); });
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pa, 3)); g.setAttribute('normal', new THREE.Float32BufferAttribute(na, 3)); return g; })();
const cornMat = new THREE.MeshStandardMaterial({ color: 0x5d8a2e, roughness: 0.75, side: THREE.DoubleSide });
cornMat.onBeforeCompile = sh => { sh.uniforms.uFrost = frostU.uFrost;
  sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vNw;').replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvNw = normalize(mat3(modelMatrix) * objectNormal);');
  sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vNw; uniform float uFrost;')
    .replace('#include <color_fragment>', `#include <color_fragment>
      diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.42, 0.36, 0.22), uFrost * 0.8);
      diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.92, 0.94, 0.97), uFrost * smoothstep(0.1, 0.8, abs(vNw.y)) * 0.75);`); };
const CORN = [];
for (let r = 0; r < 40; r++) for (let c = 0; c < 90; c++) { const x = -34 + c * 0.75 + 0.2 * hash1(r * 70 + c), z = -3.2 - r * 0.8; CORN.push([x, z, hash1(r * 7 + c * 3) * 6.28, 0.85 + 0.3 * hash1(r + c * 11)]); }
const corn = new THREE.InstancedMesh(cornGeo, cornMat, CORN.length); { const m4 = new THREE.Matrix4(); CORN.forEach(([x, z, a, s], i) => { m4.compose(V(x, 0, z), new THREE.Quaternion().setFromAxisAngle(V(0, 1, 0), a), V(s, s, s)); corn.setMatrixAt(i, m4); }); }
corn.castShadow = true; corn.receiveShadow = true; farm.add(corn);
const snowGround = new THREE.Mesh(new THREE.PlaneGeometry(600, 600).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0xeef2f6, roughness: 0.9, transparent: true, opacity: 0 })); snowGround.position.y = 0.01; snowGround.receiveShadow = true; farm.add(snowGround);
{ const barn = new THREE.Group(); barn.position.set(22, 0, -48); barn.rotation.y = -0.4; farm.add(barn); box(12, 7, 9, 0, 3.5, 0, mat(0x9a2e24, 0.85), 0.05, barn);
  const rf = new THREE.Mesh(new THREE.ConeGeometry(8.5, 4, 4, 1).rotateY(Math.PI / 4), mat(0x3a3a3e, 0.8)); rf.scale.set(1, 1, 0.75); rf.position.y = 9; rf.castShadow = true; barn.add(rf);
  const silo = new THREE.Mesh(new THREE.CylinderGeometry(2.2, 2.2, 13, 24), mat(0xb8b8b4, 0.5, 0.4)); silo.position.set(9, 6.5, 0); silo.castShadow = true; barn.add(silo);
  const dome = new THREE.Mesh(new THREE.SphereGeometry(2.2, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2), mat(0xb8b8b4, 0.5, 0.4)); dome.position.set(9, 13, 0); barn.add(dome); }
{ const fence = mat(0x6a5a48, 0.9); for (let x = -30; x <= 30; x += 2.5) box(0.12, 1.1, 0.12, x, 0.55, -2.4, fence, 0.02, farm); for (const y of [0.5, 0.95]) box(61, 0.08, 0.06, 0, y, -2.4, fence, 0, farm); }
const fsnow = cloud(1600, 0.06, 0xf2f5fa, 0.95);

// ------------------------------------------------------------------ props in his hands: the phone, the ice cream
const phone = new THREE.Group(); scene.add(phone);
{ box(0.072, 0.152, 0.009, 0, 0, 0, mat(0x1c1d22, 0.3, 0.6), 0.004, phone);
  const scr = canvasTex(144, 300, g => { const gr = g.createLinearGradient(0, 0, 0, 300); gr.addColorStop(0, '#5aa0e8'); gr.addColorStop(0.6, '#cfe3f5'); gr.addColorStop(0.61, '#4a6a3a'); gr.addColorStop(1, '#2e4a28'); g.fillStyle = gr; g.fillRect(0, 0, 144, 300);
    g.fillStyle = '#e8c8a8'; g.beginPath(); g.arc(72, 190, 34, 0, 6.3); g.fill(); g.fillStyle = '#ffffff'; g.beginPath(); g.arc(72, 272, 14, 0, 6.3); g.fill(); });
  const s = new THREE.Mesh(new THREE.PlaneGeometry(0.064, 0.142), new THREE.MeshBasicMaterial({ map: scr, toneMapped: false })); s.position.z = 0.0048; phone.add(s); }
const icecream = new THREE.Group(); scene.add(icecream);
{ const cone = new THREE.Mesh(new THREE.ConeGeometry(0.032, 0.12, 16).rotateX(Math.PI), mat(0xc8954a, 0.8)); cone.position.y = -0.02; icecream.add(cone);
  const scoop = new THREE.Mesh(new THREE.SphereGeometry(0.038, 18, 12), mat(0xf2b8c6, 0.6)); scoop.position.y = 0.055; icecream.add(scoop);
  const sc2 = new THREE.Mesh(new THREE.SphereGeometry(0.034, 18, 12), mat(0xf6efe0, 0.6)); sc2.position.y = 0.11; icecream.add(sc2); }

// ------------------------------------------------------------------ the guy
const G = await loadGuy(THREE, '/char/guy', {});
scene.add(G.root); G.root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
const HIP = V(0, 0.95, 0);
function untwistSafe() { for (const S of ['R', 'L']) { const ua = G.bones['uarm' + S], ut = G.bones['uarmTwist' + S]; ua.quaternion.multiply(ut.quaternion); ut.quaternion.identity(); } G.untwist(); }
// ------------------------------------------------------------------ rig: Euler joints + human arm angles (zero = hanging, palm to thigh, thumb forward)
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
const P = {
  stand: { armR: A(6, 8, 0, 16), armL: A(6, 8, 0, 16), neck: [2, 0, 0] },
};
for (const k of Object.keys(P)) { curl(P[k], 'R', 26); curl(P[k], 'L', 26); }
const BONES = Object.keys(G.bones);
const qTmp = new THREE.Quaternion(), eTmp = new THREE.Euler();
const ARM0 = A(4, 8, 0, 14);
function eul(p, n) { return p[n] || (n === 'armR' || n === 'armL' ? ARM0 : [0, 0, 0]); }
function mixPose(a, b, k) { const o = {}; for (const n of new Set([...Object.keys(a), ...Object.keys(b)])) { const x = eul(a, n), y = eul(b, n); o[n] = x.map((v, i) => lerp(v, y[i] ?? 0, k)); } return o; }
function addPose(a, d) { const o = { ...a }; for (const [n, v] of Object.entries(d)) { const x = eul(o, n); o[n] = x.map((w, i) => w + (v[i] || 0)); } return o; }
G.reset();
const ARMREST = {}, HANDREST = {};
for (const S of ['R', 'L']) {
  const af = G.REST['farm' + S].axis.clone();
  ARMREST[S] = { s: S === 'R' ? 1 : -1, a0: G.REST['uarm' + S].axis.clone(), af, hinge: new THREE.Vector3().crossVectors(af, V(0, 0, -1)).normalize() };
  const h = G.man.hands[S]; HANDREST[S] = { u: V(...h.u), n: V(...h.n), w: V(...h.w) };
}
const qAA = (ax, deg) => new THREE.Quaternion().setFromAxisAngle(ax, deg * D2R);
function armQuats(S, a) {
  const R_ = ARMREST[S], h = HANDREST[S], [flex, abd, rot, el, pro, wf = 0, wd = 0] = a;
  const rv = V(flex, 0, R_.s * abd); const ang = rv.length();
  const d = ang > 1e-6 ? V(0, -1, 0).applyQuaternion(qAA(rv.clone().normalize(), ang)) : V(0, -1, 0);
  const Lu = new THREE.Quaternion().setFromUnitVectors(R_.a0, d).multiply(qAA(R_.a0, R_.s * rot));
  const Lf = qAA(R_.hinge, el).multiply(qAA(R_.af, R_.s * pro));
  const Lh = qAA(h.w, R_.s * wf).multiply(qAA(h.n, R_.s * wd));
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
  const hipP = V(root.x, root.y, root.z);
  G.root.quaternion.copy(R); G.root.position.copy(hipP).sub(HIP.clone().applyQuaternion(R));
  G.root.updateMatrixWorld(true);
  LAST = lim;
}
// ------------------------------------------------------------------ hands on things: solved over real joint ranges (world-space targets)
const PALM = S => HANDREST[S].u.clone().multiplyScalar(0.06).addScaledVector(HANDREST[S].n, 0.012);
const _m = new THREE.Matrix4(), _q = new THREE.Quaternion();
const wp = o => o.getWorldPosition(new THREE.Vector3()), wq = o => o.getWorldQuaternion(new THREE.Quaternion());
function torsoInside(p) {
  const c = wp(G.bones.chest), sp = wp(G.bones.spine1);
  if (p.y > c.y + 0.22 || p.y < sp.y - 0.2) return 0;
  const iq = wq(G.bones.chest).invert(), d = p.clone().sub(c).applyQuaternion(iq);
  const ex = d.x / 0.17, ez = d.z / 0.13; const r = Math.hypot(ex, ez); return r < 1 ? (1 - r) * 0.13 : 0;
}
function handFK(S, a) {
  setArm(S, a); const hb = G.bones['hand' + S];
  G.bones['uarm' + S].updateMatrixWorld(true);
  const M = _m.copy(hb.matrixWorld); const qh = _q.setFromRotationMatrix(M);
  return { p: PALM(S).applyMatrix4(M), n: HANDREST[S].n.clone().applyQuaternion(qh), w: HANDREST[S].w.clone().applyQuaternion(qh), u: HANDREST[S].u.clone().applyQuaternion(qh),
    el: wp(G.bones['farm' + S]), sh: wp(G.bones['uarm' + S]) };
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
    return c; };
  const m = MEM[key]; const prev = m && m.frame === frame - 1 ? m.a : null;
  const COLD = [A(40, 15, 0, 80, 0), A(60, 25, 20, 60, 40), A(30, 40, -20, 100, -30), A(80, 10, 0, 110, 60), A(50, 30, 30, 40, 70), A(20, 20, -30, 120, -60), A(60, 10, -10, 100, 75), A(40, 20, 10, 90, -75)];
  const descend = (s0, big) => { let a = s0.map((v, i) => clamp(v, ARM_LIM[i][0], ARM_LIM[i][1])), ca = cost(a);
    for (let step = big; step >= 0.25; step /= 2) { let imp = true, g = 0;
      while (imp && g++ < 10) { imp = false; for (let i = 0; i < 7; i++) for (const sg of [1, -1]) { const b = a.slice(); b[i] = clamp(b[i] + sg * step, ARM_LIM[i][0], ARM_LIM[i][1]); const cb = cost(b); if (cb < ca - 1e-9) { a = b; ca = cb; imp = true; } } } }
    return { a, c: ca }; };
  let best = null;
  if (!prev && tg.seed) { const r = descend(tg.seed, 8); if (r.c < 8) best = r; }          // a good seed is trusted (keeps the same arm across a cut / the loop)
  if (!best) for (const s0 of prev ? [prev] : (tg.seed ? [tg.seed, ...COLD] : COLD)) { const r = descend(s0, prev ? 4 : 16); if (!best || r.c < best.c) best = r; }
  if (prev && best.c > 20) for (const s0 of (tg.seed ? [tg.seed, ...COLD] : COLD)) { const r = descend(s0, 16); if (r.c < best.c) best = r; }
  MEM[key] = { frame, a: best.a }; return best;
}
// body-relative points: the mouth (from the face rig) and a frame on his chest
G.reset(); G.root.updateMatrixWorld(true);
const MOUTH_L = V(0, G.man.mouthY, G.man.mouthZ ?? -0.105).applyMatrix4(G.bones.head.matrixWorld.clone().invert());
const mouthW = () => MOUTH_L.clone().applyMatrix4(G.bones.head.matrixWorld);
const yawQ = deg => new THREE.Quaternion().setFromAxisAngle(V(0, 1, 0), deg * D2R);
const fwdOf = yaw => V(-Math.sin(yaw * D2R), 0, -Math.cos(yaw * D2R));          // the way he faces (yaw 0 = -z)
const rightOf = yaw => V(Math.cos(yaw * D2R), 0, -Math.sin(yaw * D2R));         // his right
function plantFeet(base, yaw, spread = 1) { for (const [S, sx, sz] of [['R', 0.11, -0.02], ['L', -0.11, 0.02]]) { const f = base.clone().addScaledVector(rightOf(yaw), sx * spread).addScaledVector(fwdOf(yaw), -sz).add(V(0, 0.102, 0));
  G.legIK(S, f, f.clone().add(V(0, 0.45, 0)).addScaledVector(fwdOf(yaw), 1.0), yawQ(yaw)); } }
function blinkAt(s) { const u = ((s + 40) % 3.7) / 0.16; return u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0; }

// ------------------------------------------------------------------ the story: eruption clock, the guy per beat
// eruption age: the blast is 0.3 s before the end of beat 9 (so beat 9 loops straight into beat 0)
function eruptAge(t) { const b = beatAt(t), lt = t - B[b];
  if (b === 0) return 0.3 + lt; if (b === 9) return 0.3 - (DUR[9] - lt); if (b === 1) return 9 + lt; return null; }
const OVER = V(0, 0, 0.3);                                       // where he stands at the overlook (he faces +z, the camera; the valley is behind him)
// the selfie: phone at arm's length up in front of his face, screen toward him (right hand)
function selfieHand(look) { const c = wp(G.bones.neck), f = fwdOf(180), r = rightOf(180);
  return { S: 'R', p: c.clone().addScaledVector(f, 0.46).addScaledVector(r, 0.17).add(V(0, 0.16, 0)), n: f.clone().negate().add(V(0, -0.15, 0)).normalize(), c: 30, seed: LOOPARM || A(95, 20, -10, 35, 0) }; }
let LOOPARM = null;
function ruinFace(k, t) { return { fear: k, jaw: 0.55 * k, browIn: 0.35 * k, smile: 0.55 * (1 - k), blink: k > 0.3 ? 0 : blinkAt(t), look: [0, 0.05] }; }
function overlookGuy(ea, t) {                                    // ea: eruption age (negative: before the blast)
  const turn = smooth(0.25, 0.95, ea), fearK = smooth(0.3, 0.8, ea);
  const pose = addPose(P.stand, { spine2: [0, -10 * turn, 0], chest: [0, -8 * turn, 0], neck: [6 * turn, -38 * turn, 0], head: [4 * turn, -20 * turn, 0],
    armL: A(8 + 6 * fearK, 10 + 6 * fearK, 0, 20 + 20 * fearK) });
  pose.neck[0] += -3 + 2 * Math.sin(t * 1.4) * (1 - turn); pose.head[2] = 6 * (1 - turn);   // a little head tilt for the photo
  return { pose, root: { x: OVER.x, y: 0.95 - 0.01 * fearK, z: OVER.z, yaw: 180 }, face: ruinFace(fearK, t), hands: ['selfie'], feet: OVER, yaw: 180, show: true, ground: 0 };
}
// the run (beat 1): planted feet (no skating), arms pumping, a look back over the shoulder
const RUN_V = 3.7, RUN_F = 1.4, STANCE = 0.27, STRIDE = RUN_V / RUN_F;
function runGuy(lt) {
  const zH = RZ0 + RUN_V * lt, ph = lt * RUN_F;
  const foot = (off) => { const q = ph + off, n = Math.floor(q), f = q - n;
    const zp = k => RZ0 + RUN_V * ((k - off + STANCE / 2) / RUN_F);          // plant spot: under the hip at mid-stance
    if (f < STANCE) return { z: zp(n), y: 0.102, up: 0 };
    const s = (f - STANCE) / (1 - STANCE), e = 1 - Math.pow(1 - s, 1.7);         // the foot comes off the ground and swings through quickly, then reaches
    return { z: lerp(zp(n), zp(n + 1), e), y: 0.102 + 0.36 * Math.sin(Math.PI * Math.pow(s, 0.6)), up: Math.sin(Math.PI * s) }; };
  const fR = foot(0), fL = foot(0.5);
  const bob = 0.035 * Math.cos(2 * Math.PI * ph * 2);
  const look = smooth(0.5, 0.62, lt / DUR[1]) * (1 - smooth(0.78, 0.9, lt / DUR[1]));
  const sw = Math.sin(2 * Math.PI * ph);                         // + when the right leg swings forward
  const pose = addPose(P.stand, { spine1: [-12, 0, 0], spine2: [-4, 7 * sw, 0], neck: [6, -50 * look, 0], head: [4, -25 * look, 0],
    armR: A(15 - 37 * sw, 14, 0, 88 + 8 * sw), armL: A(15 + 37 * sw, 14, 0, 88 - 8 * sw) });
  curl(pose, 'R', 55); curl(pose, 'L', 55);
  return { pose, root: { x: RX, y: 0.95 + bob, z: zH, yaw: 180, tilt: -10 }, face: { fear: 1, jaw: 0.6 + 0.15 * Math.sin(lt * 9), browIn: 0.4, blink: 0, look: [0, 0.1] },
    hands: [], runFeet: { R: V(RX - 0.11, fR.y, fR.z), L: V(RX + 0.11, fL.y, fL.z), upR: fR.up, upL: fL.up }, yaw: 180, show: true, ground: 0 };
}
// the town (beats 3-5)
const TOWN_HOME = TOWN.clone().add(V(0, 0, 1.2));
function ashDepth(t) { const b = beatAt(t), lt = t - B[b]; if (b === 3) return lerp(0.04, 0.92, smooth(0.08, 0.92, lt / DUR[3])); if (b === 4 || b === 5) return 0.92; return 0; }
function townGuy(b, lt) {
  const d = DUR[b], u = lt / d;
  if (b === 3) { const look = smooth(0.35, 0.55, u);           // catches ash on his palm, then looks around at the rising ash
    const pose = addPose(P.stand, { neck: [-18 + 22 * look, 22 * look * Math.sin(lt * 0.9), 0], head: [-8 + 8 * look, 0, 0], spine1: [-3, 0, 0], armR: A(10, 10, 0, 25) });
    return { pose, root: { x: TOWN_HOME.x, y: 0.95, z: TOWN_HOME.z, yaw: 180 }, face: { fear: 0.25 + 0.6 * look, browIn: 0.4, jaw: 0.25 * look, blink: blinkAt(lt), look: [0, -0.3 + 0.4 * look] }, hands: ['palm'], feet: TOWN_HOME, yaw: 180, show: true, ground: TOWN.y }; }
  if (b === 4) { const fl = smooth(0.66, 0.74, u) * (1 - 0.6 * smooth(0.82, 1.0, u));   // flinches when the roof goes
    const pose = addPose(P.stand, { spine1: [4 * fl, 0, 0], neck: [6 - 10 * fl, -6, 0], armR: A(20 + 35 * fl, 18, 0, 60 + 40 * fl), armL: A(20 + 35 * fl, 18, 0, 60 + 40 * fl) });
    return { pose, root: { x: TOWN_HOME.x, y: 0.95 - 0.03 * fl, z: TOWN_HOME.z, yaw: 0 }, face: { fear: 0.7, jaw: 0.3 + 0.4 * fl, browIn: 0.4, blink: blinkAt(lt) }, hands: [], feet: TOWN_HOME, yaw: 0, show: true, ground: TOWN.y }; }
  // b === 5: coughs into his hand
  const cg = Math.max(0, Math.sin(lt * 9.5)) ** 2 * smooth(0.1, 0.3, lt);
  const pose = addPose(P.stand, { spine1: [-8 - 8 * cg, 0, 0], spine2: [-4 - 4 * cg, 0, 0], neck: [-6 - 6 * cg, 0, 0], head: [-2 - 3 * cg, 0, 0], armL: A(16, 12, 0, 40) });
  return { pose, root: { x: TOWN_HOME.x, y: 0.95 - 0.015 * cg, z: TOWN_HOME.z, yaw: 180 }, face: { fear: 0.6, squint: 0.4 + 0.5 * cg, browIn: 0.6, pain: 0.5 * cg, blink: 0, jaw: 0.2 + 0.3 * cg }, hands: ['mouth'], feet: TOWN_HOME, yaw: 180, show: true, ground: TOWN.y, cough: cg };
}
// the farm (beat 7): rubs his hands, blows into them, shivers
const FARM_HOME = FARM.clone().add(V(0, 0, 0.4));
function farmGuy(lt) {
  const shiv = 1.2 * Math.sin(lt * 2 * Math.PI * 7.5), blow = smooth(0.45, 0.6, lt / DUR[7]) * (1 - smooth(0.85, 0.97, lt / DUR[7]));
  const pose = addPose(P.stand, { spine1: [-6, 0, shiv * 0.5], spine2: [-4, 0, 0], chest: [-3, 0, 0], neck: [-6 - 10 * blow + shiv, 0, 0], head: [-4, 0, 0] });
  return { pose, root: { x: FARM_HOME.x, y: 0.94, z: FARM_HOME.z, yaw: 180 }, face: { fear: 0.4, browIn: 0.6, squint: 0.3, jaw: 0.1 + 0.25 * blow, oh: 0.6 * blow, blink: blinkAt(lt) },
    hands: ['rubR', 'rubL'], feet: FARM_HOME, yaw: 180, show: true, ground: FARM.y, blow };
}
// the geyser (beat 8): at the boardwalk rail, licking an ice cream, happy
const GEY_HOME = BW.clone().add(V(-1.2, BWY, 0.25)), GYAW = 160;
const lickAt = s => { const ph = ((s % 2.6) + 2.6) % 2.6; return smooth(0.9, 1.3, ph) * (1 - smooth(1.7, 2.05, ph)); };
function coneHand(s) { const c = wp(G.bones.neck), f = fwdOf(GYAW), r = rightOf(GYAW), lk = lickAt(s), m = mouthW();
  const rest = c.clone().addScaledVector(f, 0.33).addScaledVector(r, 0.16).add(V(0, -0.2, 0));
  const lip = m.clone().addScaledVector(f, 0.09).addScaledVector(r, 0.03).add(V(0, -0.11, 0));
  return { S: 'R', p: rest.lerp(lip, lk), n: r.clone().negate().lerp(r.clone().negate().addScaledVector(f, -0.95).normalize(), lk).normalize(), u: f.clone().lerp(f.clone().addScaledVector(r, -0.75).add(V(0, 0.7, 0)).normalize(), lk).normalize(), c: 62, seed: A(40, 12, 0, 110, 40) }; }
function geyserGuy(lt) { const lk = lickAt(lt);
  const back = smooth(0.3, 0.45, lt / DUR[8]) * (1 - smooth(0.62, 0.78, lt / DUR[8]));      // glances back at the geyser
  const pose = addPose(P.stand, { neck: [-4 - 9 * lk * (1 - back) - 2 * Math.sin(lt * 1.1) + 8 * back, 40 * back - 6 * lk, 0], head: [-6 - 6 * lk, 22 * back, 0], spine2: [0, 8 * back, 0], armL: A(8, 10, 0, 18) });
  return { pose, root: { x: GEY_HOME.x, y: GEY_HOME.y + 0.95, z: GEY_HOME.z, yaw: GYAW }, face: { smile: 0.75 * (1 - lk), oh: 0.5 * lk, jaw: 0.25 * lk, blink: blinkAt(lt), look: [0, 0.15] }, hands: back > 0.01 && lickAt(lt) < 0.01 ? ['cone'] : ['cone'], feet: GEY_HOME, yaw: GYAW, show: true, ground: GEY_HOME.y, lt }; }
function guyAt(t) {
  const b = beatAt(t), lt = t - B[b], ea = eruptAge(t);
  if (b === 0 || b === 9) return overlookGuy(ea, t);
  if (b === 1) return runGuy(lt);
  if (b >= 3 && b <= 5) { if (b === 5 && lt > DUR[5] * SHARD_CUT) return { pose: P.stand, root: { x: 0, y: -50, z: 0 }, face: {}, hands: [], show: false }; return townGuy(b, lt); }
  if (b === 7) return farmGuy(lt);
  if (b === 8) return geyserGuy(lt);
  return { pose: P.stand, root: { x: 0, y: -50, z: 0 }, face: {}, hands: [], show: false };
}
const SHARD_CUT = 0.5;                                           // beat 5: the cut from his cough to the ash up close
function handTarget(name, g, t) {
  if (name === 'selfie') return selfieHand();
  if (name === 'palm') { const c = wp(G.bones.chest), f = fwdOf(180), r = rightOf(180), lt = t - B[3];
    return { S: 'L', p: c.clone().addScaledVector(f, 0.36).addScaledVector(r, -0.12).add(V(0, -0.08 + 0.02 * Math.sin(lt * 1.3), 0)), n: V(0, 1, 0), u: f.clone().add(V(0, 0.15, 0)).addScaledVector(r, -0.3).normalize(), c: 12, seed: A(45, 10, 0, 85, 70) }; }
  if (name === 'mouth') { const m = mouthW(), f = fwdOf(180), r = rightOf(180);
    return { S: 'R', p: m.clone().addScaledVector(f, 0.035).add(V(0, -0.02, 0)), n: f.clone().negate(), u: r.clone().negate().add(V(0, 0.55, 0)).normalize(), c: 22, seed: A(55, 15, 0, 130, 20) }; }
  if (name === 'rubR' || name === 'rubL') { const c = wp(G.bones.chest), f = fwdOf(180), r = rightOf(180), lt = t - B[7];
    const rub = 0.035 * Math.sin(lt * 2 * Math.PI * 2.2), up = smooth(0.42, 0.56, lt / DUR[7]) * (1 - smooth(0.86, 0.98, lt / DUR[7]));
    const mid = c.clone().addScaledVector(f, 0.3).add(V(0, -0.02, 0)).lerp(mouthW().addScaledVector(f, 0.09).add(V(0, -0.02, 0)), up);
    const s = name === 'rubR' ? 1 : -1;
    return { S: name === 'rubR' ? 'R' : 'L', p: mid.clone().addScaledVector(r, s * 0.025).add(V(0, s * rub * (1 - up), 0)), n: r.clone().multiplyScalar(-s), u: V(0, 1, 0).addScaledVector(f, 0.35).normalize(), c: 18 + 20 * up, seed: A(45, 12, 0, 115, 60) }; }
  if (name === 'cone') return coneHand(g.lt);
  return null;
}

// ------------------------------------------------------------------ cameras
function shakeV(t, a) { return V(vn1(t * 14, 1) * a * 0.5, vn1(t * 14, 2) * a, vn1(t * 14, 3) * a); }
function camOverlook(ea, t) {                                    // in front of him, a little low, the valley and the vent behind him
  const k = smooth(0.0, 1.2, ea), boom = Math.exp(-Math.max(0, ea - 0.1) * 1.6) * (ea > 0.05 ? 1 : 0);
  const pos = V(0.3 - 0.05 * k, 1.35 - 0.12 * k, 3.3 + 0.8 * k).add(shakeV(ea + 50, 0.06 * boom));   // shake on the eruption clock: seamless across the loop
  const tgt = V(0.3 + 0.4 * k, 1.75 + 1.3 * k, -6);
  return { pos, tgt, fov: 54 + 4 * k };
}
function camAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b], u = lt / d, ea = eruptAge(t);
  if (b === 0 || b === 9) return camOverlook(ea, t);
  if (b === 1) { const zH = RZ0 + RUN_V * lt; return { pos: V(RX + 0.75 - 0.2 * u, 0.85 + 0.25 * u, zH + 4.2 - 0.6 * u).add(shakeV(t, 0.03)), tgt: V(RX + 0.35, 4.5 + 6 * u, zH - 20), fov: 58 }; }
  if (b === 2) { const k = sm(u); return { pos: MAP.clone().add(V(1.5, 80 - 6 * k, 30)), tgt: MAP.clone().add(V(1.5, 0, 1.5)), fov: 46 }; }
  if (b === 3) { const k = sm(u); return { pos: TOWN_HOME.clone().add(V(0.25 + 1.1 * k, 1.5 + 1.0 * k, 1.5 + 3.0 * k)), tgt: TOWN_HOME.clone().add(V(0.05 - 0.4 * k, 1.35 - 0.2 * k, 0)), fov: 46 + 6 * k }; }
  if (b === 4) { const shk = smooth(0.66, 0.7, u) * Math.exp(-Math.max(0, u - 0.68) * 12); return { pos: TOWN_HOME.clone().add(V(0.38, 2.2, 2.75 - 0.3 * u)).add(shakeV(t, 0.08 * shk)), tgt: TOWN.clone().add(V(0.3, 2.5, -12)), fov: 50 }; }
  if (b === 5) { if (u < SHARD_CUT) return { pos: TOWN_HOME.clone().add(V(0.05, 1.62, 1.05 - 0.15 * u)), tgt: TOWN_HOME.clone().add(V(0.02, 1.52, 0)), fov: 40 };
    const v = (u - SHARD_CUT) / (1 - SHARD_CUT); return { pos: SHARD.clone().add(V(0.4 - 0.8 * v, 0.2 * v, 4.5 - 1.6 * v)), tgt: SHARD.clone().add(V(0, 0, -4)), fov: 50 }; }
  if (b === 6) { const k = sm(u), e = JETS.clone().add(ENG); return { pos: e.clone().add(V(-9 + 6.2 * k, 1.2 - 1.3 * k, -7 + 7.3 * k)), tgt: e.clone().add(V(0.3 + 1.5 * (1 - k), 0.3 * (1 - k), 0.3)), fov: 50 }; }
  if (b === 7) return { pos: FARM_HOME.clone().add(V(0.45 - 0.15 * u, 1.55, 3.0 - 0.6 * u)), tgt: FARM_HOME.clone().add(V(-0.1, 1.5, 0)), fov: 46 };
  if (b === 8) { const f = fwdOf(GYAW), r = rightOf(GYAW); return { pos: GEY_HOME.clone().addScaledVector(f, 2.7 - 0.3 * u).addScaledVector(r, -0.5).add(V(0, 1.25, 0)), tgt: GEY_HOME.clone().addScaledVector(f, -6).addScaledVector(r, 1.2).add(V(0, 3.6, 0)), fov: 54 }; }
  return { pos: V(0, 2, 5), tgt: V(0, 1, 0), fov: 45 };
}

// ------------------------------------------------------------------ clipping: his body points vs every solid thing near him, and vs his own body
const SOLIDS = [];
const sbox = (name, obj, min, max) => SOLIDS.push({ name, obj, box: new THREE.Box3(min, max) });
sbox('railing', park, V(-4.2, 0, RAIL_Z - 0.1), V(4.2, 1.1, RAIL_Z + 0.1));
sbox('sign', sign, V(-0.9, 0, -0.15), V(0.9, 1.65, 0.07));
{ const bwRail = new THREE.Object3D(); bwRail.position.copy(BW); park.add(bwRail); sbox('boardwalk rail', bwRail, V(-20, BWY, -1.25), V(20, 1.34, -1.05)); }
TCARS.forEach(c => sbox('car', c, V(-1.9, 0.25, -0.85), V(1.9, 1.45, 0.85)));
{ const fenceO = new THREE.Object3D(); farm.add(fenceO); sbox('fence', fenceO, V(-31, 0, -2.5), V(31, 1.1, -2.3)); }
const BODYPTS = { handR: 0.035, handL: 0.035, farmR: 0.035, farmL: 0.035, uarmR: 0.045, uarmL: 0.045, head: 0.09, chest: 0.12, hips: 0.1, shinR: 0.05, shinL: 0.05, footR: 0.04, footL: 0.04 };
const TIPSEG = {}; G.reset(); G.root.updateMatrixWorld(true);
for (const S of ['R', 'L']) for (const f of ['index', 'middle', 'pinky', 'thumb']) { const b1 = G.bones[f + '1' + S], b2 = G.bones[f + '2' + S]; TIPSEG[f + S] = wp(b2).sub(wp(b1)).multiplyScalar(0.95).applyQuaternion(wq(b2).invert()); }
const tip = (f, S) => { const b2 = G.bones[f + '2' + S]; return wp(b2).add(TIPSEG[f + S].clone().applyQuaternion(wq(b2))); };
function segDist(p, a, b) { const ab = b.clone().sub(a), t = clamp(p.clone().sub(a).dot(ab) / ab.lengthSq(), 0, 1); return p.distanceTo(a.clone().addScaledVector(ab, t)); }
let PROPHELD = null;
function clipScan(groundY) {
  const out = []; if (!G.root.visible) return out; scene.updateMatrixWorld(true);
  const pts = Object.entries(BODYPTS).map(([n, r]) => [n, wp(G.bones[n]), r]);
  for (const S of ['R', 'L']) for (const f of ['index', 'middle', 'pinky', 'thumb']) pts.push([f + ' tip ' + S, tip(f, S), 0.008]);
  const hipP = wp(G.bones.hips), neckP = wp(G.bones.neck), headC = wp(G.bones.head).add(V(0, 0.09, 0).applyQuaternion(wq(G.bones.head)));
  for (const [n, p, r] of pts) {
    if (groundY !== null && p.y - r < groundY - 0.015) out.push({ what: n, into: 'ground', depth: +((groundY - (p.y - r)) * 100).toFixed(1) });
    for (const S of SOLIDS) { if (!S.obj.visible || !S.obj.parent?.visible && S.obj.parent !== scene) continue; const q = p.clone().applyMatrix4(S.obj.matrixWorld.clone().invert()), bx = S.box;
      const dx = Math.min(q.x - bx.min.x, bx.max.x - q.x), dy = Math.min(q.y - bx.min.y, bx.max.y - q.y), dz = Math.min(q.z - bx.min.z, bx.max.z - q.z);
      const dd = Math.min(dx, dy, dz) + r; if (dx > -r && dy > -r && dz > -r && dd > 0.012) out.push({ what: n, into: S.name, depth: +(dd * 100).toFixed(1) }); }
    if (/^(hand|farm|index|middle|pinky|thumb)/.test(n)) {
      const dT = segDist(p, hipP, neckP) - 0.11 - r; if (dT < -0.012) out.push({ what: n, into: 'his own body', depth: +(-dT * 100).toFixed(1) });
      const dH = p.distanceTo(headC) - 0.1 - r; const nearMouth = (LASTG && LASTG.hands.includes('mouth')) || (LASTG && LASTG.blow > 0.2);
      if (dH < -0.012 && !(nearMouth && dH > -0.04) && !/R$/.test(n) || dH < -0.04) out.push({ what: n, into: 'his own head', depth: +(-dH * 100).toFixed(1) }); }
  }
  { const a = PALM('R').applyMatrix4(G.bones.handR.matrixWorld), b = PALM('L').applyMatrix4(G.bones.handL.matrixWorld), dd = a.distanceTo(b); if (dd < 0.02) out.push({ what: 'palm R', into: 'palm L', depth: +((0.02 - dd) * 100).toFixed(1) }); }
  if (PROPHELD && PROPHELD.visible) { const dT = segDist(PROPHELD.position, hipP, neckP) - 0.11 - 0.03; if (dT < -0.012) out.push({ what: 'prop', into: 'his body', depth: +(-dT * 100).toFixed(1) });
    const dH = PROPHELD.position.distanceTo(headC) - 0.1 - 0.03; if (dH < -0.02 && PROPHELD !== icecream) out.push({ what: 'prop', into: 'his head', depth: +(-dH * 100).toFixed(1) }); }
  return out;
}

// ------------------------------------------------------------------ per-frame update
let LASTF = -10, LASTG = null;
const STAGE = { park, mapG, town, shardG, jetG, farm };
function update(t, frame) {
  t = ((t % TOTAL) + TOTAL) % TOTAL;
  const b = beatAt(t), lt = t - B[b], d = DUR[b], u = lt / d, ea = eruptAge(t);
  const where = (b === 0 || b === 1 || b === 8 || b === 9) ? 'park' : b === 2 ? 'mapG' : (b >= 3 && b <= 5) ? (b === 5 && u > SHARD_CUT ? 'shardG' : 'town') : b === 6 ? 'jetG' : 'farm';
  for (const [k, o] of Object.entries(STAGE)) o.visible = k === where;
  // ---- the guy
  const g = guyAt(t); LASTG = g;
  applyPose(g.pose, g.root);
  if (g.feet) plantFeet(g.feet, g.yaw);
  if (g.runFeet) for (const S of ['R', 'L']) { const f = g.runFeet[S], up = g.runFeet['up' + S];
    G.legIK(S, f, f.clone().add(V(0, 0.5, 0)).addScaledVector(fwdOf(180), 1.0), yawQ(180).multiply(qAA(V(1, 0, 0), -35 * up))); }
  G.root.updateMatrixWorld(true);
  for (const name of g.hands) { const h = handTarget(name, g, t); if (!h) continue;
    const sol = solveHand(h, name + b + (b === 5 ? 'a' : ''), frame); setArm(h.S, sol.a); LAST['arm' + h.S] = sol.a; LAST['cost' + h.S] = sol.c;
    const pp = {}; curl(pp, h.S, h.c ?? 30); for (const [n, e] of Object.entries(pp)) G.bones[n].quaternion.copy(G.REST[n].q).multiply(qTmp.setFromEuler(eTmp.set(e[0] * D2R, e[1] * D2R, e[2] * D2R))); }
  if (!g.hands.length) { delete LAST.costR; delete LAST.costL; }
  G.root.updateMatrixWorld(true); untwistSafe(); G.face(g.face); G.root.visible = g.show; G.root.updateMatrixWorld(true);
  const C = camAt(t); camera.position.copy(C.pos); camera.up.set(0, 1, 0); camera.lookAt(C.tgt); camera.fov = C.fov; camera.updateProjectionMatrix();
  // ---- props in his hands
  phone.visible = g.show && g.hands.includes('selfie'); icecream.visible = g.show && g.hands.includes('cone'); PROPHELD = phone.visible ? phone : icecream.visible ? icecream : null;
  if (phone.visible) { const hb = G.bones.handR, q = wq(hb), n = HANDREST.R.n.clone().applyQuaternion(q), pc = PALM('R').applyMatrix4(hb.matrixWorld);
    phone.position.copy(pc).addScaledVector(n, 0.026); const zA = n.clone(), yA = V(0, 1, 0).sub(zA.clone().multiplyScalar(zA.y)).normalize(), xA = new THREE.Vector3().crossVectors(yA, zA);
    phone.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(xA, yA, zA)); }
  if (icecream.visible) { const hb = G.bones.handR, q = wq(hb), n = HANDREST.R.n.clone().applyQuaternion(q), w = HANDREST.R.w.clone().applyQuaternion(q), pc = PALM('R').applyMatrix4(hb.matrixWorld);
    icecream.position.copy(pc).addScaledVector(n, 0.03).addScaledVector(w, 0.0).add(V(0, 0.02, 0)); icecream.quaternion.setFromAxisAngle(rightOf(GYAW), 0.3 * lickAt(g.lt)); }
  // ---- the park: the eruption column, ballistic bombs, the flash, the pyroclastic flow, the geyser
  colPuffs.begin(); flowPuffs.begin(); geyPuffs.begin();
  const parkOn = where === 'park';
  if (parkOn && ea !== null && ea > 0) {
    for (let i = 0; i < 1800; i++) { const bt = (i / 1800) ** 1.3 * 9, a = ea - bt; if (a < 0) continue;
      const hA = hash1(i * 3.1), hB = hash1(i * 5.7), hC = hash1(i * 9.3), hD = hash1(i * 13.9);
      const Hm = 260 + 340 * hA, y = Hm * (1 - Math.exp(-a / (bt < 0.5 ? 0.45 + 0.4 * hB : 0.9 + 0.8 * hB))) * (bt < 0.5 ? 0.75 : 1);
      const top = smooth(0.55, 1.0, y / Hm), th = hC * 6.283 + a * 0.3;
      const r = (10 + 30 * hD + 14 * a) * (0.4 + 0.6 * smooth(0, 60, y)) + top * (40 + 70 * a) * hB;
      const s = (22 + 30 * hB + 12 * a + 40 * top + (bt < 0.5 ? 30 * smooth(0, 0.6, a) : 0)) * smooth(0, 0.18, a);
      const gl = Math.pow(clamp(1 - y / 90, 0, 1), 2) * 0.9;
      const shade = 0.36 + 0.24 * smooth(0, 300, y) + 0.08 * hA;
      colPuffs.add(VENT.x + Math.cos(th) * r, VENT.y + 20 + y, VENT.z + Math.sin(th) * r * 0.8, s, shade, shade * 0.96, shade * 0.92, 0.95 * smooth(0, 0.12, a), gl); } }
  flash.intensity = parkOn && ea !== null ? 8e5 * Math.exp(-Math.max(0, ea) * 3) * (ea > 0 ? 1 : 0) : 0;
  skyU.uFlash.value = parkOn && ea !== null && ea > 0 ? 0.5 * Math.exp(-ea * 3) : 0;
  bombs.visible = parkOn && ea !== null && ea > 0 && ea < 9;
  if (bombs.visible) { const m4 = new THREE.Matrix4(); for (let i = 0; i < 40; i++) { const t0 = 0.05 + 2.4 * hash1(i * 3), a = ea - t0, vy = 70 + 60 * hash1(i * 5), vh = 15 + 30 * hash1(i * 7), th = hash1(i * 9) * 6.283;
      const y = VENT.y + 30 + vy * a - 4.9 * 2.0 * a * a; if (a < 0 || y < VENT.y - 10) { m4.makeScale(0, 0, 0); bombs.setMatrixAt(i, m4); continue; }
      m4.compose(V(VENT.x + Math.cos(th) * vh * a, y, VENT.z + Math.sin(th) * vh * a), new THREE.Quaternion().setFromEuler(new THREE.Euler(a * 3, a * 2, 0)), V(2.5, 2.5, 2.5)); bombs.setMatrixAt(i, m4); }
    bombs.instanceMatrix.needsUpdate = true; }
  if (parkOn && b === 1) { const zF = RZ0 - 125 + 22 * lt;
    for (let i = 0; i < 1500; i++) { const hA = hash1(i * 2.3), hB = hash1(i * 4.1), hC = hash1(i * 6.7), hD = hash1(i * 8.9);
      const x = RX - 230 + 460 * hA, dep = 380 * hB ** 1.6, zf = zF - 18 * (vn1(x / 45, 3) + 1) - dep;
      const Hd = 22 + 95 * smooth(0, 160, dep) * (0.6 + 0.4 * vn1(x / 80, 5)), y0 = terrainH(x, zf);
      const s = (13 + 22 * hC + dep * 0.06) * (1 + 0.15 * Math.sin(t * 0.9 + i));
      const roll = t * (1.2 + hD) + i, y = y0 + Hd * hD ** 0.8 + s * 0.35 + Math.sin(roll) * s * 0.15, z = zf + Math.cos(roll) * s * 0.18;
      const shade = 0.33 + 0.16 * (y - y0) / 120 + 0.06 * hC;
      flowPuffs.add(x, y, z, s, shade * 1.02, shade * 0.95, shade * 0.88, 0.97, dep < 30 ? 0.04 : 0); } }
  if (parkOn && b === 8) { const gt = lt + 1.2;                     // the geyser: a white column of steam and spray
    for (let i = 0; i < 500; i++) { const hA = hash1(i * 3.3), hB = hash1(i * 5.1), hC = hash1(i * 7.7), bt = hA * 4.0, a = ((gt - bt) % 4 + 4) % 4;
      const y = 1.6 + (40 * (1 - Math.exp(-a / 0.9))) * (0.5 + 0.5 * hB), r = 0.6 + 2.0 * a * hC + 3 * smooth(25, 40, y) * a;
      const th = hC * 6.283 + a; const wind = 2.5 * a;
      geyPuffs.add(GEY.x + Math.cos(th) * r + wind, GEY.y + y, GEY.z + Math.sin(th) * r, (2.2 + 3.5 * a) * (0.6 + 0.6 * hB), 0.95, 0.97, 1.0, 0.55 * (1 - smooth(2.5, 4, a))); } }
  setCloud(spray, i => { if (!(parkOn && b === 8)) return null; const a = ((lt * 1.3 + hash1(i * 3)) % 1.6), v = 18 + 10 * hash1(i * 5), th = hash1(i * 7) * 6.283, vh = 1.5 + 3 * hash1(i * 9);
    const y = 1.6 + v * a - 9.8 * a * a * 0.5; if (y < 1.2) return null; return V(GEY.x + Math.cos(th) * vh * a + 1.2 * a, GEY.y + y, GEY.z + Math.sin(th) * vh * a); });
  colPuffs.end(); flowPuffs.end(); geyPuffs.end();
  // ---- the map: the umbrella cloud grows from Yellowstone, faster downwind (east) but over 900 miles upwind too
  mapPuffs.begin();
  if (where === 'mapG') { const grow = smooth(0.0, 0.92, u), Rw = 0.6 + 12.5 * grow, Re = 0.8 + 24 * smooth(0.0, 1.0, u);
    for (let i = 0; i < 700; i++) { const hA = hash1(i * 2.9), hB = hash1(i * 6.1), hC = hash1(i * 4.3), th = hA * 6.283, ex = (Math.cos(th) + 1) / 2;
      const R = lerp(Rw, Re, ex ** 1.5) * (1 - 0.35 * Math.abs(Math.sin(th)) * (1 - ex)), r = R * Math.sqrt(hB);
      const p = MAP.clone().add(V(YS.x + Math.cos(th) * r, 1.1 + 0.8 * hC + 0.7 * (1 - r / Math.max(R, 0.1)), YS.z + Math.sin(th) * r * 0.85));
      const s = (2.2 + 2.4 * hC) * (0.6 + 0.4 * grow) * (1 - 0.35 * r / Math.max(R, 0.1));
      const sh = 0.62 + 0.12 * hC; mapPuffs.add(p.x, p.y, p.z, s, sh, sh * 0.97, sh * 0.93, 0.7 * smooth(0, 0.08, u + hB * 0.05) * (1 - 0.5 * hB)); }
    for (let i = 0; i < 60; i++) { const a = (u * 3 + i / 60) % 1; mapPuffs.add(MAP.x + YS.x + (hash1(i) - 0.5) * 0.6, MAP.y + 0.9 + a * 2.0, MAP.z + YS.z + (hash1(i * 3) - 0.5) * 0.6, 1.0 + a, 0.42, 0.4, 0.38, 0.9, 0.4 * (1 - a)); }
    const m4 = new THREE.Matrix4(); for (let i = 0; i < 24; i++) { const row = i % 4, col = Math.floor(i / 4), x = -24 + ((col * 9 + lt * 6 + row * 3) % 54), z = -10 + row * 6.5;
      m4.compose(V(x, 3.6, z), new THREE.Quaternion(), V(1.4, 1, 1.4)); arrows.setMatrixAt(i, m4); } arrows.instanceMatrix.needsUpdate = true;
    arrows.material.opacity = 0.85 * smooth(0.05, 0.2, u);
    const L = 12.1 * smooth(0.45, 0.8, u), y = 4.4; upwind.visible = L > 0.05;
    const bar = upwind.getObjectByName('bar'); bar.scale.x = Math.max(L, 0.01); bar.position.set(YS.x - L / 2, y, YS.z + 1.6);
    upwind.getObjectByName('tick0').position.set(YS.x, y, YS.z + 1.6); upwind.getObjectByName('tick1').position.set(YS.x - L, y, YS.z + 1.6); upwind.getObjectByName('tick1').visible = false;
    const tp = upwind.getObjectByName('tip'); tp.position.set(YS.x - L - 0.1, y, YS.z + 1.6); tp.rotation.z = Math.PI; }
  mapPuffs.end();
  // ---- the town: ash depth, ash on roofs and cars, falling ash, rain, the roof collapse, dust
  const depth = ashDepth(t), wet = b === 4 ? smooth(0.05, 0.4, u) : b === 5 ? 1 : 0;
  ashGround.position.y = depth; ashU.uWet.value = wet;
  for (const hs of HOUSES) for (const sl of hs.slabs) for (const pc of sl.pieces) { const th = Math.max(0.01, depth * 0.55); pc.ash.scale.y = th / 0.01; pc.ash.position.y = 0.07 + th / 2; pc.ash.material.color.setScalar(1).multiplyScalar(1); }
  for (const c of TCARS) { const th = Math.max(0.01, depth * 0.5); c.userData.cap.scale.y = th / 0.01; c.userData.cap.position.y = 1.46 + th / 2; }
  { const cu = b === 4 ? u : b === 5 ? 1 : 0, sag = smooth(0.52, 0.66, cu), fall = smooth(0.66, 0.8, cu) ** 1.6;
    for (const sl of COLLAPSE.slabs) { sl.hinge.rotation.x = sl.s * (COLLAPSE.a0 - 0.12 * sag - 1.35 * fall);
      sl.pieces.forEach((pc, k) => { pc.piece.rotation.x = sl.s * (0.25 * fall * (k - 1) * 0.6); pc.piece.position.y = -0.3 * fall * (k === 1 ? 1 : 0.4); }); } }
  dustPuffs.begin();
  if (where === 'town' && (b === 4 || b === 5)) { const cu = b === 4 ? u : 1.3 + lt / d, a = (cu - 0.76) * d; if (a > 0) {
    for (let i = 0; i < 260; i++) { const hA = hash1(i * 3.7), hB = hash1(i * 5.3), hC = hash1(i * 7.1), th = hA * 6.283, r = 1 + (3 + 6 * hB) * (1 - Math.exp(-a * 1.5));
      const p = TOWN.clone().add(V(COLLAPSE.x + Math.cos(th) * r * 1.1, 2.4 + 2.5 * hC * (1 - Math.exp(-a)) + 0.6 * a, COLLAPSE.z + Math.sin(th) * r * 0.8));
      dustPuffs.add(p.x, p.y, p.z, (1.0 + 1.8 * hB) * (1 + 0.6 * a), 0.72, 0.7, 0.66, 0.45 * Math.exp(-a * 0.6) * smooth(0, 0.15, a)); } } }
  dustPuffs.end();
  setCloud(flakes, i => { if (where !== 'town') return null; const c = camera.position.clone().sub(TOWN), h = hash1(i * 3), fall = 0.9 + 0.5 * hash1(i * 7);
    const x = c.x - 9 + 18 * hash1(i * 11) + 0.4 * Math.sin(t * 0.8 + i), z = c.z - 12 + 16 * hash1(i * 13), y = depth + ((6 - (t * fall + h * 6)) % 6 + 6) % 6;
    return TOWN.clone().add(V(x, y, z)); });
  flakes.m.material.size = b === 5 ? 0.03 : 0.05;
  rainS.visible = where === 'town' && b >= 4; if (rainS.visible) { const m4 = new THREE.Matrix4(), c = camera.position, rq = new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().lookAt(c, c.clone().add(V(0, 0, -1)), V(0, 1, 0)));
    const k = Math.round(450 * (b === 4 ? smooth(0.0, 0.25, u) : 0.6)); rainS.count = k;
    for (let i = 0; i < k; i++) { const y = ((8 - (t * 9 + hash1(i * 3) * 8)) % 8 + 8) % 8; m4.compose(V(c.x - 8 + 16 * hash1(i * 5), TOWN.y + depth + y, c.z - 14 + 18 * hash1(i * 7)), new THREE.Quaternion(), V(1, 1, 1)); rainS.setMatrixAt(i, m4); }
    rainS.instanceMatrix.needsUpdate = true; }
  breath.begin();
  if (g.show && (b === 7 || b === 5)) { const m = mouthW(), f = fwdOf(180);
    for (let i = 0; i < 14; i++) { const per = b === 7 ? 1.7 : 1.0, a = ((lt + i * 0.025) % per), k = a / per, puff = b === 7 ? (g.blow > 0.3 ? 1 : smooth(0.0, 0.1, k) * (1 - smooth(0.5, 0.7, k))) : 0;
      if (b === 5) continue; const p = m.clone().addScaledVector(f, 0.05 + 0.35 * k).add(V(0.03 * Math.sin(i), 0.06 * k, 0));
      breath.add(p.x, p.y, p.z, 0.04 + 0.13 * k, 0.9, 0.92, 0.95, 0.09 * puff * (1 - k)); } }
  breath.end();
  // ---- the shards (beat 5, after the cut): tumbling slowly
  if (where === 'shardG') { const v = (u - SHARD_CUT) / (1 - SHARD_CUT); for (const s of SHARDS) { s.m.rotation.set(s.w.x * (t * 1.5), s.w.y * (t * 1.5), s.w.z * t); s.m.position.copy(s.p0).add(V(0, 0.15 * Math.sin(t + s.p0.x), 0.3 * v)); } }
  // ---- the jet: flying through the ash cloud; ash pours into the engine, melts in the burner, sticks to the turbine; the fan runs down
  skyPuffs.begin(); exhaust.begin();
  if (where === 'jetG') { const spd = 60;
    for (let i = 0; i < 900; i++) { const hA = hash1(i * 2.7), hB = hash1(i * 3.9), hC = hash1(i * 5.3);
      const z = ((hA * 400 + t * spd) % 400) - 260, x = -60 + 120 * hB, y = -20 + 40 * hC; if (Math.abs(x - ENG.x) < 8 && Math.abs(y - ENG.y) < 5 && Math.abs(z - ENG.z) < 12) continue;
      const sh = 0.42 + 0.12 * hC; skyPuffs.add(JETS.x + x, JETS.y + y, JETS.z + z, 6 + 10 * hB, sh * 1.05, sh * 0.95, sh * 0.85, 0.55); }
    const melt = smooth(0.15, 0.55, u), die = smooth(0.72, 0.95, u);
    ENGINE.burner.material.emissiveIntensity = 2.5 * melt * (1 - die) + 0.6 * die; ENGINE.turb.emissiveIntensity = 1.6 * melt * (1 - 0.5 * die); ENGINE.glow.intensity = 5 * melt * (1 - 0.7 * die);
    const spin = (1 - 0.8 * die); ENGINE.rotors.forEach((r, k) => { r.rotation.z = t * (k === 0 ? 18 : 30) * spin + (k === 0 ? 0 : -t * 4 * die); });
    const nb = Math.floor(160 * smooth(0.25, 0.8, u)), m4 = new THREE.Matrix4(); blobs.count = nb;
    for (let i = 0; i < nb; i++) { const th = hash1(i * 3) * 6.283, r = 0.16 + 0.3 * hash1(i * 5), z = 0.72 + 0.48 * hash1(i * 7); m4.compose(V(Math.cos(th) * r, Math.sin(th) * r, z), new THREE.Quaternion(), V(1, 1, 1).multiplyScalar(0.7 + 0.8 * hash1(i * 9))); blobs.setMatrixAt(i, m4); }
    blobs.instanceMatrix.needsUpdate = true;
    for (let i = 0; i < 220; i++) { const a = ((t * 1.6 + hash1(i * 3)) % 1), z = 2.3 + a * 26, hb = hash1(i * 7), sm2 = die;
      const p = JETS.clone().add(ENG).add(V((hash1(i * 5) - 0.5) * (0.4 + a * 3), (hb - 0.5) * (0.4 + a * 3) + a * 0.6, z));
      exhaust.add(p.x, p.y, p.z, 0.5 + 3.5 * a, 0.22 + 0.1 * hb, 0.2 + 0.08 * hb, 0.19, (0.25 + 0.5 * sm2) * (1 - a), (1 - sm2) * melt * (1 - a) * 0.8); } }
  skyPuffs.end(); exhaust.end();
  setCloud(ashIn, i => { if (where !== 'jetG') return null; const a = ((t * 2.2 + hash1(i * 3)) % 1), th = hash1(i * 5) * 6.283, r = 0.6 * (1 - a * 0.6) * hash1(i * 7);
    return JETS.clone().add(ENG).add(V(Math.cos(th) * r, Math.sin(th) * r, -6 + 6.5 * a)); });
  ashIn.m.material.color.setHex(0x9a948c);
  // ---- the farm: frost on the corn, snow on the ground, falling snow
  const fk = b === 7 ? smooth(0.0, 0.85, u) : 0; frostU.uFrost.value = 0.05 + 0.7 * fk; snowGround.material.opacity = 0.35 + 0.55 * fk;
  setCloud(fsnow, i => { if (where !== 'farm') return null; const c = camera.position.clone().sub(FARM), h = hash1(i * 3);
    const x = c.x - 8 + 16 * hash1(i * 11) + 0.5 * Math.sin(t * 0.7 + i), z = c.z - 14 + 16 * hash1(i * 13), y = ((5 - (t * 0.8 + h * 5)) % 5 + 5) % 5;
    return FARM.clone().add(V(x, y, z)); });
  // ---- camera, sky, fog, sun per stage
  sky.position.copy(camera.position); skyU.uT.value = t;
  const LOOK = {                                                  // murk, fog color, fog density, sun color, sun power, hemi power, exposure, env
    park: [0, 0xb9cde0, b === 1 ? 0.0011 : 0.00042, 0xfff0dc, 3.4, 0.75, 1.0, 0.45],
    mapG: [0, 0xb9cde0, 0.0, 0xfff4e6, 3.0, 0.9, 1.0, 0.45],
    town: [1, 0x5e5852, b === 3 ? 0.03 : 0.04, 0xb0a08c, b === 4 ? 0.5 : 1.0, 0.55, 0.95, 0.22],
    shardG: [1, 0x14161a, 0.0, 0xffffff, 0, 0.3, 1.0, 0.6],
    jetG: [1, 0x6a5e52, 0.012, 0xc8b49a, 1.6, 0.8, 1.1, 0.3],
    farm: [1, 0x8a8d92, 0.018, 0xc4ccd8, 0.9, 1.0, 1.15, 0.35] }[where];
  skyU.uMurk.value = LOOK[0]; skyU.uMurkCol.value.set(where === 'jetG' ? 0x6e6052 : where === 'farm' ? 0x8c9096 : 0x6e6762);
  scene.fog.color.set(LOOK[1]); scene.fog.density = LOOK[2]; FOGC.value.copy(scene.fog.color); FOGD.value = LOOK[2];
  sun.color.set(LOOK[3]); sun.intensity = LOOK[4]; hemi.intensity = LOOK[5]; renderer.toneMappingExposure = LOOK[6]; scene.environmentIntensity = LOOK[7];
  sky.visible = where !== 'shardG';
  const focus = where === 'mapG' ? MAP.clone() : where === 'jetG' ? JETS.clone().add(ENG) : C.tgt.clone();
  if (where === 'park' && b !== 1) focus.copy(G.root.visible ? wp(G.bones.hips) : C.tgt);
  if (b === 1) focus.copy(wp(G.bones.hips));
  sun.target.position.copy(focus); sun.position.copy(focus).addScaledVector(SUNDIR, 100); sun.target.updateMatrixWorld();
  { const S = sun.shadow.camera, e = where === 'mapG' ? 30 : where === 'jetG' ? 22 : where === 'town' && b === 4 ? 20 : 9; if (S.right !== e) { S.left = -e; S.right = e; S.top = e; S.bottom = -e; S.updateProjectionMatrix(); } }
  return { beat: b, groundY: g.show ? g.ground : null, cut: b === 5 && Math.abs(u - SHARD_CUT) < 1 / (d * FPS) * 1.01 && u >= SHARD_CUT };
}

// ------------------------------------------------------------------ frame I/O (same contract as the other 3D Shorts)
let composer = null;
if (Q.get('ao') === '1') {                                   // off by default: the look was set on the direct render (sky and ash shaders write display colors)
  composer = new EffectComposer(renderer, new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: 4 }));
  composer.setPixelRatio(1); composer.setSize(W, H);
  composer.addPass(new RenderPass(scene, camera));
  const ao = new GTAOPass(scene, camera, W, H);
  ao.updateGtaoMaterial({ radius: 0.25, distanceExponent: 1, thickness: 1, scale: 1, samples: 12, distanceFallOff: 1, screenSpaceRadius: false });
  ao.updatePdMaterial({ lumaPhi: 10, depthPhi: 2, normalPhi: 3, radius: 6, rings: 2, samples: 12 });
  ao.blendIntensity = 0.7;
  composer.addPass(ao); composer.addPass(new OutputPass());
}
const draw = () => { if (composer) composer.render(); else renderer.render(scene, camera); };
const gl = renderer.getContext(), px = new Uint8Array(W * H * 4);
let GROUND = null, CUTF = false;
function stepTo(i) { const t = i / FPS, b = beatAt(((t % TOTAL) + TOTAL) % TOTAL);
  if (i !== LASTF + 1) for (let j = Math.max(Math.round(B[b] * FPS), i - 12); j < i; j++) update(j / FPS, j);
  const r = update(t, i); GROUND = r.groundY; CUTF = r.cut; LASTB = r.beat; LASTF = i; }
let LASTB = 0;
{ const f0 = Math.round(B[9] * FPS), f1 = Math.round(TOTAL * FPS); for (let i = f0; i < f1; i++) update(i / FPS, i); LOOPARM = MEM['selfie9'].a.slice(); LASTF = -10; }
window.renderAll = async (f0, f1) => { for (let i = f0; i < f1; i++) { stepTo(i); draw(); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); await fetch('/frame', { method: 'POST', body: px }); } return 'ok'; };
window.renderAtT = t => { const i = Math.round(t * FPS); stepTo(i); if (window.CAM && window.CAM.hand) { const hp = PALM(window.CAM.hand).applyMatrix4(G.bones['hand' + window.CAM.hand].matrixWorld); window.CAM.tgt = hp.toArray(); window.CAM.pos = hp.clone().add(V(...window.CAM.off)).toArray(); }
  if (window.CAM) { camera.position.set(...window.CAM.pos); camera.up.set(0, 1, 0); camera.lookAt(...window.CAM.tgt); camera.fov = window.CAM.fov || 42; camera.updateProjectionMatrix(); sky.position.copy(camera.position); for (const ps of ALLPUFFS) ps.end(); } draw(); return renderer.domElement.toDataURL('image/png'); };
window.rigReport = i => { stepTo(i); const t = i / FPS, iq = G.root.getWorldQuaternion(new THREE.Quaternion()).invert();
  return { t, beat: LASTB, ang: LAST, hips: wp(G.bones.hips).toArray(), car: 0, show: G.root.visible, cut: CUTF,
    thumbs: ['R', 'L'].map(S => wp(G.bones['index1' + S]).sub(wp(G.bones['pinky1' + S])).applyQuaternion(iq).toArray()),
    forearms: ['R', 'L'].map(S => wp(G.bones['hand' + S]).sub(wp(G.bones['farm' + S])).normalize().applyQuaternion(iq).toArray()),
    cost: [LAST.costR ?? null, LAST.costL ?? null], clip: clipScan(GROUND) }; };
window.dbg = { G, wp, mouthW, THREE, hand: (i, name) => { stepTo(i); const g = guyAt(i / FPS), h = handTarget(name, g, i / FPS), f = handFK(h.S, LAST['arm' + h.S]); const R_ = rightOf(GYAW), F_ = fwdOf(GYAW); return { nr: f.n.dot(R_), nf: f.n.dot(F_), ny: f.n.y, ur: f.u.dot(R_), uf: f.u.dot(F_), uy: f.u.y, d: f.p.distanceTo(h.p), n: f.n.dot(h.n), u: h.u ? f.u.dot(h.u) : null, a: LAST['arm' + h.S].map(Math.round), c: LAST['cost' + h.S] }; } };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS);
window.READY = true;
