#!/usr/bin/env python3
"""Put a strided farm render back in order.  python3 unstride.py FARM_DIR stride.json OUT.mp4
Job j rendered frames j, j+J, j+2J ... into clip_<j*ch>.mp4 (see ele.py --stride). Each clip's frames get their real times back
(setpts) and ffmpeg's interleave filter merges them in time order, in one pass (no PNGs on disk)."""
import sys, json, glob, os, subprocess
farm, sj, out = sys.argv[1:4]
st = json.load(open(sj)); J, CH = st['jobs'], st['ch']
clips = sorted(glob.glob(os.path.join(farm, 'clip_*.mp4')), key=lambda p: int(os.path.basename(p)[5:10]))
assert len(clips) == J, f'{len(clips)} clips, expected {J}'
args, fl = [], []
for k, c in enumerate(clips):
    job = int(os.path.basename(c)[5:10]) // CH; args += ['-i', c]
    fl.append(f'[{k}:v]setpts=({job}+N*{J})/30/TB[v{k}]')
fl.append(''.join(f'[v{k}]' for k in range(len(clips))) + f'interleave=nb_inputs={len(clips)}[o]')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error'] + args + ['-filter_complex', ';'.join(fl), '-map', '[o]', '-fps_mode', 'cfr',
                '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-r', '30', out], check=True)
n = int(subprocess.check_output(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', out]))
print('unstrided', n, 'frames ->', out)
