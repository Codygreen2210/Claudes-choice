#!/bin/bash
# joins parts/*.py (in name order) into crush.py (the parts are the source; edit them, then run this)
cd "$(dirname "$0")" && cat $(ls parts/*.py | sort) > crush.py && python3 -c "import ast; ast.parse(open('crush.py').read()); print('parse ok')"
