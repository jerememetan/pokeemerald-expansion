# Toxic Debris Animation Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show the current Toxic Spikes animation when Toxic Debris successfully scatters hazards, without changing its current mechanics.

**Architecture:** Add the archived state-save, current-move substitution, animation, wait, and state-restore sequence directly after the successful `settoxicspikes` command. The command’s existing failure branch remains before the new sequence, so it cannot animate a failed placement.

**Tech Stack:** pokeemerald battle-script assembly and the repository build system.

**Design:** [Toxic Debris Animation Migration Design](../specs/2026-08-09-toxic-debris-animation-migration-design.md)

---

## File structure

- Modify: `data/battle_scripts_1.s` — `BattleScript_ToxicDebrisActivates` only.
- No test file: compile-first validation is the selected workflow; inspect script order, compile, and test both success and failure paths in battle.

### Task 1: Add success-path visual feedback

**Files:**

- Modify: `data/battle_scripts_1.s`

- [ ] **Step 1: Inspect the current control flow**

Run `rg -n -C 7 'BattleScript_ToxicDebrisActivates|BattleScript_ToxicDebrisRet' data/battle_scripts_1.s`.

Expected: `settoxicspikes BattleScript_ToxicDebrisRet` precedes the scattered-hazards message, and the return label restores targets.

- [ ] **Step 2: Add the archived visual sequence on the success path**

Immediately after `settoxicspikes BattleScript_ToxicDebrisRet`, add:

```asm
	copyhword gChosenMove, gCurrentMove
	sethword gCurrentMove, MOVE_TOXIC_SPIKES
	attackanimation
	waitanimation
	copyhword gCurrentMove, gChosenMove
```

Leave the existing message, wait, and `BattleScript_ToxicDebrisRet` target restoration unchanged.

- [ ] **Step 3: Check script ordering**

Run `rg -n -C 10 'BattleScript_ToxicDebrisActivates|settoxicspikes|copyhword gChosenMove|sethword gCurrentMove, MOVE_TOXIC_SPIKES|attackanimation|waitanimation|BattleScript_ToxicDebrisRet' data/battle_scripts_1.s`.

Expected: the five new commands occur only between successful hazard placement and `STRINGID_POISONSPIKESSCATTERED`; the failure label occurs afterward.

- [ ] **Step 4: Compile the ROM**

Run `make -j4` in the user’s configured build environment.

Expected: exit code 0 with no battle-script assembly errors.

- [ ] **Step 5: Validate both battle paths**

1. Trigger Toxic Debris against a side where Toxic Spikes can be placed; verify the current Toxic Spikes animation appears once, followed by the scattered-hazards message.
2. Trigger Toxic Debris when placement is blocked or the opposing side already has the maximum layers; verify no animation appears and battle targeting/state remains correct.

Expected: only the successful placement path animates, with no mechanical or state regression.

- [ ] **Step 6: Commit the isolated change**

Run `git add data/battle_scripts_1.s docs/superpowers/plans/2026-08-09-toxic-debris-animation-migration.md` followed by `git commit -m "feat: animate toxic debris hazards"`.

Expected: one commit contains only this battle-script feature and its plan.

## Plan self-review

- The control-flow boundary is explicit: failed `settoxicspikes` branches before all new commands.
- The plan invokes the current Toxic Spikes animation and preserves the original move state.
- No unrelated ability, hazard, move-data, or engine behavior is in scope.
- Validation includes static ordering, a compile, and both runtime branches.
