import copy
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
    extract_legacy_item,
    merge_added_event,
    merge_base_event,
    merge_category,
)


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


if __name__ == "__main__":
    unittest.main()
