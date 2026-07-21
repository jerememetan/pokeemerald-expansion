# Phase 1 Build and Test Evidence

**Recorded:** 2026-07-22  
**Scope:** Trainer opt-in and test-only ROM mock for `TRAINER_CALVIN_1`

## Build

The normal ROM was built in the user's WSL environment with all 16 available CPU threads (`make -j16`). The resulting `pokeemerald.gba` launched in mGBA for the Route 102 smoke test.

## Focused tests

`make -j16 check TESTS='External AI'` completed after GCC 14 compatibility fixes. The user reported that all focused external-AI tests passed. The suite covers accepted legal move selection and vanilla fallback for an absent, zero-PP, out-of-range, empty-slot, self-targeting, and non-opted-in response.

## Full tests

`make -j16 check` reported:

- Tests passed: 1,122
- Tests failed: 44
- Tests known failing: 24
- Tests to-do: 98
- Assumptions failed: 34
- Tests total: 1,322

The 44 failures are cross-cutting existing mechanics (for example Dynamax, items, terrain, abilities, and unrelated vanilla AI behavior), not the `External AI` test group. The project owner confirmed they are accepted existing failures. No clean-baseline rerun was performed; this classification relies on that confirmation together with the Phase 1 scope review and passing focused suite.

## Route 102 smoke test

The user fought Youngster Calvin on Route 102 in mGBA without a Lua script or external service and confirmed that the battle behaved normally.

## Fallback result

In a normal ROM, the Phase 1 helper has no mock response and returns without changing the precomputed vanilla AI action or target. The manual Calvin battle confirms there is no wait, crash, or external-process requirement.

## Known limitations

The mock exists only under `TESTING`; there is no mGBA bridge, mailbox, local service, or model call. Target choice remains engine-owned. Switching, items, doubles, and wider trainer rollout remain deferred.

## Linked documents

- [Phase 1 specification](../specs/2026-07-18-phase-1-trainer-opt-in-and-rom-mock.md)
- [Phase 1 flow review](2026-07-18-phase-1-trainer-opt-in-and-rom-mock-flow-review.md)
- [Phase 1 implementation plan](../plans/2026-07-18-phase-1-trainer-opt-in-and-rom-mock.md)
