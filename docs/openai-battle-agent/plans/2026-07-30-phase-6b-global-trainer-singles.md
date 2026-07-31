# Phase 6B Global Trainer-Singles Implementation Plan

**Goal:** Tag every trainer as `externalAi` while preserving the ROM's trainer-single eligibility gate.

**Architecture:** Data enables trainers; the existing ROM gate decides whether a battle is supported. BAGB/3, Lua, and the Python service are unchanged.

**Specification:** [Phase 6B specification](../specs/2026-07-30-phase-6b-global-trainer-singles.md)

**Flow review:** [Phase 6B flow review](../reviews/2026-07-30-phase-6b-global-trainer-singles-flow-review.md)

## Task 1: Prove coverage boundaries test-first

- [ ] Add a failing `test/battle/ai.c` case with a formerly untagged trainer single that expects `BattleAgent_TryPublishRequest` to succeed.
- [ ] Add or retain a double-battle case that expects request publication to fail despite the trainer tag.
- [ ] Run `make -j16 check TESTS='External AI'`; expected the new trainer-single assertion fails before the data edit.

## Task 2: Apply the mechanical data change

- [ ] Modify only `src/data/trainers.h`, changing each trainer initializer's `externalAi` bit to `TRUE`.
- [ ] Do not alter `BattleAgent_IsEligible`, protocol structures, service tools, or battle controller behavior.
- [ ] Re-run `make -j16 check TESTS='External AI'`; expected all External AI tests pass.

## Task 3: Verify and document

- [ ] Run `py -3 -m unittest discover -s tools\\mgba-bridge\\tests -q`, `make -j16`, and `git diff --check`; expected all pass and a fresh `pokeemerald.gba` is produced.
- [ ] Smoke-test a formerly untagged trainer single with the service connected and absent, then confirm an excluded double stays vanilla.
- [ ] Update the roadmap and record verification evidence.

## Self-review

The plan changes only trainer data, relies on existing mode and fallback guards, tests both newly enabled and excluded paths, and excludes double-battle support and protocol changes.
