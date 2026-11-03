// ------------------------------------------------------------------ look + frame I/O
import { makeLook } from '/look.js';
const LOOK = makeLook(THREE, renderer, scene, camera, W, H, { overlays: [hud, ringA, ringB, arrA, arrB, pin, ...RINGS, ...QS], aperture: 0.0005, maxblur: 0.005, rim: false, noAO: [window.__SKY, RANGE, ...PUFF.map(p => p.s)] });
let FOC = V(0, 1, 0), WIDE = false;
function update(t) { t = clamp(t, 0, TOTAL - 1e-3); const r = shot(t); fitHud();
  const at = r.focus; sun.position.copy(at).add(V(35, 60, 25)); sun.target.position.copy(at); sun.target.updateMatrixWorld(); FOC = r.focus; WIDE = [1, 2, 9, 13].includes(r.b); return r; }
function stepTo(i) { return update(i / FPS); }
const draw = () => LOOK.render(FOC, { ao: !WIDE, dof: !WIDE });
const gl = renderer.getContext(), px = new Uint8Array(W * H * 4);
window.renderAll = async (f0, f1) => { for (let i = f0; i < f1; i++) { stepTo(i); draw(); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); await fetch('/frame', { method: 'POST', body: px }); } return 'ok'; };
window.renderAtT = t => { stepTo(Math.round(t * FPS)); draw(); return renderer.domElement.toDataURL('image/png'); };
window.dbg = { THREE, scene, camera, G, shot, HA, HB };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS); window.READY = true;
window.SCN = { THREE, scene, camera, stepTo, renderer, FPS, B, DUR, TOTAL };
