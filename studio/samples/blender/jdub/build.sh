#!/bin/bash
# joins parts/*.py (in name order) into jdub.py (the parts are the source; edit them, then run this)
cd "$(dirname "$0")" && cat $(ls parts/*.py | sort) > jdub.py && python3 -c "import ast; ast.parse(open('jdub.py').read()); print('parse ok')"
