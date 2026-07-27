#ifndef GUARD_BATTLE_AGENT_H
#define GUARD_BATTLE_AGENT_H

#include <stddef.h>

#include "global.h"
#include "battle.h"

#define BATTLE_AGENT_PROTOCOL_MAGIC   0x42414731 // "BAG1"
#define BATTLE_AGENT_PROTOCOL_VERSION 1
#define BATTLE_AGENT_BATTLE_MODE_TRAINER_SINGLE 1

enum BattleAgentRequestStatus
{
    BATTLE_AGENT_REQUEST_IDLE,
    BATTLE_AGENT_REQUEST_PENDING,
};

enum BattleAgentResponseStatus
{
    BATTLE_AGENT_RESPONSE_NONE,
};

struct BattleAgentBattlerSnapshotV1
{
    u16 species;
    u16 hp;
    u16 maxHp;
    u32 status1;
    u8 statStages[NUM_BATTLE_STATS];
};

struct BattleAgentMoveSnapshotV1
{
    u16 move;
    u8 pp;
};

struct BattleAgentSnapshotV1
{
    struct BattleAgentBattlerSnapshotV1 battlers[MAX_BATTLERS_COUNT];
    struct BattleAgentMoveSnapshotV1 requesterMoves[MAX_MON_MOVES];
    u16 weather;
    u8 terrain;
    u32 fieldStatuses;
    u32 sideStatuses[NUM_BATTLE_SIDES];
};

struct BattleAgentLegalActionV1
{
    u8 actionIndex;
    u8 moveSlot;
    u8 targetBattler;
    u8 reserved;
};

struct BattleAgentMailboxV1
{
    u32 magic;
    u16 protocolVersion;
    u8 requestStatus;
    u8 responseStatus;
    u32 requestSequence;
    u8 requestingBattler;
    u8 battleMode;
    u16 turnSequence;
    struct BattleAgentSnapshotV1 snapshot;
    u8 legalActionCount;
    struct BattleAgentLegalActionV1 legalActions[MAX_MON_MOVES];
    u32 responseSequence;
    u8 responseLegalActionIndex;
};

STATIC_ASSERT(BATTLE_AGENT_PROTOCOL_VERSION == 1, battleAgentProtocolVersionIsV1);
STATIC_ASSERT(sizeof(struct BattleAgentBattlerSnapshotV1) == 20, battleAgentBattlerSnapshotV1Size);
STATIC_ASSERT(sizeof(struct BattleAgentMoveSnapshotV1) == 4, battleAgentMoveSnapshotV1Size);
STATIC_ASSERT(sizeof(struct BattleAgentSnapshotV1) == 112, battleAgentSnapshotV1Size);
STATIC_ASSERT(sizeof(struct BattleAgentLegalActionV1) == 4, battleAgentLegalActionV1Size);
STATIC_ASSERT(sizeof(struct BattleAgentMailboxV1) == 156, battleAgentMailboxV1Size);

STATIC_ASSERT(offsetof(struct BattleAgentBattlerSnapshotV1, species) == 0, battleAgentBattlerSnapshotSpeciesOffset);
STATIC_ASSERT(offsetof(struct BattleAgentBattlerSnapshotV1, hp) == 2, battleAgentBattlerSnapshotHpOffset);
STATIC_ASSERT(offsetof(struct BattleAgentBattlerSnapshotV1, maxHp) == 4, battleAgentBattlerSnapshotMaxHpOffset);
STATIC_ASSERT(offsetof(struct BattleAgentBattlerSnapshotV1, status1) == 8, battleAgentBattlerSnapshotStatus1Offset);
STATIC_ASSERT(offsetof(struct BattleAgentBattlerSnapshotV1, statStages) == 12, battleAgentBattlerSnapshotStatStagesOffset);

STATIC_ASSERT(offsetof(struct BattleAgentMoveSnapshotV1, move) == 0, battleAgentMoveSnapshotMoveOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMoveSnapshotV1, pp) == 2, battleAgentMoveSnapshotPpOffset);

STATIC_ASSERT(offsetof(struct BattleAgentSnapshotV1, battlers) == 0, battleAgentSnapshotBattlersOffset);
STATIC_ASSERT(offsetof(struct BattleAgentSnapshotV1, requesterMoves) == 80, battleAgentSnapshotRequesterMovesOffset);
STATIC_ASSERT(offsetof(struct BattleAgentSnapshotV1, weather) == 96, battleAgentSnapshotWeatherOffset);
STATIC_ASSERT(offsetof(struct BattleAgentSnapshotV1, terrain) == 98, battleAgentSnapshotTerrainOffset);
STATIC_ASSERT(offsetof(struct BattleAgentSnapshotV1, fieldStatuses) == 100, battleAgentSnapshotFieldStatusesOffset);
STATIC_ASSERT(offsetof(struct BattleAgentSnapshotV1, sideStatuses) == 104, battleAgentSnapshotSideStatusesOffset);

STATIC_ASSERT(offsetof(struct BattleAgentLegalActionV1, actionIndex) == 0, battleAgentLegalActionIndexOffset);
STATIC_ASSERT(offsetof(struct BattleAgentLegalActionV1, moveSlot) == 1, battleAgentLegalActionMoveSlotOffset);
STATIC_ASSERT(offsetof(struct BattleAgentLegalActionV1, targetBattler) == 2, battleAgentLegalActionTargetBattlerOffset);
STATIC_ASSERT(offsetof(struct BattleAgentLegalActionV1, reserved) == 3, battleAgentLegalActionReservedOffset);

STATIC_ASSERT(offsetof(struct BattleAgentMailboxV1, magic) == 0, battleAgentMailboxMagicOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV1, protocolVersion) == 4, battleAgentMailboxProtocolVersionOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV1, requestStatus) == 6, battleAgentMailboxRequestStatusOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV1, responseStatus) == 7, battleAgentMailboxResponseStatusOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV1, requestSequence) == 8, battleAgentMailboxRequestSequenceOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV1, requestingBattler) == 12, battleAgentMailboxRequestingBattlerOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV1, battleMode) == 13, battleAgentMailboxBattleModeOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV1, turnSequence) == 14, battleAgentMailboxTurnSequenceOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV1, snapshot) == 16, battleAgentMailboxSnapshotOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV1, legalActionCount) == 128, battleAgentMailboxLegalActionCountOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV1, legalActions) == 132, battleAgentMailboxLegalActionsOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV1, responseSequence) == 148, battleAgentMailboxResponseSequenceOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV1, responseLegalActionIndex) == 152, battleAgentMailboxResponseLegalActionIndexOffset);

extern struct BattleAgentMailboxV1 gBattleAgentMailbox;

void BattleAgent_ResetMailbox(void);
bool32 BattleAgent_TryPublishRequest(u32 battler);

#if TESTING
bool32 BattleAgent_TestNormalizeSingleTarget(u32 requester, u16 move, u8 *target);
#endif

#endif // GUARD_BATTLE_AGENT_H
