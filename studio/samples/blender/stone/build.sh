#!/bin/bash
# joins parts/*.py into stone.py (the parts are the source; edit them, then run this)
cd "$(dirname "$0")" && cat parts/00_head.py parts/20_room.py parts/10_light.py parts/25_lights.py parts/30_man1.py parts/35_man2.py parts/45_anat.py parts/50_macro.py parts/60_pose.py parts/65_poses.py parts/80_cam.py parts/85_frame.py parts/99_render.py > stone.py && python3 -c "import ast; ast.parse(open('stone.py').read()); print('parse ok')"
