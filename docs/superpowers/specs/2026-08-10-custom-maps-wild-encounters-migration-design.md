# Custom Maps and Wild Encounters Migration Design

## Goal

Restore the archived ROM hack's custom map layouts and wild Pokémon encounter tables on the current Expansion 1.16.3 migration branch without replacing newer upstream infrastructure. Preserve the player's reviewed encounter choices, keep every current-only upstream encounter, and leave shared-map scripts and events outside the minimum access changes untouched.

## Baselines and Evidence

- **Target branch:** `codex/rom-hack-1.16.3-migration` at `e74a0e0db9` before this design.
- **Legacy reference:** `archive/master-pre-1.16.3` at `f5e81e85df`.
- **Common ancestor used for three-way classification:** `024848a9e9c0ae30cbb9a269779504561d5443d3`.
- **Parent design:** [Original Hack Migration to Expansion 1.16.3](2026-08-09-original-hack-1.16.3-migration-design.md).
- **Reviewed encounter decisions:** `legacy-wild-encounter-review-by-pokemon.xlsx`, completed by the user on 2026-08-10.

The decision workbook contains 108 completed rows. Every selection matches its archived row, every calculated slot matches the selected Pokémon, every row is `Ready`, and there are no missing, invalid, or duplicate `(map, base_label)` decisions. In 102 rows the displayed selection occurs once. Six rows select identical entries repeated in adjacent slots: Route 130 Ogerpon, Safari Zone North Gloom, Shoal Cave Low Tide Stairs Room Alolan Sandslash, Safari Zone Southeast Audino, Magma Hideout 2F 3R Lycanroc, and Mirage Tower 4F Aron. Within each of those rows the repeated records have identical species and levels, and deleting any matching occurrence produces the same ordered 12-entry output. The workbook's `MATCH` formula records the first matching slot as the canonical audit value.

The layout audit found 441 IDs shared by the archive and current tree. Their dimensions and primary and secondary tilesets match exactly; the only universal metadata difference is the current required `layout_version: "emerald"`. Of those shared layouts, 380 map binaries are identical and 61 are custom-only changes relative to the common ancestor. There are no upstream-only or both-changed map-binary conflicts. One shared border, `data/layouts/VerdanturfTown/border.bin`, is custom-only.

The archive also contains three custom-only layouts and maps:

| Map | Layout size | Tilesets | Archive group |
| --- | ---: | --- | --- |
| `Littleroot_Extension` | 8 x 10 | General / Petalburg | Towns and Routes |
| `Verdanturf_Extension` | 10 x 20 | General / Mauville | Towns and Routes |
| `PetalburgWoodgrove` | 25 x 30 | General / Petalburg | Dungeons |

The encounter audit uses `(group label, base_label)` as the identity because multiple encounter records may share a map. Across all encounter groups, the common ancestor has 135 records, the archive has 145, and the current tree has 399. The archive modifies 122 shared records and adds 10 records; the current tree changes none of those 135 shared records and adds 264 current-only records. Therefore the semantic encounter merge has no both-changed conflicts.

## Chosen Approach

Use a reproducible semantic three-way import rather than copying archived directories or rebuilding every map manually in PoryMap.

The import has four isolated responsibilities:

1. Materialize and validate the user's 108 removal decisions as a machine-readable migration manifest.
2. Import only the 61 proven custom-only shared layout binaries and one proven custom-only border.
3. Restore and register the three custom maps, adapting their authored sources to current conventions and adding only the adjacent access edges required to reach them.
4. Merge archived custom encounter records into the current JSON by stable `base_label`, applying the removal manifest to 13-slot land tables and retaining current global probability definitions.

The rejected alternatives are a wholesale archive copy, which would overwrite 1.16.3 map and encounter additions, and a fully manual PoryMap rebuild, which would add unnecessary transcription risk across 61 compatible layouts.

## Decision Manifest

Convert the reviewed workbook into `docs/superpowers/inventories/2026-08-10-legacy-wild-encounter-removals.json`. Each record must contain:

- encounter group label;
- map constant;
- unique `base_label`;
- selected legacy slot, numbered 1 through 13;
- species constant;
- minimum and maximum level.

Extraction must validate the workbook selection against `archive/master-pre-1.16.3:src/data/wild_encounters.json`; the spreadsheet is not trusted as an arbitrary source of species data. A selection that matches multiple legacy slots is accepted only when the matches are adjacent, their complete encounter records are identical, and deleting any matching occurrence yields the same ordered table. In that case the first matching slot is canonical. The extractor must abort on a missing decision, duplicate identity, invalid selection, non-invariant duplicate selection, slot mismatch, changed archive source, or any decision count other than 108.

The JSON manifest becomes the reproducible implementation input and review record. The external workbook remains review evidence and is not committed as a binary repository dependency.

## Shared Layout Import

Import the archived `map.bin` only for the 61 shared layout IDs classified as custom-only. Resolve each ID through both versions of `data/layouts/layouts.json` and require equal width, height, primary tileset, and secondary tileset before writing a binary. Keep the current layout entry, paths, ordering, and `layout_version` unchanged.

Import `data/layouts/VerdanturfTown/border.bin` as the only custom-only shared border. Keep all other current borders. Do not copy shared archived `map.json`, events, objects, scripts, warps, or connections as part of the bulk layout operation.

The importer must report the exact layout IDs and before/after blob hashes. It must abort if the audited counts change, a target path is missing, metadata becomes incompatible, or a binary is no longer custom-only relative to the recorded common ancestor.

## Custom Map Restoration

Restore the three custom layout directories, then append their entries to current `data/layouts/layouts.json` with the archived IDs, names, dimensions, tilesets, and paths plus `layout_version: "emerald"`. Register `Littleroot_Extension` and `Verdanturf_Extension` in `gMapGroup_TownsAndRoutes` and `PetalburgWoodgrove` in `gMapGroup_Dungeons`, preserving the current ordering and numeric stability of all existing maps.

Restore each custom map's authoritative `map.json` and adapt it to the current schema. The current directories contain only partial generated `header.inc`, `events.inc`, and `connections.inc` artifacts; they are not authoritative sources. Regenerate those outputs from the restored JSON through the repository's normal map tooling.

The current repository has no authored `scripts.pory` map sources. Translate the archived Littleroot and Verdanturf Poryscript behavior into current authored `scripts.inc` files, and retain Petalburg Woodgrove's authored `scripts.inc`. Do not restore obsolete Poryscript-generated line directives.

Add only these shared-map access deltas:

- `LittlerootTown` gains a `down` connection to `MAP_LITTLEROOT_EXTENSION` at offset `7`; the extension retains its `up` connection at offset `-7`.
- `VerdanturfTown` gains a `down` connection to `MAP_VERDANTURF_EXTENSION` at offset `9`; the extension retains its `up` connection at offset `-9`.
- `PetalburgWoods` gains warps at `(42,3)` and `(43,3)` to Woodgrove destination warps `0` and `1`. Woodgrove retains return warps at `(4,27)` and `(5,27)` to Petalburg Woods destination warps `6` and `7`.

Leave every other current field in the adjacent shared `map.json` files unchanged. Broader shared-map event, object, and script migration remains owned by its separate feature batches.

## Wild Encounter Merge

Use current `src/data/wild_encounters.json` as the output base and archived `src/data/wild_encounters.json` as the custom-content source. Match records by `(wild encounter group label, base_label)`, never by map alone.

For the 122 archive-modified records, replace the matching current record's per-map content with the archived record after conversion. Add the 10 archive-only records:

- `gFortreeCity0`
- `gLavaridgeTown0`
- `gLittlerootTown0`
- `gLittleroot_Extension0`
- `gMauvilleCity0`
- `gOldaleTown0`
- `gPetalburgWoodgrove0`
- `gRustboroCity0`
- `gScorchedSlab0`
- `gVerdanturf_Extension0`

Retain all 264 current-only encounter records and their order. Retain the current group-level encounter probability arrays, including the standard 12-slot land weighting; do not copy the archive's invalid 13-value land probability array, whose values total 85.

For each of the 108 archived 13-slot land tables, remove the manifest-selected occurrence and preserve the remaining entries' relative order, species, and levels. The six invariant duplicate selections use their canonical first matching slot; because their matching records are identical and adjacent, this produces the same final ordered table as removing any other matching occurrence. All other archived land, water, Rock Smash, and fishing records transfer without slot deletion. Preserve each archived per-map `encounter_rate` for a migrated record.

The merger must abort if a current shared record differs from the common ancestor, a `base_label` is duplicated, a manifest record is unused, a 13-slot table lacks one decision, a duplicate selection is not output-invariant, or a final land table has a slot count other than 12. It must emit a report containing every replaced, added, retained-current, and removed-slot record.

## Data Flow and Atomicity

```text
archive layouts + common ancestor + current layout metadata
                         |
                         v
               validated layout import

reviewed workbook + archived encounters
                         |
                         v
              validated removal manifest
                         |
current encounters + archive custom records + manifest
                         |
                         v
                 merged current JSON
```

Run every converter in validation or dry-run mode before writing. A failed precondition leaves the worktree unchanged. Apply map registration, access changes, and encounter output only after all source audits pass. Generated map and encounter artifacts are produced by supported repository generators rather than edited manually.

## Verification

Verification is compile-first and proportionate to data migration risk; this batch does not add a separate test-driven framework.

1. Re-run the removal-manifest verifier and require 108 exact matches with no unused or missing decisions.
2. Re-run the layout classifier and require 61 shared custom-only `map.bin` files, one shared custom-only border, and three custom-only layout IDs.
3. Parse the final layout, map-group, map, and encounter JSON files with the repository's supported tools.
4. Require every migrated species, map, layout, script, warp, and connection identifier to resolve during generation.
5. Require every final land encounter table to contain exactly 12 entries and require the final encounter identity set to equal the current 399 identities plus the 10 archive-only identities.
6. Run the supported full ROM build. If Windows filesystem performance or tool behavior is unreliable, repeat the already proven Git-export build on the WSL native filesystem and require successful linking and `pokeemerald.gba` creation.
7. Open the result in PoryMap and inspect representative early, mid, late, indoor, cave, ocean, and custom layouts for metatile integrity and connection seams.
8. In game, traverse both extension connections and both Woodgrove warp directions, then spot-check custom encounters on ordinary land, water, fishing, Rock Smash, and at least one newly registered custom map.

## Out of Scope

- Copying archived shared-map scripts, objects, dialogue, or event progression beyond the three access deltas.
- Changing the engine from 12 to 13 land slots.
- Replacing current 1.16.3 global encounter probability definitions.
- Migrating archived tilesets when the audited layouts already use matching current tilesets.
- Editing the separate AI trainer feature branch.
- Manually recreating the 61 compatible layouts in PoryMap.

## Exit Criteria

This batch is complete when the manifest and migration reports are reproducible, all audited map and encounter counts reconcile, the full ROM compiles, the three custom maps are registered and reachable, the user's 108 removal choices are reflected exactly, and no current-only upstream encounter or unrelated shared-map behavior is lost.
