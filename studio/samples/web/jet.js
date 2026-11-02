// "This jet just dropped twenty-six thousand feet in about one minute." - the Learjet 60 that came down in Greenacres, Florida
// on Nov 1, 2026 (all 9 aboard died), and four things investigators will look at. No people shown. jet.html?w=1080&h=1920
// Facts (FAA, NTSB, CNN/LiveATC, CBS, ABC): Austin -> North Eleuthera; cruising ~35,000 ft; storms; pilot: light clear ice, moderate
// turbulence, -47 C; asked to climb 2,000 ft; mayday: overspeed, descending 20,000 ft/min; 35,250 -> 8,750 ft in about a minute; data ends.
// Beats: 0 dive (hook) | 1 cruise: Learjet 60, Austin to the Bahamas | 2 the storm ahead | 3 ice on the wing, -47 C | 4 climb, then mayday
//        5 the dive, overspeed | 6 Greenacres: from above, smoke | 7 four possible causes (dark stage) | 8 1: storm gust rolls it
//        9 nose down: overspeed tape | 10 2: ice plugs the pitot tube | 11 gauge says slow, really too fast | 12 3: shock wave, Mach tuck
//        13 4: tail flutter, breakup (slow motion) | 14 the last minute (radar altitude) + what the NTSB checks | 15 cruise, then the dive (loop)
import * as THREE from 'three';
import { makeLook } from '/look.js';
import { makeLearjet60 } from '/jetmodel.js';

const Q = new URLSearchParams(location.search);
const W = +Q.get('w') || 720, H = +Q.get('h') || 1280, FPS = 30;
const TIMES = await (await fetch('/jet/times.json')).json();
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
Object.assign(sun.shadow.camera, { left: -12, right: 12, top: 12, bottom: -12, near: 1, far: 80 }); sun.shadow.bias = -0.0003; sun.shadow.normalBias = 0.04;
scene.add(sun, sun.target);

// ------------------------------------------------------------------ the jet
const J = makeLearjet60(THREE), jet = J.root, JP = J.parts; scene.add(jet);
if (Q.get('nocc')) jet.traverse(o => { if (o.isMesh && o.material.clearcoat) o.material.clearcoat = 0; });
if (Q.get('flip')) jet.traverse(o => { if (o.isMesh && o.material.side === THREE.DoubleSide) o.material.side = THREE.FrontSide; });

// ------------------------------------------------------------------ sky dome (follows the camera); uDark = inside the storm
const skyU = { uSun: { value: SUN }, uDark: { value: 0 }, uLow: { value: 0 } };
const sky = new THREE.Mesh(new THREE.SphereGeometry(300000, 48, 24), new THREE.ShaderMaterial({ uniforms: skyU, side: THREE.BackSide, depthWrite: false, fog: false,
  vertexShader: 'varying vec3 d; void main(){ d = normalize(position); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }',
  fragmentShader: `uniform vec3 uSun; uniform float uDark, uLow; varying vec3 d;
    void main(){ float h = d.y; vec3 zen = mix(vec3(.06,.22,.58), vec3(.3,.48,.75), uLow), hor = mix(vec3(.62,.75,.9), vec3(.8,.84,.87), uLow);
      vec3 c = h > 0. ? mix(hor, zen, pow(clamp(h,0.,1.), .55)) : mix(hor, vec3(.55,.62,.7), pow(clamp(-h,0.,1.), .35));
      float s = max(dot(d, uSun), 0.); c += vec3(1.,.93,.8) * (pow(s, 900.) * 6. + pow(s, 12.) * .18) * (1. - uDark);
      c = mix(c, vec3(.42,.45,.5) * (.8 + .25 * h), uDark);
      gl_FragColor = vec4(c, 1.);
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
    }` }));
sky.renderOrder = -10; scene.add(sky);

// ------------------------------------------------------------------ cloud deck: a big shader sheet (tops lit, gaps show the haze below)
const GLN = `float hh(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
  float vn(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f*f*(3.0-2.0*f); return mix(mix(hh(i), hh(i+vec2(1,0)), u.x), mix(hh(i+vec2(0,1)), hh(i+vec2(1,1)), u.x), u.y); }
  float fbm(vec2 p){ float a = .5, s = 0.; for (int i = 0; i < 6; i++){ s += a * vn(p); p = p * 2.03 + vec2(17.1, 9.2); a *= .5; } return s; }`;
const deckU = { uTravel: { value: 0 }, uCam: { value: V(0, 0, 0) }, uSun: { value: SUN }, uDark: { value: 0 }, uCov: { value: 0.5 } };
const deck = new THREE.Mesh(new THREE.PlaneGeometry(500000, 500000, 1, 1).rotateX(-Math.PI / 2), new THREE.ShaderMaterial({ uniforms: deckU, transparent: true, depthWrite: false, fog: false,
  vertexShader: 'varying vec3 w; void main(){ vec4 p = modelMatrix * vec4(position,1.); w = p.xyz; gl_Position = projectionMatrix * viewMatrix * p; }',
  fragmentShader: `${GLN} uniform float uTravel, uDark, uCov; uniform vec3 uCam, uSun; varying vec3 w;
    void main(){ vec2 p = vec2(w.x, w.z - uTravel) / 2600.;
      float n = fbm(p), n2 = fbm(p * 3.1 + 4.0);
      float cov = smoothstep(uCov - .08, uCov + .14, n);
      float lit = .62 + .5 * smoothstep(.35, .85, n2) * smoothstep(uCov, uCov + .3, n);
      vec3 c = mix(vec3(.55,.6,.68), vec3(1.), lit); c *= mix(1., .55, uDark);
      float d = length(w.xz - uCam.xz); vec3 hz = mix(vec3(.74,.82,.92), vec3(.45,.48,.52), uDark);
      c = mix(c, hz, smoothstep(20000., 140000., d)); float a = cov * (1. - smoothstep(150000., 240000., d));
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
let PL = [];                                                         // this frame's puffs: [x, y, z, size, r, g, b, a]
function commitPuffs() { const cp = camera.position; PL.sort((a, b) => ((b[0] - cp.x) ** 2 + (b[1] - cp.y) ** 2 + (b[2] - cp.z) ** 2) - ((a[0] - cp.x) ** 2 + (a[1] - cp.y) ** 2 + (a[2] - cp.z) ** 2));
  const n = Math.min(PL.length, PUFFMAX); for (let i = 0; i < n; i++) { const q = PL[i]; iP.setXYZW(i, q[0], q[1], q[2], q[3]); iC.setXYZW(i, q[4], q[5], q[6], q[7]); }
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

// ------------------------------------------------------------------ the ground at Greenacres (beat 6): streets, homes, the six-lane road, a mobile home park, a shopping centre
const GS = 6000;
const groundTex = (() => { const N = 4096, c = document.createElement('canvas'); c.width = c.height = N; const g = c.getContext('2d'); const m2p = N / GS, P = (x) => (x + GS / 2) * m2p;
  g.fillStyle = '#5f7a45'; g.fillRect(0, 0, N, N);
  for (let i = 0; i < 26000; i++) { const x = hash1(i * 1.7) * N, y = hash1(i * 2.9) * N, r = 2 + 5 * hash1(i * 3.3); g.fillStyle = `rgba(${40 + 30 * hash1(i)},${70 + 40 * hash1(i * 5)},${35 + 20 * hash1(i * 7)},0.55)`; g.beginPath(); g.arc(x, y, r, 0, 7); g.fill(); }
  const road = (x0, z0, x1, z1, w, col = '#4a4c50') => { g.strokeStyle = col; g.lineWidth = w * m2p; g.beginPath(); g.moveTo(P(x0), P(z0)); g.lineTo(P(x1), P(z1)); g.stroke(); };
  // neighbourhood blocks: streets every ~140 m east-west, ~320 m north-south, houses along them
  for (let zx = -2900; zx <= 2900; zx += 140) { if (Math.abs(zx - 160) < 80) continue; road(-2950, zx, 2950, zx, 9, '#6b6d70'); }
  for (let xx = -2900; xx <= 2900; xx += 320) road(xx, -2950, xx, 2950, 9, '#6b6d70');
  for (let zx = -2900; zx <= 2900; zx += 140) for (let xx = -2950; xx < 2950; xx += 16) { if (Math.abs(xx) < 60) continue; if (xx > -700 && xx < -120 && zx > -400 && zx < 700) continue; if (xx > 80 && xx < 520 && zx > 180 && zx < 520) continue;
    for (const side of [-1, 1]) { if (hash1(xx * 0.13 + zx * 0.71 + side) < 0.12) continue; const roof = ['#b7a58c', '#8f8f93', '#c9c3b6', '#7b5a4a', '#a9b2b8'][Math.floor(hash1(xx + zx * 3 + side) * 5)];
      g.fillStyle = roof; g.fillRect(P(xx + 2), P(zx + side * 14 - 6), 11 * m2p, 12 * m2p); g.fillStyle = 'rgba(0,0,0,0.25)'; g.fillRect(P(xx + 2), P(zx + side * 14 + 5), 11 * m2p, 2 * m2p);
      if (hash1(xx * 7 + zx) < 0.06) { g.fillStyle = '#3f8fae'; g.fillRect(P(xx + 4), P(zx + side * 30 - 3), 6 * m2p, 4 * m2p); } } }
  // retention ponds and a canal
  for (let i = 0; i < 14; i++) { const x = (hash1(i * 11) - 0.5) * 5200, z = (hash1(i * 13) - 0.5) * 5200; if (Math.abs(x) < 400 && Math.abs(z) < 700) continue; g.fillStyle = '#3d5a5c'; g.beginPath(); g.ellipse(P(x), P(z), (60 + 90 * hash1(i)) * m2p, (35 + 60 * hash1(i * 2)) * m2p, hash1(i * 3) * 3, 0, 7); g.fill(); }
  road(-2950, -1700, 2950, -1640, 18, '#3e5a5e');
  // mobile home park (west of the road, near the crash): dense small white homes
  g.fillStyle = '#7d8a6a'; g.fillRect(P(-700), P(-400), 580 * m2p, 1100 * m2p);
  for (let z = -390; z < 690; z += 24) { road(-690, z + 12, -130, z + 12, 5, '#77797c'); for (let x = -690; x < -130; x += 9) { if (hash1(x * 3.1 + z) < 0.1) continue; g.fillStyle = hash1(x + z * 1.3) < 0.5 ? '#e4e4df' : '#cfd4d6'; g.fillRect(P(x), P(z + 1), 6.5 * m2p, 9 * m2p); } }
  // shopping centre + parking (east of the road)
  g.fillStyle = '#55575b'; g.fillRect(P(80), P(180), 440 * m2p, 340 * m2p); g.fillStyle = '#c9c4ba'; g.fillRect(P(300), P(200), 200 * m2p, 90 * m2p); g.fillRect(P(110), P(420), 160 * m2p, 60 * m2p);
  g.strokeStyle = 'rgba(230,230,230,0.6)'; g.lineWidth = 1; for (let x = 100; x < 290; x += 3) { g.beginPath(); g.moveTo(P(x), P(300)); g.lineTo(P(x), P(310)); g.stroke(); }
  // Military Trail: six lanes plus a median, north-south through x = 0; 10th Ave N crossing at z = 160
  road(0, -2950, 0, 2950, 40, '#3d3f43'); road(0, -2950, 0, 2950, 4, '#6f8a52');
  road(-2950, 160, 2950, 160, 24, '#404246');
  g.strokeStyle = 'rgba(240,240,235,0.85)'; g.lineWidth = 0.4 * m2p; g.setLineDash([3 * m2p, 6 * m2p]);
  for (const x of [-13, -7, 7, 13]) { g.beginPath(); g.moveTo(P(x), 0); g.lineTo(P(x), N); g.stroke(); } g.setLineDash([]);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t; })();
const ground = new THREE.Group(); scene.add(ground); ground.visible = false;
{ const gm = new THREE.Mesh(new THREE.PlaneGeometry(GS, GS).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ map: groundTex, roughness: 0.95 })); gm.receiveShadow = true; ground.add(gm);
  const far = new THREE.Mesh(new THREE.PlaneGeometry(200000, 200000).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0x55703f, roughness: 1 })); far.position.y = -0.5; ground.add(far); }
// cars on Military Trail (both ways)
const CARN = 80, cars = new THREE.InstancedMesh(new THREE.BoxGeometry(1.9, 1.5, 4.6), new THREE.MeshStandardMaterial({ roughness: 0.4, metalness: 0.3 }), CARN); ground.add(cars);
for (let i = 0; i < CARN; i++) cars.setColorAt(i, new THREE.Color().setHSL(hash1(i * 3), hash1(i * 5) < 0.5 ? 0.05 : 0.5, 0.25 + 0.55 * hash1(i * 7)));
const _m4 = new THREE.Matrix4();
function placeCars(t, stopAt) { for (let i = 0; i < CARN; i++) { const dir = i % 2 ? 1 : -1, lane = [3.5, 10, 16.5][i % 3] * dir, sp = 17 + 5 * hash1(i * 2);
  let z = ((hash1(i * 9) * 3000 + dir * sp * (stopAt == null ? t : Math.min(t, stopAt))) % 3000 + 3000) % 3000 - 1500; if (stopAt != null && t > stopAt && Math.abs(z) < 60) z += dir * 70;
  _m4.makeTranslation(lane, 0.75, z); cars.setMatrixAt(i, _m4); } cars.instanceMatrix.needsUpdate = true; }

// ------------------------------------------------------------------ the dark stage (beat 7): grid floor
const stage = new THREE.Group(); scene.add(stage); stage.visible = false;
{ const gh = new THREE.GridHelper(80, 40, 0x2f86b8, 0x1a3c58); gh.position.set(0, -3.2, -16); stage.add(gh); }   // kept in front of the camera: lines running behind it fanned out into big blue wedges

// ------------------------------------------------------------------ explainers: gust arrows, pitch arrow, shock wave sheet, ice crystals, debris
function arrowMesh(color, op = 0.85, emis = 0.35) { const s = new THREE.Shape(); s.moveTo(-0.32, 1.6); s.lineTo(0.32, 1.6); s.lineTo(0.32, 0.55); s.lineTo(0.85, 0.55); s.lineTo(0, -0.55); s.lineTo(-0.85, 0.55); s.lineTo(-0.32, 0.55); s.closePath();
  const geo = new THREE.ExtrudeGeometry(s, { depth: 0.22, bevelEnabled: true, bevelThickness: 0.05, bevelSize: 0.05, bevelSegments: 3 }); geo.translate(0, 0, -0.11);
  return new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: emis, roughness: 0.4, transparent: true, opacity: op })); }
const gusts = [0, 1, 2].map(() => { const a = arrowMesh(0x8fd0ff, 0.0); a.scale.setScalar(2.4); scene.add(a); return a; });
const pitchArrow = new THREE.Group(); { const curve = new THREE.EllipseCurve(0, 0, 3.2, 3.2, Math.PI * 0.95, Math.PI * 0.45, true);
  const pts = curve.getPoints(40).map(p => V(0, p.y, p.x)); const tube = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 60, 0.16, 12), new THREE.MeshStandardMaterial({ color: 0xffd23a, emissive: 0xffb000, emissiveIntensity: 0.5 }));
  const head = new THREE.Mesh(new THREE.ConeGeometry(0.42, 0.95, 20), tube.material); const e = pts[pts.length - 1], e2 = pts[pts.length - 3]; head.position.copy(e); head.quaternion.setFromUnitVectors(V(0, 1, 0), e.clone().sub(e2).normalize());
  pitchArrow.add(tube, head); pitchArrow.position.set(0, 0.6, -8.0); pitchArrow.visible = false; jet.add(pitchArrow); }
// shock wave: a shimmering sheet standing on the right wing's upper surface at ~55% chord
const shockU = { uT: { value: 0 }, uA: { value: 0 } };
const shock = (() => { const secs = JP.wingSecs(1), pos = [], uv = [], idx = [];
  secs.forEach((S, i) => { if (i > 9) return; const x = S.o.x, z = S.o.z + 0.55 * S.c, y0 = S.o.y + 0.07 * S.c, h = 1.1 * S.c / 2.85 + 0.25;
    pos.push(x, y0, z, x, y0 + h, z + 0.08); uv.push(i / 9, 0, i / 9, 1); });
  for (let i = 0; i < 9; i++) { const a = i * 2; idx.push(a, a + 2, a + 1, a + 1, a + 2, a + 3); }
  const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); geo.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); geo.setIndex(idx);
  const m = new THREE.Mesh(geo, new THREE.ShaderMaterial({ uniforms: shockU, transparent: true, depthWrite: false, side: THREE.DoubleSide,
    vertexShader: 'varying vec2 v; void main(){ v = uv; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }',
    fragmentShader: `uniform float uT, uA; varying vec2 v; void main(){ float s = .65 + .35 * sin(v.x * 50. + uT * 25.) * sin(v.y * 9. - uT * 11.);
      // clamp: MSAA samples past the edge made pow(<0) = NaN (black dashes). smoothstep with reversed edges is undefined in GLSL.
      float a = pow(clamp(1. - v.y, 0., 1.), 0.8) * .95 * s + (1. - smoothstep(0., .12, v.y)) * .8;
      gl_FragColor = vec4(mix(vec3(.7,.92,1.2), vec3(1.6), 1. - smoothstep(0., .2, v.y)), clamp(a, 0., 1.) * uA);
      #include <colorspace_fragment>
    }` })); m.renderOrder = 8; jet.add(m); return m; })();
// ice crystals streaming into the pitot tube (beat 10) and the ice plug inside it
const crystals = new THREE.InstancedMesh(new THREE.OctahedronGeometry(0.0019, 0), new THREE.MeshStandardMaterial({ color: 0xf2f8ff, emissive: 0x9fb8d0, emissiveIntensity: 0.4, roughness: 0.2 }), 260); jet.add(crystals); crystals.visible = false;
const plug = new THREE.Mesh(new THREE.CylinderGeometry(0.0078, 0.0078, 0.03, 16).rotateX(Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0xf4f9ff, roughness: 0.85, emissive: 0x6080a0, emissiveIntensity: 0.15 }));
JP.pitotR.add(plug); plug.position.copy(JP.pitotTipR).add(V(0, 0, 0.01)); plug.visible = false;
// breakup debris (beat 13): panel bits off the tail
const debris = []; for (let i = 0; i < 9; i++) { const d = new THREE.Mesh(new THREE.BoxGeometry(0.05 + 0.25 * hash1(i), 0.012, 0.04 + 0.2 * hash1(i * 3)), new THREE.MeshStandardMaterial({ color: i % 3 ? 0xeeeeec : 0x9aa0a8, roughness: 0.5, metalness: 0.3 })); d.visible = false; d.castShadow = true; JP.stab.add(d); debris.push(d); }
const tipHome = JP.stabTipR.position.clone();
// rime ice on the right wing's leading edge (beat 3): small bluish-white spikes pointing into the wind, growing
const ICEN = 520, iceSp = new THREE.InstancedMesh(new THREE.ConeGeometry(0.012, 0.05, 5).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0xd8efff, emissive: 0x5d86b0, emissiveIntensity: 0.25, roughness: 0.55 }), ICEN);
iceSp.visible = false; jet.add(iceSp); const ICEP = [];
{ const secs = JP.wingSecs(1); for (let i = 0; i < ICEN; i++) { const u = hash1(i * 1.7) * 0.999 * (secs.length - 1), k = Math.floor(u), f = u - k, A = secs[k], Bs = secs[k + 1];
    const o = A.o.clone().lerp(Bs.o, f), c = lerp(A.c, Bs.c, f), a = (hash1(i * 3.1) - 0.5) * 2.2;   // around the nose of the airfoil
    ICEP.push([o.add(V(0, 0.012 * c * Math.sin(a) * 4 + 0.004, 0.012 * c * (1 - Math.cos(a)) * 3)), a, 0.5 + hash1(i * 5.3)]); } }
function placeIce(g) { for (let i = 0; i < ICEN; i++) { const [p, a, s] = ICEP[i]; const sc = clamp(g * 1.6 - (1 - s) * 0.6, 0, 1.2) * s;
  _m4.makeRotationFromEuler(_e.set(a * 0.6, 0, 0)).scale(V(sc + 0.001, sc + 0.001, sc + 0.001)); _m4.setPosition(p.x, p.y, p.z - 0.02 * sc); iceSp.setMatrixAt(i, _m4); } iceSp.instanceMatrix.needsUpdate = true; }

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
  JP.iceR.visible = JP.iceL.visible = JP.iceM.opacity > 0.002; shock.visible = shockU.uA.value > 0.002; }   // invisible-but-drawn ice made NaN (black dashes) in the film pass
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
// the last minute: altitude from radar (35,250 ft -> 8,750 ft in about a minute, then the data ends) + what the NTSB checks
function drawChart(lt, dur) { const g = chC.getContext('2d'); g.fillStyle = '#081019'; g.fillRect(0, 0, 1080, 1920);
  g.strokeStyle = 'rgba(60,110,150,0.25)'; g.lineWidth = 1; for (let x = 0; x < 1080; x += 60) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, 1920); g.stroke(); } for (let y = 0; y < 1920; y += 60) { g.beginPath(); g.moveTo(0, y); g.lineTo(1080, y); g.stroke(); }
  g.fillStyle = '#ffffff'; g.font = 'bold 64px Arial, Helvetica, sans-serif'; g.fillText('THE LAST MINUTE', 80, 330);
  g.fillStyle = '#7fa6c4'; g.font = '600 34px Arial, Helvetica, sans-serif'; g.fillText('ALTITUDE FROM RADAR (FAA)', 80, 382);
  const X0 = 170, X1 = 1000, Y0 = 430, Y1 = 900, ty = a => Y1 - (Y1 - Y0) * a / 40000, tx = s => X0 + (X1 - X0) * (s + 150) / 160;   // s: seconds, -150 .. +10
  g.strokeStyle = 'rgba(159,182,200,0.6)'; g.lineWidth = 3; g.beginPath(); g.moveTo(X0, Y0); g.lineTo(X0, Y1); g.lineTo(X1, Y1); g.stroke();
  g.fillStyle = '#9fb6c8'; g.font = '600 28px Arial, Helvetica, sans-serif'; for (const a of [0, 10000, 20000, 30000, 40000]) { g.fillText(a ? (a / 1000) + 'K FT' : '0', 60, ty(a) + 10); g.fillStyle = 'rgba(159,182,200,0.15)'; g.fillRect(X0, ty(a), X1 - X0, 2); g.fillStyle = '#9fb6c8'; }
  const pr = smooth(0.0, 0.45, lt / dur), pts = []; for (let s = -150; s <= 0; s += 1) { const a = s < -62 ? 35000 + (s > -75 ? 250 * (s + 75) / 13 : 0) : (s < -60 ? 35250 : 35250 - 26500 * Math.pow((s + 60) / 60, 1.25)); pts.push([s, a]); }
  const nShow = Math.floor(pts.length * pr); g.strokeStyle = '#ffd23a'; g.lineWidth = 8; g.lineJoin = 'round'; g.beginPath(); pts.slice(0, Math.max(1, nShow)).forEach(([s, a], i) => i ? g.lineTo(tx(s), ty(a)) : g.moveTo(tx(s), ty(a))); g.stroke();
  if (pr > 0.62) { g.fillStyle = '#ff3b30'; g.font = 'bold 36px Arial, Helvetica, sans-serif'; g.fillText('MAYDAY', tx(-60) - 70, ty(35250) - 30); g.beginPath(); g.arc(tx(-60), ty(35250), 12, 0, 7); g.fill(); }
  if (pr > 0.99) { g.fillStyle = '#ff3b30'; g.beginPath(); g.arc(tx(0), ty(8750), 14, 0, 7); g.fill(); g.font = 'bold 34px Arial, Helvetica, sans-serif'; g.fillText('DATA ENDS', tx(0) - 210, ty(8750) + 62); g.fillText('8,750 FT', tx(0) - 170, ty(8750) + 104);
    g.setLineDash([10, 12]); g.strokeStyle = 'rgba(255,59,48,0.7)'; g.lineWidth = 5; g.beginPath(); g.moveTo(tx(0), ty(8750)); g.lineTo(tx(3), Y1); g.stroke(); g.setLineDash([]); }
  g.fillStyle = '#9fb6c8'; g.font = '600 26px Arial, Helvetica, sans-serif'; g.fillText('2 MIN', tx(-120) - 30, Y1 + 40); g.fillText('1 MIN', tx(-60) - 30, Y1 + 40); g.fillText('END', tx(0) - 26, Y1 + 40);
  const items = [['RADIO CALLS', 0.12], ['RADAR', 0.3], ['WEATHER', 0.43], ['WRECKAGE', 0.6]]; let y = 1010;
  g.fillStyle = '#ffffff'; g.font = 'bold 40px Arial, Helvetica, sans-serif'; if (lt / dur > 0.08) g.fillText('THE NTSB CHECKS:', 80, y); y += 30;
  for (const [txt, at] of items) { const a = smooth(at, at + 0.06, lt / dur); if (a <= 0) continue; g.globalAlpha = a; y += 64; g.fillStyle = '#2fbf71'; g.beginPath(); g.arc(104, y - 14, 18, 0, 7); g.fill();
    g.strokeStyle = '#081019'; g.lineWidth = 6; g.beginPath(); g.moveTo(95, y - 15); g.lineTo(102, y - 7); g.lineTo(114, y - 23); g.stroke(); g.fillStyle = '#fff'; g.font = 'bold 44px Arial, Helvetica, sans-serif'; g.fillText(txt, 140, y); g.globalAlpha = 1; }
  chT.needsUpdate = true; }

// ------------------------------------------------------------------ look (MSAA, depth of field, rim) - no AO (open sky)
const LOOK = LOOKON ? makeLook(THREE, renderer, scene, camera, W, H, { overlays: [hud, chart, flash], noAO: [sky, deck], aperture: 0.0009, maxblur: 0.008, rim: 1.2 }) : null;

// ------------------------------------------------------------------ the shots
const NOSE = V(0, 0, -1), _q = new THREE.Quaternion(), _e = new THREE.Euler();
function setJet(pitch, roll, yaw = 0, pos = V(0, 0, 0)) { jet.position.copy(pos); jet.rotation.set(pitch * D2R, yaw * D2R, roll * D2R, 'YXZ'); jet.updateMatrixWorld(true); }
const fwd = () => NOSE.clone().applyQuaternion(jet.quaternion);
function env(o) { // o: { dark, low, deckAlt (ft), jetAlt (ft), cov, travel, fog, streaks, wisps, ground, stage }
  skyU.uDark.value = o.dark || 0; skyU.uLow.value = o.low || 0; deckU.uDark.value = o.dark || 0; deckU.uCov.value = o.cov ?? 0.5; deckU.uTravel.value = o.travel || 0;
  deck.visible = o.deckAlt != null; if (deck.visible) deck.position.y = (o.deckAlt - o.jetAlt) * FT;
  sky.visible = !o.stage; ground.visible = !!o.ground; stage.visible = !!o.stage;
  scene.background = o.stage ? new THREE.Color(0x060d16) : null;
  const dk = o.dark || 0; sun.intensity = o.stage ? 2.2 : lerp(3.0, 0.9, dk); hemi.intensity = o.stage ? 0.5 : lerp(0.9, 1.25, dk); hemi.color.set(dk > 0.5 ? 0xb8c0cc : 0xcfe2ff);
  scene.environmentIntensity = o.stage ? 0.35 : lerp(0.55, 0.4, dk);
  puffU.uFogD.value = o.fog || 0; puffU.uFog.value.set(o.fogC ?? 0x6e747c);
  scene.fog = o.fog ? new THREE.FogExp2(o.fogC ?? 0x6e747c, o.fog) : null;
  strU.uA.value = o.streaks || 0; }
let FOCUS = V(0, 0, 0);
function cam(pos, tgt, fov = 40, near = 0.3) { camera.position.copy(pos); camera.up.set(0, 1, 0); camera.lookAt(tgt); camera.fov = fov; camera.near = near; camera.updateProjectionMatrix(); FOCUS = tgt.clone(); }
function shake(t, amp, seed = 1) { return V(vn1(t * 9, seed) * amp, vn1(t * 9, seed + 3) * amp, vn1(t * 9, seed + 7) * amp * 0.5); }
function resetFx() { JP.iceM.opacity = 0; JP.iceR.scale.setScalar(1); gusts.forEach(a => { a.visible = false; }); pitchArrow.visible = false; shockU.uA.value = 0; crystals.visible = false; plug.visible = false;
  JP.stab.rotation.set(0, 0, 0); JP.stabTipR.position.copy(tipHome); JP.stabTipR.rotation.set(0, 0, 0); JP.stabTipR.visible = true; debris.forEach(d => { d.visible = false; });
  hud.visible = false; chart.visible = false; flash.visible = false; jet.visible = true; iceSp.visible = false; JP.pitotMouthR.material.color.set(0x050505); }

// the dive (beats 0 and 5, and the loop's last second): nose ~35 deg down, rolled, clouds streaming up past
function diveShot(t, lt, which) { const alt = (which === 0 ? 31500 : 33200) - 441 * lt;
  setJet(-35 + 2 * vn1(t * 3, 2), 18 + 4 * vn1(t * 2, 4), -8); const f = fwd();
  env({ dark: 0.55, low: 0.1, deckAlt: 24000, jetAlt: alt, cov: 0.5, travel: 180 * t, fog: 0.0012, fogC: 0x4f5761, streaks: 0.3 });
  addWisps(t, f.clone().negate(), 180, 260, 0.42, 0.55); strU.uFlow.value.copy(f).negate(); strU.uSpeed.value = 160; strU.uLen.value = 3.2;
  if (which === 0) { const p = V(25, -9 + lt * 0.6, -15).add(shake(t, 0.35)); cam(p, V(0, -1.2, -1.5), 36); }
  else { const p = V(-8, 7, 30).add(shake(t, 0.5, 3)); cam(p, f.clone().multiplyScalar(4), 42); }
  hud.visible = true; drawHud([['ALTITUDE', fmt(alt) + ' FT'], ['DROPPING', fmt(which === 0 ? 26500 : 20000) + ' FT/MIN', '#ff6a5c']], 'OVERSPEED'); }

function shotAt(t) { const b = beatAt(t), lt = t - B[b], dur = DUR[b], u = lt / dur; resetFx(); PL = [];
  strU.uT.value = t; strU.uCam.value.copy(camera.position);
  if (t > TOTAL - 1.0) { diveShot(t, t - TOTAL, 0); return { b: 15 }; }
  switch (b) {
    case 0: diveShot(t, lt, 0); break;
    case 1: { // cruise beauty: above a bright deck, slow orbit front-quarter to side
      setJet(1.5, 0.5 * Math.sin(t * 0.7), 0); env({ deckAlt: 26000, jetAlt: 35000, cov: 0.5, travel: 230 * t });
      const a = lerp(-38, 18, sm(u)) * D2R, r = lerp(58, 50, u); cam(V(Math.sin(a + Math.PI / 2) * r, 1.0 - 2.5 * u, -Math.cos(a + Math.PI / 2) * r * 0.9 + 1), V(0, 1.2, 0.5), 32);
      addStorm(V(9000, (26000 - 35000) * FT, -26000), 0.85, 1.0);
      hud.visible = true; drawHud([['ALTITUDE', '35,000 FT'], ['ROUTE', 'TX TO BAHAMAS']]); break; }
    case 2: { // the storm ahead: wide from behind and above, the tower filling the frame
      setJet(0.5, 4 * smooth(0.4, 1, u), 0); env({ deckAlt: 26000, jetAlt: 35000, cov: 0.55, travel: 230 * t, dark: 0.12 * u });
      addStorm(V(2500, (26000 - 35000) * FT, -24000 + 3000 * u), 0.95, 0.9);
      cam(V(-4 + 2 * u, 0.5, 36 - 10 * u).add(shake(t, 0.05)), V(0, 2.5, -30), 46);
      hud.visible = true; drawHud([['ALTITUDE', '35,000 FT'], ['AHEAD', 'STORMS', '#ffd23a']]); break; }
    case 3: { // ice on the wing: inside the cloud, over the fuselage looking out along the right wing; turbulence bumps
      const bump = 2.2 * vn1(t * 2.3, 9); setJet(1 + bump, 2.5 * vn1(t * 1.7, 5), 0); env({ dark: 1, low: 0.3, fog: 0.012, streaks: 0.5, travel: 230 * t });
      addWisps(t, V(0, 0, 1), 230, 140, 0.6, 0.5); strU.uFlow.value.set(0, -0.08, 1).normalize(); strU.uSpeed.value = 200; strU.uLen.value = 2.6;
      JP.iceM.opacity = 0.0; iceSp.visible = true; placeIce(0.15 + 0.85 * smooth(0, 0.85, u));
      const wp = jet.localToWorld(V(2.7, -0.43, -0.82)); cam(jet.localToWorld(V(3.9 - 0.3 * u, 0.32 + 0.02 * vn1(t * 7, 2), -2.5 + 0.3 * u)), wp, 44, 0.05);
      const alt = 35000 + 350 * vn1(t * 1.6, 3); hud.visible = true; drawHud([['OUTSIDE', '-47°C', '#8fd0ff'], ['ALTITUDE', fmt(Math.round(alt / 10) * 10) + ' FT']], 'ICE + TURBULENCE'); break; }
    case 4: { // asked to climb, then mayday: chase from behind in the storm, nose comes up a little, then drops and rolls
      const k = smooth(0.52, 0.95, u); setJet(lerp(3 * smooth(0, 0.4, u), -30, k) + 1.5 * vn1(t * 3, 1), lerp(2 * vn1(t * 2, 6), 35, k), lerp(0, -5, k));
      env({ dark: 0.9, low: 0.3, fog: 0.008, streaks: 0.4, travel: 230 * t }); const f = fwd(); addWisps(t, f.clone().negate(), 220, 200, 0.62, 0.42);
      strU.uFlow.value.copy(f).negate(); strU.uSpeed.value = 190;
      cam(V(3, 4.2 - 1.5 * k, 30).add(shake(t, 0.15 + 0.4 * k)), f.clone().multiplyScalar(3), 40);
      const alt = lerp(35000, 35250, smooth(0.1, 0.5, u)) - 20000 / 60 * Math.max(0, lt - 0.55 * dur) * 2.5;
      hud.visible = true; drawHud([['ALTITUDE', fmt(Math.round(alt / 10) * 10) + ' FT'], ['PILOT', u < 0.5 ? 'CLIMB 2,000 FT' : 'MAYDAY', u < 0.5 ? '#ffd23a' : '#ff6a5c']], u > 0.55 ? 'MAYDAY' : null); break; }
    case 5: diveShot(t, lt, 5); break;
    case 6: { // Greenacres from above: the jet streaks down onto the road; a flash, then smoke. Cars stop.
      const tI = 0.32 * dur, I = V(4, 0, 30);                       // impact time and spot (on the road)
      env({ low: 1, deckAlt: null, travel: 0, ground: true, fog: 0.00016, fogC: 0xaab9c8 }); sky.visible = true; placeCars(lt, tI + 0.3);
      const dir = V(0.25, -0.8, -0.55).normalize(), sp = 230, dist = (tI - lt) * sp;
      if (lt < tI) { setJet(-52, 10, 15, I.clone().addScaledVector(dir, -dist).add(V(0, 9, 0))); } else jet.visible = false;
      cam(V(-240, 330, 560).add(shake(t, lt > tI ? 1.5 * Math.exp(-(lt - tI) * 2) : 0.25, 5)), V(0, 70, 0), 36, 2);
      if (lt > tI) { flash.visible = true; flash.material.opacity = 0.55 * Math.exp(-(lt - tI) * 9); addSmoke(lt - tI, I); }
      break; }
    case 7: { // the dark stage: the jet turning slowly over a grid
      env({ stage: true }); setJet(2, 0, 200 + 40 * u, V(0, 0, 0)); cam(V(0, 4 + 2 * u, 31 - 5 * u), V(0, 0.3, 0), 36); break; }
    case 8: { // 1: storm gust - arrows slam down on the tail and wing, the jet rolls and noses down
      const k = smooth(0.25, 0.85, u); setJet(lerp(1, -28, k) + 1.2 * vn1(t * 4, 2), lerp(0, 58, k), 0);
      env({ dark: 0.85, low: 0.3, fog: 0.007, streaks: 0.35, travel: 220 * t }); const f = fwd(); addWisps(t, f.clone().negate(), 210, 200, 0.62, 0.4); strU.uFlow.value.copy(f).negate();
      gusts.forEach((a, i) => { a.visible = true; const ph = clamp((u - 0.05 - i * 0.08) / 0.5, 0, 1); a.material.opacity = 0.9 * Math.sin(Math.PI * ph);
        a.position.copy(jet.localToWorld(V([-3.5, 3.5, 0][i], 9 - 9 * ph, [1.5, 1.5, 6.5][i]))); a.quaternion.copy(camera.quaternion); });
      cam(V(-17, 3.5, 24).add(shake(t, 0.3, 4)), V(0, -0.5, 0), 40); break; }
    case 9: { // nose down: the speed builds past the top speed (the red zone)
      const pitch = -32 + 3 * vn1(t * 2, 1); setJet(pitch, 22, 0); env({ dark: 0.45, low: 0.2, deckAlt: 18000, jetAlt: 30000 - 441 * lt, cov: 0.48, travel: 200 * t, fog: 0.002, streaks: 0.22 });
      const f = fwd(); addWisps(t, f.clone().negate(), 200 + 60 * u, 260, 0.75, 0.36); strU.uFlow.value.copy(f).negate(); strU.uSpeed.value = 170 + 80 * u;
      cam(V(24, 2, -6).add(shake(t, 0.25 + 0.3 * u, 6)), V(0, -0.5, -1), 40);
      const sp = lerp(0.5, 0.92, smooth(0, 0.85, u)); hud.visible = true; drawHud([['SPEED', sp > 0.72 ? 'TOO FAST' : 'BUILDING', sp > 0.72 ? '#ff6a5c' : '#ffd23a']], sp > 0.72 ? 'OVERSPEED' : null, sp); break; }
    case 10: { // 2: ice crystals plug the pitot tube (the speed sensor on the nose)
      setJet(0, 0, 0); env({ dark: 1, low: 0.3, fog: 0.02, streaks: 0.0, travel: 230 * t }); addWisps(t, V(0, 0, 1), 230, 60, 0.6, 0.35);
      const tip = JP.pitotR.localToWorld(JP.pitotTipR.clone()); cam(tip.clone().add(V(0.32 - 0.06 * u, 0.06, -0.3 + 0.08 * u)), tip.clone().add(V(0, 0, 0.05)), 30, 0.02);
      crystals.visible = true; const tl = JP.pitotTipR.clone().add(JP.pitotR.position);
      for (let i = 0; i < 260; i++) { const ph = ((hash1(i * 3.3) + t * 1.6) % 1), aim = hash1(i * 7.7) < 0.35 + 0.4 * u; const sp = 0.12 * (1 - ph) + (aim ? 0 : 0.03);
        const a = hash1(i * 5.1) * Math.PI * 2, r = (aim ? 0.006 : 0.025 + 0.06 * hash1(i * 2.2)) + sp * 0.5;
        _m4.makeRotationFromEuler(_e.set(t * 7 + i, i, t * 5)); _m4.setPosition(tl.x + Math.cos(a) * r, tl.y + Math.sin(a) * r, tl.z - 0.9 * (1 - ph) + (aim ? 0 : 0.05 * ph));
        crystals.setMatrixAt(i, _m4); } crystals.instanceMatrix.needsUpdate = true;
      plug.visible = true; plug.scale.set(1, 1, smooth(0.15, 0.85, u) * 1.2 + 0.01); JP.pitotMouthR.material.color.lerpColors(new THREE.Color(0x050505), new THREE.Color(0xe8f2ff), smooth(0.2, 0.7, u));
      hud.visible = true; drawHud([['SPEED GAUGE', u < 0.55 ? 'OK' : 'WRONG', u < 0.55 ? '#ffffff' : '#ff6a5c'], ['SENSOR', u < 0.5 ? 'ICING' : 'BLOCKED', '#8fd0ff']]); break; }
    case 11: { // the gauge says slow while the jet is really too fast: they push the nose down
      const k = smooth(0.2, 0.9, u); setJet(lerp(0, -24, k), lerp(0, 12, k), 0); env({ dark: 0.85, low: 0.3, fog: 0.006, streaks: 0.35, travel: 230 * t });
      const f = fwd(); addWisps(t, f.clone().negate(), 210 + 60 * k, 200, 0.62, 0.38); strU.uFlow.value.copy(f).negate();
      cam(V(-21, 1.5, -12).add(shake(t, 0.2, 2)), V(0, -0.5, -1.5), 38);
      hud.visible = true; drawHud([['GAUGE SAYS', 'TOO SLOW', '#ffd23a'], ['REALLY', 'TOO FAST', '#ff6a5c']], null); break; }
    case 12: { // 3: near the speed of sound a shock wave stands on the wing; the nose tucks down
      const k = smooth(0.2, 0.95, u); setJet(lerp(-12, -34, k), 10, 0); env({ dark: 0.7, low: 0.15, deckAlt: 16000, jetAlt: 28000 - 441 * lt, cov: 0.5, travel: 260 * t, streaks: 0.15 });
      const f = fwd(); addWisps(t, f.clone().negate(), 260, 260, 0.8, 0.3); strU.uFlow.value.copy(f).negate();
      shockU.uT.value = t; shockU.uA.value = smooth(0.05, 0.3, u); pitchArrow.visible = false;   // seen from behind the wing it read as a lollipop
      cam(jet.localToWorld(V(3.9, 0.75, 4.6)).add(shake(t, 0.05, 7)), jet.localToWorld(V(2.6, 0.05, -0.6)), 50, 0.1); break; }   // behind the wing, looking forward: the shock faces the camera
    case 13: { // 4: breaking apart - the tail flutters, then a piece of the stabilizer tears off (slow motion)
      const ts = lt * 0.35, grow = smooth(0, 0.55, u); setJet(-30, 15, 0); env({ dark: 0.4, low: 0.15, deckAlt: 15000, jetAlt: 26000, cov: 0.5, travel: 60 * t, streaks: 0.12 });
      const f = fwd(); addWisps(t, f.clone().negate(), 70, 200, 0.8, 0.3); strU.uFlow.value.copy(f).negate(); strU.uSpeed.value = 60;
      JP.stab.rotation.z = (1.5 + 5.5 * grow) * D2R * Math.sin(ts * 2 * Math.PI * 9); JP.stab.rotation.x = 1.5 * D2R * grow * Math.sin(ts * 2 * Math.PI * 9 + 1);
      const tb = 0.58 * dur; if (lt > tb) { const a = (lt - tb) * 0.35; JP.stabTipR.position.copy(tipHome).add(V(0.6 * a, 0.5 * a - 3 * a * a, 14 * a * a + 3 * a)); JP.stabTipR.rotation.set(a * 9, a * 4, a * 11);
        debris.forEach((d, i) => { d.visible = true; const s = a * (0.8 + hash1(i)); d.position.set(1.4 + 0.5 * hash1(i * 2) + 0.4 * s, 0.1 + (hash1(i * 3) - 0.3) * 2 * s, -0.2 + 16 * s * s + 2 * s); d.rotation.set(s * 20 * hash1(i), s * 15, s * 25 * hash1(i * 5)); }); }
      cam(jet.localToWorld(V(6.5, 4.2, 15.5)).add(shake(t, 0.05, 8)), jet.localToWorld(V(0.6, 2.4, 7.5)), 38, 0.1); break; }
    case 14: { // the last minute + what the NTSB checks (full-screen chart; a calm jet behind it, unseen)
      setJet(0, 0, 0); env({ deckAlt: 26000, jetAlt: 35000, travel: 230 * t }); cam(V(0, 3, 30), V(0, 0, 0), 40); chart.visible = true; drawChart(lt, dur); break; }
    case 15: { // cruise again, golden, above the storms (then the dive, for the loop)
      setJet(1, 0, 0); env({ deckAlt: 26000, jetAlt: 35000, cov: 0.5, travel: 230 * t, dark: 0.05 });
      addStorm(V(-6000, (26000 - 35000) * FT, -24000), 0.85, 0.95); cam(V(-46 + 8 * u, 5, -10 - 10 * u), V(0, 0.3, 0), 34);
      hud.visible = true; drawHud([['STATUS', 'INVESTIGATION'], ['REPORT', 'COMING', '#ffd23a']]); break; }
  }
  return { b }; }

// ------------------------------------------------------------------ frame I/O
function update(t) { t = ((t % TOTAL) + TOTAL) % TOTAL; const r = shotAt(t); fitOverlays();
  sky.position.copy(camera.position); deckU.uCam.value.copy(camera.position); strU.uCam.value.copy(camera.position);
  sun.position.copy(jet.position).addScaledVector(SUN, 40); sun.target.position.copy(jet.position); sun.target.updateMatrixWorld();
  commitPuffs(); return r; }
function stepTo(i) { return update(i / FPS); }
const draw = () => { if (Q.get('nostr')) streaks.visible = false; if (LOOK) LOOK.render(FOCUS, { ao: false, dof: !Q.get('nodof'), rim: !Q.get('norim') }); else renderer.render(scene, camera); };
const gl = renderer.getContext(), px = new Uint8Array(W * H * 4);
window.renderAll = async (f0, f1) => { for (let i = f0; i < f1; i++) { stepTo(i); draw(); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); await fetch('/frame', { method: 'POST', body: px }); } return 'ok'; };
window.renderAtT = t => { stepTo(Math.round(t * FPS)); draw(); return renderer.domElement.toDataURL('image/png'); };
window.dbg = { THREE, scene, camera, jet, JP, update, shotAt };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS); window.READY = true;
window.SCN = { THREE, scene, camera, stepTo, renderer, FPS, B, DUR, TOTAL };
