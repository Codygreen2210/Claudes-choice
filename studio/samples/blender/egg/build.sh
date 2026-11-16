#!/bin/bash
# joins parts/*.py into egg.py (the parts are the source; edit them, then run this)
cd "$(dirname "$0")" && cat parts/[0-9]*.py > egg.py && python3 -c "import ast; ast.parse(open('egg.py').read()); print('parse ok')"
