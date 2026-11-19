# Cut lines for every art piece, for both styles (a: clean, white border; b: rough hand cut), so Blender on the farm needs no OpenCV.
#   python3 contours.py   -> art/contours.json  {style: {name: {"W", "H", "pts": [[x, y], ...]}}}
import os, json, random, glob
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); ART = os.path.join(HERE, 'art'); out = {}
for style in ('a', 'b'):
    out[style] = {}
    for f in sorted(glob.glob(os.path.join(ART, '*.png'))):
        name = os.path.basename(f)[:-4]
        if name == 'backdrop': continue
        im = cv2.imread(f, cv2.IMREAD_UNCHANGED); H, W = im.shape[:2]
        a = (im[:, :, 3] > 100).astype(np.uint8) * 255
        grow = int(0.012 * H) if style == 'a' else int(0.011 * H)
        a = cv2.dilate(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * grow + 1, 2 * grow + 1)))
        a = cv2.morphologyEx(a, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))
        cs, _ = cv2.findContours(a, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); c = max(cs, key=cv2.contourArea)
        c = cv2.approxPolyDP(c, 0.0018 * H if style == 'a' else 0.004 * H, True)[:, 0, :].astype(float)
        if style == 'b':
            r = random.Random(sum(map(ord, name)))
            c = np.array([(x + r.uniform(-1, 1) * 0.004 * H, y + r.uniform(-1, 1) * 0.004 * H) for x, y in c])
        out[style][name] = {'W': W, 'H': H, 'pts': [[round(x, 1), round(y, 1)] for x, y in c]}
json.dump(out, open(os.path.join(ART, 'contours.json'), 'w')); print({s: len(v) for s, v in out.items()})
