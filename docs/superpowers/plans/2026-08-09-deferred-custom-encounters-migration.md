# Deferred Custom Encounters Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore the five deferred custom encounters while retaining Expansion 1.16.3 maps, scripts, and trainer data as the base.

**Architecture:** Add five symbolic trainer records after `TRAINER_MAY_PLACEHOLDER`, then adapt each archived event into the current map's Poryscript/JSON source. Each encounter has its own victory-state boundary; generated trainer and map `.inc` output is recreated by the normal build.

**Tech Stack:** Competitive trainer-party syntax, Poryscript, map JSON/mapjson, trainerproc, GNU Make, mGBA manual checks.

**Design:** [Deferred Custom Encounters Migration Design](../specs/2026-08-09-deferred-custom-encounters-migration-design.md)

---

## File Structure

- Modify `include/constants/opponents.h`: append five trainer IDs `855..859`; set `TRAINERS_COUNT_EMERALD` to `860`.
- Modify `src/data/trainers.party`: add the five archived parties in current competitive syntax.
- Modify `include/constants/flags.h`: name the two verified Mom flags and one verified unused Red hide flag.
- Modify the current authored `.inc` script sources under `data/maps/`; modify `data/scripts/players_house.inc` for the shared Mom dispatch flow.
- Modify only `data/maps/AlteringCave/map.json` and `data/maps/NewMauville_Inside/map.json` for the new Red and Leaf objects.
- Regenerate, never hand-edit: `src/data/trainers.h` and map `scripts.inc` files.

### Task 1: Add the shared trainer-ID and party data

**Files:**
- Modify: `include/constants/opponents.h:861-868`
- Modify: `src/data/trainers.party`
- Generated: `src/data/trainers.h`

- [ ] Add the IDs in this exact order and set the count to 860:

```c
#define TRAINER_STEVEN_GRANITE_CAVE 855
#define TRAINER_RED_ALTERING_CAVE   856
#define TRAINER_MOM                 857
#define TRAINER_LEAF_2              858
#define TRAINER_MT_PYRE_ARCHIE      859
#define TRAINERS_COUNT_EMERALD      860
```

- [ ] Convert the five archived records from `archive/master-pre-1.16.3:src/data/{trainers.h,trainer_parties.h}` with `migration_scripts/1.9/convert_trainer_parties.py`, then append only those five `TRAINER_*` blocks to `src/data/trainers.party`. Use `tools/migration/merge_legacy_trainer_parties.py`'s current-syntax rename table for any renamed current symbol.
- [ ] Run `wsl.exe bash -lc "cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion && make src/data/trainers.h"`.

Expected: exit 0; generated output contains every new ID; `TRAINERS_COUNT_EMERALD` is 860 and is less than `MAX_TRAINERS_COUNT_EMERALD` 864.

### Task 2: Restore Steven and Red

**Files:**
- Modify: `data/maps/GraniteCave_StevensRoom/scripts.inc`
- Modify: `data/maps/AlteringCave/scripts.inc`
- Modify: `data/maps/AlteringCave/map.json`
- Modify: `include/constants/flags.h`

- [ ] Before editing, record a failing static check that `TRAINER_STEVEN_GRANITE_CAVE`, `TRAINER_RED_ALTERING_CAVE`, Red's object, and Red's dedicated hide flag are absent from the current sources.
- [ ] Insert Steven's archived no-intro battle before the current Letter message. Branch on battle loss to the existing interaction without setting `FLAG_DELIVERED_LETTER`; after victory, continue the original Letter/TM/PokeNav/exit sequence unchanged.
- [ ] Add Red with `OBJ_EVENT_GFX_RED` at `x: 18`, `y: 19`, `elevation: 0`, `MOVEMENT_TYPE_FACE_DOWN`, `TRAINER_TYPE_NONE`, and the new hide flag. Add a map-load flag check and an interaction which calls `trainerbattle_no_intro TRAINER_RED_ALTERING_CAVE`; only the victory path sets the hide flag and removes/fades Red.
- [ ] Regenerate scripts and run `git diff --check` plus the targeted trainer generation command.

Expected: a loss leaves Steven's Letter flow and Red's object available; a victory consumes only the intended encounter state.

### Task 3: Restore Mom's optional challenge

**Files:**
- Modify: `include/constants/flags.h`
- Modify: `data/scripts/players_house.inc:331-343`
- Modify: `data/maps/LittlerootTown_BrendansHouse_1F/scripts.inc`

- [ ] Confirm `0x1DA` and `0x1DE` are unused, then name them `FLAG_FOUGHT_MOM` and `FLAG_MOM_BATTLE_AVAILABLE`.
- [ ] Extend `PlayersHouse_1F_EventScript_CheckGiveAmuletCoin` exactly after the existing successful `giveitem ITEM_AMULET_COIN` path: retain `Common_EventScript_ShowBagIsFull`; set `FLAG_MOM_BATTLE_AVAILABLE`, then show the challenge yes/no prompt. Decline or battle loss leaves the availability flag set; acceptance runs `trainerbattle_no_intro TRAINER_MOM`.
- [ ] On victory, grant `ITEM_SCEPTILITE`, `ITEM_BLAZIKENITE`, and `ITEM_SWAMPERTITE` in that order with a bag-full branch after each grant, then set `FLAG_FOUGHT_MOM`. When `FLAG_FOUGHT_MOM` is set, use the existing Mom healing path and never repeat the rewards.
- [ ] Generate scripts and manually check accept, decline/retry, win, loss, and bag-full paths.

Expected: the Amulet Coin is not lost on a full bag; declining does not permanently block the challenge; the three stones are granted once.

### Task 4: Restore Leaf 2 and Mt. Pyre Archie

**Files:**
- Modify: `data/maps/NewMauville_Inside/map.json`
- Modify: `data/maps/NewMauville_Inside/scripts.inc`
- Modify: `data/text/trainers.inc`
- Modify: `data/maps/MtPyre_Summit/scripts.inc`

- [ ] Add Leaf with `OBJ_EVENT_GFX_LEAF` at `(27,34)`, `MOVEMENT_TYPE_FACE_RIGHT`, normal trainer sight range `6`, and `NewMauville_Inside_EventScript_Leaf2`. Use the archived intro/defeat flow and retain the Red-focused post-battle text in `data/text/trainers.inc`.
- [ ] In `MtPyre_Summit_EventScript_TeamAquaExits`, insert `trainerbattle_no_intro TRAINER_MT_PYRE_ARCHIE` after `MtPyre_Summit_Text_ArchieTryToStopMe` and before the existing orb/exit text. Do not alter the existing success-only removal, hide-flag, and `VAR_MT_PYRE_STATE` sequence.
- [ ] Generate map scripts and inspect the resulting `scripts.inc` for the two new trainer constants.

Expected: Leaf obeys normal trainer-defeat persistence; an Archie loss leaves all current Team Aqua objects and Mt. Pyre progression intact.

### Task 5: Build and runtime verification

**Files:**
- Modify only generated files produced by the build.

- [ ] Run `wsl.exe bash -lc "cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion && make -j8"` until it completes; if the mounted-workspace command times out, rerun incrementally and record the timeout separately from compiler failure.
- [ ] Run `git diff --check` and verify the five trainer IDs occur once in `include/constants/opponents.h`, `src/data/trainers.party`, and generated `src/data/trainers.h`.
- [ ] In mGBA, check Steven, Red (win/loss/reload), Mom (accept/decline/retry/win), Leaf, and Archie (win/loss) against the design exit criteria.
- [ ] Commit the reviewed source and generated files with `git commit -m "feat: restore deferred custom encounters"`.

## Plan Self-Review

- Shared ID allocation, five party records, map-object changes, event flows, rewards, failure behavior, generation, build, and runtime validation each have a task.
- The plan keeps current map JSON/Poryscript as the only source of truth and never copies legacy generated `.inc` files.
- No existing trainer is renumbered; the new count remains within the current fixed save allocation.
