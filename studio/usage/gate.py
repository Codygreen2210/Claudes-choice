#!/usr/bin/env python3
"""PreToolUse hook for Read: turns away a whole-file read of a big file when a ranged read would be cheaper.
Fails open: any problem means the read goes ahead."""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SKIP = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".ipynb", ".svg", ".mp4", ".wav")

def decide(inp, cfg, context_tokens, past):
    """Returns (deny_reason or None, event dict or None)."""
    ti = inp.get("tool_input") or {}
    path = ti.get("file_path") or ""
    cap = cfg["read_cap_lines"]
    if inp.get("tool_name") != "Read" or not path or path.lower().endswith(SKIP) or not os.path.isfile(path):
        return None, None
    if os.path.getsize(path) > 20_000_000:
        return None, None
    with open(path, "rb") as f:
        data = f.read()
    lines = data.count(b"\n") + 1
    limit, offset = ti.get("limit"), ti.get("offset") or 0
    sid = inp.get("session_id")
    if limit:
        if limit > cap * 1.5 and any(e.get("kind") == "gate_deny" and e.get("session") == sid and e.get("path") == path for e in past):
            return None, {"kind": "gate_override", "session": sid, "path": path}
        return None, None
    want = min(lines - offset, 2000)
    if want <= cap:
        return None, None
    excess_tokens = (len(data) / 4.0) * (want - cap) / max(lines, 1)
    # A refusal costs one extra model call, which re-reads the whole chat at the cached rate.
    if excess_tokens * 2 < 0.1 * context_tokens:
        return None, {"kind": "gate_pass_cheap", "session": sid, "path": path, "lines": lines}
    reason = (f"Usage gate: {os.path.basename(path)} has {lines} lines (cap {cap}). Grep for what you need, or Read with "
              f"offset and limit. If you truly need all of it, Read again with limit={lines}.")
    return reason, {"kind": "gate_deny", "session": sid, "path": path, "lines": lines, "saved_tokens": int(excess_tokens)}

def main():
    from common import load_config, event, events, tail_context
    inp = json.load(sys.stdin)
    cfg = load_config()
    reason, ev = decide(inp, cfg, tail_context(inp.get("transcript_path") or ""), events())
    if ev:
        event(ev.pop("kind"), v=cfg["version"], **ev)
    if reason:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}}))

if __name__ == "__main__":
    try: main()
    except Exception: pass
    sys.exit(0)
