# Legacy Trainer Teams Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the archived trainer rebalance with the upstream converter and safely merge every matching legacy `TRAINER_*` block into current `src/data/trainers.party`.

**Architecture:** `migration_scripts/1.9/convert_trainer_parties.py` remains the C-to-party converter. A small `tools/migration/merge_legacy_trainer_parties.py` command materializes the archived inputs in a temporary directory, invokes that converter, parses `.party` blocks by identifier, writes a candidate file and JSON report, and applies only with an explicit flag.

**Tech Stack:** Python 3 standard library, Git, upstream trainer-party migration script, trainerproc via the normal build.

**Design:** [Legacy Trainer Teams Migration Design](../specs/2026-08-09-legacy-trainer-teams-migration-design.md)

---

## File structure

- Create: `tools/migration/merge_legacy_trainer_parties.py` — non-destructive conversion, merge, report, and explicit apply command.
- Create: `docs/superpowers/inventories/2026-08-09-legacy-trainer-team-report.json` — generated candidate-report evidence.
- Modify: `src/data/trainers.party` — only after candidate/report review.
- Generated: `src/data/trainers.h` — regenerate through the current build, never hand-edit.

### Task 1: Build a non-destructive conversion and merge command

**Files:**

- Create: `tools/migration/merge_legacy_trainer_parties.py`

- [ ] **Step 1: Materialize the archived inputs and run the maintained converter**

Implement `git_show(path)` with `subprocess.run(['git', 'show', f'archive/master-pre-1.16.3:{path}'], check=True, text=True, capture_output=True)`. In `tempfile.TemporaryDirectory()`, write `src/data/trainers.h` and `src/data/trainer_parties.h`, then invoke:

```python
subprocess.run([
    sys.executable,
    'migration_scripts/1.9/convert_trainer_parties.py',
    str(legacy_trainers), str(legacy_parties), str(converted_party),
], check=True)
```

Expected: conversion occurs outside the worktree and produces a legacy-format `.party` candidate.

- [ ] **Step 2: Parse and validate party blocks by symbolic identifier**

Split a `.party` file at lines matching `^=== (TRAINER_[A-Z0-9_]+) ===$`, retaining each complete block verbatim. Reject duplicate identifiers, text before the first trainer block other than the header, and an empty parse. Return ordered identifiers and a `{identifier: block}` map.

- [ ] **Step 3: Write the candidate and report without mutating source**

For every current block identifier that also exists in converted legacy data, replace the current block with the converted legacy block. Retain all current-only blocks verbatim in their current order. Do not emit legacy-only blocks. Write the candidate only to required `--candidate` and report only to required `--report` paths.

Report JSON must include `legacy_count`, `current_count`, `converted_count`, ordered `converted_ids`, ordered `current_only_ids`, ordered `legacy_only_ids`, and `source_refs`.

- [ ] **Step 4: Add explicit apply protection**

Support `--apply`. Without it, reject any candidate path resolving to `src/data/trainers.party`. With it, require the candidate contents to have been freshly generated in the same invocation, then replace `src/data/trainers.party` and print its SHA-256 digest. Never invoke `git add`, `git commit`, or a build from the tool.

- [ ] **Step 5: Run the reporting command**

Run:

```powershell
python tools/migration/merge_legacy_trainer_parties.py --candidate build/legacy-trainers.party --report docs/superpowers/inventories/2026-08-09-legacy-trainer-team-report.json
python -m json.tool docs/superpowers/inventories/2026-08-09-legacy-trainer-team-report.json > $null
```

Expected: both exit 0; candidate is created; report counts are nonzero; `src/data/trainers.party` is unchanged.

### Task 2: Review and apply the converted teams

**Files:**

- Modify: `src/data/trainers.party`
- Create: `docs/superpowers/inventories/2026-08-09-legacy-trainer-team-report.json`

- [ ] **Step 1: Audit report boundaries**

Compare `converted_ids`, `current_only_ids`, and `legacy_only_ids` against current/archived identifiers. Inspect representative blocks for an early-route trainer, Gym Leader, rival, villain, Elite Four, Champion, Battle Frontier, Red, and Leaf.

Expected: every matching trainer ID is converted exactly once; current-only records remain; legacy-only records are explicitly deferred.

- [ ] **Step 2: Apply only after the candidate is accepted**

Run:

```powershell
python tools/migration/merge_legacy_trainer_parties.py --candidate build/legacy-trainers.party --report docs/superpowers/inventories/2026-08-09-legacy-trainer-team-report.json --apply
```

Expected: only matching trainer blocks in `src/data/trainers.party` change.

- [ ] **Step 3: Regenerate and compile**

Run the supported build in the configured development environment:

```powershell
make -j4
```

Expected: trainerproc regenerates `src/data/trainers.h`; build exits 0 with no unsupported species, move, item, or trainer-field error.

- [ ] **Step 4: Verify representative battles in-game**

Check party order, level, held item, and moves for one early-route trainer, each Gym tier, rival, villain, Elite Four/Champion, Battle Frontier, Red, and Leaf.

Expected: each sampled fight matches the archived team and 1.16.3-only trainers remain available.

- [ ] **Step 5: Commit the reviewed migration**

Run `git add tools/migration/merge_legacy_trainer_parties.py docs/superpowers/inventories/2026-08-09-legacy-trainer-team-report.json src/data/trainers.party src/data/trainers.h` followed by `git commit -m "feat: migrate legacy trainer teams"`.

Expected: one reviewable commit contains the converter, evidence, source authoring file, and regenerated output.

## Plan self-review

- Reuses the maintained upstream converter instead of reimplementing C parsing.
- Makes candidate generation non-destructive and applies only by explicit opt-in.
- Preserves every matching archived trainer ID while retaining current-only trainers.
- Requires an auditable exception report, current generator output, a build, and representative runtime checks.
