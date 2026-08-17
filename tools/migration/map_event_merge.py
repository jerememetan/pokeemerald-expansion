"""Pure semantic alignment and three-way merging for map event records."""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass
from typing import Callable, Iterable


__all__ = [
    "PLACEMENT_FIELDS",
    "SCHEMA_ONLY_FIELDS",
    "IDENTITY_FIELDS",
    "EventRef",
    "Match",
    "MergeResult",
    "AmbiguousMatchError",
    "UnresolvedConflictError",
    "freeze",
    "behavior_signature",
    "exact_signature",
    "align_in_stages",
    "align_side",
    "merge_fields_or_conflict",
    "merge_base_event",
    "merge_additions_or_conflict",
    "merge_added_event",
    "align_three_way",
    "build_ordered_candidates",
    "merge_category",
    "extract_legacy_item",
    "adapt_item_ball",
]


PLACEMENT_FIELDS = frozenset({"x", "y", "elevation"})
SCHEMA_ONLY_FIELDS = frozenset({"local_id"})

IDENTITY_FIELDS = {
    "object_events": (
        "type",
        "script",
        "flag",
        "trainer_type",
        "trainer_sight_or_berry_tree_id",
        "graphics_id",
        "movement_type",
        "movement_range_x",
        "movement_range_y",
        "target_local_id",
        "target_map",
    ),
    "warp_events": ("dest_map", "dest_warp_id"),
    "coord_events": ("type", "script", "weather", "var", "var_value"),
    "bg_events": (
        "type",
        "script",
        "item",
        "flag",
        "player_facing_dir",
        "secret_base_id",
    ),
}

_OWNERSHIP_FIELDS = {
    "object_events": ("graphics_id",),
    "coord_events": ("type",),
    "bg_events": ("type",),
}

_REQUIRED_EVENT_FIELDS = {
    "object_events": frozenset(
        {
            "graphics_id",
            "x",
            "y",
            "elevation",
            "movement_type",
            "movement_range_x",
            "movement_range_y",
            "trainer_type",
            "trainer_sight_or_berry_tree_id",
            "script",
            "flag",
        }
    ),
    "warp_events": frozenset(
        {"x", "y", "elevation", "dest_map", "dest_warp_id"}
    ),
    "coord_events": frozenset({"type", "x", "y", "elevation"}),
    "bg_events": frozenset({"type", "x", "y", "elevation"}),
}

_REQUIRED_CLONE_OBJECT_FIELDS = frozenset(
    {"type", "graphics_id", "x", "y", "target_local_id", "target_map"}
)

_REQUIRED_SUBTYPE_FIELDS = {
    "coord_events": {
        "trigger": frozenset({"var", "var_value", "script"}),
        "weather": frozenset({"weather"}),
    },
    "bg_events": {
        "sign": frozenset({"player_facing_dir", "script"}),
        "hidden_item": frozenset({"item", "flag"}),
        "secret_base": frozenset({"secret_base_id"}),
    },
}


@dataclass(frozen=True)
class EventRef:
    category: str
    index: int


@dataclass(frozen=True)
class Match:
    base: EventRef | None
    archive: EventRef | None
    current: EventRef | None
    method: str


@dataclass(frozen=True)
class MergeResult:
    event: dict[str, object] | None
    disposition: str
    field_sources: dict[str, str]
    conflict: str | None


class AmbiguousMatchError(ValueError):
    """Raised when semantic signatures cannot establish unique ownership."""

    def __init__(
        self,
        category: str,
        base_indices: Iterable[int],
        side_indices: Iterable[int] = (),
        *,
        archive_indices: Iterable[int] | None = None,
        current_indices: Iterable[int] | None = None,
    ) -> None:
        self.category = category
        self.base_indices = tuple(sorted(base_indices))
        self.side_indices = tuple(sorted(side_indices))
        self.archive_indices = (
            tuple(sorted(archive_indices)) if archive_indices is not None else None
        )
        self.current_indices = (
            tuple(sorted(current_indices)) if current_indices is not None else None
        )
        if self.archive_indices is not None or self.current_indices is not None:
            message = (
                f"ambiguous {category} match: base={list(self.base_indices)}, "
                f"archive={list(self.archive_indices or ())}, "
                f"current={list(self.current_indices or ())}"
            )
        else:
            message = (
                f"ambiguous {category} match: "
                f"base={list(self.base_indices)}, side={list(self.side_indices)}"
            )
        super().__init__(message)


class UnresolvedConflictError(ValueError):
    """Raised when candidate generation encounters unreviewed conflicts."""

    def __init__(self, identifiers: Iterable[str]) -> None:
        self.identifiers = tuple(sorted(identifiers))
        super().__init__(f"unresolved conflicts: {', '.join(self.identifiers)}")


@dataclass(frozen=True)
class _Alignment:
    category: str
    base_events: tuple[dict[str, object], ...]
    archive_events: tuple[dict[str, object], ...]
    current_events: tuple[dict[str, object], ...]
    matches: tuple[Match, ...]


@dataclass(frozen=True)
class _Candidate:
    identifier: str
    match: Match
    result: MergeResult
    reviewed_events: tuple[dict[str, object], ...] | None = None


_MISSING = object()
_BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_LINE_COMMENT_RE = re.compile(r"(?m)(?://|@).*$")
_FINDITEM_RE = re.compile(
    r"(?m)^[ \t]*finditem[ \t]+(ITEM_[A-Za-z0-9_]+)[ \t]*$"
)


def freeze(value: object) -> object:
    """Convert nested JSON-like data into a deterministic hashable value."""

    if isinstance(value, dict):
        return tuple(sorted((key, freeze(item)) for key, item in value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(freeze(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return tuple(sorted(freeze(item) for item in value))
    return value


def _normalize_standard_object_type(
    event: dict[str, object],
) -> dict[str, object]:
    if "graphics_id" not in event or "type" in event:
        return event
    return {**event, "type": "object"}


def behavior_signature(category: str, event: dict[str, object]) -> tuple:
    """Return the category-specific identity payload for an event."""

    fields = IDENTITY_FIELDS[category]
    signature_event = (
        _normalize_standard_object_type(event)
        if category == "object_events"
        else event
    )
    return tuple((field, freeze(signature_event.get(field))) for field in fields)


def exact_signature(event: dict[str, object]) -> str:
    """Return canonical JSON while ignoring schema-only metadata."""

    normalized = {
        key: value for key, value in event.items() if key not in SCHEMA_ONLY_FIELDS
    }
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"))


def _exact_behavior_signature(event: dict[str, object]) -> object:
    signature_event = _normalize_standard_object_type(event)
    return freeze(
        {
            key: value
            for key, value in signature_event.items()
            if key not in PLACEMENT_FIELDS and key not in SCHEMA_ONLY_FIELDS
        }
    )


def _ownership_signature(category: str, event: dict[str, object]) -> object:
    if category == "warp_events":
        fields = tuple(sorted(PLACEMENT_FIELDS))
    else:
        fields = _OWNERSHIP_FIELDS[category]
    return tuple((field, freeze(event.get(field))) for field in fields)


def _signature_groups(
    indices: set[int],
    events: list[dict[str, object]],
    signature: Callable[[dict[str, object]], object],
) -> dict[object, list[int]]:
    groups: dict[object, list[int]] = {}
    for index in sorted(indices):
        groups.setdefault(signature(events[index]), []).append(index)
    return groups


def _align_indices(
    category: str,
    base: list[dict[str, object]],
    side: list[dict[str, object]],
    stages: tuple[tuple[str, Callable[[dict[str, object]], object]], ...],
) -> tuple[list[tuple[int, int, str]], set[int], set[int]]:
    unmatched_base = set(range(len(base)))
    unmatched_side = set(range(len(side)))
    matches: list[tuple[int, int, str]] = []

    for method, signature in stages:
        base_groups = _signature_groups(unmatched_base, base, signature)
        side_groups = _signature_groups(unmatched_side, side, signature)
        for value in sorted(base_groups.keys() & side_groups.keys(), key=repr):
            base_indices = base_groups[value]
            side_indices = side_groups[value]
            if len(base_indices) == 1 and len(side_indices) == 1:
                base_index = base_indices[0]
                side_index = side_indices[0]
                matches.append((base_index, side_index, method))
                unmatched_base.remove(base_index)
                unmatched_side.remove(side_index)

    identity = stages[-1][1]
    base_groups = _signature_groups(unmatched_base, base, identity)
    side_groups = _signature_groups(unmatched_side, side, identity)
    for value in sorted(base_groups.keys() & side_groups.keys(), key=repr):
        base_indices = base_groups[value]
        side_indices = side_groups[value]
        if len(base_indices) > 1 or len(side_indices) > 1:
            raise AmbiguousMatchError(category, base_indices, side_indices)

    matches.sort()
    return matches, unmatched_base, unmatched_side


def align_in_stages(
    category: str,
    base: list[dict[str, object]],
    side: list[dict[str, object]],
    stages: tuple[Callable[..., object], ...] | None = None,
) -> list[Match]:
    """Align one side to base through increasingly broad semantic stages."""

    if stages is None:
        named_stages = (
            ("exact", exact_signature),
            ("behavior", _exact_behavior_signature),
            ("identity", lambda event: behavior_signature(category, event)),
        )
    else:
        named_stages_list: list[tuple[str, Callable[[dict[str, object]], object]]] = []
        for index, signature in enumerate(stages):
            names = ("exact", "behavior", "identity")
            name = names[min(index, len(names) - 1)]
            if signature is behavior_signature:
                bound = lambda event, signature=signature: signature(category, event)
            else:
                bound = signature
            named_stages_list.append((name, bound))
        named_stages = tuple(named_stages_list)

    matched, unmatched_base, unmatched_side = _align_indices(
        category, base, side, named_stages
    )
    result = [
        Match(
            base=EventRef(category, base_index),
            archive=EventRef(category, side_index),
            current=None,
            method=method,
        )
        for base_index, side_index, method in matched
    ]
    result.extend(
        Match(EventRef(category, index), None, None, "unmatched_base")
        for index in sorted(unmatched_base)
    )
    result.extend(
        Match(None, EventRef(category, index), None, "unmatched_side")
        for index in sorted(unmatched_side)
    )
    return result


def align_side(
    category: str,
    base: list[dict[str, object]],
    side: list[dict[str, object]],
) -> list[Match]:
    """Align a base event list with one comparison side."""

    return align_in_stages(category, base, side)


def _schema_normalized(event: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in event.items() if key not in SCHEMA_ONLY_FIELDS}


def _events_equal_ignoring_schema(
    left: dict[str, object], right: dict[str, object]
) -> bool:
    return _schema_normalized(left) == _schema_normalized(right)


def _copy_value(value: object) -> object:
    return copy.deepcopy(value)


def merge_fields_or_conflict(
    category: str,
    base: dict[str, object],
    archive: dict[str, object] | None,
    current: dict[str, object] | None,
) -> MergeResult:
    """Three-way merge a base-owned event, failing closed on overlap."""

    if archive is None and current is None:
        return MergeResult(None, "converged_delete", {}, None)
    if archive is None:
        if current is not None and _events_equal_ignoring_schema(base, current):
            return MergeResult(None, "archive_custom_delete", {}, None)
        return MergeResult(
            None,
            "conflict",
            {},
            f"{category}: archive deleted while current changed",
        )
    if current is None:
        if _events_equal_ignoring_schema(base, archive):
            return MergeResult(None, "keep_current_delete", {}, None)
        return MergeResult(
            None,
            "conflict",
            {},
            f"{category}: current deleted while archive changed",
        )

    merged: dict[str, object] = {}
    field_sources: dict[str, str] = {}
    conflicts: list[str] = []
    for field in sorted(set(base) | set(archive) | set(current)):
        base_value = base.get(field, _MISSING)
        archive_value = archive.get(field, _MISSING)
        current_value = current.get(field, _MISSING)
        if archive_value == current_value:
            value = archive_value
            source = "base" if value == base_value else "converged"
        elif archive_value == base_value:
            value = current_value
            source = "current"
        elif current_value == base_value:
            value = archive_value
            source = "archive"
        else:
            conflicts.append(field)
            continue
        field_sources[field] = source
        if value is not _MISSING:
            merged[field] = _copy_value(value)

    if conflicts:
        return MergeResult(
            None,
            "conflict",
            field_sources,
            f"{category}: conflicting fields: {', '.join(conflicts)}",
        )

    changed_sources = {source for source in field_sources.values() if source != "base"}
    if not changed_sources:
        disposition = "unchanged"
    elif changed_sources == {"converged"}:
        disposition = "converged_change"
    elif changed_sources <= {"archive"}:
        disposition = "restore_archive_change"
    elif changed_sources <= {"current"}:
        disposition = "keep_current_change"
    else:
        disposition = "merge_nonconflicting_fields"
    return MergeResult(merged, disposition, field_sources, None)


def merge_base_event(
    category: str,
    base: dict[str, object],
    archive: dict[str, object] | None,
    current: dict[str, object] | None,
) -> MergeResult:
    return merge_fields_or_conflict(category, base, archive, current)


def merge_additions_or_conflict(
    category: str,
    archive: dict[str, object] | None,
    current: dict[str, object] | None,
) -> MergeResult:
    """Merge additions that have no common-base owner."""

    if archive is None and current is None:
        raise ValueError("an addition must exist in archive or current")
    if archive is None:
        return MergeResult(
            copy.deepcopy(current), "keep_current_only_addition", {}, None
        )
    if current is None:
        return MergeResult(
            copy.deepcopy(archive), "restore_archive_only_addition", {}, None
        )
    if exact_signature(archive) != exact_signature(current):
        differing = sorted(
            field
            for field in set(archive) | set(current)
            if archive.get(field, _MISSING) != current.get(field, _MISSING)
        )
        return MergeResult(
            None,
            "conflict",
            {},
            f"{category}: colliding additions differ in fields: {', '.join(differing)}",
        )

    event = copy.deepcopy(archive)
    sources = {field: "converged" for field in event}
    for field in SCHEMA_ONLY_FIELDS:
        if field in current:
            event[field] = copy.deepcopy(current[field])
        else:
            event.pop(field, None)
        if field in archive or field in current:
            sources[field] = "current"
    disposition = (
        "converged_addition"
        if archive == current
        else "merge_nonconflicting_additions"
    )
    return MergeResult(event, disposition, sources, None)


def merge_added_event(
    category: str,
    archive: dict[str, object] | None,
    current: dict[str, object] | None,
) -> MergeResult:
    return merge_additions_or_conflict(category, archive, current)


def _default_stages(
    category: str,
) -> tuple[tuple[str, Callable[[dict[str, object]], object]], ...]:
    return (
        ("exact", exact_signature),
        ("behavior", _exact_behavior_signature),
        ("identity", lambda event: behavior_signature(category, event)),
    )


def _align_review_ownership(
    category: str,
    base: list[dict[str, object]],
    side: list[dict[str, object]],
    unmatched_base: set[int],
    unmatched_side: set[int],
) -> list[tuple[int, int, str]]:
    signature = lambda event: _ownership_signature(category, event)
    base_groups = _signature_groups(unmatched_base, base, signature)
    side_groups = _signature_groups(unmatched_side, side, signature)
    matches: list[tuple[int, int, str]] = []
    for value in sorted(base_groups.keys() & side_groups.keys(), key=repr):
        base_indices = base_groups[value]
        side_indices = side_groups[value]
        if len(base_indices) != 1 or len(side_indices) != 1:
            raise AmbiguousMatchError(category, base_indices, side_indices)
        base_index = base_indices[0]
        side_index = side_indices[0]
        matches.append((base_index, side_index, "review_ownership"))
        unmatched_base.remove(base_index)
        unmatched_side.remove(side_index)
    return matches


def align_three_way(
    category: str,
    base: list[dict[str, object]],
    archive: list[dict[str, object]],
    current: list[dict[str, object]],
) -> _Alignment:
    """Align base ownership on both sides, then align unowned additions."""

    try:
        archive_matches, archive_unmatched_base, archive_additions = _align_indices(
            category,
            base,
            archive,
            _default_stages(category),
        )
        archive_matches.extend(
            _align_review_ownership(
                category,
                base,
                archive,
                archive_unmatched_base,
                archive_additions,
            )
        )
        archive_matches.sort()
    except AmbiguousMatchError as error:
        raise AmbiguousMatchError(
            category,
            error.base_indices,
            archive_indices=error.side_indices,
            current_indices=(),
        ) from error
    try:
        current_matches, current_unmatched_base, current_additions = _align_indices(
            category,
            base,
            current,
            _default_stages(category),
        )
        current_matches.extend(
            _align_review_ownership(
                category,
                base,
                current,
                current_unmatched_base,
                current_additions,
            )
        )
        current_matches.sort()
    except AmbiguousMatchError as error:
        raise AmbiguousMatchError(
            category,
            error.base_indices,
            archive_indices=(),
            current_indices=error.side_indices,
        ) from error
    archive_by_base = {
        base_index: (side_index, method)
        for base_index, side_index, method in archive_matches
    }
    current_by_base = {
        base_index: (side_index, method)
        for base_index, side_index, method in current_matches
    }

    common_unmatched_base = archive_unmatched_base & current_unmatched_base

    matches: list[Match] = []
    for base_index in range(len(base)):
        archive_match = archive_by_base.get(base_index)
        current_match = current_by_base.get(base_index)
        methods = [
            method
            for match in (archive_match, current_match)
            if match is not None
            for method in (match[1],)
        ]
        matches.append(
            Match(
                EventRef(category, base_index),
                EventRef(category, archive_match[0]) if archive_match else None,
                EventRef(category, current_match[0]) if current_match else None,
                "/".join(methods) if methods else "deleted_both",
            )
        )

    archive_added_indices = sorted(archive_additions)
    current_added_indices = sorted(current_additions)
    archive_added_events = [archive[index] for index in archive_added_indices]
    current_added_events = [current[index] for index in current_added_indices]
    try:
        addition_matches, unmatched_archive, unmatched_current = _align_indices(
            category,
            archive_added_events,
            current_added_events,
            _default_stages(category),
        )
        addition_matches.extend(
            _align_review_ownership(
                category,
                archive_added_events,
                current_added_events,
                unmatched_archive,
                unmatched_current,
            )
        )
        addition_matches.sort()
    except AmbiguousMatchError as error:
        raise AmbiguousMatchError(
            category,
            (),
            archive_indices=(
                archive_added_indices[offset] for offset in error.base_indices
            ),
            current_indices=(
                current_added_indices[offset] for offset in error.side_indices
            ),
        ) from error
    if common_unmatched_base and unmatched_archive and unmatched_current:
        if len(unmatched_archive) == 1 and len(unmatched_current) == 1:
            archive_offset = next(iter(unmatched_archive))
            current_offset = next(iter(unmatched_current))
            addition_matches.append(
                (archive_offset, current_offset, "review_distinct_additions")
            )
            unmatched_archive.clear()
            unmatched_current.clear()
        else:
            raise AmbiguousMatchError(
                category,
                common_unmatched_base,
                archive_indices=(
                    archive_added_indices[offset]
                    for offset in unmatched_archive
                ),
                current_indices=(
                    current_added_indices[offset]
                    for offset in unmatched_current
                ),
            )
    addition_matches.sort()
    for archive_offset, current_offset, method in addition_matches:
        matches.append(
            Match(
                None,
                EventRef(category, archive_added_indices[archive_offset]),
                EventRef(category, current_added_indices[current_offset]),
                f"addition_{method}",
            )
        )
    matches.extend(
        Match(
            None,
            EventRef(category, archive_added_indices[offset]),
            None,
            "archive_only_addition",
        )
        for offset in sorted(unmatched_archive)
    )
    matches.extend(
        Match(
            None,
            None,
            EventRef(category, current_added_indices[offset]),
            "current_only_addition",
        )
        for offset in sorted(unmatched_current)
    )
    return _Alignment(
        category,
        tuple(copy.deepcopy(base)),
        tuple(copy.deepcopy(archive)),
        tuple(copy.deepcopy(current)),
        tuple(matches),
    )


def _candidate_identifier(match: Match) -> str:
    category = next(
        ref.category for ref in (match.base, match.archive, match.current) if ref is not None
    )
    if match.base is not None:
        return f"{category}:base:{match.base.index}"
    archive_index = match.archive.index if match.archive else "none"
    current_index = match.current.index if match.current else "none"
    return f"{category}:addition:archive:{archive_index}:current:{current_index}"


def _candidate_for_match(
    alignment: _Alignment,
    match: Match,
) -> _Candidate:
    base_event = alignment.base_events[match.base.index] if match.base else None
    archive_event = alignment.archive_events[match.archive.index] if match.archive else None
    current_event = alignment.current_events[match.current.index] if match.current else None
    if "review_" in match.method:
        result = MergeResult(
            None,
            "conflict",
            {},
            f"{alignment.category}: weak ownership requires reviewed resolution",
        )
    elif base_event is not None:
        result = merge_base_event(
            alignment.category, base_event, archive_event, current_event
        )
    else:
        result = merge_added_event(alignment.category, archive_event, current_event)
    identifier = _candidate_identifier(match)
    return _Candidate(identifier, match, result)


def _validate_resolution_event(
    category: str, event: dict[str, object]
) -> None:
    if category == "object_events":
        event_type = event.get("type", "object")
        if event_type == "clone":
            required = _REQUIRED_CLONE_OBJECT_FIELDS
        elif event_type == "object":
            required = _REQUIRED_EVENT_FIELDS[category]
        else:
            raise ValueError(
                f"resolution event has unsupported object_events type: {event_type!r}"
            )
    else:
        required = _REQUIRED_EVENT_FIELDS[category]
    missing = sorted(required - event.keys())
    if category in _REQUIRED_SUBTYPE_FIELDS and "type" in event:
        event_type = event["type"]
        subtype_fields = _REQUIRED_SUBTYPE_FIELDS[category]
        if not isinstance(event_type, str) or event_type not in subtype_fields:
            raise ValueError(
                f"resolution event has unsupported {category} type: {event_type!r}"
            )
        missing.extend(sorted(subtype_fields[event_type] - event.keys()))
    if missing:
        raise ValueError(
            f"resolution event for {category} missing required fields: "
            + ", ".join(sorted(set(missing)))
        )


def _apply_reviewed_resolutions(
    candidates: list[_Candidate],
    resolutions: dict[str, dict[str, object]],
) -> list[_Candidate]:
    if not isinstance(resolutions, dict):
        raise TypeError("resolutions must be a dict keyed by candidate ID")
    if any(not isinstance(identifier, str) for identifier in resolutions):
        raise TypeError("resolution IDs must be strings")

    candidates_by_id = {candidate.identifier: candidate for candidate in candidates}
    if len(candidates_by_id) != len(candidates):
        raise ValueError("duplicate candidate IDs")

    provided_ids = set(resolutions)
    known_ids = set(candidates_by_id)
    unknown_ids = sorted(provided_ids - known_ids)
    if unknown_ids:
        raise ValueError(f"unknown resolution IDs: {', '.join(unknown_ids)}")

    conflict_ids = {
        candidate.identifier
        for candidate in candidates
        if candidate.result.conflict is not None
    }
    clean_ids = sorted(provided_ids - conflict_ids)
    if clean_ids:
        raise ValueError(
            "resolution cannot overwrite clean automatic result: "
            + ", ".join(clean_ids)
        )

    resolved: dict[
        str,
        tuple[MergeResult, tuple[dict[str, object], ...] | None],
    ] = {}
    for identifier in sorted(provided_ids):
        resolution = resolutions[identifier]
        if not isinstance(resolution, dict):
            raise TypeError(f"resolution {identifier!r} must be a dict")
        is_single = set(resolution) == {"event"}
        is_keep_both = set(resolution) == {"events"}
        if not is_single and not is_keep_both:
            if "event" in resolution:
                raise ValueError(
                    f"resolution {identifier!r} must contain exactly the 'event' key"
                )
            raise ValueError(
                f"resolution {identifier!r} must contain exactly one supported key"
            )
        category = next(
            ref.category
            for ref in (
                candidates_by_id[identifier].match.base,
                candidates_by_id[identifier].match.archive,
                candidates_by_id[identifier].match.current,
            )
            if ref is not None
        )
        if is_single:
            event = resolution["event"]
            if event is not None and not isinstance(event, dict):
                raise TypeError(
                    f"resolution {identifier!r} event must be a dict or None"
                )
            if event is not None:
                _validate_resolution_event(category, event)
            resolved[identifier] = (
                MergeResult(
                    copy.deepcopy(event), "reviewed_resolution", {}, None
                ),
                None,
            )
        else:
            events = resolution["events"]
            if not isinstance(events, list) or len(events) != 2:
                raise TypeError(
                    f"resolution {identifier!r} events must be a two-event list"
                )
            if any(not isinstance(event, dict) for event in events):
                raise TypeError(
                    f"resolution {identifier!r} events must contain only dicts"
                )
            for event in events:
                _validate_resolution_event(category, event)
            resolved[identifier] = (
                MergeResult(None, "reviewed_keep_both", {}, None),
                tuple(copy.deepcopy(event) for event in events),
            )

    missing_ids = sorted(conflict_ids - provided_ids)
    if missing_ids:
        raise UnresolvedConflictError(missing_ids)

    resolved_candidates: list[_Candidate] = []
    for candidate in candidates:
        if candidate.identifier in resolved:
            result, reviewed_events = resolved[candidate.identifier]
            resolved_candidates.append(
                _Candidate(
                    candidate.identifier,
                    candidate.match,
                    result,
                    reviewed_events,
                )
            )
        else:
            resolved_candidates.append(candidate)
    return resolved_candidates


def _ordered_candidates(candidates: list[_Candidate]) -> list[_Candidate]:
    current_backbone = sorted(
        (candidate for candidate in candidates if candidate.match.current is not None),
        key=lambda candidate: candidate.match.current.index,
    )
    ordered = list(current_backbone)
    archived_only = sorted(
        (
            candidate
            for candidate in candidates
            if candidate.match.archive is not None and candidate.match.current is None
        ),
        key=lambda candidate: candidate.match.archive.index,
    )
    for candidate in archived_only:
        archive_index = candidate.match.archive.index
        prior_positions = [
            position
            for position, existing in enumerate(ordered)
            if existing.match.archive is not None
            and existing.match.archive.index < archive_index
        ]
        if prior_positions:
            insert_at = max(prior_positions) + 1
        else:
            later_positions = [
                position
                for position, existing in enumerate(ordered)
                if existing.match.archive is not None
                and existing.match.archive.index > archive_index
            ]
            insert_at = min(later_positions) if later_positions else len(ordered)
        ordered.insert(insert_at, candidate)

    unordered = [candidate for candidate in candidates if candidate not in ordered]
    unordered.sort(
        key=lambda candidate: (
            candidate.match.base.index if candidate.match.base else float("inf"),
            candidate.identifier,
        )
    )
    ordered.extend(unordered)
    return ordered


def build_ordered_candidates(
    alignment: _Alignment,
    resolutions: dict[str, dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Merge aligned events and return events plus ordered disposition records."""

    candidates = [
        _candidate_for_match(alignment, match) for match in alignment.matches
    ]
    candidates = _apply_reviewed_resolutions(candidates, resolutions)
    ordered = _ordered_candidates(candidates)
    events: list[dict[str, object]] = []
    for candidate in ordered:
        if candidate.reviewed_events is not None:
            events.extend(
                copy.deepcopy(event) for event in candidate.reviewed_events
            )
        elif candidate.result.event is not None:
            events.append(copy.deepcopy(candidate.result.event))
    records = [
        {
            "id": candidate.identifier,
            "match": candidate.match,
            "method": candidate.match.method,
            "disposition": candidate.result.disposition,
            "field_sources": dict(candidate.result.field_sources),
            "conflict": candidate.result.conflict,
        }
        for candidate in ordered
    ]
    return events, records


def merge_category(
    category: str,
    base: list[dict[str, object]],
    archive: list[dict[str, object]],
    current: list[dict[str, object]],
    resolutions: dict[str, dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    alignment = align_three_way(category, base, archive, current)
    return build_ordered_candidates(alignment, resolutions)


def extract_legacy_item(script_block: str) -> str:
    """Return the unique ITEM_* operand from a finditem command or fail."""

    without_block_comments = _BLOCK_COMMENT_RE.sub(
        lambda match: "".join(
            "\n" if character == "\n" else " " for character in match.group()
        ),
        script_block,
    )
    active_text = _LINE_COMMENT_RE.sub("", without_block_comments)
    operands = _FINDITEM_RE.findall(active_text)
    if len(operands) != 1:
        raise ValueError(
            f"expected exactly one finditem ITEM_* operand, found {len(operands)}"
        )
    return operands[0]


def adapt_item_ball(
    event: dict[str, object], script_block: str
) -> dict[str, object]:
    adapted = copy.deepcopy(event)
    adapted["script"] = "Common_EventScript_FindItem"
    adapted["trainer_sight_or_berry_tree_id"] = extract_legacy_item(script_block)
    return adapted
