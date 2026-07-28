# Phase 3A: mGBA Loopback Bridge Spike Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Prove a Windows mGBA Lua bridge can round-trip a deterministic legal mailbox response over loopback without blocking emulator frames or changing vanilla trainer AI.

**Architecture:** The Phase 2 ROM remains request-only. A generated Lua config supplies the current EWRAM mailbox address from the just-built ELF; the Lua script listens only on `127.0.0.1:57621`, frame-polls one client, validates a tiny `BAGB/1` line protocol, and writes response sequence/index before `READY`. A standard-library Python responder is a deterministic client, not an AI service.

**Tech Stack:** pokeemerald-expansion C and battle-test runner; Python 3 standard library; Lua supplied by mGBA; Windows 64-bit mGBA development build `0.11-9091-c034660f0`; WSL devkitARM tools.

**Specification:** [`../specs/2026-07-28-phase-3a-mgba-loopback-bridge.md`](../specs/2026-07-28-phase-3a-mgba-loopback-bridge.md)  
**Flow review:** [`../reviews/2026-07-28-phase-3a-mgba-loopback-bridge-flow-review.md`](../reviews/2026-07-28-phase-3a-mgba-loopback-bridge-flow-review.md)

---

## File map

- Create: `tools/mgba-bridge/bridge_protocol.py` — strict 96-byte `BAGB/1` line parser/formatter shared by the responder tests.
- Create: `tools/mgba-bridge/test_responder.py` — loopback-only deterministic responder selecting index 0 only for a positive action count.
- Create: `tools/mgba-bridge/generate_mailbox_config.py` — parses `arm-none-eabi-nm -n pokeemerald.elf` and writes a build-local Lua address config.
- Create: `tools/mgba-bridge/mgba_bridge.lua` — mGBA frame-polled listener, mailbox validator, and three-field response writer.
- Create: `tools/mgba-bridge/bridge_settings.lua` — tracked loopback/port constants; contains no generated address.
- Create: `tools/mgba-bridge/tests/test_bridge_protocol.py` — Python `unittest` protocol/parser coverage.
- Create: `tools/mgba-bridge/tests/test_generate_mailbox_config.py` — symbol-parser and generated-config coverage.
- Create: `tools/mgba-bridge/README.md` — Windows setup, version pin, generation, launch order, and manual verification matrix.
- Create: `tools/mgba-bridge/generated/.gitkeep` — preserves the generated-config directory without tracking its address file.
- Modify: `.gitignore` — ignore only `tools/mgba-bridge/generated/mailbox_address.lua`.
- Modify: `include/battle_agent.h` — name `BATTLE_AGENT_RESPONSE_READY = 1`; no mailbox layout change.
- Modify: `test/test_runner_battle.c` — use the named ready value in the existing test-only response setter.
- Modify: `test/battle/ai.c` — retain/add focused proof that a ready response is cleared by the next Phase 2 publication and has no action effect.
- Modify: `docs/openai-battle-agent/2026-07-18-mgba-ai-trainer-design.md` — link Phase 3A artifacts after verification.
- Modify: `docs/openai-battle-agent/specs/2026-07-28-phase-3a-mgba-loopback-bridge.md` — update status and evidence link after verification.
- Create: `docs/openai-battle-agent/reviews/2026-07-28-phase-3a-mgba-loopback-bridge-evidence.md` — record tool versions, hashes, automated results, and mGBA manual cases.

## Task 1: Add the named response-ready contract without consuming it

**Files:**

- Modify: `include/battle_agent.h`
- Modify: `test/test_runner_battle.c`
- Modify: `test/battle/ai.c`
- Test: `test/battle/ai.c`

- [ ] **Step 1: Make the existing stale-response test express the desired ready state.**

  In `test/test_runner_battle.c`, change the test-only response writer from the raw value `1` to a named status expected to be added to the ROM contract:

  ```c
  gBattleAgentMailbox.responseStatus = BATTLE_AGENT_RESPONSE_READY;
  gBattleAgentMailbox.responseSequence = expected->testResponseSequence;
  gBattleAgentMailbox.responseLegalActionIndex = expected->testResponseLegalActionIndex;
  ```

  The existing `External AI snapshot replaces stale request` test must continue to set this ready response on turn two and assert that turn three has `NONE`, zero sequence/index, the next request sequence, and the unchanged vanilla move.

- [ ] **Step 2: Run the focused stale-response test to verify it fails to compile.**

  Run in WSL:

  ```bash
  make -j16 check TESTS='External AI snapshot replaces stale request'
  ```

  Expected: compile failure because `BATTLE_AGENT_RESPONSE_READY` is not defined.

- [ ] **Step 3: Define the response-ready value.**

  In `include/battle_agent.h`, change the response enum to:

  ```c
  enum BattleAgentResponseStatus
  {
      BATTLE_AGENT_RESPONSE_NONE,
      BATTLE_AGENT_RESPONSE_READY,
  };
  ```

  Do not modify `BattleAgent_TryPublishRequest` other than preserving its existing clear-to-`NONE` behavior. Do not add a response reader or change `aiMoveOrAction`/`aiChosenTarget`.

- [ ] **Step 4: Run the focused test and all external-AI tests.**

  ```bash
  make -j16 check TESTS='External AI snapshot replaces stale request'
  make -j16 check TESTS='External AI'
  ```

  Expected: the stale-response test passes; all External AI tests pass; an injected ready response still does not alter the emitted vanilla move.

- [ ] **Step 5: Commit the ROM contract slice.**

  ```bash
  git add include/battle_agent.h test/test_runner_battle.c test/battle/ai.c
  git commit -m "feat(battle): name AI agent response-ready status"
  ```

## Task 2: Build and test the bounded bridge transport

**Files:**

- Create: `tools/mgba-bridge/bridge_protocol.py`
- Create: `tools/mgba-bridge/tests/test_bridge_protocol.py`
- Create: `tools/mgba-bridge/test_responder.py`
- Test: `tools/mgba-bridge/tests/test_bridge_protocol.py`

- [ ] **Step 1: Write failing parser tests.**

  In `tools/mgba-bridge/tests/test_bridge_protocol.py`, use `unittest` and add tests for these exact outcomes:

  ```python
  self.assertEqual(parse_request(b"BAGB/1 REQUEST 7 3\n"), Request(7, 3))
  self.assertEqual(parse_response(b"BAGB/1 RESPONSE 7 0\n"), Response(7, 0))
  ```

  Add rejecting cases for a missing trailing newline, `BAGB/2`, a negative/signed number, non-decimal token, action count `0` or `5`, action index `4`, a 97-byte line, and an embedded NUL. Assert each raises `ProtocolError` rather than returning a partial object.

- [ ] **Step 2: Run the parser test to verify it fails.**

  ```powershell
  py -3 -B tools/mgba-bridge/tests/test_bridge_protocol.py -v
  ```

  Expected: import failure because `bridge_protocol` does not exist.

- [ ] **Step 3: Implement the protocol module.**

  Create `tools/mgba-bridge/bridge_protocol.py` with these public constants/types/functions:

  ```python
  MAX_LINE_BYTES = 96
  PROTOCOL = b"BAGB/1"

  @dataclass(frozen=True)
  class Request:
      sequence: int
      action_count: int

  @dataclass(frozen=True)
  class Response:
      sequence: int
      action_index: int

  class ProtocolError(ValueError):
      pass

  def parse_request(line: bytes) -> Request: ...
  def parse_response(line: bytes) -> Response: ...
  def format_response(sequence: int, action_index: int) -> bytes: ...
  ```

  Each parser must first reject `len(line) > MAX_LINE_BYTES`, NUL bytes, and non-ASCII before splitting on exactly one terminal newline and four ASCII-space-separated tokens. `parse_request` accepts only `BAGB/1 REQUEST <u32 decimal> <1..4 decimal>`; `parse_response` accepts only `BAGB/1 RESPONSE <u32 decimal> <0..3 decimal>`. `format_response` rejects the same out-of-range arguments and returns exactly `b"BAGB/1 RESPONSE <sequence> <index>\\n"`.

- [ ] **Step 4: Implement the deterministic responder.**

  Create `tools/mgba-bridge/test_responder.py` using the Python standard library plus `bridge_protocol`. Its `main()` accepts only optional `--port` (default `57621`), which must be an integer in `1..65535`; the destination is fixed to `127.0.0.1` and cannot be overridden. It attempts a Python-side `socket.create_connection(("127.0.0.1", port), timeout=1)` once every 250 ms until connected; this waiting is outside mGBA. For each complete bounded request line, it calls `parse_request`, writes `format_response(request.sequence, 0)`, and flushes. It closes on malformed input, EOF, or socket error. It must never bind/listen, inspect the ROM, or select an index when action count is zero.

- [ ] **Step 5: Run transport tests.**

  ```powershell
  py -3 -B tools/mgba-bridge/tests/test_bridge_protocol.py -v
  ```

  Expected: every accepted and rejected line test passes.

- [ ] **Step 6: Commit the transport slice.**

  ```bash
  git add tools/mgba-bridge/bridge_protocol.py tools/mgba-bridge/test_responder.py tools/mgba-bridge/tests/test_bridge_protocol.py
  git commit -m "feat(bridge): add deterministic loopback responder"
  ```

## Task 3: Generate a safe build-local mailbox address config

**Files:**

- Create: `tools/mgba-bridge/generate_mailbox_config.py`
- Create: `tools/mgba-bridge/tests/test_generate_mailbox_config.py`
- Create: `tools/mgba-bridge/generated/.gitkeep`
- Modify: `.gitignore`
- Test: `tools/mgba-bridge/tests/test_generate_mailbox_config.py`

- [ ] **Step 1: Write failing symbol-parser tests.**

  In `tools/mgba-bridge/tests/test_generate_mailbox_config.py`, test a parser receiving these `nm -n` lines:

  ```text
  02001234 B gBattleAgentMailbox
  ```

  It must produce `0x02001234`. Add one test each for no mailbox symbol, two mailbox symbols, and `03001234 B gBattleAgentMailbox`; each must raise `AddressConfigError`.

- [ ] **Step 2: Run the generator test to verify it fails.**

  ```powershell
  py -3 -m unittest tools/mgba-bridge/tests/test_generate_mailbox_config.py -v
  ```

  Expected: import failure because `generate_mailbox_config` does not exist.

- [ ] **Step 3: Implement config generation.**

  Create `tools/mgba-bridge/generate_mailbox_config.py` with:

  ```python
  EWRAM_START = 0x02000000
  EWRAM_END = 0x02040000
  SYMBOL = "gBattleAgentMailbox"

  class AddressConfigError(ValueError):
      pass

  def parse_mailbox_address(nm_output: str) -> int: ...
  def write_lua_config(address: int, output_path: pathlib.Path) -> None: ...
  ```

  `parse_mailbox_address` accepts only one whitespace-separated nm record whose final token is `gBattleAgentMailbox`, parses its first field as hexadecimal, and requires `EWRAM_START <= address < EWRAM_END`. `write_lua_config` writes exactly:

  ```lua
  -- Generated from the current pokeemerald.elf; do not commit or reuse after rebuilding.
  MAILBOX_ADDRESS = 0x02001234
  ```

  `main()` requires `--elf` and accepts optional `--nm` defaulting to `arm-none-eabi-nm`; it executes `[nm, "-n", elf]` with `subprocess.run(..., check=True, text=True, capture_output=True)` and writes `tools/mgba-bridge/generated/mailbox_address.lua` unless `--output` is provided.

- [ ] **Step 4: Ignore only generated addresses.**

  Add this exact line to `.gitignore`:

  ```gitignore
  /tools/mgba-bridge/generated/mailbox_address.lua
  ```

  Create `tools/mgba-bridge/generated/.gitkeep`; do not ignore the directory or tracked scripts.

- [ ] **Step 5: Run automated tests and generation against the real ELF.**

  ```powershell
  py -3 -m unittest tools/mgba-bridge/tests/test_generate_mailbox_config.py -v
  ```

  Then in WSL after `make -j16`:

  ```bash
  python3 tools/mgba-bridge/generate_mailbox_config.py --elf pokeemerald.elf
  sed -n '1,2p' tools/mgba-bridge/generated/mailbox_address.lua
  ```

  Expected: parser tests pass; generated file contains one EWRAM `MAILBOX_ADDRESS` line and remains untracked/ignored.

- [ ] **Step 6: Commit the generator slice.**

  ```bash
  git add .gitignore tools/mgba-bridge/generate_mailbox_config.py tools/mgba-bridge/tests/test_generate_mailbox_config.py tools/mgba-bridge/generated/.gitkeep
  git commit -m "feat(bridge): generate mailbox address from ELF"
  ```

## Task 4: Implement a non-blocking Lua listener bridge

**Files:**

- Create: `tools/mgba-bridge/bridge_settings.lua`
- Create: `tools/mgba-bridge/mgba_bridge.lua`
- Test: Windows mGBA scripting console

- [ ] **Step 1: Add a Lua startup probe before mailbox writes exist.**

  Create `tools/mgba-bridge/bridge_settings.lua`:

  ```lua
  BRIDGE_HOST = "127.0.0.1"
  BRIDGE_PORT = 57621
  MAX_LINE_BYTES = 96
  ```

  Create `tools/mgba-bridge/mgba_bridge.lua` that loads `bridge_settings.lua` and generated `mailbox_address.lua` from its own script directory, binds and listens only on `BRIDGE_HOST, BRIDGE_PORT`, and registers `callbacks:add("frame", on_frame)`. Its first probe version must log `BAGB listener ready 127.0.0.1:57621` and accept a client only after `listener:hasdata()` is true. It must never call `socket.connect`.

- [ ] **Step 2: Verify the Lua probe manually.**

  In Windows, install the official 64-bit development archive `0.11-9091-c034660f0` from <https://mgba.io/downloads.html>, record `Get-FileHash -Algorithm SHA256` in the evidence file, open the rebuilt `pokeemerald.gba`, then use **Tools → Scripting…** to load `mgba_bridge.lua`.

  In a separate PowerShell window run:

  ```powershell
  py -3 tools\mgba-bridge\test_responder.py
  ```

  Expected: the mGBA scripting console logs listener start then one client connection; mGBA remains interactive. If `hasdata` does not indicate a pending accept in this build, stop and amend the Phase 3A spec/plan with the documented callback alternative before adding mailbox writes.

- [ ] **Step 3: Add fixed mailbox helpers and strict line handling.**

  Add these Lua constants and helpers to `mgba_bridge.lua`:

  ```lua
  local MAGIC = 0x42414731
  local VERSION = 1
  local REQUEST_PENDING = 1
  local RESPONSE_READY = 1
  local OFFSET_MAGIC = 0
  local OFFSET_VERSION = 4
  local OFFSET_REQUEST_STATUS = 6
  local OFFSET_RESPONSE_STATUS = 7
  local OFFSET_REQUEST_SEQUENCE = 8
  local OFFSET_REQUESTING_BATTLER = 12
  local OFFSET_BATTLE_MODE = 13
  local OFFSET_LEGAL_ACTION_COUNT = 128
  local OFFSET_RESPONSE_SEQUENCE = 148
  local OFFSET_RESPONSE_ACTION_INDEX = 152
  local TRAINER_SINGLE = 1
  ```

  Implement `read_mailbox_header()`, `is_forwardable(header)`, `send_request(header)`, `parse_response_line(line)`, `response_matches_current(response)`, and `commit_response(response)`. `read_mailbox_header()` must read only the listed fields using `emu:read8`, `emu:read16`, and `emu:read32` from `MAILBOX_ADDRESS + offset`. `is_forwardable` requires magic/version, `PENDING`, requester `0..3`, trainer-single mode, and action count `1..4`.

  Keep a `forwarded_sequence` value. Send exactly `BAGB/1 REQUEST <sequence> <count>\n` once for a forwardable sequence. Buffer at most 96 bytes; discard and disconnect on embedded NUL, non-ASCII, malformed response, or overflow. Before `commit_response`, reread header and require the same current forwardable sequence and `response.action_index < legalActionCount`. Write in exactly this order:

  ```lua
  emu:write32(MAILBOX_ADDRESS + OFFSET_RESPONSE_SEQUENCE, response.sequence)
  emu:write8(MAILBOX_ADDRESS + OFFSET_RESPONSE_ACTION_INDEX, response.action_index)
  emu:write8(MAILBOX_ADDRESS + OFFSET_RESPONSE_STATUS, RESPONSE_READY)
  ```

  Process at most one accept, one receive, and one response commit in a frame. On no client/error/invalid data, return from `on_frame` without writing mailbox memory.

- [ ] **Step 4: Run the valid-response manual test.**

  Build and generate config from WSL:

  ```bash
  make -j16
  python3 tools/mgba-bridge/generate_mailbox_config.py --elf pokeemerald.elf
  ```

  Start the responder, load the Lua script, and fight Calvin. Expected: one `REQUEST` and one `READY` log for a positive-action request. Calvin still uses the vanilla expected move because Phase 3A ROM code has no response consumer.

- [ ] **Step 5: Run the bridge failure matrix manually.**

  Verify each case with Calvin while observing mGBA remains interactive:

  | Case | Setup | Expected result |
  |---|---|---|
  | No responder | Load Lua only | No response write; battle does not pause. |
  | Disconnect | Close responder after its connection | Lua logs disconnect once; later frames remain responsive. |
  | Stale | Send `BAGB/1 RESPONSE 999 0\n` from a local test client | Lua rejects it; no `READY` write. |
  | Invalid index | Send current sequence with index `4` | Lua rejects it; no `READY` write. |
  | Malformed | Send `BAGB/1 RESPONSE nope 0\n` | Lua rejects/disconnects; no arbitrary write. |
  | Wrong version | Send `BAGB/2 RESPONSE <seq> 0\n` | Lua rejects/disconnects; no arbitrary write. |

- [ ] **Step 6: Commit the Lua bridge slice.**

  ```bash
  git add tools/mgba-bridge/bridge_settings.lua tools/mgba-bridge/mgba_bridge.lua
  git commit -m "feat(bridge): add non-blocking mGBA loopback bridge"
  ```

## Task 5: Document and verify the complete spike

**Files:**

- Create: `tools/mgba-bridge/README.md`
- Modify: `docs/openai-battle-agent/2026-07-18-mgba-ai-trainer-design.md`
- Modify: `docs/openai-battle-agent/specs/2026-07-28-phase-3a-mgba-loopback-bridge.md`
- Create: `docs/openai-battle-agent/reviews/2026-07-28-phase-3a-mgba-loopback-bridge-evidence.md`

- [ ] **Step 1: Write reproducible Windows/WSL instructions.**

  `tools/mgba-bridge/README.md` must state the exact mGBA version pin, archive SHA-256, ROM build command, config-generation command, PowerShell responder command, mGBA scripting-menu action, listener address/port, and shutdown order. It must explicitly say: do not commit `generated/mailbox_address.lua`; the responder is not AI; the ROM ignores `READY` in Phase 3A; and use no interface except `127.0.0.1`.

- [ ] **Step 2: Run final automated verification.**

  In WSL:

  ```bash
  make -j16 check TESTS='External AI'
  make -j16
  ```

  In Windows PowerShell:

  ```powershell
  py -3 -B tools/mgba-bridge/tests/test_bridge_protocol.py -v
  py -3 -B tools/mgba-bridge/tests/test_generate_mailbox_config.py -v
  ```

  Expected: External AI tests pass; ROM builds; every Python parser/generator test passes.

- [ ] **Step 3: Record evidence and phase exit.**

  The evidence review must record exact mGBA archive filename/SHA-256, `mGBA.exe --version` output if available, Python version, generated mailbox address, automated command results, valid round trip, unavailable responder, disconnect, stale, invalid-index, malformed, and wrong-version outcomes. State explicitly that the ROM did not apply the response and that the vanilla fallback remained authoritative.

  Update the Phase 3A spec status to `Implemented and verified`, link the evidence review from the parent roadmap, and state the Phase 4 prerequisite: a separately specified full-snapshot local-service protocol and ROM-side response acceptance.

- [ ] **Step 4: Review scope before committing.**

  ```bash
  git diff --check
  git diff -- include/battle_agent.h src/battle_agent.c src/battle_main.c test/battle/ai.c test/test_runner_battle.c tools/mgba-bridge docs/openai-battle-agent
  ```

  Expected: no model/API key, no non-loopback listener, no hard-coded mailbox address, no response consumer, no switch/item/double behavior, and no unrelated trainer-party change.

- [ ] **Step 5: Commit documentation and evidence.**

  ```bash
  git add tools/mgba-bridge/README.md docs/openai-battle-agent/2026-07-18-mgba-ai-trainer-design.md docs/openai-battle-agent/specs/2026-07-28-phase-3a-mgba-loopback-bridge.md docs/openai-battle-agent/reviews/2026-07-28-phase-3a-mgba-loopback-bridge-flow-review.md docs/openai-battle-agent/reviews/2026-07-28-phase-3a-mgba-loopback-bridge-evidence.md docs/openai-battle-agent/plans/2026-07-28-phase-3a-mgba-loopback-bridge.md
  git commit -m "docs(ai): record phase 3 bridge spike"
  ```

## Plan self-review

- **Specification coverage:** Task 1 names and tests `READY` without consuming it; Tasks 2–3 provide bounded transport and build-derived address discovery; Task 4 owns Lua listener/read/write behavior and every manual failure path; Task 5 records reproducible verification.
- **Type and protocol consistency:** ROM V1 offsets are the existing APCS-GNU asserted values. `BAGB/1` uses unsigned decimal sequence/action-count/index fields; responder and Lua both enforce action count 1–4 and action index 0–3 before response commit.
- **Compatibility and fallback:** Lua has no outbound connect, no non-loopback bind, and no unbounded in-emulator wait. Missing/disconnected/malformed/stale responders cause no mailbox action/target write. The ROM continues to ignore `READY`.
- **Battle-mechanics safety:** No task reads response fields in the ROM or modifies the post-score `BattleAgent_TryPublishRequest` seam. Existing vanilla move assertions remain required.
- **Scope:** The deterministic responder is deliberately not the Phase 4 service; no snapshot transport, prompt, model, API key, switch, item, double battle, or trainer rollout appears here.

## Links

- [Phase 3A specification](../specs/2026-07-28-phase-3a-mgba-loopback-bridge.md)
- [Phase 3A flow review](../reviews/2026-07-28-phase-3a-mgba-loopback-bridge-flow-review.md)
- [Phase 2 evidence](../reviews/2026-07-28-phase-2-build-and-test-evidence.md)
