# Phase 0: Discovery and Contract Baseline Implementation Plan

> **For agentic workers:** Execute this plan inline in the current session. Follow the repository's Phase Documentation Gate in `AGENTS.md`; this phase has no production-code changes.

**Goal:** Create a repository-grounded call graph, battle-state inventory, version-1 protocol specification, and integration roadmap that make the first ROM code phase safe to implement and test.

**Architecture:** The current engine continues to own AI scoring, legality, targeting, and controller emission. The documentation records its existing decision handoff and defines a future mailbox that can only replace a retained engine decision with a ROM-produced legal action. The first runtime phase is restricted to one trainer, single battles, and moves.

**Tech Stack:** `pokeemerald-expansion` C battle engine and test harness; mGBA 0.11 development Lua API; a future local Python service; Markdown documentation.

**Specification:** [`../specs/2026-07-18-phase-0-discovery-and-contract-baseline.md`](../specs/2026-07-18-phase-0-discovery-and-contract-baseline.md)

**Flow review:** [`../reviews/2026-07-18-phase-0-discovery-and-contract-baseline-flow-review.md`](../reviews/2026-07-18-phase-0-discovery-and-contract-baseline-flow-review.md)

---

## Planned file structure

- Create: `docs/openai-battle-agent/battle-ai-callgraph.md` — current decision ownership and safe moves-only seam.
- Create: `docs/openai-battle-agent/battle-state.md` — snapshot source fields, visibility rules, and deferred data.
- Create: `docs/openai-battle-agent/protocol.md` — version-1 mailbox contract and state machine.
- Create: `docs/openai-battle-agent/integration-plan.md` — ordered runtime phases and verification matrix.
- Modify: `docs/openai-battle-agent/specs/2026-07-18-phase-0-discovery-and-contract-baseline.md` — link the completed reference documents.
- Modify: `docs/openai-battle-agent/2026-07-18-mgba-ai-trainer-design.md` — link the completed Phase 0 documentation set.

### Task 1: Record the current trainer-AI decision path

**Files:**

- Create: `docs/openai-battle-agent/battle-ai-callgraph.md`
- Read: `src/battle_main.c`, `src/battle_ai_main.c`, `src/battle_ai_switch_items.c`, `src/battle_controller_opponent.c`, `include/battle.h`, `include/battle_controllers.h`

- [ ] **Step 1: Capture the source evidence.**

  Run:

  ```powershell
  rg -n "STATE_TURN_START_RECORD|ComputeBattleAiScores|AI_TrySwitchOrUseItem|OpponentHandleChooseMove|aiMoveOrAction|aiChosenTarget" src/battle_main.c src/battle_ai_main.c src/battle_ai_switch_items.c src/battle_controller_opponent.c include/battle.h
  ```

  Expected: the output identifies scoring in `battle_main.c`, target assignment in `battle_ai_main.c`, switch/item selection in `battle_ai_switch_items.c`, and controller emission in `battle_controller_opponent.c`.

- [ ] **Step 2: Write `battle-ai-callgraph.md`.**

  Include this exact ownership sequence, expanded with source links and the relevant values:

  ```text
  STATE_TURN_START_RECORD
    -> ComputeBattleAiScores(battler)
       -> BattleAI_SetupAIData(...)
          -> CheckMoveLimitations(...)
          -> aiChosenTarget[battler]
       -> BattleAI_ChooseMoveOrAction()
    -> aiMoveOrAction[battler]
  CONTROLLER_CHOOSEACTION
    -> AI_TrySwitchOrUseItem(battler)
  CONTROLLER_CHOOSEMOVE
    -> OpponentHandleChooseMove(battler)
    -> controller action emission
  ```

  State that the Phase 1 external hook must retain the `ComputeBattleAiScores` result as fallback, leave `AI_TrySwitchOrUseItem` untouched, and provide only a validated move-slot/target override before controller emission.

- [ ] **Step 3: Validate the call graph.**

  Run:

  ```powershell
  Select-String -Path docs/openai-battle-agent/battle-ai-callgraph.md -Pattern 'ComputeBattleAiScores','AI_TrySwitchOrUseItem','OpponentHandleChooseMove','aiMoveOrAction','aiChosenTarget'
  ```

  Expected: every named handoff appears in the document.

### Task 2: Define the future snapshot's engine-owned state

**Files:**

- Create: `docs/openai-battle-agent/battle-state.md`
- Read: `src/battle_ai_main.c`, `src/battle_main.c`, `include/battle.h`, `include/battle_controllers.h`, `test/battle/ai.c`, `include/test/battle.h`

- [ ] **Step 1: Record legal-move evidence.**

  Run:

  ```powershell
  rg -n "CheckMoveLimitations|moveLimitations|CanTargetBattler|gBattleMons\[battler\]\.moves|gBattleMons\[battler\]\.pp" src/battle_ai_main.c src/battle_main.c src/battle_controller_opponent.c src/battle_ai_util.c
  ```

  Expected: the output shows that the engine owns move slots, PP, limitations, and target checks.

- [ ] **Step 2: Write `battle-state.md`.**

  Add a table with the following columns: `Field`, `ROM source`, `Visible to service`, `Version-1 use`, and `Reason`. It must include active battler identity, side, species, HP/current and maximum HP, status, stat stages, move slots, current PP, weather, terrain, legal-action entries, turn number, and three recent turn events. Mark opponent hidden moves, private party data, held item, ability, and exact internal damage-calculation data as excluded unless a later specification explicitly permits them.

- [ ] **Step 3: Document legal-action construction.**

  Define each version-1 legal action as:

  ```text
  legalActionIndex: u8
  moveSlot: u8          // 0 through 3
  targetBattler: u8     // engine-approved current battler index
  ```

  State that the ROM produces entries only for non-limited moves and valid current targets; the service returns only `legalActionIndex`.

- [ ] **Step 4: Validate the visibility boundary.**

  Run:

  ```powershell
  Select-String -Path docs/openai-battle-agent/battle-state.md -Pattern 'Excluded','legalActionIndex','CheckMoveLimitations','visible'
  ```

  Expected: the document distinguishes service-visible state from excluded hidden state and names the legal-action source of truth.

### Task 3: Specify the version-1 mailbox protocol

**Files:**

- Create: `docs/openai-battle-agent/protocol.md`
- Read: `docs/openai-battle-agent/battle-state.md`, `docs/openai-battle-agent/2026-07-18-mgba-ai-trainer-design.md`, `docs/openai-battle-agent/reviews/2026-07-18-phase-0-discovery-and-contract-baseline-flow-review.md`

- [ ] **Step 1: Write the mailbox ownership and layout section.**

  Specify a named `EWRAM_DATA` global with a `magic` value, `protocolVersion = 1`, request and response sequence numbers, request/response status values, snapshot payload, and response `legalActionIndex`. State that the Lua launcher resolves the named symbol from the map file generated with the ROM and checks magic/version before use.

- [ ] **Step 2: Write the request/response state machine.**

  Include this state model:

  ```text
  ROM: IDLE -> WRITING_REQUEST -> PENDING -> ACCEPTED | FALLBACK -> IDLE
  Bridge: DISCONNECTED | CONNECTED; PENDING -> RESPONSE_READY
  ROM accepts RESPONSE_READY only when version, sequence, status, and legalActionIndex are valid.
  ```

  Define `FALLBACK` as restoring the precomputed `aiMoveOrAction` and `aiChosenTarget` without changing battle mechanics.

- [ ] **Step 3: Write the asynchronous deadline and rejection rules.**

  Record the 600-frame budget, the prohibition on busy loops and blocking Lua connects, and these rejection reasons: wrong magic, wrong version, sequence mismatch, non-ready response status, action-index out of range, action entry not currently legal, duplicate response, bridge disconnect, and deadline expiry.

- [ ] **Step 4: Validate every failure path.**

  Run:

  ```powershell
  Select-String -Path docs/openai-battle-agent/protocol.md -Pattern '600','sequence','fallback','wrong version','out of range','disconnect'
  ```

  Expected: the protocol names the deadline, sequence validation, fallback behavior, and all listed rejection classes.

### Task 4: Define runtime phases and their evidence

**Files:**

- Create: `docs/openai-battle-agent/integration-plan.md`
- Read: `docs/openai-battle-agent/protocol.md`, `docs/openai-battle-agent/battle-ai-callgraph.md`, `AGENTS.md`

- [ ] **Step 1: Write phases 1 through 9.**

  Use these exact phase boundaries: ROM-only external flag and mock action; legal-action snapshot; mGBA Lua bridge; deterministic local service; model-backed trainer; configured trainer expansion; switching/items; double battles; packaging and demo handoff.

- [ ] **Step 2: Add an evidence matrix.**

  Include the following mandatory rows: ordinary trainer unchanged, opt-in trainer with valid response, absent bridge, late response, stale response, invalid action index, invalid target, service disconnect, map/version mismatch, switch/item preservation, and double-battle target coverage. Mark the first phase responsible for each row.

- [ ] **Step 3: Link all Phase 0 documents.**

  Add a documentation index linking the parent design, Phase 0 specification, flow review, call graph, battle-state inventory, protocol, and this plan.

- [ ] **Step 4: Validate roadmap scope.**

  Run:

  ```powershell
  Select-String -Path docs/openai-battle-agent/integration-plan.md -Pattern 'switching','double battles','fallback','evidence'
  ```

  Expected: later features are explicitly sequenced after the moves-only safe slice and all phases retain fallback requirements.

### Task 5: Close Phase 0 and establish baseline evidence

**Files:**

- Modify: `docs/openai-battle-agent/specs/2026-07-18-phase-0-discovery-and-contract-baseline.md`
- Modify: `docs/openai-battle-agent/2026-07-18-mgba-ai-trainer-design.md`
- Verify: all Phase 0 documentation files

- [ ] **Step 1: Add completed-document links.**

  Replace the Phase 0 output list's plain paths with Markdown links and add the Phase 0 reference-document index to the parent design.

- [ ] **Step 2: Verify documentation quality.**

  Run:

  ```powershell
  $forbidden = @('T' + 'BD', 'TO' + 'DO', 'implement later', 'fill in details')
  Get-ChildItem docs/openai-battle-agent -Recurse -Filter *.md | Select-String -Pattern $forbidden -CaseSensitive:$false
  git diff --check
  ```

  Expected: no placeholder matches and no whitespace errors.

- [ ] **Step 3: Establish the build/test baseline.**

  Run:

  ```powershell
  make
  make check
  ```

  Expected: both commands exit with code `0`; `make` produces the configured ROM and `make check` completes the repository's headless battle-test runner. If either command fails before any source changes, record the exact failure as an environment baseline and do not attribute it to Phase 0.

- [ ] **Step 4: Confirm phase exit criteria.**

  Verify that all required Phase 0 artifacts exist, link to one another, preserve the moves-only scope, name the fallback action, and satisfy the specification's exit criteria.

## Plan self-review

- **Specification coverage:** Tasks 1–4 create each required artifact; Task 5 links and validates them.
- **Terminology consistency:** `externalAi`, `legalActionIndex`, `requestSequence`, `aiMoveOrAction`, and `aiChosenTarget` use the same meanings as the Phase 0 specification and review.
- **Protocol safety:** The plan preserves the current AI result, documents a ROM-produced legal set, rejects stale or malformed responses, and prevents a hard-coded mailbox address.
- **Scope:** No task modifies battle code, trainer data, Lua, Python, or emulator configuration. Switching, items, and doubles remain future, explicitly named phases.
