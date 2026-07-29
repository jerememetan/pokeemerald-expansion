# Phase 4A Evidence: Transport Corrections and Bounded Model-Format Retry

**Date:** 2026-07-29  
**Scope:** Calvin-only Phase 4A local bridge/service reliability corrections  
**Status:** Automated checks and live bridge response verified; full player-input/action-animation smoke test remains operator-visible.

## Automated evidence

```powershell
py -3 -m unittest discover -s tools/mgba-bridge/tests -v
```

Result: **58 tests passed**. The suite includes fixed V2 frame parsing, Lua source-contract checks, strict native/JSON tool-call compatibility, one malformed-reply retry, repeated-malformed fallback, legal action selection, and loopback connection behavior.

`git diff --check` emitted no output.

## Live transport evidence

The initial live mGBA session exposed two field-by-field serialization defects:

1. Each move wire record omitted its final reserved byte, producing a 409-byte request. The service correctly waited for the fixed 425-byte frame.
2. The six-byte legal-action wire record copied C struct byte offsets `0..5`, transmitting its padding byte and omitting `canFaintTarget`. The service correctly rejected that request as invalid action analysis.

The corrected bridge was reset and loaded exactly once. A one-shot local service client captured a **425-byte** request and passed it to the production `handle_request_frame` path. The real local model returned:

```text
model_reply={'role': 'assistant', 'content': '{"name": "list_legal_actions", "arguments": {}}'}
model_reply={'role': 'assistant', 'content': '{"name": "choose_action", "arguments": {"action_index": 0}}'}
BAGB service: request 4 chose action 0
bridge_response=b'BAGB\x02\x02\x05\x00\x04\x00\x00\x00\x00'
```

mGBA Scripting then logged:

```text
BAGB client connected
BAGB request forwarded: 4
BAGB response written: 4
```

This proves the local Ollama response was a current legal action and was committed through the V2 Lua bridge. The client intentionally closed after the one-shot capture, so Lua subsequently logged the expected disconnect.

## Fallback and remaining manual check

The ROM's saved vanilla fallback remains unchanged; no failure path in these corrections writes a move or target directly. The remaining visible smoke check is to select the player's move after the committed Calvin response and observe Calvin use the corresponding legal move. The prior Computer Use session could focus mGBA but its injected game keys did not activate the emulator's configured controls, so that final animation observation is left to the operator.

## Links

- [Model-format retry specification](../specs/2026-07-29-phase-4a-model-format-retry.md)
- [Flow review](2026-07-29-phase-4a-model-format-retry-flow-review.md)
- [Implementation plan](../plans/2026-07-29-phase-4a-model-format-retry.md)
- [Parent Phase 4A specification](../specs/2026-07-29-phase-4a-local-ollama-tool-agent.md)
