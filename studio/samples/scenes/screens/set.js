// ------------------------------------------------------------------ the living room + a right wall with the TV on it; his phone (a live camera view); the close-up sets
const STANDP = V(1.15, 0, 0.0);                                    // where he stands, facing +x (the TV on the right wall)
box(0.12, 3.2, 12, 3.3, 1.6, 0, mat(0xd9e2d6, 0.9), 0, home);      // a right wall for the TV
box(0.04, 0.12, 12, 3.22, 0.06, 0, mat(0xf4efe4, 0.6), 0, home);
// the TV picture: a made-up cartoon show (a beach at sunset); no logos
const PIC = canvasTex(512, 288, g => {
  const sk = g.createLinearGradient(0, 0, 0, 175); sk.addColorStop(0, '#6a3fa0'); sk.addColorStop(0.45, '#ff7a59'); sk.addColorStop(1, '#ffd27a'); g.fillStyle = sk; g.fillRect(0, 0, 512, 176);
  const sg = g.createRadialGradient(330, 150, 10, 330, 150, 110); sg.addColorStop(0, 'rgba(255,250,210,1)'); sg.addColorStop(0.35, 'rgba(255,230,150,0.9)'); sg.addColorStop(1, 'rgba(255,200,120,0)');
  g.fillStyle = sg; g.fillRect(200, 40, 260, 140); g.fillStyle = '#fff6cf'; g.beginPath(); g.arc(330, 150, 42, 0, Math.PI * 2); g.fill();
  const se = g.createLinearGradient(0, 172, 0, 288); se.addColorStop(0, '#2f8fc0'); se.addColorStop(1, '#123e66'); g.fillStyle = se; g.fillRect(0, 172, 512, 116);
  g.fillStyle = 'rgba(255,230,160,0.8)'; for (let i = 0; i < 9; i++) { const w = 70 - i * 6; g.fillRect(330 - w / 2 + (i % 2) * 6, 180 + i * 9, w, 3); }
  g.fillStyle = '#e8c27a'; g.beginPath(); g.moveTo(0, 230); g.quadraticCurveTo(150, 205, 260, 288); g.lineTo(0, 288); g.fill();
  g.strokeStyle = '#3a2216'; g.lineWidth = 9; g.lineCap = 'round'; g.beginPath(); g.moveTo(70, 260); g.quadraticCurveTo(95, 160, 80, 70); g.stroke();
  g.fillStyle = '#1f5a2a'; for (const [a, l] of [[-2.6, 70], [-2.2, 80], [-1.4, 75], [-0.6, 78], [-0.2, 66], [0.5, 60]]) { g.beginPath(); g.moveTo(80, 70);
    g.quadraticCurveTo(80 + Math.cos(a) * l * 0.6, 70 + Math.sin(a) * l * 0.6 - 18, 80 + Math.cos(a) * l, 70 + Math.sin(a) * l + 10); g.quadraticCurveTo(80 + Math.cos(a) * l * 0.5, 70 + Math.sin(a) * l * 0.5, 80, 74); g.fill(); }
  g.fillStyle = '#2a1a2a'; g.beginPath(); g.moveTo(420, 170); g.lineTo(470, 170); g.lineTo(462, 178); g.lineTo(428, 178); g.fill(); g.fillRect(443, 128, 3, 42);
  g.beginPath(); g.moveTo(447, 130); g.lineTo(447, 166); g.lineTo(470, 166); g.fill();
  g.strokeStyle = '#2a1a2a'; g.lineWidth = 2.5; for (const [x, y] of [[200, 70], [222, 84], [180, 92]]) { g.beginPath(); g.moveTo(x - 9, y - 3); g.quadraticCurveTo(x - 4, y - 7, x, y); g.quadraticCurveTo(x + 4, y - 7, x + 9, y - 3); g.stroke(); } });
PIC.anisotropy = 8;
const VERT = `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`;
// the TV: its screen up close is a grid of tiny red, green and blue bars (only drawn once they are big enough to see, or they alias)
const tvU = { pic: { value: PIC }, res: { value: new THREE.Vector2(1920, 1080) }, on: { value: 1 }, bright: { value: 1.25 }, macro: { value: 0 } };
const tvMat = new THREE.ShaderMaterial({ uniforms: tvU, vertexShader: VERT, toneMapped: false, fragmentShader: `uniform sampler2D pic; uniform vec2 res; uniform float on, bright, macro; varying vec2 vUv;
  void main(){ vec2 c = vUv * res, ci = floor(c), f = fract(c); vec3 p = texture2D(pic, (ci + 0.5) / res).rgb, avg = texture2D(pic, vUv).rgb;
    float sx = f.x * 3.0, k = floor(sx), fx = fract(sx);
    float st = smoothstep(0.1, 0.24, fx) * smoothstep(0.9, 0.76, fx) * smoothstep(0.07, 0.2, f.y) * smoothstep(0.93, 0.8, f.y);
    vec3 ch = k < 0.5 ? vec3(1.0, 0.0, 0.0) : (k < 1.5 ? vec3(0.0, 1.0, 0.0) : vec3(0.0, 0.0, 1.0));
    vec3 sub = ch * (0.08 + 1.1 * dot(p, ch)) * st * 2.4;
    float fw = max(fwidth(c.x), fwidth(c.y)), m = macro * smoothstep(0.28, 0.1, fw);
    gl_FragColor = vec4(mix(avg, sub, m) * bright * on, 1.0);
    #include <colorspace_fragment>
  }` });
const TVP = V(3.2, 1.22, 0.0);                                     // the screen's centre (it faces -x)
const tv = new THREE.Group(); tv.position.copy(TVP); tv.rotation.y = -Math.PI / 2; home.add(tv);
box(1.16, 0.7, 0.05, 0, 0, -0.03, mat(0x111216, 0.35, 0.4), 0.01, tv);
const tvScreen = new THREE.Mesh(new THREE.PlaneGeometry(1.1, 0.62), tvMat); tvScreen.position.z = 0.0; tv.add(tvScreen);
{ const con = new THREE.Group(); con.position.set(3.0, 0, 0); con.rotation.y = -Math.PI / 2; home.add(con);
  box(1.5, 0.48, 0.42, 0, 0.24, 0, mat(0x6a4a34, 0.7), 0.02, con); box(1.46, 0.02, 0.38, 0, 0.18, 0.012, mat(0x4a3224, 0.8), 0, con);
  box(0.22, 0.16, 0.16, -0.5, 0.56, 0, mat(0x2a6a5a, 0.6), 0.03, con); box(0.12, 0.2, 0.12, 0.55, 0.58, 0.02, mat(0xe8d8b0, 0.7), 0.02, con); }
const tvLight = new THREE.PointLight(0x9ac8ff, 0, 4, 1.5); tvLight.position.set(2.85, 1.22, 0); scene.add(tvLight);

// his phone: what its camera sees (the TV picture, zoomed in) + rainbow waves + rolling dark bars + REC
const UI = canvasTex(256, 568, g => { g.fillStyle = 'rgba(0,0,0,0.35)'; g.fillRect(0, 0, 256, 44); g.fillStyle = '#ff3b30'; g.beginPath(); g.arc(26, 22, 9, 0, Math.PI * 2); g.fill();
  g.fillStyle = '#fff'; g.font = 'bold 22px Arial'; g.fillText('REC', 44, 30); g.strokeStyle = 'rgba(255,255,255,0.8)'; g.lineWidth = 3;
  for (const [x, y, dx, dy] of [[20, 70, 1, 1], [236, 70, -1, 1], [20, 470, 1, -1], [236, 470, -1, -1]]) { g.beginPath(); g.moveTo(x, y + dy * 26); g.lineTo(x, y); g.lineTo(x + dx * 26, y); g.stroke(); }
  g.fillStyle = 'rgba(0,0,0,0.35)'; g.fillRect(0, 500, 256, 68); g.strokeStyle = '#fff'; g.lineWidth = 4; g.beginPath(); g.arc(128, 534, 24, 0, Math.PI * 2); g.stroke();
  g.fillStyle = '#ff3b30'; g.beginPath(); g.roundRect(116, 522, 24, 24, 5); g.fill(); });
const phU = { pic: { value: PIC }, ui: { value: UI }, t: { value: 0 }, wave: { value: 1 }, bars: { value: 0 }, th: { value: 0.5 }, flip: { value: 0 } };
const phMat = new THREE.ShaderMaterial({ uniforms: phU, vertexShader: VERT, toneMapped: false, fragmentShader: `uniform sampler2D pic, ui; uniform float t, wave, bars, th, flip; varying vec2 vUv;
  void main(){ vec2 uv = flip > 0.5 ? 1.0 - vUv : vUv;
    vec2 pu = vec2(0.30 + uv.x * 0.42, 0.06 + uv.y * 0.9);           // the camera's view: the middle of the TV picture, zoomed in
    vec3 col = texture2D(pic, pu).rgb;
    vec2 q = vec2(uv.x * 0.45, uv.y) * 5.0;                           // moire: curvy stripes that crawl as his hand shakes
    q += 0.09 * vec2(sin(q.y * 1.7 + t * 0.9), sin(q.x * 2.3 - t * 0.7));
    float ph = 2.6 * (q.x * cos(th) + q.y * sin(th)) + 0.55 * sin(length(q - vec2(1.2, 2.8)) * 1.9 - t * 1.4) + 0.4 * t;
    vec3 rb = 0.5 + 0.5 * cos(6.2832 * (ph * 0.5 + vec3(0.0, 0.33, 0.67)));
    float dk = 0.5 + 0.5 * cos(6.2832 * ph);
    vec3 w = col * (0.42 + 0.85 * dk) * mix(vec3(1.0), 0.35 + 1.3 * rb, 0.7);
    col = mix(col, w, wave);
    float yb = fract(uv.y * 3.0 - t * 0.6), bar = smoothstep(0.0, 0.035, yb) * (1.0 - smoothstep(0.26, 0.3, yb));   // rolling dark bars
    col *= 1.0 - bars * 0.9 * bar;
    vec4 u = texture2D(ui, uv); col = mix(col, u.rgb, u.a);
    gl_FragColor = vec4(col * 1.1, 1.0);
    #include <colorspace_fragment>
  }` });
const phone = new THREE.Group(); scene.add(phone);
{ box(0.072, 0.152, 0.009, 0, 0, 0, mat(0x1c1d22, 0.3, 0.6), 0.004, phone);
  const s = new THREE.Mesh(new THREE.PlaneGeometry(0.066, 0.146), phMat); s.position.z = 0.0048; phone.add(s);
  const bump = box(0.03, 0.03, 0.004, -0.017, 0.054, -0.0062, mat(0x2a2b30, 0.3, 0.6), 0.006, phone);
  for (const [x, y] of [[-0.024, 0.061], [-0.024, 0.047], [-0.01, 0.054]]) { const l = new THREE.Mesh(new THREE.CylinderGeometry(0.0055, 0.0055, 0.003, 20).rotateX(Math.PI / 2), mat(0x050608, 0.1, 0.2)); l.position.set(x, y, -0.0085); phone.add(l); } }
const PHONEBOX = new THREE.Box3(V(-0.036, -0.076, -0.0045), V(0.036, 0.076, 0.0045));   // the phone's own box (local), for the grip check

// the macro sets live far away, each in its own dark stage
const stage = (pos, col) => { const g = new THREE.Group(); g.position.copy(pos); scene.add(g); g.visible = false;
  g.add(new THREE.Mesh(new THREE.SphereGeometry(6, 24, 12), new THREE.MeshBasicMaterial({ color: col, side: THREE.BackSide }))); return g; };
function tag(text, color = '#ffffff', w = 0.5) { const t = canvasTex(1024, 192, g => { g.fillStyle = 'rgba(10,10,14,0.8)'; g.beginPath(); g.roundRect(6, 6, 1012, 180, 60); g.fill();
    g.fillStyle = color; g.font = 'bold 96px sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(text, 512, 100); });
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: t, depthTest: false, toneMapped: false, transparent: true })); s.scale.set(w, w * 0.1875, 1); s.renderOrder = 30; return s; }

// ------------------------------------------------------------------ the camera's sensor: a chip with a grid of light-catching squares (beats 2, 7)
const SS = V(40, 0, 0);
const sensorSet = stage(SS, 0x07090c);
const ssLight = new THREE.PointLight(0xdfe8ff, 0, 6, 1.2); ssLight.position.set(0.5, 1.9, 1.2); sensorSet.add(ssLight);
const NS = 22, SITE = 0.04, SC = V(0, 1.2, 0);                     // 22 x 22 squares, 4 cm each (the chip stands up, facing +z)
const chip = new THREE.Group(); chip.position.copy(SC); sensorSet.add(chip);
box(1.25, 1.25, 0.04, 0, 0, -0.03, mat(0x1d3a2a, 0.6), 0.01, chip);
box(NS * SITE + 0.05, NS * SITE + 0.05, 0.02, 0, 0, -0.005, mat(0xc8a040, 0.35, 0.8), 0.004, chip);
for (let i = 0; i < 14; i++) for (const s of [-1, 1]) { box(0.02, 0.05, 0.01, -0.55 + i * 0.085, s * 0.6, -0.008, mat(0xd8b050, 0.3, 0.9), 0, chip); box(0.05, 0.02, 0.01, s * 0.6, -0.55 + i * 0.085, -0.008, mat(0xd8b050, 0.3, 0.9), 0, chip); }
const siteGeo = new RoundedBoxGeometry(SITE * 0.86, SITE * 0.86, 0.012, 2, 0.003);
const sites = new THREE.InstancedMesh(siteGeo, new THREE.MeshStandardMaterial({ color: 0x2a2e38, roughness: 0.35, metalness: 0.2 }), NS * NS); chip.add(sites);
const domes = new THREE.InstancedMesh(new THREE.SphereGeometry(SITE * 0.42, 16, 8, 0, Math.PI * 2, 0, Math.PI / 2).rotateX(Math.PI / 2).scale(1, 1, 0.45),
  new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.08, metalness: 0, transparent: true, opacity: 0.35 }), NS * NS); chip.add(domes);
const glow = new THREE.InstancedMesh(new THREE.PlaneGeometry(SITE * 0.82, SITE * 0.82), new THREE.MeshBasicMaterial({ color: 0xffffff, toneMapped: false }), NS * NS); chip.add(glow);
const sitePos = i => V((i % NS - (NS - 1) / 2) * SITE, (Math.floor(i / NS) - (NS - 1) / 2) * -SITE, 0);   // row 0 at the top
{ const m = new THREE.Matrix4(); for (let i = 0; i < NS * NS; i++) { const p = sitePos(i); m.makeTranslation(p.x, p.y, 0.0); sites.setMatrixAt(i, m); m.makeTranslation(p.x, p.y, 0.007); domes.setMatrixAt(i, m);
    m.makeTranslation(p.x, p.y, 0.0065); glow.setMatrixAt(i, m); glow.setColorAt(i, new THREE.Color(0, 0, 0)); } glow.instanceColor.needsUpdate = true; }
// the picture each square catches (the TV picture, sampled once per square)
const PICPX = (() => { const c = PIC.image, g = c.getContext('2d'), d = g.getImageData(0, 0, c.width, c.height).data, out = [];
  for (let i = 0; i < NS * NS; i++) { const x = Math.floor(((i % NS) + 0.5) / NS * c.width), y = Math.floor((Math.floor(i / NS) + 0.5) / NS * c.height), k = (y * c.width + x) * 4;
    out.push(new THREE.Color().setRGB(d[k] / 255, d[k + 1] / 255, d[k + 2] / 255, THREE.SRGBColorSpace)); } return out; })();
const dotTex = canvasTex(64, 64, g => { const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.4, 'rgba(255,255,255,0.6)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); });
function dots(n, color, size) { const g = new THREE.BufferGeometry(); const p = new Float32Array(n * 3); g.setAttribute('position', new THREE.BufferAttribute(p, 3)); g.setDrawRange(0, 0);
  const m = new THREE.Points(g, new THREE.PointsMaterial({ color, size, map: dotTex, transparent: true, depthWrite: false, depthTest: false, blending: THREE.AdditiveBlending, toneMapped: false })); m.frustumCulled = false; m.renderOrder = 9; scene.add(m); return { m, p, n }; }
const RAYS = dots(240, 0xfff2c8, 0.03);
// the rolling shutter (beat 7): a glowing bar reads the rows top to bottom; a small TV beside the chip flashes on and off
const scanBar = new THREE.Mesh(new THREE.PlaneGeometry(NS * SITE + 0.08, 0.012), new THREE.MeshBasicMaterial({ color: 0x7fe0ff, transparent: true, opacity: 0.9, toneMapped: false, depthTest: false }));
scanBar.renderOrder = 12; chip.add(scanBar); scanBar.position.z = 0.02;
const miniU = { pic: { value: PIC }, res: { value: new THREE.Vector2(1920, 1080) }, on: { value: 1 }, bright: { value: 1.3 }, macro: { value: 0 } };
const miniTV = new THREE.Group(); miniTV.position.set(-0.05, 2.05, 0.15); sensorSet.add(miniTV);
box(0.6, 0.36, 0.03, 0, 0, -0.02, mat(0x111216, 0.35, 0.4), 0.008, miniTV);
miniTV.add(new THREE.Mesh(new THREE.PlaneGeometry(0.56, 0.315), new THREE.ShaderMaterial({ uniforms: miniU, vertexShader: VERT, fragmentShader: tvMat.fragmentShader, toneMapped: false })));
const onTag = tag('SCREEN ON', '#7dffa0', 0.42), offTag = tag('SCREEN OFF', '#ff6a6a', 0.42); for (const s of [onTag, offTag]) { s.position.set(-0.05, 1.95, 0.2); sensorSet.add(s); }

// ------------------------------------------------------------------ two grids (beats 3-5): the screen's glowing dots, the camera's squares on top, a bit turned
const GS = V(60, 0, 0);
const gridSet = stage(GS, 0x050608);
const grU = { t: { value: 0 }, th: { value: 0 }, sc: { value: 1 }, slide: { value: 0 }, bayer: { value: 0 }, N: { value: 60 } };
const grMat = new THREE.ShaderMaterial({ uniforms: grU, vertexShader: VERT, toneMapped: false, fragmentShader: `uniform float t, th, sc, slide, bayer, N; varying vec2 vUv;
  void main(){ vec2 p = (vUv - 0.5) * N; float aw = max(fwidth(p.x), fwidth(p.y)) * 0.8;
    vec2 f = fract(p) - 0.5; float d = length(f);
    vec3 bot = vec3(1.0, 0.96, 0.88) * (smoothstep(0.25 + aw, 0.25 - aw, d) * 1.6);   // a glowing dot per screen pixel
    float c = cos(th), s = sin(th); vec2 pr = mat2(c, -s, s, c) * p * sc;
    vec2 g = fract(pr) - 0.5; float hole = smoothstep(0.26 + aw, 0.26 - aw, abs(g.x)) * smoothstep(0.26 + aw, 0.26 - aw, abs(g.y));
    vec2 cell = floor(pr); float ex = mod(cell.x, 2.0), ey = mod(cell.y, 2.0);
    vec3 filt = ex < 0.5 && ey < 0.5 ? vec3(1.0, 0.12, 0.1) : (ex > 0.5 && ey > 0.5 ? vec3(0.15, 0.3, 1.0) : vec3(0.15, 1.0, 0.2));
    vec2 o = pr - p; float hu = fract(0.5 * (o.x + o.y));                  // how far out of line this spot is: the color the stripes take
    vec3 rb = 0.5 + 0.5 * cos(6.2832 * (hu + vec3(0.0, 0.33, 0.67)));
    vec3 top = hole * mix(vec3(1.0), mix(filt * 1.6, rb * 1.7, 0.7), bayer);
    float edge = (p.x / N + 0.5) - (1.15 - 1.3 * slide);                     // the top grid slides in from the right
    float on = smoothstep(-0.004, 0.004, edge);
    vec3 col = mix(bot, bot * top + (1.0 - hole) * vec3(0.012), on);
    gl_FragColor = vec4(col, 1.0);
    #include <colorspace_fragment>
  }` });
const GW = 2.6, gridPlane = new THREE.Mesh(new THREE.PlaneGeometry(GW, GW), grMat); gridPlane.position.set(0, 1.2, 0); gridSet.add(gridPlane);
const brightTag = tag('LINED UP = BRIGHT', '#ffe27a', 1.05), darkTag = tag('OFF = DARK', '#9fb4ff', 0.8);
const ringM = c => new THREE.MeshBasicMaterial({ color: c, transparent: true, depthTest: false, toneMapped: false });
const brightRing = new THREE.Mesh(new THREE.TorusGeometry(0.062, 0.008, 8, 48), ringM(0xffe27a)), darkRing = new THREE.Mesh(new THREE.TorusGeometry(0.062, 0.008, 8, 48), ringM(0x9fb4ff));
for (const s of [brightTag, darkTag, brightRing, darkRing]) { s.renderOrder = 30; gridSet.add(s); }
const slowTag = tag('SLOW MOTION', '#ffffff', 0.5); slowTag.position.set(3.05, 1.68, 0.0); scene.add(slowTag); slowTag.visible = false;
