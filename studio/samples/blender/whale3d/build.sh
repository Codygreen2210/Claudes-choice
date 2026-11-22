#!/bin/bash
# joins parts/*.py into whale3d.py (the parts are the source; edit them, then run this)
cd "$(dirname "$0")" && cat parts/[0-9]*.py > whale3d.py && python3 -c "import ast; ast.parse(open('whale3d.py').read()); print('parse ok')"
