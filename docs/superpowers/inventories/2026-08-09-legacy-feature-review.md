# Legacy Feature Review

This is the exhaustive feature disposition for [the generated path inventory](2026-08-09-legacy-feature-inventory.json), comparing `master` (Expansion 1.16.3, `c828d12721`) with `archive/master-pre-1.16.3` (`f5e81e85df`). The checked-in feature manifest below maps every generated destination path to exactly one feature entry. It is deliberately selector-based: the inventory remains the canonical 2,124-path listing, while the manifest makes the review readable and mechanically auditable.

“Upstream equivalent” means retain the 1.16.3 implementation and, where needed, configure it; it never means copy the archived implementation. “Planned” is an inventory status, not a claim that ROM behavior has already been ported.

| Feature | Legacy paths | 1.16.3 equivalent or target paths | Decision | Phase | Acceptance evidence |
| --- | --- | --- | --- | --- |
| Upstream map and event source conversion | [`upstream-map-event-source`](#feature-manifest) — all `maps-and-events` paths except the two explicit extension layouts | Current `data/maps/**`, `data/layouts/**`, JSON/Poryscript generation | Use upstream equivalent | 2 | The paths include generated `.inc` files and broad map-source format drift. Keep current source formats; regenerate derived scripts, build, and smoke-test affected vanilla maps. |
| Littleroot and Verdanturf extensions | [`custom-map-extensions`](#feature-manifest) — `data/layouts/{Littleroot,Verdanturf}_Extension/**` | Current layout JSON, map headers, events, and warps | Modern adaptation | 2 | These are the only added extension-layout directory names in the inventory. Recreate geometry, connections, events, and warps in current formats; enter and leave both maps from a clean save. |
| Full-screen start menu | [`fullscreen-start-menu`](#feature-manifest) — full-screen graphics plus start-menu implementation paths | Current `src/start_menu.c`, UI assets, current menu interfaces | Modern adaptation | 3 | `git show --stat 1b4f48d986` adds the fullscreen assets and implementation. Verify every visible action and the archived gender/clock variants on the current menu APIs. |
| Better Bag and remaining QoL UI | [`better-bag-and-qol-ui`](#feature-manifest) — remaining UI-category paths | Current `src/item_menu.c`, `src/option_menu.c`, item configuration and UI assets | Modern adaptation | 3 | BetterBag history (`3480da2c61`, `f5f24a808a`, `ef69dde01e`) identifies pocket and interface behavior. Verify all pockets, item selection/use, and options; retain current menu internals. |
| Species, item, move, trainer, encounter, graphic, and cry corpus | [`legacy-content-corpus`](#feature-manifest) — every `game-content` path | Current `src/data/**`, `graphics/**`, `sound/**`, trainer/encounter generators | Use upstream equivalent | 2 | `git show --stat 624403ccab` identifies legacy mint work, while the inventory’s Gen 9 assets/tables overlap maintained expansion content. Compare the legacy deltas at current source-table granularity; configure or add only content absent from 1.16.3, then verify linkage and gameplay use. |
| Battle Frontier roster tuning | [`frontier-roster-tuning`](#feature-manifest) — the archived Frontier roster table and its direct constants/engine callers | Current `src/data/battle_frontier/**`, current Frontier configuration | Modern adaptation | 4 | `git show --stat f5e81e85df` changes `battle_frontier_mons.h`, `battle_tower.c`, and the Frontier constant. Re-express only its roster/rule deltas against 1.16.3 and verify a representative facility streak. |
| Legacy battle engine, config, and tests | [`upstream-gameplay-and-battle`](#feature-manifest) — all remaining `gameplay-and-battle` paths | Current battle engine, config headers, scripts, macros, and `test/battle/**` | Use upstream equivalent | 4 | `476030333c` documents EXP All and `624403ccab` documents mint behavior; 1.16.3 supplies both systems. Configure current behavior if the archived setting differs; run targeted battle tests and EXP/mint manual checks without restoring obsolete engine code. |
| Historical tooling and generated material | [`historical-tooling-and-generated-material`](#feature-manifest) — every `tooling-and-generated-output` path | Current `Makefile`, tools, docs, generators, CI, and generated outputs | Use upstream equivalent | 5 | These paths are outside all feature-source classifiers and include old build/docs/generated artifacts. Build with the supported current command and regenerate outputs; do not import archived infrastructure. |

## Feature manifest

The machine-readable manifest supplies the behavior, dependencies, validation, status, evidence, target paths, permitted decision, and path selector for every table entry. A selector matches a record only when its `category` is equal and its path has a listed prefix; `exclude_prefixes` then removes a match. Paths are evaluated against all entries, so a gap or overlap fails validation.

<!-- feature-manifest
{
  "features": [
    {
      "id": "upstream-map-event-source",
      "legacy_paths": [{"category": "maps-and-events", "prefixes": ["data/maps/", "data/layouts/"], "exclude_prefixes": ["data/layouts/Littleroot_Extension/", "data/layouts/Verdanturf_Extension/"]}],
      "target_paths": ["data/maps/**", "data/layouts/**", "tools/poryscript/**"],
      "decision": "Use upstream equivalent", "phase": 2, "status": "planned",
      "behavior": "Keep the current map source pipeline and vanilla map behavior.",
      "dependencies": ["current JSON/Poryscript generators"],
      "validation": ["regenerate map scripts", "supported build", "affected-map smoke test"],
      "evidence": ["git diff --name-status master...archive/master-pre-1.16.3"]
    },
    {
      "id": "custom-map-extensions",
      "legacy_paths": [{"category": "maps-and-events", "prefixes": ["data/layouts/Littleroot_Extension/", "data/layouts/Verdanturf_Extension/"]}],
      "target_paths": ["data/layouts/Littleroot_Extension/**", "data/layouts/Verdanturf_Extension/**", "data/maps/**"],
      "decision": "Modern adaptation", "phase": 2, "status": "planned",
      "behavior": "Preserve the two named custom extension maps, their connections, and their events.",
      "dependencies": ["upstream map source pipeline"],
      "validation": ["clean-save entry and exit", "warp/event checks", "supported build"],
      "evidence": ["inventory paths data/layouts/Littleroot_Extension/*", "inventory paths data/layouts/Verdanturf_Extension/*"]
    },
    {
      "id": "fullscreen-start-menu",
      "legacy_paths": [{"category": "ui-and-quality-of-life", "prefixes": ["graphics/ui_startmenu_full/", "src/ui_startmenu_full.c", "src/start_menu.c", "include/ui_startmenu_full.h", "include/start_menu.h"]}],
      "target_paths": ["src/start_menu.c", "graphics/ui_startmenu_full/**", "include/start_menu.h"],
      "decision": "Modern adaptation", "phase": 3, "status": "planned",
      "behavior": "Preserve the archived full-screen menu presentation and its gender/clock variants.",
      "dependencies": ["current start-menu and option-menu APIs"],
      "validation": ["all start-menu actions", "gender/clock variants", "supported build"],
      "evidence": ["git show --stat 1b4f48d986"]
    },
    {
      "id": "better-bag-and-qol-ui",
      "legacy_paths": [{"category": "ui-and-quality-of-life", "prefixes": [""], "exclude_prefixes": ["graphics/ui_startmenu_full/", "src/ui_startmenu_full.c", "src/start_menu.c", "include/ui_startmenu_full.h", "include/start_menu.h"]}],
      "target_paths": ["src/item_menu.c", "src/option_menu.c", "include/config/item.h", "graphics/interface/**"],
      "decision": "Modern adaptation", "phase": 3, "status": "planned",
      "behavior": "Preserve the archived bag-pocket and related UI behavior without reintroducing its old menu implementation.",
      "dependencies": ["current item configuration", "current menu framework"],
      "validation": ["open every pocket", "select/use items", "option-menu smoke test"],
      "evidence": ["git show --stat 3480da2c61", "git show --stat f5f24a808a", "git show --stat ef69dde01e"]
    },
    {
      "id": "legacy-content-corpus",
      "legacy_paths": [{"category": "game-content", "prefixes": [""]}],
      "target_paths": ["src/data/**", "graphics/**", "sound/**", "data/trainers/**", "data/wild/**"],
      "decision": "Use upstream equivalent", "phase": 2, "status": "planned",
      "behavior": "Retain only archived content deltas that 1.16.3 does not already provide.",
      "dependencies": ["current species/item/move/trainer/encounter data generators"],
      "validation": ["source-table comparison", "asset linkage", "item/encounter/trainer smoke tests"],
      "evidence": ["git show --stat 624403ccab", "inventory game-content paths"]
    },
    {
      "id": "frontier-roster-tuning",
      "legacy_paths": [{"category": "gameplay-and-battle", "prefixes": ["src/data/battle_frontier/battle_frontier_mons.h", "src/battle_tower.c", "include/constants/battle_frontier.h"]}],
      "target_paths": ["src/data/battle_frontier/**", "src/battle_tower.c", "include/constants/battle_frontier.h"],
      "decision": "Modern adaptation", "phase": 4, "status": "planned",
      "behavior": "Preserve the archived Battle Frontier roster/rule tuning.",
      "dependencies": ["current Battle Frontier engine"],
      "validation": ["representative facility streak", "targeted Frontier tests", "supported build"],
      "evidence": ["git show --stat f5e81e85df"]
    },
    {
      "id": "upstream-gameplay-and-battle",
      "legacy_paths": [{"category": "gameplay-and-battle", "prefixes": [""], "exclude_prefixes": ["src/data/battle_frontier/battle_frontier_mons.h", "src/battle_tower.c", "include/constants/battle_frontier.h"]}],
      "target_paths": ["include/config/**", "src/battle_*.c", "test/battle/**", "current battle scripts/macros"],
      "decision": "Use upstream equivalent", "phase": 4, "status": "planned",
      "behavior": "Keep the current battle engine and configure only missing archived EXP All or mint behavior.",
      "dependencies": ["current battle engine", "current test suite"],
      "validation": ["targeted battle tests", "EXP All manual check", "mint manual check"],
      "evidence": ["git show --stat 476030333c", "git show --stat 624403ccab"]
    },
    {
      "id": "historical-tooling-and-generated-material",
      "legacy_paths": [{"category": "tooling-and-generated-output", "prefixes": [""]}],
      "target_paths": ["Makefile", "tools/**", "docs/**", "current generators"],
      "decision": "Use upstream equivalent", "phase": 5, "status": "planned",
      "behavior": "Keep maintained 1.16.3 tooling and generated outputs.",
      "dependencies": ["current build and generator toolchain"],
      "validation": ["supported build", "regenerate applicable outputs"],
      "evidence": ["inventory tooling-and-generated-output paths"]
    }
  ]
}
-->

## Coverage check

Run from the repository root. This reads the manifest from its explicit comment markers (not a newline-sensitive regular expression), checks each inventory path against every selector, validates the allowed decision vocabulary and all required feature fields, and prints the feature allocation.

```powershell
@'
import json
from collections import Counter

inventory = json.load(open('docs/superpowers/inventories/2026-08-09-legacy-feature-inventory.json', encoding='utf-8'))
review = open('docs/superpowers/inventories/2026-08-09-legacy-feature-review.md', encoding='utf-8').read()
marker = '<!-- feature-manifest\n'
payload = review.split(marker, 1)[1].split('\n-->', 1)[0]
manifest = json.loads(payload)
features = manifest['features']
allowed = {'Direct transfer', 'Use upstream equivalent', 'Modern adaptation', 'Custom replacement'}
required = {'id', 'legacy_paths', 'target_paths', 'decision', 'phase', 'status', 'behavior', 'dependencies', 'validation', 'evidence'}
assert all(required <= feature.keys() and feature['decision'] in allowed for feature in features)
assert len({feature['id'] for feature in features}) == len(features)

def matches(change, selector):
    path = change['path']
    return (change['category'] == selector['category']
            and any(path.startswith(prefix) for prefix in selector['prefixes'])
            and not any(path.startswith(prefix) for prefix in selector.get('exclude_prefixes', [])))

allocations = []
for change in inventory['changes']:
    matched = [feature['id'] for feature in features
               if any(matches(change, selector) for selector in feature['legacy_paths'])]
    assert len(matched) == 1, (change['path'], matched)
    allocations.append(matched[0])
assert len(allocations) == len(inventory['changes']) == 2124
print('coverage:', len(allocations), 'paths; feature counts:', dict(sorted(Counter(allocations).items())))
'@ | python -
```

Regenerate the path inventory and repeat this check whenever either compared ref changes. A selector overlap or an unassigned path is a review failure, not a request to copy legacy code.
