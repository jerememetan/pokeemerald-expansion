#!/usr/bin/env python3
"""Extract reviewed land-encounter removals and validate them against legacy data."""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import subprocess
import zipfile
from decimal import Decimal, InvalidOperation
from pathlib import Path
from xml.etree import ElementTree


LEGACY_PATH = "src/data/wild_encounters.json"
REVIEW_SHEET = "Encounter Review"
REVIEW_ROWS = range(6, 114)
ROSTER_COLUMNS = "GHIJKLMNOPQRS"
SELECTION_RE = re.compile(r"^(SPECIES_[A-Z0-9_]+) \(Lv (\d+)-(\d+)\)$")
SPREADSHEET_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
DOCUMENT_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
KNOWN_INVARIANT_DUPLICATES = {
    ("MAP_ROUTE130", "gRoute130", "SPECIES_OGERPON"),
    ("MAP_SAFARI_ZONE_NORTH", "gSafariZone_North", "SPECIES_GLOOM"),
    (
        "MAP_SHOAL_CAVE_LOW_TIDE_STAIRS_ROOM",
        "gShoalCave_LowTideStairsRoom",
        "SPECIES_SANDSLASH_ALOLAN",
    ),
    ("MAP_SAFARI_ZONE_SOUTHEAST", "gSafariZone_Southeast", "SPECIES_AUDINO"),
    ("MAP_MAGMA_HIDEOUT_2F_3R", "gMagmaHideout_2F_3R", "SPECIES_LYCANROC"),
    ("MAP_MIRAGE_TOWER_4F", "gMirageTower_4F", "SPECIES_ARON"),
}


def load_shared_strings(book: zipfile.ZipFile) -> list[str]:
    """Return the workbook's shared strings, including rich-text runs."""
    path = "xl/sharedStrings.xml"
    if path not in book.namelist():
        return []

    root = ElementTree.fromstring(book.read(path))
    return [
        "".join(node.text or "" for node in item.iter(f"{{{SPREADSHEET_NS}}}t"))
        for item in root.findall(f"{{{SPREADSHEET_NS}}}si")
    ]


def resolve_sheet_path(book: zipfile.ZipFile, sheet_name: str) -> str:
    """Resolve a worksheet name through the workbook relationship table."""
    workbook_path = "xl/workbook.xml"
    relationships_path = "xl/_rels/workbook.xml.rels"
    workbook = ElementTree.fromstring(book.read(workbook_path))
    matching_sheets = [
        sheet
        for sheet in workbook.findall(f".//{{{SPREADSHEET_NS}}}sheet")
        if sheet.get("name") == sheet_name
    ]
    if len(matching_sheets) != 1:
        raise ValueError(f"expected exactly one worksheet named {sheet_name!r}")

    relationship_id = matching_sheets[0].get(f"{{{DOCUMENT_REL_NS}}}id")
    if not relationship_id:
        raise ValueError(f"worksheet {sheet_name!r} has no relationship ID")

    relationships = ElementTree.fromstring(book.read(relationships_path))
    matches = [
        relationship
        for relationship in relationships.findall(f"{{{PACKAGE_REL_NS}}}Relationship")
        if relationship.get("Id") == relationship_id
    ]
    if len(matches) != 1:
        raise ValueError(f"worksheet relationship {relationship_id!r} is not unique")
    if matches[0].get("TargetMode") == "External":
        raise ValueError(f"worksheet {sheet_name!r} resolves to an external target")

    target = matches[0].get("Target")
    if not target:
        raise ValueError(f"worksheet relationship {relationship_id!r} has no target")
    if target.startswith("/"):
        sheet_path = posixpath.normpath(target.lstrip("/"))
    else:
        sheet_path = posixpath.normpath(posixpath.join(posixpath.dirname(workbook_path), target))
    if sheet_path == ".." or sheet_path.startswith("../") or sheet_path not in book.namelist():
        raise ValueError(f"worksheet target {target!r} is not a workbook member")
    return sheet_path


def read_cells(book: zipfile.ZipFile, sheet_path: str) -> dict[str, str]:
    """Read worksheet cells as strings from shared, inline, or scalar storage."""
    shared_strings = load_shared_strings(book)
    root = ElementTree.fromstring(book.read(sheet_path))
    cells: dict[str, str] = {}

    for cell in root.iter(f"{{{SPREADSHEET_NS}}}c"):
        reference = cell.get("r")
        if not reference:
            raise ValueError(f"cell without a reference in {sheet_path}")
        if reference in cells:
            raise ValueError(f"duplicate cell reference {reference} in {sheet_path}")

        cell_type = cell.get("t")
        value = cell.find(f"{{{SPREADSHEET_NS}}}v")
        if cell_type == "s":
            if value is None or value.text is None:
                raise ValueError(f"shared-string cell {reference} has no index")
            try:
                shared_string_index = int(value.text)
            except ValueError as error:
                raise ValueError(f"shared-string cell {reference} has an invalid index") from error
            if not 0 <= shared_string_index < len(shared_strings):
                raise ValueError(f"shared-string cell {reference} has an invalid index")
            cells[reference] = shared_strings[shared_string_index]
        elif cell_type == "inlineStr":
            cells[reference] = "".join(
                node.text or "" for node in cell.iter(f"{{{SPREADSHEET_NS}}}t")
            )
        else:
            cells[reference] = "" if value is None else value.text or ""

    return cells


def read_review_rows(path: Path) -> list[dict[str, object]]:
    """Read and structurally validate the 108 workbook decision rows."""
    selected_columns = ("A", "B", "D", "E", *ROSTER_COLUMNS)
    rows: list[dict[str, object]] = []

    with zipfile.ZipFile(path) as book:
        cells = read_cells(book, resolve_sheet_path(book, REVIEW_SHEET))

    for row_number in REVIEW_ROWS:
        references = [f"{column}{row_number}" for column in selected_columns]
        if not any(reference in cells for reference in references):
            raise ValueError(f"review row {row_number} is missing")

        map_name = cells.get(f"A{row_number}", "").strip()
        base_label = cells.get(f"B{row_number}", "").strip()
        selection = cells.get(f"D{row_number}", "").strip()
        slot_text = cells.get(f"E{row_number}", "").strip()
        roster = [cells.get(f"{column}{row_number}", "").strip() for column in ROSTER_COLUMNS]

        if not map_name:
            raise ValueError(f"review row {row_number} has a blank map")
        if not base_label:
            raise ValueError(f"review row {row_number} has a blank base_label")
        if not selection:
            raise ValueError(f"review row {row_number} has a blank selection")
        try:
            slot_number = Decimal(slot_text)
        except InvalidOperation as error:
            raise ValueError(f"review row {row_number} has a nonnumeric calculated slot") from error
        if not slot_number.is_finite() or slot_number != slot_number.to_integral_value():
            raise ValueError(f"review row {row_number} has a nonnumeric calculated slot")
        calculated_slot = int(slot_number)
        if calculated_slot not in range(1, 14):
            raise ValueError(f"review row {row_number} has an out-of-range calculated slot")
        if any(not entry for entry in roster):
            raise ValueError(f"review row {row_number} does not display exactly 13 roster entries")

        rows.append(
            {
                "row_number": row_number,
                "map": map_name,
                "base_label": base_label,
                "selection": selection,
                "calculated_slot": calculated_slot,
                "roster": roster,
            }
        )

    return rows


def git_json(ref: str, path: str) -> dict[str, object]:
    source = f"{ref}:{path}"
    try:
        result = subprocess.run(
            ["git", "show", source], check=True, capture_output=True, text=True
        )
    except subprocess.CalledProcessError as error:
        raise RuntimeError(f"failed to read {source}: {error.stderr.strip()}") from error
    return json.loads(result.stdout)


def _parse_displayed_encounter(value: str, context: str) -> tuple[str, int, int]:
    match = SELECTION_RE.fullmatch(value)
    if match is None:
        raise ValueError(f"{context} has invalid encounter text {value!r}")
    return match.group(1), int(match.group(2)), int(match.group(3))


def _archive_lookup(archive: dict[str, object]) -> dict[str, tuple[str, dict[str, object]]]:
    groups = archive.get("wild_encounter_groups")
    if not isinstance(groups, list):
        raise ValueError("legacy archive has no wild_encounter_groups list")

    lookup: dict[str, tuple[str, dict[str, object]]] = {}
    for group in groups:
        if not isinstance(group, dict) or not isinstance(group.get("label"), str):
            raise ValueError("legacy archive contains an invalid encounter group")
        group_label = group["label"]
        encounters = group.get("encounters")
        if not isinstance(encounters, list):
            raise ValueError(f"legacy encounter group {group_label} has no encounters list")
        for encounter in encounters:
            if not isinstance(encounter, dict) or not isinstance(encounter.get("base_label"), str):
                raise ValueError(f"legacy encounter group {group_label} has an invalid encounter")
            base_label = encounter["base_label"]
            if base_label in lookup:
                previous_group = lookup[base_label][0]
                raise ValueError(
                    f"legacy base_label {base_label} is duplicated in {previous_group} and {group_label}"
                )
            lookup[base_label] = (group_label, encounter)
    return lookup


def _encounter_tuple(encounter: object, context: str) -> tuple[str, int, int]:
    if not isinstance(encounter, dict):
        raise ValueError(f"{context} is not an encounter dictionary")
    species = encounter.get("species")
    min_level = encounter.get("min_level")
    max_level = encounter.get("max_level")
    if not isinstance(species, str) or type(min_level) is not int or type(max_level) is not int:
        raise ValueError(f"{context} has invalid species or levels")
    return species, min_level, max_level


def build_manifest(workbook: Path, legacy_ref: str) -> dict[str, object]:
    """Validate reviewed decisions and return their deterministic manifest."""
    review_rows = read_review_rows(workbook)
    lookup = _archive_lookup(git_json(legacy_ref, LEGACY_PATH))
    decisions: list[dict[str, object]] = []
    seen_identities: set[tuple[str, str]] = set()
    invariant_duplicates: set[tuple[str, str, str]] = set()
    single_match_count = 0

    for row in review_rows:
        row_number = row["row_number"]
        map_name = row["map"]
        base_label = row["base_label"]
        selection = row["selection"]
        calculated_slot = row["calculated_slot"]
        roster = row["roster"]
        identity = (map_name, base_label)
        if identity in seen_identities:
            raise ValueError(f"review row {row_number} duplicates decision identity {identity!r}")
        seen_identities.add(identity)

        if base_label not in lookup:
            raise ValueError(f"review row {row_number} has unknown base_label {base_label}")
        group_label, encounter = lookup[base_label]
        if encounter.get("map") != map_name:
            raise ValueError(f"review row {row_number} map does not match legacy {base_label}")

        land_mons = encounter.get("land_mons")
        if not isinstance(land_mons, dict) or not isinstance(land_mons.get("mons"), list):
            raise ValueError(f"legacy encounter {base_label} has no land roster")
        mons = land_mons["mons"]
        if len(mons) != 13:
            raise ValueError(f"legacy encounter {base_label} does not have 13 land entries")

        archive_roster = [
            _encounter_tuple(mon, f"legacy encounter {base_label} slot {index}")
            for index, mon in enumerate(mons, start=1)
        ]
        displayed_roster = [
            _parse_displayed_encounter(value, f"review row {row_number} roster slot {index}")
            for index, value in enumerate(roster, start=1)
        ]
        if displayed_roster != archive_roster:
            raise ValueError(f"review row {row_number} roster does not match legacy {base_label}")

        selected = _parse_displayed_encounter(selection, f"review row {row_number} selection")
        matching_indices = [index for index, value in enumerate(archive_roster) if value == selected]
        if not matching_indices:
            raise ValueError(f"review row {row_number} selection does not match legacy {base_label}")

        if len(matching_indices) == 1:
            single_match_count += 1
        else:
            if matching_indices != list(range(matching_indices[0], matching_indices[-1] + 1)):
                raise ValueError(f"review row {row_number} duplicate matches are not adjacent")
            matching_records = [mons[index] for index in matching_indices]
            if any(record != matching_records[0] for record in matching_records[1:]):
                raise ValueError(f"review row {row_number} duplicate records are not identical")
            deletion_results = [mons[:index] + mons[index + 1 :] for index in matching_indices]
            if any(result != deletion_results[0] for result in deletion_results[1:]):
                raise ValueError(f"review row {row_number} duplicate deletions are not invariant")
            invariant_duplicates.add((map_name, base_label, selected[0]))

        legacy_slot = matching_indices[0] + 1
        if calculated_slot != legacy_slot:
            raise ValueError(
                f"review row {row_number} calculated slot {calculated_slot} does not match "
                f"legacy slot {legacy_slot}"
            )

        decisions.append(
            {
                "group_label": group_label,
                "map": map_name,
                "base_label": base_label,
                "legacy_slot": legacy_slot,
                "species": selected[0],
                "min_level": selected[1],
                "max_level": selected[2],
            }
        )

    if invariant_duplicates != KNOWN_INVARIANT_DUPLICATES:
        missing = sorted(KNOWN_INVARIANT_DUPLICATES - invariant_duplicates)
        unexpected = sorted(invariant_duplicates - KNOWN_INVARIANT_DUPLICATES)
        raise ValueError(f"invariant duplicate set changed; missing={missing}, unexpected={unexpected}")

    decision_count = len(decisions)
    invariant_duplicate_count = len(invariant_duplicates)
    if (decision_count, single_match_count, invariant_duplicate_count) != (108, 102, 6):
        raise ValueError(
            "unexpected decision counts: "
            f"decisions={decision_count}, single={single_match_count}, "
            f"invariant_duplicates={invariant_duplicate_count}"
        )

    return {
        "source_refs": {
            "workbook": workbook.name,
            "legacy_ref": legacy_ref,
            "legacy_path": LEGACY_PATH,
        },
        "decision_count": decision_count,
        "single_match_count": single_match_count,
        "invariant_duplicate_count": invariant_duplicate_count,
        "decisions": decisions,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--legacy-ref", default="archive/master-pre-1.16.3")
    args = parser.parse_args()

    manifest = build_manifest(args.workbook, args.legacy_ref)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes((json.dumps(manifest, indent=2) + "\n").encode("utf-8"))
    print(
        f"wrote {args.output}: decisions={manifest['decision_count']} "
        f"single={manifest['single_match_count']} "
        f"invariant_duplicates={manifest['invariant_duplicate_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
