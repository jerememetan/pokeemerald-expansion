# Lavaridge Random Egg Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore the archived five-way randomized Lavaridge Egg gift on the Expansion 1.16.3 migration branch.

**Architecture:** Change only the current generated Lavaridge script source. The existing Egg Woman flow retains all eligibility, message, fanfare, and flag handling; a local routine replaces its hard-coded Wynaut command with a five-way dispatch.

**Tech Stack:** pokeemerald script assembly and the repository build system.

**Design:** [Lavaridge Random Egg Migration Design](../specs/2026-08-09-lavaridge-random-egg-migration-design.md)

---

## File structure

- Modify: `data/maps/LavaridgeTown/scripts.inc` — Egg Woman flow and local random-Egg routine.
- No test file: compile-first validation was chosen for this ROM hack; use static script checks, the supported build, and in-game trials.

### Task 1: Add the five-way Egg routine

**Files:**

- Modify: `data/maps/LavaridgeTown/scripts.inc`

- [x] **Step 1: Inspect current guards**

Run `rg -n -C 16 'LavaridgeTown_EventScript_EggWoman|LavaridgeTown_EventScript_ReceivedEgg' data/maps/LavaridgeTown/scripts.inc`.

Expected: the flow checks the received-Egg flag, acceptance, and party size; sets the flag; then gives Wynaut.

- [x] **Step 2: Replace the hard-coded result**

Replace only the post-fanfare command with:

```asm
	call LavaridgeTown_EventScript_GiveRandomEgg
```

Before `LavaridgeTown_EventScript_ReceivedEgg`, add:

```asm
LavaridgeTown_EventScript_GiveRandomEgg::
	random 5
	switch VAR_RESULT
	case 0, LavaridgeTown_EventScript_GiveEggWynaut
	case 1, LavaridgeTown_EventScript_GiveEggTogepi
	case 2, LavaridgeTown_EventScript_GiveEggChimchar
	case 3, LavaridgeTown_EventScript_GiveEggPiplup
	case 4, LavaridgeTown_EventScript_GiveEggTurtwig
	return

LavaridgeTown_EventScript_GiveEggWynaut::
	giveegg SPECIES_WYNAUT
	return
LavaridgeTown_EventScript_GiveEggTogepi::
	giveegg SPECIES_TOGEPI
	return
LavaridgeTown_EventScript_GiveEggChimchar::
	giveegg SPECIES_CHIMCHAR
	return
LavaridgeTown_EventScript_GiveEggPiplup::
	giveegg SPECIES_PIPLUP
	return
LavaridgeTown_EventScript_GiveEggTurtwig::
	giveegg SPECIES_TURTWIG
	return
```

Do not change existing guards, messages, flags, or post-receipt labels.

- [x] **Step 3: Check the source contract**

Run `rg -n -C 3 'GiveRandomEgg|GiveEgg(Wynaut|Togepi|Chimchar|Piplup|Turtwig)|random 5|SPECIES_(WYNAUT|TOGEPI|CHIMCHAR|PIPLUP|TURTWIG)' data/maps/LavaridgeTown/scripts.inc`.

Expected: one `random 5` dispatch has cases 0–4 and all five intended `giveegg` calls; original flag and party-space guards remain.

- [x] **Step 4: Build the ROM**

Run `make -j4` from a configured development environment.

Expected: exit code 0 with no script-assembly error. User verified this compile after the change on 2026-08-09.

- [ ] **Step 5: Validate in-game**

Verify that decline and full-party cases preserve the offer, accepting sets the existing flag and shows the post-receipt text later, and repeated eligible fresh-save trials produce Wynaut, Togepi, Chimchar, Piplup, and Turtwig.

- [x] **Step 6: Commit the isolated change**

Run `git add data/maps/LavaridgeTown/scripts.inc docs/superpowers/plans/2026-08-09-lavaridge-random-egg-migration.md` followed by `git commit -m "feat: randomize lavaridge egg gift"`.

Expected: one commit contains only this source feature and its plan.

## Plan self-review

- Covers every archived outcome and preserves all existing Egg Woman guards.
- Uses the current `.inc` target rather than restoring obsolete `.pory` source.
- Has no new persistent state or unrelated map behavior.
- Uses source inspection, build, and in-game evidence per the user’s compile-first preference.
