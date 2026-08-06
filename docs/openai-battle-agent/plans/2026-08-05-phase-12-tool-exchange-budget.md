# Phase 12 Tool-Exchange Time Budget Implementation Plan

**Goal:** Allow a valid multi-call local-model decision up to 45 seconds while limiting every individual Ollama HTTP response to 20 seconds.

**Architecture:** `battle_agent_service.py` receives two explicit service constants. The HTTP adapter uses `OLLAMA_RESPONSE_TIMEOUT_SECONDS`; the outer tool-agent loop measures `TOOL_EXCHANGE_TIMEOUT_SECONDS`. All bridge, action validation, and fallback paths remain unchanged.

**Tech Stack:** Python 3 standard library (`time`, `urllib`), existing `unittest`/`mock`, Ollama local `/api/chat` endpoint, mGBA bridge.

---

### Task 1: Lock the independent timing contract with tests

**Files:**
- Modify: `tools/mgba-bridge/tests/test_battle_agent_service.py`
- Test: `tools/mgba-bridge/tests/test_battle_agent_service.py`

- [ ] **Step 1: Add an import of the service module and a failing named-deadline assertion**

```python
import battle_agent_service

def test_service_uses_separate_response_and_exchange_deadlines(self) -> None:
    self.assertEqual(getattr(battle_agent_service, "OLLAMA_RESPONSE_TIMEOUT_SECONDS", None), 20.0)
    self.assertEqual(getattr(battle_agent_service, "TOOL_EXCHANGE_TIMEOUT_SECONDS", None), 45.0)
```

- [ ] **Step 2: Add the cumulative-time regression test**

```python
def test_tool_loop_allows_a_valid_choice_after_twenty_seconds_but_before_exchange_deadline(self) -> None:
    payload = bytes(_v4_payload())
    responses = [
        {"content": '{"name":"get_battle_state","arguments":{}}'},
        {"content": '{"name":"list_legal_actions","arguments":{}}'},
        {"content": '{"name":"choose_actions","arguments":{"actions":[{"battler_id":1,"action_index":0}]}}'},
    ]
    with mock.patch("battle_agent_service.request_ollama", side_effect=responses) as request, mock.patch(
        "battle_agent_service.time.monotonic", side_effect=[0.0, 0.0, 20.1, 21.0]
    ):
        selected = run_tool_agent(7, 3, (1,), 2, self.actions_by_battler, payload)
    expected = AgentDecision(((1, 0),), ("get_battle_state", "list_legal_actions", "choose_actions"))
    self.assertEqual(selected, expected)
    self.assertEqual(request.call_count, 3)
```

- [ ] **Step 3: Add the over-budget fallback regression test**

```python
def test_tool_loop_keeps_vanilla_fallback_after_the_exchange_deadline(self) -> None:
    payload = bytes(_v4_payload())
    response = {"content": '{"name":"get_battle_state","arguments":{}}'}
    with mock.patch("battle_agent_service.request_ollama", return_value=response) as request, mock.patch(
        "battle_agent_service.time.monotonic", side_effect=[0.0, 0.0, 45.0]
    ):
        selected = run_tool_agent(7, 3, (1,), 2, self.actions_by_battler, payload)
    self.assertIsNone(selected)
    self.assertEqual(request.call_count, 1)
```

- [ ] **Step 4: Run the focused suite and confirm the new assertions fail under the old shared 20-second guard**

Run: `py -3 -m unittest discover -s tools\mgba-bridge\tests -p test_battle_agent_service.py -q`
Expected: the named-deadline assertion fails because the new constants do not exist, and the cumulative-time test fails because the loop exits when its elapsed time reaches `20.1` seconds.

### Task 2: Split the service deadlines minimally

**Files:**
- Modify: `tools/mgba-bridge/battle_agent_service.py`
- Test: `tools/mgba-bridge/tests/test_battle_agent_service.py`

- [ ] **Step 1: Define the two explicit constants**

```python
OLLAMA_RESPONSE_TIMEOUT_SECONDS = 20.0
TOOL_EXCHANGE_TIMEOUT_SECONDS = 45.0
```

- [ ] **Step 2: Use the response constant only for the HTTP adapter**

```python
with urlopen(request, timeout=OLLAMA_RESPONSE_TIMEOUT_SECONDS) as response:
```

- [ ] **Step 3: Use the exchange constant only for the outer decision loop**

```python
if time.monotonic() - started >= TOOL_EXCHANGE_TIMEOUT_SECONDS:
    return None
```

- [ ] **Step 4: Run the focused suite and confirm it passes**

Run: `py -3 -m unittest discover -s tools\mgba-bridge\tests -p test_battle_agent_service.py -q`
Expected: all focused tests pass, including the cumulative-time case and pre-existing malformed/invalid/fallback tests.

### Task 3: Verify compatibility and record the phase

**Files:**
- Modify: `docs/openai-battle-agent/integration-plan.md`
- Modify: `docs/openai-battle-agent/specs/2026-08-05-phase-12-tool-exchange-budget.md`
- Modify: `docs/openai-battle-agent/reviews/2026-08-05-phase-12-tool-exchange-budget-flow-review.md`
- Modify: `docs/openai-battle-agent/plans/2026-08-05-phase-12-tool-exchange-budget.md`

- [ ] **Step 1: Add Phase 12 to the roadmap with links to this specification, flow review, and plan.**

- [ ] **Step 2: Run the full bridge test suite.**

Run: `py -3 -m unittest discover -s tools/mgba-bridge/tests -q`
Expected: all tests pass.

- [ ] **Step 3: Run the external-AI ROM test subset and normal ROM build.**

Run: `make -j16 check TESTS='External AI'`
Expected: all External AI tests pass.

Run: `make -j16`
Expected: `pokeemerald.gba` is produced successfully.

- [ ] **Step 4: Manually verify a normal single, an intentional trainer double, and a two-trainer double.**

Expected: a valid decision that completes before 45 seconds is applied; unavailable, individually timed-out, malformed, or over-budget service responses still yield the established vanilla-AI action without a freeze beyond the current waiting path.

**Compatibility and exit criteria:** No mailbox, Lua, ROM, tool schema, trainer-tag, action-validation, or fallback change is allowed. Phase 12 exits only when the fresh test/build evidence and all three manual battle types pass.
