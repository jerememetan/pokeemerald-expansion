# Phase 7B Specification: Coordinated External AI for Two-Trainer Doubles

**Status:** Flow-reviewed design; ready for implementation planning

**Roadmap:** [External AI Trainer Integration Plan](../integration-plan.md)

**Predecessor evidence:** [Phase 7A evidence](../reviews/2026-08-02-phase-7a-single-trainer-doubles-evidence.md)

**Flow review:** [Phase 7B flow review](../reviews/2026-08-03-phase-7b-two-trainer-doubles-flow-review.md)

**Implementation plan:** [Phase 7B plan](../plans/2026-08-04-phase-7b-two-trainer-doubles.md)

## Goal

Allow one local external agent decision to select the two opponent actions in a
normal `BATTLE_TYPE_TWO_OPPONENTS` battle, where two independently encountered
trainers enter one double battle. The decision can coordinate both Pokémon, but
every voluntary switch remains restricted to the reserve party owned by that
action's originating trainer.

## Scope

### In scope

- A single atomic two-action request for the opponent-left and opponent-right
  battlers in a `BATTLE_TYPE_TWO_OPPONENTS` trainer double.
- Two separately owned three-slot opposing trainer parties, published together
  as a six-record snapshot with explicit owner-battler metadata.
- ROM-generated move and voluntary-switch action lists, with each switch list
  limited to its actor's own three-slot party range.
- The existing model tools, extended only so `get_party()` identifies the owner
  of each party record. The agent chooses only published action indexes through
  one terminal `choose_actions` call.
- Atomic validation and commit of exactly one action for each controlled
  battler, including a coordinated move/switch or two switches.
- Existing thinking status, 1,800-frame normal-ROM deadline, and unchanged
  vanilla fallback.

### Out of scope

- Two independent model calls, one per trainer; the external layer makes one
  coordinated decision per turn.
- Trainer items, player reserves, player partners, multi/triple/link/wild or
  facility battles, forced replacement after a faint, and battle-mechanics
  changes.
- Cross-trainer switches, raw moves, targets, party slots, controller values,
  direct memory writes, or state-changing model tools.
- Changes to Phase 7A's one-trainer-double behavior.

## Eligibility and ownership

Phase 7B is eligible only when all of the following are true:

1. The battle is a trainer double with `BATTLE_TYPE_TWO_OPPONENTS` and exactly
   four active battlers.
2. Opponent-left and opponent-right are alive, AI-controlled, and have ordinary
   voluntary move selections; neither is absent, forced to replace, recharging,
   or locked into a multi-turn action.
3. Both `gTrainers[gTrainerBattleOpponent_A].externalAi` and
   `gTrainers[gTrainerBattleOpponent_B].externalAi` are true.

Opponent-left owns party slots 0–2 and opponent-right owns slots 3–5, using
the engine's existing `GetAIPartyIndexes` ranges. A request is not emitted if
either trainer is not opted in; in that mixed configuration both opponents use
the ordinary vanilla AI for the turn. This avoids a coordinated external
decision controlling or constraining a trainer who did not opt in.

The ROM first obtains each battler's ordinary vanilla decision. The
opponent-right battler is the designated publisher because the normal action
selection loop computes opponent-left first. Only when opponent-right reaches
the decision point, and both stored vanilla decisions are present, does the ROM
snapshot them as the pair fallback, place both opponent controllers in the
external-wait state, and publish one request. It never emits one request per
trainer or lets the left controller dispatch its ordinary choice before the
atomic request resolves.

## ROM, emulator, and service contract

Phase 7B changes BAGB/4 to **BAGB/5**. The C mailbox, Lua bridge constants,
generated mailbox configuration, Python parser/formatter, and source tests
must change together. Any version, magic, or fixed-length mismatch is rejected
and reaches vanilla fallback.

The fixed mailbox payload remains within the current 1,480-byte EWRAM mailbox
budget. The existing two-byte reserved field in each party snapshot is defined
in BAGB/5 as:

```text
owner_battler: u8     // opponent-left or opponent-right
reserved: u8          // must be zero
```

Thus the binary record size is unchanged, but the protocol version prevents an
older bridge/service from interpreting the new semantics. is_active is true
for either active opponent's actual party record, not merely for the requester.
For a BAGB/5 one-trainer double, every record instead uses
owner_battler = BATTLE_AGENT_ACTION_NONE, and the service labels it shared;
Phase 7A's six-slot shared-party behavior is otherwise unchanged.

A BAGB/5 two-trainer-double request contains:

```text
battle_mode = TRAINER_TWO_OPPONENT_DOUBLE
controlled_battlers = [opponent-left, opponent-right]
battler_count = 4
party[0..2].owner_battler = opponent-left
party[3..5].owner_battler = opponent-right
```

It retains the four active battlers, all active move records, field and side
state, and the two actor-keyed legal-action lists from BAGB/4. It introduces
no player-party records.

For get_party(), the Python service returns all six records with owner_battler
and a stable owner label (opponent-left, opponent-right, or shared for a
one-trainer double). It never reports a party record as switchable unless a
corresponding actor-specific ROM legal action has been published.
`list_legal_actions` remains the source of truth and already includes move
facts. `choose_actions` must contain exactly the two controlled battlers,
once each.

## Validation, commit, and fallback

Before commit, the ROM rechecks request sequence, complete actor coverage,
each legal-action index, move limitations, target legality, and the current
state of every selected reserve. For a switch, `GetAIPartyIndexes(actor)` is
the authoritative ownership check. A response selecting party slot 0–2 for
opponent-right, or 3–5 for opponent-left, is invalid.

The two trainers have disjoint ranges, so two selected switches cannot name the
same valid slot. The ROM nevertheless preserves the existing duplicate-slot
guard as a defensive validation. Any malformed, incomplete, stale, expired,
changed-state, cross-owner, or otherwise illegal pair is rejected as a whole:
neither external action commits. Until expiry, the request remains pending for
a valid full pair; at expiry, bridge absence/disconnect, or incompatible BAGB
endpoint, both stored vanilla decisions execute. Late replies are rejected
after the request is returned to `IDLE`.

## Tests

Test-first coverage must prove:

1. BAGB/5 parsers reject BAGB/4, wrong-version, short, long, and malformed
   frames; C static layout assertions and Lua/Python lengths agree.
2. A two-trainer battle where both trainers are opted in publishes exactly one
   atomic request with battle mode `TRAINER_TWO_OPPONENT_DOUBLE`, both opponent
   actors, and correct owner metadata for slots 0–2 and 3–5.
3. Each actor's voluntary-switch legal actions use only its owner range; the
   agent tool exposes both parties but does not expose player reserves.
4. A legal move pair, move-plus-switch, and one switch from each trainer's
   range commit through the normal opponent controller paths.
5. A cross-owner party slot, stale/partial/duplicate pair, fainted reserve, or
   changed state causes no partial commit and both original vanilla choices
   execute after fallback.
6. A one-trainer double remains BAGB/5-compatible and preserves its shared
   six-slot party semantics; eligible singles, one-trainer doubles, excluded
   modes, thinking status, and existing no-service fallback regressions pass.
7. Service audits show both selected actions and owner-labelled party data;
   the ordinary local-model decision path remains bounded to a single model
   exchange per double turn.

## Measurable exit criteria

- A connected local service completes a real two-trainer double with one model
  decision selecting both actions, including a move/switch combination or two
  owner-correct switches.
- Service logs and in-game execution agree for both selected actions.
- Invalid, absent, delayed, or BAGB/4 bridge/service responses keep the battle
  playable and use both vanilla decisions without a partial external commit.
- A normal trainer single and a one-trainer double remain working on a freshly
  built normal `pokeemerald.gba`.
- Focused External AI ROM tests, bridge protocol, Lua-source, and Python
  service tests pass; `make -j16` produces the normal ROM.
