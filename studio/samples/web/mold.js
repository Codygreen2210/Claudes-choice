// "What happens if you eat moldy bread" - a 3D Short with the sculpted, skinned guy in a kitchen.
//   mold.html?w=1080&h=1920            (times from mold/times.json; one shot per narration line)
// Beats: 0 he bites a moldy slice (hook) | 1 macro: the spot is the tip, threads run through the bread
//        2 cutting the green bit off doesn't work | 3 x-ray: stomach acid breaks the mold cells apart
//        4 most people: fine, maybe queasy | 5 x-ray: mycotoxins spread | 6 allergies: rash and a sneeze
//        7 he sniffs the loaf: spores up the nose, into the lungs | 8 throws it out | 9 grabs another slice (loops)
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
const TIMES = await (await fetch('/mold/times.json')).json();
const B = TIMES.starts, DUR = TIMES.durs, TOTAL = TIMES.total;
const clamp = (x, a, b) => Math.min(Math.max(x, a), b);
const sm = t => t * t * (3 - 2 * t);
const smooth = (a, b, x) => sm(clamp((x - a) / (b - a), 0, 1));
const lerp = (a, b, u) => a + (b - a) * u;
const D2R = Math.PI / 180;
function hash1(n) { const s = Math.sin(n * 127.1) * 43758.5453; return s - Math.floor(s); }
function vn1(x, seed) { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return lerp(hash1(i + seed * 17.3), hash1(i + 1 + seed * 17.3), u) * 2 - 1; }
const V = (x, y, z) => new THREE.Vector3(x, y, z);
const beatAt = t => { let i = 0; for (let k = 0; k < B.length; k++) if (t >= B[k]) i = k; return i; };

// ------------------------------------------------------------------ renderer / scene / light (a bright kitchen, morning sun through the window)
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(W, H);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.localClippingEnabled = true;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xf3e7d6);
const camera = new THREE.PerspectiveCamera(40, W / H, 0.01, 100);
{ const pm = new THREE.PMREMGenerator(renderer); const es = new THREE.Scene();
  es.add(new THREE.Mesh(new THREE.SphereGeometry(10, 32, 16), new THREE.MeshBasicMaterial({ color: 0xfff1de, side: THREE.BackSide })));
  const w = new THREE.Mesh(new THREE.PlaneGeometry(6, 4), new THREE.MeshBasicMaterial({ color: 0xffffff })); w.position.set(-3, 3, 6); w.lookAt(0, 1, 0); es.add(w);
  scene.environment = pm.fromScene(es, 0.04).texture; scene.environmentIntensity = 0.55; }
const hemi = new THREE.HemisphereLight(0xfff4e6, 0xb89a7a, 0.9); scene.add(hemi);
const sun = new THREE.DirectionalLight(0xffe2bd, 2.6);           // through the window behind-left of him
sun.position.set(-2.5, 3.2, 3.5); sun.target.position.set(0, 1, 0); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -2.2, right: 2.2, top: 2.2, bottom: -2.2, near: 0.5, far: 12 }); sun.shadow.bias = -0.0003; sun.shadow.normalBias = 0.02;
scene.add(sun); scene.add(sun.target);
const key = new THREE.DirectionalLight(0xfff6ea, 1.3); key.position.set(1.5, 2.6, -3.0); scene.add(key);     // soft key from the camera side
const ceil = new THREE.PointLight(0xffe9cc, 2.5, 6, 1.6); ceil.position.set(0.2, 2.5, -0.4); scene.add(ceil);

// ------------------------------------------------------------------ the kitchen
function canvasTex(w, h, draw, rep) { const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d')); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; if (rep) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(...rep); } return t; }
const woodTex = canvasTex(512, 512, g => { g.fillStyle = '#b07a4a'; g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 8; i++) { g.fillStyle = `hsl(28, ${38 + (i * 7) % 12}%, ${44 + (i * 13) % 10}%)`; g.fillRect(0, i * 64 + 1, 512, 62);
    for (let k = 0; k < 40; k++) { g.strokeStyle = 'rgba(80,45,20,0.18)'; g.beginPath(); const y = i * 64 + Math.random() * 62; g.moveTo(0, y); g.bezierCurveTo(170, y + 4, 340, y - 4, 512, y + 2); g.stroke(); } } }, [3, 3]);
const tileTex = canvasTex(512, 512, g => { g.fillStyle = '#d9d2c4'; g.fillRect(0, 0, 512, 512); g.fillStyle = '#f6f4ef';
  for (let y = 0; y < 8; y++) for (let x = 0; x < 4; x++) { const o = (y % 2) * 64; g.fillRect(x * 128 + o - 128 + 3, y * 64 + 3, 122, 58); g.fillRect(x * 128 + o + 3, y * 64 + 3, 122, 58); } }, [6, 2]);
const wallMat = new THREE.MeshStandardMaterial({ color: 0x9fc6b8, roughness: 0.9 });
const cabMat = new THREE.MeshStandardMaterial({ color: 0xf2efe8, roughness: 0.55 });
const topMat = new THREE.MeshStandardMaterial({ color: 0x3b3e44, roughness: 0.35, metalness: 0.05 });
const steel = new THREE.MeshStandardMaterial({ color: 0xc9ccd1, roughness: 0.25, metalness: 0.9 });
const kitchen = new THREE.Group(); scene.add(kitchen);
function box(w, h, d, mat, x, y, z, parent = kitchen, r = 0.012) { const m = new THREE.Mesh(r > 0 ? new RoundedBoxGeometry(w, h, d, 2, r) : new THREE.BoxGeometry(w, h, d), mat); m.position.set(x, y, z); m.castShadow = m.receiveShadow = true; parent.add(m); return m; }
{ const floor = new THREE.Mesh(new THREE.PlaneGeometry(12, 12).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ map: woodTex, roughness: 0.6 })); floor.receiveShadow = true; kitchen.add(floor);
  const back = new THREE.Mesh(new THREE.PlaneGeometry(12, 4), wallMat); back.position.set(0, 2, 1.25); back.rotation.y = Math.PI; back.receiveShadow = true; kitchen.add(back);
  const side = new THREE.Mesh(new THREE.PlaneGeometry(6, 4), wallMat); side.position.set(-2.6, 2, -1); side.rotation.y = Math.PI / 2; side.receiveShadow = true; kitchen.add(side);
  const splash = new THREE.Mesh(new THREE.PlaneGeometry(4.6, 0.6), new THREE.MeshStandardMaterial({ map: tileTex, roughness: 0.3 })); splash.position.set(0.1, 1.24, 1.245); splash.rotation.y = Math.PI; kitchen.add(splash);
  // back counter: base cabinets, worktop, upper cabinets, a window over the sink
  for (let i = 0; i < 6; i++) { const x = -2.1 + i * 0.62; if (x > -1.3 && x < -0.2) continue;
    box(0.6, 0.86, 0.6, cabMat, x, 0.45, 0.94); box(0.6, 0.6, 0.34, cabMat, x, 1.9, 1.07);
    box(0.14, 0.018, 0.02, steel, x, 0.8, 0.632, kitchen, 0.006); box(0.018, 0.14, 0.02, steel, x + 0.2, 1.68, 0.89, kitchen, 0.006); }
  box(1.1, 0.86, 0.6, cabMat, -0.75, 0.45, 0.94);
  box(4.6, 0.04, 0.64, topMat, 0.1, 0.9, 0.93);
  const winTex = canvasTex(256, 256, g => { const gr = g.createLinearGradient(0, 0, 0, 256); gr.addColorStop(0, '#9fd2ff'); gr.addColorStop(0.65, '#e6f5ff'); gr.addColorStop(0.66, '#7fb36a'); gr.addColorStop(1, '#5d8e4f'); g.fillStyle = gr; g.fillRect(0, 0, 256, 256); });
  const glass = new THREE.Mesh(new THREE.PlaneGeometry(1.0, 0.75), new THREE.MeshBasicMaterial({ map: winTex, toneMapped: false })); glass.position.set(-0.75, 1.75, 1.24); glass.rotation.y = Math.PI; kitchen.add(glass);
  for (const [w, h, x, y] of [[1.08, 0.05, -0.75, 2.14], [1.08, 0.05, -0.75, 1.36], [0.05, 0.8, -1.27, 1.75], [0.05, 0.8, -0.23, 1.75], [0.03, 0.75, -0.75, 1.75]]) box(w, h, 0.05, cabMat, x, y, 1.22);
  // the fridge
  box(0.8, 1.9, 0.72, steel, 2.2, 0.95, 0.88); box(0.03, 0.5, 0.04, new THREE.MeshStandardMaterial({ color: 0x222222 }), 1.86, 1.3, 0.5, kitchen, 0.01);
  // the island in front of him (top at 0.92)
  box(1.9, 0.86, 0.62, cabMat, 0, 0.45, -0.62); box(2.0, 0.045, 0.7, new THREE.MeshStandardMaterial({ color: 0xe8e2d6, roughness: 0.3 }), 0, 0.9, -0.62);
  // a plant and a mug for scale on the back counter
  const pot = box(0.16, 0.16, 0.16, new THREE.MeshStandardMaterial({ color: 0xd9643a, roughness: 0.7 }), 1.1, 1.0, 0.98);
  for (let i = 0; i < 7; i++) { const l = new THREE.Mesh(new THREE.SphereGeometry(0.07, 10, 8).scale(0.5, 1.4, 0.3), new THREE.MeshStandardMaterial({ color: 0x3f8f45, roughness: 0.7 }));
    l.position.set(1.1 + Math.cos(i) * 0.05, 1.17 + 0.03 * (i % 3), 0.98 + Math.sin(i) * 0.05); l.rotation.set(Math.cos(i * 2) * 0.5, i, Math.sin(i * 3) * 0.5); kitchen.add(l); }
  const mug = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.042, 0.1, 24), new THREE.MeshStandardMaterial({ color: 0xffd23f, roughness: 0.4 })); mug.position.set(0.6, 0.97, 1.0); mug.castShadow = true; kitchen.add(mug);
}
// trash can (step bin) at his right
const bin = new THREE.Group();
{ const body = new THREE.Mesh(new THREE.CylinderGeometry(0.17, 0.15, 0.55, 32, 1, true), steel); body.position.y = 0.275; bin.add(body);
  const bot = new THREE.Mesh(new THREE.CircleGeometry(0.15, 32).rotateX(-Math.PI / 2), steel); bot.position.y = 0.01; bin.add(bot);
  const inner = new THREE.Mesh(new THREE.CylinderGeometry(0.165, 0.145, 0.54, 32, 1, true), new THREE.MeshStandardMaterial({ color: 0x1b1d22, side: THREE.BackSide })); inner.position.y = 0.275; bin.add(inner);
  const lidP = new THREE.Group(); lidP.position.set(0, 0.555, 0.17); bin.add(lidP);
  const lid = new THREE.Mesh(new THREE.CylinderGeometry(0.175, 0.175, 0.03, 32), steel); lid.position.set(0, 0.0, -0.17); lidP.add(lid);
  bin.userData.lid = lidP; bin.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  bin.position.set(-1.06, 0, -0.08); scene.add(bin); }

// ------------------------------------------------------------------ bread: slice outline (square bottom, domed top), crust + crumb + mold + threads
const SW = 0.12, SH = 0.125;                                     // slice width/height (m)
function sliceOutline(n = 160) {
  const pts = [];
  for (let i = 0; i < n; i++) {
    const u = i / n; let x, y;
    if (u < 0.5) { const a = Math.PI * (u / 0.5); x = -Math.cos(a) * SW / 2 * (1 + 0.07 * Math.sin(a)); y = SH * 0.62 + Math.sin(a) * SH * 0.38; }   // the domed top
    else if (u < 0.6) { const k = (u - 0.5) / 0.1; x = SW / 2 - 0.004 * Math.sin(k * Math.PI); y = SH * 0.62 * (1 - k); }
    else if (u < 0.9) { const k = (u - 0.6) / 0.3; x = SW / 2 - SW * k; y = 0.004 * Math.sin(k * Math.PI * 3) * 0.3; }
    else { const k = (u - 0.9) / 0.1; x = -SW / 2 + 0.004 * Math.sin(k * Math.PI); y = SH * 0.62 * k; }
    pts.push(new THREE.Vector2(x, y));
  }
  return pts;
}
function bite(pts, bites) {                                        // scallop the outline where bites (circles) took bread away
  return pts.map(p => { let q = p.clone(); for (const [c, r] of bites) { const d = q.clone().sub(c); if (d.length() < r) q = c.clone().add(d.normalize().multiplyScalar(r)); } return q; });
}
const BITE = [[new THREE.Vector2(-0.04, 0.128), 0.032], [new THREE.Vector2(-0.072, 0.098), 0.028], [new THREE.Vector2(-0.012, 0.135), 0.024]];
const SPOT = new THREE.Vector2(0.025, 0.085);                     // the mold spot (on the face toward camera)
function sliceGeo(bitten, thick = 0.013, cut = 0) {
  let pts = sliceOutline(); if (bitten) pts = bite(pts, BITE);
  if (cut) pts = pts.map(p => new THREE.Vector2(p.x, Math.min(p.y, cut)));      // the top cut off along y = cut
  const g = new THREE.ExtrudeGeometry(new THREE.Shape(pts), { depth: thick, bevelEnabled: true, bevelThickness: 0.0025, bevelSize: 0.0025, bevelSegments: 2, curveSegments: 4 });
  g.translate(0, 0, -thick / 2); g.computeVertexNormals(); return g;
}
const BREAD_GLSL = `
float bh(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float bn(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f*f*(3.0-2.0*f); return mix(mix(bh(i), bh(i+vec2(1,0)), u.x), mix(bh(i+vec2(0,1)), bh(i+vec2(1,1)), u.x), u.y); }
float cell(vec2 p){ vec2 i = floor(p), f = fract(p); float d = 9.0; for (int y = -1; y <= 1; y++) for (int x = -1; x <= 1; x++) { vec2 g = vec2(x, y); vec2 o = vec2(bh(i + g), bh(i + g + 3.7)); d = min(d, length(g + o - f) * (0.6 + 0.8 * bh(i + g + 9.1))); } return d; }
float ridge(vec2 p){ return abs(bn(p) * 2.0 - 1.0); }`;
function breadMat(opts = {}) {
  const U = { uSpot: { value: SPOT.clone() }, uSpotR: { value: opts.spotR ?? 0.017 }, uThr: { value: 0 }, uXr: { value: 0 }, uMold: { value: opts.mold ?? 1 }, uSeed: { value: opts.seed ?? 0 }, uHeel: { value: opts.heel ?? 0 } };
  const m = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.85 });
  m.userData.u = U;
  m.onBeforeCompile = sh => {
    Object.assign(sh.uniforms, U);
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vL; varying vec3 vNL;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvL = position; vNL = normal;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', `#include <common>
varying vec3 vL; varying vec3 vNL; uniform vec2 uSpot; uniform float uSpotR, uThr, uXr, uMold, uSeed, uHeel;` + BREAD_GLSL)
      .replace('#include <color_fragment>', `#include <color_fragment>
  float face = smoothstep(0.75, 0.95, abs(vNL.z)) * (1.0 - uHeel * step(0.0, vL.z));
  vec2 p = vL.xy;
  // crumb: pale, airy, with little dark pits; crust: golden brown, darker toward the top
  float pits = 1.0 - smoothstep(0.08, 0.2, cell(p * 260.0 + uSeed));
  vec3 crumb = mix(vec3(0.95, 0.88, 0.72), vec3(0.88, 0.78, 0.6), bn(p * 90.0)) * (1.0 - 0.28 * pits);
  vec3 crust = mix(vec3(0.62, 0.36, 0.14), vec3(0.42, 0.22, 0.08), smoothstep(0.05, 0.13, vL.y)) * (0.9 + 0.2 * bn(p * 40.0 + vL.z * 30.0));
  vec3 c = mix(crust, crumb, face);
  // the mold spot (front face only): blue-green fuzz with a white rim, a few satellite dots
  float front = face;                                               // mold grows right through a slice: both faces
  float d = length(p - uSpot) / uSpotR + (bn(p * 220.0) - 0.5) * 0.5;
  float spot = (1.0 - smoothstep(0.75, 1.05, d)) * uMold;
  float rim = (1.0 - smoothstep(0.0, 0.25, abs(d - 0.95))) * uMold;
  float dots = 0.0; for (int i = 0; i < 5; i++) { vec2 o = vec2(bh(vec2(float(i), 3.0)) - 0.5, bh(vec2(float(i), 7.0)) - 0.5) * 0.06; dots = max(dots, 1.0 - smoothstep(0.0025, 0.004, length(p - uSpot - o))); }
  vec3 moldc = mix(vec3(0.16, 0.36, 0.3), vec3(0.42, 0.6, 0.5), bn(p * 500.0)) * (0.7 + 0.5 * bn(p * 1500.0));
  c = mix(c, vec3(0.92, 0.94, 0.9), rim * front * 0.8);
  c = mix(c, moldc, max(spot, dots * 0.9 * uMold) * front);
  // x-ray: the crumb dims, the threads (hyphae) glow, spreading out from the spot and through the whole slice
  float r = length(p - uSpot);
  // hyphae: threads radiating out from the spot, wandering, splitting into more branches further out
  vec2 q = p - uSpot; float ang = atan(q.y, q.x);
  float wob = (bn(vec2(r * 40.0, ang * 2.0 + uSeed)) - 0.5) * 0.9 + (bn(vec2(r * 120.0, ang * 5.0)) - 0.5) * 0.25;
  float n1 = 11.0, n2 = 23.0;
  float l1 = abs(sin((ang + wob) * n1 * 0.5)) * r;                 // distance-ish to the nearest main thread
  float l2 = abs(sin((ang + wob * 1.3 + 0.13) * n2 * 0.5)) * r;    // finer branches, only further out
  float th = max(1.0 - smoothstep(0.0012, 0.0024, l1), (1.0 - smoothstep(0.0009, 0.0018, l2)) * smoothstep(0.03, 0.06, r));
  th = max(th, 0.5 * (1.0 - smoothstep(0.0, 0.035, ridge(p * 160.0 + vec2(uSeed)))) * smoothstep(0.02, 0.05, r));
  float reach = 1.0 - smoothstep(uThr * 0.17, uThr * 0.17 + 0.012, r + (bn(p * 40.0) - 0.5) * 0.03);
  float thr = th * reach * face;
  c = mix(c, c * vec3(0.35, 0.33, 0.38), uXr);
  diffuseColor.rgb = c;
  vThreadGlow = thr * max(uXr, 0.15 * uThr);`)
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
  totalEmissiveRadiance += vec3(0.35, 1.0, 0.45) * vThreadGlow * 1.4;`)
      .replace('void main() {', 'float vThreadGlow = 0.0;\nvoid main() {');
  };
  m.customProgramCacheKey = () => 'bread';
  return m;
}
// the slice in his hand (whole, then bitten), the slice he cuts, the loaf he sniffs, the next slice (loop)
const sliceMat = breadMat({ seed: 1 });
const sliceWhole = new THREE.Mesh(sliceGeo(false), sliceMat), sliceBit = new THREE.Mesh(sliceGeo(true), sliceMat);
const sliceGrp = new THREE.Group(); sliceGrp.add(sliceWhole, sliceBit); scene.add(sliceGrp);
for (const m of [sliceWhole, sliceBit]) { m.castShadow = true; }
const cutMat = breadMat({ seed: 1 });
const CUTY = 0.066, KYAW = -55;
const sliceCutA = new THREE.Mesh(sliceGeo(true, 0.013, CUTY), cutMat);                   // the slice after the top is cut off
const cornerPiece = new THREE.Mesh(sliceGeo(true, 0.013), breadMat({ seed: 1 }));        // the corner (clipped to the cut side)
const cutPlane = new THREE.Plane(V(1, 0, 0), 0);
cornerPiece.material.clippingPlanes = [cutPlane]; scene.add(sliceCutA, cornerPiece);
for (const m of [sliceCutA, cornerPiece]) m.castShadow = true;
// the loaf (a row of slices pressed together, crust all round) on a cutting board on the island
const loafMat = breadMat({ seed: 5, spotR: 0.022, heel: 1 });
const loaf = new THREE.Mesh(sliceGeo(false, 0.24), loafMat); loaf.castShadow = true;
const loaf2 = new THREE.Mesh(sliceGeo(false, 0.24), breadMat({ seed: 9, spotR: 0.012, heel: 1 })); loaf2.castShadow = true;
loaf2.position.set(0.5, 0.977, -0.48); loaf2.quaternion.setFromEuler(new THREE.Euler(0, -Math.PI / 2 - 0.3, 0)); scene.add(loaf2);
const sliceBoard = new THREE.Mesh(sliceGeo(true), sliceMat); sliceBoard.castShadow = true; scene.add(sliceBoard);
const board = new THREE.Mesh(new RoundedBoxGeometry(0.42, 0.024, 0.3, 3, 0.008), new THREE.MeshStandardMaterial({ map: woodTex, roughness: 0.55 })); board.castShadow = board.receiveShadow = true;
board.position.set(-0.12, 0.937, -0.5); scene.add(board);
const BOARD_SLICE = V(-0.12, 0.957, -0.58);
const LOAF0 = { p: V(-0.3, 0.977, -0.44), q: new THREE.Quaternion().setFromEuler(new THREE.Euler(0, Math.PI / 2 - 0.25, 0)) };
loaf.position.copy(LOAF0.p); loaf.quaternion.copy(LOAF0.q); scene.add(loaf);
// the knife
const knife = new THREE.Group();
{ const bl = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.032, 0.0025), steel); bl.position.x = 0.12; knife.add(bl);
  const hd = new THREE.Mesh(new RoundedBoxGeometry(0.11, 0.024, 0.02, 2, 0.008), new THREE.MeshStandardMaterial({ color: 0x2a1c14, roughness: 0.5 })); hd.position.x = -0.035; knife.add(hd);
  knife.traverse(o => { if (o.isMesh) o.castShadow = true; }); scene.add(knife); }

// ------------------------------------------------------------------ puffs (spores, toxin, sneeze spray, crumbs): coloured soft billboards
const NP = 900;
const puffGeo = new THREE.InstancedBufferGeometry().copy(new THREE.PlaneGeometry(1, 1));
const pPos = new Float32Array(NP * 3), pSize = new Float32Array(NP), pAlpha = new Float32Array(NP), pSeed = new Float32Array(NP), pCol = new Float32Array(NP * 3);
for (let i = 0; i < NP; i++) pSeed[i] = hash1(i * 3.91);
for (const [k, a, n] of [['iPos', pPos, 3], ['iSize', pSize, 1], ['iAlpha', pAlpha, 1], ['iSeed', pSeed, 1], ['iCol', pCol, 3]]) puffGeo.setAttribute(k, new THREE.InstancedBufferAttribute(a, n));
puffGeo.instanceCount = NP;
const puffMat = new THREE.ShaderMaterial({
  transparent: true, depthWrite: false,
  vertexShader: `attribute vec3 iPos, iCol; attribute float iSize, iAlpha, iSeed; varying vec2 vUv; varying float vA, vS; varying vec3 vC;
    void main(){ vUv = position.xy; vA = iAlpha; vS = iSeed; vC = iCol;
      vec4 mv = modelViewMatrix * vec4(iPos, 1.0); float a = iSeed * 6.283; mat2 r = mat2(cos(a), -sin(a), sin(a), cos(a));
      mv.xy += r * position.xy * iSize; gl_Position = projectionMatrix * mv; }`,
  fragmentShader: `varying vec2 vUv; varying float vA, vS; varying vec3 vC;
    float h2(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5); }
    float n2(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f*f*(3.0-2.0*f); return mix(mix(h2(i), h2(i+vec2(1,0)), u.x), mix(h2(i+vec2(0,1)), h2(i+vec2(1,1)), u.x), u.y); }
    void main(){ vec2 p = vUv * 2.0; float r = length(p); float n = n2(p * 2.5 + vS * 17.0);
      float a = (1.0 - smoothstep(0.3, 1.0, r + (n - 0.5) * 0.4)) * vA; if (a < 0.003) discard;
      gl_FragColor = vec4(vC * (0.85 + 0.3 * (vUv.y + 0.5)), a);
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
    }`,
});
const puffs = new THREE.Mesh(puffGeo, puffMat); puffs.frustumCulled = false; puffs.renderOrder = 6; scene.add(puffs);
let pN = 0;
function puff(p, size, alpha, col) { if (pN >= NP || alpha < 0.004) return; pPos.set([p.x, p.y, p.z], pN * 3); pCol.set([col.r, col.g, col.b], pN * 3); pSize[pN] = size; pAlpha[pN] = alpha; pN++; }
function puffsDone() { for (let i = pN; i < NP; i++) pAlpha[i] = 0; for (const k of ['iPos', 'iSize', 'iAlpha', 'iCol']) puffGeo.attributes[k].needsUpdate = true; pN = 0; }
const C_SPORE = new THREE.Color(0.45, 0.85, 0.5), C_TOX = new THREE.Color(0.7, 0.3, 0.95), C_SPRAY = new THREE.Color(0.85, 0.92, 1.0), C_ACID = new THREE.Color(0.85, 1.0, 0.35);

// ------------------------------------------------------------------ the guy (t-shirt and jeans); x-ray organs in his body
const G = await loadGuy(THREE, '/char/guy', {});
scene.add(G.root); G.root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
const HIP = V(0.0, 0.95, 0.0);
const GUYMATS = new Set(); G.root.traverse(o => { if (o.isMesh) (Array.isArray(o.material) ? o.material : [o.material]).forEach(m => GUYMATS.add(m)); });
for (const m of GUYMATS) { m.transparent = true; m.userData.op0 = m.opacity ?? 1; }
function ghost(k) {                                       // x-ray: his body goes see-through (blue-ish), organs show
  for (const m of GUYMATS) { m.opacity = lerp(m.userData.op0, m === G.mat.shirt ? 0.1 : 0.17, k); m.depthWrite = k < 0.02; }
}
// rash (allergy): red blotches on skin and face, grown with uRash
const RASH = { uRash: { value: 0 } };
for (const key of ['skin', 'face']) {
  const m = G.mat[key]; const prev = m.onBeforeCompile;
  m.onBeforeCompile = (sh, r) => { prev && prev(sh, r); Object.assign(sh.uniforms, RASH);
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vRashP;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvRashP = position;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', `#include <common>
varying vec3 vRashP; uniform float uRash;
float rh(vec3 p){ return fract(sin(dot(p, vec3(12.9898, 78.233, 37.719))) * 43758.5453); }
float rn(vec3 p){ vec3 i = floor(p), f = fract(p); vec3 u = f*f*(3.0-2.0*f);
  return mix(mix(mix(rh(i), rh(i+vec3(1,0,0)), u.x), mix(rh(i+vec3(0,1,0)), rh(i+vec3(1,1,0)), u.x), u.y), mix(mix(rh(i+vec3(0,0,1)), rh(i+vec3(1,0,1)), u.x), mix(rh(i+vec3(0,1,1)), rh(i+vec3(1,1,1)), u.x), u.y), u.z); }`)
      .replace('#include <color_fragment>', `#include <color_fragment>
  { float rn0 = rn(vRashP * 60.0) * 0.65 + rn(vRashP * 160.0) * 0.35;
    float rn1 = rn(vRashP * 110.0 + 5.0);
    float ra = smoothstep(0.86 - uRash * 0.2, 0.89 - uRash * 0.2, rn0 * 0.7 + rn1 * 0.3) * step(0.001, uRash) * step(1.2, vRashP.y);
    float halo = smoothstep(0.8 - uRash * 0.2, 0.88 - uRash * 0.2, rn0 * 0.7 + rn1 * 0.3) * step(0.001, uRash) * step(1.2, vRashP.y);
    diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.9, 0.42, 0.38), halo * 0.45);
    diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.86, 0.2, 0.2), ra * 0.85); }`);
  };
  const ck = m.customProgramCacheKey.bind(m); m.customProgramCacheKey = () => ck() + '-rash'; m.needsUpdate = true;
}
// organs: placed in rest space, then parented to the spine bones so they ride with him
const organMat = c => new THREE.MeshPhysicalMaterial({ color: c, roughness: 0.35, clearcoat: 0.6, transparent: true, opacity: 0.92, depthTest: true });
function attach(obj, boneName) { G.reset(); G.root.updateMatrixWorld(true); obj.updateMatrixWorld(true); obj.applyMatrix4(G.bones[boneName].matrixWorld.clone().invert()); G.bones[boneName].add(obj); }
const organs = new THREE.Group();
const stomach = new THREE.Group();
// one J-shaped stomach (fundus, body, narrowing pylorus); the acid is the SAME shape shrunk inward and cut flat at its fill level,
// so it always sits inside the stomach wall, and the bread chunks float on that surface
const ST_CURVE = new THREE.CatmullRomCurve3([V(0.005, 1.27, 0.0), V(-0.02, 1.235, -0.02), V(-0.06, 1.19, -0.035), V(-0.07, 1.13, -0.04), V(-0.04, 1.085, -0.045), V(0.01, 1.08, -0.04), V(0.05, 1.1, -0.035)]);
const ST_PTS = ST_CURVE.getSpacedPoints(60);
const stRad = k => 0.035 * (1 + 0.75 * Math.sin(Math.PI * clamp((k / 60 - 0.12) / 0.7, 0, 1)));
function stomachGeo(rf) {
  const fr = ST_CURVE.computeFrenetFrames(60, false), seg = 28, pos = [], idx = [];
  for (let k = 0; k <= 60; k++) { const c = ST_PTS[k], r = stRad(k) * rf;
    for (let j = 0; j <= seg; j++) { const a = j / seg * Math.PI * 2; const v = c.clone().addScaledVector(fr.normals[k], Math.cos(a) * r).addScaledVector(fr.binormals[k], Math.sin(a) * r); pos.push(v.x, v.y, v.z); } }
  for (let k = 0; k < 60; k++) for (let j = 0; j < seg; j++) { const a = k * (seg + 1) + j, b = a + seg + 1; idx.push(a, b, a + 1, b, b + 1, a + 1); }
  for (const [k, sgn] of [[0, 1], [60, -1]]) { const ci = pos.length / 3; pos.push(ST_PTS[k].x, ST_PTS[k].y, ST_PTS[k].z);   // close the ends
    for (let j = 0; j < seg; j++) { const a = k * (seg + 1) + j; sgn > 0 ? idx.push(ci, a + 1, a) : idx.push(ci, a, a + 1); } }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setIndex(idx); g.computeVertexNormals(); return g;
}
{ const sm_ = new THREE.Mesh(stomachGeo(1), organMat(0xf08a8a)); sm_.material.side = THREE.DoubleSide; sm_.material.opacity = 0.5; sm_.renderOrder = 5; stomach.add(sm_);
  const eso = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3([V(0, 1.56, -0.03), V(0, 1.45, -0.0), V(0.0, 1.35, 0.01), V(0.005, 1.27, 0.0)]), 20, 0.011, 12, false), organMat(0xe57b7b)); eso.material.opacity = 0.6; stomach.add(eso);
  organs.add(stomach); }
const FILL_Y = 1.112;                                   // acid fill level (rest space)
const acidPlane = new THREE.Plane(V(0, -1, 0), FILL_Y);
const acid = new THREE.Mesh(stomachGeo(0.86), new THREE.MeshStandardMaterial({ color: 0xb8ff4a, emissive: 0x5a9a10, emissiveIntensity: 0.9, transparent: true, opacity: 0.8, roughness: 0.2, side: THREE.DoubleSide, clippingPlanes: [acidPlane] }));
acid.renderOrder = 4; organs.add(acid);
// the acid's flat top surface: a disc clipped to the inside of the shrunk stomach is hard, so use many small puffs instead (see update)
const BUB = [];                                         // bubble start points: inside the acid, below the surface
for (let i = 0; i < 400 && BUB.length < 40; i++) { const k = Math.floor(hash1(i * 1.7) * 61), c = ST_PTS[k], r = stRad(k) * 0.6;
  const q = c.clone().add(V((hash1(i * 3.1) - 0.5) * 2 * r, (hash1(i * 5.3) - 0.5) * 2 * r, (hash1(i * 7.9) - 0.5) * 2 * r)); if (q.y < FILL_Y - 0.012) BUB.push(q); }
const chunks = [];                                      // swallowed bread chunks with mold cells, floating on the acid
const cellMat = new THREE.MeshStandardMaterial({ color: 0x2f8f55, emissive: 0x0f4020, roughness: 0.5 });
const FLOAT_AT = [];
{ const inside = ST_PTS.map((c, k) => [c, k]).filter(([c]) => c.y < FILL_Y - 0.01);
  for (let i = 0; i < 4; i++) { const [c, k] = inside[Math.floor((i + 0.5) / 4 * inside.length)]; FLOAT_AT.push(V(c.x, FILL_Y - 0.004, c.z)); } }
for (let i = 0; i < 4; i++) { const ch = new THREE.Group(); const c = new THREE.Mesh(new RoundedBoxGeometry(0.02, 0.014, 0.016, 2, 0.005), new THREE.MeshStandardMaterial({ color: 0xe8d4a8, roughness: 0.8 })); ch.add(c);
  for (let k = 0; k < 7; k++) { const sp = new THREE.Mesh(new THREE.IcosahedronGeometry(0.0032, 1), cellMat); sp.position.set((hash1(i * 9 + k) - 0.5) * 0.018, 0.007, (hash1(i * 3 + k) - 0.5) * 0.014); ch.add(sp); }
  ch.position.copy(FLOAT_AT[i]); ch.renderOrder = 6; organs.add(ch); chunks.push(ch); }
const lungs = new THREE.Group();
for (const s of [1, -1]) { const l = new THREE.Mesh(new THREE.SphereGeometry(1, 28, 20), organMat(0xf2a3b0)); l.scale.set(0.06, 0.11, 0.06); l.position.set(0.07 * s, 1.33, 0.0); l.material.opacity = 0.5; lungs.add(l); }
{ const tr = new THREE.Mesh(new THREE.CylinderGeometry(0.009, 0.009, 0.16, 12), organMat(0xf3c1c8)); tr.position.set(0, 1.47, -0.01); lungs.add(tr); }
organs.add(lungs);
attach(organs, 'chest');
organs.visible = false; organs.traverse(o => { if (o.isMesh) o.renderOrder = 4; });
// mouth position (follows the head)
const MOUTH = new THREE.Object3D(); MOUTH.position.set(0, G.man.mouthY, (G.man.mouthZ ?? -0.1) - 0.005); attach(MOUTH, 'head');
const NOSE = new THREE.Object3D(); NOSE.position.set(0, G.man.headC[1] - 0.035, -0.125); attach(NOSE, 'head');
G.reset();
// ------------------------------------------------------------------ grips: a prop's pose decides exactly where the hand is and how it is turned
// Each grip maps prop axes onto the hand's own rest axes (u = wrist->fingers, n = out of the palm, w = across the knuckles toward the pinky)
// and puts a point of the prop at a point of the palm. Then: hand pose = prop pose * grip^-1, the arm reaches the wrist by IK.
G.root.updateMatrixWorld(true);
const HR = {}; for (const S of ['R', 'L']) { const hb = G.man.hands[S], af = G.REST['farm' + S].axis;
  const wp = V(...hb.w).sub(af.clone().multiplyScalar(af.dot(V(...hb.w)))).normalize(), np = V(...hb.n).sub(af.clone().multiplyScalar(af.dot(V(...hb.n)))).normalize();
  HR[S] = { q: G.bones['hand' + S].getWorldQuaternion(new THREE.Quaternion()), p: G.bones['hand' + S].getWorldPosition(new THREE.Vector3()), u: V(...hb.u), n: V(...hb.n), w: V(...hb.w),
    wf: wp, nf: np }; }                                   // wf/nf: flex and side-bend axes, square to the forearm
function basisQ(x, y) { x = x.clone().normalize(); y = y.clone().sub(x.clone().multiplyScalar(x.dot(y))).normalize(); const z = new THREE.Vector3().crossVectors(x, y);
  return new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(x, y, z)); }
function makeGrip(S, ax, palm, L) {                     // ax(h) -> [propX, propY] in hand-rest vectors; palm = [u, n, w] offsets (m); L = prop-local point
  const h = HR[S], [X, Y] = ax(h);
  const qoff = h.q.clone().invert().multiply(basisQ(X, Y));
  const P0 = h.p.clone().addScaledVector(h.u, palm[0]).addScaledVector(h.n, palm[1]).addScaledVector(h.w, palm[2]);
  return { S, qoff, pOff: P0.sub(h.p).applyQuaternion(h.q.clone().invert()), L: L.clone() };
}
// wrist limits (hand relative to the forearm): forearm roll (pronation/supination) +-80 deg from rest, wrist flex/extension +-60,
// side bend +-25. A grip that would need more is clamped, and the prop follows the hand, so the back of the hand never flips over.
const WLIM = { twist: 80, flex: 60, dev: 25 };
const WRIST_LOG = {};
function twistOf(q, a) { const p = a.clone().multiplyScalar(a.x * q.x + a.y * q.y + a.z * q.z); const t = new THREE.Quaternion(p.x, p.y, p.z, q.w); return t.lengthSq() < 1e-12 ? new THREE.Quaternion() : t.normalize(); }
function wristAngles(S) {                               // hand vs forearm: roll, flex/extension, side bend (deg)
  const ha = G.bones['hand' + S], af = G.REST['farm' + S].axis.clone(), h = HR[S];
  const q = ha.quaternion.clone(), tw = twistOf(q, af), sw = q.clone().multiply(tw.clone().invert());
  let ta = 2 * Math.atan2(V(tw.x, tw.y, tw.z).dot(af), tw.w) / D2R; ta = ((ta + 540) % 360) - 180;
  const swA = 2 * Math.acos(clamp(Math.abs(sw.w), 0, 1)), swAx = swA > 1e-6 ? V(sw.x, sw.y, sw.z).normalize().multiplyScalar(Math.sign(sw.w) || 1) : V(1, 0, 0);
  const rv = swAx.multiplyScalar(swA / D2R);
  return { ta, fx: rv.dot(h.wf), dv: rv.dot(h.nf) };
}
function wristCost(S) { const a = wristAngles(S); return Math.max(0, Math.abs(a.ta) - WLIM.twist) * 2 + Math.max(0, Math.abs(a.fx) - WLIM.flex) * 2 + Math.max(0, Math.abs(a.dv) - WLIM.dev) * 2 + 0.15 * (Math.abs(a.ta) + Math.abs(a.fx) + Math.abs(a.dv)); }
function clampWrist(S) {
  const ha = G.bones['hand' + S], af = G.REST['farm' + S].axis.clone(), h = HR[S];
  const q = ha.quaternion.clone(), tw = twistOf(q, af), sw = q.clone().multiply(tw.clone().invert());
  let ta = 2 * Math.atan2(V(tw.x, tw.y, tw.z).dot(af), tw.w) / D2R; ta = ((ta + 540) % 360) - 180;
  const swA = 2 * Math.acos(clamp(Math.abs(sw.w), 0, 1)), swAx = swA > 1e-6 ? V(sw.x, sw.y, sw.z).normalize().multiplyScalar(Math.sign(sw.w) || 1) : V(1, 0, 0);
  const rv = swAx.multiplyScalar(swA / D2R);                                        // rotation vector (deg) of the swing
  const fx = rv.dot(h.wf), dv = rv.dot(h.nf);
  const L = WRIST_LOG[S] = WRIST_LOG[S] || { twist: 0, flex: 0, dev: 0 };
  L.twist = Math.max(L.twist, Math.abs(ta)); L.flex = Math.max(L.flex, Math.abs(fx)); L.dev = Math.max(L.dev, Math.abs(dv));
  const ta2 = clamp(ta, -WLIM.twist, WLIM.twist), fx2 = clamp(fx, -WLIM.flex, WLIM.flex), dv2 = clamp(dv, -WLIM.dev, WLIM.dev);
  if (ta2 === ta && fx2 === fx && dv2 === dv) return;
  const rv2 = h.wf.clone().multiplyScalar(fx2).addScaledVector(h.nf, dv2);
  const sw2 = rv2.length() > 1e-6 ? new THREE.Quaternion().setFromAxisAngle(rv2.clone().normalize(), rv2.length() * D2R) : new THREE.Quaternion();
  ha.quaternion.copy(sw2.multiply(new THREE.Quaternion().setFromAxisAngle(af, ta2 * D2R)));
  G.bones['farmTwist' + S].quaternion.copy(twistOf(ha.quaternion, af));
  G.root.updateMatrixWorld(true);
}
function untwistSafe() {                                // guy3d's untwist isn't idempotent (a 2nd call drops the twist already split off): fold it back first
  for (const S of ['R', 'L']) { const ua = G.bones['uarm' + S], ut = G.bones['uarmTwist' + S]; ua.quaternion.multiply(ut.quaternion); ut.quaternion.identity(); }
  G.untwist();
}
function wristLocal(S, ta, fx, dv) {                    // hand rotation relative to the forearm from roll / flex / side bend (deg)
  const h = HR[S], af = G.REST['farm' + S].axis;
  const rv = h.wf.clone().multiplyScalar(fx).addScaledVector(h.nf, dv);
  const sw = rv.length() > 1e-6 ? new THREE.Quaternion().setFromAxisAngle(rv.clone().normalize(), rv.length() * D2R) : new THREE.Quaternion();
  return sw.multiply(new THREE.Quaternion().setFromAxisAngle(af, ta * D2R));
}
// ------------------------------------------------------------------ the human arm: every hold is solved over REAL joint ranges
// shoulder: forward raise -50..170, side raise -25..170 (minus = across the body), upper-arm roll -60..60
// elbow: a hinge, 0..145 (never bends backward or sideways); forearm roll (palm down / palm up) -80..80
// wrist: bend -65..70, side bend -25..25.  The solver finds the comfortable pose that puts the palm on the target, with the
// hand turned as close as these limits allow to how the prop wants to sit, and keeps the arm out of his own body.
if (Q.get('nmark')) { const mk = new THREE.Mesh(new THREE.SphereGeometry(0.012, 12, 8), new THREE.MeshBasicMaterial({ color: 0xff0000 }));
  mk.position.copy(HR.R.u.clone().multiplyScalar(0.06).add(HR.R.n.clone().multiplyScalar(0.05))); G.bones.handR.add(mk);
  const mk2 = new THREE.Mesh(new THREE.SphereGeometry(0.01, 12, 8), new THREE.MeshBasicMaterial({ color: 0x0000ff })); mk2.position.copy(HR.R.u.clone().multiplyScalar(0.06).add(HR.R.w.clone().multiplyScalar(0.05))); G.bones.handR.add(mk2); }
const ARM_LIM = { flex: [-50, 170], abd: [-25, 170], rot: [-60, 60], el: [0, 145], pro: [-80, 80], wf: [-65, 70], wd: [-25, 25] };
const ARM_KEYS = ['flex', 'abd', 'rot', 'el', 'pro', 'wf', 'wd'];
const ARMREST = {};
for (const S of ['R', 'L']) {
  const hd = n => G.bones[n + S].userData.head.clone();
  const a0 = G.REST['uarm' + S].axis.clone(), af = G.REST['farm' + S].axis.clone();
  ARMREST[S] = { s: S === 'R' ? 1 : -1, a0, af, offUE: hd('farm').sub(hd('uarm')), offFW: hd('hand').sub(hd('farm')),
    hinge: new THREE.Vector3().crossVectors(af, V(0, 0, -1)).normalize() };
}
const qAA = (ax, deg) => new THREE.Quaternion().setFromAxisAngle(ax, deg * D2R);
function armQuats(S, x) {                                // joint angles -> local bone rotations
  const A = ARMREST[S], h = HR[S];
  const rv = V(x.flex, 0, A.s * x.abd); const ang = rv.length();
  const d = ang > 1e-6 ? V(0, -1, 0).applyQuaternion(qAA(rv.clone().normalize(), ang)) : V(0, -1, 0);
  const Lu = new THREE.Quaternion().setFromUnitVectors(A.a0, d).multiply(qAA(A.a0, x.rot));
  const Lf = qAA(A.hinge, x.el).multiply(qAA(A.af, x.pro));
  const rw = h.wf.clone().multiplyScalar(x.wf).addScaledVector(h.nf, x.wd);
  const Lh = rw.length() > 1e-6 ? qAA(rw.clone().normalize(), rw.length()) : new THREE.Quaternion();
  return { Lu, Lf, Lh };
}
function armFK(S, x, Qp, Sw) {                           // -> world elbow, wrist, hand rotation
  const A = ARMREST[S], { Lu, Lf, Lh } = armQuats(S, x);
  const Qu = Qp.clone().multiply(Lu), Qf = Qu.clone().multiply(Lf), Qh = Qf.clone().multiply(Lh);
  const el = Sw.clone().add(A.offUE.clone().applyQuaternion(Qu)), wr = el.clone().add(A.offFW.clone().applyQuaternion(Qf));
  return { el, wr, Qh, Qu };
}
function torsoInside(p) {                                // how deep a point is inside his trunk (m, 0 = outside); a soft elliptic column
  const c = G.bones.chest.getWorldPosition(new THREE.Vector3()), sp = G.bones.spine1.getWorldPosition(new THREE.Vector3());
  const hq = G.root.quaternion, lx = V(1, 0, 0).applyQuaternion(hq), lz = V(0, 0, 1).applyQuaternion(hq);
  if (p.y > c.y + 0.22 || p.y < sp.y - 0.2) return 0;
  const q = p.clone().sub(c); const ex = q.dot(lx) / 0.16, ez = (q.dot(lz) - 0.01) / 0.12;
  const r = Math.hypot(ex, ez); return r < 1 ? (1 - r) * 0.12 : 0;
}
function armSolve(S, palmT, qHs, pOff) {                 // palm target (world), allowed hand rotations, palm offset (hand-local)
  const ua = G.bones['uarm' + S]; G.root.updateMatrixWorld(true);
  const Qp = ua.parent.getWorldQuaternion(new THREE.Quaternion()), Sw = ua.getWorldPosition(new THREE.Vector3());
  const cost = x => {
    const f = armFK(S, x, Qp, Sw);
    const palm = f.wr.clone().add(pOff.clone().applyQuaternion(f.Qh));
    let c = palm.distanceToSquared(palmT) / 2.5e-5;                                 // 5 mm off = 1: contact comes first
    if (qHs && qHs.length) { let best = 1e9; for (const [q, pen] of qHs) best = Math.min(best, (2 * Math.acos(clamp(Math.abs(f.Qh.dot(q)), 0, 1)) / D2R / 12) ** 2 + pen); c += best; }
    for (const k of ARM_KEYS) { const [lo, hi] = ARM_LIM[k], mid = k === 'el' ? 40 : k === 'flex' ? 20 : k === 'abd' ? 15 : 0; c += 0.25 * ((x[k] - mid) / (hi - lo)) ** 2 * 4; }   // comfort
    for (const p of [f.el, f.wr, f.el.clone().lerp(f.wr, 0.5)]) { const ins = torsoInside(p); c += (ins / 0.01) ** 2; }   // not through his body
    if (f.el.y > Sw.y + 0.05) c += ((f.el.y - Sw.y - 0.05) / 0.02) ** 2;          // elbows don't fly up
    return c;
  };
  const clampX = x => { for (const k of ARM_KEYS) x[k] = clamp(x[k], ARM_LIM[k][0], ARM_LIM[k][1]); return x; };
  const seeds = [{ flex: 30, abd: 15, rot: 0, el: 90, pro: 0, wf: 0, wd: 0 }, { flex: 60, abd: 10, rot: 20, el: 60, pro: 40, wf: 0, wd: 0 },
    { flex: 70, abd: 30, rot: -20, el: 110, pro: -40, wf: 10, wd: 0 }, { flex: 20, abd: 40, rot: 30, el: 40, pro: 70, wf: -20, wd: 0 }, { flex: 100, abd: 20, rot: 0, el: 120, pro: 0, wf: 0, wd: 0 },
    { flex: 45, abd: 5, rot: 0, el: 135, pro: 60, wf: 20, wd: 0 }, { flex: 60, abd: 15, rot: 30, el: 130, pro: -60, wf: -20, wd: 0 }, { flex: 35, abd: 20, rot: -30, el: 140, pro: 0, wf: 40, wd: 0 }];
  let best = null;
  for (const s0 of seeds) {
    let x = clampX({ ...s0 }), cx = cost(x);
    for (let step = 24; step >= 0.75; step /= 2) {
      let improved = true, guard = 0;
      while (improved && guard++ < 12) { improved = false;
        for (const k of ARM_KEYS) for (const sg of [1, -1]) { const y = clampX({ ...x, [k]: x[k] + sg * step }); const cy = cost(y); if (cy < cx - 1e-9) { x = y; cx = cy; improved = true; } } }
    }
    if (!best || cx < best.c) best = { x, c: cx };
  }
  return best;
}
function applyArm(S, x, w = 1) {
  const { Lu, Lf, Lh } = armQuats(S, x);
  const b = n => G.bones[n + S];
  b('uarm').quaternion.slerp(Lu, w); b('uarmTwist').quaternion.slerp(new THREE.Quaternion(), w);
  b('farm').quaternion.slerp(Lf, w); b('farmTwist').quaternion.slerp(new THREE.Quaternion(), w); b('hand').quaternion.slerp(Lh, w);
  G.root.updateMatrixWorld(true); untwistSafe();
}
const ARM_LOG = {};
function holdProp(gr, qP, posP, pole, w = 1, free = []) {   // put the hand on the prop: solved over real joint ranges (pole is ignored now)
  if (w < 0.001) return;
  const S = gr.S;
  const qHs = [];
  const angs = r => { const o = []; for (let a = -r; a <= r + 1e-6; a += Math.max(5, r / 4)) o.push(a); return o; };
  const f0 = free[0] || [V(0, 1, 0), 0], f1 = free[1] || [V(1, 0, 0), 0];
  for (const a0 of angs(f0[1])) for (const a1 of angs(f1[1])) {
    const R_ = qAA(f0[0], a0).multiply(qAA(f1[0], a1));
    qHs.push([R_.multiply(qP).multiply(gr.qoff.clone().invert()), 0.02 * (Math.abs(a0) + Math.abs(a1))]); }
  const palmW = posP.clone().add(gr.L.clone().applyQuaternion(qP));
  // undo any twist split so the solver starts from a clean chain
  for (const n of ['uarmTwist', 'farmTwist']) G.bones[n + S].quaternion.identity();
  const sol = armSolve(S, palmW, qHs, gr.pOff);
  const L = ARM_LOG[S] = ARM_LOG[S] || { cost: 0 }; L.cost = Math.max(L.cost, sol.c); L.x = sol.x;
  applyArm(S, sol.x, w);
}
function propFromHand(gr, obj) {                         // the prop rides in the hand (after the arm is posed)
  const qH = G.bones['hand' + gr.S].getWorldQuaternion(new THREE.Quaternion()), hp = G.bones['hand' + gr.S].getWorldPosition(new THREE.Vector3());
  obj.quaternion.copy(qH).multiply(gr.qoff);
  obj.position.copy(hp.add(gr.pOff.clone().applyQuaternion(qH))).sub(gr.L.clone().applyQuaternion(obj.quaternion));
}
// knife: handle across the palm, blade out past the index finger, edge on the palm side; handle centre at local (-0.035, 0, 0)
const GR_KNIFE = makeGrip('R', h => [h.w.clone().negate(), h.n.clone().negate()], [0.052, 0.024, 0.004], V(-0.04, 0, 0));
// slice: pinched by its bottom crust between thumb and fingers, front (mold) face away from the palm
const SLICE_GRIPS = [
  makeGrip('R', h => [h.w.clone(), h.u.clone()], [0.078, 0.016, 0.0], V(0.012, 0.014, 0)),                    // fingers up behind... (0)
  makeGrip('R', h => [h.w.clone().negate(), h.u.clone()], [0.07, 0.024, 0.0], V(-0.01, 0.02, 0.0065)),         // (1) fingers flat on its back, thumb on the front
  makeGrip('R', h => [h.u.clone(), h.w.clone().negate()], [0.07, 0.016, 0.0], V(-0.045, 0.03, 0)),            // (2) held from the side, fingers across
  makeGrip('R', h => [h.u.clone().negate(), h.w.clone()], [0.07, 0.016, 0.0], V(0.045, 0.03, 0)),             // (3)
  makeGrip('R', h => [h.w.clone(), h.n.clone()], [0.075, 0.0, 0.0], V(0.0, 0.0, 0.0)),                       // (4) bottom crust on the fingers (slice standing on the hand)
  makeGrip('R', h => [h.w.clone(), h.u.clone()], [0.14, 0.014, 0.0], V(0.008, 0.012, -0.0065)),              // (5) pinched by the bottom crust at the fingertips, palm toward him, knuckles to the camera
];
let GR_SLICE = SLICE_GRIPS[5];
// loaf held up in both hands, palms on its sides, fingers up
const LOAF_GRIPS = [
  makeGrip('R', h => [h.n.clone(), h.u.clone()], [0.05, 0.012, 0.0], V(-0.068, 0.05, 0.0)),          // (0) palm on its side, fingers up
  makeGrip('R', h => [h.n.clone(), h.u.clone().negate()], [0.05, 0.012, 0.0], V(-0.068, 0.05, 0.0)),  // (1) palm on its side, fingers down
  makeGrip('R', h => [h.n.clone(), h.w.clone()], [0.05, 0.012, 0.0], V(-0.068, 0.05, 0.0)),           // (2) palm on its side, fingers along it
  makeGrip('R', h => [h.n.clone(), h.w.clone().negate()], [0.05, 0.012, 0.0], V(-0.068, 0.05, 0.0)),  // (3)
  makeGrip('R', h => [h.w.clone(), h.n.clone()], [0.06, 0.012, 0.0], V(0.0, 0.0, 0.03)),              // (4) sitting on the palm, from below
  makeGrip('R', h => [h.u.clone(), h.n.clone()], [0.06, 0.012, 0.0], V(0.0, 0.0, 0.03)),              // (5)
];
let GR_LOAF_R = LOAF_GRIPS[5];
const GR_LOAF_L = makeGrip('L', h => [h.n.clone().negate(), h.u.clone()], [0.05, 0.012, 0.0], V(0.068, 0.05, 0.0));
// loaf grabbed from above with the left hand (palm on top, fingers along it)
const GR_LOAF_TOP = makeGrip('L', h => [h.w.clone().negate(), h.n.clone().negate()], [0.06, 0.014, 0.0], V(0, 0.125, -0.02));
// left hand flat on the slice on the board (palm on the face, fingers forward)
const GR_FLAT_L = makeGrip('L', h => [h.w.clone(), h.u.clone().negate()], [0.065, 0.012, 0.0], V(-0.025, 0.03, -0.008));
const GR_NECK = makeGrip('L', h => [h.n.clone(), h.u.clone()], [0.135, 0.0, 0.0], V(0, 0, 0));          // fingertips on his neck
const GR_FLAT_R = makeGrip('R', h => [h.w.clone().negate(), h.u.clone().negate()], [0.065, 0.012, 0.0], V(0, 0, 0));   // (used for the neck scratch)

// ------------------------------------------------------------------ rig helpers (same axes as quick.js / av.js)
const LIMITS = {
  spine1: [[-30, 25], [-25, 25], [-20, 20]], spine2: [[-30, 25], [-25, 25], [-20, 20]], chest: [[-25, 20], [-25, 25], [-15, 15]],
  neck: [[-35, 35], [-55, 55], [-25, 25]], head: [[-30, 30], [-40, 40], [-20, 20]],
  uarmR: [[-60, 170], [-80, 80], [-40, 175]], uarmL: [[-60, 170], [-80, 80], [-175, 40]],
  farmR: [[0, 145], [-80, 80], [-20, 20]], farmL: [[0, 145], [-80, 80], [-20, 20]],
  handR: [[-60, 60], [-30, 30], [-60, 60]], handL: [[-60, 60], [-30, 30], [-60, 60]],
  thighR: [[-30, 120], [-40, 40], [-25, 45]], thighL: [[-30, 120], [-40, 40], [-45, 25]],
  shinR: [[-150, 0], [-10, 10], [-5, 5]], shinL: [[-150, 0], [-10, 10], [-5, 5]],
  footR: [[-45, 30], [-15, 15], [-15, 15]], footL: [[-45, 30], [-15, 15], [-15, 15]],
};
function softc(x, lo, hi, knee = 6) { if (x > hi - knee) return hi - knee + knee * Math.tanh((x - (hi - knee)) / knee); if (x < lo + knee) return lo + knee - knee * Math.tanh(((lo + knee) - x) / knee); return x; }
const FINGERS = ['index', 'middle', 'ring', 'pinky'];
function curl(p, S, c, th = c) { for (const f of FINGERS) { p[f + '1' + S] = [0, 0, (S === 'R' ? -1 : 1) * c * 0.9]; p[f + '2' + S] = [0, 0, (S === 'R' ? -1 : 1) * c]; } p['thumb1' + S] = [0, 0, (S === 'R' ? -1 : 1) * th * 0.4]; return p; }
function eul(p, n) { return p[n] || [0, 0, 0]; }
function mixPose(a, b, k) { const o = {}; for (const n of new Set([...Object.keys(a), ...Object.keys(b)])) { const x = eul(a, n), y = eul(b, n); o[n] = [lerp(x[0], y[0], k), lerp(x[1], y[1], k), lerp(x[2], y[2], k)]; } return o; }
function addPose(a, d) { const o = { ...a }; for (const [n, v] of Object.entries(d)) { const x = eul(o, n); o[n] = [x[0] + v[0], x[1] + v[1], x[2] + v[2]]; } return o; }
function over(a, d) { return { ...a, ...d }; }
const qTmp = new THREE.Quaternion(), eTmp = new THREE.Euler();
let LAST = {};
function applyPose(p, root) {
  const lim = {};
  for (const n of Object.keys(G.bones)) { const b = G.bones[n]; let e = eul(p, n); if (LIMITS[n]) e = e.map((v, i) => softc(v, LIMITS[n][i][0], LIMITS[n][i][1])); lim[n] = e;
    b.position.copy(G.REST[n].pos); b.quaternion.copy(G.REST[n].q).multiply(qTmp.setFromEuler(eTmp.set(e[0] * D2R, e[1] * D2R, e[2] * D2R))); }
  const R = new THREE.Quaternion().setFromEuler(new THREE.Euler((root.tilt || 0) * D2R, (root.yaw || 0) * D2R, (root.roll || 0) * D2R, 'YXZ'));
  G.root.quaternion.copy(R); G.root.position.copy(V(root.x || 0, root.y ?? HIP.y, root.z || 0)).sub(HIP.clone().applyQuaternion(R)); G.root.updateMatrixWorld(true); LAST = lim;
}
function wpos(n) { return G.bones[n].getWorldPosition(new THREE.Vector3()); }
function armIK(S, target, pole, w) {
  if (w < 0.001) return;
  const names = ['uarm' + S, 'uarmTwist' + S, 'farm' + S, 'farmTwist' + S]; const keep = names.map(n => G.bones[n].quaternion.clone());
  G.root.updateMatrixWorld(true);
  const sh = wpos('uarm' + S), l1 = G.REST['uarm' + S].len, l2 = G.REST['farm' + S].len;
  const tv = target.clone().sub(sh); const d = clamp(tv.length(), Math.abs(l1 - l2) + 1e-3, l1 + l2 - 1e-3); const dir = tv.normalize();
  const side = new THREE.Vector3().crossVectors(dir, pole.clone().sub(sh)).normalize(), up = new THREE.Vector3().crossVectors(side, dir).normalize();
  const a = Math.acos(clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1));
  const elbow = sh.clone().addScaledVector(dir, Math.cos(a) * l1).addScaledVector(up, Math.sin(a) * l1), hand = sh.clone().addScaledVector(dir, d);
  G.bones['uarmTwist' + S].quaternion.identity(); G.bones['farmTwist' + S].quaternion.identity();
  G.aim('uarm' + S, elbow.clone().sub(sh), side); G.aim('farm' + S, hand.clone().sub(elbow), side);
  names.forEach((n, i) => G.bones[n].quaternion.copy(keep[i].clone().slerp(G.bones[n].quaternion.clone(), w)));
  G.root.updateMatrixWorld(true);
}
function handTo(S, target, pole, w, palmQ) {              // hand on a point (IK), optional world orientation for the hand
  armIK(S, target, pole, w);
  if (palmQ && w > 0.001) { const hq = G.bones['hand' + S].getWorldQuaternion(new THREE.Quaternion()); G.setWorld('hand' + S, hq.slerp(palmQ, w)); }
}
function flail(T, amp, hz, seed) { return amp * (0.65 * Math.sin(2 * Math.PI * hz * T + seed) + 0.35 * Math.sin(2 * Math.PI * hz * 1.73 * T + seed * 2.1)); }
function blink(t) { for (const b0 of [2.4, 6.0, 10.6, 14.9, 18.2, 22.8, 27.5, 31.6, 35.0]) { const u = (t - b0) / 0.16; if (u > 0 && u < 1) return Math.sin(Math.PI * u); } return 0; }

const P = {
  stand: { uarmR: [8, 0, -30], uarmL: [8, 0, 30], farmR: [14, 0, 0], farmL: [14, 0, 0], spine1: [-2, 0, 0], neck: [2, 0, 0] },
  hold: { uarmR: [40, 0, -16], uarmL: [8, 0, 28], farmR: [100, 0, 0], farmL: [14, 0, 0], neck: [-6, 0, 0], head: [-6, 0, 0] },
  belly: { uarmR: [40, 0, -14], uarmL: [44, 0, 18], farmR: [96, 0, 0], farmL: [96, 0, 0], spine1: [-6, 0, 0], neck: [-10, 0, 0], head: [-6, 0, 0] },
};
for (const k of Object.keys(P)) { curl(P[k], 'R', k === 'hold' ? 55 : 22); curl(P[k], 'L', 22); }
const GRIP = curl({}, 'R', 22, 40);                    // pinching the slice
const KNIFE_FINGERS = curl({}, 'R', 82, 50);

// ------------------------------------------------------------------ the story
const STAND = { x: 0, y: HIP.y, z: -0.1 };
function guyAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  let pose = P.stand, root = { ...STAND }, face = { blink: blink(t) }, hand = null, xr = 0, rash = 0, look = null;
  // where his right hand holds the slice (relative to the mouth), bite timing
  if (b === 0 || b === 9 || b === 1) {
    pose = over(P.hold, GRIP);
    const biteT = b === 0 ? 0.95 : 99;
    const toMouth = b === 0 ? smooth(0.15, 0.85, lt) * (1 - smooth(1.25, 1.75, lt)) : b === 9 ? smooth(d - 1.0, d, lt) * 0 : 0;
    hand = { mode: 'slice', k: toMouth };
    const chew = b === 0 ? smooth(1.15, 1.35, lt) : b === 1 ? 1 - smooth(1.5, 2.5, lt) : 0;
    const jaw = b === 0 && lt < 1.05 ? 0.55 * smooth(0.55, 0.9, lt) : chew * (0.12 + 0.12 * Math.sin(t * 11));
    face = { ...face, jaw, smile: b === 0 ? 0.35 * smooth(1.4, 2.0, lt) : b === 9 ? 0.4 : 0.15, brow: 0.2, look: [0.1, -0.35] };
    if (b === 9) { pose = over(P.hold, GRIP); hand = { mode: 'grab', k: 0, reach: smooth(0.0, 0.7, lt) * (1 - smooth(0.85, 1.7, lt)) }; face = { ...face, smile: 0.4, look: [0.3 * (1 - smooth(1.0, 1.8, lt)), -0.45] }; }
  } else if (b === 2) {
    pose = { ...mixPose(P.stand, { spine1: [-22, 0, 0], spine2: [-16, 0, 0], chest: [-6, 0, 0], neck: [-14, 0, 0], head: [-12, 0, 0] }, 1), ...KNIFE_FINGERS, ...curl({}, 'L', 8, 5) };
    hand = { mode: 'cut' };
    face = { ...face, browIn: 0.4, press: 0.4, look: [0, -0.8] };
  } else if (b === 3 || b === 5) {
    pose = mixPose(P.stand, P.belly, b === 5 ? smooth(2.0, 3.0, lt) : 0);
    xr = smooth(0.0, 0.5, lt) * (1 - smooth(d - 0.3, d, lt));
    face = b === 3 ? { ...face, jaw: 0.1 + 0.1 * Math.sin(t * 9) * (1 - smooth(0.5, 1.2, lt)), look: [0, 0] }
      : { ...face, fear: 0.5 * smooth(1.0, 2.5, lt), frown: 0.6 * smooth(1.0, 2.5, lt), pain: 0.5 * smooth(2.0, 3.0, lt), browIn: 0.7 * smooth(1.0, 2.5, lt), squint: 0.4, look: [0, -0.2] };
  } else if (b === 4) {
    const q = smooth(0.2, 1.0, lt) * (1 - smooth(2.4, 3.2, lt));
    pose = mixPose(P.stand, P.belly, q);
    pose = addPose(pose, { spine1: [-4 * q, 0, 0], neck: [6 * (1 - q), 0, 0] });
    face = { ...face, frown: 0.5 * q, press: 0.4 * q, browIn: 0.4 * q, smile: 0.5 * smooth(2.5, 3.2, lt), brow: 0.4 * smooth(2.5, 3.2, lt), look: [0, -0.1] };
  } else if (b === 6) {
    rash = smooth(0.2, 2.2, lt);
    const sneeze = lt - 2.9;
    const inhale = smooth(-1.0, 0, sneeze) * (sneeze < 0 ? 1 : 0), snap = sneeze >= 0 ? Math.exp(-sneeze * 4) : 0;
    pose = addPose(P.stand, { uarmL: [60 * smooth(0.6, 1.2, lt) * (1 - smooth(2.0, 2.5, lt)), 0, -20], farmL: [120 * smooth(0.6, 1.2, lt) * (1 - smooth(2.0, 2.5, lt)), 0, 0],
      neck: [16 * inhale - 26 * snap, 0, 0], head: [10 * inhale - 14 * snap, 0, 0], spine2: [6 * inhale - 14 * snap, 0, 0], spine1: [-8 * snap, 0, 0] });
    if (lt > 0.6 && lt < 2.5) hand = { mode: 'scratch', k: smooth(0.6, 1.2, lt) * (1 - smooth(2.0, 2.5, lt)) };
    face = { ...face, squint: 0.6 * inhale + 1.0 * snap, jaw: 0.35 * inhale + 0.5 * snap, oh: 0.4 * inhale, brow: 0.8 * inhale, pain: 0.3 * rash, browIn: 0.5 * rash * (1 - inhale), blink: Math.max(face.blink, snap) };
  } else if (b === 7) {
    const lift = smooth(0.1, 0.8, lt) * (1 - smooth(1.7, 2.2, lt));
    pose = over(addPose(P.stand, { spine1: [-6 * lift, 0, 0], neck: [-8 * lift, 0, 0] }), { ...curl({}, 'R', 40, 25), ...curl({}, 'L', 18, 10) });
    hand = { mode: 'loaf', k: lift };
    const cough = lt > 2.2 ? Math.abs(Math.sin((lt - 2.2) * 9)) * (1 - smooth(d - 0.4, d, lt)) : 0;
    xr = smooth(1.9, 2.3, lt) * (1 - smooth(d - 0.3, d, lt));
    face = { ...face, squint: 0.5 * smooth(0.6, 1.0, lt) + 0.5 * cough, oh: 0.3 * cough, jaw: 0.3 * cough, frown: 0.5 * smooth(1.6, 2.2, lt), browIn: 0.6 * smooth(1.6, 2.2, lt), look: [0, -0.6 * lift] };
  } else if (b === 8) {
    const turn = smooth(0.0, 0.7, lt);
    root.yaw = (15 * turn + 50 * smooth(0.5, 1.3, lt)) * (1 - smooth(d - 0.6, d, lt));      // turns toward the bin as he carries it
    root.x = -0.48 * smooth(0.3, 1.2, lt) * (1 - smooth(d - 0.6, d, lt));
    hand = { mode: 'toss', k: lt };
    const lean = smooth(0.0, 0.5, lt) * (1 - smooth(1.2, 1.8, lt));
    pose = { ...addPose(P.stand, { spine1: [-14 * lean, 0, 8 * lean], spine2: [-8 * lean, 0, 6 * lean] }), ...curl({}, 'L', 45, 25) };
    face = { ...face, frown: 0.4, sneer: 0.4 * smooth(0, 0.6, lt), look: [0.4 * turn, -0.5] };
  }
  return { pose, root, face, hand, xr, rash };
}

// ------------------------------------------------------------------ cameras
function shake(t, a, f = 1) { return V(vn1(t * 3 * f, 1) * a, vn1(t * 3 * f, 2) * a, vn1(t * 3 * f, 3) * a * 0.5); }
function camAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b], u = lt / d;
  let pos, tgt, fov = 40;
  const hd = wpos('head'), sl = sliceGrp.getWorldPosition(new THREE.Vector3());
  if (b === 0 || b === 9) {                               // the hook: chest-up, the slice and its spot big in the foreground at the bite
    const k = b === 0 ? sm(u) : 0;
    pos = V(0.12 - 0.05 * k, 1.5 - 0.02 * k, -1.05 + 0.25 * k); tgt = V(0.03, 1.47 - 0.02 * k, 0); fov = 40 - 3 * k;
  } else if (b === 1) {                                   // macro on the slice in his hand: the spot, then the threads
    const c = BOARD_SLICE.clone().add(V(0.012, 0, 0.07).applyQuaternion(new THREE.Quaternion().setFromAxisAngle(V(0, 1, 0), KYAW * D2R)));
    pos = c.clone().add(V(0.02, 0.3 - 0.06 * u, -0.17 + 0.03 * u)); tgt = c; fov = 34;
  } else if (b === 2) {                                   // above the cutting board
    pos = V(0.15, 1.45, -1.05 + 0.08 * u); tgt = V(-0.05, 0.97, -0.5); fov = 34 - 2 * u;
  } else if (b === 3 || b === 5) {                        // torso, x-ray
    pos = V(0.05, 1.22, -1.25 + 0.15 * u); tgt = V(-0.02, 1.16, 0); fov = 36;
  } else if (b === 4) {
    pos = V(0.35, 1.45, -1.7 + 0.2 * u); tgt = V(0.05, 1.3, 0); fov = 38;
  } else if (b === 6) {                                   // face close: the rash, then the sneeze
    pos = hd.clone().add(V(0.12, -0.02, -0.75 + 0.15 * u)); tgt = hd.clone().add(V(0, -0.1, 0)); fov = 34;
    const sneeze = lt - 2.9; if (sneeze > 0) pos.add(shake(t, 0.02 * Math.exp(-sneeze * 3), 4));
  } else if (b === 7) {                                   // the sniff, from the side-front; x-ray lungs after
    const x = smooth(1.75, 2.15, lt);
    pos = V(0.9, 1.52, -1.15).lerp(V(0.06, 1.34, -1.2), x); tgt = V(0.1, 1.47, -0.35).lerp(V(0, 1.3, -0.1), x); fov = lerp(40, 38, x);
  } else {                                                // wide: the toss into the bin
    pos = V(-0.62, 1.42, -4.2); tgt = V(-0.62, 0.9, -0.15); fov = 42;
  }
  const punch = b > 0 && b !== 9 ? (1 - smooth(0, 0.22, lt)) * 0.07 : 0;
  return { pos, tgt, fov: fov * (1 - punch) };
}

// ------------------------------------------------------------------ per-frame update
const qS = new THREE.Quaternion();
function update(t) {
  t = ((t % TOTAL) + TOTAL) % TOTAL;
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  const g = guyAt(t);
  applyPose(g.pose, g.root);
  const up = V(0, 1, 0);
  const shR = wpos('uarmR'), shL = wpos('uarmL');
  // props default
  sliceGrp.visible = false; sliceCutA.visible = cornerPiece.visible = false; knife.visible = false;
  loaf.position.copy(LOAF0.p); loaf.quaternion.copy(LOAF0.q); loaf.visible = b !== 9 && !(b === 7 && lt > 1.75 && lt < DUR[7] - 0.1);
  const H_ = g.hand;
  const slicePlace = (handPos) => {                        // the slice held by its lower corner, spot facing out
    sliceGrp.visible = true;
    const hq = G.bones.handR.getWorldQuaternion(new THREE.Quaternion());
    sliceGrp.position.copy(wpos('handR')).add(V(-0.03, 0.06, -0.04));
    sliceGrp.quaternion.setFromEuler(new THREE.Euler(0.15, 0.25, 0.12));
  };
  if (window.OVR && window.OVR.gs != null) GR_SLICE = SLICE_GRIPS[window.OVR.gs];
  if (window.OVR && window.OVR.gl != null) GR_LOAF_R = LOAF_GRIPS[window.OVR.gl];
  if (H_ && (H_.mode === 'slice' || H_.mode === 'grab')) {
    // the slice's pose decides the hand: at the chest facing the camera; at the mouth, the bitten corner at his lips
    const mouth = MOUTH.getWorldPosition(new THREE.Vector3());
    const qRest = new THREE.Quaternion().setFromEuler(new THREE.Euler(0.12, 0.3, 0.06)), pRest = V(0.1, 1.26, -0.3);
    const qe = (window.OVR && window.OVR.qm) || [0.15, 0.45, 0.05];
    const qM = new THREE.Quaternion().setFromEuler(new THREE.Euler(...qe));
    const Bp = V(-0.045, 0.118, 0);                                       // the bite corner (slice-local)
    const pM = mouth.clone().add(V(0, -0.004, -0.01)).sub(Bp.clone().applyQuaternion(qM));
    let qS = qRest.clone().slerp(qM, sm(H_.k)), pS = pRest.clone().lerp(pM, sm(H_.k));
    if (H_.reach) {                                                       // 'grab': the hand comes from the second loaf's end with the new slice
      const qL = loaf2.quaternion.clone(), pL = loaf2.localToWorld(V(-0.004, 0, 0.13));
      qS = qRest.clone(); pS = pRest.clone().lerp(pL.add(V(0, 0.02, -0.03)), H_.reach);
    }
    const fr = 1 - sm(H_.k);                                             // at the chest the slice may spin in its own plane (the spot still faces us); at the mouth it must not
    holdProp(GR_SLICE, qS, pS, shR.clone().add(V(0.35, -0.45, 0.15)), 1, [[V(0, 0, 1).applyQuaternion(qS), 80 * fr], [V(0, 1, 0), 20 * fr]]);
    sliceGrp.visible = !(H_.mode === 'grab' && lt < 0.85);
    propFromHand(GR_SLICE, sliceGrp);
  }
  const bitten = b === 0 && lt > 0.95;
  sliceBoard.visible = b === 1; sliceBoard.position.copy(BOARD_SLICE); sliceBoard.quaternion.setFromAxisAngle(V(0, 1, 0), KYAW * D2R).multiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI / 2, 0, 0)));
  if (b > 2 && b < 9) { sliceCutA.visible = cornerPiece.visible = true; }
  sliceWhole.visible = !bitten; sliceBit.visible = bitten;
  if (H_ && H_.mode === 'scratch') {                     // fingertips scratching the side of his neck
    const nk = wpos('neck').add(V(-0.058, 0.045, -0.02));
    const qS = basisQ(V(1, 0, 0.15), V(0.1, 1, -0.1));                     // palm toward the neck, fingers up: grip axes x = n, y = u
    const sc = 0.01 * Math.sin(t * 22);
    holdProp(GR_NECK, qS, nk.add(V(0, sc, 0)), shL.clone().add(V(-0.45, -0.4, 0.25)), H_.k, [[V(1, 0, 0), 40], [V(0, 1, 0), 40]]);
  }
  const KY = new THREE.Quaternion().setFromAxisAngle(V(0, 1, 0), ((window.OVR && window.OVR.kyaw != null) ? window.OVR.kyaw : KYAW) * D2R);   // the slice sits turned so the knife cuts the way a right hand naturally holds it
  const qlB = KY.clone().multiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI / 2, 0, 0)));
  const placeCut = (slide) => { const off = V(0.035, 0, 0.06).applyQuaternion(KY).multiplyScalar(slide);
    sliceCutA.position.copy(BOARD_SLICE); sliceCutA.quaternion.copy(qlB); cornerPiece.position.copy(BOARD_SLICE).add(off); cornerPiece.quaternion.copy(qlB);
    const nrm = V(0, 0, 1).applyQuaternion(KY), pt = BOARD_SLICE.clone().add(V(0, 0, CUTY).applyQuaternion(KY)).add(off);
    cutPlane.normal.copy(nrm); cutPlane.constant = -nrm.dot(pt); };
  if (b > 2 && b < 9) placeCut(1);
  if (b === 2) {                                         // the slice flat on the board, spot up (far side); the knife cuts the top off
    const c0 = BOARD_SLICE.clone();
    sliceCutA.visible = cornerPiece.visible = true;
    placeCut(smooth(1.45, 2.2, lt));
    // the knife: handle on his right, blade across the slice along the cut; down, two strokes of sawing, away
    knife.visible = true;
    const down = smooth(0.1, 0.6, lt), away = smooth(1.35, 1.9, lt);
    const saw = 0.035 * Math.sin(Math.PI * 2 * clamp((lt - 0.6) / 0.75, 0, 1) * 1.5) * smooth(0.55, 0.7, lt) * (1 - away);
    knife.position.copy(c0).add(V(0.115 + saw + 0.05 * away, 0.008 + 0.14 * (1 - down) + 0.12 * away, CUTY).applyQuaternion(KY));
    knife.quaternion.copy(KY).multiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(0, Math.PI, -0.1 * (1 - down))));
    holdProp(GR_KNIFE, knife.quaternion.clone(), knife.position.clone(), shR.clone().add(V(0.5, -0.2, 0.2)));
    propFromHand(GR_KNIFE, knife);                                         // (the knife is exactly where it was asked to be)
    const qBoard = sliceCutA.quaternion.clone();
    holdProp(GR_FLAT_L, qBoard, c0.clone(), shL.clone().add(V(-0.5, -0.2, 0.2)));
  }
  if (H_ && H_.mode === 'loaf') {                         // lifts the loaf in both hands, the cut end under his nose, then sets it down
    const nose = NOSE.getWorldPosition(new THREE.Vector3());
    const qN = new THREE.Quaternion().setFromEuler(new THREE.Euler(0.2, Math.PI, 0));       // the moldy cut end turned to his face, tipped up
    const pN = nose.clone().add(V(0.0, -0.02, -0.03)).sub(V(0.025, 0.085, -0.12).applyQuaternion(qN));
    const k = sm(H_.k);
    const pC = pN.clone().add(V(0.05, -0.3, -0.12));                                         // already in his hand at chest height when the shot starts
    loaf.quaternion.copy(qN); loaf.position.copy(pC.lerp(pN, k));
    const w = 1;
    holdProp(GR_LOAF_R, loaf.quaternion.clone(), loaf.position.clone(), shR.clone().add(V(0.45, -0.35, 0.1)), w, [[V(0, 0, 1).applyQuaternion(loaf.quaternion), 60], [V(0, 1, 0), 40]]);
    if (w > 0.99) propFromHand(GR_LOAF_R, loaf);
    // (one hand is enough for a loaf of bread; the left stays down)
  }
  if (H_ && H_.mode === 'toss') {                         // grabs the loaf with his left hand, swings it over the bin, lets go
    const lt8 = H_.k, rel = 1.35;
    const grab = smooth(0.0, 0.45, lt8);
    const above = bin.position.clone().add(V(0.1, 0.95, -0.04));
    const fly = clamp((lt8 - rel) / 0.4, 0, 1);
    const hp = lt8 < rel ? LOAF0.p.clone().lerp(above, smooth(0.35, rel, lt8)).add(V(0, 0.25 * Math.sin(Math.PI * smooth(0.35, rel, lt8)), 0)) : above.clone();
    const lp = lt8 < rel ? hp.clone() : hp.clone().lerp(bin.position.clone().add(V(0, 0.3, 0)), fly * fly);
    loaf.visible = fly < 0.97; loaf.position.copy(lp); loaf.quaternion.copy(LOAF0.q).multiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(1.8 * fly, 0, 0)));
    const hold = lt8 < rel ? loaf : null;
    const qT = hold ? loaf.quaternion.clone() : LOAF0.q.clone(), pT = hold ? loaf.position.clone() : above.clone();
    holdProp(GR_LOAF_TOP, qT, pT, shL.clone().add(V(-0.45, -0.3, 0.15)), grab * (1 - smooth(rel + 0.3, rel + 0.8, lt8)), [[V(0, 1, 0), 80], [V(1, 0, 0), 30]]);
    if (hold && grab > 0.99) propFromHand(GR_LOAF_TOP, loaf);
    bin.userData.lid.rotation.x = -1.1 * smooth(rel - 0.5, rel - 0.1, lt8) * (1 - smooth(rel + 0.6, rel + 0.9, lt8));
  } else bin.userData.lid.rotation.x = 0;
  for (const S of ['R', 'L']) {                          // fold any twist already split off back in, so a second untwist can't lose it
    const ua = G.bones['uarm' + S], ut = G.bones['uarmTwist' + S]; ua.quaternion.multiply(ut.quaternion); ut.quaternion.identity(); }
  untwistSafe(); G.face(g.face); G.root.updateMatrixWorld(true);
  RASH.uRash.value = g.rash;
  // x-ray
  ghost(g.xr); organs.visible = g.xr > 0.02;
  stomach.visible = acid.visible = b !== 7; chunks.forEach(c => c.visible = b !== 7); lungs.visible = b === 7;
  if (organs.visible) {
    const lt3 = b === 3 ? lt : 3;
    chunks.forEach((c, i) => { const k = b === 3 ? smooth(0.8 + 0.3 * i, 3.4, lt3) : 1; c.scale.setScalar(Math.max(0.001, 1 - 0.85 * k));
      c.rotation.set(0.15 * Math.sin(t * 2 + i), t * 0.4 + i, 0.15 * Math.cos(t * 1.7 + i)); c.position.copy(FLOAT_AT[i]).add(V(0, 0.002 * Math.sin(t * 3 + i), 0)); });
    organs.updateMatrixWorld(true);
    acidPlane.set(V(0, -1, 0), FILL_Y).applyMatrix4(organs.matrixWorld);           // the fill level rides with his body
  }
  // bread x-ray: threads in beat 1 (in his hand) and beat 2 (left in the slice after the cut)
  sliceMat.userData.u.uThr.value = b === 1 ? smooth(1.2, 3.8, lt) : b >= 2 ? 1 : 0; sliceMat.userData.u.uXr.value = b === 1 ? smooth(1.0, 1.8, lt) : 0;
  cutMat.userData.u.uThr.value = 1; cutMat.userData.u.uXr.value = b === 2 ? smooth(2.3, 2.9, lt) : 0; cutMat.userData.u.uMold.value = 0;
  cornerPiece.material.userData.u.uXr.value = 0;
  // particles
  const mouth = MOUTH.getWorldPosition(new THREE.Vector3()), nose = NOSE.getWorldPosition(new THREE.Vector3());
  if (b === 0 && lt > 0.95 && lt < 1.6) for (let i = 0; i < 18; i++) { const a = ((lt - 0.95) * 1.6 + hash1(i)) % 1;     // crumbs
    puff(mouth.clone().add(V((hash1(i * 3) - 0.5) * 0.08, -0.25 * a * a - 0.02, -0.04)), 0.006, 0.9 * (1 - a), new THREE.Color(0.85, 0.7, 0.45)); }
  if (b === 3 && organs.visible) {                        // acid bubbles and dissolving cells in the stomach
    for (let i = 0; i < 70; i++) { const a = (lt * (0.4 + 0.6 * hash1(i)) + hash1(i * 2)) % 1;      // bubbles rising through the acid to its surface
      const bp = BUB[i % BUB.length]; const q = V(bp.x, lerp(bp.y, FILL_Y - 0.002, a), bp.z);
      puff(organs.localToWorld(q), 0.003 + 0.003 * hash1(i), 0.9 * Math.sin(Math.PI * a), C_ACID); }
    for (let i = 0; i < 40; i++) { const a = clamp((lt - 1.0 - hash1(i) * 2.0) / 0.8, 0, 1); if (a <= 0 || a >= 1) continue;
      const c0 = FLOAT_AT[i % 4];
      puff(organs.localToWorld(c0.clone().add(V((hash1(i * 3) - 0.5) * 0.02 * (1 + a), -0.012 * a, (hash1(i * 9) - 0.5) * 0.015))), 0.005 * (1 - a), 0.9 * (1 - a), new THREE.Color(0.2, 0.6, 0.35)); }
  }
  if (b === 5 && organs.visible) {                        // mycotoxins spreading out from the gut
    const ac = organs.localToWorld(ST_PTS[30].clone());
    for (let i = 0; i < 160; i++) { const a = clamp((lt - 0.6) * 0.45 - hash1(i) * 0.6, 0, 1); if (a <= 0) continue;
      const dir = V(hash1(i * 3) - 0.5, (hash1(i * 5) - 0.3) * 1.6, (hash1(i * 7) - 0.5) * 0.3).normalize();
      puff(ac.clone().addScaledVector(dir, 0.04 + 0.35 * a), 0.012 + 0.01 * hash1(i), 0.85 * (1 - smooth(0.85, 1, a)), C_TOX); }
  }
  if (b === 6 && lt > 2.9) for (let i = 0; i < 70; i++) { const a = clamp((lt - 2.9) * (1.2 + hash1(i)) , 0, 1);   // the sneeze spray
    const dir = V((hash1(i * 3) - 0.5) * 0.6, (hash1(i * 5) - 0.6) * 0.5, -1).normalize();
    puff(mouth.clone().addScaledVector(dir, 0.05 + 0.6 * a), 0.008 + 0.03 * a, 0.7 * (1 - a), C_SPRAY); }
  if (b === 7) {                                          // spores lifting off the loaf, sucked up his nose; then glowing in the lungs
    loaf.updateMatrixWorld(true); const lp = loaf.localToWorld(V(0.02, 0.085, -0.125));
    for (let i = 0; i < 90; i++) { const a = ((lt * 0.9 + hash1(i)) % 1) * smooth(0.5, 1.0, lt) * (1 - smooth(1.9, 2.3, lt));
      const p = lp.clone().lerp(nose, a * a).add(V((hash1(i * 3) - 0.5) * 0.06 * (1 - a), (hash1(i * 5) - 0.5) * 0.04 * (1 - a), 0));
      puff(p, 0.004 + 0.004 * hash1(i * 7), 0.9 * Math.sin(Math.PI * Math.min(1, a * 1.2)) * smooth(0.5, 1.0, lt), C_SPORE); }
    if (organs.visible) {
      for (let i = 0; i < 70; i++) { const s = hash1(i) > 0.5 ? 1 : -1;
        puff(organs.localToWorld(V(0.07 * s + (hash1(i * 3) - 0.5) * 0.08, 1.33 + (hash1(i * 5) - 0.5) * 0.17, (hash1(i * 7) - 0.5) * 0.06)), 0.007, 0.85 * g.xr, C_SPORE); } }
  }
  puffsDone();
  // camera
  const C = camAt(t);
  if (window.CAM) { C.pos = V(...window.CAM.pos); C.tgt = V(...window.CAM.tgt); C.fov = window.CAM.fov || 40; }
  camera.position.copy(C.pos); camera.lookAt(C.tgt); camera.fov = C.fov; camera.updateProjectionMatrix();
  return { beat: b, t };
}

// ------------------------------------------------------------------ frame I/O
let composer = null;
if (Q.get('ao') !== '0') {
  composer = new EffectComposer(renderer, new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: 4 }));
  composer.setPixelRatio(1); composer.setSize(W, H); composer.addPass(new RenderPass(scene, camera));
  const ao = new GTAOPass(scene, camera, W, H);
  ao.updateGtaoMaterial({ radius: 0.12, distanceExponent: 1, thickness: 1, scale: 1, samples: 12, distanceFallOff: 1, screenSpaceRadius: false });
  ao.updatePdMaterial({ lumaPhi: 10, depthPhi: 2, normalPhi: 3, radius: 6, rings: 2, samples: 12 }); ao.blendIntensity = 0.7;
  composer.addPass(ao); composer.addPass(new OutputPass());
}
const draw = () => { if (composer) composer.render(); else renderer.render(scene, camera); };
const gl = renderer.getContext();
const px = new Uint8Array(W * H * 4);
function renderInto(i) { update(i / FPS); draw(); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); }
window.renderAll = async (f0, f1) => { for (let i = f0; i < f1; i++) { renderInto(i); await fetch('/frame', { method: 'POST', body: px }); } return 'ok'; };
window.renderAtT = t => { update(t); draw(); return renderer.domElement.toDataURL('image/png'); };
window.handinfo = () => ({ p: G.bones.handR.getWorldPosition(new THREE.Vector3()).toArray(), q: G.bones.handR.getWorldQuaternion(new THREE.Quaternion()).toArray(), n: HR.R.n.toArray(), u: HR.R.u.toArray() });
window.fkcheck = () => { const S = 'R', x = { flex: 40, abd: 20, rot: 10, el: 70, pro: 30, wf: 10, wd: 5 }; const ua = G.bones.uarmR; G.root.updateMatrixWorld(true);
  const f = armFK(S, x, ua.parent.getWorldQuaternion(new THREE.Quaternion()), ua.getWorldPosition(new THREE.Vector3())); applyArm(S, x, 1);
  return { fk: f.wr.toArray().map(v => +v.toFixed(4)), bone: G.bones.handR.getWorldPosition(new THREE.Vector3()).toArray().map(v => +v.toFixed(4)), fkq: f.Qh.toArray().map(v => +v.toFixed(3)), boneq: G.bones.handR.getWorldQuaternion(new THREE.Quaternion()).toArray().map(v => +v.toFixed(3)), el: f.el.toArray().map(v => +v.toFixed(3)) }; };
window.dbg = (t, o) => { window.OVR = o || null; for (const k in WRIST_LOG) delete WRIST_LOG[k]; window.DBGH = 0; update(t); window.DBGH = 0; const f = n => G.bones[n].getWorldPosition(new THREE.Vector3()).toArray().map(x => +x.toFixed(3)); knife.updateMatrixWorld(true); return { nose: (() => { loaf.updateMatrixWorld(true); return loaf.localToWorld(V(0.025, 0.085, -0.12)).distanceTo(NOSE.getWorldPosition(new THREE.Vector3())).toFixed(3); })(), err: JSON.stringify(WRIST_LOG), knifeGrip: knife.localToWorld(V(-0.04,0,0)).toArray().map(x => +x.toFixed(3)), knifeVis: knife.visible, handR: f('handR'), farmR: f('farmR'), uarmR: f('uarmR'), slice: sliceGrp.position.toArray().map(x => +x.toFixed(3)), vis: G.meshes.skin_handR ? G.meshes.skin_handR.visible : 'none', meshes: Object.keys(G.meshes) }; };
window.wristLog = () => { const o = JSON.parse(JSON.stringify(ARM_LOG)); for (const k in ARM_LOG) delete ARM_LOG[k]; return o; };
window.rigReport = i => { const r = update(i / FPS); return { t: r.t, beat: r.beat, ang: LAST }; };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS);
window.READY = true;
