#!/bin/bash
# joins parts/*.py into fork.py (the parts are the source; edit them, then run this)
cd "$(dirname "$0")" && cat parts/[0-9]*.py > fork.py && python3 -c "import ast; ast.parse(open('fork.py').read()); print('parse ok')"
