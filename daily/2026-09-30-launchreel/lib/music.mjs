// Original background music made from scratch: soft electric-piano chords, a walking bass,
// brushed hi-hat. No samples, no licensing. Same seed, same song. Returns a 16-bit WAV.

const SR = 44100;
const KEYS = { C: 48, Db: 49, D: 50, Eb: 51, E: 52, F: 53, Gb: 54, G: 55, Ab: 56, A: 57, Bb: 58, B: 59 };
const hz = (m) => 440 * Math.pow(2, (m - 69) / 12);
// Chord shapes as semitones from the key's root: [root offset, chord tones]
const PROGS = {
  chill: [[0, [0, 4, 7, 11, 14]], [9, [0, 3, 7, 10, 14]], [5, [0, 4, 7, 11, 14]], [7, [0, 4, 7, 10, 14]]], // Imaj9 vi9 IVmaj9 V9
  blues: [[0, [0, 4, 7, 10]], [5, [0, 4, 7, 10]], [0, [0, 4, 7, 10]], [7, [0, 4, 7, 10]]],
  bright: [[0, [0, 4, 7, 14]], [7, [0, 4, 7, 14]], [9, [0, 3, 7, 10]], [5, [0, 4, 7, 11]]],
};

function rng(seed) { let s = (seed >>> 0) || 1; return () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296; }

export function makeMusic({ seconds, seed = 7, key = 'F', mood = 'chill', bpm = 84, volume = 0.5 } = {}) {
  const n = Math.max(1, Math.round(seconds * SR));
  const L = new Float32Array(n), R = new Float32Array(n);
  const r = rng(seed);
  const beat = 60 / bpm, bar = beat * 4;
  const root = KEYS[key] ?? 53;
  const prog = PROGS[mood] || PROGS.chill;

  const add = (buf, at, sig, gain) => { const i0 = Math.round(at * SR); for (let i = 0; i < sig.length && i0 + i < n; i++) if (i0 + i >= 0) buf[i0 + i] += sig[i] * gain; };
  // Electric piano: a few sine partials with a bell-ish attack and a long decay.
  const ep = (f, dur, vel) => {
    const len = Math.round(dur * SR), out = new Float32Array(len);
    const trem = 4.2 + r() * 0.6;
    for (let i = 0; i < len; i++) {
      const tt = i / SR;
      const env = Math.min(1, tt / 0.006) * Math.exp(-tt * 1.6);
      const bell = Math.exp(-tt * 9) * 0.35 * Math.sin(2 * Math.PI * f * 3.98 * tt);
      out[i] = vel * env * (Math.sin(2 * Math.PI * f * tt) + 0.28 * Math.sin(2 * Math.PI * f * 2 * tt) + bell) * (1 + 0.12 * Math.sin(2 * Math.PI * trem * tt));
    }
    const rel = Math.min(len, Math.round(0.08 * SR));
    for (let i = 0; i < rel; i++) out[len - 1 - i] *= i / rel;
    return out;
  };
  const bass = (f, dur) => {
    const len = Math.round(dur * SR), out = new Float32Array(len);
    for (let i = 0; i < len; i++) { const tt = i / SR; const env = Math.min(1, tt / 0.01) * Math.exp(-tt * 3); out[i] = env * (Math.sin(2 * Math.PI * f * tt) + 0.2 * Math.sin(4 * Math.PI * f * tt)); }
    return out;
  };
  const hat = (vel) => {
    const len = Math.round(0.09 * SR), out = new Float32Array(len); let prev = 0;
    for (let i = 0; i < len; i++) { const w = r() * 2 - 1; const hp = w - prev; prev = w; out[i] = vel * hp * Math.exp(-(i / SR) * 45); }
    return out;
  };

  const bars = Math.ceil(seconds / bar) + 1;
  for (let b = 0; b < bars; b++) {
    const t0 = b * bar;
    const [off, tones] = prog[b % prog.length];
    const base = root + off;
    // Chords: on 1 and the "and" of 2, with a slight strum and random voicing lift.
    for (const at of [0, beat * 1.5 + (r() < 0.5 ? 0 : beat)]) {
      const lift = r() < 0.3 ? 12 : 0;
      tones.forEach((s, k) => {
        const f = hz(base + 12 + s + (k > 2 ? lift : 0));
        const sig = ep(f, at ? bar - at : beat * 1.6, 0.11 - k * 0.012);
        const pan = (k / Math.max(1, tones.length - 1)) * 0.6 - 0.3;
        const when = t0 + at + k * 0.012;
        add(L, when, sig, 1 - pan); add(R, when, sig, 1 + pan);
      });
    }
    // Walking bass: root, fifth, octave or approach note.
    const walk = [0, 7, r() < 0.5 ? 12 : 9, (prog[(b + 1) % prog.length][0] - off + 11) % 12 + 0];
    walk.forEach((s, k) => { const sig = bass(hz(base - 12 + s), beat * 0.9); add(L, t0 + k * beat, sig, 0.22); add(R, t0 + k * beat, sig, 0.22); });
    // Brushed hat with a light swing.
    for (let k = 0; k < 8; k++) {
      const sw = k % 2 ? beat * 0.16 : 0;
      const sig = hat(k % 2 ? 0.05 : 0.08);
      add(L, t0 + k * beat / 2 + sw, sig, 0.7); add(R, t0 + k * beat / 2 + sw, sig, 1.0);
    }
  }
  // Room: a short stereo echo.
  const d1 = Math.round(0.137 * SR), d2 = Math.round(0.191 * SR);
  for (let i = n - 1; i >= 0; i--) { if (i >= d1) L[i] += R[i - d1] * 0.18; if (i >= d2) R[i] += L[i - d2] * 0.18; }
  // Fade in/out, then scale to the target level without clipping.
  const fi = Math.min(n, SR * 0.6), fo = Math.min(n, SR * 2.5);
  for (let i = 0; i < fi; i++) { L[i] *= i / fi; R[i] *= i / fi; }
  for (let i = 0; i < fo; i++) { const g = i / fo; L[n - 1 - i] *= g; R[n - 1 - i] *= g; }
  let peak = 1e-9;
  for (let i = 0; i < n; i++) peak = Math.max(peak, Math.abs(L[i]), Math.abs(R[i]));
  const g = Math.min(0.89, 0.89 * volume * 2) / peak; // volume 0.5 = peaks at -1 dB
  return wav(L, R, g);
}

function wav(L, R, g) {
  const n = L.length, buf = Buffer.alloc(44 + n * 4);
  buf.write('RIFF', 0); buf.writeUInt32LE(36 + n * 4, 4); buf.write('WAVE', 8); buf.write('fmt ', 12);
  buf.writeUInt32LE(16, 16); buf.writeUInt16LE(1, 20); buf.writeUInt16LE(2, 22); buf.writeUInt32LE(SR, 24);
  buf.writeUInt32LE(SR * 4, 28); buf.writeUInt16LE(4, 32); buf.writeUInt16LE(16, 34); buf.write('data', 36); buf.writeUInt32LE(n * 4, 40);
  for (let i = 0; i < n; i++) {
    buf.writeInt16LE(Math.max(-32767, Math.min(32767, Math.round(L[i] * g * 32767))), 44 + i * 4);
    buf.writeInt16LE(Math.max(-32767, Math.min(32767, Math.round(R[i] * g * 32767))), 46 + i * 4);
  }
  return buf;
}
