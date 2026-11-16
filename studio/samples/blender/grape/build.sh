#!/bin/bash
# joins parts/*.py into grape.py (the parts are the source; edit them, then run this)
cd "$(dirname "$0")" && cat parts/[0-9]*.py > grape.py && python3 -c "import ast; ast.parse(open('grape.py').read()); print('parse ok')"
