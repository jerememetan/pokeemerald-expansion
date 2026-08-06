# Phase 14 Legal-Action Query Normalization Implementation Plan

**Goal:** Normalize model-supplied `list_legal_actions` arguments to the complete safe legal-action list so harmless query-shape errors do not force vanilla fallback.

**Architecture:** Remove the optional scoped parameter from only the LLM-facing schema. In `run_tool_agent`, accept any parsed arguments for `list_legal_actions`, log nonempty keys, and call the existing helper with no requested battler. The separate terminal validator remains untouched.

**Tech Stack:** Python 3 standard library, existing `unittest`/`mock`, Ollama local `/api/chat` endpoint, mGBA bridge.

---

### Task 1: Lock the model-facing contract with failing tests

**Files:**
- Modify: `tools/mgba-bridge/tests/test_battle_agent_service.py`
- Test: `tools/mgba-bridge/tests/test_battle_agent_service.py`

- [ ] **Step 1: Add a test that the exposed schema has no `list_legal_actions` properties.**

```python
schema = next(tool for tool in TOOL_SCHEMAS if tool["function"]["name"] == "list_legal_actions")
self.assertEqual(schema["function"]["parameters"]["properties"], {})
```

- [ ] **Step 2: Add a failing single-battle normalization test.**

```python
responses = [
    {"content": '{"name":"list_legal_actions","arguments":{"battler_id":0}}'},
    {"content": '{"name":"choose_actions","arguments":{"actions":[{"battler_id":1,"action_index":1}]}}'},
]
with mock.patch("battle_agent_service.request_ollama", side_effect=responses), mock.patch("battle_agent_service.log") as log:
    selected = run_tool_agent(7, 3, (1,), 2, self.actions_by_battler, bytes(_v4_payload()))
self.assertEqual(selected.actions, ((1, 1),))
log.assert_any_call("request 7 normalized list_legal_actions arguments: argument_keys=['battler_id']")
```

- [ ] **Step 3: Add a failing double-battle normalization test for an invented `controlled_battlers` argument.**

```python
responses = [
    {"content": '{"name":"list_legal_actions","arguments":{"controlled_battlers":[1,3]}}'},
    {"content": '{"name":"choose_actions","arguments":{"actions":[{"battler_id":1,"action_index":0},{"battler_id":3,"action_index":0}]}}'},
]
```

- [ ] **Step 4: Run the focused test file and confirm both normalization cases fail against the strict dispatch.**

Run: `py -3 -m unittest discover -s tools\mgba-bridge\tests -p test_battle_agent_service.py -q`
Expected: FAIL because the current schema advertises `battler_id` and the service returns `None` for both argument shapes.

### Task 2: Normalize only the safe read-only query

**Files:**
- Modify: `tools/mgba-bridge/battle_agent_service.py`
- Test: `tools/mgba-bridge/tests/test_battle_agent_service.py`

- [ ] **Step 1: Change the `list_legal_actions` schema to a no-property object.**

```python
{"parameters": {"type": "object", "properties": {}}}
```

- [ ] **Step 2: Replace the strict list-query branch with normalization.**

```python
elif name == "list_legal_actions":
    if arguments:
        log(f"request {sequence} normalized list_legal_actions arguments: argument_keys={sorted(arguments)!r}")
    result = list_legal_actions(actions_by_battler, payload=payload)
```

- [ ] **Step 3: Run the focused suite.**

Run: `py -3 -m unittest discover -s tools\mgba-bridge\tests -p test_battle_agent_service.py -q`
Expected: all focused tests pass, including existing internal scoped-query and strict terminal-validation coverage.

### Task 3: Verify and document Phase 14

**Files:**
- Modify: `docs/openai-battle-agent/integration-plan.md`
- Modify: `docs/openai-battle-agent/specs/2026-08-06-phase-14-legal-action-query-normalization.md`
- Modify: `docs/openai-battle-agent/reviews/2026-08-06-phase-14-legal-action-query-normalization-flow-review.md`
- Modify: `docs/openai-battle-agent/plans/2026-08-06-phase-14-legal-action-query-normalization.md`

- [ ] **Step 1: Add Phase 14 links to the roadmap.**

- [ ] **Step 2: Run the full Python bridge suite.**

Run: `py -3 -m unittest discover -s tools/mgba-bridge/tests -q`
Expected: all tests pass.

- [ ] **Step 3: Manually test a normal single, intentional trainer double, and two-trainer double.**

Expected: an incorrect `list_legal_actions` argument logs normalization and still permits a later legal decision. Invalid final actions, timeout, disconnection, and unrelated unsupported tools retain their current diagnostics and vanilla fallback.

**Compatibility and exit criteria:** No ROM rebuild is needed because this is Python-service-only. No tool other than `list_legal_actions`, no action validation, and no fallback branch may become more permissive. Exit after fresh Python-test evidence and manual logs show normalized calls in all three battle modes.
