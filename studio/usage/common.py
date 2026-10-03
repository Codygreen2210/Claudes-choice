"""Shared pieces for the usage tools: config, event log, and reading Claude Code session logs."""
import json, os, time, glob

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("USAGE_DATA") or os.path.join(HERE, "data")
CONFIG = os.path.join(DATA, "config.json")
DEFAULT = {
    "version": 1,
    "read_cap_lines": 400,
    "nudge_context_tokens": 120000,
    "nudge_every_turns": 8,
    # Assumed weights (API list-price ratios). Anthropic does not publish plan weights.
    "weights": {"input": 1.0, "cache_read": 0.1, "cache_write_5m": 1.25, "cache_write_1h": 2.0, "output": 5.0},
    "bounds": {"read_cap_lines": [150, 1200], "nudge_context_tokens": [60000, 250000]},
    "trial": None,
    "history": [],
}

def load_config():
    cfg = json.loads(json.dumps(DEFAULT))
    try:
        cfg.update(json.load(open(CONFIG)))
    except Exception:
        pass
    return cfg

def save_config(cfg):
    os.makedirs(DATA, exist_ok=True)
    json.dump(cfg, open(CONFIG, "w"), indent=1)

def event(kind, **kw):
    os.makedirs(DATA, exist_ok=True)
    kw.update(kind=kind, ts=int(time.time()))
    with open(os.path.join(DATA, "events.jsonl"), "a") as f:
        f.write(json.dumps(kw) + "\n")

def events():
    out = []
    try:
        for l in open(os.path.join(DATA, "events.jsonl")):
            try: out.append(json.loads(l))
            except Exception: pass
    except Exception:
        pass
    return out

def context_of(u):
    return (u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)

def tail_context(path, nbytes=400000):
    """Context size (tokens) of the most recent model call in a session log."""
    try:
        with open(path, "rb") as f:
            f.seek(0, 2); size = f.tell(); f.seek(max(0, size - nbytes))
            lines = f.read().decode("utf-8", "ignore").splitlines()
        for l in reversed(lines):
            try: d = json.loads(l)
            except Exception: continue
            if d.get("type") == "assistant" and d.get("message", {}).get("usage"):
                return context_of(d["message"]["usage"])
    except Exception:
        pass
    return 0

def weigh(u, w):
    cc = u.get("cache_creation") or {}
    w1h = cc.get("ephemeral_1h_input_tokens") or 0
    w5m = (u.get("cache_creation_input_tokens") or 0) - w1h
    return ((u.get("input_tokens") or 0) * w["input"] + (u.get("cache_read_input_tokens") or 0) * w["cache_read"]
            + max(w5m, 0) * w["cache_write_5m"] + w1h * w["cache_write_1h"] + (u.get("output_tokens") or 0) * w["output"])

def label_of(name, inp):
    if name == "Bash":
        import re
        segs = [x.strip() for x in re.split(r"&&|;|\n", str(inp.get("command", ""))) if x.strip()]
        segs = [x for x in segs if not x.startswith(("cd ", "export ", "mkdir "))] or segs[:1]
        parts = [p for p in (segs[0].split() if segs else []) if "=" not in p and p != "sudo"][:2]
        if parts and parts[0].startswith("/"): parts[0] = os.path.basename(parts[0])
        return "Bash: " + " ".join(parts)[:40]
    if name == "Read":
        return "Read " + (os.path.splitext(str(inp.get("file_path", "")))[1] or "file")
    if name in ("Agent", "Task"):
        return "Subagent report"
    return name

def parse(path, weights):
    """Read one session log. Returns totals plus tool results ranked by carry cost."""
    calls, order, tools, results, user_turns, first, last, sid = {}, [], {}, [], 0, None, None, None
    for l in open(path, errors="ignore"):
        try: d = json.loads(l)
        except Exception: continue
        ts = d.get("timestamp"); sid = sid or d.get("sessionId")
        if ts: first = first or ts; last = ts
        m = d.get("message") or {}
        if d.get("type") == "assistant":
            rid = d.get("requestId") or d.get("uuid")
            u = m.get("usage")
            if u:
                if rid not in calls: order.append(rid)
                if rid not in calls or (u.get("output_tokens") or 0) >= (calls[rid].get("output_tokens") or 0):
                    calls[rid] = u
            for c in m.get("content") or []:
                if isinstance(c, dict) and c.get("type") == "tool_use":
                    tools[c.get("id")] = label_of(c.get("name", "?"), c.get("input") or {})
        elif d.get("type") == "user":
            c = m.get("content")
            if isinstance(c, str):
                user_turns += 1
            elif isinstance(c, list):
                real = False
                for b in c:
                    if not isinstance(b, dict): continue
                    if b.get("type") == "tool_result":
                        body = b.get("content")
                        n = len(body) if isinstance(body, str) else len(json.dumps(body))
                        results.append((tools.get(b.get("tool_use_id"), "?"), n, len(order)))
                    elif b.get("type") == "text":
                        real = True
                user_turns += real
    tot = {"input": 0, "cache_read": 0, "cache_write": 0, "output": 0}
    weighted = peak = misses = 0
    for i, rid in enumerate(order):
        u = calls[rid]
        tot["input"] += u.get("input_tokens") or 0; tot["cache_read"] += u.get("cache_read_input_tokens") or 0
        tot["cache_write"] += u.get("cache_creation_input_tokens") or 0; tot["output"] += u.get("output_tokens") or 0
        weighted += weigh(u, weights); peak = max(peak, context_of(u))
        if i and not (u.get("cache_read_input_tokens") or 0) and (u.get("cache_creation_input_tokens") or 0) > 20000:
            misses += 1
    off = {}
    n = len(order)
    for lab, chars, at in results:
        toks = chars / 4.0
        carry = toks * (weights["cache_write_1h"] + weights["cache_read"] * max(n - at - 1, 0))
        o = off.setdefault(lab, {"count": 0, "tokens": 0, "carry": 0}); o["count"] += 1; o["tokens"] += int(toks); o["carry"] += int(carry)
    return {"session": sid or os.path.basename(path)[:8], "start": first, "end": last, "calls": n, "user_turns": user_turns,
            "tokens": tot, "weighted": int(weighted), "peak_context": peak, "cache_misses": misses, "offenders": off}

def subagent_weighted(path, weights):
    total = 0
    for f in glob.glob(os.path.join(os.path.splitext(path)[0], "**", "*.jsonl"), recursive=True):
        try: total += parse(f, weights)["weighted"]
        except Exception: pass
    return total
