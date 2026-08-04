# Phase 8A Double-Battle Thinking Status Verification Evidence

**Specification:** [Phase 8A specification](../specs/2026-08-04-phase-8a-double-thinking-status.md)
**Flow review:** [Phase 8A flow review](2026-08-04-phase-8a-double-thinking-status-flow-review.md)
**Implementation plan:** [Phase 8A implementation plan](../plans/2026-08-04-phase-8a-double-thinking-status.md)

## Root cause and change

`IsPlayerActionConfirmedForExternalAiStatus` only inspected the player-left
battler. That predicate predates coordinated external-AI doubles, where two
player action confirmations are required before the lower message panel can
take over. The predicate now requires every active player battler to be in one
of the existing confirmed states; absent positions are ignored. The existing
message-window, request, response, timeout, and vanilla-fallback behavior is
unchanged.

## Automated evidence

| Command | Result | Evidence |
| --- | --- | --- |
| `make -j16 check TESTS='External AI thinking status requires every alive player action in doubles'` | Pass | 1/1 focused regression passed. |
| `make -j16 check TESTS='External AI'` | Pass | 33/33 external-AI tests passed, including singles, intentional doubles, and two-trainer doubles. |
| `py -3 -m unittest discover -s tools/mgba-bridge/tests -q` | Pass | 74 tests passed. |
| `git diff --check` | Pass | No whitespace errors. |

The test runner emitted the project’s established unrelated `ASSUME failed`
messages while still reporting a successful focused and External AI suite.

## Manual evidence

On 2026-08-04, the normal rebuilt ROM was manually verified in both supported
double-battle types:

1. An intentional one-trainer double displayed `AI is thinking..` after both
   player actions were selected.
2. A two-trainer double displayed the same fixed text after both player actions
   were selected.

The existing focused and full External AI suites retain single-battle and
timeout/fallback coverage. Phase 8A exit criteria are met.
