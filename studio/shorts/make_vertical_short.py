#!/usr/bin/env python3
"""make_vertical_short.py: a full-frame vertical Short (1080x1920) cut from one scene of a story film.

    python3 make_vertical_short.py <film> <scene> "<place, small on top>" "<question, spoken>" "<question, on screen>" <out.mp4>
        [--start S --end E]                      film seconds: trim the scene to its strongest 25-35 s (sentence edges)
        [--flash A:B --flash-x X]                film seconds: the most dramatic moment, shown first (cold open)
        [--hook-say "..." --hook-show "..."]     a one-line hook spoken at 0.0 s over the flash, and shown big
        [--crop "0:960,8.5:900"]                 seconds-into-the-scene-part:centre-x pairs, the 9:16 window follows the action
        [--no-pointer]

What the first Shorts taught us (Oct 12 2026):
  - 85% swiped away on the letterboxed ones; the full-frame one did only a little better (83%). People decide in the
    first second, and our first second was a still frame and a line that needed context ("Patterson stayed.").
  - So: open on the most dramatic moment with a hook a stranger understands, spoken at 0.0 s and shown big, with the
    picture already moving (a slow push-in); then tell how it happened; keep it 25 to 35 s.
  - The picture fills the frame: the scene is re-rendered without its captions and labels, and a 9:16 window cut out.
  - It ends on one question the film answers, then points at the Related video link (said and shown), then cuts hard.
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
crop = opt('--crop', '0:960'); start = opt('--start'); stop = opt('--end')
flash = opt('--flash'); flash_x = float(opt('--flash-x', '960')); hook_say = opt('--hook-say'); hook_show = opt('--hook-show'); hook_y = int(opt('--hook-y', '420'))
pointer = '--no-pointer' not in args
if not pointer: args.remove('--no-pointer')
film, si, place, q_say, q_show, out = args[:6]; si = int(si)
if pointer: q_say = q_say.rstrip() + ' The full story is linked, right above the title.'
FD = os.path.join(ROOT, 'studio', 'works', film); sys.path.insert(0, FD)
import narrate as N
T = json.load(open(os.path.join(FD, 'timing.json')))['scenes']; sc = T[si]
W = [w for w in sc['words'] if (start is None or w['s'] >= float(start) - 0.01) and (stop is None or w['e'] <= float(stop) + 0.01)]
a0 = W[0]['s'] - 0.06                                              # the scene's voice starts at once
a1 = (W[-1]['e'] + 0.35) if stop else sc['end'] + 0.7
work = f'/home/claude/work/vshort-{film}-{si}'; os.makedirs(work, exist_ok=True)
SR = S.SR

# ---- voices: the hook and the question, in the studio voice at the film's level
from kokoro_onnx import Kokoro
M = '/home/claude/work/kokoro'
kk = Kokoro(os.path.join(M, 'kokoro-v1.0.onnx'), os.path.join(M, 'voices-v1.0.bin'))
vec = 0.75 * kk.get_voice_style('am_michael') + 0.25 * kk.get_voice_style('am_eric')
nar, _ = sf.read(os.path.join(FD, 'narration.wav')); nar = nar.mean(1) if nar.ndim > 1 else nar
meter = pyln.Meter(SR)
vchain = lambda v: S.eq(S.hp(v, 70, 2)[None, :], [('peak', 220, -1.5, 1.0)])[0]
fac = 10 ** ((-17 - meter.integrated_loudness(vchain(nar))) / 20)
fin, _ = sf.read(os.path.join(FD, 'final.wav')); fin = fin.T if fin.ndim > 1 else np.stack([fin, fin])
m, _ = sf.read(os.path.join(FD, 'music.wav')); m = m.T
fx, _ = sf.read(os.path.join(FD, 'fx.wav')); fx = fx.T
i0, i1 = int(a0 * SR), int(a1 * SR)
g = np.sqrt(np.mean(fin[:, i0:i1] ** 2)) / np.sqrt(np.mean((vchain(nar[i0:i1]) * fac) ** 2)) * 0.9
def say(text, speed=0.94, punch=0.2):
    y = librosa.resample(kk.create(text, voice=vec, speed=speed * (1 + 0.05 * punch), lang='en-us')[0].astype(np.float64), orig_sr=24000, target_sr=SR)
    nz = np.nonzero(np.abs(y) > 0.01 * np.abs(y).max())[0]; y = N.polish(y[max(0, nz[0] - 600): nz[-1] + 2400])
    y = y * (N.level(nar[int(sc['start'] * SR): int(sc['end'] * SR)]) / N.level(y))
    return vchain(y) * fac * g

parts = []
F = 0.0
if flash:
    A, B = (float(v) for v in flash.split(':'))
    hv = say(hook_say, 0.97, 0.6) if hook_say else np.zeros(1)
    F = max(B - A, 0.05 + len(hv) / SR + 0.3)
    ia, n = int(A * SR), int(F * SR)
    bed = m[:, ia:ia + n] * 0.62 + fx[:, ia:ia + n] * 0.8
    bed = bed * g * 10 ** (-4 / 20); k = int(0.15 * SR); bed[:, -k:] *= np.linspace(1, 0.6, k)
    if hook_say: bed[:, int(0.05 * SR):int(0.05 * SR) + len(hv)] += hv[:n - int(0.05 * SR)]
    parts.append(bed)
seg = fin[:, i0:i1].copy(); xf = int(0.25 * SR); seg[:, -xf:] *= np.linspace(1, 0.5, xf)
parts.append(seg)
lv = say(q_say)
pre, post = 0.3, 0.6; tail = pre + len(lv) / SR + post
qbed = m[:, i1:i1 + int(tail * SR)] * 0.62 * g * 10 ** (-6 / 20)
qpart = np.zeros((2, int(tail * SR))); qpart[:, :qbed.shape[1]] += qbed
qpart[:, int(pre * SR):int(pre * SR) + len(lv)] += lv
parts.append(qpart)
audio = np.concatenate(parts, 1)
end = audio.shape[1] / SR
k = int(0.12 * SR); audio[:, -k:] *= np.linspace(1, 0, k)                 # a hard cut back to the start
aw = os.path.join(work, 'audio.wav'); sf.write(aw, audio.T.astype(np.float32), SR, subtype='PCM_16')
cut = a1 - a0; qs = F + cut + pre

# ---- the picture: the scene again, without the film's captions and labels, covering the flash and the scene part
r0 = min(a0, A) if flash else a0
r1 = max(a1, (A + F) if flash else a1) + 0.1
clip = os.path.join(work, f'clean_{r0:.2f}_{r1:.2f}.mp4')
if not os.path.exists(clip):
    src = open(os.path.join(FD, 'film.html')).read()
    page = os.path.join(FD, '_vertical.html')
    open(page, 'w').write(src.replace('<script src="film.js"></script>', '<script>window.__vertical = true</script><script src="film.js"></script><script>window.__caps.length = 0</script>'))
    subprocess.run(['node', os.path.join(ROOT, 'studio', 'motion', 'render.mjs'), page, '--size', '1920x1080', '--from', f'{r0:.3f}', '--to', f'{r1:.3f}', '--workers', '2', '--out', clip, '--quiet'], check=True)
    os.remove(page)

# ---- captions
def ts(t): t = max(0, t); return f'{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}'
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
    fh.write('Style: K,Old Standard TT,128,&H00D2EAF4,&H00D2EAF4,&H00100C0A,&H96000000,-1,0,0,0,100,100,0,0,1,8,3,5,60,60,0,1\n')
    fh.write('Style: P,Old Standard TT,66,&H00F4EAD2,&H00F4EAD2,&H00100C0A,&H96000000,-1,0,0,0,100,100,0,0,1,6,2,5,70,70,0,1\n')
    fh.write('Style: Q,Old Standard TT,86,&H003A97C9,&H003A97C9,&H00100C0A,&H96000000,-1,0,0,0,100,100,0,0,1,7,2,5,70,70,0,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n')
    if flash and hook_show: fh.write(f'Dialogue: 0,{ts(0)},{ts(F)},K,,0,0,0,,{{\\pos(540,{hook_y})}}{hook_show}\n')
    fh.write(f'Dialogue: 0,{ts(F)},{ts(qs - 0.1)},H,,0,0,0,,{place}\n')
    for k2, (s_, e_, txt) in enumerate(caps):
        e2 = min(e_ + 0.3, caps[k2 + 1][0] - 0.05) if k2 + 1 < len(caps) else min(e_ + 0.3, cut)
        fh.write(f'Dialogue: 0,{ts(F + s_ - 0.04)},{ts(F + e2)},C,,0,0,0,,{txt}\n')
    fh.write(f'Dialogue: 0,{ts(qs - 0.1)},{ts(end)},Q,,0,0,0,,{{\\pos(540,820)}}{q_show}\n')
    if pointer: fh.write(f'Dialogue: 0,{ts(qs + 0.6)},{ts(end)},P,,0,0,0,,{{\\pos(540,1290)\\fad(200,0)}}FULL FILM: tap the link\\Nabove the title  ↓\n')

# ---- the 9:16 window: 608 x 1080 out of each 1920 x 1080 frame, scaled up to fill
keys = sorted((float(a), float(b)) for a, b in (p.split(':') for p in crop.split(',')))
def xexpr():
    if len(keys) == 1: return f'{keys[0][1] - 304:.1f}'
    e = f'{keys[-1][1] - 304:.1f}'
    for (ta, xa), (tb, xb) in reversed(list(zip(keys, keys[1:]))):
        e = f"if(lt(t,{tb:.3f}),{xa - 304:.1f}+({xb - xa:.1f})*(0.5-0.5*cos(PI*clip((t-{ta:.3f})/{max(tb - ta, 0.01):.3f},0,1))),{e})"
    return f"if(lt(t,{keys[0][0]:.3f}),{keys[0][1] - 304:.1f},{e})"
inputs, fc = [], []
if flash:
    inputs += ['-ss', f'{A - r0:.3f}', '-t', f'{F + 0.2:.3f}', '-i', clip]
    # the cold open: already moving, a slow push-in from the first frame
    fc.append(f"[0:v]trim=0:{F:.3f},setpts=PTS-STARTPTS,crop=608:1080:x={min(1312, max(0, flash_x - 304)):.1f}:y=0,scale=1080:1920:flags=lanczos,"
              f"zoompan=z='1.0+0.10*on/{int(F * 30)}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,setsar=1[f]")
mi = len(inputs) // 6
inputs += ['-ss', f'{a0 - r0:.3f}', '-i', clip]
fc.append(f"[{mi}:v]trim=0:{cut:.3f},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={tail + 0.1:.3f},"
          f"crop=608:1080:x='clip({xexpr()},0,1312)':y=0,scale=1080:1920:flags=lanczos,setsar=1,fps=30[m]")
fc.append(("[f][m]concat=n=2:v=1:a=0[v];" if flash else "[m]null[v];") + f"[v]subtitles='{ass}':fontsdir='{fonts}',format=yuv420p[o];[{mi + 1}:a]alimiter=limit=0.78:level=false[a]")
inputs += ['-i', aw]
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', *inputs, '-filter_complex', ';'.join(fc), '-map', '[o]', '-map', '[a]', '-t', f'{end:.3f}',
                '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-r', '30', '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', out], check=True)
print(out, round(end, 2), 's; flash', round(F, 2), '; scene part', round(a0, 2), '-', round(a1, 2), '; question at', round(qs, 2))
