#ifndef GUARD_BATTLE_AGENT_H
#define GUARD_BATTLE_AGENT_H

#include <stddef.h>

#include "global.h"
#include "battle.h"

#define BATTLE_AGENT_PROTOCOL_MAGIC   0x42414732 // "BAG2"
#define BATTLE_AGENT_PROTOCOL_VERSION 2
#define BATTLE_AGENT_BATTLE_MODE_TRAINER_SINGLE 1
#define BATTLE_AGENT_RESPONSE_TIMEOUT_FRAMES 900

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

struct BattleAgentBattlerSnapshotV2
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

struct BattleAgentMoveSnapshotV2
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

struct BattleAgentSnapshotV2
{
    struct BattleAgentBattlerSnapshotV2 battlers[MAX_BATTLERS_COUNT];
    struct BattleAgentMoveSnapshotV2 requesterMoves[MAX_MON_MOVES];
    struct BattleAgentMoveSnapshotV2 battlerMoves[MAX_BATTLERS_COUNT][MAX_MON_MOVES];
    u16 weather;
    u8 terrain;
    u32 fieldStatuses;
    u32 sideStatuses[NUM_BATTLE_SIDES];
};

struct BattleAgentLegalActionV2
{
    u8 actionIndex;
    u8 moveSlot;
    u8 targetBattler;
    u8 reserved;
    u8 typeEffectiveness;
    u8 hasStab;
    u8 canFaintTarget;
};

struct BattleAgentMailboxV2
{
    u32 magic;
    u16 protocolVersion;
    u8 requestStatus;
    u8 responseStatus;
    u32 requestSequence;
    u8 requestingBattler;
    u8 battleMode;
    u16 turnSequence;
    struct BattleAgentSnapshotV2 snapshot;
    u8 legalActionCount;
    struct BattleAgentLegalActionV2 legalActions[MAX_MON_MOVES];
    u32 responseSequence;
    u8 responseLegalActionIndex;
};

STATIC_ASSERT(BATTLE_AGENT_PROTOCOL_VERSION == 2, battleAgentProtocolVersionIsV2);
STATIC_ASSERT(sizeof(struct BattleAgentBattlerSnapshotV2) == 48, battleAgentBattlerSnapshotSize);
STATIC_ASSERT(sizeof(struct BattleAgentMoveSnapshotV2) == 12, battleAgentMoveSnapshotSize);
STATIC_ASSERT(sizeof(struct BattleAgentSnapshotV2) == 448, battleAgentSnapshotSize);
STATIC_ASSERT(sizeof(struct BattleAgentLegalActionV2) == 8, battleAgentLegalActionSize);
STATIC_ASSERT(sizeof(struct BattleAgentMailboxV2) == 508, battleAgentMailboxSize);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV2, magic) == 0, battleAgentMailboxMagicOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV2, protocolVersion) == 4, battleAgentMailboxProtocolVersionOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV2, requestStatus) == 6, battleAgentMailboxRequestStatusOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV2, responseStatus) == 7, battleAgentMailboxResponseStatusOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV2, requestSequence) == 8, battleAgentMailboxRequestSequenceOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV2, requestingBattler) == 12, battleAgentMailboxRequestingBattlerOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV2, battleMode) == 13, battleAgentMailboxBattleModeOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV2, turnSequence) == 14, battleAgentMailboxTurnSequenceOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV2, snapshot) == 16, battleAgentMailboxSnapshotOffset);
STATIC_ASSERT(offsetof(struct BattleAgentSnapshotV2, battlerMoves) == 240, battleAgentBattlerMovesOffset);
STATIC_ASSERT(offsetof(struct BattleAgentSnapshotV2, weather) == 432, battleAgentWeatherOffset);
STATIC_ASSERT(offsetof(struct BattleAgentSnapshotV2, terrain) == 434, battleAgentTerrainOffset);
STATIC_ASSERT(offsetof(struct BattleAgentSnapshotV2, fieldStatuses) == 436, battleAgentFieldStatusesOffset);
STATIC_ASSERT(offsetof(struct BattleAgentSnapshotV2, sideStatuses) == 440, battleAgentSideStatusesOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV2, legalActionCount) == 464, battleAgentLegalActionCountOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV2, legalActions) == 468, battleAgentLegalActionsOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV2, responseSequence) == 500, battleAgentResponseSequenceOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV2, responseLegalActionIndex) == 504, battleAgentResponseActionOffset);

extern struct BattleAgentMailboxV2 gBattleAgentMailbox;

void BattleAgent_ResetMailbox(void);
bool32 BattleAgent_TryPublishRequest(u32 battler);
bool32 BattleAgent_BeginExternalWait(u32 battler);
bool32 BattleAgent_TryConsumeResponse(u32 battler);
bool32 BattleAgent_IsWaitExpired(u32 battler);
void BattleAgent_UseVanillaFallback(u32 battler);

#if TESTING
bool32 BattleAgent_TestNormalizeSingleTarget(u32 requester, u16 move, u8 *target);
#endif

#endif // GUARD_BATTLE_AGENT_H
