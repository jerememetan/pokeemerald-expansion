# Phase 10A Readable Battler State Implementation Plan

**Goal:** Decode published battler/party state into model-readable JSON without altering ROM mechanics or mailbox layout.

**Architecture:** Keep `src/battle_agent.c` and Lua byte protocol unchanged. Add pure Python decoding helpers in `tools/mgba-bridge/battle_agent_service.py`; the same helper serves active battler and party tools.

**Files:** Modify `tools/mgba-bridge/battle_agent_service.py` and `tools/mgba-bridge/tests/test_battle_agent_service.py`; add this specification and flow review; update `docs/openai-battle-agent/integration-plan.md`.

1. Write decoding tests for a known type, major status, stat-stage delta, and direct `status2`/`status3` flag; run the bridge suite and confirm the new assertions fail.
2. Add pure `decode_types`, `decode_major_status`, `decode_stat_changes`, and `decode_volatile_status` helpers; make decoded battler JSON use their named output and preserve only ROM-published facts.
3. Run `py -3 -m unittest discover -s tools/mgba-bridge/tests -q` and expect zero failures.
4. Run `make -j16 check TESTS='External AI'` in WSL and expect zero External AI failures; smoke-test one single and one double battle with the service disconnected to confirm vanilla fallback.

**Compatibility and exit criteria:** No mailbox version or struct size changes; unavailable, stale, malformed, and invalid responses retain the existing vanilla fallback. The phase exits only with the commands above passing and documentation linked from the roadmap.
