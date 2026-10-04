"""Pinned legacy intent, restored through 1.16 native configuration and engines.

Run in WSL: python3 -m unittest tools.migration.tests.test_native_configuration -v.
Requires native cc; a missing compiler is an error, never a skipped regression.
Fixtures compile actual configuration headers, constant conditional blocks, and
unchanged engine functions. Only UI/sound/flag storage dependencies are stubbed.
"""

import ctypes
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = "f5e81e85df6fe40ae490bf7268d0186d7f0426ed"
EFFECTIVE_UPSTREAM = "1565171235"
PRE_UNIT = "5f9c2a1e32"
CONFIG = "include/config/"
CONSTANTS = "include/constants/"
# Paths/names only: the expected values are independently extracted from archive.
SETTINGS = {
    "battle.h": ["B_PROTEAN_LIBERO", "B_INTREPID_SWORD", "B_DAUNTLESS_SHIELD",
                 "B_WAIT_TIME_MULTIPLIER", "B_QUICK_MOVE_CURSOR_TO_RUN",
                 "B_AFFECTION_MECHANICS", "B_USE_FROSTBITE"],
    "wild_encounter.h": ["WE_DOUBLE_WILD_CHANCE", "WE_DOUBLE_WILD_REQUIRE_2_MONS"],
    "item.h": ["I_SHINY_CHARM_ADDITIONAL_ROLLS", "I_USE_EVO_HELD_ITEMS_FROM_BAG",
               "I_REUSABLE_TMS", "I_EXP_SHARE_FLAG", "I_EXP_SHARE_ITEM"],
    "overworld.h": ["OW_SYNCHRONIZE_NATURE"],
    "debug.h": ["DEBUG_OVERWORLD_MENU", "DEBUG_BATTLE_MENU", "DEBUG_POKEMON_SPRITE_VISUALIZER"],
    "pokedex_plus_hgss.h": ["POKEDEX_PLUS_HGSS"],
}
CUSTOM_TMS = ["DRAIN_PUNCH", "FLIP_TURN", "THUNDER_WAVE", "U_TURN", "VOLT_SWITCH", "HURRICANE"]


def git_source(ref, path):
    return subprocess.check_output(["git", "show", f"{ref}:{path}"], cwd=ROOT, text=True)


def source(path):
    return (ROOT / path).read_text()


def macros(text):
    result = {}
    for name, value in re.findall(r"^\s*#define\s+(\w+)([^\n]*)", text, re.M):
        value = value.split("//")[0].strip()
        result.setdefault(name, []).append(value)
    return result


def function(text, name):
    match = re.search(r"^(?:static )?[\w *]+\b" + re.escape(name) + r"\([^;{}]*\)\s*\{", text, re.M)
    if match is None:
        raise AssertionError(f"Missing actual engine function {name}")
    end, depth = match.end(), 1
    while depth:
        depth += (text[end] == "{") - (text[end] == "}")
        end += 1
    return text[match.start():end] + "\n"


def legendary_block(text):
    match = re.search(r"^#if P_LEGENDARY_PERFECT_IVS >= GEN_6\n.*?^#endif", text, re.M | re.S)
    if not match:
        raise AssertionError("Missing native legendary IV conditional")
    return match.group(0)


def archived_setting(path, name):
    if name.startswith("WE_DOUBLE_WILD"):
        path, name = CONFIG + "battle.h", name.replace("WE_", "B_", 1)
    elif name == "DEBUG_POKEMON_SPRITE_VISUALIZER":
        name = "DEBUG_POKEMON_MENU"
    elif name == "POKEDEX_PLUS_HGSS":
        path = "include/config.h"
    return macros(git_source(ARCHIVE, path))[name][0]


def numeric(value):
    if value == "TRUE":
        return 1
    if value == "FALSE":
        return 0
    if value.startswith("GEN_"):
        return int(value.removeprefix("GEN_"))
    if value == "FLAG_TOGGLE_EXPALL":
        return int(macros(git_source(ARCHIVE, CONSTANTS + "flags.h"))[value][0], 0)
    return int(value, 0)


PREAMBLE = "\n".join(["#include <stdint.h>", "#include <string.h>", "#define TRUE 1", "#define FALSE 0",
                        "#define IS_FRLG 0", "#define GEN_LATEST 9"] +
                       [f"#define GEN_{i} {i}" for i in range(1, 10)]) + "\n"


class NativeConfigurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="native-config-")
        cls.directory = Path(cls.temp.name)
        # Do not synthesize production setting values: compile complete real headers.
        for filename in SETTINGS:
            (cls.directory / filename).write_text(source(CONFIG + filename))
        flags = re.sub(r'^#include[^\n]*\n', '', source(CONSTANTS + "flags.h"), flags=re.M)
        (cls.directory / "flags.h").write_text(flags)
        pokemon = source(CONSTANTS + "pokemon.h")
        shiny = re.search(r"^#define SHINY_ODDS[^\n]*", pokemon, re.M).group(0)
        (cls.directory / "pokemon_constants.h").write_text(shiny + "\n" + legendary_block(pokemon))
        cls.libraries = {}
        for release in (0, 1):
            includes = "\n".join(f'#include "{filename}"' for filename in SETTINGS)
            getters = "\n".join(f"unsigned Get_{name}(void) {{ return {name}; }}"
                                for names in SETTINGS.values() for name in names)
            text = (PREAMBLE + f"#define DISABLED_ON_RELEASE {release}\n" + '#include "flags.h"\n' +
                    includes + "\n#define P_LEGENDARY_PERFECT_IVS GEN_LATEST\n" +
                    '#include "pokemon_constants.h"\n' + getters +
                    "\nunsigned Get_SHINY_ODDS(void) { return SHINY_ODDS; }\n"
                    "unsigned Get_LEGENDARY_PERFECT_IV_COUNT(void) { return LEGENDARY_PERFECT_IV_COUNT; }\n")
            cls.libraries[release] = cls.compile(f"settings_{release}", text)
        disabled = PREAMBLE + "#define P_LEGENDARY_PERFECT_IVS GEN_5\n" + '#include "pokemon_constants.h"\n'
        cls.disabled = cls.compile("legendary_disabled", disabled +
                                  "unsigned Get_LEGENDARY_PERFECT_IV_COUNT(void) { return LEGENDARY_PERFECT_IV_COUNT; }\n")
        cls.engine = cls.compile_engine("engine")
        cls.old_item = cls.compile_engine("old_item", "#undef I_EXP_SHARE_ITEM\n#define I_EXP_SHARE_ITEM GEN_5\n")
        cls.no_flag = cls.compile_engine("no_flag", "#undef I_EXP_SHARE_ITEM\n#define I_EXP_SHARE_ITEM GEN_5\n#undef I_EXP_SHARE_FLAG\n#define I_EXP_SHARE_FLAG 0\n")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    @classmethod
    def compile(cls, name, text):
        c_path, library = cls.directory / (name + ".c"), cls.directory / (name + ".so")
        c_path.write_text(text)
        result = subprocess.run(["cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-shared", "-fPIC",
                                 "-I", str(cls.directory), str(c_path), "-o", str(library)],
                                capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(f"Native fixture compilation failed ({name}):\n{result.stderr}")
        return ctypes.CDLL(str(library))

    @classmethod
    def compile_engine(cls, name, overrides=""):
        getter = function(source("src/battle_util.c"), "IsGen6ExpShareEnabled")
        item = function(source("src/item_use.c"), "ItemUseOutOfBattle_ExpShare")
        text = PREAMBLE + '#define DISABLED_ON_RELEASE 0\n#include "flags.h"\n#include "item.h"\n' + overrides
        # In the RED state I_EXP_SHARE_FLAG is zero. The fixture deliberately does
        # not inject the absent new flag name; assertions pin the expected 0x23.
        text += r'''
typedef uint8_t u8;
typedef uint32_t bool32;
typedef void (*TaskFunc)(u8);
struct Task { int16_t data[16]; };
struct Task gTasks[1];
#define tUsingRegisteredKeyItem data[3]
enum { SE_PC_OFF = 11, SE_EXP_MAX = 12, FONT_NORMAL = 1 };
const u8 gText_ExpShareOff[] = "off", gText_ExpShareOn[] = "on";
u8 flags[0x1000];
unsigned lastSound, lastMessage, lastRoute, lastCallback, dadAdvice, toggles;
bool32 FlagGet(unsigned flag) { return flags[flag]; }
void FlagToggle(unsigned flag) { flags[flag] ^= 1; toggles++; }
void PlaySE(unsigned sound) { lastSound = sound; }
void Task_CloseCantUseKeyItemMessage(u8 task) { (void)task; }
void CloseItemMessage(u8 task) { (void)task; }
void DisplayItemMessageOnField(u8 task, const u8 *message, TaskFunc callback)
{ (void)task; lastMessage = message == gText_ExpShareOn; lastRoute = 0;
  lastCallback = callback == Task_CloseCantUseKeyItemMessage; }
void DisplayItemMessage(u8 task, unsigned font, const u8 *message, TaskFunc callback)
{ (void)task; (void)font; lastMessage = message == gText_ExpShareOn; lastRoute = 1;
  lastCallback = callback == CloseItemMessage; }
void DisplayDadsAdviceCannotUseItemMessage(u8 task, unsigned registered)
{ (void)task; dadAdvice++; lastRoute = registered; }
'''
        text += getter + item + r'''
void Reset(void) { memset(flags, 0, sizeof(flags)); memset(gTasks, 0, sizeof(gTasks));
    lastSound = lastMessage = lastRoute = lastCallback = dadAdvice = toggles = 0; }
void Receipt(void) { flags[FLAG_RECEIVED_EXP_SHARE] = 1; }
void SetExpectedToggle(void) { flags[0x23] = 1; }
void Use(unsigned bag) { gTasks[0].data[2] = bag; gTasks[0].data[3] = !bag; ItemUseOutOfBattle_ExpShare(0); }
unsigned Enabled(void) { return IsGen6ExpShareEnabled(); }
unsigned ReceiptFlag(void) { return flags[FLAG_RECEIVED_EXP_SHARE]; }
unsigned ToggleFlag(void) { return flags[0x23]; }
unsigned Sound(void) { return lastSound; }
unsigned Message(void) { return lastMessage; }
unsigned Route(void) { return lastRoute; }
unsigned Callback(void) { return lastCallback; }
unsigned Advice(void) { return dadAdvice; }
unsigned Toggles(void) { return toggles; }
'''
        return cls.compile(name, text)

    def test_archived_authored_values_are_restored(self):
        for filename, names in SETTINGS.items():
            for name in names:
                expected = numeric(archived_setting(CONFIG + filename, name))
                for release, library in self.libraries.items():
                    with self.subTest(setting=name, release=release):
                        self.assertEqual(getattr(library, "Get_" + name)(), expected)

    def test_actual_pokemon_constants_and_disabled_legendary_branch(self):
        archive = macros(git_source(ARCHIVE, CONSTANTS + "pokemon.h"))
        for name in ("SHINY_ODDS", "LEGENDARY_PERFECT_IV_COUNT"):
            with self.subTest(setting=name):
                self.assertEqual(getattr(self.libraries[0], "Get_" + name)(), int(archive[name][0]))
        self.assertEqual(self.disabled.Get_LEGENDARY_PERFECT_IV_COUNT(), 0)
        self.assertEqual(128 / 65536, 1 / 512)

    def test_permanent_toggle_is_exact_archived_unused_slot_not_receipt(self):
        before = macros(git_source(PRE_UNIT, CONSTANTS + "flags.h"))
        current = macros(source(CONSTANTS + "flags.h"))
        self.assertEqual(before["FLAG_UNUSED_0x023"], ["0x23"])
        self.assertEqual(current.get("FLAG_TOGGLE_EXPALL"), ["0x23"])
        self.assertNotIn("FLAG_UNUSED_0x023", current)
        self.assertEqual(current["FLAG_RECEIVED_EXP_SHARE"], ["0x110"])
        self.assertGreater(0x23, 0x1F)

    def test_new_game_and_receipt_alone_leave_exp_all_off(self):
        self.engine.Reset()
        self.assertEqual(self.engine.Enabled(), 0)
        self.engine.Receipt()
        self.assertEqual(self.engine.Enabled(), 0)
        self.assertEqual(self.engine.ToggleFlag(), 0)

    def test_native_item_toggles_off_on_off_with_bag_and_registered_messages(self):
        for bag in (1, 0):
            with self.subTest(bag=bag):
                self.engine.Reset()
                self.engine.Receipt()
                for enabled, sound in ((1, 12), (0, 11)):
                    self.engine.Use(bag)
                    self.assertEqual(self.engine.Enabled(), enabled)
                    self.assertEqual(self.engine.ToggleFlag(), enabled)
                    self.assertEqual(self.engine.Message(), enabled)
                    self.assertEqual(self.engine.Sound(), sound)
                    self.assertEqual(self.engine.Route(), bag)
                    self.assertEqual(self.engine.Callback(), 1)
                    self.assertEqual(self.engine.ReceiptFlag(), 1)
                self.assertEqual(self.engine.Toggles(), 2)
                self.assertEqual(self.engine.Advice(), 0)

    def test_getter_uses_flag_not_item_generation_and_old_item_gives_dads_advice(self):
        for library, enabled in ((self.old_item, 1), (self.no_flag, 0)):
            with self.subTest(enabled=enabled):
                library.Reset()
                library.SetExpectedToggle()
                self.assertEqual(library.Enabled(), enabled)
                library.Use(0)
                self.assertEqual(library.Advice(), 1)
                self.assertEqual(library.Toggles(), 0)
                self.assertEqual(library.Enabled(), enabled)

    def test_native_item_table_key_pocket_reusable_tms_and_evolution_bag_wiring(self):
        text = source("src/data/items.h")
        block = re.search(r"\[ITEM_EXP_SHARE\]\s*=\s*\{(.*?)^    \},", text, re.M | re.S).group(1)
        self.assertRegex(block, r"#if I_EXP_SHARE_ITEM >= GEN_6[\s\S]*?\.importance = 1,[\s\S]*?\.pocket = POCKET_KEY_ITEMS,[\s\S]*?#else[\s\S]*?\.pocket = POCKET_ITEMS,[\s\S]*?#endif")
        self.assertIn(".fieldUseFunc = ItemUseOutOfBattle_ExpShare,", block)
        self.assertIn(".type = ITEM_USE_FIELD,", block)
        tm_blocks = re.findall(r"\[(ITEM_TM\w+)\]\s*=\s*\{(.*?)^    \},", text, re.M | re.S)
        tm_blocks = [(name, entry) for name, entry in tm_blocks if name != "ITEM_TM_CASE"]
        self.assertEqual(len(tm_blocks), 100)
        self.assertTrue({"ITEM_TM_" + name for name in CUSTOM_TMS}.issubset(dict(tm_blocks)))
        for name, entry in tm_blocks:
            with self.subTest(item=name):
                self.assertIn(".importance = I_REUSABLE_TMS,", entry)
                self.assertIn(".fieldUseFunc = ItemUseOutOfBattle_TMHM,", entry)
        self.assertRegex(text, r"#if I_USE_EVO_HELD_ITEMS_FROM_BAG == TRUE\s+#define EVO_HELD_ITEM_TYPE ITEM_USE_PARTY_MENU\s+#define EVO_HELD_ITEM_FIELD_FUNC ItemUseOutOfBattle_EvolutionStone")
        for name in ("ELECTIRIZER", "RAZOR_CLAW"):
            entry = re.search(r"\[ITEM_" + name + r"\]\s*=\s*\{(.*?)^    \},", text, re.M | re.S).group(1)
            self.assertIn(".type = EVO_HELD_ITEM_TYPE,", entry)
            self.assertIn(".fieldUseFunc = EVO_HELD_ITEM_FIELD_FUNC,", entry)
        menu = source("src/item_menu.c")
        self.assertRegex(menu, r"\[ACTION_USE\]\s*=\s*\{gMenuText_Use,\s*\{ItemMenu_UseOutOfBattle\}\}")
        self.assertIn("GetItemFieldFunc(gSpecialVar_ItemId)(taskId);", function(menu, "ItemMenu_UseOutOfBattle"))

    def test_exact_header_macro_allowlist_and_untouched_species_settings(self):
        allowed = {CONFIG + filename: set(names) for filename, names in SETTINGS.items()}
        allowed[CONFIG + "battle.h"].add("B_VAR_NO_BAG_USE")
        allowed[CONSTANTS + "pokemon.h"] = {"SHINY_ODDS", "LEGENDARY_PERFECT_IV_COUNT"}
        allowed[CONSTANTS + "flags.h"] = {"FLAG_UNUSED_0x023", "FLAG_TOGGLE_EXPALL"}
        paths = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", PRE_UNIT,
                                         CONFIG, CONSTANTS + "pokemon.h", CONSTANTS + "flags.h"], cwd=ROOT, text=True).splitlines()
        for path in paths:
            before, current = macros(git_source(PRE_UNIT, path)), macros(source(path))
            changed = {name for name in before.keys() | current.keys() if before.get(name) != current.get(name)}
            with self.subTest(path=path):
                self.assertEqual(changed, allowed.get(path, set()))
        # Correct authorship baseline, deliberately not the reverted 1.8.1 merge-base.
        for filename in ("pokemon.h", "species_enabled.h"):
            path = CONFIG + filename
            self.assertEqual(macros(git_source(ARCHIVE, path)), macros(git_source(EFFECTIVE_UPSTREAM, path)))


if __name__ == "__main__":
    unittest.main()
