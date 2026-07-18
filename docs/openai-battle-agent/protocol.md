# ROM–Bridge Protocol, Version 1

**Scope:** One external-enabled opponent battler, trainer single battle, move actions only.  
**State inventory:** [`battle-state.md`](battle-state.md)

## Purpose

The protocol allows an mGBA Lua bridge and local service to request a ROM-produced legal move action. The ROM remains authoritative: it generates the legal action list, validates the reply, and retains an ordinary AI fallback for every request.

## Mailbox location and ownership

Phase 2 will declare a named `EWRAM_DATA` global mailbox. The mGBA launch tooling resolves that symbol from the `.map` file emitted by the exact ROM build. The Lua script does not scan memory and does not use a hard-coded address.

| Field group | Writer | Reader | Rule |
|---|---|---|---|
| Magic and protocol version | ROM at initialization | Bridge and ROM | Bridge disables itself on mismatch. |
| Request sequence, status, and snapshot | ROM | Bridge | ROM writes payload before changing request status to `PENDING`. |
| Response sequence, status, and legal-action index | Bridge | ROM | Bridge writes payload before changing response status to `READY`. |
| Fallback move/action and target | ROM | ROM | Never supplied or modified by the bridge. |

## Required fields

```text
magic: u32
protocolVersion: u16             // 1
requestStatus: u8
responseStatus: u8
requestSequence: u32
responseSequence: u32
requestingBattler: u8
battleMode: u8                   // trainer single battle in version 1
turnNumber: u16
snapshot: BattleAgentSnapshotV1
legalActionCount: u8
legalActions: BattleAgentLegalActionV1[maximum action count]
responseLegalActionIndex: u8
```

`BattleAgentSnapshotV1` is the visible-state subset defined in `battle-state.md`. `BattleAgentLegalActionV1` is the three-field record `legalActionIndex`, `moveSlot`, and `targetBattler`.

## State transitions

```text
ROM:    IDLE -> WRITING_REQUEST -> PENDING -> ACCEPTED -> IDLE
                                   PENDING -> FALLBACK -> IDLE
Bridge: DISCONNECTED | CONNECTED
        CONNECTED + PENDING -> RESPONSE_READY
```

1. The ROM first runs ordinary AI scoring and records its action/target as the fallback.
2. The ROM clears the preceding response state, increments `requestSequence`, writes the snapshot and legal-action list, then sets `requestStatus = PENDING`.
3. The bridge observes the new pending sequence, forwards a framed local message, and writes a response sequence plus `responseLegalActionIndex`.
4. The bridge sets `responseStatus = READY` only after its response payload is complete.
5. The ROM accepts the response only when all validation rules pass; otherwise it continues polling its asynchronous wait state.
6. On acceptance, the ROM maps the legal-action entry to its move slot and target, then sets `aiMoveOrAction` and `aiChosenTarget`.
7. On deadline or rejection, the ROM restores/retains the precomputed ordinary AI action and target and sets `FALLBACK`.

## Validation order

The ROM validates in this order:

1. Mailbox magic equals the version-1 constant.
2. Protocol version equals `1`.
3. Response status equals `READY`.
4. Response sequence equals the current request sequence.
5. Response sequence has not already been accepted for this request.
6. `responseLegalActionIndex` is less than `legalActionCount`.
7. The selected entry is present in the current request and its move slot/target remain legal when applied.

A failure at any step rejects the response without changing the retained ordinary AI decision.

## Deadline and transport failures

An external-enabled decision uses a 600-frame asynchronous wait budget. The battle logic returns to the main loop each frame; it does not busy-wait, invoke a blocking Lua connection, or suspend mGBA frame processing. A later bridge phase presents a concise status message while the request is pending.

The following conditions select fallback: absent bridge, disconnected bridge, wrong magic, wrong version, malformed message, sequence mismatch, duplicate response, non-ready status, action-index out of range, illegal selected entry, and deadline expiry. A response received after fallback has an obsolete sequence and is ignored.

## Compatibility and security

- Lua binds only to loopback, and the local service connects before gameplay begins.
- The Lua script checks the mailbox magic and protocol version before forwarding a request.
- Request and response messages have a fixed maximum size determined by the fixed mailbox layout.
- A bridge cannot execute raw moves, targets, party indices, battle items, damage values, or scripts; it can only request an existing legal-action index.
- Any additive protocol extension requires a new protocol version, a new specification, a flow review, and an implementation plan.
