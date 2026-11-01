// ------------------------------------------------------------------ the woods: leaf litter, trees all around, a stream, a few rocks; the sky goes day -> night (beat 1)
scene.remove(lamp);
const DAY = new THREE.Color(0x9cc6e6), NIGHT = new THREE.Color(0x0b1226);
const STREAMZ = -2.3;
const woods = new THREE.Group(); scene.add(woods);
const leafTex = canvasTex(512, 512, g => { g.fillStyle = '#5a4a2e'; g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 2600; i++) { const c = ['#7a5a2a', '#9a6a2a', '#5a3a1a', '#6a7a3a', '#8a4a1a', '#4a3a22'][i % 6]; g.fillStyle = c; g.save(); g.translate(Math.random() * 512, Math.random() * 512); g.rotate(Math.random() * 6.28); g.beginPath(); g.ellipse(0, 0, 4 + Math.random() * 6, 2 + Math.random() * 3, 0, 0, 6.28); g.fill(); g.restore(); } });
leafTex.wrapS = leafTex.wrapT = THREE.RepeatWrapping; leafTex.repeat.set(10, 10);
const ground = new THREE.Mesh(new THREE.PlaneGeometry(40, 40).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ map: leafTex, roughness: 0.95 })); ground.receiveShadow = true; woods.add(ground);
const barkTex = canvasTex(128, 512, g => { g.fillStyle = '#4a3a2c'; g.fillRect(0, 0, 128, 512); for (let i = 0; i < 70; i++) { g.strokeStyle = `rgba(${20 + Math.random() * 30 | 0},${15 + Math.random() * 20 | 0},10,0.7)`; g.lineWidth = 2 + Math.random() * 4; g.beginPath(); const x = Math.random() * 128; g.moveTo(x, 0); g.bezierCurveTo(x + 10, 170, x - 10, 340, x + 4, 512); g.stroke(); } });
barkTex.wrapS = barkTex.wrapT = THREE.RepeatWrapping;
const barkM = new THREE.MeshStandardMaterial({ map: barkTex, roughness: 0.95 }), leavesM = [0x2f5a2a, 0x3a6a30, 0x274a24].map(c => mat(c, 0.9));
function tree(x, z, h, r, low = 1.4) { const t = new THREE.Mesh(new THREE.CylinderGeometry(r * 0.6, r, h, 12), barkM); t.position.set(x, h / 2, z); t.castShadow = true; t.receiveShadow = true; woods.add(t);
  const n = 4; for (let k = 0; k < n; k++) { const y = low + (h - low) * k / (n - 1), w = (1.5 - 1.1 * k / (n - 1)) * (0.8 + 0.4 * hash1(x * 3 + k)); const c = new THREE.Mesh(new THREE.ConeGeometry(w, 1.7, 10), leavesM[(k + Math.round(x * 3)) % 3]); c.position.set(x, y + 0.6, z); c.castShadow = true; woods.add(c); } return t; }   // a pine: skirts of needles from low down
for (let i = 0; i < 70; i++) { const a = hash1(i * 3.1) * 6.283, d = 3.4 + 10 * hash1(i * 7.3); const x = Math.cos(a) * d, z = Math.sin(a) * d - 0.8;   // a clearing around him and the stream bank
  if (Math.abs(z - STREAMZ) < 1.0 && Math.abs(x) < 7) continue; tree(x, z, 5 + 3 * hash1(i * 5.5), 0.14 + 0.1 * hash1(i * 2.9)); }
for (let i = 0; i < 40; i++) { const a = hash1(i * 9.7) * 6.283, d = 2.6 + 8 * hash1(i * 1.9); const b = new THREE.Mesh(new THREE.IcosahedronGeometry(0.35 + 0.35 * hash1(i * 4.1), 1), leavesM[i % 3]);   // undergrowth
  b.position.set(Math.cos(a) * d, 0.2, Math.sin(a) * d - 0.8); if (Math.abs(b.position.z - STREAMZ) < 0.7) continue; b.scale.y = 0.6; b.castShadow = true; woods.add(b); }
for (let i = 0; i < 14; i++) { const r = new THREE.Mesh(new THREE.IcosahedronGeometry(0.15 + 0.2 * hash1(i * 4.4), 1), mat(0x7a7a72, 0.9)); r.position.set((hash1(i * 6.1) - 0.5) * 9, 0.05, -1.6 - hash1(i * 2.3) * 1.6); r.scale.y = 0.6; r.castShadow = true; woods.add(r); }
// the stream (z about -2.3): flowing water across the clearing
const waterTex = canvasTex(256, 256, g => { g.fillStyle = '#2a5a7a'; g.fillRect(0, 0, 256, 256); for (let i = 0; i < 160; i++) { g.strokeStyle = `rgba(200,230,255,${0.15 + Math.random() * 0.3})`; g.lineWidth = 1 + Math.random() * 2; g.beginPath(); const y = Math.random() * 256, x = Math.random() * 256; g.moveTo(x, y); g.lineTo(x + 20 + Math.random() * 40, y + (Math.random() - 0.5) * 4); g.stroke(); } });
waterTex.wrapS = waterTex.wrapT = THREE.RepeatWrapping; waterTex.repeat.set(6, 1);
const stream = new THREE.Mesh(new THREE.PlaneGeometry(14, 0.9).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ map: waterTex, roughness: 0.08, metalness: 0.2, color: 0xb0d8f0, emissive: 0x0a2030, emissiveIntensity: 0.4 })); stream.position.set(0, 0.012, STREAMZ); woods.add(stream);
// the tally tree (beat 6): one mark a day, carved in groups of five
const TALLY = V(1.7, 0, -1.4);
const tallyTree = tree(TALLY.x, TALLY.z, 6.0, 0.32, 2.6);
const tallyCanvas = document.createElement('canvas'); tallyCanvas.width = 512; tallyCanvas.height = 768; const tallyTex = new THREE.CanvasTexture(tallyCanvas); tallyTex.colorSpace = THREE.SRGBColorSpace;
let tallyState = -1;
function drawTally(n) { const g = tallyCanvas.getContext('2d'); g.clearRect(0, 0, 512, 768); g.strokeStyle = '#e8d6b0'; g.lineCap = 'round'; g.lineWidth = 9;
  for (let i = 0; i < n; i++) { const grp = Math.floor(i / 5), k = i % 5, gx = 40 + (grp % 4) * 115, gy = 190 + Math.floor(grp / 4) * 130;
    g.beginPath(); if (k < 4) { g.moveTo(gx + k * 20, gy); g.lineTo(gx + k * 20 + 3, gy + 85); } else { g.moveTo(gx - 10, gy + 70); g.lineTo(gx + 85, gy + 12); } g.stroke(); }
  tallyTex.needsUpdate = true; }
drawTally(0);
{ const pl = new THREE.Mesh(new THREE.CylinderGeometry(0.288, 0.3, 0.9, 24, 1, true, -0.95, 1.9), new THREE.MeshStandardMaterial({ map: tallyTex, transparent: true, roughness: 0.9, depthWrite: false })); pl.position.set(TALLY.x, 1.1, TALLY.z); pl.rotation.y = 0; woods.add(pl); }
const tallyLight = new THREE.PointLight(0xffe8c8, 0, 3, 1.5); tallyLight.position.copy(TALLY).add(V(0.3, 1.4, 0.9)); scene.add(tallyLight);
const moon = new THREE.Mesh(new THREE.SphereGeometry(0.6, 20, 12), new THREE.MeshBasicMaterial({ color: 0xf0f0e0 })); moon.position.set(-4, 9, -14); scene.add(moon);

// ------------------------------------------------------------------ his water bottle (empty, then filled at the stream)
const BTR = 0.034, BTH = 0.2;
const bottle = new THREE.Group(); scene.add(bottle);
{ const plastic = new THREE.MeshPhysicalMaterial({ color: 0xdff0ff, roughness: 0.08, transparent: true, opacity: 0.35, side: THREE.DoubleSide, depthWrite: false });
  const prof = [[0, 0], [BTR, 0.004], [BTR, 0.15], [0.016, 0.185], [0.014, 0.2]].map(([x, y]) => new THREE.Vector2(x, y));
  const shell = new THREE.Mesh(new THREE.LatheGeometry(prof, 28), plastic); bottle.add(shell);
  const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.016, 0.016, 0.018, 16), mat(0x2a6ad0, 0.4)); cap.position.y = 0.208; bottle.add(cap);
  const label = new THREE.Mesh(new THREE.CylinderGeometry(BTR + 0.001, BTR + 0.001, 0.05, 28, 1, true), mat(0x3a9ad8, 0.5)); label.position.y = 0.08; bottle.add(label); }
const bwM = new THREE.MeshStandardMaterial({ color: 0x7ac0ff, emissive: 0x1a4a7a, emissiveIntensity: 0.4, roughness: 0.05, transparent: true, opacity: 0.6 });
const bwater = new THREE.Mesh(new THREE.CylinderGeometry(BTR - 0.003, BTR - 0.003, 1, 24).translate(0, 0.5, 0), bwM); bwater.position.y = 0.005; bottle.add(bwater);
const drop = new THREE.Mesh(new THREE.SphereGeometry(0.008, 12, 8), bwM); drop.scale.y = 1.4; scene.add(drop);

// ------------------------------------------------------------------ x-ray: the glow body (same skeleton) with the kidneys, liver, heart, fat and muscle
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
// the organs (in his rest pose: he faces -z, his left is -x)
const organ = (c, e, k = 0.8, op = 0.85) => new THREE.MeshStandardMaterial({ color: c, emissive: e, emissiveIntensity: k, roughness: 0.45, transparent: true, opacity: op });
// (rest pose: he faces -z, his left is -x)
const kidM = organ(0x7a2a2a, 0xff5a4a, 0.7), liverM = organ(0x6a1a1a, 0xc03a2a, 0.6), heartM = organ(0x8a1a2a, 0xff2a3a, 0.9, 1);
const KID = []; for (const s of [-1, 1]) { const k = new THREE.Mesh(new THREE.SphereGeometry(0.045, 20, 14), kidM); k.scale.set(0.6, 1.0, 0.5); G.bones.spine1.add(k); k.position.copy(toLocal(G.bones.spine1, V(s * 0.06, 1.06, 0.05))); KID.push(k); }
const liver = new THREE.Mesh(new THREE.SphereGeometry(0.07, 28, 18), liverM); G.bones.spine2.add(liver); liver.scale.set(1.35, 0.7, 0.9); liver.position.copy(toLocal(G.bones.spine2, V(0.06, 1.14, -0.03)));
const heart = new THREE.Group(); G.bones.chest.add(heart); heart.position.copy(toLocal(G.bones.chest, V(-0.025, 1.31, -0.04)));
{ const hg = new THREE.Group(); heart.add(hg); hg.rotation.z = -0.45; hg.rotation.x = 0.2;
  for (const s of [-1, 1]) { const l = new THREE.Mesh(new THREE.SphereGeometry(0.03, 24, 16), heartM); l.position.set(s * 0.02, 0.012, 0); hg.add(l); }
  const pt = new THREE.Mesh(new THREE.ConeGeometry(0.043, 0.07, 24).rotateX(Math.PI), heartM); pt.position.y = -0.03; pt.scale.z = 0.75; hg.add(pt); }
// fat: a soft yellow layer around his belly (beat 4 burns it down); muscle: red bands on his upper arms and thighs (beat 5 wastes them)
const fatM = organ(0xffd84a, 0xc09a10, 0.5, 0.5); fatM.depthWrite = false;
const fat = new THREE.Mesh(new THREE.SphereGeometry(0.16, 32, 20), fatM); G.bones.spine1.add(fat); fat.scale.set(1.0, 0.75, 0.85); fat.position.copy(toLocal(G.bones.spine1, V(0, 1.02, -0.01)));
const FAT0 = fat.scale.clone();
const muscM = organ(0xb02a2a, 0xff4a3a, 0.7, 0.8);
const MUSC = []; for (const [bn, len, r] of [['uarmR', 0.2, 0.034], ['uarmL', 0.2, 0.034], ['thighR', 0.3, 0.05], ['thighL', 0.3, 0.05]]) {
  const b = G.bones[bn], c = bn.startsWith('thigh') ? 'shin' + bn.slice(-1) : 'farm' + bn.slice(-1), a = wp(b), e = wp(G.bones[c]);
  const m = new THREE.Mesh(new THREE.CapsuleGeometry(r, len, 6, 14), muscM); const mid = a.clone().lerp(e, 0.5); b.add(m); m.position.copy(toLocal(b, mid));
  const dirL = e.clone().sub(a).normalize().applyQuaternion(wq(b).invert()); m.quaternion.setFromUnitVectors(V(0, 1, 0), dirL); MUSC.push(m); }
const dotTex = canvasTex(64, 64, g => { const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.4, 'rgba(255,255,255,0.6)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); });
function dots(n, color, size) { const g = new THREE.BufferGeometry(); const p = new Float32Array(n * 3); g.setAttribute('position', new THREE.BufferAttribute(p, 3)); g.setDrawRange(0, 0);
  const m = new THREE.Points(g, new THREE.PointsMaterial({ color, size, map: dotTex, transparent: true, depthWrite: false, depthTest: false, blending: THREE.AdditiveBlending, toneMapped: false })); m.frustumCulled = false; m.renderOrder = 9; scene.add(m); return { m, p, n }; }
const SUG = dots(200, 0xffffff, 0.022), FUEL = dots(200, 0xffc040, 0.024), WASTE = dots(160, 0x9a7a3a, 0.02);
const ORGANS = [...KID, liver, heart, fat, ...MUSC];
let XRON = false, XRNEW = false;
function setXray(k) { if ((k > 0.01) !== XRON) { XRON = k > 0.01; XRNEW = XRON; }   // the first draw after the ghost comes on comes out blank: draw() renders that frame twice
  for (const x of XRAY) x.visible = k > 0.01; xrayMat.emissiveIntensity = 0.75 * k;
  for (const o of NORMAL) o.visible = k < 0.6; for (const o of ORGANS) o.visible = k > 0.5; }
