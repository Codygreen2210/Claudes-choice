// ------------------------------------------------------------------ the bench: three props in front of him, one shown per beat (all in his reach, right hand)
const STANDP = V(0, 0, 0);
const PROPS = {};
const barM = new THREE.MeshStandardMaterial({ color: 0x33363c, roughness: 0.35, metalness: 0.6 });
{ const g = new THREE.Group(); g.position.set(-0.12, 1.12, 0.36); scene.add(g);                  // a bar running across in front of him (axis x)
  const m = new THREE.Mesh(new THREE.CylinderGeometry(0.016, 0.016, 0.7, 24).rotateZ(Math.PI / 2), barM); m.castShadow = true; g.add(m);
  PROPS.bar = { g, shape: { type: 'cyl', r: 0.016, h: 0.7, axis: 'x' } }; }
{ const g = new THREE.Group(); g.position.set(-0.14, 1.06, 0.36); scene.add(g);                   // a drink can standing in the air in front of his right side (axis y)
  const m = new THREE.Mesh(new THREE.CylinderGeometry(0.033, 0.033, 0.122, 32), new THREE.MeshStandardMaterial({ color: 0xb02020, roughness: 0.3, metalness: 0.7 })); m.castShadow = true; g.add(m);
  PROPS.can = { g, shape: { type: 'cyl', r: 0.033, h: 0.122, axis: 'y' } }; }
{ const g = new THREE.Group(); g.position.set(-0.16, 1.12, 0.32); g.rotation.x = -0.35; scene.add(g);   // a phone held upright, screen toward him, tipped back a little
  box(0.072, 0.152, 0.009, 0, 0, 0, mat(0x1c1d22, 0.3, 0.6), 0.004, g);
  PROPS.phone = { g, shape: { type: 'box', min: [-0.036, -0.076, -0.0045], max: [0.036, 0.076, 0.0045] } }; }
const ORDER = ['bar', 'can', 'phone'];
