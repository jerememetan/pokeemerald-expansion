# Phase 8A Double-Battle Thinking Status Flow Review

**Specification reviewed:** [Phase 8A specification](../specs/2026-08-04-phase-8a-double-thinking-status.md)
**Implementation plan:** [Phase 8A implementation plan](../plans/2026-08-04-phase-8a-double-thinking-status.md)
**Evidence:** [Phase 8A verification evidence](2026-08-04-phase-8a-double-thinking-status-evidence.md)
**Grounding:** `src/battle_main.c`, `src/battle_agent.c`, and the existing
thinking-status tests in `test/battle/ai.c`.

## User flows

1. **Trainer single:** the player confirms its sole action, the normal message
   window becomes idle, and the pending external request shows the fixed text.
2. **Intentional trainer double:** the player selects both actions. Until both
   are confirmed, the selection UI remains visible. Once settled and idle, the
   shared opponent request shows one fixed text until it resolves.
3. **Two-trainer double:** the same player-side readiness rule applies while
   one atomic request controls both trainer-owned opponents.
4. **Response/fallback:** accepted action pairs clear the text before battle
   actions proceed; no response clears it only through the existing timeout and
   vanilla fallback path.

## Root cause and gaps

| Severity | Finding | Resolution |
| --- | --- | --- |
| Important | `IsPlayerActionConfirmedForExternalAiStatus` was written for Phase 5 singles and checks only `B_POSITION_PLAYER_LEFT`. Phase 7 coordinated doubles reuse it unchanged, so the status can remain gated by an incomplete/nonrepresentative player-side state. | Replace it with a helper that requires every alive player battler to be action-confirmed in a double. |
| Important | Existing tests call the status state machine with manually supplied readiness values, so they never verify player-side confirmation in a real double state. | Add a testable readiness helper and regression cases for one confirmed player, both confirmed players, and an absent partner. |
| Minor | Both waiting opponent battlers can attempt the same fixed render in a coordinated double. | Keep the existing renderer unchanged because the text is identical and both waits resolve atomically; the readiness fix does not widen this behavior. |

No critical gaps remain. The readiness helper must use the same
`STATE_WAIT_ACTION_CONFIRMED` and `STATE_WAIT_ACTION_CONFIRMED_STANDBY` states
that the battle loop already recognizes, and it must exclude absent player
battlers.
