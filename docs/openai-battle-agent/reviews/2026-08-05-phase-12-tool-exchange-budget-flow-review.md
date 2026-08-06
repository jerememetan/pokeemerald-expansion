# Phase 12 Tool-Exchange Time Budget Flow Review

**Specification:** [Phase 12 specification](../specs/2026-08-05-phase-12-tool-exchange-budget.md)
**Implementation plan:** [Phase 12 implementation plan](../plans/2026-08-05-phase-12-tool-exchange-budget.md)

## Codebase context

`battle_agent_service.py` currently assigns `SERVICE_TIMEOUT_SECONDS = 20.0` to both `urlopen(..., timeout=...)` and the monotonic guard at the top of each `run_tool_agent` loop. The observed `get_battle_state`, `list_legal_actions`, then `produced no response` log path has no `rejected:` error, so it reaches the aggregate guard before the final `choose_actions` request. `handle_request_frame` already treats a `None` decision as no bridge response, allowing the ROM's established vanilla fallback. The focused unittest module already mocks `request_ollama` for tool-loop behavior.

## User flows

1. A model returns the normal `get_battle_state` and `list_legal_actions` calls slowly but still has time before 45 seconds. The service issues the final model call, validates `choose_actions`, and returns its atomic response to the unchanged bridge.
2. A single HTTP request exceeds 20 seconds. `urlopen` raises, `run_tool_agent` returns `None`, and the ROM uses vanilla AI without partial actions.
3. Several individually valid calls consume 45 seconds before `choose_actions`. The monotonic guard returns `None`; the ROM uses vanilla AI.
4. A model formats one call incorrectly. The existing correction message is attempted once, but it consumes the same 45-second exchange budget and still cannot emit a partial plan.

## Gaps resolved

| Severity | Gap | Resolution |
|---|---|---|
| Important | One constant ambiguously means both one request and a complete exchange. | Introduce separately named 20-second response and 45-second exchange constants; each call site uses exactly one. |
| Important | A larger exchange budget could accidentally permit a single hung HTTP request for 45 seconds. | Keep `urlopen` on the independent 20-second response timeout. |
| Important | A longer exchange could send an incomplete multi-battler plan. | Preserve the existing terminal `choose_actions` validation and `None` fallback path. |
| Minor | More waiting can feel slow to players. | The existing thinking status remains active; the 45-second ceiling remains finite and is documented. |

No critical or unresolved important gaps remain.
