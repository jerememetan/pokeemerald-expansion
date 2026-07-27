#include "global.h"
#include "battle_agent.h"
#include "battle_ai_util.h"
#include "battle_setup.h"
#include "battle_util.h"
#include "data.h"
#include "util.h"

#if TESTING
#include "test_runner.h"
#endif

EWRAM_DATA struct BattleAgentMailboxV1 gBattleAgentMailbox;

static bool32 BattleAgent_IsEligible(u32 battler);
static bool32 BattleAgent_NormalizeSingleTarget(u32 requester, u16 move, u8 *target);
static void BattleAgent_CopySnapshot(u32 requester);
static void BattleAgent_BuildLegalActions(u32 requester);
static void BattleAgent_BeginRequest(void);
static void BattleAgent_CommitRequest(void);

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
    struct BattleAgentSnapshotV1 *snapshot = &gBattleAgentMailbox.snapshot;

    memset(snapshot, 0, sizeof(*snapshot));
    for (battler = 0; battler < gBattlersCount && battler < MAX_BATTLERS_COUNT; battler++)
    {
        snapshot->battlers[battler].species = gBattleMons[battler].species;
        snapshot->battlers[battler].hp = gBattleMons[battler].hp;
        snapshot->battlers[battler].maxHp = gBattleMons[battler].maxHP;
        snapshot->battlers[battler].status1 = gBattleMons[battler].status1;
        memcpy(snapshot->battlers[battler].statStages, gBattleMons[battler].statStages, sizeof(snapshot->battlers[battler].statStages));
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
        struct BattleAgentLegalActionV1 *action;
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

void BattleAgent_ResetMailbox(void)
{
    memset(&gBattleAgentMailbox, 0, sizeof(gBattleAgentMailbox));
    gBattleAgentMailbox.magic = BATTLE_AGENT_PROTOCOL_MAGIC;
    gBattleAgentMailbox.protocolVersion = BATTLE_AGENT_PROTOCOL_VERSION;
    BattleAgent_BeginRequest();
    gBattleAgentMailbox.responseStatus = BATTLE_AGENT_RESPONSE_NONE;
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
    gBattleAgentMailbox.responseStatus = BATTLE_AGENT_RESPONSE_NONE;
    gBattleAgentMailbox.responseSequence = 0;
    gBattleAgentMailbox.responseLegalActionIndex = 0;
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

#if TESTING
bool32 BattleAgent_TestNormalizeSingleTarget(u32 requester, u16 move, u8 *target)
{
    return BattleAgent_NormalizeSingleTarget(requester, move, target);
}
#endif
