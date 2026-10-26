// "Put diesel in a gas car? Here's what you do" - a 3D Short with the sculpted, skinned guy at a gas station.
//   diesel.html?w=1080&h=1920            (times from diesel/times.json; one shot per narration line)
// Beats: 0 the green nozzle pumping into his gas car (hook) | 1 x-ray car: the key turns, the fuel pump pushes diesel down the line
//        2 cylinder close-up: spark lights gas mist, BOOM | 3 same: oily diesel, the spark fizzles | 4 the road: the car bucks and dies
//        5 roadside: phone to his ear, the tow truck backs in | 6 macro: the fat diesel nozzle vs the small filler hole
//        7 the car rides away on the tow truck ($) | 8 parts stage: pump, injectors, converter, filter ($$$) | 9 at the pump again (loops)
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
const TIMES = await (await fetch('/diesel/times.json')).json();
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
function canvasTex(w, h, draw) { const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), c); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t; }

// ------------------------------------------------------------------ renderer / scene / light: a sunny afternoon
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(W, H);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.0;
renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.localClippingEnabled = true;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(42, W / H, 0.02, 1200);
const SUNDIR = V(-0.5, 0.65, -0.55).normalize();
const skyMat = new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false, fog: false, uniforms: { uSun: { value: SUNDIR } },
  vertexShader: 'varying vec3 vD; void main(){ vD = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
  fragmentShader: `varying vec3 vD; uniform vec3 uSun;
    void main(){ float h = clamp(vD.y, -0.2, 1.0); vec3 top = vec3(0.24, 0.47, 0.86), hor = vec3(0.84, 0.89, 0.95);
      vec3 c = mix(hor, top, smoothstep(0.0, 0.55, h)); float s = max(dot(normalize(vD), uSun), 0.0); c += vec3(1.0, 0.95, 0.85) * (pow(s, 12.0) * 0.25 + pow(s, 900.0) * 5.0);
      c = mix(c, vec3(0.55, 0.55, 0.52), 1.0 - smoothstep(-0.2, 0.0, vD.y)); gl_FragColor = vec4(pow(c, vec3(2.2)) * 0.95, 1.0); }` });
const sky = new THREE.Mesh(new THREE.SphereGeometry(900, 48, 24), skyMat); scene.add(sky);
{ const pm = new THREE.PMREMGenerator(renderer); const es = new THREE.Scene(); es.add(new THREE.Mesh(new THREE.SphereGeometry(10, 32, 16), skyMat));
  scene.environment = pm.fromScene(es, 0.02).texture; scene.environmentIntensity = 0.6; }
const hemi = new THREE.HemisphereLight(0xd6e6ff, 0x6a6458, 0.75); scene.add(hemi);
const sun = new THREE.DirectionalLight(0xfff1dc, 2.6); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
{ const S = sun.shadow.camera; S.left = -5; S.right = 5; S.top = 5; S.bottom = -5; S.near = 0.5; S.far = 60; sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.02; }
scene.add(sun); scene.add(sun.target);

// ------------------------------------------------------------------ the gas station: concrete pad, pump island, canopy with lights; a road beyond
const STATION = new THREE.Group(); scene.add(STATION);
const concrete = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.9 });
concrete.onBeforeCompile = sh => {
  sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vWc;').replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvWc = (modelMatrix * vec4(transformed, 1.0)).xyz;');
  sh.fragmentShader = sh.fragmentShader.replace('#include <common>', `#include <common>
varying vec3 vWc;
float hh(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
float vn(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f*f*(3.0-2.0*f); return mix(mix(hh(i), hh(i+vec2(1,0)), u.x), mix(hh(i+vec2(0,1)), hh(i+vec2(1,1)), u.x), u.y); }`)
    .replace('#include <color_fragment>', `#include <color_fragment>
  { vec2 P = vWc.xz; float n = vn(P * 1.3) * 0.5 + vn(P * 7.0) * 0.3 + hh(floor(P * 80.0)) * 0.2;
    vec2 g = abs(fract(P / 4.0) - 0.5); float joint = 1.0 - smoothstep(0.485, 0.495, max(g.x, g.y));
    vec3 c = vec3(0.62, 0.61, 0.58) * (0.85 + 0.25 * n) * (0.75 + 0.25 * joint);
    float stain = smoothstep(0.6, 0.85, vn(P * 0.45 + 3.0)); c *= 1.0 - 0.25 * stain;
    diffuseColor.rgb = c; }`);
};
const ground = new THREE.Mesh(new THREE.PlaneGeometry(400, 400).rotateX(-Math.PI / 2), concrete); ground.receiveShadow = true; scene.add(ground);
const sbox = (w, h, d, x, y, z, m, r = 0, parent = STATION) => { const o = new THREE.Mesh(r > 0 ? new RoundedBoxGeometry(w, h, d, 2, Math.min(r, 0.4 * Math.min(w, h, d))) : new THREE.BoxGeometry(w, h, d), m); o.position.set(x, y, z); o.castShadow = true; o.receiveShadow = true; parent.add(o); return o; };
const PUMPX = -2.25;
const islandMat = new THREE.MeshStandardMaterial({ color: 0xd9d4c8, roughness: 0.85 });
sbox(1.0, 0.18, 4.6, PUMPX, 0.09, 1.0, islandMat, 0.03);
for (const z of [-0.6, 2.6]) { const b = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.09, 1.0, 20), new THREE.MeshStandardMaterial({ color: 0xf2c230, roughness: 0.5 })); b.position.set(PUMPX + 0.35, 0.68, z); b.castShadow = true; STATION.add(b); }
// canopy
const canopyMat = new THREE.MeshStandardMaterial({ color: 0xf4f4f2, roughness: 0.6 });
sbox(9, 0.5, 9, -1.0, 4.9, 1.0, canopyMat); sbox(9.04, 0.32, 9.04, -1.0, 4.62, 1.0, new THREE.MeshStandardMaterial({ color: 0x1e7a3a, roughness: 0.5 }));
for (const [x, z] of [[PUMPX, -1.2], [PUMPX, 3.2]]) sbox(0.36, 4.5, 0.36, x, 2.25, z, canopyMat);
const canopyLights = new THREE.InstancedMesh(new THREE.BoxGeometry(0.9, 0.04, 0.6), new THREE.MeshStandardMaterial({ color: 0x111111, emissive: 0xffffff, emissiveIntensity: 1.6 }), 6);
{ const m4 = new THREE.Matrix4(); let k = 0; for (const x of [-3.5, -1.0, 1.5]) for (const z of [-0.8, 2.8]) { m4.makeTranslation(x, 4.44, z); canopyLights.setMatrixAt(k++, m4); } STATION.add(canopyLights); }
const canopyFill = new THREE.PointLight(0xfff8ec, 6, 9, 1.4); canopyFill.position.set(-1.2, 4.0, 1.0); STATION.add(canopyFill);
// the pump (a GAS label + a green DIESEL handle on its side, the price screen)
const pump = new THREE.Group(); pump.position.set(PUMPX, 0.18, 1.35); STATION.add(pump);
{ const body = new THREE.MeshStandardMaterial({ color: 0xe9e9e6, roughness: 0.5 }), dark = new THREE.MeshStandardMaterial({ color: 0x2a2c30, roughness: 0.6 });
  sbox(0.62, 1.7, 0.9, 0, 0.85, 0, body, 0.04, pump); sbox(0.64, 0.25, 0.92, 0, 1.82, 0, new THREE.MeshStandardMaterial({ color: 0x1e7a3a, roughness: 0.5 }), 0.03, pump);
  sbox(0.02, 0.32, 0.5, 0.32, 1.38, 0, dark, 0.01, pump);
  const lab = canvasTex(512, 160, g => { g.fillStyle = '#1e7a3a'; g.fillRect(0, 0, 512, 160); g.fillStyle = '#fff'; g.font = 'bold 96px Inter, Arial'; g.textAlign = 'center'; g.fillText('DIESEL', 256, 118); });
  const dl = new THREE.Mesh(new THREE.PlaneGeometry(0.42, 0.13), new THREE.MeshStandardMaterial({ map: lab, roughness: 0.5 })); dl.position.set(0.312, 0.95, -0.2); dl.rotation.y = Math.PI / 2; pump.add(dl);
  const lab2 = canvasTex(512, 160, g => { g.fillStyle = '#c0262b'; g.fillRect(0, 0, 512, 160); g.fillStyle = '#fff'; g.font = 'bold 96px Inter, Arial'; g.textAlign = 'center'; g.fillText('GAS', 256, 118); });
  const gl2 = new THREE.Mesh(new THREE.PlaneGeometry(0.42, 0.13), new THREE.MeshStandardMaterial({ map: lab2, roughness: 0.5 })); gl2.position.set(0.312, 0.95, 0.22); gl2.rotation.y = Math.PI / 2; pump.add(gl2);
  // the gas holster with its (red) nozzle still hanging in it
  sbox(0.06, 0.22, 0.12, 0.33, 0.62, 0.22, dark, 0.01, pump);
  const rn = new THREE.Mesh(new RoundedBoxGeometry(0.05, 0.16, 0.06, 2, 0.015), new THREE.MeshStandardMaterial({ color: 0xc0262b, roughness: 0.45 })); rn.position.set(0.37, 0.6, 0.22); pump.add(rn);
  sbox(0.06, 0.22, 0.12, 0.33, 0.62, -0.2, dark, 0.01, pump); }
const priceCan = document.createElement('canvas'); priceCan.width = 320; priceCan.height = 160; const priceTex = new THREE.CanvasTexture(priceCan); priceTex.colorSpace = THREE.SRGBColorSpace;
let priceKey = '';
function drawPrice(gal) { const k = gal.toFixed(2); if (k === priceKey) return; priceKey = k; const g = priceCan.getContext('2d');
  g.fillStyle = '#0d1a10'; g.fillRect(0, 0, 320, 160); g.fillStyle = '#7dff8a'; g.font = 'bold 54px "DejaVu Sans Mono", monospace'; g.textAlign = 'right';
  g.fillText('$' + (gal * 4.28).toFixed(2), 300, 70); g.font = 'bold 40px "DejaVu Sans Mono", monospace'; g.fillText(k + ' GAL', 300, 135); priceTex.needsUpdate = true; }
drawPrice(0);
{ const sc = new THREE.Mesh(new THREE.PlaneGeometry(0.46, 0.23), new THREE.MeshBasicMaterial({ map: priceTex, toneMapped: false })); sc.position.set(PUMPX + 0.322, 0.18 + 1.38, 1.35); sc.rotation.y = Math.PI / 2; STATION.add(sc); }
// the store in the back, a few trees
{ sbox(10, 3.2, 6, 3.0, 1.6, 12, new THREE.MeshStandardMaterial({ color: 0xc9b89a, roughness: 0.9 }));
  const win = new THREE.Mesh(new THREE.PlaneGeometry(6, 1.6), new THREE.MeshStandardMaterial({ color: 0x29404f, roughness: 0.1, metalness: 0.5 })); win.position.set(3.0, 1.4, 8.99); win.rotation.y = Math.PI; STATION.add(win);
  const tr = new THREE.InstancedMesh(new THREE.SphereGeometry(1.6, 12, 10), new THREE.MeshStandardMaterial({ color: 0x3f6a2e, roughness: 1 }), 40); const m4 = new THREE.Matrix4(); let k = 0;
  for (let i = 0; i < 80 && k < 40; i++) { const x = (hash1(i) - 0.5) * 90, z = 18 + hash1(i * 3) * 40; m4.compose(V(x, 2.2, z), new THREE.Quaternion(), V(1, 1.3, 1)); tr.setMatrixAt(k++, m4); }
  tr.count = k; scene.add(tr); }
// the road (far off, for the breakdown): asphalt strip with lines
const ROADX = 120;
const road = new THREE.Group(); road.position.set(ROADX, 0, 0); scene.add(road);
{ const asph = new THREE.Mesh(new THREE.PlaneGeometry(7, 400).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0x2c2d30, roughness: 0.9 })); asph.position.y = 0.01; asph.receiveShadow = true; road.add(asph);
  const dash = new THREE.InstancedMesh(new THREE.PlaneGeometry(0.15, 2.5).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ color: 0xf2d24a }), 80); const m4 = new THREE.Matrix4();
  for (let i = 0; i < 80; i++) { m4.makeTranslation(0, 0.015, -200 + i * 5); dash.setMatrixAt(i, m4); } road.add(dash);
  const gr = new THREE.Mesh(new THREE.PlaneGeometry(60, 400).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0x5a7a3a, roughness: 1 })); gr.position.set(0, 0.005, 0); road.add(gr); gr.position.y = 0.004; asph.position.y = 0.012;
  const posts = new THREE.InstancedMesh(new THREE.BoxGeometry(0.1, 0.9, 0.1), new THREE.MeshStandardMaterial({ color: 0xdddddd }), 40);
  for (let i = 0; i < 40; i++) { m4.makeTranslation(-4.4, 0.45, -200 + i * 10); posts.setMatrixAt(i, m4); } road.add(posts); }

// ------------------------------------------------------------------ the car (sedan), its glass, door, interior
const car = new THREE.Group(); scene.add(car);
const carU = { uInv: { value: new THREE.Matrix4() } };          // world -> car space, so the lake can be cut out of the cabin
const paint = new THREE.MeshPhysicalMaterial({ color: 0x9a1d1d, roughness: 0.35, clearcoat: 1, clearcoatRoughness: 0.08, metalness: 0.25 });
const dark = new THREE.MeshStandardMaterial({ color: 0x18191b, roughness: 0.7 });
const trim = new THREE.MeshStandardMaterial({ color: 0x2a2c30, roughness: 0.55 });
const chrome = new THREE.MeshStandardMaterial({ color: 0xdddddd, metalness: 1, roughness: 0.18 });
const cloth = new THREE.MeshStandardMaterial({ color: 0x3a3d44, roughness: 0.95 });
const dash = new THREE.MeshStandardMaterial({ color: 0x24262a, roughness: 0.8 });
const BELT_Y = 0.98, ROOF_Y = 1.42, CABZ0 = -0.95, CABZ1 = 1.25, CW = 0.86;    // window line, roof, cabin front/back, half width inside
// glass: underwater fragments (outside water line) go murky green, so the glass reads as "water on the other side"
const WATER_Y = { value: -99 };
function glassMat(op = 0.28) {
  const m = new THREE.MeshPhysicalMaterial({ color: 0xbfd6e0, roughness: 0.05, metalness: 0.0, transparent: true, opacity: op, side: THREE.DoubleSide, depthWrite: false });
  m.onBeforeCompile = sh => { sh.uniforms.uWY = WATER_Y;
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vWg;').replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvWg = (modelMatrix * vec4(transformed, 1.0)).xyz;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vWg; uniform float uWY;')
      .replace('#include <color_fragment>', `#include <color_fragment>
  { float wob = 0.012 * sin(vWg.x * 9.0 + vWg.z * 7.0); float under = 1.0 - smoothstep(-0.008, 0.008, vWg.y - uWY - wob);
    diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.06, 0.26, 0.25), under); diffuseColor.a = mix(diffuseColor.a, 0.86, under);
    diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.75, 0.9, 0.9), (1.0 - smoothstep(0.0, 0.012, abs(vWg.y - uWY - wob))) * 0.8); }`); };
  return m;
}
const glassM = glassMat(), glassDoorM = glassMat(0.25);
const box = (w, h, d, x, y, z, m, parent = car, r = 0.02) => { r = Math.min(r, 0.4 * Math.min(w, h, d)); const o = new THREE.Mesh(r > 0 ? new RoundedBoxGeometry(w, h, d, 2, r) : new THREE.BoxGeometry(w, h, d), m); o.position.set(x, y, z); o.castShadow = true; o.receiveShadow = true; parent.add(o); return o; };
// lower body, hood, trunk, roof, pillars
box(1.82, 0.62, 1.35, 0, 0.62, -1.625, paint, car, 0.12);                     // nose (engine bay), solid
box(1.82, 0.62, 1.05, 0, 0.62, 1.775, paint, car, 0.12);                       // tail (trunk), solid
box(1.82, 0.12, 2.24, 0, 0.27, 0.15, paint, car, 0.03);                        // floor pan
box(0.07, 0.64, 2.24, 0.875, 0.62, 0.15, paint, car, 0.03);                    // passenger side wall (doors shut)
box(0.07, 0.64, 0.7, -0.875, 0.62, 0.9, paint, car, 0.03);                     // driver side, behind his door
box(0.07, 0.64, 0.25, -0.875, 0.62, -0.84, paint, car, 0.03);                  // driver side, ahead of his door
box(1.7, 0.6, 0.05, 0, 0.62, -0.95, dash, car, 0.01);                          // firewall
box(1.7, 0.62, 0.05, 0, 0.62, 1.25, trim, car, 0.01);                          // back of the rear seat / trunk wall
box(1.6, 0.28, 0.5, 0, 0.5, 0.95, cloth, car, 0.05);                           // rear bench
box(0.05, 0.5, 2.1, 0.84, 0.68, 0.15, trim, car, 0.01);                        // passenger side inner trim
box(1.76, 0.1, 1.5, 0, 0.96, -1.62, paint, car, 0.05);                         // hood
box(1.76, 0.1, 1.05, 0, 0.98, 1.78, paint, car, 0.05);                         // trunk lid
box(1.66, 0.06, 1.56, 0, ROOF_Y, 0.21, paint, car, 0.02);                        // roof
for (const s of [1, -1]) {
  const ap = box(0.06, 0.62, 0.06, s * 0.84, 1.2, -0.75, paint); ap.rotation.x = 0.74;     // A pillars (raked back along the windshield)
  box(0.07, 0.46, 0.09, s * 0.85, 1.2, 0.58, paint);                             // B pillars
  const cp = box(0.06, 0.52, 0.06, s * 0.84, 1.21, 1.11, paint); cp.rotation.x = -0.59;    // C pillars
}
// windshield and rear glass (laminated: they never break here), side glass (the driver's front window moves)
{ const ws = new THREE.Mesh(new THREE.PlaneGeometry(1.62, 0.6), glassM); ws.position.set(0, 1.2, -0.75); ws.rotation.x = 0.74; car.add(ws);   // top leans back
  const rw = new THREE.Mesh(new THREE.PlaneGeometry(1.56, 0.5), glassM); rw.position.set(0, 1.21, 1.11); rw.rotation.x = -0.59; car.add(rw);
  for (const s of [1, -1]) { const rg = new THREE.Mesh(new THREE.PlaneGeometry(0.5, 0.4), glassM); rg.position.set(s * 0.88, 1.19, 0.86); rg.rotation.y = Math.PI / 2; car.add(rg); }
  const pg = new THREE.Mesh(new THREE.PlaneGeometry(1.25, 0.42), glassM); pg.position.set(0.88, 1.19, -0.08); pg.rotation.y = Math.PI / 2; car.add(pg); }
// the driver's door (hinged at its front edge), with its window glass, inner panel, armrest, window switch and handle
const door = new THREE.Group(); door.position.set(-0.9, 0, -0.72); car.add(door);       // hinge line
const DOORLEN = 1.28;
box(0.06, 0.62, DOORLEN, 0, 0.62, DOORLEN / 2, paint, door, 0.02);
box(0.04, 0.5, DOORLEN - 0.12, 0.05, 0.68, DOORLEN / 2, trim, door, 0.015);                // inner panel
box(0.11, 0.05, 0.42, 0.1, 0.8, DOORLEN / 2 + 0.06, trim, door, 0.015);                   // armrest
const winSwitch = box(0.035, 0.012, 0.05, 0.13, 0.83, DOORLEN / 2 - 0.05, chrome, door, 0.004);
const handleIn = box(0.03, 0.04, 0.11, 0.08, 0.92, 0.58, chrome, door, 0.01);   // inner handle, within reach of a seated driver
const dGlass = new THREE.Mesh(new THREE.PlaneGeometry(1.18, 0.42), glassDoorM); dGlass.rotation.y = Math.PI / 2; dGlass.position.set(0.0, 1.19, DOORLEN / 2 + 0.02); door.add(dGlass);
const DGLASS_Y0 = 1.19;
// the door's outer seal around the window opening
box(0.05, 0.03, 1.22, 0.0, BELT_Y - 0.01, DOORLEN / 2 + 0.02, dark, door, 0.008);
// interior: seats, steering wheel, dashboard, center console, buckle
for (const sx of [-0.38, 0.38]) {
  box(0.52, 0.12, 0.52, sx, 0.45, 0.28, cloth, car, 0.05);                       // cushion
  const bk = box(0.52, 0.66, 0.12, sx, 0.82, 0.58, cloth, car, 0.05); bk.rotation.x = 0.22;   // back, reclined
  box(0.28, 0.18, 0.1, sx, 1.23, 0.66, cloth, car, 0.04);                         // headrest
}
box(1.7, 0.28, 0.4, 0, 0.9, -0.82, dash, car, 0.06);                             // dashboard
box(0.22, 0.24, 0.9, 0, 0.5, 0.0, dash, car, 0.04);                              // console
box(1.74, 0.04, 2.0, 0, 0.32, 0.15, new THREE.MeshStandardMaterial({ color: 0x202124, roughness: 1 }), car, 0);   // floor
const BUCKLE = V(-0.13, 0.6, 0.3);
box(0.04, 0.07, 0.03, BUCKLE.x, BUCKLE.y, BUCKLE.z, new THREE.MeshStandardMaterial({ color: 0xc0262b, roughness: 0.5 }), car, 0.008);
const WHEEL = { c: V(-0.38, 0.93, -0.12), r: 0.19, tilt: 0.42 };   // a normal reach from the seat                 // tilted toward the driver
const wheel = new THREE.Group(); wheel.position.copy(WHEEL.c); wheel.rotation.x = -WHEEL.tilt; car.add(wheel);
{ const rim = new THREE.Mesh(new THREE.TorusGeometry(WHEEL.r, 0.016, 12, 48), new THREE.MeshStandardMaterial({ color: 0x151515, roughness: 0.6 })); wheel.add(rim);
  for (const a of [0, 2.2, -2.2]) { const sp = new THREE.Mesh(new THREE.BoxGeometry(0.02, WHEEL.r, 0.012), trim); sp.position.set(Math.sin(a) * WHEEL.r / 2, -Math.cos(a) * WHEEL.r / 2, 0); sp.rotation.z = a; wheel.add(sp); }
  const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.04, 20).rotateX(Math.PI / 2), trim); wheel.add(hub);
  const col = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.62, 10).rotateX(Math.PI / 2), trim); col.position.z = -0.31; wheel.add(col); }
// wheels, lights, mirror
for (const [x, z] of [[-0.86, -1.42], [0.86, -1.42], [-0.86, 1.45], [0.86, 1.45]]) {
  const t = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.32, 0.23, 24).rotateZ(Math.PI / 2), dark); t.position.set(x, 0.32, z); t.castShadow = true; car.add(t);
  const h = new THREE.Mesh(new THREE.CylinderGeometry(0.17, 0.17, 0.24, 16).rotateZ(Math.PI / 2), chrome); h.position.set(x, 0.32, z); car.add(h); }
for (const s of [1, -1]) { box(0.36, 0.1, 0.05, s * 0.6, 0.78, -2.3, new THREE.MeshStandardMaterial({ color: 0xffffee, emissive: 0x555544, roughness: 0.2 }), car, 0.02);
  box(0.34, 0.1, 0.05, s * 0.6, 0.8, 2.3, new THREE.MeshStandardMaterial({ color: 0xaa1010, emissive: 0x440000, roughness: 0.3 }), car, 0.02); }
box(0.14, 0.09, 0.04, -0.98, 1.05, -0.62, paint, car, 0.02);
for (const m of [glassM, glassDoorM]) { m.opacity = 0.88; m.color.set(0x2c353c); }   // tinted: nobody needs to see the empty seat
// ------------------------------------------------------------------ the pump nozzle (green, diesel), its hose; the car's filler (left rear quarter)
const FILL_LOCAL = V(-0.915, 0.86, 1.48);                         // fuel filler opening on the car's left rear quarter (car space)
const fillerDoor = new THREE.Group();
const nozzle = new THREE.Group(); scene.add(nozzle);
const NOZ = { handle: V(0, 0, 0), tip: V(0.25, -0.09, 0) };          // nozzle-local: handle top at the origin, spout tip toward +x and down
{ const green = new THREE.MeshStandardMaterial({ color: 0x1f9a4a, roughness: 0.45 }), steel = new THREE.MeshStandardMaterial({ color: 0xbfc4c8, metalness: 0.9, roughness: 0.3 }), blk = new THREE.MeshStandardMaterial({ color: 0x1b1c1e, roughness: 0.6 });
  const body = new THREE.Mesh(new RoundedBoxGeometry(0.16, 0.06, 0.05, 2, 0.018), green); body.position.set(0.02, 0, 0); nozzle.add(body);
  const guard = new THREE.Mesh(new THREE.TorusGeometry(0.045, 0.006, 8, 24, Math.PI), blk); guard.position.set(0.0, -0.035, 0); guard.rotation.z = Math.PI; nozzle.add(guard);
  const lever = new THREE.Mesh(new RoundedBoxGeometry(0.1, 0.012, 0.02, 2, 0.004), steel); lever.position.set(0.0, -0.045, 0); lever.rotation.z = -0.15; nozzle.add(lever);
  const spout = new THREE.Mesh(new THREE.CylinderGeometry(0.0125, 0.0125, 0.16, 16), steel); spout.position.set(0.17, -0.045, 0); spout.rotation.z = Math.PI / 2 - 0.5; nozzle.add(spout);
  const back = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 0.06, 14), blk); back.position.set(-0.08, 0.01, 0); back.rotation.z = Math.PI / 2; nozzle.add(back);
  const lab = canvasTex(256, 96, g => { g.fillStyle = '#1f9a4a'; g.fillRect(0, 0, 256, 96); g.fillStyle = '#fff'; g.font = 'bold 60px Inter, Arial'; g.textAlign = 'center'; g.fillText('DIESEL', 128, 70); });
  for (const s of [1, -1]) { const p = new THREE.Mesh(new THREE.PlaneGeometry(0.12, 0.045), new THREE.MeshStandardMaterial({ map: lab, roughness: 0.5 })); p.position.set(0.02, 0, s * 0.0255); if (s < 0) p.rotation.y = Math.PI; nozzle.add(p); }
  nozzle.traverse(o => { if (o.isMesh) o.castShadow = true; }); }
const hose = new THREE.Mesh(new THREE.BufferGeometry(), new THREE.MeshStandardMaterial({ color: 0x1b1c1e, roughness: 0.7 })); hose.castShadow = true; scene.add(hose);
const HOSE0 = V(PUMPX + 0.32, 0.18 + 1.55, 1.15);                  // where the hose leaves the pump
function setHose(end, endDir) { const a = HOSE0, b = end.clone().addScaledVector(endDir, -0.08); const mid = a.clone().lerp(b, 0.5); mid.y = Math.min(a.y, b.y) - 0.55;
  hose.geometry.dispose(); hose.geometry = new THREE.TubeGeometry(new THREE.CatmullRomCurve3([a, a.clone().add(V(0.12, -0.25, 0)), mid, b.clone().add(V(-0.08, -0.12, 0)), b, end]), 48, 0.014, 8, false); }
const macro = new THREE.Group(); scene.add(macro); macro.visible = false;

// ------------------------------------------------------------------ the fuel system (x-ray, car space): tank, pump in the tank, the line to the engine, injectors
const fuelSys = new THREE.Group();
const ghostable = [];                                             // car materials that go see-through in the x-ray
const tank = new THREE.Mesh(new RoundedBoxGeometry(0.9, 0.22, 0.55, 3, 0.05), new THREE.MeshPhysicalMaterial({ color: 0x9aa3ad, metalness: 0.3, roughness: 0.4, transparent: true, opacity: 0.45, depthWrite: false })); tank.position.set(0, 0.36, 1.25); fuelSys.add(tank);
const tankFuel = new THREE.Mesh(new RoundedBoxGeometry(0.86, 0.16, 0.51, 3, 0.04), new THREE.MeshStandardMaterial({ color: 0x5ad65a, emissive: 0x1f7a1f, emissiveIntensity: 0.7, transparent: true, opacity: 0.8 })); tankFuel.position.set(0, 0.34, 1.25); fuelSys.add(tankFuel);
const fpump = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.18, 18), new THREE.MeshStandardMaterial({ color: 0xffb02a, emissive: 0x7a4a00, emissiveIntensity: 0.6 })); fpump.position.set(0.2, 0.38, 1.25); fuelSys.add(fpump);
const LINE = new THREE.CatmullRomCurve3([V(0.2, 0.47, 1.25), V(0.25, 0.3, 1.0), V(0.3, 0.26, 0.2), V(0.32, 0.27, -0.8), V(0.3, 0.45, -1.4), V(0.15, 0.72, -1.55), V(0.0, 0.8, -1.6)]);
fuelSys.add(new THREE.Mesh(new THREE.TubeGeometry(LINE, 80, 0.012, 8, false), new THREE.MeshStandardMaterial({ color: 0xcfd6dd, transparent: true, opacity: 0.6 })));
const engineBlock = new THREE.Mesh(new RoundedBoxGeometry(0.62, 0.38, 0.5, 3, 0.05), new THREE.MeshPhysicalMaterial({ color: 0x8a8f96, metalness: 0.5, roughness: 0.4, transparent: true, opacity: 0.55, depthWrite: false })); engineBlock.position.set(0, 0.68, -1.62); fuelSys.add(engineBlock);
const slugs = new THREE.InstancedMesh(new THREE.SphereGeometry(1, 12, 8), new THREE.MeshStandardMaterial({ color: 0x6aff6a, emissive: 0x2aa02a, emissiveIntensity: 1.2 }), 40); fuelSys.add(slugs);
fuelSys.visible = false; car.add(fuelSys); fuelSys.traverse(o => { o.userData.noGhost = true; });
const GHOST = new THREE.MeshStandardMaterial({ color: 0x4aa3ff, emissive: 0x1a4a8a, emissiveIntensity: 0.6, transparent: true, opacity: 0.13, depthWrite: false, side: THREE.DoubleSide });
let XR_ON = false;
const key = new THREE.Group(); key.position.set(-0.3, 0.86, -0.42); car.add(key); key.visible = false;      // the ignition key (x-ray beat), next to the steering column
{ const km = new THREE.MeshStandardMaterial({ color: 0xffd34a, emissive: 0xffb000, emissiveIntensity: 1.2 });
  const head = new THREE.Mesh(new THREE.TorusGeometry(0.035, 0.012, 10, 24), km); head.position.y = 0.05; key.add(head);
  const blade = new THREE.Mesh(new THREE.BoxGeometry(0.014, 0.07, 0.006), km); key.add(blade); key.rotation.y = Math.PI / 2;
  key.traverse(o => { o.userData.noGhost = true; }); key.scale.setScalar(1.6); }

// ------------------------------------------------------------------ dark stages: the engine cylinder (beats 2-3), the parts bill (beat 8)
function stage(pos, top, bot) { const g = new THREE.Group(); g.position.copy(pos); scene.add(g);
  const bg = new THREE.Mesh(new THREE.SphereGeometry(8, 32, 16), new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false,
    vertexShader: 'varying vec3 vD; void main(){ vD = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
    fragmentShader: `varying vec3 vD; void main(){ float h = vD.y * 0.5 + 0.5; vec3 c = mix(vec3(${bot.join(',')}), vec3(${top.join(',')}), h); gl_FragColor = vec4(pow(c, vec3(2.2)) * 2.5, 1.0); }` }));
  g.add(bg); const k = new THREE.DirectionalLight(0xffffff, 2.4); k.position.set(-1, 2, -3); g.add(k); g.add(k.target); const r = new THREE.PointLight(0x9fd0ff, 3, 6); r.position.set(1.5, -0.5, 1); g.add(r); return g; }
const CYL = V(-500, 0, 0);
const cylStage = stage(CYL, [0.12, 0.14, 0.2], [0.02, 0.02, 0.04]);
const steelM = new THREE.MeshStandardMaterial({ color: 0xb8bec6, metalness: 0.85, roughness: 0.35 });
const cylWall = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.3, 0.9, 48, 1, true), new THREE.MeshPhysicalMaterial({ color: 0xcfe2ff, roughness: 0.05, transparent: true, opacity: 0.18, side: THREE.DoubleSide, depthWrite: false })); cylStage.add(cylWall);
const cylHead = new THREE.Mesh(new THREE.CylinderGeometry(0.34, 0.34, 0.12, 48), steelM); cylHead.position.y = 0.51; cylStage.add(cylHead);
const plug = new THREE.Group(); plug.position.y = 0.45; cylStage.add(plug);
{ const ins = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 0.16, 16), new THREE.MeshStandardMaterial({ color: 0xf2f2ee, roughness: 0.3 })); ins.position.y = 0.18; plug.add(ins);
  const el = new THREE.Mesh(new THREE.CylinderGeometry(0.008, 0.008, 0.06, 8), steelM); el.position.y = -0.01; plug.add(el); }
const piston = new THREE.Group(); cylStage.add(piston);
{ const crown = new THREE.Mesh(new THREE.CylinderGeometry(0.29, 0.29, 0.18, 48), steelM); piston.add(crown);
  for (const y of [0.04, 0.0, -0.04]) { const r = new THREE.Mesh(new THREE.TorusGeometry(0.292, 0.006, 6, 48).rotateX(Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0x55595f, metalness: 0.9, roughness: 0.4 })); r.position.y = y; piston.add(r); }
  const rod = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.5, 0.04), steelM); rod.position.y = -0.33; piston.add(rod); }
const sparkLight = new THREE.PointLight(0x9fd0ff, 0, 2, 1.5); sparkLight.position.y = 0.4; cylStage.add(sparkLight);
const boom = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 20), new THREE.MeshBasicMaterial({ color: 0xffa040, transparent: true, opacity: 0.9, toneMapped: false, depthWrite: false })); boom.position.y = 0.3; cylStage.add(boom);
const boomLight = new THREE.PointLight(0xff8a2a, 0, 4, 1.4); boomLight.position.y = 0.25; cylStage.add(boomLight);
const softTex = canvasTex(64, 64, g => { const gr = g.createRadialGradient(32, 32, 0, 32, 32, 31); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.45, 'rgba(255,255,255,0.45)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); });
function cloud(n, size, color, op, parent = scene) { const g = new THREE.BufferGeometry(); const p = new Float32Array(n * 3); g.setAttribute('position', new THREE.BufferAttribute(p, 3));
  const m = new THREE.Points(g, new THREE.PointsMaterial({ map: softTex, color, size, transparent: true, depthWrite: false, opacity: op })); m.frustumCulled = false; parent.add(m); return { m, p, n }; }
function setCloud(c, fn) { let k = 0; for (let i = 0; i < c.n; i++) { const q = fn(i); if (q) { c.p.set([q.x, q.y, q.z], k * 3); k++; } } for (let i = k; i < c.n; i++) c.p.set([0, -999, 0], i * 3); c.m.geometry.attributes.position.needsUpdate = true; c.m.visible = k > 0; }
const mistC = cloud(260, 0.05, 0xffd890, 0.7, cylStage);          // gas mist (fine, light) / diesel droplets (big, green)
const oilC = cloud(90, 0.09, 0x7adf5a, 0.9, cylStage);
const sparks = cloud(60, 0.025, 0xbfe4ff, 1.0, cylStage);
const PARTS = V(0, 0, -500);
const partStage = stage(PARTS, [0.18, 0.06, 0.06], [0.03, 0.01, 0.02]);
const parts = [], tags = [];
{ const mk = (geo, mat, x, y) => { const m = new THREE.Mesh(geo, mat); m.userData.home = V(x, y, 0); partStage.add(m); parts.push(m); return m; };
  const orange = new THREE.MeshStandardMaterial({ color: 0xffb02a, roughness: 0.4 }), steel = steelM, blue = new THREE.MeshStandardMaterial({ color: 0x2f6bd6, roughness: 0.4 });
  mk(new THREE.CylinderGeometry(0.09, 0.09, 0.32, 24), orange, -0.2, 0.9);                                    // fuel pump
  for (let i = 0; i < 4; i++) mk(new THREE.CylinderGeometry(0.03, 0.02, 0.24, 14), steel, 0.08 + i * 0.09, 0.9);   // injectors
  mk(new RoundedBoxGeometry(0.46, 0.2, 0.24, 3, 0.06), steel, 0.0, 0.25);                                     // catalytic converter
  mk(new THREE.CylinderGeometry(0.07, 0.07, 0.24, 18), blue, 0.0, -0.3);                                         // fuel filter
  const tag = (txt, x, y) => { const t = canvasTex(512, 96, g => { g.fillStyle = '#fff'; g.font = 'bold 64px Inter, Arial'; g.textAlign = 'center'; g.fillText(txt, 256, 72); });
    const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: t, transparent: true, toneMapped: false })); sp.scale.set(0.42, 0.079, 1); sp.position.set(x, y, 0); partStage.add(sp); tags.push(sp); };
  tag('FUEL PUMP', -0.2, 0.66); tag('INJECTORS', 0.215, 0.66); tag('CONVERTER', 0.0, -0.06); tag('FUEL FILTER', 0.0, -0.52);
}

// ------------------------------------------------------------------ the tow truck (simple flatbed)
const tow = new THREE.Group(); scene.add(tow); tow.visible = false;
{ const white = new THREE.MeshPhysicalMaterial({ color: 0xf2f2f0, roughness: 0.35, clearcoat: 0.8 }), dark = new THREE.MeshStandardMaterial({ color: 0x1b1c1e, roughness: 0.6 }), yel = new THREE.MeshStandardMaterial({ color: 0xf2b21b, emissive: 0x6a4a00, emissiveIntensity: 0.6 });
  const cab = new THREE.Mesh(new RoundedBoxGeometry(2.2, 1.6, 2.0, 3, 0.15), white); cab.position.set(0, 1.35, -3.1); tow.add(cab);
  const ws = new THREE.Mesh(new THREE.PlaneGeometry(1.9, 0.6), new THREE.MeshPhysicalMaterial({ color: 0x223040, roughness: 0.05, metalness: 0.4 })); ws.position.set(0, 1.75, -4.11); ws.rotation.y = Math.PI; tow.add(ws);
  const bed = new THREE.Mesh(new THREE.BoxGeometry(2.3, 0.18, 5.2), new THREE.MeshStandardMaterial({ color: 0x3a3d42, roughness: 0.6 })); bed.position.set(0, 0.92, 0.6); tow.add(bed);
  const bar = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.12, 0.12), yel); bar.position.set(0, 2.2, -2.1); tow.add(bar);
  for (const [x, z] of [[-1.0, -3.0], [1.0, -3.0], [-1.0, 1.6], [1.0, 1.6], [-1.0, 2.6], [1.0, 2.6]]) { const w = new THREE.Mesh(new THREE.CylinderGeometry(0.45, 0.45, 0.32, 24).rotateZ(Math.PI / 2), dark); w.position.set(x, 0.45, z); tow.add(w); }
  tow.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } }); }


// ------------------------------------------------------------------ the car's fuel door (open) and filler neck, on the left rear quarter
{ const recess = new THREE.Mesh(new THREE.CircleGeometry(0.065, 32), new THREE.MeshStandardMaterial({ color: 0x3a3c40, roughness: 0.6 })); recess.position.copy(FILL_LOCAL).add(V(-0.008, 0, 0)); recess.rotation.y = -Math.PI / 2; car.add(recess);
  const neck = new THREE.Mesh(new THREE.TorusGeometry(0.0145, 0.006, 10, 28), new THREE.MeshStandardMaterial({ color: 0xa8adb3, metalness: 0.8, roughness: 0.35 })); neck.position.copy(FILL_LOCAL).add(V(-0.012, 0, 0)); neck.rotation.y = Math.PI / 2; car.add(neck);
  const hole = new THREE.Mesh(new THREE.CircleGeometry(0.0105, 24), new THREE.MeshBasicMaterial({ color: 0x000000 })); hole.position.copy(FILL_LOCAL).add(V(-0.011, 0, 0)); hole.rotation.y = -Math.PI / 2; car.add(hole);
  const flap = new THREE.Group(); flap.position.copy(FILL_LOCAL).add(V(-0.012, 0, 0.075)); flap.rotation.y = -1.9; car.add(flap);
  const fd = new THREE.Mesh(new THREE.CylinderGeometry(0.075, 0.075, 0.008, 32).rotateZ(Math.PI / 2), paint); fd.position.set(0, 0, -0.075); fd.castShadow = true; flap.add(fd); }

// ------------------------------------------------------------------ the guy
const G = await loadGuy(THREE, '/char/guy', {});
scene.add(G.root); G.root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
const HIP = V(0.0, 0.95, 0.0);
const HOME = V(-1.52, 0.95, 1.2);                                  // at the pump, facing the car (+x)
function untwistSafe() { for (const S of ['R', 'L']) { const ua = G.bones['uarm' + S], ut = G.bones['uarmTwist' + S]; ua.quaternion.multiply(ut.quaternion); ut.quaternion.identity(); } G.untwist(); }
function attach(obj, boneName) { G.reset(); G.root.updateMatrixWorld(true); obj.updateMatrixWorld(true); obj.applyMatrix4(G.bones[boneName].matrixWorld.clone().invert()); G.bones[boneName].add(obj); }
const phone = new THREE.Group(); scene.add(phone);
{ const p = new THREE.Mesh(new RoundedBoxGeometry(0.072, 0.15, 0.009, 2, 0.004), new THREE.MeshStandardMaterial({ color: 0x1a1b1e, roughness: 0.3, metalness: 0.4 })); phone.add(p);
  const sc = new THREE.Mesh(new THREE.PlaneGeometry(0.064, 0.138), new THREE.MeshBasicMaterial({ color: 0x3a8ad6, toneMapped: false })); sc.position.z = 0.0048; phone.add(sc); phone.visible = false; }
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
    return c; };
  const m = MEM[key]; const prev = m && m.frame === frame - 1 ? m.a : null;
  const seeds = prev ? [prev] : [A(40, 15, 0, 80, 0), A(60, 25, 20, 60, 40), A(30, 40, -20, 100, -30), A(80, 10, 0, 110, 60), A(50, 30, 30, 40, 70), A(20, 20, -30, 120, -60)];
  let best = null;
  for (const s0 of seeds) {
    let a = s0.map((v, i) => clamp(v, ARM_LIM[i][0], ARM_LIM[i][1])), ca = cost(a);
    for (let step = prev ? 4 : 16; step >= 0.25; step /= 2) { let imp = true, g = 0;
      while (imp && g++ < 10) { imp = false; for (let i = 0; i < 7; i++) for (const sg of [1, -1]) { const b = a.slice(); b[i] = clamp(b[i] + sg * step, ARM_LIM[i][0], ARM_LIM[i][1]); const cb = cost(b); if (cb < ca - 1e-9) { a = b; ca = cb; imp = true; } } } }
    if (!best || ca < best.c) best = { a, c: ca };
  }
  MEM[key] = { frame, a: best.a }; return best;
}


// ------------------------------------------------------------------ head points (mouth, right ear) and helpers
const MOUTH = new THREE.Object3D(); MOUTH.position.set(0, G.man.mouthY, G.man.mouthZ); attach(MOUTH, 'head');
const EARR = new THREE.Object3D(); EARR.position.set(0.078, 1.632, 0.005); attach(EARR, 'head');
G.reset();
const wpos = o => o.getWorldPosition(new THREE.Vector3());
const yawQ = deg => new THREE.Quaternion().setFromAxisAngle(V(0, 1, 0), deg * D2R);

// ------------------------------------------------------------------ the nozzle's pose: in the filler (pumping), or on its way in (beats 6, 9)
const FILL_W = () => FILL_LOCAL.clone().applyMatrix4(car.matrixWorld);
const NOZQ = new THREE.Quaternion().setFromEuler(new THREE.Euler(0, 0, 0));         // spout tip points +x and down, handle up and back (toward him)
function nozzleAt(insert) {                                     // insert 1 = tip in the filler; 0 = 22 cm back and a little up
  const tipLocal = NOZ.tip.clone().applyQuaternion(NOZQ), fill = FILL_W();
  const tipW = fill.clone().add(V(-0.012 + 0.03 * (1 - insert), 0.0, 0)).add(V(-0.22, 0.1, 0).multiplyScalar(1 - insert));
  return { q: NOZQ.clone(), p: tipW.clone().sub(tipLocal) };
}
function nozzleGrip(nz) {                                        // a real pump grip: hand on the right side of the handle, thumb along the top, fingers wrapped under onto the lever
  const n = V(0, -0.5, -0.85).normalize(), u = V(0, -0.85, 0.5).normalize();   // palm faces in (his left) and a little down; fingers point down, then curl under
  return { S: 'R', p: nz.p.clone().add(V(0.02, 0.022, 0.036).applyQuaternion(nz.q)), n: n.applyQuaternion(nz.q), u: u.applyQuaternion(nz.q), c: 78 };
}

// ------------------------------------------------------------------ the story
function blink(t) { for (const b0 of [1.6, 9.3, 15.0, 20.2, 27.7, 31.6]) { const u = (t - b0) / 0.16; if (u > 0 && u < 1) return Math.sin(Math.PI * u); } return 0; }
const FEETAT = (hp, yaw) => { const q = yawQ(yaw); return { R: hp.clone().setY(0.102).add(V(0.11, 0, -0.03).applyQuaternion(q)), L: hp.clone().setY(0.102).add(V(-0.11, 0, 0.02).applyQuaternion(q)) }; };
function carPose(t) {                                            // where the car is: at the pump, on the road, on the tow truck
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  if (b === 4) { const stop = d - 0.9, k = clamp(lt / stop, 0, 1); const z = lerp(26, 2, 1 - (1 - k) ** 1.7);                  // drives up, slows, dies
    const buck = smooth(1.2, 2.0, lt) * (1 - smooth(stop - 0.2, stop + 0.4, lt)); return { x: ROADX + 1.6, z, pitch: 2.2 * buck * Math.sin(lt * 17) * Math.max(0, Math.sin(lt * 5.3)), roll: 0.8 * buck * Math.sin(lt * 11) }; }
  if (b === 5) return { x: ROADX + 1.6, z: 2, pitch: 0, roll: 0 };
  if (b === 7) { const z = 2 - 18 * smooth(0.6, d, lt) * smooth(0.6, d, lt); return { x: ROADX + 1.6, z, y: 1.01, pitch: 0, roll: 0, onTow: true }; }
  return { x: 0, z: 0, pitch: 0, roll: 0 };
}
// idle life that loops exactly: every wave fits a whole number of times into the video, so frame one and the last frame match
const IDLE = (t, k) => 2 * Math.sin(2 * Math.PI * [9, 7, 5, 6][k] * t / TOTAL + k * 1.7);
const PHONEBOB = t => V(0.006 * Math.sin(2 * Math.PI * 11 * t / TOTAL), 0.008 * Math.sin(2 * Math.PI * 8 * t / TOTAL + 1.0), 0.005 * Math.sin(2 * Math.PI * 6 * t / TOTAL + 2.0));
function guyAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  let pose = P.stand, root = {}, face = { blink: blink(t) }, hands = [], show = true, phoneHand = null, insert = 1, pumping = false;
  if (b === 0) {                                                 // pumping, eyes on his phone (left hand), not on the pump
    pose = addPose(P.stand, { neck: [-26 + IDLE(t, 0), 10 + IDLE(t, 1) * 1.5, 0], head: [-10, 8, 0], spine2: [IDLE(t, 2) * 0.6, 8, IDLE(t, 3) * 0.8] }); pumping = true;
    hands = [{ grip: true }, { S: 'L', p: V(-1.32, 1.12, 1.07).add(PHONEBOB(t)), n: V(0.15, 1, 0.2).normalize(), u: V(0.85, 0.15, -0.4).normalize(), c: 18 }]; phoneHand = 'L';
    face = { ...face, look: [0.1, -0.6], smile: 0.25 };
  } else if (b === 9) {                                          // puts the nozzle in, squeezes (ends on frame one, phone up)
    insert = smooth(0.15, d - 0.6, lt);
    pose = addPose(P.stand, { neck: [-18 - 8 * smooth(d - 0.7, d, lt) + IDLE(t, 0), 10 * smooth(d - 0.7, d, lt) + IDLE(t, 1) * 1.5, 0], head: [-6 - 4 * smooth(d - 0.7, d, lt), 8 * smooth(d - 0.7, d, lt), 0], spine2: [IDLE(t, 2) * 0.6, 8 * smooth(d - 0.7, d, lt), IDLE(t, 3) * 0.8] });
    hands = [{ grip: true }, { S: 'L', p: V(-1.32, 1.12, 1.07).add(PHONEBOB(t)), n: V(0.15, 1, 0.2).normalize(), u: V(0.85, 0.15, -0.4).normalize(), c: 18 }]; phoneHand = 'L'; pumping = lt > d - 0.6;
    face = { ...face, look: [0.1, -0.6 * smooth(d - 0.7, d, lt) - 0.2], smile: 0.25 };
  } else if (b === 6) {                                          // macro: he forces the fat spout into the filler (we see his hand)
    { const bump = (c, w) => Math.exp(-(((lt - c) / w) ** 2));                          // comes in, knocks the ring twice (too wide to go in), then rests at the mouth and pours anyway
      insert = 0.55 + 0.37 * smooth(0, d * 0.25, lt) + 0.06 * (bump(d * 0.33, 0.07) + bump(d * 0.5, 0.07)) + 0.08 * smooth(d * 0.62, d * 0.78, lt); }
    pose = addPose(P.stand, { neck: [-20, 0, 0], spine1: [-6, 0, 0] }); hands = [{ grip: true }];
    face = { ...face, browIn: 0.6, press: 0.5 };
  } else if (b === 5) {                                          // roadside: phone at his ear, waiting for the tow
    root = { x: ROADX - 0.2, z: 3.2, yaw: 150 }; phoneHand = 'R';
    hands = [{ S: 'R', ear: true, c: 40 }];
    pose = addPose(P.stand, { neck: [2 + 3 * Math.sin(lt * 2.1), -12 + 4 * Math.sin(lt * 0.9), 0], spine2: [0, 0, 1.5 * Math.sin(lt * 1.3)], spine1: [0, 3 * Math.sin(lt * 0.7), 0] });
    face = { ...face, frown: 0.3, browIn: 0.4, jaw: 0.1 * Math.max(0, Math.sin(lt * 9)), look: [0.3, 0] };
  } else show = false;                                           // not on screen: inside the car (4), x-ray (1), stages (2, 3, 8), on the tow (7)
  return { pose, root, face, hands, show, phoneHand, insert, pumping };
}

// ------------------------------------------------------------------ cameras
function shake(t, a, f = 1) { return V(vn1(t * 3 * f, 1) * a, vn1(t * 3 * f, 2) * a, vn1(t * 3 * f, 3) * a * 0.5); }
const HOOK = { pos: V(-0.6, 1.5, 3.15), tgt: V(-1.42, 1.1, 1.3), fov: 48 };
function camAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b], u = lt / d;
  let pos, tgt, fov = 42;
  if (b === 0) { pos = HOOK.pos.clone().add(V(0.03 * u, -0.02 * u, -0.18 * u)); tgt = HOOK.tgt.clone(); fov = HOOK.fov; }
  else if (b === 9) { const w = smooth(d - 1.2, d, lt); pos = V(-0.7, 1.5, 3.4).lerp(HOOK.pos, w); tgt = V(-1.2, 1.05, 1.3).lerp(HOOK.tgt, w); fov = lerp(46, HOOK.fov, w); }
  else if (b === 1) { pos = V(-2.1 + 0.3 * u, 2.7, 4.9 - 0.3 * u); tgt = V(0, 0.5, -0.3); fov = 40; }
  else if (b === 2 || b === 3) { pos = CYL.clone().add(V(0.55 * (b === 2 ? 1 : -1) * (1 - 0.2 * u), 0.25, -1.55 + 0.15 * u)); tgt = CYL.clone().add(V(0, 0.15, 0)); fov = 40; }
  else if (b === 4) { const c = carPose(t); pos = V(ROADX - 3.2, 1.3, c.z - 4.0 + 1.5 * u); tgt = V(c.x, 0.7, c.z - 0.3); fov = 40; pos.add(shake(t, 0.01, 2)); }
  else if (b === 5) { pos = V(ROADX - 2.6, 1.5, 7.6); tgt = V(ROADX + 0.4, 1.0, 0.3); fov = 44; }
  else if (b === 6) { const f = FILL_W(); pos = f.clone().add(V(-0.25, -0.02, -0.21 + 0.03 * u)); tgt = f.clone().add(V(-0.05, 0.015, 0)); fov = 46; pos.add(shake(t, 0.004 * (Math.exp(-(((lt - d * 0.33) / 0.08) ** 2)) + Math.exp(-(((lt - d * 0.5) / 0.08) ** 2))), 6)); }
  else if (b === 7) { const c = carPose(t); pos = V(ROADX - 4.2, 1.6, 8.5); tgt = V(c.x - 0.3, 1.3, c.z - 1.5); fov = 42; }
  else { pos = PARTS.clone().add(V(0.1 * Math.sin(lt * 0.6), 0.4, -2.75 + 0.2 * u)); tgt = PARTS.clone().add(V(0, 0.33, 0)); fov = 40; }
  const punch = b > 0 ? (1 - smooth(0, 0.22, lt)) * 0.07 : 0;
  return { pos, tgt, fov: fov * (1 - punch) };
}

// ------------------------------------------------------------------ clipping: body points and props tested against solid boxes (car body, pump, ground)
const SOLIDS = [];                                               // { name, box (local), obj (frame), allow: [point names allowed inside] }
SOLIDS.push({ name: 'car body', obj: car, box: new THREE.Box3(V(-0.9, 0.32, -2.28), V(0.9, 0.93, 2.28)) });
SOLIDS.push({ name: 'car cabin', obj: car, box: new THREE.Box3(V(-0.86, 0.93, -0.72), V(0.86, 1.42, 1.12)) });
SOLIDS.push({ name: 'pump island', obj: STATION, box: new THREE.Box3(V(PUMPX - 0.5, 0, -1.3), V(PUMPX + 0.5, 0.18, 3.3)) });
SOLIDS.push({ name: 'pump', obj: pump, box: new THREE.Box3(V(-0.31, 0, -0.45), V(0.31, 1.95, 0.45)) });
const BODYPTS = { handR: 0.04, handL: 0.04, index2R: 0.012, index2L: 0.012, pinky2R: 0.012, pinky2L: 0.012, thumb2R: 0.012, thumb2L: 0.012, farmR: 0.035, farmL: 0.035, uarmR: 0.045, uarmL: 0.045, head: 0.09, chest: 0.13, hips: 0.12, shinR: 0.05, shinL: 0.05, footR: 0.04, footL: 0.04 };
function clipScan() {                                            // -> [{what, into, depth cm}] for this frame
  const out = []; if (!G.root.visible) return out;
  const pts = Object.entries(BODYPTS).map(([n, r]) => [n, G.bones[n].getWorldPosition(new THREE.Vector3()), r]);
  for (const S of ['R', 'L']) for (const f of ['index', 'middle', 'pinky', 'thumb']) { const p1 = G.bones[f + '1' + S].getWorldPosition(new THREE.Vector3()), p2 = G.bones[f + '2' + S].getWorldPosition(new THREE.Vector3());
    pts.push([f + ' tip ' + S, p2.clone().multiplyScalar(2).sub(p1), 0.008]); }                       // fingertip ~ one segment past the middle knuckle
  if (nozzle.visible) pts.push(['nozzle handle', nozzle.position.clone(), 0.02]);
  if (phone.visible) pts.push(['phone', phone.position.clone(), 0.01]);
  for (const [n, p, r] of pts) {
    if (n.startsWith('foot') && p.y < 0.06) out.push({ what: n, into: 'ground', depth: (0.06 - p.y) * 100 });
    for (const S of SOLIDS) { if (!S.obj.visible) continue; const inv = S.obj.matrixWorld.clone().invert(); const q = p.clone().applyMatrix4(inv);
      const bx = S.box; const dx = Math.min(q.x - bx.min.x, bx.max.x - q.x), dy = Math.min(q.y - bx.min.y, bx.max.y - q.y), dz = Math.min(q.z - bx.min.z, bx.max.z - q.z);
      const d = Math.min(dx, dy, dz) + r; if (dx > -r && dy > -r && dz > -r && d > 0.012) out.push({ what: n, into: S.name, depth: +(d * 100).toFixed(1) }); }
  }
  return out;
}

// ------------------------------------------------------------------ per-frame update
let gallons = 0;
function update(t, frame = Math.round(t * FPS)) {
  t = ((t % TOTAL) + TOTAL) % TOTAL;
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  // the car
  const cp = carPose(t);
  car.position.set(cp.x, cp.y ?? 0, cp.z); car.rotation.set(cp.pitch * D2R, 0, cp.roll * D2R); car.updateMatrixWorld(true);
  // the guy
  const g = guyAt(t);
  const yaw = g.root.yaw ?? -90, hx = g.root.x ?? HOME.x, hz = g.root.z ?? HOME.z;
  applyPose(g.pose, { x: hx, z: hz, yaw });
  const flat = yawQ(yaw), feet = FEETAT(V(hx, 0, hz), yaw);
  for (const S of ['R', 'L']) G.legIK(S, feet[S], feet[S].clone().add(V(0, 0.45, -1.0).applyQuaternion(flat)), flat);
  G.root.updateMatrixWorld(true);
  // the nozzle first (it sits in the filler, or rides on its path), then the hand goes to it
  const nz = nozzleAt(g.insert);
  nozzle.position.copy(nz.p); nozzle.quaternion.copy(nz.q); nozzle.visible = b === 0 || b === 6 || b === 9;
  for (const h0 of g.hands) {
    let h = { ...h0 };
    if (h.grip) h = nozzleGrip(nz);
    if (h.ear) { const e = wpos(EARR); h.p = e.add(V(0.03, -0.015, -0.02).applyQuaternion(flat)); h.n = V(-1, 0, 0).applyQuaternion(flat); h.u = V(0, 0.85, 0.5).normalize().applyQuaternion(flat); }
    const sol = solveHand(h, 'h' + h.S + b + (h0.grip ? 'g' : h0.ear ? 'e' : ''), frame); setArm(h.S, sol.a); LAST['arm' + h.S] = sol.a; LAST['cost' + h.S] = sol.c;
    const pp = {}; curl(pp, h.S, h.c ?? 30); for (const [n, e] of Object.entries(pp)) G.bones[n].quaternion.copy(G.REST[n].q).multiply(qTmp.setFromEuler(eTmp.set(e[0] * D2R, e[1] * D2R, e[2] * D2R)));
  }
  G.root.updateMatrixWorld(true);
  untwistSafe(); G.face(g.face); G.root.visible = g.show; G.root.updateMatrixWorld(true);
  // the hose follows the nozzle
  hose.visible = nozzle.visible; if (hose.visible) setHose(nozzle.position.clone().add(V(-0.1, 0.01, 0).applyQuaternion(nozzle.quaternion)), V(1, 0, 0).applyQuaternion(nozzle.quaternion));
  // the phone (in his left palm, or at his right ear)
  phone.visible = !!g.phoneHand && g.show;
  if (phone.visible) { const S = g.phoneHand, hb = G.bones['hand' + S]; hb.updateMatrixWorld(true); const q = hb.getWorldQuaternion(new THREE.Quaternion());
    const n = HANDREST[S].n.clone().applyQuaternion(q), u = HANDREST[S].u.clone().applyQuaternion(q), p = PALM(S).applyMatrix4(hb.matrixWorld);
    const zb = n.clone(), yb = u.clone().sub(zb.clone().multiplyScalar(u.dot(zb))).normalize(), xb = new THREE.Vector3().crossVectors(yb, zb);
    phone.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(xb, yb, zb)); phone.position.copy(p).addScaledVector(n, 0.012).addScaledVector(u, 0.02); }
  // the pump display counts while pumping
  gallons = b === 0 ? 6.2 + lt * 0.45 : b === 9 ? 6.2 - 0.45 * Math.min(0.6, d - lt) : 6.2 + 0.45 * DUR[0]; drawPrice(Math.max(0, gallons));
  // the x-ray car (beat 1): see-through body, fuel system, diesel slugs pushed down the line once the key turns
  const xr = b === 1;
  fuelSys.visible = xr;
  if (xr !== XR_ON) { XR_ON = xr; car.traverse(o => { if (!o.isMesh || o.userData.noGhost) return; if (!o.userData.mat0) o.userData.mat0 = o.material; o.material = xr ? GHOST : o.userData.mat0; o.castShadow = !xr; }); }
  key.visible = xr; if (xr) key.rotation.z = -1.3 * smooth(d * 0.22, d * 0.32, lt);
  if (xr) { const on = smooth(d * 0.3, d * 0.4, lt), m4 = new THREE.Matrix4();
    for (let i = 0; i < 40; i++) { const s = ((lt - d * 0.35) * 0.35 + i / 40) % 1; const ok = lt > d * 0.35 && (i / 40) < (lt - d * 0.35) * 0.6; const p = LINE.getPoint(clamp(s, 0, 1)); const r = ok ? 0.02 : 0.0001;
      m4.compose(p, new THREE.Quaternion(), V(r, r, r)); slugs.setMatrixAt(i, m4); } slugs.instanceMatrix.needsUpdate = true;
    fpump.material.emissiveIntensity = 0.6 + 1.2 * on * (0.6 + 0.4 * Math.sin(lt * 30)); }
  // the cylinder (beats 2-3): piston up and down, mist / oily drops, spark, boom (gas) or fizzle (diesel)
  cylStage.visible = b === 2 || b === 3;
  if (cylStage.visible) { const cyc = 1.25, ph = (lt % cyc) / cyc, gas = b === 2;
    const fire = gas ? Math.exp(-(((ph - 0.5) / 0.06) ** 2)) : 0;
    const py = gas ? (ph < 0.5 ? lerp(-0.25, 0.18, sm(ph / 0.5)) : lerp(0.18, -0.25, 1 - (1 - (ph - 0.5) / 0.5) ** 3)) : lerp(-0.2, 0.12, sm(clamp(lt / (d * 0.5), 0, 1))) + 0.01 * Math.sin(lt * 3);
    piston.position.y = py - 0.0;
    const spk = Math.exp(-(((ph - 0.48) / 0.025) ** 2));
    sparkLight.intensity = 6 * spk;
    boom.visible = gas && fire > 0.05; boom.scale.setScalar(0.05 + 0.28 * fire); boom.position.y = (py + 0.09 + 0.45) / 2; boom.material.opacity = 0.85 * fire; boomLight.intensity = 25 * fire;
    setCloud(mistC, i => { if (!gas || (ph > 0.5 && ph < 0.75)) return null; const a = hash1(i * 1.3) * 6.28, r = Math.sqrt(hash1(i * 2.1)) * 0.27; return V(Math.cos(a) * r, py + 0.1 + hash1(i * 3.7) * (0.43 - py), Math.sin(a) * r); });
    setCloud(oilC, i => { if (gas) return null; const a = hash1(i * 1.3) * 6.28, r = Math.sqrt(hash1(i * 2.1)) * 0.25; return V(Math.cos(a) * r, py + 0.1 + (hash1(i * 3.7) * 0.25) * (1 - 0.3 * Math.sin(lt * 2 + i)), Math.sin(a) * r); });
    setCloud(sparks, i => { if (spk < 0.05 && !(!gas && ((lt * 1.6) % 1) < 0.12)) return null; const s2 = gas ? spk : 1 - ((lt * 1.6) % 1) / 0.12; const a = hash1(i) * 6.28, r = 0.05 * hash1(i * 3) * (1 + 2 * (1 - s2)); return V(Math.cos(a) * r, 0.43 - 0.06 * hash1(i * 5), Math.sin(a) * r); });
    if (!gas) sparkLight.intensity = 3 * (((lt * 1.6) % 1) < 0.12 ? 1 : 0); }
  // the parts bill (beat 8)
  partStage.visible = b === 8;
  if (partStage.visible) parts.forEach((m, i) => { const k = smooth(0.15 * i, 0.15 * i + 0.6, lt); m.position.copy(m.userData.home).multiplyScalar(k).add(V(0, (1 - k) * 2.2, 0)); m.rotation.set(lt * 0.7 + i, lt * 0.5 + i * 2, 0); }); tags.forEach((sp, i) => { sp.material.opacity = smooth(0.5 + 0.2 * i, 0.8 + 0.2 * i, lt); });
  // the tow truck (beats 5, 7)
  tow.visible = b === 5 || b === 7;
  if (b === 5) { tow.position.set(ROADX + 1.6, 0, -9.5 + 2.2 * smooth(0.4, d, lt)); tow.rotation.y = 0; }
  if (b === 7) { tow.position.set(ROADX + 1.6, 0, car.position.z - 0.6); tow.rotation.y = 0; }
  // what is shown where
  const darkSet = b === 1 || b === 2 || b === 3 || b === 8;
  STATION.visible = !darkSet; ground.visible = !darkSet; tow.visible = tow.visible && !darkSet; nozzle.visible = nozzle.visible && !darkSet; hose.visible = hose.visible && !darkSet; road.visible = b === 4 || b === 5 || b === 7;
  car.visible = !(b === 2 || b === 3 || b === 8);
  sun.position.copy(car.position).addScaledVector(SUNDIR, 20); sun.target.position.copy(car.position); sun.target.updateMatrixWorld();
  const C = camAt(t); camera.position.copy(C.pos); camera.lookAt(C.tgt); camera.fov = C.fov; camera.updateProjectionMatrix();
  sky.visible = !darkSet; scene.background = darkSet ? new THREE.Color(b === 1 ? 0x061024 : 0x060a14) : null;
  return { beat: b, t };
}

// ------------------------------------------------------------------ frame I/O (same contract as the other 3D Shorts)
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
let lastFrame = -10;
// loop seam: frame one's hands are warm-started from the solutions at the end of beat 9 (same targets), so nothing jumps at the loop
let SEAM = null;
function primeSeam() { const f0 = Math.round(B[9] * FPS), f1 = Math.round(TOTAL * FPS) - 1; for (let j = f0; j <= f1; j++) update(j / FPS, j);
  SEAM = { hR0g: MEM['hR9g'].a.slice(), hL0: MEM['hL9'].a.slice() }; }
function stepTo(i) { const t = i / FPS, b = beatAt(((t % TOTAL) + TOTAL) % TOTAL);
  if (SEAM === null) primeSeam();
  if (i === 0 || (b === 0 && i !== lastFrame + 1)) for (const k in SEAM) MEM[k] = { frame: -1, a: SEAM[k].slice() };
  if (i !== lastFrame + 1) { const f0 = Math.max(0, Math.round(B[b] * FPS)); for (let j = f0; j < i; j++) update(j / FPS, j); }
  update(t, i); lastFrame = i; }
function renderInto(i) { stepTo(i); draw(); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); }
window.renderAll = async (f0, f1) => { for (let i = f0; i < f1; i++) { renderInto(i); await fetch('/frame', { method: 'POST', body: px }); } return 'ok'; };
window.renderAtT = t => { stepTo(Math.round(t * FPS)); if (window.CAM) { camera.position.set(...window.CAM.pos); camera.lookAt(...window.CAM.tgt); camera.fov = window.CAM.fov || 42; camera.updateProjectionMatrix(); } draw(); return renderer.domElement.toDataURL('image/png'); };
window.rigReport = i => { stepTo(i); const t = i / FPS;
  return { t, beat: beatAt(t), ang: LAST, hips: G.bones.hips.getWorldPosition(new THREE.Vector3()).toArray(), car: 0, show: G.root.visible,
    thumbs: ['R', 'L'].map(S => G.bones['index1' + S].getWorldPosition(new THREE.Vector3()).sub(G.bones['pinky1' + S].getWorldPosition(new THREE.Vector3())).applyQuaternion(G.root.getWorldQuaternion(new THREE.Quaternion()).invert()).toArray()),
    forearms: ['R', 'L'].map(S => G.bones['hand' + S].getWorldPosition(new THREE.Vector3()).sub(G.bones['farm' + S].getWorldPosition(new THREE.Vector3())).normalize().applyQuaternion(G.root.getWorldQuaternion(new THREE.Quaternion()).invert()).toArray()),
    cost: [LAST.costR ?? null, LAST.costL ?? null], clip: clipScan() }; };
window.clipTest = (i, dx) => { stepTo(i); G.root.position.x += dx; G.root.updateMatrixWorld(true); const r = clipScan(); stepTo(i); return r; };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS);
window.READY = true;
