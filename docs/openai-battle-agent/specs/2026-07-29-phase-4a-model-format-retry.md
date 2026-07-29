# Phase 4A Sub-phase Specification: Bounded Local-Model Format Retry

**Status:** Drafted from live mGBA/Ollama evidence; flow review required before implementation  
**Parent phase:** [Phase 4A local Ollama tool agent](2026-07-29-phase-4a-local-ollama-tool-agent.md)  
**Flow review:** [Model-format retry flow review](../reviews/2026-07-29-phase-4a-model-format-retry-flow-review.md)  
**Implementation plan:** [Model-format retry plan](../plans/2026-07-29-phase-4a-model-format-retry.md)
**Evidence:** [Model-format retry evidence](../reviews/2026-07-29-phase-4a-model-format-retry-evidence.md)

## Goal

Give the local `qwen2.5-coder:7b` agent one bounded opportunity to correct a malformed assistant tool-call reply. This addresses observed replies such as `{"name": get_battle_state, "arguments": {}}`, which are not valid JSON and therefore cannot safely be interpreted as a tool command. The retry must preserve the existing strict parser, legal-action authority, 12-second service deadline, and ROM vanilla-AI fallback.

## Scope

### In scope

- Only `tools/mgba-bridge/battle_agent_service.py` and its Python tests.
- A format-correction system message after one malformed or text-only assistant reply (`extract_tool_call(...) is None`).
- At most one format retry for each agent run. The retry consumes the existing bounded model-call loop and remaining monotonic deadline.
- The existing exact native `tool_calls` and exact two-key JSON-content compatibility shapes.
- Diagnostics that distinguish a rejected malformed model reply from an unavailable Ollama endpoint while retaining no battle-state persistence.

### Out of scope

- Relaxing `extract_tool_call`, accepting pseudo-JSON, Markdown, unknown tool names, extra keys, arrays, or non-object arguments.
- Adding tools, shell/file/network/emulator authority, model settings, cloud providers, trainer scope, move selection rules, or ROM/Lua protocol changes.
- Retrying HTTP failures, timeout failures, invalid tool arguments, unknown tools, or invalid/repeated terminal choices.

## Boundaries and data contract

The ROM still publishes only its fixed 425-byte V2 request and accepts only a legal action index after its independent revalidation. Lua still forwards one fixed frame and commits a fixed 13-byte response. The Python service remains the only changed component.

The accepted model-command contract is unchanged: either one native Ollama function call or a complete JSON object with exactly `name` and `arguments`, where `name` is advertised and `arguments` passes the existing per-tool checks. A retry does not transform, repair, or execute the malformed text; it asks the model for a fresh response and passes that new response through the same parser.

## Flow and failure behavior

1. The service decodes a valid V2 request and requests one tool call from Ollama.
2. If the reply parses strictly, the existing tool dispatch flow continues unchanged.
3. If it does not parse and no earlier format retry was used, the service appends a correction message stating that the previous reply was unusable and that the next reply must be one supported tool call. It requests Ollama again only while the existing 12-second deadline remains.
4. If the corrected reply parses strictly, dispatch and `choose_action` validation proceed exactly as today.
5. A second malformed reply, any disallowed command, an HTTP/timeout error, a legal-action validation failure, or deadline exhaustion returns no bridge response. The ROM uses its saved vanilla action at the existing deadline.

## Tests and measurable exit criteria

1. A failing-then-passing service test proves one malformed assistant reply followed by a valid exact JSON-content tool call and a legal `choose_action` returns the legal action.
2. Tests prove two malformed replies, an invalid tool argument, a text-only reply after the retry, and an Ollama `OSError` still return no action.
3. Tests prove the retry does not exceed `MAX_TOOL_CALLS` model attempts or the monotonic 12-second deadline.
4. `py -3 -m unittest discover -s tools/mgba-bridge/tests -v` passes.
5. Manual Windows evidence shows a correctly framed Calvin request reaches the service, at least one read-only tool is logged, a legal response is written by Lua before the ROM deadline, and Calvin performs the chosen legal move. Service/model failure must still fall back to vanilla AI.

## Links

- [Parent Phase 4A specification](2026-07-29-phase-4a-local-ollama-tool-agent.md)
- [Flow review](../reviews/2026-07-29-phase-4a-model-format-retry-flow-review.md)
- [Implementation plan](../plans/2026-07-29-phase-4a-model-format-retry.md)
