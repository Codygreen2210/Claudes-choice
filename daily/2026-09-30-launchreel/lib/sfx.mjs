// Sound effects, synthesised like the music (nothing to license): a soft mouse click, key
// taps while typing, whooshes on zooms and scrolls, a pop when a caption appears, a low hit
// on the title and end cards. sfxWav() places them on the timeline's cues.
import { wav } from './music.mjs';

const SR = 44100;
function rng(seed) { let s = seed >>> 0 || 1; return () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296; }
const buf = (sec) => new Float32Array(Math.round(sec * SR));

const SOUNDS = {
  click(r) { const o = buf(0.05); for (let i = 0; i < o.length; i++) { const t = i / SR; o[i] = (Math.sin(6.2832 * 2600 * t) * 0.5 + (r() * 2 - 1) * 0.5) * Math.exp(-t * 170); } return o; },
  key(r) { const o = buf(0.04); const f = 1700 + r() * 900; for (let i = 0; i < o.length; i++) { const t = i / SR; o[i] = (Math.sin(6.2832 * f * t) * 0.35 + (r() * 2 - 1) * 0.4) * Math.exp(-t * 210) * 0.7; } return o; },
  // Filtered noise whose brightness sweeps up and back: the classic whoosh.
  whoosh(r, len = 0.55) { const o = buf(len); let lp = 0; for (let i = 0; i < o.length; i++) { const x = i / o.length; const cut = 0.02 + 0.3 * Math.sin(Math.PI * x); lp += ((r() * 2 - 1) - lp) * cut; o[i] = lp * Math.sin(Math.PI * x) * 1.4; } return o; },
  swoosh(r) { return SOUNDS.whoosh(r, 0.4).map((v) => v * 0.7); },
  pop() { const o = buf(0.09); let ph = 0; for (let i = 0; i < o.length; i++) { const t = i / SR; ph += (900 - 500 * (t / 0.09)) / SR; o[i] = Math.sin(6.2832 * ph) * Math.exp(-t * 45) * 0.45; } return o; },
  hit() { const o = buf(0.9); let ph = 0; for (let i = 0; i < o.length; i++) { const t = i / SR; ph += (55 + 60 * Math.exp(-t * 12)) / SR; o[i] = (Math.sin(6.2832 * ph) * 0.9 + Math.sin(6.2832 * ph * 2) * 0.2) * Math.exp(-t * 4.5); } return o; },
};
const LEVEL = { click: 0.55, key: 0.35, whoosh: 0.35, swoosh: 0.3, pop: 0.35, hit: 0.6 };
export const SFX_KINDS = Object.keys(SOUNDS);

// cues: [{t, kind}]; opts: {volume 0..1, off: ['pop', ...]}
export function sfxWav(cues, seconds, { volume = 0.7, off = [], seed = 5 } = {}) {
  const n = Math.max(1, Math.round(seconds * SR));
  const L = new Float32Array(n), R = new Float32Array(n);
  const r = rng(seed);
  for (const c of cues) {
    if (off.includes(c.kind) || !SOUNDS[c.kind]) continue;
    const s = SOUNDS[c.kind](r);
    const i0 = Math.round(c.t * SR), g = LEVEL[c.kind];
    const pan = c.kind === 'key' ? (r() - 0.5) * 0.3 : 0;
    for (let i = 0; i < s.length && i0 + i < n; i++) { if (i0 + i < 0) continue; L[i0 + i] += s[i] * g * (1 - pan); R[i0 + i] += s[i] * g * (1 + pan); }
  }
  return wav(L, R, Math.max(0, Math.min(1, volume)));
}
