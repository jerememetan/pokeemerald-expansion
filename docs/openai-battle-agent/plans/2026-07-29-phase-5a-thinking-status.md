# Phase 5A In-Battle Thinking Status Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` (recommended) or inline task execution. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the visually blank external-AI decision wait with an animated `AI is thinking...` status in the standard lower battle message window, without changing battle decisions or fallback behavior.

**Architecture:** Keep the existing `STATE_WAIT_EXTERNAL_AI_RESPONSE` state and mailbox protocol unchanged. Add a small ROM-only presentation state owned by `battle_agent.c`; `battle_main.c` tells it when the player has finished action selection, and it updates/clears the lower message window while the existing response polling continues. The helper owns the window only after it renders its own text, so it cannot erase player input UI or subsequent normal battle text.

**Tech Stack:** pokeemerald-expansion C, existing battle message window (`B_WIN_MSG`), existing battle test runner, WSL/devkitARM build, Python bridge-service regression tests.

**Specification:** [Phase 5A thinking status](../specs/2026-07-29-phase-5a-thinking-status.md)

**Flow review:** [Phase 5A flow review](../reviews/2026-07-29-phase-5a-thinking-status-flow-review.md)

---

## File structure

- Modify `include/battle_agent.h`: declare the presentation update/cleanup API and the test-only inspection API.
- Modify `src/battle_agent.c`: own per-battler thinking-status state, fixed ROM strings, rendering, animation, cleanup, and `#if TESTING` state hooks.
- Modify `src/battle_main.c`: call the presentation update only while the existing external wait remains pending and pass whether the player action is confirmed.
- Modify `test/battle/ai.c`: add focused state/lifecycle tests next to the existing external-AI request tests.
- Modify `docs/openai-battle-agent/2026-07-18-mgba-ai-trainer-design.md`: link the completed implementation plan and, after verification, record Phase 5A evidence.
- Create `docs/openai-battle-agent/reviews/2026-07-29-phase-5a-thinking-status-evidence.md`: record exact automated, build, and two-scenario mGBA smoke-test evidence.

No Lua, Python service, mailbox layout, wire contract, trainer data, battle-controller action emission, or move-damage files change.

## Task 1: Define the presentation-state contract with failing tests

**Files:**

- Modify: `include/battle_agent.h`
- Modify: `test/battle/ai.c`
- Test: `test/battle/ai.c`

- [ ] **Step 1: Add the test-visible status enum and declarations, but no implementation.**

  In `include/battle_agent.h`, after the response-status enum, declare the four display states and the fixed cadence:

  ```c
  enum BattleAgentThinkingStatus
  {
      BATTLE_AGENT_THINKING_HIDDEN,
      BATTLE_AGENT_THINKING_THREE_DOTS,
      BATTLE_AGENT_THINKING_NO_DOTS,
      BATTLE_AGENT_THINKING_ONE_DOT,
      BATTLE_AGENT_THINKING_TWO_DOTS,
  };

  #define BATTLE_AGENT_THINKING_DOT_INTERVAL 30
  ```

  After the existing external-wait functions, declare:

  ```c
  void BattleAgent_UpdateThinkingStatus(u32 battler, bool32 playerActionConfirmed);
  void BattleAgent_ClearThinkingStatus(u32 battler);

  #if TESTING
  void BattleAgent_TestStartThinkingStatus(u32 battler);
  void BattleAgent_TestUpdateThinkingStatus(u32 battler, bool32 playerActionConfirmed, bool32 messageWindowIdle);
  u8 BattleAgent_TestGetThinkingStatus(u32 battler);
  u8 BattleAgent_TestGetThinkingStatusFrames(u32 battler);
  #endif
  ```

- [ ] **Step 2: Write failing focused state tests.**

  Add the following `TEST` blocks in `test/battle/ai.c` immediately before the existing `AI_SINGLE_BATTLE_TEST("External AI mock accepts Calvin's legal move slot")` test. They exercise the runtime status-state transition through test-only wrappers without needing a real window renderer.

  ```c
  TEST("External AI thinking status waits for player action confirmation")
  {
      BattleAgent_ResetMailbox();
      BattleAgent_TestStartThinkingStatus(B_POSITION_OPPONENT_LEFT);

      BattleAgent_TestUpdateThinkingStatus(B_POSITION_OPPONENT_LEFT, FALSE, TRUE);
      EXPECT_EQ(BattleAgent_TestGetThinkingStatus(B_POSITION_OPPONENT_LEFT), BATTLE_AGENT_THINKING_HIDDEN);

      BattleAgent_TestUpdateThinkingStatus(B_POSITION_OPPONENT_LEFT, TRUE, TRUE);
      EXPECT_EQ(BattleAgent_TestGetThinkingStatus(B_POSITION_OPPONENT_LEFT), BATTLE_AGENT_THINKING_THREE_DOTS);
      EXPECT_EQ(BattleAgent_TestGetThinkingStatusFrames(B_POSITION_OPPONENT_LEFT), 0);
  }

  TEST("External AI thinking status waits for an idle message window")
  {
      BattleAgent_ResetMailbox();
      BattleAgent_TestStartThinkingStatus(B_POSITION_OPPONENT_LEFT);

      BattleAgent_TestUpdateThinkingStatus(B_POSITION_OPPONENT_LEFT, TRUE, FALSE);
      EXPECT_EQ(BattleAgent_TestGetThinkingStatus(B_POSITION_OPPONENT_LEFT), BATTLE_AGENT_THINKING_HIDDEN);

      BattleAgent_TestUpdateThinkingStatus(B_POSITION_OPPONENT_LEFT, TRUE, TRUE);
      EXPECT_EQ(BattleAgent_TestGetThinkingStatus(B_POSITION_OPPONENT_LEFT), BATTLE_AGENT_THINKING_THREE_DOTS);
  }

  TEST("External AI thinking status advances dots every thirty frames")
  {
      u32 frame;

      BattleAgent_ResetMailbox();
      BattleAgent_TestStartThinkingStatus(B_POSITION_OPPONENT_LEFT);
      BattleAgent_TestUpdateThinkingStatus(B_POSITION_OPPONENT_LEFT, TRUE, TRUE);
      for (frame = 0; frame < BATTLE_AGENT_THINKING_DOT_INTERVAL - 1; frame++)
          BattleAgent_TestUpdateThinkingStatus(B_POSITION_OPPONENT_LEFT, TRUE, TRUE);
      EXPECT_EQ(BattleAgent_TestGetThinkingStatus(B_POSITION_OPPONENT_LEFT), BATTLE_AGENT_THINKING_THREE_DOTS);

      BattleAgent_TestUpdateThinkingStatus(B_POSITION_OPPONENT_LEFT, TRUE, TRUE);
      EXPECT_EQ(BattleAgent_TestGetThinkingStatus(B_POSITION_OPPONENT_LEFT), BATTLE_AGENT_THINKING_NO_DOTS);
      for (frame = 0; frame < BATTLE_AGENT_THINKING_DOT_INTERVAL; frame++)
          BattleAgent_TestUpdateThinkingStatus(B_POSITION_OPPONENT_LEFT, TRUE, TRUE);
      EXPECT_EQ(BattleAgent_TestGetThinkingStatus(B_POSITION_OPPONENT_LEFT), BATTLE_AGENT_THINKING_ONE_DOT);
  }
  ```

- [ ] **Step 3: Run the focused tests and confirm they fail for missing symbols.**

  Run from PowerShell:

  ```powershell
  wsl bash -lc "cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion && make -j16 check TESTS='External AI thinking status'"
  ```

  Expected: compilation fails because the new test-visible status API has no definitions in `src/battle_agent.c`. Do not change test expectations to make this pre-implementation command pass.

## Task 2: Implement the isolated status state machine and renderer

**Files:**

- Modify: `src/battle_agent.c`
- Modify: `include/battle_agent.h`
- Test: `test/battle/ai.c`

- [ ] **Step 1: Add the private per-battler presentation state and fixed strings.**

  In `src/battle_agent.c`, include `battle_message.h`. Next to `sBattleAgentWaitStates`, add a private EWRAM array that contains `bool8 ownsMessageWindow`, `u8 displayState`, and `u8 framesUntilNextDot` for each battler. Define the four literal ROM strings in this file:

  ```c
  static const u8 sText_AiThinking[] = _("AI is thinking");
  static const u8 sText_AiThinkingOneDot[] = _("AI is thinking.");
  static const u8 sText_AiThinkingTwoDots[] = _("AI is thinking..");
  static const u8 sText_AiThinkingThreeDots[] = _("AI is thinking...");
  ```

  Create a private `BattleAgent_GetThinkingText(u8 displayState)` switch that maps only the four non-hidden enum values to those strings and returns `gText_EmptyString3` for hidden/invalid values.

- [ ] **Step 2: Implement one pure state-update helper.**

  Add a private helper with this behavior:

  ```c
  static bool32 BattleAgent_UpdateThinkingStatusState(u32 battler, bool32 playerActionConfirmed, bool32 messageWindowIdle)
  {
      // Return FALSE unless the battler has an active external wait.
      // Before ownership: require both playerActionConfirmed and messageWindowIdle,
      // then claim the status as THREE_DOTS with a zero frame count and return TRUE.
      // After ownership: if the window is busy return FALSE without advancing dots.
      // Otherwise increment the frame count; on frame 30 reset it, rotate
      // THREE_DOTS -> NO_DOTS -> ONE_DOT -> TWO_DOTS -> THREE_DOTS, and return TRUE.
      // Return FALSE on all non-render frames.
  }
  ```

  The helper must not read or write the mailbox, AI move/target fields, battle communication state, response timeout, or text windows. It changes only the private presentation state.

- [ ] **Step 3: Implement the runtime renderer and cleanup.**

  Implement `BattleAgent_UpdateThinkingStatus` by calling the state helper with `!IsTextPrinterActive(B_WIN_MSG)`. When the helper returns `TRUE`, call:

  ```c
  gBattle_BG0_X = 0;
  gBattle_BG0_Y = 0;
  BattlePutTextOnWindow(
      BattleAgent_GetThinkingText(sBattleAgentThinkingStatuses[battler].displayState),
      B_WIN_MSG);
  ```

The BG0 assignments restore the normal message viewport after player move
selection has scrolled it to the lower move-menu region. They occur only once
the helper has claimed the status, which remains deferred until the player has
confirmed an action.

  Do not implement `BattleAgent_ClearThinkingStatus` in this task. Task 3 adds the cleanup function and connects it to accepted-response, timeout, and reset paths after its failing cleanup test exists.

- [ ] **Step 4: Add minimal test-only wrappers.**

  Under the existing `#if TESTING` block, implement the declarations from Task 1. `BattleAgent_TestStartThinkingStatus` resets just the selected presentation state and marks the corresponding existing wait state active. `BattleAgent_TestUpdateThinkingStatus` invokes `BattleAgent_UpdateThinkingStatusState` with the supplied booleans but never writes a text window. The getter functions return the private display state and elapsed-dot-frame count. These wrappers must not mutate the mailbox, move slot, target, timeout counter, or AI score.

- [ ] **Step 5: Re-run the focused state tests.**

  Run:

  ```powershell
  wsl bash -lc "cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion && make -j16 check TESTS='External AI thinking status'"
  ```

  Expected: every new `External AI thinking status` test passes. Existing move-selection tests are not changed.

- [ ] **Step 6: Commit the isolated state-machine slice.**

  ```powershell
  git add include/battle_agent.h src/battle_agent.c test/battle/ai.c
  git commit -m "feat(ai): add thinking status state"
  ```

  Expected: one commit containing only ROM presentation state, its test hooks, and focused tests.

## Task 3: Integrate status ownership with the existing external wait

**Files:**

- Modify: `src/battle_main.c`
- Modify: `test/battle/ai.c`
- Test: `test/battle/ai.c`

- [ ] **Step 1: Write failing lifecycle tests.**

  Add these tests after the Task 1 tests. The first verifies cleanup is idempotent after a status starts; the second verifies a fresh wait restarts at three dots.

  ```c
  TEST("External AI thinking status cleanup resets a completed wait")
  {
      BattleAgent_ResetMailbox();
      BattleAgent_TestStartThinkingStatus(B_POSITION_OPPONENT_LEFT);
      BattleAgent_TestUpdateThinkingStatus(B_POSITION_OPPONENT_LEFT, TRUE, TRUE);
      BattleAgent_ClearThinkingStatus(B_POSITION_OPPONENT_LEFT);

      EXPECT_EQ(BattleAgent_TestGetThinkingStatus(B_POSITION_OPPONENT_LEFT), BATTLE_AGENT_THINKING_HIDDEN);
      EXPECT_EQ(BattleAgent_TestGetThinkingStatusFrames(B_POSITION_OPPONENT_LEFT), 0);
      BattleAgent_ClearThinkingStatus(B_POSITION_OPPONENT_LEFT);
      EXPECT_EQ(BattleAgent_TestGetThinkingStatus(B_POSITION_OPPONENT_LEFT), BATTLE_AGENT_THINKING_HIDDEN);
  }

  TEST("External AI thinking status starts fresh after a previous wait")
  {
      BattleAgent_ResetMailbox();
      BattleAgent_TestStartThinkingStatus(B_POSITION_OPPONENT_LEFT);
      BattleAgent_TestUpdateThinkingStatus(B_POSITION_OPPONENT_LEFT, TRUE, TRUE);
      BattleAgent_ClearThinkingStatus(B_POSITION_OPPONENT_LEFT);
      BattleAgent_TestStartThinkingStatus(B_POSITION_OPPONENT_LEFT);
      BattleAgent_TestUpdateThinkingStatus(B_POSITION_OPPONENT_LEFT, TRUE, TRUE);

      EXPECT_EQ(BattleAgent_TestGetThinkingStatus(B_POSITION_OPPONENT_LEFT), BATTLE_AGENT_THINKING_THREE_DOTS);
      EXPECT_EQ(BattleAgent_TestGetThinkingStatusFrames(B_POSITION_OPPONENT_LEFT), 0);
  }
  ```

- [ ] **Step 2: Run the lifecycle tests and confirm failure before integration.**

  Run:

  ```powershell
  wsl bash -lc "cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion && make -j16 check TESTS='External AI thinking status cleanup'"
  ```

  Expected: the test binary fails to link because `BattleAgent_ClearThinkingStatus` is declared but not yet defined. Do not replace the call with a test-only reset helper; this test defines the required public cleanup behavior.

- [ ] **Step 3: Add a player-action-confirmation helper in `battle_main.c`.**

  Immediately after the local turn-selection state enum, define:

  ```c
  static bool32 IsPlayerActionConfirmedForExternalAiStatus(void)
  {
      u32 playerBattler = GetBattlerAtPosition(B_POSITION_PLAYER_LEFT);

      return gBattleCommunication[playerBattler] == STATE_WAIT_ACTION_CONFIRMED
          || gBattleCommunication[playerBattler] == STATE_WAIT_ACTION_CONFIRMED_STANDBY;
  }
  ```

  Before editing `battle_main.c`, implement `BattleAgent_ClearThinkingStatus` in `src/battle_agent.c` as an idempotent function. If and only if `ownsMessageWindow` is true, write `gText_EmptyString3` to `B_WIN_MSG`; then zero that battler's private presentation state. Invalid battler indexes return without writing UI. At the beginning of `BattleAgent_ResetMailbox`, call it for every valid battler before zeroing wait/presentation arrays. Call it immediately before `BattleAgent_ClearResponse()` in successful `BattleAgent_TryConsumeResponse` and in `BattleAgent_UseVanillaFallback`.

  Then, in `case STATE_WAIT_EXTERNAL_AI_RESPONSE`, preserve the existing priority exactly: timeout first, then valid response. Add the status update only after both branches fail:

  ```c
  if (BattleAgent_IsWaitExpired(battler))
  {
      BattleAgent_UseVanillaFallback(battler);
      gBattleCommunication[battler] = STATE_BEFORE_ACTION_CHOSEN;
  }
  else if (BattleAgent_TryConsumeResponse(battler))
  {
      gBattleCommunication[battler] = STATE_BEFORE_ACTION_CHOSEN;
  }
  else
  {
      BattleAgent_UpdateThinkingStatus(battler, IsPlayerActionConfirmedForExternalAiStatus());
  }
  ```

  Do not add a new `gBattleCommunication` state, do not wait longer than 900 frames, and do not alter `gBattleStruct->aiMoveOrAction` or `gBattleStruct->aiChosenTarget` in `battle_main.c`.

- [ ] **Step 4: Run all focused external-AI ROM tests.**

  Run:

  ```powershell
  wsl bash -lc "cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion && make -j16 check TESTS='External AI'"
  ```

  Expected: all External AI request, snapshot, stale-response, fallback, V2 response, and new thinking-status tests pass. In particular, accepted V2 responses still choose their requested legal move and absent responses keep the saved vanilla move.

- [ ] **Step 5: Commit the integration slice.**

  ```powershell
  git add src/battle_main.c src/battle_agent.c test/battle/ai.c
  git commit -m "feat(ai): show thinking status while waiting"
  ```

  Expected: one commit containing only the wait-state UI integration and tests.

## Task 4: Full verification, documentation, and emulator smoke tests

**Files:**

- Modify: `docs/openai-battle-agent/2026-07-18-mgba-ai-trainer-design.md`
- Create: `docs/openai-battle-agent/reviews/2026-07-29-phase-5a-thinking-status-evidence.md`
- Test: `test/battle/ai.c`, `tools/mgba-bridge/tests/test_battle_agent_service.py`

- [ ] **Step 1: Run full ROM and bridge-service regression commands.**

  Run:

  ```powershell
  wsl bash -lc "cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion && make -j16 check"
  wsl bash -lc "cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion && make -j16"
  py -3 -m unittest discover -s tools/mgba-bridge/tests
  git diff --check
  ```

  Expected: the full battle suite finishes with no new Phase 5A failures, the ROM build produces `pokeemerald.gba`, all Python bridge/service tests pass, and `git diff --check` has no whitespace errors. Record actual pass/fail counts and build output in the evidence file; do not claim success from an older run.

- [ ] **Step 2: Perform the connected-service mGBA smoke test.**

  From PowerShell, start the existing service:

  ```powershell
  py -3 tools\mgba-bridge\battle_agent_service.py
  ```

  Reset the mGBA Scripting window, load `tools/mgba-bridge/mgba_bridge.lua` once, and start a Calvin battle. Choose the player's move. Expected: the standard lower dialogue box displays `AI is thinking...` and rotates its dots while the agent is pending; a matching `BAGB response written: N` ends the status without a button press and normal battle text/action follows. Capture the accepted sequence and status behavior in the evidence file.

- [ ] **Step 3: Perform the absent-service fallback mGBA smoke test.**

  Stop the Python service with `Ctrl+C`, leave the ROM and Lua script running, and start or replay a Calvin battle. Expected: after the player confirms a move, the lower dialogue box displays and animates `AI is thinking...`; after no more than 900 rendered frames it clears automatically and Calvin uses the existing vanilla trainer-AI action. The emulator stays responsive and no thinking message remains on the next turn. Record this outcome in the evidence file.

- [ ] **Step 4: Link the evidence and update roadmap status.**

  In the Phase 5A roadmap section, link the implementation plan and evidence file. In the evidence file, link the specification, flow review, plan, exact commands, current mGBA version/hash reference, connected-service result, absent-service result, and any known limitation. Do not mark broader Phase 5 diagnostics or Phase 7 switching complete.

- [ ] **Step 5: Commit the evidence-only handoff.**

  ```powershell
  git add docs/openai-battle-agent/2026-07-18-mgba-ai-trainer-design.md docs/openai-battle-agent/reviews/2026-07-29-phase-5a-thinking-status-evidence.md
  git commit -m "docs(ai): verify thinking status UI"
  ```

  Expected: the final commit contains documentation/evidence only.

## Plan self-review

- **Specification coverage:** Task 1 and Task 2 cover delayed ownership, text-window-idle behavior, fixed strings/cadence, and no new protocol data. Task 3 covers the existing timeout-first/response-second ordering and both cleanup paths. Task 4 covers connected and absent-service behavior, build/test evidence, and no stuck UI.
- **Terminology/type consistency:** `BattleAgent_UpdateThinkingStatus`, `BattleAgent_ClearThinkingStatus`, `BATTLE_AGENT_THINKING_*`, and `BATTLE_AGENT_THINKING_DOT_INTERVAL` are named consistently across tests and implementation tasks. `B_WIN_MSG` remains the only window ID.
- **Compatibility/fallback:** The plan retains `STATE_WAIT_EXTERNAL_AI_RESPONSE`, 900-frame timeout, saved vanilla action/target, legal-action validation, V2 mailbox, Lua bridge, and Python service. It adds no player input, move, target, switching, item, or double-battle behavior.
- **Scope control:** No graphics assets, sprites, model explanations, or execution-confirmation telemetry are included. Broader Phase 5 diagnostics and Phase 7 switch/item action families remain deferred.
