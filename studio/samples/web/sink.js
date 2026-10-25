// "What happens if your car goes into water" - a 3D Short with the sculpted, skinned guy in a sinking car.
//   sink.html?w=1080&h=1920            (times from sink/times.json; one shot per narration line)
// Beats: 0 the car noses into the lake, splash (hook) | 1 cutaway: it floats, about a minute | 2 inside: hand on the door
//        3 cutaway: water up to the window, 1,000+ lb on the door | 4 inside, flooded and dark: holding his breath, the door creaks open
//        5 seatbelt off | 6 power window down, water pours in | 7 stuck: escape tool at the corner, the glass bursts
//        8 underwater: he swims out the window and up | 9 the car rolls down the boat ramp (loops into beat 0)
// World: lake surface y = 0 for z < 0 (the shore and ramp are z > 0). The car group carries the guy (he is its child), so every
// hand target is given in CAR space. His left (L) is -x = the driver's door; he faces -z = the car's front.
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
const TIMES = await (await fetch('/sink/times.json')).json();
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

// ------------------------------------------------------------------ renderer / scene / light: a bright afternoon at a lake
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(W, H);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.0;
renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.localClippingEnabled = true;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(42, W / H, 0.03, 900);
const SUNDIR = V(0.45, 0.62, 0.64).normalize();               // sun high behind the camera's usual side
const skyMat = new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false, fog: false, uniforms: { uSun: { value: SUNDIR } },
  vertexShader: 'varying vec3 vD; void main(){ vD = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
  fragmentShader: `varying vec3 vD; uniform vec3 uSun;
    void main(){ float h = clamp(vD.y, -0.2, 1.0);
      vec3 top = vec3(0.25, 0.48, 0.85), hor = vec3(0.82, 0.88, 0.94);
      vec3 c = mix(hor, top, smoothstep(0.0, 0.55, h));
      float s = max(dot(normalize(vD), uSun), 0.0); c += vec3(1.0, 0.95, 0.85) * (pow(s, 12.0) * 0.25 + pow(s, 900.0) * 5.0);
      c = mix(c, vec3(0.55, 0.62, 0.62), 1.0 - smoothstep(-0.2, 0.0, vD.y));
      gl_FragColor = vec4(pow(c, vec3(2.2)) * 0.95, 1.0); }` });
const sky = new THREE.Mesh(new THREE.SphereGeometry(600, 48, 24), skyMat); scene.add(sky);
{ const pm = new THREE.PMREMGenerator(renderer); const es = new THREE.Scene(); es.add(new THREE.Mesh(new THREE.SphereGeometry(10, 32, 16), skyMat));
  scene.environment = pm.fromScene(es, 0.02).texture; scene.environmentIntensity = 0.55; }
const hemi = new THREE.HemisphereLight(0xcfe2ff, 0x5b6a4a, 0.7); scene.add(hemi);
const sun = new THREE.DirectionalLight(0xfff1dc, 2.6); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
{ const S = sun.shadow.camera; S.left = -4; S.right = 4; S.top = 4; S.bottom = -4; S.near = 0.5; S.far = 40; sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.02; }
scene.add(sun); scene.add(sun.target);
const underFog = new THREE.FogExp2(0x123a3a, 0.32);
const surfLight = new THREE.SpotLight(0x9fe0d8, 0, 12, 0.7, 0.8, 1.0); scene.add(surfLight); scene.add(surfLight.target);

// ------------------------------------------------------------------ shore, boat ramp, trees across the lake
const RAMP = { z0: 16, z1: -2.5, y0: 1.15, y1: -1.2, w: 4.2 };          // concrete ramp running down into the water (-z)
const SHOREZ = x => 30 * smooth(4.5, 14, Math.abs(x));                        // the bank curves away from the ramp
const rampY = z => lerp(RAMP.y0, RAMP.y1, clamp((RAMP.z0 - z) / (RAMP.z0 - RAMP.z1), 0, 1));
const shoreMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.95 });
shoreMat.onBeforeCompile = sh => {
  sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vW;').replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvW = (modelMatrix * vec4(transformed, 1.0)).xyz;');
  sh.fragmentShader = sh.fragmentShader.replace('#include <common>', `#include <common>
varying vec3 vW;
float hh(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
float vn(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f*f*(3.0-2.0*f); return mix(mix(hh(i), hh(i+vec2(1,0)), u.x), mix(hh(i+vec2(0,1)), hh(i+vec2(1,1)), u.x), u.y); }`)
    .replace('#include <color_fragment>', `#include <color_fragment>
  { vec2 P = vW.xz; float n = vn(P * 0.6) * 0.6 + vn(P * 3.0) * 0.4;
    vec3 grass = mix(vec3(0.24, 0.36, 0.14), vec3(0.36, 0.45, 0.18), n);
    vec3 mud = vec3(0.36, 0.30, 0.22) * (0.8 + 0.3 * n);
    float bank = 1.0 - smoothstep(0.0, 0.6, vW.y);        // wet mud at the water's edge
    diffuseColor.rgb = mix(grass, mud, bank) * (vW.y < 0.02 ? 0.55 : 1.0); }`);
};
const shoreGeo = new THREE.PlaneGeometry(200, 120, 160, 96); shoreGeo.rotateX(-Math.PI / 2); shoreGeo.translate(0, 0, 60);
{ const p = shoreGeo.attributes.position;
  for (let i = 0; i < p.count; i++) { const x = p.getX(i), z0 = p.getZ(i), z = z0 - SHOREZ(x);
    let y = Math.min(1.2, z * 0.35) - 0.9 * smooth(2, -2, z) + 0.25 * Math.sin(x * 0.11) * smooth(4, 20, z);
    if (Math.abs(x) < RAMP.w / 2 + 1.2) y = lerp(rampY(z0) - 0.06, y, smooth(RAMP.w / 2, RAMP.w / 2 + 1.2, Math.abs(x)));
    p.setY(i, y); }
  shoreGeo.computeVertexNormals(); }
const shore = new THREE.Mesh(shoreGeo, shoreMat); shore.receiveShadow = true; scene.add(shore);
const lakeBed = new THREE.Mesh(new THREE.PlaneGeometry(200, 200).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0x2f3b2a, roughness: 1 }));
lakeBed.position.set(0, -7.5, -90); scene.add(lakeBed);
const concrete = new THREE.MeshStandardMaterial({ color: 0x9c9890, roughness: 0.9 });
{ const L = Math.hypot(RAMP.z0 - RAMP.z1, RAMP.y0 - RAMP.y1); const ramp = new THREE.Mesh(new THREE.BoxGeometry(RAMP.w, 0.2, L), concrete);
  ramp.position.set(0, (RAMP.y0 + RAMP.y1) / 2 - 0.1, (RAMP.z0 + RAMP.z1) / 2); ramp.rotation.x = -Math.atan2(RAMP.y0 - RAMP.y1, RAMP.z0 - RAMP.z1);   // high end (+z) up ramp.receiveShadow = true; scene.add(ramp);
  for (let i = 0; i < 26; i++) { const g = new THREE.Mesh(new THREE.BoxGeometry(RAMP.w * 0.96, 0.02, 0.05), new THREE.MeshStandardMaterial({ color: 0x7c7870, roughness: 1 }));
    const z = RAMP.z0 - 0.6 - i * 0.7; g.position.set(0, rampY(z) + 0.005, z); g.rotation.x = ramp.rotation.x; scene.add(g); } }
// a sign at the top of the ramp (the one Easter egg: a small subscribe sticker on its post)
{ const tex = canvasTex(512, 300, g => { g.fillStyle = '#1d5fa8'; g.fillRect(0, 0, 512, 300); g.strokeStyle = '#fff'; g.lineWidth = 12; g.strokeRect(12, 12, 488, 276);
    g.fillStyle = '#fff'; g.font = 'bold 74px Inter, Arial'; g.textAlign = 'center'; g.fillText('BOAT RAMP', 256, 130); g.font = 'bold 50px Inter, Arial'; g.fillText('NO SWIMMING', 256, 220); });
  const st = canvasTex(256, 96, g => { g.fillStyle = '#e02020'; g.beginPath(); g.roundRect(4, 4, 248, 88, 40); g.fill(); g.fillStyle = '#fff'; g.font = 'bold 44px Inter, Arial'; g.textAlign = 'center'; g.fillText('SUBSCRIBE', 128, 64); });
  const s = new THREE.Group(), post = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 2.0, 8), new THREE.MeshStandardMaterial({ color: 0x777777, metalness: 0.6, roughness: 0.4 }));
  post.position.y = 1.0; s.add(post);
  const board = new THREE.Mesh(new THREE.PlaneGeometry(1.0, 0.6), new THREE.MeshStandardMaterial({ map: tex, roughness: 0.6, side: THREE.DoubleSide })); board.position.set(0, 1.75, -0.03); board.rotation.y = Math.PI; s.add(board);
  const sk = new THREE.Mesh(new THREE.PlaneGeometry(0.16, 0.06), new THREE.MeshStandardMaterial({ map: st, roughness: 0.5 })); sk.position.set(0, 0.9, -0.045); sk.rotation.y = Math.PI; s.add(sk);
  s.position.set(-3.3, rampY(6.5) + 0.5, 6.5); s.rotation.y = -0.3; s.traverse(o => { if (o.isMesh) o.castShadow = true; }); scene.add(s); }
{ // tree line across the lake and along the shore
  const trunk = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.18, 0.25, 3, 6), new THREE.MeshStandardMaterial({ color: 0x4a3a2a, roughness: 1 }), 160);
  const crown = new THREE.InstancedMesh(new THREE.ConeGeometry(1.6, 5, 8), new THREE.MeshStandardMaterial({ color: 0x2f4a26, roughness: 1 }), 160);
  const m4 = new THREE.Matrix4(); let k = 0;
  for (let i = 0; i < 400 && k < 160; i++) { let x, z; if (i % 2) { x = (hash1(i) - 0.5) * 260; z = -70 - hash1(i * 3) * 30; } else { x = (hash1(i) < 0.5 ? -1 : 1) * (4 + hash1(i * 5) * 50); z = 6 + SHOREZ(x) + hash1(i * 7) * 30; }
    const s = 0.8 + hash1(i * 9) * 0.9, y = z > 0 ? 1.2 : 0.3;
    m4.compose(V(x, y + 1.5 * s, z), new THREE.Quaternion(), V(s, s, s)); trunk.setMatrixAt(k, m4);
    m4.compose(V(x, y + 4.5 * s, z), new THREE.Quaternion(), V(s, s, s)); crown.setMatrixAt(k, m4); k++; }
  trunk.count = crown.count = k; scene.add(trunk); scene.add(crown); }

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
const WATER_Y = { value: 0 };
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
// shattering glass: fragments that take the window's place (beat 7)
const NFR = 340;
const frag = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 1, 1), new THREE.MeshPhysicalMaterial({ color: 0xcfe6ee, roughness: 0.05, transparent: true, opacity: 0.7 }), NFR);
frag.frustumCulled = false; frag.visible = false; car.add(frag);
const FR = []; for (let i = 0; i < NFR; i++) FR.push({ z: (hash1(i * 1.3) - 0.5) * 1.14, y: (hash1(i * 2.7) - 0.5) * 0.4, s: 0.012 + hash1(i * 4.1) * 0.02, v: hash1(i * 5.3) });
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
// the escape tool (spring-loaded punch) that rides in his hand in beat 7
const tool = new THREE.Group();
{ const body = new THREE.Mesh(new THREE.CylinderGeometry(0.014, 0.016, 0.09, 14), new THREE.MeshStandardMaterial({ color: 0xf2b21b, roughness: 0.45 })); tool.add(body);
  const tip = new THREE.Mesh(new THREE.ConeGeometry(0.006, 0.02, 10), chrome); tip.position.y = 0.055; tool.add(tip); }
tool.traverse(o => { if (o.isMesh) o.castShadow = true; }); tool.visible = false; scene.add(tool);

// the passenger side comes away for the inside shots (a cutaway like the elevator's open front): everything on the +x side
const PASS = car.children.filter(o => o.position.x > 0.3 && o.position.z > -1.3 && o.position.z < 1.6);
// ------------------------------------------------------------------ water: the lake (cut out of the cabin), the cutaway face, water inside the car
const lakeU = { uT: { value: 0 }, uCut: { value: -99 }, uCutHi: { value: 99 }, uInv: carU.uInv, uRipC: { value: new THREE.Vector2() }, uRip: { value: 0 } };
const lakeMat = new THREE.MeshStandardMaterial({ color: 0x245a5c, roughness: 0.08, metalness: 0.0, transparent: true, side: THREE.DoubleSide });
lakeMat.onBeforeCompile = sh => {
  Object.assign(sh.uniforms, lakeU);
  sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vWl;').replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvWl = (modelMatrix * vec4(transformed, 1.0)).xyz;');
  sh.fragmentShader = sh.fragmentShader.replace('#include <common>', `#include <common>
varying vec3 vWl; uniform float uT, uCut, uCutHi, uRip; uniform mat4 uInv; uniform vec2 uRipC;`)
    .replace('#include <color_fragment>', `#include <color_fragment>
  { vec3 cp = (uInv * vec4(vWl, 1.0)).xyz;                         // car space
    if (abs(cp.x) < 0.9 && cp.y > 0.28 && cp.y < 1.44 && cp.z > -1.0 && cp.z < 1.3) discard;   // no lake inside the cabin
    if (abs(cp.x) < 0.91 && cp.y > 0.0 && cp.y < 1.0 && abs(cp.z) < 2.3) discard;              // nor inside the body
    if (vWl.x < uCut || vWl.x > uCutHi) discard;                  // cutaways: the lake sliced along x
    float rr = length(vWl.xz - uRipC);
    float foam = (1.0 - smoothstep(0.0, 0.35, rr - 1.4)) * uRip * (0.5 + 0.5 * sin(rr * 30.0 - uT * 8.0));
    float edge = 1.0 - smoothstep(0.0, 0.08, abs(vWl.x - uCut));
    diffuseColor.rgb = gl_FrontFacing ? mix(vec3(0.12, 0.33, 0.34), vec3(0.9, 0.95, 0.95), clamp(foam, 0.0, 1.0)) : vec3(0.55, 0.8, 0.78);
    diffuseColor.a = gl_FrontFacing ? 0.9 : 0.75; }`)
    .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
  { vec3 gr = vec3(0.10 * cos(vWl.x * 1.9 + uT * 1.4) + 0.05 * cos(vWl.x * 4.3 - vWl.z * 2.1 + uT * 2.2), 1.0,
                   0.10 * cos(vWl.z * 1.5 - uT * 1.7) + 0.04 * sin(vWl.z * 5.1 + uT));
    float rr = length(vWl.xz - uRipC); vec2 rd = (vWl.xz - uRipC) / max(rr, 1e-3);
    gr += vec3(rd.x, 0.0, rd.y) * sin(rr * 9.0 - uT * 6.0) * exp(-rr * 0.6) * uRip * 0.5;
    normal = normalize((viewMatrix * vec4(normalize(gr) * (gl_FrontFacing ? 1.0 : -1.0), 0.0)).xyz); }`);
};
const lake = new THREE.Mesh(new THREE.PlaneGeometry(260, 220, 1, 1).rotateX(-Math.PI / 2), lakeMat); lake.position.set(0, 0, -110 + 36); lake.receiveShadow = true; scene.add(lake);
// the cutaway face of the lake (an aquarium wall along x = uCut, below the surface)
const cutFaceMat = new THREE.ShaderMaterial({ transparent: true, depthWrite: false, side: THREE.DoubleSide, uniforms: { uT: lakeU.uT },
  vertexShader: 'varying vec3 vW; void main(){ vW = (modelMatrix * vec4(position, 1.0)).xyz; gl_Position = projectionMatrix * viewMatrix * vec4(vW, 1.0); }',
  fragmentShader: `varying vec3 vW; uniform float uT;
  float hh(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
  void main(){ float d = -vW.y;
    vec3 c = mix(vec3(0.16, 0.42, 0.42), vec3(0.03, 0.12, 0.13), smoothstep(0.0, 5.0, d));
    float caus = pow(0.5 + 0.5 * sin(vW.z * 7.0 + sin(vW.y * 5.0 + uT * 1.3) * 1.5 + uT) * sin(vW.y * 6.0 - uT * 0.9), 6.0) * (1.0 - smoothstep(0.0, 2.5, d));
    c += vec3(0.2, 0.35, 0.3) * caus * 0.5;
    float specks = step(0.996, hh(floor(vW.zy * 90.0 + vec2(0.0, uT * 3.0)))) * 0.25;
    c += specks;
    float a = mix(0.42, 0.8, smoothstep(0.0, 4.0, d));
    a = mix(a, 1.0, 1.0 - smoothstep(0.0, 0.015, d));                   // bright surface line
    if (d < 0.0) discard;
    gl_FragColor = vec4(mix(c, vec3(0.8, 0.95, 0.95), 1.0 - smoothstep(0.0, 0.015, d)), a);
    #include <tonemapping_fragment>
    #include <colorspace_fragment>
  }` });
const cutFace = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), cutFaceMat); cutFace.rotation.y = -Math.PI / 2; cutFace.renderOrder = 10; cutFace.visible = false; scene.add(cutFace);
// water inside the car: a box clipped to the cabin, its top at the inside water level (car space)
const inWaterMat = new THREE.MeshStandardMaterial({ color: 0x1d5652, roughness: 0.08, transparent: true, opacity: 0.62, depthWrite: false, side: THREE.DoubleSide });
const inWater = new THREE.Mesh(new THREE.BoxGeometry(2 * CW, 1, CABZ1 - CABZ0), inWaterMat); inWater.renderOrder = 8; car.add(inWater); inWater.visible = false;
// water pouring over the sill (beat 6) and jetting in (beat 7): a curved sheet with running streaks
const pourU = { uT: { value: 0 }, uA: { value: 0 } };
const pourMat = new THREE.ShaderMaterial({ transparent: true, depthWrite: false, side: THREE.DoubleSide, uniforms: pourU,
  vertexShader: 'varying vec2 vU; void main(){ vU = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
  fragmentShader: `varying vec2 vU; uniform float uT, uA;
  void main(){ float s = 0.55 + 0.45 * sin(vU.x * 60.0 + sin(vU.x * 13.0) * 2.0) * sin(vU.y * 9.0 - uT * 14.0 + vU.x * 7.0);
    float edge = smoothstep(0.0, 0.08, vU.x) * smoothstep(1.0, 0.92, vU.x);
    vec3 c = mix(vec3(0.25, 0.55, 0.55), vec3(0.85, 0.97, 0.97), s * 0.8);
    gl_FragColor = vec4(c, uA * edge * (0.18 + 0.32 * s));
    #include <tonemapping_fragment>
    #include <colorspace_fragment>
  }` });
function pourGeo(z0, z1, yTop, drop, reach) { const g = new THREE.PlaneGeometry(1, 1, 16, 16), p = g.attributes.position;
  for (let i = 0; i < p.count; i++) { const u = p.getX(i) + 0.5, v = 0.5 - p.getY(i); const z = lerp(z0, z1, u);
    p.setXYZ(i, -0.86 + reach * Math.sin(v * Math.PI * 0.5), yTop - drop * v * v, z); }
  g.computeVertexNormals(); return g; }
const pour = new THREE.Mesh(pourGeo(-0.6, 0.4, 0.99, 0.6, 0.45), pourMat); pour.renderOrder = 9; pour.visible = false; car.add(pour);
// splash: spray drops + a white crown (beats 9 -> 0)
const NSPR = 1400;
const sprGeo = new THREE.BufferGeometry(); const sprPos = new Float32Array(NSPR * 3); sprGeo.setAttribute('position', new THREE.BufferAttribute(sprPos, 3));
const dotTex = canvasTex(64, 64, g => { const gr = g.createRadialGradient(32, 32, 0, 32, 32, 30); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.5, 'rgba(255,255,255,0.6)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); });
const spray = new THREE.Points(sprGeo, new THREE.PointsMaterial({ map: dotTex, color: 0xeaf6f6, size: 0.11, transparent: true, depthWrite: false, opacity: 0.9 }));
spray.frustumCulled = false; scene.add(spray);
const foamMat = new THREE.MeshStandardMaterial({ color: 0xf2fbfb, roughness: 0.6, transparent: true, opacity: 0.9, depthWrite: false });
const foam = new THREE.Mesh(new THREE.TorusGeometry(1, 0.22, 10, 40).rotateX(Math.PI / 2).scale(1, 0.35, 1), foamMat); foam.visible = false; scene.add(foam);
// bubbles (underwater)
const NBUB = 260;
const bubGeo = new THREE.BufferGeometry(); const bubPos = new Float32Array(NBUB * 3); bubGeo.setAttribute('position', new THREE.BufferAttribute(bubPos, 3));
const bubTex = canvasTex(64, 64, g => { g.strokeStyle = 'rgba(255,255,255,0.95)'; g.lineWidth = 5; g.beginPath(); g.arc(32, 32, 24, 0, 7); g.stroke(); g.fillStyle = 'rgba(255,255,255,0.25)'; g.beginPath(); g.arc(26, 26, 8, 0, 7); g.fill(); });
const bubbles = new THREE.Points(bubGeo, new THREE.PointsMaterial({ map: bubTex, color: 0xdff6f2, size: 0.03, transparent: true, depthWrite: false, opacity: 0.85 }));
bubbles.frustumCulled = false; scene.add(bubbles);
// arrows: water pressing on the door (beat 3)
const arrowMat = new THREE.MeshStandardMaterial({ color: 0xffd23a, emissive: 0x6a4a00, roughness: 0.4 });
const arrows = [];
for (let i = 0; i < 6; i++) { const g = new THREE.Group();
  const shf = new THREE.Mesh(new THREE.CylinderGeometry(0.028, 0.028, 0.36, 14), arrowMat); shf.position.y = 0.18; g.add(shf);
  const hd = new THREE.Mesh(new THREE.ConeGeometry(0.07, 0.14, 18), arrowMat); hd.position.y = 0.43; g.add(hd);
  g.rotation.z = -Math.PI / 2; g.visible = false; scene.add(g); arrows.push(g); }

// ------------------------------------------------------------------ the guy (rides inside the car)
const G = await loadGuy(THREE, '/char/guy', {});
car.add(G.root); G.root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
const HIP = V(0.0, 0.95, 0.0);
const SEAT = V(-0.38, 0.6, 0.3);                               // his hips when seated (car space)
function untwistSafe() { for (const S of ['R', 'L']) { const ua = G.bones['uarm' + S], ut = G.bones['uarmTwist' + S]; ua.quaternion.multiply(ut.quaternion); ut.quaternion.identity(); } G.untwist(); }
// seatbelt: a strap from the B pillar over his left shoulder to the buckle by his right hip (redrawn every frame)
const beltMat = new THREE.MeshStandardMaterial({ color: 0x4a5066, roughness: 0.7 });
const belt = new THREE.Mesh(new THREE.BufferGeometry(), beltMat); belt.castShadow = true; car.add(belt);
const ANCHOR = V(-0.82, 1.28, 0.6);

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
const SIT = { thighR: [88, 0, 4], thighL: [88, 0, -4], shinR: [-78, 0, 0], shinL: [-78, 0, 0], footR: [-6, 0, 0], footL: [-6, 0, 0], spine1: [4, 0, 0], spine2: [2, 0, 0], neck: [-4, 0, 0] };
const P = {
  drive: { ...SIT, armR: A(48, 18, 0, 70), armL: A(48, 18, 0, 70) },
  brace: { ...SIT, armR: A(60, 22, 0, 40), armL: A(60, 22, 0, 40), spine1: [8, 0, 0], neck: [10, 0, 0] },
  sitLook: { ...SIT, armR: A(20, 12, 0, 50), armL: A(24, 14, 0, 60), neck: [-8, -30, 0], head: [-4, -22, 0] },
  sitHands: { ...SIT, armR: A(16, 10, 0, 45), armL: A(16, 10, 0, 45) },
  swim: { thighR: [20, 0, 6], thighL: [6, 0, -6], shinR: [-30, 0, 0], shinL: [-14, 0, 0], footR: [-30, 0, 0], footL: [-30, 0, 0], spine1: [6, 0, 0], neck: [24, 0, 0], head: [10, 0, 0],
    armR: A(112, 28, 0, 24, -10), armL: A(112, 28, 0, 24, -10) },
};
for (const k of Object.keys(P)) { curl(P[k], 'R', 28); curl(P[k], 'L', 28); }
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
  const hipP = V(root.x ?? SEAT.x, root.y ?? SEAT.y, root.z ?? SEAT.z);
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
let _carInv = new THREE.Matrix4(); const carInv = () => _carInv;
function handFK(S, a) {                                         // car-space palm point, palm normal, little-finger direction
  setArm(S, a); const hb = G.bones['hand' + S];
  G.bones['uarm' + S].updateMatrixWorld(true);
  const M = _m.copy(_carInv).multiply(hb.matrixWorld); const qh = _q.setFromRotationMatrix(M);   // bones rest unrotated: bone-local axes = rest axes
  return { p: PALM(S).applyMatrix4(M), n: HANDREST[S].n.clone().applyQuaternion(qh), w: HANDREST[S].w.clone().applyQuaternion(qh),
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

// ------------------------------------------------------------------ the car's path (position y, z and nose-down pitch), water levels
const FRAME0 = { z: 2.15, y: 0.02, p: -7 };                     // frame one: front wheels just off the ramp, nose into the water
function carPose(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  if (b === 9) { const u = lt / d; const z = lerp(11.5, FRAME0.z, 1 - (1 - u) ** 1.25);                   // rolling down the ramp, speeding up a little
    return { z, y: rampY(z) - rampY(FRAME0.z) + FRAME0.y + 0.0, p: lerp(-4.5, FRAME0.p, smooth(0.7, 1, u)), bob: 0 }; }
  if (b === 0) { const u = lt / d;                               // the plunge: nose dips hard, bounces, settles nose-down, floating
    const p = FRAME0.p - 20 * Math.sin(Math.PI * clamp(u / 0.5, 0, 1)) * (u < 0.5 ? 1 : 0) - lerp(0, 11, smooth(0.3, 0.9, u)) + 2 * Math.sin(lt * 5) * smooth(0.4, 0.6, u) * (1 - u);
    return { z: lerp(FRAME0.z, -1.2, 1 - (1 - smooth(0, 0.7, u)) ** 2), y: lerp(FRAME0.y, -0.55, smooth(0.0, 0.55, u)) - 0.08 * Math.sin(Math.PI * clamp((u - 0.3) / 0.4, 0, 1)), p }; }
  if (b === 1) return { z: -1.25 - 0.05 * lt, y: -0.58 - 0.05 * lt / d + 0.02 * Math.sin(t * 1.6), p: -18 + 1.0 * Math.sin(t * 1.3) };
  if (b === 2) return { z: -1.3, y: -0.72, p: -14 };
  if (b === 3) return { z: -1.3, y: -0.98 - 0.04 * lt / d, p: -12 };
  if (b === 4) return { z: -1.3, y: -3.4, p: -9 };
  if (b === 5) return { z: -1.3, y: -0.62, p: -16 };
  if (b === 6) return { z: -1.3, y: lerp(-0.66, -0.95, lt / d), p: -15 };
  if (b === 7) return { z: -1.3, y: -0.95, p: -13 };
  return { z: -1.3, y: lerp(-1.9, -4.2, (t - B[8]) / DUR[8]), p: -10 };
}
const INWATER = t => { const b = beatAt(t), lt = t - B[b], d = DUR[b];         // water level inside the cabin (car space y), null = dry
  if (b === 4) return 9;
  if (b === 6) return lt > 0.9 ? lerp(0.34, 0.66, smooth(0.9, d, lt)) : null;
  if (b === 7) return lt > d * 0.55 ? lerp(0.34, 0.5, smooth(d * 0.55, d, lt)) : null;
  if (b === 8) return 9;
  return null; };

// ------------------------------------------------------------------ the story, beat by beat
function blink(t) { for (const b0 of [1.6, 5.2, 9.9, 16.4, 19.6, 23.1, 27.0, 33.4]) { const u = (t - b0) / 0.16; if (u > 0 && u < 1) return Math.sin(Math.PI * u); } return 0; }
const WHEEL_PT = (ang) => { const q = new THREE.Quaternion().setFromEuler(new THREE.Euler(-WHEEL.tilt, 0, 0)); return V(Math.sin(ang) * WHEEL.r, Math.cos(ang) * WHEEL.r, 0).applyQuaternion(q).add(WHEEL.c); };
const WHEEL_N = V(0, 0, -1).applyQuaternion(new THREE.Quaternion().setFromEuler(new THREE.Euler(-WHEEL.tilt, 0, 0)));   // out of the wheel face, away from him
function guyAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  let pose = P.drive, root = {}, face = { blink: blink(t) }, hands = [], show = true, beltK = 1, curlK = { R: 28, L: 28 };
  const wheelHands = () => [{ S: 'L', p: WHEEL_PT(-1.05), n: WHEEL_N.clone().multiplyScalar(-1).add(V(0.35, 0, 0)).normalize(), c: 70 },
    { S: 'R', p: WHEEL_PT(1.05), n: WHEEL_N.clone().multiplyScalar(-1).add(V(-0.35, 0, 0)).normalize(), c: 70 }];
  if (b === 9) {                                                // driving down the ramp, calm; the nose tips at the end
    pose = P.drive; hands = wheelHands();
    face = { ...face, brow: 0.1, smile: 0.1 * (1 - smooth(d - 0.8, d, lt)), fear: 0.5 * smooth(d - 0.5, d, lt), jaw: 0.15 * smooth(d - 0.4, d, lt), look: [0, -0.1] };
  } else if (b === 0) {                                         // the impact throws him forward; he braces on the wheel, scared
    const hit = smooth(0.0, 0.35, lt), back = smooth(0.35, 1.0, lt);
    pose = addPose(P.drive, { spine1: [-14 * hit * (1 - back * 0.7), 0, 0], spine2: [-8 * hit * (1 - back * 0.7), 0, 0], neck: [-10 * hit * (1 - back) + 10 * back, 0, 0] });
    hands = wheelHands();
    face = { ...face, fear: 0.5 + 0.5 * smooth(0, 0.4, lt), jaw: 0.15 + 0.35 * smooth(0.1, 0.5, lt), oh: 0.3, browIn: 0.6, look: [0, -0.2 + 0.3 * back] };
  } else if (b === 1) {                                         // (cutaway) he looks around, hands off the wheel
    pose = keyed([[0, P.drive], [0.6, P.sitLook], [d, addPose(P.sitLook, { neck: [0, 50, 0], head: [0, 30, 0] })]], lt);
    face = { ...face, fear: 0.8, jaw: 0.2, brow: 0.6, look: [-0.5, 0] };
  } else if (b === 2) {                                         // hand on the inside door handle: the "movie" plan
    pose = P.sitLook;
    hands = [{ S: 'L', p: V(-0.79, 0.92, -0.14), n: V(-1, 0, 0), c: 55 * smooth(0.5, 1.2, lt) }];
    face = { ...face, browIn: 0.6, frown: 0.4, fear: 0.4, look: [-0.4, -0.1] };
    pose = addPose(pose, { neck: [0, -26, 0], head: [0, -16, 0] });
  } else if (b === 3) {                                         // (cutaway) he shoves the door with his shoulder and both hands
    const push = 0.5 + 0.5 * Math.sin(lt * 7);
    pose = addPose(P.sitHands, { spine1: [0, 0, -8 - 4 * push], spine2: [0, 0, -6 - 3 * push], neck: [0, -20, 0] });
    hands = [{ S: 'L', p: V(-0.8, 0.9 + 0.01 * push, 0.02), n: V(-1, 0, 0), c: 20 }, wheelHands()[1]];
    face = { ...face, browIn: 1, pain: 0.6 + 0.3 * push, press: 0.6, look: [-0.5, 0] };
  } else if (b === 4) {                                         // flooded, dark: cheeks puffed, holding his breath, pushing the door open
    const open = smooth(1.2, d - 0.3, lt);
    pose = addPose(P.sitHands, { spine1: [0, 0, -10], neck: [0, -24, 0], thighR: [-6, 0, 0], thighL: [-6, 0, 0] });
    hands = [{ S: 'L', p: V(-0.8 - 0.1 * open, 0.9, 0.0 - 0.08 * open), n: V(-1, 0, 0.3).normalize(), c: 20 }, wheelHands()[1]];
    root = { y: SEAT.y + 0.05 + 0.02 * Math.sin(t * 2), x: SEAT.x - 0.07 * open };
    face = { ...face, puff: 1, press: 0.6, browIn: 0.8, blink: 0.25 + 0.2 * Math.sin(t * 3) * 0, look: [-0.4, 0] };
  } else if (b === 5) {                                         // seatbelt off: right thumb on the red button
    const k = lt / d;
    pose = P.sitHands;
    const off = smooth(0.62, 0.9, k);                           // presses the button, then the hand goes back to his thigh
    hands = [{ S: 'R', p: BUCKLE.clone().add(V(0, 0.07, 0)).lerp(V(-0.24, 0.72, 0.06), off), n: V(0, -1, 0), w: V(1, 0, 0), c: 30 }];
    beltK = 1 - smooth(0.5, 0.75, k);
    face = { ...face, browIn: 0.5, press: 0.4, look: [0.2, -0.5] };
  } else if (b === 6) {                                         // left index finger on the window switch
    pose = addPose(P.sitHands, { neck: [0, -22, 0] }); beltK = 0;
    hands = [{ S: 'L', p: V(-0.78, 0.86, -0.07), n: V(0, -1, 0), c: 25 }];
    face = { ...face, browIn: 0.6, fear: 0.3 + 0.4 * smooth(1, 2, lt), jaw: 0.1, look: [-0.5, -0.1] };
  } else if (b === 7) {                                         // the escape tool, pressed into the lower front corner of the glass
    const press = smooth(0.4, 1.3, lt);
    pose = addPose(P.sitHands, { spine1: [0, 0, -6], neck: [0, -24, 0] }); beltK = 0;
    hands = [{ S: 'L', p: V(-0.7 - 0.05 * press, 1.04, 0.36), w: V(1, 0, 0), c: 75, tool: true }];
    face = { ...face, browIn: 0.9, press: 0.5, pain: 0.3 * press, look: [-0.5, -0.1] };
  } else {                                                      // out of the window and up (car space, so he leaves the sinking car)
    const k = lt / d; beltK = 0;
    const ph = 2 * Math.PI * 1.1 * lt, stroke = Math.sin(ph);
    pose = addPose(P.swim, { armR: [-40 * (0.5 + 0.5 * stroke), 30 * (0.5 - 0.5 * stroke), 0, 30 * (0.5 + 0.5 * stroke), 0], armL: [-40 * (0.5 + 0.5 * stroke), 30 * (0.5 - 0.5 * stroke), 0, 30 * (0.5 + 0.5 * stroke), 0],
      thighR: [16 * Math.sin(ph * 1.3), 0, 0], thighL: [16 * Math.sin(ph * 1.3 + Math.PI), 0, 0] });
    root = { x: lerp(-1.1, -2.2, k), y: lerp(1.2, 1.2 + 2.9 * k, sm(k)), z: lerp(0.0, -0.3, k), tilt: -55, roll: 75, yaw: 0 };
    face = { ...face, puff: 1, press: 0.5, browIn: 0.6, look: [0, 0.6] };
  }
  const feet = b === 8 ? null : { R: V(SEAT.x + 0.12, 0.42, -0.5), L: V(SEAT.x - 0.1, 0.42, -0.42) };
  return { pose, root, face, hands, show, beltK, feet };
}

// ------------------------------------------------------------------ cameras (world space; per beat), punch on cuts
function shake(t, a, f = 1) { return V(vn1(t * 3 * f, 1) * a, vn1(t * 3 * f, 2) * a, vn1(t * 3 * f, 3) * a * 0.5); }
const HOOK = { pos: V(-2.7, 0.75, -2.1), tgt: V(0.0, 0.45, 1.0), fov: 46 };
function carPt(cp, v) { return v.clone().applyMatrix4(cp); }
function camAt(t, CM) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b], u = lt / d;
  let pos, tgt, fov = 42, cut = -99, inside = false;
  if (b === 0) { pos = HOOK.pos.clone().add(V(0.15 * u, 0.1 * u, 0.4 * u)); tgt = HOOK.tgt.clone().lerp(V(0, 0.2, -0.6), smooth(0.2, 1, u)); fov = HOOK.fov; pos.add(shake(t, 0.03 * (1 - smooth(0.4, 1.2, lt)) * smooth(0, 0.06, lt), 3)); }
  else if (b === 9) { const w = smooth(0.55, 1, u); pos = V(-2.6 - 1.5 * (1 - w), 1.5 - 0.95 * w, 4.5 - 7.8 * w).lerp(HOOK.pos, w); tgt = V(0, 0.7, carPose(t).z - 0.6).lerp(HOOK.tgt, w); fov = lerp(46, HOOK.fov, w); }
  else if (b === 1 || b === 3) {                                // cutaway along the car's driver side (aquarium wall at x = cut)
    cut = -1.45; const k = b === 1 ? 0 : 1;
    pos = V(-5.6 + 0.4 * u + 1.5 * k, 0.15 - 0.3 * k, -1.2 - 0.2 * u - 2.4 * k); tgt = V(0 - 0.6 * k, -0.35 - 0.05 * k, -1.0 + 0.1 * k); fov = b === 1 ? 46 : 40;
  }
  else if (b === 8) { cut = -99; const hp = G.bones.hips.getWorldPosition(new THREE.Vector3()); pos = V(hp.x - 2.4, hp.y - 0.2, hp.z + 1.3); tgt = hp.clone().add(V(0, 0.15, 0)); fov = 46; }
  else {                                                        // inside: from the passenger seat, looking at him and his door
    let cp, ct, f = 52;
    if (b === 2) { cp = V(1.7, 1.4, 0.7); ct = V(-0.5, 1.02, -0.12); f = 42; }
    else if (b === 4) { cp = V(1.65, 1.2, 0.45); ct = V(-0.55, 0.95, -0.2); f = 42; }
    else if (b === 5) { cp = V(1.3, 1.05, -0.35); ct = V(-0.2, 0.78, 0.3); f = 40; }
    else if (b === 6) { cp = V(1.65, 1.25, 0.5); ct = V(-0.6, 0.95, -0.2); f = 42; }
    else { cp = V(-2.15, 1.25, 0.75); ct = V(-0.55, 1.05, 0.25); f = 40; inside = false; }
    cp.add(V(b === 7 ? 0.12 * u : -0.12 * u, -0.03 * u, 0.06 * u)); inside = b !== 7;
    pos = carPt(CM, cp); tgt = carPt(CM, ct); fov = f; pos.add(shake(t, 0.004, 2));
  }
  const punch = b > 0 ? (1 - smooth(0, 0.22, lt)) * 0.07 : 0;
  return { pos, tgt, fov: fov * (1 - punch), cut, inside };
}

// ------------------------------------------------------------------ per-frame update
let FRAMEI = 0;
function update(t, frame = Math.round(t * FPS)) {
  t = ((t % TOTAL) + TOTAL) % TOTAL;
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  // the car
  const cp = carPose(t);
  car.position.set(0, cp.y, cp.z); car.rotation.set(cp.p * D2R, 0, 0); car.updateMatrixWorld(true);
  _carInv.copy(car.matrixWorld).invert(); carU.uInv.value.copy(_carInv);
  // the door: closed, except beat 4 where he pushes it open against the (now equal) water
  door.rotation.y = b === 4 ? -0.55 * smooth(1.2, d - 0.3, lt) : 0;
  door.updateMatrixWorld(true);
  // the glass: rolls down in beat 6; shatters in beat 7; gone in beat 8 (he swims out the opening)
  const SHATTER = d * 0.5;
  dGlass.position.y = b === 6 ? DGLASS_Y0 - 0.44 * smooth(0.6, 2.2, lt) : DGLASS_Y0;
  dGlass.visible = !(b === 8 || (b === 7 && lt > SHATTER));
  // the guy
  const g = guyAt(t);
  if (window.OVR && window.OVR.p) g.pose = { ...g.pose, ...window.OVR.p };
  applyPose(g.pose, g.root);
  for (const h of g.hands) {                                    // put the hands on what they hold (warm-started from the last frame)
    const sol = solveHand(h, 'h' + h.S + b, frame); const a = sol.a; setArm(h.S, a); LAST['arm' + h.S] = a;
    const c = h.c ?? 30; const pp = {}; curl(pp, h.S, c, h.tool ? 60 : c); for (const [n, e] of Object.entries(pp)) { G.bones[n].quaternion.copy(G.REST[n].q).multiply(qTmp.setFromEuler(eTmp.set(e[0] * D2R, e[1] * D2R, e[2] * D2R))); }
    LAST['cost' + h.S] = sol.c;
  }
  if (g.feet) { const flat = new THREE.Quaternion().setFromRotationMatrix(car.matrixWorld);
    for (const S of ['R', 'L']) { const f = g.feet[S].clone().applyMatrix4(car.matrixWorld), pole = g.feet[S].clone().add(V(0, 0.6, -0.4)).applyMatrix4(car.matrixWorld);
      G.legIK(S, f, pole, flat.clone().multiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(-0.35, 0, 0)))); } }
  G.root.updateMatrixWorld(true);
  untwistSafe(); G.face(g.face); G.root.visible = g.show; G.root.updateMatrixWorld(true);
  // the tool rides in his left hand: body across the fist, tip out past the thumb side
  tool.visible = b === 7;
  if (tool.visible) { const hb = G.bones.handL; hb.updateMatrixWorld(true); const q = hb.getWorldQuaternion(new THREE.Quaternion()), hp = hb.getWorldPosition(new THREE.Vector3());
    const wv = HANDREST.L.w.clone().applyQuaternion(q), up = HANDREST.L.u.clone().applyQuaternion(q), nn = HANDREST.L.n.clone().applyQuaternion(q);
    tool.position.copy(hp).addScaledVector(up, 0.07).addScaledVector(nn, 0.03).addScaledVector(wv, -0.01);
    tool.quaternion.setFromUnitVectors(V(0, 1, 0), wv.clone().multiplyScalar(-1)); }
  // the seatbelt: anchor -> over the left shoulder -> across the chest -> right hip -> buckle; it retracts when released
  { const w = n => G.bones[n].getWorldPosition(new THREE.Vector3()).applyMatrix4(_carInv);
    const sh = w('clavL').lerp(w('uarmL'), 0.5).add(V(0.0, 0.07, -0.07)), ch = w('chest').add(V(0.03, -0.08, -0.17)), hp = w('hips').add(V(0.13, 0.0, -0.15));
    let pts;
    if (g.beltK > 0.02) { const k = g.beltK; pts = [ANCHOR, sh, ch, hp, BUCKLE.clone().add(V(0, 0.04, -0.03))].map((p, i) => i === 0 ? p : ANCHOR.clone().lerp(p, i === 4 ? k : Math.min(1, k * 1.15))); }
    else pts = [ANCHOR, ANCHOR.clone().add(V(0.02, -0.4, 0.01)), ANCHOR.clone().add(V(0.03, -0.75, 0.02))];
    belt.geometry.dispose(); belt.geometry = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 24, 0.017, 6, false); belt.scale.set(1, 1, 1); }
  // water
  const under = b === 4 || b === 8;
  WATER_Y.value = under ? -99 : 0;
  lakeU.uT.value = t; lakeU.uCut.value = -99; lakeU.uRip.value = b === 0 ? 1 - smooth(0.4, d, lt) : b === 9 ? 0 : 0.15;
  lakeU.uRipC.value.set(0, cp.z - 1.4);
  const iw = INWATER(t);
  inWater.visible = iw !== null && !under;
  if (inWater.visible) { const h = iw - 0.32 + 0.01 * Math.sin(t * 5); inWater.scale.set(1, h, 1); inWater.position.set(0, 0.32 + h / 2, (CABZ0 + CABZ1) / 2); }
  pour.visible = (b === 6 && lt > 0.7) || (b === 7 && lt > SHATTER);
  pourU.uT.value = t; pourU.uA.value = b === 6 ? smooth(0.7, 1.2, lt) : smooth(SHATTER, SHATTER + 0.15, lt);
  if (pour.visible) { const z0 = b === 6 ? -0.55 : 0.05, z1 = b === 6 ? 0.35 : 0.48; pour.geometry.dispose(); pour.geometry = pourGeo(z0, z1, b === 6 ? 0.99 : 1.05, 0.62, b === 6 ? 0.3 : 0.5); }
  // the shatter: fragments burst inward and fall
  frag.visible = b === 7 && lt > SHATTER;
  if (frag.visible) { const a = lt - SHATTER, m4 = new THREE.Matrix4();
    for (let i = 0; i < NFR; i++) { const f = FR[i]; const vx = 0.08 + 0.3 * f.v, vy = (f.y + 0.1) * 0.8;   // tempered glass drops in small cubes near the door
      const p = V(-0.86 + vx * a, DGLASS_Y0 + f.y + vy * a - 4.9 * a * a, -0.72 + 0.64 + f.z + (f.z - 0.4) * 0.5 * a);
      m4.compose(p, new THREE.Quaternion().setFromEuler(new THREE.Euler(a * 9 * f.v, a * 7, f.s * 90)), V(f.s, f.s * 0.8, f.s * 0.3)); frag.setMatrixAt(i, m4); }
    frag.instanceMatrix.needsUpdate = true; }
  // splash (beats 9 end -> 0): spray thrown up and out from the nose
  let ns = 0;
  const sAge = b === 0 ? lt + 0.12 : b === 9 && lt > d - 0.12 ? lt - (d - 0.12) : -1;
  if (sAge >= 0 && sAge < 2.4) { const nose = V(0, 0.55, -2.25).applyMatrix4(car.matrixWorld);
    for (let i = 0; i < NSPR; i++) { const born = hash1(i * 1.7) * 0.5, a = sAge - born; if (a < 0 || a > 1.6) continue;
      const ang = (hash1(i * 3.1) - 0.5) * Math.PI * 1.4, sp = 1.5 + hash1(i * 4.7) * 3.8, up = 2.2 + hash1(i * 5.9) * 3.4;
      const p = V(nose.x + Math.sin(ang) * sp * a, nose.y + up * a - 4.9 * a * a, nose.z - Math.cos(ang) * sp * a * 0.7 + 0.4 * a);
      if (p.y < -0.05) continue; sprPos.set([p.x, p.y, p.z], ns * 3); ns++; } }
  for (let i = ns; i < NSPR; i++) sprPos.set([0, -99, 0], i * 3);
  sprGeo.attributes.position.needsUpdate = true; spray.visible = ns > 0;
  foam.visible = sAge >= 0 && sAge < 3.0;
  if (foam.visible) { const nose = V(0, 0.4, -2.1).applyMatrix4(car.matrixWorld); const r = 0.5 + 1.4 * (1 - Math.exp(-sAge * 2.5));
    foam.position.set(nose.x, 0.02, nose.z + 0.2); foam.scale.set(r, 1, r * 0.8); foamMat.opacity = 0.9 * (1 - smooth(0.8, 3.0, sAge)); }
  // bubbles: leaking from the car underwater, out of his nose/mouth when he lets a little go
  let nb = 0;
  if (under || b === 3 || b === 1) { const src = b === 8 ? G.bones.head.getWorldPosition(new THREE.Vector3()) : V(0, -0.2, -1.3).applyMatrix4(car.matrixWorld);
    for (let i = 0; i < NBUB; i++) { const ph = (hash1(i * 2.3) + t * (0.25 + 0.3 * hash1(i))) % 1; const k = i % 3;
      let p; if (b === 4) p = V((hash1(i) - 0.5) * 1.6, 0.4 + ph * 1.1, (hash1(i * 5) - 0.5) * 2.0).applyMatrix4(car.matrixWorld);
      else if (b === 8) p = k === 0 ? src.clone().add(V((hash1(i) - 0.5) * 0.2, ph * 1.5, (hash1(i * 7) - 0.5) * 0.2)) : V((hash1(i) - 0.5) * 2, 0, (hash1(i * 5) - 0.5) * 4).applyMatrix4(car.matrixWorld).add(V(0, ph * 3.5, 0));
      else p = V((hash1(i) - 0.5) * 1.8, -0.1, (hash1(i * 5) - 0.5) * 4).applyMatrix4(car.matrixWorld).add(V(0, ph * Math.max(0.05, -car.position.y), 0));
      if (!under && p.y > -0.02) continue; if (b === 8 && p.y > -0.02) continue;
      bubPos.set([p.x + 0.03 * Math.sin(t * 6 + i), p.y, p.z], nb * 3); nb++; } }
  for (let i = nb; i < NBUB; i++) bubPos.set([0, -99, 0], i * 3);
  bubGeo.attributes.position.needsUpdate = true; bubbles.visible = nb > 0;
  // pressure arrows on the door (beat 3)
  arrows.forEach((a, i) => { a.visible = b === 3; if (b === 3) { const k = smooth(0.4 + i * 0.12, 0.9 + i * 0.12, lt);
    const lp = V(-1.3 + 0.08 * Math.sin(t * 4 + i), 0.45 + (i % 2) * 0.28, -0.55 + Math.floor(i / 2) * 0.42).applyMatrix4(car.matrixWorld);
    a.position.copy(lp); a.scale.setScalar(0.001 + k * (0.9 + 0.1 * Math.sin(t * 6 + i))); } });
  // camera + the cutaway + underwater mode
  const C = camAt(t, car.matrixWorld);
  camera.position.copy(C.pos); camera.lookAt(C.tgt); camera.fov = C.fov; camera.updateProjectionMatrix();
  const camUnder = camera.position.y < 0 && C.cut < -50;
  lakeU.uCut.value = C.cut; lakeU.uCutHi.value = C.inside ? 0.93 : 99;
  for (const o of PASS) o.visible = !C.inside;
  cutFace.visible = C.cut > -50;
  if (cutFace.visible) { cutFace.position.set(C.cut, -5, -1.0); cutFace.scale.set(30, 10, 1); }
  scene.fog = camUnder ? underFog : null;
  underFog.density = b === 4 ? 0.45 : 0.28;
  scene.background = camUnder ? new THREE.Color(b === 4 ? 0x061716 : 0x0e3433) : null;
  sky.visible = !camUnder;
  sun.intensity = b === 4 ? 0.35 : camUnder ? 1.0 : 2.6; hemi.intensity = b === 4 ? 0.25 : 0.7; scene.environmentIntensity = b === 4 ? 0.12 : 0.55;
  surfLight.intensity = b === 4 ? 30 : b === 8 ? 45 : 0; surfLight.position.copy(car.position).add(V(0.8, 3.6, -0.5)); surfLight.target.position.copy(car.position).add(V(-0.4, 0.4, 0)); surfLight.target.updateMatrixWorld();
  sun.position.copy(car.position).addScaledVector(SUNDIR, 15); sun.target.position.copy(car.position); sun.target.updateMatrixWorld();
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
function stepTo(i) {                                           // the hand solver warm-starts from the previous frame: replay the beat if we jumped
  const t = i / FPS, b = beatAt(((t % TOTAL) + TOTAL) % TOTAL);
  if (i !== lastFrame + 1) { const f0 = Math.max(0, Math.round(B[b] * FPS)); for (let j = f0; j < i; j++) update(j / FPS, j); }
  update(t, i); lastFrame = i;
}
function renderInto(i) { stepTo(i); draw(); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); }
window.renderAll = async (f0, f1) => { for (let i = f0; i < f1; i++) { renderInto(i); await fetch('/frame', { method: 'POST', body: px }); } return 'ok'; };
window.renderAtT = t => { stepTo(Math.round(t * FPS)); if (window.CAM) { camera.position.set(...window.CAM.pos); camera.lookAt(...window.CAM.tgt); camera.fov = window.CAM.fov || 42; camera.updateProjectionMatrix(); } draw(); return renderer.domElement.toDataURL('image/png'); };
window.rigReport = i => { stepTo(i); const r = { t: i / FPS, beat: beatAt(i / FPS) };
  return { ...r, ang: LAST, hips: G.bones.hips.getWorldPosition(new THREE.Vector3()).applyMatrix4(_carInv).toArray(), car: 0, show: G.root.visible,
    thumbs: ['R', 'L'].map(S => G.bones['index1' + S].getWorldPosition(new THREE.Vector3()).sub(G.bones['pinky1' + S].getWorldPosition(new THREE.Vector3())).applyQuaternion(G.root.getWorldQuaternion(new THREE.Quaternion()).invert()).toArray()),
    cost: [LAST.costR, LAST.costL] }; };
window.dbgBelt = () => ({ belt: belt.geometry.attributes.position ? belt.geometry.attributes.position.count : 0, vis: belt.visible, hips: G.bones.hips.getWorldPosition(new THREE.Vector3()).applyMatrix4(_carInv).toArray().map(v => +v.toFixed(3)), chest: G.bones.chest.getWorldPosition(new THREE.Vector3()).applyMatrix4(_carInv).toArray().map(v => +v.toFixed(3)), shL: G.bones.uarmL.getWorldPosition(new THREE.Vector3()).applyMatrix4(_carInv).toArray().map(v => +v.toFixed(3)), cost: [LAST.costR, LAST.costL] });
window.carCam = (cp, ct) => ({ pos: V(...cp).applyMatrix4(car.matrixWorld).toArray(), tgt: V(...ct).applyMatrix4(car.matrixWorld).toArray(), fov: 50 });
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS);
window.READY = true;
