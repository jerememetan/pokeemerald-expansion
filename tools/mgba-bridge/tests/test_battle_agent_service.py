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
    AgentDecision,
    ToolError,
    _connect,
    analyze_action,
    choose_action,
    get_battle_state,
    get_battler,
    get_battler_moves,
    get_field_state,
    get_party,
    list_legal_actions,
    compare_speed,
    format_decision_audit,
    handle_request_frame,
    run_tool_agent,
)
from bridge_protocol import ACTION_KIND_MOVE, ACTION_KIND_SWITCH, ACTION_NONE, LegalAction  # noqa: E402


def _v3_payload() -> bytearray:
    payload = bytearray(1049)
    for party_slot in range(6):
        payload[392 + party_slot * 96] = party_slot
    return payload


class BattleAgentServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.actions = (
            LegalAction(0, ACTION_KIND_MOVE, 0, 0, ACTION_NONE, 2, 1, 0),
            LegalAction(1, ACTION_KIND_MOVE, 1, 0, ACTION_NONE, 3, 1, 1),
        )

    def test_list_legal_actions_exposes_only_rom_action_indexes(self) -> None:
        self.assertEqual(
            list_legal_actions(self.actions),
            [{"action_index": 0, "kind": "move", "move_slot": 0, "target_battler": 0},
             {"action_index": 1, "kind": "move", "move_slot": 1, "target_battler": 0}],
        )

    def test_choose_action_rejects_unlisted_index(self) -> None:
        with self.assertRaises(ToolError):
            choose_action(self.actions, 2)

    def test_action_analysis_reports_only_rom_derived_facts(self) -> None:
        self.assertEqual(
            analyze_action(self.actions, 1),
            {"action_index": 1, "kind": "move", "move_slot": 1, "target_battler": 0,
             "type_effectiveness": 3, "has_stab": True, "can_faint_target": True},
        )

    def test_battle_state_reports_request_metadata_without_memory_access(self) -> None:
        self.assertEqual(
            get_battle_state(sequence=7, turn_sequence=3, requesting_battler=1, payload=bytes(1049)),
            {"request_sequence": 7, "turn_sequence": 3, "requesting_battler": 1,
             "active_battlers": [get_battler(bytes(1049), 0), get_battler(bytes(1049), 1)]},
        )

    def test_snapshot_tools_decode_the_documented_v3_offsets(self) -> None:
        payload = _v3_payload()
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

    def test_party_tool_exposes_all_slots_and_usable_metadata(self) -> None:
        payload = _v3_payload()
        party_member = 392 + 96
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

    def test_switch_action_is_exposed_without_move_facts(self) -> None:
        switch = LegalAction(2, ACTION_KIND_SWITCH, ACTION_NONE, ACTION_NONE, 4, 0, 0, 0)

        self.assertEqual(list_legal_actions((switch,)), [{"action_index": 2, "kind": "switch", "party_slot": 4}])
        self.assertEqual(analyze_action((switch,), 2), {"action_index": 2, "kind": "switch", "party_slot": 4})

    def test_tool_loop_can_inspect_party_before_selecting_a_switch(self) -> None:
        payload = bytes(1049)
        actions = (LegalAction(0, ACTION_KIND_MOVE, 0, 0, ACTION_NONE, 2, 1, 0), LegalAction(1, ACTION_KIND_SWITCH, ACTION_NONE, ACTION_NONE, 2, 0, 0, 0))
        responses = [
            {"tool_calls": [{"function": {"name": "get_party", "arguments": {}}}]},
            {"tool_calls": [{"function": {"name": "list_legal_actions", "arguments": {}}}]},
            {"tool_calls": [{"function": {"name": "choose_action", "arguments": {"action_index": 1}}}]},
        ]

        with mock.patch("battle_agent_service.request_ollama", side_effect=responses):
            selected = run_tool_agent(7, 3, 1, actions, payload)

        self.assertEqual(selected, AgentDecision(1, ("get_party", "list_legal_actions", "choose_action")))

    def test_move_and_speed_tools_use_the_active_battler_snapshot(self) -> None:
        payload = _v3_payload()
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
        payload = bytes(1049)
        responses = [
            {"tool_calls": [{"function": {"name": "list_legal_actions", "arguments": {}}}]},
            {"tool_calls": [{"function": {"name": "choose_action", "arguments": {"action_index": 1}}}]},
        ]

        with mock.patch("battle_agent_service.request_ollama", side_effect=responses) as request:
            selected = run_tool_agent(7, 3, 1, self.actions, payload)

        self.assertIsNotNone(selected)
        self.assertEqual(selected.action_index, 1)
        self.assertEqual(selected.tools_used, ("list_legal_actions", "choose_action"))
        self.assertEqual(request.call_count, 2)

    def test_tool_loop_accepts_qwen_exact_json_tool_content(self) -> None:
        payload = bytes(1049)
        responses = [
            {"content": '{"name":"list_legal_actions","arguments":{}}'},
            {"tool_calls": [{"function": {"name": "choose_action", "arguments": {"action_index": 1}}}]},
        ]

        with mock.patch("battle_agent_service.request_ollama", side_effect=responses):
            selected = run_tool_agent(7, 3, 1, self.actions, payload)

        self.assertIsNotNone(selected)
        self.assertEqual(selected.action_index, 1)

    def test_tool_loop_rejects_noncanonical_qwen_json_content(self) -> None:
        payload = bytes(1049)
        for content in (
            "I choose action 1",
            '{"name":"list_legal_actions","arguments":{},"extra":true}',
            '{"name":"list_legal_actions","arguments":[]}',
        ):
            with self.subTest(content=content), mock.patch("battle_agent_service.request_ollama", return_value={"content": content}):
                self.assertIsNone(run_tool_agent(7, 3, 1, self.actions, payload))

    def test_tool_loop_retries_one_malformed_reply_before_a_legal_choice(self) -> None:
        payload = bytes(1049)
        responses = [
            {"content": '{"name": list_legal_actions, "arguments": {}}'},
            {"content": '{"name":"list_legal_actions","arguments":{}}'},
            {"content": '{"name":"choose_action","arguments":{"action_index":1}}'},
        ]

        with mock.patch("battle_agent_service.request_ollama", side_effect=responses) as request:
            selected = run_tool_agent(7, 3, 1, self.actions, payload)

        self.assertIsNotNone(selected)
        self.assertEqual(selected.action_index, 1)
        self.assertEqual(selected.tools_used, ("list_legal_actions", "choose_action"))
        self.assertEqual(request.call_count, 3)
        self.assertEqual(
            json.loads(request.call_args_list[2].args[0][-1]["content"]),
            list_legal_actions(self.actions),
        )

    def test_decision_audit_reports_tools_actions_and_rom_facts(self) -> None:
        payload = _v3_payload()
        requester_move = 9 + 92 + 44 + 12
        payload[requester_move : requester_move + 12] = bytes((52, 0, 20, 10, 40, 100, 0, 0, 0, 0, 1, 0))
        payload[9 + 18 : 9 + 20] = (18).to_bytes(2, "little")
        payload[9 + 92 + 18 : 9 + 92 + 20] = (27).to_bytes(2, "little")

        audit = format_decision_audit(7, 1, AgentDecision(1, ("get_battle_state", "list_legal_actions")), self.actions, bytes(payload))

        self.assertIn("audit #7", audit)
        self.assertIn("tools used: get_battle_state, list_legal_actions", audit)
        self.assertIn("legal actions: 0=", audit)
        self.assertIn("selected: 1=EMBER->battler 0", audit)
        self.assertIn("selected ROM facts: STAB=yes, effectiveness=super-effective, KO=yes", audit)
        self.assertIn("speed context: battler_1_first", audit)
        self.assertNotIn("reasoning", audit)
        self.assertNotIn("payload", audit)

    def test_handle_request_frame_emits_audit_before_a_valid_response(self) -> None:
        payload = _v3_payload()
        payload[0:4] = (7).to_bytes(4, "little")
        payload[4:9] = bytes((1, 1, 3, 0, 2))
        payload[968:977] = bytes((1, 0, 0, 0, 0, 255, 2, 1, 0))
        frame = b"BAGB\x03\x01\x19\x04" + bytes(payload)

        with mock.patch("battle_agent_service.run_tool_agent", return_value=AgentDecision(0, ("list_legal_actions", "choose_action"))), mock.patch("battle_agent_service.log") as log:
            self.assertEqual(handle_request_frame(frame), b"BAGB\x03\x02\x05\x00\x07\x00\x00\x00\x00")

        self.assertTrue(any(call.args[0].startswith("audit #7") for call in log.call_args_list))

    def test_handle_request_frame_audits_vanilla_fallback_without_a_response(self) -> None:
        payload = _v3_payload()
        payload[0:4] = (7).to_bytes(4, "little")
        payload[4:9] = bytes((1, 1, 3, 0, 2))
        payload[968:977] = bytes((1, 0, 0, 0, 0, 255, 2, 1, 0))
        frame = b"BAGB\x03\x01\x19\x04" + bytes(payload)

        with mock.patch("battle_agent_service.run_tool_agent", return_value=None), mock.patch("battle_agent_service.log") as log:
            self.assertIsNone(handle_request_frame(frame))

        log.assert_any_call("audit #7: no legal model decision; vanilla_fallback")

    def test_tool_loop_rejects_a_second_malformed_reply(self) -> None:
        payload = bytes(1049)
        responses = [
            {"content": '{"name": list_legal_actions, "arguments": {}}'},
            {"content": '{"name": choose_action, "arguments": {}}'},
        ]

        with mock.patch("battle_agent_service.request_ollama", side_effect=responses) as request:
            self.assertIsNone(run_tool_agent(7, 3, 1, self.actions, payload))

        self.assertEqual(request.call_count, 2)

    def test_tool_loop_rejects_text_only_or_unknown_tool_completion(self) -> None:
        payload = bytes(1049)
        for response in ({}, {"tool_calls": [{"function": {"name": "open_shell", "arguments": {}}}]}):
            with self.subTest(response=response), mock.patch("battle_agent_service.request_ollama", return_value=response):
                self.assertIsNone(run_tool_agent(7, 3, 1, self.actions, payload))

    def test_service_emits_a_fixed_response_only_after_a_legal_selection(self) -> None:
        payload = _v3_payload()
        payload[0:4] = (7).to_bytes(4, "little")
        payload[4:9] = bytes((1, 1, 3, 0, 2))
        payload[968:977] = bytes((1, 0, 0, 0, 0, 255, 2, 1, 0))
        frame = b"BAGB\x03\x01\x19\x04" + bytes(payload)

        with mock.patch("battle_agent_service.run_tool_agent", return_value=AgentDecision(0, ("choose_action",))):
            self.assertEqual(handle_request_frame(frame), b"BAGB\x03\x02\x05\x00\x07\x00\x00\x00\x00")

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
