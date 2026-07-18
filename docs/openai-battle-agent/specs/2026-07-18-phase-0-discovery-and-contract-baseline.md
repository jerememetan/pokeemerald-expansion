# Phase 0 Specification: Discovery and Contract Baseline

**Parent design:** [`../2026-07-18-mgba-ai-trainer-design.md`](../2026-07-18-mgba-ai-trainer-design.md)

## Goal

Produce an evidence-backed baseline for the external AI trainer feature before any battle C code, Lua bridge code, or Python service code is added. The baseline must identify the existing trainer-AI decision path, the engine-owned data required to describe a legal move action, the minimum safe interception seam, the test harness conventions, and the version-1 ROM/bridge/service contract.

## In scope

- Read-only analysis of the current trainer-AI setup, move selection, action dispatch, and trainer data paths.
- Documentation of the decision call graph from turn setup to `OpponentHandleChooseMove`.
- Documentation of the existing `gBattleStruct->aiMoveOrAction` and `gBattleStruct->aiChosenTarget` ownership and use.
- Documentation of the existing battle-test conventions in `test/battle/` and `include/test/battle.h`.
- A version-1 mailbox protocol specification for one opponent battler in a single battle selecting a move and target.
- A phase-by-phase integration plan that preserves current trainer AI fallback.

## Out of scope

- Changes to C headers, sources, trainers, data tables, battle scripts, or test code.
- An mGBA Lua script, a TCP service, model calls, mailbox allocation, or an emulator build.
- Switching, items, double-battle decisions, partner targeting, a global trainer toggle, or in-ROM explanations.
- Changes to move legality, targeting, damage, turn order, or the ordinary trainer-AI scoring algorithm.

## Existing codebase facts

- `src/battle_main.c` computes an AI move/action during `STATE_TURN_START_RECORD` for battlers that satisfy `BattlerHasAi`.
- `ComputeBattleAiScores` in `src/battle_ai_main.c` initializes AI data and returns the selected move/action. It stores the selected target in `gBattleStruct->aiChosenTarget`.
- `src/battle_controller_opponent.c` reads `gBattleStruct->aiMoveOrAction` and `aiChosenTarget` in `OpponentHandleChooseMove` and emits the resulting controller action.
- `src/battle_ai_switch_items.c` handles the earlier `CONTROLLER_CHOOSEACTION` switching/item decision. It is not part of the first moves-only external-action slice.
- `struct Trainer` in `include/data.h` owns the existing `aiFlags`; `src/data/trainers.h` is the current trainer-data definition source.
- The battle harness includes AI-specific tests in `test/battle/ai.c` and supports scripted action/target assertions through macros documented in `include/test/battle.h`.

## Required outputs

1. [`../battle-ai-callgraph.md`](../battle-ai-callgraph.md) — named functions, state transitions, decision values, and the proposed moves-only seam.
2. [`../battle-state.md`](../battle-state.md) — fields to export, source ownership, visibility policy, and explicitly deferred fields.
3. [`../protocol.md`](../protocol.md) — protocol-version-1 request/response fields, memory ownership rules, message/status transitions, validation rules, and rejection behavior.
4. [`../integration-plan.md`](../integration-plan.md) — phase ordering, dependencies, build/test evidence, and rollback/fallback expectations.
5. [`../reviews/2026-07-18-phase-0-discovery-and-contract-baseline-flow-review.md`](../reviews/2026-07-18-phase-0-discovery-and-contract-baseline-flow-review.md) — the `spec-flow-analyzer` review of this specification.
6. [`../plans/2026-07-18-phase-0-discovery-and-contract-baseline.md`](../plans/2026-07-18-phase-0-discovery-and-contract-baseline.md) — the task-level plan created with `writing-plans` after the flow review.

## Contract decisions for this phase

The documentation will use these fixed decisions. They are safe because later phases can extend the contract additively behind a protocol-version bump, while no runtime consumer exists yet.

- Protocol version is `1`.
- The initial decision unit is one opponent battler in a single battle.
- Phase 1 will add `bool8 externalAi:1` to the unused seven-bit padding beside `Trainer.doubleBattle` in `struct Trainer`. It will not consume an `aiFlags` bit, because existing AI flags already use both low-order and high-order bits and represent AI behavior rather than feature opt-in.
- An action is an index into a ROM-produced legal-action array; it is not a raw move ID, target, party index, or item ID supplied by the service.
- A legal action contains a move slot from `0` through `3` and an engine-approved target battler.
- The legal-action producer will use `gBattleMons[battler].moves`, `CheckMoveLimitations(battler, 0, MOVE_LIMITATIONS_ALL)`, and the engine's targeting helpers. It will not reimplement PP, Disable, Encore, target, or fainted-battler rules in the service.
- The mailbox will be a named `EWRAM_DATA` global in the ROM. The mGBA launch tooling will resolve that global's address from the matching ROM map file; the bridge will not scan arbitrary memory or depend on a hard-coded address.
- The ROM validates protocol version, request sequence, response status, action-index bounds, and action membership before applying a response.
- Any missing, stale, malformed, or illegal response selects the already-computed ordinary trainer-AI action and target.
- The service sees only snapshot fields listed in `battle-state.md`; it does not receive hidden opposing data merely because it is available in memory.
- The ROM never waits synchronously for an external response. External-enabled trainers enter a per-frame asynchronous wait state with a `600`-frame budget (ten seconds at 60 FPS); it keeps VBlank and controller processing alive, shows a future "thinking" status, and falls back when the budget expires. The initial mock and deterministic-service phases should answer before the budget; model-backed service latency is measured against it.

## Flows and acceptance criteria

### Flow A: Ordinary trainer battle

The battle reaches `STATE_TURN_START_RECORD`, the existing engine computes the trainer action, and `OpponentHandleChooseMove` emits it. Phase 0 documents this flow without changing it.

**Acceptance criterion:** The call graph names each handoff and states that no Phase 0 source change alters it.

### Flow B: Future external-enabled trainer, valid response

A future ROM hook retains the ordinary action as fallback, produces a request with a sequence number and legal actions, and replaces the fallback only after the response passes all protocol validation.

**Acceptance criterion:** The protocol identifies the producer and consumer of each request/response field and the exact validation order.

### Flow C: Future external-enabled trainer, no usable response

The bridge is absent, disconnected, late, stale, malformed, or returns an illegal action. The ROM continues with the existing precomputed AI result.

**Acceptance criterion:** The protocol and integration plan enumerate each failure state and specify fallback without a busy wait or altered battle mechanics.

## Exit criteria

- All six required documentation outputs exist and link to one another.
- The call graph references the actual current source files and decision-state fields.
- The protocol explicitly defines data ownership, status transitions, validation, and fallback.
- The plan identifies no battle-source changes in Phase 0 and scopes the first code phase to one trainer, singles, and moves only.
- `git diff --check` reports no whitespace errors.

## Review links

- Flow review: [`../reviews/2026-07-18-phase-0-discovery-and-contract-baseline-flow-review.md`](../reviews/2026-07-18-phase-0-discovery-and-contract-baseline-flow-review.md)
- Implementation plan: [`../plans/2026-07-18-phase-0-discovery-and-contract-baseline.md`](../plans/2026-07-18-phase-0-discovery-and-contract-baseline.md)
