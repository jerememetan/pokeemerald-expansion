# Phase 8 Packaging and Handoff Flow Review

**Specification reviewed:** [Phase 8 specification](../specs/2026-08-04-phase-8-packaging-and-handoff.md)
**Implementation plan:** [Phase 8 implementation plan](../plans/2026-08-04-phase-8-packaging-and-handoff.md)
**Verification evidence:** [Phase 8 evidence](2026-08-04-phase-8-packaging-and-handoff-evidence.md)
**Reviewed:** 2026-08-04
**Method:** `spec-flow-analyzer`, grounded in the active roadmap, the current
bridge runtime guide, BAGB/5 service and Lua implementation, `.gitignore`, and
the pinned mGBA evidence.

## Repository grounding

- The active work plan calls the handoff deliverable **Phase 8**. The older
  parent design calls its then-final packaging section “Phase 9”; that is
  historical numbering, not the current delivery name.
- The active path is fixed-frame BAGB/5: `mgba_bridge.lua` loads the generated
  mailbox address, and `battle_agent_service.py` parses a BAGB/5 snapshot and
  finishes with `choose_actions`. `bridge_protocol.py` retains older BAGB/1
  helpers for its earlier tests, so a documentation guide must identify BAGB/5
  as the active runtime without implying the older helpers are launchable.
- `tools/mgba-bridge/README.md` is the operational launch guide. It already
  documents the three supported trainer scopes, loopback endpoint, generated
  file, model name, fallback, and recovery behavior.
- `tools/mgba-bridge/generated/mailbox_address.lua` is ignored by Git, so the
  guide must require regeneration after every rebuild and must never publish an
  address as a portable constant.
- The pinned mGBA record is the Phase 3A evidence: Windows path
  `C:\\Program Files\\mGBA\\mGBA.exe`, GUI title-bar version `0.10.5`, and SHA-256
  `5A3C98C2984DD04BD0D7C9378CDFAE937AE0D73A196C880BB2EECF3B254AF247`.

## Flow analysis

### 1. Fresh developer: build, connect, and demonstrate

1. Verify Windows, Ubuntu WSL build prerequisites, Python launcher, Ollama,
   local `qwen2.5-coder:7b`, and the pinned mGBA executable.
2. Close mGBA, build the ROM in WSL, then generate the Lua address from the
   resulting ELF.
3. Start one Python service in PowerShell. It waits until one Lua listener is
   available.
4. Open the fresh ROM in mGBA, load the Lua script once, and confirm both ends
   say connected.
5. Demonstrate a trainer single, intentional one-trainer double, and
   two-trainer double. The latter must produce a single audit containing both
   opponent battlers.

**Failure paths:** missing model or slow cold start, stale address, ROM lock,
listener conflict, absent service, model/tool-output failure, and service
disconnect must leave the saved vanilla AI decision usable. Reconnection after
a disconnect requires restarting mGBA and reloading Lua; it is not an in-place
reconnect contract.

### 2. Rebuild after a source change

1. Close mGBA before `make` so Windows does not retain `pokeemerald.gba`.
2. Build a fresh ELF and regenerate `mailbox_address.lua` from it.
3. Open the new ROM and load Lua once.

**Failure path:** retaining a generated address from a previous ELF risks a
version/address mismatch. The safe recovery is regenerate, then restart mGBA;
never hand-edit the generated file or mailbox.

### 3. Demonstrate fallback deliberately

1. While an external turn is pending, stop or omit the Python service.
2. The lower message panel shows the fixed `AI is thinking..` text during the
bounded wait.
3. The message clears and the already-saved trainer AI action proceeds.

**Failure path:** a user may mistake a cold model, malformed response, or
connection error for a permanent freeze. The guide must identify the expected
bounded fallback and its log markers, without asking the user to probe the
loopback port or forge a response.

### 4. Verify reproducibility without adding a launcher

1. Run the Python bridge tests and focused ROM External AI tests.
2. Run a normal ROM build with mGBA closed.
3. Confirm generated artifacts remain ignored.

**Failure path:** the guide must not accidentally become a launcher,
installer, deployment artifact, or promise that an arbitrary mGBA build/model
will work. It remains a manual local development handoff.

## Gaps found and resolutions

| Severity | Gap | Resolution |
| --- | --- | --- |
| Important | Current roadmap calls the deliverable Phase 8, while the older parent design calls packaging Phase 9. | All new artifacts use **Phase 8**, the current roadmap is authoritative, and they link to the parent design only as historical context. No historical rewrite is needed. |
| Important | The runtime guide has stale three-dot thinking-message checks, while the implementation displays exactly `AI is thinking..`. | Correct every guide/checklist occurrence to the fixed two-dot text and state that it is presentation only. |
| Important | The runtime guide contains mojibake for the menu arrow and `Pokémon`, reducing copy/readability on the handoff path. | Replace those characters with ASCII-safe wording (`Tools > Scripting...`, `Pokemon`) in the operational commands/checklists. |
| Important | A new-developer handoff needs a clear documentation boundary so it does not duplicate or contradict the operational guide. | Add one top-level Phase 8 handoff guide for prerequisites, compatibility, and end-to-end verification. Keep `tools/mgba-bridge/README.md` as the authoritative runtime/recovery guide and cross-link them. |
| Important | “Windows with WSL” is too broad to guarantee every machine configuration. | Document the validated target as Windows with Ubuntu WSL and the existing project toolchain. State exact prerequisites and verification commands; do not add an installer or claim cross-platform support. |
| Minor | The source tree still contains legacy BAGB/1 helpers and a BAGB/4 historical service docstring. | The handoff guide names BAGB/5 as the active runtime contract and does not present legacy helpers as compatible. Source-comment cleanup is outside this documentation-only phase because it changes no handoff behavior. |

No critical gaps remain after these resolutions.

## Required implementation-plan coverage

The implementation plan must:

1. Create the Phase 8 high-level handoff guide and cross-link it with the
   operational bridge README and roadmap.
2. Correct stale text and unsafe character rendering in the bridge README
   without changing its commands, protocol, or runtime behavior.
3. Include exact test/build commands, expected results, the generated-file
   ignore check, and connected/disconnected manual smoke criteria for all
   three battle scopes.
4. Record fresh Phase 8 evidence only after the commands and manual smoke are
   performed.
