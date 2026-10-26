// "What happens if you mix bleach and ammonia" - a 3D Short (Zack D style, with NileRed-style close-ups of the chemistry).
//   bath.html?w=1080&h=1920            (times from bath/times.json; one shot per narration line)
// Beats: 0 he sprays glass cleaner into a bowl of bleach, a haze rises (hook) | 1 macro: the water clouds and fizzes
//        2 molecules: ammonia + hypochlorous acid -> chloramine + water | 3 x-ray: the gas goes down his throat into his lungs
//        4 coughing, hand over his mouth, eyes squeezed | 5 the myth: he sniffs, shrugs | 6 x-ray nose: the smell signal fades
//        7 x-ray lungs: fluid rising, hours later | 8 out the door, phone to his ear | 9 back at the toilet, lifts the bottle (loops)
// Safety: shows what happens and why not to; no amounts, ratios or how-to.
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
const TIMES = await (await fetch('/bath/times.json')).json();
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

// ------------------------------------------------------------------ renderer / scene / light: a small bathroom
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(W, H);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.localClippingEnabled = true;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene(); scene.background = new THREE.Color(0xdfe6ea);
const camera = new THREE.PerspectiveCamera(42, W / H, 0.01, 200);
{ const pm = new THREE.PMREMGenerator(renderer); const es = new THREE.Scene();
  es.add(new THREE.Mesh(new THREE.SphereGeometry(10, 32, 16), new THREE.MeshBasicMaterial({ color: 0xb8c2c8, side: THREE.BackSide })));
  const pan = (c, x, y, z, sx, sy) => { const m = new THREE.Mesh(new THREE.PlaneGeometry(sx, sy), new THREE.MeshBasicMaterial({ color: c, side: THREE.DoubleSide })); m.position.set(x, y, z); m.lookAt(0, 0, 0); es.add(m); };
  pan(0xffffff, 0, 9, 0, 6, 3); pan(0xfff3e0, -6, 3, 4, 4, 6);
  scene.environment = pm.fromScene(es, 0.03).texture; scene.environmentIntensity = 0.6; }
const hemi = new THREE.HemisphereLight(0xf2f6ff, 0x8a8278, 0.75); scene.add(hemi);
const lamp = new THREE.PointLight(0xfff0dc, 9, 8, 1.4); lamp.position.set(0.0, 2.35, -0.3); lamp.castShadow = true; lamp.shadow.mapSize.set(1024, 1024); lamp.shadow.bias = -0.0005; scene.add(lamp);
const fill = new THREE.DirectionalLight(0xe8f0ff, 0.9); fill.position.set(2, 3, -3); scene.add(fill);
const hallLight = new THREE.PointLight(0xfff6e8, 0, 9, 1.2); hallLight.position.set(-0.35, 2.2, 2.6); scene.add(hallLight);

// ------------------------------------------------------------------ the room: tiled walls, floor, door to a hallway, vanity with a mirror
const RX0 = -1.25, RX1 = 1.15, RZ0 = -1.25, RZ1 = 1.1, RH = 2.5;
function tileMat(base, grout, size, rough = 0.35) {
  const m = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: rough });
  m.onBeforeCompile = sh => {
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vWt; varying vec3 vNt;').replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvWt = (modelMatrix * vec4(transformed, 1.0)).xyz; vNt = normalize(mat3(modelMatrix) * objectNormal);');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vWt; varying vec3 vNt;')
      .replace('#include <color_fragment>', `#include <color_fragment>
  { vec3 a = abs(vNt); vec2 p = a.y > 0.5 ? vWt.xz : (a.x > 0.5 ? vWt.zy : vWt.xy);
    vec2 g = abs(fract(p / ${size.toFixed(3)}) - 0.5); float gr = 1.0 - smoothstep(0.47, 0.485, max(g.x, g.y));
    vec2 id = floor(p / ${size.toFixed(3)}); float v = fract(sin(dot(id, vec2(12.9898, 78.233))) * 43758.5453);
    diffuseColor.rgb = mix(vec3(${grout.join(',')}), vec3(${base.join(',')}) * (0.95 + 0.08 * v), gr); }`);
  };
  return m;
}
const wallTile = tileMat([0.86, 0.9, 0.9], [0.62, 0.64, 0.64], 0.15), floorTile = tileMat([0.36, 0.38, 0.42], [0.22, 0.22, 0.24], 0.3, 0.5);
const paintMat = new THREE.MeshStandardMaterial({ color: 0xe9e2d4, roughness: 0.9 });
const ROOM = [];
const boxm = (w, h, d, x, y, z, m, r = 0) => { const o = new THREE.Mesh(r > 0 ? new RoundedBoxGeometry(w, h, d, 2, Math.min(r, 0.4 * Math.min(w, h, d))) : new THREE.BoxGeometry(w, h, d), m); o.position.set(x, y, z); o.castShadow = true; o.receiveShadow = true; scene.add(o); ROOM.push(o); return o; };
boxm(RX1 - RX0, 0.05, RZ1 - RZ0, (RX0 + RX1) / 2, -0.025, (RZ0 + RZ1) / 2, floorTile);
boxm(RX1 - RX0, 0.05, RZ1 - RZ0, (RX0 + RX1) / 2, RH + 0.025, (RZ0 + RZ1) / 2, paintMat);
const WALLS = [];
WALLS.push({ m: boxm(RX1 - RX0, RH, 0.1, (RX0 + RX1) / 2, RH / 2, RZ0 - 0.05, wallTile), out: c => c.z < RZ0 + 0.02 });   // behind the toilet
WALLS.push({ m: boxm(0.1, RH, RZ1 - RZ0, RX0 - 0.05, RH / 2, (RZ0 + RZ1) / 2, wallTile), out: c => c.x < RX0 + 0.02 });   // vanity wall
WALLS.push({ m: boxm(0.1, RH, RZ1 - RZ0, RX1 + 0.05, RH / 2, (RZ0 + RZ1) / 2, wallTile), out: c => c.x > RX1 - 0.02 });
const DOOR = { x0: -0.78, x1: 0.06, h: 2.05 };                                          // the doorway in the wall behind him
boxm(DOOR.x0 - RX0, RH, 0.1, (RX0 + DOOR.x0) / 2, RH / 2, RZ1 + 0.05, wallTile);
boxm(RX1 - DOOR.x1, RH, 0.1, (DOOR.x1 + RX1) / 2, RH / 2, RZ1 + 0.05, wallTile);
boxm(DOOR.x1 - DOOR.x0, RH - DOOR.h, 0.1, (DOOR.x0 + DOOR.x1) / 2, (RH + DOOR.h) / 2, RZ1 + 0.05, wallTile);
{ const dm = new THREE.MeshStandardMaterial({ color: 0xf4f1ea, roughness: 0.6 });
  const door = new THREE.Group(); door.position.set(DOOR.x0, 0, RZ1 + 0.1); door.rotation.y = -1.35; scene.add(door);
  const slab = new THREE.Mesh(new RoundedBoxGeometry(DOOR.x1 - DOOR.x0 - 0.02, DOOR.h - 0.02, 0.04, 2, 0.01), dm); slab.position.set((DOOR.x1 - DOOR.x0) / 2, DOOR.h / 2, 0); slab.castShadow = true; door.add(slab);
  const kn = new THREE.Mesh(new THREE.SphereGeometry(0.03, 16, 12), new THREE.MeshStandardMaterial({ color: 0xcccccc, metalness: 1, roughness: 0.25 })); kn.position.set(DOOR.x1 - DOOR.x0 - 0.1, 1.0, 0.04); door.add(kn); }
// the hallway beyond the door (bright: fresh air)
const hallMat = new THREE.MeshStandardMaterial({ color: 0xf2ece0, roughness: 0.9 });
boxm(2.6, 0.05, 3.2, -0.35, -0.025, RZ1 + 1.7, new THREE.MeshStandardMaterial({ color: 0xa47a52, roughness: 0.7 }));
boxm(0.1, RH, 3.2, -1.7, RH / 2, RZ1 + 1.7, hallMat); boxm(0.1, RH, 3.2, 1.0, RH / 2, RZ1 + 1.7, hallMat);
boxm(2.6, 0.05, 3.2, -0.35, RH + 0.025, RZ1 + 1.7, hallMat);
{ const win = new THREE.Mesh(new THREE.PlaneGeometry(1.1, 1.2), new THREE.MeshBasicMaterial({ color: 0xffffff, toneMapped: false })); win.position.set(0.94, 1.45, RZ1 + 2.0); win.rotation.y = -Math.PI / 2; scene.add(win); }
// vanity, sink basin, mirror (the one Easter egg: a sticky note with SUBSCRIBE on the mirror)
boxm(0.55, 0.82, 0.95, RX0 + 0.28, 0.41, -0.55, new THREE.MeshStandardMaterial({ color: 0x5a4636, roughness: 0.7 }), 0.02);
boxm(0.58, 0.04, 1.0, RX0 + 0.29, 0.84, -0.55, new THREE.MeshStandardMaterial({ color: 0xe8e4dc, roughness: 0.3 }), 0.01);
{ const mir = new THREE.Mesh(new THREE.PlaneGeometry(0.8, 0.95), new THREE.MeshStandardMaterial({ color: 0xc8d4da, metalness: 1, roughness: 0.05 })); mir.position.set(RX0 + 0.005, 1.55, -0.55); mir.rotation.y = Math.PI / 2; scene.add(mir);
  const st = canvasTex(256, 256, g => { g.fillStyle = '#ffe25a'; g.fillRect(0, 0, 256, 256); g.fillStyle = '#c0202a'; g.font = 'bold 44px Inter, Arial'; g.textAlign = 'center'; g.fillText('SUB', 128, 110); g.fillText('SCRIBE!', 128, 170); });
  const s = new THREE.Mesh(new THREE.PlaneGeometry(0.09, 0.09), new THREE.MeshStandardMaterial({ map: st, roughness: 0.8 })); s.position.set(RX0 + 0.008, 1.88, -0.25); s.rotation.y = Math.PI / 2; scene.add(s); }

// ------------------------------------------------------------------ the toilet (against the back wall), its water, the bleach jug
const TOI = V(0.32, 0, -0.84);
const porcelain = new THREE.MeshPhysicalMaterial({ color: 0xf6f6f2, roughness: 0.12, clearcoat: 1, clearcoatRoughness: 0.05 });
const toilet = new THREE.Group(); toilet.position.copy(TOI); scene.add(toilet);
{ const prof = []; for (let i = 0; i <= 24; i++) { const u = i / 24; prof.push(new THREE.Vector2(0.11 + 0.08 * Math.sin(u * Math.PI * 0.55) + 0.05 * u * u, u * 0.4)); }
  const bowlO = new THREE.Mesh(new THREE.LatheGeometry(prof, 48), porcelain); bowlO.scale.set(1, 1, 1.25); toilet.add(bowlO);
  const inner = []; for (let i = 0; i <= 24; i++) { const u = i / 24; inner.push(new THREE.Vector2(0.03 + 0.19 * Math.pow(u, 0.6), 0.16 + u * 0.235)); }
  const bowlI = new THREE.Mesh(new THREE.LatheGeometry(inner, 48), new THREE.MeshPhysicalMaterial({ color: 0xf2f2ee, roughness: 0.1, clearcoat: 1, side: THREE.BackSide })); bowlI.scale.set(1, 1, 1.25); toilet.add(bowlI);
  const rim = new THREE.Mesh(new THREE.TorusGeometry(0.225, 0.022, 14, 48).rotateX(Math.PI / 2), porcelain); rim.position.y = 0.4; rim.scale.set(1, 1, 1.25); toilet.add(rim);
  const seat = new THREE.Mesh(new THREE.TorusGeometry(0.21, 0.03, 10, 48).rotateX(Math.PI / 2).scale(1, 0.35, 1.25), new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.3 })); seat.position.y = 0.43; toilet.add(seat);
  const lid = new THREE.Mesh(new THREE.CylinderGeometry(0.24, 0.24, 0.025, 40).scale(1, 1, 1.25), new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.3 })); lid.position.set(0, 0.72, -0.27); lid.rotation.x = -1.48; toilet.add(lid);
  const tank = new THREE.Mesh(new RoundedBoxGeometry(0.5, 0.42, 0.2, 3, 0.03), porcelain); tank.position.set(0, 0.62, -0.3); toilet.add(tank);
  const tlid = new THREE.Mesh(new RoundedBoxGeometry(0.53, 0.04, 0.22, 3, 0.015), porcelain); tlid.position.set(0, 0.85, -0.3); toilet.add(tlid);
  const fl = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 0.05, 10).rotateZ(Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0xcccccc, metalness: 1, roughness: 0.2 })); fl.position.set(-0.2, 0.78, -0.19); toilet.add(fl);
  toilet.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } }); }
const WATER_Y = 0.3;
const bowlU = { uT: { value: 0 }, uCloud: { value: 0 }, uBlue: { value: 0 } };
const bowlWaterMat = new THREE.ShaderMaterial({ transparent: true, uniforms: bowlU,
  vertexShader: 'varying vec2 vP; void main(){ vP = position.xy; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
  fragmentShader: `varying vec2 vP; uniform float uT, uCloud, uBlue;
  float hh(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
  float vn(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f*f*(3.0-2.0*f); return mix(mix(hh(i), hh(i+vec2(1,0)), u.x), mix(hh(i+vec2(0,1)), hh(i+vec2(1,1)), u.x), u.y); }
  void main(){ vec2 p = vP * 9.0; float r = length(vP) / 0.2;
    vec2 sw = vec2(cos(uT * 0.8 + r * 3.0), sin(uT * 0.8 + r * 3.0)) * 0.6;
    float cl = vn(p + sw + uT * 0.3) * 0.6 + vn(p * 2.3 - sw * 1.4) * 0.4;
    vec3 clear = vec3(0.06, 0.2, 0.24), milky = vec3(0.92, 0.95, 0.8);
    float ten = 1.0 - smoothstep(0.0, 0.07, abs(cl - 0.5));                       // milky tendrils curling through
    float k = (ten * 0.85 + smoothstep(0.62, 0.8, cl) * 0.7) * uCloud;
    vec3 c = clear * (0.8 + 0.4 * (1.0 - r));
    float bl = smoothstep(0.5, 0.62, vn(p * 1.3 - sw * 2.0 + vec2(uT * 0.5, 0.0))) * uBlue;   // blue streaks of glass cleaner swirling in
    c = mix(c, vec3(0.05, 0.5, 1.0), bl * 0.95);
    c = mix(c, milky, clamp(k, 0.0, 1.0));
    float ring = 0.5 + 0.5 * sin(r * 30.0 - uT * 5.0); c += vec3(0.05) * ring * (1.0 - uCloud);
    gl_FragColor = vec4(c, mix(0.85, 0.97, clamp(k, 0.0, 1.0)));
    #include <tonemapping_fragment>
    #include <colorspace_fragment>
  }` });
const bowlWater = new THREE.Mesh(new THREE.CircleGeometry(0.17, 48).scale(1, 1.25, 1), bowlWaterMat); bowlWater.rotation.x = -Math.PI / 2; bowlWater.position.set(TOI.x, WATER_Y, TOI.z); scene.add(bowlWater);
{ // bleach jug on the floor next to the toilet (white, BLEACH label, no brand)
  const lab = canvasTex(256, 200, g => { g.fillStyle = '#ffffff'; g.fillRect(0, 0, 256, 200); g.fillStyle = '#1b5fb4'; g.fillRect(0, 40, 256, 120); g.fillStyle = '#fff'; g.font = 'bold 62px Inter, Arial'; g.textAlign = 'center'; g.fillText('BLEACH', 128, 122); });
  const jug = new THREE.Group(); jug.position.set(0.72, 0, -0.62); jug.rotation.y = -0.5; scene.add(jug);
  const body = new THREE.Mesh(new RoundedBoxGeometry(0.17, 0.27, 0.11, 3, 0.03), [new THREE.MeshStandardMaterial({ color: 0xf4f4f4, roughness: 0.4 }), new THREE.MeshStandardMaterial({ color: 0xf4f4f4, roughness: 0.4 }), new THREE.MeshStandardMaterial({ color: 0xf4f4f4, roughness: 0.4 }), new THREE.MeshStandardMaterial({ color: 0xf4f4f4, roughness: 0.4 }), new THREE.MeshStandardMaterial({ map: lab, roughness: 0.4 }), new THREE.MeshStandardMaterial({ color: 0xf4f4f4, roughness: 0.4 })]);
  body.position.y = 0.135; body.castShadow = true; jug.add(body);
  const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.022, 0.03, 0.05, 16), new THREE.MeshStandardMaterial({ color: 0xf4f4f4, roughness: 0.4 })); neck.position.set(0.04, 0.295, 0); jug.add(neck);
  const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.026, 0.026, 0.03, 16), new THREE.MeshStandardMaterial({ color: 0x1b5fb4, roughness: 0.4 })); cap.position.set(0.04, 0.33, 0); jug.add(cap);
  const h = new THREE.Mesh(new THREE.TorusGeometry(0.035, 0.012, 8, 20, Math.PI), new THREE.MeshStandardMaterial({ color: 0xf4f4f4, roughness: 0.4 })); h.position.set(-0.04, 0.27, 0); h.rotation.z = 0; jug.add(h); }

// ------------------------------------------------------------------ the spray bottle (blue glass cleaner, a GLASS label, no brand) and the phone
const bottle = new THREE.Group(); scene.add(bottle);
{ const lab = canvasTex(256, 256, g => { g.fillStyle = '#ffffff'; g.fillRect(0, 0, 256, 256); g.fillStyle = '#1aa3d9'; g.font = 'bold 60px Inter, Arial'; g.textAlign = 'center'; g.fillText('GLASS', 128, 110); g.font = 'bold 34px Inter, Arial'; g.fillStyle = '#555'; g.fillText('CLEANER', 128, 160); });
  const liq = new THREE.MeshPhysicalMaterial({ color: 0x2aa8e8, roughness: 0.1, transmission: 0.0, transparent: true, opacity: 0.85 });
  const body = new THREE.Mesh(new THREE.CylinderGeometry(0.036, 0.04, 0.17, 24), liq); body.position.y = -0.11; bottle.add(body);
  const lb = new THREE.Mesh(new THREE.CylinderGeometry(0.0405, 0.0405, 0.07, 24, 1, true, -0.9, 1.8), new THREE.MeshStandardMaterial({ map: lab, roughness: 0.5 })); lb.position.y = -0.12; lb.rotation.y = Math.PI; bottle.add(lb);
  const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.016, 0.022, 0.04, 16), new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.4 })); neck.position.y = -0.015; bottle.add(neck);
  const head = new THREE.Mesh(new RoundedBoxGeometry(0.036, 0.04, 0.085, 2, 0.01), new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.4 })); head.position.set(0, 0.022, -0.02); bottle.add(head);
  const noz = new THREE.Mesh(new THREE.CylinderGeometry(0.008, 0.008, 0.02, 10).rotateX(Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0xff7a1a, roughness: 0.5 })); noz.position.set(0, 0.025, -0.07); bottle.add(noz);
  const trig = new THREE.Mesh(new RoundedBoxGeometry(0.014, 0.05, 0.018, 2, 0.005), new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.4 })); trig.position.set(0, -0.012, -0.05); bottle.add(trig);
  bottle.traverse(o => { if (o.isMesh) o.castShadow = true; }); }
const NOZZLE = V(0, 0.025, -0.082);                                // bottle-local nozzle tip; spray goes along local -z
const phone = new THREE.Group(); scene.add(phone);
{ const p = new THREE.Mesh(new RoundedBoxGeometry(0.072, 0.15, 0.009, 2, 0.004), new THREE.MeshStandardMaterial({ color: 0x1a1b1e, roughness: 0.3, metalness: 0.4 })); phone.add(p);
  const sc = new THREE.Mesh(new THREE.PlaneGeometry(0.064, 0.138), new THREE.MeshBasicMaterial({ color: 0x3a8ad6, toneMapped: false })); sc.position.z = 0.0048; phone.add(sc); phone.visible = false; }

// ------------------------------------------------------------------ the haze (spray mist, the rising gas) and the bowl's fizz
const softTex = canvasTex(64, 64, g => { const gr = g.createRadialGradient(32, 32, 0, 32, 32, 31); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.45, 'rgba(255,255,255,0.45)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); });
function cloud(n, size, color, op) { const g = new THREE.BufferGeometry(); const p = new Float32Array(n * 3); g.setAttribute('position', new THREE.BufferAttribute(p, 3));
  const m = new THREE.Points(g, new THREE.PointsMaterial({ map: softTex, color, size, transparent: true, depthWrite: false, opacity: op })); m.frustumCulled = false; scene.add(m); return { m, p, n }; }
const mist = cloud(500, 0.035, 0xdff4ff, 0.75);                    // the spray itself
const gas = cloud(420, 0.3, 0xcfe08a, 0.2);                      // the yellow-green haze rising from the bowl
const fizz = cloud(420, 0.011, 0xf2fff0, 0.95);                     // bubbles popping on the water (macro)
const inhale = cloud(160, 0.012, 0xc8f05a, 0.9);                   // gas going into his nose and down his airway (x-ray)
function setCloud(c, fn) { let k = 0; for (let i = 0; i < c.n; i++) { const q = fn(i); if (q) { c.p.set([q.x, q.y, q.z], k * 3); k++; } } for (let i = k; i < c.n; i++) c.p.set([0, -99, 0], i * 3); c.m.geometry.attributes.position.needsUpdate = true; c.m.visible = k > 0; }

// ------------------------------------------------------------------ the molecule stage (beat 2): ammonia + hypochlorous acid -> chloramine + water
const MOL = V(400, 0, 0);
const molStage = new THREE.Group(); molStage.position.copy(MOL); scene.add(molStage);
const molBg = new THREE.Mesh(new THREE.SphereGeometry(6, 32, 16), new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false,
  vertexShader: 'varying vec3 vD; void main(){ vD = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
  fragmentShader: 'varying vec3 vD; void main(){ float h = vD.y * 0.5 + 0.5; vec3 c = mix(vec3(0.03, 0.05, 0.09), vec3(0.08, 0.14, 0.2), h); gl_FragColor = vec4(pow(c, vec3(2.2)) * 3.0, 1.0); }' }));
molStage.add(molBg);
const ATOM = { N: [0x3d6df2, 0.11], H: [0xf2f2f2, 0.065], O: [0xe8402a, 0.1], Cl: [0x3fd65a, 0.13] };
const atomMats = {}; for (const [k, [c]] of Object.entries(ATOM)) atomMats[k] = new THREE.MeshPhysicalMaterial({ color: c, roughness: 0.25, clearcoat: 1, clearcoatRoughness: 0.1 });
function atom(el) { const m = new THREE.Mesh(new THREE.SphereGeometry(ATOM[el][1], 32, 20), atomMats[el]); m.castShadow = true; molStage.add(m); return m; }
const bondMat = new THREE.MeshStandardMaterial({ color: 0xcfd6dd, roughness: 0.4 });
const bonds = []; for (let i = 0; i < 8; i++) { const b = new THREE.Mesh(new THREE.CylinderGeometry(0.022, 0.022, 1, 12), bondMat); molStage.add(b); bonds.push(b); }
function bond(i, a, b) { const m = bonds[i]; if (!a || !b) { m.visible = false; return; } m.visible = true; const d = b.clone().sub(a); m.position.copy(a).add(b).multiplyScalar(0.5); m.scale.set(1, d.length(), 1); m.quaternion.setFromUnitVectors(V(0, 1, 0), d.normalize()); }
const A_ = { N: atom('N'), H1: atom('H'), H2: atom('H'), H3: atom('H'), O: atom('O'), Hw: atom('H'), Cl: atom('Cl') };
{ const k = new THREE.DirectionalLight(0xffffff, 2.5); k.position.set(-1, 2, -3); molStage.add(k); molStage.add(k.target); const r = new THREE.PointLight(0x7fb8ff, 3, 6); r.position.set(1.5, -0.5, 1); molStage.add(r); }
const molLabels = {};
function textSprite(txt, col) { const t = canvasTex(512, 128, g => { g.font = 'bold 64px Inter, Arial'; g.textAlign = 'center'; g.lineWidth = 10; g.strokeStyle = '#111'; g.strokeText(txt, 256, 86); g.fillStyle = col; g.fillText(txt, 256, 86); });
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: t, transparent: true, depthTest: false })); s.scale.set(0.9, 0.225, 1); s.renderOrder = 20; molStage.add(s); return s; }
molLabels.amm = textSprite('AMMONIA', '#9fbaff'); molLabels.hoc = textSprite('BLEACH (HOCl)', '#a8f0b0'); molLabels.chl = textSprite('CHLORAMINE', '#c8f05a'); molLabels.wat = textSprite('WATER', '#ffffff');

// ------------------------------------------------------------------ the guy and the x-ray organs (airway, lungs, fluid, nose, smell nerve)
const G = await loadGuy(THREE, '/char/guy', {});
scene.add(G.root); G.root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
const HIP = V(0.0, 0.95, 0.0);
const HOME = V(0.04, 0.95, -0.28);                                 // where he stands, facing the toilet (-z)
function untwistSafe() { for (const S of ['R', 'L']) { const ua = G.bones['uarm' + S], ut = G.bones['uarmTwist' + S]; ua.quaternion.multiply(ut.quaternion); ut.quaternion.identity(); } G.untwist(); }
const GUYMATS = new Set(); G.root.traverse(o => { if (o.isMesh) (Array.isArray(o.material) ? o.material : [o.material]).forEach(m => GUYMATS.add(m)); });
for (const m of GUYMATS) { m.transparent = true; m.userData.op0 = m.opacity ?? 1; }
const XRAY = new THREE.Color(0x4aa3ff);
for (const m of GUYMATS) { m.userData.em0 = m.emissive ? m.emissive.clone() : null; }
function ghost(k) { for (const m of GUYMATS) { m.opacity = lerp(m.userData.op0, m === G.mat.shirt ? 0.07 : 0.2, k); m.depthWrite = k < 0.02;
  if (m.emissive) m.emissive.copy(m.userData.em0).lerp(XRAY, 0.55 * k); } }
const organMat = (c, op = 0.6) => new THREE.MeshPhysicalMaterial({ color: c, emissive: c, emissiveIntensity: 0.35, roughness: 0.35, clearcoat: 0.6, transparent: true, opacity: Math.min(1, op + 0.25) });
function attach(obj, boneName) { G.reset(); G.root.updateMatrixWorld(true); obj.updateMatrixWorld(true); obj.applyMatrix4(G.bones[boneName].matrixWorld.clone().invert()); G.bones[boneName].add(obj); }
const organs = new THREE.Group();
const AIRWAY = new THREE.CatmullRomCurve3([V(0, 1.6, -0.075), V(0, 1.585, -0.04), V(0, 1.53, -0.03), V(0, 1.47, -0.02), V(0, 1.4, -0.01)]);
organs.add(new THREE.Mesh(new THREE.TubeGeometry(AIRWAY, 30, 0.011, 12, false), organMat(0xf3a7b4, 0.7)));
const BRONCH = [1, -1].map(s => new THREE.CatmullRomCurve3([V(0, 1.4, -0.01), V(0.035 * s, 1.37, -0.005), V(0.07 * s, 1.33, 0.0)]));
for (const c of BRONCH) organs.add(new THREE.Mesh(new THREE.TubeGeometry(c, 16, 0.008, 10, false), organMat(0xf3a7b4, 0.7)));
const LUNG = s => ({ c: V(0.075 * s, 1.31, 0.0), r: V(0.062, 0.11, 0.06) });
const lungs = [1, -1].map(s => { const L = LUNG(s); const m = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 24), organMat(0xf2a3b0, 0.3)); m.material.depthWrite = false; m.scale.copy(L.r); m.position.copy(L.c); organs.add(m); return m; });
const fluidPlane = new THREE.Plane(V(0, -1, 0), 0);
const fluids = [1, -1].map(s => { const L = LUNG(s); const m = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 24), new THREE.MeshStandardMaterial({ color: 0x3f8fe0, emissive: 0x0d3a70, transparent: true, opacity: 0.75, clippingPlanes: [fluidPlane] })); m.scale.copy(L.r).multiplyScalar(0.92); m.position.copy(L.c); organs.add(m); return m; });
// nose: the smell patch at the top of the nose, the nerve up to the brain's smell bulb
const SMELL = V(0, 1.655, -0.085), BULB = V(0, 1.68, -0.05);
const smellPatch = new THREE.Mesh(new THREE.SphereGeometry(0.008, 16, 12), new THREE.MeshStandardMaterial({ color: 0xffe28a, emissive: 0xffc23a, emissiveIntensity: 1.5 })); smellPatch.position.copy(SMELL); const headOrg = new THREE.Group(); headOrg.add(smellPatch);
const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.012, 16, 12).scale(1.6, 0.7, 1.4), organMat(0xf0c0d0, 0.8)); bulb.position.copy(BULB); headOrg.add(bulb);
const brain = new THREE.Mesh(new THREE.SphereGeometry(0.068, 32, 20).scale(1, 0.75, 1.15), organMat(0xf0b8c8, 0.0)); brain.material.opacity = 0.18; brain.material.depthWrite = false; brain.position.set(0, 1.72, 0.0); headOrg.add(brain);
const NERVE = new THREE.CatmullRomCurve3([SMELL, V(0, 1.668, -0.07), BULB, V(0, 1.7, -0.02)]);
headOrg.add(new THREE.Mesh(new THREE.TubeGeometry(NERVE, 16, 0.0025, 8, false), organMat(0xffe0a0, 0.8)));
const pulses = [0, 1, 2, 3].map(() => { const m = new THREE.Mesh(new THREE.SphereGeometry(0.0055, 12, 8), new THREE.MeshBasicMaterial({ color: 0xfff1a0, transparent: true, toneMapped: false })); headOrg.add(m); return m; });
organs.traverse(o => { if (o.isMesh) o.renderOrder = 6; }); headOrg.traverse(o => { if (o.isMesh) o.renderOrder = 6; });
attach(organs, 'chest'); organs.visible = false; attach(headOrg, 'head'); headOrg.visible = false;
G.reset();

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
  const m = MEM[key]; const prev = m && (m.frame === frame - 1 || (m.frame === -1 && frame === 0)) ? m.a : null;
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


// ------------------------------------------------------------------ points that ride on his head (mouth, right ear)
const MOUTH = new THREE.Object3D(); MOUTH.position.set(0, G.man.mouthY, G.man.mouthZ); attach(MOUTH, 'head');
const EARR = new THREE.Object3D(); EARR.position.set(0.078, 1.632, 0.005); attach(EARR, 'head');
G.reset();
const wpos = o => o.getWorldPosition(new THREE.Vector3());

// ------------------------------------------------------------------ the story, beat by beat
function blink(t) { for (const b0 of [2.2, 6.1, 12.4, 19.3, 23.0, 29.0, 33.1]) { const u = (t - b0) / 0.16; if (u > 0 && u < 1) return Math.sin(Math.PI * u); } return 0; }
const BOWL = V(TOI.x, WATER_Y, TOI.z);
const SPRAY_P = V(0.26, 1.16, -0.6);                                // palm while spraying
function sprayTarget(lift = 1) {                                    // hand on the bottle, nozzle aimed at the water
  const p = V(0.2, 0.86, -0.36).lerp(SPRAY_P, lift);
  const aim = BOWL.clone().sub(p).normalize().lerp(V(0, -0.2, -1).normalize(), 1 - lift).normalize();
  const up = V(0, 1, 0).sub(aim.clone().multiplyScalar(aim.y)).normalize();
  return { S: 'R', p, w: up.clone().negate(), u: aim, c: 62, bottle: true };
}
const SIDE = { S: 'R', p: V(0.24, 0.9, -0.24), w: V(0, -1, 0), u: V(0, 0, -1), c: 62, bottle: true };   // bottle hanging at his side
const yawQ = deg => new THREE.Quaternion().setFromAxisAngle(V(0, 1, 0), deg * D2R);
function guyAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  let pose = P.stand, root = {}, face = { blink: blink(t) }, hands = [], xr = 0, walk = null, phoneOn = false, bottleOn = true;
  const spraying = (b === 0 && lt < 1.9) || (b === 9 && lt > d - 0.35);
  if (b === 9) {                                                    // calm, at the toilet; lifts the bottle and starts to spray (loops)
    const lift = smooth(0.5, d - 0.45, lt);
    pose = mixPose(P.stand, P.spray, lift); hands = [sprayTarget(lift)];
    face = { ...face, brow: 0.15, smile: 0.15 * (1 - lift), press: 0.2 * lift, look: [0.1, -0.3 - 0.3 * lift] };
  } else if (b === 0) {                                             // sprays, then the haze hits him: he pulls back
    const back = smooth(2.0, 3.0, lt);
    pose = mixPose(P.spray, P.recoil, back); hands = [sprayTarget(1 - smooth(1.9, 2.8, lt))];
    root = { z: HOME.z + 0.08 * back };
    face = { ...face, press: 0.2, look: [0.1, -0.6 * (1 - back)], squint: 0.8 * back, sneer: 0.5 * back, browIn: 0.7 * back, frown: 0.3 * back };
  } else if (b === 3 || b === 7) {                                  // x-ray: standing, gas going in / lungs filling
    pose = b === 7 ? addPose(P.stand, { spine1: [-4, 0, 0], neck: [-6, 0, 0] }) : addPose(P.stand, { chest: [3 * Math.sin(t * 2.4), 0, 0] }); hands = [SIDE]; xr = 1;
    face = { ...face, squint: 0.5, browIn: 0.6, press: 0.3 };
  } else if (b === 4) {                                             // coughing fits, left hand over his mouth, eyes squeezed shut
    const c = Math.pow(Math.max(0, Math.sin(2 * Math.PI * 1.6 * lt)), 3) * smooth(0, 0.3, lt);
    pose = addPose(P.cough, { spine1: [-12 * c, 0, 0], spine2: [-8 * c, 0, 0], neck: [-10 * c, 0, 0] });
    root = { s: 0.03 + 0.03 * c, z: HOME.z + 0.08 };
    hands = [SIDE, { S: 'L', p: null, n: null, mouth: true, c: 30 }];
    face = { ...face, blink: 0.9, pain: 0.7 + 0.3 * c, squint: 1, browIn: 1, frown: 0.5, jaw: 0.25 * c };
  } else if (b === 5) {                                             // the myth: he leans in, sniffs, shrugs - smells fine now
    const sn = smooth(0.1, 0.9, lt) * (1 - smooth(1.6, 2.3, lt)), sh = smooth(1.7, 2.4, lt);
    pose = mixPose(mixPose(P.stand, P.sniff, sn), P.shrug, sh); hands = [SIDE];
    root = { z: HOME.z + 0.05 };
    face = { ...face, squint: 0.3 * sn, sneer: 0.2 * sn, brow: 0.6 * sh, smile: 0.4 * sh, look: [0, -0.4 * sn] };
  } else if (b === 6) {                                             // x-ray of his head: the smell signal fades while the gas keeps coming in
    pose = addPose(P.stand, { chest: [2 * Math.sin(t * 2.4), 0, 0] }); hands = [SIDE]; xr = 1;
    face = { ...face, smile: 0.2, brow: 0.2 };
  } else if (b === 8) {                                             // out the door: walking, coughing, phone to his ear
    const k = lt / d; bottleOn = false; phoneOn = true;
    const A0 = V(-0.12, 0.95, -0.15), A1 = V(-0.37, 0.95, 2.05);
    const ph = 2 * Math.PI * 0.95 * lt, ramp = smooth(0, 0.3, lt);
    const pos = A0.clone().lerp(A1, lt / d);
    const c = Math.pow(Math.max(0, Math.sin(2 * Math.PI * 0.7 * lt + 1)), 4);
    pose = addPose(P.walk, { armL: [-18 * Math.sin(ph) * ramp, 0, 0, 10, 0], spine2: [0, 4 * Math.sin(ph) * ramp, 0], spine1: [-8 * c, 0, 0], neck: [-6 * c, 0, 0] });
    root = { x: pos.x, z: pos.z, yaw: 180 + Math.atan2(A1.x - A0.x, A1.z - A0.z) / D2R * 0 - 7, s: 0.015 * Math.abs(Math.sin(ph)) * ramp + 0.02 };
    walk = { A0, A1, d, lt };
    hands = [{ S: 'R', ear: true, c: 40 }];
    face = { ...face, squint: 0.6, browIn: 0.7, press: 0.2 + 0.4 * c, jaw: 0.15, look: [0, 0] };
  } else { pose = P.stand; hands = [SIDE]; }                        // beats 1 and 2: not on screen
  return { pose, root, face, hands, xr, walk, phoneOn, bottleOn, spraying };
}
const FEETHOME = { R: V(0.16, 0.102, -0.3), L: V(-0.08, 0.102, -0.26) };

// ------------------------------------------------------------------ cameras
function shake(t, a, f = 1) { return V(vn1(t * 3 * f, 1) * a, vn1(t * 3 * f, 2) * a, vn1(t * 3 * f, 3) * a * 0.5); }
const HOOK = { pos: V(1.8, 1.62, -1.5), tgt: V(0.16, 0.98, -0.55), fov: 48 };
function camAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b], u = lt / d;
  let pos, tgt, fov = 42;
  const hp = G.bones.hips.getWorldPosition(new THREE.Vector3()), hd = G.bones.head.getWorldPosition(new THREE.Vector3());
  if (b === 0) { pos = HOOK.pos.clone().add(V(0.05 * u, 0.08 * u, 0.1 * u)); tgt = HOOK.tgt.clone().add(V(0, 0.2 * smooth(0.4, 1, u), 0)); fov = HOOK.fov; }
  else if (b === 9) { const w = smooth(d - 1.2, d, lt); pos = V(1.1, 1.55, -1.3).lerp(HOOK.pos, w); tgt = V(0.1, 1.1, -0.3).lerp(HOOK.tgt, w); fov = lerp(42, HOOK.fov, w); }
  else if (b === 1) { pos = V(TOI.x + 0.12 - 0.03 * u, 0.62 - 0.06 * u, TOI.z + 0.24 - 0.04 * u); tgt = V(TOI.x - 0.01, WATER_Y, TOI.z - 0.05); fov = 40; }
  else if (b === 2) { pos = MOL.clone().add(V(0.15 - 0.3 * u, 0.25, -2.4 + 0.35 * u)); tgt = MOL.clone(); fov = 40; }
  else if (b === 3) { pos = V(0.3 - 0.08 * u, 1.48, -1.25 + 0.1 * u).add(V(hp.x, 0, hp.z - HOME.z)); tgt = V(hp.x, 1.44, hp.z - 0.02); fov = 38; }
  else if (b === 4) { pos = V(0.85, 1.35, -1.9 + 0.15 * u); tgt = V(0.05, 1.18, -0.2); fov = 40; pos.add(shake(t, 0.006, 2)); }
  else if (b === 5) { pos = V(0.95 - 0.1 * u, 1.55, -1.85); tgt = V(0.15, 1.15, -0.45); fov = 42; }
  else if (b === 6) { pos = V(0.42 - 0.08 * u, 1.69, -0.78 + 0.06 * u); tgt = V(hd.x, 1.66, hd.z - 0.04); fov = 30; }
  else if (b === 7) { pos = V(0.22 - 0.05 * u, 1.36, -1.15 + 0.12 * u); tgt = V(hp.x, 1.32, hp.z); fov = 38; }
  else { pos = V(-0.42, 1.52, 3.15); tgt = V(hp.x * 0.6 - 0.15, 1.12, hp.z); fov = 44; }
  const punch = b > 0 ? (1 - smooth(0, 0.22, lt)) * 0.07 : 0;
  return { pos, tgt, fov: fov * (1 - punch) };
}

// ------------------------------------------------------------------ the molecules (beat 2)
function molecules(t) {
  const lt = t - B[2], d = DUR[2], k = smooth(0.8, 2.2, lt);          // they meet; Cl jumps to N, H jumps to O
  const spin = qa => new THREE.Quaternion().setFromEuler(new THREE.Euler(0.3, qa, 0));
  const nPos = V(-0.55 + 0.3 * smooth(0, 1.2, lt), 0.05, 0), hocPos = V(0.6 - 0.3 * smooth(0, 1.2, lt), -0.05, 0);
  const nq = spin(lt * 0.6), oq = spin(-lt * 0.5);
  const at = (c, q, v) => c.clone().add(v.clone().applyQuaternion(q));
  // ammonia: N with 3 H in a pyramid; after: one H has left for the water, Cl sits there
  const Hs = [V(0.0, 0.17, 0.0), V(0.15, -0.07, 0.06), V(-0.1, -0.07, 0.13)];
  A_.N.position.copy(nPos);
  A_.H1.position.copy(at(nPos, nq, Hs[0]));
  A_.H2.position.copy(at(nPos, nq, Hs[1]));
  const hLeave = at(nPos, nq, Hs[2]);
  // HOCl: O bonded to H and Cl
  const oP = at(hocPos, oq, V(0, 0, 0)), hwP = at(hocPos, oq, V(0.0, -0.16, 0.05)), clP0 = at(hocPos, oq, V(-0.2, 0.08, 0));
  A_.O.position.copy(oP); A_.Hw.position.copy(hwP);
  const clEnd = at(nPos, nq, Hs[2].clone().multiplyScalar(1.45)), hEnd = at(oP.clone(), oq, V(0.06, 0.15, -0.05));
  A_.Cl.position.copy(clP0.clone().lerp(clEnd, k)); A_.H3.position.copy(hLeave.clone().lerp(hEnd, k));
  // after the swap the two new molecules drift apart
  const apart = smooth(2.2, d, lt);
  for (const n of ['O', 'Hw', 'H3']) A_[n].position.add(V(0.35 * apart, -0.15 * apart, 0.1 * apart));
  for (const n of ['N', 'H1', 'H2', 'Cl']) A_[n].position.add(V(-0.2 * apart, 0.12 * apart, -0.1 * apart));
  const mid = k > 0.15 && k < 0.85;
  bond(0, A_.N.position, A_.H1.position); bond(1, A_.N.position, A_.H2.position);
  bond(2, k < 0.5 ? A_.N.position : null, A_.H3.position); bond(3, A_.O.position, A_.Hw.position);
  bond(4, k < 0.5 ? A_.O.position : null, A_.Cl.position); bond(5, k >= 0.5 ? A_.N.position : null, A_.Cl.position); bond(6, k >= 0.5 ? A_.O.position : null, A_.H3.position);
  bonds[2].visible = bonds[2].visible && !mid; bonds[4].visible = bonds[4].visible && !mid; bonds[5].visible = bonds[5].visible && !mid; bonds[6].visible = bonds[6].visible && !mid;
  bond(7, null, null);
  const before = 1 - smooth(1.0, 1.5, lt), after = smooth(2.3, 2.7, lt);
  molLabels.amm.position.copy(nPos).add(V(0, 0.42, 0)); molLabels.amm.material.opacity = before;
  molLabels.hoc.position.copy(hocPos).add(V(0, -0.42, 0)); molLabels.hoc.material.opacity = before;
  molLabels.chl.position.copy(A_.N.position).add(V(0, 0.42, 0)); molLabels.chl.material.opacity = after;
  molLabels.wat.position.copy(A_.O.position).add(V(0, -0.36, 0)); molLabels.wat.material.opacity = after;
}

// ------------------------------------------------------------------ per-frame update
function update(t, frame = Math.round(t * FPS)) {
  t = ((t % TOTAL) + TOTAL) % TOTAL;
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  const g = guyAt(t);
  if (window.OVR && window.OVR.p) g.pose = { ...g.pose, ...window.OVR.p };
  const yaw = g.root.yaw || 0;
  applyPose(g.pose, { ...g.root, yaw });
  // feet: planted (stand) or walking (planted-foot cycle along the path)
  const flat = yawQ(yaw);
  if (g.walk) { const { A0, A1, d: wd, lt: wl } = g.walk; const fwd = A1.clone().sub(A0).setY(0).normalize(), side = V(fwd.z, 0, -fwd.x);
    const f = 0.95, L = A1.clone().sub(A0).setY(0).length(), vz = L / wd;
    for (const [S, off, sx] of [['R', 0, -1], ['L', 0.5, 1]]) {
      const cyc = f * wl + off, n = Math.floor(cyc), fr = cyc - n;
      const plant = m => clamp(vz * (m - off + 0.3) / f, 0, L);
      let s, y = 0.102; if (fr < 0.6) s = plant(n); else { const uu = (fr - 0.6) / 0.4; s = lerp(plant(n), plant(n + 1), sm(uu)); y += 0.07 * Math.sin(Math.PI * uu); }
      const ft = A0.clone().setY(y).addScaledVector(fwd, s).addScaledVector(side, 0.11 * sx);
      G.legIK(S, ft, ft.clone().addScaledVector(fwd, 1.0).add(V(0, 0.45, 0)), flat); } }
  else for (const S of ['R', 'L']) { const ft = FEETHOME[S].clone().add(V(0, 0, (g.root.z ?? HOME.z) - HOME.z)); G.legIK(S, ft, ft.clone().add(V(0, 0.45, -1.0)), flat); }
  G.root.updateMatrixWorld(true);
  // hands
  for (const h0 of g.hands) {
    const h = { ...h0 };
    if (h.mouth) { const m = wpos(MOUTH); h.p = m.add(V(0, -0.045, -0.04).applyQuaternion(flat)); h.n = V(0, 0, 1).applyQuaternion(flat); }
    if (h.ear) { const e = wpos(EARR); h.p = e.add(V(0.03, -0.015, -0.02).applyQuaternion(flat)); h.n = V(-1, 0, 0).applyQuaternion(flat); h.u = V(0, 0.85, 0.5).normalize().applyQuaternion(flat); }
    const sol = solveHand(h, 'h' + h.S + b + (h.mouth ? 'm' : h.ear ? 'e' : ''), frame); setArm(h.S, sol.a); LAST['arm' + h.S] = sol.a; LAST['cost' + h.S] = sol.c;
    const pp = {}; curl(pp, h.S, h.c ?? 30); for (const [n, e] of Object.entries(pp)) G.bones[n].quaternion.copy(G.REST[n].q).multiply(qTmp.setFromEuler(eTmp.set(e[0] * D2R, e[1] * D2R, e[2] * D2R)));
  }
  G.root.updateMatrixWorld(true);
  untwistSafe(); G.face(g.face); G.root.updateMatrixWorld(true);
  // props from the hand: the bottle (neck in the palm, nozzle along the fingers), the phone (flat in the palm)
  const handFrame = S => { const hb = G.bones['hand' + S]; hb.updateMatrixWorld(true); const q = hb.getWorldQuaternion(new THREE.Quaternion());
    return { q, p: PALM(S).applyMatrix4(hb.matrixWorld.clone().multiply(new THREE.Matrix4())), u: HANDREST[S].u.clone().applyQuaternion(q), n: HANDREST[S].n.clone().applyQuaternion(q), w: HANDREST[S].w.clone().applyQuaternion(q) }; };
  bottle.visible = g.bottleOn && !(b === 1 || b === 2);
  if (bottle.visible) { const F = handFrame('R'); const yb = F.w.clone().negate(), zb = F.u.clone().sub(yb.clone().multiplyScalar(F.u.dot(yb))).normalize().negate(), xb = new THREE.Vector3().crossVectors(yb, zb);
    bottle.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(xb, yb, zb)); bottle.position.copy(F.p).addScaledVector(F.n, 0.022); }
  phone.visible = g.phoneOn;
  if (phone.visible) { const F = handFrame('R'); const zb = F.n.clone().negate(), yb = F.u.clone().sub(zb.clone().multiplyScalar(F.u.dot(zb))).normalize(), xb = new THREE.Vector3().crossVectors(yb, zb);
    phone.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(xb, yb, zb)); phone.position.copy(F.p).addScaledVector(F.n, 0.012).addScaledVector(F.u, 0.02); }
  // x-ray
  ghost(g.xr); organs.visible = g.xr > 0.02 && b !== 6; headOrg.visible = b === 6;
  const lungLvl = b === 7 ? smooth(0.6, d - 0.3, lt) : 0;
  { const lb = LUNG(1); const chestW = G.bones.chest.getWorldPosition(new THREE.Vector3()).y - 1.3; fluidPlane.constant = chestW + lb.c.y - lb.r.y + 0.002 + lungLvl * 2 * lb.r.y * 0.85; }
  fluids.forEach(f => f.visible = b === 7 && lungLvl > 0.01);
  const sig = b === 6 ? 1 - smooth(1.2, d - 0.6, lt) : 1;
  smellPatch.material.emissiveIntensity = 0.3 + 1.6 * sig;
  pulses.forEach((p, i) => { const ph = ((t * 1.3 + i / 4) % 1); p.position.copy(NERVE.getPoint(ph)); p.material.opacity = sig * (1 - Math.abs(ph - 0.5) * 0.8); p.visible = b === 6; });
  // spray mist from the nozzle
  if (bottle.visible) bottle.updateMatrixWorld(true);
  const nozW = bottle.visible ? NOZZLE.clone().applyMatrix4(bottle.matrixWorld) : V(0, -99, 0), nozD = V(0, 0, -1).applyQuaternion(bottle.quaternion);
  const sprayAge = b === 0 ? lt + 0.35 : b === 9 ? lt - (d - 0.35) : -1;
  const sprayOn = sprayAge >= 0 && (b === 9 || lt < 2.3);
  setCloud(mist, i => { if (!sprayOn) return null; const born = (i / mist.n) * 2.2, a = (b === 0 ? lt + 0.35 : sprayAge) - born; if (a < 0 || a > 0.45 || born > (b === 0 ? 1.9 + 0.35 : 9)) return null;
    const sp = V(hash1(i) - 0.5, hash1(i * 3) - 0.5, hash1(i * 7) - 0.5).multiplyScalar(0.45); const v = nozD.clone().add(sp).normalize().multiplyScalar(1.6 + hash1(i * 5));
    return nozW.clone().addScaledVector(v, a).add(V(0, -1.2 * a * a, 0)); });
  // the gas: rises from the bowl, spreads toward his face; strongest in beats 0, 4, 5
  const gasAmt = b === 0 ? smooth(0.8, 3.2, lt) : b === 4 ? 1 : b === 5 ? 0.8 : b === 3 || b === 6 ? 0.6 : 0;
  gas.m.material.opacity = 0.22 * gasAmt;
  setCloud(gas, i => { if (gasAmt < 0.02 || b === 1 || b === 2 || b === 7 || b === 8) return null; const life = 3.5, a = ((t * 0.9 + hash1(i * 1.3) * life) % life);
    const ang = hash1(i * 2.1) * 6.28, r = 0.05 + a * 0.12;
    return V(TOI.x + Math.cos(ang) * r - 0.08 * a, WATER_Y + 0.1 + a * 0.38, TOI.z + Math.sin(ang) * r * 0.8 + 0.12 * a); });
  // fizz on the water (macro), clouding
  bowlU.uT.value = t; bowlU.uCloud.value = b === 1 ? 0.75 * smooth(0.1, 1.8, lt) : (b === 0 ? 0.25 * smooth(0.6, 3.5, lt) : b === 9 ? 0 : 0.85);
  bowlU.uBlue.value = b === 0 ? smooth(0.1, 1.2, lt) : b === 1 ? 1 - 0.6 * smooth(0.5, 2, lt) : b === 9 ? smooth(d - 0.3, d, lt) * 0.3 : 0.3;
  setCloud(fizz, i => { if (b !== 1 && b !== 0) return null; const a = ((t * 1.7 + hash1(i * 4.3)) % 1); const ang = hash1(i * 2.9) * 6.28, r = Math.sqrt(hash1(i * 5.7)) * 0.15;
    return V(TOI.x + Math.cos(ang) * r, WATER_Y + 0.004 + a * 0.05, TOI.z + Math.sin(ang) * r * 1.25); });
  // gas going in: up the nose and down the airway (x-ray beats)
  setCloud(inhale, i => { if (b !== 3 && b !== 6) return null; const a = ((t * 0.45 + i / inhale.n) % 1);
    const nose = wpos(MOUTH).add(V(0, 0.045, -0.02).applyQuaternion(flat));
    if (b === 6) { if (a < 0.5) return nose.clone().add(V((hash1(i) - 0.5) * 0.06, -0.05 + a * 0.12, -0.12 + a * 0.2).applyQuaternion(flat)); return null; }
    if (a < 0.3) return nose.clone().add(V((hash1(i) - 0.5) * 0.05, 0.0, -0.1 + a * 0.3).applyQuaternion(flat));
    const tt = (a - 0.3) / 0.7; const lp = tt < 0.6 ? AIRWAY.getPoint(tt / 0.6) : BRONCH[i % 2].getPoint((tt - 0.6) / 0.4);
    return lp.applyMatrix4(G.bones.chest.matrixWorld.clone().multiply(new THREE.Matrix4().makeTranslation(0, -1.3, -0.006))); });
  // molecules
  molStage.visible = b === 2; if (b === 2) molecules(t);
  // light: the hallway glows in beat 8 (fresh air)
  hallLight.intensity = b === 8 ? 10 : 2;
  // camera
  const C = camAt(t); camera.position.copy(C.pos); camera.lookAt(C.tgt); camera.fov = C.fov; camera.updateProjectionMatrix();
  const xray = g.xr > 0.5;
  scene.background = new THREE.Color(b === 2 ? 0x0a1220 : xray ? 0x061024 : 0xdfe6ea);
  lamp.intensity = xray ? 1.2 : 9; hemi.intensity = xray ? 0.25 : 0.75; fill.intensity = xray ? 0.2 : 0.9; scene.environmentIntensity = xray ? 0.1 : 0.6;
  const keep = new Set([G.root, inhale.m, camera]);
  for (const o of scene.children) { if (o.isLight) continue; if (o.userData.v0 === undefined) o.userData.v0 = o.visible; if (xray) { if (!keep.has(o)) { if (o.visible) o.userData.hid = true; o.visible = false; } } else if (o.userData.hid) { o.visible = true; o.userData.hid = false; } }
  for (const w of WALLS) w.m.visible = !xray && !w.out(C.pos);
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
// loop seam: frame one's grip is warm-started from the solution at the end of beat 9 (same target), so the arm can't jump at the loop
let SEAM = null;
function primeSeam() { const f0 = Math.round(B[9] * FPS), f1 = Math.round(TOTAL * FPS) - 1; for (let j = f0; j <= f1; j++) update(j / FPS, j); SEAM = MEM['hR9'] ? MEM['hR9'].a.slice() : null; }
function stepTo(i) { const t = i / FPS, b = beatAt(((t % TOTAL) + TOTAL) % TOTAL);
  if (SEAM === null) primeSeam();
  if (i === 0 || (b === 0 && i !== lastFrame + 1)) MEM['hR0'] = { frame: -1, a: SEAM.slice() };
  if (i !== lastFrame + 1) { const f0 = Math.max(0, Math.round(B[b] * FPS)); for (let j = f0; j < i; j++) update(j / FPS, j); }
  update(t, i); lastFrame = i; }
function renderInto(i) { stepTo(i); draw(); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); }
window.renderAll = async (f0, f1) => { for (let i = f0; i < f1; i++) { renderInto(i); await fetch('/frame', { method: 'POST', body: px }); } return 'ok'; };
window.renderAtT = t => { stepTo(Math.round(t * FPS)); if (window.CAM) { camera.position.set(...window.CAM.pos); camera.lookAt(...window.CAM.tgt); camera.fov = window.CAM.fov || 42; camera.updateProjectionMatrix(); } draw(); return renderer.domElement.toDataURL('image/png'); };
window.rigReport = i => { stepTo(i); const t = i / FPS;
  return { t, beat: beatAt(t), ang: LAST, hips: G.bones.hips.getWorldPosition(new THREE.Vector3()).toArray(), car: 0, show: true,
    thumbs: ['R', 'L'].map(S => G.bones['index1' + S].getWorldPosition(new THREE.Vector3()).sub(G.bones['pinky1' + S].getWorldPosition(new THREE.Vector3())).applyQuaternion(G.root.getWorldQuaternion(new THREE.Quaternion()).invert()).toArray()),
    forearms: ['R', 'L'].map(S => G.bones['hand' + S].getWorldPosition(new THREE.Vector3()).sub(G.bones['farm' + S].getWorldPosition(new THREE.Vector3())).normalize().applyQuaternion(G.root.getWorldQuaternion(new THREE.Quaternion()).invert()).toArray()),
    cost: [LAST.costR ?? null, LAST.costL ?? null] }; };
window.phoneDbg = t => { stepTo(Math.round(t * FPS)); const q = G.root.getWorldQuaternion(new THREE.Quaternion()).invert(); const hb = G.bones.handR, hq = hb.getWorldQuaternion(new THREE.Quaternion());
  const f = v => v.clone().applyQuaternion(hq).applyQuaternion(q).toArray().map(x => +x.toFixed(2)); return { u: f(HANDREST.R.u), n: f(HANDREST.R.n), w: f(HANDREST.R.w), cost: LAST.costR, arm: LAST.armR.map(x => +x.toFixed(0)) }; };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS);
window.READY = true;
