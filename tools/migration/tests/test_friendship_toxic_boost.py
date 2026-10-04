"""Bounded balance regression using actual native C, not a recreated engine.

Run in WSL: python3 -m unittest tools.migration.tests.test_friendship_toxic_boost -v.
Native cc is mandatory; missing tools fail instead of silently skipping coverage.
"""

import ctypes
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = "f5e81e85df6fe40ae490bf7268d0186d7f0426ed"
PRE_UNIT = "0758db1dc4"


def source(path, ref=None):
    if ref:
        return subprocess.check_output(["git", "show", f"{ref}:{path}"], cwd=ROOT, text=True)
    return (ROOT / path).read_text()


def function(text, name):
    match = re.search(r"^(?:static inline |static )?[\w *]+\b" + name + r"\([^;{}]*\)\s*\{", text, re.M)
    if not match:
        raise AssertionError(f"Missing actual function {name}")
    end, depth = match.end(), 1
    while depth:
        depth += (text[end] == "{") - (text[end] == "}")
        end += 1
    return text[match.start():end] + "\n"


def enum(text, name):
    return re.search(r"enum (?:__attribute__\(\(packed\)\) )?" + name + r"\s*\{[^}]+\};", text).group(0) + "\n"


def define(text, name):
    return re.search(r"^\s*#define " + name + r"\b[^\n]*(?:\\\n[^\n]*)*", text, re.M).group(0).strip() + "\n"


def condition_case(text, name):
    start = text.index("        case " + name + ":", text.index("bool32 DoesMonMeetAdditionalConditions"))
    end = text.find("        case ", start + 1)
    return text[start:end].split("        // Gen ")[0]


class FriendshipToxicBoostTests(unittest.TestCase):
    @classmethod
    def compile(cls, name, text):
        path, library = cls.directory / (name + ".c"), cls.directory / (name + ".so")
        path.write_text(text)
        result = subprocess.run(["cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-shared", "-fPIC",
                                 "-I", str(ROOT / "include"), str(path), "-o", str(library)],
                                text=True, capture_output=True)
        if result.returncode:
            raise AssertionError(f"Native fixture compilation failed ({name}):\n{result.stderr}")
        return ctypes.CDLL(str(library))

    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="friendship-toxic-")
        cls.directory = Path(cls.temp.name)
        cls.addClassCleanup(cls.temp.cleanup)
        pokemon = source("src/pokemon.c")
        constants = source("include/constants/pokemon.h")
        general = source("include/config/general.h")
        cls.preamble = "#include <stdint.h>\n#include <string.h>\ntypedef uint8_t u8;\ntypedef uint32_t u32;\ntypedef int16_t s16;\ntypedef uint32_t bool32;\n#define TRUE 1\n#define FALSE 0\n"
        cls.preamble += "".join(define(general, "GEN_" + str(i)) for i in range(1, 10)) + define(general, "GEN_LATEST")
        cls.thresholds = {}
        for generation in (None, "GEN_7", "GEN_8", "GEN_LATEST"):
            text = cls.preamble + '#include "config/pokemon.h"\n'
            if generation:
                text += "#undef P_FRIENDSHIP_EVO_THRESHOLD\n#define P_FRIENDSHIP_EVO_THRESHOLD " + generation + "\n"
            text += define(pokemon, "FRIENDSHIP_EVO_THRESHOLD")
            text += enum(constants, "EvolutionConditions") + enum(constants, "Type")
            text += enum(source("include/constants/rtc.h"), "TimeOfDay")
            text += enum(source("include/pokemon.h"), "MonData")
            text += "#define MAX_MON_MOVES 4\nstruct EvolutionParam { unsigned condition, arg1; };\n"
            text += "struct Pokemon { unsigned moves[4]; };\nstatic unsigned timeOfDay;\n"
            text += "static unsigned GetTimeOfDay(void) { return timeOfDay; }\n"
            text += "static unsigned GetMonData(struct Pokemon *mon, unsigned field) { return mon->moves[field - MON_DATA_MOVE1]; }\n"
            text += "static unsigned GetMoveType(unsigned move) { return move; }\n"
            text += "unsigned Threshold(void) { return FRIENDSHIP_EVO_THRESHOLD; }\n"
            text += "unsigned Meets(unsigned friendship, unsigned threshold, unsigned condition, unsigned arg, unsigned time, unsigned moveType) {\n"
            text += "struct Pokemon pokemon = {{moveType, 0, 0, 0}}, *mon = &pokemon; unsigned i, j; timeOfDay = time;\n"
            text += "struct EvolutionParam params[2] = {{IF_MIN_FRIENDSHIP, threshold}, {condition, arg}};\n"
            text += "for (i = 0; i < 2; i++) { bool32 currentCondition = FALSE; switch (params[i].condition) {\n"
            text += "".join(condition_case(pokemon, name) for name in ("IF_MIN_FRIENDSHIP", "IF_TIME", "IF_NOT_TIME", "IF_KNOWS_MOVE_TYPE"))
            text += "default: currentCondition = TRUE; break; } if (!currentCondition) return FALSE; } return TRUE; }\n"
            lib = cls.compile("friendship_" + str(generation), text)
            lib.Meets.argtypes = [ctypes.c_uint] * 6
            cls.thresholds[generation] = lib
        cls.speed = cls.compile_speed("speed", pokemon, source("src/battle_main.c"))
        cls.previous = cls.compile_speed("previous", pokemon, source("src/battle_main.c", PRE_UNIT))

    @classmethod
    def compile_speed(cls, name, pokemon, battle):
        constants = source("include/constants/battle.h")
        speed = function(battle, "GetBattlerTotalSpeedStat")
        # Use native masks/enums and stage ratios. Only the external inputs used
        # by this function are supplied by the fixture, not the ability policy.
        text = cls.preamble + '#include "constants/abilities.h"\n#include "constants/hold_effects.h"\n#include "fpmath.h"\n#include "config/battle.h"\n'
        text += enum(constants, "BattlerId") + enum(constants, "BattleWeather")
        text += enum(source("include/battle_gimmick.h"), "Gimmick")
        text += enum(source("include/constants/pokemon.h"), "Stat")
        masks = re.findall(r"^#define (\w+)[^\n]*", constants, re.M)
        text += "".join(define(constants, mask) for mask in masks if mask.startswith(("STATUS1_", "B_WEATHER_", "SIDE_STATUS_", "STATUS_FIELD_", "BATTLE_TYPE_")))
        text += define(source("include/constants/pokemon.h"), "MAX_STAT_STAGE")
        text += "enum { " + re.search(r"SPECIES_DITTO\s*=\s*\d+", source("include/constants/species.h")).group(0) + " };\n"
        # The exact flag identity is supplied from native constants, not a made-up id.
        flags = source("include/constants/flags.h")
        opponents = source("include/constants/opponents.h")
        text += define(opponents, "MAX_TRAINERS_COUNT_EMERALD")
        text += re.findall(r"^#define MAX_TRAINERS_COUNT\s+[^\n]+", opponents, re.M)[-1] + "\n"
        text += "".join(define(flags, name) for name in ("TRAINER_FLAGS_START", "TRAINER_FLAGS_END", "SYSTEM_FLAGS", "FLAG_BADGE03_GET"))
        text += re.search(r"const u8 gStatStageRatios[^;]+;", pokemon).group(0) + "\n"
        text += r'''
struct FixtureMon { u32 speed, status1, species, ability; u8 statStages[8];
    struct { unsigned slowStartTimer, transformed, boosterEnergyActivated, unburdenActive; } volatiles; };
static struct FixtureMon gBattleMons[4];
static u32 gFieldStatuses, gBattleTypeFlags, gSideStatuses[2];
static unsigned weatherInput, badgeInput, paradoxInput, gimmickInput, badgeGen;
#define GetConfig(setting) GetConfig_##setting()
static unsigned GetConfig_B_BADGE_BOOST(void) { return badgeGen; }
static unsigned GetConfig_B_PARALYSIS_SPEED(void) { return B_PARALYSIS_SPEED; }
static u32 GetWeather(void) { return weatherInput; }
static unsigned GetParadoxBoostedStatId(enum BattlerId battler) { (void)battler; return paradoxInput; }
static unsigned ShouldGetStatBadgeBoost(unsigned flag, enum BattlerId battler) { (void)flag; (void)battler; return badgeInput; }
static unsigned GetBattlerSide(enum BattlerId battler) { return battler & 1; }
static unsigned IsOnPlayerSide(enum BattlerId battler) { return GetBattlerSide(battler) == 0; }
static unsigned GetActiveGimmick(enum BattlerId battler) { (void)battler; return gimmickInput; }
'''
        text += function(source("src/battle_util.c"), "GetBadgeBoostModifier") + speed
        names = sorted(set(re.findall(r"\b(?:ABILITY|HOLD_EFFECT|STATUS1|B_WEATHER|SIDE_STATUS|STATUS_FIELD|BATTLE_TYPE|GIMMICK|STAT)_[A-Z0-9_]+", speed)))
        names += ["STATUS1_POISON", "STATUS1_TOXIC_POISON", "STATUS1_TOXIC_COUNTER", "STATUS1_BURN", "STATUS1_SLEEP", "STATUS1_FREEZE", "STATUS1_FROSTBITE", "ABILITY_TOXIC_BOOST", "ABILITY_NONE", "HOLD_EFFECT_NONE", "B_WEATHER_RAIN_NORMAL", "B_WEATHER_SUN_NORMAL", "B_WEATHER_HAIL", "STAT_ATK", "GIMMICK_NONE"]
        text += "".join(f"unsigned Value_{value}(void) {{ return {value}; }}\n" for value in sorted(set(names)))
        text += r'''
unsigned Speed(unsigned speed, unsigned stage, unsigned status, unsigned ability, unsigned rawAbility,
               unsigned item, unsigned weather, unsigned field, unsigned side, unsigned badge,
               unsigned battleType, unsigned battler, unsigned volatiles, unsigned paradox, unsigned gimmick) {
    memset(gBattleMons, 0, sizeof(gBattleMons));
    gBattleMons[battler].speed = speed; gBattleMons[battler].statStages[STAT_SPEED] = stage;
    gBattleMons[battler].status1 = status; gBattleMons[battler].ability = rawAbility;
    gBattleMons[battler].volatiles.slowStartTimer = volatiles & 1;
    gBattleMons[battler].volatiles.transformed = (volatiles >> 1) & 1;
    gBattleMons[battler].volatiles.boosterEnergyActivated = (volatiles >> 2) & 1;
    gBattleMons[battler].volatiles.unburdenActive = (volatiles >> 3) & 1;
    gBattleMons[battler].species = SPECIES_DITTO;
    weatherInput = weather; gFieldStatuses = field; gSideStatuses[battler & 1] = side;
    badgeInput = badge != 0; badgeGen = badge == 2 ? GEN_2 : GEN_3;
    gBattleTypeFlags = battleType; paradoxInput = paradox; gimmickInput = gimmick;
    return GetBattlerTotalSpeedStat(battler, ability, item);
}
'''
        lib = cls.compile(name, text)
        lib.Speed.argtypes = [ctypes.c_uint] * 15
        return lib

    def value(self, name):
        return getattr(self.speed, "Value_" + name)()

    def calc(self, library=None, **changes):
        inputs = dict(speed=101, stage=6, status=0, ability=0, rawAbility=0, item=0, weather=0,
                      field=0, side=0, badge=0, battleType=0, battler=0, volatiles=0, paradox=self.value("STAT_SPEED"), gimmick=0)
        inputs.update(changes)
        return (library or self.speed).Speed(*inputs.values())

    def test_archive_intent_and_modern_adaptation(self):
        archive = source("src/pokemon.c", ARCHIVE)
        self.assertRegex(archive, r"#if P_FRIENDSHIP_EVO_THRESHOLD >= GEN_9\s+#define FRIENDSHIP_EVO_THRESHOLD 120\s+#else\s+#define FRIENDSHIP_EVO_THRESHOLD 220")
        self.assertIn("(speed * 130) / 100", condition := re.search(r"else if \(ability == ABILITY_TOXIC_BOOST[^\n]+\n\s*([^\n]+)", source("src/battle_main.c", ARCHIVE)).group(1))
        self.assertEqual(condition.strip(), "speed = (speed * 130) / 100;")
        for generation in (None, "GEN_8", "GEN_LATEST"):
            with self.subTest(generation=generation):
                lib = self.thresholds[generation]
                self.assertEqual(lib.Threshold(), 120)
                for friendship in (119, 120, 121):
                    self.assertEqual(lib.Meets(friendship, lib.Threshold(), 0, 0, 0, 0), friendship >= 120)
        lib = self.thresholds["GEN_7"]
        self.assertEqual(lib.Threshold(), 220)
        self.assertEqual(lib.Meets(219, lib.Threshold(), 0, 0, 0, 0), 0)
        self.assertEqual(lib.Meets(220, lib.Threshold(), 0, 0, 0, 0), 1)

    def test_native_friendship_entries_and_additional_requirements_unchanged(self):
        # Compare the real species declarations and condition handlers to the
        # pre-unit engine, including explicit numeric exceptions if present.
        for path in sorted((ROOT / "src/data/pokemon/species_info").glob("*.h")):
            relative = path.relative_to(ROOT).as_posix()
            self.assertEqual(source(relative), source(relative, PRE_UNIT), relative)
        current, old = source("src/pokemon.c"), source("src/pokemon.c", PRE_UNIT)
        for name in ("IF_MIN_FRIENDSHIP", "IF_TIME", "IF_NOT_TIME", "IF_KNOWS_MOVE_TYPE"):
            self.assertEqual(condition_case(current, name), condition_case(old, name))
        declarations = source("src/data/pokemon/species_info/gen_1_families.h")
        for target, extra in (("PIKACHU", ""), ("ESPEON", ",{IF_NOT_TIME, TIME_NIGHT}"),
                              ("UMBREON", ",{IF_TIME, TIME_NIGHT}"), ("SYLVEON", ",{IF_KNOWS_MOVE_TYPE, TYPE_FAIRY}")):
            declaration = re.search(r"SPECIES_" + target + r", CONDITIONS\(([^)]*)\)", declarations).group(1)
            self.assertEqual(re.sub(r"\s+", "", declaration), re.sub(r"\s+", "", "{IF_MIN_FRIENDSHIP, FRIENDSHIP_EVO_THRESHOLD}" + extra))
        # Compile those actual condition arguments, rather than inventing ids.
        for target, times, moves in (("ESPEON", (1, 3), (0,)), ("UMBREON", (3, 1), (0,)), ("SYLVEON", (1,), (19, 0))):
            declaration = re.search(r"SPECIES_" + target + r", CONDITIONS\(([^)]*)\)", declarations).group(1)
            text = self.preamble + enum(source("include/constants/pokemon.h"), "EvolutionConditions")
            text += enum(source("include/constants/pokemon.h"), "Type") + enum(source("include/constants/rtc.h"), "TimeOfDay")
            second = re.findall(r"\{([^}]+)\}", declaration)[1].split(",")
            lib = self.compile("args_" + target, text + f"unsigned Condition(void) {{ return {second[0]}; }}\nunsigned Arg(void) {{ return {second[1]}; }}\n")
            for time in times:
                for move in moves:
                    expected = time != 3 if target == "ESPEON" else time == 3 if target == "UMBREON" else move == 19
                    self.assertEqual(self.thresholds[None].Meets(120, 120, lib.Condition(), lib.Arg(), time, move), expected)
                    self.assertEqual(self.thresholds[None].Meets(119, 120, lib.Condition(), lib.Arg(), time, move), 0)
        self.assertEqual(function(current, "AdjustFriendship"), function(old, "AdjustFriendship"))
        self.assertEqual(source("src/battle_util.c"), source("src/battle_util.c", PRE_UNIT))

    def test_poison_speed_and_passed_effective_ability(self):
        toxic = self.value("ABILITY_TOXIC_BOOST")
        for status in (self.value("STATUS1_POISON"), self.value("STATUS1_TOXIC_POISON"), self.value("STATUS1_TOXIC_POISON") | self.value("STATUS1_TOXIC_COUNTER")):
            for speed in (0, 1, 3, 9, 99, 101, 333):
                with self.subTest(status=status, speed=speed):
                    self.assertEqual(self.calc(speed=speed, status=status, ability=toxic), speed * 130 // 100)
                    self.assertEqual(self.calc(speed=speed, status=status, rawAbility=toxic), speed)
        for name in ("STATUS1_BURN", "STATUS1_SLEEP", "STATUS1_PARALYSIS", "STATUS1_FREEZE", "STATUS1_FROSTBITE", "STATUS1_TOXIC_COUNTER"):
            self.assertEqual(self.calc(status=self.value(name), ability=toxic), self.calc(self.previous, status=self.value(name), ability=toxic))
        self.assertEqual(self.calc(ability=toxic), 101)
        # Poison boost precedes later paralysis/item/side rounding. The native
        # booster-energy fallback must not override an applicable Toxic Boost.
        poison = self.value("STATUS1_POISON")
        self.assertEqual(self.calc(status=poison | self.value("STATUS1_PARALYSIS"), ability=toxic), 65)
        self.assertEqual(self.calc(status=poison, ability=toxic, volatiles=4), 131)
        self.assertEqual(self.calc(ability=toxic, volatiles=4), self.calc(self.previous, ability=toxic, volatiles=4))
        for weather in ("B_WEATHER_RAIN_NORMAL", "B_WEATHER_SUN_NORMAL", "B_WEATHER_SANDSTORM", "B_WEATHER_HAIL"):
            self.assertEqual(self.calc(status=poison, ability=toxic, weather=self.value(weather)), 131)

    def test_native_order_truncation_items_side_effects_and_badges(self):
        toxic, poison = self.value("ABILITY_TOXIC_BOOST"), self.value("STATUS1_POISON")
        ratios = ((10, 40), (10, 15), (10, 10), (15, 10), (40, 10))
        for speed in (1, 3, 9, 101, 333):
            for stage, (numerator, denominator) in zip((0, 5, 6, 7, 12), ratios):
                for item in ("HOLD_EFFECT_NONE", "HOLD_EFFECT_CHOICE_SCARF", "HOLD_EFFECT_MACHO_BRACE", "HOLD_EFFECT_POWER_ITEM", "HOLD_EFFECT_IRON_BALL"):
                    for side in (0, self.value("SIDE_STATUS_TAILWIND"), self.value("SIDE_STATUS_SWAMP"), self.value("SIDE_STATUS_TAILWIND") | self.value("SIDE_STATUS_SWAMP")):
                        for badge in (0, 1, 2):
                            expected = speed * numerator // denominator * 130 // 100
                            if badge:
                                modifier = 4506 if badge == 1 else 4608
                                expected = (modifier * expected + 2047) // 4096
                            expected = expected * 150 // 100 if item == "HOLD_EFFECT_CHOICE_SCARF" else expected if item == "HOLD_EFFECT_NONE" else expected // 2
                            if side & self.value("SIDE_STATUS_TAILWIND"):
                                expected *= 2
                            if side & self.value("SIDE_STATUS_SWAMP"):
                                expected //= 4
                            self.assertEqual(self.calc(speed=speed, stage=stage, status=poison, ability=toxic, item=self.value(item), side=side, badge=badge), expected)
        for battle_type in ("BATTLE_TYPE_LINK", "BATTLE_TYPE_RECORDED_LINK", "BATTLE_TYPE_FRONTIER"):
            self.assertEqual(self.calc(status=poison, ability=toxic, badge=1, battleType=self.value(battle_type)), 131)
        self.assertEqual(self.calc(status=poison, ability=toxic, badge=1, battler=1), 131)
        self.assertEqual(self.calc(status=poison, ability=toxic, item=self.value("HOLD_EFFECT_CHOICE_SCARF"), gimmick=self.value("GIMMICK_DYNAMAX")), 131)
        self.assertEqual(self.calc(status=poison, ability=toxic, item=self.value("HOLD_EFFECT_QUICK_POWDER")), 262)
        self.assertEqual(self.calc(status=poison, ability=toxic, item=self.value("HOLD_EFFECT_QUICK_POWDER"), volatiles=2), 131)

    def test_other_ability_paths_match_actual_pre_unit_function(self):
        abilities = ("ABILITY_NONE", "ABILITY_QUICK_FEET", "ABILITY_SWIFT_SWIM", "ABILITY_CHLOROPHYLL", "ABILITY_SAND_RUSH", "ABILITY_SLUSH_RUSH", "ABILITY_SURGE_SURFER", "ABILITY_SLOW_START", "ABILITY_PROTOSYNTHESIS", "ABILITY_QUARK_DRIVE", "ABILITY_UNBURDEN")
        statuses = (0, self.value("STATUS1_POISON"), self.value("STATUS1_PARALYSIS"))
        for ability in abilities:
            for status in statuses:
                for weather in (0, self.value("B_WEATHER_RAIN_NORMAL"), self.value("B_WEATHER_SUN_NORMAL"), self.value("B_WEATHER_SANDSTORM"), self.value("B_WEATHER_HAIL")):
                    for volatiles in (0, 1, 2, 4, 8):
                        inputs = dict(speed=101, stage=7, status=status, ability=self.value(ability), weather=weather, volatiles=volatiles, field=self.value("STATUS_FIELD_ELECTRIC_TERRAIN"), item=self.value("HOLD_EFFECT_CHOICE_SCARF"), side=self.value("SIDE_STATUS_TAILWIND"), badge=1)
                        self.assertEqual(self.calc(**inputs), self.calc(self.previous, **inputs), inputs)
        for item in ("HOLD_EFFECT_MACHO_BRACE", "HOLD_EFFECT_POWER_ITEM", "HOLD_EFFECT_IRON_BALL", "HOLD_EFFECT_QUICK_POWDER", "HOLD_EFFECT_UTILITY_UMBRELLA"):
            for transformed in (0, 2):
                inputs = dict(ability=self.value("ABILITY_SWIFT_SWIM"), item=self.value(item), volatiles=transformed, weather=self.value("B_WEATHER_RAIN_NORMAL"))
                self.assertEqual(self.calc(**inputs), self.calc(self.previous, **inputs), inputs)


if __name__ == "__main__":
    unittest.main()
