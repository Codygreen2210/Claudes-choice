"""editcheck.py: score a finished film's edit out of 100. Pass = 80+. Rules: docs/editing-rules.md.

Reads the rendered video: finds the cuts (ffmpeg scene detection), measures shot lengths, and checks
the soundtrack against the cuts (J/L cuts, silence before the climax, pillow shot after it, cold open,
ending hold). POV push-through hand-offs often aren't detected as cuts; that's fine, they are meant to
read as one shot.

  python3 studio/senses/editcheck.py film.mp4 [--climax 330] [--scene-thresh 0.32] [--out notes/]
--climax: seconds of the film's biggest moment. Without it, the loudest 3-second stretch is used.
"""
import argparse, json, os, re, subprocess
import numpy as np


def cuts_of(video, thresh):
    p = subprocess.run(['ffmpeg', '-hide_banner', '-i', video, '-vf', f"scale=320:-2,select='gt(scene,{thresh})',showinfo", '-an', '-f', 'null', '-'],
                       capture_output=True, text=True)
    return [float(m) for m in re.findall(r'pts_time:([\d.]+)', p.stderr)]


def duration(video):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', video]).decode().strip())


def audio_env(video, sr=8000, hop=0.05):
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', video, '-vn', '-ac', '1', '-ar', str(sr), '-f', 's16le', '-'])
    a = np.frombuffer(raw, np.int16).astype(np.float64) / 32768
    n = int(sr * hop); k = len(a) // n
    rms = np.sqrt((a[:k * n].reshape(k, n) ** 2).mean(1) + 1e-12)
    return 20 * np.log10(rms + 1e-9), hop


def ramp(v, bad, good):
    return float(min(1, max(0, (v - bad) / (good - bad))))


def check(video, climax=None, thresh=0.32):
    dur = duration(video)
    cuts = [c for c in cuts_of(video, thresh) if 0.3 < c < dur - 0.3]
    bounds = [0.0] + cuts + [dur]
    shots = np.diff(bounds)
    db, hop = audio_env(video)
    t = np.arange(len(db)) * hop
    sm = np.convolve(db, np.ones(60) / 60, mode='same')  # 3 s loudness
    if climax is None: climax = float(t[np.argmax(sm[: int(len(sm) * 0.92)])])
    R = []

    asl = float(np.median(shots))
    R.append(('Shot length (median)', 10 * min(ramp(asl, 12, 8), ramp(asl, 1.5, 3)), 10, f'{asl:.1f} s median over {len(shots)} shots (want 3-8 s)'))
    cv = float(shots.std() / shots.mean())
    R.append(('Rhythm varies', 10 * ramp(cv, 0.2, 0.5), 10, f'variation {cv:.2f} (want 0.5+, not a slideshow)'))
    long = [(round(b, 1), round(s, 1)) for b, s in zip(bounds, shots) if s > 15]
    R.append(('No dead holds', 10 * ramp(-len(long), -4, 0), 10, f'{len(long)} shots over 15 s {long[:4]} (each must move; zero is safest)'))
    flash = int((shots < 0.5).sum())
    R.append(('No flash frames', 5 * ramp(-flash, -3, 0), 5, f'{flash} shots under 0.5 s'))

    open_s = shots[[i for i, b in enumerate(bounds[:-1]) if b < dur * 0.3]]
    clim_s = shots[[i for i, b in enumerate(bounds[:-1]) if abs(b - climax) < 45]]
    speed = (open_s.mean() / clim_s.mean()) if len(open_s) and len(clim_s) else 1
    R.append(('Faster at the climax', 10 * ramp(speed, 1.0, 1.3), 10, f'climax cuts {speed:.2f}x faster than the opening (want 1.3x+)'))

    # J/L cuts: did the sound change near the cut, but not on it?
    d = np.abs(np.diff(sm[::2]))  # loudness change per 0.1 s
    jl = hard = 0
    for c in cuts:
        i = int(c / (hop * 2))
        if i < 25 or i > len(d) - 25: continue
        near = d[i - 20:i + 20]; at = d[i - 1:i + 2].max()
        peak = int(np.argmax(near)) - 20
        if near.max() < 0.6: continue  # sound didn't change much at all: a carried bed, counts as L
        if abs(peak) <= 1: hard += 1
        elif 4 <= abs(peak) <= 20: jl += 1
    flat = len(cuts) - jl - hard
    share = (jl + flat * 0.5) / max(1, len(cuts))
    R.append(('J and L cuts', 15 * ramp(share, 0.1, 0.3), 15, f'{jl} J/L, {hard} hard, {flat} carried beds over {len(cuts)} cuts (want 30%+ J/L)'))

    ci = int(climax / hop)
    before = db[max(0, ci - 80):ci]  # 4 s before
    drop = float(np.median(db[max(0, ci - 400):max(1, ci - 100)]) - before.min()) if len(before) else 0
    R.append(('Silence before the hit', 10 * ramp(drop, 3, 10), 10, f'{drop:.1f} dB dip in the 4 s before {climax:.0f} s (want 10+)'))

    after = [(b, s) for b, s in zip(bounds, shots) if climax + 2 < b < climax + 90 and s >= 4]
    quiet = any(np.median(db[int(b / hop):int((b + s) / hop)]) < np.median(db) - 4 for b, s in after)
    R.append(('Pillow shot after', 10 if quiet else (5 if after else 0), 10, 'a 4 s+ quiet hold within 90 s after the climax'))

    first_sound = float(t[np.argmax(db > np.median(db) - 15)])
    first_cut = cuts[0] if cuts else dur
    cold = (first_sound < 0.5) + (first_cut < 15)
    R.append(('Cold open', 5 * cold, 10, f'sound starts {first_sound:.1f} s, first cut {first_cut:.1f} s (want <0.5 s and <15 s)'))
    R[-1] = (R[-1][0], R[-1][1], 10, R[-1][3])
    endhold = shots[-1]
    R.append(('Ending holds', 5 * ramp(endhold, 1.5, 3), 5, f'last shot {endhold:.1f} s (want 3+)'))
    total = sum(r[1] for r in R)
    return total, R, {'cuts': cuts, 'climax': climax, 'dur': dur}


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('video'); ap.add_argument('--climax', type=float)
    ap.add_argument('--scene-thresh', type=float, default=0.32); ap.add_argument('--out')
    a = ap.parse_args()
    total, R, info = check(a.video, a.climax, a.scene_thresh)
    lines = [f'{os.path.basename(a.video)}: {total:.0f}/100  {"PASS" if total >= 80 else "FAIL"}']
    for k, got, mx, note in R:
        lines.append(f' {"  " if got >= mx * 0.8 else "->"} {k:24s} {got:5.1f}/{mx:<3d} {note}')
    print('\n'.join(lines))
    if a.out:
        os.makedirs(a.out, exist_ok=True); base = os.path.join(a.out, os.path.basename(a.video).rsplit('.', 1)[0] + '.edit')
        open(base + '.txt', 'w').write('\n'.join(lines) + '\n'); json.dump(info, open(base + '.json', 'w'))
