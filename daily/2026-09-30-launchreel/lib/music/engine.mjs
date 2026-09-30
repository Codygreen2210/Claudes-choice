// Turns a genre recipe into a finished, mastered track.
// Arrangement -> per-instrument buses (with swing and humanising) -> sends to reverb,
// sidechain, EQ -> master (glue compression, loudness to -14 LUFS, soft clip, limiter).
import { SR, TAU, rng, midiHz, db, Biquad, freeverb, chorus, pingPong, duckCurve, compress, limit, lufs, softClip } from './dsp.mjs';
import * as I from './instruments.mjs';
import { QUALITY, KEYS, chordPcs, voiceLead, spreadVoicing, phrase } from './theory.mjs';
import { GENRES, ALIAS } from './genres.mjs';
import { renderTrap, styleFor, TRAP_STYLES } from './trap.mjs';
import { renderBlues } from './blues.mjs';

export { GENRES };
const ROOTLESS = { m9: 'm9r', maj9: 'maj9r', 13: '9r', 9: '9r' };
const DRUM_BUS = { K: 'kick', S: 'snare', CL: 'snare', SN: 'snare', GS: 'snare', CH: 'hats', OH: 'hats', RIDE: 'hats', SH: 'perc', RIM: 'perc', CONGA: 'perc', TOM: 'perc' };
const SENDS = { snare: 0.7, chords: 0.45, pad: 0.6, lead: 0.55, arp: 0.35, guitar: 0.35, perc: 0.3, hats: 0.12 };
const HP = { horns: 150, chords: 150, pad: 200, lead: 220, perc: 200, arp: 200, guitar: 150, snare: 120 };

export function makeMusic({ seconds, seed = 7, key, genre, mood, bpm, volume = 0.5, parts = {} } = {}) {
  const gname = ALIAS[genre || mood] || genre || mood || 'lofi';
  const G = GENRES[gname] || GENRES.lofi;
  const on = (p) => parts[p] !== false;
  const r = rng(seed * 7919 + 13);
  const style = G.render === 'trap' ? styleFor(r) : null;
  const tempo = bpm || (style ? TRAP_STYLES[style].bpm : G.bpm), beat = 60 / tempo, bar = beat * 4, steps = G.steps, stepDur = bar / steps;
  const keyPc = KEYS[key] ?? KEYS[G.key] ?? 0;
  const n = Math.max(1, Math.round(seconds * SR));
  const nBars = Math.ceil(seconds / bar) + 1;
  const prog = G.progs ? G.progs[Math.floor(r() * G.progs.length)] : [[0, 'min']];
  const chordOfBar = (b) => prog[Math.floor(b / G.barsPerChord) % prog.length];

  // ---- arrangement ----
  const introBars = G.intro && nBars >= 6 ? (nBars >= 12 ? 2 : 1) : 0;
  const buildBar = G.build && nBars >= 6 ? introBars : -1;
  const mainStart = introBars + (buildBar >= 0 ? 1 : 0);
  const mainT = mainStart * bar;

  // ---- buses ----
  const buses = {};
  const bus = (name) => (buses[name] ||= { L: new Float32Array(n), R: new Float32Array(n) });
  const add = (name, at, sig, gain = 1, pan = 0) => {
    const b = bus(name), i0 = Math.round(at * SR), gl = gain * Math.min(1, 1 - pan), gr = gain * Math.min(1, 1 + pan);
    for (let i = Math.max(0, -i0); i < sig.length; i++) { const j = i0 + i; if (j >= n) break; b.L[j] += sig[i] * gl; b.R[j] += sig[i] * gr; }
  };
  const addSt = (name, at, [sl, sr], gain = 1) => {
    const b = bus(name), i0 = Math.round(at * SR);
    for (let i = Math.max(0, -i0); i < sl.length; i++) { const j = i0 + i; if (j >= n) break; b.L[j] += sl[i] * gain; b.R[j] += sr[i] * gain; }
  };
  const swingParts = G.swingParts || null;
  const stepTime = (b, s, part) => {
    const off = s % 2 === 1 && G.swing > 0.5 && (!swingParts || swingParts.includes(part)) ? (G.swing - 0.5) * 2 * stepDur : 0;
    return b * bar + s * stepDur + off;
  };
  const vOf = (c) => (c === 'x' ? 0.85 : c === 'r' ? 0.65 : /\d/.test(c) ? +c / 9 : 0);
  const kicks = [];
  const silences = [], post = [];

  // ---- drums ----
  if (!G.render && on('drums') && G.drums) {
    let congaTurn = 0;
    for (let b = 0; b < nBars; b++) {
      const isIntro = b < introBars, isBuild = b === buildBar, m = b - mainStart;
      let pat = G.drums.main;
      if (isBuild && G.drums.build) pat = G.drums.build;
      else if (m >= 0 && m % 8 === 7 && G.drums.fill) pat = G.drums.fill;
      else if (m >= 0 && m % 4 === 3 && G.drums.vari) pat = G.drums.vari;
      for (const [part, grid] of Object.entries(pat)) {
        if (isIntro && !(G.intro.drums || []).includes(part)) continue;
        for (let s = 0; s < steps; s++) {
          const c = grid[s] || '.'; const v0 = vOf(c); if (!v0) continue;
          const hits = c === 'r' ? [0, 0.5] : [0];
          for (const h of hits) {
            const v = Math.min(1, v0 * (0.92 + r() * 0.16));
            let t = stepTime(b, s + h, part);
            if (['CH', 'OH', 'SH', 'RIM', 'CONGA', 'RIDE'].includes(part)) t += (r() - 0.5) * 2 * (G.hatJitter || 0);
            if (['S', 'CL', 'GS'].includes(part)) t += (G.snareDrag || 0) + (r() - 0.5) * 0.004;
            let sig;
            switch (part) {
              case 'K': sig = I.kick(G.kick, v, r); kicks.push(t); break;
              case 'S': sig = I.snare(G.snare === 'clap' ? 'pop' : G.snare, v, r); break;
              case 'CL': sig = I.clap(v, r); break;
              case 'SN': sig = I.snare('pop', v * 0.5, r); break;
              case 'GS': sig = I.snare(G.snare === 'clap' ? 'pop' : G.snare, v * 0.35, r); break;
              case 'CH': sig = I.hat(false, v, r, G.hatBright || 1); break;
              case 'OH': sig = I.hat(true, v * 0.8, r, G.hatBright || 1); break;
              case 'RIDE': sig = I.hat(true, v * 0.55, r, 0.75); break;
              case 'SH': sig = I.shaker(v, r); break;
              case 'RIM': sig = I.rim(v); break;
              case 'CONGA': sig = I.conga(congaTurn++ % 3, v, r); break;
              case 'TOM': sig = I.tom([196, 164, 138, 110][s % 4], v); break;
            }
            if (sig) add(DRUM_BUS[part], t, sig, 1, { CH: 0.2, OH: 0.15, RIDE: 0.2, SH: -0.3, RIM: 0.25, CONGA: -0.35, TOM: (s % 4) * 0.2 - 0.3 }[part] || 0);
          }
        }
      }
    }
    if (G.fx.crash && mainStart > 0) add('hats', mainT, I.crash(0.8, r), 1.3, -0.2);
    if (buildBar >= 0) add('fx', buildBar * bar, I.riser(bar, r), 0.35);
  }

  if (!G.render) {
  // ---- harmony: voicings per chord ----
  const voicings = [];
  let prev = null;
  for (let b = 0; b < nBars; b++) {
    const [off, q] = chordOfBar(b);
    const C = G.chords;
    let notes;
    if (C.voicing === 'spread') notes = spreadVoicing(keyPc, [off, q], C.lo);
    else if (C.voicing === 'parallel') { const root = C.lo + ((keyPc + off - C.lo) % 12 + 12) % 12; notes = QUALITY[q].map((i) => root + i).filter((x) => x <= C.hi + 14); }
    else notes = voiceLead(keyPc, [off, C.voicing === 'rootless' ? ROOTLESS[q] || q : q], prev, { lo: C.lo, hi: C.hi });
    voicings.push(notes); prev = notes;
  }
  const rootMidi = (b, lo = 33) => { const [off] = chordOfBar(b); return lo + ((keyPc + off - lo) % 12 + 12) % 12; };

  // ---- chords ----
  if (on('chords')) {
    const C = G.chords, vel = C.vel ?? 0.6;
    const hitsOf = (grid) => [...grid].map((c, i) => [i, vOf(c) || (c === 'x' ? 0.85 : 0)]).filter(([, v]) => v);
    for (let b = 0; b < nBars; b++) {
      const chordStart = b % G.barsPerChord === 0;
      if (C.hold && !chordStart) continue;
      const hits = hitsOf(C.grid);
      hits.forEach(([s, hv], hi) => {
        const next = hits[hi + 1]?.[0] ?? steps;
        let t = stepTime(b, s, 'chords');
        if (C.push && s === 0 && r() < 0.35) t -= stepDur;
        const dur = C.hold ? bar * G.barsPerChord - 0.05 : (next - s) * stepDur * 0.92;
        const v = vel * (hv > 0 && hv !== 0.85 ? hv : 1) * (0.9 + r() * 0.1);
        playChord(C.inst, voicings[b], Math.max(0, t), dur, v);
      });
    }
    if (G.pad) for (let b = 0; b < nBars; b += G.barsPerChord) playChord('supersawPadBus', spreadVoicing(keyPc, chordOfBar(b), 48), b * bar, bar * G.barsPerChord - 0.05, G.pad.vel);
    if (G.arp) {
      const A = G.arp;
      for (let b = introBars; b < nBars; b++) {
        const vs = [...voicings[b]].sort((x, y) => x - y);
        for (let s = 0; s < steps; s++) {
          if (A.grid[s] === '.') continue;
          const idx = A.pattern[s % A.pattern.length];
          const note = vs[idx % vs.length] + (idx >= vs.length ? 12 : 0) + A.octave;
          add('arp', stepTime(b, s, 'arp'), I.pluck(midiHz(note), stepDur * 0.9, A.vel * (s % 4 === 0 ? 1 : 0.75), r, { decay: 0.1 }), 1, s % 2 ? 0.3 : -0.3);
        }
      }
    }
    if (G.guitar) {
      for (let b = introBars; b < nBars; b++) {
        const pcs = voicings[b].map((x) => x + 12).filter((x) => x <= 84);
        let k = 0;
        for (let s = 0; s < steps; s++) if (G.guitar.grid[s] === 'x') add('guitar', stepTime(b, s, 'SH'), I.guitar(midiHz(pcs[k++ % pcs.length]), 0.18, 0.55 + r() * 0.2, r, { bright: 0.65, damp: 0.99 }), 1, 0.35);
      }
    }
  }
  function playChord(inst, notes, t, dur, v) {
    notes.forEach((m, k) => {
      const f = midiHz(m), pan = (k / Math.max(1, notes.length - 1)) * 0.6 - 0.3, strum = (G.chords.strum || 0.004) * k;
      const lofiDetune = G.fx.lofi ? Math.pow(2, ((r() - 0.5) * 16) / 1200) : 1;
      switch (inst) {
        case 'epiano': add('chords', t + strum, I.ePiano(f * lofiDetune, dur, v * 0.5, r), 1, pan); break;
        case 'junoPad': add('chords', t, I.junoPad(f, dur, v * 0.3, r), 1, pan); break;
        case 'darkPad': add('chords', t, I.junoPad(f, dur, v * 0.3, r, { cutoff: 900, attack: 0.8 }), 1, pan); break;
        case 'supersawPad': addSt('chords', t, I.supersaw(f, dur, v * 0.3, r, { detune: 0.4, cutoff: 2600, attack: 1.2, release: 2 })); break;
        case 'supersawPadBus': addSt('pad', t, I.supersaw(f, dur, v * 0.3, r, { detune: 0.35, cutoff: 3000, attack: 0.3, release: 0.8 })); break;
        case 'stab': add('chords', t, I.pluck(f, dur, v * 0.45, r, { decay: 0.09, bright: 0.55 }), 1, pan); break;
        case 'pluckChord': add('chords', t + strum, I.pluck(f, dur, v * 0.4, r, { decay: 0.12, bright: 0.8 }), 1, pan); break;
        case 'futureSaw': addSt('chords', t, I.supersaw(f, dur, v * 0.35, r, { detune: 0.8, cutoff: 7000, attack: 0.008, release: 0.12, voices: 7, pitchBend: (tt) => -2 * Math.exp(-tt / 0.05) + 0.3 * Math.sin(TAU * (tempo / 60) * 2 * tt) })); break;
        case 'organ': add('chords', t, I.organ(f, dur, v * 0.45), 1, pan); break;
        default: add('chords', t, I.ePiano(f, dur, v * 0.5, r), 1, pan);
      }
    });
  }

  // ---- bass ----
  if (on('bass')) {
    const B = G.bass;
    for (let b = 0; b < nBars; b++) {
      const grid = B.follow ? (G.drums.main[B.follow]) : B.grid;
      const hits = [...grid].map((c, i) => [i, vOf(c) || (c === 'x' ? 0.85 : 0)]).filter(([, v]) => v);
      const root = rootMidi(b, B.inst === '808' ? 30 : 33);
      hits.forEach(([s, v], hi) => {
        const next = hits[hi + 1]?.[0] ?? steps;
        const dur = (next - s) * stepDur * (B.legato ?? 0.8);
        let note = root;
        if (B.octaves) note += B.octaves[hi % B.octaves.length];
        if (B.walk) note += B.walk[(b * hits.length + hi) % B.walk.length];
        if (B.melodic) note += B.melodic[hi % B.melodic.length];
        const t = stepTime(b, s, 'bass');
        const f = midiHz(note);
        let sig;
        if (B.inst === '808') { const glide = B.glide && hi === hits.length - 1 && b % 2 === 1 && r() < 0.6 ? f * (r() < 0.5 ? 2 : 0.75) : null; sig = I.bass808(f, Math.max(0.2, dur), v, glide); }
        else if (B.inst === 'sub') sig = I.subBass(f, Math.max(0.1, dur), v * 0.8, { attack: B.attack || 0.005 });
        else if (B.inst === 'upright') sig = I.uprightBass(f, Math.max(0.12, dur), v, r);
        else sig = I.pluckBass(f, Math.max(0.08, dur), v * 0.8);
        add('bass', t, sig, 1, 0);
      });
    }
  }

  // ---- lead / hook ----
  if (on('lead') && G.lead) {
    const Ld = G.lead, motif = Ld.motifs[Math.floor(r() * Ld.motifs.length)];
    const startBar = mainStart + (Ld.from || 0);
    const scale = G.scale;
    const baseOct = Ld.base + (keyPc > 6 ? -12 : 0);
    const chordAtAbs = (bar0) => (stepAbs) => chordPcs(keyPc, chordOfBar(bar0 + Math.floor(stepAbs / steps)));
    let b = startBar, turn = 0;
    while (b < nBars - 1) {
      const ph = phrase({ motif, key: keyPc, chordAt: chordAtAbs(b), scale, stepsPerBar: steps, base: baseOct - (keyPc % 12), r });
      const bars = ph.length / steps;
      if (turn % (Ld.every || 1) === 0 || Ld.loopBar) {
        for (const nt of ph.notes) {
          if (Ld.sparse && r() < Ld.sparse) continue;
          const t = stepTime(b, nt.step, 'lead');
          if (t >= seconds - 1) continue;
          const f = midiHz(nt.midi), dur = nt.len * stepDur * 0.9, v = Ld.vel * nt.vel;
          let sig;
          switch (Ld.inst) {
            case 'piano': sig = I.piano(f, dur, v); break;
            case 'brass': sig = I.brass(f, dur, v * 0.6, r); break;
            case 'bell': sig = I.bell(f, dur, v * 0.5); break;
            case 'marimba': sig = I.marimba(f, dur, v * 0.7); break;
            case 'guitar': sig = I.guitar(f, dur, v * 0.8, r, { bright: 0.75, damp: 0.997 }); break;
            default: sig = I.pluck(f, dur, v * 0.6, r, { decay: 0.22, bright: 0.9 });
          }
          add('lead', t, sig, 1, 0.05);
        }
      }
      b += bars; turn++;
    }
  }

  }
  if (G.render) {
    const ctx = { add, addSt, bus, r, keyPc, nBars, bar, beat, seconds, n, on, post, kicks, style, silence: (a, b2) => silences.push([a, b2]) };
    (G.render === 'trap' ? renderTrap : renderBlues)(ctx);
  }
  for (const fn of post) fn(buses);
  // ---- bus processing ----
  const pro = (name, fn) => { if (buses[name]) fn(buses[name]); };
  for (const [name, f] of Object.entries(HP)) pro(name, (b) => { new Biquad('hp', f).process(b.L); new Biquad('hp', f).process(b.R); });
  pro('bass', (b) => { new Biquad('lp', 5000).process(b.L); new Biquad('lp', 5000).process(b.R); });
  pro('kick', (b) => { for (const x of [b.L, b.R]) { new Biquad('peak', 60, 1, 2).process(x); } });
  if (G.fx.lofi) {
    const crush = (b) => { for (const x of [b.L, b.R]) { new Biquad('lp', 7500).process(x); for (let i = 0; i < x.length; i++) x[i] = Math.round(x[i] * 2048) / 2048; } };
    ['kick', 'snare', 'hats', 'perc'].forEach((k) => pro(k, crush));
    pro('chords', (b) => wow(b));
  }
  if (G.fx.chorus) { pro('chords', (b) => chorus(b.L, b.R, { rate: 0.6, mix: 0.45 })); pro('pad', (b) => chorus(b.L, b.R)); }
  if (G.fx.leslie) pro('chords', (b) => chorus(b.L, b.R, { rate: 5.5, depth: 0.0006, base: 0.003, mix: 0.5 }));
  if (G.fx.pingpong) { pro('lead', (b) => pingPong(b.L, b.R, { time: beat * G.fx.pingpong, feedback: 0.35, wet: 0.25 })); }
  if (G.arp?.delay) pro('arp', (b) => pingPong(b.L, b.R, { time: beat * G.arp.delay, feedback: 0.4, wet: 0.35 }));
  // sidechain
  if (G.fx.duck && kicks.length) {
    const g = duckCurve(n, kicks, { ...G.fx.duck, release: G.fx.duck.release * beat });
    for (const name of ['bass', 'chords', 'pad', 'arp', 'lead', 'guitar']) pro(name, (b) => { const k = name === 'lead' ? 0.5 : 1; for (let i = 0; i < n; i++) { const gg = 1 - (1 - g[i]) * k; b.L[i] *= gg; b.R[i] *= gg; } });
  }

  // ---- mix + reverb send ----
  const L = new Float32Array(n), R = new Float32Array(n), sL = new Float32Array(n), sR = new Float32Array(n);
  for (const [name, b] of Object.entries(buses)) {
    const g = db(G.mix[name] ?? (name === 'fx' ? -10 : -8)), send = (G.sends || SENDS)[name] ?? 0;
    for (let i = 0; i < n; i++) { const l = b.L[i] * g, rr = b.R[i] * g; L[i] += l; R[i] += rr; if (send) { sL[i] += l * send; sR[i] += rr * send; } }
  }
  const rv = G.fx.reverb || { room: 0.6, damp: 0.5, wet: 0.12 };
  const [wL, wR] = freeverb(sL, sR, { room: rv.room, damp: rv.damp, predelay: rv.predelay || 0.02 });
  const wet = rv.wet * 3.2;
  for (let i = 0; i < n; i++) { L[i] += wL[i] * wet; R[i] += wR[i] * wet; }
  if (G.fx.lofi) { let lp = 0; for (let i = 0; i < n; i++) { const w = r() * 2 - 1; lp += (w - lp) * 0.3; const crackle = r() < 5 / SR ? (r() - 0.3) * 0.25 : 0; L[i] += lp * 0.004 + crackle; R[i] += lp * 0.004 + crackle; } }
  // silence the last half-beat before the drop
  if (buildBar >= 0) { const a = Math.round((mainT - beat * 0.5) * SR), bEnd = Math.round(mainT * SR), ramp = Math.round(0.005 * SR); for (let i = a; i < bEnd && i < n; i++) { const gg = Math.min(1, Math.max(0, Math.min(i - a, bEnd - i) / ramp)); const k = 1 - gg; L[i] *= k; R[i] *= k; } }

  for (const [a0, b0] of silences) { const a = Math.max(0, Math.round(a0 * SR)), bEnd = Math.round(b0 * SR), ramp = Math.round(0.005 * SR); for (let i = a; i < bEnd && i < n; i++) { const k = 1 - Math.min(1, Math.max(0, Math.min(i - a, bEnd - i) / ramp)); L[i] *= k; R[i] *= k; } }
  // ---- master ----
  new Biquad('hp', 30).process(L); new Biquad('hp', 30).process(R);
  compress(L, R, { threshold: -20, ratio: 2, attack: 0.03, release: 0.2 });
  const loud = lufs(L, R), target = (G.lufs ?? -14) + 20 * Math.log10(Math.max(0.05, volume) / 0.5);
  const gain = isFinite(loud) ? db(target - loud) : 1;
  for (let i = 0; i < n; i++) { L[i] = softClip(L[i] * gain, 0.85); R[i] = softClip(R[i] * gain, 0.85); }
  limit(L, R, 0.79); // leaves room for inter-sample peaks after MP3/AAC encoding
  const fi = Math.min(n, SR * 0.25), fo = Math.min(n, SR * 2.5);
  for (let i = 0; i < fi; i++) { L[i] *= i / fi; R[i] *= i / fi; }
  for (let i = 0; i < fo; i++) { const k = i / fo; L[n - 1 - i] *= k; R[n - 1 - i] *= k; }
  return wav(L, R, 1);
}

// Tape wow and flutter: read through a slowly wobbling delay (lo-fi keys).
function wow(b) {
  for (const x of [b.L, b.R]) {
    const src = Float32Array.from(x), base = 0.005 * SR;
    for (let i = 0; i < x.length; i++) {
      const d = base + 0.0025 * SR * Math.sin(TAU * 0.5 * i / SR) + 0.0003 * SR * Math.sin(TAU * 6 * i / SR);
      const p = i - d, p0 = Math.floor(p), f = p - p0;
      x[i] = p0 >= 0 && p0 + 1 < src.length ? src[p0] + (src[p0 + 1] - src[p0]) * f : 0;
    }
  }
}

export function wav(L, R, g = 1, dither = true) {
  const n = L.length, b = Buffer.alloc(44 + n * 4), dr = rng(9973);
  b.write('RIFF', 0); b.writeUInt32LE(36 + n * 4, 4); b.write('WAVE', 8); b.write('fmt ', 12);
  b.writeUInt32LE(16, 16); b.writeUInt16LE(1, 20); b.writeUInt16LE(2, 22); b.writeUInt32LE(SR, 24);
  b.writeUInt32LE(SR * 4, 28); b.writeUInt16LE(4, 32); b.writeUInt16LE(16, 34); b.write('data', 36); b.writeUInt32LE(n * 4, 40);
  for (let i = 0; i < n; i++) {
    // TPDF dither when going to 16-bit
    const d = dither ? (dr() - dr()) / 32767 : 0;
    b.writeInt16LE(Math.max(-32767, Math.min(32767, Math.round((L[i] * g + d) * 32767))), 44 + i * 4);
    b.writeInt16LE(Math.max(-32767, Math.min(32767, Math.round((R[i] * g + d) * 32767))), 46 + i * 4);
  }
  return b;
}
