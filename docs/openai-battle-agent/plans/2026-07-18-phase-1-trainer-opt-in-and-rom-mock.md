# Phase 1: Trainer Opt-In and ROM Mock Implementation Plan

> **For agentic workers:** Execute this plan inline in the current session. Follow the Phase Documentation Gate in `AGENTS.md`. Keep the user's unrelated map-script changes and the earlier local build-compatibility fixes out of every Phase 1 staging command.

**Goal:** Add a generic `Trainer.externalAi` bit, opt in only Route 102's `TRAINER_CALVIN_1`, and prove a test-only ROM mock can replace a flagged single trainer's legal move while all no-response and invalid-response paths retain vanilla AI.

**Architecture:** `src/battle_main.c` continues to compute the ordinary action and target first. A focused helper in `src/battle_ai_main.c` then consults trainer data, battle-type eligibility, and a test-only move-slot response; it accepts only a currently usable `MOVE_TARGET_SELECTED` move whose existing engine target is a player-side battler, and otherwise leaves the existing values untouched. `AI_SINGLE_BATTLE_TEST` necessarily uses `BATTLE_TYPE_RECORDED`; only under `#if TESTING`, with `gTestRunnerEnabled` and a pending mock slot, the hook permits that one harness flag. The battle test runner selects real immutable trainer IDs and supplies the mock response before battle initialization.

**Tech Stack:** `pokeemerald-expansion` C17 ROM build, existing battle-test DSL, WSL Ubuntu `make`, and the project ARM toolchain.

**Specification:** [`../specs/2026-07-18-phase-1-trainer-opt-in-and-rom-mock.md`](../specs/2026-07-18-phase-1-trainer-opt-in-and-rom-mock.md)

**Flow review:** [`../reviews/2026-07-18-phase-1-trainer-opt-in-and-rom-mock-flow-review.md`](../reviews/2026-07-18-phase-1-trainer-opt-in-and-rom-mock-flow-review.md)

---

## Planned file structure

- Modify: `include/data.h` — name the second trainer-configuration bit as `externalAi` while retaining the trainer structure layout.
- Modify: `src/data/trainers.h` — set `.externalAi = TRUE` only on `TRAINER_CALVIN_1`.
- Modify: `include/battle_ai_main.h` — declare the production eligibility/override helper and `#if TESTING` mock controls.
- Modify: `src/battle_ai_main.c` — implement eligibility, move-slot validation, and the test-only response state.
- Modify: `src/battle_main.c` — call the override only after the ordinary AI move/action and target have been stored.
- Modify: `include/test/battle.h` — add `TRAINER_OPPONENT`, `EXTERNAL_AI_MOCK_MOVE`, and `RESET_EXTERNAL_AI_MOCK` test directives.
- Modify: `test/test_runner_battle.c` — configure the real opponent trainer ID and forward mock directives to the `#if TESTING` controls.
- Modify: `test/battle/ai.c` — add focused Phase 1 behavior tests.
- Modify: `docs/openai-battle-agent/2026-07-18-mgba-ai-trainer-design.md` — link the completed Phase 1 plan.
- Modify: `docs/openai-battle-agent/specs/2026-07-18-phase-1-trainer-opt-in-and-rom-mock.md` — preserve the plan link and record fresh verification evidence after implementation.
- Create: `docs/openai-battle-agent/reviews/2026-07-18-phase-1-build-and-test-evidence.md` — record exact WSL build, focused-test, full-test, and Route 102 smoke-test outcomes.

## Task 1: Add the failing behavior tests and test DSL declarations

**Files:**

- Modify: `include/test/battle.h`
- Modify: `test/battle/ai.c`
- Read: `test/test_runner_battle.c`, `include/battle_ai_main.h`, `src/data/trainers.h`

- [ ] **Step 1: Declare the test DSL surface in `include/test/battle.h`.**

  Add these macros beside `AI_FLAGS` and declarations beside `AIFlags_`:

  ```c
  #define TRAINER_OPPONENT(trainerId) TrainerOpponent_(__LINE__, trainerId)
  #define EXTERNAL_AI_MOCK_MOVE(moveSlot) ExternalAiMockMove_(__LINE__, moveSlot)
  #define RESET_EXTERNAL_AI_MOCK() ExternalAiMockReset_(__LINE__)

  void TrainerOpponent_(u32 sourceLine, u16 trainerId);
  void ExternalAiMockMove_(u32 sourceLine, s8 moveSlot);
  void ExternalAiMockReset_(u32 sourceLine);
  ```

The names must be usable only inside `GIVEN`. `RESET_EXTERNAL_AI_MOCK` must be the first statement in each test's `GIVEN` block.

- [ ] **Step 2: Add the focused test cases to the end of `test/battle/ai.c`.**

  Use `MOVE_LEER` in slot `0` and `MOVE_TACKLE` in slot `1` for accepted and ordinary fallback cases. Use `AI_FLAG_CHECK_BAD_MOVE` with `PLAYER(SPECIES_GASTLY) { Moves(MOVE_MEAN_LOOK); }` so vanilla AI rejects ineffective Normal-type Tackle against Ghost and deterministically selects Leer. The target-rejection case uses `MOVE_REST` in slot `1`, which is otherwise legal but self-targeting; every test has an opponent Lillipup and one turn whose `EXPECT_MOVE` checks the visible result.

Add these seven tests, resetting the mock as the first statement in every `GIVEN` block:

  ```c
  AI_SINGLE_BATTLE_TEST("External AI mock accepts Calvin's legal move slot")
{
    GIVEN {
        RESET_EXTERNAL_AI_MOCK();
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE);
          TRAINER_OPPONENT(TRAINER_CALVIN_1);
          EXTERNAL_AI_MOCK_MOVE(1);
          PLAYER(SPECIES_GASTLY) { Moves(MOVE_MEAN_LOOK); }
          OPPONENT(SPECIES_LILLIPUP) { Moves(MOVE_LEER, MOVE_TACKLE); }
    } WHEN {
        TURN { MOVE(player, MOVE_MEAN_LOOK); EXPECT_MOVE(opponent, MOVE_TACKLE); }
    }
}

  AI_SINGLE_BATTLE_TEST("External AI Calvin without a response keeps vanilla move")
{
    GIVEN {
        RESET_EXTERNAL_AI_MOCK();
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE);
          TRAINER_OPPONENT(TRAINER_CALVIN_1);
          PLAYER(SPECIES_GASTLY) { Moves(MOVE_MEAN_LOOK); }
          OPPONENT(SPECIES_LILLIPUP) { Moves(MOVE_LEER, MOVE_TACKLE); }
    } WHEN {
        TURN { MOVE(player, MOVE_MEAN_LOOK); EXPECT_MOVE(opponent, MOVE_LEER); }
    }
}

AI_SINGLE_BATTLE_TEST("External AI Calvin rejects a zero-PP mock move")
{
    GIVEN {
        RESET_EXTERNAL_AI_MOCK();
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE);
          TRAINER_OPPONENT(TRAINER_CALVIN_1);
          EXTERNAL_AI_MOCK_MOVE(1);
          PLAYER(SPECIES_GASTLY) { Moves(MOVE_MEAN_LOOK); }
          OPPONENT(SPECIES_LILLIPUP) {
              MovesWithPP(
                  ((struct moveWithPP){ .moveId = MOVE_LEER, .pp = 40 }),
                  ((struct moveWithPP){ .moveId = MOVE_TACKLE, .pp = 0 }));
          }
    } WHEN {
        TURN { MOVE(player, MOVE_MEAN_LOOK); EXPECT_MOVE(opponent, MOVE_LEER); }
    }
}

  AI_SINGLE_BATTLE_TEST("External AI Calvin rejects an out-of-range mock move")
{
    GIVEN {
        RESET_EXTERNAL_AI_MOCK();
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE);
          TRAINER_OPPONENT(TRAINER_CALVIN_1);
          EXTERNAL_AI_MOCK_MOVE(MAX_MON_MOVES);
          PLAYER(SPECIES_GASTLY) { Moves(MOVE_MEAN_LOOK); }
          OPPONENT(SPECIES_LILLIPUP) { Moves(MOVE_LEER, MOVE_TACKLE); }
    } WHEN {
        TURN { MOVE(player, MOVE_MEAN_LOOK); EXPECT_MOVE(opponent, MOVE_LEER); }
    }
}

  AI_SINGLE_BATTLE_TEST("External AI Calvin rejects an empty mock move")
{
    GIVEN {
        RESET_EXTERNAL_AI_MOCK();
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE);
          TRAINER_OPPONENT(TRAINER_CALVIN_1);
          EXTERNAL_AI_MOCK_MOVE(2);
          PLAYER(SPECIES_GASTLY) { Moves(MOVE_MEAN_LOOK); }
          OPPONENT(SPECIES_LILLIPUP) { Moves(MOVE_LEER, MOVE_TACKLE, MOVE_NONE); }
    } WHEN {
        TURN { MOVE(player, MOVE_MEAN_LOOK); EXPECT_MOVE(opponent, MOVE_LEER); }
    }
}

AI_SINGLE_BATTLE_TEST("External AI Calvin rejects a self-targeting mock move")
{
    GIVEN {
        RESET_EXTERNAL_AI_MOCK();
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE);
        TRAINER_OPPONENT(TRAINER_CALVIN_1);
        EXTERNAL_AI_MOCK_MOVE(1);
        PLAYER(SPECIES_GASTLY) { Moves(MOVE_MEAN_LOOK); }
        OPPONENT(SPECIES_LILLIPUP) { Moves(MOVE_LEER, MOVE_REST); }
    } WHEN {
        TURN { MOVE(player, MOVE_MEAN_LOOK); EXPECT_MOVE(opponent, MOVE_LEER); }
    }
}

  AI_SINGLE_BATTLE_TEST("External AI mock does not affect an unflagged trainer")
{
    GIVEN {
        RESET_EXTERNAL_AI_MOCK();
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE);
          TRAINER_OPPONENT(TRAINER_BILLY);
          EXTERNAL_AI_MOCK_MOVE(1);
          PLAYER(SPECIES_GASTLY) { Moves(MOVE_MEAN_LOOK); }
          OPPONENT(SPECIES_LILLIPUP) { Moves(MOVE_LEER, MOVE_TACKLE); }
    } WHEN {
        TURN { MOVE(player, MOVE_MEAN_LOOK); EXPECT_MOVE(opponent, MOVE_LEER); }
    }
}
  ```

- [ ] **Step 3: Run the focused test to prove it fails for the missing DSL.**

  Run in WSL:

  ```bash
  make check TESTS='External AI'
  ```

  Expected: linking fails because `TrainerOpponent_`, `ExternalAiMockMove_`, and `ExternalAiMockReset_` have declarations but no implementations yet. Do not change production battle code until this failure is observed.

## Task 2: Implement test-runner configuration and test-only mock controls

**Files:**

- Modify: `test/test_runner_battle.c`
- Modify: `include/battle_ai_main.h`
- Modify: `src/battle_ai_main.c`
- Read: `include/test/battle.h`, `include/battle.h`, `include/constants/battle.h`

- [ ] **Step 1: Implement the test-runner directives.**

  Include `battle_ai_main.h` in `test/test_runner_battle.c`. Add these functions next to `AIFlags_`:

  ```c
  void TrainerOpponent_(u32 sourceLine, u16 trainerId)
  {
      INVALID_IF(!IsAITest(), "TRAINER_OPPONENT is usable only in AI_SINGLE_BATTLE_TEST & AI_DOUBLE_BATTLE_TEST");
      INVALID_IF(trainerId >= TRAINERS_COUNT, "Illegal trainer: %d", &trainerId);
      DATA.recordedBattle.opponentA = trainerId;
  }

  void ExternalAiMockMove_(u32 sourceLine, s8 moveSlot)
  {
      INVALID_IF(!IsAITest(), "EXTERNAL_AI_MOCK_MOVE is usable only in AI_SINGLE_BATTLE_TEST & AI_DOUBLE_BATTLE_TEST");
      BattleAI_TestSetExternalAiMockMoveSlot(moveSlot);
  }

  void ExternalAiMockReset_(u32 sourceLine)
  {
      BattleAI_TestResetExternalAiMockResponse();
  }
  ```

  `TRAINER_OPPONENT` changes only the recorded trainer ID before `SetVariablesForRecordedBattle`; it does not edit `gTrainers` or alter the synthetic Pokémon configured by `OPPONENT(...)`.

  Reset the mock at the start of each `BattleTest_Run`, before invoking the test function. Keep `RESET_EXTERNAL_AI_MOCK()` as the first statement in each `GIVEN` block: the runner-level reset isolates battles, while the directive reset isolates parameterized invocations within a battle.

- [ ] **Step 2: Add test-only mock declarations in `include/battle_ai_main.h`.**

  Append these declarations before the closing include guard:

  ```c
  bool32 BattleAI_TryApplyExternalAiMockMove(u32 battler);

  #if TESTING
  void BattleAI_TestSetExternalAiMockMoveSlot(s8 moveSlot);
  void BattleAI_TestResetExternalAiMockResponse(void);
  #endif
  ```

- [ ] **Step 3: Implement the isolated mock state in `src/battle_ai_main.c`.**

  Add a private signed slot initialized to `-1` inside `#if TESTING`, plus the two declared setters. The reset function must restore `-1`. `BattleTest_Run` resets this state at each battle boundary, and every `GIVEN` block resets it again before configuration to protect parameterized invocations. Defer the private lookup to Task 3, where it is compiled only under `TESTING` together with its caller; this keeps Task 2's interim build free of an unused static helper:

  ```c
  #if TESTING
  static s8 sTestExternalAiMockMoveSlot = -1;

  void BattleAI_TestSetExternalAiMockMoveSlot(s8 moveSlot)
  {
      sTestExternalAiMockMoveSlot = moveSlot;
  }

  void BattleAI_TestResetExternalAiMockResponse(void)
  {
      sTestExternalAiMockMoveSlot = -1;
  }
  #endif
  ```

- [ ] **Step 4: Re-run the focused test.**

  ```bash
  make check TESTS='External AI'
  ```

  Expected: compilation now reaches the battle assertions, but the first test fails because Calvin is not yet configured and the battle hook does not yet consume the mock response.

## Task 3: Add trainer configuration and the safe ROM decision hook

**Files:**

- Modify: `include/data.h`
- Modify: `src/data/trainers.h`
- Modify: `src/battle_ai_main.c`
- Modify: `src/battle_main.c`
- Read: `include/battle_ai_main.h`, `include/battle_ai_util.h`, `src/battle_ai_switch_items.c`, `src/battle_controller_opponent.c`

- [ ] **Step 1: Name the trainer opt-in bit and configure Calvin.**

  Change `struct Trainer` exactly as follows:

  ```c
  /*0x1E*/ bool8 doubleBattle:1;
           bool8 externalAi:1;
           u8 padding:6;
  ```

  Add only this designated initializer to the existing `TRAINER_CALVIN_1` entry:

  ```c
  .externalAi = TRUE,
  ```

  Do not add the field to Calvin's rematches, Billy, or any other trainer. Do not modify any `aiFlags` value.

- [ ] **Step 2: Add the production eligibility and validation helpers in `src/battle_ai_main.c`.**

  Define `GetExternalAiMockMoveSlot` only inside `#if TESTING`, next to the mock state, and use it only from the `#if TESTING` branch of `BattleAI_TryApplyExternalAiMockMove`. The normal-build branch returns `FALSE` before any test-only mock lookup, so it allocates no mock state and preserves vanilla AI. Implement the helper with this exact decision order:

  ```c
  bool32 BattleAI_TryApplyExternalAiMockMove(u32 battler)
  {
  #if TESTING
      s8 moveSlot = GetExternalAiMockMoveSlot();
  #endif

      if (!BattlerHasAi(battler)
       || GetBattlerSide(battler) != B_SIDE_OPPONENT
       || !(gBattleTypeFlags & BATTLE_TYPE_TRAINER)
       || (gBattleTypeFlags & (BATTLE_TYPE_DOUBLE | BATTLE_TYPE_MULTI | BATTLE_TYPE_LINK
                             | BATTLE_TYPE_SAFARI | BATTLE_TYPE_PALACE
                             | BATTLE_TYPE_FRONTIER | BATTLE_TYPE_EREADER_TRAINER
                             | BATTLE_TYPE_TRAINER_HILL | BATTLE_TYPE_SECRET_BASE
                             | BATTLE_TYPE_TWO_OPPONENTS))
       || !gTrainers[gTrainerBattleOpponent_A].externalAi)
          return FALSE;

      if (gBattleStruct->aiMoveOrAction[battler] >= MAX_MON_MOVES)
          return FALSE;

  #if !TESTING
      if (gBattleTypeFlags & BATTLE_TYPE_RECORDED)
          return FALSE;

      return FALSE;
  #else
      if ((gBattleTypeFlags & BATTLE_TYPE_RECORDED)
       && (!gTestRunnerEnabled || moveSlot < 0))
          return FALSE;

      u8 moveLimitations;

      if (moveSlot < 0 || moveSlot >= MAX_MON_MOVES)
          return FALSE;

      moveLimitations = CheckMoveLimitations(battler, 0, MOVE_LIMITATIONS_ALL);
      if (gBattleMons[battler].moves[moveSlot] == MOVE_NONE
       || (moveLimitations & gBitTable[moveSlot])
       || gBattleMoves[gBattleMons[battler].moves[moveSlot]].target != MOVE_TARGET_SELECTED
       || gBattleStruct->aiChosenTarget[battler] >= MAX_BATTLERS_COUNT
       || GetBattlerSide(gBattleStruct->aiChosenTarget[battler]) != B_SIDE_PLAYER)
          return FALSE;

      gBattleStruct->aiMoveOrAction[battler] = moveSlot;
      return TRUE;
  #endif
  }
  ```

  Keep `gBattleStruct->aiChosenTarget[battler]` untouched. Do not call, alter, or move `AI_TrySwitchOrUseItem`.

- [ ] **Step 3: Invoke the hook after vanilla scoring in `src/battle_main.c`.**

  Preserve the current score computation and add one call immediately after its assignment:

  ```c
  gBattleStruct->aiMoveOrAction[battler] = ComputeBattleAiScores(battler);
  BattleAI_TryApplyExternalAiMockMove(battler);
  ```

  The return value is intentionally ignored: the helper mutates only a validated move slot and leaves the existing action/target unchanged on all other paths.

- [ ] **Step 4: Run the focused tests and confirm the green result.**

  ```bash
  make check TESTS='External AI'
  ```

Expected: all seven external-AI tests pass. The accepted Calvin mock emits Tackle; the absent, out-of-range, empty-slot, self-targeting, and unflagged cases emit Leer; the zero-PP Tackle request emits Leer.

## Task 4: Verify scope, regression safety, and the playable fallback

**Files:**

- Modify: `docs/openai-battle-agent/specs/2026-07-18-phase-1-trainer-opt-in-and-rom-mock.md`
- Modify: `docs/openai-battle-agent/2026-07-18-mgba-ai-trainer-design.md`
- Create: `docs/openai-battle-agent/reviews/2026-07-18-phase-1-build-and-test-evidence.md`
- Read: `AGENTS.md`, the Phase 1 specification and flow review

- [x] **Step 1: Check the trainer-data diff and source scope.**

  Run:

  ```bash
  git diff -- include/data.h src/data/trainers.h src/battle_ai_main.c src/battle_main.c include/battle_ai_main.h include/test/battle.h test/test_runner_battle.c test/battle/ai.c
  git diff --check
  ```

  Expected: the trainer layout has one new named bit, only Calvin's first trainer entry is opted in, and no switch/item controller, trainer party, map script, or battle mechanic file is changed.

- [x] **Step 2: Run the complete automated verification.**

  Run in WSL from the repository root:

  ```bash
  make -j"$(nproc)"
  make -j"$(nproc)" check TESTS='External AI'
  make -j"$(nproc)" check
  ```

Observed on 2026-07-22: the normal build produced the playable ROM, and all seven focused tests passed. The full suite reported 1,122 passed, 24 known-failing, 98 to-do, 34 failed assumptions, and 44 failures. The project owner classified those 44 as accepted existing failures. The Phase 1 source-scope review and focused tests found no Phase 1 regression; the exact result is recorded in the evidence review.

- [x] **Step 3: Perform the Route 102 production-ROM smoke test.**

  Launch the newly built `pokeemerald.gba` in the agreed mGBA emulator without a Lua script or service. Start the Route 102 battle against Youngster Calvin, complete at least one turn, and finish or safely exit the battle.

  Expected: Calvin's battle starts and proceeds with ordinary AI; there is no wait, crash, new UI, or need for an external process. This confirms the no-response fallback in a real playable ROM.

- [x] **Step 4: Record evidence and finish documentation links.**

  Create `docs/openai-battle-agent/reviews/2026-07-18-phase-1-build-and-test-evidence.md` with these headings and the observed date/commands/results: `Build`, `Focused tests`, `Full tests`, `Route 102 smoke test`, `Fallback result`, and `Known limitations`. State that the mock exists only under `TESTING`, no bridge exists, target choice remains engine-owned, and switches/items/doubles are deferred.

  Add the Phase 1 plan and evidence-review links to the parent design and add the evidence-review link to the Phase 1 specification.

- [ ] **Step 5: Create small scoped commits after the recorded verification evidence and final review.**

  Stage only the Phase 1 files, never the user's unrelated map scripts or prior build fixes:

  ```bash
  git add include/data.h src/data/trainers.h include/battle_ai_main.h src/battle_ai_main.c src/battle_main.c include/test/battle.h test/test_runner_battle.c test/battle/ai.c docs/openai-battle-agent/2026-07-18-mgba-ai-trainer-design.md docs/openai-battle-agent/specs/2026-07-18-phase-1-trainer-opt-in-and-rom-mock.md docs/openai-battle-agent/reviews/2026-07-18-phase-1-trainer-opt-in-and-rom-mock-flow-review.md docs/openai-battle-agent/reviews/2026-07-18-phase-1-build-and-test-evidence.md docs/openai-battle-agent/plans/2026-07-18-phase-1-trainer-opt-in-and-rom-mock.md
  git commit -m "feat(battle): add trainer external AI opt-in mock seam"
  git commit -m "test(battle): cover external AI mock fallback"
  git commit -m "docs(ai): record phase 1 verification"
  ```

  Expected: each commit contains only one of the Phase 1 trainer/AI seam, its test-harness coverage, or its documentation/evidence. If unrelated paths appear in `git diff --cached --name-only`, unstage them with `git restore --staged <path>` before committing.

## Plan self-review

- **Specification coverage:** Task 1 supplies visible acceptance and fallback tests; Task 2 gives those tests a real trainer ID and test-only response; Task 3 adds the generic data flag and validated ROM seam; Task 4 verifies build, full regression suite, and the Calvin smoke test.
- **Terminology consistency:** `externalAi`, `aiMoveOrAction`, `aiChosenTarget`, `BATTLE_TYPE_TWO_OPPONENTS`, `moveSlot`, and “fallback” retain the meanings established in the Phase 1 specification.
- **Protocol compatibility:** This plan creates no mailbox, protocol version, memory address, Lua, socket, or service API. The production helper always has no response until a later phase replaces that source.
- **Battle-mechanics safety:** The existing AI always computes first; target, switch, item, score, move effect, damage, and turn order remain engine-owned. A non-move fallback skips the hook.
- **Scope:** The only enabled data entry is `TRAINER_CALVIN_1`. Rematches, other trainers, target selection, switching, items, doubles, emulator integration, and model calls remain out of scope.
