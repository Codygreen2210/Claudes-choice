#!/bin/bash
# joins parts/*.py into torn.py (the parts are the source; edit them, then run this)
cd "$(dirname "$0")" && cat parts/00_head.py parts/10_light.py parts/20_world.py parts/25_lights.py parts/30_man1.py parts/31_tint.py parts/40_debris.py parts/60_pose.py parts/65_poses.py parts/70_map.py parts/80_cam.py parts/85_frame.py parts/99_render.py > torn.py && python3 -c "import ast; ast.parse(open('torn.py').read()); print('parse ok')"
