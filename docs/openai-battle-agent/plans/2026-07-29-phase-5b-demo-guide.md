# Phase 5B Manual Demo Guide and Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` (recommended) or inline task execution. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the existing manual Calvin demonstration into a concise,
repeatable README workflow with source-accurate success logs and safe recovery
instructions, without changing runtime behavior.

**Architecture:** The checked-in bridge README is the sole operator surface.
It will describe the existing WSL build, local Ollama, Python service, mGBA
Lua, and ROM boundaries in their required manual order. Current source and
tests remain the authority for commands, logs, one-client behavior, response
validation, and fallback; no ROM, Lua, Python, protocol, or launcher file is
modified.

**Tech Stack:** Markdown, PowerShell, WSL/Make, Python `unittest`, mGBA Lua,
local Ollama, existing Phase 4A/4B/5A evidence.

**Specification:** [Phase 5B manual demo guide](../specs/2026-07-29-phase-5b-demo-guide.md)

**Flow review:** [Phase 5B demo-guide flow review](../reviews/2026-07-29-phase-5b-demo-guide-flow-review.md)

---

## File structure

- Modify `tools/mgba-bridge/README.md`: replace the current broad Phase 4A
  guide with the exact manual build, launch, observable-log, fallback, and
  recovery workflow.
- Modify `docs/openai-battle-agent/2026-07-18-mgba-ai-trainer-design.md`:
  link the completed Phase 5B artifacts and mark the remaining Phase 5 demo
  hardening exit criterion complete only after fresh evidence exists.
- Create `docs/openai-battle-agent/reviews/2026-07-29-phase-5b-demo-guide-evidence.md`:
  record command output, source-contract verification, the connected and
  fallback manual results, and the final exit-criterion assessment.

No production or test source files change. Existing
`tools/mgba-bridge/tests/test_battle_agent_service.py`,
`tools/mgba-bridge/tests/test_mgba_bridge_source.py`, and
`test/battle/ai.c` are regression evidence, not modified tests.

## Task 1: Capture the source-accurate operator contract before editing prose

**Files:**

- Read: `tools/mgba-bridge/battle_agent_service.py:323-378`
- Read: `tools/mgba-bridge/mgba_bridge.lua:73-86,155-163,232,268,276,322,365,389`
- Read: `tools/mgba-bridge/README.md`
- Test: `tools/mgba-bridge/tests/test_battle_agent_service.py`
- Test: `tools/mgba-bridge/tests/test_mgba_bridge_source.py`

- [ ] **Step 1: Run the focused Python source/transport regression tests before changing documentation.**

  Run from PowerShell:

  ```powershell
  py -3 -m unittest tools.mgba-bridge.tests.test_battle_agent_service tools.mgba-bridge.tests.test_mgba_bridge_source -v
  ```

  Expected: every discovered focused test passes. If Python cannot resolve the
  hyphenated directory as a module, use the repository-supported discovery
  command instead:

  ```powershell
  py -3 -m unittest discover -s tools\mgba-bridge\tests -p "test_battle_agent_service.py" -v
  py -3 -m unittest discover -s tools\mgba-bridge\tests -p "test_mgba_bridge_source.py" -v
  ```

  Record the actual pass counts. Do not edit the README until the established
  service and Lua log contract is known to pass.

- [ ] **Step 2: Record the exact source-backed strings that the guide may present as expected output.**

  Verify these literals in the current source:

  ```powershell
  rg -n 'connecting to mGBA|mGBA bridge connected|request .* received|request .* chose action|audit #|produced no response' tools\mgba-bridge\battle_agent_service.py
  rg -n 'BAGB listener ready|BAGB client connected|BAGB request forwarded|BAGB response written|BAGB response rejected|BAGB client disconnected' tools\mgba-bridge\mgba_bridge.lua
  ```

  Expected: each listed diagnostic is present. Do not invent a progress log
  for the service's silent 250-ms connection retry or claim a fallback proves
  Ollama was cold.

- [ ] **Step 3: Create a documentation acceptance checklist before the README rewrite.**

  The rewritten guide must include all of these checkable facts:

  ```text
  [ ] build ROM, then regenerate mailbox_address.lua from the fresh ELF
  [ ] qwen2.5-coder:7b prerequisite and optional warm-up command
  [ ] service-first startup is allowed and waits at "connecting to mGBA"
  [ ] Lua listener-ready and both bridge-connected logs
  [ ] matching request/forwarded/response-written sequence on success
  [ ] visible thinking-status and saved-vanilla fallback behavior
  [ ] mGBA/Lua restart after a service disconnect; no listener probe/second client
  [ ] scoped recovery for model, generated-address, bind, disconnect, rejection, fallback
  [ ] exact automated regression commands and Phase artifact links
  ```

  This checklist is the test-first acceptance contract for the documentation
  change. It prevents a prose rewrite from silently omitting a boundary or
  changing runtime meaning.

## Task 2: Rewrite the manual operator guide

**Files:**

- Modify: `tools/mgba-bridge/README.md`
- Test: the Task 1 acceptance checklist and existing source-contract tests

- [ ] **Step 1: Replace the opening with a concise scope-and-safety section.**

  Preserve these facts in plain language:

  ```markdown
  - Youngster Calvin (`TRAINER_CALVIN_1`) is the only configured trainer in a standard trainer single battle.
  - The agent can inspect read-only battle data and finish only with one current ROM-authorized action index.
  - The existing trainer AI remains the fallback after at most 900 rendered frames (about 15 seconds).
  - Lua listens on `127.0.0.1:57621`; the Python service is its one client.
  ```

  Do not claim switches, items, additional trainers, double battles, model
  rationale, or automatic process startup.

- [ ] **Step 2: Write an ordered “Play the Calvin demo” section with four numbered subsections.**

  Include these exact commands, preserving the Windows/WSL boundaries:

  ```bash
  cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion
  make -j16
  python3 tools/mgba-bridge/generate_mailbox_config.py --elf pokeemerald.elf
  ```

  ```powershell
  ollama list
  ollama run qwen2.5-coder:7b "Reply with exactly READY"
  cd C:\Users\jerem\Documents\Github\pokeemerald-expansion
  py -3 tools\mgba-bridge\battle_agent_service.py
  ```

  Explain that warming is optional but recommended before a demo, and that the
  service may print `BAGB service: connecting to mGBA at 127.0.0.1:57621` and
  wait until Lua is loaded. Then instruct the reader to open the current
  `pokeemerald.gba`, choose **Tools → Scripting…**, and load
  `tools\mgba-bridge\mgba_bridge.lua` exactly once.

- [ ] **Step 3: Add a “What success looks like” log sequence and visible-game outcome.**

  Use source-accurate representative logs:

  ```text
  BAGB listener ready 127.0.0.1:57621
  BAGB client connected
  BAGB service: mGBA bridge connected
  BAGB request forwarded: 1
  BAGB service: request 1 received
  BAGB service: request 1 chose action 0
  BAGB response written: 1
  ```

  State that the request/response sequence numbers must match, the service
  audit records tools and ROM facts but not hidden model reasoning, and the
  lower battle message shows `AI is thinking...` while a reply is pending.

- [ ] **Step 4: Add a recovery table with one safe action per symptom.**

  Include exactly these rows and defaults:

  | Symptom | Meaning / safe recovery |
  | --- | --- |
  | `ollama list` lacks `qwen2.5-coder:7b` | Install/pull that configured model before starting the service. |
  | Ollama API/model is not ready | Start Ollama normally, warm the model, then begin a new Calvin demo; a first-turn fallback alone is not proof of the cause. |
  | Lua says it cannot bind/listen on `127.0.0.1:57621` | Close the previous mGBA/Lua session that owns the listener, then reopen mGBA and load the script once. |
  | Lua cannot load `generated/mailbox_address.lua` or the ROM was rebuilt | Re-run the documented generator against the fresh `pokeemerald.elf` before opening mGBA. |
  | `BAGB client disconnected`, malformed response, or response rejection | Let the current ROM wait resolve through vanilla fallback; then restart mGBA and reload Lua before starting one new Python service session. |
  | `BAGB service: ... vanilla_fallback` or no response | The ROM intentionally keeps its saved trainer-AI action. Wait for it to proceed; inspect service/Lua logs before deciding whether a new session is needed. |

  State explicitly that no one should probe port 57621, launch a second
  service, edit generated files, or send a mailbox reply manually.

- [ ] **Step 5: Add connected and fallback smoke-test checklists plus artifact links.**

  The connected checklist must require a matching `response written` sequence
  and a normal Calvin move. The fallback checklist must require stopping or
  omitting the service, observing the thinking status clear, and observing the
  saved vanilla action without a stuck battle. Link the Phase 4A, Phase 4B,
  Phase 5A, and Phase 5B specification/review/plan artifacts.

- [ ] **Step 6: Review the rewritten README against the acceptance checklist.**

  Check all nine Task 1 items manually. Expected: every checkbox is satisfied;
  no README instruction adds a process, changes a port, or implies a new
  protocol/action capability.

- [ ] **Step 7: Commit the guide-only change.**

  ```powershell
  git add tools/mgba-bridge/README.md
  git commit -m "docs(ai): harden manual demo guide"
  ```

  Expected: the commit changes only the bridge README.

## Task 3: Verify the guide and record Phase 5B evidence

**Files:**

- Create: `docs/openai-battle-agent/reviews/2026-07-29-phase-5b-demo-guide-evidence.md`
- Modify: `docs/openai-battle-agent/2026-07-18-mgba-ai-trainer-design.md`
- Test: `tools/mgba-bridge/tests/test_battle_agent_service.py`
- Test: `tools/mgba-bridge/tests/test_mgba_bridge_source.py`
- Test: `test/battle/ai.c`

- [ ] **Step 1: Run fresh automated regression commands after the README review.**

  ```powershell
  py -3 -m unittest discover -s tools\mgba-bridge\tests -v
  wsl bash -lc "cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion && make -j16 check TESTS='External AI'"
  git diff --check
  ```

  Expected: the Python suite and all focused External AI tests pass; the diff
  check prints no whitespace errors. Record actual pass counts rather than
  anticipated values.

- [ ] **Step 2: Follow the newly written connected-service checklist manually.**

  Use the current built ROM and generated mailbox address. Record the actual
  service sequence, matching Lua `response written` sequence, visible thinking
  status, and Calvin action. If the first request falls back, warm the model
  and retry only after resetting the one-client mGBA/Lua session.

- [ ] **Step 3: Follow the absent-service fallback checklist manually.**

  Stop or omit the Python service, select the player's action in Calvin's
  battle, and record that `AI is thinking...` clears as the existing saved
  vanilla trainer AI continues. Record that the emulator remains responsive
  and that no thinking status is stuck on the next turn.

- [ ] **Step 4: Create the evidence record and update the roadmap.**

  The evidence file must link this plan, its specification, and flow review;
  list the exact automated commands/results; distinguish connected and
  fallback outcomes; and state that no runtime source changed. Update Phase 5
  in the roadmap to link Phase 5B and mark its demo-hardening criterion
  complete only when both manual checks succeed.

- [ ] **Step 5: Commit the evidence-only handoff.**

  ```powershell
  git add docs/openai-battle-agent/2026-07-18-mgba-ai-trainer-design.md docs/openai-battle-agent/reviews/2026-07-29-phase-5b-demo-guide-evidence.md
  git commit -m "docs(ai): verify manual demo guide"
  ```

  Expected: this commit contains roadmap and verification evidence only.

## Plan self-review

- **Specification coverage:** Task 2 covers the manual setup, exact success
  logs, one-client recovery, scoped symptoms, connected demo, fallback demo,
  and links. Task 3 records both required manual outcomes and regression
  evidence.
- **Terminology/type consistency:** The plan uses the existing `BAGB` logs,
  `qwen2.5-coder:7b`, `127.0.0.1:57621`, mailbox V2, Youngster Calvin, and
  `AI is thinking...` names exactly as current source/docs do.
- **Protocol and mechanic compatibility:** No runtime file, port, request,
  response, trainer, legal-action, deadline, switch/item, or double-battle
  behavior changes. The existing trainer AI remains the fallback.
- **Scope control:** There is no launcher, automatic Ollama/mGBA start,
  dashboard, network service, persistent telemetry, or new health probe.
- **Placeholder scan:** This plan contains no unfinished markers; each command,
  expected outcome, source boundary, and evidence file is named explicitly.
