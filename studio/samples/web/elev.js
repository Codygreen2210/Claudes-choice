// "What happens if an elevator cable snaps" - a 3D Short with the sculpted, skinned guy in a falling elevator.
//   elev.html?w=1080&h=1920            (times from elev/times.json; one shot per narration line)
// Beats: 0 cable snapped, the car is dropping, he floats (hook) | 1 his feet float off the floor | 2 the movie trick: crouch
//        3 wide cutaway: the car streaking down the shaft | 4 he jumps, then the lights go out | 5 car top: 6 cables, one can hold it
//        6 safety brakes clamp the rails, sparks, he drops to a crouch | 7 1945: a tall tower, a car falls 75 floors
//        8 the pit: squeezed air and coiled cable slow the car | 9 he rides up calm, the cable snaps (loops into beat 0)
// World = shaft space: landing k at y = k * FH, pit floor at PIT. The car group sits at y = carH(t); cameras are given in car space.
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
const TIMES = await (await fetch('/elev/times.json')).json();
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

// ------------------------------------------------------------------ the fall: car height in the shaft, continuous through the loop
const FH = 3.05, NFL = 60, PIT = -1.6, START_FL = 58;
const G_ = 9.81, VMAX = 11;
const T_SNAP = TOTAL - 0.62;                                   // the cable snaps 0.62 s before the loop
const H0 = START_FL * FH;
const D_SEAM = 0.5 * G_ * (TOTAL - T_SNAP) ** 2, V_SEAM = G_ * (TOTAL - T_SNAP);   // drop and speed at the loop seam
const T_VMAX = (VMAX - V_SEAM) / G_;
function fallDrop(tt) {                                       // tt = time since frame 0 (beats 0-4): continues from the seam
  if (tt < T_VMAX) return D_SEAM + V_SEAM * tt + 0.5 * G_ * tt * tt;
  return D_SEAM + V_SEAM * T_VMAX + 0.5 * G_ * T_VMAX * T_VMAX + VMAX * (tt - T_VMAX);
}
const sinceSnap = t => t >= T_SNAP ? t - T_SNAP : t < B[5] ? t + (TOTAL - T_SNAP) : 99;
const B6_CLAMP = 0.42, B6_V = 9, B6_STOP = 0.38, B6_FL = 14;
function b6Drop(lt) {                                           // beat 6: falling at B6_V, brakes bite at B6_CLAMP, stopped B6_STOP later
  if (lt < B6_CLAMP) return B6_V * lt;
  const u = Math.min(lt - B6_CLAMP, B6_STOP), a = B6_V / B6_STOP;
  return B6_V * B6_CLAMP + B6_V * u - 0.5 * a * u * u;
}
function carH(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  if (b <= 4) return H0 - fallDrop(t);
  if (b === 5) return 22 * FH + 0.006 * Math.sin(t * 2.3);
  if (b === 6) return B6_FL * FH - b6Drop(lt);
  if (b === 7) return 22 * FH;
  if (b === 8) { const u = clamp(lt / (d * 0.82), 0, 1); return lerp(5.2, PIT + 0.62 + 0.16, 1 - (1 - u) ** 2.6); }
  return t < T_SNAP ? H0 : H0 - 0.5 * G_ * (t - T_SNAP) ** 2;
}
const falling = t => { const b = beatAt(t); return b <= 4 || (b === 6 && t - B[6] < B6_CLAMP + B6_STOP) || t >= T_SNAP; };

// ------------------------------------------------------------------ renderer / scene / light
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(W, H);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.localClippingEnabled = true;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x07080a);
const camera = new THREE.PerspectiveCamera(42, W / H, 0.03, 3000);
{ // environment for the steel walls and chrome: a soft warm room
  const pm = new THREE.PMREMGenerator(renderer); const es = new THREE.Scene();
  es.add(new THREE.Mesh(new THREE.SphereGeometry(10, 32, 16), new THREE.MeshBasicMaterial({ color: 0x8a8f99, side: THREE.BackSide })));
  const pan = (c, x, y, z, sx, sy) => { const m = new THREE.Mesh(new THREE.PlaneGeometry(sx, sy), new THREE.MeshBasicMaterial({ color: c, side: THREE.DoubleSide })); m.position.set(x, y, z); m.lookAt(0, 0, 0); es.add(m); };
  pan(0xffffff, 0, 9, 0, 8, 3); pan(0xfff2dc, 6, 3, -4, 4, 6); pan(0x405060, -7, 1, 3, 6, 8); pan(0x202226, 0, -9, 0, 20, 20);
  scene.environment = pm.fromScene(es, 0.03).texture; scene.environmentIntensity = 0.7;
}
const hemi = new THREE.HemisphereLight(0x9fb2c8, 0x2a2622, 0.35); scene.add(hemi);

function canvasTex(w, h, draw) { const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), c); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t; }

// ------------------------------------------------------------------ the shaft (front cut away), the building section around it
const SX = 1.34, SZB = 1.0, SZF = -1.02, RAILX = 1.2;
const shaft = new THREE.Group(); scene.add(shaft);
const TOPY = NFL * FH + 3.2;
const wallU = { uFH: { value: FH } };
function concreteMat(base, opts = {}) {
  const m = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.92, metalness: 0, ...opts });
  m.onBeforeCompile = sh => {
    Object.assign(sh.uniforms, wallU);
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vW;')
      .replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvW = (modelMatrix * vec4(transformed, 1.0)).xyz;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', `#include <common>
varying vec3 vW; uniform float uFH;
float hh(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
float vn(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f*f*(3.0-2.0*f);
  return mix(mix(hh(i), hh(i+vec2(1,0)), u.x), mix(hh(i+vec2(0,1)), hh(i+vec2(1,1)), u.x), u.y); }`)
      .replace('#include <color_fragment>', `#include <color_fragment>
  { vec2 P = vec2(vW.x + vW.z, vW.y);
    float fy = mod(vW.y, uFH);
    float slab = 1.0 - smoothstep(0.0, 0.02, abs(fy - 0.12) - 0.16);          // a floor slab band at every landing
    float form = step(0.985, fract(vW.y / 1.22 + 0.3)) + step(0.99, fract((vW.x + vW.z) / 1.2 + 0.1));   // formwork joints
    vec3 c = vec3(${base.map(v => v.toFixed(3)).join(',')});
    c *= 0.82 + 0.22 * vn(P * 1.3) + 0.08 * vn(P * 9.0);
    c = mix(c, c * 1.25 + 0.03, slab);
    c *= 1.0 - 0.25 * clamp(form, 0.0, 1.0);
    float stain = smoothstep(0.55, 0.8, vn(vec2(P.x * 3.0, P.y * 0.25))) * smoothstep(0.0, 1.0, fy / uFH);  // drips under each slab
    c *= 1.0 - 0.18 * stain;
    diffuseColor.rgb = c; }`);
  };
  return m;
}
const wallMat = concreteMat([0.36, 0.355, 0.34]);
const shaftH = TOPY - PIT;
for (const s of [1, -1]) { const w = new THREE.Mesh(new THREE.BoxGeometry(2.4, shaftH, SZB - SZF + 0.5), wallMat); w.position.set(s * (SX + 1.2), PIT + shaftH / 2, (SZB + SZF) / 2 + 0.25); w.receiveShadow = true; shaft.add(w); }
{ const w = new THREE.Mesh(new THREE.BoxGeometry(2 * SX + 0.2, shaftH, 0.4), wallMat); w.position.set(0, PIT + shaftH / 2, SZB + 0.2); w.receiveShadow = true; shaft.add(w); }
{ const f = new THREE.Mesh(new THREE.BoxGeometry(2 * SX + 4.8, 0.5, SZB - SZF + 0.6), wallMat); f.position.set(0, PIT - 0.25, (SZB + SZF) / 2); f.receiveShadow = true; shaft.add(f); }
// the cut face of the building around the shaft (section, facing the camera): slabs at every floor, hatched like a drawing
const cutU = { uFH: { value: FH } };
const cutMat = new THREE.ShaderMaterial({ uniforms: cutU,
  vertexShader: 'varying vec3 vW; void main(){ vW = (modelMatrix * vec4(position, 1.0)).xyz; gl_Position = projectionMatrix * viewMatrix * vec4(vW, 1.0); }',
  fragmentShader: `varying vec3 vW; uniform float uFH;
  float hh(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
  void main(){ float fy = mod(vW.y, uFH);
    vec3 c = vec3(0.30, 0.29, 0.28) * (0.85 + 0.2 * hh(floor(vW.xy * 90.0)));
    float slab = step(fy, 0.3);                                                   // floor slab cut
    c = mix(c, vec3(0.48, 0.46, 0.43), slab);
    c = mix(c, vec3(0.12, 0.11, 0.105), (1.0 - step(0.012, abs(fy - 0.3))) + (1.0 - step(0.012, fy)));
    float hatch = step(0.82, fract((vW.x + vW.y) * 9.0)) * (1.0 - slab);         // section hatching
    c *= 1.0 - 0.18 * hatch;
    c *= 1.0 - 0.5 * smoothstep(${SX.toFixed(2)} + 0.8, ${SX.toFixed(2)} + 2.3, abs(vW.x));   // falls off into the dark at the sides
    gl_FragColor = vec4(c, 1.0);
    #include <tonemapping_fragment>
    #include <colorspace_fragment>
  }` });
for (const s of [1, -1]) { const c = new THREE.Mesh(new THREE.PlaneGeometry(2.4, shaftH), cutMat); c.position.set(s * (SX + 1.2), PIT + shaftH / 2, SZF - 0.001); c.rotation.y = Math.PI; shaft.add(c); }
// guide rails (steel T-section) on both side walls, with brackets every landing
const railMat = new THREE.MeshStandardMaterial({ color: 0x8d9298, metalness: 0.85, roughness: 0.32 });
const bracketMat = new THREE.MeshStandardMaterial({ color: 0x3b4046, metalness: 0.6, roughness: 0.6 });
for (const s of [1, -1]) {
  const blade = new THREE.Mesh(new THREE.BoxGeometry(0.11, shaftH, 0.016), railMat); blade.position.set(s * (RAILX + 0.055), PIT + shaftH / 2, 0); shaft.add(blade);
  const foot = new THREE.Mesh(new THREE.BoxGeometry(0.014, shaftH, 0.13), railMat); foot.position.set(s * (RAILX + 0.11), PIT + shaftH / 2, 0); shaft.add(foot);
  const brk = new THREE.InstancedMesh(new THREE.BoxGeometry(0.13, 0.16, 0.2), bracketMat, NFL + 2); const m4 = new THREE.Matrix4();
  for (let k = 0; k <= NFL + 1; k++) { m4.makeTranslation(s * (SX - 0.03), k * FH + 1.6, 0); brk.setMatrixAt(k, m4); } shaft.add(brk);
}
// back wall: conduit, a junction box and a stenciled floor number at every landing, a work light every other floor
{ const pipe = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, shaftH, 10), new THREE.MeshStandardMaterial({ color: 0x6b6f72, metalness: 0.5, roughness: 0.5 }));
  pipe.position.set(-0.78, PIT + shaftH / 2, SZB - 0.05); shaft.add(pipe);
  const box = new THREE.InstancedMesh(new THREE.BoxGeometry(0.22, 0.28, 0.08), new THREE.MeshStandardMaterial({ color: 0x5d6168, metalness: 0.4, roughness: 0.6 }), NFL + 1);
  const lamp = new THREE.InstancedMesh(new THREE.BoxGeometry(0.42, 0.06, 0.06), new THREE.MeshStandardMaterial({ color: 0x222222, emissive: 0xfff1d6, emissiveIntensity: 2.2 }), NFL + 1);
  const m4 = new THREE.Matrix4(); let nl = 0;
  for (let k = 0; k <= NFL; k++) { m4.makeTranslation(-0.78, k * FH + 1.1, SZB - 0.06); box.setMatrixAt(k, m4);
    if (k % 2 === 0) { m4.makeTranslation(0.35, k * FH + 2.55, SZB - 0.04); lamp.setMatrixAt(nl++, m4); } }
  lamp.count = nl; shaft.add(box); shaft.add(lamp); }
const numAtlas = canvasTex(1024, 1024, g => {             // 8 x 8 cells of stenciled floor numbers (yellow paint)
  g.clearRect(0, 0, 1024, 1024); g.textAlign = 'center'; g.textBaseline = 'middle';
  for (let k = 0; k <= 63; k++) { const cx = (k % 8) * 128 + 64, cy = Math.floor(k / 8) * 128 + 64;
    g.fillStyle = '#e8b52a'; g.font = 'bold 84px Inter, Arial, sans-serif'; g.fillText(String(k === 0 ? 'P' : k), cx, cy + 4);
    g.globalCompositeOperation = 'destination-out'; g.fillStyle = '#000'; for (let i = 0; i < 9; i++) g.fillRect(cx - 60, cy - 40 + i * 9 + (k % 3), 120, 1.5); g.globalCompositeOperation = 'source-over'; }
});
for (let k = 0; k <= NFL; k++) {
  const geo = new THREE.PlaneGeometry(0.62, 0.62); const uv = geo.attributes.uv;
  const cx = k % 8, cy = Math.floor(k / 8);
  for (let i = 0; i < uv.count; i++) uv.setXY(i, (cx + uv.getX(i)) / 8, 1 - (cy + 1 - uv.getY(i)) / 8);
  const m = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ map: numAtlas, transparent: true, roughness: 0.8, depthWrite: false }));
  m.position.set(0.48, k * FH + 1.45, SZB - 0.004); m.rotation.y = Math.PI; shaft.add(m);
}
// pit: buffers on the floor
{ const bm = new THREE.MeshStandardMaterial({ color: 0xc9a227, metalness: 0.3, roughness: 0.5 });
  for (const x of [-0.55, 0.55]) { const b = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.14, 0.42, 20), bm); b.position.set(x, PIT + 0.21, 0.35); b.castShadow = true; shaft.add(b); } }

// ------------------------------------------------------------------ the car (front wall cut away), its frame, brakes and hitch
const CX = 0.98, CZ = 0.78, CH = 2.36;                       // inner half width, inner half depth, ceiling height
const car = new THREE.Group(); scene.add(car);
const steel = new THREE.MeshStandardMaterial({ color: 0xb9bec5, metalness: 0.88, roughness: 0.34 });
const steelDark = new THREE.MeshStandardMaterial({ color: 0x80868e, metalness: 0.85, roughness: 0.4 });
const frameMat = new THREE.MeshStandardMaterial({ color: 0x2f3338, metalness: 0.6, roughness: 0.55 });
const chrome = new THREE.MeshStandardMaterial({ color: 0xeeeeee, metalness: 1, roughness: 0.12 });
const cutEdge = new THREE.MeshStandardMaterial({ color: 0x1a1c1f, roughness: 0.7 });
const T = 0.05;
const flTex = canvasTex(512, 512, g => {                    // rubber coin floor tiles
  g.fillStyle = '#3a3c40'; g.fillRect(0, 0, 512, 512);
  for (let y = 0; y < 512; y += 32) for (let x = (y / 32) % 2 * 16; x < 512; x += 32) { g.fillStyle = '#45484d'; g.beginPath(); g.arc(x + 8, y + 8, 7, 0, 7); g.fill(); }
  g.strokeStyle = '#2a2b2e'; g.lineWidth = 4; for (let i = 0; i <= 512; i += 256) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i, 512); g.stroke(); g.beginPath(); g.moveTo(0, i); g.lineTo(512, i); g.stroke(); }
});
flTex.wrapS = flTex.wrapT = THREE.RepeatWrapping; flTex.repeat.set(2, 1.6);
{ const floor = new THREE.Mesh(new THREE.BoxGeometry(2 * CX + 2 * T, 0.12, 2 * CZ + T), new THREE.MeshStandardMaterial({ map: flTex, roughness: 0.75 }));
  floor.position.set(0, -0.06, T / 2); floor.receiveShadow = true; car.add(floor);
  const ceil = new THREE.Mesh(new THREE.BoxGeometry(2 * CX + 2 * T, 0.08, 2 * CZ + T), steelDark); ceil.position.set(0, CH + 0.04, T / 2); ceil.receiveShadow = true; car.add(ceil);
  // walls in 3 brushed panels each (seams read as an elevator)
  const panel = (w, h, d, x, y, z) => { const m = new THREE.Mesh(new RoundedBoxGeometry(w, h, d, 2, 0.006), steel); m.position.set(x, y, z); m.receiveShadow = true; m.castShadow = true; car.add(m); };
  const pw = (2 * CX) / 3;
  for (let i = 0; i < 3; i++) panel(pw - 0.008, CH - 0.02, T, -CX + pw * (i + 0.5), CH / 2, CZ + T / 2);
  const pd = (2 * CZ) / 3;
  for (const s of [1, -1]) for (let i = 0; i < 3; i++) panel(T, CH - 0.02, pd - 0.008, s * (CX + T / 2), CH / 2, -CZ + pd * (i + 0.5));
  // kick plates and the cut edges of the front (dark trim where the wall was sliced off)
  for (const s of [1, -1]) { const e = new THREE.Mesh(new THREE.BoxGeometry(T + 0.01, CH + 0.12, 0.012), cutEdge); e.position.set(s * (CX + T / 2), CH / 2, -CZ - 0.006); car.add(e); }
  { const e = new THREE.Mesh(new THREE.BoxGeometry(2 * CX + 2 * T, 0.13, 0.012), cutEdge); e.position.set(0, -0.06, -CZ - 0.006); car.add(e);
    const e2 = new THREE.Mesh(new THREE.BoxGeometry(2 * CX + 2 * T, 0.09, 0.012), cutEdge); e2.position.set(0, CH + 0.04, -CZ - 0.006); car.add(e2); }
  // handrail on the back wall
  const rail = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 2 * CX - 0.3, 16).rotateZ(Math.PI / 2), chrome); rail.position.set(0, 0.92, CZ - 0.07); car.add(rail);
  for (const x of [-CX + 0.25, 0, CX - 0.25]) { const so = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 0.07, 10).rotateX(Math.PI / 2), chrome); so.position.set(x, 0.92, CZ - 0.035); car.add(so); }
}
// ceiling light panel (emissive) + the real lights
const lightPanelMat = new THREE.MeshStandardMaterial({ color: 0x111111, emissive: 0xfff3df, emissiveIntensity: 2.4 });
{ const lp = new THREE.Mesh(new THREE.BoxGeometry(1.2, 0.02, 0.8), lightPanelMat); lp.position.set(0, CH - 0.01, 0.0); car.add(lp); }
const carLight = new THREE.SpotLight(0xfff0dc, 14, 6, 1.25, 0.8, 1.2); carLight.position.set(0, CH - 0.05, -0.1); carLight.target.position.set(0, 0, 0.1);
carLight.castShadow = true; carLight.shadow.mapSize.set(1024, 1024); carLight.shadow.bias = -0.0005; carLight.shadow.normalBias = 0.02; carLight.shadow.camera.near = 0.2;
car.add(carLight); car.add(carLight.target);
const carFill = new THREE.PointLight(0xffe8d0, 2.2, 5, 1.5); carFill.position.set(0, 1.4, -1.4); car.add(carFill);
const emLight = new THREE.PointLight(0xff2a1a, 0, 4, 1.6); emLight.position.set(-CX + 0.15, 2.1, CZ - 0.2); car.add(emLight);
const emLamp = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.05, 0.03), new THREE.MeshStandardMaterial({ color: 0x330000, emissive: 0xff2010, emissiveIntensity: 0 })); emLamp.position.set(-CX + 0.15, 2.18, CZ - 0.02); car.add(emLamp);
// floor display (LED, above the handrail) and the button panel on a side wall
const dispCan = document.createElement('canvas'); dispCan.width = 256; dispCan.height = 112;
const dispTex = new THREE.CanvasTexture(dispCan); dispTex.colorSpace = THREE.SRGBColorSpace;
let dispKey = '';
function drawDisplay(fl, down, on) {
  const key = fl + '|' + down + '|' + on; if (key === dispKey) return; dispKey = key;
  const g = dispCan.getContext('2d'); g.fillStyle = '#0b0b0c'; g.fillRect(0, 0, 256, 112);
  if (on) { g.fillStyle = '#ff4428'; g.shadowColor = '#ff3018'; g.shadowBlur = 12;
    g.font = 'bold 84px "DejaVu Sans Mono", monospace'; g.textAlign = 'right'; g.textBaseline = 'middle'; g.fillText(String(fl), 236, 60);
    if (down) { g.beginPath(); g.moveTo(22, 34); g.lineTo(78, 34); g.lineTo(50, 82); g.closePath(); g.fill(); } }
  dispTex.needsUpdate = true;
}
{ const fr = new THREE.Mesh(new RoundedBoxGeometry(0.5, 0.25, 0.03, 2, 0.01), frameMat); fr.position.set(0, 2.02, CZ - 0.01); car.add(fr);
  const sc = new THREE.Mesh(new THREE.PlaneGeometry(0.44, 0.19), new THREE.MeshBasicMaterial({ map: dispTex, toneMapped: false })); sc.position.set(0, 2.02, CZ - 0.027); sc.rotation.y = Math.PI; car.add(sc);
  const bp = new THREE.Mesh(new RoundedBoxGeometry(0.03, 0.62, 0.22, 2, 0.008), steelDark); bp.position.set(CX - 0.01, 1.2, -CZ + 0.22); car.add(bp);
  const btnMat = new THREE.MeshStandardMaterial({ color: 0xcfd3d8, metalness: 0.9, roughness: 0.25 }), ringMat = new THREE.MeshStandardMaterial({ color: 0x111111, emissive: 0x6fb8ff, emissiveIntensity: 1.2 });
  for (let i = 0; i < 6; i++) for (let j = 0; j < 2; j++) { const b = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.018, 0.012, 16).rotateZ(Math.PI / 2), i === 1 && j === 0 ? ringMat : btnMat); b.position.set(CX - 0.03, 1.0 + i * 0.07, -CZ + 0.17 + j * 0.1); car.add(b); }
  // the one Easter egg: an inspection certificate with a small subscribe sticker, on the side wall
  const cert = canvasTex(256, 320, g => { g.fillStyle = '#f4f0e4'; g.fillRect(0, 0, 256, 320); g.strokeStyle = '#7a6a40'; g.lineWidth = 6; g.strokeRect(8, 8, 240, 304);
    g.fillStyle = '#333'; g.font = 'bold 22px Inter, Arial'; g.textAlign = 'center'; g.fillText('CERTIFICATE', 128, 48); g.fillText('OF INSPECTION', 128, 76);
    g.fillStyle = '#888'; for (let i = 0; i < 6; i++) g.fillRect(36, 110 + i * 22, 184 - (i % 3) * 30, 6);
    g.fillStyle = '#e02020'; g.beginPath(); g.roundRect(48, 254, 160, 42, 21); g.fill(); g.fillStyle = '#fff'; g.font = 'bold 22px Inter, Arial'; g.fillText('SUBSCRIBE', 128, 283); });
  const cm = new THREE.Mesh(new THREE.PlaneGeometry(0.2, 0.25), new THREE.MeshStandardMaterial({ map: cert, roughness: 0.6 })); cm.position.set(CX - 0.002, 1.5, CZ - 0.45); cm.rotation.y = -Math.PI / 2; car.add(cm); }
// outside the car: sling frame, platform beams, guide shoes, safety brakes, crosshead + rope hitch
const SAFE = [];                                             // safety brake jaws (clamp onto the rails in beat 6)
{ const ext = (w, h, d, x, y, z, m = frameMat) => { const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m); b.position.set(x, y, z); b.castShadow = true; b.receiveShadow = true; car.add(b); return b; };
  ext(2 * CX + 0.5, 0.16, 0.2, 0, -0.2, 0);                  // platform plank
  ext(2 * CX + 0.5, 0.18, 0.2, 0, CH + 0.22, 0);             // crosshead
  for (const s of [1, -1]) { ext(0.1, CH + 0.6, 0.16, s * (CX + 0.17), CH / 2, 0);   // stiles
    for (const y of [-0.2, CH + 0.22]) { ext(0.12, 0.14, 0.12, s * (RAILX - 0.05), y, 0, steelDark); }   // guide shoes around the rail
    const jaw = new THREE.Group(); jaw.position.set(s * (RAILX - 0.02), -0.36, 0);
    const blk = new THREE.Mesh(new THREE.BoxGeometry(0.17, 0.17, 0.17), new THREE.MeshStandardMaterial({ color: 0xb02a1e, metalness: 0.4, roughness: 0.5 })); jaw.add(blk);
    const wedges = [];
    for (const zz of [1, -1]) { const w = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.16, 0.035), steelDark); w.position.set(s * 0.06, -0.02, zz * 0.06); jaw.add(w); wedges.push([w, zz]); }
    jaw.traverse(o => { if (o.isMesh) o.castShadow = true; });
    car.add(jaw); SAFE.push({ jaw, wedges, s }); }
  const hitch = ext(0.42, 0.06, 0.16, 0, CH + 0.34, 0.1, steelDark); hitch.name = 'hitch';
}
// emergency glow ring for the brakes (sparks are points)
const NSP = 420;
const spGeo = new THREE.BufferGeometry(); const spPos = new Float32Array(NSP * 3), spCol = new Float32Array(NSP * 3);
spGeo.setAttribute('position', new THREE.BufferAttribute(spPos, 3)); spGeo.setAttribute('color', new THREE.BufferAttribute(spCol, 3));
const dotTex = canvasTex(64, 64, g => { const gr = g.createRadialGradient(32, 32, 0, 32, 32, 30); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.35, 'rgba(255,255,255,0.8)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); });
const sparks = new THREE.Points(spGeo, new THREE.PointsMaterial({ map: dotTex, alphaTest: 0.01, size: 0.045, vertexColors: true, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false }));
sparks.frustumCulled = false; scene.add(sparks);
const stGeo = new THREE.BufferGeometry(); const stPos = new Float32Array(NSP * 6), stCol = new Float32Array(NSP * 6);
stGeo.setAttribute('position', new THREE.BufferAttribute(stPos, 3)); stGeo.setAttribute('color', new THREE.BufferAttribute(stCol, 3));
const streaks = new THREE.LineSegments(stGeo, new THREE.LineBasicMaterial({ vertexColors: true, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false }));
streaks.frustumCulled = false; scene.add(streaks);
const sparkLight = new THREE.PointLight(0xffa040, 0, 3, 1.5); scene.add(sparkLight);

// ------------------------------------------------------------------ hoist ropes: 6 steel cables; snapped ends; the coil in the pit
const NROPE = 6, ROPEX = i => (i - (NROPE - 1) / 2) * 0.065, ROPEZ = 0.1, HITCHY = CH + 0.37;
const ropeTex = canvasTex(64, 256, g => { g.fillStyle = '#6d7175'; g.fillRect(0, 0, 64, 256); for (let y = -64; y < 320; y += 10) { g.strokeStyle = '#9ea3a8'; g.lineWidth = 3; g.beginPath(); g.moveTo(0, y); g.lineTo(64, y + 26); g.stroke(); g.strokeStyle = '#3d4044'; g.lineWidth = 1.5; g.beginPath(); g.moveTo(0, y + 5); g.lineTo(64, y + 31); g.stroke(); } });
ropeTex.wrapS = ropeTex.wrapT = THREE.RepeatWrapping;
const ropeMats = [], ropes = [];
for (let i = 0; i < NROPE; i++) {
  const m = new THREE.MeshStandardMaterial({ map: ropeTex, metalness: 0.8, roughness: 0.38, emissive: 0xffc23a, emissiveIntensity: 0, transparent: true });
  ropeMats.push(m);
  const r = new THREE.Mesh(new THREE.CylinderGeometry(0.014, 0.014, 1, 10, 1, true).translate(0, 0.5, 0), m);
  r.castShadow = true; scene.add(r); ropes.push(r);
}
// snapped stubs on the car (two short, whipping, frayed) and the upper rope ends left hanging
const stubMat = new THREE.MeshStandardMaterial({ map: ropeTex, metalness: 0.8, roughness: 0.38 });
const stubs = [0, 1, 2].map(() => { const m = new THREE.Mesh(new THREE.BufferGeometry(), stubMat); m.castShadow = true; scene.add(m); return m; });
const frayMat = new THREE.MeshStandardMaterial({ color: 0xa9adb2, metalness: 0.9, roughness: 0.3 });
function frayTuft() { const g = new THREE.Group(); for (let i = 0; i < 7; i++) { const w = new THREE.Mesh(new THREE.CylinderGeometry(0.003, 0.003, 0.09 + 0.06 * hash1(i * 3.3), 4).translate(0, 0.05, 0), frayMat); w.rotation.set((hash1(i) - 0.5) * 1.6, 0, (hash1(i * 7) - 0.5) * 1.6); g.add(w); } scene.add(g); return g; }
const stubFray = stubs.map(() => frayTuft());
const topFray = [0, 1, 2, 3, 4, 5].map(() => frayTuft());
function stubGeo(pts) { return new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 16, 0.016, 8, false); }
// the coil of cable piling up in the pit (beat 8)
const coilMat = new THREE.MeshStandardMaterial({ map: ropeTex, metalness: 0.8, roughness: 0.4 });
const coils = [];
for (let i = 0; i < 14; i++) { const r = 0.32 + 0.06 * hash1(i * 2.7) - 0.012 * i;
  const c = new THREE.Mesh(new THREE.TorusGeometry(r, 0.014, 8, 48).rotateX(Math.PI / 2), coilMat);
  c.position.set(0.04 * (hash1(i) - 0.5), PIT + 0.016 + i * 0.026, 0.1 + 0.05 * (hash1(i * 5) - 0.5)); c.rotation.z = 0.06 * (hash1(i * 9) - 0.5); c.castShadow = true; c.receiveShadow = true; c.visible = false; scene.add(c); coils.push(c); }
// air under the car (beat 8): white arrows pushing up, plus streaks
const arrowMat = new THREE.MeshStandardMaterial({ color: 0xdff4ff, emissive: 0x6fb8ff, emissiveIntensity: 0.9, transparent: true, opacity: 0.9 });
const airArrows = [];
for (let i = 0; i < 4; i++) { const g = new THREE.Group();
  const sh = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.34, 16), arrowMat); sh.position.y = 0.17; g.add(sh);
  const hd = new THREE.Mesh(new THREE.ConeGeometry(0.08, 0.15, 20), arrowMat); hd.position.y = 0.41; g.add(hd);
  g.visible = false; scene.add(g); airArrows.push(g); }
// dust streaming past in the shaft (car space, wraps; sells the speed)
const NDUST = 380;
const dGeo = new THREE.BufferGeometry(); const dPos = new Float32Array(NDUST * 3 * 2);
dGeo.setAttribute('position', new THREE.BufferAttribute(dPos, 3));
const dust = new THREE.LineSegments(dGeo, new THREE.LineBasicMaterial({ color: 0xcfd6dd, transparent: true, opacity: 0.4, depthWrite: false }));
dust.frustumCulled = false; scene.add(dust);

// ------------------------------------------------------------------ 1945: a tall stepped tower in the fog (beat 7)
const TX = 0, TZ = 2400;                                     // far from the shaft, so neither shows in the other's shots
const tower = new THREE.Group(); tower.position.set(TX, 0, TZ); scene.add(tower);
const towerU = { uT: { value: 0 } };
const facade = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.85 });
facade.onBeforeCompile = sh => {
  Object.assign(sh.uniforms, towerU);
  sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vW; varying vec3 vN;')
    .replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvW = (modelMatrix * vec4(transformed, 1.0)).xyz; vN = normalize(mat3(modelMatrix) * objectNormal);');
  sh.fragmentShader = sh.fragmentShader.replace('#include <common>', `#include <common>
varying vec3 vW; varying vec3 vN; uniform float uT;
float hh(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }`)
    .replace('#include <color_fragment>', `#include <color_fragment>
  float side = abs(vN.x) > 0.5 ? vW.z : vW.x; float up = abs(vN.y);
  vec2 cell = vec2(side / 2.6, vW.y / 3.9);
  vec2 f = fract(cell); vec2 id = floor(cell);
  float win = step(0.22, f.x) * step(f.x, 0.78) * step(0.2, f.y) * step(f.y, 0.82) * (1.0 - up);
  float pier = step(0.92, fract(side / 7.8));
  vec3 stone = vec3(0.30, 0.29, 0.28) * (0.9 + 0.15 * hh(id * 0.37));
  float lit = step(0.86, hh(id + 3.1));
  vec3 glass = mix(vec3(0.06, 0.07, 0.09), vec3(1.0, 0.78, 0.45), lit);
  diffuseColor.rgb = mix(stone, glass, win * (1.0 - pier));
  totalEmissiveRadiance += vec3(1.0, 0.78, 0.45) * win * (1.0 - pier) * lit * 0.8;`);
};
const TWR = [[0, 22, 60, 44], [22, 80, 52, 38], [80, 255, 44, 30], [255, 300, 36, 24], [300, 330, 26, 18], [330, 352, 16, 12], [352, 362, 9, 7]];   // [y0, y1, width, depth]
for (const [y0, y1, w, d] of TWR) { const m = new THREE.Mesh(new THREE.BoxGeometry(w, y1 - y0, d), facade); m.position.set(0, (y0 + y1) / 2, -22 + d / 2); tower.add(m); }
{ const sp = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 3.2, 60, 12), new THREE.MeshStandardMaterial({ color: 0x8a8a88, roughness: 0.6, metalness: 0.3 })); sp.position.y = 392; tower.add(sp); }
// the shaft cutaway: a glowing slot down the front, and the car (a bright box, made big enough to read)
const TFH = 3.9, TSTART = 80, TEND = 5;                     // 75 floors: 80th down to the 5th... drawn as floor 80 -> 5
const slot = new THREE.Mesh(new THREE.PlaneGeometry(4.2, (TSTART - 0) * TFH + 6), new THREE.MeshBasicMaterial({ color: 0x0c1218, toneMapped: false }));
slot.position.set(6, (TSTART * TFH + 6) / 2, -22.05); slot.rotation.y = Math.PI; tower.add(slot);
const slotEdge = new THREE.Mesh(new THREE.PlaneGeometry(4.8, (TSTART - 0) * TFH + 6.6), new THREE.MeshBasicMaterial({ color: 0xffb53a, toneMapped: false }));
slotEdge.position.set(6, (TSTART * TFH + 6) / 2, -22.04); slotEdge.rotation.y = Math.PI; tower.add(slotEdge);
slot.position.z = -22.06;
const tCar = new THREE.Mesh(new THREE.BoxGeometry(3.6, 4.6, 1), new THREE.MeshBasicMaterial({ color: 0xfff6e0, toneMapped: false })); tCar.position.set(6, TSTART * TFH, -22.3); tower.add(tCar);
const tTrail = new THREE.Mesh(new THREE.PlaneGeometry(2.6, 1), new THREE.MeshBasicMaterial({ color: 0xffe2a0, transparent: true, opacity: 0.55, toneMapped: false, depthWrite: false })); tTrail.rotation.y = Math.PI; tower.add(tTrail);
// a few low buildings around the base
{ const inst = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 1, 1), new THREE.MeshStandardMaterial({ color: 0x3a3e44, roughness: 0.9 }), 70); const m4 = new THREE.Matrix4(); let k = 0;
  for (let i = 0; i < 200 && k < 70; i++) { const x = (hash1(i * 3.1) - 0.5) * 520, z = (hash1(i * 7.7) - 0.5) * 520 + 60; if (Math.abs(x) < 50 && Math.abs(z) < 50) continue; if (z < -60 && Math.abs(x) < 120) continue;
    const h = 20 + hash1(i * 1.3) * 90, w = 20 + hash1(i * 2.1) * 25; m4.compose(V(x, h / 2, z), new THREE.Quaternion(), V(w, h, w * 0.8)); inst.setMatrixAt(k++, m4); }
  inst.count = k; tower.add(inst); }
const towerGround = new THREE.Mesh(new THREE.PlaneGeometry(3000, 3000).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0x202326, roughness: 1 })); tower.add(towerGround);
const towerSky = new THREE.Mesh(new THREE.SphereGeometry(1400, 32, 16), new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false,
  vertexShader: 'varying vec3 vD; void main(){ vD = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
  fragmentShader: 'varying vec3 vD; void main(){ float h = clamp(vD.y, 0.0, 1.0); vec3 c = mix(vec3(0.56, 0.58, 0.6), vec3(0.22, 0.26, 0.32), smoothstep(0.0, 0.5, h)); gl_FragColor = vec4(pow(c, vec3(2.2)), 1.0); }' }));
tower.add(towerSky);
const towerSun = new THREE.DirectionalLight(0xdfe6ee, 1.2); towerSun.position.set(TX - 300, 500, TZ - 600); towerSun.target.position.set(TX, 150, TZ); scene.add(towerSun); scene.add(towerSun.target);
const fogT = new THREE.Fog(0x7d858c, 120, 1100);

// ------------------------------------------------------------------ the guy
const G = await loadGuy(THREE, '/char/guy', {});
scene.add(G.root); G.root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
const HIP = V(0.0, 0.95, 0.0);
const GZ = 0.12;                                            // where he stands in the car (z)
function untwistSafe() {                                     // guy3d's untwist isn't idempotent: fold any split twist back first
  for (const S of ['R', 'L']) { const ua = G.bones['uarm' + S], ut = G.bones['uarmTwist' + S]; ua.quaternion.multiply(ut.quaternion); ut.quaternion.identity(); }
  G.untwist();
}

// ------------------------------------------------------------------ rig: local joint angles (deg), human limits, blending
// axes (rest A-pose): thigh +x = hip flex; shin -x = knee flex; foot +x = toes up; spine -x = bend forward;
// uarm +x = arm forward, uarm z = raise (R +, L -); farm +x = elbow flex; neck/head y = turn, x = nod (+ = up/back)
const LIMITS = {
  spine1: [[-30, 20], [-20, 20], [-15, 15]], spine2: [[-30, 20], [-20, 20], [-15, 15]], chest: [[-25, 20], [-20, 20], [-15, 15]],
  neck: [[-35, 35], [-50, 50], [-20, 20]], head: [[-30, 30], [-40, 40], [-20, 20]],
  uarmR: [[-50, 170], [-60, 60], [-25, 170]], uarmL: [[-50, 170], [-60, 60], [-170, 25]],
  farmR: [[0, 145], [-80, 80], [-5, 5]], farmL: [[0, 145], [-80, 80], [-5, 5]],
  handR: [[-60, 60], [-25, 25], [-60, 60]], handL: [[-60, 60], [-25, 25], [-60, 60]],
  thighR: [[-30, 120], [-30, 30], [-25, 45]], thighL: [[-30, 120], [-30, 30], [-45, 25]],
  shinR: [[-150, 0], [-5, 5], [-5, 5]], shinL: [[-150, 0], [-5, 5], [-5, 5]],
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
// arms are given as human joint angles armR / armL = [forward raise, side raise, upper-arm roll, elbow, forearm roll] (deg),
// the same model as mold.js (shoulder -50..170 / -25..170, roll +-60, elbow hinge 0..145, forearm roll +-80)
const ARM_LIM = [[-50, 170], [-25, 170], [-60, 60], [0, 145], [-80, 80]];
const A = (fl, ab, ro, el, pr = 0) => [fl, ab, ro, el, pr];
const P = {
  stand: { armR: A(4, 8, 0, 14), armL: A(4, 8, 0, 14), neck: [4, 0, 0] },
  bored: { armR: A(6, 6, 0, 18), armL: A(2, 10, 0, 10), spine2: [0, 4, 2], neck: [10, -10, 0], head: [6, -6, 0], thighL: [6, 0, -3], shinL: [-10, 0, 0] },
  float0: { armR: A(18, 42, 0, 38, 10), armL: A(18, 42, 0, 38, 10), neck: [10, 0, 0], head: [4, 0, 0], thighR: [8, 0, 3], thighL: [8, 0, -3], shinR: [-12, 0, 0], shinL: [-12, 0, 0] },
  float: { armR: A(28, 72, 0, 22, 0), armL: A(28, 72, 0, 22, 0), spine2: [4, 0, 0], neck: [8, 0, 0], head: [4, 0, 0], thighR: [16, 0, 6], thighL: [10, 0, -6], shinR: [-26, 0, 0], shinL: [-18, 0, 0], footR: [-14, 0, 0], footL: [-10, 0, 0] },
  floatLook: { armR: A(30, 66, 0, 20, 0), armL: A(30, 66, 0, 20, 0), spine1: [-6, 0, 0], spine2: [-6, 0, 0], neck: [-26, 0, 0], head: [-12, 0, 0], thighR: [14, 0, 5], thighL: [8, 0, -5], shinR: [-22, 0, 0], shinL: [-14, 0, 0], footR: [-20, 0, 0], footL: [-16, 0, 0] },
  crouch: { thighR: [78, 0, 8], thighL: [78, 0, -8], shinR: [-104, 0, 0], shinL: [-104, 0, 0], footR: [22, 0, 0], footL: [22, 0, 0], spine1: [-16, 0, 0], spine2: [-12, 0, 0], chest: [-4, 0, 0], armR: A(42, 14, 0, 44), armL: A(42, 14, 0, 44), neck: [6, 0, 0], head: [2, 0, 0] },
  crouchDown: { thighR: [78, 0, 8], thighL: [78, 0, -8], shinR: [-104, 0, 0], shinL: [-104, 0, 0], footR: [22, 0, 0], footL: [22, 0, 0], spine1: [-18, 0, 0], spine2: [-14, 0, 0], chest: [-6, 0, 0], armR: A(36, 16, 0, 40), armL: A(36, 16, 0, 40), neck: [-24, 0, 0], head: [-12, 0, 0] },
  jump: { thighR: [6, 0, 4], thighL: [6, 0, -4], shinR: [-8, 0, 0], shinL: [-8, 0, 0], footR: [-30, 0, 0], footL: [-30, 0, 0], spine1: [4, 0, 0], spine2: [4, 0, 0], armR: A(84, 26, 0, 30), armL: A(84, 26, 0, 30), neck: [14, 0, 0], head: [6, 0, 0] },
  dark: { armR: A(62, 32, 0, 30), armL: A(62, 32, 0, 30), neck: [4, 0, 0], thighR: [14, 0, 5], thighL: [8, 0, -5], shinR: [-22, 0, 0], shinL: [-14, 0, 0], footR: [-14, 0, 0], footL: [-10, 0, 0] },
  relief: { armR: A(8, 10, 0, 24), armL: A(8, 10, 0, 24), spine2: [-4, 0, 0], neck: [-6, 0, 0], head: [2, 0, 0] },
};
for (const k of Object.keys(P)) { const c = k === 'crouch' || k === 'crouchDown' ? 40 : k === 'jump' || k === 'float' || k === 'dark' ? 10 : 22; curl(P[k], 'R', c); curl(P[k], 'L', c); }
const BONES = Object.keys(G.bones);
const qTmp = new THREE.Quaternion(), eTmp = new THREE.Euler();
const ARM0 = A(4, 8, 0, 14);
function eul(p, n) { return p[n] || (n === 'armR' || n === 'armL' ? ARM0 : [0, 0, 0]); }
function mixPose(a, b, k) { const o = {}; for (const n of new Set([...Object.keys(a), ...Object.keys(b)])) { const x = eul(a, n), y = eul(b, n); o[n] = x.map((v, i) => lerp(v, y[i], k)); } return o; }
function addPose(a, d) { const o = { ...a }; for (const [n, v] of Object.entries(d)) { const x = eul(o, n); o[n] = x.map((w, i) => w + (v[i] || 0)); } return o; }
function keyed(keys, t) {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 0; i < keys.length - 1; i++) { const [t0, a] = keys[i], [t1, b] = keys[i + 1]; if (t <= t1) return mixPose(a, b, sm((t - t0) / (t1 - t0))); }
  return keys[keys.length - 1][1];
}
function flail(T, amp, hz, seed) { return amp * (0.65 * Math.sin(2 * Math.PI * hz * T + seed) + 0.35 * Math.sin(2 * Math.PI * hz * 1.73 * T + seed * 2.1)); }
G.reset(); G.root.updateMatrixWorld(true);
const ARMREST = {};
for (const S of ['R', 'L']) {
  const af = G.REST['farm' + S].axis.clone();
  ARMREST[S] = { s: S === 'R' ? 1 : -1, a0: G.REST['uarm' + S].axis.clone(), af, hinge: new THREE.Vector3().crossVectors(af, V(0, 0, -1)).normalize() };
}
const qAA = (ax, deg) => new THREE.Quaternion().setFromAxisAngle(ax, deg * D2R);
function armQuats(S, a) {                                  // [flex, abd, rot, el, pro] -> local bone rotations (mold.js armQuats, no wrist)
  const R_ = ARMREST[S], [flex, abd, rot, el, pro] = a;
  const rv = V(flex, 0, R_.s * abd); const ang = rv.length();
  const d = ang > 1e-6 ? V(0, -1, 0).applyQuaternion(qAA(rv.clone().normalize(), ang)) : V(0, -1, 0);
  const Lu = new THREE.Quaternion().setFromUnitVectors(R_.a0, d).multiply(qAA(R_.a0, rot));
  const Lf = qAA(R_.hinge, el).multiply(qAA(R_.af, pro));
  return { Lu, Lf };
}
let LAST = {};
function applyPose(p, root) {
  const lim = {};
  for (const n of BONES) {
    if (/^(uarm|uarmTwist|farm|farmTwist|hand)[RL]$/.test(n)) continue;
    const b = G.bones[n]; let e = eul(p, n);
    if (LIMITS[n]) e = e.map((v, i) => softc(v, LIMITS[n][i][0], LIMITS[n][i][1]));
    lim[n] = e;
    b.position.copy(G.REST[n].pos);
    b.quaternion.copy(G.REST[n].q).multiply(qTmp.setFromEuler(eTmp.set(e[0] * D2R, e[1] * D2R, e[2] * D2R)));
  }
  for (const S of ['R', 'L']) {
    const a = eul(p, 'arm' + S).map((v, i) => softc(v, ARM_LIM[i][0], ARM_LIM[i][1], i === 3 ? 4 : 6));
    lim['arm' + S] = a;
    const { Lu, Lf } = armQuats(S, a);
    G.bones['uarm' + S].position.copy(G.REST['uarm' + S].pos); G.bones['uarm' + S].quaternion.copy(Lu);
    for (const n of ['uarmTwist', 'farmTwist']) { G.bones[n + S].position.copy(G.REST[n + S].pos); G.bones[n + S].quaternion.identity(); }
    G.bones['farm' + S].position.copy(G.REST['farm' + S].pos); G.bones['farm' + S].quaternion.copy(Lf);
    G.bones['hand' + S].position.copy(G.REST['hand' + S].pos); G.bones['hand' + S].quaternion.identity();
  }
  const R = new THREE.Quaternion().setFromEuler(new THREE.Euler((root.tilt || 0) * D2R, (root.yaw || 0) * D2R, (root.roll || 0) * D2R, 'YXZ'));
  const hipW = V(root.x || 0, (root.base || 0) + HIP.y + (root.lift || 0) - (root.s || 0), root.z ?? GZ);
  G.root.quaternion.copy(R);
  G.root.position.copy(hipW).sub(HIP.clone().applyQuaternion(R));
  G.root.updateMatrixWorld(true);
  LAST = lim;
}
function hipHeight(p) {                                    // standing on a floor: hip height from the thigh/shin angles
  const th = (eul(p, 'thighR')[0]) * D2R, sh = (eul(p, 'thighR')[0] + eul(p, 'shinR')[0]) * D2R;
  return 0.43 * Math.cos(th) + 0.42 * Math.cos(sh) + 0.1;
}
function blink(t) { for (const b0 of [1.4, 5.1, 9.6, 14.6, 18.2, 22.9, 26.4, 31.0, 33.3]) { const u = (t - b0) / 0.16; if (u > 0 && u < 1) return Math.sin(Math.PI * u); } return 0; }

// ------------------------------------------------------------------ the story, beat by beat (lift = how far his feet float above the floor)
const L0 = 0.5 * 0.35 * (TOTAL - T_SNAP);                    // float height at the loop seam (he drifts up at 0.35 m/s from the snap)
function floatLift(t) { const s = sinceSnap(t); return s < 99 ? 0.3 * Math.tanh((0.175 * s + 0.03 * s * s) / 0.3) : 0; }
const CR_S = 0.95 - hipHeight(P.crouch);
function guyAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  const base = carH(t);
  let pose, root = { base, lift: 0, s: 0 }, face = { blink: blink(t) }, show = true;
  if (b === 0) {                                           // floating up off the floor, arms coming up, scared
    const r0 = smooth(0, 0.7, lt);
    pose = keyed([[0, P.float0], [1.1, P.float], [d, P.float]], lt);
    pose = addPose(pose, { armR: [flail(t, 10, 0.7, 4) * r0, flail(t, 9, 0.9, 1) * r0, 0, flail(t, 10, 1.0, 3) * r0, 0], armL: [flail(t, 10, 0.7, 6) * r0, flail(t, 9, 0.85, 2) * r0, 0, flail(t, 10, 1.05, 5) * r0, 0], thighR: [flail(t, 6, 0.6, 2) * r0, 0, 0], thighL: [flail(t, 6, 0.6, 5) * r0, 0, 0] });
    root.lift = floatLift(t); root.roll = 3 * flail(t, 1, 0.35, 2) * r0; root.yaw = 4 * flail(t, 1, 0.3, 7) * r0;
    face = { ...face, fear: 0.6 + 0.4 * r0, browIn: 0.7, jaw: 0.15 + 0.4 * r0, oh: 0.3 * r0, brow: 0.6 * r0, look: [0, 0.3 * r0] };
  } else if (b === 1) {                                     // feet off the floor; he looks down at them
    pose = keyed([[0, P.float], [0.8, P.floatLook], [d, P.floatLook]], lt);
    pose = addPose(pose, { armR: [0, flail(t, 6, 0.5, 1), 0, 0, 0], armL: [0, flail(t, 6, 0.5, 3), 0, 0, 0], footR: [flail(t, 8, 0.6, 2), 0, 0], footL: [flail(t, 8, 0.6, 4), 0, 0] });
    root.lift = floatLift(t); root.roll = 3 * flail(t, 1, 0.35, 2); root.yaw = 4 * flail(t, 1, 0.3, 7);
    face = { ...face, fear: 0.7, browIn: 0.6, brow: 0.5, jaw: 0.12, oh: 0.35, look: [0, -0.6] };
  } else if (b === 2) {                                     // grabs the rail, pulls himself down into a crouch: "jump right before it hits"
    const k = smooth(0, 0.8, lt);
    pose = keyed([[0, P.floatLook], [0.8, P.crouchDown], [d, P.crouchDown]], lt);
    root.lift = lerp(floatLift(t), 0, k); root.s = CR_S * k;
    face = { ...face, browIn: 0.9, press: 0.6, frown: 0.4, fear: 0.3, look: [0, -0.5] };
  } else if (b === 3) {                                     // (wide) still crouched, bracing
    pose = addPose(P.crouchDown, { spine2: [flail(t, 2, 1.2, 1), 0, 0] }); root.s = CR_S;
    face = { ...face, browIn: 1, press: 0.7, fear: 0.4, look: [0, -0.5] };
  } else if (b === 4) {                                     // the jump, then the lights go out: arms out, feeling for the walls
    const up = smooth(0.25, 0.6, lt);
    if (lt < 1.6) { pose = keyed([[0, P.crouchDown], [0.25, P.crouch], [0.6, P.jump], [1.6, mixPose(P.jump, P.dark, 0.5)]], lt);
      root.s = CR_S * (1 - up); root.lift = 0.24 * up * (1 - 0.15 * smooth(0.6, 1.6, lt)); }
    else { pose = keyed([[0, mixPose(P.jump, P.dark, 0.5)], [0.8, P.dark], [d, P.dark]], lt - 1.6);
      pose = addPose(pose, { neck: [0, 40 * Math.sin((lt - 1.6) * 1.9) * smooth(1.6, 2.2, lt), 0], armR: [flail(t, 10, 0.8, 1), 0, 0, 0, 0], armL: [flail(t, 10, 0.8, 4), 0, 0, 0, 0] });
      root.lift = lerp(0.24 * 0.85, 0.3, smooth(1.6, 2.6, lt)) + 0.015 * Math.sin((lt - 1.6) * 2); }
    face = lt < 1.6 ? { ...face, browIn: 1, press: 0.4 * (1 - up), jaw: 0.3 * up, pain: 0.4 * up, look: [0, 0.2] } : { ...face, fear: 1, brow: 0.8, jaw: 0.25, oh: 0.4, look: [Math.sin((lt - 1.6) * 1.9) * 0.6, 0] };
  } else if (b === 5) {                                     // (not seen: car top) standing calm
    pose = P.stand; show = false;
  } else if (b === 6) {                                     // floating, then the brakes bite: he drops into a crouch, then stands up, relieved
    const hit = B6_CLAMP + 0.06;
    if (lt < hit) { pose = P.float; root.lift = 0.22; face = { ...face, fear: 1, jaw: 0.45, oh: 0.4 }; }
    else { const u = lt - hit;
      const land = smooth(0, 0.3, u);
      pose = keyed([[0, P.float], [0.3, P.crouch], [1.0, P.crouch], [d - hit, mixPose(P.crouch, P.relief, 0.6)]], u);
      const stand = smooth(1.0, d - hit, u);
      root.lift = 0.22 * (1 - land); root.s = CR_S * land * (1 - 0.6 * stand) - 0.03 * Math.sin(Math.PI * clamp(u / 0.35, 0, 1)) * land;
      face = { ...face, fear: 1 - smooth(0.4, 1.4, u), jaw: 0.3 * (1 - smooth(0.2, 0.8, u)), pain: 0.5 * Math.exp(-u * 4), brow: 0.4 * smooth(0.8, 1.6, u), smile: 0.4 * smooth(1.0, 1.8, u), look: [0, -0.2] }; }
  } else if (b === 7 || b === 8) {
    pose = P.stand; show = false;
  } else {                                                 // calm ride up, then the snap (ends exactly on frame one)
    if (t < T_SNAP) {
      pose = keyed([[0, P.stand], [0.8, P.bored], [d, P.bored]], lt);
      pose = addPose(pose, { spine2: [0.8 * Math.sin(t * 1.4), 0, 0] });
      face = { ...face, brow: 0.1, smile: 0.15, look: [0.2, 0.6] };
      const jolt = smooth(T_SNAP - 0.12, T_SNAP, t);
      face = { ...face, browIn: 0.3 * jolt, oh: 0.3 * jolt };
    } else {
      const u = (t - T_SNAP) / (TOTAL - T_SNAP);
      pose = mixPose(P.bored, P.float0, sm(clamp(u / 0.75, 0, 1)));
      root.lift = floatLift(t);
      face = { ...face, fear: 0.6 * sm(u), browIn: 0.7 * sm(u), jaw: 0.15 * sm(u), look: [0.2 * (1 - sm(u)), 0.6 * (1 - sm(u))] };
    }
  }
  return { pose, root, face, show };
}
// seam: at t = TOTAL the pose is exactly beat 0's first pose (P.float0, lift floatLift(TOTAL) == floatLift(0))

// ------------------------------------------------------------------ cameras: car space unless noted (one shot per beat, punch on cuts)
function shake(t, a, f = 1) { return V(vn1(t * 3 * f, 1) * a, vn1(t * 3 * f, 2) * a, vn1(t * 3 * f, 3) * a * 0.5); }
const HOOKCAM = { pos: V(0.85, 2.35, -6.3), tgt: V(0, 2.0, 0.2), fov: 44 };
function camAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b], u = lt / d;
  let pos, tgt, fov = 42, world = false;
  const fallK = b <= 4 ? 1 : 0;
  if (b === 0) {
    const sk = smooth(0, 0.6, lt);
    pos = HOOKCAM.pos.clone().add(V(-0.15 * u, -0.1 * u, 0.55 * u)); tgt = HOOKCAM.tgt.clone(); fov = HOOKCAM.fov;
    pos.add(shake(t, 0.012 * sk, 2.4));
  } else if (b === 1) {                                     // whole body, the gap under his feet
    pos = V(0.45 - 0.1 * u, 0.95, -3.75 + 0.15 * u); tgt = V(0, 1.15, GZ); fov = 46; pos.add(shake(t, 0.008, 2.6));
  } else if (b === 2) {
    pos = V(-0.55 + 0.1 * u, 0.62, -2.15 + 0.15 * u); tgt = V(0, 0.68, GZ); fov = 44; pos.add(shake(t, 0.008, 2.6));
  } else if (b === 3) {                                     // wide section: the whole car streaking down the shaft
    pos = V(1.9 - 0.3 * u, 2.4, -8.6 + 0.6 * u); tgt = V(0, 0.9, 0.2); fov = 40; pos.add(shake(t, 0.01, 1.5));
  } else if (b === 4) {
    if (lt < 1.6) { pos = V(0.3, 0.95, -2.85 + 0.1 * u); tgt = V(0, 1.05, GZ); fov = 46; }
    else { pos = V(0.2, 1.35, -2.25 + 0.1 * u); tgt = V(0, 1.4, GZ); fov = 44; }
    pos.add(shake(t, 0.008, 2.6));
  } else if (b === 5) {                                     // car top: the hitch and the cables running up
    pos = V(0.9 - 0.15 * u, CH + 0.7, -1.7 + 0.1 * u); tgt = V(0, CH + 1.0 + 0.15 * u, 0.1); fov = 46;
  } else if (b === 6) {
    if (lt < 1.25) { pos = V(0.45, -0.12, -1.45 + 0.05 * lt); tgt = V(RAILX - 0.02, -0.36, 0); fov = 40; pos.add(shake(t, lt > B6_CLAMP && lt < B6_CLAMP + B6_STOP + 0.15 ? 0.02 : 0.006, 3)); }
    else { const w = (lt - 1.25) / (d - 1.25); pos = V(0.35, 1.05, -2.9 + 0.15 * w); tgt = V(0, 0.95, GZ); fov = 46; }
  } else if (b === 7) {                                     // the tower in the fog (world), the car marker sliding down
    world = true; pos = V(TX - 90 + 12 * u, 120 + 10 * u, TZ - 520 + 30 * u); tgt = V(TX, 165, TZ); fov = 40;
  } else if (b === 8) {                                     // the pit (world): car slowing, air and cable under it
    world = true; pos = V(0.7, PIT + 2.0, -3.9 + 0.12 * u); tgt = V(0, PIT + 1.15, 0.25); fov = 44;
  } else {                                                 // calm medium shot, pulling back to the hook frame as the cable snaps
    const w = smooth(d - 1.3, d, lt);
    const p0 = V(0.25, 1.4, -2.35), t0 = V(0, 1.3, GZ);
    pos = p0.clone().lerp(HOOKCAM.pos, w); tgt = t0.clone().lerp(HOOKCAM.tgt, w); fov = lerp(42, HOOKCAM.fov, w);
  }
  if (!world) { const ch = carH(t); pos.y += ch; tgt.y += ch; }
  const punch = b > 0 ? (1 - smooth(0, 0.22, lt)) * 0.07 : 0;
  const punch6 = b === 6 && lt >= 1.25 ? (1 - smooth(1.25, 1.47, lt)) * 0.07 : 0;
  const punch4 = b === 4 && lt >= 1.6 ? (1 - smooth(1.6, 1.82, lt)) * 0.06 : 0;
  return { pos, tgt, fov: fov * (1 - punch - punch6 - punch4), world, fallK };
}

// ------------------------------------------------------------------ per-frame update
let CUR_T = 0;
function lightsAt(t) {                                       // interior light level 0..1, plus red emergency light
  const b = beatAt(t), lt = t - B[b];
  let k = 1, em = 0;
  const flick = a => 1 - a * (0.5 + 0.5 * Math.sign(Math.sin(t * 37 + 3 * Math.sin(t * 11)))) * (0.4 + 0.6 * Math.abs(vn1(t * 9, 4)));
  if (b === 0) k = flick(0.55 * (1 - smooth(0.4, 2.2, lt)) * smooth(0, 0.08, lt) + 0.12);
  else if (b <= 3) k = flick(0.12);
  else if (b === 4) { k = lt < 1.6 ? flick(0.15) : 0.03 * (1 - smooth(1.6, 1.75, lt)) + 0.0; em = smooth(1.6, 1.9, lt) * (0.75 + 0.25 * Math.sin(t * 6)); if (lt > 1.6 && lt < 1.75) k = 0.6 * (1 - smooth(1.6, 1.75, lt)); }
  else if (b === 6) k = lt < B6_CLAMP + B6_STOP ? flick(0.2) : 1;
  else if (b === 9 && t >= T_SNAP) { const s = t - T_SNAP; k = flick(0.55 * smooth(0, 0.08, s) * (1 - smooth(0.45, 0.62, s)) + 0.12 * smooth(0.45, 0.62, s)); }
  return { k, em };
}
function update(t) {
  t = ((t % TOTAL) + TOTAL) % TOTAL; CUR_T = t;
  const b = beatAt(t), lt = t - B[b];
  const ch = carH(t);
  car.position.set(0, ch, 0);
  const g = guyAt(t);
  if (window.OVR && window.OVR.p) { g.pose = { ...g.pose, ...window.OVR.p }; }
  applyPose(g.pose, g.root);
  untwistSafe();
  G.face(g.face);
  G.root.visible = g.show;
  G.root.updateMatrixWorld(true);
  const C = camAt(t);
  const inTower = b === 7;
  shaft.visible = car.visible = !inTower; tower.visible = inTower; towerSun.visible = inTower;
  scene.fog = inTower ? fogT : null; scene.background = new THREE.Color(inTower ? 0x8f969c : 0x07080a);
  // lights
  const L = lightsAt(t);
  lightPanelMat.emissiveIntensity = 2.4 * L.k; carLight.intensity = 14 * L.k; carFill.intensity = 2.2 * L.k;
  emLight.intensity = 3.5 * L.em; emLamp.material.emissiveIntensity = 3 * L.em;
  hemi.intensity = inTower ? 0.8 : 0.35 * Math.max(L.k, 0.12);
  scene.environmentIntensity = inTower ? 0.5 : 0.7 * Math.max(L.k, 0.05);
  // floor display
  const fl = clamp(Math.round(ch / FH), 1, NFL);
  drawDisplay(b === 5 ? 22 : b === 8 ? 1 : fl, falling(t), L.k > 0.08);
  // ropes
  const snapped = b <= 4 || b === 6 || b === 8 || t >= T_SNAP;
  const brk = H0 + HITCHY + 0.45;                           // where the cables broke (shaft space)
  for (let i = 0; i < NROPE; i++) {
    const r = ropes[i], x = ROPEX(i);
    if (b === 5 || (b === 9 && t < T_SNAP) || b === 7) {    // intact: from the hitch to the machine at the top
      const y0 = ch + HITCHY; r.position.set(x, y0, ROPEZ); r.scale.set(1, TOPY - y0, 1); r.visible = b !== 7;
      ropeTex.repeat.set(1, (TOPY - y0) * 8);
    } else if (snapped && b !== 6 && b !== 8) {              // the upper half, left hanging where it broke (with a little recoil)
      const s = sinceSnap(t), rec = 0.25 * (1 - Math.exp(-s * 6)) + 0.06 * Math.sin(s * 9) * Math.exp(-s * 2);
      const y0 = brk + rec + 0.03 * hash1(i); r.position.set(x + 0.01 * Math.sin(s * 7 + i), y0, ROPEZ); r.scale.set(1, TOPY - y0, 1); r.visible = true;
      topFray[i].position.set(x, y0, ROPEZ); topFray[i].rotation.set(Math.PI, i, 0); topFray[i].visible = true;
    } else r.visible = false;
    if (!(snapped && b !== 6 && b !== 8 && b !== 5 && b !== 7)) topFray[i].visible = false;
    if (b === 5) {                                          // count them, then all but one fade out: it still holds
      const k = lt / DUR[5];
      const glow = smooth(0.08 + i * 0.05, 0.14 + i * 0.05, k) * (1 - smooth(0.5, 0.56, k));
      const keep = i === 2;
      ropeMats[i].emissiveIntensity = keep ? 0.9 * (glow + smooth(0.55, 0.62, k)) : 0.9 * glow;
      ropeMats[i].opacity = keep ? 1 : 1 - 0.85 * smooth(0.52, 0.62, k);
    } else { ropeMats[i].emissiveIntensity = 0; ropeMats[i].opacity = 1; }
  }
  // stubs on the car top: short frayed cable ends whipping (only after the snap)
  const showStubs = snapped && b !== 7;
  stubs.forEach((m, j) => {
    m.visible = showStubs;
    stubFray[j].visible = showStubs;
    if (!showStubs) return;
    const s = b === 8 ? 3 : b === 6 ? 3 + lt : sinceSnap(t);
    const x0 = ROPEX(j * 2 + 1), base = V(x0, ch + HITCHY, ROPEZ), pts = [];
    const len = 0.7 + 0.12 * j, amp = 0.22 * Math.exp(-s * 0.25) + 0.07;
    for (let k = 0; k <= 6; k++) { const u = k / 6;
      pts.push(V(x0 + amp * u * u * Math.sin(s * (6 + j) + u * 3 + j) , ch + HITCHY + len * u * (0.9 + 0.1 * Math.cos(s * 5 + j)), ROPEZ + amp * 0.7 * u * u * Math.cos(s * (5 + j) + u * 2.5))); }
    m.geometry.dispose(); m.geometry = stubGeo(pts);
    stubFray[j].position.copy(pts[6]); stubFray[j].rotation.set(Math.sin(s * 4 + j) * 0.4, j, Math.cos(s * 3 + j) * 0.4);
  });
  // safety brakes (beat 6): wedges close onto the rail, sparks fly up, then it holds
  const clampK = b === 6 ? smooth(B6_CLAMP - 0.06, B6_CLAMP + 0.04, lt) : 0;
  for (const S of SAFE) for (const [w, zz] of S.wedges) w.position.z = zz * (0.06 - 0.03 * clampK);
  let ns = 0;
  const sparkOn = b === 6 && lt > B6_CLAMP - 0.02 && lt < B6_CLAMP + B6_STOP + 0.5;
  if (sparkOn) {
    const age0 = lt - B6_CLAMP, vel = Math.max(0, B6_V * (1 - (lt - B6_CLAMP) / B6_STOP));
    for (let i = 0; i < NSP; i++) { const side = i % 2 ? 1 : -1; const born = (hash1(i * 1.37) * (B6_STOP + 0.05)); const age = age0 - born;
      if (age < 0 || age > 0.45) continue;
      const vx = 0.3 + hash1(i * 4.1) * 1.4, vy = -0.4 - hash1(i * 2.3) * 2.6 + (hash1(i * 6.1) < 0.3 ? 2.6 : 0), vz = -0.4 - hash1(i * 7.9) * 1.6;
      const p = V(side * (RAILX + 0.03) - side * vx * age, ch - 0.47 + vy * age - 4.9 * age * age, -0.02 + vz * age);
      spPos.set([p.x, p.y, p.z], ns * 3); const heat = 1 - age / 0.45; const col = [1.0 * heat + 0.2, 0.62 * heat * heat + 0.05, 0.18 * heat * heat * heat]; spCol.set(col, ns * 3);
      const q = V(p.x + side * vx * 0.05, p.y - (vy - 9.8 * age) * 0.05, p.z - vz * 0.05);
      stPos.set([p.x, p.y, p.z, q.x, q.y, q.z], ns * 6); stCol.set([...col, col[0] * 0.3, col[1] * 0.2, col[2] * 0.1], ns * 6); ns++; }
    sparkLight.position.set(RAILX - 0.05, ch - 0.5, -0.3); sparkLight.intensity = 2.2 * (vel / B6_V + 0.2) * (lt < B6_CLAMP + B6_STOP + 0.2 ? 1 : 0);
  } else sparkLight.intensity = 0;
  for (let i = ns; i < NSP; i++) { spPos.set([0, -999, 0], i * 3); stPos.set([0, -999, 0, 0, -999, 0], i * 6); }
  spGeo.attributes.position.needsUpdate = true; spGeo.attributes.color.needsUpdate = true; sparks.visible = sparkOn;
  stGeo.attributes.position.needsUpdate = true; stGeo.attributes.color.needsUpdate = true; streaks.visible = sparkOn;
  // dust streaming past the car (car space): falls look like streaks going up
  const vrel = b <= 4 || t >= T_SNAP ? (t >= T_SNAP ? G_ * (t - T_SNAP) : (t < T_VMAX ? V_SEAM + G_ * t : VMAX)) : b === 6 && lt < B6_CLAMP + B6_STOP ? Math.max(0, lt < B6_CLAMP ? B6_V : B6_V * (1 - (lt - B6_CLAMP) / B6_STOP)) : 0;
  const yspan = 9;
  for (let i = 0; i < NDUST; i++) {
    const side = hash1(i * 5.1), x = side < 0.5 ? (hash1(i * 1.7) < 0.5 ? -1 : 1) * (CX + 0.3 + hash1(i * 2.9) * 0.08) : (hash1(i * 1.7) - 0.5) * 2 * (SX - 0.05);
    const z = side < 0.5 ? (hash1(i * 3.3) - 0.5) * 1.8 : (side < 0.75 ? SZB - 0.1 - hash1(i * 3.3) * 0.2 : -0.9 + hash1(i) * 0.3);
    let y = (((hash1(i * 9.1) * yspan - (ch % yspan)) % yspan) + yspan) % yspan - 3.5;
    const len = Math.min(1.2, vrel * 0.03 + 0.004);
    dPos.set([x, ch + y, z, x, ch + y + len, z], i * 6);
  }
  dGeo.attributes.position.needsUpdate = true; dust.visible = !inTower && b !== 5 && vrel > 0.5; dust.material.opacity = 0.35 * clamp(vrel / 6, 0, 1);
  // beat 8: coil grows in the pit, air arrows under the car
  coils.forEach((c, i) => { c.visible = b === 8 && lt / DUR[8] > i / 14 * 0.7; });
  airArrows.forEach((a, i) => { a.visible = b === 8; if (b === 8) { const k = smooth(0.15 + i * 0.08, 0.45 + i * 0.08, lt / DUR[8]);
    a.position.set(-0.75 + i * 0.5, ch - 0.95 + 0.08 * Math.sin(t * 5 + i), -0.25 + 0.15 * (i % 2)); a.scale.setScalar(0.001 + k); } });
  // the tower: the car marker slides down 75 floors, speeding up then slowing in the last floors (air in the shaft)
  if (inTower) { const k = clamp((lt - 0.4) / (DUR[7] - 0.9), 0, 1);
    const yy = lerp(TSTART * TFH, TEND * TFH, 1 - (1 - sm(k)) ** 1.0); tCar.position.y = yy;
    const top = TSTART * TFH; tTrail.scale.y = Math.max(0.01, Math.min(top - yy, 60)); tTrail.position.set(6, yy + tTrail.scale.y / 2, -22.2); tTrail.visible = k > 0.01 && k < 0.999;
    towerU.uT.value = t; }
  // camera
  camera.position.copy(C.pos); camera.lookAt(C.tgt); camera.fov = C.fov; camera.far = inTower ? 3000 : 120; camera.updateProjectionMatrix();
  return { beat: b, t };
}

// ------------------------------------------------------------------ frame I/O (same contract as quick.js / mold.js)
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
window.renderAtT = t => { update(t); if (window.CAM) { camera.position.set(...window.CAM.pos); camera.lookAt(...window.CAM.tgt); camera.fov = window.CAM.fov || 42; camera.updateProjectionMatrix(); } draw(); return renderer.domElement.toDataURL('image/png'); };
window.rigReport = i => { const r = update(i / FPS); return { t: r.t, beat: r.beat, ang: LAST, hands: ['handR', 'handL'].map(n => G.bones[n].getWorldPosition(new THREE.Vector3()).toArray()),
  chest: G.bones.chest.getWorldPosition(new THREE.Vector3()).toArray(), hips: G.bones.hips.getWorldPosition(new THREE.Vector3()).toArray(), car: carH(r.t), show: G.root.visible }; };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS);
window.READY = true;
