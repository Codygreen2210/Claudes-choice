// Level 2/3 sample: real 3D crater + jointed 3D guy, built entirely in code.
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { BokehPass } from 'three/addons/postprocessing/BokehPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { mergeVertices } from 'three/addons/utils/BufferGeometryUtils.js';
import { FXAAShader } from 'three/addons/shaders/FXAAShader.js';
import { TexturePass } from 'three/addons/postprocessing/TexturePass.js';
import { FullScreenQuad } from 'three/addons/postprocessing/Pass.js';

const Q = new URLSearchParams(location.search);
const W = +Q.get('w') || 1080, H = +Q.get('h') || 1920;
const LEVEL = +(Q.get('level') || 2);
const FPS = 30;

// ------------------------------------------------------------------ noise
function hash3(x, y, z) {
  let h = Math.imul(x | 0, 374761393) ^ Math.imul(y | 0, 668265263) ^ Math.imul(z | 0, 1440662683);
  h = Math.imul(h ^ (h >>> 13), 1274126177); h ^= h >>> 16;
  return (h >>> 0) / 4294967296;
}
const sm = t => t * t * (3 - 2 * t);
function vnoise3(x, y, z) {
  const xi = Math.floor(x), yi = Math.floor(y), zi = Math.floor(z);
  const xf = sm(x - xi), yf = sm(y - yi), zf = sm(z - zi);
  let r = 0;
  for (let k = 0; k < 2; k++) for (let j = 0; j < 2; j++) for (let i = 0; i < 2; i++) {
    const w = (i ? xf : 1 - xf) * (j ? yf : 1 - yf) * (k ? zf : 1 - zf);
    r += w * hash3(xi + i, yi + j, zi + k);
  }
  return r * 2 - 1;
}
function fbm3(x, y, z, o = 5) {
  let a = 1, f = 1, s = 0, t = 0;
  for (let i = 0; i < o; i++) { s += a * vnoise3(x * f, y * f, z * f); t += a; a *= 0.5; f *= 2.03; }
  return s / t;
}
const clamp = (x, a, b) => Math.min(Math.max(x, a), b);
const smooth = (a, b, x) => { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
const lerp = (a, b, u) => a + (b - a) * u;
const D2R = Math.PI / 180;

// ------------------------------------------------------------------ renderer / scene
const renderer = new THREE.WebGLRenderer({ antialias: !['0', 'fxaa'].includes(Q.get('aa')), preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.setSize(W, H);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = Q.get('pcf') === '0' ? THREE.PCFShadowMap : THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
renderer.outputColorSpace = THREE.SRGBColorSpace;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x4a1e17, 0.0085);
const camera = new THREE.PerspectiveCamera(50, W / H, 0.05, 1200);

// ------------------------------------------------------------------ crater geometry
const SLOT = Math.PI / 2;                 // where he stands (+z)
function rawN(th, y) {
  const cx = Math.cos(th) * 2.8, cz = Math.sin(th) * 2.8;
  return fbm3(cx, cz, y * 0.07, 5) * 3.6 + 0.7 * Math.sin(y * 1.1 + fbm3(cx * 2, cz * 2, y * 0.2, 3) * 4);
}
function pitR(th, y) {
  const base = 34 + 2.2 * (-y / 80);
  let n = rawN(th, y);
  const dth = Math.abs(Math.atan2(Math.sin(th - SLOT), Math.cos(th - SLOT)));
  const k = smooth(0.04, 0.22, dth);
  if (k < 1) {   // under his spot the cliff never juts out past the edge: it undercuts
    const n0 = rawN(th, 0);
    const safe = Math.max(n, n0 + 0.5 * smooth(0, -3, y) + 0.6 * smooth(-3, -25, y));
    n = lerp(safe, n, k);
  }
  return base + n;
}
const ZEDGE = pitR(SLOT, 0);

function rockNormalMap(size = 512, seed = 1, scale = 8) {
  const h = new Float32Array(size * size);
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    const u = x / size, v = y / size;
    // tileable: sample on a torus
    const a = u * 2 * Math.PI, b = v * 2 * Math.PI;
    h[y * size + x] = fbm3(Math.cos(a) * scale / 6 + seed, Math.sin(a) * scale / 6, Math.cos(b) * scale / 6 + Math.sin(b) * scale / 6 * 0.7, 5);
  }
  const d = new Uint8Array(size * size * 4);
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    const hx = h[y * size + (x + 1) % size] - h[y * size + (x + size - 1) % size];
    const hy = h[((y + 1) % size) * size + x] - h[((y + size - 1) % size) * size + x];
    let nx = -hx * 6, ny = -hy * 6, nz = 1; const l = Math.hypot(nx, ny, nz);
    const i = (y * size + x) * 4;
    d[i] = (nx / l * 0.5 + 0.5) * 255; d[i + 1] = (ny / l * 0.5 + 0.5) * 255; d[i + 2] = (nz / l * 0.5 + 0.5) * 255; d[i + 3] = 255;
  }
  const t = new THREE.DataTexture(d, size, size, THREE.RGBAFormat);
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.needsUpdate = true; t.generateMipmaps = true;
  t.minFilter = THREE.LinearMipmapLinearFilter; t.magFilter = THREE.LinearFilter;
  return t;
}
const ROCKN = rockNormalMap();

function rockColor(y, n, n2) {
  // basalt with strata, oxidised red near the lake, sulphur yellow near the rim
  let c = new THREE.Color().setRGB(0.075, 0.062, 0.07);
  const strata = 0.5 + 0.5 * Math.sin(y * 0.9 + n * 5);
  c.lerp(new THREE.Color().setRGB(0.16, 0.12, 0.11), strata * 0.5);
  c.multiplyScalar(0.75 + 0.5 * (n2 * 0.5 + 0.5));
  const ox = smooth(-45, -78, y) * (0.5 + 0.5 * n);
  c.lerp(new THREE.Color().setRGB(0.28, 0.07, 0.03), clamp(ox, 0, 0.8));
  const sul = smooth(-6, 0, y) * smooth(0.35, 0.75, n2 * 0.5 + 0.5);
  c.lerp(new THREE.Color().setRGB(0.55, 0.47, 0.12), sul * 0.55);
  return c;
}


// split a grid mesh into tiles that share one vertex buffer, so off-screen tiles are culled
function tiles(g, mat, NC, NRW, tc, tr, order, shadow) {
  const pos = g.attributes.position;
  const grp = new THREE.Group();
  for (let ty = 0; ty < tr; ty++) for (let tx = 0; tx < tc; tx++) {
    const i0 = Math.floor(tx * NC / tc), i1 = Math.floor((tx + 1) * NC / tc);
    const j0 = Math.floor(ty * NRW / tr), j1 = Math.floor((ty + 1) * NRW / tr);
    const idx = []; const box = new THREE.Box3(); const v = new THREE.Vector3();
    for (let j = j0; j < j1; j++) for (let i = i0; i < i1; i++) {
      const a = j * (NC + 1) + i, b = a + 1, c = a + NC + 1, d = c + 1;
      idx.push(...order(a, b, c, d));
      for (const k of [a, b, c, d]) box.expandByPoint(v.fromBufferAttribute(pos, k));
    }
    const sg = new THREE.BufferGeometry();
    for (const name in g.attributes) sg.setAttribute(name, g.attributes[name]);
    sg.setIndex(idx);
    sg.boundingBox = box; sg.boundingSphere = box.getBoundingSphere(new THREE.Sphere());
    const m = new THREE.Mesh(sg, mat); m.receiveShadow = true; m.castShadow = shadow;
    grp.add(m);
  }
  return grp;
}

function buildWall() {
  const GQ = Q.get('geo') === 'half' ? 0.5 : 1;
  const NT = Math.round(360 * GQ), NY = Math.round(220 * GQ), Y0 = -84, Y1 = 0;
  const pos = [], col = [], uv = [], idx = [];
  for (let j = 0; j <= NY; j++) {
    const y = Y0 + (Y1 - Y0) * j / NY;
    for (let i = 0; i <= NT; i++) {
      const th = (i / NT) * 2 * Math.PI;
      const r = pitR(th, y);
      pos.push(Math.cos(th) * r, y, Math.sin(th) * r);
      const n = fbm3(Math.cos(th) * 6, Math.sin(th) * 6, y * 0.15, 4), n2 = fbm3(Math.cos(th) * 20, Math.sin(th) * 20, y * 0.5, 3);
      const c = rockColor(y, n, n2); col.push(c.r, c.g, c.b);
      uv.push(i / NT * 60, y / 6);
    }
  }
  for (let j = 0; j < NY; j++) for (let i = 0; i < NT; i++) {
    const a = j * (NT + 1) + i, b = a + 1, c = a + NT + 1, d = c + 1;
    idx.push(a, c, b, b, c, d);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx); g.computeVertexNormals();
  const m = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.93, metalness: 0, normalMap: ROCKN, normalScale: new THREE.Vector2(1.6, 1.6), side: THREE.DoubleSide });
  m.onBeforeCompile = sh => {       // heat glow soaking up the wall from the lake
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying float vWY;').replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvWY = (modelMatrix * vec4(transformed, 1.0)).y;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying float vWY;').replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\ntotalEmissiveRadiance += vec3(1.0, 0.28, 0.06) * (0.02 + 0.32 * pow(smoothstep(-2.0, -80.0, vWY), 1.8)) * (0.6 + 0.4 * diffuseColor.r * 4.0);');
  };
  return tiles(g, m, NT, NY, 24, 4, (a, b, c, d) => [a, c, b, b, c, d], false);
}

function groundH(r, th) {
  const rin = pitR(th, 0);
  const d = r - rin;
  const near = Math.hypot(Math.cos(th) * r, Math.sin(th) * r - ZEDGE);
  const flat = smooth(1.2, 6, near);
  return 0.04 * fbm3(Math.cos(th) * r * 0.9, Math.sin(th) * r * 0.9, 3.3, 3) + flat * (d * 0.035 + 1.6 * fbm3(Math.cos(th) * r * 0.06, Math.sin(th) * r * 0.06, 7, 4) * smooth(2, 25, d));
}

function buildGround() {
  const GQ = Q.get('geo') === 'half' ? 0.5 : 1;
  const NT = Math.round(360 * GQ), NR = Math.round(140 * GQ);
  const pos = [], col = [], uv = [], idx = [];
  for (let j = 0; j <= NR; j++) {
    for (let i = 0; i <= NT; i++) {
      const th = (i / NT) * 2 * Math.PI;
      const rin = pitR(th, 0);
      const u = j / NR;
      const r = rin + Math.pow(u, 2.2) * 260;
      const y = groundH(r, th);
      pos.push(Math.cos(th) * r, y, Math.sin(th) * r);
      const n = fbm3(Math.cos(th) * r * 0.3, Math.sin(th) * r * 0.3, 1, 3);
      const c = rockColor(0.0, n, fbm3(Math.cos(th) * r * 0.8, Math.sin(th) * r * 0.8, 2, 3));
      col.push(c.r, c.g, c.b);
      uv.push(Math.cos(th) * r / 3, Math.sin(th) * r / 3);
    }
  }
  for (let j = 0; j < NR; j++) for (let i = 0; i < NT; i++) {
    const a = j * (NT + 1) + i, b = a + 1, c = a + NT + 1, d = c + 1;
    idx.push(a, b, c, b, d, c);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx); g.computeVertexNormals();
  const m = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.95, normalMap: ROCKN, normalScale: new THREE.Vector2(1.3, 1.3) });
  return tiles(g, m, NT, NR, 24, 3, (a, b, c, d) => [a, b, c, b, d, c], false);
}

function rockMesh(r, seed, detail = 3) {
  let g = new THREE.IcosahedronGeometry(r, detail);
  g.deleteAttribute('normal'); g.deleteAttribute('uv'); g = mergeVertices(g);
  const p = g.attributes.position;
  for (let i = 0; i < p.count; i++) {
    const v = new THREE.Vector3().fromBufferAttribute(p, i);
    const n = v.clone().normalize();
    const k = 1 + 0.32 * fbm3(n.x * 2 + seed, n.y * 2, n.z * 2, 4) + 0.08 * fbm3(n.x * 9, n.y * 9 + seed, n.z * 9, 2);
    v.copy(n.multiplyScalar(r * k)); v.y *= 0.75;
    p.setXYZ(i, v.x, v.y, v.z);
  }
  g.computeVertexNormals();
  const m = new THREE.MeshStandardMaterial({ color: 0x1d171b, roughness: 0.9, normalMap: ROCKN, normalScale: new THREE.Vector2(1.2, 1.2) });
  const mesh = new THREE.Mesh(g, m); mesh.castShadow = true; mesh.receiveShadow = true;
  return mesh;
}

// ------------------------------------------------------------------ shared noise texture: one fetch instead of four sin() hashes
const NOISE = (() => {
  const n = 256, d = new Uint8Array(n * n * 4);
  for (let i = 0; i < n * n * 4; i++) d[i] = Math.floor(hash3(i, 77, 13) * 256);
  const t = new THREE.DataTexture(d, n, n, THREE.RGBAFormat);
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.magFilter = THREE.LinearFilter; t.minFilter = THREE.LinearFilter;
  t.generateMipmaps = false; t.needsUpdate = true; return t;
})();
const GLSL_NOISE = `
    float h1(vec2 p){ vec3 p3=fract(vec3(p.xyx)*.1031); p3+=dot(p3,p3.yzx+33.33); return fract((p3.x+p3.y)*p3.z); }
    vec2 h2(vec2 p){ vec3 p3=fract(vec3(p.xyx)*vec3(.1031,.1030,.0973)); p3+=dot(p3,p3.yzx+33.33); return fract((p3.xx+p3.yz)*p3.zy); }
    float vn(vec2 p){ vec2 i=floor(p), f=fract(p); f=f*f*(3.-2.*f);
      return mix(mix(h1(i),h1(i+vec2(1,0)),f.x),mix(h1(i+vec2(0,1)),h1(i+vec2(1,1)),f.x),f.y); }`;   // backend-stable hash (no sin)

// ------------------------------------------------------------------ lava lake shader
const lavaUniforms = { uNoise: { value: NOISE }, uTime: { value: 0 }, uSim: { value: null }, uUseSim: { value: 0 }, uBoost: { value: 1.0 } };
const lavaMat = new THREE.ShaderMaterial({
  defines: { LAVA_OCT: +(Q.get('oct') || 5) },
  uniforms: lavaUniforms,
  vertexShader: `varying vec3 vW; varying vec2 vUv; void main(){ vUv=uv; vec4 w=modelMatrix*vec4(position,1.); vW=w.xyz; gl_Position=projectionMatrix*viewMatrix*w; }`,
  fragmentShader: `
    uniform float uTime; uniform sampler2D uSim; uniform float uUseSim; uniform float uBoost;
    varying vec3 vW; varying vec2 vUv;
    ${GLSL_NOISE}
    float fbm(vec2 p){ float s=0., a=.5; for(int i=0;i<LAVA_OCT;i++){ s+=a*vn(p); p*=2.03; a*=.5; } return s*(LAVA_OCT==5?1.:1.0/(1.0-pow(.5,float(LAVA_OCT)))*0.96875); }
    vec2 vor(vec2 x){
      #ifdef NOVOR
      return vec2(0.,fract(x.x));
      #endif
      vec2 n=floor(x), f=fract(x); float F1=8., F2=8.;
      for(int j=-1;j<=1;j++) for(int i=-1;i<=1;i++){ vec2 g=vec2(float(i),float(j)); vec2 o=h2(n+g); o=.5+.42*sin(uTime*.35+6.2831*o);
        vec2 r=g+o-f; float d=dot(r,r); if(d<F1){F2=F1;F1=d;} else if(d<F2){F2=d;} }
      return vec2(sqrt(F1),sqrt(F2)); }
    vec3 ramp(float h){
      vec3 c=mix(vec3(.015,.008,.008), vec3(.45,.03,.0), smoothstep(.05,.35,h));
      c=mix(c, vec3(1.,.28,.02)*2.2, smoothstep(.35,.7,h));
      c=mix(c, vec3(1.,.72,.3)*4., smoothstep(.8,1.,h));
      return c; }
    void main(){
      vec2 p=vW.xz*.11 + vec2(uTime*.015, uTime*.008);
      float heat;
      if(uUseSim>.5){
        vec2 uv=vW.xz/80.+.5;
        float crust=texture2D(uSim, uv).r;
        heat = 1.-crust;
        heat += .12*fbm(p*6.+uTime*.3)-.06;
      } else {
        vec2 q=p*.75;
        vec2 wp=vec2(fbm(q*1.1), fbm(q*1.1+7.))*.38;
        vec2 v=vor(q+wp);
        float e=v.y-v.x;
        float w=.012+.03*fbm(q*3.+3.);
        float crack=smoothstep(w, 0., e);
        float halo=smoothstep(w*3.5, 0., e)*.25;
        float c2m=smoothstep(.45,.75,fbm(q*1.5+1.)); float c2=0.;
        if(c2m>0.){ vec2 v2=vor(q*2.6+wp+4.); float e2=v2.y-v2.x; c2=smoothstep(.02, 0., e2)*.5*c2m; }
        float pool=smoothstep(.62,.8,fbm(q*.7+vec2(uTime*.03,0.)));     // torn crust: open hot lava
        heat=min(max(max(crack*.86, c2), pool*.72)*(.85+.2*fbm(p*3.+uTime*.25)) + halo*.7 + .07*fbm(p*9.), .9);
      }
      vec3 c=ramp(clamp(heat,0.,1.))*uBoost;
      c += vec3(.06,.008,0.)*fbm(p*14.);
      gl_FragColor=vec4(c,1.);
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
    }`,
});
const lava = new THREE.Mesh(new THREE.CircleGeometry(42, 128), lavaMat);
lava.rotation.x = -Math.PI / 2; lava.position.y = -80;
scene.add(lava);

// ------------------------------------------------------------------ sky
const sky = new THREE.Mesh(new THREE.SphereGeometry(900, 48, 24), new THREE.ShaderMaterial({
  uniforms: { uNoise: { value: NOISE } },
  side: THREE.BackSide, depthWrite: false, fog: false,
  vertexShader: `varying vec3 vD; void main(){ vD=normalize(position); gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
  fragmentShader: `varying vec3 vD;
    ${GLSL_NOISE}
    float fbm(vec2 p){ float s=0., a=.5; for(int i=0;i<5;i++){ s+=a*vn(p); p*=2.03; a*=.5; } return s; }
    void main(){ float y=vD.y;
      vec3 zen=vec3(.07,.05,.16), mid=vec3(.32,.13,.25), hor=vec3(1.2,.42,.2);
      vec3 c = y>0. ? mix(mix(hor,mid,smoothstep(0.,.22,y)), zen, smoothstep(.18,.8,y)) : mix(hor*.6, vec3(.05,.02,.03), smoothstep(0.,-.2,y));
      vec2 q=vD.xz/(abs(y)+.25)*2.;
      float cl=smoothstep(.45,.8,fbm(q+3.)); c=mix(c, c*vec3(1.3,.8,.75)+vec3(.12,.04,.03), cl*.6*smoothstep(-.02,.15,y));
      gl_FragColor=vec4(c,1.);
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
    }`,
}));
sky.renderOrder = 10;
scene.add(sky);

// ------------------------------------------------------------------ lights
const hemi = new THREE.HemisphereLight(0x8a7ab8, 0x7a2a14, 0.6); scene.add(hemi);
const sun = new THREE.DirectionalLight(0xffa585, 1.6);
sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
sun.shadow.camera.left = -4; sun.shadow.camera.right = 4; sun.shadow.camera.top = 4; sun.shadow.camera.bottom = -4;
sun.shadow.camera.near = 1; sun.shadow.camera.far = 60; sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.02;
scene.add(sun); scene.add(sun.target);
const lavaLight = new THREE.PointLight(0xff5a1e, 14000, 0, 2); lavaLight.position.set(0, -70, 0); scene.add(lavaLight);
const lavaLight2 = new THREE.PointLight(0xff7a30, 4000, 0, 2); lavaLight2.position.set(14, -74, -10); scene.add(lavaLight2);
const bounce = new THREE.PointLight(0xff6a28, 0, 0, 2); scene.add(bounce);   // lake glow reaching him
const uplight = new THREE.DirectionalLight(0xff5c22, 1.0); scene.add(uplight); scene.add(uplight.target);   // the lake as a big area light from below

const WALL = buildWall();
scene.add(WALL);
function ridged(x, y, z, o = 5) { let a = 1, f = 1, s = 0, t = 0; for (let i = 0; i < o; i++) { s += a * (1 - Math.abs(vnoise3(x * f, y * f, z * f))); t += a; a *= 0.5; f *= 2.1; } return s / t; }
function buildCliff() {          // a high-detail rock face where the camera looks
  const GQ = Q.get('geo') === 'half' ? 0.5 : 1;
  const NT = Math.round(260 * GQ), NY = Math.round(300 * GQ), TH = 0.22, Y0 = -22, Y1 = 0.0;
  const pos = [], col = [], uv = [], idx = [];
  for (let j = 0; j <= NY; j++) {
    const y = Y0 + (Y1 - Y0) * j / NY;
    for (let i = 0; i <= NT; i++) {
      const th = SLOT - TH + 2 * TH * i / NT;
      const R = pitR(th, y);
      const ax = th * R;
      const rd = Math.pow(ridged(ax * 0.55, y * 0.42, 5.5, 5), 2.2);
      const fine = fbm3(ax * 3, y * 3, 9, 3);
      const blend = smooth(0, 0.35, Math.min(i, NT - i) / NT) * smooth(0, 0.3, Math.min(j, NY - j) / NY) * smooth(-0.05, -0.6, y);
      const d = (0.85 * rd + 0.12 * fine) * blend * lerp(0.35, 1, smooth(-3, -14, y));
      const r = R - 0.04 - d;
      pos.push(Math.cos(th) * r, y, Math.sin(th) * r);
      const n = fbm3(ax * 0.3, y * 0.3, 1, 4), n2 = fbm3(ax * 1.5, y * 1.5, 2, 3);
      const c = rockColor(y, n, n2); const k = 0.35 + 1.3 * clamp(d, 0, 1) * (0.7 + 0.3 * Math.sin(y * 2.3 + n * 3));
      col.push(c.r * k, c.g * k, c.b * k);
      uv.push(ax / 2, y / 2);
    }
  }
  for (let j = 0; j < NY; j++) for (let i = 0; i < NT; i++) {
    const a = j * (NT + 1) + i, b = a + 1, c = a + NT + 1, d = c + 1;
    idx.push(a, c, b, b, c, d);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx); g.computeVertexNormals();
  const wall = WALL.children[0];
  const m = wall.material.clone(); m.onBeforeCompile = wall.material.onBeforeCompile; m.normalScale = new THREE.Vector2(2.2, 2.2);
  return tiles(g, m, NT, NY, 4, 4, (a, b, c, d) => [a, c, b, b, c, d], false);
}
scene.add(buildCliff());
scene.add(buildGround());
// boulders on the rim
for (let i = 0; i < 70; i++) {
  const th = SLOT + (hash3(i, 1, 2) - 0.5) * 1.2;
  const r = pitR(th, 0) + 0.6 + Math.pow(hash3(i, 3, 4), 1.5) * 18;
  const near = Math.hypot(Math.cos(th) * r, Math.sin(th) * r - ZEDGE);
  if (near < 1.4) continue;
  const s = 0.08 + Math.pow(hash3(i, 5, 6), 3) * 0.9;
  const m = rockMesh(s, i, 2);
  m.position.set(Math.cos(th) * r, groundH(r, th) + s * 0.25, Math.sin(th) * r);
  m.rotation.set(hash3(i, 7, 1) * 6, hash3(i, 8, 1) * 6, 0);
  scene.add(m);
}

// ------------------------------------------------------------------ the guy
const MAT = {
  skin: new THREE.MeshPhysicalMaterial({ color: 0xd99a7c, roughness: 0.55, sheen: 0.12, sheenColor: new THREE.Color(0xffb099), sheenRoughness: 0.6 }),
  iris: new THREE.MeshPhysicalMaterial({ color: 0x5a3a1c, roughness: 0.2, clearcoat: 1 }),
  shirt: new THREE.MeshPhysicalMaterial({ color: 0x1fae9b, roughness: 0.85, sheen: 0.8, sheenRoughness: 0.6, sheenColor: new THREE.Color(0x77ffe6) }),
  jeans: new THREE.MeshStandardMaterial({ color: 0x4068bd, roughness: 0.9, normalMap: ROCKN, normalScale: new THREE.Vector2(0.25, 0.25) }),
  shoe: new THREE.MeshStandardMaterial({ color: 0x3a2d31, roughness: 0.55 }),
  sole: new THREE.MeshStandardMaterial({ color: 0xd9d2c8, roughness: 0.7 }),
  hair: new THREE.MeshStandardMaterial({ color: 0x5b351f, roughness: 0.62 }),
  eye: new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.15, clearcoat: 1 }),
  pupil: new THREE.MeshPhysicalMaterial({ color: 0x0b0608, roughness: 0.1, clearcoat: 1 }),
  mouth: new THREE.MeshStandardMaterial({ color: 0x3d0b14, roughness: 0.7 }),
  teeth: new THREE.MeshStandardMaterial({ color: 0xf6f1e8, roughness: 0.35 }),
  tongue: new THREE.MeshStandardMaterial({ color: 0xd9566a, roughness: 0.5 }),
  brow: new THREE.MeshStandardMaterial({ color: 0x3a2014, roughness: 0.8 }),
};
const FLAP = { uFlap: { value: 0 }, uT: { value: 0 } };
if (LEVEL >= 3) MAT.shirt.onBeforeCompile = sh => {
  Object.assign(sh.uniforms, FLAP);
  sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nuniform float uFlap; uniform float uT;')
    .replace('#include <begin_vertex>', `#include <begin_vertex>
      float hem = 1.0 - smoothstep(0.0, 0.32, position.y);
      float wv = sin(position.y * 38.0 + uT * 31.0 + position.x * 24.0) * 0.6 + sin(position.x * 41.0 - uT * 23.0 + position.z * 30.0) * 0.4;
      transformed += normal * uFlap * wv * (0.004 + 0.016 * hem);`);
};
const BL = { torso: 0.52, head: 0.135, ua: 0.30, fa: 0.27, th: 0.43, sh: 0.42 };
const Yax = new THREE.Vector3(0, 1, 0);

function cap(r, len, mat, seg = 24) {
  const m = new THREE.Mesh(new THREE.CapsuleGeometry(r, len, 8, seg), mat);
  m.castShadow = true; m.receiveShadow = true; scene.add(m); return m;
}
function lathe(prof, mat, seg = 28) {
  const g = new THREE.LatheGeometry(prof.map(([r, y]) => new THREE.Vector2(r, y)), seg);
  g.computeVertexNormals();
  const m = new THREE.Mesh(g, mat); m.castShadow = true; m.receiveShadow = true; scene.add(m); return m;
}
function limbProf(r0, r1, len, bulge = 0, n = 14) {
  const p = [];
  for (let i = 0; i <= 6; i++) { const a = -Math.PI / 2 + (i / 6) * Math.PI / 2; p.push([Math.cos(a) * r0 + 1e-4, Math.sin(a) * r0]); }
  for (let i = 1; i < n; i++) { const u = i / n; p.push([lerp(r0, r1, u) + bulge * Math.sin(Math.PI * Math.pow(u, 0.8)), u * len]); }
  for (let i = 0; i <= 6; i++) { const a = (i / 6) * Math.PI / 2; p.push([Math.cos(a) * r1 + 1e-4, len + Math.sin(a) * r1]); }
  return p;
}
function limb(r0, r1, len, bulge, mat) { const m = lathe(limbProf(r0, r1, len, bulge), mat); m.userData.base = true; return m; }
function placeSeg(m, a, b) {
  if (m.userData.base) { const d = new THREE.Vector3().subVectors(b, a).normalize(); m.position.copy(a); m.quaternion.setFromUnitVectors(Yax, d); return; }
  const d = new THREE.Vector3().subVectors(b, a); const L = d.length();
  m.position.copy(a).addScaledVector(d, 0.5);
  m.quaternion.setFromUnitVectors(Yax, d.multiplyScalar(1 / L));
}
const guy = {};
guy.torso = lathe([[0.001, 0.02], [0.13, 0.03], [0.152, 0.06], [0.146, 0.16], [0.158, 0.26], [0.172, 0.34], [0.17, 0.40], [0.152, 0.445], [0.11, 0.48], [0.06, 0.505], [0.001, 0.51]], MAT.shirt, 40);
guy.torso.scale.set(1.2, 1, 0.66);
guy.pelvis = lathe([[0.001, -0.1], [0.1, -0.095], [0.145, -0.05], [0.158, 0.02], [0.152, 0.075], [0.001, 0.08]], MAT.jeans, 36); guy.pelvis.scale.set(1.18, 1, 0.7);
guy.neck = cap(0.05, 0.08, MAT.skin);
for (const s of ['N', 'F']) {
  guy['ua' + s] = limb(0.072, 0.058, BL.ua, 0.006, MAT.shirt);
  guy['fa' + s] = limb(0.047, 0.036, BL.fa, 0.008, MAT.skin);
  guy['th' + s] = limb(0.092, 0.066, BL.th, 0.01, MAT.jeans);
  guy['sh' + s] = limb(0.066, 0.05, BL.sh, 0.009, MAT.jeans);
  guy['cuff' + s] = new THREE.Mesh(new THREE.TorusGeometry(0.06, 0.012, 10, 28), MAT.shirt); guy['cuff' + s].castShadow = true; scene.add(guy['cuff' + s]);
  const hand = new THREE.Group(); scene.add(hand);
  const palm = new THREE.Mesh(new THREE.SphereGeometry(0.048, 24, 16), MAT.skin); palm.scale.set(1, 1.15, 0.55); palm.position.y = 0.045; palm.castShadow = true; hand.add(palm);
  for (let k = 0; k < 4; k++) {
    const f = new THREE.Mesh(new THREE.CapsuleGeometry(0.0125, 0.05, 4, 10), MAT.skin);
    const a = (-0.3 + 0.2 * k);
    f.position.set(Math.sin(a) * 0.05, 0.1 + Math.cos(a) * 0.02, 0); f.rotation.z = -a * 1.4; f.castShadow = true; hand.add(f);
  }
  const th = new THREE.Mesh(new THREE.CapsuleGeometry(0.013, 0.04, 4, 10), MAT.skin); th.position.set(0.045, 0.045, -0.02); th.rotation.z = -1.1; hand.add(th);
  guy['hand' + s] = hand;
  const shoe = new THREE.Group(); scene.add(shoe);
  const up = new THREE.Mesh(new THREE.CapsuleGeometry(0.055, 0.17, 6, 20), MAT.shoe); up.rotation.x = Math.PI / 2; up.scale.set(1.05, 1, 0.78); up.castShadow = true; shoe.add(up);
  const so = new THREE.Mesh(new THREE.CapsuleGeometry(0.058, 0.18, 6, 20), MAT.sole); so.rotation.x = Math.PI / 2; so.scale.set(1.08, 1, 0.3); so.position.y = -0.035; shoe.add(so);
  guy['shoe' + s] = shoe;
}
// head (local: up = +y, forward = -z)
const head = new THREE.Group(); scene.add(head); guy.head = head;
{
  const add = (geo, mat, p, s = [1, 1, 1], r = [0, 0, 0]) => { const m = new THREE.Mesh(geo, mat); m.position.set(...p); m.scale.set(...s); m.rotation.set(...r); m.castShadow = true; m.receiveShadow = true; head.add(m); return m; };
  add(new THREE.SphereGeometry(0.13, 40, 28), MAT.skin, [0, 0.01, 0], [0.93, 1.05, 1.0]);
  add(new THREE.SphereGeometry(0.11, 32, 20), MAT.skin, [0, -0.05, -0.025], [0.96, 0.82, 0.95]);
  for (const sx of [-1, 1]) {
    add(new THREE.SphereGeometry(0.03, 16, 12), MAT.skin, [sx * 0.122, 0.0, 0.0], [0.5, 1, 0.8]);
    add(new THREE.SphereGeometry(0.04, 28, 20), MAT.eye, [sx * 0.05, 0.022, -0.1], [1, 1.22, 0.62]);
    add(new THREE.SphereGeometry(0.019, 20, 14), MAT.iris, [sx * 0.05, 0.022, -0.122], [1, 1.1, 0.45]);
    guy['pupil' + sx] = add(new THREE.SphereGeometry(0.0105, 16, 12), MAT.pupil, [sx * 0.05, 0.022, -0.1285], [1, 1.1, 0.4]);
    guy['brow' + sx] = add(new THREE.CapsuleGeometry(0.011, 0.05, 4, 8), MAT.brow, [sx * 0.05, 0.085, -0.115], [1, 1, 1], [0, 0, Math.PI / 2 - sx * 0.38]);
  }
  add(new THREE.SphereGeometry(0.022, 16, 12), MAT.skin, [0, -0.005, -0.13], [0.8, 1, 1.15]);
  guy.mouth = add(new THREE.SphereGeometry(0.04, 24, 16), MAT.mouth, [0, -0.072, -0.1], [0.85, 1.0, 0.45]);
  guy.teeth = add(new THREE.BoxGeometry(0.05, 0.012, 0.02), MAT.teeth, [0, -0.045, -0.112]);
  guy.tongue = add(new THREE.SphereGeometry(0.026, 16, 12), MAT.tongue, [0, -0.1, -0.104], [1, 0.4, 1]);
  const hair = new THREE.Group(); head.add(hair); guy.hair = hair;
  const capm = new THREE.Mesh(new THREE.SphereGeometry(0.142, 36, 20, 0, Math.PI * 2, 0, Math.PI * 0.55), MAT.hair);
  capm.position.set(0, 0.02, 0.008); capm.rotation.x = 0.25; capm.castShadow = true; hair.add(capm);
  for (let i = 0; i < 22; i++) {
    const a = (i / 22) * Math.PI * 2 + hash3(i, 2, 2) * 0.3, el = 0.25 + 0.55 * hash3(i, 9, 9);
    const c = new THREE.Mesh(new THREE.SphereGeometry(0.05, 14, 10), MAT.hair);
    const dir = new THREE.Vector3(Math.cos(a) * Math.cos(el), Math.sin(el), Math.sin(a) * Math.cos(el) * 0.95 + 0.3).normalize();
    if (dir.z < -0.3 && dir.y < 0.8) continue;           // keep the forehead clear
    c.position.copy(dir.clone().multiplyScalar(0.125)).add(new THREE.Vector3(0, 0.035, 0.012));
    c.scale.set(0.75, 0.55, 1.55);
    c.lookAt(c.position.clone().add(new THREE.Vector3(0, 0.25, 1).add(dir).normalize()));
    c.castShadow = true; hair.add(c);
  }
}

// ------------------------------------------------------------------ choreography (same beats as the 2D samples)
const KEYS = [   // t, hip(x2d,y), torso, head, uaN, faN, uaF, faF, thN, shN, thF, shF, mouth, armSpread
  [0.00, -0.43, 0.925, 81, 64, -82, -70, -100, -96, -73, -77, -101, -104, 0.05, 8],
  [0.62, -0.39, 0.915, 73, 50, -70, -48, -104, -92, -72, -79, -99, -104, 0.1, 8],
  [0.76, -0.38, 0.91, 72, 52, -68, -46, -104, -92, -72, -79, -99, -104, 0.2, 8],
  [0.88, -0.31, 0.80, 64, 98, 35, 72, 140, 112, -48, -82, -112, -104, 0.85, 28],
  [1.06, -0.15, 0.60, 38, 78, 112, 150, 22, -12, -42, -66, -128, -146, 1.0, 30],
  [1.30, 0.12, 0.34, 4, 30, 176, 205, 124, 146, -152, -174, 172, 150, 1.0, 35],
];
const T_AIR = 1.30, G = 9.81, VX = 0.9, VY = -1.2, CRACK = 0.76;

function keyAt(t) {
  if (t <= KEYS[0][0]) return KEYS[0].slice(1);
  for (let i = 0; i < KEYS.length - 1; i++) {
    const a = KEYS[i], b = KEYS[i + 1];
    if (t <= b[0]) { const u = sm(clamp((t - a[0]) / (b[0] - a[0]), 0, 1)); return a.slice(1).map((v, k) => lerp(v, b[k + 1], u)); }
  }
  return KEYS[KEYS.length - 1].slice(1);
}
function hipWorld(t) {
  let x2, y;
  if (t <= T_AIR) { const k = keyAt(t); x2 = k[0]; y = k[1]; }
  else { const tau = t - T_AIR; x2 = 0.12 + VX * tau; y = 0.34 + VY * tau - 0.5 * G * tau * tau; }
  return new THREE.Vector3(0, y, ZEDGE - x2);
}
function depth(t) { return -hipWorld(t).y; }

// pose in body frame: angles (deg) in sagittal plane (0 = forward, 90 = up) + spread out to the side
function poseAt(t) {
  const k = keyAt(Math.min(t, T_AIR));
  const torso = k[2];
  let p = 90 - torso;                    // forward pitch of the body
  const toBody = a => a + p;
  let P = {
    head: toBody(k[3]), uaN: toBody(k[4]), faN: toBody(k[5]), uaF: toBody(k[6]), faF: toBody(k[7]),
    thN: toBody(k[8]), shN: toBody(k[9]), thF: toBody(k[10]), shF: toBody(k[11]),
    mouth: k[12], armS: k[13], legS: 4, roll: 0, yaw: 0, pitch: p, hairWind: 0,
  };
  if (t > T_AIR) {
    const tau = t - T_AIR, u = smooth(0, 0.45, tau);
    const F = {
      head: 92 + 6 * Math.sin(4 * tau),
      uaN: 150 + 20 * Math.sin(9 * tau), faN: 170 + 28 * Math.sin(9 * tau + 1.2),
      uaF: 150 - 20 * Math.sin(9 * tau + 0.6), faF: 170 - 28 * Math.sin(9 * tau + 1.8),
      thN: -100 + 14 * Math.sin(7 * tau), shN: -128 + 20 * Math.sin(7 * tau + 1),
      thF: -100 - 14 * Math.sin(7 * tau + 2), shF: -128 - 20 * Math.sin(7 * tau + 3),
    };
    for (const key in F) P[key] = lerp(P[key], F[key], u);
    P.armS = lerp(P.armS, 52 + 12 * Math.sin(5 * tau), u);
    P.legS = lerp(4, 20 + 6 * Math.sin(6 * tau), u);
    P.pitch = lerp(p + 40 * tau, 94 + 8 * Math.sin(1.3 * tau), u);
    P.roll = u * (14 * Math.sin(1.4 * tau) + 5 * Math.sin(3.1 * tau));
    P.yaw = u * 10 * Math.sin(0.8 * tau);
    P.mouth = 0.9 + 0.1 * Math.sin(11 * t);
    P.hairWind = u;
  }
  return P;
}
function bodyQ(P) {
  const q = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), P.yaw * D2R);
  q.multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1, 0, 0), -P.pitch * D2R));
  q.multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 0, 1), P.roll * D2R));
  return q;
}
function bdir(a, spread, side, q) {
  const s = spread * D2R, ar = a * D2R;
  const v = new THREE.Vector3(Math.sin(s) * side, Math.cos(s) * Math.sin(ar), -Math.cos(s) * Math.cos(ar));
  return v.applyQuaternion(q).normalize();
}

function poseGuy(t) {
  const P = poseAt(t), q = bodyQ(P), hip = hipWorld(t);
  const up = new THREE.Vector3(0, 1, 0).applyQuaternion(q), right = new THREE.Vector3(1, 0, 0).applyQuaternion(q);
  const fwd = new THREE.Vector3(0, 0, -1).applyQuaternion(q);
  const neck = hip.clone().addScaledVector(up, BL.torso);
  guy.torso.position.copy(hip); guy.torso.quaternion.copy(q);
  guy.pelvis.position.copy(hip).addScaledVector(up, 0.02); guy.pelvis.quaternion.copy(q);
  const hd = bdir(P.head, 0, 0, q);
  const headc = neck.clone().addScaledVector(hd, BL.head);
  placeSeg(guy.neck, neck.clone().addScaledVector(up, -0.05), neck.clone().addScaledVector(hd, 0.05));
  // head frame: up = hd, forward = perpendicular toward body forward
  const hf = fwd.clone().addScaledVector(hd, -fwd.dot(hd)).normalize();
  if ((P.head - 90) > 0) hf.applyAxisAngle(right, 0);
  const hr = new THREE.Vector3().crossVectors(hd, hf).normalize();     // right... (y x -z = x)
  const m4 = new THREE.Matrix4().makeBasis(hr.clone().negate(), hd, hf.clone().negate());
  head.position.copy(headc); head.quaternion.setFromRotationMatrix(m4);
  const mo = P.mouth;
  guy.mouth.scale.set(0.85, 0.35 + 0.9 * mo, 0.45); guy.mouth.position.y = -0.065 - 0.012 * mo;
  guy.teeth.position.y = -0.045 + 0.004 * mo; guy.tongue.position.y = -0.075 - 0.03 * mo;
  guy.tongue.visible = mo > 0.3; guy.teeth.visible = mo > 0.15;
  guy.hair.rotation.x = 0.4 * P.hairWind + 0.08 * Math.sin(t * 23) * P.hairWind;
  for (const sx of [-1, 1]) { guy['pupil' + sx].scale.set(t > 0.82 ? 0.7 : 1, t > 0.82 ? 0.77 : 1.1, 0.4); }
  for (const [s, side] of [['N', 1], ['F', -1]]) {
    const sh = hip.clone().addScaledVector(up, 0.455).addScaledVector(right, 0.2 * side);
    const el = sh.clone().addScaledVector(bdir(P['ua' + s], P.armS, side, q), BL.ua);
    const fad = bdir(P['fa' + s], P.armS * 0.6, side, q);
    const wr = el.clone().addScaledVector(fad, BL.fa);
    placeSeg(guy['ua' + s], sh, el); placeSeg(guy['fa' + s], el, wr);
    const ud = new THREE.Vector3().subVectors(el, sh).normalize();
    guy['cuff' + s].position.copy(sh).addScaledVector(ud, BL.ua - 0.01);
    guy['cuff' + s].quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), ud);
    const hand = guy['hand' + s]; hand.position.copy(wr);
    hand.quaternion.setFromUnitVectors(Yax, fad); hand.rotateY(side * 1.4);
    const hp = hip.clone().addScaledVector(right, 0.09 * side);
    const kn = hp.clone().addScaledVector(bdir(P['th' + s], P.legS, side, q), BL.th);
    const shd = bdir(P['sh' + s], P.legS * 0.5, side, q);
    const an = kn.clone().addScaledVector(shd, BL.sh);
    placeSeg(guy['th' + s], hp, kn); placeSeg(guy['sh' + s], kn, an);
    const foot = bdir(P['sh' + s] + 90, P.legS * 0.5, side, q);
    const shoe = guy['shoe' + s];
    shoe.position.copy(an).addScaledVector(foot, 0.075).addScaledVector(shd, 0.045);
    const fr = new THREE.Vector3().crossVectors(shd, foot).normalize();
    shoe.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(fr, shd.clone().negate(), foot.clone().negate()));
  }
  return { hip, P, q, headc };
}

// ------------------------------------------------------------------ the rock that gives way + pebbles
const chunk = rockMesh(0.17, 77, LEVEL >= 3 ? 5 : 3); chunk.scale.set(1.25, 0.9, 1.0); scene.add(chunk);
const CHUNK0 = new THREE.Vector3(0.09, -0.05, ZEDGE + 0.02);
const pebbles = [];
for (let i = 0; i < (LEVEL >= 3 ? 44 : 16); i++) {
  const m = rockMesh(0.02 + 0.03 * hash3(i, 2, 9), 100 + i, 1); scene.add(m);
  pebbles.push({ m, p0: new THREE.Vector3((hash3(i, 1, 1) - 0.5) * 0.4 + 0.09, -0.02 + hash3(i, 3, 3) * 0.05, ZEDGE + (hash3(i, 4, 4) - 0.3) * 0.3),
    v0: new THREE.Vector3((hash3(i, 5, 5) - 0.5) * 0.8, hash3(i, 6, 6) * 1.4, -0.2 - hash3(i, 7, 7) * 0.8), w: hash3(i, 8, 8) * 12 });
}
function debris(t) {
  const tau = Math.max(0, t - CRACK);
  chunk.position.copy(CHUNK0).add(new THREE.Vector3(0, -0.5 * G * tau * tau, -0.35 * tau));
  chunk.rotation.set(-2.4 * tau, 0.6 * tau, 0.3);
  for (const p of pebbles) {
    if (t < CRACK) { p.m.visible = false; continue; }
    p.m.visible = true;
    p.m.position.copy(p.p0).addScaledVector(p.v0, tau).add(new THREE.Vector3(0, -0.5 * G * tau * tau, 0));
    p.m.rotation.set(p.w * tau, p.w * 0.7 * tau, 0);
  }
}

// ------------------------------------------------------------------ embers + smoke
function softTex(seed) {
  const c = document.createElement('canvas'); c.width = c.height = 128; const g = c.getContext('2d');
  const im = g.createImageData(128, 128);
  for (let y = 0; y < 128; y++) for (let x = 0; x < 128; x++) {
    const dx = (x - 64) / 64, dy = (y - 64) / 64, r = Math.hypot(dx, dy);
    const n = 0.5 + 0.5 * fbm3(x / 22 + seed, y / 22, seed, 4);
    const a = clamp(1 - r, 0, 1) ** 1.6 * n;
    const i = (y * 128 + x) * 4; im.data[i] = im.data[i + 1] = im.data[i + 2] = 255; im.data[i + 3] = a * 255;
  }
  g.putImageData(im, 0, 0); const t = new THREE.CanvasTexture(c); return t;
}
const smokeT = softTex(3);
const smokes = [];
const wisps = [];
for (let i = 0; i < 9; i++) {      // heat wisps rising up the wall near him
  const mat = new THREE.SpriteMaterial({ map: smokeT, color: new THREE.Color(0.8, 0.45, 0.35), transparent: true, opacity: 0.0, depthWrite: false });
  const s = new THREE.Sprite(mat); scene.add(s); wisps.push({ s, x: (hash3(i, 4, 4) - 0.5) * 9, z: ZEDGE - 1.5 - hash3(i, 5, 4) * 4, ph: hash3(i, 6, 4), sz: 2.5 + hash3(i, 7, 4) * 3 });
}
for (let i = 0; i < (LEVEL >= 3 ? 40 : 18); i++) {
  const mat = new THREE.SpriteMaterial({ map: smokeT, color: new THREE.Color(0.55, 0.33, 0.3), transparent: true, opacity: 0.22, depthWrite: false, fog: true });
  const s = new THREE.Sprite(mat); scene.add(s);
  smokes.push({ s, th: hash3(i, 1, 7) * Math.PI * 2, r: 6 + hash3(i, 2, 7) * 24, y0: -78 + hash3(i, 3, 7) * 80, sp: 2 + hash3(i, 4, 7) * 3, sz: 10 + hash3(i, 5, 7) * 18 });
}
function updSmoke(t) {
  for (const o of wisps) {
    const u = (o.ph + t * 0.12) % 1;
    o.s.position.set(o.x + Math.sin(t + o.ph * 9) * 0.6, -14 + u * 16, o.z);
    o.s.scale.setScalar(o.sz * (0.6 + u));
    o.s.material.opacity = 0.18 * Math.sin(Math.PI * u);
    o.s.visible = o.s.material.opacity > 0.004 && !Q.get('nosmoke');
  }
  for (const o of smokes) {
    const y = ((o.y0 + 80 + o.sp * t) % 95) - 80;
    o.s.position.set(Math.cos(o.th + t * 0.03) * o.r, y, Math.sin(o.th + t * 0.03) * o.r);
    o.s.scale.setScalar(o.sz * (1 + (y + 80) / 120));
    o.s.material.opacity = 0.16 * smooth(-80, -70, y) * smooth(15, 0, y) * (LEVEL >= 3 ? 1.2 : 1);
    o.s.visible = o.s.material.opacity > 0.004 && !Q.get('nosmoke');
    o.s.material.color.setRGB(0.4 + 0.5 * smooth(-30, -78, y), 0.24 + 0.1 * smooth(-30, -78, y), 0.25);
  }
}
const NE = LEVEL >= 3 ? 1600 : 500;
const eGeo = new THREE.BufferGeometry(); const ePos = new Float32Array(NE * 3);
eGeo.setAttribute('position', new THREE.BufferAttribute(ePos, 3));
const eMat = new THREE.PointsMaterial({ color: new THREE.Color(3, 1.3, 0.35), size: LEVEL >= 3 ? 0.09 : 0.07, sizeAttenuation: true, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false });
scene.add(new THREE.Points(eGeo, eMat));
function updEmbers(t) {
  for (let i = 0; i < NE; i++) {
    const th = hash3(i, 11, 1) * Math.PI * 2, r = Math.sqrt(hash3(i, 12, 1)) * 34;
    const sp = 3 + hash3(i, 13, 1) * 6, ph = hash3(i, 14, 1) * 90;
    const y = ((ph + sp * t) % 90) - 80;
    ePos[i * 3] = Math.cos(th) * r + Math.sin(t * 1.3 + i) * 0.8;
    ePos[i * 3 + 1] = y;
    ePos[i * 3 + 2] = Math.sin(th) * r + Math.cos(t * 1.1 + i) * 0.8;
  }
  eGeo.attributes.position.needsUpdate = true;
}

// ------------------------------------------------------------------ cameras
const SHOTS = LEVEL >= 3 ? null : [[0, 1.86, 'A'], [1.86, 3.9, 'B'], [3.9, 99, 'C']];
const wallGap = t => 0.12 + VX * Math.max(0, t - T_AIR);   // his distance out from the cliff
function shake(t, amt, f = 1) {
  return new THREE.Vector3(vnoise3(t * 3 * f, 1, 0), vnoise3(t * 3 * f, 2, 0), vnoise3(t * 3 * f, 3, 0)).multiplyScalar(amt);
}
function camA(t) {
  const E = new THREE.Vector3(0, 0, ZEDGE);
  const k = smooth(0.8, 1.6, t);
  const lag = hipWorld(Math.max(0, t - 0.1));
  // from out over the pit: him on top of a sheer cliff, the wall falling away into the glow
  const push = smooth(0, 0.8, t);
  const look = E.clone().add(new THREE.Vector3(0, 0.15 - 0.2 * push, 0.35)).lerp(lag.clone().add(new THREE.Vector3(0, -0.4, 0)), k);
  const pos = E.clone().add(new THREE.Vector3(2.5 - 0.6 * push, -2.4 + 0.5 * push, -8.6 + 2.2 * push)).add(new THREE.Vector3(0, -2.2, 0.6).multiplyScalar(k));
  const sh = t > CRACK ? Math.exp(-(t - CRACK) * 5) * 0.035 : 0;
  pos.add(shake(t, 0.012 + sh, 3));
  camera.fov = 40; camera.up.set(0, 1, 0);
  camera.position.copy(pos); camera.lookAt(look);
}
function camB(t, t0) {
  const hip = hipWorld(t);
  const u = t - t0;
  camera.fov = 66; camera.up.set(Math.sin(u * 0.4) * 0.15, 0, -1);
  camera.position.copy(hip).add(new THREE.Vector3(0.35, -3.3 + 0.25 * u, -2.7)).add(shake(t, 0.05, 2));
  camera.lookAt(hip.clone().add(new THREE.Vector3(0, 0, -0.35)));
}
function camC(t, t0) {
  const hip = hipWorld(t);
  const u = t - t0;
  camera.fov = 55; camera.up.set(0, 0, -1);
  camera.position.copy(hip).add(new THREE.Vector3(1.5, 3.4 - 0.2 * u, Math.min(wallGap(t) - 1.0, 1.2))).add(shake(t, 0.05, 2.5));
  camera.lookAt(hip.clone().add(new THREE.Vector3(-0.2, -3.6, -0.8)));
}

// ------------------------------------------------------------------ level 3: time ramp, sim lava, dust, post, motion blur
function ACT(t) {                      // real time -> action time (slow motion on the slip)
  if (LEVEL < 3) return t;
  if (t < 0.62) return t;
  if (t < 1.22) return 0.62 + 0.4 * (t - 0.62);
  if (t < 1.5) { const u = t - 1.22; return 0.86 + 0.4 * u + 0.6 * u * u / 0.56; }
  return 1.056 + (t - 1.5);
}
let SIM = null, simTex = null;
if (LEVEL >= 3) {
  const buf = await (await fetch('/lava.bin')).arrayBuffer();
  SIM = new Uint8Array(buf); 
  simTex = new THREE.DataTexture(SIM.subarray(0, 512 * 512), 512, 512, THREE.RedFormat, THREE.UnsignedByteType);
  simTex.magFilter = THREE.LinearFilter; simTex.minFilter = THREE.LinearFilter; simTex.needsUpdate = true;
  lavaUniforms.uSim.value = simTex; lavaUniforms.uUseSim.value = Q.get('nosim') ? 0 : 1;
}
const kicker = new THREE.PointLight(0xff8a4a, 0, 4, 2); scene.add(kicker);   // a small warm kicker for the close-up
const dusts = [];
if (LEVEL >= 3) for (let i = 0; i < 70; i++) {
  const mat = new THREE.SpriteMaterial({ map: smokeT, color: new THREE.Color(0.42, 0.33, 0.3), transparent: true, opacity: 0, depthWrite: false });
  const sp = new THREE.Sprite(mat); scene.add(sp);
  const dir = new THREE.Vector3(hash3(i, 1, 5) - 0.5, hash3(i, 2, 5) * 0.8 - 0.1, -hash3(i, 3, 5) * 0.9).normalize();
  dusts.push({ sp, dir, sp0: 0.25 + hash3(i, 4, 5) * 0.9, sz: 0.03 + hash3(i, 5, 5) * 0.09 });
}
function updDust(a) {
  for (const d of dusts) {
    const tau = a - CRACK;
    if (tau < 0) { d.sp.material.opacity = 0; continue; }
    const dist = d.sp0 * (1 - Math.exp(-tau * 3)) / 3 * 3;
    d.sp.position.copy(CHUNK0).addScaledVector(d.dir, dist).add(new THREE.Vector3(0, -0.6 * tau * tau, 0));
    d.sp.scale.setScalar(d.sz * (1 + tau * 3));
    d.sp.material.opacity = 0.4 * Math.exp(-tau * 1.6) * smooth(0, 0.03, tau);
  }
}
const SHOTS3 = [[0, 0.62, 'A'], [0.62, 1.22, 'E'], [1.22, 1.95, 'M'], [1.95, 3.5, 'B'], [3.5, 99, 'C']];
let FOCUS = 9, APER = 0.003, HAZE = 0.5;
function camE(t, a) {                  // extreme close-up: boot on the crumbling lip
  const foot = guy.shoeN.position.clone();
  const u = t - 0.62;
  camera.fov = 30; camera.up.set(0, 1, 0);
  const base = new THREE.Vector3(0.09, 0.02, ZEDGE + 0.15);
  camera.position.copy(base).add(new THREE.Vector3(0.72 - 0.06 * u, 0.2 + 0.02 * u, -0.98 + 0.08 * u)).add(shake(t, 0.003, 2));
  const look = base.clone().add(new THREE.Vector3(0, 0.02, 0)).lerp(foot, 0.45);
  kicker.position.copy(camera.position).add(new THREE.Vector3(0.1, -0.45, 0.1)); kicker.intensity = 3.5;
  camera.lookAt(look);
  FOCUS = camera.position.distanceTo(look); APER = 0.03; HAZE = 0.35;
}
function camM(t, a) {                  // medium side shot as he pitches over the edge
  const hip = hipWorld(Math.max(0, a - 0.06));
  camera.fov = 44; camera.up.set(0, 1, 0);
  const u = t - 1.22;
  camera.position.set(2.5 - 0.3 * u, 0.5 - 1.6 * u, ZEDGE - 1.7 - 0.4 * u).add(shake(t, 0.02, 3));
  camera.lookAt(hip.clone().add(new THREE.Vector3(0, -0.15, 0)));
  FOCUS = camera.position.distanceTo(hip); APER = 0.006; HAZE = 0.5;
}

// ------------------------------------------------------------------ frame
function update(t) {
  const a = ACT(t);
  const g = poseGuy(a);
  debris(a); updSmoke(a); updEmbers(a); updDust(a);
  lavaUniforms.uTime.value = a;
  if (SIM) { const f = clamp(Math.round(t * FPS), 0, SIM.length / (512 * 512) - 1); simTex.image.data = SIM.subarray(f * 512 * 512, (f + 1) * 512 * 512); simTex.needsUpdate = true; }
  FLAP.uT.value = a; FLAP.uFlap.value = smooth(0.85, 1.5, a);
  const hip = g.hip;
  sun.position.copy(hip).add(new THREE.Vector3(-14, 9, 16)); sun.target.position.copy(hip);
  sun.target.updateMatrixWorld();
  uplight.position.copy(hip).add(new THREE.Vector3(0, -50, -38)); uplight.target.position.copy(hip); uplight.target.updateMatrixWorld();
  const dl = Math.max(80 - depth(a), 3);
  bounce.position.copy(hip).add(new THREE.Vector3(0, -Math.min(dl, 14), -7));
  bounce.intensity = 9000 * Math.pow(14 / (dl + 6), 2) * smooth(0.9, 2.2, a);
  let shot = 'A', t0 = 0;
  for (const [x0, x1, s] of (LEVEL >= 3 ? SHOTS3 : SHOTS)) if (t >= x0 && t < x1) { shot = s; t0 = x0; }
  if (shot === 'A') { camA(a); FOCUS = camera.position.distanceTo(hip); APER = 0.0025; HAZE = 0.45; }
  else if (shot === 'E') camE(t, a);
  else if (shot === 'M') camM(t, a);
  else if (shot === 'B') { camB(a, ACT(t0)); FOCUS = camera.position.distanceTo(hip); APER = 0.004; HAZE = 0.55; }
  else { camC(a, ACT(t0)); FOCUS = camera.position.distanceTo(hip); APER = 0.0025; HAZE = 1.0; }
  if (shot !== 'E') kicker.intensity = 0;
  if (LEVEL >= 3 && (shot === 'B' || shot === 'C')) camera.position.add(shake(t * 3.0, 0.035 * smooth(1.6, 3.5, a), 4));
  camera.aspect = W / H; camera.updateProjectionMatrix();
  if (composer && bokeh) {
    bokeh.uniforms.focus.value = FOCUS; bokeh.uniforms.aperture.value = APER; bokeh.uniforms.maxblur.value = 0.012;
    haze.uniforms.uTime.value = t; haze.uniforms.uAmt.value = HAZE;
  }
}

let composer = null, bokeh = null, haze = null;
// level 3 motion blur on the GPU: each sub-frame renders into sceneRT and is added into accRT
const accRT = LEVEL >= 3 ? new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, depthBuffer: false }) : null;
const sceneRT = LEVEL >= 3 ? new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType }) : null;
const accQuad = LEVEL >= 3 ? new FullScreenQuad(new THREE.ShaderMaterial({
  uniforms: { tMap: { value: null }, uW: { value: 1 } },
  vertexShader: 'varying vec2 vUv; void main(){ vUv=uv; gl_Position=vec4(position.xy,0.,1.); }',
  fragmentShader: 'uniform sampler2D tMap; uniform float uW; varying vec2 vUv; void main(){ gl_FragColor=texture2D(tMap,vUv)*uW; }',
  blending: THREE.CustomBlending, blendEquation: THREE.AddEquation, blendSrc: THREE.OneFactor, blendDst: THREE.OneFactor,
  blendSrcAlpha: THREE.OneFactor, blendDstAlpha: THREE.OneFactor, depthTest: false, depthWrite: false, transparent: true,
})) : null;
if (LEVEL < 3 && Q.get('aa') === 'fxaa') {     // level 2: cheap edge smoothing instead of 4x MSAA
  composer = new EffectComposer(renderer, new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType }));
  composer.addPass(new RenderPass(scene, camera));
  composer.addPass(new OutputPass());
  const fx = new ShaderPass(FXAAShader); fx.uniforms.resolution.value.set(1 / W, 1 / H);
  composer.addPass(fx);
}
if (LEVEL >= 3) {
  renderer.setRenderTarget(null);
  composer = new EffectComposer(renderer, new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType }));
  composer.addPass(new ShaderPass({                 // start the chain from the motion-blurred frame (replace, never add)
    uniforms: { tSrc: { value: accRT.texture } },
    vertexShader: 'varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }',
    fragmentShader: 'uniform sampler2D tSrc; varying vec2 vUv; void main(){ gl_FragColor=texture2D(tSrc,vUv); }',
  }, 'tUnused'));
  composer.passes[0].uniforms.tSrc.value = accRT.texture;     // set after the pass clones its uniforms
  bokeh = new BokehPass(scene, camera, { focus: 9, aperture: 0.003, maxblur: 0.012 });
  composer.addPass(bokeh);
  composer.addPass(new UnrealBloomPass(new THREE.Vector2(W / 2, H / 2), 0.32, 0.35, 1.4));
  haze = new ShaderPass({
    uniforms: { tDiffuse: { value: null }, uNoise: { value: NOISE }, uTime: { value: 0 }, uAmt: { value: 0.5 } },
    vertexShader: `varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
    fragmentShader: `uniform sampler2D tDiffuse; uniform float uTime; uniform float uAmt; varying vec2 vUv;
      ${GLSL_NOISE}
      float fbm(vec2 p){ float s=0., a=.5; for(int i=0;i<4;i++){ s+=a*vn(p); p*=2.1; a*=.5; } return s; }
      void main(){
        vec2 uv=vUv;
        float m=uAmt*(0.25+0.75*smoothstep(0.75,0.0,uv.y));
        vec2 d=vec2(fbm(uv*vec2(7.,14.)+vec2(0.,-uTime*2.2)), fbm(uv*vec2(7.,14.)+vec2(5.3,-uTime*2.6)))-.5;
        uv+=d*.009*m;
        vec2 c=uv-.5; float ca=.006*dot(c,c)*4.;
        vec3 col=vec3(texture2D(tDiffuse, uv+c*ca).r, texture2D(tDiffuse, uv).g, texture2D(tDiffuse, uv-c*ca).b);
        gl_FragColor=vec4(col,1.);
      }`,
  });
  composer.addPass(haze);
  composer.addPass(new OutputPass());
}

const gl = renderer.getContext();
const px = new Uint8Array(W * H * 4);
const SUBQ = Q.get('sub');
const SUB_BY_SHOT = { A: 2, E: 2, M: 5, B: 4, C: 4 };
const HALTON = [[0.5, 0.333], [0.25, 0.667], [0.75, 0.111], [0.125, 0.444], [0.625, 0.778], [0.375, 0.222]];
function shotAt(t) { let sh = 'A'; for (const [x0, x1, s] of (LEVEL >= 3 ? SHOTS3 : SHOTS)) if (t >= x0 && t < x1) sh = s; return sh; }
function draw() { if (composer) composer.render(); else renderer.render(scene, camera); }
function renderInto(i) {
  if (LEVEL >= 3) {
    const S = SUBQ ? +SUBQ : SUB_BY_SHOT[shotAt(i / FPS)];
    // sub-frame times across a 180-degree shutter; the one nearest the centre goes last (it drives depth of field)
    const offs = Array.from({ length: S }, (_, s) => (s + 0.5) / S * 0.5 - 0.25).sort((x, y) => Math.abs(y) - Math.abs(x));
    renderer.setRenderTarget(accRT); renderer.setClearColor(0x000000, 0); renderer.clear();
    renderer.shadowMap.autoUpdate = false;
    offs.forEach((o, s) => {
      update((i + o) / FPS);
      const [jx, jy] = HALTON[s % HALTON.length];
      camera.setViewOffset(W, H, jx - 0.5, jy - 0.5, W, H);      // sub-pixel jitter = free anti-aliasing
      renderer.shadowMap.needsUpdate = true;
      renderer.setRenderTarget(sceneRT); renderer.render(scene, camera);
      accQuad.material.uniforms.tMap.value = sceneRT.texture; accQuad.material.uniforms.uW.value = 1 / S;
      renderer.setRenderTarget(accRT); renderer.autoClear = false; accQuad.render(renderer); renderer.autoClear = true;
    });
    camera.clearViewOffset();
    renderer.setRenderTarget(null);
    composer.render();
  } else {
    update(i / FPS); draw();
  }
  gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px);
}
window.renderFrame = i => {
  renderInto(i);
  let b = ''; const C = 0x8000;
  for (let k = 0; k < px.length; k += C) b += String.fromCharCode.apply(null, px.subarray(k, k + C));
  return btoa(b);
};
window.renderAll = async (f0, f1) => {      // stream raw frames to the local server: no base64, no round trips
  for (let i = f0; i < f1; i++) {
    renderInto(i);
    await fetch('/frame', { method: 'POST', body: px });
  }
  return 'ok';
};
window.renderPNG = i => { renderInto(i); return renderer.domElement.toDataURL('image/png'); };
window.track = i => {
  const t = i / FPS, a = ACT(t);
  update(t);
  camera.updateMatrixWorld();
  const inv = camera.matrixWorldInverse;
  const loc = v => { const p = v.clone().applyMatrix4(inv); return [p.x, p.y, p.z]; };
  const hip = hipWorld(a);
  const wallPt = new THREE.Vector3();
  { const th = Math.atan2(camera.position.z, camera.position.x); const r = pitR(th, camera.position.y); wallPt.set(Math.cos(th) * r, camera.position.y, Math.sin(th) * r); }
  let shot = 'A'; for (const [x0, x1, s] of (LEVEL >= 3 ? SHOTS3 : SHOTS)) if (t >= x0 && t < x1) shot = s;
  return { t, a, shot, hip: loc(hip), chunk: loc(chunk.position), lava: loc(new THREE.Vector3(0, -80, 0)), wall: loc(wallPt),
           camY: camera.position.y, rimL: loc(new THREE.Vector3(-30, 1, ZEDGE + 5)),
           wup: new THREE.Vector3(0, 1, 0).transformDirection(inv).toArray(), speed: (a > T_AIR) ? Math.hypot(VX, -VY + G * (a - T_AIR)) : 0 };
};
window.dbgCam = i => { update(i / FPS); return [camera.position.toArray(), camera.getWorldDirection(new THREE.Vector3()).toArray(), guy.shoeN.position.toArray(), ZEDGE]; };
if (Q.get('lights') === 'few') { lavaLight2.visible = false; kicker.visible = false; }
if (Q.get('sm')) { sun.shadow.mapSize.set(+Q.get('sm'), +Q.get('sm')); }
if (Q.get('noshadow')) renderer.shadowMap.enabled = false;
if (Q.get('nosmoke')) { for (const o of smokes) o.s.visible = false; for (const o of wisps) o.s.visible = false; }
if (Q.get('skylast')) { sky.renderOrder = 10; }
if (Q.get('nolava')) lava.visible = false;
if (Q.get('lavaflat')) lava.material = new THREE.MeshBasicMaterial({ color: 0xff6600 });
if (Q.get('novor')) { lavaMat.defines.NOVOR = 1; lavaMat.needsUpdate = true; }
window.dbgAcc = i => {
  renderInto(i);
  const rd = rt => { const b = new Uint16Array(4 * 16); renderer.readRenderTargetPixels(rt, W / 2, H / 2, 4, 4, b); return Array.from(b.slice(0, 8)).map(v => THREE.DataUtils.fromHalfFloat(v).toFixed(3)); };
  return { scene: rd(sceneRT), acc: rd(accRT) };
};
window.READY = true;
