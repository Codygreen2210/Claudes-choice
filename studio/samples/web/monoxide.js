// "You just started your truck in the garage to warm it up, and the door is shut." - a 3D Short: carbon monoxide.
//   monoxide.html?w=1080&h=1920            (times from monoxide/times.json; one shot per narration line)
// Beats: 0 the truck idles, exhaust pours into the shut garage (hook) | 1 at the pipe: you can't see it or smell it
//        2 inside his blood: CO knocks the oxygen off the red cells | 3 x-ray: brain and heart go dim | 4 headache, dizzy, sick
//        5 confused, weak: he catches himself on the truck, it goes black | 6 door open is still not safe; the alarm: get out | 7 he starts it (loops)
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { loadGuy } from '/guy3d.js';

const Q = new URLSearchParams(location.search);
const W = +Q.get('w') || 720, H = +Q.get('h') || 1280;
const FPS = 30;
const TIMES = await (await fetch('/monoxide/times.json')).json();
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
// ================================================================== CARBON MONOXIDE
// ------------------------------------------------------------------ the garage: concrete floor, walls, a sectional door (shut), shelves, a work light; a pickup truck idling
const home = new THREE.Group(); scene.add(home);
scene.remove(lamp);
const GDOOR_Z = 3.5, GW0 = -3.0, GW1 = 2.6, GBACK = -3.6, GH = 2.9;
const conc = canvasTex(512, 512, g => { g.fillStyle = '#8c8a86'; g.fillRect(0, 0, 512, 512); for (let i = 0; i < 9000; i++) { const c = 110 + Math.random() * 60; g.fillStyle = `rgba(${c},${c},${c - 4},0.25)`; g.fillRect(Math.random() * 512, Math.random() * 512, 2, 2); }
  for (let i = 0; i < 6; i++) { g.fillStyle = `rgba(40,36,30,${0.08 + Math.random() * 0.1})`; g.beginPath(); g.ellipse(Math.random() * 512, Math.random() * 512, 30 + Math.random() * 60, 20 + Math.random() * 40, Math.random() * 3, 0, 6.28); g.fill(); }
  g.fillStyle = 'rgba(30,30,30,0.5)'; g.fillRect(255, 0, 2, 512); g.fillRect(0, 255, 512, 2); });
conc.wrapS = conc.wrapT = THREE.RepeatWrapping; conc.repeat.set(4, 4);
const floor = new THREE.Mesh(new THREE.PlaneGeometry(14, 14).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ map: conc, roughness: 0.85 })); floor.receiveShadow = true; home.add(floor);
const drywall = mat(0xd8d4ca, 0.95);
box(GW1 - GW0, GH, 0.12, (GW0 + GW1) / 2, GH / 2, GBACK, drywall, 0, home);
box(0.12, GH, GDOOR_Z - GBACK, GW0, GH / 2, (GDOOR_Z + GBACK) / 2, drywall, 0, home);
box(0.12, GH, GDOOR_Z - GBACK, GW1, GH / 2, (GDOOR_Z + GBACK) / 2, drywall, 0, home);
box(GW1 - GW0 + 0.2, 0.1, GDOOR_Z - GBACK + 0.2, (GW0 + GW1) / 2, GH, (GDOOR_Z + GBACK) / 2, mat(0xcfcac0, 0.95), 0, home);   // ceiling
// the sectional door: four panels that roll up into the ceiling (beat 6 opens it); a wall strip around it
const gdoor = new THREE.Group(); home.add(gdoor);
const panelTex = canvasTex(512, 128, g => { g.fillStyle = '#e8e6e0'; g.fillRect(0, 0, 512, 128); g.strokeStyle = 'rgba(0,0,0,0.18)'; g.lineWidth = 4; for (let i = 0; i < 4; i++) g.strokeRect(14 + i * 124, 18, 108, 92); g.fillStyle = 'rgba(0,0,0,0.25)'; g.fillRect(0, 124, 512, 4); });
const GPANELS = []; for (let i = 0; i < 4; i++) { const p = new THREE.Mesh(new THREE.BoxGeometry(GW1 - GW0 - 0.3, 0.6, 0.05), new THREE.MeshStandardMaterial({ map: panelTex, roughness: 0.6 })); p.castShadow = true; p.receiveShadow = true; gdoor.add(p); GPANELS.push(p); }
box(0.3, GH, 0.14, GW0 + 0.15, GH / 2, GDOOR_Z, drywall, 0, home); box(0.3, GH, 0.14, GW1 - 0.15, GH / 2, GDOOR_Z, drywall, 0, home); box(GW1 - GW0, GH - 2.45, 0.14, (GW0 + GW1) / 2, (GH + 2.45) / 2, GDOOR_Z, drywall, 0, home);
function setGarageDoor(k) { GPANELS.forEach((p, i) => { const s = i * 0.6 + 0.3, y = s + k * 2.4;                  // each panel rides up the track, then lies flat under the ceiling
  if (y < 2.4) { p.position.set((GW0 + GW1) / 2, y, GDOOR_Z - 0.04); p.rotation.x = 0; } else { p.position.set((GW0 + GW1) / 2, 2.45, GDOOR_Z - 0.04 - (y - 2.4)); p.rotation.x = Math.PI / 2; } }); }
setGarageDoor(0);
// outside (seen when the door is up): driveway, lawn, sky
const outside = new THREE.Group(); scene.add(outside);
{ const sky = new THREE.Mesh(new THREE.PlaneGeometry(40, 16), new THREE.MeshBasicMaterial({ color: 0xa8cce8 })); sky.position.set(0, 6, 22); sky.rotation.y = Math.PI; outside.add(sky);
  const lawn = new THREE.Mesh(new THREE.PlaneGeometry(40, 18).rotateX(-Math.PI / 2), mat(0x5d8a3a, 0.95)); lawn.position.set(0, -0.005, 12.5); outside.add(lawn);
  const drive = new THREE.Mesh(new THREE.PlaneGeometry(5, 12).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ map: conc, roughness: 0.85 })); drive.position.set(-0.2, 0.002, 9.5); outside.add(drive); }
// shelves with boxes and cans, a workbench, a hanging work light
{ const wood = mat(0x9a7a50, 0.8), steelS = mat(0x6a6e74, 0.5, 0.5);
  for (const y of [0.9, 1.5, 2.1]) box(0.45, 0.04, 2.2, GW0 + 0.28, y, -1.8, steelS, 0, home);
  for (const z of [-2.85, -0.75]) box(0.04, 2.2, 0.04, GW0 + 0.48, 1.1, z, steelS, 0, home);
  for (const [y, z, w, h, c] of [[0.92, -2.4, 0.4, 0.3, 0xb08a5a], [0.92, -1.9, 0.35, 0.25, 0x8a6a40], [1.52, -2.5, 0.3, 0.22, 0xc81e1e], [1.52, -1.6, 0.4, 0.35, 0xb08a5a], [2.12, -2.2, 0.38, 0.3, 0x3a6ab0], [0.92, -1.2, 0.3, 0.4, 0x2a2a2e], [1.52, -1.05, 0.25, 0.3, 0xe8c040]])
    box(0.38, h, w, GW0 + 0.28, y + h / 2 + 0.02, z, mat(c, 0.7), 0.01, home);
  box(2.2, 0.06, 0.65, 0.2, 0.92, GBACK + 0.4, wood, 0.01, home); for (const x of [-0.8, 1.2]) box(0.06, 0.9, 0.55, x, 0.45, GBACK + 0.4, wood, 0, home);
  box(1.8, 0.9, 0.03, 0.2, 1.7, GBACK + 0.08, mat(0x8a6a48, 0.9), 0, home);    // pegboard
  for (let i = 0; i < 7; i++) box(0.04, 0.22, 0.03, -0.5 + i * 0.22, 1.75, GBACK + 0.12, mat(0x3a3a40, 0.4, 0.6), 0.005, home); }
const workLight = new THREE.PointLight(0xfff0d8, 9, 9, 1.4); workLight.position.set(-0.6, 2.6, 0.8); workLight.castShadow = true; workLight.shadow.mapSize.set(1024, 1024); scene.add(workLight);
{ const fx = new THREE.Mesh(new THREE.BoxGeometry(1.2, 0.05, 0.14), new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xfff4e0, emissiveIntensity: 1.2 })); fx.position.set(-0.6, GH - 0.06, 0.8); home.add(fx); }
// the CO alarm on the wall by the door (beat 6)
const alarm = new THREE.Group(); alarm.position.set(GW0 + 0.07, 1.55, 2.6); alarm.rotation.y = Math.PI / 2; home.add(alarm);
const alarmCanvas = document.createElement('canvas'); alarmCanvas.width = 256; alarmCanvas.height = 256; const alarmTex = new THREE.CanvasTexture(alarmCanvas); alarmTex.colorSpace = THREE.SRGBColorSpace;
let alarmState = -1;
function drawAlarm(on) { const g = alarmCanvas.getContext('2d'); g.fillStyle = '#f2f0ea'; g.fillRect(0, 0, 256, 256);
  g.fillStyle = '#2a2a2e'; g.font = 'bold 24px sans-serif'; g.textAlign = 'center'; g.fillText('CARBON MONOXIDE', 128, 50); g.fillText('ALARM', 128, 82);
  g.fillStyle = '#1a2a1a'; g.fillRect(58, 104, 140, 58); g.fillStyle = on ? '#ff3a2a' : '#5aff6a'; g.font = 'bold 44px monospace'; g.fillText(on ? 'CO' : '0', 128, 150);
  g.fillStyle = on ? '#ff2a20' : '#4a1a1a'; g.beginPath(); g.arc(128, 206, 18, 0, 6.28); g.fill(); g.fillStyle = 'rgba(0,0,0,0.3)'; for (let i = 0; i < 5; i++) g.fillRect(40 + i * 40, 232, 22, 6);
  alarmTex.needsUpdate = true; }
drawAlarm(false);
{ const body = new THREE.Mesh(new RoundedBoxGeometry(0.16, 0.16, 0.05, 3, 0.02), mat(0xf2f0ea, 0.5)); alarm.add(body);
  const face = new THREE.Mesh(new THREE.PlaneGeometry(0.15, 0.15), new THREE.MeshStandardMaterial({ map: alarmTex, emissive: 0xffffff, emissiveMap: alarmTex, emissiveIntensity: 0.25 })); face.position.z = 0.026; alarm.add(face); }
const alarmLight = new THREE.PointLight(0xff2a20, 0, 1.2, 2); alarmLight.position.set(0, -0.05, 0.12); alarm.add(alarmLight);

// ------------------------------------------------------------------ the pickup (nose toward the back wall); its tailpipe at the back left
const truck = new THREE.Group(); scene.add(truck);
const TPIPE = V(-1.02, 0.34, 1.1);                                   // the tailpipe's open end: a side exit just ahead of the back left wheel (truck space = world)
{ const paintT = new THREE.MeshPhysicalMaterial({ color: 0x1e3a5a, roughness: 0.35, clearcoat: 1, clearcoatRoughness: 0.1, metalness: 0.3 }), darkT = mat(0x18191b, 0.7), chromeT = mat(0xdddddd, 0.18, 1);
  const glassT = new THREE.MeshPhysicalMaterial({ color: 0x2c353c, roughness: 0.05, transparent: true, opacity: 0.88 });
  const B = (w, h, d, x, y, z, m, r = 0.04) => box(w, h, d, x, y, z, m, r, truck);
  B(1.96, 0.62, 1.6, 0, 0.86, -1.85, paintT, 0.1);                   // hood / engine
  B(1.96, 0.7, 1.45, 0, 0.9, -0.33, paintT, 0.08);                   // cab lower
  B(1.86, 0.62, 1.3, 0, 1.55, -0.36, glassT, 0.08);                  // cab glass
  B(1.9, 0.08, 1.36, 0, 1.88, -0.36, paintT, 0.04);                  // roof
  for (const s of [-1, 1]) B(0.08, 0.6, 0.08, s * 0.92, 1.55, -1.0, paintT, 0.02);
  B(1.96, 0.18, 2.3, 0, 0.62, 1.55, paintT, 0.04);                   // bed floor
  for (const s of [-1, 1]) B(0.07, 0.55, 2.3, s * 0.95, 0.98, 1.55, paintT, 0.03);   // bed sides (top 1.25)
  B(1.96, 0.55, 0.07, 0, 0.98, 2.68, paintT, 0.03);                  // tailgate
  B(2.0, 0.16, 0.14, 0, 0.5, 2.78, chromeT, 0.04);                   // rear bumper
  B(2.0, 0.2, 0.16, 0, 0.55, -2.68, chromeT, 0.05);                  // front bumper
  B(1.6, 0.34, 0.04, 0, 0.98, -2.66, mat(0x2a2c30, 0.4, 0.6), 0.02); // grille
  for (const s of [-1, 1]) { B(0.3, 0.14, 0.04, s * 0.72, 1.0, 2.71, new THREE.MeshStandardMaterial({ color: 0xaa1010, emissive: 0x880000, emissiveIntensity: 0.6 }), 0.02);
    B(0.32, 0.14, 0.04, s * 0.62, 1.0, -2.69, new THREE.MeshStandardMaterial({ color: 0xffffee, emissive: 0x666655 }), 0.02); }
  for (const [x, z] of [[-0.88, -1.85], [0.88, -1.85], [-0.88, 1.75], [0.88, 1.75]]) { const t = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.4, 0.3, 28).rotateZ(Math.PI / 2), darkT); t.position.set(x, 0.4, z); t.castShadow = true; truck.add(t);
    const h = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.22, 0.31, 18).rotateZ(Math.PI / 2), chromeT); h.position.set(x, 0.4, z); truck.add(h); }
  const pipe = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.4, 14).rotateZ(Math.PI / 2), chromeT); pipe.position.copy(TPIPE).add(V(0.2, 0, 0)); truck.add(pipe);
  const hole = new THREE.Mesh(new THREE.CircleGeometry(0.032, 14).rotateY(-Math.PI / 2), mat(0x0a0a0a, 0.9)); hole.position.copy(TPIPE).add(V(-0.002, 0, 0)); truck.add(hole); }

// ------------------------------------------------------------------ exhaust: camera-facing puffs placed from time alone; a haze that fills the garage
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
const SMOKE = puffs(700, `vec2 p = vUv * 2.0 - 1.0; float s = vO.w * 13.0;
  float n = vn(p * 2.0 + s - vec2(0.0, uT * 0.8)) * 0.6 + vn(p * 5.0 - s * 2.0) * 0.4;
  float r = dot(p, p) + (n - 0.5) * 0.8; float a = (1.0 - smoothstep(0.25, 0.95, r)) * vO.y; if (a < 0.004) discard;
  vec3 col = mix(vec3(0.16, 0.15, 0.15), vec3(0.93, 0.94, 0.96), vO.x) * (0.85 + 0.3 * n);
  gl_FragColor = vec4(col, a);`, THREE.NormalBlending);
// the exhaust: puffs pour out of the pipe, roll along the floor and rise; k = how much (0..1), fill = how full the garage is (0..1)
function exhaust(t, k, fill) {
  if (k > 0.01) for (let i = 0; i < 260; i++) { const a = ((t * (0.35 + 0.25 * hash1(i * 3.1)) + hash1(i * 1.9)) % 1), ang = hash1(i * 5.1) * 6.283;
    const sp = V(-0.8 + Math.cos(ang) * 0.3, 0, Math.sin(ang) * 0.6).multiplyScalar(a * (1.1 + 0.8 * hash1(i * 2.7)));     // out the side, spreading along the floor
    const p = TPIPE.clone().add(V(-0.05, 0.02, 0)).add(sp).add(V(vn1(t * 0.7 + i, 2) * 0.15 * a, 0.9 * a * a + 0.05 * a, vn1(t * 0.6 + i, 4) * 0.1 * a));
    p.z = Math.min(p.z, GDOOR_Z - 0.15 - 0.3 * hash1(i)); p.x = clamp(p.x, GW0 + 0.2, GW1 - 0.2);
    SMOKE.add(p, 0.05 + 0.45 * a, 0.75, Math.sin(Math.PI * Math.min(1, a * 1.2)) * 0.42 * k, hash1(i * 6.6)); }
  if (fill > 0.01) for (let i = 0; i < 160; i++) { const p = V(GW0 + 0.4 + hash1(i * 7.1) * (GW1 - GW0 - 0.8) + vn1(t * 0.2 + i, 1) * 0.3, 0.3 + hash1(i * 3.3) * 2.3 * Math.min(1, fill * 1.4), GBACK + 0.4 + hash1(i * 5.9) * (GDOOR_Z - GBACK - 0.8) + vn1(t * 0.2 + i, 3) * 0.3);
    SMOKE.add(p, 0.6 + 0.6 * hash1(i * 2.2), 0.7, 0.1 * fill * (0.5 + 0.5 * hash1(i * 9.1)), hash1(i * 4.7)); } }

// ------------------------------------------------------------------ x-ray: the glow body (same skeleton) with the heart and the brain
const xrayMat = new THREE.MeshStandardMaterial({ color: 0x000000, emissive: 0x58b8ff, emissiveIntensity: 1, transparent: true, opacity: 1, depthWrite: false, blending: THREE.AdditiveBlending, roughness: 1, metalness: 0 });
xrayMat.onBeforeCompile = sh => { sh.fragmentShader = sh.fragmentShader.replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\n  totalEmissiveRadiance *= 0.015 + 0.85 * pow(1.0 - abs(dot(normalize(normal), normalize(vViewPosition))), 2.4);'); };
const XRAY = [], NORMAL = [];
G.root.traverse(o => { if (!o.isMesh || o.userData.xray) return; NORMAL.push(o); });
for (const o of Object.entries(G.meshes).filter(([n]) => !/^(hair|hairCards|sole)/.test(n)).map(([, m]) => m)) {
  let x; if (o.isSkinnedMesh) { x = new THREE.SkinnedMesh(o.geometry, xrayMat); x.bind(o.skeleton, o.bindMatrix); } else x = new THREE.Mesh(o.geometry, xrayMat);
  x.userData.xray = true; x.position.copy(o.position); x.quaternion.copy(o.quaternion); x.scale.copy(o.scale); x.frustumCulled = false; x.castShadow = false; x.renderOrder = 5; o.parent.add(x); XRAY.push(x); }
G.reset(); G.root.updateMatrixWorld(true);
const toLocal = (bone, p) => bone.worldToLocal(p.clone());
const HC = V(...G.man.headC);
// the heart: two lobes and a point, slightly to his left of centre; it squeezes with each beat
const heartM = new THREE.MeshStandardMaterial({ color: 0x8a1a2a, emissive: 0xff2a3a, emissiveIntensity: 0.9, roughness: 0.4 });
const heart = new THREE.Group(); G.bones.chest.add(heart); heart.position.copy(toLocal(G.bones.chest, V(-0.025, 1.31, -0.04)));
{ const hg = new THREE.Group(); heart.add(hg); hg.rotation.z = -0.45; hg.rotation.x = 0.2;
  for (const s of [-1, 1]) { const l = new THREE.Mesh(new THREE.SphereGeometry(0.03, 24, 16), heartM); l.position.set(s * 0.02, 0.012, 0); hg.add(l); }
  const pt = new THREE.Mesh(new THREE.ConeGeometry(0.043, 0.07, 24).rotateX(Math.PI), heartM); pt.position.y = -0.03; pt.scale.z = 0.75; hg.add(pt);
  const ao = new THREE.Mesh(new THREE.TorusGeometry(0.02, 0.008, 8, 16, Math.PI), heartM); ao.position.set(0.0, 0.045, 0); hg.add(ao); }
const heartGlow = new THREE.PointLight(0xff3040, 0, 0.6, 2); heart.add(heartGlow);
// the brain (beat 5: electric storm)
const brainM = new THREE.MeshStandardMaterial({ color: 0x9a5a7a, emissive: 0xff8ab8, emissiveIntensity: 0.6, roughness: 0.45 });
const brain = new THREE.Group(); G.bones.head.add(brain); brain.position.copy(toLocal(G.bones.head, HC.clone().add(V(0, 0.035, 0.012)))); brain.scale.setScalar(0.86);
{ const g = new THREE.SphereGeometry(0.072, 48, 32); const p = g.attributes.position; for (let i = 0; i < p.count; i++) { const v = V(p.getX(i), p.getY(i), p.getZ(i)).normalize();
    const fold = 0.0035 * Math.sin(v.x * 40 + Math.sin(v.y * 25) * 2) * Math.sin(v.z * 35 + v.y * 20) + (Math.abs(v.x) < 0.06 ? -0.006 : 0);
    v.multiplyScalar(0.072 + fold); v.y *= 0.82; v.z *= 1.18; p.setXYZ(i, v.x, v.y, v.z); } g.computeVertexNormals(); brain.add(new THREE.Mesh(g, brainM)); }
// lightning in the brain: jagged glowing tubes, rebuilt from time alone
const ORGANS = [heart, brain];
let XRON = false, XRNEW = false;
function setXray(k) { if ((k > 0.01) !== XRON) { XRON = k > 0.01; XRNEW = XRON; }   // the first draw after the ghost comes on comes out blank: draw() renders that frame twice
  for (const x of XRAY) x.visible = k > 0.01; xrayMat.emissiveIntensity = 0.75 * k;
  for (const o of NORMAL) o.visible = k < 0.6; for (const o of ORGANS) o.visible = k > 0.5; }
// his phone (scrolling while the truck warms up)
const phone = new THREE.Group(); scene.add(phone);
const phoneCanvas = document.createElement('canvas'); phoneCanvas.width = 160; phoneCanvas.height = 330;
const phoneTex = new THREE.CanvasTexture(phoneCanvas); phoneTex.colorSpace = THREE.SRGBColorSpace;
function drawPhone(scroll) { const g = phoneCanvas.getContext('2d'); g.fillStyle = '#111418'; g.fillRect(0, 0, 160, 330);
  for (let i = -1; i < 5; i++) { const y = i * 96 - (scroll % 96); g.fillStyle = ['#e85a4a', '#4a9ae8', '#f2c14a', '#6ad08a', '#b06ae8'][(i + Math.floor(scroll / 96) + 50) % 5]; g.fillRect(10, y + 8, 140, 64); g.fillStyle = '#3a3f48'; g.fillRect(10, y + 78, 90, 8); }
  phoneTex.needsUpdate = true; }
{ box(0.072, 0.152, 0.009, 0, 0, 0, mat(0x1c1d22, 0.3, 0.6), 0.004, phone); const s = new THREE.Mesh(new THREE.PlaneGeometry(0.064, 0.142), new THREE.MeshBasicMaterial({ map: phoneTex, toneMapped: false })); s.position.z = 0.0048; phone.add(s); }
drawPhone(0); let phoneState = -1;
// the dark that closes in when he passes out (a ring in front of the camera)
scene.add(camera);
const vigM = new THREE.ShaderMaterial({ uniforms: { uR: { value: 1.5 }, uAsp: { value: W / H } }, transparent: true, depthTest: false, depthWrite: false,
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
  fragmentShader: `uniform float uR, uAsp; varying vec2 vUv;
    void main(){ vec2 p = (vUv - 0.5) * vec2(uAsp, 1.0) * 2.0; float d = length(p);       // 0 at the centre, ~1 at the top/bottom edges
      float a = smoothstep(uR, uR + 0.45, d); gl_FragColor = vec4(0.0, 0.0, 0.0, a); }` });
const vig = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), vigM); vig.position.z = -0.1; vig.renderOrder = 20; camera.add(vig);
function setVignette(k) { vig.visible = k > 0.01; const h = 2 * 0.1 * Math.tan(camera.fov * D2R / 2), w = h * camera.aspect; vig.scale.set(w * 1.02, h * 1.02, 1);   // always covers the whole frame
  vigM.uniforms.uR.value = lerp(1.3, 0.02, k); }                      // the clear middle shrinks: the dark closes in from the edges
const blackM = new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, depthTest: false, depthWrite: false }); const black = new THREE.Mesh(new THREE.PlaneGeometry(10, 10), blackM); black.position.z = -0.11; black.renderOrder = 21; camera.add(black);

// ------------------------------------------------------------------ inside a blood vessel (beat 2): red cells carrying oxygen; carbon monoxide pushes the oxygen off and holds on
const VES = V(40, 0, 0);
const vessel = new THREE.Group(); vessel.position.copy(VES); scene.add(vessel);
const vesLight = new THREE.PointLight(0xffe0e0, 0, 6, 1.2); vesLight.position.set(0, 0.3, 0.6); vessel.add(vesLight);
{ const wallTex = canvasTex(512, 256, g => { g.fillStyle = '#8a1a24'; g.fillRect(0, 0, 512, 256); for (let i = 0; i < 300; i++) { g.fillStyle = `rgba(${150 + Math.random() * 60 | 0},30,40,0.35)`; g.beginPath(); g.ellipse(Math.random() * 512, Math.random() * 256, 8 + Math.random() * 20, 4 + Math.random() * 8, 0, 0, 6.28); g.fill(); } });
  wallTex.wrapS = wallTex.wrapT = THREE.RepeatWrapping; wallTex.repeat.set(3, 2);
  const tube = new THREE.Mesh(new THREE.CylinderGeometry(0.9, 0.9, 12, 40, 1, true).rotateX(Math.PI / 2), new THREE.MeshStandardMaterial({ map: wallTex, side: THREE.BackSide, roughness: 0.6, emissive: 0x3a0a10, emissiveIntensity: 0.5 })); vessel.add(tube);
  vessel.add(new THREE.Mesh(new THREE.SphereGeometry(8, 16, 8), new THREE.MeshBasicMaterial({ color: 0x1a0306, side: THREE.BackSide }))); }
const rbcG = (() => { const pts = []; for (let i = 0; i <= 24; i++) { const r = 0.16 * i / 24; const h = 0.035 * (0.45 + 1.2 * (r / 0.16) ** 2 - 1.4 * (r / 0.16) ** 4) * Math.sqrt(Math.max(0, 1 - (r / 0.16) ** 2)) + 0.004; pts.push(new THREE.Vector2(r, h)); }
  for (let i = 24; i >= 0; i--) pts.push(new THREE.Vector2(0.16 * i / 24, -pts[i].y)); return new THREE.LatheGeometry(pts, 40); })();   // a red blood cell: a dimpled disc
const rbcM = new THREE.MeshStandardMaterial({ color: 0xd8242e, emissive: 0x5a0a10, emissiveIntensity: 0.4, roughness: 0.4 });
const RBCN = 9, RBC = []; for (let i = 0; i < RBCN; i++) { const m = new THREE.Mesh(rbcG, rbcM.clone()); vessel.add(m); RBC.push(m); }
const o2M = new THREE.MeshStandardMaterial({ color: 0xff4a4a, emissive: 0xc01010, emissiveIntensity: 0.6, roughness: 0.3 });   // oxygen: two red balls
const cM = new THREE.MeshStandardMaterial({ color: 0x1a1a1e, roughness: 0.4 }), oM = o2M;                                       // carbon monoxide: a black ball and a red ball
function mol(a, b, r) { const g = new THREE.Group(); const m1 = new THREE.Mesh(new THREE.SphereGeometry(r, 16, 12), a), m2 = new THREE.Mesh(new THREE.SphereGeometry(r, 16, 12), b); m1.position.x = -r * 0.8; m2.position.x = r * 0.8; g.add(m1, m2); vessel.add(g); return g; }
const O2S = [], COS = []; for (let i = 0; i < RBCN * 2; i++) { O2S.push(mol(o2M, o2M, 0.022)); COS.push(mol(cM, oM, 0.024)); }
function vtag(text, color, w) { const c = canvasTex(512, 128, g => { g.fillStyle = 'rgba(10,10,14,0.75)'; g.beginPath(); g.roundRect(4, 4, 504, 120, 30); g.fill(); g.fillStyle = color; g.font = 'bold 64px sans-serif'; g.textAlign = 'center'; g.fillText(text, 256, 86); });
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: c, depthTest: false, toneMapped: false })); s.scale.set(w, w / 4, 1); s.renderOrder = 10; vessel.add(s); return s; }
const tagO2 = vtag('OXYGEN', '#ff8a8a', 0.34), tagCO = vtag('CO', '#e8e8e8', 0.2);
const _M = new THREE.Matrix4(), _Q = new THREE.Quaternion(), _S = V(1, 1, 1);
// a big red X over the open-door shot (beat 6: still not safe)
const redX = new THREE.Sprite(new THREE.SpriteMaterial({ map: canvasTex(256, 256, g => { g.strokeStyle = '#ff2a20'; g.lineWidth = 34; g.lineCap = 'round'; g.beginPath(); g.moveTo(40, 40); g.lineTo(216, 216); g.moveTo(216, 40); g.lineTo(40, 216); g.stroke(); }), depthTest: false, toneMapped: false, transparent: true }));
redX.scale.set(1.6, 1.6, 1); redX.position.set(-0.3, 1.2, 2.2); redX.renderOrder = 12; scene.add(redX);
// a sick green tint over the picture (beats 4-5)
const tintM = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 1, depthTest: false, depthWrite: false, blending: THREE.MultiplyBlending, premultipliedAlpha: true }); const tint = new THREE.Mesh(new THREE.PlaneGeometry(10, 10), tintM); tint.position.z = -0.105; tint.renderOrder = 19; camera.add(tint);
// carbon monoxide in the air at the pipe (beat 1): shown, then it fades away to nothing (you can't see it)
const coAirC = new THREE.MeshStandardMaterial({ color: 0x1a1a1e, roughness: 0.4, transparent: true }), coAirO = new THREE.MeshStandardMaterial({ color: 0xff4a4a, emissive: 0xc01010, emissiveIntensity: 0.6, roughness: 0.3, transparent: true });
const COAIR = []; for (let i = 0; i < 16; i++) { const g = new THREE.Group(); for (const [m, x] of [[coAirC, -0.016], [coAirO, 0.016]]) { const s = new THREE.Mesh(new THREE.SphereGeometry(0.02, 14, 10), m); s.position.x = x; g.add(s); } g.renderOrder = 8; scene.add(g); COAIR.push(g); }
const PH = { rot: 15, n: 0.0165, u: 0.0, w: 0.0, c: 40, th: 30, opp: 30 };   // the phone in his hand: angle of its long side off the palm's width, offsets, finger curl
window.PH = PH;

// ------------------------------------------------------------------ the story
const STANDP = V(-1.45, 0, 2.05);                                   // where he stands: by the truck's back left corner, facing the back wall (-z)
const YAW = 0;
const LOOPSEED = { R: null, L: null };
function blinkAt(s) { const u = ((s + 40) % 3.7) / 0.16; return u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0; }
const F = fwdOf(YAW), Rt = rightOf(YAW), UP = V(0, 1, 0);         // his forward (-z), his right (+x, the truck side), up
const STAND1 = { ...addPose(STAND, { spine1: [-4, 0, 0], neck: [6, 0, 0] }), armL: A(10, 14, 0, 22), armR: A(10, 14, 0, 22) };
// his phone in the left hand, screen toward his face
function phoneHand() { const hd = wp(G.bones.head), n = UP.clone().multiplyScalar(0.62).addScaledVector(F, -0.78).normalize(), u = F.clone().multiplyScalar(0.78).addScaledVector(UP, 0.62).normalize();
  return { S: 'L', p: hd.clone().addScaledVector(F, 0.27).addScaledVector(Rt, 0.04).add(V(0, -0.32, 0)), n, u, c: PH.c, th: PH.th, opp: PH.opp, memAbs: 'phoneL', seed: A(40, 10, 0, 110, -40) }; }
// his left palm on his forehead (headache)
function browHand() { const hd = wp(G.bones.head), q = wq(G.bones.head), fwdH = V(0, 0, -1).applyQuaternion(q), upH = V(0, 1, 0).applyQuaternion(q);
  return { S: 'L', p: hd.clone().addScaledVector(fwdH, 0.14).addScaledVector(upH, 0.06), n: fwdH.clone().negate(), u: Rt.clone().addScaledVector(upH, 0.3).normalize(), c: 18, th: 15, soft: 0.012, memAbs: 'browL', seed: A(110, 20, 20, 135, -20) }; }
// his right hand catching himself on the truck's bed rail (top 1.25, its side at x = -0.98)
function railHand(dz = 0) { return { S: 'R', p: V(-0.99, 1.265, STANDP.z - 0.12 + dz), n: V(0, -1, 0), u: F.clone().addScaledVector(Rt, 0.4).normalize(), c: 45, th: 30, memAbs: 'railR', seed: A(40, 30, 0, 50, -40) }; }

// the state at a time ----------------------------------------------
function guyAt(t) {
  const b = beatAt(t), lt = t - B[b], d = DUR[b];
  const face = { blink: blinkAt(lt + b * 1.3) };
  let pose = STAND1, root = { x: STANDP.x, y: 0.95, z: STANDP.z, yaw: YAW }, hands = [], show = true, cut = false;
  let ex = 1, fill = 0, xr = 0, phoneOn = false, phoneScroll = 0, vesT = -1, starve = 0, sick = 0, vig = 0, black = 0, door = 0, alarmOn = false, alarmShot = false, crank = -1, sway = 0, redX = 0;
  if (b === 7 || b === 0) {                                         // 7: he's just started it and stands scrolling while it warms up; 0: the garage fills
    phoneOn = true; phoneScroll = (b === 7 ? lt : DUR[7] + lt) * 50;
    hands = [b === 0 && LOOPSEED.L ? { ...phoneHand(), seed: LOOPSEED.L, seedIsPrev: true } : phoneHand()];
    pose = addPose(STAND1, { neck: [-16, 0, 0], head: [-10, 0, 0] }); Object.assign(face, { look: [0, -0.6] });
    if (b === 7) { crank = lt; ex = smooth(0.3, 1.2, lt) * 0.6; fill = 0; } else { ex = 0.6 + 0.4 * smooth(0, d, lt); fill = 0.25 * smooth(0, d, lt); }
  } else if (b === 1) {                                             // the exhaust up close at the pipe: you can't see it or smell it
    ex = 0.45; fill = 0.15; phoneOn = true; phoneScroll = (DUR[7] + DUR[0] + lt) * 50; hands = [phoneHand()];
    pose = addPose(STAND1, { neck: [-16, 0, 0], head: [-10, 0, 0] }); Object.assign(face, { look: [0, -0.6] });
  } else if (b === 2) {                                             // inside his blood: the CO pushes the oxygen off the red cells
    show = false; vesT = lt; ex = 0;
  } else if (b === 3) {                                             // x-ray: his brain and heart go dim
    xr = 1; starve = smooth(0.2, d, lt); ex = 1; fill = 0.4;
    pose = addPose(STAND1, { neck: [-4, 0, 0] });
  } else if (b === 4) {                                             // headache, dizzy, sick: hand to his forehead, swaying
    ex = 1; fill = 0.5 + 0.1 * smooth(0, d, lt); sick = smooth(0, d, lt); sway = sick;
    hands = [{ ...browHand(), blend: smooth(0.15, 1.0, lt) }];
    pose = addPose(STAND1, { neck: [6 * sick, 4 * Math.sin(lt * 2.2) * sick, 3 * Math.sin(lt * 1.7) * sick], head: [4, 0, 0], spine1: [3 * Math.sin(lt * 1.6) * sick, 0, 2 * Math.sin(lt * 1.3) * sick] });
    Object.assign(face, { squint: 0.6 * sick, brow: 0.7 * sick, jaw: 0.1, look: [0, -0.2] });
  } else if (b === 5) {                                             // confused, weak: he catches himself on the truck; it all goes dark
    ex = 1; fill = 0.65; sick = 1; sway = 1; const k = smooth(0, 1.2, lt);
    { const h = railHand(); h.p.y += 0.12 * (1 - k) ** 2; h.p.x -= 0.08 * (1 - k); hands = [{ ...h, blend: k }]; }     // comes over the rail and down onto it
    pose = addPose(STAND1, { spine1: [10 * k, 0, 6 * k], spine2: [6 * k, 0, 4 * k], neck: [-10 * k + 4 * Math.sin(lt * 2), 6 * Math.sin(lt * 1.4), 0], head: [-6 * k, 0, 4 * k] });
    root = { x: STANDP.x + 0.08 * k, y: 0.95 - 0.05 * k, z: STANDP.z, yaw: YAW + 8 * k };
    vig = smooth(0.4, d - 0.25, lt) * (1 - 0.06 * Math.max(0, Math.sin(lt * 7.5))); black = smooth(d - 0.45, d - 0.05, lt);      // the edges go dark in waves (each heartbeat), then black
    Object.assign(face, { squint: 0.4, brow: 0.5, jaw: 0.25, look: [0.2, -0.3], blink: lt > d - 1.0 ? smooth(d - 1.0, d - 0.4, lt) : 0 });
  } else if (b === 6) {                                             // the door wide open is still not safe; then the alarm: get out
    show = false; ex = 1; door = 1; fill = 0.25;
    cut = lt >= 2.2 && lt - 2.2 < 1 / 30 + 1e-6;
    if (lt < 2.2) redX = smooth(0.7, 1.0, lt); else { alarmShot = true; alarmOn = Math.floor((lt - 2.2) / 0.25) % 2 === 0; }
  }
  const wb = 2 * Math.PI * Math.round(TOTAL / 2.6) / TOTAL;           // breathing (whole cycles over the loop)
  pose = addPose(pose, { spine1: [0.9 * Math.sin(wb * t), 0, 0], spine2: [0.6 * Math.sin(wb * t + 0.4), 0, 0], neck: [0.7 * Math.sin(wb * t + 1.1), 0, 0] });
  return { b, lt, d, pose, root, hands, show, cut, ex, fill, xr, phoneOn, phoneScroll, vesT, starve, sick, vig, black, door, alarmOn, alarmShot, crank, sway, redX, face };
}

// ------------------------------------------------------------------ cameras
function shakeV(t, a) { return V(vn1(t * 14, 1) * a * 0.5, vn1(t * 14, 2) * a, vn1(t * 14, 3) * a); }
const CAM7 = { pos: V(-2.55, 1.8, 0.15), tgt: V(-1.15, 0.95, 2.6), fov: 52 };      // at his front-left by the shelves: his face, the truck's back end, the pipe, the shut door behind him
function camAt(t, g) {
  const b = g.b, lt = g.lt, d = g.d, k = smooth(0, d, lt);
  if (b === 7) return { pos: CAM7.pos.clone().add(V(0.05 * (1 - k), 0.05 * (1 - k), -0.1 * (1 - k))), tgt: CAM7.tgt, fov: CAM7.fov };
  if (b === 0) return { pos: CAM7.pos.clone().lerp(V(-2.4, 1.72, 0.5), k), tgt: CAM7.tgt.clone().lerp(V(-1.2, 0.95, 2.6), k), fov: 52 - 4 * k };
  if (b === 1) return { pos: TPIPE.clone().add(V(-0.55, 0.32, -1.05 + 0.15 * k)), tgt: TPIPE.clone().add(V(-0.35, 0.18, 0.15)), fov: 42 };
  if (b === 2) return { pos: VES.clone().add(V(0.05, 0.08, 1.6 - 0.5 * k)), tgt: VES.clone().add(V(0, 0, -1.0)), fov: 55 };
  if (b === 3) return { pos: V(-1.75, 1.55, 1.2 - 0.1 * k), tgt: V(-1.45, 1.42, 2.05), fov: 46 };
  if (b === 4) { const r = 2.5 * Math.sin(lt * 1.7) * g.sick; return { pos: V(-1.85, 1.62, 1.15).add(shakeV(t * 0.3, 0.02 * g.sick)), tgt: V(-1.45, 1.5, 2.05), fov: 42, roll: r }; }
  if (b === 5) { const r = 5 * Math.sin(lt * 1.4) * g.sick; return { pos: V(-2.05, 1.55, 0.85).add(shakeV(t * 0.3, 0.03)), tgt: V(-1.3, 1.2, 2.1), fov: 48 + 6 * k, roll: r }; }
  if (b === 6) { if (!g.alarmShot) return { pos: V(0.9, 1.7, 7.2 - 0.4 * smooth(0, 2.2, lt)), tgt: V(-0.2, 1.0, 2.0), fov: 50 };
    return { pos: V(GW0 + 0.75, 1.58, 2.6), tgt: V(GW0, 1.55, 2.6), fov: 40 }; }
  return CAM7;
}

// ------------------------------------------------------------------ clipping: him vs the truck, the floor and his own body
const SOLIDS = [];
const sbox = (name, obj, min, max) => SOLIDS.push({ name, obj, box: new THREE.Box3(min, max) });
sbox('truck bed', truck, V(-1.0, 0.1, 0.25), V(1.0, 1.25, 2.85)); sbox('truck cab', truck, V(-1.0, 0.1, -2.75), V(1.0, 1.9, 0.25));
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
// depth inside his body (> 0 = inside), from the 4 nearest skin samples weighted by nearness (one sample flips sign in creases)
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
  const solids = SOLIDS.filter(sd => sd.obj.visible && !/^couch/.test(sd.name)).map(sd => ({ inv: sd.obj.matrixWorld.clone().invert(), box: sd.box }));
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
let STATE = null;
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
function propFromHand(obj, S, build) { const q = wq(G.bones['hand' + S]), h = RG.HANDREST[S];
  const n = h.n.clone().applyQuaternion(q), w = h.w.clone().applyQuaternion(q), u = h.u.clone().applyQuaternion(q); build(obj, RG.palmW(S), n, u, w); }
const basisQ = (x, y) => { const X = x.clone().normalize(), Y = y.clone().addScaledVector(X, -y.dot(X)).normalize(), Z = new THREE.Vector3().crossVectors(X, Y); return new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(X, Y, Z)); };
const HAZE = new THREE.Color(0x8a8a86);
function update(t, frame) {
  t = ((t % TOTAL) + TOTAL) % TOTAL;
  let g = guyAt(t); STATE = { b: g.b };
  setGarageDoor(g.door); outside.visible = g.door > 0.01;
  scene.updateMatrixWorld(true);
  // him
  G.root.visible = g.show;
  RG.applyPose(g.pose, g.root);
  const yaw = g.root.yaw, f = fwdOf(yaw), r = rightOf(yaw);
  const ground = V(g.root.x, 0, g.root.z);
  for (const [S, sx] of [['R', 0.11], ['L', -0.11]]) {
    const fp = V(STANDP.x, 0, STANDP.z).addScaledVector(rightOf(YAW), sx).addScaledVector(fwdOf(YAW), S === 'R' ? 0.02 : -0.02);     // feet stay planted while he sways
    fp.y = ANKLEH; RG.foot(S, fp, fp.clone().add(V(0, 0.45, 0)).addScaledVector(fwdOf(YAW), 1), yawQ(YAW)); }
  G.root.updateMatrixWorld(true);
  const list = [];
  if (g.show) { BODYNOW = surfNow(); const g2 = guyAt(t); g.hands = g2.hands; for (const h of g.hands) list.push(h); }
  for (const h of list) if (h.memAbs) h.memAbs += ':' + g.b;            // a hold never carries across a cut (chunks start each beat cold, so must a straight render)
  if (list.length) { RG.hands(list, 'b' + g.b, frame); LASTH = list; }
  for (const S of ['R', 'L']) if (!list.some(h => h.S === S)) delete RG.LAST['cost' + S];
  G.root.updateMatrixWorld(true); RG.untwist(); G.face(g.face); G.root.updateMatrixWorld(true);
  // his phone: in his left hand (screen to him), or in his pocket
  phone.visible = g.show && g.phoneOn;
  if (phone.visible) propFromHand(phone, 'L', (o, pw, n, u, w) => { const ax = w.clone().multiplyScalar(Math.cos(PH.rot * D2R)).addScaledVector(u, Math.sin(PH.rot * D2R));   // long side across the palm: the fingers wrap its edge
    o.quaternion.copy(basisQ(new THREE.Vector3().crossVectors(ax, n), ax)); o.position.copy(pw).addScaledVector(n, PH.n).addScaledVector(u, PH.u).addScaledVector(w, PH.w); });
  const ps = Math.floor(g.phoneScroll); if (ps !== phoneState) { drawPhone(g.phoneScroll); phoneState = ps; }
  // x-ray: brain and heart dim as they starve
  setXray(g.xr); { const pz = Math.exp(-((((t * (80 - 20 * g.starve) / 60) % 1 - 0.05) / 0.06) ** 2)); heart.scale.setScalar(1 + 0.1 * pz * (1 - 0.6 * g.starve));
    heartM.emissiveIntensity = (0.7 + 0.9 * pz) * (1 - 0.8 * g.starve); heartM.emissive.set(0xff2a3a).lerp(new THREE.Color(0x4a5a8a), g.starve); heartGlow.intensity = g.xr > 0.5 ? 0.6 * pz * (1 - g.starve) : 0;
    brainM.emissiveIntensity = 0.6 * (1 - 0.85 * g.starve) + 0.25 * g.starve * (0.5 + 0.5 * Math.sin(t * 9)); brainM.emissive.set(0xff8ab8).lerp(new THREE.Color(0x5a6a9a), g.starve); }
  // exhaust and haze (garage beats only)
  SMOKE.begin(); SMOKE.m.uniforms.uT.value = t; if (g.vesT < 0 && !g.alarmShot) exhaust(t, g.ex, g.fill); SMOKE.end();
  truck.position.y = g.ex > 0.01 ? 0.004 * Math.sin(t * 60) * (g.crank >= 0 && g.crank < 0.8 ? 3 : 1) : 0;       // the engine idles
  // CO in the air at the pipe (beat 1)
  { const on = g.b === 1; const op = on ? smooth(0.1, 0.5, g.lt) * (1 - smooth(1.9, 2.8, g.lt)) : 0; coAirC.opacity = coAirO.opacity = op;
    COAIR.forEach((m, i) => { m.visible = op > 0.01; if (!m.visible) return; const a = ((g.lt * (0.18 + 0.1 * hash1(i * 2.1)) + hash1(i * 4.3)) % 1);
      m.position.copy(TPIPE).add(V(-0.1 - 0.7 * a, 0.05 + 0.35 * a * a + 0.1 * hash1(i * 3.7), (hash1(i * 5.9) - 0.5) * 0.5 * (0.3 + a))); m.rotation.set(g.lt * (1 + hash1(i)), g.lt * 1.3, i); }); }
  // inside the vessel (beat 2): cells drift past; CO arrives at 1.0 s and knocks the oxygen off
  vessel.visible = g.vesT >= 0; vesLight.intensity = g.vesT >= 0 ? 4 : 0;
  if (g.vesT >= 0) { const lt = g.vesT;
    RBC.forEach((c, i) => { const z = 1.0 - ((lt * 0.35 + i / RBCN * 3.2) % 3.2) * 1.0 - 0.2, a = hash1(i * 3.1) * 6.28;
      c.position.set(Math.cos(a) * 0.35 * hash1(i * 5.5), Math.sin(a) * 0.3 * hash1(i * 7.7), z); c.rotation.set(1.2 + 0.4 * Math.sin(lt + i), lt * 0.3 + i, 0.3 * i);
      const hit = smooth(1.2 + 0.25 * i % 1.0, 1.7 + 0.25 * i % 1.0, lt); c.material.color.set(0xd8242e).lerp(new THREE.Color(0xff3a5a), hit * 0.6);
      for (let j = 0; j < 2; j++) { const o = O2S[i * 2 + j], co = COS[i * 2 + j], side = j ? 1 : -1, n = V(0, 0, side).applyEuler(c.rotation);
        const stuck = c.position.clone().addScaledVector(n, 0.05); const h = smooth(1.15 + 0.25 * (i % 4) + 0.1 * j, 1.55 + 0.25 * (i % 4) + 0.1 * j, lt);
        o.position.copy(stuck).add(V(side * 0.4 * h, 0.35 * h, 0.1 * h)); o.rotation.set(lt * 2 * h, 0, i); o.visible = true;
        co.position.copy(c.position.clone().add(V(-side * 0.8, 0.6, 0.6)).lerp(stuck, Math.min(1, h * 1.3))); co.rotation.set(0, lt + i, 0); co.visible = lt > 0.9; } });
    tagO2.position.copy(O2S[3].position).add(V(0, 0.09, 0)); tagO2.material.opacity = smooth(0.2, 0.5, lt) * (1 - smooth(2.6, 2.9, lt));
    tagCO.position.copy(COS[3].position).add(V(0, 0.09, 0)); tagCO.material.opacity = smooth(1.1, 1.4, lt); }
  // the alarm (beat 6)
  { const st = g.alarmOn ? 1 : 0; if (st !== alarmState) { drawAlarm(g.alarmOn); alarmState = st; } alarmLight.intensity = g.alarmOn ? 2.5 : 0; }
  redX.visible = g.redX > 0.01; redX.material.opacity = g.redX;
  // camera (with a dizzy roll), the dark closing in, the sick tint, the haze
  const C = camAt(t, g); camera.position.copy(C.pos); camera.up.set(0, 1, 0); camera.lookAt(C.tgt); if (C.roll) camera.rotateZ(C.roll * D2R); camera.fov = C.fov; camera.updateProjectionMatrix();
  setVignette(g.vig); black.visible = g.black > 0.001; blackM.opacity = g.black;
  tint.visible = g.sick > 0.01; tintM.color.setRGB(1, 1, 1).lerp(new THREE.Color(0.8, 0.95, 0.7), g.sick);
  const garage = g.vesT < 0;
  scene.fog = garage && !g.alarmShot ? new THREE.FogExp2(HAZE, 0.02 + 0.09 * g.fill) : null;
  sun.position.set(1.5, 6, 9); sun.target.position.set(0, 0, 0); sun.target.updateMatrixWorld();
  sun.intensity = g.door > 0.01 ? 2.2 : 0.25; hemi.intensity = garage ? 0.55 : 0.4; scene.environmentIntensity = 0.3; workLight.intensity = garage ? 9 : 0;
  scene.background = new THREE.Color(0x2a2a2a);
  return { beat: g.b, cut: g.cut };
}
G.reset(); G.root.updateMatrixWorld(true);
const ANKLEH = wp(G.bones.footR).y;

// ------------------------------------------------------------------ frame I/O (same contract as the other 3D Shorts)
const draw = () => { if (XRNEW) { renderer.render(scene, camera); XRNEW = false; } renderer.render(scene, camera); };
const gl = renderer.getContext(), px = new Uint8Array(W * H * 4);
let CUTF = false, LASTB = 0;
function segStart(t) { const b = beatAt(t), lt = t - B[b]; if (b === 6 && lt >= 2.2) return B[6] + 2.2; return B[b]; }   // where a hold starts cold
function stepTo(i) { const t = i / FPS, tt = ((t % TOTAL) + TOTAL) % TOTAL;
  if (i !== LASTF + 1) for (let j = Math.ceil(segStart(tt) * FPS - 1e-6) + Math.floor(t / TOTAL) * Math.round(TOTAL * FPS); j < i; j++) update(j / FPS, j);
  const r = update(t, i); CUTF = r.cut; LASTB = r.beat; LASTF = i; }
// the loop: beat 0's phone hand starts where beat 7 ends
for (let i = Math.ceil(B[7] * FPS); i < Math.round(TOTAL * FPS); i++) update(i / FPS, i);
LOOPSEED.L = RG.LAST.armL.slice();
draw(); update(B[3] + 1.0, -50); draw(); update(B[2] + 1.5, -40); draw();     // warm-up: compile the x-ray and the vessel shaders now
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
window.dbg = { G, RG, wp, THREE, LOOPSEED, update, guyAt, renderer, scene, camera, setBN: () => { BODYNOW = surfNow(); }, F, Rt, UP };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS);
window.READY = true;
