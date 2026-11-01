// ------------------------------------------------------------------ the night dock (the room is hidden); sky, stars and the moon ride with the camera
home.visible = false;
const STANDP = V(0, 0, -1.5);                                      // where he stands on the dock, facing +z (the shore, the camera); the sea and the moon behind him
const MD = V(-0.1, 0.5, -1).normalize();                            // the moon's direction (behind him, about 26 deg up)
const SKY = new THREE.Group(); scene.add(SKY);                      // moves with the camera, so the sky and the moon have no parallax
{ const g = new THREE.SphereGeometry(140, 32, 20), c = new Float32Array(g.attributes.position.count * 3), lo = new THREE.Color(0x1c2c4c), hi = new THREE.Color(0x03060f);
  for (let i = 0; i < g.attributes.position.count; i++) { const y = g.attributes.position.getY(i) / 140, k = Math.pow(clamp(y * 2.2, 0, 1), 0.6), col = lo.clone().lerp(hi, k); c.set([col.r, col.g, col.b], i * 3); }
  g.setAttribute('color', new THREE.BufferAttribute(c, 3));
  SKY.add(new THREE.Mesh(g, new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.BackSide, depthWrite: false, fog: false }))); }
const skyMat = SKY.children[0].material;
const STARS = (() => { const n = 1600, p = new Float32Array(n * 3), s = new Float32Array(n);
  for (let i = 0; i < n; i++) { const u = hash1(i * 1.7) * 2 - 1, a = hash1(i * 3.1 + 2) * Math.PI * 2, r = Math.sqrt(1 - u * u); p.set([Math.cos(a) * r * 130, u * 130, Math.sin(a) * r * 130], i * 3); s[i] = 0.4 + 1.6 * Math.pow(hash1(i * 5.3 + 1), 6); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(p, 3)); g.setAttribute('sz', new THREE.BufferAttribute(s, 1));
  const m = new THREE.ShaderMaterial({ uniforms: { uK: { value: 1 }, uT: { value: 0 }, uH: { value: H } }, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    vertexShader: 'attribute float sz; uniform float uT, uH; varying float vA; void main(){ vec4 mv = modelViewMatrix * vec4(position,1.0); gl_Position = projectionMatrix * mv;' +
      ' float tw = 0.75 + 0.25 * sin(uT + position.x * 1.3 + position.z); vA = tw * min(1.0, sz); gl_PointSize = max(1.5, sz * uH / 900.0 * 2.2); }',
    fragmentShader: 'uniform float uK; varying float vA; void main(){ float d = length(gl_PointCoord - 0.5); if (d > 0.5) discard; gl_FragColor = vec4(vec3(0.85,0.9,1.0), vA * uK * smoothstep(0.5, 0.1, d)); }' });
  const o = new THREE.Points(g, m); o.frustumCulled = false; o.renderOrder = -1; SKY.add(o); return m; })();
const moonTex = canvasTex(512, 512, g => { g.fillStyle = '#d8d6cc'; g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 9; i++) { g.fillStyle = 'rgba(120,118,112,0.35)'; g.beginPath(); g.ellipse(80 + hash1(i * 4.1) * 360, 80 + hash1(i * 2.7) * 360, 40 + hash1(i * 9.2) * 70, 30 + hash1(i * 6.6) * 50, hash1(i) * 3, 0, 7); g.fill(); }
  for (let i = 0; i < 140; i++) { const x = hash1(i * 7.7) * 512, y = hash1(i * 3.3 + 9) * 512, r = 2 + 18 * Math.pow(hash1(i * 1.9), 3);
    g.fillStyle = 'rgba(90,88,84,0.35)'; g.beginPath(); g.arc(x, y, r, 0, 7); g.fill(); g.strokeStyle = 'rgba(250,250,245,0.45)'; g.lineWidth = Math.max(1, r * 0.25); g.beginPath(); g.arc(x - r * 0.15, y - r * 0.15, r, 3.4, 5.6); g.stroke(); } });
const skyMoon = new THREE.Mesh(new THREE.SphereGeometry(5.4, 48, 32), new THREE.MeshBasicMaterial({ map: moonTex, transparent: true, fog: false, toneMapped: false }));
skyMoon.position.copy(MD).multiplyScalar(100); skyMoon.lookAt(0, 0, 0); SKY.add(skyMoon);
const glowTex = canvasTex(256, 256, g => { const gr = g.createRadialGradient(128, 128, 0, 128, 128, 128); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.25, 'rgba(255,255,255,0.35)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 256, 256); });
const moonGlow = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, color: 0xb8c8ff, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, fog: false, toneMapped: false }));
moonGlow.scale.setScalar(34); moonGlow.position.copy(MD).multiplyScalar(101); SKY.add(moonGlow);
const moonLight = new THREE.DirectionalLight(0xaabfff, 0); moonLight.position.copy(MD).multiplyScalar(20); scene.add(moonLight); scene.add(moonLight.target);
moonLight.castShadow = true; moonLight.shadow.mapSize.set(2048, 2048); { const S = moonLight.shadow.camera; S.left = -4; S.right = 4; S.top = 4; S.bottom = -4; S.near = 1; S.far = 40; moonLight.shadow.bias = -0.0004; moonLight.shadow.normalBias = 0.02; }

// the sea: one big plane with rolling waves (periods divide the video length, so the loop has no seam)
const WAVES = [[3, 0.035, V(0.8, 0, 0.6)], [5, 0.022, V(-0.4, 0, 1)], [8, 0.012, V(0.95, 0, -0.3)]].map(([k, a, d]) => ({ w: 2 * Math.PI * k / TOTAL * 4, a, d: d.normalize(), kx: 0.9 + 0.6 * k / 8 }));
function seaMat(color) { const m = new THREE.MeshStandardMaterial({ color, roughness: 0.18, metalness: 0.0 });
  m.userData.uT = { value: 0 };
  m.onBeforeCompile = sh => { sh.uniforms.uT = m.userData.uT;
    const W_ = WAVES.map(w => `vec4(${w.d.x.toFixed(3)}, ${w.d.z.toFixed(3)}, ${w.kx.toFixed(3)}, ${w.a.toFixed(3)})`), WS = WAVES.map(w => w.w.toFixed(5));
    sh.vertexShader = 'uniform float uT;\n' + sh.vertexShader.replace('#include <beginnormal_vertex>', `vec3 objectNormal = vec3(0.0, 0.0, 1.0); float hgt = 0.0; vec2 dh = vec2(0.0);
      { vec4 W[3]; W[0] = ${W_[0]}; W[1] = ${W_[1]}; W[2] = ${W_[2]}; float S[3]; S[0] = ${WS[0]}; S[1] = ${WS[1]}; S[2] = ${WS[2]};
        for (int i = 0; i < 3; i++) { float ph = dot(W[i].xy, vec2(position.x, -position.y)) * W[i].z - uT * S[i]; hgt += W[i].w * sin(ph); dh += W[i].w * W[i].z * cos(ph) * W[i].xy; } }
      objectNormal = normalize(vec3(-dh.x, dh.y, 1.0));`).replace('#include <begin_vertex>', 'vec3 transformed = vec3(position.x, position.y, position.z + hgt);'); };
  return m; }
const sea = new THREE.Mesh(new THREE.PlaneGeometry(400, 400, 220, 220).rotateX(0), seaMat(0x0e2238)); sea.material.roughness = 0.32; sea.rotation.x = -Math.PI / 2; sea.receiveShadow = true; scene.add(sea);
const glit = new THREE.Mesh(new THREE.PlaneGeometry(3.2, 60), new THREE.MeshBasicMaterial({ map: canvasTex(64, 512, g => { g.fillStyle = '#000'; g.fillRect(0, 0, 64, 512);
  for (let i = 0; i < 260; i++) { const y = hash1(i * 2.3) * 512, x = 32 + (hash1(i * 5.1) - 0.5) * 50 * (0.3 + y / 512); g.fillStyle = `rgba(230,236,255,${0.3 + 0.6 * hash1(i)})`; g.fillRect(x - 6, y, 4 + 10 * hash1(i * 3.7), 2); } }),
  transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false }));
glit.rotation.x = -Math.PI / 2; glit.renderOrder = 2; scene.add(glit);

// the dock: planks on pilings; a post with a rod holder at the sea end; a lantern
const wood = canvasTex(512, 128, g => { g.fillStyle = '#6a5038'; g.fillRect(0, 0, 512, 128); for (let i = 0; i < 70; i++) { g.strokeStyle = `rgba(${40 + 30 * hash1(i)},${28 + 20 * hash1(i * 2)},18,${0.25 + 0.3 * hash1(i * 3)})`; g.lineWidth = 1 + 2 * hash1(i * 5); const y = hash1(i * 7.3) * 128; g.beginPath(); g.moveTo(0, y); g.bezierCurveTo(170, y + 5 * (hash1(i * 9) - 0.5), 340, y - 4, 512, y + 3); g.stroke(); } });
wood.wrapS = wood.wrapT = THREE.RepeatWrapping;
const plankM = new THREE.MeshStandardMaterial({ map: wood, roughness: 0.85 }), postM = new THREE.MeshStandardMaterial({ color: 0x4a3626, roughness: 0.9 });
const dock = new THREE.Group(); scene.add(dock);
for (let z = -2.55; z < 4.5; z += 0.21) { const p = box(2.3, 0.05, 0.19, 0, -0.025, z, plankM, 0.008, dock); p.rotation.y = (hash1(z * 9) - 0.5) * 0.012; p.position.y -= 0.004 * hash1(z * 5); }
for (const x of [-1.05, 1.05]) box(0.12, 0.16, 7.1, x, -0.13, 0.95, postM, 0, dock);
// the pilings: wood with a wet band and barnacles below the high-tide line
const pileTex = canvasTex(128, 512, g => { const gr = g.createLinearGradient(0, 0, 0, 512); gr.addColorStop(0, '#5a4430'); gr.addColorStop(0.17, '#4a3a2a'); gr.addColorStop(0.2, '#1e2a22'); gr.addColorStop(1, '#14201a'); g.fillStyle = gr; g.fillRect(0, 0, 128, 512);
  for (let i = 0; i < 160; i++) { const y = 108 + hash1(i * 3.3) * 400, x = hash1(i * 7.1) * 128; g.fillStyle = `rgba(${200 + 40 * hash1(i)},${200 + 30 * hash1(i * 2)},190,0.8)`; g.beginPath(); g.arc(x, y, 2 + 4 * hash1(i * 5.5), 0, 7); g.fill(); }
  for (let i = 0; i < 40; i++) { g.strokeStyle = 'rgba(30,20,12,0.4)'; const x = hash1(i * 4.4) * 128; g.beginPath(); g.moveTo(x, 0); g.lineTo(x + 3, 512); g.stroke(); } });
const pileM = new THREE.MeshStandardMaterial({ map: pileTex, roughness: 0.9 });
const PILES = [];
const FOAM = [];   // a ring of foam where the sea meets each piling: shows the tide sinking at a glance
const foamM = new THREE.MeshBasicMaterial({ color: 0xcfe0f0, transparent: true, opacity: 0.7, depthWrite: false });
for (const z of [-2.45, -0.75, 0.95, 2.65]) for (const x of [-1.12, 1.12]) { const p = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.12, 3.2, 18), pileM); p.position.set(x, -1.5, z); p.castShadow = p.receiveShadow = true; dock.add(p); PILES.push(p);
  const f = new THREE.Mesh(new THREE.RingGeometry(0.12, 0.2, 28).rotateX(-Math.PI / 2), foamM); f.position.set(x, 0, z); dock.add(f); FOAM.push(f); }
const post = new THREE.Mesh(new THREE.CylinderGeometry(0.075, 0.08, 1.05, 14), postM); post.position.set(1.12, 0.5, -2.45); post.castShadow = true; dock.add(post);
const holder = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.3, 12), mat(0x22262c, 0.4, 0.6)); dock.add(holder);
const ROD0 = V(1.17, 0.72, -2.52), RODTIP = V(1.75, 2.55, -4.1);
holder.position.copy(ROD0).add(RODTIP.clone().sub(ROD0).normalize().multiplyScalar(0.05)); holder.quaternion.setFromUnitVectors(V(0, 1, 0), RODTIP.clone().sub(ROD0).normalize());
const rod = new THREE.Group(); dock.add(rod); rod.position.copy(ROD0);
const RODLEN = RODTIP.distanceTo(ROD0);
{ const m = new THREE.Mesh(new THREE.CylinderGeometry(0.006, 0.016, RODLEN, 10), mat(0x1a1c22, 0.35, 0.3)); m.position.y = RODLEN / 2; rod.add(m);
  const grip = new THREE.Mesh(new THREE.CylinderGeometry(0.022, 0.022, 0.32, 12), mat(0x2a2018, 0.9)); grip.position.y = 0.16; rod.add(grip);
  const reel = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.05, 16).rotateZ(Math.PI / 2), mat(0x8a8e96, 0.3, 0.8)); reel.position.set(0, 0.42, 0.04); rod.add(reel); }
rod.quaternion.setFromUnitVectors(V(0, 1, 0), RODTIP.clone().sub(ROD0).normalize());
const lineG = new THREE.BufferGeometry().setFromPoints([V(0, 0, 0), V(0, 0, 0)]);
const fishLine = new THREE.Line(lineG, new THREE.LineBasicMaterial({ color: 0xc8d0d8, transparent: true, opacity: 0.6 })); fishLine.frustumCulled = false; scene.add(fishLine);
const bobber = new THREE.Group(); scene.add(bobber);
{ const t = new THREE.Mesh(new THREE.SphereGeometry(0.045, 16, 10, 0, 7, 0, Math.PI / 2), mat(0xd02a22, 0.4)); bobber.add(t); const b = new THREE.Mesh(new THREE.SphereGeometry(0.045, 16, 10, 0, 7, Math.PI / 2, Math.PI / 2), mat(0xf2f2ee, 0.4)); bobber.add(b); }
const BOB = V(2.6, 0, -6.4);
const lantern = new THREE.Group(); lantern.position.set(-0.75, 0, -2.2); dock.add(lantern);
const lanternGlass = new THREE.MeshStandardMaterial({ color: 0xffe0a0, emissive: 0xffb050, emissiveIntensity: 2.2, roughness: 0.3, transparent: true, opacity: 0.9 });
{ box(0.16, 0.03, 0.16, 0, 0.015, 0, mat(0x2a2a2e, 0.4, 0.7), 0.005, lantern); box(0.13, 0.18, 0.13, 0, 0.12, 0, lanternGlass, 0.01, lantern); box(0.16, 0.03, 0.16, 0, 0.225, 0, mat(0x2a2a2e, 0.4, 0.7), 0.005, lantern);
  const hd = new THREE.Mesh(new THREE.TorusGeometry(0.05, 0.006, 6, 16, Math.PI), mat(0x2a2a2e, 0.4, 0.7)); hd.position.y = 0.24; lantern.add(hd); }
const lanternLight = new THREE.PointLight(0xffb868, 2.4, 6, 1.6); lanternLight.position.set(-0.75, 0.3, -2.2); scene.add(lanternLight);
// the shore behind the camera: a dark tree line far off, a few house lights (only seen in wide shots)
const shore = new THREE.Group(); scene.add(shore);
{ const tm = new THREE.MeshStandardMaterial({ color: 0x0a120e, roughness: 1 }); for (let i = 0; i < 40; i++) { const x = -60 + i * 3 + 2 * hash1(i), h = 4 + 5 * hash1(i * 3.1); const c = new THREE.Mesh(new THREE.ConeGeometry(1.8, h, 7), tm); c.position.set(x, h / 2 - 0.5, 40 + 6 * hash1(i * 7)); shore.add(c); } }

// ------------------------------------------------------------------ space stage (beats 1, 3, 7, 8): Earth, the Moon, the Sun, light on its way
const SP = V(600, 0, 0);
const space = new THREE.Group(); space.position.copy(SP); scene.add(space);
function nz2(x, y) { let v = 0, a = 0.5, f = 1; for (let o = 0; o < 5; o++) { v += a * (vn1(x * f + 10 * o, 3 + o) * 0.5 + vn1(y * f + 7 * o, 11 + o) * 0.5); a *= 0.5; f *= 2.1; } return v; }
const earthTex = canvasTex(1024, 512, g => { const im = g.createImageData(1024, 512);
  for (let y = 0; y < 512; y++) for (let x = 0; x < 1024; x++) { const lon = x / 1024 * 6.283, lat = (y / 512 - 0.5) * Math.PI;
    const px = Math.cos(lat) * Math.cos(lon) * 2.2, py = Math.cos(lat) * Math.sin(lon) * 2.2, pz = Math.sin(lat) * 2.2;
    const n = vn1(px * 1.1 + 3, 1) * 0.35 + vn1(py * 1.3 + pz, 2) * 0.35 + vn1(pz * 1.7 + px * 0.6, 4) * 0.3 + 0.18 * vn1(px * 4 + py * 3, 7);
    const land = n > 0.12, ice = Math.abs(lat) > 1.22 + 0.06 * vn1(lon * 3, 9), i = (y * 1024 + x) * 4;
    let c = land ? [60 + 50 * n, 135 + 40 * n, 60] : [22, 80 + 30 * (n + 0.5), 175 + 30 * (n + 0.5)];
    if (land && n > 0.32) c = [190, 165, 110]; if (ice) c = [235, 240, 245];
    im.data[i] = c[0]; im.data[i + 1] = c[1]; im.data[i + 2] = c[2]; im.data[i + 3] = 255; }
  g.putImageData(im, 0, 0); });
const earth = new THREE.Group(); space.add(earth);
const earthBall = new THREE.Mesh(new THREE.SphereGeometry(1, 96, 64), new THREE.MeshStandardMaterial({ map: earthTex, roughness: 0.75 })); earth.add(earthBall);
const atmo = new THREE.Mesh(new THREE.SphereGeometry(1.035, 64, 48), new THREE.MeshBasicMaterial({ color: 0x5aa0ff, transparent: true, opacity: 0.16, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.BackSide }));
earth.add(atmo);
const axisM = new THREE.MeshBasicMaterial({ color: 0xffe14a, toneMapped: false });
const axis = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.018, 3.4, 8), axisM); earth.add(axis);
const upRef = new THREE.Mesh(new THREE.CylinderGeometry(0.008, 0.008, 3.0, 8), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.45, toneMapped: false })); space.add(upRef);
const tiltTag = new THREE.Sprite(new THREE.SpriteMaterial({ map: (() => { const c = document.createElement('canvas'); c.width = 512; c.height = 256; const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.userData.c = c; return t; })(), depthTest: false, transparent: true, toneMapped: false }));
tiltTag.scale.set(1.0, 0.5, 1); tiltTag.renderOrder = 12; tiltTag.material.color.setScalar(2.4); space.add(tiltTag); let tiltShown = -1;   // color over 1: the output pass tone-maps everything, so a plain sprite came out dim
function drawTilt(d) { if (d === tiltShown) return; tiltShown = d; const c = tiltTag.material.map.userData.c, g = c.getContext('2d'); g.clearRect(0, 0, 512, 256);
  g.font = 'bold 170px Arial'; g.textAlign = 'center'; g.lineWidth = 18; g.strokeStyle = 'rgba(0,0,0,0.85)'; g.strokeText(d + '°', 256, 190); g.fillStyle = '#ffe14a'; g.fillText(d + '°', 256, 190); tiltTag.material.map.needsUpdate = true; }
const tideM = new THREE.MeshStandardMaterial({ color: 0x5ab4ff, emissive: 0x1a6ad0, emissiveIntensity: 0.9, transparent: true, opacity: 0.5, roughness: 0.2, depthWrite: false });
const tide = new THREE.Mesh(new THREE.SphereGeometry(1, 64, 48), tideM); space.add(tide);
const smoon = new THREE.Mesh(new THREE.SphereGeometry(0.27, 48, 32), new THREE.MeshStandardMaterial({ map: moonTex, roughness: 0.95 })); space.add(smoon);
const SMOON = V(0.35, 2.85, -0.8); smoon.position.copy(SMOON);
const popRing = new THREE.Mesh(new THREE.RingGeometry(0.3, 0.36, 48), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false, side: THREE.DoubleSide }));
space.add(popRing); popRing.position.copy(SMOON);
const sunBall = new THREE.Mesh(new THREE.SphereGeometry(3.5, 48, 32), new THREE.MeshBasicMaterial({ color: 0xfff2c0, toneMapped: false })); space.add(sunBall);
const sunGlow = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, color: 0xffc860, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false })); space.add(sunGlow);
const SUNPOS = V(-16, 5, 6); sunBall.position.copy(SUNPOS); sunGlow.position.copy(SUNPOS); sunGlow.scale.setScalar(34);
const sunEdge = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, color: 0xffc050, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false })); sunEdge.scale.setScalar(3.2); sunEdge.position.set(-2.1, 0.3, 0); space.add(sunEdge);
const spaceSun = new THREE.DirectionalLight(0xfff0d8, 0); spaceSun.position.copy(SP).add(SUNPOS); spaceSun.target.position.copy(SP); scene.add(spaceSun); scene.add(spaceSun.target);
const earthShine = new THREE.PointLight(0xc8d8ff, 0, 8, 1.2); space.add(earthShine);
// light on its way from the Moon to Earth: a packet of glowing dots along the line
const dotTex = canvasTex(64, 64, g => { const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.4, 'rgba(255,255,255,0.6)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); });
function dots(n, color, size, depthTest = false) { const g = new THREE.BufferGeometry(); const p = new Float32Array(n * 3); g.setAttribute('position', new THREE.BufferAttribute(p, 3)); g.setDrawRange(0, 0);
  const m = new THREE.Points(g, new THREE.PointsMaterial({ color, size, map: dotTex, transparent: true, depthWrite: false, depthTest, blending: THREE.AdditiveBlending, toneMapped: false })); m.frustumCulled = false; m.renderOrder = 9; scene.add(m); return { m, p, n }; }
const PHOT = dots(160, 0xfff4d0, 0.09, true);
const PULL = dots(240, 0xffd070, 0.06, true);                         // the Sun's pull on the sea (beat 3)

// ------------------------------------------------------------------ the beach (beat 5): a nest in the sand, hatchlings crawling toward a street light, the sea behind
const BE = V(0, 0, 600);
const beach = new THREE.Group(); beach.position.copy(BE); scene.add(beach);
const sandTex = canvasTex(512, 512, g => { g.fillStyle = '#8a7a5c'; g.fillRect(0, 0, 512, 512); for (let i = 0; i < 9000; i++) { const v = 100 + 60 * hash1(i * 1.3); g.fillStyle = `rgba(${v + 30},${v + 15},${v - 20},0.5)`; g.fillRect(hash1(i * 7.9) * 512, hash1(i * 3.1) * 512, 2, 2); } });
sandTex.wrapS = sandTex.wrapT = THREE.RepeatWrapping; sandTex.repeat.set(30, 30);
{ const sg = new THREE.PlaneGeometry(120, 120, 120, 120).rotateX(-Math.PI / 2); const P = sg.attributes.position;
  for (let i = 0; i < P.count; i++) { const x = P.getX(i), z = P.getZ(i); const fl = smooth(3, 6, Math.hypot(x, (z - 2) * 0.6)); P.setY(i, (z < -4 ? (z + 4) * 0.06 : 0) + fl * (0.04 * vn1(x * 1.3 + z * 0.7, 5) + 0.03 * vn1(x * 3.1, 8))); } sg.computeVertexNormals();
  const s = new THREE.Mesh(sg, new THREE.MeshStandardMaterial({ map: sandTex, color: 0x9a907c, roughness: 0.95 })); s.receiveShadow = true; beach.add(s); }
const beachSea = new THREE.Mesh(new THREE.PlaneGeometry(200, 100, 120, 60), seaMat(0x0c1c2c)); beachSea.rotation.x = -Math.PI / 2; beachSea.position.set(0, -0.32, -58); beach.add(beachSea);
const nest = new THREE.Mesh(new THREE.TorusGeometry(0.1, 0.03, 10, 24).rotateX(Math.PI / 2), new THREE.MeshStandardMaterial({ map: sandTex, roughness: 1 })); nest.position.set(0, 0.012, -1.0); beach.add(nest);
const hole = new THREE.Mesh(new THREE.CircleGeometry(0.1, 24).rotateX(-Math.PI / 2), mat(0x2a2016, 1)); hole.position.set(0, 0.006, -1.0); beach.add(hole);
const lampPole = new THREE.Group(); lampPole.position.set(1.8, 0, 9); beach.add(lampPole);
{ box(0.12, 2.8, 0.12, 0, 1.4, 0, mat(0x2a2c30, 0.5, 0.6), 0, lampPole); box(0.9, 0.08, 0.12, -0.42, 2.75, 0, mat(0x2a2c30, 0.5, 0.6), 0, lampPole);
  const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.13, 16, 10), new THREE.MeshBasicMaterial({ color: 0xfff0c8, toneMapped: false })); bulb.position.set(-0.8, 2.65, 0); lampPole.add(bulb);
  const gl_ = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, color: 0xffa040, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false })); gl_.scale.setScalar(1.3); gl_.position.copy(bulb.position); lampPole.add(gl_); }
const streetLight = new THREE.PointLight(0xffa850, 0, 40, 1.0); streetLight.position.set(1.0, 2.6, 609); scene.add(streetLight);
const scuteTex = canvasTex(256, 256, g => { g.fillStyle = '#3a3428'; g.fillRect(0, 0, 256, 256); g.strokeStyle = '#1a1712'; g.lineWidth = 6;
  for (let r = 0; r < 4; r++) for (let c = 0; c < 4; c++) { const x = 32 + c * 64 + (r % 2) * 32, y = 32 + r * 64; g.beginPath(); for (let k = 0; k < 6; k++) { const a = k / 6 * 6.283; g.lineTo(x + 34 * Math.cos(a), y + 34 * Math.sin(a)); } g.closePath(); g.stroke(); } });
const turtleM = new THREE.MeshStandardMaterial({ color: 0x2c2a26, roughness: 0.55 }), shellM = new THREE.MeshStandardMaterial({ map: scuteTex, roughness: 0.85 }), edgeM = new THREE.MeshStandardMaterial({ color: 0x3a3630, roughness: 0.7 });
const TURT = [];
for (let i = 0; i < 14; i++) { const t = new THREE.Group(); beach.add(t); t.scale.setScalar(1.6);
  const sh = new THREE.Mesh(new THREE.SphereGeometry(0.03, 24, 16), shellM); sh.scale.set(1, 0.38, 1.3); sh.position.y = 0.014; sh.castShadow = true; t.add(sh);
  const rim = new THREE.Mesh(new THREE.TorusGeometry(0.03, 0.0035, 6, 28).rotateX(Math.PI / 2), edgeM); rim.scale.set(1, 1, 1.3); rim.position.y = 0.012; t.add(rim);
  const hd = new THREE.Mesh(new THREE.SphereGeometry(0.0115, 14, 10), turtleM); hd.scale.set(1, 0.85, 1.25); hd.position.set(0, 0.016, 0.046); t.add(hd);
  for (const s of [-1, 1]) { const e = new THREE.Mesh(new THREE.SphereGeometry(0.0028, 8, 6), new THREE.MeshBasicMaterial({ color: 0x050505 })); e.position.set(s * 0.0075, 0.02, 0.052); t.add(e); }
  const fl = []; for (const [x, z, s, front] of [[0.026, 0.024, 1, true], [-0.026, 0.024, -1, true], [0.02, -0.03, 1, false], [-0.02, -0.03, -1, false]]) { const p = new THREE.Group(); p.position.set(x, 0.01, z); t.add(p);
    const f = new THREE.Mesh(new THREE.SphereGeometry(1, 12, 8), turtleM); f.scale.set(front ? 0.03 : 0.013, 0.003, front ? 0.011 : 0.008); f.position.set(s * (front ? 0.026 : 0.01), 0, front ? -0.008 : -0.004); f.rotation.y = s * (front ? 0.35 : 0.5); p.add(f);
    const ed = new THREE.Mesh(new THREE.SphereGeometry(1, 10, 6), edgeM); ed.scale.copy(f.scale).multiply(V(1.03, 0.6, 1.03)); ed.position.copy(f.position).add(V(0, -0.0012, 0)); ed.rotation.copy(f.rotation); p.add(ed); fl.push([p, s, front]); }
  const ang = (hash1(i * 4.2) - 0.5) * 1.3, r0 = 0.03 + 0.08 * hash1(i * 2.2);
  TURT.push({ g: t, fl, ang, start: V(Math.sin(ang * 2) * r0, 0.0, -1.0 + Math.cos(ang * 2) * r0), delay: 0.09 * i + 0.1 * hash1(i), sp: 0.22 + 0.08 * hash1(i * 6.1), ph: hash1(i * 9) * 6 }); }

// ------------------------------------------------------------------ the reef at night (beat 6): branching coral holding egg bundles that never let go
const RF = V(-600, 0, 0);
const reef = new THREE.Group(); reef.position.copy(RF); scene.add(reef);
{ const fl = new THREE.Mesh(new THREE.PlaneGeometry(60, 60, 60, 60).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ map: sandTex, color: 0x6a7a8a, roughness: 1 })); reef.add(fl);
  const P = fl.geometry.attributes.position; for (let i = 0; i < P.count; i++) P.setY(i, 0.15 * vn1(P.getX(i) * 0.5, 2) + 0.1 * vn1(P.getZ(i) * 0.7, 6)); fl.geometry.computeVertexNormals(); }
const EGGS = [];
const coralCols = [0xd8705a, 0xc85a8a, 0xe0a050, 0x9a6ad0, 0xd06070];
function branch(parent, p, dir, len, r, depth, col, seed) {
  const end = p.clone().addScaledVector(dir, len), m = new THREE.Mesh(new THREE.CylinderGeometry(r * 0.75, r, len, 8), new THREE.MeshStandardMaterial({ color: col, roughness: 0.7, emissive: col, emissiveIntensity: 0.05 }));
  m.position.copy(p).lerp(end, 0.5); m.quaternion.setFromUnitVectors(V(0, 1, 0), dir); parent.add(m);
  if (depth === 0) { const e = new THREE.Mesh(new THREE.SphereGeometry(r * 1.7, 10, 8), new THREE.MeshStandardMaterial({ color: 0xffc0d0, emissive: 0xff7aa0, emissiveIntensity: 0.6, roughness: 0.4 })); e.position.copy(end); parent.add(e); EGGS.push({ e, ph: hash1(seed) * 6.28 }); return; }
  for (let k = 0; k < 2 + (hash1(seed) > 0.6 ? 1 : 0); k++) { const s2 = seed * 3.7 + k * 1.9, nd = dir.clone().add(V(hash1(s2) - 0.5, 0.1, hash1(s2 + 1) - 0.5).multiplyScalar(1.9)).normalize();
    branch(parent, end, nd, len * 0.9, r * 0.74, depth - 1, col, s2); } }
for (let i = 0; i < 46; i++) { const a = hash1(i * 3.3) * 6.28, d = 0.25 + 2.4 * Math.sqrt(hash1(i * 5.7)), x = Math.cos(a) * d, z = Math.min(0.5, Math.sin(a) * d - 0.9);
  branch(reef, V(x, 0.05, z), V((hash1(i * 2.9) - 0.5) * 0.4, 1, (hash1(i * 4.9) - 0.5) * 0.4).normalize(), 0.1 + 0.08 * hash1(i), 0.032 + 0.014 * hash1(i * 8.8), 3, coralCols[i % coralCols.length], i + 1); }
branch(reef, V(0.12, 0.05, 0.55), V(0, 1, 0), 0.12, 0.035, 3, 0xe07060, 99);   // the hero coral, nearest the camera
for (let i = 0; i < 30; i++) { const b = new THREE.Mesh(new THREE.SphereGeometry(0.22 + 0.15 * hash1(i * 2.2), 24, 16), new THREE.MeshStandardMaterial({ color: 0x9a8a5a, roughness: 0.9 })); b.scale.y = 0.6;
  const a = hash1(i * 8.1) * 6.28, d = 1 + 3 * hash1(i * 1.1); b.position.set(Math.cos(a) * d, 0.08, Math.sin(a) * d - 1); reef.add(b); }
const reefLight = new THREE.PointLight(0x7ab0ff, 0, 14, 1.0); reefLight.position.set(-599.2, 2.6, 2.4); scene.add(reefLight);
const surf = new THREE.Mesh(new THREE.PlaneGeometry(80, 80, 120, 120), seaMat(0x1a3a5a)); surf.rotation.x = Math.PI / 2; surf.position.set(0, 5.2, 0); surf.material.side = THREE.DoubleSide; reef.add(surf);
const SNOW = dots(400, 0xc8dcff, 0.025, true);
