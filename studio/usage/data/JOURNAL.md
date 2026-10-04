# Usage journal

One row per session, oldest first. "Units" are tokens weighted by assumed price ratios (fresh input 1, cached re-read 0.1, cache write 1.25 or 2, output 5). Anthropic does not publish how a plan weighs these, so treat units as a yardstick for comparing sessions, not as plan percent.

| Date | Rules v | Your turns | Model calls | Units | Units per turn | Subagent units | Biggest chat size | Re-reads at full price | Read gate (stopped / overridden) | Costliest thing kept in the chat |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-10-03 | 1 | 11 | 28 | 1.0M | 1.1M | 11.4M | 224k | 0 | 0 / 0 | Subagent report (65k) |
| 2026-10-03 | 1 | 13 | 80 | 3.4M | 757k | 6.5M | 365k | 0 | 0 / 0 | Subagent report (238k) |
| 2026-10-04 | 1 | 9 | 81 | 3.2M | 1.1M | 6.2M | 284k | 0 | 0 / 0 | Subagent report (83k) |

## Rule changes

- none yet (rules v1: read cap 400 lines, nudge at 120k tokens)
