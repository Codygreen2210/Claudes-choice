"""Level 3 finishing: grade (teal shadows / warm highlights, S-curve), halation, vignette, film grain, captions."""
import sys, subprocess, numpy as np, cv2
from ovl import overlay, W, H, FPS
src, dst = sys.argv[1], sys.argv[2]
dec = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-i', src, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-c:v', 'libx264', '-crf', '15', '-pix_fmt', 'yuv420p', dst], stdin=subprocess.PIPE)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = (1 - 0.42 * ((((xx - W / 2) / (W * 0.7)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2) ** 1.2))[..., None]
rng = np.random.default_rng(1)
i = 0
while True:
    b = dec.stdout.read(W * H * 3)
    if len(b) < W * H * 3: break
    f = np.frombuffer(b, np.uint8).reshape(H, W, 3).astype(np.float32) / 255
    lum = f @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    # halation: hot areas bleed a red glow into the film
    hot = np.clip(lum - 0.75, 0, None)
    hal = cv2.GaussianBlur(hot, (0, 0), 22)[..., None] * np.array([1.0, 0.35, 0.12], np.float32) * 0.9
    f = f + hal
    # split tone + S-curve
    sh = np.clip(1 - lum * 2, 0, 1)[..., None]; hi = np.clip(lum * 2 - 1, 0, 1)[..., None]
    f = f + sh * np.array([-0.012, 0.012, 0.03], np.float32) + hi * np.array([0.03, 0.01, -0.025], np.float32)
    f = np.clip(f, 0, 1)
    f = f + 0.12 * (f - f * f) * (2 * f - 1) * -1 + 0.18 * (f * f * (3 - 2 * f) - f)
    m = f.mean(2, keepdims=True); f = m + (f - m) * 1.08
    f = f * VIG
    # grain: finer in the brights, heavier in the mids
    g = cv2.resize(rng.standard_normal((H // 2, W // 2)).astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    f = f + g[..., None] * 0.028 * (0.35 + 0.65 * np.clip(4 * lum * (1 - lum), 0, 1))[..., None]
    fr = np.clip(f * 255, 0, 255).astype(np.uint8)
    enc.stdin.write(overlay(fr, i / FPS).tobytes()); i += 1
enc.stdin.close(); enc.wait(); print('frames', i)
