# Phase 6A Flow Review: Voluntary AI Switching in Trainer Singles

**Specification reviewed:** [Phase 6A voluntary switching](../specs/2026-07-29-phase-6a-voluntary-switching.md)

## Codebase grounding

The current mailbox is fixed BAGB/2: `BattleAgentMailboxV2` has four move-only
legal actions, and `bridge_protocol.py` rejects any request that is not
trainer-single with two active battlers. `BattleAgent_IsEligible` likewise
excludes double/multi modes and requires a current `aiMoveOrAction` move slot.
`battle_ai_switch_items.c` already identifies usable trainer-party candidates
with `GetAIPartyIndexes` and `IsValidForBattle`, then writes
`AI_monToSwitchIntoId[battler]` and emits `B_ACTION_SWITCH`. The action
selection controller separately handles recharge/multi-turn forced actions and
its normal `B_ACTION_SWITCH` path checks escape prevention before selecting a
party member.

## User flows

1. **Model chooses a move.** The agent reads active battle state, optionally
   reads its reserve party, selects a current legal move action, and the ROM
   applies it through the existing move path.
2. **Model chooses a voluntary switch.** The agent reads `get_party()`, sees a
   usable reserve, selects a switch action index, and the ROM rechecks current
   trainer-party and escape legality before supplying the standard switch
   action/slot to the battle controller.
3. **No usable reserve or locked action.** The legal list has moves only, or
   no external request is published when the engine will force recharge,
   multi-turn continuation, or replacement behavior.
4. **Invalid/late switch response.** The ROM drops it and keeps the request
   pending; deadline expiry restores the saved vanilla move and no external
   switch state survives.
5. **Existing trainer item decision.** For a voluntary external-agent turn,
   no vanilla item can replace the accepted model move/switch. Items are not
   external actions and remain outside this slice.

## Gaps found and resolved

### Critical

None. The ROM can continue to own action enumeration, party legality, and the
final controller input; the model never receives a writable party slot.

### Important

1. **The current response commit can only write a move slot.** Assigning
   `B_ACTION_SWITCH` to `aiMoveOrAction` would collide with the move-slot
   contract. The specification now requires a dedicated external-action state
   that reaches the existing `B_ACTION_SWITCH`/`AI_monToSwitchIntoId` controller
   path instead.
2. **The current wait begins before normal action selection and can precede a
   forced recharge/multi-turn branch.** Such a turn cannot legally offer a
   voluntary switch. The specification now forbids publishing an external
   request unless the engine will enter normal voluntary action selection.
3. **Vanilla switch/item helpers could overwrite the selected external
   action.** The user asked for move/switch intelligence but no items. The
   specification now makes an external-agent voluntary turn authoritative for
   move/switch only and suppresses vanilla voluntary switch/item selection on
   that turn; timeout restores the saved vanilla move instead.
4. **Party-validity and controller escape checks are not identical concepts.**
   A usable reserve alone does not prove the active battler may switch. The
   specification requires both a ROM party-candidate check and a live
   controller-equivalent switchability recheck at response commit.

### Minor

1. **The current V2 action limit is four.** A unified four-move/six-switch
   list needs ten entries and an explicit action kind. BAGB/3 is therefore a
   deliberate incompatible local protocol revision, not an overloaded V2
   record. Lua, Python, tests, generated mailbox addressing, and the ROM must
   update together.

## Resolved defaults

1. `get_party()` returns all six opposing party records, including unavailable
   slots; only ROM-generated legal actions determine which reserve can be
   chosen.
2. Switch actions follow move actions in action-index order, using ascending
   trainer party slot order.
3. The single-battle agent never receives player reserve data, an item action,
   a forced replacement action, or double-battle data.
4. A missing, stale, malformed, or illegal reply preserves the unchanged
   900-frame deadline and restored vanilla move fallback.

## Recommended next steps

1. Create a BAGB/3 serialization layout with static size/offset assertions and
   matching Lua/Python parser tests before modifying runtime behavior.
2. Add ROM unit tests for party snapshots, action enumeration, commit
   validation, locked-action exclusion, and fallback cleanup before production
   changes.
3. Update the local service tools and audit only after the ROM owns the V3
   party/action contract; then run bridge, External AI, fresh-ROM, connected,
   and absent-service verification.
