# Usage journal

One row per session, oldest first. "Units" are tokens weighted by assumed price ratios (fresh input 1, cached re-read 0.1, cache write 1.25 or 2, output 5). Anthropic does not publish how a plan weighs these, so treat units as a yardstick for comparing sessions, not as plan percent.

| Date | Rules v | Your turns | Model calls | Units | Units per turn | Subagent units | Biggest chat size | Re-reads at full price | Read gate (stopped / overridden) | Costliest thing kept in the chat |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-10-03 | 1 | 6 | 19 | 787k | 2.0M | 11.4M | 210k | 0 | 0 / 0 | Subagent report (49k) |

## Rule changes

- none yet (rules v1: read cap 400 lines, nudge at 120k tokens)
