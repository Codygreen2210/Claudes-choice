// ------------------------------------------------------------------ the desert test track (the room is hidden). The sled stays at the origin and the world
// slides past it (distance D in metres), so nothing ever gets far from the origin at 632 mph.
home.visible = false;
const SEATTOP = 0.74, RAIL = 0.62;
const SKYG = new THREE.Group(); scene.add(SKYG);                    // rides with the camera
{ const g = new THREE.SphereGeometry(200, 32, 20), c = new Float32Array(g.attributes.position.count * 3), lo = new THREE.Color(0xf2e8d8), hi = new THREE.Color(0x4e86c8);
  for (let i = 0; i < g.attributes.position.count; i++) { const y = g.attributes.position.getY(i) / 200, k = Math.pow(clamp(y * 3.2, 0, 1), 0.55), col = lo.clone().lerp(hi, k); c.set([col.r, col.g, col.b], i * 3); }
  g.setAttribute('color', new THREE.BufferAttribute(c, 3));
  SKYG.add(new THREE.Mesh(g, new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.BackSide, depthWrite: false, fog: false }))); }
// far mountains (static, so the near world reads as the thing moving)
const MTN = new THREE.Group(); scene.add(MTN);
{ const mm = new THREE.MeshStandardMaterial({ color: 0x8a7e72, roughness: 1 });
  for (let i = 0; i < 60; i++) { const a = i / 60 * Math.PI * 2, r = 150 + 25 * hash1(i * 3.1), h = 8 + 22 * Math.pow(hash1(i * 7.7), 1.5);
    const m = new THREE.Mesh(new THREE.ConeGeometry(14 + 14 * hash1(i), h, 6), mm); m.position.set(Math.cos(a) * r, h / 2 - 1, Math.sin(a) * r); m.rotation.y = hash1(i * 2) * 3; MTN.add(m); } }
// the ground: gypsum sand plus the track's ties, drawn in the shader from the distance D, and averaged along the run over one frame's travel
// (so at full speed it smears into streaks instead of strobing)
const GU = { uD: { value: 0 }, uStep: { value: 0 } };
const groundM = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.95 });
groundM.onBeforeCompile = sh => { Object.assign(sh.uniforms, GU);
  sh.vertexShader = 'varying vec3 vWp;\n' + sh.vertexShader.replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\n vWp = (modelMatrix * vec4(transformed, 1.0)).xyz;');
  sh.fragmentShader = 'varying vec3 vWp; uniform float uD, uStep;\n' + GLSLN + `
    vec3 sandAt(vec2 p){ float n = vn(p * 1.7) * 0.5 + vn(p * 6.0) * 0.3 + vn(p * 23.0) * 0.2;
      vec3 c = mix(vec3(0.66, 0.58, 0.47), vec3(0.86, 0.79, 0.67), n);
      float onTrack = step(abs(p.x), 0.82);
      float tie = step(fract(p.y / 0.9), 0.2) * onTrack;
      c = mix(c, vec3(0.32, 0.24, 0.17), tie * 0.9);
      c = mix(c, vec3(0.58, 0.52, 0.45), onTrack * (1.0 - tie) * 0.55);
      return c; }
  ` + sh.fragmentShader.replace('#include <map_fragment>', `#include <map_fragment>
    { vec3 acc = vec3(0.0); for (int i = 0; i < 10; i++) { float f = float(i) / 9.0; acc += sandAt(vec2(vWp.x, -vWp.z + uD + f * uStep)); }
      diffuseColor.rgb *= acc / 10.0; }`); };
const ground = new THREE.Mesh(new THREE.PlaneGeometry(700, 700, 1, 1).rotateX(-Math.PI / 2), groundM); ground.receiveShadow = true; scene.add(ground);
// rails (smooth steel: they look the same at any speed)
const railM = new THREE.MeshStandardMaterial({ color: 0x8a8c90, roughness: 0.3, metalness: 0.85 });
for (const x of [-RAIL, RAIL]) { const r = new THREE.Mesh(new THREE.BoxGeometry(0.07, 0.12, 700), railM); r.position.set(x, 0.06, 0); r.receiveShadow = r.castShadow = true; scene.add(r); }
// poles beside the track every 30 m (they stretch into streaks at speed)
const POLES = []; const poleM = new THREE.MeshStandardMaterial({ color: 0x5a4636, roughness: 0.9 });
for (let i = 0; i < 16; i++) { const p = new THREE.Mesh(new THREE.BoxGeometry(0.16, 4.5, 0.16), poleM); p.castShadow = true; scene.add(p);
  const arm = new THREE.Mesh(new THREE.BoxGeometry(1.2, 0.1, 0.1), poleM); arm.position.y = 2.0; p.add(arm); POLES.push({ p, k: i, x: (i % 2 ? -1 : 1) * 3.6 }); }

// ------------------------------------------------------------------ the sled: a steel frame on rail slippers, the seat and straps, nine rockets behind, the scoop underneath
const sled = new THREE.Group(); scene.add(sled);
const steel = new THREE.MeshStandardMaterial({ color: 0xb8bcc2, roughness: 0.35, metalness: 0.8 }), redP = new THREE.MeshStandardMaterial({ color: 0xc8302a, roughness: 0.45, metalness: 0.2 });
const darkM = mat(0x22252a, 0.5, 0.4), seatM = mat(0x3a2e24, 0.8);
for (const x of [-RAIL, RAIL]) { box(0.14, 0.1, 2.4, x, 0.17, -0.25, darkM, 0.02, sled); box(0.06, 0.5, 0.06, x, 0.42, 0.6, steel, 0, sled); box(0.06, 0.5, 0.06, x, 0.42, -1.0, steel, 0, sled); }
box(1.36, 0.08, 2.3, 0, 0.66, -0.25, redP, 0.02, sled);                                 // the deck
box(0.56, 0.06, 0.5, 0, SEATTOP - 0.03, 0.02, seatM, 0.02, sled);                       // seat pan
box(0.56, 0.78, 0.07, 0, SEATTOP + 0.39, -0.24, seatM, 0.02, sled);                     // backrest
box(0.3, 0.26, 0.08, 0, SEATTOP + 0.9, -0.24, seatM, 0.03, sled);                       // headrest
box(0.62, 0.05, 0.3, 0, 0.71, 0.66, steel, 0.01, sled);                                 // footrest plate (its height is set at load from his feet)
const footrest = sled.children[sled.children.length - 1];
for (const x of [-0.31, 0.31]) box(0.05, 0.5, 0.05, x, SEATTOP + 0.2, -0.22, steel, 0, sled);
// the rocket pack: a 3 x 3 block of tubes behind the seat, nozzles facing back
const pack = new THREE.Group(); pack.position.set(0, 1.0, -1.05); sled.add(pack);
box(0.98, 0.98, 0.2, 0, 0, 0.5, redP, 0.03, pack);
const NOZ = [];
for (let r = 0; r < 3; r++) for (let c = 0; c < 3; c++) { const x = (c - 1) * 0.3, y = (r - 1) * 0.3;
  const tube = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 0.9, 20).rotateX(Math.PI / 2), steel); tube.position.set(x, y, 0); tube.castShadow = true; pack.add(tube);
  const nz = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.13, 0.16, 20, 1, true).rotateX(Math.PI / 2), darkM); nz.material = darkM.clone(); nz.material.side = THREE.DoubleSide; nz.position.set(x, y, -0.52); pack.add(nz);
  NOZ.push(V(x, y + 1.0, -1.05 - 0.6)); }
// the scoop: a blade under the front that drops into the water pools
const scoop = box(0.36, 0.22, 0.08, 0, 0.12, 0.95, steel, 0.01, sled); scoop.rotation.x = 0.5;
// his helmet: an open-face shell on the head bone (built in rest space, then moved into the bone's frame)
const helmet = new THREE.Group();
{ G.reset(); G.root.updateMatrixWorld(true); const hc = V(...G.man.headC), hb = G.bones.head;
  const shellM = new THREE.MeshStandardMaterial({ color: 0xe8e6de, roughness: 0.3, metalness: 0.1 });
  const s = new THREE.Mesh(new THREE.SphereGeometry(0.128, 32, 20, 0, Math.PI * 2, 0, Math.PI * 0.42), shellM); s.scale.set(1, 1, 1.08); s.position.set(0, 0.045, 0); helmet.add(s);
  helmet.position.copy(hc); hb.updateMatrixWorld(true); const inv = hb.matrixWorld.clone().invert(); helmet.applyMatrix4(inv); hb.add(helmet); helmet.traverse(o => { if (o.isMesh) o.castShadow = true; }); }
// the harness: two shoulder straps and a lap belt, riding the chest and hips bones
const strapM = new THREE.MeshStandardMaterial({ color: 0x5a6a3a, roughness: 0.85 });
const STRAPS = [];
function strapBand(bone, a, b, w = 0.045) { const g = new THREE.Mesh(new THREE.BoxGeometry(w, 1, 0.012), strapM); g.castShadow = true; scene.add(g); STRAPS.push({ g, bone, a, b }); }

// ------------------------------------------------------------------ fire, smoke, water
const dotTex = canvasTex(64, 64, g => { const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.45, 'rgba(255,255,255,0.55)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); });
function pts(n, color, size, blend = THREE.AdditiveBlending, depthTest = true) { const g = new THREE.BufferGeometry(); const p = new Float32Array(n * 3); g.setAttribute('position', new THREE.BufferAttribute(p, 3)); g.setDrawRange(0, 0);
  const m = new THREE.Points(g, new THREE.PointsMaterial({ color, size, map: dotTex, transparent: true, depthWrite: false, depthTest, blending: blend, toneMapped: blend !== THREE.AdditiveBlending })); m.frustumCulled = false; m.renderOrder = 8; scene.add(m); return { m, p, n }; }
const flameM = new THREE.MeshBasicMaterial({ color: 0xffb24a, transparent: true, opacity: 0.9, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false });
const coreM = new THREE.MeshBasicMaterial({ color: 0xfff4d0, transparent: true, opacity: 1, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false });
const FLAMES = NOZ.map(p => { const g = new THREE.Group(); g.position.copy(p); sled.add(g);
  const o = new THREE.Mesh(new THREE.ConeGeometry(0.12, 1, 18, 1, true).rotateX(-Math.PI / 2).translate(0, 0, -0.5), flameM); g.add(o);
  const c = new THREE.Mesh(new THREE.ConeGeometry(0.06, 0.6, 14, 1, true).rotateX(-Math.PI / 2).translate(0, 0, -0.3), coreM); g.add(c); return g; });
const fireLight = new THREE.PointLight(0xffa040, 0, 9, 1.4); fireLight.position.set(0, 1.0, -1.9); sled.add(fireLight);
const SMOKE = pts(1400, 0xbab2a6, 0.55, THREE.NormalBlending); SMOKE.m.material.opacity = 0.55;
const SPRAY = pts(1400, 0xe8f4ff, 0.12, THREE.NormalBlending); SPRAY.m.material.opacity = 1;
const MIST = pts(470, 0xffffff, 1.5, THREE.NormalBlending); MIST.m.material.opacity = 0.45;
const DUST = pts(900, 0x8a7a64, 1.6, THREE.NormalBlending); DUST.m.material.opacity = 0.55;   // darker than the sand, or it vanishes against it   // dust thrown up off the track behind the sled
const BURST = pts(500, 0xff7a1a, 1.2, THREE.NormalBlending); BURST.m.material.toneMapped = false;   // solid fire: additive washed out against the bright sky                                                    // the ignition fireball, billowing out round the sled
const BSMOKE = pts(500, 0xc8c0b4, 1.3, THREE.NormalBlending); BSMOKE.m.material.opacity = 0.5;
// the water brake: shallow troughs between the rails, one after another
const POOLS = []; const poolWater = new THREE.MeshStandardMaterial({ color: 0x5a8aa8, roughness: 0.1, metalness: 0.1, transparent: true, opacity: 0.85 });
for (let k = 0; k < 9; k++) { const g = new THREE.Group(); scene.add(g);
  box(0.9, 0.12, 0.08, 0, 0.06, -0.9, mat(0x9a948a, 0.9), 0, g); box(0.9, 0.12, 0.08, 0, 0.06, 0.9, mat(0x9a948a, 0.9), 0, g);
  const w = new THREE.Mesh(new THREE.PlaneGeometry(0.86, 1.76).rotateX(-Math.PI / 2), poolWater); w.position.y = 0.1; g.add(w); POOLS.push(g); }

// ------------------------------------------------------------------ the eye up close (beat 7): blood vessels burst, then the dark closes in from the edges
const EY = V(600, 0, 0);
const eyeSet = new THREE.Group(); eyeSet.position.copy(EY); scene.add(eyeSet);
eyeSet.add(new THREE.Mesh(new THREE.SphereGeometry(8, 24, 12), new THREE.MeshBasicMaterial({ color: 0x120608, side: THREE.BackSide })));
const scleraTex = canvasTex(1024, 512, g => { g.fillStyle = '#f2ece4'; g.fillRect(0, 0, 1024, 512);
  for (let i = 0; i < 40; i++) { g.strokeStyle = `rgba(200,80,80,${0.12 + 0.12 * hash1(i)})`; g.lineWidth = 1 + 2 * hash1(i * 3); let x = 512 + (hash1(i * 5) - 0.5) * 900, y = hash1(i * 7) < 0.5 ? 40 : 470; g.beginPath(); g.moveTo(x, y);
    for (let k = 0; k < 10; k++) { x += (hash1(i * 11 + k) - 0.5) * 60; y += (y < 256 ? 1 : -1) * 18; g.lineTo(x, y); } g.stroke(); }
  const ix = 256, iy = 256; const gr = g.createRadialGradient(ix, iy, 10, ix, iy, 110); gr.addColorStop(0, '#0a0a0a'); gr.addColorStop(0.32, '#0a0a0a'); gr.addColorStop(0.34, '#3a6a4a'); gr.addColorStop(0.8, '#5a8a5a'); gr.addColorStop(1, '#2a3a2a');
  g.fillStyle = gr; g.beginPath(); g.ellipse(ix, iy, 110, 110, 0, 0, 7); g.fill(); });
const veinTex = canvasTex(1024, 512, g => { g.clearRect(0, 0, 1024, 512);
  for (let i = 0; i < 90; i++) { g.strokeStyle = `rgba(190,10,20,${0.5 + 0.4 * hash1(i)})`; g.lineWidth = 2 + 5 * hash1(i * 3); let x = 256 + (hash1(i * 5) - 0.5) * 900, y = hash1(i * 7) < 0.5 ? 20 : 490; g.beginPath(); g.moveTo(x, y);
    for (let k = 0; k < 14; k++) { x += (hash1(i * 13 + k) - 0.5) * 70; y += (y < 256 ? 1 : -1) * (12 + 8 * hash1(i + k)); g.lineTo(x, y); } g.stroke(); }
  for (let i = 0; i < 14; i++) { const x = 256 + (hash1(i * 17) - 0.5) * 700, y = 60 + hash1(i * 19) * 390; if (Math.hypot(x - 256, y - 256) < 130) continue; const gr = g.createRadialGradient(x, y, 0, x, y, 70); gr.addColorStop(0, 'rgba(170,0,10,0.85)'); gr.addColorStop(1, 'rgba(170,0,10,0)'); g.fillStyle = gr; g.fillRect(x - 70, y - 70, 140, 140); } });
const eyeball = new THREE.Mesh(new THREE.SphereGeometry(1, 64, 48), new THREE.MeshStandardMaterial({ map: scleraTex, roughness: 0.15 })); eyeSet.add(eyeball);
const veins = new THREE.Mesh(new THREE.SphereGeometry(1.003, 64, 48), new THREE.MeshStandardMaterial({ map: veinTex, transparent: true, opacity: 0, roughness: 0.2, depthWrite: false })); eyeball.add(veins);
const iris = new THREE.Mesh(new THREE.CircleGeometry(0.42, 48), new THREE.MeshStandardMaterial({ map: canvasTex(256, 256, g => { const gr = g.createRadialGradient(128, 128, 20, 128, 128, 128); gr.addColorStop(0, '#050505'); gr.addColorStop(0.36, '#050505'); gr.addColorStop(0.38, '#2a5a3a'); gr.addColorStop(0.8, '#4a8a5a'); gr.addColorStop(1, '#1a2a1a'); g.fillStyle = gr; g.fillRect(0, 0, 256, 256);
  for (let i = 0; i < 60; i++) { const a = i / 60 * 6.283; g.strokeStyle = 'rgba(160,200,140,0.25)'; g.beginPath(); g.moveTo(128 + Math.cos(a) * 50, 128 + Math.sin(a) * 50); g.lineTo(128 + Math.cos(a) * 124, 128 + Math.sin(a) * 124); g.stroke(); } }), roughness: 0.1 }));
iris.position.z = 1.008; eyeball.add(iris);   // in front of the sclera (at 0.985 the white sphere covered the pupil), turning with the eyeball
const eyeLight = new THREE.PointLight(0xfff0e0, 0, 10, 1.2); eyeLight.position.set(1.5, 1.6, 3); eyeSet.add(eyeLight);

// ------------------------------------------------------------------ the seat belt today (beat 8, second half): a car seat, the belt slides across, the buckle clicks in
const BT = V(-600, 0, 0);
const beltSet = new THREE.Group(); beltSet.position.copy(BT); scene.add(beltSet);
beltSet.add(new THREE.Mesh(new THREE.SphereGeometry(8, 24, 12), new THREE.MeshBasicMaterial({ color: 0x1a1c22, side: THREE.BackSide })));
const fabric = canvasTex(256, 256, g => { g.fillStyle = '#16171c'; g.fillRect(0, 0, 256, 256); for (let y = 0; y < 256; y += 4) { g.fillStyle = 'rgba(255,255,255,0.04)'; g.fillRect(0, y, 256, 1); } });
fabric.wrapS = fabric.wrapT = THREE.RepeatWrapping; fabric.repeat.set(3, 3);
box(1.2, 1.4, 0.2, 0, 0.6, -0.2, new THREE.MeshStandardMaterial({ map: fabric, roughness: 0.95 }), 0.08, beltSet);
const webbing = canvasTex(64, 256, g => { g.fillStyle = '#6a6a72'; g.fillRect(0, 0, 64, 256); for (let x = 0; x < 64; x += 3) { g.fillStyle = 'rgba(0,0,0,0.18)'; g.fillRect(x, 0, 1, 256); } });
const belt = new THREE.Mesh(new THREE.BoxGeometry(0.12, 1.6, 0.01), new THREE.MeshStandardMaterial({ map: webbing, roughness: 0.8 })); beltSet.add(belt);
const tongue = new THREE.Group(); beltSet.add(tongue);
box(0.14, 0.12, 0.02, 0, 0, 0, mat(0xc8ccd2, 0.25, 0.9), 0.005, tongue); box(0.07, 0.1, 0.012, 0, -0.1, 0, mat(0xc8ccd2, 0.25, 0.9), 0.003, tongue);
const latch = new THREE.Group(); latch.position.set(0.42, -0.1, 0.02); beltSet.add(latch);
box(0.16, 0.26, 0.09, 0, 0, 0, mat(0x111216, 0.5), 0.02, latch); box(0.12, 0.07, 0.025, 0, 0.06, 0.05, new THREE.MeshStandardMaterial({ color: 0xe0281e, emissive: 0x501008, roughness: 0.4 }), 0.008, latch);
const beltLight = new THREE.PointLight(0xfff2e0, 0, 8, 1.0); beltLight.position.set(0.5, 0.8, 1.4); beltSet.add(beltLight);

// ------------------------------------------------------------------ the gauge: speed (mph) and g, stuck to the camera so it stays sharp (drawn after the film look)
scene.add(camera);
const gaugeC = document.createElement('canvas'); gaugeC.width = 512; gaugeC.height = 600;
const gaugeT = new THREE.CanvasTexture(gaugeC); gaugeT.colorSpace = THREE.SRGBColorSpace;
const gauge = new THREE.Mesh(new THREE.PlaneGeometry(0.066, 0.0773), new THREE.MeshBasicMaterial({ map: gaugeT, transparent: true, depthTest: false, depthWrite: false, toneMapped: false }));
gauge.renderOrder = 30; camera.add(gauge); gauge.position.set(0.034, 0.048, -0.2); gauge.visible = false;
let GSHOWN = '';
function drawGauge(mph, gs, label) { const key = Math.round(mph) + '|' + gs.toFixed(1) + '|' + label; if (key === GSHOWN) return; GSHOWN = key;
  const g = gaugeC.getContext('2d'); g.clearRect(0, 0, 512, 600); const cx = 256, cy = 256, R = 220, a0 = Math.PI * 0.75, a1 = Math.PI * 2.25, MAX = 700;
  g.fillStyle = 'rgba(8,10,14,0.82)'; g.beginPath(); g.arc(cx, cy, R + 22, 0, 7); g.fill();
  g.lineWidth = 26; g.strokeStyle = 'rgba(255,255,255,0.12)'; g.beginPath(); g.arc(cx, cy, R - 20, a0, a1); g.stroke();
  const am = a0 + (a1 - a0) * Math.min(1, mph / MAX); g.strokeStyle = mph > 600 ? '#ff4030' : '#ffd23a'; g.beginPath(); g.arc(cx, cy, R - 20, a0, am); g.stroke();
  g.fillStyle = '#ffffff'; g.font = 'bold 26px Arial'; g.textAlign = 'center';
  for (let v = 0; v <= MAX; v += 100) { const a = a0 + (a1 - a0) * v / MAX; g.save(); g.translate(cx + Math.cos(a) * (R - 60), cy + Math.sin(a) * (R - 60)); g.fillText(v, 0, 9); g.restore(); }
  g.strokeStyle = '#ffffff'; g.lineWidth = 8; g.beginPath(); g.moveTo(cx, cy); g.lineTo(cx + Math.cos(am) * (R - 36), cy + Math.sin(am) * (R - 36)); g.stroke();
  g.fillStyle = '#ffffff'; g.beginPath(); g.arc(cx, cy, 14, 0, 7); g.fill();
  g.font = 'bold 92px Arial'; g.lineWidth = 10; g.strokeStyle = 'rgba(0,0,0,0.8)'; g.strokeText(Math.round(mph), cx, cy + 128); g.fillText(Math.round(mph), cx, cy + 128);
  g.font = 'bold 34px Arial'; g.fillStyle = '#c8ccd4'; g.fillText('MPH', cx, cy + 168);
  g.fillStyle = 'rgba(8,10,14,0.82)'; g.beginPath(); g.roundRect(96, 506, 320, 84, 20); g.fill();
  g.font = 'bold 62px Arial'; g.fillStyle = gs >= 20 ? '#ff4030' : '#7fe0ff'; g.fillText(label || (gs.toFixed(gs < 10 ? 1 : 0) + ' G'), cx, 570);
  gaugeT.needsUpdate = true; }
// the dark that closes in from the edges (a full-frame shader plane; never a shrinking ring)
const darkM2 = new THREE.ShaderMaterial({ uniforms: { uR: { value: 2 }, uA: { value: 0 } }, transparent: true, depthTest: false, depthWrite: false,
  vertexShader: 'varying vec2 vU; void main(){ vU = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
  fragmentShader: 'uniform float uR, uA; varying vec2 vU; void main(){ vec2 p = (vU - 0.5) * vec2(1.0, 1.78); float d = length(p); float k = smoothstep(uR - 0.18, uR + 0.02, d); gl_FragColor = vec4(0.0, 0.0, 0.0, max(k, uA)); }' });
const darkPlane = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), darkM2); darkPlane.renderOrder = 25; camera.add(darkPlane); darkPlane.position.set(0, 0, -0.1); darkPlane.visible = false;
