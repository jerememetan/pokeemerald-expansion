# Phase 3A mGBA Loopback Bridge Evidence

**Status:** Final verification recorded  
**Specification:** [Phase 3A specification](../specs/2026-07-28-phase-3a-mgba-loopback-bridge.md)  
**Implementation plan:** [Phase 3A implementation plan](../plans/2026-07-28-phase-3a-mgba-loopback-bridge.md)  
**Flow review:** [Phase 3A flow review](2026-07-28-phase-3a-mgba-loopback-bridge-flow-review.md)

## Final tool and build evidence

- **mGBA executable:** `C:\Program Files\mGBA\mGBA.exe`
- **mGBA version:** Windows title bar reported `0.10.5`.
- **mGBA executable SHA-256:**
  `5A3C98C2984DD04BD0D7C9378CDFAE937AE0D73A196C880BB2EECF3B254AF247`
- **Executable version invocation:**

  ```powershell
  & 'C:\Program Files\mGBA\mGBA.exe' --version
  ```

  was run and returned immediately with no stdout or stderr on this Windows
  build. Therefore the observed GUI title-bar version (`0.10.5`) is the version
  evidence; `--version` is not a textual version source for this executable.
- **Focused ROM test:** WSL `make -j16 check TESTS='External AI'` passed
  **17/17** tests. The known `ASSUME` diagnostics are the established unrelated
  baseline and did not represent an External AI test failure.
- **ROM build:** final WSL `make -j16` succeeded after mGBA was closed.
- **Address config:** the generator ran against that fresh `pokeemerald.elf`.
  Its output was in the permitted EWRAM range, and
  `git check-ignore tools/mgba-bridge/generated/mailbox_address.lua` printed
  `tools/mgba-bridge/generated/mailbox_address.lua`. The generated address
  itself is intentionally not recorded or committed.

## Validated manual bridge behavior

Windows mGBA displayed version **0.10.5** in its title bar. The Lua listener
started at `127.0.0.1:57621`, accepted the deterministic local responder, and
logged forwarded requests with matching response writes for sequences `1`
through `4`. Calvin's battle remained playable and continued to use the
vanilla trainer AI, as required because Phase 3A does not consume `READY`.

The following manual fallback checks were also observed while fighting Calvin:

| Case | Observed result |
|---|---|
| No responder | Listener started; no client or response-write log; battle remained playable. |
| Active responder disconnect | A request was forwarded, then `BAGB client disconnected: response receive failed: disconnected` appeared; no later response write occurred. |
| Stale reply | `BAGB/1 RESPONSE 999 0` was rejected; no response write occurred. |
| Invalid action index | A current-sequence reply with index `4` was rejected as malformed; no response write occurred. |
| Malformed sequence | `BAGB/1 RESPONSE nope 0` disconnected the client as malformed; no response write occurred. |
| Wrong protocol version | `BAGB/2 RESPONSE <sequence> 0` disconnected the client as malformed; no response write occurred. |

These checks validate the Lua listener, the loopback transport, and its safe
failure behavior. They do **not** prove ROM response consumption: the ROM
intentionally ignores `READY` in Phase 3A and the vanilla fallback remains
authoritative.

## Phase exit and next prerequisite

Phase 3A's bridge-spike exit criteria are met. The documented evidence shows
the ROM remains buildable
and its focused External AI tests pass, generation is tied to the fresh ELF and
the generated config is ignored, and the valid and failure manual cases retain
playability and the vanilla fallback.

Phase 4 may begin only with its own specification, flow review, and plan for a
full-snapshot local-service protocol and ROM-side response acceptance. Phase
3A's two-field deterministic responder is not that service.
