import bpy, sys, os, json
D = '/root/.config/blender/5.2/extensions/.user/user_default/mpfb/data'
import addon_utils; addon_utils.enable('bl_ext.user_default.mpfb', default_set=True)
from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.targetservice import TargetService
bpy.ops.wm.read_homefile(use_empty=True)
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
macro = TargetService.get_default_macro_info_dict()
print('macro', json.dumps(macro))
macro.update({'gender': 1.0, 'age': 0.42, 'muscle': 0.55, 'weight': 0.55, 'height': 0.55, 'proportions': 0.6})
b = HumanService.create_human(macro_detail_dict=macro)
print('basemesh', b.name, len(b.data.vertices))
try: HumanService.add_builtin_rig(b, 'default'); print('rig ok')
except Exception as e: print('rig fail', e)
HumanService.set_character_skin(f'{D}/skins/young_caucasian_male/young_caucasian_male.mhmat', b, skin_type='ENHANCED_SSS')
for f, t in [('eyes/high-poly/high-poly.mhclo', 'Eyes'), ('eyebrows/eyebrow001/eyebrow001.mhclo', 'Eyebrows'), ('eyelashes/eyelashes01/eyelashes01.mhclo', 'Eyelashes'),
             ('teeth/teeth_base/teeth_base.mhclo', 'Teeth'), ('tongue/tongue01/tongue01.mhclo', 'Tongue'), ('hair/short02/short02.mhclo', 'Hair'),
             ('clothes/male_casualsuit06/male_casualsuit06.mhclo', 'Clothes'), ('clothes/shoes05/shoes05.mhclo', 'Clothes')]:
    p = f'{D}/{f}'
    if not os.path.exists(p): print('missing', p); continue
    try: o = HumanService.add_mhclo_asset(p, b, asset_type=t, subdiv_levels=0, material_type='MAKESKIN'); print('added', t, o.name if o else None)
    except Exception as e: print('fail', t, e)
bpy.ops.wm.save_as_mainfile(filepath='/home/claude/mh/human.blend')
print([ (o.name, o.type) for o in bpy.data.objects])
