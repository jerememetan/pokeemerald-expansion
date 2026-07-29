# Phase 4A Bounded Local-Model Format Retry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` or inline execution task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the local Ollama agent recover once from a malformed tool-call reply while preserving strict command parsing and the ROM's vanilla-AI fallback.

**Architecture:** `run_tool_agent` will retain its 12-iteration, 12-second bounded loop. When `extract_tool_call` returns `None` for the first time, it will append a fixed correction system message and continue; every subsequent response still uses the existing parser, tool dispatcher, and terminal `choose_action` validation. No binary protocol, Lua code, ROM code, tool schema, or model authority changes.

**Tech Stack:** Python 3 standard library, `unittest`, existing fake Ollama request seam, local Ollama `/api/chat`.

---

## File structure

- Modify `tools/mgba-bridge/battle_agent_service.py` — add a constant correction message and a one-time parser-failure retry branch inside `run_tool_agent`.
- Modify `tools/mgba-bridge/tests/test_battle_agent_service.py` — simulate malformed and corrected model replies through the existing `request_ollama` patch seam.
- Modify `tools/mgba-bridge/README.md` — record that malformed model output gets one bounded correction attempt and all other failures still use vanilla fallback.
- Create `docs/openai-battle-agent/reviews/2026-07-29-phase-4a-model-format-retry-evidence.md` — record automated and live verification after the implementation.

## Task 1: Prove one malformed reply is recoverable

**Files:**

- Modify: `tools/mgba-bridge/tests/test_battle_agent_service.py`

- [ ] **Step 1: Write the failing recovery test.**

  Add a test beside the existing compatibility tests that patches `request_ollama` with these four replies in order:

  ```python
  {"role": "assistant", "content": '{"name": get_battle_state, "arguments": {}}'},
  {"role": "assistant", "content": '{"name": "list_legal_actions", "arguments": {}}'},
  {"role": "assistant", "content": '{"name": "choose_action", "arguments": {"action_index": 1}}'},
  ```

  Call `run_tool_agent(7, 3, 0, actions, payload)` using the module's existing fixture action tuple and payload. Assert it returns `1`, `request_ollama` was called three times, and the third request contains the existing legal-action tool result. This proves the malformed reply itself was not executed and the later choice remains legal.

- [ ] **Step 2: Write the failing repeated-malformed test.**

  Patch `request_ollama` with two malformed pseudo-JSON replies. Assert `run_tool_agent(...) is None` and that it makes exactly two requests. This proves there is one retry, not an unbounded correction loop.

- [ ] **Step 3: Run the focused test module and confirm RED.**

  Run:

  ```powershell
  py -3 -m unittest discover -s tools/mgba-bridge/tests -p test_battle_agent_service.py -v
  ```

  Expected: the recovery test fails because the current implementation returns `None` after the first malformed reply; the repeated-malformed test may already pass.

## Task 2: Add the minimal bounded retry

**Files:**

- Modify: `tools/mgba-bridge/battle_agent_service.py`
- Test: `tools/mgba-bridge/tests/test_battle_agent_service.py`

- [ ] **Step 1: Define the constant correction message.**

  Next to `MAX_TOOL_CALLS`, define:

  ```python
  FORMAT_RETRY_MESSAGE = (
      "Your previous reply was not a valid tool call. Reply with exactly one "
      "supported tool call; do not answer in prose or malformed JSON."
  )
  ```

- [ ] **Step 2: Add one retry state variable.**

  At the start of `run_tool_agent`, directly after `started = time.monotonic()`, define:

  ```python
  format_retry_used = False
  ```

- [ ] **Step 3: Replace the existing immediate parser-failure return.**

  Replace:

  ```python
  if tool_call is None:
      return None
  ```

  with:

  ```python
  if tool_call is None:
      if format_retry_used:
          return None
      format_retry_used = True
      log(f"request {sequence} retrying malformed tool call")
      messages.append({"role": "system", "content": FORMAT_RETRY_MESSAGE})
      continue
  ```

  Do not alter `extract_tool_call`, tool schemas, argument validation, exception handling, the monotonic deadline, or `choose_action` validation. Because this is inside the existing `for _ in range(MAX_TOOL_CALLS)` loop, malformed output consumes one bounded model iteration.

- [ ] **Step 4: Run focused tests and confirm GREEN.**

  Run:

  ```powershell
  py -3 -m unittest discover -s tools/mgba-bridge/tests -p test_battle_agent_service.py -v
  ```

  Expected: recovery, repeated-malformed, strict compatibility, invalid argument, timeout, and legal-choice tests all pass.

## Task 3: Verify compatibility, fallback, and live connection

**Files:**

- Modify: `tools/mgba-bridge/README.md`
- Create: `docs/openai-battle-agent/reviews/2026-07-29-phase-4a-model-format-retry-evidence.md`

- [ ] **Step 1: Document the behavior.**

  In the service diagnostics/fallback section of `tools/mgba-bridge/README.md`, state that one malformed model tool-call reply receives one correction request, but a second malformed reply, endpoint failure, invalid command, timeout, or no legal choice sends no response and preserves vanilla fallback.

- [ ] **Step 2: Run all Python checks and source hygiene.**

  Run:

  ```powershell
  py -3 -m unittest discover -s tools/mgba-bridge/tests -v
  git diff --check
  ```

  Expected: all tests pass, including the bridge source-contract suite; `git diff --check` emits no output.

- [ ] **Step 3: Perform the live smoke test.**

  In mGBA Scripting choose **File → Reset**, then load `tools/mgba-bridge/mgba_bridge.lua` exactly once. Restart `py -3 tools/mgba-bridge/battle_agent_service.py` after the Lua listener is ready. Fight Calvin and verify:

  ```text
  BAGB client connected
  BAGB request forwarded: N
  BAGB response written: N
  ```

  and service output contains either normal tool calls or one `retrying malformed tool call` followed by a legal `chose action`. Confirm Calvin performs the corresponding legal move before the ROM deadline. Stop the service once and confirm vanilla fallback remains responsive.

- [ ] **Step 4: Record evidence and update the parent links.**

  Write the exact automated command results, the 425-byte live-frame parsing evidence, the pre-fix action-padding rejection, the successful post-fix response log, and the fallback observation in the evidence file. Link that file from the parent Phase 4A specification and roadmap only after all exit criteria pass.

- [ ] **Step 5: Commit the narrow slice.**

  Run:

  ```powershell
  git add tools/mgba-bridge/battle_agent_service.py tools/mgba-bridge/tests/test_battle_agent_service.py tools/mgba-bridge/README.md docs/openai-battle-agent/specs/2026-07-29-phase-4a-model-format-retry.md docs/openai-battle-agent/reviews/2026-07-29-phase-4a-model-format-retry-flow-review.md docs/openai-battle-agent/reviews/2026-07-29-phase-4a-model-format-retry-evidence.md docs/openai-battle-agent/plans/2026-07-29-phase-4a-model-format-retry.md
  git commit -m "fix(agent): retry one malformed local tool call"
  ```

## Compatibility and fallback checklist

- The fixed 425-byte request, 13-byte response, V2 wire order, Lua listener, ROM response checks, and 900-frame fallback remain unchanged.
- The service still accepts only native calls or strict exact JSON content; it never repairs malformed content.
- Only one malformed parser failure retries; all invalid commands and endpoint/deadline errors remain no-response paths.
- The retry is bounded by the existing 12 model-loop iterations and 12-second monotonic deadline.
- The returned terminal action remains a current ROM-provided legal index, with ROM-side target normalization and fallback unchanged.

## Self-review

- **Specification coverage:** Task 1 covers one-retry and repeated-malformed cases; Task 2 implements only the specified state and message; Task 3 verifies docs, automated compatibility, live response, and fallback.
- **Terminology and types:** The plan consistently uses `extract_tool_call`, `run_tool_agent`, `MAX_TOOL_CALLS`, `FORMAT_RETRY_MESSAGE`, strict JSON content, legal action index, 12-second deadline, and 900-frame ROM fallback.
- **Protocol/mechanics safety:** No task changes wire bytes, Lua memory reads/writes, ROM action application, tools, move targeting, or damage mechanics.
- **Scope:** The plan is a service-only reliability correction; it excludes broader trainer coverage, switching, items, doubles, and any parser relaxation.

## Links

- [Specification](../specs/2026-07-29-phase-4a-model-format-retry.md)
- [Flow review](../reviews/2026-07-29-phase-4a-model-format-retry-flow-review.md)
- [Parent Phase 4A plan](2026-07-29-phase-4a-local-ollama-tool-agent.md)
