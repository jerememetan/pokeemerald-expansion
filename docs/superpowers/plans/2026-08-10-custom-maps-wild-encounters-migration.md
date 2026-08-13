# Custom Maps and Wild Encounters Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore 61 custom shared layouts, three registered custom maps, and every reviewed custom wild encounter on Expansion 1.16.3 without losing current-only upstream data.

**Architecture:** Three standard-library migration commands provide reproducible decision extraction, binary-layout import, and semantic encounter merge. Map registration and access edges remain small authored JSON/script patches. Every mutation has a dry-run or candidate stage, exact audited counts, and compile-first verification.

**Tech Stack:** Python 3 standard library, Git object access, OOXML (`zipfile` and `xml.etree.ElementTree`), current `mapjson`, current wild-encounter generator, Make, and PoryMap for visual inspection.

**Design:** [Custom Maps and Wild Encounters Migration Design](../specs/2026-08-10-custom-maps-wild-encounters-migration-design.md)

**Validation strategy:** The user explicitly chose compile-first migration rather than a new unit-test harness. Each tool must fail closed on count, identity, hash, schema, and slot invariants before `--apply`; generation and a full ROM build are the executable acceptance checks.

---

## File structure

- Create `tools/migration/extract_legacy_wild_encounter_removals.py` — read the reviewed workbook, validate every decision against the archived JSON, and emit the removal manifest.
- Create `tools/migration/import_legacy_map_layouts.py` — classify and materialize only proven custom layout binaries, with candidate and explicit-apply modes.
- Create `tools/migration/merge_legacy_wild_encounters.py` — perform the conflict-checked semantic encounter merge.
- Create `docs/superpowers/inventories/2026-08-10-legacy-wild-encounter-removals.json` — 108 reviewed removal records.
- Create `docs/superpowers/inventories/2026-08-10-legacy-map-layout-report.json` — binary import hashes and classification evidence.
- Create `docs/superpowers/inventories/2026-08-10-legacy-wild-encounter-report.json` — replaced, added, retained, and removed-slot evidence.
- Modify `data/layouts/layouts.json` — append three Emerald layouts without renumbering existing layouts.
- Modify `data/maps/map_groups.json` — append two maps to Towns and Routes and one map to Dungeons without renumbering existing entries.
- Create `data/maps/{Littleroot_Extension,Verdanturf_Extension,PetalburgWoodgrove}/map.json` — adapted current-schema custom map sources.
- Create `data/maps/{Littleroot_Extension,Verdanturf_Extension,PetalburgWoodgrove}/scripts.inc` — current authored script sources.
- Modify `data/event_scripts.s` — include the three new authored map scripts in their matching map-group sections.
- Modify `data/maps/{LittlerootTown,VerdanturfTown,PetalburgWoods}/map.json` — only the reciprocal access edges.
- Modify `data/text/trainers.inc` — only the three Verdanturf Leaf dialogue labels required by the restored object.
- Modify 61 existing `data/layouts/*/map.bin` files and `data/layouts/VerdanturfTown/border.bin` through the validated importer.
- Create `data/layouts/{Littleroot_Extension,Verdanturf_Extension,PetalburgWoodgrove}/{map.bin,border.bin}` through the validated importer.
- Modify `src/data/wild_encounters.json` through the semantic merger.
- Generated but ignored: map `.inc` outputs, layout/map constants, and `src/data/wild_encounters.h`; regenerate them, never hand-edit or commit them.

### Task 1: Extract and freeze the reviewed removal decisions

**Files:**

- Create: `tools/migration/extract_legacy_wild_encounter_removals.py`
- Create: `docs/superpowers/inventories/2026-08-10-legacy-wild-encounter-removals.json`

- [ ] **Step 1: Implement the standard-library workbook reader**

Use `zipfile.ZipFile` and `xml.etree.ElementTree` only. Resolve the `Encounter Review` sheet through `xl/workbook.xml` plus `xl/_rels/workbook.xml.rels`; do not assume it is `sheet1.xml`. Support shared-string, inline-string, and numeric cells. Expose these interfaces:

```python
def load_shared_strings(book: zipfile.ZipFile) -> list[str]: ...
def resolve_sheet_path(book: zipfile.ZipFile, sheet_name: str) -> str: ...
def read_cells(book: zipfile.ZipFile, sheet_path: str) -> dict[str, str]: ...
def read_review_rows(path: Path) -> list[dict[str, object]]: ...
```

`read_review_rows` must read rows 6 through 113 and columns `A`, `B`, `D`, `E`, and `G:S`. It must reject a missing row, blank map, blank `base_label`, blank selection, a nonnumeric calculated slot, or a roster with other than 13 displayed entries.

- [ ] **Step 2: Validate selections against the archived source**

Load `archive/master-pre-1.16.3:src/data/wild_encounters.json` with:

```python
def git_json(ref: str, path: str) -> dict[str, object]:
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)
```

Build a globally unique `base_label` lookup that retains each record's group label; reject a duplicated `base_label` across groups. Parse each workbook selection with `r"^(SPECIES_[A-Z0-9_]+) \(Lv (\d+)-(\d+)\)$"`. Resolve the workbook `base_label`, then require its map, species, levels, and calculated slot to match the archive. Emit the resolved group label into the manifest.

For multiple matches, require adjacent indices, identical complete encounter dictionaries, and identical results after deleting each matching index. Record the first match as `legacy_slot`. These six known invariant duplicates must validate: Route 130 Ogerpon, Safari Zone North Gloom, Shoal Cave Low Tide Stairs Room Alolan Sandslash, Safari Zone Southeast Audino, Magma Hideout 2F 3R Lycanroc, and Mirage Tower 4F Aron.

- [ ] **Step 3: Add fail-closed CLI and deterministic JSON output**

Implement:

```python
parser.add_argument("--workbook", required=True, type=Path)
parser.add_argument("--output", required=True, type=Path)
parser.add_argument("--legacy-ref", default="archive/master-pre-1.16.3")
```

The output root must contain `source_refs`, `decision_count`, `single_match_count`, `invariant_duplicate_count`, and ordered `decisions`. Each decision contains `group_label`, `map`, `base_label`, `legacy_slot`, `species`, `min_level`, and `max_level`. Require counts `108`, `102`, and `6` before writing.

- [ ] **Step 4: Run extraction and inspect boundaries**

Run:

```powershell
python tools/migration/extract_legacy_wild_encounter_removals.py --workbook 'C:\Users\jerem\.codex\outputs\019fe59c-21bf-7572-9c2f-3b2fd3b56168\legacy-wild-encounter-review-by-pokemon.xlsx' --output docs/superpowers/inventories/2026-08-10-legacy-wild-encounter-removals.json
python -m json.tool docs/superpowers/inventories/2026-08-10-legacy-wild-encounter-removals.json > $null
```

Expected: both commands exit 0; counts are 108 decisions, 102 single matches, and 6 invariant duplicates. Spot-check Route 101 removes Skitty at slot 5 and Petalburg Woodgrove removes Eevee at slot 11.

- [ ] **Step 5: Commit the decision evidence**

```powershell
git add tools/migration/extract_legacy_wild_encounter_removals.py docs/superpowers/inventories/2026-08-10-legacy-wild-encounter-removals.json
git commit -m "tools: record reviewed wild encounter removals"
```

Expected: one commit contains only the extractor and reproducible 108-row manifest.

### Task 2: Import only audited layout binaries

**Files:**

- Create: `tools/migration/import_legacy_map_layouts.py`
- Create: `docs/superpowers/inventories/2026-08-10-legacy-map-layout-report.json`
- Modify/Create: audited `data/layouts/*/{map.bin,border.bin}` paths only

- [ ] **Step 1: Implement three-way layout classification**

Use constants and helpers:

```python
LEGACY_REF = "archive/master-pre-1.16.3"
BASE_REF = "024848a9e9c0ae30cbb9a269779504561d5443d3"
LAYOUTS_JSON = "data/layouts/layouts.json"
CUSTOM_LAYOUT_IDS = {
    "LAYOUT_LITTLEROOT_EXTENSION",
    "LAYOUT_VERDANTURF_EXTENSION",
    "LAYOUT_PETALBURG_WOODGROVE",
}
METADATA_FIELDS = ("width", "height", "primary_tileset", "secondary_tileset")

def git_bytes(ref: str, path: str) -> bytes: ...
def git_json(ref: str, path: str) -> dict[str, object]: ...
def sha256(data: bytes) -> str: ...
```

For every shared layout ID, require equal `METADATA_FIELDS`. Classify a shared `map.bin` as custom-only only when `legacy != base` and `current == base`. Require exactly 61 custom-only maps, 380 identical maps, zero upstream-only changes, and zero both-changed conflicts. Classify unique border paths the same way and require only `data/layouts/VerdanturfTown/border.bin` to be custom-only.

- [ ] **Step 2: Add candidate and explicit apply modes**

Implement required `--candidate-dir` and `--report`, plus optional `--apply`. Candidate mode writes the 61 shared maps, one border, and six binary files for the three custom layouts beneath the candidate directory using repository-relative paths. Apply mode writes only the freshly validated candidate bytes to those exact worktree paths.

Report `source_refs`, classification counts, and for every write: layout ID, repository path, old SHA-256 when present, new SHA-256, and byte length. Reject archive-only layout IDs other than the exact three constants and require each custom border to be 8 bytes.

- [ ] **Step 3: Generate and review the candidate**

```powershell
python tools/migration/import_legacy_map_layouts.py --candidate-dir build/legacy-map-layouts --report docs/superpowers/inventories/2026-08-10-legacy-map-layout-report.json
python -m json.tool docs/superpowers/inventories/2026-08-10-legacy-map-layout-report.json > $null
git status --short
```

Expected: source paths remain unchanged; the report lists 61 shared map binaries, one shared border, and three custom layout pairs with no conflict category.

- [ ] **Step 4: Apply and verify exact scope**

```powershell
python tools/migration/import_legacy_map_layouts.py --candidate-dir build/legacy-map-layouts --report docs/superpowers/inventories/2026-08-10-legacy-map-layout-report.json --apply
git status --short
git diff --stat
```

Expected: exactly 61 existing `map.bin` files and `VerdanturfTown/border.bin` change; three new layout directories contain only `map.bin` and `border.bin`.

- [ ] **Step 5: Commit binary import and evidence**

```powershell
$report = Get-Content -LiteralPath 'docs/superpowers/inventories/2026-08-10-legacy-map-layout-report.json' -Raw | ConvertFrom-Json
$layoutPaths = @($report.writes | ForEach-Object { $_.repository_path })
git add -- tools/migration/import_legacy_map_layouts.py docs/superpowers/inventories/2026-08-10-legacy-map-layout-report.json
git add -- $layoutPaths
git commit -m "feat: restore custom map layouts"
```

Expected: the commit contains no map registration, scripts, or encounter data.

### Task 3: Register and connect the three custom maps

**Files:**

- Modify: `data/layouts/layouts.json`
- Modify: `data/maps/map_groups.json`
- Modify: `data/event_scripts.s`
- Create: `data/maps/Littleroot_Extension/{map.json,scripts.inc}`
- Create: `data/maps/Verdanturf_Extension/{map.json,scripts.inc}`
- Create: `data/maps/PetalburgWoodgrove/{map.json,scripts.inc}`
- Modify: `data/maps/LittlerootTown/map.json`
- Modify: `data/maps/VerdanturfTown/map.json`
- Modify: `data/maps/PetalburgWoods/map.json`
- Modify: `data/text/trainers.inc`

- [ ] **Step 1: Register current-schema layout entries**

Append the three archived entries to the end of the `data/layouts/layouts.json` array in Verdanturf, Littleroot, and Woodgrove order so every existing layout retains its numeric ID. Each entry must add:

```json
"border_width": 2,
"border_height": 2,
"layout_version": "emerald"
```

Keep the archived IDs, names, dimensions, tilesets, and file paths exactly as specified by the design. Parse the result with `python -m json.tool data/layouts/layouts.json > $null`.

- [ ] **Step 2: Register maps without moving existing IDs**

Append `"Verdanturf_Extension"` and `"Littleroot_Extension"` to the end of `gMapGroup_TownsAndRoutes`. Append `"PetalburgWoodgrove"` to the end of `gMapGroup_Dungeons`. Do not insert them beside their neighboring maps because insertion would renumber later current map IDs.

Run `python -m json.tool data/maps/map_groups.json > $null`. Expected: every previously generated current map constant retains its group and number; the three new constants occupy new final indices in their groups.

- [ ] **Step 3: Create adapted authoritative map JSON**

Create each file from its archived `map.json`, then make only these schema adaptations:

```json
"region": "REGION_HOENN"
```

Add `region` after `music` in all three maps. Change Woodgrove's archived `"connections": 0` to `"connections": []`. Preserve archived objects, coordinates, weather, music, warps, and flags exactly.

Run `python -m json.tool` on all three files. Expected: each exits 0 and references its new layout ID.

- [ ] **Step 4: Create current authored scripts and required Leaf text**

Create `Littleroot_Extension/scripts.inc` as:

```asm
Littleroot_Extension_MapScripts::
	.byte 0
```

Create `PetalburgWoodgrove/scripts.inc` as:

```asm
PetalburgWoodgrove_MapScripts::
	.byte 0
```

Create `Verdanturf_Extension/scripts.inc` with the map-script terminator plus:

```asm
Verdanturf_Extension_EventScript_Leaf::
	trainerbattle_single TRAINER_LEAF, VerdanturfExtension_LeafIntro, VerdanturfExtension_LeafDefeat
	msgbox VerdanturfExtension_LeafPostBattle, MSGBOX_AUTOCLOSE
	end
```

In `data/event_scripts.s`, append the Verdanturf and Littleroot script includes to the end of the Towns and Routes map-script section in map-group order, and append the Woodgrove script include to the end of the Dungeons section. Do not reorder existing includes.

Append only the archived `VerdanturfExtension_LeafIntro`, `VerdanturfExtension_LeafDefeat`, and `VerdanturfExtension_LeafPostBattle` string blocks to `data/text/trainers.inc`. Preserve their archived text byte-for-byte; do not import neighboring trainer text.

- [ ] **Step 5: Add only reciprocal access edges**

Patch current shared map JSON without replacing other fields:

```json
{"map":"MAP_LITTLEROOT_EXTENSION","offset":7,"direction":"down"}
{"map":"MAP_VERDANTURF_EXTENSION","offset":9,"direction":"down"}
```

Add the first to `LittlerootTown.connections` and the second to `VerdanturfTown.connections`. Append Petalburg Woods warps `(42,3) -> MAP_PETALBURG_WOODGROVE warp 0` and `(43,3) -> MAP_PETALBURG_WOODGROVE warp 1`. Do not alter existing objects, scripts, connections, or warps.

- [ ] **Step 6: Regenerate maps and compile the map batch**

```powershell
make -j4 generated
make -j4
```

Expected: `mapjson` generates all three maps, all reciprocal constants resolve, the Verdanturf Leaf dialogue links, the ROM links successfully, and ignored generated files are not staged.

- [ ] **Step 7: Commit registered custom maps**

Stage only the authored map sources in this batch:

```powershell
git add data/layouts/layouts.json data/maps/map_groups.json data/event_scripts.s data/maps/Littleroot_Extension/map.json data/maps/Littleroot_Extension/scripts.inc data/maps/Verdanturf_Extension/map.json data/maps/Verdanturf_Extension/scripts.inc data/maps/PetalburgWoodgrove/map.json data/maps/PetalburgWoodgrove/scripts.inc data/maps/LittlerootTown/map.json data/maps/VerdanturfTown/map.json data/maps/PetalburgWoods/map.json data/text/trainers.inc
git commit -m "feat: register custom extension maps"
```

Expected: the commit excludes ignored generated `.inc` and header outputs.

### Task 4: Merge all archived custom wild encounters

**Files:**

- Create: `tools/migration/merge_legacy_wild_encounters.py`
- Create: `docs/superpowers/inventories/2026-08-10-legacy-wild-encounter-report.json`
- Modify: `src/data/wild_encounters.json`

- [ ] **Step 1: Implement stable identity and conflict checks**

Use `(group["label"], encounter["base_label"])` as the only identity. Load current JSON from disk, legacy JSON from `archive/master-pre-1.16.3`, and base JSON from `024848a9e9c0ae30cbb9a269779504561d5443d3`. Reject duplicate identities.

Require these exact classifications before producing a candidate:

```python
EXPECTED = {
    "base": 135,
    "legacy": 145,
    "current": 399,
    "legacy_modified": 122,
    "legacy_only": 10,
    "current_only": 264,
    "both_changed_conflicts": 0,
}
```

Also require current group-level `fields` to remain the output fields; never copy the legacy 13-value land-rate array.

- [ ] **Step 2: Implement reviewed 13-to-12 conversion**

Load the committed removal manifest and index it by `(group_label, base_label)`. For every legacy-modified or legacy-only record:

```python
converted = copy.deepcopy(legacy_record)
land = converted.get("land_mons")
if land and len(land["mons"]) == 13:
    decision = decisions.pop(identity)
    removed = land["mons"].pop(decision["legacy_slot"] - 1)
    assert removed == {
        "min_level": decision["min_level"],
        "max_level": decision["max_level"],
        "species": decision["species"],
    }
```

Require every converted land table to have 12 entries, every decision to be consumed once, and all 108 removals to match. Preserve water, Rock Smash, fishing, per-map rates, and the relative order of all remaining entries.

- [ ] **Step 3: Build candidate output without reordering current data**

Replace each of the 122 modified identities in its existing current position. Append the 10 legacy-only identities to `gWildMonHeaders` in their archived relative order. Keep all 264 current-only records in place. Require final totals of 409 identities across all groups and 398 records in `gWildMonHeaders`.

Support required `--candidate`, `--report`, and `--removals`, plus optional `--apply`. Without `--apply`, never write `src/data/wild_encounters.json`. Report exact identity lists for `replaced`, `added`, `retained_current_only`, and `removed_slots`, plus SHA-256 digests.

- [ ] **Step 4: Generate and audit the candidate**

```powershell
python tools/migration/merge_legacy_wild_encounters.py --removals docs/superpowers/inventories/2026-08-10-legacy-wild-encounter-removals.json --candidate build/legacy-wild-encounters.json --report docs/superpowers/inventories/2026-08-10-legacy-wild-encounter-report.json
python -m json.tool build/legacy-wild-encounters.json > $null
python -m json.tool docs/superpowers/inventories/2026-08-10-legacy-wild-encounter-report.json > $null
git status --short
```

Expected: source JSON remains unchanged; report counts are 122 replaced, 10 added, 264 retained-current-only, 108 removed slots, and zero conflicts.

- [ ] **Step 5: Apply, generate, and compile**

```powershell
python tools/migration/merge_legacy_wild_encounters.py --removals docs/superpowers/inventories/2026-08-10-legacy-wild-encounter-removals.json --candidate build/legacy-wild-encounters.json --report docs/superpowers/inventories/2026-08-10-legacy-wild-encounter-report.json --apply
python tools/wild_encounters/wild_encounters_to_header.py
make -j4
```

Expected: generation resolves every species and all three custom map constants; the full ROM links with 12 land entries per table.

- [ ] **Step 6: Commit encounter migration**

```powershell
git add tools/migration/merge_legacy_wild_encounters.py docs/superpowers/inventories/2026-08-10-legacy-wild-encounter-report.json src/data/wild_encounters.json
git commit -m "feat: migrate custom wild encounters"
```

Expected: no generated `src/data/wild_encounters.h` or build artifact is staged.

### Task 5: End-to-end verification and handoff

**Files:**

- Verify authored and generated state; no new source file is required.

- [ ] **Step 1: Re-run every deterministic verifier**

Re-run the Task 1 extractor, Task 2 importer in candidate mode, and Task 4 merger in candidate mode. Compare reports to the committed JSON evidence.

Expected: 108 decisions, 61 shared custom maps, one shared border, three custom layouts, 122 replaced encounters, 10 added encounters, 264 retained current-only encounters, and zero conflicts.

- [ ] **Step 2: Verify a clean full build**

Run `make -j4`. If the mounted Windows worktree is unreliable, export committed `HEAD` to a temporary WSL-native directory, run `make -j4` there, and require exit 0 plus a generated `pokeemerald.gba`. Do not copy build artifacts back into the repository.

- [ ] **Step 3: Inspect layout integrity in PoryMap**

Open the current project and inspect at least: Route 101, Route 119, Sootopolis City, Victory Road B2F, Littleroot Extension, Verdanturf Extension, and Petalburg Woodgrove. Confirm dimensions, tilesets, metatiles, borders, and connection/warp seams.

- [ ] **Step 4: Perform in-game path and encounter checks**

Traverse Littleroot Town south and back, Verdanturf Town south and back, and both Petalburg Woods/Woodgrove warp pairs. Trigger one migrated land encounter, water encounter, fishing encounter, Rock Smash encounter, and one encounter in each custom map that defines encounters.

Expected: transitions work in both directions, no player is placed in an impassable tile, and sampled species/levels match the migrated tables.

- [ ] **Step 5: Confirm clean repository state**

```powershell
git status --short
git log -5 --oneline
```

Expected: no uncommitted authored source remains; the recent commits separate decision evidence, binary layouts, map registration, and encounter data.

## Plan self-review

- Covers every design requirement, including the three Leaf dialogue dependencies discovered during file mapping.
- Keeps binary import, authored map registration, and encounter merge independently reviewable and reversible.
- Uses candidate-first commands and exact count assertions instead of adding a test framework the user rejected.
- Never copies shared archived scripts/events or legacy group-level encounter probabilities.
- Preserves all current-only encounters and current map IDs while making all three custom maps reachable.
