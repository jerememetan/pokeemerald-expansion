"""Native-C regressions for HM gates, actors, and the existing party menu.

Run with WSL python3 -m unittest tools.migration.tests.test_hm_unlocks -v.
The entire real field_move.c/table and extracted engine function bodies are
compiled, not reimplemented. Stubs isolate flags, party data, script bytes,
and UI drawing. Both variants use real flag constants; FRLG retains its
badge-only policy because upstream has zero-valued receipt placeholders.
"""

import ctypes
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
HMS = ["CUT", "FLASH", "ROCK_SMASH", "STRENGTH", "SURF", "FLY", "DIVE", "WATERFALL"]
EMERALD_BADGES = [1, 2, 3, 4, 5, 6, 7, 8]
FRLG_BADGES = [2, 1, 6, 4, 5, 3, 7, 7]
PARTY_SIZE = 6


def function(source, name):
    """Extract one unchanged function definition, ignoring forward declarations."""
    match = re.search(r"^(?:static )?[\w *]+\b" + re.escape(name)
                      + r"\([^;{}]*\)\s*\{", source, re.M)
    if match is None:
        return None
    end = match.end()
    depth = 1
    while depth:
        if source[end] == "{":
            depth += 1
        elif source[end] == "}":
            depth -= 1
        end += 1
    return source[match.start():end] + "\n"


def no_includes(source):
    return re.sub(r'^#include[^\n]*\n', '', source, flags=re.M)


STUBS = r"""
#include <stdint.h>
#include <string.h>
#include <stddef.h>
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef int16_t s16;
typedef uint8_t bool8;
typedef uint32_t bool32;
typedef void (*TaskFunc)(u8);
#define TRUE 1
#define FALSE 0
#define PARTY_SIZE 6
#define B_TRAINER_PLAYER 0
#define MAX_MON_MOVES 4
#define OW_ROCK_CLIMB_FIELD_MOVE FALSE
#define OW_DEFOG_FIELD_MOVE FALSE
#define SCREFF_V1 1
#define PLAYER_AVATAR_FLAG_SURFING 1
#define SE_SELECT 1
enum Species { SPECIES_NONE, SPECIES_TEST };
enum { MON_DATA_SPECIES, MON_DATA_IS_EGG, MON_DATA_HELD_ITEM, MON_DATA_MOVE1 };
struct Pokemon { u16 species, moves[4], item; u8 egg; };
static struct Pokemon gParties[1][PARTY_SIZE];
static u8 flags[0x1000];
static u32 effects, surfing, invalidReads, pike;
static u16 gSpecialVar_Result, gSpecialVar_0x8004;
static bool32 FlagGet(u32 flag) { return flags[flag]; }
static u32 GetMonData(struct Pokemon *mon, u32 field, ...)
{
    if (mon < &gParties[0][0] || mon >= &gParties[0][PARTY_SIZE])
    { invalidReads++; return 0; }
    if (field == MON_DATA_SPECIES) return mon->species;
    if (field == MON_DATA_IS_EGG) return mon->egg;
    if (field == MON_DATA_HELD_ITEM) return mon->item;
    return mon->moves[field - MON_DATA_MOVE1];
}
static bool8 MonKnowsMove(struct Pokemon *mon, enum Move move)
{
    for (u32 i = 0; i < MAX_MON_MOVES; i++)
        if (mon->moves[i] == move) return TRUE;
    return FALSE;
}
struct ScriptContext { u8 bytes[2], position; };
static u8 ScriptReadByte(struct ScriptContext *ctx) { return ctx->bytes[ctx->position++]; }
static void Script_RequestEffects(u32 value) { effects |= value; }
static bool32 TestPlayerAvatarFlags(u32 value) { return surfing & value; }
static bool32 InBattlePike(void) { return pike; }
static bool32 ItemIsMail(u32 item) { return item == 1; }
static void AppendToList(u8 *list, u8 *length, u8 action) { list[(*length)++] = action; }
struct Task { s16 data[16]; TaskFunc func; };
static struct Task gTasks[1];
static void Task_HandleSelectionMenuInput(u8 taskId) { (void)taskId; }
void PlaySE(u32 value) { (void)value; }
static u32 removedWindows;
void PartyMenuRemoveWindow(u8 *id) { *id = 0xFF; removedWindows++; }
struct WindowTemplate { u8 top, height; };
static struct WindowTemplate displayedWindow;
static const struct WindowTemplate sItemGiveTakeWindowTemplate = {0};
static const struct WindowTemplate sMailReadTakeWindowTemplate = {0};
static const struct WindowTemplate sCatalogSelectWindowTemplate = {0};
static const struct WindowTemplate sZygardeCubeSelectWindowTemplate = {0};
static const struct WindowTemplate sMoveSelectWindowTemplate = {0};
static void SetWindowTemplateFields(struct WindowTemplate *w, u8 bg, u8 left,
                                   u8 top, u8 width, u8 height, u8 palette, u16 base)
{ (void)bg; (void)left; (void)width; (void)palette; (void)base; w->top = top; w->height = height; }
static u8 AddWindow(const struct WindowTemplate *w) { displayedWindow = *w; return 7; }
static void DrawStdFrameWithCustomTileAndPalette(u8 w, bool32 c, u16 t, u8 p)
{ (void)w; (void)c; (void)t; (void)p; }
static u8 GetMenuCursorDimensionByFont(u8 font, u8 value) { (void)font; (void)value; return 0; }
static u8 GetFontAttribute(u8 font, u8 attr) { (void)font; (void)attr; return 0; }
static const u8 sFontColorTable[5][3] = {{0}};
static const u8 *GetMoveName(u32 move) { (void)move; return (const u8 *)"move"; }
static void AddTextPrinterParameterized4(u8 w, u8 f, u8 x, u8 y, u8 l, u8 s,
                                        const u8 *c, u8 speed, const u8 *text)
{ (void)w; (void)f; (void)x; (void)y; (void)l; (void)s; (void)c; (void)speed; (void)text; }
static void InitMenuInUpperLeftCorner(u8 w, u8 count, u8 pos, bool32 wrap)
{ (void)w; (void)count; (void)pos; (void)wrap; }
static void ScheduleBgCopyTilemapToVram(u8 bg) { (void)bg; }
#define FONT_NORMAL 0
#define FONTATTR_LETTER_SPACING 0
#define COMPOUND_STRING(s) ((const u8 *)(s))
"""

WRAPPERS = r"""
void FixtureReset(void)
{
    effects = surfing = invalidReads = pike = removedWindows = 0;
    memset(flags, 0, sizeof(flags));
    memset(gParties, 0, sizeof(gParties));
    memset(&menu, 0, sizeof(menu));
    memset(gTasks, 0, sizeof(gTasks));
    menu.before = 0xA5; menu.after = 0x5A;
    gSpecialVar_Result = 999; gSpecialVar_0x8004 = 321;
}
void FixtureFlags(u32 value)
{
    memset(flags, 0, sizeof(flags));
    for (u32 i = 0; i < 16; i++)
        if (value & (1u << i)) flags[fixtureFlags[i]] = 1;
}
void FixtureSurfing(u32 value) { surfing = value; }
void FixturePike(u32 value) { pike = value; }
void FixtureMon(u32 slot, u16 species, u8 egg)
{ gParties[0][slot].species = species; gParties[0][slot].egg = egg; }
void FixtureMove(u32 slot, u32 moveSlot, u16 move) { gParties[0][slot].moves[moveSlot] = move; }
void FixtureItem(u32 value) { gParties[0][0].item = value; }
u32 FixtureMoveID(u32 move) { return FieldMove_GetMoveId(move); }
u32 FixtureUnlocked(u32 move) { return IsFieldMoveUnlocked(move); }
u32 FixtureScript(u8 move, u8 check)
{
    struct ScriptContext ctx = {{move, check}, 0};
    return ScrCmd_checkfieldmove(&ctx);
}
u32 FixtureResult(void) { return gSpecialVar_Result; }
u32 FixtureSpecies(void) { return gSpecialVar_0x8004; }
u32 FixtureEffects(void) { return effects; }
u32 FixtureInvalidReads(void) { return invalidReads; }
void FixtureRoot(void) { SetPartyMonFieldSelectionActions(gParties[0], 0); DisplaySelectionWindow(SELECTWINDOW_ACTIONS); }
u32 FixtureCount(void) { return menu.numActions; }
u32 FixtureAction(u32 i) { return menu.actions[i]; }
u32 FixtureCapacity(void) { return sizeof(menu.actions); }
u32 FixtureCanaries(void) { return menu.before == 0xA5 && menu.after == 0x5A; }
u32 FixtureTop(void) { return displayedWindow.top; }
u32 FixtureHeight(void) { return displayedWindow.height; }
u32 FixtureCursorReset(void) { return gTasks[0].data[0] == 0xFF; }
u32 FixtureInputHandler(void) { return gTasks[0].func == Task_HandleSelectionMenuInput; }
u32 FixtureRemoved(void) { return removedWindows; }
"""


class HMUnlockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="hm-unlocks-")
        cls.addClassCleanup(cls.temp.cleanup)
        field = no_includes((ROOT / "src/field_move.c").read_text())
        header = no_includes((ROOT / "include/field_move.h").read_text())
        party = (ROOT / "src/party_menu.c").read_text()
        script = function((ROOT / "src/scrcmd.c").read_text(), "ScrCmd_checkfieldmove")
        surf = function((ROOT / "src/field_player_avatar.c").read_text(), "PartyHasMonWithSurf")
        root = function(party, "SetPartyMonFieldSelectionActions")
        submenu = function(party, "CursorCb_HMs")
        window = function(party, "DisplaySelectionWindow")
        menu_enum = re.search(r'enum \{\s*MENU_SUMMARY,.*?\n\};', party, re.S)[0]
        capacity = re.search(r'\bu8 actions\[(\d+)\];', party)[1]
        # Preserve array capacity and place an immediate canary on each side.
        menu_struct = f"""
struct Menu {{ u8 before; u8 actions[{capacity}]; u8 after; u8 numActions; u8 windowId[3]; }};
static struct Menu menu;
static struct Menu *sPartyMenuInternal = &menu;
"""
        constants = ''.join(no_includes((ROOT / path).read_text()) for path in [
            "include/constants/moves.h", "include/constants/field_move.h",
            "include/constants/party_menu.h", "include/constants/opponents.h",
            "include/constants/opponents_frlg.h",
        ])
        flags_source = (ROOT / "include/constants/flags.h").read_text().replace(
            '#include "constants/flags_frlg.h"',
            (ROOT / "include/constants/flags_frlg.h").read_text(),
        )
        flags = no_includes(flags_source) + '\nstatic const u32 fixtureFlags[] = { ' + ', '.join(
            [f'FLAG_BADGE0{i + 1}_GET' for i in range(8)]
            + [f'FLAG_RECEIVED_HM_{name}' for name in HMS]
        ) + ' };\n'
        setup_names = sorted(set(re.findall(r'\.fieldMoveFunc = (\w+)', field)))
        setups = ''.join(f'static bool32 {name}(void) {{ return TRUE; }}\n' for name in setup_names)
        # UI callbacks not under test are inert, but the real option table and
        # HMs callback binding are compiled so enum/table drift is visible.
        data = (ROOT / "src/data/party_menu.h").read_text()
        table = re.search(r'struct\s*\{\s*const u8 \*text;\s*TaskFunc func;\s*\} static const sCursorOptions\[MENU_FIELD_MOVES\] =\s*\{.*?\n\};', data, re.S)[0]
        # Engine's old-style declaration is legal but native cc -Wextra warns;
        # move only the qualifiers, leaving every option and callback intact.
        table = 'static const ' + table.replace('} static const sCursorOptions', '} sCursorOptions')
        callbacks = sorted(set(re.findall(r',\s*(CursorCb_\w+)\}', table)))
        callbacks_c = ''.join(
            'static void CursorCb_HMs(u8 taskId);\n' if name == "CursorCb_HMs"
            else f'static void {name}(u8 taskId) {{ (void)taskId; }}\n'
            for name in callbacks
        )
        texts = sorted(set(re.findall(r'\{(\w+),', table)))
        text_stubs = ''.join(f'static const u8 {name}[] = "text";\n' for name in texts)
        selector = """
u32 FixtureSelect(u8 move, u8 check) { return FieldMove_GetPartyMon(move, check); }
"""
        submenu_wrapper = """
u32 FixtureHMEntry(void) { return MENU_HMS; }
void FixtureSubmenu(void) { sCursorOptions[MENU_HMS].func(0); }
"""
        cls.libs = {}
        for variant in ("emerald", "frlg"):
            runner = (f'#define IS_FRLG {int(variant == "frlg")}\n'
                      + constants + STUBS + flags + header + setups + field
                      + script + surf + menu_enum + menu_struct
                      + callbacks_c + text_stubs + table + window + root
                      + submenu + selector + submenu_wrapper + WRAPPERS)
            library = Path(cls.temp.name) / f"{variant}.so"
            result = subprocess.run(
                ["cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-shared", "-fPIC", "-x", "c", "-", "-o", str(library)],
                input=runner, capture_output=True, text=True,
            )
            if result.returncode:
                raise AssertionError(f"{variant} actual-C compilation failed:\n{result.stderr}")
            lib = ctypes.CDLL(str(library))
            for name in ("FixtureFlags", "FixtureSurfing", "FixturePike", "FixtureItem", "FixtureMoveID", "FixtureUnlocked", "FixtureAction"):
                getattr(lib, name).argtypes = [ctypes.c_uint32]
            lib.FixtureMon.argtypes = [ctypes.c_uint32, ctypes.c_uint16, ctypes.c_uint8]
            lib.FixtureMove.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint16]
            for name in ("FixtureSelect", "FixtureScript"):
                getattr(lib, name).argtypes = [ctypes.c_uint8, ctypes.c_uint8]
            for name in re.findall(r'u32 (Fixture\w+)\(', runner):
                getattr(lib, name).restype = ctypes.c_uint32
            cls.libs[variant] = lib

    def setUp(self):
        for lib in self.libs.values():
            lib.FixtureReset()

    @staticmethod
    def gate(index, badges, badge=True, receipt=True):
        return ((1 << (badges[index] - 1)) if badge else 0) | ((1 << (index + 8)) if receipt else 0)

    def test_all_eight_independent_badge_and_receipt_pairs(self):
        for variant, badges in (("emerald", EMERALD_BADGES), ("frlg", FRLG_BADGES)):
            lib = self.libs[variant]
            for hm in range(8):
                for badge in (False, True):
                    for receipt in (False, True):
                        with self.subTest(variant=variant, hm=HMS[hm], badge=badge, receipt=receipt):
                            lib.FixtureFlags(self.gate(hm, badges, badge, receipt))
                            self.assertEqual(lib.FixtureUnlocked(hm), int(badge and (receipt or variant == "frlg")))

    def test_other_badges_and_other_receipts_do_not_unlock(self):
        for variant, badges in (("emerald", EMERALD_BADGES), ("frlg", FRLG_BADGES)):
            lib = self.libs[variant]
            for hm in range(8):
                with self.subTest(variant=variant, hm=HMS[hm]):
                    lib.FixtureFlags(0xFFFF & ~(1 << (badges[hm] - 1)))
                    self.assertFalse(lib.FixtureUnlocked(hm))
                    lib.FixtureFlags(0xFFFF & ~(1 << (hm + 8)))
                    self.assertEqual(lib.FixtureUnlocked(hm), int(variant == "frlg"))

    def test_unlocked_hms_choose_actor_without_learning_and_preserve_script_outputs(self):
        for variant, badges in (("emerald", EMERALD_BADGES), ("frlg", FRLG_BADGES)):
            lib = self.libs[variant]
            for hm in range(8):
                for check in (False, True):
                    with self.subTest(variant=variant, hm=HMS[hm], check=check):
                        lib.FixtureReset()
                        lib.FixtureFlags(self.gate(hm, badges))
                        lib.FixtureMon(0, 25, 1)
                        lib.FixtureMon(1, 133, 0)
                        self.assertEqual(lib.FixtureSelect(hm, check), 1)
                        self.assertEqual(lib.FixtureScript(hm, check), 0)
                        self.assertEqual(lib.FixtureResult(), 1)
                        self.assertEqual(lib.FixtureSpecies(), 133)
                        self.assertEqual(lib.FixtureEffects(), 1)
                        self.assertEqual(lib.FixtureInvalidReads(), 0)

    def test_learned_hms_cannot_bypass_lock_even_without_optional_check(self):
        for variant, badges in (("emerald", EMERALD_BADGES), ("frlg", FRLG_BADGES)):
            lib = self.libs[variant]
            for hm in range(8):
                for badge, receipt in ((False, False), (True, False), (False, True)):
                    if variant == "frlg" and badge:
                        continue  # Actual FRLG is badge-only, no receipt storage.
                    for check in (False, True):
                        with self.subTest(variant=variant, hm=HMS[hm], badge=badge, receipt=receipt, check=check):
                            lib.FixtureReset()
                            lib.FixtureFlags(self.gate(hm, badges, badge, receipt))
                            lib.FixtureMon(0, 25, 0)
                            lib.FixtureMove(0, 0, lib.FixtureMoveID(hm))
                            self.assertEqual(lib.FixtureSelect(hm, check), PARTY_SIZE)
                            self.assertEqual(lib.FixtureScript(hm, check), 0)
                            self.assertEqual(lib.FixtureResult(), PARTY_SIZE)
                            self.assertEqual(lib.FixtureSpecies(), 321)
                            self.assertEqual(lib.FixtureEffects(), 1)
                            self.assertEqual(lib.FixtureInvalidReads(), 0)

    def test_empty_all_egg_first_none_and_last_valid_party_slots(self):
        for variant, lib in self.libs.items():
            for hm in range(8):
                for case in ("empty", "eggs", "hole", "last", "first"):
                    with self.subTest(hm=HMS[hm], case=case):
                        lib.FixtureReset()
                        lib.FixtureFlags(0xFFFF)
                        if case in ("eggs", "last"):
                            for slot in range(PARTY_SIZE):
                                lib.FixtureMon(slot, 25, 1)
                                lib.FixtureMove(slot, 0, lib.FixtureMoveID(hm))
                        if case == "last":
                            lib.FixtureMon(5, 133, 0)
                        if case == "hole":
                            lib.FixtureMon(0, 25, 1)
                            lib.FixtureMon(2, 133, 0)
                            lib.FixtureMove(2, 0, lib.FixtureMoveID(hm))
                        if case == "first":
                            for slot in range(PARTY_SIZE):
                                lib.FixtureMon(slot, 25 + slot, 0)
                        expected = {"last": 5, "first": 0}.get(case, PARTY_SIZE)
                        self.assertEqual(lib.FixtureSelect(hm, True), expected)
                        lib.FixtureScript(hm, True)
                        self.assertEqual(lib.FixtureResult(), expected)
                        self.assertEqual(lib.FixtureSpecies(), 321 if expected == PARTY_SIZE else (133 if expected == 5 else 25))
                        self.assertEqual(lib.FixtureInvalidReads(), 0)

    def test_non_hms_keep_known_move_and_optional_unlock_policy(self):
        for lib in self.libs.values():
            for move in range(8, 16):
                with self.subTest(move=move):
                    lib.FixtureReset()
                    lib.FixtureMon(0, 25, 0)
                    lib.FixtureMon(1, 133, 0)
                    self.assertEqual(lib.FixtureSelect(move, False), PARTY_SIZE)
                    lib.FixtureMove(1, 2, lib.FixtureMoveID(move))
                    self.assertEqual(lib.FixtureSelect(move, False), 1)
                    self.assertEqual(lib.FixtureSelect(move, True), PARTY_SIZE if move in (14, 15) else 1)
                    lib.FixtureMon(1, 133, 1)
                    self.assertEqual(lib.FixtureSelect(move, False), PARTY_SIZE)

    def test_surf_uses_unlocked_non_egg_actor_and_already_surfing_blocks(self):
        for variant, lib in self.libs.items():
            lib.FixtureMon(0, 25, 0)
            lib.FixtureFlags(0xFFFF)
            self.assertTrue(lib.PartyHasMonWithSurf())
            lib.FixtureSurfing(1)
            self.assertFalse(lib.PartyHasMonWithSurf())
            lib.FixtureSurfing(0)
            lib.FixtureMon(0, 25, 1)
            lib.FixtureMove(0, 0, lib.FixtureMoveID(4))
            self.assertFalse(lib.PartyHasMonWithSurf())
            lib.FixtureMon(0, 25, 0)
            for flags in ((0, 1 << 12) if variant == "frlg" else (0, 1 << 4, 1 << 12)):
                lib.FixtureFlags(flags)
                self.assertFalse(lib.PartyHasMonWithSurf())
            lib.FixtureReset()
            lib.FixtureFlags(0xFFFF)
            self.assertFalse(lib.PartyHasMonWithSurf())
            self.assertEqual(lib.FixtureInvalidReads(), 0)

    def actions(self, lib):
        return [lib.FixtureAction(i) for i in range(lib.FixtureCount())]

    def test_root_preserves_four_known_moves_and_has_only_one_hm_entry(self):
        for variant, lib in self.libs.items():
            lib.FixtureFlags(0xFFFF)
            lib.FixtureMon(0, 25, 0)
            lib.FixtureMon(1, 133, 0)
            for slot, move in enumerate((0, 1, 8, 9)):
                lib.FixtureMove(0, slot, lib.FixtureMoveID(move))
            lib.FixtureRoot()
            actions = self.actions(lib)
            self.assertEqual(len(actions), 9)
            self.assertEqual(actions[0], 0)  # Summary
            self.assertEqual(actions[-3:], [1, 3, 2])  # Switch, Item, Cancel
            self.assertEqual(actions.count(lib.FixtureHMEntry()), 1)
            base = actions[1]
            self.assertEqual(actions[1:5], [base, base + 1, base + 8, base + 9])
            self.assertEqual(lib.FixtureCapacity(), 9)
            self.assertTrue(lib.FixtureCanaries())
            self.assertEqual((lib.FixtureTop(), lib.FixtureHeight()), (1, 18))

    def test_root_hm_entry_depends_on_gate_not_learning(self):
        for variant, lib in self.libs.items():
            lib.FixtureMon(0, 25, 0)
            for flags in (0, 0xFF00):
                lib.FixtureFlags(flags)
                lib.FixtureRoot()
                self.assertEqual(self.actions(lib), [0, 3, 2])
            lib.FixtureFlags(0xFF)
            lib.FixtureRoot()
            self.assertEqual(self.actions(lib), [0, lib.FixtureHMEntry(), 3, 2] if variant == "frlg" else [0, 3, 2])
            lib.FixtureFlags(0xFFFF)
            lib.FixtureRoot()
            self.assertEqual(self.actions(lib), [0, lib.FixtureHMEntry(), 3, 2])
            lib.FixtureItem(1)
            lib.FixtureRoot()
            self.assertEqual(self.actions(lib), [0, lib.FixtureHMEntry(), 7, 2])
            lib.FixturePike(1)
            lib.FixtureRoot()
            self.assertEqual(self.actions(lib), [0, lib.FixtureHMEntry(), 2])

    def test_submenu_all_eight_hms_cancel_capacity_window_and_input(self):
        for lib in self.libs.values():
            self.assertNotEqual(lib.FixtureHMEntry(), 2**32 - 1, "HMs submenu is absent")
            lib.FixtureFlags(0xFFFF)
            lib.FixtureRoot()
            lib.FixtureSubmenu()
            actions = self.actions(lib)
            self.assertEqual(len(actions), 9)
            self.assertEqual(actions[:8], list(range(actions[0], actions[0] + 8)))
            self.assertEqual(actions[-1], 2)
            self.assertEqual(lib.FixtureCapacity(), 9)
            self.assertTrue(lib.FixtureCanaries())
            self.assertEqual((lib.FixtureTop(), lib.FixtureHeight()), (1, 18))
            self.assertTrue(lib.FixtureCursorReset())
            self.assertTrue(lib.FixtureInputHandler())
            self.assertGreaterEqual(lib.FixtureRemoved(), 1)

    def test_submenu_each_single_unlock_and_all_locked_show_only_allowed_actions(self):
        for variant, badges in (("emerald", EMERALD_BADGES), ("frlg", FRLG_BADGES)):
            lib = self.libs[variant]
            self.assertNotEqual(lib.FixtureHMEntry(), 2**32 - 1, "HMs submenu is absent")
            lib.FixtureFlags(0xFFFF)
            lib.FixtureSubmenu()
            base = lib.FixtureAction(0)
            for hm in range(8):
                with self.subTest(variant=variant, hm=HMS[hm]):
                    lib.FixtureFlags(self.gate(hm, badges))
                    lib.FixtureSubmenu()
                    expected = [base + i for i in range(8) if badges[i] == badges[hm]] if variant == "frlg" else [base + hm]
                    self.assertEqual(self.actions(lib), expected + [2])
                    self.assertTrue(lib.FixtureCanaries())
            lib.FixtureFlags(0)
            lib.FixtureSubmenu()
            self.assertEqual(self.actions(lib), [2])


if __name__ == "__main__":
    unittest.main()
