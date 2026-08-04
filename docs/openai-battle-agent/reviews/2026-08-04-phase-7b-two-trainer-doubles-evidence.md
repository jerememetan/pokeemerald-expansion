# Phase 7B Two-Trainer Doubles Evidence

**Date:** 2026-08-04
**Specification:** [Phase 7B specification](../specs/2026-08-03-phase-7b-two-trainer-doubles.md)
**Flow review:** [Phase 7B flow review](2026-08-03-phase-7b-two-trainer-doubles-flow-review.md)
**Implementation plan:** [Phase 7B plan](../plans/2026-08-04-phase-7b-two-trainer-doubles.md)

## Automated verification

| Command | Result |
| --- | --- |
| `make -j16 check TESTS='External AI'` in WSL | Passed: 32 tests. Coverage included existing trainer singles, the Phase 7A one-trainer double request and double-switch paths, no-response fallback, thinking status, and Phase 7B atomic move pairs, move-plus-switch, and two owner-correct switches. |
| `py -3 -m unittest discover -s tools\mgba-bridge\tests -q` in PowerShell | Passed: 74 tests. Coverage included BAGB/5 request parsing, Lua-source contract checks, atomic service responses, and owner-labelled `get_party` output. |
| `git diff --check` | Passed with no whitespace errors. |

The normal ROM was rebuilt after closing mGBA, and the BAGB/5 mailbox Lua
configuration was regenerated from the resulting ELF.

## Manual smoke evidence

The user tested the rebuilt ROM with the local mGBA bridge and service and
reported these working scenarios:

1. A two-independent-trainer encounter that becomes a double battle.
2. A normal intentional one-trainer double battle.
3. A normal trainer single battle.

This confirms the Phase 7B path uses the same service while retaining the
previously working single and Phase 7A double behavior. The normal bridge
fallback remains the preserved ROM behavior when no valid external response is
available.

## Exit-criteria assessment

- One atomic external decision controls both opponents in a two-trainer double.
- Published party data labels slots 0–2 as opponent-left and 3–5 as
  opponent-right; legal switches remain actor-scoped ROM actions.
- Automated ROM and Python coverage passes.
- The rebuilt normal ROM was manually smoke-tested for two-trainer doubles,
  one-trainer doubles, and singles.
