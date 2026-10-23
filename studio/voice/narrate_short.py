#!/usr/bin/env python3
"""Narrate a Short with the studio voice (Kokoro, local, free), matched to the beer-flood narrator.

    python3 studio/voice/narrate_short.py <models dir> <beer_ref.wav> <out dir> --lines lines.json

lines.json is a list of strings, one per beat. Writes narration.wav (44.1 kHz) and times.json:
{"durs": [...beat seconds...], "starts": [...], "voice": [[start, end], ...]} so the picture can retime to the read.
"""
import argparse, json, os, re, subprocess
import numpy as np, soundfile as sf, librosa
from scipy import signal as sg
from kokoro_onnx import Kokoro

SR = 24000
LEAD, TAIL = 0.06, 0.10          # silence before a line starts in its beat, and after it ends


def ltas(y):
    f, p = sg.welch(y, SR, nperseg=2048)
    return f, 10 * np.log10(p + 1e-14)


def squeeze(a, max_pause=0.13, floor=0.012):
    """Cut every quiet gap inside a take down to max_pause s, so there's no dead air or breathy pause mid-line."""
    env = np.convolve(np.abs(a), np.ones(240) / 240, 'same')
    quiet = env < floor
    out, i, n, keep = [], 0, len(a), int(max_pause * SR)
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]:
                j += 1
            if j - i > keep:
                h = keep // 2
                seg = np.concatenate([a[i:i + h] * np.linspace(1, 0, h), a[j - h:j] * np.linspace(0, 1, h)])
                out.append(seg)
            else:
                out.append(a[i:j])
            i = j
        else:
            j = i
            while j < n and not quiet[j]:
                j += 1
            out.append(a[i:j]); i = j
    return np.concatenate(out)


def trim(a):
    nz = np.where(np.abs(a) > 0.01)[0]
    return a[max(0, nz[0] - 240):nz[-1] + 480]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('models'); ap.add_argument('ref'); ap.add_argument('out')
    ap.add_argument('--lines', required=True)
    ap.add_argument('--holds', help='json list of extra seconds per beat')
    ap.add_argument('--speed', type=float, default=1.12)
    ap.add_argument('--preset', help='named voice from voices.json (male is the default; female = Cody\'s A3 pick)')
    ap.add_argument('--voice', default='am_fenrir:0.65,am_puck:0.35', help='voice blend, e.g. af_heart:0.6,af_bella:0.4')
    ap.add_argument('--no-match', action='store_true', help='skip the tone match to the reference read (use for voices unlike the ref)')
    ap.add_argument('--lang', default='en-us')
    ap.add_argument('--gap', type=float, default=0.12, help='pause at a sentence end inside a line (s)')
    ap.add_argument('--max-pause', type=float, default=0.13, help='longest quiet gap allowed inside a sentence (s)')
    ap.add_argument('--choppy', action='store_true', help='old way: speak each sentence separately (each one restarts like a fresh breath)')
    ap.add_argument('--hold', type=float, default=0.8, help="pause for '...' (s)")
    ap.add_argument('--after-scale', type=float, default=0.35, help='scale the pause after each line (tight, no dead air)')
    a = ap.parse_args()
    if a.preset:                                    # a saved voice overrides the voice settings
        P = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'voices.json')))[a.preset]
        a.voice, a.speed, a.no_match = P['voice'], P['speed'], not P.get('match', True)
        a.gap, a.hold, a.after_scale = P.get('gap', a.gap), P.get('hold', a.hold), P.get('after_scale', a.after_scale)
        a.max_pause = P.get('max_pause', a.max_pause)
    lines = json.load(open(a.lines))
    # a line is a string, or {"text", "speed" (x base speed), "after" (pause after the line, s)}
    lines = [l if isinstance(l, dict) else {'text': l} for l in lines]
    holds = json.load(open(a.holds)) if a.holds else [l.get('after', 0.3) * a.after_scale for l in lines]
    k = Kokoro(os.path.join(a.models, 'kokoro-v1.0.onnx'), os.path.join(a.models, 'voices-v1.0.bin'))
    style = None
    for part in a.voice.split(','):
        nm, w = (part.split(':') + ['1'])[:2]
        v = k.get_voice_style(nm.strip()) * float(w)
        style = v if style is None else style + v
    female = a.voice.startswith(('af_', 'bf_'))
    # words the voice gets wrong: swap in the right sound (say.json), captions keep the real word
    say = {w.lower(): ph for w, ph in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'say.json'))).items() if not w.startswith('_')}

    def speak(txt, sp):
        if not any(re.search(r'\b' + re.escape(w) + r'\b', txt, re.I) for w in say):
            return k.create(txt, voice=style, speed=sp, lang=a.lang)[0]
        ph = k.tokenizer.phonemize(txt, a.lang)
        for w, fix in say.items():
            ph = ph.replace(k.tokenizer.phonemize(w, a.lang).strip(), fix)
        return k.create(ph, voice=style, speed=sp, lang=a.lang, is_phonemes=True)[0]
    takes = []
    for line in lines:
        sp = a.speed * line.get('speed', 1.0)
        segs = []
        # '...' is a held beat (0.8 s). By default a whole line is spoken in ONE take so the sentences run on
        # naturally (owner: 'take the breaths out'); --choppy splits at sentence ends like before.
        splitter = r'(\.\.\.|(?<=[.!?])\s+)' if a.choppy else r'(\.\.\.)'
        for chunk in re.split(splitter, line['text'].strip()):
            if chunk is None or not chunk.strip():
                continue
            if chunk == '...':
                segs.append(np.zeros(int(a.hold * SR))); continue
            y = speak(chunk.strip(), sp)
            segs += [squeeze(trim(y), a.max_pause), np.zeros(int(a.gap * SR))]
        takes.append(np.concatenate(segs[:-1]))
    # every line at the same loudness, so the voice never jumps between beats
    lv = [np.sqrt(np.mean(y[np.abs(y) > 0.02] ** 2)) for y in takes]
    ref_lv = float(np.median(lv))
    takes = [y * float(np.clip(ref_lv / (l + 1e-9), 0.6, 1.6)) for y, l in zip(takes, lv)]
    # tone match to the beer narrator, measured on the whole read
    ref, _ = librosa.load(a.ref, sr=SR)
    f, Lr = ltas(ref); _, Ly = ltas(np.concatenate(takes))
    diff = np.clip(sg.savgol_filter(Lr - Ly - np.mean((Lr - Ly)[(f > 300) & (f < 3000)]), 101, 2), -5, 5)
    diff[f < 70] = -12
    if a.no_match:
        diff = np.where(f < 70, -12.0, 0.0)
    fir = sg.minimum_phase(sg.firwin2(513, f / (SR / 2), 10 ** (diff / 20)), method='homomorphic')
    starts, durs, voice, t = [], [], [], 0.0
    for y, h in zip(takes, holds):
        d = LEAD + len(y) / SR + TAIL + h
        starts.append(t); durs.append(d); voice.append([t + LEAD, t + LEAD + len(y) / SR]); t += d
    out = np.zeros(int(t * SR) + SR)
    for y, (s0, _) in zip(takes, voice):
        y = sg.lfilter(fir, [1.0], y)
        env = np.sqrt(sg.lfilter([1 - 0.9995], [1, -0.9995], y ** 2)) + 1e-4
        g = np.clip((np.median(env[env > 0.01]) / env) ** 0.3, 0.7, 1.6)
        y = y * sg.lfilter([0.002], [1, -0.998], g)
        th = 10 ** (-18 / 20); ab = np.abs(y); c = np.where(ab > th, (th + (ab - th) / 2) / (ab + 1e-9), 1.0)
        y = y * sg.lfilter([0.02], [1, -0.98], c)
        i = int(s0 * SR); out[i:i + len(y)] += y
    out = out[:int(t * SR)]
    os.makedirs(a.out, exist_ok=True)
    raw = os.path.join(a.out, 'narration_raw.wav')
    sf.write(raw, out / (np.max(np.abs(out)) + 1e-9) * 0.9, SR)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', raw, '-af',
                    ('highpass=f=90,equalizer=f=300:t=o:w=1.2:g=-2.5,equalizer=f=4500:t=o:w=1.2:g=2,equalizer=f=9500:t=o:w=1:g=-2,'
                     'loudnorm=I=-16:TP=-2:LRA=15') if female else
                    'equalizer=f=450:t=o:w=1.3:g=-5,equalizer=f=150:t=o:w=1:g=2,loudnorm=I=-16:TP=-2:LRA=15',
                    '-ar', '44100', os.path.join(a.out, 'narration.wav')])
    os.unlink(raw)
    json.dump(dict(durs=durs, starts=starts, voice=voice, total=t), open(os.path.join(a.out, 'times.json'), 'w'), indent=1)
    print('ok', round(t, 2))


if __name__ == '__main__':
    main()
