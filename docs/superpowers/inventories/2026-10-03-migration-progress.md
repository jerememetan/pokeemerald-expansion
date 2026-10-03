# Legacy restoration progress — 2026-10-03

The target remains Expansion 1.16.3 with the archived custom hack restored.
The AI Trainer branch is outside this migration. The complete migration is
not yet finished; compilation alone does not establish in-game parity.

## Current map-event checkpoint

The pinned event merge covers 61 shared layouts, 75 shared maps, and 69 maps
with archived event changes. It produces 68 changed map documents. All 68
live documents match independently regenerated candidates, including the
five maps resaved with different JSON field ordering. Only formatting was
normalized; their event values and order were preserved.

The restoration includes 44 custom visible-item adaptations, six of which
give five items, and six custom TM mappings: Drain Punch, Flip Turn,
Thunder Wave, U-turn, Volt Switch, and Hurricane. TM32 retains its archived
3000 price. Current upstream move animations and Psychic Noise remain the
chosen implementations.

A final review found and corrected the three paired gym rewards' use of bag
possession as delivery state. Six existing unused permanent flags now track
each successful TM and Mega Stone delivery independently. Real-source
branch checks cover pre-owned items, a failed TM, a failed stone followed by
removal of the delivered TM, and the completed leader interaction. The full
focused migration suite passes all 146 tests; in-game sampling is still
pending.

The heal-location JSON truncation was repaired separately. All 949 tracked
authored JSON documents below `data` and `src` parse successfully. The user
confirmed that their ROM compiles; no playthrough has been performed.

## Automated checkpoint evidence

- Fresh full migration suite: 146 tests passed.
- Independent specification and code-quality reviews: approved after fixes.
- Authoritative map hashes: all 68 exactly match the canonical report.
- Post-state importer run: zero authoritative replacements.
- Recovery regressions: failed recovery naming retains and names the
  original copies while other maps roll back; a concurrent write during
  rollback retains both the writer's bytes and a named exact preimage.
- Clean WSL-native tools, map generation, and full ROM build: exit 0.
  The runtime sources in the build copy exactly match all 87 modified
  `data`, `include`, and `src` paths, including the separate user edits.
- Generated ROM: 33,554,432 bytes; SHA-256
  `93acb13325df7b51d46cf2d4a0e782a26d148eb2ddf6b7e914e245aac99bcb94`.

The clean build used a disposable native filesystem copy. No ROM, save,
generated include, or candidate artifact is included in the checkpoint
commit. Rebuild the normal workspace before playtesting the latest reward
changes; its earlier compiled ROM was not replaced by the validation build.

## Remaining restoration work

The feature inventory's old `planned` statuses are not completion evidence.
A fresh source audit identified these outstanding areas:

- New-game berry varieties and higher harvest yields.
- Remaining Strength and Dive/surfacing HM-possession gates.
- Custom level-cap progression and experience reduction.
- Poisoned Toxic Boost speed tuning and disabled affection effects.
- Remaining custom move, evolution, item-price, and Pokémon configuration
  values; EXP All and reusable-TM configuration.
- Battle Frontier roster tuning and Fallarbor Tent Wailmer's Ice Beam.
- The full-screen start menu and additional Better Bag pockets.

The Mom challenge and starter Mega Stone rewards are already present in
the current house scripts, but still need in-game checks. The Route 122
blocker requires a separate placement decision: the archive set its flag
but did not contain the corresponding object, so a working placement cannot
be inferred from the old source.

The next small, independent restoration unit is berry parity: the eight
initial-tree substitutions and the archived yield calculation, adapted to
the current berry system. Larger UI and battle changes should stay separate.

## User edits kept separate

Do not stage or overwrite newer edits to `data/layouts/Route123/map.bin`,
`data/layouts/layouts.json`, `src/data/wild_encounters.json`,
`src/data/region_map/region_map_sections.json`, or the pre-existing formatting
edit in `src/data/heal_locations.json` as part of the map-event checkpoint.

## Manual acceptance still required

Inspect high-change maps and all custom-map transitions in PoryMap. Test
moved NPCs, trainer interactions, item quantities, signs/hidden items,
coordinate triggers, warps, and partial gym-reward retries in mGBA using a
disposable save. These checks remain pending and must not be reported as
completed based on successful generation or compilation.
