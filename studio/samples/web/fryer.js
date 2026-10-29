// "You just dropped a frozen turkey into a deep fryer." - a 3D Short: why a frozen turkey blows up a fryer, and the right way.
//   fryer.html?w=1080&h=1920            (times from fryer/times.json; one shot per narration line)
// Beats: 0 he drops the frozen bird into the hot oil, it erupts (hook) | 1 cutaway: the ice inside meets 350 F oil
//        2 cutaway: it flashes to steam, the oil boils over the rim | 3 it pours onto the flame: fireball, the siding catches; he jumps back
//        4 the fridge: thaw it, a day per five pounds | 5 out in the yard: flame off, lower it slowly | 6 wide: far from the house, extinguisher, no water
//        7 he holds the frozen bird over the oil again (loops)
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { loadGuy } from '/guy3d.js';

const Q = new URLSearchParams(location.search);
const W = +Q.get('w') || 720, H = +Q.get('h') || 1280;
const FPS = 30;
const TIMES = await (await fetch('/fryer/times.json')).json();
const B = TIMES.starts, DUR = TIMES.durs, TOTAL = TIMES.total;
const beatAt = t => { let i = 0; for (let k = 0; k < B.length; k++) if (t >= B[k]) i = k; return i; };
const clamp = (x, a, b) => Math.min(Math.max(x, a), b);
const sm = t => t * t * (3 - 2 * t);
const smooth = (a, b, x) => sm(clamp((x - a) / (b - a), 0, 1));
const lerp = (a, b, u) => a + (b - a) * u;
const D2R = Math.PI / 180;
function hash1(n) { const s = Math.sin(n * 127.1) * 43758.5453; return s - Math.floor(s); }
function vn1(x, seed) { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return lerp(hash1(i + seed * 17.3), hash1(i + 1 + seed * 17.3), u) * 2 - 1; }
const V = (x, y, z) => new THREE.Vector3(x, y, z);
function canvasTex(w, h, draw) { const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), c); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t; }
const qAA = (ax, deg) => new THREE.Quaternion().setFromAxisAngle(ax, deg * D2R);
const yawQ = deg => qAA(V(0, 1, 0), deg);
const fwdOf = yaw => V(-Math.sin(yaw * D2R), 0, -Math.cos(yaw * D2R));          // the way he faces (yaw 0 = -z)
const rightOf = yaw => V(Math.cos(yaw * D2R), 0, -Math.sin(yaw * D2R));         // his right
const wp = o => o.getWorldPosition(new THREE.Vector3()), wq = o => o.getWorldQuaternion(new THREE.Quaternion());

// ------------------------------------------------------------------ renderer, light
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(W, H);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05; renderer.outputColorSpace = THREE.SRGBColorSpace;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(45, W / H, 0.03, 300);
const ENVC = new THREE.Color(0xd9cbb6);
{ const pm = new THREE.PMREMGenerator(renderer); const es = new THREE.Scene(); es.background = ENVC; es.add(new THREE.HemisphereLight(0xfff2e0, 0x6a5040, 1));
  scene.environment = pm.fromScene(es, 0.04).texture; scene.environmentIntensity = 0.35; }
const hemi = new THREE.HemisphereLight(0xfff0dd, 0x6b5a48, 0.85); scene.add(hemi);
const sun = new THREE.DirectionalLight(0xffe3bf, 2.6); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
{ const S = sun.shadow.camera; S.left = -5; S.right = 5; S.top = 5; S.bottom = -5; S.near = 0.5; S.far = 30; sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.02; }
scene.add(sun); scene.add(sun.target);
const lamp = new THREE.PointLight(0xffc98a, 6, 9, 1.6); lamp.position.set(2.2, 1.9, -2.4); lamp.castShadow = false; scene.add(lamp);
const mat = (c, r = 0.8, m = 0) => new THREE.MeshStandardMaterial({ color: c, roughness: r, metalness: m });
const box = (w, h, d, x, y, z, m, r = 0, parent = scene) => { const o = new THREE.Mesh(r > 0 ? new RoundedBoxGeometry(w, h, d, 2, Math.min(r, 0.4 * Math.min(w, h, d))) : new THREE.BoxGeometry(w, h, d), m); o.position.set(x, y, z); o.castShadow = true; o.receiveShadow = true; parent.add(o); return o; };

const GLSLN = `float hh(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); } float vn(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f*f*(3.0-2.0*f); return mix(mix(hh(i), hh(i+vec2(1,0)), u.x), mix(hh(i+vec2(0,1)), hh(i+vec2(1,1)), u.x), u.y); }`;
// ------------------------------------------------------------------ the owner (same guy as always)
const G = await loadGuy(THREE, '/char/guy', {});
scene.add(G.root); G.root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
const HIP = V(0, 0.95, 0);
const LIMITS = {
  spine1: [[-30, 20], [-20, 20], [-15, 15]], spine2: [[-30, 20], [-20, 20], [-15, 15]], chest: [[-25, 20], [-20, 20], [-15, 15]],
  neck: [[-35, 35], [-50, 50], [-20, 20]], head: [[-30, 30], [-40, 40], [-20, 20]],
  thighR: [[-30, 120], [-30, 30], [-25, 45]], thighL: [[-30, 120], [-30, 30], [-45, 25]],
  shinR: [[-150, 0], [-5, 5], [-5, 5]], shinL: [[-150, 0], [-5, 5], [-5, 5]],
  footR: [[-45, 30], [-15, 15], [-15, 15]], footL: [[-45, 30], [-15, 15], [-15, 15]],
};
const ARM_LIM = [[-50, 170], [-25, 170], [-60, 60], [0, 145], [-80, 80], [-65, 70], [-25, 25]];
function softc(x, lo, hi, knee = 6) { if (x > hi - knee) return hi - knee + knee * Math.tanh((x - (hi - knee)) / knee); if (x < lo + knee) return lo + knee - knee * Math.tanh(((lo + knee) - x) / knee); return x; }
const FINGERS = ['index', 'middle', 'ring', 'pinky'];
function curl(p, S, c, th = c) { for (const f of FINGERS) { p[f + '1' + S] = [0, 0, (S === 'R' ? -1 : 1) * c * 0.9]; p[f + '2' + S] = [0, 0, (S === 'R' ? -1 : 1) * c]; } p['thumb1' + S] = [0, 0, (S === 'R' ? -1 : 1) * th * 0.4]; return p; }
const A = (fl, ab, ro, el, pr = 0, wf = 0, wd = 0) => [fl, ab, ro, el, pr, wf, wd];
const ARM0 = A(4, 8, 0, 14);
function eul(p, n) { return p[n] || (n === 'armR' || n === 'armL' ? ARM0 : [0, 0, 0]); }
function mixPose(a, b, k) { const o = {}; for (const n of new Set([...Object.keys(a), ...Object.keys(b)])) { const x = eul(a, n), y = eul(b, n); o[n] = x.map((v, i) => lerp(v, y[i] ?? 0, k)); } return o; }
function addPose(a, d) { const o = { ...a }; for (const [n, v] of Object.entries(d)) { const x = eul(o, n); o[n] = x.map((w, i) => w + (v[i] || 0)); } return o; }
function keyed(keys, t) { if (t <= keys[0][0]) return keys[0][1]; for (let i = 0; i < keys.length - 1; i++) { const [t0, a] = keys[i], [t1, b] = keys[i + 1]; if (t <= t1) return mixPose(a, b, sm((t - t0) / (t1 - t0))); } return keys[keys.length - 1][1]; }
const STAND = curl(curl({ armR: A(6, 8, 0, 16), armL: A(6, 8, 0, 16), neck: [2, 0, 0] }, 'R', 26), 'L', 26);
const qTmp = new THREE.Quaternion(), eTmp = new THREE.Euler();
// one rig per person (the same body plan): pose, arm angles, hand solve, feet, body-relative points
function makeRig(Gx, tag) {
  const BONES = Object.keys(Gx.bones); Gx.reset();
  const ARMREST = {}, HANDREST = {};
  for (const S of ['R', 'L']) { const af = Gx.REST['farm' + S].axis.clone();
    ARMREST[S] = { s: S === 'R' ? 1 : -1, a0: Gx.REST['uarm' + S].axis.clone(), af, hinge: new THREE.Vector3().crossVectors(af, V(0, 0, -1)).normalize() };
    const h = Gx.man.hands[S]; HANDREST[S] = { u: V(...h.u), n: V(...h.n), w: V(...h.w) }; }
  function armQuats(S, a) { const R_ = ARMREST[S], h = HANDREST[S], [flex, abd, rot, el, pro, wf = 0, wd = 0] = a;
    const rv = V(flex, 0, R_.s * abd); const ang = rv.length();
    const d = ang > 1e-6 ? V(0, -1, 0).applyQuaternion(qAA(rv.clone().normalize(), ang)) : V(0, -1, 0);
    return { Lu: new THREE.Quaternion().setFromUnitVectors(R_.a0, d).multiply(qAA(R_.a0, R_.s * rot)), Lf: qAA(R_.hinge, el).multiply(qAA(R_.af, R_.s * pro)), Lh: qAA(h.w, R_.s * wf).multiply(qAA(h.n, R_.s * wd)) }; }
  function setArm(S, a) { const { Lu, Lf, Lh } = armQuats(S, a);
    Gx.bones['uarm' + S].quaternion.copy(Lu); Gx.bones['uarmTwist' + S].quaternion.identity(); Gx.bones['farm' + S].quaternion.copy(Lf); Gx.bones['farmTwist' + S].quaternion.identity(); Gx.bones['hand' + S].quaternion.copy(Lh); }
  const R = { G: Gx, tag, LAST: {}, HANDREST, setArm };
  R.applyPose = (p, root) => { const lim = {};
    for (const n of BONES) { if (/^(uarm|uarmTwist|farm|farmTwist|hand)[RL]$/.test(n)) continue;
      const b = Gx.bones[n]; let e = eul(p, n); if (LIMITS[n]) e = e.map((v, i) => softc(v, LIMITS[n][i][0], LIMITS[n][i][1]));
      lim[n] = e; b.position.copy(Gx.REST[n].pos); b.quaternion.copy(Gx.REST[n].q).multiply(qTmp.setFromEuler(eTmp.set(e[0] * D2R, e[1] * D2R, e[2] * D2R))); }
    for (const S of ['R', 'L']) { const a = eul(p, 'arm' + S).map((v, i) => softc(v, ARM_LIM[i][0], ARM_LIM[i][1], i === 3 ? 4 : 5)); lim['arm' + S] = a; setArm(S, a); }
    const q = new THREE.Quaternion().setFromEuler(new THREE.Euler((root.tilt || 0) * D2R, (root.yaw || 0) * D2R, (root.roll || 0) * D2R, 'YXZ'));
    Gx.root.quaternion.copy(q); Gx.root.position.copy(V(root.x, root.y, root.z)).sub(HIP.clone().applyQuaternion(q)); Gx.root.updateMatrixWorld(true);
    R.LAST = lim; };
  R.PALM = S => HANDREST[S].u.clone().multiplyScalar(0.06).addScaledVector(HANDREST[S].n, 0.012);
  R.palmW = S => R.PALM(S).applyMatrix4(Gx.bones['hand' + S].matrixWorld);
  function torsoInside(p) { const c = wp(Gx.bones.chest), sp = wp(Gx.bones.spine1), iq = wq(Gx.bones.chest).invert(), d = p.clone().sub(c).applyQuaternion(iq);
    if (d.y > 0.22 || p.clone().sub(sp).applyQuaternion(iq).y < -0.2) return 0; const r = Math.hypot(d.x / 0.17, d.z / 0.13); return r < 1 ? (1 - r) * 0.13 : 0; }
  const _m = new THREE.Matrix4(), _q = new THREE.Quaternion();
  function handFK(S, a) { setArm(S, a); const hb = Gx.bones['hand' + S]; Gx.bones['uarm' + S].updateMatrixWorld(true);
    const M = _m.copy(hb.matrixWorld); const qh = _q.setFromRotationMatrix(M);
    return { p: R.PALM(S).applyMatrix4(M), n: HANDREST[S].n.clone().applyQuaternion(qh), w: HANDREST[S].w.clone().applyQuaternion(qh), u: HANDREST[S].u.clone().applyQuaternion(qh), el: wp(Gx.bones['farm' + S]), sh: wp(Gx.bones['uarm' + S]) }; }
  R.handFK = handFK;
  const MEM = {}; R.MEM = MEM;
  R.solveHand = (tg, key, frame) => { const S = tg.S;
    const cost = a => { const f = handFK(S, a);
      let c = tg.free ? 0 : f.p.distanceToSquared(tg.p) / (0.006 * 0.006);      // free: only the extra cost places the hand (a tool tip, say)
      if (tg.anchor) for (let i = 0; i < 7; i++) c += ((a[i] - tg.anchor[i]) / 2) ** 2;
      if (tg.n) c += (1 - f.n.dot(tg.n)) * 40; if (tg.w) c += (1 - f.w.dot(tg.w)) * 25; if (tg.u) c += (1 - f.u.dot(tg.u)) * 25;
      for (let i = 0; i < 7; i++) { const [lo, hi] = ARM_LIM[i], mid = [20, 15, 0, 60, 0, 0, 0][i]; c += 0.6 * ((a[i] - mid) / (hi - lo)) ** 2; }
      const ins = torsoInside(f.el) + torsoInside(f.el.clone().lerp(f.p, 0.5)); c += (ins / 0.01) ** 2;
      if (prev) for (let i = 0; i < 7; i++) c += ((a[i] - prev[i]) / 3) ** 2;
      if (tg.extra) c += tg.extra(f);
      return c; };
    const m = MEM[key]; let prev = m && m.frame === frame - 1 ? m.a : (tg.seedIsPrev && tg.seed ? tg.seed : null);
    const COLD = [A(40, 15, 0, 80, 0), A(60, 25, 20, 60, 40), A(30, 40, -20, 100, -30), A(80, 10, 0, 110, 60), A(50, 30, 30, 40, 70), A(20, 20, -30, 120, -60), A(60, 10, -10, 100, 75), A(40, 20, 10, 90, -75)];
    const descend = (s0, big) => { let a = s0.map((v, i) => clamp(v, ARM_LIM[i][0], ARM_LIM[i][1])), ca = cost(a);
      for (let step = big; step >= 0.25; step /= 2) { let imp = true, g = 0;
        while (imp && g++ < 10) { imp = false; for (let i = 0; i < 7; i++) for (const sg of [1, -1]) { const b = a.slice(); b[i] = clamp(b[i] + sg * step, ARM_LIM[i][0], ARM_LIM[i][1]); const cb = cost(b); if (cb < ca - 1e-9) { a = b; ca = cb; imp = true; } } } }
      return { a, c: ca }; };
    let best = null;
    if (!prev && tg.seed) { const r = descend(tg.seed, 8); if (r.c < 8) best = r; }
    if (!best) for (const s0 of prev ? [prev] : (tg.seed ? [tg.seed, ...COLD] : COLD)) { const r = descend(s0, prev ? 4 : 16); if (!best || r.c < best.c) best = r; }
    if (!prev) for (let r = 0; r < 4; r++) { const p2 = descend(best.a, 6 / (r + 1)); if (p2.c < best.c - 1e-6) best = p2; else break; }   // a cold start: polish (coordinate descent stalls in long valleys)
    if (prev && best.c > 20 && !tg.local) for (const s0 of (tg.seed ? [tg.seed, ...COLD] : COLD)) { const r = descend(s0, 16); if (r.c < best.c) best = r; }
    MEM[key] = { frame, a: best.a }; const pv = prev; prev = null; best.miss = cost(best.a); prev = pv; return best; };
  const fingers = h => { const pp = {}; curl(pp, h.S, h.c ?? 30, h.th); if (h.opp) pp['thumb1' + h.S][0] = -h.opp; if (h.point) { pp['index1' + h.S] = [0, 0, -5]; pp['index2' + h.S] = [0, 0, -5]; }
    for (const [n, e] of Object.entries(pp)) Gx.bones[n].quaternion.copy(Gx.REST[n].q).multiply(qTmp.setFromEuler(eTmp.set(e[0] * D2R, e[1] * D2R, e[2] * D2R))); };
  const withContact = h => { if (!R.contactCost) return h; const cc = R.contactCost(h), ex = h.extra; return { ...h, extra: ex ? f => ex(f) + cc(f) : cc }; };
  R.hands = (list, key, frame) => { for (const h0 of list) { const h = withContact(h0);
      let posed; if (h.from) { fingers(h.from); posed = R.solveHand(withContact(h.from), key + (h.from.mem || 'from' + h.S), frame).a; } else posed = (R.LAST['arm' + h.S] || ARM0).slice();
      fingers(h); const sol = R.solveHand(h, h.memAbs || key + (h.mem || h.S), frame);
      const bl = h.blend ?? 1; let a = sol.a, c = sol.miss;
      if (h.blend !== undefined || h.from) {                    // moving from one hold (or the pose) to another: joint angles ease across, and a small
        const al = posed.map((v, i) => lerp(v, sol.a[i], bl));   // nudge (anchored to that eased arm) keeps the hand, fingers and elbow out of his body
        const fc = h.from ? (h.from.c ?? 30) : 26, ft = h.from ? (h.from.th ?? fc) : 26;
        fingers({ S: h.S, c: lerp(fc, h.c ?? 30, bl), th: lerp(ft, h.th ?? (h.c ?? 30), bl), point: h.point && bl > 0.5 });
        const ns = R.solveHand(withContact({ S: h.S, free: true, soft: h.soft, p: handFK(h.S, al).p, anchor: al, seed: al, seedIsPrev: true, local: true }), key + 'nudge' + h.S, -99);
        a = ns.a; if (bl < 0.999) c = null; }                    // on the way there it isn't holding anything yet (the clip check covers the path)
      setArm(h.S, a); R.LAST['arm' + h.S] = a; R.LAST['cost' + h.S] = c; } };
  R.untwist = () => { for (const S of ['R', 'L']) { const ua = Gx.bones['uarm' + S], ut = Gx.bones['uarmTwist' + S]; ua.quaternion.multiply(ut.quaternion); ut.quaternion.identity(); } Gx.untwist(); };
  R.foot = (S, f, pole, q) => Gx.legIK(S, f, pole, q);
  Gx.reset(); Gx.root.updateMatrixWorld(true);
  const ML = V(0, Gx.man.mouthY, Gx.man.mouthZ ?? -0.105).applyMatrix4(Gx.bones.head.matrixWorld.clone().invert());
  R.mouthW = () => ML.clone().applyMatrix4(Gx.bones.head.matrixWorld);
  const TIPSEG = {}; for (const S of ['R', 'L']) for (const f of ['index', 'middle', 'pinky', 'thumb']) { const b1 = Gx.bones[f + '1' + S], b2 = Gx.bones[f + '2' + S]; TIPSEG[f + S] = wp(b2).sub(wp(b1)).multiplyScalar(0.95).applyQuaternion(wq(b2).invert()); }
  R.tip = (f, S) => { const b2 = Gx.bones[f + '2' + S]; return wp(b2).add(TIPSEG[f + S].clone().applyQuaternion(wq(b2))); };
  return R;
}
const RG = makeRig(G, 'him');
G.reset(); G.root.updateMatrixWorld(true);
const EAR_L = V(0.08, 1.64, 0.01).applyMatrix4(G.bones.head.matrixWorld.clone().invert());
// ================================================================== FROZEN TURKEY
// ------------------------------------------------------------------ the backyard: grass, a deck by the house (the wrong spot), the open yard (the right spot)
renderer.localClippingEnabled = true;
scene.remove(lamp);
hemi.color.set(0xdcecff); hemi.groundColor.set(0x5f6e3e); hemi.intensity = 0.9;
const SKY = new THREE.Color(0xa6cdee); scene.background = SKY;
const ground = new THREE.Mesh(new THREE.PlaneGeometry(90, 90).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ roughness: 0.95,
  map: (() => { const t = canvasTex(512, 512, g => { g.fillStyle = '#5d8a3a'; g.fillRect(0, 0, 512, 512);
    for (let i = 0; i < 9000; i++) { const c = 70 + Math.random() * 70; g.fillStyle = `rgba(${c * 0.6 | 0},${c + 40 | 0},${c * 0.35 | 0},0.5)`; g.fillRect(Math.random() * 512, Math.random() * 512, 2, 5); } });
    t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(40, 40); return t; })() }));
ground.receiveShadow = true; scene.add(ground);
// the house + deck move together: near (wall 1.1 m behind the fryer) or far (wall 6.6 m away, fryer on the grass)
const world = new THREE.Group(); scene.add(world);
const HZ = -1.1, FARZ = -5.5;
let HOUSEZ = HZ;
const deck = new THREE.Mesh(new THREE.PlaneGeometry(7, 2.5).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ roughness: 0.8,
  map: canvasTex(1024, 366, g => { for (let i = 0; i < 26; i++) { const c = 150 + 25 * Math.random(); g.fillStyle = `rgb(${c},${c * 0.68 | 0},${c * 0.45 | 0})`; g.fillRect(i * 40, 0, 40, 366);
    g.fillStyle = 'rgba(40,24,12,0.7)'; g.fillRect(i * 40, 0, 3, 366); for (let k = 0; k < 12; k++) { g.fillStyle = `rgba(90,55,30,${0.08 + Math.random() * 0.1})`; g.fillRect(i * 40 + Math.random() * 36, Math.random() * 366, 2, 40 + Math.random() * 80); } } }) }));
deck.position.set(0, 0.003, HZ + 1.25); deck.receiveShadow = true; world.add(deck);
const sidingTex = canvasTex(512, 512, g => { g.fillStyle = '#c3cfd6'; g.fillRect(0, 0, 512, 512); for (let i = 0; i < 16; i++) { g.fillStyle = 'rgba(60,75,85,0.35)'; g.fillRect(0, i * 32 + 28, 512, 4); g.fillStyle = 'rgba(255,255,255,0.25)'; g.fillRect(0, i * 32, 512, 3); } });
sidingTex.wrapS = sidingTex.wrapT = THREE.RepeatWrapping; sidingTex.repeat.set(5, 2.5);
const houseWall = box(10, 3.2, 0.2, 0, 1.6, HZ - 0.1, new THREE.MeshStandardMaterial({ map: sidingTex, roughness: 0.8 }), 0, world);
box(10.6, 0.16, 0.7, 0, 3.22, HZ + 0.15, mat(0xf2f2ee, 0.6), 0, world);                                  // the eave
box(10, 0.3, 0.06, 0, 0.15, HZ + 0.03, mat(0x8a8a86, 0.9), 0, world);                                   // the foundation strip
{ const glass = new THREE.MeshStandardMaterial({ color: 0x4a6a86, roughness: 0.08, metalness: 0.5 });
  for (const [x, y, w, h] of [[-1.7, 1.05, 0.95, 2.1], [1.4, 1.65, 1.2, 1.1], [3.6, 1.65, 1.2, 1.1]]) { box(w + 0.14, h + 0.14, 0.05, x, y, HZ + 0.02, mat(0xf6f4ee, 0.5), 0, world); box(w, h, 0.06, x, y, HZ + 0.03, glass, 0, world); }
  box(0.06, 1.1, 0.07, 1.4, 1.65, HZ + 0.04, mat(0xf6f4ee, 0.5), 0, world); box(0.06, 1.1, 0.07, 3.6, 1.65, HZ + 0.04, mat(0xf6f4ee, 0.5), 0, world); }
// scorch on the siding (shows after the fire climbs it)
const scorchM = new THREE.MeshBasicMaterial({ map: canvasTex(256, 256, g => { const gr = g.createRadialGradient(128, 160, 10, 128, 150, 128); gr.addColorStop(0, 'rgba(10,8,6,0.95)'); gr.addColorStop(0.6, 'rgba(25,18,12,0.6)'); gr.addColorStop(1, 'rgba(30,20,10,0)'); g.fillStyle = gr; g.fillRect(0, 0, 256, 256); }), transparent: true, opacity: 0, depthWrite: false });
const scorch = new THREE.Mesh(new THREE.PlaneGeometry(1.8, 2.4), scorchM); scorch.position.set(0, 1.25, HZ + 0.005); world.add(scorch);
// fence and a tree for the yard
{ const fm = mat(0xb08a5a, 0.85);
  for (const x of [-5, 5]) { for (let z = -9; z < 9; z += 0.16) box(0.02, 1.5, 0.13, x, 0.75, z, fm, 0, scene); box(0.05, 0.08, 18, x + Math.sign(x) * 0.03, 1.2, 0, fm, 0, scene); }
  const tr = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.18, 2.6, 12), mat(0x5a3f28, 0.9)); tr.position.set(-3.6, 1.3, 3.2); tr.castShadow = true; scene.add(tr);
  for (const [x, y, z, r] of [[-3.6, 3.0, 3.2, 1.1], [-3.0, 2.6, 3.0, 0.8], [-4.1, 2.5, 3.5, 0.8], [-3.6, 2.4, 2.6, 0.7]]) { const b = new THREE.Mesh(new THREE.IcosahedronGeometry(r, 2), mat(0x4c7a34, 0.9)); b.position.set(x, y, z); b.castShadow = true; scene.add(b); }
  for (const [x, z] of [[-3.5, 0.2], [2.6, 0.1], [4.2, 0.0]]) { const b = new THREE.Mesh(new THREE.IcosahedronGeometry(0.45, 2), mat(0x3f6e2c, 0.9)); b.position.set(x, 0.3, HZ + z + 0.35); b.scale.y = 0.8; world.add(b); } }

// ------------------------------------------------------------------ the fryer: a stand with a propane burner, a tall pot of oil, a tank, a flame knob on a post
const POT = V(0, 0.32, 0);                                         // pot bottom centre
const POTR = 0.17, POTH = 0.40, RIM = POT.y + POTH;
const OIL0 = POT.y + 0.17;                                         // the oil line with nothing in it
const ROD_L = 0.6, HR = 0.016, GRIP = 0.012;                       // the lifting rod: rack base to the grip's centre; the grip's radius
const KNOB = V(0.07, 0.9, 0.33);                                   // the flame knob, on a post at his left (facing him, tilted up)
const KAX = V(0.6, 0.8, 0).normalize();
const STANDP = V(0.40, 0, 0.03);                                   // where he stands (facing -x)
const CUTP = new THREE.Plane(V(0, 0, -1), 0);                      // cutaway keeps z <= 0
const CLIP = [CUTP];
const steel = new THREE.MeshStandardMaterial({ color: 0xb4b8be, roughness: 0.32, metalness: 0.85, side: THREE.DoubleSide });
const iron = new THREE.MeshStandardMaterial({ color: 0x26262a, roughness: 0.6, metalness: 0.5 });
const stand = new THREE.Group(); scene.add(stand);
{ for (let i = 0; i < 3; i++) { const a = i / 3 * Math.PI * 2 + 0.5, top = V(Math.cos(a) * 0.19, 0.29, Math.sin(a) * 0.19), bot = V(Math.cos(a) * 0.25, 0, Math.sin(a) * 0.25);
    const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.011, 0.011, top.distanceTo(bot), 8), iron); leg.position.copy(top).add(bot).multiplyScalar(0.5); leg.quaternion.setFromUnitVectors(V(0, 1, 0), top.clone().sub(bot).normalize()); leg.castShadow = true; stand.add(leg); }
  const ring = new THREE.Mesh(new THREE.TorusGeometry(0.19, 0.012, 8, 40).rotateX(Math.PI / 2), iron); ring.position.y = 0.3; stand.add(ring);
  for (let i = 0; i < 3; i++) { const a = i / 3 * Math.PI * 2 + 1.55; const arm = box(0.2, 0.012, 0.02, Math.cos(a) * 0.1, 0.305, Math.sin(a) * 0.1, iron, 0, stand); arm.rotation.y = -a; }
  const burner = new THREE.Mesh(new THREE.CylinderGeometry(0.075, 0.06, 0.035, 24), iron); burner.position.y = 0.245; stand.add(burner);
}
const kpost = new THREE.Group(); scene.add(kpost);                // the knob post (bolted to the ring) and its little valve box
{ const post = new THREE.Mesh(new THREE.CylinderGeometry(0.01, 0.01, 0.9, 8), iron); post.position.set(KNOB.x + 0.02, 0.45, KNOB.z); post.castShadow = true; kpost.add(post);
  box(0.05, 0.06, 0.06, KNOB.x - 0.005, KNOB.y - 0.012, KNOB.z, mat(0xb02020, 0.4), 0.008, kpost); }
const knobG = new THREE.Group(); knobG.position.copy(KNOB); knobG.quaternion.setFromUnitVectors(V(1, 0, 0), KAX); scene.add(knobG);
const knobSpin = new THREE.Group(); knobG.add(knobSpin);
{ const b = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.023, 0.024, 24).rotateZ(Math.PI / 2), mat(0x1c1c20, 0.35, 0.3)); b.position.x = 0.012; knobSpin.add(b);
  const ridge = new THREE.Mesh(new THREE.BoxGeometry(0.008, 0.034, 0.007), mat(0xd8d8dc, 0.4)); ridge.position.x = 0.025; knobSpin.add(ridge); }
// the pot: lathe body, two side handles; the oil inside (scaled to its level)
const pot = new THREE.Group(); pot.position.copy(POT); scene.add(pot);
const potBody = new THREE.Mesh(new THREE.LatheGeometry([[0, 0], [POTR - 0.012, 0], [POTR, 0.012], [POTR, POTH], [POTR + 0.007, POTH + 0.004]].map(([x, y]) => new THREE.Vector2(x, y)), 64), steel);
potBody.castShadow = true; pot.add(potBody);
for (const s of [-1, 1]) { const hd = new THREE.Mesh(new THREE.TorusGeometry(0.03, 0.006, 6, 16, Math.PI), steel); hd.position.set(0, POTH - 0.05, s * (POTR + 0.004)); hd.rotation.y = s > 0 ? 0 : Math.PI; hd.rotation.z = 0; pot.add(hd); }
const oilM = new THREE.MeshStandardMaterial({ color: 0xc8962a, emissive: 0x5a2a00, emissiveIntensity: 0.35, roughness: 0.06, metalness: 0.1, transparent: true, opacity: 0.86, side: THREE.DoubleSide });
const oil = new THREE.Mesh(new THREE.CylinderGeometry(POTR - 0.004, POTR - 0.004, 1, 56).translate(0, 0.5, 0), oilM); oil.position.y = 0.006; pot.add(oil);
// the oil sheet pouring down the outside of the pot
const sheetM = new THREE.MeshStandardMaterial({ color: 0xd8a032, emissive: 0x6a3400, emissiveIntensity: 0.4, roughness: 0.1, transparent: true, opacity: 0, side: THREE.DoubleSide, depthWrite: false });
const sheet = new THREE.Mesh(new THREE.CylinderGeometry(POTR + 0.008, POTR + 0.012, 1, 56, 1, true).translate(0, -0.5, 0), sheetM); scene.add(sheet);
const poolM = new THREE.MeshStandardMaterial({ color: 0x8a5a14, emissive: 0x3a1800, roughness: 0.1, transparent: true, opacity: 0.85 });
const pool = new THREE.Mesh(new THREE.CircleGeometry(1, 40).rotateX(-Math.PI / 2), poolM); pool.position.set(0, 0.006, 0); scene.add(pool);
// cut faces (cutaway only): oil slab, pot floor and walls
const cutFaces = new THREE.Group(); cutFaces.position.copy(POT); scene.add(cutFaces); cutFaces.visible = false;
const oilCut = new THREE.Mesh(new THREE.PlaneGeometry(2 * (POTR - 0.004), 1).translate(0, 0.5, 0), new THREE.MeshStandardMaterial({ color: 0xd8a432, emissive: 0x6a3a00, emissiveIntensity: 0.5, roughness: 0.3, transparent: true, opacity: 0.5, depthWrite: false, side: THREE.DoubleSide }));
oilCut.position.set(0, 0.006, -0.0015); cutFaces.add(oilCut);
{ const dm = new THREE.MeshStandardMaterial({ color: 0x5a5c62, roughness: 0.4, metalness: 0.6, side: THREE.DoubleSide });
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(2 * POTR, 0.006), dm); fl.position.set(0, 0.003, 0.0006); cutFaces.add(fl);
  for (const sx of [-1, 1]) { const wl = new THREE.Mesh(new THREE.PlaneGeometry(0.005, POTH), dm); wl.position.set(sx * (POTR + 0.0025), POTH / 2, 0.0006); cutFaces.add(wl); } }
// the propane tank behind the fryer, the hose
{ const tm = mat(0xeeeeea, 0.45, 0.2), tank = new THREE.Group(); tank.position.set(-0.42, 0, -0.42); scene.add(tank);
  const body = new THREE.Mesh(new THREE.CylinderGeometry(0.155, 0.155, 0.34, 28), tm); body.position.y = 0.22; tank.add(body);
  for (const y of [0.05, 0.39]) { const d = new THREE.Mesh(new THREE.SphereGeometry(0.155, 28, 12), tm); d.scale.y = 0.4; d.position.y = y; tank.add(d); }
  const col = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.09, 0.1, 20, 1, true), tm); col.position.y = 0.48; tank.add(col);
  const v = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 0.06, 10), mat(0x9a8a40, 0.4, 0.7)); v.position.y = 0.46; tank.add(v);
  tank.traverse(o => { if (o.isMesh) o.castShadow = true; });
  const hose = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3([V(-0.42, 0.49, -0.42), V(-0.3, 0.3, -0.3), V(-0.15, 0.04, -0.15), V(-0.06, 0.15, -0.04), V(-0.04, 0.24, 0)]), 40, 0.008, 6), mat(0x111111, 0.6)); scene.add(hose); }
// a fire extinguisher (the right way only)
const ext = new THREE.Group(); ext.position.set(0.62, 0, 0.5); scene.add(ext);
{ const r = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.36, 20), mat(0xc81e1e, 0.35, 0.2)); r.position.y = 0.18; ext.add(r);
  const t = new THREE.Mesh(new THREE.SphereGeometry(0.06, 20, 10, 0, Math.PI * 2, 0, Math.PI / 2), mat(0xc81e1e, 0.35, 0.2)); t.position.y = 0.36; ext.add(t);
  box(0.03, 0.06, 0.03, 0, 0.43, 0, mat(0x222222, 0.5), 0, ext); box(0.09, 0.012, 0.02, 0.03, 0.46, 0, mat(0x222222, 0.5), 0, ext);
  const lab = new THREE.Mesh(new THREE.PlaneGeometry(0.08, 0.12), new THREE.MeshStandardMaterial({ map: canvasTex(64, 96, g => { g.fillStyle = '#f4f0e6'; g.fillRect(0, 0, 64, 96); g.fillStyle = '#222'; g.font = 'bold 22px sans-serif'; g.fillText('ABC', 10, 56); }) }));
  lab.position.set(0, 0.2, 0.061); ext.add(lab); ext.rotation.y = -0.6; ext.traverse(o => { if (o.isMesh) o.castShadow = true; }); }

// ------------------------------------------------------------------ the turkey (on the fryer's rack + rod), and a second one for the fridge
const frostTex = canvasTex(256, 256, g => { g.fillStyle = '#eef5fb'; g.fillRect(0, 0, 256, 256);
  for (let i = 0; i < 1400; i++) { g.fillStyle = Math.random() < 0.5 ? 'rgba(255,255,255,0.9)' : 'rgba(170,200,230,0.5)'; g.fillRect(Math.random() * 256, Math.random() * 256, 1 + Math.random() * 3, 1 + Math.random() * 3); }
  g.strokeStyle = 'rgba(255,255,255,0.7)'; for (let i = 0; i < 90; i++) { const x = Math.random() * 256, y = Math.random() * 256, a = Math.random() * 6.28; g.beginPath(); g.moveTo(x, y); g.lineTo(x + 9 * Math.cos(a), y + 9 * Math.sin(a)); g.stroke(); } });
const skinTex = canvasTex(256, 256, g => { g.fillStyle = '#ecc7a0'; g.fillRect(0, 0, 256, 256); for (let i = 0; i < 2500; i++) { g.fillStyle = `rgba(${200 + Math.random() * 40 | 0},${150 + Math.random() * 30 | 0},${110 + Math.random() * 30 | 0},0.35)`; g.beginPath(); g.arc(Math.random() * 256, Math.random() * 256, 1 + Math.random() * 1.6, 0, 6.28); g.fill(); } });
function makeTurkey(withRack) {
  const g = new THREE.Group();
  const skinM = new THREE.MeshStandardMaterial({ map: skinTex, roughness: 0.5 });
  const frostM = new THREE.MeshStandardMaterial({ map: frostTex, roughness: 0.3, transparent: true, opacity: 1, depthWrite: false, side: THREE.DoubleSide });
  const add = (geo, p, s, q) => { for (const [m, k] of [[skinM, 1], [frostM, 1.04]]) { const o = new THREE.Mesh(geo, m); o.position.copy(p); o.scale.copy(s).multiplyScalar(k); if (q) o.quaternion.copy(q); o.castShadow = m === skinM; o.renderOrder = m === frostM ? 3 : 0; g.add(o); } };
  const sph = new THREE.SphereGeometry(1, 40, 28), C0 = V(0, 0.09, 0);
  add(sph, C0, V(0.125, 0.082, 0.1));                                                   // the body, lying breast up; legs at the back (-x)
  for (const s of [-1, 1]) { add(sph, V(0.02, 0.112, s * 0.05), V(0.095, 0.05, 0.045));              // the two breast halves
    const dir = V(-0.62, 0.62, s * 0.3).normalize(), q = new THREE.Quaternion().setFromUnitVectors(V(0, 1, 0), dir), c = V(-0.075, 0.13, s * 0.055).addScaledVector(dir, 0.04);
    add(new THREE.CapsuleGeometry(0.03, 0.06, 6, 14), c, V(1, 1, 1), q);                                 // a drumstick
    add(sph, c.clone().addScaledVector(dir, 0.062), V(0.02, 0.02, 0.02));                                // its knobby end
    add(sph, V(0.035, 0.075, s * 0.095), V(0.055, 0.03, 0.022)); }                                       // a wing, tucked
  const cavM = new THREE.MeshStandardMaterial({ color: 0x9a5848, roughness: 0.7, side: THREE.BackSide });
  const cav = new THREE.Mesh(sph, cavM); cav.position.set(-0.012, 0.085, 0); cav.scale.set(0.085, 0.05, 0.062); g.add(cav);
  const iceM = new THREE.MeshStandardMaterial({ color: 0xcdeeff, emissive: 0x5aa8e0, emissiveIntensity: 0.4, roughness: 0.15, metalness: 0.1, transparent: true, opacity: 0.95, flatShading: true, side: THREE.DoubleSide });
  const ice = new THREE.Mesh(new THREE.IcosahedronGeometry(1, 1), iceM); ice.position.set(-0.012, 0.082, 0); g.add(ice);
  const sh = new THREE.Shape(); sh.absellipse(0, 0.09, 0.125, 0.082, 0, Math.PI * 2); const hole = new THREE.Path(); hole.absellipse(-0.012, 0.085, 0.085, 0.05, 0, Math.PI * 2, true); sh.holes.push(hole);
  const cutM = new THREE.MeshStandardMaterial({ color: 0xe9b49c, roughness: 0.6, side: THREE.DoubleSide });
  const cut = new THREE.Mesh(new THREE.ShapeGeometry(sh, 40), cutM); cut.position.z = -0.0006; cut.visible = false; g.add(cut);
  const mats = [skinM, frostM, cavM, iceM, cutM];
  const ICE = V(0.062, 0.036, 0.046);
  if (withRack) { const wire = steel, BR = 0.15, BH = 0.2;                                             // a wire basket with a bail; the lifting rod and its grip
    for (const y of [0.004, 0.1, BH]) { const ring = new THREE.Mesh(new THREE.TorusGeometry(BR, 0.003, 6, 48).rotateX(Math.PI / 2), wire); ring.position.y = y; g.add(ring); }
    for (let i = 0; i < 14; i++) { const a = i / 14 * Math.PI * 2, bar = new THREE.Mesh(new THREE.CylinderGeometry(0.0025, 0.0025, BH, 5), wire); bar.position.set(Math.cos(a) * BR, BH / 2, Math.sin(a) * BR); g.add(bar); }
    for (const x of [-0.1, -0.05, 0, 0.05, 0.1]) { const l = 2 * Math.sqrt(BR * BR - x * x); const c1 = new THREE.Mesh(new THREE.CylinderGeometry(0.0025, 0.0025, l, 5).rotateX(Math.PI / 2), wire); c1.position.set(x, 0.004, 0); g.add(c1);
      const c2 = new THREE.Mesh(new THREE.CylinderGeometry(0.0025, 0.0025, l, 5).rotateZ(Math.PI / 2), wire); c2.position.set(0, 0.004, x); g.add(c2); }
    const bail = new THREE.Mesh(new THREE.TorusGeometry(BR, 0.0035, 6, 40, Math.PI), wire); bail.rotation.y = Math.PI / 2; bail.position.y = BH; bail.scale.set(1, 0.5, 1); g.add(bail);
    const rod = new THREE.Mesh(new THREE.CylinderGeometry(0.006, 0.006, ROD_L - BH - 0.075), steel); rod.position.y = (ROD_L + BH + 0.075) / 2; g.add(rod);
    const grip = new THREE.Mesh(new THREE.CylinderGeometry(HR, HR, 0.12, 16), mat(0x1a1a1c, 0.6)); grip.position.y = ROD_L; g.add(grip);
    const hook = new THREE.Mesh(new THREE.TorusGeometry(0.022, 0.005, 6, 20, Math.PI * 1.4), steel); hook.position.y = ROD_L + 0.085; g.add(hook); }
  return { g, skinM, frostM, ice, cut, mats, ICE,
    frost(k) { frostM.opacity = 0.82 * k; frostM.visible = k > 0.01; skinM.color.setRGB(lerp(1, 0.92, k), lerp(1, 0.96, k), lerp(1, 1.0, k)); } };
}
const bird = makeTurkey(true); scene.add(bird.g);

// ------------------------------------------------------------------ the kitchen fridge (beat 4), far off on its own
const FR = V(40, 0, 0);
const kitchen = new THREE.Group(); kitchen.position.copy(FR); scene.add(kitchen);
const fridgeLight = new THREE.PointLight(0xeef6ff, 0, 2.2, 1.5); fridgeLight.position.set(0, 1.55, 0.05); kitchen.add(fridgeLight);
const fbird = makeTurkey(false);
const dayCanvas = document.createElement('canvas'); dayCanvas.width = 280; dayCanvas.height = 180; const dayTex = new THREE.CanvasTexture(dayCanvas); dayTex.colorSpace = THREE.SRGBColorSpace;
let dayState = -1;
function drawDay(n) { const g = dayCanvas.getContext('2d'); g.fillStyle = '#fff6c8'; g.fillRect(0, 0, 280, 180); g.fillStyle = '#c0392b'; g.fillRect(0, 0, 280, 46);
  g.fillStyle = '#fff'; g.font = 'bold 34px sans-serif'; g.textAlign = 'center'; g.fillText('20 LB TURKEY', 140, 36); g.fillStyle = '#1a1a1a'; g.font = 'bold 92px sans-serif'; g.fillText('DAY ' + n, 140, 150); dayTex.needsUpdate = true; }
{ kitchen.add(new THREE.Mesh(new THREE.PlaneGeometry(6, 6).rotateX(-Math.PI / 2), mat(0xcfc6b8, 0.6)));
  box(6, 3, 0.1, 0, 1.5, -0.45, mat(0xe9e1d0, 0.9), 0, kitchen);
  box(1.4, 0.92, 0.62, -1.15, 0.46, -0.1, mat(0x6b8aa0, 0.6), 0.02, kitchen); box(1.45, 0.04, 0.66, -1.15, 0.94, -0.1, mat(0x2e2e32, 0.3), 0, kitchen);
  box(1.4, 0.92, 0.62, 1.15, 0.46, -0.1, mat(0x6b8aa0, 0.6), 0.02, kitchen); box(1.45, 0.04, 0.66, 1.15, 0.94, -0.1, mat(0x2e2e32, 0.3), 0, kitchen);
  const shell = mat(0xe6e9ec, 0.35, 0.25), inside = new THREE.MeshStandardMaterial({ color: 0xf6f8fa, roughness: 0.5, emissive: 0xdde8f0, emissiveIntensity: 0.25 });
  box(0.04, 1.85, 0.68, -0.4, 0.925, 0, shell, 0, kitchen); box(0.04, 1.85, 0.68, 0.4, 0.925, 0, shell, 0, kitchen);
  box(0.84, 0.05, 0.68, 0, 1.825, 0, shell, 0, kitchen); box(0.84, 0.12, 0.68, 0, 0.06, 0, shell, 0, kitchen); box(0.84, 1.85, 0.04, 0, 0.925, -0.32, shell, 0, kitchen);
  box(0.75, 1.7, 0.01, 0, 0.94, -0.295, inside, 0, kitchen); box(0.01, 1.7, 0.6, -0.375, 0.94, 0, inside, 0, kitchen); box(0.01, 1.7, 0.6, 0.375, 0.94, 0, inside, 0, kitchen);
  const glassS = new THREE.MeshStandardMaterial({ color: 0xdfefff, roughness: 0.1, transparent: true, opacity: 0.35 });
  for (const y of [0.55, 0.92, 1.3]) box(0.74, 0.01, 0.6, 0, y, 0, glassS, 0, kitchen);
  box(0.7, 0.3, 0.55, 0, 0.3, 0.02, new THREE.MeshStandardMaterial({ color: 0xe8f2f8, transparent: true, opacity: 0.6, roughness: 0.2 }), 0.02, kitchen);
  // a few things on the shelves: milk, juice; lettuce and ketchup below
  { const jug = new THREE.Group(); jug.position.set(-0.17, 1.305, -0.08); kitchen.add(jug); box(0.11, 0.2, 0.11, 0, 0.1, 0, new THREE.MeshStandardMaterial({ color: 0xf4f6f6, roughness: 0.4, transparent: true, opacity: 0.95 }), 0.025, jug);
    const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.018, 0.02, 14), mat(0x2a5ad0, 0.4)); cap.position.y = 0.21; jug.add(cap); box(0.111, 0.07, 0.111, 0, 0.09, 0, mat(0x3a7ae0, 0.5), 0.02, jug);
    const oj = new THREE.Group(); oj.position.set(0.05, 1.305, -0.1); kitchen.add(oj); box(0.075, 0.19, 0.075, 0, 0.095, 0, mat(0xf29a2a, 0.5), 0.004, oj);
    const gab = box(0.075, 0.04, 0.053, 0, 0.205, 0, mat(0xf29a2a, 0.5), 0, oj); gab.rotation.x = Math.PI / 4;
    const lt = new THREE.Mesh(new THREE.IcosahedronGeometry(0.075, 2), mat(0x7ab84a, 0.8)); lt.position.set(0.2, 1.38, -0.12); kitchen.add(lt);
    const k1 = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.035, 0.17, 16), mat(0xc81e1e, 0.3)); k1.position.set(-0.27, 0.64, -0.1); kitchen.add(k1);
    const k2 = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.026, 0.035, 12), mat(0xf4f4f0, 0.4)); k2.position.set(-0.27, 0.74, -0.1); kitchen.add(k2); }
  // the door, swung open toward the camera's left
  const hinge = new THREE.Group(); hinge.position.set(-0.42, 0, 0.34); hinge.rotation.y = 1.95; kitchen.add(hinge);
  box(0.84, 1.75, 0.06, 0.42, 0.95, 0.03, shell, 0.01, hinge); box(0.74, 1.6, 0.01, 0.42, 0.95, -0.005, inside, 0, hinge);
  for (const y of [0.45, 0.9, 1.35]) box(0.7, 0.12, 0.08, 0.42, y, -0.05, new THREE.MeshStandardMaterial({ color: 0xe8f2f8, transparent: true, opacity: 0.55 }), 0, hinge);
  // the turkey on a tray on the middle shelf, and the day card leaning on the tray
  box(0.44, 0.02, 0.34, 0, 0.935, 0.0, mat(0x9aa0a6, 0.3, 0.6), 0.008, kitchen);
  fbird.g.rotation.y = 0.5; fbird.g.position.set(-0.08, 0.946, -0.06); fbird.ice.visible = false; kitchen.add(fbird.g);
  const card = new THREE.Mesh(new THREE.PlaneGeometry(0.17, 0.11), new THREE.MeshBasicMaterial({ map: dayTex, toneMapped: false })); card.position.set(0.035, 0.995, 0.2); card.rotation.set(-0.25, -0.15, 0); kitchen.add(card); }
drawDay(1);

// ------------------------------------------------------------------ fire, smoke, steam, the blue burner flame: camera-facing puffs placed from time alone
const FIREN = 1400, SMOKEN = 500;
function puffs(n, frag, blending) {
  const geo = new THREE.InstancedBufferGeometry().copy(new THREE.PlaneGeometry(1, 1)); geo.instanceCount = 0;
  const P = new Float32Array(n * 4), O = new Float32Array(n * 4), aP = new THREE.InstancedBufferAttribute(P, 4), aO = new THREE.InstancedBufferAttribute(O, 4);
  aP.setUsage(THREE.DynamicDrawUsage); aO.setUsage(THREE.DynamicDrawUsage); geo.setAttribute('aP', aP); geo.setAttribute('aO', aO);
  const m = new THREE.ShaderMaterial({ uniforms: { uT: { value: 0 }, uGain: { value: 1 } }, transparent: true, depthWrite: false, blending,
    vertexShader: `attribute vec4 aP, aO; varying vec2 vUv; varying vec4 vO;
      void main(){ vec3 c = aP.xyz; vec3 R = vec3(viewMatrix[0][0], viewMatrix[1][0], viewMatrix[2][0]), U = vec3(viewMatrix[0][1], viewMatrix[1][1], viewMatrix[2][1]);
        float a = aO.w * 6.2831; vec2 p = mat2(cos(a), -sin(a), sin(a), cos(a)) * position.xy; vec3 w = c + (R * p.x + U * p.y) * aP.w;
        vUv = uv; vO = aO; gl_Position = projectionMatrix * viewMatrix * vec4(w, 1.0); }`,
    fragmentShader: `uniform float uT, uGain; ${GLSLN} varying vec2 vUv; varying vec4 vO;
      void main(){ ${frag} }` });
  const mesh = new THREE.Mesh(geo, m); mesh.frustumCulled = false; mesh.renderOrder = 6; scene.add(mesh);
  let k = 0;
  return { mesh, m, begin() { k = 0; }, add(p, size, heat, alpha, seed) { if (k >= n || alpha < 0.004) return; P.set([p.x, p.y, p.z, size], k * 4); O.set([heat, alpha, 0, seed], k * 4); k++; },
    end() { geo.instanceCount = k; aP.needsUpdate = true; aO.needsUpdate = true; } };
}
const FIRE = puffs(FIREN, `vec2 p = vUv * 2.0 - 1.0; float s = vO.w * 17.0;
  float n = vn(p * 2.5 + vec2(s, s * 0.7) - vec2(0.0, uT * 4.0)) * 0.65 + vn(p * 6.0 + s * 3.0 - vec2(0.0, uT * 7.0)) * 0.35;
  float r = length(p * vec2(1.0, 0.85)) + (n - 0.5) * 0.75;
  float m = 1.0 - smoothstep(0.25, 0.95, r); if (m < 0.01) discard;
  float h = vO.x * (0.75 + 0.5 * n) * (1.0 - 0.45 * smoothstep(0.0, 1.0, r));
  vec3 col = mix(vec3(0.55, 0.06, 0.01), vec3(1.0, 0.42, 0.06), smoothstep(0.1, 0.55, h));
  col = mix(col, vec3(1.0, 0.86, 0.45), smoothstep(0.55, 0.95, h));
  gl_FragColor = vec4(col * m * vO.y * 1.1 * uGain, 1.0);`, THREE.AdditiveBlending);
const BLUE = puffs(160, `vec2 p = vUv * 2.0 - 1.0; float s = vO.w * 11.0;
  float n = vn(p * 3.0 + vec2(s) - vec2(0.0, uT * 9.0));
  float r = length(p * vec2(1.3, 0.7)) + (n - 0.5) * 0.5; float m = 1.0 - smoothstep(0.2, 0.9, r); if (m < 0.01) discard;
  vec3 col = mix(vec3(0.05, 0.18, 0.95), vec3(0.55, 0.8, 1.0), smoothstep(0.3, 0.9, vO.x * (1.0 - r)));
  gl_FragColor = vec4(col * m * vO.y * uGain, 1.0);`, THREE.AdditiveBlending);
const SMOKE = puffs(SMOKEN, `vec2 p = vUv * 2.0 - 1.0; float s = vO.w * 13.0;
  float n = vn(p * 2.0 + s - vec2(0.0, uT * 0.8)) * 0.6 + vn(p * 5.0 - s * 2.0) * 0.4;
  float r = dot(p, p) + (n - 0.5) * 0.8; float a = (1.0 - smoothstep(0.25, 0.95, r)) * vO.y; if (a < 0.004) discard;
  vec3 col = mix(vec3(0.16, 0.15, 0.15), vec3(0.93, 0.94, 0.96), vO.x) * (0.85 + 0.3 * n);
  gl_FragColor = vec4(col, a);`, THREE.NormalBlending);
FIRE.mesh.renderOrder = 7; BLUE.mesh.renderOrder = 7;
const fireLight = new THREE.PointLight(0xff7a2a, 0, 7, 1.6); scene.add(fireLight);
// foam (oil bubbling up) and steam bubbles: small instanced spheres
const foamM = new THREE.MeshStandardMaterial({ color: 0xfaecc8, emissive: 0x5a3a10, emissiveIntensity: 0.2, roughness: 0.3 });
const FOAMN = 700, foam = new THREE.InstancedMesh(new THREE.SphereGeometry(1, 10, 8), foamM, FOAMN); foam.frustumCulled = false; scene.add(foam);
const bubM = new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xdde8ff, emissiveIntensity: 0.6, roughness: 0.2, transparent: true, opacity: 0.9 });
const BUBN = 160, bubs = new THREE.InstancedMesh(new THREE.SphereGeometry(1, 12, 8), bubM, BUBN); bubs.frustumCulled = false; bubs.renderOrder = 5; scene.add(bubs);
const _M = new THREE.Matrix4(), _Q = new THREE.Quaternion(), _S = V(1, 1, 1);
let fk = 0, bk = 0;
const foamAdd = (p, r, sy = 0.75) => { if (fk >= FOAMN || r < 0.0005) return; _S.set(r, r * sy, r); foam.setMatrixAt(fk++, _M.compose(p, _Q, _S)); };
const bubAdd = (p, r) => { if (bk >= BUBN || r < 0.0005) return; _S.set(r, r, r); bubs.setMatrixAt(bk++, _M.compose(p, _Q, _S)); };

// the blue burner flame under the pot (k = 0 off .. 1 on)
function burnerFlame(t, k, cut = false) { if (k < 0.01) return;
  for (let i = 0; i < 56; i++) { const ang = i / 56 * Math.PI * 2 + 0.02 * hash1(i), a = ((t * 3.1 + hash1(i * 3.3)) % 1);   // the ring under the pot
    const r = 0.07 + 0.09 * a * a, p = V(Math.cos(ang) * r, Math.min(0.266 + 0.05 * a * k, POT.y - 0.006), Math.sin(ang) * r);
    BLUE.add(p, (0.024 + 0.014 * (1 - a)) * (0.6 + 0.4 * k), 1 - a, Math.sin(Math.PI * Math.min(1, a * 1.2)) * 0.9 * k, hash1(i * 4.1)); }
  for (let i = 0; i < 44; i++) { const ang = (i + 0.5) / 44 * Math.PI * 2, a = ((t * 2.6 + hash1(i * 5.3)) % 1);              // licking up the pot's sides
    const p = V(Math.cos(ang) * (POTR + 0.014 + 0.01 * a), POT.y - 0.01 + 0.12 * a * k, Math.sin(ang) * (POTR + 0.014 + 0.01 * a)); if (cut && p.z > -0.02) continue;
    BLUE.add(p, (0.03 + 0.012 * (1 - a)) * k, (1 - a) * 0.8, Math.sin(Math.PI * Math.min(1, a * 1.1)) * 0.85 * k, hash1(i * 6.1)); } }
// bubbling oil: foam on the surface (k 0..1), at height y
function oilFoam(t, y, k, cut) { if (k < 0.01) return;
  const n = Math.round(420 * Math.min(1, k));
  for (let i = 0; i < n; i++) { const ang = hash1(i * 5.7) * Math.PI * 2, rr = Math.sqrt(hash1(i * 9.1)) * (POTR - 0.014);
    const p = V(Math.cos(ang) * rr, y + 0.002, Math.sin(ang) * rr); if (cut && p.z > 0.006) continue;
    const a = ((t * (2.2 + 2 * hash1(i * 2.2)) + hash1(i * 3.9)) % 1), heap = k > 0.6 ? (k - 0.6) * 0.09 * (1 - rr / POTR) : 0;
    p.y += heap * hash1(i * 6.3) + 0.006 * k * Math.sin(Math.PI * a);
    foamAdd(p, (0.003 + 0.008 * k) * (0.5 + hash1(i * 1.7)) * Math.sin(Math.PI * a) ** 0.4, 0.6); } }
// oil foaming over the rim and running down the outside of the pot (s 0..1)
function spillFoam(t, s, cut) { if (s < 0.01) return;
  for (let i = 0; i < Math.round(240 * s); i++) { const ang = hash1(i * 4.3) * Math.PI * 2, a = ((t * (0.55 + 0.4 * hash1(i * 7.1)) + hash1(i * 2.9)) % 1);
    let r, y; if (a < 0.18) { const u = a / 0.18; r = lerp(POTR - 0.03, POTR + 0.016, u); y = RIM + 0.012 * Math.sin(Math.PI * u) + 0.004; }
    else { const u = (a - 0.18) / 0.82; r = POTR + 0.016 + 0.01 * u; y = RIM - (RIM - 0.28) * u ** 1.5; }
    const p = V(Math.cos(ang) * r, y, Math.sin(ang) * r); if (cut && p.z > 0.01) continue;
    foamAdd(p, (0.008 + 0.008 * hash1(i * 3.7)) * (1 - 0.4 * Math.max(0, a - 0.5)), 1.1); } }
// fire on the oil in the pot (level 0..2)
function potFire(t, level) { if (level < 0.01) return;
  const n = Math.round(180 * Math.min(1.6, level)), H = 0.15 + 0.5 * level, R0 = POTR * 0.9;
  for (let i = 0; i < n; i++) { const sp = 1.2 + 0.9 * hash1(i * 7.1), a = ((t * sp + hash1(i * 3.3)) % 1 + 1) % 1;
    const ang = hash1(i * 5.7) * Math.PI * 2, rr = Math.sqrt(hash1(i * 9.1)) * R0 * (1 - 0.5 * a);
    const p = V(Math.cos(ang) * rr + vn1(t * 2.3 + i * 0.37, 3) * 0.05 * a * level, RIM + 0.02 + a * H, Math.sin(ang) * rr + vn1(t * 2.1 + i * 0.53, 5) * 0.05 * a * level);
    FIRE.add(p, (0.06 + 0.07 * level) * (1 - 0.5 * a) * (0.7 + 0.6 * hash1(i * 2.9)), 1 - a * 0.9, Math.sin(Math.PI * Math.min(1, a * 1.15)) ** 0.6 * Math.min(1, level * 2), hash1(i * 4.4)); } }
// burning oil on the deck around the stand (radius r), and up the outside of the pot
function groundFire(t, r, k) { if (k < 0.01) return;
  for (let i = 0; i < Math.round(260 * k); i++) { const a = ((t * (1.1 + 0.7 * hash1(i * 2.1)) + hash1(i * 1.7)) % 1), ang = hash1(i * 6.7) * Math.PI * 2, rr = Math.sqrt(hash1(i * 4.3)) * r;
    const onPot = i % 3 === 0, p = onPot ? V(Math.cos(ang) * (POTR + 0.03), 0.3 + a * 0.5, Math.sin(ang) * (POTR + 0.03)) : V(Math.cos(ang) * rr, 0.02 + a * (0.25 + 0.3 * (1 - rr / r)), Math.sin(ang) * rr);
    FIRE.add(p, (0.07 + 0.09 * (1 - a)) * (0.7 + 0.5 * hash1(i * 3.1)), 1 - a * 0.85, Math.sin(Math.PI * a) ** 0.6 * 0.8 * k, hash1(i * 3.9)); } }
// the fireball: s = seconds since the oil hit the flame
function fireball(s, t) { if (s < 0) return;
  const O = V(0, RIM - 0.1, 0);
  for (let i = 0; i < 460; i++) { const d0 = hash1(i * 3.7), ang = hash1(i * 6.1) * Math.PI * 2;
    const u = s - 0.12 * hash1(i * 8.3); if (u <= 0) continue;
    const dir = V(Math.cos(ang) * (0.3 + 0.7 * d0), 1.2 + 1.5 * hash1(i * 2.2), Math.sin(ang) * (0.3 + 0.7 * d0)).normalize();
    const reach = (0.55 + 1.2 * hash1(i * 5.3)) * (1 - Math.exp(-u * 2.8));
    const p = O.clone().addScaledVector(dir, reach).add(V(0, 0.3 * u * u, 0));
    const wz = HOUSEZ + 0.14; if (p.z < wz) { p.y += (wz - p.z) * 0.9; p.x *= 1.15; p.z = wz; }    // it hits the siding and climbs it
    const life = 1.5 + 1.1 * hash1(i * 7.7), a = u / life; if (a > 1) continue;
    const size = (0.15 + 0.42 * Math.sqrt(a)) * (0.7 + 0.6 * hash1(i * 4.9));
    FIRE.add(p, size * 0.85, 1 - 0.85 * a, 0.19 * Math.sin(Math.PI * Math.min(1, a * 1.3 + 0.1)) ** 0.5 * (1 - a * 0.4), hash1(i * 1.3));
    if (a > 0.4 && i % 3 === 0) SMOKE.add(p.clone().add(V(0, 0.2 * (a - 0.4), 0)), size * 1.4, 0.15, 0.5 * (a - 0.4) * (1 - a) * 4, hash1(i * 2.6)); } }
// smoke off hot oil / steam off the bubbling pot
function potSmoke(t, k, steam = 0, top = RIM) { if (k < 0.01) return;
  for (let i = 0; i < 70; i++) { const a = ((t * (0.4 + 0.25 * hash1(i * 3.1)) + hash1(i * 1.9)) % 1), ang = hash1(i * 5.1) * Math.PI * 2, rr = Math.sqrt(hash1(i * 7.3)) * POTR * 0.85;
    const p = V(Math.cos(ang) * rr + vn1(t * 0.9 + i, 2) * 0.08 * a, top + a * (0.6 + 0.4 * steam), Math.sin(ang) * rr + vn1(t * 0.8 + i, 4) * 0.08 * a);
    SMOKE.add(p, 0.05 + (0.18 + 0.12 * steam) * a, 0.7 + 0.3 * steam, Math.sin(Math.PI * a) * (0.35 + 0.25 * steam) * k, hash1(i * 6.6)); } }

// ------------------------------------------------------------------ the story
const T_TOUCH = 0.87;                                              // beat 0: the frozen bird hits the oil
const T_FLASH = 0.45;                                              // beat 2: the ice flashes to steam
const T_IGN = 0.3;                                                 // beat 3: the spilled oil reaches the flame
const BASE_HI = 0.76, BASE_LO = 0.44;                                              // rack base height while he holds it over the pot
const LOOPSEED = { R: null, L: null };
function blinkAt(s) { const u = ((s + 40) % 3.7) / 0.16; return u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0; }
const F = fwdOf(90), Rt = rightOf(90), UP = V(0, 1, 0);           // his forward (-x), his right (-z), up
const STAND1 = addPose(STAND, { spine1: [-4, 0, 0], neck: [6, 0, 0] });

// hand builders ------------------------------------------------------
// the rod's grip in his right hand: palm on its side (facing his left), thumb up, fingers around it
function rodHand(grip, S = 'R') { const s = S === 'R' ? 1 : -1, n = Rt.clone().multiplyScalar(-s).addScaledVector(F, 0.25).normalize(), u = new THREE.Vector3().crossVectors(UP, n).multiplyScalar(-s).normalize();
  return { S, p: grip.clone().addScaledVector(n, -(HR + GRIP)), n, u, c: 85, th: 60, opp: 45, memAbs: 'rod' + S, seed: A(40, 15, 0, 80, 10) }; }
// the flame knob: palm over it like a jar lid, fingers around it; roll = how far it's turned (deg). Left hand mirrors the right.
let KSUP = -58;
function knobHand(S, roll = 0) { const s = S === 'R' ? 1 : -1;
  const face = KNOB.clone().addScaledVector(KAX, 0.026), u0 = Rt.clone().multiplyScalar(-s).addScaledVector(KAX, s * Rt.dot(KAX)).normalize();
  const u = u0.applyAxisAngle(KAX, s * roll * D2R), n = KAX.clone().negate().applyAxisAngle(u, -s * KSUP * D2R);
  return { S, p: face.clone().addScaledVector(KAX, 0.03).addScaledVector(u, -0.03), u, n, c: 58, th: 60, opp: 35, memAbs: 'knob' + S, seed: A(40, 10, 0, 70, 60, 20) }; }
// shielding his face from the blast: palms out toward the fire
function shieldHands() { const hd = wp(G.bones.head);
  return ['R', 'L'].map(S => { const s = S === 'R' ? 1 : -1;
    return { S, p: hd.clone().addScaledVector(F, 0.26).addScaledVector(Rt, 0.13 * s).add(V(0, -0.05, 0)), n: F.clone().addScaledVector(UP, 0.2).normalize(), u: UP.clone().addScaledVector(F, -0.2).normalize(), c: 18, th: 15, seed: A(100, 20, 30, 120, 40) }; }); }
const gripAt = base => V(0, base + ROD_L, 0);

// the state at a time ----------------------------------------------
function guyAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  const face = { blink: blinkAt(lt + b * 1.3) };
  let pose = STAND1, root = { x: STANDP.x, y: 0.95, z: STANDP.z, yaw: 90 }, hands = [], show = true, cut = false;
  let base = BASE_HI, frost = 1, ice = 1, burner = 1, knobTurn = 0, cutaway = false, far = false, fridge = false;
  let oilY = OIL0, boil = 0, spill = 0, steam = 0, smoke = 0, ball = -1, gfire = 0, gr = 0, pfire = 0, wallBurn = 0, stepBack = 0, thaw = 0, day = 1, bubK = 0, steamK = 0;
  if (b === 7 || b === 0) {                                         // 7: he holds the frozen bird over the hot oil; 0: drops it in, it erupts
    smoke = 0.5;
    if (b === 7) { base = BASE_HI + 0.03 * (1 - smooth(0, d, lt));
      hands = [rodHand(gripAt(base))]; pose = addPose(STAND1, { neck: [-18, 4, 0], head: [-12, 0, 0], spine1: [4, 0, 0] });
      Object.assign(face, { look: [0.1, -0.5] });
    } else {
      const u = clamp(lt / 0.95, 0, 1); base = BASE_HI - (BASE_HI - BASE_LO) * u * u;
      const hit = smooth(T_TOUCH, T_TOUCH + 0.35, lt);
      boil = hit; steam = hit; oilY = OIL0 + (RIM - 0.035 - OIL0) * smooth(T_TOUCH, T_TOUCH + 1.4, lt); smoke = 0.5 + 0.5 * hit;
      const flinch = smooth(T_TOUCH + 0.05, T_TOUCH + 0.4, lt);
      pose = addPose(STAND1, { neck: [-18 + 8 * flinch, 4 - 10 * flinch, 0], head: [-12 + 6 * flinch, 0, 0], spine1: [4 + 8 * u - 10 * flinch, 0, 0], spine2: [-6 * flinch, 0, 0] });
      root = { x: STANDP.x + 0.05 * flinch, y: 0.95 - 0.01 * flinch, z: STANDP.z, yaw: 90 }; stepBack = 0.05 * flinch;
      Object.assign(face, { look: [0.1, -0.5 * (1 - flinch)], fear: flinch, brow: flinch, oh: 0.4 * flinch, jaw: 0.3 * flinch, squint: 0.3 * flinch });
      hands = [{ ...rodHand(gripAt(base)), ...(LOOPSEED.R ? { seed: LOOPSEED.R, seedIsPrev: true } : {}) }];
    }
  } else if (b === 1 || b === 2) {                                 // cutaway: the ice inside meets the oil; it flashes to steam and the oil boils over
    show = false; cutaway = true; base = BASE_LO;
    if (b === 1) { oilY = RIM - 0.035 + 0.01 * smooth(0, d, lt); boil = 0.8; bubK = 0.35 + 0.35 * smooth(0, d, lt); }
    else { const f = smooth(T_FLASH, T_FLASH + 0.5, lt); ice = 1 - f; bubK = 0.7 + 0.3 * f; steamK = f;
      oilY = RIM - 0.025 + 0.037 * smooth(T_FLASH + 0.1, 1.9, lt); boil = 0.7 + 0.5 * f; spill = smooth(1.9, d, lt); steam = f; }
  } else if (b === 3) {                                             // it pours onto the flame: the fireball; he lets go and jumps back
    base = BASE_LO - 0.06 * smooth(T_IGN, T_IGN + 0.25, lt); oilY = RIM + 0.012; boil = 1.1; spill = 1; steam = 1;
    ball = lt - T_IGN; gfire = smooth(T_IGN, T_IGN + 0.3, lt); gr = 0.3 + 0.5 * smooth(T_IGN, d, lt); pfire = 1.2 * smooth(T_IGN + 0.1, T_IGN + 0.5, lt);
    wallBurn = smooth(T_IGN + 0.5, d, lt);
    const k = smooth(T_IGN, T_IGN + 0.55, lt); stepBack = 0.3 * k;
    pose = addPose(STAND1, { spine1: [-2 + 10 * k, 0, 0], spine2: [8 * k, 0, 0], neck: [-14 + 10 * k, -20 * k, 0], head: [-8 + 6 * k, -10 * k, 0] });
    root = { x: STANDP.x + 0.05 + stepBack, y: 0.94 - 0.02 * k, z: STANDP.z, yaw: 90 };
    hands = shieldHands().map(h => ({ ...h, blend: k, ...(h.S === 'R' ? { from: rodHand(gripAt(BASE_LO)) } : {}) }));
    Object.assign(face, { fear: 1, brow: 1, squint: 0.9 * k, jaw: 0.35, blink: 0, look: [0.4, 0] });
  } else if (b === 4) {                                             // the right way: thaw it in the fridge, a day per five pounds
    show = false; fridge = true; thaw = smooth(0.2, d - 0.3, lt); day = 1 + Math.min(3, Math.floor(clamp((lt - 0.55) / 0.85, 0, 3.99)));
  } else if (b === 5) {                                             // flame off, then lower it in slowly
    far = true; frost = 0;
    const kOn = smooth(0.0, 0.45, lt), turn = smooth(0.45, 0.8, lt), off = smooth(0.95, 1.4, lt); knobTurn = turn; burner = 1 - turn;
    const low = smooth(1.0, d, lt); base = BASE_HI - 0.33 * low;
    const sub = clamp((OIL0 - base) / 0.3, 0, 1); boil = 0.25 * sub; oilY = OIL0 + 0.04 * sub; smoke = 0.3; steam = 0.3 * sub;
    hands = [rodHand(gripAt(base))]; if (off < 0.999) hands.push({ ...knobHand('L', -50 + 50 * turn), blend: kOn * (1 - off) });
    pose = addPose(STAND1, { spine1: [6 + 8 * low, 0, 0], neck: [-16 - 4 * low, 8 * (1 - off), 0], head: [-10, 0, 0] });
    Object.assign(face, { look: [0.1 * (1 - off), -0.5], brow: 0.2 });
  } else if (b === 6) {                                             // outside, far from the house; never water: frying calmly, extinguisher by him
    far = true; frost = 0; base = 0.34; oilY = OIL0 + 0.07; boil = 0.3; steam = 0.4; smoke = 0.3;
    stepBack = 0.35; root = { x: STANDP.x + stepBack, y: 0.95, z: STANDP.z + 0.1, yaw: 90 };
    pose = addPose(STAND1, { neck: [-12, 0, 0], head: [-6, 0, 0] }); Object.assign(face, { look: [0, -0.3] });
  }
  const wb = 2 * Math.PI * Math.round(TOTAL / 2.6) / TOTAL;           // breathing (whole cycles over the loop)
  pose = addPose(pose, { spine1: [0.9 * Math.sin(wb * t), 0, 0], spine2: [0.6 * Math.sin(wb * t + 0.4), 0, 0], neck: [0.7 * Math.sin(wb * t + 1.1), 0, 0] });
  return { b, lt, d, pose, root, hands, show, cut, base, frost, ice, burner, knobTurn, cutaway, far, fridge, oilY, boil, spill, steam, smoke, ball, gfire, gr, pfire, wallBurn, stepBack, thaw, day, bubK, steamK, face };
}

// ------------------------------------------------------------------ cameras
function shakeV(t, a) { return V(vn1(t * 14, 1) * a * 0.5, vn1(t * 14, 2) * a, vn1(t * 14, 3) * a); }
const CAM7 = { pos: V(-0.3, 1.5, 2.05), tgt: V(0.12, 1.02, 0), fov: 46 };     // at his front-left, high: his face up top, the pot and the flame below
function camAt(t, g) {
  const b = g.b, lt = g.lt, d = g.d, k = smooth(0, d, lt);
  if (b === 7) return { pos: CAM7.pos.clone().add(V(0.06 * (1 - k), 0.03 * (1 - k), 0.1 * (1 - k))), tgt: CAM7.tgt, fov: CAM7.fov };
  if (b === 0) { const h = smooth(T_TOUCH, T_TOUCH + 0.6, lt);
    return { pos: CAM7.pos.clone().lerp(V(-0.2, 1.42, 1.55), k).add(shakeV(t, 0.006 * h)), tgt: CAM7.tgt.clone().lerp(V(0.1, 0.86, 0), k), fov: 46 - 3 * k }; }
  if (b === 1) return { pos: V(0, 0.54, 1.25 - 0.15 * k), tgt: V(0, 0.5, 0), fov: 40 };
  if (b === 2) { const f = lt > T_FLASH ? 0.006 * Math.exp(-(lt - T_FLASH) * 3) : 0;
    return { pos: V(0, 0.54 + 0.06 * k, 1.1 + 0.2 * k).add(shakeV(t, f)), tgt: V(0, 0.5 + 0.06 * k, 0), fov: 40 }; }
  if (b === 3) return { pos: V(-0.35, 1.45, 2.6).add(shakeV(t, lt > T_IGN ? 0.035 * Math.exp(-(lt - T_IGN) * 2) : 0)), tgt: V(0.2, 1.05, -0.3), fov: 54 };
  if (b === 4) return { pos: FR.clone().add(V(0.05 - 0.02 * k, 1.15 - 0.03 * k, 1.22 - 0.22 * k)), tgt: FR.clone().add(V(0, 1.03, 0)), fov: 42 };
  if (b === 5) return { pos: V(-0.3, 1.48, 1.95), tgt: V(0.12, 0.95, 0.05), fov: 46 };
  if (b === 6) return { pos: V(-0.3, 1.5, 2.0).lerp(V(0.9, 2.5, 4.9), k), tgt: V(0.1, 0.75, 0).lerp(V(0, 0.9, -2.8), k), fov: 46 + 4 * k };
  return CAM7;
}

// ------------------------------------------------------------------ clipping: him vs the fryer, the house, the floor and his own body
const SOLIDS = [];
const sbox = (name, obj, min, max) => SOLIDS.push({ name, obj, box: new THREE.Box3(min, max) });
sbox('pot', pot, V(-POTR - 0.01, -0.06, -POTR - 0.01), V(POTR + 0.01, POTH + 0.005, POTR + 0.01));
sbox('house', world, V(-5, 0, HZ - 0.2), V(5, 3.2, HZ));
sbox('knobpost', knobG, V(-0.06, -0.04, -0.035), V(0.01, 0.03, 0.035));
const BODYPTS = { handR: 0.025, handL: 0.025, farmR: 0.035, farmL: 0.035, uarmR: 0.045, uarmL: 0.045, head: 0.09, chest: 0.12, hips: 0.1, shinR: 0.05, shinL: 0.05, footR: 0.04, footL: 0.04, thighR: 0.06, thighL: 0.06 };
// his own body surface (head, neck, torso; not the arms): skinned sample points with outward normals, rebuilt each frame
const BODYSURF = (() => { const keep = new Set(['hips', 'spine1', 'spine2', 'chest', 'neck', 'head', 'jaw', 'clavR', 'clavL', 'browR', 'browL']), out = [];
  for (const [mn, step] of [['skin_head', 10], ['shirt', 2], ['jeans', 5]]) { const m = G.meshes[mn]; if (!m) continue; const ga = m.geometry.attributes, names = m.skeleton.bones.map(b => b.name);
    for (let i = 0; i < ga.position.count; i += step) { let bw = -1, bi = 0; for (let k = 0; k < 4; k++) { const w = ga.skinWeight.getComponent(i, k); if (w > bw) { bw = w; bi = ga.skinIndex.getComponent(i, k); } }
      if (keep.has(names[bi])) out.push([m, i]); } }
  return out; })();
let SURF = null;
function surfNow() { const n = BODYSURF.length, P = new Float32Array(n * 3), N = new Float32Array(n * 3);
  for (let j = 0; j < n; j++) { const [m, i] = BODYSURF[j], ga = m.geometry.attributes;
    const a = V(ga.position.getX(i), ga.position.getY(i), ga.position.getZ(i)), b = V(0, 0, 0);
    m.applyBoneTransform(i, a); b.set(ga.position.getX(i) + ga.normal.getX(i) * 0.01, ga.position.getY(i) + ga.normal.getY(i) * 0.01, ga.position.getZ(i) + ga.normal.getZ(i) * 0.01);
    const sw = m.geometry.attributes.position; const save = [sw.getX(i), sw.getY(i), sw.getZ(i)]; sw.setXYZ(i, b.x, b.y, b.z); m.applyBoneTransform(i, b); sw.setXYZ(i, ...save);
    a.applyMatrix4(m.matrixWorld); b.applyMatrix4(m.matrixWorld); b.sub(a).normalize();
    P.set([a.x, a.y, a.z], j * 3); N.set([b.x, b.y, b.z], j * 3); }
  return { P, N, n }; }
function nearDepth(p, P, N, each) { const bd = [1e9, 1e9, 1e9, 1e9], bj = [-1, -1, -1, -1];
  each(j => { const dx = p.x - P[j * 3], dy = p.y - P[j * 3 + 1], dz = p.z - P[j * 3 + 2], d = dx * dx + dy * dy + dz * dz;
    if (d < bd[3]) { let q = 3; while (q > 0 && d < bd[q - 1]) { bd[q] = bd[q - 1]; bj[q] = bj[q - 1]; q--; } bd[q] = d; bj[q] = j; } });
  let sw = 0, sd = 0; for (let q = 0; q < 4; q++) { const j = bj[q]; if (j < 0) continue; const w = 1 / (Math.sqrt(bd[q]) + 0.004);
    sd += w * -((p.x - P[j * 3]) * N[j * 3] + (p.y - P[j * 3 + 1]) * N[j * 3 + 1] + (p.z - P[j * 3 + 2]) * N[j * 3 + 2]); sw += w; }
  return sw ? sd / sw : -1; }
function bodyDepth(p) { const { P, N, n } = SURF; return nearDepth(p, P, N, f => { for (let j = 0; j < n; j++) f(j); }); }
let BODYNOW = null, LASTH = [];
window.costParts = (i) => { stepTo(i); return LASTH.map(h => { const a = RG.LAST['arm' + h.S], f = RG.handFK(h.S, a); const cc = RG.contactCost(h)();
  return h.S + (h.free ? ' FREE' : '') + ' pos ' + (f.p.distanceTo(h.p) * 100).toFixed(1) + 'cm n ' + (h.n ? f.n.dot(h.n).toFixed(2) : '-') + ' w ' + (h.w ? f.w.dot(h.w).toFixed(2) : '-') + ' u ' + (h.u ? f.u.dot(h.u).toFixed(2) : '-') + ' contact ' + cc.toFixed(1) + ' extra ' + (h.extra ? h.extra(f).toFixed(1) : '-') + ' arm ' + a.map(v => v.toFixed(0)).join(','); }).join(' | '); };
const TIPS = ['index', 'middle', 'pinky', 'thumb'];
RG.contactCost = h => { const S = h.S, c0 = h.p, near = [];
  if (BODYNOW) { const { P, n } = BODYNOW; for (let j = 0; j < n; j++) { const dx = P[j * 3] - c0.x, dy = P[j * 3 + 1] - c0.y, dz = P[j * 3 + 2] - c0.z; if (dx * dx + dy * dy + dz * dz < 0.3 * 0.3) near.push(j); } }
  const NP = new Float32Array(near.length * 3), NN = new Float32Array(near.length * 3); near.forEach((j, k) => { for (let a = 0; a < 3; a++) { NP[k * 3 + a] = BODYNOW.P[j * 3 + a]; NN[k * 3 + a] = BODYNOW.N[j * 3 + a]; } });
  const solids = SOLIDS.filter(sd => sd.obj.visible).map(sd => ({ inv: sd.obj.matrixWorld.clone().invert(), box: sd.box }));
  const CS = 0.025, cell = (x, y, z) => (Math.floor(x / CS) + 512) * 1048576 + (Math.floor(y / CS) + 512) * 1024 + (Math.floor(z / CS) + 512), GRID = new Map();
  for (let k = 0; k < near.length; k++) { const key = cell(NP[k * 3], NP[k * 3 + 1], NP[k * 3 + 2]); let a = GRID.get(key); if (!a) GRID.set(key, a = []); a.push(k); }
  const depthB = p => { if (!near.length) return -1; const cx = Math.floor(p.x / CS), cy = Math.floor(p.y / CS), cz = Math.floor(p.z / CS); let any = false;
    const cells = []; for (let i = -1; i <= 1; i++) for (let j = -1; j <= 1; j++) for (let l = -1; l <= 1; l++) { const a = GRID.get((cx + i + 512) * 1048576 + (cy + j + 512) * 1024 + (cz + l + 512)); if (a) { cells.push(a); any = true; } }
    return any ? nearDepth(p, NP, NN, f => { for (const a of cells) for (const k of a) f(k); }) : nearDepth(p, NP, NN, f => { for (let k = 0; k < near.length; k++) f(k); }); };
  const depthS = p => { let m = -1; for (const sd of solids) { const q = p.clone().applyMatrix4(sd.inv), b = sd.box; m = Math.max(m, Math.min(q.x - b.min.x, b.max.x - q.x, q.y - b.min.y, b.max.y - q.y, q.z - b.min.z, b.max.z - q.z)); } return m; };
  return () => { let c = 0; const pts = TIPS.map(f => [RG.tip(f, S), 0.008]); pts.push([RG.palmW(S), 0.004]); const el = wp(G.bones['farm' + S]);
    const soft = h.soft || 0; for (const [p, r] of pts) { const d = Math.max(depthB(p) - soft, depthS(p)) + r - 0.003; if (d > 0) c += (d / 0.002) ** 2; }
    { const d = depthB(el) + 0.03 - 0.003; if (d > 0) c += (d / 0.003) ** 2; }
    { const wr = wp(G.bones['hand' + S]), d = Math.max(depthB(wr) - soft, depthS(wr)) + 0.024 - 0.003; if (d > 0) c += (d / 0.002) ** 2; }
    return c; }; };
function clipScan() { const out = []; scene.updateMatrixWorld(true);
  if (!G.root.visible) return out;
  const pts = Object.entries(BODYPTS).map(([n, r]) => [n, n.startsWith('thigh') ? wp(G.bones[n]).lerp(wp(G.bones['shin' + n.slice(-1)]), 0.5) : wp(G.bones[n]), r]);
  for (const S of ['R', 'L']) for (const f of ['index', 'middle', 'pinky', 'thumb']) pts.push([f + ' tip ' + S, RG.tip(f, S), 0.008]);
  for (const [n, p, r] of pts) {
    if (p.y - r < -0.015) out.push({ what: 'him ' + n, into: 'floor', depth: +((-(p.y - r)) * 100).toFixed(1) });
    for (const S of SOLIDS) { if (!S.obj.visible) continue; const q = p.clone().applyMatrix4(S.obj.matrixWorld.clone().invert()), bx = S.box;
      const dx = Math.min(q.x - bx.min.x, bx.max.x - q.x), dy = Math.min(q.y - bx.min.y, bx.max.y - q.y), dz = Math.min(q.z - bx.min.z, bx.max.z - q.z);
      const dd = Math.min(dx, dy, dz) + r; if (dx > -r && dy > -r && dz > -r && dd > 0.012) out.push({ what: 'him ' + n, into: S.name, depth: +(dd * 100).toFixed(1) }); }
    if (/^(hand|farm|index|middle|pinky|thumb)/.test(n)) { if (!SURF) SURF = surfNow();
      const dB = bodyDepth(p) + r; if (dB > 0.012) out.push({ what: 'him ' + n, into: 'own body', depth: +(dB * 100).toFixed(1) }); } }
  SURF = null;
  return out; }

// ------------------------------------------------------------------ per-frame update
let LASTF = -10;
function update(t, frame) {
  t = ((t % TOTAL) + TOTAL) % TOTAL;
  const g = guyAt(t);
  // the set: near the house or far out in the yard; the bird on its rod where the story puts it (his hand follows it)
  world.position.z = g.far ? FARZ : 0; HOUSEZ = HZ + world.position.z; deck.visible = !g.far; ext.visible = g.far;
  bird.g.position.set(0, g.base, 0); bird.frost(g.frost); bird.ice.visible = g.ice > 0.01; bird.ice.scale.copy(bird.ICE).multiplyScalar(Math.max(0.001, g.ice));
  scene.updateMatrixWorld(true);
  // him
  G.root.visible = g.show;
  RG.applyPose(g.pose, g.root);
  const yaw = g.root.yaw, f = fwdOf(yaw), r = rightOf(yaw);
  const ground0 = V(g.root.x, 0, g.root.z);
  for (const [S, sx] of [['R', 0.11], ['L', -0.11]]) {
    const back = g.stepBack * (S === 'R' ? 1 : 0.6);
    const fp = ground0.clone().addScaledVector(r, sx).addScaledVector(f, (S === 'R' ? 0.02 : -0.02) - back * 0.3);
    fp.y = ANKLEH; RG.foot(S, fp, fp.clone().add(V(0, 0.45, 0)).addScaledVector(f, 1), yawQ(yaw)); }
  G.root.updateMatrixWorld(true);
  const list = [];
  if (g.show) { BODYNOW = surfNow(); const g2 = guyAt(t); g.hands = g2.hands; for (const h of g.hands) list.push(h); }
  if (list.length) { RG.hands(list, 'b' + g.b, frame); LASTH = list; }
  for (const S of ['R', 'L']) if (!list.some(h => h.S === S)) delete RG.LAST['cost' + S];
  G.root.updateMatrixWorld(true); RG.untwist(); G.face(g.face); G.root.updateMatrixWorld(true);
  // knob
  knobSpin.rotation.x = -g.knobTurn * 50 * D2R; kpost.visible = knobG.visible = !g.cutaway;
  // cutaway: pot, oil, foam and the bird lose their near half
  for (const m of [steel, oilM, foamM, ...bird.mats]) { const want = g.cutaway ? CLIP : null; if (m.clippingPlanes !== want) { m.clippingPlanes = want; m.needsUpdate = true; } }
  cutFaces.visible = g.cutaway; bird.cut.visible = g.cutaway; if (g.cutaway) bird.frostM.visible = false;
  { const im = bird.ice.material; if (im.depthTest === g.cutaway) { im.depthTest = !g.cutaway; im.needsUpdate = true; } bird.ice.renderOrder = g.cutaway ? 9 : 0; }   // in the cutaway the ice shows clear through the oil
  // oil level
  const lvl = g.oilY - POT.y - 0.006; oil.scale.y = lvl; oilCut.scale.y = lvl;
  // the oil sheet down the outside and the pool on the deck
  sheetM.opacity = 0.75 * smooth(0, 0.5, g.spill); sheet.visible = g.spill > 0.01 && !g.cutaway; sheet.position.y = RIM + 0.004; sheet.scale.y = (RIM - 0.27) * smooth(0, 0.6, g.spill);
  pool.visible = g.b === 3; pool.scale.setScalar(Math.max(0.01, g.gr));
  // foam and bubbles
  fk = 0; bk = 0;
  oilFoam(t, g.oilY, g.boil, g.cutaway); spillFoam(t, g.spill, g.cutaway);
  if (g.bubK > 0) {                                                  // steam bubbles off the ice, rising through the oil (cutaway)
    const top = g.oilY, ic = V(-0.012, g.base + 0.085, 0);
    for (let i = 0; i < Math.round(150 * g.bubK); i++) { const a = ((t * (0.9 + 0.8 * hash1(i * 2.3)) + hash1(i * 5.1)) % 1), ang = hash1(i * 3.3) * 6.283;
      const r0 = 0.02 + 0.06 * hash1(i * 7.9) + g.steamK * 0.06 * hash1(i * 1.1), y = ic.y + (top - ic.y) * a;
      const p = V(Math.cos(ang) * r0 * (1 + 0.8 * a) + vn1(t * 3 + i, 1) * 0.01, y, -0.004 - 0.03 * hash1(i * 4.4));
      bubAdd(p, (0.002 + 0.004 * a + 0.006 * g.steamK * hash1(i * 6.1)) * (0.6 + 0.4 * hash1(i))); } }
  foam.count = fk; foam.instanceMatrix.needsUpdate = true; bubs.count = bk; bubs.instanceMatrix.needsUpdate = true;
  // fire, smoke, steam, the burner flame, and the light they throw
  FIRE.begin(); SMOKE.begin(); BLUE.begin(); for (const P of [FIRE, SMOKE, BLUE]) P.m.uniforms.uT.value = t;
  FIRE.m.uniforms.uGain.value = g.cutaway ? 0.5 : 1; BLUE.m.uniforms.uGain.value = g.cutaway ? 0.8 : 1;
  if (!g.fridge) {
    burnerFlame(t, g.burner * (g.b === 3 ? 1 - g.gfire : 1), g.cutaway);
    potFire(t, g.pfire); groundFire(t, g.gr, g.gfire); if (g.ball >= 0) fireball(g.ball, t);
    if (g.wallBurn > 0) for (let i = 0; i < 200; i++) { const a = ((t * (0.8 + 0.5 * hash1(i * 2.1)) + hash1(i * 1.7)) % 1);   // the siding catches
      const p = V((hash1(i * 6.7) - 0.5) * 1.5 * g.wallBurn, 0.6 + a * 2.2 * g.wallBurn, HOUSEZ + 0.12 + 0.1 * hash1(i * 3.1));
      FIRE.add(p, 0.12 + 0.16 * (1 - a), 1 - a * 0.85, Math.sin(Math.PI * a) ** 0.6 * 0.8 * g.wallBurn, hash1(i * 3.9)); }
    potSmoke(t, Math.max(g.smoke, g.steam), g.steam, g.cutaway ? RIM : Math.max(RIM, g.oilY));
    if (g.b === 3 && g.lt > T_IGN + 0.4) for (let i = 0; i < 120; i++) { const a = ((t * 0.3 + hash1(i * 2.3)) % 1);
      SMOKE.add(V((hash1(i * 5.1) - 0.5) * 1.2, 1.4 + a * 1.8, HOUSEZ + 0.3 + hash1(i * 6.2) * 0.8), 0.35 + 0.35 * a, 0.12, 0.55 * Math.sin(Math.PI * a) * smooth(T_IGN + 0.4, T_IGN + 1.2, g.lt), hash1(i * 7.4)); } }
  FIRE.end(); SMOKE.end(); BLUE.end();
  scorchM.opacity = 0.85 * g.wallBurn;
  const fl = g.fridge ? 0 : (g.ball >= 0 ? 6 * Math.exp(-g.ball * 1.2) + 1.6 : 0) + g.pfire + g.gfire + 0.3 * g.burner;
  fireLight.position.set(0.1, RIM + 0.4, 0.1); fireLight.intensity = 3.0 * fl * (0.85 + 0.15 * vn1(t * 12, 9));
  // the fridge: frost melting off, the day card
  fbird.frost(1 - g.thaw); fridgeLight.intensity = g.fridge ? 2.4 : 0; if (g.day !== dayState) { drawDay(g.day); dayState = g.day; }
  // camera and light
  const C = camAt(t, g); camera.position.copy(C.pos); camera.up.set(0, 1, 0); camera.lookAt(C.tgt); camera.fov = C.fov; camera.updateProjectionMatrix();
  const dim = g.cutaway ? 0.5 : 1;
  sun.position.set(2.2, 4.2, 3.2).add(g.fridge ? FR : V(0, 0, 0)); sun.target.position.copy(g.fridge ? FR : V(0, 0, 0)); sun.target.updateMatrixWorld();
  sun.intensity = (g.fridge ? 1.2 : 2.7) * dim; hemi.intensity = 0.9 * dim; scene.environmentIntensity = 0.35 * dim;
  scene.background = g.cutaway ? SKY.clone().multiplyScalar(0.35) : SKY;
  return { beat: g.b, cut: g.cut };
}
G.reset(); G.root.updateMatrixWorld(true);
const ANKLEH = wp(G.bones.footR).y;

// ------------------------------------------------------------------ frame I/O (same contract as the other 3D Shorts)
const draw = () => renderer.render(scene, camera);
const gl = renderer.getContext(), px = new Uint8Array(W * H * 4);
let CUTF = false, LASTB = 0;
function segStart(t) { return B[beatAt(t)]; }                      // every hold starts cold at its beat (a jump replays from there)
function stepTo(i) { const t = i / FPS, tt = ((t % TOTAL) + TOTAL) % TOTAL;
  if (i !== LASTF + 1) for (let j = Math.ceil(segStart(tt) * FPS - 1e-6) + Math.floor(t / TOTAL) * Math.round(TOTAL * FPS); j < i; j++) update(j / FPS, j);
  const r = update(t, i); CUTF = r.cut; LASTB = r.beat; LASTF = i; }
// the loop: beat 0's rod hand starts where beat 7 ends
for (let i = Math.ceil(B[7] * FPS); i < Math.round(TOTAL * FPS); i++) update(i / FPS, i);
LOOPSEED.R = RG.LAST.armR.slice();
draw();
for (const k of Object.keys(RG.MEM)) delete RG.MEM[k]; LASTF = -10;
window.renderAll = async (f0, f1) => { for (let i = f0; i < f1; i++) { stepTo(i); draw(); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); await fetch('/frame', { method: 'POST', body: px }); } return 'ok'; };
window.renderAtT = t => { const i = Math.round(t * FPS); stepTo(i);
  if (window.CAM && window.CAM.hand) { const hp = RG.palmW(window.CAM.hand); window.CAM.tgt = hp.toArray(); window.CAM.pos = hp.clone().add(V(...window.CAM.off)).toArray(); }
  if (window.CAM) { camera.position.set(...window.CAM.pos); camera.up.set(0, 1, 0); camera.lookAt(...window.CAM.tgt); camera.fov = window.CAM.fov || 42; camera.updateProjectionMatrix(); }
  draw(); return renderer.domElement.toDataURL('image/png'); };
window.rigReport = i => { stepTo(i); const t = i / FPS, iq = G.root.getWorldQuaternion(new THREE.Quaternion()).invert();
  const ang = { ...RG.LAST }; delete ang.costR; delete ang.costL;
  return { t, beat: LASTB, ang, hips: wp(G.bones.hips).toArray(), car: 0, show: G.root.visible, cut: CUTF,
    thumbs: ['R', 'L'].map(S => wp(G.bones['index1' + S]).sub(wp(G.bones['pinky1' + S])).applyQuaternion(iq).toArray()),
    forearms: ['R', 'L'].map(S => wp(G.bones['hand' + S]).sub(wp(G.bones['farm' + S])).normalize().applyQuaternion(iq).toArray()),
    cost: [RG.LAST.costR ?? null, RG.LAST.costL ?? null], clip: clipScan() }; };
window.dbg = { G, RG, wp, THREE, LOOPSEED, update, guyAt, renderer, scene, camera, setBN: () => { BODYNOW = surfNow(); }, KNOB, KAX, F, Rt, UP, knobHand, rodHand };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS);
window.READY = true;
