// anatomy.js - a detailed see-through body for the x-ray shots (the MakeHuman man, ~1.75 m, standing rest pose: facing -z, his left is -x, up +y).
// Bones: skull with jaw and teeth, every vertebra C1-L5, 12 pairs of ribs with their cartilage, sternum, collarbones, shoulder blades, arm bones.
// Organs: voice box (thyroid and cricoid cartilage, epiglottis, the two vocal cords), windpipe with its C-shaped rings, the bronchial tree, both lungs
// (three lobes on the right, two on the left, with the notch for the heart), heart with aorta and great veins, diaphragm, liver, the gullet (with its
// three narrow spots), and a J-shaped stomach with folds (rugae) inside and a pool of acid that always lies flat (world gravity).
// Shapes are signed-distance fields meshed with surface nets (smooth, no seams), or swept tubes.
//   import { buildAnatomy } from '/anatomy.js';  const AN = buildAnatomy(THREE, G, { renderer });
//   AN.setAcidColumn(k)   0 = in the stomach .. 1 = at the voice box       AN.setAcidPool(fill)   0..1 of the stomach's height (world-level surface)
//   AN.setValve(open)  AN.setCords(shut)  AN.setFlash(k)  AN.setBurns(k)  AN.setLungSores(k)  AN.dropsAt(t, on)  AN.setVisible(on)
//   AN.parts.{gullet, valve, larynx, stomach, lungs, ...}   AN.points.{larynx, valve, stomach, carina, mid}() -> world positions
const clamp = (x, a, b) => Math.min(Math.max(x, a), b);
const lerp = (a, b, u) => a + (b - a) * u;
const sm = t => t * t * (3 - 2 * t);
const smooth = (a, b, x) => sm(clamp((x - a) / (b - a), 0, 1));
function hash1(n) { const s = Math.sin(n * 127.1) * 43758.5453; return s - Math.floor(s); }

export function buildAnatomy(THREE, G, opts = {}) {
  const V = (x, y, z) => new THREE.Vector3(x, y, z);
  const renderer = opts.renderer; if (renderer) renderer.localClippingEnabled = true;
  // ---------------------------------------------------------------- SDF toolkit
  const elli = (p, c, r) => { const x = (p.x - c[0]) / r[0], y = (p.y - c[1]) / r[1], z = (p.z - c[2]) / r[2], k0 = Math.hypot(x, y, z), k1 = Math.hypot(x / r[0], y / r[1], z / r[2]); return k0 * (k0 - 1) / Math.max(k1, 1e-6); };
  const cap = (p, a, b, ra, rb = ra) => { const bax = b[0] - a[0], bay = b[1] - a[1], baz = b[2] - a[2], pax = p.x - a[0], pay = p.y - a[1], paz = p.z - a[2];
    const t = clamp((pax * bax + pay * bay + paz * baz) / (bax * bax + bay * bay + baz * baz), 0, 1); return Math.hypot(pax - bax * t, pay - bay * t, paz - baz * t) - (ra + (rb - ra) * t); };
  const boxd = (p, c, h) => { const qx = Math.abs(p.x - c[0]) - h[0], qy = Math.abs(p.y - c[1]) - h[1], qz = Math.abs(p.z - c[2]) - h[2];
    return Math.hypot(Math.max(qx, 0), Math.max(qy, 0), Math.max(qz, 0)) + Math.min(Math.max(qx, qy, qz), 0); };
  const smin = (a, b, k) => { const h = Math.max(k - Math.abs(a - b), 0) / k; return Math.min(a, b) - h * h * k * 0.25; };
  const smax = (a, b, k) => -smin(-a, -b, k);
  // surface nets over a box [x0..x1]x[y0..y1]x[z0..z1] at cell size h -> BufferGeometry with field normals
  function mesh(sdf, lo, hi, h) {
    const nx = Math.ceil((hi[0] - lo[0]) / h) + 2, ny = Math.ceil((hi[1] - lo[1]) / h) + 2, nz = Math.ceil((hi[2] - lo[2]) / h) + 2;
    const x0 = lo[0] - h * 0.5, y0 = lo[1] - h * 0.5, z0 = lo[2] - h * 0.5;
    const F = new Float32Array(nx * ny * nz), id = (i, j, k) => i + nx * (j + ny * k), q = V(0, 0, 0);
    for (let k = 0; k < nz; k++) for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) F[id(i, j, k)] = sdf(q.set(x0 + i * h, y0 + j * h, z0 + k * h));
    const VI = new Int32Array(nx * ny * nz).fill(-1), pos = [], E = [[0, 1], [2, 3], [4, 5], [6, 7], [0, 2], [1, 3], [4, 6], [5, 7], [0, 4], [1, 5], [2, 6], [3, 7]];
    const c = new Float32Array(8);
    for (let k = 0; k < nz - 1; k++) for (let j = 0; j < ny - 1; j++) for (let i = 0; i < nx - 1; i++) {
      let neg = 0; for (let m = 0; m < 8; m++) { c[m] = F[id(i + (m & 1), j + ((m >> 1) & 1), k + ((m >> 2) & 1))]; if (c[m] < 0) neg++; } if (neg === 0 || neg === 8) continue;
      let sx = 0, sy = 0, sz = 0, n = 0; for (const [a, b] of E) { if ((c[a] < 0) === (c[b] < 0)) continue; const t = c[a] / (c[a] - c[b]);
        sx += (a & 1) + t * ((b & 1) - (a & 1)); sy += ((a >> 1) & 1) + t * (((b >> 1) & 1) - ((a >> 1) & 1)); sz += ((a >> 2) & 1) + t * (((b >> 2) & 1) - ((a >> 2) & 1)); n++; }
      VI[id(i, j, k)] = pos.length / 3; pos.push(x0 + (i + sx / n) * h, y0 + (j + sy / n) * h, z0 + (k + sz / n) * h); }
    const idx = [], quad = (a, b, cc, d, flip) => { if (a < 0 || b < 0 || cc < 0 || d < 0) return; flip ? idx.push(a, cc, b, a, d, cc) : idx.push(a, b, cc, a, cc, d); };
    for (let k = 1; k < nz - 1; k++) for (let j = 1; j < ny - 1; j++) for (let i = 1; i < nx - 1; i++) { const s0 = F[id(i, j, k)] < 0;
      if (s0 !== (F[id(i + 1, j, k)] < 0)) quad(VI[id(i, j - 1, k - 1)], VI[id(i, j, k - 1)], VI[id(i, j, k)], VI[id(i, j - 1, k)], !s0);
      if (s0 !== (F[id(i, j + 1, k)] < 0)) quad(VI[id(i - 1, j, k - 1)], VI[id(i - 1, j, k)], VI[id(i, j, k)], VI[id(i, j, k - 1)], !s0);
      if (s0 !== (F[id(i, j, k + 1)] < 0)) quad(VI[id(i - 1, j - 1, k)], VI[id(i, j - 1, k)], VI[id(i, j, k)], VI[id(i - 1, j, k)], !s0); }
    const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); geo.setIndex(idx);
    const nrm = new Float32Array(pos.length), e = h * 0.5;
    for (let v = 0; v < pos.length; v += 3) { const x = pos[v], y = pos[v + 1], z = pos[v + 2];
      const gx = sdf(q.set(x + e, y, z)) - sdf(q.set(x - e, y, z)), gy = sdf(q.set(x, y + e, z)) - sdf(q.set(x, y - e, z)), gz = sdf(q.set(x, y, z + e)) - sdf(q.set(x, y, z - e)), l = Math.hypot(gx, gy, gz) || 1;
      nrm[v] = gx / l; nrm[v + 1] = gy / l; nrm[v + 2] = gz / l; }
    { const ia = geo.index.array, A = V(0, 0, 0), B = V(0, 0, 0), C = V(0, 0, 0); let agree = 0;
      for (let t = 0; t < ia.length; t += 3) { A.fromArray(pos, ia[t] * 3); B.fromArray(pos, ia[t + 1] * 3); C.fromArray(pos, ia[t + 2] * 3); const fn = B.sub(A).cross(C.sub(A)); agree += Math.sign(fn.x * nrm[ia[t] * 3] + fn.y * nrm[ia[t] * 3 + 1] + fn.z * nrm[ia[t] * 3 + 2]); }
      if (agree < 0) for (let t = 0; t < ia.length; t += 3) { const tmp = ia[t + 1]; ia[t + 1] = ia[t + 2]; ia[t + 2] = tmp; } }
    geo.setAttribute('normal', new THREE.BufferAttribute(nrm, 3)); geo.computeBoundingSphere(); return geo; }
  // a swept tube along points with a radius (and flattening) per point: cross-section ellipse rx (along the side axis) x ry (along the curve's normal)
  function sweep(pts, rad, opt = {}) { const curve = new THREE.CatmullRomCurve3(pts, false, 'centripetal'), N = opt.n || 80, R = opt.r || 16;
    const P = curve.getSpacedPoints(N), pos = [], nrm = [], idx = [], up0 = opt.up || V(0, 0, 1);
    let prevN = null;
    for (let i = 0; i <= N; i++) { const u = i / N, T = curve.getTangentAt(Math.min(u, 0.9999)).normalize();
      let Nn = prevN ? prevN.clone() : up0.clone(); Nn.addScaledVector(T, -Nn.dot(T)); if (Nn.lengthSq() < 1e-6) Nn = V(1, 0, 0).addScaledVector(T, -T.x); Nn.normalize(); prevN = Nn;
      const Bn = new THREE.Vector3().crossVectors(T, Nn).normalize(), r = typeof rad === 'function' ? rad(u) : rad, fl = opt.flat ? (typeof opt.flat === 'function' ? opt.flat(u) : opt.flat) : 1;
      for (let j = 0; j <= R; j++) { const a = j / R * Math.PI * 2, ca = Math.cos(a), sa = Math.sin(a);
        const d = Bn.clone().multiplyScalar(ca * r).addScaledVector(Nn, sa * r * fl); pos.push(P[i].x + d.x, P[i].y + d.y, P[i].z + d.z);
        const n = Bn.clone().multiplyScalar(ca * fl).addScaledVector(Nn, sa).normalize(); nrm.push(n.x, n.y, n.z); } }
    for (let i = 0; i < N; i++) for (let j = 0; j < R; j++) { const a = i * (R + 1) + j, b = a + R + 1; idx.push(a, b, a + 1, b, b + 1, a + 1); }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('normal', new THREE.Float32BufferAttribute(nrm, 3)); g.setIndex(idx);
    g.userData.curve = curve; g.userData.N = N; g.userData.R = R; return g; }

  // ---------------------------------------------------------------- materials: an x-ray-style medical look (rim-lit, glowing, see-through where it should be)
  const rimPatch = (m, k = 1.6, pw = 2.2, base = 0.35) => { m.onBeforeCompile = sh => { sh.fragmentShader = sh.fragmentShader.replace('#include <emissivemap_fragment>',
      `#include <emissivemap_fragment>\n  { float fr = pow(1.0 - abs(dot(normalize(normal), normalize(vViewPosition))), ${pw.toFixed(2)}); totalEmissiveRadiance *= ${base.toFixed(2)} + ${k.toFixed(2)} * fr; }`); };
    m.customProgramCacheKey = () => 'rim' + k + pw + base; return m; };
  const M = (color, emissive, ei, op, extra = {}) => rimPatch(new THREE.MeshStandardMaterial({ color, emissive, emissiveIntensity: ei, roughness: 0.42, metalness: 0, transparent: op < 1, opacity: op, depthWrite: op >= 0.95, ...extra }), extra.rk ?? 1.6, extra.rp ?? 2.2, extra.rb ?? 0.35);
  const MAT = {
    bone: M(0xe9e4d6, 0xbfd6f0, 0.55, 0.78, { rb: 0.55, rk: 1.2 }), boneDim: M(0xd8d2c4, 0x9fb8d8, 0.4, 0.42, { rb: 0.5 }),
    cart: M(0xb8d8e8, 0x9ad0ff, 0.5, 0.55, { rb: 0.4 }), teeth: M(0xf4f0e6, 0xdfe8f4, 0.5, 0.9),
    lung: M(0xd88a9a, 0xff8aa0, 0.22, 0.32, { rk: 2.4, rp: 2.6, rb: 0.2, side: THREE.DoubleSide }), bronch: M(0xc8e6ff, 0xa8dcff, 0.7, 0.75),
    heart: M(0xa8222c, 0xff3a3a, 0.55, 0.85), aorta: M(0xc8303a, 0xff4a4a, 0.55, 0.85), vein: M(0x4a5aa8, 0x6a8aff, 0.5, 0.8),
    diaph: M(0xc87a6a, 0xff9a7a, 0.25, 0.28, { side: THREE.DoubleSide, rk: 2.2 }), liver: M(0x7a2a24, 0xc0503a, 0.35, 0.55, { rk: 2.0 }),
    gullet: M(0xd87a88, 0xff8a9a, 0.45, 0.62, { rk: 2.0, side: THREE.DoubleSide }), stomach: M(0xd07080, 0xff8a9a, 0.32, 0.42, { rk: 2.2, side: THREE.DoubleSide }),
    rugae: M(0xe8909c, 0xff9aa8, 0.5, 0.75), valve: M(0xb83a4a, 0xff5a6a, 0.9, 0.95), larynx: M(0xc8dcea, 0xbfe6ff, 0.55, 0.72),
    cord: M(0xfff0f0, 0xffe0e0, 0.7, 0.98), epi: M(0xe8a0b0, 0xffb0c0, 0.5, 0.8),
    acid: new THREE.MeshStandardMaterial({ color: 0xb8ff4a, emissive: 0x7ad818, emissiveIntensity: 1.15, roughness: 0.25, transparent: true, opacity: 0.92, side: THREE.DoubleSide }),
    skin: rimPatch(new THREE.MeshStandardMaterial({ color: 0x000000, emissive: 0x58b8ff, emissiveIntensity: 0.9, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, roughness: 1 }), 0.9, 2.6, 0.02),
  };
  MAT.rib = MAT.bone.clone(); MAT.rib.onBeforeCompile = MAT.bone.onBeforeCompile; MAT.rib.customProgramCacheKey = MAT.bone.customProgramCacheKey; MAT.ribc = MAT.cart.clone(); MAT.ribc.onBeforeCompile = MAT.cart.onBeforeCompile; MAT.ribc.customProgramCacheKey = MAT.cart.customProgramCacheKey;
  MAT.ster = MAT.boneDim.clone(); MAT.ster.onBeforeCompile = MAT.boneDim.onBeforeCompile; MAT.ster.customProgramCacheKey = MAT.boneDim.customProgramCacheKey;
  MAT.acidPool = MAT.acid.clone(); MAT.acidPool.opacity = 0.62; MAT.acidPool.emissiveIntensity = 0.8; MAT.acidPool.depthWrite = false; MAT.acidPool.clippingPlanes = [new THREE.Plane(V(0, -1, 0), 0)];
  // ---------------------------------------------------------------- attach groups (children are given in rest world coords)
  const saveP = G.root.position.clone(), saveQ = G.root.quaternion.clone(); G.reset(); G.root.position.set(0, 0, 0); G.root.quaternion.identity(); G.root.updateMatrixWorld(true);
  const parentInv = G.root.parent ? G.root.parent.matrixWorld.clone().invert() : new THREE.Matrix4();
  const groupOn = name => { const b = G.bones[name], g = new THREE.Group(); b.add(g); const m = b.matrixWorld.clone().invert().multiply(G.root.parent ? G.root.parent.matrixWorld : new THREE.Matrix4()); g.applyMatrix4(m); g.updateMatrixWorld(true); return g; };
  const GR = { head: groupOn('head'), neck: groupOn('neck'), chest: groupOn('chest'), sp2: groupOn('spine2'), sp1: groupOn('spine1') };
  for (const S of ['R', 'L']) { GR['uarm' + S] = groupOn('uarm' + S); GR['farm' + S] = groupOn('farm' + S); }
  const ALL = [];
  const add = (grp, geo, mat, ro = 6) => { const m = new THREE.Mesh(geo, mat); m.renderOrder = ro; m.frustumCulled = false; grp.add(m); ALL.push(m); return m; };
  const R0 = n => G.bones[n].getWorldPosition(new THREE.Vector3()).applyMatrix4(parentInv);
  const HC = V(...G.man.headC);

  // ================================================================ BONES
  // ---- skull: cranium, brow, cheekbones, eye sockets and nose opening (carved), upper jaw, lower jaw, teeth
  { const cx = HC.x, cy = HC.y, cz = HC.z;
    const sk = p => { let d = elli(p, [cx, cy + 0.035, cz + 0.012], [0.071, 0.083, 0.094]);
      d = smin(d, elli(p, [cx, cy + 0.005, cz - 0.055], [0.06, 0.035, 0.045]), 0.02);                       // forehead/brow
      d = smin(d, elli(p, [cx, cy - 0.04, cz - 0.07], [0.042, 0.035, 0.035]), 0.02);                        // upper jaw (maxilla)
      for (const s of [-1, 1]) { d = smin(d, cap(p, [cx + s * 0.05, cy - 0.022, cz - 0.068], [cx + s * 0.067, cy - 0.025, cz - 0.01], 0.009, 0.007), 0.012);   // cheekbone + arch
        d = smin(d, elli(p, [cx + s * 0.06, cy - 0.055, cz + 0.035], [0.013, 0.02, 0.014]), 0.01); }        // mastoid
      for (const s of [-1, 1]) d = smax(d, -elli(p, [cx + s * 0.031, cy + 0.0, cz - 0.09], [0.019, 0.017, 0.03]), 0.006);   // eye sockets
      d = smax(d, -elli(p, [cx, cy - 0.032, cz - 0.1], [0.011, 0.016, 0.02]), 0.004);                      // nose opening
      d = smax(d, -elli(p, [cx, cy + 0.035, cz + 0.012], [0.064, 0.076, 0.087]), 0.004);                   // hollow inside (a shell, so it reads like bone)
      return d; };
    add(GR.head, mesh(sk, [cx - 0.095, cy - 0.085, cz - 0.125], [cx + 0.095, cy + 0.125, cz + 0.115], 0.0032), MAT.bone, 7);
    const jaw = p => { let d = 1; const A = [cx, cy - 0.09, cz - 0.078];
      for (const s of [-1, 1]) { d = Math.min(d, cap(p, [cx + s * 0.028, cy - 0.093, cz - 0.07], [cx + s * 0.05, cy - 0.085, cz - 0.02], 0.008, 0.008));
        d = smin(d, cap(p, [cx + s * 0.05, cy - 0.085, cz - 0.02], [cx + s * 0.055, cy - 0.04, cz + 0.005], 0.008, 0.006), 0.008); }
      d = smin(d, elli(p, A, [0.03, 0.012, 0.012]), 0.01); return d; };
    add(GR.head, mesh(jaw, [cx - 0.07, cy - 0.11, cz - 0.1], [cx + 0.07, cy - 0.025, cz + 0.02], 0.0028), MAT.bone, 7);
    const teeth = new THREE.InstancedMesh(new THREE.CapsuleGeometry(0.0032, 0.007, 4, 8), MAT.teeth, 28); const m4 = new THREE.Matrix4(); let n = 0;
    for (const row of [0, 1]) for (let i = 0; i < 14; i++) { const a = (i / 13 - 0.5) * 2.3, r = 0.027; const x = cx + Math.sin(a) * r, z = cz - 0.052 - Math.cos(a) * r * 0.95, y = cy - (row ? 0.077 : 0.062);
      m4.makeTranslation(x, y, z); teeth.setMatrixAt(n++, m4); }
    teeth.renderOrder = 7; teeth.frustumCulled = false; GR.head.add(teeth); ALL.push(teeth); }

  // ---- the spine: C1-C7, T1-T12, L1-L5 (body, pedicles, arch, spinous and transverse processes), with discs
  const VERTS = [];
  { const lev = []; const C1 = HC.y - 0.06, C7 = 1.445, T12 = 1.18, L5 = 0.99;
    for (let i = 0; i < 7; i++) lev.push({ k: 'C', i, y: lerp(C1, C7, i / 6), z: lerp(0.008, 0.036, sm(i / 6)), s: lerp(0.72, 0.92, i / 6) });
    for (let i = 0; i < 12; i++) { const u = i / 11; lev.push({ k: 'T', i, y: lerp(1.424, T12, u), z: 0.04 + 0.022 * Math.sin(Math.PI * u), s: lerp(0.95, 1.22, u) }); }
    for (let i = 0; i < 5; i++) { const u = i / 4; lev.push({ k: 'L', i, y: lerp(1.148, L5, u), z: lerp(0.045, 0.03, u) - 0.012 * Math.sin(Math.PI * u), s: lerp(1.3, 1.45, u) }); }
    const bodyGeo = new THREE.LatheGeometry([[0, -0.5], [0.92, -0.5], [1, -0.4], [0.86, 0], [1, 0.4], [0.92, 0.5], [0, 0.5]].map(([x, y]) => new THREE.Vector2(x, y)), 24);
    for (const L of lev) { const g = new THREE.Group(), s = L.s, grp = L.k === 'C' ? GR.neck : L.k === 'T' ? (L.i < 9 ? GR.chest : GR.sp2) : GR.sp1;
      const h = L.k === 'C' ? 0.011 : L.k === 'T' ? 0.0155 : 0.022, r = 0.0125 * s;
      if (!(L.k === 'C' && L.i === 0)) { const b = new THREE.Mesh(bodyGeo, MAT.bone); b.scale.set(r, h, r * 0.82); b.position.set(0, 0, -0.012 * s); g.add(b); }
      const arch = new THREE.Mesh(new THREE.TorusGeometry(0.0095 * s, 0.0026 * s, 8, 20, Math.PI * 1.25).rotateX(Math.PI / 2).rotateY(-Math.PI * 0.125 + Math.PI), MAT.bone); arch.position.set(0, 0, 0.006 * s); g.add(arch);
      const spLen = (L.k === 'C' ? 0.016 : L.k === 'T' ? 0.03 : 0.024) * s, spDown = L.k === 'T' ? 0.6 : 0.15;
      const sp = new THREE.Mesh(new THREE.CapsuleGeometry(0.0028 * s, spLen, 4, 8), MAT.bone); sp.rotation.x = Math.PI / 2 - spDown; sp.position.set(0, -spLen * 0.5 * Math.sin(spDown), 0.016 * s + spLen * 0.5 * Math.cos(spDown)); g.add(sp);
      for (const sd of [-1, 1]) { const tl = (L.k === 'L' ? 0.022 : L.k === 'T' ? 0.016 : 0.011) * s, tp = new THREE.Mesh(new THREE.CapsuleGeometry(0.0026 * s, tl, 4, 8), MAT.bone);
        tp.rotation.z = Math.PI / 2; tp.rotation.y = sd * (L.k === 'T' ? 0.45 : 0.1); tp.position.set(sd * (0.011 * s + tl * 0.5), 0, 0.012 * s); g.add(tp); }
      if (L.k === 'C' && L.i === 1) { const dens = new THREE.Mesh(new THREE.CapsuleGeometry(0.004, 0.008, 4, 8), MAT.bone); dens.position.set(0, 0.012, -0.012); g.add(dens); }
      g.position.set(0, L.y, L.z); g.traverse(o => { if (o.isMesh) { o.renderOrder = 7; o.frustumCulled = false; ALL.push(o); } }); grp.add(g); VERTS.push({ ...L, g });
      if (L !== lev[lev.length - 1] && !(L.k === 'C' && L.i === 0)) { const disc = new THREE.Mesh(new THREE.CylinderGeometry(r * 0.95, r * 0.95, h * 0.45, 20), MAT.cart); disc.scale.z = 0.82; disc.position.set(0, L.y - h * 0.75 - 0.002, L.z - 0.012 * s); disc.renderOrder = 6; grp.add(disc); ALL.push(disc); } } }

  // ---- ribs 1-12 (flat bands that curve round from the spine to the front), costal cartilage to the sternum, the sternum, collarbones, shoulder blades
  const ribY = i => VERTS.find(v => v.k === 'T' && v.i === i).y, ribZ = i => VERTS.find(v => v.k === 'T' && v.i === i).z;
  const RIB = []; // half-width a, half-depth b, centre z, how far round the bone goes (0 = back, 1 = front), drop from back to front end
  const A_ = [0.055, 0.085, 0.105, 0.118, 0.128, 0.136, 0.142, 0.145, 0.144, 0.14, 0.128, 0.11], B_ = [0.055, 0.072, 0.084, 0.092, 0.098, 0.102, 0.105, 0.106, 0.104, 0.1, 0.092, 0.08];
  const END = [0.8, 0.78, 0.77, 0.76, 0.75, 0.74, 0.73, 0.72, 0.7, 0.68, 0.55, 0.42], DROP = [0.045, 0.06, 0.075, 0.085, 0.095, 0.1, 0.105, 0.105, 0.1, 0.095, 0.06, 0.04];
  const STY = i => [1.405, 1.38, 1.355, 1.33, 1.305, 1.28, 1.255][i];                        // where cartilage of ribs 1-7 meets the sternum
  const ribPt = (i, s, th) => { const a = A_[i], b = B_[i], zc = 0.002, yb = ribY(i) - 0.004;
    const x = s * a * Math.sin(th * Math.PI), z = zc + b * Math.cos(th * Math.PI), y = yb - DROP[i] * sm(th) - 0.012 * Math.sin(th * Math.PI); return V(x, y, z); };
  for (let i = 0; i < 12; i++) for (const s of [-1, 1]) {
    const pts = [V(s * 0.012, ribY(i) + 0.002, ribZ(i) + 0.002), V(s * 0.03, ribY(i), ribZ(i) + 0.022)]; for (let k = 1; k <= 14; k++) pts.push(ribPt(i, s, lerp(0.12, END[i], k / 14)));
    const grp = i < 9 ? GR.chest : GR.sp2;
    add(grp, sweep(pts, u => lerp(0.0055, 0.0075, sm(Math.min(1, u * 3))) * (i === 0 ? 1.2 : 1), { n: 48, r: 10, flat: 0.42, up: V(0, 1, 0) }), MAT.rib, 7);
    if (i < 10) { const e = ribPt(i, s, END[i]), tgt = i < 7 ? V(s * 0.016, STY(i), -0.1) : ribPt(Math.min(6, i - 1), s, END[Math.min(6, i - 1)] + 0.04);
      const mid = e.clone().lerp(tgt, 0.5).add(V(0, i < 7 ? -0.004 : 0.01, -0.006));
      add(grp, sweep([e, mid, tgt], 0.0055, { n: 16, r: 8, flat: 0.5, up: V(0, 1, 0) }), MAT.ribc, 6); } }
  add(GR.chest, mesh(p => { let d = boxd(p, [0, 1.395, -0.101], [0.025, 0.026, 0.005]) - 0.003;     // manubrium
    d = smin(d, boxd(p, [0, 1.3, -0.106], [0.015, 0.068, 0.0045]) - 0.003, 0.01);                  // body
    d = smin(d, cap(p, [0, 1.232, -0.104], [0, 1.212, -0.098], 0.006, 0.003), 0.006);               // xiphoid
    return smax(d, -elli(p, [0, 1.425, -0.1], [0.012, 0.008, 0.02]), 0.003); }, [-0.04, 1.2, -0.12], [0.04, 1.43, -0.085], 0.0022), MAT.ster, 7);
  for (const s of [-1, 1]) { add(GR.chest, sweep([V(s * 0.022, 1.418, -0.098), V(s * 0.06, 1.428, -0.088), V(s * 0.11, 1.432, -0.06), V(s * 0.145, 1.44, -0.02), V(s * 0.165, 1.437, 0.005)], u => 0.0065 + 0.002 * Math.abs(u - 0.5) * 2, { n: 40, r: 10, flat: 0.75, up: V(0, 1, 0) }), MAT.bone, 7);
    add(GR.chest, mesh(p => { const a = [s * 0.065, 1.425, 0.098], b = [s * 0.088, 1.27, 0.108], c = [s * 0.155, 1.4, 0.05];   // shoulder blade: a thin triangle plate with its spine ridge and socket
        const pl = Math.min(cap(p, a, b, 0.004), cap(p, b, c, 0.004), cap(p, c, a, 0.006)); let d = pl;
        const ab = V(...b).sub(V(...a)), ac = V(...c).sub(V(...a)), nn = new THREE.Vector3().crossVectors(ab, ac).normalize(), pp = p.clone().sub(V(...a));
        const dn = Math.abs(pp.dot(nn)) - 0.0022, inP = (() => { const w = pp.clone().addScaledVector(nn, -pp.dot(nn)); const d00 = ab.dot(ab), d01 = ab.dot(ac), d11 = ac.dot(ac), d20 = w.dot(ab), d21 = w.dot(ac), den = d00 * d11 - d01 * d01;
          const v = (d11 * d20 - d01 * d21) / den, ww = (d00 * d21 - d01 * d20) / den; return Math.max(-v, -ww, v + ww - 1) * 0.12; })();
        d = Math.min(d, Math.max(dn, inP)); d = smin(d, cap(p, [s * 0.07, 1.39, 0.104], [s * 0.152, 1.425, 0.06], 0.004, 0.006), 0.006);
        return smin(d, elli(p, [s * 0.158, 1.398, 0.045], [0.008, 0.014, 0.012]), 0.006); }, [Math.min(s * 0.05, s * 0.17), 1.25, 0.03], [Math.max(s * 0.05, s * 0.17), 1.45, 0.12], 0.0028), MAT.boneDim, 6); }
  // arm bones (humerus; radius and ulna), carried by his arm bones so they follow every pose
  for (const S of ['R', 'L']) { const sg = S === 'R' ? 1 : -1, sh = R0('uarm' + S), el = R0('farm' + S), wr = R0('hand' + S);
    const hh = sh.clone().add(V(-sg * 0.012, -0.004, 0.006)); add(GR['uarm' + S], new THREE.SphereGeometry(0.021, 20, 14).translate(hh.x, hh.y, hh.z), MAT.bone, 7);
    add(GR['uarm' + S], sweep([hh, hh.clone().lerp(el, 0.5), el.clone().add(V(0, 0.012, 0))], u => 0.009 + 0.004 * (Math.abs(u - 0.5) * 2) ** 3, { n: 30, r: 12 }), MAT.bone, 7);
    add(GR['uarm' + S], new THREE.CapsuleGeometry(0.008, 0.04, 6, 12).rotateZ(Math.PI / 2).translate(el.x, el.y + 0.005, el.z), MAT.bone, 7);
    const side = V(0, 0, 1);
    for (const [k, r0, r1] of [[-1, 0.0055, 0.008], [1, 0.0065, 0.0045]]) { const a = el.clone().addScaledVector(side, k * 0.01), b = wr.clone().addScaledVector(side, k * 0.011);
      add(GR['farm' + S], sweep([a, a.clone().lerp(b, 0.5), b], u => lerp(r0, r1, u), { n: 24, r: 10 }), MAT.bone, 7); } }

  // ================================================================ AIRWAY, LUNGS, HEART
  // ---- voice box: hyoid, thyroid cartilage (the Adam's apple shield), cricoid ring, epiglottis, the vocal cords
  const LAR = V(0, 1.508, -0.048);
  const larynx = new THREE.Group(); GR.neck.add(larynx); larynx.position.copy(LAR);
  { add(larynx, sweep([-1, -0.5, 0, 0.5, 1].map(u => V(u * 0.024, 0.03 + 0.004 * u * u, -0.006 + 0.022 * u * u)), 0.0028, { n: 24, r: 8 }), MAT.larynx, 8);    // hyoid
    add(larynx, mesh(p => { const q = p.clone(); let d = 1; for (const s of [-1, 1]) { const ang = s * 0.62, nx = Math.cos(ang), nz = Math.sin(ang);   // two plates meeting at the front
        const lx = q.x * nx + (q.z + 0.006) * nz * s, lz = -q.x * nz * s + (q.z + 0.006) * nx; d = Math.min(d, boxd(V(lx, q.y, lz), [s * 0.014, 0.002, 0.0], [0.014, 0.013, 0.0016])); }
      return smax(d, -elli(q, [0, 0.016, -0.02], [0.006, 0.006, 0.01]), 0.002); }, [-0.035, -0.014, -0.03], [0.035, 0.02, 0.025], 0.0012), MAT.larynx, 8);
    add(larynx, new THREE.TorusGeometry(0.0115, 0.0035, 10, 28).rotateX(Math.PI / 2).translate(0, -0.018, 0.004), MAT.larynx, 8);              // cricoid
    add(larynx, mesh(p => smax(elli(p, [0, 0.03, 0.012], [0.011, 0.014, 0.003]), -elli(p, [0, 0.04, 0.0], [0.03, 0.01, 0.03]), 0.002), [-0.015, 0.012, 0.004], [0.015, 0.048, 0.02], 0.0010), MAT.epi, 8); }
  const CORDS = [-1, 1].map(s => { const c = add(larynx, mesh(p => elli(p, [0, 0, 0], [0.0035, 0.0022, 0.0125]), [-0.005, -0.004, -0.015], [0.005, 0.004, 0.015], 0.0007), MAT.cord, 9); c.position.set(s * 0.006, 0.0, 0.002); c.rotation.y = -s * 0.25; return c; });
  const larFlash = new THREE.Mesh(new THREE.SphereGeometry(0.03, 16, 12), new THREE.MeshBasicMaterial({ color: 0xff2a2a, transparent: true, opacity: 0, depthWrite: false, depthTest: false, blending: THREE.AdditiveBlending, toneMapped: false }));
  larFlash.renderOrder = 10; larynx.add(larFlash); ALL.push(larFlash);
  // ---- windpipe with C rings (open at the back), the carina, both main bronchi and a branching tree inside the lungs
  const TR0 = LAR.clone().add(V(0, -0.024, 0.006)), CAR = V(0, 1.33, 0.012);
  const WIND = new THREE.CatmullRomCurve3([TR0, V(0, 1.44, -0.03), V(0, 1.38, -0.012), CAR]);
  add(GR.chest, sweep(WIND.getPoints(12), 0.0085, { n: 50, r: 14 }), MAT.bronch.clone(), 7).material.opacity = 0.35;
  for (let k = 0; k < 15; k++) { const u = (k + 0.5) / 15, p = WIND.getPointAt(u), t = WIND.getTangentAt(u);
    const ring = add(GR.chest, new THREE.TorusGeometry(0.0095, 0.0016, 6, 20, Math.PI * 1.55), MAT.cart, 8); ring.position.copy(p); ring.quaternion.setFromUnitVectors(V(0, 0, 1), t); ring.rotateZ(Math.PI * 0.725 + Math.PI); }
  const BRANCH = [];
  const tree = (a, dir, len, r, depth, seed) => { const b = a.clone().addScaledVector(dir, len); BRANCH.push([a, b, r]); if (depth <= 0) return;
    const ax = new THREE.Vector3().crossVectors(dir, V(0.3, 0.2, 1).normalize()).normalize();
    for (const sg of [-1, 1]) { const q = new THREE.Quaternion().setFromAxisAngle(ax.clone().applyAxisAngle(dir, hash1(seed + sg) * 6.28), sg * (0.45 + 0.25 * hash1(seed * 3 + sg)));
      tree(b, dir.clone().applyQuaternion(q).normalize(), len * (0.72 + 0.1 * hash1(seed * 7 + sg)), r * 0.7, depth - 1, seed * 2 + sg + 3); } };
  for (const s of [-1, 1]) { const d = V(s * 0.9, -0.5 + (s > 0 ? 0.08 : -0.05), 0.05).normalize(); tree(CAR, d, s > 0 ? 0.028 : 0.04, 0.0065, 5, s > 0 ? 11 : 23); }
  for (const [a, b, r] of BRANCH) { const gm = add(GR.chest, sweep([a, a.clone().lerp(b, 0.5), b], u => lerp(r, r * 0.8, u), { n: 6, r: 8 }), MAT.bronch, 7); }
  // ---- lungs: each one fills its side of the ribcage, rounded apex above the collarbone, a concave base on the diaphragm; the left one makes room for the heart
  const ribInside = (p, pad) => { const yy = clamp(p.y, 1.16, 1.43), u = (1.43 - yy) / 0.27, a = lerp(0.05, 0.145, Math.sqrt(sm(clamp(u * 1.6, 0, 1)))) - pad, b = lerp(0.05, 0.1, Math.sqrt(sm(clamp(u * 1.6, 0, 1)))) - pad;
    return Math.hypot(p.x / a, (p.z - 0.002) / b) - 1; };
  const DOME = s => [s * 0.07, s > 0 ? 1.085 : 1.07, 0.0];
  const lungSdf = s => p => { let d = ribInside(p, 0.012) * 0.06; d = Math.max(d, 1.452 - p.y > 0 ? -1 : (p.y - 1.452));
    d = Math.max(d, -(s * p.x - 0.022 - 0.02 * Math.max(0, 1.38 - p.y)));                    // the middle (between the lungs)
    d = smax(d, -elli(p, DOME(s), [0.13, 0.14, 0.14]), 0.01);                                  // the dome of the diaphragm under it
    if (s < 0) d = smax(d, -elli(p, [-0.03, 1.26, -0.05], [0.07, 0.065, 0.065]), 0.012);       // the heart's notch (left)
    d = smax(d, -cap(p, [s * 0.03, 1.33, 0.01], [s * 0.05, 1.32, 0.0], 0.012), 0.006);        // the root (where the bronchus goes in)
    // the fissures between the lobes: thin grooves
    const fz = p.z - 0.002, obl = (p.y - 1.37) + 0.62 * (-fz) + 0.0; d = smax(d, -(Math.abs(obl) - 0.0035), 0.002);
    if (s > 0) { const hor = p.y - 1.305; if (fz < 0.02) d = smax(d, -(Math.abs(hor) - 0.003), 0.002); }
    return d; };
  const lungs = new THREE.Group(); GR.chest.add(lungs);
  const LUNGS = [-1, 1].map(s => add(lungs, mesh(lungSdf(s), [s < 0 ? -0.16 : 0.0, 1.15, -0.12], [s < 0 ? 0 : 0.16, 1.46, 0.12], 0.0034), MAT.lung, 4));
  // ---- heart (ventricles, atria) with the aorta (arch and descending), pulmonary trunk, superior vena cava
  const heartC = V(-0.018, 1.27, -0.048);
  const heart = new THREE.Group(); GR.chest.add(heart);
  add(heart, mesh(p => { let d = elli(p, [-0.03, 1.255, -0.06], [0.044, 0.052, 0.04]);
    d = smin(d, cap(p, [-0.012, 1.285, -0.05], [-0.06, 1.215, -0.07], 0.03, 0.01), 0.02);                       // ventricles toward the apex (left, down, front)
    d = smin(d, elli(p, [0.018, 1.29, -0.035], [0.026, 0.028, 0.026]), 0.012);                                  // right atrium
    d = smin(d, elli(p, [-0.03, 1.3, -0.02], [0.022, 0.018, 0.02]), 0.01);                                      // left atrium (behind)
    return d; }, [-0.1, 1.15, -0.12], [0.06, 1.34, 0.0], 0.0026), MAT.heart, 6);
  add(heart, sweep([V(-0.005, 1.3, -0.045), V(0.0, 1.355, -0.04), V(-0.012, 1.385, -0.015), V(-0.025, 1.375, 0.018), V(-0.024, 1.34, 0.035), V(-0.022, 1.25, 0.04), V(-0.018, 1.18, 0.035)], 0.0115, { n: 70, r: 14 }), MAT.aorta, 6);
  for (const [x, z] of [[0.004, -0.032], [-0.006, -0.024], [-0.016, -0.012]]) add(heart, sweep([V(x, 1.375, z), V(x * 1.4, 1.41, z - 0.004)], 0.0045, { n: 6, r: 8 }), MAT.aorta, 6);   // the three branches off the arch
  add(heart, sweep([V(-0.022, 1.3, -0.075), V(-0.022, 1.33, -0.06), V(-0.005, 1.345, -0.03), V(0.03, 1.335, 0.0)], 0.009, { n: 30, r: 12 }), MAT.vein, 6);                // pulmonary trunk
  add(heart, sweep([V(0.024, 1.31, -0.03), V(0.026, 1.36, -0.03), V(0.022, 1.41, -0.025)], 0.008, { n: 20, r: 12 }), MAT.vein, 6);                                      // superior vena cava
  // ---- diaphragm: a thin double dome under the lungs and heart (higher on the right), with the hole the gullet goes through
  const HIATUS = V(-0.022, 1.205, -0.022);
  add(GR.sp2, mesh(p => { let d = 1; for (const s of [-1, 1]) d = smin(d, elli(p, DOME(s), [0.13, 0.14, 0.14]), 0.03); d = Math.abs(d) - 0.0018;
    d = Math.max(d, ribInside(p, 0.002) * 0.06); d = Math.max(d, 1.14 - p.y); return smax(d, -cap(p, HIATUS.toArray(), [HIATUS.x, HIATUS.y - 0.02, HIATUS.z], 0.013), 0.003); }, [-0.16, 1.13, -0.12], [0.16, 1.24, 0.12], 0.0034), MAT.diaph, 5);
  // ---- liver (his right, under the diaphragm)
  add(GR.sp2, mesh(p => { let d = elli(p, [0.05, 1.155, -0.02], [0.105, 0.05, 0.085]); d = smin(d, elli(p, [-0.04, 1.17, -0.05], [0.06, 0.025, 0.05]), 0.03);
    d = smax(d, -elli(p, [0.0, 1.085, -0.03], [0.16, 0.05, 0.12]), 0.02); return smax(d, elli(p, DOME(1), [0.128, 0.138, 0.138]), 0.01); }, [-0.11, 1.09, -0.12], [0.16, 1.22, 0.08], 0.0036), MAT.liver, 5);

  // ================================================================ THE GULLET, THE VALVE AND THE STOMACH
  const CARDIA = V(-0.036, 1.172, -0.044);
  const GPTS = [LAR.clone().add(V(0, -0.025, 0.026)), V(0.0, 1.45, 0.012), V(-0.004, 1.39, 0.018), V(-0.008, 1.33, 0.022), V(-0.012, 1.27, 0.012), V(-0.018, 1.23, -0.006), HIATUS, V(-0.03, 1.188, -0.036), CARDIA];
  const gulGeo = sweep(GPTS, u => 0.0105 * (1 - 0.28 * Math.exp(-(((u - 0.02) / 0.04) ** 2)) - 0.2 * Math.exp(-(((u - 0.35) / 0.05) ** 2)) - 0.25 * Math.exp(-(((u - 0.86) / 0.04) ** 2))), { n: 140, r: 20, flat: u => lerp(0.72, 1, sm(clamp(u * 2, 0, 1))) });
  const gullet = add(GR.chest, gulGeo, MAT.gullet, 6);
  const GUL = gulGeo.userData.curve;
  // burns along the lower gullet (years of acid)
  const burnM = new THREE.MeshBasicMaterial({ color: 0xff2a10, transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false });
  const BURNS = []; for (let i = 0; i < 14; i++) { const u = 0.5 + 0.45 * hash1(i * 3.7), p = GUL.getPointAt(u), b = add(GR.chest, new THREE.SphereGeometry(0.009 + 0.004 * hash1(i), 12, 8), burnM, 9); b.scale.set(1.25, 1.9, 1.25); b.position.copy(p); b.visible = false; BURNS.push(b); }
  // the acid column inside the gullet (bottom up)
  const GULUP = new THREE.CatmullRomCurve3(GUL.getSpacedPoints(80).reverse(), false, 'centripetal');
  const ACT = 120, ARAD = 12, acidCol = add(GR.chest, new THREE.TubeGeometry(GULUP, ACT, 0.0068, ARAD), MAT.acid, 8), acidTip = add(GR.chest, new THREE.SphereGeometry(0.0072, 14, 10), MAT.acid, 8);
  // the valve (lower esophageal sphincter): a thick muscle ring at the junction
  const valve = new THREE.Group(); GR.sp2.add(valve); valve.position.copy(GUL.getPointAt(0.93)); valve.quaternion.setFromUnitVectors(V(0, 1, 0), GUL.getTangentAt(0.93).negate().normalize());
  const valveRing = add(valve, new THREE.TorusGeometry(0.0095, 0.0045, 14, 32).rotateX(Math.PI / 2), MAT.valve, 9);
  // the stomach: fundus up under the left dome, the body sweeping down and across, the antrum, the pylorus, the start of the duodenum
  const SPINE = [CARDIA, V(-0.06, 1.2, -0.04), V(-0.085, 1.165, -0.055), V(-0.088, 1.11, -0.07), V(-0.065, 1.065, -0.08), V(-0.025, 1.055, -0.085), V(0.012, 1.07, -0.08), V(0.03, 1.085, -0.068), V(0.045, 1.09, -0.05)];
  const SR = [0.012, 0.038, 0.047, 0.05, 0.046, 0.036, 0.024, 0.012, 0.012];
  const stomSdf = (inset = 0) => p => { let d = 1; for (let i = 0; i < SPINE.length - 1; i++) d = smin(d, cap(p, SPINE[i].toArray(), SPINE[i + 1].toArray(), SR[i] - inset, SR[i + 1] - inset), 0.025); return d; };
  const stomOuter = stomSdf(0), stomInner = stomSdf(0.004);
  const SB = [[-0.15, 0.99, -0.15], [0.07, 1.26, 0.0]];
  const stomach = new THREE.Group(); GR.sp2.add(stomach);
  add(stomach, mesh(p => Math.abs(stomOuter(p) + 0.002) - 0.002, SB[0], SB[1], 0.003), MAT.stomach, 6);
  // the folds (rugae) on the inside wall: long ridges along the stomach, drawn as a ridged inner surface
  add(stomach, mesh(p => { const d = stomInner(p); const r = 0.0016 * Math.sin((p.x * 0.8 + p.z * 1.6) * 520 + Math.sin(p.y * 190) * 2.0); return Math.abs(d + 0.003 - r) - 0.0012; }, SB[0], SB[1], 0.0024), MAT.rugae, 6);
  // the acid pool: the inside of the stomach, cut flat at the acid's level (a world-horizontal plane, so it always lies level whichever way he lies)
  const pool = add(stomach, mesh(p => stomInner(p) + 0.0015, SB[0], SB[1], 0.003), MAT.acidPool, 7);
  pool.geometry.computeBoundingBox();
  // drops into the lungs (beat: acid slips into the airway) and irritated spots in the lungs
  const dropM = new THREE.MeshBasicMaterial({ color: 0xc8ff5a, transparent: true, opacity: 0.95, depthWrite: false, toneMapped: false });
  const DROPS = []; for (let i = 0; i < 16; i++) { const d = add(GR.chest, new THREE.SphereGeometry(0.0045, 10, 8), dropM, 10); d.visible = false; DROPS.push(d); }
  const sorM = new THREE.MeshBasicMaterial({ color: 0xff3a2a, transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false });
  const SORES = []; for (let i = 0; i < 14; i++) { const [a, b] = BRANCH[BRANCH.length - 1 - i * 3]; const s = add(GR.chest, new THREE.SphereGeometry(0.011, 12, 8), sorM, 9); s.position.copy(b); s.visible = false; SORES.push(s); }

  // ================================================================ THE SEE-THROUGH SKIN: a faint glow outline of his body (shirt shape for the torso), head, arms, hands
  const skin = new THREE.Group(); GR.chest.add(skin);
  const SKINS = [skin];
  for (const nm of ['shirt', 'skin_head', 'skin_armR', 'skin_handR', 'skin_armL', 'skin_handL']) { const o = G.meshes[nm]; if (!o) continue; const x = new THREE.SkinnedMesh(o.geometry, MAT.skin); x.bind(o.skeleton, o.bindMatrix);
    x.position.copy(o.position); x.quaternion.copy(o.quaternion); x.scale.copy(o.scale); x.frustumCulled = false; x.renderOrder = 11; x.userData.xray = true; o.parent.add(x); SKINS.push(x); ALL.push(x); }

  G.root.position.copy(saveP); G.root.quaternion.copy(saveQ); G.root.updateMatrixWorld(true);

  // ================================================================ controls
  const wpos = o => o.getWorldPosition(new THREE.Vector3());
  let XON = false;
  const API = {
    parts: { gullet, valve, larynx, stomach, lungs, heart, skin, pool, acidCol },
    all: ALL, curve: GUL, wind: WIND, carina: CAR,
    setVisible(on) { XON = on; for (const m of ALL) m.visible = on && !m.userData.hidden; for (const b of BURNS) b.visible = on && burnM.opacity > 0.01; for (const d of DROPS) d.visible = false; for (const x of SORES) x.visible = on && sorM.opacity > 0.01; },
    setRibs(k) { MAT.rib.opacity = 0.78 * k; MAT.ribc.opacity = 0.55 * k; MAT.ster.opacity = 0.42 * k; for (const m of [MAT.rib, MAT.ribc, MAT.ster]) m.depthWrite = false; },
    setSkin(k) { MAT.skin.emissiveIntensity = 0.9 * k; },
    setAcidColumn(k) { const n = Math.round(clamp(k, 0, 1) * ACT); acidCol.geometry.setDrawRange(0, n * ARAD * 6); acidCol.userData.hidden = acidTip.userData.hidden = n === 0;
      acidCol.visible = acidTip.visible = XON && n > 0; acidTip.position.copy(GULUP.getPointAt(clamp(k, 0, 1))); },
    setAcidPool(fill) { pool.updateMatrixWorld(true); const bb = pool.geometry.boundingBox, P = [];
      for (const x of [bb.min.x, bb.max.x]) for (const y of [bb.min.y, bb.max.y]) for (const z of [bb.min.z, bb.max.z]) P.push(V(x, y, z).applyMatrix4(pool.matrixWorld).y);
      const lo = Math.min(...P), hi = Math.max(...P); MAT.acidPool.clippingPlanes[0].constant = lerp(lo, hi, clamp(fill, 0, 1)); },
    setValve(open) { valveRing.scale.set(lerp(0.72, 1.4, open), lerp(1.25, 0.8, open), lerp(0.72, 1.4, open)); MAT.valve.emissive.setRGB(1, lerp(0.3, 0.7, open), lerp(0.35, 0.2, open)); },
    setCords(shut) { CORDS.forEach((c, i) => { const s = i ? 1 : -1; c.position.x = s * lerp(0.006, 0.0022, shut); c.rotation.y = -s * lerp(0.25, 0.02, shut); }); },
    setFlash(k) { larFlash.material.opacity = 0.7 * k; },
    setBurns(k) { burnM.opacity = 0.75 * k; MAT.gullet.emissive.setRGB(1, lerp(0.54, 0.22, k), lerp(0.6, 0.22, k)); for (const b of BURNS) b.visible = XON && k > 0.01; },
    setLungSores(k) { sorM.opacity = 0.65 * k; for (const x of SORES) x.visible = XON && k > 0.01; MAT.lung.emissive.setRGB(1, lerp(0.54, 0.25, k), lerp(0.63, 0.3, k)); MAT.lung.opacity = lerp(0.32, 0.5, k); },
    dropsAt(t, on) { DROPS.forEach((dr, i) => { dr.visible = on && XON; if (!on) return; const s = (t * 0.45 + i / DROPS.length) % 1, br = BRANCH[(i * 7) % BRANCH.length];
      dr.position.copy(s < 0.55 ? WIND.getPointAt(s / 0.55) : CAR.clone().lerp(br[1], (s - 0.55) / 0.45)); }); },
    points: { larynx: () => wpos(larynx), valve: () => wpos(valve), stomach: () => SPINE[3].clone().applyMatrix4(GR.sp2.matrixWorld), carina: () => CAR.clone().applyMatrix4(GR.chest.matrixWorld),
      mid: () => GUL.getPointAt(0.55).applyMatrix4(GR.chest.matrixWorld) },
  };
  API.setAcidColumn(0); API.setValve(0); API.setCords(0);
  return API;
}
