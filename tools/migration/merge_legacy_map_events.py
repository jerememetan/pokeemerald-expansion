"""Audit and generate reviewed legacy map-event migration candidates."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Callable, Iterable

from map_event_merge import (
    AmbiguousMatchError,
    _validate_resolution_event,
    align_three_way,
    behavior_signature,
    exact_signature,
    extract_legacy_item_and_quantity,
    adapt_item_ball,
    merge_added_event,
    merge_base_event,
    resolve_reviewed_event,
    validate_resolution_consumption,
)


BASE_COMMIT = "024848a9e9c0ae30cbb9a269779504561d5443d3"
LEGACY_COMMIT = "f5e81e85df6fe40ae490bf7268d0186d7f0426ed"
CURRENT_BASELINE_COMMIT = "49c5f6dcaa57f0fc4dbc5bb114377ad49d6b9f5d"
LAYOUT_REPORT = Path(
    "docs/superpowers/inventories/2026-08-10-legacy-map-layout-report.json"
)
AUDIT_INVENTORY = Path(
    "docs/superpowers/inventories/2026-08-17-legacy-map-event-audit.json"
)
RESOLUTION_INVENTORY = Path(
    "docs/superpowers/inventories/2026-08-17-legacy-map-event-resolutions.json"
)
REPORT_INVENTORY = Path(
    "docs/superpowers/inventories/2026-08-17-legacy-map-event-report.json"
)

# Frozen against CURRENT_BASELINE_COMMIT and the reviewed Task 4 working-tree
# postimages. Whole-file hashes reject both missing changes and unrelated edits;
# closure hashes prove that each selected behavior landed at its intended label.
DEPENDENCY_POSTIMAGE_SPECS = {
    "data/maps/EverGrandeCity_PokemonLeague_1F/scripts.inc": {
        "old_sha256": "4ad7306b9c19a193234a50698335d12277ecfb9602c5a5438a207631e90026f4",
        "new_sha256": "5209b0a7d493ede9f539543821e55c11a4064fa383a01e77d84154a5dc22e9f8",
        "dependencies": [{"id": "dependency:EverGrandeCity_PokemonLeague_1F_EventScript_Clerk", "target_label": "EverGrandeCity_PokemonLeague_1F_EventScript_Clerk", "kind": "current_adaptation", "target_sha256": "aa5834985de0e937c43771692c0e3dcd0b694740f17c547b1bab1c05e0e88012", "rationale": "Legacy expanded shop inventory expressed with the current mart macro."}],
        "required_literals": [],
    },
    "data/maps/OldaleTown/scripts.inc": {
        "old_sha256": "21e4ed52e4a4dfe6a7f641bbb55f91e01abaf081266e7747f367c1411aca50ba",
        "new_sha256": "42723024a67fcb28b4f71b760c56a0311fe897b561df56d79a9b03e91612595a",
        "dependencies": [{"id": "dependency:OldaleTown_EventScript_MartEmployee", "target_label": "OldaleTown_EventScript_MartEmployee", "kind": "current_adaptation", "target_sha256": "a16d8e7a4807a2b5d3116b67e1eab0e69ced4868e9abcb8e5449dc2327b56d21", "rationale": "Legacy five-Potion gift expressed with the current item-give macro."}],
        "required_literals": [],
    },
    "data/maps/Route104/scripts.inc": {
        "old_sha256": "66a308b973b9c39331f141fd8eff010f9162dd018d6d6babbbf692f8c7c7bf88",
        "new_sha256": "b1158108f33dddbd080b2273f44d8b6ea80de1b55127e33f8214d15e882f96b4",
        "dependencies": [
            {"id": "dependency:Route104_EventScript_Boy2", "target_label": "Route104_EventScript_Boy2", "kind": "direct_legacy", "target_sha256": "2b479192cd9b6cd5063d88a838d7dbfe55c82696ca96221c5ebae6c15cf81b29", "rationale": "Exact reviewed legacy reusable-TM dialogue closure."},
            {"id": "dependency:Route104_EventScript_ExpertF", "target_label": "Route104_EventScript_ExpertF", "kind": "direct_legacy", "target_sha256": "1bce34743a157d239a27a8240754480b4fa80e2d27d8f51d4c4f82827da4c2c6", "rationale": "Exact reviewed legacy five-Chesto-Berry closure."},
            {"id": "dependency:Route104_EventScript_WhiteHerbFlorist", "target_label": "Route104_EventScript_WhiteHerbFlorist", "kind": "direct_legacy", "target_sha256": "5e94ef3b635a22b6142327dfe50368c8b74d83036e9df6b5e6183709af76179d", "rationale": "Exact reviewed legacy five-White-Herb closure."},
        ],
        "required_literals": [],
    },
    "data/maps/Route111/scripts.inc": {
        "old_sha256": "05c97b54a8a41a6a3ac61762a9c4f4287d8c245be32c2b8a8d2d5122aca301a9",
        "new_sha256": "54d020f266bb9b19b70e2f8407acdc1d6c5264b9d06234a34d20b0b09dc6259f",
        "dependencies": [{"id": "dependency:Route111_EventScript_Girl", "target_label": "Route111_EventScript_Girl", "kind": "direct_legacy", "target_sha256": "b7ffafcac5a8f709ed2ae8e23883f000f1558edc30775092b54e36acd5c7c099", "rationale": "Exact reviewed legacy five-Razz-Berry closure."}],
        "required_literals": [],
    },
    "data/maps/Route120/scripts.inc": {
        "old_sha256": "f198facc670a4c5e18ed8c6cac6eb3467bf9c7b7b9754ed07a12a89bb3fa34d5",
        "new_sha256": "093f63d9d4a9230e62860fc331e7231b57f58c62cb0ea0d6cddf6ce9deaabb95",
        "dependencies": [{"id": "dependency:Route120_EventScript_BadgeCheck", "target_label": "Route120_EventScript_BadgeCheck", "kind": "current_adaptation", "target_sha256": "4f404705a436935ec8cab359577bc759ef746be8b2dce6ab8a0f0dcea0f24519", "rationale": "Legacy six-badge gate and Red battle adapted to current local-id syntax."}],
        "required_literals": [],
    },
    "data/maps/Route123/scripts.inc": {
        "old_sha256": "38ee3124b082969df3f7b6cdedf00d0e8ae19a7f7e76225ba2cb9c09ac86dbe1",
        "new_sha256": "47f59c38687fd88f16f85f517a8c22cf019296cd87e1a23348de537a9d5a6c13",
        "dependencies": [{"id": "dependency:Route123_EventScript_BadgeChecker", "target_label": "Route123_EventScript_BadgeChecker", "kind": "current_adaptation", "target_sha256": "179787711346ad0ff7e8ac3d051ad36b1a1bd07c28070cb261e0b2a05340a529", "rationale": "Legacy eight-badge gate and Red battle adapted to current local-id syntax."}],
        "required_literals": [],
    },
    "data/maps/RustboroCity/scripts.inc": {
        "old_sha256": "58da962a0a271596e4ad5d0f17d1040865863ef1f5be54e5c1316ba5f7b8ddaa",
        "new_sha256": "9942fb4586e8eb45fd5327d94c5f52a5f28e5b765725ece4a2773160360341b7",
        "dependencies": [{"id": "dependency:RustboroCity_EventScript_Rival", "target_label": "RustboroCity_EventScript_Rival", "kind": "current_adaptation", "target_sha256": "29cd346fe272c156e4048be56352a7e337563a5507316f97b5954c855672ebef", "rationale": "Legacy mandatory rival battle preserved while retaining current trainer macros."}],
        "required_literals": [],
    },
    "data/maps/SootopolisCity/scripts.inc": {
        "old_sha256": "cf776e017a7593c593f9962e02e18928444b3f8c469491ebf204a2c5cdf8df67",
        "new_sha256": "ce17580eb487855b6e8b3b94b448a46c6d55b65ae20f49ab5aac400406df9f64",
        "dependencies": [
            {"id": "dependency:SootopolisCity_EventScript_Kiri", "target_label": "SootopolisCity_EventScript_Kiri", "kind": "current_adaptation", "target_sha256": "4824a62bd437e5f32c86e3a094e9adeefd34dd3bbf4d789e7cccada2c77e7a58", "rationale": "Legacy five-berry gifts expressed with current item-give macros."},
            {"id": "dependency:SootopolisCity_EventScript_Maxie", "target_label": "SootopolisCity_EventScript_Maxie", "kind": "current_adaptation", "target_sha256": "24f26f0a1d5c1ae4b110158e55aafc2976f1290dd1392f7376fa6f685bfd83b1", "rationale": "Legacy Cameruptite gift merged into the current Maxie/Archie departure flow."},
        ],
        "required_literals": [],
    },
    "data/scripts/field_move_scripts.inc": {
        "old_sha256": "61483d2eecafc9ea2e4695bd81fe6691864c831a950eabb8eae5814cce469dbe",
        "new_sha256": "57db6410dc8bd40f8a18f6d7019507dfa8a58c414db3e0e5d1215fdd8789afed",
        "dependencies": [
            {"id": "dependency:EventScript_CutTree", "target_label": "EventScript_CutTree", "kind": "current_adaptation", "target_sha256": "3f3a3862dbaeab37d680cca263fd7ba56606d61c9b682fd54282642e9724091e", "rationale": "Legacy badge-plus-HM gate preserved in the current follower-aware Cut flow."},
            {"id": "dependency:EventScript_RockSmash", "target_label": "EventScript_RockSmash", "kind": "current_adaptation", "target_sha256": "182f8b9c90135c16b76ed14c8c3265910a663934bb96690d0aa69ef62ee3aeb9", "rationale": "Legacy badge-plus-HM gate preserved in the current follower-aware Rock Smash flow."},
        ],
        "required_literals": [],
    },
    "data/scripts/move_tutors.inc": {
        "old_sha256": "51603d2dc63d7919c40b0d4782ca8cbacbcbc39948a90b1186cc4f0c38910088",
        "new_sha256": "dd7306bb83f68dfcbb144c152f0211f9b76c18ecd049d5d78795fe69de4822d0",
        "dependencies": [{"id": "dependency:SootopolisCity_PokemonCenter_1F_EventScript_DoubleEdgeTutor", "target_label": "SootopolisCity_PokemonCenter_1F_EventScript_DoubleEdgeTutor", "kind": "current_adaptation", "target_sha256": "b43ddbfd07d3bb41d1153cacaad27b5793b4910c57d8870f9dcd66b85abfd38a", "rationale": "Legacy repeatable tutor entry retained with the current tutor macros."}],
        "required_literals": [],
    },
    "include/constants/flags.h": {
        "old_sha256": "8edc96def953819e714c709b47169067c0f830468db190f9a23560e6091648cf",
        "new_sha256": "05c1ce13071a6ee47ba3b37f8ae4e9b975facb12a93602d5de66ec59053bd151",
        "dependencies": [],
        "required_literals": [
            {"id": "constant:FLAG_ROUTE120_BADGECHECKED", "text": "#define FLAG_ROUTE120_BADGECHECKED 0x22", "rationale": "Reviewed reuse of an upstream unused flag."},
            {"id": "constant:FLAG_ROUTE123_BADGECHECKED", "text": "#define FLAG_ROUTE123_BADGECHECKED 0x24", "rationale": "Reviewed reuse of an upstream unused flag."},
            {"id": "constant:FLAG_RECEIVED_CAMERUPTITE", "text": "#define FLAG_RECEIVED_CAMERUPTITE  0x265", "rationale": "Reviewed reuse of an upstream unused flag."},
        ],
    },
}
EXPECTED_SHARED_LAYOUTS = 61
EXPECTED_SCOPED_MAPS = 75
EXPECTED_ARCHIVE_CHANGED_MAPS = 69
EXPECTED_ALIGNMENT_RECORDS = 1643
EVENT_CATEGORIES = ("object_events", "warp_events", "coord_events", "bg_events")
CUSTOM_MAPS = (
    "Littleroot_Extension",
    "Verdanturf_Extension",
    "PetalburgWoodgrove",
)
NO_SCRIPT_SENTINELS = frozenset({"0", "0x0", "NULL"})
EXPECTED_ARCHIVE_CHANGED_MAP_NAMES = (
    "AlteringCave", "AquaHideout_B1F", "BattleFrontier_PokemonCenter_1F",
    "DewfordTown", "DewfordTown_PokemonCenter_1F", "EverGrandeCity",
    "EverGrandeCity_PokemonCenter_1F", "EverGrandeCity_PokemonLeague_1F",
    "FallarborTown_PokemonCenter_1F", "FortreeCity_PokemonCenter_1F",
    "JaggedPass", "LavaridgeTown_Gym_1F", "LavaridgeTown_Gym_B1F",
    "LilycoveCity", "LilycoveCity_PokemonCenter_1F", "MagmaHideout_1F",
    "MagmaHideout_2F_1R", "MauvilleCity", "MauvilleCity_PokemonCenter_1F",
    "MossdeepCity_Gym", "MossdeepCity_PokemonCenter_1F", "MtPyre_1F",
    "MtPyre_2F", "MtPyre_3F", "OldaleTown_PokemonCenter_1F",
    "PacifidlogTown_PokemonCenter_1F", "PetalburgCity_PokemonCenter_1F",
    "PetalburgWoods", "Route102", "Route103", "Route104", "Route106",
    "Route107", "Route108", "Route109", "Route110", "Route111",
    "Route112", "Route113", "Route114", "Route115", "Route116",
    "Route117", "Route118", "Route119", "Route119_WeatherInstitute_1F",
    "Route120", "Route121", "Route123", "Route124", "Route125",
    "Route126", "Route127", "Route128", "Route129", "Route130",
    "Route131", "RustboroCity", "RustboroCity_PokemonCenter_1F",
    "SeafloorCavern_Room1", "SeafloorCavern_Room3",
    "SlateportCity_PokemonCenter_1F", "SootopolisCity_Gym_1F",
    "SootopolisCity_Gym_B1F", "SootopolisCity_PokemonCenter_1F",
    "VerdanturfTown_PokemonCenter_1F", "VictoryRoad_1F", "VictoryRoad_B1F",
    "VictoryRoad_B2F",
)
PRELIMINARY_ARCHIVE_CHANGED_LABELS = frozenset(
    {
        "AlteringCave_Red_Fight", "Route104_EventScript_ExpertF",
        "Route104_EventScript_WhiteHerbFlorist", "Route104_EventScript_Darian",
        "Route111_EventScript_Girl", "Route120_EventScript_Callie",
        "Route120_EventScript_BadgeCheck", "Route123_EventScript_BadgeChecker",
        "RustboroCity_EventScript_Boy1",
    }
)
PRELIMINARY_BOTH_CHANGED_LABEL = "EverGrandeCity_PokemonLeague_1F_EventScript_Clerk"
SOURCE_COMMITS = {
    "base": BASE_COMMIT,
    "legacy": LEGACY_COMMIT,
    "current": CURRENT_BASELINE_COMMIT,
}
_LABEL_RE = re.compile(r"(?m)^([A-Za-z_][A-Za-z0-9_]*):{1,2}[ \t]*(?:\r?\n|$)")
_GENERATED_LINE_RE = re.compile(
    r'^[ \t]*#\s*(?:line\s+)?\d+(?:\s+"[^"]*")?[ \t]*(?:\r?\n|$)',
    re.MULTILINE,
)
_FINDITEM_COMMAND_RE = re.compile(
    r"(?m)^[ \t]*finditem[ \t]+(ITEM_[A-Za-z0-9_]+)(?:[ \t]*,[^\n]*)?[ \t]*$"
)
_ABSENT = object()


def repository_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True
    )
    if result.returncode:
        raise RuntimeError(
            "git rev-parse repository root failed: "
            + result.stderr.decode("utf-8", errors="replace").strip()
        )
    return Path(result.stdout.decode().strip()).resolve()


def _git(command: list[str], operation: str, *, allow_absent: bool = False) -> bytes:
    result = subprocess.run(["git", *command], capture_output=True)
    if result.returncode and not (allow_absent and result.returncode == 1):
        fatal = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"{operation} failed: {fatal or f'exit {result.returncode}'}")
    return result.stdout


def resolve_commit(ref: str) -> str:
    operation = f"git rev-parse {ref}^{{commit}}"
    value = _git(["rev-parse", "--verify", f"{ref}^{{commit}}"], operation).decode().strip()
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise RuntimeError(f"{operation} returned non-OID {value!r}")
    return value


def git_bytes(commit: str, path: str) -> bytes:
    """Read an immutable Git blob, retaining operation/ref:path on failure."""

    return _git(["show", f"{commit}:{path}"], f"git show {commit}:{path}")


def git_json(commit: str, path: str) -> dict[str, object]:
    raw = git_bytes(commit, path)
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid JSON object at {commit}:{path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object at {commit}:{path}")
    return value


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _resolution_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2) + "\n").encode("utf-8")


def _object(value: object, context: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{context} must be a JSON object")
    return value


def derive_scope(
    layout_report: dict[str, object],
    baseline_layouts: dict[str, object],
    baseline_maps: dict[str, dict[str, object]],
) -> tuple[set[str], list[str]]:
    """Purely derive shared layout IDs and their baseline map owners."""

    writes = layout_report.get("writes")
    layouts = baseline_layouts.get("layouts")
    if not isinstance(writes, list) or not isinstance(layouts, list):
        raise ValueError("layout report writes and baseline layouts must be lists")
    map_paths: set[str] = set()
    for index, raw in enumerate(writes):
        write = _object(raw, f"layout report write {index}")
        path = write.get("repository_path")
        if not isinstance(path, str) or "old_sha256" not in write:
            raise ValueError(f"layout report write {index} is malformed")
        if path.endswith("/map.bin") and write["old_sha256"] is not None:
            map_paths.add(path)
    layout_ids: set[str] = set()
    for index, raw in enumerate(layouts):
        layout = _object(raw, f"baseline layout {index}")
        if layout.get("blockdata_filepath") in map_paths:
            layout_id = layout.get("id")
            if not isinstance(layout_id, str):
                raise ValueError(f"baseline layout {index} has invalid id")
            layout_ids.add(layout_id)
    map_names = sorted(
        name for name, document in baseline_maps.items()
        if document.get("layout") in layout_ids
    )
    return layout_ids, map_names


def normalize_script_block(block: str) -> str:
    """Normalize only generated preprocessor line directives."""

    return _GENERATED_LINE_RE.sub("", block)


def _script_label_view(text: str) -> str:
    """Mask comments and strings without changing source offsets or newlines."""

    masked = list(text)
    state = "code"
    index = 0
    while index < len(text):
        character = text[index]
        following = text[index + 1] if index + 1 < len(text) else ""
        if state == "code":
            if character == '"':
                masked[index] = " "
                state = "string"
            elif character == "/" and following == "*":
                masked[index] = masked[index + 1] = " "
                state = "block_comment"
                index += 1
            elif character == "/" and following == "/":
                masked[index] = masked[index + 1] = " "
                state = "line_comment"
                index += 1
            elif character == "@":
                masked[index] = " "
                state = "line_comment"
        elif state == "string":
            if character == "\\" and following:
                if character not in "\r\n":
                    masked[index] = " "
                if following not in "\r\n":
                    masked[index + 1] = " "
                index += 1
            else:
                if character not in "\r\n":
                    masked[index] = " "
                if character == '"':
                    state = "code"
        elif state == "block_comment":
            if character not in "\r\n":
                masked[index] = " "
            if character == "*" and following == "/":
                masked[index + 1] = " "
                state = "code"
                index += 1
        else:
            if character in "\r\n":
                state = "code"
            else:
                masked[index] = " "
        index += 1
    return "".join(masked)


def parse_label_blocks(data: bytes, context: str) -> dict[str, str]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"dependency parse ambiguity at {context}: {error}") from error
    matches = list(_LABEL_RE.finditer(_script_label_view(text)))
    blocks: dict[str, str] = {}
    for index, match in enumerate(matches):
        label = match.group(1)
        if label in blocks:
            raise ValueError(f"dependency parse ambiguity: duplicate {label} in {context}")
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        normalized = normalize_script_block(text[match.start():end])
        # Separator whitespace belongs to neither defining label block.
        blocks[label] = normalized.rstrip() + "\n"
    return blocks


def expand_label_block(label: str, blocks: dict[str, str]) -> tuple[str, list[str]]:
    """Return a root block plus same-owner label blocks it directly depends on."""

    if label not in blocks:
        raise ValueError(f"dependency parse ambiguity: missing root label {label}")
    ordered: list[str] = []
    visited: set[str] = set()

    def visit(current: str) -> None:
        if current in visited:
            return
        visited.add(current)
        ordered.append(current)
        active = _script_label_view(blocks[current])
        for token in re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", active):
            if token in blocks:
                visit(token)

    visit(label)
    return "".join(blocks[current] for current in ordered), ordered


def classify_dependency_blocks(
    base: str | None,
    archive: str | None,
    current: str | None,
    *,
    external_common: bool = False,
) -> str:
    """Classify normalized three-way script behavior into one exact category."""

    if base is None and archive is None and current is None:
        raise ValueError("dependency owner is missing from base, archive, and current")
    if base is None:
        if archive is None:
            return "current-only"
        if current is None:
            return "archived-only"
        return "converged" if archive == current else "both-changed"
    if archive == base and current == base:
        return "external-common" if external_common else "identical"
    if archive != base and current == base:
        return "archive-changed/current-base"
    if archive == base and current != base:
        return "current-changed/archive-base"
    if archive == current:
        return "converged"
    return "both-changed"


def is_dependency_label(value: object) -> bool:
    return isinstance(value, str) and value not in NO_SCRIPT_SENTINELS


def _extract_item_evidence(block: str, label: str) -> tuple[str, bool]:
    """Extract an item, noting whether the approved one-item adapter can preserve it."""

    try:
        item, quantity = extract_legacy_item_and_quantity(block)
        return item, quantity == 1
    except ValueError as strict_error:
        without_blocks = re.sub(r"/\*.*?\*/", "", block, flags=re.DOTALL)
        active = re.sub(r"(?m)(?://|@).*$", "", without_blocks)
        operands = _FINDITEM_COMMAND_RE.findall(active)
        if len(operands) != 1:
            raise ValueError(f"{label}: {strict_error}") from strict_error
        # A quantity-bearing legacy command cannot be represented by the current
        # map event item field alone, so retain it as conflict evidence.
        return operands[0], False


def is_standardized_item_equivalent(
    adapter_compatible: bool, item_evidence: list[dict[str, object]]
) -> bool:
    return (
        adapter_compatible
        and bool(item_evidence)
        and all(evidence.get("equivalent") is True for evidence in item_evidence)
    )


class Sources:
    def __init__(self, commits: dict[str, str]) -> None:
        self.commits = commits
        self.hashes: dict[str, dict[str, str]] = {name: {} for name in commits}

    def bytes(self, name: str, path: str) -> bytes:
        data = git_bytes(self.commits[name], path)
        prior = self.hashes[name].setdefault(path, sha256(data))
        if prior != sha256(data):
            raise RuntimeError(f"immutable blob changed while reading {self.commits[name]}:{path}")
        return data

    def json(self, name: str, path: str) -> dict[str, object]:
        raw = self.bytes(name, path)
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError(
                f"invalid JSON object at {self.commits[name]}:{path}: {error}"
            ) from error
        return _object(value, f"{self.commits[name]}:{path}")


def _map_paths(commit: str) -> list[str]:
    raw = _git(
        ["ls-tree", "-r", "--name-only", commit, "--", "data/maps"],
        f"git ls-tree {commit}:data/maps",
    )
    return sorted(raw.decode("utf-8").splitlines())


def _event_arrays(document: dict[str, object], context: str) -> dict[str, list[dict[str, object]]]:
    arrays: dict[str, list[dict[str, object]]] = {}
    for category in EVENT_CATEGORIES:
        raw = document.get(category)
        if not isinstance(raw, list):
            raise ValueError(f"malformed events: {context}.{category} must be a list")
        events: list[dict[str, object]] = []
        for index, event in enumerate(raw):
            if not isinstance(event, dict):
                raise ValueError(
                    f"malformed events: {context}.{category}[{index}] must be an object"
                )
            try:
                _validate_resolution_event(category, event)
            except (TypeError, ValueError) as error:
                raise ValueError(
                    f"malformed events: {context}.{category}[{index}]: {error}"
                ) from error
            events.append(event)
        arrays[category] = events
    return arrays


def _event_hash(event: dict[str, object]) -> str:
    return sha256(json.dumps(event, sort_keys=True, separators=(",", ":")).encode())


def _match_record(
    map_name: str,
    category: str,
    method: str,
    base_index: int | None,
    archive_index: int | None,
    current_index: int | None,
    events: tuple[dict[str, object] | None, dict[str, object] | None, dict[str, object] | None],
) -> tuple[dict[str, object], dict[str, object] | None]:
    base_event, archive_event, current_event = events
    if "review_" in method:
        result = None
        conflict = f"{category}: weak ownership requires reviewed resolution"
        disposition = "unresolved"
        field_sources: dict[str, str] = {}
    elif base_event is not None:
        result = merge_base_event(category, base_event, archive_event, current_event)
        conflict = result.conflict
        disposition = result.disposition if conflict is None else "unresolved"
        field_sources = result.field_sources
    else:
        result = merge_added_event(category, archive_event, current_event)
        conflict = result.conflict
        disposition = result.disposition if conflict is None else "unresolved"
        field_sources = result.field_sources
    if base_index is not None:
        suffix = f"base-{base_index}"
    else:
        suffix = f"addition-archive-{archive_index if archive_index is not None else 'none'}-current-{current_index if current_index is not None else 'none'}"
    identifier = f"{map_name}:{category}:{suffix}"
    record: dict[str, object] = {
        "id": identifier,
        "base_index": base_index,
        "archive_index": archive_index,
        "current_index": current_index,
        "method": method,
        "disposition": disposition,
        "field_sources": field_sources,
        "event_sha256": {
            name: _event_hash(event) if event is not None else None
            for name, event in zip(("base", "archive", "current"), events)
        },
    }
    unresolved = None
    if conflict is not None:
        record["conflict"] = conflict
        unresolved = {
            "id": identifier,
            "issue_type": "event",
            "map": map_name,
            "category": category,
            "base_index": base_index,
            "archive_index": archive_index,
            "current_index": current_index,
            "reason": conflict,
            "evidence": {name: event for name, event in zip(("base", "archive", "current"), events)},
        }
    return record, unresolved


def build_ambiguity_slots(
    group_id: str,
    map_name: str,
    category: str,
    indices: dict[str, list[int]],
    evidence: dict[str, list[dict[str, object]]],
    reason: str,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    slot_count = max((len(values) for values in indices.values()), default=0)
    if slot_count == 0:
        raise ValueError(f"ambiguity group {group_id} has no candidate records")
    slot_ids = [f"{group_id}:slot-{number:02d}" for number in range(1, slot_count + 1)]
    group = {
        "id": group_id,
        "map": map_name,
        "category": category,
        "base_indices": list(indices["base"]),
        "archive_indices": list(indices["archive"]),
        "current_indices": list(indices["current"]),
        "reason": reason,
        "slot_ids": slot_ids,
        "evidence": {
            side: [
                {"index": index, "event": event}
                for index, event in zip(indices[side], evidence[side])
            ]
            for side in ("base", "archive", "current")
        },
    }
    archive_hashes = {
        str(index): _event_hash(event)
        for index, event in zip(indices["archive"], evidence["archive"])
    }
    current_hashes = {
        str(index): _event_hash(event)
        for index, event in zip(indices["current"], evidence["current"])
    }
    slots: list[dict[str, object]] = []
    for offset, slot_id in enumerate(slot_ids):
        base_index = indices["base"][offset] if offset < len(indices["base"]) else None
        base_event = evidence["base"][offset] if offset < len(evidence["base"]) else None
        slots.append(
            {
                "id": slot_id,
                "group_id": group_id,
                "slot": offset + 1,
                "issue_type": "ambiguity_slot",
                "map": map_name,
                "category": category,
                "base_index": base_index,
                "archive_index": None,
                "current_index": None,
                "allowed_archive_indices": list(indices["archive"]),
                "allowed_current_indices": list(indices["current"]),
                "reason": reason,
                "evidence": {
                    "group_id": group_id,
                    "base_event": base_event,
                    "archive_candidate_sha256": archive_hashes,
                    "current_candidate_sha256": current_hashes,
                },
            }
        )
    return group, slots


def _audit_category(
    map_name: str,
    category: str,
    base: list[dict[str, object]],
    archive: list[dict[str, object]],
    current: list[dict[str, object]],
) -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
]:
    remaining = {
        "base": list(enumerate(base)),
        "archive": list(enumerate(archive)),
        "current": list(enumerate(current)),
    }
    records: list[dict[str, object]] = []
    unresolved: list[dict[str, object]] = []
    ambiguity_groups: list[dict[str, object]] = []
    ambiguity_number = 0
    while any(remaining.values()):
        try:
            alignment = align_three_way(
                category,
                [event for _index, event in remaining["base"]],
                [event for _index, event in remaining["archive"]],
                [event for _index, event in remaining["current"]],
            )
        except AmbiguousMatchError as error:
            local = {
                "base": list(error.base_indices),
                "archive": list(error.archive_indices or ()),
                "current": list(error.current_indices or ()),
            }
            if local["base"]:
                selected_base = [remaining["base"][index][1] for index in local["base"]]
                exact_values = {exact_signature(event) for event in selected_base}
                behavior_values = {behavior_signature(category, event) for event in selected_base}
                for side in ("archive", "current"):
                    if local[side]:
                        continue
                    exact_candidates = [
                        index for index, (_original, event) in enumerate(remaining[side])
                        if exact_signature(event) in exact_values
                    ]
                    local[side] = exact_candidates or [
                        index for index, (_original, event) in enumerate(remaining[side])
                        if behavior_signature(category, event) in behavior_values
                    ]
            if not any(local.values()):
                raise ValueError(f"unresolved identity ambiguity without indices for {map_name}:{category}")
            original = {
                side: [remaining[side][index][0] for index in indices]
                for side, indices in local.items()
            }
            evidence = {
                side: [remaining[side][index][1] for index in indices]
                for side, indices in local.items()
            }
            ambiguity_number += 1
            identifier = f"{map_name}:{category}:ambiguity-{ambiguity_number:02d}"
            reason = str(error)
            record = {
                "id": identifier,
                "base_indices": original["base"],
                "archive_indices": original["archive"],
                "current_indices": original["current"],
                "method": "ambiguous",
                "disposition": "unresolved",
                "conflict": reason,
                "event_sha256": {
                    side: [_event_hash(event) for event in evidence[side]]
                    for side in evidence
                },
            }
            group, slots = build_ambiguity_slots(
                identifier, map_name, category, original, evidence, reason
            )
            record["resolution_slot_ids"] = group["slot_ids"]
            records.append(record)
            ambiguity_groups.append(group)
            unresolved.extend(slots)
            for side in remaining:
                remove = set(local[side])
                remaining[side] = [
                    item for index, item in enumerate(remaining[side]) if index not in remove
                ]
            continue

        for match in alignment.matches:
            indices = {
                "base": remaining["base"][match.base.index][0] if match.base else None,
                "archive": remaining["archive"][match.archive.index][0] if match.archive else None,
                "current": remaining["current"][match.current.index][0] if match.current else None,
            }
            events = (
                base[indices["base"]] if indices["base"] is not None else None,
                archive[indices["archive"]] if indices["archive"] is not None else None,
                current[indices["current"]] if indices["current"] is not None else None,
            )
            record, issue = _match_record(
                map_name, category, match.method, indices["base"], indices["archive"],
                indices["current"], events,
            )
            records.append(record)
            if issue is not None:
                unresolved.append(issue)
        remaining = {side: [] for side in remaining}

    records.sort(key=lambda item: item["id"])
    unresolved.sort(key=lambda item: item["id"])
    ambiguity_groups.sort(key=lambda item: item["id"])
    for side, events in (("base", base), ("archive", archive), ("current", current)):
        singular = [record[f"{side}_index"] for record in records if f"{side}_index" in record and record[f"{side}_index"] is not None]
        grouped = [index for record in records for index in record.get(f"{side}_indices", [])]
        covered = singular + grouped
        if sorted(covered) != list(range(len(events))) or len(covered) != len(set(covered)):
            raise ValueError(f"duplicate/unresolved identity ambiguity coverage for {map_name}:{category}:{side}: {covered}")
    return records, unresolved, ambiguity_groups


def _referenced_scripts(
    documents: dict[str, dict[str, dict[str, list[dict[str, object]]]]],
    map_audits: Iterable[dict[str, object]],
) -> tuple[set[str], dict[str, list[dict[str, object]]]]:
    labels: set[str] = set()
    references: dict[str, list[dict[str, object]]] = defaultdict(list)
    source_indices = (("base", "base"), ("legacy", "archive"), ("current", "current"))
    for map_audit in map_audits:
        map_name = str(map_audit["map"])
        categories = map_audit["categories"]
        for category in EVENT_CATEGORIES:
            relevant: dict[str, set[int]] = {source: set() for source in SOURCE_COMMITS}
            for record in categories[category]["alignments"]:
                if record["disposition"] == "unchanged":
                    continue
                for source, index_name in source_indices:
                    singular = record.get(f"{index_name}_index")
                    if singular is not None:
                        relevant[source].add(singular)
                    relevant[source].update(record.get(f"{index_name}_indices", []))
            for source in SOURCE_COMMITS:
                for index in sorted(relevant[source]):
                    event = documents[map_name][source][category][index]
                    label = event.get("script")
                    if is_dependency_label(label):
                        labels.add(label)
                        references[label].append(
                            {"map": map_name, "source": source, "category": category, "index": index}
                        )
    # These pinned diagnostics are behavior deltas behind otherwise unchanged
    # event records, so they are explicitly part of the relevant boundary.
    required_labels = PRELIMINARY_ARCHIVE_CHANGED_LABELS | {PRELIMINARY_BOTH_CHANGED_LABEL}
    for map_name in sorted(documents):
        for source in SOURCE_COMMITS:
            for category in EVENT_CATEGORIES:
                for index, event in enumerate(documents[map_name][source][category]):
                    label = event.get("script")
                    if label in required_labels:
                        labels.add(label)
                        reference = {
                            "map": map_name,
                            "source": source,
                            "category": category,
                            "index": index,
                        }
                        if reference not in references[label]:
                            references[label].append(reference)
    return labels, references


def _owner_paths(commit: str, labels: set[str]) -> set[str]:
    paths: set[str] = set()
    ordered = sorted(labels)
    for start in range(0, len(ordered), 80):
        expression = "^(" + "|".join(re.escape(label) for label in ordered[start:start + 80]) + ")::"
        output = _git(
            ["grep", "-l", "-E", expression, commit, "--", "data"],
            f"git grep labels {commit}:data",
            allow_absent=True,
        ).decode("utf-8")
        for line in output.splitlines():
            prefix = f"{commit}:"
            if not line.startswith(prefix):
                raise RuntimeError(f"unexpected git grep output for {commit}:data: {line!r}")
            path = line[len(prefix):]
            # Poryscript sources intentionally duplicate their generated scripts.inc.
            # The pinned event layer is assembled from the generated .inc owners.
            if path.endswith(".inc"):
                paths.add(path)
    return paths


def _dependency_inventory(
    sources: Sources,
    labels: set[str],
    references: dict[str, list[dict[str, object]]],
    documents: dict[str, dict[str, dict[str, list[dict[str, object]]]]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    definitions: dict[str, dict[str, tuple[str, str, list[str]]]] = {label: {} for label in labels}
    for source, commit in sources.commits.items():
        for path in sorted(_owner_paths(commit, labels)):
            blocks = parse_label_blocks(sources.bytes(source, path), f"{commit}:{path}")
            for label in labels & blocks.keys():
                if source in definitions[label]:
                    prior = definitions[label][source][0]
                    raise ValueError(
                        f"dependency parse ambiguity: {label} owned by both {prior} and {path} at {commit}"
                    )
                expanded, block_labels = expand_label_block(label, blocks)
                definitions[label][source] = (path, expanded, block_labels)

    dependencies: list[dict[str, object]] = []
    unresolved: list[dict[str, object]] = []
    for label in sorted(labels):
        found = definitions[label]
        blocks = {source: found.get(source, ("", None))[1] for source in SOURCE_COMMITS}
        owners = {source: found[source][0] if source in found else None for source in SOURCE_COMMITS}
        block_labels = {
            source: found[source][2] if source in found else [] for source in SOURCE_COMMITS
        }
        refs = sorted(references[label], key=lambda item: (item["map"], item["source"], item["category"], item["index"]))
        archive_item_refs: list[tuple[dict[str, object], str]] = []
        archive_block = blocks["legacy"]
        strict_item_equivalence = True
        if archive_block is not None and re.search(r"(?m)^\s*finditem\b", archive_block):
            item, strict_item_equivalence = _extract_item_evidence(archive_block, label)
            for reference in refs:
                if reference["source"] == "legacy" and reference["category"] == "object_events":
                    archive_item_refs.append((reference, item))
        item_evidence: list[dict[str, object]] = []
        if archive_item_refs and label != "Common_EventScript_FindItem":
            for reference, item in archive_item_refs:
                map_name = str(reference["map"])
                archive_event = documents[map_name]["legacy"]["object_events"][int(reference["index"])]
                candidates = [
                    (index, event) for index, event in enumerate(documents[map_name]["current"]["object_events"])
                    if event.get("script") == "Common_EventScript_FindItem"
                    and event.get("flag") == archive_event.get("flag")
                ]
                if len(candidates) != 1:
                    raise ValueError(
                        f"standardized item dependency {map_name}:{label} has {len(candidates)} current Common_EventScript_FindItem events for flag {archive_event.get('flag')}"
                    )
                index, event = candidates[0]
                item_evidence.append(
                    {
                        "map": map_name,
                        "archive_index": reference["index"],
                        "archive_label": label,
                        "finditem": item,
                        "flag": archive_event.get("flag"),
                        "current_index": index,
                        "current_label": "Common_EventScript_FindItem",
                        "current_item_field": event.get("trainer_sight_or_berry_tree_id"),
                        "equivalent": event.get("trainer_sight_or_berry_tree_id") == item,
                        "adapter_compatible": strict_item_equivalence,
                    }
                )
            if is_standardized_item_equivalent(
                strict_item_equivalence, item_evidence
            ):
                classification = "standardized item equivalent"
            else:
                classification = classify_dependency_blocks(
                    blocks["base"], blocks["legacy"], blocks["current"]
                )
        else:
            external = all(
                owner is None or not any(owner == f"data/maps/{reference['map']}/scripts.inc" for reference in refs)
                for owner in owners.values()
            )
            try:
                classification = classify_dependency_blocks(
                    blocks["base"], blocks["legacy"], blocks["current"],
                    external_common=external,
                )
            except ValueError as error:
                raise ValueError(f"dependency {label}: {error}") from error
        block_hashes = {
            source: sha256(block.encode("utf-8")) if block is not None else None
            for source, block in blocks.items()
        }
        identifier = f"dependency:{label}"
        dependency = {
            "id": identifier,
            "label": label,
            "classification": classification,
            "owners": owners,
            "normalized_block_sha256": block_hashes,
            "block_labels": block_labels,
            "references": refs,
            "item_equivalence": item_evidence,
            "normalized_blocks": blocks,
        }
        dependencies.append(dependency)
        if classification in {"archive-changed/current-base", "both-changed", "archived-only"}:
            base_refs = [reference for reference in refs if reference["source"] == "base"]
            archive_refs = [reference for reference in refs if reference["source"] == "legacy"]
            current_refs = [reference for reference in refs if reference["source"] == "current"]
            primary = (archive_refs or current_refs or base_refs or [None])[0]
            unresolved.append(
                {
                    "id": identifier,
                    "issue_type": "dependency",
                    "map": primary["map"] if primary else None,
                    "category": "dependency",
                    "base_index": base_refs[0]["index"] if base_refs else None,
                    "archive_index": archive_refs[0]["index"] if archive_refs else None,
                    "current_index": current_refs[0]["index"] if current_refs else None,
                    "reason": f"dependency behavior is {classification}",
                    "evidence": dependency,
                }
            )

    by_label = {item["label"]: item for item in dependencies}
    missing = sorted((PRELIMINARY_ARCHIVE_CHANGED_LABELS | {PRELIMINARY_BOTH_CHANGED_LABEL}) - by_label.keys())
    if missing:
        raise ValueError(f"preliminary dependency labels missing from audit: {missing}")
    return dependencies, unresolved


def _group_event(
    group: dict[str, object], side: str, index: int | None
) -> dict[str, object] | None:
    if index is None:
        return None
    candidates = [
        item for item in group["evidence"][side] if item["index"] == index
    ]
    if len(candidates) != 1:
        raise ValueError(
            f"ambiguity group {group['id']} has no unique {side} event at index {index}"
        )
    return candidates[0]["event"]


def _validate_event_resolution(
    entry: dict[str, object],
    category: str,
    base: dict[str, object] | None,
    archive: dict[str, object] | None,
    current: dict[str, object] | None,
) -> None:
    identifier = entry["id"]
    decision = entry["decision"]
    field_sources = entry["field_sources"]
    if decision != "merge_fields" and field_sources != {}:
        raise ValueError(
            f"resolution {identifier} field_sources must be empty for {decision}"
        )
    if decision == "use_archive":
        if archive is None:
            raise ValueError(f"resolution {identifier} cannot use absent archive event")
        _validate_resolution_event(category, archive)
        return
    if decision == "use_current":
        if current is None:
            raise ValueError(f"resolution {identifier} cannot use absent current event")
        _validate_resolution_event(category, current)
        return
    if decision == "delete":
        if base is None and archive is None and current is None:
            raise ValueError(f"resolution {identifier} cannot delete an empty slot")
        return
    if decision == "keep_both":
        if archive is None or current is None:
            raise ValueError(
                f"resolution {identifier} keep_both requires archive and current events"
            )
        _validate_resolution_event(category, archive)
        _validate_resolution_event(category, current)
        return
    if decision == "deduplicate":
        if archive is None or current is None:
            raise ValueError(
                f"resolution {identifier} deduplicate requires archive and current events"
            )
        if exact_signature(archive) != exact_signature(current):
            raise ValueError(
                f"resolution {identifier} cannot deduplicate non-equivalent events"
            )
        _validate_resolution_event(category, current)
        return
    if decision == "current_equivalent":
        raise ValueError(
            f"resolution {identifier} current_equivalent is dependency-only"
        )
    if decision != "merge_fields":
        raise ValueError(f"resolution {identifier} unsupported event decision {decision}")
    if base is None or archive is None or current is None:
        raise ValueError(
            f"resolution {identifier} merge_fields requires base, archive, and current events"
        )
    differing = {
        field
        for field in set(archive) | set(current)
        if archive.get(field, _ABSENT) != current.get(field, _ABSENT)
    }
    if not differing:
        raise ValueError(
            f"resolution {identifier} merge_fields has no differing fields"
        )
    if set(field_sources) != differing:
        raise ValueError(
            f"resolution {identifier} field_sources differ: "
            f"got={sorted(field_sources)}, expected={sorted(differing)}"
        )
    if any(source not in {"archive", "current"} for source in field_sources.values()):
        raise ValueError(f"resolution {identifier} has invalid field source")
    resolved: dict[str, object] = {}
    for field in sorted(set(archive) | set(current)):
        source = field_sources.get(field)
        value = (
            archive.get(field, _ABSENT)
            if source == "archive"
            else current.get(field, _ABSENT)
            if source == "current"
            else archive.get(field, _ABSENT)
        )
        if value is not _ABSENT:
            resolved[field] = value
    _validate_resolution_event(category, resolved)


def _validate_dependency_resolution(
    entry: dict[str, object],
    issue: dict[str, object],
    dependencies: dict[str, dict[str, object]],
) -> None:
    identifier = entry["id"]
    if entry["field_sources"] != {}:
        raise ValueError(
            f"resolution {identifier} dependency field_sources must be empty"
        )
    dependency = issue["evidence"]
    blocks = dependency["normalized_blocks"]
    decision = entry["decision"]
    if decision == "use_archive":
        if blocks["legacy"] is None:
            raise ValueError(
                f"resolution {identifier} cannot use absent archive dependency"
            )
        return
    if decision == "use_current":
        if blocks["current"] is None:
            raise ValueError(
                f"resolution {identifier} cannot use absent current dependency"
            )
        return
    if decision == "current_equivalent":
        if blocks["legacy"] is None:
            raise ValueError(
                f"resolution {identifier} has no archive dependency behavior"
            )
        current_label = entry["current_label"]
        if current_label == dependency["label"]:
            raise ValueError(
                f"resolution {identifier} renamed target must differ from source label"
            )
        target = dependencies.get(current_label)
        if target is None:
            raise ValueError(
                f"resolution {identifier} current dependency target does not exist: "
                f"{current_label}"
            )
        if target["classification"] in {
            "archive-changed/current-base", "both-changed", "archived-only",
        }:
            raise ValueError(
                f"resolution {identifier} target {current_label} has unresolved "
                f"classification {target['classification']}"
            )
        current_block = target["normalized_blocks"]["current"]
        current_owner = target["owners"]["current"]
        if current_block is None or current_owner is None:
            raise ValueError(
                f"resolution {identifier} target {current_label} lacks current behavior"
            )
        actual_hash = sha256(current_block.encode("utf-8"))
        if actual_hash != target["normalized_block_sha256"]["current"]:
            raise ValueError(
                f"resolution {identifier} target {current_label} inventory hash mismatch"
            )
        if entry["current_sha256"] != actual_hash:
            raise ValueError(
                f"resolution {identifier} target {current_label} hash differs: "
                f"got={entry['current_sha256']}, expected={actual_hash}"
            )
        source_owner = dependency["owners"]["legacy"]
        source_maps = {
            reference["map"] for reference in dependency["references"]
            if reference["source"] == "legacy"
        }
        target_maps = {
            reference["map"] for reference in target["references"]
            if reference["source"] == "current"
        }
        compatible_owner = (
            source_owner == current_owner or bool(source_maps & target_maps)
        )
        owner_evidence = entry.get("owner_evidence")
        if owner_evidence is not None and (
            not isinstance(owner_evidence, str) or not owner_evidence.strip()
        ):
            raise ValueError(
                f"resolution {identifier} owner_evidence must be a nonempty string"
            )
        if not compatible_owner and owner_evidence is None:
            raise ValueError(
                f"resolution {identifier} target {current_label} has incompatible "
                "map/owner context without owner_evidence"
            )
        return
    raise ValueError(
        f"resolution {identifier} decision {decision} is invalid for dependency issue"
    )


def validate_resolution_entries(
    entries: list[dict[str, object]],
    known: dict[str, dict[str, object]],
    ambiguity_groups: dict[str, dict[str, object]] | None = None,
    dependencies: dict[str, dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    if not isinstance(entries, list) or any(not isinstance(entry, dict) for entry in entries):
        raise ValueError("resolution manifest resolutions must be a list of objects")
    ambiguity_groups = ambiguity_groups or {}
    dependencies = dependencies or {}
    ids = [entry.get("id") for entry in entries]
    if any(not isinstance(identifier, str) for identifier in ids):
        raise ValueError("resolution IDs must be strings")
    duplicates = sorted(identifier for identifier, count in Counter(ids).items() if count > 1)
    if duplicates:
        raise ValueError(f"duplicate resolution IDs: {duplicates}")
    unknown = sorted(set(ids) - known.keys())
    if unknown:
        raise ValueError(f"unknown/unused resolution IDs: {unknown}")
    allowed_decisions = {
        "use_archive", "use_current", "merge_fields", "delete", "keep_both",
        "current_equivalent", "deduplicate",
    }
    required = {
        "id", "map", "category", "base_index", "archive_index", "current_index",
        "decision", "field_sources", "evidence",
    }
    by_id = {entry["id"]: entry for entry in entries}
    for entry in entries:
        identifier = entry["id"]
        issue = known[identifier]
        allowed_keys = set(required)
        if (
            issue.get("issue_type") == "dependency"
            and entry.get("decision") == "current_equivalent"
        ):
            allowed_keys.update({"current_label", "current_sha256"})
            if "owner_evidence" in entry:
                allowed_keys.add("owner_evidence")
        if set(entry) != allowed_keys:
            raise ValueError(
                f"resolution {identifier} keys differ: got={sorted(entry)}, "
                f"expected={sorted(allowed_keys)}"
            )
        if entry["decision"] not in allowed_decisions:
            raise ValueError(f"resolution {identifier} has unsupported decision {entry['decision']!r}")
        if not isinstance(entry["field_sources"], dict):
            raise ValueError(f"resolution {identifier} field_sources must be an object")
        for index_field in ("base_index", "archive_index", "current_index"):
            index = entry[index_field]
            if index is not None and (not isinstance(index, int) or isinstance(index, bool)):
                raise ValueError(
                    f"resolution {identifier} {index_field} must be an integer or null"
                )
        for field in ("map", "category"):
            if entry[field] != issue.get(field):
                raise ValueError(
                    f"resolution {identifier} {field}={entry[field]!r} does not match audit {issue.get(field)!r}"
                )
        if issue.get("issue_type") == "ambiguity_slot":
            if entry["base_index"] != issue["base_index"]:
                raise ValueError(
                    f"resolution {identifier} base_index does not match fixed slot"
                )
            for side in ("archive", "current"):
                index = entry[f"{side}_index"]
                allowed = issue[f"allowed_{side}_indices"]
                if index is not None and index not in allowed:
                    raise ValueError(
                        f"resolution {identifier} {side}_index {index} is outside candidate set {allowed}"
                    )
        else:
            for field in ("base_index", "archive_index", "current_index"):
                if entry[field] != issue.get(field):
                    raise ValueError(
                        f"resolution {identifier} {field}={entry[field]!r} does not match audit {issue.get(field)!r}"
                    )
        if not isinstance(entry["evidence"], str) or not entry["evidence"].strip():
            raise ValueError(f"resolution {identifier} evidence must be a nonempty string")
        if issue.get("issue_type") == "dependency":
            _validate_dependency_resolution(entry, issue, dependencies)
            continue
        if issue.get("issue_type") == "ambiguity_slot":
            group = ambiguity_groups.get(issue["group_id"])
            if group is None:
                raise ValueError(
                    f"resolution {identifier} references unknown ambiguity group {issue['group_id']}"
                )
            base = _group_event(group, "base", entry["base_index"])
            archive = _group_event(group, "archive", entry["archive_index"])
            current = _group_event(group, "current", entry["current_index"])
        else:
            evidence = issue["evidence"]
            base, archive, current = (
                evidence["base"], evidence["archive"], evidence["current"]
            )
        _validate_event_resolution(
            entry, issue["category"], base, archive, current
        )

    for group_id, group in ambiguity_groups.items():
        supplied = [identifier for identifier in group["slot_ids"] if identifier in by_id]
        if not supplied:
            continue
        if set(supplied) != set(group["slot_ids"]):
            missing = sorted(set(group["slot_ids"]) - set(supplied))
            raise ValueError(
                f"ambiguity group {group_id} has incomplete resolutions: missing={missing}"
            )
        for side in ("archive", "current"):
            selected = [
                by_id[identifier][f"{side}_index"]
                for identifier in group["slot_ids"]
                if by_id[identifier][f"{side}_index"] is not None
            ]
            duplicates = sorted(
                index for index, count in Counter(selected).items() if count > 1
            )
            if duplicates:
                raise ValueError(
                    f"ambiguity group {group_id} selects duplicate {side} indices {duplicates}"
                )
            expected = list(group[f"{side}_indices"])
            if sorted(selected) != sorted(expected):
                raise ValueError(
                    f"ambiguity group {group_id} does not consume every {side} record: "
                    f"selected={sorted(selected)}, expected={sorted(expected)}"
                )
    return sorted(entries, key=lambda entry: entry["id"])


def _validate_resolutions(
    path: Path,
    known: dict[str, dict[str, object]],
    ambiguity_groups: dict[str, dict[str, object]] | None = None,
    dependencies: dict[str, dict[str, object]] | None = None,
) -> dict[str, object]:
    expected_empty = {"source_commits": SOURCE_COMMITS, "resolutions": []}
    if not path.exists():
        return expected_empty
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid resolutions JSON at {path}: {error}") from error
    value = _object(value, f"resolutions {path}")
    if set(value) != {"source_commits", "resolutions"} or value["source_commits"] != SOURCE_COMMITS:
        raise ValueError(f"resolution manifest schema/source commits differ at {path}")
    input_order_bytes = _resolution_bytes(
        {"source_commits": SOURCE_COMMITS, "resolutions": value["resolutions"]}
    )
    if raw != input_order_bytes:
        raise ValueError(
            f"existing resolution file is not deterministically formatted: {path}"
        )
    entries = validate_resolution_entries(
        value["resolutions"], known, ambiguity_groups, dependencies
    )
    return {"source_commits": SOURCE_COMMITS, "resolutions": entries}


def _validate_paths(root: Path, args: argparse.Namespace) -> tuple[Path, Path, Path, Path]:
    candidate, audit, resolutions, report = (
        args.candidate_dir.resolve(), args.audit.resolve(), args.resolutions.resolve(), args.report.resolve()
    )
    named = {"candidate": candidate, "audit": audit, "resolutions": resolutions, "report": report}
    if len(set(named.values())) != 4:
        raise ValueError(f"output path collision: {named}")
    for left_name, left in named.items():
        for right_name, right in named.items():
            if left_name >= right_name:
                continue
            if left in right.parents or right in left.parents:
                raise ValueError(f"output path collision/containment: {left_name}={left}, {right_name}={right}")
    canonical = {
        "audit": (root / AUDIT_INVENTORY).resolve(),
        "resolutions": (root / RESOLUTION_INVENTORY).resolve(),
        "report": (root / REPORT_INVENTORY).resolve(),
    }
    build_root = (root / "build").resolve()
    temporary_root = Path(tempfile.gettempdir()).resolve()
    protected_files = {(root / LAYOUT_REPORT).resolve(), Path(__file__).resolve()}
    protected_dirs = [
        (root / directory).resolve()
        for directory in ("data", "src", "include", "tools")
    ]
    for name, path in named.items():
        inside_repository = path == root or root in path.parents
        if path == root or path in protected_files or any(
            path == directory or directory in path.parents for directory in protected_dirs
        ):
            raise ValueError(f"{name} path collides with protected input/source: {path}")
        if inside_repository:
            if name == "candidate":
                if path == build_root or build_root not in path.parents:
                    raise ValueError(
                        f"candidate path inside repository must be below {build_root}: {path}"
                    )
            elif path != canonical[name]:
                raise ValueError(
                    f"{name} path inside repository must be canonical {canonical[name]}: {path}"
                )
        elif path == temporary_root or temporary_root not in path.parents:
            raise ValueError(
                f"external {name} path must be below temporary root {temporary_root}: {path}"
            )
        if name == "candidate" and path.exists() and not path.is_dir():
            raise ValueError(f"candidate path is not a directory: {path}")
        if name != "candidate" and path.exists() and path.is_dir():
            raise ValueError(f"{name} path is a directory: {path}")
    return candidate, audit, resolutions, report


def _stage_file(path: Path, data: bytes, purpose: str) -> Path:
    if not path.parent.is_dir():
        raise ValueError(f"{purpose} parent is not an existing directory: {path.parent}")
    handle, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if temporary.read_bytes() != data:
            raise RuntimeError(f"{purpose} staging verification failed for {path}")
        return temporary
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _destination_preimage(path: Path) -> bytes | None:
    if not os.path.lexists(path):
        return None
    if not path.is_file():
        raise ValueError(f"evidence destination is not a regular file: {path}")
    if not os.access(path, os.W_OK):
        raise ValueError(f"evidence destination is not writable: {path}")
    return path.read_bytes()


def publish_evidence_pair(
    audit_path: Path,
    audit_data: bytes,
    resolutions_path: Path,
    resolution_data: bytes,
    *,
    fault: Callable[[str, int, Path], None] | None = None,
    replace: Callable[[Path, Path], None] = os.replace,
) -> None:
    """Publish audit/resolution evidence as one recoverable paired transaction."""

    destinations = [
        (resolutions_path, resolution_data),
        (audit_path, audit_data),
    ]
    if audit_path == resolutions_path:
        raise ValueError("paired evidence destinations collide")
    preimages: dict[Path, bytes | None] = {}
    for path, _data in destinations:
        if not path.parent.is_dir():
            raise ValueError(f"evidence parent is not an existing directory: {path.parent}")
        preimages[path] = _destination_preimage(path)

    forwards: dict[Path, Path] = {}
    rollbacks: dict[Path, Path] = {}
    cleanup: set[Path] = set()
    preserved: set[Path] = set()
    changed = [
        (path, data) for path, data in destinations if preimages[path] != data
    ]
    replaced: list[Path] = []
    try:
        # Stage and verify every desired output before the first replacement.
        for path, data in destinations:
            forward = _stage_file(path, data, "forward evidence")
            forwards[path] = forward
            cleanup.add(forward)
        for path, _data in changed:
            preimage = preimages[path]
            if preimage is not None:
                rollback = _stage_file(path, preimage, "rollback evidence")
                rollbacks[path] = rollback
                cleanup.add(rollback)

        for path, _data in destinations:
            if _destination_preimage(path) != preimages[path]:
                raise RuntimeError(f"evidence destination changed while staging: {path}")

        for index, (path, _data) in enumerate(changed):
            if _destination_preimage(path) != preimages[path]:
                raise RuntimeError(f"evidence destination changed before replacement: {path}")
            if fault is not None:
                fault("before", index, path)
            replace(forwards[path], path)
            cleanup.discard(forwards[path])
            replaced.append(path)
            if fault is not None:
                fault("after", index, path)

        for path, data in destinations:
            if _destination_preimage(path) != data:
                raise RuntimeError(f"published evidence verification failed: {path}")
    except BaseException as publication_error:
        rollback_errors: list[str] = []
        for path in reversed(replaced):
            preimage = preimages[path]
            try:
                if preimage is None:
                    path.unlink(missing_ok=True)
                else:
                    rollback = rollbacks[path]
                    replace(rollback, path)
                    cleanup.discard(rollback)
                if _destination_preimage(path) != preimage:
                    raise RuntimeError("restored bytes do not match captured preimage")
            except BaseException as rollback_error:
                detail = f"{path}: {rollback_error}"
                rollback = rollbacks.get(path)
                if rollback is not None and rollback.exists():
                    preserved.add(rollback)
                    detail += f"; exact recovery data retained at {rollback}"
                elif preimage is None:
                    detail += "; destination should be absent and contains no recoverable preimage"
                rollback_errors.append(detail)
        if rollback_errors:
            raise RuntimeError(
                "paired evidence publication failed and rollback failed: "
                + "; ".join(rollback_errors)
            ) from publication_error
        raise RuntimeError(
            "paired evidence publication failed; prior audit/resolution state restored: "
            f"{publication_error}"
        ) from publication_error
    finally:
        for temporary in cleanup - preserved:
            temporary.unlink(missing_ok=True)


def _canonical_candidate_map_bytes(data: bytes, context: str) -> None:
    try:
        document = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{context} is not valid candidate map JSON: {error}") from error
    if not isinstance(document, dict):
        raise ValueError(f"{context} candidate map must be an object")
    required = {"layout", *EVENT_CATEGORIES}
    if not required.issubset(document):
        raise ValueError(
            f"{context} candidate map lacks canonical fields: {sorted(required - document.keys())}"
        )
    if not isinstance(document["layout"], str) or any(
        not isinstance(document[category], list) for category in EVENT_CATEGORIES
    ):
        raise ValueError(f"{context} candidate map has invalid canonical field types")


def _validate_candidate_file_set(files: dict[str, bytes]) -> None:
    if not isinstance(files, dict):
        raise TypeError("candidate files must be a path-to-bytes object")
    for relative, data in files.items():
        parts = PurePosixPath(relative).parts if isinstance(relative, str) else ()
        if (
            len(parts) != 4
            or parts[:2] != ("data", "maps")
            or parts[3] != "map.json"
            or not re.fullmatch(r"[A-Za-z0-9_]+", parts[2])
        ):
            raise ValueError(f"invalid managed candidate path: {relative!r}")
        if not isinstance(data, bytes):
            raise TypeError(f"candidate data must be bytes: {relative}")
        _canonical_candidate_map_bytes(data, f"candidate {relative}")


def _validate_candidate_report_bytes(report_data: bytes, files: dict[str, bytes]) -> None:
    try:
        report = json.loads(report_data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"candidate report is not valid JSON: {error}") from error
    if not isinstance(report, dict) or report.get("mode") != "candidate-only":
        raise ValueError("candidate report must be a candidate-only JSON object")
    expected_hashes = {
        relative: sha256(data) for relative, data in sorted(files.items())
    }
    expected_maps = sorted(PurePosixPath(relative).parts[2] for relative in files)
    if (
        report.get("candidate_sha256") != expected_hashes
        or report.get("candidate_map_count") != len(files)
        or report.get("candidate_maps") != expected_maps
    ):
        raise ValueError("candidate report does not describe the exact candidate tree")


def _validate_existing_candidate_tree(candidate_dir: Path) -> None:
    if not candidate_dir.exists():
        return
    if not candidate_dir.is_dir() or candidate_dir.is_symlink():
        raise ValueError(f"candidate path is not a managed directory: {candidate_dir}")
    files = [path for path in candidate_dir.rglob("*") if path.is_file()]
    relative_files = {path.relative_to(candidate_dir).as_posix() for path in files}
    expected_dirs = {Path("data"), Path("data/maps")}
    for relative in relative_files:
        parts = PurePosixPath(relative).parts
        if (
            len(parts) != 4
            or parts[:2] != ("data", "maps")
            or parts[3] != "map.json"
            or not re.fullmatch(r"[A-Za-z0-9_]+", parts[2])
        ):
            raise ValueError(f"unexpected managed candidate content: {candidate_dir / relative}")
        expected_dirs.add(Path("data/maps") / parts[2])
    actual_dirs = {
        path.relative_to(candidate_dir)
        for path in candidate_dir.rglob("*")
        if path.is_dir() and not path.is_symlink()
    }
    unexpected = sorted(
        str(path.relative_to(candidate_dir))
        for path in candidate_dir.rglob("*")
        if path.is_symlink()
        or (path.is_dir() and path.relative_to(candidate_dir) not in expected_dirs)
    )
    unexpected.extend(str(path) for path in sorted(actual_dirs - expected_dirs))
    if unexpected:
        raise ValueError(f"unexpected managed candidate content: {unexpected}")
    for path in files:
        _canonical_candidate_map_bytes(
            path.read_bytes(), f"existing candidate {path.relative_to(candidate_dir).as_posix()}"
        )


def _fsync_directory(path: Path) -> None:
    try:
        descriptor = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)


def _reserved_absent_path(parent: Path, prefix: str, directory: bool) -> Path:
    if directory:
        path = Path(tempfile.mkdtemp(prefix=prefix, dir=parent))
        path.rmdir()
        return path
    descriptor, name = tempfile.mkstemp(prefix=prefix, dir=parent)
    os.close(descriptor)
    path = Path(name)
    path.unlink()
    return path


def _remove_temporary(path: Path) -> None:
    if not os.path.lexists(path):
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def _path_snapshot(path: Path) -> tuple[object, ...]:
    """Capture exact path existence, type, and recursive contents."""

    if not os.path.lexists(path):
        return ("absent",)
    if path.is_symlink():
        return ("symlink", os.readlink(path))
    if path.is_file():
        return ("file", path.read_bytes())
    if path.is_dir():
        return (
            "directory",
            tuple(
                (entry.name, _path_snapshot(path / entry.name))
                for entry in sorted(os.scandir(path), key=lambda entry: entry.name)
            ),
        )
    return ("other", path.lstat().st_mode)


def publish_candidate_bundle(
    candidate_dir: Path,
    candidate_files: dict[str, bytes],
    report_path: Path,
    report_data: bytes,
    *,
    fault: Callable[[str, Path], None] | None = None,
    move: Callable[[Path, Path], None] = os.rename,
) -> None:
    """Atomically publish a complete managed candidate tree and its report."""

    candidate_dir = candidate_dir.resolve()
    report_path = report_path.resolve()
    if candidate_dir == report_path or candidate_dir in report_path.parents or report_path in candidate_dir.parents:
        raise ValueError("candidate/report publication paths collide")
    if not isinstance(report_data, bytes):
        raise TypeError("report data must be bytes")
    _validate_candidate_file_set(candidate_files)
    _validate_candidate_report_bytes(report_data, candidate_files)
    candidate_preimage = _path_snapshot(candidate_dir)
    _validate_existing_candidate_tree(candidate_dir)
    if not candidate_dir.parent.is_dir() or not report_path.parent.is_dir():
        raise ValueError("candidate and report parents must already exist")
    report_preimage = _path_snapshot(report_path)
    _destination_preimage(report_path)
    if _path_snapshot(candidate_dir) != candidate_preimage:
        raise RuntimeError(f"candidate destination changed before staging: {candidate_dir}")
    if _path_snapshot(report_path) != report_preimage:
        raise RuntimeError(f"report destination changed before staging: {report_path}")

    staged_candidate = Path(
        tempfile.mkdtemp(prefix=f".{candidate_dir.name}.stage.", dir=candidate_dir.parent)
    )
    candidate_backup = _reserved_absent_path(
        candidate_dir.parent, f".{candidate_dir.name}.backup.", True
    )
    report_backup = _reserved_absent_path(
        report_path.parent, f".{report_path.name}.backup.", False
    )
    staged_report: Path | None = None
    candidate_backed_up = False
    candidate_installed = False
    report_backed_up = False
    report_installed = False
    temporaries = {staged_candidate, candidate_backup, report_backup}
    try:
        for relative, data in sorted(candidate_files.items()):
            destination = staged_candidate / Path(*PurePosixPath(relative).parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        for directory in sorted(
            (path for path in staged_candidate.rglob("*") if path.is_dir()),
            key=lambda path: len(path.parts),
            reverse=True,
        ):
            _fsync_directory(directory)
        _fsync_directory(staged_candidate)
        staged_report = _stage_file(report_path, report_data, "candidate report")
        temporaries.add(staged_report)
        if fault is not None:
            fault("after_staging", staged_candidate)

        if os.path.lexists(candidate_dir):
            move(candidate_dir, candidate_backup)
            candidate_backed_up = True
            candidate_current = _path_snapshot(candidate_backup)
        else:
            candidate_current = ("absent",)
        if candidate_current != candidate_preimage:
            raise RuntimeError(
                f"candidate destination changed while staging: {candidate_dir}"
            )
        if fault is not None:
            fault("before_candidate_install", candidate_dir)
        move(staged_candidate, candidate_dir)
        candidate_installed = True
        if fault is not None:
            fault("after_candidate_install", candidate_dir)

        if os.path.lexists(report_path):
            move(report_path, report_backup)
            report_backed_up = True
            report_current = _path_snapshot(report_backup)
        else:
            report_current = ("absent",)
        if report_current != report_preimage:
            raise RuntimeError(f"report destination changed while staging: {report_path}")
        if fault is not None:
            fault("before_report_install", report_path)
        os.link(staged_report, report_path)
        report_installed = True
        staged_report.unlink()
        if fault is not None:
            fault("after_report_install", report_path)
        if report_path.read_bytes() != report_data:
            raise RuntimeError("published candidate report verification failed")
        _validate_existing_candidate_tree(candidate_dir)
        published = {
            path.relative_to(candidate_dir).as_posix(): path.read_bytes()
            for path in candidate_dir.rglob("map.json")
        }
        if published != candidate_files:
            raise RuntimeError("published candidate tree verification failed")
    except BaseException as publication_error:
        rollback_errors: list[str] = []
        if report_installed and staged_report is not None:
            try:
                move(report_path, staged_report)
                report_installed = False
            except BaseException as rollback_error:
                rollback_errors.append(f"remove published report: {rollback_error}")
        if report_backed_up:
            try:
                if os.path.lexists(report_path):
                    raise RuntimeError(
                        "report destination is occupied; cannot restore prior report "
                        "without overwriting it"
                    )
                move(report_backup, report_path)
                report_backed_up = False
            except BaseException as rollback_error:
                rollback_errors.append(f"restore prior report: {rollback_error}")
        if candidate_installed:
            try:
                move(candidate_dir, staged_candidate)
                candidate_installed = False
            except BaseException as rollback_error:
                rollback_errors.append(f"remove published candidate tree: {rollback_error}")
        if candidate_backed_up:
            try:
                if os.path.lexists(candidate_dir):
                    raise RuntimeError("published candidate tree still occupies destination")
                move(candidate_backup, candidate_dir)
                candidate_backed_up = False
            except BaseException as rollback_error:
                rollback_errors.append(f"restore prior candidate tree: {rollback_error}")
        if rollback_errors:
            recovery_copies = {
                path
                for path, needed in (
                    (candidate_backup, candidate_backed_up),
                    (report_backup, report_backed_up),
                )
                if needed and os.path.lexists(path)
            }
            for temporary in temporaries - recovery_copies:
                try:
                    _remove_temporary(temporary)
                except BaseException as cleanup_error:
                    rollback_errors.append(
                        f"clean transaction temporary {temporary}: {cleanup_error}"
                    )
                    recovery_copies.add(temporary)
            retained = sorted(str(path) for path in recovery_copies)
            raise RuntimeError(
                "candidate/report publication failed and rollback failed; "
                "recovery copies retained: "
                + ", ".join(retained)
                + f"; rollback errors: {rollback_errors}"
            ) from publication_error
        for temporary in temporaries:
            _remove_temporary(temporary)
        raise
    else:
        for temporary in temporaries:
            _remove_temporary(temporary)
        _fsync_directory(candidate_dir.parent)
        if report_path.parent != candidate_dir.parent:
            _fsync_directory(report_path.parent)


def build_audit(root: Path, commits: dict[str, str], layout_report_data: bytes) -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    try:
        layout_report = json.loads(layout_report_data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid JSON object at {LAYOUT_REPORT}: {error}") from error
    layout_report = _object(layout_report, str(LAYOUT_REPORT))
    sources = Sources(commits)
    baseline_layouts = sources.json("current", "data/layouts/layouts.json")
    baseline_maps: dict[str, dict[str, object]] = {}
    for path in _map_paths(commits["current"]):
        parts = PurePosixPath(path).parts
        if len(parts) == 4 and parts[:2] == ("data", "maps") and parts[-1] == "map.json":
            baseline_maps[parts[2]] = sources.json("current", path)
    layout_ids, map_names = derive_scope(layout_report, baseline_layouts, baseline_maps)
    if len(layout_ids) != EXPECTED_SHARED_LAYOUTS or len(map_names) != EXPECTED_SCOPED_MAPS:
        raise ValueError(
            f"scope count mismatch: layouts={len(layout_ids)} expected={EXPECTED_SHARED_LAYOUTS}, maps={len(map_names)} expected={EXPECTED_SCOPED_MAPS}"
        )
    overlap = sorted(set(map_names) & set(CUSTOM_MAPS))
    if overlap:
        raise ValueError(f"custom maps leaked into shared overwrite scope: {overlap}")

    documents: dict[str, dict[str, dict[str, list[dict[str, object]]]]] = {}
    map_audits: list[dict[str, object]] = []
    event_unresolved: list[dict[str, object]] = []
    ambiguity_groups: list[dict[str, object]] = []
    category_counts = {
        category: {
            "base": 0, "archive": 0, "current": 0, "alignments": 0,
            "exact_three_way": 0, "automatic": 0, "unresolved": 0,
            "unresolved_alignments": 0, "dispositions": {},
        }
        for category in EVENT_CATEGORIES
    }
    archive_changed_maps: list[str] = []
    for map_name in map_names:
        path = f"data/maps/{map_name}/map.json"
        per_source = {
            source: _event_arrays(sources.json(source, path), f"{source}:{path}")
            for source in SOURCE_COMMITS
        }
        documents[map_name] = per_source
        changed = any(per_source["base"][category] != per_source["legacy"][category] for category in EVENT_CATEGORIES)
        if changed:
            archive_changed_maps.append(map_name)
        categories: dict[str, object] = {}
        for category in EVENT_CATEGORIES:
            arrays = [per_source[source][category] for source in SOURCE_COMMITS]
            records, issues, groups = _audit_category(map_name, category, *arrays)
            categories[category] = {
                "counts": dict(zip(("base", "archive", "current"), map(len, arrays))),
                "alignments": records,
            }
            counts = category_counts[category]
            for count_name, events in zip(("base", "archive", "current"), arrays):
                counts[count_name] += len(events)
            counts["alignments"] += len(records)
            counts["unresolved"] += len(issues)
            counts["automatic"] += sum(
                record["disposition"] != "unresolved" for record in records
            )
            counts["unresolved_alignments"] += sum(
                record["disposition"] == "unresolved" for record in records
            )
            counts["exact_three_way"] += sum(record["method"] == "exact/exact" for record in records)
            disposition_counter = Counter(counts["dispositions"])
            disposition_counter.update(record["disposition"] for record in records)
            counts["dispositions"] = dict(sorted(disposition_counter.items()))
            event_unresolved.extend(issues)
            ambiguity_groups.extend(groups)
        map_audits.append({"map": map_name, "archive_changed": changed, "categories": categories})
    if tuple(archive_changed_maps) != EXPECTED_ARCHIVE_CHANGED_MAP_NAMES:
        raise ValueError(
            "archive changed-map set/order mismatch: "
            f"got={archive_changed_maps}, expected={list(EXPECTED_ARCHIVE_CHANGED_MAP_NAMES)}"
        )
    if len(archive_changed_maps) != EXPECTED_ARCHIVE_CHANGED_MAPS:
        raise ValueError(f"archive changed-map count mismatch: {len(archive_changed_maps)}")

    custom_records = []
    for map_name in CUSTOM_MAPS:
        path = f"data/maps/{map_name}/map.json"
        per_source = {
            source: _event_arrays(sources.json(source, path), f"{source}:{path}")
            for source in ("legacy", "current")
        }
        custom_records.append(
            {
                "map": map_name,
                "excluded_from_overwrite_scope": True,
                "layout": {source: sources.json(source, path).get("layout") for source in ("legacy", "current")},
                "event_arrays_equal": {
                    category: per_source["legacy"][category] == per_source["current"][category]
                    for category in EVENT_CATEGORIES
                },
                "blob_sha256": {source: sources.hashes[source][path] for source in ("legacy", "current")},
            }
        )

    labels, references = _referenced_scripts(documents, map_audits)
    dependencies, dependency_unresolved = _dependency_inventory(sources, labels, references, documents)
    all_unresolved = sorted([*event_unresolved, *dependency_unresolved], key=lambda item: item["id"])
    known = {item["id"]: item for item in all_unresolved}
    if len(known) != len(all_unresolved):
        raise ValueError("duplicate unresolved IDs")
    alignment_record_count = sum(
        counts["alignments"] for counts in category_counts.values()
    )
    if alignment_record_count != EXPECTED_ALIGNMENT_RECORDS:
        raise ValueError(
            f"alignment record count mismatch: {alignment_record_count}"
        )
    audit = {
        "schema_version": 1,
        "mode": "audit-only",
        "source_commits": {
            source: {"ref": SOURCE_COMMITS[source], "resolved_oid": commits[source]}
            for source in SOURCE_COMMITS
        },
        "source_blobs": {
            "layout_report": {"path": str(LAYOUT_REPORT).replace("\\", "/"), "sha256": sha256(layout_report_data)},
            "git": sources.hashes,
        },
        "scope": {
            "shared_layout_count": len(layout_ids),
            "shared_layout_ids": sorted(layout_ids),
            "scoped_map_count": len(map_names),
            "scoped_maps": map_names,
            "archive_changed_map_count": len(archive_changed_maps),
            "archive_changed_maps": archive_changed_maps,
            "custom_maps": custom_records,
        },
        "category_counts": category_counts,
        "alignment_record_count": alignment_record_count,
        "maps": map_audits,
        "ambiguity_group_count": len(ambiguity_groups),
        "ambiguity_resolution_slot_count": sum(
            len(group["slot_ids"]) for group in ambiguity_groups
        ),
        "ambiguity_groups": sorted(ambiguity_groups, key=lambda item: item["id"]),
        "dependency_counts": dict(sorted(Counter(item["classification"] for item in dependencies).items())),
        "dependencies": dependencies,
        "unresolved_count": len(all_unresolved),
        "unresolved": all_unresolved,
    }
    return audit, known


def _reviewed_event_units(
    category: str,
    category_audit: dict[str, object],
    arrays: dict[str, list[dict[str, object]]],
    resolutions: dict[str, dict[str, object]],
    ambiguity_groups: dict[str, dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Construct reviewed units while retaining current order as the backbone."""

    units: list[dict[str, object]] = []
    records: list[dict[str, object]] = []
    for alignment in category_audit["alignments"]:
        if alignment["method"] == "ambiguous":
            group = ambiguity_groups[alignment["id"]]
            selections = [resolutions[identifier] for identifier in group["slot_ids"]]
        else:
            selections = [resolutions[alignment["id"]]] if alignment["disposition"] == "unresolved" else [None]
        for selection in selections:
            if selection is None:
                base_index = alignment["base_index"]
                archive_index = alignment["archive_index"]
                current_index = alignment["current_index"]
                base = arrays["base"][base_index] if base_index is not None else None
                archive = arrays["legacy"][archive_index] if archive_index is not None else None
                current = arrays["current"][current_index] if current_index is not None else None
                result = (
                    merge_base_event(category, base, archive, current)
                    if base is not None
                    else merge_added_event(category, archive, current)
                )
                if result.conflict is not None:
                    raise UnresolvedConflictError([alignment["id"]])
                events = [] if result.event is None else [result.event]
                disposition = result.disposition
                identifier = alignment["id"]
            else:
                identifier = selection["id"]
                archive_index = selection["archive_index"]
                current_index = selection["current_index"]
                archive = arrays["legacy"][archive_index] if archive_index is not None else None
                current = arrays["current"][current_index] if current_index is not None else None
                events = resolve_reviewed_event(category, archive, current, selection)
                disposition = f"reviewed_{selection['decision']}"
            units.append(
                {
                    "id": identifier,
                    "archive_index": archive_index,
                    "current_index": current_index,
                    "events": copy.deepcopy(events),
                    "disposition": disposition,
                }
            )

    current_backbone = sorted(
        (unit for unit in units if unit["current_index"] is not None),
        key=lambda unit: unit["current_index"],
    )
    ordered = list(current_backbone)
    for unit in sorted(
        (unit for unit in units if unit["archive_index"] is not None and unit["current_index"] is None),
        key=lambda unit: unit["archive_index"],
    ):
        prior = [
            index for index, existing in enumerate(ordered)
            if existing["archive_index"] is not None
            and existing["archive_index"] < unit["archive_index"]
        ]
        if prior:
            insertion = max(prior) + 1
        else:
            later = [
                index for index, existing in enumerate(ordered)
                if existing["archive_index"] is not None
                and existing["archive_index"] > unit["archive_index"]
            ]
            insertion = min(later) if later else len(ordered)
        ordered.insert(insertion, unit)
    ordered.extend(unit for unit in units if unit not in ordered)
    output: list[dict[str, object]] = []
    for unit in ordered:
        output.extend(copy.deepcopy(unit["events"]))
        records.append(
            {
                "id": unit["id"],
                "disposition": unit["disposition"],
                "output_count": len(unit["events"]),
            }
        )
    return output, records


def _adapt_reviewed_item_events(
    events: list[dict[str, object]],
    dependency_by_label: dict[str, dict[str, object]],
    dependency_resolutions: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for event in events:
        label = event.get("script")
        dependency = dependency_by_label.get(label) if isinstance(label, str) else None
        resolution = dependency_resolutions.get(f"dependency:{label}")
        legacy_block = dependency["normalized_blocks"]["legacy"] if dependency else None
        if (
            resolution is not None
            and resolution["decision"] == "use_archive"
            and isinstance(legacy_block, str)
            and re.search(r"(?m)^\s*finditem\b", legacy_block)
        ):
            output.append(adapt_item_ball(event, legacy_block))
        else:
            output.append(copy.deepcopy(event))
    return output


def dependency_report_record(
    resolution: dict[str, object],
    dependency: dict[str, object],
    dependencies: dict[str, dict[str, object]],
) -> dict[str, object]:
    """Project one validated dependency decision into deterministic evidence."""

    identifier = resolution["id"]
    label = dependency["label"]
    decision = resolution["decision"]
    is_item_adapter = any(
        item.get("archive_label") == label
        for item in dependency["item_equivalence"]
    )
    if decision == "current_equivalent":
        current_label = resolution["current_label"]
        target = dependencies[current_label]
        current_owner = target["owners"]["current"]
        current_sha256 = target["normalized_block_sha256"]["current"]
        return {
            "id": identifier,
            "label": label,
            "source_label": label,
            "decision": decision,
            "disposition": "current_equivalent",
            "source_owner": dependency["owners"]["legacy"],
            "source_sha256": dependency["normalized_block_sha256"]["legacy"],
            "current_label": current_label,
            "current_owner": current_owner,
            "target_owner": current_owner,
            "current_sha256": current_sha256,
            "target_sha256": current_sha256,
            "block_labels": dependency["block_labels"]["legacy"],
            "authored": False,
            "resolution_evidence": resolution["evidence"],
            "missing_dependencies": [],
        }

    source = "legacy" if decision == "use_archive" else "current"
    target_owner = dependency["owners"].get("current") or dependency["owners"].get("legacy")
    authored = decision == "use_archive" and not is_item_adapter
    return {
        "id": identifier,
        "label": label,
        "source_label": label,
        "decision": decision,
        "disposition": (
            "candidate_item_adapter"
            if is_item_adapter
            else f"selected_{source}"
        ),
        "source_owner": dependency["owners"].get(source),
        "target_owner": target_owner,
        "source_sha256": dependency["normalized_block_sha256"].get(source),
        "target_sha256": dependency["normalized_block_sha256"].get("current"),
        "block_labels": dependency["block_labels"].get(source, []),
        "authored": authored,
        "resolution_evidence": resolution["evidence"],
        "missing_dependencies": [],
    }


def validate_dependency_postimages(
    actual_files: dict[str, bytes],
    baseline_files: dict[str, bytes],
    resolutions: dict[str, dict[str, object]],
    dependencies: dict[str, dict[str, object]],
    specs: dict[str, dict[str, object]],
) -> dict[str, object]:
    """Validate reviewed dependency closures and exact owner postimages."""

    missing: set[str] = set()
    records: list[dict[str, object]] = []
    writes: list[dict[str, object]] = []
    specified_ids: set[str] = set()
    for path, spec in sorted(specs.items()):
        transformations = spec["dependencies"]
        literal_specs = spec["required_literals"]
        path_ids = {
            transformation["id"] for transformation in transformations
        } | {literal["id"] for literal in literal_specs}
        specified_ids.update(transformation["id"] for transformation in transformations)
        baseline = baseline_files.get(path)
        actual = actual_files.get(path)
        if baseline is None or sha256(baseline) != spec["old_sha256"]:
            raise ValueError(f"dependency spec baseline hash differs for {path}")
        if actual is None or sha256(actual) != spec["new_sha256"]:
            missing.update(path_ids)
        parsed: dict[str, str] = {}
        if actual is not None:
            try:
                parsed = parse_label_blocks(actual, f"dependency target {path}")
            except ValueError:
                missing.update(path_ids)
        for transformation in transformations:
            identifier = transformation["id"]
            label = identifier.removeprefix("dependency:")
            dependency = dependencies.get(label)
            resolution = resolutions.get(identifier)
            errors: list[str] = []
            if dependency is None:
                errors.append("missing source dependency inventory")
            if resolution is None or resolution.get("decision") != "use_archive":
                errors.append("missing reviewed use_archive resolution")
            target_label = transformation["target_label"]
            try:
                target_block, target_labels = expand_label_block(target_label, parsed)
            except ValueError as error:
                target_block, target_labels = "", []
                errors.append(str(error))
            actual_target_hash = sha256(target_block.encode("utf-8")) if target_block else None
            if actual_target_hash != transformation["target_sha256"]:
                errors.append("actual target closure hash differs from reviewed postimage")
            source_hash = (
                dependency["normalized_block_sha256"]["legacy"]
                if dependency is not None
                else None
            )
            if transformation["kind"] == "direct_legacy" and actual_target_hash != source_hash:
                errors.append("direct legacy target closure differs from selected source")
            if errors:
                missing.add(identifier)
            records.append(
                {
                    "id": identifier,
                    "label": label,
                    "source_label": label,
                    "source_owner": dependency["owners"]["legacy"] if dependency else None,
                    "source_sha256": source_hash,
                    "decision": "use_archive",
                    "disposition": "selected_legacy",
                    "actual_target_label": target_label,
                    "target_owner": path,
                    "actual_target_sha256": actual_target_hash,
                    "target_sha256": actual_target_hash,
                    "target_block_labels": target_labels,
                    "adaptation_kind": transformation["kind"],
                    "adaptation_rationale": transformation["rationale"],
                    "authored": True,
                    "resolution_evidence": resolution.get("evidence") if resolution else None,
                    "missing_dependencies": errors,
                }
            )
        for literal in literal_specs:
            if actual is None or literal["text"].encode("utf-8") not in actual:
                missing.add(literal["id"])
        writes.append(
            {
                "path": path,
                "labels": sorted(path_ids),
                "source": "exact reviewed dependency postimage",
                "old_sha256": sha256(baseline),
                "new_sha256": sha256(actual) if actual is not None else None,
                "target_sha256": sha256(actual) if actual is not None else None,
            }
        )

    for identifier, resolution in sorted(resolutions.items()):
        if identifier in specified_ids:
            continue
        label = identifier.removeprefix("dependency:")
        dependency = dependencies.get(label)
        if dependency is None:
            missing.add(identifier)
            continue
        is_item_adapter = any(
            item.get("archive_label") == label
            for item in dependency["item_equivalence"]
        )
        decision = resolution["decision"]
        if is_item_adapter and decision == "use_archive":
            record = dependency_report_record(resolution, dependency, dependencies)
            record.update(
                {
                    "actual_target_label": "Common_EventScript_FindItem",
                    "adaptation_kind": "candidate_item_adapter",
                    "adaptation_rationale": (
                        "Legacy finditem operands are stored in the candidate object template."
                    ),
                    "missing_dependencies": [],
                }
            )
            records.append(record)
        elif decision in {"use_current", "current_equivalent"}:
            record = dependency_report_record(resolution, dependency, dependencies)
            record.update(
                {
                    "actual_target_label": record.get("current_label", label),
                    "actual_target_sha256": record.get("current_sha256", record["target_sha256"]),
                    "adaptation_kind": (
                        "renamed_current_equivalent"
                        if decision == "current_equivalent"
                        else "retained_current"
                    ),
                    "adaptation_rationale": resolution["evidence"],
                    "missing_dependencies": [],
                }
            )
            records.append(record)
        else:
            missing.add(identifier)
    return {
        "dependency_records": sorted(records, key=lambda record: record["id"]),
        "dependency_writes": writes,
        "missing_dependencies": sorted(missing),
    }


def candidate_event_bounds_error(
    event: dict[str, object], width: int, height: int
) -> str | None:
    """Return the exact packed-field/coordinate error for one event."""

    x, y = event.get("x"), event.get("y")
    if (
        not isinstance(x, int)
        or isinstance(x, bool)
        or not isinstance(y, int)
        or isinstance(y, bool)
        or x < 0
        or x >= width
        or y < 0
        or y >= height
    ):
        return f"coordinates must be integers inside {width}x{height}, got ({x!r}, {y!r})"
    range_x = event.get("movement_range_x", 0)
    range_y = event.get("movement_range_y", 0)
    if event.get("script") == "Common_EventScript_FindItem":
        if (
            not isinstance(range_x, int)
            or isinstance(range_x, bool)
            or not 0 <= range_x <= 15
        ):
            return (
                "item quantity movement_range_x must be an integer in 0..15, "
                f"got {range_x!r}"
            )
    elif (
        not isinstance(range_x, int)
        or isinstance(range_x, bool)
        or not 0 <= range_x <= 15
    ):
        return f"movement_range_x must be an integer in 0..15, got {range_x!r}"
    if (
        not isinstance(range_y, int)
        or isinstance(range_y, bool)
        or not 0 <= range_y <= 15
    ):
        return f"movement_range_y must be an integer in 0..15, got {range_y!r}"
    return None


def generate_candidates_and_report(
    root: Path,
    audit: dict[str, object],
    documents: dict[str, dict[str, dict[str, list[dict[str, object]]]]],
    resolutions: dict[str, object],
    sources: Sources,
) -> tuple[dict[str, object], dict[str, bytes]]:
    entries = resolutions["resolutions"]
    by_id = {entry["id"]: entry for entry in entries}
    unresolved_ids = set(audit.get("resolution_ids", ())) or {
        item["id"] for item in audit["unresolved"]
    }
    validate_resolution_consumption(unresolved_ids, by_id)
    event_resolutions = {key: value for key, value in by_id.items() if value["category"] != "dependency"}
    dependency_resolutions = {key: value for key, value in by_id.items() if value["category"] == "dependency"}
    groups = {group["id"]: group for group in audit["ambiguity_groups"]}
    dependency_by_label = {item["label"]: item for item in audit["dependencies"]}
    candidate_hashes: dict[str, str] = {}
    map_validations: list[dict[str, object]] = []
    disposition_counts: Counter[str] = Counter()
    item_records: list[dict[str, object]] = []
    candidate_documents: dict[str, dict[str, object]] = {}
    candidate_files: dict[str, bytes] = {}
    authoritative_before = {
        map_audit["map"]: sha256(
            (root / "data" / "maps" / map_audit["map"] / "map.json").read_bytes()
        )
        for map_audit in audit["maps"]
    }
    changed_maps: list[str] = []
    for map_audit in audit["maps"]:
        map_name = map_audit["map"]
        path = f"data/maps/{map_name}/map.json"
        current_document = sources.json("current", path)
        candidate = copy.deepcopy(current_document)
        category_records: dict[str, object] = {}
        for category in EVENT_CATEGORIES:
            merged, records = _reviewed_event_units(
                category,
                map_audit["categories"][category],
                {
                    source: documents[map_name][source][category]
                    for source in SOURCE_COMMITS
                },
                event_resolutions,
                groups,
            )
            if category == "object_events":
                merged = _adapt_reviewed_item_events(
                    merged, dependency_by_label, dependency_resolutions
                )
                for event in merged:
                    if event.get("script") == "Common_EventScript_FindItem" and isinstance(event.get("trainer_sight_or_berry_tree_id"), str) and event["trainer_sight_or_berry_tree_id"].startswith("ITEM_"):
                        item_records.append(
                            {
                                "map": map_name,
                                "flag": event.get("flag"),
                                "item": event["trainer_sight_or_berry_tree_id"],
                                "quantity": event.get("movement_range_x"),
                            }
                        )
            candidate[category] = merged
            category_records[category] = records
            disposition_counts.update(record["disposition"] for record in records)
        if any(candidate[key] != current_document[key] for key in EVENT_CATEGORIES):
            changed_maps.append(map_name)
            relative = f"data/maps/{map_name}/map.json"
            data = _json_bytes(candidate)
            candidate_files[relative] = data
            candidate_hashes[relative] = sha256(data)
        candidate_documents[map_name] = candidate
        map_validations.append(
            {
                "map": map_name,
                "layout_preserved": candidate.get("layout") == current_document.get("layout"),
                "non_event_fields_preserved": all(
                    candidate.get(key) == value
                    for key, value in current_document.items()
                    if key not in EVENT_CATEGORIES
                ),
                "categories": category_records,
            }
        )

    layout_by_id = {
        layout["id"]: layout
        for layout in sources.json("current", "data/layouts/layouts.json")["layouts"]
    }
    duplicate_identities: list[dict[str, object]] = []
    out_of_bounds: list[dict[str, object]] = []
    invalid_item_quantities: list[dict[str, object]] = []
    local_id_duplicates: list[dict[str, object]] = []
    for map_name, document in candidate_documents.items():
        layout = layout_by_id[document["layout"]]
        width, height = layout["width"], layout["height"]
        for category in EVENT_CATEGORIES:
            seen_exact: dict[str, int] = {}
            for index, event in enumerate(document[category]):
                signature = exact_signature(event)
                if signature in seen_exact:
                    duplicate_identities.append(
                        {"map": map_name, "category": category, "indices": [seen_exact[signature], index]}
                    )
                else:
                    seen_exact[signature] = index
                bounds_error = candidate_event_bounds_error(event, width, height)
                if bounds_error is not None:
                    record = {
                        "map": map_name,
                        "category": category,
                        "index": index,
                        "reason": bounds_error,
                    }
                    if bounds_error.startswith("item quantity "):
                        invalid_item_quantities.append(record)
                    else:
                        out_of_bounds.append(record)
            local_ids = [event["local_id"] for event in document[category] if "local_id" in event]
            duplicate_local_ids = sorted(
                value for value, count in Counter(local_ids).items() if count > 1
            )
            if duplicate_local_ids:
                local_id_duplicates.append(
                    {"map": map_name, "category": category, "local_ids": duplicate_local_ids}
                )
    if duplicate_identities:
        raise ValueError(f"duplicate event identities: {duplicate_identities}")
    if out_of_bounds:
        raise ValueError(f"out-of-bounds events: {out_of_bounds}")
    if invalid_item_quantities:
        raise ValueError(f"invalid packed item quantities: {invalid_item_quantities}")
    if local_id_duplicates:
        raise ValueError(f"duplicate local IDs: {local_id_duplicates}")
    if len(item_records) != 44 or len([item for item in item_records if item["quantity"] == 5]) != 6:
        raise ValueError("custom item wrapper count/quantity invariant differs")
    woodgrove_warps = [
        event for event in candidate_documents["PetalburgWoods"]["warp_events"]
        if event.get("dest_map") == "MAP_PETALBURG_WOODGROVE"
    ]
    if not woodgrove_warps or any(event.get("elevation") != 3 for event in woodgrove_warps):
        raise ValueError("PetalburgWoods Woodgrove access must retain elevation 3")
    authoritative_after = {
        map_name: sha256((root / "data" / "maps" / map_name / "map.json").read_bytes())
        for map_name in authoritative_before
    }
    if authoritative_after != authoritative_before:
        raise RuntimeError("authoritative map JSON changed during candidate generation")

    custom_validations = []
    for record in audit["scope"]["custom_maps"]:
        custom_validations.append(
            {
                "map": record["map"],
                "validation_only": True,
                "event_arrays_equal": record["event_arrays_equal"],
                "blob_sha256": record["blob_sha256"],
            }
        )
    dependency_validation = validate_dependency_postimages(
        {
            path: (root / path).read_bytes()
            for path in DEPENDENCY_POSTIMAGE_SPECS
            if (root / path).is_file()
        },
        {
            path: sources.bytes("current", path)
            for path in DEPENDENCY_POSTIMAGE_SPECS
        },
        dependency_resolutions,
        dependency_by_label,
        DEPENDENCY_POSTIMAGE_SPECS,
    )
    missing_dependencies = dependency_validation["missing_dependencies"]
    if missing_dependencies:
        raise ValueError(
            f"missing or altered reviewed dependencies: {missing_dependencies}"
        )
    dependency_records = dependency_validation["dependency_records"]
    dependency_writes = dependency_validation["dependency_writes"]
    named_automatic = {}
    for label in (
        "Route104_EventScript_Darian",
        "Route120_EventScript_Callie",
        "RustboroCity_EventScript_Boy1",
        "SootopolisCity_EventScript_Archie",
    ):
        dependency = dependency_by_label[label]
        named_automatic[label] = {
            "classification": dependency["classification"],
            "current_owner": dependency["owners"]["current"],
            "current_sha256": dependency["normalized_block_sha256"]["current"],
            "disposition": "retained_current",
        }
    quantity_five = [item for item in item_records if item["quantity"] == 5]
    report = {
        "schema_version": 1,
        "mode": "candidate-only",
        "source_commits": audit["source_commits"],
        "invariants": {
            "scoped_map_count": len(map_validations),
            "archive_changed_map_count": audit["scope"]["archive_changed_map_count"],
            "resolution_count": len(entries),
            "unresolved_count": 0,
            "unused_resolution_count": 0,
            "ambiguity_group_count": len(groups),
            "duplicate_event_identity_count": 0,
            "out_of_bounds_event_count": 0,
            "invalid_item_quantity_count": len(invalid_item_quantities),
            "duplicate_local_id_count": 0,
            "missing_dependency_count": len(missing_dependencies),
            "custom_item_wrapper_count": len(item_records),
            "quantity_five_item_count": len(quantity_five),
        },
        "candidate_map_count": len(changed_maps),
        "candidate_maps": changed_maps,
        "candidate_sha256": dict(sorted(candidate_hashes.items())),
        "authoritative_map_sha256_aggregate": sha256(
            json.dumps(authoritative_before, sort_keys=True, separators=(",", ":")).encode()
        ),
        "woodgrove_access_warps": woodgrove_warps,
        "event_disposition_counts": dict(sorted(disposition_counts.items())),
        "map_validations": map_validations,
        "custom_map_validations": custom_validations,
        "item_wrappers": item_records,
        "quantity_five_items": quantity_five,
        "dependencies": dependency_records,
        "named_current_dependency_validations": named_automatic,
        "dependency_writes": dependency_writes,
    }
    return report, candidate_files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-dir", required=True, type=Path)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--resolutions", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--audit-only", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    if args.apply:
        parser.error("--apply is reserved for Task 5; candidate generation never writes authoritative maps")
    root = repository_root()
    candidate_path, audit_path, resolutions_path, report_path = _validate_paths(root, args)
    commits = {name: resolve_commit(ref) for name, ref in SOURCE_COMMITS.items()}
    for name, expected in SOURCE_COMMITS.items():
        if commits[name] != expected:
            raise RuntimeError(f"pinned {name} ref moved/tampered: resolved {commits[name]}, expected {expected}")
    layout_report_path = (root / LAYOUT_REPORT).resolve()
    layout_report_data = layout_report_path.read_bytes()
    audit, known = build_audit(root, commits, layout_report_data)
    ambiguity_groups = {
        group["id"]: group for group in audit["ambiguity_groups"]
    }
    dependencies = {
        dependency["label"]: dependency for dependency in audit["dependencies"]
    }
    resolutions = _validate_resolutions(
        resolutions_path, known, ambiguity_groups, dependencies
    )
    resolved_ids = {entry["id"] for entry in resolutions["resolutions"]}
    audit["resolved_count"] = len(resolved_ids)
    audit["unresolved"] = [item for item in audit["unresolved"] if item["id"] not in resolved_ids]
    audit["unresolved_count"] = len(audit["unresolved"])
    audit["resolution_ids"] = sorted(resolved_ids)
    if args.audit_only:
        resolution_data = _resolution_bytes(resolutions)
        audit_data = _json_bytes(audit)
        publish_evidence_pair(
            audit_path, audit_data, resolutions_path, resolution_data
        )
    else:
        if audit["unresolved_count"]:
            raise UnresolvedConflictError(item["id"] for item in audit["unresolved"])
        sources = Sources(commits)
        documents: dict[str, dict[str, dict[str, list[dict[str, object]]]]] = {}
        for map_audit in audit["maps"]:
            map_name = map_audit["map"]
            path = f"data/maps/{map_name}/map.json"
            documents[map_name] = {
                source: _event_arrays(sources.json(source, path), f"{source}:{path}")
                for source in SOURCE_COMMITS
            }
        report, candidate_files = generate_candidates_and_report(
            root, audit, documents, resolutions, sources
        )
        publish_candidate_bundle(
            candidate_path, candidate_files, report_path, _json_bytes(report)
        )
        print(
            f"candidates: maps={report['candidate_map_count']} "
            f"items={report['invariants']['custom_item_wrapper_count']} "
            f"quantity-five={report['invariants']['quantity_five_item_count']}"
        )
        print(f"report file: {report_path}")
        return 0
    print(
        f"audit: layouts={EXPECTED_SHARED_LAYOUTS} maps={EXPECTED_SCOPED_MAPS} "
        f"archive-changed={EXPECTED_ARCHIVE_CHANGED_MAPS} unresolved={audit['unresolved_count']}"
    )
    print(f"audit file: {audit_path}")
    print(f"resolutions file: {resolutions_path}")
    return 2 if audit["unresolved_count"] else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
