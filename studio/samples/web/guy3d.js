// The sculpted, skinned 3D guy: loads char/guy.{json,bin} (from char/character.py), builds the skeleton,
// skinned meshes and the face rig (eyes, lids, brows, jaw, teeth, tongue, expression shapes), and gives ways to pose it:
//   G.aim(bone, worldDir, worldBendAxis)  - point a bone along a direction with a defined twist (used by the rig)
//   G.pose({bone: [rx, ry, rz] deg})       - local offsets, for tests
//   G.face({jaw, blink, brow, browIn, look:[x,y], fear, smile, frown, squint, oh, puff, sneer, press, pain})
//   G.untwist()                            - after posing: spread arm roll over the twist bones (call before render)
//   G.legIK(side, footWorld, poleWorld[, footQuatWorld]) - plant a foot exactly (two-bone IK, knee toward the pole)
// Rendering: blended dual-quaternion skinning (keeps volume at elbows/knees/shoulders), baked ambient occlusion,
// skin with pores and light bleeding through (subsurface wrap), denim twill with stitching, knit jersey, strand hair
// cards with a sliding highlight, and eyes with a detailed iris.

// ------------------------------------------------------------------ material patches (composable)
function addPatch(THREE, m, key, fn) {
  if (!m.userData.patches) {
    const prev = m.onBeforeCompile && m.onBeforeCompile !== THREE.Material.prototype.onBeforeCompile ? m.onBeforeCompile : null;
    const prevKey = prev ? (m.customProgramCacheKey !== THREE.Material.prototype.customProgramCacheKey ? m.customProgramCacheKey() : prev.toString()) : '';
    m.userData.patches = prev ? [[prevKey, prev]] : [];
    m.onBeforeCompile = (sh, r) => { for (const [, f] of m.userData.patches) f(sh, r); };
    m.customProgramCacheKey = () => m.userData.patches.map(p => p[0]).join('|');
  }
  if (!m.userData.patches.some(p => p[0] === key)) m.userData.patches.push([key, fn]);
  m.needsUpdate = true;
  return m;
}

const GLSL_COMMON_V = `
vec4 gQ = vec4(0.0, 0.0, 0.0, 1.0); vec4 gD = vec4(0.0);
vec4 qmulG(vec4 a, vec4 b){ return vec4(a.w * b.xyz + b.w * a.xyz + cross(a.xyz, b.xyz), a.w * b.w - dot(a.xyz, b.xyz)); }
vec4 m2qG(mat4 m){
  float tr = m[0][0] + m[1][1] + m[2][2]; vec4 q;
  if (tr > 0.0) { float s = sqrt(tr + 1.0) * 2.0; q = vec4((m[1][2] - m[2][1]) / s, (m[2][0] - m[0][2]) / s, (m[0][1] - m[1][0]) / s, 0.25 * s); }
  else if (m[0][0] > m[1][1] && m[0][0] > m[2][2]) { float s = sqrt(1.0 + m[0][0] - m[1][1] - m[2][2]) * 2.0; q = vec4(0.25 * s, (m[1][0] + m[0][1]) / s, (m[2][0] + m[0][2]) / s, (m[1][2] - m[2][1]) / s); }
  else if (m[1][1] > m[2][2]) { float s = sqrt(1.0 + m[1][1] - m[0][0] - m[2][2]) * 2.0; q = vec4((m[1][0] + m[0][1]) / s, 0.25 * s, (m[2][1] + m[1][2]) / s, (m[2][0] - m[0][2]) / s); }
  else { float s = sqrt(1.0 + m[2][2] - m[0][0] - m[1][1]) * 2.0; q = vec4((m[2][0] + m[0][2]) / s, (m[2][1] + m[1][2]) / s, 0.25 * s, (m[0][1] - m[1][0]) / s); }
  return q;
}
vec3 qrotG(vec4 q, vec3 v){ return v + 2.0 * cross(q.xyz, cross(q.xyz, v) + q.w * v); }
void dqAdd(inout vec4 Q, inout vec4 D, mat4 m, float w, vec4 ref){
  vec4 q = m2qG(m); vec4 d = 0.5 * qmulG(vec4(m[3].xyz, 0.0), q);
  if (dot(q, ref) < 0.0) { q = -q; d = -d; }
  Q += w * q; D += w * d;
}`;

// blended dual-quaternion skinning: uDQ = 0 is plain linear blend, 1 is pure dual quaternion
function dqSkin(THREE, m, amount = 0.75) {
  const U = { uDQ: { value: amount } };
  return addPatch(THREE, m, 'dq', sh => {
    Object.assign(sh.uniforms, U);
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nuniform float uDQ;\n' + GLSL_COMMON_V)
      .replace('#include <skinnormal_vertex>', `vec3 objectNormalRest = objectNormal;
#include <skinnormal_vertex>
#ifdef USE_SKINNING
  { vec4 ref = m2qG(boneMatX); vec4 Q = vec4(0.0), D = vec4(0.0);
    dqAdd(Q, D, boneMatX, skinWeight.x, ref); dqAdd(Q, D, boneMatY, skinWeight.y, ref);
    dqAdd(Q, D, boneMatZ, skinWeight.z, ref); dqAdd(Q, D, boneMatW, skinWeight.w, ref);
    float ln = length(Q); gQ = Q / ln; gD = D / ln; }
#endif`)
      .replace('#include <skinning_vertex>', `#ifdef USE_SKINNING
  vec4 skinVertex = bindMatrix * vec4( transformed, 1.0 );
  vec4 skinned = vec4( 0.0 );
  skinned += boneMatX * skinVertex * skinWeight.x; skinned += boneMatY * skinVertex * skinWeight.y;
  skinned += boneMatZ * skinVertex * skinWeight.z; skinned += boneMatW * skinVertex * skinWeight.w;
  vec3 pL = ( bindMatrixInverse * skinned ).xyz;
  vec3 p0 = skinVertex.xyz;
  vec3 pD = qrotG(gQ, p0) + 2.0 * (gQ.w * gD.xyz - gD.w * gQ.xyz + cross(gQ.xyz, gD.xyz));
  pD = ( bindMatrixInverse * vec4(pD, 1.0) ).xyz;
  transformed = mix(pL, pD, uDQ);
#endif`);
    // normals: blend the linear-skinned normal with the dual-quat rotated one
    sh.vertexShader = sh.vertexShader.replace('#include <defaultnormal_vertex>', `#ifdef USE_SKINNING
  { vec3 nD = mat3(bindMatrixInverse) * qrotG(gQ, mat3(bindMatrix) * objectNormalRest);
    objectNormal = normalize(mix(objectNormal, nD, uDQ)); }
#endif
#include <defaultnormal_vertex>`);
  });
}

// baked ambient occlusion (vertex attribute 'ao'): darkens ambient fully and direct light a little
function bakedAO(THREE, m) {
  return addPatch(THREE, m, 'ao', sh => {
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\n#ifdef USE_SKINNING\nattribute float ao;\n#endif\nvarying float vAO;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\n#ifdef USE_SKINNING\nvAO = ao;\n#else\nvAO = 1.0;\n#endif');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying float vAO;')
      .replace('#include <aomap_fragment>', `#include <aomap_fragment>
  { float a = vAO * vAO; reflectedLight.indirectDiffuse *= a; reflectedLight.indirectSpecular *= a;
    reflectedLight.directDiffuse *= mix(1.0, vAO, 0.4); reflectedLight.directSpecular *= mix(1.0, vAO, 0.6); }`);
  });
}

const GLSL_NOISE = `
float hG(vec3 p){ p = fract(p * 0.3183099 + 0.1); p *= 17.0; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }
float nG(vec3 x){ vec3 i = floor(x), f = fract(x); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(mix(hG(i), hG(i + vec3(1,0,0)), f.x), mix(hG(i + vec3(0,1,0)), hG(i + vec3(1,1,0)), f.x), f.y),
             mix(mix(hG(i + vec3(0,0,1)), hG(i + vec3(1,0,1)), f.x), mix(hG(i + vec3(0,1,1)), hG(i + vec3(1,1,1)), f.x), f.y), f.z); }
vec3 bumpG(vec3 surf_pos, vec3 surf_norm, float h, float scale, float faceDirection){
  vec2 dH = vec2(dFdx(h), dFdy(h)) * scale;
  vec3 sx = normalize(dFdx(surf_pos)), sy = normalize(dFdy(surf_pos));
  vec3 R1 = cross(sy, surf_norm), R2 = cross(surf_norm, sx);
  float det = dot(sx, R1) * faceDirection;
  return normalize(abs(det) * surf_norm - sign(det) * (dH.x * R1 + dH.y * R2));
}`;

// a surface-detail patch: rest-space position in, height + colour tweaks out (bump through screen derivatives)
function detail(THREE, m, key, glslColorAndHeight, extraLight = '') {
  return addPatch(THREE, m, key, sh => {
    if (!sh.vertexShader.includes('varying vec3 vRestD;'))
      sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vRestD;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvRestD = position;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vRestD;\n' + (sh.fragmentShader.includes('float hG(') ? '' : GLSL_NOISE) + '\nfloat dH_' + key + ' = 0.0;')
      .replace('#include <color_fragment>', `#include <color_fragment>
  { vec3 P = vRestD; float h = 0.0; float fade = clamp(1.0 - length(fwidth(P)) * 260.0, 0.0, 1.0);
    ${glslColorAndHeight}
    dH_${key} = h * fade; }`)
      .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
  normal = bumpG(-vViewPosition, normal, dH_${key}, 1.0, faceDirection);`)
      .replace('#include <lights_fragment_end>', '#include <lights_fragment_end>\n' + extraLight);
  });
}

// skin: pores, fine creases, a little colour mottling; light bleeding through at the terminator (subsurface wrap)
const SKIN_GLSL = `
  float pores = nG(P * 2600.0) * 0.6 + nG(P * 900.0) * 0.4;
  h = (pores - 0.5) * 0.00012 + (nG(P * 260.0) - 0.5) * 0.00008;
  diffuseColor.rgb *= 1.0 + fade * (0.035 * (nG(P * 140.0) - 0.5) + 0.03 * (pores - 0.5));`;
const SKIN_SSS = `
#if NUM_DIR_LIGHTS > 0
  for (int i = 0; i < NUM_DIR_LIGHTS; i++) {
    float ndl = dot(normal, directionalLights[i].direction);
    float wrap = clamp((ndl + 0.5) / 1.5, 0.0, 1.0) - clamp(ndl, 0.0, 1.0);
    reflectedLight.directDiffuse += directionalLights[i].color * wrap * diffuseColor.rgb * vec3(0.75, 0.4, 0.3) * 0.18;
  }
#endif`;
// denim: right-hand twill (diagonal ribs), slubby threads, fades on the thighs and knees, orange double stitching
const DENIM_GLSL = `
  float side = P.x >= 0.0 ? 1.0 : -1.0;
  float cx = side * (0.09 + max(0.0, 0.95 - P.y) * 0.07);
  float ang = atan(P.z, (P.x - cx) * side);
  float u = ang * 0.072, v = P.y;
  if (P.y > 0.86) u = P.x;
  float tw = sin((u * 0.72 + v) * 6.2832 * 420.0);
  float slub = nG(vec3(u * 40.0, v * 1400.0, 0.0));
  h = (tw * 0.5 + 0.5) * 0.00006 + slub * 0.00003;
  diffuseColor.rgb *= 1.0 + fade * (0.12 * (tw * 0.5) + 0.08 * (slub - 0.5));
  float fd = (1.0 - smoothstep(-0.075, -0.02, P.z)) * (smoothstep(0.6, 0.72, P.y) * (1.0 - smoothstep(0.82, 0.9, P.y)) + 0.8 * exp(-pow((P.y - 0.53) / 0.05, 2.0)));
  diffuseColor.rgb = mix(diffuseColor.rgb, diffuseColor.rgb * vec3(1.35, 1.32, 1.22) + vec3(0.04, 0.05, 0.08), fd * 0.45);
  float arc = abs(ang) * 0.072, arcIn = abs(abs(ang) - 3.14159) * 0.072;
  float dash = step(0.45, fract(v * 230.0));
  float st = 0.0;
  if (P.y < 0.84) {
    st = max(st, (1.0 - smoothstep(0.0005, 0.0011, abs(arc - 0.004))) * dash);
    st = max(st, (1.0 - smoothstep(0.0005, 0.0011, abs(arc - 0.0105))) * dash);
    st = max(st, (1.0 - smoothstep(0.0005, 0.0011, abs(arcIn - 0.003))) * dash);
  }
  float hemY = ${'${HEM}'};
  st = max(st, (1.0 - smoothstep(0.0005, 0.0011, abs(P.y - hemY))) * step(0.45, fract(ang * 0.072 * 230.0)));
  diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.85, 0.52, 0.18), st * 0.85);
  h += st * 0.00012;`;
// jersey knit: tiny vertical V-stitches, a soft mottle
const JERSEY_GLSL = `
  float ang = atan(P.z, P.x);
  float u = P.x * 900.0, v = P.y * 1100.0;
  float k = abs(fract(u + 0.5 * abs(fract(v) - 0.5)) - 0.5);
  h = k * 0.00005 + (nG(P * 300.0) - 0.5) * 0.00004;
  diffuseColor.rgb *= 1.0 + 0.06 * (nG(P * 90.0) - 0.5) + fade * 0.04 * (k - 0.25);`;

// iris: radial fibres, a darker limbal ring, a lighter collarette around the pupil (object-space disc)
function irisMat(THREE, R) {
  const m = new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.25, clearcoat: 1, clearcoatRoughness: 0.03 });
  m.onBeforeCompile = sh => {
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vObj;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvObj = position;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vObj;\n' + GLSL_NOISE)
      .replace('#include <color_fragment>', `#include <color_fragment>
  { float r = length(vObj.xy) / ${(R * 0.5).toFixed(6)}; float a = atan(vObj.y, vObj.x);
    float fib = nG(vec3(a * 18.0, r * 3.0, 0.0)) * 0.6 + nG(vec3(a * 45.0, r * 8.0, 2.0)) * 0.4;
    vec3 base = mix(vec3(0.36, 0.22, 0.09), vec3(0.52, 0.36, 0.16), fib);
    base = mix(base, vec3(0.62, 0.46, 0.22), (1.0 - smoothstep(0.38, 0.55, r)) * 0.7);        // collarette
    base = mix(base, vec3(0.10, 0.06, 0.03), smoothstep(0.78, 0.98, r));                      // limbal ring
    diffuseColor.rgb = base; }`);
  };
  m.customProgramCacheKey = () => 'iris';
  return m;
}

// strand hair cards: alpha strands from a generated texture, Kajiya-Kay highlights sliding along each strand
function hairCardsMat(THREE, color) {
  const c = document.createElement('canvas'); c.width = 128; c.height = 256; const g = c.getContext('2d');
  g.clearRect(0, 0, 128, 256);
  for (let i = 0; i < 46; i++) {
    const x = 6 + Math.random() * 116, w = 1.2 + Math.random() * 2.2, l = 150 + Math.random() * 106, sh = 0.75 + Math.random() * 0.5;
    const grd = g.createLinearGradient(0, 0, 0, l); grd.addColorStop(0, `rgba(${255 * sh | 0},${255 * sh | 0},${255 * sh | 0},1)`); grd.addColorStop(0.85, `rgba(${255 * sh | 0},${255 * sh | 0},${255 * sh | 0},0.9)`); grd.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = grd; g.beginPath(); g.moveTo(x - w / 2, 0); g.quadraticCurveTo(x + (Math.random() - 0.5) * 8, l * 0.5, x + (Math.random() - 0.5) * 6, l); g.lineTo(x + w / 2, 0); g.fill();
  }
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  const m = new THREE.MeshStandardMaterial({ color, map: tex, alphaTest: 0.42, alphaToCoverage: true, side: THREE.DoubleSide, roughness: 0.55 });
  m.onBeforeCompile = sh => {
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nattribute vec3 tan;\nvarying vec3 vTanV;')
      .replace('#include <skinning_vertex>', '#include <skinning_vertex>\n#ifdef USE_SKINNING\nvTanV = normalize(normalMatrix * mat3(skinWeight.x * boneMatX + skinWeight.y * boneMatY + skinWeight.z * boneMatZ + skinWeight.w * boneMatW) * tan);\n#else\nvTanV = normalize(normalMatrix * tan);\n#endif');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vTanV;')
      .replace('#include <lights_fragment_end>', `#include <lights_fragment_end>
#if NUM_DIR_LIGHTS > 0
  { vec3 T = normalize(vTanV), Vv = normalize(vViewPosition);
    for (int i = 0; i < NUM_DIR_LIGHTS; i++) { vec3 L = directionalLights[i].direction;
      vec3 Tp = normalize(T + normal * 0.12), Ts = normalize(T - normal * 0.1);
      float s1 = pow(sqrt(max(0.0, 1.0 - pow(dot(Tp, normalize(L + Vv)), 2.0))), 110.0);
      float s2 = pow(sqrt(max(0.0, 1.0 - pow(dot(Ts, normalize(L + Vv)), 2.0))), 24.0);
      float lit = clamp(dot(normal, L) * 0.5 + 0.5, 0.0, 1.0);
      reflectedLight.directSpecular += directionalLights[i].color * lit * (s1 * 0.22 + s2 * 0.12 * diffuseColor.rgb * 2.0); } }
#endif`);
  };
  m.customProgramCacheKey = () => 'haircards';
  return m;
}

// Face paint, per pixel, from each vertex's rest position (so it rides the skin through skinning): brows with hair strokes,
// upper lash line, red lips with a darker parting line.  Broad tones (beard shadow, flush) come in as vertex colours.
function facePaint(THREE, m, man) {
  m.vertexColors = true;
  const L = man.lips || [];
  const U = { uEyeR: { value: new THREE.Vector3(...man.eyes.R) }, uEyeL: { value: new THREE.Vector3(...man.eyes.L) }, uMouth: { value: new THREE.Vector2(man.mouthY, man.mouthZ ?? -0.097) },
    uLipC: { value: L.map(l => new THREE.Vector3(...l[0])) }, uLipR: { value: L.map(l => new THREE.Vector3(...l[1])) } };
  const N = L.length;
  return addPatch(THREE, m, 'facepaint' + N, sh => {
    Object.assign(sh.uniforms, U);
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vRest;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvRest = position;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', `#include <common>
varying vec3 vRest; uniform vec3 uEyeR, uEyeL; uniform vec2 uMouth; uniform vec3 uLipC[${N}]; uniform vec3 uLipR[${N}];
float h21(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
float brow(vec3 p, vec3 e, float s){
  float u = (p.x - e.x) * s;
  float yb = e.y + 0.0165 + 0.0035 * cos(3.14159 * (u - 0.008) / 0.046) - 0.0012 * (1.0 - smoothstep(-0.018, -0.008, u));
  float th = clamp(0.0085 - 0.0055 * (u + 0.016) / 0.04, 0.003, 0.0085);
  float dy = p.y - yb;
  float edge = th * (0.42 + 0.08 * sin(u * 1500.0) + 0.05 * sin(u * 3700.0 + 1.0));
  float band = 1.0 - smoothstep(edge * 0.7, edge, abs(dy));
  float span = smoothstep(-0.019, -0.0145, u) * (1.0 - smoothstep(0.0205, 0.026, u));
  float a = mix(1.25, 0.12, smoothstep(-0.016, 0.012, u));
  float w = -sin(a) * u + cos(a) * dy;
  float lane = floor(w / 0.00055);
  float hair = (1.0 - smoothstep(0.0, 0.25, abs(fract(w / 0.00055) - 0.5) - 0.12)) * step(0.25, h21(vec2(lane, s)));
  return band * span * mix(0.55, 1.0, hair) * step(p.z, e.z - 0.004);
}
float lash(vec3 p, vec3 e, float s){
  float u = (p.x - e.x) * s; float uu = clamp(u / 0.0135, -1.6, 1.6);
  float cut = e.y + ${(man.lidUp ?? 0.0046).toFixed(5)} - 0.0066 * uu * uu + 0.0008 * uu;
  float r = length(p - e); float d = p.y - cut;
  float up = (1.0 - smoothstep(0.0002, 0.0011 + 0.0006 * clamp(uu, 0.0, 1.0), d)) * step(-0.0007, d);
  float lcut = e.y + ${(man.lidLo ?? -0.0056).toFixed(5)} + 0.0042 * uu * uu + 0.0008 * uu; float dl = lcut - p.y;
  float lo = 0.45 * (1.0 - smoothstep(0.0001, 0.0007, dl)) * step(-0.0005, dl);
  return max(up, lo) * (1.0 - smoothstep(0.0158, 0.0178, r)) * step(p.z, e.z);
}`).replace('#include <color_fragment>', `#include <color_fragment>
{
  vec3 p = vRest;
  float br = max(brow(p, uEyeR, 1.0), brow(p, uEyeL, -1.0));
  diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.16, 0.095, 0.06), br * 0.92);
  float ls = max(lash(p, uEyeR, 1.0), lash(p, uEyeL, -1.0));
  diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.05, 0.03, 0.03), ls * 0.95);
  float ld = 1.0;
  for (int i = 0; i < ${N}; i++) { vec3 q = (p - uLipC[i]) / uLipR[i]; ld = min(ld, (length(q) - 1.0) * min(uLipR[i].x, min(uLipR[i].y, uLipR[i].z))); }
  float lip = (1.0 - smoothstep(-0.0002, 0.0011, ld)) * step(p.z, uMouth.y + 0.009);
  diffuseColor.rgb = mix(diffuseColor.rgb, diffuseColor.rgb * vec3(0.8, 0.5, 0.5), lip * 0.9);
  float slit = exp(-pow((p.y - uMouth.x) / 0.0011, 2.0)) * (1.0 - smoothstep(0.02, 0.0235, abs(p.x))) * (1.0 - smoothstep(0.0, 0.0025, ld));
  diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.18, 0.06, 0.07), slit * 0.8);
}`);
  });
}

export async function loadGuy(THREE, base, opts = {}) {
  const man = await (await fetch(base + '.json')).json();
  const bin = await (await fetch(base + '.bin')).arrayBuffer();
  const LEVEL = opts.quality ?? 2;              // 0 = plain (fast previews), 1 = + skinning/AO, 2 = everything
  const root = new THREE.Group();
  const bones = {}, list = [];
  for (const b of man.bones) {
    const bone = new THREE.Bone(); bone.name = b.name;
    const h = new THREE.Vector3(...b.head);
    const ph = b.parent ? new THREE.Vector3(...man.bones.find(x => x.name === b.parent).head) : new THREE.Vector3();
    bone.position.copy(h.clone().sub(ph));
    bone.userData = { head: h, tail: new THREE.Vector3(...b.tail), parent: b.parent };
    bones[b.name] = bone; list.push(bone);
  }
  for (const b of man.bones) (b.parent ? bones[b.parent] : root).add(bones[b.name]);
  root.updateMatrixWorld(true);
  const skeleton = new THREE.Skeleton(list);
  const M = opts.materials || {};
  const mat = {
    skin: M.skin || new THREE.MeshPhysicalMaterial({ color: 0xd99a7c, roughness: 0.55, sheen: 0.15, sheenColor: new THREE.Color(0xffb099) }),
    shirt: M.shirt || new THREE.MeshPhysicalMaterial({ color: 0x1fae9b, roughness: 0.85, sheen: 0.8, sheenRoughness: 0.6, sheenColor: new THREE.Color(0x77ffe6) }),
    jeans: M.jeans || new THREE.MeshStandardMaterial({ color: 0x4068bd, roughness: 0.9 }),
    shoe: M.shoe || new THREE.MeshStandardMaterial({ color: 0x3a2d31, roughness: 0.55 }),
    hair: M.hair || new THREE.MeshStandardMaterial({ color: 0x5b351f, roughness: 0.6 }),
    sole: M.sole || new THREE.MeshStandardMaterial({ color: 0xe8e2d6, roughness: 0.7 }),
  };
  const capSkin = mat.skin.clone();             // the blink cap: same look, no skinning patches
  mat.face = facePaint(THREE, mat.skin.clone(), man);      // painted face: brows, lashes, lips (cloned before any patching)
  if (LEVEL >= 1) for (const k of ['skin', 'face', 'shirt', 'jeans', 'shoe', 'hair', 'sole']) { dqSkin(THREE, mat[k]); bakedAO(THREE, mat[k]); }
  if (LEVEL >= 2) {
    detail(THREE, mat.skin, 'skin', SKIN_GLSL, SKIN_SSS); detail(THREE, mat.face, 'skin', SKIN_GLSL, SKIN_SSS);
    const hem = (man.jeansHem ?? 0.115) + 0.016;
    detail(THREE, mat.jeans, 'denim', DENIM_GLSL.replace('${HEM}', hem.toFixed(4)));
    detail(THREE, mat.shirt, 'jersey', JERSEY_GLSL);
    mat.hair.color.multiplyScalar(0.72);        // the shell is the dark underlayer; the cards carry the look
  }
  const hairColor = (M.hair ? M.hair.color : new THREE.Color(0x5b351f)).clone().multiplyScalar(1.3);
  const which = n => n.startsWith('skin') ? mat.skin : n === 'shirt' ? mat.shirt : n === 'jeans' ? mat.jeans : n.startsWith('shoe') ? mat.shoe : n.startsWith('sole') ? mat.sole : mat.hair;
  const meshes = {};
  for (const m of man.meshes) {
    if (m.name === 'hairCards' && LEVEL < 2) continue;
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(bin, m.pos, m.nv * 3), 3));
    g.setIndex(new THREE.BufferAttribute(new Uint32Array(bin, m.idx, m.nf * 3), 1));
    g.setAttribute('skinIndex', new THREE.BufferAttribute(new Uint16Array(bin, m.si, m.nv * 4), 4));
    g.setAttribute('skinWeight', new THREE.BufferAttribute(new Float32Array(bin, m.sw, m.nv * 4), 4));
    if (m.col !== undefined) g.setAttribute('color', new THREE.BufferAttribute(new Uint8Array(bin, m.col, m.nv * 4), 4, true));
    if (m.ao !== undefined) g.setAttribute('ao', new THREE.BufferAttribute(new Uint8Array(bin, m.ao, m.nv), 1, true));
    if (m.uv !== undefined) g.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(bin, m.uv, m.nv * 2), 2));
    if (m.tan !== undefined) g.setAttribute('tan', new THREE.BufferAttribute(new Float32Array(bin, m.tan, m.nv * 3), 3));
    if (m.nrm !== undefined) g.setAttribute('normal', new THREE.BufferAttribute(new Float32Array(bin, m.nrm, m.nv * 3), 3));
    else g.computeVertexNormals();
    if (m.morphs && m.morphs.length) {
      g.morphTargetsRelative = true;
      g.morphAttributes.position = m.morphs.map(mm => { const a = new THREE.BufferAttribute(new Float32Array(bin, mm.p, m.nv * 3), 3); a.name = mm.name; return a; });
      g.morphAttributes.normal = m.morphs.map(mm => { const a = new THREE.BufferAttribute(new Float32Array(bin, mm.n, m.nv * 3), 3); a.name = mm.name; return a; });
    }
    let mt = which(m.name);
    if (m.name === 'hairCards') mt = hairCardsMat(THREE, hairColor);
    if (m.col !== undefined) mt = mat.face;
    const sm = new THREE.SkinnedMesh(g, mt);
    sm.castShadow = m.name !== 'hairCards'; sm.receiveShadow = true; sm.frustumCulled = false;
    sm.bind(skeleton, new THREE.Matrix4());
    root.add(sm); meshes[m.name] = sm;
  }
  // ---------------- face rig (rigid parts riding on the head and jaw bones)
  const headB = bones.head, jawB = bones.jaw;
  const toLocal = (bone, p) => { const w = new THREE.Vector3(...p); return bone.worldToLocal(w); };
  const eyeMat = new THREE.MeshPhysicalMaterial({ color: 0xfbf6f0, roughness: 0.1, clearcoat: 1 });
  const pupMat = new THREE.MeshPhysicalMaterial({ color: 0x050304, roughness: 0.1, clearcoat: 1 });
  const dark = new THREE.MeshStandardMaterial({ color: 0x3d0b14, roughness: 0.8 });
  const teethM = new THREE.MeshStandardMaterial({ color: 0xf6f1e8, roughness: 0.35 });
  const tongueM = new THREE.MeshStandardMaterial({ color: 0xd9566a, roughness: 0.5 });
  const R = man.eyeR, eyes = {}, lids = {}, brows = {};
  const iMat = LEVEL >= 2 ? irisMat(THREE, R) : new THREE.MeshPhysicalMaterial({ color: 0x5a3a1c, roughness: 0.2, clearcoat: 1 });
  for (const S of ['R', 'L']) {
    const e = new THREE.Group(); e.position.copy(toLocal(headB, man.eyes[S])); headB.add(e);
    // real eye: 24 mm ball, 11.7 mm iris sitting just under a clear cornea bulge
    const ball = new THREE.Mesh(new THREE.SphereGeometry(R, 32, 24), eyeMat); e.add(ball);
    const iris = new THREE.Mesh(new THREE.SphereGeometry(R * 0.5, 32, 16), iMat); iris.scale.set(1, 1, 0.3); iris.position.z = -R * 0.9; e.add(iris);
    const pup = new THREE.Mesh(new THREE.SphereGeometry(R * 0.2, 16, 12), pupMat); pup.scale.set(1, 1, 0.3); pup.position.z = -R * 0.955; e.add(pup);
    const cornea = new THREE.Mesh(new THREE.SphereGeometry(R * 0.55, 24, 16), new THREE.MeshPhysicalMaterial({ color: 0xffffff, transparent: true, opacity: 0.1, roughness: 0.0, clearcoat: 1, specularIntensity: 1 }));
    cornea.scale.set(1, 1, 0.45); cornea.position.z = -R * 0.93; e.add(cornea);
    for (const m of [ball, iris, pup, cornea]) m.castShadow = false;
    eyes[S] = { g: e, pup };
    // blink: a skin cap tucked inside the sculpted upper lid that slides down over the eye (shown only while blinking)
    const edge = Math.asin((man.lidUp ?? 0.0046) / (R * 1.18));
    const cap = new THREE.Mesh(new THREE.SphereGeometry(R * 1.18, 32, 12, Math.PI, Math.PI, 0.25, Math.PI / 2 - edge - 0.25), capSkin);
    const lidG = new THREE.Group(); lidG.add(cap); lidG.position.copy(e.position); headB.add(lidG);
    const lr = R * 1.19, lp = [];
    for (let i = 0; i <= 16; i++) { const f = Math.PI + 0.45 + (Math.PI - 0.9) * i / 16; lp.push(new THREE.Vector3(-lr * Math.cos(f) * Math.cos(edge), lr * Math.sin(edge), lr * Math.sin(f) * Math.cos(edge))); }
    const lash = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(lp), 24, 0.0004, 4), new THREE.MeshStandardMaterial({ color: 0x1a1010, roughness: 0.9 }));
    lidG.add(lash);
    lids[S] = { g: lidG, cap, lash, edge };
    brows[S] = bones['brow' + S];
  }
  const my = man.mouthY;
  const mz = man.mouthZ ?? -0.092;
  const mouthIn = new THREE.Mesh(new THREE.SphereGeometry(0.021, 24, 16), dark); mouthIn.scale.set(1.1, 0.8, 1.0);
  mouthIn.position.copy(toLocal(headB, [0, my - 0.006, mz + 0.024])); headB.add(mouthIn);
  const teethU = new THREE.Mesh(new THREE.CapsuleGeometry(0.0055, 0.028, 4, 10), teethM); teethU.rotation.z = Math.PI / 2;
  teethU.position.copy(toLocal(headB, [0, my + 0.002, mz + 0.0085])); headB.add(teethU);
  const teethL = new THREE.Mesh(new THREE.CapsuleGeometry(0.005, 0.025, 4, 10), teethM); teethL.rotation.z = Math.PI / 2;
  teethL.position.copy(toLocal(jawB, [0, my - 0.006, mz + 0.011])); jawB.add(teethL);
  const tongue = new THREE.Mesh(new THREE.SphereGeometry(0.018, 16, 12), tongueM); tongue.scale.set(1.1, 0.45, 1.3);
  tongue.position.copy(toLocal(jawB, [0, my - 0.011, mz + 0.026])); jawB.add(tongue);
  root.updateMatrixWorld(true);

  // ---------------- posing
  const REST = {};
  for (const b of list) REST[b.name] = { pos: b.position.clone(), q: b.quaternion.clone(), axis: b.userData.tail.clone().sub(b.userData.head).normalize(),
    len: b.userData.tail.distanceTo(b.userData.head) };
  const F = new THREE.Vector3(0, 0, -1), U = new THREE.Vector3(0, 1, 0);
  const basis = (a, n) => { const x = n.clone().sub(a.clone().multiplyScalar(n.dot(a))).normalize(); const z = new THREE.Vector3().crossVectors(a, x); return new THREE.Matrix4().makeBasis(x, a, z); };
  const restNormal = name => {      // the bend axis each bone had in the rest pose (matches main.js hingeDir)
    const a = REST[name].axis; let n = new THREE.Vector3().crossVectors(a, F);
    if (n.lengthSq() < 1e-4) n.crossVectors(a, U); return n.normalize();
  };
  function reset() { for (const b of list) { b.position.copy(REST[b.name].pos); b.quaternion.copy(REST[b.name].q); } root.updateMatrixWorld(true); }
  function aim(name, dir, bend) {   // world direction + world bend axis -> local rotation
    const b = bones[name], a0 = REST[name].axis, n0 = restNormal(name);
    const R0 = basis(a0, n0), R1 = basis(dir.clone().normalize(), bend.clone().normalize());
    const qw = new THREE.Quaternion().setFromRotationMatrix(R1.multiply(R0.clone().invert()));
    const pq = new THREE.Quaternion(); if (b.parent && b.parent.isBone) b.parent.getWorldQuaternion(pq); else root.getWorldQuaternion(pq);
    b.quaternion.copy(pq.invert().multiply(qw)); b.updateMatrixWorld(true);
  }
  function setWorld(name, qw) {
    const b = bones[name], pq = new THREE.Quaternion();
    if (b.parent && b.parent.isBone) b.parent.getWorldQuaternion(pq); else root.getWorldQuaternion(pq);
    b.quaternion.copy(pq.invert().multiply(qw)); b.updateMatrixWorld(true);
  }
  function pose(p) {
    reset();
    for (const [k, e] of Object.entries(p)) if (bones[k]) bones[k].quaternion.multiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(e[0] * Math.PI / 180, e[1] * Math.PI / 180, e[2] * Math.PI / 180)));
    untwist();
    root.updateMatrixWorld(true);
  }
  // swing-twist split about a local axis: q = swing * twist
  const twistOf = (q, a) => { const p = a.clone().multiplyScalar(a.x * q.x + a.y * q.y + a.z * q.z); const t = new THREE.Quaternion(p.x, p.y, p.z, q.w); return t.lengthSq() < 1e-12 ? new THREE.Quaternion() : t.normalize(); };
  function untwist() {
    if (!bones.uarmTwistR) return;
    for (const S of ['R', 'L']) {
      const ua = bones['uarm' + S], ut = bones['uarmTwist' + S], fa = bones['farm' + S], ft = bones['farmTwist' + S], ha = bones['hand' + S];
      // upper arm: keep the swing on the arm, move its roll to the twist bone (the shoulder skin stops wringing)
      const au = REST['uarm' + S].axis, tw = twistOf(ua.quaternion, au);
      ua.quaternion.multiply(tw.clone().invert()); ut.quaternion.copy(tw);
      // forearm: its own roll and the hand's roll both live on the forearm twist bone (elbow skin stays put)
      const af = REST['farm' + S].axis, tf = twistOf(fa.quaternion, af);
      fa.quaternion.multiply(tf.clone().invert()); ha.quaternion.premultiply(tf);
      ft.quaternion.copy(twistOf(ha.quaternion, af));
    }
    root.updateMatrixWorld(true);
  }
  // two-bone leg IK: hip fixed, foot to the target, knee bending toward the pole; optional world foot orientation
  function legIK(S, target, pole, footQ) {
    root.updateMatrixWorld(true);
    const th = bones['thigh' + S], sh = bones['shin' + S];
    const hip = th.getWorldPosition(new THREE.Vector3());
    const l1 = REST['thigh' + S].len, l2 = REST['shin' + S].len;
    const tv = target.clone().sub(hip); let d = tv.length();
    d = Math.min(Math.max(d, Math.abs(l1 - l2) + 1e-3), l1 + l2 - 1e-4);
    const dir = tv.normalize();
    const pv = pole.clone().sub(hip); const side = new THREE.Vector3().crossVectors(dir, pv).normalize();   // knee hinge axis
    const up = new THREE.Vector3().crossVectors(side, dir).normalize();                                     // toward the pole, in-plane
    const a = Math.acos(Math.min(1, Math.max(-1, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))));
    const knee = hip.clone().addScaledVector(dir, Math.cos(a) * l1).addScaledVector(up, Math.sin(a) * l1);
    const foot = hip.clone().addScaledVector(dir, d);
    aim('thigh' + S, knee.clone().sub(hip), side);
    aim('shin' + S, foot.clone().sub(knee), side);
    if (footQ) setWorld('foot' + S, footQ);
    return { knee, foot, reach: tv.length() };
  }
  const EXPR = ['smile', 'frown', 'squint', 'oh', 'puff', 'sneer', 'press', 'pain'];
  function face(f = {}) {
    const jaw = f.jaw ?? 0, blink = f.blink ?? 0, brow = f.brow ?? 0, browIn = f.browIn ?? 0, look = f.look || [0, 0], fear = f.fear ?? 0;
    bones.jaw.quaternion.setFromAxisAngle(new THREE.Vector3(1, 0, 0), -jaw * 20 * Math.PI / 180);   // chin swings down and back
    const oh = f.oh ?? 0, narrow = 1 - 0.5 * Math.min(1, oh);          // a rounded mouth: the inside narrows with the lips
    tongue.visible = jaw > 0.2; teethU.visible = teethL.visible = mouthIn.visible = jaw > 0.04;
    teethU.scale.set(1, narrow, 1); teethL.scale.set(1, narrow, 1); tongue.scale.set(1.1 * narrow, 0.45, 1.3); mouthIn.scale.set(1.1 * narrow, 0.8, 1.0);
    const hm = meshes.skin_head;
    if (hm && hm.morphTargetDictionary) for (const k of EXPR) { const i = hm.morphTargetDictionary[k]; if (i !== undefined) hm.morphTargetInfluences[i] = Math.max(0, Math.min(1.2, f[k] ?? 0)); }
    const squint = (f.squint ?? 0) + 0.5 * (f.smile ?? 0) + 0.6 * (f.pain ?? 0);
    for (const S of ['R', 'L']) {
      eyes[S].g.rotation.set(-look[1] * 0.35, look[0] * 0.45, 0);
      eyes[S].pup.scale.setScalar(1 - 0.35 * fear);
      const L = lids[S], close = Math.min(1, blink + 0.25 * Math.max(0, -look[1]) + 0.25 * squint);
      L.g.rotation.x = -close * (L.edge + Math.asin(-(man.lidLo ?? -0.0056) / (R * 1.18)) + 0.06);
      L.cap.visible = L.lash.visible = close > 0.03;
      const sx = S === 'R' ? 1 : -1;
      brows[S].position.copy(REST['brow' + S].pos); brows[S].position.y += 0.004 * brow + 0.003 * fear - 0.0015 * browIn - 0.0012 * (f.pain ?? 0) - 0.001 * (f.frown ?? 0);
      brows[S].rotation.set(0, 0, sx * (0.1 * browIn + 0.12 * fear + 0.1 * (f.pain ?? 0)));
    }
  }
  face({});
  return { root, bones, skeleton, meshes, mat, aim, setWorld, pose, reset, face, untwist, legIK, man, REST, restNormal, EXPR };
}
