# Phase 2 Flow Review: Legal-Action Snapshot

**Specification reviewed:** [`../specs/2026-07-26-phase-2-legal-action-snapshot.md`](../specs/2026-07-26-phase-2-legal-action-snapshot.md)  
**Parent roadmap:** [`../2026-07-18-mgba-ai-trainer-design.md`](../2026-07-18-mgba-ai-trainer-design.md)

## Codebase grounding

- `STATE_TURN_START_RECORD` in `src/battle_main.c` computes the vanilla action with `ComputeBattleAiScores` before Phase 1's post-score hook. `aiMoveOrAction` can be a move slot or `AI_CHOICE_SWITCH`, so a moves-only request must be gated after that computation.
- `BattleAI_SetupAIData` already derives `AI_DATA->moveLimitations` with `CheckMoveLimitations`, but the producer must recompute the mask rather than expose stale AI scratch state.
- `OpponentHandleChooseMove` in `src/battle_controller_opponent.c` forces `MOVE_TARGET_USER` and `MOVE_TARGET_USER_OR_SELECTED` to the requester and normalizes `MOVE_TARGET_BOTH` to a player battler. `GetMoveTarget` and `GetBattlerMoveTargetType` in `src/battle_util.c` supply the engine's dynamic target semantics.
- `gBattleMons`, `gBattleWeather`, `gBattleTerrain`, `gFieldStatuses`, and `gSideStatuses` are existing EWRAM battle state. Existing test globals use `EWRAM_DATA`; ordinary initialized `.data` is discarded by the test linker.
- The battle-test runner starts synthetic AI tests with `BATTLE_TYPE_RECORDED`; Phase 1 already contains a narrowly scoped `TESTING` runner exception. Phase 2 needs an analogous publication-only exception to test the producer without weakening a release ROM.

## User flows

1. **Eligible Calvin single battle.** Vanilla AI produces its move and target. The producer initializes or refreshes the mailbox, snapshots visible state, enumerates legal actions, sets `PENDING` last, and returns immediately to the unchanged controller path.
2. **Self-targeting usable move.** The producer retains the requester move slot and assigns requester as the action target. The future service can select it by action index without inventing a target.
3. **Opponent-targeting usable move.** The producer normalizes the effective target category to the sole live player battler and emits a move-slot/action-index entry.
4. **Unavailable or unsupported move.** An empty, limited, invalid-target, or non-normalizable-target move has no action entry. The existing vanilla choice continues untouched.
5. **Later eligible turn.** The next publication clears response fields, increments the sequence, replaces the prior snapshot/actions, and never reads a stale response.
6. **Ordinary/special battle.** An unconfigured trainer, non-move vanilla fallback, double, link, recorded release battle, or any excluded mode performs no mailbox mutation.

## Gaps found and resolved

### Critical

1. **The first draft did not exclude a vanilla switch or special fallback.** `ComputeBattleAiScores` can return values outside move slots. Publishing a moves-only request for that turn would create a future race with the switch/item controller. The specification now requires a move-slot fallback before publication.

2. **The first draft relied on raw move target data.** `GetBattlerMoveTargetType` can change target semantics at runtime, including Curse and Expanding Force. The specification now requires the effective helper and explicitly excludes unnormalizable categories.

3. **The test harness marks every synthetic AI battle as recorded.** A production-only recorded exclusion would make the producer untestable. The specification now allows publication only under `#if TESTING && gTestRunnerEnabled`; release ROMs still reject every recorded battle and no response is applied.

### Important

1. **The fixed mailbox needed an initialization and layout rule.** `EWRAM_DATA` variables are not a bridge contract by implication. The specification now requires ROM-side initialization before the first request plus no pointers/bitfields and compile-time layout assertions.

2. **A fainted target is difficult to reach in a controller-level single-battle test.** The specification now requires a narrow test-only helper test for target normalization rather than pretending a normal turn can select a fainted opponent.

3. **An unconsumed request had no replacement policy.** The specification now explicitly supersedes it only on the next eligible turn with a new sequence and cleared response fields; it never blocks.

### Minor

1. **`turnSequence` is a publication counter in Phase 2, not an engine-wide turn counter.** The field is retained because it gives the bridge future debugging context. The implementation plan must name and document it as such.

## Questions resolved by safe defaults

1. **Does Phase 2 apply a mailbox response?** No. Applying responses belongs after bridge/service sequencing is specified.
2. **Does Phase 2 publish requests for every trainer?** No. It uses the existing `externalAi` field and enables only Calvin.
3. **Does an unsupported but otherwise usable move invalidate the turn?** No. It is omitted from the external list; normal AI may still choose it.

## Recommended next steps

1. Keep Phase 2 as one vertical slice: mailbox initialization, snapshot/action production, and test inspection only.
2. Write a Phase 2 implementation plan that names the mailbox module, exact constants/structs, producer seam, and test accessors.
3. Do not add polling, Lua, sockets, or model code until the mailbox producer has focused build/test evidence.

## Links

- [Phase 2 specification](../specs/2026-07-26-phase-2-legal-action-snapshot.md)
- [Phase 2 implementation plan](../plans/2026-07-26-phase-2-legal-action-snapshot.md)
- [Phase 1 flow review](2026-07-18-phase-1-trainer-opt-in-and-rom-mock-flow-review.md)
- [Protocol v1](../protocol.md)
