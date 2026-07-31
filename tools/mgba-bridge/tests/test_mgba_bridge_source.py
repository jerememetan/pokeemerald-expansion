"""Source-contract checks for the bounded BAGB/3 Lua bridge."""

from __future__ import annotations

import unittest
from pathlib import Path


SOURCE = (Path(__file__).resolve().parents[1] / "mgba_bridge.lua").read_text(encoding="utf-8")


class LuaBridgeV3SourceTests(unittest.TestCase):
    def test_uses_v3_fixed_binary_frames(self) -> None:
        for value in (
            "local MAGIC = 0x42414732", "local VERSION = 3",
            "local REQUEST_FRAME_SIZE = 1057", "local RESPONSE_FRAME_SIZE = 13",
            "local REQUEST_PAYLOAD_SIZE = 1049", "local RESPONSE_PAYLOAD_SIZE = 5",
            "local function append_battler_record(parts, base, moves_base)",
            "local function append_party_member(parts, slot)",
            "local function parse_response_frame(frame)",
            "local OFFSET_LEGAL_ACTIONS = 1068",
            "local OFFSET_RESPONSE_SEQUENCE = 1148",
            "local OFFSET_RESPONSE_ACTION_INDEX = 1152",
        ):
            self.assertIn(value, SOURCE)
        self.assertNotIn("BAGB/1 REQUEST", SOURCE)
        self.assertNotIn("socket.connect", SOURCE)
        self.assertNotIn("contains_only_non_nul_ascii", SOURCE)
        self.assertNotIn("parse_u32(token)", SOURCE)

    def test_keeps_loopback_binding_and_response_commit_order(self) -> None:
        self.assertIn('BRIDGE_HOST ~= "127.0.0.1"', SOURCE)
        sequence = SOURCE.index("emu:write32(MAILBOX_ADDRESS + OFFSET_RESPONSE_SEQUENCE, response.sequence)")
        action = SOURCE.index("emu:write8(MAILBOX_ADDRESS + OFFSET_RESPONSE_ACTION_INDEX, response.action_index)")
        status = SOURCE.index("emu:write8(MAILBOX_ADDRESS + OFFSET_RESPONSE_STATUS, RESPONSE_READY)")
        self.assertLess(sequence, action)
        self.assertLess(action, status)

    def test_response_requires_exact_binary_length(self) -> None:
        self.assertIn("if #receive_buffer > RESPONSE_FRAME_SIZE then", SOURCE)
        self.assertIn("if #receive_buffer < RESPONSE_FRAME_SIZE then", SOURCE)
        self.assertIn("response.action_index < header.action_count", SOURCE)

    def test_request_assembly_includes_each_move_reserved_byte_and_checks_payload_size(self) -> None:
        move_serialization = SOURCE[SOURCE.index("for slot = 0, 3 do"):SOURCE.index("local function append_battler(parts, battler)")]
        self.assertIn("append_u8(parts, 0)", move_serialization)
        self.assertIn("if #payload_bytes ~= REQUEST_PAYLOAD_SIZE then", SOURCE)

    def test_request_assembly_includes_party_and_full_action_records(self) -> None:
        action_serialization = SOURCE[SOURCE.index("for slot = 0, PARTY_SIZE - 1 do"):SOURCE.index("local payload_bytes")]
        self.assertIn("append_party_member(payload, slot)", action_serialization)
        self.assertIn("for index = 0, 9 do", action_serialization)
        self.assertIn("for field = 0, 7", action_serialization)


if __name__ == "__main__":
    unittest.main()
