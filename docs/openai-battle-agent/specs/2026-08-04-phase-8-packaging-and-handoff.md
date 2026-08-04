# Phase 8 Specification: Packaging and Handoff

**Status:** Flow-reviewed; pending implementation plan
**Roadmap:** [External AI Trainer Integration Plan](../integration-plan.md)
**Predecessor:** [Phase 7B evidence](../reviews/2026-08-04-phase-7b-two-trainer-doubles-evidence.md)
**Flow review:** [Phase 8 flow review](../reviews/2026-08-04-phase-8-packaging-and-handoff-flow-review.md)
**Implementation plan:** [Phase 8 implementation plan](../plans/2026-08-04-phase-8-packaging-and-handoff.md)
**Verification evidence:** [Phase 8 evidence](../reviews/2026-08-04-phase-8-packaging-and-handoff-evidence.md)

## Goal

Make the completed local external-AI trainer feature reproducible for a new
developer on Windows with WSL, without adding launch automation or changing
ROM, Lua, protocol, service, model, or battle behavior.

## Terminology and documentation boundary

The current [integration plan](../integration-plan.md) names this delivery
**Phase 8** and is authoritative for all new artifacts. The parent design's
older "Phase 9: Packaging and handoff" heading is historical numbering and is
not rewritten by this phase.

This phase creates one high-level handoff guide for prerequisites,
compatibility, verification, and the end-to-end flow. The existing
`tools/mgba-bridge/README.md` remains the authoritative operational guide for
starting, observing, and recovering the local runtime. The two documents must
link to one another and must agree on the active BAGB/5 runtime contract.

## In scope

- One documentation-led handoff covering prerequisites, exact WSL build and
  mailbox-generation commands, PowerShell service startup, mGBA Lua loading,
  and the three supported battle scopes: trainer singles, intentional
  one-trainer doubles, and two-trainer doubles.
- A compatibility record for the manually validated mGBA executable, including
  its Windows path, title-bar version, and SHA-256 hash. The documented local
  model remains `qwen2.5-coder:7b`.
- A concise verification checklist that runs the full bridge/service tests,
  focused external-AI ROM tests, normal ROM build, and manual connected and
  disconnected smoke cases.
- Clear recovery instructions for ROM file locks, stale generated mailbox
  addresses, listener-port conflicts, model absence/cold startup, malformed
  responses, and service disconnects.
- Documentation evidence showing that the handoff was checked against the
  current BAGB/5 implementation.
- The supported handoff target is Windows with Ubuntu WSL and the existing
  project build toolchain. The guide states commands to verify prerequisites;
  it does not install or manage them.

## Out of scope

- Launchers, installers, process managers, automatic Ollama warm-up, automatic
  mGBA launch, auto-loading Lua, or automatic service restart.
- Any change to ROM code, mailbox layout, BAGB/5 protocol, Lua bridge, Python
  service, Ollama prompt/model behavior, trainer tags, timing, or battle rules.
- New model downloads, weights, credentials, cloud services, user telemetry, or
  release/distribution artifacts.

## Component boundaries

| Component | Phase 8 responsibility | Must remain unchanged |
| --- | --- | --- |
| ROM / ELF / map | Build from WSL and generate the matching Lua mailbox address. | Battle and mailbox behavior. |
| mGBA Lua bridge | Load one copy after generating the address file. | Loopback-only BAGB/5 forwarding and mailbox writes. |
| Python service | Start manually from PowerShell. | Tool-only model decision and vanilla fallback behavior. |
| Ollama | Verify the configured local model exists; optional manual warm-up. | Model installation and lifecycle management. |
| Documentation | State verified commands, boundaries, recovery, and smoke observations. | No generated artifacts or false portability claims. |

## Handoff flow

1. The developer confirms WSL build dependencies, Python 3, Ollama, the local
   `qwen2.5-coder:7b` model, and the pinned Windows mGBA installation.
2. With mGBA closed, the developer builds `pokeemerald.gba` in WSL and runs
   `generate_mailbox_config.py` against the same fresh `pokeemerald.elf`.
3. The developer starts the Python service in PowerShell; it may wait at
   `connecting to mGBA` until Lua becomes available.
4. The developer opens the fresh ROM in mGBA and loads
   `tools/mgba-bridge/mgba_bridge.lua` exactly once. Lua accepts the service
   connection on loopback.
5. The developer demonstrates a connected decision in a trainer single,
   intentional one-trainer double, and two-trainer double. For the latter, one
   audit must contain actions for both opponent battlers.
6. The developer stops the service during a voluntary opponent turn, observes
   the bounded `AI is thinking..` state clear, and confirms the saved vanilla
   AI actions continue the battle. A fresh connected attempt requires mGBA and
   Lua restart after a disconnect.

## Failure and fallback behavior

- If `pokeemerald.gba` cannot be overwritten, mGBA or another Windows process
  still holds the file; close it and rebuild. Do not delete generated or source
  files to work around the lock.
- If the generated mailbox address is missing or stale, regenerate it from the
  current ELF, then close and reopen mGBA before loading Lua.
- If Lua cannot listen on `127.0.0.1:57621`, close the previous mGBA/Lua
  session; do not run a second service or probe the listener.
- If Ollama is missing, unavailable, cold, malformed, slow, or disconnected,
  the service produces no valid response and the ROM retains its saved vanilla
  decision after the finite deadline.
- BAGB/4 scripts/services are incompatible with this BAGB/5 ROM. Version,
  magic, length, or malformed-response failures must not be manually bypassed;
  rebuild/regenerate/reload the matching components instead.

## Tests and exit criteria

The phase is complete when all are true:

1. `py -3 -m unittest discover -s tools\mgba-bridge\tests -q` passes.
2. `make -j16 check TESTS='External AI'` passes in WSL.
3. With mGBA closed, `make -j16` succeeds and mailbox address generation uses
   the resulting ELF.
4. The handoff guide is internally consistent with BAGB/5, current service
   log terminology (`choose_actions`), the fixed `AI is thinking..` message, all three battle
   modes, and the documented recovery behavior.
5. A manual smoke demonstrates a valid connected request and a disconnected
   vanilla fallback, then confirms trainer singles, one-trainer doubles, and
   two-trainer doubles remain playable.
6. No generated ROM, ELF, map, mailbox-address file, model data, or machine-
   specific transient artifact is committed.
