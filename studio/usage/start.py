#!/usr/bin/env python3
"""SessionStart hook: puts notes/STATE.md in front of Claude at the start of every session and again after a compaction."""
import os, sys
try:
    root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    lines = open(os.path.join(root, "notes", "STATE.md")).read().splitlines()[:60]
    print("[state] Where things stand (from notes/STATE.md). Pick up from here; keep this file current as you work.\n" + "\n".join(lines))
except Exception:
    pass
sys.exit(0)
