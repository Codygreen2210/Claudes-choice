"""Swap re-rendered frames into a finished shot.   python3 splice.py SHOT.mp4 REDODIR redo.json OUT.mp4
redo.json {frames, jobs, ch}: redo job r (REDODIR/clip_<r*ch>.mp4) holds frames[r::jobs] in order."""
import sys, json, subprocess
shot, rd, rj, out = sys.argv[1:5]; R = json.load(open(rj)); FR, J, CH = R['frames'], R['jobs'], R['ch']
pr = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,nb_read_frames', '-of', 'json', shot]))['streams'][0]
W, H, N = pr['width'], pr['height'], int(pr['nb_read_frames']); n = W * H * 3
def reader(p): return subprocess.Popen(['ffmpeg', '-v', 'error', '-threads', '1', '-i', p, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
src = reader(shot); clips = {r: reader(f'{rd}/clip_{r * CH:05d}.mp4') for r in range(J)}; job = {f: k % J for k, f in enumerate(FR)}
enc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30', '-i', '-',
                       '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-threads', '2', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
for f in range(N):
    b = src.stdout.read(n)
    if f in job: b = clips[job[f]].stdout.read(n)
    assert len(b) == n, f'ran out at frame {f}'
    enc.stdin.write(b)
enc.stdin.close(); enc.wait(); print(N, 'frames,', len(FR), 'swapped')
