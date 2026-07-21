# Phase 1 Flow Review: Trainer Opt-In and ROM Mock

**Specification reviewed:** [`../specs/2026-07-18-phase-1-trainer-opt-in-and-rom-mock.md`](../specs/2026-07-18-phase-1-trainer-opt-in-and-rom-mock.md)

**Related documents:** [implementation plan](../plans/2026-07-18-phase-1-trainer-opt-in-and-rom-mock.md) · [build and test evidence](2026-07-18-phase-1-build-and-test-evidence.md)

## Codebase grounding

- `struct Trainer` in `include/data.h` has `doubleBattle:1` followed by seven unused bits, so an `externalAi:1` field can retain the byte layout and does not need an `aiFlags` bit.
- `TRAINER_CALVIN_1` is declared in `src/data/trainers.h`, is started by `Route102_EventScript_Calvin` in `data/maps/Route102/scripts.inc`, and owns one level-6 Lillipup. `Tackle` and `Odor Sleuth` are `MOVE_TARGET_SELECTED`; `Leer` is `MOVE_TARGET_BOTH` and therefore remains fallback-only in Phase 1.
- `STATE_TURN_START_RECORD` in `src/battle_main.c` stores `ComputeBattleAiScores(battler)` in `gBattleStruct->aiMoveOrAction[battler]`; the same computation writes `gBattleStruct->aiChosenTarget[battler]`.
- `include/battle_ai_main.h` defines ordinary move choices as slots `0` through `3`; `AI_CHOICE_FLEE`, `AI_CHOICE_WATCH`, and `AI_CHOICE_SWITCH` are distinct non-move values.
- `AI_TrySwitchOrUseItem` is reached from the opponent controller's action-selection path, before `OpponentHandleChooseMove`; it must not be intercepted by a moves-only hook.
- `AI_SINGLE_BATTLE_TEST` builds synthetic opponent parties and starts with `TRAINER_LEAF` as its recorded opponent ID. `SetVariablesForRecordedBattle` necessarily adds `BATTLE_TYPE_RECORDED`. The test-only seam must therefore allow that one flag only when `gTestRunnerEnabled` is true and a pending test mock exists; a non-test ROM and all other recorded cases retain the normal rejection.

## User flows

```mermaid
flowchart TD
  A["AI battler reaches STATE_TURN_START_RECORD"] --> B["Compute vanilla action and target"]
  B --> C{"Phase 1 eligible?"}
  C -- "No" --> V["Emit unchanged vanilla action"]
  C -- "Yes" --> D{"Fallback is an ordinary move slot 0..3?"}
  D -- "No: switch/item/special action" --> V
  D -- "Yes" --> E{"Test mock response present?"}
  E -- "No" --> V
  E -- "Yes" --> F{"Slot range, non-empty, non-limited, direct selected opponent target?"}
  F -- "No" --> V
  F -- "Yes" --> G["Replace move slot only; retain engine target"]
  G --> H["Opponent controller emits move"]
  V --> H
```

1. **Calvin production-ROM battle.** Route 102 starts `TRAINER_CALVIN_1`. He is opted in, but production code has no mock response, so the precomputed vanilla move and target are emitted. The battle completes normally.
2. **Eligible test mock.** A synthetic single AI battle selects `TRAINER_CALVIN_1` in its recorded harness battle and submits a legal `MOVE_TARGET_SELECTED` move slot. Under `#if TESTING`, `gTestRunnerEnabled` plus that pending mock permits the harness's otherwise excluded `BATTLE_TYPE_RECORDED` flag. The hook replaces only the move slot after confirming its precomputed target is player-side; the target remains engine-owned. The visible move proves the seam works.
3. **Absent or invalid mock.** The mock is absent, out of range, empty, limited by the engine, self/ally/field/non-direct-targeting, or target-incompatible. The hook rejects it and leaves both fallback values unchanged; an absent mock also does not activate the recorded-harness exception.
4. **Non-opted-in or unsupported battle.** A normal trainer, double, multi, special facility, Palace, link, or wild battle skips the hook and follows the existing path. Recorded battles also skip it unless they are the active `#if TESTING` harness with a pending mock.
5. **Vanilla switch/item path.** The ordinary controller can choose a switch/item or `AI_CHOICE_SWITCH`; the Phase 1 hook never replaces a non-move fallback, so the existing behavior remains authoritative.

## Gaps

### Critical

1. **The initial specification permitted a mock move to replace a fallback switch or special action.** `ComputeBattleAiScores` can return `AI_CHOICE_SWITCH` rather than a move slot. Replacing that value would violate the stated moves-only boundary and can interfere with the separate `AI_TrySwitchOrUseItem` path.

   **Resolution:** attempt a mock only when the precomputed fallback is an ordinary move slot `0..3`; otherwise retain the fallback unconditionally.

2. **Keeping the vanilla target is safe only for an explicitly bounded move set.** The initial text allowed any current legal slot but did not prove that the fallback target was compatible with that move. This would be unsafe for self-target or unusual target categories.

   **Resolution:** Phase 1 accepts mock slots only when `gBattleMoves[move].target == MOVE_TARGET_SELECTED` and the normal engine target is a valid player-side battler. This accepts direct moves such as `Tackle` and `Odor Sleuth`; `Leer` is `MOVE_TARGET_BOTH`, so it remains a vanilla fallback but is not mock-selectable. Self, ally, field, random, user-or-selected, and other non-direct categories are rejected. A general move-slot/target action list is deferred to Phase 2.

### Important

1. **The test runner starts AI battles as `TRAINER_LEAF`.** `AI_SINGLE_BATTLE_TEST` configures synthetic Pokémon and AI flags, so it would otherwise never reach Calvin's real data flag.

   **Resolution:** add a `TRAINER_OPPONENT(trainerId)` test directive that changes only `DATA.recordedBattle.opponentA` while the test is being configured. It is valid only in AI single-battle tests and uses production `gTrainers` data after normal battle initialization. No production eligibility override is needed.

2. **The special-battle exclusion list must be code-expressible.** “Other special battle” would invite inconsistent future conditions.

   **Resolution:** derive a single `IsExternalAiEligibleBattler` predicate that requires `BATTLE_TYPE_TRAINER` and rejects the concrete flags listed in the specification: `BATTLE_TYPE_DOUBLE`, `BATTLE_TYPE_MULTI`, `BATTLE_TYPE_LINK`, `BATTLE_TYPE_RECORDED`, `BATTLE_TYPE_SAFARI`, `BATTLE_TYPE_PALACE`, `BATTLE_TYPE_FRONTIER`, `BATTLE_TYPE_EREADER_TRAINER`, `BATTLE_TYPE_TRAINER_HILL`, `BATTLE_TYPE_SECRET_BASE`, and `BATTLE_TYPE_TWO_OPPONENTS`. The implementation plan must verify their actual constant names.

3. **`CheckMoveLimitations` must be read at the decision seam, not inferred from AI scores.** A nonzero AI score is not a legal-action contract.

   **Resolution:** recompute `CheckMoveLimitations(battler, 0, MOVE_LIMITATIONS_ALL)` immediately before accepting the mock, then reject a bit set for the requested slot. The test disables the selected move through existing battle-test facilities and asserts fallback.

### Minor

1. **Calvin's rematches are separate IDs.** The user selected the first Route 102 encounter, not all Calvin battles.

   **Resolution:** set only `TRAINER_CALVIN_1.externalAi = TRUE`; do not alter `TRAINER_CALVIN_2` through `TRAINER_CALVIN_5`.

2. **Build-helper compatibility fixes are present in the working tree.** `tools/mapjson/json11.cpp` and `src/secret_base.c` contain prior local build fixes unrelated to Phase 1.

   **Resolution:** do not bundle or revert them in Phase 1. The plan's verification records their presence and limits Phase 1 source edits to the listed files.

## Questions and settled defaults

1. **When an opted-in trainer has no bridge yet, what happens?** The production ROM reports no mock response and emits the precomputed vanilla fallback. This is safe because no external state is required.
2. **Can any trainer use the field later?** Yes. The data field and production predicate are generic; Phase 1 enables only `TRAINER_CALVIN_1` to keep acceptance testing controlled.
3. **Can a test response choose a target?** No. It supplies a move slot only for `MOVE_TARGET_SELECTED` fixtures whose normal target is player-side. Phase 2 owns the first action format with explicit target validation.
4. **Does Phase 1 change switching or items?** No. A non-move fallback skips mock handling and the existing controller path continues unchanged.

## Recommended next steps

1. Amend the Phase 1 specification with the two critical resolutions and the precise test-only override boundary.
2. Recheck the amended specification for the generic field, Calvin-only data change, slot-only temporary contract, and no-response fallback.
3. After the user approves the reviewed specification, write the task-level implementation plan in `docs/openai-battle-agent/plans/`.
