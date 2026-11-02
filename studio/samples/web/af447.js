// "This airliner just fell 38,000 feet in three and a half minutes, with its nose pointed up." - Air France 447 (June 1, 2009), an Airbus A330-200.
// Facts from the BEA final report (July 5, 2012): pitot icing, autopilot off at 02:10:05, climb to ~38,000 ft, stall, 3 min 30 s descent at ~10,900 ft/min,
// impact 02:14:28 nose 16 deg up; 228 aboard; recorders found May 2011 at ~3,980 m. No people shown. af447.html?w=1080&h=1920
import * as THREE from 'three';
import { makeLook } from '/look.js';
import { makeLearjet60 } from '/jetmodel.js';
import { makeA330 } from '/a330model.js';

const Q = new URLSearchParams(location.search);
const W = +Q.get('w') || 720, H = +Q.get('h') || 1280, FPS = 30;
const TIMES = await (await fetch('/af447/times.json')).json();
const B = TIMES.starts, DUR = TIMES.durs, TOTAL = TIMES.total;
const beatAt = t => { let i = 0; for (let k = 0; k < B.length; k++) if (t >= B[k]) i = k; return i; };
const clamp = (x, a, b) => Math.min(Math.max(x, a), b), lerp = (a, b, u) => a + (b - a) * u;
const sm = x => x * x * (3 - 2 * x), smooth = (a, b, x) => sm(clamp((x - a) / (b - a), 0, 1));
const D2R = Math.PI / 180, FT = 0.3048;
function hash1(n) { const s = Math.sin(n * 127.1) * 43758.5453; return s - Math.floor(s); }
function vn1(x, seed) { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return lerp(hash1(i + seed * 17.3), hash1(i + 1 + seed * 17.3), u) * 2 - 1; }
const V = (x, y, z) => new THREE.Vector3(x, y, z);
const LOOKON = Q.get('look') !== '0';

// ------------------------------------------------------------------ renderer, camera, light
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(W, H);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.0; renderer.outputColorSpace = THREE.SRGBColorSpace;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(40, W / H, 0.3, 400000); scene.add(camera);
const SUN = V(0.62, 0.7, 0.35).normalize();                         // south (+x) and high: 12:50 pm in November, flying east (-z)
{ const pm = new THREE.PMREMGenerator(renderer), es = new THREE.Scene();
  const sk = new THREE.Mesh(new THREE.SphereGeometry(10, 32, 16), new THREE.ShaderMaterial({ side: THREE.BackSide, vertexShader: 'varying vec3 d; void main(){ d = normalize(position); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }',
    fragmentShader: 'varying vec3 d; void main(){ float h = d.y; vec3 c = h > 0. ? mix(vec3(.75,.84,.95), vec3(.25,.45,.8), pow(h,.6)) : mix(vec3(.75,.8,.86), vec3(.92,.93,.95), pow(-h,.5)); gl_FragColor = vec4(c,1.); }' }));
  es.add(sk); scene.environment = pm.fromScene(es, 0.02).texture; scene.environmentIntensity = 0.55; }
const hemi = new THREE.HemisphereLight(0xcfe2ff, 0x8a8f99, 0.9); scene.add(hemi);
const sun = new THREE.DirectionalLight(0xfff3e2, 3.0); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -45, right: 45, top: 45, bottom: -45, near: 1, far: 280 }); sun.shadow.bias = -0.0003; sun.shadow.normalBias = 0.04;
scene.add(sun, sun.target);

// ------------------------------------------------------------------ the jet
const J = makeA330(THREE), jet = J.root, JP = J.parts; scene.add(jet);
const LJ = makeLearjet60(THREE); scene.add(LJ.root); LJ.root.visible = false;   // the Florida jet (last beat)
if (Q.get('nocc')) jet.traverse(o => { if (o.isMesh && o.material.clearcoat) o.material.clearcoat = 0; });
if (Q.get('flip')) jet.traverse(o => { if (o.isMesh && o.material.side === THREE.DoubleSide) o.material.side = THREE.FrontSide; });

// ------------------------------------------------------------------ sky dome (follows the camera); uDark = inside the storm
const MOON = V(-0.35, 0.62, -0.7).normalize();
const skyU = { uSun: { value: SUN }, uDark: { value: 0 }, uLow: { value: 0 }, uNight: { value: 0 }, uMoon: { value: MOON } };
const sky = new THREE.Mesh(new THREE.SphereGeometry(300000, 48, 24), new THREE.ShaderMaterial({ uniforms: skyU, side: THREE.BackSide, depthWrite: false, fog: false,
  vertexShader: 'varying vec3 d; void main(){ d = normalize(position); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }',
  fragmentShader: `uniform vec3 uSun, uMoon; uniform float uDark, uLow, uNight; varying vec3 d;
    float sh(vec3 p){ p = fract(p * 443.897); p += dot(p, p.yzx + 19.19); return fract((p.x + p.y) * p.z); }
    void main(){ float h = d.y; vec3 zen = mix(vec3(.06,.22,.58), vec3(.3,.48,.75), uLow), hor = mix(vec3(.62,.75,.9), vec3(.8,.84,.87), uLow);
      vec3 c = h > 0. ? mix(hor, zen, pow(clamp(h,0.,1.), .55)) : mix(hor, vec3(.55,.62,.7), pow(clamp(-h,0.,1.), .35));
      float s = max(dot(d, uSun), 0.); c += vec3(1.,.93,.8) * (pow(s, 900.) * 6. + pow(s, 12.) * .18) * (1. - uDark);
      c = mix(c, vec3(.42,.45,.5) * (.8 + .25 * h), uDark);
      vec3 nc = mix(vec3(.025,.04,.08), vec3(.004,.008,.022), pow(clamp(h, 0., 1.), .5)); if (h < 0.) nc = vec3(.012,.018,.032);
      vec3 q = floor(d * 380.); float st = step(.9975, sh(q)) * smoothstep(0., .25, h); nc += vec3(.8,.85,1.) * st * (.5 + .5 * sh(q + 7.));
      float m = max(dot(d, uMoon), 0.); nc += vec3(.9,.93,1.) * (smoothstep(.99955, .9997, m) * 2.5 + pow(m, 60.) * .06);
      nc = mix(nc, vec3(.03,.035,.045), uDark * .8);
      c = mix(c, nc, uNight);
      gl_FragColor = vec4(c, 1.);
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
    }` }));
sky.renderOrder = -10; scene.add(sky);

// ------------------------------------------------------------------ cloud deck: a big shader sheet (tops lit, gaps show the haze below)
const GLN = `float hh(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
  float vn(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f*f*(3.0-2.0*f); return mix(mix(hh(i), hh(i+vec2(1,0)), u.x), mix(hh(i+vec2(0,1)), hh(i+vec2(1,1)), u.x), u.y); }
  float fbm(vec2 p){ float a = .5, s = 0.; for (int i = 0; i < 6; i++){ s += a * vn(p); p = p * 2.03 + vec2(17.1, 9.2); a *= .5; } return s; }`;
const deckU = { uTravel: { value: 0 }, uCam: { value: V(0, 0, 0) }, uSun: { value: SUN }, uDark: { value: 0 }, uCov: { value: 0.5 }, uNight: { value: 0 } };
const deck = new THREE.Mesh(new THREE.PlaneGeometry(500000, 500000, 1, 1).rotateX(-Math.PI / 2), new THREE.ShaderMaterial({ uniforms: deckU, transparent: true, depthWrite: false, fog: false,
  vertexShader: 'varying vec3 w; void main(){ vec4 p = modelMatrix * vec4(position,1.); w = p.xyz; gl_Position = projectionMatrix * viewMatrix * p; }',
  fragmentShader: `${GLN} uniform float uTravel, uDark, uCov, uNight; uniform vec3 uCam, uSun; varying vec3 w;
    void main(){ vec2 p = vec2(w.x, w.z - uTravel) / 2600.;
      float n = fbm(p), n2 = fbm(p * 3.1 + 4.0);
      float cov = smoothstep(uCov - .08, uCov + .14, n);
      float lit = .62 + .5 * smoothstep(.35, .85, n2) * smoothstep(uCov, uCov + .3, n);
      vec3 c = mix(vec3(.55,.6,.68), vec3(1.), lit); c *= mix(1., .55, uDark);
      float d = length(w.xz - uCam.xz); vec3 hz = mix(vec3(.74,.82,.92), vec3(.45,.48,.52), uDark);
      c = mix(c, hz, smoothstep(20000., 140000., d)); c *= mix(vec3(1.), vec3(.11,.13,.2), uNight); float a = cov * (1. - smoothstep(150000., 240000., d));
      gl_FragColor = vec4(c, a);
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
    }` }));
deck.renderOrder = -9; scene.add(deck);

// ------------------------------------------------------------------ puffs: camera-facing soft cloud sprites (storm tower, wisps, smoke), sorted far to near
function puffTex() { const c = document.createElement('canvas'); c.width = c.height = 256; const g = c.getContext('2d');
  for (let i = 0; i < 26; i++) { const a = hash1(i * 3.1) * Math.PI * 2, r = 30 + 55 * hash1(i * 7.7), x = 128 + Math.cos(a) * r * 0.9, y = 128 + Math.sin(a) * r * 0.8, rr = 38 + 40 * hash1(i * 1.9);
    const gr = g.createRadialGradient(x, y, 0, x, y, rr); const v = Math.round(200 + 55 * (1 - (y - 40) / 180)); gr.addColorStop(0, `rgba(${v},${v},${v},0.55)`); gr.addColorStop(1, `rgba(${v},${v},${v},0)`); g.fillStyle = gr; g.fillRect(0, 0, 256, 256); }
  const id = g.getImageData(0, 0, 256, 256); for (let y = 0; y < 256; y++) for (let x = 0; x < 256; x++) { const k = (y * 256 + x) * 4, r = Math.hypot(x - 128, y - 128) / 128; id.data[k + 3] *= clamp(1.25 - r * 1.25, 0, 1); }
  g.putImageData(id, 0, 0); const t = new THREE.CanvasTexture(c); return t; }
const PUFFMAX = 900;
const pGeo = new THREE.InstancedBufferGeometry(); { const b = new THREE.PlaneGeometry(1, 1); pGeo.index = b.index; pGeo.setAttribute('position', b.attributes.position); pGeo.setAttribute('uv', b.attributes.uv); }
const iP = new THREE.InstancedBufferAttribute(new Float32Array(PUFFMAX * 4), 4), iC = new THREE.InstancedBufferAttribute(new Float32Array(PUFFMAX * 4), 4);
iP.setUsage(THREE.DynamicDrawUsage); iC.setUsage(THREE.DynamicDrawUsage); pGeo.setAttribute('iP', iP); pGeo.setAttribute('iC', iC); pGeo.instanceCount = 0;
const puffU = { map: { value: puffTex() }, uFog: { value: new THREE.Color(0x7d848d) }, uFogD: { value: 0 } };
const puffs = new THREE.Mesh(pGeo, new THREE.ShaderMaterial({ uniforms: puffU, transparent: true, depthWrite: false, fog: false,
  vertexShader: `attribute vec4 iP; attribute vec4 iC; varying vec2 vUv; varying vec4 vC; varying float vD;
    void main(){ vUv = uv; vC = iC; vec4 mv = modelViewMatrix * vec4(iP.xyz, 1.); float a = iP.x * .0137 + iP.z * .0071; mat2 R = mat2(cos(a), -sin(a), sin(a), cos(a));
      mv.xy += R * position.xy * iP.w; vD = -mv.z; gl_Position = projectionMatrix * mv; }`,
  fragmentShader: `uniform sampler2D map; uniform vec3 uFog; uniform float uFogD; varying vec2 vUv; varying vec4 vC; varying float vD;
    void main(){ vec4 t = texture2D(map, vUv); float a = t.a * vC.a; a *= smoothstep(0.5, 6.0, vD); if (a < .003) discard;
      vec3 c = vC.rgb * mix(.78, 1.08, t.r); float f = 1. - exp(-uFogD * uFogD * vD * vD); c = mix(c, uFog, f);
      gl_FragColor = vec4(c, a);
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
    }` }));
puffs.frustumCulled = false; puffs.renderOrder = 5; scene.add(puffs);
let PL = [], PK = [1, 1, 1];                                     // PK: light on the puffs (moonlight at night)                                                         // this frame's puffs: [x, y, z, size, r, g, b, a]
function commitPuffs() { const cp = camera.position; PL.sort((a, b) => ((b[0] - cp.x) ** 2 + (b[1] - cp.y) ** 2 + (b[2] - cp.z) ** 2) - ((a[0] - cp.x) ** 2 + (a[1] - cp.y) ** 2 + (a[2] - cp.z) ** 2));
  const n = Math.min(PL.length, PUFFMAX); for (let i = 0; i < n; i++) { const q = PL[i]; iP.setXYZW(i, q[0], q[1], q[2], q[3]); iC.setXYZW(i, q[4] * PK[0], q[5] * PK[1], q[6] * PK[2], q[7]); }
  pGeo.instanceCount = n; iP.needsUpdate = iC.needsUpdate = true; PL = []; }
// storm tower (local: base at y 0, around the axis), shaded top-lit and sun-side-lit
const STORM = []; for (let i = 0; i < 560; i++) { const h = Math.pow(hash1(i * 1.37), 0.9), anv = smooth(0.8, 0.95, h);
  const Rmax = lerp(4300 * (1 - 0.18 * h), 11500, anv), r = Rmax * (i % 4 ? 0.72 + 0.28 * Math.sqrt(hash1(i * 2.91)) : 0.5 * hash1(i * 2.91)), a = hash1(i * 5.3) * Math.PI * 2;   // most on the surface (cauliflower edge), a few inside
  const y = anv > 0.3 ? 6100 + 900 * hash1(i * 8.1) : h * 7200 + 300 * hash1(i * 6.6);
  const dir = V(Math.cos(a), anv > 0.3 ? 0.6 : 0.15, Math.sin(a)).normalize(), side = dir.dot(SUN);
  const sh = clamp(0.28 + 0.5 * h + 0.42 * Math.max(side, 0) - 0.08 * Math.max(-side, 0), 0.2, 1.15);
  STORM.push([V(Math.cos(a) * r, y, Math.sin(a) * r * 0.85), (1100 + 900 * hash1(i * 4.4)) * (1 + 0.5 * anv), sh]); }
// a thunderhead: base on the cloud deck (off.y), ~7 km tall, flat anvil ~11 km across; shaded from the top and the sun side
function addStorm(off, alpha = 0.7, dark = 1, k = 1) { for (const [p, s, sh] of STORM) { const v = sh * dark; PL.push([off.x + p.x * k, off.y + p.y * k, off.z + p.z * k, s * k, v * 0.97, v, v * 1.04, alpha]); } }
// wisps: cloud chunks streaming past the jet (speed), in the air-flow direction
const WISP = []; for (let i = 0; i < 70; i++) WISP.push([V(hash1(i * 1.1) - 0.5, hash1(i * 2.3) - 0.5, hash1(i * 3.7)), 18 + 40 * hash1(i * 4.9), hash1(i * 6.1)]);
function addWisps(t, flow, speed, box, shade = 0.85, alpha = 0.32, center = V(0, 0, 0)) {
  const f = flow.clone().normalize(), a = Math.abs(f.y) < 0.9 ? V(0, 1, 0) : V(1, 0, 0), s1 = new THREE.Vector3().crossVectors(f, a).normalize(), s2 = new THREE.Vector3().crossVectors(f, s1);
  for (const [u, s, k] of WISP) { const along = (((u.z * box * 2 + speed * t) % (box * 2)) + box * 2) % (box * 2) - box;
    const p = center.clone().addScaledVector(s1, u.x * box * 0.7).addScaledVector(s2, u.y * box * 0.5).addScaledVector(f, along);
    const fade = 1 - smooth(box * 0.7, box, Math.abs(along)); const v = shade * (0.85 + 0.2 * k); PL.push([p.x, p.y, p.z, s * (box / 220), v, v, v * 1.03, alpha * fade]); } }
// smoke from the crash site (ground stage): rises and drifts east-north-east, dark
function addSmoke(tSince, at) { if (tSince <= 0) return; for (let i = 0; i < 140; i++) { const born = i * 0.045; if (tSince < born) break; const age = tSince - born;
  const p = V(at.x + age * 7 + (hash1(i) - 0.5) * 24, at.y + 6 + age * (16 + 8 * hash1(i * 2)), at.z - age * 3 + (hash1(i * 3) - 0.5) * 24), sz = 22 + age * 16;
  const v = lerp(0.12, 0.3, clamp(age / 5, 0, 1)); PL.push([p.x, p.y, p.z, sz, v, v * 0.98, v * 0.96, 0.75 * (1 - smooth(5, 9, age))]); }
  for (let i = 0; i < 16; i++) { const age = (tSince * 1.4 + i * 0.37) % 1.6, p = V(at.x + (hash1(i * 9) - 0.5) * 26, at.y + 4 + age * 14, at.z + (hash1(i * 5) - 0.5) * 26);
    PL.push([p.x, p.y, p.z, 14 + age * 10, 1.6, 0.62, 0.2, 0.5 * (1 - age / 1.6) * smooth(0, 0.3, tSince)]); } }

// ------------------------------------------------------------------ streaks: rain / ice crystals rushing past (a box that follows the camera)
const NSTR = 1400, strSeed = new Float32Array(NSTR * 2 * 3), strEnd = new Float32Array(NSTR * 2);
for (let i = 0; i < NSTR; i++) for (let e = 0; e < 2; e++) { strSeed.set([hash1(i * 1.3), hash1(i * 2.7), hash1(i * 4.1)], (i * 2 + e) * 3); strEnd[i * 2 + e] = e; }
const strGeo = new THREE.BufferGeometry(); strGeo.setAttribute('position', new THREE.BufferAttribute(strSeed, 3)); strGeo.setAttribute('e', new THREE.BufferAttribute(strEnd, 1));
const strU = { uCam: { value: V(0, 0, 0) }, uFlow: { value: V(0, 0, 1) }, uT: { value: 0 }, uBox: { value: 24 }, uLen: { value: 2.5 }, uA: { value: 0.0 }, uSpeed: { value: 120 } };
const streaks = new THREE.LineSegments(strGeo, new THREE.ShaderMaterial({ uniforms: strU, transparent: true, depthWrite: false, fog: false,
  vertexShader: `attribute float e; uniform vec3 uCam, uFlow; uniform float uT, uBox, uLen, uSpeed; varying float vA;
    void main(){ vec3 p = position * uBox - uBox * .5; p += uFlow * uSpeed * uT; p = mod(p + uBox * .5, uBox) - uBox * .5; vA = 1. - smoothstep(uBox * .3, uBox * .5, length(p));
      p += uFlow * uLen * e; gl_Position = projectionMatrix * viewMatrix * vec4(uCam + p, 1.); }`,
  fragmentShader: 'uniform float uA; varying float vA; void main(){ gl_FragColor = vec4(vec3(.92,.95,1.), uA * vA); }' }));
streaks.frustumCulled = false; streaks.renderOrder = 6; scene.add(streaks);

// ------------------------------------------------------------------ the dark stage (beat 7): grid floor
const stage = new THREE.Group(); scene.add(stage); stage.visible = false;
{ const gh = new THREE.GridHelper(80, 40, 0x2f86b8, 0x1a3c58); gh.position.set(0, -3.2, -16); stage.add(gh); }   // kept in front of the camera: lines running behind it fanned out into big blue wedges

function arrowMesh(color, op = 0.85, emis = 0.35) { const s = new THREE.Shape(); s.moveTo(-0.32, 1.6); s.lineTo(0.32, 1.6); s.lineTo(0.32, 0.55); s.lineTo(0.85, 0.55); s.lineTo(0, -0.55); s.lineTo(-0.85, 0.55); s.lineTo(-0.32, 0.55); s.closePath();
  const geo = new THREE.ExtrudeGeometry(s, { depth: 0.22, bevelEnabled: true, bevelThickness: 0.05, bevelSize: 0.05, bevelSegments: 3 }); geo.translate(0, 0, -0.11);
  return new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: emis, roughness: 0.4, transparent: true, opacity: op })); }
// ice crystals streaming into the pitot tube (beat 10) and the ice plug inside it
const crystals = new THREE.InstancedMesh(new THREE.OctahedronGeometry(0.0032, 0), new THREE.MeshStandardMaterial({ color: 0xf2f8ff, emissive: 0x9fb8d0, emissiveIntensity: 0.4, roughness: 0.2 }), 260); jet.add(crystals); crystals.visible = false;
const plug = new THREE.Mesh(new THREE.CylinderGeometry(0.0125, 0.0125, 0.05, 16).rotateX(Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0xf4f9ff, roughness: 0.85, emissive: 0x6080a0, emissiveIntensity: 0.15 }));
JP.pitotR.add(plug); plug.position.copy(JP.pitotTipR).add(V(0, 0, 0.01)); plug.visible = false;
// ------------------------------------------------------------------ overlays stuck to the camera: the readout (HUD), the radar chart, the flash
const hudC = document.createElement('canvas'); hudC.width = 520; hudC.height = 440; const hudT = new THREE.CanvasTexture(hudC); hudT.colorSpace = THREE.SRGBColorSpace;
const hud = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: hudT, transparent: true, depthTest: false, depthWrite: false, toneMapped: false }));
hud.renderOrder = 30; camera.add(hud); hud.visible = false;
const chC = document.createElement('canvas'); chC.width = 1080; chC.height = 1920; const chT = new THREE.CanvasTexture(chC); chT.colorSpace = THREE.SRGBColorSpace;
const chart = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: chT, depthTest: false, depthWrite: false, toneMapped: false }));
chart.renderOrder = 29; camera.add(chart); chart.visible = false;
const flash = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0, depthTest: false, depthWrite: false, toneMapped: false }));
flash.renderOrder = 31; camera.add(flash); flash.visible = false;
function fitOverlays() { const d = camera.near * 1.6, h = 2 * d * Math.tan(camera.fov * D2R / 2), w = h * camera.aspect;
  const gw = 0.4 * w, gh = gw * 440 / 520; hud.scale.set(gw, gh, 1); hud.position.set(w / 2 - gw / 2 - 0.035 * w, h / 2 - 0.165 * h - gh / 2, -d);
  chart.scale.set(w, h, 1); chart.position.set(0, 0, -d * 1.02); flash.scale.set(w * 1.1, h * 1.1, 1); flash.position.set(0, 0, -d * 0.98);
  }   // invisible-but-drawn ice made NaN (black dashes) in the film pass
const fmt = n => Math.round(n).toLocaleString('en-US');
function rr(g, x, y, w, h, r) { g.beginPath(); g.roundRect(x, y, w, h, r); }
// rows: [label, value, color]; flag: big text box (red); tape: 0..1 speed pointer with a red zone over .72
function drawHud(rows, flag, tape) { const g = hudC.getContext('2d'); g.clearRect(0, 0, 520, 440);
  rr(g, 6, 6, 508, 428, 34); g.fillStyle = 'rgba(8,14,22,0.72)'; g.fill(); g.lineWidth = 4; g.strokeStyle = 'rgba(160,200,235,0.55)'; g.stroke();
  let y = 30; const tw = tape != null ? 120 : 0;
  for (const [lab, val, col] of rows) { g.fillStyle = '#9fb6c8'; g.font = '600 34px Arial, Helvetica, sans-serif'; g.fillText(lab, 34, y + 38);
    g.fillStyle = col || '#ffffff'; g.font = 'bold 66px Arial, Helvetica, sans-serif'; g.fillText(val, 34, y + 104, 520 - 34 - 30 - tw); y += 120; }   // maxWidth: long values (TX TO BAHAMAS) ran out of the box
  if (tape != null) { const x0 = 520 - 40 - 70, y0 = 40, hh = 360; g.fillStyle = 'rgba(255,255,255,0.08)'; g.fillRect(x0, y0, 70, hh);
    for (let k = 0; k < 14; k++) { const yy = y0 + hh * (k / 13); if (k / 13 < 0.28) { g.fillStyle = k % 2 ? '#e33' : '#fff'; g.fillRect(x0, yy, 70, hh / 13 / 1); } }
    g.fillStyle = 'rgba(255,255,255,0.65)'; for (let k = 0; k <= 13; k++) g.fillRect(x0, y0 + hh * k / 13, 18, 3);
    const py = y0 + hh * (1 - clamp(tape, 0, 1)); g.fillStyle = tape > 0.72 ? '#ff3b30' : '#ffd23a'; g.beginPath(); g.moveTo(x0 - 4, py); g.lineTo(x0 - 40, py - 20); g.lineTo(x0 - 40, py + 20); g.fill();
    g.fillStyle = '#9fb6c8'; g.font = '600 26px Arial, Helvetica, sans-serif'; g.fillText('SPEED', x0 - 14, y0 + hh + 34); }
  if (flag) { g.font = 'bold 56px Arial, Helvetica, sans-serif'; const fw = Math.min(460 - tw, g.measureText(flag).width + 40); rr(g, 30, 440 - 100, fw, 76, 16); g.fillStyle = '#d9241b'; g.fill();
    g.fillStyle = '#fff'; g.fillText(flag, 50, 440 - 42, fw - 40); }
  hudT.needsUpdate = true; }

// ================================================================== AIR FRANCE 447 (June 1, 2009): stages, explainers, shots
const _m4 = new THREE.Matrix4(), _e = new THREE.Euler();
// ------------------------------------------------------------------ night ocean: dark water with moon glitter (y set per shot)
const oceanU = { uT: { value: 0 }, uCam: { value: V(0, 0, 0) }, uMoon: { value: MOON } };
const ocean = new THREE.Mesh(new THREE.PlaneGeometry(400000, 400000).rotateX(-Math.PI / 2), new THREE.ShaderMaterial({ uniforms: oceanU, fog: false,
  vertexShader: 'varying vec3 w; void main(){ vec4 p = modelMatrix * vec4(position,1.); w = p.xyz; gl_Position = projectionMatrix * viewMatrix * p; }',
  fragmentShader: `${GLN} uniform float uT; uniform vec3 uCam, uMoon; varying vec3 w;
    void main(){ vec2 p = w.xz / 40.; float n = fbm(p + vec2(uT * .05, uT * .03)) + .5 * fbm(p * 3.7 - uT * .1);
      vec3 v = normalize(w - uCam), nn = normalize(vec3((n - .7) * .35, 1., (fbm(p.yx * 1.3) - .5) * .35)), r = reflect(v, nn);
      float g = pow(max(dot(r, uMoon), 0.), 220.) * 3.5 + pow(max(dot(r, uMoon), 0.), 12.) * .06;
      float d = length(w.xz - uCam.xz); vec3 c = vec3(.004,.01,.02) + vec3(.02,.035,.05) * n + vec3(.75,.8,.95) * g;
      c = mix(c, vec3(.02,.03,.05), smoothstep(3000., 60000., d));
      gl_FragColor = vec4(c, 1.);
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
    }` }));
ocean.renderOrder = -8; ocean.visible = false; scene.add(ocean);
// ------------------------------------------------------------------ the deep sea (beat 11): the seafloor at ~3,980 m, a recorder lit by an ROV lamp, marine snow
const deep = new THREE.Group(); deep.visible = false; scene.add(deep);
{ const fl = new THREE.Mesh(new THREE.PlaneGeometry(200, 200, 120, 120).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0x6f6a5e, roughness: 1 }));
  const pa = fl.geometry.attributes.position; for (let i = 0; i < pa.count; i++) { const x = pa.getX(i), z = pa.getZ(i); pa.setY(i, 0.25 * vn1(x * 0.3, 2) * vn1(z * 0.3, 5) + 0.08 * Math.sin(x * 1.7 + z * 0.9)); } fl.geometry.computeVertexNormals(); fl.receiveShadow = true; deep.add(fl);
  // the recorder: orange box, white stripes (the real ones are painted "international orange"), half sunk, plus twisted debris
  const rec = new THREE.Group(); rec.position.set(0, 0.12, 0); rec.rotation.set(0.12, 0.7, -0.18); deep.add(rec);
  const om = new THREE.MeshStandardMaterial({ color: 0xff5a1a, roughness: 0.55 }); const body = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.17, 0.3), om); body.castShadow = true; rec.add(body);
  const drum = new THREE.Mesh(new THREE.CylinderGeometry(0.075, 0.075, 0.2, 24).rotateZ(Math.PI / 2), om); drum.position.set(0.12, 0.16, 0); rec.add(drum);
  for (const x of [-0.12, 0.05]) { const st = new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.175, 0.305), new THREE.MeshStandardMaterial({ color: 0xf2f2ee, roughness: 0.6 })); st.position.x = x; rec.add(st); }
  const beacon = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 0.14, 12).rotateZ(Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0x777b80, metalness: 0.8, roughness: 0.3 })); beacon.position.set(-0.32, 0.03, 0); rec.add(beacon);
  for (let i = 0; i < 14; i++) { const d = new THREE.Mesh(new THREE.BoxGeometry(0.3 + 1.2 * hash1(i), 0.02 + 0.05 * hash1(i * 2), 0.2 + 0.8 * hash1(i * 3)), new THREE.MeshStandardMaterial({ color: i % 3 ? 0x8c9096 : 0xd8d8d4, roughness: 0.6, metalness: 0.4 }));
    d.position.set((hash1(i * 5) - 0.5) * 14, 0.05, -2 - hash1(i * 7) * 12); d.rotation.set(hash1(i) - 0.5, hash1(i * 9) * 6, hash1(i * 11) - 0.5); deep.add(d); }
  const lamp = new THREE.SpotLight(0xdfeeff, 60, 18, 0.42, 0.6, 1.6); lamp.position.set(-1.2, 2.6, 2.2); lamp.target.position.set(0, 0, 0); lamp.castShadow = true; deep.add(lamp, lamp.target); }
const SNOW = new THREE.Points(new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute(Array.from({ length: 1800 }, (_, i) => (hash1(i * 1.3 + (i % 3) * 7) - 0.5) * [10, 5, 10][i % 3]), 3)),
  new THREE.PointsMaterial({ color: 0xb8c8d0, size: 0.025, transparent: true, opacity: 0.7, depthWrite: false })); deep.add(SNOW);
// ------------------------------------------------------------------ airflow over the right wing (beat 6): smooth lines that break up and swirl in the stall
const FLOWN = 14, FLOWP = 60, flowPos = [], flowAl = [], flowSeed = [];
{ const secs = JP.wingSecs(1); for (let k = 0; k < FLOWN; k++) { const S = secs[1 + Math.floor(k * 11 / FLOWN)];
    for (let j = 0; j < FLOWP; j++) for (const e of [0, 1]) { const u = (j + e) / FLOWP, x = -0.25 + 1.45 * u;   // from in front of the leading edge to past the trailing edge (chords)
      const xc = clamp(x, 0, 1), yt = 5 * 0.12 * (0.2969 * Math.sqrt(xc) - 0.126 * xc - 0.3516 * xc * xc + 0.2843 * xc ** 3 - 0.1036 * xc ** 4) + 0.03 * Math.sin(Math.PI * xc);
      flowPos.push(S.o.x, S.o.y + (yt + 0.02) * S.c + (x < 0 ? -x * 0.1 * S.c : 0), S.o.z + x * S.c); flowAl.push(u); flowSeed.push(k); } } }
const flowGeo = new THREE.BufferGeometry(); flowGeo.setAttribute('position', new THREE.Float32BufferAttribute(flowPos, 3)); flowGeo.setAttribute('al', new THREE.Float32BufferAttribute(flowAl, 1)); flowGeo.setAttribute('sd', new THREE.Float32BufferAttribute(flowSeed, 1));
const flowU = { uT: { value: 0 }, uSep: { value: 0 }, uA: { value: 0 } };
const flow = new THREE.LineSegments(flowGeo, new THREE.ShaderMaterial({ uniforms: flowU, transparent: true, depthWrite: false,
  vertexShader: `attribute float al, sd; uniform float uT, uSep; varying float vAl, vSd;
    void main(){ vAl = al; vSd = sd; vec3 p = position; float sep = uSep * smoothstep(.22, .55, al);           // past ~1/3 chord the flow tears off the wing
      float a = al * 22. - uT * 9. + sd * 1.7; p.y += sep * (1.2 + .9 * sin(a) + .5 * sin(a * 2.3 + sd)); p.z += sep * .9 * cos(a * 1.3); p.x += sep * .5 * sin(a * .7 + sd * 3.);
      gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.); }`,
  fragmentShader: `uniform float uT, uSep, uA; varying float vAl, vSd;
    void main(){ float dash = step(.35, fract(vAl * 9. - uT * 2.2 + vSd * .37)); float a = uA * dash * smoothstep(0., .06, vAl) * (1. - smoothstep(.9, 1., vAl));
      vec3 c = mix(vec3(.55,.9,1.), vec3(1.,.45,.35), uSep * smoothstep(.25, .5, vAl)); gl_FragColor = vec4(c * 1.4, a);
      #include <colorspace_fragment>
    }` }));
flow.renderOrder = 9; flow.visible = false; jet.add(flow);
// ------------------------------------------------------------------ "lower the nose" arrow (beat 9) and a ghost of the jet nose-down
const noseArrow = new THREE.Group(); { const pts = new THREE.EllipseCurve(0, 0, 9, 9, Math.PI * 0.95, Math.PI * 0.55, true).getPoints(40).map(p => V(0, p.y, p.x)).reverse();   // head at the front, pointing down: nose-down (it pointed nose-up before)
  const m = new THREE.MeshStandardMaterial({ color: 0x3ad27a, emissive: 0x20a050, emissiveIntensity: 0.6 }); const tube = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 60, 0.45, 12), m);
  const head = new THREE.Mesh(new THREE.ConeGeometry(1.2, 2.6, 20), m); const e = pts[pts.length - 1], e2 = pts[pts.length - 3]; head.position.copy(e); head.quaternion.setFromUnitVectors(V(0, 1, 0), e.clone().sub(e2).normalize());
  noseArrow.add(tube, head); noseArrow.position.set(0, 2, -14); noseArrow.visible = false; jet.add(noseArrow); }
const ghost = J.root.clone(true); ghost.traverse(o => { if (o.isMesh) { o.material = new THREE.MeshBasicMaterial({ color: 0x3ad27a, transparent: true, opacity: 0.18, depthWrite: false }); o.castShadow = false; } }); ghost.visible = false; scene.add(ghost);

// ------------------------------------------------------------------ look
const LOOK = LOOKON ? makeLook(THREE, renderer, scene, camera, W, H, { overlays: [hud, chart, flash], noAO: [sky, deck, ocean], aperture: 0.0006, maxblur: 0.007, rim: 1.4 }) : null;

// ------------------------------------------------------------------ shots
const NOSE = V(0, 0, -1);
function setPlane(o, pitch, roll, yaw = 0, pos = V(0, 0, 0)) { o.position.copy(pos); o.rotation.set(pitch * D2R, yaw * D2R, roll * D2R, 'YXZ'); o.updateMatrixWorld(true); }
const setJet = (p, r, y, pos) => setPlane(jet, p, r, y, pos);
const fwd = () => NOSE.clone().applyQuaternion(jet.quaternion);
// o: { night, dark, low, deckAlt, jetAlt, cov, travel, fog, fogC, streaks, ocean (ft below the jet), stage, deep, day }
function env(o) { const N = o.night ?? 1;
  skyU.uDark.value = o.dark || 0; skyU.uLow.value = o.low || 0; skyU.uNight.value = N; deckU.uDark.value = o.dark || 0; deckU.uNight.value = N; deckU.uCov.value = o.cov ?? 0.5; deckU.uTravel.value = o.travel || 0;
  deck.visible = o.deckAlt != null; if (deck.visible) deck.position.y = (o.deckAlt - o.jetAlt) * FT;
  ocean.visible = o.ocean != null; if (ocean.visible) ocean.position.y = -o.ocean * FT;
  sky.visible = !o.stage && !o.deep; stage.visible = !!o.stage; deep.visible = !!o.deep;
  scene.background = o.stage ? new THREE.Color(0x060d16) : o.deep ? new THREE.Color(0x01070c) : null;
  const dk = o.dark || 0;
  if (o.deep) { sun.intensity = 0; hemi.intensity = 0.05; scene.environmentIntensity = 0.02; }
  else if (N > 0.5) { sun.color.set(0xb9c8ff); sun.intensity = lerp(1.7, 0.7, dk); hemi.color.set(0x5a6f9a); hemi.groundColor.set(0x0a0f18); hemi.intensity = lerp(0.55, 0.7, dk); scene.environmentIntensity = 0.12; }
  else { sun.color.set(0xfff3e2); sun.intensity = o.stage ? 2.2 : lerp(3.0, 0.9, dk); hemi.color.set(dk > 0.5 ? 0xb8c0cc : 0xcfe2ff); hemi.groundColor.set(0x8a8f99); hemi.intensity = o.stage ? 0.5 : lerp(0.9, 1.25, dk); scene.environmentIntensity = o.stage ? 0.35 : lerp(0.55, 0.4, dk); }
  PK = N > 0.5 && !o.stage ? [0.26, 0.3, 0.42] : [1, 1, 1];
  puffU.uFogD.value = o.fog || 0; puffU.uFog.value.set(o.fogC ?? (N > 0.5 ? 0x0d1320 : 0x6e747c));
  scene.fog = o.deep ? new THREE.FogExp2(0x02121c, 0.16) : o.fog ? new THREE.FogExp2(o.fogC ?? (N > 0.5 ? 0x0d1320 : 0x6e747c), o.fog) : null;
  strU.uA.value = o.streaks || 0; }
let FOCUS = V(0, 0, 0), LIGHTAT = V(0, 0, 0), SUNDIR = MOON;
function cam(pos, tgt, fov = 40, near = 0.3) { camera.position.copy(pos); camera.up.set(0, 1, 0); camera.lookAt(tgt); camera.fov = fov; camera.near = near; camera.updateProjectionMatrix(); FOCUS = tgt.clone(); }
function shake(t, amp, seed = 1) { return V(vn1(t * 9, seed) * amp, vn1(t * 9, seed + 3) * amp, vn1(t * 9, seed + 7) * amp * 0.5); }
function resetFx() { hud.visible = false; chart.visible = false; flash.visible = false; jet.visible = true; LJ.root.visible = false; crystals.visible = false; plug.visible = false; flow.visible = false; flowU.uA.value = 0;
  noseArrow.visible = false; ghost.visible = false; JP.pitotMouthR.material.color.set(0x050505); LIGHTAT = V(0, 0, 0); SUNDIR = MOON; }
// the fall (hook, beat 8, the loop's last second): nose ~15 deg up, belly first, the air and the clouds rushing UP past it
function fallShot(t, lt, which) { const alt = (which === 0 ? 30500 : 33500) - 182 * lt;
  setJet(15 + 1.5 * vn1(t * 1.3, 2), -5 + 4 * vn1(t * 0.9, 4), 10); const fl = V(0.05, 0.72, 0.69).normalize();   // air from below-front (falling, slowly moving forward)
  env({ night: 1, dark: 0.45, deckAlt: 24000, jetAlt: alt, cov: 0.5, travel: 60 * t, fog: 0.0011, streaks: 0.22 });
  addWisps(t, fl, 110, 420, 0.7, 0.5); strU.uFlow.value.copy(fl); strU.uSpeed.value = 75; strU.uLen.value = 3;
  if (which === 0) cam(V(150, -28 + lt * 1.2, -70).add(shake(t, 1.2)), V(0, -1, -3), 36, 1);
  else cam(V(-150, -8, 60).add(shake(t, 1.2, 3)), V(0, 0, 0), 38, 1);
  hud.visible = true; drawHud([['ALTITUDE', fmt(Math.round(alt / 10) * 10) + ' FT'], ['FALLING', '10,900 FT/MIN', '#ff6a5c']], 'STALL'); }
function shotAt(t) { const b = beatAt(t), lt = t - B[b], dur = DUR[b], u = lt / dur; resetFx(); PL = [];
  strU.uT.value = t; oceanU.uT.value = t; flowU.uT.value = t;
  if (t > TOTAL - 1.0) { fallShot(t, t - TOTAL, 0); return { b: 14 }; }
  switch (b) {
    case 0: fallShot(t, lt, 0); break;
    case 1: { // cruise at night: moonlit cloud tops, the A330 with its lights, slow orbit
      setJet(2, 0.5 * Math.sin(t * 0.5), 0); env({ night: 1, deckAlt: 24000, jetAlt: 35000, cov: 0.52, travel: 240 * t });
      const a = lerp(-34, 12, sm(u)) * D2R, r = lerp(150, 128, u); cam(V(Math.sin(a + Math.PI / 2) * r, 8 - 10 * u, -Math.cos(a + Math.PI / 2) * r * 0.9), V(0, 2, 2), 32, 1);
      hud.visible = true; drawHud([['ROUTE', 'RIO TO PARIS'], ['ON BOARD', '228 PEOPLE']]); break; }
    case 2: { // the storms ahead, in the dark
      setJet(1.5, 2 * smooth(0.5, 1, u), 0); env({ night: 1, deckAlt: 24000, jetAlt: 35000, cov: 0.55, travel: 240 * t, dark: 0.1 * u });
      addStorm(V(-3500, (24000 - 35000) * FT, -26000 + 3000 * u), 0.95, 0.55); addStorm(V(9000, (24000 - 35000) * FT, -38000), 0.9, 0.5, 0.8);
      cam(V(-14 + 4 * u, 3, 120 - 30 * u).add(shake(t, 0.1)), V(0, 8, -60), 46, 1);
      hud.visible = true; drawHud([['ALTITUDE', '35,000 FT'], ['TIME', '2:10 AM UTC']]); break; }
    case 3: { // ice crystals clog the pitot tube
      setJet(1, 0, 0); env({ night: 1, dark: 1, fog: 0.02, streaks: 0, travel: 240 * t }); addWisps(t, V(0, 0, 1), 240, 80, 0.5, 0.35);
      const tip = JP.pitotR.localToWorld(JP.pitotTipR.clone()); cam(tip.clone().add(V(0.55 - 0.1 * u, 0.1, -0.5 + 0.12 * u)), tip.clone().add(V(0, 0, 0.08)), 30, 0.03);
      LIGHTAT = tip; SUNDIR = V(0.4, 0.8, -0.4).normalize();
      crystals.visible = true; const tl = JP.pitotTipR.clone().add(JP.pitotR.position);
      for (let i = 0; i < 260; i++) { const ph = ((hash1(i * 3.3) + t * 1.6) % 1), aim = hash1(i * 7.7) < 0.35 + 0.45 * u, a = hash1(i * 5.1) * Math.PI * 2, r = (aim ? 0.01 : 0.04 + 0.1 * hash1(i * 2.2)) + 0.1 * (1 - ph) * 0.5;
        _m4.makeRotationFromEuler(_e.set(t * 7 + i, i, t * 5)); _m4.setPosition(tl.x + Math.cos(a) * r, tl.y + Math.sin(a) * r, tl.z - 1.4 * (1 - ph) + (aim ? 0 : 0.08 * ph)); crystals.setMatrixAt(i, _m4); }
      crystals.instanceMatrix.needsUpdate = true; plug.visible = true; plug.position.copy(JP.pitotTipR).add(V(0, 0, 0.018)); plug.scale.set(1, 1, smooth(0.1, 0.85, u) * 1.2 + 0.01);
      JP.pitotMouthR.material.color.lerpColors(new THREE.Color(0x050505), new THREE.Color(0xe8f2ff), smooth(0.2, 0.7, u));
      hud.visible = true; drawHud([['SPEED SENSORS', u < 0.5 ? 'ICING' : 'BLOCKED', '#8fd0ff']]); break; }
    case 4: { // the readings go haywire, the autopilot drops out; the wings rock
      const roll = 9 * Math.sin(lt * 2.2) * smooth(0.2, 0.6, u); setJet(1 + 1.5 * vn1(t * 3, 1), roll, 0); env({ night: 1, dark: 0.9, fog: 0.004, streaks: 0.35, travel: 240 * t });
      const f = fwd(); addWisps(t, f.clone().negate(), 230, 300, 0.55, 0.45); strU.uFlow.value.copy(f).negate(); strU.uSpeed.value = 200;
      cam(V(10, 14, 115).add(shake(t, 0.4)), V(0, 2, -10), 40, 1);
      const spd = u < 0.3 ? 275 : Math.round(60 + 220 * hash1(Math.floor(t * 6)));   // garbled: jumps around (5 times a second)
      hud.visible = true; drawHud([['SPEED', spd + ' KTS', u < 0.3 ? '#ffffff' : '#ffd23a'], ['AUTOPILOT', u < 0.35 ? 'ON' : 'OFF', u < 0.35 ? '#ffffff' : '#ff6a5c']], u > 0.35 ? 'AUTOPILOT OFF' : null); break; }
    case 5: { // the pilot flying pulls the nose up: it climbs to 38,000 ft, the speed bleeds away
      const k = smooth(0.0, 0.7, u); setJet(lerp(2, 13, k), -3, 0); env({ night: 1, dark: 0.4, deckAlt: 24000, jetAlt: 35000 + 3000 * smooth(0.1, 1, u), cov: 0.5, travel: lerp(240, 150, u) * t, streaks: 0.15 });
      const f = fwd(); addWisps(t, f.clone().negate(), lerp(220, 120, u), 400, 0.6, 0.3); strU.uFlow.value.copy(f).negate();
      cam(V(175, 6, 12).add(shake(t, 0.35, 5)), V(0, 2, 0), 34, 1);
      const alt = 35000 + 3000 * smooth(0.1, 1, u); hud.visible = true; drawHud([['ALTITUDE', fmt(Math.round(alt / 10) * 10) + ' FT'], ['CLIMBING', '7,000 FT/MIN', '#ffd23a']], null, lerp(0.45, 0.12, u)); break; }
    case 6: { // STALL: the air tears off the top of the wing
      setJet(14, -4, 0); env({ night: 1, dark: 0.3, deckAlt: 24000, jetAlt: 37500, cov: 0.5, travel: 90 * t, streaks: 0.1 });
      flow.visible = true; flowU.uA.value = smooth(0, 0.12, u); flowU.uSep.value = smooth(0.15, 0.6, u);
      cam(jet.localToWorld(V(13, 9, 30)).add(shake(t, 0.35, 6)), jet.localToWorld(V(13, -1, 3)), 44, 0.5);
      hud.visible = true; drawHud([['WING', u < 0.4 ? 'LOSING LIFT' : 'STALLED', u < 0.4 ? '#ffd23a' : '#ff6a5c']], u > 0.2 ? 'STALL' : null); break; }
    case 7: { // the readings come back, but the nose stays up
      setJet(15, -5, 0); env({ night: 1, dark: 0.35, deckAlt: 24000, jetAlt: 37000 - 182 * lt, cov: 0.5, travel: 70 * t, streaks: 0.15 });
      const fl = V(0.05, 0.72, 0.69).normalize(); addWisps(t, fl, 100, 400, 0.6, 0.35); strU.uFlow.value.copy(fl);
      cam(V(-170, 3, -10).add(shake(t, 0.7, 2)), V(0, 2, 0), 34, 1);
      hud.visible = true; drawHud([['SPEED READINGS', 'BACK', '#2fbf71'], ['NOSE', '15° UP', '#ff6a5c']], 'STALL'); break; }
    case 8: fallShot(t, lt, 8); break;
    case 9: { // what would have saved it: lower the nose (a ghost of the jet nose-down), but it stayed up
      env({ night: 0, stage: true }); setJet(15, 0, 90); ghost.visible = true; const k = smooth(0.1, 0.6, u);
      setPlane(ghost, lerp(15, -6, k), 0, 90, V(0, 0, 0)); noseArrow.visible = u > 0.1; noseArrow.scale.setScalar(2.1 * sm(clamp((u - 0.1) / 0.15, 0, 1)));
      cam(V(0, 8, 230), V(-4, 2, 0), 34, 1); break; }
    case 10: { // the ocean, in the dark: belly first; the picture fades out before it hits
      const tI = 0.62 * dur, h = Math.max(0, (tI - lt) * 55 + 18); setJet(16, -5, 10, V(0, 0, 0)); env({ night: 1, ocean: h / FT, travel: 0 }); sun.intensity = 2.6; hemi.intensity = 0.8;
      const fl = V(0.05, 0.72, 0.69).normalize(); addWisps(t, fl, 60, 300, 0.35, 0.2 * smooth(0, 0.3, u));
      cam(V(-95, -h * 0.25 + 14, 55), V(0, -h * 0.35, 0), 40, 1); flash.visible = true; flash.material.color.set(0x000000); flash.material.opacity = smooth(tI - 0.5, tI, lt);
      hud.visible = lt < tI; drawHud([['TIME', '2:14 AM UTC'], ['ALTITUDE', fmt(Math.max(0, Math.round(h / FT / 10) * 10)) + ' FT', '#ff6a5c']]); break; }
    case 11: { // the black boxes, about 13,000 ft down, for nearly two years
      env({ night: 1, deep: true }); jet.visible = false; LIGHTAT = V(0, 0, 0);
      const a = lerp(-0.5, 0.4, u); cam(V(Math.sin(a) * 3.2, 1.3 - 0.3 * u, Math.cos(a) * 3.2), V(0, 0.15, 0), 40, 0.05);
      SNOW.position.y = -((t * 0.12) % 2.5); break; }
    case 12: { // the new speed probes (daylight)
      setJet(1, 0, 0); env({ night: 0, deckAlt: 24000, jetAlt: 35000, cov: 0.5, travel: 240 * t });
      const tip = JP.pitotR.localToWorld(JP.pitotTipR.clone()); cam(tip.clone().add(V(0.7 - 0.25 * u, 0.18, -0.55 + 0.25 * u)), tip.clone().add(V(0, 0, 0.1)), 32, 0.03); LIGHTAT = tip; SUNDIR = SUN;
      hud.visible = true; drawHud([['OLD PROBE', 'BANNED', '#ff6a5c'], ['NEW PROBE', 'FITTED', '#2fbf71']]); break; }
    case 13: { // pilots train for it: steady nose, steady power (dawn, level flight)
      setJet(5, 0, 0); env({ night: 0.15, deckAlt: 24000, jetAlt: 35000, cov: 0.5, travel: 240 * t });
      const a = lerp(20, -10, u) * D2R; cam(V(Math.sin(a) * 120 + 20, 6, Math.cos(a) * 120), V(0, 2, 0), 32, 1);
      hud.visible = true; drawHud([['NOSE', 'STEADY', '#2fbf71'], ['POWER', 'SET', '#2fbf71']]); break; }
    case 14: { // two days ago: the Learjet over Florida (daytime storm, diving); then the fall again (loop)
      jet.visible = false; LJ.root.visible = true; setPlane(LJ.root, -30, 18, -8); const f = NOSE.clone().applyQuaternion(LJ.root.quaternion);
      env({ night: 0, dark: 0.5, deckAlt: 24000, jetAlt: 31000 - 441 * lt, cov: 0.5, travel: 180 * t, fog: 0.0015, fogC: 0x4f5761, streaks: 0.3 });
      addWisps(t, f.clone().negate(), 180, 260, 0.45, 0.5); strU.uFlow.value.copy(f).negate(); strU.uSpeed.value = 160;
      cam(V(25, -9, -15).add(shake(t, 0.35)), V(0, -1.2, -1.5), 36); hud.visible = true; drawHud([['NOV 1, 2026', 'FLORIDA'], ['CAUSE', 'UNKNOWN', '#ffd23a']]); break; }
  }
  return { b }; }

// ------------------------------------------------------------------ frame I/O
function update(t) { t = ((t % TOTAL) + TOTAL) % TOTAL; const r = shotAt(t); fitOverlays();
  sky.position.copy(camera.position); deckU.uCam.value.copy(camera.position); strU.uCam.value.copy(camera.position); oceanU.uCam.value.copy(camera.position);
  const at = LIGHTAT.lengthSq() ? LIGHTAT : (LJ.root.visible ? LJ.root.position : jet.position);
  sun.position.copy(at).addScaledVector(SUNDIR, 150); sun.target.position.copy(at); sun.target.updateMatrixWorld();
  commitPuffs(); return r; }
function stepTo(i) { return update(i / FPS); }
const draw = () => { if (LOOK) LOOK.render(FOCUS, { ao: false, dof: true }); else renderer.render(scene, camera); };
const gl = renderer.getContext(), px = new Uint8Array(W * H * 4);
window.renderAll = async (f0, f1) => { for (let i = f0; i < f1; i++) { stepTo(i); draw(); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); await fetch('/frame', { method: 'POST', body: px }); } return 'ok'; };
window.renderAtT = t => { stepTo(Math.round(t * FPS)); draw(); return renderer.domElement.toDataURL('image/png'); };
window.dbg = { THREE, scene, camera, jet, JP, update, shotAt };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS); window.READY = true;
window.SCN = { THREE, scene, camera, stepTo, renderer, FPS, B, DUR, TOTAL };
