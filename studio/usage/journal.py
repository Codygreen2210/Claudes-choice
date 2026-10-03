#!/usr/bin/env python3
"""Reads Claude Code session logs and keeps a journal of where usage went, session by session.
  python3 studio/usage/journal.py                 journal every session log for this project
  python3 studio/usage/journal.py path/to.jsonl   journal one
  (as a hook it reads transcript_path from stdin: --hook, or --hook-throttled for at most once per 15 min)"""
import json, sys, os, glob, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DATA, load_config, parse, subagent_weighted, events

JPATH = os.path.join(DATA, "journal.jsonl")

def rows():
    out = {}
    try:
        for l in open(JPATH):
            r = json.loads(l); out[r["session"]] = r
    except Exception:
        pass
    return out

def record(path, cfg):
    r = parse(path, cfg["weights"])
    if not r["calls"]:
        return None
    r["subagent_weighted"] = subagent_weighted(path, cfg["weights"])
    ev = [e for e in events() if e.get("session") == r["session"]]
    r["gate_denies"] = sum(e["kind"] == "gate_deny" for e in ev)
    r["gate_overrides"] = sum(e["kind"] == "gate_override" for e in ev)
    r["gate_saved_tokens"] = sum(e.get("saved_tokens", 0) for e in ev if e["kind"] == "gate_deny")
    r["nudges"] = sum(e["kind"] == "nudge" for e in ev)
    old = rows().get(r["session"])
    r["config_version"] = old["config_version"] if old else cfg["version"]
    r["per_turn"] = int((r["weighted"] + r["subagent_weighted"]) / max(r["user_turns"], 1))
    top = sorted(r["offenders"].items(), key=lambda kv: -kv[1]["carry"])[:8]
    r["offenders"] = dict(top)
    return r

def write(all_rows, cfg):
    os.makedirs(DATA, exist_ok=True)
    ordered = sorted(all_rows.values(), key=lambda r: r.get("start") or "")
    with open(JPATH, "w") as f:
        for r in ordered: f.write(json.dumps(r) + "\n")
    k = lambda n: f"{n / 1000:.0f}k" if n < 1e6 else f"{n / 1e6:.1f}M"
    L = ["# Usage journal", "",
         "One row per session, oldest first. \"Units\" are tokens weighted by assumed price ratios (fresh input 1, cached re-read 0.1, "
         "cache write 1.25 or 2, output 5). Anthropic does not publish how a plan weighs these, so treat units as a yardstick for "
         "comparing sessions, not as plan percent.", "",
         "| Date | Rules v | Your turns | Model calls | Units | Units per turn | Subagent units | Biggest chat size | Re-reads at full price | Read gate (stopped / overridden) | Costliest thing kept in the chat |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in ordered:
        top = next(iter(r["offenders"].items()), ("-", {"carry": 0}))
        L.append(f"| {(r.get('start') or '')[:10]} | {r['config_version']} | {r['user_turns']} | {r['calls']} | {k(r['weighted'])} | {k(r['per_turn'])} | "
                 f"{k(r['subagent_weighted'])} | {k(r['peak_context'])} | {r['cache_misses']} | {r['gate_denies']} / {r['gate_overrides']} | {top[0]} ({k(top[1]['carry'])}) |")
    L += ["", "## Rule changes", ""]
    L += [f"- {h}" for h in cfg.get("history", [])] or ["- none yet (rules v1: read cap %d lines, nudge at %s tokens)" % (cfg["read_cap_lines"], k(cfg["nudge_context_tokens"]))]
    open(os.path.join(DATA, "JOURNAL.md"), "w").write("\n".join(L) + "\n")

def main(argv):
    cfg = load_config()
    paths = [a for a in argv if not a.startswith("--")]
    if "--hook" in argv or "--hook-throttled" in argv:
        inp = json.load(sys.stdin)
        paths = [inp.get("transcript_path")]
        stamp = os.path.join(DATA, ".last-journal")
        if "--hook-throttled" in argv and os.path.exists(stamp) and time.time() - os.path.getmtime(stamp) < 900:
            return
        os.makedirs(DATA, exist_ok=True); open(stamp, "w").write("")
    if not paths:
        proj = os.path.expanduser("~/.claude/projects/" + os.getcwd().replace("/", "-"))
        paths = sorted(glob.glob(os.path.join(proj, "*.jsonl")))
    allr = rows()
    for p in paths:
        if p and os.path.isfile(p):
            r = record(p, cfg)
            if r: allr[r["session"]] = r
    import evolve
    cfg = evolve.run(list(allr.values()), cfg)
    write(allr, cfg)
    if "--hook" not in argv and "--hook-throttled" not in argv:
        print(open(os.path.join(DATA, "JOURNAL.md")).read())

def autocommit():
    """Commit and push only the journal files, never on main. Quiet on any failure."""
    import subprocess
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    git = lambda *a: subprocess.run(["git", "-C", root] + list(a), capture_output=True, text=True, timeout=15)
    rel = os.path.relpath(DATA, root)
    if git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip() in ("main", "master", "HEAD", ""):
        return
    if not git("status", "--porcelain", "--", rel).stdout.strip():
        return
    git("add", "--", rel)
    git("-c", "user.name=Claude", "-c", "user.email=noreply@anthropic.com", "commit", "-q", "-m",
        "Usage journal update (automatic)\n\nCo-Authored-By: Claude <noreply@anthropic.com>", "--", rel)
    git("push", "-q")

if __name__ == "__main__":
    hook = any(a.startswith("--hook") for a in sys.argv)
    try: main(sys.argv[1:])
    except Exception:
        if not hook: raise
    if hook or "--commit" in sys.argv:
        try: autocommit()
        except Exception: pass
    sys.exit(0)
