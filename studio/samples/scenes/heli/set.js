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
    const rock = [0.3 + 0.12 * k, 0.26 + 0.1 * k, 0.23 + 0.08 * k], grass = [0.88 + 0.05 * k, 0.87 + 0.05 * k, 0.85 + 0.04 * k], snow = [0.9, 0.92, 0.96];
    let c = y < 40 ? grass : rock; if (ny > 0.62 + 0.15 * k) c = snow; if (y > 1700) c = ny > 0.5 ? snow : [0.45, 0.43, 0.42]; const cc = new THREE.Color().setRGB(c[0], c[1], c[2], THREE.SRGBColorSpace); col.push(cc.r, cc.g, cc.b); }
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  const t = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.95 })); t.receiveShadow = true; scene.add(t); }
// snow patches and stones scattered on the valley floor near the pad
for (let i = 0; i < 160; i++) { const x = (hash1(i * 3.1) - 0.5) * 220, z = (hash1(i * 7.3) - 0.5) * 300; if (Math.abs(x) < 16 && Math.abs(z) < 16) continue;
  if (Math.abs(x) < 60 && Math.abs(z) < 60) continue; const s = new THREE.Mesh(new THREE.CircleGeometry(0.6 + 1.6 * hash1(i), 14).rotateX(-Math.PI / 2), mat(0xf2f5fa, 0.9)); s.position.set(x, 0.32 + 0.002 * i, z); s.scale.z = 0.6 + 0.8 * hash1(i * 9); s.receiveShadow = true; scene.add(s); }
for (let i = 0; i < 120; i++) { const x = (hash1(i * 5.9) - 0.5) * 200, z = (hash1(i * 2.3) - 0.5) * 260; if (Math.abs(x) < 15 && Math.abs(z) < 15) continue;
  const r = new THREE.Mesh(new THREE.DodecahedronGeometry(0.3 + 0.9 * hash1(i * 4), 0), mat(0x6f6a66, 0.95)); r.position.set(x, 0.3, z); r.rotation.set(i, i * 2, i * 3); r.castShadow = true; scene.add(r); }
// the helipad: flat ground, a ring of white stones, a painted H
{ const pad = new THREE.Mesh(new THREE.CircleGeometry(11, 48).rotateX(-Math.PI / 2), mat(0xd6d2ca, 0.95)); pad.position.y = 0.31; pad.receiveShadow = true; scene.add(pad);
  for (let i = 0; i < 40; i++) { const a = i / 40 * Math.PI * 2, st = new THREE.Mesh(new THREE.DodecahedronGeometry(0.28, 0), mat(0xf4f4f0, 0.8)); st.position.set(Math.cos(a) * 11, 0.4, Math.sin(a) * 11); st.castShadow = true; scene.add(st); }
  const hm = mat(0xf4f4f0, 0.8); for (const [w, d, x, z] of [[0.9, 6, -1.8, 0], [0.9, 6, 1.8, 0], [2.7, 0.9, 0, 0]]) { const p = new THREE.Mesh(new THREE.BoxGeometry(w, 0.04, d), hm); p.position.set(x, 0.33, z); p.receiveShadow = true; scene.add(p); } }
// a windsock and a line of prayer flags between two poles
const sockM = mat(0xff6a1a, 0.7); box(0.1, 5, 0.1, 13, 2.8, -6, mat(0xcccccc, 0.5), 0); const sock = new THREE.Mesh(new THREE.ConeGeometry(0.35, 2.2, 14, 1, true).rotateZ(Math.PI / 2), sockM); sock.position.set(14.1, 5.1, -6); scene.add(sock);
const flags = [];
{ const a = V(-26, 4.5, 12), b = V(-15, 3.6, 20); box(0.12, 4.5, 0.12, a.x, 2.4, a.z, mat(0x7a5a3a, 0.9), 0); box(0.12, 3.6, 0.12, b.x, 1.9, b.z, mat(0x7a5a3a, 0.9), 0);
  const cols = [0x2a5bd7, 0xf4f4f0, 0xd62a2a, 0x2aa04a, 0xf2c21a]; for (let i = 0; i < 20; i++) { const u = (i + 0.5) / 20, p = a.clone().lerp(b, u); p.y -= 0.9 * Math.sin(Math.PI * u);
    const f = new THREE.Mesh(new THREE.PlaneGeometry(0.32, 0.38), new THREE.MeshStandardMaterial({ color: cols[i % 5], roughness: 0.8, side: THREE.DoubleSide })); f.position.copy(p).add(V(0, -0.2, 0)); f.lookAt(f.position.clone().add(V(-0.6, 0, 1))); scene.add(f); flags.push(f); }
  const rope = []; for (let i = 0; i <= 24; i++) { const u = i / 24, p = a.clone().lerp(b, u); p.y -= 0.9 * Math.sin(Math.PI * u); rope.push(p); }
  scene.add(new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(rope), 40, 0.015, 5), mat(0xd8d0c0, 0.9))); }
// stone lodges with coloured tin roofs (the village), along the east side of the floor
for (let i = 0; i < 14; i++) { const x = 34 + 22 * hash1(i * 1.7) + (i % 2) * 14, z = -70 + i * 11 + 4 * hash1(i * 3), w = 7 + 4 * hash1(i * 5), d = 5 + 3 * hash1(i * 8), h = 2.6 + 1.2 * hash1(i * 4);
  const L = new THREE.Group(); L.position.set(x, 0.3, z); L.rotation.y = 0.1 * (hash1(i) - 0.5); scene.add(L);
  box(w, h, d, 0, h / 2, 0, mat(new THREE.Color().setHSL(0.08, 0.08, 0.55 + 0.12 * hash1(i * 6)), 0.95), 0.05, L).castShadow = true;
  const roof = new THREE.Mesh(new THREE.CylinderGeometry(0.01, d * 0.62, w * 1.05, 4, 1).rotateZ(Math.PI / 2).rotateX(Math.PI / 4), mat([0x2b5fb3, 0x2f8a4a, 0xb53a2a, 0x2a7f9a][i % 4], 0.55, 0.35)); roof.scale.set(1, 0.42, 1); roof.position.y = h + d * 0.2; roof.castShadow = true; L.add(roof);
  for (let k = -1; k <= 1; k += 2) box(0.9, 0.9, 0.05, k * w * 0.25, h * 0.55, d / 2 + 0.02, mat(0x2a3440, 0.3), 0, L); }
// low stone walls (yak pens)
for (let i = 0; i < 6; i++) box(14, 0.9, 0.6, 30 + 8 * hash1(i), 0.75, -40 + i * 16, mat(0x7a756e, 0.95), 0.1).castShadow = true;
// ---- the helicopter: Airbus AS350 B3 / H125 at real size (fuselage 10.93 m nose to tail rotor, main rotor 10.69 m, 3 blades turning clockwise from above,
// tail rotor 1.86 m on the LEFT of the fin, rotor head 3.34 m up, skids 2.2 m apart). Root at the skid bottoms, nose to -z. No logos or names.
const glassM = new THREE.MeshStandardMaterial({ color: 0x24333f, roughness: 0.06, metalness: 0.5, transparent: true, opacity: 0.9 });
const bladeM = mat(0x26282c, 0.5, 0.3), darkM = mat(0x34373c, 0.6, 0.4), skidM = mat(0xa7adb5, 0.35, 0.75);
const ROTOR_Y = 3.15, ROTOR_R = 5.345;
// fuselage cross-sections (z, half width, bottom y, top y), measured off AS350 side and top views
const SECT = [[-2.62, 0.04, 1.28, 1.36], [-2.5, 0.42, 0.95, 1.72], [-2.3, 0.66, 0.8, 1.98], [-2.0, 0.82, 0.72, 2.16], [-1.6, 0.9, 0.68, 2.27], [-1.0, 0.935, 0.66, 2.33],
  [-0.2, 0.935, 0.66, 2.34], [0.6, 0.92, 0.68, 2.33], [1.2, 0.86, 0.76, 2.3], [1.7, 0.66, 0.98, 2.22], [2.15, 0.42, 1.28, 2.12], [2.6, 0.31, 1.45, 2.04]];
function loftHeli(paintM, lowM) { const NA = 36, P = [], cols = [], idxP = [], idxL = [], idxG = [];
  const pt = (s, a) => { const [z, hw, yb, yt] = s, c = Math.cos(a), sn = Math.sin(a), e = 2 / 2.7; return V(hw * Math.sign(c) * Math.abs(c) ** e, (yb + yt) / 2 + (yt - yb) / 2 * Math.sign(sn) * Math.abs(sn) ** e, z); };
  for (const s of SECT) for (let i = 0; i <= NA; i++) P.push(pt(s, i / NA * Math.PI * 2));
  for (let k = 0; k < SECT.length - 1; k++) for (let i = 0; i < NA; i++) { const a = k * (NA + 1) + i, b = a + 1, c = a + NA + 1, d = c + 1;
    const m = P[a].clone().add(P[b]).add(P[c]).add(P[d]).multiplyScalar(0.25);
    const ax = Math.abs(m.x), glass = (m.z < -1.05 && m.y > 0.9 && !(m.y > 2.2 && m.z > -1.6)) || (ax > 0.7 && m.y > 1.42 && m.y < 2.12 && ((m.z > -0.95 && m.z < -0.12) || (m.z > 0.05 && m.z < 1.05)));
    const low = !glass && m.y < 1.05 && m.z > -1.4;
    (glass ? idxG : low ? idxL : idxP).push(a, c, b, b, c, d); }
  const g = new THREE.BufferGeometry(); g.setFromPoints(P); const all = [...idxP, ...idxL, ...idxG]; g.setIndex(all);
  g.addGroup(0, idxP.length, 0); g.addGroup(idxP.length, idxL.length, 1); g.addGroup(idxP.length + idxL.length, idxG.length, 2); g.computeVertexNormals();
  const m = new THREE.Mesh(g, [paintM, lowM, glassM]); m.castShadow = true; return m; }
function makeHeli(bodyC, lowC, boomC) { const h = new THREE.Group(); scene.add(h); const bodyM = mat(bodyC, 0.32, 0.25), lowM = mat(lowC, 0.4, 0.25), boomM = mat(boomC, 0.35, 0.25), U = h.userData;
  const body = new THREE.Group(); h.add(body); U.body = body; U.win = new THREE.Object3D();
  body.add(loftHeli(bodyM, lowM));
  // door frames: thin dark lines between the side windows
  for (const s of [-1, 1]) for (const z of [-0.98, -0.03, 1.08]) box(0.03, 0.75, 0.05, s * 0.935, 1.78, z, darkM, 0, body);
  // engine and main gearbox fairing (the 'doghouse'), air intake grilles, exhaust on the right side
  const cowl = box(1.18, 0.5, 2.9, 0, 2.52, 0.75, bodyM, 0.22, body); cowl.castShadow = true;
  box(1.0, 0.32, 0.9, 0, 2.86, 0.2, bodyM, 0.15, body); for (const s of [-1, 1]) box(0.02, 0.22, 0.6, s * 0.6, 2.55, 0.9, darkM, 0, body);
  const ex = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.18, 0.5, 14).rotateZ(Math.PI / 2 - 0.4), darkM); ex.position.set(0.55, 2.55, 2.05); body.add(ex);
  // tail boom (tapered, slightly rising), horizontal stabiliser with end fins, the upper and lower fins, tail skid
  { const z0 = 2.5, z1 = 7.55, dz = z1 - z0, bm = new THREE.Mesh(new THREE.CylinderGeometry(0.15, 0.31, dz, 18).rotateX(Math.PI / 2), boomM); bm.position.set(0, 1.78, (z0 + z1) / 2); bm.rotation.x = -0.03; bm.castShadow = true; body.add(bm); }
  box(2.1, 0.06, 0.55, 0, 1.86, 6.15, boomM, 0.02, body); for (const s of [-1, 1]) box(0.05, 0.5, 0.42, s * 1.05, 1.9, 6.18, boomM, 0.02, body);
  { const sh = new THREE.Shape(); sh.moveTo(0, 0); sh.lineTo(0.75, 0); sh.lineTo(1.05, 1.25); sh.lineTo(0.62, 1.25); sh.closePath();
    const fin = new THREE.Mesh(new THREE.ExtrudeGeometry(sh, { depth: 0.08, bevelEnabled: false }).rotateY(-Math.PI / 2), boomM); fin.position.set(0.04, 1.86, 7.0); fin.castShadow = true; body.add(fin);
    const lo = new THREE.Shape(); lo.moveTo(0, 0); lo.lineTo(0.7, 0); lo.lineTo(0.85, -0.55); lo.lineTo(0.5, -0.55); lo.closePath();
    const vf = new THREE.Mesh(new THREE.ExtrudeGeometry(lo, { depth: 0.07, bevelEnabled: false }).rotateY(-Math.PI / 2), boomM); vf.position.set(0.035, 1.8, 7.0); body.add(vf);
    const ts = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 0.6, 6).rotateX(0.9), skidM); ts.position.set(0, 1.12, 7.65); body.add(ts); }
  // tail rotor: 2 blades, 1.86 m across, on the left side of the fin
  const trot = new THREE.Group(); trot.position.set(-0.16, 2.3, 7.72); body.add(trot); U.trot = trot; box(0.12, 0.12, 0.12, 0, 0, 0, darkM, 0.03, trot);
  for (let k = 0; k < 2; k++) { const b = box(0.03, 1.86, 0.15, -0.04, 0, 0, bladeM, 0, trot); b.rotation.x = k * Math.PI / 2; }
  // skids: two long tubes with upturned toes, two curved cross tubes up to the belly
  for (const s of [-1, 1]) { const pts = [V(s * 1.1, 0.42, -2.25), V(s * 1.1, 0.12, -1.95), V(s * 1.1, 0.04, -1.6), V(s * 1.1, 0.04, 1.35), V(s * 1.1, 0.07, 1.55)];
    const sk = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 24, 0.045, 8), skidM); sk.castShadow = true; h.add(sk);
    for (const z of [-0.95, 0.75]) { const ct = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3([V(s * 1.1, 0.04, z), V(s * 1.04, 0.45, z), V(s * 0.78, 0.72, z)]), 10, 0.05, 8), skidM); ct.castShadow = true; h.add(ct); } }
  for (const z of [-0.95, 0.75]) box(1.56, 0.08, 0.1, 0, 0.72, z, skidM, 0.03, h);
  // main rotor: mast, Starflex hub, three blades (clockwise from above), a faint blur disc
  const mast = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.12, 0.3, 12), darkM); mast.position.set(0, 3.02, 0); body.add(mast);
  const rot = new THREE.Group(); rot.position.set(0, ROTOR_Y, 0); body.add(rot); U.rot = rot;
  const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.36, 0.1, 3), darkM); rot.add(hub); box(0.14, 0.24, 0.14, 0, 0.12, 0, darkM, 0.04, rot); U.blades = [];
  for (let k = 0; k < 3; k++) { const arm = new THREE.Group(); arm.rotation.y = k * Math.PI * 2 / 3; rot.add(arm);
    box(0.4, 0.09, 0.2, 0.42, 0, 0, darkM, 0.03, arm); const b = box(ROTOR_R - 0.6, 0.045, 0.35, (ROTOR_R + 0.6) / 2, -0.02, 0, bladeM, 0, arm); b.castShadow = true;
    const cap = box(0.3, 0.047, 0.35, ROTOR_R - 0.15, -0.02, 0, mat(0xe8e8e8, 0.5), 0, arm); arm.userData.full = [b, cap];
    const stub = box(1.3, 0.045, 0.35, 1.25, -0.02, 0, bladeM, 0, arm); stub.visible = false; arm.userData.stub = stub; U.blades.push(arm); }
  const disc = new THREE.Mesh(new THREE.CircleGeometry(ROTOR_R, 64).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ color: 0x202428, transparent: true, opacity: 0.12, depthWrite: false })); disc.position.y = -0.02; rot.add(disc); U.disc = disc;
  return h; }
// paint from the webcam video: one red, one white with a blue lower band and blue tail boom. Which company flew which is not reported; red = cargo (A) is a guess.
const HA = makeHeli(0xc23a22, 0x3a2622, 0xc23a22), HB = makeHeli(0xe9ecef, 0x1c3f8f, 0x1c3f8f);    // A: cargo from Lukla; B: from base camp with two trekkers
// debris: rotor blade pieces, small body bits and window glass (no people are ever shown)
const bitM = [mat(0x2a2c30, 0.5, 0.3), mat(0xc23a22, 0.4), mat(0xe9ecef, 0.4), mat(0x1c3f8f, 0.4)], glassBitM = new THREE.MeshStandardMaterial({ color: 0xbfe4ff, roughness: 0.05, metalness: 0.2, transparent: true, opacity: 0.8 });
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
const arrA = flatArrow(0xff4a3a), arrB = flatArrow(0xe8eef4);
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
const pole = new THREE.Group(); box(0.14, 3.2, 0.14, 0, 1.6, 0, mat(0x7a5a3a, 0.9), 0, pole); pole.visible = false; scene.add(pole);
const poleTop = new THREE.Group(); box(0.14, 1.1, 0.14, 0, 0.55, 0, mat(0x7a5a3a, 0.9), 0, poleTop); const flagTop = box(0.6, 0.4, 0.04, 0.3, 0.9, 0, mat(0xff6a1a, 0.7), 0, poleTop); poleTop.visible = false; scene.add(poleTop);
const bladePiece = box(ROTOR_R - 1.9, 0.045, 0.35, 0, 0, 0, bladeM, 0); bladePiece.visible = false;
// readout
const hudC = document.createElement('canvas'); hudC.width = 520; hudC.height = 440; const hudT = new THREE.CanvasTexture(hudC); hudT.colorSpace = THREE.SRGBColorSpace;
const hud = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: hudT, transparent: true, depthTest: false, depthWrite: false, toneMapped: false })); hud.renderOrder = 30; camera.add(hud); scene.add(camera); hud.visible = false;
function drawHud(rows, flag, fcol = '#d9241b') { const g = hudC.getContext('2d'); g.clearRect(0, 0, 520, 440); g.beginPath(); g.roundRect(6, 6, 508, 428, 34); g.fillStyle = 'rgba(8,14,22,0.74)'; g.fill(); g.lineWidth = 4; g.strokeStyle = 'rgba(160,200,235,0.55)'; g.stroke();
  let y = 30; for (const [lab, val, col] of rows) { g.fillStyle = '#9fb6c8'; g.font = '600 34px Arial, Helvetica, sans-serif'; g.fillText(lab, 34, y + 38); g.fillStyle = col || '#fff'; g.font = 'bold 62px Arial, Helvetica, sans-serif'; g.fillText(val, 34, y + 102, 452); y += 120; }
  if (flag) { g.font = 'bold 52px Arial, Helvetica, sans-serif'; const fw = Math.min(460, g.measureText(flag).width + 40); g.beginPath(); g.roundRect(30, 340, fw, 76, 16); g.fillStyle = fcol; g.fill(); g.fillStyle = '#fff'; g.fillText(flag, 50, 397, fw - 40); }
  hudT.needsUpdate = true; }
function fitHud() { const d = camera.near * 1.6, h = 2 * d * Math.tan(camera.fov * D2R / 2), w = h * camera.aspect, gw = 0.4 * w, gh = gw * 440 / 520; hud.scale.set(gw, gh, 1); hud.position.set(w / 2 - gw / 2 - 0.035 * w, h / 2 - 0.165 * h - gh / 2, -d); }
