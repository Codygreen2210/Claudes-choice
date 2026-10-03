#!/usr/bin/env python3
"""UserPromptSubmit hook: when the chat has grown expensive, tell Claude to save state and offer a fresh session."""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    from common import load_config, event, events, tail_context
    inp = json.load(sys.stdin)
    cfg = load_config()
    ctx = tail_context(inp.get("transcript_path") or "")
    sid = inp.get("session_id")
    mine = [e for e in events() if e.get("session") == sid]
    turns = sum(1 for e in mine if e["kind"] == "turn")
    last = max([e.get("turn", 0) for e in mine if e["kind"] == "nudge"] or [-99])
    event("turn", session=sid, turn=turns + 1, context=ctx, v=cfg["version"])
    if ctx >= cfg["nudge_context_tokens"] and turns + 1 - last >= cfg["nudge_every_turns"]:
        event("nudge", session=sid, turn=turns + 1, context=ctx, v=cfg["version"])
        print(f"[usage] This chat is about {ctx // 1000}k tokens and is re-read on every turn. Before answering, make sure "
              f"notes/STATE.md has the current state (decisions, files, next step) in a few lines, and tell the user in one "
              f"line that a fresh session picking up from notes/STATE.md would cost less. Then do what they asked.")

if __name__ == "__main__":
    try: main()
    except Exception: pass
    sys.exit(0)
