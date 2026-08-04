# Phase 8A Specification: Double-Battle Thinking Status

**Status:** Complete; automated and manual evidence recorded
**Roadmap:** [External AI Trainer Integration Plan](../integration-plan.md)
**Flow review:** [Phase 8A flow review](../reviews/2026-08-04-phase-8a-double-thinking-status-flow-review.md)
**Implementation plan:** [Phase 8A implementation plan](../plans/2026-08-04-phase-8a-double-thinking-status.md)
**Evidence:** [Phase 8A verification evidence](../reviews/2026-08-04-phase-8a-double-thinking-status-evidence.md)
**Regression source:** The original single-battle status predicate in
`src/battle_main.c` was introduced before coordinated double battles and checks
only `B_POSITION_PLAYER_LEFT`.

## Goal

Show the fixed lower-panel `AI is thinking..` status during a pending external
AI request in both intentional one-trainer doubles and two-trainer doubles,
after the player's active battlers have completed action selection.

## In scope

- Replace the single-player confirmation predicate with one that evaluates all
  alive player battlers participating in the current battle.
- In a trainer single, retain the current left-player confirmation behavior.
- In a trainer double, wait until both active player battlers have reached an
  action-confirmed state before the status may claim the normal message window.
- Preserve the existing idle-window requirement and fixed two-dot text.
- Add focused regression coverage for the double-aware readiness decision and
  retain existing status, external-AI, one-trainer-double, and two-trainer-
  double coverage.

## Out of scope

- ROM mailbox, BAGB/5, Lua, Python service, Ollama prompt/model behavior,
  action validation, AI decisions, timeout length, trainer eligibility,
  player menus, message rendering style, and fallback behavior.
- Any new animation, status text, or asynchronous input behavior.

## Boundaries and contract

| Component | Phase 8A responsibility | Unchanged behavior |
| --- | --- | --- |
| Battle action-selection loop | Decide when it is safe to request the thinking-status render. | It remains non-blocking and continues polling the external request. |
| Battle-agent status renderer | Render only when given a settled-player signal and idle message window. | It owns and clears `B_WIN_MSG` exactly as before. |
| Double request coordination | Wait for one atomic response covering both AI battlers. | Legal actions, accepted responses, switches, and fallback are unchanged. |
| Service/Lua | None. | Existing request/response transport remains untouched. |

## Required behavior

1. While the player is selecting either move in a double, the player-facing
   selection UI remains authoritative and the thinking text does not overwrite
   it.
2. Once all alive player battlers are in an action-confirmed state and the
   normal message window is idle, a pending opponent external-AI request shows
   exactly `AI is thinking..`.
3. A valid response clears the status and applies the existing atomic decision.
4. An absent, malformed, late, invalid, or disconnected response clears the
   status at the existing deadline and uses saved vanilla AI actions.
5. Trainer singles retain their existing thinking-status behavior.

## Failure and fallback behavior

- A player battler that is absent/fainted is excluded from the double readiness
  check, matching normal action-selection behavior.
- If either alive player battler has not confirmed an action, no status is
  rendered yet; the external wait still continues normally.
- A message printer that is active defers rendering until idle; it does not
  interrupt battle text.
- No status-rendering condition may block response consumption or vanilla
  fallback.

## Tests and exit criteria

The corrective sub-phase is complete only when:

1. A test proves a single is ready after its player action is confirmed.
2. A test proves a double is not ready until both alive player actions are
   confirmed, then is ready.
3. Existing fixed-text, response, fallback, and double-action tests pass.
4. `make -j16 check TESTS='External AI'`, the Python bridge suite, and a
   normal `make -j16` pass.
5. Manual mGBA smoke shows the message in a trainer single, an intentional
   one-trainer double, and a two-trainer double; it clears on an accepted
   response and on a disconnected-service fallback.
