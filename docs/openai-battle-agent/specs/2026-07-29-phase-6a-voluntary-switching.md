# Phase 6A Specification: Voluntary AI Switching in Trainer Singles

**Status:** Approved design, flow review, and implementation plan; awaiting implementation

**Roadmap:** [mGBA AI Trainer Design](../2026-07-18-mgba-ai-trainer-design.md)

**Flow review:** [Phase 6A flow review](../reviews/2026-07-29-phase-6a-voluntary-switching-flow-review.md)

**Implementation plan:** [Phase 6A plan](../plans/2026-07-29-phase-6a-voluntary-switching.md)

**Prerequisite:** Phases 0–5 are verified for the Calvin trainer-single demo.

## Goal

Let an eligible trainer-single external agent decide for itself whether to use
a move or voluntarily switch to a legal reserve Pokémon. The agent learns
about its own active and reserve party through read-only tools, then selects
only one ROM-generated legal action. Battle items remain outside the agent's
authority and retain existing vanilla behavior.

## Scope

### In scope

- Replace the move-only BAGB/2 single-battle request with an additive BAGB/3
  trainer-single request/response contract.
- Publish all six opposing party slots in a fixed read-only party snapshot:
  slot, active/usable state, species, level, HP/max HP, status, types,
  ability, held item, battle stats, and four move records with PP.
- Add `get_party()` to the local model's read-only tool set. It returns that
  current opponent party snapshot only; it cannot inspect the player's bench
  or issue a switch.
- Publish a unified, ordered legal-action list containing every currently
  legal move action followed by every currently legal voluntary switch action.
- Let `list_legal_actions()` and `analyze_action(index)` describe either
  action family, and preserve `choose_action(index)` as the sole terminal
  write authority.
- Commit a validated voluntary switch through the existing trainer AI switch
  action path, including the selected party slot, or commit a validated move
  exactly as Phase 4A does today.
- Retain a complete vanilla fallback snapshot for the current trainer decision
  before external waiting begins.

### Out of scope

- Battle items, player actions, player-party information, forced replacement
  after a faint, wild battles, link/multi/facility modes, double battles,
  global trainer enablement, new trainer tags, UI redesign, and model-written
  battle text.
- A model-supplied move ID, target ID, party slot, action kind, or direct
  memory write. The model selects only an action index present in this request.

## ROM and service contract

### Eligibility and action timing

The existing `externalAi` trainer flag remains the only opt-in. The ROM
continues to exclude unsupported battle modes. It publishes BAGB/3 only when
the opponent has reached a normal voluntary action-selection turn: it does not
publish during a forced replacement, recharge, multi-turn lock, or any state
where the normal controller will force an action. The ROM computes its current
vanilla move/target first and snapshots that move fallback before publishing.

For an `externalAi` trainer turn that reaches BAGB/3, the accepted external
move or switch replaces vanilla voluntary move/switch/item selection for that
turn. Thus the external agent gets move/switch authority and no trainer item
is used on that turn. If the request has no valid reply, the saved vanilla
move/target is restored; forced engine handling outside this flow remains
unchanged.

### BAGB/3 request data

The request keeps the existing active-battler, field, side-condition, and move
data, changes `protocolVersion` to 3, and changes the battle-agent mailbox
and binary frame constants together. It adds six fixed-size opponent-party
records. Each record has:

```text
party_slot, is_active, is_usable,
species, level, hp, max_hp, status1, status2, status3,
type1, type2, type3, ability, item,
attack, defense, speed, sp_attack, sp_defense,
move[0..3] { move, pp, type, power, accuracy, effect, target, priority, split }
```

`is_usable` is determined by the ROM's existing trainer-party validity and
voluntary-switch rules. A fainted, empty, active, trapped, or otherwise
unavailable slot is represented accurately in `get_party()` but is never a
legal switch action.

Each legal action has an explicit `kind`:

```text
MOVE:   kind=MOVE, move_slot=0..3, target_battler=0..3, party_slot=NONE
SWITCH: kind=SWITCH, move_slot=NONE, target_battler=NONE, party_slot=0..5
```

The action list contains at most ten entries: four move actions and six switch
actions. Action indexes are contiguous from zero in the exact order published.
The response stays a `(sequence, action_index)` pair. No party slot or action
kind is returned separately by the model.

### Agent tools

The local service exposes these read-only tools before the existing terminal
tool:

- `get_battle_state()` and `get_battler(id)` for active battle data.
- `get_party()` for the opponent's six current party records.
- `get_battler_moves(id)` and `get_field_state()` for current battle facts.
- `list_legal_actions()` for current move and switch indexes.
- `analyze_action(index)` for a ROM-generated move analysis or a switch
  candidate summary. Switch analysis never invents damage, effectiveness, or
  a target.
- `compare_speed()` for active-battler normal speed ordering.
- `choose_action(index)` as the one terminal selection.

The model may call `get_party()` only if it wants reserve information; it is
not required before it chooses a move. Tool calls remain bounded by the
existing service deadline and tool-call cap.

## Validation, commit, and fallback

- Before accepting a response, the ROM verifies the current pending sequence,
  action index, action kind, and every action field against the current live
  battle state.
- A move action repeats Phase 4A legality checks: valid move slot, usable PP,
  and a legal live target.
- A switch action verifies that the slot is in the opposing trainer party, is
  currently switchable under the same engine rules used by trainer AI, is not
  active/fainted/empty, and remains legal at commit time.
- A valid switch uses a dedicated external-action commit state, stores the
  existing `AI_CHOICE_SWITCH` value (never the controller `B_ACTION_SWITCH`
  value) in `aiMoveOrAction`, sets `AI_monToSwitchIntoId[battler]`, and emits
  the normal opponent-side `B_ACTION_SWITCH` controller action. It never
  bypasses the battle controller or writes player data.
- A stale, malformed, duplicate, illegal, or changed-state response is
  discarded. The original wait continues until a valid response or the
  unchanged 900-frame deadline.
- On timeout or any no-response case, restore the pre-wait vanilla move/target
  and clear any external-action commit state before continuing battle flow.
- Items never become a legal BAGB/3 action and are suppressed only for an
  `externalAi` trainer turn that reached the voluntary external-action flow.

## Tests

Add ROM, bridge-source, protocol, and service tests that prove:

1. BAGB/3 publishes six current opponent party records and does not expose the
   player bench.
2. `get_party()` returns those records; no read-only tool can mutate a party.
3. A legal voluntary switch action is emitted only for a usable, inactive,
   switchable reserve slot.
4. No switch action is emitted for fainted, empty, active, trapped, or
   otherwise forbidden slots.
5. A valid current switch response commits the existing trainer switch action
   and requested legal party slot.
6. A stale, illegal, or changed-state switch response is rejected without
   changing the saved vanilla decision.
7. Move actions, existing response rejection, thinking status, and no-response
   fallback retain their current behavior under protocol V3.
8. An item choice and a forced replacement stay on their existing vanilla path.

## Measurable exit criteria

- In a configured trainer-single battle with a usable reserve, the local agent
  can inspect `get_party()`, choose a legal voluntary switch, and the selected
  reserve appears through normal battle switching.
- Invalid switch attempts are never committed, and absent/late service replies
  preserve the original vanilla trainer decision without a freeze.
- Focused ROM, Python protocol/service, Lua-source, and full relevant External
  AI tests pass; a fresh ROM builds.
- A connected and an absent-service manual trainer-single smoke test both pass.

Double battles and broad `externalAi` enablement begin only after this slice
has fresh evidence.
