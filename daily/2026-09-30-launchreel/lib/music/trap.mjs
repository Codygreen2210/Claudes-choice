// Trap / rap beats, modelled on how named producers build them (grooves and progressions only;
// melodies are generated). Hats are the lead instrument of the drums: they change rate every
// beat or two (8ths, 16ths, triplets, 1/32 rolls with pitch ramps). The 808 IS the bass and
// usually the kick. Melody is a sparse, dark 2-bar loop, not a pad.
import { SR, midiHz, Biquad, SVF } from './dsp.mjs';
import * as I from './instruments.mjs';
import { parseMotif, chordPcs } from './theory.mjs';

// Hat segment per beat: '8','16','t8','t16','32', optional pitch ramp like '32+5' or '32-5+7', '-' = rest.
const STYLES = {
  tay: { label: 'Tay Keith-style', bpm: 140, kick: true,
    b808: ['x.......x.x...x.', 'x.......x.x...x.', 'x.......x.x...x.', 'x.......x.x.x.x.'],
    hats: [['16', '16', '16', 't16'], ['16', '32', '16', '16'], ['16', '16', '16', 't16'], ['16', '16', '32+5', '32+12']],
    perc: { 3: { 15: 'rim' } }, leads: ['darkPiano', 'musicBox'] },
  metro: { label: 'Metro Boomin-style', bpm: 148, kick: false,
    b808: ['x.........x.....', 'x.....x...x.....', 'x.........x.....', 'x.....x...x.....'],
    hats: [['8', '8', '16', '8'], ['8', '8', '16', '8'], ['8', '8', '16', '8'], ['8', 't16', '8', '32+7']],
    snap: true, leads: ['musicBox', 'flute', 'choir'] },
  pierre: { label: "Pi'erre Bourne-style", bpm: 162, kick: false,
    b808: ['x..x..x...x..x..', 'x..x..x...x..x..', 'x..x..x...x..x..', 'x..x..x...x.....'],
    hats: [['t8', '16', 't8', '16'], ['t8', '16', 't8', '16'], ['t8', '16', 't8', '16'], ['t16', 't16', '32+3', '-']],
    plinks: true, leads: ['musicBox', 'squareLead'] },
  southside: { label: 'Southside-style', bpm: 140, kick: true,
    b808: ['x.....x.x.....x.', 'x.....x.x.....x.', 'x.....x.x.....x.', 'x.....x.x.x.x.x.'],
    hats: [['16', '32', '16', 't16'], ['16', '16', '16', '16'], ['16', '32', '16', 't16'], ['16', '16', '32', '32-5+7']],
    leads: ['darkPiano', 'choir'] },
};
const PROGS = [[[0, 'min'], [8, 'maj']], [[0, 'min'], [10, 'maj'], [8, 'maj'], [10, 'maj']], [[8, 'maj'], [10, 'maj'], [0, 'min'], [0, 'min']], [[0, 'min'], [5, 'min']], [[0, 'min'], [8, 'maj'], [3, 'maj'], [10, 'maj']]];
// Original 2-bar loop motifs (degree:16ths); '.' = rest.
const MOTIFS = ['5:2 .:2 b3:2 .:2 1:4 .:4 b6:2 5:2 .:4 b3:6 .:2', '1:3 1:3 b3:2 5:3 b3:3 1:2 b7-:3 b7-:3 1:2 b3:4 .:4', 'b6:1 5:1 b3:1 1:1 b6:1 5:1 b3:1 1:1 b6:1 5:1 b3:1 1:1 b6:1 5:1 b3:1 1:1 b2:8 .:8', '5:3 b6:3 5:2 b3:4 .:4 1:8 .:4 b7-:4'];

// 48 ticks per bar (12 per beat): where the hits of each hat segment fall within a beat.
const SEG = { 8: [0, 6], 16: [0, 3, 6, 9], t8: [0, 4, 8], t16: [0, 2, 4, 6, 8, 10], 32: [0, 1.5, 3, 4.5, 6, 7.5, 9, 10.5] };

export function styleFor(r) { const ks = Object.keys(STYLES); return ks[Math.floor(r() * ks.length)]; }
export const TRAP_STYLES = STYLES;

export function renderTrap(ctx) {
  const { add, r, keyPc, nBars, on, post, seconds } = ctx;
  const S = STYLES[ctx.style] || STYLES.tay;
  const bar = ctx.bar, tick = bar / 48, step = bar / 16;
  const prog = PROGS[Math.floor(r() * PROGS.length)];
  const chordOf = (b) => prog[b % prog.length];
  const introBars = nBars >= 6 ? 2 : nBars >= 4 ? 1 : 0;
  const mainT = introBars * bar;
  ctx.silence(mainT - bar / 4, mainT); // full stop on the last beat before the drop
  const kicks = ctx.kicks;

  // ---- drums (from the drop) ----
  if (on('drums')) for (let b = introBars; b < nBars; b++) {
    const m = b - introBars, v4 = m % 4, drop = m % 8 === 7; // bar 8 of each 8: drop-out on the last 2 beats
    // clap on beat 3, layered with a snare, slightly late
    const ct = b * bar + 8 * step + 0.004;
    add('snare', ct, I.clap(0.95, r), 1, 0); add('snare', ct, I.snare('trap', 0.45, r), 1, 0);
    if (S.snap && m % 2 === 1) add('perc', b * bar + 12 * step, I.rim(0.45), 1, -0.3);
    if (drop) for (const s of [12, 13, 14, 15]) add('snare', b * bar + s * step, I.clap(0.3 + (s - 12) * 0.18, r), 1, 0);
    // hats
    const segs = S.hats[v4];
    segs.forEach((seg, beatI) => {
      if (seg === '-' || (drop && beatI >= 2)) return;
      const mm = /^(t?\d+)([+-]\d+)?([+-]\d+)?$/.exec(seg); if (!mm) return;
      const pos = SEG[mm[1]] || SEG[16];
      const p0 = mm[3] ? +mm[2] : 0, p1 = mm[3] ? +mm[3] : mm[2] ? +mm[2] : 0;
      pos.forEach((tk, k) => {
        const roll = mm[1] === '32' || mm[1] === 't16';
        const vel = roll ? 0.45 + 0.4 * (k / pos.length) : 0.75 * (0.92 + r() * 0.16);
        const semis = p0 + (p1 - p0) * (k / Math.max(1, pos.length - 1));
        add('hats', b * bar + (beatI * 12 + tk) * tick, I.hat(false, vel, r, 1.05, semis), 1, 0.12);
      });
    });
    if (S.perc?.[v4]) for (const [s, kind] of Object.entries(S.perc[v4])) add('perc', b * bar + s * step, I.rim(0.5), 1, 0.3);
    if (S.plinks) for (const s of [3, 11]) add('perc', b * bar + s * step, I.bell(midiHz(84 + keyPc % 12), 0.1, 0.25, { ratio: 2, index: 1, decay: 0.12 }), 1, 0.35);
  }
  if (on('drums') && nBars > introBars) add('hats', mainT - bar / 4, reverseCymbal(bar / 4, r), 0.6, -0.2);

  // ---- 808 (the bassline; also the kick unless the style layers one) ----
  if (on('bass') || on('drums')) {
    const hits = [];
    for (let b = introBars; b < nBars; b++) {
      const m = b - introBars, grid = S.b808[m % 4], drop = m % 8 === 7;
      const root = 28 + ((keyPc + chordOf(b)[0] - 28) % 12 + 12) % 12; // E1..D#2
      for (let s = 0; s < 16; s++) {
        if (grid[s] !== 'x' || (drop && s >= 8)) continue;
        const lastOfBar = !grid.slice(s + 1).includes('x');
        let note = root;
        const slideUp = lastOfBar && s > 0 && m % 2 === 1 && r() < 0.75; // once per 2 bars: bend up, then back down to the next root
        if (slideUp) note = root + [12, 3, 7][Math.floor(r() * 3)];
        else if (s > 0 && r() < 0.15) note = root + [7, 10][Math.floor(r() * 2)];
        hits.push({ t: b * bar + s * step, note, slideUp });
      }
    }
    hits.forEach((h, i) => {
      const next = hits[i + 1];
      const dur = Math.max(0.12, (next ? next.t : seconds) - h.t);
      const prev = hits[i - 1];
      // a slide: the previous note bends into this one instead of a new attack
      const from = prev && (h.slideUp || prev.slideUp) ? midiHz(prev.note) : null;
      if (on('bass')) add('bass', h.t, I.tr808(midiHz(h.note), Math.min(dur, 2.4), 0.95, { from }), 1, 0);
      if (S.kick && on('drums') && !from) add('kick', h.t, I.kick('trap', 0.9, r), 1, 0);
      kicks.push(h.t);
    });
  }

  // ---- melody loop: sparse, dark, doubled an octave up ----
  if (on('lead') || on('chords')) {
    const inst = S.leads[Math.floor(r() * S.leads.length)];
    const motif = parseMotif(MOTIFS[Math.floor(r() * MOTIFS.length)]);
    const scalePcs = [0, 2, 3, 5, 7, 8, 11].map((x) => (x + keyPc) % 12);
    const base = 60 + (keyPc > 5 ? keyPc - 12 : keyPc);
    for (let b = 0; b < nBars; b += 2) {
      let st = 0;
      for (const n of motif) {
        const t = b * bar + st * step; st += n.len;
        if (n.rest || t >= seconds - 0.5) continue;
        let p = base + n.semis;
        const pcs = chordPcs(keyPc, chordOf(b + Math.floor((st - n.len) / 16)));
        if (!scalePcs.includes(((p % 12) + 12) % 12) && !pcs.includes(((p % 12) + 12) % 12)) p += 1;
        const dur = n.len * step * 0.95, v = 0.55;
        const mk = (pitch, vel) => inst === 'musicBox' ? I.musicBox(midiHz(pitch + 12), dur, vel) : inst === 'flute' ? I.flute(midiHz(pitch + 12), dur, vel, r) : inst === 'choir' ? I.choir(midiHz(pitch), dur * 1.5, vel * 0.7, r) : inst === 'squareLead' ? I.squareLead(midiHz(pitch + 12), dur, vel, r) : I.darkPiano(midiHz(pitch), dur, vel);
        if (on('lead')) { add('lead', t, mk(p, v), 1, -0.15); add('lead', t, mk(p + 12, v * 0.4), 1, 0.2); }
      }
    }
    // Intro: the melody starts muffled and opens up into the drop.
    post.push((buses) => {
      const b = buses.lead; if (!b || !introBars) return;
      const end = Math.round(mainT * SR), fl = new SVF(), fr = new SVF();
      for (let i = 0; i < end && i < b.L.length; i++) { const k = i / end; const fc = 700 * Math.pow(12, k * k); if (i % 32 === 0) { fl.set(fc, 0.2); fr.set(fc, 0.2); } b.L[i] = fl.run(b.L[i]); b.R[i] = fr.run(b.R[i]); }
    });
    // mono dotted-quarter delay, low feedback, filtered
    post.push((buses) => { const b = buses.lead; if (!b) return; const d = Math.round(bar * 0.375 * SR), hp = new Biquad('hp', 400), lp = new Biquad('lp', 3000); const tap = new Float32Array(b.L.length);
      for (let i = d; i < tap.length; i++) tap[i] = lp.run(hp.run((b.L[i - d] + b.R[i - d]) * 0.5 + tap[i - d] * 0.25)); for (let i = 0; i < tap.length; i++) { b.L[i] += tap[i] * 0.22; b.R[i] += tap[i] * 0.22; } });
  }
}
function reverseCymbal(sec, r) { const n = Math.round(sec * SR), o = new Float32Array(n), hp = new Biquad('hp', 5000); for (let i = 0; i < n; i++) { const k = i / n; o[i] = hp.run(r() * 2 - 1) * k * k * 0.6; } return o; }
