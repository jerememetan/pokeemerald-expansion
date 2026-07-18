# Battle State Inventory

**Phase:** 0 — Discovery and contract baseline  
**Protocol:** [`protocol.md`](protocol.md)

## Version-1 visibility rule

The service receives only information that is visible to a player in the current battle plus the ROM-produced legal-action list. The external service is not an extension of the engine's omniscient AI and cannot infer legality from omitted state.

| Field | ROM source | Visible to service | Version-1 use | Reason |
|---|---|---:|---|---|
| Requesting battler | Current AI battler index and `gBattlerPositions` | Yes | Identify the acting opponent | The service must select for one concrete battler. |
| Battle type | `gBattleTypeFlags` | Yes | Reject unsupported modes | Version 1 accepts a trainer single battle only. |
| Turn number | New ROM-owned counter in the future mailbox producer | Yes | Sequence/debug context | The current engine has turn state but no public agent turn counter. |
| Active species | `gBattleMons[battler].species` | Yes | Battle summary | Visible on the battlefield. |
| Current and maximum HP | `gBattleMons[battler].hp`, `maxHP` | Yes | Battle summary | Exact values are an intentional developer-demo convenience. |
| Major status | `gBattleMons[battler].status1` | Yes | Battle summary | Visible status condition. |
| Stat stages | `gBattleMons[battler].statStages` | Yes | Battle summary | A compact representation of visible battle modifiers. |
| Move slots and current PP | `gBattleMons[requester].moves`, `pp` | Own battler only | Explain legal choices | The service must not select a move outside these slots. |
| Weather | `gBattleWeather` | Yes | Battle context | Displayed field state. |
| Terrain/field effects | `gFieldStatuses`, `gBattleTerrain` | Yes, normalized | Battle context | Protocol exports only documented field bits. |
| Side conditions | `gSideStatuses` | Yes, normalized | Battle context | Protocol exports only battle-visible side effects. |
| Legal action entries | ROM producer using move slots, `CheckMoveLimitations`, and target helpers | Yes | Sole action input | The ROM is the legality authority. |
| Recent turn events | New fixed-size ROM event ring | Yes | Short tactical context | Version 1 stores at most three normalized events. |

## Excluded state

| Excluded field | Why it is excluded |
|---|---|
| Opponent hidden move slots and PP | Not normally visible to the other battler. |
| Opponent private party composition | Not normally visible before the Pokémon appears. |
| Opponent ability and held item | Hidden unless revealed by existing battle events; version 1 exports no inference data. |
| `AI_DATA->simulatedDmg`, effectiveness, accuracy, and speed predictions | Internal AI calculations; exposing them would make the service omniscient and couple the protocol to implementation details. |
| Raw pointers, `gBattleResources` buffers, scripts, and protection internals | These are unstable engine implementation details and are unsafe bridge data. |
| RNG state | The service may not influence or predict random outcomes. |

## Legal-action construction

The future ROM producer creates entries only after ordinary AI data exists. It obtains candidate moves from `gBattleMons[requester].moves`, marks unusable slots with `CheckMoveLimitations(requester, 0, MOVE_LIMITATIONS_ALL)`, and uses the engine target rules to enumerate current valid targets.

```text
legalActionIndex: u8
moveSlot: u8          // 0 through 3
targetBattler: u8     // current, engine-approved battler index
```

An action is present only when all of the following are true:

1. `moveSlot` contains a non-empty move.
2. The slot is not set in the current move-limitations mask.
3. The target is valid for that move at this instant.
4. The battle mode is supported by version 1.

The service returns only `legalActionIndex`. The ROM rechecks the selected index against the current request's action list before overwriting `aiMoveOrAction` and `aiChosenTarget`.

## Deferred fields

- Switching candidates and party indices belong to the switching extension.
- Battle items and item targets belong to the item extension.
- Partner targeting, spread moves, and two coordinated opponent actions belong to the double-battle specification.
- Revealed hidden-information tracking may be added only with a dedicated visibility policy and protocol-version review.
