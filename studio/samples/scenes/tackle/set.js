// ------------------------------------------------------------------ set: a floodlit stadium at night, two stand-in players (no crests, no likenesses)
home.visible = false; lamp.visible = false;
scene.background = new THREE.Color(0x05080f); scene.environmentIntensity = 0.25; scene.fog = new THREE.Fog(0x0a0f1a, 120, 420);
hemi.color.set(0x8fa4c8); hemi.groundColor.set(0x1c2a14); hemi.intensity = 0.55;
sun.color.set(0xf4f6ff); sun.intensity = 3.2; sun.position.set(30, 60, 20);
{ const S = sun.shadow.camera; S.left = -14; S.right = 14; S.top = 14; S.bottom = -14; S.near = 1; S.far = 160; S.updateProjectionMatrix(); }
// the pitch: mown stripes, white lines (penalty box at the -z end), a goal
const PW = 68, PL = 105, GOALZ = -PL / 2;
const pitchTex = canvasTex(1024, 2048, g => { for (let i = 0; i < 20; i++) { g.fillStyle = i % 2 ? '#2f6f2c' : '#367a31'; g.fillRect(0, i * 2048 / 20, 1024, 2048 / 20 + 1); }
  for (let k = 0; k < 9000; k++) { g.fillStyle = `rgba(${20 + 30 * Math.random()},${60 + 50 * Math.random()},${20 + 20 * Math.random()},0.25)`; g.fillRect(Math.random() * 1024, Math.random() * 2048, 2, 3); }
  const X = x => (x / PW + 0.5) * 1024, Z = z => (z / PL + 0.5) * 2048; g.strokeStyle = 'rgba(245,245,240,0.92)'; g.lineWidth = 0.12 / PW * 1024 * 1.6;
  g.strokeRect(X(-PW / 2 + 0.5), Z(-PL / 2 + 0.5), X(PW / 2 - 0.5) - X(-PW / 2 + 0.5), Z(PL / 2 - 0.5) - Z(-PL / 2 + 0.5));
  g.beginPath(); g.moveTo(X(-PW / 2), Z(0)); g.lineTo(X(PW / 2), Z(0)); g.stroke(); g.beginPath(); g.arc(X(0), Z(0), 9.15 / PW * 1024, 0, 7); g.stroke();
  for (const sz of [-1, 1]) { const e = sz * (PL / 2 - 0.5); g.strokeRect(X(-20.16), sz < 0 ? Z(e) : Z(e - 16.5), X(20.16) - X(-20.16), Z(16.5) - Z(0)); g.strokeRect(X(-9.16), sz < 0 ? Z(e) : Z(e - 5.5), X(9.16) - X(-9.16), Z(5.5) - Z(0));
    g.beginPath(); g.arc(X(0), Z(e - sz * 11), 3, 0, 7); g.fillStyle = '#fff'; g.fill(); } });
const pitch = new THREE.Mesh(new THREE.PlaneGeometry(PW + 8, PL + 8).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ map: pitchTex, roughness: 0.92 }));
pitch.receiveShadow = true; scene.add(pitch); pitchTex.repeat.set(1, 1);
{ const surround = new THREE.Mesh(new THREE.PlaneGeometry(PW + 40, PL + 40).rotateX(-Math.PI / 2), mat(0x24452a, 0.95)); surround.position.y = -0.01; scene.add(surround); }
const goal = new THREE.Group(); goal.position.set(0, 0, GOALZ + 0.5); scene.add(goal);
{ const pm = mat(0xf4f4f0, 0.35); const post = (x) => { const p = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 2.44, 12), pm); p.position.set(x, 1.22, 0); p.castShadow = true; goal.add(p); };
  post(-3.66); post(3.66); const bar = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 7.44, 12).rotateZ(Math.PI / 2), pm); bar.position.set(0, 2.44, 0); goal.add(bar);
  const net = new THREE.Mesh(new THREE.BoxGeometry(7.32, 2.44, 2.0), new THREE.MeshBasicMaterial({ color: 0xe8e8e8, wireframe: true, transparent: true, opacity: 0.25 })); net.position.set(0, 1.22, -1.0); goal.add(net); }
// stands with a crowd (instanced), four floodlight towers
const stands = new THREE.Group(); scene.add(stands);   // rows step outward from the touchline (they were pulled into the pitch once)
{ const sm = mat(0x1b1f28, 0.9); const crowd = []; const add = (w, d, x, z, ry) => { for (let r = 0; r < 14; r++) { const st = box(w, 0.5, 0.9, 0, 0.6 + r * 0.55, 0, sm, 0, stands); st.position.set(x, 0.6 + r * 0.55, z); st.rotation.y = ry;
      const dir = V(Math.sin(ry), 0, Math.cos(ry)); st.position.addScaledVector(dir, r * 0.85); for (let k = 0; k < w; k += 0.55) crowd.push(st.position.clone().add(V(Math.cos(ry), 0, -Math.sin(ry)).multiplyScalar(k - w / 2)).add(V(0, 0.45, 0))); } };
  add(PL + 10, 0, PW / 2 + 7, 0, Math.PI / 2); add(PL + 10, 0, -PW / 2 - 7, 0, -Math.PI / 2); add(PW + 10, 0, 0, -PL / 2 - 7, Math.PI); add(PW + 10, 0, 0, PL / 2 + 7, 0);
  const cm = new THREE.InstancedMesh(new THREE.BoxGeometry(0.42, 0.55, 0.3), new THREE.MeshStandardMaterial({ roughness: 0.8 }), crowd.length); const m4 = new THREE.Matrix4();
  crowd.forEach((p, i) => { m4.makeTranslation(p.x, p.y, p.z); cm.setMatrixAt(i, m4); cm.setColorAt(i, new THREE.Color().setHSL(hash1(i * 1.3), 0.4 * hash1(i * 2.1), 0.15 + 0.35 * hash1(i * 3.7))); }); stands.add(cm); }
for (const [x, z] of [[-48, -66], [48, -66], [-48, 66], [48, 66]]) { const t = box(1.2, 42, 1.2, x, 21, z, mat(0x2a2e36, 0.6, 0.4), 0, scene);
  const panel = new THREE.Mesh(new THREE.PlaneGeometry(9, 4), new THREE.MeshBasicMaterial({ color: 0xffffff, toneMapped: false })); panel.position.set(x * 0.97, 43, z * 0.97); panel.lookAt(0, 0, 0); scene.add(panel);
  const glow = new THREE.Sprite(new THREE.SpriteMaterial({ map: canvasTex(128, 128, g => { const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64); gr.addColorStop(0, 'rgba(255,255,255,0.9)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 128, 128); }), transparent: true, depthWrite: false, toneMapped: false }));
  glow.scale.set(14, 14, 1); glow.position.copy(panel.position); scene.add(glow); }
for (const [x, z] of [[-40, -55], [40, -55], [-40, 55], [40, 55]]) { const fl = new THREE.SpotLight(0xf2f5ff, 900, 160, 0.8, 0.5, 1.4); fl.position.set(x, 40, z); fl.target.position.set(0, 0, z * 0.3); scene.add(fl, fl.target); }
// the ball
const ball = new THREE.Mesh(new THREE.IcosahedronGeometry(0.11, 2), new THREE.MeshStandardMaterial({ map: canvasTex(256, 128, g => { g.fillStyle = '#f6f6f2'; g.fillRect(0, 0, 256, 128); g.fillStyle = '#1c1c22'; for (let r = 0; r < 4; r++) for (let c = 0; c < 8; c++) { const x = c * 32 + (r % 2) * 16 + 8, y = r * 32 + 16; g.beginPath(); for (let k = 0; k < 5; k++) { const a = k / 5 * Math.PI * 2 - Math.PI / 2; g.lineTo(x + Math.cos(a) * 7, y + Math.sin(a) * 7); } g.fill(); } }), roughness: 0.5, flatShading: false }));
ball.castShadow = true; scene.add(ball);
// kits: the forward in white, the keeper in green with black trousers (both generic)
function kit(Gx, shirt, pants) { for (const [n, c] of [['shirt', shirt], ['jeans', pants]]) { const m = Gx.meshes[n]; if (!m) continue; m.material = m.material.clone(); m.material.map = null; m.material.color.set(c); m.material.roughness = 0.75; m.material.needsUpdate = true; }
  for (const n of ['shoeR', 'shoeL']) { const m = Gx.meshes[n]; if (!m) continue; m.material = m.material.clone(); m.material.map = null; m.material.color.set(0x15161a); m.material.needsUpdate = true; } }
// kits: Tenerife white shirt + blue shorts; the Andorra keeper wore black (match photos)
kit(G, 0xf6f6f2, 0x1f3f9a);
const K = await loadGuy(THREE, '/char/' + (Q.get('char') || window.CHARDEF || 'guy'), { fingers3: !!window.FINGERS3 }); scene.add(K.root); K.root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
kit(K, 0x17181b, 0x0e0f11); const RK = makeRig(K, 'keeper');
// the red card, the ambulance, the hospital (outside the stadium, along +x)
const card = new THREE.Mesh(new THREE.PlaneGeometry(0.075, 0.11), new THREE.MeshStandardMaterial({ color: 0xe0161c, emissive: 0x500000, side: THREE.DoubleSide, roughness: 0.4 })); card.scale.setScalar(6); card.visible = false; scene.add(card);
const out = new THREE.Group(); out.position.set(260, 0, 0); scene.add(out); out.visible = false;
{ const road = new THREE.Mesh(new THREE.PlaneGeometry(14, 600).rotateX(-Math.PI / 2), mat(0x24262b, 0.85)); road.position.y = 0.02; road.receiveShadow = true; out.add(road);
  for (let z = -300; z < 300; z += 9) box(0.18, 0.02, 3, 0, 0.035, z, mat(0xd8d8d0, 0.6), 0, out);
  const gr = new THREE.Mesh(new THREE.PlaneGeometry(400, 600).rotateX(-Math.PI / 2), mat(0x1d2a1a, 1)); out.add(gr);
  for (let i = 0; i < 18; i++) { const lp = box(0.2, 7, 0.2, 8.5, 3.5, -270 + i * 32, mat(0x30343b, 0.6, 0.5), 0, out); const bulb = new THREE.PointLight(0xffd59a, 25, 22, 1.6); bulb.position.set(7.5, 7, -270 + i * 32); out.add(bulb); }
  const hosp = new THREE.Group(); hosp.position.set(-30, 0, -210); out.add(hosp); box(46, 22, 26, 0, 11, 0, mat(0xd9d6cf, 0.8), 0, hosp);
  for (let r = 0; r < 5; r++) for (let c = 0; c < 10; c++) { const w = new THREE.Mesh(new THREE.PlaneGeometry(2.2, 1.6), new THREE.MeshBasicMaterial({ color: hash1(r * 10 + c) < 0.65 ? 0xffe6b0 : 0x1a2230, toneMapped: false })); w.position.set(-20 + c * 4.4, 3 + r * 4, 13.05); hosp.add(w); }
  const sign = new THREE.Mesh(new THREE.PlaneGeometry(14, 2.6), new THREE.MeshBasicMaterial({ map: canvasTex(512, 96, g => { g.fillStyle = '#c4161c'; g.fillRect(0, 0, 512, 96); g.fillStyle = '#fff'; g.font = 'bold 60px Arial'; g.fillText('EMERGENCY', 70, 70); }), toneMapped: false })); sign.position.set(0, 19.5, 13.1); hosp.add(sign); }
const amb = new THREE.Group(); out.add(amb);
{ const wm = mat(0xf2f2ee, 0.45, 0.1); box(2.1, 2.5, 5.6, 0, 1.75, 0.4, wm, 0.15, amb); box(2.1, 1.7, 1.6, 0, 1.35, -2.9, wm, 0.15, amb);
  box(2.12, 0.3, 7.2, 0, 1.4, -0.4, mat(0xd7261e, 0.5), 0, amb); box(2.0, 0.8, 0.05, 0, 1.8, -3.72, mat(0x0d1218, 0.2, 0.3), 0, amb);
  for (const [x, z] of [[-1, -2.6], [1, -2.6], [-1, 2.2], [1, 2.2]]) { const wh = new THREE.Mesh(new THREE.CylinderGeometry(0.45, 0.45, 0.3, 20).rotateZ(Math.PI / 2), mat(0x111111, 0.8)); wh.position.set(x, 0.45, z); amb.add(wh); }
  for (const x of [-0.7, 0.7]) { const b = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.15, 0.3), new THREE.MeshBasicMaterial({ color: 0x3a6dff, toneMapped: false })); b.position.set(x, 3.08, -0.6); amb.add(b); }
  const hl = new THREE.SpotLight(0xfff2d8, 120, 60, 0.5, 0.5, 1.5); hl.position.set(0, 1.2, -3.8); hl.target.position.set(0, 0, -30); amb.add(hl, hl.target); }
// readout (same look as the plane Shorts)
const hudC = document.createElement('canvas'); hudC.width = 520; hudC.height = 440; const hudT = new THREE.CanvasTexture(hudC); hudT.colorSpace = THREE.SRGBColorSpace;
const hud = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: hudT, transparent: true, depthTest: false, depthWrite: false, toneMapped: false })); hud.renderOrder = 30; camera.add(hud); scene.add(camera); hud.visible = false;
function drawHud(rows, flag) { const g = hudC.getContext('2d'); g.clearRect(0, 0, 520, 440); g.beginPath(); g.roundRect(6, 6, 508, 428, 34); g.fillStyle = 'rgba(8,14,22,0.74)'; g.fill(); g.lineWidth = 4; g.strokeStyle = 'rgba(160,200,235,0.55)'; g.stroke();
  let y = 30; for (const [lab, val, col] of rows) { g.fillStyle = '#9fb6c8'; g.font = '600 34px Arial, Helvetica, sans-serif'; g.fillText(lab, 34, y + 38); g.fillStyle = col || '#fff'; g.font = 'bold 62px Arial, Helvetica, sans-serif'; g.fillText(val, 34, y + 102, 452); y += 120; }
  if (flag) { g.font = 'bold 52px Arial, Helvetica, sans-serif'; const fw = Math.min(460, g.measureText(flag).width + 40); g.beginPath(); g.roundRect(30, 340, fw, 76, 16); g.fillStyle = '#d9241b'; g.fill(); g.fillStyle = '#fff'; g.fillText(flag, 50, 397, fw - 40); }
  hudT.needsUpdate = true; }
function fitHud() { const d = camera.near * 1.6, h = 2 * d * Math.tan(camera.fov * D2R / 2), w = h * camera.aspect, gw = 0.4 * w, gh = gw * 440 / 520; hud.scale.set(gw, gh, 1); hud.position.set(w / 2 - gw / 2 - 0.035 * w, h / 2 - 0.165 * h - gh / 2, -d); }
// ------------------------------------------------------------------ x-ray view: the forward's body goes glassy, a heart and a brain inside (explainer beats)
const XRAYM = new THREE.MeshBasicMaterial({ color: 0x7fd3ff, transparent: true, opacity: 0.16, depthWrite: false, side: THREE.DoubleSide, blending: THREE.AdditiveBlending });
const XRSAVE = new Map(); let XRON = false;
G.reset(); G.root.updateMatrixWorld(true);
// the heart: two ventricles tapering to an apex (pointing down, forward and to his left), two atria, the aorta arching back, the pulmonary trunk
// and the vena cava (blue, as in diagrams), coronary vessels over the front. Built in metres, ~13 cm tall.
const heart = new THREE.Group();
{ const meat = new THREE.MeshPhysicalMaterial({ color: 0x9a1822, roughness: 0.38, clearcoat: 0.8, clearcoatRoughness: 0.25, emissive: 0x2a0306 });
  const meat2 = meat.clone(); meat2.color.set(0x7d1620); const art = new THREE.MeshPhysicalMaterial({ color: 0xc23a3c, roughness: 0.35, clearcoat: 0.7 }); const vein = new THREE.MeshPhysicalMaterial({ color: 0x3756a8, roughness: 0.4, clearcoat: 0.6 });
  const fat = new THREE.MeshStandardMaterial({ color: 0xd9b25e, roughness: 0.6 }), cor = new THREE.MeshStandardMaterial({ color: 0xd8463a, roughness: 0.4 });
  const vg = new THREE.SphereGeometry(0.05, 40, 28), pa = vg.attributes.position;
  for (let i = 0; i < pa.count; i++) { let x = pa.getX(i), y = pa.getY(i), z = pa.getZ(i); const k = y < 0 ? 1 + (y / 0.05) * 0.62 : 1 - (y / 0.05) * 0.1; pa.setXYZ(i, x * k, y * 1.35, z * k * 0.85); } vg.computeVertexNormals();
  const vent = new THREE.Mesh(vg, meat); heart.add(vent);
  const rv = new THREE.Mesh(new THREE.SphereGeometry(0.034, 28, 20), meat); rv.scale.set(1, 1.3, 0.75); rv.position.set(0.02, -0.005, -0.018); heart.add(rv);
  for (const [x, z, c] of [[0.028, 0.012, meat2], [-0.026, 0.02, meat2]]) { const at = new THREE.Mesh(new THREE.SphereGeometry(0.026, 24, 16), c); at.position.set(x, 0.05, z); at.scale.set(1, 0.85, 1); heart.add(at); }
  const tube = (pts, r, m) => { const t = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts.map(p => V(...p))), 40, r, 14), m); heart.add(t); return t; };
  tube([[0.002, 0.04, 0.0], [0.0, 0.1, 0.0], [-0.02, 0.128, 0.02], [-0.04, 0.115, 0.038], [-0.046, 0.07, 0.045]], 0.013, art);            // aorta, arching back and down
  for (const [x, y, z] of [[0.004, 0.13, 0.008], [-0.012, 0.135, 0.018], [-0.026, 0.13, 0.026]]) tube([[x, y - 0.012, z], [x * 1.4, y + 0.02, z]], 0.0045, art);   // its branches
  tube([[-0.012, 0.035, -0.03], [-0.016, 0.085, -0.022], [-0.02, 0.105, -0.005]], 0.012, vein);                                              // pulmonary trunk
  tube([[-0.02, 0.105, -0.005], [-0.05, 0.11, 0.0]], 0.008, vein); tube([[-0.02, 0.105, -0.005], [0.01, 0.112, 0.012]], 0.008, vein);
  tube([[0.034, 0.05, 0.016], [0.035, 0.1, 0.014], [0.034, 0.14, 0.01]], 0.01, vein);                                                      // superior vena cava
  tube([[0.01, 0.03, -0.042], [-0.008, -0.01, -0.044], [-0.02, -0.045, -0.032], [-0.022, -0.068, -0.014]], 0.0035, fat);                   // front groove with its vessel
  tube([[0.01, 0.03, -0.044], [-0.008, -0.01, -0.046], [-0.02, -0.045, -0.034], [-0.022, -0.068, -0.016]], 0.002, cor);
  tube([[0.03, 0.025, -0.02], [0.044, -0.01, -0.005], [0.03, -0.045, 0.012]], 0.0022, cor); tube([[-0.03, 0.02, -0.03], [-0.045, -0.015, -0.01], [-0.04, -0.05, 0.01]], 0.0022, cor);
  heart.rotation.set(0.35, 0.3, -0.45); }
heart.position.copy(wp(G.bones.chest).add(V(-0.02, -0.035, -0.035))); scene.add(heart); G.bones.chest.attach(heart); heart.visible = false;
const HEARTS = heart.scale.clone();
const brain = new THREE.Mesh(new THREE.SphereGeometry(1, 40, 24), new THREE.MeshStandardMaterial({ color: 0xf0a6b4, emissive: 0x401018, emissiveIntensity: 0.6, roughness: 0.6 }));
{ const pa = brain.geometry.attributes.position; for (let i = 0; i < pa.count; i++) { const x = pa.getX(i), y = pa.getY(i), z = pa.getZ(i), f = 1 + 0.04 * Math.sin(x * 23 + z * 17) * Math.sin(y * 19 + x * 7); pa.setXYZ(i, x * f, y * f, z * f); } brain.geometry.computeVertexNormals(); }
brain.scale.set(0.068, 0.056, 0.083); brain.position.copy(wp(G.bones.head).add(V(0, 0.085, 0.0))); scene.add(brain); G.bones.head.attach(brain); brain.visible = false;
const BRAINP = brain.position.clone(), BRAINS = brain.scale.clone();
const XRSKIP = new Set(); heart.traverse(o => XRSKIP.add(o)); XRSKIP.add(brain);
function xray(on) { if (XRON === on) return; XRON = on; G.root.traverse(o => { if (!o.isMesh || XRSKIP.has(o)) return; if (on) { XRSAVE.set(o, o.material); o.material = XRAYM; o.castShadow = false; } else { o.material = XRSAVE.get(o) || o.material; o.castShadow = true; } }); heart.visible = brain.visible = on; }
// heart-rhythm line for the readout: 'beat' (normal), 'vf' (quivering), 'flat' (none)
function drawECG(g, mode, t, x0, y0, w, h) { g.strokeStyle = mode === 'beat' ? '#2fbf71' : '#ff5a4f'; g.lineWidth = 6; g.lineJoin = 'round'; g.beginPath();
  for (let i = 0; i <= 120; i++) { const x = x0 + w * i / 120, s = t * 1.6 + i / 120 * 2.2; let y;
    if (mode === 'beat') { const ph = s % 1; y = ph > 0.42 && ph < 0.47 ? -1 : ph > 0.47 && ph < 0.5 ? 0.35 : ph > 0.6 && ph < 0.72 ? -0.18 * Math.sin((ph - 0.6) / 0.12 * Math.PI) : 0; }
    else if (mode === 'vf') y = 0.45 * Math.sin(s * 37 + Math.sin(s * 11) * 2) + 0.25 * Math.sin(s * 23.7 + 1.3);
    else y = 0.02 * Math.sin(s * 9);
    const yy = y0 + h / 2 + y * h * 0.45; i ? g.lineTo(x, yy) : g.moveTo(x, yy); } g.stroke(); }
function drawHudECG(title, val, col, mode, t, flag) { drawHud([[title, val, col]], flag); const g = hudC.getContext('2d'); drawECG(g, mode, t, 34, 170, 452, 150); hudT.needsUpdate = true; }
// impact marks for the x-ray at the hit: red glows on the chest and the head
const impact = new THREE.Group(); scene.add(impact); impact.visible = false;
{ const tex = canvasTex(128, 128, g => { const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64); gr.addColorStop(0, 'rgba(255,80,60,1)'); gr.addColorStop(0.4, 'rgba(255,40,30,0.5)'); gr.addColorStop(1, 'rgba(255,0,0,0)'); g.fillStyle = gr; g.fillRect(0, 0, 128, 128); });
  for (const s of [0.32, 0.26]) { const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthWrite: false, depthTest: false, toneMapped: false, blending: THREE.AdditiveBlending })); sp.scale.set(s, s, 1); sp.renderOrder = 20; impact.add(sp); } }
