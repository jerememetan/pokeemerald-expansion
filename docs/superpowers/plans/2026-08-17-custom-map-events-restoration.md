# Custom Map Events Restoration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore the complete archived event layer for the 61 migrated shared layouts while retaining nonconflicting Expansion 1.16.3 events and adapting all required behavior dependencies.

**Architecture:** A pure semantic alignment library performs deterministic three-way matching for object, warp, coordinate, and background events. A pinned-source CLI derives the 75-map scope, emits a reviewable audit and resolution manifest, generates candidates, validates dependencies, and applies only a coherent reviewed destination set. Focused script adaptations are authored separately from the generated map candidates, and a full ROM build is the final executable acceptance check.

**Tech Stack:** Python 3 standard library (`dataclasses`, `difflib`, `hashlib`, `json`, `pathlib`, `subprocess`, `tempfile`, `unittest`), Git object reads, current `mapjson`, Make, PoryMap, and mGBA.

---

**Design:** [Custom Map Events Restoration Design](../specs/2026-08-14-custom-map-events-restoration-design.md)

**Validation strategy:** Use small standard-library unit fixtures only for the semantic matcher and transaction boundaries; do not introduce a ROM-wide test framework. Candidate/report invariants, map generation, and a clean full ROM build remain the executable acceptance checks.

## File structure

- Create `tools/migration/map_event_merge.py` — pure event signatures, alignment, three-way merge, ordering, and dependency-adaptation helpers.
- Create `tools/migration/merge_legacy_map_events.py` — pinned Git/source orchestration, candidate/report generation, validation, idempotent apply, and recovery.
- Create `tools/migration/tests/test_map_event_merge.py` — focused standard-library fixtures for moved, added, deleted, converged, field-merged, and ambiguous events.
- Create `docs/superpowers/inventories/2026-08-17-legacy-map-event-audit.json` — deterministic audit of all scoped maps and unresolved identities.
- Create `docs/superpowers/inventories/2026-08-17-legacy-map-event-resolutions.json` — reviewed explicit decisions for every ambiguous event and behavior conflict.
- Create `docs/superpowers/inventories/2026-08-17-legacy-map-event-report.json` — final per-event dispositions, dependency ownership, hashes, and validation evidence.
- Modify through the reviewed report: authoritative `data/maps/*/map.json` files for the exact changed subset of the 75 scoped shared maps.
- Modify only when required by the dependency report: focused blocks in existing `data/maps/*/scripts.inc`, `data/text/*.inc`, and current constant/data owners.
- Generated but never staged: candidate maps below `build/legacy-map-events/`, generated map `.inc` files, constants, build outputs, ROMs, and saves.

## Pinned evidence

```python
BASE_COMMIT = "024848a9e9c0ae30cbb9a269779504561d5443d3"
LEGACY_COMMIT = "f5e81e85df6fe40ae490bf7268d0186d7f0426ed"
CURRENT_BASELINE_COMMIT = "49c5f6dcaa57f0fc4dbc5bb114377ad49d6b9f5d"
LAYOUT_REPORT = Path(
    "docs/superpowers/inventories/2026-08-10-legacy-map-layout-report.json"
)
EXPECTED_SHARED_LAYOUTS = 61
EXPECTED_SCOPED_MAPS = 75
EXPECTED_ARCHIVE_CHANGED_MAPS = 69
EVENT_CATEGORIES = ("object_events", "warp_events", "coord_events", "bg_events")
```

The initial diagnostic identified archive deltas on these 69 maps; the production audit must reproduce this exact set before it can write review evidence:

```text
AlteringCave
AquaHideout_B1F
BattleFrontier_PokemonCenter_1F
DewfordTown
DewfordTown_PokemonCenter_1F
EverGrandeCity
EverGrandeCity_PokemonCenter_1F
EverGrandeCity_PokemonLeague_1F
FallarborTown_PokemonCenter_1F
FortreeCity_PokemonCenter_1F
JaggedPass
LavaridgeTown_Gym_1F
LavaridgeTown_Gym_B1F
LilycoveCity
LilycoveCity_PokemonCenter_1F
MagmaHideout_1F
MagmaHideout_2F_1R
MauvilleCity
MauvilleCity_PokemonCenter_1F
MossdeepCity_Gym
MossdeepCity_PokemonCenter_1F
MtPyre_1F
MtPyre_2F
MtPyre_3F
OldaleTown_PokemonCenter_1F
PacifidlogTown_PokemonCenter_1F
PetalburgCity_PokemonCenter_1F
PetalburgWoods
Route102
Route103
Route104
Route106
Route107
Route108
Route109
Route110
Route111
Route112
Route113
Route114
Route115
Route116
Route117
Route118
Route119
Route119_WeatherInstitute_1F
Route120
Route121
Route123
Route124
Route125
Route126
Route127
Route128
Route129
Route130
Route131
RustboroCity
RustboroCity_PokemonCenter_1F
SeafloorCavern_Room1
SeafloorCavern_Room3
SlateportCity_PokemonCenter_1F
SootopolisCity_Gym_1F
SootopolisCity_Gym_B1F
SootopolisCity_PokemonCenter_1F
VerdanturfTown_PokemonCenter_1F
VictoryRoad_1F
VictoryRoad_B1F
VictoryRoad_B2F
```

### Task 1: Build and test the pure semantic matcher

**Files:**

- Create: `tools/migration/map_event_merge.py`
- Create: `tools/migration/tests/test_map_event_merge.py`

- [ ] **Step 1: Write failing fixtures for the approved merge rules**

Create standard-library `unittest` fixtures with small complete event records. Cover these cases individually:

```python
class ObjectMergeTests(unittest.TestCase):
    def test_archive_move_and_current_schema_change_merge(self):
        base = object_event(x=4, y=5, script="Map_EventScript_Npc")
        archive = {**base, "x": 14, "y": 15}
        current = {**base, "local_id": "LOCALID_MAP_NPC"}
        result = merge_base_event("object_events", base, archive, current)
        self.assertEqual((result.event["x"], result.event["y"]), (14, 15))
        self.assertEqual(result.event["local_id"], "LOCALID_MAP_NPC")
        self.assertEqual(result.disposition, "merge_nonconflicting_fields")

    def test_archive_delete_current_unchanged_deletes(self):
        base = object_event(x=4, y=5, script="Map_EventScript_Npc")
        result = merge_base_event("object_events", base, None, base)
        self.assertIsNone(result.event)
        self.assertEqual(result.disposition, "archive_custom_delete")

    def test_current_only_addition_is_retained(self):
        added = object_event(x=6, y=7, script="Map_EventScript_CurrentNpc")
        result = merge_added_event("object_events", None, added)
        self.assertEqual(result.event, added)
        self.assertEqual(result.disposition, "keep_current_only_addition")

    def test_archived_only_addition_is_restored(self):
        added = object_event(x=8, y=9, script="Map_EventScript_CustomNpc")
        result = merge_added_event("object_events", added, None)
        self.assertEqual(result.event, added)
        self.assertEqual(result.disposition, "restore_archive_only_addition")

    def test_same_behavior_change_converges(self):
        base = object_event(x=4, y=5, script="Map_EventScript_Npc")
        moved = {**base, "x": 10}
        result = merge_base_event("object_events", base, moved, moved)
        self.assertEqual(result.event, moved)
        self.assertEqual(result.disposition, "converged_change")

    def test_same_field_conflict_is_unresolved(self):
        base = object_event(x=4, y=5, script="Map_EventScript_Npc")
        archive = {**base, "x": 10}
        current = {**base, "x": 12}
        result = merge_base_event("object_events", base, archive, current)
        self.assertIsNotNone(result.conflict)

    def test_repeated_indistinguishable_objects_are_ambiguous(self):
        repeated = object_event(x=4, y=5, script="Map_EventScript_Npc")
        with self.assertRaises(AmbiguousMatchError):
            align_side("object_events", [repeated, repeated], [repeated, repeated])
```

Add category fixtures for warp destination identity, coordinate trigger payloads, and background-event script/hidden-item payloads. Add ordering fixtures proving archived additions are placed between their matched archived neighbors while current-only relative order remains stable.

- [ ] **Step 2: Run the focused tests and verify the red state**

```powershell
python -m unittest discover -s tools/migration/tests -p 'test_map_event_merge.py' -v
```

Expected: failure because `map_event_merge` and its interfaces do not exist.

- [ ] **Step 3: Implement the matching interfaces**

Expose these focused types and functions. `AmbiguousMatchError` includes the category and candidate indices; `merge_added_event` handles archive/current additions without a base owner. `merge_category` consumes reviewed resolutions by ID and returns the ordered candidates plus disposition records.

```python
PLACEMENT_FIELDS = frozenset({"x", "y", "elevation"})
SCHEMA_ONLY_FIELDS = frozenset({"local_id"})

@dataclass(frozen=True)
class EventRef:
    category: str
    index: int

@dataclass(frozen=True)
class Match:
    base: EventRef | None
    archive: EventRef | None
    current: EventRef | None
    method: str

@dataclass(frozen=True)
class MergeResult:
    event: dict[str, object] | None
    disposition: str
    field_sources: dict[str, str]
    conflict: str | None

class AmbiguousMatchError(ValueError):
    pass

def behavior_signature(category: str, event: dict[str, object]) -> tuple:
    fields = IDENTITY_FIELDS[category]
    return tuple((field, freeze(event.get(field))) for field in fields)

def exact_signature(event: dict[str, object]) -> str:
    normalized = {key: value for key, value in event.items() if key not in SCHEMA_ONLY_FIELDS}
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"))

def align_side(category: str, base: list[dict], side: list[dict]) -> list[Match]:
    return align_in_stages(category, base, side, (exact_signature, behavior_signature))

def merge_base_event(
    category: str,
    base: dict,
    archive: dict | None,
    current: dict | None,
) -> MergeResult:
    return merge_fields_or_conflict(category, base, archive, current)

def merge_added_event(category: str, archive: dict | None, current: dict | None) -> MergeResult:
    return merge_additions_or_conflict(category, archive, current)

def merge_category(
    category: str,
    base: list[dict],
    archive: list[dict],
    current: list[dict],
    resolutions: dict[str, dict],
) -> tuple[list[dict], list[dict]]:
    alignment = align_three_way(category, base, archive, current)
    return build_ordered_candidates(alignment, resolutions)
```

Define `IDENTITY_FIELDS`, `freeze`, `align_in_stages`, `merge_fields_or_conflict`, `merge_additions_or_conflict`, `align_three_way`, and `build_ordered_candidates` in the same focused module. Matching stages must be exact-full-record, exact-behavior-without-placement, then unique category identity. An automatic match is accepted only when unique in both directions. Do not implement nearest-coordinate or first-entry fallback.

- [ ] **Step 4: Implement current item-ball adaptation and test it**

Archived item balls use map-specific scripts such as `Route119_EventScript_ItemElixir`; current maps use `Common_EventScript_FindItem` with the item in `trainer_sight_or_berry_tree_id`.

Implement:

```python
def extract_legacy_item(script_block: str) -> str:
    """Return the unique ITEM_* operand from a finditem command or fail."""

def adapt_item_ball(event: dict[str, object], script_block: str) -> dict[str, object]:
    adapted = copy.deepcopy(event)
    adapted["script"] = "Common_EventScript_FindItem"
    adapted["trainer_sight_or_berry_tree_id"] = extract_legacy_item(script_block)
    return adapted
```

Tests must prove the item and flag are retained, coordinates are unchanged by the adapter, and zero/multiple `ITEM_*` operands fail closed.

- [ ] **Step 5: Run tests and commit the matcher**

```powershell
python -m unittest discover -s tools/migration/tests -p 'test_map_event_merge.py' -v
python -m py_compile tools/migration/map_event_merge.py
git diff --check
git add tools/migration/map_event_merge.py tools/migration/tests/test_map_event_merge.py
git commit -m "tools: add semantic map event matcher"
```

Expected: all focused tests pass and the commit contains only the pure matcher and its fixtures.

### Task 2: Build the pinned audit and freeze the unresolved inventory

**Files:**

- Create: `tools/migration/merge_legacy_map_events.py`
- Create: `docs/superpowers/inventories/2026-08-17-legacy-map-event-audit.json`
- Create: `docs/superpowers/inventories/2026-08-17-legacy-map-event-resolutions.json`

- [ ] **Step 1: Implement immutable Git and layout-scope loading**

Use one resolved immutable commit for every read. Implement the Git helpers directly and keep scope derivation pure:

```python
def git_bytes(commit: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        check=True,
        capture_output=True,
    )
    return result.stdout

def git_json(commit: str, path: str) -> dict[str, object]:
    value = json.loads(git_bytes(commit, path).decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object at {commit}:{path}")
    return value

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def derive_scope(
    layout_report: dict,
    baseline_layouts: dict,
    baseline_maps: dict[str, dict],
) -> tuple[set[str], list[str]]:
    map_paths = {
        write["repository_path"]
        for write in layout_report["writes"]
        if write["repository_path"].endswith("/map.bin")
        and write["old_sha256"] is not None
    }
    layout_ids = {
        layout["id"]
        for layout in baseline_layouts["layouts"]
        if layout["blockdata_filepath"] in map_paths
    }
    map_names = sorted(
        name for name, document in baseline_maps.items() if document["layout"] in layout_ids
    )
    return layout_ids, map_names
```

Require 61 shared layouts, 75 scoped shared maps, and the exact 69-map archive-delta set listed above. Verify the three custom maps separately and exclude them from overwrite candidates.

- [ ] **Step 2: Add audit CLI and deterministic output**

Implement:

```python
parser.add_argument("--candidate-dir", required=True, type=Path)
parser.add_argument("--audit", required=True, type=Path)
parser.add_argument("--resolutions", required=True, type=Path)
parser.add_argument("--report", required=True, type=Path)
parser.add_argument("--audit-only", action="store_true")
parser.add_argument("--apply", action="store_true")
```

In `--audit-only` mode, write the complete alignment inventory even when unresolved matches remain, never write candidates, and exit 2 when `unresolved_count > 0`. The audit root records source commits/hashes, scope counts, category counts, exact matches, unresolved IDs, and dependency references.

Initialize the resolution file with this complete schema and an empty list:

```json
{
  "source_commits": {
    "base": "024848a9e9c0ae30cbb9a269779504561d5443d3",
    "legacy": "f5e81e85df6fe40ae490bf7268d0186d7f0426ed",
    "current": "49c5f6dcaa57f0fc4dbc5bb114377ad49d6b9f5d"
  },
  "resolutions": []
}
```

- [ ] **Step 3: Add dependency block auditing**

Parse labels from the defining current/base/archive `scripts.inc` owner and normalize generated `#` line directives only. Classify referenced labels as identical, archive-changed/current-base, current-changed/archive-base, converged, both-changed, archived-only, current-only, external-common, or standardized item equivalent.

The preliminary audit must explicitly revisit these archive-changed/current-base labels:

```text
AlteringCave_Red_Fight
Route104_EventScript_ExpertF
Route104_EventScript_WhiteHerbFlorist
Route104_EventScript_Darian
Route111_EventScript_Girl
Route120_EventScript_Callie
Route120_EventScript_BadgeCheck
Route123_EventScript_BadgeChecker
RustboroCity_EventScript_Boy1
```

It must also explicitly resolve the preliminary both-changed label `EverGrandeCity_PokemonLeague_1F_EventScript_Clerk`. Presence of a current label is not sufficient; compare normalized block behavior.

- [ ] **Step 4: Run the audit and inspect exact boundaries**

```powershell
python tools/migration/merge_legacy_map_events.py --candidate-dir build/legacy-map-events --audit docs/superpowers/inventories/2026-08-17-legacy-map-event-audit.json --resolutions docs/superpowers/inventories/2026-08-17-legacy-map-event-resolutions.json --report docs/superpowers/inventories/2026-08-17-legacy-map-event-report.json --audit-only
python -m json.tool docs/superpowers/inventories/2026-08-17-legacy-map-event-audit.json > $null
python -m json.tool docs/superpowers/inventories/2026-08-17-legacy-map-event-resolutions.json > $null
git status --short
```

Expected: exit 2 only when the audit reports exact unresolved event IDs; no candidate/source map changes; scope is exactly 61 layouts, 75 maps, and 69 maps with archive deltas.

- [ ] **Step 5: Commit the reproducible audit**

```powershell
git add tools/migration/merge_legacy_map_events.py docs/superpowers/inventories/2026-08-17-legacy-map-event-audit.json docs/superpowers/inventories/2026-08-17-legacy-map-event-resolutions.json
git commit -m "tools: audit legacy map event changes"
```

Expected: the commit changes no authoritative map or script source.

### Task 3: Review and freeze every ambiguous event and behavior decision

**Files:**

- Modify: `docs/superpowers/inventories/2026-08-17-legacy-map-event-resolutions.json`
- Modify: `docs/superpowers/inventories/2026-08-17-legacy-map-event-audit.json`

- [ ] **Step 1: Resolve every audit ID with exact evidence**

Each resolution entry must use this schema:

```json
{
  "id": "Route119:object_events:base-17",
  "map": "Route119",
  "category": "object_events",
  "base_index": 17,
  "archive_index": 17,
  "current_index": 17,
  "decision": "merge_fields",
  "field_sources": {"x": "archive", "y": "archive", "script": "current"},
  "evidence": "Unique flag and trainer identity; archive moved placement while current adapted behavior."
}
```

Allowed decisions are `use_archive`, `use_current`, `merge_fields`, `delete`, `keep_both`, `current_equivalent`, and `deduplicate`. Every index is an integer or `null`; every `merge_fields` entry names all differing fields. Reject unknown IDs, duplicate IDs, unused resolutions, or free-form decisions.

- [ ] **Step 2: Review dependency equivalents**

For item balls, require evidence linking the archived map-specific script's unique `finditem ITEM_*` operand to the current generic event. For renamed custom behavior, record the current label and compare commands; for example, verify whether current `AlteringCave_EventScript_Red` is the deliberate equivalent of archived `AlteringCave_Red_Fight` before selecting `current_equivalent`.

For the Route 120 and Route 123 badge-check events and all other archive semantic changes, choose `use_archive`, `merge_fields`, or an evidenced current equivalent. Do not select a category-level default.

- [ ] **Step 3: Re-run audit mode until it is fully resolved**

```powershell
python tools/migration/merge_legacy_map_events.py --candidate-dir build/legacy-map-events --audit docs/superpowers/inventories/2026-08-17-legacy-map-event-audit.json --resolutions docs/superpowers/inventories/2026-08-17-legacy-map-event-resolutions.json --report docs/superpowers/inventories/2026-08-17-legacy-map-event-report.json --audit-only
```

Expected: exit 0, `unresolved_count: 0`, every resolution is consumed exactly once, and every archived/custom and current-only event has one disposition.

- [ ] **Step 4: Commit reviewed resolutions**

```powershell
git add docs/superpowers/inventories/2026-08-17-legacy-map-event-audit.json docs/superpowers/inventories/2026-08-17-legacy-map-event-resolutions.json
git commit -m "docs: resolve legacy map event conflicts"
```

Expected: a docs-only commit freezes every manual decision before source mutation.

### Task 4: Generate exact candidates and adapt behavior dependencies

**Files:**

- Modify: `tools/migration/map_event_merge.py`
- Modify: `tools/migration/merge_legacy_map_events.py`
- Modify: `tools/migration/tests/test_map_event_merge.py`
- Create: `docs/superpowers/inventories/2026-08-17-legacy-map-event-report.json`
- Modify only as named by the resolved dependency inventory: focused `data/maps/*/scripts.inc`, `data/text/*.inc`, and constant/data owner files.

- [ ] **Step 1: Write failing tests for resolution consumption and dependency adapters**

Add fixtures proving:

- Every unresolved ID requires exactly one resolution.
- Every supplied resolution is consumed.
- Field-source maps cover every differing field.
- Archived item-ball scripts adapt to `Common_EventScript_FindItem` with the correct item.
- A deliberate current equivalent must name an existing current label and an evidence hash.
- Both-changed script behavior remains unresolved without a specific decision.

Run the test command and require failures before implementing the missing behavior.

- [ ] **Step 2: Implement final candidate construction**

For each scoped map, deep-copy the current-baseline JSON and replace only the four event arrays with reviewed merged output. Preserve every other current field, including Task 3's Petalburg Woods access warps. Verify candidate maps reference their unchanged current layout IDs.

Write candidates beneath:

```text
build/legacy-map-events/data/maps/<MapName>/map.json
```

Do not write candidates for the three custom maps; instead compare their current event arrays against their adapted archived source and report validation status.

- [ ] **Step 3: Author only required dependency patches**

For each dependency disposition marked `use_archive` or `merge_fields`, transplant the smallest complete label block plus recursively required labels/text/constants. Strip archived generated `#` directives, adapt current macro names, and keep current equivalents where selected.

At minimum, explicitly close the nine preliminary archive-changed labels and the one both-changed clerk label listed in Task 2. The final report must name the exact source and target path for every authored patch. Do not copy whole shared script files.

- [ ] **Step 4: Validate candidate invariants and write the final report**

Require:

```python
assert scoped_map_count == 75
assert archive_changed_map_count == 69
assert unresolved_count == 0
assert duplicate_event_identity_count == 0
assert out_of_bounds_event_count == 0
assert missing_dependency_count == 0
assert unused_resolution_count == 0
```

Validate object coordinates and movement ranges against layout dimensions, local-ID uniqueness, flag/item/trainer/graphics/constants, warp destinations and indices, and every script symbol. Record exact current-only retained counts and archive-added/moved/deleted/merged counts by category.

- [ ] **Step 5: Run candidate generation without apply**

```powershell
python tools/migration/merge_legacy_map_events.py --candidate-dir build/legacy-map-events --audit docs/superpowers/inventories/2026-08-17-legacy-map-event-audit.json --resolutions docs/superpowers/inventories/2026-08-17-legacy-map-event-resolutions.json --report docs/superpowers/inventories/2026-08-17-legacy-map-event-report.json
python -m json.tool docs/superpowers/inventories/2026-08-17-legacy-map-event-report.json > $null
git status --short
```

Expected: authoritative `map.json` files remain unchanged; candidates and report are deterministic; no unresolved match/dependency remains.

- [ ] **Step 6: Commit the candidate engine, evidence, and focused dependency patches**

Stage the two tools, tests, final report, and only dependency paths listed by the report. Exclude candidate maps and generated files.

```powershell
git commit -m "feat: adapt custom map event behavior"
```

Expected: the commit compiles against the still-current map arrays or the patches are guarded so the intermediate commit remains buildable.

### Task 5: Apply reviewed event maps and compile

**Files:**

- Modify through report allowlist: exact authoritative `data/maps/*/map.json` candidate targets.
- Modify: `docs/superpowers/inventories/2026-08-17-legacy-map-event-report.json` only if apply-state hashes are recorded.

- [ ] **Step 1: Add coherent-state and recovery tests**

Use isolated temporary directories to prove:

- An exact pre-migration set applies all candidates.
- An exact post-migration set performs zero authoritative replacements.
- One preimage among postimages and one postimage among preimages both fail before writes.
- An arbitrary third-state map fails before candidates/report/source mutation.
- Forward failure rolls back all prior maps.
- Forward plus rollback failure retains every sole preimage under an explicit path named in the error.
- Candidate/report/source/resolution/internal paths cannot collide.

- [ ] **Step 2: Apply the reviewed candidates**

```powershell
python tools/migration/merge_legacy_map_events.py --candidate-dir build/legacy-map-events --audit docs/superpowers/inventories/2026-08-17-legacy-map-event-audit.json --resolutions docs/superpowers/inventories/2026-08-17-legacy-map-event-resolutions.json --report docs/superpowers/inventories/2026-08-17-legacy-map-event-report.json --apply
```

Expected: only report-listed authoritative map paths change; every applied hash matches its candidate; no transaction or recovery debris remains.

- [ ] **Step 3: Generate maps and run the full build**

```powershell
make -j4 generated
make -j4
```

If the mounted Windows worktree stalls, export exact authored HEAD plus the reviewed map candidates to a temporary WSL-native directory. Run `make -j4 tools`, `make -j4 generated`, and `make -j4`; require exit 0 and a nonempty `pokeemerald.gba`. Do not copy build artifacts back.

- [ ] **Step 4: Verify deterministic post-state rerun**

Run the candidate command and `--apply` again from the post-state. Expected: candidate/report hashes reproduce exactly and apply reports zero authoritative replacements.

- [ ] **Step 5: Commit the authoritative map arrays**

Build the stage allowlist from `report.writes[].repository_path`, stage exactly those map JSON paths plus the final report if changed, and commit:

```powershell
git commit -m "feat: restore custom map events"
```

Expected: no generated includes, ROM, save, build candidate, or unrelated map source is staged.

### Task 6: End-to-end map and runtime verification

**Files:**

- Verify authored/generated state; no new source file is required.

- [ ] **Step 1: Re-run every deterministic verifier**

Run the matcher tests, audit-only command, candidate command, post-state apply, JSON parsing, Python compilation, and `git diff --check`. Require exact report/candidate reproduction and zero unresolved/dependency errors.

- [ ] **Step 2: Verify all scoped event arrays programmatically**

For all 75 maps, compare final events to the disposition report. Require every archived custom change and current-only addition to appear exactly once, coordinates/movement bounds to fit, destinations to resolve, and dependency labels/constants to exist.

- [ ] **Step 3: Inspect high-risk maps in PoryMap**

Open without saving and inspect at minimum:

```text
Route104, Route110, Route111, Route116, Route119, Route120, Route123,
MossdeepCity_Gym, LavaridgeTown_Gym_1F, LavaridgeTown_Gym_B1F,
Littleroot_Extension, Verdanturf_Extension, PetalburgWoodgrove
```

Confirm NPCs/trainers/items occupy intended passable tiles and that signs, hidden items, coordinate triggers, and warps align with the visible map geometry.

- [ ] **Step 4: Perform mGBA sampling with a disposable save**

Exercise at least one example of each disposition: moved NPC, archived-added NPC, current-only retained NPC, archived deletion, trainer, visible item, hidden item/sign, coordinate trigger, and moved warp. Also traverse both extension connections and both Woods/Woodgrove warp pairs.

Do not mutate a real save. If no disposable save or navigation harness exists, report these checks as pending manual acceptance and do not claim them.

- [ ] **Step 5: Confirm clean handoff**

```powershell
git status --short
git log -8 --oneline
git worktree list
```

Expected: tracked tree clean, only intended worktrees registered, no `.legacy-*`, recovery, candidate, generated, ROM, or save artifact staged.

## Plan self-review

- Every design requirement maps to a task: semantic alignment (Task 1), pinned audit and exact ownership (Task 2), reviewed ambiguity resolution (Task 3), dependencies and candidates (Task 4), idempotent safe apply/build (Task 5), and visual/runtime handoff (Task 6).
- The plan distinguishes 75 scoped shared maps, 69 archived event-delta maps, and three validation-only custom maps.
- Current item-ball schema adaptation and preliminary changed-script labels are explicit rather than deferred generically.
- Source mutation cannot begin until the audit has zero unresolved IDs and all resolution entries are consumed.
- No new ROM-wide test framework is introduced; standard-library fixtures cover only algorithms that compilation cannot validate.
- Placeholder scan is clean: runtime-generated conflict IDs are resolved through a defined schema and review gate rather than unspecified implementation work.
