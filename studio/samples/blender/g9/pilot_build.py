# The pilot for the 9 G Short: the MakeHuman man (MPFB2, see ../mh/setup.sh) in a coverall (male_worksuit01, dyed flight-suit sage
# by g9.py), boots, default rig; no hair, brows or lashes (a helmet and visor go over his head). Textures are packed into the .blend.
#   python3 pilot_build.py OUT.blend
import bpy, sys, os
D = '/root/.config/blender/5.2/extensions/.user/user_default/mpfb/data'
import addon_utils; addon_utils.enable('bl_ext.user_default.mpfb', default_set=True)
from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.targetservice import TargetService
out = sys.argv[-1]
bpy.ops.wm.read_homefile(use_empty=True)
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
macro = TargetService.get_default_macro_info_dict()
macro.update({'gender': 1.0, 'age': 0.45, 'muscle': 0.62, 'weight': 0.5, 'height': 0.52, 'proportions': 0.62})
b = HumanService.create_human(macro_detail_dict=macro)
HumanService.add_builtin_rig(b, 'default')                     # the rig first: assets added before it don't follow it
HumanService.set_character_skin(f'{D}/skins/young_caucasian_male/young_caucasian_male.mhmat', b, skin_type='ENHANCED_SSS')
for f, t in [('eyes/high-poly/high-poly.mhclo', 'Eyes'), ('clothes/male_worksuit01/male_worksuit01.mhclo', 'Clothes'), ('clothes/shoes05/shoes05.mhclo', 'Clothes')]:
    p = f'{D}/{f}'
    if not os.path.exists(p): print('missing', p); continue
    o = HumanService.add_mhclo_asset(p, b, asset_type=t, subdiv_levels=0, material_type='MAKESKIN'); print('added', t, o.name if o else None)
try: bpy.ops.file.pack_all()
except Exception as e: print('pack', e)
bpy.ops.wm.save_as_mainfile(filepath=out)
for o in bpy.data.objects: print(o.name, o.type, len(o.data.vertices) if o.type == 'MESH' else '', [m.type for m in o.modifiers])
