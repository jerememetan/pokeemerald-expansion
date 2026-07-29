# Phase 4A qwen2.5-coder Tool-Call Compatibility Implementation Plan

**Goal:** Accept qwen2.5-coder's exact local JSON tool-call content shape without widening the agent's authority.

**Architecture:** Normalize either one native Ollama function call or one exact
assistant-content JSON object into `(name, arguments)`. Reuse the existing
allowlist, per-tool argument checks, tool budget, terminal action validation,
and V2 response formatter.

**Files:**

- Modify: `tools/mgba-bridge/battle_agent_service.py`
- Modify: `tools/mgba-bridge/tests/test_battle_agent_service.py`
- Modify: `docs/openai-battle-agent/specs/2026-07-29-phase-4a-local-ollama-tool-agent.md`
- Create: this plan and its [flow review](../reviews/2026-07-29-phase-4a-tool-call-compatibility-flow-review.md)

## Steps

1. Add a failing Python test where the first mock Ollama message has content
   `{"name":"list_legal_actions","arguments":{}}` and the second has a
   valid native `choose_action(1)` call; expect action index `1`.
2. Add failing tests for content with extra keys, text, and non-object
   `arguments`; expect `run_tool_agent` to return `None`.
3. Add `extract_tool_call(message)` in `battle_agent_service.py`. It accepts
   exactly one native function call or parses `message["content"]` with
   `json.loads`, requiring the exact key set `{name, arguments}`, a string
   name, and a dictionary arguments value. It returns `None` otherwise.
4. Replace the inline native-only extraction in `run_tool_agent` with the
   helper. Keep the existing dispatch, deadline, and `choose_action` checks
   unchanged.
5. Run `py -3 -m unittest discover -s tools/mgba-bridge/tests -v`; expected:
   every test passes. Run one warmed local qwen request; expected: it performs
   one or more read-only tool calls and returns a legal action before the
   12-second service deadline.

## Self-review

The amendment does not modify the binary protocol, Lua bridge, ROM timeout,
tool catalog, action validation, or trainer scope. It adds no new model tool,
filesystem access, network destination, or move/target authority. Every
alternate content message has the same strict name and arguments validation as
native Ollama calls.
