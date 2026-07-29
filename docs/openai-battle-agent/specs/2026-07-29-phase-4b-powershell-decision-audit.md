# Phase 4B Specification: PowerShell Decision Audit

**Status:** User-approved design; awaiting flow review and implementation plan  
**Parent roadmap:** [mGBA AI trainer design](../2026-07-18-mgba-ai-trainer-design.md)  
**Prerequisite:** [Phase 4A evidence](../reviews/2026-07-29-phase-4a-model-format-retry-evidence.md)

## Goal

Make every completed local-agent decision observable in the PowerShell service log. The audit must show which read-only tools the model called, the ROM-provided legal action options, the selected legal action, and ROM-derived facts relevant to judging that action. It must not claim to expose or reconstruct the model's hidden reasoning.

## Scope

### In scope

- `TRAINER_CALVIN_1`'s existing Phase 4A move decisions only.
- One compact, multi-line `BAGB audit #<sequence>` record after a valid terminal `choose_action`.
- The record contains the request sequence, ordered tool names actually dispatched for that request, each ROM-provided legal action's index, move slot, resolved move label, and target battler, plus the selected action's ROM-derived STAB, effectiveness, KO predicate, move priority, and normal speed context.
- The service computes audit values only from the already-decoded V2 payload, current legal actions, static catalog labels, and existing pure service helpers.
- A concise no-decision audit outcome when the model run ends without a legal terminal choice, identifying the safe outcome as `vanilla_fallback` without logging a raw model reply or a battle payload.
- Unit tests for successful, malformed-retry, and no-choice audit records.

### Out of scope

- ROM UI, mGBA overlay, persistent files, telemetry, raw binary frame dumps, full tool-result transcripts, model chain-of-thought, model-provided prose explanations, trainer switching, items, doubles, new model tools, or protocol changes.

## Boundaries and data contract

The ROM, Lua bridge, V2 frame, 900-frame fallback, and legal-action validation are unchanged. The audit is an operator-only PowerShell diagnostic emitted by `battle_agent_service.py`; it is not sent to the ROM, Lua, or model.

The audit can say that a tool was called and can display deterministic ROM facts. It must label its facts as `ROM facts` and its tool list as `tools used`; it must never state that the model considered every displayed option or infer an internal rationale.

## Audit format

For a successful action, the service writes this fixed-shape record after validating `choose_action`:

```text
BAGB audit #5
  tools used: get_battle_state, compare_speed, list_legal_actions
  legal actions: 0=Ember->battler 0; 1=Growl->battler 0
  selected: 0=Ember->battler 0
  selected ROM facts: STAB=yes, effectiveness=super-effective, KO=no, priority=0
  speed context: battler_1_first
```

Tool names appear in call order and may repeat. Legal actions appear in the ROM's current action-index order. Unknown catalog labels use the existing `UNKNOWN` value. The exact enum display for effectiveness is a stable service-owned label derived from the existing numeric category; it does not recalculate battle damage.

For a no-response run, the service writes one line:

```text
BAGB audit #5: no legal model decision; vanilla_fallback
```

It may still retain the existing concise failure diagnostics, but must not add raw model content or full snapshot data.

## Failure and fallback behavior

| Condition | Required behavior |
|---|---|
| Valid legal `choose_action` | Emit exactly one successful audit record, then return the unchanged 13-byte V2 response. |
| Malformed first tool call, then valid selection | Include the successfully dispatched tools only; the existing retry diagnostic remains separate. |
| Second malformed response, endpoint failure, invalid tool/arguments, invalid action, deadline, or tool cap | Emit the no-decision audit line; write no bridge response; ROM keeps saved vanilla AI fallback. |
| Audit formatting error | Treat it as a service failure: write no bridge response and rely on ROM fallback. Never choose a different action or alter battle state. |

## Tests and measurable exit criteria

1. Service tests prove a successful audit reflects tool order, legal actions, selected action, and only deterministic ROM facts.
2. Tests prove malformed-retry flow records only successfully dispatched tools, while repeated malformed or invalid choices print the fallback audit and return no response.
3. Tests prove an unknown catalog entry and all legal action indexes format safely without querying mGBA or reading files beyond the existing catalog.
4. `py -3 -m unittest discover -s tools/mgba-bridge/tests -v` passes.
5. Manual Windows smoke test against Calvin displays a PowerShell audit matching the accepted mGBA sequence and the corresponding `BAGB response written` log. A stopped service remains responsive and uses vanilla fallback.

## Explicitly deferred decision

Trainer switching is deferred to a separate phase. It requires a distinct legal-action family, active and bench snapshot contract, ROM-side replacement validation, trainer-controller integration, and failure tests. Keeping it out of this audit phase prevents audit work from silently expanding move-action authority.

## Links

- [Phase 4A specification](2026-07-29-phase-4a-local-ollama-tool-agent.md)
- [Phase 4A evidence](../reviews/2026-07-29-phase-4a-model-format-retry-evidence.md)
