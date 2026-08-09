# Legacy Feature Inventory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a reproducible, reviewed inventory of every archived-hack difference before porting ROM features to 1.16.3.

**Architecture:** A small standard-library Python command reads Git's NUL-delimited name-status output for `master...archive/master-pre-1.16.3`, assigns every path to a migration category, and emits deterministic JSON. A Markdown review groups those paths into feature decisions. The tool is reporting-only and never copies legacy source files.

**Tech Stack:** Python 3 standard library, Git, unittest.

---

## File structure

- Create: `tools/migration/generate_legacy_inventory.py` — Git-diff parser and JSON renderer.
- Create: `tools/migration/tests/test_generate_legacy_inventory.py` — parser, classifier, and JSON-shape tests.
- Create: `docs/superpowers/inventories/2026-08-09-legacy-feature-inventory.json` — generated path-level evidence.
- Create: `docs/superpowers/inventories/2026-08-09-legacy-feature-review.md` — feature-level decisions.
- Modify: `docs/superpowers/specs/2026-08-09-original-hack-1.16.3-migration-design.md` — links to both evidence files.

### Task 1: Define the inventory behavior with failing tests

**Files:**

- Create: `tools/migration/tests/test_generate_legacy_inventory.py`
- Test: `tools/migration/tests/test_generate_legacy_inventory.py`

- [ ] **Step 1: Add tests for NUL-delimited Git records, including rename records**

```python
raw = b"M\\0src/main.c\\0A\\0graphics/ui_startmenu_full/logo.png\\0R100\\0old.c\\0new.c\\0"
assert parse_name_status(raw) == [
    {"status": "M", "old_path": None, "path": "src/main.c"},
    {"status": "A", "old_path": None, "path": "graphics/ui_startmenu_full/logo.png"},
    {"status": "R100", "old_path": "old.c", "path": "new.c"},
]
```

- [ ] **Step 2: Add table-driven classifier tests**

```python
assert classify_path("data/maps/LittlerootTown/scripts.pory") == "maps-and-events"
assert classify_path("graphics/ui_startmenu_full/bg.png") == "ui-and-quality-of-life"
assert classify_path("data/trainers.parties") == "game-content"
assert classify_path("src/battle_script_commands.c") == "gameplay-and-battle"
assert classify_path("tools/poryscript/poryscript") == "tooling-and-generated-output"
```

- [ ] **Step 3: Run the test module before implementation**

Run: `python -m unittest tools/migration/tests/test_generate_legacy_inventory.py -v`

Expected: FAIL because `generate_legacy_inventory` does not exist.

- [ ] **Step 4: Commit the failing test checkpoint**

Run: `git add tools/migration/tests/test_generate_legacy_inventory.py; git commit -m "test: define legacy inventory expectations"`

Expected: one test-only commit.

### Task 2: Implement the reporting-only inventory command

**Files:**

- Create: `tools/migration/generate_legacy_inventory.py`
- Test: `tools/migration/tests/test_generate_legacy_inventory.py`

- [ ] **Step 1: Implement `parse_name_status(raw)`**

Split the byte string by `b"\\0"`, discard the final empty field, decode UTF-8, and consume one path for ordinary statuses or two paths for statuses beginning with `R` or `C`. Return dictionaries with exactly `status`, `old_path`, and `path`.

- [ ] **Step 2: Implement `classify_path(path)` with these ordered rules**

```python
if path.startswith(("data/maps/", "data/layouts/")):
    return "maps-and-events"
if path.startswith(("graphics/ui_", "graphics/interface", "src/start_menu", "src/option_menu", "src/item_menu")):
    return "ui-and-quality-of-life"
if path.startswith(("data/trainers", "data/wild", "src/data/pokemon/", "src/data/items", "src/data/moves", "graphics/pokemon/", "graphics/items/", "sound/")):
    return "game-content"
if path.startswith(("src/", "include/", "asm/", "constants/", "data/battle", "test/battle/")):
    return "gameplay-and-battle"
return "tooling-and-generated-output"
```

- [ ] **Step 3: Implement `render_inventory(base_ref, legacy_ref, records)`**

Attach the category to each record, sort changes by `path`, count categories with `collections.Counter`, and return JSON containing exactly `base_ref`, `legacy_ref`, `summary`, and `changes`, using `indent=2`, `sort_keys=True`, and a trailing newline.

- [ ] **Step 4: Implement the command-line entry point**

Use `argparse` flags `--base` (default `master`), `--legacy` (default `archive/master-pre-1.16.3`), and required `--output`. Run `git diff --name-status -z <base>...<legacy>` with `subprocess.run(check=True, stdout=subprocess.PIPE)`, then create the output parent directory and write the JSON in UTF-8.

- [ ] **Step 5: Run tests and commit**

Run: `python -m unittest tools/migration/tests/test_generate_legacy_inventory.py -v`

Expected: all parser, category, and render tests pass.

Run: `git add tools/migration/generate_legacy_inventory.py tools/migration/tests/test_generate_legacy_inventory.py; git commit -m "tools: add legacy migration inventory generator"`

Expected: one implementation commit.

### Task 3: Generate the evidence and complete the feature review

**Files:**

- Create: `docs/superpowers/inventories/2026-08-09-legacy-feature-inventory.json`
- Create: `docs/superpowers/inventories/2026-08-09-legacy-feature-review.md`
- Modify: `docs/superpowers/specs/2026-08-09-original-hack-1.16.3-migration-design.md`
- Test: generated JSON validation and review coverage check.

- [ ] **Step 1: Generate the inventory**

Run: `python tools/migration/generate_legacy_inventory.py --base master --legacy archive/master-pre-1.16.3 --output docs/superpowers/inventories/2026-08-09-legacy-feature-inventory.json`

Expected: non-empty `changes`, `base_ref` equal to `master`, and `legacy_ref` equal to `archive/master-pre-1.16.3`.

- [ ] **Step 2: Create the review with this exact table header**

```markdown
| Feature | Legacy paths | 1.16.3 equivalent or target paths | Decision | Phase | Acceptance evidence |
| --- | --- | --- | --- | --- | --- |
```

Use only `Direct transfer`, `Use upstream equivalent`, `Modern adaptation`, and `Custom replacement` in the Decision column. Every generated path must occur in exactly one review row; upstream equivalents must be used instead of duplicate legacy code.

- [ ] **Step 3: Link the evidence from the migration design**

Add after `## Current Evidence`:

```markdown
The generated [path inventory](../inventories/2026-08-09-legacy-feature-inventory.json) and [feature review](../inventories/2026-08-09-legacy-feature-review.md) are the authoritative migration checklist for this work.
```

- [ ] **Step 4: Validate and commit the evidence**

Run: `python -m json.tool docs/superpowers/inventories/2026-08-09-legacy-feature-inventory.json > $null; git diff --check; python -c "import json; print(len(json.load(open('docs/superpowers/inventories/2026-08-09-legacy-feature-inventory.json'))['changes']))"`

Expected: exit code 0, no whitespace errors, and a positive count.

Run: `git add docs/superpowers/inventories docs/superpowers/specs/2026-08-09-original-hack-1.16.3-migration-design.md; git commit -m "docs: inventory legacy hack features"`

Expected: one evidence commit.

## Plan self-review

- This plan implements the approved inventory phase and changes no ROM behavior.
- It keeps `master` untouched and derives all evidence from preserved local refs.
- Rename handling, deterministic output, category coverage, JSON validation, and feature-level review are explicit.
- A follow-up feature plan will be created only after this inventory supplies actual target paths and acceptance evidence.
