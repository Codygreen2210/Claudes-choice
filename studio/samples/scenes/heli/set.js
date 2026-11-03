// ------------------------------------------------------------------ set: a high Himalayan valley (Pheriche-like), a stone-ringed helipad, two generic AS350-type helicopters (no logos)
home.visible = false; lamp.visible = false; G.root.visible = false;
camera.far = 9000; camera.updateProjectionMatrix();
scene.background = new THREE.Color(0x9ec4ea); scene.fog = new THREE.Fog(0xc4d6e8, 900, 7000); scene.environmentIntensity = 0.35;
hemi.color.set(0xdbe8ff); hemi.groundColor.set(0x8a8478); hemi.intensity = 0.6; sun.color.set(0xfff2de); sun.intensity = 2.8; sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.04;
{ const S = sun.shadow.camera; S.left = -18; S.right = 18; S.top = 18; S.bottom = -18; S.near = 1; S.far = 300; S.updateProjectionMatrix(); }
// sky dome that rides with the camera (inside the far plane), day or dusk
const SKY = new THREE.Mesh(new THREE.SphereGeometry(8000, 32, 16), new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false, fog: false, uniforms: { uSet: { value: 0 } },
  vertexShader: 'varying vec3 d; void main(){ d = normalize(position); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }',
  fragmentShader: `uniform float uSet; varying vec3 d; void main(){ float h = clamp(d.y, 0., 1.); vec3 day = mix(vec3(.78,.87,.96), vec3(.20,.42,.80), pow(h, .5)); vec3 dusk = mix(vec3(1.,.66,.5), vec3(.22,.2,.42), pow(h, .45));
    gl_FragColor = vec4(mix(day, dusk, uSet), 1.);
    #include <colorspace_fragment>
  }` })); SKY.renderOrder = -10; SKY.frustumCulled = false; scene.add(SKY); window.__SKY = SKY;
const SKYU = SKY.material.uniforms;
// terrain: a flat glacial valley floor running north (-z, to base camp) and south (+z, to Lukla), steep rock walls, snow peaks
function n2(x, z) { const xi = Math.floor(x), zi = Math.floor(z), xf = x - xi, zf = z - zi, h = (a, b) => hash1(a * 157.1 + b * 311.7);
  const u = xf * xf * (3 - 2 * xf), v = zf * zf * (3 - 2 * zf); return lerp(lerp(h(xi, zi), h(xi + 1, zi), u), lerp(h(xi, zi + 1), h(xi + 1, zi + 1), u), v); }
function fbm(x, z) { let s = 0, a = 0.5, f = 1; for (let i = 0; i < 5; i++) { s += a * n2(x * f, z * f); f *= 2.03; a *= 0.5; } return s; }
const valleyX = z => 60 * Math.sin(z / 900);
function HT(x, z) { const d = Math.abs(x - valleyX(z)); const wall = smooth(130, 900, d), r = fbm(x / 420, z / 420);
  let h = wall * (500 + 1300 * r) + smooth(700, 2600, d) * 900 * fbm(x / 900 + 7, z / 900);
  for (const [px, pz, ph, pr] of [[-1500, -2600, 1900, 800], [1700, -1200, 1700, 700], [-1300, 900, 1500, 650], [1500, 2400, 1700, 800], [300, -4200, 2200, 1200]]) h += ph * Math.exp(-((x - px) ** 2 + (z - pz) ** 2) / (pr * pr));
  return h + (1 - wall) * 1.2 * (fbm(x / 30, z / 30) - 0.5); }
{ const g = new THREE.PlaneGeometry(14000, 14000, 360, 360).rotateX(-Math.PI / 2), P = g.attributes.position, col = [];
  for (let i = 0; i < P.count; i++) { const x = P.getX(i), z = P.getZ(i); let y = HT(x, z); if (Math.abs(x) < 40 && Math.abs(z) < 40) y = Math.min(y, 0.3 * smooth(25, 40, Math.max(Math.abs(x), Math.abs(z)))); P.setY(i, y); }
  g.computeVertexNormals(); const N = g.attributes.normal;
  for (let i = 0; i < P.count; i++) { const y = P.getY(i), ny = N.getY(i), x = P.getX(i), z = P.getZ(i), k = fbm(x / 25, z / 25);
    const rock = [0.36 + 0.12 * k, 0.33 + 0.1 * k, 0.31 + 0.08 * k], grass = [0.46 + 0.06 * k, 0.43 + 0.05 * k, 0.37 + 0.04 * k], snow = [0.9, 0.92, 0.96];
    let c = y < 40 ? grass : rock; if (y > 900 + 300 * k && ny > 0.72) c = snow; if (y > 1700) c = ny > 0.5 ? snow : [0.45, 0.43, 0.42]; const cc = new THREE.Color().setRGB(c[0], c[1], c[2], THREE.SRGBColorSpace); col.push(cc.r, cc.g, cc.b); }
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  const t = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.95 })); t.receiveShadow = true; scene.add(t); }
// snow patches and stones scattered on the valley floor near the pad
for (let i = 0; i < 160; i++) { const x = (hash1(i * 3.1) - 0.5) * 220, z = (hash1(i * 7.3) - 0.5) * 300; if (Math.abs(x) < 16 && Math.abs(z) < 16) continue;
  if (Math.abs(x) < 60 && Math.abs(z) < 60) continue; const s = new THREE.Mesh(new THREE.CircleGeometry(0.6 + 1.6 * hash1(i), 14).rotateX(-Math.PI / 2), mat(0xf2f5fa, 0.9)); s.position.set(x, 0.32 + 0.002 * i, z); s.scale.z = 0.6 + 0.8 * hash1(i * 9); s.receiveShadow = true; scene.add(s); }
for (let i = 0; i < 120; i++) { const x = (hash1(i * 5.9) - 0.5) * 200, z = (hash1(i * 2.3) - 0.5) * 260; if (Math.abs(x) < 15 && Math.abs(z) < 15) continue;
  const r = new THREE.Mesh(new THREE.DodecahedronGeometry(0.3 + 0.9 * hash1(i * 4), 0), mat(0x6f6a66, 0.95)); r.position.set(x, 0.3, z); r.rotation.set(i, i * 2, i * 3); r.castShadow = true; scene.add(r); }
// the helipad: flat ground, a ring of white stones, a painted H
{ const pad = new THREE.Mesh(new THREE.CircleGeometry(11, 48).rotateX(-Math.PI / 2), mat(0x8c8579, 0.95)); pad.position.y = 0.31; pad.receiveShadow = true; scene.add(pad);
  for (let i = 0; i < 40; i++) { const a = i / 40 * Math.PI * 2, st = new THREE.Mesh(new THREE.DodecahedronGeometry(0.28, 0), mat(0xf4f4f0, 0.8)); st.position.set(Math.cos(a) * 11, 0.4, Math.sin(a) * 11); st.castShadow = true; scene.add(st); }
  const hm = mat(0xf4f4f0, 0.8); for (const [w, d, x, z] of [[0.9, 6, -1.8, 0], [0.9, 6, 1.8, 0], [2.7, 0.9, 0, 0]]) { const p = new THREE.Mesh(new THREE.BoxGeometry(w, 0.04, d), hm); p.position.set(x, 0.33, z); p.receiveShadow = true; scene.add(p); } }
// a windsock and a line of prayer flags between two poles
const sockM = mat(0xff6a1a, 0.7); box(0.1, 5, 0.1, 13, 2.8, -6, mat(0xcccccc, 0.5), 0); const sock = new THREE.Mesh(new THREE.ConeGeometry(0.35, 2.2, 14, 1, true).rotateZ(Math.PI / 2), sockM); sock.position.set(14.1, 5.1, -6); scene.add(sock);
const flags = [];
{ const a = V(-15, 4.5, 14), b = V(-4, 3.6, 22); box(0.12, 4.5, 0.12, a.x, 2.4, a.z, mat(0x7a5a3a, 0.9), 0); box(0.12, 3.6, 0.12, b.x, 1.9, b.z, mat(0x7a5a3a, 0.9), 0);
  const cols = [0x2a5bd7, 0xf4f4f0, 0xd62a2a, 0x2aa04a, 0xf2c21a]; for (let i = 0; i < 20; i++) { const u = (i + 0.5) / 20, p = a.clone().lerp(b, u); p.y -= 0.9 * Math.sin(Math.PI * u);
    const f = new THREE.Mesh(new THREE.PlaneGeometry(0.45, 0.55), new THREE.MeshStandardMaterial({ color: cols[i % 5], roughness: 0.8, side: THREE.DoubleSide })); f.position.copy(p).add(V(0, -0.3, 0)); f.lookAt(f.position.clone().add(V(-0.6, 0, 1))); scene.add(f); flags.push(f); } }
// stone lodges with coloured tin roofs (the village), along the east side of the floor
for (let i = 0; i < 14; i++) { const x = 34 + 22 * hash1(i * 1.7) + (i % 2) * 14, z = -70 + i * 11 + 4 * hash1(i * 3), w = 7 + 4 * hash1(i * 5), d = 5 + 3 * hash1(i * 8), h = 2.6 + 1.2 * hash1(i * 4);
  const L = new THREE.Group(); L.position.set(x, 0.3, z); L.rotation.y = 0.1 * (hash1(i) - 0.5); scene.add(L);
  box(w, h, d, 0, h / 2, 0, mat(new THREE.Color().setHSL(0.08, 0.08, 0.55 + 0.12 * hash1(i * 6)), 0.95), 0.05, L).castShadow = true;
  const roof = new THREE.Mesh(new THREE.CylinderGeometry(0.01, d * 0.62, w * 1.05, 4, 1).rotateZ(Math.PI / 2).rotateX(Math.PI / 4), mat([0x2b5fb3, 0x2f8a4a, 0xb53a2a, 0x2a7f9a][i % 4], 0.55, 0.35)); roof.scale.set(1, 0.42, 1); roof.position.y = h + d * 0.2; roof.castShadow = true; L.add(roof);
  for (let k = -1; k <= 1; k += 2) box(0.9, 0.9, 0.05, k * w * 0.25, h * 0.55, d / 2 + 0.02, mat(0x2a3440, 0.3), 0, L); }
// low stone walls (yak pens)
for (let i = 0; i < 6; i++) box(14, 0.9, 0.6, 30 + 8 * hash1(i), 0.75, -40 + i * 16, mat(0x7a756e, 0.95), 0.1).castShadow = true;
// ---- the helicopter (AS350-type: one main rotor with three blades, tail rotor on the left, skids). Root at the skid bottoms, nose to -z.
const glassM = new THREE.MeshStandardMaterial({ color: 0x1e2c38, roughness: 0.08, metalness: 0.4, transparent: true, opacity: 0.88 });
const bladeM = mat(0x2a2c30, 0.5, 0.3), darkM = mat(0x34373c, 0.6, 0.4), skidM = mat(0x9aa0a8, 0.4, 0.7);
const ROTOR_Y = 3.1, ROTOR_R = 5.35;
function makeHeli(bodyC, stripeC) { const h = new THREE.Group(); scene.add(h); const bodyM = mat(bodyC, 0.35, 0.2), strM = mat(stripeC, 0.4, 0.2), U = h.userData;
  const body = new THREE.Group(); body.position.y = 0.55; h.add(body); U.body = body;
  const cab = new THREE.Mesh(new THREE.SphereGeometry(1, 40, 24), bodyM); cab.scale.set(0.92, 0.88, 1.95); cab.position.set(0, 1.0, 0); cab.castShadow = true; body.add(cab);
  const win = new THREE.Mesh(new THREE.SphereGeometry(1, 40, 24, 0, Math.PI * 2, 0, Math.PI * 0.62), glassM); win.scale.set(0.935, 0.895, 1.97); win.rotation.x = -Math.PI / 2 - 0.25; win.position.set(0, 1.08, -0.15); body.add(win); U.win = win;
  for (const s of [-1, 1]) { const sw = new THREE.Mesh(new THREE.PlaneGeometry(1.2, 0.62), glassM); sw.position.set(s * 0.925, 1.2, 0.55); sw.rotation.y = s * Math.PI / 2; body.add(sw); }
  const belly = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 16), strM); belly.scale.set(0.93, 0.5, 1.9); belly.position.set(0, 0.55, 0.05); body.add(belly);   // stripe colour on the lower body
  box(1.3, 0.75, 2.3, 0, 1.95, 1.0, bodyM, 0.3, body).castShadow = true;   // engine and gearbox cowl
  box(0.5, 0.4, 0.9, 0, 2.05, 2.2, darkM, 0.15, body);                   // exhaust
  const boom = new THREE.Mesh(new THREE.CylinderGeometry(0.17, 0.36, 4.9, 16).rotateX(Math.PI / 2), bodyM); boom.position.set(0, 1.45, 4.35); boom.castShadow = true; body.add(boom);
  const strBoom = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.37, 2.2, 16).rotateX(Math.PI / 2), strM); strBoom.position.set(0, 1.42, 3.2); body.add(strBoom);
  const stab = box(2.3, 0.07, 0.5, 0, 1.45, 5.0, bodyM, 0.03, body); for (const s of [-1, 1]) box(0.06, 0.55, 0.45, s * 1.15, 1.45, 5.0, strM, 0.02, body);
  const fin = new THREE.Mesh(new THREE.BoxGeometry(0.1, 1.5, 0.75), strM); fin.position.set(0, 2.0, 6.55); fin.rotation.x = 0.3; fin.castShadow = true; body.add(fin);
  box(0.1, 0.55, 0.5, 0, 0.95, 6.55, strM, 0.02, body);
  const trot = new THREE.Group(); trot.position.set(-0.18, 2.1, 6.75); body.add(trot); U.trot = trot;
  for (let k = 0; k < 2; k++) { const b = box(0.04, 0.93 * 2, 0.16, 0, 0, 0, bladeM, 0, trot); b.rotation.x = k * Math.PI / 2; }
  // skids
  for (const s of [-1, 1]) { const sk = new THREE.Mesh(new THREE.CapsuleGeometry(0.05, 3.4, 4, 8).rotateX(Math.PI / 2), skidM); sk.position.set(s * 1.05, 0.05, -0.1); sk.castShadow = true; h.add(sk);
    for (const z of [-0.9, 0.8]) { const st = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, 0.85, 8), skidM); st.position.set(s * 0.8, 0.45, z); st.rotation.z = -s * 0.55; h.add(st); } }
  // main rotor: mast, hub, three blades; a faint disc for the blur
  box(0.18, 0.55, 0.18, 0, 2.55, 0.1, darkM, 0.04, body); const rot = new THREE.Group(); rot.position.set(0, ROTOR_Y - 0.55, 0.1); body.add(rot); U.rot = rot;
  box(0.5, 0.18, 0.5, 0, 0, 0, darkM, 0.08, rot); U.blades = [];
  for (let k = 0; k < 3; k++) { const arm = new THREE.Group(); arm.rotation.y = k * Math.PI * 2 / 3; rot.add(arm); const b = box(ROTOR_R - 0.2, 0.05, 0.34, (ROTOR_R + 0.2) / 2, 0, 0, bladeM, 0, arm); b.castShadow = true;
    box(0.25, 0.052, 0.34, ROTOR_R - 0.15, 0, 0, mat(0xe8e8e8, 0.5), 0, arm); U.blades.push(arm); }
  const disc = new THREE.Mesh(new THREE.CircleGeometry(ROTOR_R, 48).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ color: 0x202428, transparent: true, opacity: 0.12, depthWrite: false })); disc.position.y = 0.01; rot.add(disc); U.disc = disc;
  return h; }
const HA = makeHeli(0xf4f5f6, 0x1f8f9a), HB = makeHeli(0xf2f2f0, 0xc0302a);    // A: cargo, up from Lukla (teal stripe); B: from base camp with two trekkers (red stripe)
// debris: rotor blade pieces, small body bits and window glass (no people are ever shown)
const bitM = [mat(0x2a2c30, 0.5, 0.3), mat(0xf2f2f0, 0.4), mat(0xc0302a, 0.4), mat(0x1f8f9a, 0.4)], glassBitM = new THREE.MeshStandardMaterial({ color: 0xbfe4ff, roughness: 0.05, metalness: 0.2, transparent: true, opacity: 0.8 });
const DEB = [];
function addDeb(geo, m, t0, p0, v0, spin) { const o = new THREE.Mesh(geo, m); o.castShadow = true; o.visible = false; scene.add(o); DEB.push({ o, t0, p0, v0, spin }); }
// snow / dust puffs
const puffTex = canvasTex(128, 128, g => { const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64); gr.addColorStop(0, 'rgba(255,255,255,0.9)'); gr.addColorStop(0.5, 'rgba(240,240,240,0.45)'); gr.addColorStop(1, 'rgba(230,230,230,0)'); g.fillStyle = gr; g.fillRect(0, 0, 128, 128); });
const PUFF = []; function addPuff(t0, p, r, life) { const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: puffTex, transparent: true, depthWrite: false, color: 0xf3f1ec })); s.visible = false; scene.add(s); PUFF.push({ s, t0, p, r, life }); }
// overlays for the explainers: rotor rings seen from above, path arrows, radio rings, the tower and its range, the tape
const ringA = new THREE.Mesh(new THREE.RingGeometry(ROTOR_R - 0.25, ROTOR_R, 64).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ color: 0xffd23a, transparent: true, opacity: 0.9, depthTest: false, toneMapped: false })),
  ringB = ringA.clone(); ringB.material = ringA.material.clone(); for (const r of [ringA, ringB]) { r.renderOrder = 22; r.visible = false; scene.add(r); }
function flatArrow(color) { const s = new THREE.Shape(); s.moveTo(-0.6, 0); s.lineTo(0.6, 0); s.lineTo(0.6, 6); s.lineTo(1.6, 6); s.lineTo(0, 9); s.lineTo(-1.6, 6); s.lineTo(-0.6, 6); s.closePath();
  const m = new THREE.Mesh(new THREE.ShapeGeometry(s).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.85, depthTest: false, toneMapped: false, side: THREE.DoubleSide })); m.renderOrder = 21; m.visible = false; scene.add(m); return m; }
const arrA = flatArrow(0x3ad2c8), arrB = flatArrow(0xff5a4a);
const ringTex = canvasTex(256, 256, g => { g.strokeStyle = 'rgba(120,220,255,1)'; g.lineWidth = 14; g.beginPath(); g.arc(128, 128, 110, 0, Math.PI * 2); g.stroke(); });
const RINGS = []; for (let i = 0; i < 8; i++) { const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: ringTex, transparent: true, depthTest: false, depthWrite: false, toneMapped: false })); s.renderOrder = 23; s.visible = false; scene.add(s); RINGS.push(s); }
const qTex = canvasTex(256, 256, g => { g.fillStyle = '#ffd23a'; g.beginPath(); g.arc(128, 128, 110, 0, Math.PI * 2); g.fill(); g.fillStyle = '#1a1a1a'; g.font = 'bold 190px Arial'; g.textAlign = 'center'; g.fillText('?', 128, 195); });
const QS = [0, 1].map(() => { const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: qTex, transparent: true, depthTest: false, toneMapped: false })); s.renderOrder = 24; s.visible = false; scene.add(s); return s; });
const TOWER = new THREE.Group(); { const z = 2600, x = valleyX(z) + 40; TOWER.position.set(x, 0, z); scene.add(TOWER);
  box(6, 26, 6, 0, 13, 0, mat(0xdedad2, 0.7), 0.3, TOWER); box(10, 5, 10, 0, 28, 0, glassM, 0.4, TOWER); box(11, 0.8, 11, 0, 31, 0, mat(0xb8b2a8, 0.6), 0.2, TOWER); }
const RANGE = new THREE.Mesh(new THREE.SphereGeometry(1900, 48, 24, 0, Math.PI * 2, 0, Math.PI / 2), new THREE.MeshBasicMaterial({ color: 0x46b4ff, transparent: true, opacity: 0.16, depthWrite: false, side: THREE.DoubleSide, toneMapped: false }));
RANGE.position.copy(TOWER.position); RANGE.visible = false; scene.add(RANGE);
const pin = new THREE.Sprite(new THREE.SpriteMaterial({ map: canvasTex(256, 256, g => { g.fillStyle = '#ff4a3a'; g.beginPath(); g.arc(128, 100, 80, Math.PI, 0); g.lineTo(128, 250); g.closePath(); g.fill(); g.fillStyle = '#fff'; g.beginPath(); g.arc(128, 100, 34, 0, Math.PI * 2); g.fill(); }), depthTest: false, toneMapped: false })); pin.renderOrder = 25; pin.visible = false; scene.add(pin);
const tape = new THREE.Mesh(new THREE.BoxGeometry(16, 0.08, 0.02), new THREE.MeshBasicMaterial({ color: 0xf2c21a, toneMapped: false })); tape.visible = false; scene.add(tape);
const tipTrail = new THREE.Mesh(new THREE.TorusGeometry(ROTOR_R - 0.1, 0.07, 6, 64, Math.PI * 0.9).rotateX(Math.PI / 2), new THREE.MeshBasicMaterial({ color: 0xffb020, transparent: true, opacity: 0.85, toneMapped: false, depthWrite: false })); tipTrail.visible = false; scene.add(tipTrail);
const pole = new THREE.Group(); box(0.12, 4.0, 0.12, 0, 2.0, 0, mat(0x7a5a3a, 0.9), 0, pole); const flagTop = box(0.6, 0.4, 0.04, 0.3, 3.8, 0, mat(0xff6a1a, 0.7), 0, pole); pole.visible = false; scene.add(pole);
// readout
const hudC = document.createElement('canvas'); hudC.width = 520; hudC.height = 440; const hudT = new THREE.CanvasTexture(hudC); hudT.colorSpace = THREE.SRGBColorSpace;
const hud = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: hudT, transparent: true, depthTest: false, depthWrite: false, toneMapped: false })); hud.renderOrder = 30; camera.add(hud); scene.add(camera); hud.visible = false;
function drawHud(rows, flag, fcol = '#d9241b') { const g = hudC.getContext('2d'); g.clearRect(0, 0, 520, 440); g.beginPath(); g.roundRect(6, 6, 508, 428, 34); g.fillStyle = 'rgba(8,14,22,0.74)'; g.fill(); g.lineWidth = 4; g.strokeStyle = 'rgba(160,200,235,0.55)'; g.stroke();
  let y = 30; for (const [lab, val, col] of rows) { g.fillStyle = '#9fb6c8'; g.font = '600 34px Arial, Helvetica, sans-serif'; g.fillText(lab, 34, y + 38); g.fillStyle = col || '#fff'; g.font = 'bold 62px Arial, Helvetica, sans-serif'; g.fillText(val, 34, y + 102, 452); y += 120; }
  if (flag) { g.font = 'bold 52px Arial, Helvetica, sans-serif'; const fw = Math.min(460, g.measureText(flag).width + 40); g.beginPath(); g.roundRect(30, 340, fw, 76, 16); g.fillStyle = fcol; g.fill(); g.fillStyle = '#fff'; g.fillText(flag, 50, 397, fw - 40); }
  hudT.needsUpdate = true; }
function fitHud() { const d = camera.near * 1.6, h = 2 * d * Math.tan(camera.fov * D2R / 2), w = h * camera.aspect, gw = 0.4 * w, gh = gw * 440 / 520; hud.scale.set(gw, gh, 1); hud.position.set(w / 2 - gw / 2 - 0.035 * w, h / 2 - 0.165 * h - gh / 2, -d); }
