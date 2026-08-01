# Phase 7A One-Trainer Double Battles Implementation Plan

> **For agentic workers:** Execute inline task-by-task. Steps use checkboxes.

**Goal:** Let the external local agent atomically choose both opponent actions
for an intentional one-trainer double battle, including ally-target moves and
voluntary single/double switches.

**Architecture:** Replace the one-requester BAGB/3 mailbox with BAGB/4's
two-controlled-battler batch. The ROM publishes both action lists and retains
both vanilla choices; Lua and Python forward a fixed V4 frame; the local model
uses read-only tools then supplies one actor-keyed pair. The ROM validates the
whole pair and commits it through existing controller paths or restores both
vanilla choices at the existing timeout.

**Tech Stack:** pokeemerald-expansion C battle engine/tests, mGBA Lua,
Python 3 standard-library service/tests, local Ollama tool calling.

**Specification:** [Phase 7A specification](../specs/2026-08-02-phase-7a-single-trainer-doubles.md)

**Flow review:** [Phase 7A flow review](../reviews/2026-08-02-phase-7a-single-trainer-doubles-flow-review.md)

---

## Files

- Modify `include/battle_agent.h`: define BAGB/4 mailbox, double mode,
  two controlled battlers, actor-keyed action lists, paired response, and
  compile-time wire/layout assertions.
- Modify `src/battle_agent.c`: implement eligibility, batch publication,
  double target enumeration, pair validation/commit, paired fallback, and
  atomic wait state.
- Modify `src/battle_ai_main.c`: start one shared external wait only after both
  opponent vanilla move selections exist; leave all out-of-scope modes alone.
- Modify `src/battle_controller_opponent.c`: emit accepted move/switch actions
  from the coordinated pair and suppress normal item/switch selection only
  while that accepted paired action is pending.
- Modify `include/test/battle.h` and `test/test_runner_battle.c`: declare and
  implement actor-keyed request/action/pair-response assertions and injection.
- Modify `test/battle/ai.c`: add Phase 7A ROM integration and fallback cases.
- Modify `tools/mgba-bridge/bridge_protocol.py`: strictly parse/format V4
  request/response frames and actor-keyed actions.
- Modify `tools/mgba-bridge/mgba_bridge.lua`: use V4 sizes/version and write a
  response only after complete-pair validation.
- Modify `tools/mgba-bridge/battle_agent_service.py`: expose V4 tools,
  implement `choose_actions`, and produce paired action audits.
- Modify `tools/mgba-bridge/tests/test_bridge_protocol.py`,
  `test_battle_agent_service.py`, `test_battle_agent_source.py`, and
  `test_mgba_bridge_source.py`: cover the V4 contract and source guards.
- Modify `docs/openai-battle-agent/integration-plan.md` and add
  `docs/openai-battle-agent/reviews/2026-08-02-phase-7a-single-trainer-doubles-evidence.md`
  after verification.

## Task 1: Define and test BAGB/4 wire structures

**Files:**
- Modify: `include/battle_agent.h`, `tools/mgba-bridge/bridge_protocol.py`
- Test: `tools/mgba-bridge/tests/test_bridge_protocol.py`

- [ ] **Step 1: Write failing protocol tests.** Add V4 fixtures containing
  `battle_mode=TRAINER_DOUBLE`, controlled battlers `[1, 3]`, four battlers,
  two action-list counts, and a valid response pair:

  ```python
  request = parse_request_frame(v4_double_request_frame())
  self.assertEqual(request.controlled_battlers, (1, 3))
  self.assertEqual(request.actions_by_battler[1][0].target_battler, 3)
  self.assertEqual(format_response_frame(7, ((1, 0), (3, 2))), V4_PAIR_RESPONSE)
  ```

  Add rejection tests for V3 version, wrong length, duplicate actor, missing
  actor, foreign actor, action index outside that actor's list, and a response
  with trailing bytes.

- [ ] **Step 2: Run the focused tests and observe failure.**

  ```bash
  python3 -m unittest discover -s tools/mgba-bridge/tests -p 'test_bridge_protocol.py' -q
  ```

  Expected: failures because V3 accepts only one requester and one action.

- [ ] **Step 3: Implement the smallest V4 layout.** Replace V3 names and
  constants consistently with `BATTLE_AGENT_PROTOCOL_VERSION 4`,
  `BATTLE_AGENT_BATTLE_MODE_TRAINER_DOUBLE 2`, two controlled-battler IDs,
  per-actor counts, `BATTLE_AGENT_MAX_ACTIONS_PER_BATTLER 22`, and a 44-record
  bounded action area. Add `actorBattler` to the action record and two
  `{actorBattler, actionIndex}` response records. Mirror every C offset/size
  assertion in `bridge_protocol.py`'s fixed frame decoder and formatter.

- [ ] **Step 4: Run focused protocol tests.**

  ```bash
  python3 -m unittest discover -s tools/mgba-bridge/tests -p 'test_bridge_protocol.py' -q
  ```

  Expected: all protocol tests pass; invalid frames raise `ProtocolError`.

## Task 2: Add test-runner support for one atomic pair

**Files:**
- Modify: `include/test/battle.h`, `test/test_runner_battle.c`
- Test: `test/battle/ai.c`

- [ ] **Step 1: Write a failing double test.** Add an
  `AI_DOUBLE_BATTLE_TEST` that declares one expected V4 request, both controlled
  battlers, one action list for each, and one injected pair response:

  ```c
  EXPECT_AGENT_DOUBLE_REQUEST(1, B_POSITION_OPPONENT_LEFT, B_POSITION_OPPONENT_RIGHT);
  EXPECT_AGENT_DOUBLE_ACTION(B_POSITION_OPPONENT_LEFT, 0, 0, B_POSITION_PLAYER_LEFT);
  EXPECT_AGENT_DOUBLE_ACTION(B_POSITION_OPPONENT_RIGHT, 0, 0, B_POSITION_PLAYER_RIGHT);
  SET_AGENT_DOUBLE_TEST_RESPONSE(1, B_POSITION_OPPONENT_LEFT, 0,
                                 B_POSITION_OPPONENT_RIGHT, 0);
  ```

- [ ] **Step 2: Run the focused ROM test and observe failure.**

  ```bash
  make -j16 check TESTS='External AI double publishes one coordinated request'
  ```

  Expected: compile failure because the test DSL and injector do not exist.

- [ ] **Step 3: Implement test-only expectation storage and injection.** Add
  actor-keyed action arrays sized by `BATTLE_AGENT_MAX_ACTIONS_PER_BATTLER` to
  `ExpectedBattleAgentRequest`; add the three macros/functions above; update
  `CheckBattleAgentRequest` to verify V4 pair metadata; inject both response
  entries together only when the expected request is pending.

- [ ] **Step 4: Re-run the focused test.**

  ```bash
  make -j16 check TESTS='External AI double publishes one coordinated request'
  ```

  Expected: it compiles but fails at runtime until Task 3 publishes a pair.

## Task 3: Publish one legal paired request

**Files:**
- Modify: `src/battle_agent.c`, `src/battle_ai_main.c`, `include/battle_agent.h`
- Test: `test/battle/ai.c`

- [ ] **Step 1: Expand the failing ROM cases.** Add cases asserting that a
  one-trainer double publishes exactly one request with four battlers and that
  no request publishes for `BATTLE_TYPE_TWO_OPPONENTS`,
  `BATTLE_TYPE_INGAME_PARTNER`, an absent battler, recharge, multi-turn lock,
  forced replacement, or a non-move vanilla decision.

- [ ] **Step 2: Run the cases and observe current behavior.**

  ```bash
  make -j16 check TESTS='External AI double'
  ```

  Expected: intentional-double cases fail because `BattleAgent_IsEligible`
  rejects `BATTLE_TYPE_DOUBLE`; exclusion cases remain green.

- [ ] **Step 3: Implement shared wait publication.** Add
  `BattleAgent_BeginExternalDoubleWait(left, right)` and a batch wait record
  that saves both vanilla move/target choices under one sequence. Permit only
  one-trainer doubles with two living, normal-move AI opponents. Have the AI
  selection path call it after both vanilla choices exist; subsequent opponent
  callbacks attach to that same batch rather than publishing again. Copy all
  four active snapshots and the one shared opponent party.

- [ ] **Step 4: Build actor-keyed legal lists.** For each controlled opponent,
  call `CheckMoveLimitations`; for each usable move enumerate exact live
  selectable targets using the engine's target/`CanTargetBattler` logic. Emit
  one `target=NONE` action for non-selectable spread, side, or field moves.
  Append ascending party slots that pass the existing live switch checks. Do
  not include an active, empty, fainted, trapped, locked, or duplicate-actor
  action.

- [ ] **Step 5: Re-run the double publication cases.**

  ```bash
  make -j16 check TESTS='External AI double'
  ```

  Expected: exact request metadata/actions pass; the response execution cases
  still fail until Task 4.

## Task 4: Validate and commit the complete pair

**Files:**
- Modify: `src/battle_agent.c`, `src/battle_controller_opponent.c`
- Test: `test/battle/ai.c`

- [ ] **Step 1: Write failing response cases.** Add tests for: Helping Hand on
  the ally plus an attack; move plus switch; distinct double switch; duplicate
  shared switch slot; stale sequence; missing right actor; duplicate left
  actor; a now-fainted reserve; and a target that became absent. Every invalid
  pair must assert neither opponent uses the injected action.

- [ ] **Step 2: Run the response cases and observe failure.**

  ```bash
  make -j16 check TESTS='External AI double'
  ```

  Expected: valid pairs cannot yet be consumed and invalid pairs are not
  atomically rejected.

- [ ] **Step 3: Implement pair validation.** Verify request status/sequence,
  exactly the two controlled actor IDs, and each actor's current action record.
  Re-run move limitations and target legality; re-run switchability/party
  validity; reject if two switches select the same slot or either slot is
  currently active. Store neither action until every check succeeds.

- [ ] **Step 4: Implement atomic commit and fallback.** On success, write both
  existing `aiMoveOrAction`, `aiChosenTarget`, and/or `AI_monToSwitchIntoId`
  values, then mark both controller emissions accepted. On failure leave the
  batch pending. At the 900-frame deadline restore both saved vanilla choices,
  clear the shared response/wait state, and clear one thinking message. Update
  opponent controller emission so an accepted pair uses normal move and switch
  controller paths and never calls item selection for that turn.

- [ ] **Step 5: Re-run the response cases.**

  ```bash
  make -j16 check TESTS='External AI double'
  ```

  Expected: combo, move-plus-switch, distinct double-switch, and all atomic
  rejection/fallback cases pass.

## Task 5: Teach Lua and the tool agent BAGB/4

**Files:**
- Modify: `tools/mgba-bridge/mgba_bridge.lua`,
  `tools/mgba-bridge/battle_agent_service.py`
- Test: `tools/mgba-bridge/tests/test_mgba_bridge_source.py`,
  `tools/mgba-bridge/tests/test_battle_agent_service.py`

- [ ] **Step 1: Write failing service/source tests.** Assert that Lua uses V4
  request/response lengths and only writes a full pair. Assert that the Python
  service exposes four battlers, actor-keyed `list_legal_actions`,
  `analyze_action(actor_battler, action_index)`, and terminal
  `choose_actions(actions)`. Add a fixture where the model calls
  `get_battle_state`, `get_party`, both action analyses, then chooses Helping
  Hand plus an attack. Add invalid partial/duplicate/foreign action-pair tests.

- [ ] **Step 2: Run the focused Python suite and observe failure.**

  ```bash
  python3 -m unittest discover -s tools/mgba-bridge/tests -p 'test_*bridge*.py' -q
  python3 -m unittest discover -s tools/mgba-bridge/tests -p 'test_battle_agent_service.py' -q
  ```

  Expected: V3 frame-size assertions and `choose_action` assumptions fail.

- [ ] **Step 3: Implement the V4 bridge/service.** Replace Lua's fixed V3
  constants/parser/commit offsets with V4 values. In Python, decode both actor
  lists and all four active battlers; retain every read-only tool; change the
  terminal schema/prompt/validator to `choose_actions`. Return a response only
  after the pair validates against request actors. Emit an audit line for each
  selected action plus the pair-level tool list. Do not add items or player
  reserve tools.

- [ ] **Step 4: Re-run focused Python tests.**

  ```bash
  python3 -m unittest discover -s tools/mgba-bridge/tests -q
  ```

  Expected: all bridge/service tests pass; no test accepts a partial response.

## Task 6: Preserve trainer singles and document evidence

**Files:**
- Modify: `test/battle/ai.c`, `tools/mgba-bridge/tests/test_bridge_protocol.py`,
  `tools/mgba-bridge/tests/test_battle_agent_service.py`,
  `docs/openai-battle-agent/integration-plan.md`
- Create: `docs/openai-battle-agent/reviews/2026-08-02-phase-7a-single-trainer-doubles-evidence.md`

- [ ] **Step 1: Add V4 single-regression and absent-service tests.** Prove a
  trainer single still publishes one legal action list, a valid response still
  applies, invalid V4 responses fall back, and the thinking panel remains the
  fixed `AI is thinking..` message. Prove one-trainer doubles fall back with a
  missing service and that two-trainer doubles remain bridge-silent.

- [ ] **Step 2: Run the full automated gate.**

  ```bash
  make -j16 check TESTS='External AI'
  python3 -m unittest discover -s tools/mgba-bridge/tests -q
  git diff --check
  ```

  Expected: zero External AI failures, Python exit code 0, and no whitespace
  errors.

- [ ] **Step 3: Build a fresh ROM.** Close mGBA, then run:

  ```bash
  make -j16
  ```

  Expected: `pokeemerald.gba` is regenerated and the final command is
  `tools/mgba-bridge/generated/mailbox_address.lua`.

- [ ] **Step 4: Perform manual smoke tests.** With mGBA's Lua bridge and the
  Python service running, battle an intentional one-trainer double and confirm
  one request per turn, paired audits, an ally-target pair, and a double-switch
  when legal. Repeat without the Python service and confirm both opponents
  use vanilla moves after the thinking timeout. Trigger a two-trainer double
  and confirm no BAGB request appears.

- [ ] **Step 5: Record evidence and commit.** Write exact command outcomes,
  ROM build date, and manual observations in the evidence review; link it from
  the integration plan. Commit only the Phase 7A source, tests, docs, and
  bridge files:

  ```bash
  git add include/battle_agent.h src/battle_agent.c src/battle_ai_main.c src/battle_controller_opponent.c include/test/battle.h test/test_runner_battle.c test/battle/ai.c tools/mgba-bridge docs/openai-battle-agent
  git commit -m "feat(ai): coordinate one-trainer double battles"
  ```

## Self-review

- **Specification coverage:** Tasks 1 and 5 cover BAGB/4 and tools; Tasks 2–4
  cover atomic ROM/controller behavior, targeting, switching, eligibility, and
  fallback; Task 6 covers singles compatibility, exclusions, verification, and
  evidence.
- **Terminology/type consistency:** The plan uses `controlled_battlers`,
  actor-keyed `action_index`, `choose_actions`, and
  `BATTLE_AGENT_BATTLE_MODE_TRAINER_DOUBLE` consistently. It never proposes a
  model-supplied raw move, target, party slot, or item.
- **Scope check:** `BATTLE_TYPE_TWO_OPPONENTS`, `BATTLE_TYPE_INGAME_PARTNER`,
  player reserves, items, and forced replacements receive explicit regression
  exclusions. Phase 7B remains a separate phase.
- **Mechanics safety:** Accepted selections are written through existing AI
  data/controller paths; all failed selections are all-or-nothing and retain
  both saved vanilla decisions.
