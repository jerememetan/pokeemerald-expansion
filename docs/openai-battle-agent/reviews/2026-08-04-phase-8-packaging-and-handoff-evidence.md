# Phase 8 Packaging and Handoff Evidence

**Status:** Automated verification complete; fresh manual walkthrough pending
**Specification:** [Phase 8 specification](../specs/2026-08-04-phase-8-packaging-and-handoff.md)
**Flow review:** [Phase 8 flow review](2026-08-04-phase-8-packaging-and-handoff-flow-review.md)
**Implementation plan:** [Phase 8 implementation plan](../plans/2026-08-04-phase-8-packaging-and-handoff.md)
**Handoff guide:** [Local AI Trainer Handoff](../phase-8-handoff.md)

## Documentation scope check

Phase 8 added the high-level handoff guide and aligned the bridge runtime
README. No ROM, Lua, protocol, Python service, model, trainer data, test, or
battle-mechanics source was changed by this phase. The documentation names the
active BAGB/5 runtime, `choose_actions`, the fixed `AI is thinking..` status,
all three supported trainer scopes, and the existing vanilla fallback.

## Fresh automated evidence (2026-08-04)

| Command | Result |
| --- | --- |
| PowerShell: `py -3 -m unittest discover -s tools\mgba-bridge\tests -q` | Passed: **74 tests** in 0.056 seconds; no failures or errors. |
| Ubuntu WSL: `make -j16 check TESTS='External AI'` | Passed: **32 External AI tests**. The command exited 0. The established unrelated `ASSUME failed` diagnostics appeared but no External AI test failed. |
| Ubuntu WSL, with no running mGBA process: `make -j16` | Passed: a fresh `pokeemerald.gba` was produced. |
| Ubuntu WSL: `python3 tools/mgba-bridge/generate_mailbox_config.py --elf pokeemerald.elf` | Passed after the fresh normal build. |
| Ubuntu WSL: `git check-ignore tools/mgba-bridge/generated/mailbox_address.lua` | Passed: printed `tools/mgba-bridge/generated/mailbox_address.lua`. |
| PowerShell: `git diff --check` | Passed: no whitespace error output. |

The mGBA process check returned no process before the normal build, so no ROM
file lock was present for this build evidence.

## Manual walkthrough still required for Phase 8 exit

Run the guide's live workflow against this fresh ROM:

1. Start the PowerShell service, open mGBA, load Lua once, and verify one
   connected trainer-single decision.
2. Verify one intentional one-trainer double decision and one two-trainer
   double decision. The two-trainer audit must select actions for both opponent
   battlers.
3. Stop or omit the service on a voluntary opponent turn. Confirm the lower
   panel shows the fixed `AI is thinking..` text during the bounded wait,
   clears automatically, and lets saved vanilla trainer AI continue the
   battle.

Earlier Phase 7B evidence already records successful manual verification for
all three battle scopes. This Phase 8 record deliberately leaves the new
handoff-guide walkthrough pending until it is repeated and observed.
