#!/bin/bash
# joins parts/*.py into boat.py (the parts are the source; edit them, then run this)
cd "$(dirname "$0")" && cat parts/[0-9]*.py > boat.py && python3 -c "import ast; ast.parse(open('boat.py').read()); print('parse ok')"
