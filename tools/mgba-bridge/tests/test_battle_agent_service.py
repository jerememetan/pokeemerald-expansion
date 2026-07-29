"""Focused tests for read-only battle-agent tools."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest import mock


BRIDGE_DIRECTORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BRIDGE_DIRECTORY))

from battle_agent_service import (  # noqa: E402
    ToolError,
    _connect,
    analyze_action,
    choose_action,
    get_battle_state,
    get_battler,
    get_battler_moves,
    get_field_state,
    list_legal_actions,
    compare_speed,
    handle_request_frame,
    run_tool_agent,
)
from bridge_protocol import LegalAction  # noqa: E402


class BattleAgentServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.actions = (
            LegalAction(0, 0, 0, 2, 1, 0),
            LegalAction(1, 1, 0, 3, 1, 1),
        )

    def test_list_legal_actions_exposes_only_rom_action_indexes(self) -> None:
        self.assertEqual(
            list_legal_actions(self.actions),
            [{"action_index": 0, "move_slot": 0, "target_battler": 0},
             {"action_index": 1, "move_slot": 1, "target_battler": 0}],
        )

    def test_choose_action_rejects_unlisted_index(self) -> None:
        with self.assertRaises(ToolError):
            choose_action(self.actions, 2)

    def test_action_analysis_reports_only_rom_derived_facts(self) -> None:
        self.assertEqual(
            analyze_action(self.actions, 1),
            {"action_index": 1, "move_slot": 1, "target_battler": 0,
             "type_effectiveness": 3, "has_stab": True, "can_faint_target": True},
        )

    def test_battle_state_reports_request_metadata_without_memory_access(self) -> None:
        self.assertEqual(
            get_battle_state(sequence=7, turn_sequence=3, requesting_battler=1, payload=bytes(417)),
            {"request_sequence": 7, "turn_sequence": 3, "requesting_battler": 1,
             "active_battlers": [get_battler(bytes(417), 0), get_battler(bytes(417), 1)]},
        )

    def test_snapshot_tools_decode_the_documented_v2_offsets(self) -> None:
        payload = bytearray(417)
        payload[9:11] = (261).to_bytes(2, "little")
        payload[11:15] = bytes((6, 17, 18, 19))
        payload[15:17] = (42).to_bytes(2, "little")
        payload[17:19] = (99).to_bytes(2, "little")
        payload[19:21] = (25).to_bytes(2, "little")
        payload[21:23] = (30).to_bytes(2, "little")
        payload[23:25] = (15).to_bytes(2, "little")
        payload[380:384] = (3).to_bytes(4, "little")

        battler = get_battler(bytes(payload), 0)

        self.assertEqual(battler["species"], 261)
        self.assertEqual(battler["level"], 6)
        self.assertEqual(battler["ability"], 42)
        self.assertEqual(battler["item"], 99)
        self.assertEqual(battler["hp"], 25)
        self.assertEqual(get_field_state(bytes(payload))["field_statuses"], 3)

    def test_move_and_speed_tools_use_the_active_battler_snapshot(self) -> None:
        payload = bytearray(417)
        payload[9 + 18:9 + 20] = (18).to_bytes(2, "little")
        payload[9 + 92 + 18:9 + 92 + 20] = (27).to_bytes(2, "little")
        payload[9 + 44:9 + 56] = bytes((33, 0, 20, 0, 0, 35, 0, 0, 40, 100, 0, 0))

        moves = get_battler_moves(bytes(payload), 0)

        self.assertEqual(moves[0]["move"], 33)
        self.assertEqual(moves[0]["pp"], 20)
        self.assertEqual(compare_speed(bytes(payload)), {
            "battler_0_speed": 18,
            "battler_1_speed": 27,
            "normal_order": "battler_1_first",
            "note": "Move priority can override normal speed order.",
        })

    def test_tool_loop_returns_only_a_terminal_legal_choice(self) -> None:
        payload = bytes(417)
        responses = [
            {"tool_calls": [{"function": {"name": "list_legal_actions", "arguments": {}}}]},
            {"tool_calls": [{"function": {"name": "choose_action", "arguments": {"action_index": 1}}}]},
        ]

        with mock.patch("battle_agent_service.request_ollama", side_effect=responses) as request:
            selected = run_tool_agent(7, 3, 1, self.actions, payload)

        self.assertEqual(selected, 1)
        self.assertEqual(request.call_count, 2)

    def test_tool_loop_accepts_qwen_exact_json_tool_content(self) -> None:
        payload = bytes(417)
        responses = [
            {"content": '{"name":"list_legal_actions","arguments":{}}'},
            {"tool_calls": [{"function": {"name": "choose_action", "arguments": {"action_index": 1}}}]},
        ]

        with mock.patch("battle_agent_service.request_ollama", side_effect=responses):
            self.assertEqual(run_tool_agent(7, 3, 1, self.actions, payload), 1)

    def test_tool_loop_rejects_noncanonical_qwen_json_content(self) -> None:
        payload = bytes(417)
        for content in (
            "I choose action 1",
            '{"name":"list_legal_actions","arguments":{},"extra":true}',
            '{"name":"list_legal_actions","arguments":[]}',
        ):
            with self.subTest(content=content), mock.patch("battle_agent_service.request_ollama", return_value={"content": content}):
                self.assertIsNone(run_tool_agent(7, 3, 1, self.actions, payload))

    def test_tool_loop_retries_one_malformed_reply_before_a_legal_choice(self) -> None:
        payload = bytes(417)
        responses = [
            {"content": '{"name": list_legal_actions, "arguments": {}}'},
            {"content": '{"name":"list_legal_actions","arguments":{}}'},
            {"content": '{"name":"choose_action","arguments":{"action_index":1}}'},
        ]

        with mock.patch("battle_agent_service.request_ollama", side_effect=responses) as request:
            self.assertEqual(run_tool_agent(7, 3, 1, self.actions, payload), 1)

        self.assertEqual(request.call_count, 3)
        self.assertEqual(
            json.loads(request.call_args_list[2].args[0][-1]["content"]),
            list_legal_actions(self.actions),
        )

    def test_tool_loop_rejects_a_second_malformed_reply(self) -> None:
        payload = bytes(417)
        responses = [
            {"content": '{"name": list_legal_actions, "arguments": {}}'},
            {"content": '{"name": choose_action, "arguments": {}}'},
        ]

        with mock.patch("battle_agent_service.request_ollama", side_effect=responses) as request:
            self.assertIsNone(run_tool_agent(7, 3, 1, self.actions, payload))

        self.assertEqual(request.call_count, 2)

    def test_tool_loop_rejects_text_only_or_unknown_tool_completion(self) -> None:
        payload = bytes(417)
        for response in ({}, {"tool_calls": [{"function": {"name": "open_shell", "arguments": {}}}]}):
            with self.subTest(response=response), mock.patch("battle_agent_service.request_ollama", return_value=response):
                self.assertIsNone(run_tool_agent(7, 3, 1, self.actions, payload))

    def test_service_emits_a_fixed_response_only_after_a_legal_selection(self) -> None:
        payload = bytearray(417)
        payload[0:4] = (7).to_bytes(4, "little")
        payload[4:9] = bytes((1, 1, 3, 0, 2))
        payload[392:399] = bytes((1, 0, 0, 0, 2, 1, 0))
        frame = b"BAGB\x02\x01\xa1\x01" + bytes(payload)

        with mock.patch("battle_agent_service.run_tool_agent", return_value=0):
            self.assertEqual(handle_request_frame(frame), b"BAGB\x02\x02\x05\x00\x07\x00\x00\x00\x00")

    def test_connect_retries_to_the_lua_listener_and_returns_the_client_socket(self) -> None:
        connection = mock.Mock()
        with mock.patch("battle_agent_service.socket.create_connection", side_effect=[OSError("not ready"), connection]) as create_connection:
            with mock.patch("battle_agent_service.time.sleep") as sleep:
                self.assertIs(_connect(57621), connection)

        self.assertEqual(
            create_connection.call_args_list,
            [mock.call(("127.0.0.1", 57621), timeout=1), mock.call(("127.0.0.1", 57621), timeout=1)],
        )
        sleep.assert_called_once_with(0.25)
        connection.settimeout.assert_called_once_with(None)


if __name__ == "__main__":
    unittest.main()
