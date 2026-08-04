# Phase 7A Flow Review: Coordinated One-Trainer Double Battles

**Specification reviewed:** [Phase 7A one-trainer doubles](../specs/2026-08-02-phase-7a-single-trainer-doubles.md)

**Implementation plan:** [Phase 7A plan](../plans/2026-08-02-phase-7a-single-trainer-doubles.md)

## Codebase grounding

`src/battle_agent.c` currently publishes one BAGB/3 request for one requester,
builds at most ten action records, and validates only a single-battle target.
Its eligibility check rejects `BATTLE_TYPE_DOUBLE` and
`BATTLE_TYPE_TWO_OPPONENTS`. `src/battle_controller_opponent.c` asks each
opponent controller for an action separately, and its normal switch path
already prevents choosing an active party slot in doubles. `GetAIPartyIndexes`
uses the full `gEnemyParty` range for a one-trainer double but splits party
ranges for `BATTLE_TYPE_TWO_OPPONENTS` and player-partner modes.

The BAGB/3 Lua/Python bridge requires fixed 1049-byte requests and 5-byte
responses, accepts only `battle_mode=TRAINER_SINGLE` with two active battlers,
and its service exposes one global legal-action list followed by
`choose_action(index)`. The test runner likewise models one request and one
injected action index per turn. Existing core double-AI tests include
Helping Hand coordination and prevention of selecting the same reserve for two
opponent positions.

## User flows

1. **Coordinated move pair.** Both opposing battlers reach ordinary voluntary
   selection. The ROM publishes one four-battler snapshot and two legal-action
   lists. The agent inspects actions/state and selects one action for each;
   the ROM validates both and the normal controller executes them.
2. **Ally-target combination.** The agent sees a Helping Hand entry targeted
   at its ally and an attack entry for that ally. It submits both in one pair;
   the ROM commits them together rather than treating the second choice as a
   later, changed battle state.
3. **Move plus switch or double switch.** The shared party tool and each actor's
   actions reveal legal reserves. The agent chooses one or two switch records;
   the ROM prevents either active slot or a duplicate shared reserve from being
   selected.
4. **Forced or incomplete double state.** If either opponent is absent,
   fainted, locked, recharging, or has a non-move vanilla decision, Phase 7A
   publishes nothing. The engine handles the replacement or forced action and
   a later ordinary two-active turn may start a new request.
5. **Bad/external failure.** A missing, partial, stale, malformed, mismatched,
   or now-illegal response changes neither opponent action. On the existing
   deadline both saved vanilla choices resume and the thinking message clears.
6. **Out-of-scope double.** Two simultaneous trainer encounters and in-game
   player-partner doubles stay on vanilla AI with no bridge request.

## Gaps found and resolved

### Critical

1. **The existing controller asks opponents independently, but the requested
   feature requires an atomic pair.** If the first controller were allowed to
   publish/commit alone, the second action could observe an artificial partial
   state and double switches could collide. The specification now requires a
   shared batch coordinator that begins only after both vanilla selections
   exist, blocks both controllers on the same sequence, and commits neither
   until the complete pair validates.

2. **BAGB/3's one-index response and ten global action records cannot encode a
   pair.** The specification now defines BAGB/4 with two actor-keyed lists,
   bounded 22-entry lists, and an exactly-two-entry response. Lua, Python, C,
   tests, and generated mailbox addressing must migrate as one local release;
   version/length mismatch is a safe no-response path.

### Important

1. **A double battle can be one trainer, two trainers, or include an in-game
   player partner.** The latter two have different party/controller ownership.
   Phase 7A is narrowed to one opposing trainer, while
   `BATTLE_TYPE_TWO_OPPONENTS` and `BATTLE_TYPE_INGAME_PARTNER` explicitly
   remain vanilla.

2. **A voluntary double switch has pair-level legality beyond two independent
   single switches.** The specification requires rechecking both actions
   against live state and rejecting the full response when switch slots
   duplicate or equal either active party slot.

3. **Move target categories are not all one battler.** The specification
   distinguishes exact legal targets (including ally/self) from spread/field/
   side moves that receive a canonical `NONE` target and remain subject to
   ordinary controller target derivation. No target category is guessed by the
   model.

4. **Existing player-partner battles may not be covered by the generic MULTI
   exclusion.** The specification explicitly excludes
   `BATTLE_TYPE_INGAME_PARTNER`, avoiding an unintended player-side boundary
   expansion.

### Minor

1. **BAGB/4 replaces a deployed local protocol.** Existing single-battle
   functionality needs regression coverage under the V4 component set, but an
   old service will safely produce vanilla fallback rather than corrupting
   memory or parsing a different payload.

2. **The current audit prints one action.** Phase 7A needs a paired audit with
   actor, selected action, and ROM-derived facts for each chosen action so the
   user can verify coordination.

## Resolved defaults

1. One trainer double = trainer double without two-opponent or in-game-partner
   flags; only this mode receives BAGB/4 in Phase 7A.
2. The model selects exactly two actor/index entries as a single terminal
   response. A direct choice without other tools is allowed, but no tool grants
   write authority besides `choose_actions`.
   The service gives the local Qwen model an explicit one-tool-call-per-reply
   instruction and normalizes only its scoped legal-action query and bare
   `choose_actions` list form. Both are read-only/shape compatibility changes;
   the existing complete actor/index validation remains the authority.
3. A failure in either half rejects the entire pair; both original vanilla
   choices are restored only at the unchanged timeout.
4. Player reserves and trainer items remain unavailable. Forced replacements
   stay entirely on the normal engine path.
5. One non-selectable spread/field/side move produces one action with
   `target_battler=NONE`; explicit live targets produce one entry each.

## Recommended next steps

1. Write the Phase 7A implementation plan with a test-first BAGB/4 layout
   task, followed by paired batch coordination, double target enumeration,
   controller commit, service tools/audit, and evidence tasks.
2. Add test-runner support for two actor-keyed action lists and an atomic
   injected response before production runtime changes.
3. Retain an explicit exclusion regression for `BATTLE_TYPE_TWO_OPPONENTS` and
   add one for `BATTLE_TYPE_INGAME_PARTNER` before enabling double eligibility.
