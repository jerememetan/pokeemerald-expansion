# Phase 10A Specification: Readable Battler State

**Roadmap:** [External AI Trainer Integration Plan](../integration-plan.md)

**Goal:** Make `get_battle_state`, `get_battler`, and `get_party` return named, model-readable active and reserve Pokémon facts instead of opaque ROM identifiers.

**In scope:** Translate the existing mailbox values into named types, major status, volatile status, named stat changes from -6 to +6, species/ability/item names, and readable stats. The same decoded battler representation is used for active battlers and reserve-party entries.

**Out of scope:** No ROM mechanics, action legality, model prompts, mailbox layout, new status counters, Taunt/Encore/Disable state, or item usage changes. Taunt and related disable-structure facts are intentionally deferred because the V4 mailbox does not publish them; omitting them is safe because the ROM remains the legal-action authority.

**Boundaries and contract:** The ROM continues publishing V4 numeric snapshot fields. The local Python service translates only those published values before returning JSON tool results. The emulator bridge remains byte-transparent. Existing numeric move/action identifiers used internally are not changed.

**Failure and fallback:** Unknown enum values are returned as `UNKNOWN` (or omitted from a named list) and never manufacture a legal action. If the service fails, times out, or returns an invalid response, the ROM keeps its existing vanilla-AI fallback.

**Tests:** Unit tests cover type/status/stat decoding and representative volatile flags; source and External AI tests preserve the mailbox behavior.

**Exit criteria:** All bridge tests pass, `make -j16 check TESTS='External AI'` passes, and a smoke-tested model can read named statuses/types/stages while normal battle behavior and fallback are unchanged.
