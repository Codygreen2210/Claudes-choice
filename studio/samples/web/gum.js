// "What happens if you swallow gum" - a 3D Short with the sculpted, skinned guy (bathroom set from bath.js).
//   gum.html?w=1080&h=1920            (times from gum/times.json; one shot per narration line)
// Beats: 0 x-ray: the swallow (hook) | 1 the 7-year myth: he rubs his belly | 2 x-ray: acid strips the color | 3 stage: rubber, acid bounces off
//        4 x-ray: through the coiled gut | 5 the calendar flips, the toilet swirls | 6 endoscope: a clean stomach | 7 stage: a gum ball stuck in a gut
//        8 holds up a pack | 9 a new stick, chew, swallow -> fades into frame one's x-ray (loop)
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
const TIMES = await (await fetch('/gum/times.json')).json();
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

// ------------------------------------------------------------------ props: a stick of gum, the pack, a wall calendar
const gumPink = new THREE.MeshStandardMaterial({ color: 0xff7ab0, roughness: 0.45 });
const stick = new THREE.Mesh(new RoundedBoxGeometry(0.072, 0.02, 0.004, 2, 0.0015), gumPink); stick.castShadow = true; scene.add(stick);
const pack = new THREE.Group(); scene.add(pack);
{ const lab = canvasTex(256, 128, g => { g.fillStyle = '#21b07a'; g.fillRect(0, 0, 256, 128); g.fillStyle = '#fff'; g.font = 'bold 64px Inter, Arial'; g.textAlign = 'center'; g.fillText('GUM', 128, 86); });
  const m = new THREE.MeshStandardMaterial({ color: 0x21b07a, roughness: 0.5 }), f = new THREE.MeshStandardMaterial({ map: lab, roughness: 0.5 });
  const b = new THREE.Mesh(new RoundedBoxGeometry(0.08, 0.05, 0.02, 2, 0.004), [m, m, m, m, f, m]); b.castShadow = true; pack.add(b); }
const calCan = document.createElement('canvas'); calCan.width = 256; calCan.height = 300; const calTex = new THREE.CanvasTexture(calCan); calTex.colorSpace = THREE.SRGBColorSpace;
let calKey = '';
function drawCal(day) { if (day === calKey) return; calKey = day; const g = calCan.getContext('2d');
  g.fillStyle = '#ffffff'; g.fillRect(0, 0, 256, 300); g.fillStyle = '#d23a3a'; g.fillRect(0, 0, 256, 80);
  g.fillStyle = '#fff'; g.font = 'bold 54px Inter, Arial'; g.textAlign = 'center'; g.fillText(day, 128, 60);
  g.fillStyle = '#222'; g.font = 'bold 120px Inter, Arial'; g.fillText({ MON: '1', TUE: '2', WED: '3', THU: '4' }[day] || '1', 128, 230); calTex.needsUpdate = true; }
drawCal('MON');
const cal = new THREE.Mesh(new THREE.PlaneGeometry(0.26, 0.3), new THREE.MeshStandardMaterial({ map: calTex, roughness: 0.8 })); cal.position.set(0.82, 1.42, RZ0 + 0.005); scene.add(cal);
const calPage = new THREE.Mesh(new THREE.PlaneGeometry(0.26, 0.3).translate(0, -0.15, 0), new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.8, side: THREE.DoubleSide })); calPage.position.set(0.82, 1.57, RZ0 + 0.008); scene.add(calPage);

// ------------------------------------------------------------------ dark stages far from the room: the gum up close (beat 3), the endoscope (beat 6), the stuck gum ball (beat 7)
function stage(pos, top, bot) { const g = new THREE.Group(); g.position.copy(pos); scene.add(g);
  const bg = new THREE.Mesh(new THREE.SphereGeometry(8, 32, 16), new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false,
    vertexShader: 'varying vec3 vD; void main(){ vD = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
    fragmentShader: `varying vec3 vD; void main(){ float h = vD.y * 0.5 + 0.5; vec3 c = mix(vec3(${bot.join(',')}), vec3(${top.join(',')}), h); gl_FragColor = vec4(pow(c, vec3(2.2)) * 2.5, 1.0); }` }));
  g.add(bg); const k = new THREE.DirectionalLight(0xffffff, 2.4); k.position.set(-1, 2, -3); g.add(k); g.add(k.target); const r = new THREE.PointLight(0x9fd0ff, 3, 6); r.position.set(1.5, -0.5, 1); g.add(r); return g; }
// gum blob geometry: a lumpy chewed wad
function blobGeo(r, seed) { const g = new THREE.SphereGeometry(r, 64, 48), p = g.attributes.position;
  for (let i = 0; i < p.count; i++) { const v = V(p.getX(i), p.getY(i), p.getZ(i)); const n = v.clone().normalize();
    const d = 1 + 0.12 * Math.sin(n.x * 5 + seed) * Math.sin(n.y * 4 + seed * 2) + 0.06 * Math.sin(n.z * 9 + seed * 3); v.copy(n.multiplyScalar(r * d)); v.y *= 0.8; p.setXYZ(i, v.x, v.y, v.z); }
  g.computeVertexNormals(); return g; }
const GUMSTAGE = V(-400, 0, 0);
const gumStage = stage(GUMSTAGE, [0.12, 0.3, 0.12], [0.02, 0.06, 0.03]);
const bigGumMat = new THREE.MeshPhysicalMaterial({ color: 0xc9a3b2, roughness: 0.5, clearcoat: 0.4, sheen: 0.5, sheenColor: new THREE.Color(0xffd0e0) });
const bigGum = new THREE.Mesh(blobGeo(0.32, 1.3), bigGumMat); gumStage.add(bigGum);
const acidDrops = new THREE.InstancedMesh(new THREE.SphereGeometry(1, 16, 12), new THREE.MeshStandardMaterial({ color: 0xb8ff4a, emissive: 0x5a9a10, emissiveIntensity: 0.8, transparent: true, opacity: 0.85 }), 40); gumStage.add(acidDrops);
const ENDO = V(0, 0, 400);
const endoStage = new THREE.Group(); endoStage.position.copy(ENDO); scene.add(endoStage);
const wallU = { uT: { value: 0 } };
const stomachWall = new THREE.Mesh(new THREE.SphereGeometry(1.6, 64, 48).scale(1, 0.8, 1.8), new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.25, side: THREE.BackSide }));
stomachWall.material.onBeforeCompile = sh => { Object.assign(sh.uniforms, wallU);
  sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vO;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvO = position;');
  sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vO; uniform float uT;')
    .replace('#include <color_fragment>', `#include <color_fragment>
  { float fold = 0.5 + 0.5 * sin(vO.z * 9.0 + sin(vO.x * 4.0) * 1.5 + sin(vO.y * 6.0) * 0.8);
    diffuseColor.rgb = mix(vec3(0.55, 0.16, 0.2), vec3(0.98, 0.55, 0.55), smoothstep(0.25, 0.85, fold)); }`)
    .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
  { vec3 gr = vec3(cos(vO.z * 9.0 + sin(vO.x * 4.0) * 1.5) * 0.35, 0.0, sin(vO.x * 7.0 + vO.z * 3.0) * 0.2);
    normal = normalize(normal + (viewMatrix * vec4(gr, 0.0)).xyz); }`); };
endoStage.add(stomachWall);
const endoLight = new THREE.SpotLight(0xfff2e6, 40, 6, 0.75, 0.6, 1.2); endoStage.add(endoLight); endoStage.add(endoLight.target);
const vign = new THREE.Mesh(new THREE.RingGeometry(0.135, 3, 96), new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.94, depthTest: false }));
vign.position.set(0, 0, -0.5); vign.renderOrder = 30; camera.add(vign); scene.add(camera); vign.visible = false;
const KIDS = V(0, 0, -400);
const kidStage = stage(KIDS, [0.04, 0.08, 0.2], [0.01, 0.02, 0.06]);

// ------------------------------------------------------------------ the gut (rest space): esophagus, stomach, small intestine coil, colon
const tubeMat = (c, op) => new THREE.MeshPhysicalMaterial({ color: c, emissive: c, emissiveIntensity: 0.3, roughness: 0.35, clearcoat: 0.6, transparent: true, opacity: op, depthWrite: false });
const ESO = new THREE.CatmullRomCurve3([V(0, 1.565, -0.075), V(0, 1.54, -0.04), V(0, 1.47, -0.02), V(0.0, 1.38, -0.01), V(0.004, 1.3, -0.005), V(0.005, 1.27, 0.0)]);
const ST_CURVE = new THREE.CatmullRomCurve3([V(0.005, 1.27, 0.0), V(-0.02, 1.235, -0.02), V(-0.06, 1.19, -0.035), V(-0.07, 1.13, -0.04), V(-0.04, 1.085, -0.045), V(0.01, 1.08, -0.04), V(0.05, 1.1, -0.035)]);
const stRad = k => 0.035 * (1 + 0.75 * Math.sin(Math.PI * clamp((k / 60 - 0.12) / 0.7, 0, 1)));
function stomachGeo(rf) { const ST_PTS = ST_CURVE.getSpacedPoints(60), fr = ST_CURVE.computeFrenetFrames(60, false), seg = 28, pos = [], idx = [];
  for (let k = 0; k <= 60; k++) { const c = ST_PTS[k], r = stRad(k) * rf;
    for (let j = 0; j <= seg; j++) { const a = j / seg * Math.PI * 2; const v = c.clone().addScaledVector(fr.normals[k], Math.cos(a) * r).addScaledVector(fr.binormals[k], Math.sin(a) * r); pos.push(v.x, v.y, v.z); } }
  for (let k = 0; k < 60; k++) for (let j = 0; j < seg; j++) { const a = k * (seg + 1) + j, b = a + seg + 1; idx.push(a, b, a + 1, b, b + 1, a + 1); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setIndex(idx); g.computeVertexNormals(); return g; }
const SI_PTS = [V(0.05, 1.1, -0.035), V(0.07, 1.075, -0.045)];
for (let r = 0; r < 6; r++) { const y = 1.06 - r * 0.026, dir = r % 2 ? 1 : -1;
  for (let k = 0; k <= 4; k++) SI_PTS.push(V(dir * (0.075 - k * 0.0375), y + 0.006 * Math.sin(k * 2.1 + r), -0.05 + 0.012 * Math.sin(k * 1.7 + r * 0.9))); }
SI_PTS.push(V(0.075, 0.9, -0.045));
const SI = new THREE.CatmullRomCurve3(SI_PTS);
const COLON = new THREE.CatmullRomCurve3([V(0.075, 0.9, -0.045), V(0.105, 0.93, -0.035), V(0.11, 1.0, -0.03), V(0.105, 1.08, -0.035), V(0.0, 1.095, -0.05), V(-0.105, 1.08, -0.035), V(-0.11, 1.0, -0.03), V(-0.09, 0.92, -0.03), V(-0.02, 0.88, -0.02), V(0.0, 0.84, 0.0)]);
const PATH = [ESO, ST_CURVE, SI, COLON];
function gutGroup() { const g = new THREE.Group();
  g.add(new THREE.Mesh(new THREE.TubeGeometry(ESO, 40, 0.009, 12, false), tubeMat(0xe98a9a, 0.55)));
  g.add(new THREE.Mesh(stomachGeo(1), tubeMat(0xf08a8a, 0.4)));
  g.add(new THREE.Mesh(new THREE.TubeGeometry(SI, 400, 0.0085, 10, false), tubeMat(0xf5a3a8, 0.45)));
  g.add(new THREE.Mesh(new THREE.TubeGeometry(COLON, 160, 0.017, 14, false), tubeMat(0xd99a7a, 0.4)));
  g.traverse(o => { if (o.isMesh) o.renderOrder = 5; }); return g; }
const gut = gutGroup();
const acidMesh = new THREE.Mesh(stomachGeo(0.86), new THREE.MeshStandardMaterial({ color: 0xb8ff4a, emissive: 0x5a9a10, emissiveIntensity: 0.8, transparent: true, opacity: 0.55, depthWrite: false, clippingPlanes: [new THREE.Plane(V(0, -1, 0), 1.115)] }));
gut.add(acidMesh);
const gumWad = new THREE.Mesh(blobGeo(0.011, 2.1), new THREE.MeshStandardMaterial({ color: 0xff6fa8, emissive: 0xff3a8a, emissiveIntensity: 0.6, roughness: 0.4 })); gumWad.renderOrder = 7; gut.add(gumWad);
// beat 7: the gut on its own (bigger), with a big gum ball blocking it and food piling up behind
const kidGut = gutGroup(); kidGut.scale.setScalar(3.2); kidGut.position.set(0, -3.2, 0); kidStage.add(kidGut);
const BALL_U = 0.62;
const bigBall = new THREE.Mesh(blobGeo(0.03, 4.4), new THREE.MeshStandardMaterial({ color: 0xff7ab0, emissive: 0xff3a8a, emissiveIntensity: 0.5, roughness: 0.4 })); bigBall.position.copy(SI.getPoint(BALL_U)); kidGut.add(bigBall);
const backlog = new THREE.InstancedMesh(new THREE.SphereGeometry(1, 10, 8), new THREE.MeshStandardMaterial({ color: 0x8a5a3a, roughness: 0.8 }), 24); kidGut.add(backlog);

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
  const seeds = prev ? [prev] : [...(tg.seed ? [tg.seed.concat([0, 0, 0, 0, 0, 0, 0]).slice(0, 7)] : []), A(40, 15, 0, 80, 0), A(60, 25, 20, 60, 40), A(30, 40, -20, 100, -30), A(80, 10, 0, 110, 60), A(50, 30, 30, 40, 70), A(20, 20, -30, 120, -60)];
  let best = null;
  for (const s0 of seeds) {
    let a = s0.map((v, i) => clamp(v, ARM_LIM[i][0], ARM_LIM[i][1])), ca = cost(a);
    for (let step = prev ? 4 : 16; step >= 0.25; step /= 2) { let imp = true, g = 0;
      while (imp && g++ < 10) { imp = false; for (let i = 0; i < 7; i++) for (const sg of [1, -1]) { const b = a.slice(); b[i] = clamp(b[i] + sg * step, ARM_LIM[i][0], ARM_LIM[i][1]); const cb = cost(b); if (cb < ca - 1e-9) { a = b; ca = cb; imp = true; } } } }
    if (!best || ca < best.c) best = { a, c: ca };
  }
  MEM[key] = { frame, a: best.a }; return best;
}


attach(gut, 'chest'); gut.visible = false; G.reset();
const MOUTH = new THREE.Object3D(); MOUTH.position.set(0, G.man.mouthY, G.man.mouthZ); attach(MOUTH, 'head');
const BELLY = new THREE.Object3D(); BELLY.position.set(0.0, 1.08, -0.14); attach(BELLY, 'spine1');
G.reset();
const wpos = o => o.getWorldPosition(new THREE.Vector3());
// where his right palm sits in the plain standing pose (the hand-to-mouth move starts and ends exactly there, so it hands off to the pose cleanly)
let STAND_R;
{ applyPose(P.stand, {}); for (const S of ['R', 'L']) G.legIK(S, V(...(S === 'R' ? [0.16, 0.102, -0.3] : [-0.08, 0.102, -0.26])), V(0, 0.55, -1.3), new THREE.Quaternion()); G.root.updateMatrixWorld(true);
  const f = handFK('R', eul(P.stand, 'armR')); STAND_R = { p: f.p.clone(), n: f.n.clone(), u: f.u.clone() }; G.reset(); }
// gum position along the gut: s in [0,4) walks esophagus, stomach, small intestine, colon
function gutPt(s) { const i = clamp(Math.floor(s), 0, 3); return PATH[i].getPoint(clamp(s - i, 0, 1)); }

// ------------------------------------------------------------------ the story
function blink(t) { for (const b0 of [1.9, 5.2, 10.3, 20.1, 28.6, 31.0]) { const u = (t - b0) / 0.16; if (u > 0 && u < 1) return Math.sin(Math.PI * u); } return 0; }
const yawQ = deg => new THREE.Quaternion().setFromAxisAngle(V(0, 1, 0), deg * D2R);
const FEETHOME = { R: V(0.16, 0.102, -0.3), L: V(-0.08, 0.102, -0.26) };
let PEAK_R = null;
const XFADE = 0.45;                                               // beat 9's last XFADE seconds fade into the frame-one x-ray
function guyAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  let pose = P.stand, face = { blink: blink(t) }, hands = [], xr = 0, show = true, gumS = null, gumCol = 0, stickAt = null, packOn = false;
  if (b === 0) {                                                   // x-ray: the swallow; the wad slides down the esophagus into the stomach
    xr = 1; const u = lt / d; gumS = 1.0 * (1 - Math.pow(1 - smooth(0, 0.92, u), 1.6)) + 0.12 * smooth(0.92, 1, u);
    pose = addPose(P.stand, { neck: [-6 * Math.sin(Math.PI * smooth(0, 0.4, u)), 0, 0] });
    face = { ...face, jaw: 0.0, press: 0.6 * (1 - smooth(0.2, 0.6, u)), oh: 0.3 * smooth(0.5, 0.8, u), brow: 0.4 * smooth(0.5, 0.8, u) };
  } else if (b === 1) {                                            // the myth: he looks down at his belly, rubs it, worried
    pose = addPose(P.stand, { neck: [-20, 0, 0], head: [-10, 0, 0], spine1: [-4, 0, 0] });
    hands = [{ S: 'L', belly: true, c: 20 }];
    face = { ...face, fear: 0.5, browIn: 0.8, frown: 0.4, look: [0, -0.7] };
  } else if (b === 2) { xr = 1; gumS = 1.42 + 0.12 * smooth(0, d, lt); gumCol = smooth(0.4, d - 0.3, lt);        // x-ray: in the stomach's acid, fading
  } else if (b === 4) { xr = 1; gumS = 2.0 + smooth(0.05, d, lt) * 1.0; gumCol = 1;                              // x-ray: riding through the coil
  } else if (b === 8) {                                            // holds up the pack
    pose = addPose(P.stand, { neck: [-6, 0, 0] }); packOn = true;
    hands = [{ S: 'R', p: V(0.14, 1.22, -0.58), n: V(0, 1, 0), u: V(-0.4, 0, -1).normalize(), c: 15, pack: true }];
    face = { ...face, brow: 0.5, smile: 0.3, look: [0.2, -0.3] };
  } else if (b === 9) {                                            // a new stick: up to his mouth, in, chew, swallow (fades into frame one's x-ray)
    const up = smooth(0.1, 0.8, lt), inMouth = lt > 0.85;
    if (lt < 1.05) hands = [{ S: 'R', mouth: true, k: up, c: 40 }];
    else if (PEAK_R) pose = { ...pose, armR: PEAK_R.map((v, i) => lerp(v, eul(P.stand, 'armR')[i] ?? 0, smooth(1.05, 1.5, lt))) };   // the arm eases back down from where the reach ended
    if (!inMouth) stickAt = 'hand';
    const chew = lt > 0.9 && lt < d - 0.55 ? Math.max(0, Math.sin(2 * Math.PI * 1.9 * lt)) : 0;
    face = { ...face, jaw: 0.18 * chew + (lt < 0.85 ? 0.22 * smooth(0.5, 0.8, lt) : 0), smile: 0.25, press: 0.5 * smooth(d - 0.55, d - 0.3, lt), look: [0.2, -0.2] };
    xr = smooth(d - XFADE, d, lt); if (xr > 0.01) gumS = 0;
  } else { show = b !== 3 && b !== 5 && b !== 6 && b !== 7; }
  return { pose, face, hands, xr, show, gumS, gumCol, stickAt, packOn };
}

// ------------------------------------------------------------------ cameras
const XCAM = { pos: V(0.46, 1.44, -0.92), tgt: V(0.02, 1.4, -0.3), fov: 36 };
function shake(t, a, f = 1) { return V(vn1(t * 3 * f, 1) * a, vn1(t * 3 * f, 2) * a, vn1(t * 3 * f, 3) * a * 0.5); }
function camAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b], u = lt / d;
  let pos, tgt, fov = 42;
  if (b === 0) { const k = smooth(0.2, 1, u); pos = XCAM.pos.clone().lerp(V(0.36, 1.32, -0.86), k); tgt = XCAM.tgt.clone().lerp(V(0.01, 1.25, -0.31), k); fov = XCAM.fov; }
  else if (b === 1) { pos = V(0.95 - 0.1 * u, 1.5, -1.75); tgt = V(0.06, 1.15, -0.32); fov = 40; }
  else if (b === 2) { pos = V(0.26 - 0.05 * u, 1.22, -0.82 + 0.05 * u); tgt = V(0.0, 1.16, -0.32); fov = 32; }
  else if (b === 3) { const a = 0.6 + 0.5 * u; pos = GUMSTAGE.clone().add(V(Math.sin(a) * 1.3, 0.25, -Math.cos(a) * 1.3)); tgt = GUMSTAGE.clone(); fov = 40; }
  else if (b === 4) { pos = V(0.28 - 0.04 * u, 1.04, -0.9 + 0.06 * u); tgt = V(0.03, 0.99, -0.33); fov = 34; }
  else if (b === 5) { const w = smooth(0.52, 0.7, u); pos = V(0.2, 1.45, -0.25).lerp(V(0.0, 1.45, -0.1), w); tgt = V(0.78, 1.38, -1.2).lerp(V(0.38, 0.4, -0.86), w); fov = lerp(40, 50, w); }
  else if (b === 6) { pos = ENDO.clone().add(V(0.05 * Math.sin(lt * 0.9), -0.1 + 0.05 * Math.sin(lt * 0.7), -2.1 + 1.8 * smooth(0, d, lt))); tgt = pos.clone().add(V(0.15 * Math.sin(lt * 0.5), -0.05, 1)); fov = 60; }
  else if (b === 7) { pos = KIDS.clone().add(V(0.5 - 0.15 * u, 0.15, -1.45 + 0.15 * u)); tgt = KIDS.clone().add(bigBall.position.clone().multiplyScalar(3.2).add(V(0, -3.2, 0))).lerp(KIDS, 0.25); fov = 40; }
  else if (b === 8) { pos = V(0.75 - 0.08 * u, 1.48, -1.45); tgt = V(0.08, 1.28, -0.4); fov = 40; }
  else { const w = smooth(d - XFADE - 0.35, d, lt); pos = V(0.62, 1.55, -1.2).lerp(XCAM.pos, w); tgt = V(0.04, 1.5, -0.3).lerp(XCAM.tgt, w); fov = lerp(38, XCAM.fov, w); }
  const punch = b > 0 ? (1 - smooth(0, 0.22, lt)) * 0.07 : 0;
  return { pos, tgt, fov: fov * (1 - punch) };
}

// ------------------------------------------------------------------ per-frame update
function update(t, frame = Math.round(t * FPS)) {
  t = ((t % TOTAL) + TOTAL) % TOTAL;
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  const g = guyAt(t);
  if (window.OVR && window.OVR.p) g.pose = { ...g.pose, ...window.OVR.p };
  applyPose(g.pose, {});
  const flat = yawQ(0);
  for (const S of ['R', 'L']) { const ft = FEETHOME[S].clone(); G.legIK(S, ft, ft.clone().add(V(0, 0.45, -1.0)), flat); }
  G.root.updateMatrixWorld(true);
  for (const h0 of g.hands) { const h = { ...h0 };
    if (h.belly) { const p = wpos(BELLY); h.p = p.add(V(0.02 + 0.02 * Math.sin(t * 5), 0.01 * Math.cos(t * 5), -0.03)); h.n = V(0, 0, 1); }
    if (h.mouth) { const m = wpos(MOUTH); const at = m.clone().add(V(0.0, -0.035, -0.095)); h.p = STAND_R.p.clone().lerp(at, h.k); h.n = STAND_R.n.clone().lerp(V(-0.6, 0.2, 0.75).normalize(), h.k).normalize(); if (h.k < 0.02) h.u = STAND_R.u; h.seed = eul(P.stand, 'armR'); }
    const sol = solveHand(h, 'h' + h.S + b + (h.mouth ? 'm' : h.belly ? 'b' : ''), frame); setArm(h.S, sol.a); if (h.mouth) PEAK_R = sol.a.slice(); LAST['arm' + h.S] = sol.a; LAST['cost' + h.S] = sol.c;
    const pp = {}; curl(pp, h.S, h.c ?? 30); for (const [n, e] of Object.entries(pp)) G.bones[n].quaternion.copy(G.REST[n].q).multiply(qTmp.setFromEuler(eTmp.set(e[0] * D2R, e[1] * D2R, e[2] * D2R)));
  }
  G.root.updateMatrixWorld(true);
  untwistSafe(); G.face(g.face); G.root.visible = g.show; G.root.updateMatrixWorld(true);
  const handFrame = S => { const hb = G.bones['hand' + S]; hb.updateMatrixWorld(true); const q = hb.getWorldQuaternion(new THREE.Quaternion());
    return { q, p: PALM(S).applyMatrix4(hb.matrixWorld), u: HANDREST[S].u.clone().applyQuaternion(q), n: HANDREST[S].n.clone().applyQuaternion(q), w: HANDREST[S].w.clone().applyQuaternion(q) }; };
  // the stick rides in his fingertips (beat 9), the pack lies on his palm (beat 8)
  stick.visible = g.stickAt === 'hand';
  if (stick.visible) { const F = handFrame('R'); const xb = F.u.clone(), zb = F.n.clone(), yb = new THREE.Vector3().crossVectors(zb, xb);
    stick.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(xb, yb, zb)); stick.position.copy(F.p).addScaledVector(F.u, 0.065).addScaledVector(F.n, 0.012); }
  pack.visible = g.packOn;
  if (pack.visible) { const F = handFrame('R'); const yb = F.u.clone(), zb = F.n.clone(), xb = new THREE.Vector3().crossVectors(yb, zb);
    pack.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(xb, yb, zb)); pack.position.copy(F.p).addScaledVector(F.n, 0.016); }
  // x-ray: the gut and the wad
  ghost(g.xr); gut.visible = g.xr > 0.02;
  gumWad.visible = g.gumS !== null && g.xr > 0.02;
  if (gumWad.visible) { gumWad.position.copy(gutPt(g.gumS)); gumWad.material.color.setHex(0xff6fa8).lerp(new THREE.Color(0x9a9a96), g.gumCol); gumWad.material.emissive.setHex(0xff3a8a).lerp(new THREE.Color(0x202020), g.gumCol); gumWad.rotation.set(t * 1.3, t * 0.7, 0); }
  acidMesh.visible = b === 2 || b === 0;
  // stages
  gumStage.visible = b === 3; endoStage.visible = b === 6; kidStage.visible = b === 7; vign.visible = b === 6;
  if (b === 3) { const s = 1 + 0.06 * Math.sin(lt * 5); bigGum.scale.set(s, 1 / Math.sqrt(s), s); bigGum.rotation.y = lt * 0.4;
    const m4 = new THREE.Matrix4(); for (let i = 0; i < 40; i++) { const ph = ((lt * 0.8 + hash1(i * 1.7)) % 1), ang = hash1(i * 3.1) * 6.28, el = (hash1(i * 5.3) - 0.5) * 2.2;
      const dir = V(Math.cos(ang) * Math.cos(el), Math.sin(el), Math.sin(ang) * Math.cos(el)); const r = 0.36 + 0.9 * Math.abs(1 - 2 * ph);      // in, bounce off, out
      m4.compose(dir.multiplyScalar(r), new THREE.Quaternion(), V(1, 1, 1).multiplyScalar(0.025 + 0.02 * hash1(i))); acidDrops.setMatrixAt(i, m4); } acidDrops.instanceMatrix.needsUpdate = true; }
  if (b === 6) { wallU.uT.value = t; }
  if (b === 7) { const k = smooth(0.3, d * 0.7, lt); const m4 = new THREE.Matrix4();
    for (let i = 0; i < 24; i++) { const p = SI.getPoint(clamp(BALL_U - 0.012 - i * 0.004, 0, 1)); const s = 0.007 * k * (0.7 + 0.5 * hash1(i)); m4.compose(p, new THREE.Quaternion(), V(s, s, s)); backlog.setMatrixAt(i, m4); }
    backlog.instanceMatrix.needsUpdate = true; bigBall.scale.setScalar(0.85 + 0.15 * smooth(0, 1, lt) + 0.03 * Math.sin(lt * 3)); kidGut.rotation.y = 0.15 * Math.sin(lt * 0.4); }
  // calendar flips MON -> WED, then the toilet swirls (beat 5)
  if (b === 5) { const day = Math.min(2, Math.floor(lt / (d * 0.6) * 3)); drawCal(['MON', 'TUE', 'WED'][day]); const f = (lt / (d * 0.6) * 3) % 1; calPage.visible = lt < d * 0.6 && day < 2; calPage.rotation.x = -Math.PI * smooth(0, 0.6, f) * 0.95; }
  else { drawCal('MON'); calPage.visible = false; }
  bowlU.uT.value = b === 5 ? t + 6 * smooth(d * 0.6, d, lt) * (lt - d * 0.6) : t; bowlU.uCloud.value = 0; bowlU.uBlue.value = b === 5 ? 0.6 * smooth(d * 0.6, d * 0.8, lt) : 0;
  // camera + x-ray look
  const C = camAt(t); camera.position.copy(C.pos); camera.lookAt(C.tgt); camera.fov = C.fov; camera.updateProjectionMatrix();
  if (b === 6) { endoLight.position.copy(C.pos).sub(ENDO); endoLight.target.position.copy(C.tgt).sub(ENDO); endoLight.target.updateMatrixWorld(); }
  const xray = g.xr > 0.5 && (b === 0 || b === 2 || b === 4 || b === 9);
  const onStage = b === 3 || b === 6 || b === 7;
  scene.background = new THREE.Color(xray || onStage ? 0x061024 : 0xdfe6ea);
  lamp.intensity = xray ? 1.2 : 9; hemi.intensity = xray ? 0.25 : 0.75; fill.intensity = xray ? 0.2 : 0.9; scene.environmentIntensity = xray ? 0.1 : 0.6;
  const keep = new Set([G.root, camera, gumStage, endoStage, kidStage]);
  for (const o of scene.children) { if (o.isLight) continue; if (xray || onStage) { if (!keep.has(o)) { if (o.visible) o.userData.hid = true; o.visible = false; } } else if (o.userData.hid) { o.visible = true; o.userData.hid = false; } }
  if (!xray && !onStage) { for (const w of WALLS) w.m.visible = !w.out(C.pos); stick.visible = g.stickAt === 'hand'; pack.visible = g.packOn; calPage.visible = calPage.visible && b === 5; }
  if (onStage) G.root.visible = false;
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
function stepTo(i) { const t = i / FPS, b = beatAt(((t % TOTAL) + TOTAL) % TOTAL);
  if (i !== lastFrame + 1) { const f0 = Math.max(0, Math.round(B[b] * FPS)); for (let j = f0; j < i; j++) update(j / FPS, j); }
  update(t, i); lastFrame = i; }
function renderInto(i) { stepTo(i); draw(); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); }
window.renderAll = async (f0, f1) => { for (let i = f0; i < f1; i++) { renderInto(i); await fetch('/frame', { method: 'POST', body: px }); } return 'ok'; };
window.renderAtT = t => { stepTo(Math.round(t * FPS)); if (window.CAM) { camera.position.set(...window.CAM.pos); camera.lookAt(...window.CAM.tgt); camera.fov = window.CAM.fov || 42; camera.updateProjectionMatrix(); } draw(); return renderer.domElement.toDataURL('image/png'); };
window.rigReport = i => { stepTo(i); const t = i / FPS;
  return { t, beat: beatAt(t), ang: LAST, hips: G.bones.hips.getWorldPosition(new THREE.Vector3()).toArray(), car: 0, show: G.root.visible,
    thumbs: ['R', 'L'].map(S => G.bones['index1' + S].getWorldPosition(new THREE.Vector3()).sub(G.bones['pinky1' + S].getWorldPosition(new THREE.Vector3())).applyQuaternion(G.root.getWorldQuaternion(new THREE.Quaternion()).invert()).toArray()),
    forearms: ['R', 'L'].map(S => G.bones['hand' + S].getWorldPosition(new THREE.Vector3()).sub(G.bones['farm' + S].getWorldPosition(new THREE.Vector3())).normalize().applyQuaternion(G.root.getWorldQuaternion(new THREE.Quaternion()).invert()).toArray()),
    cost: [LAST.costR ?? null, LAST.costL ?? null] }; };
window.dbgHand = (i) => { stepTo(i); const f = handFK('R', LAST.armR); return { c: LAST.costR, p: f.p.toArray().map(x => +x.toFixed(3)), n: f.n.toArray().map(x => +x.toFixed(2)), a: LAST.armR.map(x => +x.toFixed(0)) }; };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS);
window.READY = true;
