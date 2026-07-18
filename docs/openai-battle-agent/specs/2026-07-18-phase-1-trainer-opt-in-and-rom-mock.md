# Phase 1 Specification: Trainer Opt-In and ROM Mock

**Parent design:** [`../2026-07-18-mgba-ai-trainer-design.md`](../2026-07-18-mgba-ai-trainer-design.md)
**Prerequisite phase:** [`2026-07-18-phase-0-discovery-and-contract-baseline.md`](2026-07-18-phase-0-discovery-and-contract-baseline.md)

## Goal

Establish a generic per-trainer `externalAi` opt-in and prove the ROM can replace a flagged single-battle trainer's already-computed move with a deterministic, engine-legal mock response. `TRAINER_CALVIN_1` on Route 102 is the first and only enabled trainer. The ordinary trainer AI remains the fallback for every case where a mock response is unavailable or unusable.

## Scope

### In scope

- Add `externalAi` as a one-bit field in `struct Trainer`'s currently unused seven-bit padding, preserving the structure's existing size and all `aiFlags` meanings.
- Set `.externalAi = TRUE` only for `TRAINER_CALVIN_1` in `src/data/trainers.h`; all other trainers retain the zero-initialized default.
- Add a generic ROM predicate that recognizes an AI-controlled opponent battler belonging to a flagged trainer in an ordinary single trainer battle.
- Preserve the result of `ComputeBattleAiScores` and its `aiChosenTarget` as the fallback before attempting any mock override.
- Add a test-only mock-response seam that can request a move-slot index for an eligible battler.
- Accept the test mock only when the requested slot is `0` through `3`, contains a move, and is not disabled by the engine's current move-limitations mask. An absent, invalid, or disabled mock response leaves the fallback unchanged.
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

1. The battler is controlled by existing opponent AI (`BattlerHasAi`).
2. The battle has `BATTLE_TYPE_TRAINER` and does not have `BATTLE_TYPE_TWO_OPPONENTS`.
3. The battle does not have `BATTLE_TYPE_DOUBLE`, `BATTLE_TYPE_MULTI`, `BATTLE_TYPE_LINK`, `BATTLE_TYPE_RECORDED`, `BATTLE_TYPE_SAFARI`, `BATTLE_TYPE_PALACE`, `BATTLE_TYPE_FRONTIER`, `BATTLE_TYPE_EREADER_TRAINER`, `BATTLE_TYPE_TRAINER_HILL`, or `BATTLE_TYPE_SECRET_BASE`.
4. `gTrainers[gTrainerBattleOpponent_A].externalAi` is true.

The predicate is configuration-generic: later data entries may set the same field. Phase 1 enables only `TRAINER_CALVIN_1`.

### Decision sequence

At the existing `STATE_TURN_START_RECORD` seam in `src/battle_main.c`:

1. Run `ComputeBattleAiScores(battler)` exactly as today and assign its result to `gBattleStruct->aiMoveOrAction[battler]`.
2. Treat that move/action and the engine-assigned `gBattleStruct->aiChosenTarget[battler]` as the fallback.
3. If the generic eligibility predicate is false, make no further Phase 1 call.
4. If the fallback is not a move slot from `0` through `3`, make no mock call and retain it unconditionally. This preserves the separate switch/item path and special AI actions.
5. If eligible with a move-slot fallback, ask the test-only mock seam for a move slot. A production ROM reports no response.
6. Validate the response against the current battler: slot range, non-`MOVE_NONE` slot, the freshly computed `CheckMoveLimitations(battler, 0, MOVE_LIMITATIONS_ALL)` mask, and Phase 1's opponent-targeting test-fixture contract.
7. On success, replace only `aiMoveOrAction[battler]` with that legal move slot. Keep the target the normal engine selected. Phase 1 accepts only Calvin-compatible opponent-targeting moves (`Leer`, `Tackle`, and `Odor Sleuth`) and test fixtures restricted to that target category; target selection is deferred to Phase 2.
8. On any rejection or absence, leave both fallback fields unchanged.

Move slots `0` through `3` are already the ordinary move values consumed by `OpponentHandleChooseMove`. Special AI actions (`AI_CHOICE_FLEE`, `AI_CHOICE_WATCH`, and `AI_CHOICE_SWITCH`) are never mock-selectable.

### Test-only mock contract

The test build exposes a narrowly scoped setter/resetter for one pending mock move slot. A new battle-test directive selects the actual opponent trainer ID in the synthetic recorded battle, allowing the focused tests to use `TRAINER_CALVIN_1` and `TRAINER_BILLY` without mutating `const gTrainers`. Its default state is “no response.” The normal ROM compiles the same decision hook but always receives “no response” and derives eligibility only from trainer data; it contains no debug menu, persistent save data, or externally writable state.

Each test must reset the mock state in `FINALLY` so state cannot carry to another test. The mock response has no target field; therefore tests use opponent-targeting moves only. Phase 2 replaces this temporary slot-only seam with a ROM-generated legal-action list containing both move slot and target.

## Failure and fallback behavior

| Condition | Required result |
| --- | --- |
| Trainer is not opted in | Existing AI move/action and target are used unchanged. |
| Battle type is outside Phase 1 eligibility | Existing AI path is used unchanged, even if its trainer data has `externalAi`. |
| Fallback is switch, item, flee, watch, or any non-move action | Do not query the mock; preserve the existing controller behavior. |
| Test mock has no response | Existing AI move/action and target are used unchanged. |
| Mock slot is outside `0..3` | Reject it; use fallback. |
| Mock slot is empty or currently limited (including zero PP or Disable) | Reject it; use fallback. |
| Existing AI chooses switch/item/action before move selection | Leave `AI_TrySwitchOrUseItem` and its controller path unchanged. |
| Production ROM | No mock response exists; an opted-in trainer uses existing AI exactly as before. |

No Phase 1 branch waits, loops for a response, touches emulator memory, or changes an ordinary trainer's scoring. Later mailbox timeouts are not implemented here.

## Tests

Create focused tests adjacent to the existing AI tests. They must use a controlled opponent move set where the mock-selected move is visibly distinct from the fallback move and all moves target the opponent.

1. **Accepted response:** an eligible test configuration with an enabled mock for a legal `Tackle` slot visibly uses `Tackle`.
2. **Absent response:** the same eligible configuration with the mock reset uses its known vanilla fallback move.
3. **Limited response:** the requested mock slot has zero PP before action selection; the visible move is the known vanilla fallback, never the zero-PP move.
4. **Non-opted-in trainer:** a test configuration selects `TRAINER_BILLY`, uses identical moves and a valid mock, and visibly uses its known vanilla fallback.
5. **Trainer data:** the focused tests exercise Calvin's enabled production data and Billy's disabled production data without a mutable trainer-table override.

The test plan must identify the exact existing test harness extension needed to simulate `externalAi` without mutating `const gTrainers` at runtime. A test-only eligibility override is allowed only inside `#if TESTING`; it may not affect production ROM behavior.

## Measurable exit criteria

- `sizeof(struct Trainer)` remains unchanged and `aiFlags` values for existing trainers are unchanged.
- `TRAINER_CALVIN_1.externalAi` is true; `TRAINER_BILLY.externalAi` remains false by default; no other trainer is newly opted in.
- In a controlled single battle, a valid test mock causes the expected legal move to be emitted.
- Absent, out-of-range, empty, and disabled mock slots all produce the precomputed vanilla fallback action and target.
- The Phase 1 hook never queries a mock for a fallback switch/item/special action and never runs for doubles, special battle types, or non-opted-in trainers.
- `make -j2`, the focused Phase 1 test command, and `make check` succeed in WSL.
- A manual Route 102 battle against Calvin completes normally in the production ROM, demonstrating fallback before a real bridge exists.

## Documentation links

- Phase 0 flow review: [`../reviews/2026-07-18-phase-0-discovery-and-contract-baseline-flow-review.md`](../reviews/2026-07-18-phase-0-discovery-and-contract-baseline-flow-review.md)
- Phase 1 flow review: [`../reviews/2026-07-18-phase-1-trainer-opt-in-and-rom-mock-flow-review.md`](../reviews/2026-07-18-phase-1-trainer-opt-in-and-rom-mock-flow-review.md)
- Phase 1 implementation plan: [`../plans/2026-07-18-phase-1-trainer-opt-in-and-rom-mock.md`](../plans/2026-07-18-phase-1-trainer-opt-in-and-rom-mock.md)
