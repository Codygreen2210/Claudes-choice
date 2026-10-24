"""Comparison reel: a title card before each 5-second sample."""
import subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
W, H = 1080, 1920
BLACK = '/usr/share/fonts/opentype/inter/Inter-Black.otf'
CARDS = [
    ('s0_baseline.mp4', 'BASELINE', 'What we make now', ['Picture: 2D shapes, side view', 'Sound: synth effects + score']),
    ('s1_handdrawn.mp4', 'LEVEL 1', 'Hand-drawn rig', ['Picture: jointed skeleton, ink lines,', 'painted crater, look-up tunnel shot', 'Sound: real foley, crater echo,', 'wind tied to his fall speed']),
    ('s2_3d.mp4', 'LEVEL 2', 'Real 3D', ['Picture: sculpted crater, lava shader,', '3D guy, lava light, 3 camera angles', 'Sound: binaural 3D placement,', 'doppler, distance (use headphones)']),
    ('s3_cinematic.mp4', 'LEVEL 3', 'Cinematic', ['Picture: simulated lava, slow-mo boot', 'close-up, depth of field, motion blur', 'Sound: original score, built rock + lava', 'sounds, slow-mo audio, mastered']),
]
def card(big, sub, lines, path):
    im = Image.new('RGB', (W, H), (14, 10, 18)); d = ImageDraw.Draw(im)
    f1 = ImageFont.truetype(BLACK, 150); f2 = ImageFont.truetype(BLACK, 84); f3 = ImageFont.truetype(BLACK, 48)
    def c(txt, y, f, col):
        d.text(((W - d.textlength(txt, font=f)) / 2, y), txt, font=f, fill=col)
    c(big, 620, f1, (255, 236, 80)); c(sub, 810, f2, (255, 255, 255))
    for k, ln in enumerate(lines):
        c(ln, 1000 + k * 70, f3, (200, 190, 210))
    im.save(path)
parts = []
for i, (clip, big, sub, lines) in enumerate(CARDS):
    png = f'card{i}.png'; card(big, sub, lines, png)
    cm = f'card{i}.mp4'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-t', '1.8', '-i', png, '-f', 'lavfi', '-t', '1.8', '-i', 'anullsrc=r=44100:cl=stereo',
                    '-vf', 'fps=30,format=yuv420p,fade=t=in:st=0:d=0.25', '-c:v', 'libx264', '-crf', '18', '-c:a', 'aac', '-shortest', cm], check=True)
    parts += [cm, clip]
inp = sum([['-i', p] for p in parts], [])
fc = ''.join(f'[{k}:v]scale=1080:1920,setsar=1,fps=30,format=yuv420p[v{k}];[{k}:a]aresample=44100,aformat=channel_layouts=stereo[a{k}];' for k in range(len(parts)))
fc += ''.join(f'[v{k}][a{k}]' for k in range(len(parts))) + f'concat=n={len(parts)}:v=1:a=1[v][a]'
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', *inp, '-filter_complex', fc, '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p',
                '-c:a', 'aac', '-b:a', '192k', 'style-samples-reel.mp4'], check=True)
print('reel done')
