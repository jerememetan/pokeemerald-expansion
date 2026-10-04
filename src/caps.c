#include "global.h"
#include "battle.h"
#include "event_data.h"
#include "caps.h"
#include "pokemon.h"


u32 GetCurrentLevelCap(void)
{
    static const u32 sLevelCapFlagMap[][2] =
    {
        {FLAG_BADGE01_GET, 15},
        {FLAG_BADGE02_GET, 20},
        {FLAG_BADGE03_GET, 26},
        {FLAG_BADGE04_GET, 35},
        {FLAG_BADGE05_GET, 39},
        {FLAG_BADGE06_GET, 49},
        {FLAG_HIDE_LILYCOVE_CITY_RIVAL, 53},
        {FLAG_BADGE07_GET, 60},
        {FLAG_BADGE08_GET, 69},
        {FLAG_IS_CHAMPION, 81},
    };

    u32 i;

    if (B_LEVEL_CAP_TYPE == LEVEL_CAP_FLAG_LIST)
    {
        for (i = 0; i < ARRAY_COUNT(sLevelCapFlagMap); i++)
        {
            if (!FlagGet(sLevelCapFlagMap[i][0]))
                return sLevelCapFlagMap[i][1];
        }
    }
    else if (B_LEVEL_CAP_TYPE == LEVEL_CAP_VARIABLE)
    {
        return VarGet(B_LEVEL_CAP_VARIABLE);
    }

    return MAX_LEVEL;
}

static u32 GetPartyExpFactor(u32 level)
{
    // Archived relative-party multipliers, expressed in hundredths.
    static const u16 sRelativePartyScaling[] =
    {
        300, 275, 250, 233, 225, 200, 180, 170, 160, 150,
        140, 130, 120, 110, 100, 90, 80, 75, 66, 50,
        40, 33, 25, 20, 15, 10, 5,
    };
    u32 count;
    u32 total = 0;
    u32 threshold;
    u32 teamLevel;

    for (count = 0; count < PARTY_SIZE; count++)
    {
        if (GetMonData(&gParties[B_TRAINER_PLAYER][count], MON_DATA_SPECIES) == SPECIES_NONE)
            break;
        total += gParties[B_TRAINER_PLAYER][count].level;
    }
    if (count == 0)
        return 100;

    threshold = (total / count) * 4 / 5;
    total = 0;
    for (u32 i = 0; i < count; i++)
    {
        if (gParties[B_TRAINER_PLAYER][i].level >= threshold)
            total += gParties[B_TRAINER_PLAYER][i].level;
    }
    // Deliberately divide by the original party count, even for filtered mons.
    teamLevel = total / count;
    if (level >= teamLevel + 12)
        return sRelativePartyScaling[ARRAY_COUNT(sRelativePartyScaling) - 1];
    if (level + 14 <= teamLevel)
        return sRelativePartyScaling[0];
    return sRelativePartyScaling[level + 14 - teamLevel];
}

u32 GetSoftLevelCapExpValue(u32 level, u32 expValue)
{
    static const u32 sExpScalingUp[5] = { 16, 8, 4, 2, 1 };
    u32 currentLevelCap = GetCurrentLevelCap();
    u64 scaledExp = expValue;

    if (B_EXP_CAP_TYPE == EXP_CAP_NONE)
        return expValue;

    if (level < currentLevelCap)
    {
        if (B_LEVEL_CAP_EXP_UP)
        {
            u32 levelDifference = currentLevelCap - level;
            if (levelDifference > ARRAY_COUNT(sExpScalingUp) - 1)
                levelDifference = ARRAY_COUNT(sExpScalingUp) - 1;
            scaledExp += expValue / sExpScalingUp[levelDifference];
        }
    }
    else if (B_EXP_CAP_TYPE == EXP_CAP_HARD)
    {
        return 0;
    }
    if (B_EXP_CAP_TYPE == EXP_CAP_SOFT)
    {
        u32 numerator = GetPartyExpFactor(level);
        u32 denominator = 100;

        // MAX_LEVEL is a no-cap sentinel once every milestone flag is set.
        // A variable cap of MAX_LEVEL is still an explicitly selected cap.
        if (level >= currentLevelCap
         && B_LEVEL_CAP_TYPE != LEVEL_CAP_NONE
         && (B_LEVEL_CAP_TYPE != LEVEL_CAP_FLAG_LIST || currentLevelCap != MAX_LEVEL))
        {
            if (level == currentLevelCap)
            {
                numerator *= 3;
                denominator = 1000;
            }
            else
            {
                denominator = 1000000;
            }
        }
        // Combine the two factors before truncating, without floating point.
        scaledExp = scaledExp * numerator / denominator;
    }
    return scaledExp > (u32)-1 ? (u32)-1 : (u32)scaledExp;
}

u32 GetCurrentEVCap(void)
{
    static const u16 sEvCapFlagMap[][2] = {
        // Define EV caps for each milestone
        {FLAG_BADGE01_GET, MAX_TOTAL_EVS *  1 / 17},
        {FLAG_BADGE02_GET, MAX_TOTAL_EVS *  3 / 17},
        {FLAG_BADGE03_GET, MAX_TOTAL_EVS *  5 / 17},
        {FLAG_BADGE04_GET, MAX_TOTAL_EVS *  7 / 17},
        {FLAG_BADGE05_GET, MAX_TOTAL_EVS *  9 / 17},
        {FLAG_BADGE06_GET, MAX_TOTAL_EVS * 11 / 17},
        {FLAG_BADGE07_GET, MAX_TOTAL_EVS * 13 / 17},
        {FLAG_BADGE08_GET, MAX_TOTAL_EVS * 15 / 17},
        {FLAG_IS_CHAMPION, MAX_TOTAL_EVS},
    };

    if (B_EV_CAP_TYPE == EV_CAP_FLAG_LIST)
    {
        for (u32 evCap = 0; evCap < ARRAY_COUNT(sEvCapFlagMap); evCap++)
        {
            if (!FlagGet(sEvCapFlagMap[evCap][0]))
                return sEvCapFlagMap[evCap][1];
        }
    }
    else if (B_EV_CAP_TYPE == EV_CAP_VARIABLE)
    {
        return VarGet(B_EV_CAP_VARIABLE);
    }
    else if (B_EV_CAP_TYPE == EV_CAP_NO_GAIN)
    {
        return 0;
    }

    return MAX_TOTAL_EVS;
}
