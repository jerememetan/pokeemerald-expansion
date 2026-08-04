# Phase 8A Double-Battle Thinking Status Implementation Plan

> **For agentic workers:** Execute this corrective plan task-by-task with tests before the implementation change.

**Goal:** Restore the visible fixed thinking status for pending external-AI requests in both supported double-battle types.

**Specification:** [Phase 8A specification](../specs/2026-08-04-phase-8a-double-thinking-status.md)
**Flow review:** [Phase 8A flow review](../reviews/2026-08-04-phase-8a-double-thinking-status-flow-review.md)
**Evidence:** [Phase 8A verification evidence](../reviews/2026-08-04-phase-8a-double-thinking-status-evidence.md)

**Architecture:** Make the battle-main readiness predicate inspect every alive
player battler. Export a test-only wrapper for the predicate so battle tests
can prove single, double, and absent-partner readiness without changing mailbox
or service behavior.

**Tech Stack:** pokeemerald-expansion C, existing battle test runner, WSL
devkitARM build, Python `unittest` bridge suite.

---

### Task 1: Add failing readiness regression tests

**Files:**
- Modify: `include/battle_agent.h`
- Modify: `test/battle/ai.c`
- Modify: `src/battle_main.c`

- [ ] Add a TESTING-only declaration for a wrapper that returns the player-side
  thinking-status readiness predicate.
- [ ] Add battle tests that set player-left/player-right confirmation states and
  assert: a single confirmed player is ready; a double with only one confirmed
  player is not ready; a double with both confirmed players is ready; and an
  absent right player does not prevent readiness.
- [ ] Run `make -j16 check TESTS='External AI thinking status player readiness'`.
  Expected before the fix: the double-with-one-confirmed test demonstrates the
  left-only predicate is insufficient.

### Task 2: Implement the smallest double-aware predicate

**Files:**
- Modify: `src/battle_main.c`
- Modify: `include/battle_agent.h`

- [ ] Add a local helper that recognizes `STATE_WAIT_ACTION_CONFIRMED` and
  `STATE_WAIT_ACTION_CONFIRMED_STANDBY`.
- [ ] Make `IsPlayerActionConfirmedForExternalAiStatus` iterate player-side
  battlers. Skip absent battlers; return false for any alive player battler
  outside either confirmed state; otherwise return true.
- [ ] Add the TESTING-only wrapper used by Task 1. Do not alter
  `BattleAgent_UpdateThinkingStatus`, response polling, timeout, or renderer.
- [ ] Re-run the focused readiness command. Expected: all readiness cases pass.

### Task 3: Regression verification and evidence

**Files:**
- Modify: `docs/openai-battle-agent/integration-plan.md`
- Create: `docs/openai-battle-agent/reviews/2026-08-04-phase-8a-double-thinking-status-evidence.md`

- [ ] Run in WSL: `make -j16 check TESTS='External AI'` and `make -j16`.
  Expected: no External AI test failures and a fresh ROM.
- [ ] Run in PowerShell: `py -3 -m unittest discover -s tools\mgba-bridge\tests -q`
  and `git diff --check`. Expected: no failures/errors and no whitespace errors.
- [ ] Manual smoke: verify `AI is thinking..` after player action confirmation
  in a trainer single, intentional double, and two-trainer double. Stop the
  service during a pending double request and verify the text clears into
  vanilla fallback.
- [ ] Record only observed results in the evidence document and link the spec,
  flow review, plan, and evidence from the roadmap.
