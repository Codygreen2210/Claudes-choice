#!/usr/bin/env python3
"""Catch code hidden inside a // comment (a scripted edit that appends '// note' mid-line silently comments out what follows it).
   python3 scenes/lint.py file.js ...   -> prints suspect lines, exit 1 if any. Run by every scene's build.sh.
   Hit three times on 2026-11-01/02: eyeSet.add(iris), let tiltShown, and a whole contactsheet line went dark."""
import re, sys
CODE = re.compile(r"(\b(if|for|while) \([^)]*\)[^;]*;|\b(const|let|var) [A-Za-z_$][\w$]* = [^;]*;|[A-Za-z_$][\w$.]*\([^)]*\)\s*;|\b(continue|break|return[^;]*);)")
bad = 0
for fn in sys.argv[1:]:
    for n, line in enumerate(open(fn, encoding='utf8'), 1):
        s, q, i = line, None, 0
        while i < len(s) - 1:                                   # find a // that is not inside a string or a regex-ish literal
            c = s[i]
            if q: q = None if c == q and s[i - 1] != '\\' else q
            elif c in '\'"`': q = c
            elif s[i:i + 2] == '//' and (i == 0 or s[i - 1] != ':'): break
            i += 1
        else: continue
        if not s[:i].strip(): continue                         # a whole-line comment (docs, usage examples) is fine; the trap is code BEFORE the //
        com = s[i + 2:]
        if CODE.search(com) and not com.strip().startswith('http'):
            print(f"{fn}:{n}: code after // (commented out?): {s.strip()[:160]}"); bad += 1
sys.exit(1 if bad else 0)
