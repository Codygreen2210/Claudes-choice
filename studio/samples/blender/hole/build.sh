#!/bin/bash
# joins parts/*.py into hole.py (the parts are the source; edit them, then run this)
cd "$(dirname "$0")" && cat parts/00_head.py parts/10_scene.py parts/20_frame.py parts/99_render.py > hole.py && python3 -c "import ast; ast.parse(open('hole.py').read()); print('parse ok')"
