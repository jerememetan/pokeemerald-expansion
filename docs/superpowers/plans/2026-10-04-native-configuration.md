# Native Configuration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development.
> Steps use checkbox syntax for tracking.

**Goal:** Restore 21 proven choices through native settings/constants.

**Architecture:** Only explicit current macros/constants and one unused
permanent flag change; native item/Pokemon/battle implementations remain.

**Tech Stack:** C headers, Python unittest, native WSL cc, Git, Make.

---

Full specification: docs/superpowers/specs/2026-10-04-native-configuration-design.md.

## Task 1: Verify old intent, then native settings

Runtime allowlist: include/config/battle.h, item.h, overworld.h,
wild_encounter.h, debug.h, pokedex_plus_hgss.h; include/constants/pokemon.h,
include/constants/flags.h. New test: tools/migration/tests/test_native_configuration.py.

- [x] Create tests asserting the full 21-entry map in the specification, with
  archive values independently read from pinned sources. Note renamed old
  double-wild/debug macros and relocated HGSS option. Ensure old Pokemon
  and species-enabled configs have no authored macro deltas against1565171235.
- [x] Compile actual current config headers with narrow definition stubs,
  and extract/compile actual constants conditional blocks for SHINY_ODDS and
  legendary IV count. Confirm the disabled IV branch stays zero and debug
  stays off whether DISABLED_ON_RELEASE is 0 or 1.
- [x] Extract actual ItemUseOutOfBattle_ExpShare and IsGen6ExpShareEnabled
  bodies; compile with real current item settings and narrow engine stubs.
  Tests must verify receipt alone does not enable EXP All, then item use
  toggles the permanent flag off/on/off, messages in bag/registered modes,
  and no mutation of FLAG_RECEIVED_EXP_SHARE. Test real getter with type
  below GEN_6 too. Missing cc is a failure, not silently skipped.
- [x] Run red: WSL python3 -m unittest tools.migration.tests.test_native_configuration -v.
  Expect configuration assertions and native EXP All behaviour to fail, not
  compiler errors caused by an undeclared new flag.
- [x] Apply only the 21 macro values from the specification. Rename unused
  FLAG_UNUSED_0x023 to FLAG_TOGGLE_EXPALL, retaining 0x23 and unrelated flags.
  Update the obsolete EXP Share config comment to describe its allocated
  permanent toggle. No grants/default-on script, no copied item table.
- [x] Run green, checking native Key Item pocket/field-use binding, reusable
  TM importance and held-evolution-item action wiring. Verify exact macro
  allowlist against pre-unit source to catch extra changes. git diff --check.
- [x] Independent spec review then quality review; fix and rereview findings.

## Task 2: Shared validation and checkpoint

- [x] Run all focused migration modules, including completed HM and prior
  berry/cap/map units. Windows Python for importer suite; WSL Python/cc for
  actual-C fixtures. Do not claim stock battle-suite compatibility.
- [x] Build exact runtime sources in a persistent native validation copy and
  compare each runtime overlay to workspace bytes. Record final ROM hash.
- [x] Commit native configuration separately from HM sources/tests; explicit
  allowlists only, no generated files or save rewrites.
- [x] Document 21 restored choices, already-equivalent systems, friendship/
  species/Toxic Boost/bag-policy exclusions, manual acceptance and remaining
  UI work. Do not label all Pokemon customization complete via GEN_LATEST.
