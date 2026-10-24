// "How to survive an avalanche" - a 3D Short with the sculpted, skinned guy (and a friend).
//   av.html?w=1080&h=1920            (times from av/times.json; one shot per narration line)
// Beats: 0 he cracks the slope (hook) | 1 wide: the slab breaks and runs | 2 rides hard for the side | 3 caught: swims
//        4 cutaway: punches a hand up | 5 cutaway: arm over face, air pocket | 6 it stops: sets like concrete
//        7 spit? a myth, he can't move | 8 a friend digs him out | 9 back on the slope (loops into beat 0)
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { GTAOPass } from 'three/addons/postprocessing/GTAOPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { loadGuy } from '/guy3d.js';

const Q = new URLSearchParams(location.search);
const W = +Q.get('w') || 1080, H = +Q.get('h') || 1920;
const FPS = 30;
const TIMES = await (await fetch('/av/times.json')).json();
const B = TIMES.starts, DUR = TIMES.durs, TOTAL = TIMES.total;
const clamp = (x, a, b) => Math.min(Math.max(x, a), b);
const sm = t => t * t * (3 - 2 * t);
const smooth = (a, b, x) => sm(clamp((x - a) / (b - a), 0, 1));
const lerp = (a, b, u) => a + (b - a) * u;
const D2R = Math.PI / 180;
function hash1(n) { const s = Math.sin(n * 127.1) * 43758.5453; return s - Math.floor(s); }
function vn1(x, seed) { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return lerp(hash1(i + seed * 17.3), hash1(i + 1 + seed * 17.3), u) * 2 - 1; }
const V = (x, y, z) => new THREE.Vector3(x, y, z);

// ------------------------------------------------------------------ terrain: one long 32-degree slope into a flat runout
const SLOPE = 32 * D2R, TANA = Math.tan(SLOPE), COSA = Math.cos(SLOPE), SINA = Math.sin(SLOPE);
const sp = (z, r = 3) => Math.max(z, 0) + r * Math.log1p(Math.exp(-Math.abs(z) / r));
const SLAB = { x0: -14, x1: 14, z1: 108, T: 0.6, rows: 16, bs: 2.0 };   // the slab that breaks (crack along z1)
SLAB.z0 = SLAB.z1 - SLAB.rows * SLAB.bs * COSA;
const XB = 12, ZB = -8;                                               // where he ends up buried
function terrain(x, z) {
  let h = TANA * sp(z) - 0.8 * TANA * sp(z - 175, 6);
  h += Math.min(30, 0.012 * Math.max(0, Math.abs(x) - 16) ** 2);     // the slope is a wide chute between ridges
  const quiet = 1 - smooth(-4, 6, z) * (1 - smooth(130, 150, z)) * (1 - smooth(16, 22, Math.abs(x)));   // flat & clean in the chute
  h += quiet * (0.35 * Math.sin(x * 0.21 + 0.4) * Math.cos(z * 0.13) + 0.18 * Math.sin(x * 0.47 + z * 0.31));
  return h;
}
const GLSL_TERRAIN = `
float sp3(float z, float r){ return max(z, 0.0) + r * log(1.0 + exp(-abs(z) / r)); }
float sm01(float a, float b, float x){ float t = clamp((x - a) / (b - a), 0.0, 1.0); return t * t * (3.0 - 2.0 * t); }
float terrainH(float x, float z){
  float h = ${TANA.toFixed(6)} * sp3(z, 3.0) - 0.8 * ${TANA.toFixed(6)} * sp3(z - 175.0, 6.0);
  h += min(30.0, 0.012 * pow(max(0.0, abs(x) - 16.0), 2.0));
  float quiet = 1.0 - sm01(-4.0, 6.0, z) * (1.0 - sm01(130.0, 150.0, z)) * (1.0 - sm01(16.0, 22.0, abs(x)));
  h += quiet * (0.35 * sin(x * 0.21 + 0.4) * cos(z * 0.13) + 0.18 * sin(x * 0.47 + z * 0.31));
  return h;
}`;
// the debris pile where he ends up (runout), with lumpy chunks
const PILE = 1.95;
function pileH(x, z) { return PILE * Math.exp(-(((x - XB) ** 2) / 70 + ((z - ZB) ** 2) / 55)); }
function lumps(x, z) { return 0.13 * Math.sin(1.7 * x + 0.3 * z) * Math.sin(1.3 * z - 0.6 * x) + 0.08 * Math.sin(3.1 * x + 2.3 * z) + 0.05 * Math.sin(4.7 * x - 3.9 * z + 1.0); }
function debrisH(x, z) { const p = pileH(x, z); return terrain(x, z) + p - 0.08 + lumps(x, z) * Math.min(1, p * 1.5); }
const GLSL_DEBRIS = `
float pileH(float x, float z){ return ${PILE.toFixed(3)} * exp(-(pow(x - ${XB.toFixed(1)}, 2.0) / 70.0 + pow(z - (${ZB.toFixed(1)}), 2.0) / 55.0)); }
float lumpsH(float x, float z){ return 0.13 * sin(1.7 * x + 0.3 * z) * sin(1.3 * z - 0.6 * x) + 0.08 * sin(3.1 * x + 2.3 * z) + 0.05 * sin(4.7 * x - 3.9 * z + 1.0); }
float debrisH(float x, float z){ float p = pileH(x, z); return terrainH(x, z) + p - 0.08 + lumpsH(x, z) * min(1.0, p * 1.5); }`;

// ------------------------------------------------------------------ renderer / scene / sky
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(W, H);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 0.82;
renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.localClippingEnabled = true;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene();
const FOGC = new THREE.Color(0xc9daf0);
scene.fog = new THREE.Fog(FOGC.clone(), 80, 700);
const camera = new THREE.PerspectiveCamera(42, W / H, 0.03, 2000);

const SUNDIR = V(-0.45, 0.62, -0.64).normalize();      // bright mid-morning sun, in front-left of him
const skyMat = new THREE.ShaderMaterial({
  side: THREE.BackSide, depthWrite: false, fog: false,
  uniforms: { uSun: { value: SUNDIR }, uLin: { value: Q.get('ao') !== '0' ? 1 : 0 } },
  vertexShader: 'varying vec3 vD; void main(){ vD = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
  fragmentShader: `varying vec3 vD; uniform vec3 uSun; uniform float uLin;
    void main(){ float h = clamp(vD.y, -0.2, 1.0);
      vec3 top = vec3(0.12, 0.33, 0.72), mid = vec3(0.45, 0.65, 0.9), hor = vec3(0.82, 0.88, 0.95);
      vec3 c = mix(hor, mid, smoothstep(0.0, 0.15, h)); c = mix(c, top, smoothstep(0.12, 0.7, h));
      float s = max(dot(normalize(vD), uSun), 0.0);
      c += vec3(1.0, 0.95, 0.85) * (pow(s, 12.0) * 0.25 + pow(s, 1200.0) * 8.0);
      gl_FragColor = vec4(uLin > 0.5 ? pow(c, vec3(2.2)) * 0.95 : c, 1.0); }`,
});
const sky = new THREE.Mesh(new THREE.SphereGeometry(1500, 48, 24), skyMat); scene.add(sky);
{ const pm = new THREE.PMREMGenerator(renderer); const es = new THREE.Scene();
  es.add(new THREE.Mesh(new THREE.SphereGeometry(10, 32, 16), skyMat));
  scene.environment = pm.fromScene(es, 0.02).texture; scene.environmentIntensity = 0.35; }
const hemi = new THREE.HemisphereLight(0xa9c6ff, 0xe8eef8, 0.85); scene.add(hemi);
const sun = new THREE.DirectionalLight(0xfff3e2, 3.2);
sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
const SC = sun.shadow.camera; SC.near = 0.5; SC.far = 120;
sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.03;
scene.add(sun); scene.add(sun.target);
function shadowBox(r) { if (SC.right !== r) { SC.left = -r; SC.right = r; SC.top = r; SC.bottom = -r; SC.updateProjectionMatrix(); } }

// ------------------------------------------------------------------ snow material (ground, debris, slab blocks)
// world-space sparkle, soft drift noise, bluish shadows from the sky light; the bed under the slab is icier and grey
const CRACK = { p: { value: 0 }, x: { value: 0 } };
const SNOW_GLSL = `
float sh(vec3 p){ return fract(sin(dot(p, vec3(12.9898, 78.233, 37.719))) * 43758.5453); }
float sn(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f*f*(3.0-2.0*f);
  float a = fract(sin(dot(i, vec2(127.1, 311.7))) * 43758.5); float b = fract(sin(dot(i + vec2(1,0), vec2(127.1, 311.7))) * 43758.5);
  float c = fract(sin(dot(i + vec2(0,1), vec2(127.1, 311.7))) * 43758.5); float d = fract(sin(dot(i + vec2(1,1), vec2(127.1, 311.7))) * 43758.5);
  return mix(mix(a, b, u.x), mix(c, d, u.x), u.y); }`;
function snowMat(kind) {             // kind: 'ground' | 'debris' | 'block'
  const m = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.82, metalness: 0 });
  m.userData.u = { uBed: { value: 0 }, uCrack: CRACK.p, uCrackX: CRACK.x };
  m.onBeforeCompile = sh => {
    Object.assign(sh.uniforms, m.userData.u);
    sh.vertexShader = sh.vertexShader.replace('#include <common>', `#include <common>
varying vec3 vT; varying vec3 vW;${kind === 'block' ? '\nattribute vec3 iRest;' : ''}`)
      .replace('#include <worldpos_vertex>', `#include <worldpos_vertex>
{ vec4 wp = vec4(transformed, 1.0);
#ifdef USE_INSTANCING
  wp = instanceMatrix * wp;
#endif
  vW = (modelMatrix * wp).xyz;
  ${kind === 'block' ? `vT = iRest + vec3(position.x, position.y * ${COSA.toFixed(5)} + position.z * ${SINA.toFixed(5)}, -position.y * ${SINA.toFixed(5)} + position.z * ${COSA.toFixed(5)});` : 'vT = vW;'} }`);
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', `#include <common>
varying vec3 vT; varying vec3 vW; uniform float uBed, uCrack, uCrackX;` + SNOW_GLSL)
      .replace('#include <color_fragment>', `#include <color_fragment>
  { vec2 P = vT.xz;
    float n = sn(P * 0.35) * 0.5 + sn(P * 1.7) * 0.3 + sn(P * 7.0) * 0.2;
    vec3 c = mix(vec3(0.86, 0.9, 0.97), vec3(1.0), n);
    ${kind === 'ground' ? `// the bed surface left behind by the slab: older, icier, a little grey
    float inSlab = step(${SLAB.x0.toFixed(1)}, vW.x) * step(vW.x, ${SLAB.x1.toFixed(1)}) * step(${SLAB.z0.toFixed(1)}, vW.z) * step(vW.z, ${SLAB.z1.toFixed(1)});
    float bed = inSlab * smoothstep(0.15, 0.4, ${TANA.toFixed(5)} * vW.z - vW.y) * uBed;
    c = mix(c, vec3(0.7, 0.76, 0.85) * (0.9 + 0.2 * sn(P * 3.0)), bed * 0.8);` : ''}
    ${kind === 'block' ? 'c *= 0.97 + 0.03 * sh(floor(vT * 3.0));' : ''}
    // the crack: a dark line racing across the slope from where he is
    float cz = abs(vW.z - ${SLAB.z1.toFixed(2)} + 0.04 * sin(vW.x * 9.0));
    float below = vW.z - ${SLAB.z1.toFixed(2)};
    float line = 1.0 - smoothstep(0.08, 0.15, cz);
    float shade = (1.0 - smoothstep(0.0, 0.7, -below)) * step(below, 0.0) * 0.4;      // the crown's shadow, downhill of the line
    float cl = max(line, shade) * step(abs(vW.x - uCrackX), uCrack * 40.0) * step(${SLAB.x0.toFixed(1)}, vW.x) * step(vW.x, ${SLAB.x1.toFixed(1)}) * step(0.001, uCrack);
    c = mix(c, vec3(0.2, 0.27, 0.4), cl * 0.9);
    diffuseColor.rgb = c; }`)
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
  { vec3 q = floor(vT * 55.0); float g = step(0.9965, sh(q));
    vec3 vd = normalize(cameraPosition - vW); float tw = step(0.6, sh(q + floor(dot(vd, vec3(31.0, 17.0, 23.0)))));
    totalEmissiveRadiance += vec3(1.6, 1.7, 1.9) * g * tw; }`);
  };
  m.customProgramCacheKey = () => 'snow-' + kind;
  return m;
}

// ------------------------------------------------------------------ ground mesh: dense in the action, sparse far away
const groundMat = snowMat('ground');
function axisSamples(spec) { const out = []; for (const [a, b, n] of spec) for (let i = 0; i < n; i++) out.push(a + (b - a) * i / n); out.push(spec[spec.length - 1][1]); return out; }
const GX = axisSamples([[-700, -60, 40], [-60, -24, 18], [-24, 24, 96], [24, 60, 18], [60, 700, 40]]);
const GZ = axisSamples([[-500, -60, 30], [-60, -20, 40], [-20, 130, 300], [130, 200, 30], [200, 900, 40]]);
function buildGrid(xs, zs, hf) {
  const nx = xs.length, nz = zs.length, pos = new Float32Array(nx * nz * 3), idx = [];
  for (let j = 0; j < nz; j++) for (let i = 0; i < nx; i++) { const k = (j * nx + i) * 3; pos[k] = xs[i]; pos[k + 1] = hf(xs[i], zs[j]); pos[k + 2] = zs[j]; }
  for (let j = 0; j < nz - 1; j++) for (let i = 0; i < nx - 1; i++) { const a = j * nx + i, b = a + 1, c = a + nx, d = c + 1; idx.push(a, c, b, b, c, d); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setIndex(idx); g.computeVertexNormals(); return g;
}
const inSlabBed = (x, z) => x > SLAB.x0 + 0.5 && x < SLAB.x1 - 0.5 && z > SLAB.z0 + 0.5 && z < SLAB.z1 - 0.5;
const ground = new THREE.Mesh(buildGrid(GX, GZ, (x, z) => terrain(x, z) - (inSlabBed(x, z) ? SLAB.T : 0)), groundMat);
ground.receiveShadow = true; scene.add(ground);

// far peaks: displaced cones, rock where steep, snow above
function peak(x, z, h, r, seed) {
  const g = new THREE.ConeGeometry(r, h, 96, 48, true); const p = g.attributes.position; const col = new Float32Array(p.count * 3);
  for (let i = 0; i < p.count; i++) {
    const v = V(p.getX(i), p.getY(i), p.getZ(i)); const a = Math.atan2(v.z, v.x), y01 = (v.y + h / 2) / h;
    const n = vn1(a * 4 + seed, 1) * 0.12 + vn1(a * 13 + seed * 2, 2) * 0.05 + vn1(y01 * 9 + a * 3 + seed, 3) * 0.06;
    const rr = Math.hypot(v.x, v.z) * (1 + n * (0.4 + 0.6 * y01)); v.x = Math.cos(a) * rr; v.z = Math.sin(a) * rr; v.y += vn1(a * 6 + seed, 4) * h * 0.04 * y01;
    p.setXYZ(i, v.x, v.y, v.z);
    const rock = clamp(0.5 + vn1(a * 9 + y01 * 7 + seed, 5) * 0.9 - y01 * 0.6, 0, 1) > 0.55 ? 1 : 0;
    const c = rock ? [0.25, 0.26, 0.3] : [0.93, 0.95, 1.0]; col.set(c, i * 3);
  }
  g.setAttribute('color', new THREE.BufferAttribute(col, 3)); g.computeVertexNormals();
  const m = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.9, flatShading: false }));
  m.position.set(x, h / 2 - 20, z); scene.add(m); return m;
}
peak(-260, 520, 330, 260, 1); peak(40, 640, 420, 300, 2); peak(330, 560, 300, 240, 3); peak(-520, 300, 260, 230, 4); peak(560, 260, 240, 220, 5); peak(-140, -520, 260, 260, 6); peak(260, -560, 300, 280, 7);

// pines along the ridges and around the runout (instanced: trunk + three snowy cones)
{ const pts = [];
  for (let i = 0; i < 2600 && pts.length < 520; i++) {
    const x = (hash1(i * 3.17) - 0.5) * 220, z = -70 + hash1(i * 7.31) * 230;
    if (Math.abs(x) < 19 && z > -2) continue;                        // not in the chute
    if (Math.hypot(x - XB, z - ZB) < 14) continue;                    // not on the debris
    if (z < -2 && Math.abs(x - 6) < 12 && z > -40) continue;          // keep the runout open
    pts.push([x, z, 0.75 + hash1(i * 1.9) * 0.7]); }
  const green = new THREE.MeshStandardMaterial({ color: 0x1f3a2c, roughness: 0.9 }), snowy = new THREE.MeshStandardMaterial({ color: 0xe8eef8, roughness: 0.85 });
  const trunk = new THREE.MeshStandardMaterial({ color: 0x3b2a1e, roughness: 0.9 });
  const parts = [[new THREE.CylinderGeometry(0.12, 0.16, 2.2, 6), trunk, 1.1, 1],
    [new THREE.ConeGeometry(1.7, 3.2, 8), green, 2.6, 1], [new THREE.ConeGeometry(1.25, 2.6, 8), green, 4.3, 1], [new THREE.ConeGeometry(0.8, 2.0, 8), green, 5.9, 1],
    [new THREE.ConeGeometry(1.45, 1.0, 8), snowy, 3.75, 1], [new THREE.ConeGeometry(1.0, 0.8, 8), snowy, 5.2, 1], [new THREE.ConeGeometry(0.55, 0.7, 8), snowy, 6.6, 1]];
  const m4 = new THREE.Matrix4();
  for (const [g, mt, y] of parts) { const im = new THREE.InstancedMesh(g, mt, pts.length);
    pts.forEach(([x, z, s], i) => { m4.compose(V(x, terrain(x, z) + y * s - 0.2, z), new THREE.Quaternion().setFromEuler(new THREE.Euler(0, hash1(i) * 6, 0)), V(s, s, s)); im.setMatrixAt(i, m4); });
    im.castShadow = true; im.receiveShadow = true; im.frustumCulled = false; scene.add(im); } }

// ------------------------------------------------------------------ the slab: blocks that fit the slope exactly, then break up
const BS = SLAB.bs;
const NBX = Math.round((SLAB.x1 - SLAB.x0) / BS), NBS = SLAB.rows;
const BLOCKS = [];
for (let j = 0; j < NBS; j++) for (let i = 0; i < NBX; i++) {
  const s = (j + 0.5) * BS;                                         // slope distance below the crack
  const z = SLAB.z1 - s * COSA, x = SLAB.x0 + (i + 0.5) * BS, k = BLOCKS.length;
  const near = Math.exp(-(((z - 100) / 7) ** 2)) * smooth(-9, -4, x);      // the blocks along his line stay whole longer
  BLOCKS.push({ x, z, s, near, r: hash1(k * 1.31), r2: hash1(k * 2.77), r3: hash1(k * 5.13), ax: V(hash1(k * 9.1) - 0.5, hash1(k * 4.4) - 0.5, hash1(k * 6.6) - 0.5).normalize() });
}
const iRest = new Float32Array(BLOCKS.length * 3);
BLOCKS.forEach((b, i) => { const c = blockRest(b); iRest.set([c.x, c.y, c.z], i * 3); });
function blockRest(b) { return V(b.x, TANA * b.z - SLAB.T / 2 * (1 / COSA), b.z); }
const blockMat = snowMat('block');
const blocks = new THREE.InstancedMesh(new THREE.BoxGeometry(BS, SLAB.T, BS), blockMat, BLOCKS.length);
blocks.geometry.setAttribute('iRest', new THREE.InstancedBufferAttribute(iRest, 3));
blocks.castShadow = true; blocks.receiveShadow = true; blocks.frustumCulled = false; scene.add(blocks);
// slab motion: creeps after the crack, then accelerates downhill (capped), blocks spread and tumble once broken
const T_CRACK = 0.95, T_REL = 1.9;
function slabD(t) { if (t < T_REL) return 0; const dt = t - T_REL, a = 1.25, vmax = 16, tc = vmax / a; return dt < tc ? 0.5 * a * dt * dt : 0.5 * a * tc * tc + vmax * (dt - tc); }
function slabV(t) { return (slabD(t + 0.01) - slabD(t)) / 0.01; }
const qSlope = new THREE.Quaternion().setFromEuler(new THREE.Euler(-SLOPE, 0, 0));
function blockPose(b, t, outP, outQ) {
  const D = slabD(t);
  const w = 1 - b.near * (1 - smooth(92, 104, D));                           // near him: rides as one piece until it hits him
  const spread = D * (0.06 * b.r + 0.002 * b.s * b.r2) * w;               // the upper blocks run a little faster: gaps open
  const d = D * (1 + 0.03 * b.r3 * w) + spread;
  const z = b.z - d * COSA;
  const brk = smooth(1.5 + 4 * b.r, 8 + 6 * b.r, d) * w;                  // broken up after a few metres
  const y = terrain(b.x, z) - SLAB.T / 2 / COSA * (1 - brk) + brk * (0.28 + 0.4 * Math.abs(Math.sin(d * (0.6 + b.r2) + b.r * 6)));
  outP.set(b.x + brk * (b.r2 - 0.5) * 2.5 * (1 - Math.abs(b.x) / 16), y, z);
  const pitch = Math.atan(TANA * (sp(z + 0.5) - sp(z - 0.5)));            // follows the slope onto the flat
  outQ.setFromEuler(new THREE.Euler(-pitch, 0, 0));
  if (brk > 0) outQ.multiply(new THREE.Quaternion().setFromAxisAngle(b.ax, brk * d * (0.15 + 0.25 * b.r2)));
  return brk;
}
// crack line + powder at the crown (drawn as part of the puff system below)

// ------------------------------------------------------------------ powder cloud: soft camera-facing puffs (instanced billboards)
const NP = 900;
const puffGeo = new THREE.InstancedBufferGeometry().copy(new THREE.PlaneGeometry(1, 1));
const pPos = new Float32Array(NP * 3), pSize = new Float32Array(NP), pAlpha = new Float32Array(NP), pSeed = new Float32Array(NP);
for (let i = 0; i < NP; i++) pSeed[i] = hash1(i * 3.91);
puffGeo.setAttribute('iPos', new THREE.InstancedBufferAttribute(pPos, 3)); puffGeo.setAttribute('iSize', new THREE.InstancedBufferAttribute(pSize, 1));
puffGeo.setAttribute('iAlpha', new THREE.InstancedBufferAttribute(pAlpha, 1)); puffGeo.setAttribute('iSeed', new THREE.InstancedBufferAttribute(pSeed, 1));
puffGeo.instanceCount = NP;
const puffMat = new THREE.ShaderMaterial({
  transparent: true, depthWrite: false, fog: true,
  uniforms: THREE.UniformsUtils.merge([THREE.UniformsLib.fog, { uSunV: { value: V(0, 1, 0) } }]),
  vertexShader: `attribute vec3 iPos; attribute float iSize, iAlpha, iSeed; varying vec2 vUv; varying float vA, vS; varying float vFogDepth;
    void main(){ vUv = position.xy; vA = iAlpha; vS = iSeed;
      vec4 mv = modelViewMatrix * vec4(iPos, 1.0);
      float a = iSeed * 6.283; mat2 r = mat2(cos(a), -sin(a), sin(a), cos(a));
      mv.xy += r * position.xy * iSize; vFogDepth = -mv.z;
      gl_Position = projectionMatrix * mv; }`,
  fragmentShader: `varying vec2 vUv; varying float vA, vS; varying float vFogDepth; uniform vec3 fogColor; uniform float fogNear, fogFar;
    float h2(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5); }
    float n2(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f*f*(3.0-2.0*f); return mix(mix(h2(i), h2(i+vec2(1,0)), u.x), mix(h2(i+vec2(0,1)), h2(i+vec2(1,1)), u.x), u.y); }
    void main(){ vec2 p = vUv * 2.0; float r = length(p);
      float n = n2(p * 2.2 + vS * 17.0) * 0.6 + n2(p * 5.0 + vS * 5.0) * 0.4;
      float a = (1.0 - smoothstep(0.35, 1.0, r + (n - 0.5) * 0.55)) * vA;
      if (a < 0.003) discard;
      float lit = clamp(0.55 + 0.45 * vUv.y * 2.0 + (n - 0.5) * 0.3, 0.0, 1.0);
      vec3 c = mix(vec3(0.5, 0.58, 0.74), vec3(1.0, 1.0, 1.0), lit);
      float fogF = smoothstep(fogNear, fogFar, vFogDepth); c = mix(c, fogColor, fogF);
      gl_FragColor = vec4(c, a);
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
    }`,
});
const puffs = new THREE.Mesh(puffGeo, puffMat); puffs.frustumCulled = false; puffs.renderOrder = 5; scene.add(puffs);
let pN = 0;
function puff(p, size, alpha) { if (pN >= NP || alpha < 0.004) return; pPos.set([p.x, p.y, p.z], pN * 3); pSize[pN] = size; pAlpha[pN] = alpha; pN++; }
function puffsDone() { for (let i = pN; i < NP; i++) pAlpha[i] = 0; for (const k of ['iPos', 'iSize', 'iAlpha']) puffGeo.attributes[k].needsUpdate = true; pN = 0; }

// ------------------------------------------------------------------ the debris pile (runout) and the cutaway wall
const debrisMat = snowMat('debris');
const DX = axisSamples([[XB - 16, XB + 16, 128]]), DZ = axisSamples([[ZB - 14, ZB + 12, 104]]);
const debrisGeo = buildGrid(DX, DZ, debrisH);
const debrisY0 = Float32Array.from(debrisGeo.attributes.position.array);
let debrisY0Hole = 0;                                     // set once his buried pose is known
const debris = new THREE.Mesh(debrisGeo, debrisMat); debris.receiveShadow = true; debris.castShadow = true; scene.add(debris);
// snow boulders lying on the pile
const boulders = (() => { const g = new THREE.IcosahedronGeometry(1, 1); const p = g.attributes.position;
  for (let i = 0; i < p.count; i++) { const v = V(p.getX(i), p.getY(i), p.getZ(i)); v.multiplyScalar(1 + 0.18 * (hash1(i * 7.7 + v.x * 3) - 0.5)); p.setXYZ(i, v.x, v.y, v.z); }
  g.computeVertexNormals(); const im = new THREE.InstancedMesh(g, debrisMat, 170); const m4 = new THREE.Matrix4(); let k = 0;
  for (let i = 0; i < 900 && k < 170; i++) { const x = XB + (hash1(i * 2.3) - 0.5) * 22, z = ZB + (hash1(i * 5.9) - 0.5) * 18;
    if (pileH(x, z) < 0.25 || Math.hypot(x - XB, z - ZB) < 1.4) continue; const s = 0.12 + 0.45 * hash1(i * 8.1) ** 2;
    m4.compose(V(x, debrisH(x, z) + s * 0.25, z), new THREE.Quaternion().setFromEuler(new THREE.Euler(hash1(i) * 6, hash1(i * 2) * 6, 0)), V(s * 1.2, s * 0.8, s)); im.setMatrixAt(k++, m4); }
  im.count = k; im.castShadow = true; im.receiveShadow = true; scene.add(im); return im; })();
const CUTZ = 0.2, WALLZ = ZB + CUTZ;
const clipCut = new THREE.Plane(V(0, 0, 1), -WALLZ);
const cutU = { uT: { value: 0 }, uFlow: { value: 0 }, uSet: { value: 0 }, uPocket: { value: new THREE.Vector4(0, 0, 0.1, 0.08) }, uPocketA: { value: 0 }, uBody: { value: new THREE.Vector4(0, 0, 0, 0) } };
const cutMat = new THREE.ShaderMaterial({
  uniforms: cutU, side: THREE.DoubleSide,
  vertexShader: 'varying vec3 vW; void main(){ vW = (modelMatrix * vec4(position, 1.0)).xyz; gl_Position = projectionMatrix * viewMatrix * vec4(vW, 1.0); }',
  fragmentShader: `varying vec3 vW; uniform float uT, uFlow, uSet, uPocketA; uniform vec4 uPocket, uBody;
  ${GLSL_TERRAIN}
  ${GLSL_DEBRIS}
  float hh(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
  vec3 vor(vec2 p){ vec2 i = floor(p), f = fract(p); float d1 = 9.0, d2 = 9.0; float id = 0.0;
    for (int y = -1; y <= 1; y++) for (int x = -1; x <= 1; x++) { vec2 g = vec2(x, y); vec2 o = vec2(hh(i + g), hh(i + g + 7.3));
      float d = length(g + o - f); if (d < d1) { d2 = d1; d1 = d; id = hh(i + g + 3.1); } else if (d < d2) d2 = d; }
    return vec3(d1, d2 - d1, id); }
  void main(){
    float z = ${WALLZ.toFixed(3)}; float top = debrisH(vW.x, z), gr = terrainH(vW.x, z);
    if (vW.y > top) discard;
    float depth = top - vW.y;
    vec3 c;
    if (vW.y < gr - 0.05) {                                   // the old ground underneath: layered, firm
      float l = sin(vW.y * 18.0 + sin(vW.x * 2.0) * 0.5) * 0.5 + 0.5;
      c = mix(vec3(0.6, 0.66, 0.76), vec3(0.5, 0.56, 0.68), l) * (0.92 + 0.12 * hh(floor(vW.xy * 200.0)));
    } else {                                                   // avalanche debris: a jumble of snow chunks
      vec2 q = vec2(vW.x - uFlow, vW.y) * 6.5;
      vec3 v = vor(q); vec3 v2 = vor(q * 2.7 + 5.0);
      float edge = 1.0 - smoothstep(0.02, 0.09, v.y);
      vec3 chunk = mix(vec3(0.78, 0.84, 0.93), vec3(0.92, 0.95, 1.0), v.z) * (0.94 + 0.06 * v2.z);
      vec3 loose = mix(chunk, vec3(0.55, 0.62, 0.75), edge * 0.7);
      // set: packed hard and grey, chunks fused, hairline cracks
      vec3 setc = mix(vec3(0.66, 0.7, 0.76), vec3(0.74, 0.77, 0.82), v.z) * (0.9 + 0.12 * hh(floor(vW.xy * 260.0)));
      setc = mix(setc, vec3(0.48, 0.52, 0.6), (1.0 - smoothstep(0.0, 0.025, v2.y)) * 0.5);
      c = mix(loose, setc, uSet);
      c *= mix(1.0, 0.82, smoothstep(0.0, 1.6, depth));       // darker deeper down
    }
    // a dark rim right under the surface line
    c = mix(c, vec3(0.42, 0.5, 0.65), (1.0 - smoothstep(0.0, 0.025, depth)) * 0.6);
    // the air pocket in front of his face
    vec2 pd = (vW.xy - uPocket.xy) / uPocket.zw; float pr = length(pd);
    float pocket = (1.0 - smoothstep(0.92, 1.0, pr)) * uPocketA;
    float rim = (1.0 - smoothstep(0.0, 0.12, abs(pr - 1.0))) * uPocketA;
    c = mix(c, vec3(0.08, 0.14, 0.26), pocket * 0.85);
    c = mix(c, vec3(0.45, 0.85, 1.0), rim * (0.7 + 0.3 * sin(uT * 6.0)));
    // the body's imprint: shadow cast into the wall right around him
    gl_FragColor = vec4(c, 1.0);
    #include <tonemapping_fragment>
    #include <colorspace_fragment>
  }`,
});
const cutWall = new THREE.Mesh(new THREE.PlaneGeometry(40, 6, 1, 1), cutMat);
cutWall.position.set(XB, 0.5, WALLZ); cutWall.visible = false; scene.add(cutWall);

// ------------------------------------------------------------------ props: snowboard, shovel, probe arrow, spit drop
function canvasTex(w, h, draw) { const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d')); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t; }
const boardTex = canvasTex(1024, 192, g => {
  const gr = g.createLinearGradient(0, 0, 1024, 0); gr.addColorStop(0, '#ff3d2e'); gr.addColorStop(0.5, '#ffb22e'); gr.addColorStop(1, '#ff3d2e');
  g.fillStyle = gr; g.fillRect(0, 0, 1024, 192); g.fillStyle = '#111'; g.font = 'bold 120px Inter, Arial'; g.textAlign = 'center'; g.fillText('SEND IT', 512, 140);
  g.fillStyle = 'rgba(255,255,255,0.25)'; for (let i = 0; i < 9; i++) g.fillRect(60 + i * 110, 0, 18, 192); });
const board = new THREE.Group();
{ const geo = new RoundedBoxGeometry(1.56, 0.022, 0.28, 3, 0.01); const p = geo.attributes.position;
  for (let i = 0; i < p.count; i++) { const x = p.getX(i), ax = Math.abs(x); const w = 1 - 0.12 * smooth(0.25, 0.78, ax) + 0.0 ; p.setZ(i, p.getZ(i) * (ax > 0.62 ? 1 - 0.5 * ((ax - 0.62) / 0.16) ** 2 : 1) * (w > 0 ? 1 : 1));
    p.setY(i, p.getY(i) + 2.6 * Math.max(0, ax - 0.6) ** 2); }
  geo.computeVertexNormals();
  // top graphic: planar UVs along the board
  const uv = new Float32Array(p.count * 2); for (let i = 0; i < p.count; i++) { uv[i * 2] = p.getX(i) / 1.56 + 0.5; uv[i * 2 + 1] = p.getZ(i) / 0.28 + 0.5; } geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  const deck = new THREE.Mesh(geo, new THREE.MeshPhysicalMaterial({ map: boardTex, roughness: 0.35, clearcoat: 0.8, clearcoatRoughness: 0.1 }));
  deck.castShadow = true; board.add(deck);
  const bk = new THREE.MeshStandardMaterial({ color: 0x1a1a1a, roughness: 0.5 });
  for (const x of [-0.26, 0.26]) { const bd = new THREE.Mesh(new RoundedBoxGeometry(0.12, 0.05, 0.26, 2, 0.02), bk); bd.position.set(x, 0.035, 0); bd.castShadow = true; board.add(bd);
    const hb = new THREE.Mesh(new RoundedBoxGeometry(0.11, 0.16, 0.025, 2, 0.01), bk); hb.position.set(x, 0.1, 0.115); hb.rotation.x = -0.25; board.add(hb);      // highback
    for (const [zz, yy] of [[-0.06, 0.1], [0.04, 0.12]]) { const st = new THREE.Mesh(new RoundedBoxGeometry(0.135, 0.022, 0.05, 2, 0.008), new THREE.MeshStandardMaterial({ color: 0x2b6cff, roughness: 0.5 })); st.position.set(x, yy, zz); board.add(st); } }
  scene.add(board); }
const shovel = new THREE.Group();
{ const alu = new THREE.MeshStandardMaterial({ color: 0xd7dde4, roughness: 0.3, metalness: 0.8 }), blade = new THREE.MeshStandardMaterial({ color: 0xff8a1e, roughness: 0.45 });
  const sh = new THREE.Mesh(new THREE.CylinderGeometry(0.016, 0.016, 0.72, 10), alu); sh.position.y = -0.3; shovel.add(sh);
  const grip = new THREE.Mesh(new RoundedBoxGeometry(0.11, 0.035, 0.035, 2, 0.012), new THREE.MeshStandardMaterial({ color: 0x222222, roughness: 0.6 })); grip.position.y = 0.06; shovel.add(grip);
  const bl = new THREE.Mesh(new RoundedBoxGeometry(0.24, 0.28, 0.025, 2, 0.01), blade); bl.position.set(0, -0.78, 0.02); bl.rotation.x = 0.25; shovel.add(bl);
  shovel.traverse(o => { if (o.isMesh) o.castShadow = true; }); scene.add(shovel); }
const arrowMat = new THREE.MeshStandardMaterial({ color: 0x3cff6a, emissive: 0x0b7a22, roughness: 0.4, transparent: true });
const arrow = new THREE.Group();
{ const sh = new THREE.Shape(); sh.moveTo(0, -0.18); sh.lineTo(1.6, -0.18); sh.lineTo(1.6, -0.45); sh.lineTo(2.4, 0); sh.lineTo(1.6, 0.45); sh.lineTo(1.6, 0.18); sh.lineTo(0, 0.18); sh.closePath();
  const m = new THREE.Mesh(new THREE.ExtrudeGeometry(sh, { depth: 0.06, bevelEnabled: true, bevelSize: 0.03, bevelThickness: 0.03, bevelSegments: 2 }), arrowMat); arrow.add(m); scene.add(arrow); }
const dropMat = new THREE.MeshPhysicalMaterial({ color: 0xbfe6ff, roughness: 0.05, transmission: 0.0, transparent: true, opacity: 0.9, emissive: 0x2a6a9a, emissiveIntensity: 0.6 });
const drop = new THREE.Mesh(new THREE.SphereGeometry(0.009, 16, 12).scale(1, 1.4, 1), dropMat); scene.add(drop);
const trail = new THREE.Mesh(new THREE.CylinderGeometry(0.003, 0.003, 1, 8), dropMat); scene.add(trail);

// ------------------------------------------------------------------ the two guys (winter clothes over the same sculpt)
const SNOWY = { uSnow: { value: 0 } };
function snowy(m, U = SNOWY) {           // snow caked onto clothes (rest-pose noise so it sticks to the cloth)
  m.onBeforeCompile = sh => {
    Object.assign(sh.uniforms, U);
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vRestS;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvRestS = position;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', `#include <common>
varying vec3 vRestS; uniform float uSnow;
float snh(vec3 p){ return fract(sin(dot(p, vec3(12.9898, 78.233, 37.719))) * 43758.5453); }
float snn(vec3 p){ vec3 i = floor(p), f = fract(p); vec3 u = f*f*(3.0-2.0*f);
  return mix(mix(mix(snh(i), snh(i+vec3(1,0,0)), u.x), mix(snh(i+vec3(0,1,0)), snh(i+vec3(1,1,0)), u.x), u.y),
             mix(mix(snh(i+vec3(0,0,1)), snh(i+vec3(1,0,1)), u.x), mix(snh(i+vec3(0,1,1)), snh(i+vec3(1,1,1)), u.x), u.y), u.z); }`)
      .replace('#include <color_fragment>', `#include <color_fragment>
  float sn0 = snn(vRestS * 38.0) * 0.6 + snn(vRestS * 110.0) * 0.4;
  float snA = smoothstep(1.0 - uSnow * 0.75, 1.02 - uSnow * 0.75, sn0) * step(0.001, uSnow);
  diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.93, 0.96, 1.0), snA);`)
      .replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\n  roughnessFactor = mix(roughnessFactor, 0.85, snA);');
  };
  return m;
}
function outfit(jacket, pants, beanie, U) {
  const nylon = c => snowy(new THREE.MeshPhysicalMaterial({ color: c, roughness: 0.5, sheen: 0.4, sheenRoughness: 0.5, sheenColor: new THREE.Color(0xffffff), clearcoat: 0.25, clearcoatRoughness: 0.5 }), U);
  return { skin: new THREE.MeshPhysicalMaterial({ color: 0xd99a7c, roughness: 0.55, sheen: 0.12, sheenColor: new THREE.Color(0xffb099), sheenRoughness: 0.6 }),
    shirt: nylon(jacket), sleeve: nylon(jacket), glove: snowy(new THREE.MeshStandardMaterial({ color: 0x17181c, roughness: 0.6 }), U),
    jeans: snowy(new THREE.MeshStandardMaterial({ color: pants, roughness: 0.75 }), U), shoe: snowy(new THREE.MeshStandardMaterial({ color: 0x2a2320, roughness: 0.6 }), U),
    sole: new THREE.MeshStandardMaterial({ color: 0x1c1c1c, roughness: 0.8 }), hair: new THREE.MeshStandardMaterial({ color: 0x4a2c1a, roughness: 0.62 }), beanie };
}
function addBeanie(G, color, stripe) {
  const tex = canvasTex(256, 256, g => { g.fillStyle = color; g.fillRect(0, 0, 256, 256); g.fillStyle = 'rgba(0,0,0,0.12)'; for (let x = 0; x < 256; x += 8) g.fillRect(x, 0, 3, 256);
    g.fillStyle = stripe; g.fillRect(0, 196, 256, 22); });
  tex.wrapS = THREE.RepeatWrapping; tex.repeat.set(3, 1);
  const mat = new THREE.MeshStandardMaterial({ map: tex, roughness: 0.95 });
  const hc = V(...G.man.headC), headH = V(0, 0, 0);
  G.reset(); G.root.updateMatrixWorld(true);
  const grp = new THREE.Group();
  const tilt = 0.28, th = Math.PI * 0.53;
  const cap = new THREE.Mesh(new THREE.SphereGeometry(1, 48, 24, 0, Math.PI * 2, 0, th), mat);
  cap.scale.set(0.094, 0.118, 0.114); cap.position.copy(hc).add(V(0, 0.022, 0.014)); cap.rotation.x = tilt; cap.castShadow = true; grp.add(cap);
  const cuff = new THREE.Mesh(new THREE.TorusGeometry(1, 0.12, 10, 48).rotateX(Math.PI / 2), mat);
  const ey = Math.cos(th);                                       // the cap's rim sits at this fraction of its height
  cuff.scale.set(0.094 * Math.sin(th) + 0.004, 0.11, 0.114 * Math.sin(th) + 0.004); cuff.position.copy(cap.position).add(V(0, 0.118 * ey * Math.cos(tilt) + 0.004, 0.118 * ey * Math.sin(tilt))); cuff.rotation.x = tilt; grp.add(cuff);
  const pom = new THREE.Mesh(new THREE.IcosahedronGeometry(0.032, 2), new THREE.MeshStandardMaterial({ color: stripe, roughness: 1 }));
  pom.position.copy(cap.position).add(V(0, 0.118 * Math.cos(tilt), 0.118 * Math.sin(tilt))); grp.add(pom);
  grp.updateMatrixWorld(true);
  const inv = G.bones.head.matrixWorld.clone().invert();
  grp.applyMatrix4(inv);
  G.bones.head.add(grp);
  for (const n of ['hairCards']) if (G.meshes[n]) G.meshes[n].visible = false;
  return grp;
}
const SNOW1 = { uSnow: { value: 0 } }, SNOW2 = { uSnow: { value: 0.12 } };
const G = await loadGuy(THREE, '/char/guy', { materials: outfit(0xe2312a, 0x272c38, null, SNOW1) });
scene.add(G.root); G.root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
addBeanie(G, '#ffcf26', '#1d1d1d');
const F = await loadGuy(THREE, '/char/guy', { materials: outfit(0x1f9fd8, 0x3a3a3a, null, SNOW2) });
scene.add(F.root); F.root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
addBeanie(F, '#e8412c', '#ffffff');
const HIP = V(0.0, 0.95, 0.0);
const ANK = G.bones.footR.userData.head.y;                 // ankle height above the sole at rest

// ------------------------------------------------------------------ rig: local joint angles (deg), limits, blending (same axes as quick.js)
const LIMITS = {
  spine1: [[-30, 25], [-25, 25], [-20, 20]], spine2: [[-30, 25], [-25, 25], [-20, 20]], chest: [[-25, 20], [-25, 25], [-15, 15]],
  neck: [[-35, 35], [-55, 55], [-25, 25]], head: [[-30, 30], [-40, 40], [-20, 20]],
  uarmR: [[-60, 170], [-80, 80], [-40, 175]], uarmL: [[-60, 170], [-80, 80], [-175, 40]],
  farmR: [[0, 145], [-80, 80], [-20, 20]], farmL: [[0, 145], [-80, 80], [-20, 20]],
  handR: [[-60, 60], [-30, 30], [-60, 60]], handL: [[-60, 60], [-30, 30], [-60, 60]],
  thighR: [[-30, 120], [-40, 40], [-25, 45]], thighL: [[-30, 120], [-40, 40], [-45, 25]],
  shinR: [[-150, 0], [-10, 10], [-5, 5]], shinL: [[-150, 0], [-10, 10], [-5, 5]],
  footR: [[-45, 30], [-15, 15], [-15, 15]], footL: [[-45, 30], [-15, 15], [-15, 15]],
  clavR: [[-15, 15], [-10, 10], [-10, 25]], clavL: [[-15, 15], [-10, 10], [-25, 10]],
};
function softc(x, lo, hi, knee = 6) {
  if (x > hi - knee) return hi - knee + knee * Math.tanh((x - (hi - knee)) / knee);
  if (x < lo + knee) return lo + knee - knee * Math.tanh(((lo + knee) - x) / knee);
  return x;
}
const FINGERS = ['index', 'middle', 'ring', 'pinky'];
function curl(p, S, c, th = c) {
  for (const f of FINGERS) { p[f + '1' + S] = [0, 0, (S === 'R' ? -1 : 1) * c * 0.9]; p[f + '2' + S] = [0, 0, (S === 'R' ? -1 : 1) * c]; }
  p['thumb1' + S] = [0, 0, (S === 'R' ? -1 : 1) * th * 0.4]; return p;
}
const P = {
  ride: { spine1: [-8, 0, 0], spine2: [-4, 6, 0], chest: [0, 4, 0], uarmR: [22, 0, -12], uarmL: [10, 0, 12], farmR: [34, 0, 0], farmL: [28, 0, 0], neck: [6, 10, 0], head: [2, 6, 0] },
  lookBack: { spine1: [-2, 0, 0], spine2: [0, 14, 0], chest: [4, 12, 0], uarmR: [30, 0, 0], uarmL: [10, 0, -2], farmR: [50, 0, 0], farmL: [36, 0, 0], neck: [14, 40, 0], head: [12, 26, 0] },
  charge: { spine1: [-10, 0, 0], spine2: [-6, 8, 0], chest: [-2, 8, 0], uarmR: [30, 0, 4], uarmL: [12, 0, -2], farmR: [36, 0, 0], farmL: [30, 0, 0], neck: [-2, 32, 0], head: [-2, 20, 0] },
  swimA: { spine1: [-8, 0, 0], spine2: [-6, 10, 0], uarmR: [150, 0, 30], uarmL: [-30, 0, -40], farmR: [20, 0, 0], farmL: [40, 0, 0], neck: [18, 0, 0], head: [10, 0, 0], thighR: [30, 0, 8], thighL: [10, 0, -8], shinR: [-40, 0, 0], shinL: [-20, 0, 0] },
  swimB: { spine1: [-8, 0, 0], spine2: [-6, -10, 0], uarmR: [-30, 0, 40], uarmL: [150, 0, -30], farmR: [40, 0, 0], farmL: [20, 0, 0], neck: [18, 0, 0], head: [10, 0, 0], thighR: [10, 0, 8], thighL: [30, 0, -8], shinR: [-20, 0, 0], shinL: [-40, 0, 0] },
  buried: { spine1: [-4, 0, 6], spine2: [-2, 0, 6], chest: [0, 0, 4], uarmR: [20, 0, 40], uarmL: [30, 0, -40], farmR: [50, 0, 0], farmL: [60, 0, 0], neck: [6, 0, 0], head: [4, 0, 0],
    thighR: [26, 0, 10], thighL: [8, 0, -6], shinR: [-46, 0, 0], shinL: [-18, 0, 0], footR: [-10, 0, 0], footL: [-6, 0, 0] },
  punch: { uarmR: [10, 0, 112], farmR: [8, 0, 0], handR: [0, 0, 10] },
  cup: { uarmL: [70, -20, -26], farmL: [118, 30, 0], handL: [-20, 0, 0] },
  // the friend
  run: { spine1: [-12, 0, 0], spine2: [-8, 0, 0], uarmR: [0, 0, -26], uarmL: [0, 0, 26], farmR: [70, 0, 0], farmL: [70, 0, 0], neck: [6, 0, 0] },
  kneel: { thighR: [80, 0, 6], thighL: [10, 0, -6], shinR: [-95, 0, 0], shinL: [-110, 0, 0], footR: [20, 0, 0], footL: [-20, 0, 0], spine1: [-18, 0, 0], spine2: [-14, 0, 0], chest: [-6, 0, 0],
    uarmR: [60, 0, -20], uarmL: [70, 0, 24], farmR: [40, 0, 0], farmL: [50, 0, 0], neck: [10, 0, 0], head: [6, 0, 0] },
  dig: { uarmR: [90, 0, -22], uarmL: [96, 0, 28], farmR: [20, 0, 0], farmL: [30, 0, 0], spine1: [-24, 0, 0], spine2: [-18, 0, 0] },
  scoop: { uarmR: [40, 0, -10], uarmL: [52, 0, 18], farmR: [70, 0, 0], farmL: [76, 0, 0], spine1: [-8, 0, 0], spine2: [-4, 0, 0], chest: [4, 0, 0] },
};
for (const k of Object.keys(P)) { const c = ['charge', 'kneel', 'dig', 'scoop', 'run'].includes(k) ? 72 : k === 'punch' ? 85 : k === 'cup' ? 40 : 22; curl(P[k], 'R', c); curl(P[k], 'L', k === 'cup' ? 40 : c); }
function eul(p, n) { return p[n] || [0, 0, 0]; }
function mixPose(a, b, k) { const o = {}; for (const n of new Set([...Object.keys(a), ...Object.keys(b)])) { const x = eul(a, n), y = eul(b, n); o[n] = [lerp(x[0], y[0], k), lerp(x[1], y[1], k), lerp(x[2], y[2], k)]; } return o; }
function addPose(a, d) { const o = { ...a }; for (const [n, v] of Object.entries(d)) { const x = eul(o, n); o[n] = [x[0] + v[0], x[1] + v[1], x[2] + v[2]]; } return o; }
function over(a, d) { return { ...a, ...d }; }
function keyed(keys, t) {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 0; i < keys.length - 1; i++) { const [t0, a] = keys[i], [t1, b] = keys[i + 1]; if (t <= t1) return mixPose(a, b, sm((t - t0) / (t1 - t0))); }
  return keys[keys.length - 1][1];
}
function flail(T, amp, hz, seed) { return amp * (0.65 * Math.sin(2 * Math.PI * hz * T + seed) + 0.35 * Math.sin(2 * Math.PI * hz * 1.73 * T + seed * 2.1)); }
const qTmp = new THREE.Quaternion(), eTmp = new THREE.Euler();
const LASTA = {};
function applyPose(g, p, root, key) {               // root: absolute hips position {x, y, z} + yaw/tilt/roll (deg)
  const lim = {};
  for (const n of Object.keys(g.bones)) {
    const b = g.bones[n]; let e = eul(p, n);
    if (LIMITS[n]) e = e.map((v, i) => softc(v, LIMITS[n][i][0], LIMITS[n][i][1]));
    lim[n] = e;
    b.position.copy(g.REST[n].pos);
    b.quaternion.copy(g.REST[n].q).multiply(qTmp.setFromEuler(eTmp.set(e[0] * D2R, e[1] * D2R, e[2] * D2R)));
  }
  const R = new THREE.Quaternion().setFromEuler(new THREE.Euler((root.tilt || 0) * D2R, (root.yaw || 0) * D2R, (root.roll || 0) * D2R, 'YXZ'));
  g.root.quaternion.copy(R);
  g.root.position.copy(V(root.x, root.y, root.z)).sub(HIP.clone().applyQuaternion(R));
  g.root.updateMatrixWorld(true);
  LASTA[key] = lim;
}

function armIK(g, S, target, pole, w, flip = 1) {        // two-bone arm IK (shoulder fixed), blended over the posed arm by w
  if (w < 0.001) return;
  const names = ['uarm' + S, 'uarmTwist' + S, 'farm' + S, 'farmTwist' + S];
  const keep = names.map(n => g.bones[n].quaternion.clone());
  g.root.updateMatrixWorld(true);
  const sh = g.bones['uarm' + S].getWorldPosition(new THREE.Vector3());
  const l1 = g.REST['uarm' + S].len, l2 = g.REST['farm' + S].len;
  const tv = target.clone().sub(sh); let d = clamp(tv.length(), Math.abs(l1 - l2) + 1e-3, l1 + l2 - 1e-3);
  const dir = tv.normalize();
  const side = new THREE.Vector3().crossVectors(dir, pole.clone().sub(sh)).normalize().multiplyScalar(flip);
  const up = new THREE.Vector3().crossVectors(side, dir).normalize().multiplyScalar(flip);
  const a = Math.acos(clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1));
  const elbow = sh.clone().addScaledVector(dir, Math.cos(a) * l1).addScaledVector(up, Math.sin(a) * l1);
  const hand = sh.clone().addScaledVector(dir, d);
  g.bones['uarmTwist' + S].quaternion.identity(); g.bones['farmTwist' + S].quaternion.identity();
  g.aim('uarm' + S, elbow.clone().sub(sh), side);
  g.aim('farm' + S, hand.clone().sub(elbow), side);
  names.forEach((n, i) => g.bones[n].quaternion.copy(keep[i].clone().slerp(g.bones[n].quaternion.clone(), w)));
  g.root.updateMatrixWorld(true);
}

// ------------------------------------------------------------------ the story
const beatAt = t => { let i = 0; for (let k = 0; k < B.length; k++) if (t >= B[k]) i = k; return i; };
const X0 = -6, VX0 = 0.6, Z0 = 100;                      // where he is riding when it cracks
function rideX(t) {                                       // his own traverse across the slope (beats 0-3, and 9 into the loop)
  const b = beatAt(t), lt = t - B[b];
  if (b === 9) return X0 - VX0 * (DUR[9] - lt);
  if (t < 1.4) return X0 + VX0 * t - 0.5 * (VX0 / 1.4) * t * t;
  const xs = X0 + 0.5 * VX0 * 1.4;
  if (t < B[1] + 0.8) return xs;
  const u = t - (B[1] + 0.8);
  return Math.min(13.2, xs + 0.45 * u * u);               // pushes off, then charges for the edge of the slab
}
function boardPose(t) {                                   // board centre (on the moving slab) and its edge tilt
  const x = rideX(t), D = beatAt(t) === 9 ? 0 : slabD(t), z = Z0 - D * COSA;
  return { x, z, y: terrain(x, z) + 0.012, edge: beatAt(t) === 2 ? 15 : 21 };
}
// buried pose geometry (beats 4-8)
const SURF_B = debrisH(XB, ZB);
const BURY = { x: XB, y: SURF_B - 1.32, z: ZB - 0.02, roll: 28 };

function guyAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  const f = { blink: blink(t) };
  let pose, root, ride = null, face = f, snow = 0;
  if (b === 0 || b === 9 || b === 1 || b === 2 || (b === 3 && lt < 0.4)) {
    const bp = boardPose(t);
    ride = bp;
    root = { x: bp.x, y: bp.y + 0.76, z: bp.z + 0.06, yaw: 0 };
    if (b === 9) { pose = P.ride; face = { ...f, smile: 0.55, brow: 0.2, look: [0.15, 0] }; root.y += 0.015 * Math.sin(t * 5); }
    else if (b === 0) {
      const k = smooth(T_CRACK + 0.1, T_CRACK + 0.7, lt);
      pose = mixPose(P.ride, P.lookBack, k);
      root.y += 0.015 * Math.sin(t * 5) * (1 - k) - 0.05 * k;
      const jolt = Math.exp(-((((lt - T_CRACK - 0.05) / 0.12)) ** 2));
      root.y -= 0.04 * jolt;
      face = { ...f, smile: 0.55 * (1 - smooth(T_CRACK, T_CRACK + 0.25, lt)), brow: 0.2 + 0.8 * k, fear: k, jaw: 0.35 * k, oh: 0.4 * k, look: [0.15 + 0.5 * k, 0.35 * k] };
    } else if (b === 1) {
      const k = smooth(0.5, 1.4, lt);
      pose = mixPose(P.lookBack, P.charge, k);
      pose = addPose(pose, { uarmR: [flail(t, 6, 1.1, 1), 0, 0], uarmL: [flail(t, 6, 1.0, 2), 0, 0] });
      root.y -= 0.05 + 0.04 * k; root.yaw = -6 * k;
      face = { ...f, fear: 1 - 0.3 * k, browIn: 0.6 * k, jaw: 0.3 - 0.1 * k, press: 0.4 * k, look: [0.5 - 0.6 * k, 0.2 * (1 - k)] };
    } else {
      pose = P.charge;
      const wob = flail(t, 1, 1.6, 3);
      pose = addPose(pose, { uarmR: [6 * wob, 0, 8 * wob], uarmL: [-5 * wob, 0, -6 * wob], spine2: [0, 4 * wob, 0] });
      root.y -= 0.04 + 0.02 * Math.sin(t * 9); root.yaw = -8;
      face = b === 3 ? { ...f, fear: 1, brow: 1, jaw: 0.5, oh: 0.4, look: [-0.3, 0.3] } : { ...f, browIn: 1, pain: 0.4, press: 0.5, sneer: 0.2, look: [-0.5, 0] };
    }
  } else if (b === 3) {                                   // caught: knocked off his feet, swimming in the flow
    const bp = boardPose(B[3]);
    const hit = smooth(0.3, 0.75, lt);
    const D = slabD(t), z = Z0 - D * COSA, x = lerp(bp.x, 9.5, smooth(0.3, d, lt));
    const sw = smooth(0.7, 1.1, lt);
    const ph = (lt - 0.7) * 2.4;
    const swim = mixPose(P.swimA, P.swimB, 0.5 + 0.5 * Math.sin(ph * Math.PI));
    pose = mixPose(mixPose(P.charge, P.lookBack, hit), swim, sw);
    root = { x, y: terrain(x, z) + lerp(0.66, 0.9, hit) + 0.25 * sw + 0.15 * Math.sin(lt * 3.1) * sw, z: z + 0.1, tilt: lerp(0, 55, hit) + 12 * Math.sin(lt * 2.3) * sw, roll: lerp(0, -25, hit) + 15 * Math.sin(lt * 1.7) * sw, yaw: -10 + 25 * sw };
    face = { ...f, fear: 1, browIn: 0.4, jaw: 0.5 + 0.2 * Math.sin(lt * 7), pain: 0.6 * hit, oh: 0.3, squint: 0.5 * sw, look: [0, 0.2] };
    snow = 0.6 * hit;
  } else if (b >= 4 && b <= 7) {                          // buried
    root = { x: BURY.x, y: BURY.y, z: BURY.z, roll: BURY.roll };
    snow = 1;
    if (b === 4) {
      const slide = 1 - smooth(0, 1.4, lt);
      root.x = BURY.x - 0.6 * slide * slide; root.roll = BURY.roll - 14 * slide; root.y = BURY.y + 0.12 * slide;
      const pk = smooth(0.45, 1.15, lt);
      pose = mixPose(P.buried, over(P.buried, P.punch), pk);
      pose = addPose(pose, { spine2: [0, 0, flail(t, 3, 1.2, 2) * slide], uarmL: [flail(t, 10, 1.4, 1) * slide, 0, 0] });
      face = { ...f, fear: 0.8, browIn: 0.8, press: 0.6 * pk, pain: 0.4 * pk, squint: 0.7, jaw: 0.1 };
    } else if (b === 5) {
      const ck = smooth(0.1, 0.9, lt);
      pose = mixPose(over(P.buried, P.punch), over(over(P.buried, P.punch), P.cup), ck);
      face = { ...f, fear: 0.6, browIn: 0.7, squint: 0.6, jaw: 0.08, look: [0.2, -0.1] };
    } else if (b === 6) {
      const st = smooth(0, 0.5, lt);
      pose = over(over(P.buried, P.punch), P.cup);
      const strain = smooth(0.9, 1.4, lt) * (1 - smooth(d - 0.5, d, lt));
      pose = addPose(pose, { spine2: [0, 0, flail(t, 1.2, 9, 1) * strain], uarmR: [flail(t, 1.5, 11, 2) * strain, 0, 0], thighR: [flail(t, 1.5, 10, 3) * strain, 0, 0] });
      face = { ...f, fear: 0.5 + 0.4 * strain, browIn: 1, pain: 0.8 * strain, press: 0.7, squint: 0.6 + 0.4 * strain, jaw: 0.05 + 0.1 * (1 - st) };
    } else {
      pose = over(over(P.buried, P.punch), P.cup);
      const spit = smooth(0.25, 0.5, lt) * (1 - smooth(1.1, 1.5, lt));
      const strain = smooth(3.2, 3.6, lt) * (1 - smooth(d - 0.3, d, lt));
      pose = addPose(pose, { spine2: [0, 0, flail(t, 1.2, 9, 1) * strain], uarmR: [flail(t, 1.5, 11, 2) * strain, 0, 0] });
      face = { ...f, fear: 0.5, browIn: 0.6 + 0.4 * strain, oh: 0.6 * spit, jaw: 0.12 * spit, pain: 0.7 * strain, press: 0.5 * (1 - spit), squint: 0.4 + 0.5 * strain, look: [0, -0.6 * smooth(0.4, 0.9, lt) * (1 - smooth(1.8, 2.3, lt))] };
    }
  } else {                                                // beat 8: dug out; he gasps at the end
    root = { x: BURY.x, y: BURY.y, z: BURY.z, roll: BURY.roll };
    snow = 1;
    pose = over(over(P.buried, P.punch), P.cup);
    const air = smooth(d - 1.3, d - 0.8, lt);
    pose = mixPose(pose, over(pose, { uarmL: [30, 0, -40], farmL: [50, 0, 0], neck: [20, 0, 0], head: [10, 0, 0] }), air);
    face = { ...f, fear: 0.3 * (1 - air), jaw: 0.55 * air, oh: 0.5 * air, brow: 0.8 * air, browIn: 0.8 * (1 - air), squint: 0.7 * (1 - air), look: [0, 0.5 * air] };
  }
  const cup = b === 5 ? smooth(0.1, 0.9, lt) : b === 6 ? 1 : b === 7 ? 1 - 0.7 * smooth(0.0, 0.35, lt) : b === 8 ? 0.3 * (1 - smooth(d - 1.3, d - 0.8, lt)) : 0;
  return { pose, root, face, ride, snow, cup };
}
const SHOVEL_L = 0.92;                                     // grip to blade tip
function friendAt(t, hole) {                              // only in beat 8: kneels uphill of his head, facing it (and us)
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  if (b !== 8) return null;
  const K = V(hole.x - 0.5, 0, hole.z + 0.85);
  const fwd = V(hole.x - K.x, 0, hole.z - K.z).normalize(), right = V(-fwd.z, 0, fwd.x), kyaw = Math.atan2(-fwd.x, -fwd.z) / D2R;
  let pose, root, face = { blink: blink(t + 1.3) }, dig = null, reach = 0;
  if (lt < 1.05) {                                        // runs in down the debris
    const u = lt / 1.05, ph = 2 * Math.PI * 1.7 * lt;
    pose = addPose(P.run, { thighR: [32 * Math.sin(ph), 0, 0], thighL: [-32 * Math.sin(ph), 0, 0], shinR: [-(15 + 45 * Math.max(0, Math.sin(ph + 1.2))), 0, 0], shinL: [-(15 + 45 * Math.max(0, Math.sin(ph + 1.2 + Math.PI))), 0, 0],
      uarmR: [-28 * Math.sin(ph), 0, 0], uarmL: [28 * Math.sin(ph), 0, 0] });
    const x = lerp(K.x - 2.4, K.x, sm(u)), z = lerp(K.z + 3.2, K.z, sm(u));
    root = { x, y: debrisH(x, z) + 0.92 + 0.03 * Math.abs(Math.sin(ph)), z, yaw: lerp(-37, kyaw, smooth(0.6, 1.0, u)) };
    face = { ...face, fear: 0.6, browIn: 0.8, jaw: 0.25, look: [0.2, -0.4] };
  } else {
    const k = smooth(1.05, 1.5, lt);
    const on = smooth(1.35, 1.6, lt) * (1 - smooth(d - 1.1, d - 0.85, lt));
    reach = smooth(d - 1.0, d - 0.6, lt);
    const sy = debrisY0Hole, dd = digDepth(t);
    // one stroke a second: stab in, pry back, lift and throw to his right, swing back
    const p = ((lt - 1.5) % 1 + 1) % 1;
    const at = (f, r, y) => K.clone().addScaledVector(fwd, f).addScaledVector(right, r).setY(y);
    const k0 = at(0.5, 0.05, sy + 0.32), k1 = at(0.78, 0.02, sy - 0.12 - 0.45 * dd), k2 = at(0.55, 0.06, sy + 0.02 - 0.2 * dd), k3 = at(0.3, 0.72, sy + 0.42);
    const seg = (a, b2, u) => a.clone().lerp(b2, sm(clamp(u, 0, 1)));
    const blade = p < 0.3 ? seg(k0, k1, p / 0.3) : p < 0.5 ? seg(k1, k2, (p - 0.3) / 0.2) : p < 0.75 ? seg(k2, k3, (p - 0.5) / 0.25) : seg(k3, k0, (p - 0.75) / 0.25);
    const lean = p < 0.3 ? sm(p / 0.3) : p < 0.5 ? 1 - 0.6 * sm((p - 0.3) / 0.2) : 0.4 * (1 - sm((p - 0.5) / 0.5));
    const twist = p < 0.5 ? 0 : p < 0.75 ? sm((p - 0.5) / 0.25) : 1 - sm((p - 0.75) / 0.25);
    const ky = debrisH(K.x, K.z);
    const chest = K.clone().addScaledVector(fwd, 0.12 + 0.12 * lean).addScaledVector(right, 0.12 + 0.12 * twist).setY(ky + 0.95 - 0.12 * lean);
    const sh = chest.clone().sub(blade).normalize();
    const grip = blade.clone().addScaledVector(sh, SHOVEL_L);
    dig = { blade, grip, low: blade.clone().addScaledVector(sh, 0.42), toss: p > 0.55 && p < 0.85 ? (p - 0.55) / 0.3 : -1, on };
    pose = mixPose(P.run, over(P.kneel, { spine1: [-16 - 14 * lean * on, -8 * twist * on, 0], spine2: [-12 - 10 * lean * on, -10 * twist * on, 0], chest: [-4, -6 * twist * on, 0], neck: [18, 0, 0], head: [8, 0, 0] }), k);
    root = { x: K.x, y: ky + lerp(0.9, 0.5, k) - 0.04 * lean * on, z: K.z, yaw: kyaw };
    face = { ...face, fear: 0.4 * (1 - reach), browIn: 1 - 0.6 * reach, press: 0.5 * on, pain: 0.35 * on * lean, jaw: 0.1 + 0.35 * reach, smile: 0.45 * smooth(d - 0.45, d - 0.1, lt), brow: 0.8 * reach, look: [0, -0.6] };
  }
  return { pose, root, face, dig, reach, hole, right, fwd };
}
function blink(t) { for (const b0 of [1.6, 6.2, 11.1, 17.4, 21.0, 27.9, 33.0, 37.2]) { const u = (t - b0) / 0.16; if (u > 0 && u < 1) return Math.sin(Math.PI * u); } return 0; }
function digDepth(t) { const b = beatAt(t), lt = t - B[b]; if (b !== 8) return 0; return smooth(1.5, DUR[8] - 1.1, lt); }

// ------------------------------------------------------------------ cameras, one shot per beat
function wpos(g, n) { return g.bones[n].getWorldPosition(new THREE.Vector3()); }
function shake(t, a, f = 1) { return V(vn1(t * 3 * f, 1) * a, vn1(t * 3 * f, 2) * a, vn1(t * 3 * f, 3) * a * 0.5); }
function camAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b], u = lt / d;
  let pos, tgt, fov = 42, cut = false;
  const hp = wpos(G, 'hips'), hd = wpos(G, 'head');
  if (b === 0 || b === 9) {                               // the hook: low and in front, him big, the crack above him
    const bp = boardPose(b === 0 ? 0 : t);
    const x = b === 0 ? bp.x : rideX(t);
    const k = b === 0 ? sm(u) : 0;
    const fy = terrain(X0, Z0);
    const trk = b === 9 ? (rideX(t) - X0) * (1 - sm(clamp(lt / d, 0, 1))) : 0;
    const ride = b === 0 ? V(0, -SINA, -COSA).multiplyScalar(slabD(t)) : V(0, 0, 0);     // rides down with the slab once it goes
    pos = V(X0 + 0.4 + 0.1 * k + trk, fy + 0.95 + 0.05 * k, Z0 - 3.5 + 0.45 * k).add(ride);
    tgt = V(X0 - 0.05 + 0.2 * k + trk, fy + 2.0 + 0.4 * k, Z0 + 4).add(ride);
    fov = 52 - 4 * k;
    if (b === 0) { const jolt = Math.exp(-((((lt - T_CRACK - 0.05) / 0.25)) ** 2)); pos.add(shake(t, 0.06 * jolt, 3)); pos.add(shake(t, 0.012 * smooth(T_REL, d, lt), 2)); }
  } else if (b === 1) {                                   // wide from the side: the whole slab breaking up and running
    const D = slabD(t), zc = Z0 - D * COSA;                // from the ridge: the whole slab breaking up and running
    pos = V(-64, terrain(-64, 62) + 6, 62);
    tgt = V(2, lerp(Z0 * TANA - 4, zc * TANA - 2, 0.85), lerp(Z0 - 6, zc, 0.85));
    fov = lerp(30, 38, sm(u));
  } else if (b === 2) {                                   // chase: behind him and to the side, the edge of the slab ahead
    pos = hp.clone().add(V(0.55 - 0.2 * u, 0.55, -3.6)); tgt = hp.clone().add(V(0.35, -0.2, 0.0)); fov = 44; pos.add(shake(t, 0.02, 2.5));
  } else if (b === 3) {                                   // in the flow with him: handheld, whiteout
    pos = hp.clone().add(V(-1.9, 0.9, -2.0)); tgt = hp.clone().add(V(0.3, 0.1, 0)); fov = 52; pos.add(shake(t, 0.06, 2.8));
  } else if (b === 4) {                                   // cutaway: the whole burial, the hand breaking the surface
    pos = V(BURY.x + 0.2, SURF_B - 0.55, BURY.z - 4.6 + 0.4 * u); tgt = V(BURY.x - 0.05, SURF_B - 0.7, WALLZ); fov = 44; cut = true;
    pos.add(shake(t, 0.02 * (1 - smooth(0, 1.6, lt)), 2));
  } else if (b === 5) {                                   // cutaway, close on his face and the pocket
    const h = hd.clone();
    pos = V(h.x + 0.15, h.y + 0.05, BURY.z - 1.25 + 0.15 * u); tgt = V(h.x - 0.02, h.y - 0.02, WALLZ); fov = 40; cut = true;
  } else if (b === 6) {                                   // cutaway, medium: it sets
    const st = Math.exp(-((((lt - 0.2) / 0.15)) ** 2));
    pos = V(BURY.x + 0.1, SURF_B - 0.7, BURY.z - 2.3 - 0.1 * u); tgt = V(BURY.x - 0.1, SURF_B - 0.75, WALLZ); fov = 44; cut = true; pos.add(shake(t, 0.03 * st, 4));
  } else if (b === 7) {                                   // cutaway, tight on the face: the spit drop
    const h = hd.clone();
    pos = V(h.x + 0.05, h.y - 0.02, BURY.z - 0.85 - 0.25 * smooth(2.0, d, lt)); tgt = V(h.x - 0.04, h.y - 0.06, WALLZ); fov = 38; cut = true;
  } else {                                                // surface: the friend digs; push in to his face at the end
    const k = smooth(d - 1.6, d - 0.2, lt);
    const hole = V(hd.x, SURF_B, hd.z);
    const p0 = V(hole.x + 0.6, hole.y + 1.05, hole.z - 2.4), t0 = V(hole.x - 0.05, hole.y + 0.3, hole.z + 0.5);
    const p1 = hd.clone().add(V(0.2, 0.6, -0.75)), t1 = hd.clone().add(V(0, 0.02, 0));
    pos = p0.lerp(p1, k); tgt = t0.lerp(t1, k); fov = 46 - 8 * k;
  }
  const punch = b > 0 && b !== 9 ? (1 - smooth(0, 0.22, lt)) * 0.07 : 0;
  return { pos, tgt, fov: fov * (1 - punch), cut };
}

// ------------------------------------------------------------------ per-frame update
const pT = new THREE.Vector3(), qT = new THREE.Quaternion(), m4 = new THREE.Matrix4(), one = V(1, 1, 1);
const crackFx = { on: 0 }; let camCache = V(0, 0, 0);
function update(t) {
  t = ((t % TOTAL) + TOTAL) % TOTAL;
  const b = beatAt(t), lt = t - B[b];
  const g = guyAt(t);
  if (window.OVR && window.OVR.b === b) g.pose = over(g.pose, window.OVR.p);     // pose tuning hook (debug)
  applyPose(G, g.pose, g.root, 'G');
  if (g.ride) {                                           // feet locked to the board's bindings (leg IK)
    const bq = new THREE.Quaternion().setFromEuler(new THREE.Euler(-g.ride.edge * D2R, 0, 0));
    const c = V(g.ride.x, g.ride.y, g.ride.z);
    board.position.copy(c); board.quaternion.copy(bq); board.visible = true;
    for (const [S, x, yaw] of [['R', 0.26, -14], ['L', -0.26, 10]]) {
      const tgt = V(x, 0.05 + ANK, 0).applyQuaternion(bq).add(c);
      G.legIK(S, tgt, tgt.clone().add(V(0, 0.35, -1.0)), bq.clone().multiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(0, yaw * D2R, 0))));
    }
    G.root.updateMatrixWorld(true);
  } else board.visible = false;
  if (g.cup > 0) {
    const hw = wpos(G, 'head'), hq = G.bones.head.getWorldQuaternion(new THREE.Quaternion());
    const tgt = hw.clone().add(V(0.03, -0.035, -0.13).applyQuaternion(hq));       // forearm across, in front of his mouth
    const sh = wpos(G, 'uarmL');
    armIK(G, 'L', tgt, sh.clone().add(V(-0.4, -0.02, -0.3).applyQuaternion(hq)), g.cup);
  }
  G.untwist(); G.face(g.face);
  G.root.updateMatrixWorld(true);
  SNOW1.uSnow.value = 0.42 * g.snow;
  // the friend
  const hd0 = wpos(G, 'head'); debrisY0Hole = debrisH(hd0.x + 0.1, hd0.z + 0.3); const fr = friendAt(t, { x: hd0.x, z: hd0.z });
  F.root.visible = !!fr;
  if (fr) {
    applyPose(F, fr.pose, fr.root, 'F');
    if (fr.dig) {                                         // the shovel moves first; both hands ride on it (top hand on the grip, lower hand on the shaft)
      const { blade, grip, low } = fr.dig;
      shovel.position.copy(grip);
      shovel.quaternion.setFromUnitVectors(V(0, -1, 0), blade.clone().sub(grip).normalize());
      shovel.rotateY(Math.atan2(fr.fwd.x, fr.fwd.z));
      const up = V(0, 1, 0), w = fr.dig.on * (1 - fr.reach);
      const sR = wpos(F, 'uarmR'), sL = wpos(F, 'uarmL');
      armIK(F, 'R', grip, sR.clone().addScaledVector(fr.right, 0.45).addScaledVector(up, -0.35), Math.max(w, 0.0001) && 1);
      armIK(F, 'L', low, sL.clone().addScaledVector(fr.right, -0.45).addScaledVector(up, -0.35).addScaledVector(fr.fwd, 0.1), 1);
      if (fr.reach > 0) {                                 // shovel down, both hands brush the snow off his face
        const hd = wpos(G, 'head');
        armIK(F, 'R', hd.clone().addScaledVector(fr.right, 0.09).add(V(0, 0.1, 0)), sR.clone().addScaledVector(fr.right, 0.4).addScaledVector(up, -0.3), fr.reach);
        armIK(F, 'L', hd.clone().addScaledVector(fr.right, -0.09).add(V(0, 0.1, 0)), sL.clone().addScaledVector(fr.right, -0.4).addScaledVector(up, -0.3), fr.reach);
      }
    }
    F.untwist(); F.face(fr.face); F.root.updateMatrixWorld(true);
  }
  shovel.visible = !!(fr && fr.dig && fr.reach < 0.5);
  const C = camAt(t); camCache = C.pos.clone();
  // the crack, then the slab blocks
  CRACK.p.value = b === 9 ? 0 : smooth(T_CRACK, T_CRACK + 0.7, t); CRACK.x.value = X0 + 0.9;
  const D = slabD(t);
  const slabOn = b <= 3 || b === 9;
  blocks.visible = slabOn; groundMat.userData.u.uBed.value = b === 9 ? 0 : slabOn ? smooth(0.5, 2.0, D) : 1;
  let brokenAny = 0;
  if (slabOn) {
    const tt = b === 9 ? 0 : t;
    BLOCKS.forEach((bl, i) => { const br = blockPose(bl, tt, pT, qT); brokenAny = Math.max(brokenAny, br);
      const hide = (b === 3 && pT.distanceTo(camCache) < 7) || (b === 2 && br > 0.05 && pT.distanceTo(camCache) < 14) ? 0.0001 : 1;          // no slab pieces right in the lens while he is swallowed
      const sc = (1 - 0.55 * br) * hide;                                        // breaking up into smaller chunks
      m4.compose(pT, qT, V(sc, 1 - 0.3 * br, sc).multiplyScalar(hide)); blocks.setMatrixAt(i, m4); });
    blocks.instanceMatrix.needsUpdate = true;
  }
  // debris pile (runout): only after the slide; the friend's hole
  const deb = b >= 4 && b <= 8;
  debris.visible = deb; boulders.visible = deb;
  if (deb) {
    const p = debrisGeo.attributes.position.array, dd = digDepth(t), hole = { x: hd0.x, z: hd0.z };
    if (dd > 0 || debris.userData.dug) {
      for (let i = 0; i < p.length; i += 3) { const r2 = ((p[i] - hole.x - 0.1) ** 2) / 0.3 + ((p[i + 2] - hole.z + 0.1) ** 2) / 0.3;
        const floor = hd0.y - 0.16;                                    // dug down to just below his chin
        const cutd = Math.max(0, debrisY0[i + 1] - floor) * dd * Math.exp(-r2 * r2 * 0.5);
        p[i + 1] = debrisY0[i + 1] - cutd + 0.14 * dd * Math.exp(-((Math.sqrt(r2) - 1.7) ** 2) * 2.0); }
      debrisGeo.attributes.position.needsUpdate = true; debrisGeo.computeVertexNormals(); debris.userData.dug = dd > 0;
    }
  }
  // cutaway
  for (const m of [groundMat, debrisMat]) m.clippingPlanes = C.cut ? [clipCut] : null;
  cutWall.visible = C.cut;
  cutU.uT.value = t;
  cutU.uFlow.value = b === 4 ? -0.6 * (1 - smooth(0, 1.4, lt)) ** 2 : 0;
  cutU.uSet.value = b < 6 ? 0 : b === 6 ? smooth(0.05, 0.5, lt) : 1;
  const hd = wpos(G, 'head');
  cutU.uPocket.value.set(hd.x - 0.02, hd.y - 0.04, 0.13, 0.11);
  cutU.uPocketA.value = b === 5 ? smooth(0.7, 1.3, lt) : b === 6 || b === 7 ? 0.55 : 0;
  // the spit drop (beat 7): leaves his lips, runs down across his cheek (he's tilted), the trail stays
  drop.visible = trail.visible = false;
  if (b === 7) {
    const mouth = wpos(G, 'jaw').add(V(0, -0.02, -0.09).applyQuaternion(G.bones.head.getWorldQuaternion(new THREE.Quaternion())));
    const u = smooth(0.4, 2.2, lt);
    if (lt > 0.35) { drop.visible = true; trail.visible = u > 0.02;
      const p = mouth.clone().add(V(0.012 * u, -0.07 * u, -0.004));
      drop.position.copy(p); trail.position.copy(mouth.clone().lerp(p, 0.5)); trail.scale.set(1, Math.max(0.001, p.distanceTo(mouth)), 1); trail.lookAt(p); trail.rotateX(Math.PI / 2); }
  }
  // escape arrow (beat 2)
  arrow.visible = b === 2;
  if (b === 2) { const hp = wpos(G, 'hips'), k = smooth(0.1, 0.5, lt);
    const ax = hp.x + 0.75 + 0.08 * Math.sin(lt * 7), az = hp.z - 0.6; arrow.position.set(ax, hp.y + 0.55, az); arrow.rotation.set(0, Math.PI, 0); arrow.scale.setScalar(0.22 * k + 0.001);
    arrowMat.opacity = 0.9 * k; }
  // powder: crown dust at the crack, the cloud boiling off the broken slab, spray off the board, the whiteout around him
  if (slabOn && b !== 9) {
    const crackK = smooth(T_CRACK, T_CRACK + 0.9, t);
    for (let i = 0; i < 70 && t > T_CRACK; i++) { const x = SLAB.x0 + (i + 0.5) * (SLAB.x1 - SLAB.x0) / 70;
      const front = clamp((t - T_CRACK) / 0.9 * 36 - Math.abs(x - X0 - 2), 0, 1);
      const zc = SLAB.z1 - Math.max(0, D * 0.9) * COSA, a = front * 0.35 * (1 - smooth(4, 8, t));
      puff(V(x + hash1(i) * 0.3, terrain(x, zc) + 0.2 + 0.5 * hash1(i * 3) * crackK, zc - 0.3), 0.8 + 1.2 * crackK * hash1(i * 7), a); }
    if (D > 0.5) for (let i = 0; i < 340; i++) {
      const bl = BLOCKS[Math.floor(hash1(i * 1.7) * BLOCKS.length)], born = 1.2 + hash1(i * 4.1) * 30;
      const age = Math.max(0, Math.min(D, 60) - born) / 10; if (age <= 0) continue;
      blockPose(bl, t - 0.35 * age * 3, pT, qT);
      const rise = 2.0 * age + 3.2 * age * age;
      const p = pT.clone().add(V((hash1(i * 5.3) - 0.5) * 4, rise, 3.5 * age + (hash1(i * 8.8) - 0.5) * 3));
      puff(p, 2.0 + 8 * Math.min(1.2, age) * (0.6 + 0.6 * hash1(i * 2.2)), 0.42 * smooth(0, 0.15, age) * (1 - smooth(1.6, 2.6, age)));
    }
  }
  if (g.ride && (b === 0 || b === 2 || b === 9 || b === 1)) {          // board spray off the heel edge
    const spd = b === 2 ? 1 : b === 1 ? 0.6 : 0.35;
    for (let i = 0; i < 26; i++) { const a = ((t * 6 + hash1(i)) % 1);
      const p = V(g.ride.x - 0.8 - a * 1.6 * spd, g.ride.y + 0.08 + a * 0.4 * spd + 0.2 * a * a, g.ride.z + 0.15 + (hash1(i * 3) - 0.5) * 0.3);
      puff(p, 0.15 + 0.5 * a * spd, 0.5 * (1 - a) * spd); }
  }
  if (b === 2) {                                          // snow streaking past: speed
    const hp = wpos(G, 'hips');
    for (let i = 0; i < 70; i++) { const a = (t * (1.6 + hash1(i) * 1.2) + hash1(i * 3.3)) % 1;
      puff(hp.clone().add(V(3.5 - 7 * a, -0.8 + 2.2 * hash1(i * 5.1), -1.2 + 2.5 * hash1(i * 7.9))), 0.04 + 0.08 * hash1(i * 2.1), 0.8 * Math.sin(Math.PI * a)); }
    for (let i = 0; i < 24; i++) { const a = (t * 3 + hash1(i * 9.1)) % 1;            // spray off the heel edge, trailing behind
      puff(hp.clone().add(V(-0.9 - 1.4 * a, -0.85 + 0.5 * a, 0.2 + 0.2 * hash1(i))), 0.12 + 0.5 * a, 0.55 * (1 - a)); }
  }
  if (b === 3) {                                          // swallowed: boiling snow all around him
    const lt3 = t - B[3], k = smooth(0.15, 0.7, lt3), hp = wpos(G, 'hips');
    for (let i = 0; i < 260; i++) { const a = (lt3 * (0.6 + 0.8 * hash1(i * 2.9)) + hash1(i)) % 1;
      const ang = hash1(i * 5.5) * 6.283, r = 0.6 + 3.2 * hash1(i * 7.7);
      const p = hp.clone().add(V(Math.cos(ang) * r, -1.0 + 3.0 * hash1(i * 1.1) + 0.8 * a, Math.sin(ang) * r + 4 - 8 * a));
      if (p.distanceTo(camera.position) < 0.6) continue;
      puff(p, 0.6 + 1.6 * hash1(i * 4.3), 0.42 * k * Math.sin(Math.PI * a)); }
  }
  if (b === 4) {                                          // settling snow above the surface as it slows
    const k = 1 - smooth(0.6, 2.4, lt);
    for (let i = 0; i < 60; i++) { const x = BURY.x + (hash1(i) - 0.5) * 8, z = BURY.z + 0.4 + hash1(i * 3) * 6;
      puff(V(x, debrisH(x, z) + 0.3 + 0.8 * hash1(i * 7), z), 0.8 + 1.5 * hash1(i * 9), 0.35 * k); }
  }
  if (b === 8 && fr) {                                    // snow flying off the shovel
    const lt8 = t - B[8];
    if (fr.dig && fr.dig.toss >= 0) for (let i = 0; i < 40; i++) { const a = clamp(fr.dig.toss * (0.6 + 0.6 * hash1(i)) - 0.1 * hash1(i * 2), 0, 1);
      const p = fr.dig.blade.clone().addScaledVector(fr.right, 1.1 * a + 0.2 * (hash1(i * 3) - 0.5)).add(V((hash1(i * 5) - 0.5) * 0.25, 0.5 * a - 0.9 * a * a, (hash1(i * 7) - 0.5) * 0.25));
      puff(p, 0.05 + 0.2 * a, 0.75 * (1 - a * 0.8)); }
  }
  puffsDone();
  // whiteout fog while he is in the flow; clean mountain air otherwise
  const wo = b === 3 ? smooth(0.2, 0.9, t - B[3]) * (1 - smooth(DUR[3] - 0.5, DUR[3], t - B[3]) * 0.4) : 0;
  scene.fog.color.copy(FOGC).lerp(new THREE.Color(0xf2f6fc), wo); scene.fog.near = lerp(80, 4.5, wo); scene.fog.far = lerp(700, 24, wo);
  // light: shadow box follows the action
  const focus = b === 1 ? V(0, (Z0 - D * COSA) * TANA, Z0 - D * COSA) : wpos(G, 'hips');
  shadowBox(b === 1 ? 30 : 6);
  sun.position.copy(focus).addScaledVector(SUNDIR, 60); sun.target.position.copy(focus); sun.target.updateMatrixWorld();
  if (window.CAM) { C.pos = V(...window.CAM.pos); C.tgt = V(...window.CAM.tgt); C.fov = window.CAM.fov || 40; }
  camera.position.copy(C.pos); camera.lookAt(C.tgt); camera.fov = C.fov; camera.updateProjectionMatrix();
  for (const [k, o] of Object.entries({ puffs, blocks, arrow, board, ground })) if (DBG_HIDE.includes(k)) o.visible = false;
  return { beat: b, t };
}
const DBG_HIDE = (Q.get('hide') || '').split(',');

// ------------------------------------------------------------------ frame I/O (same contract as quick.js)
let composer = null;
if (Q.get('ao') !== '0') {
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
const gl = renderer.getContext();
const px = new Uint8Array(W * H * 4);
function renderInto(i) { update(i / FPS); draw(); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); }
window.renderAll = async (f0, f1) => { for (let i = f0; i < f1; i++) { renderInto(i); await fetch('/frame', { method: 'POST', body: px }); } return 'ok'; };
window.renderPNG = i => { update(i / FPS); draw(); return renderer.domElement.toDataURL('image/png'); };
window.renderAtT = t => { update(t); draw(); return renderer.domElement.toDataURL('image/png'); };
window.rigReport = i => { const r = update(i / FPS); return { t: r.t, beat: r.beat, ang: LASTA.G, hands: ['handR', 'handL'].map(n => G.bones[n].getWorldPosition(new THREE.Vector3()).toArray()),
  chest: G.bones.chest.getWorldPosition(new THREE.Vector3()).toArray(), hips: G.bones.hips.getWorldPosition(new THREE.Vector3()).toArray() }; };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS);
window.READY = true;
