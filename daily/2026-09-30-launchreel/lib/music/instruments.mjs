// Instruments, each rendering one note/hit to a mono Float32Array. Recipes follow Sound on
// Sound's "Synth Secrets" (808 kick/snare/hats), Chowning FM (electric piano, bells) and
// common production practice (supersaw, Juno pad, 808 bass with glide).
import { SR, TAU, SVF, Biquad, saw, square, adsr, sat, midiHz } from './dsp.mjs';

const buf = (sec) => new Float32Array(Math.max(1, Math.round(sec * SR)));
const env = (t, a, d) => Math.min(1, t / a) * Math.exp(-t / d);

// ---------------- drums ----------------
export function kick(kind, vel, r) {
  const spec = { '808': [150, 48, 0.04, 0.9, 3], '909': [230, 50, 0.012, 0.35, 2], pop: [180, 55, 0.02, 0.26, 1.6], soft: [120, 50, 0.03, 0.3, 1.2], lofi: [140, 52, 0.025, 0.3, 1.5] }[kind] || [180, 55, 0.02, 0.26, 1.6];
  const [f0, f1, pt, dec, drive] = spec;
  const o = buf(dec * 3.5); let ph = 0;
  const clickF = new Biquad('bp', kind === '909' ? 4000 : 3000, 1);
  for (let i = 0; i < o.length; i++) {
    const t = i / SR; ph += (f1 + (f0 - f1) * Math.exp(-t / pt)) / SR;
    const body = Math.sin(TAU * ph) * Math.min(1, t / 0.001) * Math.exp(-t / dec);
    const click = t < 0.006 ? clickF.run(r() * 2 - 1) * (1 - t / 0.006) * 0.6 : 0;
    o[i] = sat(body + click, drive) * vel;
  }
  if (kind !== '808') { new Biquad('peak', 60, 1, 3).process(o); new Biquad('peak', 330, 1.5, -4).process(o); }
  return o;
}
export function snare(kind, vel, r) {
  const dec = { trap: 0.22, pop: 0.2, gated: 0.16, lofi: 0.14, soft: 0.12 }[kind] || 0.18;
  const o = buf(kind === 'gated' ? 0.35 : dec * 3);
  const hp = new Biquad('hp', 1500), pk = new Biquad('peak', 5000, 1, 4);
  for (let i = 0; i < o.length; i++) {
    const t = i / SR, bend = 1 + 0.15 * Math.exp(-t / 0.01);
    const tone = (Math.sin(TAU * 180 * bend * t) + 0.6 * Math.sin(TAU * 330 * bend * t)) * Math.exp(-t / 0.09);
    const noise = pk.run(hp.run(r() * 2 - 1)) * Math.exp(-t / dec);
    o[i] = sat(tone * 0.5 + noise * 0.75, 1.5) * vel;
  }
  if (kind === 'gated') for (let i = 0; i < o.length; i++) { const t = i / SR; o[i] *= t < 0.22 ? 1.6 : Math.max(0, 1 - (t - 0.22) / 0.04); }
  if (kind === 'lofi') new Biquad('lp', 6000).process(o);
  return o;
}
export function clap(vel, r) {
  const o = buf(0.4), bp = new Biquad('bp', 1100, 1.2), hp = new Biquad('hp', 600);
  for (let i = 0; i < o.length; i++) {
    const t = i / SR; let e = 0;
    for (const s of [0, 0.011, 0.022]) if (t >= s && t < s + 0.01) e = Math.max(e, 1 - (t - s) / 0.01);
    if (t >= 0.033) e = Math.max(e, Math.exp(-(t - 0.033) / 0.07));
    o[i] = hp.run(bp.run(r() * 2 - 1)) * e * 2.2 * vel;
  }
  return o;
}
// Metallic hats: six square waves at the TR-808 ratios, band-passed high, plus a little noise.
const HATF = [205.3, 304.4, 369.6, 522.7, 540, 800];
export function hat(open, vel, r, bright = 1) {
  const dec = open ? 0.32 : 0.045, o = buf(dec * 4);
  const ph = HATF.map(() => r()), bp = new Biquad('bp', 10000 * bright, 0.9), hp1 = new Biquad('hp', 7000 * bright), hp2 = new Biquad('hp', 7000 * bright);
  for (let i = 0; i < o.length; i++) {
    const t = i / SR; let m = 0;
    for (let k = 0; k < 6; k++) { ph[k] = (ph[k] + HATF[k] * 1.8 / SR) % 1; m += ph[k] < 0.5 ? 1 : -1; }
    const x = m / 6 * 0.85 + (r() * 2 - 1) * 0.15;
    o[i] = hp2.run(hp1.run(bp.run(x))) * Math.min(1, t / 0.0005) * Math.exp(-t / dec) * 1.8 * vel;
  }
  return o;
}
export function shaker(vel, r) { const o = buf(0.12), bp = new Biquad('bp', 7000, 2); for (let i = 0; i < o.length; i++) { const t = i / SR; o[i] = bp.run(r() * 2 - 1) * Math.min(1, t / 0.015) * Math.exp(-t / 0.04) * 2 * vel; } return o; }
export function rim(vel) { const o = buf(0.08), bp = new Biquad('bp', 2000, 2); for (let i = 0; i < o.length; i++) { const t = i / SR; o[i] = bp.run(Math.tanh(4 * (Math.sin(TAU * 1700 * t) + Math.sin(TAU * 500 * t)))) * Math.exp(-t / 0.025) * 2 * vel; } return o; }
export function conga(pitch, vel, r) {
  const f = [200, 290, 390][pitch] || 290, o = buf(0.5), res = new Biquad('bp', f, 8); let ph = 0;
  for (let i = 0; i < o.length; i++) { const t = i / SR; ph += f * (1 + 0.4 * Math.exp(-t / 0.008)) / SR; const tick = t < 0.003 ? (r() * 2 - 1) * 0.5 : 0; o[i] = (Math.sin(TAU * ph) * Math.exp(-t / 0.18) + res.run(tick) * 3) * vel; }
  return o;
}
export function tom(f, vel) { const o = buf(0.6); let ph = 0; for (let i = 0; i < o.length; i++) { const t = i / SR; ph += f * (1 + 0.5 * Math.exp(-t / 0.03)) / SR; o[i] = sat(Math.sin(TAU * ph) * Math.exp(-t / 0.25), 1.5) * vel; } return o; }
// Noise riser (HP sweeping up) and a downlifter/impact, for builds and drops.
export function riser(sec, r) { const o = buf(sec), f = new SVF(); for (let i = 0; i < o.length; i++) { const k = i / o.length; f.set(200 * Math.pow(50, k), 0.4); o[i] = f.run(r() * 2 - 1, 'bp') * k * k * 0.9; } return o; }
export function crash(vel, r) { const o = buf(2.2), hp = new Biquad('hp', 5000); for (let i = 0; i < o.length; i++) { const t = i / SR; o[i] = hp.run(r() * 2 - 1) * Math.exp(-t / 0.7) * 0.7 * vel; } return o; }

// ---------------- bass ----------------
// 808: sine + pitch drop + saturation so it is heard on phones; glide to the next note.
export function bass808(freq, dur, vel, glideTo = null) {
  const o = buf(dur + 0.05); let ph = 0, f = freq * 3;
  const gk = 1 - Math.exp(-1 / (0.06 * SR)), lp = new Biquad('lp', 5000);
  for (let i = 0; i < o.length; i++) {
    const t = i / SR;
    const target = glideTo && t > dur * 0.6 ? glideTo : freq;
    f = t < 0.04 ? freq * (1 + 2 * Math.exp(-t / 0.01)) : f + (target - f) * gk;
    ph += f / SR;
    const a = Math.min(1, t / 0.002) * Math.exp(-t / Math.max(0.4, dur * 1.2)) * (t > dur ? Math.max(0, 1 - (t - dur) / 0.05) : 1);
    o[i] = lp.run(Math.tanh(3 * Math.sin(TAU * ph)) * 0.6) * a * vel;
  }
  return o;
}
export function subBass(freq, dur, vel, { attack = 0.005, harm = 0.15 } = {}) {
  const o = buf(dur + 0.08); let ph = 0;
  for (let i = 0; i < o.length; i++) { const t = i / SR; ph += freq / SR; const a = Math.min(1, t / attack) * (t > dur ? Math.max(0, 1 - (t - dur) / 0.08) : 1); o[i] = sat(Math.sin(TAU * ph) + harm * Math.sin(2 * TAU * ph), 1.3) * a * vel; }
  return o;
}
export function pluckBass(freq, dur, vel) { // saw through a filter envelope: house/pop/synthwave
  const o = buf(dur + 0.05), f = new SVF(); let ph = 0, ph2 = 0.3;
  for (let i = 0; i < o.length; i++) { const t = i / SR; ph = (ph + freq / SR) % 1; ph2 = (ph2 + freq * 0.5 / SR) % 1; f.set(180 + 2200 * Math.exp(-t / 0.08), 0.3);
    const a = Math.min(1, t / 0.003) * (t > dur ? Math.max(0, 1 - (t - dur) / 0.04) : 1) * Math.exp(-t / 0.6);
    o[i] = f.run(saw(ph, freq / SR) * 0.6 + Math.sin(TAU * ph2) * 0.7) * a * vel; }
  return o;
}
export function uprightBass(freq, dur, vel, r) { // plucked, woody: lo-fi, blues
  const o = buf(dur + 0.1), lp = new Biquad('lp', 900); let ph = 0;
  for (let i = 0; i < o.length; i++) { const t = i / SR; ph += freq / SR; const a = env(t, 0.004, 0.5) * (t > dur ? Math.max(0, 1 - (t - dur) / 0.1) : 1);
    o[i] = lp.run(Math.sin(TAU * ph) + 0.4 * Math.sin(2 * TAU * ph) * Math.exp(-t / 0.08) + (t < 0.01 ? (r() - 0.5) * 0.3 : 0)) * a * vel; }
  return o;
}

// ---------------- keys, pads, leads ----------------
// Rhodes-style electric piano: 2-operator FM with a tine "ping" and a warm body.
export function ePiano(freq, dur, vel, r) {
  const len = dur + 0.6, o = buf(len); let pc = r(), pt = r(), pb = r();
  const idx = 0.6 + vel * 0.9;
  for (let i = 0; i < o.length; i++) {
    const t = i / SR;
    pt += freq * 14 / SR; pb += freq / SR; pc += freq / SR;
    const tine = Math.sin(TAU * pt) * 2.5 * idx * Math.exp(-t / 0.012);
    const body = Math.sin(TAU * pb) * (0.3 + 1.2 * Math.exp(-t / 0.9)) * idx * 0.6;
    const a = Math.min(1, t / 0.003) * Math.exp(-t / 1.8) * (t > dur ? Math.max(0, 1 - (t - dur) / 0.15) : 1);
    o[i] = sat(Math.sin(TAU * pc + tine + body), 1.3) * a * vel;
  }
  return o;
}
// Additive piano: inharmonic partials, upper ones decaying faster, 3 strings slightly detuned.
export function piano(freq, dur, vel) {
  const o = buf(dur + 0.4), B = 0.0004;
  for (let n = 1; n <= 9; n++) {
    const fn = n * freq * Math.sqrt(1 + B * n * n); if (fn > 12000) break;
    const amp = Math.pow(vel, n * 0.12) / Math.pow(n, 1.3), tau = 2.8 / Math.pow(n, 0.7);
    for (const det of [-0.0003, 0, 0.0003]) {
      const f = fn * (1 + det), w = TAU * f / SR;
      for (let i = 0; i < o.length; i++) { const t = i / SR; const two = 0.5 * Math.exp(-t / 0.3) + 0.5 * Math.exp(-t / tau); o[i] += Math.sin(w * i) * amp * two * (t > dur ? Math.max(0, 1 - (t - dur) / 0.3) : 1) / 3; }
    }
  }
  for (let i = 0; i < o.length; i++) o[i] *= Math.min(1, i / (SR * 0.002)) * vel * 0.8;
  return o;
}
// Supersaw: 7 detuned PolyBLEP saws, random phases, filtered. Returns [L, R] for width.
export function supersaw(freq, dur, vel, r, { detune = 0.35, cutoff = 3000, attack = 0.4, release = 1.2, voices = 7, res = 0.1, pitchBend = null } = {}) {
  const len = dur + release, n = Math.round(len * SR), L = new Float32Array(n), R = new Float32Array(n);
  const cents = [0, -11, 11, -22, 22, -35, 35, -48, 48].slice(0, voices).map((c) => c * detune);
  const pans = cents.map((_, k) => (k === 0 ? 0 : (k % 2 ? -1 : 1) * Math.min(0.8, 0.25 * Math.ceil(k / 2))));
  const ph = cents.map(() => r()), fl = new SVF(), fr = new SVF(); fl.set(cutoff, res); fr.set(cutoff, res);
  const e = adsr(n, attack, 0.5, 0.85, release, dur), norm = 1 / Math.sqrt(voices);
  for (let i = 0; i < n; i++) {
    const t = i / SR, pb = pitchBend ? Math.pow(2, pitchBend(t) / 12) : 1;
    let l = 0, rr = 0;
    for (let k = 0; k < cents.length; k++) {
      const f = freq * pb * Math.pow(2, cents[k] / 1200), dt = f / SR; ph[k] = (ph[k] + dt) % 1;
      const s = saw(ph[k], dt) * (k === 0 ? 1 : 0.6); l += s * (1 - pans[k]) * 0.5; rr += s * (1 + pans[k]) * 0.5;
    }
    L[i] = fl.run(l * norm) * e[i] * vel; R[i] = fr.run(rr * norm) * e[i] * vel;
  }
  return [L, R];
}
// Juno-style pad: saw + PWM square + sub, low-passed (chorus is added on the bus).
export function junoPad(freq, dur, vel, r, { attack = 0.5, release = 1.5, cutoff = 1800 } = {}) {
  const len = dur + release, n = Math.round(len * SR), o = new Float32Array(n), f = new SVF(); f.set(cutoff, 0.25);
  let p1 = r(), p2 = r(), p3 = r(); const e = adsr(n, attack, 1, 0.8, release, dur), dt = freq / SR;
  for (let i = 0; i < n; i++) { const t = i / SR; p1 = (p1 + dt) % 1; p2 = (p2 + dt * 1.003) % 1; p3 = (p3 + dt / 2) % 1;
    const pw = 0.5 + 0.3 * Math.sin(TAU * 0.6 * t); o[i] = f.run(saw(p1, dt) * 0.5 + square(p2, dt, pw) * 0.4 + square(p3, dt / 2) * 0.2) * e[i] * vel; }
  return o;
}
export function brass(freq, dur, vel, r) { // synthwave brass: two saws, filter envelope
  const len = dur + 0.3, n = Math.round(len * SR), o = new Float32Array(n), f = new SVF(); let p1 = r(), p2 = r(); const dt = freq / SR;
  for (let i = 0; i < n; i++) { const t = i / SR; p1 = (p1 + dt * 1.0046) % 1; p2 = (p2 + dt * 0.9954) % 1;
    const fe = t < 0.06 ? 400 + 3600 * (t / 0.06) : 1200 + 2800 * Math.exp(-(t - 0.06) / 0.4); f.set(fe, 0.2);
    const a = Math.min(1, t / 0.02) * (t > dur ? Math.max(0, 1 - (t - dur) / 0.3) : 0.85 + 0.15 * Math.exp(-t / 0.3));
    o[i] = f.run(saw(p1, dt) + saw(p2, dt)) * 0.5 * a * vel; }
  return o;
}
export function pluck(freq, dur, vel, r, { decay = 0.15, bright = 1 } = {}) { // filter-env pluck (synthwave/house/pop)
  const n = Math.round((dur + 0.3) * SR), o = new Float32Array(n), f = new SVF(); let p1 = r(), p2 = r(); const dt = freq / SR;
  for (let i = 0; i < n; i++) { const t = i / SR; p1 = (p1 + dt) % 1; p2 = (p2 + dt * 1.005) % 1; f.set(200 + 6000 * bright * Math.exp(-t / decay), 0.3);
    o[i] = f.run(saw(p1, dt) * 0.6 + square(p2, dt) * 0.3) * Math.min(1, t / 0.002) * Math.exp(-t / (decay * 2.2)) * vel; }
  return o;
}
export function bell(freq, dur, vel, { ratio = 3.5, index = 5, decay = 1.6 } = {}) { // FM bell / mallet
  const n = Math.round((dur + decay) * SR), o = new Float32Array(n);
  for (let i = 0; i < n; i++) { const t = i / SR; const I = index * Math.exp(-t / (decay * 0.4)) + 0.3; o[i] = Math.sin(TAU * freq * t + I * Math.sin(TAU * freq * ratio * t)) * Math.min(1, t / 0.002) * Math.exp(-t / decay) * vel; }
  return o;
}
export const marimba = (freq, dur, vel) => bell(freq, dur, vel, { ratio: 4, index: 3, decay: 0.35 });
export function organ(freq, dur, vel) { // drawbar organ for blues: 16', 8', 4' + slight overdrive, leslie on the bus
  const n = Math.round((dur + 0.08) * SR), o = new Float32Array(n);
  for (let i = 0; i < n; i++) { const t = i / SR; const a = Math.min(1, t / 0.01) * (t > dur ? Math.max(0, 1 - (t - dur) / 0.08) : 1);
    o[i] = sat(Math.sin(TAU * freq * 0.5 * t) * 0.5 + Math.sin(TAU * freq * t) + Math.sin(TAU * freq * 2 * t) * 0.6 + Math.sin(TAU * freq * 3 * t) * 0.25 + (t < 0.01 ? Math.sin(TAU * freq * 4 * t) * 0.4 : 0), 1.4) * a * vel * 0.5; }
  return o;
}
// Karplus-Strong plucked string: highlife guitar, blues guitar.
export function guitar(freq, dur, vel, r, { bright = 0.5, damp = 0.996 } = {}) {
  const n = Math.round((dur + 0.5) * SR), o = new Float32Array(n), N = Math.max(2, Math.round(SR / freq)), d = new Float32Array(N);
  let lp = 0; for (let i = 0; i < N; i++) { lp += ((r() * 2 - 1) - lp) * (0.3 + bright * 0.6); d[i] = lp; }
  let p = 0;
  for (let i = 0; i < n; i++) { const nx = (p + 1) % N; const v = 0.5 * (d[p] + d[nx]) * damp; o[i] = d[p] * vel * (i / SR > dur ? Math.max(0, 1 - (i / SR - dur) / 0.08) : 1); d[p] = v; p = nx; }
  return o;
}
export const hz = midiHz;
