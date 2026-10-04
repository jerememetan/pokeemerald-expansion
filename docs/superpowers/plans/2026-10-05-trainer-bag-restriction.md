# Trainer Bag Restriction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development.
> Steps use checkbox syntax for tracking.

**Goal:** Apply the selected trainer-only bag policy without allocating save data.

**Architecture:** One native configuration change. Existing VarGet literal
semantics and IsAllowedToUseBag implement the rule; no engine adaptation.

**Tech Stack:** C, Python unittest, native WSL cc, Git and Make.

## Task 1: Configuration and bounded native regression

Files: modify `include/config/battle.h` and
`tools/migration/tests/test_native_configuration.py`; create
`tools/migration/tests/test_bag_restriction.py`. Baseline `6c4fde611f`.

- [x] Compile actual current config and actual GetVarPointer/VarGet/VarSet
  from `src/event_data.c` plus IsAllowedToUseBag from `src/battle_util.c`.
  Native `cc -std=c11 -Wall -Wextra -Werror` is mandatory. Supply only
  external globals/types/storage; do not recreate either policy or VarGet.
  Include actual variable and battle constants. Variant overrides use the
  current header followed by `#undef B_VAR_NO_BAG_USE` and a test definition.
- [x] Assert actual default behavior: trainer flags return FALSE, wild flags
  return TRUE, also with BATTLE_TYPE_DOUBLE. Test modes NO_BAG_RESTRICTION,
  NO_BAG_AGAINST_TRAINER, NO_BAG_IN_BATTLE and invalid fallback. Compile a
  real unused-variable-ID variant and set its mode via actual VarSet to
  exercise override behavior. Check literal VarGet does not access saved
  variables; VarSet on the literal returns FALSE and leaves every value intact.
- [x] Run focused RED before changing runtime configuration:
  `wsl.exe -e bash -lc 'cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion && python3 -m unittest tools.migration.tests.test_bag_restriction -v'`.
  Expected assertion failures for default trainer permission, not fixture errors.
- [x] Change only the bag configuration line to:

```c
#define B_VAR_NO_BAG_USE NO_BAG_AGAINST_TRAINER // Literal mode 0/1/2, or a variable ID containing that mode.
```

  Preserve surrounding style/alignment and add a concise mode explanation.
  Do not allocate a variable, change helper/callers, or alter save initialization.
- [x] Extend the existing explicit macro allowlist, not archived SETTINGS:

```python
allowed[CONFIG + "battle.h"].add("B_VAR_NO_BAG_USE")
```

- [x] Run the focused module plus native-configuration checks GREEN. Verify
  exact one-file runtime allowlist and `git diff --check`. Read-only spec
  review, then quality review; fix and rereview findings.

## Task 2: Integration and checkpoint

- [x] Run all native-C modules:
  `wsl.exe -e bash -lc 'cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion && python3 -m unittest tools.migration.tests.test_legacy_berries tools.migration.tests.test_legacy_caps tools.migration.tests.test_hm_unlocks tools.migration.tests.test_native_configuration tools.migration.tests.test_friendship_toxic_boost tools.migration.tests.test_bag_restriction -v'`.
  Then `python -m unittest tools.migration.tests.test_map_event_merge`.
- [x] Overlay only `include/config/battle.h` into the existing native build
  `/home/jereme/pokeemerald-hm-config.08TZvd`. Check all previously reviewed
  runtime/data overlays still match. Run `make -j4 generated` and `make -j4`,
  inspect exit statuses and final ROM size/SHA-256. No outputs copied back.
- [x] Final combined integration review. Commit the explicitly scoped
  config/tests together, and save a dated checkpoint separately. Mark actual
  completed checks here. Record manual trainer/wild/capture testing pending,
  current skip of Pokemon stats/abilities/evolution edits, unchanged capacity
  and saves, and no automatic push.
