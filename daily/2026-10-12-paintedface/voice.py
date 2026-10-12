#!/usr/bin/env python3
"""Painted Face: the voice pass.

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
    'For most of history, looking good could kill you.',
    'Venetian ceruse: white lead, spread across the face. Britain called it a poison in sixteen thirty-one. People wore it for two more centuries.',
    "Roman women dripped belladonna into their eyes to widen the pupils. That's atropine. Optometrists still use it today, in a controlled dose.",
    'Victorians ate arsenic. Complexion wafers, swallowed for clear skin, sold as safe into the nineteen hundreds.',
    'Hair removal cream was arsenic sulphide. Toxic vapour, blistered skin, and with time, organ failure.',
    'Eighteen seventy-four: mercury and lard, rubbed along the eyelids to grow lashes back.',
    'From nineteen thirty-three, France sold radium face cream. Samples tested thirty years later still read radioactive.',
    'Lash-Lure dyed lashes with a coal tar chemical. Ulcerated eyelids. Scarred corneas. Blindness. One death, in nineteen thirty-four.',
    "That forced the nineteen thirty-eight act, America's first cosmetics law. It exempted hair dye. The chemical is still in it.",
    'Read the label.',
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


def lines_from(segs, texts):
    """Group segments into one span per line of the script.

    The obvious rule — split at the N-1 widest silences, since paragraph breaks
    should be longer than sentence breaks — is not reliable. On this read it put
    15.6 s against a 15-word line (0.96 words/s) and 9.3 s against "Read the
    label." (0.32 words/s), because this narrator pauses inside sentences about
    as long as she pauses between paragraphs.

    So instead: every line should take time roughly in proportion to how much
    there is to say. This finds the contiguous grouping whose spans best match
    each line's share of the text, by dynamic programming over the segments.
    Gaps are never consulted, so an unusually long breath mid-sentence can't
    move a boundary.
    """
    n, L = len(segs), len(texts)
    if n < L:
        raise SystemExit(f'only {n} speech segments for {L} lines; check the take')

    total = segs[-1][1] - segs[0][0]
    weight = [len(t) for t in texts]                 # characters track speech time well
    share = [w / sum(weight) for w in weight]
    want = [s * total for s in share]

    INF = float('inf')
    # dp[k][i]: best cost covering segments [0, i) with the first k lines
    dp = [[INF] * (n + 1) for _ in range(L + 1)]
    back = [[-1] * (n + 1) for _ in range(L + 1)]
    dp[0][0] = 0.0
    for k in range(1, L + 1):
        for i in range(k, n - (L - k) + 1):
            for j in range(k - 1, i):
                if dp[k - 1][j] == INF:
                    continue
                span = segs[i - 1][1] - segs[j][0]
                cost = dp[k - 1][j] + (span - want[k - 1]) ** 2
                if cost < dp[k][i]:
                    dp[k][i] = cost
                    back[k][i] = j

    cuts, i = [], n
    for k in range(L, 0, -1):
        j = back[k][i]
        cuts.append((j, i))
        i = j
    cuts.reverse()
    return [[segs[j][0], segs[i - 1][1]] for j, i in cuts]


if __name__ == '__main__':
    import soundfile as sf

    raw, sr = sf.read(RAW, always_2d=True)
    assert sr == SR, f'expected {SR}, got {sr}'
    mono = raw.mean(axis=1)

    y = voice_chain(mono)
    S.write(os.path.join(HERE, 'narration.wav'), y)

    segs = segments(y.mean(axis=0))
    groups = lines_from(segs, LINES)

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
