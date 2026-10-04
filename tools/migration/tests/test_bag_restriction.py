"""Trainer-only bag regression using the actual native policy and var helpers.

Run in WSL: python3 -m unittest tools.migration.tests.test_bag_restriction -v.
Native cc is mandatory; a missing compiler is an error, never a skipped test.
Only external types, globals and main/special variable storage are supplied.
"""

import ctypes
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
PRE_UNIT = "6c4fde611f"
MODES = ("NO_BAG_RESTRICTION", "NO_BAG_AGAINST_TRAINER",
         "NO_BAG_IN_BATTLE", "NO_BAG_INVALID_VALUE")


def source(path, ref=None):
    if ref:
        return subprocess.check_output(["git", "show", f"{ref}:{path}"], cwd=ROOT, text=True)
    return (ROOT / path).read_text()


def function(text, name):
    match = re.search(r"^(?:static )?[\w *]+\b" + re.escape(name) + r"\([^;{}]*\)\s*\{", text, re.M)
    if match is None:
        raise AssertionError(f"Missing actual engine function {name}")
    end, depth = match.end(), 1
    while depth:
        depth += (text[end] == "{") - (text[end] == "}")
        end += 1
    return text[match.start():end] + "\n"


def define(text, name):
    match = re.search(r"^#define\s+" + re.escape(name) + r"\b[^\n]*", text, re.M)
    if match is None:
        raise AssertionError(f"Missing native constant {name}")
    return match.group(0) + "\n"


class BagRestrictionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="bag-restriction-")
        cls.directory = Path(cls.temp.name)
        cls.addClassCleanup(cls.temp.cleanup)
        cls.preamble = r'''
#include <stdint.h>
#include <stddef.h>
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint8_t bool8;
typedef uint32_t bool32;
#define TRUE 1
#define FALSE 0
#define TESTING 0
#include "constants/vars.h"
#include "config/battle.h"
'''
        # Extract the exact real battle masks, not invented fixture values.
        battle = source("include/constants/battle.h")
        cls.preamble += "".join(define(battle, name) for name in
                                ("BATTLE_TYPE_TRAINER", "BATTLE_TYPE_DOUBLE"))
        cls.engine = "".join(function(source("src/event_data.c"), name) for name in
                             ("GetVarPointer", "VarGet", "VarSet"))
        cls.engine += function(source("src/battle_util.c"), "IsAllowedToUseBag")
        cls.default = cls.compile("default")
        cls.literals = {mode: cls.compile(mode, mode) for mode in MODES}
        cls.variable = cls.compile("variable", "VAR_UNUSED_0x40F7")

    @classmethod
    def compile(cls, name, override=None):
        text = cls.preamble
        if override is not None:
            text += f"#undef B_VAR_NO_BAG_USE\n#define B_VAR_NO_BAG_USE {override}\n"
        text += r'''
struct SaveBlock1 { u16 vars[VARS_COUNT]; };
static struct SaveBlock1 save;
struct SaveBlock1 *gSaveBlock1Ptr = &save;
static u16 specialValues[SPECIAL_VARS_END - SPECIAL_VARS_START + 1];
u16 *gSpecialVars[SPECIAL_VARS_END - SPECIAL_VARS_START + 1];
u32 gBattleTypeFlags;
'''
        text += cls.engine
        text += r'''
void Reset(void)
{
    unsigned i;
    gSaveBlock1Ptr = &save;
    for (i = 0; i < VARS_COUNT; i++)
        save.vars[i] = 0x1234 + i;
    for (i = 0; i < sizeof(specialValues) / sizeof(specialValues[0]); i++)
    {
        specialValues[i] = 0x5678 + i;
        gSpecialVars[i] = &specialValues[i];
    }
    gBattleTypeFlags = 0;
}
unsigned Query(unsigned flags)
{
    gBattleTypeFlags = flags;
    return IsAllowedToUseBag();
}
unsigned QueryWithoutSave(unsigned flags)
{
    unsigned result;
    gSaveBlock1Ptr = NULL;
    result = Query(flags);
    gSaveBlock1Ptr = &save;
    return result;
}
unsigned Saved(unsigned index) { return save.vars[index]; }
unsigned Special(unsigned index) { return specialValues[index]; }
unsigned ResetConfiguredMode(void) { return VarSet(B_VAR_NO_BAG_USE, 0); }
unsigned ConfiguredMode(void) { return VarGet(B_VAR_NO_BAG_USE); }
'''
        names = (*MODES, "B_VAR_NO_BAG_USE", "BATTLE_TYPE_TRAINER", "BATTLE_TYPE_DOUBLE",
                 "VARS_START", "VARS_COUNT", "SPECIAL_VARS_START", "SPECIAL_VARS_END",
                 "VAR_UNUSED_0x40F7")
        text += "".join(f"unsigned Value_{value}(void) {{ return {value}; }}\n" for value in names)
        path, library = cls.directory / (name + ".c"), cls.directory / (name + ".so")
        path.write_text(text)
        result = subprocess.run(["cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-shared", "-fPIC",
                                 "-I", str(ROOT / "include"), str(path), "-o", str(library)],
                                capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(f"Native fixture compilation failed ({name}):\n{result.stderr}")
        lib = ctypes.CDLL(str(library))
        for getter in ("Query", "QueryWithoutSave", "Saved", "Special"):
            getattr(lib, getter).argtypes = [ctypes.c_uint]
            getattr(lib, getter).restype = ctypes.c_uint
        lib.GetVarPointer.argtypes = [ctypes.c_uint16]
        lib.GetVarPointer.restype = ctypes.POINTER(ctypes.c_uint16)
        lib.VarGet.argtypes = [ctypes.c_uint16]
        lib.VarGet.restype = ctypes.c_uint16
        lib.VarSet.argtypes = [ctypes.c_uint16, ctypes.c_uint16]
        lib.VarSet.restype = ctypes.c_uint8
        lib.Reset()
        return lib

    def value(self, name, library=None):
        return getattr(library or self.default, "Value_" + name)()

    def battle_flags(self):
        trainer, double = self.value("BATTLE_TYPE_TRAINER"), self.value("BATTLE_TYPE_DOUBLE")
        return (0, double, trainer, trainer | double)

    def snapshot(self, library):
        saved = tuple(library.Saved(i) for i in range(self.value("VARS_COUNT")))
        count = self.value("SPECIAL_VARS_END") - self.value("SPECIAL_VARS_START") + 1
        special = tuple(library.Special(i) for i in range(count))
        return saved, special

    def test_current_default_denies_normal_and_double_trainer_bag(self):
        for flags in self.battle_flags()[2:]:
            with self.subTest(flags=flags):
                self.assertEqual(self.default.Query(flags), 0, "Default trainer bag must be disabled")

    def test_current_default_allows_normal_and_double_wild_bag(self):
        for flags in self.battle_flags()[:2]:
            with self.subTest(flags=flags):
                self.assertEqual(self.default.Query(flags), 1)

    def test_literal_modes_and_invalid_fallback(self):
        expectations = ((1, 1, 1, 1), (1, 1, 0, 0), (0, 0, 0, 0), (1, 1, 1, 1))
        for mode, expected in zip(MODES, expectations):
            library = self.literals[mode]
            for flags, allowed in zip(self.battle_flags(), expected):
                with self.subTest(mode=mode, flags=flags):
                    self.assertEqual(library.Query(flags), allowed)

    def test_literal_helpers_do_not_read_or_mutate_save_or_special_storage(self):
        for name, library in (("default", self.default), *self.literals.items()):
            library.Reset()
            before = self.snapshot(library)
            literal = self.value("B_VAR_NO_BAG_USE", library)
            with self.subTest(mode=name):
                self.assertLess(literal, self.value("VARS_START"))
                self.assertFalse(library.GetVarPointer(literal))
                self.assertEqual(library.VarGet(literal), literal)
                for flags in self.battle_flags():
                    self.assertEqual(library.QueryWithoutSave(flags), library.Query(flags))
                self.assertEqual(library.ResetConfiguredMode(), 0)
                for value in range(4):
                    self.assertEqual(library.VarSet(literal, value), 0)
                    self.assertEqual(library.ConfiguredMode(), literal)
                self.assertEqual(self.snapshot(library), before)

    def test_real_variable_id_uses_actual_varset_for_all_modes(self):
        library = self.variable
        library.Reset()
        var_id = self.value("VAR_UNUSED_0x40F7")
        self.assertEqual(self.value("B_VAR_NO_BAG_USE", library), var_id)
        self.assertTrue(library.GetVarPointer(var_id))
        for mode, expected in enumerate(((1, 1, 1, 1), (1, 1, 0, 0), (0, 0, 0, 0), (1, 1, 1, 1))):
            with self.subTest(mode=mode):
                self.assertEqual(library.VarSet(var_id, mode), 1)
                self.assertEqual(library.VarGet(var_id), mode)
                self.assertEqual(library.ConfiguredMode(), mode)
                for flags, allowed in zip(self.battle_flags(), expected):
                    self.assertEqual(library.Query(flags), allowed)
        self.assertEqual(library.ResetConfiguredMode(), 1)
        self.assertEqual(library.ConfiguredMode(), 0)

    def test_native_helpers_resolve_special_variable_storage(self):
        self.variable.Reset()
        special_id = self.value("SPECIAL_VARS_START")
        self.assertTrue(self.variable.GetVarPointer(special_id))
        self.assertEqual(self.variable.VarSet(special_id, 2), 1)
        self.assertEqual(self.variable.VarGet(special_id), 2)
        self.assertEqual(self.variable.Special(0), 2)

    def test_native_helpers_callers_initialization_and_constants_unchanged(self):
        for path in ("src/event_data.c", "src/battle_main.c", "src/item_use.c", "src/overworld.c",
                     "src/battle_controller_player.c", "src/battle_controller_player_partner.c",
                     "src/debug.c", "include/constants/vars.h", "include/constants/vars_frlg.h",
                     "include/constants/battle.h"):
            with self.subTest(path=path):
                self.assertEqual(source(path), source(path, PRE_UNIT))
        # Pin only the relevant helper, not the unrelated whole battle-util file.
        self.assertEqual(function(source("src/battle_util.c"), "IsAllowedToUseBag"),
                         function(source("src/battle_util.c", PRE_UNIT), "IsAllowedToUseBag"))


if __name__ == "__main__":
    unittest.main()
