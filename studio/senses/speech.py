#!/usr/bin/env python3
"""speech: read a voice recording the way a narration coach would.

  python3 studio/senses/speech.py take.wav [more.wav ...] [--json out.json] [--plot out.png]

It finds the pauses and the breath groups between them, then measures, for each file:
  - talk rate (syllables per second while speaking) and overall rate (pauses included)
  - how often the speaker pauses, and how long (short = inside a sentence, long = between thoughts)
  - breath-group length, and how much it varies (people vary a lot; machines tend not to)
  - pitch: the range used, how far it falls across a breath group (declination),
    and how far it jumps back up after a pause (the reset that says "new thought")
  - loudness fall across a breath group, and how much the last syllable stretches

Time of a frame = its middle (see misses.md). Syllables are counted from loudness peaks in the
voiced band, so the rate is an estimate: good for comparing recordings, not a phonetic count.
"""
import sys, json, argparse
import numpy as np
import soundfile as sf
import librosa
from scipy.signal import butter, sosfiltfilt, find_peaks
from scipy.ndimage import uniform_filter1d

SR = 16000
HOP = 160            # 10 ms
MIN_PAUSE = 0.15     # shorter gaps are stop consonants, not pauses


def load(path):
    y, sr = librosa.load(path, sr=SR, mono=True)
    return y / (np.max(np.abs(y)) + 1e-9)


def envelope(y):
    sos = butter(4, [250, 3400], btype='band', fs=SR, output='sos')
    v = sosfiltfilt(sos, y)
    win = 400
    e = np.sqrt(uniform_filter1d(v * v, win)[::HOP] + 1e-12)
    return 20 * np.log10(e + 1e-9)          # dB per 10 ms frame, centred


def speech_mask(db):
    floor = np.percentile(db, 5)
    top = np.percentile(db, 95)
    thr = max(floor + 9, top - 32)
    m = db > thr
    # close gaps under MIN_PAUSE, drop blips under 60 ms
    def runs(mask):
        d = np.diff(np.concatenate([[0], mask.astype(int), [0]]))
        return list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))
    for a, b in runs(~m):
        if (b - a) * HOP / SR < MIN_PAUSE and a > 0 and b < len(m):
            m[a:b] = True
    for a, b in runs(m):
        if (b - a) * HOP / SR < 0.06:
            m[a:b] = False
    return m, runs(m)


def syllables(db, a, b):
    seg = db[a:b]
    if len(seg) < 5:
        return np.array([], int)
    sm = uniform_filter1d(seg, 5)
    pk, _ = find_peaks(sm, prominence=2.5, distance=9)
    return pk + a


def analyse(path):
    y = load(path)
    db = envelope(y)
    mask, groups = speech_mask(db)
    if not groups:
        return None
    t = lambda f: f * HOP / SR
    f0, vflag, _ = librosa.pyin(y, fmin=60, fmax=400, sr=SR, hop_length=HOP, frame_length=1024)
    n = min(len(f0), len(db))
    f0 = f0[:n]
    st = 12 * np.log2(f0 / 100.0)           # semitones re 100 Hz

    pauses = [t(groups[i + 1][0] - groups[i][1]) for i in range(len(groups) - 1)]
    glen, rates, decl, resets, efall, finals = [], [], [], [], [], []
    nsyl = 0
    prev_end_pitch = None
    for a, b in groups:
        b = min(b, n)
        dur = t(b - a)
        pk = syllables(db, a, b)
        nsyl += len(pk)
        glen.append(dur)
        if dur > 0.6 and len(pk) >= 3:
            rates.append(len(pk) / dur)
            iv = np.diff(pk) * HOP / SR
            if len(iv) >= 4:
                finals.append(iv[-1] / np.median(iv[:-1]))
        s = st[a:b]
        ok = np.isfinite(s)
        if ok.sum() > 20 and dur > 0.8:
            x = np.arange(b - a)[ok] * HOP / SR
            k = np.polyfit(x, s[ok], 1)
            decl.append(k[0] * dur)          # semitones fallen (negative) across the group
            q = max(3, ok.sum() // 5)
            start_p, end_p = np.median(s[ok][:q]), np.median(s[ok][-q:])
            if prev_end_pitch is not None:
                resets.append(start_p - prev_end_pitch)
            prev_end_pitch = end_p
            e = db[a:b]
            third = max(2, (b - a) // 3)
            efall.append(np.mean(e[-third:]) - np.mean(e[:third]))
    speak = sum(glen)
    total = t(groups[-1][1] - groups[0][0])
    okall = np.isfinite(st)
    p = np.array(pauses) if pauses else np.array([0.0])
    return {
        'file': path, 'seconds': round(total, 2),
        'talk_rate_syl_s': round(nsyl / speak, 2),
        'overall_rate_syl_s': round(nsyl / total, 2),
        'pause_share': round(1 - speak / total, 3),
        'pauses_per_min': round(60 * len(pauses) / total, 1),
        'pause_median_s': round(float(np.median(p)), 3),
        'pause_p90_s': round(float(np.percentile(p, 90)), 3),
        'pauses': [round(x, 3) for x in pauses],
        'group_median_s': round(float(np.median(glen)), 2),
        'group_cv': round(float(np.std(glen) / (np.mean(glen) + 1e-9)), 2),
        'groups': [round(x, 2) for x in glen],
        'rate_cv': round(float(np.std(rates) / (np.mean(rates) + 1e-9)), 3) if len(rates) > 1 else None,
        'pitch_median_hz': round(float(100 * 2 ** (np.median(st[okall]) / 12)), 1) if okall.any() else None,
        'pitch_range_st': round(float(np.percentile(st[okall], 95) - np.percentile(st[okall], 5)), 2) if okall.any() else None,
        'declination_st': round(float(np.median(decl)), 2) if decl else None,
        'reset_st': round(float(np.median(resets)), 2) if resets else None,
        'energy_fall_db': round(float(np.median(efall)), 2) if efall else None,
        'final_stretch': round(float(np.median(finals)), 2) if finals else None,
        'bounds': [(round(t(a), 3), round(t(b), 3)) for a, b in groups],
    }


def pool(rs):
    """One profile from many recordings: medians of the per-file numbers, all pauses pooled."""
    keys = ['talk_rate_syl_s', 'overall_rate_syl_s', 'pause_share', 'pauses_per_min', 'group_median_s', 'group_cv',
            'rate_cv', 'pitch_range_st', 'declination_st', 'reset_st', 'energy_fall_db', 'final_stretch']
    out = {'files': len(rs), 'seconds': round(sum(r['seconds'] for r in rs), 1)}
    for k in keys:
        v = [r[k] for r in rs if r[k] is not None]
        if v:
            out[k] = round(float(np.median(v)), 3)
            out[k + '_iqr'] = [round(float(np.percentile(v, 25)), 3), round(float(np.percentile(v, 75)), 3)]
    allp = np.array([p for r in rs for p in r['pauses']])
    if len(allp):
        out['pause_n'] = len(allp)
        out['pause_quartiles_s'] = [round(float(np.percentile(allp, q)), 3) for q in (10, 25, 50, 75, 90)]
    allg = np.array([g for r in rs for g in r['groups']])
    out['group_quartiles_s'] = [round(float(np.percentile(allg, q)), 2) for q in (10, 25, 50, 75, 90)]
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('files', nargs='+')
    ap.add_argument('--json')
    ap.add_argument('--pool', action='store_true', help='print one pooled profile instead of a line per file')
    a = ap.parse_args()
    rs = [r for r in (analyse(f) for f in a.files) if r]
    if a.pool:
        print(json.dumps(pool(rs), indent=1))
    else:
        for r in rs:
            print(json.dumps({k: v for k, v in r.items() if k not in ('pauses', 'groups', 'bounds')}))
    if a.json:
        json.dump({'pooled': pool(rs), 'files': rs}, open(a.json, 'w'), indent=1)
