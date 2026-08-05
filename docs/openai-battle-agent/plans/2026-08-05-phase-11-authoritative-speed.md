# Phase 11 Authoritative Speed Implementation Plan

**Goal:** Expose the ROM's effective active speed to `compare_speed` and apply Trick Room's ordering reversal.

**Architecture:** Reuse the existing V4 active snapshot `speed` word. `src/battle_agent.c` writes `GetBattlerTotalSpeedStat(battler)`; Python retains its parser offsets and reads the existing field-status word to reverse its advisory ordering under Trick Room.

**Files:** Modify `src/battle_agent.c`, `tools/mgba-bridge/battle_agent_service.py`, `tools/mgba-bridge/tests/test_battle_agent_source.py`, and `tools/mgba-bridge/tests/test_battle_agent_service.py`; add these phase documents; update `docs/openai-battle-agent/integration-plan.md`.

1. Add a failing source regression test requiring `snapshotBattler->speed = GetBattlerTotalSpeedStat(battler);`; run the focused source suite and confirm it fails against the raw `gBattleMons` assignment.
2. Include `battle_main.h` and replace only the active snapshot assignment. Do not alter V4 struct layout, version, Lua configuration, or party reserve Speed.
3. Add a failing Python test with faster battler 1 and Trick Room active; assert the returned order starts with slower battler 0 and `trick_room_active` is true.
4. Update `compare_speed` to read field status at the existing V4 offset, order ROM-published effective speeds ascending only under Trick Room, and document priority/equal-speed limits.
5. Run `py -3 -m unittest discover -s tools/mgba-bridge/tests -q`, `make -j16 check TESTS='External AI'`, and `make -j16`; expect all commands to pass. Smoke-test Tailwind/paralysis/stat-stage/Trick Room output and disconnected fallback in normal singles and doubles.

**Compatibility and exit criteria:** Existing mailbox byte layout and vanilla fallback remain untouched. Exit only after fresh build/test evidence and the manual cases above show named, advisory speed context without gameplay regressions.
