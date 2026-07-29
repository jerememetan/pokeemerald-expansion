# Phase 4A Specification: Local Ollama Tool Agent and ROM Response Acceptance

**Status:** Design and flow reviewed; awaiting user review before implementation planning  
**Parent roadmap:** [`../2026-07-18-mgba-ai-trainer-design.md`](../2026-07-18-mgba-ai-trainer-design.md)  
**Prerequisite:** [Phase 3A bridge evidence](../reviews/2026-07-29-phase-3a-mgba-loopback-bridge-evidence.md)

## Goal

Make `TRAINER_CALVIN_1` use a local Ollama agent in a standard trainer single battle. The agent may inspect an explicitly bounded set of read-only battle-analysis tools and may submit one ROM-provided legal action index. The ROM remains authoritative: it revalidates the response and uses its already-computed vanilla trainer-AI move on every unavailable, late, stale, malformed, or illegal response.

This phase uses the locally installed `qwen2.5-coder:7b` model through the Ollama loopback API. It is the first phase in which an external response may change Calvin's selected move.

## Scope

### In scope

- `TRAINER_CALVIN_1` only; opponent-side, standard trainer single battles; move actions only.
- A V2 fixed-layout mailbox snapshot covering both active battlers' trainer-AI-authorized battle information: species, level, HP/max HP, type slots, ability, held item, current battle stats, stat stages, primary/secondary/tertiary status masks, and all four move IDs, PP values, and static move-analysis fields (type, power, accuracy, effect, target category, priority, and split).
- Existing field information: weather, terrain, field status, and both side-status masks.
- A legal-action list containing the only move-slot and target combinations the ROM may apply.
- Per-legal-action ROM facts derived with existing battle-engine logic: target, move metadata needed by the service, type-effectiveness category, move priority, and whether the existing AI's KO predicate says the move can faint its target.
- A bounded binary `BAGB/2` loopback frame between Lua and the Python service.
- A local Python service, using only the standard library, that calls Ollama at `http://127.0.0.1:11434/api/chat` with model `qwen2.5-coder:7b`.
- The following read-only tools, advertised to the agent without a required call order:

  | Tool | Result |
  |---|---|
  | `get_battle_state()` | Request sequence, turn, requester, both active battlers' current snapshot, and active-battle metadata. |
  | `get_field_state()` | Weather, terrain, field statuses, and both side-status masks. |
  | `get_battler(battler_id)` | One active battler's AI-authorized traits, HP, statuses, battle stats, and stat stages. |
  | `get_battler_moves(battler_id)` | All four active moves, PP, and locally resolved move names/metadata for either active battler. |
  | `list_legal_actions()` | Every currently legal action index, with its move slot and target. |
  | `analyze_action(action_index)` | A legal action's resolved move data, target, STAB, type-effectiveness category, priority, and ROM KO predicate. |
  | `compare_speed()` | The active battlers' current speed values and the normal-order comparison; it must state that priority can override speed. |
  | `choose_action(action_index)` | Terminal command selecting exactly one action from `list_legal_actions()`. |

- A generated, checked-in local catalog mapping exported species, abilities, items, moves, and move effects to human-readable names. Its generator reads only this repository's constants/data; the service uses it only to label data already authorized by the V2 snapshot and never queries mGBA or the ROM directly.
- A per-Calvin 900-frame (15-second) response window. The ROM computes and saves vanilla AI's decision before opening this window, then enters a new frame-yielding action-selection wait state that does not emit Calvin's opponent-controller command until it resolves. Other battlers continue through the existing action-selection loop. The 900th visit to this wait state takes the saved vanilla fallback before attempting to consume a response.
- ROM-side response acceptance only after a matching V2 request sequence, `READY` status, legal action index, still-eligible battle, and a fresh `BattleAgent_NormalizeSingleTarget` result matching the stored legal-action target are all confirmed.

### Out of scope

- Bench-party information for either side, switching, battle items, doubles, multi battles, wild battles, link battles, facility variants, or trainer rollout beyond Calvin.
- Arbitrary mGBA memory reads, raw ROM pointers, arbitrary service-provided moves/targets, direct shell/file/network tools for the model, cloud model APIs, API keys, or a UI inside the ROM.
- Damage simulation invented by Python. Phase 4A exposes the existing engine's per-action KO predicate and deterministic metadata, not an independently reimplemented damage formula.
- Unbounded model/tool loops, a wait longer than 900 frames, replacing vanilla AI globally, or changing move effects, damage calculation, targeting rules, or turn resolution.

### qwen2.5-coder compatibility decision

Ollama-native `message.tool_calls` remains the preferred service input. During
local verification on this project, the approved `qwen2.5-coder:7b` model
instead emitted an assistant `content` value that was exactly one JSON object
with `name` and `arguments` keys. The service may accept that alternate shape
only when all of the following are true: `content` is a JSON object with
exactly those two keys, `name` is one advertised tool name, and `arguments` is
an object that passes the same per-tool validation as a native tool call.
Plain text, Markdown, JSON arrays, extra keys, duplicate terminal choices,
unknown names, malformed JSON, and invalid arguments produce no response.
This is a local-model message compatibility adapter; it does not change the
ROM/Lua wire protocol, the tool allowlist, or action authority.

## Boundaries

| Component | Responsibility | Must not do |
|---|---|---|
| ROM | Build V2 snapshot and legal actions, calculate/save vanilla fallback, run bounded wait, revalidate/apply an action index. | Perform networking, call Ollama, trust a move ID/target from the service, or wait beyond 900 frames. |
| Lua bridge | Read only documented V2 mailbox fields, frame and forward `BAGB/2`, validate bounded responses, commit only three response fields. | Decide moves, access undocumented memory, connect outbound, bind non-loopback, or extend the deadline. |
| Python tool service | Decode V2 frame, expose only listed read-only tools plus `choose_action`, call local Ollama, validate its terminal index, return one bounded response. | Read mGBA/ROM memory, expose shell/filesystem/network tools to the model, bind a public interface, or invent a move/target. |
| Ollama model | Reason over tool results and call `choose_action` once. | Receive secrets, direct socket access, unrestricted tool arguments, or authority to bypass legal-action validation. |

## V2 mailbox and bridge contract

`BATTLE_AGENT_PROTOCOL_VERSION` changes from `1` to `2`. V1 requests and responses are not accepted by the Phase 4A ROM, Lua bridge, or service. The ROM remains the source of truth for fixed-layout size and field offsets through compile-time assertions.

The V2 snapshot adds, for each active battler, fixed-width level, three type slots, ability, held item, current Attack/Defense/Speed/Sp. Attack/Sp. Defense, `status2`, `status3`, and four move/PP entries. It retains the V1 visible HP, status1, stat stages, field state, and legal actions. It adds a fixed-width action-analysis entry for every legal action with the action index, normalized target, priority, type-effectiveness category, and ROM KO predicate. All fields are initialized; no pointers, strings, variable-length data, or compiler-dependent booleans are exported.

The Lua/Python transport is canonical little-endian binary. It is encoded and decoded field-by-field in the following explicit V2 wire order; it never copies a padded C structure:

```text
Frame header (8 bytes)
  magic:        ASCII "BAGB"                 // 4 bytes
  version:      2                            // u8
  kind:         REQUEST=1, RESPONSE=2        // u8
  payloadLength: 0..1024                     // u16 little-endian

REQUEST payload
  requestSequence: u32
  V2 snapshot and legal-action payload in the documented V2 wire-field order

RESPONSE payload
  requestSequence: u32
  legalActionIndex: u8
```

The fixed request payload is 417 bytes and uses this byte order:

```text
requestSequence: u32
requestingBattler: u8
battleMode: u8                         // TRAINER_SINGLE only
turnSequence: u16
battlerCount: u8                       // must be 2 for this phase
battlers[4]: BattleAgentBattlerWireV2  // 92 bytes each; unused slots are zero
weather: u16
terrain: u8
fieldStatuses: u32
sideStatuses[2]: u32                   // player side then opponent side
legalActionCount: u8                   // 1..4
legalActions[4]: BattleAgentLegalActionWireV2 // 6 bytes each; unused entries are zero

BattleAgentBattlerWireV2 (92 bytes)
  species: u16; level: u8; type1/type2/type3: u8 each
  ability: u16; item: u16; hp/maxHp: u16 each
  attack/defense/speed/spAttack/spDefense: u16 each
  status1/status2/status3: u32 each; statStages[8]: u8 each
  moves[4], each 12 bytes:
    move: u16; pp: u8; type: u8; power: u8; accuracy: u8; effect: u16
    targetCategory: u8; priority: s8; split: u8; reserved: u8

BattleAgentLegalActionWireV2 (6 bytes)
  actionIndex: u8; moveSlot: u8; targetBattler: u8
  typeEffectiveness: u8; hasStab: u8; canFaintTarget: u8
```

`typeEffectiveness` is an enum supplied by ROM battle logic (`IMMUNE`, `NOT_VERY_EFFECTIVE`, `NEUTRAL`, `SUPER_EFFECTIVE`); `hasStab` and `canFaintTarget` are strictly `0` or `1`. `status1`, `status2`, `status3`, `fieldStatuses`, and `sideStatuses` retain their repository bit-mask values, with catalog labels supplied outside the wire frame. The fixed response payload is five bytes. The enclosing frame is therefore 425 bytes for a request and 13 bytes for a response.

The V2 wire payload has one fixed byte size defined by the ROM header and duplicated as a Python/Lua constant under tests. Its size must be at most 1024. The bridge rejects a bad magic/version/kind, any payload length other than that fixed request or response size, a partial/extra frame, a sequence mismatch, or an action index outside the current `legalActionCount`. It processes no more than one complete receive and one response commit per frame. Before committing, it rereads the current V2 header and legal-action count; it writes `responseSequence`, `responseLegalActionIndex`, then `responseStatus = READY` last.

## Agent and service flow

1. The ROM computes its ordinary trainer-AI choice and target exactly as today and saves them as the fallback.
2. For eligible Calvin move turns, it publishes a V2 request with `PENDING`, saves the vanilla move and target, and enters `STATE_WAIT_EXTERNAL_AI_RESPONSE`. That state yields through the existing battle task rather than busy-waiting; it is the only state that may wait for this request and it cannot emit Calvin's opponent-controller command before accepting or rejecting the response.
3. Lua forwards one V2 frame to the single loopback service client.
4. The service rejects an unavailable Ollama endpoint, unavailable `qwen2.5-coder:7b`, malformed frame, or malformed catalog before calling the model. It returns no response in those cases.
5. The service supplies the agent with the tool schemas and a system instruction that only `choose_action` can finish a decision. The agent may call at most 12 tools within a 12-second monotonic service deadline. Tool arguments must be type-checked, battler IDs must refer to the two active battlers, and action indices must refer to the current legal list.
6. The service executes each tool from the decoded request and appends a bounded tool result. It gives Ollama no direct process, file, network, or emulator tool.
7. `choose_action(index)` succeeds only once. The service validates the index against the decoded legal actions and sends the V2 response. Any text-only completion, repeated terminal tool call, invalid argument, HTTP error, or service deadline exhaustion sends no response.
8. On one of the first 899 wait-state visits, a matching `READY` response is consumed only after the ROM revalidates the current request and legal action, re-runs `BattleAgent_NormalizeSingleTarget` for the selected move slot, and confirms the result equals the stored action target. It replaces only `aiMoveOrAction` and `aiChosenTarget` from that action, then proceeds through the unchanged opponent controller.
9. On the 900th wait-state visit or every other path, the ROM uses the saved vanilla action and target. It clears/supersedes response data when the next request is published.

## Failure and fallback behavior

| Condition | Required behavior |
|---|---|
| Ollama/service absent, model unavailable, HTTP failure, unsupported tool-call response shape, or 12-second service timeout | No response; ROM uses saved vanilla move on the 900th wait-state visit. |
| Lua absent/disconnected/malformed frame | No response commit; ROM uses saved vanilla move. |
| Stale sequence, wrong V1/V2 version, duplicate response, invalid index, target failing fresh normalization, or request no longer pending | Reject response; use saved vanilla move. |
| Agent calls unknown tool, malformed arguments, more than 12 tools, or emits text without `choose_action` | Service sends no response. |
| No legal action or non-move vanilla fallback | Do not open external wait; use vanilla decision immediately. |
| Calvin is not eligible or battle becomes unsupported | Clear external wait state and use vanilla decision immediately. |

## Tests and measurable exit criteria

1. C compile-time assertions prove V2 layout and every Lua-read field offset; focused battle tests prove the V2 snapshot includes authorized active-battler state and excludes both benches.
2. C battle tests prove a matching, ready, legal response changes Calvin's move/target; stale, wrong-version, illegal, normalization-mismatched, expired, no-legal-action, and unsupported-battle responses preserve the saved vanilla choice.
3. The 900-frame wait is tested without a service response and must advance frames rather than freeze the battle task; a response present only on the 900th visit must lose to the saved fallback.
4. Python tests cover binary V2 frame parsing/fixed-length limits, catalog generation/resolution, every tool result, tool-argument validation, tool-call cap, terminal selection validation, 12-second service cutoff, and Ollama HTTP failure/model-unavailable fallback using a local fake HTTP server.
5. Lua source tests prove loopback-only binding, V2 frame bounds, documented V2 reads only, exactly the three response writes in order, and no outbound `socket.connect`.
6. Manual Windows test: with Ollama serving `qwen2.5-coder:7b`, Calvin's agent calls at least one read-only tool, chooses a legal action, and the ROM applies it before the deadline.
7. Manual Windows test: stop Ollama or the Python service during Calvin's wait; the battle remains responsive and Calvin uses the saved vanilla move at or before 15 seconds.
8. `make -j16 check TESTS='External AI'`, all Python service/bridge tests, and `make -j16` pass. No unconfigured trainer or unsupported battle changes behavior.

## Links

- [Phase 3A bridge evidence](../reviews/2026-07-29-phase-3a-mgba-loopback-bridge-evidence.md)
- [Phase 3A specification](2026-07-28-phase-3a-mgba-loopback-bridge.md)
- [Phase 4A flow review](../reviews/2026-07-29-phase-4a-local-ollama-tool-agent-flow-review.md)
- [Phase 4A implementation plan](../plans/2026-07-29-phase-4a-local-ollama-tool-agent.md)
