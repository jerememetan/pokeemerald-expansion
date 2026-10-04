# Friendship and Toxic Boost restoration

Approved outcomes: the user requested the two proposed remaining small
changes: friendship evolution at 120 and poisoned Toxic Boost at 1.3x Speed.
Continue the approved native-adaptation strategy; no new evolution or battle
engine. Starting checkpoint: `0758db1dc4` on the migration branch.

## Smallest implementation

Lower the modern branch of `FRIENDSHIP_EVO_THRESHOLD` in `src/pokemon.c`
from 160 to 120. Keep the current `>= GEN_8` generation switch and older
220 branch. Current configuration is `GEN_LATEST`, so friendship conditions
in the native species tables use 120. Do not alter friendship gain, affection,
level-up triggers, day/night or move-type requirements, or species tables.
The archived macro used 120 for its configured modern game; retain the
current switch rather than transplant its obsolete generation guard.

In `GetBattlerTotalSpeedStat` in `src/battle_main.c`, insert the archived
Toxic Boost branch immediately after Quick Feet and before Surge Surfer:

```c
else if (ability == ABILITY_TOXIC_BOOST && gBattleMons[battler].status1 & STATUS1_PSN_ANY)
    speed = (speed * 130) / 100;
```

Both ordinary and bad poison qualify. No poison, burn, paralysis, sleep,
freeze/Frostbite, or the toxic-counter bits alone must not grant the bonus.
Use the passed effective/AI-estimated ability, not a fresh hidden-ability
lookup. Keep native stage, weather, badge, item, Tailwind, paralysis and swamp
ordering, including integer truncation at the archived position. Leave
Toxic Boost's existing physical damage bonus and all other ability branches
unchanged. No float arithmetic, new ability IDs or extra settings.

Runtime allowlist: only `src/pokemon.c` and `src/battle_main.c`.
New test: `tools/migration/tests/test_friendship_toxic_boost.py`.
No maps, scripts, encounters, trainer teams, item tables, UI, config headers,
generated sources, existing saves or unrelated feature edits.

## Verification

Compile the actual threshold definition and actual native friendship
condition case under narrow native-C fixtures. Verify 119 fails, 120 and
121 pass, and older generation's 219/220 boundary remains. Check real species
entries still use the common threshold and retain additional conditions;
explicit exceptional friendship thresholds are not rewritten.

Compile the whole actual `GetBattlerTotalSpeedStat` under narrow dependencies.
Independently read the archived Toxic Boost branch and its integer formula.
Verify ordinary/bad poison, toxic counters without poison, other statuses,
wrong/effective ability, small and odd Speed truncation, non-neutral stages,
Choice Scarf/halving items, Tailwind/swamp and badge composition. Compare
non-Toxic cases against the pre-unit actual speed function to detect unrelated
changes. Missing native cc is an error, not a skipped test.

Tests must fail for the intended absent behaviour before runtime edits, then
pass. Independent specification then quality review, existing focused
migration checks, exact-source native ROM compile and recorded source/ROM
hashes precede completion. Gameplay evolution and turn-order acceptance
remain explicitly pending. Do not automatically push or merge these new
commits; the preceding push request covered the earlier checkpoint.
