#ifndef GUARD_BATTLE_AGENT_H
#define GUARD_BATTLE_AGENT_H

#include <stddef.h>

#include "global.h"
#include "battle.h"

#define BATTLE_AGENT_PROTOCOL_MAGIC   0x42414732 // "BAG2"
#define BATTLE_AGENT_PROTOCOL_VERSION 5
#define BATTLE_AGENT_BATTLE_MODE_TRAINER_SINGLE 1
#define BATTLE_AGENT_BATTLE_MODE_TRAINER_DOUBLE 2
#define BATTLE_AGENT_BATTLE_MODE_TRAINER_TWO_OPPONENT_DOUBLE 3
#if TESTING
#define BATTLE_AGENT_RESPONSE_TIMEOUT_FRAMES 900
#else
#define BATTLE_AGENT_RESPONSE_TIMEOUT_FRAMES 1800
#endif
#define BATTLE_AGENT_MAX_ACTIONS_PER_BATTLER 22
#define BATTLE_AGENT_MAX_CONTROLLED_BATTLERS 2
#define BATTLE_AGENT_ACTION_NONE 0xFF

enum BattleAgentRequestStatus
{
    BATTLE_AGENT_REQUEST_IDLE,
    BATTLE_AGENT_REQUEST_PENDING,
};

enum BattleAgentResponseStatus
{
    BATTLE_AGENT_RESPONSE_NONE,
    BATTLE_AGENT_RESPONSE_READY = 1,
};

enum BattleAgentActionKind
{
    BATTLE_AGENT_ACTION_KIND_MOVE,
    BATTLE_AGENT_ACTION_KIND_SWITCH,
};

enum BattleAgentThinkingStatus
{
    BATTLE_AGENT_THINKING_HIDDEN,
    BATTLE_AGENT_THINKING_THREE_DOTS,
    BATTLE_AGENT_THINKING_NO_DOTS,
    BATTLE_AGENT_THINKING_ONE_DOT,
    BATTLE_AGENT_THINKING_TWO_DOTS,
};

#define BATTLE_AGENT_THINKING_DOT_INTERVAL 30

struct BattleAgentBattlerSnapshotV3
{
    u16 species;
    u16 hp;
    u16 maxHp;
    u32 status1;
    u8 statStages[NUM_BATTLE_STATS];
    u8 level;
    u8 type1;
    u8 type2;
    u8 type3;
    u16 ability;
    u16 item;
    u16 attack;
    u16 defense;
    u16 speed;
    u16 spAttack;
    u16 spDefense;
    u32 status2;
    u32 status3;
};

struct BattleAgentMoveSnapshotV3
{
    u16 move;
    u8 pp;
    u8 type;
    u8 power;
    u8 accuracy;
    u16 effect;
    u16 target;
    s8 priority;
    u8 split;
};

struct BattleAgentPartySnapshotV3
{
    struct BattleAgentBattlerSnapshotV3 battler;
    struct BattleAgentMoveSnapshotV3 moves[MAX_MON_MOVES];
    u8 isActive;
    u8 isUsable;
    u8 ownerBattler;
    u8 reserved;
};

struct BattleAgentSnapshotV3
{
    struct BattleAgentBattlerSnapshotV3 battlers[MAX_BATTLERS_COUNT];
    struct BattleAgentMoveSnapshotV3 requesterMoves[MAX_MON_MOVES];
    struct BattleAgentMoveSnapshotV3 battlerMoves[MAX_BATTLERS_COUNT][MAX_MON_MOVES];
    u16 weather;
    u8 terrain;
    u32 fieldStatuses;
    u32 sideStatuses[NUM_BATTLE_SIDES];
    struct BattleAgentPartySnapshotV3 party[PARTY_SIZE];
};

struct BattleAgentLegalActionV4
{
    u8 actorBattler;
    u8 actionIndex;
    u8 kind;
    u8 moveSlot;
    u8 targetBattler;
    u8 partySlot;
    u8 typeEffectiveness;
    u8 hasStab;
    u8 canFaintTarget;
} __attribute__((packed));

struct BattleAgentMailboxV4
{
    u32 magic;
    u16 protocolVersion;
    u8 requestStatus;
    u8 responseStatus;
    u32 requestSequence;
    u8 battleMode;
    u8 controlledBattlerCount;
    u16 turnSequence;
    u8 battlerCount;
    u8 controlledBattlers[BATTLE_AGENT_MAX_CONTROLLED_BATTLERS];
    u8 legalActionCounts[BATTLE_AGENT_MAX_CONTROLLED_BATTLERS];
    u8 reserved[2];
    struct BattleAgentSnapshotV3 snapshot;
    struct BattleAgentLegalActionV4 legalActions[BATTLE_AGENT_MAX_CONTROLLED_BATTLERS][BATTLE_AGENT_MAX_ACTIONS_PER_BATTLER];
    u32 responseSequence;
    u8 responseActionCount;
    u8 responseBattlers[BATTLE_AGENT_MAX_CONTROLLED_BATTLERS];
    u8 responseActionIndexes[BATTLE_AGENT_MAX_CONTROLLED_BATTLERS];
};

STATIC_ASSERT(BATTLE_AGENT_PROTOCOL_VERSION == 5, battleAgentProtocolVersionIsV5);
STATIC_ASSERT(sizeof(struct BattleAgentBattlerSnapshotV3) == 48, battleAgentBattlerSnapshotSize);
STATIC_ASSERT(sizeof(struct BattleAgentMoveSnapshotV3) == 12, battleAgentMoveSnapshotSize);
STATIC_ASSERT(sizeof(struct BattleAgentPartySnapshotV3) == 100, battleAgentPartySnapshotSize);
STATIC_ASSERT(offsetof(struct BattleAgentPartySnapshotV3, ownerBattler) == 98, battleAgentPartyOwnerBattlerOffset);
STATIC_ASSERT(sizeof(struct BattleAgentSnapshotV3) == 1048, battleAgentSnapshotSize);
STATIC_ASSERT(sizeof(struct BattleAgentLegalActionV4) == 9, battleAgentLegalActionSize);
STATIC_ASSERT(sizeof(struct BattleAgentMailboxV4) == 1480, battleAgentMailboxSize);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV4, magic) == 0, battleAgentMailboxMagicOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV4, protocolVersion) == 4, battleAgentMailboxProtocolVersionOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV4, requestStatus) == 6, battleAgentMailboxRequestStatusOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV4, responseStatus) == 7, battleAgentMailboxResponseStatusOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV4, requestSequence) == 8, battleAgentMailboxRequestSequenceOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV4, battleMode) == 12, battleAgentMailboxBattleModeOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV4, controlledBattlerCount) == 13, battleAgentMailboxControlledCountOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV4, turnSequence) == 14, battleAgentMailboxTurnSequenceOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV4, battlerCount) == 16, battleAgentMailboxBattlerCountOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV4, controlledBattlers) == 17, battleAgentMailboxControlledBattlersOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV4, legalActionCounts) == 19, battleAgentMailboxLegalActionCountsOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV4, snapshot) == 24, battleAgentMailboxSnapshotOffset);
STATIC_ASSERT(offsetof(struct BattleAgentSnapshotV3, battlerMoves) == 240, battleAgentBattlerMovesOffset);
STATIC_ASSERT(offsetof(struct BattleAgentSnapshotV3, weather) == 432, battleAgentWeatherOffset);
STATIC_ASSERT(offsetof(struct BattleAgentSnapshotV3, terrain) == 434, battleAgentTerrainOffset);
STATIC_ASSERT(offsetof(struct BattleAgentSnapshotV3, fieldStatuses) == 436, battleAgentFieldStatusesOffset);
STATIC_ASSERT(offsetof(struct BattleAgentSnapshotV3, sideStatuses) == 440, battleAgentSideStatusesOffset);
STATIC_ASSERT(offsetof(struct BattleAgentSnapshotV3, party) == 448, battleAgentPartyOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV4, legalActions) == 1072, battleAgentLegalActionsOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV4, responseSequence) == 1468, battleAgentResponseSequenceOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV4, responseActionCount) == 1472, battleAgentMailboxResponseActionCountOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV4, responseBattlers) == 1473, battleAgentMailboxResponseBattlersOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV4, responseActionIndexes) == 1475, battleAgentMailboxResponseActionIndexesOffset);

extern struct BattleAgentMailboxV4 gBattleAgentMailbox;

void BattleAgent_ResetMailbox(void);
bool32 BattleAgent_TryPublishRequest(u32 battler);
bool32 BattleAgent_IsFirstCoordinatedDoubleBattler(u32 battler);
bool32 BattleAgent_BeginExternalWait(u32 battler);
bool32 BattleAgent_TryConsumeResponse(u32 battler);
bool32 BattleAgent_IsWaitExpired(u32 battler);
void BattleAgent_UseVanillaFallback(u32 battler);
bool32 BattleAgent_TryEmitAcceptedAction(u32 battler);
void BattleAgent_UpdateThinkingStatus(u32 battler, bool32 playerActionConfirmed);
void BattleAgent_ClearThinkingStatus(u32 battler);

#if TESTING
bool32 BattleAgent_TestNormalizeSingleTarget(u32 requester, u16 move, u8 *target);
void BattleAgent_TestStartThinkingStatus(u32 battler);
void BattleAgent_TestUpdateThinkingStatus(u32 battler, bool32 playerActionConfirmed, bool32 messageWindowIdle);
u8 BattleAgent_TestGetThinkingStatus(u32 battler);
u8 BattleAgent_TestGetThinkingStatusFrames(u32 battler);
bool32 BattleAgent_TestArePlayerActionsConfirmed(bool32 leftActive, bool32 leftConfirmed, bool32 rightActive, bool32 rightConfirmed);
#endif

#endif // GUARD_BATTLE_AGENT_H
