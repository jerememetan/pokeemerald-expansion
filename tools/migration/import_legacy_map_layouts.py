#!/usr/bin/env python3
"""Audit and import custom map-layout binaries from the legacy archive."""

from __future__ import annotations

import argparse
import functools
import hashlib
import json
import os
import subprocess
import uuid
from pathlib import Path, PurePosixPath
from typing import Any


LEGACY_REF = "archive/master-pre-1.16.3"
AUDITED_LEGACY_COMMIT = "f5e81e85df6fe40ae490bf7268d0186d7f0426ed"
BASE_REF = "024848a9e9c0ae30cbb9a269779504561d5443d3"
CURRENT_BASELINE_COMMIT = "a68f1c7c8af8a6138a766cd98f3d3292cda14614"
LAYOUTS_JSON = "data/layouts/layouts.json"
CUSTOM_LAYOUT_IDS = {
    "LAYOUT_LITTLEROOT_EXTENSION",
    "LAYOUT_VERDANTURF_EXTENSION",
    "LAYOUT_PETALBURG_WOODGROVE",
}
METADATA_FIELDS = ("width", "height", "primary_tileset", "secondary_tileset")

EXPECTED_LAYOUT_COUNTS = {"legacy": 444, "base": 441, "current": 785, "shared": 441}
EXPECTED_MAP_COUNTS = {
    "identical": 380,
    "custom_only": 61,
    "upstream_only": 0,
    "both_changed_conflicts": 0,
}
EXPECTED_CUSTOM_BORDER = "data/layouts/VerdanturfTown/border.bin"
EXPECTED_CUSTOM_LAYOUTS = {
    "LAYOUT_LITTLEROOT_EXTENSION": {
        "name": "Littleroot_Extension_Layout",
        "width": 8,
        "height": 10,
        "primary_tileset": "gTileset_General",
        "secondary_tileset": "gTileset_Petalburg",
        "border_filepath": "data/layouts/Littleroot_Extension/border.bin",
        "blockdata_filepath": "data/layouts/Littleroot_Extension/map.bin",
    },
    "LAYOUT_VERDANTURF_EXTENSION": {
        "name": "Verdanturf_Extension_Layout",
        "width": 10,
        "height": 20,
        "primary_tileset": "gTileset_General",
        "secondary_tileset": "gTileset_Mauville",
        "border_filepath": "data/layouts/Verdanturf_Extension/border.bin",
        "blockdata_filepath": "data/layouts/Verdanturf_Extension/map.bin",
    },
    "LAYOUT_PETALBURG_WOODGROVE": {
        "name": "PetalburgWoodgrove_Layout",
        "width": 25,
        "height": 30,
        "primary_tileset": "gTileset_General",
        "secondary_tileset": "gTileset_Petalburg",
        "border_filepath": "data/layouts/PetalburgWoodgrove/border.bin",
        "blockdata_filepath": "data/layouts/PetalburgWoodgrove/map.bin",
    },
}


@functools.cache
def git_bytes(ref: str, path: str) -> bytes:
    """Read one repository path from an immutable Git revision."""
    source = f"{ref}:{path}"
    try:
        result = subprocess.run(
            ["git", "show", source], check=True, capture_output=True
        )
    except subprocess.CalledProcessError as error:
        detail = error.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"failed to read {source}: {detail}") from error
    return result.stdout


def git_json(ref: str, path: str) -> dict[str, Any]:
    """Read and decode one JSON object from a Git revision."""
    try:
        value = json.loads(git_bytes(ref, path).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid JSON at {ref}:{path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object at {ref}:{path}")
    return value


def sha256(data: bytes) -> str:
    """Return the lowercase SHA-256 digest for bytes."""
    return hashlib.sha256(data).hexdigest()


def repository_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        capture_output=True,
        text=True,
    )
    return Path(result.stdout.strip()).resolve()


def resolve_legacy_commit(
    ref: str = LEGACY_REF, audited_commit: str = AUDITED_LEGACY_COMMIT
) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", f"{ref}^{{commit}}"],
        check=True,
        capture_output=True,
        text=True,
    )
    resolved_commit = result.stdout.strip()
    if resolved_commit != audited_commit:
        raise ValueError(
            f"legacy ref {ref} resolved to {resolved_commit!r}; "
            f"expected audited commit {audited_commit}"
        )
    return resolved_commit


def validate_source_refs(legacy_commit: str) -> None:
    for commit in (BASE_REF, CURRENT_BASELINE_COMMIT):
        result = subprocess.run(
            ["git", "rev-parse", "--verify", f"{commit}^{{commit}}"],
            check=True,
            capture_output=True,
            text=True,
        )
        if result.stdout.strip() != commit:
            raise ValueError(f"immutable source commit did not resolve exactly: {commit}")
    result = subprocess.run(
        ["git", "merge-base", "--all", legacy_commit, CURRENT_BASELINE_COMMIT],
        check=True,
        capture_output=True,
        text=True,
    )
    merge_bases = result.stdout.splitlines()
    if merge_bases != [BASE_REF]:
        raise ValueError(
            f"unexpected merge base for {LEGACY_REF} and {CURRENT_BASELINE_COMMIT}: "
            f"{merge_bases} "
            f"(expected [{BASE_REF!r}])"
        )


def layout_index(document: dict[str, Any], source: str) -> dict[str, dict[str, Any]]:
    layouts = document.get("layouts")
    if not isinstance(layouts, list):
        raise ValueError(f"{source} has no layouts list")

    indexed: dict[str, dict[str, Any]] = {}
    for position, layout in enumerate(layouts):
        if not isinstance(layout, dict) or not isinstance(layout.get("id"), str):
            raise ValueError(f"{source} layout {position} is invalid")
        layout_id = layout["id"]
        if layout_id in indexed:
            raise ValueError(f"{source} contains duplicate layout ID {layout_id}")
        indexed[layout_id] = layout
    return indexed


def checked_binary_path(value: object, filename: str, context: str) -> str:
    if not isinstance(value, str) or "\\" in value:
        raise ValueError(f"{context} has an invalid {filename} path")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or ".." in path.parts
        or len(path.parts) < 4
        or path.parts[:2] != ("data", "layouts")
        or path.name != filename
        or str(path) != value
    ):
        raise ValueError(f"{context} has unsafe or noncanonical path {value!r}")
    return value


def git_optional_bytes(ref: str, path: str) -> bytes | None:
    """Read one Git path, returning None only when that path is absent."""
    result = subprocess.run(
        ["git", "ls-tree", "-z", "--name-only", ref, "--", path],
        check=True,
        capture_output=True,
    )
    if not result.stdout:
        return None
    listed_path = result.stdout.removesuffix(b"\0").decode("utf-8")
    if listed_path != path:
        raise RuntimeError(f"unexpected Git path while inspecting {ref}:{path}: {listed_path}")
    return git_bytes(ref, path)


def classify(legacy: bytes, base: bytes, current: bytes) -> str:
    legacy_changed = legacy != base
    current_changed = current != base
    if not legacy_changed and not current_changed:
        return "identical"
    if legacy_changed and not current_changed:
        return "custom_only"
    if not legacy_changed and current_changed:
        return "upstream_only"
    return "both_changed_conflicts"


def ensure_within(root: Path, target: Path, context: str) -> None:
    try:
        target.relative_to(root)
    except ValueError as error:
        raise ValueError(f"{context} escapes {root}") from error


def write_candidate(candidate_root: Path, path: str, data: bytes) -> Path:
    target = candidate_root.joinpath(*PurePosixPath(path).parts).resolve()
    ensure_within(candidate_root, target, f"candidate path {path}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return target


def verify_destination_state(
    root: Path, writes: list[tuple[str, str, bytes, bytes | None]]
) -> str:
    baseline_paths = []
    postimage_paths = []
    mismatches = []
    for _layout_id, path, new_data, expected_old_data in writes:
        target = root.joinpath(*PurePosixPath(path).parts).resolve()
        ensure_within(root / "data" / "layouts", target, f"destination path {path}")
        try:
            live_data = target.read_bytes()
        except FileNotFoundError:
            live_data = None
        except (IsADirectoryError, PermissionError) as error:
            mismatches.append(f"{path}: could not read destination ({error})")
            continue

        if live_data == expected_old_data:
            baseline_paths.append(path)
        elif live_data == new_data:
            postimage_paths.append(path)
        else:
            expected = (
                "absence"
                if expected_old_data is None
                else f"baseline sha256 {sha256(expected_old_data)}"
            )
            actual = "absence" if live_data is None else f"sha256 {sha256(live_data)}"
            mismatches.append(
                f"{path}: expected {expected} or postimage sha256 {sha256(new_data)}, "
                f"found {actual}"
            )
    if mismatches:
        raise RuntimeError(
            "authoritative layout destination mismatch; no candidate, report, or "
            "authoritative files were written:\n- "
            + "\n- ".join(mismatches)
        )
    if baseline_paths and postimage_paths:
        raise RuntimeError(
            "mixed authoritative layout state; no candidate, report, or authoritative "
            "files were written:\n- baseline paths: "
            + ", ".join(baseline_paths)
            + "\n- postimage paths: "
            + ", ".join(postimage_paths)
        )
    return "baseline" if baseline_paths else "postimage"


def _write_fsynced_file(temporary: Path, data: bytes) -> None:
    temporary.parent.mkdir(parents=True, exist_ok=True)
    with temporary.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _preserve_failed_restoration(
    restoration: Path,
    target: Path,
    old_data: bytes,
    cleanup_paths: set[Path],
) -> str:
    """Keep an exact preimage after restoration itself could not be installed."""
    cleanup_paths.discard(restoration)
    try:
        restoration_data = restoration.read_bytes()
    except BaseException as validation_error:
        return (
            f"restoration retained at {restoration}; could not revalidate captured "
            f"preimage: {validation_error}"
        )
    if restoration_data != old_data:
        return f"restoration retained at {restoration}, but differs from captured preimage"
    recovery = target.parent / (
        f".{target.name}.legacy-map-layout-recovery-{uuid.uuid4().hex}.bin"
    )
    if os.path.lexists(recovery):
        return (
            f"exact preimage retained at {restoration}; recovery path unexpectedly "
            f"exists: {recovery}"
        )
    try:
        os.replace(restoration, recovery)
    except BaseException as publication_error:
        return (
            f"exact preimage retained at {restoration}; recovery publication failed: "
            f"{publication_error}"
        )
    return f"exact preimage preserved at recovery path {recovery}"


def apply_writes_atomically(
    root: Path,
    writes: list[tuple[str, str, bytes, bytes | None]],
    validated_candidates: dict[str, bytes],
) -> int:
    # Fail before staging anything if classification-time inputs have changed.
    if verify_destination_state(root, writes) == "postimage":
        return 0

    transaction_id = uuid.uuid4().hex
    cleanup_paths: set[Path] = set()
    plans: list[tuple[Path, Path | None, Path, bytes | None, str]] = []
    for index, (_layout_id, path, _new_data, old_data) in enumerate(writes):
        target = root.joinpath(*PurePosixPath(path).parts).resolve()
        ensure_within(root / "data" / "layouts", target, f"apply path {path}")
        forward = target.parent / (
            f".{target.name}.legacy-layout-{transaction_id}-forward-{index}"
        )
        restoration = (
            target.parent
            / f".{target.name}.legacy-layout-{transaction_id}-rollback-{index}"
            if old_data is not None
            else None
        )
        planned_temporaries = [forward]
        if restoration is not None:
            planned_temporaries.append(restoration)
        for temporary in planned_temporaries:
            if os.path.lexists(temporary):
                raise RuntimeError(f"temporary apply path unexpectedly exists: {temporary}")
            cleanup_paths.add(temporary)
        plans.append((forward, restoration, target, old_data, path))

    try:
        for forward, restoration, _target, old_data, path in plans:
            _write_fsynced_file(forward, validated_candidates[path])
            if restoration is not None:
                assert old_data is not None
                _write_fsynced_file(restoration, old_data)

        # Close the staging race before the first authoritative replacement.
        if verify_destination_state(root, writes) != "baseline":
            raise RuntimeError("authoritative layout destinations changed while staging")

        rollback_plans: list[tuple[Path, Path | None, bytes | None, str]] = []
        replacing_path = "<none>"
        try:
            for forward, restoration, target, old_data, replacing_path in plans:
                rollback_plans.append((target, restoration, old_data, replacing_path))
                os.replace(forward, target)
        except BaseException as apply_error:
            rollback_errors = []
            for target, restoration, old_data, path in reversed(rollback_plans):
                try:
                    if old_data is None:
                        target.unlink(missing_ok=True)
                    else:
                        if restoration is None:
                            raise RuntimeError("missing restoration path")
                        os.replace(restoration, target)
                except BaseException as rollback_error:
                    detail = f"{path}: {rollback_error}"
                    if old_data is not None and restoration is not None:
                        try:
                            detail += "; " + _preserve_failed_restoration(
                                restoration, target, old_data, cleanup_paths
                            )
                        except BaseException as preservation_error:
                            detail += f"; preimage preservation failed: {preservation_error}"
                    rollback_errors.append(detail)

            if not rollback_errors:
                try:
                    if verify_destination_state(root, writes) != "baseline":
                        raise RuntimeError("rollback did not restore the baseline state")
                except BaseException as rollback_error:
                    rollback_errors.append(str(rollback_error))

            if rollback_errors:
                raise RuntimeError(
                    f"atomic apply failed while replacing {replacing_path}; rollback also "
                    f"failed: {'; '.join(rollback_errors)}"
                ) from apply_error
            raise RuntimeError(
                f"atomic apply failed while replacing {replacing_path}; "
                "all replaced files were restored"
            ) from apply_error
        if verify_destination_state(root, writes) != "postimage":
            raise RuntimeError("atomic apply did not install the complete postimage state")
        return len(writes)
    finally:
        for temporary in cleanup_paths:
            temporary.unlink(missing_ok=True)


def build_import(
    root: Path,
) -> tuple[dict[str, object], list[tuple[str, str, bytes, bytes | None]]]:
    legacy_commit = resolve_legacy_commit()
    validate_source_refs(legacy_commit)
    legacy = layout_index(git_json(legacy_commit, LAYOUTS_JSON), "legacy layouts")
    base = layout_index(git_json(BASE_REF, LAYOUTS_JSON), "base layouts")
    current = layout_index(
        git_json(CURRENT_BASELINE_COMMIT, LAYOUTS_JSON), "current layouts"
    )

    shared_ids = set(legacy) & set(current)
    archive_only_ids = set(legacy) - set(current)
    layout_counts = {
        "legacy": len(legacy),
        "base": len(base),
        "current": len(current),
        "shared": len(shared_ids),
        "archive_only": len(archive_only_ids),
        "current_only": len(set(current) - set(legacy)),
    }
    for key, expected in EXPECTED_LAYOUT_COUNTS.items():
        if layout_counts[key] != expected:
            raise ValueError(
                f"unexpected {key} layout count: {layout_counts[key]} (expected {expected})"
            )
    if archive_only_ids != CUSTOM_LAYOUT_IDS:
        raise ValueError(
            "unexpected archive-only layout IDs: "
            f"missing={sorted(CUSTOM_LAYOUT_IDS - archive_only_ids)}, "
            f"unexpected={sorted(archive_only_ids - CUSTOM_LAYOUT_IDS)}"
        )
    if set(base) != shared_ids:
        raise ValueError(
            "base layout IDs do not exactly match the archive/current shared layout IDs"
        )

    map_counts = {key: 0 for key in EXPECTED_MAP_COUNTS}
    border_counts = {key: 0 for key in EXPECTED_MAP_COUNTS}
    map_custom: list[tuple[str, str, bytes]] = []
    border_owners: dict[str, list[str]] = {}

    for layout_id in sorted(shared_ids):
        legacy_layout = legacy[layout_id]
        base_layout = base[layout_id]
        current_layout = current[layout_id]
        for field in METADATA_FIELDS:
            values = (legacy_layout.get(field), base_layout.get(field), current_layout.get(field))
            if values[0] != values[1] or values[0] != values[2]:
                raise ValueError(
                    f"metadata mismatch for {layout_id}.{field}: "
                    f"legacy={values[0]!r}, base={values[1]!r}, current={values[2]!r}"
                )

        paths: dict[str, str] = {}
        for field, filename in (
            ("blockdata_filepath", "map.bin"),
            ("border_filepath", "border.bin"),
        ):
            ref_paths = [
                checked_binary_path(layout.get(field), filename, f"{name} {layout_id}")
                for name, layout in (
                    ("legacy", legacy_layout),
                    ("base", base_layout),
                    ("current", current_layout),
                )
            ]
            if len(set(ref_paths)) != 1:
                raise ValueError(f"binary path mismatch for {layout_id}.{field}: {ref_paths}")
            paths[field] = ref_paths[0]

        map_path = paths["blockdata_filepath"]
        map_legacy = git_bytes(legacy_commit, map_path)
        map_base = git_bytes(BASE_REF, map_path)
        map_current = git_bytes(CURRENT_BASELINE_COMMIT, map_path)
        map_class = classify(map_legacy, map_base, map_current)
        map_counts[map_class] += 1
        if map_class == "custom_only":
            map_custom.append((layout_id, map_path, map_legacy))

        border_path = paths["border_filepath"]
        border_owners.setdefault(border_path, []).append(layout_id)

    border_classes: dict[str, str] = {}
    for border_path in sorted(border_owners):
        border_class = classify(
            git_bytes(legacy_commit, border_path),
            git_bytes(BASE_REF, border_path),
            git_bytes(CURRENT_BASELINE_COMMIT, border_path),
        )
        border_classes[border_path] = border_class
        border_counts[border_class] += 1

    if map_counts != EXPECTED_MAP_COUNTS:
        raise ValueError(f"unexpected map classification counts: {map_counts}")
    custom_border_paths = []
    for border_path in sorted(border_owners):
        if border_classes[border_path] == "custom_only":
            custom_border_paths.append(border_path)
    if custom_border_paths != [EXPECTED_CUSTOM_BORDER]:
        raise ValueError(f"unexpected custom-only border paths: {custom_border_paths}")
    if border_counts["upstream_only"] or border_counts["both_changed_conflicts"]:
        raise ValueError(f"unexpected border classification counts: {border_counts}")

    owner_ids = border_owners[EXPECTED_CUSTOM_BORDER]
    if len(owner_ids) != 1:
        raise ValueError(
            f"custom border {EXPECTED_CUSTOM_BORDER} has ambiguous owners: {owner_ids}"
        )
    shared_border = (
        owner_ids[0],
        EXPECTED_CUSTOM_BORDER,
        git_bytes(legacy_commit, EXPECTED_CUSTOM_BORDER),
    )

    custom_pairs: list[tuple[str, str, bytes]] = []
    for layout_id in sorted(CUSTOM_LAYOUT_IDS):
        layout = legacy[layout_id]
        expected = EXPECTED_CUSTOM_LAYOUTS[layout_id]
        for field, expected_value in expected.items():
            if layout.get(field) != expected_value:
                raise ValueError(
                    f"unexpected custom layout value for {layout_id}.{field}: "
                    f"{layout.get(field)!r} (expected {expected_value!r})"
                )
        map_path = checked_binary_path(
            layout.get("blockdata_filepath"), "map.bin", f"legacy {layout_id}"
        )
        border_path = checked_binary_path(
            layout.get("border_filepath"), "border.bin", f"legacy {layout_id}"
        )
        map_data = git_bytes(legacy_commit, map_path)
        border_data = git_bytes(legacy_commit, border_path)
        expected_map_length = expected["width"] * expected["height"] * 2
        if len(map_data) != expected_map_length:
            raise ValueError(
                f"custom map {map_path} is {len(map_data)} bytes; expected {expected_map_length}"
            )
        if len(border_data) != 8:
            raise ValueError(f"custom border {border_path} is {len(border_data)} bytes; expected 8")
        custom_pairs.extend(
            [(layout_id, map_path, map_data), (layout_id, border_path, border_data)]
        )

    writes = sorted([*map_custom, shared_border, *custom_pairs], key=lambda item: item[1])
    if len(writes) != 68 or len({path for _, path, _ in writes}) != 68:
        raise ValueError(
            f"unexpected write set size or duplicate path: writes={len(writes)}, "
            f"unique={len({path for _, path, _ in writes})}"
        )

    custom_target_paths = {path for _layout_id, path, _data in custom_pairs}
    writes_with_preimages = []
    write_records = []
    for layout_id, path, data in writes:
        old_data = git_optional_bytes(CURRENT_BASELINE_COMMIT, path)
        if path in custom_target_paths and old_data is not None:
            raise ValueError(
                f"archive-only custom layout target exists in baseline: {path}"
            )
        writes_with_preimages.append((layout_id, path, data, old_data))
        write_records.append(
            {
                "layout_id": layout_id,
                "repository_path": path,
                "old_sha256": sha256(old_data) if old_data is not None else None,
                "new_sha256": sha256(data),
                "byte_length": len(data),
            }
        )

    verify_destination_state(root, writes_with_preimages)

    report: dict[str, object] = {
        "source_refs": {
            "legacy_ref": LEGACY_REF,
            "legacy_commit": legacy_commit,
            "base_ref": BASE_REF,
            "current_source": "worktree",
            "layouts_json": LAYOUTS_JSON,
        },
        "classification_counts": {
            "layouts": layout_counts,
            "maps": map_counts,
            "unique_borders": border_counts,
        },
        "writes": write_records,
    }
    return report, writes_with_preimages


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-dir", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    root = repository_root()
    candidate_root = args.candidate_dir.resolve()
    report_path = args.report.resolve()
    if candidate_root == root:
        parser.error("--candidate-dir must not be the repository root")
    if report_path == root / LAYOUTS_JSON:
        parser.error("--report must not overwrite the layouts registry")

    report, writes = build_import(root)
    candidate_paths: dict[str, Path] = {}
    for _layout_id, path, data, _old_data in writes:
        authoritative = root.joinpath(*PurePosixPath(path).parts).resolve()
        candidate = candidate_root.joinpath(*PurePosixPath(path).parts).resolve()
        if report_path in (authoritative, candidate):
            parser.error(f"--report collides with layout binary path {path}")
        if candidate == authoritative:
            parser.error(f"--candidate-dir would overwrite authoritative path {path}")
        candidate_paths[path] = write_candidate(candidate_root, path, data)

    validated_candidates: dict[str, bytes] = {}
    for _layout_id, path, expected_data, _old_data in writes:
        candidate_data = candidate_paths[path].read_bytes()
        if candidate_data != expected_data:
            raise ValueError(f"candidate verification failed for {path}")
        validated_candidates[path] = candidate_data

    if args.apply:
        replacement_count = apply_writes_atomically(root, writes, validated_candidates)
        print(f"applied {replacement_count} validated layout binaries")
    else:
        print(f"wrote {len(writes)} candidate layout binaries to {candidate_root}")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_bytes((json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    print(f"report: {report_path}")
    print(
        "maps: identical=380 custom-only=61 upstream-only=0 both-changed=0; "
        "custom shared borders=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
