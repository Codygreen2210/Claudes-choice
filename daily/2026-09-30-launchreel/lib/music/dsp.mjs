// DSP building blocks, sample by sample at 44.1 kHz. Recipes from the RBJ EQ cookbook,
// Cytomic's state-variable filter, PolyBLEP oscillators, EarLevel ADSR and Jezar's Freeverb.
export const SR = 44100;
export const TAU = Math.PI * 2;

export function rng(seed) { let s = seed >>> 0 || 1; return () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296; }
export const midiHz = (m) => 440 * Math.pow(2, (m - 69) / 12);
export const db = (d) => Math.pow(10, d / 20);

// ---- oscillators (PolyBLEP removes the harsh aliasing of naive saws/squares) ----
function blep(t, dt) {
  if (t < dt) { t /= dt; return t + t - t * t - 1; }
  if (t > 1 - dt) { t = (t - 1) / dt; return t * t + t + t + 1; }
  return 0;
}
export function saw(ph, dt) { return 2 * ph - 1 - blep(ph, dt); }
export function square(ph, dt, pw = 0.5) { return (ph < pw ? 1 : -1) + blep(ph, dt) - blep((ph + 1 - pw) % 1, dt); }

// ---- filters ----
// Cytomic state-variable filter: stable while swept. mode 'lp' | 'hp' | 'bp'.
export class SVF {
  constructor() { this.ic1 = 0; this.ic2 = 0; this.set(1000, 0.1); }
  set(fc, res = 0.1) {
    const g = Math.tan(Math.PI * Math.min(fc, SR * 0.45) / SR), k = 2 - 2 * Math.min(res, 0.98);
    this.k = k; this.a1 = 1 / (1 + g * (g + k)); this.a2 = g * this.a1; this.a3 = g * this.a2;
  }
  run(x, mode = 'lp') {
    const v3 = x - this.ic2, v1 = this.a1 * this.ic1 + this.a2 * v3, v2 = this.ic2 + this.a2 * this.ic1 + this.a3 * v3;
    this.ic1 = 2 * v1 - this.ic1; this.ic2 = 2 * v2 - this.ic2;
    return mode === 'lp' ? v2 : mode === 'bp' ? v1 : x - this.k * v1 - v2;
  }
}
// RBJ biquad. type: lp hp bp peak lowshelf highshelf
export class Biquad {
  constructor(type, f, q = 0.707, gainDb = 0) {
    const w = TAU * Math.min(f, SR * 0.45) / SR, cs = Math.cos(w), sn = Math.sin(w), a = sn / (2 * q), A = Math.pow(10, gainDb / 40);
    let b0, b1, b2, a0, a1, a2;
    if (type === 'lp') { b0 = (1 - cs) / 2; b1 = 1 - cs; b2 = b0; a0 = 1 + a; a1 = -2 * cs; a2 = 1 - a; }
    else if (type === 'hp') { b0 = (1 + cs) / 2; b1 = -(1 + cs); b2 = b0; a0 = 1 + a; a1 = -2 * cs; a2 = 1 - a; }
    else if (type === 'bp') { b0 = a; b1 = 0; b2 = -a; a0 = 1 + a; a1 = -2 * cs; a2 = 1 - a; }
    else if (type === 'peak') { b0 = 1 + a * A; b1 = -2 * cs; b2 = 1 - a * A; a0 = 1 + a / A; a1 = -2 * cs; a2 = 1 - a / A; }
    else { // shelves
      const sq = 2 * Math.sqrt(A) * a, s = type === 'lowshelf' ? 1 : -1;
      b0 = A * ((A + 1) - s * (A - 1) * cs + sq); b1 = s * 2 * A * ((A - 1) - s * (A + 1) * cs); b2 = A * ((A + 1) - s * (A - 1) * cs - sq);
      a0 = (A + 1) + s * (A - 1) * cs + sq; a1 = -s * 2 * ((A - 1) + s * (A + 1) * cs); a2 = (A + 1) + s * (A - 1) * cs - sq;
    }
    this.b0 = b0 / a0; this.b1 = b1 / a0; this.b2 = b2 / a0; this.a1 = a1 / a0; this.a2 = a2 / a0;
    this.x1 = this.x2 = this.y1 = this.y2 = 0;
  }
  run(x) { const y = this.b0 * x + this.b1 * this.x1 + this.b2 * this.x2 - this.a1 * this.y1 - this.a2 * this.y2; this.x2 = this.x1; this.x1 = x; this.y2 = this.y1; this.y1 = y; return y; }
  process(buf) { for (let i = 0; i < buf.length; i++) buf[i] = this.run(buf[i]); return buf; }
}
export function eq(buf, ...bands) { for (const b of bands) new Biquad(...b).process(buf); return buf; }

// ---- envelopes ----
// Exponential ADSR sampled into an array (a, d, r in seconds; s 0..1; hold = seconds before release).
export function adsr(len, a, d, s, r, hold) {
  const out = new Float32Array(len);
  const aN = Math.max(1, Math.round(a * SR)), hN = Math.max(1, Math.round(hold * SR)), rN = Math.max(1, Math.round(r * SR));
  const dk = Math.exp(-1 / Math.max(1, (d * SR) / 4));
  let v = 0, relV = 0;
  for (let i = 0; i < len; i++) {
    if (i < hN) v = i < aN ? 1 - Math.pow(1 - i / aN, 2.2) : s + (v - s) * dk;
    else { if (i === hN) relV = v; const k = (i - hN) / rN; v = k >= 1 ? 0 : relV * Math.exp(-4 * k) * (1 - k); }
    out[i] = v;
  }
  return out;
}
export const softClip = (x, t = 0.8) => (Math.abs(x) <= t ? x : Math.sign(x) * (t + (1 - t) * Math.tanh((Math.abs(x) - t) / (1 - t))));
export const sat = (x, drive = 2) => Math.tanh(drive * x) / Math.tanh(drive);

// ---- effects ----
const COMBS = [1116, 1188, 1277, 1356, 1422, 1491, 1557, 1617], APS = [556, 441, 341, 225];
// Freeverb on a stereo send. Returns wet L/R.
export function freeverb(inL, inR, { room = 0.7, damp = 0.4, predelay = 0.02, hp = 250, lp = 7000 } = {}) {
  const n = inL.length, fb = room * 0.28 + 0.7, dmp = damp * 0.4, pd = Math.round(predelay * SR);
  const hpL = new Biquad('hp', hp), hpR = new Biquad('hp', hp);
  const outL = new Float32Array(n), outR = new Float32Array(n);
  for (const [src, dst, spread, hpf] of [[inL, outL, 0, hpL], [inR, outR, 23, hpR]]) {
    const combs = COMBS.map((c) => ({ buf: new Float32Array(c + spread), i: 0, store: 0 }));
    const aps = APS.map((c) => ({ buf: new Float32Array(c + spread), i: 0 }));
    for (let s = 0; s < n; s++) {
      const x = (s >= pd ? hpf.run(src[s - pd]) : 0) * 0.015;
      let acc = 0;
      for (const c of combs) { const o = c.buf[c.i]; c.store = o * (1 - dmp) + c.store * dmp; c.buf[c.i] = x + c.store * fb; if (++c.i >= c.buf.length) c.i = 0; acc += o; }
      for (const a of aps) { const b = a.buf[a.i]; const y = -acc + b; a.buf[a.i] = acc + b * 0.5; if (++a.i >= a.buf.length) a.i = 0; acc = y; }
      dst[s] = acc;
    }
  }
  const l1 = new Biquad('lp', lp), l2 = new Biquad('lp', lp);
  l1.process(outL); l2.process(outR);
  return [outL, outR];
}
// Stereo chorus (Juno-ish): modulated short delays, L and R LFOs opposite.
export function chorus(L, R, { rate = 0.6, depth = 0.0018, base = 0.0075, mix = 0.45 } = {}) {
  const n = L.length, size = Math.ceil((base + depth) * SR) + 4, bl = new Float32Array(size), br = new Float32Array(size);
  let w = 0;
  for (let i = 0; i < n; i++) {
    bl[w] = L[i]; br[w] = R[i];
    const ph = TAU * rate * i / SR;
    const tap = (buf, d) => { const pos = w - d * SR; const p0 = Math.floor(pos), f = pos - p0; const a = buf[(p0 + size) % size], b = buf[(p0 + 1 + size) % size]; return a + (b - a) * f; };
    const wl = tap(bl, base + depth * Math.sin(ph)), wr = tap(br, base - depth * Math.sin(ph));
    L[i] = L[i] * (1 - mix) + wl * mix; R[i] = R[i] * (1 - mix) + wr * mix;
    w = (w + 1) % size;
  }
}
// Tempo-synced ping-pong delay, darkening repeats. Adds into L/R.
export function pingPong(L, R, { time, feedback = 0.38, wet = 0.2 }) {
  const n = L.length, d = Math.round(time * SR); const dl = new Float32Array(n), dr = new Float32Array(n);
  const lpL = new Biquad('lp', 4500), lpR = new Biquad('lp', 4500), hpL = new Biquad('hp', 300), hpR = new Biquad('hp', 300);
  for (let i = d; i < n; i++) {
    dl[i] = lpL.run(hpL.run((L[i - d] + R[i - d]) * 0.5 + dr[i - d] * feedback));
    dr[i] = lpR.run(hpR.run(dl[i - d] * feedback));
  }
  for (let i = 0; i < n; i++) { L[i] += dl[i] * wet; R[i] += dr[i] * wet; }
}
// Deterministic sidechain: a gain curve that dips at each kick and recovers.
export function duckCurve(n, kicks, { depth = 0.6, release = 0.25, curve = 2 }) {
  const g = new Float32Array(n).fill(1), rel = release * SR, att = 0.003 * SR;
  for (const k of kicks) {
    const i0 = Math.round(k * SR);
    for (let i = Math.max(0, i0 - att); i < i0 + rel && i < n; i++) {
      const v = i < i0 ? 1 - depth * ((i - (i0 - att)) / att) : 1 - depth * (1 - Math.pow((i - i0) / rel, 1 / curve));
      if (v < g[i]) g[i] = v;
    }
  }
  return g;
}
// Feed-forward compressor (log domain, RMS-ish detector), stereo linked. In place.
export function compress(L, R, { threshold = -18, ratio = 2, attack = 0.03, release = 0.2, makeup = 0, knee = 6 }) {
  const aA = Math.exp(-1 / (attack * SR)), aR = Math.exp(-1 / (release * SR));
  let env = 0, rms = 0; const rk = Math.exp(-1 / (0.01 * SR));
  for (let i = 0; i < L.length; i++) {
    const p = Math.max(L[i] * L[i], R[i] * R[i]); rms = rk * rms + (1 - rk) * p;
    const x = 10 * Math.log10(rms + 1e-12);
    let over = x - threshold, gc = 0;
    if (over > knee / 2) gc = -over * (1 - 1 / ratio);
    else if (over > -knee / 2) gc = -(1 - 1 / ratio) * Math.pow(over + knee / 2, 2) / (2 * knee);
    env = gc < env ? aA * env + (1 - aA) * gc : aR * env + (1 - aR) * gc;
    const g = Math.pow(10, (env + makeup) / 20); L[i] *= g; R[i] *= g;
  }
}
// Lookahead limiter to a ceiling (linear), 5 ms lookahead, smooth release.
export function limit(L, R, ceiling = 0.89) {
  const n = L.length, la = Math.round(0.005 * SR), rel = Math.exp(-1 / (0.06 * SR));
  const need = new Float32Array(n);
  for (let i = 0; i < n; i++) { const p = Math.max(Math.abs(L[i]), Math.abs(R[i])); need[i] = p > ceiling ? ceiling / p : 1; }
  // minimum over the lookahead window (sliding, simple O(n*la/8) with stride)
  const gmin = new Float32Array(n).fill(1);
  for (let i = 0; i < n; i++) if (need[i] < 1) for (let j = Math.max(0, i - la); j <= i; j++) if (need[i] < gmin[j]) gmin[j] = need[i];
  let g = 1;
  for (let i = 0; i < n; i++) {
    const tgt = gmin[i];
    g = tgt < g ? tgt : rel * g + (1 - rel) * tgt;
    L[i] *= g; R[i] *= g;
  }
  for (let i = 0; i < n; i++) { L[i] = Math.max(-ceiling, Math.min(ceiling, L[i])); R[i] = Math.max(-ceiling, Math.min(ceiling, R[i])); }
}
// Integrated loudness (ITU-R BS.1770, simplified gating) in LUFS.
export function lufs(L, R) {
  const kw = (buf) => { const a = Float32Array.from(buf); new Biquad('highshelf', 1681, 0.707, 4).process(a); new Biquad('hp', 38, 0.5).process(a); return a; };
  const kl = kw(L), kr = kw(R), blk = Math.round(0.4 * SR), hop = Math.round(0.1 * SR);
  const ms = [];
  for (let s = 0; s + blk <= kl.length; s += hop) { let sum = 0; for (let i = s; i < s + blk; i++) sum += kl[i] * kl[i] + kr[i] * kr[i]; ms.push(sum / blk); }
  const L0 = (m) => -0.691 + 10 * Math.log10(m + 1e-12);
  let g = ms.filter((m) => L0(m) > -70); if (!g.length) return -70;
  const rel = L0(g.reduce((a, b) => a + b, 0) / g.length) - 10;
  g = g.filter((m) => L0(m) > rel);
  return L0(g.reduce((a, b) => a + b, 0) / g.length);
}
