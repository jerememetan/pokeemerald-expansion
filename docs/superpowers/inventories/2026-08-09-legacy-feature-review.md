# Legacy Feature Review

This review is a complete, path-level disposition of the generated [legacy path inventory](2026-08-09-legacy-feature-inventory.json). It compares `master` (Expansion 1.16.3, `c828d12721`) with `archive/master-pre-1.16.3` (`f5e81e85df`). A path belongs to exactly one inventory category, and each category appears in exactly one table row; the selector manifest below is deliberately machine-checkable.

The review distinguishes behavior from implementation. Legacy upstream ports, generated assembly, old test suites, and obsolete build tooling remain on the current release. Custom behavior is brought forward only through the current data/configuration interfaces or the smallest dedicated implementation needed after a phase validates it.

| Feature | Legacy paths | 1.16.3 equivalent or target paths | Decision | Phase | Acceptance evidence |
| --- | --- | --- | --- | --- | --- |
| Map and event behavior | [maps-and-events selector](#coverage-manifest) (1,220 paths: `data/maps/**`, `data/layouts/**`) | `data/maps/**`, `data/layouts/**`, current map JSON/Poryscript generators | Modern adaptation | 2 | The inventory includes the custom `Littleroot_Extension` and `Verdanturf_Extension` layouts alongside all map-source conversions. Recreate changed layouts, events, warps, objects, and scripts in current JSON/Poryscript; do not copy generated `.inc` output. Verify new-game, each changed warp/event, and the extension-map entry/exit in-game. |
| Start-menu, bag, and QoL interface | [ui-and-quality-of-life selector](#coverage-manifest) (41 paths: fullscreen menu graphics and `src/start_menu`, `src/option_menu`, `src/item_menu` changes) | `src/start_menu.c`, `src/item_menu.c`, `include/config/item.h`, current UI graphics/build rules | Modern adaptation | 3 | Legacy commits `1b4f48d986` (full-screen start menu) and BetterBag history (`3480da2c61`, `f5f24a808a`, `ef69dde01e`) establish the intended custom UI and pocket behavior. Implement only the preserved screen/pocket behavior on current APIs; exercise every menu action, pocket, and gender/clock variant. |
| Custom content: species, items, moves, trainers, encounters, graphics, and cries | [game-content selector](#coverage-manifest) (118 paths: `data/trainers/**`, `data/wild/**`, `src/data/{pokemon,items,moves}/**`, Pokémon/item graphics, `sound/**`) | Current `src/data/**`, `graphics/**`, `sound/**`, trainer and encounter source formats | Direct transfer | 2 | The legacy history records nature-mint content in `624403ccab` and custom trainer/frontier tuning in `f5e81e85df`. Transfer only deltas that change available content, using current tables/assets and current generated formats; verify item use, learnsets, encounters, trainer parties, and asset linkage. |
| Battle, gameplay, and Battle Frontier tuning | [gameplay-and-battle selector](#coverage-manifest) (593 paths: battle/config/core sources, headers, macros, and battle tests) | `include/config/**`, `src/data/**`, `src/battle_*.c`, `src/data/battle_frontier/**`, current `test/battle/**` | Use upstream equivalent | 4 | Current 1.16.3 already owns the battle engine, scripts, macros, and tests. Legacy commits `476030333c` (EXP All), `624403ccab` (mints), and `f5e81e85df` (Frontier tables) identify behavior to configure or re-express on those interfaces. Add only missing content/configuration; run targeted battle tests plus EXP, mint, and Frontier streak/manual checks. |
| Historical tooling, generated output, and imported upstream material | [tooling-and-generated-output selector](#coverage-manifest) (152 paths: documentation, build/config, generated scripts/text, tools, and non-feature assets) | Current 1.16.3 `Makefile`, `tools/**`, generated source pipeline, docs, and CI configuration | Use upstream equivalent | 5 | These paths fall outside the feature classifiers because they are old build/documentation/generated artifacts. Keep 1.16.3’s maintained tooling, regenerate derived files from current inputs, and confirm the supported build plus relevant generators complete without importing legacy infrastructure. |

## Evidence used

- `git log master..archive/master-pre-1.16.3` identifies the independent legacy feature work rather than treating every version-skew path as custom behavior.
- `git show --stat 1b4f48d986`, `624403ccab`, `476030333c`, and `f5e81e85df` show the fullscreen menu, nature-mint, EXP All, and Battle Frontier work respectively.
- `git diff --name-status -z master...archive/master-pre-1.16.3` is the inventory generator’s input. The generated JSON, rather than this prose, is the authoritative enumeration.

## Coverage manifest

The following selectors intentionally use the inventory’s mutually exclusive `category` field. They are review-row identifiers, not directory globs: a renamed path is accounted for by its generated destination `path`, exactly as it appears in the inventory.

```json
{
  "maps-and-events": "Map and event behavior",
  "ui-and-quality-of-life": "Start-menu, bag, and QoL interface",
  "game-content": "Custom content: species, items, moves, trainers, encounters, graphics, and cries",
  "gameplay-and-battle": "Battle, gameplay, and Battle Frontier tuning",
  "tooling-and-generated-output": "Historical tooling, generated output, and imported upstream material"
}
```

Coverage check (run from the repository root):

```powershell
@'
import json, re
from collections import Counter
inventory = json.load(open('docs/superpowers/inventories/2026-08-09-legacy-feature-inventory.json', encoding='utf-8'))
review = open('docs/superpowers/inventories/2026-08-09-legacy-feature-review.md', encoding='utf-8').read()
manifest = json.loads(re.search(r'```json\\n(.*?)\\n```', review, re.S).group(1))
counts = Counter(change['category'] for change in inventory['changes'])
assert set(manifest) == set(counts), (set(manifest), set(counts))
assert sum(counts.values()) == len(inventory['changes']) == 2124
matches = [sum(change['category'] == selector for selector in manifest) for change in inventory['changes']]
assert Counter(matches) == {1: len(inventory['changes'])}, Counter(matches)
assert dict(sorted(counts.items())) == inventory['summary']
print('coverage:', len(inventory['changes']), 'paths; selectors:', len(manifest), '; category counts:', dict(sorted(counts.items())))
'@ | python -
```

The `Counter` is over every generated record; categories are a single required field in the generator, the manifest has one key for each category, and the set equality plus total makes a missing or duplicate review selector fail. The count assertion pins this review to the 2,124-path inventory produced from the stated refs; regenerate and re-review if the inventory changes.
