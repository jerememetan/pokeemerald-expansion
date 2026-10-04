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

- [ ] Compile actual source threshold and native `IF_MIN_FRIENDSHIP` case
  with current config. Independently assert boundary behavior, not only
  textual presence: 119 false, 120/121 true. Compile generation variants
  GEN_7/GEN_8/GEN_LATEST; modern thresholds 120, old 220. Check the native
  species friendship conditions and retained day/night/Fairy requirements.
- [ ] Compile full actual speed function and pinned pre-unit counterpart
  with narrow dependency stubs and real relevant constants. Compare poisoned
  Toxic Boost to the independent archived `(speed * 130) / 100` formula;
  all other cases must match pre-unit behavior. Cover both poison bits,
  non-poison/toxic-counter-only states, effective ability, integer rounding,
  stages, Choice Scarf/halving, Tailwind/swamp and badge composition.
- [ ] Run `wsl.exe -e bash -lc 'cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion && python3 -m unittest tools.migration.tests.test_friendship_toxic_boost -v'`.
  RED must show expected assertion failures, not fixture compile failures.
  Compiler is `cc -std=c11 -Wall -Wextra -Werror`; never skip missing cc.
- [ ] Replace only the modern threshold literal:

```c
#define FRIENDSHIP_EVO_THRESHOLD ((P_FRIENDSHIP_EVO_THRESHOLD >= GEN_8) ? 120 : 220)
```

- [ ] Add only this speed branch after Quick Feet:

```c
else if (ability == ABILITY_TOXIC_BOOST && gBattleMons[battler].status1 & STATUS1_PSN_ANY)
    speed = (speed * 130) / 100;
```

- [ ] Run the same focused command GREEN; check `git diff --check` and exact
  two-file runtime allowlist. No production test hooks or old engine import.
- [ ] Independent spec review, then quality review; fix and rereview findings.

## Task 2: Shared validation and checkpoint

- [ ] Run all prior focused native-C modules plus the new module:
  `wsl.exe -e bash -lc 'cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion && python3 -m unittest tools.migration.tests.test_legacy_berries tools.migration.tests.test_legacy_caps tools.migration.tests.test_hm_unlocks tools.migration.tests.test_native_configuration tools.migration.tests.test_friendship_toxic_boost -v'`.
- [ ] Run `python -m unittest tools.migration.tests.test_map_event_merge`.
- [ ] Overlay the two reviewed runtime sources into the existing persistent
  `/home/jereme/pokeemerald-hm-config.08TZvd` native validation tree. Confirm
  unchanged prior runtime overlays and user-authored paths match workspace.
  Run `make -j4 generated` then `make -j4`; check exit statuses and final ROM
  size/SHA-256. Do not copy generated files, ROM or saves into the repository.
- [ ] Save the reviewed changes using explicit runtime/test paths; record
  verification, manual evolution/turn-order checks and remaining migration
  work in a dated checkpoint. Commit docs separately. No automatic push.
- [ ] Final combined integration review. Keep master and AI Trainer separate.
