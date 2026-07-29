# Phase 4B Evidence: PowerShell Decision Audit

**Status:** Automated verification complete; manual Calvin smoke test pending
**Specification:** [Phase 4B PowerShell decision audit](../specs/2026-07-29-phase-4b-powershell-decision-audit.md)

## Automated verification

```powershell
py -3 -m unittest discover -s tools/mgba-bridge/tests -p test_battle_agent_service.py -v
```

Result: **17 tests passed**. The focused suite proves that a successful
decision retains only successfully dispatched tool names, formats the selected
ROM action facts and speed context, emits the audit before the unchanged V2
response, and logs `vanilla_fallback` without a response on no decision.

```powershell
py -3 -m unittest discover -s tools/mgba-bridge/tests
```

Result: **61 tests passed** with no failures or errors.

## Manual verification procedure

Restart only the Python service so it loads the audit implementation; the Lua
bridge and ROM do not need rebuilding for this Python-only change. Fight
Calvin and verify a service record beginning `BAGB service: audit #N` matches
the mGBA `BAGB response written: N` sequence. Then stop the service during a
pending request and verify the service/mGBA remains responsive and Calvin uses
the existing vanilla fallback.

## Links

- [Flow review](2026-07-29-phase-4b-powershell-decision-audit-flow-review.md)
- [Implementation plan](../plans/2026-07-29-phase-4b-powershell-decision-audit.md)
