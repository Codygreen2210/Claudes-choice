#!/usr/bin/env python3
"""make_short.py <film> <master.mp4> "<HOOK LINE 1>" "<HOOK LINE 2>" <out.mp4>

Cuts a vertical Short (1080x1920) from a story film's opening scene: the wide picture sits whole in the middle,
the hook above it, large word-timed captions under it, and one line pointing at the full film.
Everything stays clear of the Shorts buttons (right 140 px, bottom 380 px).
"""
import json, os, subprocess, sys, re
film, master, h1, h2, out = sys.argv[1:6]
HERE = os.path.dirname(os.path.abspath(__file__)); FD = os.path.join(HERE, '..', 'works', film)
T = json.load(open(os.path.join(FD, 'timing.json')))['scenes']
cut = T[1]['start'] - 0.45; end = cut + 1.2; last = T[0]['end']
work = f'/home/claude/work/short-{film}'; os.makedirs(work, exist_ok=True)

# 1. the still frame everything sits on
html = f"""<!doctype html><meta charset="utf-8"><style>
@font-face{{font-family:Playfair;src:url(../works/{film}/fonts/Playfair.ttf);font-weight:400 900}}
@font-face{{font-family:PlayfairI;src:url(../works/{film}/fonts/Playfair-Italic.ttf);font-weight:400 900}}
html,body{{margin:0;background:#000}}canvas{{display:block}}</style><canvas id="cv" width="1080" height="1920"></canvas><script>
const c = document.getElementById('cv').getContext('2d')
const fit = (s, px, max, font) => {{ c.font = `900 ${{px}}px ${{font}}`; const w = c.measureText(s).width; return w > max ? px * max / w : px }}
window.__duration = 1
window.__init = async () => {{ await Promise.all(['900 40px Playfair', '700 40px PlayfairI'].map(f => document.fonts.load(f))) }}
window.__seek = () => {{
  const g = c.createRadialGradient(540, 900, 100, 540, 900, 1300); g.addColorStop(0, '#2a2119'); g.addColorStop(1, '#0c0a08'); c.fillStyle = g; c.fillRect(0, 0, 1080, 1920)
  c.textAlign = 'center'; c.textBaseline = 'alphabetic'
  let p = fit({json.dumps(h1)}, 170, 940, 'Playfair'); c.font = `900 ${{p}}px Playfair`; c.fillStyle = '#f4ead2'; c.fillText({json.dumps(h1)}, 540, 390)
  p = fit({json.dumps(h2)}, 130, 940, 'Playfair'); c.font = `900 ${{p}}px Playfair`; c.fillStyle = '#e2452f'; c.fillText({json.dumps(h2)}, 540, 390 + p * 1.12)
  c.fillStyle = '#c9973a'; c.fillRect(60, 588, 960, 4); c.fillRect(60, 1216, 960, 4)
  c.font = '700 52px PlayfairI'; c.fillStyle = '#c9973a'; c.fillText('Full story on the channel', 500, 1500)
}}
</script>"""
page = os.path.join(HERE, f'_{film}.html'); open(page, 'w').write(html)
subprocess.run(['node', os.path.join(HERE, '..', 'motion', 'render.mjs'), page, '--size', '1080x1920', '--shots', '0', '--outdir', work], check=True, stdout=subprocess.DEVNULL)
os.remove(page); bg = os.path.join(work, 't000.00.png')

# 2. captions: short lines, broken where the voice breaks
def ts(t): t = max(0, t); return f'{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}'
caps, cur = [], []
W = T[0]['words']
for i, w in enumerate(W):
    cur.append(w); txt = ' '.join(x['w'] for x in cur); nxt = W[i + 1] if i + 1 < len(W) else None
    gap = nxt['s'] - w['e'] if nxt else 9
    if re.search(r'[.?!…]["”]?$', w['w']) or gap > 0.4 or len(txt) > 20 or (nxt and len(txt + ' ' + nxt['w']) > 27): caps.append((cur[0]['s'], cur[-1]['e'], txt)); cur = []
if cur: caps.append((cur[0]['s'], cur[-1]['e'], ' '.join(x['w'] for x in cur)))
ass = os.path.join(work, 'caps.ass')
with open(ass, 'w') as f:
    f.write('[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 2\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n')
    f.write('Style: C,Old Standard TT,74,&H00D2EAF4,&H00D2EAF4,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,8,40,40,1268,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n')
    for k, (s, e, txt) in enumerate(caps):
        e2 = min(e + 0.3, caps[k + 1][0] - 0.09) if k + 1 < len(caps) else e + 0.3
        f.write(f'Dialogue: 0,{ts(s - 0.05)},{ts(e2)},C,,0,0,0,,{txt}\n')

# 3. picture + sound
fonts = os.path.join(FD, 'fonts')
vf = (f"[1:v]trim=0:{cut:.3f},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=1.2,scale=1080:608:flags=lanczos[v];"
      f"[0:v][v]overlay=0:600:shortest=1,subtitles='{ass}':fontsdir='{fonts}',fade=t=in:st=0:d=0.3,fade=t=out:st={end - 0.35:.3f}:d=0.35,format=yuv420p[o];"
      f"[2:a]atrim=0:{end:.3f},afade=t=out:st={last + 0.25:.3f}:d={max(0.4, cut + 0.4 - last - 0.25):.3f},volume=-0.6dB,alimiter=limit=0.84:level=false[a]")
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-framerate', '30', '-t', f'{end:.3f}', '-i', bg, '-i', master, '-i', os.path.join(FD, 'final.wav'),
                '-filter_complex', vf, '-map', '[o]', '-map', '[a]', '-t', f'{end:.3f}', '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-r', '30', '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', out], check=True)
print(out, round(end, 2), 's', len(caps), 'captions')
