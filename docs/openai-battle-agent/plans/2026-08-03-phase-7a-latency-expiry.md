# Phase 7A latency and expiry correction implementation plan

> **For agentic workers:** execute test-first, one task at a time.

**Goal:** Prevent late local-model responses from being mistaken for moves used
by a completed battle turn, while giving the configured local Ollama tool loop
a bounded 1,800-frame response window.

**Architecture:** Keep BAGB/4 request and response bytes unchanged. The ROM
remains the authority: it accepts complete validated responses only while the
mailbox is pending, and it makes that mailbox idle whenever vanilla fallback
starts. Lua then rejects a late response against the idle mailbox.

**Tech stack:** pokeemerald-expansion C battle engine/tests, mGBA Lua bridge,
Python standard-library service tests.

**Specification:** [Phase 7A specification](../specs/2026-08-02-phase-7a-single-trainer-doubles.md)

**Flow review:** [Latency and expiry flow review](../reviews/2026-08-03-phase-7a-latency-expiry-flow-review.md)

## Files

- Modify: `include/battle_agent.h` — raise only the finite response frame
  budget from 900 to 1,800.
- Modify: `src/battle_agent.c` — mark a timed-out request idle in
  `BattleAgent_UseVanillaFallback` after restoring saved vanilla state.
- Modify: `test/battle/ai.c` — assert that fallback invalidates the pending
  request, using the existing stale-response/rejected-switch test fixture.
- Modify: `docs/openai-battle-agent/specs/2026-08-02-phase-7a-single-trainer-doubles.md`
  and this review/plan — record exact timeout and late-response behavior.

## Task 1: Prove fallback invalidates the request

- [ ] Add `EXPECT_EQ(gBattleAgentMailbox.requestStatus,
  BATTLE_AGENT_REQUEST_IDLE);` immediately after the existing
  `BattleAgent_UseVanillaFallback(B_POSITION_OPPONENT_LEFT);` call in the
  `External AI V4 rejects a reserve that faints while it waits` test.
- [ ] Run:

  ```bash
  make -j16 check TESTS='External AI V4 rejects a reserve that faints while it waits'
  ```

  Expected before implementation: failure because the mailbox remains
  `BATTLE_AGENT_REQUEST_PENDING`.

## Task 2: Implement the bounded expiry correction

- [ ] Change `BATTLE_AGENT_RESPONSE_TIMEOUT_FRAMES` in
  `include/battle_agent.h` from `900` to `1800` for normal ROM builds, while
  retaining the existing 900-frame value under `TESTING` so intentional
  no-service test cases stay bounded and fast.
- [ ] In `BattleAgent_UseVanillaFallback` in `src/battle_agent.c`, after the
  existing `BattleAgent_ClearResponse();` call, invoke
  `BattleAgent_BeginRequest();` so `requestStatus` becomes idle only after the
  saved vanilla action/target and local wait state have been restored.
- [ ] Re-run the Task 1 command.

  Expected after implementation: PASS.

## Task 3: Verify compatibility and user-visible boundaries

- [ ] Run:

  ```bash
  make -j16 check TESTS='External AI'
  python3 -m unittest discover -s tools/mgba-bridge/tests -q
  git diff --check
  ```

  Expected: all External AI tests and Python bridge tests pass with no diff
  whitespace errors.
- [ ] Build and manually test with mGBA Lua plus the Python service. A decision
  completed before the deadline must match its service audit in battle. A
  decision returned after expiry must show `BAGB response rejected` in the Lua
  console and the battle must use its saved vanilla action instead.

## Task 4: Reduce ordinary move-decision round trips

- [ ] Write focused service tests that require `list_legal_actions` to include
  the legal move's ROM identity, PP, battle facts, and move metadata, and that
  require the ordinary model prompt to prefer battle state, legal actions, and
  a terminal choice without repetitive per-action analysis.
- [ ] Run the focused test first and confirm it fails before implementation.
- [ ] Modify `tools/mgba-bridge/battle_agent_service.py` so the legal-action
  output uses the current payload to add those published facts. Keep
  `analyze_action` and every other read-only tool available.
- [ ] Update the ordinary-decision prompt to prefer the compact path, while
  permitting `get_party` for a voluntary switch and other inspection tools when
  genuinely needed.
- [ ] Run:

  ```bash
  python3 -m unittest discover -s tools/mgba-bridge/tests -q
  ```

  Expected: every bridge/service test passes.

## Self-review

- **Specification coverage:** Task 1 tests the missing state transition; Task
  2 changes only the documented deadline and stale-response invalidation; Task
  3 verifies existing protocol, fallback, singles, and atomic-double behavior.
- **Protocol compatibility:** no mailbox size, version, or byte offset changes.
- **Battle mechanics:** only external-wait duration and stale request state
  change; normal controller action selection and vanilla fallback remain intact.
- **Scope:** no items, new model tools, heuristic scorer, or trainer eligibility
  changes are included.
