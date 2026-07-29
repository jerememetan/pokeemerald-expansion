"""Tests for the repository-constant catalog generator."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


BRIDGE_DIRECTORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BRIDGE_DIRECTORY))

from generate_catalog import CatalogError, parse_constants  # noqa: E402


class GenerateCatalogTests(unittest.TestCase):
    def test_parse_constants_uses_numeric_ids_and_symbolic_labels(self) -> None:
        catalog = parse_constants("#define MOVE_TACKLE 33\n#define MOVE_NONE 0\n", "MOVE_")

        self.assertEqual(catalog, {"0": "NONE", "33": "TACKLE"})

    def test_parse_constants_rejects_duplicate_numeric_ids(self) -> None:
        with self.assertRaises(CatalogError):
            parse_constants("#define MOVE_TACKLE 33\n#define MOVE_SCRATCH 33\n", "MOVE_")

    def test_parse_constants_ignores_explicit_non_item_sentinel(self) -> None:
        catalog = parse_constants(
            "#define ITEM_NONE 0\n#define ITEM_USE_MAIL 0\n",
            "ITEM_",
            ignored_names={"ITEM_USE_MAIL"},
        )

        self.assertEqual(catalog, {"0": "NONE"})

    def test_parse_constants_ignores_non_data_prefix(self) -> None:
        catalog = parse_constants(
            "#define ITEM_POKE_BALL 1\n#define ITEM_USE_PARTY_MENU 1\n",
            "ITEM_",
            ignored_prefixes=("ITEM_USE_",),
        )

        self.assertEqual(catalog, {"1": "POKE_BALL"})


if __name__ == "__main__":
    unittest.main()
