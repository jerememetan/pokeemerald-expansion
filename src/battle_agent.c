#include "global.h"
#include "battle_agent.h"
#include "battle_ai_util.h"
#include "battle_message.h"
#include "battle_setup.h"
#include "battle_util.h"
#include "constants/battle_ai.h"
#include "data.h"
#include "text.h"
#include "util.h"

#if TESTING
#include "test_runner.h"
#endif

EWRAM_DATA struct BattleAgentMailboxV2 gBattleAgentMailbox;

struct BattleAgentWaitState
{
    u32 sequence;
    u16 frames;
    u8 fallbackMoveOrAction;
    u8 fallbackTarget;
    bool8 active;
};

static EWRAM_DATA struct BattleAgentWaitState sBattleAgentWaitStates[MAX_BATTLERS_COUNT];

struct BattleAgentThinkingStatusState
{
    u8 displayState;
    u8 frames;
    bool8 ownsMessageWindow;
};

static EWRAM_DATA struct BattleAgentThinkingStatusState sBattleAgentThinkingStatuses[MAX_BATTLERS_COUNT];

static const u8 sText_AiThinking[] = _("AI is thinking");
static const u8 sText_AiThinkingOneDot[] = _("AI is thinking.");
static const u8 sText_AiThinkingTwoDots[] = _("AI is thinking..");
static const u8 sText_AiThinkingThreeDots[] = _("AI is thinking...");

static bool32 BattleAgent_IsEligible(u32 battler);
static bool32 BattleAgent_NormalizeSingleTarget(u32 requester, u16 move, u8 *target);
static void BattleAgent_CopySnapshot(u32 requester);
static void BattleAgent_BuildLegalActions(u32 requester);
static void BattleAgent_BeginRequest(void);
static void BattleAgent_CommitRequest(void);
static void BattleAgent_ClearResponse(void);
static const u8 *BattleAgent_GetThinkingText(u8 displayState);
static bool32 BattleAgent_UpdateThinkingStatusState(u32 battler, bool32 playerActionConfirmed, bool32 messageWindowIdle);

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
    switch (displayState)
    {
    case BATTLE_AGENT_THINKING_THREE_DOTS:
        return sText_AiThinkingThreeDots;
    case BATTLE_AGENT_THINKING_NO_DOTS:
        return sText_AiThinking;
    case BATTLE_AGENT_THINKING_ONE_DOT:
        return sText_AiThinkingOneDot;
    case BATTLE_AGENT_THINKING_TWO_DOTS:
        return sText_AiThinkingTwoDots;
    default:
        return gText_EmptyString3;
    }
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
        status->displayState = BATTLE_AGENT_THINKING_THREE_DOTS;
        status->frames = 0;
        return TRUE;
    }

    if (!messageWindowIdle || ++status->frames < BATTLE_AGENT_THINKING_DOT_INTERVAL)
        return FALSE;

    status->frames = 0;
    switch (status->displayState)
    {
    case BATTLE_AGENT_THINKING_THREE_DOTS:
        status->displayState = BATTLE_AGENT_THINKING_NO_DOTS;
        break;
    case BATTLE_AGENT_THINKING_NO_DOTS:
        status->displayState = BATTLE_AGENT_THINKING_ONE_DOT;
        break;
    case BATTLE_AGENT_THINKING_ONE_DOT:
        status->displayState = BATTLE_AGENT_THINKING_TWO_DOTS;
        break;
    default:
        status->displayState = BATTLE_AGENT_THINKING_THREE_DOTS;
        break;
    }
    return TRUE;
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
    struct BattleAgentSnapshotV2 *snapshot = &gBattleAgentMailbox.snapshot;

    memset(snapshot, 0, sizeof(*snapshot));
    for (battler = 0; battler < gBattlersCount && battler < MAX_BATTLERS_COUNT; battler++)
    {
        struct BattleAgentBattlerSnapshotV2 *snapshotBattler = &snapshot->battlers[battler];

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
            struct BattleAgentMoveSnapshotV2 *snapshotMove = &snapshot->battlerMoves[battler][moveSlot];

            snapshotMove->move = move;
            snapshotMove->pp = gBattleMons[battler].pp[moveSlot];
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
    }

    for (moveSlot = 0; moveSlot < MAX_MON_MOVES; moveSlot++)
    {
        snapshot->requesterMoves[moveSlot].move = gBattleMons[requester].moves[moveSlot];
        snapshot->requesterMoves[moveSlot].pp = gBattleMons[requester].pp[moveSlot];
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
        struct BattleAgentLegalActionV2 *action;
        u16 move = gBattleMons[requester].moves[moveSlot];
        u8 target;

        if (move == MOVE_NONE
         || (moveLimitations & gBitTable[moveSlot])
         || !BattleAgent_NormalizeSingleTarget(requester, move, &target))
            continue;

        if (gBattleAgentMailbox.legalActionCount >= MAX_MON_MOVES)
            break;

        action = &gBattleAgentMailbox.legalActions[gBattleAgentMailbox.legalActionCount];
        action->actionIndex = gBattleAgentMailbox.legalActionCount;
        action->moveSlot = moveSlot;
        action->targetBattler = target;
        action->reserved = 0;
        action->typeEffectiveness = BattleAgent_GetEffectivenessCategory(AI_DATA->effectiveness[requester][target][moveSlot]);
        action->hasStab = IS_BATTLER_OF_TYPE(requester, gBattleMoves[move].type);
        action->canFaintTarget = CanIndexMoveFaintTarget(requester, target, moveSlot, 0);
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
        BattlePutTextOnWindow(BattleAgent_GetThinkingText(sBattleAgentThinkingStatuses[battler].displayState), B_WIN_MSG);
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
    struct BattleAgentLegalActionV2 *action;
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
    if (action->moveSlot >= MAX_MON_MOVES)
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
    waitState->active = FALSE;
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
    BattleAgent_ClearThinkingStatus(battler);
    BattleAgent_ClearResponse();
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
