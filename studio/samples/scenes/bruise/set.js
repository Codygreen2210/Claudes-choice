
// ------------------------------------------------------------------ the room: he stands by a coffee table (beats 7, 0, 3, 4, 6); his jeans are shorts today
const STANDP = V(0.35, 0, -0.35);                                   // where he stands (he faces +z, the back wall behind him)
G.reset(); G.root.updateMatrixWorld(true);
const KNEEY = wp(G.bones.shinL).y, HEMY = KNEEY + 0.07;
// shorts: the jeans below the hem draw as bare skin; up to five bruises painted on the skin (rest-pose positions)
const BU = { uBS: { value: [0, 1, 2, 3, 4].map(() => new THREE.Vector4(0, -5, 0, 0.03)) }, uBC: { value: [0, 1, 2, 3, 4].map(() => new THREE.Color(0x5a2a5a)) },
  uBA: { value: [0, 0, 0, 0, 0] }, uSkin: { value: new THREE.Color(0xd99a7c) } };
{ const jm = G.meshes.jeans.material, prev = jm.onBeforeCompile, prevKey = jm.customProgramCacheKey ? jm.customProgramCacheKey.bind(jm) : () => '';
  jm.onBeforeCompile = (sh, r) => { prev.call(jm, sh, r); Object.assign(sh.uniforms, BU);
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nuniform vec4 uBS[5]; uniform vec3 uBC[5]; uniform float uBA[5]; uniform vec3 uSkin;')
      .replace('dH_denim = h * fade; }', `dH_denim = h * fade; }
  { float leg = 1.0 - smoothstep(${(HEMY - 0.003).toFixed(4)}, ${(HEMY + 0.003).toFixed(4)}, vRestD.y);
    float cuff = (1.0 - leg) * (1.0 - smoothstep(${(HEMY + 0.028).toFixed(4)}, ${(HEMY + 0.032).toFixed(4)}, vRestD.y)); diffuseColor.rgb *= 1.0 - 0.18 * cuff;
    vec3 c = uSkin * (1.0 + 0.05 * (nG(vRestD * 140.0) - 0.5));
    for (int i = 0; i < 5; i++) { float d = length((vRestD - uBS[i].xyz) / vec3(1.0, 1.35, 1.0)) / uBS[i].w; float n = nG(vRestD * 70.0 + float(i) * 3.1);
      float a = uBA[i] * (1.0 - smoothstep(0.3, 1.0, d + 0.35 * (n - 0.5))); c = mix(c, uBC[i] * (0.85 + 0.3 * n), clamp(a, 0.0, 1.0)); }
    diffuseColor.rgb = mix(diffuseColor.rgb, c, leg); dH_denim *= 1.0 - leg; }`); };
  jm.customProgramCacheKey = () => prevKey() + '|shorts'; jm.needsUpdate = true; }
// the main bruise: the front of his left shin; find the skin vertex there (to aim the camera at it as he moves)
const JG = G.meshes.jeans.geometry.attributes.position;
const BRV = (() => { const sx = wp(G.bones.shinL).x, yc = KNEEY - 0.13; let best = -1, bz = 1e9;
  for (let i = 0; i < JG.count; i++) { const x = JG.getX(i), y = JG.getY(i), z = JG.getZ(i); if (Math.abs(y - yc) < 0.012 && Math.abs(x - sx) < 0.03 && z < bz) { bz = z; best = i; } } return best; })();
const BR0 = V(JG.getX(BRV), JG.getY(BRV), JG.getZ(BRV));
BU.uBS.value[0].set(BR0.x, BR0.y, BR0.z, 0.045);
// more bruises (beats 4 and 6): the other shin, his left knee, his right calf side
{ const sxR = wp(G.bones.shinR).x; const near = (xc, yc, pick) => { let best = 0, bv = 1e9; for (let i = 0; i < JG.count; i++) { const x = JG.getX(i), y = JG.getY(i), z = JG.getZ(i); if (Math.abs(y - yc) < 0.012 && Math.abs(x - xc) < 0.04) { const s = pick(x, z); if (s < bv) { bv = s; best = i; } } } return V(JG.getX(best), JG.getY(best), JG.getZ(best)); };
  const a = near(sxR, KNEEY - 0.2, (x, z) => z), b = near(wp(G.bones.shinL).x, KNEEY - 0.01, (x, z) => z), c = near(sxR, KNEEY - 0.08, (x, z) => -x + 0.5 * z), d = near(wp(G.bones.shinL).x, KNEEY - 0.27, (x, z) => -x);
  BU.uBS.value[1].set(a.x, a.y, a.z, 0.035); BU.uBS.value[2].set(b.x, b.y, b.z, 0.03); BU.uBS.value[3].set(c.x, c.y, c.z, 0.04); BU.uBS.value[4].set(d.x, d.y, d.z, 0.03); }
function bruiseW() { const m = G.meshes.jeans, a = BR0.clone(); m.applyBoneTransform(BRV, a); return a.applyMatrix4(m.matrixWorld); }
const BCOL = { red: new THREE.Color(0xa01c26), blue: new THREE.Color(0x3a3a8a), purple: new THREE.Color(0x5a2660), green: new THREE.Color(0x7d9040), yellow: new THREE.Color(0xc8a848) };
function bruiseCol(k) {                                             // 0 fresh red .. 1 blue .. 2 purple .. 3 green .. 4 yellow
  const st = [BCOL.red, BCOL.blue, BCOL.purple, BCOL.green, BCOL.yellow], i = Math.min(3, Math.floor(k)), f = k - i; return st[i].clone().lerp(st[i + 1], Math.min(1, f)); }

// the coffee table (placed in the tail so its edge is right where his shin swings)
const woodM = new THREE.MeshStandardMaterial({ map: canvasTex(512, 256, g => { g.fillStyle = '#7a4a2a'; g.fillRect(0, 0, 512, 256); for (let i = 0; i < 70; i++) { g.strokeStyle = `rgba(${40 + Math.random() * 30},20,10,${0.15 + Math.random() * 0.2})`; g.lineWidth = 1 + Math.random() * 2; g.beginPath(); const y = Math.random() * 256; g.moveTo(0, y); g.bezierCurveTo(170, y + 8 * Math.random() - 4, 340, y - 6, 512, y + 4 * Math.random()); g.stroke(); } }), roughness: 0.45 });
const TOPY = 0.42;
const ctable = new THREE.Group(); home.add(ctable);
box(1.0, 0.045, 0.55, 0, TOPY - 0.0225, 0.275, woodM, 0.012, ctable);
for (const [x, z] of [[-0.45, 0.05], [0.45, 0.05], [-0.45, 0.5], [0.45, 0.5]]) box(0.05, TOPY - 0.045, 0.05, x, (TOPY - 0.045) / 2, z, woodM, 0.01, ctable);
box(0.92, 0.025, 0.47, 0, 0.12, 0.275, woodM, 0.008, ctable);                 // the shelf below
// on the table: a mug, a remote; and (beat 6) two pill bottles
{ const mug = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.036, 0.095, 24), mat(0xe8e2d4, 0.4)); mug.position.set(-0.3, TOPY + 0.0475, 0.33); ctable.add(mug);
  box(0.05, 0.02, 0.17, 0.25, TOPY + 0.01, 0.38, mat(0x222226, 0.5), 0.006, ctable); }
const bottleT = (txt, sub, col) => canvasTex(512, 256, g => { g.fillStyle = '#f4f2ec'; g.fillRect(0, 0, 512, 256); g.fillStyle = col; g.fillRect(0, 36, 512, 120); g.fillStyle = '#fff'; g.font = 'bold 54px sans-serif'; g.textAlign = 'center'; g.fillText(txt, 256, 122); g.fillStyle = '#333'; g.font = 'bold 36px sans-serif'; g.fillText(sub, 256, 208); });
const PILLS = new THREE.Group(); ctable.add(PILLS); PILLS.visible = false;
for (const [x, z, txt, sub, col, h] of [[0.02, 0.2, 'ASPIRIN', '325 mg TABLETS', '#c8202a', 0.11], [0.17, 0.25, 'BLOOD', 'THINNER', '#2a5ab0', 0.13]]) {
  const b = new THREE.Mesh(new THREE.CylinderGeometry(0.034, 0.034, h, 32, 1, true), new THREE.MeshStandardMaterial({ map: bottleT(txt, sub, col), roughness: 0.5 })); b.position.set(x, TOPY + h / 2, z); b.rotation.y = -2.46; PILLS.add(b);
  const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.037, 0.037, 0.025, 32), mat(0xf6f6f2, 0.4)); cap.position.set(x, TOPY + h + 0.0125, z); PILLS.add(cap);
  const bot = new THREE.Mesh(new THREE.CircleGeometry(0.034, 24).rotateX(Math.PI / 2), mat(0xf4f2ec, 0.5)); bot.position.set(x, TOPY + 0.001, z); PILLS.add(bot);
  if (x < 0.1) for (let j = 0; j < 4; j++) { const p = new THREE.Mesh(new THREE.SphereGeometry(0.008, 12, 8), mat(0xf8f6f0, 0.5)); p.scale.y = 0.45; p.position.set(-0.06 + j * 0.022, TOPY + 0.004, 0.13 + (j % 2) * 0.02); PILLS.add(p); } }

// his phone (beats 7 and 0: he walks into the table reading it)
const phone = new THREE.Group(); scene.add(phone);
const phoneCanvas = document.createElement('canvas'); phoneCanvas.width = 360; phoneCanvas.height = 760;
const phoneTex = new THREE.CanvasTexture(phoneCanvas); phoneTex.colorSpace = THREE.SRGBColorSpace;
{ const pg = phoneCanvas.getContext('2d'); pg.fillStyle = '#101418'; pg.fillRect(0, 0, 360, 760);
  for (let i = 0; i < 6; i++) { pg.fillStyle = ['#2a3a4a', '#3a2a3a', '#2a4a3a'][i % 3]; pg.fillRect(20, 40 + i * 120, 320, 100); pg.fillStyle = '#c8d0d8'; pg.fillRect(34, 60 + i * 120, 200, 14); pg.fillRect(34, 86 + i * 120, 150, 10); } phoneTex.needsUpdate = true; }
{ const body = new THREE.Mesh(new THREE.BoxGeometry(0.072, 0.15, 0.008), mat(0x1a1a1e, 0.35, 0.4)); phone.add(body);
  const scr = new THREE.Mesh(new THREE.PlaneGeometry(0.066, 0.142), new THREE.MeshBasicMaterial({ map: phoneTex, toneMapped: false })); scr.position.z = 0.0041; phone.add(scr); }

// ------------------------------------------------------------------ the skin up close (a dark stage): skin, the layer under it, fat, muscle; tiny blood vessels
const MS = V(40, 0, 0);
const skinSet = new THREE.Group(); skinSet.position.copy(MS); scene.add(skinSet);
const msLight = new THREE.PointLight(0xfff0e8, 0, 6, 1.2); msLight.position.set(0.5, 1.9, 1.4); skinSet.add(msLight);
const msFill = new THREE.PointLight(0xffd8c8, 0, 5, 1.2); msFill.position.set(-0.8, 1.2, 1.2); skinSet.add(msFill);
skinSet.add(new THREE.Mesh(new THREE.SphereGeometry(5, 24, 12), new THREE.MeshBasicMaterial({ color: 0x120a0c, side: THREE.BackSide })));
const SKTOP = 1.25, SKW = 1.0, SKD = 0.6;                            // top of the skin; width (x), depth (z); the cut face is at z = +SKD/2
const LAY = new THREE.Group(); skinSet.add(LAY);
const layM = (c, r = 0.7) => new THREE.MeshStandardMaterial({ color: c, roughness: r });
const EPI = new THREE.Mesh(new THREE.BoxGeometry(SKW, 1, SKD), layM(0xd99a7c, 0.55)); LAY.add(EPI);
const DER = new THREE.Mesh(new THREE.BoxGeometry(SKW, 1, SKD), layM(0xe6908a)); LAY.add(DER);
const FAT = new THREE.Mesh(new THREE.BoxGeometry(SKW, 1, SKD), layM(0xf0cf72, 0.6)); LAY.add(FAT);
const MUS = new THREE.Mesh(new THREE.BoxGeometry(SKW, 0.8, SKD), new THREE.MeshStandardMaterial({ map: canvasTex(256, 128, g => { g.fillStyle = '#8a2228'; g.fillRect(0, 0, 256, 128); for (let i = 0; i < 26; i++) { g.strokeStyle = `rgba(${170 + Math.random() * 40},60,60,0.5)`; g.lineWidth = 2; g.beginPath(); const y = i * 5 + Math.random() * 3; g.moveTo(0, y); g.lineTo(256, y + 2); g.stroke(); } }), roughness: 0.6 })); LAY.add(MUS);
const FATB = []; for (let i = 0; i < 9; i++) { const s = new THREE.Mesh(new THREE.SphereGeometry(0.06, 20, 14), layM(0xf6dc86, 0.5)); s.userData.x = -0.44 + i * 0.11; s.userData.r = hash1(i * 4.1); LAY.add(s); FATB.push(s); }
// the vessels: tubes running across, lying in the cut face; the one under the hit has a middle piece that breaks
const vesM2 = new THREE.MeshStandardMaterial({ color: 0xc81e2a, emissive: 0x400408, roughness: 0.4 }), veinM2 = new THREE.MeshStandardMaterial({ color: 0x5a4aa8, roughness: 0.4 });
const VES = [];
for (const [fy, r, m, ph] of [[0.25, 0.011, vesM2, 0.3], [0.55, 0.016, vesM2, 1.7], [0.8, 0.022, veinM2, 2.9]]) {         // fy: depth as a fraction of the under-layer
  const parts = []; for (const [x0, x1] of [[-0.5, -0.06], [-0.06, 0.06], [0.06, 0.5]]) {
    const pts = []; for (let j = 0; j <= 12; j++) { const x = x0 + (x1 - x0) * j / 12; pts.push(V(x, 0.012 * Math.sin(x * 9 + ph), 0)); }
    const t = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 24, r, 10), m); LAY.add(t); parts.push(t); }
  VES.push({ fy, r, parts }); }
// leaked blood: a stain spreading in the cut face, the same spot seen through the skin on top, and drops
const poolM = new THREE.MeshBasicMaterial({ color: 0xa01c26, transparent: true, opacity: 0, depthWrite: false });
poolM.alphaMap = canvasTex(256, 256, g => { const gr = g.createRadialGradient(128, 128, 30, 128, 128, 128); gr.addColorStop(0, '#fff'); gr.addColorStop(0.7, '#ddd'); gr.addColorStop(1, '#000'); g.fillStyle = gr; g.fillRect(0, 0, 256, 256); });
const POOL = new THREE.Mesh(new THREE.CircleGeometry(1, 48), poolM); POOL.renderOrder = 3; LAY.add(POOL);
const topM = new THREE.MeshStandardMaterial({ color: 0xa01c26, transparent: true, opacity: 0, depthWrite: false, roughness: 0.6, map: canvasTex(256, 256, g => { const gr = g.createRadialGradient(128, 128, 10, 128, 128, 128); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.55, 'rgba(255,255,255,0.8)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 256, 256); }) });
topM.alphaMap = topM.map; const TOPSPOT = new THREE.Mesh(new THREE.PlaneGeometry(0.5, 0.36).rotateX(-Math.PI / 2), topM); TOPSPOT.position.set(0, SKTOP + 0.0015, 0.06); TOPSPOT.renderOrder = 3; skinSet.add(TOPSPOT);
const BLOOD = (() => { const g = new THREE.BufferGeometry(), n = 160, p = new Float32Array(n * 3); g.setAttribute('position', new THREE.BufferAttribute(p, 3)); g.setDrawRange(0, 0);
  const m = new THREE.Points(g, new THREE.PointsMaterial({ color: 0xb01828, size: 0.028, map: dotTex0(), transparent: true, depthWrite: false, toneMapped: false })); m.frustumCulled = false; m.renderOrder = 4; scene.add(m); return { m, p, n }; })();
function dotTex0() { return canvasTex(64, 64, g => { const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.5, 'rgba(255,255,255,0.9)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); }); }
// the hit: a table edge comes down on the skin
const EDGE = new THREE.Mesh(new RoundedBoxGeometry(0.34, 0.16, SKD + 0.1, 3, 0.03), woodM); skinSet.add(EDGE);
// layer thickness (beat 5: older skin is thinner, less padding)
function setLayers(thin) { const e = 0.04 * (1 - 0.4 * thin), d = 0.22 * (1 - 0.55 * thin), f = 0.26 * (1 - 0.65 * thin); let y = SKTOP;
  EPI.scale.y = e; EPI.position.y = y - e / 2; y -= e; DER.scale.y = d; DER.position.y = y - d / 2; const dTop = y; y -= d;
  FAT.scale.y = f; FAT.position.y = y - f / 2; for (const s of FATB) { s.position.set(s.userData.x, y - f * (0.3 + 0.4 * s.userData.r), SKD / 2 - 0.045); s.scale.set(1, Math.max(0.2, f / 0.26), 1); } y -= f;
  MUS.position.y = y - 0.4;
  for (const v of VES) for (const p of v.parts) p.position.set(0, dTop - d * v.fy, SKD / 2 - 0.004);
  return { dTop, d }; }
let LAYNOW = setLayers(0);
let XRNEW = false;
