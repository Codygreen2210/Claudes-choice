import sys, time
import numpy as np
from PIL import Image
from common import *


def scene():
    c = Canvas(0, -300, 1.0)
    c.background('#2a2350', '#5a4a8a', glow=(540, 700, 380, '#ffb860', 0.35))
    box(c, 0, 380, 900, 120, WOOD, r=30)
    guy(c, -160, 330, 0.9, face='shock', arms=((150, 20), (130, 125)))
    guy(c, 260, 330, 0.75, face='happy', woman=True, glasses=True, shirt=RED)
    disc(c, 300, -980, 90, ramp('#ffcc33'))
    c.shape(heart(-330, -1000, 140), (-410, -1080, -250, -920), RED)
    c.glow(circle(0, -1150, 20), (-20, -1170, 20, -1130), '#ffe14d', 40, 0.8)
    hook_text(c, 'ENGINE V3', 1.0)
    return c


out = sys.argv[1] if len(sys.argv) > 1 else 'test.png'
scene()  # warm caches
t = time.time()
c = scene()
img = c.to_uint8()
print('shape', img.shape, 'sec', round(time.time() - t, 3))
Image.fromarray(img).save(out)
np.save(out + '.npy', img)
