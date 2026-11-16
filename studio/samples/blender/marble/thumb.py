"""Thumbnail still: the two leaders flying through the ring on the final jump, close up.   python3 thumb.py OUT.png [frame]"""
import sys, os
out = sys.argv[1]; fr = int(sys.argv[2]) if len(sys.argv) > 2 else 3778
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'marble.py')).read(); src = src[:src.index("if __name__ == '__main__':")]
sys.argv = ['marble.py', '/tmp/x', '0', '1', '--samples', '96', '--scale', '1.0']
g = {'__file__': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'marble.py'), '__name__': 'thumb'}; exec(compile(src, g['__file__'], 'exec'), g)
import math, bpy
from mathutils import Vector
g['frame'](fr); h = g['LMK']['kick3_h']; hp = g['LMK']['hoop']
sd = Vector((math.sin(h), -math.cos(h), 0)); fw = Vector((math.cos(h), math.sin(h), 0))
cp = hp + sd * -1.55 + fw * 0.9 + Vector((0, 0, 0.32)); g['look'](cp, hp + fw * -0.35 + Vector((0, 0, -0.08)), 30, fstop=11.0)
g['S'].render.use_motion_blur = False
for o in bpy.data.objects:
    if o.name.startswith(('s_', 'panel')): o.hide_render = True
g['S'].view_settings.look = 'AgX - Punchy'; g['S'].render.filepath = out
import bpy; bpy.ops.render.render(write_still=True); print('thumb', out)
