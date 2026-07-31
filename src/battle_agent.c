#include "global.h"
#include "battle_agent.h"
#include "battle_ai_main.h"
#include "battle_ai_switch_items.h"
#include "battle_ai_util.h"
#include "battle_controllers.h"
#include "battle_message.h"
#include "battle_setup.h"
#include "battle_util.h"
#include "constants/battle_ai.h"
#include "data.h"
#include "menu.h"
#include "text.h"
#include "util.h"
#include "window.h"

#if TESTING
#include "test_runner.h"
#endif

EWRAM_DATA struct BattleAgentMailboxV3 gBattleAgentMailbox;

struct BattleAgentWaitState
{
    u32 sequence;
    u16 frames;
    u8 fallbackMoveOrAction;
    u8 fallbackTarget;
    bool8 active;
    bool8 hasAcceptedAction;
};

static EWRAM_DATA struct BattleAgentWaitState sBattleAgentWaitStates[MAX_BATTLERS_COUNT];

struct BattleAgentThinkingStatusState
{
    u8 displayState;
    u8 frames;
    bool8 ownsMessageWindow;
};

static EWRAM_DATA struct BattleAgentThinkingStatusState sBattleAgentThinkingStatuses[MAX_BATTLERS_COUNT];

static const u8 sText_AiThinkingTwoDots[] = _("AI is thinking..");
static const u8 sThinkingStatusTextColors[] = {1, 15, 6};

static bool32 BattleAgent_IsEligible(u32 battler);
static bool32 BattleAgent_NormalizeSingleTarget(u32 requester, u16 move, u8 *target);
static bool32 BattleAgent_IsLegalSwitch(u32 requester, u8 partySlot);
static void BattleAgent_CopySnapshot(u32 requester);
static void BattleAgent_BuildLegalActions(u32 requester);
static void BattleAgent_CopyMoveSnapshot(struct BattleAgentMoveSnapshotV3 *snapshotMove, u16 move, u8 pp);
static void BattleAgent_BeginRequest(void);
static void BattleAgent_CommitRequest(void);
static void BattleAgent_ClearResponse(void);
static const u8 *BattleAgent_GetThinkingText(u8 displayState);
static bool32 BattleAgent_UpdateThinkingStatusState(u32 battler, bool32 playerActionConfirmed, bool32 messageWindowIdle);
static void BattleAgent_RenderThinkingStatus(u32 battler);

static u8 BattleAgent_GetEffectivenessCategory(u8 effectiveness)
{
    if (effectiveness == AI_EFFECTIVENESS_x0)
        return 0;
    if (effectiveness < AI_EFFECTIVENESS_x1)
        return 1;
    if (effectiveness == AI_EFFECTIVENESS_x1)
        return 2;
    return 3;
}

static const u8 *BattleAgent_GetThinkingText(u8 displayState)
{
    (void)displayState;
    return sText_AiThinkingTwoDots;
}

static void BattleAgent_RenderThinkingStatus(u32 battler)
{
    FillWindowPixelBuffer(B_WIN_MSG, PIXEL_FILL(15));
    AddTextPrinterParameterized4(B_WIN_MSG,
                                 FONT_NORMAL,
                                 0,
                                 1,
                                 0,
                                 0,
                                 sThinkingStatusTextColors,
                                 TEXT_SKIP_DRAW,
                                 BattleAgent_GetThinkingText(sBattleAgentThinkingStatuses[battler].displayState));
    PutWindowTilemap(B_WIN_MSG);
    CopyWindowToVram(B_WIN_MSG, COPYWIN_FULL);
}

static bool32 BattleAgent_UpdateThinkingStatusState(u32 battler, bool32 playerActionConfirmed, bool32 messageWindowIdle)
{
    struct BattleAgentThinkingStatusState *status;

    if (battler >= MAX_BATTLERS_COUNT || !sBattleAgentWaitStates[battler].active)
        return FALSE;

    status = &sBattleAgentThinkingStatuses[battler];
    if (!status->ownsMessageWindow)
    {
        if (!playerActionConfirmed || !messageWindowIdle)
            return FALSE;

        status->ownsMessageWindow = TRUE;
        status->displayState = BATTLE_AGENT_THINKING_TWO_DOTS;
        status->frames = 0;
        return TRUE;
    }

    return FALSE;
}

static bool32 BattleAgent_IsEligible(u32 battler)
{
    if (battler >= gBattlersCount
     || !BattlerHasAi(battler)
     || GetBattlerSide(battler) != B_SIDE_OPPONENT
     || !(gBattleTypeFlags & BATTLE_TYPE_TRAINER)
     || (gBattleTypeFlags & (BATTLE_TYPE_DOUBLE | BATTLE_TYPE_MULTI | BATTLE_TYPE_LINK
                           | BATTLE_TYPE_SAFARI | BATTLE_TYPE_PALACE
                           | BATTLE_TYPE_FRONTIER | BATTLE_TYPE_EREADER_TRAINER
                           | BATTLE_TYPE_TRAINER_HILL | BATTLE_TYPE_SECRET_BASE
                           | BATTLE_TYPE_TWO_OPPONENTS))
     || !gTrainers[gTrainerBattleOpponent_A].externalAi
     || gBattleMons[battler].status2 & (STATUS2_MULTIPLETURNS | STATUS2_RECHARGE)
     || gBattleStruct->aiMoveOrAction[battler] >= MAX_MON_MOVES)
        return FALSE;

#if TESTING
    if ((gBattleTypeFlags & BATTLE_TYPE_RECORDED) && !gTestRunnerEnabled)
        return FALSE;
#else
    if (gBattleTypeFlags & BATTLE_TYPE_RECORDED)
        return FALSE;
#endif

    return TRUE;
}

static bool32 BattleAgent_IsLegalSwitch(u32 requester, u8 partySlot)
{
    struct Pokemon *party;
    s32 firstPartySlot;
    s32 lastPartySlot;

    if (requester >= gBattlersCount
     || partySlot >= PARTY_SIZE
     || gBattleMons[requester].status2 & (STATUS2_MULTIPLETURNS | STATUS2_RECHARGE)
     || !CanBattlerEscape(requester))
        return FALSE;

    GetAIPartyIndexes(requester, &firstPartySlot, &lastPartySlot);
    if (partySlot < firstPartySlot || partySlot >= lastPartySlot)
        return FALSE;

    party = GetBattlerParty(requester);
    return partySlot != gBattlerPartyIndexes[requester] && IsValidForBattle(&party[partySlot]);
}

static void BattleAgent_CopyMoveSnapshot(struct BattleAgentMoveSnapshotV3 *snapshotMove, u16 move, u8 pp)
{
    memset(snapshotMove, 0, sizeof(*snapshotMove));
    snapshotMove->move = move;
    snapshotMove->pp = pp;
    if (move != MOVE_NONE)
    {
        snapshotMove->type = gBattleMoves[move].type;
        snapshotMove->power = gBattleMoves[move].power;
        snapshotMove->accuracy = gBattleMoves[move].accuracy;
        snapshotMove->effect = gBattleMoves[move].effect;
        snapshotMove->target = gBattleMoves[move].target;
        snapshotMove->priority = gBattleMoves[move].priority;
        snapshotMove->split = gBattleMoves[move].split;
    }
}

static bool32 BattleAgent_GetSoleLivePlayerTarget(u8 *target)
{
    u32 battler;
    u8 liveTarget = MAX_BATTLERS_COUNT;

    for (battler = 0; battler < gBattlersCount; battler++)
    {
        if (GetBattlerSide(battler) == B_SIDE_PLAYER && IsBattlerAlive(battler))
        {
            if (liveTarget != MAX_BATTLERS_COUNT)
                return FALSE;
            liveTarget = battler;
        }
    }

    if (liveTarget == MAX_BATTLERS_COUNT)
        return FALSE;

    *target = liveTarget;
    return TRUE;
}

static bool32 BattleAgent_NormalizeSingleTarget(u32 requester, u16 move, u8 *target)
{
    u32 moveTarget;

    if (requester >= gBattlersCount || move == MOVE_NONE)
        return FALSE;

    moveTarget = GetBattlerMoveTargetType(requester, move);
    switch (moveTarget)
    {
    case MOVE_TARGET_USER:
    case MOVE_TARGET_USER_OR_SELECTED:
        *target = requester;
        break;
    case MOVE_TARGET_SELECTED:
    case MOVE_TARGET_DEPENDS:
    case MOVE_TARGET_RANDOM:
    case MOVE_TARGET_BOTH:
    case MOVE_TARGET_FOES_AND_ALLY:
    case MOVE_TARGET_OPPONENTS_FIELD:
        if (!BattleAgent_GetSoleLivePlayerTarget(target))
            return FALSE;
        break;
    default:
        return FALSE;
    }

    return *target < gBattlersCount && IsBattlerAlive(*target);
}

static void BattleAgent_CopySnapshot(u32 requester)
{
    u32 battler;
    u32 moveSlot;
    struct BattleAgentSnapshotV3 *snapshot = &gBattleAgentMailbox.snapshot;

    memset(snapshot, 0, sizeof(*snapshot));
    for (battler = 0; battler < gBattlersCount && battler < MAX_BATTLERS_COUNT; battler++)
    {
        struct BattleAgentBattlerSnapshotV3 *snapshotBattler = &snapshot->battlers[battler];

        snapshotBattler->species = gBattleMons[battler].species;
        snapshotBattler->hp = gBattleMons[battler].hp;
        snapshotBattler->maxHp = gBattleMons[battler].maxHP;
        snapshotBattler->status1 = gBattleMons[battler].status1;
        memcpy(snapshotBattler->statStages, gBattleMons[battler].statStages, sizeof(snapshotBattler->statStages));
        snapshotBattler->level = gBattleMons[battler].level;
        snapshotBattler->type1 = gBattleMons[battler].type1;
        snapshotBattler->type2 = gBattleMons[battler].type2;
        snapshotBattler->type3 = gBattleMons[battler].type3;
        snapshotBattler->ability = gBattleMons[battler].ability;
        snapshotBattler->item = gBattleMons[battler].item;
        snapshotBattler->attack = gBattleMons[battler].attack;
        snapshotBattler->defense = gBattleMons[battler].defense;
        snapshotBattler->speed = gBattleMons[battler].speed;
        snapshotBattler->spAttack = gBattleMons[battler].spAttack;
        snapshotBattler->spDefense = gBattleMons[battler].spDefense;
        snapshotBattler->status2 = gBattleMons[battler].status2;
        snapshotBattler->status3 = gStatuses3[battler];

        for (moveSlot = 0; moveSlot < MAX_MON_MOVES; moveSlot++)
        {
            u16 move = gBattleMons[battler].moves[moveSlot];
            BattleAgent_CopyMoveSnapshot(&snapshot->battlerMoves[battler][moveSlot], move, gBattleMons[battler].pp[moveSlot]);
        }
    }

    for (moveSlot = 0; moveSlot < MAX_MON_MOVES; moveSlot++)
    {
        BattleAgent_CopyMoveSnapshot(&snapshot->requesterMoves[moveSlot], gBattleMons[requester].moves[moveSlot], gBattleMons[requester].pp[moveSlot]);
    }

    for (battler = 0; battler < PARTY_SIZE; battler++)
    {
        struct Pokemon *party = GetBattlerParty(requester);
        struct Pokemon *mon = &party[battler];
        struct BattleAgentPartySnapshotV3 *snapshotParty = &snapshot->party[battler];
        u16 species = GetMonData(mon, MON_DATA_SPECIES_OR_EGG);

        snapshotParty->battler.species = species;
        snapshotParty->battler.hp = GetMonData(mon, MON_DATA_HP);
        snapshotParty->battler.maxHp = GetMonData(mon, MON_DATA_MAX_HP);
        snapshotParty->battler.status1 = GetMonData(mon, MON_DATA_STATUS);
        memset(snapshotParty->battler.statStages, DEFAULT_STAT_STAGE, sizeof(snapshotParty->battler.statStages));
        snapshotParty->battler.level = GetMonData(mon, MON_DATA_LEVEL);
        if (species != SPECIES_NONE && species != SPECIES_EGG)
        {
            snapshotParty->battler.type1 = gSpeciesInfo[species].types[0];
            snapshotParty->battler.type2 = gSpeciesInfo[species].types[1];
            snapshotParty->battler.type3 = TYPE_MYSTERY;
            snapshotParty->battler.ability = gSpeciesInfo[species].abilities[GetMonData(mon, MON_DATA_ABILITY_NUM)];
        }
        snapshotParty->battler.item = GetMonData(mon, MON_DATA_HELD_ITEM);
        snapshotParty->battler.attack = GetMonData(mon, MON_DATA_ATK);
        snapshotParty->battler.defense = GetMonData(mon, MON_DATA_DEF);
        snapshotParty->battler.speed = GetMonData(mon, MON_DATA_SPEED);
        snapshotParty->battler.spAttack = GetMonData(mon, MON_DATA_SPATK);
        snapshotParty->battler.spDefense = GetMonData(mon, MON_DATA_SPDEF);
        snapshotParty->isActive = battler == gBattlerPartyIndexes[requester];
        snapshotParty->isUsable = IsValidForBattle(mon);
        for (moveSlot = 0; moveSlot < MAX_MON_MOVES; moveSlot++)
            BattleAgent_CopyMoveSnapshot(&snapshotParty->moves[moveSlot], GetMonData(mon, MON_DATA_MOVE1 + moveSlot), GetMonData(mon, MON_DATA_PP1 + moveSlot));
    }

    snapshot->weather = gBattleWeather;
    snapshot->terrain = gBattleTerrain;
    snapshot->fieldStatuses = gFieldStatuses;
    memcpy(snapshot->sideStatuses, gSideStatuses, sizeof(snapshot->sideStatuses));
}

static void BattleAgent_BuildLegalActions(u32 requester)
{
    u32 moveSlot;
    u8 moveLimitations;

    gBattleAgentMailbox.legalActionCount = 0;
    memset(gBattleAgentMailbox.legalActions, 0, sizeof(gBattleAgentMailbox.legalActions));
    moveLimitations = CheckMoveLimitations(requester, 0, MOVE_LIMITATIONS_ALL);

    for (moveSlot = 0; moveSlot < MAX_MON_MOVES; moveSlot++)
    {
        struct BattleAgentLegalActionV3 *action;
        u16 move = gBattleMons[requester].moves[moveSlot];
        u8 target;

        if (move == MOVE_NONE
         || (moveLimitations & gBitTable[moveSlot])
         || !BattleAgent_NormalizeSingleTarget(requester, move, &target))
            continue;

        if (gBattleAgentMailbox.legalActionCount >= BATTLE_AGENT_MAX_LEGAL_ACTIONS)
            break;

        action = &gBattleAgentMailbox.legalActions[gBattleAgentMailbox.legalActionCount];
        action->actionIndex = gBattleAgentMailbox.legalActionCount;
        action->kind = BATTLE_AGENT_ACTION_KIND_MOVE;
        action->moveSlot = moveSlot;
        action->targetBattler = target;
        action->partySlot = BATTLE_AGENT_ACTION_NONE;
        action->typeEffectiveness = BattleAgent_GetEffectivenessCategory(AI_DATA->effectiveness[requester][target][moveSlot]);
        action->hasStab = IS_BATTLER_OF_TYPE(requester, gBattleMoves[move].type);
        action->canFaintTarget = CanIndexMoveFaintTarget(requester, target, moveSlot, 0);
        gBattleAgentMailbox.legalActionCount++;
    }

    for (moveSlot = 0; moveSlot < PARTY_SIZE && gBattleAgentMailbox.legalActionCount < BATTLE_AGENT_MAX_LEGAL_ACTIONS; moveSlot++)
    {
        struct BattleAgentLegalActionV3 *action;

        if (!BattleAgent_IsLegalSwitch(requester, moveSlot))
            continue;

        action = &gBattleAgentMailbox.legalActions[gBattleAgentMailbox.legalActionCount];
        action->actionIndex = gBattleAgentMailbox.legalActionCount;
        action->kind = BATTLE_AGENT_ACTION_KIND_SWITCH;
        action->moveSlot = BATTLE_AGENT_ACTION_NONE;
        action->targetBattler = BATTLE_AGENT_ACTION_NONE;
        action->partySlot = moveSlot;
        gBattleAgentMailbox.legalActionCount++;
    }
}

static void BattleAgent_CommitRequest(void)
{
    // ARM GCC honors this memory clobber as a compiler barrier before the volatile commit store.
    asm volatile("" ::: "memory");
    *(volatile u8 *)&gBattleAgentMailbox.requestStatus = BATTLE_AGENT_REQUEST_PENDING;
}

static void BattleAgent_BeginRequest(void)
{
    *(volatile u8 *)&gBattleAgentMailbox.requestStatus = BATTLE_AGENT_REQUEST_IDLE;
    asm volatile("" ::: "memory");
}

static void BattleAgent_ClearResponse(void)
{
    gBattleAgentMailbox.responseStatus = BATTLE_AGENT_RESPONSE_NONE;
    gBattleAgentMailbox.responseSequence = 0;
    gBattleAgentMailbox.responseLegalActionIndex = 0;
}

void BattleAgent_ResetMailbox(void)
{
    u32 battler;

    for (battler = 0; battler < MAX_BATTLERS_COUNT; battler++)
        BattleAgent_ClearThinkingStatus(battler);
    memset(&gBattleAgentMailbox, 0, sizeof(gBattleAgentMailbox));
    memset(sBattleAgentWaitStates, 0, sizeof(sBattleAgentWaitStates));
    gBattleAgentMailbox.magic = BATTLE_AGENT_PROTOCOL_MAGIC;
    gBattleAgentMailbox.protocolVersion = BATTLE_AGENT_PROTOCOL_VERSION;
    BattleAgent_BeginRequest();
    BattleAgent_ClearResponse();
}

bool32 BattleAgent_TryPublishRequest(u32 battler)
{
    if (!BattleAgent_IsEligible(battler))
        return FALSE;

    if (gBattleAgentMailbox.magic != BATTLE_AGENT_PROTOCOL_MAGIC
     || gBattleAgentMailbox.protocolVersion != BATTLE_AGENT_PROTOCOL_VERSION)
    {
        BattleAgent_ResetMailbox();
    }

    BattleAgent_BeginRequest();
    BattleAgent_ClearResponse();
    BattleAgent_CopySnapshot(battler);
    BattleAgent_BuildLegalActions(battler);

    gBattleAgentMailbox.requestSequence++;
    if (gBattleAgentMailbox.requestSequence == 0)
        gBattleAgentMailbox.requestSequence = 1;

    gBattleAgentMailbox.requestingBattler = battler;
    gBattleAgentMailbox.battleMode = BATTLE_AGENT_BATTLE_MODE_TRAINER_SINGLE;
    gBattleAgentMailbox.turnSequence++;
    if (gBattleAgentMailbox.turnSequence == 0)
        gBattleAgentMailbox.turnSequence = 1;

    BattleAgent_CommitRequest();
    return TRUE;
}

bool32 BattleAgent_BeginExternalWait(u32 battler)
{
    struct BattleAgentWaitState *waitState;

    if (battler >= MAX_BATTLERS_COUNT || !BattleAgent_TryPublishRequest(battler) || gBattleAgentMailbox.legalActionCount == 0)
        return FALSE;

    waitState = &sBattleAgentWaitStates[battler];
    waitState->sequence = gBattleAgentMailbox.requestSequence;
    waitState->frames = 0;
    waitState->fallbackMoveOrAction = gBattleStruct->aiMoveOrAction[battler];
    waitState->fallbackTarget = gBattleStruct->aiChosenTarget[battler];
    waitState->active = TRUE;
#if TESTING
    TestRunner_Battle_InjectBattleAgentResponse(battler);
#endif
    return TRUE;
}

void BattleAgent_UpdateThinkingStatus(u32 battler, bool32 playerActionConfirmed)
{
    if (BattleAgent_UpdateThinkingStatusState(battler, playerActionConfirmed, !IsTextPrinterActive(B_WIN_MSG)))
    {
        gBattle_BG0_X = 0;
        gBattle_BG0_Y = 0;
        BattleAgent_RenderThinkingStatus(battler);
    }
}

void BattleAgent_ClearThinkingStatus(u32 battler)
{
    struct BattleAgentThinkingStatusState *status;

    if (battler >= MAX_BATTLERS_COUNT)
        return;

    status = &sBattleAgentThinkingStatuses[battler];
    if (status->ownsMessageWindow)
        BattlePutTextOnWindow(gText_EmptyString3, B_WIN_MSG);
    memset(status, 0, sizeof(*status));
}

bool32 BattleAgent_TryConsumeResponse(u32 battler)
{
    struct BattleAgentWaitState *waitState;
    struct BattleAgentLegalActionV3 *action;
    u8 target;
    u16 move;
    u8 moveLimitations;

    if (battler >= MAX_BATTLERS_COUNT)
        return FALSE;

    waitState = &sBattleAgentWaitStates[battler];
    if (!waitState->active || gBattleAgentMailbox.responseStatus != BATTLE_AGENT_RESPONSE_READY)
        return FALSE;

    if (gBattleAgentMailbox.requestStatus != BATTLE_AGENT_REQUEST_PENDING
     || gBattleAgentMailbox.responseSequence != waitState->sequence
     || gBattleAgentMailbox.responseLegalActionIndex >= gBattleAgentMailbox.legalActionCount)
    {
        BattleAgent_ClearResponse();
        return FALSE;
    }

    action = &gBattleAgentMailbox.legalActions[gBattleAgentMailbox.responseLegalActionIndex];
    if (action->kind == BATTLE_AGENT_ACTION_KIND_MOVE)
    {
        if (action->moveSlot >= MAX_MON_MOVES
         || action->partySlot != BATTLE_AGENT_ACTION_NONE)
        {
            BattleAgent_ClearResponse();
            return FALSE;
        }

        move = gBattleMons[battler].moves[action->moveSlot];
        moveLimitations = CheckMoveLimitations(battler, 0, MOVE_LIMITATIONS_ALL);
        if (move == MOVE_NONE
         || (moveLimitations & gBitTable[action->moveSlot])
         || !BattleAgent_NormalizeSingleTarget(battler, move, &target)
         || target != action->targetBattler)
        {
            BattleAgent_ClearResponse();
            return FALSE;
        }

        gBattleStruct->aiMoveOrAction[battler] = action->moveSlot;
        gBattleStruct->aiChosenTarget[battler] = target;
    }
    else if (action->kind == BATTLE_AGENT_ACTION_KIND_SWITCH)
    {
        if (action->moveSlot != BATTLE_AGENT_ACTION_NONE
         || action->targetBattler != BATTLE_AGENT_ACTION_NONE
         || !BattleAgent_IsLegalSwitch(battler, action->partySlot))
        {
            BattleAgent_ClearResponse();
            return FALSE;
        }

        gBattleStruct->aiMoveOrAction[battler] = AI_CHOICE_SWITCH;
        gBattleStruct->AI_monToSwitchIntoId[battler] = action->partySlot;
    }
    else
    {
        BattleAgent_ClearResponse();
        return FALSE;
    }

    waitState->active = FALSE;
    waitState->hasAcceptedAction = TRUE;
    BattleAgent_ClearThinkingStatus(battler);
    BattleAgent_ClearResponse();
    return TRUE;
}

bool32 BattleAgent_IsWaitExpired(u32 battler)
{
    if (battler >= MAX_BATTLERS_COUNT || !sBattleAgentWaitStates[battler].active)
        return FALSE;

    return ++sBattleAgentWaitStates[battler].frames >= BATTLE_AGENT_RESPONSE_TIMEOUT_FRAMES;
}

void BattleAgent_UseVanillaFallback(u32 battler)
{
    struct BattleAgentWaitState *waitState;

    if (battler >= MAX_BATTLERS_COUNT)
        return;

    waitState = &sBattleAgentWaitStates[battler];
    if (!waitState->active)
        return;

    gBattleStruct->aiMoveOrAction[battler] = waitState->fallbackMoveOrAction;
    gBattleStruct->aiChosenTarget[battler] = waitState->fallbackTarget;
    waitState->active = FALSE;
    waitState->hasAcceptedAction = FALSE;
    BattleAgent_ClearThinkingStatus(battler);
    BattleAgent_ClearResponse();
}

bool32 BattleAgent_TryEmitAcceptedAction(u32 battler)
{
    struct BattleAgentWaitState *waitState;

    if (battler >= MAX_BATTLERS_COUNT)
        return FALSE;

    waitState = &sBattleAgentWaitStates[battler];
    if (!waitState->hasAcceptedAction)
        return FALSE;

    waitState->hasAcceptedAction = FALSE;
    if (gBattleStruct->aiMoveOrAction[battler] == AI_CHOICE_SWITCH)
        BtlController_EmitTwoReturnValues(battler, BUFFER_B, B_ACTION_SWITCH, 0);
    else
        BtlController_EmitTwoReturnValues(battler, BUFFER_B, B_ACTION_USE_MOVE, gBattleStruct->aiChosenTarget[battler] << 8);
    return TRUE;
}

#if TESTING
bool32 BattleAgent_TestNormalizeSingleTarget(u32 requester, u16 move, u8 *target)
{
    return BattleAgent_NormalizeSingleTarget(requester, move, target);
}

void BattleAgent_TestStartThinkingStatus(u32 battler)
{
    if (battler >= MAX_BATTLERS_COUNT)
        return;

    memset(&sBattleAgentThinkingStatuses[battler], 0, sizeof(sBattleAgentThinkingStatuses[battler]));
    sBattleAgentWaitStates[battler].active = TRUE;
}

void BattleAgent_TestUpdateThinkingStatus(u32 battler, bool32 playerActionConfirmed, bool32 messageWindowIdle)
{
    BattleAgent_UpdateThinkingStatusState(battler, playerActionConfirmed, messageWindowIdle);
}

u8 BattleAgent_TestGetThinkingStatus(u32 battler)
{
    if (battler >= MAX_BATTLERS_COUNT)
        return BATTLE_AGENT_THINKING_HIDDEN;

    return sBattleAgentThinkingStatuses[battler].displayState;
}

u8 BattleAgent_TestGetThinkingStatusFrames(u32 battler)
{
    if (battler >= MAX_BATTLERS_COUNT)
        return 0;

    return sBattleAgentThinkingStatuses[battler].frames;
}
#endif
