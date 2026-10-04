# Legacy restoration progress - 2026-10-04

This continues the 2026-10-03 map/event checkpoint. The target remains the
custom archived hack on Expansion 1.16.3, without the AI Trainer branch.
This berry/cap unit is implemented; the complete migration and gameplay
acceptance are still unfinished.

## Completed source units

- `e775e7b818`: eight archived starting-tree substitutions and the higher
  harvest calculation, using current berry IDs. Modern moisture/mulch logic
  remains intact. Existing saves are not reset or rewritten.
- `e11e6af9f5`: ten soft-cap milestones (15, 20, 26, 35, 39, 49, 53, 60, 69,
  81), including the Lilycove rival milestone, and archived party-relative
  experience scaling. After Champion, cap reduction ends. The original
  filtered-party denominator is deliberately retained.

Caps use current participation and Exp. Share hooks before modern experience
modifiers. At-cap factor is 0.3, above-cap factor is 0.0001, multiplied with
the party factor before one truncation. Integer arithmetic replaces archived
floating-point rounding noise; empty-party and overflow guards prevent
undefined/extreme-input failures. Rare Candy, EVs, affection, EXP All and
generation-based XP settings were not changed in this unit.

Pinned archive: `f5e81e85df6fe40ae490bf7268d0186d7f0426ed`.
The user's `bf8074499f` map/encounter cleanup is preserved with no further
changes to its five authored paths. Upstream animations and Psychic Noise
remain the selected implementations.

## Verification evidence

- Independent specification and quality reviews passed for both units.
  The final quality-review coverage suggestion was addressed with a full
  six-member mixed-party test.
- Fresh berry/cap run: all 18 tests passed (4 berry, 14 cap).
- Berry fixtures compile the actual current and archived C kernels and
  compare 1,310,720 inputs per watering mode; all starting-tree commands
  also match the archive after adapting item-to-berry identifiers.
- Cap fixtures compile actual `src/caps.c` with the real cap config header
  in ten variants. Coverage includes every milestone, all 27 relative
  factors and clamps, 4,050 combined cap/party/input cases, rounding,
  saturation, first-empty and six-member parties, eggs/fainted members,
  NONE/HARD/variable/optional EXP-up, unchanged EV modes, and existing hooks.
- Fresh existing map/event/reward regression run: all 146 tests passed.
  Together with the 18 berry/cap checks, this checkpoint passes 164 tests.
- Native validation: tools, generated sources and full ROM compile passed;
  applying the final cap files then recompiling/relinking also passed.
- Final ROM: 33,554,432 bytes, SHA-256
  `dcb5f1d13d92418e28b5964017414da7467269c200b12fd6724a103493cfc247`.
- Berry-only checkpoint ROM SHA-256:
  `5c225b76fb6e097a73209be00f2b4677c8b8d9f8aef8934bf0595f711fde8a77`.

The validation copy was created from `git archive a393fea195`, with the four
reviewed runtime files overlaid from the workspace. SHA-256 byte comparison
confirmed all four overlays and the five user-authored map/encounter paths
match the native build copy. Runtime overlay hashes:

| Path | SHA-256 |
| --- | --- |
| data/scripts/new_game.inc | c9c5c954f75724174f0c02ee73e70ca5072528784795d89b37b484559619472f |
| src/berry.c | 927e0fede8a442e9ed1c030f1a841a097d350d584224be600c6c97b289fac134 |
| src/caps.c | a52d31a9b604ba3cfae685d5edb87535c2dd729801d3cb9fde35bffadcf7fb44 |
| include/config/caps.h | 1b82e0a6ea68fc72a1a8b239ad3c31239d83c9939bc8cda43d8c30dfa17fbbd0 |

Build/log location on this machine:
`/home/jereme/pokeemerald-validation.dEggDc` inside Ubuntu WSL.
The initial `/tmp` build directory vanished after WSL restarted because
`/tmp` is a temporary filesystem; validation was repeated in this persistent
directory. No ROM, generated files or saves were copied into the repository.
Rebuild the usual workspace before playing its ROM, or use the validation
ROM directly. The existing workspace ROM was not replaced.

Reproduce the checks with native Windows Python for the existing importer
suite and native WSL Python/cc for the real-C fixtures:

```powershell
python -m unittest tools.migration.tests.test_map_event_merge
wsl.exe -e bash -lc 'cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion && python3 -m unittest tools.migration.tests.test_legacy_berries tools.migration.tests.test_legacy_caps -v'
```

The stock battle suite's vanilla-experience expectations were not adapted or
claimed compatible with intentionally changed cap defaults. Compilation and
focused tests do not prove final on-screen XP amounts after every upstream
modifier.

## Manual acceptance pending

Use a disposable fresh save to inspect all eight substituted trees on Routes
115/116/110/121/123. Check planted berries with zero through four watered
stages, including yields above table maxima. Do not reset existing save trees.

Check each badge transition and the Lilycove rival fly-away. Compare awarded
XP below, at and above the cap, both for participants and Exp. Share. Sample
low-level catch-up, high-level penalties and a mixed six-member party. Verify
that Champion completion ends cap reduction while party scaling remains.

The prior map/NPC/trainer/warp/reward-retry playtests are also still pending.

## Remaining migration work

The older feature manifest's `planned` entries are historical dispositions,
not completion evidence. This note supersedes them for the two units above.
Outstanding areas from the current checkpoint remain:

- Strength and Dive/surfacing HM-possession gates.
- Poisoned Toxic Boost speed tuning and disabled affection effects.
- Remaining move, evolution, item-price and Pokemon configuration values;
  EXP All and reusable-TM configuration.
- Battle Frontier roster tuning and Fallarbor Tent Wailmer's Ice Beam.
- Full-screen start menu and additional Better Bag pockets.
- Route 122 blocker placement decision: the archive set its flag but did
  not contain an object from which a working placement could be inferred.

The next small independent restoration unit is the remaining HM gates.
Larger battle/data and UI changes should stay separate.
