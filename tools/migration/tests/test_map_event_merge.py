import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

from tools.migration.map_event_merge import (
    AmbiguousMatchError,
    EventRef,
    Match,
    UnresolvedConflictError,
    adapt_item_ball,
    align_side,
    behavior_signature,
    exact_signature,
    extract_legacy_item_and_quantity,
    extract_legacy_item,
    merge_added_event,
    merge_base_event,
    merge_category,
    resolve_reviewed_event,
    validate_resolution_consumption,
)

MIGRATION_TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MIGRATION_TOOLS))
import merge_legacy_map_events as merge_tool
sys.path.pop(0)


def object_event(x=4, y=5, script="Map_EventScript_Npc", **changes):
    event = {
        "graphics_id": "OBJ_EVENT_GFX_MAN_1",
        "x": x,
        "y": y,
        "elevation": 3,
        "movement_type": "MOVEMENT_TYPE_FACE_DOWN",
        "movement_range_x": 0,
        "movement_range_y": 0,
        "trainer_type": "TRAINER_TYPE_NONE",
        "trainer_sight_or_berry_tree_id": "0",
        "script": script,
        "flag": "0",
    }
    event.update(changes)
    return event


def clone_object_event(x=4, y=5, **changes):
    event = {
        "type": "clone",
        "graphics_id": "OBJ_EVENT_GFX_CUTTABLE_TREE_FRLG",
        "x": x,
        "y": y,
        "target_local_id": "LOCALID_ROUTE9_CUT_TREE",
        "target_map": "MAP_ROUTE9",
    }
    event.update(changes)
    return event


def warp_event(x=1, y=2, dest_map="MAP_OTHER", dest_warp_id="0"):
    return {
        "x": x,
        "y": y,
        "elevation": 0,
        "dest_map": dest_map,
        "dest_warp_id": dest_warp_id,
    }


def coord_event(x=3, y=4, script="Map_EventScript_Trigger"):
    return {
        "type": "trigger",
        "x": x,
        "y": y,
        "elevation": 0,
        "var": "VAR_TEMP_1",
        "var_value": "0",
        "script": script,
    }


def bg_script_event(x=5, y=6, script="Map_EventScript_Sign"):
    return {
        "type": "sign",
        "x": x,
        "y": y,
        "elevation": 0,
        "player_facing_dir": "BG_EVENT_PLAYER_FACING_ANY",
        "script": script,
    }


def bg_hidden_item_event(x=7, y=8, item="ITEM_POTION"):
    return {
        "type": "hidden_item",
        "x": x,
        "y": y,
        "elevation": 0,
        "item": item,
        "flag": "FLAG_HIDDEN_ITEM_MAP_POTION",
    }


def bg_secret_base_event(x=9, y=10):
    return {
        "type": "secret_base",
        "x": x,
        "y": y,
        "elevation": 0,
        "secret_base_id": "SECRET_BASE_TREE1_1",
    }


class SignatureAndAlignmentTests(unittest.TestCase):
    def test_standard_object_type_schema_transition_uses_behavior_not_exact(self):
        implicit = object_event()
        explicit = {**implicit, "type": "object"}

        self.assertNotEqual(exact_signature(implicit), exact_signature(explicit))
        self.assertEqual(
            behavior_signature("object_events", implicit),
            behavior_signature("object_events", explicit),
        )
        matches = align_side("object_events", [implicit], [explicit])
        self.assertEqual(matches[0].method, "behavior")

        moved = {**explicit, "x": 14}
        matches = align_side("object_events", [implicit], [moved])
        self.assertEqual(matches[0].method, "behavior")

    def test_standard_object_type_normalization_does_not_create_graphics_ambiguity(self):
        first = object_event(script="Map_EventScript_First")
        second = object_event(script="Map_EventScript_Second")
        side = [
            {**second, "type": "object"},
            {**first, "type": "object"},
        ]

        matches = align_side("object_events", [first, second], side)

        behavior_matches = [
            match for match in matches if match.method == "behavior"
        ]
        self.assertEqual(
            [(match.base.index, match.archive.index) for match in behavior_matches],
            [(0, 1), (1, 0)],
        )

    def test_align_side_does_not_return_weak_ownership_matches(self):
        cases = (
            (
                "object_events",
                object_event(script="Map_EventScript_Base"),
                object_event(script="Map_EventScript_Other"),
            ),
            (
                "bg_events",
                bg_script_event(script="Map_EventScript_Base"),
                bg_script_event(script="Map_EventScript_Other"),
            ),
            (
                "warp_events",
                warp_event(dest_map="MAP_BASE"),
                warp_event(dest_map="MAP_OTHER"),
            ),
        )
        for category, base, side in cases:
            with self.subTest(category=category):
                matches = align_side(category, [base], [side])
                self.assertEqual(
                    [match.method for match in matches],
                    ["unmatched_base", "unmatched_side"],
                )
                self.assertNotIn(
                    "review_ownership", [match.method for match in matches]
                )

    def test_exact_signature_ignores_schema_only_local_id(self):
        event = object_event()
        with_local_id = {**event, "local_id": "LOCALID_MAP_NPC"}
        self.assertEqual(exact_signature(event), exact_signature(with_local_id))

    def test_warp_identity_is_its_destination(self):
        warp = warp_event(dest_map="MAP_CAVE", dest_warp_id="2")
        moved = {**warp, "x": 20, "y": 21}
        other_destination = {**moved, "dest_warp_id": "3"}
        self.assertEqual(
            behavior_signature("warp_events", warp),
            behavior_signature("warp_events", moved),
        )
        self.assertNotEqual(
            behavior_signature("warp_events", warp),
            behavior_signature("warp_events", other_destination),
        )

    def test_coordinate_identity_includes_trigger_payload(self):
        trigger = coord_event()
        moved = {**trigger, "x": 30, "y": 31}
        other_script = {**moved, "script": "Map_EventScript_OtherTrigger"}
        self.assertEqual(
            behavior_signature("coord_events", trigger),
            behavior_signature("coord_events", moved),
        )
        self.assertNotEqual(
            behavior_signature("coord_events", trigger),
            behavior_signature("coord_events", other_script),
        )

    def test_background_identity_covers_scripts_and_hidden_item_payloads(self):
        sign = bg_script_event()
        hidden_item = bg_hidden_item_event()
        self.assertNotEqual(
            behavior_signature("bg_events", sign),
            behavior_signature("bg_events", {**sign, "script": "Map_EventScript_Other"}),
        )
        self.assertNotEqual(
            behavior_signature("bg_events", hidden_item),
            behavior_signature("bg_events", {**hidden_item, "item": "ITEM_ANTIDOTE"}),
        )
        secret_base = bg_secret_base_event()
        self.assertNotEqual(
            behavior_signature("bg_events", secret_base),
            behavior_signature(
                "bg_events",
                {**secret_base, "secret_base_id": "SECRET_BASE_TREE2_1"},
            ),
        )

    def test_alignment_uses_behavior_after_a_move(self):
        base = [object_event()]
        moved = [{**base[0], "x": 14, "y": 15}]
        self.assertEqual(
            align_side("object_events", base, moved),
            [
                Match(
                    base=EventRef("object_events", 0),
                    archive=EventRef("object_events", 0),
                    current=None,
                    method="behavior",
                )
            ],
        )

    def test_repeated_indistinguishable_objects_are_ambiguous(self):
        repeated = object_event()
        with self.assertRaisesRegex(
            AmbiguousMatchError,
            r"object_events.*base=\[0, 1\].*side=\[0, 1\]",
        ):
            align_side("object_events", [repeated, repeated], [repeated, repeated])

    def test_align_side_leaves_one_to_many_weak_ownership_unmatched(self):
        base = object_event(script="Map_EventScript_Base")
        archive_one = {**base, "script": "Map_EventScript_ArchiveOne"}
        archive_two = {**base, "script": "Map_EventScript_ArchiveTwo"}
        matches = align_side(
            "object_events", [base], [archive_one, archive_two]
        )
        self.assertEqual(
            [match.method for match in matches],
            ["unmatched_base", "unmatched_side", "unmatched_side"],
        )


class ObjectMergeTests(unittest.TestCase):
    def test_archive_move_and_current_schema_change_merge(self):
        base = object_event(x=4, y=5)
        archive = {**base, "x": 14, "y": 15}
        current = {**base, "local_id": "LOCALID_MAP_NPC"}
        result = merge_base_event("object_events", base, archive, current)
        self.assertEqual((result.event["x"], result.event["y"]), (14, 15))
        self.assertEqual(result.event["local_id"], "LOCALID_MAP_NPC")
        self.assertEqual(result.field_sources["x"], "archive")
        self.assertEqual(result.field_sources["local_id"], "current")
        self.assertEqual(result.disposition, "merge_nonconflicting_fields")
        self.assertIsNone(result.conflict)

    def test_archive_delete_current_unchanged_deletes(self):
        base = object_event()
        result = merge_base_event("object_events", base, None, base)
        self.assertIsNone(result.event)
        self.assertEqual(result.disposition, "archive_custom_delete")

    def test_current_only_addition_is_retained(self):
        added = object_event(x=6, y=7, script="Map_EventScript_CurrentNpc")
        result = merge_added_event("object_events", None, added)
        self.assertEqual(result.event, added)
        self.assertEqual(result.disposition, "keep_current_only_addition")

    def test_archived_only_addition_is_restored(self):
        added = object_event(x=8, y=9, script="Map_EventScript_CustomNpc")
        result = merge_added_event("object_events", added, None)
        self.assertEqual(result.event, added)
        self.assertEqual(result.disposition, "restore_archive_only_addition")

    def test_same_behavior_change_converges(self):
        base = object_event()
        moved = {**base, "x": 10}
        result = merge_base_event("object_events", base, moved, moved)
        self.assertEqual(result.event, moved)
        self.assertEqual(result.disposition, "converged_change")

    def test_same_field_conflict_is_unresolved(self):
        base = object_event()
        archive = {**base, "x": 10}
        current = {**base, "x": 12}
        result = merge_base_event("object_events", base, archive, current)
        self.assertIsNone(result.event)
        self.assertIn("x", result.conflict)

    def test_both_side_deletion_has_deletion_disposition(self):
        result = merge_base_event("object_events", object_event(), None, None)
        self.assertIsNone(result.event)
        self.assertEqual(result.disposition, "converged_delete")

    def test_current_schema_absence_removes_stale_archived_local_id(self):
        current = object_event(script="Map_EventScript_Added")
        archive = {**current, "local_id": "LOCALID_STALE"}
        result = merge_added_event("object_events", archive, current)
        self.assertNotIn("local_id", result.event)

    def test_current_schema_value_replaces_stale_archived_local_id(self):
        current = object_event(
            script="Map_EventScript_Added", local_id="LOCALID_CURRENT"
        )
        archive = {**current, "local_id": "LOCALID_STALE"}
        result = merge_added_event("object_events", archive, current)
        self.assertEqual(result.event["local_id"], "LOCALID_CURRENT")

    def test_absent_schema_field_has_no_source_on_converged_addition(self):
        added = object_event(script="Map_EventScript_Added")
        result = merge_added_event("object_events", added, added)
        self.assertNotIn("local_id", result.field_sources)


class CategoryMergeAndOrderingTests(unittest.TestCase):
    def assert_unresolved(self, callback):
        with self.assertRaises(UnresolvedConflictError):
            callback()

    def test_both_changed_object_behavior_retains_base_ownership_as_conflict(self):
        base = object_event(script="Map_EventScript_Base")
        archive = {**base, "script": "Map_EventScript_Archive"}
        current = {**base, "script": "Map_EventScript_Current"}
        self.assert_unresolved(
            lambda: merge_category(
                "object_events", [base], [archive], [current], {}
            )
        )

    def test_both_changed_object_movement_retains_base_ownership_as_conflict(self):
        base = object_event(movement_type="MOVEMENT_TYPE_FACE_DOWN")
        archive = {**base, "movement_type": "MOVEMENT_TYPE_FACE_LEFT"}
        current = {**base, "movement_type": "MOVEMENT_TYPE_FACE_RIGHT"}
        self.assert_unresolved(
            lambda: merge_category(
                "object_events", [base], [archive], [current], {}
            )
        )

    def test_weak_object_identity_never_authorizes_synthetic_hybrid(self):
        base = object_event(script="Map_EventScript_Base")
        unrelated_archive = {**base, "script": "Map_EventScript_Replacement"}
        current_edit = {**base, "x": 12}
        self.assert_unresolved(
            lambda: merge_category(
                "object_events",
                [base],
                [unrelated_archive],
                [current_edit],
                {},
            )
        )

    def test_three_way_one_to_many_weak_ownership_remains_ambiguous(self):
        base = object_event(script="Map_EventScript_Base")
        archive_one = {**base, "script": "Map_EventScript_ArchiveOne"}
        archive_two = {**base, "script": "Map_EventScript_ArchiveTwo"}

        with self.assertRaises(AmbiguousMatchError):
            merge_category(
                "object_events",
                [base],
                [archive_one, archive_two],
                [],
                {},
            )

    def test_reviewed_weak_object_candidate_can_use_valid_replacement(self):
        base = object_event(script="Map_EventScript_Base")
        archive = {**base, "script": "Map_EventScript_Replacement"}
        current = {**base, "x": 12}
        events, records = merge_category(
            "object_events",
            [base],
            [archive],
            [current],
            {"object_events:base:0": {"event": archive}},
        )
        self.assertEqual(events, [archive])
        self.assertEqual(records[0]["disposition"], "reviewed_resolution")

    def test_divergent_object_graphics_are_review_replacements(self):
        base = object_event(
            script="Map_EventScript_Base",
            graphics_id="OBJ_EVENT_GFX_MAN_1",
        )
        archive = {
            **base,
            "script": "Map_EventScript_Archive",
            "graphics_id": "OBJ_EVENT_GFX_WOMAN_1",
        }
        current = {
            **base,
            "script": "Map_EventScript_Current",
            "graphics_id": "OBJ_EVENT_GFX_BOY_1",
        }
        self.assert_unresolved(
            lambda: merge_category(
                "object_events", [base], [archive], [current], {}
            )
        )

    def test_distinct_replacements_can_be_reviewed_to_keep_both_losslessly(self):
        base = object_event(
            script="Map_EventScript_Base",
            graphics_id="OBJ_EVENT_GFX_MAN_1",
        )
        archive = {
            **base,
            "script": "Map_EventScript_Archive",
            "graphics_id": "OBJ_EVENT_GFX_WOMAN_1",
            "metadata": {"side": ["archive"]},
        }
        current = {
            **base,
            "script": "Map_EventScript_Current",
            "graphics_id": "OBJ_EVENT_GFX_BOY_1",
            "metadata": {"side": ["current"]},
        }
        events, records = merge_category(
            "object_events",
            [base],
            [archive],
            [current],
            {
                "object_events:addition:archive:0:current:0": {
                    "events": [archive, current]
                }
            },
        )
        self.assertEqual(events, [archive, current])
        self.assertIn("reviewed_keep_both", [record["disposition"] for record in records])
        events[0]["metadata"]["side"].append("mutated")
        events[1]["metadata"]["side"].append("mutated")
        self.assertEqual(archive["metadata"], {"side": ["archive"]})
        self.assertEqual(current["metadata"], {"side": ["current"]})

    def test_keep_both_copies_sibling_events_independently(self):
        base = object_event(
            script="Map_EventScript_Base",
            graphics_id="OBJ_EVENT_GFX_MAN_1",
        )
        shared_metadata = {"tags": ["shared"]}
        archive = {
            **base,
            "script": "Map_EventScript_Archive",
            "graphics_id": "OBJ_EVENT_GFX_WOMAN_1",
            "metadata": shared_metadata,
        }
        current = {
            **base,
            "script": "Map_EventScript_Current",
            "graphics_id": "OBJ_EVENT_GFX_BOY_1",
            "metadata": shared_metadata,
        }

        events, _ = merge_category(
            "object_events",
            [base],
            [archive],
            [current],
            {
                "object_events:addition:archive:0:current:0": {
                    "events": [archive, current]
                }
            },
        )

        events[0]["metadata"]["tags"].append("archive-only")
        self.assertEqual(events[1]["metadata"], {"tags": ["shared"]})
        self.assertEqual(shared_metadata, {"tags": ["shared"]})

    def test_distinct_replacements_can_choose_either_side_or_delete(self):
        base = object_event(
            script="Map_EventScript_Base",
            graphics_id="OBJ_EVENT_GFX_MAN_1",
        )
        archive = {
            **base,
            "script": "Map_EventScript_Archive",
            "graphics_id": "OBJ_EVENT_GFX_WOMAN_1",
        }
        current = {
            **base,
            "script": "Map_EventScript_Current",
            "graphics_id": "OBJ_EVENT_GFX_BOY_1",
        }
        resolution_id = "object_events:addition:archive:0:current:0"
        for name, event, expected in (
            ("archive", archive, [archive]),
            ("current", current, [current]),
            ("delete", None, []),
        ):
            with self.subTest(name=name):
                events, _ = merge_category(
                    "object_events",
                    [base],
                    [archive],
                    [current],
                    {resolution_id: {"event": event}},
                )
                self.assertEqual(events, expected)

    def test_both_changed_warp_destination_is_unresolved(self):
        base = warp_event(dest_map="MAP_BASE")
        archive = {**base, "dest_map": "MAP_ARCHIVE"}
        current = {**base, "dest_map": "MAP_CURRENT"}
        self.assert_unresolved(
            lambda: merge_category("warp_events", [base], [archive], [current], {})
        )

    def test_divergent_warp_placement_is_a_review_replacement(self):
        base = warp_event(x=1, dest_map="MAP_BASE")
        archive = {**base, "x": 2, "dest_map": "MAP_ARCHIVE"}
        current = {**base, "x": 3, "dest_map": "MAP_CURRENT"}
        self.assert_unresolved(
            lambda: merge_category("warp_events", [base], [archive], [current], {})
        )

    def test_both_changed_coordinate_script_is_unresolved(self):
        base = coord_event(script="Map_EventScript_Base")
        archive = {**base, "script": "Map_EventScript_Archive"}
        current = {**base, "script": "Map_EventScript_Current"}
        self.assert_unresolved(
            lambda: merge_category("coord_events", [base], [archive], [current], {})
        )

    def test_both_changed_coordinate_payload_is_unresolved(self):
        base = coord_event()
        archive = {**base, "var_value": "1"}
        current = {**base, "var_value": "2"}
        self.assert_unresolved(
            lambda: merge_category("coord_events", [base], [archive], [current], {})
        )

    def test_both_changed_background_script_is_unresolved(self):
        base = bg_script_event(script="Map_EventScript_Base")
        archive = {**base, "script": "Map_EventScript_Archive"}
        current = {**base, "script": "Map_EventScript_Current"}
        self.assert_unresolved(
            lambda: merge_category("bg_events", [base], [archive], [current], {})
        )

    def test_divergent_background_types_are_review_replacements(self):
        base = bg_script_event(script="Map_EventScript_Base")
        archive = bg_hidden_item_event(x=base["x"], y=base["y"])
        current = bg_secret_base_event(x=base["x"], y=base["y"])
        self.assert_unresolved(
            lambda: merge_category("bg_events", [base], [archive], [current], {})
        )

    def test_weak_background_type_never_authorizes_synthetic_hybrid(self):
        base = bg_script_event(script="Map_EventScript_Base")
        unrelated_archive = {**base, "script": "Map_EventScript_Replacement"}
        current_edit = {**base, "x": 12}
        self.assert_unresolved(
            lambda: merge_category(
                "bg_events", [base], [unrelated_archive], [current_edit], {}
            )
        )

    def test_secret_base_type_alone_never_authorizes_synthetic_hybrid(self):
        base = bg_secret_base_event()
        unrelated_archive = {
            **base,
            "secret_base_id": "SECRET_BASE_TREE2_1",
        }
        current_edit = {**base, "x": 12}
        self.assert_unresolved(
            lambda: merge_category(
                "bg_events", [base], [unrelated_archive], [current_edit], {}
            )
        )

    def test_merge_category_never_filters_same_field_conflict(self):
        base = object_event(x=4)
        archive = {**base, "x": 10}
        current = {**base, "x": 12}
        self.assert_unresolved(
            lambda: merge_category(
                "object_events", [base], [archive], [current], {}
            )
        )

    def test_colliding_additions_are_unresolved(self):
        archive = object_event(script="Map_EventScript_ArchiveAddition")
        current = object_event(script="Map_EventScript_CurrentAddition")
        self.assert_unresolved(
            lambda: merge_category(
                "object_events", [], [archive], [current], {}
            )
        )

    def test_exact_resolution_can_resolve_only_the_matching_conflict(self):
        base = object_event(x=4)
        archive = {**base, "x": 10}
        current = {**base, "x": 12}
        events, records = merge_category(
            "object_events",
            [base],
            [archive],
            [current],
            {"object_events:base:0": {"event": archive}},
        )
        self.assertEqual(events, [archive])
        self.assertEqual(records[0]["disposition"], "reviewed_resolution")

    def test_resolution_cannot_overwrite_clean_automatic_result(self):
        event = object_event()
        with self.assertRaisesRegex(ValueError, "clean automatic result"):
            merge_category(
                "object_events",
                [event],
                [event],
                [event],
                {"object_events:base:0": {"event": {**event, "x": 99}}},
            )

    def test_unknown_resolution_is_rejected(self):
        event = object_event()
        with self.assertRaisesRegex(ValueError, "unknown.*object_events:base:99"):
            merge_category(
                "object_events",
                [event],
                [event],
                [event],
                {"object_events:base:99": {"event": event}},
            )

    def test_malformed_resolution_is_rejected(self):
        base = object_event(x=4)
        archive = {**base, "x": 10}
        current = {**base, "x": 12}
        with self.assertRaisesRegex(TypeError, "event must be a dict or None"):
            merge_category(
                "object_events",
                [base],
                [archive],
                [current],
                {"object_events:base:0": {"event": "not an event"}},
            )

    def test_resolution_requires_the_exact_supported_shape(self):
        base = object_event(x=4)
        archive = {**base, "x": 10}
        current = {**base, "x": 12}
        with self.assertRaisesRegex(ValueError, "exactly the 'event' key"):
            merge_category(
                "object_events",
                [base],
                [archive],
                [current],
                {
                    "object_events:base:0": {
                        "event": archive,
                        "disposition": "unsupported",
                    }
                },
            )

    def test_duplicate_resolution_sequence_is_rejected(self):
        event = object_event()
        duplicate_entries = [
            ("object_events:base:0", {"event": event}),
            ("object_events:base:0", {"event": event}),
        ]
        with self.assertRaisesRegex(TypeError, "dict keyed by candidate ID"):
            merge_category(
                "object_events",
                [event],
                [event],
                [event],
                duplicate_entries,  # type: ignore[arg-type]
            )

    def test_resolution_event_is_deep_copied(self):
        base = object_event(x=4)
        archive = {**base, "x": 10, "metadata": {"tags": ["archive"]}}
        current = {**base, "x": 12, "metadata": {"tags": ["current"]}}
        resolution_event = copy.deepcopy(archive)
        events, _ = merge_category(
            "object_events",
            [base],
            [archive],
            [current],
            {"object_events:base:0": {"event": resolution_event}},
        )
        events[0]["metadata"]["tags"].append("mutated")
        self.assertEqual(resolution_event["metadata"], {"tags": ["archive"]})

    def test_malformed_resolution_event_is_rejected_for_each_category(self):
        cases = {
            "object_events": object_event(),
            "warp_events": warp_event(),
            "coord_events": coord_event(),
            "bg_events": bg_script_event(),
        }
        for category, base in cases.items():
            with self.subTest(category=category):
                archive = {**base, "x": 10}
                current = {**base, "x": 12}
                with self.assertRaisesRegex(ValueError, "missing required fields"):
                    merge_category(
                        category,
                        [base],
                        [archive],
                        [current],
                        {f"{category}:base:0": {"event": {"garbage": 1}}},
                    )

    def test_valid_clone_object_resolution_is_accepted(self):
        base = object_event(x=4)
        archive = {**base, "x": 10}
        current = {**base, "x": 12}
        clone = clone_object_event(extra_schema="allowed")
        events, _ = merge_category(
            "object_events",
            [base],
            [archive],
            [current],
            {"object_events:base:0": {"event": clone}},
        )
        self.assertEqual(events, [clone])

    def test_malformed_clone_and_standard_cross_shapes_are_rejected(self):
        base = object_event(x=4)
        archive = {**base, "x": 10}
        current = {**base, "x": 12}
        malformed_clone = clone_object_event()
        del malformed_clone["target_local_id"]
        malformed_standard = {
            **clone_object_event(),
            "type": "object",
        }
        for name, replacement in (
            ("clone", malformed_clone),
            ("standard", malformed_standard),
        ):
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, "missing required fields"):
                    merge_category(
                        "object_events",
                        [base],
                        [archive],
                        [current],
                        {"object_events:base:0": {"event": replacement}},
                    )

    def test_resolution_event_allows_additional_schema_fields(self):
        base = object_event(x=4)
        archive = {**base, "x": 10, "future_schema": "preserved"}
        current = {**base, "x": 12}
        events, _ = merge_category(
            "object_events",
            [base],
            [archive],
            [current],
            {"object_events:base:0": {"event": archive}},
        )
        self.assertEqual(events, [archive])

    def test_resolution_event_rejects_non_string_event_type(self):
        base = bg_script_event()
        archive = {**base, "x": 10}
        current = {**base, "x": 12}
        malformed = {**archive, "type": []}
        with self.assertRaisesRegex(ValueError, "unsupported bg_events type"):
            merge_category(
                "bg_events",
                [base],
                [archive],
                [current],
                {"bg_events:base:0": {"event": malformed}},
            )

    def test_archived_addition_stays_between_archived_neighbors(self):
        first = object_event(script="Map_EventScript_First")
        second = object_event(x=8, script="Map_EventScript_Second")
        archived_addition = object_event(x=6, script="Map_EventScript_Archived")
        events, records = merge_category(
            "object_events",
            [first, second],
            [first, archived_addition, second],
            [first, second],
            {},
        )
        self.assertEqual(
            [event["script"] for event in events],
            [
                "Map_EventScript_First",
                "Map_EventScript_Archived",
                "Map_EventScript_Second",
            ],
        )
        self.assertEqual(
            [record["disposition"] for record in records],
            ["unchanged", "restore_archive_only_addition", "unchanged"],
        )

    def test_current_only_additions_keep_relative_order(self):
        first = object_event(script="Map_EventScript_First")
        second = object_event(x=8, script="Map_EventScript_Second")
        archived_addition = object_event(
            x=6,
            script="Map_EventScript_Archived",
            graphics_id="OBJ_EVENT_GFX_FAT_MAN",
        )
        current_one = object_event(
            x=10,
            script="Map_EventScript_CurrentOne",
            graphics_id="OBJ_EVENT_GFX_RICH_BOY",
        )
        current_two = object_event(
            x=11,
            script="Map_EventScript_CurrentTwo",
            graphics_id="OBJ_EVENT_GFX_LITTLE_GIRL",
        )
        events, _ = merge_category(
            "object_events",
            [first, second],
            [first, archived_addition, second],
            [first, current_one, current_two, second],
            {},
        )
        scripts = [event["script"] for event in events]
        self.assertLess(
            scripts.index("Map_EventScript_CurrentOne"),
            scripts.index("Map_EventScript_CurrentTwo"),
        )
        self.assertLess(
            scripts.index("Map_EventScript_First"),
            scripts.index("Map_EventScript_Archived"),
        )
        self.assertLess(
            scripts.index("Map_EventScript_Archived"),
            scripts.index("Map_EventScript_Second"),
        )

    def test_multiple_archived_insertions_use_current_deletion_as_order_anchor(self):
        first = object_event(script="Map_EventScript_First")
        deleted = object_event(
            x=7,
            script="Map_EventScript_Deleted",
            graphics_id="OBJ_EVENT_GFX_WOMAN_1",
        )
        last = object_event(
            x=12,
            script="Map_EventScript_Last",
            graphics_id="OBJ_EVENT_GFX_BOY_1",
        )
        archived_one = object_event(
            x=8,
            script="Map_EventScript_ArchivedOne",
            graphics_id="OBJ_EVENT_GFX_FAT_MAN",
        )
        archived_two = object_event(
            x=9,
            script="Map_EventScript_ArchivedTwo",
            graphics_id="OBJ_EVENT_GFX_LITTLE_GIRL",
        )
        current_only = object_event(
            x=10,
            script="Map_EventScript_CurrentOnly",
            graphics_id="OBJ_EVENT_GFX_RICH_BOY",
        )
        events, records = merge_category(
            "object_events",
            [first, deleted, last],
            [first, deleted, archived_one, archived_two, last],
            [first, current_only, last],
            {},
        )
        self.assertEqual(
            [event["script"] for event in events],
            [
                "Map_EventScript_First",
                "Map_EventScript_ArchivedOne",
                "Map_EventScript_ArchivedTwo",
                "Map_EventScript_CurrentOnly",
                "Map_EventScript_Last",
            ],
        )
        self.assertIn(
            "keep_current_delete",
            [record["disposition"] for record in records],
        )

    def test_converged_delete_with_archive_only_addition_stays_independent(self):
        base = object_event(script="Map_EventScript_Deleted")
        added = object_event(
            script="Map_EventScript_ArchiveOnly",
            graphics_id="OBJ_EVENT_GFX_WOMAN_1",
        )
        events, records = merge_category(
            "object_events", [base], [added], [], {}
        )
        self.assertEqual(events, [added])
        self.assertEqual(
            {record["disposition"] for record in records},
            {"converged_delete", "restore_archive_only_addition"},
        )

    def test_converged_delete_with_current_only_addition_stays_independent(self):
        base = object_event(script="Map_EventScript_Deleted")
        added = object_event(
            script="Map_EventScript_CurrentOnly",
            graphics_id="OBJ_EVENT_GFX_WOMAN_1",
        )
        events, records = merge_category(
            "object_events", [base], [], [added], {}
        )
        self.assertEqual(events, [added])
        self.assertEqual(
            {record["disposition"] for record in records},
            {"converged_delete", "keep_current_only_addition"},
        )

    def test_converged_delete_with_identical_both_side_addition_deduplicates(self):
        base = object_event(script="Map_EventScript_Deleted")
        added = object_event(
            script="Map_EventScript_ConvergedAddition",
            graphics_id="OBJ_EVENT_GFX_WOMAN_1",
        )
        events, records = merge_category(
            "object_events", [base], [added], [added], {}
        )
        self.assertEqual(events, [added])
        self.assertEqual(
            {record["disposition"] for record in records},
            {"converged_delete", "converged_addition"},
        )

    def test_multiple_converged_deletions_allow_independent_side_addition(self):
        first = object_event(script="Map_EventScript_DeletedOne")
        second = object_event(
            script="Map_EventScript_DeletedTwo",
            graphics_id="OBJ_EVENT_GFX_BOY_1",
        )
        added = object_event(
            script="Map_EventScript_ArchiveOnly",
            graphics_id="OBJ_EVENT_GFX_WOMAN_1",
        )
        events, records = merge_category(
            "object_events", [first, second], [added], [], {}
        )
        self.assertEqual(events, [added])
        self.assertEqual(
            [record["disposition"] for record in records].count("converged_delete"),
            2,
        )

    def test_three_way_ambiguity_reports_archive_and_current_indices_separately(self):
        first = object_event(
            script="Map_EventScript_BaseOne",
            graphics_id="OBJ_EVENT_GFX_MAN_1",
        )
        second = object_event(
            script="Map_EventScript_BaseTwo",
            graphics_id="OBJ_EVENT_GFX_BOY_1",
        )
        archive = [
            object_event(
                script="Map_EventScript_ArchiveOne",
                graphics_id="OBJ_EVENT_GFX_WOMAN_1",
            ),
            object_event(
                script="Map_EventScript_ArchiveTwo",
                graphics_id="OBJ_EVENT_GFX_FAT_MAN",
            ),
        ]
        current = [
            object_event(
                script="Map_EventScript_CurrentOne",
                graphics_id="OBJ_EVENT_GFX_RICH_BOY",
            ),
            object_event(
                script="Map_EventScript_CurrentTwo",
                graphics_id="OBJ_EVENT_GFX_LITTLE_GIRL",
            ),
        ]
        with self.assertRaisesRegex(
            AmbiguousMatchError,
            r"base=\[0, 1\].*archive=\[0, 1\].*current=\[0, 1\]",
        ):
            merge_category("object_events", [first, second], archive, current, {})

    def test_base_to_archive_ambiguity_preserves_archive_provenance(self):
        repeated = object_event()

        with self.assertRaisesRegex(
            AmbiguousMatchError,
            r"base=\[0, 1\].*archive=\[0, 1\].*current=\[\]",
        ):
            merge_category(
                "object_events",
                [repeated, repeated],
                [repeated, repeated],
                [],
                {},
            )

    def test_base_to_current_ambiguity_preserves_current_provenance(self):
        repeated = object_event()

        with self.assertRaisesRegex(
            AmbiguousMatchError,
            r"base=\[0, 1\].*archive=\[\].*current=\[0, 1\]",
        ):
            merge_category(
                "object_events",
                [repeated, repeated],
                [],
                [repeated, repeated],
                {},
            )

    def test_addition_ambiguity_reports_original_archive_and_current_indices(self):
        matched = object_event(script="Map_EventScript_Matched")
        repeated_addition = object_event(script="Map_EventScript_Added")
        archive = [matched, repeated_addition, repeated_addition]
        current = [matched, repeated_addition, repeated_addition]

        with self.assertRaisesRegex(
            AmbiguousMatchError,
            r"base=\[\].*archive=\[1, 2\].*current=\[1, 2\]",
        ):
            merge_category(
                "object_events",
                [matched],
                archive,
                current,
                {},
            )

    def test_merge_category_deep_copies_nested_event_values(self):
        event = object_event(metadata={"tags": ["original"]})
        events, _ = merge_category(
            "object_events", [event], [event], [event], {}
        )
        events[0]["metadata"]["tags"].append("mutated")
        self.assertEqual(event["metadata"], {"tags": ["original"]})


class ItemBallAdapterTests(unittest.TestCase):
    def test_adapts_legacy_item_ball_without_mutating_placement_or_flag(self):
        original = object_event(
            x=13,
            y=17,
            graphics_id="OBJ_EVENT_GFX_ITEM_BALL",
            script="Route119_EventScript_ItemElixir",
            flag="FLAG_ITEM_ROUTE_119_ELIXIR",
        )
        snapshot = copy.deepcopy(original)
        adapted = adapt_item_ball(
            original,
            "Route119_EventScript_ItemElixir::\n    finditem ITEM_ELIXIR\n    end\n",
        )
        self.assertEqual(adapted["trainer_sight_or_berry_tree_id"], "ITEM_ELIXIR")
        self.assertEqual(adapted["script"], "Common_EventScript_FindItem")
        self.assertEqual(adapted["movement_range_x"], 1)
        self.assertEqual(adapted["flag"], "FLAG_ITEM_ROUTE_119_ELIXIR")
        self.assertEqual((adapted["x"], adapted["y"], adapted["elevation"]), (13, 17, 3))
        self.assertEqual(original, snapshot)

    def test_extract_legacy_item_fails_when_no_finditem_operand_exists(self):
        with self.assertRaises(ValueError):
            extract_legacy_item("Map_EventScript_NoItem::\n    end\n")

    def test_extract_legacy_item_fails_when_multiple_operands_exist(self):
        with self.assertRaises(ValueError):
            extract_legacy_item("    finditem ITEM_POTION\n    finditem ITEM_ELIXIR\n")

    def test_extract_legacy_item_ignores_comments_and_non_command_text(self):
        block = """
// finditem ITEM_POTION
@ finditem ITEM_MAX_REVIVE
/*
    finditem ITEM_ANTIDOTE
*/
    .string "finditem ITEM_REVIVE"
    finditem ITEM_ELIXIR // active command
"""
        self.assertEqual(extract_legacy_item(block), "ITEM_ELIXIR")

    def test_extract_legacy_item_fails_when_operand_is_on_another_line(self):
        with self.assertRaises(ValueError):
            extract_legacy_item("    finditem\n    ITEM_ELIXIR\n")

    def test_extract_legacy_item_fails_when_operands_only_appear_in_comments(self):
        with self.assertRaises(ValueError):
            extract_legacy_item(
                "// finditem ITEM_POTION\n/* finditem ITEM_ELIXIR */\n"
            )

    def test_adapts_explicit_item_quantity(self):
        adapted = adapt_item_ball(
            object_event(movement_range_x=0),
            "Map_EventScript_Item::\n    finditem ITEM_GREAT_BALL, 5\n",
        )
        self.assertEqual(
            (adapted["trainer_sight_or_berry_tree_id"], adapted["movement_range_x"]),
            ("ITEM_GREAT_BALL", 5),
        )

    def test_accepts_maximum_packed_item_quantity(self):
        adapted = adapt_item_ball(
            object_event(movement_range_x=0),
            "Map_EventScript_Item::\n    finditem ITEM_GREAT_BALL, 15\n",
        )
        self.assertEqual(adapted["movement_range_x"], 15)

    def test_rejects_item_quantities_that_overflow_packed_field(self):
        for quantity in (16, 999999999999999999999999):
            with self.subTest(quantity=quantity), self.assertRaisesRegex(
                ValueError, "1..15"
            ):
                extract_legacy_item_and_quantity(
                    f"finditem ITEM_GREAT_BALL, {quantity}\n"
                )

    def test_candidate_bounds_validate_item_quantity_without_walking_radius(self):
        item = object_event(
            x=9,
            script="Common_EventScript_FindItem",
            movement_range_x=15,
        )
        self.assertIsNone(merge_tool.candidate_event_bounds_error(item, 10, 10))
        item["movement_range_x"] = 16
        self.assertEqual(
            merge_tool.candidate_event_bounds_error(item, 10, 10),
            "item quantity movement_range_x must be an integer in 0..15, got 16",
        )

    def test_candidate_bounds_require_packed_object_movement_ranges(self):
        event = object_event(movement_range_x=15, movement_range_y=15)
        self.assertIsNone(merge_tool.candidate_event_bounds_error(event, 10, 10))
        for field, value in (
            ("movement_range_x", 16),
            ("movement_range_y", 16),
            ("movement_range_x", -1),
            ("movement_range_y", True),
            ("movement_range_x", "1"),
        ):
            with self.subTest(field=field, value=value):
                invalid = object_event(movement_range_x=0, movement_range_y=0)
                invalid[field] = value
                self.assertEqual(
                    merge_tool.candidate_event_bounds_error(invalid, 10, 10),
                    f"{field} must be an integer in 0..15, got {value!r}",
                )

    def test_extract_item_quantity_rejects_invalid_nonpositive_or_extra_operands(self):
        for command in (
            "finditem ITEM_POTION, 0\n",
            "finditem ITEM_POTION, -1\n",
            "finditem ITEM_POTION, nope\n",
            "finditem ITEM_POTION, 2, 3\n",
        ):
            with self.subTest(command=command), self.assertRaises(ValueError):
                extract_legacy_item_and_quantity(command)


class ReviewedResolutionConstructionTests(unittest.TestCase):
    def test_every_unresolved_id_requires_exactly_one_resolution(self):
        with self.assertRaises(UnresolvedConflictError):
            validate_resolution_consumption({"one", "two"}, {"one": {}})
        with self.assertRaises(ValueError):
            validate_resolution_consumption({"one"}, {"one": {}, "stale": {}})

    def test_merge_fields_requires_exact_coverage_and_valid_result(self):
        archive = object_event(x=8, local_id="1")
        current = object_event(x=4, local_id="2")
        entry = {"decision": "merge_fields", "field_sources": {"x": "archive", "local_id": "current"}}
        merged = resolve_reviewed_event("object_events", archive, current, entry)
        self.assertEqual((merged[0]["x"], merged[0]["local_id"]), (8, "2"))
        with self.assertRaises(ValueError):
            resolve_reviewed_event(
                "object_events", archive, current,
                {"decision": "merge_fields", "field_sources": {"x": "archive"}},
            )

    def test_keep_both_copies_in_archive_then_current_order(self):
        archive = object_event(script="Archive")
        current = object_event(script="Current")
        events = resolve_reviewed_event(
            "object_events", archive, current,
            {"decision": "keep_both", "field_sources": {}},
        )
        self.assertEqual([event["script"] for event in events], ["Archive", "Current"])
        events[0]["script"] = "mutated"
        self.assertEqual(archive["script"], "Archive")

    def test_use_current_and_delete_are_exact(self):
        current = object_event(script="Current")
        self.assertEqual(
            resolve_reviewed_event(
                "object_events", None, current,
                {"decision": "use_current", "field_sources": {}},
            ),
            [current],
        )
        self.assertEqual(
            resolve_reviewed_event(
                "object_events", None, current,
                {"decision": "delete", "field_sources": {}},
            ),
            [],
        )

    def test_invalid_or_stale_decision_fails(self):
        with self.assertRaises(ValueError):
            resolve_reviewed_event(
                "object_events", object_event(), object_event(),
                {"decision": "current_equivalent", "field_sources": {}},
            )


class DependencyCurrentEquivalentTests(unittest.TestCase):
    def setUp(self):
        self.current_block = "Current_EventScript_Renamed::\n\tend\n"
        self.current_hash = hashlib.sha256(self.current_block.encode()).hexdigest()
        self.source = {
            "label": "Legacy_EventScript_Source",
            "classification": "archived-only",
            "normalized_blocks": {"base": None, "legacy": "Legacy::\n\tend\n", "current": None},
            "normalized_block_sha256": {
                "base": None,
                "legacy": hashlib.sha256(b"Legacy::\n\tend\n").hexdigest(),
                "current": None,
            },
            "owners": {
                "base": None,
                "legacy": "data/maps/TestMap/scripts.inc",
                "current": None,
            },
            "references": [{"source": "legacy", "map": "TestMap"}],
            "block_labels": {"base": [], "legacy": ["Legacy_EventScript_Source"], "current": []},
            "item_equivalence": [],
        }
        self.target = {
            "label": "Current_EventScript_Renamed",
            "classification": "current-only",
            "normalized_blocks": {"base": None, "legacy": None, "current": self.current_block},
            "normalized_block_sha256": {
                "base": None,
                "legacy": None,
                "current": self.current_hash,
            },
            "owners": {
                "base": None,
                "legacy": None,
                "current": "data/maps/TestMap/scripts.inc",
            },
            "references": [{"source": "current", "map": "TestMap"}],
            "block_labels": {"base": [], "legacy": [], "current": ["Current_EventScript_Renamed"]},
            "item_equivalence": [],
        }
        self.issue = {
            "id": "dependency:Legacy_EventScript_Source",
            "issue_type": "dependency",
            "map": "TestMap",
            "category": "dependency",
            "base_index": None,
            "archive_index": 0,
            "current_index": None,
            "evidence": self.source,
        }
        self.entry = {
            "id": self.issue["id"],
            "map": "TestMap",
            "category": "dependency",
            "base_index": None,
            "archive_index": 0,
            "current_index": None,
            "decision": "current_equivalent",
            "field_sources": {},
            "evidence": "Pinned renamed current behavior is equivalent.",
            "current_label": self.target["label"],
            "current_sha256": self.current_hash,
        }

    def validate(self, entry=None, dependencies=None):
        return merge_tool.validate_resolution_entries(
            [entry or self.entry],
            {self.issue["id"]: self.issue},
            dependencies=dependencies or {
                self.source["label"]: self.source,
                self.target["label"]: self.target,
            },
        )

    def test_accepts_exact_renamed_current_label_and_hash(self):
        self.assertEqual(self.validate(), [self.entry])

    def test_rejects_tampered_renamed_current_hash(self):
        entry = copy.deepcopy(self.entry)
        entry["current_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "hash differs"):
            self.validate(entry)

    def test_rejects_nonexistent_renamed_current_label(self):
        entry = copy.deepcopy(self.entry)
        entry["current_label"] = "Missing_EventScript"
        with self.assertRaisesRegex(ValueError, "target does not exist"):
            self.validate(entry)

    def test_report_record_proves_both_sides_of_renamed_equivalence(self):
        record = merge_tool.dependency_report_record(
            self.entry,
            self.source,
            {
                self.source["label"]: self.source,
                self.target["label"]: self.target,
            },
        )
        self.assertEqual(record["label"], self.source["label"])
        self.assertEqual(record["source_owner"], "data/maps/TestMap/scripts.inc")
        self.assertEqual(
            record["source_sha256"],
            self.source["normalized_block_sha256"]["legacy"],
        )
        self.assertEqual(record["disposition"], "current_equivalent")
        self.assertEqual(record["current_label"], self.target["label"])
        self.assertEqual(record["target_owner"], "data/maps/TestMap/scripts.inc")
        self.assertEqual(record["current_sha256"], self.current_hash)
        self.assertEqual(record["target_sha256"], self.current_hash)
        self.assertEqual(record["resolution_evidence"], self.entry["evidence"])


class CandidateBundlePublicationTests(unittest.TestCase):
    NEW_FILES = {
        "data/maps/NewMap/map.json": json.dumps(
            {
                "layout": "LAYOUT_NEW_MAP",
                "object_events": [],
                "warp_events": [],
                "coord_events": [],
                "bg_events": [],
            },
            sort_keys=True,
        ).encode(),
    }
    NEW_REPORT = json.dumps(
        {
            "mode": "candidate-only",
            "candidate_map_count": 1,
            "candidate_maps": ["NewMap"],
            "candidate_sha256": {
                "data/maps/NewMap/map.json": hashlib.sha256(
                    NEW_FILES["data/maps/NewMap/map.json"]
                ).hexdigest()
            },
        },
        sort_keys=True,
    ).encode()

    def write_candidate(self, root, contents=None):
        if contents is None:
            contents = json.dumps(
                {
                    "layout": "LAYOUT_OLD_MAP",
                    "object_events": [],
                    "warp_events": [],
                    "coord_events": [],
                    "bg_events": [],
                },
                sort_keys=True,
            ).encode()
        path = root / "candidates" / "data" / "maps" / "OldMap" / "map.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)

    def snapshot(self, root):
        candidate = root / "candidates"
        report = root / "report.json"
        files = (
            {
                path.relative_to(candidate).as_posix(): path.read_bytes()
                for path in candidate.rglob("*")
                if path.is_file()
            }
            if candidate.exists()
            else None
        )
        return files, report.read_bytes() if report.exists() else None

    def assert_no_transaction_debris(self, root):
        self.assertFalse(
            [
                path.name
                for path in root.iterdir()
                if ".stage." in path.name or ".backup." in path.name
            ]
        )

    def test_success_replaces_complete_tree_and_removes_stale_managed_map(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_candidate(root)
            (root / "report.json").write_bytes(b"old report")
            merge_tool.publish_candidate_bundle(
                root / "candidates", self.NEW_FILES, root / "report.json", self.NEW_REPORT
            )
            self.assertEqual(self.snapshot(root), (self.NEW_FILES, self.NEW_REPORT))
            self.assert_no_transaction_debris(root)

    def test_success_handles_absent_prior_tree_and_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            merge_tool.publish_candidate_bundle(
                root / "candidates", self.NEW_FILES, root / "report.json", self.NEW_REPORT
            )
            self.assertEqual(self.snapshot(root), (self.NEW_FILES, self.NEW_REPORT))
            self.assert_no_transaction_debris(root)

    def test_fault_matrix_restores_exact_prior_state(self):
        phases = (
            "after_staging",
            "before_candidate_install",
            "after_candidate_install",
            "before_report_install",
            "after_report_install",
        )
        for candidate_exists in (False, True):
            for report_exists in (False, True):
                for phase in phases:
                    with self.subTest(
                        candidate_exists=candidate_exists,
                        report_exists=report_exists,
                        phase=phase,
                    ), tempfile.TemporaryDirectory() as directory:
                        root = Path(directory)
                        if candidate_exists:
                            self.write_candidate(root)
                        if report_exists:
                            (root / "report.json").write_bytes(b"old report")
                        before = self.snapshot(root)

                        def fault(actual_phase, _path):
                            if actual_phase == phase:
                                raise RuntimeError(f"fault at {phase}")

                        with self.assertRaisesRegex(RuntimeError, f"fault at {phase}"):
                            merge_tool.publish_candidate_bundle(
                                root / "candidates",
                                self.NEW_FILES,
                                root / "report.json",
                                self.NEW_REPORT,
                                fault=fault,
                            )
                        self.assertEqual(self.snapshot(root), before)
                        self.assert_no_transaction_debris(root)

    def test_keyboard_interrupt_restores_prior_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_candidate(root)
            before = self.snapshot(root)

            def interrupt(phase, _path):
                if phase == "after_candidate_install":
                    raise KeyboardInterrupt

            with self.assertRaises(KeyboardInterrupt):
                merge_tool.publish_candidate_bundle(
                    root / "candidates",
                    self.NEW_FILES,
                    root / "report.json",
                    self.NEW_REPORT,
                    fault=interrupt,
                )
            self.assertEqual(self.snapshot(root), before)
            self.assert_no_transaction_debris(root)

    def test_unexpected_candidate_content_rejects_before_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_candidate(root)
            unexpected = root / "candidates" / "notes.txt"
            unexpected.write_text("user data")
            (root / "report.json").write_bytes(b"old report")
            before = self.snapshot(root)
            with self.assertRaisesRegex(ValueError, "unexpected managed candidate content"):
                merge_tool.publish_candidate_bundle(
                    root / "candidates",
                    self.NEW_FILES,
                    root / "report.json",
                    self.NEW_REPORT,
                )
            self.assertEqual(self.snapshot(root), before)
            self.assert_no_transaction_debris(root)

    def test_rollback_failure_retains_and_names_recovery_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_candidate(root)

            def fault(phase, _path):
                if phase == "after_candidate_install":
                    raise RuntimeError("publication failed")

            def fail_restore(source, destination):
                if ".backup." in source.name and destination == root / "candidates":
                    raise OSError("rollback blocked")
                os.rename(source, destination)

            with self.assertRaisesRegex(RuntimeError, "recovery copies retained") as raised:
                merge_tool.publish_candidate_bundle(
                    root / "candidates",
                    self.NEW_FILES,
                    root / "report.json",
                    self.NEW_REPORT,
                    fault=fault,
                    move=fail_restore,
                )
            backups = [path for path in root.iterdir() if ".backup." in path.name]
            self.assertEqual(len(backups), 1)
            self.assertTrue(backups[0].is_dir())
            self.assertIn(str(backups[0]), str(raised.exception))

    def test_report_rollback_failure_still_restores_candidate_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_candidate(root)
            (root / "report.json").write_bytes(b"old report")
            old_candidates, _ = self.snapshot(root)

            def fault(phase, _path):
                if phase == "after_report_install":
                    raise RuntimeError("publication failed")

            def fail_report_removal(source, destination):
                if (
                    source == root / "report.json"
                    and source.read_bytes() == self.NEW_REPORT
                    and destination.name.startswith(".report.json.")
                ):
                    raise OSError("report rollback blocked")
                os.rename(source, destination)

            with self.assertRaisesRegex(RuntimeError, "recovery copies retained"):
                merge_tool.publish_candidate_bundle(
                    root / "candidates",
                    self.NEW_FILES,
                    root / "report.json",
                    self.NEW_REPORT,
                    fault=fault,
                    move=fail_report_removal,
                )
            self.assertEqual(self.snapshot(root)[0], old_candidates)
            self.assertTrue(
                [path for path in root.iterdir() if ".report.json.backup." in path.name]
            )

    def test_report_must_describe_exact_candidate_tree_before_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            before = self.snapshot(root)
            with self.assertRaisesRegex(ValueError, "candidate report"):
                merge_tool.publish_candidate_bundle(
                    root / "candidates",
                    self.NEW_FILES,
                    root / "report.json",
                    b"{}",
                )
            self.assertEqual(self.snapshot(root), before)

    def test_candidate_and_report_paths_cannot_overlap(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(ValueError, "paths collide"):
                merge_tool.publish_candidate_bundle(
                    root / "candidates",
                    self.NEW_FILES,
                    root / "candidates" / "report.json",
                    self.NEW_REPORT,
                )

    def test_report_change_after_staging_aborts_and_preserves_latest_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_candidate(root)
            (root / "report.json").write_bytes(b"old report")

            def mutate_report(phase, _path):
                if phase == "after_staging":
                    (root / "report.json").write_bytes(b"concurrent report")

            with self.assertRaisesRegex(RuntimeError, "changed while staging"):
                merge_tool.publish_candidate_bundle(
                    root / "candidates",
                    self.NEW_FILES,
                    root / "report.json",
                    self.NEW_REPORT,
                    fault=mutate_report,
                )
            self.assertEqual(self.snapshot(root)[1], b"concurrent report")
            self.assertIn("data/maps/OldMap/map.json", self.snapshot(root)[0])
            self.assert_no_transaction_debris(root)

    def test_candidate_changes_after_staging_abort_and_preserve_latest_tree(self):
        mutations = ("content", "unexpected")
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.write_candidate(root)
                (root / "report.json").write_bytes(b"old report")

                def mutate_candidate(phase, _path):
                    if phase != "after_staging":
                        return
                    if mutation == "content":
                        self.write_candidate(root, self.NEW_FILES["data/maps/NewMap/map.json"])
                    else:
                        (root / "candidates" / "notes.txt").write_bytes(b"concurrent note")

                mutate_candidate("after_staging", None)
                expected = self.snapshot(root)
                # Restore the initial state so the mutation occurs inside publication.
                if mutation == "content":
                    self.write_candidate(root)
                else:
                    (root / "candidates" / "notes.txt").unlink()

                with self.assertRaisesRegex(RuntimeError, "changed while staging"):
                    merge_tool.publish_candidate_bundle(
                        root / "candidates",
                        self.NEW_FILES,
                        root / "report.json",
                        self.NEW_REPORT,
                        fault=mutate_candidate,
                    )
                self.assertEqual(self.snapshot(root), expected)
                self.assert_no_transaction_debris(root)

    def test_absent_destinations_created_after_staging_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            def create_destinations(phase, _path):
                if phase == "after_staging":
                    self.write_candidate(root)
                    (root / "report.json").write_bytes(b"concurrent report")

            with self.assertRaisesRegex(RuntimeError, "changed while staging"):
                merge_tool.publish_candidate_bundle(
                    root / "candidates",
                    self.NEW_FILES,
                    root / "report.json",
                    self.NEW_REPORT,
                    fault=create_destinations,
                )
            self.assertIn("data/maps/OldMap/map.json", self.snapshot(root)[0])
            self.assertEqual(self.snapshot(root)[1], b"concurrent report")
            self.assert_no_transaction_debris(root)

    def test_existing_destinations_removed_after_staging_remain_absent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_candidate(root)
            (root / "report.json").write_bytes(b"old report")

            def remove_destinations(phase, _path):
                if phase == "after_staging":
                    shutil.rmtree(root / "candidates")
                    (root / "report.json").unlink()

            with self.assertRaisesRegex(RuntimeError, "changed while staging"):
                merge_tool.publish_candidate_bundle(
                    root / "candidates",
                    self.NEW_FILES,
                    root / "report.json",
                    self.NEW_REPORT,
                    fault=remove_destinations,
                )
            self.assertEqual(self.snapshot(root), (None, None))
            self.assert_no_transaction_debris(root)

    def test_report_created_before_install_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_candidate(root)
            before_candidates = self.snapshot(root)[0]

            def create_report(phase, _path):
                if phase == "before_report_install":
                    (root / "report.json").write_bytes(b"concurrent report")

            with self.assertRaises(FileExistsError):
                merge_tool.publish_candidate_bundle(
                    root / "candidates",
                    self.NEW_FILES,
                    root / "report.json",
                    self.NEW_REPORT,
                    fault=create_report,
                    move=os.replace,
                )
            self.assertEqual(self.snapshot(root), (before_candidates, b"concurrent report"))
            self.assert_no_transaction_debris(root)

    def test_report_changed_before_install_preserves_old_report_recovery_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_candidate(root)
            (root / "report.json").write_bytes(b"old report")
            before_candidates = self.snapshot(root)[0]

            def replace_report(phase, _path):
                if phase == "before_report_install":
                    (root / "report.json").write_bytes(b"concurrent report")

            with self.assertRaisesRegex(RuntimeError, "recovery copies retained") as raised:
                merge_tool.publish_candidate_bundle(
                    root / "candidates",
                    self.NEW_FILES,
                    root / "report.json",
                    self.NEW_REPORT,
                    fault=replace_report,
                    move=os.replace,
                )
            self.assertEqual(self.snapshot(root), (before_candidates, b"concurrent report"))
            debris = [
                path
                for path in root.iterdir()
                if ".stage." in path.name or ".backup." in path.name
            ]
            self.assertEqual(len(debris), 1)
            self.assertIn(".report.json.backup.", debris[0].name)
            self.assertEqual(debris[0].read_bytes(), b"old report")
            self.assertIn(str(debris[0]), str(raised.exception))
            self.assertIn(
                "cannot restore prior report without overwriting it",
                str(raised.exception),
            )


class FrozenDependencyPostimageSpecTests(unittest.TestCase):
    def test_frozen_specs_cover_all_authored_closures_and_owner_files(self):
        specs = merge_tool.DEPENDENCY_POSTIMAGE_SPECS
        self.assertEqual(len(specs), 11)
        dependency_ids = {
            dependency["id"]
            for spec in specs.values()
            for dependency in spec["dependencies"]
        }
        literal_ids = {
            literal["id"]
            for spec in specs.values()
            for literal in spec["required_literals"]
        }
        self.assertEqual(len(dependency_ids), 14)
        self.assertEqual(
            literal_ids,
            {
                "constant:FLAG_ROUTE120_BADGECHECKED",
                "constant:FLAG_ROUTE123_BADGECHECKED",
                "constant:FLAG_RECEIVED_CAMERUPTITE",
            },
        )


class DependencyPostimageValidationTests(unittest.TestCase):
    def setUp(self):
        self.baseline = b"Root::\n\tmsgbox OldText\n\tend\nOldText:\n\t.string \"old$\"\n"
        self.direct = b"Root::\n\tmsgbox NewText\n\tend\nNewText:\n\t.string \"new$\"\n"
        self.adapted = b"Root::\n\tmsgbox NewText\n\tend\nNewText:\n\t.string \"adapted$\"\n"
        direct_block = merge_tool.expand_label_block(
            "Root", merge_tool.parse_label_blocks(self.direct, "direct")
        )[0]
        adapted_block = merge_tool.expand_label_block(
            "Root", merge_tool.parse_label_blocks(self.adapted, "adapted")
        )[0]
        self.source = {
            "id": "dependency:Root",
            "label": "Root",
            "owners": {"legacy": "scripts.inc", "current": "scripts.inc"},
            "normalized_blocks": {"legacy": direct_block, "current": None},
            "normalized_block_sha256": {
                "legacy": hashlib.sha256(direct_block.encode()).hexdigest(),
                "current": None,
            },
            "block_labels": {"legacy": ["Root"], "current": []},
            "item_equivalence": [],
        }
        self.resolution = {
            "id": "dependency:Root",
            "decision": "use_archive",
            "evidence": "reviewed",
        }
        self.direct_spec = {
            "scripts.inc": {
                "old_sha256": hashlib.sha256(self.baseline).hexdigest(),
                "new_sha256": hashlib.sha256(self.direct).hexdigest(),
                "dependencies": [
                    {
                        "id": "dependency:Root",
                        "target_label": "Root",
                        "kind": "direct_legacy",
                        "target_sha256": hashlib.sha256(direct_block.encode()).hexdigest(),
                        "rationale": "Exact reviewed legacy closure.",
                    }
                ],
                "required_literals": [],
            }
        }
        self.adapted_spec = copy.deepcopy(self.direct_spec)
        self.adapted_spec["scripts.inc"]["new_sha256"] = hashlib.sha256(
            self.adapted
        ).hexdigest()
        self.adapted_spec["scripts.inc"]["dependencies"][0].update(
            kind="current_adaptation",
            target_sha256=hashlib.sha256(adapted_block.encode()).hexdigest(),
            rationale="Reviewed current syntax adaptation.",
        )

    def validate(self, actual, spec=None, dependencies=None, resolutions=None):
        return merge_tool.validate_dependency_postimages(
            {"scripts.inc": actual},
            {"scripts.inc": self.baseline},
            (
                {self.resolution["id"]: self.resolution}
                if resolutions is None
                else resolutions
            ),
            {self.source["label"]: self.source} if dependencies is None else dependencies,
            self.direct_spec if spec is None else spec,
        )

    def test_accepts_exact_direct_and_reviewed_adaptation_postimages(self):
        direct = self.validate(self.direct)
        self.assertEqual(direct["missing_dependencies"], [])
        self.assertEqual(
            direct["dependency_records"][0]["actual_target_sha256"],
            self.source["normalized_block_sha256"]["legacy"],
        )
        adapted = self.validate(self.adapted, self.adapted_spec)
        self.assertEqual(adapted["missing_dependencies"], [])
        self.assertEqual(
            adapted["dependency_records"][0]["adaptation_kind"],
            "current_adaptation",
        )

    def test_missing_patch_and_unrelated_edit_are_reported_from_whole_postimage(self):
        missing = self.validate(self.baseline)
        self.assertIn("dependency:Root", missing["missing_dependencies"])
        unrelated = self.validate(self.direct + b"@ unrelated\n")
        self.assertIn("dependency:Root", unrelated["missing_dependencies"])

    def test_changed_or_removed_target_block_is_reported(self):
        changed = self.validate(self.direct.replace(b'"new$"', b'"wrong$"'))
        self.assertIn("dependency:Root", changed["missing_dependencies"])
        removed = self.validate(b"Other::\n\tend\n")
        self.assertIn("dependency:Root", removed["missing_dependencies"])

    def test_missing_required_constant_is_reported(self):
        baseline = b"#define FLAG_UNUSED 0x22\n"
        actual = b"#define FLAG_REQUIRED 0x22\n"
        spec = {
            "scripts.inc": {
                "old_sha256": hashlib.sha256(baseline).hexdigest(),
                "new_sha256": hashlib.sha256(actual).hexdigest(),
                "dependencies": [],
                "required_literals": [
                    {
                        "id": "constant:FLAG_REQUIRED",
                        "text": "#define FLAG_REQUIRED 0x22",
                        "rationale": "Reviewed unused flag reuse.",
                    }
                ],
            }
        }
        valid = merge_tool.validate_dependency_postimages(
            {"scripts.inc": actual},
            {"scripts.inc": baseline},
            {},
            {},
            spec,
        )
        self.assertEqual(valid["missing_dependencies"], [])
        missing = merge_tool.validate_dependency_postimages(
            {"scripts.inc": baseline},
            {"scripts.inc": baseline},
            {},
            {},
            spec,
        )
        self.assertIn("constant:FLAG_REQUIRED", missing["missing_dependencies"])

    def test_candidate_item_adapter_needs_no_source_file_write(self):
        item_source = copy.deepcopy(self.source)
        item_source["label"] = "Legacy_Item"
        item_source["id"] = "dependency:Legacy_Item"
        item_source["item_equivalence"] = [{"archive_label": "Legacy_Item"}]
        item_resolution = {
            "id": "dependency:Legacy_Item",
            "decision": "use_archive",
            "evidence": "adapt into candidate object event",
        }
        result = merge_tool.validate_dependency_postimages(
            {},
            {},
            {item_resolution["id"]: item_resolution},
            {item_source["label"]: item_source},
            {},
        )
        self.assertEqual(result["missing_dependencies"], [])
        self.assertEqual(
            result["dependency_records"][0]["adaptation_kind"],
            "candidate_item_adapter",
        )


if __name__ == "__main__":
    unittest.main()
