// ------------------------------------------------------------------ set: a generic steel hypercoaster in a park, afternoon (no park branding)
home.visible = false; lamp.visible = false;
scene.background = new THREE.Color(0x9cc7ef); scene.fog = new THREE.Fog(0xb9d4ea, 160, 900); scene.environmentIntensity = 0.5;
hemi.color.set(0xd6e8ff); hemi.groundColor.set(0x5a6b3a); hemi.intensity = 0.95; sun.color.set(0xffefd6); sun.intensity = 3.0;
{ const S = sun.shadow.camera; S.left = -10; S.right = 10; S.top = 10; S.bottom = -10; S.near = 1; S.far = 200; S.updateProjectionMatrix(); }
// sky dome with a soft gradient
{ const sk = new THREE.Mesh(new THREE.SphereGeometry(1500, 32, 16), new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false, fog: false, uniforms: { uSet: { value: 0 } },
    vertexShader: 'varying vec3 d; void main(){ d = normalize(position); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }',
    fragmentShader: `uniform float uSet; varying vec3 d; void main(){ float h = clamp(d.y, 0., 1.); vec3 day = mix(vec3(.75,.86,.96), vec3(.32,.56,.88), pow(h, .6)); vec3 dusk = mix(vec3(1.,.62,.38), vec3(.25,.22,.42), pow(h, .5));
      gl_FragColor = vec4(mix(day, dusk, uSet), 1.);
      #include <colorspace_fragment>
    }` })); sk.renderOrder = -10; scene.add(sk); window.__SKY = sk; }
const SKYU = window.__SKY.material.uniforms;
const groundM = new THREE.MeshStandardMaterial({ map: canvasTex(1024, 1024, g => { g.fillStyle = '#5f8a3e'; g.fillRect(0, 0, 1024, 1024); for (let i = 0; i < 20000; i++) { g.fillStyle = `rgba(${40 + 40 * Math.random()},${90 + 60 * Math.random()},${30 + 30 * Math.random()},0.35)`; g.fillRect(Math.random() * 1024, Math.random() * 1024, 2, 3); } }), roughness: 1 });
groundM.map.wrapS = groundM.map.wrapT = THREE.RepeatWrapping; groundM.map.repeat.set(60, 60);
const ground = new THREE.Mesh(new THREE.PlaneGeometry(3000, 3000).rotateX(-Math.PI / 2), groundM); ground.receiveShadow = true; scene.add(ground);
for (let i = 0; i < 140; i++) { const x = (hash1(i * 1.3) - 0.5) * 700, z = -300 + (hash1(i * 2.7) - 0.5) * 700; if (x > -320 && x < 20 && z > -70 && z < 115) continue;
  const tr = new THREE.Group(); tr.position.set(x, 0, z); scene.add(tr); const h = 6 + 8 * hash1(i * 5);
  const tk = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.4, h * 0.4, 8), mat(0x5b4030, 0.9)); tk.position.y = h * 0.2; tr.add(tk);
  const cr = new THREE.Mesh(new THREE.SphereGeometry(h * 0.32, 12, 10), mat(new THREE.Color().setHSL(0.27 + 0.05 * hash1(i), 0.45, 0.25 + 0.1 * hash1(i * 3)), 0.9)); cr.position.y = h * 0.62; cr.scale.y = 1.2; tr.add(cr); }
// the layout, after the real ride (B&M hyper, 2006): 200 ft lift, 170 ft first drop, camelback + 175 ft drop, banked turnaround, camelback,
// 540-degree helix, camelback, horseshoe, three small hills, banked turn back to the station (metres; out of the station heading -z)
const LAYOUT = [[0, 2.2, 30], [0, 2.2, 0], [0, 2.2, -25], [-8, 2.6, -40], [-22, 4, -46], [-35, 9, -46], [-80, 35, -46], [-125, 59, -46], [-136, 61.5, -46], [-145, 59, -46], [-158, 40, -46], [-168, 16, -46], [-178, 6, -46], [-192, 22, -46], [-205, 44, -46], [-215, 55.5, -46], [-223, 55.5, -46], [-233, 44, -46], [-246, 22, -46], [-258, 4, -46], [-280, 7, -40], [-296, 11, -22], [-294, 13, 0], [-276, 15, 12], [-258, 26, 12], [-243, 41, 12], [-233, 42.5, 12], [-223, 41, 12], [-208, 24, 12], [-192, 5, 12], [-176, 12, 13], [-150, 21, 14], [-142.35, 20.42, 15.52], [-135.86, 19.83, 19.86], [-131.52, 19.25, 26.35], [-130, 18.67, 34], [-131.52, 18.08, 41.65], [-135.86, 17.5, 48.14], [-142.35, 16.92, 52.48], [-150, 16.33, 54], [-157.65, 15.75, 52.48], [-164.14, 15.17, 48.14], [-168.48, 14.58, 41.65], [-170, 14, 34], [-168.48, 13.42, 26.35], [-164.14, 12.83, 19.86], [-157.65, 12.25, 15.52], [-150, 11.67, 14], [-142.35, 11.08, 15.52], [-135.86, 10.5, 19.86], [-131.52, 9.92, 26.35], [-130, 9.33, 34], [-131.52, 8.75, 41.65], [-135.86, 8.17, 48.14], [-142.35, 7.58, 52.48], [-150, 7, 54], [-172, 7, 54], [-182, 20, 54], [-192, 36, 54], [-200, 37.5, 54], [-208, 36, 54], [-218, 20, 54], [-232, 5, 54], [-250, 6, 60], [-260, 8, 76], [-252, 9, 92], [-234, 8, 96], [-222, 18, 96], [-212, 25.5, 96], [-202, 18, 96], [-190, 6, 96], [-178, 15, 96], [-168, 19.5, 96], [-158, 15, 96], [-146, 6, 96], [-134, 13, 96], [-124, 16.5, 96], [-114, 13, 96], [-100, 6, 96], [-70, 6, 96], [-40, 7, 92], [-18, 6, 82], [-5, 3.5, 68], [0, 2.4, 50], [0, 2.2, 40]].map(p => V(...p));
const CURVE = new THREE.CatmullRomCurve3(LAYOUT, false, 'centripetal', 0.5); const LEN = CURVE.getLength();
const frameAt = s => { const u = clamp(s / LEN, 0, 1), p = CURVE.getPointAt(u), t = CURVE.getTangentAt(u).normalize(); const r = new THREE.Vector3().crossVectors(t, V(0, 1, 0)).normalize(); const up = new THREE.Vector3().crossVectors(r, t).normalize(); return { p, t, r, up }; };
const sNear = (x, y, z) => { let best = 0, bd = 1e9; const q = V(x, y, z); for (let s = 0; s < LEN; s += 0.5) { const d = frameAt(s).p.distanceToSquared(q); if (d < bd) { bd = d; best = s; } } return best; };
// rails (two running rails), the box spine under them, ties; turquoise track on grey supports (2025 repaint)
const trackM = mat(0x2fb7b0, 0.45, 0.35), supM = mat(0x9ea3a8, 0.6, 0.3);
{ const N = 1400, L = [], Rr = [], Sp = []; for (let i = 0; i <= N; i++) { const f = frameAt(LEN * i / N); L.push(f.p.clone().addScaledVector(f.r, -0.62)); Rr.push(f.p.clone().addScaledVector(f.r, 0.62)); Sp.push(f.p.clone().addScaledVector(f.up, -0.55)); }
  for (const [pts, r] of [[L, 0.08], [Rr, 0.08], [Sp, 0.32]]) { const m = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), N, r, 10), trackM); m.castShadow = m.receiveShadow = true; scene.add(m); }
  for (let s = 0; s < LEN; s += 1.6) { const f = frameAt(s), tie = new THREE.Mesh(new THREE.BoxGeometry(1.35, 0.1, 0.12), trackM); tie.position.copy(f.p).addScaledVector(f.up, -0.2); tie.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(f.r, f.up, f.t.clone().negate())); scene.add(tie);
    const web = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.4, 0.08), trackM); web.position.copy(f.p).addScaledVector(f.up, -0.4); web.quaternion.copy(tie.quaternion); scene.add(web); }
  for (let s = 40; s < LEN - 4; s += 9) { const f = frameAt(s); if (f.p.y < 3) continue; const top = f.p.clone().addScaledVector(f.up, -0.85), h = top.y;
    const col = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.42, h, 12), supM); col.position.set(top.x, h / 2, top.z); col.castShadow = true; scene.add(col);
    if (h > 18) { const rh = V(f.r.x, 0, f.r.z).normalize(); for (const sd of [-1, 1]) {   // splayed legs out to the sides of the track (never along it)
      const base = top.clone().addScaledVector(rh, sd * h * 0.24).setY(0), dir = top.clone().sub(base), len = dir.length();
      const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.3, len, 10), supM); leg.position.copy(base).addScaledVector(dir, 0.5); leg.quaternion.setFromUnitVectors(V(0, 1, 0), dir.normalize()); leg.castShadow = true; scene.add(leg); } } } }
// the station: platform, roof, gate, check lights
const station = new THREE.Group(); scene.add(station);
{ box(3.2, 1.2, 26, -2.9, 0.6, 0, mat(0x8d8f93, 0.8), 0, station); box(3.2, 1.2, 26, 2.9, 0.6, 0, mat(0x8d8f93, 0.8), 0, station);
  box(10, 0.25, 28, 0, 6.5, 0, mat(0x2f4a6a, 0.6), 0, station); for (const [x, z] of [[-4.4, -13], [4.4, -13], [-4.4, 13], [4.4, 13]]) box(0.3, 6.4, 0.3, x, 3.2, z, mat(0xdedede, 0.5), 0, station);
  for (let i = 0; i < 9; i++) box(0.05, 0.9, 0.05, -1.45, 1.65, -9 + i * 2.1, mat(0x9aa0a6, 0.4, 0.6), 0, station); }
const lights = []; for (const x of [-1.5, 1.5]) { const l = new THREE.Mesh(new THREE.SphereGeometry(0.09, 16, 10), new THREE.MeshBasicMaterial({ color: 0x1c3a1c, toneMapped: false })); l.position.set(x * 2.4, 2.4, -11); station.add(l); lights.push(l); }
const closedSign = new THREE.Mesh(new THREE.PlaneGeometry(2.2, 0.8), new THREE.MeshBasicMaterial({ map: canvasTex(512, 180, g => { g.fillStyle = '#b3141a'; g.fillRect(0, 0, 512, 180); g.fillStyle = '#fff'; g.font = 'bold 120px Arial'; g.fillText('CLOSED', 40, 135); }), toneMapped: false }));
closedSign.position.set(-3.6, 1.9, 13.4); closedSign.visible = false; station.add(closedSign);
const tape = new THREE.Mesh(new THREE.BoxGeometry(14, 0.06, 0.02), new THREE.MeshBasicMaterial({ color: 0xf2c21a, toneMapped: false })); tape.visible = false; scene.add(tape);
// the train: 9 cars x 4 seats (36), floorless, padded clamshell lap bars; riders: two MakeHuman men in the front car, simple figures elsewhere
const CARL = 2.15, cars = [], bars = [], belts = [];
const seatM = mat(0x17707a, 0.6), carM = mat(0xe8702a, 0.45, 0.3), padM = mat(0x1a8790, 0.65), metM = mat(0xb7bcc3, 0.35, 0.8);   // orange and teal trains, teal seats and restraints
for (let c = 0; c < 9; c++) { const car = new THREE.Group(); scene.add(car); cars.push(car);
  box(4.2, 0.35, 1.7, 0, 0.3, 0, carM, 0.08, car); car.userData.wallL = box(0.12, 0.3, 1.6, -2.05, 0.55, 0, carM, 0.04, car); box(0.12, 0.3, 1.6, 2.05, 0.55, 0, carM, 0.04, car);   // open-sided cars, low fenders
  for (const x of [-1.2, 1.2]) for (const z of [-0.65, 0.65]) { const w = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.16, 0.12, 14).rotateZ(Math.PI / 2), metM); w.position.set(x * 0.5, -0.05, z); car.add(w); }
  const cb = []; for (let k = 0; k < 4; k++) { const x = -1.5 + k; box(0.82, 0.12, 0.62, x, 0.88, 0.12, seatM, 0.05, car); box(0.3, 0.4, 0.4, x, 0.64, 0.15, carM, 0.04, car); box(0.82, 1.05, 0.14, x, 1.43, 0.46, seatM, 0.06, car); box(0.82, 0.32, 0.2, x, 2.08, 0.45, seatM, 0.08, car);   // seat top at 0.94
    // the clamshell lap bar: hinged at the front of the seat, a padded block that comes down over the thighs
    // B&M-style lap bar: the post rises from the floor between the rider's shins and swings back; the pad (kept level) lands on the thighs
    const hinge = new THREE.Group(); hinge.position.set(x, 0.5, -0.55); car.add(hinge);
    box(0.08, 0.743, 0.07, 0, 0.371, 0, padM, 0.02, hinge); const tip = new THREE.Group(); tip.position.set(0, 0.743, 0); hinge.add(tip);
    const pad = box(0.62, 0.13, 0.34, 0, 0.0, 0.14, padM, 0.06, tip); pad.rotation.x = -0.1; pad.castShadow = true; hinge.userData.tip = tip;
    hinge.rotation.x = -0.35; cb.push(hinge);
    const belt = new THREE.Group(); belt.position.set(x, 0.0, 0.0); car.add(belt); box(0.05, 0.16, 0.025, 0, 1.03, -0.02, mat(0x222222, 0.6), 0.005, belt); box(0.08, 0.06, 0.04, 0, 1.08, -0.04, metM, 0.01, belt); belt.visible = false; belts.push(belt);
    if (c > 0 || k === 0 || k === 3) { const fig = new THREE.Group(); fig.position.set(x, 0.95, 0.15); car.add(fig); if (c === 0 && k === 0) car.userData.fig0 = fig; const col = new THREE.Color().setHSL(hash1(c * 7 + k), 0.55, 0.45);
      const torso = new THREE.Mesh(new THREE.CapsuleGeometry(0.17, 0.42, 6, 12), mat(col, 0.8)); torso.position.set(0, 0.48, 0.12); fig.add(torso);
      const head = new THREE.Mesh(new THREE.SphereGeometry(0.11, 16, 12), mat(new THREE.Color().setHSL(0.07, 0.4, 0.3 + 0.35 * hash1(c + k * 3)), 0.6)); head.position.set(0, 0.98, 0.1); fig.add(head);
      const legs = new THREE.Mesh(new THREE.CapsuleGeometry(0.11, 0.42, 6, 10), mat(0x2b3a55, 0.8)); legs.rotation.x = Math.PI / 2; legs.position.set(0, 0.12, -0.2); fig.add(legs); } }
  bars.push(cb); }
// the two MakeHuman riders (front car, seats 2 and 3); K's shirt colour changes when he is the ride worker (station beat)
const K = await loadGuy(THREE, '/char/' + (Q.get('char') || window.CHARDEF || 'guy'), { fingers3: !!window.FINGERS3 }); scene.add(K.root); K.root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
const RK = makeRig(K, 'rider2');
function shirt(Gx, c) { const m = Gx.meshes.shirt; if (!m) return; if (!m.userData.own) { m.material = m.material.clone(); m.material.map = null; m.userData.own = true; } m.material.color.set(c); }
shirt(G, 0x2f6fd0); shirt(K, 0x3a3f46);
// x-ray: the near rider goes glassy so the gap between him and the seat, and the bar on his thighs, show
const XRAYM = new THREE.MeshBasicMaterial({ color: 0x7fd3ff, transparent: true, opacity: 0.18, depthWrite: false, side: THREE.DoubleSide, blending: THREE.AdditiveBlending });
const XRSAVE = new Map(); let XRON = false;
function xray(on) { if (XRON === on) return; XRON = on; G.root.traverse(o => { if (!o.isMesh) return; if (on) { XRSAVE.set(o, o.material); o.material = XRAYM; o.castShadow = false; } else { o.material = XRSAVE.get(o) || o.material; o.castShadow = true; } }); }
// arrows (body floats up / seat drops away / the bar holds down) and a contact glow where the bar meets the thighs
function arrowMesh(color) { const s = new THREE.Shape(); s.moveTo(-0.05, -0.32); s.lineTo(0.05, -0.32); s.lineTo(0.05, 0.08); s.lineTo(0.13, 0.08); s.lineTo(0, 0.25); s.lineTo(-0.13, 0.08); s.lineTo(-0.05, 0.08); s.closePath();
  return new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth: 0.04, bevelEnabled: false }), new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.92, depthTest: false, toneMapped: false })); }
const upArrow = arrowMesh(0x3ad27a), downArrow = arrowMesh(0xffb020), barArrow = arrowMesh(0xff4a3a); for (const a of [upArrow, downArrow, barArrow]) { a.renderOrder = 25; a.visible = false; scene.add(a); }
const glow = new THREE.Sprite(new THREE.SpriteMaterial({ map: canvasTex(128, 128, g => { const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64); gr.addColorStop(0, 'rgba(255,90,60,1)'); gr.addColorStop(1, 'rgba(255,0,0,0)'); g.fillStyle = gr; g.fillRect(0, 0, 128, 128); }), transparent: true, depthTest: false, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false }));
glow.scale.set(0.5, 0.5, 1); glow.renderOrder = 24; glow.visible = false; scene.add(glow);
// the locking ratchet on the front car's seat 2 hinge (shown in the close-up): a toothed wheel and a pawl
const ratchet = new THREE.Group(); { const sh = new THREE.Shape(); const n = 14; for (let i = 0; i < n * 2; i++) { const a = i / (n * 2) * Math.PI * 2, r = i % 2 ? 0.07 : 0.095; i ? sh.lineTo(Math.cos(a) * r, Math.sin(a) * r) : sh.moveTo(Math.cos(a) * r, Math.sin(a) * r); } sh.closePath();
  const wheel = new THREE.Mesh(new THREE.ExtrudeGeometry(sh, { depth: 0.03, bevelEnabled: false }).rotateY(Math.PI / 2), mat(0xd9a52b, 0.35, 0.8)); ratchet.add(wheel);
  const pawl = new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.03, 0.16), mat(0xc0c5cc, 0.3, 0.85)); pawl.position.set(0.0, 0.11, -0.06); pawl.rotation.x = 0.5; ratchet.add(pawl); ratchet.userData.wheel = wheel; ratchet.userData.pawl = pawl; }
ratchet.position.set(-0.5 - 0.08, 0.5, -0.55); ratchet.visible = false;
// readout
const hudC = document.createElement('canvas'); hudC.width = 520; hudC.height = 440; const hudT = new THREE.CanvasTexture(hudC); hudT.colorSpace = THREE.SRGBColorSpace;
const hud = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: hudT, transparent: true, depthTest: false, depthWrite: false, toneMapped: false })); hud.renderOrder = 30; camera.add(hud); scene.add(camera); hud.visible = false;
function drawHud(rows, flag, fcol = '#d9241b') { const g = hudC.getContext('2d'); g.clearRect(0, 0, 520, 440); g.beginPath(); g.roundRect(6, 6, 508, 428, 34); g.fillStyle = 'rgba(8,14,22,0.74)'; g.fill(); g.lineWidth = 4; g.strokeStyle = 'rgba(160,200,235,0.55)'; g.stroke();
  let y = 30; for (const [lab, val, col] of rows) { g.fillStyle = '#9fb6c8'; g.font = '600 34px Arial, Helvetica, sans-serif'; g.fillText(lab, 34, y + 38); g.fillStyle = col || '#fff'; g.font = 'bold 62px Arial, Helvetica, sans-serif'; g.fillText(val, 34, y + 102, 452); y += 120; }
  if (flag) { g.font = 'bold 52px Arial, Helvetica, sans-serif'; const fw = Math.min(460, g.measureText(flag).width + 40); g.beginPath(); g.roundRect(30, 340, fw, 76, 16); g.fillStyle = fcol; g.fill(); g.fillStyle = '#fff'; g.fillText(flag, 50, 397, fw - 40); }
  hudT.needsUpdate = true; }
function fitHud() { const d = camera.near * 1.6, h = 2 * d * Math.tan(camera.fov * D2R / 2), w = h * camera.aspect, gw = 0.4 * w, gh = gw * 440 / 520; hud.scale.set(gw, gh, 1); hud.position.set(w / 2 - gw / 2 - 0.035 * w, h / 2 - 0.165 * h - gh / 2, -d); }
cars[0].add(ratchet);
