# Phase 2: Legal-Action Snapshot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Publish a fixed, ROM-owned V1 snapshot and legal move-action list for an eligible Calvin single-battle turn without changing vanilla turn behavior.

**Architecture:** Add a narrow battle-agent module that owns the EWRAM mailbox, its explicit initialization, eligibility check, visible-state snapshot, and target-normalized action producer. `battle_main.c` invokes the producer only after the existing AI has produced a move fallback. The producer writes `PENDING` last and never consumes a response; Phase 1's mock remains the only test-time action override.

**Tech Stack:** pokeemerald-expansion C, devkitARM, mGBA battle-test runner, existing battle state and target helpers.

**Specification:** [`../specs/2026-07-26-phase-2-legal-action-snapshot.md`](../specs/2026-07-26-phase-2-legal-action-snapshot.md)  
**Flow review:** [`../reviews/2026-07-26-phase-2-legal-action-snapshot-flow-review.md`](../reviews/2026-07-26-phase-2-legal-action-snapshot-flow-review.md)

---

## File map

- Create: `include/battle_agent.h` — V1 protocol constants, fixed-layout mailbox types, public producer API, and `TESTING` inspection API.
- Create: `src/battle_agent.c` — EWRAM mailbox storage, eligibility, initialization, snapshot copy, target normalization, legal-action construction, and test inspection helpers.
- Modify: `src/battle_main.c` — call the producer immediately after `ComputeBattleAiScores` and before the Phase 1 test mock hook.
- Modify: `include/test/battle.h` — declare a Phase 2 mailbox expectation directive for AI battle tests.
- Modify: `test/test_runner_battle.c` — persist and check mailbox expectations at the AI action-selection boundary.
- Modify: `test/battle/ai.c` — add focused Phase 2 Calvin, fallback, target, zero-PP, and stale-publication tests.
- Modify: `docs/openai-battle-agent/2026-07-18-mgba-ai-trainer-design.md` — link the completed Phase 2 artifacts.
- Modify: `docs/openai-battle-agent/specs/2026-07-26-phase-2-legal-action-snapshot.md` — add implementation evidence after verification.
- Create: `docs/openai-battle-agent/reviews/2026-07-26-phase-2-build-and-test-evidence.md` — record WSL builds, focused tests, full-suite result, and Calvin smoke test.

## Task 1: Add the mailbox contract and isolated test expectation

**Files:**

- Create: `include/battle_agent.h`
- Create: `src/battle_agent.c`
- Modify: `include/test/battle.h`
- Modify: `test/test_runner_battle.c`
- Test: `test/battle/ai.c`

- [ ] **Step 1: Add a failing Calvin mailbox expectation test.**

  Add an `AI_SINGLE_BATTLE_TEST` named `External AI snapshot publishes Calvin's legal move actions`. Configure `TRAINER_CALVIN_1`, a Gastly player, and Lillipup with `MOVE_LEER`, `MOVE_TACKLE`, and `MOVE_REST`. During its first turn, expect a pending request with three entries, request sequence `1`, and no response status. Use a new directive:

  ```c
  #define EXPECT_AGENT_REQUEST(sequence, actionCount) \
      ExpectBattleAgentRequest_(__LINE__, sequence, actionCount)
  ```

  Place it inside the first `TURN` after `MOVE(player, MOVE_MEAN_LOOK)` and retain `EXPECT_MOVE(opponent, MOVE_LEER)` to prove normal AI remains in control.

- [ ] **Step 2: Run the focused test to verify it fails because the directive and mailbox do not exist.**

  Run in WSL:

  ```bash
  make -j"$(nproc)" check TESTS='External AI snapshot publishes Calvin'
  ```

  Expected: compile failure identifying the undefined expectation directive/API. Do not add the producer yet.

- [ ] **Step 3: Define the V1 contract and mailbox storage.**

  In `include/battle_agent.h`, define these constants and types with only fixed-width fields:

  ```c
  #define BATTLE_AGENT_PROTOCOL_MAGIC 0x42414731 // "BAG1"
  #define BATTLE_AGENT_PROTOCOL_VERSION 1

  enum BattleAgentRequestStatus
  {
      BATTLE_AGENT_REQUEST_IDLE,
      BATTLE_AGENT_REQUEST_PENDING,
  };

  enum BattleAgentResponseStatus
  {
      BATTLE_AGENT_RESPONSE_NONE,
  };

  struct BattleAgentBattlerSnapshotV1
  {
      u16 species;
      u16 hp;
      u16 maxHp;
      u32 status1;
      u8 statStages[NUM_BATTLE_STATS];
  };

  struct BattleAgentMoveSnapshotV1
  {
      u16 move;
      u8 pp;
  };

  struct BattleAgentSnapshotV1
  {
      struct BattleAgentBattlerSnapshotV1 battlers[MAX_BATTLERS_COUNT];
      struct BattleAgentMoveSnapshotV1 requesterMoves[MAX_MON_MOVES];
      u16 weather;
      u8 terrain;
      u32 fieldStatuses;
      u32 sideStatuses[NUM_BATTLE_SIDES];
  };

  struct BattleAgentLegalActionV1
  {
      u8 actionIndex;
      u8 moveSlot;
      u8 targetBattler;
  };

  struct BattleAgentMailboxV1
  {
      u32 magic;
      u16 protocolVersion;
      u8 requestStatus;
      u8 responseStatus;
      u32 requestSequence;
      u32 responseSequence;
      u8 requestingBattler;
      u8 battleMode;
      u16 turnSequence;
      struct BattleAgentSnapshotV1 snapshot;
      u8 legalActionCount;
      struct BattleAgentLegalActionV1 legalActions[MAX_MON_MOVES];
      u8 responseLegalActionIndex;
  };

  extern struct BattleAgentMailboxV1 gBattleAgentMailbox;
  bool32 BattleAgent_TryPublishRequest(u32 battler);
  ```

  Add `STATIC_ASSERT` checks for the known protocol version, every action-field width, and `offsetof(struct BattleAgentMailboxV1, legalActions) > offsetof(struct BattleAgentMailboxV1, snapshot)`. In `src/battle_agent.c`, define `EWRAM_DATA struct BattleAgentMailboxV1 gBattleAgentMailbox;` and a static `BattleAgent_EnsureInitialized` that clears it, writes magic/version, and leaves request/response status at `IDLE`/`NONE`.

- [ ] **Step 4: Add the test directive plumbing without publication behavior.**

  In `include/test/battle.h`, declare:

  ```c
  void ExpectBattleAgentRequest_(u32 sourceLine, u32 sequence, u8 actionCount);
  ```

  In `test/test_runner_battle.c`, add an expectation record to the current battle-test data containing `expected`, `sourceLine`, `sequence`, and `actionCount`. Reject directive use outside an AI test `TURN`. At the existing opponent-action expectation boundary, compare `gBattleAgentMailbox.requestSequence`, `requestStatus`, `responseStatus`, and `legalActionCount` against the record. Report mismatch with `Test_ExitWithResult(TEST_RESULT_FAIL, ...)` using `sourceLine`.

- [ ] **Step 5: Run the focused test and verify it fails for the expected absent publication.**

  Run:

  ```bash
  make -j"$(nproc)" check TESTS='External AI snapshot publishes Calvin'
  ```

  Expected: test compiles, reaches the expectation, and fails because the mailbox remains `IDLE` with sequence `0`.

- [ ] **Step 6: Commit the contract/test-infrastructure slice.**

  ```bash
  git add include/battle_agent.h src/battle_agent.c include/test/battle.h test/test_runner_battle.c test/battle/ai.c
  git commit -m "feat(battle): define AI agent mailbox contract"
  ```

## Task 2: Build visible snapshots and normalized legal actions

**Files:**

- Modify: `src/battle_agent.c`
- Modify: `include/battle_agent.h`
- Modify: `test/battle/ai.c`
- Test: `test/battle/ai.c`

- [ ] **Step 1: Add failing action-content tests.**

  Add these tests, each with `TRAINER_CALVIN_1` and an expected vanilla move:

  ```c
  AI_SINGLE_BATTLE_TEST("External AI snapshot includes selected and self targets")
  {
      GIVEN {
          TRAINER_OPPONENT(TRAINER_CALVIN_1);
          AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE);
          PLAYER(SPECIES_GASTLY) { Moves(MOVE_MEAN_LOOK); }
          OPPONENT(SPECIES_LILLIPUP) { Moves(MOVE_LEER, MOVE_TACKLE, MOVE_REST); }
      } WHEN {
          TURN {
              MOVE(player, MOVE_MEAN_LOOK);
              EXPECT_AGENT_ACTION(0, 0, B_POSITION_PLAYER_LEFT);
              EXPECT_AGENT_ACTION(1, 1, B_POSITION_PLAYER_LEFT);
              EXPECT_AGENT_ACTION(2, 2, B_POSITION_OPPONENT_LEFT);
              EXPECT_MOVE(opponent, MOVE_LEER);
          }
      }
  }
  ```

  Add `EXPECT_AGENT_ACTION(actionIndex, moveSlot, targetBattler)` beside the request directive. Add separate failing tests for a `MOVE_NONE` slot, zero-PP `Tackle`, and an unflagged `TRAINER_BILLY` expectation of unchanged sequence `0`.

- [ ] **Step 2: Run the new tests to verify they fail because the list is not built.**

  ```bash
  make -j"$(nproc)" check TESTS='External AI snapshot'
  ```

  Expected: action assertions fail while the mailbox contains no actions.

- [ ] **Step 3: Implement eligibility, snapshot copy, and target normalizer.**

  Add these static functions to `src/battle_agent.c`:

  ```c
  static bool32 BattleAgent_IsEligible(u32 battler);
  static bool32 BattleAgent_NormalizeSingleTarget(u32 requester, u16 move, u8 *target);
  static void BattleAgent_CopySnapshot(u32 requester);
  static void BattleAgent_BuildLegalActions(u32 requester);
  ```

  `BattleAgent_IsEligible` must mirror Phase 1's opponent/trainer/single/excluded-flag and `externalAi` checks, require `aiMoveOrAction[battler] < MAX_MON_MOVES`, and reject `BATTLE_TYPE_RECORDED` except under `#if TESTING` when `gTestRunnerEnabled` is true.

  `BattleAgent_NormalizeSingleTarget` must call `GetBattlerMoveTargetType(requester, move)`, use the requester for `MOVE_TARGET_USER` and `MOVE_TARGET_USER_OR_SELECTED`, use the sole live player-side battler for `MOVE_TARGET_SELECTED`, `MOVE_TARGET_DEPENDS`, `MOVE_TARGET_RANDOM`, `MOVE_TARGET_BOTH`, `MOVE_TARGET_FOES_AND_ALLY`, and `MOVE_TARGET_OPPONENTS_FIELD`, reject all other categories, and return false when the resulting target is out of range or fainted.

  `BattleAgent_CopySnapshot` must copy only the specification's public fields from `gBattleMons`, `gBattleWeather`, `gBattleTerrain`, `gFieldStatuses`, and `gSideStatuses`. It must copy all four requester move IDs/PP values even for unusable slots.

  `BattleAgent_BuildLegalActions` must recompute `CheckMoveLimitations(requester, 0, MOVE_LIMITATIONS_ALL)`, skip `MOVE_NONE` and masked slots, call the normalizer, and append dense entries where `actionIndex == legalActionCount` before incrementing `legalActionCount`.

- [ ] **Step 4: Add test-only direct normalization coverage.**

  Under `#if TESTING`, expose:

  ```c
  bool32 BattleAgent_TestNormalizeSingleTarget(u32 requester, u16 move, u8 *target);
  ```

  Add a direct `TEST("External AI snapshot rejects a fainted selected target")` in `test/battle/ai.c` that sets a single-battle fixture's player target to fainted, calls the helper, and asserts `FALSE`. Reset the touched test fixture state before return. This isolates a state that a normal controller turn cannot select.

- [ ] **Step 5: Run focused tests and verify they pass.**

  ```bash
  make -j"$(nproc)" check TESTS='External AI snapshot'
  ```

  Expected: all mailbox request/action, self-target, selected-target, zero-PP, empty, unflagged, and direct fainted-target tests pass; vanilla expected moves remain unchanged.

- [ ] **Step 6: Commit legal-action construction.**

  ```bash
  git add include/battle_agent.h src/battle_agent.c include/test/battle.h test/test_runner_battle.c test/battle/ai.c
  git commit -m "feat(battle): publish legal AI move actions"
  ```

## Task 3: Publish from the battle seam and prove stale replacement/fallback

**Files:**

- Modify: `src/battle_main.c`
- Modify: `src/battle_agent.c`
- Modify: `test/battle/ai.c`
- Test: `test/battle/ai.c`

- [ ] **Step 1: Add failing publication-sequence tests.**

  Add a two-turn Calvin test that expects request sequence `1` on turn one, sets non-`NONE` test response fields through a narrow `SET_AGENT_TEST_RESPONSE(sequence, actionIndex)` directive, and expects sequence `2`, `responseStatus == BATTLE_AGENT_RESPONSE_NONE`, and cleared response sequence/index on turn two. Add an unflagged-Billy test asserting no sequence/status mutation. Both tests must also expect the same vanilla emitted moves as before.

- [ ] **Step 2: Run the sequence tests to verify they fail before the seam call exists.**

  ```bash
  make -j"$(nproc)" check TESTS='External AI snapshot replaces stale request'
  ```

  Expected: the second-turn expectation fails because no producer call publishes a new request.

- [ ] **Step 3: Call the producer at the post-score seam.**

  In `src/battle_main.c`, retain this order exactly:

  ```c
  gBattleStruct->aiMoveOrAction[battler] = ComputeBattleAiScores(battler);
  BattleAgent_TryPublishRequest(battler);
  BattleAI_TryApplyExternalAiMockMove(battler);
  ```

  `BattleAgent_TryPublishRequest` must return `FALSE` without changing mailbox state when ineligible. For an eligible move fallback, it must initialize as needed, increment `requestSequence` and `turnSequence`, clear `responseStatus`, `responseSequence`, and `responseLegalActionIndex`, copy snapshot and legal actions, then write `requestStatus = BATTLE_AGENT_REQUEST_PENDING` last. It must never read response fields and must never write `aiMoveOrAction` or `aiChosenTarget`.

- [ ] **Step 4: Run all Phase 1 and Phase 2 focused tests.**

  ```bash
  make -j"$(nproc)" check TESTS='External AI'
  ```

  Expected: Phase 1's seven mock/fallback tests and every Phase 2 snapshot test pass. The accepted Phase 1 mock still changes only its legal test move; all Phase 2 publication tests preserve vanilla moves.

- [ ] **Step 5: Commit the seam integration.**

  ```bash
  git add src/battle_main.c src/battle_agent.c test/battle/ai.c include/test/battle.h test/test_runner_battle.c
  git commit -m "feat(battle): publish AI agent requests after scoring"
  ```

## Task 4: Verify production fallback and document Phase 2

**Files:**

- Modify: `docs/openai-battle-agent/2026-07-18-mgba-ai-trainer-design.md`
- Modify: `docs/openai-battle-agent/specs/2026-07-26-phase-2-legal-action-snapshot.md`
- Create: `docs/openai-battle-agent/reviews/2026-07-26-phase-2-build-and-test-evidence.md`
- Test: WSL build/test commands and mGBA smoke test

- [ ] **Step 1: Review scope and protocol boundaries.**

  ```bash
  git diff -- include/battle_agent.h src/battle_agent.c src/battle_main.c include/test/battle.h test/test_runner_battle.c test/battle/ai.c
  git diff --check
  ```

  Expected: no Lua, socket, Python, model, response-application, switch/item, double, or unrelated trainer change appears. The only production seam is one publication call after ordinary AI scoring.

- [ ] **Step 2: Run fresh WSL verification.**

  ```bash
  make -j"$(nproc)"
  make -j"$(nproc)" check TESTS='External AI'
  make -j"$(nproc)" check
  ```

  Expected: the normal ROM builds; focused tests pass; full-suite results are recorded exactly and compared with the accepted repository baseline policy from Phase 1.

- [ ] **Step 3: Smoke-test the production ROM.**

  Open `pokeemerald.gba` in mGBA without Lua or a service, start Calvin's Route 102 battle, play at least two turns, and finish or safely exit. Expected: normal battle flow with no pause, UI change, or external-process requirement.

- [ ] **Step 4: Record evidence and links.**

  Write the evidence review with `Build`, `Focused tests`, `Full tests`, `Route 102 smoke test`, `Mailbox behavior`, `Fallback result`, and `Known limitations` headings. State that `PENDING` is publication-only, no response is consumed, and no bridge/service/model exists. Link the Phase 2 specification, flow review, plan, and evidence review from the parent roadmap.

- [ ] **Step 5: Commit documentation only after evidence is recorded.**

  ```bash
  git add docs/openai-battle-agent/2026-07-18-mgba-ai-trainer-design.md docs/openai-battle-agent/specs/2026-07-26-phase-2-legal-action-snapshot.md docs/openai-battle-agent/reviews/2026-07-26-phase-2-legal-action-snapshot-flow-review.md docs/openai-battle-agent/reviews/2026-07-26-phase-2-build-and-test-evidence.md docs/openai-battle-agent/plans/2026-07-26-phase-2-legal-action-snapshot.md
  git commit -m "docs(ai): record phase 2 legal-action snapshot"
  ```

## Plan self-review

- **Specification coverage:** Tasks 1–3 cover mailbox layout, publication eligibility, visible snapshot, legal action construction, target normalization, stale replacement, and no-response behavior; Task 4 covers build, test, smoke, and documentation evidence.
- **Type consistency:** The mailbox uses `u8`, `u16`, and `u32`, `MAX_MON_MOVES`, `MAX_BATTLERS_COUNT`, and `NUM_BATTLE_SIDES` consistently. A legal action always references a dense `actionIndex`, move slot, and normalized target battler.
- **Protocol compatibility:** Phase 2 writes only protocol version 1 request fields. It defines no transport, raw move input, or response acceptance.
- **Battle-mechanics safety:** Vanilla scoring occurs first and remains authoritative. The producer exits for non-move fallbacks and never mutates action, target, controller, damage, switch, or item state.
- **Scope:** Only the existing Calvin opt-in can publish. Doubles, broad trainer enablement, mGBA, services, and models remain separate later phases.
