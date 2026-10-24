// The sculpted, skinned 3D guy: loads char/guy.{json,bin} (from char/character.py), builds the skeleton,
// skinned meshes and the face rig (eyes, lids, brows, jaw, teeth, tongue), and gives two ways to pose it:
//   G.aim(bone, worldDir, worldBendAxis)  - point a bone along a direction with a defined twist (used by the rig)
//   G.pose({bone: [rx, ry, rz] deg})       - local offsets, for tests
//   G.face({jaw, blink, brow, browIn, look:[x,y], fear})
// Face paint, per pixel, from each vertex's rest position (so it rides the skin through skinning): brows with hair strokes,
// upper lash line, red lips with a darker parting line.  Broad tones (beard shadow, flush) come in as vertex colours.
function facePaint(THREE, m, man) {
  m.vertexColors = true;
  const L = man.lips || [];
  const U = { uEyeR: { value: new THREE.Vector3(...man.eyes.R) }, uEyeL: { value: new THREE.Vector3(...man.eyes.L) }, uMouth: { value: new THREE.Vector2(man.mouthY, man.mouthZ ?? -0.097) },
    uLipC: { value: L.map(l => new THREE.Vector3(...l[0])) }, uLipR: { value: L.map(l => new THREE.Vector3(...l[1])) } };
  const N = L.length;
  m.onBeforeCompile = sh => {
    Object.assign(sh.uniforms, U);
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vRest;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvRest = position;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', `#include <common>
varying vec3 vRest; uniform vec3 uEyeR, uEyeL; uniform vec2 uMouth; uniform vec3 uLipC[${N}]; uniform vec3 uLipR[${N}];
float h21(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
float brow(vec3 p, vec3 e, float s){
  float u = (p.x - e.x) * s;
  float yb = e.y + 0.0165 + 0.0035 * cos(3.14159 * (u - 0.008) / 0.046) - 0.0012 * (1.0 - smoothstep(-0.018, -0.008, u));
  float th = clamp(0.0085 - 0.0055 * (u + 0.016) / 0.04, 0.003, 0.0085);
  float dy = p.y - yb;
  float edge = th * (0.42 + 0.08 * sin(u * 1500.0) + 0.05 * sin(u * 3700.0 + 1.0));
  float band = 1.0 - smoothstep(edge * 0.7, edge, abs(dy));
  float span = smoothstep(-0.019, -0.0145, u) * (1.0 - smoothstep(0.0205, 0.026, u));
  float a = mix(1.25, 0.12, smoothstep(-0.016, 0.012, u));          // hairs grow up at the inner end, outward along the tail
  float w = -sin(a) * u + cos(a) * dy;
  float lane = floor(w / 0.00055);
  float hair = (1.0 - smoothstep(0.0, 0.25, abs(fract(w / 0.00055) - 0.5) - 0.12)) * step(0.25, h21(vec2(lane, s)));
  return band * span * mix(0.55, 1.0, hair) * step(p.z, e.z - 0.004);
}
float lash(vec3 p, vec3 e, float s){
  float u = (p.x - e.x) * s; float uu = clamp(u / 0.0135, -1.6, 1.6);
  float cut = e.y + 0.0046 - 0.0066 * uu * uu + 0.0008 * uu;
  float r = length(p - e); float d = p.y - cut;
  float up = (1.0 - smoothstep(0.0002, 0.0011 + 0.0006 * clamp(uu, 0.0, 1.0), d)) * step(-0.0007, d);
  float lcut = e.y - 0.0056 + 0.0042 * uu * uu + 0.0008 * uu; float dl = lcut - p.y;
  float lo = 0.45 * (1.0 - smoothstep(0.0001, 0.0007, dl)) * step(-0.0005, dl);
  return max(up, lo) * (1.0 - smoothstep(0.0158, 0.0178, r)) * step(p.z, e.z);
}`).replace('#include <color_fragment>', `#include <color_fragment>
{
  vec3 p = vRest;
  float br = max(brow(p, uEyeR, 1.0), brow(p, uEyeL, -1.0));
  diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.16, 0.095, 0.06), br * 0.92);
  float ls = max(lash(p, uEyeR, 1.0), lash(p, uEyeL, -1.0));
  diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.05, 0.03, 0.03), ls * 0.95);
  float ld = 1.0;
  for (int i = 0; i < ${N}; i++) { vec3 q = (p - uLipC[i]) / uLipR[i]; ld = min(ld, (length(q) - 1.0) * min(uLipR[i].x, min(uLipR[i].y, uLipR[i].z))); }
  float lip = (1.0 - smoothstep(-0.0002, 0.0011, ld)) * step(p.z, uMouth.y + 0.009);
  diffuseColor.rgb = mix(diffuseColor.rgb, diffuseColor.rgb * vec3(0.8, 0.5, 0.5), lip * 0.9);
  float slit = exp(-pow((p.y - uMouth.x) / 0.0011, 2.0)) * (1.0 - smoothstep(0.02, 0.0235, abs(p.x))) * (1.0 - smoothstep(0.0, 0.0025, ld));
  diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.18, 0.06, 0.07), slit * 0.8);
}`);
  };
  m.customProgramCacheKey = () => 'facepaint' + N;
  return m;
}

export async function loadGuy(THREE, base, opts = {}) {
  const man = await (await fetch(base + '.json')).json();
  const bin = await (await fetch(base + '.bin')).arrayBuffer();
  const root = new THREE.Group();
  const bones = {}, list = [];
  for (const b of man.bones) {
    const bone = new THREE.Bone(); bone.name = b.name;
    const h = new THREE.Vector3(...b.head);
    const ph = b.parent ? new THREE.Vector3(...man.bones.find(x => x.name === b.parent).head) : new THREE.Vector3();
    bone.position.copy(h.clone().sub(ph));
    bone.userData = { head: h, tail: new THREE.Vector3(...b.tail), parent: b.parent };
    bones[b.name] = bone; list.push(bone);
  }
  for (const b of man.bones) (b.parent ? bones[b.parent] : root).add(bones[b.name]);
  root.updateMatrixWorld(true);
  const skeleton = new THREE.Skeleton(list);
  const M = opts.materials || {};
  const mat = {
    skin: M.skin || new THREE.MeshPhysicalMaterial({ color: 0xd99a7c, roughness: 0.55, sheen: 0.15, sheenColor: new THREE.Color(0xffb099) }),
    shirt: M.shirt || new THREE.MeshPhysicalMaterial({ color: 0x1fae9b, roughness: 0.85, sheen: 0.8, sheenRoughness: 0.6, sheenColor: new THREE.Color(0x77ffe6) }),
    jeans: M.jeans || new THREE.MeshStandardMaterial({ color: 0x4068bd, roughness: 0.9 }),
    shoe: M.shoe || new THREE.MeshStandardMaterial({ color: 0x3a2d31, roughness: 0.55 }),
    hair: M.hair || new THREE.MeshStandardMaterial({ color: 0x5b351f, roughness: 0.6 }),
    sole: M.sole || new THREE.MeshStandardMaterial({ color: 0xe8e2d6, roughness: 0.7 }),
  };
  const which = n => n.startsWith('skin') ? mat.skin : n === 'shirt' ? mat.shirt : n === 'jeans' ? mat.jeans : n.startsWith('shoe') ? mat.shoe : n.startsWith('sole') ? mat.sole : mat.hair;
  const meshes = {};
  for (const m of man.meshes) {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(bin, m.pos, m.nv * 3), 3));
    g.setIndex(new THREE.BufferAttribute(new Uint32Array(bin, m.idx, m.nf * 3), 1));
    g.setAttribute('skinIndex', new THREE.BufferAttribute(new Uint16Array(bin, m.si, m.nv * 4), 4));
    g.setAttribute('skinWeight', new THREE.BufferAttribute(new Float32Array(bin, m.sw, m.nv * 4), 4));
    if (m.col !== undefined) g.setAttribute('color', new THREE.BufferAttribute(new Uint8Array(bin, m.col, m.nv * 4), 4, true));
    g.computeVertexNormals();
    let mt = which(m.name);
    if (m.col !== undefined) { mt = facePaint(THREE, mt.clone(), man); mat.face = mt; }   // painted face: brows, lashes, lips
    const sm = new THREE.SkinnedMesh(g, mt);
    sm.castShadow = true; sm.receiveShadow = true; sm.frustumCulled = false;
    sm.bind(skeleton, new THREE.Matrix4());
    root.add(sm); meshes[m.name] = sm;
  }
  // ---------------- face rig (rigid parts riding on the head and jaw bones)
  const headB = bones.head, jawB = bones.jaw;
  const local = (bone, p) => new THREE.Vector3(...p).sub(bone.userData.head.clone().add(new THREE.Vector3()));   // rest is axis-aligned
  const toLocal = (bone, p) => { const w = new THREE.Vector3(...p); return bone.worldToLocal(w); };
  const eyeMat = new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.12, clearcoat: 1 });
  const irisMat = new THREE.MeshPhysicalMaterial({ color: 0x5a3a1c, roughness: 0.2, clearcoat: 1 });
  const pupMat = new THREE.MeshPhysicalMaterial({ color: 0x0b0608, roughness: 0.1, clearcoat: 1 });
  const dark = new THREE.MeshStandardMaterial({ color: 0x3d0b14, roughness: 0.8 });
  const teethM = new THREE.MeshStandardMaterial({ color: 0xf6f1e8, roughness: 0.35 });
  const tongueM = new THREE.MeshStandardMaterial({ color: 0xd9566a, roughness: 0.5 });
  const browM = new THREE.MeshStandardMaterial({ color: 0x3a2014, roughness: 0.8 });
  const R = man.eyeR, eyes = {}, lids = {}, brows = {};
  for (const S of ['R', 'L']) {
    const e = new THREE.Group(); e.position.copy(toLocal(headB, man.eyes[S])); headB.add(e);
    // real eye: 24 mm ball, 11.7 mm iris sitting just under a clear cornea bulge; lids are skin (lid bones)
    const ball = new THREE.Mesh(new THREE.SphereGeometry(R, 32, 24), eyeMat); e.add(ball);
    const iris = new THREE.Mesh(new THREE.SphereGeometry(R * 0.5, 24, 16), irisMat); iris.scale.set(1, 1, 0.3); iris.position.z = -R * 0.9; e.add(iris);
    const pup = new THREE.Mesh(new THREE.SphereGeometry(R * 0.2, 16, 12), pupMat); pup.scale.set(1, 1, 0.3); pup.position.z = -R * 0.955; e.add(pup);
    const cornea = new THREE.Mesh(new THREE.SphereGeometry(R * 0.55, 24, 16), new THREE.MeshPhysicalMaterial({ color: 0xffffff, transparent: true, opacity: 0.12, roughness: 0.02, clearcoat: 1 }));
    cornea.scale.set(1, 1, 0.45); cornea.position.z = -R * 0.93; e.add(cornea);
    for (const m of [ball, iris, pup, cornea]) m.castShadow = false;
    eyes[S] = { g: e, pup };
    // blink: a skin cap tucked inside the sculpted upper lid that slides down over the eye (shown only while blinking)
    const edge = Math.asin(0.0046 / (R * 1.18));
    const cap = new THREE.Mesh(new THREE.SphereGeometry(R * 1.18, 32, 12, Math.PI, Math.PI, 0.25, Math.PI / 2 - edge - 0.25), mat.skin);
    const lidG = new THREE.Group(); lidG.add(cap); lidG.position.copy(e.position); headB.add(lidG);
    const lr = R * 1.19, lp = [];
    for (let i = 0; i <= 16; i++) { const f = Math.PI + 0.45 + (Math.PI - 0.9) * i / 16; lp.push(new THREE.Vector3(-lr * Math.cos(f) * Math.cos(edge), lr * Math.sin(edge), lr * Math.sin(f) * Math.cos(edge))); }
    const lash = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(lp), 24, 0.0004, 4), new THREE.MeshStandardMaterial({ color: 0x1a1010, roughness: 0.9 }));
    lidG.add(lash);
    lids[S] = { g: lidG, cap, lash, edge };
    brows[S] = bones['brow' + S];
  }
  const my = man.mouthY, hc = man.headC;
  const mz = man.mouthZ ?? -0.092;
  const mouthIn = new THREE.Mesh(new THREE.SphereGeometry(0.021, 24, 16), dark); mouthIn.scale.set(1.1, 0.8, 1.0);
  mouthIn.position.copy(toLocal(headB, [0, my - 0.006, mz + 0.024])); headB.add(mouthIn);
  const teethU = new THREE.Mesh(new THREE.CapsuleGeometry(0.0055, 0.028, 4, 10), teethM); teethU.rotation.z = Math.PI / 2;
  teethU.position.copy(toLocal(headB, [0, my + 0.002, mz + 0.0085])); headB.add(teethU);
  const teethL = new THREE.Mesh(new THREE.CapsuleGeometry(0.005, 0.025, 4, 10), teethM); teethL.rotation.z = Math.PI / 2;
  teethL.position.copy(toLocal(jawB, [0, my - 0.006, mz + 0.011])); jawB.add(teethL);
  const tongue = new THREE.Mesh(new THREE.SphereGeometry(0.018, 16, 12), tongueM); tongue.scale.set(1.1, 0.45, 1.3);
  tongue.position.copy(toLocal(jawB, [0, my - 0.011, mz + 0.026])); jawB.add(tongue);
  root.updateMatrixWorld(true);

  // ---------------- posing
  const REST = {};
  for (const b of list) REST[b.name] = { pos: b.position.clone(), q: b.quaternion.clone(), axis: b.userData.tail.clone().sub(b.userData.head).normalize() };
  const F = new THREE.Vector3(0, 0, -1), U = new THREE.Vector3(0, 1, 0);
  const basis = (a, n) => { const x = n.clone().sub(a.clone().multiplyScalar(n.dot(a))).normalize(); const z = new THREE.Vector3().crossVectors(a, x); return new THREE.Matrix4().makeBasis(x, a, z); };
  const restNormal = name => {      // the bend axis each bone had in the rest pose (matches main.js hingeDir)
    const a = REST[name].axis; let n = new THREE.Vector3().crossVectors(a, F);
    if (n.lengthSq() < 1e-4) n.crossVectors(a, U); return n.normalize();
  };
  function reset() { for (const b of list) { b.position.copy(REST[b.name].pos); b.quaternion.copy(REST[b.name].q); } root.updateMatrixWorld(true); }
  function aim(name, dir, bend) {   // world direction + world bend axis -> local rotation
    const b = bones[name], a0 = REST[name].axis, n0 = restNormal(name);
    const R0 = basis(a0, n0), R1 = basis(dir.clone().normalize(), bend.clone().normalize());
    const qw = new THREE.Quaternion().setFromRotationMatrix(R1.multiply(R0.clone().invert()));
    const pq = new THREE.Quaternion(); if (b.parent && b.parent.isBone) b.parent.getWorldQuaternion(pq); else root.getWorldQuaternion(pq);
    b.quaternion.copy(pq.invert().multiply(qw)); b.updateMatrixWorld(true);
  }
  function setWorld(name, qw) {
    const b = bones[name], pq = new THREE.Quaternion();
    if (b.parent && b.parent.isBone) b.parent.getWorldQuaternion(pq); else root.getWorldQuaternion(pq);
    b.quaternion.copy(pq.invert().multiply(qw)); b.updateMatrixWorld(true);
  }
  function pose(p) {
    reset();
    for (const [k, e] of Object.entries(p)) if (bones[k]) bones[k].quaternion.multiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(e[0] * Math.PI / 180, e[1] * Math.PI / 180, e[2] * Math.PI / 180)));
    root.updateMatrixWorld(true);
  }
  function face(f = {}) {
    const jaw = f.jaw ?? 0, blink = f.blink ?? 0, brow = f.brow ?? 0, browIn = f.browIn ?? 0, look = f.look || [0, 0], fear = f.fear ?? 0;
    bones.jaw.quaternion.setFromAxisAngle(new THREE.Vector3(1, 0, 0), -jaw * 20 * Math.PI / 180);   // chin swings down and back
    tongue.visible = jaw > 0.2; teethU.visible = teethL.visible = mouthIn.visible = jaw > 0.04;
    for (const S of ['R', 'L']) {
      eyes[S].g.rotation.set(-look[1] * 0.35, look[0] * 0.45, 0);
      eyes[S].pup.scale.setScalar(1 - 0.35 * fear);
      // open lids sit above/below the iris; wide eyes (fear) pull them further back; blink closes them
      // eyelids only show when blinking: rotate the upper cap from tucked-back (open) to covering the front (shut)
      const L = lids[S], close = Math.min(1, blink + 0.25 * Math.max(0, -look[1]));
      L.g.rotation.x = -close * (L.edge + Math.asin(0.0056 / (R * 1.18)) + 0.06);
      L.cap.visible = L.lash.visible = close > 0.03;
      const sx = S === 'R' ? 1 : -1;
      brows[S].position.copy(REST['brow' + S].pos); brows[S].position.y += 0.004 * brow + 0.003 * fear - 0.0015 * browIn;
      brows[S].rotation.set(0, 0, sx * (0.1 * browIn + 0.12 * fear));   // inner ends up = worried; knit pulls them down
    }
  }
  face({});
  return { root, bones, skeleton, meshes, mat, aim, setWorld, pose, reset, face, man, REST, restNormal };
}
