// ------------------------------------------------------------------ the play, in real seconds from the catch (tau = 0), laid out from the game photos:
// Hockenson catches at the Lions 30 and turns upfield with the ball in his right arm; Campbell comes in low from his front-right and hits his right hip,
// O'Neill comes in low from his left; Hockenson pitches forward over them and lands on Campbell's upper back; Campbell stays face down at the 25.
const TC = 0.75, TDOWN = 1.6;
const ZC = zOf('DET', 30), ZHIT = zOf('DET', 27), ZDOWN = SPOT.z, HX = SPOT.x + 0.2;
const QB = V(-0.6, 1.9, zOf('DET', 42));
const yawOfDir = d => Math.atan2(-d.x, -d.z) / D2R;               // fwdOf(yaw) = (-sin, 0, -cos)
const DIRC = V(0.9, 0, 0.35).normalize(), YAWC = yawOfDir(DIRC);    // Campbell's line into him: from his front-left (photos: Campbell at his left hip)
const DIRO = V(-1, 0, -0.15).normalize(), YAWO = yawOfDir(DIRO);    // O'Neill's: from his right, a little behind (photos: O'Neill high at his right shoulder)
const HHIT = V(HX, 0, ZHIT);
function play(tau) { const o = {};
  // Hockenson
  if (tau < 0) { const ph = 1.2 + tau * 9.5; o.h = { pose: mixPose(run(ph), CATCH, smooth(-0.35, 0, tau)), pos: { x: HX + 0.2, y: bob(ph), z: ZC - tau * 6.2, yaw: lerp(0, -8, smooth(-0.6, 0, tau)) }, plant: true }; }
  else if (tau < TC) { const ph = 1.2 + tau * 9.5, k = smooth(TC - 0.32, TC - 0.04, tau);
    o.h = { pose: mixPose(mixPose(CATCH, carry(ph), smooth(0, 0.3, tau)), H_HIT, k), pos: { x: lerp(HX + 0.2, HX, tau / TC), y: lerp(bob(ph), 0.84, k), z: lerp(ZC, ZHIT, tau / TC), yaw: lerp(-8, 0, smooth(0, TC, tau)), tilt: -24 * k }, plant: true }; }
  else { const k = smooth(TC, TDOWN, tau);
    o.h = { pose: mixPose(H_HIT, H_FALL, smooth(TC, TC + 0.5, tau)), pos: { x: HX - 0.3 * k, y: lerp(0.84, 0.42, k), z: ZHIT - 0.45 * k, yaw: 14 * k, tilt: lerp(-24, -62, smooth(TC + 0.05, TDOWN, tau)), roll: 18 * k }, plant: 'feet' }; }
  o.ball = tau < 0 ? { free: true, k: clamp(1 + tau / 0.9, 0, 1) } : { free: false, k: smooth(0, 0.3, tau) };
  // Campbell: runs in on his line, gets low (back flat), hits; then goes down flat on his front, still driving
  const CPOS = HHIT.clone().addScaledVector(DIRC, -0.95);
  if (tau < TC) { const u = clamp((tau + 1.6) / (TC + 1.6), 0, 1), ph = 0.3 + tau * 8.5, k = smooth(TC - 0.4, TC - 0.02, tau), p = HHIT.clone().addScaledVector(DIRC, -lerp(4.6, 0.95, sm(u))).add(V(0, 0, -0.8 * (1 - u)));
    o.c = { pose: mixPose(tau < -0.8 ? READY : mixPose(READY, run(ph, -18), smooth(-0.8, -0.45, tau)), C_HIT, k), pos: { x: p.x, y: lerp(0.9, 0.66, k), z: p.z, yaw: YAWC, tilt: -64 * k }, plant: 'feet', wrap: smooth(TC - 0.7, TC - 0.1, tau) }; }
  else { const k = smooth(TC, TDOWN, tau), p = CPOS.clone().addScaledVector(DIRC, 0.22 * k);
    const fall = clamp((tau - TC) / (TDOWN - TC - 0.25), 0, 1);   // dropping under gravity to his front
    o.c = { pose: mixPose(C_HIT, C_FALL, k), pos: { x: p.x, y: lerp(0.66, 0.2, fall * fall), z: p.z, yaw: YAWC, tilt: lerp(-64, -87, smooth(0, 1, fall)) }, plant: 'feet', wrap: 1 - smooth(TC + 0.02, TC + 0.32, tau) }; }
  // O'Neill: chasing from behind the quarterback, low into his left hip, then down to his knees holding on
  const OPOS = HHIT.clone().addScaledVector(DIRO, -0.6);
  if (tau < TC) { const u = clamp((tau + 1.6) / (TC + 1.6), 0, 1), ph = 2.0 + tau * 9.5, k = smooth(TC - 0.4, TC - 0.02, tau), from = HHIT.clone().add(V(3.2, 0, 3.4)), p = from.lerp(OPOS, sm(u));
    o.o = { pose: mixPose(run(ph, -18), O_HIT, k), pos: { x: p.x, y: lerp(0.92, 0.86, k), z: p.z, yaw: lerp(140, YAWO, smooth(-0.6, TC - 0.1, tau)), tilt: -26 * k }, plant: true, wrap: smooth(TC - 0.7, TC - 0.1, tau) }; }
  else { const k = smooth(TC, TDOWN, tau), p = OPOS.clone().addScaledVector(DIRO, -0.55 * smooth(TC, TC + 0.35, tau));   // he lets go and drops to his knees, back off the pile
    o.o = { pose: mixPose(O_HIT, O_DOWN, k), pos: { x: p.x, y: lerp(0.86, 0.6, k), z: p.z, yaw: YAWO + 10 * k, tilt: lerp(-26, -30, k) }, plant: true, wrap: 1 - smooth(TC + 0.04, TC + 0.3, tau) }; }
  return o; }
// Hockenson's body frame (from his bones): right, up, forward
function frameOf(Px) { const Gx = Px.G, lat = wp(Gx.bones.uarmR).sub(wp(Gx.bones.uarmL)).normalize(), up = wp(Gx.bones.neck).sub(wp(Gx.bones.spine1)).normalize(), fwd = new THREE.Vector3().crossVectors(up, lat).normalize();
  return { lat, up, fwd, chest: wp(Gx.bones.chest), waist: wp(Gx.bones.spine1) }; }
function tuck(Px) { const F = frameOf(Px), c = F.chest.clone().addScaledVector(F.fwd, 0.2).addScaledVector(F.lat, 0.1).addScaledVector(F.up, -0.13);
  const ax = F.fwd.clone().multiplyScalar(0.85).addScaledVector(F.up, 0.3).addScaledVector(F.lat, -0.2).normalize(); return { c, ax, F }; }
// put a player down: pose, then plant him on the turf (lowest point on the ground) or just keep him out of it
function place(Px, R_, s) { if (!s) { Px.G.root.visible = false; return; } Px.G.root.visible = true; R_.applyPose(s.pose, s.pos); R_.untwist(); Px.G.root.updateMatrixWorld(true); ground(Px, s.plant !== false); }
function ground(Px, plant) { const lo = lowestOf(Px); let dy = 0;
  if (plant === 'feet') { let f = 1e9; for (const c of caps(Px)) if (c.part === 'foot') f = Math.min(f, Math.min(c.a.y, c.b.y) - c.r); dy = Math.max(0.002 - f, 0.002 - lo); }   // feet on the turf, nothing under it
  else if (plant || lo < 0.002) dy = 0.002 - lo;
  if (dy) { Px.G.root.position.y += dy; Px.G.root.updateMatrixWorld(true); } }
// push movers out of the bodies they overlap (arms are left to the hand solve); `flat` keeps a planted player's feet down (sideways push only)
function resolve(pairs, iters = 10) { for (let it = 0; it < iters; it++) { let worst = 0;
  for (const [A, B, flat, arms, wA = 1, flatB = true] of pairs) { if (!A.G.root.visible || !B.G.root.visible) continue; const ov = overlap(A, B, !arms); if (ov.depth <= 0.001) continue; worst = Math.max(worst, ov.depth);
    // A moves wA of the way out along the overlap normal, B the rest the other way (a flat mover only slides sideways)
    for (const [P, w, sg, fl] of [[A, wA, 1, flat], [B, 1 - wA, -1, flatB]]) { if (w <= 1e-4) continue; const d = ov.n.clone().multiplyScalar(sg);
      if (fl) { d.y = 0; if (d.lengthSq() < 1e-6) continue; d.normalize(); const c = Math.max(0.2, Math.abs(ov.n.dot(d))); P.G.root.position.addScaledVector(d, w * (ov.depth + 0.002) / c); }
      else P.G.root.position.addScaledVector(d, w * (ov.depth + 0.002)); P.G.root.updateMatrixWorld(true); } }
  if (worst < 0.002) break; } }
// the hands: wraps round Hockenson's hips (targets on his body frame, palms toward him), every arm kept out of the other bodies
const HANDS = (R_, list, key, frame) => { R_.hands(list, key, frame); R_.untwist(); R_.G.root.updateMatrixWorld(true); };
for (const R_ of [RG, RH, RO, RT]) R_.contactCost = armCost(R_);
const LASTT = {};
const ownHelmet = P => caps(P).filter(x => x.part === 'helmet');
// a hand target on the outside of a body: start at `c`, walk out along `dir` until the hand (radius 3.5 cm + 5 mm) clears every capsule of `body`
function outside(body, c, dir, gap = 0.04) { const cs = caps(body), d = dir.clone().normalize(); for (let r = 0.05; r < 0.6; r += 0.005) { const p = c.clone().addScaledVector(d, r);
    if (cs.every(y => segDist(p, p, y.a, y.b).d > y.r + gap)) return p; } return c.clone().addScaledVector(d, 0.6); }
const around = (F, a) => F.fwd.clone().setY(0).normalize().multiplyScalar(Math.cos(a * D2R)).addScaledVector(F.lat.clone().setY(0).normalize(), Math.sin(a * D2R));   // 0 = his front, 90 = his right, -90 = his left
function wrapTargets(F, who) { const hp = wp(HOCK.G.bones.hips).addScaledVector(F.up, 0.04), ch = F.chest.clone().addScaledVector(F.up, 0.06);
  if (who === 'c') return [{ S: 'L', p: outside(HOCK, hp.clone().add(V(0, -0.08, 0)), around(F, -30)), c: 45 }, { S: 'R', p: outside(HOCK, hp, around(F, -125)), c: 45 }];   // round his hips: near arm in front of his left hip, far arm behind it
  return [{ S: 'R', p: outside(HOCK, ch.clone().addScaledVector(F.up, 0.16), around(F, 110)), c: 45 }, { S: 'L', p: outside(HOCK, ch.clone().addScaledVector(F.up, -0.05), around(F, 125)), c: 45 }]; }   // over his right shoulder, and round his back
// bodies apart along fixed directions, by bisection (so the result changes smoothly with play time): Campbell backs off along his run line while
// they stand, Hockenson rides up onto him as they go down (a blend between); O'Neill backs off along his own line from both of them
function pushOut(movers, clear) { const save = movers.map(([P]) => P.G.root.position.clone()), at = s => { movers.forEach(([P, d], i) => { P.G.root.position.copy(save[i]).addScaledVector(d, s); P.G.root.updateMatrixWorld(true); }); };
  if (clear()) return; let lo = 0, hi = 0.05; at(hi); while (!clear() && hi < 0.8) { lo = hi; hi *= 2; at(hi); }
  for (let k = 0; k < 18; k++) { const m = (lo + hi) / 2; at(m); if (clear()) hi = m; else lo = m; } at(hi); }
const apart = (A, B, tol = 0.001) => overlap(A, B).depth <= tol;
function separatePlay(tau) { const wf = 0.45 * smooth(TC - 0.02, TC + 0.3, tau), back = DIRC.clone().negate();   // Hockenson takes at most 45% of the push (upward, onto him); Campbell is driven back for the rest
  pushOut([[CAMP, back.clone().multiplyScalar(1 - wf)], [HOCK, V(0, wf, 0)]], () => apart(CAMP, HOCK));
  pushOut([[ONEIL, DIRO.clone().negate()]], () => apart(ONEIL, HOCK) && apart(ONEIL, CAMP)); }
// arm solve without history (the same answer whatever frame came before, so render chunks match): coordinate descent from a fixed seed over human joint
// limits, paying for a missed target, a turned palm, distance from an anchor pose, and any point of the arm inside another body (or his own torso / helmet)
function contactPts(f) { const pts = []; for (let k = 1; k <= 6; k++) pts.push([f.sh.clone().lerp(f.el, k / 6), 0.053]); for (let k = 1; k <= 6; k++) pts.push([f.el.clone().lerp(f.p, k / 6), 0.044]); for (const k of [0.025, 0.05, 0.075, 0.1]) pts.push([f.p.clone().addScaledVector(f.u, k), 0.032]); return pts; }   // the fingers too
let CALLN = 0, WARM_IN = null, WARM_OUT = {}, CALLK = {}; const FING = {};
function armSolve(R_, S, o) { const others = o.others || [], key = R_.tag + S + ':' + (o.p ? 'p' : 'n') + (o.n ? 'n' : '') + ':' + (o.ascale || 0) + ':' + (o.steps ? o.steps[0] : 16) + ':' + (CALLK[R_.tag + S] = (CALLK[R_.tag + S] || 0) + 1);
  const cost = a => { const f = R_.handFK(S, a); let c = 0;
    if (o.p) c += f.p.distanceToSquared(o.p) / (0.008 * 0.008);
    if (o.n) c += (1 - f.n.dot(o.n)) * 30; if (o.u) c += (1 - f.u.dot(o.u)) * 20;
    if (o.anchor) for (let i = 0; i < 7; i++) c += ((a[i] - o.anchor[i]) / (o.ascale || 3)) ** 2;
    for (let i = 0; i < 7; i++) { const [lo, hi] = ARM_LIM[i], mid = [20, 15, 0, 60, 0, 0, 0][i]; c += 0.6 * ((a[i] - mid) / (hi - lo)) ** 2; }
    const wr = wp(R_.G.bones['hand' + S]), tip = R_.G.tailW('middle2' + S);   // the arm as the same capsules the clip report uses
    for (const [p0, p1, r] of [[f.sh, f.el, 0.052], [f.el, wr, 0.042], [wr, tip, 0.032]]) for (const y of others) { const d = segDist(p0, p1, y.a, y.b).d - (r + y.r); if (d < 0.008) c += ((d - 0.008) / 0.002) ** 2; }   // keep 8 mm clear
    return c; };
  const sd0 = WARM_IN && WARM_IN[key] ? WARM_IN[key] : o.seed;   // warm start from the same solve one step earlier (table build only)
  let a = sd0.map((v, i) => clamp(v, ARM_LIM[i][0], ARM_LIM[i][1])), ca = cost(a);
  if (WARM_IN && WARM_IN[key]) { const b0 = o.seed.map((v, i) => clamp(v, ARM_LIM[i][0], ARM_LIM[i][1])), cb0 = cost(b0); if (cb0 < ca - 25) { a = b0; ca = cb0; } }
  for (const step of o.steps || [16, 8, 4, 2, 1, 0.5]) { let imp = true, g = 0; while (imp && g++ < 12) { imp = false; for (let i = 0; i < 7; i++) for (const sg of [1, -1]) { const b = a.slice(); b[i] = clamp(b[i] + sg * step, ARM_LIM[i][0], ARM_LIM[i][1]); if (o.box && Math.abs(b[i] - o.seed[i]) > o.box) continue; const cb = cost(b); if (cb < ca - 1e-9) { a = b; ca = cb; imp = true; } } } }
  WARM_OUT[key] = a; R_.setArm(S, a); R_.LAST['arm' + S] = a; const f = R_.handFK(S, a); return { a, c: ca, miss: o.p ? f.p.distanceTo(o.p) : 0 }; }
const ownBody = P => caps(P).filter(x => x.part === 'helmet' || x.part === 'torso');
const BODYOF = P => caps(P);
const SEEDS = {};
const CANDS = [A(150, 30, 0, 40), A(120, 60, 30, 60), A(160, 10, -30, 30), A(100, 40, 60, 90), A(140, 20, 40, 70), A(90, 20, 0, 100), A(130, 45, -40, 50), A(70, 50, 30, 80)];
function fingersAll(R_, S, c) { FING[R_.tag + S] = c; const pp = {}; curl(pp, S, c); for (const [n, e] of Object.entries(pp)) if (R_.G.bones[n]) R_.G.bones[n].quaternion.copy(R_.G.REST[n].q).multiply(qTmp.setFromEuler(eTmp.set(e[0] * D2R, e[1] * D2R, e[2] * D2R))); }
function stagePlayRaw(o, tau, frame) { CALLN = 0; WARM_OUT = {}; CALLK = {}; for (const R_ of [RG, RO, RH]) for (const S of ['R', 'L']) FING[R_.tag + S] = null;
  place(HOCK, RH, o.h); place(CAMP, RG, o.c); place(ONEIL, RO, o.o);
  const falling = tau > TC + 0.05;
  separatePlay(tau);
  for (const [P, s] of [[HOCK, o.h], [CAMP, o.c], [ONEIL, o.o]]) ground(P, s.plant !== false);
  // Hockenson's right hand: the ball comes from his hands into the tuck under his right arm
  const T = tuck(HOCK), bk = o.ball;
  if (!bk.free) { const handsMid = wp(HOCK.G.bones.handR).lerp(wp(HOCK.G.bones.handL), 0.5).addScaledVector(T.F.fwd, 0.07), c = handsMid.lerp(T.c, bk.k);
    ball.position.copy(c); ball.quaternion.setFromUnitVectors(V(0, 0, 1), T.ax);
    if (bk.k > 0.02) { const p = c.clone().addScaledVector(T.ax, 0.07).addScaledVector(T.F.up, 0.05), pose = RH.LAST.armR.slice();
      const bl = pose.map((v, i) => lerp(v, (SEEDS.hR || pose)[i], bk.k)); RH.setArm('R', bl); RH.LAST.armR = bl; fingersAll(RH, 'R', lerp(60, 55, bk.k)); } }   // the tuck arm, fixed (solved once)
  else { const q = QB.clone().lerp(wp(HOCK.G.bones.handR).lerp(wp(HOCK.G.bones.handL), 0.5).addScaledVector(frameOf(HOCK).fwd, 0.07), bk.k).add(V(0, 2.0 * Math.sin(Math.PI * bk.k), 0)); ball.position.copy(q); ball.quaternion.setFromUnitVectors(V(0, 0, 1), V(0.1, -0.15, 1).normalize()); }
  // the defenders' wraps (targets just outside his body), blended in from their running arms; then every arm nudged out of every body
  const F = frameOf(HOCK);
  // the defenders' wraps are FIXED arms (solved once at the hit, against the bodies there), eased in from the running arms and out to the pose's
  // arms; only a small local nudge per frame keeps them out of bodies. A per-frame solve to moving targets flipped between answers (arm pops).
  for (const [P, R_, s, who, oth] of [[CAMP, RG, o.c, 'c', [HOCK, ONEIL]], [ONEIL, RO, o.o, 'o', [HOCK, CAMP]]]) {
    const others = oth.flatMap(q => BODYOF(q)).concat(ownHelmet(P)), w = sm(clamp(s.wrap || 0, 0, 1));
    for (const S of ['R', 'L']) { const pose = (s.pose['arm' + S] || ARM0).slice(), sd = SEEDS[who + S] || pose, mid = sd.map((v, i) => [Math.max(v, pose[i]) + 15, Math.max(v, pose[i]) + 20, (v + pose[i]) / 2, Math.min(v, pose[i]), (v + pose[i]) / 2, (v + pose[i]) / 2, (v + pose[i]) / 2][i]);   // in and out by way of a raised, open arm (a straight blend swept through his ball arm)
      const a = w < 0.5 ? pose.map((v, i) => lerp(v, mid[i], sm(w * 2))) : mid.map((v, i) => lerp(v, sd[i], sm(w * 2 - 1)));
      fingersAll(R_, S, lerp(30, 45, w));
      armSolve(R_, S, { seed: a, anchor: a, ascale: 6, others, steps: [8, 4, 2, 1, 0.5], box: 25 }); } }
  armSolve(RH, 'L', { seed: RH.LAST.armL, anchor: RH.LAST.armL, ascale: 3, others: [...caps(CAMP), ...caps(ONEIL)].concat(ownHelmet(HOCK)), steps: [2, 1, 0.5], box: 6 });
  // one more pass over every arm against everyone (each arm moved last sees the others' final arms)
  for (const [P, R_, oth] of [[CAMP, RG, [HOCK, ONEIL]], [ONEIL, RO, [HOCK, CAMP]], [HOCK, RH, [CAMP, ONEIL]]]) { const others = oth.flatMap(q => caps(q)).concat(ownHelmet(P));
    for (const S of ['R', 'L']) { if (P === HOCK && S === 'R' && !bk.free && bk.k > 0.5) continue; const a = R_.LAST['arm' + S].slice(); armSolve(R_, S, { seed: a, anchor: a, ascale: 6, others, steps: [8, 4, 2, 1, 0.5], box: 25 }); } }
  for (const R_ of [RG, RO, RH]) { R_.untwist(); R_.G.root.updateMatrixWorld(true); }
  for (let k = 0; k < 3; k++) { for (const [P, s] of [[HOCK, o.h], [CAMP, o.c], [ONEIL, o.o]]) ground(P, false); separatePlay(tau); } }
// the play's arms are solved once at load, in order along a fine grid of play time (each step warm-started from the one before), and every frame
// reads the table (bodies, arms, fingers, ball) and blends between grid steps: no solving at render time, so any chunk of frames comes out the
// same as a straight run, and the solver can't flip between answers from one frame to the next.
const TAU0 = -1.7, TAU1 = TDOWN + 0.15, DTAU = 1 / 120; let TAB = null;
function snap() { const S_ = p => ({ pos: p.G.root.position.clone(), q: p.G.root.quaternion.clone() }); const r = {};
  for (const [nm, P, R_] of [['c', CAMP, RG], ['o', ONEIL, RO], ['h', HOCK, RH]]) r[nm] = { ...S_(P), R: R_.LAST.armR.slice(), L: R_.LAST.armL.slice(), fR: FING[R_.tag + 'R'], fL: FING[R_.tag + 'L'] };
  r.ball = { pos: ball.position.clone(), q: ball.quaternion.clone() }; return r; }
function buildTable() { TAB = []; WARM_IN = null; const n = Math.ceil((TAU1 - TAU0) / DTAU);
  for (let k = 0; k <= n; k++) { const tau = TAU0 + k * DTAU; stagePlayRaw(play(tau), tau, -1); WARM_IN = WARM_OUT; TAB.push(snap()); } WARM_IN = null; }
function stagePlay(o, tau, frame) { if (!TAB || tau < TAU0 || tau > TAU1) return stagePlayRaw(o, tau, frame);
  const x = (tau - TAU0) / DTAU, i = Math.min(TAB.length - 2, Math.floor(x)), f = x - i, A_ = TAB[i], B_ = TAB[i + 1];
  place(HOCK, RH, o.h); place(CAMP, RG, o.c); place(ONEIL, RO, o.o);
  for (const [nm, P, R_] of [['c', CAMP, RG], ['o', ONEIL, RO], ['h', HOCK, RH]]) { const a = A_[nm], b = B_[nm];
    P.G.root.position.copy(a.pos).lerp(b.pos, f); P.G.root.quaternion.copy(a.q).slerp(b.q, f); P.G.root.updateMatrixWorld(true);
    for (const S of ['R', 'L']) { const arm = a[S].map((v, j) => lerp(v, b[S][j], f)); R_.setArm(S, arm); R_.LAST['arm' + S] = arm; const fa = a['f' + S], fb = b['f' + S]; if (fa != null && fb != null) fingersAll(R_, S, lerp(fa, fb, f)); }
    R_.untwist(); P.G.root.updateMatrixWorld(true); }
  ball.position.copy(A_.ball.pos).lerp(B_.ball.pos, f); ball.quaternion.copy(A_.ball.q).slerp(B_.ball.q, f); }
// seeds: solved once at load from a fixed moment (the hit), from several starting arms, so every frame starts its solve from the same good arm
function makeSeeds() { const tau = TC - 0.03, o = play(tau); place(HOCK, RH, o.h); place(CAMP, RG, o.c); place(ONEIL, RO, o.o);
  resolve([[CAMP, HOCK, true], [ONEIL, HOCK, true], [ONEIL, CAMP, true]]); for (const [P, s] of [[HOCK, o.h], [CAMP, o.c], [ONEIL, o.o]]) ground(P, s.plant !== false);
  const T = tuck(HOCK), c = T.c, p = c.clone().addScaledVector(T.ax, 0.07).addScaledVector(T.F.up, 0.05); let best = null;
  for (const sd of [RH.LAST.armR, ...CANDS]) { const r = armSolve(RH, 'R', { p, n: c.clone().sub(p).normalize(), u: T.ax.clone(), seed: sd, others: ownHelmet(HOCK) }); if (!best || r.c < best.c) best = r; } SEEDS.hR = best.a; RH.setArm('R', best.a);
  const F = frameOf(HOCK);
  for (const [P, R_, who, oth] of [[CAMP, RG, 'c', [HOCK, ONEIL]], [ONEIL, RO, 'o', [HOCK, CAMP]]]) { const tg = wrapTargets(F, who), others = oth.flatMap(q => BODYOF(q)).concat(ownHelmet(P));
    for (const h of tg) { let b = null; for (const sd of [R_.LAST['arm' + h.S], ...CANDS]) { const r = armSolve(R_, h.S, { p: h.p, seed: sd, others }); if (!b || r.c < b.c) b = r; } SEEDS[who + h.S] = b.a; R_.setArm(h.S, b.a); } }
  return SEEDS; }
const FWD_H = () => frameOf(HOCK).fwd;
// ------------------------------------------------------------------ story: one shot per line
const XRL = [6, 7, 8, 12];
const SLOW0 = [TC - 0.08, TC + 0.02];       // the hook: almost frozen at the hit
function shot(t) { const nb = beatAt(t), lt = t - B[nb], dur = DUR[nb], u = lt / dur;
  hud.visible = false; board.visible = false; cart.visible = false; TR.root.visible = false; SIG.visible = false; NERVES.forEach(l => l.visible = false); CORD.pinch = 0;
  for (const P of PLAYERS) { P.G.root.visible = true; P.airOK = false; } ball.visible = true;
  let cp, ct, fov = 34, near = 0.05, xr = false, roll = 0;
  const ST = { c: null, h: null, o: null };
  // the hook camera: from the photo side (his front and Campbell's back, O'Neill on the left), swinging slowly
  const camHook = (lt0) => { const a = (lerp(172, 150, lt0 / DUR[0])) * D2R, c = V(HX - 0.1, 0.9, ZHIT - 0.05); return { cp: V(c.x + Math.sin(a) * 4.2, 1.2, c.z + Math.cos(a) * 4.2), ct: c }; };
  switch (nb) {
    // 13: real speed, easing into frame one's slow motion at the end so the loop doesn't jump
    case 0: case 13: { // the hit: nearly frozen, the camera circling (13 runs the play in real time and lands on frame one)
      let tau, cam;
      if (nb === 0) { tau = lerp(SLOW0[0], SLOW0[1], u); cam = camHook(lt); }
      else { const left = dur - lt, v0 = (SLOW0[1] - SLOW0[0]) / DUR[0]; tau = SLOW0[0] - (v0 * left + (0.85 - v0) * left * left / (left + 0.4)); const h = camHook(0), k = smooth(0, dur * 0.85, lt);
        cam = { cp: V(SPOT.x - 9, 6, ZC + 9).lerp(h.cp, k), ct: V(SPOT.x, 0.9, ZC - 1).lerp(h.ct, k) };
        hud.visible = lt < dur * 0.6; drawHud([['GET WELL', 'SOON', '#2fbf71'], ['#46', 'JACK CAMPBELL']]); }
      ST.play = play(tau); ST.tau = tau; cp = cam.cp; ct = cam.ct; fov = 32; break; }
    case 1: { // who he is: Campbell, ready, at the 25 before the snap; push in
      ST.c = { pose: READY, pos: { x: SPOT.x - 0.5, y: 0.84, z: ZDOWN - 2.6, yaw: 180 } }; ST.h = null; ST.o = null; ball.visible = false;
      const c = V(SPOT.x - 0.5, 1.25, ZDOWN - 2.6); cp = V(c.x + lerp(1.6, 1.0, u), lerp(1.45, 1.35, u), c.z + lerp(3.6, 2.4, u)); ct = c.clone(); fov = 34;
      hud.visible = true; drawHud([['LIONS #46', 'CAMPBELL'], ['ALL-PRO', 'LINEBACKER', '#ffd23a']]); break; }
    case 2: { // Ford Field, the 4th quarter, the snap: a high broadcast view as the play starts (the three players in it)
      const tau = lerp(-1.6, -0.9, u); ST.play = play(tau); ST.tau = tau;
      cp = V(SPOT.x - 14 + 3 * u, 10 - u, ZC - 13 + 2 * u); ct = V(SPOT.x + 0.5, 0.6, ZC - 0.5); fov = 30;
      hud.visible = true; drawHud([['4TH QUARTER', 'LIONS 12-7'], ['3RD & 15', 'AT DET 35', '#ffd23a']]); break; }
    case 3: { // the short pass over the middle: real time, the camera tracking him
      const tau = lerp(-1.5, 0.5, u), o = play(tau); ST.play = o; ST.tau = tau;
      const hz = o.h.pos.z; cp = V(HX + 3.6, 1.55, hz + 3.4); ct = V(HX + 0.1, 1.0, hz - 0.6); fov = 36; break; }
    case 4: { // SLOW MOTION from the side: the hit and the twist down
      const tau = lerp(TC - 0.2, TDOWN + 0.05, smooth(0.02, 0.97, u)); ST.play = play(tau); ST.tau = tau;
      const c = V(HX + 0.3, lerp(0.85, 0.4, smooth(TC, TDOWN, tau)), lerp(ZHIT, ZHIT - 0.4, smooth(TC, TDOWN, tau)));
      const a = lerp(205, 160, u) * D2R; cp = V(c.x + Math.sin(a) * 4.4, lerp(1.15, 0.95, u), c.z + Math.cos(a) * 4.4); ct = c; fov = 32; roll = lerp(-3, 3, u); break; }
    case 5: { // face down, not moving; the others get up around him (overhead, slow)
      const o = play(TDOWN); ST.c = { pose: PRONE, pos: { ...o.c.pos, tilt: -87 }, plant: false };
      const hp = o.h.pos, ku = smooth(0.2, 0.9, u); ST.h = { pose: mixPose(SIDE, KNEEL, ku), pos: { x: hp.x + 0.8, y: lerp(0.3, 0.6, ku), z: hp.z - 0.1, yaw: lerp(-60, 60, ku), roll: lerp(-80, 0, smooth(0.15, 0.8, u)) }, plant: ku > 0.6 };
      ST.o = { pose: mixPose(KNEEL, STAND, smooth(0.1, 0.8, u)), pos: { x: o.o.pos.x - 0.3, y: lerp(0.6, 0.95, smooth(0.1, 0.8, u)), z: o.o.pos.z + 0.6, yaw: -60 } };
      ST.res = [[HOCK, CAMP, false], [ONEIL, CAMP, true], [ONEIL, HOCK, true]];
      placeBallLater = { free: true, p: V(SPOT.x + 0.9, 0.09, ZDOWN + 0.7) };
      const c = V(o.c.pos.x, 0.2, o.c.pos.z), a = lerp(0.2, 0.45, u); cp = V(c.x + Math.sin(a) * 2.6, lerp(5.6, 4.6, u), c.z + Math.cos(a) * 2.6); ct = c; fov = 34; break; }
    case 6: case 7: case 8: case 12: { // x-ray explainers: he stands in his pads, see-through; the neck, the cord, the signals
      xr = true; ST.c = { pose: STAND, pos: { x: SPOT.x, y: 0.95, z: ZDOWN, yaw: 90 } }; ST.h = null; ST.o = null; ball.visible = false;
      if (nb === 8) { const b = smooth(0.08, 0.45, u); ST.c.pose = addPose(STAND, { neck: [-34 * b, 0, 0], head: [-28 * b, 0, 0], spine2: [-10 * b, 0, 0] }); CORD.pinch = smooth(0.3, 0.55, u); }
      break; }
    case 9: { // the board: on his back, strapped down, a trainer holding his head still
      ST.c = { pose: SUPINE, pos: { x: SPOT.x + 0.6, y: 0.2, z: ZDOWN - 1.2, yaw: 180, tilt: 90 }, plant: false }; ST.h = null; ST.o = null; ball.visible = false; board.visible = true;
      ST.tr = true; const c = V(SPOT.x + 0.6, 0.35, ZDOWN - 1.95); cp = V(c.x + lerp(1.9, 1.5, u), lerp(1.05, 0.9, u), c.z + lerp(0.9, 0.6, u)); ct = c; fov = 34; break; }
    case 10: case 11: { // both teams take a knee; the cart takes him off the field toward the tunnel
      ball.visible = false; cart.visible = true; board.visible = true;
      const drive = nb === 10 ? smooth(0.55, 1.0, u) * 0.18 : 0.18 + 0.82 * smooth(0, 1, u);
      const cz = lerp(ZDOWN - 1.2, -GL - EZ - 4, drive), cx = lerp(SPOT.x + 0.6, -FW / 2 - 4, sm(drive));
      ST.cart = { x: cx, z: cz, yaw: Math.atan2(-(lerp(SPOT.x + 0.6, -FW / 2 - 4, sm(Math.min(1, drive + 0.02))) - cx), -1) / D2R };
      ST.c = { pose: SUPINE, onCart: true }; ST.h = { pose: KNEEL, pos: { x: SPOT.x + 1.0, y: 0.6, z: ZDOWN + 1.6, yaw: 165 } }; ST.o = { pose: KNEEL, pos: { x: SPOT.x - 0.35, y: 0.6, z: ZDOWN + 0.3, yaw: -165 } };
      if (nb === 10) { cp = V(SPOT.x + 0.3, lerp(1.3, 1.7, u), ZDOWN + 6.6 - 0.8 * u); ct = V(SPOT.x + 0.4, 0.7, ZDOWN - 0.4); fov = 38; hud.visible = u > 0.45; drawHud([['GAME STOPPED', '~10 MIN'], ['BOTH TEAMS', 'TOOK A KNEE', '#ffd23a']]); }
      else { cp = V(SPOT.x - 6, 4.5, ZDOWN + 8 - 4 * u); ct = V(cx, 0.8, cz); fov = 36; hud.visible = true; drawHud([['LEFT', 'ALERT, BREATHING', '#2fbf71'], ['FINAL', 'LIONS 19-15']]); }
      break; }
  }
  // pose everyone
  if (ST.play) stagePlay(ST.play, ST.tau, Math.round(t * FPS));
  else { place(CAMP, RG, ST.c && !ST.c.onCart ? ST.c : null); place(HOCK, RH, ST.h); place(ONEIL, RO, ST.o); if (ST.res) for (let k = 0; k < 3; k++) { resolve(ST.res, 16); for (const P of [CAMP, HOCK, ONEIL]) if (P.G.root.visible) ground(P, false); } }
  if (ST.cart) { cart.position.set(ST.cart.x, 0, ST.cart.z); cart.rotation.y = ST.cart.yaw * D2R; cart.updateMatrixWorld(true);
    board.position.copy(V(0, CARTDECK, 0.6).applyMatrix4(cart.matrixWorld)); board.rotation.y = cart.rotation.y; board.updateMatrixWorld(true);
    const bc = V(0, 0.24, 0.05).applyMatrix4(board.matrixWorld); CAMP.G.root.visible = true; CAMP.airOK = true;   // on the cart's deck
    RG.applyPose(SUPINE, { x: bc.x, y: bc.y, z: bc.z, yaw: cart.rotation.y / D2R + 180, tilt: 90 }); RG.untwist(); G.root.updateMatrixWorld(true); }
  if (ST.tr) { board.position.set(SPOT.x + 0.6, 0, ZDOWN - 1.2 + 0.05); board.rotation.y = 0; board.updateMatrixWorld(true);
    // the trainer kneels at his head, both hands flat on the sides of the helmet
    TR.root.visible = true; const hc = wp(CAMP.helmet); RT.applyPose(TR_KNEEL, { x: hc.x, y: 0.6, z: hc.z - 0.62, yaw: 180 }); TR.root.updateMatrixWorld(true);
    { const lo = lowestOfG(TR); TR.root.position.y += 0.002 - lo; TR.root.updateMatrixWorld(true); }
    const side = V(1, 0, 0), others = caps(CAMP);
    for (const [S, sg] of [['R', -1], ['L', 1]]) { const p = outside(CAMP, hc.clone(), side.clone().multiplyScalar(sg), 0.035), n = side.clone().multiplyScalar(-sg);
      if (!TRSEED[S]) { let b = null; for (const sd of [RT.LAST['arm' + S], ...CANDS]) { const r = armSolve(RT, S, { p, n, seed: sd, others }); if (!b || r.c < b.c) b = r; } TRSEED[S] = b.a; }
      armSolve(RT, S, { p, n, seed: TRSEED[S], others }); fingersAll(RT, S, 12); }
    RT.untwist(); TR.root.updateMatrixWorld(true); }
  if (board.visible && CAMP.G.root.visible) strapsOn(CAMP);
  if (ball.visible && !ST.play && placeBallLater) { ball.position.copy(placeBallLater.p); ball.quaternion.identity(); } placeBallLater = null;
  G.face({ blink: nb === 5 || nb === 9 || nb === 10 || nb === 11 ? 0.85 : 0 });
  // x-ray close-ups
  xray(xr);
  if (xr) { const N = placeSpine(); const neckP = wp(G.bones.neck);
    if (nb === 6) { cp = neckP.clone().add(V(lerp(0.75, 0.55, u), lerp(0.12, 0.08, u), lerp(0.55, 0.35, u))); ct = neckP.clone().add(V(0, 0.06, 0)); fov = 30; near = 0.02;
      hud.visible = true; drawHud([['NECK BONES', '7', '#ffffff'], ['INSIDE', 'SPINAL CORD', '#ffd23a']]); }
    else if (nb === 7 || nb === 12) { const hip = wp(G.bones.hips); cp = hip.clone().add(V(lerp(3.3, 2.9, u), 0.35, lerp(1.0, 0.7, u))); ct = hip.clone().add(V(0, 0.05, 0)); fov = 34; near = 0.03;
      const paths = nervePaths(N.curve);
      if (nb === 7) drawSignals(paths, lt, () => 1);
      else { drawSignals(paths, lt, (k) => k.startsWith('leg') || k === 'cord' ? 1 : 0.6); hud.visible = true; drawHud([['LOWER BODY', 'FULL MOVEMENT', '#2fbf71'], ['UPPER BODY', 'GETTING BETTER', '#ffd23a']]); } }
    else { cp = neckP.clone().add(V(0.72, 0.02, 0.32)); ct = neckP.clone().add(V(0, 0.02, 0.04)); fov = 32; near = 0.02;
      const paths = nervePaths(N.curve); const pinch = CORD.pinch;
      drawSignals(paths, lt, (k, uu) => k === 'cord' ? (uu < CORD.k * 0.9 ? 1 : 1 - pinch) : 1 - pinch);
      hud.visible = u > 0.3; drawHud([['NECK', 'BENT TOO FAR', '#ff6a5c'], ['SIGNALS', pinch > 0.6 ? 'BLOCKED' : 'SQUEEZED', '#ff6a5c']]); }
    HOCK.G.root.visible = ONEIL.G.root.visible = false; }
  if (CAMQ) { const [w, bn, d, f] = CAMQ.split(':'), P = { C: CAMP, H: HOCK, O: ONEIL }[w], bp = wp(P.G.bones[bn]), dd = d.split(',').map(Number);
    ct = bp; cp = bp.clone().add(V(dd[0], dd[1], dd[2])); fov = +f || 30; near = 0.01; roll = 0; }
  camera.position.copy(cp); camera.up.set(Math.sin(roll * D2R), Math.cos(roll * D2R), 0); camera.lookAt(ct); camera.fov = fov; camera.near = near; camera.updateProjectionMatrix();
  return { b: nb, focus: ct }; }
let placeBallLater = null; const TRSEED = {};
const TR_KNEEL = curl(curl({ spine1: [-28, 0, 0], spine2: [-14, 0, 0], chest: [-8, 0, 0], neck: [20, 0, 0], head: [16, 0, 0], thighR: [80, 0, 8], shinR: [-95, 0, 0], footR: [0, 0, 0], thighL: [-4, 0, -6], shinL: [-100, 0, 0], footL: [-30, 0, 0] }, 'R', 12), 'L', 12);
// trainer: lowest point from his bones (he has no kit capsules)
function lowestOfG(Gx) { let lo = 1e9; for (const n of ['shinR', 'shinL', 'footR', 'footL', 'hips']) lo = Math.min(lo, wp(Gx.bones[n]).y - 0.06); return lo; } const CAMQ = Q.get('cam');
// ------------------------------------------------------------------ look + frame I/O
import { makeLook } from '/look.js';
const LOOK = makeLook(THREE, renderer, scene, camera, W, H, { overlays: [hud], aperture: 0.0008, maxblur: 0.006, rim: 1.6 });
let FOC = V(0, 1, 0), XRNOW = false;
function update(t) { t = clamp(t, 0, TOTAL - 1e-3); const r = shot(t); fitHud(); XRNOW = XRON; renderer.toneMappingExposure = XRON ? 0.42 : 1.05;   // the room goes dim behind the x-ray so the glow and the signals read
  const at = cart.visible ? cart.position.clone() : wp(G.bones.hips);
  sun.position.copy(at).add(V(8, 40, 14)); sun.target.position.copy(at); sun.target.updateMatrixWorld(); FOC = r.focus; return r; }
function stepTo(i) { return update(i / FPS); }
const draw = () => LOOK.render(FOC, { ao: !XRNOW, dof: !XRNOW });
const gl = renderer.getContext(), px = new Uint8Array(W * H * 4);
window.renderAll = async (f0, f1) => { for (let i = f0; i < f1; i++) { stepTo(i); draw(); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); await fetch('/frame', { method: 'POST', body: px }); } return 'ok'; };
window.renderAtT = t => { stepTo(Math.round(t * FPS)); draw(); return renderer.domElement.toDataURL('image/png'); };
// rig report for jointjerk: Campbell's joints, and any body point under the turf
window.rigReport = i => { const r = stepTo(i); const ang = {};
  for (const [tag, R_, P] of [['', RG, CAMP], ['h_', RH, HOCK], ['o_', RO, ONEIL]]) if (P.G.root.visible) for (const [k, v] of Object.entries(R_.LAST)) if (Array.isArray(v)) ang[tag + k] = v;
  return { beat: r.b, b: r.b, ang, hips: wp(G.bones.hips).toArray(), car: 0, show: G.root.visible, clip: clipList(PLAYERS) }; };
window.dbg = { THREE, scene, camera, G, RG, RH, RO, PLAYERS, shot, play, SIG, sigP, NERVES, stagePlayRaw, clipList, getTAB: () => TAB, TAU0, DTAU, place, draw, caps, segDist, contactPts, armSolve, ownHelmet, CAMP, HOCK, ONEIL, C_HIT, O_HIT, H_HIT, STAND, V, wp,
  report: i => { const st = stepTo(i); const r = x => x == null ? null : +x.toFixed(1), v = p => p.toArray().map(x => +x.toFixed(3));
    return { costs: { cL: r(RG.LAST.costL), cR: r(RG.LAST.costR), oL: r(RO.LAST.costL), oR: r(RO.LAST.costR), hR: r(RH.LAST.costR) }, clip: clipList(PLAYERS), cHelmet: v(wp(CAMP.helmet)), hWaist: v(wp(HOCK.G.bones.spine1)), cHips: v(wp(G.bones.hips)), cArmL: RG.LAST.armL, cArmR: RG.LAST.armR, miss: Object.fromEntries(Object.entries(LASTT).flatMap(([w, l]) => l.map(h => [w + h.S, +((w === 'c' ? RG : RO).palmW(h.S).distanceTo(h.p) * 100).toFixed(1)]))), shC: v(wp(G.bones.uarmR)), tgt: v(LASTT.c[1].p) }; } };
makeSeeds(); if (Q.get("table") === "1") buildTable();
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS); window.READY = true;
window.SCN = { THREE, scene, camera, stepTo, renderer, FPS, B, DUR, TOTAL };
