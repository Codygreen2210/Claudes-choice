// ------------------------------------------------------------------ look + frame I/O
import { makeLook } from '/look.js';
const LOOK = makeLook(THREE, renderer, scene, camera, W, H, { overlays: [hud, upArrow, downArrow, barArrow, glow], aperture: 0.0007, maxblur: 0.006, rim: 1.4, noAO: [window.__SKY] });
let FOC = V(0, 1, 0);
function update(t) { t = clamp(t, 0, TOTAL - 1e-3); const r = shot(t); fitHud();
  const at = cars[0].position.clone(); sun.position.copy(at).add(V(25, 45, 30)); sun.target.position.copy(at); sun.target.updateMatrixWorld(); FOC = r.focus; return r; }
function stepTo(i) { return update(i / FPS); }
const draw = () => LOOK.render(FOC, { ao: true, dof: true });
const gl = renderer.getContext(), px = new Uint8Array(W * H * 4);
window.renderAll = async (f0, f1) => { for (let i = f0; i < f1; i++) { stepTo(i); draw(); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); await fetch('/frame', { method: 'POST', body: px }); } return 'ok'; };
window.renderAtT = t => { stepTo(Math.round(t * FPS)); draw(); return renderer.domElement.toDataURL('image/png'); };
window.dbg = { THREE, scene, camera, G, K, RG, RK, shot, cars };
window.TOTAL = TOTAL; window.FRAMES = Math.round(TOTAL * FPS); window.READY = true;
window.SCN = { THREE, scene, camera, stepTo, renderer, FPS, B, DUR, TOTAL };
