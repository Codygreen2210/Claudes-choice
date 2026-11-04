// ------------------------------------------------------------------ set: Ford Field (indoors, afternoon game), the Lions' 25, three players in full pads (colours and numbers only, no logos)
home.visible = false; lamp.visible = false;
scene.background = new THREE.Color(0x1a1d24); scene.environmentIntensity = 0.45; scene.fog = new THREE.Fog(0x22262e, 90, 260);
hemi.color.set(0xe8eef8); hemi.groundColor.set(0x2c4a26); hemi.intensity = 0.6;
sun.color.set(0xfff8ee); sun.intensity = 2.6;
{ const S = sun.shadow.camera; S.left = -9; S.right = 9; S.top = 9; S.bottom = -9; S.near = 1; S.far = 120; S.updateProjectionMatrix(); }
// the field, in metres: x across (sideline to sideline), z along. The Lions' goal line is at -z, so the Vikings drive toward -z.
const YD = 0.9144, FW = 160 / 3 * YD, GL = 50 * YD, EZ = 10 * YD;
const zOf = (side, yd) => side === 'DET' ? -GL + yd * YD : GL - yd * YD;     // a yard line by its name: DET 25 = 25 yards out from the Lions' goal line
const SPOT = V(1.1, 0, zOf('DET', 25));                                         // where Hockenson went down: the Lions 25, between the hashes (short middle)
const HASHX = FW / 2 - (70 * 12 + 9) * 0.0254;                                  // NFL hashes: 70 ft 9 in in from each sideline (18 ft 6 in apart)
const HONOLULU = 0x0076b6, LSILVER = 0xa5acaf, VPURPLE = 0x4f2683, VGOLD = 0xffc62f;
// turf: green with 5-yard mow bands; fine grain from world position in the shader
const turfTex = canvasTex(512, 2048, g => { const N = 24; for (let i = 0; i < N; i++) { g.fillStyle = i % 2 ? '#18421a' : '#1c4a1e'; g.fillRect(0, i * 2048 / N, 512, 2048 / N + 1); }
  for (let k = 0; k < 14000; k++) { g.fillStyle = `rgba(${18 + 30 * Math.random()},${55 + 50 * Math.random()},${18 + 20 * Math.random()},0.22)`; g.fillRect(Math.random() * 512, Math.random() * 2048, 1.5, 2.5); } });
const turfM = new THREE.MeshStandardMaterial({ map: turfTex, roughness: 0.95 });
turfM.onBeforeCompile = sh => { sh.vertexShader = 'varying vec3 vWP;\n' + sh.vertexShader.replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\n vWP = (modelMatrix * vec4(transformed, 1.0)).xyz;');
  sh.fragmentShader = 'varying vec3 vWP;\nfloat th(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }\n' + sh.fragmentShader
    .replace('#include <map_fragment>', `#include <map_fragment>
      { float g1 = th(floor(vWP.xz * 260.0)), g2 = th(floor(vWP.xz * 45.0) + 7.0); float fd = clamp(1.0 - length(fwidth(vWP.xz)) * 90.0, 0.0, 1.0);
        diffuseColor.rgb *= 1.0 + fd * (0.22 * (g1 - 0.5) + 0.1 * (g2 - 0.5)); }`); };
turfM.customProgramCacheKey = () => 'turf';
const field = new THREE.Mesh(new THREE.PlaneGeometry(FW + 14, 2 * GL + 2 * EZ + 14).rotateX(-Math.PI / 2), turfM); field.receiveShadow = true; scene.add(field);
turfTex.wrapS = turfTex.wrapT = THREE.RepeatWrapping; turfTex.repeat.set(1, (2 * GL + 2 * EZ + 14) / (24 * 5 * YD));
// lines are their own thin planes (crisp at any distance): sidelines and end lines (6 ft border), goal lines, every 5 yards, the yard ticks and hashes
const lineM = new THREE.MeshStandardMaterial({ color: 0xf2f2ee, roughness: 0.8, polygonOffset: true, polygonOffsetFactor: -2 });
const LINES = new THREE.Group(); scene.add(LINES);
const strip = (x0, z0, x1, z1, y = 0.004, m = lineM) => { const w = Math.abs(x1 - x0), d = Math.abs(z1 - z0); const s = new THREE.Mesh(new THREE.PlaneGeometry(w, d).rotateX(-Math.PI / 2), m); s.position.set((x0 + x1) / 2, y, (z0 + z1) / 2); s.receiveShadow = true; LINES.add(s); return s; };
const W4 = 4 * 0.0254;
strip(-FW / 2 - 1.83, -GL - EZ - 1.83, -FW / 2, GL + EZ + 1.83); strip(FW / 2, -GL - EZ - 1.83, FW / 2 + 1.83, GL + EZ + 1.83);
strip(-FW / 2, -GL - EZ - 1.83, FW / 2, -GL - EZ); strip(-FW / 2, GL + EZ, FW / 2, GL + EZ + 1.83);
for (let yd = 0; yd <= 100; yd += 5) { const z = -GL + yd * YD, w = yd % 100 === 0 ? 8 * 0.0254 : W4; strip(-FW / 2, z - w / 2, FW / 2, z + w / 2); }
{ const tick = new THREE.InstancedMesh(new THREE.PlaneGeometry(W4, 0.61).rotateX(-Math.PI / 2), lineM, 99 * 4); const m4 = new THREE.Matrix4(); let n = 0;
  for (let yd = 1; yd < 100; yd++) { if (yd % 5 === 0) continue; const z = -GL + yd * YD;
    for (const x of [-FW / 2 + 0.15 + 0.305, FW / 2 - 0.15 - 0.305, -HASHX, HASHX]) { m4.makeTranslation(x, 0.004, z); m4.multiply(new THREE.Matrix4().makeRotationY(Math.PI / 2)); tick.setMatrixAt(n++, m4); } }
  tick.count = n; tick.receiveShadow = true; LINES.add(tick); }
// end zones in Honolulu blue (plain: no wordmarks)
const ezM = new THREE.MeshStandardMaterial({ color: HONOLULU, roughness: 0.9, polygonOffset: true, polygonOffsetFactor: -1 });
for (const s of [-1, 1]) strip(-FW / 2, s < 0 ? -GL - EZ : GL, FW / 2, s < 0 ? -GL : GL + EZ, 0.003, ezM);
// yard numbers: 6 ft tall, tops 12 yards in from each sideline, bottoms toward the sideline, arrows pointing to the nearer goal
const numTex = {}; const digitTex = d => numTex[d] || (numTex[d] = canvasTex(128, 192, g => { g.fillStyle = '#f2f2ee'; g.font = 'bold 190px Arial, Helvetica, sans-serif'; g.textAlign = 'center'; g.textBaseline = 'alphabetic'; g.fillText(d, 64, 180); }));
const arrowTex = canvasTex(64, 64, g => { g.fillStyle = '#f2f2ee'; g.beginPath(); g.moveTo(4, 32); g.lineTo(60, 8); g.lineTo(60, 56); g.fill(); });
for (let yd = 10; yd <= 90; yd += 10) { const z = -GL + yd * YD, label = String(yd <= 50 ? yd : 100 - yd);
  for (const side of [-1, 1]) { const xc = side * (FW / 2 - 12 * YD + 1.83 / 2);   // centre of the 6-ft tall number band
    [...label].forEach((d, i) => { const p = new THREE.Mesh(new THREE.PlaneGeometry(1.22, 1.83).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ map: digitTex(d), transparent: true, roughness: 0.85, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -3 }));
      // the reader stands at the near sideline: the number's bottom faces that sideline
      p.rotation.y = side > 0 ? -Math.PI / 2 : Math.PI / 2; const off = (i - (label.length - 1) / 2) * 1.35; p.position.set(xc, 0.005, z + (side > 0 ? -off : off)); p.receiveShadow = true; LINES.add(p); });
    if (yd !== 50) { const toward = yd < 50 ? -1 : 1, a = new THREE.Mesh(new THREE.PlaneGeometry(0.45, 0.45).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ map: arrowTex, transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -3 }));
      a.rotation.y = toward < 0 ? Math.PI / 2 : -Math.PI / 2; a.position.set(xc + side * 0.55, 0.005, z + toward * (1.35 * (label.length) / 2 + 0.55)); LINES.add(a); } } }
// goalposts at the end lines (yellow)
for (const s of [-1, 1]) { const gp = new THREE.Group(); gp.position.set(0, 0, s * (GL + EZ + 1.83)); scene.add(gp); const ym = mat(0xf5d21e, 0.4, 0.2);
  const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 3.05, 12), ym); pole.position.y = 1.52; gp.add(pole);
  const arm = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, 1.8, 12).rotateX(Math.PI / 2), ym); arm.position.set(0, 3.05, -s * 0.9); gp.add(arm);
  const bar = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 5.64, 12).rotateZ(Math.PI / 2), ym); bar.position.set(0, 3.05, -s * 1.8); gp.add(bar);
  for (const x of [-2.82, 2.82]) { const up = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 9.1, 10), ym); up.position.set(x, 3.05 + 4.55, -s * 1.8); gp.add(up); } }
// the stands (a domed stadium): rows stepping back from the field on all four sides, an instanced crowd (blue and silver, some purple), the roof
const stands = new THREE.Group(); scene.add(stands);
{ const sm = mat(0x2a2e36, 0.9); const crowd = []; const LEN = 2 * GL + 2 * EZ;
  const add = (w, x, z, ry) => { for (let r = 0; r < 26; r++) { const st = box(w, 0.42, 0.8, 0, 0, 0, sm, 0, stands); const dir = V(Math.sin(ry), 0, Math.cos(ry));
      st.position.set(x, 1.2 + r * 0.42, z).addScaledVector(dir, r * 0.82); st.rotation.y = ry;
      for (let k = 0; k < w; k += 0.52) crowd.push(st.position.clone().add(V(Math.cos(ry), 0, -Math.sin(ry)).multiplyScalar(k - w / 2)).add(V(0, 0.48, 0))); } };
  add(LEN + 12, FW / 2 + 9, 0, Math.PI / 2); add(LEN + 12, -FW / 2 - 9, 0, -Math.PI / 2); add(FW + 18, 0, -LEN / 2 - 8, Math.PI); add(FW + 18, 0, LEN / 2 + 8, 0);
  const cm = new THREE.InstancedMesh(new THREE.BoxGeometry(0.4, 0.62, 0.3), new THREE.MeshStandardMaterial({ roughness: 0.8 }), crowd.length); const m4 = new THREE.Matrix4();
  const PAL = [0x0076b6, 0x0076b6, 0x0a5c90, 0xb0b7bb, 0xe8e8e4, 0x1b1d22, 0x4f2683, 0x7a1f2a, 0x3a4048];
  crowd.forEach((p, i) => { m4.makeTranslation(p.x, p.y + 0.06 * hash1(i * 9.1), p.z); cm.setMatrixAt(i, m4); const c = new THREE.Color(PAL[Math.floor(hash1(i * 1.7) * PAL.length)]); c.multiplyScalar(0.55 + 0.5 * hash1(i * 3.3)); cm.setColorAt(i, c); });
  stands.add(cm);
  const wall = mat(0x0a6aa6, 0.75); box(FW + 6, 1.4, 0.3, 0, 0.7, -LEN / 2 - 5, wall, 0, stands); box(FW + 6, 1.4, 0.3, 0, 0.7, LEN / 2 + 5, wall, 0, stands);   // padded walls in Honolulu blue (match photos)
  box(0.3, 1.4, LEN + 10, -FW / 2 - 7.5, 0.7, 0, wall, 0, stands); box(0.3, 1.4, LEN + 10, FW / 2 + 7.5, 0.7, 0, wall, 0, stands);
  // the roof: a dark lid with rows of lights, and a lit band of suite windows on the sides
  const roof = new THREE.Mesh(new THREE.PlaneGeometry(260, 300).rotateX(Math.PI / 2), mat(0x2a2d33, 0.9)); roof.position.y = 58; stands.add(roof);
  const lightM = new THREE.MeshBasicMaterial({ color: 0xffffff, toneMapped: false });
  for (let i = -6; i <= 6; i++) for (const x of [-30, -15, 0, 15, 30]) { const l = new THREE.Mesh(new THREE.PlaneGeometry(2.4, 0.8).rotateX(Math.PI / 2), lightM); l.position.set(x, 57.8, i * 14); stands.add(l); }
  for (const s of [-1, 1]) { const band = new THREE.Mesh(new THREE.PlaneGeometry(LEN + 20, 2.2), new THREE.MeshBasicMaterial({ color: 0xffe6b8, toneMapped: false })); band.position.set(s * (FW / 2 + 31), 14.5, 0); band.rotation.y = -s * Math.PI / 2; stands.add(band); } }
for (const [x, z] of [[-20, -40], [20, -40], [-20, 0], [20, 0], [-20, 40], [20, 40]]) { const fl = new THREE.SpotLight(0xf6f8ff, 380, 120, 0.9, 0.6, 1.3); fl.position.set(x, 52, z); fl.target.position.set(x * 0.4, 0, z); scene.add(fl, fl.target); }

// ------------------------------------------------------------------ the players: the MakeHuman man three times (Campbell #46 and O'Neill #66 in the Lions' silver Rivalries set; Hockenson #87 in all purple)
const K_H = await loadGuy(THREE, '/char/' + (Q.get('char') || window.CHARDEF || 'guy'), { fingers3: !!window.FINGERS3 }); scene.add(K_H.root);
const K_O = await loadGuy(THREE, '/char/' + (Q.get('char') || window.CHARDEF || 'guy'), { fingers3: !!window.FINGERS3 }); scene.add(K_O.root);
for (const g of [K_H, K_O]) g.root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
const RH = makeRig(K_H, 'hock'), RO = makeRig(K_O, 'oneill');
// kit colours (linear values go to shaders; THREE.Color does the sRGB conversion)
const KITS = {
  // from the game photos (Nov 1): Lions silver jersey and pants, dark slanted numbers with a blue outline, a black-and-blue stripe on the shoulder and down the lower thigh,
  // black socks and cleats, bare hands, Honolulu blue helmet with a black centre stripe and a black facemask. Vikings all purple, white numbers with gold trim,
  // gold-and-white shoulder stripes, white gloves and white cleats, a dark facemask.
  DET: { jersey: 0xb7bcc0, pants: 0xb3b8bc, sock: 0x151619, shoe: 0x151619, glove: null, helmet: HONOLULU, stripe: 0x111214, mask: 0x141518, num: '#2b2e33', numLine: '#0a84d0', name: '#2b2e33', italic: true, cap: [0x141518, HONOLULU], pantStripe: [0x141518, HONOLULU] },
  MIN: { jersey: VPURPLE, pants: VPURPLE, sock: VPURPLE, shoe: 0xeeeeea, glove: 0xf2f2ee, helmet: VPURPLE, stripe: null, mask: 0x2b2238, num: '#ffffff', numLine: '#ffc62f', name: '#ffffff', italic: false, cap: [VGOLD, 0xffffff], pantStripe: null },
};
// the jersey number, drawn once per player (front and back of the pads; small on the shoulder caps)
function nameTex(nm, K) { return canvasTex(1024, 160, g => { g.clearRect(0, 0, 1024, 160); g.font = '800 120px "Inter Display", "Liberation Sans", sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillStyle = K.name; g.fillText(nm, 512, 84, 980); }); }
function numberTex(n, K) { return canvasTex(512, 384, g => { g.clearRect(0, 0, 512, 384); g.save(); g.translate(256, 200); if (K.italic) g.transform(1, 0, -0.22, 1, 0, 0);
  g.font = '900 330px "Inter Display", "Liberation Sans", sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.lineJoin = 'round';
  g.lineWidth = 26; g.strokeStyle = K.numLine; g.strokeText(String(n), 0, 0); g.fillStyle = K.num; g.fillText(String(n), 0, 0); g.restore(); }); }
const lin = c => new THREE.Color(c);
const PLAYERS = [];
function suitUp(Gx, team, number, name, tattoo = false) { const K = KITS[team]; Gx.reset(); Gx.root.position.set(0, 0, 0); Gx.root.quaternion.identity(); Gx.root.updateMatrixWorld(true);
  const P = { G: Gx, team, number, K };
  for (const [n, c, r] of [['shirt', K.jersey, 0.62], ['jeans', K.pants, 0.6], ['shoeR', K.shoe, 0.45], ['shoeL', K.shoe, 0.45]]) { const m = Gx.meshes[n]; if (!m) continue;
    m.material = m.material.clone(); m.material.map = null; m.material.color.set(c); m.material.roughness = r; if (n === 'shirt' && team === 'DET') { m.material.metalness = 0.05; } m.material.needsUpdate = true; }
  for (const n of ['hair', 'hairCards']) if (Gx.meshes[n]) Gx.meshes[n].visible = false;   // under the helmet
  // pants: socks below the knee (game pants stop just under it), the Lions' blue-and-black stripe down the lower half of the outer leg
  const KNEEY = wp(Gx.bones.shinL).y, LEGX = Math.abs(wp(Gx.bones.thighL).x);
  { const jm = Gx.meshes.jeans.material, prev = jm.onBeforeCompile, prevKey = jm.customProgramCacheKey ? jm.customProgramCacheKey.bind(jm) : () => '';
    const U = { uSock: { value: lin(K.sock) }, uS1: { value: lin(K.pantStripe ? K.pantStripe[0] : K.pants) }, uS2: { value: lin(K.pantStripe ? K.pantStripe[1] : K.pants) } };
    jm.onBeforeCompile = (sh, r) => { if (prev) prev.call(jm, sh, r); Object.assign(sh.uniforms, U);
      sh.vertexShader = 'varying vec3 vRestK;\n' + sh.vertexShader.replace('#include <begin_vertex>', '#include <begin_vertex>\n vRestK = position;');
      sh.fragmentShader = 'varying vec3 vRestK; uniform vec3 uSock, uS1, uS2;\n' + sh.fragmentShader.replace('#include <map_fragment>', `#include <map_fragment>
        { float y = vRestK.y; float sock = 1.0 - smoothstep(${(KNEEY - 0.055).toFixed(4)}, ${(KNEEY - 0.045).toFixed(4)}, y);
          float out_ = abs(vRestK.x) - ${LEGX.toFixed(4)};   // how far out from the middle of the leg (the stripe runs down the outside)
          float band = smoothstep(${(KNEEY - 0.04).toFixed(4)}, ${(KNEEY - 0.03).toFixed(4)}, y) * (1.0 - smoothstep(${(KNEEY + 0.19).toFixed(4)}, ${(KNEEY + 0.2).toFixed(4)}, y));
          float s1 = band * smoothstep(0.040, 0.046, out_), s2 = band * smoothstep(0.056, 0.062, out_);
          ${K.pantStripe ? 'diffuseColor.rgb = mix(diffuseColor.rgb, uS1, s1); diffuseColor.rgb = mix(diffuseColor.rgb, uS2, s2);' : ''}
          float cuff = (1.0 - sock) * (1.0 - smoothstep(${(KNEEY - 0.045).toFixed(4)}, ${(KNEEY - 0.03).toFixed(4)}, y));
          diffuseColor.rgb = mix(diffuseColor.rgb * (1.0 - 0.25 * cuff), uSock, sock); }`); };
    jm.customProgramCacheKey = () => prevKey() + '|kit' + (K.pantStripe ? 's' : ''); jm.needsUpdate = true; }
  // gloves painted on the hand skin (from 3 cm up the forearm), so nothing can poke through
  { const sk = Gx.meshes.skin_head, ga = sk.geometry.attributes, names = sk.skeleton.bones.map(b => b.name), a = new Float32Array(ga.position.count);
    const WR = {}; for (const S of ['R', 'L']) { const wr = wp(Gx.bones['hand' + S]), el = wp(Gx.bones['farm' + S]); WR[S] = { wr, d: wr.clone().sub(el).normalize() }; }
    const _p = V(0, 0, 0);
    for (let i = 0; i < ga.position.count; i++) { let arm = 0, side = null; for (let k = 0; k < 4; k++) { const w = ga.skinWeight.getComponent(i, k), n = names[ga.skinIndex.getComponent(i, k)];
        if (/^(farm|hand|index|middle|ring|pinky|thumb)/.test(n)) { arm += w; side = n.slice(-1); } }
      let gl = 0; if (arm > 0.3 && side && WR[side]) { _p.set(ga.position.getX(i), ga.position.getY(i), ga.position.getZ(i)); gl = clamp((_p.clone().sub(WR[side].wr).dot(WR[side].d) + 0.03) / 0.02, 0, 1); }
      if (!K.glove) gl = 0;
      if (tattoo && arm > 0.5 && side === 'R') { _p.set(ga.position.getX(i), ga.position.getY(i), ga.position.getZ(i)); const el = wp(Gx.bones.farmR), along = _p.clone().sub(el).dot(WR.R.d), L = WR.R.wr.distanceTo(el);
        if (along > 0.02 && along < L - 0.04) gl = -1; }   // his right forearm: a sleeve tattoo (from the photos)
      a[i] = gl; }
    sk.geometry.setAttribute('aGlove', new THREE.BufferAttribute(a, 1));
    const m = sk.material = sk.material.clone(), old = m.onBeforeCompile, oldKey = m.customProgramCacheKey ? m.customProgramCacheKey.bind(m) : () => '';
    const U = { uGlove: { value: lin(K.glove) } };
    m.onBeforeCompile = (sh, r) => { if (old) old.call(m, sh, r); Object.assign(sh.uniforms, U);
      sh.vertexShader = 'attribute float aGlove; varying float vGlove; varying vec3 vTP;\n' + sh.vertexShader.replace('#include <begin_vertex>', '#include <begin_vertex>\n vGlove = aGlove; vTP = position;');
      sh.fragmentShader = 'varying float vGlove; varying vec3 vTP; uniform vec3 uGlove;\nfloat tH(vec3 p){ p = fract(p * 0.3183099 + 0.1); p *= 17.0; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }\nfloat tN(vec3 x){ vec3 i = floor(x), f = fract(x); f = f*f*(3.0-2.0*f); return mix(mix(mix(tH(i), tH(i+vec3(1,0,0)), f.x), mix(tH(i+vec3(0,1,0)), tH(i+vec3(1,1,0)), f.x), f.y), mix(mix(tH(i+vec3(0,0,1)), tH(i+vec3(1,0,1)), f.x), mix(tH(i+vec3(0,1,1)), tH(i+vec3(1,1,1)), f.x), f.y), f.z); }\n' + sh.fragmentShader
        .replace('#include <map_fragment>', `#include <map_fragment>
          { float gl = smoothstep(0.4, 0.6, vGlove); diffuseColor.rgb = mix(diffuseColor.rgb, uGlove, gl);
            float tt = smoothstep(-0.4, -0.6, vGlove); float n = tN(vTP * 90.0) * 0.6 + tN(vTP * 210.0) * 0.4; float ink = smoothstep(0.42, 0.5, n) * (1.0 - smoothstep(0.6, 0.68, n)) + 0.55 * smoothstep(0.66, 0.72, n);
            diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.03, 0.035, 0.045), tt * clamp(ink, 0.0, 1.0) * 0.85); }`)
        .replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\n roughnessFactor = mix(roughnessFactor, 0.6, smoothstep(0.4, 0.6, vGlove));'); };
    m.customProgramCacheKey = () => oldKey() + '|glove'; m.needsUpdate = true; }
  // the helmet: a shell over the crown, sides and back with a face opening, a centre stripe (Lions), a facemask cage. Built with the opening on +z, then turned to his eyes.
  { const hb = Gx.bones.head, helmet = new THREE.Group();
    const E = wp(Gx.bones.eyeR).add(wp(Gx.bones.eyeL)).multiplyScalar(0.5), fd = E.clone().sub(V(...Gx.man.headC)).setY(0).normalize();
    const hc = E.clone().addScaledVector(fd, -0.07).add(V(0, 0.03, 0)), R0 = 0.142;
    const keep = d => { const az = Math.atan2(d.x, d.z), el = Math.asin(clamp(d.y, -1, 1)), A_ = Math.abs(az);
      const bottom = A_ < 1.6 ? lerp(-0.86, -0.66, sm(clamp((A_ - 0.75) / 0.85, 0, 1))) : lerp(-0.62, -0.42, sm(clamp((A_ - 1.6) / 1.2, 0, 1)));   // jaw guards come down low, the back stops at the skull base
      if (el < bottom) return false;
      if (A_ < 0.78 && el < 0.06) return false;                         // the face opening (up to the brow)
      return true; };
    const shellGeo = (r, filter) => { const sg = new THREE.SphereGeometry(r, 96, 64), pos = sg.attributes.position, idx = sg.index.array, out = [];
      for (let f = 0; f < idx.length; f += 3) { const c = V(0, 0, 0); for (let k = 0; k < 3; k++) c.add(V(pos.getX(idx[f + k]), pos.getY(idx[f + k]), pos.getZ(idx[f + k]))); c.normalize(); if (filter(c)) out.push(idx[f], idx[f + 1], idx[f + 2]); }
      sg.setIndex(out); return sg; };
    const shellM = new THREE.MeshPhysicalMaterial({ color: new THREE.Color(K.helmet).multiplyScalar(team === 'DET' ? 0.82 : 1), roughness: 0.22, clearcoat: 1, clearcoatRoughness: 0.08, metalness: team === 'DET' ? 0.25 : 0.1, side: THREE.DoubleSide });
    const shell = new THREE.Mesh(shellGeo(R0, keep), shellM); shell.scale.set(1.0, 1.06, 1.13); helmet.add(shell);
    const liner = new THREE.Mesh(shellGeo(R0 * 0.93, keep), mat(0x1a1b1e, 0.9)); liner.scale.copy(shell.scale); helmet.add(liner);   // pads inside
    if (K.stripe !== null) { const st = new THREE.Mesh(shellGeo(R0 * 1.004, d => keep(d) && Math.abs(d.x) < 0.07 && d.y > -0.35), new THREE.MeshPhysicalMaterial({ color: K.stripe, roughness: 0.35, clearcoat: 1, side: THREE.DoubleSide })); st.scale.copy(shell.scale); helmet.add(st); }
    // facemask: three bars across and a centre bar, curving back to the jaw guards (round tubes)
    const maskM = new THREE.MeshStandardMaterial({ color: K.mask, roughness: 0.4, metalness: 0.3 });
    const arc = (y, rz, a0, rxz) => { const pts = []; for (let i = 0; i <= 24; i++) { const a = lerp(-a0, a0, i / 24); pts.push(V(Math.sin(a) * rxz, y, Math.cos(a) * rz)); } return pts; };
    const bar = pts => { const t = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 48, 0.0055, 8), maskM); t.castShadow = true; helmet.add(t); };
    const sx = shell.scale;
    for (const [y, rz, a0] of [[-0.012, 0.172, 0.86], [-0.06, 0.178, 0.8], [-0.105, 0.165, 0.74]]) bar(arc(y, rz * sx.z / 1.13, a0, R0 * 1.02));
    bar([V(0, 0.0, R0 * sx.z * 0.98), V(0, -0.012, 0.172 * sx.z / 1.13), V(0, -0.06, 0.178 * sx.z / 1.13), V(0, -0.105, 0.165 * sx.z / 1.13)]);
    for (const s of [-1, 1]) bar([V(s * Math.sin(0.5) * R0 * 1.02, -0.012, Math.cos(0.5) * 0.172 * sx.z / 1.13), V(s * Math.sin(0.48) * R0 * 1.02, -0.06, Math.cos(0.48) * 0.178 * sx.z / 1.13), V(s * Math.sin(0.44) * R0 * 1.02, -0.105, Math.cos(0.44) * 0.165 * sx.z / 1.13)]);
    // chin strap and cup (white)
    const cup = new THREE.Mesh(new THREE.SphereGeometry(0.03, 16, 10, 0, Math.PI * 2, 0, Math.PI * 0.55), mat(0xf0f0ea, 0.4)); cup.rotation.x = Math.PI * 0.62; cup.scale.set(1.3, 1, 0.8); cup.position.set(0, -0.168, 0.062); cup.visible = false; helmet.add(cup);
    helmet.rotation.y = Math.atan2(fd.x, fd.z); helmet.position.copy(hc); hb.updateMatrixWorld(true); helmet.applyMatrix4(hb.matrixWorld.clone().invert()); hb.add(helmet);
    helmet.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } }); P.helmet = helmet; P.helmetShell = shell; }
  // shoulder pads under the jersey: the jersey itself is pushed out over the chest, back and shoulders (3-6 cm, thinning to nothing at the edges) in its
  // rest pose, so it stays one skinned cloth that bends with him (a rigid shell crumpled and gapped when his arms went up). The numbers, the name on the
  // back and the shoulder stripes are painted on it in rest-pose space.
  { const sh = Gx.meshes.shirt, g0 = sh.geometry, ga = g0.attributes, names = sh.skeleton.bones.map(b => b.name), N = ga.position.count;
    const chestY = wp(Gx.bones.chest).y, neckY = wp(Gx.bones.neck).y, shY = wp(Gx.bones.uarmR).y, yLow = chestY - 0.07, shX = Math.abs(wp(Gx.bones.uarmR).x);
    const pos = ga.position.clone(), rest = ga.position.clone(), nrm = ga.normal, rn = ga.normal.clone();
    for (let i = 0; i < N; i++) { let c = 0; for (let k = 0; k < 4; k++) { const n = names[ga.skinIndex.getComponent(i, k)]; if (/^(chest|clav|neck|spine2)/.test(n)) c += ga.skinWeight.getComponent(i, k); }
      const y = ga.position.getY(i), x = ga.position.getX(i);
      const t = sm(clamp((c - 0.25) / 0.45, 0, 1)) * sm(clamp((y - yLow) / 0.08, 0, 1)) * (1 - 0.35 * sm(clamp((Math.abs(x) - shX + 0.02) / 0.06, 0, 1)));
      const capn = sm(clamp((Math.abs(x) - shX + 0.12) / 0.1, 0, 1)) * sm(clamp((y - shY + 0.08) / 0.08, 0, 1));   // the shoulder caps
      const collar = 1 - sm(clamp((y - neckY + 0.1) / 0.07, 0, 1)) * (1 - capn);   // the neckline stays snug (pushed out it opened a gap round his neck)
      const off = (0.03 + 0.028 * capn) * t * collar, up = (0.01 + 0.025 * capn) * t * collar * sm(clamp((y - chestY) / 0.12, 0, 1)), outx = 0.025 * capn * t * Math.sign(x);
      pos.setXYZ(i, x + nrm.getX(i) * off + outx, y + nrm.getY(i) * off + up, ga.position.getZ(i) + nrm.getZ(i) * off); }
    g0.setAttribute('position', pos); g0.setAttribute('aRest', rest); g0.setAttribute('aRN', rn); g0.computeVertexNormals(); g0.computeBoundingSphere();
    const numT = numberTex(number, K), nmT = nameTex(name, K), cb = wp(Gx.bones.chest);
    const pm = sh.material, prev = pm.onBeforeCompile, prevKey = pm.customProgramCacheKey ? pm.customProgramCacheKey.bind(pm) : () => '';
    pm.roughness = 0.62; if (pm.isMeshPhysicalMaterial) { pm.sheen = 0.3; pm.sheenColor = new THREE.Color(0xffffff); }
    const U = { uNum: { value: numT }, uName: { value: nmT }, uC1: { value: lin(K.cap ? K.cap[0] : K.jersey) }, uC2: { value: lin(K.cap ? K.cap[1] : K.jersey) } };
    pm.onBeforeCompile = (s, r) => { if (prev) prev.call(pm, s, r); Object.assign(s.uniforms, U);
      s.vertexShader = 'attribute vec3 aRest; attribute vec3 aRN; varying vec3 vR; varying vec3 vRN;\n' + s.vertexShader.replace('#include <begin_vertex>', '#include <begin_vertex>\n vR = aRest; vRN = aRN;');
      s.fragmentShader = 'varying vec3 vR; varying vec3 vRN; uniform sampler2D uNum, uName; uniform vec3 uC1, uC2;\n' + s.fragmentShader.replace('#include <map_fragment>', `#include <map_fragment>
        { vec3 n = normalize(vRN); float cx = ${cb.x.toFixed(4)};
          ${K.cap ? `float ax = abs(vR.x), top_ = smoothstep(${(shY - 0.07).toFixed(4)}, ${(shY - 0.045).toFixed(4)}, vR.y) * smoothstep(0.35, 0.6, n.y);   // two stripes over the top of each shoulder, front to back
          float s1 = top_ * smoothstep(${(shX - 0.075).toFixed(4)}, ${(shX - 0.07).toFixed(4)}, ax) * (1.0 - smoothstep(${(shX - 0.045).toFixed(4)}, ${(shX - 0.04).toFixed(4)}, ax));
          float s2 = top_ * smoothstep(${(shX - 0.038).toFixed(4)}, ${(shX - 0.033).toFixed(4)}, ax) * (1.0 - smoothstep(${(shX - 0.022).toFixed(4)}, ${(shX - 0.017).toFixed(4)}, ax));
          diffuseColor.rgb = mix(diffuseColor.rgb, uC1, s1); diffuseColor.rgb = mix(diffuseColor.rgb, uC2, s2);` : ''}
          // numbers on the front and back (22 cm tall, under the collar); at rest he faces -z
          vec2 uv; float front = smoothstep(0.25, 0.45, -n.z), back = smoothstep(0.25, 0.45, n.z);
          float W = 0.30, H = 0.225, top = ${(neckY - 0.07).toFixed(4)};
          float tp = back > 0.0 ? top - 0.085 : top;
          uv = vec2((vR.x - cx) / W * (back > 0.0 ? 1.0 : -1.0) + 0.5, 1.0 - (tp - vR.y) / H * 0.82 - 0.09);
          vec4 nc = texture2D(uNum, uv); float inside = step(0.0, uv.x) * step(uv.x, 1.0) * step(0.0, uv.y) * step(uv.y, 1.0);
          float a = nc.a * inside * max(front, back); diffuseColor.rgb = mix(diffuseColor.rgb, nc.rgb, a);
          vec2 uvn = vec2((vR.x - cx) / 0.34 + 0.5, (vR.y - (tp + 0.012)) / 0.055); vec4 nn = texture2D(uName, uvn);   // the name across the upper back, above the number
          float inn = step(0.0, uvn.x) * step(uvn.x, 1.0) * step(0.0, uvn.y) * step(uvn.y, 1.0); diffuseColor.rgb = mix(diffuseColor.rgb, nn.rgb, nn.a * inn * back); }`); };
    pm.customProgramCacheKey = () => prevKey() + '|jersey' + team; pm.needsUpdate = true; P.pads = sh; }
  PLAYERS.push(P); return P; }
const CAMP = suitUp(G, 'DET', 46, 'CAMPBELL'), ONEIL = suitUp(K_O, 'DET', 66, "O'NEILL"), HOCK = suitUp(K_H, 'MIN', 87, 'HOCKENSON', true);
G.reset(); G.root.updateMatrixWorld(true);
// the football: a prolate spheroid, brown leather, white laces
const ball = new THREE.Group(); scene.add(ball);
{ const g = new THREE.SphereGeometry(1, 40, 24); g.scale(0.085, 0.085, 0.142); const pa = g.attributes.position;
  for (let i = 0; i < pa.count; i++) { const z = pa.getZ(i) / 0.142, k = Math.pow(1 - z * z, 0.12); pa.setX(i, pa.getX(i) * k); pa.setY(i, pa.getY(i) * k); } g.computeVertexNormals();
  const bm = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ color: 0x6a3418, roughness: 0.55 })); bm.castShadow = true; ball.add(bm);
  for (let i = -3; i <= 4; i++) { const l = box(0.028, 0.006, 0.006, 0, 0.083, i * 0.012, mat(0xf4f0e6, 0.6), 0, ball); }
  box(0.004, 0.006, 0.1, 0, 0.083, 0.005, mat(0xf4f0e6, 0.6), 0, ball); }
// readout (same look as the other news Shorts)
const hudC = document.createElement('canvas'); hudC.width = 520; hudC.height = 440; const hudT = new THREE.CanvasTexture(hudC); hudT.colorSpace = THREE.SRGBColorSpace;
const hud = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: hudT, transparent: true, depthTest: false, depthWrite: false, toneMapped: false })); hud.renderOrder = 30; camera.add(hud); scene.add(camera); hud.visible = false;
function drawHud(rows, flag) { const g = hudC.getContext('2d'); g.clearRect(0, 0, 520, 440); g.beginPath(); g.roundRect(6, 6, 508, 428, 34); g.fillStyle = 'rgba(8,14,22,0.74)'; g.fill(); g.lineWidth = 4; g.strokeStyle = 'rgba(160,200,235,0.55)'; g.stroke();
  let y = 30; for (const [lab, val, col] of rows) { g.fillStyle = '#9fb6c8'; g.font = '600 34px Arial, Helvetica, sans-serif'; g.fillText(lab, 34, y + 38); g.fillStyle = col || '#fff'; g.font = 'bold 62px Arial, Helvetica, sans-serif'; g.fillText(val, 34, y + 102, 452); y += 120; }
  if (flag) { g.font = 'bold 52px Arial, Helvetica, sans-serif'; const fw = Math.min(460, g.measureText(flag).width + 40); g.beginPath(); g.roundRect(30, 340, fw, 76, 16); g.fillStyle = flag.startsWith('+') ? '#1f9d55' : '#d9241b'; g.fill(); g.fillStyle = '#fff'; g.fillText(flag.replace(/^\+/, ''), 50, 397, fw - 40); }
  hudT.needsUpdate = true; }
function fitHud() { const d = camera.near * 1.6, h = 2 * d * Math.tan(camera.fov * D2R / 2), w = h * camera.aspect, gw = 0.4 * w, gh = gw * 440 / 520; hud.scale.set(gw, gh, 1); hud.position.set(w / 2 - gw / 2 - 0.035 * w, h / 2 - 0.165 * h - gh / 2, -d); }
