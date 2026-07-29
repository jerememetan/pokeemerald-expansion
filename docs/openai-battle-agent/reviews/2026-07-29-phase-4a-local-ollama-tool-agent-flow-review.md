# Phase 4A Flow Review: Local Ollama Tool Agent and ROM Response Acceptance

**Specification reviewed:** [Phase 4A specification](../specs/2026-07-29-phase-4a-local-ollama-tool-agent.md)  
**Review date:** 2026-07-29  
**Method:** `spec-flow-analyzer`, grounded in `src/battle_main.c`, `src/battle_agent.c`, `include/battle_agent.h`, `src/battle_ai_main.c`, and the Phase 3A Lua/Python bridge.

## Repository context

- `HandleTurnActionSelectionState` currently computes an opponent choice, publishes the V1 observation, then immediately emits the opponent controller command. A real response cannot affect the current turn without a distinct, frame-yielding action-selection state before that emission.
- `BattleAgent_TryPublishRequest` has the necessary single-trainer eligibility check and legal-action builder, but V1 exposes only an observation and deliberately never consumes a response.
- `BattleAgent_NormalizeSingleTarget` is the existing single-battle target authority. A V2 response must be rechecked through this function (or one behaviorally identical private helper), rather than checking only that a target happens to be alive.
- Phase 3A Lua accepts one loopback client and has a small ASCII line protocol. V2 will replace that wire format; `bridge_protocol.py`, source tests, deterministic responder, and Lua must change together.

## User flows

### 1. Calvin receives a valid local-agent decision

```mermaid
flowchart LR
    A["Calvin move turn"] --> B["Compute and save vanilla choice"]
    B --> C["Publish V2 request"]
    C --> D["Yield in external-AI wait state"]
    D --> E["Lua forwards binary frame"]
    E --> F["Service runs read-only tools with Ollama"]
    F --> G["choose_action legal index"]
    G --> H["Lua commits READY last"]
    H --> I["ROM revalidates and applies legal action"]
    I --> J["Existing opponent controller emits move"]
```

### 2. The local service or model is unavailable

`PENDING` remains unanswered while the normal battle task continues to run. On the 900th observed action-selection frame, the ROM clears the request and continues with the saved vanilla move and target. No controller command is emitted twice.

### 3. A response is stale, malformed, or no longer legal

Lua rejects malformed transport before writing RAM. If a `READY` record reaches the ROM, the ROM checks request status, sequence, eligibility, move-slot legality, and normalized target. It rejects a failure and continues with the saved vanilla result, without asking the service to retry.

### 4. The model does not make a valid terminal tool call

The service accepts at most 12 read-only tool calls. Unknown/invalid calls, a textual completion, a repeated `choose_action`, an HTTP error, or exhaustion of the service-side deadline produce no response. Flow 2 then handles the fallback.

## Gaps

### Critical

1. **The original specification did not name the action-selection handoff that prevents immediate controller emission.** `src/battle_main.c` currently falls through from publishing to `STATE_BEFORE_ACTION_CHOSEN`. Without an explicit state contract, an implementer could publish a request but still select vanilla immediately, or accidentally block all battle processing. **Resolution:** the specification now requires a Calvin-only `STATE_WAIT_EXTERNAL_AI_RESPONSE` state that yields on each frame, does not emit the opponent controller before resolution, and lets the surrounding action-selection loop continue processing other battlers.

2. **“Still-live target” was weaker than the repository’s legal-target rule.** A live target can still be invalid for a user-targeting move or a target type no longer supported by the phase. **Resolution:** consuming a V2 response must re-run `BattleAgent_NormalizeSingleTarget` for the selected move slot and require that its normalized target equals the stored legal action target.

### Important

1. **The binary contract said “mailbox field order” but did not forbid ABI padding in transport.** Lua/Python cannot safely infer C structure padding. **Resolution:** V2 transport has a separately enumerated byte order and fixed payload size; it is encoded/decoded field-by-field, never by copying C mailbox bytes.

2. **The deadline did not define its exact boundary.** **Resolution:** the response is accepted only during the first 899 wait-state visits; the 900th visit chooses the vanilla fallback before reading/applying a response. This gives a hard maximum of 900 frames and deterministic tie behavior.

3. **The user asked for the trainer AI’s actionable information, but the catalog provenance was not explicit.** **Resolution:** V2 exports move IDs plus static move fields needed for analysis (type, power, accuracy, effect, target category, priority, split), and a checked-in catalog generated from this repository’s constants/data supplies names and effect labels. The service never reads emulator memory.

4. **The service needed a bounded model-call policy in addition to the ROM deadline.** **Resolution:** one agent run has a 12-tool-call maximum and a 12-second monotonic service deadline; it returns no response on expiry. The shorter service deadline leaves time for Lua delivery before the ROM’s 15-second cutoff.

### Minor

1. **No UI/status indicator is specified.** Safe default: Phase 4A remains headless; bridge/service logs are the manual diagnostic surface. A ROM UI is out of scope.

2. **Ollama may return native tool calls in more than one JSON shape across versions.** Safe default: accept only the documented `message.tool_calls` array with one named tool per call; an unknown shape is treated as no response.

## Questions and resolved defaults

1. **Must the player’s action-selection UI freeze while Calvin waits?** No. The new wait state is per Calvin battler; the existing loop continues processing other battlers. This prevents a global freeze while preserving the fact that a turn cannot start until all actions are confirmed.
2. **Can a late response win a race on frame 900?** No. The 900th wait-state visit falls back before consumption, so the deadline is deterministic and safe.
3. **May the model select a move/target directly?** No. It returns only `legalActionIndex`; the ROM owns move slot and normalized target.
4. **May Python calculate damage or inspect RAM to enrich a response?** No. The ROM exports deterministic analysis facts, and Python only formats/tool-exposes the received V2 data.

## Recommended next steps

1. Incorporate the two critical and four important resolutions into the Phase 4A specification.
2. Have the user review the revised specification before creating its implementation plan, as required by the brainstorming workflow.
3. After approval, use `writing-plans` to create an exact, test-first implementation plan that names the new battle-selection state, V2 field-by-field encoder, service, catalog generator, and tests.

