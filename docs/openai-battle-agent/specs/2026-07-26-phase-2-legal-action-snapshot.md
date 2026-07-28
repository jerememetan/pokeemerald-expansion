# Phase 2 Specification: Legal-Action Snapshot

**Status:** Implemented and verified 2026-07-28
**Parent roadmap:** [`../2026-07-18-mgba-ai-trainer-design.md`](../2026-07-18-mgba-ai-trainer-design.md)  
**Prerequisite:** [Phase 1 build and test evidence](../reviews/2026-07-18-phase-1-build-and-test-evidence.md)

## Goal

Publish a compact, versioned, ROM-owned snapshot and legal move-action list for one opted-in opponent in a standard trainer single battle. The snapshot is the sole future input to the mGBA bridge and local decision service. It must never change the current turn's vanilla choice in Phase 2.

## Scope

### In scope

- A fixed-layout `EWRAM_DATA` mailbox with protocol magic, version, request status, sequence number, requesting battler, visible battle snapshot, and legal actions. Its C definition uses no bitfields or pointers and has compile-time size/offset assertions recorded beside the definition.
- One request publication after ordinary AI has computed its fallback action and target for an eligible `externalAi` trainer.
- Trainer single battles only; opponent-side battlers only; move actions only.
- Snapshot fields: requesting battler, turn sequence, active battlers' species/HP/max HP/status/stat stages, requester's move IDs and PP, weather, terrain, field status, and both side-status masks.
- A legal-action list whose entries contain a stable action index, a move slot, and the target battler the existing opponent controller will emit in a single battle.
- Test-only inspection helpers and focused battle tests for action construction and stale request replacement.

### Out of scope

- mGBA Lua, sockets, a Python service, model calls, response polling, frame waits, UI, audio, or a pause state.
- Applying any mailbox response to `aiMoveOrAction` or `aiChosenTarget`.
- Switches, battle items, doubles, multi battles, partner targets, wild battles, Palace, link/recorded/facility variants, and broad trainer rollout.
- Hidden opponent party data, held items, abilities, RNG state, vanilla AI simulation values, damage predictions, raw pointers, and scripts.

## ROM, emulator, and service boundaries

| Component | Phase 2 responsibility | Must not do |
|---|---|---|
| ROM | Own and populate the mailbox, compute legal actions from live engine state, retain vanilla AI fallback. | Wait for, read, or apply an external response. |
| mGBA bridge | None in this phase; a later phase may read the named mailbox symbol. | Be required for a playable battle. |
| Local service/model | None in this phase. | Receive hidden state or control the ROM. |

## Eligibility and publication flow

1. The existing AI path computes `aiMoveOrAction` and `aiChosenTarget` first.
2. The ROM publishes only when all of the following are true: the battler has AI, is opponent-side, the battle is a trainer single battle, the trainer's `externalAi` bit is set, no Phase 1-excluded battle flag is active, and the already-computed fallback is a move slot `0` through `MAX_MON_MOVES - 1`. Switch/item/special fallbacks never publish a request.
3. Before writing a request, the ROM increments the mailbox request sequence, clears response fields to `NONE`, writes the complete snapshot and legal-action array, then sets request status to `PENDING` last.
4. The current turn continues immediately on the existing controller path. Publishing must not alter `aiMoveOrAction`, `aiChosenTarget`, switching, items, target emission, timing, or UI.
5. The next eligible request supersedes an unconsumed earlier request by using a new sequence. Phase 2 neither reads nor accepts a response.

The battle-test runner necessarily marks its synthetic AI battles as recorded. Under `#if TESTING` only, an active `gTestRunnerEnabled` run may publish a request despite `BATTLE_TYPE_RECORDED`; release builds always exclude recorded battles. This exception is publication-only and does not permit a response to affect a turn.

The ROM initializes the mailbox itself before its first request by clearing it and then writing valid magic/version and `IDLE`. A non-eligible turn must not increment the request sequence or overwrite a pending eligible request.

## Data contract

All fields use fixed-width project types and are explicitly initialized before publication. No pointers, variable-length data, or compiler-dependent `bool` values are exported.

```text
BattleAgentMailboxV1
  magic: u32
  protocolVersion: u16                 // 1
  requestStatus: u8                    // IDLE or PENDING in Phase 2
  responseStatus: u8                   // always NONE in Phase 2
  requestSequence: u32                 // monotonically increments per published request
  requestingBattler: u8
  battleMode: u8                       // trainer-single only
  turnSequence: u16                    // increments per published request in Phase 2
  snapshot: BattleAgentSnapshotV1
  legalActionCount: u8                 // 0..MAX_MON_MOVES
  legalActions: BattleAgentLegalActionV1[MAX_MON_MOVES]
  responseSequence: u32                // cleared in Phase 2
  responseLegalActionIndex: u8         // cleared in Phase 2

BattleAgentSnapshotV1
  battlers[MAX_BATTLERS_COUNT]:
    species: u16
    hp: u16
    maxHp: u16
    status1: u32
    statStages[NUM_BATTLE_STATS]: u8
  requesterMoves[MAX_MON_MOVES]:
    move: u16
    pp: u8
  weather: u16
  terrain: u8
  fieldStatuses: u32
  sideStatuses[NUM_BATTLE_SIDES]: u32

BattleAgentLegalActionV1
  actionIndex: u8
  moveSlot: u8
  targetBattler: u8
```

`actionIndex` is dense and equals the entry's array index. A future bridge/service returns only this index; it never sends a move ID or target chosen independently.

## Legal-action construction

The producer recomputes `CheckMoveLimitations(requester, 0, MOVE_LIMITATIONS_ALL)` at request construction. It adds exactly one action for each requester move slot that is non-empty and not limited. It obtains the effective target category through `GetBattlerMoveTargetType(requester, move)`, not directly from `gBattleMoves[move].target`, so dynamic target rules such as Curse and Expanding Force are reflected. Every generated target is normalized to the target the existing single-battle opponent controller would emit:

- `MOVE_TARGET_USER` and `MOVE_TARGET_USER_OR_SELECTED` target the requester.
- `MOVE_TARGET_SELECTED`, `MOVE_TARGET_DEPENDS`, `MOVE_TARGET_RANDOM`, `MOVE_TARGET_BOTH`, `MOVE_TARGET_FOES_AND_ALLY`, and `MOVE_TARGET_OPPONENTS_FIELD` target the sole live player-side battler.
- A target category that cannot be normalized safely in a trainer single battle (including ally-only or all-battler categories) produces no action for that slot. The vanilla fallback remains available for it.

The producer never emits an action for a fainted target. In a valid single battle, all emitted target battlers must be in range, alive, and either the requester or the live player-side battler. Legal-action construction must not mutate global target state.

## Failure and fallback behavior

| Condition | Required behavior |
|---|---|
| Battle/battler/trainer is ineligible | Do not write a request; leave the current mailbox request unchanged. |
| No legal move slots | Publish an empty action list only if the battle still reaches ordinary move selection; do not invent an action. Vanilla AI remains authoritative. |
| Unsupported target category or invalid/fainted target | Omit that move slot from the list; leave vanilla AI unchanged. |
| Mailbox already `PENDING` | Replace it only when a new eligible turn produces a new sequence; no wait or retry loop. |
| Any future response fields contain data | Clear them before publication; Phase 2 never consumes them. |
| Future bridge/service absent or corrupt | No behavior exists in Phase 2, so gameplay continues unchanged. |

## Tests

Focused tests must prove:

1. Calvin's eligible trainer single battle publishes a `PENDING` request after vanilla scoring.
2. A normal trainer and every excluded battle type leave the mailbox sequence/status unchanged.
3. A usable selected-target move produces its own move-slot/action-index entry with the player battler target.
4. A usable self-target move produces an entry targeting the requester.
5. Empty and zero-PP/limited slots produce no entry.
6. The target-normalization helper rejects an invalid or fainted player target in a direct `#if TESTING` helper test; its caller produces no opponent-targeting entry.
7. A later eligible turn replaces a pending request with a larger sequence and cleared response fields.
8. Publication leaves the emitted vanilla move and target unchanged.

## Measurable exit criteria

- The mailbox symbol is fixed-layout, EWRAM-resident, initialized with protocol version 1, and contains no pointers.
- Only standard, single, opted-in opponent trainer turns publish requests.
- Every emitted legal action uses an unmasked non-empty move slot and a live normalized target.
- The focused Phase 2 tests pass, along with the existing Phase 1 external-AI tests.
- A normal Calvin Route 102 battle remains playable without mGBA Lua or a service and does not wait for a response.

## Links

- [Parent roadmap](../2026-07-18-mgba-ai-trainer-design.md)
- [Battle state inventory](../battle-state.md)
- [Protocol v1](../protocol.md)
- [Phase 1 specification](2026-07-18-phase-1-trainer-opt-in-and-rom-mock.md)
- [Phase 2 flow review](../reviews/2026-07-26-phase-2-legal-action-snapshot-flow-review.md)
- [Phase 2 implementation plan](../plans/2026-07-26-phase-2-legal-action-snapshot.md)
- [Phase 2 build and test evidence](../reviews/2026-07-28-phase-2-build-and-test-evidence.md)
