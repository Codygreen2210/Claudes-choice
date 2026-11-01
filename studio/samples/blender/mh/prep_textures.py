# Tan the young male skin; paint the MakeHuman logo off the t-shirt and dye it the channel's teal (jeans untouched).
import sys, cv2, numpy as np
from PIL import Image
D = sys.argv[1]
for n in ('young_lightskinned_male_diffuse.png', 'young_lightskinned_male_diffuse2.png'):
    im = np.asarray(Image.open(f'{D}/skins/textures/{n}').convert('RGB')).astype(np.float32) / 255
    Image.fromarray((np.clip(im ** 1.15 * np.array([0.86, 0.70, 0.56]) * 1.06, 0, 1) * 255).astype(np.uint8)).save(f'{D}/skins/textures/' + n.replace('.png', '_tan.png'))
mm = f'{D}/skins/young_caucasian_male/young_caucasian_male.mhmat'; s = open(mm).read()
if '_tan.png' not in s: open(mm, 'w').write(s.replace('young_lightskinned_male_diffuse.png', 'young_lightskinned_male_diffuse_tan.png').replace('young_lightskinned_male_diffuse2.png', 'young_lightskinned_male_diffuse2_tan.png'))
c = f'{D}/clothes/male_casualsuit06/male_casualsuit06_diffuse'
import os, shutil
if not os.path.exists(c + '.orig.png'): shutil.copy(c + '.png', c + '.orig.png')
im = cv2.imread(c + '.orig.png'); H, W = im.shape[:2]; hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
top = np.zeros((H, W), bool); top[:int(H * 0.43)] = True
m8 = cv2.dilate((((hsv[..., 1] > 50) | (hsv[..., 2] < 175)) & top).astype(np.uint8) * 255, np.ones((9, 9), np.uint8))
n, lab, st, _ = cv2.connectedComponentsWithStats(m8); keep = np.zeros_like(m8)
for i in range(1, n):
    x, y, w, h, a = st[i]
    if a > 400 and h < H * 0.12 and w < W * 0.3: keep[lab == i] = 255
f = cv2.inpaint(im, keep, 9, cv2.INPAINT_TELEA).astype(np.float32) / 255
shirt = np.clip(f.mean(2, keepdims=True) * np.array([0.60, 0.68, 0.12])[None, None] * 1.25, 0, 1)
t = np.zeros((H, W, 1), np.float32); t[:int(H * 0.43)] = 1
cv2.imwrite(c + '.png', ((f * (1 - t) + shirt * t) * 255).astype(np.uint8))
print('textures ready')
