# Phase 6B Specification: Global Trainer-Single Enablement

**Goal:** Enable the existing external AI opt-in flag for every trainer definition, so every battle already eligible for BAGB/3 uses the local agent.

**Scope:** Set `externalAi = TRUE` in every entry of `src/data/trainers.h`. Preserve the existing ROM eligibility gate unchanged: only opponent-side trainer singles enter external waiting. Unsupported doubles, multi battles, links, facilities, wild battles, forced actions, recharge, and multi-turn locks remain on vanilla AI.

**Out of scope:** BAGB/3 protocol changes, tool/service changes, items, double-battle agent support, trainer-party edits, or changes to battle mechanics.

**Boundaries:** Trainer data supplies only the opt-in bit. `BattleAgent_IsEligible` remains the ROM authority that rejects unsupported modes. Lua and the Python service continue to receive requests only when the ROM publishes them.

**Failure and fallback:** If the local service is absent, slow, malformed, or rejects an action, every newly enabled trainer retains the current 900-frame vanilla move fallback. An unsupported battle never starts an external request.

**Tests:** Add a trainer-single test using a previously untagged trainer and verify it publishes a request. Retain/extend an excluded-double test verifying no request. Run the full External AI suite and build a fresh ROM.

**Exit criteria:** A formerly untagged trainer single produces a connected BAGB request and stays playable with the service absent; an excluded double remains vanilla; all relevant tests and a fresh ROM build pass.

**Implementation plan:** [Phase 6B plan](../plans/2026-07-30-phase-6b-global-trainer-singles.md)
