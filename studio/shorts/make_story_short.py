#!/usr/bin/env python3
"""make_story_short.py: a vertical Short (1080x1920) that tells one complete scene from a story film.

    python3 make_story_short.py <film> <master.mp4> <scene> "<HOOK 1>" "<HOOK 2>" "<question, spoken>" "<question, on screen>" <out.mp4> [--clip pre-cut.mp4]

What it does (lessons from the Oct 2026 YouTube research):
  - opens on the scene's first line, no title card or date, so the first second is already story;
  - plays one whole scene with its own turn and ending, not a teaser of the film's opening;
  - ends on one question the full film answers, said by the studio voice over a held, dimmed last frame;
  - large word-timed captions under the picture, hook above, all clear of the Shorts buttons.
--clip: a render of just this scene (from --from/--to), used when the master predates a fix to the drawing kit.
"""
import json, os, re, subprocess, sys, warnings
warnings.filterwarnings('ignore')
import numpy as np, soundfile as sf, librosa, pyloudnorm as pyln
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
sys.path.insert(0, ROOT)
from studio.instruments import synth as S

args = [a for a in sys.argv[1:]]
clip = None
if '--clip' in args: k = args.index('--clip'); clip = args[k + 1]; del args[k:k + 2]
film, master, si, h1, h2, q_say, q_show, out = args[:8]; si = int(si)
FD = os.path.join(HERE, '..', 'works', film); sys.path.insert(0, FD)
import narrate as N
T = json.load(open(os.path.join(FD, 'timing.json')))['scenes']; sc = T[si]
a0 = sc['start'] - 0.05                                                     # just after the dissolve into the scene
a1 = min(T[si + 1]['start'] - 0.5, sc['end'] + 1.1) if si + 1 < len(T) else sc['end'] + 1.1
work = f'/home/claude/work/story-short-{film}'; os.makedirs(work, exist_ok=True)
SR = S.SR

# ---- the closing question, in the film's own voice and level
from kokoro_onnx import Kokoro
M = '/home/claude/work/kokoro'
kk = Kokoro(os.path.join(M, 'kokoro-v1.0.onnx'), os.path.join(M, 'voices-v1.0.bin'))
vec = 0.75 * kk.get_voice_style('am_michael') + 0.25 * kk.get_voice_style('am_eric')
line = librosa.resample(kk.create(q_say, voice=vec, speed=0.94 * (1 - 0.05 * 0.4), lang='en-us')[0].astype(np.float64), orig_sr=24000, target_sr=SR)
nz = np.nonzero(np.abs(line) > 0.01 * np.abs(line).max())[0]; line = line[max(0, nz[0] - 800): nz[-1] + 2400]
line = N.polish(line)
nar, _ = sf.read(os.path.join(FD, 'narration.wav'))
if nar.ndim > 1: nar = nar.mean(1)
line = line * (N.level(nar[int(sc['start'] * SR): int(sc['end'] * SR)]) / N.level(line))
meter = pyln.Meter(SR)
vchain = lambda v: S.eq(S.hp(v, 70, 2)[None, :], [('peak', 220, -1.5, 1.0)])[0]
fac = 10 ** ((-17 - meter.integrated_loudness(vchain(nar))) / 20)
fin, _ = sf.read(os.path.join(FD, 'final.wav')); fin = fin.T if fin.ndim > 1 else np.stack([fin, fin])
i0, i1 = int(a0 * SR), int(a1 * SR)
vseg = vchain(nar[i0:i1]) * fac
g = np.sqrt(np.mean(fin[:, i0:i1] ** 2)) / np.sqrt(np.mean(vseg ** 2)) * 0.84          # the master's gain (a touch under, so the question sits level with the scene), voice-dominated stretch
lv = vchain(line) * fac * g
# the music under it: the film's own bed, carried on past the cut, ducked under the question
m, _ = sf.read(os.path.join(FD, 'music.wav')); f, _ = sf.read(os.path.join(FD, 'fx.wav'))
pre, post = 0.45, 1.9; tail = pre + len(lv) / SR + post
j0, j1 = i1, i1 + int(tail * SR)
bed = (m[j0:j1].T * 0.62 + f[j0:j1].T * 0.8)
tt = np.arange(bed.shape[1]) / SR
duck = 10 ** (-5 * np.clip(np.minimum((tt - pre + 0.3) / 0.3, (pre + len(lv) / SR + 0.4 - tt) / 0.4), 0, 1) / 20)
bed = bed * duck * g
xf = int(0.3 * SR); seg = fin[:, i0:i1].copy(); seg[:, -xf:] *= np.linspace(1, 0, xf); bed[:, :xf] *= np.linspace(0, 1, xf)
audio = np.concatenate([seg, np.zeros((2, bed.shape[1]))], 1)
audio[:, seg.shape[1] - xf: seg.shape[1] - xf + bed.shape[1]] += bed[:, :audio.shape[1] - (seg.shape[1] - xf)]
q0 = seg.shape[1] - xf + int(pre * SR); audio[:, q0:q0 + len(lv)] += lv
end = audio.shape[1] / SR - xf / SR
audio = audio[:, :int(end * SR)]
fo = int(1.2 * SR); audio[:, -fo:] *= np.linspace(1, 0, fo) ** 1.5
aw = os.path.join(work, 'audio.wav'); sf.write(aw, audio.T.astype(np.float32), SR, subtype='PCM_16')
cut = a1 - a0; qs = (q0 / SR); qe = qs + len(lv) / SR

# ---- the frame everything sits on
html = f"""<!doctype html><meta charset="utf-8"><style>
@font-face{{font-family:Playfair;src:url(../works/{film}/fonts/Playfair.ttf);font-weight:400 900}}
@font-face{{font-family:PlayfairI;src:url(../works/{film}/fonts/Playfair-Italic.ttf);font-weight:400 900}}
html,body{{margin:0;background:#000}}canvas{{display:block}}</style><canvas id="cv" width="1080" height="1920"></canvas><script>
const c = document.getElementById('cv').getContext('2d')
const fit = (s, px, max) => {{ c.font = `900 ${{px}}px Playfair`; const w = c.measureText(s).width; return w > max ? px * max / w : px }}
window.__duration = 1
window.__init = async () => {{ await Promise.all(['900 40px Playfair', '700 40px PlayfairI'].map(f => document.fonts.load(f))) }}
window.__seek = () => {{
  const g = c.createRadialGradient(540, 900, 100, 540, 900, 1300); g.addColorStop(0, '#2a2119'); g.addColorStop(1, '#0c0a08'); c.fillStyle = g; c.fillRect(0, 0, 1080, 1920)
  c.textAlign = 'center'
  let p = fit({json.dumps(h1)}, 170, 940); c.font = `900 ${{p}}px Playfair`; c.fillStyle = '#f4ead2'; c.fillText({json.dumps(h1)}, 540, 390)
  p = fit({json.dumps(h2)}, 130, 940); c.font = `900 ${{p}}px Playfair`; c.fillStyle = '#e2452f'; c.fillText({json.dumps(h2)}, 540, 390 + p * 1.12)
  c.fillStyle = '#c9973a'; c.fillRect(60, 588, 960, 4); c.fillRect(60, 1216, 960, 4)
  c.font = '700 52px PlayfairI'; c.fillStyle = '#c9973a'; c.fillText('Full story on the channel', 500, 1500)
}}
</script>"""
page = os.path.join(HERE, f'_{film}_story.html'); open(page, 'w').write(html)
subprocess.run(['node', os.path.join(HERE, '..', 'motion', 'render.mjs'), page, '--size', '1080x1920', '--shots', '0', '--outdir', work], check=True, stdout=subprocess.DEVNULL)
os.remove(page); bg = os.path.join(work, 't000.00.png')

# ---- captions: the scene's words, then the question large over the held frame
def ts(t): t = max(0, t); return f'{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}'
W = [w for w in sc['words'] if w['s'] >= a0 - 0.01 and w['e'] <= a1 + 0.2]
caps, cur = [], []
for i, w in enumerate(W):
    cur.append(w); txt = ' '.join(x['w'] for x in cur); nxt = W[i + 1] if i + 1 < len(W) else None
    gap = nxt['s'] - w['e'] if nxt else 9
    if re.search(r'[.?!…]["”]?$', w['w']) or gap > 0.4 or len(txt) > 20 or (nxt and len(txt + ' ' + nxt['w']) > 27): caps.append((cur[0]['s'] - a0, cur[-1]['e'] - a0, txt)); cur = []
if cur: caps.append((cur[0]['s'] - a0, cur[-1]['e'] - a0, ' '.join(x['w'] for x in cur)))
ass = os.path.join(work, 'caps.ass')
with open(ass, 'w') as fh:
    fh.write('[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 2\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n')
    fh.write('Style: C,Old Standard TT,74,&H00D2EAF4,&H00D2EAF4,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,8,40,40,1268,1\n')
    fh.write('Style: Q,Old Standard TT,70,&H003A97C9,&H003A97C9,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,5,60,60,0,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n')
    for k, (s_, e_, txt) in enumerate(caps):
        e2 = min(e_ + 0.3, caps[k + 1][0] - 0.09) if k + 1 < len(caps) else min(e_ + 0.3, cut)
        fh.write(f'Dialogue: 0,{ts(s_ - 0.05)},{ts(e2)},C,,0,0,0,,{txt}\n')
    fh.write(f'Dialogue: 0,{ts(qs - 0.1)},{ts(end)},Q,,0,0,0,,{{\\pos(540,904)\\fad(250,0)}}{q_show}\n')

# ---- picture + sound
fonts = os.path.join(FD, 'fonts')
src = ['-i', clip] if clip else ['-ss', f'{a0:.3f}', '-i', master]
vf = (f"[1:v]trim=0:{cut:.3f},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={end - cut + 0.1:.3f},scale=1080:608:flags=lanczos,"
      f"drawbox=x=0:y=0:w=1080:h=608:color=black@0.84:t=fill:enable='gte(t,{cut:.3f})'[v];"
      f"[0:v][v]overlay=0:600:shortest=1,subtitles='{ass}':fontsdir='{fonts}',fade=t=in:st=0:d=0.15,fade=t=out:st={end - 0.4:.3f}:d=0.4,format=yuv420p[o];"
      f"[2:a]volume=-0.6dB,alimiter=limit=0.84:level=false[a]")
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-framerate', '30', '-t', f'{end:.3f}', '-i', bg, *src, '-i', aw,
                '-filter_complex', vf, '-map', '[o]', '-map', '[a]', '-t', f'{end:.3f}', '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-r', '30',
                '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', out], check=True)
print(out, round(end, 2), 's; scene', si, round(a0, 2), '-', round(a1, 2), '; question at', round(qs, 2))
