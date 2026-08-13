#!/usr/bin/env python3
"""Build and optionally apply the reviewed legacy wild-encounter merge."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


LEGACY_REF = "archive/master-pre-1.16.3"
LEGACY_COMMIT = "f5e81e85df6fe40ae490bf7268d0186d7f0426ed"
BASE_COMMIT = "024848a9e9c0ae30cbb9a269779504561d5443d3"
CURRENT_BASELINE_COMMIT = "f763eadb5030b543ba5a4827f79ddbe44c01ec62"
REMOVALS_SHA256 = "e99ce094a320517a39261eb7d6d3157692da9548969486f25c47be6aab447991"
ENCOUNTERS_PATH = Path("src/data/wild_encounters.json")
SPECIES_PATH = Path("include/constants/species.h")
REMOVALS_PATH = Path(
    "docs/superpowers/inventories/2026-08-10-legacy-wild-encounter-removals.json"
)
WILD_GROUP = "gWildMonHeaders"

EXPECTED_COUNTS = {
    "base": 135,
    "legacy": 145,
    "current": 399,
    "legacy_modified": 122,
    "legacy_only": 10,
    "current_only": 264,
    "both_changed_conflicts": 0,
}
EXPECTED_WILD_FINAL = 398
EXPECTED_FINAL = 409
EXPECTED_REMOVALS = 108
EXPECTED_ARCHIVE_ONLY = {
    "gFortreeCity0",
    "gLavaridgeTown0",
    "gLittlerootTown0",
    "gLittleroot_Extension0",
    "gMauvilleCity0",
    "gOldaleTown0",
    "gPetalburgWoodgrove0",
    "gRustboroCity0",
    "gScorchedSlab0",
    "gVerdanturf_Extension0",
}
EXPECTED_ARCHIVE_ONLY_ORDER = [
    "gLittlerootTown0",
    "gRustboroCity0",
    "gMauvilleCity0",
    "gOldaleTown0",
    "gLavaridgeTown0",
    "gVerdanturf_Extension0",
    "gLittleroot_Extension0",
    "gFortreeCity0",
    "gScorchedSlab0",
    "gPetalburgWoodgrove0",
]
SPECIES_ALIASES = {
    "SPECIES_ARCANINE_HISUIAN": "SPECIES_ARCANINE_HISUI",
    "SPECIES_AVALUGG_HISUIAN": "SPECIES_AVALUGG_HISUI",
    "SPECIES_BASCULEGION_FEMALE": "SPECIES_BASCULEGION_F",
    "SPECIES_BASCULEGION_MALE": "SPECIES_BASCULEGION_M",
    "SPECIES_BRAVIARY_HISUIAN": "SPECIES_BRAVIARY_HISUI",
    "SPECIES_CORSOLA_GALARIAN": "SPECIES_CORSOLA_GALAR",
    "SPECIES_DARMANITAN_GALARIAN": "SPECIES_DARMANITAN_GALAR",
    "SPECIES_ELECTRODE_HISUIAN": "SPECIES_ELECTRODE_HISUI",
    "SPECIES_FARFETCHD_GALARIAN": "SPECIES_FARFETCHD_GALAR",
    "SPECIES_FLORGES_WHITE_FLOWER": "SPECIES_FLORGES_WHITE",
    "SPECIES_GEODUDE_ALOLAN": "SPECIES_GEODUDE_ALOLA",
    "SPECIES_GOLEM_ALOLAN": "SPECIES_GOLEM_ALOLA",
    "SPECIES_GRIMER_ALOLAN": "SPECIES_GRIMER_ALOLA",
    "SPECIES_GROWLITHE_HISUIAN": "SPECIES_GROWLITHE_HISUI",
    "SPECIES_INDEEDEE_FEMALE": "SPECIES_INDEEDEE_F",
    "SPECIES_INDEEDEE_MALE": "SPECIES_INDEEDEE_M",
    "SPECIES_LILLIGANT_HISUIAN": "SPECIES_LILLIGANT_HISUI",
    "SPECIES_MAROWAK_ALOLAN": "SPECIES_MAROWAK_ALOLA",
    "SPECIES_MEOWSTIC_FEMALE": "SPECIES_MEOWSTIC_F",
    "SPECIES_MEOWSTIC_MALE": "SPECIES_MEOWSTIC_M",
    "SPECIES_MUK_ALOLAN": "SPECIES_MUK_ALOLA",
    "SPECIES_NINETALES_ALOLAN": "SPECIES_NINETALES_ALOLA",
    "SPECIES_PERSIAN_ALOLAN": "SPECIES_PERSIAN_ALOLA",
    "SPECIES_PONYTA_GALARIAN": "SPECIES_PONYTA_GALAR",
    "SPECIES_QWILFISH_HISUIAN": "SPECIES_QWILFISH_HISUI",
    "SPECIES_RAICHU_ALOLAN": "SPECIES_RAICHU_ALOLA",
    "SPECIES_RATTATA_ALOLAN": "SPECIES_RATTATA_ALOLA",
    "SPECIES_SANDSLASH_ALOLAN": "SPECIES_SANDSLASH_ALOLA",
    "SPECIES_SLIGGOO_HISUIAN": "SPECIES_SLIGGOO_HISUI",
    "SPECIES_SLOWBRO_GALARIAN": "SPECIES_SLOWBRO_GALAR",
    "SPECIES_SLOWKING_GALARIAN": "SPECIES_SLOWKING_GALAR",
    "SPECIES_SLOWPOKE_GALARIAN": "SPECIES_SLOWPOKE_GALAR",
    "SPECIES_STUNFISK_GALARIAN": "SPECIES_STUNFISK_GALAR",
    "SPECIES_TAUROS_PALDEAN_BLAZE_BREED": "SPECIES_TAUROS_PALDEA_BLAZE",
    "SPECIES_URSHIFU_RAPID_STRIKE_STYLE": "SPECIES_URSHIFU_RAPID_STRIKE",
    "SPECIES_URSHIFU_SINGLE_STRIKE_STYLE": "SPECIES_URSHIFU_SINGLE_STRIKE",
    "SPECIES_VOLTORB_HISUIAN": "SPECIES_VOLTORB_HISUI",
    "SPECIES_WEEZING_GALARIAN": "SPECIES_WEEZING_GALAR",
    "SPECIES_WOOPER_PALDEAN": "SPECIES_WOOPER_PALDEA",
    "SPECIES_ZIGZAGOON_GALARIAN": "SPECIES_ZIGZAGOON_GALAR",
    "SPECIES_ZOROARK_HISUIAN": "SPECIES_ZOROARK_HISUI",
}
DECISION_KEYS = {
    "group_label",
    "map",
    "base_label",
    "legacy_slot",
    "species",
    "min_level",
    "max_level",
}

JsonObject = dict[str, Any]
Identity = tuple[str, str]


@dataclass
class DestinationPlan:
    name: str
    path: Path
    preimage: bytes | None
    intended: bytes
    forward: Path
    restoration: Path | None
    backup: Path | None
    recovery_hold: Path
    retain_backup: bool = False
    retain_recovery_hold: bool = False
    retain_restoration: bool = False


def fail(message: str) -> None:
    raise ValueError(message)


def run_git(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            check=True,
            text=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as error:
        stderr = (error.stderr or "").strip()
        fail(f"git {' '.join(args)} failed: {stderr or 'no stderr'}")
    return result.stdout.strip()


def load_json_bytes(data: bytes, source: str) -> JsonObject:
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        fail(f"{source}: invalid UTF-8 JSON: {error}")
    if not isinstance(value, dict):
        fail(f"{source}: top-level JSON value must be an object")
    return value


def git_bytes(commit: str, path: Path) -> bytes:
    source = f"{commit}:{path.as_posix()}"
    try:
        result = subprocess.run(
            ["git", "show", source],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as error:
        stderr = error.stderr.decode("utf-8", errors="replace").strip()
        fail(f"git show {source} failed: {stderr or 'no stderr'}")
    return result.stdout


def git_json(commit: str, path: Path) -> JsonObject:
    return load_json_bytes(git_bytes(commit, path), f"{commit}:{path.as_posix()}")


def groups(document: JsonObject, source: str) -> list[JsonObject]:
    value = document.get("wild_encounter_groups")
    if not isinstance(value, list):
        fail(f"{source}: wild_encounter_groups must be a list")
    seen: set[str] = set()
    result: list[JsonObject] = []
    for group in value:
        if not isinstance(group, dict) or not isinstance(group.get("label"), str):
            fail(f"{source}: each encounter group must have a string label")
        label = group["label"]
        if label in seen:
            fail(f"{source}: duplicate encounter group label {label}")
        seen.add(label)
        if not isinstance(group.get("encounters"), list):
            fail(f"{source}: {label}.encounters must be a list")
        result.append(group)
    return result


def index_document(
    document: JsonObject, source: str
) -> tuple[list[Identity], dict[Identity, JsonObject]]:
    order: list[Identity] = []
    records: dict[Identity, JsonObject] = {}
    for group in groups(document, source):
        label = group["label"]
        for encounter in group["encounters"]:
            if not isinstance(encounter, dict) or not isinstance(encounter.get("base_label"), str):
                fail(f"{source}: every encounter must have a string base_label")
            identity = (label, encounter["base_label"])
            if identity in records:
                fail(f"{source}: duplicate identity {identity!r}")
            records[identity] = encounter
            order.append(identity)
    return order, records


def identity_json(identity: Identity) -> JsonObject:
    return {"group_label": identity[0], "base_label": identity[1]}


def resolve_sources(repo: Path) -> tuple[str, str, str]:
    legacy_commit = run_git("rev-parse", f"{LEGACY_REF}^{{commit}}")
    if legacy_commit != LEGACY_COMMIT:
        fail(
            f"{LEGACY_REF} resolved to {legacy_commit}, expected immutable audit commit "
            f"{LEGACY_COMMIT}"
        )
    base_commit = run_git("rev-parse", f"{BASE_COMMIT}^{{commit}}")
    if base_commit != BASE_COMMIT:
        fail(f"base commit resolved to {base_commit}, expected {BASE_COMMIT}")
    current_baseline_commit = run_git("rev-parse", f"{CURRENT_BASELINE_COMMIT}^{{commit}}")
    if current_baseline_commit != CURRENT_BASELINE_COMMIT:
        fail(
            f"current baseline commit resolved to {current_baseline_commit}, "
            f"expected {CURRENT_BASELINE_COMMIT}"
        )
    if Path(run_git("rev-parse", "--show-toplevel")).resolve() != repo:
        fail("repository root changed during source resolution")
    return legacy_commit, base_commit, current_baseline_commit


def require_within_repo(path: Path, repo: Path, name: str) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(repo)
    except ValueError:
        fail(f"{name} must be contained within repository root {repo}")
    return resolved


def validate_paths(args: argparse.Namespace, repo: Path) -> tuple[Path, Path, Path, Path]:
    target = require_within_repo(repo / ENCOUNTERS_PATH, repo, "target")
    candidate = require_within_repo(args.candidate, repo, "--candidate")
    report = require_within_repo(args.report, repo, "--report")
    removals = require_within_repo(args.removals, repo, "--removals")
    canonical_removals = require_within_repo(repo / REMOVALS_PATH, repo, "canonical removals")
    merger_script = require_within_repo(Path(__file__), repo, "merger script/advisory lock")
    species = require_within_repo(repo / SPECIES_PATH, repo, "species input")
    if removals != canonical_removals:
        fail(f"--removals must resolve to canonical manifest {canonical_removals}")

    outputs = {"candidate": candidate, "report": report}
    reserved = {
        "target": target,
        "removals": canonical_removals,
        "merger script/advisory lock": merger_script,
        "species input": species,
    }
    if candidate == report:
        fail(f"path collision: candidate and report both resolve to {candidate}")
    for output_name, output_path in outputs.items():
        for reserved_name, reserved_path in reserved.items():
            if output_path == reserved_path:
                fail(
                    f"path collision: {output_name} and {reserved_name} both resolve to "
                    f"{output_path}"
                )
    if not removals.is_file():
        fail(f"removal manifest does not exist: {removals}")
    return target, candidate, report, removals


def classify(
    base_order: list[Identity],
    base: dict[Identity, JsonObject],
    legacy_order: list[Identity],
    legacy: dict[Identity, JsonObject],
    current_order: list[Identity],
    current: dict[Identity, JsonObject],
) -> tuple[dict[str, int], list[Identity], list[Identity], list[Identity]]:
    base_ids = set(base)
    legacy_ids = set(legacy)
    current_ids = set(current)
    if not base_ids <= legacy_ids:
        fail(f"legacy source is missing base identities: {sorted(base_ids - legacy_ids)!r}")
    if not base_ids <= current_ids:
        fail(f"current source is missing base identities: {sorted(base_ids - current_ids)!r}")

    legacy_modified = [identity for identity in base_order if legacy[identity] != base[identity]]
    legacy_only = [identity for identity in legacy_order if identity not in base_ids]
    current_only = [identity for identity in current_order if identity not in base_ids]

    current_shared_changed = [
        identity for identity in base_order if current[identity] != base[identity]
    ]
    both_changed_conflicts = [
        identity
        for identity in legacy_modified
        if current[identity] != base[identity] and current[identity] != legacy[identity]
    ]
    if current_shared_changed:
        fail(
            "current shared identities differ from the immutable base; fail-closed merge "
            f"refuses upstream-only or converged changes: {current_shared_changed!r}"
        )

    counts = {
        "base": len(base),
        "legacy": len(legacy),
        "current": len(current),
        "legacy_modified": len(legacy_modified),
        "legacy_only": len(legacy_only),
        "current_only": len(current_only),
        "both_changed_conflicts": len(both_changed_conflicts),
    }
    if counts != EXPECTED_COUNTS:
        fail(f"classification mismatch: got {counts!r}, expected {EXPECTED_COUNTS!r}")

    archive_only_labels = [identity[1] for identity in legacy_only]
    if set(archive_only_labels) != EXPECTED_ARCHIVE_ONLY:
        fail(
            "archive-only base_label set changed: "
            f"got {sorted(archive_only_labels)!r}, expected {sorted(EXPECTED_ARCHIVE_ONLY)!r}"
        )
    if archive_only_labels != EXPECTED_ARCHIVE_ONLY_ORDER:
        fail(
            "archive-only archived relative order changed: "
            f"got {archive_only_labels!r}, expected {EXPECTED_ARCHIVE_ONLY_ORDER!r}"
        )
    if any(identity[0] != WILD_GROUP for identity in legacy_only):
        fail("every archive-only identity must belong to gWildMonHeaders")
    return counts, legacy_modified, legacy_only, current_only


def load_decisions(data: bytes, source: str) -> tuple[JsonObject, dict[Identity, JsonObject]]:
    if sha256(data) != REMOVALS_SHA256:
        fail(
            f"{source}: reviewed removal manifest sha256 mismatch; "
            f"expected {REMOVALS_SHA256}, got {sha256(data)}"
        )
    manifest = load_json_bytes(data, source)
    expected_top_keys = {
        "source_refs",
        "decision_count",
        "single_match_count",
        "invariant_duplicate_count",
        "decisions",
    }
    if set(manifest) != expected_top_keys:
        fail(f"removal manifest schema mismatch: keys are {sorted(manifest)!r}")
    source_refs = manifest["source_refs"]
    if not isinstance(source_refs, dict):
        fail("removal manifest source_refs must be an object")
    if set(source_refs) != {"workbook", "legacy_ref", "legacy_path"}:
        fail("removal manifest source_refs schema mismatch")
    if not isinstance(source_refs["workbook"], str) or not source_refs["workbook"]:
        fail("removal manifest workbook reference must be a nonempty string")
    if source_refs.get("legacy_ref") != LEGACY_REF:
        fail("removal manifest legacy_ref does not match the audited legacy ref")
    if source_refs.get("legacy_path") != ENCOUNTERS_PATH.as_posix():
        fail("removal manifest legacy_path does not match the encounter source")
    expected_manifest_counts = {
        "decision_count": EXPECTED_REMOVALS,
        "single_match_count": 102,
        "invariant_duplicate_count": 6,
    }
    for key, expected in expected_manifest_counts.items():
        if manifest.get(key) != expected:
            fail(f"removal manifest {key} is {manifest.get(key)!r}, expected {expected}")
    raw_decisions = manifest["decisions"]
    if not isinstance(raw_decisions, list) or len(raw_decisions) != EXPECTED_REMOVALS:
        fail(f"removal manifest must contain exactly {EXPECTED_REMOVALS} decisions")

    decisions: dict[Identity, JsonObject] = {}
    for index, decision in enumerate(raw_decisions):
        if not isinstance(decision, dict) or set(decision) != DECISION_KEYS:
            fail(f"removal decision {index} has an invalid schema")
        identity_values = (decision["group_label"], decision["base_label"])
        if not all(isinstance(value, str) and value for value in identity_values):
            fail(f"removal decision {index} has an invalid identity")
        identity: Identity = identity_values
        if identity in decisions:
            fail(f"duplicate removal decision for {identity!r}")
        if not isinstance(decision["map"], str) or not decision["map"]:
            fail(f"removal decision {index} has an invalid map")
        if not isinstance(decision["species"], str) or not decision["species"]:
            fail(f"removal decision {index} has an invalid species")
        for level_key in ("legacy_slot", "min_level", "max_level"):
            if type(decision[level_key]) is not int:
                fail(f"removal decision {index} has a non-integer {level_key}")
        if not 1 <= decision["legacy_slot"] <= 13:
            fail(f"removal decision {index} has an out-of-range legacy_slot")
        decisions[identity] = decision
    return manifest, decisions


def convert_record(
    identity: Identity,
    legacy_record: JsonObject,
    decisions: dict[Identity, JsonObject],
    alias_occurrences: dict[str, int],
) -> tuple[JsonObject, JsonObject | None]:
    converted = copy.deepcopy(legacy_record)
    land = converted.get("land_mons")
    removed_report: JsonObject | None = None
    if land is not None:
        if not isinstance(land, dict) or not isinstance(land.get("mons"), list):
            fail(f"legacy {identity!r} has an invalid land_mons table")
        mons = land["mons"]
        if len(mons) == 13:
            decision = decisions.pop(identity, None)
            if decision is None:
                fail(f"legacy 13-slot land table {identity!r} lacks a removal decision")
            if legacy_record.get("map") != decision["map"]:
                fail(f"removal decision map mismatch for {identity!r}")
            removed = mons.pop(decision["legacy_slot"] - 1)
            expected_removed = {
                "min_level": decision["min_level"],
                "max_level": decision["max_level"],
                "species": decision["species"],
            }
            if removed != expected_removed:
                fail(
                    f"removal decision slot contents mismatch for {identity!r}: "
                    f"got {removed!r}, expected {expected_removed!r}"
                )
            removed_report = {
                **identity_json(identity),
                "map": decision["map"],
                "legacy_slot": decision["legacy_slot"],
                **expected_removed,
            }
        if len(mons) != 12:
            fail(f"converted land table {identity!r} has {len(mons)} slots, expected 12")
    if identity in decisions and (land is None or len(land["mons"]) != 13):
        fail(f"removal decision targets non-13-slot converted record {identity!r}")
    for table_name in ("land_mons", "water_mons", "rock_smash_mons", "fishing_mons"):
        table = converted.get(table_name)
        if table is None:
            continue
        if not isinstance(table, dict) or not isinstance(table.get("mons"), list):
            fail(f"legacy {identity!r} has an invalid {table_name} table")
        for mon in table["mons"]:
            if not isinstance(mon, dict) or not isinstance(mon.get("species"), str):
                fail(f"legacy {identity!r} has an invalid species in {table_name}")
            old_species = mon["species"]
            new_species = SPECIES_ALIASES.get(old_species)
            if new_species is not None:
                mon["species"] = new_species
                alias_occurrences[old_species] += 1
    return converted, removed_report


def load_species_constants(data: bytes, source: str) -> set[str]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        fail(f"{source}: invalid UTF-8: {error}")
    constants = set(re.findall(r"\bSPECIES_[A-Z0-9_]+\b", text))
    if "SPECIES_NONE" not in constants:
        fail(f"could not parse species constants from {source}")
    if len(set(SPECIES_ALIASES.values())) != len(SPECIES_ALIASES):
        fail("species aliases must be one-to-one semantic renames")
    missing_alias_targets = set(SPECIES_ALIASES.values()) - constants
    if missing_alias_targets:
        fail(f"species alias targets are absent from current constants: {sorted(missing_alias_targets)!r}")
    return constants


def validate_species(candidate: JsonObject, constants: set[str]) -> None:
    unresolved: set[str] = set()
    for group in groups(candidate, "candidate species validation"):
        for encounter in group["encounters"]:
            for table_name in ("land_mons", "water_mons", "rock_smash_mons", "fishing_mons"):
                table = encounter.get(table_name)
                if table is None:
                    continue
                for mon in table["mons"]:
                    species = mon.get("species")
                    if species not in constants:
                        unresolved.add(str(species))
    if unresolved:
        fail(f"candidate contains unmapped or unknown species constants: {sorted(unresolved)!r}")


def group_metadata(document: JsonObject, source: str) -> list[JsonObject]:
    return [
        {key: copy.deepcopy(value) for key, value in group.items() if key != "encounters"}
        for group in groups(document, source)
    ]


def validate_final(
    candidate: JsonObject,
    current_document: JsonObject,
    current_order: list[Identity],
    current_records: dict[Identity, JsonObject],
    replacements: dict[Identity, JsonObject],
    legacy_only: list[Identity],
    current_only: list[Identity],
) -> None:
    candidate_order, candidate_records = index_document(candidate, "candidate")
    expected_order: list[Identity] = []
    for group in groups(current_document, "current"):
        label = group["label"]
        expected_order.extend((label, encounter["base_label"]) for encounter in group["encounters"])
        if label == WILD_GROUP:
            expected_order.extend(legacy_only)
    if candidate_order != expected_order:
        fail("candidate identity order differs from current order plus archived additions")
    if len(candidate_records) != EXPECTED_FINAL:
        fail(f"candidate has {len(candidate_records)} identities, expected {EXPECTED_FINAL}")
    if group_metadata(candidate, "candidate") != group_metadata(current_document, "current"):
        fail("candidate changed current group objects or group-level fields")
    wild_count = next(
        len(group["encounters"])
        for group in groups(candidate, "candidate")
        if group["label"] == WILD_GROUP
    )
    if wild_count != EXPECTED_WILD_FINAL:
        fail(f"candidate {WILD_GROUP} has {wild_count} records, expected {EXPECTED_WILD_FINAL}")
    for identity in current_order:
        expected = replacements.get(identity, current_records[identity])
        if candidate_records[identity] != expected:
            fail(f"candidate record mismatch at current identity {identity!r}")
    for identity in current_only:
        if candidate_records[identity] != current_records[identity]:
            fail(f"candidate changed current-only record {identity!r}")
    for identity, record in candidate_records.items():
        land = record.get("land_mons")
        if land is not None:
            if not isinstance(land, dict) or not isinstance(land.get("mons"), list):
                fail(f"candidate {identity!r} has invalid land_mons")
            if len(land["mons"]) != 12:
                fail(f"candidate land table {identity!r} has {len(land['mons'])} slots")


def json_bytes(value: JsonObject) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.parent / f".{path.name}.legacy-wild-{uuid.uuid4().hex}.tmp"
    if os.path.lexists(temp_path):
        fail(f"temporary output path unexpectedly exists: {temp_path}")
    try:
        stage_temp(temp_path, data)
        os.replace(temp_path, path)
    finally:
        cleanup_path(temp_path)


def cleanup_path(path: Path) -> None:
    """Remove a planned temporary, tolerating one interrupt at the unlink boundary."""
    first_error: BaseException | None = None
    for _attempt in range(2):
        try:
            path.unlink(missing_ok=True)
            return
        except BaseException as error:
            if not os.path.lexists(path):
                return
            first_error = first_error or error
    assert first_error is not None
    raise first_error


def stage_temp(temporary: Path, data: bytes) -> None:
    try:
        with temporary.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        cleanup_path(temporary)
        raise


def read_optional(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None


def acquire_apply_lock(path: Path) -> int:
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0))
    try:
        if os.name == "nt":
            import msvcrt

            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BaseException:
        os.close(fd)
        raise
    return fd


def release_apply_lock(fd: int) -> None:
    try:
        if os.name == "nt":
            import msvcrt

            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


def fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def publish_recovery(plan: DestinationPlan, message: str) -> str:
    assert plan.backup is not None
    recovery = plan.path.parent / (
        f".{plan.path.name}.legacy-wild-concurrent-edit-{uuid.uuid4().hex}.recovery"
    )
    try:
        os.link(plan.backup, recovery)
    except BaseException as error:
        plan.retain_backup = True
        return (
            f"{message}; recovery publication failed ({error}); retained only copy at "
            f"explicit backup path {plan.backup}"
        )
    return f"{message}; preserved captured edit at recovery file {recovery}"


def vacate_live_for_recovery(plan: DestinationPlan) -> tuple[bytes | None, str | None]:
    live = read_optional(plan.path)
    if live is None:
        return None, None
    try:
        os.replace(plan.path, plan.recovery_hold)
    except BaseException as error:
        actual = read_optional(plan.path)
        if actual is None and read_optional(plan.recovery_hold) == live:
            return live, None
        return actual, f"{plan.name} could not atomically vacate live path: {error}"
    captured = read_optional(plan.recovery_hold)
    return captured, None


def install_absent(source: Path, destination: Path, expected: bytes) -> bool:
    try:
        os.link(source, destination)
    except BaseException:
        return read_optional(destination) == expected
    return read_optional(destination) == expected


def recover_destination(plan: DestinationPlan) -> str | None:
    captured_live, vacate_error = vacate_live_for_recovery(plan)
    if vacate_error is not None:
        return vacate_error
    if captured_live not in (None, plan.intended):
        # A non-transaction live inode always wins. Reinstall it without clobbering.
        if not install_absent(plan.recovery_hold, plan.path, captured_live):
            plan.retain_recovery_hold = True
            return f"{plan.name} live concurrent edit retained at {plan.recovery_hold}"

    backup_data = read_optional(plan.backup) if plan.backup is not None else None
    if captured_live not in (None, plan.intended):
        if backup_data not in (None, plan.preimage, captured_live):
            return publish_recovery(
                plan,
                f"{plan.name} had distinct live and captured-backup concurrent edits; "
                f"live edit restored at {plan.path}",
            )
        return f"{plan.name} live concurrent edit restored and preserved at {plan.path}"

    restore_data = backup_data if backup_data is not None else plan.preimage
    restore_source = plan.backup if backup_data is not None else plan.restoration
    if restore_data is None:
        return None
    if restore_source is None:
        return f"{plan.name} has no captured backup or restoration file"
    if install_absent(restore_source, plan.path, restore_data):
        if backup_data != plan.preimage:
            return f"{plan.name} old-inode concurrent edit restored and preserved at {plan.path}"
        return None
    live_after = read_optional(plan.path)
    if live_after not in (None, restore_data):
        if backup_data not in (None, live_after):
            return publish_recovery(
                plan,
                f"{plan.name} restore raced with a live concurrent edit preserved at {plan.path}",
            )
        return f"{plan.name} live concurrent edit preserved at {plan.path}"
    if restore_source == plan.backup:
        plan.retain_backup = True
    else:
        plan.retain_restoration = True
    return (
        f"{plan.name} could not restore captured preimage; retained only restoration copy "
        f"at {restore_source}"
    )


def restore_after_failure(plans: list[DestinationPlan]) -> list[str]:
    results: list[str] = []
    for plan in reversed(plans):
        try:
            result = recover_destination(plan)
        except BaseException as error:
            result = f"{plan.name} recovery failed: {error}"
        if result is not None:
            results.append(result)
    return results


def vacate_and_install(plan: DestinationPlan) -> None:
    if plan.preimage is None:
        if read_optional(plan.path) is not None:
            fail(f"{plan.name} unexpectedly exists before no-clobber install")
    else:
        assert plan.backup is not None
        os.replace(plan.path, plan.backup)
        fsync_directory(plan.path.parent)
        backup_data = plan.backup.read_bytes()
        if backup_data != plan.preimage:
            fail(f"{plan.name} captured backup differs from expected preimage")
    try:
        os.link(plan.forward, plan.path)
    except FileExistsError as error:
        raise RuntimeError(
            f"{plan.name} no-clobber install found a concurrent live destination"
        ) from error
    fsync_directory(plan.path.parent)
    if plan.path.read_bytes() != plan.intended:
        fail(f"{plan.name} live destination differs after no-clobber install")
    if plan.backup is not None and plan.backup.read_bytes() != plan.preimage:
        fail(f"{plan.name} captured old inode changed after install")
    cleanup_path(plan.forward)
    fsync_directory(plan.path.parent)


def apply_with_report(
    target: Path,
    original: bytes,
    candidate_path: Path,
    candidate_data: bytes,
    report_path: Path,
    report_data: bytes,
) -> None:
    report_preimage = read_optional(report_path)
    transaction_id = uuid.uuid4().hex
    target_forward = target.parent / f".{target.name}.legacy-wild-{transaction_id}-forward"
    report_forward = report_path.parent / f".{report_path.name}.legacy-wild-{transaction_id}-forward"
    target_restore = target.parent / f".{target.name}.legacy-wild-{transaction_id}-rollback"
    report_restore = (
        report_path.parent / f".{report_path.name}.legacy-wild-{transaction_id}-rollback"
        if report_preimage is not None
        else None
    )
    target_backup = target.parent / f".{target.name}.legacy-wild-{transaction_id}-captured-backup"
    report_backup = (
        report_path.parent / f".{report_path.name}.legacy-wild-{transaction_id}-captured-backup"
        if report_preimage is not None
        else None
    )
    target_recovery_hold = target.parent / (
        f".{target.name}.legacy-wild-{transaction_id}-recovery-hold"
    )
    report_recovery_hold = report_path.parent / (
        f".{report_path.name}.legacy-wild-{transaction_id}-recovery-hold"
    )
    cleanup_paths = [
        target_forward,
        report_forward,
        target_restore,
        target_backup,
        target_recovery_hold,
        report_recovery_hold,
    ]
    if report_restore is not None:
        cleanup_paths.append(report_restore)
    if report_backup is not None:
        cleanup_paths.append(report_backup)
    for temporary in cleanup_paths:
        if os.path.lexists(temporary):
            fail(f"transaction temporary unexpectedly exists: {temporary}")

    lock_fd: int | None = None
    plans: list[DestinationPlan] = []
    try:
        try:
            lock_fd = acquire_apply_lock(Path(__file__).resolve())
        except (BlockingIOError, OSError) as error:
            fail(f"another wild-encounter apply holds the merger-script lock: {error}")

        if target.read_bytes() == candidate_data and read_optional(report_path) == report_data:
            if read_optional(candidate_path) != candidate_data:
                write_atomic(candidate_path, candidate_data)
            return

        write_atomic(candidate_path, candidate_data)
        if candidate_path.read_bytes() != candidate_data:
            fail("published candidate does not match the freshly validated candidate")
        if target.read_bytes() != original:
            fail("target changed after validation; refusing to apply stale candidate")
        if read_optional(report_path) != report_preimage:
            fail("report changed after validation; refusing to apply stale report")

        # Every cleanup and rollback path is enrolled before the first file is created.
        stage_temp(target_forward, candidate_data)
        stage_temp(report_forward, report_data)
        stage_temp(target_restore, original)
        if report_restore is not None:
            stage_temp(report_restore, report_preimage)

        plans = [
            DestinationPlan(
                "target",
                target,
                original,
                candidate_data,
                target_forward,
                target_restore,
                target_backup,
                target_recovery_hold,
            ),
            DestinationPlan(
                "report",
                report_path,
                report_preimage,
                report_data,
                report_forward,
                report_restore,
                report_backup,
                report_recovery_hold,
            ),
        ]

        try:
            vacate_and_install(plans[0])
            if read_optional(report_path) != report_preimage:
                fail("report changed before its atomic vacate")
            vacate_and_install(plans[1])
            if target.read_bytes() != candidate_data or report_path.read_bytes() != report_data:
                fail("destination pair changed before transaction commit")
            for plan in plans:
                if plan.backup is not None and plan.backup.read_bytes() != plan.preimage:
                    fail(f"{plan.name} captured old inode changed before transaction commit")
            for plan in plans:
                if plan.backup is not None:
                    cleanup_path(plan.backup)
            fsync_directory(target.parent)
            if report_path.parent != target.parent:
                fsync_directory(report_path.parent)
        except BaseException as apply_error:
            recovery_results = restore_after_failure(plans)
            if recovery_results:
                raise RuntimeError(
                    "wild-encounter apply aborted with concurrent-edit/recovery results: "
                    + "; ".join(recovery_results)
                ) from apply_error
            raise RuntimeError(
                "wild-encounter apply failed; target and report were restored"
            ) from apply_error
    finally:
        try:
            for temporary in cleanup_paths:
                owner = next(
                    (
                        plan
                        for plan in plans
                        if temporary in (plan.backup, plan.recovery_hold, plan.restoration)
                    ),
                    None,
                )
                if owner is not None and (
                    (temporary == owner.backup and owner.retain_backup)
                    or (temporary == owner.recovery_hold and owner.retain_recovery_hold)
                    or (temporary == owner.restoration and owner.retain_restoration)
                ):
                    continue
                cleanup_path(temporary)
        finally:
            if lock_fd is not None:
                release_apply_lock(lock_fd)


def build_merge(
    current_document: JsonObject,
    legacy_document: JsonObject,
    base_document: JsonObject,
    decisions_data: bytes,
    decisions_source: str,
    species_constants: set[str],
) -> tuple[JsonObject, JsonObject]:
    current_order, current_records = index_document(current_document, "current")
    legacy_order, legacy_records = index_document(legacy_document, "legacy")
    base_order, base_records = index_document(base_document, "base")
    counts, legacy_modified, legacy_only, current_only = classify(
        base_order,
        base_records,
        legacy_order,
        legacy_records,
        current_order,
        current_records,
    )
    _manifest, decisions = load_decisions(decisions_data, decisions_source)
    migration_ids = set(legacy_modified) | set(legacy_only)
    unexpected_decisions = set(decisions) - migration_ids
    if unexpected_decisions:
        fail(f"removal decisions target unexpected records: {sorted(unexpected_decisions)!r}")

    replacements: dict[Identity, JsonObject] = {}
    removed_by_identity: dict[Identity, JsonObject] = {}
    alias_occurrences = {legacy_name: 0 for legacy_name in SPECIES_ALIASES}
    conversion_order = [identity for identity in current_order if identity in migration_ids] + legacy_only
    for identity in conversion_order:
        converted, removed = convert_record(
            identity, legacy_records[identity], decisions, alias_occurrences
        )
        replacements[identity] = converted
        if removed is not None:
            removed_by_identity[identity] = removed
    if decisions:
        fail(f"unused removal decisions remain: {sorted(decisions)!r}")
    if len(removed_by_identity) != EXPECTED_REMOVALS:
        fail(
            f"consumed {len(removed_by_identity)} removal decisions, expected {EXPECTED_REMOVALS}"
        )

    candidate = copy.deepcopy(current_document)
    for group in groups(candidate, "candidate construction"):
        label = group["label"]
        group["encounters"] = [
            copy.deepcopy(replacements.get((label, encounter["base_label"]), encounter))
            for encounter in group["encounters"]
        ]
        if label == WILD_GROUP:
            group["encounters"].extend(copy.deepcopy(replacements[identity]) for identity in legacy_only)

    replaced = [identity for identity in current_order if identity in set(legacy_modified)]
    validate_final(
        candidate,
        current_document,
        current_order,
        current_records,
        replacements,
        legacy_only,
        current_only,
    )
    validate_species(candidate, species_constants)
    unused_aliases = [name for name, count in alias_occurrences.items() if count == 0]
    if unused_aliases:
        fail(f"audited species alias mappings were not consumed: {unused_aliases!r}")
    report_details: JsonObject = {
        "counts": {
            **counts,
            "replaced": len(replaced),
            "added": len(legacy_only),
            "retained_current_only": len(current_only),
            "removed_slots": len(removed_by_identity),
            "final": EXPECTED_FINAL,
            "final_gWildMonHeaders": EXPECTED_WILD_FINAL,
        },
        "replaced": [identity_json(identity) for identity in replaced],
        "added": [identity_json(identity) for identity in legacy_only],
        "retained_current_only": [identity_json(identity) for identity in current_only],
        "removed_slots": [
            removed_by_identity[identity]
            for identity in conversion_order
            if identity in removed_by_identity
        ],
        "species_aliases": {
            "distinct_count": len(SPECIES_ALIASES),
            "occurrence_count": sum(alias_occurrences.values()),
            "mappings": [
                {
                    "legacy_species": legacy_name,
                    "current_species": current_name,
                    "occurrence_count": alias_occurrences[legacy_name],
                }
                for legacy_name, current_name in SPECIES_ALIASES.items()
            ],
        },
    }
    return candidate, report_details


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--removals", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    repo = Path(run_git("rev-parse", "--show-toplevel")).resolve()
    target, candidate_path, report_path, removals_path = validate_paths(args, repo)
    legacy_commit, base_commit, current_baseline_commit = resolve_sources(repo)

    original = target.read_bytes()
    removals_data = removals_path.read_bytes()
    if sha256(removals_data) != REMOVALS_SHA256:
        fail(
            f"{removals_path}: reviewed removal manifest sha256 mismatch; "
            f"expected {REMOVALS_SHA256}, got {sha256(removals_data)}"
        )
    legacy_document = git_json(legacy_commit, ENCOUNTERS_PATH)
    base_document = git_json(base_commit, ENCOUNTERS_PATH)
    current_baseline_bytes = git_bytes(current_baseline_commit, ENCOUNTERS_PATH)
    current_document = load_json_bytes(
        current_baseline_bytes,
        f"{current_baseline_commit}:{ENCOUNTERS_PATH.as_posix()}",
    )
    species_data = git_bytes(current_baseline_commit, SPECIES_PATH)
    species_constants = load_species_constants(
        species_data, f"{current_baseline_commit}:{SPECIES_PATH.as_posix()}"
    )
    candidate_document, report_details = build_merge(
        current_document,
        legacy_document,
        base_document,
        removals_data,
        str(removals_path),
        species_constants,
    )
    candidate_data = json_bytes(candidate_document)
    if original not in (current_baseline_bytes, candidate_data):
        fail(
            "live encounter source is neither the exact audited pre-merge baseline nor "
            "the exact recomputed merged candidate"
        )
    report: JsonObject = {
        "source_refs": {
            "current_path": ENCOUNTERS_PATH.as_posix(),
            "current_commit": current_baseline_commit,
            "legacy_ref": LEGACY_REF,
            "legacy_commit": legacy_commit,
            "legacy_path": ENCOUNTERS_PATH.as_posix(),
            "base_commit": base_commit,
            "base_path": ENCOUNTERS_PATH.as_posix(),
            "removals_path": removals_path.relative_to(repo).as_posix(),
            "removals_sha256": sha256(removals_data),
            "species_path": SPECIES_PATH.as_posix(),
            "species_commit": current_baseline_commit,
            "species_sha256": sha256(species_data),
        },
        **report_details,
        "old_sha256": sha256(current_baseline_bytes),
        "candidate_sha256": sha256(candidate_data),
    }
    report_data = json_bytes(report)

    published_document = load_json_bytes(candidate_data, "fresh candidate")
    current_order, current_records = index_document(current_document, "current")
    legacy_order, legacy_records = index_document(legacy_document, "legacy")
    base_order, base_records = index_document(base_document, "base")
    _counts, legacy_modified, legacy_only, current_only = classify(
        base_order,
        base_records,
        legacy_order,
        legacy_records,
        current_order,
        current_records,
    )
    _candidate_order, candidate_records = index_document(candidate_document, "candidate")
    expected_replacements = {
        identity: candidate_records[identity]
        for identity in set(legacy_modified) | set(legacy_only)
    }
    validate_final(
        published_document,
        current_document,
        current_order,
        current_records,
        expected_replacements,
        legacy_only,
        current_only,
    )

    if args.apply:
        apply_with_report(
            target, original, candidate_path, candidate_data, report_path, report_data
        )
        print(f"applied {target.relative_to(repo).as_posix()}; sha256={report['candidate_sha256']}")
    else:
        write_atomic(candidate_path, candidate_data)
        write_atomic(report_path, report_data)
        print(f"candidate: {candidate_path.relative_to(repo).as_posix()}")
        print(f"report: {report_path.relative_to(repo).as_posix()}")
    print(
        f"replaced={report['counts']['replaced']} added={report['counts']['added']} "
        f"retained-current-only={report['counts']['retained_current_only']} "
        f"removed-slots={report['counts']['removed_slots']} conflicts=0"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, subprocess.CalledProcessError, ValueError, RuntimeError) as error:
        print(f"error: {error}", file=os.sys.stderr)
        raise SystemExit(1)
