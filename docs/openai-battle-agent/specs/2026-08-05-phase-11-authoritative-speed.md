# Phase 11 Specification: Authoritative Speed Context

**Roadmap:** [External AI Trainer Integration Plan](../integration-plan.md)
**Flow review:** [Phase 11 flow review](../reviews/2026-08-05-phase-11-authoritative-speed-flow-review.md)
**Implementation plan:** [Phase 11 implementation plan](../plans/2026-08-05-phase-11-authoritative-speed.md)

**Goal:** Replace Python's raw-Speed ordering approximation with the ROM's effective active speed calculated by `GetBattlerTotalSpeedStat`.

**Scope:** Populate the existing active-battler `speed` mailbox word with `GetBattlerTotalSpeedStat`; no mailbox version, size, or offset changes are required. `compare_speed` sorts that effective speed, reverses its ordinary order under the published Trick Room bit, and reports the field condition. The helper includes active-battle modifiers such as stat stages, paralysis, Tailwind, ability, held-item, and other ROM-defined effects. Priority remains action-specific and is not predicted as one global order. Reserve-party Speed remains the stored party stat because the reserve is not an active battler.

**Out of scope:** Predicting move priority, equal-speed RNG, or non-active Pokémon's hypothetical switch-in speed.

**Boundaries and failure behavior:** The ROM is the authority for effective speed; Python only presents its published active values and the existing field bit. Action legality, selection, mailbox response, timeout, and vanilla fallback are unchanged. Unknown/missing external service behavior remains vanilla fallback.

**Tests and exit criteria:** Source test asserts `BattleAgent_CopySnapshot` calls the ROM helper. Python test proves Trick Room reversal. Full bridge tests, `make -j16 check TESTS='External AI'`, and a normal ROM build must pass. Manual smoke tests verify Tailwind/paralysis/stage and Trick Room tool output while singles/doubles and fallback remain intact.
