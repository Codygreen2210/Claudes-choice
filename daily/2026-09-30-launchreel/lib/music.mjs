// Original music library, synthesised from scratch: no samples, no loops from anywhere else,
// so nothing to license and nothing for YouTube/TikTok to flag. Same settings + seed = same song.
// makeMusic() returns a 16-bit stereo WAV. GENRES lists what's available for the editor.

const SR = 44100;
const KEYS = { C: 48, Db: 49, D: 50, Eb: 51, E: 52, F: 53, Gb: 54, G: 55, Ab: 56, A: 57, Bb: 58, B: 59 };
const hz = (m) => 440 * Math.pow(2, (m - 69) / 12);
const MAJ = { I: [0, [0, 4, 7, 11]], ii: [2, [0, 3, 7, 10]], iii: [4, [0, 3, 7, 10]], IV: [5, [0, 4, 7, 11]], V: [7, [0, 4, 7, 10]], vi: [9, [0, 3, 7, 10]] };
const MIN = { i: [0, [0, 3, 7, 10]], III: [3, [0, 4, 7, 11]], iv: [5, [0, 3, 7, 10]], v: [7, [0, 3, 7, 10]], VI: [8, [0, 4, 7, 11]], VII: [10, [0, 4, 7, 10]] };
const P = (tbl, names) => names.split(' ').map((n) => tbl[n]);

// Each genre: tempo, chord loop, and which instruments play how.
export const GENRES = {
  lofi: { label: 'Lo-fi', blurb: 'Dusty keys, lazy swing', bpm: 82, prog: P(MAJ, 'I vi IV V'), chords: 'ep', bass: 'round', drums: 'lofi', lead: null, swing: 0.16, crackle: true },
  synthwave: { label: 'Synthwave', blurb: 'Neon pads, driving arp', bpm: 104, prog: P(MIN, 'i VI III VII'), chords: 'pad', bass: 'pulse8', drums: 'four', lead: 'arp', duck: true },
  house: { label: 'House', blurb: 'Four on the floor, bright stabs', bpm: 122, prog: P(MIN, 'i VII VI VII'), chords: 'stab', bass: 'offbeat', drums: 'house', lead: null, duck: true },
  trap: { label: 'Trap-lite', blurb: 'Deep 808, rolling hats', bpm: 140, half: true, prog: P(MIN, 'i VI iv v'), chords: 'bell', bass: '808', drums: 'trap', lead: null },
  ambient: { label: 'Ambient', blurb: 'Slow wash, no drums', bpm: 70, prog: P(MAJ, 'I IV vi IV'), chords: 'pad', bass: 'drone', drums: null, lead: 'bell' },
  pop: { label: 'Upbeat pop', blurb: 'Plucks and claps, happy', bpm: 112, prog: P(MAJ, 'I V vi IV'), chords: 'pluck', bass: 'pulse8', drums: 'pop', lead: 'hook' },
  blues: { label: 'Slow blues', blurb: 'Shuffle, electric piano', bpm: 70, prog: [[0, [0, 4, 7, 10]], [5, [0, 4, 7, 10]], [0, [0, 4, 7, 10]], [7, [0, 4, 7, 10]]], chords: 'ep', bass: 'walk', drums: 'brush', lead: null, swing: 0.2 },
};
const ALIAS = { chill: 'lofi', bright: 'pop' };

function rng(seed) { let s = (seed >>> 0) || 1; return () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296; }

// ---------- instruments (each returns a mono Float32Array) ----------
const buf = (sec) => new Float32Array(Math.max(1, Math.round(sec * SR)));
function ep(f, dur, vel, r) {
  const o = buf(dur), trem = 4 + r() * 0.8;
  for (let i = 0; i < o.length; i++) { const t = i / SR; const env = Math.min(1, t / 0.006) * Math.exp(-t * 1.5);
    o[i] = vel * env * (Math.sin(6.2832 * f * t) + 0.28 * Math.sin(12.566 * f * t) + Math.exp(-t * 9) * 0.35 * Math.sin(6.2832 * f * 3.98 * t)) * (1 + 0.12 * Math.sin(6.2832 * trem * t)); }
  return release(o, 0.08);
}
// Detuned saws through a soft low-pass: the classic warm pad.
function pad(f, dur, vel, bright = 0.08) {
  const o = buf(dur); const det = [0.996, 1, 1.004]; let lp = 0; const ph = [0, 0.33, 0.66];
  for (let i = 0; i < o.length; i++) { const t = i / SR; let s = 0;
    for (let k = 0; k < 3; k++) { ph[k] = (ph[k] + (f * det[k]) / SR) % 1; s += 2 * ph[k] - 1; }
    lp += (s / 3 - lp) * bright;
    const env = Math.min(1, t / 0.35) * Math.min(1, (dur - t) / 0.4);
    o[i] = vel * env * lp; }
  return o;
}
function stab(f, dur, vel) { const o = pad(f, Math.min(dur, 0.22), vel * 1.5, 0.25); for (let i = 0; i < o.length; i++) o[i] *= Math.exp(-(i / SR) * 10); return o; }
// Karplus-Strong plucked string.
function pluck(f, dur, vel, r) {
  const o = buf(dur); const N = Math.max(2, Math.round(SR / f)); const d = new Float32Array(N);
  for (let i = 0; i < N; i++) d[i] = r() * 2 - 1;
  let p = 0; for (let i = 0; i < o.length; i++) { const nx = (p + 1) % N; const v = 0.5 * (d[p] + d[nx]) * 0.996; o[i] = d[p] * vel; d[p] = v; p = nx; }
  return release(o, 0.05);
}
function bell(f, dur, vel) { const o = buf(dur); for (let i = 0; i < o.length; i++) { const t = i / SR; o[i] = vel * Math.exp(-t * 2.2) * (Math.sin(6.2832 * f * t) + 0.5 * Math.sin(6.2832 * f * 2.76 * t) * Math.exp(-t * 4)); } return release(o, 0.05); }
function sub(f, dur, vel, glide = 0) { const o = buf(dur); let ph = 0;
  for (let i = 0; i < o.length; i++) { const t = i / SR; const ff = f * (1 + glide * Math.exp(-t * 18)); ph += ff / SR; const s = Math.sin(6.2832 * ph);
    o[i] = vel * Math.tanh(1.6 * s) * Math.min(1, t / 0.005) * (glide ? Math.exp(-t * 0.9) : Math.exp(-t * 2.5)); }
  return release(o, 0.04);
}
function kick(vel) { const o = buf(0.35); let ph = 0; for (let i = 0; i < o.length; i++) { const t = i / SR; ph += (48 + 110 * Math.exp(-t * 35)) / SR; o[i] = vel * Math.sin(6.2832 * ph) * Math.exp(-t * 9); } return o; }
function noiseHit(dur, vel, decay, hp, r, tone = 0) { const o = buf(dur); let prev = 0, lp = 0;
  for (let i = 0; i < o.length; i++) { const t = i / SR; const w = r() * 2 - 1; const h = w - prev * hp; prev = w; lp += (h - lp) * 0.6;
    o[i] = vel * (lp + (tone ? 0.5 * Math.sin(6.2832 * tone * t) * Math.exp(-t * 30) : 0)) * Math.exp(-t * decay); }
  return o;
}
const snare = (v, r) => noiseHit(0.25, v, 16, 0.6, r, 190);
const clap = (v, r) => { const o = buf(0.3); for (const off of [0, 0.011, 0.022]) { const h = noiseHit(0.25, v * 0.8, 22, 0.8, r); const s = Math.round(off * SR); for (let i = 0; i < h.length && i + s < o.length; i++) o[i + s] += h[i]; } return o; };
const hat = (v, r, open = false) => noiseHit(open ? 0.3 : 0.07, v, open ? 9 : 55, 0.98, r);
function release(o, sec) { const n = Math.min(o.length, Math.round(sec * SR)); for (let i = 0; i < n; i++) o[o.length - 1 - i] *= i / n; return o; }

// ---------- arrangement ----------
export function makeMusic({ seconds, seed = 7, key = 'F', genre, mood, bpm, volume = 0.5, parts = {} } = {}) {
  const gname = ALIAS[genre || mood] || genre || mood || 'lofi';
  const G = GENRES[gname] || GENRES.lofi;
  const on = (p) => parts[p] !== false;
  const n = Math.max(1, Math.round(seconds * SR));
  const L = new Float32Array(n), R = new Float32Array(n);
  const r = rng(seed);
  const tempo = bpm || G.bpm;
  const beat = 60 / tempo, bar = beat * 4, step = beat / 4;
  const root = KEYS[key] ?? 53;
  const add = (at, sig, gain, pan = 0) => { const i0 = Math.round(at * SR); const gl = gain * (1 - pan), gr = gain * (1 + pan);
    for (let i = 0; i < sig.length; i++) { const j = i0 + i; if (j < 0) continue; if (j >= n) break; L[j] += sig[i] * gl; R[j] += sig[i] * gr; } };
  const kicks = [];
  const bars = Math.ceil(seconds / bar) + 1;
  // A short melody motif, reused so the hook is memorable.
  const motif = Array.from({ length: 8 }, () => [0, 2, 4, 7, 9, 12][Math.floor(r() * 6)]);
  for (let b = 0; b < bars; b++) {
    const t0 = b * bar;
    const [off, tones] = G.prog[b % G.prog.length];
    const base = root + off;
    const sw = (k) => (k % 2 ? (G.swing || 0) * step * 2 : 0);
    const intro = b === 0; // lighter first bar
    // chords
    if (on('chords')) {
      if (G.chords === 'ep') for (const at of [0, beat * 1.5 + (r() < 0.5 ? 0 : beat)]) tones.forEach((s, k) => add(t0 + at + k * 0.012, ep(hz(base + 12 + s), at ? bar - at : beat * 1.6, 0.1 - k * 0.012, r), 1, (k / 3) * 0.6 - 0.3));
      if (G.chords === 'pad') tones.forEach((s, k) => add(t0, pad(hz(base + 12 + s), bar + 0.3, 0.07), 1, (k / 3) * 0.8 - 0.4));
      if (G.chords === 'stab') for (const k of [2, 6, 10, 14]) if (!intro || k > 8) tones.forEach((s, j) => add(t0 + k * step, stab(hz(base + 12 + s), 0.2, 0.06), 1, j * 0.15 - 0.2));
      if (G.chords === 'pluck') for (const k of [0, 3, 6, 8, 11, 14]) tones.slice(0, 3).forEach((s, j) => add(t0 + k * step + j * 0.008, pluck(hz(base + 24 + s), 0.6, 0.12, r), 1, j * 0.3 - 0.3));
      if (G.chords === 'bell') for (const k of [0, 6, 12]) add(t0 + k * step, bell(hz(base + 24 + tones[(k / 6) % tones.length]), 1.2, 0.09), 1, 0.2);
    }
    // bass
    if (on('bass')) {
      const bf = hz(base - 12);
      if (G.bass === 'round') [0, 2.5].forEach((q) => add(t0 + q * beat, sub(bf, beat * 1.4, 0.35), 1));
      if (G.bass === 'walk') [0, 7, r() < 0.5 ? 12 : 9, 10].forEach((s, k) => add(t0 + k * beat, sub(hz(base - 12 + s), beat * 0.9, 0.3), 1));
      if (G.bass === 'pulse8') for (let k = 0; k < 8; k++) add(t0 + k * beat / 2, sub(bf * (k % 4 === 3 ? 2 : 1), beat * 0.45, 0.26), 1);
      if (G.bass === 'offbeat') for (let k = 0; k < 4; k++) add(t0 + k * beat + beat / 2, sub(bf, beat * 0.4, 0.34), 1);
      if (G.bass === '808') [0, 1.75, 3].forEach((q, k) => add(t0 + q * beat, sub(bf * (k === 2 && r() < 0.5 ? 1.5 : 1), beat * 1.6, 0.5, k === 0 ? 0.4 : 0), 1));
      if (G.bass === 'drone') add(t0, pad(bf, bar + 0.4, 0.12, 0.02), 1);
    }
    // drums
    if (on('drums') && G.drums && !(intro && G.drums !== 'lofi')) {
      const K = (at, v = 0.9) => { add(at, kick(v), 1); kicks.push(at); };
      if (G.drums === 'four' || G.drums === 'house') for (let k = 0; k < 4; k++) K(t0 + k * beat);
      if (G.drums === 'four') { [1, 3].forEach((k) => add(t0 + k * beat, snare(0.35, r), 1)); for (let k = 0; k < 8; k++) add(t0 + k * beat / 2, hat(0.12, r), 1, 0.3); }
      if (G.drums === 'house') { [1, 3].forEach((k) => add(t0 + k * beat, clap(0.4, r), 1)); for (let k = 0; k < 4; k++) add(t0 + k * beat + beat / 2, hat(0.18, r, true), 1, 0.25); }
      if (G.drums === 'lofi') { K(t0, 0.7); K(t0 + beat * 2.5, 0.6); [1, 3].forEach((k) => add(t0 + k * beat, snare(0.22, r), 1)); for (let k = 0; k < 8; k++) add(t0 + k * beat / 2 + sw(k), hat(k % 2 ? 0.05 : 0.09, r), 1, 0.3); }
      if (G.drums === 'brush') for (let k = 0; k < 8; k++) add(t0 + k * beat / 2 + sw(k), hat(k % 2 ? 0.05 : 0.08, r), 1, 0.3);
      if (G.drums === 'pop') { K(t0); K(t0 + beat * 2); K(t0 + beat * 2.5, 0.6); [1, 3].forEach((k) => add(t0 + k * beat, clap(0.38, r), 1)); for (let k = 0; k < 8; k++) add(t0 + k * beat / 2, hat(0.09, r), 1, 0.3); }
      if (G.drums === 'trap') { K(t0); K(t0 + beat * 2.75, 0.7); add(t0 + beat * 2, clap(0.42, r), 1);
        for (let k = 0; k < 16; k++) { add(t0 + k * step, hat(0.08, r), 1, 0.35); if (k === 11 || k === 15) for (let q = 1; q < 3; q++) add(t0 + k * step + q * step / 3, hat(0.06, r), 1, 0.35); } }
    }
    // lead
    if (on('lead') && G.lead && b % 2 === 1) {
      if (G.lead === 'arp') for (let k = 0; k < 16; k++) add(t0 + k * step, pluck(hz(base + 24 + tones[k % tones.length] + (k % 8 > 3 ? 12 : 0)), step * 2, 0.07, r), 1, k % 2 ? 0.4 : -0.4);
      if (G.lead === 'hook') motif.forEach((s, k) => add(t0 + k * beat / 2, pluck(hz(base + 24 + s), beat, 0.1, r), 1, 0.15));
      if (G.lead === 'bell') add(t0 + beat * 2, bell(hz(base + 24 + motif[b % 8]), 2.5, 0.06), 1, -0.2);
    }
  }
  // Sidechain "pump" on house/synthwave: duck everything but the kick briefly after each kick.
  if (G.duck && kicks.length) {
    const env = new Float32Array(n).fill(1);
    for (const k of kicks) { const i0 = Math.round(k * SR); for (let i = 0; i < SR * 0.18 && i0 + i < n; i++) env[i0 + i] = Math.min(env[i0 + i], 0.55 + 0.45 * (i / (SR * 0.18))); }
    for (let i = 0; i < n; i++) { L[i] *= env[i]; R[i] *= env[i]; }
  }
  if (G.crackle) for (let i = 0; i < n; i++) if (r() < 0.0006) { const v = (r() - 0.5) * 0.08; L[i] += v; R[i] += v; }
  // Room: a short stereo echo.
  const d1 = Math.round(0.137 * SR), d2 = Math.round(0.191 * SR), wet = G.drums ? 0.14 : 0.3;
  for (let i = n - 1; i >= 0; i--) { if (i >= d1) L[i] += R[i - d1] * wet; if (i >= d2) R[i] += L[i - d2] * wet; }
  const fi = Math.min(n, SR * 0.6), fo = Math.min(n, SR * 2.5);
  for (let i = 0; i < fi; i++) { L[i] *= i / fi; R[i] *= i / fi; }
  for (let i = 0; i < fo; i++) { const g = i / fo; L[n - 1 - i] *= g; R[n - 1 - i] *= g; }
  // Soft-clip, then scale to the requested level.
  let peak = 1e-9;
  for (let i = 0; i < n; i++) { L[i] = Math.tanh(L[i] * 1.2); R[i] = Math.tanh(R[i] * 1.2); peak = Math.max(peak, Math.abs(L[i]), Math.abs(R[i])); }
  const g = Math.min(0.89, 0.89 * volume * 2) / peak; // volume 0.5 = peaks at -1 dB
  return wav(L, R, g);
}

function wav(L, R, g) {
  const n = L.length, b = Buffer.alloc(44 + n * 4);
  b.write('RIFF', 0); b.writeUInt32LE(36 + n * 4, 4); b.write('WAVE', 8); b.write('fmt ', 12);
  b.writeUInt32LE(16, 16); b.writeUInt16LE(1, 20); b.writeUInt16LE(2, 22); b.writeUInt32LE(SR, 24);
  b.writeUInt32LE(SR * 4, 28); b.writeUInt16LE(4, 32); b.writeUInt16LE(16, 34); b.write('data', 36); b.writeUInt32LE(n * 4, 40);
  for (let i = 0; i < n; i++) {
    b.writeInt16LE(Math.max(-32767, Math.min(32767, Math.round(L[i] * g * 32767))), 44 + i * 4);
    b.writeInt16LE(Math.max(-32767, Math.min(32767, Math.round(R[i] * g * 32767))), 46 + i * 4);
  }
  return b;
}
