# Phase 10B Readable Field and Move State Flow Review

**Specification reviewed:** [Phase 10B specification](../specs/2026-08-05-phase-10b-readable-field-and-move-state.md)

## Repository context

`get_field_state` reads V4 weather/terrain/field/side words at fixed Python offsets. `get_battler_moves` already reads each published move. Both are read-only tool paths and the ROM continues validating all choices.

## Flows

1. The model inspects field effects or a move; Python returns named facts.
2. The model uses those facts with `list_legal_actions` and eventually calls `choose_actions`.
3. A bit/category not known to Python is labelled unknown, not assumed absent.
4. Any invalid, late, absent, or malformed external response reaches the existing vanilla fallback.

## Gaps resolved

| Severity | Gap | Resolution |
|---|---|---|
| Important | Numeric target flags are ambiguous to the model. | Publish exact named target categories. |
| Important | Field effects and Pokémon-local volatile effects could be conflated. | Keep field/side effects in `get_field_state`; local volatile effects are Phase 10A battler data. |
| Minor | Some new ROM constants may not have a Python label. | Return `UNKNOWN`, retaining ROM action validation. |

No critical gaps remain.
