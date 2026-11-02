// jetmodel.js - a Learjet 60 built to its published size (Wikipedia / FAA type data): length 17.88 m, span 13.34 m (winglets),
// height 4.47 m, low swept wing with winglets, T-tail (Learjet 35 tail), two PW305A engines high on the rear fuselage, two "delta fins"
// under the tail, wraparound windshield, 7 oval cabin windows a side, entry door forward left. Generic white paint, no tail number, no logos.
//   const J = makeLearjet60(THREE);  scene.add(J.root);   // nose toward -z, y up, origin near the wing (centre of gravity)
//   J.parts: { stab (pivot at the fin top), stabTipR (breakable outer right stab), fairing (stab bullet), iceL/iceR (wing leading-edge ice), pitotR, pitotMouthR, ... }
export function makeLearjet60(THREE) {
  const V = (x, y, z) => new THREE.Vector3(x, y, z), XAX = new THREE.Vector3(1, 0, 0);   // twist about the jet's own x (same sense both wings)
  const L = 17.88, ZC = 8.6;                     // fuselage length; stations s are metres from the nose, z = s - ZC
  const root = new THREE.Group(); root.name = 'learjet60';
  const P = {};
  // ---------------------------------------------------------------- fuselage: rings of an oval section, nose droop, tail upsweep
  const RX = 0.97, RY = 1.0;
  function sec(s) {                                // centre y, radius x, radius y at station s
    let k = 1, cy = 0;
    if (s < 3.9) { const u = s / 3.9; k = Math.pow(1 - Math.pow(1 - u, 2.3), 0.62); cy = -0.2 * Math.pow(1 - u, 2); }
    if (s > 11.6) { const u = (s - 11.6) / (L - 11.6); k = 1 - 0.86 * Math.pow(u, 1.35); cy = 0.42 * Math.pow(u, 1.25); }
    return [cy, Math.max(RX * k, 0.012), Math.max(RY * k, 0.012)]; }
  const NS = 170, NA = 64;
  function tube(secFn, len, ns, na, z0) { const pos = [], uv = [], idx = [];
    for (let i = 0; i <= ns; i++) { const s = len * i / ns, [cy, rx, ry] = secFn(s);
      for (let j = 0; j <= na; j++) { const a = j / na * Math.PI * 2; pos.push(rx * Math.sin(a), cy - ry * Math.cos(a), s - z0); uv.push(j / na, s / len); } }
    for (let i = 0; i < ns; i++) for (let j = 0; j < na; j++) { const a = i * (na + 1) + j, b = a + na + 1; idx.push(a, a + 1, b, b, a + 1, b + 1); }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); g.setIndex(idx); g.computeVertexNormals(); return g; }
  // paint: canvas u = around (0 bottom, .25 right, .5 top, .75 left), v = along (0 nose .. 1 tail); flipY off so canvas row = station
  const CW = 1024, CH = 4096, cv = document.createElement('canvas'); cv.width = CW; cv.height = CH; const g = cv.getContext('2d');
  const X = u => u * CW, Y = s => s / L * CH;
  g.fillStyle = '#f3f3f1'; g.fillRect(0, 0, CW, CH);
  { const gr = g.createLinearGradient(0, 0, CW, 0); for (const [u, c] of [[0, '#c2c6cc'], [0.1, '#c8ccd1'], [0.15, '#f3f3f1'], [0.85, '#f3f3f1'], [0.9, '#c8ccd1'], [1, '#c2c6cc']]) gr.addColorStop(u, c); g.fillStyle = gr; g.fillRect(0, 0, CW, CH); }
  // cheat lines: navy band + thin grey pinstripe, both sides, from the nose cone back to the tail cone, rising a little at the tail
  for (const sd of [1, -1]) { const uc = u => sd > 0 ? u : 1 - u;
    g.beginPath(); for (let s = 1.2; s <= 16.6; s += 0.1) { const rise = s > 12 ? (s - 12) * 0.006 : 0; g.lineTo(X(uc(0.205 + rise)), Y(s)); }
    for (let s = 16.6; s >= 1.2; s -= 0.1) { const rise = s > 12 ? (s - 12) * 0.006 : 0, w = 0.026 * (s < 2 ? (s - 1.2) / 0.8 : 1); g.lineTo(X(uc(0.205 + rise + w * sd * sd)), Y(s)); }
    g.closePath(); g.fillStyle = '#1c2a4b'; g.fill();
    g.strokeStyle = '#8f98a6'; g.lineWidth = 3; g.beginPath(); for (let s = 1.6; s <= 16.2; s += 0.1) { const rise = s > 12 ? (s - 12) * 0.006 : 0; g.lineTo(X(uc(0.239 + rise)), Y(s)); } g.stroke(); }
  // windshield (dark, glossy through the clearcoat) wrapping the nose top, with frame posts
  const wsPoly = [[0.305, 3.95], [0.318, 2.95], [0.39, 2.42], [0.5, 2.26], [0.61, 2.42], [0.682, 2.95], [0.695, 3.95], [0.64, 3.98], [0.615, 3.3], [0.5, 3.12], [0.385, 3.3], [0.36, 3.98]];
  g.beginPath(); wsPoly.forEach(([u, s]) => g.lineTo(X(u), Y(s))); g.closePath(); g.fillStyle = '#0d141c'; g.fill();
  g.strokeStyle = '#e9e9e6'; g.lineWidth = 7; for (const [a, b] of [[[0.5, 2.26], [0.5, 3.12]], [[0.36, 2.62], [0.392, 3.28]], [[0.64, 2.62], [0.608, 3.28]], [[0.312, 3.45], [0.372, 3.45]], [[0.688, 3.45], [0.628, 3.45]]]) { g.beginPath(); g.moveTo(X(a[0]), Y(a[1])); g.lineTo(X(b[0]), Y(b[1])); g.stroke(); }
  { const gr = g.createLinearGradient(X(0.4), 0, X(0.6), 0); gr.addColorStop(0, 'rgba(120,150,180,0)'); gr.addColorStop(0.5, 'rgba(150,180,210,0.25)'); gr.addColorStop(1, 'rgba(120,150,180,0)'); g.fillStyle = gr; g.fillRect(X(0.4), Y(2.45), X(0.2), Y(0.5)); }
  // cabin windows: rounded ovals above the side's midline
  const oval = (u, s, wu, hs, fill) => { g.beginPath(); g.ellipse(X(u), Y(s), X(wu) / 2, Y(hs) / 2, 0, 0, Math.PI * 2); g.fillStyle = fill; g.fill(); };
  for (const sd of [1, -1]) for (let i = 0; i < 7; i++) { const s = 5.05 + i * 0.74, u = sd > 0 ? 0.287 : 0.713; oval(u, s, 0.064, 0.36, '#c9ced4'); oval(u, s, 0.052, 0.3, '#121a24'); }
  // entry door, forward left (thin outline), baggage door aft right, panel lines
  g.strokeStyle = '#a9adb3'; g.lineWidth = 3; { const r = 18; const x0 = X(0.672), x1 = X(0.79), y0 = Y(4.02), y1 = Y(4.86); g.beginPath(); g.roundRect(x0, y0, x1 - x0, y1 - y0, r); g.stroke(); }
  { const x0 = X(0.24), x1 = X(0.31), y0 = Y(11.0), y1 = Y(11.6); g.beginPath(); g.roundRect(x0, y0, x1 - x0, y1 - y0, 10); g.stroke(); }
  g.strokeStyle = 'rgba(120,125,132,0.45)'; g.lineWidth = 2; for (const s of [1.05, 2.2, 3.95, 10.7, 12.3, 14.6, 16.4]) { g.beginPath(); g.moveTo(0, Y(s)); g.lineTo(CW, Y(s)); g.stroke(); }
  // static ports / antennas dots
  g.fillStyle = '#7a7f86'; for (const [u, s] of [[0.27, 1.9], [0.73, 1.9], [0.5, 6.2], [0.5, 9.8], [0.02, 7.0]]) { g.beginPath(); g.arc(X(u), Y(s), 4, 0, 7); g.fill(); }
  const paint = new THREE.CanvasTexture(cv); paint.colorSpace = THREE.SRGBColorSpace; paint.flipY = false; paint.anisotropy = 8;
  const skinM = new THREE.MeshPhysicalMaterial({ map: paint, roughness: 0.32, metalness: 0.05, clearcoat: 0.7, clearcoatRoughness: 0.15 });
  const fus = new THREE.Mesh(tube(sec, L, NS, NA, ZC), skinM); fus.castShadow = fus.receiveShadow = true; root.add(fus); P.fus = fus;
  // ---------------------------------------------------------------- lifting surfaces: lofted NACA sections
  function airfoil(n, t, m = 0.02, p = 0.4) { const up = [], lo = [];
    for (let i = 0; i <= n; i++) { const x = 0.5 * (1 - Math.cos(Math.PI * i / n));
      const yt = 5 * t * (0.2969 * Math.sqrt(x) - 0.126 * x - 0.3516 * x * x + 0.2843 * x ** 3 - 0.1036 * x ** 4) + (x > 0.999 ? 0 : 0);
      const yc = x < p ? m / (p * p) * (2 * p * x - x * x) : m / ((1 - p) ** 2) * ((1 - 2 * p) + 2 * p * x - x * x);
      up.push([x, yc + yt]); lo.push([x, yc - yt]); }
    return [...up.reverse(), ...lo.slice(1)]; }     // TE (top) -> LE -> TE (bottom)
  // sections: {o: leading-edge point (Vector3), c: chord, t: thickness, tw: twist deg, up: thickness direction (Vector3), ch: chord direction (Vector3)}
  function loft(secs, nA = 26, mat, colorFn) { const pos = [], col = [], idx = [], nP = 2 * nA + 1;
    for (const S of secs) { const af = airfoil(nA, S.t, S.m ?? 0.02); const tw = (S.tw || 0) * Math.PI / 180;
      const ch = S.ch.clone().applyAxisAngle(XAX, tw), up = S.up.clone().applyAxisAngle(XAX, tw);
      af.forEach(([x, y], k) => { const p = S.o.clone().addScaledVector(ch, x * S.c).addScaledVector(up, y * S.c); pos.push(p.x, p.y, p.z);
        const c = colorFn ? colorFn(x, k) : [1, 1, 1]; col.push(...c); }); }
    for (let i = 0; i < secs.length - 1; i++) for (let j = 0; j < nP - 1; j++) { const a = i * nP + j, b = a + nP; idx.push(a, b, a + 1, a + 1, b, b + 1); }
    // close the tip (a fan to the tip section's middle)
    const last = (secs.length - 1) * nP; const cen = V(0, 0, 0); for (let j = 0; j < nP; j++) cen.add(V(pos[(last + j) * 3], pos[(last + j) * 3 + 1], pos[(last + j) * 3 + 2])); cen.divideScalar(nP);
    const ci = pos.length / 3; pos.push(cen.x, cen.y, cen.z); col.push(1, 1, 1); for (let j = 0; j < nP - 1; j++) idx.push(last + j, ci, last + j + 1);
    const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3)); geo.setIndex(idx); geo.computeVertexNormals();
    const me = new THREE.Mesh(geo, mat); me.castShadow = me.receiveShadow = true; return me; }
  const wingM = new THREE.MeshPhysicalMaterial({ color: 0xf1f1ef, vertexColors: true, roughness: 0.33, metalness: 0.08, clearcoat: 0.6, clearcoatRoughness: 0.18, side: THREE.DoubleSide });
  const leMetal = (x) => x < 0.07 ? [0.74, 0.76, 0.79] : (x > 0.84 ? [0.93, 0.93, 0.93] : [1, 1, 1]);   // bare heated leading edge, flap/aileron line
  const sw = d => Math.tan(d * Math.PI / 180);
  // main wing (low, 2.5 deg dihedral, ~15 deg leading-edge sweep, washout), root at the fuselage side
  const wingSecs = sd => { const out = []; const s0 = 7.15, y0 = -0.56, x0 = 0.55, semi = 5.65;
    for (let i = 0; i <= 10; i++) { const u = i / 10, x = x0 + semi * u, c = 2.85 + (1.05 - 2.85) * u, y = y0 + (x - x0) * sw(2.5), z = s0 + (x - x0) * sw(15) - ZC;
      out.push({ o: V(sd * x, y, z), c, t: 0.135 - 0.04 * u, tw: -3 * u, up: V(0, 1, 0), ch: V(0, 0, 1), span: V(sd, 0, 0) }); }
    return out; };
  const wingR = loft(wingSecs(1), 26, wingM, leMetal), wingL = loft(wingSecs(-1), 26, wingM, leMetal); root.add(wingR, wingL); P.wingR = wingR; P.wingL = wingL;
  const tipOf = sd => { const s = wingSecs(sd)[10]; return s; };
  // winglets: up and canted out 15 deg, swept 38 deg, chord 1.05 -> 0.42
  const wingletSecs = sd => { const t = tipOf(sd), out = [];
    for (let i = 0; i <= 6; i++) { const u = i / 6, h = 0.98 * u, c = 1.02 + (0.42 - 1.02) * Math.pow(u, 0.8);
      const o = V(t.o.x + sd * (0.02 + h * sw(15)), t.o.y + h + 0.02, t.o.z + 0.03 + h * sw(38) + (1.02 - c) * 0.25 * u);
      out.push({ o, c, t: 0.09, m: 0, tw: 0, up: V(sd, 0, 0), ch: V(0, 0, 1), span: V(0, 1, 0) }); }
    return out; };
  for (const sd of [1, -1]) { const wl = loft(wingletSecs(sd), 18, wingM, leMetal); root.add(wl); }
  // tip blend: a short fairing between the wing tip and the winglet foot
  // vertical fin: base on the tail cone, 50 deg sweep
  const finSecs = []; for (let i = 0; i <= 8; i++) { const u = i / 8, y = 0.42 + 2.33 * u, c = 3.25 + (1.45 - 3.25) * u, z = 13.55 + 2.33 * u * sw(50) - ZC;
    finSecs.push({ o: V(0, y, z), c, t: 0.11 - 0.02 * u, m: 0, up: V(1, 0, 0), ch: V(0, 0, 1), span: V(0, 1, 0) }); }
  const fin = loft(finSecs, 22, wingM, leMetal); root.add(fin); P.fin = fin;
  const finTop = finSecs[8];
  // horizontal stabilizer on top (T-tail), pivot group so it can flutter; outer right part separable (breakup beat)
  const stab = new THREE.Group(); stab.position.set(0, finTop.o.y - 0.02, finTop.o.z + 0.55); root.add(stab); P.stab = stab;
  const stabSecs = (sd, u0, u1) => { const out = []; for (let i = 0; i <= 6; i++) { const u = u0 + (u1 - u0) * i / 6, x = 0.05 + 2.2 * u, c = 1.5 + (0.72 - 1.5) * u;
      out.push({ o: V(sd * x, -x * sw(2), -0.55 + x * sw(30)), c, t: 0.095, m: 0, up: V(0, 1, 0), ch: V(0, 0, 1), span: V(sd, 0, 0) }); } return out; };
  stab.add(loft(stabSecs(-1, 0, 1), 20, wingM, leMetal));
  stab.add(loft(stabSecs(1, 0, 0.55), 20, wingM, leMetal));
  const stabTipR = new THREE.Group(); stab.add(stabTipR); const tipMesh = loft(stabSecs(1, 0.55, 1), 20, wingM, leMetal); stabTipR.add(tipMesh); P.stabTipR = stabTipR;
  // bullet fairing at the fin/stab joint
  const bul = new THREE.Mesh(new THREE.SphereGeometry(1, 28, 16), skinM.clone()); bul.material.map = null; bul.material.color.set(0xf1f1ef);
  bul.scale.set(0.16, 0.17, 0.95); bul.position.set(0, 0.04, -0.15); stab.add(bul); bul.castShadow = true; P.fairing = bul;
  // ventral "delta fins" under the tail cone, 45 deg out each side
  for (const sd of [1, -1]) { const sh = new THREE.Shape(); sh.moveTo(0, 0); sh.lineTo(1.9, 0); sh.lineTo(1.75, -0.62); sh.lineTo(1.2, -0.66); sh.closePath();
    const df = new THREE.Mesh(new THREE.ExtrudeGeometry(sh, { depth: 0.035, bevelEnabled: true, bevelThickness: 0.01, bevelSize: 0.01, bevelSegments: 2 }), wingM.clone());
    df.material.vertexColors = false; df.rotation.set(0, -Math.PI / 2, 0); const piv = new THREE.Group(); piv.add(df); piv.rotation.z = sd * 0.7; piv.position.set(0, -0.32, 14.6 - ZC); root.add(piv); df.castShadow = true; }
  // wing-to-body fairing
  { const wf = new THREE.Mesh(new THREE.SphereGeometry(1, 40, 20), new THREE.MeshPhysicalMaterial({ color: 0xd9dce0, roughness: 0.35, clearcoat: 0.5 }));
    wf.scale.set(0.82, 0.34, 2.3); wf.position.set(0, -0.7, 8.4 - ZC); root.add(wf); wf.castShadow = wf.receiveShadow = true; }
  // ---------------------------------------------------------------- engines: nacelles on short pylons, high on the rear fuselage
  const nacM = new THREE.MeshPhysicalMaterial({ color: 0xeeeeec, roughness: 0.3, metalness: 0.1, clearcoat: 0.6 });
  const darkM = new THREE.MeshStandardMaterial({ color: 0x15181c, roughness: 0.6, metalness: 0.3 });
  const lipM = new THREE.MeshStandardMaterial({ color: 0xb6bcc4, roughness: 0.25, metalness: 0.85 });
  const nacProf = []; const NL = 2.75; for (let i = 0; i <= 40; i++) { const u = i / 40; let r;
    if (u < 0.08) r = 0.43 + 0.09 * Math.sqrt(u / 0.08); else if (u < 0.55) r = 0.52; else r = 0.52 - 0.17 * Math.pow((u - 0.55) / 0.45, 1.6);
    nacProf.push(new THREE.Vector2(r, u * NL)); }
  for (const sd of [1, -1]) { const ng = new THREE.Group(); ng.position.set(sd * 1.55, 0.5, 12.15 - ZC); root.add(ng);
    const nac = new THREE.Mesh(new THREE.LatheGeometry(nacProf, 48).rotateX(Math.PI / 2), nacM); nac.castShadow = nac.receiveShadow = true; ng.add(nac);
    const lip = new THREE.Mesh(new THREE.TorusGeometry(0.455, 0.045, 12, 48), lipM); ng.add(lip);
    const fan = new THREE.Mesh(new THREE.CircleGeometry(0.42, 40), darkM); fan.position.z = 0.22; fan.rotation.y = Math.PI; ng.add(fan);
    const spin = new THREE.Mesh(new THREE.ConeGeometry(0.13, 0.28, 20).rotateX(-Math.PI / 2), lipM); spin.position.z = 0.1; ng.add(spin);
    for (let b = 0; b < 18; b++) { const bl = new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.36, 0.01), lipM); const a = b / 18 * Math.PI * 2; bl.position.set(Math.sin(a) * 0.24, Math.cos(a) * 0.24, 0.215); bl.rotation.z = -a; bl.rotation.y = 0.5; ng.add(bl); }
    const ex = new THREE.Mesh(new THREE.CircleGeometry(0.34, 32), darkM); ex.position.z = NL - 0.02; ng.add(ex);
    const cone = new THREE.Mesh(new THREE.ConeGeometry(0.18, 0.5, 24).rotateX(Math.PI / 2), lipM); cone.position.z = NL + 0.08; ng.add(cone);
    // pylon: a flattened wedge from the fuselage side to the nacelle
    const py = new THREE.Mesh(new THREE.BoxGeometry(0.62, 0.14, 1.45), nacM); py.position.set(-sd * 0.6, -0.02, 1.3); py.rotation.z = sd * 0.12; py.castShadow = true; ng.add(py); }
  // ---------------------------------------------------------------- small details: pitot probes (lower nose sides), nav lights, antennas
  const probeM = new THREE.MeshStandardMaterial({ color: 0xc9ced4, roughness: 0.2, metalness: 0.9 });
  for (const sd of [1, -1]) { const pg = new THREE.Group(); const s = 1.55, [cy, rx] = sec(s); pg.position.set(sd * rx * 0.86, cy - 0.32, s - ZC); root.add(pg);
    const mt = V(sd * 0.1, -0.06, -0.035), mlen = mt.length(); const mast = new THREE.Mesh(new THREE.BoxGeometry(0.008, mlen + 0.02, 0.045), probeM);   // a thin blade from the skin out to the tube
    mast.position.copy(mt).multiplyScalar(0.5); mast.quaternion.setFromUnitVectors(V(0, 1, 0), mt.clone().normalize()); pg.add(mast);
    const tb = new THREE.Mesh(new THREE.CylinderGeometry(0.011, 0.013, 0.24, 16).rotateX(Math.PI / 2), probeM); tb.position.set(sd * 0.1, -0.06, -0.1); pg.add(tb);
    const mouth = new THREE.Mesh(new THREE.CircleGeometry(0.0075, 16), new THREE.MeshBasicMaterial({ color: 0x050505 })); mouth.position.set(sd * 0.1, -0.06, -0.2205); mouth.rotation.y = Math.PI; pg.add(mouth);
    if (sd > 0) { P.pitotR = pg; P.pitotTipR = V(sd * 0.1, -0.06, -0.22); P.pitotMouthR = mouth; } }
  const navL = (c, x, y, z) => { const m = new THREE.Mesh(new THREE.SphereGeometry(0.045, 12, 8), new THREE.MeshBasicMaterial({ color: c, toneMapped: false })); m.position.set(x, y, z); root.add(m); return m; };
  { const tR = tipOf(1), tL = tipOf(-1); P.navR = navL(0x40ff70, tR.o.x + 0.06, tR.o.y + 0.08, tR.o.z + 0.2); P.navL = navL(0xff3030, tL.o.x - 0.06, tL.o.y + 0.08, tL.o.z + 0.2); P.navT = navL(0xffffff, 0, 0.42, L - ZC - 0.05); }
  for (const [y, z, h] of [[1.0, 5.0 - ZC, 0.22], [-1.0, 10.0 - ZC, 0.16]]) { const an = new THREE.Mesh(new THREE.BoxGeometry(0.015, h, 0.12), probeM); an.position.set(0, y + Math.sign(y) * h / 2, z); an.rotation.x = 0.4; root.add(an); }
  // ---------------------------------------------------------------- ice on the wing leading edges (beat 3): a rough white rim, opacity driven by the scene
  const iceM = new THREE.MeshStandardMaterial({ color: 0xeef6ff, roughness: 0.9, transparent: true, opacity: 0, depthWrite: false });
  function iceFor(sd) { const secs = wingSecs(sd); const pos = [], idx = []; const nA = 10;
    secs.forEach((S, i) => { const tw = (S.tw || 0) * Math.PI / 180, ch = S.ch.clone().applyAxisAngle(XAX, tw), up = S.up.clone().applyAxisAngle(XAX, tw);
      for (let k = 0; k <= nA; k++) { const a = Math.PI * (0.5 + k / nA), r = 0.035 * S.c * (1 + 0.25 * Math.sin(i * 7.1 + k * 3.3));
        const p = S.o.clone().addScaledVector(ch, 0.035 * S.c + Math.cos(a) * r * 1.25).addScaledVector(up, Math.sin(a) * -r * 1.4); pos.push(p.x, p.y, p.z); } });
    for (let i = 0; i < secs.length - 1; i++) for (let k = 0; k < nA; k++) { const a = i * (nA + 1) + k, b = a + nA + 1; idx.push(a, b, a + 1, a + 1, b, b + 1); }
    const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); geo.setIndex(idx); geo.computeVertexNormals();
    const nr = geo.attributes.normal; for (let i = 0; i < nr.count; i++) if (Math.hypot(nr.getX(i), nr.getY(i), nr.getZ(i)) < 0.5) nr.setXYZ(i, 0, 1, 0);   // no zero normals (NaN in the shader)
    const m = new THREE.Mesh(geo, iceM); m.visible = false; root.add(m); return m; }
  P.iceR = iceFor(1); P.iceL = iceFor(-1); P.iceM = iceM;
  root.traverse(o => { if (o.isMesh && o.material !== iceM) { o.castShadow = true; o.receiveShadow = true; } });
  // a zero-length normal turns into NaN in the shader and paints black pixels through the film pass: fix any, on every part
  root.traverse(o => { const nr = o.isMesh && o.geometry.attributes.normal; if (!nr) return; for (let i = 0; i < nr.count; i++) if (!(Math.hypot(nr.getX(i), nr.getY(i), nr.getZ(i)) > 0.5)) nr.setXYZ(i, 0, 1, 0); });
  P.wingSecs = wingSecs;
  return { root, parts: P, L, ZC, sec };
}
