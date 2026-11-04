// ------------------------------------------------------------------ set: a coastal B.C. valley in late fall: a dirt trail through tall conifers, steep mountains, overcast light
home.visible = false; lamp.visible = false;
camera.far = 6000; camera.updateProjectionMatrix();
scene.background = new THREE.Color(0xaabccb); scene.fog = new THREE.Fog(0xb2c0cb, 60, 1500); scene.environmentIntensity = 0.4;
hemi.color.set(0xdbe6f0); hemi.groundColor.set(0x4a4a32); hemi.intensity = 1.1; sun.color.set(0xfff0dc); sun.intensity = 1.6; sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.03;
{ const S = sun.shadow.camera; S.left = -14; S.right = 14; S.top = 14; S.bottom = -14; S.near = 1; S.far = 200; S.updateProjectionMatrix(); }
const SKY = new THREE.Mesh(new THREE.SphereGeometry(5000, 32, 16), new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false, fog: false, uniforms: { uSet: { value: 0 } },
  vertexShader: 'varying vec3 d; void main(){ d = normalize(position); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }',
  fragmentShader: `uniform float uSet; varying vec3 d; void main(){ float h = clamp(d.y, 0., 1.); vec3 day = mix(vec3(.72,.78,.83), vec3(.5,.6,.7), pow(h, .6)); vec3 dusk = mix(vec3(.95,.62,.45), vec3(.22,.22,.38), pow(h, .5));
    gl_FragColor = vec4(mix(day, dusk, uSet), 1.);
    #include <colorspace_fragment>
  }` })); SKY.renderOrder = -10; SKY.frustumCulled = false; scene.add(SKY); window.__SKY = SKY;
const SKYU = SKY.material.uniforms;
function n2(x, z) { const xi = Math.floor(x), zi = Math.floor(z), xf = x - xi, zf = z - zi, h = (a, b) => hash1(a * 157.1 + b * 311.7);
  const u = xf * xf * (3 - 2 * xf), v = zf * zf * (3 - 2 * zf); return lerp(lerp(h(xi, zi), h(xi + 1, zi), u), lerp(h(xi, zi + 1), h(xi + 1, zi + 1), u), v); }
function fbm(x, z) { let s = 0, a = 0.5, f = 1; for (let i = 0; i < 5; i++) { s += a * n2(x * f, z * f); f *= 2.03; a *= 0.5; } return s; }
// the valley runs along z; floor about 600 m wide; steep walls up to ~1.6 km with snow on top (Bella Coola valley)
function HT(x, z) { const d = Math.abs(x + 300), wall = smooth(320, 1100, d); return wall * (900 + 900 * fbm(x / 500, z / 500)) + (1 - wall) * 0.6 * (fbm(x / 20, z / 20) - 0.5); }
{ const g = new THREE.PlaneGeometry(9000, 9000, 300, 300).rotateX(-Math.PI / 2), P = g.attributes.position, col = [];
  for (let i = 0; i < P.count; i++) { const x = P.getX(i), z = P.getZ(i); let y = HT(x, z); if (Math.abs(x) < 60 && Math.abs(z) < 120) y = Math.min(y, 0.0); P.setY(i, y); }
  g.computeVertexNormals(); const N = g.attributes.normal;
  for (let i = 0; i < P.count; i++) { const y = P.getY(i), ny = N.getY(i), k = fbm(P.getX(i) / 40, P.getZ(i) / 40);
    let c = y < 30 ? [0.22 + 0.08 * k, 0.27 + 0.08 * k, 0.15] : (y < 700 ? [0.14 + 0.05 * k, 0.22 + 0.06 * k, 0.13] : [0.42, 0.42, 0.42]); if (y > 1150 + 200 * k && ny > 0.45) c = [0.9, 0.92, 0.95];
    const cc = new THREE.Color().setRGB(c[0], c[1], c[2], THREE.SRGBColorSpace); col.push(cc.r, cc.g, cc.b); }
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  const t = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 1 })); t.receiveShadow = true; scene.add(t); }
// the river (wide, grey-green) down the middle of the valley, away from the trail
{ const r = new THREE.Mesh(new THREE.PlaneGeometry(70, 9000).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0x6f8a86, roughness: 0.2, metalness: 0.1 })); r.position.set(-300, 0.15, 0); scene.add(r); }
// the trail: packed dirt, a gentle S along z through the trees
const trailX = z => 1.6 * Math.sin(z / 14);
{ const pts = [], N = 160; const g = new THREE.BufferGeometry(), pos = [], idx = [];
  for (let i = 0; i <= N; i++) { const z = 60 - i * 1.2, x = trailX(z), w = 0.85 + 0.15 * Math.sin(i * 0.7); pos.push(x - w, 0.03, z, x + w, 0.03, z); if (i) { const a = (i - 1) * 2; idx.push(a, a + 1, a + 2, a + 1, a + 3, a + 2); } }
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setIndex(idx); g.computeVertexNormals();
  const m = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ map: canvasTex(256, 256, c => { c.fillStyle = '#6b5640'; c.fillRect(0, 0, 256, 256); for (let i = 0; i < 4000; i++) { c.fillStyle = `rgba(${60 + 50 * Math.random()},${45 + 40 * Math.random()},${30 + 30 * Math.random()},0.5)`; c.fillRect(Math.random() * 256, Math.random() * 256, 2, 2); } }), roughness: 1 }));
  m.receiveShadow = true; scene.add(m); }
// conifers (instanced): trunk + three stacked cones; thick near the trail, a forest across the valley floor for the air shot
const TREES = [];
{ const R = [], trunkG = new THREE.CylinderGeometry(0.18, 0.32, 1, 7), coneG = new THREE.ConeGeometry(1, 1, 9);
  for (let i = 0; i < 2600; i++) { const near = i < 900; const x = near ? (hash1(i * 1.1) - 0.5) * 120 : -600 + hash1(i * 2.3) * 700, z = near ? 60 - hash1(i * 3.7) * 170 : (hash1(i * 5.1) - 0.5) * 2400;
    if (Math.abs(x - trailX(z)) < 3.2 + 2 * hash1(i * 7)) continue; if (Math.abs(x + 300) < 45) continue; R.push([x, z, 14 + 16 * hash1(i * 9), hash1(i * 11)]); }
  const n = R.length, trunk = new THREE.InstancedMesh(trunkG, mat(0x4a3526, 0.95), n), cones = new THREE.InstancedMesh(coneG, mat(0x1f3b26, 0.9), n * 3), M = new THREE.Matrix4(), q = new THREE.Quaternion(), col = new THREE.Color();
  R.forEach(([x, z, h, k], i) => { M.compose(V(x, h * 0.25, z), q, V(1 + k * 0.3, h * 0.5, 1 + k * 0.3)); trunk.setMatrixAt(i, M);
    for (let j = 0; j < 3; j++) { const w = (2.6 + 1.2 * k) * (1 - j * 0.24), y0 = h * (0.3 + j * 0.22); M.compose(V(x, y0 + h * 0.2, z), q, V(w, h * 0.42, w)); cones.setMatrixAt(i * 3 + j, M);
      col.setHSL(0.36 + 0.04 * k, 0.35, 0.13 + 0.06 * k + j * 0.01); cones.setColorAt(i * 3 + j, col); } TREES.push([x, z]); });
  trunk.castShadow = cones.castShadow = true; trunk.receiveShadow = cones.receiveShadow = true; scene.add(trunk, cones); }
// undergrowth: ferns and salal (low green clumps), mossy logs, a few rocks
for (let i = 0; i < 260; i++) { const z = 50 - hash1(i * 2.9) * 120, x = trailX(z) + (hash1(i * 4.3) > 0.5 ? 1 : -1) * (2.2 + 7 * hash1(i * 6.1));
  const b = new THREE.Mesh(new THREE.DodecahedronGeometry(0.22 + 0.3 * hash1(i), 1), mat(new THREE.Color().setHSL(0.29 + 0.05 * hash1(i * 3), 0.5, 0.1 + 0.05 * hash1(i * 5)), 0.95)); b.position.set(x, 0.15, z); b.scale.set(1.3, 0.55, 1.1); b.castShadow = true; scene.add(b); }
for (let i = 0; i < 10; i++) { const z = 40 - i * 11, x = trailX(z) + (i % 2 ? 5 : -5); const l = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.35, 7, 10).rotateZ(Math.PI / 2), mat(0x4b5a32, 0.95)); l.position.set(x, 0.3, z); l.rotation.y = i; l.castShadow = true; scene.add(l); }
// ---- the grizzly: ~2 m long, ~1.05 m at the shoulder hump, dished face, round ears, long front claws. Root on the ground under the chest, nose to -z
const furTex = canvasTex(256, 256, c => { c.fillStyle = '#5a3d24'; c.fillRect(0, 0, 256, 256); for (let i = 0; i < 9000; i++) { const l = 30 + 60 * Math.random(); c.strokeStyle = `rgba(${l + 40},${l + 15},${l - 10},0.35)`; c.beginPath(); const x = Math.random() * 256, y = Math.random() * 256; c.moveTo(x, y); c.lineTo(x + 2 * Math.random() - 1, y + 5); c.stroke(); } });
furTex.wrapS = furTex.wrapT = THREE.RepeatWrapping; furTex.repeat.set(3, 3);
const furM = new THREE.MeshStandardMaterial({ map: furTex, color: 0xb08a63, roughness: 1 }), furDark = new THREE.MeshStandardMaterial({ map: furTex, color: 0x6d5038, roughness: 1 }), furTip = new THREE.MeshStandardMaterial({ map: furTex, color: 0xd2b48c, roughness: 1 });
const BEAR = new THREE.Group(); scene.add(BEAR);
{ const U = BEAR.userData, sph = (m, sx, sy, sz, x, y, z, par = BEAR) => { const o = new THREE.Mesh(new THREE.SphereGeometry(1, 24, 16), m); o.scale.set(sx, sy, sz); o.position.set(x, y, z); o.castShadow = true; par.add(o); return o; };
  const body = new THREE.Group(); BEAR.add(body); U.body = body;
  sph(furM, 0.5, 0.48, 0.95, 0, 0.88, 0.05, body); sph(furTip, 0.42, 0.3, 0.42, 0, 1.18, -0.38, body); sph(furM, 0.48, 0.5, 0.52, 0, 0.86, 0.62, body); sph(furDark, 0.3, 0.32, 0.42, 0, 0.92, -0.8, body);
  const head = new THREE.Group(); head.position.set(0, 0.92, -1.1); body.add(head); U.head = head;
  sph(furTip, 0.25, 0.23, 0.27, 0, 0, 0, head); const muz = new THREE.Mesh(new THREE.CylinderGeometry(0.085, 0.13, 0.32, 16).rotateX(Math.PI / 2), furDark); muz.position.set(0, -0.06, -0.28); head.add(muz);
  sph(mat(0x111111, 0.3), 0.06, 0.045, 0.04, 0, -0.04, -0.44, head); for (const s of [-1, 1]) { sph(furDark, 0.08, 0.08, 0.04, s * 0.17, 0.2, 0.02, head); sph(mat(0x0b0b0b, 0.2), 0.022, 0.022, 0.02, s * 0.1, 0.06, -0.21, head); }
  const jaw = sph(furDark, 0.09, 0.04, 0.16, 0, -0.14, -0.22, head); U.jaw = jaw;
  sph(furTip, 0.06, 0.12, 0.05, 0, 0.84, 0.98, body);   // tail stub
  U.legs = [];
  for (const [x, z, front] of [[-0.27, -0.52, 1], [0.27, -0.52, 1], [-0.26, 0.62, 0], [0.26, 0.62, 0]]) { const hip = new THREE.Group(); hip.position.set(x, 0.86, z); body.add(hip);
    const up = new THREE.Mesh(new THREE.CapsuleGeometry(front ? 0.15 : 0.17, 0.4, 6, 12), furDark); up.position.y = -0.28; up.castShadow = true; hip.add(up);
    const knee = new THREE.Group(); knee.position.y = -0.52; hip.add(knee); const lo = new THREE.Mesh(new THREE.CapsuleGeometry(0.12, 0.26, 6, 12), furDark); lo.position.y = -0.14; lo.castShadow = true; knee.add(lo);
    const paw = new THREE.Mesh(new THREE.SphereGeometry(1, 16, 10), furDark); paw.scale.set(0.14, 0.07, 0.19); paw.position.set(0, -0.3, -0.05); knee.add(paw);
    if (front) for (let c = -2; c <= 2; c++) { const cl = new THREE.Mesh(new THREE.ConeGeometry(0.014, 0.1, 6).rotateX(-Math.PI / 2 - 0.5), mat(0xd8cfb8, 0.4)); cl.position.set(c * 0.045, -0.33, -0.25); knee.add(cl); }
    U.legs.push({ hip, knee, front }); } }
// pose the bear: position, heading, gait phase (radians) and stride (0 = standing, 1 = full gallop), head pitch, mouth
function setBear(p, yaw, ph = 0, amp = 0, headP = 0, mouth = 0, sniff = 0) { const U = BEAR.userData; BEAR.visible = true; BEAR.position.copy(p); BEAR.rotation.set(0, yaw, 0);
  U.body.position.y = 0.06 * amp * Math.abs(Math.sin(ph)); U.body.rotation.x = 0.06 * amp * Math.sin(ph + 1);
  U.legs.forEach((l, i) => { const o = [0, 0.4, Math.PI, Math.PI + 0.4][i], s = Math.sin(ph + o); l.hip.rotation.x = 0.75 * amp * s; l.knee.rotation.x = (l.front ? -1 : 1) * 0.6 * amp * Math.max(0, Math.sin(ph + o + 1.2)); });
  U.head.rotation.x = headP + 0.08 * amp * Math.sin(ph * 2) + sniff * 0.15 * Math.sin(ph * 3); U.head.rotation.y = sniff * 0.3 * Math.sin(ph * 0.8); U.jaw.position.y = -0.14 - 0.06 * mouth; U.jaw.rotation.x = 0.3 * mouth; }
// ---- the hikers: rain jackets (shirt recoloured, arm skin painted as sleeves to the wrist), jeans, boots; a backpack; bear spray
const K = await loadGuy(THREE, '/char/' + (Q.get('char') || window.CHARDEF || 'guy'), { fingers3: !!window.FINGERS3 }); scene.add(K.root); K.root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
const RK = makeRig(K, 'hiker2');
function jacket(Gx, hex) { const lin = new THREE.Color(hex);
  const sh = Gx.meshes.shirt; if (sh) { sh.material = sh.material.clone(); sh.material.map = null; sh.material.color.set(hex); sh.material.roughness = 0.6; sh.material.needsUpdate = true; }
  for (const n of ['shoeR', 'shoeL']) { const m = Gx.meshes[n]; if (!m) continue; m.material = m.material.clone(); m.material.map = null; m.material.color.set(0x3a2a1c); m.material.roughness = 0.6; m.material.needsUpdate = true; }
  const sk = Gx.meshes.skin_head, ga = sk.geometry.attributes, names = sk.skeleton.bones.map(b => b.name), a = new Float32Array(ga.position.count * 2);
  Gx.reset(); Gx.root.updateMatrixWorld(true); const WR = {}; for (const S of ['R', 'L']) { const wr = wp(Gx.bones['hand' + S]), el = wp(Gx.bones['farm' + S]); WR[S] = { wr, d: wr.clone().sub(el).normalize() }; }
  const _p = V(0, 0, 0);
  for (let i = 0; i < ga.position.count; i++) { let arm = 0, side = null; for (let k = 0; k < 4; k++) { const w = ga.skinWeight.getComponent(i, k), n = names[ga.skinIndex.getComponent(i, k)];
      if (/^(uarm|uarmTwist|farm|farmTwist)/.test(n)) { arm += w; side = n.slice(-1); } }
    let sl = 0; if (arm > 0.3 && side && WR[side]) { _p.set(ga.position.getX(i), ga.position.getY(i), ga.position.getZ(i)).applyMatrix4(sk.matrixWorld); sl = clamp((-_p.clone().sub(WR[side].wr).dot(WR[side].d) - 0.02) / 0.02, 0, 1); }
    a[i * 2] = sl; }
  sk.geometry.setAttribute('aSuit', new THREE.BufferAttribute(a, 2));
  const m = sk.material = sk.material.clone(), old = m.onBeforeCompile, oldKey = m.customProgramCacheKey ? m.customProgramCacheKey.bind(m) : () => '';
  m.onBeforeCompile = (s, r) => { if (old) old.call(m, s, r);
    s.vertexShader = 'attribute vec2 aSuit; varying vec2 vSuit;\n' + s.vertexShader.replace('#include <begin_vertex>', '#include <begin_vertex>\n vSuit = aSuit;');
    s.fragmentShader = 'varying vec2 vSuit;\n' + s.fragmentShader.replace('#include <map_fragment>', `#include <map_fragment>
      diffuseColor.rgb = mix(diffuseColor.rgb, vec3(${lin.r.toFixed(4)}, ${lin.g.toFixed(4)}, ${lin.b.toFixed(4)}), smoothstep(0.45, 0.55, vSuit.x));`)
      .replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\n roughnessFactor = mix(roughnessFactor, 0.6, smoothstep(0.45, 0.55, vSuit.x));'); };
  m.customProgramCacheKey = () => oldKey() + '|jacket' + hex; m.needsUpdate = true; }
jacket(G, 0x9a2d22); jacket(K, 0x2c5a44);
function makePack(c) { const p = new THREE.Group(); scene.add(p); box(0.36, 0.48, 0.2, 0, 0, 0, mat(c, 0.8), 0.06, p).castShadow = true; box(0.3, 0.2, 0.06, 0, -0.08, 0.12, mat(new THREE.Color(c).multiplyScalar(0.7), 0.8), 0.03, p);
  for (const s of [-1, 1]) box(0.05, 0.4, 0.04, s * 0.12, 0.02, -0.12, mat(0x222222, 0.8), 0.01, p); return p; }
const PACKG = makePack(0x37474f), PACKK = makePack(0x6a4a2a);
function placePack(pk, Gx) { const ch = wp(Gx.bones.chest), q = Gx.root.quaternion; pk.position.copy(ch).add(V(0, -0.1, 0.19).applyQuaternion(q)); pk.quaternion.copy(q); pk.visible = true; }
function makeSpray() { const s = new THREE.Group(); scene.add(s); const c = new THREE.Mesh(new THREE.CylinderGeometry(0.032, 0.032, 0.2, 16), mat(0xe8641c, 0.5)); s.add(c);
  box(0.05, 0.05, 0.05, 0, 0.12, 0, mat(0x1b1b1b, 0.5), 0.01, s); box(0.02, 0.025, 0.04, 0, 0.12, -0.04, mat(0x1b1b1b, 0.5), 0, s); box(0.012, 0.05, 0.03, 0, 0.07, -0.05, mat(0x1b1b1b, 0.5), 0, s); return s; }
const SPRAYG = makeSpray(), SPRAYK = makeSpray();
// the spray can in the right hand, nozzle along the forearm; or on the hip belt
function sprayInHand(sp, Gx) { const h = wp(Gx.bones.handR), f = wp(Gx.bones.farmR), d = h.clone().sub(f).normalize(); sp.position.copy(h).addScaledVector(d, 0.05);
  sp.quaternion.setFromUnitVectors(V(0, 1, 0), d); sp.visible = true; return { p: h.clone().addScaledVector(d, 0.18), d }; }
function sprayOnHip(sp, Gx) { const q = Gx.root.quaternion, hp = wp(Gx.bones.thighR || Gx.bones.hips); sp.position.copy(hp).add(V(0.12, 0.08, 0).applyQuaternion(q)); sp.quaternion.copy(q); sp.visible = true; }
// the pepper cloud: soft orange puffs from the nozzle
const cloudTex = canvasTex(128, 128, g => { const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64); gr.addColorStop(0, 'rgba(255,150,60,0.9)'); gr.addColorStop(0.5, 'rgba(240,120,50,0.45)'); gr.addColorStop(1, 'rgba(230,110,40,0)'); g.fillStyle = gr; g.fillRect(0, 0, 128, 128); });
const CLOUD = []; for (let i = 0; i < 40; i++) { const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: cloudTex, transparent: true, depthWrite: false })); s.visible = false; scene.add(s); CLOUD.push(s); }
// the closed trail: a sign, tape, and a culvert bear trap on its trailer
const signM = new THREE.MeshBasicMaterial({ map: canvasTex(512, 300, g => { g.fillStyle = '#f2c21a'; g.fillRect(0, 0, 512, 300); g.fillStyle = '#111'; g.fillRect(14, 14, 484, 272); g.fillStyle = '#f2c21a'; g.fillRect(24, 24, 464, 252); g.fillStyle = '#111'; g.font = 'bold 92px Arial'; g.textAlign = 'center'; g.fillText('AREA', 256, 128); g.fillText('CLOSED', 256, 228); }), toneMapped: false });
const SIGN = new THREE.Group(); { const b = new THREE.Mesh(new THREE.PlaneGeometry(1.1, 0.65), signM); b.position.y = 1.35; SIGN.add(b); for (const s of [-1, 1]) box(0.07, 1.4, 0.07, s * 0.45, 0.7, -0.03, mat(0x6b5a44, 0.9), 0, SIGN); } scene.add(SIGN);
const TAPE = new THREE.Mesh(new THREE.BoxGeometry(5, 0.07, 0.01), new THREE.MeshBasicMaterial({ color: 0xf2c21a, toneMapped: false })); scene.add(TAPE);
const TRAP = new THREE.Group(); { const tm = mat(0xaab0b6, 0.4, 0.7); const c = new THREE.Mesh(new THREE.CylinderGeometry(0.65, 0.65, 2.6, 24, 1, true).rotateX(Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0xaab0b6, roughness: 0.45, metalness: 0.7, side: THREE.DoubleSide })); c.position.y = 1.15; c.castShadow = true; TRAP.add(c);
  const end = new THREE.Mesh(new THREE.CircleGeometry(0.65, 24), tm); end.position.set(0, 1.15, 1.3); TRAP.add(end); box(0.06, 1.4, 0.06, 0, 1.15, -1.32, mat(0x555a60, 0.5, 0.6), 0, TRAP); for (let i = 0; i < 9; i++) { const h = new THREE.Mesh(new THREE.CircleGeometry(0.05, 10), mat(0x111111, 0.8)); h.position.set(0.651, 1.0 + 0.3 * (i % 3), -0.9 + 0.45 * Math.floor(i / 3)); h.rotation.y = Math.PI / 2; TRAP.add(h); }
  for (const s of [-1, 1]) { const w = new THREE.Mesh(new THREE.CylinderGeometry(0.33, 0.33, 0.2, 18).rotateZ(Math.PI / 2), mat(0x1b1b1b, 0.8)); w.position.set(s * 0.78, 0.33, 0.3); TRAP.add(w); }
  box(0.08, 0.08, 1.4, 0, 0.45, -1.8, mat(0x555a60, 0.5, 0.6), 0, TRAP); } scene.add(TRAP);
// arrows and the readout
function arrowMesh(color) { const s = new THREE.Shape(); s.moveTo(-0.05, -0.32); s.lineTo(0.05, -0.32); s.lineTo(0.05, 0.08); s.lineTo(0.13, 0.08); s.lineTo(0, 0.25); s.lineTo(-0.13, 0.08); s.lineTo(-0.05, 0.08); s.closePath();
  const m = new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth: 0.04, bevelEnabled: false }), new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.92, depthTest: false, toneMapped: false })); m.renderOrder = 25; m.visible = false; scene.add(m); return m; }
const ARS = [arrowMesh(0xff4a3a), arrowMesh(0xff4a3a), arrowMesh(0x3ad27a), arrowMesh(0x3ad27a)];
const XM = new THREE.Sprite(new THREE.SpriteMaterial({ map: canvasTex(256, 256, g => { g.strokeStyle = '#ff3b2e'; g.lineWidth = 34; g.lineCap = 'round'; g.beginPath(); g.moveTo(50, 50); g.lineTo(206, 206); g.moveTo(206, 50); g.lineTo(50, 206); g.stroke(); }), depthTest: false, toneMapped: false })); XM.renderOrder = 26; XM.visible = false; scene.add(XM);
const hudC = document.createElement('canvas'); hudC.width = 520; hudC.height = 440; const hudT = new THREE.CanvasTexture(hudC); hudT.colorSpace = THREE.SRGBColorSpace;
const hud = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: hudT, transparent: true, depthTest: false, depthWrite: false, toneMapped: false })); hud.renderOrder = 30; camera.add(hud); scene.add(camera); hud.visible = false;
function drawHud(rows, flag, fcol = '#d9241b') { const g = hudC.getContext('2d'); g.clearRect(0, 0, 520, 440); g.beginPath(); g.roundRect(6, 6, 508, 428, 34); g.fillStyle = 'rgba(8,14,22,0.74)'; g.fill(); g.lineWidth = 4; g.strokeStyle = 'rgba(160,200,235,0.55)'; g.stroke();
  let y = 30; for (const [lab, val, col] of rows) { g.fillStyle = '#9fb6c8'; g.font = '600 34px Arial, Helvetica, sans-serif'; g.fillText(lab, 34, y + 38); g.fillStyle = col || '#fff'; g.font = 'bold 62px Arial, Helvetica, sans-serif'; g.fillText(val, 34, y + 102, 452); y += 120; }
  if (flag) { g.font = 'bold 52px Arial, Helvetica, sans-serif'; const fw = Math.min(460, g.measureText(flag).width + 40); g.beginPath(); g.roundRect(30, 340, fw, 76, 16); g.fillStyle = fcol; g.fill(); g.fillStyle = '#fff'; g.fillText(flag, 50, 397, fw - 40); }
  hudT.needsUpdate = true; }
function fitHud() { const d = camera.near * 1.6, h = 2 * d * Math.tan(camera.fov * D2R / 2), w = h * camera.aspect, gw = 0.4 * w, gh = gw * 440 / 520; hud.scale.set(gw, gh, 1); hud.position.set(w / 2 - gw / 2 - 0.035 * w, h / 2 - 0.165 * h - gh / 2, -d); }
