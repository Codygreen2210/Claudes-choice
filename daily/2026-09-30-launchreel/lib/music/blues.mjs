// Slow blues in the B.B. King tradition: 12/8 feel, horn section, triplet piano, round electric
// bass, and a guitar that sings: bends, a fast one-sided "hummingbird" vibrato, sparse
// call-and-response phrases starting on pickups. Changes are the standard shared forms; the
// licks are original, written to his techniques (the "B.B. box": 1 2 b3 3 4 5 6).
import { SR, midiHz, Biquad } from './dsp.mjs';
import * as I from './instruments.mjs';
import { QUALITY } from './theory.mjs';

QUALITY['9n5'] = [0, 4, 10, 14]; // horn-style voicings leave out the 5th
QUALITY['13n5'] = [0, 4, 10, 14, 21];
// 12-bar slow blues with quick change and turnaround; a bar can hold two chords (half each).
const FORM = [[[0, '9n5']], [[5, '9n5']], [[0, '9n5']], [[0, '13n5']], [[5, '9n5']], [[5, 'dim7']], [[0, '9n5']], [[9, '7']], [[2, 'm7']], [[7, '9n5']], [[0, '9n5'], [5, '9n5']], [[0, '9n5'], [7, '7#9']]];
QUALITY.dim7 = QUALITY.dim7 || [0, 3, 6, 9];
const DEG = { 1: 0, b2: 1, 2: 2, b3: 3, 3: 4, 4: 5, b5: 6, 5: 7, b6: 8, 6: 9, b7: 10, 7: 11 };
const semis = (d) => { const m = /^([b#]?\d)([\^v]?)$/.exec(d); return DEG[m[1]] + (m[2] === '^' ? 12 : m[2] === 'v' ? -12 : 0); };
// Original licks (length in 12/8 eighths). bend: bend up to that degree; pre: start bent up from that degree and release; grace: slide in from a half step below.
const LICKS = [
  [{ d: '2', l: 1, bend: '3' }, { d: '3', l: 1 }, { d: '1', l: 4, vib: 1 }],
  [{ d: '4', l: 1 }, { d: '5', l: 1 }, { d: 'b7', l: 2, grace: 1 }, { d: '6', l: 1 }, { d: '5', l: 4, vib: 1 }],
  [{ d: '4', l: 5, bend: '5', vib: 1 }, { d: '4', l: 1, pre: '5' }, { d: 'b3', l: 1 }, { d: '1', l: 3, vib: 1 }],
  [{ d: '5v', l: 1 }, { d: '6v', l: 1 }, { d: '1', l: 1 }, { d: 'b3', l: 1, cents: 30 }, { d: '1', l: 5, vib: 1 }],
  [{ d: '1^', l: 2, pre: '2^' }, { d: '6', l: 1 }, { d: '5', l: 1 }, { d: '3', l: 2, grace: 1 }, { d: '1', l: 4, vib: 1 }],
  [{ d: '6', l: 1, bend: 'b7' }, { d: '5', l: 1 }, { d: '3', l: 1 }, { d: '2', l: 1 }, { d: '1', l: 5, vib: 1 }],
];
const ENDING = [{ d: '3', l: 1 }, { d: '2', l: 1 }, { d: '1', l: 1 }, { d: '6v', l: 1 }, { d: '5v', l: 2 }, { d: '2', l: 1, bend: '3' }, { d: '1', l: 12, vib: 1 }];

export function renderBlues(ctx) {
  const { add, addSt, r, keyPc, on, bar, seconds, post } = ctx;
  const e8 = bar / 12; // one 12/8 eighth
  const nBars = Math.max(3, Math.floor(seconds / bar));
  // Plan: 1 intro bar (turnaround), as much of the form as fits, then the ending bar (V7 stop -> I9).
  const body = Math.max(1, Math.min(12, nBars - 2));
  const plan = [{ kind: 'intro', chords: [[7, '7#9']] }];
  for (let i = 0; i < body; i++) plan.push({ kind: 'form', formBar: i, chords: FORM[i] });
  plan.push({ kind: 'end', chords: [[7, '7#9'], [0, '9n5']] });
  const chordAt = (b, half) => { const c = plan[b].chords; return c[Math.min(c.length - 1, half)]; };
  const root = (off, lo) => lo + ((keyPc + off - lo) % 12 + 12) % 12;
  const T = (b, step) => b * bar + step * e8;

  // ---- drums: triplet ride, foot hat on 2 & 4, lazy backbeat with ghost, kick with the bass ----
  if (on('drums')) plan.forEach((p, b) => {
    const last = b === plan.length - 1;
    for (let s = 0; s < 12; s++) {
      if (last && s > 0) break; // ending: one hit, then the held chord rings
      const acc = s % 3 === 0 ? 0.7 : s % 3 === 1 ? 0.4 : 0.5;
      add('hats', T(b, s) + (r() - 0.5) * 0.006, I.ride(acc * (0.9 + r() * 0.2), r), 1, 0.25);
    }
    if (last) { add('kick', T(b, 0), I.kick('soft', 0.8, r), 1, 0); add('hats', T(b, 6), I.crash(0.7, r), 1.2, -0.2); add('snare', T(b, 0), I.snare('soft', 0.6, r), 1, 0); return; }
    for (const s of [3, 9]) { add('snare', T(b, s) + 0.008, I.snare('soft', 0.8, r), 1, 0); add('perc', T(b, s), I.footHat(0.35, r), 1, 0.2); }
    for (const s of [5, 11]) add('snare', T(b, s) + 0.008, I.snare('soft', 0.18, r), 1, 0);
    for (const [s, v] of [[0, 0.85], [6, 0.65], [8, 0.4]]) add('kick', T(b, s), I.kick('soft', v, r), 1, 0);
    const nextIsEnd = b === plan.length - 2;
    if (b === 0 || nextIsEnd) for (const [s, v] of [[9, 0.9], [10, 0.7], [11, 0.85]]) add('snare', T(b, s) + 0.006, I.snare('soft', v, r), 1, 0); // fill into bar 1 / the ending
    if (b === 1) add('hats', T(b, 0), I.crash(0.5, r), 1, -0.2);
  });

  // ---- bass: root on 1 and 3, a pickup into the next chord; walk-ups in bars 4 and 10 ----
  if (on('bass')) plan.forEach((p, b) => {
    const [off] = chordAt(b, 0), rt = root(off, 36);
    if (p.kind === 'end') { add('bass', T(b, 0), I.elecBass(midiHz(root(7, 36)), e8 * 5, 0.9), 1, 0); add('bass', T(b, 6), I.elecBass(midiHz(root(0, 36)), e8 * 10, 0.9), 1, 0); return; }
    const walk = p.formBar === 3 || p.formBar === 9;
    if (walk) [0, 4, 7, 9].forEach((iv, k) => add('bass', T(b, k * 3), I.elecBass(midiHz(rt + iv), e8 * 2.6, 0.85), 1, 0));
    else {
      const second = chordAt(b, 1)[0];
      add('bass', T(b, 0), I.elecBass(midiHz(rt), e8 * 5.5, 0.9), 1, 0);
      add('bass', T(b, 6), I.elecBass(midiHz(root(second, 36)), e8 * 2.8, 0.8), 1, 0);
      const nxt = plan[b + 1] ? root(plan[b + 1].chords[0][0], 36) : rt;
      add('bass', T(b, 9), I.elecBass(midiHz(nxt - 1), e8 * 2.6, 0.7), 1, 0); // chromatic lead-in
    }
  });

  // ---- horns (pads early, stabs on 2 & 4 later) and triplet piano comping ----
  if (on('chords')) plan.forEach((p, b) => {
    const halves = p.chords.length;
    p.chords.forEach(([off, q], h) => {
      const t0 = T(b, h * (12 / halves)), len = bar / halves;
      const rt = root(off, 53);
      const tones = QUALITY[q].filter((i) => i !== 0).map((i) => rt + (i % 12) + (i >= 12 ? 12 : 0)).slice(0, 3); // 3rd, b7, 9th
      if (p.kind === 'end' && h === 1) { tones.concat([rt + 12 + 2]).forEach((m, k) => add('horns', t0, I.horn(midiHz(m), e8 * 10, 0.6, r), 1, k * 0.25 - 0.3)); return; }
      if (p.kind === 'end') { tones.forEach((m, k) => add('horns', t0, I.horn(midiHz(m), e8 * 1.2, 0.8, r, { stab: true }), 1, k * 0.25 - 0.3)); return; }
      const late = (p.formBar ?? 0) >= 6;
      if (!late) tones.forEach((m, k) => add('horns', t0, I.horn(midiHz(m), len * 0.95, 0.35, r), 1, k * 0.25 - 0.25));
      else for (const s of [3, 9]) if (s >= h * (12 / halves) && s < (h + 1) * (12 / halves)) tones.forEach((m, k) => add('horns', T(b, s), I.horn(midiHz(m), e8 * 0.9, 0.6, r, { stab: true }), 1, k * 0.25 - 0.25));
    });
    if (p.kind !== 'end') for (const s of [3, 5, 9, 11]) {
      const [off, q] = chordAt(b, s >= 6 && halves > 1 ? 1 : 0), rt = root(off, 60);
      QUALITY[q].filter((i) => i !== 0).slice(0, 3).forEach((i) => add('chords', T(b, s) + r() * 0.008, I.piano(midiHz(rt + (i % 12)), e8 * 0.8, 0.28 + r() * 0.08), 1, 0.25));
    }
  });

  // ---- guitar: calls on bars 1, 3, 5, 7, 9, 11 (starting on the pickup), rests in between; the ending lick ----
  if (on('lead')) {
    const used = new Set();
    const pick = () => { let i; do i = Math.floor(r() * LICKS.length); while (used.has(i) && used.size < LICKS.length); used.add(i); if (used.size >= LICKS.length) used.clear(); return LICKS[i]; };
    const home = root(0, 64); // around the B.B. box
    plan.forEach((p, b) => {
      let lick = null, start = 0;
      if (p.kind === 'form' && p.formBar % 2 === 0) { lick = pick(); start = T(b, 0) - e8 * (1 + Math.floor(r() * 2)); }
      if (p.kind === 'end') { lick = ENDING; start = T(b, 0) - e8 * 3; }
      if (!lick) return;
      let t = start + 0.02;
      lick.forEach((n, k) => {
        const dur = n.l * e8, f0 = midiHz(home + semis(n.d));
        const vel = k === 0 ? 1 : k === lick.length - 1 ? 0.9 : 0.72;
        const flat = r() < 0.3 ? -0.1 : 0; // real bends often land a little flat
        const to = n.bend ? midiHz(home + semis(n.bend) + flat) : null, from = n.pre ? midiHz(home + semis(n.pre)) : null;
        const vibOn = n.vib || n.l >= 4 || !!n.bend;
        const depth = 25 + r() * 25, rate = 6 + r();
        const pitchFn = (tt) => {
          let f = f0;
          if (to) { const k2 = Math.min(1, tt / 0.12); f = to - (to - f0) * Math.pow(1 - k2, 2); }
          if (from) { const k2 = Math.min(1, tt / 0.15); f = from + (f0 - from) * (1 - Math.pow(1 - k2, 2)); }
          if (n.grace && tt < 0.03) f *= Math.pow(2, (-1 + tt / 0.03) / 12);
          if (n.cents) f *= Math.pow(2, (n.cents * Math.min(1, tt / 0.3)) / 1200);
          if (vibOn && tt > 0.2) f *= Math.pow(2, (depth * Math.min(1, (tt - 0.2) / 0.2) * (0.5 - 0.5 * Math.cos(2 * Math.PI * rate * (tt - 0.2)))) / 1200);
          return f;
        };
        if (t + dur > 0) add('lead', t, I.bluesGuitar(pitchFn, dur, vel * 0.8, r, n.l >= 4 ? 0.6 : 0.08), 1, 0.08);
        t += dur;
      });
    });
    // Lucille-ish tone: neck pickup voice, clean tube amp breaking up on the attacks, speaker roll-off.
    post.push((buses) => { const b = buses.lead; if (!b) return; for (const x of [b.L, b.R]) { new Biquad('hp', 90).process(x); new Biquad('peak', 200, 1, 3).process(x); new Biquad('peak', 1500, 1.2, 4).process(x); for (let i = 0; i < x.length; i++) x[i] = Math.tanh(x[i] * 2.2) / 1.6; new Biquad('lp', 4500).process(x); new Biquad('highshelf', 5000, 0.7, -6).process(x); } });
  }
}
