# Friendship and Toxic Boost checkpoint - 2026-10-04

This follows `2026-10-04-hm-configuration-progress.md`. Only the two approved
balance adaptations and associated validation maintenance are in scope.
The entire custom-hack migration and gameplay acceptance are not complete.
Work remains on `codex/rom-hack-1.16.3-migration`, separate from master and
AI Trainer. No automatic push is part of this pass.

## Completed balance unit

`bdb80abf77 feat: restore friendship and poisoned Toxic Boost tuning`:

- The modern shared friendship evolution threshold is 120 instead of 160.
  The native GEN_8 switch and older 220 threshold remain. Normal evolution
  triggers, species declarations, explicit exceptions, day/night and Fairy
  move requirements, friendship gains and affection behavior are unchanged.
- Poisoned Toxic Boost users receive the archive's integer-truncated 1.3x
  Speed bonus, for both normal and bad poison. The current Speed function
  uses its passed effective ability, after Quick Feet and before Surge
  Surfer. Other abilities and modifier ordering remain intact. The existing
  physical damage bonus is untouched.

Runtime changes are confined to `src/pokemon.c` and `src/battle_main.c`.
No legacy battle or evolution engine was imported. The five user-authored
map/encounter cleanup paths from `bf8074499f` remain unchanged.

## Validation maintenance

The first wider map-import suite failed because the exact flags-header
postimage fingerprint predated the approved `db3cd5023a` EXP All flag rename.
All ten previously required map/reward constants were intact. Reversing
only `FLAG_TOGGLE_EXPALL` to its former unused name in memory reproduced
the prior fingerprint; no runtime regression or missing map flag was found.

`7ccc627005 fix: recognize approved EXP All dependency postimage` refreshes
that reviewed fingerprint and explicitly
requires the permanent EXP All flag at 0x23. It preserves strict
whole-file validation, the original baseline hash and all existing literals.
No maps, scripts, historical reports or runtime headers are regenerated.

## Verification evidence

- Independent balance specification and quality reviews approved the unit.
- Independent specification and quality reviews approved the metadata fix.
- Final combined integration review approved the changes and checkpoint;
  19 relevant focused checks were independently rerun, with source/ROM hashes
  and preserved map paths verified. Gameplay acceptance remains pending.
- Genuine independent pre-unit RED reproduction: five tests, 17 expected
  assertion failures, zero compilation/setup errors. No runtime source was
  reverted in the working tree for this reproduction.
- Fresh combined native-C run: 42 tests passed (four berry, 14 cap, 11 HM,
  eight configuration, five balance). Compiler flags include
  `-std=c11 -Wall -Wextra -Werror`; missing compiler fails, not skips.
- Balance fixtures compile the actual threshold and evolution condition
  cases, actual complete Speed function, native constants and badge math.
  Coverage includes 119/120/121 and old 219/220 boundaries; additional
  conditions; both poison types, non-poison/counter-only negatives; passed
  versus raw ability; integer rounding; stages, items, badge and side effects;
  Booster Energy precedence and pre-unit equality for other abilities.
- Independent old-metadata RED reproduction: nine tests, seven assertion
  failures, zero errors. Fourteen focused dependency-validator tests passed
  after correction. Eight new regressions cover approved acceptance,
  missing/altered EXP All flag, prior postimage and unrelated-edit rejection,
  original baseline and all ten prior constants.
- Fresh full map/event/reward importer suite: 154 tests passed. Combined
  with the 42 native-C checks above, 196 tests passed.
- Native generated sources and full Emerald ROM build passed after the two
  final runtime files were overlaid into the existing validation tree.
- All 21 current source/data paths (two new runtime files, 14 prior runtime
  overlays, five user-authored paths) match the native build copy byte-for-byte.

Build tree: `/home/jereme/pokeemerald-hm-config.08TZvd` in Ubuntu WSL, initially
archived from `5f9c2a1e32`, with all reviewed runtime overlays applied.
New logs: `balance-generation.log`, `balance-rom-build.log`.

ROM: 33,554,432 bytes; SHA-256:
`78f81d9253f09c46b9feec0de5ac6edeb3797fae10c78fec8726ae5e7d6895f7`.

Source hashes:

- `src/pokemon.c`: `dc01e69fa350e21eff5474d3368ce372330ddf6a97b3a64e4af4f3aaa0b25a3b`
- `src/battle_main.c`: `d68b58119ba637a640ecd62672de0c363b74f390745b8f5078892d4c71f42286`

No ROM, generated files or saves were copied back. Rebuild the usual workspace
ROM before playing these changes, or use the native validation ROM directly.
Stock upstream battle-suite compatibility is not claimed.

## Manual acceptance and remaining work

With a disposable save, check friendship evolution below/at 120 on normal
level-up, including Eevee day/night and Fairy-move variants. Check that a
poisoned Toxic Boost user changes turn order as expected, no boost without
poison, and suppression/ability changes use the effective ability. Fixtures
and compilation do not establish full in-game caller or on-screen behavior.
All prior HM/configuration/berry/cap/map acceptance checks remain pending.

These two completed outcomes supersede only the friendship and Toxic Boost
items in the prior inventory. Species stats/abilities/learnsets/evolutions,
remaining move/item-price data, Frontier/Tent teams, full-screen start menu,
Better Bag, deliberate bag restrictions and unresolved Route122 blocker
placement remain outside this pass.
