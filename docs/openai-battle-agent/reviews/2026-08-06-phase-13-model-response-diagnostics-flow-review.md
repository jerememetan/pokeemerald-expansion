# Phase 13 Model-Response Diagnostics Flow Review

**Specification:** [Phase 13 specification](../specs/2026-08-06-phase-13-model-response-diagnostics.md)
**Implementation plan:** [Phase 13 implementation plan](../plans/2026-08-06-phase-13-model-response-diagnostics.md)

## Codebase context

`extract_tool_call` returns only a call or `None`. `run_tool_agent` logs `retrying malformed tool call` on its first `None`, then silently returns `None` on a second one. The outer loop also returns `None` without a deadline log. `handle_request_frame` consequently emits the same `produced no response` line for all of these cases. Parsed `choose_actions` already reaches `choose_actions`, whose `ToolError` log identifies invalid action-pair shape. The bridge accepts a response only after an `AgentDecision` is constructed, so logging-only changes cannot affect ROM action selection.

## User flows

1. Ollama emits invalid JSON, multiple calls, or invalid native-call structure. The service logs a specific parser category and bounded preview, sends the existing one retry, then either proceeds normally or logs the second malformed category and falls back.
2. Ollama emits a syntactically parsed but unsupported name/argument combination. The service logs that exact name and sorted argument keys, then falls back.
3. Valid individual calls consume the 45-second exchange budget. The service logs the measured elapsed duration, then falls back.
4. Ollama emits a valid terminal action plan. No diagnostic log is emitted; current action validation, audit, bridge response, and ROM behavior are unchanged.

## Gaps resolved

| Severity | Gap | Resolution |
|---|---|---|
| Important | `None` collapses malformed syntax, unsupported calls, and elapsed budget into one ambiguous final log. | Classify the parser's rejected response and log the outer deadline before the unchanged `None` return. |
| Important | Full assistant content can be verbose or contain echoed game data. | Log only a 240-character, newline-normalized `repr` preview from the response object. |
| Important | Diagnostics could accidentally make invalid calls accepted. | Reuse the parser result for control flow; all new helpers are observational only. |
| Minor | Native function name may be unavailable when the structure is invalid. | State structural category rather than guessing a tool name. |

No critical or unresolved important gaps remain.
