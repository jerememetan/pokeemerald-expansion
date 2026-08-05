# Phase 10B Specification: Readable Field and Move State

**Roadmap:** [External AI Trainer Integration Plan](../integration-plan.md)

**Goal:** Make `get_field_state` and `get_battler_moves` explain existing mailbox facts with battle names an LLM can reason about.

**In scope:** Decode weather, terrain, supported field and side effects, move type, target category, and physical/special/status split. Keep numeric move effect values internally mapped to existing effect names.

**Out of scope:** Add no damage simulator, future-turn prediction, hidden-information inference, battle rule changes, new mailbox data, or response-contract change.

**Boundaries and contract:** ROM and Lua publish the same V4 bytes. Python returns readable JSON; unknown terrain/move target/split becomes `UNKNOWN`. `get_field_state` lists effects currently published by the V4 field/side bits, while battler tools remain responsible for Pokémon-local effects.

**Failure and fallback:** Translation cannot create an action. An unrecognized value is visible as `UNKNOWN`; bridge/service failure leaves the ROM's vanilla trainer AI as fallback.

**Tests:** Unit tests assert representative weather/field flags and all move category decoders. External AI integration tests verify unchanged protocol behavior.

**Exit criteria:** Full bridge tests and External AI checks pass, and field/move tools display names rather than raw numeric categories.
