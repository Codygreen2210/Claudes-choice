// ------------------------------------------------------------------ the counter: the 6th can (to his left), five empties; ten spoons of sugar for beats 1-2
const TOPC = 0.945;                                                // counter top height
const STANDP = V(-2.03, 0, -0.62);                                 // where he stands (facing -x)
clock.visible = false;
const CANR = 0.033, CANH = 0.122;                                  // a 12 oz can
const canTex = canvasTex(256, 128, g => { const gr = g.createLinearGradient(0, 0, 0, 128); gr.addColorStop(0, '#e0141e'); gr.addColorStop(1, '#a00a12'); g.fillStyle = gr; g.fillRect(0, 0, 256, 128);
  g.fillStyle = 'rgba(255,255,255,0.85)'; for (let i = 0; i < 26; i++) { g.beginPath(); g.arc(150 + Math.random() * 100, 10 + Math.random() * 108, 2 + Math.random() * 5, 0, 6.28); g.fill(); }   // bubbles (no real brand's marks)
  g.font = 'bold 44px sans-serif'; g.fillStyle = '#ffffff'; g.textAlign = 'center'; g.fillText('COLA', 80, 62); g.font = 'bold 16px sans-serif'; g.fillText('CLASSIC FIZZ', 80, 92); });
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
const CAN0 = V(-2.43, TOPC, -0.24);                                  // the 6th can (to his left)
let CANYAW = -88, CANSPIN = 0;                                     // which way its label faces: on the counter (deg) / in his hand (rad)
const can = makeCan(); can.position.copy(CAN0); scene.add(can);
for (const [x, z, ry, side, cr] of [[-2.55, -1.0, 0.4, 0, 0.6], [-2.47, -1.1, 2.1, 0, 0], [-2.6, -0.87, 0, 1, 0.3], [-2.62, -1.2, 1.0, 0, 0.4], [-2.52, -1.28, 2.6, 1, 0]]) {
  const e = makeCan(cr); e.rotation.y = ry; if (side) { e.rotation.set(0, ry, Math.PI / 2); e.position.set(x, TOPC + CANR * 1.05, z); } else e.position.set(x, TOPC, z); scene.add(e); }
// fizz: tiny foam beads shooting out of the opening (beat 0, the can was just cracked) and the puddle when it's dropped (beat 6)
const fizzM = new THREE.MeshStandardMaterial({ color: 0xd8b48a, emissive: 0x3a2010, emissiveIntensity: 0.3, roughness: 0.3, transparent: true, opacity: 0.9 });
const FIZZN = 160, fizz = new THREE.InstancedMesh(new THREE.SphereGeometry(1, 8, 6), fizzM, FIZZN); fizz.frustumCulled = false; scene.add(fizz);
const puddle = new THREE.Mesh(new THREE.CircleGeometry(1, 40).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0x3a1a08, roughness: 0.05, metalness: 0.2, transparent: true, opacity: 0.85 })); puddle.position.y = 0.003; scene.add(puddle);
// ten sugar cubes (a teaspoon each) stacked into a tower beside the can; a red DAILY MAX line above the 9th
const CUBE = 0.02, TOWER = V(-2.515, TOPC, -0.18);
const sugarM = new THREE.MeshStandardMaterial({ map: canvasTex(64, 64, g => { g.fillStyle = '#f6f4ee'; g.fillRect(0, 0, 64, 64); for (let i = 0; i < 400; i++) { g.fillStyle = Math.random() < 0.5 ? '#ffffff' : '#d6d2c8'; g.fillRect(Math.random() * 64, Math.random() * 64, 2, 2); } }), roughness: 0.75 });
const cube10M = sugarM.clone(); cube10M.emissive = new THREE.Color(0xff2a20); cube10M.emissiveIntensity = 0;
const CUBES = []; for (let i = 0; i < 10; i++) { const c = new THREE.Mesh(new RoundedBoxGeometry(CUBE, CUBE, CUBE, 2, 0.002), i === 9 ? cube10M : sugarM); c.castShadow = true; c.receiveShadow = true; scene.add(c); CUBES.push(c); }
const limitM = new THREE.MeshBasicMaterial({ color: 0xff2a20, toneMapped: false, transparent: true });
const limitBar = new THREE.Mesh(new THREE.BoxGeometry(0.036, 0.004, 0.036), limitM); limitBar.position.copy(TOWER).add(V(0, 9 * CUBE + 0.001, 0)); scene.add(limitBar);
const limitTag = new THREE.Sprite(new THREE.SpriteMaterial({ map: canvasTex(512, 128, g => { g.fillStyle = 'rgba(200,20,20,0.92)'; g.beginPath(); g.roundRect(4, 4, 504, 120, 28); g.fill(); g.fillStyle = '#fff'; g.font = 'bold 60px sans-serif'; g.textAlign = 'center'; g.fillText('DAILY MAX', 256, 84); }), depthTest: false, toneMapped: false, transparent: true }));
limitTag.scale.set(0.09, 0.0225, 1); limitTag.renderOrder = 10; scene.add(limitTag);

// ------------------------------------------------------------------ x-ray: the glow body (same skeleton) with the stomach, pancreas and liver
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
const stomachM = organ(0x9a4a5a, 0xff7a90, 0.6), pancM = organ(0xb89a40, 0xffd060, 0.5), liverM = organ(0x6a1a1a, 0xc03a2a, 0.6);
const stomach = new THREE.Mesh(new THREE.SphereGeometry(0.05, 24, 16), stomachM); G.bones.spine2.add(stomach); stomach.scale.set(1.3, 0.9, 0.8); stomach.rotation.z = -0.5; stomach.position.copy(toLocal(G.bones.spine2, V(-0.05, 1.12, -0.04)));
const panc = new THREE.Mesh(new THREE.CapsuleGeometry(0.014, 0.1, 6, 12), pancM); G.bones.spine1.add(panc); panc.rotation.z = Math.PI / 2 - 0.2; panc.position.copy(toLocal(G.bones.spine1, V(-0.01, 1.06, -0.01)));
const liver = new THREE.Mesh(new THREE.SphereGeometry(0.07, 28, 18), liverM); G.bones.spine2.add(liver); liver.scale.set(1.35, 0.7, 0.9); liver.position.copy(toLocal(G.bones.spine2, V(0.06, 1.14, -0.03)));
const LIVER0 = liver.scale.clone();
// sugar in his blood (white sparks) and insulin (blue) from the pancreas; fat drops in the liver (yellow)
const dotTex = canvasTex(64, 64, g => { const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.4, 'rgba(255,255,255,0.6)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); });
function dots(n, color, size) { const g = new THREE.BufferGeometry(); const p = new Float32Array(n * 3); g.setAttribute('position', new THREE.BufferAttribute(p, 3)); g.setDrawRange(0, 0);
  const m = new THREE.Points(g, new THREE.PointsMaterial({ color, size, map: dotTex, transparent: true, depthWrite: false, depthTest: false, blending: THREE.AdditiveBlending, toneMapped: false })); m.frustumCulled = false; m.renderOrder = 9; scene.add(m); return { m, p, n }; }
const SUG = dots(320, 0xffffff, 0.022), INS = dots(120, 0x4aa8ff, 0.026);
const fatM = new THREE.MeshStandardMaterial({ color: 0xffd84a, emissive: 0xc09a10, emissiveIntensity: 0.6, roughness: 0.4 });
const fatDrops = []; for (let i = 0; i < 14; i++) { const m = new THREE.Mesh(new THREE.SphereGeometry(0.012 + 0.008 * hash1(i * 3.1), 12, 8), fatM); liver.add(m); m.position.set((hash1(i * 5.3) - 0.5) * 0.11, (hash1(i * 7.7) - 0.5) * 0.06, (hash1(i * 2.9) - 0.5) * 0.08); fatDrops.push(m); }
const ORGANS = [stomach, panc, liver];
let XRON = false, XRNEW = false;
function setXray(k) { if ((k > 0.01) !== XRON) { XRON = k > 0.01; XRNEW = XRON; }   // the first draw after the ghost comes on comes out blank: draw() renders that frame twice
  for (const x of XRAY) x.visible = k > 0.01; xrayMat.emissiveIntensity = 0.75 * k;
  for (const o of NORMAL) o.visible = k < 0.6; for (const o of ORGANS) o.visible = k > 0.5; }


// ------------------------------------------------------------------ a tooth up close (beat 4): every sip washes cola over it; acid eats pits into the enamel
const TOOTH = V(40, 0, 0);
const toothSet = new THREE.Group(); toothSet.position.copy(TOOTH); scene.add(toothSet);
const toothLight = new THREE.PointLight(0xffffff, 0, 4, 1.2); toothLight.position.set(0.25, 0.55, 0.6); toothSet.add(toothLight);
{ toothSet.add(new THREE.Mesh(new THREE.SphereGeometry(3, 32, 16), new THREE.MeshBasicMaterial({ color: 0x3a0a10, side: THREE.BackSide })));
  const gum = new THREE.Mesh(new RoundedBoxGeometry(1.4, 0.16, 0.5, 4, 0.07), new THREE.MeshStandardMaterial({ color: 0xd8607a, roughness: 0.5, emissive: 0x4a1020, emissiveIntensity: 0.3 })); gum.position.y = -0.02; toothSet.add(gum); }
const enamelTex = document.createElement('canvas'); enamelTex.width = 512; enamelTex.height = 512; const enamelMap = new THREE.CanvasTexture(enamelTex); enamelMap.colorSpace = THREE.SRGBColorSpace;
let pitState = -1;
function drawPits(k) { const g = enamelTex.getContext('2d'); g.fillStyle = '#f8f4ea'; g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 46; i++) { const a = clamp(k * 1.25 - hash1(i * 3.3) * 0.25, 0, 1); if (a <= 0) continue; const x = hash1(i * 5.1) * 512, y = 120 + hash1(i * 7.9) * 300, r = (4 + 16 * hash1(i * 2.2)) * a;
    const gr = g.createRadialGradient(x, y, 0, x, y, r); gr.addColorStop(0, 'rgba(90,60,30,0.95)'); gr.addColorStop(0.7, 'rgba(150,110,60,0.7)'); gr.addColorStop(1, 'rgba(200,170,120,0)'); g.fillStyle = gr; g.beginPath(); g.arc(x, y, r, 0, 6.28); g.fill(); }
  enamelMap.needsUpdate = true; }
drawPits(0);
const toothM = new THREE.MeshStandardMaterial({ map: enamelMap, roughness: 0.22, metalness: 0.02, color: 0xffffff, emissive: 0x6a6a66, emissiveIntensity: 0.45 });
const tooth = new THREE.Group(); toothSet.add(tooth); tooth.position.y = 0.0;
{ const prof = [[0.0, -0.02], [0.13, -0.02], [0.155, 0.05], [0.2, 0.17], [0.215, 0.26], [0.2, 0.31], [0.0, 0.31]].map(([x, y]) => new THREE.Vector2(x, y));
  const crown = new THREE.Mesh(new THREE.LatheGeometry(prof, 48), toothM); crown.scale.z = 0.85; tooth.add(crown);
  for (const [x, z] of [[-0.085, -0.07], [0.085, -0.07], [-0.085, 0.07], [0.085, 0.07]]) { const c = new THREE.Mesh(new THREE.SphereGeometry(0.105, 28, 18), toothM); c.scale.set(1, 0.55, 0.9); c.position.set(x, 0.31, z); tooth.add(c); } }
for (const x of [-0.48, 0.48]) { const t2 = tooth.clone(); t2.position.x = x; t2.scale.setScalar(0.9); toothSet.add(t2); }
const colaM = new THREE.MeshStandardMaterial({ color: 0x5a2a0e, emissive: 0x2a1004, roughness: 0.05, metalness: 0.1, transparent: true, opacity: 0.55, depthWrite: false });
const wave = new THREE.Mesh(new THREE.BoxGeometry(1.8, 1, 0.8).translate(0, 0.5, 0), colaM); wave.renderOrder = 6; toothSet.add(wave);
const BUBN = 90, bubs = new THREE.InstancedMesh(new THREE.SphereGeometry(1, 10, 8), new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xffe8d0, emissiveIntensity: 0.4, transparent: true, opacity: 0.8 }), BUBN); bubs.frustumCulled = false; bubs.renderOrder = 7; toothSet.add(bubs);
const _M = new THREE.Matrix4(), _Q = new THREE.Quaternion(), _S = V(1, 1, 1);
