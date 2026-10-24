"""Streamed finishing pass: raw RGBA frames on stdin (bottom-up, straight from the GPU) ->
   [grade] -> captions -> one final encode.
   python3 finish.py out.mp4 [--grade] [--w 1080 --h 1920]"""
import sys, subprocess, numpy as np, cv2
from ovl import overlay, W, H, FPS

GRADE = '--grade' in sys.argv
dst = sys.argv[1] if len(sys.argv) > 1 else None
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = (1 - 0.42 * ((((xx - W / 2) / (W * 0.7)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2) ** 1.2))[..., None].astype(np.float32)
# tone curve as a lookup table (same maths as before, done once)
_x = np.linspace(0, 1, 4096, dtype=np.float32)
CURVE = (_x + 0.12 * (_x - _x * _x) * (2 * _x - 1) * -1 + 0.18 * (_x * _x * (3 - 2 * _x) - _x)).astype(np.float32)
LUMW = np.array([[0.2126, 0.7152, 0.0722]], np.float32)
SPLIT_SH = np.array([-0.012, 0.012, 0.03], np.float32); SPLIT_HI = np.array([0.03, 0.01, -0.025], np.float32)
HAL = np.array([1.0, 0.35, 0.12], np.float32) * 0.9
rng = np.random.default_rng(1)


def grade(f8):
    f = f8.astype(np.float32) * (1 / 255)
    lum = cv2.transform(f, LUMW)                                    # HxW
    hot = np.clip(lum - 0.75, 0, None)
    small = cv2.resize(hot, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    hal = cv2.resize(cv2.GaussianBlur(small, (0, 0), 22 / 4), (W, H), interpolation=cv2.INTER_LINEAR)
    f += hal[..., None] * HAL
    sh = np.clip(1 - lum * 2, 0, 1)[..., None]; hi = np.clip(lum * 2 - 1, 0, 1)[..., None]
    f += sh * SPLIT_SH; f += hi * SPLIT_HI
    np.clip(f, 0, 1, out=f)
    f = CURVE[(f * 4095).astype(np.int32)]
    m = f.mean(2, keepdims=True); f *= 1.08; f -= m * 0.08
    f *= VIG
    g = cv2.resize(rng.standard_normal((H // 2, W // 2), dtype=np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    f += (g * (0.028 * (0.35 + 0.65 * np.clip(4 * lum * (1 - lum), 0, 1))))[..., None]
    return np.clip(f * 255, 0, 255).astype(np.uint8)


if __name__ == '__main__':
    enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-c:v', 'libx264', '-crf', '15' if GRADE else '16', '-pix_fmt', 'yuv420p', dst], stdin=subprocess.PIPE)
    src = sys.stdin.buffer
    i = 0
    n = W * H * 4
    while True:
        b = src.read(n)
        if len(b) < n:
            break
        fr = np.frombuffer(b, np.uint8).reshape(H, W, 4)[::-1, :, :3]
        if GRADE:
            fr = grade(fr)
        enc.stdin.write(overlay(fr, i / FPS).tobytes()); i += 1
    enc.stdin.close(); enc.wait()
    print('finished', i, 'frames', file=sys.stderr)
