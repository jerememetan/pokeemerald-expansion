# Phase 3A Flow Review: mGBA Loopback Bridge Spike

**Specification reviewed:** [`../specs/2026-07-28-phase-3a-mgba-loopback-bridge.md`](../specs/2026-07-28-phase-3a-mgba-loopback-bridge.md)  
**Parent roadmap:** [`../2026-07-18-mgba-ai-trainer-design.md`](../2026-07-18-mgba-ai-trainer-design.md)

## Codebase and platform grounding

- The ROM already exposes `gBattleAgentMailbox` as an `EWRAM_DATA` V1 mailbox. Its compile-time ARM APCS-GNU assertions establish the bridge offsets: request status `6`, response status `7`, request sequence `8`, legal-action count `128`, response sequence `148`, and response action index `152`.
- `BattleAgent_TryPublishRequest` explicitly commits a request with a compiler barrier and a volatile `PENDING` write last. It clears all response fields before each new eligible request and does not consume a response.
- The only production seam is immediately after `ComputeBattleAiScores` and before the Phase 1 test mock. The existing focused tests prove the output vanilla move remains unchanged.
- The current response enum defines only `NONE`; a named `READY = 1` value is required before any external writer can use the response slot consistently.
- The repository already ignores `*.elf` and `*.gba`, but has no mGBA bridge directory. `pokeemerald.elf` is the modern build artifact named by the Makefile. A generated Lua address config therefore needs a dedicated ignore entry.
- Official mGBA documentation exposes Lua GBA memory reads/writes, frame callbacks, loopback socket binding, per-frame socket events/polling, and warns that Lua `socket.connect` is blocking. Manual verification validated the Windows 64-bit stable mGBA `0.10.5` title-bar version; final evidence must record the SHA-256 and `--version` output of the exact executable used. [Scripting API](https://mgba.io/docs/scripting.html), [downloads](https://mgba.io/downloads.html).

## User flows

1. **Valid responder round trip.** The user builds the ROM, generates a mailbox-address Lua config from the same ELF, starts the deterministic responder, loads the Lua script in Windows mGBA, and battles Calvin. Lua sees one fresh `PENDING` sequence, sends one bounded request line, accepts a valid matching response, writes the three permitted response fields, and logs success. Calvin still uses vanilla AI.
2. **Responder absent at launch.** Lua binds the local listener and receives no client. It reads frames but performs no mailbox write. The ROM never waits and the battle remains playable.
3. **Responder disconnects or sends a partial line.** Lua removes/drops that client state without reconnecting. It does not write a partial or stale response; later frames continue.
4. **Stale or invalid response.** A response with the wrong sequence, an index outside the current 0–3 legal list, a wrong protocol token, a signed/non-decimal field, or a line longer than 96 bytes is logged and discarded. No other emulator memory is touched.
5. **ROM rebuilt without regenerating config.** Lua detects a missing/generated-address failure or a mailbox header/shape mismatch and disables writes. The user regenerates config from the current ELF.
6. **New request supersedes an old one.** Lua's forwarded-sequence state changes only for a new current sequence. A late response for the older sequence cannot be written after revalidation.

## Gaps found and resolved

### Critical

1. **Lua's outbound connect is explicitly blocking.** Calling it to reach a Python listener would freeze mGBA when the responder is unavailable.

   **Resolution:** Lua is listener-only. It binds `127.0.0.1`; Python, which is outside the emulator, connects with its own bounded retry/timeout. Lua must only call `accept` after its listener reports readable data and must process at most one accept and one complete response per frame.

2. **The response state had no named ready value or write-commit rule.** A bridge writing raw `1` would be an undocumented protocol extension and could expose a partially written response to a future consumer.

   **Resolution:** Phase 3A adds `BATTLE_AGENT_RESPONSE_READY = 1`. Lua revalidates the current request immediately before writing, writes sequence then action index, and writes `READY` last. It never writes request fields, snapshot bytes, legal actions, AI actions, or targets.

3. **An ELF-derived address can be stale after rebuilding.** A stale config could otherwise direct Lua to unrelated EWRAM.

   **Resolution:** config generation is mandatory after every ROM build, emits an ignored file, and rejects non-EWRAM/missing/duplicate symbols. Lua additionally requires V1 magic, version, `PENDING`, trainer-single mode, requester range, and legal-action count 1–4 before forward/write; it rechecks sequence/status/count before committing a response. Any failed check disables that frame's operation.

### Important

1. **The Phase 2 mailbox permits an empty legal list.** A responder selecting action zero for that request would be invalid.

   **Resolution:** Lua does not send a bridge request for action count zero; Python never replies to zero count; manual coverage records this no-write path.

2. **The current test runner assumes response status is `NONE`.** New bridge-ready tests would fail unless the test API names the allowed state deliberately.

   **Resolution:** update the test-only response setter and assertions to use `BATTLE_AGENT_RESPONSE_READY`, then add one focused test that a ready response remains non-authoritative and is cleared by the next publication.

3. **A small spike message does not transport the Phase 2 snapshot.** Treating it as a durable service protocol would force unnecessary compatibility promises.

   **Resolution:** the `BAGB/1` two-field request line is explicitly bridge-spike-only. Phase 4 must specify a new, full snapshot service message before any model service is built.

### Minor

1. **mGBA console logs can become noisy on repeated malformed input.**

   **Resolution:** log each rejection reason at most once per request sequence/client event, cap quoted line content at 32 printable characters, and never print snapshot data.

## Questions resolved by safe defaults

1. **Which Windows mGBA build is used?** Use the manually validated Windows 64-bit mGBA `0.10.5`; record the SHA-256 and `--version` output of the exact executable, not an archive checksum, and fail setup if the scripting window cannot load a probe script.
2. **Which port is used?** Default to `57621`, configurable only through a tracked Lua settings file. Bind address is fixed to `127.0.0.1`.
3. **Does the bridge wait for a response?** No. It observes each frame and never calls an unbounded connection, receive, or retry operation inside mGBA.
4. **What response can the deterministic responder select?** Index `0` only, and only when the announced count is in `1..4`. The bridge independently validates it.

## Recommended next steps

1. Amend the specification with the explicit build/port pin and the `accept` readability guard.
2. Write the Phase 3A task plan around a Python parser/generator test suite, a Lua probe, a named ROM `READY` status, and manual mGBA evidence.
3. Do not add ROM response consumption, snapshot transport, or model code in this phase.

## Links

- [Phase 3A specification](../specs/2026-07-28-phase-3a-mgba-loopback-bridge.md)
- [Phase 2 evidence](2026-07-28-phase-2-build-and-test-evidence.md)
- [Phase 3A evidence](2026-07-29-phase-3a-mgba-loopback-bridge-evidence.md)
- [mGBA scripting API](https://mgba.io/docs/scripting.html)
