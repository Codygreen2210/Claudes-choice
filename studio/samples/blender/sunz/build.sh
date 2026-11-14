#!/bin/bash
# joins parts/*.py into sunz.py (the parts are the source; edit them, then run this)
cd "$(dirname "$0")" && cat parts/[0-9]*.py > sunz.py && python3 -c "import ast; ast.parse(open('sunz.py').read()); print('parse ok')"
