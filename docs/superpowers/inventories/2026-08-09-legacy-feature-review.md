# Legacy Feature Review

This is the exhaustive feature disposition for [the generated path inventory](2026-08-09-legacy-feature-inventory.json), comparing `master` (Expansion 1.16.3, `c828d12721`) with `archive/master-pre-1.16.3` (`f5e81e85df`). The checked-in feature manifest below maps every generated destination path to exactly one feature entry. It is deliberately selector-based: the inventory remains the canonical 2,124-path listing, while the manifest makes the review readable and mechanically auditable.

“Upstream equivalent” means retain the 1.16.3 implementation and, where needed, configure it; it never means copy the archived implementation. “Planned” is an inventory status, not a claim that ROM behavior has already been ported.

| Feature | Legacy paths | 1.16.3 equivalent or target paths | Decision | Phase | Acceptance evidence |
| --- | --- | --- | --- | --- | --- |
| Upstream map and event source conversion | [`upstream-map-event-source`](#feature-manifest) — all `maps-and-events` paths except the explicit custom map features below | Current `data/maps/**`, `data/layouts/**`, JSON/Poryscript generation | Use upstream equivalent | 2 | The paths include generated `.inc` files and broad map-source format drift. Keep current source formats; regenerate derived scripts, build, and smoke-test affected vanilla maps. |
| Littleroot and Verdanturf extensions | [`custom-map-extensions`](#feature-manifest) — all ten `data/{maps,layouts}/{Littleroot,Verdanturf}_Extension/**` paths | Current layout JSON, map headers, events, and warps | Modern adaptation | 2 | The inventory adds five source/layout paths for each extension. Recreate geometry, connections, events, and warps in current formats; enter and leave both maps from a clean save. |
| Petalburg Woodgrove early-game and rebattle map edits | [`petalburg-woodgrove-map-edits`](#feature-manifest) — four `data/{maps,layouts}/PetalburgWoodgrove/**` paths | Current Petalburg Woodgrove JSON/layout/event sources | Modern adaptation | 2 | `0080ad90f7` adds the map/layout/scripts as part of map reworks and mandatory trainers; `43acf35679` changes its tiles; `8ae5c75c40` updates a gym-rebattle placement. Recreate those authored map/event deltas and verify the early-game route plus the rebattle trigger. |
| Gym rebattle map integration | [`gym-rebattle-map-integration`](#feature-manifest) — Route 117/118/120 layouts and Route 120 event placement | Current Route 117/118/120 layout and map-event sources | Modern adaptation | 2 | `8ae5c75c40` places stronger gym-rebattle content in the overworld. Preserve those map/event placements while `custom-trainer-content` owns the teams; verify each placement and rebattle trigger. |
| V2.5.1 debug-map cleanup | [`v2-5-1-debug-map-cleanup`](#feature-manifest) — Littleroot Town and Mauville House 1 map JSON | Current map JSON sources | Use upstream equivalent | 2 | `1d21bfc560` removes the Littleroot Dusclops test object and normalizes empty Mauville map fields. Keep the current maps without the debug object; verify no debug NPC is present and Mauville House 1 remains traversable. |
| Dialogue corrections | [`dialogue-corrections`](#feature-manifest) — Fortree Gym, Route 120/122 Poryscript, and `data/text/trainers.inc` | Current map script sources and `data/text/trainers.inc` | Modern adaptation | 2 | `19b9449e16` makes the Fortree Gym Guide warn that Winona uses Double Battles and corrects the Route 120 gate condition to require beating Winona. Retain the Mom and Route 122 paragraph breaks, Leaf’s Red-focused post-battle text, and Mom’s Pokémon Breeder F portrait through their established feature owners. Verify each dialogue and portrait in-game. |
| Ever Grande NPC interactions | [`ever-grande-old-lady-interaction`](#feature-manifest) — Ever Grande and Route 111 Old Lady Rest Stop map JSON | Current map JSON/event sources | Modern adaptation | 2 | `1bcac4480d` assigns the Route 111 Old Lady interaction to an Ever Grande NPC; `1c782a38a9` places a visible League nurse (`OBJ_EVENT_GFX_NURSE`, `script: NULL`). Retain the Old Lady dialogue and nurse placement without inventing a nurse interaction; keep current empty-event JSON formatting for the Rest Stop. Verify each placement and Rest Stop traversal. |
| V2.5.5 new-game berry distribution | [`v2-5-5-new-game-berries`](#feature-manifest) — `data/scripts/new_game.inc` | Current new-game berry initialization | Modern adaptation | 2 | `1c782a38a9` changes named Route 115/116/110/121/123 berry trees to Cherri, Oran, Persim, and Sitrus varieties. Port those authored initial-tree values and verify a fresh save. |
| V2.5.5 terrain whitespace cleanup | [`v2-5-5-terrain-cleanup`](#feature-manifest) — `src/battle_util.c` | Current terrain resolution | Use upstream equivalent | 4 | The only diff is whitespace in the permanent Misty Terrain assignment; retain current code and verify fog terrain behavior through existing battle coverage. |
| Petalburg Woodgrove connection event | [`petalburg-woodgrove-connection`](#feature-manifest) — Petalburg Woods map and global event-script paths | Current Petalburg Woods JSON/Poryscript and event source | Modern adaptation | 2 | `0080ad90f7` adds the Woodgrove map and its connection. Preserve the connecting warp/event and verify travel in both directions. |
| V2.2.2 map reworks, Red encounter, and Game Corner shop | [`v2-2-2-map-events`](#feature-manifest) — the Route 123/124, Game Corner, Glass Workshop, route/gauntlet, and event paths changed by `0080ad90f7` | Current map JSON/Poryscript, layout, event, mart, item-ball, and player-house sources | Modern adaptation | 2 | `0080ad90f7` documents Route 123 Red, Game Corner Mega Stones, map gauntlets, item placements, Glass Workshop prices, and Mom’s Mega Stones; `19b9449e16` adds Route 122 shop-dialogue paragraph breaks. Port those authored values/events to current formats; verify each map/event/shop path in-game. |
| V2.2.2 progression rewards and affection setting | [`v2-2-2-progression-and-affection`](#feature-manifest) — Player’s House, item-ball, and battle-affection configuration | Current player-house/item-ball scripts and `include/config/battle.h` | Modern adaptation | 2 | `0080ad90f7` explicitly documents Mom’s post-Norman starter Mega Stones, named Mega Stone pickups, and removal of affection mechanics. Port rewards/pickups through current scripts and set the current affection configuration to false; verify badge-gated rewards, pickup flags, and friendship/affection behavior. |
| Full-screen start menu | [`fullscreen-start-menu`](#feature-manifest) — full-screen graphics, implementation, dedicated headers, and Pokédex return flow | Current start-menu/fullscreen APIs, `src/pokedex_plus_hgss.c`, and UI assets | Modern adaptation | 3 | `1b4f48d986` adds the fullscreen menu; `6351f90370` makes Pokédex close return to it and enables the flag-selected alternate clock tilemap. Verify every visible action, gender/clock variants, and Pokédex open/close return flow. |
| Better Bag and remaining QoL UI | [`better-bag-and-qol-ui`](#feature-manifest) — remaining UI-category paths | Current `src/item_menu.c`, `src/option_menu.c`, item configuration and UI assets | Modern adaptation | 3 | BetterBag history (`3480da2c61`, `f5f24a808a`, `ef69dde01e`) identifies pocket and interface behavior. Verify all pockets, item selection/use, and options; retain current menu internals. |
| Current-only content additions | [`current-only-content-additions`](#feature-manifest) — 66 `game-content` deletion records (present in 1.16.3, absent from legacy) | Same current `src/data/**`, `graphics/**`, and `.wav` cry sources | Use upstream equivalent | 2 | Inventory status `D` proves the legacy ref lacks these current paths, including newer items/species assets and source tables. Retain the 1.16.3 assets/tables; verify the supported build and representative asset linkage. |
| Content source-format renames | [`content-source-format-renames`](#feature-manifest) — 10 renamed learnset/species-info records | Current `level_up_learnsets/**`, `species_info/*_families.h`, and generated data inputs | Use upstream equivalent | 2 | The inventory’s `R*` records prove these are source-format moves, not legacy-only assets. Keep the current split family-table representation and validate the relevant data generators. |
| Pokémon graphics and cry-pipeline updates | [`upstream-pokemon-assets-and-cries`](#feature-manifest) — 34 modified Pokémon graphic/palette and cry-table records | Current PNG/palette asset pipeline and current cry tables/data | Use upstream equivalent | 2 | Direct diffs show the eight Pokémon asset quartets are presentation-format changes and the two cry files are current table/data-pipeline changes; retain current output/assets rather than copying legacy binaries. |
| Custom item and Pokémon-data tuning | [`custom-item-and-pokemon-data`](#feature-manifest) — eight modified item/experience/form/effect/dex/learnset tables | Current `src/data/items.h` and Pokémon data generators/tables | Modern adaptation | 2 | Direct table diffs show archived item prices/content, experience/form/effect, dex, species, and teachable-learnset deltas. Preserve those intended values through current source tables/generators, without restoring obsolete table layouts. |
| Battle Frontier roster tuning | [`frontier-roster-tuning`](#feature-manifest) — the archived Frontier roster table and its direct constants/engine callers | Current `src/data/battle_frontier/**`, current Frontier configuration | Modern adaptation | 4 | `git show --stat f5e81e85df` changes `battle_frontier_mons.h`, `battle_tower.c`, and the Frontier constant. Re-express only its roster/rule deltas against 1.16.3 and verify a representative facility streak. |
| Fallarbor Battle Tent Wailmer moveset | [`fallarbor-tent-wailmer`](#feature-manifest) — `src/data/battle_frontier/battle_tent.h` | Current `gFallarborBattleTentMons` `TrainerMon` table | Modern adaptation | 4 | `0c42c0d20d` replaces Splash with Ice Beam on Fallarbor Tent Wailmer. Adapt the legacy FacilityMon value to the current TrainerMon table; encounter/select Wailmer and verify Ice Beam. |
| Custom trainer content | [`custom-trainer-content`](#feature-manifest) — `src/data/trainer_parties.h` and `src/data/trainers.h` | Current trainer party/trainer source tables | Modern adaptation | 2 | Preserve the Mom challenge team (`c73e48076b`), V2.2.2 mandatory trainers (`0080ad90f7`), stronger gym rebattle teams (`c73e48076b`), and Mom’s Pokémon Breeder F portrait (`19b9449e16`). Verify each battle family and Mom’s battle portrait against the current tables. |
| Mom Mega-Stone challenge and reward | [`mom-mega-stone-challenge`](#feature-manifest) — Littleroot house scripts, Mom flags/opponent, and Mom trainer tables | Current Poryscript, player-house scripts, flags, opponent IDs, and trainer tables | Modern adaptation | 2 | `c73e48076b` adds an optional Mom battle after the Amulet Coin and rewards Sceptilite, Blazikenite, and Swampertite; `19b9449e16` corrects its surprise-gift paragraph break. Port the dialogue, accept/decline/repeat flags, trainer, and reward sequence; verify all branches and bag-full handling. |
| Current move animations, Torque updates, and Psychic Noise effect | [`c73e-move-animations`](#feature-manifest) — legacy battle animation scripts, move data, and descriptions | Current 1.16.3 battle-animation and `src/data/moves_info.h` | Use upstream equivalent | 4 | Use 1.16.3's animations for Lumina Crash, Population Bomb, Ruination, Collision Course, Electro Drift, Pounce, Rage Fist, Aqua Step, Shed Tail, Tidy Up, Trailblaze, Chilling Water, and Blazing/Wicked/Noxious/Combat/Magical Torque. Per user policy, retain the current Torque `---` descriptions and Psychic Noise healing-prevention behavior. |
| Burning Bulwark V2 behavior | [`burning-bulwark-v2`](#feature-manifest) — `data/battle_scripts_1.s` | Current `src/battle_move_resolution.c` and `BattleScript_BanefulBunkerEffect` | Use upstream equivalent | 4 | `4f838e8e13` removes `HITMARKER_STATUS_ABILITY_EFFECT`. Current resolution routes the protection effect through Baneful Bunker handling; verify protection, burn on contact, and no unintended ability-status effect. |
| Protected-state macro repair | [`protected-state-macro-repair`](#feature-manifest) — `include/battle.h` | Current protection-state interfaces | Modern adaptation | 4 | `30e31f607d` restores the macro continuation so Burning Bulwark, Obstruct, and Silk Trap are protected states. The current tree no longer exposes that macro, so preserve the observable protection behavior through its current resolution interfaces; verify all three block hits. |
| Release debug-menu configuration | [`release-debug-configuration`](#feature-manifest) — `include/config/debug.h` | Current release debug configuration | Use upstream equivalent | 5 | `0d237e61e6` disables overworld, battle, and Pokémon debug menus. Current 1.16.3 uses `DISABLED_ON_RELEASE` for these interfaces; verify release configuration cannot open any debug menu. |
| Toxic Boost speed tuning | [`toxic-boost-speed-tuning`](#feature-manifest) — `src/battle_main.c` | Current battle speed-stat calculation | Modern adaptation | 4 | `0080ad90f7` documents poisoned Toxic Boost at 1.3× Speed. Re-express the multiplier on current battle APIs and cover poisoned/non-poisoned cases. |
| V2.2.2 wild encounter tuning | [`v2-2-2-wild-encounters`](#feature-manifest) — `src/data/wild_encounters.json` | Current wild encounter JSON/data generator | Modern adaptation | 2 | `0080ad90f7` changes authored encounter species/levels. Port its values to current encounter JSON and verify representative encounter tables in-game. |
| Higher berry yields | [`higher-berry-yields`](#feature-manifest) — `src/berry.c` | Current berry growth/yield logic | Modern adaptation | 2 | `0080ad90f7` documents higher berry yield. Port the intended yield values to the current berry API and verify harvested output. |
| Level-cap XP reduction and post-Lilycove cap | [`level-cap-progression`](#feature-manifest) — battle script commands and event data | Current level-cap configuration, battle script commands, and progression flags | Modern adaptation | 4 | `0080ad90f7` documents reduced XP before severe cap enforcement and a post-Lilycove cap. Port the thresholds/flag progression and test XP on both sides of each cap. |
| Legacy battle engine, config, and tests | [`upstream-gameplay-and-battle`](#feature-manifest) — all remaining `gameplay-and-battle` paths | Current battle engine, config headers, scripts, macros, and `test/battle/**` | Use upstream equivalent | 4 | `476030333c` documents EXP All and `624403ccab` documents mint behavior; 1.16.3 supplies both systems. Configure current behavior if the archived setting differs; run targeted battle tests and EXP/mint manual checks without restoring obsolete engine code. |
| Historical tooling and generated material | [`historical-tooling-and-generated-material`](#feature-manifest) — every `tooling-and-generated-output` path | Current `Makefile`, tools, docs, generators, CI, and generated outputs | Use upstream equivalent | 5 | These paths are outside all feature-source classifiers and include old build/docs/generated artifacts. Build with the supported current command and regenerate outputs; do not import archived infrastructure. |

## Feature manifest

The machine-readable manifest supplies the behavior, dependencies, validation, status, evidence, target paths, permitted decision, and path selector for every table entry. A selector matches a record only when its `category` is equal and its path has a listed prefix; `exclude_prefixes` then removes a match. Paths are evaluated against all entries, so a gap or overlap fails validation.

<!-- feature-manifest
{
  "features": [
    {
      "id": "upstream-map-event-source",
      "legacy_paths": [{"category": "maps-and-events", "prefixes": ["data/maps/", "data/layouts/"], "exclude_prefixes": ["data/layouts/Littleroot_Extension/", "data/maps/Littleroot_Extension/", "data/layouts/Verdanturf_Extension/", "data/maps/Verdanturf_Extension/", "data/layouts/PetalburgWoodgrove/", "data/maps/PetalburgWoodgrove/", "data/maps/Route123/", "data/maps/Route124/", "data/maps/MauvilleCity_GameCorner/", "data/maps/Route113_GlassWorkshop/", "data/maps/Route122/", "data/maps/Route125/", "data/maps/Route126/", "data/maps/Route127/", "data/maps/Route128/", "data/maps/Route129/", "data/maps/Route130/", "data/maps/Route131/", "data/maps/VictoryRoad_", "data/maps/AquaHideout_", "data/maps/MossdeepCity_Gym/", "data/maps/MossdeepCity_SpaceCenter_1F/", "data/maps/EverGrandeCity_", "data/maps/EverGrandeCity/map.json", "data/maps/Route111_OldLadysRestStop/map.json", "data/maps/MagmaHideout_", "data/maps/MeteorFalls_", "data/maps/MtPyre_", "data/maps/PetalburgWoods/", "data/maps/SootopolisCity_Gym_1F/", "data/maps/VerdanturfTown_", "data/maps/LittlerootTown/map.json", "data/maps/MauvilleCity_House1/map.json", "data/maps/LittlerootTown_BrendansHouse_1F/scripts.inc", "data/maps/LittlerootTown_BrendansHouse_1F/scripts.pory", "data/maps/FortreeCity_Gym/scripts.pory", "data/maps/Route120/scripts.pory", "data/maps/Route120/map.json", "data/layouts/Route117/map.bin", "data/layouts/Route118/map.bin", "data/layouts/Route120/map.bin", "data/layouts/Route123/", "data/layouts/Route124/", "data/layouts/Route125/", "data/layouts/Route126/", "data/layouts/Route127/", "data/layouts/Route128/", "data/layouts/Route130/", "data/layouts/Route131/", "data/layouts/VictoryRoad_", "data/layouts/AquaHideout_B1F/", "data/layouts/EverGrandeCity/", "data/layouts/MossdeepCity_Gym/", "data/layouts/MtPyre_2F/"]}],
      "target_paths": ["data/maps/**", "data/layouts/**", "tools/poryscript/**"],
      "decision": "Use upstream equivalent", "phase": 2, "status": "planned",
      "behavior": "Keep the current map source pipeline and vanilla map behavior.",
      "dependencies": ["current JSON/Poryscript generators"],
      "validation": ["regenerate map scripts", "supported build", "affected-map smoke test"],
      "evidence": ["git diff --name-status master...archive/master-pre-1.16.3"]
    },
    {
      "id": "custom-map-extensions",
      "legacy_paths": [{"category": "maps-and-events", "prefixes": ["data/layouts/Littleroot_Extension/", "data/maps/Littleroot_Extension/", "data/layouts/Verdanturf_Extension/", "data/maps/Verdanturf_Extension/"]}],
      "target_paths": ["data/layouts/Littleroot_Extension/**", "data/maps/Littleroot_Extension/**", "data/layouts/Verdanturf_Extension/**", "data/maps/Verdanturf_Extension/**"],
      "decision": "Modern adaptation", "phase": 2, "status": "planned",
      "behavior": "Preserve the two named custom extension maps, their connections, and their events.",
      "dependencies": ["upstream map source pipeline"],
      "validation": ["clean-save entry and exit", "warp/event checks", "supported build"],
      "evidence": ["inventory adds five Littleroot_Extension paths", "inventory adds five Verdanturf_Extension paths"]
    },
    {
      "id": "petalburg-woodgrove-map-edits",
      "legacy_paths": [{"category": "maps-and-events", "prefixes": ["data/layouts/PetalburgWoodgrove/", "data/maps/PetalburgWoodgrove/"]}],
      "target_paths": ["data/layouts/PetalburgWoodgrove/**", "data/maps/PetalburgWoodgrove/**"],
      "decision": "Modern adaptation", "phase": 2, "status": "planned",
      "behavior": "Preserve the authored Woodgrove tile, early-game trainer, and gym-rebattle placement changes.",
      "dependencies": ["upstream map source pipeline", "trainer-rebattle data"],
      "validation": ["early-game traversal", "mandatory-trainer checks", "gym-rebattle trigger", "supported build"],
      "evidence": ["git show --stat 0080ad90f7", "git show --stat 43acf35679", "git show --stat 8ae5c75c40"]
    },
    {"id":"petalburg-woodgrove-connection","legacy_paths":[{"category":"maps-and-events","prefixes":["data/maps/PetalburgWoods/map.json"]},{"category":"tooling-and-generated-output","prefixes":["data/event_scripts.s"]}],"target_paths":["data/maps/PetalburgWoods/**","current event scripts"],"decision":"Modern adaptation","phase":2,"status":"planned","behavior":"Preserve the Woodgrove connecting warp/event.","dependencies":["current map/event pipeline"],"validation":["bidirectional Woodgrove warp check"],"evidence":["git show --name-status 0080ad90f7 -- data/maps/PetalburgWoods/map.json data/event_scripts.s"]},
    {
      "id": "v2-2-2-map-events",
      "legacy_paths": [{"category": "maps-and-events", "prefixes": ["data/maps/Route123/", "data/maps/Route124/", "data/maps/MauvilleCity_GameCorner/", "data/maps/Route113_GlassWorkshop/", "data/maps/Route122/", "data/maps/Route125/", "data/maps/Route126/", "data/maps/Route127/", "data/maps/Route128/", "data/maps/Route129/", "data/maps/Route130/", "data/maps/Route131/", "data/maps/VictoryRoad_", "data/maps/AquaHideout_", "data/maps/MossdeepCity_Gym/", "data/maps/MossdeepCity_SpaceCenter_1F/", "data/maps/EverGrandeCity_", "data/maps/MagmaHideout_", "data/maps/MeteorFalls_", "data/maps/MtPyre_", "data/maps/PetalburgWoods/", "data/maps/SootopolisCity_Gym_1F/", "data/maps/VerdanturfTown_", "data/layouts/Route123/", "data/layouts/Route124/", "data/layouts/Route125/", "data/layouts/Route126/", "data/layouts/Route127/", "data/layouts/Route128/", "data/layouts/Route130/", "data/layouts/Route131/", "data/layouts/VictoryRoad_", "data/layouts/AquaHideout_B1F/", "data/layouts/EverGrandeCity/", "data/layouts/MossdeepCity_Gym/", "data/layouts/MtPyre_2F/"], "exclude_prefixes": ["data/maps/PetalburgWoods/map.json", "data/maps/Route122/scripts.pory"]}],
      "target_paths": ["data/maps/Route123/**", "data/maps/Route124/**", "data/maps/MauvilleCity_GameCorner/**", "data/maps/Route113_GlassWorkshop/**", "current map/event/mart sources"],
      "decision": "Modern adaptation", "phase": 2, "status": "planned",
      "behavior": "Preserve V2.2.2 authored map gauntlets, the Route 123 Red event, Game Corner Mega Stone shop, item placements, and related progression events; Route 122 shop dialogue paragraph breaks are owned by dialogue-corrections.",
      "dependencies": ["current map JSON/Poryscript pipeline", "item and trainer data"],
      "validation": ["Route 123 Red event", "Route 124 traversal", "Game Corner inventory", "Glass Workshop prices", "Victory Road and route event checks"],
      "evidence": ["git show --name-status 0080ad90f7", "commit message documents Route 123, Game Corner, map reworks, prices, and Mega Stone events"]
    },
    {
      "id": "v2-2-2-progression-and-affection",
      "legacy_paths": [{"category": "tooling-and-generated-output", "prefixes": ["data/scripts/item_ball_scripts.inc"]}, {"category": "gameplay-and-battle", "prefixes": ["include/config/battle.h"]}],
      "target_paths": ["data/scripts/players_house.inc", "data/scripts/item_ball_scripts.inc", "include/config/battle.h"],
      "decision": "Modern adaptation", "phase": 2, "status": "planned",
      "behavior": "Give all three starter Mega Stones after Norman, retain named Mega Stone pickups, and disable affection mechanics.",
      "dependencies": ["badge/progression flags", "current item-ball and player-house script APIs", "current battle configuration"],
      "validation": ["post-Norman Mom reward", "every named Mega Stone pickup and flag", "B_AFFECTION_MECHANICS equals FALSE", "supported build"],
      "evidence": ["git show --name-status 0080ad90f7 -- data/scripts/players_house.inc data/scripts/item_ball_scripts.inc include/config/battle.h", "0080ad90f7 commit message"]
    },
    {
      "id": "fullscreen-start-menu",
      "legacy_paths": [{"category": "ui-and-quality-of-life", "prefixes": ["graphics/ui_startmenu_full/", "src/start_menu.c"]}, {"category": "gameplay-and-battle", "prefixes": ["src/ui_startmenu_full.c", "src/pokedex_plus_hgss.c", "include/start_menu.h", "include/ui_startmenu_full.h"]}],
      "target_paths": ["src/start_menu.c", "src/ui_startmenu_full.c", "src/pokedex_plus_hgss.c", "graphics/ui_startmenu_full/**", "include/start_menu.h", "include/ui_startmenu_full.h"],
      "decision": "Modern adaptation", "phase": 3, "status": "planned",
      "behavior": "Preserve the archived full-screen menu presentation and its gender/clock variants.",
      "dependencies": ["current start-menu and option-menu APIs"],
      "validation": ["all start-menu actions", "gender/clock variants", "Pokédex open/close returns to fullscreen menu", "supported build"],
      "evidence": ["git show --stat 1b4f48d986", "git show 6351f90370 -- src/ui_startmenu_full.c src/pokedex_plus_hgss.c"]
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
      "id": "current-only-content-additions",
      "legacy_paths": [{"category": "game-content", "prefixes": [""], "statuses": ["D"]}],
      "target_paths": ["src/data/**", "graphics/**", "sound/direct_sound_samples/cries/*.wav"],
      "decision": "Use upstream equivalent", "phase": 2, "status": "planned",
      "behavior": "Retain content added by current 1.16.3 that the archived ref does not contain.",
      "dependencies": ["current species/item/move/trainer/encounter data generators"],
      "validation": ["supported build", "asset linkage", "representative item/species/cry lookup"],
      "evidence": ["inventory game-content status D count: 66", "master contains the listed current paths"]
    },
    {
      "id": "content-source-format-renames",
      "legacy_paths": [{"category": "game-content", "prefixes": [""], "statuses": ["R050", "R052", "R053", "R054", "R056", "R057", "R058", "R089"]}],
      "target_paths": ["src/data/pokemon/level_up_learnsets/**", "src/data/pokemon/species_info/*_families.h"],
      "decision": "Use upstream equivalent", "phase": 2, "status": "planned",
      "behavior": "Use current split learnset and species-family source formats.",
      "dependencies": ["current Pokémon data generators"],
      "validation": ["regenerate Pokémon data", "supported build"],
      "evidence": ["inventory game-content rename records: 10", "master src/data/pokemon/species_info/*_families.h"]
    },
    {
      "id": "upstream-pokemon-assets-and-cries",
      "legacy_paths": [{"category": "game-content", "prefixes": ["graphics/pokemon/", "sound/cry_tables.inc", "sound/direct_sound_data.inc"], "statuses": ["M"]}],
      "target_paths": ["graphics/pokemon/**", "sound/cry_tables.inc", "sound/direct_sound_data.inc"],
      "decision": "Use upstream equivalent", "phase": 2, "status": "planned",
      "behavior": "Keep current Pokémon presentation and cry-pipeline output.",
      "dependencies": ["current graphics converter", "current cry build pipeline"],
      "validation": ["asset linkage", "cry playback", "supported build"],
      "evidence": ["git diff --stat master archive/master-pre-1.16.3 -- graphics/pokemon/{brute_bonnet,chi_yu,flutter_mane,iron_bundle,sandy_shocks,scream_tail,skeledirge,slither_wing}", "git diff --numstat master archive/master-pre-1.16.3 -- sound/cry_tables.inc sound/direct_sound_data.inc"],
      "semantic_comparison": {"graphics/pokemon/{brute_bonnet,chi_yu,flutter_mane,iron_bundle,sandy_shocks,scream_tail,skeledirge,slither_wing}/{back.png,front.png,normal.pal,shiny.pal}": "current asset-pipeline presentation supersedes legacy PNG/palette output", "sound/cry_tables.inc": "current cry table supersedes legacy table", "sound/direct_sound_data.inc": "current cry data pipeline supersedes legacy data"}
    },
    {
      "id": "custom-item-and-pokemon-data",
      "legacy_paths": [{"category": "game-content", "prefixes": ["src/data/items.h", "src/data/pokemon/experience_tables.h", "src/data/pokemon/form_change_tables.h", "src/data/pokemon/form_species_tables.h", "src/data/pokemon/item_effects.h", "src/data/pokemon/pokedex_orders.h", "src/data/pokemon/species_info.h", "src/data/pokemon/teachable_learnsets.h"], "statuses": ["M"]}],
      "target_paths": ["src/data/items.h", "src/data/pokemon/experience_tables.h", "src/data/pokemon/form_change_table_pointers.h", "src/data/pokemon/form_species_tables.h", "src/data/pokemon/item_effects.h", "src/data/pokemon/pokedex_orders.h", "src/data/pokemon/species_info.h", "src/data/pokemon/all_learnables.json"],
      "decision": "Modern adaptation", "phase": 2, "status": "planned",
      "behavior": "Preserve the archived item economy/content and Pokémon data tuning through current source formats.",
      "dependencies": ["current item and Pokémon data generators"],
      "validation": ["table-level legacy-to-current value comparison", "item/mint use", "experience/form/learnset checks", "supported build"],
      "evidence": ["git diff --numstat master archive/master-pre-1.16.3 -- src/data/items.h src/data/pokemon/experience_tables.h src/data/pokemon/form_change_tables.h src/data/pokemon/form_species_tables.h src/data/pokemon/item_effects.h src/data/pokemon/pokedex_orders.h src/data/pokemon/species_info.h src/data/pokemon/teachable_learnsets.h"],
      "semantic_comparison": {"src/data/items.h": "legacy item prices, descriptions, pockets, and item definitions require value-level port", "src/data/pokemon/experience_tables.h": "legacy experience progression tuning requires value-level port", "src/data/pokemon/form_change_tables.h": "legacy form-change data requires current-format port", "src/data/pokemon/form_species_tables.h": "legacy form-species data requires current-format port", "src/data/pokemon/item_effects.h": "legacy item-effect data requires current-format port", "src/data/pokemon/pokedex_orders.h": "legacy dex ordering requires current-format port", "src/data/pokemon/species_info.h": "legacy species data requires current-format port", "src/data/pokemon/teachable_learnsets.h": "legacy teachable learnsets require conversion to current all_learnables input"}
    },
    {
      "id": "frontier-roster-tuning",
      "legacy_paths": [{"category": "gameplay-and-battle", "prefixes": ["src/data/battle_frontier/battle_frontier_mons.h", "src/data/battle_frontier/battle_frontier_trainer_mons.h", "src/battle_tower.c", "include/constants/battle_frontier.h"]}],
      "target_paths": ["src/data/battle_frontier/battle_frontier_mons.h", "src/data/battle_frontier/battle_frontier_trainer_mons.h", "src/battle_tower.c", "include/constants/battle_frontier.h"],
      "decision": "Modern adaptation", "phase": 4, "status": "planned",
      "behavior": "Preserve the archived Battle Frontier roster/rule tuning.",
      "dependencies": ["current Battle Frontier engine"],
      "validation": ["representative facility streak", "targeted Frontier tests", "supported build"],
      "evidence": ["git show --stat f5e81e85df", "git show --name-status 0080ad90f7 -- src/data/battle_frontier/battle_frontier_trainer_mons.h"]
    },
    {
      "id": "custom-trainer-content",
      "legacy_paths": [{"category": "gameplay-and-battle", "prefixes": ["src/data/trainer_parties.h", "src/data/trainers.h"]}],
      "target_paths": ["src/data/trainer_parties.h", "src/data/trainers.h"],
      "decision": "Modern adaptation", "phase": 2, "status": "planned",
      "behavior": "Preserve Mom challenge, V2.2.2 mandatory-trainer, and stronger gym-rebattle teams, plus Mom's Pokémon Breeder F battle portrait.",
      "dependencies": ["current trainer source tables", "map/event progression"],
      "validation": ["Mom challenge team and Pokémon Breeder F portrait", "mandatory trainer encounters", "stronger gym rebattle teams", "supported build"],
      "evidence": ["git show c73e48076b -- src/data/trainer_parties.h src/data/trainers.h", "git show 0080ad90f7 -- src/data/trainer_parties.h src/data/trainers.h", "git show 19b9449e16 -- src/data/trainers.h changes MOM to TRAINER_PIC_POKEMON_BREEDER_F"]
    },
    {"id":"mom-mega-stone-challenge","legacy_paths":[{"category":"maps-and-events","prefixes":["data/maps/LittlerootTown_BrendansHouse_1F/scripts.inc","data/maps/LittlerootTown_BrendansHouse_1F/scripts.pory"]},{"category":"tooling-and-generated-output","prefixes":["data/scripts/players_house.inc"]},{"category":"gameplay-and-battle","prefixes":["include/constants/flags.h","include/constants/opponents.h"]}],"target_paths":["data/maps/LittlerootTown_BrendansHouse_1F/**","data/scripts/players_house.inc","current flags/opponents"],"decision":"Modern adaptation","phase":2,"status":"planned","behavior":"Optional Mom battle awards three starter Mega Stones; its surprise-gift sentence begins a new paragraph after 'myself.'","dependencies":["current Poryscript and trainer content","custom-trainer-content"],"validation":["accept/decline/repeat battle", "Mom surprise-gift paragraph break", "three reward items", "bag-full handling"],"evidence":["git show c73e48076b -- data/maps/LittlerootTown_BrendansHouse_1F/scripts.pory data/scripts/players_house.inc include/constants/flags.h include/constants/opponents.h","git show 19b9449e16 -- data/maps/LittlerootTown_BrendansHouse_1F/scripts.pory"]},
    {"id":"dialogue-corrections","legacy_paths":[{"category":"maps-and-events","prefixes":["data/maps/FortreeCity_Gym/scripts.pory","data/maps/Route120/scripts.pory","data/maps/Route122/scripts.pory"]},{"category":"tooling-and-generated-output","prefixes":["data/text/trainers.inc"]}],"target_paths":["data/maps/FortreeCity_Gym/scripts.inc","data/maps/Route120/scripts.inc","data/maps/Route122/scripts.inc","data/text/trainers.inc","src/data/trainers.h"],"decision":"Modern adaptation","phase":2,"status":"planned","behavior":"Fortree's Gym Guide explicitly warns of Winona's Double Battle. Route 120's gate says passing requires defeating Winona. Route 122's adult-only shop speech gains paragraph breaks. Leaf's New Mauville post-battle text in data/text/trainers.inc asks about Red and the player's strength. Mom uses the Pokémon Breeder F battle portrait.","dependencies":["generated map-script .inc mirrors retained by upstream-map-event-source, mom-mega-stone-challenge, and v2-2-2-map-events","custom-trainer-content owns src/data/trainers.h","c73e-move-animations retains data/battle_anim_scripts.s","gym-rebattle-map-integration retains data/layouts/Route118/map.bin"],"validation":["talk to Fortree Gym Guide before Winona and verify Double Battle warning","meet Route 120 gate requirement and verify Winona condition","talk to Route 122 shop NPC and verify paragraph pagination","defeat Leaf in New Mauville and verify the data/text/trainers.inc Red-focused post-battle text","start Mom challenge and verify Pokémon Breeder F portrait","supported build"],"evidence":["git show 19b9449e16 -- data/maps/FortreeCity_Gym/scripts.pory data/maps/LittlerootTown_BrendansHouse_1F/scripts.pory data/maps/Route120/scripts.pory data/maps/Route122/scripts.pory data/text/trainers.inc src/data/trainers.h","git show master:data/text/trainers.inc confirms current text source; data/maps/NewMauville_Inside/scripts.inc has no Leaf text"]},
    {"id":"c73e-move-animations","legacy_paths":[{"category":"gameplay-and-battle","prefixes":["data/battle_anim_scripts.s","src/data/battle_moves.h","src/data/text/move_descriptions.h"]}],"target_paths":["data/battle_anim_scripts.s","src/data/moves_info.h"],"decision":"Use upstream equivalent","phase":4,"status":"planned","behavior":"Use current 1.16.3 animations for Lumina Crash, Population Bomb, Ruination, Collision Course, Electro Drift, Pounce, Rage Fist, Aqua Step, Shed Tail, Tidy Up, Trailblaze, Chilling Water, and all five Torque moves; deliberately retain current Torque `---` descriptions and Psychic Noise healing prevention.","dependencies":["current battle animation engine","src/data/moves_info.h"],"validation":["confirm each listed move, including all five Torque moves, has a current animation","confirm all five current Torque descriptions are `---`","confirm Psychic Noise healing prevention","supported build"],"evidence":["user decision: retain current 1.16.3 Torque descriptions","git show e6c3bf419f -- data/battle_anim_scripts.s src/data/text/move_descriptions.h","src/data/moves_info.h contains current Torque descriptions"]},
    {"id":"gym-rebattle-map-integration","legacy_paths":[{"category":"maps-and-events","prefixes":["data/layouts/Route117/map.bin","data/layouts/Route118/map.bin","data/layouts/Route120/map.bin","data/maps/Route120/map.json"]}],"target_paths":["data/layouts/Route117/map.bin","data/layouts/Route118/map.bin","data/layouts/Route120/map.bin","data/maps/Route120/map.json"],"decision":"Modern adaptation","phase":2,"status":"planned","behavior":"Preserve Route 117/118/120 gym-rebattle placement and Route 120 event integration.","dependencies":["custom-trainer-content","current map pipeline"],"validation":["visit all three placements","trigger Route 120 rebattle event","supported build"],"evidence":["git show --name-status 8ae5c75c40"]},
    {"id":"protected-state-macro-repair","legacy_paths":[{"category":"gameplay-and-battle","prefixes":["include/battle.h"]}],"target_paths":["src/battle_move_resolution.c","current protection-state interfaces"],"decision":"Modern adaptation","phase":4,"status":"planned","behavior":"Burning Bulwark, Obstruct, and Silk Trap must each be treated as protected states.","dependencies":["current battle move resolution"],"validation":["each move blocks an incoming hit","supported battle tests"],"evidence":["git show 30e31f607d -- include/battle.h","current tree no longer exposes IS_BATTLER_PROTECTED"]},
    {"id":"v2-5-1-debug-map-cleanup","legacy_paths":[{"category":"maps-and-events","prefixes":["data/maps/LittlerootTown/map.json","data/maps/MauvilleCity_House1/map.json"]}],"target_paths":["data/maps/LittlerootTown/map.json","data/maps/MauvilleCity_House1/map.json"],"decision":"Use upstream equivalent","phase":2,"status":"planned","behavior":"Retain maps without the Littleroot Dusclops debug object and with valid empty Mauville event collections.","dependencies":["current map JSON pipeline"],"validation":["no Littleroot debug Dusclops NPC","enter/exit Mauville House 1","supported build"],"evidence":["git show 1d21bfc560 -- data/maps/LittlerootTown/map.json data/maps/MauvilleCity_House1/map.json"]},
    {"id":"release-debug-configuration","legacy_paths":[{"category":"gameplay-and-battle","prefixes":["include/config/debug.h"]}],"target_paths":["include/config/debug.h"],"decision":"Use upstream equivalent","phase":5,"status":"planned","behavior":"Release builds do not expose overworld, battle, or Pokémon debug menus.","dependencies":["DISABLED_ON_RELEASE configuration"],"validation":["R+Start does not open overworld debug","Select does not open battle/Pokémon debug in release configuration"],"evidence":["git show 0d237e61e6 -- include/config/debug.h","current include/config/debug.h uses DISABLED_ON_RELEASE"]},
    {"id":"fallarbor-tent-wailmer","legacy_paths":[{"category":"gameplay-and-battle","prefixes":["src/data/battle_frontier/battle_tent.h"]}],"target_paths":["src/data/battle_frontier/battle_tent.h:gFallarborBattleTentMons"],"decision":"Modern adaptation","phase":4,"status":"planned","behavior":"Fallarbor Battle Tent Wailmer uses Ice Beam instead of Splash.","dependencies":["current TrainerMon table format"],"validation":["encounter/select Fallarbor Tent Wailmer", "verify Ice Beam is usable", "supported build"],"evidence":["git show 0c42c0d20d -- src/data/battle_frontier/battle_tent.h", "current gFallarborBattleTentMons is const struct TrainerMon and lists MOVE_SPLASH"]},
    {"id":"ever-grande-old-lady-interaction","legacy_paths":[{"category":"maps-and-events","prefixes":["data/maps/EverGrandeCity/map.json","data/maps/Route111_OldLadysRestStop/map.json"]}],"target_paths":["data/maps/EverGrandeCity/map.json","data/maps/Route111_OldLadysRestStop/map.json","current Old Lady script source"],"decision":"Modern adaptation","phase":2,"status":"planned","behavior":"Ever Grande retains the scripted Route 111 Old Lady NPC and the V2.5.5 visible League nurse object (OBJ_EVENT_GFX_NURSE at 21,27 with script NULL); the nurse has no invented interaction. The Rest Stop preserves valid empty event collections.","dependencies":["current map JSON object-event schema","current Old Lady script source","current map script pipeline"],"validation":["talk to Ever Grande Old Lady NPC and verify dialogue", "verify visible Ever Grande nurse at 21,27 has no interaction", "enter/exit Route 111 Old Lady Rest Stop", "supported build"],"evidence":["git show 1bcac4480d -- data/maps/EverGrandeCity/map.json data/maps/Route111_OldLadysRestStop/map.json","git show 1c782a38a9 -- data/maps/EverGrandeCity/map.json adds OBJ_EVENT_GFX_NURSE at 21,27 with script NULL"]},
    {"id":"v2-5-5-new-game-berries","legacy_paths":[{"category":"tooling-and-generated-output","prefixes":["data/scripts/new_game.inc"]}],"target_paths":["data/scripts/new_game.inc"],"decision":"Modern adaptation","phase":2,"status":"planned","behavior":"Fresh games use the V2.5.5 Cherri, Oran, Persim, and Sitrus substitutions at named berry trees.","dependencies":["current new-game scripts","berry-tree IDs"],"validation":["fresh-save berry-tree species at Route 115/116/110/121/123"],"evidence":["git show 1c782a38a9 -- data/scripts/new_game.inc"]},
    {"id":"v2-5-5-terrain-cleanup","legacy_paths":[{"category":"gameplay-and-battle","prefixes":["src/battle_util.c"]}],"target_paths":["src/battle_util.c"],"decision":"Use upstream equivalent","phase":4,"status":"planned","behavior":"Keep current permanent Misty Terrain fog handling.","dependencies":["current terrain resolution"],"validation":["fog terrain battle coverage"],"evidence":["git show 1c782a38a9 -- src/battle_util.c shows whitespace-only change"]},
    {"id":"burning-bulwark-v2","legacy_paths":[{"category":"gameplay-and-battle","prefixes":["data/battle_scripts_1.s"]}],"target_paths":["src/battle_move_resolution.c","data/battle_scripts_1.s:BattleScript_BanefulBunkerEffect"],"decision":"Use upstream equivalent","phase":4,"status":"planned","behavior":"Current protection resolution supplies Burning Bulwark protection and burn-on-contact behavior without the legacy ability-status marker.","dependencies":["current battle move resolution","BattleScript_BanefulBunkerEffect"],"validation":["Burning Bulwark protects against contact", "contact attacker is burned", "no unintended ability-status effect"],"evidence":["git show 4f838e8e13 -- data/battle_scripts_1.s", "src/battle_move_resolution.c calls BattleScript_BanefulBunkerEffect for current protection resolution"]},
    {"id":"toxic-boost-speed-tuning","legacy_paths":[{"category":"gameplay-and-battle","prefixes":["src/battle_main.c"]}],"target_paths":["src/battle_main.c"],"decision":"Modern adaptation","phase":4,"status":"planned","behavior":"Use 1.3x Speed for poisoned Toxic Boost.","dependencies":["current battle stat calculation"],"validation":["poisoned and non-poisoned Toxic Boost battle tests"],"evidence":["git show 0080ad90f7 -- src/battle_main.c","0080ad90f7 commit message"]},
    {"id":"v2-2-2-wild-encounters","legacy_paths":[{"category":"gameplay-and-battle","prefixes":["src/data/wild_encounters.json"]}],"target_paths":["src/data/wild_encounters.json"],"decision":"Modern adaptation","phase":2,"status":"planned","behavior":"Preserve authored V2.2.2 wild species and level changes.","dependencies":["current wild encounter generator"],"validation":["representative encounter-table and in-game checks"],"evidence":["git show 0080ad90f7 -- src/data/wild_encounters.json"]},
    {"id":"higher-berry-yields","legacy_paths":[{"category":"gameplay-and-battle","prefixes":["src/berry.c"]}],"target_paths":["src/berry.c"],"decision":"Modern adaptation","phase":2,"status":"planned","behavior":"Preserve higher berry yields.","dependencies":["current berry growth system"],"validation":["plant-to-harvest yield check"],"evidence":["git show 0080ad90f7 -- src/berry.c"]},
    {"id":"level-cap-progression","legacy_paths":[{"category":"gameplay-and-battle","prefixes":["src/battle_script_commands.c","include/event_data.h"]}],"target_paths":["src/battle_script_commands.c","include/event_data.h","include/config/level_caps.h"],"decision":"Modern adaptation","phase":4,"status":"planned","behavior":"Preserve pre-cap XP reduction and post-Lilycove cap progression.","dependencies":["current level-cap configuration and event flags"],"validation":["XP below/at cap", "post-Lilycove cap flag", "supported build"],"evidence":["git show 0080ad90f7 -- src/battle_script_commands.c include/event_data.h","0080ad90f7 commit message"]},
    {
      "id": "upstream-gameplay-and-battle",
      "legacy_paths": [{"category": "gameplay-and-battle", "prefixes": [""], "exclude_prefixes": ["src/data/battle_frontier/battle_frontier_mons.h", "src/data/battle_frontier/battle_frontier_trainer_mons.h", "src/data/battle_frontier/battle_tent.h", "src/battle_tower.c", "include/constants/battle_frontier.h", "src/data/trainer_parties.h", "src/data/trainers.h", "include/config/battle.h", "include/config/debug.h", "include/battle.h", "include/constants/flags.h", "include/constants/opponents.h", "src/battle_main.c", "src/battle_util.c", "src/data/wild_encounters.json", "src/berry.c", "src/battle_script_commands.c", "include/event_data.h", "data/battle_anim_scripts.s", "data/battle_scripts_1.s", "src/data/battle_moves.h", "src/data/text/move_descriptions.h", "src/ui_startmenu_full.c", "src/pokedex_plus_hgss.c", "include/start_menu.h", "include/ui_startmenu_full.h"]}],
      "target_paths": ["include/config/**", "src/battle_*.c", "test/battle/**", "current battle scripts/macros"],
      "decision": "Use upstream equivalent", "phase": 4, "status": "planned",
      "behavior": "Keep the current battle engine and configure only missing archived EXP All or mint behavior.",
      "dependencies": ["current battle engine", "current test suite"],
      "validation": ["targeted battle tests", "EXP All manual check", "mint manual check"],
      "evidence": ["git show --stat 476030333c", "git show --stat 624403ccab"]
    },
    {
      "id": "historical-tooling-and-generated-material",
      "legacy_paths": [{"category": "tooling-and-generated-output", "prefixes": [""], "exclude_prefixes": ["data/scripts/players_house.inc", "data/scripts/item_ball_scripts.inc", "data/event_scripts.s", "data/scripts/new_game.inc", "data/text/trainers.inc"]}],
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
            and (not selector.get('statuses') or change['status'] in selector['statuses'])
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
