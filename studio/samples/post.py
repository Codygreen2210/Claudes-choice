"""Add hook + captions to a rendered picture: python3 post.py in.mp4 out.mp4"""
import sys, subprocess, numpy as np
from ovl import overlay, W, H, FPS
src, dst = sys.argv[1], sys.argv[2]
dec = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-i', src, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', dst], stdin=subprocess.PIPE)
i = 0
while True:
    b = dec.stdout.read(W * H * 3)
    if len(b) < W * H * 3: break
    fr = np.frombuffer(b, np.uint8).reshape(H, W, 3)
    enc.stdin.write(overlay(fr, i / FPS).tobytes()); i += 1
enc.stdin.close(); enc.wait(); print('frames', i)
