// ------------------------------------------------------------------ hold, fit, judge
import { makeContact } from '/contact.js';
const CT = makeContact(THREE, G);
for (const k of ORDER) CT.prop(k, PROPS[k].g, PROPS[k].shape);
let BODYNOW = null; const SURF = null;
const FIT = {};                                          // per prop: { gap (palm offset), grasp }
const AIMBASE = {}, AIMROT = {};
function holdFor(k, off) { const a = aimFor(k), base = AIMBASE[k] ?? a.base, rot = AIMROT[k] || 0;
  if (rot) { const sh = PROPS[k].shape, ax = V(sh.axis === 'x' ? 1 : 0, sh.axis === 'y' ? 1 : 0, sh.axis === 'z' ? 1 : 0).applyQuaternion(PROPS[k].g.quaternion), q = qAA(ax, rot); a.n.applyQuaternion(q); a.u.applyQuaternion(q); } return { S: 'R', p: a.c.clone().addScaledVector(a.n, -(a.back + off)).addScaledVector(a.u, -base), n: a.n, u: a.u, c: 0, th: 0, memAbs: 'hold:' + k, seed: A(40, 15, 0, 80, 0) }; }
function poseFor(t, frame) { const g = guyAt(t); for (const k of ORDER) PROPS[k].g.visible = k === g.prop;
  RG.applyPose(g.pose, g.root); G.root.updateMatrixWorld(true);
  const off = FIT[g.prop] ? FIT[g.prop].off : 0.03; RG.hands([holdFor(g.prop, off)], 'b' + g.b, frame); G.root.updateMatrixWorld(true);
  if (FIT[g.prop]) CT.applyGrasp('R', FIT[g.prop].grasp); RG.untwist(); G.face(g.face); G.root.updateMatrixWorld(true); return g; }
// fit each prop once: for several placements (how far along the fingers the prop sits), ease the palm in until it's 0.8 mm off, close the
// hand on it, and judge the grip with the contact checker; keep the best (a full hold first, then the most wrap). One fixed placement left the
// bar sitting too far out along the fingers, so they hooked over it and couldn't close underneath (bench, 2026-11-02).
const BASES = [0.005, 0.02, 0.035, 0.05, 0.065], ROTS = [-40, -20, 0, 20, 40];   // along the fingers, and round the prop's axis (cylinders)
for (const [bi, k] of ORDER.entries()) { const t0 = B[bi] + 1; let best = null;
  for (const rot of PROPS[k].shape.type === 'cyl' ? ROTS : [0]) for (const base of BASES) { AIMBASE[k] = base; AIMROT[k] = rot;
    let lo = -0.01, hi = 0.05;
    for (let it = 0; it < 9; it++) { const md = (lo + hi) / 2; FIT[k] = { off: md, grasp: {} }; for (const kk of Object.keys(RG.MEM)) delete RG.MEM[kk]; poseFor(t0, -100);
      const pg = CT.partGap('R', k, 'palm'); if (pg.g < 0.0008 || pg.nIn > 0) lo = md; else hi = md; }
    FIT[k] = { off: hi, grasp: {} }; for (const kk of Object.keys(RG.MEM)) delete RG.MEM[kk]; poseFor(t0, -100);
    const gp = CT.grasp('R', k); FIT[k].grasp = gp; for (const kk of Object.keys(RG.MEM)) delete RG.MEM[kk]; poseFor(t0, -100);
    const r = CT.report([{ S: 'R', prop: k, mode: 'hold' }]).find(x => x.prop === k), cost = RG.LAST.costR || 0;
    // a finger that barely bends is lying flat along the prop (index straight down the bar, bench 2026-11-02): a real hold curls them all
    const flat = ['index', 'middle', 'ring', 'pinky'].filter(f => gp[f] && gp[f].a[0] + gp[f].a[1] + gp[f].a[2] < 70).length;
    const sc = (r.verdict === 'ok' ? 1000 : r.verdict === 'LOOSE' ? 500 : 0) + (r.cover || (r.oppose ? 150 : 0)) + 10 * r.touching.length - 2 * cost - 120 * flat;
    if (!best || sc > best.sc) best = { sc, base, rot, off: hi, grasp: gp, v: r.verdict, cover: r.cover, flat }; }
  AIMBASE[k] = best.base; AIMROT[k] = best.rot; FIT[k] = { off: best.off, grasp: best.grasp, base: best.base, rot: best.rot, v: best.v, cover: best.cover, flat: best.flat }; }
window.GRASPFIT = FIT;
// ------------------------------------------------------------------ frame I/O
let LASTB = 0, LASTF = -10;
function update(t, frame) { t = ((t % TOTAL) + TOTAL) % TOTAL; const g = poseFor(t, frame);
  const C = camAt(t, g); camera.position.copy(C.pos); camera.up.set(0, 1, 0); camera.lookAt(C.tgt); camera.fov = C.fov; camera.updateProjectionMatrix(); return { beat: g.b, prop: g.prop }; }
function stepTo(i) { const r = update(i / FPS, i); LASTB = r.beat; LASTF = i; return r; }
const draw = () => renderer.render(scene, camera);
const gl = renderer.getContext(), px = new Uint8Array(W * H * 4);
window.renderAll = async (f0, f1) => { for (let i = f0; i < f1; i++) { stepTo(i); draw(); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); await fetch('/frame', { method: 'POST', body: px }); } return 'ok'; };
window.renderAtT = t => { stepTo(Math.round(t * FPS));
  if (window.CAM) { camera.position.set(...window.CAM.pos); camera.up.set(0, 1, 0); camera.lookAt(...window.CAM.tgt); camera.fov = window.CAM.fov || 42; camera.updateProjectionMatrix(); }
  draw(); return renderer.domElement.toDataURL('image/png'); };
window.rigReport = i => { const r = stepTo(i); const ang = { ...RG.LAST }; delete ang.costR; delete ang.costL;
  return { t: i / FPS, beat: r.beat, ang, hips: wp(G.bones.hips).toArray(), show: true, cut: false, cost: [RG.LAST.costR ?? null, null], clip: [],
    contacts: CT.report([{ S: 'R', prop: r.prop, mode: 'hold' }]) }; };
window.contactSelfTest = () => CT.selfTest([{ S: 'R', prop: ORDER[LASTB], mode: 'hold' }]);
window.dbg = { G, RG, CT, THREE, scene, camera, renderer, wp };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS); window.READY = true;
window.SCN = { THREE, scene, camera, G, stepTo, renderer, FPS, B, DUR, TOTAL };
