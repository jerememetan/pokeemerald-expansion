"""Focused tests for the V4 read-only battle-agent tools."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest import mock


BRIDGE_DIRECTORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BRIDGE_DIRECTORY))

from battle_agent_service import (  # noqa: E402
    AgentDecision,
    ToolError,
    _connect,
    SERVICE_TIMEOUT_SECONDS,
    advance_model_index,
    analyze_action,
    choose_actions,
    compare_speed,
    decode_major_status,
    decode_stat_changes,
    decode_types,
    decode_volatile_status,
    decode_field_state,
    decode_move_target,
    decode_move_split,
    default_model_index,
    format_decision_audit,
    format_console_audit,
    get_battle_state,
    get_battler,
    get_battler_moves,
    get_field_state,
    get_party,
    handle_request_frame,
    list_legal_actions,
    parse_ollama_model_list,
    run_tool_agent,
)
from bridge_protocol import (  # noqa: E402
    ACTION_KIND_MOVE,
    ACTION_KIND_SWITCH,
    ACTION_NONE,
    BATTLE_MODE_TRAINER_DOUBLE,
    BATTLE_MODE_TRAINER_SINGLE,
    BATTLE_MODE_TRAINER_TWO_OPPONENT_DOUBLE,
    LegalAction,
    VERSION,
    format_response_frame,
)


def _v4_payload(*, battle_mode: int = BATTLE_MODE_TRAINER_SINGLE) -> bytearray:
    payload = bytearray(1369)
    for party_slot in range(6):
        payload[397 + party_slot * 96] = party_slot
        payload[397 + party_slot * 96 + 3] = ACTION_NONE
    payload[0:4] = (7).to_bytes(4, "little")
    if battle_mode == BATTLE_MODE_TRAINER_SINGLE:
        payload[4:14] = bytes((battle_mode, 1, 3, 0, 2, 1, ACTION_NONE, 1, 0, 0))
    else:
        payload[4:14] = bytes((battle_mode, 2, 3, 0, 4, 1, 3, 1, 1, 0))
    return payload


def _frame(payload: bytearray) -> bytes:
    return b"BAGB" + bytes((VERSION, 1)) + len(payload).to_bytes(2, "little") + bytes(payload)


class BattleAgentServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.actions_by_battler = {
            1: (
                LegalAction(0, ACTION_KIND_MOVE, 0, 0, ACTION_NONE, 2, 1, 0, actor_battler=1),
                LegalAction(1, ACTION_KIND_MOVE, 1, 0, ACTION_NONE, 3, 1, 1, actor_battler=1),
            ),
        }

    def test_model_list_parser_reads_only_model_names(self) -> None:
        output = "NAME ID SIZE MODIFIED\nqwen2.5-coder:7b abc 4.7 GB now\nllama3.2:3b def 2.0 GB now\n"

        self.assertEqual(parse_ollama_model_list(output), ("qwen2.5-coder:7b", "llama3.2:3b"))
        self.assertEqual(parse_ollama_model_list("NAME ID SIZE MODIFIED\n\n"), ())

    def test_model_selection_prefers_qwen_and_wraps(self) -> None:
        models = ("llama3.2:3b", "qwen2.5-coder:7b")

        self.assertEqual(default_model_index(models), 1)
        self.assertEqual(default_model_index(models[:1]), 0)
        self.assertEqual(advance_model_index(0, -1, len(models)), 1)
        self.assertEqual(advance_model_index(1, 1, len(models)), 0)

    def test_service_timeout_allows_twenty_seconds_for_local_model_responses(self) -> None:
        self.assertEqual(SERVICE_TIMEOUT_SECONDS, 20.0)

    def test_console_audit_highlights_selected_decision_only_when_ansi_enabled(self) -> None:
        audit = "audit #7\n  tools used: list_legal_actions\n  selected: battler 1: 1=BOUNCE->battler 0\n  battler 1 ROM facts: STAB=yes"

        self.assertIn("\x1b[1;92m  selected:", format_console_audit(audit, True))
        self.assertIn("\x1b[1;92m  battler 1 ROM facts:", format_console_audit(audit, True))
        self.assertEqual(format_console_audit(audit, False), audit)

    def test_readable_battle_facts_decode_types_status_and_stat_deltas(self) -> None:
        self.assertEqual(decode_types((10, 9, 10)), ["FIRE"])
        self.assertEqual(decode_major_status(1 << 6), ["PARALYSIS"])
        self.assertEqual(decode_stat_changes((7, 5, 6, 8, 4, 6, 6, 6)), {
            "attack": 1, "defense": -1, "speed": 0, "special_attack": 2,
            "special_defense": -2, "accuracy": 0, "evasion": 0,
        })

    def test_volatile_status_decoder_names_directly_published_effects(self) -> None:
        self.assertEqual(decode_volatile_status((1 << 0) | (1 << 24), (1 << 2) | (1 << 10) | (1 << 27)), [
            "CONFUSION", "SUBSTITUTE", "LEECH_SEED", "ROOTED", "HEAL_BLOCK",
        ])

    def test_field_state_decoder_names_weather_field_and_side_effects(self) -> None:
        self.assertEqual(decode_field_state((1 << 0), 0, (1 << 1), (1 << 0) | (1 << 14), (1 << 1) | (1 << 5)), {
            "weather": ["RAIN"], "terrain": "GRASS", "field_effects": ["TRICK_ROOM"],
            "player_side_effects": ["REFLECT", "STEALTH_ROCK"],
            "opponent_side_effects": ["LIGHT_SCREEN", "SAFEGUARD"],
        })

    def test_move_metadata_decoders_name_target_and_damage_category(self) -> None:
        self.assertEqual(decode_move_target(0), "SELECTED_TARGET")
        self.assertEqual(decode_move_target(1 << 7), "ALLY")
        self.assertEqual(decode_move_split(0), "PHYSICAL")
        self.assertEqual(decode_move_split(2), "STATUS")

    def test_list_legal_actions_is_actor_keyed(self) -> None:
        self.assertEqual(
            list_legal_actions(self.actions_by_battler),
            [{"battler_id": 1, "actions": [
                {"action_index": 0, "kind": "move", "move_slot": 0, "target_battler": 0},
                {"action_index": 1, "kind": "move", "move_slot": 1, "target_battler": 0},
            ]}],
        )

    def test_legal_action_list_includes_published_move_facts(self) -> None:
        payload = _v4_payload()
        move_offset = 14 + 92 + 44
        payload[move_offset : move_offset + 12] = bytes((33, 0, 20, 0, 35, 100, 40, 0, 1, 0, 255, 0))

        action = list_legal_actions(self.actions_by_battler, payload=bytes(payload))[0]["actions"][0]

        self.assertEqual(action["move"], 33)
        self.assertEqual(action["move_name"], "TACKLE")
        self.assertEqual(action["pp"], 20)
        self.assertEqual(action["power"], 35)
        self.assertEqual(action["accuracy"], 100)
        self.assertEqual(action["type_effectiveness"], 2)
        self.assertTrue(action["has_stab"])
        self.assertFalse(action["can_faint_target"])

    def test_choose_actions_rejects_unlisted_missing_or_duplicate_choices(self) -> None:
        paired = {
            1: (LegalAction(0, ACTION_KIND_SWITCH, ACTION_NONE, ACTION_NONE, 2, 0, 0, 0, actor_battler=1),),
            3: (LegalAction(0, ACTION_KIND_SWITCH, ACTION_NONE, ACTION_NONE, 2, 0, 0, 0, actor_battler=3),),
        }
        for choices in (
            [{"battler_id": 1, "action_index": 4}],
            [{"battler_id": 1, "action_index": 0}],
            [{"battler_id": 1, "action_index": 0}, {"battler_id": 3, "action_index": 0}],
        ):
            with self.subTest(choices=choices):
                with self.assertRaises(ToolError):
                    choose_actions(paired, choices)

    def test_choose_actions_accepts_one_action_per_controlled_battler(self) -> None:
        selected = choose_actions(self.actions_by_battler, [{"battler_id": 1, "action_index": 1}])
        self.assertEqual(selected, ((1, 1),))

    def test_action_analysis_reports_only_rom_derived_facts(self) -> None:
        self.assertEqual(
            analyze_action(self.actions_by_battler[1], 1),
            {"action_index": 1, "kind": "move", "move_slot": 1, "target_battler": 0,
             "type_effectiveness": 3, "has_stab": True, "can_faint_target": True},
        )

    def test_battle_state_reports_all_active_battlers_and_control(self) -> None:
        payload = bytes(_v4_payload(battle_mode=BATTLE_MODE_TRAINER_DOUBLE))
        state = get_battle_state(sequence=7, turn_sequence=3, controlled_battlers=(1, 3), battler_count=4, payload=payload)
        self.assertEqual(state["controlled_battlers"], [1, 3])
        self.assertEqual([entry["battler_id"] for entry in state["active_battlers"]], [0, 1, 2, 3])

    def test_snapshot_tools_decode_documented_v4_offsets(self) -> None:
        payload = _v4_payload()
        payload[14:16] = (261).to_bytes(2, "little")
        payload[16:20] = bytes((6, 17, 18, 19))
        payload[20:22] = (42).to_bytes(2, "little")
        payload[22:24] = (99).to_bytes(2, "little")
        payload[24:26] = (25).to_bytes(2, "little")
        payload[385:389] = (3).to_bytes(4, "little")

        battler = get_battler(bytes(payload), 0)

        self.assertEqual(battler["species"], 261)
        self.assertEqual(battler["level"], 6)
        self.assertEqual(battler["ability"], 42)
        self.assertEqual(battler["item"], 99)
        self.assertEqual(battler["hp"], 25)
        self.assertEqual(get_field_state(bytes(payload))["field_effects"], ["MAGIC_ROOM", "TRICK_ROOM"])

    def test_party_tool_exposes_all_slots_and_usable_metadata(self) -> None:
        payload = _v4_payload()
        party_member = 397 + 96
        payload[party_member : party_member + 4] = bytes((1, 0, 1, 0))
        payload[party_member + 4 : party_member + 6] = (261).to_bytes(2, "little")
        payload[party_member + 6 : party_member + 10] = bytes((6, 17, 18, 19))
        payload[party_member + 10 : party_member + 14] = bytes((42, 0, 99, 0))
        payload[party_member + 14 : party_member + 18] = bytes((25, 0, 30, 0))

        party = get_party(bytes(payload))

        self.assertEqual(len(party), 6)
        self.assertEqual(party[1]["party_slot"], 1)
        self.assertFalse(party[1]["is_active"])
        self.assertTrue(party[1]["is_usable"])
        self.assertEqual(party[1]["species"], 261)
        self.assertEqual(party[1]["hp"], 25)

    def test_party_tool_labels_two_trainer_party_owners(self) -> None:
        payload = _v4_payload(battle_mode=BATTLE_MODE_TRAINER_TWO_OPPONENT_DOUBLE)
        for party_slot in range(6):
            payload[397 + party_slot * 96 + 3] = 1 if party_slot < 3 else 3

        party = get_party(bytes(payload))

        self.assertEqual([member["owner_battler"] for member in party], [1, 1, 1, 3, 3, 3])
        self.assertEqual([member["owner"] for member in party], ["opponent-left"] * 3 + ["opponent-right"] * 3)
        self.assertNotIn("switchable", party[0])

    def test_move_and_speed_tools_read_four_active_battlers(self) -> None:
        payload = _v4_payload(battle_mode=BATTLE_MODE_TRAINER_DOUBLE)
        payload[14 + 18:14 + 20] = (18).to_bytes(2, "little")
        payload[14 + 92 + 18:14 + 92 + 20] = (27).to_bytes(2, "little")
        payload[14 + 3 * 92 + 18:14 + 3 * 92 + 20] = (55).to_bytes(2, "little")
        payload[14 + 44:14 + 56] = bytes((33, 0, 20, 0, 0, 35, 0, 0, 40, 100, 0, 0))

        self.assertEqual(get_battler_moves(bytes(payload), 0)[0]["move"], 33)
        speed = compare_speed(bytes(payload), 4)
        self.assertEqual(speed["speeds"]["battler_3"], 55)
        self.assertEqual(speed["normal_order"][0], "battler_3")

    def test_compare_speed_reverses_effective_speed_order_in_trick_room(self) -> None:
        payload = _v4_payload(battle_mode=BATTLE_MODE_TRAINER_DOUBLE)
        payload[14 + 18:14 + 20] = (18).to_bytes(2, "little")
        payload[14 + 92 + 18:14 + 92 + 20] = (55).to_bytes(2, "little")
        payload[385:389] = (1 << 1).to_bytes(4, "little")

        speed = compare_speed(bytes(payload), 2)

        self.assertTrue(speed["trick_room_active"])
        self.assertEqual(speed["normal_order"], ["battler_0", "battler_1"])

    def test_tool_loop_requires_atomic_terminal_choice(self) -> None:
        payload = bytes(_v4_payload(battle_mode=BATTLE_MODE_TRAINER_DOUBLE))
        actions = {
            1: (LegalAction(0, ACTION_KIND_MOVE, 0, 0, ACTION_NONE, 2, 1, 0, actor_battler=1),),
            3: (LegalAction(0, ACTION_KIND_MOVE, 0, 0, ACTION_NONE, 2, 1, 0, actor_battler=3),),
        }
        responses = [
            {"tool_calls": [{"function": {"name": "list_legal_actions", "arguments": {}}}]},
            {"tool_calls": [{"function": {"name": "choose_actions", "arguments": {"actions": [
                {"battler_id": 1, "action_index": 0}, {"battler_id": 3, "action_index": 0}
            ]}}}]},
        ]
        with mock.patch("battle_agent_service.request_ollama", side_effect=responses) as request:
            selected = run_tool_agent(7, 3, (1, 3), 4, actions, payload)
        self.assertEqual(selected, AgentDecision(((1, 0), (3, 0)), ("list_legal_actions", "choose_actions")))
        self.assertEqual(request.call_count, 2)

    def test_tool_loop_accepts_qwen_exact_json_tool_content(self) -> None:
        payload = bytes(_v4_payload())
        responses = [
            {"content": '{"name":"list_legal_actions","arguments":{}}'},
            {"content": '{"name":"choose_actions","arguments":{"actions":[{"battler_id":1,"action_index":1}]}}'},
        ]
        with mock.patch("battle_agent_service.request_ollama", side_effect=responses):
            selected = run_tool_agent(7, 3, (1,), 2, self.actions_by_battler, payload)
        self.assertEqual(selected.actions, ((1, 1),))

    def test_tool_loop_accepts_qwen_bare_terminal_action_list(self) -> None:
        """Qwen's tool template may omit the schema's outer actions object."""
        payload = bytes(_v4_payload())
        response = {"content": '{"name":"choose_actions","arguments":[{"battler_id":1,"action_index":1}]}' }
        with mock.patch("battle_agent_service.request_ollama", return_value=response):
            selected = run_tool_agent(7, 3, (1,), 2, self.actions_by_battler, payload)
        self.assertEqual(selected, AgentDecision(((1, 1),), ("choose_actions",)))

    def test_tool_loop_accepts_a_scoped_legal_action_query(self) -> None:
        """A model may request its own list rather than the complete action map."""
        payload = bytes(_v4_payload())
        responses = [
            {"content": '{"name":"list_legal_actions","arguments":{"battler_id":1}}'},
            {"content": '{"name":"choose_actions","arguments":{"actions":[{"battler_id":1,"action_index":1}]}}'},
        ]
        with mock.patch("battle_agent_service.request_ollama", side_effect=responses):
            selected = run_tool_agent(7, 3, (1,), 2, self.actions_by_battler, payload)
        self.assertEqual(selected, AgentDecision(((1, 1),), ("list_legal_actions", "choose_actions")))

    def test_tool_loop_rejects_text_only_or_unknown_tool_completion(self) -> None:
        payload = bytes(_v4_payload())
        for response in ({}, {"tool_calls": [{"function": {"name": "open_shell", "arguments": {}}}]}):
            with self.subTest(response=response), mock.patch("battle_agent_service.request_ollama", return_value=response):
                self.assertIsNone(run_tool_agent(7, 3, (1,), 2, self.actions_by_battler, payload))

    def test_decision_audit_reports_each_actor_and_rom_facts(self) -> None:
        payload = _v4_payload(battle_mode=BATTLE_MODE_TRAINER_DOUBLE)
        payload[14 + 92 + 44:14 + 92 + 56] = bytes((52, 0, 20, 10, 40, 100, 0, 0, 0, 0, 1, 0))
        actions = {
            1: (LegalAction(0, ACTION_KIND_MOVE, 0, 0, ACTION_NONE, 2, 1, 0, actor_battler=1),),
            3: (LegalAction(0, ACTION_KIND_SWITCH, ACTION_NONE, ACTION_NONE, 4, 0, 0, 0, actor_battler=3),),
        }
        audit = format_decision_audit(7, 4, AgentDecision(((1, 0), (3, 0)), ("get_battle_state", "choose_actions")), actions, bytes(payload))
        self.assertIn("selected: battler 1: 0=EMBER->battler 0; battler 3: 0=SWITCH->party 4", audit)
        self.assertIn("battler 1 ROM facts: STAB=yes", audit)
        self.assertIn("battler 3 ROM facts: switch_to_party_slot=4", audit)
        self.assertNotIn("reasoning", audit)

    def test_handle_request_frame_emits_v5_atomic_response_after_a_valid_decision(self) -> None:
        payload = _v4_payload(battle_mode=BATTLE_MODE_TRAINER_DOUBLE)
        payload[973:982] = bytes((1, 0, ACTION_KIND_MOVE, 0, 0, ACTION_NONE, 2, 1, 0))
        payload[1171:1180] = bytes((3, 0, ACTION_KIND_MOVE, 0, 0, ACTION_NONE, 2, 1, 0))
        with mock.patch("battle_agent_service.run_tool_agent", return_value=AgentDecision(((1, 0), (3, 0)), ("choose_actions",))), mock.patch("battle_agent_service.log") as log:
            self.assertEqual(handle_request_frame(_frame(payload)), format_response_frame(7, ((1, 0), (3, 0))))
        self.assertTrue(any(call.args[0].startswith("audit #7") for call in log.call_args_list))

    def test_handle_request_frame_audits_vanilla_fallback_without_a_response(self) -> None:
        payload = _v4_payload()
        payload[973:982] = bytes((1, 0, ACTION_KIND_MOVE, 0, 0, ACTION_NONE, 2, 1, 0))
        with mock.patch("battle_agent_service.run_tool_agent", return_value=None), mock.patch("battle_agent_service.log") as log:
            self.assertIsNone(handle_request_frame(_frame(payload)))
        log.assert_any_call("audit #7: no legal model decision; vanilla_fallback")

    def test_connect_retries_to_the_lua_listener_and_returns_the_client_socket(self) -> None:
        connection = mock.Mock()
        with mock.patch("battle_agent_service.socket.create_connection", side_effect=[OSError("not ready"), connection]) as create_connection:
            with mock.patch("battle_agent_service.time.sleep") as sleep:
                self.assertIs(_connect(57621), connection)
        self.assertEqual(create_connection.call_count, 2)
        sleep.assert_called_once_with(0.25)
        connection.settimeout.assert_called_once_with(None)


if __name__ == "__main__":
    unittest.main()
