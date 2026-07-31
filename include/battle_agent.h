#ifndef GUARD_BATTLE_AGENT_H
#define GUARD_BATTLE_AGENT_H

#include <stddef.h>

#include "global.h"
#include "battle.h"

#define BATTLE_AGENT_PROTOCOL_MAGIC   0x42414732 // "BAG2"
#define BATTLE_AGENT_PROTOCOL_VERSION 3
#define BATTLE_AGENT_BATTLE_MODE_TRAINER_SINGLE 1
#define BATTLE_AGENT_RESPONSE_TIMEOUT_FRAMES 900
#define BATTLE_AGENT_MAX_LEGAL_ACTIONS (MAX_MON_MOVES + PARTY_SIZE)
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
    u16 reserved;
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

struct BattleAgentLegalActionV3
{
    u8 actionIndex;
    u8 kind;
    u8 moveSlot;
    u8 targetBattler;
    u8 partySlot;
    u8 typeEffectiveness;
    u8 hasStab;
    u8 canFaintTarget;
};

struct BattleAgentMailboxV3
{
    u32 magic;
    u16 protocolVersion;
    u8 requestStatus;
    u8 responseStatus;
    u32 requestSequence;
    u8 requestingBattler;
    u8 battleMode;
    u16 turnSequence;
    struct BattleAgentSnapshotV3 snapshot;
    u8 legalActionCount;
    struct BattleAgentLegalActionV3 legalActions[BATTLE_AGENT_MAX_LEGAL_ACTIONS];
    u32 responseSequence;
    u8 responseLegalActionIndex;
};

STATIC_ASSERT(BATTLE_AGENT_PROTOCOL_VERSION == 3, battleAgentProtocolVersionIsV3);
STATIC_ASSERT(sizeof(struct BattleAgentBattlerSnapshotV3) == 48, battleAgentBattlerSnapshotSize);
STATIC_ASSERT(sizeof(struct BattleAgentMoveSnapshotV3) == 12, battleAgentMoveSnapshotSize);
STATIC_ASSERT(sizeof(struct BattleAgentPartySnapshotV3) == 100, battleAgentPartySnapshotSize);
STATIC_ASSERT(sizeof(struct BattleAgentSnapshotV3) == 1048, battleAgentSnapshotSize);
STATIC_ASSERT(sizeof(struct BattleAgentLegalActionV3) == 8, battleAgentLegalActionSize);
STATIC_ASSERT(sizeof(struct BattleAgentMailboxV3) == 1156, battleAgentMailboxSize);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV3, magic) == 0, battleAgentMailboxMagicOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV3, protocolVersion) == 4, battleAgentMailboxProtocolVersionOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV3, requestStatus) == 6, battleAgentMailboxRequestStatusOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV3, responseStatus) == 7, battleAgentMailboxResponseStatusOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV3, requestSequence) == 8, battleAgentMailboxRequestSequenceOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV3, requestingBattler) == 12, battleAgentMailboxRequestingBattlerOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV3, battleMode) == 13, battleAgentMailboxBattleModeOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV3, turnSequence) == 14, battleAgentMailboxTurnSequenceOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV3, snapshot) == 16, battleAgentMailboxSnapshotOffset);
STATIC_ASSERT(offsetof(struct BattleAgentSnapshotV3, battlerMoves) == 240, battleAgentBattlerMovesOffset);
STATIC_ASSERT(offsetof(struct BattleAgentSnapshotV3, weather) == 432, battleAgentWeatherOffset);
STATIC_ASSERT(offsetof(struct BattleAgentSnapshotV3, terrain) == 434, battleAgentTerrainOffset);
STATIC_ASSERT(offsetof(struct BattleAgentSnapshotV3, fieldStatuses) == 436, battleAgentFieldStatusesOffset);
STATIC_ASSERT(offsetof(struct BattleAgentSnapshotV3, sideStatuses) == 440, battleAgentSideStatusesOffset);
STATIC_ASSERT(offsetof(struct BattleAgentSnapshotV3, party) == 448, battleAgentPartyOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV3, legalActionCount) == 1064, battleAgentLegalActionCountOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV3, legalActions) == 1068, battleAgentLegalActionsOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV3, responseSequence) == 1148, battleAgentResponseSequenceOffset);
STATIC_ASSERT(offsetof(struct BattleAgentMailboxV3, responseLegalActionIndex) == 1152, battleAgentResponseActionOffset);

extern struct BattleAgentMailboxV3 gBattleAgentMailbox;

void BattleAgent_ResetMailbox(void);
bool32 BattleAgent_TryPublishRequest(u32 battler);
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
#endif

#endif // GUARD_BATTLE_AGENT_H
