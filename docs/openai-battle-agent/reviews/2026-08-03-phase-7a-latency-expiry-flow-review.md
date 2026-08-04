# Phase 7A latency and expiry flow review

**Specification:** [Phase 7A specification](../specs/2026-08-02-phase-7a-single-trainer-doubles.md)

## Repository grounding

`src/battle_agent.c` counts `BATTLE_AGENT_RESPONSE_TIMEOUT_FRAMES` in emulated
frames and `BattleAgent_UseVanillaFallback` previously cleared only response
fields. `tools/mgba-bridge/mgba_bridge.lua` treats a pending request as
forwardable and logs a response write without receiving a ROM acknowledgement.
`tools/mgba-bridge/battle_agent_service.py` needs several local Ollama calls
for a tool exchange. The user's mGBA screenshots show roughly 300 FPS, making
the former 900-frame deadline about three wall-clock seconds.

## User flows

1. **Warm local-model decision.** The ROM publishes one single or atomic
   double request, the service completes its bounded tool calls before 1,800
   frames, Lua writes the validated response, and the ROM consumes the named
   action(s) through normal opponent controllers.
2. **Model is slow or unavailable.** The deadline expires, both saved vanilla
   actions resume, the thinking status clears, and the request becomes idle.
   A service reply arriving afterward is rejected by Lua and cannot be mistaken
   for a decision used by the battle.
3. **Invalid response before expiry.** Existing action/actor/target validation
   rejects it; the request remains pending until a valid response or expiry.
4. **Ordinary move selection.** The model reads battle state and an enriched
   legal-action list, then selects its actor-keyed action(s) without spending a
   separate round trip per move. It can still inspect party data before a
   voluntary switch.

## Gaps

### Critical

None after specifying mailbox invalidation on expiry. Previously a late Lua
write could be indistinguishable in operator logs from a consumed response.

### Important

1. The deadline is emulator-frame based rather than wall-clock based. The
   explicit 1,800-frame value is a safe bounded local-model allowance on the
   documented unthrottled setup; a missing service still reaches vanilla AI.
2. The service audit is a record of its selected legal action, not a ROM
   acceptance acknowledgement. The idle mailbox rule makes late writes visible
   as Lua rejection rather than a misleading apparent success.
3. Per-action analysis can exceed the unthrottled deadline. Publishing the same
   deterministic move facts with each legal action is the token-efficient
   default; `analyze_action` remains available for exceptional inspection.

### Minor

The first cold model request can still take longer than a warm request. The
service remains manually started before battle; preloading the model is outside
this correction.

## Decisions

1. Use an 1,800-frame deadline, not an unbounded wait. This preserves the
   existing fallback guarantee and accommodates measured 3–5 second exchanges
   at the user's current emulator speed.
2. On fallback, set request status to idle and clear the response. This makes a
   late response harmless without altering BAGB/4 frame layout.
3. Keep service-side invalid/malformed output as vanilla fallback. No heuristic
   decision path is added.
4. Prefer battle state plus an enriched legal-action listing before terminal
   selection. Do not remove the read-only tool surface or limit party reads for
   voluntary switch decisions.

## Recommended implementation checks

Add a failing ROM test proving fallback makes the mailbox request idle, then
set that status in `BattleAgent_UseVanillaFallback`. Run the focused External
AI test and the full External AI and Python bridge suites. In mGBA, a late
reply must log `BAGB response rejected`; a timely response must result in the
audited move(s) in battle.
