#!/bin/bash
# joins parts/*.py into glass.py (the parts are the source; edit them, then run this)
cd "$(dirname "$0")" && cat parts/[0-9]*.py > glass.py && python3 -c "import ast; ast.parse(open('glass.py').read()); print('parse ok')"
