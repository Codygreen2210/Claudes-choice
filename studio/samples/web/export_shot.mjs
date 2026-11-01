// Export one shot of a 3D Short page to a .glb for Blender: the visible scene at its first frame, plus every moving
// node (his bones, the phone, the camera) and his face shapes baked per frame into one animation.
//   node export_shot.mjs PAGE F0 F1 OUT.glb          (frames F0..F1-1; the page must set window.SCN)
// His face paint (brows, lashes, lips) is a shader in the page, so it is baked into a front-projected texture first.
import http from 'http'; import fs from 'fs'; import path from 'path';
import { chromium } from 'playwright-core';
import { CHROME } from './browser.mjs';
process.env.GALLIUM_DRIVER = process.env.GALLIUM_DRIVER || 'llvmpipe';
const [,, pg, f0s, f1s, out] = process.argv;
const root = import.meta.dirname;
const types = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json' };
const srv = http.createServer((req, res) => { const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); res.end(); return; } res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' }); res.end(d); }); }).listen(0);
const browser = await chromium.launch({ executablePath: CHROME, args: ['--use-gl=angle', '--use-angle=gl-egl', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 270, height: 480 } });
page.on('pageerror', e => console.error('[err]', e.message)); page.on('console', m => console.error('[log]', m.text()));
await page.goto(`http://127.0.0.1:${srv.address().port}/${pg}?w=1080&h=1920`);
await page.waitForFunction('window.READY === true', null, { timeout: 900000 });
const b64 = await page.evaluate(async ([F0, F1]) => {
  const { THREE, scene, camera, G, stepTo, renderer, FPS, phone2 } = window.SCN;
  const { GLTFExporter } = await import('/node_modules/three/examples/jsm/exporters/GLTFExporter.js');
  stepTo(F0);                                                       // after load the page sits on its warm-up frame
  // --- bake the painted face into a texture, front-projected (rest pose faces -z)
  const head = G.meshes.skin_head, hg = head.geometry, P = hg.attributes.position;
  hg.computeBoundingBox(); const bb = hg.boundingBox, pad = 0.004;
  const x0 = bb.min.x - pad, x1 = bb.max.x + pad, y0 = bb.min.y - pad, y1 = bb.max.y + pad;
  const uv = new Float32Array(P.count * 2); for (let i = 0; i < P.count; i++) { uv[i * 2] = (x1 - P.getX(i)) / (x1 - x0); uv[i * 2 + 1] = (y1 - P.getY(i)) / (y1 - y0); }   // glTF: v = 0 is the top row
  hg.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  const TS = 2048, rt = new THREE.WebGLRenderTarget(TS, Math.round(TS * (y1 - y0) / (x1 - x0)));
  rt.texture.colorSpace = THREE.SRGBColorSpace;
  // render the real head (its own patched material) in the rest pose, everything else hidden, flat white light only
  const vis = new Map(), lit = []; scene.traverse(o => { vis.set(o, o.visible); if (o.isMesh || o.isPoints || o.isSprite || o.isLine) o.visible = o === head; if (o.isLight) { lit.push([o, o.intensity]); o.intensity = 0; } });
  const amb = new THREE.AmbientLight(0xffffff, Math.PI); scene.add(amb);
  const keep = { env: scene.environmentIntensity, bg: scene.background, fog: scene.fog, mi: head.morphTargetInfluences.slice(), rp: G.root.position.clone(), rq: G.root.quaternion.clone() };
  scene.environmentIntensity = 0; scene.background = new THREE.Color(0xd99a7c); scene.fog = null; head.morphTargetInfluences.fill(0);
  G.reset(); G.root.position.set(0, 0, 0); G.root.quaternion.identity(); G.root.visible = true; scene.updateMatrixWorld(true);
  const oc = new THREE.OrthographicCamera(-(x1 - x0) / 2, (x1 - x0) / 2, (y1 - y0) / 2, -(y1 - y0) / 2, 0.01, 5);
  oc.position.set((x0 + x1) / 2, (y0 + y1) / 2, -2); oc.lookAt((x0 + x1) / 2, (y0 + y1) / 2, 0);
  const tm = renderer.toneMapping; renderer.toneMapping = THREE.NoToneMapping;
  renderer.setRenderTarget(rt); renderer.render(scene, oc); renderer.setRenderTarget(null); renderer.toneMapping = tm;
  scene.remove(amb); for (const [o, v] of vis) o.visible = v; for (const [o, i] of lit) o.intensity = i;
  scene.environmentIntensity = keep.env; scene.background = keep.bg; scene.fog = keep.fog; head.morphTargetInfluences.splice(0, keep.mi.length, ...keep.mi); G.root.position.copy(keep.rp); G.root.quaternion.copy(keep.rq);
  const px = new Uint8Array(rt.width * rt.height * 4); renderer.readRenderTargetPixels(rt, 0, 0, rt.width, rt.height, px);
  const cv = document.createElement('canvas'); cv.width = rt.width; cv.height = rt.height; const cx = cv.getContext('2d'), im = cx.createImageData(rt.width, rt.height);
  for (let k = 3; k < px.length; k += 4) px[k] = 255;              // opaque: Blender would read alpha as cut-outs
  for (let y = 0; y < rt.height; y++) im.data.set(px.subarray((rt.height - 1 - y) * rt.width * 4, (rt.height - y) * rt.width * 4), y * rt.width * 4);   // GL rows are bottom-up
  cx.putImageData(im, 0, 0);
  const faceTex = new THREE.CanvasTexture(cv); faceTex.colorSpace = THREE.SRGBColorSpace; faceTex.flipY = false;
  // --- record the shot: every node that moves, and his face shapes
  const nodes = []; scene.traverse(o => nodes.push(o));
  const T = [], rec = new Map(); const morphs = [];
  for (let i = F0; i < F1; i++) { stepTo(i); T.push((i - F0) / FPS);
    for (const o of nodes) { let r = rec.get(o); if (!r) rec.set(o, r = { p: [], q: [], s: [], v: [] });
      r.p.push(...o.position.toArray()); r.q.push(...o.quaternion.toArray()); r.s.push(...o.scale.toArray()); r.v.push(o.visible); }
    morphs.push(...head.morphTargetInfluences); }
  stepTo(F0); scene.updateMatrixWorld(true);
  const tracks = [], same = (a, n) => { for (let k = n; k < a.length; k++) if (Math.abs(a[k] - a[k % n]) > 1e-6) return false; return true; };
  for (const [o, r] of rec) {
    if (!same(r.p, 3)) tracks.push(new THREE.VectorKeyframeTrack(o.uuid + '.position', T, r.p));
    if (!same(r.q, 4)) tracks.push(new THREE.QuaternionKeyframeTrack(o.uuid + '.quaternion', T, r.q));
    if (!same(r.s, 3)) tracks.push(new THREE.VectorKeyframeTrack(o.uuid + '.scale', T, r.s)); }
  if (!same(morphs, head.morphTargetInfluences.length)) tracks.push(new THREE.NumberKeyframeTrack(head.uuid + '.morphTargetInfluences', T, morphs));
  const clip = new THREE.AnimationClip('shot', T[T.length - 1] + 1 / FPS, tracks);
  // --- what goes in the file: the visible scene, the head with its baked face, and the camera
  if (phone2) phone2.visible = false;                              // the corner insert is added in the edit, not in the 3D
  head.userData.faceBaked = true;
  scene.traverse(o => { if (o.isMesh && o.material && o.material.isMeshPhysicalMaterial && o.material.roughness === 0.25 && o.material.clearcoat === 1 && o.material.color.getHex() === 0xffffff)
    o.material = new THREE.MeshPhysicalMaterial({ color: 0x4a2c16, roughness: 0.3, clearcoat: 1, name: 'iris' }); });   // the iris is a shader in the page
  for (const [k, m] of Object.entries(G.meshes)) if (m.material && !m.material.name) m.material.name = k.replace(/[RL]$/, '');   // skin_arm, shirt, jeans... so Blender can tell them apart
  const fm = new THREE.MeshPhysicalMaterial({ map: faceTex, roughness: 0.5, name: 'face_baked' }); const oldM = head.material; head.material = fm;
  camera.name = 'shot_camera';
  const names = new Map(); scene.traverse(o => { if (!o.name) o.name = o.type + '_' + o.id; let n = o.name, k = 1; while (names.has(n)) n = o.name + '_' + (k++); names.set(n, 1); o.name = n; });
  const KEEP = new Set(['position', 'normal', 'uv', 'skinIndex', 'skinWeight']);      // Blender's importer chokes on the page's own attributes (ao, hden, ...)
  scene.traverse(o => { if (o.isMesh && o.geometry) for (const k of Object.keys(o.geometry.attributes)) if (!KEEP.has(k)) o.geometry.deleteAttribute(k); });
  const ex = new GLTFExporter();
  const glb = await ex.parseAsync(scene, { binary: true, onlyVisible: true, animations: [clip], maxTextureSize: 4096 });
  head.material = oldM;
  let s = ''; const u8 = new Uint8Array(glb); for (let i = 0; i < u8.length; i += 0x8000) s += String.fromCharCode.apply(null, u8.subarray(i, i + 0x8000));
  return [btoa(s), tracks.length, T.length];
}, [+f0s, +f1s]);
fs.writeFileSync(out, Buffer.from(b64[0], 'base64'));
console.log(`wrote ${out}: ${b64[1]} tracks over ${b64[2]} frames`);
await browser.close(); srv.close();
