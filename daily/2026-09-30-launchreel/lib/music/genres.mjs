// Genre recipes, from research into production practice and chart hits (see README for sources).
// Grids: one bar per string, one character per step (16 = sixteenths, 12 = 12/8 triplets).
// '.' rest, 1-9 velocity, x = 8, r = a 1/32 roll (two hits in the step).
// Progressions: [semitones from the key, chord quality], one chord per `barsPerChord` bars.

export const GENRES = {
  lofi: {
    label: 'Lo-fi', blurb: 'Dusty Rhodes, lazy swing', bpm: 82, swing: 0.58, steps: 16, mode: 'major', scale: 'majPent', key: 'Eb',
    progs: [[[2, 'm9'], [7, '13'], [0, 'maj9'], [0, 'maj9']], [[5, 'maj7'], [4, '7'], [9, 'm7'], [7, 'm7']], [[5, 'maj7'], [7, '7'], [4, 'm7'], [9, 'm7']], [[0, 'maj7'], [9, 'm9'], [2, 'm9'], [7, '7']]],
    barsPerChord: 1, kick: 'lofi', snare: 'lofi', snareDrag: 0.02, hatJitter: 0.012, hatBright: 0.7,
    drums: {
      main: { K: '9......6..7.....', S: '....9.......9...', GS: '.......2.2.....2', CH: '5.3.6.3.5.3.6.3.', OH: '..............4.', RIM: '..........3.....' },
      vari: { K: '9......6..7...5.', S: '....9.......9.3.', GS: '.......2.2......', CH: '5.3.6.3.5.3.6.3.', OH: '..............4.' },
    },
    bass: { inst: 'upright', grid: '7......5..6.....', legato: 0.95 },
    chords: { inst: 'epiano', grid: 'x.....x.........', voicing: 'rootless', lo: 50, hi: 72, strum: 0.02, push: true },
    lead: { inst: 'piano', motifs: ['5:2 6:2 1\':4 .:8 6:3 5:5 .:8', '3:1 5:1 7:2 9:4 .:4 7:4', '5:2 3:2 2:4 .:8 1:4 .:12'], base: 72, every: 2, vel: 0.5 },
    intro: { drums: [] }, fx: { lofi: true, reverb: { room: 0.6, damp: 0.6, wet: 0.15 }, duck: { depth: 0.25, release: 0.4, curve: 1.5 } },
    mix: { kick: 0, snare: -4, hats: -14, perc: -16, bass: -3, chords: -5, pad: -14, lead: -10 },
  },
  synthwave: {
    label: 'Synthwave', blurb: 'Neon pads, gated snare, drive', bpm: 100, swing: 0.5, steps: 16, mode: 'minor', scale: 'minor', key: 'A',
    progs: [[[0, 'min'], [8, 'maj'], [3, 'maj'], [10, 'maj']], [[0, 'min'], [7, 'min'], [10, 'maj'], [5, 'maj']], [[8, 'maj'], [10, 'maj'], [0, 'min'], [0, 'min']], [[0, 'min'], [5, 'min'], [8, 'maj'], [7, 'maj']]],
    barsPerChord: 1, kick: 'pop', snare: 'gated', hatJitter: 0.002, hatBright: 1,
    drums: {
      main: { K: '9...9...9...9...', S: '....9.......9...', CH: '6.6.6.6.6.6.6.6.', OH: '..5...5...5...5.' },
      vari: { K: '9...9...9...9...', S: '....9.......9...', CH: '6.6.6.6.6.6.6.6.', OH: '..5...5...5...5.' },
      fill: { K: '9...9...9.......', S: '....9...5.6.7.89', TOM: '............9876', CH: '6.6.6.6.6.6.....' },
    },
    bass: { inst: 'pluckBass', grid: 'x.x.x.x.x.x.x.x.', octaves: [0, 12], legato: 0.8 },
    chords: { inst: 'junoPad', grid: 'x...............', voicing: 'spread', lo: 48, hi: 79, hold: true },
    arp: { inst: 'pluck', grid: 'xxxxxxxxxxxxxxxx', pattern: [0, 1, 2, 3], octave: 12, vel: 0.45, delay: 0.75 },
    lead: { inst: 'brass', motifs: ['1:4 b3:4 5:8 4:4 b3:4 2:8', '5:6 b6:2 5:4 b3:4 1:16', 'b7:4 1\':12 .:16'], base: 72, every: 2, vel: 0.55, from: 2 },
    intro: { drums: [] }, fx: { chorus: true, reverb: { room: 0.9, damp: 0.3, wet: 0.28 }, duck: { depth: 0.4, release: 0.5, curve: 2 }, crash: true },
    mix: { kick: 0, snare: -2, hats: -12, perc: -12, bass: -4, chords: -10, arp: -9, lead: -7 },
  },
  house: {
    label: 'House', blurb: 'Four on the floor, offbeat stabs', bpm: 124, swing: 0.54, swingParts: ['CH', 'OH', 'SH', 'RIM', 'CONGA'], steps: 16, mode: 'minor', scale: 'minPent', key: 'A',
    progs: [[[0, 'm9'], [5, 'm9']], [[0, 'm9'], [10, 'maj7']], [[8, 'maj7'], [10, 'maj'], [0, 'm9'], [0, 'm9']], [[2, 'm9'], [7, '13']]],
    barsPerChord: 2, kick: '909', snare: 'clap', hatJitter: 0.003,
    drums: {
      main: { K: '9...9...9...9...', CL: '....8.......8...', OH: '..7...7...7...7.', SH: '4343434343434343', RIM: '...5..5....5..5.', CONGA: '......6.....5.5.' },
      vari: { K: '9...9...9...9.9.', CL: '....8.......8...', OH: '..7...7...7...7.', SH: '4343434343434343', CONGA: '......6.....5.5.' },
      fill: { K: '9...9...9.......', CL: '....8...8.8.8888', OH: '..7...7...7.....', SH: '43434343' + '........' },
    },
    bass: { inst: 'pluckBass', grid: '..x...x...x...x.', octaves: [0, 0, 12, 0], legato: 0.6 },
    chords: { inst: 'stab', grid: '..x...x...x...x.', voicing: 'parallel', lo: 57, hi: 72 },
    lead: { inst: 'bell', motifs: ['b7:1 .:1 1\':2 .:1 b3\':1 .:1 1\':3 .:6', '5:2 .:1 5:1 b7:1 1\':4 .:7'], base: 72, every: 2, vel: 0.35, from: 4 },
    intro: { drums: ['K', 'OH', 'SH'] }, fx: { reverb: { room: 0.5, damp: 0.5, wet: 0.12 }, duck: { depth: 0.6, release: 0.6, curve: 2 }, crash: true },
    mix: { kick: 0, snare: -5, hats: -10, perc: -13, bass: -3, chords: -8, lead: -12 },
  },
  trap: {
    label: 'Trap', blurb: 'Hard 808s, switching hats, dark loop', bpm: 140, steps: 16, key: 'Db', render: 'trap', lufs: -10,
    mix: { bass: 0, snare: -3, kick: -6, hats: -11, perc: -15, lead: -8 },
    sends: { snare: 0.12, lead: 0.6, perc: 0.2 }, fx: { reverb: { room: 0.85, damp: 0.5, wet: 0.22, predelay: 0.03 } },
  },
  ambient: {
    label: 'Ambient', blurb: 'Slow swells, big space, no drums', bpm: 72, swing: 0.5, steps: 16, mode: 'major', scale: 'majPent', key: 'D',
    progs: [[[0, 'maj9'], [5, 'maj7']], [[0, 'add9'], [10, 'add9'], [5, 'add9']], [[9, 'madd9'], [5, 'maj7'], [0, 'sus2']], [[0, 'add9'], [2, 'maj']]],
    barsPerChord: 2, drums: null,
    bass: { inst: 'sub', grid: 'x...............', legato: 1, attack: 0.3 },
    chords: { inst: 'supersawPad', grid: 'x...............', voicing: 'spread', lo: 40, hi: 86, hold: true, vel: 0.55 },
    lead: { inst: 'bell', motifs: ['5:8 .:8 9:12 .:4', '3:6 2:2 1:16 .:8', '6:4 5:12 .:16'], base: 76, every: 2, vel: 0.3, sparse: 0.4 },
    intro: { drums: [] }, fx: { reverb: { room: 0.95, damp: 0.2, wet: 0.5, predelay: 0.04 }, pingpong: 0.75, chorus: true },
    mix: { kick: -8, bass: -10, chords: -3, lead: -8 },
  },
  pop: {
    label: 'Upbeat pop', blurb: 'Bright plucks, claps, a hook', bpm: 112, swing: 0.5, steps: 16, mode: 'major', scale: 'major', key: 'C',
    progs: [[[0, 'maj'], [7, 'maj'], [9, 'min'], [5, 'maj']], [[9, 'min'], [5, 'maj'], [0, 'maj'], [7, 'maj']], [[0, 'add9'], [9, 'min'], [5, 'maj'], [7, 'sus4']], [[5, 'maj'], [0, 'maj'], [7, 'maj'], [9, 'min']]],
    barsPerChord: 1, kick: 'pop', snare: 'clap', hatJitter: 0.003,
    drums: {
      main: { K: '9...9...9...9...', CL: '....9.......9...', SN: '....7.......7...', OH: '..6...6...6...6.', SH: '5454545454545454' },
      vari: { K: '9...9...9...9..6', CL: '....9.......9...', SN: '....7.......7...', OH: '..6...6...6...6.', SH: '5454545454545454' },
      build: { K: '9...9...9...9...', CL: '8.8.8.8.88888888', SH: '5454545454545454' },
    },
    bass: { inst: 'pluckBass', grid: 'x.x.x.x.x.x.x.xx', octaves: [0, 0, 0, 0, 0, 0, 0, 12], legato: 0.7 },
    chords: { inst: 'pluckChord', grid: '..x...x...x...x.', voicing: 'close', lo: 60, hi: 79 },
    pad: { inst: 'supersawPad', vel: 0.25 },
    lead: { inst: 'pluckLead', motifs: ['3:2 3:1 2:1 1:2 2:2 3:4 5:4', '5:1 5:1 6:2 5:2 3:2 2:3 1:5', '1\':2 7:2 5:4 6:2 5:2 3:4'], base: 72, every: 2, vel: 0.6, from: 2 },
    intro: { drums: [] }, build: true, fx: { reverb: { room: 0.7, damp: 0.4, wet: 0.15 }, duck: { depth: 0.35, release: 0.5, curve: 2 }, crash: true, pingpong: 0.75 },
    mix: { kick: 0, snare: -3, hats: -12, perc: -15, bass: -4, chords: -7, pad: -14, lead: -5 },
  },
  future: {
    label: 'Future bass', blurb: 'Wobbling supersaw chords, big drop', bpm: 150, swing: 0.5, steps: 16, mode: 'major', scale: 'majPent', key: 'F',
    progs: [[[5, 'maj7'], [7, 'add9'], [4, 'm7'], [9, 'm9']], [[9, 'm9'], [5, 'maj9'], [0, 'add9'], [7, 'sus4']], [[5, 'maj7'], [4, 'm7'], [9, 'm7'], [7, 'maj']]],
    barsPerChord: 1, kick: 'pop', snare: 'clap', hatJitter: 0.002,
    drums: {
      main: { K: '9.......9.7.....', CL: '........9.......', CH: '..5...5...5...5.', SH: '3.3.3.3.3.3.3.3.' },
      vari: { K: '9.......9.7...6.', CL: '........9.......', CH: '..5...5...5...5.', SH: '3.3.3.3.3.3.3.3.' },
      build: { S: '3.4.5.6.7777888r', CH: '5.5.5.5.5.5.5.5.' },
    },
    bass: { inst: 'sub', grid: 'x.......x.......', legato: 1 },
    chords: { inst: 'futureSaw', grid: '9..7..8...7..6..', voicing: 'close', lo: 53, hi: 81, vel: 0.8 },
    lead: { inst: 'pluckLead', motifs: ['5:1 6:1 1\':2 .:1 6:1 5:3 3:4 .:3', '1\':1 5:1 3:1 5:1 1\':2 2\':6 .:4'], base: 76, every: 2, vel: 0.45, from: 2 },
    intro: { drums: [] }, build: true, fx: { reverb: { room: 0.85, damp: 0.35, wet: 0.25 }, duck: { depth: 0.9, release: 0.8, curve: 3 }, crash: true },
    mix: { kick: 0, snare: -3, hats: -12, perc: -15, bass: -3, chords: -4, lead: -8 },
  },
  afro: {
    label: 'Afrobeats', blurb: '3-3-2 bounce, highlife guitar', bpm: 104, swing: 0.56, swingParts: ['SH', 'CONGA', 'CH'], steps: 16, mode: 'major', scale: 'majPent', key: 'A',
    progs: [[[0, 'maj7'], [5, 'maj7'], [7, 'maj'], [5, 'maj7']], [[2, 'm7'], [7, '7'], [0, 'maj7'], [0, 'maj7']], [[9, 'm7'], [5, 'maj7'], [0, 'maj7'], [7, '7']], [[5, 'maj7'], [4, 'm7']]],
    barsPerChord: 1, kick: 'soft', snare: 'soft', hatJitter: 0.008,
    drums: {
      main: { K: '9.....7...9.....', RIM: '...7..7.....7...', CL: '....6.......6...', SH: '5363536353635363', CH: '..6...6...6...6.', CONGA: '..6..7....6.5.7.' },
      vari: { K: '9.....7...9..6..', RIM: '...7..7.....7...', SH: '5363536353635363', CONGA: '..6..7....6.5.7.' },
    },
    bass: { inst: 'sub', grid: '8..7..6...8.6...', melodic: [0, 7, 12, 0, 10], legato: 0.5 },
    chords: { inst: 'epiano', grid: 'x.......x.......', voicing: 'close', lo: 55, hi: 74, vel: 0.35 },
    guitar: { grid: '.x.x..x..x.x..x.' },
    lead: { inst: 'marimba', motifs: ['3:1 5:2 3:1 2:2 1:2 6-:4 1:4', '5:2 5:1 6:1 5:2 3:2 2:4 .:4', '1\':1 6:1 5:2 .:2 3:2 5:4 .:4'], base: 72, every: 2, vel: 0.5, from: 2 },
    intro: { drums: ['SH', 'CONGA', 'RIM'] }, fx: { reverb: { room: 0.55, damp: 0.5, wet: 0.12 } },
    mix: { kick: 0, snare: -5, hats: -10, perc: -8, bass: -3, chords: -9, guitar: -8, lead: -7 },
  },
  blues: {
    label: 'Slow blues', blurb: 'B.B.-style guitar, horns, 12/8', bpm: 54, steps: 12, key: 'Bb', render: 'blues', lufs: -15,
    mix: { lead: -4, horns: -11, chords: -11, bass: -5, kick: -7, snare: -8, hats: -13, perc: -16 },
    sends: { lead: 0.45, horns: 0.45, chords: 0.35, snare: 0.35, hats: 0.15 }, fx: { reverb: { room: 0.62, damp: 0.45, wet: 0.18, predelay: 0.02 } },
  },
};
export const ALIAS = { chill: 'lofi', bright: 'pop', futurebass: 'future', afrobeats: 'afro' };
