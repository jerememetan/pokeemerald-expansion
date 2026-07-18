# Battle AI Call Graph

**Phase:** 0 — Discovery and contract baseline  
**Specification:** [`specs/2026-07-18-phase-0-discovery-and-contract-baseline.md`](specs/2026-07-18-phase-0-discovery-and-contract-baseline.md)

## Existing moves-decision path

```text
BattleMainLoop
  STATE_TURN_START_RECORD                         src/battle_main.c
    RecordedBattle_CopyBattlerMoves(battler)
    if BattlerHasAi(battler) and not Battle Palace
      AI_DATA->mostSuitableMonId[battler] = GetMostSuitableMonToSwitchInto(...)
      gBattleStruct->aiMoveOrAction[battler] = ComputeBattleAiScores(battler)
        sBattler_AI = battler                     src/battle_ai_main.c
        BattleAI_SetupAIData(0xF, battler)
          BattleAI_SetupFlags()
          SetAiLogicDataForTurn(...)
          CheckMoveLimitations(battler, 0, MOVE_LIMITATIONS_ALL)
          gBattleStruct->aiChosenTarget[battler] = SetRandomTarget(battler)
        BattleAI_ChooseMoveOrAction()
          ChooseMoveOrAction_Singles(...) or ChooseMoveOrAction_Doubles(...)

  CONTROLLER_CHOOSEACTION                         src/battle_controller_opponent.c
    AI_TrySwitchOrUseItem(battler)                src/battle_ai_switch_items.c

  CONTROLLER_CHOOSEMOVE
    OpponentHandleChooseMove(battler)             src/battle_controller_opponent.c
      chosenMoveId = gBattleStruct->aiMoveOrAction[battler]
      gBattlerTarget = gBattleStruct->aiChosenTarget[battler]
      BtlController_EmitTwoReturnValues(...)
```

## Decision-state ownership

| Value | Producer | Consumer | Meaning in the current engine |
|---|---|---|---|
| `AI_DATA->moveLimitations[battler]` | `CheckMoveLimitations` during `BattleAI_SetupAIData` | AI scoring helpers | Bit mask for move slots that cannot currently be used. |
| `gBattleStruct->aiMoveOrAction[battler]` | `ComputeBattleAiScores` | `OpponentHandleChooseMove`; switch/item helpers also inspect it | Move slot `0`–`3` or one of the special `AI_CHOICE_*` values. |
| `gBattleStruct->aiChosenTarget[battler]` | `BattleAI_SetupAIData` and AI selection helpers | `OpponentHandleChooseMove` | Current target battler index for the selected action. |
| `gBattlerTarget` | Controller sets it from `aiChosenTarget` | Move target/animation path | Controller-local target used when emitting the action. |
| `gBattleResources->bufferA[battler]` | Battle main/controller command protocol | `OpponentHandleChooseMove` | Carries the battler's move slots and PP information to the controller. |

## Safe first interception seam

The Phase 1 hook belongs after the ordinary `ComputeBattleAiScores` result exists and before `OpponentHandleChooseMove` emits a move. It must retain the current `aiMoveOrAction` and `aiChosenTarget` as fallback, then replace both values only after validating a legal-action entry produced by the ROM.

This seam is safe for the initial moves-only scope because it does not modify move scoring, battle scripts, damage calculation, or controller emission. It also leaves `CONTROLLER_CHOOSEACTION` and `AI_TrySwitchOrUseItem` unchanged, so existing switching and item decisions remain engine-controlled.

## Boundaries for future phases

- `BATTLE_TYPE_PALACE` uses `ChooseMoveAndTargetInBattlePalace` and is excluded from version 1.
- Double battles use `ChooseMoveOrAction_Doubles` and need a separate turn-level action contract.
- Wild, Safari, roamer, recorded, link, and Battle Frontier variants have distinct flags or controller paths and remain unchanged until separately specified.
- `aiMoveOrAction` can encode non-move choices. Version 1 accepts only ROM-produced legal move actions; it never lets the service submit a raw action value.
