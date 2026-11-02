// ------------------------------------------------------------------ the story: stand; each beat his right hand holds one prop
const YAW = 180;
const F = fwdOf(YAW), Rt = rightOf(YAW), UP = V(0, 1, 0);
// how the hand meets each prop: n = palm normal (palm -> prop), u = finger direction; the palm point is eased in until the skin touches
function aimFor(k) { const g = PROPS[k].g, c = wp(g);
  // base: how far along the fingers from the palm centre the prop's centre sits (a bar or can sits across the finger bases, where fingers can wrap it)
  if (k === 'bar') return { c, n: V(0, -0.94, 0.34).normalize(), u: V(0, 0.34, 0.94).normalize(), back: 0.016, base: 0.028 };   // overhand: palm down on top, fingers forward over it and under
  if (k === 'can') return { c, n: V(0.9, 0, 0.44).normalize(), u: V(-0.44, 0, 0.9).normalize(), back: 0.033, base: 0.03 };      // handshake hold: palm facing in, thumb up, fingers forward round it
  const q = g.quaternion; return { c, n: V(0, 0, -1).applyQuaternion(q), u: V(1, 0, 0).applyQuaternion(q), back: 0.0045, base: 0.012 };   // phone: resting in his palm, screen to his face (palm on the far side), fingers round the far long edge
}
function guyAt(t) { const b = beatAt(t), lt = t - B[b];
  const pose = addPose(STAND, { neck: [10, 0, 0], head: [8, 0, 0] }); return { b, lt, pose, root: { x: STANDP.x, y: 0.95, z: STANDP.z, yaw: YAW }, prop: ORDER[b], show: true, face: { look: [0, -0.4] } }; }
const CAM0 = { pos: V(-0.55, 1.35, 1.05), tgt: V(-0.15, 1.08, 0.3), fov: 36 };
function camAt(t, g) { return CAM0; }
