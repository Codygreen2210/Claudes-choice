// ------------------------------------------------------------------ x-ray: his body goes glassy; neck bones (C1-C7 and the top of the back), the spinal cord, nerve signals
const XRAYM = new THREE.MeshBasicMaterial({ color: 0x7fd3ff, transparent: true, opacity: 0.13, depthWrite: false, side: THREE.DoubleSide, blending: THREE.AdditiveBlending });
const XRSAVE = new Map(); let XRON = false;
const boneM = new THREE.MeshStandardMaterial({ color: 0xf1ead8, roughness: 0.45, emissive: 0x3a3428, emissiveIntensity: 0.6 });
const cordM = new THREE.MeshStandardMaterial({ color: 0xffd36a, roughness: 0.4, emissive: 0xffa21a, emissiveIntensity: 0.9 });
const SPINE = new THREE.Group(); scene.add(SPINE); SPINE.visible = false;
const VERTS = [];
function vertebra(s) { const g = new THREE.Group();
  const body = new THREE.Mesh(new THREE.CylinderGeometry(0.0115 * s, 0.012 * s, 0.013, 20), boneM); body.position.z = 0.012 * s; g.add(body);             // the round body in front
  const ring = new THREE.Mesh(new THREE.TorusGeometry(0.0095 * s, 0.0032 * s, 8, 24).rotateX(Math.PI / 2), boneM); ring.position.z = -0.006 * s; g.add(ring);   // the arch round the cord
  const spin = new THREE.Mesh(new THREE.ConeGeometry(0.004 * s, 0.022 * s, 8).rotateX(-Math.PI / 2 - 0.4), boneM); spin.position.set(0, -0.004, -0.022 * s); g.add(spin);  // the spike at the back
  for (const x of [-1, 1]) { const tp = new THREE.Mesh(new THREE.CapsuleGeometry(0.0028 * s, 0.012 * s, 4, 8).rotateZ(Math.PI / 2), boneM); tp.position.set(x * 0.017 * s, 0, -0.004 * s); g.add(tp); }   // side wings
  SPINE.add(g); return g; }
for (let i = 0; i < 11; i++) VERTS.push(vertebra(i < 7 ? 1.0 + i * 0.05 : 1.4 + (i - 7) * 0.06));   // C1..C7 then T1..T4 (bigger going down)
const skull = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 20), new THREE.MeshStandardMaterial({ color: 0xf1ead8, roughness: 0.5, transparent: true, opacity: 0.35, emissive: 0x3a3428, emissiveIntensity: 0.4, depthWrite: false }));
skull.scale.set(0.072, 0.085, 0.095); SPINE.add(skull);
const brainX = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 20), new THREE.MeshStandardMaterial({ color: 0xf0a6b4, emissive: 0x401018, emissiveIntensity: 0.6, roughness: 0.6 }));
{ const pa = brainX.geometry.attributes.position; for (let i = 0; i < pa.count; i++) { const x = pa.getX(i), y = pa.getY(i), z = pa.getZ(i), f = 1 + 0.04 * Math.sin(x * 23 + z * 17) * Math.sin(y * 19 + x * 7); pa.setXYZ(i, x * f, y * f, z * f); } brainX.geometry.computeVertexNormals(); }
brainX.scale.set(0.06, 0.05, 0.075); SPINE.add(brainX);
let cord = null; const pinchGlow = new THREE.Sprite(new THREE.SpriteMaterial({ map: canvasTex(128, 128, g => { const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64); gr.addColorStop(0, 'rgba(255,70,50,1)'); gr.addColorStop(0.45, 'rgba(255,40,30,0.45)'); gr.addColorStop(1, 'rgba(255,0,0,0)'); g.fillStyle = gr; g.fillRect(0, 0, 128, 128); }), transparent: true, depthWrite: false, depthTest: false, toneMapped: false, blending: THREE.AdditiveBlending }));
pinchGlow.renderOrder = 22; SPINE.add(pinchGlow);
// nerve signals: dots running out along paths (brain -> cord -> arms and legs)
const NSIG = 900; const sigG = new THREE.BufferGeometry(); const sigP = new Float32Array(NSIG * 3), sigC = new Float32Array(NSIG * 3);
sigG.setAttribute('position', new THREE.BufferAttribute(sigP, 3)); sigG.setAttribute('color', new THREE.BufferAttribute(sigC, 3));
const dotTex = canvasTex(64, 64, g => { const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.45, 'rgba(255,255,255,0.5)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); });
// the dots are tiny glowing beads (an instanced mesh: point sprites don't draw at size on this renderer)
const SIG = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1, 1), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, depthWrite: false, depthTest: false, blending: THREE.AdditiveBlending, toneMapped: false }), NSIG);
SIG.frustumCulled = false; SIG.renderOrder = 24; scene.add(SIG); SIG.visible = false; const _m4 = new THREE.Matrix4(), _c = new THREE.Color();
for (let i = 0; i < NSIG; i++) SIG.setColorAt(i, _c.setRGB(0, 0, 0));
const nerveM = new THREE.LineBasicMaterial({ color: 0xffc04a, transparent: true, opacity: 0.55, depthTest: false, blending: THREE.AdditiveBlending, toneMapped: false });
const NERVES = []; for (let i = 0; i < 5; i++) { const l = new THREE.Line(new THREE.BufferGeometry().setFromPoints(Array.from({ length: 40 }, () => V(0, 0, 0))), nerveM.clone()); l.renderOrder = 23; l.frustumCulled = false; scene.add(l); l.visible = false; NERVES.push(l); }
const XRSKIP = new Set([SPINE]);
function xray(on) { if (XRON === on) return; XRON = on; G.root.traverse(o => { if (!o.isMesh || XRSKIP.has(o)) return; if (on) { XRSAVE.set(o, o.material); o.material = XRAYM; o.castShadow = false; } else { o.material = XRSAVE.get(o) || o.material; o.castShadow = true; } }); SPINE.visible = on; }
// the neck curve: from the top of the chest to the base of the skull, bending the way his neck and head bones bend; a point a little behind it is the cord
function neckCurve() { const c = G.bones.chest, n = G.bones.neck, h = G.bones.head;
  const q0 = wq(c), qn = wq(n), qh = wq(h), up0 = V(0, 1, 0).applyQuaternion(qn), uph = V(0, 1, 0).applyQuaternion(qh);
  const p0 = wp(n).addScaledVector(V(0, 1, 0).applyQuaternion(q0), -0.075), p3 = wp(h).addScaledVector(uph, 0.01), L = p0.distanceTo(p3);
  const back = qq => FWD.clone().applyQuaternion(qq).multiplyScalar(-1);
  return { curve: new THREE.CubicBezierCurve3(p0, p0.clone().addScaledVector(up0, L * 0.4), p3.clone().addScaledVector(uph, -L * 0.4), p3), back0: back(qn), backh: back(qh), q0, qn, qh }; }
let FWD = V(0, 0, 1);   // his facing at rest (set from the eyes below)
{ G.reset(); G.root.updateMatrixWorld(true); const E = wp(G.bones.eyeR).add(wp(G.bones.eyeL)).multiplyScalar(0.5); FWD = E.sub(V(...G.man.headC)).setY(0).normalize(); }
const CORD = { pinch: 0, k: 0.55, swell: 0 };
function placeSpine() { const N = neckCurve(), cv = N.curve; const tmpQ = new THREE.Quaternion();
  const PTS = []; for (let i = 0; i <= 30; i++) { const u = i / 30, p = cv.getPoint(u), t = cv.getTangent(u).normalize(), b = N.back0.clone().lerp(N.backh, u).normalize(); PTS.push({ p, t, b }); }
  // C1 at the top (u = 1) down to C7 (u ~ 0.1), then T1..T4 below the curve along the chest
  for (let i = 0; i < 11; i++) { const v = VERTS[i]; let p, t, b;
    if (i < 7) { const u = 1 - (i + 0.5) / 7.3; p = cv.getPoint(u); t = cv.getTangent(u).normalize(); b = N.back0.clone().lerp(N.backh, u).normalize(); }
    else { const up = V(0, 1, 0).applyQuaternion(N.q0); p = cv.getPoint(0).addScaledVector(up, -0.024 * (i - 6)); t = up; b = FWD.clone().applyQuaternion(N.q0).multiplyScalar(-1); }
    const z = b.clone().multiplyScalar(-1); const x = new THREE.Vector3().crossVectors(t, z).normalize(); const zz = new THREE.Vector3().crossVectors(x, t);
    v.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(x, t, zz)); v.position.copy(p).addScaledVector(b, -0.006); }
  skull.position.copy(wp(G.bones.head)).add(V(0, 0.075, 0).applyQuaternion(N.qh)).addScaledVector(FWD.clone().applyQuaternion(N.qh), 0.015); skull.quaternion.copy(N.qh);
  brainX.position.copy(skull.position).add(V(0, 0.012, 0).applyQuaternion(N.qh)); brainX.quaternion.copy(N.qh);
  // the cord: through the arches, from the brain down past T4; squeezed at the pinch point
  const cp = [brainX.position.clone()]; for (let i = 0; i <= 30; i++) { const u = 1 - i / 30; cp.push(cv.getPoint(u).addScaledVector(N.back0.clone().lerp(N.backh, u).normalize(), 0.0)); }
  const up0 = V(0, 1, 0).applyQuaternion(N.q0); for (let k = 1; k <= 4; k++) cp.push(cv.getPoint(0).addScaledVector(up0, -0.024 * k));
  const curve = new THREE.CatmullRomCurve3(cp); if (cord) { SPINE.remove(cord); cord.geometry.dispose(); }
  const tg = new THREE.TubeGeometry(curve, 80, 0.0058, 10); const pa = tg.attributes.position, nb = 11;
  if (CORD.pinch > 0) for (let i = 0; i < pa.count; i++) { const seg = Math.floor(i / nb) / 80, d = Math.abs(seg - CORD.k), s = 1 - 0.6 * CORD.pinch * Math.exp(-(d * d) / 0.0012);   // squeeze the tube toward its own centre near the pinch
      const c = curve.getPoint(Math.min(1, Math.floor(i / nb) / 80)); pa.setXYZ(i, c.x + (pa.getX(i) - c.x) * s, c.y + (pa.getY(i) - c.y) * s, c.z + (pa.getZ(i) - c.z) * s); }
  if (CORD.swell > 0) for (let i = 0; i < pa.count; i++) { const seg = Math.floor(i / nb) / 80, d = Math.abs(seg - CORD.k), s = 1 + 1.3 * CORD.swell * Math.exp(-(d * d) / 0.004);
      const c = curve.getPoint(Math.min(1, seg)); pa.setXYZ(i, c.x + (pa.getX(i) - c.x) * s, c.y + (pa.getY(i) - c.y) * s, c.z + (pa.getZ(i) - c.z) * s); }
  const hurt = Math.max(CORD.pinch, CORD.swell);
  tg.computeVertexNormals(); cord = new THREE.Mesh(tg, cordM); cord.renderOrder = 21; SPINE.add(cord); cordM.emissive.setRGB(1, lerp(0.63, 0.15, hurt), lerp(0.1, 0.05, hurt));
  pinchGlow.position.copy(curve.getPoint(CORD.k)); pinchGlow.scale.setScalar(0.09 * hurt); pinchGlow.visible = hurt > 0.02;
  return { curve }; }
// signal paths for this frame: the cord, then out to each hand and foot
function nervePaths(curve) { const top = curve.getPoints(30), base = top[top.length - 1];
  const arm = S => [base, wp(G.bones['clav' + S]), wp(G.bones['uarm' + S]), wp(G.bones['farm' + S]), wp(G.bones['hand' + S]), R_tip(S)];
  const leg = S => [base, wp(G.bones.spine2), wp(G.bones.spine1), wp(G.bones.hips), wp(G.bones['thigh' + S]), wp(G.bones['shin' + S]), wp(G.bones['foot' + S])];
  return { cord: top, armR: arm('R'), armL: arm('L'), legR: leg('R'), legL: leg('L') }; }
const R_tip = S => RG.tip('middle', S);
// fill the dots: `alive(path, u)` says how bright a dot is at that point along that path (0 = no signal)
let SIGSCALE = 1;   // smaller beads in close-ups
function drawSignals(paths, t, alive) { let n = 0; const keys = ['cord', 'armR', 'armL', 'legR', 'legL'];
  keys.forEach((k, ki) => { const c = new THREE.CatmullRomCurve3(paths[k].map(p => p.clone()), false, 'centripetal'); const ln = NERVES[ki];
    const pts = c.getPoints(39); ln.geometry.setFromPoints(pts); ln.visible = true; ln.material.opacity = 0.18 + 0.4 * alive(k, 0.5);
    const per = k === 'cord' ? 14 : 22; for (let j = 0; j < per && n < NSIG; j++) { const u = ((j / per) + t * (k === 'cord' ? 0.55 : 0.45)) % 1, a = alive(k, u); const p = c.getPoint(u); if (a <= 0) continue;
      const sz = SIGSCALE * 0.017 * (0.5 + 0.5 * a); _m4.makeScale(sz, sz, sz).setPosition(p); SIG.setMatrixAt(n, _m4); SIG.setColorAt(n, a > 0.5 ? _c.setRGB(0.25 * a, 1.0 * a, 0.75 * a) : _c.setRGB(a, a * 0.75, a * 0.2)); n++; } });
  for (let i = n; i < NSIG; i++) { _m4.makeScale(0, 0, 0); SIG.setMatrixAt(i, _m4); } SIG.instanceMatrix.needsUpdate = true; SIG.instanceColor.needsUpdate = true; SIG.count = NSIG; SIG.visible = true; }

// ------------------------------------------------------------------ the backboard, the trainer, the medical cart
const board = new THREE.Group(); scene.add(board); board.visible = false;
{ const om = mat(0xf27a12, 0.5); box(0.42, 0.045, 1.85, 0, 0.0225, 0, om, 0.02, board);
  for (const z of [-0.78, -0.4, 0.05, 0.42, 0.75]) box(0.5, 0.016, 0.07, 0, 0.32, z, mat(0x111216, 0.8), 0.006, board);   // straps (raised to his body height below)
  for (const x of [-1, 1]) box(0.09, 0.12, 0.16, x * 0.15, 0.1, -0.83, mat(0xd8241c, 0.6), 0.02, board); }               // head blocks
const BSTRAPS = board.children.slice(1, 6);
const TR = await loadGuy(THREE, '/char/' + (Q.get('char') || window.CHARDEF || 'guy'), { fingers3: !!window.FINGERS3 }); scene.add(TR.root); TR.root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
for (const [n, c] of [['shirt', 0x15171c], ['jeans', 0x8a7a5c], ['shoeR', 0x1a1a1c], ['shoeL', 0x1a1a1c]]) { const m = TR.meshes[n]; if (!m) continue; m.material = m.material.clone(); m.material.map = null; m.material.color.set(c); m.material.needsUpdate = true; }
const RT = makeRig(TR, 'trainer'); TR.root.visible = false;
const cart = new THREE.Group(); scene.add(cart); cart.visible = false;
{ const wm = mat(0xeeeeea, 0.45, 0.05), dk = mat(0x1d1f24, 0.7);
  box(1.25, 0.32, 3.4, 0, 0.48, 0, wm, 0.06, cart); box(1.25, 0.9, 0.12, 0, 1.0, -0.95, dk, 0.03, cart);                // body, seat back (the flat deck behind it carries the board)
  box(1.1, 0.14, 0.5, 0, 0.72, -1.25, dk, 0.04, cart); box(1.3, 0.06, 0.9, 0, 2.0, -1.2, wm, 0.03, cart);               // seat, roof
  for (const x of [-0.6, 0.6]) box(0.05, 1.3, 0.05, x, 1.35, -1.6, dk, 0, cart);
  for (const [x, z] of [[-0.62, -1.15], [0.62, -1.15], [-0.62, 1.1], [0.62, 1.1]]) { const wh = new THREE.Mesh(new THREE.CylinderGeometry(0.24, 0.24, 0.18, 20).rotateZ(Math.PI / 2), dk); wh.position.set(x, 0.24, z); cart.add(wh); }
  box(0.5, 0.06, 0.06, 0, 1.0, -1.2, dk, 0, cart); }
const CARTDECK = 0.64;
// straps across him: each one laid over the top of his body at its spot on the board (from his capsules)
function strapsOn(Px) { board.updateMatrixWorld(true); const inv = board.matrixWorld.clone().invert(), cs = caps(Px).filter(c => c.part !== 'arm');
  for (const st of BSTRAPS) { let top = 0.12; for (const c of cs.filter(c => c.part === 'torso' || c.part === 'leg')) for (let k = 0; k <= 20; k++) { const p = c.a.clone().lerp(c.b, k / 20).applyMatrix4(inv); if (Math.abs(p.z - st.position.z) < 0.05 && Math.abs(p.x) < 0.25) top = Math.max(top, p.y + c.r); } st.position.y = top + 0.004; } }   // the flatbed top, where the board rides

// ------------------------------------------------------------------ poses (this rig: negative spine x bends forward)
function run(ph, lean = -12) { const s = Math.sin(ph), c = Math.cos(ph);
  return curl(curl({ spine1: [lean, 0, 0], chest: [-4, 0, 0], neck: [10, 0, 0], thighR: [24 + 46 * s, 0, 0], thighL: [24 - 46 * s, 0, 0],
    shinR: [-30 - 70 * Math.max(0, -s) - 15 * Math.max(0, c), 0, 0], shinL: [-30 - 70 * Math.max(0, s) - 15 * Math.max(0, -c), 0, 0], footR: [8 * s, 0, 0], footL: [-8 * s, 0, 0],
    armR: A(10 - 46 * s, 16, 0, 90), armL: A(10 + 46 * s, 16, 0, 90) }, 'R', 55), 'L', 55); }
const bob = ph => 0.93 + 0.035 * Math.abs(Math.cos(ph));
// Hockenson: the catch (hands up in front), then the ball tucked in his right arm
const CATCH = curl(curl({ spine1: [-8, 0, 0], neck: [6, 0, 0], thighR: [30, 0, 0], shinR: [-40, 0, 0], thighL: [5, 0, 0], shinL: [-25, 0, 0], armR: A(95, 18, 0, 35, 40), armL: A(95, 18, 0, 35, 40) }, 'R', 25), 'L', 25);
const carry = ph => { const p = run(ph, -16); p.armR = A(20, 12, 30, 112, 70); p.handR = [0, 0, 0]; return curl(p, 'R', 60); };
// the tackle: Campbell wraps high from the front and twists him down; O'Neill hits low from the side
const WRAP = curl(curl({ spine1: [-26, 0, 0], spine2: [-10, 0, 0], chest: [-6, 0, 0], neck: [18, 0, 0], head: [8, 0, 0], thighR: [55, 0, 0], shinR: [-60, 0, 0], thighL: [20, 0, 0], shinL: [-50, 0, 0],
  armR: A(85, 25, 10, 80, 20), armL: A(85, 25, 10, 80, 20) }, 'R', 45), 'L', 45);
const LOW = curl(curl({ spine1: [-30, 0, 0], spine2: [-14, 0, 0], chest: [-8, 0, 0], neck: [22, 0, 0], head: [10, 0, 0], thighR: [70, 0, 0], shinR: [-80, 0, 0], thighL: [35, 0, 0], shinL: [-70, 0, 0],
  armR: A(70, 30, 0, 60), armL: A(70, 30, 0, 60) }, 'R', 45), 'L', 45);
const HIT_H = curl(curl({ spine1: [10, 8, 0], chest: [6, 0, 0], neck: [-6, 0, 0], thighR: [20, 0, 0], shinR: [-35, 0, 0], thighL: [-5, 0, 0], shinL: [-20, 0, 0], armR: A(20, 12, 30, 112, 70), armL: A(40, 50, 0, 40) }, 'R', 60), 'L', 30);
// on the ground: Campbell face down and still (arms at his sides, head turned a little); Hockenson on his side; O'Neill getting up
const PRONE = curl(curl({ spine1: [2, 0, 0], neck: [10, 22, 0], head: [4, 20, 0], thighR: [4, 0, 4], shinR: [-14, 0, 0], thighL: [2, 0, -3], shinL: [-8, 0, 0], footR: [30, 0, 0], footL: [28, 0, 0],
  armR: A(-8, 16, 0, 20), armL: A(-8, 14, 0, 24) }, 'R', 25), 'L', 25);   // face down and still, arms at his sides
const SIDE = curl(curl({ spine1: [-10, 0, 6], thighR: [40, 0, 0], shinR: [-60, 0, 0], thighL: [20, 0, 0], shinL: [-40, 0, 0], armR: A(30, 12, 30, 100, 70), armL: A(40, 40, 0, 30) }, 'R', 50), 'L', 25);
const KNEEL = curl(curl({ spine1: [-8, 0, 0], neck: [26, 0, 0], head: [10, 0, 0], thighR: [85, 0, 0], shinR: [-88, 0, 0], footR: [0, 0, 0], thighL: [-6, 0, 0], shinL: [-100, 0, 0], footL: [-30, 0, 0],
  armR: A(28, 10, 0, 60), armL: A(10, 10, 0, 20) }, 'R', 30), 'L', 30);
const SUPINE = curl(curl({ neck: [0, 0, 0], head: [0, 0, 0], armR: A(-4, 8, 0, 8), armL: A(-4, 8, 0, 8), footR: [10, 0, 0], footL: [10, 0, 0] }, 'R', 18), 'L', 18);
const READY = curl(curl({ spine1: [-14, 0, 0], neck: [16, 0, 0], thighR: [32, 0, 6], shinR: [-48, 0, 0], thighL: [32, 0, -6], shinL: [-48, 0, 0], footR: [14, 0, 0], footL: [14, 0, 0], armR: A(30, 22, 0, 70), armL: A(30, 22, 0, 70) }, 'R', 40), 'L', 40);
// the hit, from the game photos: Hockenson bent over the ball; Campbell low at his right hip from the front, back flat, head up and turned, legs driving back;
// O'Neill low at his left hip from the side. (Root tilt pitches the whole body; positive thigh brings a leg forward.)
const H_HIT = curl(curl({ spine1: [-28, 4, 0], spine2: [-14, 0, 0], chest: [-8, 0, 0], neck: [10, 0, 0], head: [-12, 0, 0], thighR: [22, 0, 4], shinR: [-55, 0, 0], footR: [6, 0, 0], thighL: [46, 0, -4], shinL: [-52, 0, 0], footL: [-4, 0, 0],
  armR: A(40, 10, 30, 120, 60), armL: A(-28, 40, 0, 55) }, 'R', 60), 'L', 40);   // used with the root pitched 24 deg forward: bent low over the two of them
const H_FALL = curl(curl({ spine1: [-30, 6, 0], spine2: [-14, 0, 0], chest: [-8, 0, 0], neck: [16, 0, 0], head: [0, 0, 0], thighR: [10, 0, 6], shinR: [-25, 0, 0], footR: [30, 0, 0], thighL: [24, 0, -6], shinL: [-35, 0, 0], footL: [30, 0, 0],
  armR: A(40, 10, 30, 120, 60), armL: A(-20, 45, 0, 50) }, 'R', 60), 'L', 30);
// Campbell (body flat, head pressed into his left hip, near knee almost down, far leg driving back)
const C_HIT = curl(curl({ spine1: [-6, 0, 0], spine2: [-6, 0, 0], chest: [-4, 0, 0], neck: [22, -8, 0], head: [8, -12, 0], thighR: [52, 0, 8], shinR: [-48, 0, 0], footR: [24, 0, 0], thighL: [30, 0, -4], shinL: [-34, 0, 0], footL: [30, 0, 0],
  armR: A(80, 20, 0, 70), armL: A(80, 30, 0, 70) }, 'R', 50), 'L', 50);
const C_FALL = curl(curl({ spine1: [-2, 0, 0], spine2: [-2, 0, 0], neck: [8, -16, 0], head: [4, -18, 0], thighR: [20, 0, 6], shinR: [-40, 0, 0], footR: [35, 0, 0], thighL: [4, 0, -4], shinL: [-25, 0, 0], footL: [35, 0, 0],
  armR: A(-8, 16, 0, 20), armL: A(-8, 14, 0, 24) }, 'R', 25), 'L', 25);   // he lands face first, arms limp at his sides
// O'Neill (leaning in high, head at his right shoulder, wide driving legs)
const O_HIT = curl(curl({ spine1: [-12, 0, 0], spine2: [-8, 0, 0], chest: [-4, 0, 0], neck: [24, 0, 0], head: [6, 12, 0], thighR: [52, 0, 8], shinR: [-62, 0, 0], footR: [6, 0, 0], thighL: [-12, 0, -8], shinL: [-30, 0, 0], footL: [28, 0, 0],
  armR: A(75, 25, 0, 75), armL: A(75, 25, 0, 75) }, 'R', 50), 'L', 50);
const O_DOWN = curl(curl({ spine1: [-20, 0, 0], spine2: [-8, 0, 0], neck: [24, 0, 0], head: [8, 0, 0], thighR: [70, 0, 6], shinR: [-120, 0, 0], footR: [-20, 0, 0], thighL: [60, 0, -6], shinL: [-120, 0, 0], footL: [-20, 0, 0],
  armR: A(-15, 35, 0, 40), armL: A(-15, 35, 0, 40) }, 'R', 30), 'L', 30);   // lets go: arms back at his sides
const HIPS = { ...STAND, armR: A(10, 35, 40, 100), armL: A(10, 35, 40, 100) };
// ------------------------------------------------------------------ body capsules (with the pads and the helmet): the clip check, the ground, and the contact solve
function segDist(p1, q1, p2, q2) { const d1 = q1.clone().sub(p1), d2 = q2.clone().sub(p2), r = p1.clone().sub(p2), a = d1.dot(d1), e = d2.dot(d2), f = d2.dot(r);
  let s_, t_; if (a < 1e-9 && e < 1e-9) { s_ = t_ = 0; } else if (a < 1e-9) { s_ = 0; t_ = clamp(f / e, 0, 1); } else { const c = d1.dot(r); if (e < 1e-9) { t_ = 0; s_ = clamp(-c / a, 0, 1); } else { const b = d1.dot(d2), den = a * e - b * b;
    s_ = den > 1e-9 ? clamp((b * f - c * e) / den, 0, 1) : 0; t_ = (b * s_ + f) / e; if (t_ < 0) { t_ = 0; s_ = clamp(-c / a, 0, 1); } else if (t_ > 1) { t_ = 1; s_ = clamp((b - c) / a, 0, 1); } } }
  const c1 = p1.clone().addScaledVector(d1, s_), c2 = p2.clone().addScaledVector(d2, t_); return { d: c1.distanceTo(c2), c1, c2 }; }
function caps(Px) { const Gx = Px.G, b = n => wp(Gx.bones[n]);
  const N = b('neck'), C = b('chest'), S = b('spine1'), Hp = b('hips'), lat = b('uarmR').sub(b('uarmL')).normalize(), latH = b('thighR').sub(b('thighL')).normalize(), out = [];
  const cap = (a, c, r, part) => out.push({ a, b: c, r, part });
  for (const s of [-1, 1]) { cap(N.clone().lerp(C, 0.3).addScaledVector(lat, s * 0.085), S.clone().addScaledVector(lat, s * 0.075), 0.13, 'torso'); cap(S.clone().addScaledVector(lat, s * 0.07), Hp.clone().addScaledVector(latH, s * 0.065), 0.12, 'torso'); }
  for (const S_ of ['R', 'L']) { const u = b('uarm' + S_); cap(u, u, 0.095, 'pad'); }
  const hc = wp(Px.helmet), hf = V(0, 0, 1).applyQuaternion(wq(Px.helmet)); cap(hc, hc.clone().addScaledVector(hf, 0.04), 0.15, 'helmet');   // the shell and the facemask out front cap(N, b('head'), 0.06, 'neck');
  for (const S_ of ['R', 'L']) { cap(b('thigh' + S_).addScaledVector(latH, 0), b('shin' + S_), 0.08, 'leg'); cap(b('shin' + S_), b('foot' + S_), 0.055, 'leg'); cap(b('foot' + S_), Gx.tailW('foot' + S_), 0.045, 'foot');
    const ap = Px === HOCK && S_ === 'R' ? 'barm' : 'arm';   // his ball arm is locked to his chest: the body push treats it as body
    cap(b('uarm' + S_), b('farm' + S_), 0.052, ap); cap(b('farm' + S_), b('hand' + S_), 0.042, ap); cap(b('hand' + S_), Gx.tailW('middle2' + S_), 0.032, ap); }
  return out; }
const ARMP = new Set(['arm']);
// the deepest overlap between two players' capsules (arms left out with skipArms: arms are fixed by the hand solve, not by moving the body)
function overlap(A, B, skipArms = true) { const ca = caps(A), cb = caps(B); let best = { depth: 0 };
  for (const x of ca) { if (skipArms && ARMP.has(x.part)) continue; for (const y of cb) { if (skipArms && ARMP.has(y.part)) continue;
    const r = segDist(x.a, x.b, y.a, y.b), dep = x.r + y.r - r.d; if (dep > best.depth) best = { depth: dep, n: r.c1.clone().sub(r.c2).normalize(), x: x.part, y: y.part }; } }
  return best; }
// every overlap deeper than tol, arms included: the report the rig check reads
function clipList(list, tol = 0.006) { const out = [];
  for (let i = 0; i < list.length; i++) for (let j = i + 1; j < list.length; j++) { const A = list[i], B = list[j]; if (!A.G.root.visible || !B.G.root.visible) continue; const ca = caps(A), cb = caps(B);
    for (const x of ca) for (const y of cb) { const r = segDist(x.a, x.b, y.a, y.b), dep = x.r + y.r - r.d; if (dep > tol) out.push(`${A.number}:${x.part} in ${B.number}:${y.part} ${(dep * 100).toFixed(1)}cm`); } }
  for (const P of list) { if (!P.G.root.visible) continue; const cs = caps(P);   // his own arms through his own helmet or pads, his helmet into his own pads (head down)
    const hel = cs.find(c => c.part === 'helmet'); cs.filter(c => c.part === 'arm' || c.part === 'barm').forEach((x, j) => { const a0 = j % 3 === 0 ? x.a.clone().lerp(x.b, 0.3) : x.a;   // the top of the upper arm sits by the helmet at the shoulder: test from 30% down
      const r = segDist(a0, x.b, hel.a, hel.b); if (x.r + hel.r - r.d > 0.02) out.push(`${P.number}: arm in own helmet`); });
    const g = lowestOf(P); if (g < -0.008) out.push(`${P.number}: under the turf ${(g * 100).toFixed(1)}cm`);
    if (g > 0.25 && !P.airOK) out.push(`${P.number}: floating ${(g * 100).toFixed(0)}cm off the turf`); }   // a body pushed into the air (a bad separation) is as wrong as a clip
  return out; }
function lowestOf(Px) { let lo = 1e9; for (const c of caps(Px)) lo = Math.min(lo, Math.min(c.a.y, c.b.y) - c.r); return lo; }
const lowest = lowestOf;
// the hand solve pays for an arm inside someone else's body (their torso, pads, helmet, legs)
const OTHERS = new Map();
function armCost(R_) { return () => f => { const others = OTHERS.get(R_) || []; if (!others.length) return 0; let c = 0;
  const pts = []; for (let k = 0; k <= 3; k++) pts.push([f.sh.clone().lerp(f.el, k / 3), 0.05]); for (let k = 1; k <= 3; k++) pts.push([f.el.clone().lerp(f.p, k / 3), 0.042]);
  for (const [p, r] of pts) for (const y of others) { const d = segDist(p, p, y.a, y.b).d - (r + y.r); if (d < 0.004) c += ((d - 0.004) / 0.002) ** 2; }   // keep 4 mm clear; 1 cm in costs ~40 a point
  return c; }; }
