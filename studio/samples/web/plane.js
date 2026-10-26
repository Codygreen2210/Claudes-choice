// "Your plane is going down. Here's what you do" - a 3D Short with the sculpted, skinned guy in an airliner.
//   plane.html?w=1080&h=1920            (times from plane/times.json; one shot per narration line)
// Beats: 0 the bang: cabin lurching, things floating, he grips the armrests (hook) | 1 masks drop, he puts his on
//        2 pulls the lap belt low and tight | 3 brace: feet flat, head and arms against the seat in front
//        4 outside: the jet belly-lands in a field (the hit), then inside: braced while the cabin shakes
//        5 smoke fills the cabin from the top; he gets low in the aisle | 6 crouch-walks, counting rows by touch, to the EXIT
//        7 drops his bag at the door, rides the slide, runs from the jet | 8 dark stage: 100 people, 95 light up
//        9 back in his seat before it happened; ends on frame one
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
const TIMES = await (await fetch('/plane/times.json')).json();
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

// ------------------------------------------------------------------ the cabin (interior set at the origin; the nose is toward -z, his row is at z = 0)
// Narrow-body economy: 3 + 3 seats, 0.79 m pitch, aisle |x| < 0.26, floor y = 0, the fuselage wall a cylinder (r 1.95) centred at y 0.75.
const CABIN = new THREE.Group(); scene.add(CABIN);
const PITCH = 0.79, ROWS = [-6, -5, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8];          // row k sits at z = -k * PITCH ... see rowZ()
const rowZ = k => -k * PITCH;                                                  // row 0 = his row; rows 1..4 ahead of him, then the door zone
const DOORZ = -4.35;                                                           // the left front exit door (no seats from -3.75 to -4.95)
const SEATX = [-1.43, -0.96, -0.49, 0.49, 0.96, 1.43];
const ME = { x: -0.49, row: 0 };                                               // his seat: left aisle seat
const R0 = 1.95, CY = 0.75;
const wallX = y => Math.sqrt(Math.max(0, R0 * R0 - (y - CY) * (y - CY)));
const cabinMat = (c, r = 0.7) => new THREE.MeshStandardMaterial({ color: c, roughness: r });
const panelMat = cabinMat(0xe9e7e2, 0.6), binMat = cabinMat(0xf3f2ee, 0.45), carpet = cabinMat(0x3c4250, 0.95), seatMat = cabinMat(0x24346a, 0.85),
  seatDark = cabinMat(0x1a1d24, 0.7), armMat = cabinMat(0x2b2d33, 0.5);
const cbox = (w, h, d, x, y, z, m, r = 0.02, parent = CABIN) => { const o = new THREE.Mesh(r > 0 ? new RoundedBoxGeometry(w, h, d, 2, Math.min(r, 0.4 * Math.min(w, h, d))) : new THREE.BoxGeometry(w, h, d), m); o.position.set(x, y, z); o.castShadow = true; o.receiveShadow = true; parent.add(o); return o; };
const ZF = -9.5, ZB = 7.5;                                                     // cabin front/back (we never see the ends: dark fog / bulkheads)
{ const fl = new THREE.Mesh(new THREE.PlaneGeometry(3.6, ZB - ZF).rotateX(-Math.PI / 2), carpet); fl.position.set(0, 0, (ZF + ZB) / 2); fl.receiveShadow = true; CABIN.add(fl);
  const aisle = new THREE.Mesh(new THREE.PlaneGeometry(0.5, ZB - ZF).rotateX(-Math.PI / 2), cabinMat(0x4a3e3a, 0.95)); aisle.position.set(0, 0.002, (ZF + ZB) / 2); CABIN.add(aisle);
  const wall = new THREE.Mesh(new THREE.CylinderGeometry(R0, R0, ZB - ZF, 64, 1, true).rotateX(Math.PI / 2), panelMat); wall.material.side = THREE.BackSide; wall.position.set(0, CY, (ZF + ZB) / 2); wall.receiveShadow = true; CABIN.add(wall);
  cbox(3.2, 0.06, ZB - ZF, 0, 2.2, (ZF + ZB) / 2, panelMat, 0);              // ceiling between the bins
  cbox(3.9, 2.8, 0.1, 0, 1.2, ZF, panelMat, 0); cbox(3.9, 2.8, 0.1, 0, 1.2, ZB, panelMat, 0); }   // bulkheads
// overhead bins (each row's door can swing open), the reading-light / mask panels under them
const BINS = [];
for (const s of [-1, 1]) for (let z = ZF + 0.6; z < ZB - 0.5; z += 1.58) {
  const g = new THREE.Group(); g.position.set(s * 1.12, 1.98, z + 0.79); CABIN.add(g);
  cbox(0.86, 0.42, 1.54, s * 0.18, 0, 0, binMat, 0.04, g);
  const door = new THREE.Group(); door.position.set(-s * 0.25, -0.2, 0); g.add(door);              // hinged at the top of the aisle side
  cbox(0.04, 0.38, 1.5, 0, 0.19, 0, binMat, 0.015, door); door.children[0].position.y = 0.19;
  door.position.y = -0.21 + 0.0; door.rotation.z = 0; BINS.push({ g, door, s, z: z + 0.79 });
  cbox(0.62, 0.05, 1.5, s * 0.08, -0.25, 0, cabinMat(0xdcdad4, 0.5), 0.01, g);                     // passenger service panel (masks drop from here)
}
const ceilLight = new THREE.InstancedMesh(new THREE.BoxGeometry(0.06, 0.02, 1.4), new THREE.MeshStandardMaterial({ color: 0x111111, emissive: 0xfff6e8, emissiveIntensity: 1.6 }), 24);
{ const m4 = new THREE.Matrix4(); let k = 0; for (const s of [-1, 1]) for (let z = ZF + 1.0; z < ZB - 0.6 && k < 24; z += 1.58) { m4.makeTranslation(s * 0.75, 2.16, z); ceilLight.setMatrixAt(k++, m4); } ceilLight.count = k; CABIN.add(ceilLight); }
const cabinLights = [];
for (const z of [-6, -2.5, 1, 4.5]) { const l = new THREE.PointLight(0xfff3e2, 5, 6, 1.6); l.position.set(0, 2.0, z); CABIN.add(l); cabinLights.push(l); }
const keyLight = new THREE.SpotLight(0xfff1dc, 18, 7, 0.7, 0.6, 1.4); keyLight.position.set(0.6, 2.05, -1.2); keyLight.target.position.set(-0.5, 0.9, 0.1); keyLight.castShadow = true; keyLight.shadow.mapSize.set(1024, 1024); keyLight.shadow.bias = -0.0005; CABIN.add(keyLight); CABIN.add(keyLight.target);
// windows: one per row each side at seated eye height, showing the sky (it scrolls and tilts when the jet drops)
const winU = { uT: { value: 0 }, uRoll: { value: 0 }, uDrop: { value: 0 }, uFlash: { value: 0 }, uDark: { value: 0 }, uFire: { value: 0 } };
const winMat = new THREE.ShaderMaterial({ uniforms: winU, vertexShader: 'varying vec2 vU; varying vec3 vW; void main(){ vU = uv; vW = (modelMatrix * vec4(position, 1.0)).xyz; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
  fragmentShader: `varying vec2 vU; varying vec3 vW; uniform float uT, uRoll, uDrop, uFlash, uDark, uFire;
    float hh(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
    float vn(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f*f*(3.0-2.0*f); return mix(mix(hh(i), hh(i+vec2(1,0)), u.x), mix(hh(i+vec2(0,1)), hh(i+vec2(1,1)), u.x), u.y); }
    void main(){ vec2 c = vU - 0.5; float e = length(max(abs(c * vec2(1.0, 0.72)) - vec2(0.22, 0.22), 0.0)); if (e > 0.13) discard;
      float y = c.y * 1.4 + c.x * uRoll - uDrop;                        // horizon tilts with the roll, rises as the jet drops
      vec3 sky = mix(vec3(0.85, 0.9, 0.96), vec3(0.35, 0.58, 0.9), smoothstep(-0.1, 0.6, y));
      float cl = vn(vec2(vW.z * 1.3 + uT * 2.5, y * 3.0 + 4.0)) * 0.7 + vn(vec2(vW.z * 3.0 + uT * 6.0, y * 7.0)) * 0.3;
      sky = mix(sky, vec3(1.0), smoothstep(0.55, 0.75, cl) * 0.8);
      vec3 grd = mix(vec3(0.35, 0.45, 0.28), vec3(0.55, 0.6, 0.5), vn(vec2(vW.z * 4.0 + uT * 4.0, y * 9.0)));
      vec3 col = mix(grd, sky, smoothstep(-0.32, -0.28, y));
      col = mix(col, vec3(1.0, 0.6, 0.2), uFlash * smoothstep(0.5, 0.0, length(c)));   // the bang: an orange flash
      { vec2 fp = c - vec2(0.05, -0.16); float fl = vn(vec2(fp.x * 9.0, fp.y * 6.0 - uT * 9.0)) * 0.6 + vn(vec2(fp.x * 20.0, fp.y * 14.0 - uT * 16.0)) * 0.4;   // the engine on fire
        float flame = smoothstep(0.22, 0.0, length(fp * vec2(1.6, 0.9))) * smoothstep(0.25, 0.6, fl + 0.25 - fp.y);
        float smk = smoothstep(0.3, 0.05, length((c - vec2(0.12, 0.05)) * vec2(1.2, 0.8))) * smoothstep(0.35, 0.65, fl);
        col = mix(col, vec3(0.12, 0.11, 0.1), smk * 0.8 * uFire); col = mix(col, mix(vec3(1.0, 0.35, 0.05), vec3(1.0, 0.85, 0.3), fl), flame * uFire); }
      col *= 1.0 - 0.75 * uDark;
      float rim = smoothstep(0.08, 0.13, e); col = mix(col, vec3(0.75, 0.75, 0.72), rim);
      gl_FragColor = vec4(pow(col, vec3(2.2)) * 1.6, 1.0); }` });
const winGeo = new THREE.PlaneGeometry(0.32, 0.44);
for (const s of [-1, 1]) for (let k = -10; k <= 9; k++) { const z = rowZ(k) + 0.1; if (z < ZF + 0.3 || z > ZB - 0.3 || (s < 0 && z < -3.75 && z > -4.95)) continue;
  const w = new THREE.Mesh(winGeo, winMat); w.position.set(s * (wallX(1.12) - 0.012), 1.12, z); w.rotation.y = -s * Math.PI / 2; CABIN.add(w); }
// seats (instanced): cushion, back, headrest, armrests, base; seat-back pocket on the rear of each back
const seatRows = []; for (let k = -10; k <= 9; k++) { const z = rowZ(k); if (z < ZF + 0.8 || z > ZB - 0.5) continue; if (z < -3.6 && z > -5.1) continue; seatRows.push(z); }
const SEATS = []; for (const z of seatRows) for (const x of SEATX) SEATS.push({ x, z });
const SB = { cushY: 0.42, cushH: 0.12, cushD: 0.48, backY: 0.84, backH: 0.74, backZ: 0.25, backT: 0.1, tilt: 0.12, w: 0.44 };
{ const mk = (geo, mat, n) => { const m = new THREE.InstancedMesh(geo, mat, n); m.castShadow = true; m.receiveShadow = true; CABIN.add(m); return m; };
  const cush = mk(new RoundedBoxGeometry(SB.w, SB.cushH, SB.cushD, 2, 0.04), seatMat, SEATS.length), back = mk(new RoundedBoxGeometry(SB.w, SB.backH, SB.backT, 2, 0.04), seatMat, SEATS.length),
    head = mk(new RoundedBoxGeometry(SB.w * 0.86, 0.2, 0.06, 2, 0.025), cabinMat(0xd8d4cc, 0.8), SEATS.length), base = mk(new THREE.BoxGeometry(SB.w * 0.9, 0.34, 0.3), seatDark, SEATS.length),
    pocket = mk(new THREE.BoxGeometry(SB.w * 0.8, 0.3, 0.012), seatDark, SEATS.length);
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion().setFromEuler(new THREE.Euler(SB.tilt, 0, 0));
  SEATS.forEach((s, i) => {
    m4.makeTranslation(s.x, SB.cushY, s.z - 0.02); cush.setMatrixAt(i, m4);
    const bp = V(s.x, SB.backY, s.z + SB.backZ); m4.compose(bp, q, V(1, 1, 1)); back.setMatrixAt(i, m4);
    m4.compose(bp.clone().add(V(0, 0.32, -0.035).applyQuaternion(q)), q, V(1, 1, 1)); head.setMatrixAt(i, m4);
    m4.makeTranslation(s.x, 0.18, s.z + 0.02); base.setMatrixAt(i, m4);
    m4.compose(bp.clone().add(V(0, -0.12, SB.backT / 2 + 0.006).applyQuaternion(q)), q, V(1, 1, 1)); pocket.setMatrixAt(i, m4); });
  const arms = []; for (const z of seatRows) for (const x of [-1.665, -1.195, -0.725, -0.255, 0.255, 0.725, 1.195, 1.665]) arms.push({ x, z });
  const arm = mk(new RoundedBoxGeometry(0.05, 0.06, 0.44, 2, 0.02), armMat, arms.length);
  arms.forEach((a, i) => { m4.makeTranslation(a.x, 0.63, a.z - 0.02); arm.setMatrixAt(i, m4); }); }
// the seat-back rear face (where his head goes in the brace): z of the rear surface of the seat in front at height y
const frontBackZ = y => rowZ(1) + SB.backZ + (SB.backT / 2) / Math.cos(SB.tilt) + (y - SB.backY) * Math.tan(SB.tilt);
// emergency floor path lights + EXIT signs (glow in the smoke)
const pathLights = new THREE.InstancedMesh(new THREE.BoxGeometry(0.03, 0.012, 0.12), new THREE.MeshStandardMaterial({ color: 0x111111, emissive: 0xffe08a, emissiveIntensity: 0 }), 80);
{ const m4 = new THREE.Matrix4(); let k = 0; for (const s of [-1, 1]) for (let z = ZF + 0.5; z < ZB - 0.3 && k < 80; z += 0.45) { m4.makeTranslation(s * 0.25, 0.008, z); pathLights.setMatrixAt(k++, m4); } pathLights.count = k; CABIN.add(pathLights); }
const exitTex = canvasTex(256, 96, g => { g.fillStyle = '#b30d14'; g.fillRect(0, 0, 256, 96); g.fillStyle = '#fff'; g.font = 'bold 70px Inter, Arial'; g.textAlign = 'center'; g.fillText('EXIT', 128, 74); });
const exitMat = new THREE.MeshBasicMaterial({ map: exitTex, toneMapped: false, fog: false });
const exitSigns = [];
for (const [x, z, ry] of [[-0.75, DOORZ + 0.45, 0], [0, -3.6, 0]]) { const e = new THREE.Mesh(new THREE.PlaneGeometry(0.34, 0.13), exitMat); e.position.set(x, 2.08, z); e.rotation.y = ry; CABIN.add(e); exitSigns.push(e); }
const exitGlow = new THREE.PointLight(0xff3030, 0, 3.5, 1.5); exitGlow.position.set(-0.8, 1.9, DOORZ + 0.3); CABIN.add(exitGlow);
// the left front door: a plug door in the wall that swings out; daylight pours in through it
const DOOR = new THREE.Group(); CABIN.add(DOOR);
{ const fr = cabinMat(0xcfcac2, 0.5);
  cbox(0.1, 1.9, 0.1, -1.82, 0.95, DOORZ - 0.48, fr); cbox(0.1, 1.9, 0.1, -1.82, 0.95, DOORZ + 0.48, fr); cbox(0.1, 0.1, 1.0, -1.8, 1.92, DOORZ, fr); }
const doorLeaf = new THREE.Group(); doorLeaf.position.set(-1.86, 0, DOORZ + 0.45); DOOR.add(doorLeaf);
cbox(0.08, 1.85, 0.9, 0, 0.93, -0.45, cabinMat(0xdedad3, 0.5), 0.03, doorLeaf);
const doorLight = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 1.85), new THREE.MeshBasicMaterial({ color: 0xfff4dc, toneMapped: false, transparent: true, opacity: 0 }));
doorLight.position.set(-1.9, 0.93, DOORZ); doorLight.rotation.y = Math.PI / 2; CABIN.add(doorLight);
const dayLight = new THREE.SpotLight(0xfff1dc, 0, 6, 0.9, 0.7, 1.2); dayLight.position.set(-2.6, 1.4, DOORZ); dayLight.target.position.set(0, 0.4, DOORZ); CABIN.add(dayLight); CABIN.add(dayLight.target);

// ------------------------------------------------------------------ props: the mask (falls from the panel, then rides on his face), the lap belt, his bag, flying things
const MASK_HOME = V(ME.x - 0.08, 1.73, 0.0);
const mask = new THREE.Group(); CABIN.add(mask);
{ const yel = new THREE.MeshStandardMaterial({ color: 0xffd21e, roughness: 0.45, side: THREE.DoubleSide });
  const cup = new THREE.Mesh(new THREE.SphereGeometry(0.055, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2).rotateX(-Math.PI / 2), yel); cup.scale.set(1, 1, 0.85); mask.add(cup);
  const bag = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.045, 0.12, 14), new THREE.MeshStandardMaterial({ color: 0xf0f0f0, transparent: true, opacity: 0.55, roughness: 0.3 })); bag.position.set(0, -0.1, -0.03); mask.add(bag); }
const maskTube = new THREE.Mesh(new THREE.BufferGeometry(), new THREE.MeshStandardMaterial({ color: 0xe8e8e8, transparent: true, opacity: 0.7, roughness: 0.3 })); CABIN.add(maskTube);
const otherMasks = new THREE.InstancedMesh(new THREE.SphereGeometry(0.05, 14, 8, 0, Math.PI * 2, 0, Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0xffd21e, roughness: 0.45 }), 60);
const OM = []; for (const z of seatRows) for (const x of SEATX) if (!(x === ME.x && z === 0)) OM.push({ x: x + (x < 0 ? -0.08 : 0.08), z, ph: hash1(x * 7 + z * 13) * 6.28 });
otherMasks.count = Math.min(60, OM.length); CABIN.add(otherMasks);
const maskStrings = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.003, 0.003, 1, 4), new THREE.MeshStandardMaterial({ color: 0xdddddd }), 60); maskStrings.count = otherMasks.count; CABIN.add(maskStrings);
const belt = new THREE.Mesh(new THREE.BufferGeometry(), new THREE.MeshStandardMaterial({ color: 0x2a3a5c, roughness: 0.8 })); belt.castShadow = true; CABIN.add(belt);
const buckle = cbox(0.07, 0.045, 0.02, 0, 0, 0, new THREE.MeshStandardMaterial({ color: 0xc9ccd2, metalness: 0.9, roughness: 0.25 }), 0.008);
const bagP = new THREE.Group(); CABIN.add(bagP);                                // his backpack
{ const bm = cabinMat(0x7a2e2e, 0.8); cbox(0.3, 0.42, 0.18, 0, 0.21, 0, bm, 0.06, bagP); cbox(0.24, 0.16, 0.05, 0, 0.14, 0.1, cabinMat(0x5e2222, 0.8), 0.03, bagP);
  const hd = new THREE.Mesh(new THREE.TorusGeometry(0.05, 0.012, 8, 16, Math.PI), cabinMat(0x222222, 0.6)); hd.position.set(0, 0.42, 0); bagP.add(hd); }
const cup = new THREE.Group(); CABIN.add(cup);                                  // the cup and the phone that float up in the drop
{ const c = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.028, 0.09, 16, 1, true), new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.6, side: THREE.DoubleSide })); cup.add(c);
  const drink = new THREE.Mesh(new THREE.SphereGeometry(0.03, 12, 8), new THREE.MeshPhysicalMaterial({ color: 0x8a4a1a, roughness: 0.1, transmission: 0.3, transparent: true, opacity: 0.85 })); drink.position.y = 0.09; cup.add(drink); cup.userData.drink = drink; }
const floaters = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 1, 1), new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.7 }), 9); CABIN.add(floaters);
const FL = []; for (let i = 0; i < 9; i++) { const r = hash1(i * 7.7); FL.push({ p: V(-0.45 - 0.9 * hash1(i * 3.1), 0.55 + 0.25 * hash1(i * 5.3), -0.55 + 0.6 * hash1(i * 2.2)), r, s: i % 3 === 0 ? V(0.11, 0.004, 0.11) : i % 3 === 1 ? V(0.07, 0.11, 0.025) : V(0.13, 0.19, 0.02) });
  floaters.setColorAt(i, new THREE.Color([0xf5f5f0, 0xe8492f, 0x2f7de8][i % 3])); }
const phoneF = new THREE.Mesh(new RoundedBoxGeometry(0.072, 0.15, 0.009, 2, 0.004), new THREE.MeshStandardMaterial({ color: 0x1a1b1e, roughness: 0.3, metalness: 0.4 })); CABIN.add(phoneF);
// smoke: a thick layer that grows down from the ceiling (soft sprites) + fog
const softTex = canvasTex(64, 64, g => { const gr = g.createRadialGradient(32, 32, 0, 32, 32, 31); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.45, 'rgba(255,255,255,0.45)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); });
function cloud(n, size, color, op, parent = scene) { const g = new THREE.BufferGeometry(); const p = new Float32Array(n * 3); g.setAttribute('position', new THREE.BufferAttribute(p, 3));
  const m = new THREE.Points(g, new THREE.PointsMaterial({ map: softTex, color, size, transparent: true, depthWrite: false, opacity: op })); m.frustumCulled = false; parent.add(m); return { m, p, n }; }
function setCloud(c, fn) { let k = 0; for (let i = 0; i < c.n; i++) { const q = fn(i); if (q) { c.p.set([q.x, q.y, q.z], k * 3); k++; } } for (let i = k; i < c.n; i++) c.p.set([0, -999, 0], i * 3); c.m.geometry.attributes.position.needsUpdate = true; c.m.visible = k > 0; }
const smoke = cloud(700, 0.9, 0x5c5a58, 0.35, CABIN);

// ------------------------------------------------------------------ outside: the jet and a field (far from the cabin set, at JX)
const JX = 400, OUT = new THREE.Group(); OUT.position.set(JX, 0, 0); scene.add(OUT);
const grass = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.95 });
grass.onBeforeCompile = sh => {
  sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vWc;').replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvWc = (modelMatrix * vec4(transformed, 1.0)).xyz;');
  sh.fragmentShader = sh.fragmentShader.replace('#include <common>', `#include <common>
varying vec3 vWc;
float hh(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
float vn(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f*f*(3.0-2.0*f); return mix(mix(hh(i), hh(i+vec2(1,0)), u.x), mix(hh(i+vec2(0,1)), hh(i+vec2(1,1)), u.x), u.y); }`)
    .replace('#include <color_fragment>', `#include <color_fragment>
  { vec2 P = vWc.xz; float n = vn(P * 0.15) * 0.5 + vn(P * 1.7) * 0.3 + hh(floor(P * 40.0)) * 0.2;
    vec3 c = mix(vec3(0.24, 0.36, 0.14), vec3(0.42, 0.5, 0.22), n);
    float scar = (1.0 - smoothstep(1.6, 2.6, abs(P.x - ${JX.toFixed(1)}))) * smoothstep(-20.0, 5.0, P.y) * (1.0 - smoothstep(30.0, 60.0, P.y));   // the skid scar the jet ploughs
    c = mix(c, vec3(0.32, 0.25, 0.18) * (0.8 + 0.4 * n), scar * uScar);
    diffuseColor.rgb = c; }`);
  sh.uniforms.uScar = SCAR; sh.fragmentShader = sh.fragmentShader.replace('varying vec3 vWc;', 'varying vec3 vWc; uniform float uScar;');
};
const SCAR = { value: 0 };
const field = new THREE.Mesh(new THREE.PlaneGeometry(1200, 1200).rotateX(-Math.PI / 2), grass); field.position.set(JX, 0, 0); field.receiveShadow = true; scene.add(field);
{ const tr = new THREE.InstancedMesh(new THREE.SphereGeometry(3.2, 10, 8), new THREE.MeshStandardMaterial({ color: 0x35552a, roughness: 1 }), 70); const m4 = new THREE.Matrix4(); let k = 0;
  for (let i = 0; i < 200 && k < 70; i++) { const a = hash1(i) * 6.28, r = 70 + hash1(i * 3) * 160; const x = JX + Math.cos(a) * r, z = Math.sin(a) * r; m4.compose(V(x, 3.4, z), new THREE.Quaternion(), V(1, 1.4, 1)); tr.setMatrixAt(k++, m4); }
  tr.count = k; scene.add(tr); }
// the jet (local: nose toward -z, cabin floor at y = FLOOR above the belly; left = -x). Scale matches the cabin: fuselage r 1.95.
const jet = new THREE.Group(); OUT.add(jet);
const JFLOOR = 1.2;                                                             // cabin floor height above the belly (the door sill when it lies on the ground)
const livery = new THREE.MeshPhysicalMaterial({ color: 0xf4f5f7, roughness: 0.35, clearcoat: 0.6 }), blueM = new THREE.MeshPhysicalMaterial({ color: 0x1f4fa8, roughness: 0.4, clearcoat: 0.6 }),
  greyM = new THREE.MeshStandardMaterial({ color: 0x9aa1a8, metalness: 0.6, roughness: 0.4 }), darkM = new THREE.MeshStandardMaterial({ color: 0x16181c, roughness: 0.5 });
{ const add = (geo, m, x, y, z, rx = 0, ry = 0, rz = 0) => { const o = new THREE.Mesh(geo, m); o.position.set(x, y, z); o.rotation.set(rx, ry, rz); o.castShadow = true; o.receiveShadow = true; jet.add(o); return o; };
  const cy = R0;                                                                // fuselage centre above the belly
  add(new THREE.CylinderGeometry(R0, R0, 30, 48).rotateX(Math.PI / 2), livery, 0, cy, 0);
  add(new THREE.SphereGeometry(R0, 48, 24, 0, Math.PI * 2, 0, Math.PI / 2).rotateX(-Math.PI / 2), livery, 0, cy, -15).scale.set(1, 1, 1.6);
  add(new THREE.ConeGeometry(R0, 7, 48).rotateX(Math.PI / 2), livery, 0, cy + 0.6, 18.5).scale.set(1, 0.7, 1);
  add(new THREE.CylinderGeometry(R0 * 1.004, R0 * 1.004, 30, 48, 1, true, -0.35, 0.7).rotateX(Math.PI / 2), blueM, 0, cy, 0).rotation.z = Math.PI / 2;   // a blue stripe down each side
  add(new THREE.CylinderGeometry(R0 * 1.004, R0 * 1.004, 30, 48, 1, true, -0.35, 0.7).rotateX(Math.PI / 2), blueM, 0, cy, 0).rotation.z = -Math.PI / 2;
  const wing = new THREE.Shape(); wing.moveTo(0, 0); wing.lineTo(17, 5.5); wing.lineTo(17, 7); wing.lineTo(0, 6); wing.lineTo(0, 0);
  for (const s of [-1, 1]) { const w = add(new THREE.ExtrudeGeometry(wing, { depth: 0.3, bevelEnabled: false }).rotateX(Math.PI / 2), livery, s * 1.0, cy - 0.7, -2.0); w.scale.set(s, 1, 1);
    add(new THREE.CylinderGeometry(0.85, 0.78, 4.2, 28).rotateX(Math.PI / 2), greyM, s * 5.6, 0.95, -2.4);            // engines under the wings
    add(new THREE.CircleGeometry(0.78, 28), darkM, s * 5.6, 0.95, -4.52, 0, Math.PI);
    const ht = new THREE.Shape(); ht.moveTo(0, 0); ht.lineTo(6, 2.6); ht.lineTo(6, 3.6); ht.lineTo(0, 3.4); ht.lineTo(0, 0);
    add(new THREE.ExtrudeGeometry(ht, { depth: 0.2, bevelEnabled: false }).rotateX(Math.PI / 2), livery, s * 0.5, cy + 0.9, 16.5).scale.set(s, 1, 1); }
  const vt = new THREE.Shape(); vt.moveTo(0, 0); vt.lineTo(5, 7); vt.lineTo(7.2, 7); vt.lineTo(6.5, 0); vt.lineTo(0, 0);
  const fin = add(new THREE.ExtrudeGeometry(vt, { depth: 0.3, bevelEnabled: false }), blueM, -0.15, cy + 1.6, 14.5, 0, -Math.PI / 2, 0);
  const wins = new THREE.InstancedMesh(new THREE.PlaneGeometry(0.25, 0.34), darkM, 80); const m4 = new THREE.Matrix4(); let k = 0;
  for (const s of [-1, 1]) for (let z = -11; z < 12 && k < 80; z += 0.79) { if (s < 0 && Math.abs(z - (-11 + 0.79 * 9)) < 0.6) continue; m4.compose(V(s * (R0 + 0.01), cy + 0.45, z), new THREE.Quaternion().setFromEuler(new THREE.Euler(0, s * Math.PI / 2, 0)), V(1, 1, 1)); wins.setMatrixAt(k++, m4); }
  wins.count = k; jet.add(wins);
  add(new THREE.PlaneGeometry(1.6, 0.6), darkM, 0, cy + 0.85, -16.4, -0.5, 0, 0); }           // cockpit windows
// the exterior door (left front) and the slide (inflates in beat 7). Door in jet space at JDOOR (sill centre).
const JDOOR = V(-R0 + 0.05, JFLOOR, -10.2);
const jetDoor = new THREE.Mesh(new RoundedBoxGeometry(0.08, 1.85, 0.9, 2, 0.03), livery); jet.add(jetDoor);
const doorHole = new THREE.Mesh(new THREE.PlaneGeometry(0.88, 1.83), new THREE.MeshBasicMaterial({ color: 0x1a1612 })); doorHole.position.copy(JDOOR).add(V(-0.03, 0.93, 0)); doorHole.rotation.y = -Math.PI / 2; jet.add(doorHole);
const SLIDE_LEN = 4.4, SLIDE_ANG = Math.atan2(JFLOOR, SLIDE_LEN);
const slide = new THREE.Group(); slide.position.copy(JDOOR); slide.rotation.z = 0; jet.add(slide);
{ const ym = new THREE.MeshStandardMaterial({ color: 0xffc21a, roughness: 0.55 });
  const bed = new THREE.Mesh(new THREE.BoxGeometry(SLIDE_LEN, 0.14, 1.1), ym); bed.position.set(-SLIDE_LEN / 2, -0.06, 0); bed.castShadow = true; slide.add(bed);
  for (const s of [-1, 1]) { const tube = new THREE.Mesh(new THREE.CylinderGeometry(0.17, 0.17, SLIDE_LEN + 0.2, 16).rotateZ(Math.PI / 2), ym); tube.position.set(-SLIDE_LEN / 2, 0.1, s * 0.62); tube.castShadow = true; slide.add(tube); } }
slide.rotation.z = SLIDE_ANG;                                                    // tips down from the sill to the ground (toward -x)
const dust = cloud(600, 3.2, 0x8a7a62, 0.32, scene);                             // dirt spray on the belly landing
const jetSmoke = cloud(260, 4.5, 0x3a3836, 0.45, scene);                          // smoke rising from the wing after
const sparksC = cloud(160, 0.35, 0xffc36a, 1.0, scene);
const fireC = cloud(90, 2.4, 0xff4a08, 0.45, scene); fireC.m.material.toneMapped = false;
const fireCore = cloud(60, 1.2, 0xffc23a, 0.6, scene); fireCore.m.material.toneMapped = false;

// ------------------------------------------------------------------ the 95-out-of-100 stage (dark, far away)
const STAT = V(0, 0, -600);
const statStage = new THREE.Group(); statStage.position.copy(STAT); scene.add(statStage);
statStage.add(new THREE.Mesh(new THREE.SphereGeometry(30, 32, 16), new THREE.MeshBasicMaterial({ color: 0x050a14, side: THREE.BackSide })));
{ const l = new THREE.DirectionalLight(0xffffff, 2.2); l.position.set(1, 2, 3); statStage.add(l); statStage.add(l.target); }
const PEEPS = 100, peepMatOn = new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0x1a8a3e, emissiveIntensity: 0.9, roughness: 0.5 }),
  peepMatOff = new THREE.MeshStandardMaterial({ color: 0x5a5f68, roughness: 0.7 });
const peepGeo = (() => { const b = new THREE.CapsuleGeometry(0.11, 0.2, 4, 10); b.translate(0, 0.2, 0); const h = new THREE.SphereGeometry(0.085, 14, 10); h.translate(0, 0.52, 0);
  const g = new THREE.BufferGeometry(); const pa = [...b.toNonIndexed().attributes.position.array, ...h.toNonIndexed().attributes.position.array];
  const na = [...b.toNonIndexed().attributes.normal.array, ...h.toNonIndexed().attributes.normal.array];
  g.setAttribute('position', new THREE.Float32BufferAttribute(pa, 3)); g.setAttribute('normal', new THREE.Float32BufferAttribute(na, 3)); return g; })();
const peepsOn = new THREE.InstancedMesh(peepGeo, peepMatOn, 95), peepsOff = new THREE.InstancedMesh(peepGeo, peepMatOff, 5);
statStage.add(peepsOn); statStage.add(peepsOff);
const PEEP = []; for (let i = 0; i < PEEPS; i++) { const r = Math.floor(i / 10), c = i % 10; PEEP.push(V((c - 4.5) * 0.3, 2.1 - r * 0.42, 0)); }
const OFFSET = [13, 37, 58, 71, 94];                                             // the 5 who don't make it (scattered, not a block)

// ------------------------------------------------------------------ the guy
const G = await loadGuy(THREE, '/char/guy', {});
scene.add(G.root); G.root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
const HIP = V(0.0, 0.95, 0.0);
const SEATHIP = V(ME.x, 0.585, 0.05);                                      // his hips when seated (cushion top 0.48)
const HOME = SEATHIP;
function untwistSafe() { for (const S of ['R', 'L']) { const ua = G.bones['uarm' + S], ut = G.bones['uarmTwist' + S]; ua.quaternion.multiply(ut.quaternion); ut.quaternion.identity(); } G.untwist(); }
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
    if (typeof handExtra === 'function') c += handExtra(S, f);           // the scene's solids (seats, armrests): keep the arm out of them
    return c; };
  const m = MEM[key]; const prev = m && m.frame === frame - 1 ? m.a : null;
  const COLD = [A(40, 15, 0, 80, 0), A(60, 25, 20, 60, 40), A(30, 40, -20, 100, -30), A(80, 10, 0, 110, 60), A(50, 30, 30, 40, 70), A(20, 20, -30, 120, -60), A(60, 10, -10, 100, 75), A(40, 20, 10, 90, -75)];
  const seeds = prev ? [prev] : COLD;
  let best = null;
  for (const s0 of seeds) {
    let a = s0.map((v, i) => clamp(v, ARM_LIM[i][0], ARM_LIM[i][1])), ca = cost(a);
    for (let step = prev ? 4 : 16; step >= 0.25; step /= 2) { let imp = true, g = 0;
      while (imp && g++ < 10) { imp = false; for (let i = 0; i < 7; i++) for (const sg of [1, -1]) { const b = a.slice(); b[i] = clamp(b[i] + sg * step, ARM_LIM[i][0], ARM_LIM[i][1]); const cb = cost(b); if (cb < ca - 1e-9) { a = b; ca = cb; imp = true; } } } }
    if (!best || ca < best.c) best = { a, c: ca };
  }
  if (prev && best.c > 20) {                                     // warm start stuck (the target turned the hand past what small steps reach): try the cold seeds too
    for (const s0 of COLD) { let a = s0.map((v, i) => clamp(v, ARM_LIM[i][0], ARM_LIM[i][1])), ca = cost(a);
      for (let step = 16; step >= 0.25; step /= 2) { let imp = true, g = 0;
        while (imp && g++ < 10) { imp = false; for (let i = 0; i < 7; i++) for (const sg of [1, -1]) { const b = a.slice(); b[i] = clamp(b[i] + sg * step, ARM_LIM[i][0], ARM_LIM[i][1]); const cb = cost(b); if (cb < ca - 1e-9) { a = b; ca = cb; imp = true; } } } }
      if (ca < best.c) best = { a, c: ca }; } }
  MEM[key] = { frame, a: best.a }; return best;
}


// ------------------------------------------------------------------ poses (sitting from the car Short; crouch, slide and run added)
const SIT = { thighR: [88, 0, 4], thighL: [88, 0, -4], shinR: [-80, 0, 0], shinL: [-80, 0, 0], footR: [-4, 0, 0], footL: [-4, 0, 0], spine1: [4, 0, 0], spine2: [2, 0, 0], neck: [-4, 0, 0] };
Object.assign(P, {
  sit: { ...SIT, armR: A(16, 10, 0, 45), armL: A(16, 10, 0, 45) },
  crouch: { spine1: [-14, 0, 0], spine2: [-10, 0, 0], neck: [22, 0, 0], head: [10, 0, 0], armR: A(30, 12, 0, 60), armL: A(30, 12, 0, 60) },
  slideSit: { thighR: [84, 0, 6], thighL: [84, 0, -6], shinR: [-6, 0, 0], shinL: [-6, 0, 0], footR: [10, 0, 0], footL: [10, 0, 0], spine1: [-6, 0, 0], neck: [-8, 0, 0], armR: A(70, 14, 0, 30), armL: A(70, 14, 0, 30) },
  run: { spine1: [-10, 0, 0], neck: [4, 0, 0], armR: A(0, 10, 0, 90), armL: A(0, 10, 0, 90) },
});
for (const k of ['sit', 'crouch', 'slideSit', 'run']) { curl(P[k], 'R', 30); curl(P[k], 'L', 30); }
const MOUTH = new THREE.Object3D(); MOUTH.position.set(0, G.man.mouthY, G.man.mouthZ); attach(MOUTH, 'head');
G.reset();
const wpos = o => o.getWorldPosition(new THREE.Vector3());
const yawQ = deg => new THREE.Quaternion().setFromAxisAngle(V(0, 1, 0), deg * D2R);
const headFwd = () => V(0, 0, -1).applyQuaternion(G.bones.head.getWorldQuaternion(new THREE.Quaternion()));

// blend two hand frames (palm normal n, finger direction u) as a rotation, never through a dead spot
function frameQ(n, u) { const nn = n.clone().normalize(), uu = u.clone().sub(nn.clone().multiplyScalar(u.dot(nn))).normalize(), w = new THREE.Vector3().crossVectors(uu, nn);
  return new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(uu, nn, w)); }
function blendFrame(n0, u0, n1, u1, k) { const q = frameQ(n0, u0).slerp(frameQ(n1, u1), k); return { n: V(0, 1, 0).applyQuaternion(q), u: V(1, 0, 0).applyQuaternion(q) }; }
// ------------------------------------------------------------------ fixed hand targets
const ARMR = { L: V(-0.725, 0.665, -0.2), R: V(-0.255, 0.665, -0.2) };          // front ends of his two armrests (top surface)
const gripRest = S => ({ S, p: ARMR[S].clone().add(V(0, 0.035, 0.035)), n: V(0, -1, 0), u: V(0, -0.25, -1).normalize(), c: 72 });
const BELT = { L: V(ME.x - 0.22, 0.5, 0.17), R: V(ME.x + 0.22, 0.5, 0.17) };       // lap belt anchors (seat sides)
// brace: forearms on the seat back in front, head down against them (FAA high-density brace)
const braceHand = S => { const s = S === 'R' ? 1 : -1, y = 1.0; return { S, p: V(ME.x + s * 0.1, y, frontBackZ(y) + 0.035), n: V(0, 0, -1), u: V(-s * 0.45, 0.89, 0).normalize(), c: 4 }; };
// the brace amount that puts his forehead on his forearms against the seat back (solved once, numerically)
let BRACE_K = 1;
function bracePose(k) { return addPose(P.sit, { spine1: [-30 * k, 0, 0], spine2: [-26 * k, 0, 0], chest: [-14 * k, 0, 0], neck: [-26 * k, 0, 0], head: [-10 * k, 0, 0] }); }
const BRACE_TILT = -24;

// ------------------------------------------------------------------ the story
function blink(t) { for (const b0 of [1.4, 7.0, 12.3, 19.6, 25.1, 31.2, 36.5]) { const u = (t - b0) / 0.16; if (u > 0 && u < 1) return Math.sin(Math.PI * u); } return 0; }
// time around the bang: from 0.6 s before the loop point through beat 0 (so frame one is mid-drop and the last frame leads into it)
const HT = t => (t > TOTAL - 0.6 ? t - TOTAL : t);
const PRE = 0.6;
function feetSeat() { return { R: V(ME.x + 0.1, 0.1, -0.38), L: V(ME.x - 0.1, 0.1, -0.36) }; }
function guyAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b], tt = HT(t);
  let pose = P.sit, root = {}, face = { blink: blink(t) }, hands = [], show = true, feet = feetSeat(), walk = null, maskOn = false, maskHeld = 0, beltK = 1, beltPull = 0, bagHeld = false;
  const scared = { browIn: 0.9, fear: 0.8, jaw: 0.25 };
  if (b === 0 || (b === 9 && tt < 0)) {                       // the bang: he grabs both armrests, body lifts a little in the drop
    const g = smooth(-0.45, -0.05, tt), lift = 0.02 * smooth(-0.4, 0.3, tt) * (1 - smooth(DUR[0] - 0.8, DUR[0], tt));
    pose = addPose(P.sit, { spine1: [-5 * g, 0, 0], spine2: [-3 * g, 0, 0], neck: [10 * g + 3 * Math.sin(tt * 9) * g, 6 * Math.sin(tt * 2.3) * g, 0] });
    if (b === 9) pose = mixPose(CALM, pose, smooth(-0.6, -0.25, tt));
    root = { y: SEATHIP.y + lift };
    hands = [g > 0.5 ? gripRest('R') : { ...gripRest('R'), p: ARMR.R.clone().add(V(-0.06, 0.03, 0.1)).lerp(gripRest('R').p, g / 0.5) }, gripRest('L')];
    if (b === 9) { const gr = gripRest('R'), f = blendFrame(PHONE_H.n, PHONE_H.u, gr.n, gr.u, g); hands = [{ S: 'R', p: PHONE_H.p.clone().lerp(gr.p, g), n: f.n, u: f.u, c: lerp(PHONE_H.c, gr.c, g) }, gripRest('L')]; }
    face = { ...face, ...Object.fromEntries(Object.entries(scared).map(([k, v]) => [k, v * g])), look: [0.15 * g, 0.25 * g] };
  } else if (b === 1) {                                      // masks drop; he reaches up, grabs his, pulls it to his face
    const reach = smooth(0.35, 1.0, lt), pull = smooth(1.0, 1.8, lt);
    hands = () => { const dangle = MASKDANGLE(t), m = wpos(MOUTH).addScaledVector(headFwd(), 0.1).add(V(0, -0.01, 0));
      const grab = dangle.clone().add(V(0.05, -0.01, 0)), tgt = grab.clone().lerp(m, pull);       // the hand comes to the mask's right side, palm in
      const gr = gripRest('R'), GN = V(-1, 0, 0.25).normalize(), GU = V(0, 1, 0);
      const f = pull > 0 ? blendFrame(GN, GU, V(0, 0, 1), V(-0.25, 1, 0), pull) : blendFrame(gr.n, gr.u, GN, GU, reach);
      return [{ S: 'R', p: gr.p.clone().lerp(tgt, reach), n: f.n, u: f.u, c: lerp(gr.c, 40, reach) }, gripRest('L')]; };
    pose = addPose(P.sit, { neck: [14 * (1 - pull) + 4, 0, 0], head: [6 * (1 - pull), 0, 0] });
    maskHeld = smooth(0.9, 1.05, lt); maskOn = pull > 0.98;
    face = { ...face, browIn: 0.8, fear: 0.6, jaw: 0.15 * (1 - pull), look: [0.0, 0.5 * (1 - pull)] };
  } else if (b === 2) {                                      // pulls the lap belt low and tight: left hand holds the buckle, right pulls the strap end
    maskOn = true; beltPull = smooth(0.3, 1.3, lt) - 0.15 * smooth(1.6, 2.2, lt);
    hands = () => { const bk = BUCKLE_AT(); return [{ S: 'R', p: bk.clone().add(V(0.07 + 0.12 * beltPull, 0.035 + 0.03 * beltPull, -0.01)), n: V(0, -1, 0), u: V(0.15, 0, -1).normalize(), c: 65 },
             { S: 'L', p: bk.clone().add(V(-0.06, 0.035, -0.005)), n: V(0, -1, 0), u: V(0.2, 0, -1).normalize(), c: 55 }]; };
    pose = addPose(P.sit, { neck: [-28, 0, 0], head: [-8, 0, 0], spine1: [-4, 0, 0] });
    face = { ...face, browIn: 0.7, press: 0.5, look: [0, -0.6] };
  } else if (b === 3 || b === 4) {                           // brace (and stay braced through the hit)
    maskOn = true; const k = b === 3 ? smooth(0.5, 1.6, lt) : 1;
    pose = bracePose(k * BRACE_K); root = { tilt: BRACE_TILT * k };
    hands = () => { const from = { R: BUCKLE_AT().add(V(0.19, 0.065, -0.01)), L: BUCKLE_AT().add(V(-0.06, 0.035, -0.005)) };
    return ['R', 'L'].map(S => { const h = braceHand(S), kk = b === 3 ? smooth(0.3, 1.4, lt) : 1, f = blendFrame(V(0, -1, 0), V(S === 'R' ? 0.15 : 0.2, 0, -1), h.n, h.u, kk);
      return { ...h, p: from[S].clone().lerp(h.p, kk).add(V(0, 0.1 * Math.sin(Math.PI * kk), 0.07 * Math.sin(Math.PI * kk))), n: f.n, u: f.u, c: lerp(60, h.c, kk) }; }); };
    face = { ...face, browIn: 1, press: 0.6, blink: b === 4 ? 1 : face.blink * (1 - k) + k * 0.85 };
    if (b === 4) root = { ...root, z: SEATHIP.z + 0.004 * Math.sin(lt * 40) * (1 - smooth(DUR[4] * 0.55, DUR[4], lt)) };
  } else if (b === 5) {                                      // smoke: standing in the aisle, coughing, then gets down low, hand over his mouth
    const low = smooth(DUR[5] * 0.35, DUR[5] * 0.6, lt), cough = Math.pow(Math.max(0, Math.sin(lt * 5.5)), 6) * (1 - low * 0.6);
    pose = mixPose(addPose(P.stand, { spine1: [-10 * cough, 0, 0], neck: [-8 * cough + 6, 0, 0] }), P.crouch, low);
    root = { x: 0.02, z: 0.12, y: lerp(0.95, 0.62, low), tilt: lerp(0, -28, low), yaw: 0 };
    feet = { R: V(0.13, 0.1, 0.02), L: V(-0.1, 0.1, 0.2 - 0.12 * low) };
    hands = () => { const f = blendFrame(V(1, 0, 0), V(0, -1, 0), V(0.1, -1, 0), V(0, -0.15, -1), low);
      return [handOverMouth('R'), { S: 'L', p: V(-0.19, 0.84, 0.13).lerp(V(-0.25, 0.73, -0.2), low), n: f.n, u: f.u, c: lerp(20, 40, low) }]; };
    face = { ...face, squint: 0.8, browIn: 0.9, press: 0.3, look: [0, 0.4 * (1 - low)] };
  } else if (b === 6) {                                      // crouch-walk down the aisle, left hand counting the armrests by touch
    const A0 = V(0.02, 0, 0.12), A1 = V(0.0, 0, DOORZ + 0.55);
    const zh = lerp(A0.z, A1.z, smooth(0, d, lt) * 0.15 + (lt / d) * 0.85);
    pose = addPose(P.crouch, { spine2: [0, 4 * Math.sin(lt * 7), 0] });
    root = { x: 0.0, z: zh, y: 0.62 + 0.015 * Math.abs(Math.sin(lt * 7)), tilt: -28, yaw: 0 };
    walk = { A0, A1, d, lt, f: 1.1, stance: 0.6, lift: 0.05, zAt: zh };
    hands = () => [handOverMouth('R'), countHand(zh)];
    face = { ...face, squint: 0.8, browIn: 0.9, press: 0.3, look: [0, 0.35] };
  } else if (b === 7) {
    const k = lt / d;
    if (k < SL0) {                                           // at the door: daylight, he lets go of his bag
      const RT = V(-1.05, 0.66, DOORZ + 0.15), yw = 70, fw = V(-Math.sin(yw * D2R), 0, -Math.cos(yw * D2R)), rt = V(Math.cos(yw * D2R), 0, -Math.sin(yw * D2R));
      pose = addPose(P.crouch, { neck: [6, 10, 0] }); root = { x: RT.x, z: RT.z, y: RT.y, tilt: -22, yaw: yw };
      feet = { R: RT.clone().setY(0.1).addScaledVector(rt, 0.12).addScaledVector(fw, 0.08), L: RT.clone().setY(0.1).addScaledVector(rt, -0.12).addScaledVector(fw, -0.06) };
      const drop = smooth(SL0 * d * 0.35, SL0 * d * 0.55, lt); bagHeld = drop < 0.5;
      hands = [{ S: 'R', p: RT.clone().setY(0.56).addScaledVector(rt, 0.22), n: rt.clone().negate(), u: V(0, -1, 0), c: lerp(80, 15, drop) },
               { S: 'L', p: V(-1.68, 1.08, DOORZ + 0.43), n: V(-0.3, 0, -1).normalize(), u: V(0, 1, 0), c: 70 }];
      face = { ...face, squint: 0.5, browIn: 0.7, look: [-0.3, 0] };
    } else if (k < SL1) {                                    // the slide: sitting, arms forward, feet first (jet space -> world)
      const u = smooth(SL0 * d, SL1 * d, lt), s = lerp(0.2, SLIDE_LEN + 0.3, u * u * 0.4 + u * 0.6);
      const base = slidePt(Math.min(s, SLIDE_LEN)); if (s > SLIDE_LEN) base.x -= (s - SLIDE_LEN); base.y = Math.max(base.y, 0);
      pose = P.slideSit; feet = null;
      root = { x: base.x, y: base.y + 0.2, z: base.z, yaw: 90, tilt: 6 + (s < SLIDE_LEN ? SLIDE_ANG / D2R : 0) };
      face = { ...face, browIn: 0.6, jaw: 0.3, look: [0, 0] };
    } else {                                                 // runs from the jet across the field
      const u = (k - SL1) / (1 - SL1), A0 = RUN0, A1 = RUN1;
      const ph = 2 * Math.PI * 1.45 * (lt - SL1 * d), pos = A0.clone().lerp(A1, u);
      pose = addPose(P.run, { armR: [-45 * Math.sin(ph), 0, 0, 0, 0], armL: [45 * Math.sin(ph), 0, 0, 0, 0], spine2: [0, 8 * Math.sin(ph), 0] });
      root = { x: pos.x, z: pos.z, y: 0.93 + 0.04 * Math.abs(Math.sin(ph)), tilt: -10, yaw: Math.atan2(-(A1.x - A0.x), -(A1.z - A0.z)) / D2R };
      walk = { A0, A1, d: d * (1 - SL1), lt: lt - SL1 * d, f: 1.45, stance: 0.38, lift: 0.14 };
      face = { ...face, browIn: 0.7, jaw: 0.35, look: [0, 0] };
    }
  } else if (b === 8) show = false;
  else {                                                     // 9: before it all: calm, looking at his phone (the bang comes in the last 0.6 s, above)
    pose = CALM;
    hands = [{ ...PHONE_H }, gripRest('L')];
    face = { ...face, smile: 0.2, look: [0, -0.6] };
  }
  return { pose, root, face, hands, show, feet, walk, maskOn, maskHeld, beltK, beltPull, bagHeld };
}
function handOverMouth(S) { const m = wpos(MOUTH), f = headFwd(); return { S, p: m.clone().addScaledVector(f, 0.045).add(V(0, -0.045, 0)), n: f.clone().negate(), u: V(0, 1, 0).sub(f.clone().multiplyScalar(f.y)).normalize(), c: 30, mouth: true }; }
// counting rows: the left hand runs along the aisle armrests just ahead of him and dips to touch each one (rows 1-4)
const COUNT_Z = [1, 2, 3, 4].map(k => rowZ(k) - 0.1);
function countHand(zh) {
  const z = zh - 0.45; let w = 0; for (const zc of COUNT_Z) w = Math.max(w, Math.exp(-(((z - zc) / 0.13) ** 2)));
  return { S: 'L', p: V(lerp(-0.16, -0.245, w), 0.705 + 0.11 * (1 - w), z), n: V(0.1, -1, 0).normalize(), u: V(-0.1, -0.3, -1).normalize(), c: 15 };
}
const SL0 = 0.3, SL1 = 0.62;
const CALM = addPose(P.sit, { neck: [-20, 0, 0], head: [-6, 0, 0] });
const PHONE_H = { S: 'R', p: V(ME.x + 0.07, 0.86, -0.24), n: V(-1, 0.35, 0.15).normalize(), u: V(0, 0.6, -1).normalize(), c: 25 };
const slidePt = s => V(-s * Math.cos(SLIDE_ANG), -s * Math.sin(SLIDE_ANG), 0).applyAxisAngle(V(0, 0, 1), 0).add(JDOOR).applyMatrix4(jet.matrixWorld);
let RUN0 = V(0, 0, 0), RUN1 = V(0, 0, 0);
// the mask: where it dangles (beat 1), and the buckle (follows his hips)
function MASKDANGLE(t) { const b = beatAt(t), lt = t - B[b]; const fall = smooth(0.05, 0.3, lt); const bounce = Math.exp(-lt * 3) * Math.sin(lt * 14) * 0.05;
  return MASK_HOME.clone().add(V(0.02 * Math.sin(lt * 3.1), -0.42 * fall + bounce * fall, -0.22 * fall + 0.015 * Math.sin(lt * 2.3))); }
function BUCKLE_AT() { const h = G.bones.hips.getWorldPosition(new THREE.Vector3()); return V(h.x, h.y + 0.095, h.z - 0.165); }

// ------------------------------------------------------------------ the jet's flight (beat 4: comes down and skids; it rests in the field after)
const TOUCH = 0.38;                                              // fraction of the exterior part of beat 4 when the belly hits
const EXT4 = 0.55;                                               // beat 4: exterior until this fraction, then inside
function jetPose(t) {
  const b = beatAt(t), lt = t - B[b];
  if (b === 4) { const te = DUR[4] * EXT4, u = lt / te, ut = u / TOUCH;
    if (u < TOUCH) { const z = lerp(150, 0, ut), y = lerp(14, 0, 1 - (1 - ut) ** 1.6); return { y, z, pitch: lerp(6, 3, ut), roll: 3 * Math.sin(lt * 4) * (1 - ut) }; }
    const v = (u - TOUCH) / (1 - TOUCH), z = -26 * (1 - (1 - Math.min(v, 1.6) / 1.6) ** 2);
    return { y: 0.05 * Math.max(0, Math.sin(lt * 30)) * (1 - Math.min(v, 1)), z, pitch: 3 * (1 - smooth(0, 0.35, v)) - 1.2 * smooth(0.3, 0.6, v), roll: 1.5 * Math.sin(lt * 9) * (1 - Math.min(v, 1)) };
  }
  return { y: 0, z: -26, pitch: -1.2, roll: 0 };
}

// ------------------------------------------------------------------ cameras
function shake(t, a, f = 1) { return V(vn1(t * 3 * f, 1) * a, vn1(t * 3 * f, 2) * a, vn1(t * 3 * f, 3) * a * 0.5); }
const HOOK = { pos: V(0.1, 1.45, -0.55), tgt: V(-0.95, 1.04, 0.02), fov: 56 };
function camAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b], u = lt / d, tt = HT(t);
  let pos, tgt, fov = 46, roll = 0;
  if (b === 0 || (b === 9 && tt < 0)) { const g = smooth(-0.45, 0.0, tt), dec = 1 - smooth(DUR[0] - 1.2, DUR[0], tt);
    pos = HOOK.pos.clone().add(V(0.02 * (tt + PRE), -0.01 * (tt + PRE), -0.03 * (tt + PRE))); tgt = HOOK.tgt.clone(); fov = HOOK.fov;
    pos.add(shake(t, 0.025 * g * dec + 0.004, 4)); roll = 3.5 * g * Math.sin(tt * 1.7 + 0.3) * dec; }
  else if (b === 9) { const w = smooth(d - PRE - 1.4, d - PRE, lt); pos = V(0.08, 1.32, -0.78).lerp(HOOK.pos.clone(), w); tgt = V(-0.62, 1.0, 0.02).lerp(HOOK.tgt, w); fov = lerp(48, HOOK.fov, w); }
  else if (b === 1) { pos = V(0.16, 1.4, -0.86); tgt = V(-0.45, 1.24, -0.02); fov = 46; pos.add(shake(t, 0.01, 3)); roll = 2 * Math.sin(lt * 1.3); }
  else if (b === 2) { pos = V(0.02, 1.08, -0.72 - 0.04 * u); tgt = V(-0.48, 0.6, -0.04); fov = 44; pos.add(shake(t, 0.006, 3)); }
  else if (b === 3) { pos = V(0.72, 1.18, -0.4 + 0.05 * u); tgt = V(-0.46, 0.86, -0.3); fov = 46; pos.add(shake(t, 0.008, 3)); }
  else if (b === 4) {
    if (u < EXT4) { const ut = u / EXT4, jp = jetPose(t); pos = V(JX - 27, 2.0, -22); tgt = V(JX - 2, 2.4 + jp.y * 0.8, jp.z * 0.75 - 3); fov = 46; pos.add(shake(t, 0.35 * smooth(TOUCH, TOUCH + 0.05, ut) * (1 - smooth(TOUCH + 0.1, 1, ut)), 6)); }
    else { const v = (u - EXT4) / (1 - EXT4); pos = V(0.72, 1.18, -0.36); tgt = V(-0.46, 0.86, -0.3); fov = 46; pos.add(shake(t, 0.05 * (1 - smooth(0, 1, v)) + 0.004, 7)); roll = 4 * Math.sin(lt * 20) * (1 - v); } }
  else if (b === 5) { pos = V(0.05, 0.95, -2.0 + 0.2 * u); tgt = V(0.0, 0.95 - 0.25 * smooth(0.3, 0.6, u), 0.25); fov = 48; }
  else if (b === 6) { const gz = wpos(G.bones.hips).z; pos = V(0.2, 1.12, gz + 1.25); tgt = V(-0.18, 0.72, gz - 1.4); fov = 50; }
  else if (b === 7) { if (u < SL0) { pos = V(0.75, 1.25, DOORZ + 1.35); tgt = V(-1.0, 0.65, DOORZ - 0.05); fov = 46; }
    else if (u < SL1) { const m = slidePt(SLIDE_LEN * 0.55); pos = m.clone().add(V(-3.4, 1.3, 4.4)); tgt = m.clone().add(V(-0.4, 0.2, 0)).lerp(wpos(G.bones.hips), 0.75); fov = 44; }
    else { const eng = V(JX - 5.6, 1.0, -28.4), hp = wpos(G.bones.hips); pos = RUN1.clone().add(V(-5.6, 1.5, 2.2)); tgt = hp.clone().lerp(eng, 0.3).add(V(0, 1.2, 0)); fov = 54; } }
  else { pos = STAT.clone().add(V(0, 0.2, 10.4 - 0.5 * u)); tgt = STAT.clone().add(V(0, 0.2, 0)); fov = 40; }
  const punch = b > 0 ? (1 - smooth(0, 0.22, lt)) * 0.07 : 0;
  return { pos, tgt, fov: fov * (1 - punch), roll };
}

// ------------------------------------------------------------------ clipping: body points + props vs solid boxes (seats, armrests, bins, floor, walls, the slide)
const SOLIDS = [];
function solidBox(name, pos, size, rotX = 0, parent = CABIN, allow = []) { const o = new THREE.Object3D(); o.position.copy(pos); o.rotation.x = rotX; parent.add(o); o.updateMatrixWorld(true);
  SOLIDS.push({ name, obj: o, box: new THREE.Box3(size.clone().multiplyScalar(-0.5), size.clone().multiplyScalar(0.5)), allow }); }
for (const s of SEATS) { if (s.z > 0.9 || s.z < -4.0 || Math.abs(s.x) > 1.0) continue;     // the seats he can touch
  const mine = s.x === ME.x && s.z === 0;
  solidBox(mine ? 'his seat cushion' : 'seat cushion', V(s.x, SB.cushY, s.z - 0.02), V(SB.w, SB.cushH, SB.cushD), 0, CABIN, mine ? ['hips'] : []);
  solidBox(mine ? 'his seat back' : 'seat back', V(s.x, SB.backY, s.z + SB.backZ), V(SB.w, SB.backH, SB.backT), SB.tilt, CABIN, mine ? ['chest', 'hips'] : []); }
for (const z of seatRows) { if (z > 0.9 || z < -4.0) continue; for (const x of [-1.195, -0.725, -0.255, 0.255, 0.725]) solidBox('armrest', V(x, 0.63, z - 0.02), V(0.05, 0.06, 0.44)); }
for (const bn of BINS) if (bn.s < 0 && bn.z < 1.5 && bn.z > -5) solidBox('overhead bin', V(-1.12 + -0.18, 1.98, bn.z), V(0.86, 0.42, 1.54));
const BODYPTS = { handR: 0.035, handL: 0.035, farmR: 0.035, farmL: 0.035, uarmR: 0.045, uarmL: 0.045, head: 0.09, chest: 0.12, hips: 0.1, shinR: 0.05, shinL: 0.05, footR: 0.04, footL: 0.04 };
function clipScan() {
  const out = []; if (!G.root.visible) return out;
  const pts = Object.entries(BODYPTS).map(([n, r]) => [n, wpos(G.bones[n]), r]);
  for (const S of ['R', 'L']) for (const f of ['index', 'middle', 'pinky', 'thumb']) pts.push([f + ' tip ' + S, fingerTip(f, S), 0.008]);
  if (mask.visible) pts.push(['mask', mask.position.clone(), 0.04]);
  const inCabin = Math.abs(G.root.position.x) < 50;
  for (const [n, p, r] of pts) {
    const floorY = inCabin ? 0 : (SLIDING ? -99 : 0);
    if (p.y - r < floorY - 0.012) out.push({ what: n, into: inCabin ? 'floor' : 'ground', depth: +((floorY - (p.y - r)) * 100).toFixed(1) });
    if (inCabin) { const rr = Math.hypot(p.x, p.y - CY); if (rr + r > R0 + 0.012 && p.y > 0.05) out.push({ what: n, into: 'cabin wall', depth: +((rr + r - R0) * 100).toFixed(1) }); }
    for (const S of SOLIDS) { if (S.allow.includes(n)) continue; const q = p.clone().applyMatrix4(S.inv), bx = S.box;
      const dx = Math.min(q.x - bx.min.x, bx.max.x - q.x), dy = Math.min(q.y - bx.min.y, bx.max.y - q.y), dz = Math.min(q.z - bx.min.z, bx.max.z - q.z);
      const dd = Math.min(dx, dy, dz) + r; if (dx > -r && dy > -r && dz > -r && dd > 0.012) out.push({ what: n, into: S.name, depth: +(dd * 100).toFixed(1) }); }
    if (SLIDING) { const q = p.clone().applyMatrix4(slide.matrixWorld.clone().invert()); if (q.x < 0 && q.x > -SLIDE_LEN && Math.abs(q.z) < 0.55 && q.y - r < 0.01 - 0.012 && q.y > -0.3) out.push({ what: n, into: 'slide', depth: +((0.01 - (q.y - r)) * 100).toFixed(1) }); }
  }
  return out;
}
let SLIDING = false;
// the hand solver also avoids the seats: elbow, mid-forearm and palm inside any solid near him cost a lot
let NEAR = [];
function handExtra(S, f) { let c = 0; for (const [p, r] of [[f.el, 0.045], [f.el.clone().lerp(f.p, 0.5), 0.04], [f.p, 0.035]]) for (const N of NEAR) {
    const q = p.clone().applyMatrix4(N.inv), bx = N.box; const dx = Math.min(q.x - bx.min.x, bx.max.x - q.x), dy = Math.min(q.y - bx.min.y, bx.max.y - q.y), dz = Math.min(q.z - bx.min.z, bx.max.z - q.z);
    if (dx > -r && dy > -r && dz > -r) { const dd = Math.min(dx, dy, dz) + r; c += (dd / 0.01) ** 2; } }
  return c; }
for (const S of SOLIDS) S.inv = S.obj.matrixWorld.clone().invert();
// fingertips: one segment past the last finger bone, following that bone's own curl (rest-pose segment carried in the bone's frame)
const TIPSEG = {}; G.reset(); G.root.updateMatrixWorld(true);
for (const S of ['R', 'L']) for (const f of ['index', 'middle', 'pinky', 'thumb']) { const b1 = G.bones[f + '1' + S], b2 = G.bones[f + '2' + S];
  TIPSEG[f + S] = wpos(b2).sub(wpos(b1)).multiplyScalar(0.95).applyQuaternion(b2.getWorldQuaternion(new THREE.Quaternion()).invert()); }
const fingerTip = (f, S) => { const b2 = G.bones[f + '2' + S]; return wpos(b2).add(TIPSEG[f + S].clone().applyQuaternion(b2.getWorldQuaternion(new THREE.Quaternion()))); };

// ------------------------------------------------------------------ per-frame update
function update(t, frame = Math.round(t * FPS)) {
  t = ((t % TOTAL) + TOTAL) % TOTAL;
  const b = beatAt(t), lt = t - B[b], d = DUR[b], tt = HT(t), u = lt / d;
  const outside = (b === 4 && u < EXT4) || (b === 7 && u >= SL0);
  // the jet (outside)
  const jp = jetPose(t); jet.position.set(0, jp.y, jp.z); jet.rotation.set(jp.pitch * D2R, 0, jp.roll * D2R); OUT.updateMatrixWorld(true);
  { const s0 = slidePt(0), s1 = slidePt(SLIDE_LEN); RUN0.copy(s1).add(V(-0.6, 0, 0)).setY(0); RUN1.copy(RUN0).add(V(-7.5, 0, 3.5)); }
  // the guy
  SLIDING = b === 7 && u >= SL0 && u < SL1;
  const g = guyAt(t);
  const yaw = g.root.yaw ?? 0;
  applyPose(g.pose, { ...g.root, x: g.root.x ?? HOME.x, y: g.root.y ?? HOME.y, z: g.root.z ?? HOME.z, yaw });
  const flat = yawQ(yaw);
  if (g.walk) { const { A0, A1, d: wd, lt: wl, f, stance, lift } = g.walk; const fwd = A1.clone().sub(A0).setY(0).normalize(), side = V(-fwd.z, 0, fwd.x);
    const L = A1.clone().sub(A0).setY(0).length(), vz = L / wd;
    for (const [S, off, sx] of [['R', 0, 1], ['L', 0.5, -1]]) {
      const cyc = f * wl + off, n = Math.floor(cyc), fr = cyc - n;
      const plant = m => clamp(vz * (m - off + 0.3) / f, -0.2, L + 0.2);
      let s, y = 0.1; if (fr < stance) s = plant(n); else { const uu = (fr - stance) / (1 - stance); s = lerp(plant(n), plant(n + 1), sm(uu)); y += lift * Math.sin(Math.PI * uu); }
      const ft = A0.clone().setY(y).addScaledVector(fwd, s).addScaledVector(side, 0.11 * sx);
      G.legIK(S, ft, ft.clone().addScaledVector(fwd, 1.0).add(V(0, 0.45, 0)), flat); } }
  else if (g.feet) for (const S of ['R', 'L']) { const f = g.feet[S]; G.legIK(S, f, f.clone().add(V(0, 0.6, -0.5).applyQuaternion(flat)), flat); }
  G.root.updateMatrixWorld(true);
  { const sh = wpos(G.bones.chest); NEAR = Math.abs(sh.x) < 50 ? SOLIDS.filter(S => S.obj.position.distanceTo(sh) < 1.3) : []; }
  for (const h of (typeof g.hands === 'function' ? g.hands() : g.hands)) {
    const sol = solveHand(h, 'h' + h.S + b + (h.mouth ? 'm' : '') + (b === 7 ? (u < SL0 ? 'a' : 'b') : ''), frame); setArm(h.S, sol.a); LAST['arm' + h.S] = sol.a; LAST['cost' + h.S] = sol.c;
    const pp = {}; curl(pp, h.S, h.c ?? 30); for (const [n, e] of Object.entries(pp)) G.bones[n].quaternion.copy(G.REST[n].q).multiply(qTmp.setFromEuler(eTmp.set(e[0] * D2R, e[1] * D2R, e[2] * D2R)));
  }
  G.root.updateMatrixWorld(true);
  untwistSafe(); G.face(g.face); G.root.visible = g.show; G.root.updateMatrixWorld(true);
  // the mask: on its string (beats 0-1), in his hand, on his face (beats 1-4)
  const inSeat = b <= 4 || b === 9;
  mask.visible = (b === 1 || g.maskOn) && !outside && b !== 9 && b !== 0;
  if (mask.visible) {
    let mp, mq;
    if (g.maskOn) { mp = wpos(MOUTH).addScaledVector(headFwd(), 0.03); mq = G.bones.head.getWorldQuaternion(new THREE.Quaternion()); }
    else { const dangle = MASKDANGLE(t); mq = new THREE.Quaternion().setFromEuler(new THREE.Euler(0.3 * Math.sin(lt * 2), 0, 0));
      if (g.maskHeld > 0) { const hb = G.bones.handR; hb.updateMatrixWorld(true); const q = hb.getWorldQuaternion(new THREE.Quaternion()); const palm = PALM('R').applyMatrix4(hb.matrixWorld).addScaledVector(HANDREST.R.n.clone().applyQuaternion(q), 0.05);
        mp = dangle.lerp(palm, g.maskHeld); } else mp = dangle; }
    mask.position.copy(mp); mask.quaternion.copy(mq); }
  maskTube.visible = mask.visible && b === 1;
  if (maskTube.visible) { const a = MASK_HOME.clone().add(V(0, 0.02, 0)), e = mask.position.clone(); const m = a.clone().lerp(e, 0.5).add(V(0, -0.05, 0));
    maskTube.geometry.dispose(); maskTube.geometry = new THREE.TubeGeometry(new THREE.CatmullRomCurve3([a, m, e]), 16, 0.006, 5, false); }
  // everyone else's masks: dropped in beats 1-4 (and hanging in the smoke)
  const drop = b >= 1 && b <= 6 ? smooth(0.05, 0.3, b === 1 ? lt : 9) : 0;
  otherMasks.visible = maskStrings.visible = drop > 0 && !outside;
  if (otherMasks.visible) { const m4 = new THREE.Matrix4(); for (let i = 0; i < otherMasks.count; i++) { const o = OM[i], sw = 0.03 * Math.sin(t * 2.1 + o.ph);
      const p = V(o.x + sw, 1.73 - 0.45 * drop + (b === 1 ? Math.exp(-lt * 3) * Math.sin(lt * 14 + o.ph) * 0.05 * drop : 0), o.z - 0.2 * drop);
      m4.compose(p, new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI / 2 + 0.3, 0, 0)), V(1, 1, 1)); otherMasks.setMatrixAt(i, m4);
      const top = V(o.x, 1.73, o.z), mid = top.clone().lerp(p, 0.5), len = top.distanceTo(p);
      m4.compose(mid, new THREE.Quaternion().setFromUnitVectors(V(0, 1, 0), top.clone().sub(p).normalize()), V(1, len, 1)); maskStrings.setMatrixAt(i, m4); }
    otherMasks.instanceMatrix.needsUpdate = true; maskStrings.instanceMatrix.needsUpdate = true; }
  // the lap belt: anchor -> over the left hip -> buckle -> over the right hip -> anchor; tighter after the pull
  belt.visible = buckle.visible = inSeat && !outside && g.show && b !== 5;
  if (belt.visible) { const h = wpos(G.bones.hips), sag = 0.03 * (1 - (b >= 3 ? 1 : b === 2 ? g.beltPull : 0));
    const fwd = V(0, 0, -1).applyQuaternion(G.root.quaternion);
    const bk = h.clone().addScaledVector(fwd, 0.165).add(V(0, 0.095 - sag, 0));
    const pts = [BELT.L, h.clone().add(V(-0.2, 0.03, 0)).addScaledVector(fwd, 0.02), h.clone().add(V(-0.11, 0.085 - sag, 0)).addScaledVector(fwd, 0.14), bk, h.clone().add(V(0.11, 0.085 - sag, 0)).addScaledVector(fwd, 0.14), h.clone().add(V(0.2, 0.03, 0)).addScaledVector(fwd, 0.02), BELT.R];
    belt.geometry.dispose(); belt.geometry = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 40, 0.014, 6, false); belt.scale.set(1, 1, 1);
    buckle.position.copy(bk).addScaledVector(fwd, 0.012); buckle.quaternion.copy(G.root.quaternion); }
  // the bag: in his hand at the door, then dropped
  bagP.visible = b === 7 && u < SL0;
  if (bagP.visible) { if (g.bagHeld) { const hb = G.bones.handR; hb.updateMatrixWorld(true); const p = PALM('R').applyMatrix4(hb.matrixWorld); bagP.position.copy(p).add(V(0, -0.47, 0)); bagP.rotation.set(0, 0.4, 0.05 * Math.sin(t * 3)); BAGDROP = { p: bagP.position.clone(), t }; }
    else { const a = t - BAGDROP.t, y = Math.max(0, BAGDROP.p.y - 4.9 * a * a); bagP.position.set(BAGDROP.p.x, y, BAGDROP.p.z); bagP.rotation.set(0, 0.4, y > 0 ? 0.6 * a : 0.35 * smooth(0, 0.3, a - Math.sqrt(BAGDROP.p.y / 4.9))); } }
  // floating cup and phone (the drop), flying forward (the hit)
  const hook = b === 0 || (b === 9 && tt < 0);
  cup.visible = phoneF.visible = hook || (b === 4 && u >= EXT4) || b === 9;
  const CUP0 = V(-0.96, 0.525, -0.1);                         // the cup sits on the empty middle seat until the drop lifts it
  const phoneInHand = () => { const hb = G.bones.handR; hb.updateMatrixWorld(true); const q = hb.getWorldQuaternion(new THREE.Quaternion());
    return { p: PALM('R').applyMatrix4(hb.matrixWorld).addScaledVector(HANDREST.R.n.clone().applyQuaternion(q), 0.012), q: q.clone().multiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(-Math.PI / 2, 0, 0))) }; };
  if (hook) { const k = smooth(-0.45, 0.4, tt), up = Math.max(0, tt + 0.45);
    cup.position.copy(CUP0).lerp(V(-0.7, 1.0, -0.35), k).add(V(0.03 * up, 0.05 * Math.sin(tt * 2) * k, -0.04 * up)); cup.rotation.set(0.6 * up, 0.3 * up, 0.9 * up);
    cup.userData.drink.position.set(0.02 * Math.sin(tt * 3) * k, lerp(0.04, 0.09 + 0.12, k), 0); cup.userData.drink.scale.set(1 + 0.4 * k, lerp(0.35, 0.7, k), 1 + 0.4 * k);
    const fp = V(ME.x + 0.02, 0.86 + 0.42 * k, -0.24 - 0.05 * up), fq = new THREE.Quaternion().setFromEuler(new THREE.Euler(1.2 * up + 0.4, 0.8 * up, 0.5 * up));
    const w = b === 9 ? smooth(-0.5, -0.25, tt) : 1, hp = phoneInHand();
    phoneF.position.copy(hp.p).lerp(fp, w); phoneF.quaternion.copy(hp.q).slerp(fq, w); }
  else if (b === 9) { cup.position.copy(CUP0); cup.rotation.set(0, 0, 0); cup.userData.drink.position.set(0, 0.04, 0); cup.userData.drink.scale.set(1, 0.35, 1);
    const hp = phoneInHand(); phoneF.position.copy(hp.p); phoneF.quaternion.copy(hp.q); }
  else if (b === 4) { const v = (u - EXT4) / (1 - EXT4); cup.position.set(-1.0, 0.62 + 0.35 * v - 0.9 * v * v, -0.1 - 1.6 * v); cup.rotation.set(5 * v, 2 * v, 0); phoneF.position.set(-1.2, 0.75 + 0.2 * v - 0.7 * v * v, -0.25 - 2.0 * v); phoneF.rotation.set(7 * v, 3 * v, 1); }
  floaters.visible = hook;
  if (hook) { const k = smooth(-0.45, 0.4, tt), m4 = new THREE.Matrix4();
    FL.forEach((f, i) => { const p = f.p.clone().add(V(0.05 * Math.sin(tt * 1.3 + i), (0.35 + 0.3 * f.r) * k + 0.04 * Math.sin(tt * 2 + i), 0.03 * Math.cos(tt + i)));
      m4.compose(p, new THREE.Quaternion().setFromEuler(new THREE.Euler(f.r * 4 * (tt + 0.5) + i, f.r * 3 * (tt + 0.5), i)), f.s); floaters.setMatrixAt(i, m4); });
    floaters.instanceMatrix.needsUpdate = true; }
  // bins: pop open in the drop and the hit
  for (const bn of BINS) { const near = Math.abs(bn.z) < 4; let o = 0;
    if (hook && near) o = smooth(-0.3 + 0.05 * Math.abs(bn.z), 0.2 + 0.05 * Math.abs(bn.z), tt) * (0.8 + 0.2 * Math.sin(tt * 7 + bn.z));
    else if (b >= 1 && b <= 6 && near) o = 0.9 + 0.05 * Math.sin(t * 3 + bn.z) + (b === 4 && u >= EXT4 ? 0.1 * Math.sin(lt * 25 + bn.z) : 0);
    bn.door.rotation.z = -bn.s * 1.6 * o; }
  // the windows: sky drops and tilts in the dive; dark later
  winU.uT.value = t; const dive = hook ? smooth(-0.4, 0.5, tt) : b >= 1 && b <= 3 ? 1 : 0;
  winU.uRoll.value = dive * (0.35 * Math.sin(t * 0.9) + 0.25); winU.uDrop.value = dive * (0.25 + 0.15 * Math.sin(t * 0.6)) + (b === 4 ? 0.6 : 0);
  winU.uFire.value = hook ? smooth(-0.5, -0.2, tt) : b >= 1 && b <= 3 ? 1 : 0;
  winU.uFlash.value = hook ? Math.exp(-(((tt + 0.5) / 0.12) ** 2)) + 0.4 * Math.exp(-(((tt + 0.2) / 0.08) ** 2)) : 0;
  const dark = b === 5 || b === 6 || (b === 7 && u < SL0); winU.uDark.value = dark ? 0.8 : 0;
  // light: normal, flickering in the drop, dark with emergency lights in the smoke
  const flick = hook ? 0.75 + 0.25 * (Math.sin(tt * 37) > 0.6 ? 0 : 1) : 1;
  for (const l of cabinLights) l.intensity = dark ? 0.35 : 5 * flick;
  ceilLight.material.emissiveIntensity = dark ? 0.04 : 1.6 * flick; keyLight.intensity = dark ? 2.5 : 18 * flick;
  pathLights.material.emissiveIntensity = dark ? 2.2 : 0; exitGlow.intensity = dark ? 3 + 0.3 * Math.sin(t * 6) : 0;
  // smoke: a layer that grows down from the ceiling; fog in the cabin
  smoke.m.visible = dark;
  if (dark) { const lo = b === 5 ? lerp(1.9, 1.15, smooth(0, d * 0.7, lt)) : 1.1;
    setCloud(smoke, i => { const x = (hash1(i * 1.7) - 0.5) * 3.2, z = ZF + 1 + hash1(i * 2.3) * (ZB - ZF - 2), y = lo + hash1(i * 3.1) * (2.2 - lo) + 0.06 * Math.sin(t * 0.7 + i);
      return V(x + 0.15 * Math.sin(t * 0.3 + i), y, z + 0.2 * Math.sin(t * 0.2 + i * 1.3)); }); }
  scene.fog = dark ? FOG : null;
  // the door: opens with daylight at the start of beat 7
  const open = b === 7 && u < SL0 ? 1 : 0;
  doorLeaf.rotation.y = 1.45 * open; doorLight.material.opacity = 0.9 * open; dayLight.intensity = 25 * open;
  // outside: the scar in the field, dust, sparks, smoke from the wing
  SCAR.value = b === 4 ? smooth(TOUCH * DUR[4] * EXT4, DUR[4] * EXT4, lt) : b === 7 ? 1 : 0;
  { const te = DUR[4] * EXT4, ut = b === 4 ? lt / te : -1, hit = ut > TOUCH ? ut - TOUCH : -1;
    setCloud(dust, i => { if (hit < 0 || hit > 0.62 || b !== 4) return null; const a0 = hash1(i) * Math.PI, sp = 6 + 10 * hash1(i * 3), age = hit * te * (0.6 + 0.4 * hash1(i * 7));
      const z0 = jp.z + (hash1(i * 5) - 0.3) * 8; return V(JX + Math.cos(a0) * (2 + sp * age) * (hash1(i * 11) > 0.5 ? 1 : -1), 0.3 + sp * age * Math.sin(a0) * 0.6 - 3 * age * age, z0 + 4 * age); });
    setCloud(sparksC, i => { if (hit < 0 || hit > 0.6 || b !== 4) return null; const age = (hit * te * 3 + hash1(i)) % 0.5; return V(JX + (hash1(i * 2) - 0.5) * 3.5, 0.1 + 2.5 * age - 6 * age * age, jp.z + 4 + 12 * age * hash1(i * 4)); });
    const smk = b === 7 && u >= SL0 ? 1 : b === 4 && hit > 0 ? smooth(0.1, 0.6, hit) : 0;
    setCloud(jetSmoke, i => { if (smk <= 0 || i > 260 * smk) return null; const age = (t * 0.25 + hash1(i)) % 1;
      return V(JX - 5.6 + (hash1(i * 3) - 0.5) * (2 + 4 * age) - 2 * age, 1.2 + age * 14, jp.z - 1 + (hash1(i * 5) - 0.5) * (2 + 4 * age) - 11 * age); }); }
  setCloud(fireC, i => { const on = (b === 7 && u >= SL0) || (b === 4 && u < EXT4 && u / EXT4 > TOUCH + 0.1); if (!on) return null; const age = (t * 1.6 + hash1(i)) % 1;
    return V(JX - 5.6 + (hash1(i * 3) - 0.5) * 1.2 * (1 - age), 1.55 + age * 1.8, jp.z - 2.4 + (hash1(i * 5) - 0.5) * 3.2); });
  fireC.m.material.opacity = 0.42 + 0.1 * Math.sin(t * 23);
  setCloud(fireCore, i => { if (!fireC.m.visible) return null; const age = (t * 2.2 + hash1(i * 9)) % 1; return V(JX - 5.6 + (hash1(i * 4) - 0.5) * 0.8 * (1 - age), 1.5 + age * 1.0, jp.z - 2.4 + (hash1(i * 6) - 0.5) * 2.6); });
  slide.visible = jetDoor.visible = b === 7; doorHole.visible = b === 7;
  jetDoor.position.copy(JDOOR).add(V(-0.5, 0.93, 0.95)); jetDoor.rotation.y = 0.2;
  // the stat stage: people pop in, then 95 light up green
  statStage.visible = b === 8;
  if (statStage.visible) { const m4 = new THREE.Matrix4(); let on = 0, off = 0;
    for (let i = 0; i < PEEPS; i++) { const pop = smooth(0.02 * i * d * 0.35 / 2, 0.02 * i * d * 0.35 / 2 + 0.25, lt); const lit = smooth(d * 0.45 + 0.008 * i, d * 0.45 + 0.008 * i + 0.15, lt);
      const isOff = OFFSET.includes(i), sc = Math.max(0.001, pop * (1 + 0.15 * Math.sin(Math.PI * clamp((lt - d * 0.45 - 0.008 * i) / 0.15, 0, 1)) * (isOff ? 0 : 1)));
      m4.compose(PEEP[i], new THREE.Quaternion(), V(sc, sc, sc));
      if (isOff) peepsOff.setMatrixAt(off++, m4); else { peepsOn.setMatrixAt(on++, m4); peepsOn.setColorAt(on - 1, new THREE.Color().lerpColors(new THREE.Color(0x5a5f68), new THREE.Color(0x3fe07a), lit)); } }
    peepsOn.instanceMatrix.needsUpdate = true; peepsOff.instanceMatrix.needsUpdate = true; if (peepsOn.instanceColor) peepsOn.instanceColor.needsUpdate = true;
    peepMatOn.emissiveIntensity = 0.9 * smooth(d * 0.45, d * 0.8, lt); }
  // what is shown where
  CABIN.visible = !outside && b !== 8; OUT.visible = field.visible = outside; sky.visible = outside;
  scene.background = b === 8 ? new THREE.Color(0x050a14) : outside ? null : new THREE.Color(0x0e0f12);
  sun.position.copy(outside ? V(JX, 0, -10) : V(0, 0, 0)).addScaledVector(SUNDIR, 40); sun.target.position.copy(outside ? V(JX, 0, -10) : V(0, 0, 0)); sun.target.updateMatrixWorld(); sun.intensity = outside ? 2.6 : 0;
  { const S = sun.shadow.camera, e = outside ? 18 : 5; if (S.right !== e) { S.left = -e; S.right = e; S.top = e; S.bottom = -e; S.updateProjectionMatrix(); } }
  hemi.intensity = outside ? 0.75 : 0.35;
  const C = camAt(t); camera.position.copy(C.pos); camera.up.set(Math.sin(C.roll * D2R), Math.cos(C.roll * D2R), 0); camera.lookAt(C.tgt); camera.fov = C.fov; camera.updateProjectionMatrix();
  return { beat: b, t };
}
let BAGDROP = { p: V(0, 0.4, DOORZ), t: 0 };
const FOG = new THREE.FogExp2(0x2b2a29, 0.22);
// solve the brace depth once: forehead (just above the eyes) on the forearms against the seat back
{ let lo = 0.3, hi = 1.4;
  for (let it = 0; it < 18; it++) { const k = (lo + hi) / 2; applyPose(bracePose(k), { x: HOME.x, y: HOME.y, z: HOME.z, tilt: BRACE_TILT });
    for (const S of ['R', 'L']) { const f = feetSeat()[S]; G.legIK(S, f, f.clone().add(V(0, 0.6, -0.5)), new THREE.Quaternion()); }
    G.root.updateMatrixWorld(true); const hp = wpos(G.bones.head).add(V(0, 0.07, 0)), front = hp.z - 0.1;
    if (front > frontBackZ(hp.y) + 0.075) lo = k; else hi = k; }
  BRACE_K = (lo + hi) / 2; G.reset(); }
// in-beat hard cuts (beat 4: outside -> inside; beat 7: door -> slide -> run): the rig check treats these like beat changes
const CUTS = [B[4] + DUR[4] * EXT4, B[7] + DUR[7] * SL0, B[7] + DUR[7] * SL1];
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
  SEAM = { hR0: MEM['hR9'].a.slice(), hL0: MEM['hL9'].a.slice() }; }
function stepTo(i) { const t = i / FPS, b = beatAt(((t % TOTAL) + TOTAL) % TOTAL);
  if (SEAM === null) primeSeam();
  if (i === 0 || (b === 0 && i !== lastFrame + 1)) for (const k in SEAM) MEM[k] = { frame: -1, a: SEAM[k].slice() };
  if (i !== lastFrame + 1) { const f0 = Math.max(0, Math.round(B[b] * FPS)); for (let j = f0; j < i; j++) update(j / FPS, j); }
  update(t, i); lastFrame = i; }
function renderInto(i) { stepTo(i); draw(); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); }
window.renderAll = async (f0, f1) => { for (let i = f0; i < f1; i++) { renderInto(i); await fetch('/frame', { method: 'POST', body: px }); } return 'ok'; };
window.renderAtT = t => { stepTo(Math.round(t * FPS)); if (window.CAM) { camera.position.set(...window.CAM.pos); camera.lookAt(...window.CAM.tgt); camera.fov = window.CAM.fov || 42; camera.updateProjectionMatrix(); } draw(); return renderer.domElement.toDataURL('image/png'); };
window.rigReport = i => { stepTo(i); const t = i / FPS;
  return { t, beat: beatAt(t), ang: LAST, hips: G.bones.hips.getWorldPosition(new THREE.Vector3()).toArray(), car: 0, show: G.root.visible, cut: CUTS.some(c => Math.abs(c - t) < 0.5 / FPS),
    thumbs: ['R', 'L'].map(S => G.bones['index1' + S].getWorldPosition(new THREE.Vector3()).sub(G.bones['pinky1' + S].getWorldPosition(new THREE.Vector3())).applyQuaternion(G.root.getWorldQuaternion(new THREE.Quaternion()).invert()).toArray()),
    forearms: ['R', 'L'].map(S => G.bones['hand' + S].getWorldPosition(new THREE.Vector3()).sub(G.bones['farm' + S].getWorldPosition(new THREE.Vector3())).normalize().applyQuaternion(G.root.getWorldQuaternion(new THREE.Quaternion()).invert()).toArray()),
    cost: [LAST.costR ?? null, LAST.costL ?? null], clip: clipScan() }; };
window.clipTest = (i, dz) => { stepTo(i); G.root.position.z += dz; G.root.updateMatrixWorld(true); const r = clipScan(); stepTo(i); return r; };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS);
window.READY = true;
