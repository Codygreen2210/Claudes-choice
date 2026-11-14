# Equirect Earth color map (2048x1024) -> earth_col.jpg, from the GLOBE 1 km land mask (pip download global-land-mask, MIT; data NOAA GLOBE, public domain).
#   python3 -I earth_tex.py globe_combined_mask_compressed.npz OUTDIR
import sys, numpy as np
from PIL import Image
src, out = sys.argv[1], sys.argv[2]
z = np.load(src, allow_pickle=False); m = z['mask']; lat = z['lat']
H, W = 1024, 2048
fy, fx = m.shape[0] // H, m.shape[1] // W                     # 21, 21 (crop the remainder)
sea = m[:fy * H:3, :fx * W:3].reshape(H, fy // 3, W, fx // 3).mean(axis=(1, 3)) if False else None
sub = m[:fy * H, :fx * W][::3, ::3]
sea = sub.reshape(H, sub.shape[0] // H, W, sub.shape[1] // W).mean(axis=(1, 3)).astype(np.float32)
if lat[0] < lat[-1]: sea = sea[::-1]                          # row 0 = north
land = 1 - sea
rng = np.random.default_rng(3)
def fbm(h, w, oct_=6, seed=0):
    r = np.random.default_rng(seed); acc = np.zeros((h, w), np.float32); amp = 1.0
    for o in range(oct_):
        s = 2 ** (o + 2); g = r.random((s // 2 + 1, s + 1)).astype(np.float32)
        gi = np.array(Image.fromarray(g).resize((w, h), Image.BICUBIC)); acc += amp * gi; amp *= 0.55
    return (acc - acc.min()) / (acc.max() - acc.min())
n1 = fbm(H, W, 9, 1); n2 = fbm(H, W, 9, 2)
la = np.abs(np.linspace(90, -90, H))[:, None] * np.ones((1, W))
# land colour: green belts, tan/ochre deserts (20-35 deg), dark boreal, white ice
green = np.array([0.16, 0.30, 0.10]); dgreen = np.array([0.10, 0.20, 0.08]); desert = np.array([0.62, 0.50, 0.32]); tan = np.array([0.45, 0.40, 0.25])
dry = np.clip(1 - np.abs(la - 26) / 12, 0, 1) * np.clip(n1 * 1.6 - 0.25, 0, 1)
bor = np.clip((la - 48) / 12, 0, 1)
lc = green * (1 - dry[..., None]) + desert * dry[..., None]
lc = lc * (1 - bor[..., None]) + dgreen * bor[..., None]
lc = lc * (0.8 + 0.4 * n2[..., None]); lc = lc * (1 - 0.3 * np.clip(n1 - 0.5, 0, 1)[..., None]) + tan * 0.12
ice = np.clip((la - 66) / 6, 0, 1) * land; ice = np.maximum(ice, np.clip((la - 78) / 4, 0, 1))
deep = np.array([0.004, 0.022, 0.085]); shal = np.array([0.02, 0.12, 0.26])
# shallow water near coasts: blur the land mask
lb = np.array(Image.fromarray((land * 255).astype(np.uint8)).filter(__import__('PIL.ImageFilter', fromlist=['x']).GaussianBlur(4))) / 255.0
oc = deep + (shal - deep) * np.clip(lb * 2.2, 0, 1)[..., None]
c = oc * (1 - land[..., None]) + lc * land[..., None]
c = c * (1 - ice[..., None]) + np.array([0.86, 0.9, 0.95]) * ice[..., None]
img = (np.clip(c, 0, 1) ** (1 / 2.2) * 255).astype(np.uint8)
Image.fromarray(img).save(out + '/earth_col.jpg', quality=92)
Image.fromarray((np.clip(land, 0, 1) * 255).astype(np.uint8)).save(out + '/earth_land.png')
print('ok', img.shape, land.mean())
