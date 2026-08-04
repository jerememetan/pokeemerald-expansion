# Phase 9 Local Ollama Model Selection Implementation Plan

> **For agentic workers:** Execute this plan task-by-task in this session. Each code change must be test-first and preserve the local-only, vanilla-fallback contract.

**Goal:** Let a PowerShell user choose one installed Ollama model with arrow keys before the battle-agent service connects to mGBA.

**Specification:** [Phase 9 specification](../specs/2026-08-04-phase-9-local-model-selection.md)
**Flow review:** [Phase 9 flow review](../reviews/2026-08-04-phase-9-local-model-selection-flow-review.md)
**Evidence:** [Phase 9 verification evidence](../reviews/2026-08-04-phase-9-local-model-selection-evidence.md)

**Architecture:** Resolve a model in `main` before `serve` opens the loopback socket. Keep parsing, defaulting, and menu navigation pure and testable. Pass the chosen `model: str` down to `request_ollama`; do not use mutable global model state.

**Tech Stack:** Python standard library (`argparse`, `subprocess`, `sys`, `msvcrt`), existing `unittest` bridge suite, local Ollama HTTP endpoint, mGBA loopback socket.

---

### Task 1: Add failing selector tests

**Files:**
- Modify: `tools/mgba-bridge/tests/test_battle_agent_service.py`
- Modify: `tools/mgba-bridge/battle_agent_service.py`

- [ ] Import `parse_ollama_model_list`, `default_model_index`, and `advance_model_index` into the service test module.
- [ ] Add these failing tests:

```python
def test_model_list_parser(self):
    output = "NAME ID SIZE MODIFIED\nqwen2.5-coder:7b abc 4.7 GB now\nllama3.2:3b def 2.0 GB now\n"
    self.assertEqual(parse_ollama_model_list(output), ("qwen2.5-coder:7b", "llama3.2:3b"))

def test_default_and_wrapping_selection(self):
    self.assertEqual(default_model_index(("llama3.2:3b", "qwen2.5-coder:7b")), 1)
    self.assertEqual(advance_model_index(0, -1, 2), 1)
    self.assertEqual(advance_model_index(1, 1, 2), 0)
```

- [ ] Run `py -3 -m unittest discover -s tools/mgba-bridge/tests -q`.
- [ ] Expected result before implementation: import failure for the selector functions.

### Task 2: Implement discovery and selection primitives

**Files:**
- Modify: `tools/mgba-bridge/battle_agent_service.py`
- Test: `tools/mgba-bridge/tests/test_battle_agent_service.py`

- [ ] Add `PREFERRED_OLLAMA_MODEL = "qwen2.5-coder:7b"`, parser/default/wrap functions, and `discover_ollama_models()` using `subprocess.run(["ollama", "list"], check=True, capture_output=True, text=True)`.
- [ ] The parser ignores blank lines and the `NAME` header, returning only the first whitespace-delimited field of each model row.
- [ ] Convert missing command, failed command, and zero models into `ModelSelectionError("No local Ollama models found. Run 'ollama list' or 'ollama pull <model>'.")` before `serve` is called.
- [ ] Add mocked tests for normal output, header-only output, `OSError`, and `CalledProcessError`.
- [ ] Run the bridge suite. Expected: new selector tests pass with no Ollama process or mGBA required.

### Task 3: Implement interactive and noninteractive selection

**Files:**
- Modify: `tools/mgba-bridge/battle_agent_service.py`
- Test: `tools/mgba-bridge/tests/test_battle_agent_service.py`

- [ ] Implement `select_ollama_model(models, *, interactive, read_key, write_line) -> str`.
- [ ] In Windows interactive mode, render `>` on the selected model. Map `msvcrt.getwch()` extended Up/Down keys through `advance_model_index`; Enter returns the selected model; Ctrl+C propagates `KeyboardInterrupt`.
- [ ] For noninteractive streams, return the preferred model if present, otherwise the first model, without reading input. For other interactive systems, use a numbered line prompt with the same default.
- [ ] Test Down/Enter, Up/Enter wraparound, noninteractive no-key reads, and propagated `KeyboardInterrupt` using injected readers.
- [ ] Run the bridge suite. Expected: all selector and existing service tests pass.

### Task 4: Thread the model through request handling

**Files:**
- Modify: `tools/mgba-bridge/battle_agent_service.py`
- Modify: `tools/mgba-bridge/tests/test_battle_agent_service.py`

- [ ] Change request functions to receive `model: str` explicitly:

```python
request_ollama(model: str, messages: list[dict[str, object]])
run_tool_agent(model: str, sequence: int, ...)
handle_request_frame(model: str, frame: bytes)
_serve_connection(model: str, connection: socket.socket)
serve(model: str, host: str = LOOPBACK_HOST, port: int = 57621)
```

- [ ] Add `--model`; when present, it skips discovery/menu and is passed exactly to `serve`. Otherwise `main` discovers and selects before calling `serve`.
- [ ] Update mocks and add a request-body assertion that the selected model becomes the existing JSON `model` field.
- [ ] Run `py -3 -m unittest discover -s tools/mgba-bridge/tests -q`. Expected: all tests pass.

### Task 5: Verify compatibility and document launch

**Files:**
- Modify: `docs/openai-battle-agent/phase-8-handoff.md`
- Create: `docs/openai-battle-agent/reviews/2026-08-04-phase-9-local-model-selection-evidence.md`
- Modify: `docs/openai-battle-agent/integration-plan.md`

- [ ] Document `py -3 tools\\mgba-bridge\\battle_agent_service.py`, `py -3 tools\\mgba-bridge\\battle_agent_service.py --model qwen2.5-coder:7b`, and `ollama list`.
- [ ] Document that Ctrl+C at the menu exits before connecting; Ctrl+C after connecting leaves the existing ROM timeout/vanilla fallback unchanged.
- [ ] Run `py -3 -m unittest discover -s tools/mgba-bridge/tests -q`, `git diff --check`, `make -j16 check TESTS='External AI'`, and `make -j16`.
- [ ] Expected: every bridge test, External AI test, and normal ROM build passes.
- [ ] Manual PowerShell smoke test: confirm preferred highlight, both arrow directions, Enter, `--model`, Ctrl+C before connection, selected-model battle, and absent-service fallback.

### Task 6: Increase the local-model service deadline

**Files:**
- Modify: `tools/mgba-bridge/battle_agent_service.py`
- Modify: `tools/mgba-bridge/tests/test_battle_agent_service.py`

- [ ] Add a failing test that asserts `SERVICE_TIMEOUT_SECONDS == 20.0`.
- [ ] Change the one shared service deadline from `12.0` to `20.0`; do not alter the ROM timeout, mailbox, Lua bridge, or fallback code.
- [ ] Run the bridge suite. Expected: the 20-second assertion and all existing tests pass.

### Task 7: Highlight accepted decisions in the terminal

**Files:**
- Modify: `tools/mgba-bridge/battle_agent_service.py`
- Modify: `tools/mgba-bridge/tests/test_battle_agent_service.py`

- [ ] Add failing tests for a formatter that colors only `selected:` and selected ROM-facts audit lines when ANSI is enabled, and leaves all lines unchanged when it is disabled.
- [ ] Implement the formatter at the `log` boundary using bright-green/bold ANSI escapes and reset escapes; keep `format_decision_audit` plain text.
- [ ] Run the bridge suite. Expected: highlighted and plain-text tests plus all existing tests pass.

## Plan self-review

- **Coverage:** Tasks 1–3 cover discovery, defaults, arrow navigation, cancellation, errors, and noninteractive behavior; Task 4 covers exact model propagation and `--model`; Task 5 supplies documentation and exit evidence.
- **Type consistency:** discovery yields `tuple[str, ...]`, selection returns `str`, and every request path receives that `str`.
- **Scope:** No ROM, Lua, mailbox, action-validation, model-download, persistence, or cloud-provider changes.
- **No placeholders:** exact files, interfaces, commands, expected outcomes, and manual acceptance criteria are present.
