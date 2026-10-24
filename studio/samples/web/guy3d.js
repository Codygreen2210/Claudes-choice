// The sculpted, skinned 3D guy: loads char/guy.{json,bin} (from char/character.py), builds the skeleton,
// skinned meshes and the face rig (eyes, lids, brows, jaw, teeth, tongue), and gives two ways to pose it:
//   G.aim(bone, worldDir, worldBendAxis)  - point a bone along a direction with a defined twist (used by the rig)
//   G.pose({bone: [rx, ry, rz] deg})       - local offsets, for tests
//   G.face({jaw, blink, brow, browIn, look:[x,y], fear})
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
  };
  const which = n => n.startsWith('skin') ? mat.skin : n === 'shirt' ? mat.shirt : n === 'jeans' ? mat.jeans : n.startsWith('shoe') ? mat.shoe : mat.hair;
  const meshes = {};
  for (const m of man.meshes) {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(bin, m.pos, m.nv * 3), 3));
    g.setIndex(new THREE.BufferAttribute(new Uint32Array(bin, m.idx, m.nf * 3), 1));
    g.setAttribute('skinIndex', new THREE.BufferAttribute(new Uint16Array(bin, m.si, m.nv * 4), 4));
    g.setAttribute('skinWeight', new THREE.BufferAttribute(new Float32Array(bin, m.sw, m.nv * 4), 4));
    g.computeVertexNormals();
    const sm = new THREE.SkinnedMesh(g, which(m.name));
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
    const ball = new THREE.Mesh(new THREE.SphereGeometry(R, 32, 24), eyeMat); e.add(ball);
    const iris = new THREE.Mesh(new THREE.SphereGeometry(R * 0.52, 24, 16), irisMat); iris.scale.set(1, 1, 0.35); iris.position.z = -R * 0.86; e.add(iris);
    const pup = new THREE.Mesh(new THREE.SphereGeometry(R * 0.27, 16, 12), pupMat); pup.scale.set(1, 1, 0.3); pup.position.z = -R * 0.97; e.add(pup);
    for (const m of [ball, iris, pup]) m.castShadow = false;
    eyes[S] = { g: e, pup };
    // eyelids: skin shells hinged at the eye centre (upper closes down, lower closes up a little)
    const up = new THREE.Mesh(new THREE.SphereGeometry(R * 1.035, 32, 16, 0, Math.PI * 2, 0, Math.PI * 0.5), mat.skin);
    const lo = new THREE.Mesh(new THREE.SphereGeometry(R * 1.03, 32, 16, 0, Math.PI * 2, Math.PI * 0.68, Math.PI * 0.32), mat.skin);
    const lidU = new THREE.Group(), lidL = new THREE.Group(); lidU.add(up); lidL.add(lo);
    lidU.position.copy(e.position); lidL.position.copy(e.position); headB.add(lidU); headB.add(lidL);
    lids[S] = { up: lidU, lo: lidL };
    const bg = new THREE.Group(); const sxb = S === 'R' ? 1 : -1;
    for (const [dx, ang, len] of [[-0.011, 0.18, 0.024], [0.012, -0.22, 0.024]]) {
      const br = new THREE.Mesh(new THREE.CapsuleGeometry(0.0052, len, 4, 10), browM);
      br.rotation.z = Math.PI / 2 + sxb * ang; br.position.set(sxb * dx, 0.003 - Math.abs(dx) * 0.25, 0); br.scale.set(1, 1, 0.7); bg.add(br);
    }
    bg.position.copy(toLocal(headB, [man.eyes[S][0], man.eyes[S][1] + 0.04, man.eyes[S][2] - 0.022])); headB.add(bg);
    brows[S] = bg;
  }
  const my = man.mouthY, hc = man.headC;
  const mouthIn = new THREE.Mesh(new THREE.SphereGeometry(0.026, 24, 16), dark); mouthIn.scale.set(1.1, 0.8, 0.9);
  mouthIn.position.copy(toLocal(headB, [0, my - 0.008, -0.07])); headB.add(mouthIn);
  const teethU = new THREE.Mesh(new THREE.CapsuleGeometry(0.007, 0.036, 4, 10), teethM); teethU.rotation.z = Math.PI / 2;
  teethU.position.copy(toLocal(headB, [0, my + 0.001, -0.083])); headB.add(teethU);
  const teethL = new THREE.Mesh(new THREE.CapsuleGeometry(0.0065, 0.032, 4, 10), teethM); teethL.rotation.z = Math.PI / 2;
  teethL.position.copy(toLocal(jawB, [0, my - 0.008, -0.08])); jawB.add(teethL);
  const tongue = new THREE.Mesh(new THREE.SphereGeometry(0.022, 16, 12), tongueM); tongue.scale.set(1.1, 0.45, 1.3);
  tongue.position.copy(toLocal(jawB, [0, my - 0.014, -0.068])); jawB.add(tongue);
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
    tongue.visible = jaw > 0.2;
    for (const S of ['R', 'L']) {
      eyes[S].g.rotation.set(-look[1] * 0.35, look[0] * 0.45, 0);
      eyes[S].pup.scale.setScalar(1 - 0.35 * fear);
      // open lids sit above/below the iris; wide eyes (fear) pull them further back; blink closes them
      // eyelids only show when blinking: rotate the upper cap from tucked-back (open) to covering the front (shut)
      lids[S].up.rotation.x = 1.35 * (1 - blink) - 1.45 * blink; lids[S].up.visible = blink > 0.02;
      lids[S].lo.visible = blink > 0.5; lids[S].lo.rotation.x = 0.35 * (1 - blink);
      const sx = S === 'R' ? 1 : -1;
      brows[S].position.y = brows[S].userData.y0 + 0.005 * brow + 0.003 * fear;
      brows[S].rotation.z = sx * (0.1 * browIn + 0.12 * fear);        // inner ends up = worried
    }
  }
  for (const S of ['R', 'L']) brows[S].userData.y0 = brows[S].position.y;
  face({});
  return { root, bones, skeleton, meshes, mat, aim, setWorld, pose, reset, face, man, REST, restNormal };
}
