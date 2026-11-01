// ------------------------------------------------------------------ the counter: four cans (three empty), a measuring tube for the caffeine; the clock moves near the counter
const TOPC = 0.945;                                                // counter top height
const STANDP = V(-2.03, 0, -0.62);                                 // where he stands (facing -x)
clock.position.set(-2.63, TOPC + 0.095, 0.03); clock.scale.setScalar(0.3); clock.rotation.y = 0.45;   // a kitchen clock standing on the counter
const CANR = 0.033, CANH = 0.157;
const canTex = canvasTex(256, 160, g => { const gr = g.createLinearGradient(0, 0, 0, 160); gr.addColorStop(0, '#16224a'); gr.addColorStop(1, '#0a1230'); g.fillStyle = gr; g.fillRect(0, 0, 256, 160);
  g.fillStyle = '#7dff3a'; g.beginPath(); g.moveTo(150, 10); g.lineTo(108, 84); g.lineTo(134, 84); g.lineTo(104, 152); g.lineTo(170, 66); g.lineTo(142, 66); g.lineTo(172, 10); g.closePath(); g.fill();
  g.font = 'bold 40px sans-serif'; g.fillStyle = '#ffffff'; g.textAlign = 'center'; g.save(); g.translate(64, 80); g.rotate(-Math.PI / 2); g.fillText('ZAPP', 0, 14); g.restore();
  g.font = 'bold 15px sans-serif'; g.fillStyle = '#7dff3a'; g.save(); g.translate(222, 80); g.rotate(-Math.PI / 2); g.fillText('300MG CAFFEINE', 0, 6); g.restore(); });
const alu = mat(0xc8ccd2, 0.25, 0.9);
function makeCan(crushed = 0) { const g = new THREE.Group();
  const body = new THREE.Mesh(new THREE.CylinderGeometry(CANR, CANR, CANH - 0.016, 36, 1, true), new THREE.MeshStandardMaterial({ map: canTex, roughness: 0.3, metalness: 0.5 })); body.position.y = CANH / 2; g.add(body);
  for (const [y, r0, r1] of [[0.004, CANR * 0.82, CANR], [CANH - 0.004, CANR, CANR * 0.82]]) { const n = new THREE.Mesh(new THREE.CylinderGeometry(y > 0.1 ? r1 : r1, y > 0.1 ? r0 : r0, 0.008, 36), alu); n.position.y = y; g.add(n); }
  const lid = new THREE.Mesh(new THREE.CylinderGeometry(CANR * 0.8, CANR * 0.8, 0.003, 30), alu); lid.position.y = CANH; g.add(lid);
  const tab = new THREE.Mesh(new RoundedBoxGeometry(0.014, 0.002, 0.024, 1, 0.001), alu); tab.position.set(0, CANH + 0.003, 0.006); g.add(tab);
  const hole = new THREE.Mesh(new THREE.CircleGeometry(0.007, 16).rotateX(-Math.PI / 2), mat(0x111111, 0.6)); hole.position.set(0, CANH + 0.0018, -0.012); hole.scale.x = 1.3; g.add(hole);
  g.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  if (crushed) g.scale.set(1 + 0.15 * crushed, 1 - 0.3 * crushed, 1 - 0.1 * crushed);
  return g; }
const CAN0 = V(-2.43, TOPC, -0.38);                               // the 4th can (to his left)
let CANYAW = 70, CANSPIN = 0;                                       // which way its label faces: on the counter (deg) / in his hand (rad)
const can = makeCan(); can.position.copy(CAN0); scene.add(can);
for (const [x, z, ry, side, cr] of [[-2.52, -0.95, 0.4, 0, 0.6], [-2.46, -1.05, 2.1, 0, 0], [-2.58, -0.82, 0, 1, 0.3]]) {
  const e = makeCan(cr); e.rotation.y = ry; if (side) { e.rotation.set(0, 0.3, Math.PI / 2); e.position.set(x + 0.02, TOPC + CANR * 1.1, z); } else e.position.set(x, TOPC, z); scene.add(e); }
// the measuring tube: a clear cylinder with ticks every 300 mg, a red LIMIT line at 400; green caffeine fills it
const TUBE = V(-2.56, TOPC, -0.2), TUBER = 0.055, TUBEH = 0.46, MG2H = 0.36 / 1200;
const tube = new THREE.Group(); tube.position.copy(TUBE); scene.add(tube);
const tubeTex = canvasTex(200, 1000, g => { g.clearRect(0, 0, 200, 1000);           // the arc it wraps is about 1:5 (wide:tall)
  const yOf = mg => 1000 - (0.012 + mg * MG2H) / TUBEH * 1000;
  g.textAlign = 'left'; for (const mg of [300, 600, 900, 1200]) { const y = yOf(mg); g.fillStyle = '#ffffff'; g.fillRect(8, y - 3, 34, 6); g.font = 'bold 30px sans-serif'; g.fillText(mg + ' MG', 50, y + 11); }
  const y4 = yOf(400); g.fillStyle = '#ff2a20'; g.fillRect(0, y4 - 5, 200, 10); g.font = 'bold 30px sans-serif'; g.fillText('LIMIT 400', 40, y4 - 14); });
{ const glassT = new THREE.Mesh(new THREE.CylinderGeometry(TUBER, TUBER, TUBEH, 40, 1, true), new THREE.MeshPhysicalMaterial({ color: 0xe8f4ff, roughness: 0.05, transparent: true, opacity: 0.22, side: THREE.DoubleSide, depthWrite: false }));
  glassT.position.y = TUBEH / 2; tube.add(glassT);
  const marks = new THREE.Mesh(new THREE.CylinderGeometry(TUBER + 0.001, TUBER + 0.001, TUBEH, 40, 1, true, -Math.PI / 2 - 0.8, 1.6), new THREE.MeshBasicMaterial({ map: tubeTex, transparent: true, depthWrite: false, toneMapped: false }));
  marks.position.y = TUBEH / 2; marks.renderOrder = 4; tube.add(marks);
  const base = new THREE.Mesh(new THREE.CylinderGeometry(TUBER + 0.02, TUBER + 0.025, 0.012, 40), mat(0x2a2a30, 0.4)); base.position.y = 0.006; tube.add(base); }
const fillM = new THREE.MeshStandardMaterial({ color: 0x7dff3a, emissive: 0x3aa010, emissiveIntensity: 0.6, roughness: 0.15, transparent: true, opacity: 0.85 });
const fill = new THREE.Mesh(new THREE.CylinderGeometry(TUBER - 0.004, TUBER - 0.004, 1, 36).translate(0, 0.5, 0), fillM); fill.position.y = 0.012; tube.add(fill);
tube.rotation.y = Math.PI / 2 + 0.35;                              // the ticks face the camera (front-left of him)
// the evening light through the window (beat 6: five hours go by)
const dusk = new THREE.Color(0xff9a50);

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
const boltM = new THREE.MeshBasicMaterial({ color: 0xfff6b0, toneMapped: false, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, depthTest: false });
const bolts = []; for (let i = 0; i < 7; i++) { const m = new THREE.Mesh(new THREE.BufferGeometry(), boltM); m.renderOrder = 9; m.frustumCulled = false; brain.add(m); bolts.push(m); }
function setBolts(t, k) { bolts.forEach((m, i) => { const on = k > 0.01 && hash1(Math.floor(t * 12) * 7.1 + i * 3.3) < 0.85 * k; m.visible = on; if (!on) return;
    const sd = Math.floor(t * 12) * 13.7 + i * 5.1, a = V(hash1(sd) - 0.5, hash1(sd + 1) - 0.5, hash1(sd + 2) - 0.5).normalize().multiplyScalar(0.06), b = V(hash1(sd + 3) - 0.5, hash1(sd + 4) - 0.5, hash1(sd + 5) - 0.5).normalize().multiplyScalar(0.06);
    const pts = []; for (let j = 0; j <= 8; j++) { const u = j / 8, p = a.clone().lerp(b, u); if (j > 0 && j < 8) p.add(V(hash1(sd + j * 1.7) - 0.5, hash1(sd + j * 2.3) - 0.5, hash1(sd + j * 3.1) - 0.5).multiplyScalar(0.03)); p.multiplyScalar(1.1); pts.push(p); }
    m.geometry.dispose(); m.geometry = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 24, 0.0028, 5, false); }); }
const ORGANS = [heart, brain];
let XRON = false, XRNEW = false;
function setXray(k) { if ((k > 0.01) !== XRON) { XRON = k > 0.01; XRNEW = XRON; }   // the first draw after the ghost comes on comes out blank: draw() renders that frame twice
  for (const x of XRAY) x.visible = k > 0.01; xrayMat.emissiveIntensity = 0.75 * k;
  for (const o of NORMAL) o.visible = k < 0.6; for (const o of ORGANS) o.visible = k > 0.5; }

// ------------------------------------------------------------------ inside the brain (beat 3): a nerve cell's surface with receptors; caffeine sits in them, the "tired" signal bounces off
const CELL = V(40, 0, 0);
const cellSet = new THREE.Group(); cellSet.position.copy(CELL); scene.add(cellSet);
const cellLight = new THREE.PointLight(0xffd8e8, 0, 6, 1.2); cellLight.position.set(0.3, 1.2, 0.8); cellSet.add(cellLight);
{ const bg = new THREE.Mesh(new THREE.SphereGeometry(4, 32, 16), new THREE.MeshBasicMaterial({ color: 0x2a0a22, side: THREE.BackSide })); cellSet.add(bg);
  const memTex = canvasTex(512, 512, g => { g.fillStyle = '#d87aa0'; g.fillRect(0, 0, 512, 512); for (let i = 0; i < 260; i++) { g.fillStyle = `rgba(${150 + Math.random() * 60 | 0},60,110,0.35)`; g.beginPath(); g.arc(Math.random() * 512, Math.random() * 512, 6 + Math.random() * 14, 0, 6.28); g.fill(); } });
  const memG = new THREE.PlaneGeometry(3, 3, 60, 60).rotateX(-Math.PI / 2); const p = memG.attributes.position; for (let i = 0; i < p.count; i++) { const x = p.getX(i), z = p.getZ(i); p.setY(i, -0.12 * (x * x + z * z) + 0.02 * Math.sin(x * 9) * Math.sin(z * 7)); } memG.computeVertexNormals();
  const mem = new THREE.Mesh(memG, new THREE.MeshStandardMaterial({ map: memTex, roughness: 0.6, emissive: 0x401028, emissiveIntensity: 0.4 })); cellSet.add(mem); }
const RECS = [V(-0.16, 0, 0.07), V(0, 0, -0.08), V(0.16, 0, 0.07)];
const recM = new THREE.MeshStandardMaterial({ color: 0x8a4ad0, emissive: 0x4a1a90, emissiveIntensity: 0.5, roughness: 0.4 });
for (const r of RECS) { r.y = -0.12 * (r.x * r.x + r.z * r.z); const g = new THREE.Group(); g.position.copy(r); cellSet.add(g);
  for (let k = 0; k < 4; k++) { const a = k / 4 * Math.PI * 2 + 0.4, arm = new THREE.Mesh(new THREE.CapsuleGeometry(0.018, 0.07, 6, 12), recM); arm.position.set(Math.cos(a) * 0.05, 0.045, Math.sin(a) * 0.05); arm.rotation.set(Math.sin(a) * 0.35, 0, -Math.cos(a) * 0.35); g.add(arm); } }
const cafM = new THREE.MeshStandardMaterial({ color: 0xff8a20, emissive: 0xc04a00, emissiveIntensity: 0.6, roughness: 0.35, flatShading: true });
const adeM = new THREE.MeshStandardMaterial({ color: 0x4aa8ff, emissive: 0x1a5ac0, emissiveIntensity: 0.6, roughness: 0.3 });
const cafs = RECS.map(() => { const m = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, 0.03, 6), cafM); cellSet.add(m); return m; });
const ades = RECS.map(() => { const m = new THREE.Mesh(new THREE.IcosahedronGeometry(0.04, 2), adeM); cellSet.add(m); return m; });
function tag(text, color, w = 0.34) { const c = canvasTex(512, 128, g => { g.fillStyle = 'rgba(10,10,14,0.75)'; g.beginPath(); g.roundRect(4, 4, 504, 120, 30); g.fill(); g.fillStyle = color; g.font = 'bold 64px sans-serif'; g.textAlign = 'center'; g.fillText(text, 256, 86); });
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: c, depthTest: false, toneMapped: false })); s.scale.set(w, w / 4, 1); s.renderOrder = 10; cellSet.add(s); return s; }
const tagCaf = tag('CAFFEINE', '#ffb060', 0.26), tagAde = tag('"TIRED" SIGNAL', '#8ac8ff', 0.32);
