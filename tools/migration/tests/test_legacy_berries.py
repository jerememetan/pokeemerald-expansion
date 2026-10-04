"""Verify berry restoration against the pinned archive using actual C kernels.

Run with native ``cc`` available (for example, through WSL). Compiler failures
are test failures, not silently skipped coverage.
"""

from pathlib import Path
import re
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = "f5e81e85df6fe40ae490bf7268d0186d7f0426ed"
EXPECTED_VARIETIES = {
    "BERRY_TREE_ROUTE_116_PINAP_1": "BERRY_ID_CHERI",
    "BERRY_TREE_ROUTE_115_BLUK_1": "BERRY_ID_ORAN",
    "BERRY_TREE_ROUTE_115_BLUK_2": "BERRY_ID_ORAN",
    "BERRY_TREE_ROUTE_110_NANAB_1": "BERRY_ID_ORAN",
    "BERRY_TREE_ROUTE_110_NANAB_2": "BERRY_ID_PERSIM",
    "BERRY_TREE_ROUTE_121_NANAB_2": "BERRY_ID_SITRUS",
    "BERRY_TREE_ROUTE_123_PECHA": "BERRY_ID_SITRUS",
    "BERRY_TREE_ROUTE_123_RAWST": "BERRY_ID_SITRUS",
}


def archived_source(path):
    return subprocess.run(
        ["git", "show", f"{ARCHIVE}:{path}"], cwd=ROOT,
        check=True, capture_output=True, text=True,
    ).stdout


def reset_commands(source):
    match = re.search(
        r"(?ms)^EventScript_ResetAllBerries::\s*\n(.*?)(?=^\w+::)",
        source,
    )
    if match is None:
        raise AssertionError("initial berry reset block missing")
    adapted = re.sub(
        r"ITEM_TO_BERRY\(ITEM_(\w+)_BERRY\)", r"BERRY_ID_\1", match[1],
    )
    return [
        re.sub(r"\s+", " ", line.split("@", 1)[0].strip())
        for line in adapted.splitlines()
        if line.split("@", 1)[0].strip()
    ]


def yield_definition(source):
    match = re.search(
        r"(?ms)^static u8 CalcBerryYieldInternal\([^;]*?\)\s*\n\{.*?^\}",
        source,
    )
    if match is None:
        raise AssertionError("yield definition missing")
    return match[0]


HARNESS = r"""
#include <stdint.h>
#include <stdio.h>
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
#define NUM_WATER_STAGES 4
static u16 randomValue;
static u16 Random(void) { return randomValue; }
"""

RUNNER = r"""
int main(void)
{
    static const u16 bounds[][2] = {{5, 2}, {10, 2}, {15, 10}, {1, 1}};
    for (unsigned pair = 0; pair < sizeof(bounds) / sizeof(bounds[0]); pair++)
    {
        for (u8 water = 0; water <= NUM_WATER_STAGES; water++)
        {
            for (unsigned rng = 0; rng <= UINT16_MAX; rng++)
            {
                randomValue = (u16)rng;
                u8 actual = CalcBerryYieldInternal(bounds[pair][0], bounds[pair][1], water);
                u8 legacy = LegacyCalcBerryYieldInternal(bounds[pair][0], bounds[pair][1], water);
#if OW_BERRY_MOISTURE
                u8 expected = (u8)bounds[pair][1];
                (void)legacy;
#else
                u8 expected = legacy;
#endif
                if (actual != expected)
                {
                    fprintf(stderr, "max=%u min=%u water=%u rng=%u: expected=%u actual=%u\n",
                            bounds[pair][0], bounds[pair][1], water, rng, expected, actual);
                    return 1;
                }
            }
        }
    }
    return 0;
}
"""


class LegacyBerryTests(unittest.TestCase):
    def test_all_initial_tree_commands_match_archive(self):
        self.assertEqual(
            reset_commands((ROOT / "data/scripts/new_game.inc").read_text()),
            reset_commands(archived_source("data/scripts/new_game.inc")),
        )

    def test_eight_custom_initial_varieties(self):
        commands = reset_commands((ROOT / "data/scripts/new_game.inc").read_text())
        trees = {}
        for command in commands:
            match = re.fullmatch(r"setberrytree (\w+), (\w+), (\w+)", command)
            if match:
                trees[match[1]] = match[2]
        for tree, variety in EXPECTED_VARIETIES.items():
            with self.subTest(tree=tree):
                self.assertEqual(trees[tree], variety)

    def check_c_kernel(self, moisture):
        current = yield_definition((ROOT / "src/berry.c").read_text())
        legacy = yield_definition(archived_source("src/berry.c")).replace(
            "CalcBerryYieldInternal", "LegacyCalcBerryYieldInternal", 1,
        )
        source = f"#define OW_BERRY_MOISTURE {moisture}\n" + HARNESS + current + "\n" + legacy + RUNNER
        with tempfile.TemporaryDirectory(prefix="legacy-berries-") as directory:
            runner = Path(directory) / "runner"
            compiled = subprocess.run(
                ["cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-x", "c", "-", "-o", str(runner)],
                input=source, capture_output=True, text=True,
            )
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            result = subprocess.run([str(runner)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_default_yields_match_archive_for_every_rng_value(self):
        self.check_c_kernel(moisture=0)

    def test_optional_moisture_yields_remain_minimum(self):
        self.check_c_kernel(moisture=1)


if __name__ == "__main__":
    unittest.main()
