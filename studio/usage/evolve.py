"""The tuner. It may change two numbers by itself, inside fixed bounds, one at a time, on trial:
  read_cap_lines         how big a whole-file read can be before the gate asks for a range
  nudge_context_tokens   how big the chat gets before Claude is told to save state and offer a fresh session
A change is kept only if the next 5 sessions are not more than 10% worse in units per turn; otherwise it is put back.
Anything bigger than those two numbers is written to data/PROPOSALS.md for a person to approve."""
import os, statistics
from common import DATA, save_config

MIN_SESSIONS, MIN_TURNS = 5, 3

def _median(rs):
    v = [r["per_turn"] for r in rs if r["user_turns"] >= MIN_TURNS]
    return statistics.median(v) if len(v) >= MIN_SESSIONS else None

def _clamp(cfg, key, val):
    lo, hi = cfg["bounds"][key]
    return int(max(lo, min(hi, val)))

def run(rows, cfg):
    rows = sorted(rows, key=lambda r: r.get("start") or "")
    cur = [r for r in rows if r["config_version"] == cfg["version"]]
    med = _median(cur)
    changed = False
    t = cfg.get("trial")
    if t and med is not None:
        if med > t["baseline"] * 1.10:
            cfg[t["key"]] = t["old"]
            cfg["history"].append(f"v{cfg['version']} PUT BACK: {t['key']} {t['new']} -> {t['old']}; units per turn went {int(t['baseline'])} -> {int(med)} over {len(cur)} sessions")
            cfg["version"] += 1
        else:
            cfg["history"].append(f"v{cfg['version']} KEPT: {t['key']} = {t['new']}; units per turn {int(t['baseline'])} -> {int(med)} over {len(cur)} sessions")
        cfg["trial"] = None; changed = True
    elif not t and med is not None:
        den = sum(r["gate_denies"] for r in cur); ovr = sum(r["gate_overrides"] for r in cur)
        carry = {}
        for r in cur:
            for lab, o in r["offenders"].items(): carry[lab] = carry.get(lab, 0) + o["carry"]
        top = max(carry, key=carry.get) if carry else ""
        peak = statistics.median([r["peak_context"] for r in cur])
        reread = sum(r["tokens"]["cache_read"] * cfg["weights"]["cache_read"] for r in cur) / max(sum(r["weighted"] for r in cur), 1)
        key = new = why = None
        if den >= 10 and ovr / den > 0.5:
            key, new, why = "read_cap_lines", cfg["read_cap_lines"] * 1.25, f"{ovr} of {den} stopped reads were needed in full anyway"
        elif top.startswith("Read") and (den == 0 or ovr / den < 0.15):
            key, new, why = "read_cap_lines", cfg["read_cap_lines"] * 0.8, "file reads are still the costliest thing kept in the chat"
        elif peak > cfg["nudge_context_tokens"] and reread > 0.5:
            key, new, why = "nudge_context_tokens", cfg["nudge_context_tokens"] * 0.85, f"re-reading the chat is {int(reread * 100)}% of units"
        if key:
            new = _clamp(cfg, key, new)
            if new != cfg[key]:
                cfg["trial"] = {"key": key, "old": cfg[key], "new": new, "baseline": med}
                cfg["version"] += 1
                cfg["history"].append(f"v{cfg['version']} TRIAL: {key} {cfg[key]} -> {new} because {why}; baseline {int(med)} units per turn")
                cfg[key] = new; changed = True
    if changed:
        save_config(cfg)
    _proposals(rows[-10:])
    return cfg

HINT = [("Bash:", "run it through studio/usage/quiet.py, or use a narrower command"),
        ("Subagent", "ask subagents for a shorter report, or have them write findings to a file and return one line"),
        ("Read", "the tuner handles this one by itself"),
        ("WebFetch", "ask the fetch for the specific facts wanted, not the page"),
        ("WebSearch", "fewer, sharper searches"),
        ("mcp__", "connector results are large: ask for fewer fields or fewer rows")]

def _proposals(rows):
    carry = {}
    for r in rows:
        for lab, o in r["offenders"].items():
            c = carry.setdefault(lab, [0, 0]); c[0] += o["carry"]; c[1] += o["count"]
    total = sum(r["weighted"] for r in rows) or 1
    L = ["# Proposals", "", "What cost the most to keep in the chat over the last %d sessions. The tuner does not act on these; a person decides." % len(rows), "",
         "| Thing | Times | Share of units | Suggested change |", "|---|---|---|---|"]
    for lab, (c, n) in sorted(carry.items(), key=lambda kv: -kv[1][0])[:6]:
        hint = next((h for p, h in HINT if lab.startswith(p)), "look at whether all of it was needed")
        L.append(f"| {lab} | {n} | {100 * c / total:.0f}% | {hint} |")
    sub = sum(r.get("subagent_weighted", 0) for r in rows)
    L += ["", f"Subagents' own work was {100 * sub / (sub + total):.0f}% of all units in these sessions (main chat {100 * total / (sub + total):.0f}%). "
          "Each subagent starts cold and pays for its own setup, so fewer, narrower subagents is the biggest lever when this number is high."]
    os.makedirs(DATA, exist_ok=True)
    open(os.path.join(DATA, "PROPOSALS.md"), "w").write("\n".join(L) + "\n")
