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
// mode 'hold': skin must not go in (CLIP), something must touch (else FLOATING), and the touches must WRAP the prop: at least 3 hand parts
//              touching, and for a cylinder contacts reaching more than 180 degrees round its axis (not all on one side), for anything else contacts from opposite sides (else LOOSE).
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
    P = P || handWorld(S); const gaps = {}, dirs = [], locs = []; let nIn = 0, worst = 0; const cen = new THREE.Vector3(); let nc = 0;
    // shift (self-test): pretend the prop sits `shift` metres further into the hand
    let sv = null; if (shift) { const hc = new THREE.Vector3(); for (let k = 0; k < P.length; k += 3) hc.add(_v.set(P[k], P[k + 1], P[k + 2])); hc.divideScalar(P.length / 3);
      const pc = _t.clone(); sv = hc.sub(pc).normalize().multiplyScalar(shift); }
    for (let k = 0; k < HAND[S].length; k++) { const part = HAND[S][k][1]; _v.set(P[k * 3], P[k * 3 + 1], P[k * 3 + 2]); if (sv) _v.sub(sv);
      const loc = _v.clone().applyMatrix4(_inv).multiply(_s); const [d, n] = sdf(pr.shape, loc);
      if (gaps[part] === undefined || d < gaps[part]) gaps[part] = d;
      if (d < -IN) { nIn++; worst = Math.max(worst, -d); }
      if (d < TOUCH) { dirs.push(n.clone().applyQuaternion(_q)); locs.push(loc.clone()); cen.add(_v); nc++; } }
    let spread = 0; const smp = dirs.filter((_, j) => j % Math.max(1, Math.floor(dirs.length / 40)) === 0);
    for (let a = 0; a < smp.length; a++) for (let b = a + 1; b < smp.length; b++) spread = Math.max(spread, Math.acos(Math.max(-1, Math.min(1, smp[a].dot(smp[b])))));
    const touching = Object.entries(gaps).filter(([, g]) => g < TOUCH).map(([k]) => k);
    // wrap: for a cylinder, how far round its axis the contacts reach (the biggest empty arc, subtracted from 360); a held bar or can needs 200+.
    // For anything else: do the contacts push from opposite sides (two contact directions within 45 degrees of head-on)?
    let cover = 0, oppose = false; const sh = pr.shape;
    if (sh.type === 'cyl' && locs.length) { const ax = sh.axis || 'y', [p1, p2] = ax === 'x' ? ['y', 'z'] : ax === 'y' ? ['z', 'x'] : ['x', 'y'];
      const ang = locs.map(l => Math.atan2(l[p2], l[p1])).sort((x, y) => x - y); let gap = 2 * Math.PI - (ang[ang.length - 1] - ang[0]);
      for (let j = 1; j < ang.length; j++) gap = Math.max(gap, ang[j] - ang[j - 1]); cover = (2 * Math.PI - gap) * 180 / Math.PI; }
    for (let a = 0; a < smp.length && !oppose; a++) for (let b = a + 1; b < smp.length; b++) if (smp[a].dot(smp[b]) < -0.7) { oppose = true; break; }
    return { gaps, nIn, worst, spread: spread * 180 / Math.PI, cover, oppose, touching, near: Math.min(...Object.values(gaps)), at: nc ? cen.divideScalar(nc) : null, shape: pr.shape.type }; }
  function verdict(r, mode) { if (!r) return 'hidden';
    if (r.nIn > 0) return 'CLIP';
    if (mode === 'hold') { if (r.near > FLOAT) return 'FLOATING'; if (r.touching.length < 3 || !r.touching.includes('palm')) return 'LOOSE';   // no palm contact: it's between the fingers, not in the hand
      if (r.shape === 'cyl' ? r.cover <= 180 : !r.oppose) return 'LOOSE'; return 'ok'; }   // cylinder: held only if the contacts aren't all on one side (no empty arc of 180+)   // a draped hand touched 3+ parts at 151 degrees spread and passed the old test (bench, 2026-11-02)
    if (mode === 'rest') return r.near > FLOAT ? 'FLOATING' : 'ok';
    return 'ok'; }
  // every hand against every prop: listed pairs are judged by their mode, every other pair only for clipping
  function report(holds = []) { const out = [], P = { R: handWorld('R'), L: handWorld('L') };
    for (const S of ['R', 'L']) for (const name of Object.keys(PROPS)) { const h = holds.find(x => x.S === S && x.prop === name), mode = h ? h.mode : 'none';
      const r = probe(S, name, 0, P[S]); if (!r) continue; const v = verdict(r, mode); if (mode === 'none' && v === 'ok') continue;
      out.push({ S, prop: name, mode, verdict: v, inPts: r.nIn, depth: +(r.worst * 100).toFixed(2), near: +(r.near * 1000).toFixed(1), spread: Math.round(r.spread), cover: Math.round(r.cover), oppose: r.oppose, touching: r.touching,
        gaps: Object.fromEntries(Object.entries(r.gaps).map(([k, g]) => [k, +(g * 1000).toFixed(1)])), at: r.at ? r.at.toArray().map(x => +x.toFixed(4)) : null }); }
    return out; }
  // prove the detector on this frame: push each listed prop 2 cm into its hand; a working detector must call that CLIP
  function selfTest(holds) { const res = []; for (const h of holds) { const r = probe(h.S, h.prop, 0.02); if (r) res.push({ S: h.S, prop: h.prop, caught: r.nIn > 0, inPts: r.nIn }); } return res; }
  // ---- grasp: close a hand on a prop the way a real hand closes. The arm/palm placement is the caller's (aim the palm at the prop first).
  // Each finger bends knuckle by knuckle (base, middle, tip) in small steps until its skin touches the prop, never going in; the thumb then
  // swings round (opposition) and bends until it touches the prop or the index finger. Joints: <f>1, <f>2, <f>3 (G.fingers3) bent about local z.
  const R0 = {}; const rq = new THREE.Quaternion(), re = new THREE.Euler();
  function setJ(name, ex, ey, ez) { const b = G.bones[name]; if (!b) return; b.quaternion.copy(G.REST[name].q).multiply(rq.setFromEuler(re.set(ex * Math.PI / 180, ey * Math.PI / 180, ez * Math.PI / 180))); }
  function partGap(S, name, part) { const pr = PROPS[name]; pr.obj.updateWorldMatrix(true, false); pr.obj.matrixWorld.decompose(_t, _q, _s); _inv.copy(pr.obj.matrixWorld).invert();
    let g = 1, nIn = 0; for (const [i, p] of HAND[S]) { if (p !== part) continue; _v.set(ga.position.getX(i), ga.position.getY(i), ga.position.getZ(i)); m.applyBoneTransform(i, _v); _v.applyMatrix4(m.matrixWorld);
      const [d] = sdf(pr.shape, _v.applyMatrix4(_inv).multiply(_s)); if (d < g) g = d; if (d < -IN) nIn++; } return { g, nIn }; }
  // thumb against the curled fingers (skin vertex to skin vertex, every 2nd vertex): in a power grip on a bar the thumb wraps over the fingers,
  // not the bar, so it needs something besides the prop to stop on. Returns metres between the nearest thumb and index/middle skin points.
  // Thumb side: only its last segment (thumb3, or thumb2 without fingers3); fingers: the index/middle middle and tip segments. Whole digits fooled
  // it: the thumb's base always sits by the index knuckle, so a thumb sticking straight out still read 5 mm (sled, 2026-11-02).
  const TF = {}, boneOf = i => { let bw = -1, bi = 0; for (let k = 0; k < 4; k++) { const w = ga.skinWeight.getComponent(i, k); if (w > bw) { bw = w; bi = ga.skinIndex.getComponent(i, k); } } return names[bi]; };
  for (const S of ['R', 'L']) { TF[S] = { th: [], fi: [] }; const tipB = names.includes('thumb3' + S) ? 'thumb3' + S : 'thumb2' + S, fiB = ['index2', 'index3', 'middle2', 'middle3'].map(b => b + S);
    HAND[S].forEach(([i], k) => { if (k % 2) return; const b = boneOf(i); if (b === tipB) TF[S].th.push(i); else if (fiB.includes(b)) TF[S].fi.push(i); }); }
  function thumbFinger(S) { const w = ids => ids.map(i => { _v.set(ga.position.getX(i), ga.position.getY(i), ga.position.getZ(i)); m.applyBoneTransform(i, _v); return _v.clone().applyMatrix4(m.matrixWorld); });
    const A = w(TF[S].th), Bf = w(TF[S].fi); let d2 = 1; for (const a of A) for (const b of Bf) { const d = a.distanceToSquared(b); if (d < d2) d2 = d; } return Math.sqrt(d2); }
  // bend a thumb joint TOWARD a point (deg > 0 always curls in). The thumb's joints aren't on the fingers' local z: bent about z, the
  // tip curled sideways and backward in every sled shot (2026-11-02). The axis here is worked out from where the bones really are, each call.
  const _a = new THREE.Vector3(), _b = new THREE.Vector3(), _pq = new THREE.Quaternion(), _rq = new THREE.Quaternion();
  function curlToward(bn, deg, target) { const b = G.bones[bn]; if (!b || !deg) return; G.root.updateMatrixWorld(true);
    const p = new THREE.Vector3().setFromMatrixPosition(b.matrixWorld), tail = G.tailW(bn);
    _a.copy(tail).sub(p); _b.copy(target).sub(p); const ax = _a.cross(_b); if (ax.lengthSq() < 1e-12) return; ax.normalize();
    b.parent.getWorldQuaternion(_pq); _rq.setFromAxisAngle(ax, deg * Math.PI / 180);
    b.quaternion.premultiply(_pq.clone().invert().multiply(_rq).multiply(_pq)); }
  function grasp(S, name, o = {}) { const sg = S === 'R' ? -1 : 1, stop = o.stop ?? 0.0012, lim = o.lim || [95, 105, 85], out = {};
    const touch = (part) => { G.root.updateMatrixWorld(true); return partGap(S, name, part); };
    for (const f of ['index', 'middle', 'ring', 'pinky']) { const a = [0, 0, 0];
      const apply = () => { setJ(f + '1' + S, 0, 0, sg * a[0]); setJ(f + '2' + S, 0, 0, sg * a[1]); setJ(f + '3' + S, 0, 0, sg * a[2]); };
      apply(); let r = touch(f);
      // close like a real hand: all three knuckles together; when blocked, the outer two carry on; then the tip alone. One knuckle at a time
      // left the finger straight and touching only at its tip (it blocked everything else). Stops 0.4 mm short so frame wobble can't push skin in.
      const has3 = !!G.bones[f + '3' + S];
      for (const step of [[3, 3, 2.1], [0, 3, 2.1], [0, 0, 3]]) { if (!has3 && step[0] === 0 && step[1] === 0) break;
        for (let it = 0; it < 60; it++) { const nx = a.map((v, j) => Math.min(lim[j], v + step[j])); if (nx.every((v, j) => v === a[j])) break;
          const prev = a.slice(); for (let j = 0; j < 3; j++) a[j] = nx[j]; apply(); r = touch(f);
          if (r.nIn > 0 || r.g < 0.0004) { for (let j = 0; j < 3; j++) a[j] = prev[j]; apply(); r = touch(f); break; } } }
      out[f] = { a: a.slice(), gap: +(r.g * 1000).toFixed(1) }; }
    // thumb: opposition (thumb1 x) brings it round the far side, then its joints bend until it touches the prop (or the index finger)
    let best = null;
    for (const opp of o.opps || [0, 25, 50, 75, 100]) for (const yaw of o.yaws || [-45, -20, 0, 20, 45]) { const a = [0, 0];
      const apply = () => { setJ('thumb1' + S, -opp, yaw, sg * a[0]); thumbCurl(S, name, a[1]); };
      apply(); let r = touch('thumb'); if (r.nIn > 0 || thumbFinger(S) < 0.005) continue;
      const blocked = () => r.nIn > 0 || r.g < 0.0004 || thumbFinger(S) < 0.005;   // stops on the prop or on the fingers
      for (let j = 0; j < 2; j++) while (a[j] < [60, 80][j]) { a[j] += 3; apply(); r = touch('thumb'); if (blocked()) { a[j] -= 3; apply(); r = touch('thumb'); break; } }
      const onFingers = thumbFinger(S) < 0.008;
      if (r.g > 0.002 && !onFingers) continue;   // a thumb that reaches neither the prop nor the fingers doesn't count
      const pr = probe(S, name), sc = (pr.shape === 'cyl' ? pr.cover + 0.8 * (a[0] + a[1]) + (pr.cover > 180 ? 200 : 0) : (pr.oppose ? 180 : 0)) - pr.nIn * 100;
      // keep the thumb pose that wraps the prop most. On a cylinder a bent thumb also scores: an unbent one lay straight down the bar (bench, 2026-11-02)
      if (!best || sc > best.sc) best = { sc, g: r.g, opp, yaw, a: a.slice() }; }
    if (best) { setJ('thumb1' + S, -best.opp, best.yaw, sg * best.a[0]); thumbCurl(S, name, best.a[1]); out.thumb = { opp: best.opp, yaw: best.yaw, a: best.a, prop: name, curl: 'toward', gap: +(best.g * 1000).toFixed(1) }; }
    G.root.updateMatrixWorld(true); return out; }
  // re-apply a saved grasp (out of grasp()) each frame after the arm solve, so the fingers keep their fitted angles
  function applyGrasp(S, gp) { const sg = S === 'R' ? -1 : 1;
    for (const f of ['index', 'middle', 'ring', 'pinky']) if (gp[f]) { const a = gp[f].a; setJ(f + '1' + S, 0, 0, sg * a[0]); setJ(f + '2' + S, 0, 0, sg * a[1]); setJ(f + '3' + S, 0, 0, sg * a[2]); }
    if (gp.thumb) { const t = gp.thumb; setJ('thumb1' + S, -t.opp, t.yaw || 0, sg * t.a[0]); thumbCurl(S, t.prop, t.a[1]); } }
  // the thumb's middle and tip joints curl toward the held prop's centre (its own axis, worked out each call; see curlToward)
  function thumbCurl(S, name, deg) { setJ('thumb2' + S, 0, 0, 0); if (G.bones['thumb3' + S]) setJ('thumb3' + S, 0, 0, 0); const pr = PROPS[name]; if (!pr || !deg) return;
    G.root.updateMatrixWorld(true); const c = new THREE.Vector3().setFromMatrixPosition(pr.obj.matrixWorld);
    curlToward('thumb2' + S, deg, c); if (G.bones['thumb3' + S]) curlToward('thumb3' + S, deg * 0.8, c); }
  return { prop, report, selfTest, probe, grasp, applyGrasp, partGap, thumbFinger, curlToward, PROPS, HAND };
}
