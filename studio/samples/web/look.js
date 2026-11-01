// The "film look" for the 3D Shorts: ambient occlusion (soft contact shadows where things meet), depth of field
// (the background melts a little behind what's in focus), a rim light that outlines the subject against the room,
// and MSAA through the whole chain. Grain, halation, split toning and the vignette stay in finish.py.
//   const LOOK = makeLook(THREE, renderer, scene, camera, W, H);  ...  LOOK.render(focusPoint, { ao: true, dof: true })
// Plus idleAt(): a standing "life" layer from real motion capture (web/mocap/*.json, made by mocap_idle.py).
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { GTAOPass } from 'three/addons/postprocessing/GTAOPass.js';
import { BokehPass } from 'three/addons/postprocessing/BokehPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

export function makeLook(THREE, renderer, scene, camera, W, H, o = {}) {
  const rt = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: 4 });
  const comp = new EffectComposer(renderer, rt); comp.setPixelRatio(1); comp.setSize(W, H);
  comp.addPass(new RenderPass(scene, camera));
  const ao = new GTAOPass(scene, camera, W, H); ao.blendIntensity = o.ao ?? 0.85;
  ao.updateGtaoMaterial({ radius: o.aoRadius ?? 0.22, distanceExponent: 1.5, thickness: 1, scale: 1, samples: 16 });
  ao.updatePdMaterial({ lumaPhi: 10, depthPhi: 2, normalPhi: 3, radius: 6, rings: 2, samples: 16 });
  comp.addPass(ao);
  // noAO: far-away backdrops (a sky dome, a moon and its glow sprite) are hidden while the AO pass draws its own depth and normals;
  // the AO there read the glow sprite as a solid square and darkened it (moon, 2026-11-01). They still draw in the main pass.
  if (o.noAO && o.noAO.length) { const r0 = ao.render.bind(ao);
    ao.render = (...a) => { const was = o.noAO.map(x => x.visible); o.noAO.forEach(x => { x.visible = false; }); try { r0(...a); } finally { o.noAO.forEach((x, i) => { x.visible = was[i]; }); } }; }
  const dof = new BokehPass(scene, camera, { focus: 1.5, aperture: o.aperture ?? 0.0012, maxblur: o.maxblur ?? 0.006 });
  comp.addPass(dof);
  comp.addPass(new OutputPass());
  // overlays (a phone insert stuck to the camera): drawn after the effects so the depth of field can't blur them
  for (const ov of o.overlays || []) ov.traverse(x => x.layers.set(1));
  const rim = new THREE.DirectionalLight(o.rimColor ?? 0xfff2e6, o.rim ?? 2.4); rim.castShadow = false; scene.add(rim, rim.target);
  const fw = new THREE.Vector3();
  return { comp, ao, dof, rim,
    // focus: the world point the camera looks at (also where the rim light aims); fx: { ao, dof, rim } switches for this frame
    render(focus, fx = {}) {
      camera.updateMatrixWorld(); camera.getWorldDirection(fw);
      if (focus) { dof.uniforms.focus.value = camera.position.distanceTo(focus);
        rim.target.position.copy(focus); rim.position.copy(focus).addScaledVector(fw, 3).add(new THREE.Vector3(0, 2.2, 0)); rim.target.updateMatrixWorld(); }
      ao.enabled = fx.ao !== false; dof.enabled = fx.dof !== false && !!focus; rim.intensity = fx.rim === false ? 0 : (o.rim ?? 2.4);
      camera.layers.set(0); comp.render();
      if ((o.overlays || []).some(v => v.visible)) { const ac = renderer.autoClear, bg = scene.background; renderer.autoClear = false; scene.background = null;   // the background would paint over the frame
        camera.layers.set(1); renderer.render(scene, camera); camera.layers.set(0); renderer.autoClear = ac; scene.background = bg; } } };
}

// --- standing life from motion capture, seamless over a loop of length T seconds
export async function loadIdle(url) { return await (await fetch(url)).json(); }
export function idleAt(M, t, T, k = {}) {
  const n = M.n, f = u => { let x = (u * M.fps) % (2 * n - 2); if (x < 0) x += 2 * n - 2; return x < n - 1 ? x : 2 * n - 2 - x; };   // ping-pong in time
  const s = (arr, u) => { const x = f(u), i = Math.floor(x), a = x - i; return arr[i] * (1 - a) + arr[Math.min(n - 1, i + 1)] * a; };
  const w = t / T, mix = arr => s(arr, t) * w + s(arr, t + T) * (1 - w);        // m(t) blended with m(t+T): equal at t = 0 and t = T
  const r3 = (key, g) => [0, 1, 2].map(j => g * mix(M[key][j]));
  const cap = (v, c) => Math.max(-c, Math.min(c, v)), sh = k.shift ?? 0.35, rg = k.rot ?? 0.8;
  return { dx: cap(sh * mix(M.hips_x), 0.025), dz: cap(sh * mix(M.hips_z), 0.025), yaw: cap(rg * mix(M.hips[1]), 4),
    back: r3('back', rg), chest: r3('chest', rg), neck: r3('neck', rg * (k.head ?? 0.6)), head: r3('head', rg * (k.head ?? 0.6)) };
}
// small eye darts every ~1.1 s (seamless over T)
export function saccade(t, T, hash1) { const n = Math.max(1, Math.round(T / 1.1)), L = T / n, i = Math.floor(t / L) % n, a = Math.min(1, (t - Math.floor(t / L) * L) / 0.06);
  const v = j => [(hash1(j * 7.31 + 1) - 0.5) * 0.2, (hash1(j * 3.17 + 5) - 0.5) * 0.12];
  const p = v((i + n - 1) % n), q = v(i); return [p[0] + (q[0] - p[0]) * a, p[1] + (q[1] - p[1]) * a]; }
