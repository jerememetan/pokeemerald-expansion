#!/usr/bin/env python3
"""Convert archived trainer data and merge matching teams into a candidate .party file."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


LEGACY_REF = "archive/master-pre-1.16.3"
CURRENT_PARTY = Path("src/data/trainers.party")
UPSTREAM_CONVERTER = Path("migration_scripts/1.9/convert_trainer_parties.py")
HEADER_RE = re.compile(r"^=== (TRAINER_[A-Z0-9_]+) ===$", re.MULTILINE)
CURRENT_SYNTAX_RENAMES = {
    "Urshifu Single-Style": "Urshifu Single Strike",
    "Urshifu Rapid-Style": "Urshifu Rapid Strike",
    "Zamazenta Crowned Shield": "Zamazenta Crowned",
    "Unown Qmark": "Unown Q",
    "Indeedee Male": "Indeedee M",
    "Setup First Turn": "Force Setup First Turn",
}


def git_show(path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{LEGACY_REF}:{path}"],
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout


def normalize_legacy_sources(parties: str, trainers: str) -> tuple[str, str, dict[str, int]]:
    """Repair only cosmetic legacy syntax the maintained converter does not accept."""
    changes: dict[str, int] = {}

    parties, changes["ability_spacing"] = re.subn(
        r"(?m)^(\s*\.ability)\s*=\s*ABILITY_", r"\1 = ABILITY_", parties
    )
    parties, changes["inline_pokemon_opening"] = re.subn(
        r"(?m)^\s*\{\s*\.lvl\s*=", "    {\n    .lvl =", parties
    )
    parties, changes["pokemon_opening_indentation"] = re.subn(
        r"(?m)^[ \t]+\{$", "    {", parties
    )
    parties, changes["pokemon_closing_indentation"] = re.subn(
        r"(?m)^\s*(\},?)\s*$", r"    \1", parties
    )
    parties, changes["numeric_shiny"] = re.subn(
        r"\.isShiny\s*=\s*1\s*,", ".isShiny = TRUE,", parties
    )
    parties, false_shiny = re.subn(
        r"\.isShiny\s*=\s*0\s*,", ".isShiny = FALSE,", parties
    )
    changes["numeric_shiny"] += false_shiny

    trainers, changes["female_music_default"] = re.subn(
        r"\.encounterMusic_gender\s*=\s*F_TRAINER_FEMALE\s*,",
        ".encounterMusic_gender = F_TRAINER_FEMALE | TRAINER_ENCOUNTER_MUSIC_MALE,",
        trainers,
    )
    return parties, trainers, {name: count for name, count in changes.items() if count}


def normalize_current_syntax(text: str) -> tuple[str, dict[str, int]]:
    changes: dict[str, int] = {}
    for legacy_name, current_name in CURRENT_SYNTAX_RENAMES.items():
        text, count = text.replace(legacy_name, current_name), text.count(legacy_name)
        if count:
            changes[legacy_name] = count
    return text, changes


def parse_party(text: str, source: str) -> tuple[str, list[str], dict[str, str]]:
    cursor = 0
    while True:
        whitespace = re.match(r"\s*", text[cursor:])
        assert whitespace is not None
        cursor += whitespace.end()
        if not text.startswith("/*", cursor):
            break
        comment_end = text.find("*/", cursor + 2)
        if comment_end == -1:
            raise ValueError(f"{source}: unterminated leading comment")
        cursor = comment_end + 2

    matches = [match for match in HEADER_RE.finditer(text) if match.start() >= cursor]
    if not matches:
        raise ValueError(f"{source}: no trainer blocks found")

    header = text[:matches[0].start()]

    order: list[str] = []
    blocks: dict[str, str] = {}
    for index, match in enumerate(matches):
        identifier = match.group(1)
        if identifier in blocks:
            raise ValueError(f"{source}: duplicate trainer identifier {identifier}")
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks[identifier] = text[match.start():end].rstrip() + "\n"
        order.append(identifier)
    return header.rstrip() + "\n\n", order, blocks


def convert_legacy() -> tuple[str, str, dict[str, int], dict[str, int]]:
    with tempfile.TemporaryDirectory(prefix="legacy-trainer-parties-") as directory:
        temporary = Path(directory)
        legacy_trainers = temporary / "trainers.h"
        legacy_parties = temporary / "trainer_parties.h"
        converted = temporary / "trainers.party"
        legacy_parties_text, legacy_trainers_text, normalizations = normalize_legacy_sources(
            git_show("src/data/trainer_parties.h"), git_show("src/data/trainers.h")
        )
        legacy_trainers.write_text(legacy_trainers_text.rstrip() + "\n", encoding="utf-8")
        legacy_parties.write_text(legacy_parties_text.rstrip() + "\n", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(UPSTREAM_CONVERTER), str(legacy_trainers), str(legacy_parties), str(converted)],
            text=True,
            capture_output=True,
        )
        if result.returncode:
            raise RuntimeError(result.stderr or result.stdout)
        diagnostics = result.stderr + result.stdout
        if diagnostics.strip():
            raise RuntimeError(f"upstream converter reported unsupported legacy data:\n{diagnostics}")
        converted_text, syntax_renames = normalize_current_syntax(converted.read_text(encoding="utf-8"))
        return converted_text, diagnostics, normalizations, syntax_renames


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--append-legacy-only", action="store_true")
    args = parser.parse_args()

    candidate = args.candidate.resolve()
    report_path = args.report.resolve()
    current_path = CURRENT_PARTY.resolve()
    if candidate == current_path and not args.apply:
        parser.error("--candidate must differ from src/data/trainers.party without --apply")
    if not UPSTREAM_CONVERTER.is_file():
        parser.error(f"missing upstream converter: {UPSTREAM_CONVERTER}")

    legacy_text, converter_output, normalizations, syntax_renames = convert_legacy()
    current_text = CURRENT_PARTY.read_text(encoding="utf-8")
    _legacy_header, legacy_order, legacy_blocks = parse_party(legacy_text, "converted legacy party")
    current_header, current_order, current_blocks = parse_party(current_text, str(CURRENT_PARTY))

    converted_ids = [identifier for identifier in current_order if identifier in legacy_blocks]
    current_only_ids = [identifier for identifier in current_order if identifier not in legacy_blocks]
    legacy_only_ids = [identifier for identifier in legacy_order if identifier not in current_blocks]
    if len(converted_ids) != len(set(converted_ids)):
        raise ValueError("matching trainer identifiers are not unique")

    candidate_order = current_order + (legacy_only_ids if args.append_legacy_only else [])
    candidate_text = current_header
    candidate_text += "\n\n".join(
        legacy_blocks.get(identifier, current_blocks.get(identifier, "")).rstrip()
        for identifier in candidate_order
    )
    candidate_text = "\n".join(line.rstrip() for line in candidate_text.splitlines()) + "\n"
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_bytes(candidate_text.encode("utf-8"))

    report = {
        "source_refs": {
            "legacy_ref": LEGACY_REF,
            "current_source": str(CURRENT_PARTY.as_posix()),
            "upstream_converter": str(UPSTREAM_CONVERTER.as_posix()),
        },
        "legacy_count": len(legacy_order),
        "current_count": len(current_order),
        "converted_count": len(converted_ids),
        "converted_ids": converted_ids,
        "current_only_ids": current_only_ids,
        "legacy_only_ids": legacy_only_ids,
        "appended_legacy_only_ids": legacy_only_ids if args.append_legacy_only else [],
        "input_normalizations": normalizations,
        "current_syntax_renames": syntax_renames,
        "converter_diagnostics": converter_output.splitlines(),
        "candidate_sha256": hashlib.sha256(candidate_text.encode("utf-8")).hexdigest(),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_bytes((json.dumps(report, indent=2) + "\n").encode("utf-8"))

    if args.apply:
        current_path.write_bytes(candidate_text.encode("utf-8"))
        print(f"applied {current_path}; sha256={report['candidate_sha256']}")
    else:
        print(f"candidate: {candidate}")
        print(f"report: {report_path}")
        print(f"converted={len(converted_ids)} current-only={len(current_only_ids)} legacy-only={len(legacy_only_ids)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
