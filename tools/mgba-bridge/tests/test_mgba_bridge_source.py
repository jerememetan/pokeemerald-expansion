"""Source-contract checks for the bounded BAGB/5 Lua bridge."""

from __future__ import annotations

import unittest
from pathlib import Path


SOURCE = (Path(__file__).resolve().parents[1] / "mgba_bridge.lua").read_text(encoding="utf-8")


class LuaBridgeV5SourceTests(unittest.TestCase):
    def test_uses_v5_fixed_atomic_binary_frames(self) -> None:
        for value in (
            "local MAGIC = 0x42414732", "local VERSION = 5",
            "local REQUEST_FRAME_SIZE = 1377", "local RESPONSE_FRAME_SIZE = 17",
            "local REQUEST_PAYLOAD_SIZE = 1369", "local RESPONSE_PAYLOAD_SIZE = 9",
            "local MAX_ACTIONS_PER_BATTLER = 22", "local ACTION_RECORD_SIZE = 9",
            "local OFFSET_LEGAL_ACTIONS = 1072",
            "local OFFSET_RESPONSE_SEQUENCE = 1468",
            "local OFFSET_RESPONSE_ACTION_COUNT = 1472",
            "local function append_battler_record(parts, base, moves_base)",
            "local function append_party_member(parts, slot)",
            "local function parse_response_frame(frame)",
        ):
            self.assertIn(value, SOURCE)
        self.assertNotIn("BAGB/1 REQUEST", SOURCE)
        self.assertNotIn("socket.connect", SOURCE)

    def test_keeps_loopback_binding_and_atomic_response_commit_order(self) -> None:
        self.assertIn('BRIDGE_HOST ~= "127.0.0.1"', SOURCE)
        sequence = SOURCE.index("emu:write32(MAILBOX_ADDRESS + OFFSET_RESPONSE_SEQUENCE, response.sequence)")
        count = SOURCE.index("emu:write8(MAILBOX_ADDRESS + OFFSET_RESPONSE_ACTION_COUNT, response.action_count)")
        first_action = SOURCE.index("emu:write8(MAILBOX_ADDRESS + OFFSET_RESPONSE_ACTION_INDEXES, response.action_indexes[1])")
        status = SOURCE.index("emu:write8(MAILBOX_ADDRESS + OFFSET_RESPONSE_STATUS, RESPONSE_READY)")
        self.assertLess(sequence, count)
        self.assertLess(count, first_action)
        self.assertLess(first_action, status)

    def test_response_requires_exact_length_and_matches_every_controlled_battler(self) -> None:
        self.assertIn("if #receive_buffer > RESPONSE_FRAME_SIZE then", SOURCE)
        self.assertIn("if #receive_buffer < RESPONSE_FRAME_SIZE then", SOURCE)
        self.assertIn("response.action_count == header.controlled_count", SOURCE)
        self.assertIn("response.battlers[1] == header.controlled[1]", SOURCE)

    def test_request_assembly_includes_each_move_reserved_byte_and_checks_payload_size(self) -> None:
        move_serialization = SOURCE[SOURCE.index("for slot = 0, 3 do"):SOURCE.index("local function append_battler(parts, battler)")]
        self.assertIn("append_u8(parts, 0)", move_serialization)
        self.assertIn("if #payload_bytes ~= REQUEST_PAYLOAD_SIZE then", SOURCE)

    def test_request_assembly_includes_party_and_both_action_lists(self) -> None:
        action_serialization = SOURCE[SOURCE.index("for slot = 0, PARTY_SIZE - 1 do"):SOURCE.index("local payload_bytes")]
        self.assertIn("append_party_member(payload, slot)", action_serialization)
        self.assertIn("for list = 0, 1 do", action_serialization)
        self.assertIn("for index = 0, MAX_ACTIONS_PER_BATTLER - 1 do", action_serialization)
        self.assertIn("for field = 0, ACTION_RECORD_SIZE - 1", action_serialization)


if __name__ == "__main__":
    unittest.main()
