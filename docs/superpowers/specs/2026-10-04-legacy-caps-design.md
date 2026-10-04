# Archived Level Caps and Party Experience

Restore the approved archived behaviour from
`f5e81e85df6fe40ae490bf7268d0186d7f0426ed` through the current cap hook,
not by replacing the battle engine. Starting checkpoint: `bf8074499f`.

## Behaviour

Enable `EXP_CAP_SOFT` and `LEVEL_CAP_FLAG_LIST`. The first unset flag selects
the cap, in this exact order:

| Flag | Cap |
| --- | --- |
| FLAG_BADGE01_GET | 15 |
| FLAG_BADGE02_GET | 20 |
| FLAG_BADGE03_GET | 26 |
| FLAG_BADGE04_GET | 35 |
| FLAG_BADGE05_GET | 39 |
| FLAG_BADGE06_GET | 49 |
| FLAG_HIDE_LILYCOVE_CITY_RIVAL | 53 |
| FLAG_BADGE07_GET | 60 |
| FLAG_BADGE08_GET | 69 |
| FLAG_IS_CHAMPION | 81 |

When all flags are set, return MAX_LEVEL and apply no cap reduction.
The existing Lilycove rival object removal already sets its object flag;
no extra map/script mutation is needed.

Below cap, cap factor is 1; at cap it is 0.3; above cap it is 0.0001.
Multiply by the archived party-relative factor and truncate once, not
separately for each factor. Recipient level minus team level, clamped to
[-14, 12], selects these factors in hundredths:

```text
300,275,250,233,225,200,180,170,160,150,140,130,120,110,
100,90,80,75,66,50,40,33,25,20,15,10,5
```

Team level deliberately retains the archive's original denominator:
scan the player party until the first SPECIES_NONE; average all those
levels using integer division; threshold is average * 4 / 5; sum levels
at or above threshold and divide by the ORIGINAL party count. Do not
exclude eggs/fainted members or change the denominator to qualifying count.
For an empty party use a neutral factor of 100 instead of division by zero.

Use u64 intermediate arithmetic, rational factors and a final u32 saturation
for otherwise overflowing boosted inputs. This is a safety guard for invalid
or extreme inputs, not a gameplay rebalance. Remove legacy floating-point
rounding noise, while preserving the intended decimal factors and one-floor
semantics. Do not force a minimum of one experience point.

NONE must still return unchanged input; HARD still returns zero at/above
cap and preserves its existing below-cap optional EXP-up behaviour. SOFT
retains that optional EXP-up setting before party scaling (disabled by
default). Variable caps remain supported. Rare Candy, EV caps, affection,
EXP All and core generation-based XP calculations are separate and unchanged.

## Implementation boundary

Only src/caps.c and include/config/caps.h need runtime changes. A private
party-factor helper is sufficient. Current participation and Exp. Share
hooks already call GetSoftLevelCapExpValue before ApplyExperienceMultipliers;
do not duplicate those hooks or edit battle_script_commands.c.

## Verification and limits

Small Python unittest fixtures compile actual src/caps.c using native WSL cc,
with narrow stubs and the real configuration header. Check every milestone,
party factor/clamp, archived denominator, empty/first-empty party, combined
rounding, tiny/large input, post-Champion behaviour and configuration variants.
Use pinned archived tables as independent evidence. Check Lilycove's implicit
flag chain and both existing XP hooks. Review then build the exact sources.

The stock battle test suite assumes vanilla EXP and is not claimed compatible
with these intentionally changed defaults. Do not introduce a configuration
registry or global test framework to work around those expectations.
In-game badge/rival progression, cap XP and party catch-up remain manual
acceptance checks; a ROM compile cannot establish them.
