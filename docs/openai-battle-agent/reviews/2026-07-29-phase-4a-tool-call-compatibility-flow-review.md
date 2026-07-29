# Phase 4A qwen2.5-coder Tool-Call Compatibility Flow Review

**Specification:** [Phase 4A local Ollama tool agent](../specs/2026-07-29-phase-4a-local-ollama-tool-agent.md)  
**Implementation plan:** [Compatibility amendment](../plans/2026-07-29-phase-4a-tool-call-compatibility.md)

## Codebase grounding

`tools/mgba-bridge/battle_agent_service.py` already limits authority to
`TOOL_SCHEMAS`, validates the terminal action through `choose_action`, and
returns `None` for invalid model output. `bridge_protocol.py` accepts only a
fixed V2 response frame, while `src/battle_agent.c` independently validates
the request sequence, legal action index, move limitations, and normalized
target. A rejected service message therefore cannot alter battle mechanics.

The local `qwen2.5-coder:7b` verification returned an assistant content JSON
object such as `{"name":"list_legal_actions","arguments":{}}` rather than
Ollama's `message.tool_calls` array. No native service code currently parses
that shape.

## User flows

1. **Native tool-call happy path.** Ollama returns exactly one native function
   call, the service validates and runs the read-only tool, then accepts one
   legal `choose_action` call and emits a 13-byte V2 response.
2. **qwen compatibility happy path.** qwen emits exactly one JSON object in
   assistant content. The adapter converts it to the same internal name and
   argument pair as Flow 1, so all existing tool and terminal validation is
   reused.
3. **Malformed or untrusted content.** Text, Markdown, invalid JSON, a JSON
   array, extra object members, unknown names, or non-object arguments are
   rejected. The service writes no response and ROM fallback remains active.
4. **Deadline/failure.** An unavailable endpoint or a model call exceeding the
   existing 12-second service deadline returns no action. The existing 900th
   ROM wait-state visit uses vanilla AI.

## Gaps

### Critical

None. The fixed ROM/Lua frame and ROM validation are unchanged.

### Important

1. **Ambiguous assistant content could become accidental authority.** A loose
   parser could interpret ordinary explanatory text as a command. Resolution:
   parse only a complete JSON object with exactly `name` and `arguments`, then
   pass it through the existing allowlist and argument checks.
2. **Native and compatibility calls could diverge.** Resolution: normalize
   both forms to one internal tuple before dispatch; do not duplicate handlers
   or terminal validation.

### Minor

1. **First model load can exceed the service deadline.** The service safely
   falls back. Documentation tells the operator to verify/warm Ollama before a
   live demo; no deadline increase is safe for the approved 15-second ROM
   budget.

## Questions and defaults

1. Should arbitrary JSON-looking text be accepted? **No.** Only the exact
   two-key object is safe because it is structurally equivalent to one
   advertised tool call.
2. Should the service accept multiple calls in one assistant message? **No.**
   The existing one-call-at-a-time loop makes the 12-call budget and failure
   behavior deterministic.

## Recommended next steps

1. Add failing tests for exact content JSON acceptance and rejection of extra
   keys/text.
2. Add one normalization helper used by the existing tool loop.
3. Run the Python suite and a real warmed qwen exchange. Preserve native
   `tool_calls` behavior and all fallback paths.
