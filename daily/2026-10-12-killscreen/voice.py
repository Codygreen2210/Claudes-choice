#!/usr/bin/env python3
"""Kill Screen: the voice pass.

Takes the raw narration take and fixes what the studio's ears flagged on it:

    low-mid 68% of the energy  ("crowded low-mids, can sound muddy or boxy")
    high-mid 7%, air 1%        (consonants and presence missing)
    crest 20.7 dB              (far too dynamic to survive a phone speaker)
    -24.6 LUFS integrated      (way too quiet for a narrator stem)

It also finds where the speaker breathes, and writes those times out, so the
picture can cut on the voice instead of on a guess.

    python3 voice.py        ->  narration.wav, lines.json
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'studio', 'instruments'))

import synth as S          # noqa: E402

sys.path.insert(0, '/home/claude/shims')
import pyloudnorm as pyln  # noqa: E402

SR = S.SR
RAW = os.path.join(HERE, 'narration-raw.wav')

# The read, line by line, in order. Used to label the detected segments.
LINES = [
    "You've played these. You have no idea what's in them.",
    "Pac-Man has a level nobody can beat. At two fifty-six, a counter overflows and the maze turns to garbage.",
    "The ghosts aren't random. Blinky chases. Pinky cuts you off. Inky's erratic. Clyde just wanders.",
    "Space Invaders speeds up by accident. Fewer aliens, less work for the hardware.",
    "Mario only exists because Nintendo lost the Popeye license.",
    "Nintendo was founded in eighteen eighty-nine, selling playing cards.",
    "Tetris came out of Soviet Moscow. Its author earned nothing from it for a decade.",
    "The Konami code was a developer's testing shortcut he forgot to remove.",
    "Atari really did bury E.T. in the desert. In twenty fourteen, they dug it up.",
    "Which one got you?",
]


# --------------------------------------------------------------------------- voice chain
def deess(x, lo=5500, hi=9500, thr_db=-30.0, amount=0.7):
    """Pull down only the sibilant band, and only while it is loud.

    A static shelf would dull every word; this leaves the consonants alone
    until an 's' actually spikes.
    """
    band = S.bp(x, lo, hi, 2)
    env = np.abs(band)
    # 15 ms smoothing, one pole
    a = np.exp(-1.0 / (0.015 * SR))
    env = np.maximum.reduce([env])
    from scipy import signal as sg
    env = sg.lfilter([1 - a], [1, -a], env, axis=-1)
    env_db = 20 * np.log10(env + 1e-9)
    over = np.maximum(0.0, env_db - thr_db)
    red = 1.0 - amount * (1.0 - 10 ** (-over / 20.0))
    return x - band * (1.0 - red)


def vox_comp(x, thr_db=-24.0, ratio=4.0, atk=0.005, rel=0.090):
    """A fast compressor for speech.

    synth.glue is deliberately gentle bus compression (20 ms detector, slow
    release), and on this read it only took the crest from 20.7 to 19.4 dB.
    A narrator on a phone speaker wants 12-14 dB, so this stage does the work
    and glue just evens out the result.
    """
    from scipy import signal as sg
    env = np.abs(x if x.ndim == 1 else x.mean(axis=0))
    ka = np.exp(-1.0 / (atk * SR))
    env = sg.lfilter([1 - ka], [1, -ka], env)
    lvl = 20 * np.log10(env + 1e-9)
    gr = -np.maximum(0.0, lvl - thr_db) * (1 - 1 / ratio)
    kr = np.exp(-1.0 / (rel * SR))
    g = sg.lfilter([1 - kr], [1, -kr], gr)
    return x * 10 ** (np.minimum(g, 0) / 20)


def level(x, target_db=-20.0, limit_db=10.0):
    """Even out phrase-to-phrase level, the way a dialogue editor would.

    Measured on this read: the loud and quiet passages sit 20.7 dB apart, and
    only 15% of the file is silence, so that spread is real speech and not an
    artefact of the pauses. A peak compressor can't fix it — it only pulls the
    loud phrases down and leaves the quiet ones where they were. So each phrase
    gets its own gain, interpolated smoothly so nothing pumps.
    """
    segs = segments(x)
    if not segs:
        return x
    gains, centres = [], []
    for a, b in segs:
        seg = x[S.smp(a):S.smp(b)]
        if seg.size == 0:
            continue
        rms_db = 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9)
        g = np.clip(target_db - rms_db, -limit_db, limit_db)
        gains.append(g)
        centres.append(S.smp((a + b) / 2))
    if not gains:
        return x
    idx = np.arange(x.shape[-1])
    env_db = np.interp(idx, centres, gains)
    return x * 10 ** (env_db / 20.0)


def voice_chain(x):
    x = S.hp(x, 85, 2)                       # rumble and plosive thumps

    x = S.eq(x, [
        ('peak', 330, -3.5, 0.9),            # the boxiness the ears found
        ('peak', 850, -2.0, 1.2),            # honk
        ('peak', 4000, 3.5, 0.8),            # presence: consonants were at 7%
        ('highshelf', 9500, 3.0, 0.7),       # air was at 1%
    ])

    x = deess(x)
    x = level(x)                                  # the 20.7 dB phrase spread
    x = vox_comp(x, thr_db=-18.0, ratio=3.0)      # catch what's left on top
    x = S.glue(x, thr=-20, ratio=2.0, rel=0.12)
    x = S.saturate(x, drive=1.15)                 # a little weight

    # -16 LUFS for the stem: loud enough to lead, with room for the limiter.
    st = S.stereo(x)
    meter = pyln.Meter(SR)
    cur = meter.integrated_loudness(st.T)
    st = st * 10 ** ((-16.0 - cur) / 20.0)
    # 0.84 ≈ -1.5 dBTP. At ceiling 0.89 it measured exactly -1.0 dBTP, which is
    # the house limit rather than inside it.
    return S.limiter(st, ceiling=0.84)


# --------------------------------------------------------------------------- where the voice breathes
def segments(x, hop=0.010, win=0.025, floor_db=-42.0, min_sil=0.20, min_speech=0.12):
    """Speech segments, by framed RMS against a floor relative to the loudest frame."""
    h, w = S.smp(hop), S.smp(win)
    n = (x.shape[-1] - w) // h
    rms = np.array([np.sqrt(np.mean(x[..., i * h:i * h + w] ** 2)) for i in range(max(0, n))])
    db = 20 * np.log10(rms + 1e-9)
    thr = db.max() + floor_db
    voiced = db > thr

    segs, i = [], 0
    while i < len(voiced):
        if voiced[i]:
            j = i
            while j < len(voiced) and voiced[j]:
                j += 1
            segs.append([i * hop, j * hop])
            i = j
        else:
            i += 1
    # close gaps shorter than min_sil, then drop crumbs
    merged = []
    for s in segs:
        if merged and s[0] - merged[-1][1] < min_sil:
            merged[-1][1] = s[1]
        else:
            merged.append(s)
    return [s for s in merged if s[1] - s[0] >= min_speech]


def lines_from(segs, count):
    """Group segments into `count` lines by splitting at the longest silences.

    Paragraph breaks in the read are longer than sentence breaks, so the
    count-1 widest gaps are the line boundaries.
    """
    gaps = sorted(
        ((segs[i + 1][0] - segs[i][1], i) for i in range(len(segs) - 1)),
        reverse=True,
    )
    cuts = sorted(i for _, i in gaps[:count - 1])
    out, start = [], 0
    for c in cuts + [len(segs) - 1]:
        out.append([segs[start][0], segs[c][1]])
        start = c + 1
    return out


if __name__ == '__main__':
    import soundfile as sf

    raw, sr = sf.read(RAW, always_2d=True)
    assert sr == SR, f'expected {SR}, got {sr}'
    mono = raw.mean(axis=1)

    y = voice_chain(mono)
    S.write(os.path.join(HERE, 'narration.wav'), y)

    segs = segments(y.mean(axis=0))
    groups = lines_from(segs, len(LINES))

    cards = []
    for i, (a, b) in enumerate(groups):
        cards.append({
            'index': i,
            'start': round(a, 3),
            'end': round(b, 3),
            'text': LINES[i],
            'words': len(LINES[i].split()),
        })

    with open(os.path.join(HERE, 'lines.json'), 'w') as f:
        json.dump({'duration': y.shape[-1] / SR, 'lines': cards}, f, indent=2)

    print(f'narration.wav  {y.shape[-1] / SR:.2f}s')
    print(f'{len(segs)} speech segments -> {len(groups)} lines')
    print(f'{"#":>2}  {"start":>6} {"end":>6} {"len":>5} {"w":>3}  words/s  text')
    for c in cards:
        d = c['end'] - c['start']
        print(f'{c["index"]:>2}  {c["start"]:>6.2f} {c["end"]:>6.2f} {d:>5.2f} {c["words"]:>3}  '
              f'{c["words"] / d:>7.2f}  {c["text"][:46]}')
