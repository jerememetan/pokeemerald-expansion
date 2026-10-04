# HM and native-configuration checkpoint - 2026-10-04

This follows the berry/cap checkpoint in `2026-10-04-migration-progress.md`.
The HM and configuration source units are implemented and compiled, not the
entire custom-hack migration. Disposable-save gameplay acceptance remains
pending. Work stays on `codex/rom-hack-1.16.3-migration`; `master` and the AI
Trainer branch were not changed by this pass.

## Completed units

- `106baea6bd`: all eight Emerald HMs require their badge and received-HM
  flag, without teaching any party member the move. A shared helper selects
  the first non-egg animation actor and fails safely for empty/all-egg parties.
  Script outputs, non-HM learned-move rules, terrain/follower/link safeguards,
  existing effects and activated Strength session state remain intact.
  Direct Cut/Rock Smash scripts remain unchanged. Actual FRLG badge-only
  mapping is retained; its upstream receipt aliases are zero.
- The existing party menu now has one HMs entry and an unlocked-HM submenu.
  Fly and Flash are accessible without teaching. Eight HMs plus Cancel fit
  the nine-entry action buffer; the worst-case root also fits nine entries.
  This is not a full-screen start-menu restoration.
- `db3cd5023a`: 21 proven native settings/constants restored, with only eight
  headers changed. The full value map is in
  `../specs/2026-10-04-native-configuration-design.md`.

The configuration choices include reusable TMs, held evolution items usable
from the Bag, native EXP All, Frostbite, disabled affection battle effects,
Gen8 Protean/Libero and Intrepid Sword/Dauntless Shield, faster battle pauses,
quick Run cursor, Synchronize nature matching, 20 percent double encounters
with two usable members required, five additional Shiny Charm rolls, base
shiny odds 128/65536 (1/512), four guaranteed perfect legendary IVs, the native
HGSS Pokédex and three debug menus disabled in developer builds too.

EXP All uses the native Exp. Share Key Item USE action. Permanent toggle
`FLAG_TOGGLE_EXPALL` occupies the archive's unused slot `0x23`, above temporary
flags. `FLAG_RECEIVED_EXP_SHARE` (`0x110`) remains the separate Mr. Stone reward
flag. A fresh game starts OFF; receiving the item does not auto-enable it.
Using it toggles ON/OFF, including the registered-overworld route. No old
item or experience engine was copied.

## Historical evidence and retained equivalents

Archive: `f5e81e85df6fe40ae490bf7268d0186d7f0426ed`. Configuration authorship
comparison uses effective older upstream `1565171235`, not merge-base
`024848a9e9`: the latter's 1.8.1 merge was explicitly reverted. There are no
authored old macro deltas in Pokemon/species-enabled configuration against
the effective baseline. Keep current latest data and species enablement.

Eleven other archived overworld ability choices already have equivalent
current consumers. Expanded move names and nature mints are already native.
Those settings/engines were not blanket-replaced. Current move animations
and Psychic Noise remain the user-selected versions.

The user's `bf8074499f` cleanup is unchanged on all five authored paths:
Route123 map, layouts registry, heal locations, region sections and wild
encounters. No maps, scripts, encounters, teams or saves were rewritten here.

## Verification evidence

- Independent specification and quality reviews approved each source unit.
- Final combined integration review approved both commits: no flag collisions,
  menu-index errors, hook conflicts or scope leaks found.
- Genuine HM RED: 11 tests, 117 assertion failures after successful native
  compilation. Final HM suite compiles the real shared helper, full field-move
  table, script/Surf functions and party root/submenu/window functions.
- Genuine configuration RED: eight tests, 49 expected assertion failures,
  no compilation errors. The unrelated TM_CASE fixture match was corrected
  before that run and before runtime edits.
- Fresh combined native-C run: 37 tests passed (four berry, 14 cap, 11 HM,
  eight configuration). Native compiler uses `-std=c11 -Wall -Wextra -Werror`.
  Config tests compile actual headers/constants and actual native EXP Share
  getter/item functions, both bag and registered paths, flag isolation,
  debug build modes and the disabled legendary-IV branch. Missing `cc` fails.
- Fresh map/event/reward importer suite: all 146 tests passed. Total: 183.
- Exact configuration macro allowlist and unchanged species settings passed;
  `git diff --check` passed. Stock battle-suite compatibility is not claimed.
- Native tools, generated sources and full Emerald ROM build passed. The
  HM-only build passed first, then all final runtime overlays were applied
  and generation/full build passed again with both units together.
- All 14 changed runtime files and the five user-authored paths were SHA-256
  compared between workspace and native build copy; every pair matched.

Build copy: `/home/jereme/pokeemerald-hm-config.08TZvd` in Ubuntu WSL, archived
from `5f9c2a1e32` then overlaid with the 14 reviewed runtime files.
Logs: `tools-build.log`, `generation.log`, `rom-build.log`,
`configuration-generation.log`, `configuration-rom-build.log`.

Final ROM: 33,554,432 bytes; SHA-256:
`24788d03f5481881f32cf73dd06f2c030af4c9c9a36e2c046b4e9b0c5017c098`.
HM-only ROM hash:
`d990d065f46788e6a8385a600935f0c8a254857c210e78f60d319d19610b3ca5`.

No generated files, ROM or saves were copied back to the repository. The
usual workspace ROM was not replaced. Rebuild it before playing these changes,
or use the native validation ROM directly.

Reproduce checks:

```powershell
python -m unittest tools.migration.tests.test_map_event_merge
wsl.exe -e bash -lc 'cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion && python3 -m unittest tools.migration.tests.test_legacy_berries tools.migration.tests.test_legacy_caps tools.migration.tests.test_hm_unlocks tools.migration.tests.test_native_configuration -v'
```

## Manual acceptance pending

Use a disposable save to check each HM before/after both prerequisites, with
no learned HM, then an egg-only party. Exercise the fully unlocked HMs menu,
Cancel, Fly return, Flash in a cave, Strength persistence, Surf, Dive/surfacing
and Waterfall direction/terrain. Smoke-test follower and link restrictions.

Check EXP All receipt while OFF, bag/registered toggles and actual party XP;
reusable TM count, held-evolution-item consumption, double encounters,
ability behaviour, Frostbite and the HGSS Pokédex. Compilation and fixtures
do not prove on-screen effects or statistical shiny odds in a playthrough.
Prior berry/cap/map/NPC/warp/reward acceptance remains pending too.

## Remaining migration work

This note supersedes earlier inventory dispositions only for HM requirements
and the specific native choices above. It does not mark every planned bucket
complete. Outstanding custom data/behaviour includes:

- Friendship evolution threshold 120: native generation choice offers
  160/220, not 120; needs a separate numeric adaptation.
- Per-species stats, abilities, learnsets/evolutions and remaining custom
  move and item-price data, not restored through generation settings alone.
- Toxic Boost's custom poisoned 1.3x Speed algorithm.
- Battle Frontier roster tuning and Fallarbor Tent Wailmer's Ice Beam.
- Full-screen start menu and additional Better Bag pockets. Read-only checks
  found this checkout still uses the regular start menu and five standard
  Bag pockets; HGSS Pokédex is a separate native toggle.
- Deliberate bag-restriction policy: old `B_FLAG_NO_BAG_USE=1` named temporary
  flag 1, not an enabled boolean. Current `B_VAR_NO_BAG_USE` requires a variable
  ID with a mode value. The unsafe old literal was not copied.
- Route122 blocker placement: archive set a flag but contained no object
  from which to infer a working placement.

Emerald configuration is the target. Preserving FRLG HM callbacks is not a
claim that the Emerald-specific EXP All flag configuration supports FRLG.
