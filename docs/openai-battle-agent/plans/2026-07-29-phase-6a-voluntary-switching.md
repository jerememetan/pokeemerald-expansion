# Phase 6A Voluntary AI Switching Implementation Plan

> **For agentic workers:** Execute inline task-by-task. Steps use checkboxes.

**Goal:** Add ROM-validated voluntary move-or-switch decisions for eligible trainer singles; battle items remain absent.

**Architecture:** BAGB/3 carries six opponent reserve records and tagged move/switch actions. The ROM alone enumerates, validates, and commits actions; Lua/Python forward and expose only read-only tools plus an action index.

**Specification:** [Phase 6A spec](../specs/2026-07-29-phase-6a-voluntary-switching.md)

**Flow review:** [Phase 6A flow review](../reviews/2026-07-29-phase-6a-voluntary-switching-flow-review.md)

## Files

- Modify `include/battle_agent.h`, `src/battle_agent.c`, and `src/battle_main.c` for BAGB/3 data, action validation, switch commit, and fallback.
- Modify `tools/mgba-bridge/bridge_protocol.py`, `mgba_bridge.lua`, and `battle_agent_service.py` for the matching protocol and tools.
- Modify `test/battle/ai.c`, `tools/mgba-bridge/tests/test_bridge_protocol.py`, `test_battle_agent_service.py`, and `test_mgba_bridge_source.py`.
- Update the roadmap and add Phase 6A verification evidence after live tests.

## Task 1: Define the BAGB/3 wire contract test-first

- [ ] Add failing `test_bridge_protocol.py` cases for six party records, ten tagged actions, move/switch action fields, malformed kind fields, out-of-range party slots, noncontiguous indexes, wrong frame length, and V2 rejection.
- [ ] Run:

  ```powershell
  py -3 -m unittest discover -s tools\mgba-bridge\tests -p "test_bridge_protocol.py" -v
  ```

  Expected: V3 tests fail because the parser is fixed to version 2, two battlers, and four move actions.
- [ ] Define V3 party, tagged-action, snapshot, mailbox, size, and offset assertions in `include/battle_agent.h`. Update `bridge_protocol.py` to parse only the exact V3 frame and retain `(sequence, actionIndex)` responses.
- [ ] Re-run the focused parser test; expected pass. Commit protocol files and their tests as `feat(agent): define voluntary switch protocol`.

## Task 2: Publish reserve state and legal switches test-first

- [ ] Add failing ROM tests in `test/battle/ai.c` proving six opponent party records are emitted; move actions precede switch actions; only usable inactive switchable reserves are listed; and forced recharge/multi-turn states do not publish an external request.
- [ ] Run:

  ```powershell
  wsl bash -lc "cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion && make -j16 check TESTS='External AI switch'"
  ```

  Expected: new assertions fail because V2 has no party snapshot or switch action kind.
- [ ] In `src/battle_agent.c`, use `GetAIPartyIndexes`, `IsValidForBattle`, active party indexes, and live escape restrictions to populate the V3 opponent-party snapshot and append ascending-party-slot switch actions. Keep player party data private and preserve move legality.
- [ ] Re-run the focused ROM test; expected pass. Commit ROM data/action files as `feat(agent): publish legal voluntary switches`.

## Task 3: Commit current switch actions test-first

- [ ] Add failing ROM tests for valid switch commit, stale/illegal switch rejection, reserve state changed after request, no residual switch state after timeout, and existing move fallback behavior.
- [ ] Implement a dedicated external action state. Move actions retain current commit logic. Switch actions revalidate candidate and escape rules, set `AI_monToSwitchIntoId[battler]`, and reach the normal `B_ACTION_SWITCH` controller path; never store a switch code in `aiMoveOrAction`.
- [ ] In `src/battle_main.c`, suppress vanilla voluntary switch/item heuristics only for the current external-agent turn, so they cannot overwrite an accepted external move/switch or its fallback. Forced engine actions remain unchanged.
- [ ] Run the focused ROM suite; expected all switch, move, rejection, thinking-status, and fallback tests pass. Commit as `feat(agent): commit voluntary switch actions`.

## Task 4: Expose tools, update bridge, and verify

- [ ] Add failing Python/Lua source tests for V3 frame offsets/length, ten-action maximum, `get_party`, tagged `list_legal_actions`, switch `analyze_action`, and action-index-only `choose_action`.
- [ ] Update `mgba_bridge.lua`, `bridge_protocol.py`, and `battle_agent_service.py` together. `get_party()` may read only the six ROM snapshot records; it cannot select a slot. Audit output distinguishes move and switch actions without model rationale.
- [ ] Run:

  ```powershell
  py -3 -m unittest discover -s tools\mgba-bridge\tests -v
  wsl bash -lc "cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion && make -j16 check TESTS='External AI'"
  wsl bash -lc "cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion && make -j16"
  git diff --check
  ```

  Expected: all checks pass and `pokeemerald.gba` builds.
- [ ] Manually verify a connected Calvin switch after `get_party()` and an absent-service fallback. Record evidence, update the roadmap, and commit docs only.

## Plan self-review

- Covers V3 protocol, party privacy, legal enumeration, switch controller integration, no-item authority, fallback, test-first steps, verification, and documentation.
- Excludes double battles, forced replacement, player reserve data, battle items, and global trainer enablement.
