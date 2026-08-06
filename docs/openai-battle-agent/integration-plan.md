# External AI Trainer Integration Plan

**Parent design:** [`2026-07-18-mgba-ai-trainer-design.md`](2026-07-18-mgba-ai-trainer-design.md)  
**Phase 0 specification:** [`specs/2026-07-18-phase-0-discovery-and-contract-baseline.md`](specs/2026-07-18-phase-0-discovery-and-contract-baseline.md)  
**Phase 0 flow review:** [`reviews/2026-07-18-phase-0-discovery-and-contract-baseline-flow-review.md`](reviews/2026-07-18-phase-0-discovery-and-contract-baseline-flow-review.md)  
**Phase 0 task plan:** [`plans/2026-07-18-phase-0-discovery-and-contract-baseline.md`](plans/2026-07-18-phase-0-discovery-and-contract-baseline.md)
**Phase 0 build baseline:** [`reviews/2026-07-18-phase-0-build-baseline.md`](reviews/2026-07-18-phase-0-build-baseline.md)

## Phase order

| Phase | Deliverable | Runtime scope | Required evidence |
|---|---|---|---|
| 0 | Call graph, state inventory, protocol, and roadmap | Documentation only | Cross-linked documents, `git diff --check`, build/test baseline. |
| 1 | `Trainer.externalAi` and deterministic ROM-only mock selection | One trainer; singles; moves | Ordinary AI unchanged; opt-in trainer selects a legal mock move; switch/item path unchanged. |
| 2 | Named EWRAM mailbox and ROM legal-action snapshot | Same as Phase 1 | Legal slots/targets exported; stale/invalid responses rejected; fallback tests pass. |
| 3 | Pinned mGBA Lua bridge | Local mGBA demo | Map-address resolution; loopback connection; bridge absence/disconnect does not stop battle. |
| 4 | Deterministic local Python service | One demo trainer | Service completes a battle through the mailbox; malformed replies fall back. |
| 5 | Model-backed decision adapter | One demo trainer | Structured response validation, latency metrics, connected/disconnected demo. |
| 6A | Voluntary switching | Trainer singles | ROM validates party actions; no items; fallback covers moves and switches. |
| 6B | Global trainer-single enablement | All eligible trainer singles | Every trainer is tagged; unsupported modes remain vanilla. |
| 7A | One-trainer double battles | Intentional trainer doubles | One atomic two-action agent plan covers ally, enemy, self, spread, move/switch, and double-switch choices. [Evidence](reviews/2026-08-02-phase-7a-single-trainer-doubles-evidence.md) recorded 2026-08-03. |
| 7B | Two-trainer double battles | Two trainers that spot the player together | One atomic agent decision controls both opponents, while each action and reserve party remains owned by its originating trainer. [Evidence](reviews/2026-08-04-phase-7b-two-trainer-doubles-evidence.md) recorded 2026-08-04. |
| 8A | Double-battle thinking-status correction | Intentional and two-trainer doubles | The presentation-only pending-response status waits for every active player action before claiming the normal message window. [Specification](specs/2026-08-04-phase-8a-double-thinking-status.md), [flow review](reviews/2026-08-04-phase-8a-double-thinking-status-flow-review.md), [implementation plan](plans/2026-08-04-phase-8a-double-thinking-status.md), and [evidence](reviews/2026-08-04-phase-8a-double-thinking-status-evidence.md). |
| 8 | Packaging and demo handoff | New developer path | Pinned mGBA build, launch guide, smoke test, reproducible fallback demonstration. [Specification](specs/2026-08-04-phase-8-packaging-and-handoff.md), [flow review](reviews/2026-08-04-phase-8-packaging-and-handoff-flow-review.md), [implementation plan](plans/2026-08-04-phase-8-packaging-and-handoff.md), and [evidence](reviews/2026-08-04-phase-8-packaging-and-handoff-evidence.md). |
| 9 | Local Ollama model selection | Python service launch | Player selects one already-installed local model; explicit CLI override and all ROM fallback behavior remain available. [Specification](specs/2026-08-04-phase-9-local-model-selection.md), [flow review](reviews/2026-08-04-phase-9-local-model-selection-flow-review.md), and [implementation plan](plans/2026-08-04-phase-9-local-model-selection.md). |
| 10A | Readable battler state | Python model tools | Active and reserve Pokémon facts use named types, statuses, volatile effects, and stat-stage deltas without changing the V4 mailbox. [Specification](specs/2026-08-05-phase-10a-readable-battler-state.md), [flow review](reviews/2026-08-05-phase-10a-readable-battler-state-flow-review.md), and [implementation plan](plans/2026-08-05-phase-10a-readable-battler-state.md). |
| 10B | Readable field and move state | Python model tools | Published field/side effects and move type/target/split use named JSON values; no battle or protocol mechanics change. [Specification](specs/2026-08-05-phase-10b-readable-field-and-move-state.md), [flow review](reviews/2026-08-05-phase-10b-readable-field-and-move-state-flow-review.md), and [implementation plan](plans/2026-08-05-phase-10b-readable-field-and-move-state.md). |
| 11 | Authoritative speed context | ROM snapshot and Python model tool | Active speed uses the battle engine's total-speed helper, while `compare_speed` applies the existing Trick Room field rule. [Specification](specs/2026-08-05-phase-11-authoritative-speed.md), [flow review](reviews/2026-08-05-phase-11-authoritative-speed-flow-review.md), and [implementation plan](plans/2026-08-05-phase-11-authoritative-speed.md). |
| 12 | Tool-exchange time budget | Python model service | Each Ollama response remains bounded to 20 seconds, while a valid multi-tool decision may use up to 45 seconds before the existing vanilla fallback. [Specification](specs/2026-08-05-phase-12-tool-exchange-budget.md), [flow review](reviews/2026-08-05-phase-12-tool-exchange-budget-flow-review.md), and [implementation plan](plans/2026-08-05-phase-12-tool-exchange-budget.md). |
| 13 | Model-response diagnostics | Python model service | Every malformed, unsupported, invalid, or expired model decision has a bounded, specific console diagnostic before the existing vanilla fallback. [Specification](specs/2026-08-06-phase-13-model-response-diagnostics.md), [flow review](reviews/2026-08-06-phase-13-model-response-diagnostics-flow-review.md), and [implementation plan](plans/2026-08-06-phase-13-model-response-diagnostics.md). |
| 14 | Legal-action query normalization | Python model service | Harmless model arguments to the read-only complete legal-action query are normalized, while terminal action validation and fallback remain strict. [Specification](specs/2026-08-06-phase-14-legal-action-query-normalization.md), [flow review](reviews/2026-08-06-phase-14-legal-action-query-normalization-flow-review.md), and [implementation plan](plans/2026-08-06-phase-14-legal-action-query-normalization.md). |

## Evidence matrix

| Behavior | First responsible phase | Required proof |
|---|---:|---|
| Ordinary trainer behavior unchanged | 1 | Existing AI tests and a non-opt-in trainer battle. |
| Valid opt-in response | 1 | ROM-only mock chooses a listed move and target. |
| Absent bridge | 2 | Mailbox request expires into ordinary AI fallback. |
| Late response | 2 | Response with an expired sequence is ignored. |
| Stale response | 2 | Mismatched sequence is ignored. |
| Invalid action index | 2 | Out-of-range index falls back. |
| Invalid target | 2 | Selected entry fails current legality recheck and falls back. |
| Service disconnect | 3 | Lua connection loss causes fallback without an emulator freeze. |
| Map/version mismatch | 3 | Lua magic/version check disables the bridge. |
| Switching/item preservation | 1 | Existing `AI_TrySwitchOrUseItem` action remains available for an opt-in trainer. |
| One-trainer double-battle target coverage | 7A | Battle tests include ally, enemy, self, spread, absent, and fainted targets. |
| Two-trainer-double party ownership | 7B | No action can select the other trainer's reserve party. |

## Documentation rule for every phase

Before production-code work begins, create a phase-specific specification in `specs/`, analyze it with `spec-flow-analyzer` into `reviews/`, resolve all critical and important gaps, and create a task-level plan with `writing-plans` in `plans/`. The phase cannot advance without fresh build/test evidence and its documented exit criteria.

## Rollback and fallback invariant

Every runtime phase preserves the existing trainer AI path. The external layer is opt-in, cannot alter battle rules, and can replace the existing decision only with a ROM-produced legal action. If any external dependency is missing, slow, stale, malformed, incompatible, or invalid, the ordinary trainer AI remains the action source.
