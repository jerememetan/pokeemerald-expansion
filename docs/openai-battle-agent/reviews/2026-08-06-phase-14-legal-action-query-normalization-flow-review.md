# Phase 14 Legal-Action Query Normalization Flow Review

**Specification:** [Phase 14 specification](../specs/2026-08-06-phase-14-legal-action-query-normalization.md)
**Implementation plan:** [Phase 14 implementation plan](../plans/2026-08-06-phase-14-legal-action-query-normalization.md)

## Codebase context

The observed service log shows repeated `list_legal_actions` fallbacks with keys `battler_id` and `controlled_battlers`. The current model-facing schema advertises an optional `battler_id`, while `run_tool_agent` accepts it only when its value is an action-map key. The no-argument call already returns every controlled opponent's legal actions, and `choose_actions` independently validates every final actor/action pair. Therefore returning the no-argument result for any list-query arguments exposes no additional data or capability.

## User flows

1. Model calls `list_legal_actions` with `{}`. Service returns all controlled actors' legal actions, as today.
2. Model calls it with a wrong `battler_id` or invented `controlled_battlers`. Service logs the normalized keys, returns the same all-actor list, and permits the next model turn to make a terminal legal selection.
3. Model makes an invalid terminal choice. Existing `choose_actions` validation rejects it and ROM falls back.
4. Any other tool has wrong arguments. Existing diagnostics and fallback remain unchanged.

## Gaps resolved

| Severity | Gap | Resolution |
|---|---|---|
| Important | The schema's optional scope invites Qwen to pass battler identifiers that vary by battle side. | Remove the optional property from the model-facing schema and always provide the complete list. |
| Important | Accepting arguments might accidentally bypass action legality. | Normalize only this read-only query; retain the exact final `choose_actions` validation. |
| Minor | Existing direct callers may rely on the internal scoped helper. | Preserve the function's optional scoped parameter; change only the model dispatch. |

No critical or unresolved important gaps remain.
