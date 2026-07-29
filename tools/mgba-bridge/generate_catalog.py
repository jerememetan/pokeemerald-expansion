"""Generate a local symbolic battle-agent catalog from repository constants."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


class CatalogError(ValueError):
    """Raised when a constant table cannot produce an unambiguous catalog."""


_DEFINE = re.compile(r"^\s*#define\s+([A-Z][A-Z0-9_]*)\s+([0-9]+)\s*(?://.*)?$")


def parse_constants(
    text: str,
    prefix: str,
    *,
    ignored_names: set[str] | None = None,
    ignored_prefixes: tuple[str, ...] = (),
) -> dict[str, str]:
    """Return numeric-string IDs mapped to prefix-stripped constant names."""
    result: dict[str, str] = {}
    ignored_names = ignored_names or set()
    for line in text.splitlines():
        match = _DEFINE.match(line)
        if match is None:
            continue
        name, number = match.groups()
        if not name.startswith(prefix):
            continue
        if name in ignored_names or name.startswith(ignored_prefixes):
            continue
        if number in result:
            raise CatalogError(f"duplicate numeric ID {number} for {prefix}")
        result[number] = name[len(prefix) :]
    return dict(sorted(result.items(), key=lambda item: int(item[0])))


def build_catalog(repository: Path) -> dict[str, dict[str, str]]:
    sources = {
        "species": ("include/constants/species.h", "SPECIES_"),
        "moves": ("include/constants/moves.h", "MOVE_"),
        "abilities": ("include/constants/abilities.h", "ABILITY_"),
        "items": ("include/constants/items.h", "ITEM_"),
        "effects": ("include/constants/battle_move_effects.h", "EFFECT_"),
    }
    return {
        name: parse_constants(
            (repository / relative).read_text(encoding="utf-8"),
            prefix,
            ignored_prefixes=("ITEM_USE_",) if name == "items" else (),
        )
        for name, (relative, prefix) in sources.items()
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    catalog = build_catalog(args.repository.resolve())
    args.output.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
