# Phase 12 Specification: Tool-Exchange Time Budget

**Roadmap:** [External AI Trainer Integration Plan](../integration-plan.md)
**Flow review:** [Phase 12 flow review](../reviews/2026-08-05-phase-12-tool-exchange-budget-flow-review.md)
**Implementation plan:** [Phase 12 implementation plan](../plans/2026-08-05-phase-12-tool-exchange-budget.md)

**Goal:** Make valid multi-step local-model decisions less likely to fall back before `choose_actions` by giving the complete tool exchange 45 seconds, while retaining a 20-second limit for each individual Ollama HTTP response.

**In scope:** Split the existing shared Python timeout into two named constants. `request_ollama` uses a 20-second per-response timeout. `run_tool_agent` uses a 45-second monotonic end-to-end budget across all model calls, tool dispatches, and one malformed-format retry. The maximum of 12 model turns, exact legal-action validation, and one-call-at-a-time tool protocol remain unchanged.

**Out of scope:** ROM mailbox fields or versions, mGBA Lua behavior, trainer tagging, battle mechanics, changing Ollama models or options, retrying a timed-out HTTP request, automatic model warm-up, and improving malformed model output.

**Boundaries and data contract:** This is Python-service-only. The ROM continues to wait for its existing external response window and shows the existing thinking status; it accepts only a timely, current, ROM-listed legal action. No JSON schema or bridge frame changes are made.

**Failure and fallback behavior:** If any individual Ollama request takes longer than 20 seconds, fails, or returns invalid data, the service returns no response and the ROM keeps the existing vanilla trainer-AI fallback. If valid individual calls consume 45 seconds in total without a valid atomic `choose_actions`, the same fallback applies. The service never sends a partial choice. A malformed tool reply still gets only the existing one format-correction attempt inside the 45-second budget.

**Tests and measurable exit criteria:** Python tests must prove a normal three-call exchange that crosses 20 seconds cumulatively but finishes before 45 seconds reaches `choose_actions`; the same test must fail under the former shared 20-second limit. Tests must assert the independent 20-second per-response and 45-second exchange constants. `py -3 -m unittest discover -s tools/mgba-bridge/tests -q` passes. Manual smoke testing demonstrates a slow but valid local decision completes before the 45-second deadline, while service disconnection, an individual delayed response, malformed output, singles, and both double-battle variants retain their current fallback/gameplay behavior.
