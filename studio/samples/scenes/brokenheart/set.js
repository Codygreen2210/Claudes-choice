// ------------------------------------------------------------------ the living room (same home as always); his phone; the x-ray heart; a big heart up close (beats 3, 6)
const STANDP = V(0.2, 0, 0.4);                                     // where he stands, facing +z (the camera), the couch and window behind him
// his phone: a message on screen, then (beat 5) a 911 call
const phone = new THREE.Group(); scene.add(phone);
const phoneCanvas = document.createElement('canvas'); phoneCanvas.width = 480; phoneCanvas.height = 990;
const phoneTex = new THREE.CanvasTexture(phoneCanvas); phoneTex.colorSpace = THREE.SRGBColorSpace;
let phoneState = '';
function drawPhone(mode) { const g = phoneCanvas.getContext('2d'); g.setTransform(3, 0, 0, 3, 0, 0); g.fillStyle = mode === 'call' ? '#0c3a1c' : '#101418'; g.fillRect(0, 0, 160, 330); g.textAlign = 'center';
  if (mode === 'call') { g.fillStyle = '#fff'; g.font = 'bold 50px Arial'; g.fillText('911', 80, 110); g.font = 'bold 22px Arial'; g.fillText('CALLING', 80, 150); g.fillStyle = '#e8322a'; g.beginPath(); g.arc(80, 270, 26, 0, Math.PI * 2); g.fill(); }
  else { g.fillStyle = '#8a8f98'; g.font = '16px Arial'; g.fillText('Mom', 80, 40); g.fillStyle = '#2a2e36'; g.beginPath(); g.roundRect(10, 70, 140, 120, 16); g.fill();
    g.fillStyle = '#fff'; g.font = 'bold 19px Arial'; g.textAlign = 'left'; ['Call me now.', 'Something', 'terrible', 'happened.'].forEach((l, i) => g.fillText(l, 22, 102 + i * 24)); }
  phoneTex.needsUpdate = true; }
{ box(0.072, 0.152, 0.009, 0, 0, 0, mat(0x1c1d22, 0.3, 0.6), 0.004, phone); const s = new THREE.Mesh(new THREE.PlaneGeometry(0.064, 0.142), new THREE.MeshBasicMaterial({ map: phoneTex, toneMapped: false })); s.position.z = 0.0048; phone.add(s); }
drawPhone('msg');

// ------------------------------------------------------------------ x-ray: the glow body (same skeleton) with the heart and the adrenal glands
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
// the heart (to his left of centre) and the adrenal glands on top of the kidneys (they squirt the stress hormones)
const heartM = new THREE.MeshStandardMaterial({ color: 0x8a1a2a, emissive: 0xff2a3a, emissiveIntensity: 0.9, roughness: 0.4 });
const heart = new THREE.Group(); G.bones.chest.add(heart); heart.position.copy(toLocal(G.bones.chest, V(-0.025, 1.31, -0.04)));
const xLV = new THREE.Group();                                     // its bottom (the left ventricle's tip): balloons in beats 1-5
{ const hg = new THREE.Group(); heart.add(hg); hg.rotation.z = -0.45; hg.rotation.x = 0.2;
  for (const s of [-1, 1]) { const l = new THREE.Mesh(new THREE.SphereGeometry(0.03, 24, 16), heartM); l.position.set(s * 0.02, 0.012, 0); hg.add(l); }
  const pt = new THREE.Mesh(new THREE.ConeGeometry(0.043, 0.07, 24).rotateX(Math.PI), heartM); pt.position.y = -0.03; pt.scale.z = 0.75; hg.add(pt);
  hg.add(xLV); xLV.position.y = -0.045; const bl = new THREE.Mesh(new THREE.SphereGeometry(0.03, 24, 16), heartM); xLV.add(bl); xLV.scale.setScalar(0.01); }
const adrM = new THREE.MeshStandardMaterial({ color: 0xc89a2a, emissive: 0xffb020, emissiveIntensity: 0.6, roughness: 0.4 });
const ADR = []; for (const s of [-1, 1]) { const a = new THREE.Mesh(new THREE.ConeGeometry(0.025, 0.03, 12), adrM); G.bones.spine1.add(a); a.position.copy(toLocal(G.bones.spine1, V(s * 0.06, 1.12, 0.05))); ADR.push(a); }
const dotTex = canvasTex(64, 64, g => { const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.4, 'rgba(255,255,255,0.6)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); });
function dots(n, color, size) { const g = new THREE.BufferGeometry(); const p = new Float32Array(n * 3); g.setAttribute('position', new THREE.BufferAttribute(p, 3)); g.setDrawRange(0, 0);
  const m = new THREE.Points(g, new THREE.PointsMaterial({ color, size, map: dotTex, transparent: true, depthWrite: false, depthTest: false, blending: THREE.AdditiveBlending, toneMapped: false })); m.frustumCulled = false; m.renderOrder = 9; scene.add(m); return { m, p, n }; }
const ADRN = dots(260, 0xffc030, 0.024);
const ORGANS = [heart, ...ADR];
let XRON = false, XRNEW = false;
function setXray(k) { if ((k > 0.01) !== XRON) { XRON = k > 0.01; XRNEW = XRON; }   // the first draw after the ghost comes on comes out blank: draw() renders that frame twice
  for (const x of XRAY) x.visible = k > 0.01; xrayMat.emissiveIntensity = 0.45 * k;
  for (const o of NORMAL) o.visible = k < 0.6; for (const o of ORGANS) o.visible = k > 0.5; }

// ------------------------------------------------------------------ the big heart (a dark stage): its bottom balloons out; a clay octopus pot beside it for the shape
const HS = V(40, 0, 0);
const heartSet = new THREE.Group(); heartSet.position.copy(HS); scene.add(heartSet);
const hsLight = new THREE.PointLight(0xffe8e0, 0, 6, 1.2); hsLight.position.set(0.6, 1.0, 1.4); heartSet.add(hsLight);
heartSet.add(new THREE.Mesh(new THREE.SphereGeometry(5, 24, 12), new THREE.MeshBasicMaterial({ color: 0x14060a, side: THREE.BackSide })));
const bigM = new THREE.MeshStandardMaterial({ color: 0xa82030, emissive: 0x3a0610, emissiveIntensity: 0.4, roughness: 0.45 });
const vesM = new THREE.MeshStandardMaterial({ color: 0xc84a4a, roughness: 0.5 }), veinM = new THREE.MeshStandardMaterial({ color: 0x4a5ab0, roughness: 0.5 });
const BIG = new THREE.Group(); BIG.position.y = 1.0; heartSet.add(BIG);
// the left ventricle (main pumping chamber) is one soft mesh we reshape every frame: normal = a cone with a rounded point;
// ballooned = round wide bottom, tight narrow neck (the octopus pot). The bottom stops moving; only the neck still squeezes.
const LVG = new THREE.SphereGeometry(1, 72, 54), LV0 = LVG.attributes.position.array.slice();
const LVC = new Float32Array(LV0.length); LVG.setAttribute('color', new THREE.BufferAttribute(LVC, 3));
const bigLVM = bigM.clone(); bigLVM.color.set(0xffffff); bigLVM.vertexColors = true;
const bigLV = new THREE.Mesh(LVG, bigLVM);
const LVRED = new THREE.Color(0xa82030), LVSTUN = new THREE.Color(0xc87a86);
function shapeLV(bal, sq) { const P = LVG.attributes.position.array;
  for (let i = 0; i < P.length; i += 3) { const x = LV0[i], y = LV0[i + 1], z = LV0[i + 2], s = (y + 1) / 2;
    const kN = 0.5 + 0.5 * Math.pow(s, 0.55), kB = 1.3 - 0.72 * Math.pow(s, 1.4);
    const st = bal * (1 - Math.min(1, Math.max(0, (s - 0.2) / 0.45))); LVC[i] = LVRED.r + (LVSTUN.r - LVRED.r) * st; LVC[i + 1] = LVRED.g + (LVSTUN.g - LVRED.g) * st; LVC[i + 2] = LVRED.b + (LVSTUN.b - LVRED.b) * st;
    const k = (kN + (kB - kN) * bal) * (1 - 0.1 * sq * (s + (1 - s) * (1 - bal)));
    const yy = y < 0 ? y * (1.0 + 0.12 * (1 - bal) - 0.1 * bal) : y;      // the point pulls in as it rounds out
    P[i] = x * 0.2 * k; P[i + 1] = yy * 0.3; P[i + 2] = z * 0.18 * k; }
  LVG.attributes.position.needsUpdate = true; LVG.attributes.color.needsUpdate = true; LVG.computeVertexNormals(); }
shapeLV(0, 0);
{ const body = new THREE.Group(); BIG.add(body); body.rotation.z = 0.25; body.rotation.y = -0.25;
  body.add(bigLV); bigLV.position.set(0.05, -0.1, 0.0);
  const rv = new THREE.Mesh(new THREE.SphereGeometry(1, 40, 30), bigM); rv.scale.set(0.15, 0.24, 0.13); rv.position.set(-0.13, -0.02, 0.07); rv.rotation.z = -0.25; body.add(rv);   // right ventricle (stays normal)
  for (const [x, y, z, r] of [[-0.12, 0.2, -0.03, 0.12], [0.13, 0.22, -0.06, 0.11]]) { const s = new THREE.Mesh(new THREE.SphereGeometry(r, 32, 24), bigM); s.position.set(x, y, z); body.add(s); }   // the two upper chambers
  const ao = new THREE.Mesh(new THREE.TorusGeometry(0.085, 0.042, 14, 28, Math.PI * 1.15), vesM); ao.position.set(0.02, 0.33, -0.02); ao.rotation.z = 0.15; body.add(ao);
  const aoS = new THREE.Mesh(new THREE.CylinderGeometry(0.042, 0.045, 0.14, 16), vesM); aoS.position.set(0.1, 0.27, -0.02); body.add(aoS);
  const pa = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.045, 0.22, 16), veinM); pa.position.set(-0.14, 0.34, 0.03); pa.rotation.z = 0.25; body.add(pa); }
const potM = new THREE.MeshStandardMaterial({ color: 0x9a5a34, roughness: 0.85, side: THREE.DoubleSide });
const pot = new THREE.Group(); pot.position.set(0.42, 0.42, 0.05); heartSet.add(pot);
{ const prof = [[0, 0], [0.16, 0.01], [0.21, 0.12], [0.2, 0.26], [0.12, 0.36], [0.06, 0.42], [0.065, 0.48], [0.075, 0.5]].map(([x, y]) => new THREE.Vector2(x * 0.8, y * 0.8));
  const m = new THREE.Mesh(new THREE.LatheGeometry(prof, 40), potM); pot.add(m);
  const rope = new THREE.Mesh(new THREE.TorusGeometry(0.052, 0.008, 8, 24).rotateX(Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0xc8b088, roughness: 0.9 })); rope.position.y = 0.33; pot.add(rope); }   // wide round bottom, narrow neck: the shape the ballooned heart takes
const potTag = new THREE.Sprite(new THREE.SpriteMaterial({ map: canvasTex(512, 128, g => { g.fillStyle = 'rgba(10,10,14,0.75)'; g.beginPath(); g.roundRect(4, 4, 504, 120, 30); g.fill(); g.fillStyle = '#e8c8a0'; g.font = 'bold 52px sans-serif'; g.textAlign = 'center'; g.fillText('OCTOPUS POT', 256, 82); }), depthTest: false, toneMapped: false, transparent: true }));
potTag.scale.set(0.34, 0.085, 1); potTag.position.set(0.42, 0.34, 0.25); potTag.renderOrder = 10; heartSet.add(potTag);
const FLOW = dots(220, 0xff4a4a, 0.03);

// the phone up close (an insert in the corner of the frame): the message (beats 7, 0) and the 911 call (beat 5)
scene.add(camera);
const phone2 = new THREE.Group(); camera.add(phone2); phone2.visible = false;
{ box(0.072, 0.152, 0.009, 0, 0, 0, mat(0x1c1d22, 0.3, 0.6), 0.004, phone2); const s = new THREE.Mesh(new THREE.PlaneGeometry(0.064, 0.142), new THREE.MeshBasicMaterial({ map: phoneTex, toneMapped: false })); s.position.z = 0.0048; phone2.add(s);
  phone2.traverse(o => { if (o.isMesh) { o.renderOrder = 20; o.material = o.material.clone(); o.material.depthTest = false; } }); }
