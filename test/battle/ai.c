#include "global.h"
#include "test/battle.h"
#include "battle_agent.h"
#include "battle_ai_main.h"
#include "battle_ai_util.h"

AI_SINGLE_BATTLE_TEST("AI gets baited by Protect Switch tactics") // This behavior is to be fixed.
{
    GIVEN {
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE | AI_FLAG_CHECK_VIABILITY | AI_FLAG_TRY_TO_FAINT | AI_FLAG_SMART_SWITCHING);
        PLAYER(SPECIES_STUNFISK);
        PLAYER(SPECIES_PELIPPER);
        OPPONENT(SPECIES_DARKRAI) { Moves(MOVE_TACKLE, MOVE_PECK, MOVE_EARTHQUAKE, MOVE_THUNDERBOLT); }
        OPPONENT(SPECIES_SCIZOR) { Moves(MOVE_HYPER_BEAM, MOVE_FACADE, MOVE_GIGA_IMPACT, MOVE_EXTREME_SPEED); }
    } WHEN {

        TURN { MOVE(player, MOVE_PROTECT);  EXPECT_MOVE(opponent, MOVE_EARTHQUAKE); } // E-quake
        TURN { SWITCH(player, 1);           EXPECT_MOVE(opponent, MOVE_EARTHQUAKE); } // E-quake
        TURN { MOVE(player, MOVE_PROTECT);  EXPECT_MOVE(opponent, MOVE_THUNDERBOLT); } // T-Bolt
        TURN { SWITCH(player, 0);           EXPECT_MOVE(opponent, MOVE_THUNDERBOLT); } // T-Bolt
        TURN { MOVE(player, MOVE_PROTECT);  EXPECT_MOVE(opponent, MOVE_EARTHQUAKE); } // E-quake
        TURN { SWITCH(player, 1);           EXPECT_MOVE(opponent, MOVE_EARTHQUAKE);} // E-quake
        TURN { MOVE(player, MOVE_PROTECT);  EXPECT_MOVE(opponent, MOVE_THUNDERBOLT); } // T-Bolt
    }
}

AI_SINGLE_BATTLE_TEST("AI prefers Bubble over Water Gun if it's slower")
{
    u32 speedPlayer, speedAi;

    PARAMETRIZE { speedPlayer = 200; speedAi = 10; }
    PARAMETRIZE { speedPlayer = 10; speedAi = 200; }

    GIVEN {
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE | AI_FLAG_CHECK_VIABILITY | AI_FLAG_TRY_TO_FAINT);
        PLAYER(SPECIES_SCIZOR) { Speed(speedPlayer); }
        OPPONENT(SPECIES_WOBBUFFET) { Moves(MOVE_WATER_GUN, MOVE_BUBBLE); Speed(speedAi); }
    } WHEN {
        if (speedPlayer > speedAi)
        {
            TURN { SCORE_GT(opponent, MOVE_BUBBLE, MOVE_WATER_GUN); }
            TURN { SCORE_GT(opponent, MOVE_BUBBLE, MOVE_WATER_GUN); }
        }
        else
        {
            TURN { SCORE_EQ(opponent, MOVE_BUBBLE, MOVE_WATER_GUN); }
            TURN { SCORE_EQ(opponent, MOVE_BUBBLE, MOVE_WATER_GUN); }
        }
    }
}

AI_SINGLE_BATTLE_TEST("AI prefers Water Gun over Bubble if it knows that foe has Contrary")
{
    u32 abilityAI;

    PARAMETRIZE { abilityAI = ABILITY_MOXIE; }
    PARAMETRIZE { abilityAI = ABILITY_MOLD_BREAKER; } // Mold Breaker ignores Contrary.
    GIVEN {
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE | AI_FLAG_CHECK_VIABILITY | AI_FLAG_TRY_TO_FAINT);
        PLAYER(SPECIES_SHUCKLE) { Ability(ABILITY_CONTRARY); }
        OPPONENT(SPECIES_PINSIR) { Moves(MOVE_WATER_GUN, MOVE_BUBBLE); Ability(abilityAI); }
    } WHEN {
            TURN { MOVE(player, MOVE_DEFENSE_CURL); }
            TURN { MOVE(player, MOVE_DEFENSE_CURL);
                   if (abilityAI == ABILITY_MOLD_BREAKER) { SCORE_EQ(opponent, MOVE_WATER_GUN, MOVE_BUBBLE); }
                   else { SCORE_GT(opponent, MOVE_WATER_GUN, MOVE_BUBBLE); }}
    } SCENE {
        MESSAGE("Shuckle's Defense fell!"); // Contrary activates
    } THEN {
        EXPECT(gBattleResources->aiData->abilities[B_POSITION_PLAYER_LEFT] == ABILITY_CONTRARY);
    }
}

AI_SINGLE_BATTLE_TEST("AI prefers moves with better accuracy, but only if they both require the same number of hits to ko")
{
    u16 move1 = MOVE_NONE, move2 = MOVE_NONE, move3 = MOVE_NONE, move4 = MOVE_NONE;
    u16 hp, expectedMove, turns, abilityAtk, expectedMove2;

    abilityAtk = ABILITY_NONE;
    expectedMove2 = MOVE_NONE;

    // Here it's a simple test, both Slam and Strength deal the same damage, but Strength always hits, whereas Slam often misses.
    PARAMETRIZE { move1 = MOVE_SLAM; move2 = MOVE_STRENGTH; move3 = MOVE_TACKLE; hp = 490; expectedMove = MOVE_STRENGTH; turns = 4; }
    PARAMETRIZE { move1 = MOVE_SLAM; move2 = MOVE_STRENGTH; move3 = MOVE_SWIFT; move4 = MOVE_TACKLE; hp = 365; expectedMove = MOVE_STRENGTH; turns = 3; }
    PARAMETRIZE { move1 = MOVE_SLAM; move2 = MOVE_STRENGTH; move3 = MOVE_SWIFT; move4 = MOVE_TACKLE; hp = 245; expectedMove = MOVE_STRENGTH; turns = 2; }
    PARAMETRIZE { move1 = MOVE_SLAM; move2 = MOVE_STRENGTH; move3 = MOVE_SWIFT; move4 = MOVE_TACKLE; hp = 125; expectedMove = MOVE_STRENGTH; turns = 1; }
    // Mega Kick deals more damage, but can miss more often. Here, AI should choose Mega Kick if it can faint target in less number of turns than Strength. Otherwise, it should use Strength.
    PARAMETRIZE { move1 = MOVE_MEGA_KICK; move2 = MOVE_STRENGTH; move3 = MOVE_SWIFT; move4 = MOVE_TACKLE; hp = 170; expectedMove = MOVE_MEGA_KICK; turns = 1; }
    PARAMETRIZE { move1 = MOVE_MEGA_KICK; move2 = MOVE_STRENGTH; move3 = MOVE_SWIFT; move4 = MOVE_TACKLE; hp = 245; expectedMove = MOVE_STRENGTH; turns = 2; }
    // Swift always hits and Guts has accuracy of 100%. Hustle lowers accuracy of all physical moves.
    PARAMETRIZE { abilityAtk = ABILITY_HUSTLE; move1 = MOVE_MEGA_KICK; move2 = MOVE_STRENGTH; move3 = MOVE_SWIFT; move4 = MOVE_TACKLE; hp = 5; expectedMove = MOVE_SWIFT; turns = 1; }
    PARAMETRIZE { abilityAtk = ABILITY_HUSTLE; move1 = MOVE_MEGA_KICK; move2 = MOVE_STRENGTH; move3 = MOVE_GUST; move4 = MOVE_TACKLE; hp = 5; expectedMove = MOVE_GUST; turns = 1; }
    // Mega Kick and Slam both have lower accuracy. Gust and Tackle both have 100, so AI can choose either of them.
    PARAMETRIZE { move1 = MOVE_MEGA_KICK; move2 = MOVE_SLAM; move3 = MOVE_TACKLE; move4 = MOVE_GUST; hp = 5; expectedMove = MOVE_GUST; expectedMove2 = MOVE_TACKLE; turns = 1; }
    // All moves hit with No guard ability
    PARAMETRIZE { move1 = MOVE_MEGA_KICK; move2 = MOVE_GUST; hp = 5; expectedMove = MOVE_MEGA_KICK; expectedMove2 = MOVE_GUST; turns = 1; }
    // Tests to compare move that always hits and a beneficial effect. A move with higher acc should be chosen in this case.
    PARAMETRIZE { move1 = MOVE_SHOCK_WAVE; move2 = MOVE_ICY_WIND; hp = 5; expectedMove = MOVE_SHOCK_WAVE; turns = 1; }
    PARAMETRIZE { move1 = MOVE_SHOCK_WAVE; move2 = MOVE_ICY_WIND; move3 = MOVE_THUNDERBOLT; hp = 5; expectedMove = MOVE_SHOCK_WAVE; expectedMove2 = MOVE_THUNDERBOLT; turns = 1; }

    GIVEN {
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE | AI_FLAG_CHECK_VIABILITY | AI_FLAG_TRY_TO_FAINT);
        PLAYER(SPECIES_WOBBUFFET) { HP(hp); }
        PLAYER(SPECIES_WOBBUFFET);
        ASSUME(gBattleMoves[MOVE_SWIFT].accuracy == 0);
        ASSUME(gBattleMoves[MOVE_SLAM].power == gBattleMoves[MOVE_STRENGTH].power);
        ASSUME(gBattleMoves[MOVE_MEGA_KICK].power > gBattleMoves[MOVE_STRENGTH].power);
        ASSUME(gBattleMoves[MOVE_SLAM].accuracy < gBattleMoves[MOVE_STRENGTH].accuracy);
        ASSUME(gBattleMoves[MOVE_MEGA_KICK].accuracy < gBattleMoves[MOVE_STRENGTH].accuracy);
        ASSUME(gBattleMoves[MOVE_TACKLE].accuracy == 100);
        ASSUME(gBattleMoves[MOVE_GUST].accuracy == 100);
        ASSUME(gBattleMoves[MOVE_SHOCK_WAVE].accuracy == 0);
        ASSUME(gBattleMoves[MOVE_THUNDERBOLT].accuracy == 100);
        ASSUME(gBattleMoves[MOVE_ICY_WIND].accuracy != 100);
        OPPONENT(SPECIES_EXPLOUD) { Moves(move1, move2, move3, move4); Ability(abilityAtk); SpAttack(50); } // Low Sp.Atk, so Swift deals less damage than Strength.
    } WHEN {
            switch (turns)
            {
            case 1:
                if (expectedMove2 != MOVE_NONE) {
                    TURN { EXPECT_MOVES(opponent, expectedMove, expectedMove2); SEND_OUT(player, 1); }
                }
                else {
                    TURN { EXPECT_MOVE(opponent, expectedMove); SEND_OUT(player, 1); }
                }
                break;
            case 2:
                TURN { EXPECT_MOVE(opponent, expectedMove); }
                TURN { EXPECT_MOVE(opponent, expectedMove); SEND_OUT(player, 1); }
                break;
            case 3:
                TURN { EXPECT_MOVE(opponent, expectedMove); }
                TURN { EXPECT_MOVE(opponent, expectedMove); }
                TURN { EXPECT_MOVE(opponent, expectedMove); SEND_OUT(player, 1); }
                break;
            case 4:
                TURN { EXPECT_MOVE(opponent, expectedMove); }
                TURN { EXPECT_MOVE(opponent, expectedMove); }
                TURN { EXPECT_MOVE(opponent, expectedMove); }
                TURN { EXPECT_MOVE(opponent, expectedMove); SEND_OUT(player, 1); }
                break;
            }
    } SCENE {
        MESSAGE("Wobbuffet fainted!");
    }
}

AI_SINGLE_BATTLE_TEST("AI prefers moves which deal more damage instead of moves which are super-effective but deal less damage")
{
    u8 turns = 0;
    u16 move1 = MOVE_NONE, move2 = MOVE_NONE, move3 = MOVE_NONE, move4 = MOVE_NONE;
    u16 expectedMove, abilityAtk, abilityDef;

    abilityAtk = ABILITY_NONE;

    // Scald and Poison Jab take 3 hits, Waterfall takes 2.
    PARAMETRIZE { move1 = MOVE_WATERFALL; move2 = MOVE_SCALD; move3 = MOVE_POISON_JAB; move4 = MOVE_WATER_GUN; expectedMove = MOVE_WATERFALL; turns = 2; }
    // Poison Jab takes 3 hits, Water gun 5. Immunity so there's no poison chip damage.
    PARAMETRIZE { move1 = MOVE_POISON_JAB; move2 = MOVE_WATER_GUN; expectedMove = MOVE_POISON_JAB; abilityDef = ABILITY_IMMUNITY; turns = 3; }

    GIVEN {
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE | AI_FLAG_CHECK_VIABILITY | AI_FLAG_TRY_TO_FAINT);
        PLAYER(SPECIES_TYPHLOSION) { Ability(abilityDef); }
        PLAYER(SPECIES_WOBBUFFET);
        OPPONENT(SPECIES_NIDOQUEEN) { Moves(move1, move2, move3, move4); Ability(abilityAtk); }
    } WHEN {
            switch (turns)
            {
            case 2:
                TURN { EXPECT_MOVE(opponent, expectedMove); }
                TURN { EXPECT_MOVE(opponent, expectedMove); SEND_OUT(player, 1); }
                break;
            case 3:
                TURN { EXPECT_MOVE(opponent, expectedMove); }
                TURN { EXPECT_MOVE(opponent, expectedMove); }
                TURN { EXPECT_MOVE(opponent, expectedMove); SEND_OUT(player, 1); }
                break;
            }
    } SCENE {
        MESSAGE("Typhlosion fainted!");
    }
}

AI_SINGLE_BATTLE_TEST("AI prefers Earthquake over Drill Run if both require the same number of hits to ko")
{
    // Drill Run has less accuracy than E-quake, but can score a higher crit. However the chance is too small, so AI should ignore it.
    GIVEN {
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE | AI_FLAG_CHECK_VIABILITY | AI_FLAG_TRY_TO_FAINT);
        PLAYER(SPECIES_TYPHLOSION);
        PLAYER(SPECIES_WOBBUFFET);
        OPPONENT(SPECIES_GEODUDE) { Moves(MOVE_EARTHQUAKE, MOVE_DRILL_RUN); }
    } WHEN {
        TURN { EXPECT_MOVE(opponent, MOVE_EARTHQUAKE); }
        TURN { EXPECT_MOVE(opponent, MOVE_EARTHQUAKE); SEND_OUT(player, 1); }
    }
    SCENE {
        MESSAGE("Typhlosion fainted!");
    }
}

AI_SINGLE_BATTLE_TEST("AI prefers a weaker move over a one with a downside effect if both require the same number of hits to ko")
{
    u16 move1 = MOVE_NONE, move2 = MOVE_NONE, move3 = MOVE_NONE, move4 = MOVE_NONE;
    u16 hp, expectedMove, turns;

    // Both moves require the same number of turns but Flamethrower will be chosen over Overheat (powerful effect)
    PARAMETRIZE { move1 = MOVE_OVERHEAT; move2 = MOVE_FLAMETHROWER; hp = 300; expectedMove = MOVE_FLAMETHROWER; turns = 2; }
    // Overheat kill in least amount of turns
    PARAMETRIZE { move1 = MOVE_OVERHEAT; move2 = MOVE_FLAMETHROWER; hp = 250; expectedMove = MOVE_OVERHEAT; turns = 1; }

    GIVEN {
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE | AI_FLAG_CHECK_VIABILITY | AI_FLAG_TRY_TO_FAINT);
        PLAYER(SPECIES_WOBBUFFET) { HP(hp); }
        PLAYER(SPECIES_WOBBUFFET);
        OPPONENT(SPECIES_TYPHLOSION) { Moves(move1, move2, move3, move4); }
    } WHEN {
        switch (turns)
        {
        case 1:
            TURN { EXPECT_MOVE(opponent, expectedMove); SEND_OUT(player, 1); }
            break;
        case 2:
            TURN { EXPECT_MOVE(opponent, expectedMove); }
            TURN { EXPECT_MOVE(opponent, expectedMove); SEND_OUT(player, 1); }
            break;
        }
    } SCENE {
        MESSAGE("Wobbuffet fainted!");
    }
}

AI_SINGLE_BATTLE_TEST("AI prefers moves with the best possible score, chosen randomly if tied")
{
    GIVEN {
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE | AI_FLAG_CHECK_VIABILITY | AI_FLAG_TRY_TO_FAINT);
        PLAYER(SPECIES_WOBBUFFET) { HP(5); };
        PLAYER(SPECIES_WOBBUFFET);
        OPPONENT(SPECIES_WOBBUFFET) { Moves(MOVE_THUNDERBOLT, MOVE_SLUDGE_BOMB, MOVE_TAKE_DOWN); }
    } WHEN {
        TURN { EXPECT_MOVES(opponent, MOVE_THUNDERBOLT, MOVE_SLUDGE_BOMB); SEND_OUT(player, 1); }
    }
    SCENE {
        MESSAGE("Wobbuffet fainted!");
    }
}

AI_SINGLE_BATTLE_TEST("AI can choose a status move that boosts the attack by two")
{
    GIVEN {
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE | AI_FLAG_CHECK_VIABILITY | AI_FLAG_TRY_TO_FAINT);
        PLAYER(SPECIES_WOBBUFFET) { HP(277); };
        PLAYER(SPECIES_WOBBUFFET);
        OPPONENT(SPECIES_KANGASKHAN) { Moves(MOVE_STRENGTH, MOVE_HORN_ATTACK, MOVE_SWORDS_DANCE); }
    } WHEN {
        TURN { EXPECT_MOVES(opponent, MOVE_STRENGTH, MOVE_SWORDS_DANCE); }
        TURN { EXPECT_MOVE(opponent, MOVE_STRENGTH); SEND_OUT(player, 1); }
    }
}

AI_SINGLE_BATTLE_TEST("AI chooses the safest option to faint the target, taking into account accuracy and move effect")
{
    u16 move1 = MOVE_NONE, move2 = MOVE_NONE, move3 = MOVE_NONE, move4 = MOVE_NONE;
    u16 expectedMove, expectedMove2 = MOVE_NONE;
    u16 abilityAtk = ABILITY_NONE, holdItemAtk = ITEM_NONE;

    // Psychic is not very effective, but always hits. Solarbeam requires a charging turn, Double Edge has recoil and Focus Blast can miss;
    PARAMETRIZE { abilityAtk = ABILITY_STURDY; move1 = MOVE_FOCUS_BLAST; move2 = MOVE_SOLAR_BEAM; move3 = MOVE_PSYCHIC; move4 = MOVE_DOUBLE_EDGE; expectedMove = MOVE_PSYCHIC; }
    // Same as above, but ai mon has rock head ability, so it can use Double Edge without taking recoil damage. Psychic can also lower Special Defense,
    // but because it faints the target it doesn't matter.
    PARAMETRIZE { abilityAtk = ABILITY_ROCK_HEAD; move1 = MOVE_FOCUS_BLAST; move2 = MOVE_SOLAR_BEAM; move3 = MOVE_PSYCHIC; move4 = MOVE_DOUBLE_EDGE;
                  expectedMove = MOVE_PSYCHIC; expectedMove2 = MOVE_DOUBLE_EDGE; }
    // This time it's Solarbeam + Psychic, because the weather is sunny.
    PARAMETRIZE { abilityAtk = ABILITY_DROUGHT; move1 = MOVE_FOCUS_BLAST; move2 = MOVE_SOLAR_BEAM; move3 = MOVE_PSYCHIC; move4 = MOVE_DOUBLE_EDGE;
                  expectedMove = MOVE_PSYCHIC; expectedMove2 = MOVE_SOLAR_BEAM; }
    // Psychic and Solar Beam are chosen because user is holding Power Herb
    PARAMETRIZE { abilityAtk = ABILITY_STURDY; holdItemAtk = ITEM_POWER_HERB; move1 = MOVE_FOCUS_BLAST; move2 = MOVE_SOLAR_BEAM; move3 = MOVE_PSYCHIC; move4 = MOVE_DOUBLE_EDGE;
                  expectedMove = MOVE_PSYCHIC; expectedMove2 = MOVE_SOLAR_BEAM; }
    // Psychic and Skull Bash are chosen because user is holding Power Herb
    PARAMETRIZE { abilityAtk = ABILITY_STURDY; holdItemAtk = ITEM_POWER_HERB; move1 = MOVE_FOCUS_BLAST; move2 = MOVE_SKULL_BASH; move3 = MOVE_PSYCHIC; move4 = MOVE_DOUBLE_EDGE;
                  expectedMove = MOVE_PSYCHIC; expectedMove2 = MOVE_SKULL_BASH; }
    // Skull Bash is chosen because it's the most accurate and is holding Power Herb
    PARAMETRIZE { abilityAtk = ABILITY_STURDY; holdItemAtk = ITEM_POWER_HERB; move1 = MOVE_FOCUS_BLAST; move2 = MOVE_SKULL_BASH; move3 = MOVE_SLAM; move4 = MOVE_DOUBLE_EDGE;
                  expectedMove = MOVE_SKULL_BASH; }
    // Crabhammer is chosen even if Skull Bash is more accurate, the user has no Power Herb
    PARAMETRIZE { abilityAtk = ABILITY_STURDY; move1 = MOVE_FOCUS_BLAST; move2 = MOVE_SKULL_BASH; move3 = MOVE_SLAM; move4 = MOVE_CRABHAMMER;
                  expectedMove = MOVE_CRABHAMMER; }

    GIVEN {
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE | AI_FLAG_CHECK_VIABILITY | AI_FLAG_TRY_TO_FAINT);
        PLAYER(SPECIES_WOBBUFFET) { HP(5); }
        PLAYER(SPECIES_WOBBUFFET);
        OPPONENT(SPECIES_GEODUDE) { Moves(move1, move2, move3, move4); Ability(abilityAtk); Item(holdItemAtk); }
    } WHEN {
        TURN {  if (expectedMove2 == MOVE_NONE) { EXPECT_MOVE(opponent, expectedMove); SEND_OUT(player, 1); }
                else {EXPECT_MOVES(opponent, expectedMove, expectedMove2); SCORE_EQ(opponent, expectedMove, expectedMove2); SEND_OUT(player, 1);}
             }
    }
    SCENE {
        MESSAGE("Wobbuffet fainted!");
    }
}

AI_SINGLE_BATTLE_TEST("AI won't use Solar Beam if there is no Sun up or the user is not holding Power Herb")
{
    u16 abilityAtk = ABILITY_NONE;
    u16 holdItemAtk = ITEM_NONE;

    PARAMETRIZE { abilityAtk = ABILITY_DROUGHT; }
    PARAMETRIZE { holdItemAtk = ITEM_POWER_HERB; }
    PARAMETRIZE { }

    GIVEN {
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE | AI_FLAG_CHECK_VIABILITY | AI_FLAG_TRY_TO_FAINT);
        PLAYER(SPECIES_WOBBUFFET) { HP(211); }
        PLAYER(SPECIES_WOBBUFFET);
        OPPONENT(SPECIES_TYPHLOSION) { Moves(MOVE_SOLAR_BEAM, MOVE_GRASS_PLEDGE); Ability(abilityAtk); Item(holdItemAtk); }
    } WHEN {
        if (abilityAtk == ABILITY_DROUGHT) {
            TURN { EXPECT_MOVES(opponent, MOVE_SOLAR_BEAM, MOVE_GRASS_PLEDGE); }
            TURN { EXPECT_MOVES(opponent, MOVE_SOLAR_BEAM, MOVE_GRASS_PLEDGE); SEND_OUT(player, 1); }
        } else if (holdItemAtk == ITEM_POWER_HERB) {
            TURN { EXPECT_MOVES(opponent, MOVE_SOLAR_BEAM, MOVE_GRASS_PLEDGE); MOVE(player, MOVE_KNOCK_OFF); }
            TURN { EXPECT_MOVE(opponent, MOVE_GRASS_PLEDGE); SEND_OUT(player, 1); }
        } else {
            TURN { EXPECT_MOVE(opponent, MOVE_GRASS_PLEDGE); }
            TURN { EXPECT_MOVE(opponent, MOVE_GRASS_PLEDGE); SEND_OUT(player, 1); }
        }
    } SCENE {
        MESSAGE("Wobbuffet fainted!");
    }
}

AI_SINGLE_BATTLE_TEST("AI won't use ground type attacks against flying type Pokemon unless Gravity is in effect")
{
    GIVEN {
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE | AI_FLAG_CHECK_VIABILITY | AI_FLAG_TRY_TO_FAINT);
        PLAYER(SPECIES_CROBAT);
        PLAYER(SPECIES_WOBBUFFET);
        OPPONENT(SPECIES_NIDOQUEEN) { Moves(MOVE_EARTHQUAKE, MOVE_TACKLE, MOVE_POISON_STING, MOVE_GUST); }
    } WHEN {
            TURN { NOT_EXPECT_MOVE(opponent, MOVE_EARTHQUAKE); }
            TURN { MOVE(player, MOVE_GRAVITY); NOT_EXPECT_MOVE(opponent, MOVE_EARTHQUAKE); }
            TURN { EXPECT_MOVE(opponent, MOVE_EARTHQUAKE); SEND_OUT(player, 1); }
    } SCENE {
        MESSAGE("Gravity intensified!");
    }
}

AI_DOUBLE_BATTLE_TEST("AI won't use a Weather changing move if partner already chose such move")
{
    u32 j, k;
    static const u16 weatherMoves[] = {MOVE_SUNNY_DAY, MOVE_HAIL, MOVE_RAIN_DANCE, MOVE_SANDSTORM, MOVE_SNOWSCAPE};
    u16 weatherMoveLeft = MOVE_NONE, weatherMoveRight = MOVE_NONE;

    for (j = 0; j < ARRAY_COUNT(weatherMoves); j++)
    {
        for (k = 0; k < ARRAY_COUNT(weatherMoves); k++)
        {
            PARAMETRIZE { weatherMoveLeft = weatherMoves[j]; weatherMoveRight = weatherMoves[k]; }
        }
    }

    GIVEN {
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE | AI_FLAG_CHECK_VIABILITY | AI_FLAG_TRY_TO_FAINT);
        PLAYER(SPECIES_WOBBUFFET);
        PLAYER(SPECIES_WOBBUFFET);
        OPPONENT(SPECIES_WOBBUFFET) { Moves(weatherMoveLeft); }
        OPPONENT(SPECIES_WOBBUFFET) { Moves(MOVE_TACKLE, weatherMoveRight); }
    } WHEN {
            TURN {  NOT_EXPECT_MOVE(opponentRight, weatherMoveRight);
                    SCORE_LT_VAL(opponentRight, weatherMoveRight, AI_SCORE_DEFAULT, target:playerLeft);
                    SCORE_LT_VAL(opponentRight, weatherMoveRight, AI_SCORE_DEFAULT, target:playerRight);
                    SCORE_LT_VAL(opponentRight, weatherMoveRight, AI_SCORE_DEFAULT, target:opponentLeft);
                 }
    }
}

AI_DOUBLE_BATTLE_TEST("AI will not use Helping Hand if partner does not have any damage moves")
{
    u16 move1 = MOVE_NONE, move2 = MOVE_NONE, move3 = MOVE_NONE, move4 = MOVE_NONE;

    PARAMETRIZE{ move1 = MOVE_LEER; move2 = MOVE_TOXIC; }
    PARAMETRIZE{ move1 = MOVE_HELPING_HAND; move2 = MOVE_PROTECT; }
    PARAMETRIZE{ move1 = MOVE_ACUPRESSURE; move2 = MOVE_DOUBLE_TEAM; move3 = MOVE_TOXIC; move4 = MOVE_PROTECT; }

    GIVEN {
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE | AI_FLAG_CHECK_VIABILITY | AI_FLAG_TRY_TO_FAINT);
        PLAYER(SPECIES_WOBBUFFET);
        PLAYER(SPECIES_WOBBUFFET);
        OPPONENT(SPECIES_WOBBUFFET) { Moves(MOVE_HELPING_HAND, MOVE_TACKLE); }
        OPPONENT(SPECIES_WOBBUFFET) { Moves(move1, move2, move3, move4); }
    } WHEN {
            TURN {  NOT_EXPECT_MOVE(opponentLeft, MOVE_HELPING_HAND);
                    SCORE_LT_VAL(opponentLeft, MOVE_HELPING_HAND, AI_SCORE_DEFAULT, target:playerLeft);
                    SCORE_LT_VAL(opponentLeft, MOVE_HELPING_HAND, AI_SCORE_DEFAULT, target:playerRight);
                    SCORE_LT_VAL(opponentLeft, MOVE_HELPING_HAND, AI_SCORE_DEFAULT, target:opponentLeft);
                 }
    } SCENE {
        NOT MESSAGE("Foe Wobbuffet used Helping Hand!");
    }
}

AI_DOUBLE_BATTLE_TEST("AI will not use a status move if partner already chose Helping Hand")
{
    s32 j;
    u32 statusMove = MOVE_NONE;

    for (j = MOVE_NONE + 1; j < MOVES_COUNT; j++)
    {
        if (gBattleMoves[j].split == SPLIT_STATUS) {
            PARAMETRIZE{ statusMove = j; }
        }
    }

    GIVEN {
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE | AI_FLAG_CHECK_VIABILITY | AI_FLAG_TRY_TO_FAINT);
        PLAYER(SPECIES_WOBBUFFET);
        PLAYER(SPECIES_WOBBUFFET);
        OPPONENT(SPECIES_WOBBUFFET) { Moves(MOVE_HELPING_HAND); }
        OPPONENT(SPECIES_WOBBUFFET) { Moves(MOVE_TACKLE, statusMove); }
    } WHEN {
            TURN {  NOT_EXPECT_MOVE(opponentRight, statusMove);
                    SCORE_LT_VAL(opponentRight, statusMove, AI_SCORE_DEFAULT, target:playerLeft);
                    SCORE_LT_VAL(opponentRight, statusMove, AI_SCORE_DEFAULT, target:playerRight);
                    SCORE_LT_VAL(opponentRight, statusMove, AI_SCORE_DEFAULT, target:opponentLeft);
                 }
    } SCENE {
        MESSAGE("Foe Wobbuffet used Helping Hand!");
    }
}

AI_SINGLE_BATTLE_TEST("AI without any flags chooses moves at random - singles")
{
    GIVEN {
        AI_FLAGS(0);
        PLAYER(SPECIES_WOBBUFFET);
        OPPONENT(SPECIES_NIDOQUEEN) { Moves(MOVE_SPLASH, MOVE_EXPLOSION, MOVE_RAGE, MOVE_HELPING_HAND); }
    } WHEN {
            TURN { EXPECT_MOVES(opponent, MOVE_SPLASH, MOVE_EXPLOSION, MOVE_RAGE, MOVE_HELPING_HAND);
                   SCORE_EQ_VAL(opponent, MOVE_SPLASH, AI_SCORE_DEFAULT);
                   SCORE_EQ_VAL(opponent, MOVE_EXPLOSION, AI_SCORE_DEFAULT);
                   SCORE_EQ_VAL(opponent, MOVE_RAGE, AI_SCORE_DEFAULT);
                   SCORE_EQ_VAL(opponent, MOVE_HELPING_HAND, AI_SCORE_DEFAULT);
                }
    }
}

AI_DOUBLE_BATTLE_TEST("AI without any flags chooses moves at random - doubles")
{
    GIVEN {
        AI_FLAGS(0);
        PLAYER(SPECIES_WOBBUFFET);
        PLAYER(SPECIES_WOBBUFFET);
        OPPONENT(SPECIES_NIDOQUEEN) { Moves(MOVE_SPLASH, MOVE_EXPLOSION, MOVE_RAGE, MOVE_HELPING_HAND); }
        OPPONENT(SPECIES_NIDOQUEEN) { Moves(MOVE_SPLASH, MOVE_EXPLOSION, MOVE_RAGE, MOVE_HELPING_HAND); }
    } WHEN {
            TURN { EXPECT_MOVES(opponentLeft, MOVE_SPLASH, MOVE_EXPLOSION, MOVE_RAGE, MOVE_HELPING_HAND);
                   EXPECT_MOVES(opponentRight, MOVE_SPLASH, MOVE_EXPLOSION, MOVE_RAGE, MOVE_HELPING_HAND);
                   SCORE_EQ_VAL(opponentLeft, MOVE_SPLASH, AI_SCORE_DEFAULT, target:playerLeft);
                   SCORE_EQ_VAL(opponentLeft, MOVE_EXPLOSION, AI_SCORE_DEFAULT, target:playerLeft);
                   SCORE_EQ_VAL(opponentLeft, MOVE_RAGE, AI_SCORE_DEFAULT, target:playerLeft);
                   SCORE_EQ_VAL(opponentLeft, MOVE_HELPING_HAND, AI_SCORE_DEFAULT, target:playerLeft);
                   SCORE_EQ_VAL(opponentRight, MOVE_SPLASH, AI_SCORE_DEFAULT, target:playerLeft);
                   SCORE_EQ_VAL(opponentRight, MOVE_EXPLOSION, AI_SCORE_DEFAULT, target:playerLeft);
                   SCORE_EQ_VAL(opponentRight, MOVE_RAGE, AI_SCORE_DEFAULT, target:playerLeft);
                   SCORE_EQ_VAL(opponentRight, MOVE_HELPING_HAND, AI_SCORE_DEFAULT, target:playerLeft);
                }
    }
}

AI_SINGLE_BATTLE_TEST("AI will choose either Rock Tomb or Bulldoze if Stat drop effect will activate and they kill with the same number of hits")
{
    GIVEN {
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE | AI_FLAG_CHECK_VIABILITY | AI_FLAG_TRY_TO_FAINT);
        PLAYER(SPECIES_WOBBUFFET) { HP(46); Speed(20); }
        PLAYER(SPECIES_WYNAUT) { Speed(20); }
        OPPONENT(SPECIES_WOBBUFFET) { Speed(10); Moves(MOVE_BULLDOZE, MOVE_ROCK_TOMB); }
    } WHEN {
            TURN { EXPECT_MOVES(opponent, MOVE_BULLDOZE, MOVE_ROCK_TOMB); }
            TURN { EXPECT_MOVES(opponent, MOVE_BULLDOZE, MOVE_ROCK_TOMB); SEND_OUT(player, 1); }
    } SCENE {
        MESSAGE("Wobbuffet fainted!");
    }
}

AI_SINGLE_BATTLE_TEST("AI_FLAG_SMART_MON_CHOICES: AI will not switch in a Pokemon which is slower and gets 1HKOed after fainting")
{
    bool32 alakazamFirst;
    u32 speedAlakazm;
    u32 aiSmartSwitchFlags = 0;

    PARAMETRIZE{ speedAlakazm = 200; alakazamFirst = TRUE; } // AI will always send out Alakazan as it sees a KO with Focus Blast, even if Alakazam dies before it can get it off
    PARAMETRIZE{ speedAlakazm = 200; alakazamFirst = FALSE; aiSmartSwitchFlags = AI_FLAG_SMART_SWITCHING | AI_FLAG_SMART_MON_CHOICES; } // AI_FLAG_SMART_MON_CHOICES lets AI see that Alakazam would be KO'd before it can KO, and won't switch it in
    PARAMETRIZE{ speedAlakazm = 400; alakazamFirst = TRUE; aiSmartSwitchFlags = AI_FLAG_SMART_SWITCHING | AI_FLAG_SMART_MON_CHOICES; } // AI_FLAG_SMART_MON_CHOICES recognizes that Alakazam is faster and can KO, and will switch it in

    GIVEN {
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE | AI_FLAG_CHECK_VIABILITY | AI_FLAG_TRY_TO_FAINT | aiSmartSwitchFlags);
        PLAYER(SPECIES_WEAVILE) { Speed(300); Ability(ABILITY_SHADOW_TAG); } // Weavile has Shadow Tag, so AI can't switch on the first turn, but has to do it after fainting.
        OPPONENT(SPECIES_KADABRA) { Speed(200); Moves(MOVE_PSYCHIC, MOVE_DISABLE, MOVE_TAUNT, MOVE_CALM_MIND); }
        OPPONENT(SPECIES_ALAKAZAM) { Speed(speedAlakazm); Moves(MOVE_FOCUS_BLAST, MOVE_PSYCHIC); } // Alakazam has a move which OHKOes Weavile, but it doesn't matter if he's getting KO-ed first.
        OPPONENT(SPECIES_BLASTOISE) { Speed(200); Moves(MOVE_BUBBLE_BEAM, MOVE_WATER_GUN, MOVE_LEER, MOVE_STRENGTH); } // Can't OHKO, but survives a hit from Weavile's Night Slash.
    } WHEN {
            TURN { MOVE(player, MOVE_NIGHT_SLASH) ; EXPECT_SEND_OUT(opponent, alakazamFirst ? 1 : 2); } // AI doesn't send out Alakazam if it gets outsped
    } SCENE {
        MESSAGE("Foe Kadabra fainted!");
        if (alakazamFirst) {
            MESSAGE("{PKMN} TRAINER LEAF sent out Alakazam!");
        } else {
            MESSAGE("{PKMN} TRAINER LEAF sent out Blastoise!");
        }
    }
}

AI_SINGLE_BATTLE_TEST("AI switches if Perish Song is about to kill")
{
    GIVEN {
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE | AI_FLAG_CHECK_VIABILITY | AI_FLAG_TRY_TO_FAINT);
        PLAYER(SPECIES_WOBBUFFET);
        OPPONENT(SPECIES_WOBBUFFET) {Moves(MOVE_TACKLE); }
        OPPONENT(SPECIES_CROBAT) {Moves(MOVE_TACKLE); }
    } WHEN {
            TURN { MOVE(player, MOVE_PERISH_SONG); }
            TURN { ; }
            TURN { ; }
            TURN { EXPECT_SWITCH(opponent, 1); }
    } SCENE {
        MESSAGE("{PKMN} TRAINER LEAF sent out Crobat!");
    }
}

AI_SINGLE_BATTLE_TEST("AI_FLAG_SMART_MON_CHOICES: AI will not switch in a Pokemon which is slower and gets 1HKOed after fainting")
{
    bool32 alakazamFaster;
    u32 speedAlakazm;

    PARAMETRIZE{ speedAlakazm = 200; alakazamFaster = FALSE; }
    PARAMETRIZE{ speedAlakazm = 400; alakazamFaster = TRUE; }

    GIVEN {
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE | AI_FLAG_CHECK_VIABILITY | AI_FLAG_TRY_TO_FAINT | AI_FLAG_SMART_MON_CHOICES);
        PLAYER(SPECIES_WEAVILE) { Speed(300); Ability(ABILITY_SHADOW_TAG); } // Weavile has Shadow Tag, so AI can't switch on the first turn, but has to do it after fainting.
        OPPONENT(SPECIES_KADABRA) { Speed(200); Moves(MOVE_PSYCHIC, MOVE_DISABLE, MOVE_TAUNT, MOVE_CALM_MIND); }
        OPPONENT(SPECIES_ALAKAZAM) { Speed(speedAlakazm); Moves(MOVE_FOCUS_BLAST, MOVE_PSYCHIC); } // Alakazam has a move which OHKOes Weavile, but it doesn't matter if he's getting KO-ed first.
        OPPONENT(SPECIES_BLASTOISE) { Speed(200); Moves(MOVE_BUBBLE_BEAM, MOVE_WATER_GUN, MOVE_LEER, MOVE_STRENGTH); } // Can't OHKO, but survives a hit from Weavile's Night Slash.
    } WHEN {
            TURN { MOVE(player, MOVE_NIGHT_SLASH) ; EXPECT_SEND_OUT(opponent, alakazamFaster ? 1 : 2); }
    } SCENE {
        MESSAGE("Foe Kadabra fainted!");
        if (alakazamFaster) {
            MESSAGE("{PKMN} TRAINER LEAF sent out Alakazam!");
        } else {
            MESSAGE("{PKMN} TRAINER LEAF sent out Blastoise!");
        }
    }
}

AI_SINGLE_BATTLE_TEST("AI_FLAG_SMART_MON_CHOICES: AI considers hazard damage when choosing which Pokemon to switch in")
{
    u32 aiIsSmart = 0;
    u32 aiSmartSwitchFlags = 0;

    PARAMETRIZE{ aiIsSmart = 0; aiSmartSwitchFlags = 0; } // AI doesn't care about hazard damage resulting in Pokemon being KO'd
    PARAMETRIZE{ aiIsSmart = 1; aiSmartSwitchFlags = AI_FLAG_SMART_MON_CHOICES; } // AI_FLAG_SMART_MON_CHOICES avoids being KO'd as a result of hazards damage

    GIVEN {
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE | AI_FLAG_CHECK_VIABILITY | AI_FLAG_TRY_TO_FAINT | aiSmartSwitchFlags);
        PLAYER(SPECIES_MEGANIUM) { Speed(100); SpDefense(328); SpAttack(265); Moves(MOVE_STEALTH_ROCK, MOVE_SURF); } // Meganium does ~56% minimum ~66% maximum, enough to KO Charizard after rocks and never KO Typhlosion after rocks
        OPPONENT(SPECIES_PONYTA) { Level(5); Speed(5); Moves(MOVE_TACKLE); }
        OPPONENT(SPECIES_CHARIZARD) { Speed(200); Moves(MOVE_FLAMETHROWER); SpAttack(317); SpDefense(207); MaxHP(297); } // Outspeends and 2HKOs Meganium
        OPPONENT(SPECIES_TYPHLOSION) { Speed(200); Moves(MOVE_FLAMETHROWER); SpAttack(317); SpDefense(207); MaxHP(297); } // Outspeends and 2HKOs Meganium
    } WHEN {
            TURN { MOVE(player, MOVE_STEALTH_ROCK) ;}
            TURN { MOVE(player, MOVE_SURF) ; EXPECT_SEND_OUT(opponent, aiIsSmart ? 2 : 1); } // AI sends out Typhlosion to get the KO with the flag rather than Charizard
    }
}

AI_SINGLE_BATTLE_TEST("AI_FLAG_SMART_MON_CHOICES: Mid-battle switches prioritize type matchup + SE move, then type matchup")
{
    u32 aiSmartSwitchFlags = 0;
    u32 move1;
    u32 move2;
    u32 expectedIndex;

    PARAMETRIZE{ expectedIndex = 3; move1 = MOVE_TACKLE; move2 = MOVE_TACKLE; aiSmartSwitchFlags = 0; } // When not smart, AI will only switch in a defensive mon if it has a SE move, otherwise will just default to damage
    PARAMETRIZE{ expectedIndex = 1; move1 = MOVE_GIGA_DRAIN; move2 = MOVE_TACKLE; aiSmartSwitchFlags = 0; }
    PARAMETRIZE{ expectedIndex = 2; move1 = MOVE_TACKLE; move2 = MOVE_TACKLE; aiSmartSwitchFlags = AI_FLAG_SMART_MON_CHOICES; } // When smart, AI will prioritize SE move, but still switch in good type matchup without SE move
    PARAMETRIZE{ expectedIndex = 1; move1 = MOVE_GIGA_DRAIN; move2 = MOVE_TACKLE; aiSmartSwitchFlags = AI_FLAG_SMART_MON_CHOICES; }

    GIVEN {
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE | AI_FLAG_CHECK_VIABILITY | AI_FLAG_TRY_TO_FAINT | aiSmartSwitchFlags);
        PLAYER(SPECIES_MARSHTOMP) { Level(30); Moves(MOVE_MUD_BOMB, MOVE_WATER_GUN, MOVE_GROWL, MOVE_MUD_SHOT); Speed(5); }
        OPPONENT(SPECIES_PONYTA) { Level(1); Moves(MOVE_NONE); Speed(6); } // Forces switchout
        OPPONENT(SPECIES_TANGELA) { Level(30); Moves(move1); Speed(4); }
        OPPONENT(SPECIES_LOMBRE) { Level(30); Moves(move2); Speed(4); }
        OPPONENT(SPECIES_HARIYAMA) { Level(30); Moves(MOVE_VITAL_THROW); Speed(4); }
    } WHEN {
            TURN { MOVE(player, MOVE_GROWL) ; EXPECT_SWITCH(opponent, expectedIndex); }
    }
}

AI_SINGLE_BATTLE_TEST("AI_FLAG_SMART_MON_CHOICES: Mid-battle switches prioritize defensive options")
{
    GIVEN {
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE | AI_FLAG_CHECK_VIABILITY | AI_FLAG_TRY_TO_FAINT | AI_FLAG_SMART_MON_CHOICES);
        PLAYER(SPECIES_SWELLOW) { Level(30); Moves(MOVE_WING_ATTACK, MOVE_BOOMBURST); Speed(5); }
        OPPONENT(SPECIES_PONYTA) { Level(1); Moves(MOVE_NONE); Speed(4); } // Forces switchout
        OPPONENT(SPECIES_ARON) { Level(30); Moves(MOVE_HEADBUTT); Speed(4); } // Mid battle, AI sends out Aron
        OPPONENT(SPECIES_ELECTRODE) { Level(30); Moves(MOVE_CHARGE_BEAM); Speed(6); }
    } WHEN {
            TURN { MOVE(player, MOVE_WING_ATTACK) ; EXPECT_SWITCH(opponent, 1); }
    }
}

AI_SINGLE_BATTLE_TEST("AI_FLAG_SMART_MON_CHOICES: Post-KO switches prioritize offensive options")
{
    GIVEN {
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE | AI_FLAG_CHECK_VIABILITY | AI_FLAG_TRY_TO_FAINT | AI_FLAG_SMART_MON_CHOICES);
        PLAYER(SPECIES_SWELLOW) { Level(30); Moves(MOVE_WING_ATTACK, MOVE_BOOMBURST); Speed(5); }
        OPPONENT(SPECIES_PONYTA) { Level(1); Moves(MOVE_TACKLE); Speed(4); }
        OPPONENT(SPECIES_ARON) { Level(30); Moves(MOVE_HEADBUTT); Speed(4); } // Mid battle, AI sends out Aron
        OPPONENT(SPECIES_ELECTRODE) { Level(30); Moves(MOVE_CHARGE_BEAM); Speed(6); }
    } WHEN {
            TURN { MOVE(player, MOVE_WING_ATTACK) ; EXPECT_SEND_OUT(opponent, 2); }
    }
}

AI_SINGLE_BATTLE_TEST("AI_FLAG_SMART_SWITCHING: AI switches out after sufficient stat drops")
{
    GIVEN {
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE | AI_FLAG_CHECK_VIABILITY | AI_FLAG_TRY_TO_FAINT | AI_FLAG_SMART_SWITCHING);
        PLAYER(SPECIES_HITMONTOP) { Level(30); Moves(MOVE_CHARM, MOVE_TACKLE); Ability(ABILITY_INTIMIDATE); Speed(5); }
        OPPONENT(SPECIES_GRIMER) { Level(30); Moves(MOVE_TACKLE); Speed(4); }
        OPPONENT(SPECIES_PONYTA) { Level(30); Moves(MOVE_HEADBUTT); Speed(4); }
    } WHEN {
            TURN { MOVE(player, MOVE_CHARM) ;}
            TURN { MOVE(player, MOVE_TACKLE) ; EXPECT_SWITCH(opponent, 1); }
    }
}

AI_SINGLE_BATTLE_TEST("AI_FLAG_SMART_SWITCHING: AI will not switch out if Pokemon would faint to hazards unless party member can clear them")
{
    u32 move1;

    PARAMETRIZE{move1 = MOVE_TACKLE; }
    PARAMETRIZE{move1 = MOVE_RAPID_SPIN; }

    GIVEN {
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE | AI_FLAG_CHECK_VIABILITY | AI_FLAG_TRY_TO_FAINT | AI_FLAG_SMART_SWITCHING);
        PLAYER(SPECIES_HITMONTOP) { Level(30); Moves(MOVE_CHARM, MOVE_TACKLE, MOVE_STEALTH_ROCK, MOVE_EARTHQUAKE); Ability(ABILITY_INTIMIDATE); Speed(5); }
        OPPONENT(SPECIES_GRIMER) { Level(30); Moves(MOVE_TACKLE); Item(ITEM_FOCUS_SASH); Speed(4); }
        OPPONENT(SPECIES_PONYTA) { Level(30); Moves(MOVE_HEADBUTT, move1); Speed(4); }
    } WHEN {
            TURN { MOVE(player, MOVE_STEALTH_ROCK) ;}
            TURN { MOVE(player, MOVE_EARTHQUAKE) ;}
            TURN { MOVE(player, MOVE_CHARM) ;}
            TURN { // If the AI has a mon that can remove hazards, don't prevent them switching out
                MOVE(player, MOVE_CHARM);
                if (move1 == MOVE_RAPID_SPIN)
                    EXPECT_SWITCH(opponent, 1);
                else if (move1 == MOVE_TACKLE)
                    EXPECT_MOVE(opponent, MOVE_TACKLE);
            }
    }
}

AI_DOUBLE_BATTLE_TEST("AI will not try to switch for the same pokemon for 2 spots in a double battle")
{
    u32 flags;

    PARAMETRIZE {flags = AI_FLAG_SMART_SWITCHING; }
    PARAMETRIZE {flags = 0; }

    GIVEN {
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE | AI_FLAG_CHECK_VIABILITY | AI_FLAG_TRY_TO_FAINT | flags);
        PLAYER(SPECIES_RATTATA);
        PLAYER(SPECIES_RATTATA);
        // No moves to damage player.
        OPPONENT(SPECIES_GENGAR) { Moves(MOVE_SHADOW_BALL); }
        OPPONENT(SPECIES_HAUNTER) { Moves(MOVE_SHADOW_BALL); }
        OPPONENT(SPECIES_GENGAR) { Moves(MOVE_SHADOW_BALL); }
        OPPONENT(SPECIES_RATICATE) { Moves(MOVE_HEADBUTT); }
    } WHEN {
        TURN { EXPECT_SWITCH(opponentLeft, 3); };
    } SCENE {
        MESSAGE("{PKMN} TRAINER LEAF withdrew Gengar!");
        MESSAGE("{PKMN} TRAINER LEAF sent out Raticate!");
        NONE_OF {
            MESSAGE("{PKMN} TRAINER LEAF withdrew Haunter!");
            MESSAGE("{PKMN} TRAINER LEAF sent out Raticate!");
        }
    }
}

TEST("External AI thinking status waits for player action confirmation")
{
    BattleAgent_ResetMailbox();
    BattleAgent_TestStartThinkingStatus(B_POSITION_OPPONENT_LEFT);

    BattleAgent_TestUpdateThinkingStatus(B_POSITION_OPPONENT_LEFT, FALSE, TRUE);
    EXPECT_EQ(BattleAgent_TestGetThinkingStatus(B_POSITION_OPPONENT_LEFT), BATTLE_AGENT_THINKING_HIDDEN);

    BattleAgent_TestUpdateThinkingStatus(B_POSITION_OPPONENT_LEFT, TRUE, TRUE);
    EXPECT_EQ(BattleAgent_TestGetThinkingStatus(B_POSITION_OPPONENT_LEFT), BATTLE_AGENT_THINKING_TWO_DOTS);
    EXPECT_EQ(BattleAgent_TestGetThinkingStatusFrames(B_POSITION_OPPONENT_LEFT), 0);
}

TEST("External AI thinking status waits for an idle message window")
{
    BattleAgent_ResetMailbox();
    BattleAgent_TestStartThinkingStatus(B_POSITION_OPPONENT_LEFT);

    BattleAgent_TestUpdateThinkingStatus(B_POSITION_OPPONENT_LEFT, TRUE, FALSE);
    EXPECT_EQ(BattleAgent_TestGetThinkingStatus(B_POSITION_OPPONENT_LEFT), BATTLE_AGENT_THINKING_HIDDEN);

    BattleAgent_TestUpdateThinkingStatus(B_POSITION_OPPONENT_LEFT, TRUE, TRUE);
    EXPECT_EQ(BattleAgent_TestGetThinkingStatus(B_POSITION_OPPONENT_LEFT), BATTLE_AGENT_THINKING_TWO_DOTS);
}

TEST("External AI thinking status keeps a fixed two-dot message")
{
    u32 frame;

    BattleAgent_ResetMailbox();
    BattleAgent_TestStartThinkingStatus(B_POSITION_OPPONENT_LEFT);
    BattleAgent_TestUpdateThinkingStatus(B_POSITION_OPPONENT_LEFT, TRUE, TRUE);
    for (frame = 0; frame < BATTLE_AGENT_THINKING_DOT_INTERVAL * 2; frame++)
        BattleAgent_TestUpdateThinkingStatus(B_POSITION_OPPONENT_LEFT, TRUE, TRUE);
    EXPECT_EQ(BattleAgent_TestGetThinkingStatus(B_POSITION_OPPONENT_LEFT), BATTLE_AGENT_THINKING_TWO_DOTS);
    EXPECT_EQ(BattleAgent_TestGetThinkingStatusFrames(B_POSITION_OPPONENT_LEFT), 0);
}

TEST("External AI thinking status cleanup resets a completed wait")
{
    BattleAgent_ResetMailbox();
    BattleAgent_TestStartThinkingStatus(B_POSITION_OPPONENT_LEFT);
    BattleAgent_TestUpdateThinkingStatus(B_POSITION_OPPONENT_LEFT, TRUE, TRUE);
    BattleAgent_ClearThinkingStatus(B_POSITION_OPPONENT_LEFT);

    EXPECT_EQ(BattleAgent_TestGetThinkingStatus(B_POSITION_OPPONENT_LEFT), BATTLE_AGENT_THINKING_HIDDEN);
    EXPECT_EQ(BattleAgent_TestGetThinkingStatusFrames(B_POSITION_OPPONENT_LEFT), 0);
    BattleAgent_ClearThinkingStatus(B_POSITION_OPPONENT_LEFT);
    EXPECT_EQ(BattleAgent_TestGetThinkingStatus(B_POSITION_OPPONENT_LEFT), BATTLE_AGENT_THINKING_HIDDEN);
}

TEST("External AI thinking status starts fresh after a previous wait")
{
    BattleAgent_ResetMailbox();
    BattleAgent_TestStartThinkingStatus(B_POSITION_OPPONENT_LEFT);
    BattleAgent_TestUpdateThinkingStatus(B_POSITION_OPPONENT_LEFT, TRUE, TRUE);
    BattleAgent_ClearThinkingStatus(B_POSITION_OPPONENT_LEFT);
    BattleAgent_TestStartThinkingStatus(B_POSITION_OPPONENT_LEFT);
    BattleAgent_TestUpdateThinkingStatus(B_POSITION_OPPONENT_LEFT, TRUE, TRUE);

    EXPECT_EQ(BattleAgent_TestGetThinkingStatus(B_POSITION_OPPONENT_LEFT), BATTLE_AGENT_THINKING_TWO_DOTS);
    EXPECT_EQ(BattleAgent_TestGetThinkingStatusFrames(B_POSITION_OPPONENT_LEFT), 0);
}

TEST("External AI thinking status shows the normal message panel")
{
    BattleAgent_ResetMailbox();
    BattleAgent_TestStartThinkingStatus(B_POSITION_OPPONENT_LEFT);
    gBattle_BG0_X = 24;
    gBattle_BG0_Y = DISPLAY_HEIGHT * 2;

    BattleAgent_UpdateThinkingStatus(B_POSITION_OPPONENT_LEFT, TRUE);

    EXPECT_EQ(gBattle_BG0_X, 0);
    EXPECT_EQ(gBattle_BG0_Y, 0);
    BattleAgent_ClearThinkingStatus(B_POSITION_OPPONENT_LEFT);
}

AI_SINGLE_BATTLE_TEST("External AI mock accepts Calvin's legal move slot")
{
    GIVEN {
        RESET_EXTERNAL_AI_MOCK();
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE);
        TRAINER_OPPONENT(TRAINER_CALVIN_1);
        EXTERNAL_AI_MOCK_MOVE(1);
        PLAYER(SPECIES_GASTLY) { Moves(MOVE_MEAN_LOOK); }
        OPPONENT(SPECIES_LILLIPUP) { Moves(MOVE_LEER, MOVE_TACKLE); }
    } WHEN {
        TURN {
            MOVE(player, MOVE_MEAN_LOOK);
            EXPECT_AGENT_REQUEST(1, 2);
            EXPECT_MOVE(opponent, MOVE_TACKLE, target:player);
        }
    }
}

AI_SINGLE_BATTLE_TEST("External AI publishes and applies a response for a formerly untagged trainer")
{
    GIVEN {
        RESET_EXTERNAL_AI_MOCK();
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE);
        TRAINER_OPPONENT(TRAINER_RICKY_1);
        EXTERNAL_AI_MOCK_MOVE(1);
        PLAYER(SPECIES_GASTLY) { Moves(MOVE_MEAN_LOOK); }
        OPPONENT(SPECIES_LILLIPUP) { Moves(MOVE_LEER, MOVE_TACKLE); }
    } WHEN {
        TURN {
            MOVE(player, MOVE_MEAN_LOOK);
            EXPECT_AGENT_REQUEST(1, 2);
            EXPECT_AGENT_ACTION(0, 0, B_POSITION_PLAYER_LEFT);
            EXPECT_AGENT_ACTION(1, 1, B_POSITION_PLAYER_LEFT);
            EXPECT_MOVE(opponent, MOVE_TACKLE, target:player);
        }
    }
}

TEST("External AI mailbox uses protocol V3")
{
    EXPECT(BATTLE_AGENT_PROTOCOL_VERSION == 3);
}

AI_SINGLE_BATTLE_TEST("External AI V3 publishes party data and applies a legal voluntary switch")
{
    GIVEN {
        RESET_EXTERNAL_AI_MOCK();
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE);
        TRAINER_OPPONENT(TRAINER_CALVIN_1);
        PLAYER(SPECIES_GASTLY) { Moves(MOVE_GROWL); }
        OPPONENT(SPECIES_LILLIPUP) { MaxHP(100); HP(80); Moves(MOVE_LEER); }
        OPPONENT(SPECIES_POOCHYENA) { MaxHP(80); HP(70); Moves(MOVE_TACKLE); }
    } WHEN {
        TURN {
            MOVE(player, MOVE_GROWL);
            EXPECT_AGENT_REQUEST(1, 2);
            EXPECT_AGENT_ACTION(0, 0, B_POSITION_PLAYER_LEFT);
            EXPECT_AGENT_SWITCH_ACTION(1, 1);
            SET_AGENT_TEST_RESPONSE(1, 1);
            EXPECT_SWITCH(opponent, 1);
        }
    } THEN {
        EXPECT_EQ(gBattleAgentMailbox.snapshot.party[0].battler.species, SPECIES_LILLIPUP);
        EXPECT_EQ(gBattleAgentMailbox.snapshot.party[0].battler.hp, GetMonData(&gEnemyParty[0], MON_DATA_HP));
        EXPECT_EQ(gBattleAgentMailbox.snapshot.party[1].battler.species, SPECIES_POOCHYENA);
        EXPECT_EQ(gBattleAgentMailbox.snapshot.party[1].battler.hp, GetMonData(&gEnemyParty[1], MON_DATA_HP));
        EXPECT_EQ(gBattleAgentMailbox.snapshot.party[1].isUsable, TRUE);
    }
}

AI_SINGLE_BATTLE_TEST("External AI V3 does not publish a voluntary action while locked")
{
    u8 originalMoveOrAction;

    GIVEN {
        RESET_EXTERNAL_AI_MOCK();
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE);
        TRAINER_OPPONENT(TRAINER_CALVIN_1);
        PLAYER(SPECIES_GASTLY) { Moves(MOVE_GROWL); }
        OPPONENT(SPECIES_LILLIPUP) { Moves(MOVE_LEER); }
        OPPONENT(SPECIES_POOCHYENA) { Moves(MOVE_TACKLE); }
    } WHEN {
        TURN { MOVE(player, MOVE_GROWL); EXPECT_MOVE(opponent, MOVE_LEER); }
    } THEN {
        originalMoveOrAction = gBattleStruct->aiMoveOrAction[B_POSITION_OPPONENT_LEFT];
        BattleAgent_ResetMailbox();
        gBattleMons[B_POSITION_OPPONENT_LEFT].status2 |= STATUS2_RECHARGE;
        gBattleStruct->aiMoveOrAction[B_POSITION_OPPONENT_LEFT] = 0;
        EXPECT_EQ(BattleAgent_TryPublishRequest(B_POSITION_OPPONENT_LEFT), FALSE);
        EXPECT_EQ(gBattleAgentMailbox.requestStatus, BATTLE_AGENT_REQUEST_IDLE);
        gBattleMons[B_POSITION_OPPONENT_LEFT].status2 &= ~STATUS2_RECHARGE;
        gBattleStruct->aiMoveOrAction[B_POSITION_OPPONENT_LEFT] = originalMoveOrAction;
    }
}

AI_SINGLE_BATTLE_TEST("External AI V3 rejects a reserve that faints while it waits")
{
    u16 originalReserveHp;
    u16 zero = 0;
    u32 originalMoveOrAction;
    u32 originalTarget;
    u32 requestSequence;

    GIVEN {
        RESET_EXTERNAL_AI_MOCK();
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE);
        TRAINER_OPPONENT(TRAINER_CALVIN_1);
        PLAYER(SPECIES_GASTLY) { Moves(MOVE_GROWL); }
        OPPONENT(SPECIES_LILLIPUP) { Moves(MOVE_LEER); }
        OPPONENT(SPECIES_POOCHYENA) { Moves(MOVE_TACKLE); }
    } WHEN {
        TURN { MOVE(player, MOVE_GROWL); EXPECT_MOVE(opponent, MOVE_LEER); }
    } THEN {
        originalMoveOrAction = gBattleStruct->aiMoveOrAction[B_POSITION_OPPONENT_LEFT];
        originalTarget = gBattleStruct->aiChosenTarget[B_POSITION_OPPONENT_LEFT];
        originalReserveHp = GetMonData(&gEnemyParty[1], MON_DATA_HP);
        BattleAgent_ResetMailbox();
        gBattleStruct->aiMoveOrAction[B_POSITION_OPPONENT_LEFT] = 0;
        gBattleStruct->AI_monToSwitchIntoId[B_POSITION_OPPONENT_LEFT] = PARTY_SIZE;
        EXPECT_EQ(BattleAgent_BeginExternalWait(B_POSITION_OPPONENT_LEFT), TRUE);
        requestSequence = gBattleAgentMailbox.requestSequence;
        SetMonData(&gEnemyParty[1], MON_DATA_HP, &zero);
        gBattleAgentMailbox.responseSequence = requestSequence;
        gBattleAgentMailbox.responseLegalActionIndex = 1;
        gBattleAgentMailbox.responseStatus = BATTLE_AGENT_RESPONSE_READY;
        EXPECT_EQ(BattleAgent_TryConsumeResponse(B_POSITION_OPPONENT_LEFT), FALSE);
        EXPECT_EQ(gBattleStruct->AI_monToSwitchIntoId[B_POSITION_OPPONENT_LEFT], PARTY_SIZE);
        BattleAgent_UseVanillaFallback(B_POSITION_OPPONENT_LEFT);
        EXPECT_EQ(gBattleStruct->aiMoveOrAction[B_POSITION_OPPONENT_LEFT], 0);
        SetMonData(&gEnemyParty[1], MON_DATA_HP, &originalReserveHp);
        gBattleStruct->aiMoveOrAction[B_POSITION_OPPONENT_LEFT] = originalMoveOrAction;
        gBattleStruct->aiChosenTarget[B_POSITION_OPPONENT_LEFT] = originalTarget;
    }
}

AI_SINGLE_BATTLE_TEST("External AI Calvin without a response keeps vanilla move")
{
    GIVEN {
        RESET_EXTERNAL_AI_MOCK();
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE);
        TRAINER_OPPONENT(TRAINER_CALVIN_1);
        PLAYER(SPECIES_GASTLY) { Moves(MOVE_MEAN_LOOK); }
        OPPONENT(SPECIES_LILLIPUP) { Moves(MOVE_LEER, MOVE_TACKLE); }
    } WHEN {
        TURN { MOVE(player, MOVE_MEAN_LOOK); EXPECT_MOVE(opponent, MOVE_LEER); }
    }
}

AI_SINGLE_BATTLE_TEST("External AI V2 response applies a current legal action")
{
    GIVEN {
        RESET_EXTERNAL_AI_MOCK();
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE);
        TRAINER_OPPONENT(TRAINER_CALVIN_1);
        PLAYER(SPECIES_GASTLY) { Moves(MOVE_MEAN_LOOK); }
        OPPONENT(SPECIES_LILLIPUP) { Moves(MOVE_LEER, MOVE_TACKLE); }
    } WHEN {
        TURN {
            MOVE(player, MOVE_MEAN_LOOK);
            EXPECT_AGENT_REQUEST(1, 2);
            SET_AGENT_TEST_RESPONSE(1, 1);
            EXPECT_MOVE(opponent, MOVE_TACKLE, target:player);
        }
    }
}

AI_SINGLE_BATTLE_TEST("External AI snapshot publishes Calvin's legal move actions")
{
    GIVEN {
        RESET_EXTERNAL_AI_MOCK();
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE);
        TRAINER_OPPONENT(TRAINER_CALVIN_1);
        PLAYER(SPECIES_GASTLY) { Moves(MOVE_MEAN_LOOK); }
        OPPONENT(SPECIES_LILLIPUP) { Moves(MOVE_LEER, MOVE_TACKLE, MOVE_REST); }
    } WHEN {
        TURN {
            MOVE(player, MOVE_MEAN_LOOK);
            EXPECT_AGENT_REQUEST(1, 3);
            EXPECT_MOVE(opponent, MOVE_LEER, target:player);
        }
    }
}

AI_SINGLE_BATTLE_TEST("External AI snapshot replaces stale request")
{
    GIVEN {
        RESET_EXTERNAL_AI_MOCK();
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE);
        TRAINER_OPPONENT(TRAINER_CALVIN_1);
        PLAYER(SPECIES_GASTLY) { Moves(MOVE_MEAN_LOOK, MOVE_DISABLE, MOVE_GROWL); }
        OPPONENT(SPECIES_LILLIPUP) { Moves(MOVE_LEER, MOVE_TACKLE); }
    } WHEN {
        TURN {
            MOVE(player, MOVE_MEAN_LOOK);
            EXPECT_AGENT_REQUEST(1, 2);
            EXPECT_MOVE(opponent, MOVE_LEER, target:player);
        }
        TURN {
            MOVE(player, MOVE_DISABLE);
            EXPECT_AGENT_REQUEST(2, 2);
            SET_AGENT_TEST_RESPONSE(123, 3);
            EXPECT_MOVE(opponent, MOVE_LEER, target:player);
        }
        TURN {
            MOVE(player, MOVE_GROWL);
            EXPECT_AGENT_REQUEST(3, 1);
            EXPECT_AGENT_ACTION(0, 1, B_POSITION_PLAYER_LEFT);
            EXPECT_AGENT_EMPTY_ACTION(1);
            EXPECT_MOVE(opponent, MOVE_TACKLE, target:player);
        }
    }
}

AI_SINGLE_BATTLE_TEST("External AI snapshot includes selected and self targets")
{
    GIVEN {
        RESET_EXTERNAL_AI_MOCK();
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE);
        TRAINER_OPPONENT(TRAINER_CALVIN_1);
        PLAYER(SPECIES_GASTLY) { Moves(MOVE_MEAN_LOOK); }
        OPPONENT(SPECIES_LILLIPUP) { Moves(MOVE_LEER, MOVE_TACKLE, MOVE_REST); }
    } WHEN {
        TURN {
            MOVE(player, MOVE_MEAN_LOOK);
            EXPECT_AGENT_REQUEST(1, 3);
            EXPECT_AGENT_ACTION(0, 0, B_POSITION_PLAYER_LEFT);
            EXPECT_AGENT_ACTION(1, 1, B_POSITION_PLAYER_LEFT);
            EXPECT_AGENT_ACTION(2, 2, B_POSITION_OPPONENT_LEFT);
            EXPECT_MOVE(opponent, MOVE_LEER);
        }
    }
}

AI_SINGLE_BATTLE_TEST("External AI snapshot copies seeded visible battle state")
{
    GIVEN {
        RESET_EXTERNAL_AI_MOCK();
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE);
        TRAINER_OPPONENT(TRAINER_CALVIN_1);
        PLAYER(SPECIES_GASTLY) {
            MaxHP(120);
            HP(90);
            Moves(MOVE_GROWL);
        }
        OPPONENT(SPECIES_LILLIPUP) {
            MaxHP(140);
            HP(100);
            Status1(STATUS1_POISON);
            MovesWithPP(
                ((struct moveWithPP){ .moveId = MOVE_LEER, .pp = 5 }),
                ((struct moveWithPP){ .moveId = MOVE_TACKLE, .pp = 9 }),
                ((struct moveWithPP){ .moveId = MOVE_REST, .pp = 3 }));
        }
    } WHEN {
        TURN {
            MOVE(player, MOVE_GROWL);
            EXPECT_AGENT_REQUEST(1, 3);
            EXPECT_AGENT_BATTLER(B_POSITION_PLAYER_LEFT, SPECIES_GASTLY, 90, 120, STATUS1_NONE);
            EXPECT_AGENT_BATTLER(B_POSITION_OPPONENT_LEFT, SPECIES_LILLIPUP, 100, 140, STATUS1_POISON);
            EXPECT_AGENT_REQUESTER_MOVE(0, MOVE_LEER, 5);
            EXPECT_AGENT_REQUESTER_MOVE(1, MOVE_TACKLE, 9);
            EXPECT_AGENT_REQUESTER_MOVE(2, MOVE_REST, 3);
            EXPECT_AGENT_ENVIRONMENT(B_WEATHER_NONE, BATTLE_TERRAIN_BUILDING, 0, 0, 0);
            EXPECT_MOVE(opponent, MOVE_LEER);
        }
    }
}

AI_SINGLE_BATTLE_TEST("External AI snapshot excludes empty and zero-PP move slots")
{
    GIVEN {
        RESET_EXTERNAL_AI_MOCK();
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE);
        TRAINER_OPPONENT(TRAINER_CALVIN_1);
        PLAYER(SPECIES_GASTLY) { Moves(MOVE_MEAN_LOOK); }
        OPPONENT(SPECIES_LILLIPUP) {
            MovesWithPP(
                ((struct moveWithPP){ .moveId = MOVE_LEER, .pp = 40 }),
                ((struct moveWithPP){ .moveId = MOVE_TACKLE, .pp = 0 }),
                ((struct moveWithPP){ .moveId = MOVE_NONE, .pp = 0 }));
        }
    } WHEN {
        TURN {
            MOVE(player, MOVE_MEAN_LOOK);
            EXPECT_AGENT_REQUEST(1, 1);
            EXPECT_AGENT_ACTION(0, 0, B_POSITION_PLAYER_LEFT);
            EXPECT_MOVE(opponent, MOVE_LEER);
        }
    }
}

AI_SINGLE_BATTLE_TEST("External AI snapshot publishes an empty legal list for a valid fallback")
{
    GIVEN {
        RESET_EXTERNAL_AI_MOCK();
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE);
        TRAINER_OPPONENT(TRAINER_CALVIN_1);
        PLAYER(SPECIES_GASTLY) { Moves(MOVE_MEAN_LOOK); }
        OPPONENT(SPECIES_LILLIPUP) { Moves(MOVE_PERISH_SONG); }
    } WHEN {
        TURN {
            MOVE(player, MOVE_MEAN_LOOK);
            EXPECT_AGENT_REQUEST(1, 0);
            EXPECT_MOVE(opponent, MOVE_PERISH_SONG);
        }
    }
}

AI_SINGLE_BATTLE_TEST("External AI snapshot preserves a pending request in excluded battles")
{
    u32 excludedIndex;
    u32 action;
    u32 battleTypeFlags;
    static const u32 sExcludedFlags[] = {
        BATTLE_TYPE_DOUBLE, BATTLE_TYPE_MULTI, BATTLE_TYPE_LINK, BATTLE_TYPE_SAFARI,
        BATTLE_TYPE_PALACE, BATTLE_TYPE_BATTLE_TOWER, BATTLE_TYPE_DOME, BATTLE_TYPE_ARENA,
        BATTLE_TYPE_FACTORY, BATTLE_TYPE_PIKE, BATTLE_TYPE_PYRAMID, BATTLE_TYPE_FRONTIER,
        BATTLE_TYPE_EREADER_TRAINER,
        BATTLE_TYPE_TRAINER_HILL, BATTLE_TYPE_SECRET_BASE, BATTLE_TYPE_TWO_OPPONENTS,
    };

    GIVEN {
        RESET_EXTERNAL_AI_MOCK();
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE);
        TRAINER_OPPONENT(TRAINER_CALVIN_1);
        PLAYER(SPECIES_GASTLY) { Moves(MOVE_MEAN_LOOK); }
        OPPONENT(SPECIES_LILLIPUP) { Moves(MOVE_LEER); }
    } WHEN {
        TURN { MOVE(player, MOVE_MEAN_LOOK); EXPECT_MOVE(opponent, MOVE_LEER); }
    } THEN {
        action = gBattleStruct->aiMoveOrAction[B_POSITION_OPPONENT_LEFT];
        battleTypeFlags = gBattleTypeFlags;
        for (excludedIndex = 0; excludedIndex < ARRAY_COUNT(sExcludedFlags); excludedIndex++) {
            BattleAgent_ResetMailbox();
            gBattleAgentMailbox.requestStatus = BATTLE_AGENT_REQUEST_PENDING;
            gBattleAgentMailbox.requestSequence = 7;
            gBattleAgentMailbox.requestingBattler = B_POSITION_OPPONENT_LEFT;
            gBattleAgentMailbox.battleMode = BATTLE_AGENT_BATTLE_MODE_TRAINER_SINGLE;
            gBattleAgentMailbox.turnSequence = 7;
            gBattleAgentMailbox.legalActionCount = 1;
            gBattleTypeFlags = battleTypeFlags | sExcludedFlags[excludedIndex];
            EXPECT_EQ(BattleAgent_TryPublishRequest(B_POSITION_OPPONENT_LEFT), FALSE);
            EXPECT_EQ(gBattleAgentMailbox.requestStatus, BATTLE_AGENT_REQUEST_PENDING);
            EXPECT_EQ(gBattleAgentMailbox.requestSequence, 7);
        }
        gBattleTypeFlags = battleTypeFlags;
        gBattleStruct->aiMoveOrAction[B_POSITION_OPPONENT_LEFT] = action;
    }
}

AI_SINGLE_BATTLE_TEST("External AI snapshot preserves a pending request for a non-move fallback")
{
    u32 fallback;

    GIVEN {
        RESET_EXTERNAL_AI_MOCK();
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE);
        TRAINER_OPPONENT(TRAINER_CALVIN_1);
        PLAYER(SPECIES_GASTLY) { Moves(MOVE_MEAN_LOOK); }
        OPPONENT(SPECIES_LILLIPUP) { Moves(MOVE_LEER); }
    } WHEN {
        TURN { MOVE(player, MOVE_MEAN_LOOK); EXPECT_MOVE(opponent, MOVE_LEER); }
    } THEN {
        fallback = gBattleStruct->aiMoveOrAction[B_POSITION_OPPONENT_LEFT];
        BattleAgent_ResetMailbox();
        gBattleAgentMailbox.requestStatus = BATTLE_AGENT_REQUEST_PENDING;
        gBattleAgentMailbox.requestSequence = 7;
        gBattleAgentMailbox.requestingBattler = B_POSITION_OPPONENT_LEFT;
        gBattleAgentMailbox.battleMode = BATTLE_AGENT_BATTLE_MODE_TRAINER_SINGLE;
        gBattleAgentMailbox.turnSequence = 7;
        gBattleAgentMailbox.legalActionCount = 1;
        gBattleStruct->aiMoveOrAction[B_POSITION_OPPONENT_LEFT] = AI_CHOICE_SWITCH;
        EXPECT_EQ(BattleAgent_TryPublishRequest(B_POSITION_OPPONENT_LEFT), FALSE);
        EXPECT_EQ(gBattleAgentMailbox.requestStatus, BATTLE_AGENT_REQUEST_PENDING);
        EXPECT_EQ(gBattleAgentMailbox.requestSequence, 7);
        gBattleStruct->aiMoveOrAction[B_POSITION_OPPONENT_LEFT] = fallback;
    }
}

TEST("External AI snapshot rejects a fainted selected target")
{
    u8 target;
    u8 battlersCount = gBattlersCount;
    u8 absentBattlerFlags = gAbsentBattlerFlags;
    u8 playerPosition = gBattlerPositions[B_POSITION_PLAYER_LEFT];
    u8 opponentPosition = gBattlerPositions[B_POSITION_OPPONENT_LEFT];
    u16 playerHp = gBattleMons[B_POSITION_PLAYER_LEFT].hp;

    gBattlersCount = 2;
    gAbsentBattlerFlags = 0;
    gBattlerPositions[B_POSITION_PLAYER_LEFT] = B_POSITION_PLAYER_LEFT;
    gBattlerPositions[B_POSITION_OPPONENT_LEFT] = B_POSITION_OPPONENT_LEFT;
    gBattleMons[B_POSITION_PLAYER_LEFT].hp = 0;

    EXPECT_EQ(BattleAgent_TestNormalizeSingleTarget(B_POSITION_OPPONENT_LEFT, MOVE_LEER, &target), FALSE);

    gBattleMons[B_POSITION_PLAYER_LEFT].hp = playerHp;
    gBattlerPositions[B_POSITION_OPPONENT_LEFT] = opponentPosition;
    gBattlerPositions[B_POSITION_PLAYER_LEFT] = playerPosition;
    gAbsentBattlerFlags = absentBattlerFlags;
    gBattlersCount = battlersCount;
}

AI_SINGLE_BATTLE_TEST("External AI Calvin rejects a zero-PP mock move")
{
    GIVEN {
        RESET_EXTERNAL_AI_MOCK();
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE);
        TRAINER_OPPONENT(TRAINER_CALVIN_1);
        EXTERNAL_AI_MOCK_MOVE(1);
        PLAYER(SPECIES_GASTLY) { Moves(MOVE_MEAN_LOOK); }
        OPPONENT(SPECIES_LILLIPUP) {
            MovesWithPP(
                ((struct moveWithPP){ .moveId = MOVE_LEER, .pp = 40 }),
                ((struct moveWithPP){ .moveId = MOVE_TACKLE, .pp = 0 }));
        }
    } WHEN {
        TURN { MOVE(player, MOVE_MEAN_LOOK); EXPECT_MOVE(opponent, MOVE_LEER); }
    }
}

AI_SINGLE_BATTLE_TEST("External AI Calvin rejects an out-of-range mock move")
{
    GIVEN {
        RESET_EXTERNAL_AI_MOCK();
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE);
        TRAINER_OPPONENT(TRAINER_CALVIN_1);
        EXTERNAL_AI_MOCK_MOVE(MAX_MON_MOVES);
        PLAYER(SPECIES_GASTLY) { Moves(MOVE_MEAN_LOOK); }
        OPPONENT(SPECIES_LILLIPUP) { Moves(MOVE_LEER, MOVE_TACKLE); }
    } WHEN {
        TURN { MOVE(player, MOVE_MEAN_LOOK); EXPECT_MOVE(opponent, MOVE_LEER); }
    }
}

AI_SINGLE_BATTLE_TEST("External AI Calvin rejects an empty mock move")
{
    GIVEN {
        RESET_EXTERNAL_AI_MOCK();
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE);
        TRAINER_OPPONENT(TRAINER_CALVIN_1);
        EXTERNAL_AI_MOCK_MOVE(2);
        PLAYER(SPECIES_GASTLY) { Moves(MOVE_MEAN_LOOK); }
        OPPONENT(SPECIES_LILLIPUP) { Moves(MOVE_LEER, MOVE_TACKLE, MOVE_NONE); }
    } WHEN {
        TURN { MOVE(player, MOVE_MEAN_LOOK); EXPECT_MOVE(opponent, MOVE_LEER); }
    }
}

AI_SINGLE_BATTLE_TEST("External AI Calvin rejects a self-targeting mock move")
{
    GIVEN {
        RESET_EXTERNAL_AI_MOCK();
        AI_FLAGS(AI_FLAG_CHECK_BAD_MOVE);
        TRAINER_OPPONENT(TRAINER_CALVIN_1);
        EXTERNAL_AI_MOCK_MOVE(1);
        PLAYER(SPECIES_GASTLY) { Moves(MOVE_MEAN_LOOK); }
        OPPONENT(SPECIES_LILLIPUP) { Moves(MOVE_LEER, MOVE_REST); }
    } WHEN {
        TURN { MOVE(player, MOVE_MEAN_LOOK); EXPECT_MOVE(opponent, MOVE_LEER); }
    }
}
