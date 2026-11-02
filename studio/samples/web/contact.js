// contact.js - does a hand really touch / hold a prop, without going into it? Judged on his SKINNED hand mesh (the skin you see),
// not on bone points: bone points passed while the skin was 1-2 cm inside a phone and a grab bar (2026-11-01).
//
//   import { makeContact } from '/contact.js';
//   const CT = makeContact(THREE, G);                         // G = the loaded character (loadGuy)
//   CT.prop('bar R', barMesh, { type: 'cyl', r: 0.016, h: 0.46, axis: 'z' });   // shapes in the object's own frame, in metres
//   CT.prop('pad L', padGroup, { type: 'box', min: [-0.05, -0.04, -0.2], max: [0.05, 0, 0.2] });
//   ... each frame (after the pose is final):  const c = CT.report([{ S: 'R', prop: 'bar R', mode: 'hold' }, { S: 'L', prop: 'pad L', mode: 'rest' }]);
//   ... return it from rigReport as `contacts: c` and jointjerk judges it.
//
// mode 'hold': skin must not go in (CLIP), something must touch (else FLOATING), and the touches must WRAP the prop:
//              at least 3 hand parts touching and contact directions spread over 120 degrees round it (else LOOSE: resting on it, not holding it).
// mode 'rest': must touch, must not go in.   mode 'none' (or a prop with no hold listed): must not go in, that's all.
// Shapes: box {min, max} | cyl {r, h, axis 'x'|'y'|'z'} (centred) | sphere {r}.  The object's world scale is applied.
export function makeContact(THREE, G, opts = {}) {
  const TOUCH = opts.touch ?? 0.003, IN = opts.in ?? 0.0008, FLOAT = opts.float ?? 0.006;
  const m = G.meshes.skin_head, ga = m.geometry.attributes, names = m.skeleton.bones.map(b => b.name);
  const PART = n => { const r = n.match(/^(hand|thumb|index|middle|ring|pinky)\d?([RL])$/); return r ? [r[2], r[1] === 'hand' ? 'palm' : r[1]] : null; };
  const HAND = { R: [], L: [] };                                     // [vertex index, part]
  for (let i = 0; i < ga.position.count; i++) { let bw = -1, bi = 0; for (let k = 0; k < 4; k++) { const w = ga.skinWeight.getComponent(i, k); if (w > bw) { bw = w; bi = ga.skinIndex.getComponent(i, k); } }
    const p = PART(names[bi]); if (p) HAND[p[0]].push([i, p[1]]); }
  const PROPS = {};
  const _v = new THREE.Vector3(), _s = new THREE.Vector3(), _q = new THREE.Quaternion(), _t = new THREE.Vector3(), _inv = new THREE.Matrix4();
  function prop(name, obj, shape) { PROPS[name] = { obj, shape }; }
  function handWorld(S) { const out = new Float32Array(HAND[S].length * 3);
    HAND[S].forEach(([i], k) => { _v.set(ga.position.getX(i), ga.position.getY(i), ga.position.getZ(i)); m.applyBoneTransform(i, _v); _v.applyMatrix4(m.matrixWorld); out[k * 3] = _v.x; out[k * 3 + 1] = _v.y; out[k * 3 + 2] = _v.z; });
    return out; }
  // signed distance (m) from a point in the prop's metric local frame, and the outward direction there
  function sdf(sh, p) {
    if (sh.type === 'sphere') { const L = p.length(); return [L - sh.r, L > 1e-9 ? p.clone().divideScalar(L) : new THREE.Vector3(0, 1, 0)]; }
    if (sh.type === 'cyl') { const ax = sh.axis || 'y', a = p[ax], perp = p.clone(); perp[ax] = 0; const rr = perp.length(), dr = rr - sh.r, da = Math.abs(a) - sh.h / 2;
      if (dr > 0 && da > 0) { const n = perp.clone().normalize().multiplyScalar(dr); n[ax] = Math.sign(a) * da; const L = n.length(); return [L, n.divideScalar(L)]; }
      if (dr > da) return [dr, rr > 1e-9 ? perp.divideScalar(rr) : new THREE.Vector3(1, 0, 0)];
      const n = new THREE.Vector3(); n[ax] = Math.sign(a) || 1; return [da, n]; }
    const mn = new THREE.Vector3(...sh.min), mx = new THREE.Vector3(...sh.max), c = mn.clone().add(mx).multiplyScalar(0.5), h = mx.clone().sub(mn).multiplyScalar(0.5);
    const d = p.clone().sub(c), q = new THREE.Vector3(Math.abs(d.x) - h.x, Math.abs(d.y) - h.y, Math.abs(d.z) - h.z);
    const o = new THREE.Vector3(Math.max(q.x, 0), Math.max(q.y, 0), Math.max(q.z, 0)), oL = o.length();
    if (oL > 0) return [oL, new THREE.Vector3(o.x * Math.sign(d.x), o.y * Math.sign(d.y), o.z * Math.sign(d.z)).divideScalar(oL)];
    const k = q.x > q.y ? (q.x > q.z ? 'x' : 'z') : (q.y > q.z ? 'y' : 'z'), n = new THREE.Vector3(); n[k] = Math.sign(d[k]) || 1; return [Math.max(q.x, q.y, q.z), n]; }
  // one hand against one prop: per-part nearest gap, skin points inside, contact directions (world)
  function probe(S, name, shift = 0, P = null) { const pr = PROPS[name]; if (!pr || !pr.obj.visible) return null;
    pr.obj.updateWorldMatrix(true, false); pr.obj.matrixWorld.decompose(_t, _q, _s); _inv.copy(pr.obj.matrixWorld).invert();
    P = P || handWorld(S); const gaps = {}, dirs = []; let nIn = 0, worst = 0; const cen = new THREE.Vector3(); let nc = 0;
    // shift (self-test): pretend the prop sits `shift` metres further into the hand
    let sv = null; if (shift) { const hc = new THREE.Vector3(); for (let k = 0; k < P.length; k += 3) hc.add(_v.set(P[k], P[k + 1], P[k + 2])); hc.divideScalar(P.length / 3);
      const pc = _t.clone(); sv = hc.sub(pc).normalize().multiplyScalar(shift); }
    for (let k = 0; k < HAND[S].length; k++) { const part = HAND[S][k][1]; _v.set(P[k * 3], P[k * 3 + 1], P[k * 3 + 2]); if (sv) _v.sub(sv);
      const loc = _v.clone().applyMatrix4(_inv).multiply(_s); const [d, n] = sdf(pr.shape, loc);
      if (gaps[part] === undefined || d < gaps[part]) gaps[part] = d;
      if (d < -IN) { nIn++; worst = Math.max(worst, -d); }
      if (d < TOUCH) { dirs.push(n.applyQuaternion(_q)); cen.add(_v); nc++; } }
    let spread = 0; const smp = dirs.filter((_, j) => j % Math.max(1, Math.floor(dirs.length / 40)) === 0);
    for (let a = 0; a < smp.length; a++) for (let b = a + 1; b < smp.length; b++) spread = Math.max(spread, Math.acos(Math.max(-1, Math.min(1, smp[a].dot(smp[b])))));
    const touching = Object.entries(gaps).filter(([, g]) => g < TOUCH).map(([k]) => k);
    return { gaps, nIn, worst, spread: spread * 180 / Math.PI, touching, near: Math.min(...Object.values(gaps)), at: nc ? cen.divideScalar(nc) : null }; }
  function verdict(r, mode) { if (!r) return 'hidden';
    if (r.nIn > 0) return 'CLIP';
    if (mode === 'hold') { if (r.near > FLOAT) return 'FLOATING'; if (r.touching.length < 3 || r.spread < 120) return 'LOOSE'; return 'ok'; }
    if (mode === 'rest') return r.near > FLOAT ? 'FLOATING' : 'ok';
    return 'ok'; }
  // every hand against every prop: listed pairs are judged by their mode, every other pair only for clipping
  function report(holds = []) { const out = [], P = { R: handWorld('R'), L: handWorld('L') };
    for (const S of ['R', 'L']) for (const name of Object.keys(PROPS)) { const h = holds.find(x => x.S === S && x.prop === name), mode = h ? h.mode : 'none';
      const r = probe(S, name, 0, P[S]); if (!r) continue; const v = verdict(r, mode); if (mode === 'none' && v === 'ok') continue;
      out.push({ S, prop: name, mode, verdict: v, inPts: r.nIn, depth: +(r.worst * 100).toFixed(2), near: +(r.near * 1000).toFixed(1), spread: Math.round(r.spread), touching: r.touching,
        gaps: Object.fromEntries(Object.entries(r.gaps).map(([k, g]) => [k, +(g * 1000).toFixed(1)])), at: r.at ? r.at.toArray().map(x => +x.toFixed(4)) : null }); }
    return out; }
  // prove the detector on this frame: push each listed prop 2 cm into its hand; a working detector must call that CLIP
  function selfTest(holds) { const res = []; for (const h of holds) { const r = probe(h.S, h.prop, 0.02); if (r) res.push({ S: h.S, prop: h.prop, caught: r.nIn > 0, inPts: r.nIn }); } return res; }
  return { prop, report, selfTest, probe, PROPS, HAND };
}
