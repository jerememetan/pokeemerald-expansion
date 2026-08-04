# Phase 7B Flow Review: Two-Trainer Doubles

**Specification reviewed:** [Phase 7B specification](../specs/2026-08-03-phase-7b-two-trainer-doubles.md)
**Implementation context:** src/battle_main.c, src/battle_agent.c,
src/battle_ai_main.c, src/battle_ai_switch_items.c, and tools/mgba-bridge/

**Implementation plan:** [Phase 7B plan](../plans/2026-08-04-phase-7b-two-trainer-doubles.md)

## Repository grounding

The base game calculates an AI move once per battler in
HandleTurnActionSelectionState and uses ChooseMoveOrAction_Doubles for each
call. The second battler can inspect the already chosen move of its lower-ID
ally, but the engine does not create an atomic two-action plan.
GetAIPartyIndexes assigns the two-opponent ranges 0–2 and 3–5 by flank.
Phase 7A currently excludes BATTLE_TYPE_TWO_OPPONENTS, treats the six records
as one shared party, and waits atomically for two actions.

## User flows

1. **Both trainers opted in; valid response.** The engine calculates the two
   ordinary choices, then opponent-right publishes one BAGB/5 request with four
   battlers, owner-labelled party records, and two legal-action lists. One
   model exchange selects the two published indexes. ROM validation accepts
   both and the normal opponent controllers execute them.
2. **Voluntary switches.** The model reads the party tool, which displays both
   trainers' reserves and their owner labels. It can select an action only
   from the actor's legal list. ROM rechecks the actor's engine-owned range
   before accepting each switch, including a two-switch pair.
3. **Mixed opt-in or ordinary two-trainer double.** If either trainer lacks
   externalAi, the external path never starts. Each opponent follows the
   existing vanilla path without a wait state or bridge traffic.
4. **No response or invalid response.** Missing, stale, BAGB/4, partial, or
   cross-owner responses cannot alter either action. The pending pair expires,
   clears the thinking status, becomes IDLE, and uses both stored vanilla
   choices.
5. **Unsupported turn state.** A fainted, absent, forced, recharging, or
   multi-turn-locked opponent produces no coordinated request. Normal battle
   logic owns that turn; a later fully voluntary turn can request again.
6. **Regression modes.** Singles and Phase 7A one-trainer doubles keep their
   BAGB/5 forms. Player-partner, multi, link, facility, and other excluded
   modes remain bridge-silent.

## Gaps found and resolved

### Critical

None remain. The specification explicitly assigns publication to
opponent-right after both vanilla choices exist, preventing a partial
controller handoff.

### Important

1. **BAGB/5 reused bytes could make shared and split parties ambiguous.**
   BattleAgentPartySnapshotV3.reserved is currently unused. The specification
   resolves this by versioning to BAGB/5, defining owner_battler, and reserving
   BATTLE_AGENT_ACTION_NONE exclusively for the unchanged Phase 7A shared
   party.
2. **A one-sided opt-in could accidentally control the other trainer.**
   The specification resolves this by requiring both A and B trainer records
   to have externalAi; otherwise neither action enters the external wait.
3. **Published party visibility could be confused with switch authority.**
   The specification makes actor-keyed legal actions and the ROM's
   GetAIPartyIndexes(actor) recheck authoritative. Party tool data is
   inspection-only.

### Minor

1. **Trainer identity is not needed in the tool contract.** Stable
   opponent-left/opponent-right labels are sufficient because legal actions
   carry the actual actor and owner restrictions. This avoids exposing extra
   trainer metadata without affecting decisions.
2. **Two switches cannot collide with disjoint ranges.** Preserve the existing
   duplicate-slot validation anyway as a defense against malformed mailbox
   data.

## Review conclusion

The revised specification defines all lifecycle, ownership, protocol,
validation, fallback, and regression behavior needed for an implementation
plan. No critical or important ambiguity remains.
