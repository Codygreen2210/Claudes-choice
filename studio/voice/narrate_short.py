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
LEAD, TAIL = 0.12, 0.22          # silence before a line starts in its beat, and after it ends


def ltas(y):
    f, p = sg.welch(y, SR, nperseg=2048)
    return f, 10 * np.log10(p + 1e-14)


def trim(a):
    nz = np.where(np.abs(a) > 0.01)[0]
    return a[max(0, nz[0] - 240):nz[-1] + 480]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('models'); ap.add_argument('ref'); ap.add_argument('out')
    ap.add_argument('--lines', required=True)
    ap.add_argument('--holds', help='json list of extra seconds per beat')
    ap.add_argument('--speed', type=float, default=1.28)
    a = ap.parse_args()
    lines = json.load(open(a.lines))
    # a line is a string, or {"text", "speed" (x base speed), "after" (pause after the line, s)}
    lines = [l if isinstance(l, dict) else {'text': l} for l in lines]
    holds = json.load(open(a.holds)) if a.holds else [l.get('after', 0.3) for l in lines]
    k = Kokoro(os.path.join(a.models, 'kokoro-v1.0.onnx'), os.path.join(a.models, 'voices-v1.0.bin'))
    style = k.get_voice_style('am_fenrir') * 0.65 + k.get_voice_style('am_puck') * 0.35
    takes = []
    for line in lines:
        sp = a.speed * line.get('speed', 1.0)
        segs = []
        # '...' is a held beat (0.55 s); a sentence end is the narrator's normal 0.24 s breath
        for chunk in re.split(r'(\.\.\.|(?<=[.!?])\s+)', line['text'].strip()):
            if chunk is None or not chunk.strip():
                continue
            if chunk == '...':
                segs.append(np.zeros(int(0.55 * SR))); continue
            y, _ = k.create(chunk.strip(), voice=style, speed=sp, lang='en-us')
            segs += [trim(y), np.zeros(int(0.24 * SR))]
        takes.append(np.concatenate(segs[:-1]))
    # tone match to the beer narrator, measured on the whole read
    ref, _ = librosa.load(a.ref, sr=SR)
    f, Lr = ltas(ref); _, Ly = ltas(np.concatenate(takes))
    diff = np.clip(sg.savgol_filter(Lr - Ly - np.mean((Lr - Ly)[(f > 300) & (f < 3000)]), 101, 2), -5, 5)
    diff[f < 70] = -12
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
                    'equalizer=f=450:t=o:w=1.3:g=-5,equalizer=f=150:t=o:w=1:g=2,loudnorm=I=-16:TP=-2:LRA=15',
                    '-ar', '44100', os.path.join(a.out, 'narration.wav')])
    os.unlink(raw)
    json.dump(dict(durs=durs, starts=starts, voice=voice, total=t), open(os.path.join(a.out, 'times.json'), 'w'), indent=1)
    print('ok', round(t, 2))


if __name__ == '__main__':
    main()
