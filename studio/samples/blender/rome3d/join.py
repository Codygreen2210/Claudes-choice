"""Interleave a stride farm run back into one shot.   python3 join.py OUTDIR N J CH OUT.mp4
OUTDIR/clip_<j*CH>.mp4 holds frames j, j+J, j+2J, ... (J stride jobs)."""
import sys, subprocess, json
d, N, J, CH, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
pr = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'json', f'{d}/clip_00000.mp4']))['streams'][0]
W, H = pr['width'], pr['height']; n = W * H * 3
def reader(p): return subprocess.Popen(['ffmpeg', '-v', 'error', '-threads', '1', '-i', p, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
clips = [reader(f'{d}/clip_{j * CH:05d}.mp4') for j in range(J)]
enc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30', '-i', '-',
                       '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-threads', '2', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
for f in range(N):
    b = clips[f % J].stdout.read(n); assert len(b) == n, f'ran out at frame {f} (job {f % J})'
    enc.stdin.write(b)
enc.stdin.close(); enc.wait(); print(N, 'frames', W, 'x', H)
