#!/usr/bin/env python3
"""Drop a farm redo render (redo.json: frames, jobs, ch) back into a finished shot.
   python3 redo_splice.py SHOT.mp4 FARM_DIR redo.json OUT.mp4
Job j rendered frames[j::jobs] into clip_<j*ch>.mp4, in order; every other frame comes from SHOT.mp4. Streams, nothing on disk."""
import sys, json, glob, os, subprocess
shot, farm, rj, out = sys.argv[1:5]
R = json.load(open(rj)); J, CH, FR = R['jobs'], R['ch'], R['frames']
w, h, n = subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_frames', '-show_entries',
                                   'stream=width,height,nb_read_frames', '-of', 'csv=p=0', shot]).decode().strip().split(',')
w, h, n = int(w), int(h), int(n); fs = w * h * 3
src = {}
for j in range(J):
    for k, f in enumerate(FR[j::J]): src[f] = j
for j in range(J): assert os.path.exists(os.path.join(farm, f'clip_{j * CH:05d}.mp4')), f'missing clip for job {j}'
rd = lambda p: subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-i', p, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-'], stdout=subprocess.PIPE)
base = rd(shot); clips = {j: rd(os.path.join(farm, f'clip_{j * CH:05d}.mp4')) for j in range(J)}
enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-r', '30', '-i', '-',
                        '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
swapped = 0
for f in range(n):
    b = base.stdout.read(fs)
    if f in src:
        b = clips[src[f]].stdout.read(fs); assert len(b) == fs, f'clip for job {src[f]} ran short at frame {f}'; swapped += 1
    enc.stdin.write(b)
enc.stdin.close(); enc.wait()
print(f'spliced {swapped} of {len(FR)} redo frames into {n} -> {out}')
