"""Break down a video the way the owner watches one: hook, camera and pacing, script and voice, sound, on-screen text.
    python3 studio/senses/watch.py VIDEO.mp4 --out DIR [--transcript transcript.json] [--info info.json]
transcript.json / info.json default to files beside the video (the Watch room workflow writes them; see watch.sh).
Writes DIR/report.txt (plain numbers + notes), DIR/stats.json (for comparing videos), DIR/watch.png (timeline),
DIR/sheet.png (one frame a second), DIR/hook.png (the first 3 seconds, 4 frames a second).
Compare two:  python3 studio/senses/watch.py --compare A/stats.json B/stats.json"""
import sys, os, json, argparse, subprocess, re
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('video', nargs='?'); ap.add_argument('--out', default=None)
ap.add_argument('--transcript', default=None); ap.add_argument('--info', default=None)
ap.add_argument('--compare', nargs=2, default=None)
a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ compare mode
if a.compare:
    A, B = [json.load(open(p)) for p in a.compare]
    na, nb = [os.path.basename(os.path.dirname(os.path.abspath(p))) or p for p in a.compare]
    print(f'{"":34s}{na[:18]:>18s}{nb[:18]:>18s}')
    for k in A:
        if isinstance(A[k], (int, float)) and isinstance(B.get(k), (int, float)):
            print(f'{k:34s}{A[k]:>18.2f}{B[k]:>18.2f}')
    sys.exit(0)

import cv2
V = a.video; out = a.out or os.path.splitext(V)[0] + '_watch'; os.makedirs(out, exist_ok=True)
vd = os.path.dirname(os.path.abspath(V))
tp = a.transcript or os.path.join(vd, 'transcript.json'); ip = a.info or os.path.join(vd, 'info.json')
TR = json.load(open(tp)) if os.path.exists(tp) else None
INFO = json.load(open(ip)) if os.path.exists(ip) else {}

# ------------------------------------------------------------------ read frames (small) once
cap = cv2.VideoCapture(V); FPS = cap.get(cv2.CAP_PROP_FPS) or 30.0
W0, H0 = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
SW = 240; SH = int(round(SW * H0 / W0 / 2) * 2)
STEP = max(1, int(round(FPS / 15)))                       # analyse ~15 frames a second
small, big_t, bigs = [], [], []                          # gray small frames; plus 2 fps frames at 540 px wide for text/sheets
k = 0; nxt_big = 0.0
while True:
    ok, fr = cap.read()
    if not ok: break
    t = k / FPS
    if k % STEP == 0: small.append((t, cv2.cvtColor(cv2.resize(fr, (SW, SH), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY), cv2.resize(fr, (48, int(48 * H0 / W0)))))
    if t >= nxt_big - 1e-6:
        bigs.append(cv2.resize(fr, (540, int(540 * H0 / W0)), interpolation=cv2.INTER_AREA)); big_t.append(t); nxt_big += 0.25
    k += 1
cap.release()
DUR = k / FPS
T = np.array([s[0] for s in small]); dt = STEP / FPS

# ------------------------------------------------------------------ cuts: colour-histogram jumps between neighbours
def hist(img):
    h = cv2.calcHist([cv2.cvtColor(img, cv2.COLOR_BGR2HSV)], [0, 1], None, [16, 8], [0, 180, 0, 256]); return cv2.normalize(h, h).flatten()
H = [hist(s[2]) for s in small]
hd = np.array([0.0] + [1 - cv2.compareHist(H[i - 1], H[i], cv2.HISTCMP_CORREL) for i in range(1, len(H))])
gd = np.array([0.0] + [float(np.mean(np.abs(small[i][1].astype(float) - small[i - 1][1]))) for i in range(1, len(small))])
base = np.array([np.median(gd[max(0, i - 15):i + 15]) for i in range(len(gd))])
cut_i = [i for i in range(1, len(gd)) if (hd[i] > 0.45 and gd[i] > 3 * base[i] + 8) or hd[i] > 0.75]
cuts = []
for i in cut_i:
    if not cuts or T[i] - cuts[-1] > 0.25: cuts.append(float(T[i]))

# ------------------------------------------------------------------ camera motion: optical flow, global (median) motion in % of frame width per second
cutset = set(cut_i); mot = np.zeros(len(small)); zoom = np.zeros(len(small))
# Track corners frame to frame and fit one camera move (shift + zoom) with RANSAC. Captions and logos sit still while
# the picture moves, so pixels that barely change for +-0.5 s are masked out; a still shot then has almost nothing left = still.
G = np.stack([s_[1] for s_ in small]).astype(np.float32)
for i in range(1, len(small)):
    if i in cutset: continue
    lo_, hi_ = max(0, i - 7), min(len(small), i + 8)
    cs = [c for c in cuts if T[lo_] < c <= T[hi_ - 1]]
    if cs:                                                        # keep the window inside this shot
        c0 = max([j for j in range(lo_, hi_) if j in cutset and T[j] <= T[i]], default=lo_); c1 = min([j for j in range(lo_, hi_) if j in cutset and T[j] > T[i]], default=hi_)
        lo_, hi_ = c0, c1
    live = (G[lo_:hi_].std(0) > 3.0).astype(np.uint8) * 255
    p0 = cv2.goodFeaturesToTrack(small[i - 1][1], 300, 0.01, 5, mask=live)
    if p0 is None or len(p0) < 12: continue
    p1, st_, _ = cv2.calcOpticalFlowPyrLK(small[i - 1][1], small[i][1], p0, None, winSize=(21, 21), maxLevel=3)
    gd_ = st_.ravel() == 1
    if gd_.sum() < 12: continue
    Mx, inl = cv2.estimateAffinePartial2D(p0[gd_], p1[gd_], method=cv2.RANSAC, ransacReprojThreshold=1.5)
    if Mx is None or inl.sum() < 8: continue
    sc = float(np.hypot(Mx[0, 0], Mx[1, 0])); tx, ty = float(Mx[0, 2] + (sc - 1) * SW / 2), float(Mx[1, 2] + (sc - 1) * SH / 2)
    rot = abs(float(np.arctan2(Mx[1, 0], Mx[0, 0]))) * SW / 2
    mot[i] = (np.hypot(tx, ty) + abs(sc - 1) * SW * 0.5 + rot) / SW * 100 / dt; zoom[i] = (sc - 1) * 100 / dt
# a fast move can look like a cut to the colour test: if the camera is moving hard on both sides, it was a move, not a cut
real = []
for c in cuts:
    j = int(np.searchsorted(T, c)); a_, b_ = mot[max(0, j - 4):j - 1], mot[j + 1:j + 4]
    if len(a_) and len(b_) and np.median(a_) > 20 and np.median(b_) > 20: mot[j] = (np.median(a_) + np.median(b_)) / 2; cutset.discard(j)
    else: real.append(c)
cuts = real
for i in cutset: mot[i] = mot[i - 1] if i > 0 else 0
ms = np.convolve(mot, np.ones(5) / 5, mode='same')               # ~1/3 s smoothing
CLS = [('still', 0, 3), ('drift', 3, 12), ('move', 12, 40), ('whip', 40, 1e9)]
def cls(v): return next(n for n, lo, hi in CLS if lo <= v < hi)
lab = [cls(v) for v in ms]
share = {n: float(np.mean([l == n for l in lab])) for n, _, _ in CLS}
# rests = runs of still/drift of 1 s or more (camera calm long enough to take in the moment)
rests = []; s0 = None
for i, l in enumerate(lab + ['move']):
    calm = l in ('still', 'drift') and i not in cutset
    if calm and s0 is None: s0 = i
    if not calm and s0 is not None:
        if T[min(i, len(T) - 1)] - T[s0] >= 1.0: rests.append((float(T[s0]), float(T[min(i, len(T) - 1)])))
        s0 = None
shot_lens = np.diff([0.0] + cuts + [DUR])

# ------------------------------------------------------------------ on-screen text: tesseract boxes on 2 fps frames
def ocr(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY); words = []
    for inv in (False, True):                                     # white captions with outline, and dark text on light
        x = 255 - g if inv else g
        x = cv2.threshold(x, 200, 255, cv2.THRESH_BINARY)[1] if not inv else cv2.threshold(x, 190, 255, cv2.THRESH_BINARY)[1]
        x = 255 - x
        try: r = subprocess.run(['tesseract', 'stdin', 'stdout', '--psm', '11', 'tsv'], input=cv2.imencode('.png', x)[1].tobytes(), capture_output=True, timeout=30).stdout.decode(errors='ignore')
        except Exception: continue
        for ln in r.splitlines()[1:]:
            p = ln.split('\t')
            if len(p) < 12: continue
            w = p[11].strip(); cf = float(p[10]) if p[10] not in ('', '-1') else -1
            if cf > 70 and len(re.sub(r'[^A-Za-z0-9]', '', w)) >= 2:
                words.append((w, int(p[6]), int(p[7]), int(p[8]), int(p[9])))
    return words
text_t = big_t[::2]; text_f = bigs[::2]; TXT = []
for t, f in zip(text_t, text_f):
    ws = ocr(f); hh = f.shape[0]
    TXT.append({'t': t, 'words': [w[0] for w in ws], 'h': [w[4] / hh * 100 for w in ws], 'y': [(w[2] + w[4] / 2) / hh * 100 for w in ws]})
txt_on = np.array([len(x['words']) > 0 for x in TXT])
heights = [h for x in TXT for h in x['h']]; ys = [y for x in TXT for y in x['y']]
# text "events": a new caption when the set of words changes
tev = 0; prev = None
for x in TXT:
    key = ' '.join(sorted(set(w.upper() for w in x['words'])))
    if key and key != prev: tev += 1
    prev = key

# ------------------------------------------------------------------ script and voice
words = [w for s in TR['segments'] for w in s.get('words', [])] if TR else []
segs = TR['segments'] if TR else []
speech_s = sum(w['end'] - w['start'] for w in words)
first_word = words[0]['start'] if words else None
gaps = [(words[i]['end'], words[i + 1]['start']) for i in range(len(words) - 1) if words[i + 1]['start'] - words[i]['end'] > 0.35]
full = ' '.join(s['text'] for s in segs)
sents = [x.strip() for x in re.split(r'(?<=[.!?])\s+', full) if x.strip()]
cta_words = ('subscribe', 'follow', 'like', 'comment', 'share', 'part 2', 'part two', 'watch till', 'link in')
cta = [s for s in sents[-3:] if any(c in s.lower() for c in cta_words)]
opens_q = bool(sents) and sents[0].rstrip().endswith('?')

# ------------------------------------------------------------------ sound: ears + quiet spots + hit density
wav = os.path.join(out, 'audio.wav')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', V, '-vn', '-ac', '2', '-ar', '48000', wav], check=False)
ears = ''; quiet = []; onsets = []; lvl = None; lvl_t = None
if os.path.exists(wav) and os.path.getsize(wav) > 1000:
    subprocess.run([sys.executable, os.path.join(HERE, 'listen.py'), wav, '--out', out], capture_output=True)
    lp = os.path.join(out, 'audio.listen.txt'); ears = open(lp).read() if os.path.exists(lp) else ''
    import soundfile as sf
    x, sr = sf.read(wav); x = x.mean(1) if x.ndim > 1 else x
    win, hop = int(0.4 * sr), int(0.1 * sr)
    st = np.array([20 * np.log10(np.sqrt(np.mean(x[i:i + win] ** 2)) + 1e-9) for i in range(0, max(1, len(x) - win), hop)])
    med = np.median(st); qs = [i * 0.1 for i, v in enumerate(st) if v < med - 8 and 0.2 < i * 0.1 < len(x) / sr - 0.6]
    for q in qs:
        if quiet and q - quiet[-1][1] <= 0.15: quiet[-1][1] = q + 0.4
        else: quiet.append([q, q + 0.4])
    lvl = st - med; lvl_t = np.arange(len(st)) * 0.1 + 0.2
    try:
        import librosa
        onsets = list(librosa.onset.onset_detect(y=x.astype(np.float32), sr=sr, units='time', backtrack=False))
    except Exception: pass

# ------------------------------------------------------------------ hook (first 3 s)
h_i = T < 3.0
hook = {'motion_first_half_second': float(np.mean(ms[T < 0.5])) if np.any(T < 0.5) else 0.0,
        'motion_first_3s': float(np.mean(ms[h_i])) if np.any(h_i) else 0.0,
        'cuts_first_3s': sum(1 for c in cuts if c < 3.0), 'first_word_s': first_word,
        'text_on_frame_one': bool(TXT and TXT[0]['words']),
        'words_first_3s': len([w for w in words if w['start'] < 3.0])}

# ------------------------------------------------------------------ stats + report
wps = len(words) / speech_s if speech_s else 0.0
stats = {'duration_s': DUR, 'cuts': len(cuts), 'cuts_per_min': len(cuts) / DUR * 60, 'avg_shot_s': float(np.mean(shot_lens)),
         'longest_shot_s': float(np.max(shot_lens)), 'camera_still_pct': share['still'] * 100, 'camera_drift_pct': share['drift'] * 100,
         'camera_move_pct': share['move'] * 100, 'camera_whip_pct': share['whip'] * 100, 'camera_avg_speed': float(np.mean(ms)),
         'rests_1s_plus': len(rests), 'rest_time_pct': sum(b - a_ for a_, b in rests) / DUR * 100,
         'longest_rest_s': max([b - a_ for a_, b in rests], default=0.0), 'moves_per_10s': 0.0,
         'hook_motion_first_half_s': hook['motion_first_half_second'], 'hook_motion_3s': hook['motion_first_3s'],
         'first_word_s': first_word if first_word is not None else -1, 'words': len(words),
         'words_per_s_talking': wps, 'words_per_s_overall': len(words) / DUR, 'talk_time_pct': speech_s / DUR * 100,
         'voice_gaps_over_0_35s': len(gaps), 'text_on_screen_pct': float(np.mean(txt_on) * 100) if len(txt_on) else 0.0,
         'text_changes_per_10s': tev / DUR * 10, 'text_height_pct_median': float(np.median(heights)) if heights else 0.0,
         'text_y_pct_median': float(np.median(ys)) if ys else 0.0, 'quiet_spots': len(quiet),
         'sound_hits_per_s': len(onsets) / DUR if DUR else 0.0}
# a "move" starts each time the camera goes from calm to moving
stats['moves_per_10s'] = sum(1 for i in range(1, len(lab)) if lab[i] in ('move', 'whip') and lab[i - 1] in ('still', 'drift')) / DUR * 10
for k_ in ('view_count', 'like_count', 'comment_count', 'channel_follower_count'):
    if INFO.get(k_) is not None: stats[k_] = float(INFO[k_])
json.dump(stats, open(os.path.join(out, 'stats.json'), 'w'), indent=1)

L = []
P = L.append
P(f"WATCH: {INFO.get('title') or os.path.basename(V)}")
if INFO.get('webpage_url'): P(f"  {INFO['webpage_url']}")
meta = [f"{INFO[k_]:,} {n}" for k_, n in (('view_count', 'views'), ('like_count', 'likes'), ('comment_count', 'comments')) if INFO.get(k_) is not None]
if INFO.get('channel'): meta.append(f"channel {INFO['channel']}" + (f" ({INFO['channel_follower_count']:,} subs)" if INFO.get('channel_follower_count') else ''))
if INFO.get('views') is None and INFO.get('view_count') and INFO.get('channel_follower_count'): meta.append(f"views/subs {INFO['view_count'] / max(1, INFO['channel_follower_count']):.1f}x")
if meta: P('  ' + ', '.join(meta))
P(f"  {DUR:.1f} s, {W0}x{H0}, {FPS:.0f} fps")
P('')
P('HOOK (first 3 s)')
P(f"  camera speed in the first half second: {hook['motion_first_half_second']:.0f} ({cls(hook['motion_first_half_second'])}); first 3 s: {hook['motion_first_3s']:.0f}")
P(f"  first word at {first_word:.2f} s" if first_word is not None else '  no transcript (first word unknown)')
P(f"  cuts in the first 3 s: {hook['cuts_first_3s']}; text on frame one: {'yes' if hook['text_on_frame_one'] else 'no'}; words in the first 3 s: {hook['words_first_3s']}")
if sents: P(f"  opening line: \"{sents[0]}\"" + ('  (opens with a QUESTION)' if opens_q else ''))
P('')
P('CAMERA AND PACING (camera speed = how far the picture slides, % of the frame width a second)')
P(f"  cuts: {len(cuts)} ({len(cuts) / DUR * 60:.0f} a minute), average shot {np.mean(shot_lens):.1f} s, longest {np.max(shot_lens):.1f} s" + ('  -> ONE CONTINUOUS SHOT' if len(cuts) == 0 else ''))
P(f"  time the camera is still {share['still'] * 100:.0f}%, drifting {share['drift'] * 100:.0f}%, moving {share['move'] * 100:.0f}%, whipping {share['whip'] * 100:.0f}%  (average speed {np.mean(ms):.0f})")
P(f"  rests (calm 1 s or more): {len(rests)}, {sum(b - a_ for a_, b in rests) / DUR * 100:.0f}% of the video, longest {stats['longest_rest_s']:.1f} s; new camera moves: {stats['moves_per_10s']:.1f} every 10 s")
if rests: P('  rest spots: ' + ', '.join(f'{a_:.1f}-{b:.1f}' for a_, b in rests[:14]) + (' ...' if len(rests) > 14 else ''))
if cuts: P('  cut times: ' + ', '.join(f'{c:.1f}' for c in cuts[:30]) + (' ...' if len(cuts) > 30 else ''))
P('')
P('SCRIPT AND VOICE')
if TR:
    P(f"  {len(words)} words; {wps:.2f} words a second while talking, {len(words) / DUR:.2f} over the whole video; talking {speech_s / DUR * 100:.0f}% of the time")
    P(f"  pauses over 0.35 s: {len(gaps)}" + (' at ' + ', '.join(f'{g0:.1f}' for g0, _ in gaps[:12]) if gaps else ''))
    P(f"  sentences: {len(sents)}, average {np.mean([len(s.split()) for s in sents]):.1f} words" if sents else '')
    P(f"  last line: \"{sents[-1]}\"" if sents else '')
    P(f"  call to action at the end: {'yes: ' + cta[-1] if cta else 'no'}")
    P('  transcript:')
    for s in segs: P(f"    {s['start']:5.1f}  {s['text']}")
else: P('  no transcript.json (run it through watch.sh to get one)')
P('')
P('SOUND')
for ln in ears.splitlines():
    if ln.startswith(('loudness', 'tempo', 'energy')): P('  ' + ln)
P(f"  sound hits: {len(onsets) / DUR:.1f} a second; quiet spots (0.4 s, 8 dB under the rest): {len(quiet)}" + (' at ' + ', '.join(f'{q0:.1f}' for q0, _ in quiet[:10]) if quiet else ''))
lo = ears.split('listen out for:')[1].strip().splitlines() if 'listen out for:' in ears else []
for ln in lo[:4]:
    if ln.strip().startswith('-'): P('  ears: ' + ln.strip()[2:])
P('')
P('ON-SCREEN TEXT')
P(f"  text on screen {np.mean(txt_on) * 100:.0f}% of the time, changes {tev / DUR * 10:.1f} times every 10 s")
if heights: P(f"  letter height about {np.median(heights):.1f}% of the frame height, sitting {np.median(ys):.0f}% down from the top")
seen = []
for x in TXT:
    s = ' '.join(x['words'])
    if s and (not seen or s != seen[-1][1]): seen.append((x['t'], s))
for t, s in seen[:25]: P(f"    {t:5.1f}  {s[:70]}")
open(os.path.join(out, 'report.txt'), 'w').write('\n'.join(L) + '\n')

# ------------------------------------------------------------------ pictures
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
C = {'still': '#2e7d32', 'drift': '#9ccc65', 'move': '#ffb300', 'whip': '#e53935'}
fig, ax = plt.subplots(4, 1, figsize=(14, 7.5), sharex=True, gridspec_kw={'height_ratios': [3, 1, 1, 2]}, facecolor='#111')
for a_ in ax: a_.set_facecolor('#111'); a_.tick_params(colors='#bbb'); [s.set_color('#444') for s in a_.spines.values()]
for n, lo_, hi_ in CLS: ax[0].fill_between(T, 0, ms, where=[l == n for l in lab], color=C[n], step='mid', label=n)
for c in cuts: [a_.axvline(c, color='white', lw=0.8, alpha=0.7) for a_ in ax]
for r0, r1 in rests: ax[0].axvspan(r0, r1, color='#2e7d32', alpha=0.12)
ax[0].set_ylim(0, max(50, np.percentile(ms, 99) * 1.1)); ax[0].set_ylabel('camera speed', color='#bbb'); ax[0].legend(loc='upper right', ncol=4, fontsize=8, facecolor='#222', labelcolor='#ddd')
ax[0].set_title(f"{(INFO.get('title') or os.path.basename(V))[:80]}   cuts {len(cuts)}   rest {stats['rest_time_pct']:.0f}%   {wps:.1f} words/s", color='white', loc='left', fontsize=10)
for w in words: ax[1].axvspan(w['start'], w['end'], ymin=0.15, ymax=0.85, color='#4fc3f7', lw=0)
for s in segs: ax[1].text(s['start'], 0.5, s['text'][:28], color='white', fontsize=6, va='center', clip_on=True)
ax[1].set_yticks([]); ax[1].set_ylabel('voice', color='#bbb')
ax[2].fill_between([x['t'] for x in TXT], 0, [1 if x['words'] else 0 for x in TXT], step='mid', color='#ffd54f'); ax[2].set_yticks([]); ax[2].set_ylabel('text', color='#bbb')
if lvl is not None: ax[3].plot(lvl_t, lvl, color='#ce93d8', lw=0.8)
for o in onsets: ax[3].axvline(o, ymin=0.0, ymax=0.15, color='#80deea', lw=0.6)
for q0, q1 in quiet: ax[3].axvspan(q0, q1, color='#e53935', alpha=0.4)
ax[3].set_ylabel('loudness / hits', color='#bbb'); ax[3].set_xlabel('seconds', color='#bbb')
plt.tight_layout(); plt.savefig(os.path.join(out, 'watch.png'), dpi=110, facecolor='#111'); plt.close()

def tile(frames, ts, cols, w):
    fs = []
    for f, t in zip(frames, ts):
        g = cv2.resize(f, (w, int(w * f.shape[0] / f.shape[1]))); cv2.rectangle(g, (0, 0), (62, 18), (0, 0, 0), -1)
        cv2.putText(g, f'{t:.2f}' if t < 10 else f'{t:.1f}', (3, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1); fs.append(g)
    while len(fs) % cols: fs.append(np.zeros_like(fs[0]))
    return np.vstack([np.hstack(fs[r * cols:(r + 1) * cols]) for r in range(len(fs) // cols)])
sel = [i for i, t in enumerate(big_t) if abs(t - round(t)) < 0.01]
cv2.imwrite(os.path.join(out, 'sheet.png'), tile([bigs[i] for i in sel], [big_t[i] for i in sel], 10, 160))
hk = [i for i, t in enumerate(big_t) if t < 3.0]
cv2.imwrite(os.path.join(out, 'hook.png'), tile([bigs[i] for i in hk], [big_t[i] for i in hk], 6, 200))
print(open(os.path.join(out, 'report.txt')).read())
