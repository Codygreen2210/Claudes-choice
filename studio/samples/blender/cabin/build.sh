#!/bin/bash
# joins parts/*.py into cabin.py (the parts are the source; edit them, then run this)
cd "$(dirname "$0")" && cat parts/00_head.py parts/10_light.py parts/20_cabin.py parts/22_out.py parts/25_lights.py parts/30_man1.py parts/31_tint.py parts/35_xray.py parts/45_lungs.py parts/60_pose.py parts/65_poses.py parts/70_fly.py parts/80_cam.py parts/85_frame.py parts/99_render.py > cabin.py && python3 -c "import ast; ast.parse(open('cabin.py').read()); print('parse ok')"
