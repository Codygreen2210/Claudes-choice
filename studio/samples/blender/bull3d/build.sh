#!/bin/bash
# joins parts/*.py into bull3d.py (the parts are the source; edit them, then run this)
cd "$(dirname "$0")" && cat parts/[0-9]*.py > bull3d.py && python3 -c "import ast; ast.parse(open('bull3d.py').read()); print('parse ok')"
