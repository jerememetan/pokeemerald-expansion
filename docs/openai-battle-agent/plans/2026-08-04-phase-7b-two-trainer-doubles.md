# Phase 7B Two-Trainer Doubles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or inline task execution to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Enable one external-agent decision to coordinate both opponents in a two-trainer double battle without allowing either trainer to use the other's reserve party.

**Architecture:** Upgrade the existing BAGB/4 mailbox to BAGB/5 without changing its fixed 1,480-byte EWRAM size. A party record gains owner-battler semantics in its former reserved byte; the ROM publishes one atomic two-actor request only when both trainers opt in, and ROM legal-action validation remains the authority for each trainer's switch range.

**Tech Stack:** pokeemerald-expansion C and battle test runner; mGBA Lua 5.3 scripting; Python 3 standard-library service and unittest; local Ollama runtime.

---

**Specification:** [Phase 7B specification](../specs/2026-08-03-phase-7b-two-trainer-doubles.md)
**Flow review:** [Phase 7B flow review](../reviews/2026-08-03-phase-7b-two-trainer-doubles-flow-review.md)
**Predecessor:** [Phase 7A evidence](../reviews/2026-08-02-phase-7a-single-trainer-doubles-evidence.md)

## File structure

| File | Responsibility |
|---|---|
| include/battle_agent.h | BAGB/5 constants, battle mode, party-record owner field, and static layout assertions. |
| src/battle_agent.c | Two-trainer eligibility, owner-aware snapshot export, legal-action publication, and atomic validation. |
| src/battle_main.c | Holds the left opponent until right has calculated both vanilla fallbacks and begins the one coordinated wait. |
| include/test/battle.h | Test DSL entry point for an AI two-opponent battle and party-owner assertions. |
| test/test_runner_battle.c | Builds the two-opponent test fixture, stores expected owner metadata, and injects atomic responses. |
| test/battle/ai.c | ROM behavior and fallback regressions. |
| tools/mgba-bridge/bridge_protocol.py | BAGB/5 parser, formatter, typed party owner data, and strict version rejection. |
| tools/mgba-bridge/mgba_bridge.lua | BAGB/5 request acceptance and fixed-frame forwarding. |
| tools/mgba-bridge/battle_agent_service.py | Party-tool owner labels and BAGB/5 audit output. |
| tools/mgba-bridge/tests/*.py | Binary, bridge-source, and service tool-contract regressions. |
| tools/mgba-bridge/README.md | Two-trainer launch and smoke-test documentation. |
| docs/openai-battle-agent/* | Cross-linked evidence and roadmap completion status. |

### Task 1: Lock BAGB/5 contract behavior with failing Python and source tests

**Files:**
- Modify: tools/mgba-bridge/bridge_protocol.py
- Modify: tools/mgba-bridge/tests/test_bridge_protocol.py
- Modify: tools/mgba-bridge/tests/test_mgba_bridge_source.py
- Modify: tools/mgba-bridge/tests/test_battle_agent_service.py

- [ ] **Step 1: Write the failing protocol tests.**

Add tests that build a valid two-trainer-double binary request whose party slots
0–2 use owner battler 1 and slots 3–5 use owner battler 3. Assert:

~~~python
request = parse_request_frame(two_trainer_payload)
self.assertEqual(request.protocol_version, 5)
self.assertEqual(request.battle_mode, TRAINER_TWO_OPPONENT_DOUBLE)
self.assertEqual([member.owner_battler for member in request.snapshot.party], [1, 1, 1, 3, 3, 3])
with self.assertRaises(ProtocolError):
    parse_request_frame(v4_request_frame)
~~~

Add a Lua source assertion for local VERSION = 5 and acceptance of all three
battle modes: trainer single, one-trainer double, and two-trainer double.

- [ ] **Step 2: Run the new tests to verify they fail.**

Run:

~~~powershell
py -3 -m unittest discover -s tools\mgba-bridge\tests -p test_bridge_protocol.py -v
py -3 -m unittest discover -s tools\mgba-bridge\tests -p test_mgba_bridge_source.py -v
~~~

Expected: the new BAGB/5 expectation fails because the production protocol is
still version 4 and party records have no parsed owner field.

- [ ] **Step 3: Implement only the binary contract changes.**

In bridge_protocol.py, define protocol version 5 and the third battle-mode
constant. Parse each party record’s byte at offset 98 as owner_battler and byte
99 as reserved; reject a nonzero reserved byte. Extend the immutable party
snapshot type with owner_battler. Retain payload length 1,369, request-frame
length 1,377, response length 17, and all action record layouts.

In mgba_bridge.lua, change VERSION to 5 and allow:

~~~lua
header.battle_mode == TRAINER_SINGLE
    or header.battle_mode == TRAINER_DOUBLE
    or header.battle_mode == TRAINER_TWO_OPPONENT_DOUBLE
~~~

Do not change its response write order or fixed frame sizes.

- [ ] **Step 4: Run protocol and source tests.**

Run:

~~~powershell
py -3 -m unittest discover -s tools\mgba-bridge\tests -p test_bridge_protocol.py -v
py -3 -m unittest discover -s tools\mgba-bridge\tests -p test_mgba_bridge_source.py -v
~~~

Expected: every selected test passes, including rejection of BAGB/4 frames.

- [ ] **Step 5: Commit the isolated contract slice.**

Run:

~~~powershell
git add tools/mgba-bridge/bridge_protocol.py tools/mgba-bridge/mgba_bridge.lua tools/mgba-bridge/tests/test_bridge_protocol.py tools/mgba-bridge/tests/test_mgba_bridge_source.py
git commit -m "feat(ai): version bridge protocol for two-trainer doubles"
~~~

Expected: one commit containing only the BAGB/5 protocol and its tests.

### Task 2: Add two-trainer test-fixture support and failing ROM expectations

**Files:**
- Modify: include/test/battle.h
- Modify: test/test_runner_battle.c
- Modify: test/battle/ai.c
- Modify: include/battle_agent.h

- [ ] **Step 1: Write failing two-trainer battle tests.**

Introduce an AI test fixture whose recorded battle flags include trainer,
double, and two-opponents, and whose opponent A and B are distinct
external-AI-tagged trainer records. Add DSL support:

~~~c
#define AI_TWO_OPPONENT_BATTLE_TEST(description) ...
#define EXPECT_AGENT_PARTY_OWNER(slot, battler) ...
~~~

Add these tests in test/battle/ai.c:

1. Both opted-in trainers publish one request with controlled battlers 1 and 3,
   mode TRAINER_TWO_OPPONENT_DOUBLE, party owners [1, 1, 1, 3, 3, 3], and two
   accepted move actions.
2. A move by battler 1 plus a switch by battler 3 accepts only a published
   slot from 3–5.
3. A double switch accepts one range-valid slot for each trainer.
4. A response which names a cross-owner switch action is rejected atomically
   and both precomputed vanilla choices execute after timeout.
5. Setting one trainer’s externalAi field false produces no request and normal
   vanilla actions.

- [ ] **Step 2: Run the focused test to verify it fails.**

Run in WSL:

~~~bash
make -j16 check TESTS='External AI applies one atomic action pair in a two-trainer double battle'
~~~

Expected: compilation fails because the fixture and owner assertion macros do
not exist, or the new request expectation fails because two-trainer doubles
are currently excluded.

- [ ] **Step 3: Implement the test-runner data structures.**

Add a BATTLE_TEST_AI_TWO_OPPONENTS fixture enum and configure it with:

~~~c
DATA.recordedBattle.battleFlags = BATTLE_TYPE_IS_MASTER
    | BATTLE_TYPE_TRAINER
    | BATTLE_TYPE_DOUBLE
    | BATTLE_TYPE_TWO_OPPONENTS;
DATA.recordedBattle.opponentA = TRAINER_LEAF;
DATA.recordedBattle.opponentB = TRAINER_RED;
DATA.hasAI = TRUE;
~~~

Extend ExpectedBattleAgentRequest with six expected owner bytes and an
owner-expectation mask. Implement ExpectBattleAgentPartyOwner_ and validate
the mailbox party owner byte in CheckBattleAgentRequest. Keep all existing
single and one-trainer-double response helper semantics unchanged.

- [ ] **Step 4: Re-run the focused test.**

Run the command from Step 2.

Expected: it compiles but fails its request expectation, proving the test
reaches the current two-trainer exclusion before ROM behavior is changed.

- [ ] **Step 5: Commit the fixture/test scaffolding.**

Run:

~~~bash
git add include/test/battle.h test/test_runner_battle.c test/battle/ai.c include/battle_agent.h
git commit -m "test(ai): cover two-trainer double ownership"
~~~

Expected: the commit contains only test infrastructure and failing expected
behavior; do not commit a generated ROM.

### Task 3: Implement ROM eligibility, owner-aware snapshot export, and atomic commit

**Files:**
- Modify: include/battle_agent.h
- Modify: src/battle_agent.c
- Modify: src/battle_main.c
- Modify: test/battle/ai.c

- [ ] **Step 1: Update C mailbox definitions.**

Change BATTLE_AGENT_PROTOCOL_VERSION to 5. Add
BATTLE_AGENT_BATTLE_MODE_TRAINER_TWO_OPPONENT_DOUBLE with value 3. Replace
the PartySnapshotV3 reserved u16 with:

~~~c
u8 ownerBattler;
u8 reserved;
~~~

Preserve every static size and offset assertion that must remain unchanged:
party record 100, snapshot 1,048, mailbox 1,480, and legal actions at offset
1,072. Add an assertion that ownerBattler is at party-member offset 98.

- [ ] **Step 2: Make the Task 2 request test fail only on ROM behavior.**

Run the command from Task 2 Step 2.

Expected: it compiles and reports that no BAGB request was published for the
two-trainer fixture.

- [ ] **Step 3: Add explicit two-trainer eligibility and snapshot helpers.**

In src/battle_agent.c, split the current base eligibility predicate so
one-trainer and two-trainer checks can share active/AI/trainer/lock-state
validation while preserving their distinct flag and trainer-opt-in rules.
Implement:

~~~c
static bool32 BattleAgent_IsTwoTrainerCoordinatedDoubleBattle(void);
static void BattleAgent_CopyPartySnapshot(u32 ownerBattler, s32 firstSlot, s32 lastSlot);
static void BattleAgent_CopyTwoTrainerPartySnapshot(u32 leftBattler, u32 rightBattler);
~~~

The two-trainer predicate must require BATTLE_TYPE_TWO_OPPONENTS, no
BATTLE_TYPE_INGAME_PARTNER or multi/link/facility exclusions, active living
opponents, and externalAi on both trainer A and trainer B. It must not accept
a single opted-in trainer.

Copy slots 0–2 from the left owner and 3–5 from the right owner. For every
record set ownerBattler to that controlled battler, set isActive if its global
party slot equals that owner’s active party index, and write reserved as zero.
For all singles and one-trainer doubles write ownerBattler as
BATTLE_AGENT_ACTION_NONE and retain their existing shared six-slot snapshot.

- [ ] **Step 4: Publish the correct mode and preserve the right-side start point.**

Extend BattleAgent_TryPublishRequest so a two-trainer coordinated battle sets
mode TRAINER_TWO_OPPONENT_DOUBLE, controlled battlers [opponent-left,
opponent-right], and builds each actor’s legal list with the existing
GetAIPartyIndexes range. Keep opponent-left in the external wait after its
vanilla score is calculated; allow opponent-right to invoke
BattleAgent_BeginExternalWait after both choices exist. This produces exactly
one request and saves both original choices as the fallback before either
controller can dispatch an action.

- [ ] **Step 5: Enforce per-trainer switch ownership at final validation.**

Keep BattleAgent_IsLegalSwitch as the commit authority. Its existing
GetAIPartyIndexes(requester) range check must run for each selected action
before any action is written. For a two-trainer mode, reject any selected party
slot outside the requester’s range even if the slot contains a usable Pokémon.
Validate the entire pair first, then write both aiMoveOrAction, targets, and
AI_monToSwitchIntoId values only after all validation succeeds.

- [ ] **Step 6: Run focused ROM tests.**

Run in WSL:

~~~bash
make -j16 check TESTS='External AI'
~~~

Expected: all focused External AI tests pass, including singles, Phase 7A
one-trainer doubles, the new two-trainer move/switch tests, mixed opt-in
silence, and atomic cross-owner fallback.

- [ ] **Step 7: Commit ROM implementation.**

Run:

~~~bash
git add include/battle_agent.h src/battle_agent.c src/battle_main.c test/battle/ai.c
git commit -m "feat(ai): coordinate two-trainer double battles"
~~~

Expected: only ROM implementation and directly coupled tests are committed.

### Task 4: Expose owner-labelled parties to the agent and prove tool behavior

**Files:**
- Modify: tools/mgba-bridge/battle_agent_service.py
- Modify: tools/mgba-bridge/tests/test_battle_agent_service.py

- [ ] **Step 1: Write failing service tests.**

Build a parsed BAGB/5 request with two owners and assert:

~~~python
party = service.get_party(request)
self.assertEqual(party[0]["owner_battler"], 1)
self.assertEqual(party[0]["owner"], "opponent-left")
self.assertEqual(party[3]["owner_battler"], 3)
self.assertEqual(party[3]["owner"], "opponent-right")
self.assertNotIn("switchable", party[0])
~~~

Add a one-trainer BAGB/5 fixture assertion that every party record reports
owner_battler 255 and owner shared.

- [ ] **Step 2: Run the service test to verify it fails.**

Run:

~~~powershell
py -3 -m unittest discover -s tools\mgba-bridge\tests -p test_battle_agent_service.py -v
~~~

Expected: owner_battler and owner are absent from get_party output.

- [ ] **Step 3: Implement owner-labelled tool output.**

Format each party record from its parsed ownerBattler field. Map 255 to
shared; map the request’s first controlled battler to opponent-left and its
second to opponent-right. Preserve all current party facts and the explicit
rule that only list_legal_actions expresses selectable switches. Add the owner
labels to the audit’s party summary, while retaining the current one-call
terminal choose_actions contract.

- [ ] **Step 4: Run the complete bridge/service suite.**

Run:

~~~powershell
py -3 -m unittest discover -s tools/mgba-bridge/tests -q
~~~

Expected: all tests pass, including the new BAGB/5 owner and BAGB/4 rejection
cases.

- [ ] **Step 5: Commit service visibility.**

Run:

~~~powershell
git add tools/mgba-bridge/battle_agent_service.py tools/mgba-bridge/tests/test_battle_agent_service.py
git commit -m "feat(ai): expose two-trainer party ownership"
~~~

Expected: one service/tool-contract commit with no model weights or generated
files.

### Task 5: Document, verify, and smoke-test the normal ROM

**Files:**
- Modify: tools/mgba-bridge/README.md
- Modify: docs/openai-battle-agent/integration-plan.md
- Create: docs/openai-battle-agent/reviews/2026-08-04-phase-7b-two-trainer-doubles-evidence.md

- [ ] **Step 1: Update launch and smoke-test documentation.**

Document that the same service command handles singles, one-trainer doubles,
and two-trainer doubles:

~~~powershell
py -3 toolsmgba-bridgeattle_agent_service.py
~~~

Add the exact two-trainer smoke assertions: exactly one request per voluntary
turn; one audit with two selected actions; party output labelled
opponent-left/opponent-right; switches never cross owners; service absence
continues the battle with vanilla choices. State that BAGB/4 bridge/service
combinations are intentionally rejected.

- [ ] **Step 2: Build and run all automated verification.**

Run in WSL:

~~~bash
make -j16 check TESTS='External AI'
make -j16
~~~

Run in PowerShell:

~~~powershell
py -3 -m unittest discover -s tools/mgba-bridge/tests -q
git diff --check
~~~

Expected: External AI tests pass, the normal pokeemerald.gba is produced, all
Python tests pass, and Git reports no whitespace errors.

- [ ] **Step 3: Perform connected and disconnected manual smoke tests.**

1. Close mGBA before building so Windows does not lock pokeemerald.gba.
2. Start mGBA with the generated BAGB/5 Lua bridge loaded.
3. Start the service command in a separate PowerShell window.
4. Trigger two map trainers who spot the player together. Confirm the service
   prints one request and one two-action audit for each fully voluntary turn.
5. Compare each audit action to the animations/messages in the game. Confirm
   any switch belongs to the labelled trainer range.
6. Stop the service while at a voluntary two-trainer turn. Confirm AI is
   thinking.. clears at expiry and both opponents make vanilla choices without
   freezing the battle.
7. Restart the service and smoke test one ordinary trainer single and one
   Phase 7A intentional one-trainer double.

- [ ] **Step 4: Record evidence and mark the roadmap status.**

Create the evidence file linking the specification, flow review, this plan,
automated command results, normal-ROM build result, and all manual observations.
Update the Phase 7B roadmap row with an evidence link only after every exit
criterion is satisfied.

- [ ] **Step 5: Commit documentation and evidence.**

Run:

~~~powershell
git add tools/mgba-bridge/README.md docs/openai-battle-agent
git commit -m "docs(ai): record two-trainer double verification"
~~~

Expected: documentation/evidence is separate from production code commits.

## Compatibility and fallback checklist

- BAGB/4 requests or responses are rejected due to version 5; no state is
  committed from an incompatible bridge or service.
- Mailbox sizes, payload sizes, response sizes, and ROM offsets stay unchanged.
- Only a both-opted-in BATTLE_TYPE_TWO_OPPONENTS battle uses BAGB/5 mode 3.
- Mixed opt-in, player-partner, multi, link, facility, forced replacement,
  locked, absent, and fainted paths remain vanilla.
- One-trainer doubles preserve shared-party metadata and all existing action
  validation; singles preserve their one-action response rule.
- No external item action, player reserve data, raw move/target/party control,
  or mechanics change is introduced.

## Plan self-review

| Specification requirement | Implementing task |
|---|---|
| One model decision and atomic pair | Tasks 2 and 3 |
| Separate trainer ownership | Tasks 2, 3, and 4 |
| BAGB/5 compatibility rejection | Task 1 |
| Read-only owner-labelled tooling | Task 4 |
| Full-pair fallback and no partial commits | Tasks 2, 3, and 5 |
| Single and Phase 7A regression protection | Tasks 3 and 5 |
| Normal-ROM manual evidence | Task 5 |

The plan has no unresolved decisions, unfinished steps, or mailbox layout
changes that would exceed current EWRAM. All names used by later tasks are
introduced in Tasks 1–3.

## Phase exit criteria

Phase 7B is complete only when Task 5 evidence records passing automated
verification, successful connected and disconnected two-trainer smoke tests,
matching service/game actions, and successful single plus one-trainer-double
regression smoke tests.
