#!/bin/bash
# joins parts/*.py into marble.py (the parts are the source; edit them, then run this)
cd "$(dirname "$0")" && cat parts/[0-9]*.py > marble.py && python3 -c "import ast; ast.parse(open('marble.py').read()); print('parse ok')"
