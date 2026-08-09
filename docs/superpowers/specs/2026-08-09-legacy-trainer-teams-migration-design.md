# Legacy Trainer Teams Migration Design

## Goal

Recreate the archived trainer-team rebalance on Expansion 1.16.3 by converting every legacy trainer that has a matching current trainer identifier into the current `src/data/trainers.party` format.

## Policy

For every trainer identifier present in both `archive/master-pre-1.16.3` and 1.16.3, the archived trainer record is authoritative. Preserve its team composition, party order, levels, IVs, EVs, abilities, held items, moves, trainer class, portrait, gender, music, battle type, AI flags, and trainer items wherever the current format supports them.

Trainers present only in 1.16.3 remain unchanged. Legacy-only trainers are reported explicitly and are added only through separately reviewed map/content work; they are not silently discarded or assigned a guessed current ID.

## Scope

In scope:

- Reuse the upstream `migration_scripts/1.9/convert_trainer_parties.py` conversion tool against archived `src/data/trainer_parties.h` and `src/data/trainers.h` materialized into a temporary directory.
- A small reporting/merge tool that reads the converter output and current `src/data/trainers.party` by symbolic identifier.
- Parsing current `src/data/trainers.party` into trainer blocks keyed by `TRAINER_*` identifier.
- Producing a deterministic candidate current-format file plus a machine-readable report of converted, current-only, legacy-only, and unsupported records.
- Replacing matching current trainer blocks only after the report is reviewed.
- Regenerating `src/data/trainers.h` through the current trainer processor and compiling the ROM.

Out of scope:

- Copying legacy generated headers or numeric trainer IDs.
- Changing current-only trainer records, map scripts, trainer placement, trainer count, or save allocation as part of the bulk conversion.
- Guessing mappings for renamed IDs, unavailable species/moves/items, or old engine-only fields.

## Architecture

The established upstream `migration_scripts/1.9/convert_trainer_parties.py` performs the old C trainer-structure to competitive `.party` conversion. A one-off Python standard-library command under `tools/migration/` resolves the two archived source files with `git show archive/master-pre-1.16.3:<path>`, writes them only to a temporary directory, invokes that converter, then parses its output and current `src/data/trainers.party`. It maps records by symbolic `TRAINER_*` name rather than numeric ID and writes candidate output only to an explicitly named path. It never overwrites `src/data/trainers.party` by default.

The report includes exact counts and identifiers for: converted matching trainers, current-only trainers retained unchanged, legacy-only trainers needing separate treatment, and every unsupported field/value. Conversion fails rather than emitting a partial trainer block when an archived value cannot be represented in current syntax.

After report review, a separate explicit apply mode replaces only converted matching blocks. The normal `make` dependency regenerates `src/data/trainers.h`; it is never edited by hand.

## Failure and Fallback

- Parse ambiguity, duplicate identifiers, unsupported values, or count mismatch stops conversion with a nonzero exit and leaves the current trainer file untouched.
- The candidate-output path must differ from `src/data/trainers.party`; the tool rejects an in-place output unless an explicit apply flag is supplied.
- A failed generator/build reverts the uncommitted application change; the clean 1.16.3 trainer file remains the fallback.

## Validation and Exit Criteria

1. Every legacy/current identifier intersection has exactly one converted candidate block; no matching legacy team is omitted.
2. Every current-only trainer is byte-for-byte retained in the candidate output.
3. Every legacy-only or unsupported record appears in the report with a reason; none is silently changed.
4. Spot comparisons cover early-route, Gym, rival, villain, Elite Four, Champion, Battle Frontier, Red, and Leaf trainers.
5. Generated `src/data/trainers.h` and the supported ROM build succeed after reviewed application.
6. Targeted in-game battles confirm representative team order, level, held item, and moves.

## Evidence

- Upstream converter: `migration_scripts/1.9/convert_trainer_parties.py`.
- Legacy data: `archive/master-pre-1.16.3:src/data/trainer_parties.h`, `archive/master-pre-1.16.3:src/data/trainers.h`, and `archive/master-pre-1.16.3:include/constants/opponents.h`.
- Current authoring source: `src/data/trainers.party`; derived output: `src/data/trainers.h`.
- Baseline counts observed on 2026-08-09: 859 legacy party arrays and 855 current trainer blocks.
- Parent migration design: `2026-08-09-original-hack-1.16.3-migration-design.md`.
