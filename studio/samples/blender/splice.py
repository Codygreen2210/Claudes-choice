"""Swap re-rendered frames into a finished shot (no full re-render): frames from a redo farm run replace the same frames in shot.mp4.
    python3 splice.py SHOT.mp4 REDO_FARM_DIR redo.json OUT.mp4
redo.json: {"frames": [...], "jobs": J, "ch": C}; job j's clip (clip_<j*C>.mp4) holds frames[j::J] in order."""
import sys, json, subprocess
import numpy as np
shot, farm, rj, out = sys.argv[1:5]
R = json.load(open(rj)); FR, J, CH = R['frames'], R['jobs'], R['ch']
where = {f: k % J for k, f in enumerate(FR)}
W, H = map(int, subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', shot], text=True).strip().split(','))
n = W * H * 3
def reader(p): return subprocess.Popen(['ffmpeg', '-v', 'error', '-i', p, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
src = reader(shot); clips = {j: reader(f'{farm}/clip_{j * CH:05d}.mp4') for j in range(J)}
enc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30', '-i', '-',
                        '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
f = 0; swapped = 0
while True:
    b = src.stdout.read(n)
    if len(b) < n: break
    if f in where:
        nb = clips[where[f]].stdout.read(n)
        assert len(nb) == n, f'clip for job {where[f]} ran out at frame {f}'
        b = nb; swapped += 1
    enc.stdin.write(b); f += 1
enc.stdin.close(); enc.wait(); print(f'{f} frames, {swapped} swapped (wanted {len(FR)})')
