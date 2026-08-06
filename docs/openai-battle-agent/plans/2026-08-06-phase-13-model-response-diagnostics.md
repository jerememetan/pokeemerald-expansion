# Phase 13 Model-Response Diagnostics Implementation Plan

**Goal:** Emit actionable, bounded Python-service diagnostics for every invalid or expired model decision while preserving all decision and fallback behavior.

**Architecture:** Keep `extract_tool_call` as the sole acceptance gate. Add pure helpers that describe an already-rejected response and format a safe preview. `run_tool_agent` logs those results immediately before following its existing retry/`None` paths; it also logs elapsed time at the existing outer deadline.

**Tech Stack:** Python 3 standard library (`json`, `time`), existing `unittest`/`mock`, Ollama local `/api/chat` endpoint, mGBA bridge.

---

### Task 1: Add failing diagnostic-contract tests

**Files:**
- Modify: `tools/mgba-bridge/tests/test_battle_agent_service.py`
- Test: `tools/mgba-bridge/tests/test_battle_agent_service.py`

- [ ] **Step 1: Import the planned `describe_malformed_tool_call` and assert the parser categories.**

```python
describe = getattr(battle_agent_service, "describe_malformed_tool_call", lambda _: "helper_missing")

def test_malformed_tool_diagnostic_classifies_parser_failures(self) -> None:
    self.assertEqual(describe({"tool_calls": []}), "native_tool_calls_count=0")
    self.assertEqual(describe({"content": "not json"}), "content_invalid_json")
    self.assertEqual(describe({"content": '{"name":"get_battle_state","arguments":{},"extra":true}'}), "content_unexpected_keys")
    self.assertEqual(describe({"content": '{"name":"choose_actions","arguments":[]}'}), "valid")
```

- [ ] **Step 2: Add a failing bounded-preview test.**

```python
preview_response = getattr(battle_agent_service, "format_model_response_preview", lambda _: "helper_missing")

def test_model_response_preview_is_single_line_and_bounded(self) -> None:
    preview = preview_response({"content": "first\\n" + "x" * 300})
    self.assertNotEqual(preview, "helper_missing")
    self.assertNotIn("\\n", preview)
    self.assertLessEqual(len(preview), 240)
```

- [ ] **Step 3: Add failing tool-loop logging tests.**

```python
with mock.patch("battle_agent_service.request_ollama", return_value={"content": "not json"}), mock.patch("battle_agent_service.log") as log:
    self.assertIsNone(run_tool_agent(7, 3, (1,), 2, self.actions_by_battler, bytes(_v4_payload())))
log.assert_any_call("request 7 malformed tool call: content_invalid_json; response='not json'; retrying once")
```

```python
with mock.patch("battle_agent_service.time.monotonic", side_effect=[0.0, 45.2]), mock.patch("battle_agent_service.log") as log:
    self.assertIsNone(run_tool_agent(7, 3, (1,), 2, self.actions_by_battler, bytes(_v4_payload())))
log.assert_any_call("request 7 exchange deadline reached after 45.2s")
```

- [ ] **Step 4: Run the focused suite and confirm it fails because the helpers and diagnostics do not exist.**

Run: `py -3 -m unittest discover -s tools\mgba-bridge\tests -p test_battle_agent_service.py -q`
Expected: FAIL with missing helper imports/assertions and missing diagnostic log calls.

### Task 2: Add diagnostics without changing acceptance behavior

**Files:**
- Modify: `tools/mgba-bridge/battle_agent_service.py`
- Test: `tools/mgba-bridge/tests/test_battle_agent_service.py`

- [ ] **Step 1: Add `describe_malformed_tool_call(message)` that mirrors every `extract_tool_call` rejection branch and returns a stable category string.**

```python
if not isinstance(content, str):
    return "content_missing" if content is None else "content_not_string"
try:
    compatibility_call = json.loads(content)
except json.JSONDecodeError:
    return "content_invalid_json"
if not isinstance(compatibility_call, dict):
    return "content_not_object"
if set(compatibility_call) != {"name", "arguments"}:
    return "content_unexpected_keys"
```

- [ ] **Step 2: Add `format_model_response_preview(message)` that uses the assistant content when present, otherwise the response representation; it replaces CR/LF with spaces and truncates the returned string to 240 characters.**

```python
content = message.get("content")
preview = repr(content) if isinstance(content, str) else repr(message)
return preview.replace("\r", " ").replace("\n", " ")[:MODEL_RESPONSE_PREVIEW_LIMIT]
```

- [ ] **Step 3: When `extract_tool_call` returns `None`, log the category and preview before the existing one-retry or `None` path.**

- [ ] **Step 4: Log `request {sequence} exchange deadline reached after {elapsed:.1f}s` before the existing outer-loop `None` return.**

- [ ] **Step 5: Before returning `None` for a parsed unsupported tool, log `request {sequence} unsupported tool call: name={name!r}, argument_keys={sorted(arguments)!r}`.**

- [ ] **Step 6: Run the focused suite and confirm all diagnostics and previous parser/validation tests pass.**

Run: `py -3 -m unittest discover -s tools\mgba-bridge\tests -p test_battle_agent_service.py -q`
Expected: all focused tests pass.

### Task 3: Verify and document Phase 13

**Files:**
- Modify: `docs/openai-battle-agent/integration-plan.md`
- Modify: `docs/openai-battle-agent/specs/2026-08-06-phase-13-model-response-diagnostics.md`
- Modify: `docs/openai-battle-agent/reviews/2026-08-06-phase-13-model-response-diagnostics-flow-review.md`
- Modify: `docs/openai-battle-agent/plans/2026-08-06-phase-13-model-response-diagnostics.md`

- [ ] **Step 1: Add Phase 13 to the roadmap with links to these documents.**

- [ ] **Step 2: Run the full Python bridge suite.**

Run: `py -3 -m unittest discover -s tools/mgba-bridge/tests -q`
Expected: all tests pass.

- [ ] **Step 3: Run External AI ROM tests and a normal ROM build.**

Run: `make -j16 check TESTS='External AI'`
Expected: all External AI tests pass.

Run: `make -j16`
Expected: `pokeemerald.gba` builds successfully.

- [ ] **Step 4: Manually reproduce a malformed response or inspect the next fallback.**

Expected: each fallback is preceded by a reason such as `content_invalid_json`, `native_tool_calls_count=2`, a typed unsupported-tool line, a `choose_actions` validation error, or the measured exchange deadline. A valid single or double decision has no diagnostic line and remains applied exactly as before.

**Compatibility and exit criteria:** The only runtime change is console logging. No external action, retry count, parser acceptance, timeout, protocol, or ROM behavior may change. Exit only after fresh test/build evidence and a manual log confirms a specific reason before fallback.
