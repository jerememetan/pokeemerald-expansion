# Phase 3A Specification: mGBA Loopback Bridge Spike

**Status:** Implemented and verified
**Parent roadmap:** [`../2026-07-18-mgba-ai-trainer-design.md`](../2026-07-18-mgba-ai-trainer-design.md)  
**Prerequisite:** [Phase 2 build and test evidence](../reviews/2026-07-28-phase-2-build-and-test-evidence.md)

## Goal

Prove that a Windows mGBA Lua script can observe a Phase 2 mailbox request and round-trip a deterministic, valid response over a loopback-only connection without blocking emulator frames, input, or the ROM's existing vanilla trainer AI.

This is a bridge spike. It does **not** make the ROM apply an external choice. Calvin must continue using the move selected by the existing trainer AI even after the bridge writes a valid response.

## Scope

### In scope

- Windows 64-bit mGBA `0.10.5` with Lua scripting, validated by the mGBA title bar during manual bridge checks. Before phase exit, record the SHA-256 and `--version` output of the exact `mGBA.exe` used; an archive hash is not sufficient.
- One Lua script that binds a TCP listener to `127.0.0.1` on a documented configurable port, accepts at most one local client, and runs all socket work through frame polling/callbacks.
- One deterministic local Python responder for the bridge spike. It connects to the Lua listener, returns action index `0` only when the bridge announces a pending request with at least one legal action, and otherwise sends no response.
- A small, line-delimited bridge transport for the spike:

  ```text
  BAGB/1 REQUEST <requestSequence> <legalActionCount>\n
  BAGB/1 RESPONSE <requestSequence> <legalActionIndex>\n
  ```

  Both integers are unsigned decimal ASCII without leading sign characters. A complete line must be at most 96 bytes.

- A generated, untracked Lua mailbox-address configuration derived from the just-built `pokeemerald.elf` symbol `gBattleAgentMailbox`; no hard-coded EWRAM address and no memory scan.
- A response-status contract addition in the ROM header only: `BATTLE_AGENT_RESPONSE_READY = 1`. The bridge writes `responseSequence`, then `responseLegalActionIndex`, and writes `responseStatus = READY` last. It writes no other mailbox byte.
- Lua console diagnostics for listener start, client connect/disconnect, request forwarded, rejected response, and response written. Diagnostics contain no model prompt, hidden state, or unbounded packet data.
- Repeatable manual bridge-spike verification for valid response, absent responder, disconnect, stale response, malformed response, and wrong protocol line.

### Out of scope

- Reading or applying `READY` in the ROM; changing `aiMoveOrAction`, `aiChosenTarget`, controller state, damage, UI, input, timing, or battle mechanics.
- A model, API key, cloud service, HTTP, OpenAI client, prompt, explanation, switch, item, double-battle, or broad-trainer support.
- Binding non-loopback interfaces, accepting more than one responder, reconnect loops in Lua, arbitrary emulator-memory writes, ROM-address scanning, or transport of hidden battle data.
- A durable local-service protocol. Phase 4 may replace the spike's two-field request line with a versioned full-snapshot message after its own specification and review.

## Boundaries

| Component | Responsibility | Must not do |
|---|---|---|
| ROM | Publish Phase 2 request; define `READY`; continue vanilla AI. | Poll network, wait, accept a response, or change a chosen move. |
| Lua bridge | Read validated mailbox fields; forward one pending request sequence; validate a responder line; write only three response fields in commit order. | Use `socket.connect`, alter any action/target field, or pause/wait for a client. |
| Python responder | Connect to `127.0.0.1`, parse bounded bridge lines, choose index `0` only when count is positive, send one bounded line. | Inspect the ROM, bind a public address, or implement AI/model logic. |
| Generated address config | Supply the current ELF-derived mailbox address to Lua. | Be committed or reused with another build. |

## Mailbox and address contract

The Phase 2 V1 mailbox is 156 bytes under this repository's ARM APCS-GNU ABI. Its bridge-relevant offsets are fixed by existing C assertions:

| Field | Offset | Bridge access |
|---|---:|---|
| `magic` | 0 | read, must equal `BAG1` |
| `protocolVersion` | 4 | read, must equal 1 |
| `requestStatus` | 6 | read, must equal `PENDING` before forwarding |
| `responseStatus` | 7 | write `READY` last only |
| `requestSequence` | 8 | read and echo in response |
| `legalActionCount` | 128 | read; must be 1 through 4 for this spike |
| `responseSequence` | 148 | write first |
| `responseLegalActionIndex` | 152 | write second |

The generator must invoke `arm-none-eabi-nm -n pokeemerald.elf`, locate the unique global `gBattleAgentMailbox` symbol, reject a missing/non-EWRAM/out-of-range address, and write `tools/mgba-bridge/generated/mailbox_address.lua`. The generated file contains only `MAILBOX_ADDRESS = 0x020...` and is ignored by Git. Lua must refuse every read/write if magic or version differs from the generated build's expected V1 values.

## Bridge flow and failure behavior

1. The user builds the ROM and generates the address config from that same ELF.
2. Lua loads the generated config, binds `127.0.0.1:57621` by default, starts listening, and registers a frame callback. It never calls Lua's blocking `socket.connect`.
3. The Python responder may connect before or after mGBA starts. Lua calls `accept` only after the listener reports readable data, accepts no more than one client, and performs at most one bounded receive-processing step per frame.
4. On a new `PENDING` mailbox sequence with action count 1–4, Lua sends exactly one `REQUEST` line and remembers that sequence as forwarded.
5. Lua accepts only one complete, bounded `RESPONSE` line with protocol `BAGB/1`, the currently pending sequence, and an index less than current `legalActionCount`. It discards every other line without writing memory.
6. For an accepted line, Lua writes response sequence and index, then writes `READY` last. It logs the result. The ROM does not consume it in Phase 3A.
7. No client, disconnect, partial line, socket error, bad magic/version, stale sequence, invalid index, malformed line, or zero-action request causes a wait, reconnect attempt, action change, or arbitrary write. Lua logs a bounded reason and resumes frame processing.
8. A newly observed mailbox sequence supersedes any in-flight/previous bridge state. A late response for an older sequence is ignored.

## Tests and measurable exit criteria

1. A Python unit test validates every accepted/rejected bridge line and enforces the 96-byte limit.
2. A generator test fixture proves the mailbox symbol parser accepts one EWRAM symbol and rejects missing, duplicate, and non-EWRAM symbols.
3. A ROM test confirms the V1 header exposes `BATTLE_AGENT_RESPONSE_READY` but publication still clears response fields and never changes the vanilla AI decision.
4. Manual Windows mGBA test: with the deterministic responder connected, Lua logs one forwarded request and one `READY` write for Calvin; Calvin still uses the vanilla-selected move.
5. Manual Windows mGBA test: without a responder, and after an active responder disconnects, input and frames continue normally and Calvin's battle remains playable.
6. Manual Windows mGBA test: stale sequence, invalid action index, malformed line, and wrong protocol line are rejected with no mailbox action/target writes.
7. The ROM builds and `make -j16 check TESTS='External AI'` remains green. No Phase 3A test changes battle mechanics or widens eligibility.

## Links

- [Parent roadmap](../2026-07-18-mgba-ai-trainer-design.md)
- [Phase 2 specification](2026-07-26-phase-2-legal-action-snapshot.md)
- [Phase 2 evidence](../reviews/2026-07-28-phase-2-build-and-test-evidence.md)
- [Phase 3A flow review](../reviews/2026-07-28-phase-3a-mgba-loopback-bridge-flow-review.md)
- [Phase 3A implementation plan](../plans/2026-07-28-phase-3a-mgba-loopback-bridge.md)
- [Phase 3A evidence](../reviews/2026-07-29-phase-3a-mgba-loopback-bridge-evidence.md)
- [mGBA scripting API](https://mgba.io/docs/scripting.html)
- [mGBA development downloads](https://mgba.io/downloads.html)
