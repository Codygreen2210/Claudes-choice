// ------------------------------------------------------------------ the garage: concrete floor, walls, a sectional door (shut), shelves, a work light; a pickup truck idling
const home = new THREE.Group(); scene.add(home);
scene.remove(lamp);
const GDOOR_Z = 3.5, GW0 = -3.0, GW1 = 2.6, GBACK = -3.6, GH = 2.9;
const conc = canvasTex(512, 512, g => { g.fillStyle = '#8c8a86'; g.fillRect(0, 0, 512, 512); for (let i = 0; i < 9000; i++) { const c = 110 + Math.random() * 60; g.fillStyle = `rgba(${c},${c},${c - 4},0.25)`; g.fillRect(Math.random() * 512, Math.random() * 512, 2, 2); }
  for (let i = 0; i < 6; i++) { g.fillStyle = `rgba(40,36,30,${0.08 + Math.random() * 0.1})`; g.beginPath(); g.ellipse(Math.random() * 512, Math.random() * 512, 30 + Math.random() * 60, 20 + Math.random() * 40, Math.random() * 3, 0, 6.28); g.fill(); }
  g.fillStyle = 'rgba(30,30,30,0.5)'; g.fillRect(255, 0, 2, 512); g.fillRect(0, 255, 512, 2); });
conc.wrapS = conc.wrapT = THREE.RepeatWrapping; conc.repeat.set(4, 4);
const floor = new THREE.Mesh(new THREE.PlaneGeometry(14, 14).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ map: conc, roughness: 0.85 })); floor.receiveShadow = true; home.add(floor);
const drywall = mat(0xd8d4ca, 0.95);
box(GW1 - GW0, GH, 0.12, (GW0 + GW1) / 2, GH / 2, GBACK, drywall, 0, home);
box(0.12, GH, GDOOR_Z - GBACK, GW0, GH / 2, (GDOOR_Z + GBACK) / 2, drywall, 0, home);
box(0.12, GH, GDOOR_Z - GBACK, GW1, GH / 2, (GDOOR_Z + GBACK) / 2, drywall, 0, home);
box(GW1 - GW0 + 0.2, 0.1, GDOOR_Z - GBACK + 0.2, (GW0 + GW1) / 2, GH, (GDOOR_Z + GBACK) / 2, mat(0xcfcac0, 0.95), 0, home);   // ceiling
// the sectional door: four panels that roll up into the ceiling (beat 6 opens it); a wall strip around it
const gdoor = new THREE.Group(); home.add(gdoor);
const panelTex = canvasTex(512, 128, g => { g.fillStyle = '#e8e6e0'; g.fillRect(0, 0, 512, 128); g.strokeStyle = 'rgba(0,0,0,0.18)'; g.lineWidth = 4; for (let i = 0; i < 4; i++) g.strokeRect(14 + i * 124, 18, 108, 92); g.fillStyle = 'rgba(0,0,0,0.25)'; g.fillRect(0, 124, 512, 4); });
const GPANELS = []; for (let i = 0; i < 4; i++) { const p = new THREE.Mesh(new THREE.BoxGeometry(GW1 - GW0 - 0.3, 0.6, 0.05), new THREE.MeshStandardMaterial({ map: panelTex, roughness: 0.6 })); p.castShadow = true; p.receiveShadow = true; gdoor.add(p); GPANELS.push(p); }
box(0.3, GH, 0.14, GW0 + 0.15, GH / 2, GDOOR_Z, drywall, 0, home); box(0.3, GH, 0.14, GW1 - 0.15, GH / 2, GDOOR_Z, drywall, 0, home); box(GW1 - GW0, GH - 2.45, 0.14, (GW0 + GW1) / 2, (GH + 2.45) / 2, GDOOR_Z, drywall, 0, home);
function setGarageDoor(k) { GPANELS.forEach((p, i) => { const s = i * 0.6 + 0.3, y = s + k * 2.4;                  // each panel rides up the track, then lies flat under the ceiling
  if (y < 2.4) { p.position.set((GW0 + GW1) / 2, y, GDOOR_Z - 0.04); p.rotation.x = 0; } else { p.position.set((GW0 + GW1) / 2, 2.45, GDOOR_Z - 0.04 - (y - 2.4)); p.rotation.x = Math.PI / 2; } }); }
setGarageDoor(0);
// outside (seen when the door is up): driveway, lawn, sky
const outside = new THREE.Group(); scene.add(outside);
{ const sky = new THREE.Mesh(new THREE.PlaneGeometry(40, 16), new THREE.MeshBasicMaterial({ color: 0xa8cce8 })); sky.position.set(0, 6, 22); sky.rotation.y = Math.PI; outside.add(sky);
  const lawn = new THREE.Mesh(new THREE.PlaneGeometry(40, 18).rotateX(-Math.PI / 2), mat(0x5d8a3a, 0.95)); lawn.position.set(0, -0.005, 12.5); outside.add(lawn);
  const drive = new THREE.Mesh(new THREE.PlaneGeometry(5, 12).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ map: conc, roughness: 0.85 })); drive.position.set(-0.2, 0.002, 9.5); outside.add(drive); }
// shelves with boxes and cans, a workbench, a hanging work light
{ const wood = mat(0x9a7a50, 0.8), steelS = mat(0x6a6e74, 0.5, 0.5);
  for (const y of [0.9, 1.5, 2.1]) box(0.45, 0.04, 2.2, GW0 + 0.28, y, -1.8, steelS, 0, home);
  for (const z of [-2.85, -0.75]) box(0.04, 2.2, 0.04, GW0 + 0.48, 1.1, z, steelS, 0, home);
  for (const [y, z, w, h, c] of [[0.92, -2.4, 0.4, 0.3, 0xb08a5a], [0.92, -1.9, 0.35, 0.25, 0x8a6a40], [1.52, -2.5, 0.3, 0.22, 0xc81e1e], [1.52, -1.6, 0.4, 0.35, 0xb08a5a], [2.12, -2.2, 0.38, 0.3, 0x3a6ab0], [0.92, -1.2, 0.3, 0.4, 0x2a2a2e], [1.52, -1.05, 0.25, 0.3, 0xe8c040]])
    box(0.38, h, w, GW0 + 0.28, y + h / 2 + 0.02, z, mat(c, 0.7), 0.01, home);
  box(2.2, 0.06, 0.65, 0.2, 0.92, GBACK + 0.4, wood, 0.01, home); for (const x of [-0.8, 1.2]) box(0.06, 0.9, 0.55, x, 0.45, GBACK + 0.4, wood, 0, home);
  box(1.8, 0.9, 0.03, 0.2, 1.7, GBACK + 0.08, mat(0x8a6a48, 0.9), 0, home);    // pegboard
  for (let i = 0; i < 7; i++) box(0.04, 0.22, 0.03, -0.5 + i * 0.22, 1.75, GBACK + 0.12, mat(0x3a3a40, 0.4, 0.6), 0.005, home); }
const workLight = new THREE.PointLight(0xfff0d8, 9, 9, 1.4); workLight.position.set(-0.6, 2.6, 0.8); workLight.castShadow = true; workLight.shadow.mapSize.set(1024, 1024); scene.add(workLight);
{ const fx = new THREE.Mesh(new THREE.BoxGeometry(1.2, 0.05, 0.14), new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xfff4e0, emissiveIntensity: 1.2 })); fx.position.set(-0.6, GH - 0.06, 0.8); home.add(fx); }
// the CO alarm on the wall by the door (beat 6)
const alarm = new THREE.Group(); alarm.position.set(GW0 + 0.07, 1.55, 2.6); alarm.rotation.y = Math.PI / 2; home.add(alarm);
const alarmCanvas = document.createElement('canvas'); alarmCanvas.width = 256; alarmCanvas.height = 256; const alarmTex = new THREE.CanvasTexture(alarmCanvas); alarmTex.colorSpace = THREE.SRGBColorSpace;
let alarmState = -1;
function drawAlarm(on) { const g = alarmCanvas.getContext('2d'); g.fillStyle = '#f2f0ea'; g.fillRect(0, 0, 256, 256);
  g.fillStyle = '#2a2a2e'; g.font = 'bold 24px sans-serif'; g.textAlign = 'center'; g.fillText('CARBON MONOXIDE', 128, 50); g.fillText('ALARM', 128, 82);
  g.fillStyle = '#1a2a1a'; g.fillRect(58, 104, 140, 58); g.fillStyle = on ? '#ff3a2a' : '#5aff6a'; g.font = 'bold 44px monospace'; g.fillText(on ? 'CO' : '0', 128, 150);
  g.fillStyle = on ? '#ff2a20' : '#4a1a1a'; g.beginPath(); g.arc(128, 206, 18, 0, 6.28); g.fill(); g.fillStyle = 'rgba(0,0,0,0.3)'; for (let i = 0; i < 5; i++) g.fillRect(40 + i * 40, 232, 22, 6);
  alarmTex.needsUpdate = true; }
drawAlarm(false);
{ const body = new THREE.Mesh(new RoundedBoxGeometry(0.16, 0.16, 0.05, 3, 0.02), mat(0xf2f0ea, 0.5)); alarm.add(body);
  const face = new THREE.Mesh(new THREE.PlaneGeometry(0.15, 0.15), new THREE.MeshStandardMaterial({ map: alarmTex, emissive: 0xffffff, emissiveMap: alarmTex, emissiveIntensity: 0.25 })); face.position.z = 0.026; alarm.add(face); }
const alarmLight = new THREE.PointLight(0xff2a20, 0, 1.2, 2); alarmLight.position.set(0, -0.05, 0.12); alarm.add(alarmLight);

// ------------------------------------------------------------------ the pickup (nose toward the back wall); its tailpipe at the back left
const truck = new THREE.Group(); scene.add(truck);
const TPIPE = V(-1.02, 0.34, 1.1);                                   // the tailpipe's open end: a side exit just ahead of the back left wheel (truck space = world)
{ const paintT = new THREE.MeshPhysicalMaterial({ color: 0x1e3a5a, roughness: 0.35, clearcoat: 1, clearcoatRoughness: 0.1, metalness: 0.3 }), darkT = mat(0x18191b, 0.7), chromeT = mat(0xdddddd, 0.18, 1);
  const glassT = new THREE.MeshPhysicalMaterial({ color: 0x2c353c, roughness: 0.05, transparent: true, opacity: 0.88 });
  const B = (w, h, d, x, y, z, m, r = 0.04) => box(w, h, d, x, y, z, m, r, truck);
  B(1.96, 0.62, 1.6, 0, 0.86, -1.85, paintT, 0.1);                   // hood / engine
  B(1.96, 0.7, 1.45, 0, 0.9, -0.33, paintT, 0.08);                   // cab lower
  B(1.86, 0.62, 1.3, 0, 1.55, -0.36, glassT, 0.08);                  // cab glass
  B(1.9, 0.08, 1.36, 0, 1.88, -0.36, paintT, 0.04);                  // roof
  for (const s of [-1, 1]) B(0.08, 0.6, 0.08, s * 0.92, 1.55, -1.0, paintT, 0.02);
  B(1.96, 0.18, 2.3, 0, 0.62, 1.55, paintT, 0.04);                   // bed floor
  for (const s of [-1, 1]) B(0.07, 0.55, 2.3, s * 0.95, 0.98, 1.55, paintT, 0.03);   // bed sides (top 1.25)
  B(1.96, 0.55, 0.07, 0, 0.98, 2.68, paintT, 0.03);                  // tailgate
  B(2.0, 0.16, 0.14, 0, 0.5, 2.78, chromeT, 0.04);                   // rear bumper
  B(2.0, 0.2, 0.16, 0, 0.55, -2.68, chromeT, 0.05);                  // front bumper
  B(1.6, 0.34, 0.04, 0, 0.98, -2.66, mat(0x2a2c30, 0.4, 0.6), 0.02); // grille
  for (const s of [-1, 1]) { B(0.3, 0.14, 0.04, s * 0.72, 1.0, 2.71, new THREE.MeshStandardMaterial({ color: 0xaa1010, emissive: 0x880000, emissiveIntensity: 0.6 }), 0.02);
    B(0.32, 0.14, 0.04, s * 0.62, 1.0, -2.69, new THREE.MeshStandardMaterial({ color: 0xffffee, emissive: 0x666655 }), 0.02); }
  for (const [x, z] of [[-0.88, -1.85], [0.88, -1.85], [-0.88, 1.75], [0.88, 1.75]]) { const t = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.4, 0.3, 28).rotateZ(Math.PI / 2), darkT); t.position.set(x, 0.4, z); t.castShadow = true; truck.add(t);
    const h = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.22, 0.31, 18).rotateZ(Math.PI / 2), chromeT); h.position.set(x, 0.4, z); truck.add(h); }
  const pipe = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.4, 14).rotateZ(Math.PI / 2), chromeT); pipe.position.copy(TPIPE).add(V(0.2, 0, 0)); truck.add(pipe);
  const hole = new THREE.Mesh(new THREE.CircleGeometry(0.032, 14).rotateY(-Math.PI / 2), mat(0x0a0a0a, 0.9)); hole.position.copy(TPIPE).add(V(-0.002, 0, 0)); truck.add(hole); }

// ------------------------------------------------------------------ exhaust: camera-facing puffs placed from time alone; a haze that fills the garage
function puffs(n, frag, blending) {
  const geo = new THREE.InstancedBufferGeometry().copy(new THREE.PlaneGeometry(1, 1)); geo.instanceCount = 0;
  const P = new Float32Array(n * 4), O = new Float32Array(n * 4), aP = new THREE.InstancedBufferAttribute(P, 4), aO = new THREE.InstancedBufferAttribute(O, 4);
  aP.setUsage(THREE.DynamicDrawUsage); aO.setUsage(THREE.DynamicDrawUsage); geo.setAttribute('aP', aP); geo.setAttribute('aO', aO);
  const m = new THREE.ShaderMaterial({ uniforms: { uT: { value: 0 }, uGain: { value: 1 } }, transparent: true, depthWrite: false, blending,
    vertexShader: `attribute vec4 aP, aO; varying vec2 vUv; varying vec4 vO;
      void main(){ vec3 c = aP.xyz; vec3 R = vec3(viewMatrix[0][0], viewMatrix[1][0], viewMatrix[2][0]), U = vec3(viewMatrix[0][1], viewMatrix[1][1], viewMatrix[2][1]);
        float a = aO.w * 6.2831; vec2 p = mat2(cos(a), -sin(a), sin(a), cos(a)) * position.xy; vec3 w = c + (R * p.x + U * p.y) * aP.w;
        vUv = uv; vO = aO; gl_Position = projectionMatrix * viewMatrix * vec4(w, 1.0); }`,
    fragmentShader: `uniform float uT, uGain; ${GLSLN} varying vec2 vUv; varying vec4 vO;
      void main(){ ${frag} }` });
  const mesh = new THREE.Mesh(geo, m); mesh.frustumCulled = false; mesh.renderOrder = 6; scene.add(mesh);
  let k = 0;
  return { mesh, m, begin() { k = 0; }, add(p, size, heat, alpha, seed) { if (k >= n || alpha < 0.004) return; P.set([p.x, p.y, p.z, size], k * 4); O.set([heat, alpha, 0, seed], k * 4); k++; },
    end() { geo.instanceCount = k; aP.needsUpdate = true; aO.needsUpdate = true; } };
}
const SMOKE = puffs(700, `vec2 p = vUv * 2.0 - 1.0; float s = vO.w * 13.0;
  float n = vn(p * 2.0 + s - vec2(0.0, uT * 0.8)) * 0.6 + vn(p * 5.0 - s * 2.0) * 0.4;
  float r = dot(p, p) + (n - 0.5) * 0.8; float a = (1.0 - smoothstep(0.25, 0.95, r)) * vO.y; if (a < 0.004) discard;
  vec3 col = mix(vec3(0.16, 0.15, 0.15), vec3(0.93, 0.94, 0.96), vO.x) * (0.85 + 0.3 * n);
  gl_FragColor = vec4(col, a);`, THREE.NormalBlending);
// the exhaust: puffs pour out of the pipe, roll along the floor and rise; k = how much (0..1), fill = how full the garage is (0..1)
function exhaust(t, k, fill) {
  if (k > 0.01) for (let i = 0; i < 260; i++) { const a = ((t * (0.35 + 0.25 * hash1(i * 3.1)) + hash1(i * 1.9)) % 1), ang = hash1(i * 5.1) * 6.283;
    const sp = V(-0.8 + Math.cos(ang) * 0.3, 0, Math.sin(ang) * 0.6).multiplyScalar(a * (1.1 + 0.8 * hash1(i * 2.7)));     // out the side, spreading along the floor
    const p = TPIPE.clone().add(V(-0.05, 0.02, 0)).add(sp).add(V(vn1(t * 0.7 + i, 2) * 0.15 * a, 0.9 * a * a + 0.05 * a, vn1(t * 0.6 + i, 4) * 0.1 * a));
    p.z = Math.min(p.z, GDOOR_Z - 0.15 - 0.3 * hash1(i)); p.x = clamp(p.x, GW0 + 0.2, GW1 - 0.2);
    SMOKE.add(p, 0.05 + 0.45 * a, 0.75, Math.sin(Math.PI * Math.min(1, a * 1.2)) * 0.42 * k, hash1(i * 6.6)); }
  if (fill > 0.01) for (let i = 0; i < 160; i++) { const p = V(GW0 + 0.4 + hash1(i * 7.1) * (GW1 - GW0 - 0.8) + vn1(t * 0.2 + i, 1) * 0.3, 0.3 + hash1(i * 3.3) * 2.3 * Math.min(1, fill * 1.4), GBACK + 0.4 + hash1(i * 5.9) * (GDOOR_Z - GBACK - 0.8) + vn1(t * 0.2 + i, 3) * 0.3);
    SMOKE.add(p, 0.6 + 0.6 * hash1(i * 2.2), 0.7, 0.1 * fill * (0.5 + 0.5 * hash1(i * 9.1)), hash1(i * 4.7)); } }

// ------------------------------------------------------------------ x-ray: the glow body (same skeleton) with the heart and the brain
const xrayMat = new THREE.MeshStandardMaterial({ color: 0x000000, emissive: 0x58b8ff, emissiveIntensity: 1, transparent: true, opacity: 1, depthWrite: false, blending: THREE.AdditiveBlending, roughness: 1, metalness: 0 });
xrayMat.onBeforeCompile = sh => { sh.fragmentShader = sh.fragmentShader.replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\n  totalEmissiveRadiance *= 0.015 + 0.85 * pow(1.0 - abs(dot(normalize(normal), normalize(vViewPosition))), 2.4);'); };
const XRAY = [], NORMAL = [];
G.root.traverse(o => { if (!o.isMesh || o.userData.xray) return; NORMAL.push(o); });
for (const o of Object.entries(G.meshes).filter(([n]) => !/^(hair|hairCards|sole)/.test(n)).map(([, m]) => m)) {
  let x; if (o.isSkinnedMesh) { x = new THREE.SkinnedMesh(o.geometry, xrayMat); x.bind(o.skeleton, o.bindMatrix); } else x = new THREE.Mesh(o.geometry, xrayMat);
  x.userData.xray = true; x.position.copy(o.position); x.quaternion.copy(o.quaternion); x.scale.copy(o.scale); x.frustumCulled = false; x.castShadow = false; x.renderOrder = 5; o.parent.add(x); XRAY.push(x); }
G.reset(); G.root.updateMatrixWorld(true);
const toLocal = (bone, p) => bone.worldToLocal(p.clone());
const HC = V(...G.man.headC);
// the heart: two lobes and a point, slightly to his left of centre; it squeezes with each beat
const heartM = new THREE.MeshStandardMaterial({ color: 0x8a1a2a, emissive: 0xff2a3a, emissiveIntensity: 0.9, roughness: 0.4 });
const heart = new THREE.Group(); G.bones.chest.add(heart); heart.position.copy(toLocal(G.bones.chest, V(-0.025, 1.31, -0.04)));
{ const hg = new THREE.Group(); heart.add(hg); hg.rotation.z = -0.45; hg.rotation.x = 0.2;
  for (const s of [-1, 1]) { const l = new THREE.Mesh(new THREE.SphereGeometry(0.03, 24, 16), heartM); l.position.set(s * 0.02, 0.012, 0); hg.add(l); }
  const pt = new THREE.Mesh(new THREE.ConeGeometry(0.043, 0.07, 24).rotateX(Math.PI), heartM); pt.position.y = -0.03; pt.scale.z = 0.75; hg.add(pt);
  const ao = new THREE.Mesh(new THREE.TorusGeometry(0.02, 0.008, 8, 16, Math.PI), heartM); ao.position.set(0.0, 0.045, 0); hg.add(ao); }
const heartGlow = new THREE.PointLight(0xff3040, 0, 0.6, 2); heart.add(heartGlow);
// the brain (beat 5: electric storm)
const brainM = new THREE.MeshStandardMaterial({ color: 0x9a5a7a, emissive: 0xff8ab8, emissiveIntensity: 0.6, roughness: 0.45 });
const brain = new THREE.Group(); G.bones.head.add(brain); brain.position.copy(toLocal(G.bones.head, HC.clone().add(V(0, 0.035, 0.012)))); brain.scale.setScalar(0.86);
{ const g = new THREE.SphereGeometry(0.072, 48, 32); const p = g.attributes.position; for (let i = 0; i < p.count; i++) { const v = V(p.getX(i), p.getY(i), p.getZ(i)).normalize();
    const fold = 0.0035 * Math.sin(v.x * 40 + Math.sin(v.y * 25) * 2) * Math.sin(v.z * 35 + v.y * 20) + (Math.abs(v.x) < 0.06 ? -0.006 : 0);
    v.multiplyScalar(0.072 + fold); v.y *= 0.82; v.z *= 1.18; p.setXYZ(i, v.x, v.y, v.z); } g.computeVertexNormals(); brain.add(new THREE.Mesh(g, brainM)); }
// lightning in the brain: jagged glowing tubes, rebuilt from time alone
const ORGANS = [heart, brain];
let XRON = false, XRNEW = false;
function setXray(k) { if ((k > 0.01) !== XRON) { XRON = k > 0.01; XRNEW = XRON; }   // the first draw after the ghost comes on comes out blank: draw() renders that frame twice
  for (const x of XRAY) x.visible = k > 0.01; xrayMat.emissiveIntensity = 0.75 * k;
  for (const o of NORMAL) o.visible = k < 0.6; for (const o of ORGANS) o.visible = k > 0.5; }
// his phone (scrolling while the truck warms up)
const phone = new THREE.Group(); scene.add(phone);
const phoneCanvas = document.createElement('canvas'); phoneCanvas.width = 160; phoneCanvas.height = 330;
const phoneTex = new THREE.CanvasTexture(phoneCanvas); phoneTex.colorSpace = THREE.SRGBColorSpace;
function drawPhone(scroll) { const g = phoneCanvas.getContext('2d'); g.fillStyle = '#111418'; g.fillRect(0, 0, 160, 330);
  for (let i = -1; i < 5; i++) { const y = i * 96 - (scroll % 96); g.fillStyle = ['#e85a4a', '#4a9ae8', '#f2c14a', '#6ad08a', '#b06ae8'][(i + Math.floor(scroll / 96) + 50) % 5]; g.fillRect(10, y + 8, 140, 64); g.fillStyle = '#3a3f48'; g.fillRect(10, y + 78, 90, 8); }
  phoneTex.needsUpdate = true; }
{ box(0.072, 0.152, 0.009, 0, 0, 0, mat(0x1c1d22, 0.3, 0.6), 0.004, phone); const s = new THREE.Mesh(new THREE.PlaneGeometry(0.064, 0.142), new THREE.MeshBasicMaterial({ map: phoneTex, toneMapped: false })); s.position.z = 0.0048; phone.add(s); }
drawPhone(0); let phoneState = -1;
// the dark that closes in when he passes out (a ring in front of the camera)
scene.add(camera);
const vigM = new THREE.ShaderMaterial({ uniforms: { uR: { value: 1.5 }, uAsp: { value: W / H } }, transparent: true, depthTest: false, depthWrite: false,
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
  fragmentShader: `uniform float uR, uAsp; varying vec2 vUv;
    void main(){ vec2 p = (vUv - 0.5) * vec2(uAsp, 1.0) * 2.0; float d = length(p);       // 0 at the centre, ~1 at the top/bottom edges
      float a = smoothstep(uR, uR + 0.45, d); gl_FragColor = vec4(0.0, 0.0, 0.0, a); }` });
const vig = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), vigM); vig.position.z = -0.1; vig.renderOrder = 20; camera.add(vig);
function setVignette(k) { vig.visible = k > 0.01; const h = 2 * 0.1 * Math.tan(camera.fov * D2R / 2), w = h * camera.aspect; vig.scale.set(w * 1.02, h * 1.02, 1);   // always covers the whole frame
  vigM.uniforms.uR.value = lerp(1.3, 0.02, k); }                      // the clear middle shrinks: the dark closes in from the edges
const blackM = new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, depthTest: false, depthWrite: false }); const black = new THREE.Mesh(new THREE.PlaneGeometry(10, 10), blackM); black.position.z = -0.11; black.renderOrder = 21; camera.add(black);

// ------------------------------------------------------------------ inside a blood vessel (beat 2): red cells carrying oxygen; carbon monoxide pushes the oxygen off and holds on
const VES = V(40, 0, 0);
const vessel = new THREE.Group(); vessel.position.copy(VES); scene.add(vessel);
const vesLight = new THREE.PointLight(0xffe0e0, 0, 6, 1.2); vesLight.position.set(0, 0.3, 0.6); vessel.add(vesLight);
{ const wallTex = canvasTex(512, 256, g => { g.fillStyle = '#8a1a24'; g.fillRect(0, 0, 512, 256); for (let i = 0; i < 300; i++) { g.fillStyle = `rgba(${150 + Math.random() * 60 | 0},30,40,0.35)`; g.beginPath(); g.ellipse(Math.random() * 512, Math.random() * 256, 8 + Math.random() * 20, 4 + Math.random() * 8, 0, 0, 6.28); g.fill(); } });
  wallTex.wrapS = wallTex.wrapT = THREE.RepeatWrapping; wallTex.repeat.set(3, 2);
  const tube = new THREE.Mesh(new THREE.CylinderGeometry(0.9, 0.9, 12, 40, 1, true).rotateX(Math.PI / 2), new THREE.MeshStandardMaterial({ map: wallTex, side: THREE.BackSide, roughness: 0.6, emissive: 0x3a0a10, emissiveIntensity: 0.5 })); vessel.add(tube);
  vessel.add(new THREE.Mesh(new THREE.SphereGeometry(8, 16, 8), new THREE.MeshBasicMaterial({ color: 0x1a0306, side: THREE.BackSide }))); }
const rbcG = (() => { const pts = []; for (let i = 0; i <= 24; i++) { const r = 0.16 * i / 24; const h = 0.035 * (0.45 + 1.2 * (r / 0.16) ** 2 - 1.4 * (r / 0.16) ** 4) * Math.sqrt(Math.max(0, 1 - (r / 0.16) ** 2)) + 0.004; pts.push(new THREE.Vector2(r, h)); }
  for (let i = 24; i >= 0; i--) pts.push(new THREE.Vector2(0.16 * i / 24, -pts[i].y)); return new THREE.LatheGeometry(pts, 40); })();   // a red blood cell: a dimpled disc
const rbcM = new THREE.MeshStandardMaterial({ color: 0xd8242e, emissive: 0x5a0a10, emissiveIntensity: 0.4, roughness: 0.4 });
const RBCN = 9, RBC = []; for (let i = 0; i < RBCN; i++) { const m = new THREE.Mesh(rbcG, rbcM.clone()); vessel.add(m); RBC.push(m); }
const o2M = new THREE.MeshStandardMaterial({ color: 0xff4a4a, emissive: 0xc01010, emissiveIntensity: 0.6, roughness: 0.3 });   // oxygen: two red balls
const cM = new THREE.MeshStandardMaterial({ color: 0x1a1a1e, roughness: 0.4 }), oM = o2M;                                       // carbon monoxide: a black ball and a red ball
function mol(a, b, r) { const g = new THREE.Group(); const m1 = new THREE.Mesh(new THREE.SphereGeometry(r, 16, 12), a), m2 = new THREE.Mesh(new THREE.SphereGeometry(r, 16, 12), b); m1.position.x = -r * 0.8; m2.position.x = r * 0.8; g.add(m1, m2); vessel.add(g); return g; }
const O2S = [], COS = []; for (let i = 0; i < RBCN * 2; i++) { O2S.push(mol(o2M, o2M, 0.022)); COS.push(mol(cM, oM, 0.024)); }
function vtag(text, color, w) { const c = canvasTex(512, 128, g => { g.fillStyle = 'rgba(10,10,14,0.75)'; g.beginPath(); g.roundRect(4, 4, 504, 120, 30); g.fill(); g.fillStyle = color; g.font = 'bold 64px sans-serif'; g.textAlign = 'center'; g.fillText(text, 256, 86); });
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: c, depthTest: false, toneMapped: false })); s.scale.set(w, w / 4, 1); s.renderOrder = 10; vessel.add(s); return s; }
const tagO2 = vtag('OXYGEN', '#ff8a8a', 0.34), tagCO = vtag('CO', '#e8e8e8', 0.2);
const _M = new THREE.Matrix4(), _Q = new THREE.Quaternion(), _S = V(1, 1, 1);
// a big red X over the open-door shot (beat 6: still not safe)
const redX = new THREE.Sprite(new THREE.SpriteMaterial({ map: canvasTex(256, 256, g => { g.strokeStyle = '#ff2a20'; g.lineWidth = 34; g.lineCap = 'round'; g.beginPath(); g.moveTo(40, 40); g.lineTo(216, 216); g.moveTo(216, 40); g.lineTo(40, 216); g.stroke(); }), depthTest: false, toneMapped: false, transparent: true }));
redX.scale.set(1.6, 1.6, 1); redX.position.set(-0.3, 1.2, 2.2); redX.renderOrder = 12; scene.add(redX);
// a sick green tint over the picture (beats 4-5)
const tintM = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 1, depthTest: false, depthWrite: false, blending: THREE.MultiplyBlending, premultipliedAlpha: true }); const tint = new THREE.Mesh(new THREE.PlaneGeometry(10, 10), tintM); tint.position.z = -0.105; tint.renderOrder = 19; camera.add(tint);
// carbon monoxide in the air at the pipe (beat 1): shown, then it fades away to nothing (you can't see it)
const coAirC = new THREE.MeshStandardMaterial({ color: 0x1a1a1e, roughness: 0.4, transparent: true }), coAirO = new THREE.MeshStandardMaterial({ color: 0xff4a4a, emissive: 0xc01010, emissiveIntensity: 0.6, roughness: 0.3, transparent: true });
const COAIR = []; for (let i = 0; i < 16; i++) { const g = new THREE.Group(); for (const [m, x] of [[coAirC, -0.016], [coAirO, 0.016]]) { const s = new THREE.Mesh(new THREE.SphereGeometry(0.02, 14, 10), m); s.position.x = x; g.add(s); } g.renderOrder = 8; scene.add(g); COAIR.push(g); }
