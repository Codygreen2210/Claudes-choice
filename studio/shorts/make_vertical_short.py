#!/usr/bin/env python3
"""make_vertical_short.py: a full-frame vertical Short (1080x1920) cut from one complete scene of a story film.

    python3 make_vertical_short.py <film> <scene> "<hook, small on top>" "<question, spoken>" "<question, on screen>" <out.mp4>
                                   [--crop "0:960,8.5:900,20:960"] [--clip pre-rendered-clean-scene.mp4]

Built from what the first Short taught us (Oct 12 2026: 85% swiped away, stalled at 667 views):
  - the picture fills the whole tall frame: the scene is re-rendered without its burned-in captions and labels,
    and a 9:16 window is cut out of it, panning to follow the action (--crop: seconds-into-the-Short:centre-x pairs);
  - the voice starts at 0.0 s on the scene's first word; no fade from black, no title card;
  - captions sit large on the picture, clear of the Shorts buttons; the hook is small at the top;
  - it ends on one spoken question the full film answers, over the last frame, then cuts straight back to the start.
"""
import json, os, re, subprocess, sys, warnings
warnings.filterwarnings('ignore')
import numpy as np, soundfile as sf, librosa, pyloudnorm as pyln
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, ROOT)
from studio.instruments import synth as S

args = sys.argv[1:]
def opt(name, default=None):
    if name in args: k = args.index(name); v = args[k + 1]; del args[k:k + 2]; return v
    return default
crop = opt('--crop', '0:960'); clip = opt('--clip')
pointer = '--no-pointer' not in args
if not pointer: args.remove('--no-pointer')
film, si, hook, q_say, q_show, out = args[:6]; si = int(si)
# point at the Related video link (the only tappable way from a Short to the film): said, and shown low on the frame
if pointer: q_say = q_say.rstrip() + ' The full story is linked, right above the title.'
FD = os.path.join(ROOT, 'studio', 'works', film); sys.path.insert(0, FD)
import narrate as N
T = json.load(open(os.path.join(FD, 'timing.json')))['scenes']; sc = T[si]
a0 = sc['words'][0]['s'] - 0.06                                   # the voice starts at once
a1 = sc['end'] + 0.7
work = f'/home/claude/work/vshort-{film}-{si}'; os.makedirs(work, exist_ok=True)
SR = S.SR

# ---- the picture: the scene again, without the film's captions and labels
if not clip:
    src = open(os.path.join(FD, 'film.html')).read()
    page = os.path.join(FD, '_vertical.html')
    open(page, 'w').write(src.replace('<script src="film.js"></script>', '<script>window.__vertical = true</script><script src="film.js"></script><script>window.__caps.length = 0</script>'))
    clip = os.path.join(work, 'clean.mp4')
    subprocess.run(['node', os.path.join(ROOT, 'studio', 'motion', 'render.mjs'), page, '--size', '1920x1080', '--from', f'{a0:.3f}', '--to', f'{a1:.3f}', '--workers', '2', '--out', clip, '--quiet'], check=True)
    os.remove(page)

# ---- the sound: the scene from the master mix, then the question in the studio voice over the bed
from kokoro_onnx import Kokoro
M = '/home/claude/work/kokoro'
kk = Kokoro(os.path.join(M, 'kokoro-v1.0.onnx'), os.path.join(M, 'voices-v1.0.bin'))
vec = 0.75 * kk.get_voice_style('am_michael') + 0.25 * kk.get_voice_style('am_eric')
line = librosa.resample(kk.create(q_say, voice=vec, speed=0.94 * (1 + 0.05 * 0.2), lang='en-us')[0].astype(np.float64), orig_sr=24000, target_sr=SR)
nz = np.nonzero(np.abs(line) > 0.01 * np.abs(line).max())[0]; line = N.polish(line[max(0, nz[0] - 800): nz[-1] + 2400])
nar, _ = sf.read(os.path.join(FD, 'narration.wav')); nar = nar.mean(1) if nar.ndim > 1 else nar
line = line * (N.level(nar[int(sc['start'] * SR): int(sc['end'] * SR)]) / N.level(line))
meter = pyln.Meter(SR)
vchain = lambda v: S.eq(S.hp(v, 70, 2)[None, :], [('peak', 220, -1.5, 1.0)])[0]
fac = 10 ** ((-17 - meter.integrated_loudness(vchain(nar))) / 20)
fin, _ = sf.read(os.path.join(FD, 'final.wav')); fin = fin.T if fin.ndim > 1 else np.stack([fin, fin])
i0, i1 = int(a0 * SR), int(a1 * SR)
g = np.sqrt(np.mean(fin[:, i0:i1] ** 2)) / np.sqrt(np.mean((vchain(nar[i0:i1]) * fac) ** 2)) * 0.9
lv = vchain(line) * fac * g
m, _ = sf.read(os.path.join(FD, 'music.wav'))
pre, post = 0.3, 0.6; tail = pre + len(lv) / SR + post
bed = m[i1:i1 + int(tail * SR)].T * 0.62 * g
seg = fin[:, i0:i1].copy(); xf = int(0.25 * SR); seg[:, -xf:] *= np.linspace(1, 0.5, xf)
audio = np.concatenate([seg, np.zeros((2, bed.shape[1]))], 1)
audio[:, seg.shape[1]:seg.shape[1] + bed.shape[1]] += bed * 10 ** (-6 / 20)
q0 = seg.shape[1] + int(pre * SR); audio[:, q0:q0 + len(lv)] += lv
end = audio.shape[1] / SR
k = int(0.12 * SR); audio[:, -k:] *= np.linspace(1, 0, k)                 # no fade-out: a hard cut back to the start
aw = os.path.join(work, 'audio.wav'); sf.write(aw, audio.T.astype(np.float32), SR, subtype='PCM_16')
cut = a1 - a0; qs = q0 / SR

# ---- captions: big on the picture, above the Shorts buttons; the hook small at the top; the question last
def ts(t): t = max(0, t); return f'{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}'
W = [w for w in sc['words'] if w['s'] >= a0 - 0.01]
caps, cur = [], []
for i, w in enumerate(W):
    cur.append(w); txt = ' '.join(x['w'] for x in cur); nxt = W[i + 1] if i + 1 < len(W) else None
    gap = nxt['s'] - w['e'] if nxt else 9
    if re.search(r'[.?!…]["”]?$', w['w']) or gap > 0.4 or len(txt) > 16 or (nxt and len(txt + ' ' + nxt['w']) > 22): caps.append((cur[0]['s'] - a0, cur[-1]['e'] - a0, txt)); cur = []
if cur: caps.append((cur[0]['s'] - a0, cur[-1]['e'] - a0, ' '.join(x['w'] for x in cur)))
ass = os.path.join(work, 'caps.ass'); fonts = os.path.join(FD, 'fonts')
with open(ass, 'w') as fh:
    fh.write('[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n')
    fh.write('Style: C,Old Standard TT,84,&H00D2EAF4,&H00D2EAF4,&H00100C0A,&H96000000,-1,0,0,0,100,100,0,0,1,6,2,2,70,70,600,1\n')
    fh.write('Style: H,Playfair Display,50,&H00D2EAF4,&H00D2EAF4,&H00100C0A,&H96000000,-1,0,0,0,100,100,3,0,1,4,0,8,60,60,190,1\n')
    fh.write('Style: P,Old Standard TT,66,&H00F4EAD2,&H00F4EAD2,&H00100C0A,&H96000000,-1,0,0,0,100,100,0,0,1,6,2,5,70,70,0,1\n')
    fh.write('Style: Q,Old Standard TT,86,&H003A97C9,&H003A97C9,&H00100C0A,&H96000000,-1,0,0,0,100,100,0,0,1,7,2,5,70,70,0,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n')
    fh.write(f'Dialogue: 0,{ts(0)},{ts(qs - 0.1)},H,,0,0,0,,{hook}\n')
    for k2, (s_, e_, txt) in enumerate(caps):
        e2 = min(e_ + 0.3, caps[k2 + 1][0] - 0.05) if k2 + 1 < len(caps) else min(e_ + 0.3, cut)
        fh.write(f'Dialogue: 0,{ts(s_ - 0.04)},{ts(e2)},C,,0,0,0,,{txt}\n')
    fh.write(f'Dialogue: 0,{ts(qs - 0.1)},{ts(end)},Q,,0,0,0,,{{\\pos(540,820)}}{q_show}\n')
    if pointer: fh.write(f'Dialogue: 0,{ts(qs + 0.6)},{ts(end)},P,,0,0,0,,{{\\pos(540,1290)\\fad(200,0)}}FULL FILM: tap the link\\Nabove the title  ↓\n')

# ---- the 9:16 window: 608 x 1080 out of the 1920 x 1080 scene, panning between keys, scaled up to fill
keys = sorted((float(a), float(b)) for a, b in (p.split(':') for p in crop.split(',')))
def xexpr():
    if len(keys) == 1: return f'{keys[0][1] - 304:.1f}'
    e = f'{keys[-1][1] - 304:.1f}'
    for (ta, xa), (tb, xb) in reversed(list(zip(keys, keys[1:]))):
        e = f"if(lt(t,{tb:.3f}),{xa - 304:.1f}+({xb - xa:.1f})*(0.5-0.5*cos(PI*clip((t-{ta:.3f})/{max(tb - ta, 0.01):.3f},0,1))),{e})"
    return f"if(lt(t,{keys[0][0]:.3f}),{keys[0][1] - 304:.1f},{e})"
vf = (f"[0:v]trim=0:{cut:.3f},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={end - cut + 0.1:.3f},"
      f"crop=608:1080:x='clip({xexpr()},0,1312)':y=0,scale=1080:1920:flags=lanczos,"
      f"subtitles='{ass}':fontsdir='{fonts}',format=yuv420p[o];[1:a]alimiter=limit=0.84:level=false[a]")
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', clip, '-i', aw, '-filter_complex', vf, '-map', '[o]', '-map', '[a]', '-t', f'{end:.3f}',
                '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-r', '30', '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', out], check=True)
print(out, round(end, 2), 's; scene', si, round(a0, 2), '-', round(a1, 2), '; question at', round(qs, 2))
