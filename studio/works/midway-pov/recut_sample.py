"""recut_sample.py: re-edit Midway's climax (10:20 to the Hiryu turn, ~1:30) by docs/editing-rules.md.

Changes against the film as posted (same drawings, same narration):
  - punch-ins on the long POV holds, tightening as the dive goes (rules 2, 4): bridge 1.18x on
    "Not one torpedo has hit", up into the empty sky on "Nobody is watching the sky", 1.3x on
    "It grows in your sight", 1.6x on "Release."
  - J-cut (rule 13): the dive bombers' engines come in far and high 3 s before we see them
  - silence before the hit (rule 14): everything ducks the 1.6 s before "Release."
  - pillow shot (rule 9): after "three of the carriers that bombed Pearl Harbor are on fire",
    5 s on the burning carriers with only fire, wind and sea, narration held back; the fire bed
    leads in under the line (J) so the pause doesn't feel like a gap
  - the ending holds 3.2 s on the Hiryu turn and fades (rule 12)
Usage: python3 recut_sample.py full.mp4 out.mp4
"""
import os, subprocess, sys, tempfile
import numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'sfx')); sys.path.insert(0, os.path.join(HERE, '..', '..', 'instruments'))
import foley as F

SRC, OUT = sys.argv[1], sys.argv[2]
SR = 48000
A0, PIL, A1, END = 277.0, 351.6, 356.4, 3.2   # source in, pillow point, source out, end hold
PILLOW = 5.0
# picture: (src_t0, src_t1, zoom, focus_y)  punch-ins anchor to the bottom (focus_y 1.0) so burned-in captions stay whole
SEGS = [(277.0, 296.3, 1.0, .5), (296.3, 303.4, 1.18, 1.0), (303.4, 306.8, 1.45, 1.0), (306.8, 321.1, 1.0, .5), (321.1, 329.1, 1.0, .5),
        (329.1, 334.2, 1.3, 1.0), (334.2, 335.8, 1.6, 1.0), (335.8, 339.5, 1.0, .5), (339.5, 346.6, 1.15, 1.0), (346.6, PIL, 1.3, 1.0)]
TAIL = [(PIL, A1, 1.0, .5)]
tmp = tempfile.mkdtemp()


def ff(*a): subprocess.run(['ffmpeg', '-v', 'error', '-y', *a], check=True)


def seg(i, t0, t1, z, fy):
    o = f'{tmp}/s{i:02d}.mp4'
    vf = 'scale=1920:1080' if z == 1 else f'crop=iw/{z}:ih/{z}:(iw-iw/{z})/2:(ih-ih/{z})*{fy},scale=1920:1080'
    ff('-ss', f'{t0}', '-t', f'{t1 - t0:.3f}', '-i', SRC, '-vf', vf + ',fps=30,format=yuv420p', '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '17', o)
    return o


def hold(i, t, dur, z0, z1, fade=0):
    o = f'{tmp}/s{i:02d}.mp4'; png = f'{tmp}/h{i}.png'
    ff('-ss', f'{t}', '-i', SRC, '-frames:v', '1', png)
    n = int(dur * 30)
    vf = f"scale=3840:-1,zoompan=z='{z0}+({z1}-{z0})*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s=1920x1080:fps=30,format=yuv420p"
    if fade: vf += f',fade=t=out:st={dur - fade}:d={fade}'
    ff('-loop', '1', '-i', png, '-vf', vf, '-t', f'{dur}', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '17', o)
    return o


parts = [seg(i, *s) for i, s in enumerate(SEGS)]
parts.append(hold(20, PIL - 0.05, PILLOW, 1.0, 1.07))
parts += [seg(30 + i, *s) for i, s in enumerate(TAIL)]
parts.append(hold(40, A1 - 0.05, END, 1.0, 1.04, fade=1.2))
open(f'{tmp}/list.txt', 'w').write(''.join(f"file '{p}'\n" for p in parts))
ff('-f', 'concat', '-safe', '0', '-i', f'{tmp}/list.txt', '-c', 'copy', f'{tmp}/pic.mp4')

# ---- sound
ff('-ss', f'{A0}', '-t', f'{A1 - A0 + 0.5}', '-i', SRC, '-vn', '-ac', '2', '-ar', str(SR), f'{tmp}/a.wav')
src, _ = sf.read(f'{tmp}/a.wav')
s = lambda t: int(round((t - A0) * SR))


def xf(a, b, n=1440):  # 30 ms crossfade join
    r = np.linspace(0, 1, n)[:, None]
    return np.concatenate([a[:-n], a[-n:] * (1 - r) + b[:n] * r, b[n:]])


# silence before the hit: duck 1.6 s before "Release." (334.2), slam back on the word
g = np.ones(len(src))
d0, d1 = s(332.6), s(334.15)
g[d0:d1] = np.interp(np.arange(d1 - d0), [0, (d1 - d0) * .25, d1 - d0], [1, 10 ** (-14 / 20), 10 ** (-14 / 20)])
src = src * g[:, None]

pre = src[:s(PIL)]
post = src[s(PIL):s(A1)]
amb_len = PILLOW + END + 3.0
tr = F.Track(amb_len + 2.0, tail=1.0)
tr.bed('fire', 0.0, amb_len, db=-2, fin=1.5, fout=1.0)
tr.bed('waves', 0.0, amb_len, db=-8, fin=2.0, fout=1.0)
tr.bed('wind', 0.0, amb_len, db=-10, fin=2.0, fout=1.0)
amb = np.asarray(tr.out()).T if np.asarray(tr.out()).shape[0] == 2 else np.asarray(tr.out())
amb = amb[:, :2] if amb.ndim == 2 else np.stack([amb, amb], 1)
amb = amb * 0.9
lead = int(1.5 * SR)  # the fire leads in under the last line (J-cut into the pillow)
pre[-lead:] += amb[:lead] * np.linspace(0, 1, lead)[:, None]
pillow = amb[lead:lead + int(PILLOW * SR)]
endamb = amb[lead + int(PILLOW * SR):lead + int((PILLOW + END) * SR)]
end = endamb.copy()  # the next scene's narration starts right after A1, so the hold is ambience only
end *=np.concatenate([np.ones(len(end) - int(1.2 * SR)), np.linspace(1, 0, int(1.2 * SR))])[:, None]
mix = xf(xf(xf(pre, pillow), post), end)

# J-cut: the dive bombers' engines arrive far and high 3 s before we see them (seen at ~315.8 source)
jt = (312.8 - A0)
eng = F.Track(9.0, tail=1.0); eng.bed('drone_far', 0.0, 7.0, db=-6, fin=2.5, fout=1.5); eng.hit('dive_run', 4.0, db=-14)
e = np.asarray(eng.out()); e = e.T if e.shape[0] == 2 else e
mix[int(jt * SR):int(jt * SR) + len(e)] += e[:len(mix) - int(jt * SR)] * 0.9

peak = np.abs(mix).max()
if peak > 0.89: mix *= 0.89 / peak  # keep true peak under -1 dBTP
sf.write(f'{tmp}/mix.wav', mix, SR)
ff('-i', f'{tmp}/pic.mp4', '-i', f'{tmp}/mix.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', OUT)
sf.write(OUT.rsplit('.', 1)[0] + '.wav', mix, SR)
import json
lens = [t1 - t0 for t0, t1, *_ in SEGS] + [PILLOW] + [t1 - t0 for t0, t1, *_ in TAIL] + [END]
json.dump([round(float(x), 3) for x in np.cumsum(lens)[:-1]], open(OUT.rsplit('.', 1)[0] + '.cuts.json', 'w'))
print('wrote', OUT)
