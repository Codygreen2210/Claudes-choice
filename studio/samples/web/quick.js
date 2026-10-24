// "What happens if you step in quicksand" - a 3D Short with the sculpted, skinned guy.
//   quick.html?w=1080&h=1920            (times from qs/times.json; one shot per narration line)
// Beats: 0 sinking (hook) | 1 panic kick | 2 cutaway: sand packs | 3 stops at the waist | 4 cutaway: 2x denser, floats
//        5 tugs a leg -> deadlifts a car | 6 the tide coming | 7 cutaway: wiggles, water seeps in | 8 leans back, floats out
//        9 walks straight back in (loops into beat 0)
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
const TIMES = await (await fetch('/qs/times.json')).json();
const B = TIMES.starts, DUR = TIMES.durs, TOTAL = TIMES.total;
const clamp = (x, a, b) => Math.min(Math.max(x, a), b);
const sm = t => t * t * (3 - 2 * t);
const smooth = (a, b, x) => sm(clamp((x - a) / (b - a), 0, 1));
const lerp = (a, b, u) => a + (b - a) * u;
const D2R = Math.PI / 180;
function hash1(n) { const s = Math.sin(n * 127.1) * 43758.5453; return s - Math.floor(s); }
function vn1(x, seed) { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return lerp(hash1(i + seed * 17.3), hash1(i + 1 + seed * 17.3), u) * 2 - 1; }

// ------------------------------------------------------------------ renderer / scene / sky
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(W, H);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.0;
renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.localClippingEnabled = true;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0xe9c9a6, 30, 140);
const camera = new THREE.PerspectiveCamera(42, W / H, 0.03, 600);

const SUNDIR = new THREE.Vector3(-0.55, 0.32, -0.77).normalize();      // low golden sun, in front-left of him
const skyMat = new THREE.ShaderMaterial({
  side: THREE.BackSide, depthWrite: false, fog: false,
  uniforms: { uSun: { value: SUNDIR }, uLin: { value: Q.get('ao') !== '0' ? 1 : 0 } },
  vertexShader: 'varying vec3 vD; void main(){ vD = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
  fragmentShader: `varying vec3 vD; uniform vec3 uSun; uniform float uLin;
    void main(){ float h = clamp(vD.y, -0.2, 1.0);
      vec3 top = vec3(0.30, 0.50, 0.80), mid = vec3(0.92, 0.72, 0.55), hor = vec3(1.0, 0.80, 0.58);
      vec3 c = mix(hor, mid, smoothstep(0.0, 0.12, h)); c = mix(c, top, smoothstep(0.1, 0.65, h));
      float s = max(dot(normalize(vD), uSun), 0.0);
      c += vec3(1.0, 0.75, 0.45) * (pow(s, 8.0) * 0.35 + pow(s, 900.0) * 6.0);
      c = mix(c, vec3(0.85, 0.72, 0.6), (1.0 - smoothstep(-0.2, 0.0, vD.y)));
      gl_FragColor = vec4(uLin > 0.5 ? pow(c, vec3(2.2)) * 0.92 : c, 1.0); }`,
});
const sky = new THREE.Mesh(new THREE.SphereGeometry(500, 48, 24), skyMat); scene.add(sky);
{ // environment light for glossy wet sand and water
  const pm = new THREE.PMREMGenerator(renderer); const es = new THREE.Scene();
  es.add(new THREE.Mesh(new THREE.SphereGeometry(10, 32, 16), skyMat));
  scene.environment = pm.fromScene(es, 0.02).texture; scene.environmentIntensity = 0.28;
}
const hemi = new THREE.HemisphereLight(0xb7c8ff, 0xc89a6a, 0.55); scene.add(hemi);
const sun = new THREE.DirectionalLight(0xffd0a0, 3.0);
sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
const SC = sun.shadow.camera; SC.left = -3; SC.right = 3; SC.top = 3; SC.bottom = -3; SC.near = 0.5; SC.far = 40;
sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.02;
scene.add(sun); scene.add(sun.target);
const fill = new THREE.DirectionalLight(0x9fb8ff, 0.5); fill.position.set(4, 3, 5); scene.add(fill);

// ------------------------------------------------------------------ ground: wet tidal flat, ripples, the quicksand pool
const POOL = { x: 0, z: 0, r: 1.45 };
const CARX = 7.5, CARZ = 4.5;                      // where the car sits (firm sand, off to the side)
const FOOT = [];                                   // his footprints leading back to the pool (x, z, angle)
for (let i = 0; i < 9; i++) FOOT.push(new THREE.Vector3((i % 2 ? 0.1 : -0.1) + Math.sin(i * 0.7) * 0.05, 0.85 + i * 0.62, 0));
const groundU = { uT: { value: 0 }, uRip: { value: 0 }, uRipC: { value: new THREE.Vector2(0, 0) }, uPoolR: { value: POOL.r },
  uFoot: { value: FOOT }, uTide: { value: 60 }, uDry: { value: 0 }, uMatte: { value: 0 } };
const groundMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.6, metalness: 0 });
groundMat.onBeforeCompile = sh => {
  Object.assign(sh.uniforms, groundU);
  sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vW;')
    .replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvW = (modelMatrix * vec4(transformed, 1.0)).xyz;');
  sh.fragmentShader = sh.fragmentShader.replace('#include <common>', `#include <common>
varying vec3 vW; uniform float uT, uRip, uPoolR, uTide, uDry, uMatte; uniform vec2 uRipC; uniform vec3 uFoot[9];
float hh(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
float vn(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f*f*(3.0-2.0*f);
  return mix(mix(hh(i), hh(i+vec2(1,0)), u.x), mix(hh(i+vec2(0,1)), hh(i+vec2(1,1)), u.x), u.y); }
// sand ripples (wind/tide marks): wavy parallel ridges, faded inside the pool
float rip(vec2 p){ float w = p.x * 0.8 + p.y * 0.6 + 0.35 * sin(p.y * 1.7) + 0.2 * vn(p * 0.7) * 3.0;
  return sin(w * 11.0) * 0.5 + 0.5; }`)
    .replace('#include <color_fragment>', `#include <color_fragment>
  vec2 P = vW.xz; float r = length(P);
  float pool = 1.0 - smoothstep(uPoolR - 0.25, uPoolR + 0.15, r + 0.12 * (vn(P * 2.0) - 0.5));
  float wet = mix(0.55 + 0.35 * vn(P * 0.35), 1.0, pool) * (1.0 - uDry);
  float ripA = (1.0 - pool) * (0.6 + 0.4 * vn(P * 0.5));
  vec3 dry = vec3(0.88, 0.70, 0.46), wetc = vec3(0.56, 0.41, 0.25), mud = vec3(0.22, 0.155, 0.095);
  vec3 col = mix(dry, wetc, wet);
  col = mix(col, mud, pool * 0.95);
  col = mix(col, wetc * 0.75, (1.0 - pool) * (1.0 - smoothstep(uPoolR, uPoolR + 0.55, r)) * 0.6);   // a damp halo around the pool
  col *= 0.92 + 0.12 * vn(P * 9.0) + 0.06 * rip(P) * ripA;
  // footprints
  for (int i = 0; i < 9; i++) { vec2 d = P - uFoot[i].xy; d = vec2(d.x * 1.0, d.y * 0.42);
    float fp = 1.0 - smoothstep(0.05, 0.075, length(d)); col = mix(col, wetc * 0.7, fp * 0.8); }
  diffuseColor.rgb = col;
  float tideWet = (1.0 - smoothstep(uTide - 0.5, uTide + 0.5, vW.z));
  vWetness = max(wet, tideWet);`)
    .replace('#include <roughnessmap_fragment>', `#include <roughnessmap_fragment>
  roughnessFactor = mix(0.92, 0.6, vWetness);
  roughnessFactor = mix(roughnessFactor, mix(0.3, 0.7, uMatte), pool);`)
    .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
  { // ripple normals (tangent-free: perturb the up-facing normal in view space)
    float e = 0.01; vec2 P2 = vW.xz;
    float h0 = rip(P2), hx = rip(P2 + vec2(e, 0.0)), hz = rip(P2 + vec2(0.0, e));
    vec3 gr = vec3(-(hx - h0) / e, 0.0, -(hz - h0) / e) * 0.010 * ripA;
    // the pool: soft rings spreading out from where he moves
    float rr = length(P2 - uRipC);
    float ring = sin(rr * 26.0 - uT * 7.0) * exp(-rr * 1.3) * uRip * pool;
    vec2 rd = (P2 - uRipC) / max(rr, 1e-3);
    gr += vec3(rd.x, 0.0, rd.y) * ring * 0.16;
    gr += vec3(vn(P2 * 6.0) - 0.5, 0.0, vn(P2 * 6.0 + 7.0) - 0.5) * 0.06 * (1.0 - pool);
    vec3 nW = normalize(vec3(0.0, 1.0, 0.0) + gr);
    normal = normalize((viewMatrix * vec4(nW, 0.0)).xyz);
  }`)
    .replace('void main() {', 'float vWetness = 0.0; float pool = 0.0; float ripA = 0.0;\nvoid main() {');
  // the variables above are assigned inside main (pool/ripA declared global so later chunks see them)
  sh.fragmentShader = sh.fragmentShader.replace('float pool = 1.0 - smoothstep', 'pool = 1.0 - smoothstep').replace('float ripA = (1.0 - pool)', 'ripA = (1.0 - pool)');
};
const groundGeo = new THREE.PlaneGeometry(260, 260, 260, 260); groundGeo.rotateX(-Math.PI / 2);
{ // gentle undulation far away, dead flat around the action (so feet and the pool meet the surface cleanly)
  const p = groundGeo.attributes.position;
  for (let i = 0; i < p.count; i++) { const x = p.getX(i), z = p.getZ(i), r = Math.hypot(x, z);
    p.setY(i, (Math.sin(x * 0.09) * Math.cos(z * 0.07) * 0.35 + Math.sin(x * 0.031 + 1) * 0.6) * smooth(14, 45, r) * smooth(6, -10, z) - 0.7 * smooth(12, 45, z)); }
  groundGeo.computeVertexNormals();
}
const ground = new THREE.Mesh(groundGeo, groundMat); ground.receiveShadow = true; scene.add(ground);

// sea far behind him (+z) and the incoming tide sheet
const waterU = { uT: { value: 0 }, uEdge: { value: 60 } };
const waterMat = new THREE.MeshStandardMaterial({ color: 0x2f6a72, roughness: 0.06, metalness: 0.0, transparent: true });
waterMat.onBeforeCompile = sh => {
  Object.assign(sh.uniforms, waterU);
  sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vW;')
    .replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvW = (modelMatrix * vec4(transformed, 1.0)).xyz;');
  sh.fragmentShader = sh.fragmentShader.replace('#include <common>', `#include <common>
varying vec3 vW; uniform float uT, uEdge;`)
    .replace('#include <color_fragment>', `#include <color_fragment>
  float wob = 0.6 * sin(vW.x * 0.35 + uT * 0.8) + 0.35 * sin(vW.x * 1.3 - uT * 1.4) + 0.15 * sin(vW.x * 3.1 + uT * 2.0);
  float e = vW.z - (uEdge + wob);                       // > 0 is water
  if (e < 0.0) discard;
  float foam = (1.0 - smoothstep(0.0, 1.2, e)) * (0.65 + 0.35 * sin(vW.x * 9.0 + uT * 3.0) * sin(vW.x * 4.0 - uT));
  float shallow = smoothstep(0.0, 6.0, e);
  diffuseColor.rgb = mix(vec3(0.32, 0.46, 0.46), vec3(0.10, 0.30, 0.36), shallow);
  diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.95, 0.93, 0.88), foam);
  diffuseColor.a = mix(0.82, 0.97, shallow);`)
    .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
  { vec3 gr = vec3(0.12 * cos(vW.x * 1.7 + uT * 1.6) + 0.06 * cos(vW.x * 4.1 - vW.z * 2.0 + uT * 2.3), 1.0,
                   0.12 * cos(vW.z * 1.3 - uT * 1.9) + 0.05 * sin(vW.z * 5.0 + uT)); normal = normalize((viewMatrix * vec4(normalize(gr), 0.0)).xyz); }`);
};
const water = new THREE.Mesh(new THREE.PlaneGeometry(300, 250, 1, 1).rotateX(-Math.PI / 2), waterMat);
water.position.set(0, 0.012, 117); water.receiveShadow = true; scene.add(water);

// warning sign in the background (with the one Easter egg: a small subscribe sticker on the post)
function canvasTex(w, h, draw) { const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d')); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t; }
const signTex = canvasTex(512, 384, g => {
  g.fillStyle = '#f2c230'; g.fillRect(0, 0, 512, 384); g.strokeStyle = '#151515'; g.lineWidth = 22; g.strokeRect(14, 14, 484, 356);
  g.fillStyle = '#151515'; g.font = 'bold 92px Inter, Arial, sans-serif'; g.textAlign = 'center'; g.fillText('DANGER', 256, 150);
  g.font = 'bold 74px Inter, Arial, sans-serif'; g.fillText('QUICKSAND', 256, 270);
});
const stickTex = canvasTex(256, 96, g => { g.fillStyle = '#e02020'; g.beginPath(); g.roundRect(4, 4, 248, 88, 40); g.fill(); g.fillStyle = '#fff'; g.font = 'bold 44px Inter, Arial'; g.textAlign = 'center'; g.fillText('SUBSCRIBE', 128, 64); });
const sign = new THREE.Group();
{ const wood = new THREE.MeshStandardMaterial({ color: 0x6b4a2e, roughness: 0.9 });
  const post = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.06, 1.9, 10), wood); post.position.y = 0.95; post.castShadow = true; sign.add(post);
  const board = new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.6, 0.03), [wood, wood, wood, wood, new THREE.MeshStandardMaterial({ map: signTex, roughness: 0.7 }), wood]);
  board.position.set(0, 1.6, -0.05); board.castShadow = true; sign.add(board);
  const st = new THREE.Mesh(new THREE.PlaneGeometry(0.16, 0.06), new THREE.MeshStandardMaterial({ map: stickTex, roughness: 0.5 })); st.position.set(0, 0.85, -0.062); sign.add(st);
  sign.position.set(-2.6, 0, 3.2); sign.rotation.y = 0.35; scene.add(sign); }
// a few shells and pebbles so the flat reads at scale
{ const g = new THREE.SphereGeometry(1, 8, 6), mt = new THREE.MeshStandardMaterial({ color: 0xe9dfcf, roughness: 0.6 });
  const inst = new THREE.InstancedMesh(g, mt, 260); const m4 = new THREE.Matrix4(); let k = 0;
  for (let i = 0; i < 600 && k < 260; i++) { const x = (hash1(i * 3.1) - 0.5) * 30, z = (hash1(i * 7.7) - 0.5) * 30; if (Math.hypot(x, z) < POOL.r + 0.4) continue;
    const s = 0.012 + hash1(i * 1.3) * 0.025; m4.compose(new THREE.Vector3(x, s * 0.2, z), new THREE.Quaternion().setFromEuler(new THREE.Euler(0, hash1(i) * 6, 0)), new THREE.Vector3(s * 1.4, s * 0.5, s)); inst.setMatrixAt(k++, m4); }
  inst.count = k; inst.receiveShadow = true; scene.add(inst); }

// ------------------------------------------------------------------ the cutaway: a sand wall through the pool
const CUTZ = 0.16;                                   // just behind his legs, so they stand in front of the section
const clipCut = new THREE.Plane(new THREE.Vector3(0, 0, 1), -CUTZ);
const cutU = { uPack: { value: 0 }, uSeep: { value: 0 }, uT: { value: 0 }, uLegs: { value: [0, 1, 2, 3].map(() => new THREE.Vector2()) }, uBowl: { value: 1.3 } };
const cutMat = new THREE.ShaderMaterial({
  uniforms: cutU, side: THREE.DoubleSide,
  vertexShader: 'varying vec3 vW; void main(){ vW = (modelMatrix * vec4(position, 1.0)).xyz; gl_Position = projectionMatrix * viewMatrix * vec4(vW, 1.0); }',
  fragmentShader: `varying vec3 vW; uniform float uPack, uSeep, uT, uBowl; uniform vec2 uLegs[4];
  float hh(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
  float segd(vec2 p, vec2 a, vec2 b){ vec2 pa = p - a, ba = b - a; float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0); return length(pa - ba * h); }
  void main(){
    vec2 p = vW.xy; float y = -p.y;                    // depth below the surface
    // firm sand: layered strata, grain speckle
    float layer = sin(y * 22.0 + sin(p.x * 3.0) * 0.6) * 0.5 + 0.5;
    vec3 firm = mix(vec3(0.42, 0.28, 0.14), vec3(0.32, 0.21, 0.10), layer) * (0.85 + 0.3 * hh(floor(p * 260.0)));
    // the quicksand bowl: water-logged, darker, glistening grains, with a slow swirl
    float bowl = (p.x * p.x) / (1.45 * 1.45) + (y * y) / (uBowl * uBowl);
    float inB = (1.0 - smoothstep(0.96, 1.02, bowl));
    vec3 qs = vec3(0.10, 0.065, 0.035) * (0.8 + 0.4 * hh(floor((p + vec2(0.0, uT * 0.01)) * 300.0)));
    qs += vec3(0.25, 0.3, 0.32) * step(0.985, hh(floor(p * 140.0) + floor(uT * 3.0))) * 0.35;   // glints of water
    vec3 c = mix(firm, qs, inB);
    // packed sand hugging his legs (darker, tighter grain)
    float dl = min(segd(p, uLegs[0], uLegs[1]), segd(p, uLegs[2], uLegs[3]));
    float pk = (1.0 - smoothstep(0.07, 0.17, dl)) * uPack * inB * step(0.0, y);
    c = mix(c, vec3(0.035, 0.022, 0.012) * (0.7 + 0.6 * hh(floor(p * 500.0))), pk * 0.95);
    // water seeping down along the legs
    float sp = (1.0 - smoothstep(0.05, 0.12, dl)) * uSeep * inB * step(0.0, y);
    float streak = 0.5 + 0.5 * sin(y * 40.0 + uT * 6.0 + p.x * 30.0);
    c = mix(c, vec3(0.06, 0.2, 0.35), sp * (0.5 + 0.35 * streak));
    // a crisp top edge (the surface line) and a dark bottom fade
    c *= mix(0.45, 1.0, (1.0 - smoothstep(0.6, 2.0, y)));
    c = mix(c, vec3(0.05, 0.035, 0.02), (1.0 - smoothstep(0.0, 0.012, y)) * 0.6);
    gl_FragColor = vec4(c, 1.0);
    #include <tonemapping_fragment>
    #include <colorspace_fragment>
  }`,
});
const cutWall = new THREE.Mesh(new THREE.PlaneGeometry(9, 2.2), cutMat);
cutWall.position.set(0, -1.1, CUTZ); cutWall.rotation.y = Math.PI; cutWall.visible = false; scene.add(cutWall);
cutWall.rotation.y = 0; // faces -z (toward the camera at -z) by default plane normal is +z; flip
cutWall.scale.x = -1;
// up arrows (buoyancy) and the seep particles
const arrowMat = new THREE.MeshStandardMaterial({ color: 0xffd23a, emissive: 0x6a4a00, roughness: 0.4 });
const arrows = [];
for (let i = 0; i < 3; i++) { const g = new THREE.Group();
  const sh = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 0.32, 16), arrowMat); sh.position.y = 0.16; g.add(sh);
  const hd = new THREE.Mesh(new THREE.ConeGeometry(0.085, 0.16, 20), arrowMat); hd.position.y = 0.4; g.add(hd);
  g.visible = false; scene.add(g); arrows.push(g); }
const NSEEP = 220;
const seepGeo = new THREE.BufferGeometry(); const seepPos = new Float32Array(NSEEP * 3); seepGeo.setAttribute('position', new THREE.BufferAttribute(seepPos, 3));
const seep = new THREE.Points(seepGeo, new THREE.PointsMaterial({ color: 0x8fd0ff, size: 0.018, transparent: true, opacity: 0.85, depthWrite: false }));
seep.visible = false; scene.add(seep);

// ------------------------------------------------------------------ the car (for "the force of lifting a car")
const car = new THREE.Group();
{ const paint = new THREE.MeshPhysicalMaterial({ color: 0xc8322a, roughness: 0.32, clearcoat: 1, clearcoatRoughness: 0.08, metalness: 0.2 });
  const glass = new THREE.MeshPhysicalMaterial({ color: 0x1a2630, roughness: 0.05, metalness: 0.3 });
  const black = new THREE.MeshStandardMaterial({ color: 0x151515, roughness: 0.6 });
  const chrome = new THREE.MeshStandardMaterial({ color: 0xdddddd, roughness: 0.2, metalness: 1 });
  const lamp = new THREE.MeshStandardMaterial({ color: 0xaa1010, emissive: 0x550000, roughness: 0.3 });
  const body = new THREE.Mesh(new RoundedBoxGeometry(1.8, 0.62, 4.4, 4, 0.16), paint); body.position.y = 0.62; car.add(body);
  const cab = new THREE.Mesh(new RoundedBoxGeometry(1.62, 0.55, 2.2, 4, 0.2), paint); cab.position.set(0, 1.15, 0.25); car.add(cab);
  const win = new THREE.Mesh(new RoundedBoxGeometry(1.64, 0.4, 2.0, 3, 0.12), glass); win.position.set(0, 1.18, 0.25); car.add(win);
  for (const [x, z] of [[-0.82, -1.35], [0.82, -1.35], [-0.82, 1.4], [0.82, 1.4]]) {
    const wh = new THREE.Mesh(new THREE.CylinderGeometry(0.34, 0.34, 0.24, 24).rotateZ(Math.PI / 2), black); wh.position.set(x, 0.34, z); car.add(wh);
    const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.17, 0.17, 0.25, 16).rotateZ(Math.PI / 2), chrome); hub.position.set(x, 0.34, z); car.add(hub); }
  const bump = new THREE.Mesh(new RoundedBoxGeometry(1.84, 0.16, 0.18, 2, 0.06), black); bump.position.set(0, 0.42, 2.22); car.add(bump);
  for (const x of [-0.65, 0.65]) { const l = new THREE.Mesh(new RoundedBoxGeometry(0.34, 0.12, 0.05, 2, 0.02), lamp); l.position.set(x, 0.78, 2.205); car.add(l); }
  car.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
}
const carPivot = new THREE.Group(); carPivot.add(car); car.position.set(0, 0, 1.35);   // pivot at the front axle
carPivot.position.set(CARX, 0, CARZ - 1.35); carPivot.visible = false; scene.add(carPivot);

// ------------------------------------------------------------------ the guy (with mud up to the waist)
const MUD = { uMud: { value: 1.05 }, uSurf: { value: 1 } };
function muddy(m) {
  m.onBeforeCompile = sh => {
    Object.assign(sh.uniforms, MUD);
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying float vRestY; varying vec3 vRestP; varying vec3 vWp;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvRestY = position.y; vRestP = position;')
      .replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvWp = (modelMatrix * vec4(transformed, 1.0)).xyz;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', `#include <common>
varying float vRestY; varying vec3 vRestP; varying vec3 vWp; uniform float uMud, uSurf;
float mh(vec3 p){ return fract(sin(dot(p, vec3(12.9898, 78.233, 37.719))) * 43758.5453); }`)
      .replace('#include <color_fragment>', `#include <color_fragment>
  float edge = uMud + 0.022 * sin(vRestP.x * 37.0 + vRestP.z * 23.0) + 0.014 * sin(vRestP.x * 71.0 - vRestP.z * 53.0) + 0.01 * sin(vRestP.z * 113.0);
  float md = (1.0 - smoothstep(edge - 0.03, edge + 0.02, vRestY));
  float speck = 0.5 + 0.5 * sin(vRestP.x * 23.0 + vRestP.y * 31.0) * sin(vRestP.z * 19.0 - vRestP.y * 17.0);
  float mudAmt = md * (0.75 + 0.25 * speck);
  diffuseColor.rgb *= mix(1.0, 0.62, mudAmt);                                            // soaked dark
  diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.30, 0.22, 0.12), mudAmt * 0.28);         // a film of mud
  float band = uSurf * (1.0 - smoothstep(0.0, 0.08 + 0.025 * sin(vWp.x * 60.0), vWp.y)) * step(-0.02, vWp.y) * step(length(vWp.xz), 1.6);
  diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.17, 0.12, 0.08), band * 0.9);
  mudAmt = max(mudAmt, band);`)
      .replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\n  roughnessFactor = mix(roughnessFactor, 0.35, mudAmt);');
  };
  return m;
}
const MAT = {
  skin: new THREE.MeshPhysicalMaterial({ color: 0xd99a7c, roughness: 0.55, sheen: 0.12, sheenColor: new THREE.Color(0xffb099), sheenRoughness: 0.6 }),
  shirt: muddy(new THREE.MeshPhysicalMaterial({ color: 0x1fae9b, roughness: 0.85, sheen: 0.8, sheenRoughness: 0.6, sheenColor: new THREE.Color(0x77ffe6) })),
  jeans: muddy(new THREE.MeshStandardMaterial({ color: 0x4068bd, roughness: 0.9 })),
  shoe: muddy(new THREE.MeshStandardMaterial({ color: 0x3a2d31, roughness: 0.55 })),
  sole: muddy(new THREE.MeshStandardMaterial({ color: 0xd9d2c8, roughness: 0.7 })),
  hair: new THREE.MeshStandardMaterial({ color: 0x5b351f, roughness: 0.62 }),
};
const G = await loadGuy(THREE, '/char/guy', { materials: MAT });
scene.add(G.root);
G.root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
const HIP = new THREE.Vector3(0.0, 0.95, 0.0);

// surface collars: wet sand bunched where the body goes into the sand
const collarMat = new THREE.MeshStandardMaterial({ color: 0x2c1f13, roughness: 0.18 });
const collars = [0, 1, 2].map(() => { const m = new THREE.Mesh(new THREE.TorusGeometry(1, 0.42, 10, 40).rotateX(Math.PI / 2).scale(1, 0.25, 1), collarMat); m.receiveShadow = true; m.castShadow = true; m.visible = false; scene.add(m); return m; });

// ------------------------------------------------------------------ rig: local joint angles (deg), limits, blending
// axes (rest A-pose): thigh +x = hip flex; shin -x = knee flex; foot +x = toes up; spine -x = bend forward;
// uarm +x = arm forward, uarm z = raise (R +, L -); farm +x = elbow flex; neck/head y = turn, x = nod (+ = up/back)
const LIMITS = {
  spine1: [[-30, 20], [-20, 20], [-15, 15]], spine2: [[-30, 20], [-20, 20], [-15, 15]], chest: [[-25, 20], [-20, 20], [-15, 15]],
  neck: [[-35, 35], [-50, 50], [-20, 20]], head: [[-30, 30], [-40, 40], [-20, 20]],
  uarmR: [[-50, 170], [-80, 80], [-40, 175]], uarmL: [[-50, 170], [-80, 80], [-175, 40]],
  farmR: [[0, 145], [-80, 80], [-20, 20]], farmL: [[0, 145], [-80, 80], [-20, 20]],
  handR: [[-60, 60], [-30, 30], [-60, 60]], handL: [[-60, 60], [-30, 30], [-60, 60]],
  thighR: [[-30, 120], [-40, 40], [-25, 45]], thighL: [[-30, 120], [-40, 40], [-45, 25]],
  shinR: [[-150, 0], [-10, 10], [-5, 5]], shinL: [[-150, 0], [-10, 10], [-5, 5]],
  footR: [[-45, 30], [-15, 15], [-15, 15]], footL: [[-45, 30], [-15, 15], [-15, 15]],
  clavR: [[-15, 15], [-10, 10], [-10, 25]], clavL: [[-15, 15], [-10, 10], [-25, 10]],
};
function softc(x, lo, hi, knee = 6) {      // soft clamp: eases into the limit instead of hitting a wall
  if (x > hi - knee) return hi - knee + knee * Math.tanh((x - (hi - knee)) / knee);
  if (x < lo + knee) return lo + knee - knee * Math.tanh(((lo + knee) - x) / knee);
  return x;
}
const FINGERS = ['index', 'middle', 'ring', 'pinky'];
function curl(p, S, c, th = c) {             // finger curl (deg) for one hand
  for (const f of FINGERS) { p[f + '1' + S] = [0, 0, (S === 'R' ? -1 : 1) * c * 0.9]; p[f + '2' + S] = [0, 0, (S === 'R' ? -1 : 1) * c]; }
  p['thumb1' + S] = [0, 0, (S === 'R' ? -1 : 1) * th * 0.4]; return p;
}
// named poses (only the joints that differ from the rest pose)
const P = {
  stand: { uarmR: [5, 0, -30], uarmL: [5, 0, 30], farmR: [12, 0, 0], farmL: [12, 0, 0] },
  balance: { uarmR: [22, 0, 14], uarmL: [22, 0, -14], farmR: [42, 0, 0], farmL: [42, 0, 0], spine2: [-6, 0, 0], neck: [-14, 0, 0], head: [-8, 0, 0] },
  flail: { uarmR: [40, 0, 75], uarmL: [40, 0, -75], farmR: [50, 0, 0], farmL: [50, 0, 0], spine2: [4, 0, 0], neck: [10, 0, 0], head: [6, 0, 0] },
  freeze: { uarmR: [15, 0, 45], uarmL: [15, 0, -45], farmR: [15, 0, 0], farmL: [15, 0, 0], spine2: [-3, 0, 0], neck: [-6, 0, 0] },
  restArms: { uarmR: [25, 0, 52], uarmL: [25, 0, -52], farmR: [20, 0, 0], farmL: [20, 0, 0], neck: [0, 0, 0] },   // forearms resting on the sand
  tug: { spine1: [-12, 0, 0], spine2: [-14, 0, 0], chest: [-8, 0, 0], uarmR: [62, 0, -8], uarmL: [62, 0, 8], farmR: [20, 0, 0], farmL: [20, 0, 0], neck: [-18, 0, 0], head: [-6, 0, 0] },
  tugBack: { spine1: [6, 0, 0], spine2: [6, 0, 0], chest: [4, 0, 0], uarmR: [38, 0, -10], uarmL: [38, 0, 10], farmR: [40, 0, 0], farmL: [40, 0, 0], neck: [8, 0, 0], head: [4, 0, 0] },
  squat: { thighR: [72, 0, 6], thighL: [72, 0, -6], shinR: [-88, 0, 0], shinL: [-88, 0, 0], footR: [18, 0, 0], footL: [18, 0, 0], spine1: [-14, 0, 0], spine2: [-12, 0, 0], chest: [-6, 0, 0], uarmR: [52, 0, -26], uarmL: [52, 0, 26], farmR: [8, 0, 0], farmL: [8, 0, 0], neck: [22, 0, 0] },
  lift: { thighR: [44, 0, 6], thighL: [44, 0, -6], shinR: [-55, 0, 0], shinL: [-55, 0, 0], footR: [10, 0, 0], footL: [10, 0, 0], spine1: [-6, 0, 0], spine2: [-4, 0, 0], chest: [0, 0, 0], uarmR: [38, 0, -26], uarmL: [38, 0, 26], farmR: [6, 0, 0], farmL: [6, 0, 0], neck: [16, 0, 0], head: [6, 0, 0] },
  lookTide: { uarmR: [25, 0, 52], uarmL: [25, 0, -52], farmR: [20, 0, 0], farmL: [20, 0, 0], neck: [6, 45, 0], head: [4, 30, 0] },
  wiggle: { uarmR: [20, 0, 58], uarmL: [20, 0, -58], farmR: [18, 0, 0], farmL: [18, 0, 0], thighR: [12, 0, 0], thighL: [12, 0, 0], shinR: [-14, 0, 0], shinL: [-14, 0, 0], neck: [-12, 0, 0] },
  float: { uarmR: [0, 0, 92], uarmL: [0, 0, -92], farmR: [10, 0, 0], farmL: [10, 0, 0], neck: [-25, 0, 0], head: [-10, 0, 0], thighR: [6, 0, 4], thighL: [6, 0, -4], shinR: [-6, 0, 0], shinL: [-6, 0, 0] },
  relief: { uarmR: [8, 0, -26], uarmL: [8, 0, 26], farmR: [18, 0, 0], farmL: [18, 0, 0], neck: [6, 0, 0], head: [4, 0, 0] },
  plunge: { uarmR: [26, 0, 30], uarmL: [26, 0, -30], farmR: [48, 0, 0], farmL: [48, 0, 0], spine2: [-4, 0, 0], neck: [-12, 0, 0], head: [-6, 0, 0] },
};
for (const k of Object.keys(P)) { curl(P[k], 'R', k === 'tug' || k === 'squat' || k === 'lift' ? 70 : 18); curl(P[k], 'L', k === 'tug' || k === 'squat' || k === 'lift' ? 70 : 18); }
const BONES = Object.keys(G.bones);
const qTmp = new THREE.Quaternion(), qA = new THREE.Quaternion(), qB = new THREE.Quaternion(), eTmp = new THREE.Euler();
function eul(p, n) { return p[n] || [0, 0, 0]; }
function mixPose(a, b, k) {                  // per-joint blend of Euler triples (poses stay well inside +-180, so linear is short-way)
  const o = {}; for (const n of new Set([...Object.keys(a), ...Object.keys(b)])) { const x = eul(a, n), y = eul(b, n); o[n] = [lerp(x[0], y[0], k), lerp(x[1], y[1], k), lerp(x[2], y[2], k)]; } return o;
}
function addPose(a, d) { const o = { ...a }; for (const [n, v] of Object.entries(d)) { const x = eul(o, n); o[n] = [x[0] + v[0], x[1] + v[1], x[2] + v[2]]; } return o; }
function keyed(keys, t) {                    // keys: [[t, pose], ...] eased between keys
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 0; i < keys.length - 1; i++) { const [t0, a] = keys[i], [t1, b] = keys[i + 1]; if (t <= t1) return mixPose(a, b, sm((t - t0) / (t1 - t0))); }
  return keys[keys.length - 1][1];
}
function flail(T, amp, hz, seed) { return amp * (0.65 * Math.sin(2 * Math.PI * hz * T + seed) + 0.35 * Math.sin(2 * Math.PI * hz * 1.73 * T + seed * 2.1)); }
let LAST = {};
function applyPose(p, root) {
  const lim = {};
  for (const n of BONES) {
    const b = G.bones[n]; let e = eul(p, n);
    if (LIMITS[n]) e = e.map((v, i) => softc(v, LIMITS[n][i][0], LIMITS[n][i][1]));
    lim[n] = e;
    b.position.copy(G.REST[n].pos);
    b.quaternion.copy(G.REST[n].q).multiply(qTmp.setFromEuler(eTmp.set(e[0] * D2R, e[1] * D2R, e[2] * D2R)));
  }
  // root: pivot around the hips; tilt back (x), yaw, then place the hips
  const R = new THREE.Quaternion().setFromEuler(new THREE.Euler((root.tilt || 0) * D2R, (root.yaw || 0) * D2R, (root.roll || 0) * D2R, 'YXZ'));
  const hipW = new THREE.Vector3(root.x || 0, HIP.y - (root.s || 0), root.z || 0);
  G.root.quaternion.copy(R);
  G.root.position.copy(hipW).sub(HIP.clone().applyQuaternion(R));
  G.root.updateMatrixWorld(true);
  LAST = lim;
}

// ------------------------------------------------------------------ the story, beat by beat
const RIPFIX = (2 * Math.PI * Math.round(7 * TOTAL / (2 * Math.PI)) / TOTAL) / 7;     // ripple rings loop seamlessly
const beatAt = t => { let i = 0; for (let k = 0; k < B.length; k++) if (t >= B[k]) i = k; return i; };
const S_KNEE = 0.52, S_DEEP = 0.86, S_WAIST = 0.93;
function sinkAt(t) {                        // how far his hips are below the surface
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  if (b === 0) return lerp(S_KNEE, 0.64, 1 - Math.pow(1 - lt / d, 1.6));
  if (b === 1) return lerp(0.64, S_DEEP, sm(lt / d)) + 0.02 * Math.sin(lt * 9) * (1 - lt / d);
  if (b === 2) return lerp(S_DEEP, 0.9, sm(lt / d));
  if (b === 3) return lerp(0.9, S_WAIST, sm(Math.min(1, lt / 1.2)));
  if (b === 4 || b === 6) return S_WAIST + 0.015 * Math.sin(t * 2.2);
  if (b === 5) return S_WAIST + 0.012 * Math.sin(t * 2.2);
  if (b === 7) return lerp(S_WAIST, 0.86, sm(lt / d)) + 0.01 * Math.sin(t * 2.2);
  return 0;
}
function guyAt(t) {                         // -> { pose, root, face, collar }
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  let pose, root = { s: sinkAt(t) }, face = { blink: blink(t) }, collar = true, ik = null;
  if (b === 0) {
    pose = keyed([[0, P.plunge], [0.7, P.balance], [d, mixPose(P.balance, P.freeze, 0.3)]], lt);
    const r0 = smooth(0, 0.6, lt);
    pose = addPose(pose, Object.fromEntries(Object.entries({ uarmR: [flail(t, 8, 0.8, 4), 0, flail(t, 12, 1.1, 1)], uarmL: [flail(t, 8, 0.8, 6), 0, -flail(t, 12, 1.05, 2)], farmR: [flail(t, 10, 1.2, 3), 0, 0], farmL: [flail(t, 10, 1.25, 5), 0, 0], spine2: [0, flail(t, 5, 0.6, 3), flail(t, 3, 0.7, 8)] }).map(([k, v]) => [k, v.map(x => x * r0)])));
    root.yaw = 5 * Math.sin(t * 1.3) * r0; root.roll = 2.5 * Math.sin(t * 1.7 + 1) * r0; face = { ...face, fear: 0.6, browIn: 0.6, frown: 0.35, jaw: 0.12 + 0.1 * smooth(0, 0.4, lt), look: [0, -0.4 + 0.4 * smooth(0.8, 1.6, lt)] };
  } else if (b === 1) {
    pose = keyed([[0, mixPose(P.balance, P.freeze, 0.3)], [0.35, P.flail], [d - 0.4, P.flail], [d, P.freeze]], lt);
    const k = smooth(0.2, 0.6, lt) * (1 - smooth(d - 0.6, d - 0.2, lt));
    pose = addPose(pose, { uarmR: [flail(t, 28, 2.2, 1), 0, flail(t, 22, 1.9, 4)].map(v => v * k), uarmL: [flail(t, 28, 2.1, 7), 0, -flail(t, 22, 2.0, 5)].map(v => v * k),
      farmR: [flail(t, 25, 2.3, 2) * k, 0, 0], farmL: [flail(t, 25, 2.4, 3) * k, 0, 0], spine2: [0, flail(t, 8, 1.4, 6) * k, flail(t, 5, 1.2, 9) * k],
      thighR: [flail(t, 14, 1.8, 3) * k, 0, 0], thighL: [flail(t, 14, 1.8, 6) * k, 0, 0], shinR: [-Math.abs(flail(t, 20, 1.8, 3)) * k, 0, 0], shinL: [-Math.abs(flail(t, 20, 1.8, 6)) * k, 0, 0] });
    root.yaw = flail(t, 6, 0.9, 2) * k; root.roll = flail(t, 3, 1.1, 5) * k;
    face = { ...face, fear: 1, jaw: 0.75 * k + 0.1, brow: 1, pain: 0.6 * k, frown: 0.35 * (1 - k), look: [flail(t, 0.3, 0.7, 1), 0] };
  } else if (b === 2) {
    pose = keyed([[0, P.freeze], [d, mixPose(P.freeze, P.restArms, 0.4)]], lt);
    face = { ...face, fear: 0.7, browIn: 1, jaw: 0.05, frown: 0.5, press: 0.5, look: [0, -0.5] };
  } else if (b === 3) {
    pose = keyed([[0, mixPose(P.freeze, P.restArms, 0.4)], [1.0, P.restArms], [d, P.restArms]], lt);
    pose = addPose(pose, { neck: [6 * smooth(0.8, 1.5, lt), 0, 0] });
    face = { ...face, fear: 0.2 * (1 - smooth(0.6, 1.4, lt)), brow: 0.6 * smooth(0.6, 1.4, lt), jaw: 0.08, smile: 0.55 * smooth(0.6, 1.4, lt), frown: 0.5 * (1 - smooth(0.2, 0.8, lt)), look: [0, 0.1] };
  } else if (b === 4) {
    pose = addPose(P.restArms, { uarmR: [0, 0, 3 * Math.sin(t * 2.2)], uarmL: [0, 0, -3 * Math.sin(t * 2.2 + 0.5)] });
    face = { ...face, brow: 0.3, smile: 0.25, look: [0, -0.2] };
  } else if (b === 5) {
    const k = lt / d;
    if (k < 0.5) {                            // grab a thigh under the sand and heave
      const heave = smooth(0.12, 0.3, k) * (0.5 + 0.5 * Math.sin((k - 0.12) * 40));
      pose = mixPose(keyed([[0, P.restArms], [0.35 * d * 0.5, P.tug]], lt), P.tugBack, heave * 0.7);
      face = { ...face, browIn: 1, jaw: 0.25 * heave, fear: 0.3, pain: 0.35 + 0.6 * heave, press: 0.5 * (1 - heave) };
    } else {                                  // the car: squat, grip the bumper, heave it up
      root.x = CARX; root.z = CARZ + 2.62; collar = false;
      const u = (lt - 0.5 * d) / (0.5 * d);
      const up = smooth(0.15, 0.85, u);
      pose = mixPose(P.squat, P.lift, up);
      pose = addPose(pose, { spine2: [0, flail(t, 2, 6, 1), 0], uarmR: [flail(t, 1.5, 7, 2), 0, 0] });      // strain tremor
      const legs = mixPose(P.squat, P.lift, up);
      root.s = 0.95 - hipHeight(legs);
      face = { ...face, browIn: 1, jaw: 0.2, fear: 0.2, pain: 0.9, sneer: 0.3 };
    }
  } else if (b === 6) {
    pose = keyed([[0, P.restArms], [0.6, P.lookTide], [d, P.lookTide]], lt);
    face = { ...face, fear: smooth(0.6, 1.6, lt), browIn: 0.8, jaw: 0.1 + 0.25 * smooth(1.2, 2.0, lt), frown: 0.5 * smooth(0.6, 1.6, lt), oh: 0.4 * smooth(1.2, 2.0, lt), look: [0.6, 0] };
  } else if (b === 7) {
    const k = smooth(0.2, 0.8, lt);
    pose = keyed([[0, P.lookTide], [0.5, P.wiggle], [d, P.wiggle]], lt);
    const wg = k * (1 - smooth(d - 0.4, d, lt));
    pose = addPose(pose, { thighR: [10 * Math.sin(t * 4.2) * wg, 0, 0], thighL: [10 * Math.sin(t * 4.2 + 2.6) * wg, 0, 0],
      shinR: [-Math.abs(7 * Math.sin(t * 4.2)) * wg, 0, 0], shinL: [-Math.abs(7 * Math.sin(t * 4.2 + 2.6)) * wg, 0, 0],
      footR: [12 * Math.sin(t * 4.2 + 1) * wg, 0, 0], footL: [12 * Math.sin(t * 4.2 + 3.6) * wg, 0, 0] });
    face = { ...face, browIn: 0.6, jaw: 0.05, press: 0.6, look: [0, -0.6] };
  } else if (b === 8) {
    const lean = smooth(0.1, 1.5, lt);                  // leans back until he lies flat
    const scoot = smooth(1.3, d, lt);
    pose = keyed([[0, P.wiggle], [1.2, P.float], [d, P.float]], lt);
    const pad = smooth(1.3, 1.8, lt);
    pose = addPose(pose, { uarmR: [flail(t, 12, 1.1, 1) * pad, 0, 8 * Math.sin(t * 6.9) * pad], uarmL: [flail(t, 12, 1.1, 3) * pad, 0, -8 * Math.sin(t * 6.9) * pad] });
    root.tilt = 82 * lean; root.s = lerp(0.86, 0.97, lean); root.z = 0.0 + 1.55 * scoot; collar = lean < 0.5;
    face = { ...face, browIn: 0.3 * (1 - lean), smile: 0.35 * smooth(1.6, 2.6, lt), look: [0, 0.4] };
  } else {                                              // walks back in: firm sand, then the plunge (loops to beat 0)
    const plunge = d - 0.62;
    if (lt < plunge) {
      const ph = 2 * Math.PI * 0.95 * lt, k = smooth(0.0, 0.35, lt) * (1 - smooth(plunge - 0.25, plunge, lt));
      pose = addPose(P.relief, { thighR: [22 * Math.sin(ph) * k, 0, 0], thighL: [-22 * Math.sin(ph) * k, 0, 0],
        shinR: [-(8 + 28 * Math.max(0, Math.sin(ph + 1.2))) * k, 0, 0], shinL: [-(8 + 28 * Math.max(0, Math.sin(ph + 1.2 + Math.PI))) * k, 0, 0],
        uarmR: [-16 * Math.sin(ph) * k, 0, 0], uarmL: [16 * Math.sin(ph) * k, 0, 0], spine2: [0, 4 * Math.sin(ph) * k, 0] });
      root.s = 0.012 * Math.abs(Math.sin(ph)) * k + 0.02; root.z = lerp(1.75, 0.2, lt / plunge);
      // planted feet: each foot sits still on the sand through its stance, then swings to the next footprint (leg IK)
      const f = 0.95, vz = 1.55 / plunge, feet = {};
      for (const [S, off, sx] of [['R', 0, 1], ['L', 0.5, -1]]) {
        const cyc = f * lt + off, n = Math.floor(cyc), fr = cyc - n;
        const plantZ = m => 1.75 - vz * (m - off + 0.3) / f;
        let z, y = 0.102;
        if (fr < 0.6) z = plantZ(n);
        else { const u = (fr - 0.6) / 0.4; z = lerp(plantZ(n), plantZ(n + 1), sm(u)); y += 0.07 * Math.sin(Math.PI * u); }
        feet[S] = new THREE.Vector3(0.11 * sx, y, z);
      }
      ik = { w: k, feet };
      face = { ...face, brow: 0.4, jaw: 0.05, look: [0, -0.1], smile: 0.6 * smooth(0.1, 0.6, lt) };
    } else {
      const u = (lt - plunge) / (d - plunge);
      pose = keyed([[0, P.relief], [0.38, P.plunge], [1, P.plunge]], u);
      root.s = lerp(0.02, S_KNEE, sm(clamp(u / 0.85, 0, 1))); root.z = lerp(0.2, 0, sm(u));
      face = { ...face, fear: smooth(0, 0.5, u) * 0.6, browIn: 0.6 * smooth(0, 0.5, u), jaw: 0.12 + 0.1 * Math.sin(Math.PI * clamp(u / 0.8, 0, 1)), look: [0, -0.4 * smooth(0.2, 1, u)],
        smile: 0.6 * (1 - smooth(0, 0.35, u)), oh: 0.55 * Math.sin(Math.PI * clamp(u / 0.85, 0, 1)), frown: 0.35 * smooth(0.3, 1, u) };
    }
    collar = root.s > 0.06;
  }
  return { pose, root, face, collar, ik };
}
function hipHeight(p) {                     // standing on firm ground: hip height from the thigh/shin angles
  const th = (eul(p, 'thighR')[0]) * D2R, sh = (eul(p, 'thighR')[0] + eul(p, 'shinR')[0]) * D2R;
  return 0.43 * Math.cos(th) + 0.42 * Math.cos(sh) + 0.1;
}
function blink(t) { for (const b0 of [0.9, 4.6, 9.8, 15.2, 19.9, 24.3, 28.9, 33.9]) { const u = (t - b0) / 0.16; if (u > 0 && u < 1) return Math.sin(Math.PI * u); } return 0; }

// ------------------------------------------------------------------ cameras, one shot per beat (slow push-ins, punch on cuts)
const V = (x, y, z) => new THREE.Vector3(x, y, z);
function hipW() { return G.bones.hips.getWorldPosition(new THREE.Vector3()); }
function headW() { return G.bones.head.getWorldPosition(new THREE.Vector3()); }
function shake(t, a, f = 1) { return V(vn1(t * 3 * f, 1) * a, vn1(t * 3 * f, 2) * a, vn1(t * 3 * f, 3) * a * 0.5); }
function camAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b], u = lt / d;
  let pos, tgt, fov = 42;
  const hd = headW();
  if (b === 0 || b === 9) {                      // the hook frame: low, in front, he fills the frame (beat 9 ends exactly here)
    const k = b === 0 ? u : 0;
    pos = V(0.35, 1.2 - 0.05 * k, -2.55 + 0.3 * k); tgt = V(0, 0.56, 0); fov = 44;
    const sk = b === 0 ? smooth(0, 0.6, lt) : 0;
    if (b === 9) { const w = sm(clamp((u - 0.35) / 0.65, 0, 1)); pos = V(lerp(0.7, 0.35, w), lerp(1.55, 1.2, w), lerp(-3.4, -2.55, w)); tgt = V(0, lerp(0.85, 0.56, w), lerp(0.7, 0, w)); }
    pos.add(shake(t, 0.008 * sk));
  } else if (b === 1) {                          // tight, handheld, a bit higher
    pos = V(-0.75 + 0.15 * u, 0.85, -1.55 + 0.15 * u); tgt = V(0, 0.42, 0); fov = 46; pos.add(shake(t, 0.03, 2.2));
  } else if (b === 2) {                          // cutaway, close on the legs
    pos = V(0.1, 0.1, -1.75 + 0.2 * u); tgt = V(0, -0.32, 0.05); fov = 46;
  } else if (b === 3) {                          // stopped at the waist, wide-ish, calm
    pos = V(0.9 - 0.2 * u, 0.62, -2.4 + 0.3 * u); tgt = V(0, 0.55, 0); fov = 40;
  } else if (b === 4) {                          // cutaway, whole body, arrows pushing up
    pos = V(0.0, 0.3, -3.4 + 0.35 * u); tgt = V(0, -0.05, 0.05); fov = 46;
  } else if (b === 5) {
    if (u < 0.5) { pos = V(-0.95, 0.95, -1.75 + 0.15 * u); tgt = V(0, 0.3, 0); fov = 42; pos.add(shake(t, 0.01, 2)); }
    else { const w = (u - 0.5) / 0.5; pos = V(CARX - 3.3 + 0.25 * w, 1.15, CARZ + 4.2 - 0.2 * w); tgt = V(CARX + 0.1, 0.62, CARZ + 1.8); fov = 42; }
  } else if (b === 6) {                          // behind him, the tide sliding in across the flat
    pos = V(-0.6 + 0.1 * u, 1.75, -2.4 + 0.15 * u); tgt = V(0.2, 0.25, 3.5); fov = 46;
  } else if (b === 7) {                          // cutaway, low, legs wiggling, water seeping
    pos = V(-0.3, 0.08, -1.5 + 0.12 * u); tgt = V(0, -0.5, 0.05); fov = 48;
  } else if (b === 8) {                          // high, looking down as he leans back and floats out
    const h = hipW();
    pos = V(1.3, 2.6, h.z - 1.6); tgt = V(0, 0.0, h.z + 0.4); fov = 46;
  }
  // punch: a quick zoom hit on every hard cut
  const punch = b > 0 ? (1 - smooth(0, 0.22, lt)) * 0.07 : 0;
  return { pos, tgt, fov: fov * (1 - punch), cut: (b === 2 || b === 4 || b === 7) };
}

// ------------------------------------------------------------------ per-frame update
const segPlane = (a, b, y) => { const k = (y - a.y) / (b.y - a.y); return (k >= 0 && k <= 1) ? a.clone().lerp(b, k) : null; };
function update(t) {
  t = ((t % TOTAL) + TOTAL) % TOTAL;
  const b = beatAt(t);
  const g = guyAt(t);
  applyPose(g.pose, g.root);
  if (g.ik && g.ik.w > 0.001) {              // blend the planted-foot IK over the FK legs
    const keep = {}; for (const n of ['thighR', 'shinR', 'footR', 'thighL', 'shinL', 'footL']) keep[n] = G.bones[n].quaternion.clone();
    const flat = new THREE.Quaternion().setFromEuler(new THREE.Euler(0, (g.root.yaw || 0) * D2R, 0));
    for (const S of ['R', 'L']) { const ft = g.ik.feet[S]; G.legIK(S, ft, ft.clone().add(new THREE.Vector3(0, 0.45, -1.0)), flat); }
    for (const n of Object.keys(keep)) G.bones[n].quaternion.copy(keep[n].slerp(G.bones[n].quaternion.clone(), g.ik.w));
    G.root.updateMatrixWorld(true);
  }
  G.untwist();
  G.face(g.face);
  G.root.updateMatrixWorld(true);
  // sun shadow follows the action
  const h = hipW();
  sun.position.copy(h).addScaledVector(SUNDIR, 15); sun.target.position.copy(h); sun.target.updateMatrixWorld();
  // cutaway
  const C = camAt(t);
  const cut = C.cut;
  groundMat.clippingPlanes = cut ? [clipCut] : null; waterMat.clippingPlanes = cut ? [clipCut] : null;
  cutWall.visible = cut;
  for (const c of collars) c.material.clippingPlanes = cut ? [clipCut] : null;
  // collars where legs / body go into the sand (pool surface is y = 0)
  const wp = n => G.bones[n].getWorldPosition(new THREE.Vector3());
  const items = [];
  if (g.collar && g.root.s > 0.05) {
    if (g.root.s > 0.9) items.push([h.clone().setY(0), 0.19, 0.15]);
    else for (const S of ['R', 'L']) { const p = segPlane(wp('thigh' + S), wp('shin' + S), 0) || segPlane(wp('shin' + S), wp('foot' + S), 0); if (p) items.push([p, 0.075, 0.07]); }
  }
  collars.forEach((c, i) => { const it = items[i]; c.visible = false && !!it; if (it) { c.position.copy(it[0]).setY(0.0); c.scale.set(it[1] * 1.05, 0.22, it[2] * 1.05); } });
  // ground uniforms: ripples spread from him in the pool, stronger while he thrashes
  groundU.uT.value = t * RIPFIX; waterU.uT.value = t;
  groundU.uMatte.value = (b === 5 && (t - B[5]) / DUR[5] < 0.5) ? 1 : 0;      // no sun glare on the pool in the low tug shot
  groundU.uRipC.value.set(h.x, h.z);
  groundU.uRip.value = b === 1 ? 0.6 : b === 8 ? 0.35 : b === 0 || b === 9 ? 0.25 : b === 7 ? 0.15 : 0.06;
  // tide: far away all along, sliding in during beat 6 (and held after)
  const tide = b < 6 ? 14 : b === 6 ? lerp(14, 5.5, sm((t - B[6]) / DUR[6])) : b <= 8 ? 5.5 : 14;
  waterU.uEdge.value = tide; groundU.uTide.value = tide;
  // cutaway props
  const legs = ['R', 'L'].flatMap(S => [wp('thigh' + S), wp('foot' + S)]);
  legs.forEach((p, i) => cutU.uLegs.value[i].set(p.x, p.y));
  cutU.uT.value = t;
  cutU.uPack.value = b === 2 ? smooth(0.5, 2.2, t - B[2]) : b === 4 ? 1 : b === 7 ? 1 - smooth(1.0, 3.6, t - B[7]) : 0;
  cutU.uSeep.value = b === 7 ? smooth(0.6, 1.6, t - B[7]) : 0;
  arrows.forEach((a, i) => { a.visible = b === 4; if (b === 4) { const lt = t - B[4]; const k = smooth(0.3 + i * 0.15, 0.9 + i * 0.15, lt);
    a.position.set(-0.32 + i * 0.32, -1.08 + 0.12 * Math.sin(lt * 3 + i), -0.02); a.scale.setScalar(0.001 + k); } });
  seep.visible = b === 7;
  if (b === 7) { const lt = t - B[7], ff = legs;
    for (let i = 0; i < NSEEP; i++) { const leg = i % 2, a = ff[leg * 2], f = ff[leg * 2 + 1], ph = (hash1(i * 1.7) + lt * (0.25 + 0.2 * hash1(i))) % 1;
      const p = a.clone().lerp(f, ph); const ang = hash1(i * 3.3) * 6.28; seepPos[i * 3] = p.x + Math.cos(ang) * 0.075; seepPos[i * 3 + 1] = Math.min(p.y, -0.01); seepPos[i * 3 + 2] = Math.min(p.z - 0.07, CUTZ - 0.02); }
    seepGeo.attributes.position.needsUpdate = true; seep.material.opacity = 0.85 * smooth(0.6, 1.4, lt); }
  // the car: rear bumper rides up with his hands
  carPivot.visible = b === 5 && (t - B[5]) / DUR[5] >= 0.5;
  if (carPivot.visible) {
    const hy = (wp('handR').y + wp('handL').y) / 2 - 0.04;
    const ang = Math.asin(clamp((hy - 0.42) / 2.9, -0.1, 0.2));
    carPivot.rotation.x = -ang;
  }
  sign.visible = b !== 4 && b !== 2 && b !== 7;
  // camera
  camera.position.copy(C.pos); camera.lookAt(C.tgt); camera.fov = C.fov; camera.updateProjectionMatrix();
  return { beat: b, t };
}

// ------------------------------------------------------------------ frame I/O (same contract as main.js)
// ground-truth ambient occlusion in screen space (contact shadows where he meets the sand, folds, armpits); ?ao=0 turns it off
let composer = null;
if (Q.get('ao') !== '0') {
  composer = new EffectComposer(renderer, new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: 4 }));
  composer.setPixelRatio(1); composer.setSize(W, H);
  composer.addPass(new RenderPass(scene, camera));
  const ao = new GTAOPass(scene, camera, W, H);
  ao.updateGtaoMaterial({ radius: 0.25, distanceExponent: 1, thickness: 1, scale: 1, samples: 12, distanceFallOff: 1, screenSpaceRadius: false });
  ao.updatePdMaterial({ lumaPhi: 10, depthPhi: 2, normalPhi: 3, radius: 6, rings: 2, samples: 12 });
  ao.blendIntensity = 0.85;
  composer.addPass(ao); composer.addPass(new OutputPass());
}
const draw = () => { if (composer) composer.render(); else renderer.render(scene, camera); };
const gl = renderer.getContext();
const px = new Uint8Array(W * H * 4);
function renderInto(i) { update(i / FPS); draw(); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); }
window.renderAll = async (f0, f1) => { for (let i = f0; i < f1; i++) { renderInto(i); await fetch('/frame', { method: 'POST', body: px }); } return 'ok'; };
window.renderPNG = i => { update(i / FPS); draw(); return renderer.domElement.toDataURL('image/png'); };
window.renderAtT = t => { update(t); draw(); return renderer.domElement.toDataURL('image/png'); };
window.rigReport = i => { const r = update(i / FPS); return { t: r.t, beat: r.beat, ang: LAST, hands: ['handR', 'handL'].map(n => G.bones[n].getWorldPosition(new THREE.Vector3()).toArray()),
  chest: G.bones.chest.getWorldPosition(new THREE.Vector3()).toArray(), hips: G.bones.hips.getWorldPosition(new THREE.Vector3()).toArray(), car: carPivot.visible };
};
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS);
window.READY = true;
