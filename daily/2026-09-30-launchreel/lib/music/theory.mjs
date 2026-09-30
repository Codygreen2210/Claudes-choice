// Harmony and melody. Chord progressions are the real ones hit songs use (progressions are
// shared building blocks, not anyone's property); melodies are generated from motif rhythms
// and chord-tone rules, never copied.

export const QUALITY = {
  maj: [0, 4, 7], min: [0, 3, 7], maj7: [0, 4, 7, 11], m7: [0, 3, 7, 10], 7: [0, 4, 7, 10],
  add9: [0, 4, 7, 14], madd9: [0, 3, 7, 14], maj9: [0, 4, 7, 11, 14], m9: [0, 3, 7, 10, 14], m11: [0, 3, 7, 10, 14, 17],
  9: [0, 4, 7, 10, 14], 13: [0, 4, 10, 14, 21], '7#9': [0, 4, 10, 15], sus2: [0, 2, 7], sus4: [0, 5, 7],
  6: [0, 4, 7, 9], m6: [0, 3, 7, 9], 5: [0, 7], m9r: [3, 7, 10, 14], maj9r: [4, 7, 11, 14], '9r': [4, 10, 14, 21],
};
export const SCALES = {
  major: [0, 2, 4, 5, 7, 9, 11], minor: [0, 2, 3, 5, 7, 8, 10], dorian: [0, 2, 3, 5, 7, 9, 10],
  harmonic: [0, 2, 3, 5, 7, 8, 11], mixolydian: [0, 2, 4, 5, 7, 9, 10], blues: [0, 3, 5, 6, 7, 10], majPent: [0, 2, 4, 7, 9], minPent: [0, 3, 5, 7, 10],
};
export const KEYS = { C: 0, Db: 1, D: 2, Eb: 3, E: 4, F: 5, Gb: 6, G: 7, Ab: 8, A: 9, Bb: 10, B: 11 };

// Chord tones as pitch classes (0-11) for [rootOffset, quality] in a key.
export const chordPcs = (key, [off, q]) => QUALITY[q].map((i) => (key + off + i) % 12);

// Voice leading: of all inversions/octaves in [lo, hi], pick the one closest to the previous voicing.
export function voiceLead(key, chord, prev, { lo = 52, hi = 76, maxNotes = 5 } = {}) {
  const [off, q] = chord; const ints = QUALITY[q].slice(0, maxNotes);
  const root = key + off;
  const cands = [];
  for (let inv = 0; inv < ints.length; inv++) {
    const rot = ints.slice(inv).concat(ints.slice(0, inv).map((x) => x + 12));
    for (let base = lo - 24; base <= hi; base++) {
      if ((base - root - rot[0]) % 12 !== 0) continue;
      const notes = rot.map((x) => base + (x - rot[0]));
      if (notes[0] < lo || notes.at(-1) > hi + 4) continue;
      cands.push(notes);
    }
  }
  if (!cands.length) return ints.map((x) => lo + ((root + x - lo) % 12 + 12) % 12);
  if (!prev) { const mid = (lo + hi) / 2; return cands.sort((a, b) => Math.abs(avg(a) - mid) - Math.abs(avg(b) - mid))[0]; }
  const cost = (c) => { let s = 0; for (const n of c) s += Math.min(...prev.map((p) => Math.abs(p - n))); for (const p of prev) s += Math.min(...c.map((n) => Math.abs(p - n))); return s + Math.abs(c.at(-1) - prev.at(-1)) * 0.5; };
  return cands.sort((a, b) => cost(a) - cost(b))[0];
}
const avg = (a) => a.reduce((x, y) => x + y, 0) / a.length;
// Spread voicing for pads/ambient: root low, fifth, then the colour tones an octave up.
export function spreadVoicing(key, [off, q], base = 48) {
  const root = base + ((key + off - base) % 12 + 12) % 12, ints = QUALITY[q];
  return [root, root + 7, ...ints.filter((i) => i !== 0 && i !== 7).map((i) => root + 12 + (i % 12) + (i >= 12 ? 12 : 0))];
}

// "5:2 b3:1 1':4 .:2" -> [{deg:'5', semis:7, len:2}, ...]; degrees are major-scale numbers with b/# and ' (octave up) / - (down).
const MAJ = [0, 2, 4, 5, 7, 9, 11];
export function parseMotif(str) {
  const out = [];
  for (const tok of str.split(/\s+/)) {
    if (!tok || tok === '|') continue;
    const m = /^(\.|[#b]?\d+['-]*)[^:]*:(\d+)$/.exec(tok);
    if (!m) continue;
    const len = +m[2];
    if (m[1] === '.') { out.push({ rest: true, len }); continue; }
    const d = /^([#b]?)(\d+)(['-]*)$/.exec(m[1]);
    const n = +d[2] - 1;
    let semis = MAJ[n % 7] + 12 * Math.floor(n / 7) + (d[1] === 'b' ? -1 : d[1] === '#' ? 1 : 0);
    for (const c of d[3]) semis += c === "'" ? 12 : -12;
    out.push({ semis, len });
  }
  return out;
}
const snapTo = (pitch, pcs) => { let best = pitch, bd = 99; for (let d = -3; d <= 3; d++) if (pcs.includes(((pitch + d) % 12 + 12) % 12) && Math.abs(d) < bd) { bd = Math.abs(d); best = pitch + d; } return best; };

// A 4-bar phrase A A' B A from a motif: same rhythm repeating, the answer varied, strong beats on chord tones.
// Returns notes [{step, len, midi, vel}] with steps counted across the phrase (stepsPerBar each bar).
export function phrase({ motif, key, chordAt, scale, stepsPerBar = 16, base = 72, r }) {
  const m = parseMotif(motif);
  const motifLen = m.reduce((s, x) => s + x.len, 0) || stepsPerBar;
  const unit = Math.ceil(motifLen / stepsPerBar) * stepsPerBar; // 1 or 2 bars
  const scalePcs = SCALES[scale].map((x) => (x + key) % 12);
  const notes = [];
  const sections = unit >= stepsPerBar * 2 ? ['A', 'B'] : ['A', "A'", 'B', 'A'];
  sections.forEach((sec, si) => {
    let step = si * unit;
    const lift = sec === 'B' ? (r() < 0.5 ? 2 : 4) : 0; // B section a step or third higher in the scale
    m.forEach((n, ni) => {
      if (!n.rest) {
        let p = base + ((key % 12)) + n.semis + lift;
        if (sec === "A'" && ni === m.length - 1) p += r() < 0.5 ? -3 : 2; // the answer ends somewhere new
        const pcs = chordAt(step);
        const strong = step % (stepsPerBar / 4) === 0; // on a beat
        p = strong ? snapTo(p, pcs) : snapTo(p, scalePcs);
        notes.push({ step, len: n.len, midi: p, vel: strong ? 0.9 : 0.72 + r() * 0.1 });
      }
      step += n.len;
    });
  });
  return { notes, length: unit * sections.length };
}
