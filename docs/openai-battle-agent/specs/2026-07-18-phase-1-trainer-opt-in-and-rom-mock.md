# Phase 1 Specification: Trainer Opt-In and ROM Mock

**Parent design:** [`../2026-07-18-mgba-ai-trainer-design.md`](../2026-07-18-mgba-ai-trainer-design.md)
**Prerequisite phase:** [`2026-07-18-phase-0-discovery-and-contract-baseline.md`](2026-07-18-phase-0-discovery-and-contract-baseline.md)

## Goal

Establish a generic per-trainer `externalAi` opt-in and prove the ROM can replace a flagged single-battle trainer's already-computed move with a deterministic, engine-legal mock response. `TRAINER_CALVIN_1` on Route 102 is the first and only enabled trainer. The ordinary trainer AI remains the fallback for every case where a mock response is unavailable or unusable.

## Scope

### In scope

- Add `externalAi` as a one-bit field in `struct Trainer`'s currently unused seven-bit padding, preserving the structure's existing size and all `aiFlags` meanings.
- Set `.externalAi = TRUE` only for `TRAINER_CALVIN_1` in `src/data/trainers.h`; all other trainers retain the zero-initialized default.
- Add a generic ROM predicate that recognizes an opponent-side AI battler belonging to a flagged trainer in an ordinary single trainer battle.
- Preserve the result of `ComputeBattleAiScores` and its `aiChosenTarget` as the fallback before attempting any mock override.
- Add a test-only mock-response seam that can request a move-slot index for an eligible battler.
- Accept the test mock only when the requested slot is `0` through `3`, contains a move, is not disabled by the engine's current move-limitations mask, and is a direct opponent-targeting move compatible with the existing engine target. An absent, invalid, disabled, or target-incompatible mock response leaves the fallback unchanged.
- Add a focused battle-test directive that selects the trainer ID for an AI single battle, then add tests for an accepted mock move, absent mock fallback, rejected limited-slot fallback, and non-opted-in fallback.
- Build the normal ROM and run the focused test group plus the full battle-test command.

### Out of scope

- EWRAM mailbox allocation, protocol structures, mGBA Lua, sockets, Python, models, prompts, model explanations, or network configuration.
- Waiting for a response, frame budgets, battle UI changes, logging, or player-visible external-AI indicators.
- Service-selected targets, self-targeting support, target validation, a general legal-action list, switches, items, party choices, or double battles.
- Changes to trainer parties, trainer scripts, move effects, damage calculations, target selection, turn order, ordinary AI scoring, or `AI_TrySwitchOrUseItem`.
- Opting in Calvin's rematches (`TRAINER_CALVIN_2` through `TRAINER_CALVIN_5`) or any additional trainer.

## ROM, emulator, and service boundaries

| Component | Phase 1 responsibility | Explicit non-responsibility |
| --- | --- | --- |
| ROM | Stores trainer opt-in data; computes vanilla fallback; accepts only a current legal test mock move slot. | Communicating with an emulator or service; accepting raw moves/targets from an external process. |
| mGBA | None. | Loading scripts, inspecting memory, waiting, or modifying ROM memory. |
| Local service/model | None. | Starting a process, receiving battle state, or making a decision. |
| Battle test runner | Supplies test-only mock responses and verifies visible moves/fallbacks. | Representing the future mailbox protocol. |

## Data and control-flow contract

### Trainer opt-in

`struct Trainer` changes from one named bit plus seven padding bits to two named bits plus six padding bits:

```c
bool8 doubleBattle:1;
bool8 externalAi:1;
u8 padding:6;
```

`externalAi` is configuration, not a vanilla AI behavior flag. It must never be encoded in `aiFlags`, and no existing initializer must be changed solely to add `.externalAi = FALSE`.

### Eligibility

The generic predicate returns true only when all conditions hold:

1. The battler is controlled by existing AI (`BattlerHasAi`) and is on `B_SIDE_OPPONENT`.
2. The battle has `BATTLE_TYPE_TRAINER` and does not have `BATTLE_TYPE_TWO_OPPONENTS`.
3. The battle does not have `BATTLE_TYPE_DOUBLE`, `BATTLE_TYPE_MULTI`, `BATTLE_TYPE_LINK`, `BATTLE_TYPE_RECORDED`, `BATTLE_TYPE_SAFARI`, `BATTLE_TYPE_PALACE`, `BATTLE_TYPE_FRONTIER`, `BATTLE_TYPE_EREADER_TRAINER`, `BATTLE_TYPE_TRAINER_HILL`, or `BATTLE_TYPE_SECRET_BASE`.
4. `gTrainers[gTrainerBattleOpponent_A].externalAi` is true.

The one test-build exception is deliberately narrower than the eligibility predicate: `AI_SINGLE_BATTLE_TEST` uses `SetVariablesForRecordedBattle`, which adds `BATTLE_TYPE_RECORDED`. Under `#if TESTING` only, the hook may continue past that one flag only when `gTestRunnerEnabled` is true and a pending mock slot is present. The test mock is still subject to every other eligibility and move validation rule. A normal ROM, any non-test build, and a test-build recorded battle without that active harness and mock all reject recorded battles.

The predicate is configuration-generic: later data entries may set the same field. Phase 1 enables only `TRAINER_CALVIN_1`.

### Decision sequence

At the existing `STATE_TURN_START_RECORD` seam in `src/battle_main.c`:

1. Run `ComputeBattleAiScores(battler)` exactly as today and assign its result to `gBattleStruct->aiMoveOrAction[battler]`.
2. Treat that move/action and the engine-assigned `gBattleStruct->aiChosenTarget[battler]` as the fallback.
3. If the generic eligibility predicate is false, make no further Phase 1 call.
4. If the fallback is not a move slot from `0` through `3`, make no mock call and retain it unconditionally. This preserves the separate switch/item path and special AI actions.
5. If eligible with a move-slot fallback, ask the test-only mock seam for a move slot. A production ROM reports no response.
6. Validate the response against the current battler: slot range, non-`MOVE_NONE` slot, the freshly computed `CheckMoveLimitations(battler, 0, MOVE_LIMITATIONS_ALL)` mask, and the exact Phase 1 target policy below.
7. On success, replace only `aiMoveOrAction[battler]` with that legal move slot. Keep the target the normal engine selected. Phase 1 accepts only moves whose `gBattleMoves[move].target` is exactly `MOVE_TARGET_SELECTED` and whose existing `aiChosenTarget` is a valid player-side battler. This accepts direct opponent-targeting moves such as `Tackle` and `Odor Sleuth`; Calvin's `Leer` is `MOVE_TARGET_BOTH`, so it remains a valid vanilla fallback but is not mock-selectable. Self, ally, field, random, user-or-selected, and other non-direct categories are rejected. Target selection is deferred to Phase 2.
8. On any rejection or absence, leave both fallback fields unchanged.

Move slots `0` through `3` are already the ordinary move values consumed by `OpponentHandleChooseMove`. Special AI actions (`AI_CHOICE_FLEE`, `AI_CHOICE_WATCH`, and `AI_CHOICE_SWITCH`) are never mock-selectable.

### Test-only mock contract

The test build exposes a narrowly scoped setter/resetter for one pending mock move slot. A new battle-test directive selects the actual opponent trainer ID in the synthetic recorded battle, allowing the focused tests to use `TRAINER_CALVIN_1` and `TRAINER_BILLY` without mutating `const gTrainers`. Its default state is “no response.” The normal ROM compiles the same decision hook but returns `FALSE` before any test-only mock lookup and derives eligibility only from trainer data; it contains no debug menu, persistent save data, or externally writable state.

`BattleTest_Run` resets the mock state at the start of each run, before invoking its test function, so state cannot carry across battles. Each test must also reset the mock state as the first statement in its `GIVEN` block, before configuring any mock response, so parameterized invocations cannot carry state from an earlier run. Because the test runner starts its synthetic battles through `SetVariablesForRecordedBattle`, it necessarily adds `BATTLE_TYPE_RECORDED`; the `#if TESTING` harness exception above permits only an active `gTestRunnerEnabled` run with a pending mock slot. The mock response has no target field; therefore accepted responses use `MOVE_TARGET_SELECTED` opponent-targeting moves. The target-rejection test deliberately supplies a self-targeting move and confirms fallback. Phase 2 replaces this temporary slot-only seam with a ROM-generated legal-action list containing both move slot and target.

## Failure and fallback behavior

| Condition | Required result |
| --- | --- |
| Trainer is not opted in | Existing AI move/action and target are used unchanged. |
| Battle type is outside Phase 1 eligibility | Existing AI path is used unchanged, even if its trainer data has `externalAi`. |
| Recorded battle in a normal ROM, non-test build, inactive test harness, or with no pending mock | Existing AI path is used unchanged. |
| Fallback is switch, item, flee, watch, or any non-move action | Do not query the mock; preserve the existing controller behavior. |
| Test mock has no response | Existing AI move/action and target are used unchanged. |
| Mock slot is outside `0..3` | Reject it; use fallback. |
| Mock slot is empty or currently limited (including zero PP or Disable) | Reject it; use fallback. |
| Mock move is not exactly `MOVE_TARGET_SELECTED`, or the engine target is not a valid player-side battler | Reject it; use fallback. |
| Existing AI chooses switch/item/action before move selection | Leave `AI_TrySwitchOrUseItem` and its controller path unchanged. |
| Production ROM | No mock response exists; an opted-in trainer uses existing AI exactly as before. |

No Phase 1 branch waits, loops for a response, touches emulator memory, or changes an ordinary trainer's scoring. Later mailbox timeouts are not implemented here.

## Tests

Create focused tests adjacent to the existing AI tests. They must use a controlled opponent move set where a successful mock-selected move is visibly distinct from the fallback move; the target-rejection case deliberately supplies a non-direct-target move.

1. **Accepted response:** with Lillipup's `Tackle` in slot 1 and a Ghost player, an eligible configuration with an enabled slot-1 mock visibly uses `Tackle`.
2. **Absent response:** the same eligible configuration with the mock reset visibly uses `Leer`, the known vanilla fallback after `AI_FLAG_CHECK_BAD_MOVE` rejects ineffective Normal-type `Tackle`.
3. **Limited response:** the requested slot-1 `Tackle` has zero PP before action selection; the visible move is `Leer`, never the zero-PP move.
4. **Out-of-range response:** a `MAX_MON_MOVES` mock slot visibly uses the vanilla `Leer` fallback.
5. **Empty response:** a slot-2 mock where Lillipup has `MOVE_NONE` visibly uses the vanilla `Leer` fallback.
6. **Unsupported target:** a slot-1 self-targeting `Rest` mock is otherwise legal but visibly uses the vanilla `Leer` fallback.
7. **Non-opted-in trainer:** a test configuration selects `TRAINER_BILLY`, uses the same Lillipup moves and a valid slot-1 mock, and visibly uses the vanilla `Leer` fallback.
8. **Trainer data:** the focused tests exercise Calvin's enabled production data and Billy's disabled production data without a mutable trainer-table override.

The test plan must identify the exact existing test harness extension needed to simulate `externalAi` without mutating `const gTrainers` at runtime. A test-only eligibility override is allowed only inside `#if TESTING`; it may not affect production ROM behavior.

## Measurable exit criteria

- `sizeof(struct Trainer)` remains unchanged and `aiFlags` values for existing trainers are unchanged.
- `TRAINER_CALVIN_1.externalAi` is true; `TRAINER_BILLY.externalAi` remains false by default; no other trainer is newly opted in.
- In a controlled single battle, a valid direct opponent-targeting test mock causes the expected legal move to be emitted.
- Absent, out-of-range, empty, disabled, and target-incompatible mock slots all produce the precomputed vanilla fallback action and target.
- The Phase 1 hook never queries a mock for a fallback switch/item/special action and never runs for doubles, special battle types, or non-opted-in trainers.
- The normal build and focused Phase 1 command succeed in WSL. No Phase 1 test failure or failure attributable to this slice is permitted. The 2026-07-22 full-suite run's 44 unrelated failures are explicitly accepted by the project owner and recorded, together with the absence of a clean baseline rerun, in the Phase 1 evidence review.
- A manual Route 102 battle against Calvin completes normally in the production ROM, demonstrating fallback before a real bridge exists.

## Documentation links

- Phase 0 flow review: [`../reviews/2026-07-18-phase-0-discovery-and-contract-baseline-flow-review.md`](../reviews/2026-07-18-phase-0-discovery-and-contract-baseline-flow-review.md)
- Phase 1 flow review: [`../reviews/2026-07-18-phase-1-trainer-opt-in-and-rom-mock-flow-review.md`](../reviews/2026-07-18-phase-1-trainer-opt-in-and-rom-mock-flow-review.md)
- Phase 1 implementation plan: [`../plans/2026-07-18-phase-1-trainer-opt-in-and-rom-mock.md`](../plans/2026-07-18-phase-1-trainer-opt-in-and-rom-mock.md)
- Phase 1 build and test evidence: [`../reviews/2026-07-18-phase-1-build-and-test-evidence.md`](../reviews/2026-07-18-phase-1-build-and-test-evidence.md)
