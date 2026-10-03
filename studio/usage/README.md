# Usage tools

Cuts how much of a Claude plan a session in this repo uses, keeps a journal of what happened, and tunes itself.

| Piece | What it does | When it runs |
|---|---|---|
| `gate.py` | Stops a whole-file read of a big file and asks for a range, but only when that saves more than the extra round trip costs. | Before every Read |
| `quiet.py` | Runs a noisy command and returns only failures and the tail. Full output is kept in `.usage-logs/`. | When Claude runs tests or builds through it |
| `nudge.py` | When the chat passes a size limit, tells Claude to save state to `notes/STATE.md` and offer a fresh session. | On each message you send |
| `start.py` | Loads `notes/STATE.md` so Claude knows where things stand. | Start of every session, and after a compaction |
| `journal.py` | Reads the real session logs and writes one row per session to `data/JOURNAL.md`: units used, units per turn, what cost most. | End of session, before compaction, every 15 min |
| `evolve.py` | The tuner. Changes one of two numbers on trial, keeps it only if the next 5 sessions are not more than 10% worse, otherwise puts it back. Writes bigger ideas to `data/PROPOSALS.md` for a person. | Each time the journal runs |

## What is and is not proven
- The journal reads real token counts from Claude Code's own logs. Those are facts.
- "Units" weigh those tokens by assumed price ratios. Anthropic does not publish plan weights, so units compare sessions; they are not plan percent.
- No saving has been measured yet. It needs at least 5 sessions before and after a change. The honest check is the usage bar in Settings before and after the same job.

## Limits
- Works in Claude Code sessions on this repo (laptop or cloud). It does nothing for the phone chat app.
- Cloud sessions are wiped, so the journal only lasts if `studio/usage/data/` is committed.
- The tuner only touches `read_cap_lines` and `nudge_context_tokens`, inside the bounds in `data/config.json`. Everything else needs a person.

Tests: `python3 studio/usage/test_usage.py`
