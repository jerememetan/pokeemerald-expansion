# mGBA AI Trainer Design

**Status:** Phase 2 and Phase 3A verified; Phase 4A implementation in progress

**Goal:** Add a local, external AI decision layer to `pokeemerald-expansion` that can control selected trainer battle actions in a playable ROM, while the ROM remains the sole authority on battle rules and always falls back to the existing trainer AI.

## Product boundary

The first playable demo is a specially configured single-battle trainer. The external layer may choose one legal move and target for that trainer. The player sees a normal battle; any model explanation is displayed outside the ROM by the host service.

The first demo does not include items, switching, online services, model credentials in the ROM, a replacement battle engine, or changes to damage calculation. It is intentionally a local mGBA-based developer/demo feature.

## Selected architecture

The system has four bounded components:

1. **ROM decision hook.** The game preserves the current trainer-AI path. It decides whether the current battler is enabled for external control, exports a compact request, validates a returned action, and otherwise uses the existing decision.
2. **Shared EWRAM mailbox.** The ROM owns a fixed, versioned C structure containing a request sequence number, a request status, visible battle state, legal actions, and a response slot. It is the only data the mGBA script may read or write for decisions.
3. **mGBA Lua bridge.** A Lua script observes the mailbox on each frame, sends requests to a loopback-only host connection, and writes validated transport responses into the mailbox. It never alters arbitrary game memory and never blocks the emulator during a battle.
4. **Local AI trainer service.** A separate local Python process accepts one bridge connection, converts snapshots into an AI prompt/tool context, chooses one provided legal action, records an explanation, and returns a small response message.

The service starts before mGBA and establishes the TCP connection to a Lua listener. This avoids mGBA's blocking outbound socket connection behavior. Phase 3A manually validated Windows mGBA 0.10.5 for the bridge; the final evidence must record the exact executable's SHA-256 and `--version` output.

## ROM control-flow seam

The current engine calculates trainer actions in `src/battle_main.c` and stores them in `gBattleStruct->aiMoveOrAction[battler]` and `gBattleStruct->aiChosenTarget[battler]`. `OpponentHandleChooseMove` in `src/battle_controller_opponent.c` consumes those values and emits the action.

The external layer will integrate around this established decision state. It will not alter move effects, damage, turn ordering, target legality, or battle scripts. The engine determines legal move slots and targets; the service can only select from that supplied list.

## Mailbox contract

The mailbox is a fixed-size C structure in EWRAM with these rules:

- `protocolVersion` must equal `1` on both sides.
- `requestSequence` increases for each external decision request and is never reused within a battle.
- The ROM publishes the snapshot fully before marking the request `PENDING`.
- A response is usable only when its sequence equals the current request sequence, its status is `READY`, and its selected action is in the current legal-action list.
- The bridge writes only response fields and changes response status to `READY` after the response payload is complete.
- The ROM clears or supersedes all previous response data before requesting a new decision.

The initial request payload includes: battle ID, turn number, requesting battler, active battlers' visible species/HP/status/stat stages, weather/terrain, four own move slots, a compact list of legal move-and-target actions, and the last three turn events. It excludes hidden opponent data unless the normal trainer AI would legally possess it for the configured trainer.

The initial response payload contains only: protocol version, request sequence, selected legal-action index, and a response status. The explanation remains in the host service and is not required for the ROM to play.

## Failure behavior

Correct battle behavior has priority over AI participation.

- External mode disabled: use existing trainer AI unchanged.
- Bridge absent, disconnected, malformed, or too slow: use existing trainer AI for that decision.
- Stale sequence, mismatched protocol, illegal move slot, illegal target, or duplicate response: reject it and use existing trainer AI.
- Service error or model error: return an error response if possible; the ROM falls back.
- mGBA script error: the ROM remains playable because no external response arrives.

The ROM must not wait in a busy loop or pause the emulator for an AI response. It checks a bounded number of frames, then falls back. The exact frame budget is a measurable configuration value chosen during the bridge spike; the demo's service is expected to answer within that budget on a local machine.

## End-to-end roadmap

### Phase 0: Discovery and contracts

Document the current battle-AI call graph, the existing test/build commands, trainer configuration data, legal-action helpers, and global state ownership. Define the mailbox C layout and a byte-for-byte Lua/Python wire representation before adding external behavior.

**Exit criterion:** A reviewed call graph, protocol document, and test matrix identify one safe hook and the required legality checks.

### Phase 1: ROM-only external mode

Add a generic `Trainer.externalAi` opt-in that is separate from vanilla `aiFlags`. Enable it only for Route 102's `TRAINER_CALVIN_1`, then add a ROM-only, test-only mock-response seam that can supply a legal opponent-targeting move slot. Confirm ordinary trainers, unsupported battle types, absent mock responses, and rejected mock responses retain existing AI behavior.

**Exit criterion:** The ROM builds, existing battle tests pass, and Calvin can use a deterministic legal test mock move without changing any other trainer or a vanilla switch/item action.

### Phase 2: Legal-action snapshot

Build a compact snapshot and legal-action list from engine-owned state. Initially support singles and moves only. Add tests for disabled moves, self-targeting moves, selected-target moves, no-PP moves, fainted targets, and stale responses.

**Exit criterion:** Snapshot tests prove every emitted action is legal, and no external selector can force an unlisted move or target.

### Phase 3A: mGBA bridge spike

Validated with Windows mGBA 0.10.5, a Lua frame-polling script round-trips a fixed mailbox response without blocking input or frames. It binds only to loopback and rejects unexpected messages. The evidence records the hash of the executable actually used, rather than an archive. The executable's `--version` invocation returned no console output on this Windows build, so the observed title-bar version is recorded instead.

**Exit criterion:** A scripted test session demonstrates request/response sequencing, disconnection fallback, and no pause when the service is unavailable.

**Verified:** See [Phase 3A evidence](reviews/2026-07-29-phase-3a-mgba-loopback-bridge-evidence.md). Phase 4 requires its own reviewed specification and plan for the full-snapshot local-service protocol and ROM-side response acceptance; Phase 3A's deterministic responder is not a service implementation.

### Phase 4A: Local Ollama tool agent and ROM response acceptance

Upgrade the mailbox and bridge to V2, add a bounded ROM response wait/acceptance seam, and create a loopback-only Python tool service for the local `qwen2.5-coder:7b` Ollama model. The model receives only read-only battle-analysis tools and can return one supplied legal action index; it never gets a rule-based move scorer, direct emulator access, or authority to name a move or target. The ROM keeps its already-computed vanilla choice and uses it at the 900-frame deadline or on any invalid response.

**Exit criterion:** Calvin completes a playable trainer-single battle using a legal local-agent action when available. All absent, malformed, stale, illegal, or late replies take the saved vanilla fallback without freezing the battle.

**Planning artifacts:** [specification](specs/2026-07-29-phase-4a-local-ollama-tool-agent.md), [flow review](reviews/2026-07-29-phase-4a-local-ollama-tool-agent-flow-review.md), [implementation plan](plans/2026-07-29-phase-4a-local-ollama-tool-agent.md), and [qwen compatibility review](reviews/2026-07-29-phase-4a-tool-call-compatibility-flow-review.md). Phase 4A is not verified until fresh ROM build/test and connected mGBA evidence are recorded.

### Phase 4B: PowerShell decision audit

Add an operator-only, deterministic decision audit to the local service. It records tools actually used, ROM-provided legal move options, the selected legal action, and ROM facts that make the choice assessable; it does not expose model reasoning, alter the V2 protocol, or add action authority.

**Exit criterion:** A connected Calvin turn emits an audit that matches its accepted bridge sequence and action; all no-decision cases log `vanilla_fallback` and preserve the existing ROM fallback.

**Planning artifacts:** [specification](specs/2026-07-29-phase-4b-powershell-decision-audit.md), [flow review](reviews/2026-07-29-phase-4b-powershell-decision-audit-flow-review.md), and [implementation plan](plans/2026-07-29-phase-4b-powershell-decision-audit.md).

### Phase 5: Agent diagnostics and trainer demo hardening

Instrument local-agent latency, tool calls, selections, rejected responses, fallback count, and battle outcome. Improve the repeatable mGBA demo and error diagnostics without widening the action authority beyond the Phase 4A tool/action contract.

**Exit criterion:** A documented repeatable demo works with the service connected and remains playable when it is disconnected.

### Phase 5A: In-battle thinking status

Add a presentation-only status to the normal lower battle message window while
the ROM waits for an external trainer action. It displays `AI is thinking` with
an animated ellipsis and clears before either an accepted response resumes
action selection or the existing timeout uses vanilla fallback. This is a
separate vertical slice from Phase 5 diagnostics: it does not change the
mailbox, bridge, service, action authority, or deadline.

**Exit criterion:** Calvin visibly shows the status during a pending external
request; it clears automatically on both accepted response and absent-service
fallback, while battle behavior remains unchanged.

**Status:** Complete. [Specification](specs/2026-07-29-phase-5a-thinking-status.md),
[flow review](reviews/2026-07-29-phase-5a-thinking-status-flow-review.md),
[implementation plan](plans/2026-07-29-phase-5a-thinking-status.md), and
[verification evidence](reviews/2026-07-29-phase-5a-thinking-status-evidence.md).

### Phase 6: Broaden trainer coverage

Add a debug/global enable mode and then opt-in trainer configuration. Keep the same mailbox protocol version unless an additive, backward-compatible extension is needed.

**Exit criterion:** Multiple configured trainers can use the service independently without affecting unconfigured battles.

### Phase 7: Switching and battle items

Extend the legal-action list to switch actions first, then battle items if wanted. Treat each action family as a separate protocol and test expansion; the model never invents a party index or item.

**Exit criterion:** Switching/item choices are fully legality-validated and have individual fallback tests.

### Phase 8: Double battles

Extend snapshots and legal actions for two AI battlers, ally-targeting, spread moves, and synchronized turn decisions. Decide and document whether one service request returns both actions or each battler gets a separate request; the recommended design is one turn-level request containing each AI battler's legal actions.

**Exit criterion:** Battle tests cover enemy, ally, self, spread, absent, and fainted targets; a playable double battle completes with safe fallback for either battler.

### Phase 9: Packaging and handoff

Provide a pinned mGBA build/version, Lua script, Python environment instructions, ROM build instructions, a launch sequence, known limitations, and an automated smoke test.

**Exit criterion:** A new developer can build the ROM, launch the service and mGBA script, play the demo trainer, and reproduce a fallback case from the documentation.

## Verification strategy

Every change uses a test-first cycle where the repository supports it. Each phase must have both automated evidence and a repeatable emulator test. Required regression categories are ordinary-AI behavior, disabled external mode, valid response, missing response, late response, stale response, malformed response, illegal action, service disconnect, and version mismatch.

Before a phase is declared complete, run the full relevant battle-test suite and ROM build from a clean state, inspect the diff for unrelated battle mechanics changes, and record the exact mGBA build and service version used for the emulator test.

## Deferred decisions

Later phase specifications will select any additive protocol extensions and broader trainer/model configuration. The mailbox symbol strategy, trainer opt-in bit, V2 wire contract, and 900-frame asynchronous deadline are established by the completed phases and Phase 4A specification. These details do not alter the safety invariant: only engine-provided legal actions may be executed.

## Phase 0 reference set

- [Phase 0 specification](specs/2026-07-18-phase-0-discovery-and-contract-baseline.md)
- [Phase 0 flow review](reviews/2026-07-18-phase-0-discovery-and-contract-baseline-flow-review.md)
- [Battle AI call graph](battle-ai-callgraph.md)
- [Battle state inventory](battle-state.md)
- [Protocol version 1](protocol.md)
- [Integration plan](integration-plan.md)
- [Phase 0 task plan](plans/2026-07-18-phase-0-discovery-and-contract-baseline.md)
- [Phase 1 specification](specs/2026-07-18-phase-1-trainer-opt-in-and-rom-mock.md)
- [Phase 1 flow review](reviews/2026-07-18-phase-1-trainer-opt-in-and-rom-mock-flow-review.md)
- [Phase 1 implementation plan](plans/2026-07-18-phase-1-trainer-opt-in-and-rom-mock.md)
- [Phase 1 build and test evidence](reviews/2026-07-18-phase-1-build-and-test-evidence.md)
- [Phase 2 specification](specs/2026-07-26-phase-2-legal-action-snapshot.md)
- [Phase 2 flow review](reviews/2026-07-26-phase-2-legal-action-snapshot-flow-review.md)
- [Phase 2 implementation plan](plans/2026-07-26-phase-2-legal-action-snapshot.md)
- [Phase 2 build and test evidence](reviews/2026-07-28-phase-2-build-and-test-evidence.md)
- [Phase 3A specification](specs/2026-07-28-phase-3a-mgba-loopback-bridge.md)
- [Phase 3A flow review](reviews/2026-07-28-phase-3a-mgba-loopback-bridge-flow-review.md)
- [Phase 3A implementation plan](plans/2026-07-28-phase-3a-mgba-loopback-bridge.md)
- [Phase 3A evidence](reviews/2026-07-29-phase-3a-mgba-loopback-bridge-evidence.md)
- [Phase 4A specification](specs/2026-07-29-phase-4a-local-ollama-tool-agent.md)
- [Phase 4A flow review](reviews/2026-07-29-phase-4a-local-ollama-tool-agent-flow-review.md)
- [Phase 4A implementation plan](plans/2026-07-29-phase-4a-local-ollama-tool-agent.md)
- [Phase 4B specification](specs/2026-07-29-phase-4b-powershell-decision-audit.md)
- [Phase 4B flow review](reviews/2026-07-29-phase-4b-powershell-decision-audit-flow-review.md)
- [Phase 4B implementation plan](plans/2026-07-29-phase-4b-powershell-decision-audit.md)
