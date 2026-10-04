"""Compile actual cap code with narrow party/save stubs and its real config.

Run under native WSL Python with cc. Compiler errors fail rather than skip.
"""

import ctypes
from decimal import Decimal
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = "f5e81e85df6fe40ae490bf7268d0186d7f0426ed"
FLAGS = [f"FLAG_BADGE0{i}_GET" for i in range(1, 7)] + [
    "FLAG_HIDE_LILYCOVE_CITY_RIVAL", "FLAG_BADGE07_GET", "FLAG_BADGE08_GET",
    "FLAG_IS_CHAMPION",
]
CAPS = [15, 20, 26, 35, 39, 49, 53, 60, 69, 81]
FACTORS = [300, 275, 250, 233, 225, 200, 180, 170, 160, 150, 140, 130,
           120, 110, 100, 90, 80, 75, 66, 50, 40, 33, 25, 20, 15, 10, 5]
U32_MAX = 2**32 - 1


def archive_source():
    return subprocess.run(
        ["git", "show", f"{ARCHIVE}:src/battle_script_commands.c"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout


STUBS = r"""
#include <stdint.h>
#include <string.h>
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;
typedef int32_t s32;
#define FALSE 0
#define TRUE 1
#define MAX_LEVEL 100
#define MAX_TOTAL_EVS 510
#define PARTY_SIZE 6
#define B_TRAINER_PLAYER 0
#define SPECIES_NONE 0
#define MON_DATA_SPECIES 0
#define ARRAY_COUNT(a) (sizeof(a) / sizeof((a)[0]))
struct Pokemon { u16 species; u8 level; u8 egg; u16 hp; };
static struct Pokemon gParties[1][PARTY_SIZE];
static u32 flags;
static u16 variable;
static u32 FlagGet(u32 flag) { return (flags >> flag) & 1; }
static u32 VarGet(u32 id) { (void)id; return variable; }
static u32 GetMonData(struct Pokemon *mon, u32 field, ...)
{ (void)field; return mon->species; }
"""
WRAPPERS = r"""
void FixtureReset(void) { flags = 0; variable = 0; memset(gParties, 0, sizeof(gParties)); }
void FixtureFlags(u32 value) { flags = value; }
void FixtureVariable(u16 value) { variable = value; }
void FixtureMon(u32 slot, u16 species, u8 level, u8 egg, u16 hp)
{ gParties[0][slot] = (struct Pokemon){species, level, egg, hp}; }
u32 FixtureExpType(void) { return B_EXP_CAP_TYPE; }
u32 FixtureLevelType(void) { return B_LEVEL_CAP_TYPE; }
u32 FixtureRareCandy(void) { return B_RARE_CANDY_CAP; }
u32 FixtureExpUp(void) { return B_LEVEL_CAP_EXP_UP; }
u32 FixtureEVType(void) { return B_EV_CAP_TYPE; }
u32 FixtureEVItems(void) { return B_EV_ITEMS_CAP; }
"""


class LegacyCapsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="legacy-caps-")
        cls.addClassCleanup(cls.temp.cleanup)
        source = re.sub(r'^#include[^\n]*\n', '', (ROOT / "src/caps.c").read_text(), flags=re.M)
        configs = {
            "default": {},
            "none": {"B_EXP_CAP_TYPE": "EXP_CAP_NONE"},
            "hard": {"B_EXP_CAP_TYPE": "EXP_CAP_HARD"},
            "hard_up": {"B_EXP_CAP_TYPE": "EXP_CAP_HARD", "B_LEVEL_CAP_EXP_UP": "TRUE"},
            "soft_up": {"B_LEVEL_CAP_EXP_UP": "TRUE"},
            "soft_nocap": {"B_LEVEL_CAP_TYPE": "LEVEL_CAP_NONE"},
            "variable": {"B_LEVEL_CAP_TYPE": "LEVEL_CAP_VARIABLE"},
            "ev_flags": {"B_EV_CAP_TYPE": "EV_CAP_FLAG_LIST"},
            "ev_variable": {"B_EV_CAP_TYPE": "EV_CAP_VARIABLE"},
            "ev_none": {"B_EV_CAP_TYPE": "EV_CAP_NO_GAIN"},
        }
        cls.libs = {}
        for variant, overrides in configs.items():
            enum = 'enum { ' + ', '.join(f'{flag} = {i}' for i, flag in enumerate(FLAGS)) + ' };\n'
            config = f'#include "{ROOT / "include/config/caps.h"}"\n'
            for name, value in overrides.items():
                config += f'#undef {name}\n#define {name} {value}\n'
            # NONE/HARD compile out party use in some implementations; this
            # narrow stub must not turn that into a false test compilation error.
            runner = STUBS.replace('static u32 GetMonData', 'u32 GetMonData') + enum + config + source + WRAPPERS
            library = Path(cls.temp.name) / f"{variant}.so"
            result = subprocess.run(
                ["cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-shared", "-fPIC", "-x", "c", "-", "-o", str(library)],
                input=runner, capture_output=True, text=True,
            )
            if result.returncode:
                raise AssertionError(f"{variant} actual-C compilation failed:\n{result.stderr}")
            lib = ctypes.CDLL(str(library))
            lib.GetSoftLevelCapExpValue.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
            lib.GetSoftLevelCapExpValue.restype = ctypes.c_uint32
            lib.FixtureMon.argtypes = [ctypes.c_uint32, ctypes.c_uint16, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint16]
            lib.FixtureFlags.argtypes = [ctypes.c_uint32]
            lib.FixtureVariable.argtypes = [ctypes.c_uint16]
            cls.libs[variant] = lib

    def setUp(self):
        for lib in self.libs.values():
            lib.FixtureReset()

    def party(self, levels, variant="default", egg=0, hp=1):
        lib = self.libs[variant]
        for slot, level in enumerate(levels):
            lib.FixtureMon(slot, 0 if level is None else 1, level or 0, egg, hp)
        return lib

    def test_archived_tables_independently_match_spec(self):
        source = archive_source()
        source = re.sub(r'//[^\n]*', '', source)
        def values(name):
            return re.search(rf'\b{name}\[[^]]+\]\s*=\s*\{{(.*?)\}};', source, re.S)[1]
        self.assertEqual(re.findall(r'FLAG_\w+', values("sLevelCapFlags")), FLAGS)
        self.assertEqual([int(v) for v in re.findall(r'\d+', values("sLevelCaps"))], CAPS)
        self.assertEqual([int(Decimal(v) * 100) for v in re.findall(r'\d+\.\d+', values("sRelativePartyScaling"))], FACTORS)
        self.assertEqual([Decimal(v) for v in re.findall(r'\d*\.\d+', values("sLevelCapReduction"))],
                         [Decimal(".3")] + [Decimal(".0001")] * 6)

    def test_default_configuration_only_enables_soft_flag_caps(self):
        lib = self.libs["default"]
        self.assertEqual(lib.FixtureExpType(), 2)
        self.assertEqual(lib.FixtureLevelType(), 1)
        self.assertEqual((lib.FixtureRareCandy(), lib.FixtureExpUp(), lib.FixtureEVType(), lib.FixtureEVItems()), (0, 0, 0, 0))

    def test_every_cap_transition_and_first_unset_flag(self):
        lib = self.libs["default"]
        for i, cap in enumerate(CAPS):
            with self.subTest(stage=i):
                lib.FixtureFlags((1 << i) - 1)
                self.assertEqual(lib.GetCurrentLevelCap(), cap)
                lib.FixtureFlags(1023 ^ (1 << i))
                self.assertEqual(lib.GetCurrentLevelCap(), cap)
        lib.FixtureFlags(1023)
        self.assertEqual(lib.GetCurrentLevelCap(), 100)

    def test_below_at_above_each_cap_with_neutral_party(self):
        lib = self.libs["default"]
        for i, cap in enumerate(CAPS):
            lib.FixtureFlags((1 << i) - 1)
            for level, expected in ((cap - 1, 10000), (cap, 3000), (cap + 1, 1), (cap + 7, 1)):
                with self.subTest(cap=cap, level=level):
                    self.party([level])
                    self.assertEqual(lib.GetSoftLevelCapExpValue(level, 10000), expected)

    def test_all_relative_factors_and_clamps_after_champion(self):
        lib = self.party([50])
        lib.FixtureFlags(1023)
        for diff in range(-40, 51):
            index = max(-14, min(12, diff)) + 14
            with self.subTest(diff=diff):
                self.assertEqual(lib.GetSoftLevelCapExpValue(50 + diff, 10000), FACTORS[index] * 100)
        self.party([100])
        self.assertEqual(lib.GetSoftLevelCapExpValue(100, 10000), 10000)

    def test_team_denominator_and_threshold_preserve_archive(self):
        for levels, team in (([40, 40, 20], 26), ([21, 21, 15], 19), ([50, 50, 1], 33)):
            with self.subTest(levels=levels):
                lib = self.party(levels)
                lib.FixtureFlags(1023)
                self.assertEqual(lib.GetSoftLevelCapExpValue(team, 10000), 10000)
                self.assertEqual(lib.GetSoftLevelCapExpValue(team + 1, 10000), 9000)

    def test_full_six_member_party_uses_original_count_after_filtering(self):
        # Sum 225 / 6 -> average 37; threshold 37 * 4 / 5 -> 29.
        # Qualifying sum 210 / ORIGINAL count 6 -> team level 35.
        lib = self.party([60, 60, 50, 40, 10, 5])
        lib.FixtureFlags(1023)
        self.assertEqual(lib.GetSoftLevelCapExpValue(35, 10000), 10000)
        self.assertEqual(lib.GetSoftLevelCapExpValue(36, 10000), 9000)

    def test_first_empty_slot_stops_scan_and_empty_is_neutral(self):
        lib = self.party([25, None, 100])
        lib.FixtureFlags(1023)
        self.assertEqual(lib.GetSoftLevelCapExpValue(25, 10000), 10000)
        lib = self.party([None, 100])
        self.assertEqual(lib.GetSoftLevelCapExpValue(1, 10000), 10000)
        lib.FixtureFlags(0)
        self.assertEqual(lib.GetSoftLevelCapExpValue(15, 10000), 3000)

    def test_eggs_and_fainted_members_still_count(self):
        lib = self.party([50, 50, 1], egg=1, hp=0)
        lib.FixtureFlags(1023)
        self.assertEqual(lib.GetSoftLevelCapExpValue(33, 10000), 10000)
        self.assertEqual(lib.GetSoftLevelCapExpValue(34, 10000), 9000)

    def test_combined_cap_and_party_matrix(self):
        lib = self.libs["default"]
        for stage, cap in enumerate(CAPS):
            lib.FixtureFlags((1 << stage) - 1)
            for level in (cap - 1, cap, cap + 1):
                for diff in range(-14, 13):
                    self.party([level - diff])
                    factor = FACTORS[diff + 14]
                    numerator = factor * (3 if level == cap else 1)
                    denominator = 100 if level < cap else 1000 if level == cap else 1000000
                    for raw in (0, 1, 4, 10001, U32_MAX):
                        with self.subTest(stage=stage, level=level, diff=diff, raw=raw):
                            expected = min(U32_MAX, raw * numerator // denominator)
                            self.assertEqual(lib.GetSoftLevelCapExpValue(level, raw), expected)

    def test_combined_rounding_zero_tiny_and_saturated_inputs(self):
        lib = self.party([23])  # level 15 is eight below team: 1.8 * .3
        self.assertEqual(lib.GetSoftLevelCapExpValue(15, 4), 2)
        self.assertEqual(lib.GetSoftLevelCapExpValue(15, 0), 0)
        self.assertEqual(lib.GetSoftLevelCapExpValue(15, 1), 0)
        self.assertEqual(lib.GetSoftLevelCapExpValue(16, 1), 0)
        lib.FixtureFlags(1023)
        self.assertEqual(lib.GetSoftLevelCapExpValue(1, U32_MAX), U32_MAX)
        self.assertEqual(lib.GetSoftLevelCapExpValue(24, U32_MAX), U32_MAX * 90 // 100)

    def test_none_hard_variable_and_optional_exp_up_semantics(self):
        none = self.party([99], "none")
        for level in (1, 15, 16, 100):
            self.assertEqual(none.GetSoftLevelCapExpValue(level, 12345), 12345)
        hard = self.party([99], "hard")
        self.assertEqual(hard.GetSoftLevelCapExpValue(14, 100), 100)
        self.assertEqual(hard.GetSoftLevelCapExpValue(15, 100), 0)
        self.assertEqual(hard.GetSoftLevelCapExpValue(16, 100), 0)
        for diff, divisor in ((1, 8), (2, 4), (3, 2), (4, 1), (5, 1)):
            up = self.party([15 - diff], "hard_up")
            self.assertEqual(up.GetSoftLevelCapExpValue(15 - diff, 100), 100 + 100 // divisor)
        up = self.party([22], "soft_up")
        self.assertEqual(up.GetSoftLevelCapExpValue(14, 100), 112 * 180 // 100)
        self.assertEqual(up.GetSoftLevelCapExpValue(1, U32_MAX), U32_MAX)
        no_cap = self.party([100], "soft_nocap")
        self.assertEqual(no_cap.GetCurrentLevelCap(), 100)
        self.assertEqual(no_cap.GetSoftLevelCapExpValue(100, 10000), 10000)
        variable = self.party([42], "variable")
        variable.FixtureVariable(42)
        self.assertEqual(variable.GetCurrentLevelCap(), 42)
        self.assertEqual(variable.GetSoftLevelCapExpValue(42, 10000), 3000)
        variable.FixtureVariable(100)
        self.party([100], "variable")
        self.assertEqual(variable.GetSoftLevelCapExpValue(100, 10000), 3000)

    def test_ev_cap_modes_are_unchanged(self):
        self.assertEqual(self.libs["default"].GetCurrentEVCap(), 510)
        lib = self.libs["ev_flags"]
        # EV flags deliberately do not acquire the additional level-cap milestone.
        ev_flags = FLAGS[:6] + FLAGS[7:]
        for i, flag in enumerate(ev_flags):
            lib.FixtureFlags(sum(1 << FLAGS.index(f) for f in ev_flags[:i]))
            expected = 510 if i == 8 else 510 * (2 * i + 1) // 17
            self.assertEqual(lib.GetCurrentEVCap(), expected)
        lib.FixtureFlags(1023)
        self.assertEqual(lib.GetCurrentEVCap(), 510)
        self.libs["ev_variable"].FixtureVariable(37)
        self.assertEqual(self.libs["ev_variable"].GetCurrentEVCap(), 37)
        self.assertEqual(self.libs["ev_none"].GetCurrentEVCap(), 0)

    def test_lilycove_rival_flag_chain_and_existing_exp_hooks(self):
        objects = json.loads((ROOT / "data/maps/LilycoveCity/map.json").read_text())["object_events"]
        self.assertTrue(any(obj["flag"] == "FLAG_HIDE_LILYCOVE_CITY_RIVAL" and "Rival" in obj["script"] for obj in objects))
        script = (ROOT / "data/maps/LilycoveCity/scripts.inc").read_text()
        fly = script.split("LilycoveCity_EventScript_RivalFlyAway::", 1)[1].split("\n\n", 1)[0]
        self.assertIn("removeobject VAR_LAST_TALKED", fly)
        scrcmd = (ROOT / "src/scrcmd.c").read_text()
        self.assertRegex(scrcmd, r'(?s)bool8 ScrCmd_removeobject\([^)]*\).*?RemoveObjectEventByLocalIdAndMap')
        movement = (ROOT / "src/event_object_movement.c").read_text()
        removal = movement.split("void RemoveObjectEventByLocalIdAndMap(", 1)[1].split("\n}\n", 1)[0]
        self.assertRegex(removal, r'FlagSet\(')
        battle = (ROOT / "src/battle_script_commands.c").read_text()
        start = battle.index("gBattleStruct->battlerExpReward = GetSoftLevelCapExpValue")
        end = battle.index("ApplyExperienceMultipliers(&gBattleStruct->battlerExpReward", start)
        hook = battle[start:end]
        self.assertEqual(hook.count("GetSoftLevelCapExpValue("), 2)
        self.assertIn("gBattleStruct->expValue)", hook)
        self.assertIn("gBattleStruct->expShareExpValue)", hook)


if __name__ == "__main__":
    unittest.main()
