# Phase 14 Specification: Legal-Action Query Normalization

**Roadmap:** [External AI Trainer Integration Plan](../integration-plan.md)
**Flow review:** [Phase 14 flow review](../reviews/2026-08-06-phase-14-legal-action-query-normalization-flow-review.md)
**Implementation plan:** [Phase 14 implementation plan](../plans/2026-08-06-phase-14-legal-action-query-normalization.md)

**Goal:** Prevent harmless `list_legal_actions` argument mistakes from discarding an otherwise recoverable model decision.

**In scope:** Present `list_legal_actions` to the model as a no-argument tool that always returns all ROM-authorized actions grouped by controlled battler. If a model still supplies any arguments—such as `battler_id` or hallucinated `controlled_battlers`—the Python service logs that it normalized the query and returns the same complete action list. The existing internal helper may retain its scoped argument for direct tests and non-model callers.

**Out of scope:** Relaxing any other tool's parameters, changing `choose_actions` validation, accepting unlisted moves/targets/switches, changing prompts other than the affected tool description, changing retries/time budgets, mailbox protocol, mGBA Lua, ROM behavior, or trainer AI fallback.

**Boundaries and data contract:** Python tool-schema and dispatch behavior only. The normalized result is exactly the no-argument `list_legal_actions(actions_by_battler, payload=payload)` result; no player actions, private data, or new JSON fields are exposed. The terminal action still must be an existing legal entry for every controlled battler.

**Failure and fallback behavior:** Invalid `list_legal_actions` arguments no longer cause fallback because the complete read-only list is safe and already available without arguments. Any later malformed response, unsupported tool, timeout, missing decision, or invalid `choose_actions` follows the current diagnostics and vanilla fallback. No partial response is sent to the ROM.

**Tests and measurable exit criteria:** Tests must assert the model-facing schema exposes no `list_legal_actions` properties, and that both `{\"battler_id\": 0}` and `{\"controlled_battlers\": [1, 3]}` normalize to a successful complete-list/terminal-choice flow. Existing valid empty-argument and internal scoped-query tests must stay green. `py -3 -m unittest discover -s tools/mgba-bridge/tests -q` passes. Manual single and both double-battle smoke tests show normalized-query logs followed by model decisions; invalid terminal choices still fall back.
