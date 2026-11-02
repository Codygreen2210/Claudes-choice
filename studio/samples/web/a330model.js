// a330model.js - an Airbus A330-200 built to its published size (Airbus / SKYbrary): length 58.82 m, span 60.30 m (with winglets),
// height 17.39 m, fuselage 5.64 m wide; low wing, ~30 deg sweep, straight inboard trailing edge, upswept winglets; two GE CF6-80E1
// engines (F-GZCP's type) under the wings; conventional tail with the stabilizer low on the tail cone; six-window Airbus cockpit, cabin windows
// at the 21-inch pitch, four doors a side, big belly fairing. Generic white paint, no airline livery, no registration, no logos.
//   const A = makeA330(THREE);  scene.add(A.root);   // nose toward -z, y up, origin near the wing (centre of gravity)
//   A.parts: { pitotR (group), pitotTipR, pitotMouthR, wingSecs(sd), fin, stab, navR/navL/navT, iceM, ... }   (same names as jetmodel.js)
export function makeA330(THREE) {
  const V = (x, y, z) => new THREE.Vector3(x, y, z), XAX = new THREE.Vector3(1, 0, 0);
  const L = 58.82, ZC = 27.5, R = 2.82;
  const root = new THREE.Group(); root.name = 'a330-200';
  const P = {};
  // ---------------------------------------------------------------- fuselage: round section, Airbus nose, long tail cone sweeping up
  function sec(s) { let k = 1, cy = 0;
    if (s < 8.2) { const u = s / 8.2; k = Math.pow(1 - Math.pow(1 - u, 2.2), 0.55); cy = -0.55 * Math.pow(1 - u, 2.2); }
    if (s > 43.5) { const u = (s - 43.5) / (L - 43.5); k = 1 - 0.85 * Math.pow(u, 1.25); cy = 1.75 * Math.pow(u, 1.15); }
    return [cy, Math.max(R * k, 0.03), Math.max(R * 1.0 * k, 0.03)]; }
  const NS = 260, NA = 72;
  function tube(secFn, len, ns, na, z0) { const pos = [], uv = [], idx = [];
    for (let i = 0; i <= ns; i++) { const s = len * i / ns, [cy, rx, ry] = secFn(s);
      for (let j = 0; j <= na; j++) { const a = j / na * Math.PI * 2; pos.push(rx * Math.sin(a), cy - ry * Math.cos(a), s - z0); uv.push(j / na, s / len); } }
    for (let i = 0; i < ns; i++) for (let j = 0; j < na; j++) { const a = i * (na + 1) + j, b = a + na + 1; idx.push(a, a + 1, b, b, a + 1, b + 1); }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); g.setIndex(idx); g.computeVertexNormals(); return g; }
  // paint: u = around (0 bottom, .25 right, .5 top, .75 left), v = along the fuselage
  const CW = 2048, CH = 8192, cv = document.createElement('canvas'); cv.width = CW; cv.height = CH; const g = cv.getContext('2d');
  const X = u => u * CW, Y = s => s / L * CH, CIRC = 2 * Math.PI * R;
  { const gr = g.createLinearGradient(0, 0, CW, 0); for (const [u, c] of [[0, '#b9bec5'], [0.13, '#c3c8ce'], [0.17, '#f2f2f0'], [0.83, '#f2f2f0'], [0.87, '#c3c8ce'], [1, '#b9bec5']]) gr.addColorStop(u, c); g.fillStyle = gr; g.fillRect(0, 0, CW, CH); }
  // cockpit: six windows (two big front panes, two side panes each side), black frame band like an Airbus
  { const ws = [[0.318, 4.45], [0.335, 3.55], [0.41, 3.02], [0.5, 2.92], [0.59, 3.02], [0.665, 3.55], [0.682, 4.45], [0.676, 4.95], [0.62, 4.98], [0.6, 4.3], [0.5, 4.05], [0.4, 4.3], [0.38, 4.98], [0.324, 4.95]];
    g.beginPath(); ws.forEach(([u, s]) => g.lineTo(X(u), Y(s))); g.closePath(); g.fillStyle = '#0c1219'; g.fill();
    g.strokeStyle = '#2a2f35'; g.lineWidth = 5; g.lineWidth = 9; for (const u of [0.5, 0.415, 0.585, 0.36, 0.64]) { g.beginPath(); g.moveTo(X(u), Y(2.9)); g.lineTo(X(u + (u - 0.5) * 0.06), Y(5.0)); g.stroke(); } }
  // cabin windows at the 21-inch pitch, skipping the doors and the wing box
  const DOORS = [6.4, 16.4, 37.3, 50.2];
  const winU = 0.288, wW = 0.25 / CIRC, wH = 0.36;
  for (let s = 8.0; s < 51.5; s += 0.533) { if (DOORS.some(d => Math.abs(s - d) < 1.2)) continue; if (s > 24.0 && s < 25.6) continue;
    for (const u of [winU, 1 - winU]) { g.beginPath(); g.ellipse(X(u), Y(s), X(wW) / 2 * 1.25, Y(wH) / 2, 0, 0, 7); g.fillStyle = '#c7ccd2'; g.fill(); g.beginPath(); g.ellipse(X(u), Y(s), X(wW) / 2, Y(wH) / 2 * 0.84, 0, 0, 7); g.fillStyle = '#121a24'; g.fill(); } }
  // doors: outlines with a small window, both sides; cargo doors on the right, low
  g.lineWidth = 3; g.strokeStyle = '#9ea4ab';
  for (const d of DOORS) for (const sd of [1, -1]) { const u0 = sd > 0 ? 0.22 : 0.78 - 0.11, s0 = d - 0.54; g.beginPath(); g.roundRect(X(u0), Y(s0), X(0.11), Y(1.07), 14); g.stroke();
    g.beginPath(); g.ellipse(X(u0 + 0.068), Y(d), X(wW) / 2, Y(0.3) / 2, 0, 0, 7); g.fillStyle = '#121a24'; g.fill(); }
  for (const [s0, s1] of [[11.5, 14.2], [40.5, 42.5]]) { g.beginPath(); g.roundRect(X(0.1), Y(s0), X(0.09), Y(s1 - s0), 8); g.stroke(); }
  g.strokeStyle = 'rgba(110,116,124,0.4)'; g.lineWidth = 2; for (const s of [2.2, 8.2, 20.5, 31.0, 43.5, 52.0, 56.5]) { g.beginPath(); g.moveTo(0, Y(s)); g.lineTo(CW, Y(s)); g.stroke(); }
  const paint = new THREE.CanvasTexture(cv); paint.colorSpace = THREE.SRGBColorSpace; paint.flipY = false; paint.anisotropy = 8;
  const skinM = new THREE.MeshPhysicalMaterial({ map: paint, roughness: 0.34, metalness: 0.05, clearcoat: 0.6, clearcoatRoughness: 0.18 });
  const fus = new THREE.Mesh(tube(sec, L, NS, NA, ZC), skinM); root.add(fus); P.fus = fus;
  // ---------------------------------------------------------------- lofted surfaces (same airfoil / loft as jetmodel.js)
  function airfoil(n, t, m = 0.02, p = 0.4) { const up = [], lo = [];
    for (let i = 0; i <= n; i++) { const x = 0.5 * (1 - Math.cos(Math.PI * i / n));
      const yt = 5 * t * (0.2969 * Math.sqrt(x) - 0.126 * x - 0.3516 * x * x + 0.2843 * x ** 3 - 0.1036 * x ** 4) + 0.0015;
      const yc = x < p ? m / (p * p) * (2 * p * x - x * x) : m / ((1 - p) ** 2) * ((1 - 2 * p) + 2 * p * x - x * x);
      up.push([x, yc + yt]); lo.push([x, yc - yt]); }
    return [...up.reverse(), ...lo.slice(1)]; }
  function loft(secs, nA, mat, colorFn) { const pos = [], col = [], idx = [], nP = 2 * nA + 1;
    for (const S of secs) { const af = airfoil(nA, S.t, S.m ?? 0.02), tw = (S.tw || 0) * Math.PI / 180, ch = S.ch.clone().applyAxisAngle(XAX, tw), up = S.up.clone().applyAxisAngle(XAX, tw);
      af.forEach(([x, y]) => { const p = S.o.clone().addScaledVector(ch, x * S.c).addScaledVector(up, y * S.c); pos.push(p.x, p.y, p.z); col.push(...(colorFn ? colorFn(x) : [1, 1, 1])); }); }
    for (let i = 0; i < secs.length - 1; i++) for (let j = 0; j < nP - 1; j++) { const a = i * nP + j, b = a + nP; idx.push(a, b, a + 1, a + 1, b, b + 1); }
    const last = (secs.length - 1) * nP, cen = V(0, 0, 0); for (let j = 0; j < nP; j++) cen.add(V(pos[(last + j) * 3], pos[(last + j) * 3 + 1], pos[(last + j) * 3 + 2])); cen.divideScalar(nP);
    const ci = pos.length / 3; pos.push(cen.x, cen.y, cen.z); col.push(1, 1, 1); for (let j = 0; j < nP - 1; j++) idx.push(last + j, ci, last + j + 1);
    const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3)); geo.setIndex(idx); geo.computeVertexNormals();
    return new THREE.Mesh(geo, mat); }
  const wingM = new THREE.MeshPhysicalMaterial({ color: 0xeeeeec, vertexColors: true, roughness: 0.36, metalness: 0.1, clearcoat: 0.5, clearcoatRoughness: 0.2, side: THREE.DoubleSide });
  const leMetal = x => x < 0.05 ? [0.72, 0.74, 0.77] : (x > 0.82 ? [0.9, 0.9, 0.9] : [0.93, 0.93, 0.92]);   // wings a touch grey (Airbus wing paint), bare leading edge
  const sw = d => Math.tan(d * Math.PI / 180);
  // main wing: root at the fuselage side, ~32 deg leading-edge sweep, straight inboard trailing edge to the kink, 5.5 deg dihedral, washout
  const wingSecs = sd => { const out = [], x0 = 2.3, xk = 10.5, xt = 29.6, s0 = 21.3;
    for (let i = 0; i <= 14; i++) { const x = x0 + (xt - x0) * Math.pow(i / 14, 1.0), le = s0 + (x - x0) * sw(32), te = x < xk ? 32.4 + (x - x0) * 0.08 : 32.4 + (xk - x0) * 0.08 + (x - xk) * sw(22);
      const u = (x - x0) / (xt - x0); out.push({ o: V(sd * x, -1.55 + (x - x0) * sw(5.5), le - ZC), c: te - le, t: 0.135 - 0.04 * u, tw: -4 * u, up: V(0, 1, 0), ch: V(0, 0, 1) }); }
    return out; };
  const wingR = loft(wingSecs(1), 28, wingM, leMetal), wingL = loft(wingSecs(-1), 28, wingM, leMetal); root.add(wingR, wingL); P.wingR = wingR; P.wingL = wingL;
  const tipOf = sd => wingSecs(sd)[14];
  // winglets: 2.74 m tall, canted out a little, swept
  for (const sd of [1, -1]) { const t = tipOf(sd), secs = []; for (let i = 0; i <= 6; i++) { const u = i / 6, h = 2.74 * u, c = lerp(t.c * 0.95, 0.75, Math.pow(u, 0.9));
      secs.push({ o: V(t.o.x + sd * (0.05 + h * sw(8)), t.o.y + 0.05 + h, t.o.z + 0.1 + h * sw(42) + (t.c * 0.95 - c) * 0.3 * u), c, t: 0.085, m: 0, up: V(sd, 0, 0), ch: V(0, 0, 1) }); }
    root.add(loft(secs, 16, wingM, leMetal)); }
  // vertical fin on the tail cone
  const finSecs = []; for (let i = 0; i <= 8; i++) { const u = i / 8, y = 1.9 + 8.9 * u, c = lerp(9.6, 3.5, u), s = 45.6 + 8.9 * u * sw(41);
    finSecs.push({ o: V(0, y, s - ZC), c, t: 0.11 - 0.02 * u, m: 0, up: V(1, 0, 0), ch: V(0, 0, 1) }); }
  const fin = loft(finSecs, 22, wingM, leMetal); root.add(fin); P.fin = fin;
  // horizontal stabilizer: low on the tail cone, 19.4 m span, ~34 deg sweep, 7 deg dihedral (one group, so it can be moved as a whole)
  const stab = new THREE.Group(); root.add(stab); P.stab = stab;
  for (const sd of [1, -1]) { const secs = []; for (let i = 0; i <= 8; i++) { const u = i / 8, x = 1.1 + 8.6 * u, c = lerp(6.2, 2.0, u);
      secs.push({ o: V(sd * x, 0.75 + (x - 1.1) * sw(7), 49.6 + (x - 1.1) * sw(34) - ZC), c, t: 0.1, m: 0, up: V(0, 1, 0), ch: V(0, 0, 1) }); }
    stab.add(loft(secs, 20, wingM, leMetal)); }
  // belly fairing (the big wing-to-body bulge) and the APU exhaust at the tail
  { const bf = new THREE.Mesh(new THREE.SphereGeometry(1, 48, 24), new THREE.MeshPhysicalMaterial({ color: 0xc8ccd1, roughness: 0.38, clearcoat: 0.4 })); bf.scale.set(2.55, 1.15, 10.5); bf.position.set(0, -2.15, 27.3 - ZC); root.add(bf); }
  { const ap = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.2, 0.4, 20).rotateX(Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0x2a2d31, roughness: 0.5, metalness: 0.6 })); ap.position.set(0, sec(L - 0.25)[0], L - 0.2 - ZC); root.add(ap); }
  // ---------------------------------------------------------------- CF6-80E1 nacelles on pylons, under and ahead of the wing
  const nacM = new THREE.MeshPhysicalMaterial({ color: 0xe9e9e7, roughness: 0.32, metalness: 0.1, clearcoat: 0.5 });
  const darkM = new THREE.MeshStandardMaterial({ color: 0x14171b, roughness: 0.6, metalness: 0.3 });
  const lipM = new THREE.MeshStandardMaterial({ color: 0xb8bec6, roughness: 0.25, metalness: 0.85 });
  const NL = 6.3, prof = []; for (let i = 0; i <= 44; i++) { const u = i / 44; let r;
    if (u < 0.07) r = 1.28 + 0.18 * Math.sqrt(u / 0.07); else if (u < 0.5) r = 1.46 - 0.02 * (u - 0.07); else r = 1.45 - 0.55 * Math.pow((u - 0.5) / 0.5, 1.5);
    prof.push(new THREE.Vector2(r, u * NL)); }
  for (const sd of [1, -1]) { const x = 9.7, wsI = wingSecs(sd), wle = wsI.reduce((b, S) => Math.abs(Math.abs(S.o.x) - x) < Math.abs(Math.abs(b.o.x) - x) ? S : b);
    const ng = new THREE.Group(); ng.position.set(sd * x, wle.o.y - 1.95, wle.o.z - 5.2); root.add(ng);
    ng.add(new THREE.Mesh(new THREE.LatheGeometry(prof, 56).rotateX(Math.PI / 2), nacM));
    ng.add(new THREE.Mesh(new THREE.TorusGeometry(1.32, 0.1, 12, 56), lipM));
    const fan = new THREE.Mesh(new THREE.CircleGeometry(1.25, 48), darkM); fan.position.z = 0.55; fan.rotation.y = Math.PI; ng.add(fan);
    const spin = new THREE.Mesh(new THREE.ConeGeometry(0.42, 0.9, 24).rotateX(-Math.PI / 2), lipM); spin.position.z = 0.25; ng.add(spin);
    for (let b = 0; b < 24; b++) { const bl = new THREE.Mesh(new THREE.BoxGeometry(0.09, 1.0, 0.02), lipM); const a = b / 24 * Math.PI * 2; bl.position.set(Math.sin(a) * 0.72, Math.cos(a) * 0.72, 0.52); bl.rotation.z = -a; bl.rotation.y = 0.45; ng.add(bl); }
    const ex = new THREE.Mesh(new THREE.CircleGeometry(0.88, 40), darkM); ex.position.z = NL - 0.02; ng.add(ex);
    const cone = new THREE.Mesh(new THREE.ConeGeometry(0.55, 1.6, 28).rotateX(Math.PI / 2), lipM); cone.position.z = NL + 0.4; ng.add(cone);
    const py = new THREE.Mesh(new THREE.BoxGeometry(0.5, 1.6, 6.2), nacM); py.position.set(0, 1.35, 3.6); ng.add(py); }
  // ---------------------------------------------------------------- pitot probes (lower nose sides), nav lights
  const probeM = new THREE.MeshStandardMaterial({ color: 0xc9ced4, roughness: 0.2, metalness: 0.9 });
  for (const sd of [1, -1]) { const s = 4.7, [cy, rx] = sec(s), a = 0.62; const pg = new THREE.Group(); pg.position.set(sd * rx * Math.sin(Math.PI / 2 + a) , cy - rx * Math.cos(Math.PI / 2 + a), s - ZC); root.add(pg);
    const mt = V(sd * 0.14, -0.11, -0.05), mast = new THREE.Mesh(new THREE.BoxGeometry(0.012, mt.length() + 0.02, 0.055), probeM); mast.position.copy(mt).multiplyScalar(0.5); mast.quaternion.setFromUnitVectors(V(0, 1, 0), mt.clone().normalize()); pg.add(mast);
    const tb = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.022, 0.32, 16).rotateX(Math.PI / 2), probeM); tb.position.set(sd * 0.14, -0.11, -0.15); pg.add(tb);
    const mouth = new THREE.Mesh(new THREE.CircleGeometry(0.012, 16), new THREE.MeshBasicMaterial({ color: 0x050505 })); mouth.position.set(sd * 0.14, -0.11, -0.3105); mouth.rotation.y = Math.PI; pg.add(mouth);
    if (sd > 0) { P.pitotR = pg; P.pitotTipR = V(sd * 0.14, -0.11, -0.31); P.pitotMouthR = mouth; } }
  const navL = (c, x, y, z, r = 0.12) => { const m = new THREE.Mesh(new THREE.SphereGeometry(r, 12, 8), new THREE.MeshBasicMaterial({ color: c, toneMapped: false })); m.position.set(x, y, z); root.add(m); return m; };
  { const tR = tipOf(1), tL = tipOf(-1); P.navR = navL(0x40ff70, tR.o.x + 0.1, tR.o.y, tR.o.z + 0.3); P.navL = navL(0xff3030, tL.o.x - 0.1, tL.o.y, tL.o.z + 0.3); P.navT = navL(0xffffff, 0, sec(L - 0.4)[0] + 0.4, L - 0.4 - ZC);
    P.beaconT = navL(0xff2020, 0, R + 0.08, 20 - ZC, 0.15); P.beaconB = navL(0xff2020, 0, -R - 0.08, 30 - ZC, 0.15); }
  // invisible leading-edge ice (same interface as jetmodel.js; the scenes draw ice spikes themselves)
  const iceM = new THREE.MeshStandardMaterial({ color: 0xeef6ff, transparent: true, opacity: 0, depthWrite: false });
  P.iceM = iceM; P.iceR = new THREE.Object3D(); P.iceL = new THREE.Object3D(); root.add(P.iceR, P.iceL);
  root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; const nr = o.geometry.attributes.normal; if (nr) for (let i = 0; i < nr.count; i++) if (!(Math.hypot(nr.getX(i), nr.getY(i), nr.getZ(i)) > 0.5)) nr.setXYZ(i, 0, 1, 0); } });
  P.wingSecs = wingSecs; P.sec = sec;
  return { root, parts: P, L, ZC, sec };
  function lerp(a, b, u) { return a + (b - a) * u; }
}
