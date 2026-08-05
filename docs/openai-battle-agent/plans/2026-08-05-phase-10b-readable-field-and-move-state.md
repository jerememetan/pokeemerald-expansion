# Phase 10B Readable Field and Move State Implementation Plan

**Goal:** Translate existing field and move snapshot categories into readable JSON for the local model.

**Architecture:** Keep the V4 mailbox and emulator bridge unchanged. Centralize pure enum/bit decoding in `tools/mgba-bridge/battle_agent_service.py` and protect it with service-level unit tests.

**Files:** Modify `tools/mgba-bridge/battle_agent_service.py` and `tools/mgba-bridge/tests/test_battle_agent_service.py`; add these phase documents; update `docs/openai-battle-agent/integration-plan.md`.

1. Add failing tests for representative field flags and every known move split/target category; run `py -3 -m unittest discover -s tools/mgba-bridge/tests -p test_battle_agent_service.py -q` and confirm failure.
2. Add pure field, target, and split decoders. Return named `weather`, `terrain`, `field_effects`, side effects, move `type`, `target_category`, and `split` values.
3. Re-run the bridge suite and expect zero failures.
4. Run `make -j16 check TESTS='External AI'` in WSL and manually inspect a field/move tool audit; confirm disconnected bridge still falls back to vanilla AI.

**Exit criteria:** No protocol layout changes, all named tool output is covered by unit tests, and bridge plus External AI test commands pass.
