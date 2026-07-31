# Phase 6B Global Trainer-Singles Flow Review

**Specification:** [Phase 6B specification](../specs/2026-07-30-phase-6b-global-trainer-singles.md)

## Codebase grounding

`src/data/trainers.h` currently sets `externalAi = TRUE` for Calvin. Both `src/battle_agent.c` and `src/battle_ai_main.c` additionally require a trainer single and reject doubles, multi battles, links, facilities, wild battles, forced actions, recharge, and multi-turn locks.

## Flows

1. A normal trainer single now has `externalAi = TRUE`; the existing eligibility gate publishes BAGB/3 and the service selects a legal action or the ROM falls back to vanilla.
2. A double or other excluded battle may have `externalAi = TRUE`, but the existing eligibility gate rejects it before any request, leaving vanilla behavior unchanged.
3. An absent or invalid service response for any newly enabled trainer uses the saved vanilla move/target at the existing deadline.

## Gaps resolved

- **Important — all trainers includes unsupported modes.** Default: tag data may be global, but the existing eligibility gate remains the enforcement boundary; no double-battle request is published.
- **Important — every enabled trainer needs safe service failure.** Default: retain the existing timeout and fallback unchanged; this phase does not widen authority.
- **Minor — broad data diff reviewability.** Default: use a mechanical replacement limited to trainer initializers and verify Calvin plus one formerly untagged trainer in tests.

No critical gaps remain.
