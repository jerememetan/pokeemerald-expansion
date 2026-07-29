# Phase 4B PowerShell Decision Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` or inline execution task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Print a compact, deterministic PowerShell audit for each valid local-agent move decision without exposing hidden reasoning or changing ROM/Lua action authority.

**Architecture:** The Python service will replace its `int` model-loop result with an immutable `AgentDecision` containing the existing legal action index and ordered names of successfully dispatched tools. `handle_request_frame` will create a pure audit string from that record, the decoded V2 payload, and legal actions; it prints the audit before formatting the unchanged 13-byte V2 response. A no-decision result prints the one-line vanilla-fallback audit and sends nothing.

**Tech Stack:** Python 3 standard library, `dataclasses`, `unittest`, current V2 bridge protocol, existing static catalog.

---

## File structure

- Modify `tools/mgba-bridge/battle_agent_service.py` — add `AgentDecision`, immutable ROM-fact formatting helpers, and audit emission at the response boundary.
- Modify `tools/mgba-bridge/tests/test_battle_agent_service.py` — add test-first assertions for audit text, actual tool history, malformed retry, and no-decision fallback.
- Modify `tools/mgba-bridge/README.md` — show a representative audit and state its evidentiary boundary.
- Modify `docs/openai-battle-agent/specs/2026-07-29-phase-4b-powershell-decision-audit.md` — link this plan and mark it flow reviewed.
- Create `docs/openai-battle-agent/reviews/2026-07-29-phase-4b-powershell-decision-audit-evidence.md` — record the command result and manual log after implementation.

## Task 1: Define audit outputs with failing tests

**Files:**

- Modify: `tools/mgba-bridge/tests/test_battle_agent_service.py`

- [ ] **Step 1: Add a failing successful-decision audit test.**

  Import `AgentDecision` and the pure `format_decision_audit` helper. Create a 417-byte payload whose requester (battler 1) move slot 1 is `MOVE_EMBER`, whose active speeds make battler 1 faster, and use existing two legal actions. Assert:

  ```python
  decision = AgentDecision(1, ("get_battle_state", "list_legal_actions"))
  audit = format_decision_audit(7, 1, decision, actions, payload)
  self.assertIn("audit #7", audit)
  self.assertIn("tools used: get_battle_state, list_legal_actions", audit)
  self.assertIn("legal actions: 0=", audit)
  self.assertIn("selected: 1=", audit)
  self.assertIn("selected ROM facts: STAB=yes", audit)
  self.assertIn("speed context: battler_1_first", audit)
  ```

  Also assert the audit does not contain `reasoning`, raw model content, or a full payload representation.

- [ ] **Step 2: Add failing audit-emission tests.**

  Patch `run_tool_agent` to return `AgentDecision(0, ("list_legal_actions", "choose_action"))`, patch `log`, call `handle_request_frame` with the existing valid V2 frame fixture, and assert the response remains exactly `b"BAGB\\x02\\x02\\x05\\x00\\x07\\x00\\x00\\x00\\x00"` while one `log` call starts with `audit #7`.

  In a second test, patch `run_tool_agent` to return `None`, call `handle_request_frame`, assert `None`, and assert one log call equals `"audit #7: no legal model decision; vanilla_fallback"`.

- [ ] **Step 3: Add a failing malformed-retry history test.**

  Reuse the existing malformed-first-reply fixture. Assert `run_tool_agent(...)` returns `AgentDecision(1, ("list_legal_actions", "choose_action"))`; the rejected malformed reply is absent from the tuple.

- [ ] **Step 4: Run focused tests and verify RED.**

  Run:

  ```powershell
  py -3 -m unittest discover -s tools/mgba-bridge/tests -p test_battle_agent_service.py -v
  ```

  Expected: import/expectation failures because `AgentDecision`, `format_decision_audit`, and audit emission do not yet exist; existing action-return tests may fail until deliberately updated in Task 2.

## Task 2: Preserve decision provenance through the service

**Files:**

- Modify: `tools/mgba-bridge/battle_agent_service.py`
- Test: `tools/mgba-bridge/tests/test_battle_agent_service.py`

- [ ] **Step 1: Add the immutable result type.**

  Directly after `ToolError`, define:

  ```python
  @dataclass(frozen=True)
  class AgentDecision:
      action_index: int
      tools_used: tuple[str, ...]
  ```

  Import `dataclass` from `dataclasses`. Do not put model content, arguments, or payloads in this type.

- [ ] **Step 2: Update `run_tool_agent`.**

  Change its return annotation to `AgentDecision | None`, initialize `tools_used: list[str] = []`, and append a tool name only after its arguments pass the existing branch validation and the tool result is computed. On terminal selection, return:

  ```python
  return AgentDecision(action_index, tuple(tools_used + ["choose_action"]))
  ```

  Preserve the exact strict parser, one malformed-output retry, `MAX_TOOL_CALLS`, `SERVICE_TIMEOUT_SECONDS`, and all no-response returns.

- [ ] **Step 3: Update existing action-loop tests.**

  Replace exact integer assertions with `self.assertEqual(result.action_index, 1)` after asserting `result is not None`. Keep every existing invalid-message assertion as `None`.

- [ ] **Step 4: Run focused tests and verify provenance behavior.**

  Run:

  ```powershell
  py -3 -m unittest discover -s tools/mgba-bridge/tests -p test_battle_agent_service.py -v
  ```

  Expected: all model-loop tests pass and only successful dispatches appear in `tools_used`.

## Task 3: Format and emit deterministic audits

**Files:**

- Modify: `tools/mgba-bridge/battle_agent_service.py`
- Test: `tools/mgba-bridge/tests/test_battle_agent_service.py`

- [ ] **Step 1: Add pure formatting helpers.**

  Define `EFFECTIVENESS_LABELS = {0: "immune", 1: "not-very-effective", 2: "neutral", 3: "super-effective"}`. Add `format_legal_action(action, requester_moves)` and `format_decision_audit(sequence, requesting_battler, decision, actions, payload)`. The latter must use `get_battler_moves(payload, requesting_battler)`, `analyze_action(actions, decision.action_index, requester_moves)`, and `compare_speed(payload)`; it must join only the fixed fields required by the specification.

  Raise `ToolError` when an action index is absent or an effectiveness category is not in `EFFECTIVENESS_LABELS`. Do not calculate damage, inspect mGBA, or call Ollama.

- [ ] **Step 2: Emit audit before response formatting.**

  In `handle_request_frame`, preserve parsing and `request received` logging. If `run_tool_agent` returns `None`, log exactly:

  ```python
  log(f"audit #{request.sequence}: no legal model decision; vanilla_fallback")
  ```

  and return `None`. Otherwise call and log `format_decision_audit(...)` inside the existing `ToolError`/`ValueError` failure boundary before calling `format_response_frame`. If formatting raises, log a concise rejection and return `None`; never send a response first.

- [ ] **Step 3: Run focused tests and verify GREEN.**

  Run:

  ```powershell
  py -3 -m unittest discover -s tools/mgba-bridge/tests -p test_battle_agent_service.py -v
  ```

  Expected: exact V2 response bytes remain unchanged for valid decisions, valid audits contain only deterministic facts, and no-decision cases emit fallback audit text with no response.

## Task 4: Verify and document the vertical slice

**Files:**

- Modify: `tools/mgba-bridge/README.md`
- Modify: `docs/openai-battle-agent/specs/2026-07-29-phase-4b-powershell-decision-audit.md`
- Create: `docs/openai-battle-agent/reviews/2026-07-29-phase-4b-powershell-decision-audit-evidence.md`

- [ ] **Step 1: Document a representative audit.**

  Add the approved audit example to `tools/mgba-bridge/README.md`, followed by: “This is a deterministic record of available ROM facts and tools used; it is not the model's hidden reasoning.”

- [ ] **Step 2: Run complete automated verification.**

  Run:

  ```powershell
  py -3 -m unittest discover -s tools/mgba-bridge/tests -v
  git diff --check
  ```

  Expected: every bridge/service test passes and `git diff --check` emits no output.

- [ ] **Step 3: Run the manual Calvin smoke test.**

  Reset mGBA Scripting, load `tools/mgba-bridge/mgba_bridge.lua` exactly once, start `py -3 tools/mgba-bridge/battle_agent_service.py`, and fight Calvin. Expected PowerShell/mGBA evidence:

  ```text
  BAGB service: audit #N
    tools used: ...
    legal actions: ...
    selected: ...
    selected ROM facts: ...
  BAGB response written: N
  ```

  Stop the service during a later pending request; expected: one `vanilla_fallback` audit and a responsive vanilla move by the existing ROM deadline.

- [ ] **Step 4: Record evidence and commit.**

  Record exact test totals, one successful audit/log sequence, and fallback observation in the evidence file. Link it from the Phase 4B specification. Then run:

  ```powershell
  git add tools/mgba-bridge/battle_agent_service.py tools/mgba-bridge/tests/test_battle_agent_service.py tools/mgba-bridge/README.md docs/openai-battle-agent/specs/2026-07-29-phase-4b-powershell-decision-audit.md docs/openai-battle-agent/reviews/2026-07-29-phase-4b-powershell-decision-audit-flow-review.md docs/openai-battle-agent/reviews/2026-07-29-phase-4b-powershell-decision-audit-evidence.md docs/openai-battle-agent/plans/2026-07-29-phase-4b-powershell-decision-audit.md
  git commit -m "feat(agent): add decision audit logs"
  ```

## Compatibility and fallback checklist

- V2 request/response sizes, Lua forwarding, ROM mailbox, and legal action authority are unchanged.
- The audit never receives a model-provided rationale or raw model response.
- Audit facts come exclusively from decoded V2 payload, legal action list, catalog labels, and pure service helpers.
- Every parser, endpoint, tool-validation, deadline, and audit-formatting failure returns no response; ROM fallback remains unchanged.
- Switching, items, bench snapshots, doubles, and trainer scope expansion remain excluded.

## Self-review

- **Specification coverage:** Task 1 defines every successful and no-decision output; Task 2 carries only validated tool provenance; Task 3 formats before bridge response; Task 4 verifies operator visibility and fallback.
- **Terminology and types:** The plan consistently uses `AgentDecision`, `tools_used`, `format_decision_audit`, legal action, ROM facts, `vanilla_fallback`, V2 response, 12-second service deadline, and 900-frame ROM fallback.
- **Protocol/mechanics safety:** No task changes model tools, response byte layout, Lua writes, ROM selection, targeting, or battle calculations.
- **Scope:** The plan is audit-only. Trainer switching is explicitly postponed to a separately specified action-family phase.

## Links

- [Phase 4B specification](../specs/2026-07-29-phase-4b-powershell-decision-audit.md)
- [Flow review](../reviews/2026-07-29-phase-4b-powershell-decision-audit-flow-review.md)
- [Phase 4A local-agent plan](2026-07-29-phase-4a-local-ollama-tool-agent.md)
