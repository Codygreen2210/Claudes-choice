"""Join a stride farm run where some jobs were cut off, plus the redo run for their missing frames, into one shot.
    python3 assemble.py FARMDIR partial.json REDODIR redo.json N OUT.mp4
FARMDIR/clip_<j*100>.mp4 holds frames j, j+20, ... (20 jobs). partial.json {start: frames kept}; for those jobs the
last kept frame and everything after come from the redo run (redo job r = frames[r::J])."""
import sys, json, subprocess
farm, pj, redo_dir, rj, N, out = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]), sys.argv[6]
part = {int(k) // 100: v for k, v in json.load(open(pj)).items()}; R = json.load(open(rj)); FR, RJ, RCH = R['frames'], R['jobs'], R['ch']
redo_of = {f: k % RJ for k, f in enumerate(FR)}
W, H = 1920, 1080; n = W * H * 3
def reader(p): return subprocess.Popen(['ffmpeg', '-v', 'error', '-threads', '1', '-i', p, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
clips = {j: reader(f'{farm}/clip_{j * 100:05d}.mp4') for j in range(20)}; rclips = {r: reader(f'{redo_dir}/clip_{r * RCH:05d}.mp4') for r in range(RJ)}
enc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30', '-i', '-',
                       '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-threads', '2', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
used = 0
for f in range(N):
    j, k = f % 20, f // 20
    if f in redo_of:
        b = rclips[redo_of[f]].stdout.read(n); used += 1
        if j in part and k < part[j]: clips[j].stdout.read(n)        # skip the farm copy of a frame we're redoing
    else: b = clips[j].stdout.read(n)
    assert len(b) == n, f'ran out at frame {f} (job {j})'
    enc.stdin.write(b)
enc.stdin.close(); enc.wait(); print(N, 'frames,', used, 'from the redo run')
