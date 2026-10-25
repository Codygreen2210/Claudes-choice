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
  bin.position.set(-1.28, 0, -0.2); scene.add(bin); }

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
  float front = step(vL.z, 0.0) * face;
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
for (const m of [sliceWhole, sliceBit]) { m.castShadow = true; m.position.set(0, -SH * 0.42, 0); }
const cutMat = breadMat({ seed: 1 });
const CUTY = 0.066;
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
const LOAF0 = { p: V(-0.6, 0.977, -0.5), q: new THREE.Quaternion().setFromEuler(new THREE.Euler(0, Math.PI / 2 - 0.25, 0)) };
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
{ const curve = new THREE.CatmullRomCurve3([V(0.005, 1.27, 0.0), V(-0.02, 1.235, -0.02), V(-0.06, 1.19, -0.035), V(-0.07, 1.13, -0.04), V(-0.04, 1.085, -0.045), V(0.01, 1.08, -0.04), V(0.05, 1.1, -0.035)]);
  const g = new THREE.TubeGeometry(curve, 40, 0.035, 20, false); const p = g.attributes.position;
  for (let i = 0; i < p.count; i++) { const v = V(p.getX(i), p.getY(i), p.getZ(i)); const u = curve.getUtoTmapping(0, 0); }
  // swell the body of the stomach (J shape: wide fundus/body, narrowing pylorus)
  const pts = curve.getSpacedPoints(40);
  for (let i = 0; i < p.count; i++) { const v = V(p.getX(i), p.getY(i), p.getZ(i)); let best = 0, bd = 9; pts.forEach((c, k) => { const dd = c.distanceTo(v); if (dd < bd) { bd = dd; best = k; } });
    const s = 1 + 0.75 * Math.sin(Math.PI * clamp((best / 40 - 0.12) / 0.7, 0, 1)); const c = pts[best]; v.sub(c).multiplyScalar(s).add(c); p.setXYZ(i, v.x, v.y, v.z); }
  g.computeVertexNormals();
  const sm_ = new THREE.Mesh(g, organMat(0xf08a8a)); sm_.material.side = THREE.DoubleSide; sm_.material.opacity = 0.55; stomach.add(sm_);
  const eso = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3([V(0, 1.56, -0.03), V(0, 1.45, -0.0), V(0.0, 1.35, 0.01), V(0.005, 1.27, 0.0)]), 20, 0.011, 12, false), organMat(0xe57b7b)); eso.material.opacity = 0.6; stomach.add(eso);
  organs.add(stomach); }
// stomach acid (a glowing pool in the bottom of the stomach) and its contents
const acid = new THREE.Mesh(new THREE.SphereGeometry(1, 24, 16), new THREE.MeshStandardMaterial({ color: 0xb8ff4a, emissive: 0x5a9a10, emissiveIntensity: 0.8, transparent: true, opacity: 0.7, roughness: 0.2 }));
acid.scale.set(0.055, 0.03, 0.04); acid.position.set(-0.035, 1.105, -0.04); organs.add(acid);
const chunks = [];                                      // swallowed bread chunks with mold cells
const cellMat = new THREE.MeshStandardMaterial({ color: 0x2f8f55, emissive: 0x0f4020, roughness: 0.5 });
for (let i = 0; i < 4; i++) { const ch = new THREE.Group(); const c = new THREE.Mesh(new RoundedBoxGeometry(0.022, 0.016, 0.018, 2, 0.005), new THREE.MeshStandardMaterial({ color: 0xe8d4a8, roughness: 0.8 })); ch.add(c);
  for (let k = 0; k < 7; k++) { const s = new THREE.Mesh(new THREE.IcosahedronGeometry(0.0035, 1), cellMat); s.position.set((hash1(i * 9 + k) - 0.5) * 0.024, 0.006 + hash1(i * 5 + k) * 0.004, (hash1(i * 3 + k) - 0.5) * 0.02); ch.add(s); }
  ch.position.set(-0.05 + 0.025 * i, 1.11 + 0.008 * (i % 2), -0.04 + 0.006 * i); organs.add(ch); chunks.push(ch); }
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
const GRIP = curl({}, 'R', 62, 30);

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
    pose = mixPose(P.stand, { spine1: [-22, 0, 0], spine2: [-16, 0, 0], chest: [-6, 0, 0], neck: [-14, 0, 0], head: [-12, 0, 0], ...curl({}, 'R', 70, 40) }, 1);
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
    const lift = smooth(0.0, 0.7, lt) * (1 - smooth(1.7, 2.2, lt));
    pose = over(addPose(P.stand, { spine1: [-6 * lift, 0, 0], neck: [-8 * lift, 0, 0] }), { ...curl({}, 'R', 45, 30), ...curl({}, 'L', 45, 30) });
    hand = { mode: 'loaf', k: lift };
    const cough = lt > 2.2 ? Math.abs(Math.sin((lt - 2.2) * 9)) * (1 - smooth(d - 0.4, d, lt)) : 0;
    xr = smooth(1.9, 2.3, lt) * (1 - smooth(d - 0.3, d, lt));
    face = { ...face, squint: 0.5 * smooth(0.6, 1.0, lt) + 0.5 * cough, oh: 0.3 * cough, jaw: 0.3 * cough, frown: 0.5 * smooth(1.6, 2.2, lt), browIn: 0.6 * smooth(1.6, 2.2, lt), look: [0, -0.6 * lift] };
  } else if (b === 8) {
    const turn = smooth(0.0, 0.7, lt);
    root.yaw = 30 * turn * (1 - smooth(d - 0.6, d, lt));
    hand = { mode: 'toss', k: lt };
    pose = P.stand;
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
    const c = BOARD_SLICE.clone().add(V(0.0, 0, 0.06)); pos = c.clone().add(V(0.02, 0.3 - 0.06 * u, -0.17 + 0.03 * u)); tgt = c; fov = 34;
  } else if (b === 2) {                                   // above the cutting board
    pos = V(0.15, 1.45, -1.05 + 0.08 * u); tgt = V(-0.05, 0.97, -0.5); fov = 34 - 2 * u;
  } else if (b === 3 || b === 5) {                        // torso, x-ray
    pos = V(0.05, 1.3, -1.25 + 0.15 * u); tgt = V(0.0, 1.24, 0); fov = 36;
  } else if (b === 4) {
    pos = V(0.35, 1.45, -1.7 + 0.2 * u); tgt = V(0.05, 1.3, 0); fov = 38;
  } else if (b === 6) {                                   // face close: the rash, then the sneeze
    pos = hd.clone().add(V(0.12, -0.02, -0.75 + 0.15 * u)); tgt = hd.clone().add(V(0, -0.1, 0)); fov = 34;
    const sneeze = lt - 2.9; if (sneeze > 0) pos.add(shake(t, 0.02 * Math.exp(-sneeze * 3), 4));
  } else if (b === 7) {                                   // the sniff, from the side-front; x-ray lungs after
    const x = smooth(1.75, 2.15, lt);
    pos = V(1.25, 1.56, -0.28).lerp(V(0.06, 1.34, -1.2), x); tgt = V(-0.02, 1.5, -0.24).lerp(V(0, 1.3, -0.1), x); fov = lerp(30, 38, x);
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
  if (H_ && (H_.mode === 'slice' || H_.mode === 'grab')) {
    // at the chest, the slice faces the camera; to the mouth, the bite corner meets his lips; 'grab' reaches the second loaf first
    const mouth = MOUTH.getWorldPosition(new THREE.Vector3());
    const rest = V(0.12, 1.28, -0.32), atMouth = mouth.clone().add(V(0.035, -0.075, -0.075));
    let tgt = rest.clone().lerp(atMouth, H_.k);
    if (H_.reach) tgt = tgt.lerp(loaf2.position.clone().add(V(-0.17, 0.02, 0.02)), H_.reach);
    handTo('R', tgt, shR.clone().add(V(0.35, -0.4, 0.1)), 1);
    sliceGrp.visible = !(H_.mode === 'grab' && lt < 0.85);
    sliceGrp.quaternion.setFromEuler(new THREE.Euler(lerp(0.05, -0.2, H_.k), lerp(0.25, 1.15, H_.k), lerp(0.05, 0.25, H_.k)));
    sliceGrp.position.copy(wpos('handR')).add(V(-0.05, 0.085, -0.045).applyQuaternion(new THREE.Quaternion().setFromEuler(new THREE.Euler(0, lerp(0, 0.9, H_.k), 0))));
  }
  const bitten = b === 0 && lt > 0.95;
  sliceBoard.visible = b === 1; sliceBoard.position.copy(BOARD_SLICE); sliceBoard.quaternion.setFromEuler(new THREE.Euler(Math.PI / 2, 0, 0));
  if (b > 2 && b < 9) { sliceCutA.visible = cornerPiece.visible = true; }
  sliceWhole.visible = !bitten; sliceBit.visible = bitten;
  if (H_ && H_.mode === 'scratch') handTo('L', wpos('neck').add(V(-0.06, 0.02, -0.06)), shL.clone().add(V(-0.4, -0.3, 0)), H_.k);
  if (b > 2 && b < 9) {
    const ql = new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI / 2, 0, 0)), off = V(0.05, 0, 0.05);
    sliceCutA.position.copy(BOARD_SLICE); sliceCutA.quaternion.copy(ql); cornerPiece.position.copy(BOARD_SLICE).add(off); cornerPiece.quaternion.copy(ql);
    cutPlane.normal.set(0, 0, 1); cutPlane.constant = -(BOARD_SLICE.z + CUTY + off.z);
  }
  if (b === 2) {                                         // the slice flat on the board, spot up (far side); the knife cuts the top off
    const c0 = BOARD_SLICE.clone();
    const ql = new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI / 2, 0, 0));
    sliceCutA.visible = cornerPiece.visible = true;
    sliceCutA.position.copy(c0); sliceCutA.quaternion.copy(ql);
    const slide = smooth(1.45, 2.2, lt), off = V(0.05 * slide, 0, 0.05 * slide);
    cornerPiece.position.copy(c0).add(off); cornerPiece.quaternion.copy(ql);
    cutPlane.normal.set(0, 0, 1); cutPlane.constant = -(c0.z + CUTY + off.z);
    // the knife: handle on his right, blade across the slice along the cut; down, two strokes of sawing, away
    knife.visible = true;
    const down = smooth(0.1, 0.6, lt), away = smooth(1.35, 1.9, lt);
    const saw = 0.035 * Math.sin(Math.PI * 2 * clamp((lt - 0.6) / 0.75, 0, 1) * 1.5) * smooth(0.55, 0.7, lt) * (1 - away);
    knife.position.set(c0.x + 0.115 + saw + 0.05 * away, c0.y + 0.008 + 0.14 * (1 - down) + 0.12 * away, c0.z + CUTY);
    knife.quaternion.setFromEuler(new THREE.Euler(0, Math.PI, -0.1 * (1 - down)));
    knife.updateMatrixWorld(true); const grip = knife.localToWorld(V(-0.035, 0.0, 0));
    const pe = (window.OVR && window.OVR.palm) || [0, 0, 0];
    const palm = knife.quaternion.clone().multiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(pe[0] * D2R, pe[1] * D2R, pe[2] * D2R)));
    handTo('R', grip.clone().add(V(0, 0.02, 0)), shR.clone().add(V(0.45, -0.25, 0.05)), 1, palm);
    handTo('L', c0.clone().add(V(-0.03, 0.025, 0.02)), shL.clone().add(V(-0.45, -0.3, 0.1)), 1);
  }
  if (H_ && H_.mode === 'loaf') {                         // lifts the loaf in both hands, cut end to his nose, then sets it down
    const nose = NOSE.getWorldPosition(new THREE.Vector3());
    const atNose = nose.clone().add(V(0.0, -0.075, -0.05));
    const p = LOAF0.p.clone().lerp(atNose, H_.k);
    const qN = new THREE.Quaternion().setFromEuler(new THREE.Euler(0.15, Math.PI, 0));
    loaf.position.copy(p); loaf.quaternion.copy(LOAF0.q.clone().slerp(qN, H_.k));
    const along = V(0, 0, -1).applyQuaternion(loaf.quaternion), side = V(1, 0, 0).applyQuaternion(loaf.quaternion);
    const mid = p.clone().addScaledVector(along, -0.12 * 0 + 0.0).add(V(0, 0.05, 0)).addScaledVector(V(0, 0, 1).applyQuaternion(loaf.quaternion), 0.12);
    const w = smooth(0, 0.35, lt) * (1 - smooth(1.55, 2.05, lt));
    handTo('R', mid.clone().addScaledVector(side, 0.075), shR.clone().add(V(0.4, -0.35, 0)), w);
    handTo('L', mid.clone().addScaledVector(side, -0.075), shL.clone().add(V(-0.4, -0.35, 0)), w);
  }
  if (H_ && H_.mode === 'toss') {                         // grabs the loaf with his left hand, swings it over the bin, lets go
    const lt8 = H_.k, rel = 1.35;
    const grab = smooth(0.0, 0.45, lt8);
    const above = bin.position.clone().add(V(0.12, 0.98, -0.02));
    const fly = clamp((lt8 - rel) / 0.4, 0, 1);
    const hp = lt8 < rel ? LOAF0.p.clone().lerp(above, smooth(0.35, rel, lt8)).add(V(0, 0.25 * Math.sin(Math.PI * smooth(0.35, rel, lt8)), 0)) : above.clone();
    const lp = lt8 < rel ? hp.clone() : hp.clone().lerp(bin.position.clone().add(V(0, 0.3, 0)), fly * fly);
    loaf.visible = fly < 0.97; loaf.position.copy(lp); loaf.quaternion.copy(LOAF0.q).multiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(1.8 * fly, 0, 0)));
    handTo('L', (lt8 < rel ? hp : above.clone().add(V(0, 0.05, 0))).clone().add(V(0.0, 0.07, 0)), shL.clone().add(V(-0.4, -0.3, 0.1)), grab * (1 - smooth(rel + 0.3, rel + 0.8, lt8)));
    bin.userData.lid.rotation.x = -1.1 * smooth(rel - 0.5, rel - 0.1, lt8) * (1 - smooth(rel + 0.6, rel + 0.9, lt8));
  } else bin.userData.lid.rotation.x = 0;
  G.untwist(); G.face(g.face); G.root.updateMatrixWorld(true);
  RASH.uRash.value = g.rash;
  // x-ray
  ghost(g.xr); organs.visible = g.xr > 0.02;
  stomach.visible = acid.visible = b !== 7; chunks.forEach(c => c.visible = b !== 7); lungs.visible = b === 7;
  if (organs.visible) {
    const lt3 = b === 3 ? lt : 3;
    chunks.forEach((c, i) => { const k = b === 3 ? smooth(0.8 + 0.3 * i, 3.4, lt3) : 1; c.scale.setScalar(Math.max(0.001, 1 - 0.85 * k)); c.rotation.set(t * 0.7 + i, t * 0.5, 0); });
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
    const ac = acid.getWorldPosition(new THREE.Vector3());
    for (let i = 0; i < 60; i++) { const a = (lt * (0.4 + 0.6 * hash1(i)) + hash1(i * 2)) % 1;
      puff(ac.clone().add(V((hash1(i * 5) - 0.5) * 0.09, -0.01 + 0.05 * a, (hash1(i * 7) - 0.5) * 0.04)), 0.004 + 0.004 * hash1(i), 0.9 * Math.sin(Math.PI * a), C_ACID); }
    for (let i = 0; i < 40; i++) { const a = clamp((lt - 1.0 - hash1(i) * 2.0) / 0.8, 0, 1); if (a <= 0 || a >= 1) continue;
      const c0 = chunks[i % 4].getWorldPosition(new THREE.Vector3());
      puff(c0.clone().add(V((hash1(i * 3) - 0.5) * 0.03 * (1 + 2 * a), 0.02 * a, (hash1(i * 9) - 0.5) * 0.02)), 0.006 * (1 - a), 0.9 * (1 - a), new THREE.Color(0.2, 0.6, 0.35)); }
  }
  if (b === 5 && organs.visible) {                        // mycotoxins spreading out from the gut
    const ac = acid.getWorldPosition(new THREE.Vector3());
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
window.rigReport = i => { const r = update(i / FPS); return { t: r.t, beat: r.beat, ang: LAST }; };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS);
window.READY = true;
