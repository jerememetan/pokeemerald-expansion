# Badge and Received-HM Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development.
> Steps use checkbox syntax for tracking.

**Goal:** All eight HMs work after badge and HM receipt, without teaching.

**Architecture:** Reuse current unlock callbacks, share party selection, and
add only a small HM submenu to the current party menu. Existing effects remain.

**Tech Stack:** C/script sources, Python unittest, native WSL cc, Make.

---

Specification: docs/superpowers/specs/2026-10-04-hm-unlocks-design.md.

## Task 1: Tests before implementing the unlock/selector/menu unit

Runtime allowlist: src/field_move.c, include/field_move.h, src/scrcmd.c,
src/field_player_avatar.c, src/party_menu.c, src/data/party_menu.h.
New tests: tools/migration/tests/test_hm_unlocks.py.

- [ ] Create real-C fixtures under Python unittest using native cc with
  -std=c11 -Wall -Wextra -Werror. Use actual field_move.c and actual extracted
  script/Surf/menu functions, not a Python reimplementation. Stub only engine
  dependencies. Expected Emerald pairs are Cut1, Flash2, RockSmash3,
  Strength4, Surf5, Fly6, Dive7, Waterfall8 with corresponding received flags.
  FRLG uses existing alternate badges Cut2/Flash1/RockSmash6/Fly3/Waterfall7;
  its received-HM aliases are zero, so retain actual badge-only semantics.
- [ ] Run red: WSL python3 -m unittest tools.migration.tests.test_hm_unlocks -v.
  Existing badge-only unlocks and learned-HM lookup must produce genuine
  assertion failures, not missing-helper compilation errors. Use actual old
  script selector to establish the no-teaching regression before introducing
  the new shared selector. Afterward compile the real shared selector.
- [ ] Change each Emerald HM callback's badge return to badge && received-HM
  flag. Preserve the existing FRLG badge-only behaviour without inventing
  receipt flags: use existing FRLG branches or badge && (IS_FRLG || receipt).
  Add pokemon.h for GetMonData/MonKnowsMove/gParties declarations if needed.
- [ ] Implement/decorate this shared selector and declare it in field_move.h:

```c
u32 FieldMove_GetPartyMon(enum FieldMove fieldMove, bool32 checkUnlocked)
{
    bool32 isHM = fieldMove <= FIELD_MOVE_WATERFALL;
    if ((isHM || checkUnlocked) && !IsFieldMoveUnlocked(fieldMove))
        return PARTY_SIZE;
    for (u32 i = 0; i < PARTY_SIZE; i++)
    {
        if (GetMonData(&gParties[B_TRAINER_PLAYER][i], MON_DATA_SPECIES) == SPECIES_NONE)
            break;
        if (!GetMonData(&gParties[B_TRAINER_PLAYER][i], MON_DATA_IS_EGG)
         && (isHM || MonKnowsMove(&gParties[B_TRAINER_PLAYER][i], FieldMove_GetMoveId(fieldMove))))
            return i;
    }
    return PARTY_SIZE;
}
```

- [ ] Replace ScrCmd_checkfieldmove's lookup loop with the shared selector,
  retaining Script_RequestEffects, successful species output and PARTY_SIZE.
  Replace PartyHasMonWithSurf's loop with !alreadySurfing && helper < PARTY_SIZE;
  include field_move.h in field_player_avatar.c. Keep all other Surf checks.
- [ ] Add MENU_HMS before MENU_FIELD_MOVES, its callback forward declaration
  and sCursorOptions entry labelled HMs. Expand actions[8] to actions[9].
  Root menu keeps its four-known-move loop and adds one MENU_HMS entry only
  if at least one HM is unlocked. Do not duplicate every HM in the root.
- [ ] CursorCb_HMs removes the old selection window, clears the action list,
  appends each unlocked field move from CUT through WATERFALL and Cancel,
  then uses DisplaySelectionWindow(SELECTWINDOW_ACTIONS). Reset task cursor
  data to 0xFF and retain Task_HandleSelectionMenuInput. Current field-move
  callbacks and Cancel handle execution/return, with no new animation engine.
- [ ] Run green including both badge/receipt gates, no-learned versus learned
  states, egg/empty/first-empty parties, non-HM moves, script outputs, Surf
  state, both game mappings, all eight submenu entries and worst-case root
  nine entries. Assert canaries/capacity and window formula with nine rows.
- [ ] Independent spec review, then quality review; fix and rereview findings.

## Task 2: Native configuration restoration and shared checkpoint

- [ ] Execute the separate audited configuration plan, using current settings.
- [ ] Run old migration regressions plus new real-C tests; git diff --check.
- [ ] Build exact current runtime sources in a persistent native validation
  copy (not /tmp), compare changed-source bytes, record ROM size and SHA-256.
- [ ] Commit this HM unit and the configuration unit separately using explicit
  allowlists. Never include generated artifacts, saves or unrelated edits.
- [ ] Record pending in-game acceptance and still-unported data/UI mechanics
  in the dated checkpoint note, without claiming complete hack restoration.
