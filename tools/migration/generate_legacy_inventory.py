#!/usr/bin/env python3
"""Generate a path-level inventory of archived legacy changes."""

import argparse
import collections
import json
import subprocess
from pathlib import Path


def parse_name_status(raw):
    """Parse NUL-delimited ``git diff --name-status -z`` output."""
    fields = [field.decode("utf-8") for field in raw.split(b"\0") if field]
    records = []
    index = 0

    while index < len(fields):
        status = fields[index]
        index += 1
        if not status:
            raise ValueError("missing diff status")

        is_rename_or_copy = status[0] in {"R", "C"}
        path_count = 2 if is_rename_or_copy else 1
        if len(fields) - index < path_count:
            raise ValueError(f"missing path for diff status {status!r}")

        old_path = fields[index] if is_rename_or_copy else None
        path = fields[index + path_count - 1]
        index += path_count
        records.append({"status": status, "old_path": old_path, "path": path})

    return records


def classify_path(path):
    """Return the migration category for a changed path."""
    if path.startswith(("data/maps/", "data/layouts/")):
        return "maps-and-events"
    if path.startswith(
        ("graphics/ui_", "graphics/interface", "src/start_menu", "src/option_menu", "src/item_menu")
    ):
        return "ui-and-quality-of-life"
    if path.startswith(
        (
            "data/trainers",
            "data/wild",
            "src/data/pokemon/",
            "src/data/items",
            "src/data/moves",
            "graphics/pokemon/",
            "graphics/items/",
            "sound/",
        )
    ):
        return "game-content"
    if path.startswith(("src/", "include/", "asm/", "constants/", "data/battle", "test/battle/")):
        return "gameplay-and-battle"
    return "tooling-and-generated-output"


def render_inventory(base_ref, legacy_ref, records):
    """Return a deterministic inventory document for parsed diff records."""
    changes = []
    for record in records:
        change = dict(record)
        change["category"] = classify_path(change["path"])
        changes.append(change)
    changes.sort(key=lambda change: change["path"])

    summary = collections.Counter(change["category"] for change in changes)
    return {
        "base_ref": base_ref,
        "legacy_ref": legacy_ref,
        "summary": dict(sorted(summary.items())),
        "changes": changes,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="master", help="base Git reference")
    parser.add_argument(
        "--legacy", default="archive/master-pre-1.16.3", help="legacy Git reference"
    )
    parser.add_argument("--output", required=True, type=Path, help="output JSON file")
    args = parser.parse_args()

    result = subprocess.run(
        ["git", "diff", "--name-status", "-z", f"{args.base}...{args.legacy}"],
        check=True,
        stdout=subprocess.PIPE,
    )
    inventory = render_inventory(args.base, args.legacy, parse_name_status(result.stdout))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
