#include "global.h"
#include "battle_agent.h"
#include "battle_ai_main.h"
#include "battle_ai_switch_items.h"
#include "battle_ai_util.h"
#include "battle_anim.h"
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

EWRAM_DATA struct BattleAgentMailboxV4 gBattleAgentMailbox;

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
static bool32 BattleAgent_IsBaseEligible(u32 battler);
static bool32 BattleAgent_IsTwoTrainerBattlerConfigured(u32 battler);
static bool32 BattleAgent_IsTwoTrainerBattlerEligible(u32 battler);
static bool32 BattleAgent_IsCoordinatedDoubleBattle(void);
static u32 BattleAgent_GetDoublePartner(u32 battler);
static bool32 BattleAgent_NormalizeSingleTarget(u32 requester, u16 move, u8 *target);
static bool32 BattleAgent_IsLegalSwitch(u32 requester, u8 partySlot);
static void BattleAgent_CopySnapshot(u32 requester);
static void BattleAgent_BuildLegalActions(u32 requester, u8 actionListIndex, bool32 isDouble);
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

static bool32 BattleAgent_IsBaseEligible(u32 battler)
{
    if (battler >= gBattlersCount
     || !BattlerHasAi(battler)
     || GetBattlerSide(battler) != B_SIDE_OPPONENT
     || !(gBattleTypeFlags & BATTLE_TYPE_TRAINER)
     || (gBattleTypeFlags & (BATTLE_TYPE_MULTI | BATTLE_TYPE_LINK
                           | BATTLE_TYPE_SAFARI | BATTLE_TYPE_PALACE
                           | BATTLE_TYPE_FRONTIER | BATTLE_TYPE_EREADER_TRAINER
                           | BATTLE_TYPE_TRAINER_HILL | BATTLE_TYPE_SECRET_BASE
                           | BATTLE_TYPE_TWO_OPPONENTS | BATTLE_TYPE_INGAME_PARTNER))
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

static bool32 BattleAgent_IsTwoTrainerBattlerConfigured(u32 battler)
{
    if (battler >= gBattlersCount
     || !BattlerHasAi(battler)
     || GetBattlerSide(battler) != B_SIDE_OPPONENT
     || !(gBattleTypeFlags & BATTLE_TYPE_TRAINER)
     || !(gBattleTypeFlags & BATTLE_TYPE_TWO_OPPONENTS)
     || (gBattleTypeFlags & (BATTLE_TYPE_MULTI | BATTLE_TYPE_LINK
                           | BATTLE_TYPE_SAFARI | BATTLE_TYPE_PALACE
                           | BATTLE_TYPE_FRONTIER | BATTLE_TYPE_EREADER_TRAINER
                           | BATTLE_TYPE_TRAINER_HILL | BATTLE_TYPE_SECRET_BASE
                           | BATTLE_TYPE_INGAME_PARTNER))
     || !gTrainers[gTrainerBattleOpponent_A].externalAi
     || !gTrainers[gTrainerBattleOpponent_B].externalAi)
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

static bool32 BattleAgent_IsTwoTrainerBattlerEligible(u32 battler)
{
    return BattleAgent_IsTwoTrainerBattlerConfigured(battler)
        && !(gBattleMons[battler].status2 & (STATUS2_MULTIPLETURNS | STATUS2_RECHARGE))
        && gBattleStruct->aiMoveOrAction[battler] < MAX_MON_MOVES;
}

static bool32 BattleAgent_IsEligible(u32 battler)
{
    return BattleAgent_IsBaseEligible(battler)
        && !(gBattleTypeFlags & BATTLE_TYPE_DOUBLE);
}

static u32 BattleAgent_GetDoublePartner(u32 battler)
{
    return GetBattlerAtPosition(BATTLE_PARTNER(GetBattlerPosition(battler)));
}

static bool32 BattleAgent_IsCoordinatedDoubleBattle(void)
{
    u32 left = GetBattlerAtPosition(B_POSITION_OPPONENT_LEFT);
    u32 right = GetBattlerAtPosition(B_POSITION_OPPONENT_RIGHT);

    if (!(gBattleTypeFlags & BATTLE_TYPE_DOUBLE)
     || gBattlersCount != MAX_BATTLERS_COUNT
     || gBattleTypeFlags & BATTLE_TYPE_INGAME_PARTNER
     || left >= gBattlersCount
     || right >= gBattlersCount
     || !IsBattlerAlive(left)
     || !IsBattlerAlive(right))
        return FALSE;

    if (gBattleTypeFlags & BATTLE_TYPE_TWO_OPPONENTS)
        return BattleAgent_IsTwoTrainerBattlerEligible(left)
            && BattleAgent_IsTwoTrainerBattlerEligible(right);

    return BattleAgent_IsBaseEligible(left)
        && BattleAgent_IsBaseEligible(right);
}

bool32 BattleAgent_IsFirstCoordinatedDoubleBattler(u32 battler)
{
    u32 left = GetBattlerAtPosition(B_POSITION_OPPONENT_LEFT);
    u32 right = GetBattlerAtPosition(B_POSITION_OPPONENT_RIGHT);

    if (battler != left)
        return FALSE;

    // The battle loop evaluates the left opponent before calculating the right
    // opponent's vanilla action. Hold the left side here so the right side can
    // publish one atomic request after both actions are available.
    if (gBattleTypeFlags & BATTLE_TYPE_TWO_OPPONENTS)
    {
        return (gBattleTypeFlags & BATTLE_TYPE_DOUBLE)
            && gBattlersCount == MAX_BATTLERS_COUNT
            && !(gBattleTypeFlags & BATTLE_TYPE_INGAME_PARTNER)
            && left < gBattlersCount
            && right < gBattlersCount
            && IsBattlerAlive(left)
            && IsBattlerAlive(right)
            && BattleAgent_IsTwoTrainerBattlerConfigured(left)
            && BattleAgent_IsTwoTrainerBattlerConfigured(right);
    }

    return BattleAgent_IsCoordinatedDoubleBattle();
}

static bool32 BattleAgent_IsLegalSwitch(u32 requester, u8 partySlot)
{
    struct Pokemon *party;
    s32 firstPartySlot;
    s32 lastPartySlot;
    u32 partner;

    if (requester >= gBattlersCount
     || partySlot >= PARTY_SIZE
     || gBattleMons[requester].status2 & (STATUS2_MULTIPLETURNS | STATUS2_RECHARGE)
     || !CanBattlerEscape(requester))
        return FALSE;

    GetAIPartyIndexes(requester, &firstPartySlot, &lastPartySlot);
    if (partySlot < firstPartySlot || partySlot >= lastPartySlot)
        return FALSE;

    partner = BattleAgent_GetDoublePartner(requester);
    party = GetBattlerParty(requester);
    return partySlot != gBattlerPartyIndexes[requester]
        && (!(gBattleTypeFlags & BATTLE_TYPE_DOUBLE) || partner >= gBattlersCount || partySlot != gBattlerPartyIndexes[partner])
        && IsValidForBattle(&party[partySlot]);
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
        if (gBattleTypeFlags & BATTLE_TYPE_TWO_OPPONENTS)
        {
            u32 ownerBattler = battler < PARTY_SIZE / 2
                ? GetBattlerAtPosition(B_POSITION_OPPONENT_LEFT)
                : GetBattlerAtPosition(B_POSITION_OPPONENT_RIGHT);

            snapshotParty->isActive = battler == gBattlerPartyIndexes[ownerBattler];
            snapshotParty->ownerBattler = ownerBattler;
        }
        else
        {
            snapshotParty->isActive = battler == gBattlerPartyIndexes[requester];
            snapshotParty->ownerBattler = BATTLE_AGENT_ACTION_NONE;
        }
        snapshotParty->isUsable = IsValidForBattle(mon);
        for (moveSlot = 0; moveSlot < MAX_MON_MOVES; moveSlot++)
            BattleAgent_CopyMoveSnapshot(&snapshotParty->moves[moveSlot], GetMonData(mon, MON_DATA_MOVE1 + moveSlot), GetMonData(mon, MON_DATA_PP1 + moveSlot));
    }

    snapshot->weather = gBattleWeather;
    snapshot->terrain = gBattleTerrain;
    snapshot->fieldStatuses = gFieldStatuses;
    memcpy(snapshot->sideStatuses, gSideStatuses, sizeof(snapshot->sideStatuses));
}

static bool32 BattleAgent_AddMoveAction(u32 requester, u8 actionListIndex, u16 move, u8 moveSlot, u8 target)
{
    struct BattleAgentLegalActionV4 *action;
    u8 *actionCount = &gBattleAgentMailbox.legalActionCounts[actionListIndex];

    if (*actionCount >= BATTLE_AGENT_MAX_ACTIONS_PER_BATTLER)
        return FALSE;

    action = &gBattleAgentMailbox.legalActions[actionListIndex][*actionCount];
    action->actorBattler = requester;
    action->actionIndex = *actionCount;
    action->kind = BATTLE_AGENT_ACTION_KIND_MOVE;
    action->moveSlot = moveSlot;
    action->targetBattler = target;
    action->partySlot = BATTLE_AGENT_ACTION_NONE;
    if (target == BATTLE_AGENT_ACTION_NONE)
    {
        action->typeEffectiveness = 2;
        action->hasStab = IS_BATTLER_OF_TYPE(requester, gBattleMoves[move].type);
        action->canFaintTarget = FALSE;
    }
    else
    {
        action->typeEffectiveness = BattleAgent_GetEffectivenessCategory(AI_DATA->effectiveness[requester][target][moveSlot]);
        action->hasStab = IS_BATTLER_OF_TYPE(requester, gBattleMoves[move].type);
        action->canFaintTarget = CanIndexMoveFaintTarget(requester, target, moveSlot, 0);
    }
    (*actionCount)++;
    return TRUE;
}

static void BattleAgent_BuildLegalActions(u32 requester, u8 actionListIndex, bool32 isDouble)
{
    u32 moveSlot;
    u8 moveLimitations;

    gBattleAgentMailbox.legalActionCounts[actionListIndex] = 0;
    memset(gBattleAgentMailbox.legalActions[actionListIndex], 0, sizeof(gBattleAgentMailbox.legalActions[actionListIndex]));
    moveLimitations = CheckMoveLimitations(requester, 0, MOVE_LIMITATIONS_ALL);

    for (moveSlot = 0; moveSlot < MAX_MON_MOVES; moveSlot++)
    {
        u16 move = gBattleMons[requester].moves[moveSlot];
        u8 target;

        if (move == MOVE_NONE || (moveLimitations & gBitTable[moveSlot]))
            continue;

        if (!isDouble)
        {
            if (BattleAgent_NormalizeSingleTarget(requester, move, &target))
                BattleAgent_AddMoveAction(requester, actionListIndex, move, moveSlot, target);
        }
        else
        {
            u32 targetBattler;
            u32 moveTarget = GetBattlerMoveTargetType(requester, move);

            if (moveTarget == MOVE_TARGET_USER || moveTarget == MOVE_TARGET_USER_OR_SELECTED)
                BattleAgent_AddMoveAction(requester, actionListIndex, move, moveSlot, requester);
            else if (moveTarget == MOVE_TARGET_ALLY)
                BattleAgent_AddMoveAction(requester, actionListIndex, move, moveSlot, BattleAgent_GetDoublePartner(requester));
            else if (moveTarget == MOVE_TARGET_SELECTED || moveTarget == MOVE_TARGET_DEPENDS || moveTarget == MOVE_TARGET_RANDOM)
            {
                for (targetBattler = 0; targetBattler < gBattlersCount; targetBattler++)
                {
                    if (GetBattlerSide(targetBattler) != GetBattlerSide(requester) && IsBattlerAlive(targetBattler))
                        BattleAgent_AddMoveAction(requester, actionListIndex, move, moveSlot, targetBattler);
                }
            }
            else
            {
                BattleAgent_AddMoveAction(requester, actionListIndex, move, moveSlot, BATTLE_AGENT_ACTION_NONE);
            }
        }
    }

    for (moveSlot = 0; moveSlot < PARTY_SIZE && gBattleAgentMailbox.legalActionCounts[actionListIndex] < BATTLE_AGENT_MAX_ACTIONS_PER_BATTLER; moveSlot++)
    {
        struct BattleAgentLegalActionV4 *action;

        if (!BattleAgent_IsLegalSwitch(requester, moveSlot))
            continue;

        action = &gBattleAgentMailbox.legalActions[actionListIndex][gBattleAgentMailbox.legalActionCounts[actionListIndex]];
        action->actorBattler = requester;
        action->actionIndex = gBattleAgentMailbox.legalActionCounts[actionListIndex];
        action->kind = BATTLE_AGENT_ACTION_KIND_SWITCH;
        action->moveSlot = BATTLE_AGENT_ACTION_NONE;
        action->targetBattler = BATTLE_AGENT_ACTION_NONE;
        action->partySlot = moveSlot;
        gBattleAgentMailbox.legalActionCounts[actionListIndex]++;
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
    gBattleAgentMailbox.responseActionCount = 0;
    gBattleAgentMailbox.responseBattlers[0] = BATTLE_AGENT_ACTION_NONE;
    gBattleAgentMailbox.responseBattlers[1] = BATTLE_AGENT_ACTION_NONE;
    gBattleAgentMailbox.responseActionIndexes[0] = BATTLE_AGENT_ACTION_NONE;
    gBattleAgentMailbox.responseActionIndexes[1] = BATTLE_AGENT_ACTION_NONE;
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
    if (!BattleAgent_IsEligible(battler)
     && (!BattleAgent_IsCoordinatedDoubleBattle() || GetBattlerSide(battler) != B_SIDE_OPPONENT))
        return FALSE;

    if (gBattleAgentMailbox.magic != BATTLE_AGENT_PROTOCOL_MAGIC
     || gBattleAgentMailbox.protocolVersion != BATTLE_AGENT_PROTOCOL_VERSION)
    {
        BattleAgent_ResetMailbox();
    }

    BattleAgent_BeginRequest();
    BattleAgent_ClearResponse();
    BattleAgent_CopySnapshot(battler);

    gBattleAgentMailbox.requestSequence++;
    if (gBattleAgentMailbox.requestSequence == 0)
        gBattleAgentMailbox.requestSequence = 1;

    if (BattleAgent_IsCoordinatedDoubleBattle())
    {
        u32 left = GetBattlerAtPosition(B_POSITION_OPPONENT_LEFT);
        u32 right = GetBattlerAtPosition(B_POSITION_OPPONENT_RIGHT);

        gBattleAgentMailbox.battleMode = (gBattleTypeFlags & BATTLE_TYPE_TWO_OPPONENTS)
            ? BATTLE_AGENT_BATTLE_MODE_TRAINER_TWO_OPPONENT_DOUBLE
            : BATTLE_AGENT_BATTLE_MODE_TRAINER_DOUBLE;
        gBattleAgentMailbox.controlledBattlerCount = 2;
        gBattleAgentMailbox.battlerCount = MAX_BATTLERS_COUNT;
        gBattleAgentMailbox.controlledBattlers[0] = left;
        gBattleAgentMailbox.controlledBattlers[1] = right;
        BattleAgent_BuildLegalActions(left, 0, TRUE);
        BattleAgent_BuildLegalActions(right, 1, TRUE);
    }
    else
    {
        gBattleAgentMailbox.battleMode = BATTLE_AGENT_BATTLE_MODE_TRAINER_SINGLE;
        gBattleAgentMailbox.controlledBattlerCount = 1;
        gBattleAgentMailbox.battlerCount = 2;
        gBattleAgentMailbox.controlledBattlers[0] = battler;
        gBattleAgentMailbox.controlledBattlers[1] = BATTLE_AGENT_ACTION_NONE;
        BattleAgent_BuildLegalActions(battler, 0, FALSE);
        gBattleAgentMailbox.legalActionCounts[1] = 0;
    }
    gBattleAgentMailbox.turnSequence++;
    if (gBattleAgentMailbox.turnSequence == 0)
        gBattleAgentMailbox.turnSequence = 1;

    BattleAgent_CommitRequest();
    return TRUE;
}

bool32 BattleAgent_BeginExternalWait(u32 battler)
{
    struct BattleAgentWaitState *waitState;
    u32 controlledIndex;

    if (battler >= MAX_BATTLERS_COUNT || !BattleAgent_TryPublishRequest(battler))
        return FALSE;

    for (controlledIndex = 0; controlledIndex < gBattleAgentMailbox.controlledBattlerCount; controlledIndex++)
    {
        u32 controlledBattler = gBattleAgentMailbox.controlledBattlers[controlledIndex];

        if (gBattleAgentMailbox.legalActionCounts[controlledIndex] == 0)
            return FALSE;
        waitState = &sBattleAgentWaitStates[controlledBattler];
        waitState->sequence = gBattleAgentMailbox.requestSequence;
        waitState->frames = 0;
        waitState->fallbackMoveOrAction = gBattleStruct->aiMoveOrAction[controlledBattler];
        waitState->fallbackTarget = gBattleStruct->aiChosenTarget[controlledBattler];
        waitState->active = TRUE;
        waitState->hasAcceptedAction = FALSE;
    }

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
    u8 selectedActionIndexes[BATTLE_AGENT_MAX_CONTROLLED_BATTLERS];
    u32 controlledIndex;
    u32 responseIndex;

    if (battler >= MAX_BATTLERS_COUNT)
        return FALSE;

    waitState = &sBattleAgentWaitStates[battler];
    if (waitState->hasAcceptedAction)
        return TRUE;

    if (!waitState->active || gBattleAgentMailbox.responseStatus != BATTLE_AGENT_RESPONSE_READY)
        return FALSE;

    if (gBattleAgentMailbox.requestStatus != BATTLE_AGENT_REQUEST_PENDING
     || gBattleAgentMailbox.responseSequence != waitState->sequence
     || gBattleAgentMailbox.responseActionCount != gBattleAgentMailbox.controlledBattlerCount)
    {
        BattleAgent_ClearResponse();
        return FALSE;
    }

    for (controlledIndex = 0; controlledIndex < gBattleAgentMailbox.controlledBattlerCount; controlledIndex++)
    {
        bool32 found = FALSE;

        for (responseIndex = 0; responseIndex < gBattleAgentMailbox.responseActionCount; responseIndex++)
        {
            if (gBattleAgentMailbox.responseBattlers[responseIndex] == gBattleAgentMailbox.controlledBattlers[controlledIndex])
            {
                if (found || gBattleAgentMailbox.responseActionIndexes[responseIndex] >= gBattleAgentMailbox.legalActionCounts[controlledIndex])
                {
                    BattleAgent_ClearResponse();
                    return FALSE;
                }
                selectedActionIndexes[controlledIndex] = gBattleAgentMailbox.responseActionIndexes[responseIndex];
                found = TRUE;
            }
        }
        if (!found)
        {
            BattleAgent_ClearResponse();
            return FALSE;
        }
    }

    for (controlledIndex = 0; controlledIndex < gBattleAgentMailbox.controlledBattlerCount; controlledIndex++)
    {
        u32 controlledBattler = gBattleAgentMailbox.controlledBattlers[controlledIndex];
        struct BattleAgentLegalActionV4 *action = &gBattleAgentMailbox.legalActions[controlledIndex][selectedActionIndexes[controlledIndex]];
        u16 move;
        u8 target;
        u8 moveLimitations;

        if (action->actorBattler != controlledBattler)
        {
            BattleAgent_ClearResponse();
            return FALSE;
        }

        if (action->kind == BATTLE_AGENT_ACTION_KIND_MOVE)
        {
            if (action->moveSlot >= MAX_MON_MOVES || action->partySlot != BATTLE_AGENT_ACTION_NONE)
            {
                BattleAgent_ClearResponse();
                return FALSE;
            }
            move = gBattleMons[controlledBattler].moves[action->moveSlot];
            moveLimitations = CheckMoveLimitations(controlledBattler, 0, MOVE_LIMITATIONS_ALL);
            if (move == MOVE_NONE || (moveLimitations & gBitTable[action->moveSlot]))
            {
                BattleAgent_ClearResponse();
                return FALSE;
            }
            if (gBattleAgentMailbox.battleMode == BATTLE_AGENT_BATTLE_MODE_TRAINER_SINGLE)
            {
                if (!BattleAgent_NormalizeSingleTarget(controlledBattler, move, &target) || target != action->targetBattler)
                {
                    BattleAgent_ClearResponse();
                    return FALSE;
                }
                gBattleStruct->aiChosenTarget[controlledBattler] = target;
            }
            else if (action->targetBattler != BATTLE_AGENT_ACTION_NONE)
            {
                u32 moveTarget = GetBattlerMoveTargetType(controlledBattler, move);
                if (action->targetBattler >= gBattlersCount || !IsBattlerAlive(action->targetBattler)
                 || ((moveTarget == MOVE_TARGET_USER || moveTarget == MOVE_TARGET_USER_OR_SELECTED) && action->targetBattler != controlledBattler)
                 || (moveTarget == MOVE_TARGET_ALLY && action->targetBattler != BattleAgent_GetDoublePartner(controlledBattler))
                 || (moveTarget != MOVE_TARGET_USER && moveTarget != MOVE_TARGET_USER_OR_SELECTED && moveTarget != MOVE_TARGET_ALLY && GetBattlerSide(action->targetBattler) == GetBattlerSide(controlledBattler)))
                {
                    BattleAgent_ClearResponse();
                    return FALSE;
                }
                gBattleStruct->aiChosenTarget[controlledBattler] = action->targetBattler;
            }
            gBattleStruct->aiMoveOrAction[controlledBattler] = action->moveSlot;
        }
        else if (action->kind == BATTLE_AGENT_ACTION_KIND_SWITCH)
        {
            u32 otherIndex;
            if (action->moveSlot != BATTLE_AGENT_ACTION_NONE || action->targetBattler != BATTLE_AGENT_ACTION_NONE || !BattleAgent_IsLegalSwitch(controlledBattler, action->partySlot))
            {
                BattleAgent_ClearResponse();
                return FALSE;
            }
            for (otherIndex = 0; otherIndex < controlledIndex; otherIndex++)
            {
                struct BattleAgentLegalActionV4 *otherAction = &gBattleAgentMailbox.legalActions[otherIndex][selectedActionIndexes[otherIndex]];
                if (otherAction->kind == BATTLE_AGENT_ACTION_KIND_SWITCH && otherAction->partySlot == action->partySlot)
                {
                    BattleAgent_ClearResponse();
                    return FALSE;
                }
            }
            gBattleStruct->aiMoveOrAction[controlledBattler] = AI_CHOICE_SWITCH;
            gBattleStruct->AI_monToSwitchIntoId[controlledBattler] = action->partySlot;
        }
        else
        {
            BattleAgent_ClearResponse();
            return FALSE;
        }
    }

    for (controlledIndex = 0; controlledIndex < gBattleAgentMailbox.controlledBattlerCount; controlledIndex++)
    {
        u32 controlledBattler = gBattleAgentMailbox.controlledBattlers[controlledIndex];
        sBattleAgentWaitStates[controlledBattler].active = FALSE;
        sBattleAgentWaitStates[controlledBattler].hasAcceptedAction = TRUE;
        BattleAgent_ClearThinkingStatus(controlledBattler);
    }
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
    BattleAgent_BeginRequest();
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
