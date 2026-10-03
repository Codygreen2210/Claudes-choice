import json, os, sys, tempfile, unittest
T = tempfile.mkdtemp(); os.environ["USAGE_DATA"] = os.path.join(T, "data")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, gate, evolve

def U(i, cr, cw, o): return {"input_tokens": i, "cache_read_input_tokens": cr, "cache_creation_input_tokens": cw, "output_tokens": o, "cache_creation": {"ephemeral_1h_input_tokens": cw}}

class Tests(unittest.TestCase):
    def test_parse(self):
        p = os.path.join(T, "s.jsonl")
        rows = [
            {"type": "user", "sessionId": "s1", "timestamp": "2026-10-03T10:00:00Z", "message": {"content": "hi"}},
            {"type": "assistant", "requestId": "r1", "message": {"usage": U(10, 0, 1000, 5), "content": [{"type": "thinking"}]}},
            {"type": "assistant", "requestId": "r1", "message": {"usage": U(10, 0, 1000, 50), "content": [{"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "cd x && npm test"}}]}},
            {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "t1", "content": "x" * 4000}]}},
            {"type": "assistant", "requestId": "r2", "message": {"usage": U(5, 2000, 100, 20), "content": []}},
            {"type": "assistant", "requestId": "r3", "message": {"usage": U(5, 2100, 100, 20), "content": []}},
        ]
        open(p, "w").write("\n".join(json.dumps(r) for r in rows))
        r = common.parse(p, common.DEFAULT["weights"])
        self.assertEqual((r["calls"], r["user_turns"], r["tokens"]["output"]), (3, 1, 90))
        self.assertEqual(r["weighted"], int(20 + 4100 * 0.1 + 1200 * 2 + 90 * 5))
        o = r["offenders"]["Bash: npm test"]
        self.assertEqual((o["tokens"], o["carry"]), (1000, int(1000 * (2 + 0.1 * 1))))
        self.assertEqual(common.tail_context(p), 2205)

    def test_gate(self):
        big = os.path.join(T, "big.txt"); open(big, "w").write("line of text here\n" * 3000)
        small = os.path.join(T, "small.txt"); open(small, "w").write("a\n" * 50)
        cfg = dict(common.DEFAULT)
        inp = lambda path, **k: {"tool_name": "Read", "session_id": "s", "tool_input": dict(file_path=path, **k)}
        self.assertIsNone(gate.decide(inp(small), cfg, 0, [])[0])
        reason, ev = gate.decide(inp(big), cfg, 50000, [])
        self.assertIn("3001 lines", reason); self.assertEqual(ev["kind"], "gate_deny")
        self.assertIsNone(gate.decide(inp(big, limit=100), cfg, 50000, [])[0])
        self.assertEqual(gate.decide(inp(big, limit=3001), cfg, 0, [dict(ev, kind="gate_deny")])[1]["kind"], "gate_override")
        # huge chat: one refused read costs more than it saves, so it passes
        self.assertEqual(gate.decide(inp(big), cfg, 5_000_000, [])[1]["kind"], "gate_pass_cheap")
        self.assertIsNone(gate.decide(inp(os.path.join(T, "pic.png")), cfg, 0, [])[0])

    def test_evolve_trial_then_put_back(self):
        cfg = json.loads(json.dumps(common.DEFAULT))
        row = lambda i, v, per: {"session": f"{v}-{i}", "start": f"2026-10-{v:02d}T{i:02d}", "config_version": v, "user_turns": 5, "per_turn": per, "weighted": per * 5,
                                 "gate_denies": 0, "gate_overrides": 0, "peak_context": 50000, "tokens": {"cache_read": 0},
                                 "offenders": {"Read .py": {"count": 3, "tokens": 9000, "carry": 30000}}}
        rows = [row(i, 1, 1000) for i in range(5)]
        cfg = evolve.run(rows, cfg)
        self.assertEqual((cfg["version"], cfg["read_cap_lines"], cfg["trial"]["old"]), (2, 320, 400))
        cfg = evolve.run(rows + [row(i, 2, 1500) for i in range(5)], cfg)   # worse: put back
        self.assertEqual((cfg["read_cap_lines"], cfg["trial"], cfg["version"]), (400, None, 3))
        self.assertIn("PUT BACK", cfg["history"][-1])

    def test_evolve_keeps_a_win_and_respects_bounds(self):
        cfg = json.loads(json.dumps(common.DEFAULT)); cfg["read_cap_lines"] = 150
        row = lambda i, v, per: {"session": f"{v}-{i}", "start": f"2026-10-{v:02d}T{i:02d}", "config_version": v, "user_turns": 5, "per_turn": per, "weighted": per * 5,
                                 "gate_denies": 0, "gate_overrides": 0, "peak_context": 50000, "tokens": {"cache_read": 0},
                                 "offenders": {"Read .py": {"count": 3, "tokens": 9000, "carry": 30000}}}
        cfg = evolve.run([row(i, 1, 1000) for i in range(5)], cfg)
        self.assertEqual((cfg["version"], cfg["read_cap_lines"]), (1, 150))   # already at the floor: no change

if __name__ == "__main__":
    unittest.main()
