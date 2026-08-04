# Phase 9 Local Ollama Model Selection Evidence

**Specification:** [Phase 9 specification](../specs/2026-08-04-phase-9-local-model-selection.md)
**Flow review:** [Phase 9 flow review](2026-08-04-phase-9-local-model-selection-flow-review.md)
**Implementation plan:** [Phase 9 implementation plan](../plans/2026-08-04-phase-9-local-model-selection.md)

## Automated evidence

- `py -3 -m unittest discover -s tools/mgba-bridge/tests -q`: 76 tests passed.
- Local discovery found `hermes3:8b` and `qwen2.5-coder:7b`; noninteractive selection chose the preferred Qwen model.

## Manual evidence required

Confirm the arrow-key menu, Enter, `--model`, Ctrl+C at the menu, and one
connected battle in Windows PowerShell. Existing absent-service fallback must
remain playable. Full ROM build and External AI evidence follows this smoke test.
