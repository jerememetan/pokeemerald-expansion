# Phase 7A Specification: Coordinated External AI for One-Trainer Doubles

**Status:** Approved design; specification ready for flow review

**Roadmap:** [External AI Trainer Integration Plan](../integration-plan.md)

**Flow review:** [Phase 7A flow review](../reviews/2026-08-02-phase-7a-single-trainer-doubles-flow-review.md)

**Implementation plan:** Pending flow-review approval

**Prerequisite:** Phase 6B trainer singles have fresh External AI, Python, ROM
build, and connected-service smoke-test evidence.

## Goal

Allow the local external agent to choose both actions for an intentional,
one-trainer double battle from one shared, read-only battle snapshot. The
single decision must support coordinated move combinations, a move plus a
voluntary switch, or a legal double switch, while the ROM remains the sole
authority for targeting, action legality, controller input, and fallback.

## Scope

### In scope

- Trainer double battles with exactly one opposing trainer: `BATTLE_TYPE_TRAINER`
  and `BATTLE_TYPE_DOUBLE`, without `BATTLE_TYPE_TWO_OPPONENTS`,
  `BATTLE_TYPE_INGAME_PARTNER`, multi, link, facility, or other currently
  excluded modes.
- One atomic request per normal voluntary opponent action-selection turn. It
  contains the four active battlers, the shared opponent six-slot party,
  field/side state, and legal actions for both opposing battlers.
- An agent-selected pair of move and/or voluntary-switch actions. Each move
  action includes an exact ROM-approved target when the move targets one
  battler, including an ally target such as Helping Hand.
- The existing read-only inspection model extended to double state:
  `get_battle_state`, `get_field_state`, `get_battler`, `get_battler_moves`,
  `get_party`, `list_legal_actions`, `analyze_action`, and `compare_speed`.
  `choose_actions` is the only terminal selection tool.
- A fixed `AI is thinking..` message while the atomic request is pending, using
  the existing message-window ownership rules.
- BAGB/4 ROM, Lua, Python, and test support. The local components update as a
  set; an old or mismatched component must reject the frame rather than parse
  it as BAGB/3.

### Out of scope

- Two-trainer doubles (`BATTLE_TYPE_TWO_OPPONENTS`), player-partner doubles
  (`BATTLE_TYPE_INGAME_PARTNER`), player-side AI, triple or multi battles,
  wild/link/facility battles, battle items, player reserve data, forced
  replacement after a faint, or changes to battle mechanics.
- Model-supplied move IDs, target IDs, party slots, action kinds, controller
  values, direct memory writes, free-form search, or any tool that mutates
  battle state. The agent can only inspect ROM-published information and
  select published action indexes.
- Adding heuristic move scoring. The model reasons from the read-only tools;
  the ROM exposes deterministic facts and validates decisions.

## Eligibility and lifecycle

The existing global `Trainer.externalAi` opt-in remains necessary. Phase 7A
adds eligibility only when the battle is a one-trainer double and both opponent
active battlers are present, alive, AI-controlled, and currently have ordinary
voluntary move selections. `BATTLE_TYPE_TWO_OPPONENTS` and
`BATTLE_TYPE_INGAME_PARTNER` remain explicitly ineligible for Phase 7B and a
future player-partner phase respectively.

The ROM waits until both opposing vanilla move/target choices are available,
then snapshots both choices as the pair's fallback and publishes exactly one
request. It must not publish separately for the left and right opponent.

No request is published when either opponent is absent, fainted, recharging,
locked into a multi-turn action, being forcibly replaced, or otherwise has a
non-move vanilla choice. The normal engine handles that turn. Once a later
turn again has two active opponents with voluntary move choices, Phase 7A may
publish a new request.

## BAGB/4 data contract

BAGB/4 replaces BAGB/3 for the local ROM/Lua/Python deployment. `protocolVersion`
is `4`; the binary frame header version, fixed payload size, Lua constants,
Python parser/formatter, generated mailbox address configuration, and static
C layout assertions change together. A version or length mismatch produces no
accepted response and therefore reaches the ROM fallback.

The request metadata contains:

```text
request_sequence, turn_sequence, battle_mode=TRAINER_DOUBLE,
controlled_battlers[2] = opponent-left, opponent-right,
battler_count=4
```

The snapshot contains all four active battlers, each active battler's four
move records, field weather/terrain/statuses, both side statuses, and the six
records of the single opposing trainer's shared party. Party records retain
their existing slot, active, usable, identity, battle statistics, held item,
status, type, ability, and move/PP fields. No player reserve record is added.

Each legal action is a ROM-created record:

```text
actor_battler, action_index, kind,
move_slot, target_battler, party_slot,
type_effectiveness, has_stab, can_faint_target
```

`action_index` is contiguous within its `actor_battler` list. The two lists are
published in controlled-battler order. Each list permits at most 22 entries:
the four move slots expanded across up to four target choices, followed by up
to six voluntary switches. This is a fixed bound of 44 records per request.

For an explicitly selectable move target, the ROM publishes one action for
each currently legal live target. This includes the acting Pokémon, its ally,
and either opposing Pokémon when game rules permit. For a spread, field, side,
or otherwise non-selectable target category, the ROM publishes exactly one
action with `target_battler=NONE`; normal controller target derivation remains
responsible for execution. Empty moves, zero-PP moves, restricted moves,
fainted/absent targets, and targets prohibited by the engine never appear.

The response is:

```text
response_sequence,
actions[2] = { actor_battler, action_index }
```

It must name both controlled battlers exactly once. The agent cannot submit a
raw target, move, switch slot, or controller opcode.

## Tool contract

All tools are read-only except the terminal selector. The local model may call
the tools in any order within the existing bounded call and time limits.

- `get_battle_state()` returns request metadata, the two controlled opponent
  battlers, and all four active battler snapshots.
- `get_field_state()`, `get_battler(id)`, and `get_battler_moves(id)` expose
  the corresponding published ROM data for IDs 0 through 3 only.
- `get_party()` returns the one opposing trainer's six shared party records,
  including unavailable and active slots. It does not expose player reserves
  and does not switch a Pokémon.
- `list_legal_actions()` returns the two actor-keyed action lists. It is the
  source of truth for which targets and switches are selectable this turn.
- `analyze_action(actor_battler, action_index)` returns ROM-derived facts for
  that exact action. It never estimates an unlisted action or makes a choice.
- `compare_speed()` exposes the normal active-battler speed context; the agent
  must still use each action's priority and battle state when planning.
- `choose_actions(actions)` accepts exactly two `{battler_id, action_index}`
  selections and terminates reasoning. It rejects missing, duplicate, foreign,
  or non-legal actor/index pairs.

The system prompt directs the model to inspect tools as needed and finish
exactly once with `choose_actions`; it produces no player-facing battle text.

## Validation, commit, and fallback

The ROM rechecks the pending sequence and the complete pair immediately before
commit. For every move it validates the actor, move slot, PP/limitation state,
action kind fields, and exact live target policy. For every switch it validates
the actor's current switchability and that its selected party slot is usable,
inactive, and in the shared trainer party.

If both actions are switches, their party slots must differ. A requested
reserve cannot equal either currently active party slot. If any response field
is missing, duplicated, stale, malformed, out of range, changed-state, or
illegal, the ROM accepts neither action. It leaves the request pending until a
valid complete pair arrives or the existing 900-frame deadline expires.

On an accepted pair, the ROM writes the two ordinary `aiMoveOrAction`, target,
and/or `AI_monToSwitchIntoId` values and uses the existing opponent controller
move/switch paths. It does not bypass animation, replacement, escape, or
party ownership logic. No item is offered or used on an accepted external
turn.

On timeout, service absence/disconnect, protocol mismatch, or no valid pair,
the ROM restores both pre-wait vanilla move/target choices, clears every
external wait/response state, clears the thinking message, and continues the
turn. A late reply cannot modify a later request.

## Tests

Add test-first coverage that proves:

1. BAGB/4 serializes and strictly parses a one-trainer double request with
   four active battlers, two controlled battlers, shared party data, and two
   bounded action lists; malformed, V3, short, long, and invalid-pair frames
   are rejected.
2. The ROM publishes exactly one request for a normal one-trainer double turn,
   never two sequential requester requests, and it does not publish for
   `BATTLE_TYPE_TWO_OPPONENTS`.
3. Legal action enumeration covers ally, player-left, player-right, self, and
   canonical spread/field targets while excluding absent/fainted/invalid
   targets and unavailable move slots.
4. A legal Helping Hand-to-ally plus legal attack pair is accepted and reaches
   the normal controller move path.
5. Legal move-plus-switch and double-switch pairs commit the specified shared
   party slots; selecting the same reserve twice is rejected atomically.
6. Partial, stale, duplicate-actor, out-of-range, malformed, locked, trapped,
   fainted-reserve, and changed-state pairs commit neither selected action and
   retain both vanilla fallbacks after expiry.
7. Python tools expose four active battlers, actor-keyed actions, and the
   `choose_actions` contract; the service audit records both selected actions
   and their ROM facts. It cannot use items or expose player reserves.
8. Lua source and bridge tests enforce BAGB/4 lengths/version and no partial
   response write. Existing trainer-single BAGB/4 regression tests, thinking
   status, invalid-response behavior, and service-absent fallback continue to
   pass.

## Measurable exit criteria

- A connected local service completes an intentional one-trainer double by
  selecting a coordinated valid pair, including an ally-target combo and a
  legal double switch, through normal battle execution.
- An absent, incompatible, late, partial, or invalid service reply leaves the
  battle playable and restores both vanilla actions with no external partial
  commit.
- A two-trainer double still produces no BAGB request and uses vanilla AI.
- Focused ROM, bridge protocol, Lua-source, service, and full External AI
  tests pass; `make -j16` produces a fresh ROM.
- Manual connected and absent-service smoke tests pass for an intentional
  one-trainer double; manual two-trainer-double smoke testing confirms it is
  still excluded.

Phase 7B may begin only after these criteria have fresh evidence.
