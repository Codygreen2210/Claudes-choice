#!/usr/bin/env python3
"""assemble.py: turn the voice takes into one narration track and the timing the picture is cut to.

For each scene it needs  vo/s<N>.mp3  (the take) and  vo/s<N>.words.json  (word times from the transcript).
It then:
  1. lines the transcript's words up with the script's words, so cues and captions use the script's spelling
  2. finds the real silences in the waveform (studio/senses/speech.py), not just the transcript's gaps
  3. retimes the pauses: each one is kept as the voice gave it unless it falls outside the band a human
     narrator uses for that kind of break (comma / full stop / a beat), and then it is brought to the edge
     of the band. Nothing is stretched or sped up; only silence is cut or added, in the middle of the gap.
  4. joins the scenes with a breath between them and writes narration.wav, timing.json, timing.js
"""
import json, re, sys, os, subprocess, difflib
import numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..'))
from studio.senses import speech as SP

SR = 44100
LEAD, TAIL, GAP = 2.0, 5.0, 1.25
# pause bands, seconds. Inside-sentence band is the middle 80% of 99 pauses measured in five human narrators
# (LibriVox readers, see notes/human.json); the between-sentence bands are from read-speech studies
# (mean pauses 0.47-0.77 s) and from the one orator in the set (0.7 s median).
BAND = {'none': (0.0, 0.16), 'comma': (0.17, 0.46), 'stop': (0.50, 0.85), 'dots': (0.45, 0.80), 'beat': (0.95, 1.35)}
norm = lambda s: re.sub(r'[^a-z0-9]', '', s.lower())

def decode(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)

def kind(word, beat_after):
    if beat_after: return 'beat'
    if re.search(r'…["”]?$', word): return 'dots'
    if re.search(r'[.?!]["”]?$', word): return 'stop'
    if re.search(r'[,;:]["”]?$', word): return 'comma'
    return 'none'

def align(script_words, heard):
    """script_words: [str]; heard: [{text,start,end}] -> [(s, e)] for every script word."""
    a = [norm(w) for w in script_words]; b = [norm(h['text']) for h in heard]
    out = [None] * len(a)
    for tag, i0, i1, j0, j1 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == 'equal':
            for k in range(i1 - i0): out[i0 + k] = (heard[j0 + k]['start'], heard[j0 + k]['end'])
        elif tag == 'replace' and j1 > j0:                         # "39 dollars" heard as "$39" and the like: share the span by length
            s, e = heard[j0]['start'], heard[j1 - 1]['end']; L = [max(1, len(x)) for x in a[i0:i1]]; c = np.concatenate([[0], np.cumsum(L)]) / sum(L)
            for k in range(i1 - i0): out[i0 + k] = (s + (e - s) * c[k], s + (e - s) * c[k + 1])
    # anything still missing sits between its neighbours
    for i, v in enumerate(out):
        if v is None:
            p = next((out[k][1] for k in range(i - 1, -1, -1) if out[k]), 0.0); n = next((out[k][0] for k in range(i + 1, len(out)) if out[k]), p + 0.3)
            out[i] = (p, max(p + 0.05, min(n, p + 0.4)))
    return out

def scene(i, text_tagged, report):
    y = decode(f'{HERE}/vo/s{i + 1}.mp3')
    heard = json.load(open(f'{HERE}/vo/s{i + 1}.words.json'))
    heard = [h for h in heard if h.get('type', 'word') == 'word' and norm(h['text']) and not re.fullmatch(r'\[.*\]', h['text'])]
    # script words, remembering where a [pause] tag followed
    toks = text_tagged.split(); words, beat = [], []
    for t in toks:
        if re.fullmatch(r'\[.*?\]', t):
            if words: beat[-1] = True
        else: words.append(t); beat.append(False)
    times = align(words, heard)
    # trim the take to its speech
    db = SP.envelope(np.interp(np.arange(0, len(y), SR / SP.SR), np.arange(len(y)), y)); mask, runs = SP.speech_mask(db)
    fr = SP.HOP / SP.SR
    t_first, t_last = runs[0][0] * fr, runs[-1][1] * fr
    floor = float(np.sqrt(np.mean(y[: int(max(0.05, t_first - 0.02) * SR)] ** 2) + 1e-12)) if t_first > 0.08 else 1e-5
    rngl = np.random.default_rng(i)
    pieces, shift, cuts = [], 0.0, []
    pos = max(0.0, t_first - 0.06)
    for k in range(len(words) - 1):
        gap0, gap1 = times[k][1], times[k + 1][0]
        kd = kind(words[k], beat[k])
        # the quiet stretch inside this gap, from the waveform
        # (the transcript's word ends run on into the silence, so look from just inside the word to the next word's start)
        a = int((times[k][0] + 0.05) / fr); b = int((gap1 + 0.06) / fr) + 1
        quiet = [(max(r0, a), min(r1, b)) for r0, r1 in zip([0] + [r[1] for r in runs], [r[0] for r in runs] + [len(mask)]) if min(r1, b) - max(r0, a) > 0]
        if not quiet:
            if kd in ('none',): continue
            qs = qe = (gap0 + gap1) / 2; have = 0.0
        else:
            qa, qb = max(quiet, key=lambda r: r[1] - r[0]); qs, qe = qa * fr, qb * fr; have = qe - qs
        lo, hi = BAND[kd]
        want = min(max(have, lo), hi) if kd != 'none' else have
        if kd == 'none' and have > 0.3: want = 0.2                # a stumble in mid-phrase
        report.append((i + 1, words[k], kd, round(have, 3), round(want, 3)))
        if abs(want - have) < 0.03: continue
        mid = (qs + qe) / 2
        cuts.append((mid, want - have))
    # apply the edits left to right
    out = []; cur = int(pos * SR); delta = 0.0; marks = []
    for mid, d in cuts:
        m = int(mid * SR)
        if d > 0:
            out.append(y[cur:m]); out.append(rngl.standard_normal(int(d * SR)) * floor * 0.7); cur = m
        else:
            h = int(-d * SR / 2); out.append(y[cur:m - h]); cur = m + h
        marks.append((mid, d))
    out.append(y[cur:int(min(len(y) / SR, t_last + 0.25) * SR)])
    # short crossfades at every join so no edit clicks
    xf = int(0.008 * SR); res = out[0].copy()
    for seg in out[1:]:
        if len(seg) < xf or len(res) < xf: res = np.concatenate([res, seg]); continue
        w = np.linspace(0, 1, xf); res[-xf:] = res[-xf:] * (1 - w) + seg[:xf] * w; res = np.concatenate([res, seg[xf:]])
    def remap(t):
        s = t - pos
        for mid, d in marks:
            if t > mid: s += d
        return s - xf / SR * sum(1 for mid, d in marks if t > mid)
    tw = [(max(0, remap(s)), max(0, remap(e))) for s, e in times]
    return res, words, tw

def main():
    script = json.load(open(f'{HERE}/script.json'))
    tagged = script['tagged']
    t = LEAD; audio = [np.zeros(int(LEAD * SR))]; scenes = []; report = []
    for i, txt in enumerate(tagged):
        y, words, tw = scene(i, txt, report)
        scenes.append({'start': round(t + tw[0][0], 3), 'end': round(t + tw[-1][1], 3), 'words': [{'w': w, 's': round(t + s, 3), 'e': round(t + e, 3)} for w, (s, e) in zip(words, tw)]})
        audio.append(y); t += len(y) / SR
        if i < len(tagged) - 1: audio.append(np.zeros(int(GAP * SR))); t += GAP
    audio.append(np.zeros(int(TAIL * SR))); total = round(t + TAIL, 2)
    y = np.concatenate(audio)
    sf.write(f'{HERE}/narration.wav', y.astype(np.float32), SR, subtype='PCM_16')
    T = {'scenes': scenes, 'total': total}
    json.dump(T, open(f'{HERE}/timing.json', 'w')); open(f'{HERE}/timing.js', 'w').write('window.TIMING = ' + json.dumps(T))
    json.dump(report, open(f'{HERE}/notes/pauses.json', 'w'))
    ch = [r for r in report if abs(r[3] - r[4]) >= 0.03]
    print(f'narration.wav {total}s; {len(report)} breaks looked at, {len(ch)} retimed')
    for r in ch: print('  scene', r[0], repr(r[1]), r[2], r[3], '->', r[4])

if __name__ == '__main__':
    os.makedirs(f'{HERE}/notes', exist_ok=True); main()
