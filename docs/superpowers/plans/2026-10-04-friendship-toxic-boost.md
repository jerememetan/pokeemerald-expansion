# Friendship and Toxic Boost Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development.
> Steps use checkbox syntax for tracking.

**Goal:** Restore modern friendship evolution at 120 and poisoned Toxic
Boost's archived 1.3x Speed bonus.

**Architecture:** Two minimal edits in existing native calculation paths;
retain current evolution conditions and Speed-modifier ordering.

**Tech Stack:** C, Python unittest, native WSL cc, Git and Make.

---

## Task 1: Two bounded balance tunings

Modify only `src/pokemon.c`, `src/battle_main.c`.
Create `tools/migration/tests/test_friendship_toxic_boost.py`.
Archive: `f5e81e85df6fe40ae490bf7268d0186d7f0426ed`.
Pre-unit source baseline: `0758db1dc4`.

- [x] Compile actual source threshold and native `IF_MIN_FRIENDSHIP` case
  with current config. Independently assert boundary behavior, not only
  textual presence: 119 false, 120/121 true. Compile generation variants
  GEN_7/GEN_8/GEN_LATEST; modern thresholds 120, old 220. Check the native
  species friendship conditions and retained day/night/Fairy requirements.
- [x] Compile full actual speed function and pinned pre-unit counterpart
  with narrow dependency stubs and real relevant constants. Compare poisoned
  Toxic Boost to the independent archived `(speed * 130) / 100` formula;
  all other cases must match pre-unit behavior. Cover both poison bits,
  non-poison/toxic-counter-only states, effective ability, integer rounding,
  stages, Choice Scarf/halving, Tailwind/swamp and badge composition.
- [x] Run `wsl.exe -e bash -lc 'cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion && python3 -m unittest tools.migration.tests.test_friendship_toxic_boost -v'`.
  RED must show expected assertion failures, not fixture compile failures.
  Compiler is `cc -std=c11 -Wall -Wextra -Werror`; never skip missing cc.
- [x] Replace only the modern threshold literal:

```c
#define FRIENDSHIP_EVO_THRESHOLD ((P_FRIENDSHIP_EVO_THRESHOLD >= GEN_8) ? 120 : 220)
```

- [x] Add only this speed branch after Quick Feet:

```c
else if (ability == ABILITY_TOXIC_BOOST && gBattleMons[battler].status1 & STATUS1_PSN_ANY)
    speed = (speed * 130) / 100;
```

- [x] Run the same focused command GREEN; check `git diff --check` and exact
  two-file runtime allowlist. No production test hooks or old engine import.
- [x] Independent spec review, then quality review; fix and rereview findings.

## Task 2: Refresh approved EXP All dependency fingerprint

Validation exposed a stale flags-header postimage hash from before the approved
`db3cd5023a` EXP All rename. All ten existing required constants remain intact.
Undoing only that rename in memory reproduces the old reviewed postimage hash.
This maintenance task changes no runtime behavior or map data.

- [x] Add focused regression tests in `tools/migration/tests/test_map_event_merge.py`
  proving the approved header passes, while the pre-EXP All header, an altered
  EXP All flag, and unrelated edits fail. Demonstrate genuine RED first.
- [x] Change only the flags-header `new_sha256` in
  `tools/migration/merge_legacy_map_events.py` to
  `dda3eb5f9f4e7814273689b70080d9f882811fe1f630a1b88501353f9d8cd04a`,
  and require `#define FLAG_TOGGLE_EXPALL   0x23` explicitly. Preserve the
  baseline hash, all existing literals, and strict whole-file validation.
- [x] Run focused GREEN, independent spec review, then quality review.
  Do not regenerate maps or historical reports. Commit tool/tests separately.

## Task 3: Shared validation and checkpoint

- [x] Run all prior focused native-C modules plus the new module:
  `wsl.exe -e bash -lc 'cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion && python3 -m unittest tools.migration.tests.test_legacy_berries tools.migration.tests.test_legacy_caps tools.migration.tests.test_hm_unlocks tools.migration.tests.test_native_configuration tools.migration.tests.test_friendship_toxic_boost -v'`.
- [x] Run `python -m unittest tools.migration.tests.test_map_event_merge`.
- [x] Overlay the two reviewed runtime sources into the existing persistent
  `/home/jereme/pokeemerald-hm-config.08TZvd` native validation tree. Confirm
  unchanged prior runtime overlays and user-authored paths match workspace.
  Run `make -j4 generated` then `make -j4`; check exit statuses and final ROM
  size/SHA-256. Do not copy generated files, ROM or saves into the repository.
- [x] Save the reviewed changes using explicit runtime/test paths; record
  verification, manual evolution/turn-order checks and remaining migration
  work in a dated checkpoint. Commit docs separately. No automatic push.
- [x] Final combined integration review. Keep master and AI Trainer separate.
