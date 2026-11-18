#!/bin/bash
# joins parts/*.py into rome3d.py (the parts are the source; edit them, then run this)
cd "$(dirname "$0")" && cat parts/[0-9]*.py > rome3d.py && python3 -c "import ast; ast.parse(open('rome3d.py').read()); print('parse ok')"
