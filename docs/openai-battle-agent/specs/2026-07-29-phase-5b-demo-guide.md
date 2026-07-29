# Phase 5B Specification: Manual Demo Guide and Recovery

**Status:** Approved design; awaiting flow review and implementation plan

**Roadmap:** [mGBA AI Trainer Design](../2026-07-18-mgba-ai-trainer-design.md#phase-5-agent-diagnostics-and-trainer-demo-hardening)

**Prerequisite:** Phase 4A local Ollama action selection, Phase 4B decision
audit, and Phase 5A thinking-status presentation remain unchanged.

## Goal

Make the existing Calvin demo repeatable for the current manual Windows/mGBA
setup. A developer should be able to follow one concise guide to warm Ollama,
start the Python service, open the built ROM, load the Lua bridge, recognize a
successful agent turn, and recover from the documented common failures.

## Scope

### In scope

- Rewrite `tools/mgba-bridge/README.md` into an ordered manual launch and
  recovery guide for the existing local setup.
- State the required order and the expected, observable PowerShell and mGBA
  Scripting logs at every connection boundary.
- Provide a compact symptom-to-recovery table for model/API unavailability,
  a missing model, a stale generated mailbox address, a Lua listener port
  conflict, service disconnection, rejected/malformed response, and vanilla
  fallback.
- Include connected-service and absent-service smoke-test checklists that use
  Youngster Calvin and the existing `AI is thinking...` message.
- Cross-link the Phase 4A/4B/5A specification and evidence artifacts.

### Out of scope

- Starting Ollama, Python, mGBA, or Lua automatically.
- Adding a launcher, health-check process, dashboard, telemetry persistence,
  new command-line flags, or any code change.
- Changing the ROM, mailbox V2 format, Lua listener, Python decision loop,
  900-frame fallback deadline, model, trainer coverage, legal actions,
  switching/items, or double battles.

## Existing-boundary contract

| Boundary | Required manual responsibility | Unchanged behavior |
| --- | --- | --- |
| WSL build | Rebuild ROM and regenerate the ignored mailbox Lua address after source changes. | Produces the ROM/ELF used by mGBA. |
| Ollama | Run locally and contain `qwen2.5-coder:7b`; warm it before a live demo when necessary. | Serves only the existing local chat request. |
| Python service | Remain running in its PowerShell window; connect after Lua is listening. | Uses only the loopback bridge and can return one legal action. |
| mGBA Lua bridge | Load once in mGBA after opening the current ROM. | Accepts one service connection on `127.0.0.1:57621`. |
| ROM | Start a Calvin battle and choose the player action. | Shows thinking status, accepts legal response, or uses saved vanilla fallback. |

The guide must state that a Lua listener/service session is one-to-one: after a
service disconnect, restart mGBA and reload the Lua script before starting a
new Python-service session. It must never suggest using a second probe or
second service connection to test that listener.

## User flows

1. **Connected demo:** Build/regenerate, confirm the model, warm it if needed,
   start the service, open the ROM, load Lua, and fight Calvin. The guide maps
   service `request N`/`chose action` and Lua `request forwarded`/`response
   written` messages to a normal in-game agent turn.
2. **No response/fallback demo:** Run Calvin without the service or stop the
   service after a forwarded request. The guide identifies the visible
   thinking status, the bounded wait, vanilla action, and required session
   reset before retrying.
3. **Setup/recovery:** The user matches an observed terminal or mGBA symptom to
   one minimal corrective action, then restarts only the component required by
   that documented recovery.

## Failure and fallback behavior

- Documentation must distinguish a normal first-turn cold-model fallback from
  a bridge failure and recommend warming Ollama before a demo.
- If the model/service fails, the guide must say that no response is normal
  and the ROM's existing saved vanilla trainer AI continues after its unchanged
  timeout; it must not instruct the user to restart the ROM during that wait.
- If Lua cannot bind port 57621, the guide must instruct the user to close the
  previous mGBA/Lua listener before loading the script again.
- If `generated/mailbox_address.lua` is stale after a rebuild, the guide must
  direct regeneration from the fresh ELF before launching mGBA.
- No recovery step may require changing a port, editing generated files,
  disabling fallback, or sending a manual mailbox response.

## Tests and verification

- Review every command and log string against the current checked-in README,
  `battle_agent_service.py`, `mgba_bridge.lua`, and bridge tests.
- Run the existing Python bridge-service suite and focused External AI ROM
  suite; no production behavior has changed, so they are regression evidence.
- Run `git diff --check`.
- Manually follow the revised connected-service checklist and the
  absent-service fallback checklist once, recording outcomes in a Phase 5B
  evidence file.

## Measurable exit criteria

- A new developer can follow the README from build through a connected Calvin
  decision without unstated ordering assumptions.
- The guide contains exact success logs, the one-to-one bridge-session rule,
  and a recovery action for each scoped symptom.
- A user validates both connected and fallback checklists without a stuck
  battle or a protocol/action change.
- Existing relevant automated tests pass and the documentation diff has no
  whitespace errors.
