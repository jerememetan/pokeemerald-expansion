# Phase 4A Local Ollama Tool Agent and ROM Response Acceptance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the local `qwen2.5-coder:7b` Ollama model choose one ROM-provided legal move for `TRAINER_CALVIN_1`, while the ROM always safely falls back to its saved vanilla trainer-AI action.

**Architecture:** The ROM upgrades the mailbox to V2, snapshots only active-battler state and legal move actions, then yields in a per-Calvin action-selection state for at most 900 frames. Lua converts that snapshot to a 425-byte `BAGB/2` request, and a loopback-only Python service presents read-only tools to Ollama. The service can return only a legal action index; ROM-side consumption revalidates it through the same target-normalization rule used to create the action.

**Tech Stack:** pokeemerald-expansion C/ARM GCC, mGBA 0.10.5 Lua, Python 3 standard library, Ollama `/api/chat`, unittest, existing battle-test runner.

---

## File structure

- Modify `include/battle_agent.h` — replace V1 mailbox definitions/assertions with V2 C mailbox fields, explicit wire constants, response/wait APIs, and test-only helpers.
- Modify `src/battle_agent.c` — construct V2 active-battler/action analysis, retain the vanilla fallback, own response validation/timeout state, and expose bounded wait helpers.
- Modify `src/battle_main.c` — add the per-battler external-AI wait state between vanilla scoring and opponent-controller emission.
- Modify `test/battle/ai.c` and `test/test_runner_battle.c` — create V2 snapshot/response/timeout battle tests and a test-only mailbox response writer.
- Replace `tools/mgba-bridge/bridge_protocol.py` and `tools/mgba-bridge/test_responder.py` — V2 fixed binary framing plus a deterministic V2 test responder.
- Create `tools/mgba-bridge/battle_agent_service.py` — loopback server, V2 decoder, catalog-backed read-only tools, Ollama tool-call loop, and bounded response encoder.
- Create `tools/mgba-bridge/generate_catalog.py` and commit `tools/mgba-bridge/catalog_v2.json` — generate symbolic labels solely from repository constants.
- Modify `tools/mgba-bridge/mgba_bridge.lua` — replace the V1 line protocol with bounded V2 binary framing and documented V2 memory reads/writes.
- Modify/create `tools/mgba-bridge/tests/test_bridge_protocol.py`, `test_mgba_bridge_source.py`, `test_battle_agent_service.py`, and `test_generate_catalog.py` — protocol, source-safety, tool, catalog, and fake-Ollama tests.
- Modify `tools/mgba-bridge/README.md`, `docs/openai-battle-agent/2026-07-18-mgba-ai-trainer-design.md`, and add `docs/openai-battle-agent/reviews/2026-07-29-phase-4a-local-ollama-tool-agent-evidence.md` — launch, recovery, and verification evidence.

## Task 1: Define and test the ROM V2 contract

**Files:**
- Modify: `include/battle_agent.h`
- Modify: `src/battle_agent.c`
- Modify: `test/battle/ai.c`
- Modify: `test/test_runner_battle.c`

- [ ] **Step 1: Add failing V2 snapshot tests.**

  Add tests named `External AI V2 snapshot copies both active battlers and move analysis` and `External AI V2 snapshot excludes party benches`. Seed the player and Calvin battlers with non-default level, types, item, ability, stats, statuses, move PP, weather, terrain, and side status. Assert the test-side V2 snapshot has exactly those values for battler IDs `0` and `1`, `battlerCount == 2`, and four zeroed inactive slots; assert party member 1 data never appears.

  Also assert one legal action has the expected slot, target, priority, STAB flag, effectiveness enum, and `canFaintTarget` value supplied by the battle engine.

- [ ] **Step 2: Run the focused test and confirm the current V1 contract cannot satisfy it.**

  Run:

  ```powershell
  wsl bash -lc "cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion && make -j16 check TESTS='External AI V2 snapshot'"
  ```

  Expected: compilation failure because `BattleAgentMailboxV2` and the V2 test getters do not exist.

- [ ] **Step 3: Replace the V1 contract with explicit V2 structures and assertions.**

  In `include/battle_agent.h`, define the protocol and wire constants below. Keep C mailbox structures separate from wire encoding; Lua never copies the C structure.

  ```c
  #define BATTLE_AGENT_PROTOCOL_MAGIC 0x42414732 // "BAG2"
  #define BATTLE_AGENT_PROTOCOL_VERSION 2
  #define BATTLE_AGENT_WIRE_REQUEST_SIZE 417
  #define BATTLE_AGENT_WIRE_RESPONSE_SIZE 5
  #define BATTLE_AGENT_RESPONSE_TIMEOUT_FRAMES 900

  enum BattleAgentTypeEffectiveness
  {
      BATTLE_AGENT_EFFECTIVENESS_IMMUNE,
      BATTLE_AGENT_EFFECTIVENESS_NOT_VERY_EFFECTIVE,
      BATTLE_AGENT_EFFECTIVENESS_NEUTRAL,
      BATTLE_AGENT_EFFECTIVENESS_SUPER_EFFECTIVE,
  };

  struct BattleAgentMoveSnapshotV2
  {
      u16 move;
      u8 pp;
      u8 type;
      u8 power;
      u8 accuracy;
      u16 effect;
      u8 targetCategory;
      s8 priority;
      u8 split;
      u8 reserved;
  };

  struct BattleAgentBattlerSnapshotV2
  {
      u16 species;
      u8 level, type1, type2, type3;
      u16 ability, item, hp, maxHp;
      u16 attack, defense, speed, spAttack, spDefense;
      u32 status1, status2, status3;
      u8 statStages[NUM_BATTLE_STATS];
      struct BattleAgentMoveSnapshotV2 moves[MAX_MON_MOVES];
  };

  struct BattleAgentLegalActionV2
  {
      u8 actionIndex, moveSlot, targetBattler;
      u8 typeEffectiveness, hasStab, canFaintTarget;
  };
  ```

  Define `BattleAgentSnapshotV2` with `battlerCount`, four battlers, weather, terrain, field statuses, and side statuses. Define `BattleAgentMailboxV2` with the existing request/response header fields plus the V2 snapshot/action array. Add `STATIC_ASSERT`s for fixed-width member sizes, every field Lua reads, the 92-byte canonical battler representation, 6-byte action representation, and the `417`-byte encoded request calculation. Rename global `gBattleAgentMailbox` to type `BattleAgentMailboxV2`; the symbol name must not change.

- [ ] **Step 4: Implement minimal V2 snapshot/action construction.**

  In `src/battle_agent.c`, replace `BattleAgent_CopySnapshot` with a zero-initializing V2 copy routine that reads only `gBattleMons`, `gBattleWeather`, `gBattleTerrain`, `gFieldStatuses`, `gSideStatuses`, and `gBattleMoves`. For each active battler copy:

  ```c
  snapshotBattler->level = gBattleMons[battler].level;
  snapshotBattler->type1 = gBattleMons[battler].type1;
  snapshotBattler->ability = gBattleMons[battler].ability;
  snapshotBattler->item = gBattleMons[battler].item;
  snapshotBattler->attack = gBattleMons[battler].attack;
  snapshotBattler->status2 = gBattleMons[battler].status2;
  snapshotBattler->moves[slot].move = gBattleMons[battler].moves[slot];
  snapshotBattler->moves[slot].pp = gBattleMons[battler].pp[slot];
  snapshotBattler->moves[slot].type = gBattleMoves[move].type;
  ```

  Complete the other listed V2 fields from the same source. Do not access `gPlayerParty`, `gEnemyParty`, or party-index arrays.

  Extend legal action creation with `hasStab = IS_BATTLER_OF_TYPE(requester, gBattleMoves[move].type)`, a four-value category derived from `GetTypeModifier`, and `canFaintTarget = CanIndexMoveFaintTarget(requester, target, moveSlot, 0)`. Keep `BattleAgent_NormalizeSingleTarget` as the sole target construction rule.

- [ ] **Step 5: Run the V2 snapshot tests.**

  Run:

  ```powershell
  wsl bash -lc "cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion && make -j16 check TESTS='External AI V2 snapshot'"
  ```

  Expected: all V2 snapshot tests pass; no test reads party bench state.

- [ ] **Step 6: Commit the contract slice.**

  ```powershell
  git add include/battle_agent.h src/battle_agent.c test/battle/ai.c test/test_runner_battle.c
  git commit -m "feat(battle): publish V2 agent snapshots"
  ```

## Task 2: Gate Calvin’s controller command on bounded ROM response acceptance

**Files:**
- Modify: `include/battle_agent.h`
- Modify: `src/battle_agent.c`
- Modify: `src/battle_main.c`
- Modify: `test/battle/ai.c`
- Modify: `test/test_runner_battle.c`

- [ ] **Step 1: Add failing response-consumption tests.**

  Add focused tests proving (a) a matching `READY` V2 response uses legal action 1 instead of the seeded vanilla slot, (b) stale sequence, action index `>= legalActionCount`, non-pending status, and an action whose freshly normalized target differs preserve the saved vanilla move/target, and (c) a response injected only on wait visit 900 loses to fallback.

  Add a test that progresses 900 action-selection frames without a response and asserts both that frame count advances and Calvin chooses the saved vanilla action exactly once.

- [ ] **Step 2: Confirm the tests fail before response consumption exists.**

  Run:

  ```powershell
  wsl bash -lc "cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion && make -j16 check TESTS='External AI V2 response'"
  ```

  Expected: FAIL because V1 responses are not consumed and no wait-state timeout exists.

- [ ] **Step 3: Add state-owned fallback and validation helpers.**

  Add these public declarations to `include/battle_agent.h`:

  ```c
  bool32 BattleAgent_BeginExternalWait(u32 battler);
  bool32 BattleAgent_TryConsumeResponse(u32 battler);
  bool32 BattleAgent_IsWaitExpired(u32 battler);
  void BattleAgent_UseVanillaFallback(u32 battler);
  ```

  In `src/battle_agent.c`, store per-battler `fallbackMoveOrAction`, `fallbackTarget`, `requestSequence`, and `waitFrames` in a private zero-initialized `EWRAM_DATA` state. `BattleAgent_BeginExternalWait` must copy the already-computed `aiMoveOrAction` and `aiChosenTarget`, publish a request, and return `FALSE` without changing either value when eligibility fails or no legal action exists.

  `BattleAgent_TryConsumeResponse` must require `PENDING`, `READY`, sequence equality, `actionIndex < legalActionCount`, and a legal action whose move slot is still usable. It must rerun `BattleAgent_NormalizeSingleTarget(battler, gBattleMons[battler].moves[action->moveSlot], &target)` and require `target == action->targetBattler`. Only then assign:

  ```c
  gBattleStruct->aiMoveOrAction[battler] = action->moveSlot;
  gBattleStruct->aiChosenTarget[battler] = target;
  ```

  It clears `responseStatus` after every attempted consumption. `BattleAgent_IsWaitExpired` increments once per visit and returns true when `++waitFrames >= BATTLE_AGENT_RESPONSE_TIMEOUT_FRAMES`; `BattleAgent_UseVanillaFallback` restores exactly the saved two fields and clears the private wait record.

- [ ] **Step 4: Add the action-selection state.**

  In the local `HandleTurnActionSelectionState` enum in `src/battle_main.c`, insert `STATE_WAIT_EXTERNAL_AI_RESPONSE` between `STATE_BEFORE_ACTION_CHOSEN` and `STATE_WAIT_ACTION_CHOSEN`. Replace the current publish/mock calls after `ComputeBattleAiScores` with:

  ```c
  if (BattleAgent_BeginExternalWait(battler))
  {
      gBattleCommunication[battler] = STATE_WAIT_EXTERNAL_AI_RESPONSE;
      break;
  }
  ```

  Add the new switch case:

  ```c
  case STATE_WAIT_EXTERNAL_AI_RESPONSE:
      if (BattleAgent_IsWaitExpired(battler))
      {
          BattleAgent_UseVanillaFallback(battler);
          gBattleCommunication[battler] = STATE_BEFORE_ACTION_CHOSEN;
      }
      else if (BattleAgent_TryConsumeResponse(battler))
      {
          gBattleCommunication[battler] = STATE_BEFORE_ACTION_CHOSEN;
      }
      break;
  ```

  Do not alter `OpponentHandleChooseMove`, move effects, damage code, player state progression, or non-Calvin trainer behavior.

- [ ] **Step 5: Run the response and full external-AI suites.**

  Run:

  ```powershell
  wsl bash -lc "cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion && make -j16 check TESTS='External AI V2 response'"
  wsl bash -lc "cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion && make -j16 check TESTS='External AI'"
  ```

  Expected: the V2 response tests and all existing external-AI tests pass; unsupported battles and unflagged trainers retain vanilla behavior.

- [ ] **Step 6: Commit the bounded acceptance slice.**

  ```powershell
  git add include/battle_agent.h src/battle_agent.c src/battle_main.c test/battle/ai.c test/test_runner_battle.c
  git commit -m "feat(battle): accept bounded external AI responses"
  ```

## Task 3: Implement the V2 Python protocol, catalog, and tool-only Ollama service

**Files:**
- Create: `tools/mgba-bridge/battle_agent_service.py`
- Create: `tools/mgba-bridge/generate_catalog.py`
- Create: `tools/mgba-bridge/catalog_v2.json`
- Modify: `tools/mgba-bridge/bridge_protocol.py`
- Modify: `tools/mgba-bridge/test_responder.py`
- Modify: `tools/mgba-bridge/tests/test_bridge_protocol.py`
- Create: `tools/mgba-bridge/tests/test_battle_agent_service.py`
- Create: `tools/mgba-bridge/tests/test_generate_catalog.py`

- [ ] **Step 1: Write failing binary protocol tests.**

  In `test_bridge_protocol.py`, construct a 425-byte request containing a 417-byte payload and assert `parse_request_frame` returns sequence, battler count, two active battlers, and legal actions. Assert rejection for bad magic, version 1, kind mismatch, payload length 416/418, truncated data, appended data, invalid boolean values, `battlerCount != 2`, and legal count outside `1..4`. Assert `format_response_frame(7, 2)` is exactly 13 bytes and decodes to sequence 7/action 2.

- [ ] **Step 2: Implement a strict field-by-field codec.**

  Replace the line protocol in `bridge_protocol.py` with:

  ```python
  MAGIC = b"BAGB"
  VERSION = 2
  KIND_REQUEST = 1
  KIND_RESPONSE = 2
  REQUEST_PAYLOAD_SIZE = 417
  RESPONSE_PAYLOAD_SIZE = 5
  REQUEST_FRAME_SIZE = 8 + REQUEST_PAYLOAD_SIZE
  RESPONSE_FRAME_SIZE = 8 + RESPONSE_PAYLOAD_SIZE

  def parse_request_frame(frame: bytes) -> Request: ...
  def format_response_frame(sequence: int, action_index: int) -> bytes: ...
  ```

  Use `struct.unpack_from('<I', ...)` and explicit byte offsets that match the approved V2 wire table. Do not deserialize a C struct, accept variable length, or accept trailing bytes. Define frozen dataclasses for battler moves, battlers, actions, and request.

- [ ] **Step 3: Write failing catalog and tool tests.**

  In `test_generate_catalog.py`, feed representative `#define MOVE_TACKLE 33`, `#define SPECIES_POOCHYENA 261`, and `#define EFFECT_HIT 0` lines and assert canonical numeric-string keys and labels. Reject duplicate numeric IDs and malformed constants.

  In `test_battle_agent_service.py`, decode a fixture request and assert exact results for all tools: `get_battle_state`, `get_field_state`, `get_battler(0|1)`, `get_battler_moves(0|1)`, `list_legal_actions`, `analyze_action(0)`, and `compare_speed`. Assert invalid IDs, non-integer action indexes, unknown tools, 13th tool call, repeated `choose_action`, text-only completion, and a selection outside the legal list produce no response.

- [ ] **Step 4: Implement catalog generation and service tool authority.**

  `generate_catalog.py` must parse only these repository files: `include/constants/species.h`, `moves.h`, `abilities.h`, `items.h`, and `battle_move_effects.h`. It writes sorted JSON:

  ```json
  {"abilities": {"1": "STENCH"}, "effects": {"0": "HIT"}, "items": {}, "moves": {"33": "TACKLE"}, "species": {"261": "POOCHYENA"}}
  ```

  `battle_agent_service.py` must connect only to the Lua listener at
  `127.0.0.1:57621`, retry until that one listener is ready, read exactly
  `REQUEST_FRAME_SIZE`, and return a response only from `choose_action`.
  Define the complete tool map:

  ```python
  TOOL_HANDLERS = {
      "get_battle_state": get_battle_state,
      "get_field_state": get_field_state,
      "get_battler": get_battler,
      "get_battler_moves": get_battler_moves,
      "list_legal_actions": list_legal_actions,
      "analyze_action": analyze_action,
      "compare_speed": compare_speed,
      "choose_action": choose_action,
  }
  ```

  Use `time.monotonic()` and stop without writing if 12 seconds or 12 tool calls elapse. Use `urllib.request.Request` only against `http://127.0.0.1:11434/api/chat`; request model `qwen2.5-coder:7b`, stream false, and pass tool schemas. Accept only `message.tool_calls` JSON entries containing a listed tool name and object arguments. The service must never invoke subprocesses, read arbitrary files after initial catalog load, or expose a socket/filesystem/process tool to the model.

- [ ] **Step 5: Add fake-Ollama integration tests.**

  Start a local `http.server.ThreadingHTTPServer` fixture. Return a read-only tool call followed by `choose_action(1)` and assert a legal 13-byte response. Return HTTP 500, missing tool calls, unknown tool, invalid arguments, repeated terminal call, and delayed response beyond a monkeypatched 12-second monotonic deadline; assert no response is sent in each case.

- [ ] **Step 6: Run the Python suite and catalog generation.**

  Run:

  ```powershell
  py -3 -m unittest discover -s tools/mgba-bridge/tests -v
  py -3 tools/mgba-bridge/generate_catalog.py --output tools/mgba-bridge/catalog_v2.json
  py -3 -m unittest tools/mgba-bridge/tests/test_generate_catalog.py -v
  ```

  Expected: all tests pass and `catalog_v2.json` changes only when project constants change.

- [ ] **Step 7: Commit the local service slice.**

  ```powershell
  git add tools/mgba-bridge
  git commit -m "feat(bridge): add local Ollama tool service"
  ```

## Task 4: Replace Lua V1 transport with bounded V2 binary forwarding

**Files:**
- Modify: `tools/mgba-bridge/mgba_bridge.lua`
- Modify: `tools/mgba-bridge/tests/test_mgba_bridge_source.py`
- Modify: `tools/mgba-bridge/README.md`

- [ ] **Step 1: Add source-contract tests before Lua changes.**

  Assert the Lua source contains `MAGIC = 0x42414732`, `VERSION = 2`, `REQUEST_FRAME_SIZE = 425`, `RESPONSE_FRAME_SIZE = 13`, loopback-only bind, no `socket.connect`, documented V2 offsets only, fixed reads of V2 field widths, exact length checks, and exactly this commit order:

  ```lua
  emu:write32(MAILBOX_ADDRESS + OFFSET_RESPONSE_SEQUENCE, response.sequence)
  emu:write8(MAILBOX_ADDRESS + OFFSET_RESPONSE_ACTION_INDEX, response.action_index)
  emu:write8(MAILBOX_ADDRESS + OFFSET_RESPONSE_STATUS, RESPONSE_READY)
  ```

- [ ] **Step 2: Run the source test and confirm V1 fails.**

  Run:

  ```powershell
  py -3 -m unittest tools/mgba-bridge/tests/test_mgba_bridge_source.py -v
  ```

  Expected: FAIL because the source still emits `BAGB/1` ASCII lines.

- [ ] **Step 3: Implement fixed binary frame assembly and receive buffering.**

  Add explicit little-endian helpers `append_u8`, `append_u16`, `append_u32`, `append_s8`, `read_u8`, and `read_u32`. Read the V2 mailbox fields one at a time using generated offset constants, append precisely 417 request payload bytes, then prepend the eight-byte `BAGB/2` header. On receive, buffer until exactly 13 bytes; reject a frame with any bad header, bad fixed length, wrong sequence, out-of-range action, or extra byte. Preserve one complete receive and one response commit maximum per frame.

  Retain the current listener behavior: `BRIDGE_HOST` must equal `127.0.0.1`, one client only, socket errors disconnect safely, and the bridge never creates an outbound connection.

- [ ] **Step 4: Run all bridge tests.**

  Run:

  ```powershell
  py -3 -m unittest discover -s tools/mgba-bridge/tests -v
  ```

  Expected: protocol and source suites pass; no V1 protocol token remains in production bridge files.

- [ ] **Step 5: Document and commit the V2 bridge.**

  Update `tools/mgba-bridge/README.md` with this exact launch order: build ROM, generate mailbox config, run `py -3 tools/mgba-bridge/battle_agent_service.py`, load `mgba_bridge.lua`, launch the ROM, then start Calvin’s battle. Document that stopping the service triggers vanilla fallback by 15 seconds.

  ```powershell
  git add tools/mgba-bridge/mgba_bridge.lua tools/mgba-bridge/tests/test_mgba_bridge_source.py tools/mgba-bridge/README.md
  git commit -m "feat(bridge): forward V2 binary agent frames"
  ```

## Task 5: Integrate, verify, and record Phase 4A evidence

**Files:**
- Modify: `docs/openai-battle-agent/2026-07-18-mgba-ai-trainer-design.md`
- Create: `docs/openai-battle-agent/reviews/2026-07-29-phase-4a-local-ollama-tool-agent-evidence.md`
- Modify: `tools/mgba-bridge/README.md`

- [ ] **Step 1: Run clean automated verification.**

  Run:

  ```powershell
  wsl bash -lc "cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion && make -j16 check TESTS='External AI'"
  py -3 -m unittest discover -s tools/mgba-bridge/tests -v
  wsl bash -lc "cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion && make -j16"
  ```

  Expected: external-AI tests pass, every Python test passes, and `pokeemerald.gba` builds. Record unrelated existing `ASSUME` failures separately rather than calling them Phase 4A regressions.

- [ ] **Step 2: Complete the connected manual smoke test.**

  In PowerShell, confirm `ollama list` contains `qwen2.5-coder:7b`; start `ollama serve` only if it is not already listening. Start the service, load the Lua script in mGBA, and fight Calvin. Record the service log showing at least one read-only tool call, one `choose_action`, the matching request sequence, and a legal response before the ROM deadline. Confirm Calvin performs the corresponding legal move.

- [ ] **Step 3: Complete failure-mode smoke tests.**

  Repeat Calvin’s battle once with the Python service stopped and once after disconnecting it during a pending request. Confirm mGBA stays responsive, Lua logs disconnect/no response, and Calvin proceeds with the saved vanilla move by the 900th wait frame. Repeat with a stale and an out-of-range responder frame; confirm Lua or ROM rejects it and vanilla remains intact.

- [ ] **Step 4: Write evidence and update the roadmap.**

  Evidence must list the exact commit, commands/results, mGBA version/hash already recorded for Phase 3A, Ollama model tag, connected log excerpt, each fallback result, and the known limitations: Calvin only, singles, active battlers, moves only, no bench/switch/items/doubles. Update the roadmap status to Phase 4A verified only after every exit criterion is met.

- [ ] **Step 5: Final review and commit.**

  Inspect `git diff --check` and `git status --short`; confirm no generated mailbox address, ROM, ELF, save file, or unrelated user change is staged. Commit only evidence/documentation:

  ```powershell
  git add docs/openai-battle-agent tools/mgba-bridge/README.md
  git commit -m "docs(ai): record Phase 4A verification"
  ```

## Compatibility and fallback checklist

- V1 `BAGB/1`, V1 mailbox magic/version, malformed frames, stale responses, duplicate responses, and action indexes outside the current V2 legal list are rejected.
- The ROM alone selects the fallback before entering the wait; it uses that fallback after exactly 900 wait-state visits and never leaves Calvin stuck in a pending state.
- Unconfigured trainers, wild/link/double/multi/facility/recorded production battles, switch/item choices, absent battlers, and no-legal-action states do not open the V2 wait.
- Python uses no third-party dependency, no cloud endpoint, no API key, no subprocess, no arbitrary filesystem reads, no emulator memory access, and no public network binding.
- No task changes battle damage, effects, targeting semantics, or the opponent controller outside the one pre-emission wait seam.

## Self-review

- **Specification coverage:** Tasks 1–2 implement every V2 mailbox, legal-action, timeout, and fallback requirement. Tasks 3–4 implement the fixed binary transport, local-only model service, catalog, all eight tools, 12-tool/12-second limits, and loopback safety. Task 5 proves the connected and failure paths and records evidence.
- **Terminology and types:** The plan consistently uses `BattleAgentMailboxV2`, `BattleAgentLegalActionV2`, `legalActionIndex`, `BAGB/2`, 417-byte request payload, 425-byte request frame, 5-byte response payload, 13-byte response frame, 12-second service limit, and 900-frame ROM limit.
- **Protocol/mechanics safety:** Response authority is only an action index; fresh target normalization plus existing move limitations guard ROM application. The saved vanilla action survives every failure path. No party bench data or battle mechanics modification is introduced.
- **Scope:** This remains the smallest approved vertical slice: Calvin, trainer singles, active battlers, and move actions. Switching, items, doubles, broad trainer coverage, UI, and cloud providers remain excluded.

## Links

- [Phase 4A specification](../specs/2026-07-29-phase-4a-local-ollama-tool-agent.md)
- [Phase 4A flow review](../reviews/2026-07-29-phase-4a-local-ollama-tool-agent-flow-review.md)
- [qwen2.5-coder tool-call compatibility amendment](2026-07-29-phase-4a-tool-call-compatibility.md)
- [Project roadmap](../2026-07-18-mgba-ai-trainer-design.md)
