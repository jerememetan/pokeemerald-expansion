# Archived Caps Implementation Plan

Approved continuation of faithful restoration; use subagent-driven-development.
Source specification: docs/superpowers/specs/2026-10-04-legacy-caps-design.md.
Archive: f5e81e85df6fe40ae490bf7268d0186d7f0426ed.

## Task 1: Regression tests, then runtime restoration

Files: src/caps.c, include/config/caps.h,
tools/migration/tests/test_legacy_caps.py. No other runtime edits.

- [x] Add actual-C fixtures before production edits. Strip only includes from
  src/caps.c, supply minimal Pokemon/flag/variable stubs, and compile with the
  real config header using native cc, -std=c11 -Wall -Wextra -Werror.
  Variants can override configuration after including the header. Missing
  compiler must fail, not silently skip tests. Disposable outputs only.
- [x] Derive the cap and relative-factor expectations from the pinned archive
  as well as the explicit approved spec; do not duplicate only the new code.
- [x] Run red with WSL python3 -m unittest tools.migration.tests.test_legacy_caps -v.
- [x] Enable SOFT and FLAG_LIST, restore all ten flag/cap pairs, and add one
  private helper for party scaling. Retain denominator and first-empty rules.
- [x] In the existing hook, combine factors using u64 intermediates:
  below cap exp * hundredths / 100; at cap exp * hundredths * 3 / 1000;
  above cap exp * hundredths / 1000000. All flags set means no cap reduction.
  Saturate to maximum u32; empty party gets neutral scaling. Preserve NONE,
  HARD, variable, optional EXP-up, and EV behaviour as specified.
- [x] Test all cap transitions, out-of-order flags, all flags set, cap-1/cap/
  cap+1, all 27 relative indices and clamp extremes, zero/tiny/large inputs,
  combined rounding and saturation. Include [40,40,20] -> team 26,
  [21,21,15] -> team 19, first-empty slots and eggs/fainted membership.
- [x] Check the existing Lilycove flag chain and separate participation/share
  hook placement. No new battle hook or object-removal mutation.
- [x] Run green and git diff --check. Obtain spec review, then quality review;
  address findings and rereview.

## Task 2: Verify and checkpoint both independent units

- [x] Rerun the whole focused migration suite, including berry and cap tests.
- [x] Make an exact native source snapshot and run tools, generated sources,
  and a full ROM compile. Record source parity and ROM size/SHA-256.
- [x] Commit reviewed/verified berry and cap runtime units separately with
  their tests; stage only explicit allowlists, no generated artifacts/saves.
- [x] Update the dated progress note, mark these units implemented, record
  manual acceptance pending, and retain outstanding unrelated migration work.
- [x] Finish this requested berry/cap continuation without claiming the whole
  archived hack or in-game playthrough is complete.
