"""theory: notes, scales, chords, progressions and voicings, so I can think in music instead of numbers.

    from studio.instruments import theory as T
    T.note('C4')                         -> 60
    T.chord('Am7', octave=4)             -> [57, 60, 64, 67]
    T.progression('C G Am F', octave=4)  -> voiced with smooth voice leading
    T.scale('D', 'dorian', octave=4)     -> [62, 64, 65, 67, 69, 71, 72]
    T.roman('I V vi IV', key='E')        -> ['E', 'B', 'C#m', 'A']
"""
from __future__ import annotations

import itertools
import re

NAMES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
PC = {'C': 0, 'B#': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'Fb': 4, 'F': 5, 'E#': 5, 'F#': 6, 'Gb': 6,
      'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11, 'Cb': 11}

SCALES = {
    'major': [0, 2, 4, 5, 7, 9, 11], 'minor': [0, 2, 3, 5, 7, 8, 10], 'dorian': [0, 2, 3, 5, 7, 9, 10],
    'phrygian': [0, 1, 3, 5, 7, 8, 10], 'lydian': [0, 2, 4, 6, 7, 9, 11], 'mixolydian': [0, 2, 4, 5, 7, 9, 10],
    'locrian': [0, 1, 3, 5, 6, 8, 10], 'harmonic minor': [0, 2, 3, 5, 7, 8, 11], 'melodic minor': [0, 2, 3, 5, 7, 9, 11],
    'major pentatonic': [0, 2, 4, 7, 9], 'minor pentatonic': [0, 3, 5, 7, 10], 'blues': [0, 3, 5, 6, 7, 10],
    'whole tone': [0, 2, 4, 6, 8, 10], 'hirajoshi': [0, 2, 3, 7, 8], 'in': [0, 1, 5, 7, 8],
}

QUALITIES = {
    '': [0, 4, 7], 'm': [0, 3, 7], 'dim': [0, 3, 6], 'aug': [0, 4, 8], 'sus2': [0, 2, 7], 'sus4': [0, 5, 7], '5': [0, 7],
    '6': [0, 4, 7, 9], 'm6': [0, 3, 7, 9], '7': [0, 4, 7, 10], 'maj7': [0, 4, 7, 11], 'm7': [0, 3, 7, 10],
    'mMaj7': [0, 3, 7, 11], 'm7b5': [0, 3, 6, 10], 'dim7': [0, 3, 6, 9], 'add9': [0, 4, 7, 14], 'madd9': [0, 3, 7, 14],
    '9': [0, 4, 7, 10, 14], 'maj9': [0, 4, 7, 11, 14], 'm9': [0, 3, 7, 10, 14], '7sus4': [0, 5, 7, 10], '11': [0, 4, 7, 10, 14, 17],
    'm11': [0, 3, 7, 10, 14, 17], '13': [0, 4, 7, 10, 14, 21], 'maj7#11': [0, 4, 7, 11, 18],
}


def note(name: str | int) -> int:
    """'C4' -> 60, 'F#2' -> 42, 'Bb' -> 70 (octave 4 by default). Ints pass through."""
    if isinstance(name, int):
        return name
    m = re.fullmatch(r'([A-G][#b]?)(-?\d)?', name.strip())
    if not m:
        raise ValueError(f'not a note: {name}')
    return PC[m.group(1)] + 12 * (int(m.group(2) or 4) + 1)


def name(midi: int) -> str:
    return f'{NAMES[midi % 12]}{midi // 12 - 1}'


def scale(root: str, mode: str = 'major', octave: int = 4, octaves: int = 1) -> list[int]:
    r = PC[root] + 12 * (octave + 1)
    steps = SCALES[mode]
    return [r + 12 * o + s for o in range(octaves) for s in steps] + [r + 12 * octaves]


def parse_chord(sym: str) -> tuple[int, list[int], int | None]:
    """'F#m7/C#' -> (root pc, intervals, bass pc or None)"""
    m = re.fullmatch(r'([A-G][#b]?)([^/]*)(?:/([A-G][#b]?))?', sym.strip())
    if not m:
        raise ValueError(f'not a chord: {sym}')
    q = m.group(2)
    if q not in QUALITIES:
        raise ValueError(f'unknown chord quality "{q}" in {sym}; known: {sorted(QUALITIES)}')
    return PC[m.group(1)], QUALITIES[q], (PC[m.group(3)] if m.group(3) else None)


def chord(sym: str, octave: int = 4, inversion: int = 0) -> list[int]:
    root, ivs, bass = parse_chord(sym)
    notes = [root + 12 * (octave + 1) + i for i in ivs]
    for _ in range(inversion):
        notes = notes[1:] + [notes[0] + 12]
    if bass is not None:
        b = bass + 12 * octave
        while b >= notes[0]:
            b -= 12
        notes = [b] + notes
    return notes


def bass_of(sym: str, octave: int = 2) -> int:
    root, _, bass = parse_chord(sym)
    return (bass if bass is not None else root) + 12 * (octave + 1)


def voice_lead(prev: list[int], sym: str, low: int = 52, high: int = 79) -> list[int]:
    """Voice `sym` with the same number of notes as `prev` (or its own size), choosing the inversion and
    octave placement that moves the voices least."""
    root, ivs, _ = parse_chord(sym)
    pcs = [(root + i) % 12 for i in ivs]
    k = len(prev) if prev else len(pcs)
    pool = []
    for pc in pcs:
        pool += [m for m in range(low, high + 1) if m % 12 == pc]
    best, best_cost = None, 1e9
    for combo in itertools.combinations(sorted(pool), k):
        if not set(pcs[:3]) <= {c % 12 for c in combo} and len(pcs) >= 3 and k >= 3:
            continue
        if combo[-1] - combo[0] > 19:
            continue
        cost = sum(abs(a - b) for a, b in zip(sorted(prev), combo)) if prev else abs(sum(combo) / k - (low + high) / 2)
        cost += 0.5 * sum(1 for a, b in zip(combo, combo[1:]) if b - a < 2)   # avoid seconds clusters
        if cost < best_cost:
            best, best_cost = list(combo), cost
    return best or chord(sym)


def progression(syms: str | list[str], octave: int = 4, voices: int = 4, smooth: bool = True) -> list[list[int]]:
    syms = syms.split() if isinstance(syms, str) else syms
    out, prev = [], None
    lo, hi = 12 * (octave + 1) - 8, 12 * (octave + 1) + 19
    for s in syms:
        if smooth:
            v = voice_lead(prev or [], s, lo, hi) if prev else voice_lead([], s, lo, hi)
            if len(v) < voices and len(parse_chord(s)[1]) >= 3:
                v = sorted(v + [v[0] + 12])[:voices]
        else:
            v = chord(s, octave)
        out.append(v); prev = v
    return out


ROMAN = {'I': 0, 'II': 2, 'III': 4, 'IV': 5, 'V': 7, 'VI': 9, 'VII': 11}


def roman(numerals: str, key: str = 'C', minor: bool = False) -> list[str]:
    """'I V vi IV' in E -> ['E', 'B', 'C#m', 'A']. Uppercase = major, lowercase = minor, 'o' = dim, 7 appends."""
    base = SCALES['minor' if minor else 'major']
    out = []
    for tok in numerals.split():
        m = re.fullmatch(r'([b#]?)([ivIV]+)(o|\+)?(7|maj7)?', tok)
        if not m:
            raise ValueError(tok)
        acc, rn, mod, sev = m.groups()
        deg = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII'].index(rn.upper())
        pc = (PC[key] + base[deg] + (-1 if acc == 'b' else 1 if acc == '#' else 0)) % 12
        q = '' if rn.isupper() else 'm'
        if mod == 'o': q = 'dim'
        if mod == '+': q = 'aug'
        if sev == '7': q = {'': '7', 'm': 'm7', 'dim': 'm7b5'}.get(q, q + '7')
        if sev == 'maj7': q = 'maj7'
        out.append(NAMES[pc] + q)
    return out


def in_scale(m: int, root: str, mode: str) -> bool:
    return (m - PC[root]) % 12 in SCALES[mode]


def snap(m: float, root: str, mode: str) -> int:
    """Nearest note in the scale."""
    m = int(round(m))
    for d in (0, 1, -1, 2, -2):
        if in_scale(m + d, root, mode):
            return m + d
    return m


def euclid(hits: int, steps: int, rotate: int = 0) -> list[int]:
    """Euclidean rhythm: spread `hits` as evenly as possible over `steps` (1 = hit). E(3,8) is the tresillo."""
    pat = [1 if (i * hits) % steps < hits else 0 for i in range(steps)]
    return pat[-rotate:] + pat[:-rotate] if rotate else pat
