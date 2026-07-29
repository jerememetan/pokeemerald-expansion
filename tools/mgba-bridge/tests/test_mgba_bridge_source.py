"""Source-contract regression tests for the mGBA Lua listener probe."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "mgba_bridge.lua"


class LuaListenerSourceContractTests(unittest.TestCase):
    def test_listen_uses_the_lua_success_sentinel_and_rejects_errors(self) -> None:
        source = SCRIPT_PATH.read_text(encoding="utf-8")

        self.assertIn("local LUA_SOCKET_SUCCESS = 1", source)
        self.assertIn(
            "if not ok_listen or listen_result ~= LUA_SOCKET_SUCCESS then", source
        )
        self.assertNotIn("listen_result ~= sockerr_ok", source)

    def test_mailbox_bridge_uses_only_the_phase_3a_header_contract(self) -> None:
        source = SCRIPT_PATH.read_text(encoding="utf-8")

        for constant in (
            "local MAGIC = 0x42414731",
            "local VERSION = 1",
            "local REQUEST_PENDING = 1",
            "local RESPONSE_READY = 1",
            "local OFFSET_MAGIC = 0",
            "local OFFSET_VERSION = 4",
            "local OFFSET_REQUEST_STATUS = 6",
            "local OFFSET_RESPONSE_STATUS = 7",
            "local OFFSET_REQUEST_SEQUENCE = 8",
            "local OFFSET_REQUESTING_BATTLER = 12",
            "local OFFSET_BATTLE_MODE = 13",
            "local OFFSET_LEGAL_ACTION_COUNT = 128",
            "local OFFSET_RESPONSE_SEQUENCE = 148",
            "local OFFSET_RESPONSE_ACTION_INDEX = 152",
            "local TRAINER_SINGLE = 1",
            "local function read_mailbox_header()",
            "local function is_forwardable(header)",
        ):
            self.assertIn(constant, source)

        for read in (
            "emu:read32(MAILBOX_ADDRESS + OFFSET_MAGIC)",
            "emu:read16(MAILBOX_ADDRESS + OFFSET_VERSION)",
            "emu:read8(MAILBOX_ADDRESS + OFFSET_REQUEST_STATUS)",
            "emu:read32(MAILBOX_ADDRESS + OFFSET_REQUEST_SEQUENCE)",
            "emu:read8(MAILBOX_ADDRESS + OFFSET_REQUESTING_BATTLER)",
            "emu:read8(MAILBOX_ADDRESS + OFFSET_BATTLE_MODE)",
            "emu:read8(MAILBOX_ADDRESS + OFFSET_LEGAL_ACTION_COUNT)",
        ):
            self.assertIn(read, source)

    def test_all_mailbox_accesses_are_from_the_allowlist_in_order(self) -> None:
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        expected = [
            "emu:read32(MAILBOX_ADDRESS + OFFSET_MAGIC)",
            "emu:read16(MAILBOX_ADDRESS + OFFSET_VERSION)",
            "emu:read8(MAILBOX_ADDRESS + OFFSET_REQUEST_STATUS)",
            "emu:read32(MAILBOX_ADDRESS + OFFSET_REQUEST_SEQUENCE)",
            "emu:read8(MAILBOX_ADDRESS + OFFSET_REQUESTING_BATTLER)",
            "emu:read8(MAILBOX_ADDRESS + OFFSET_BATTLE_MODE)",
            "emu:read8(MAILBOX_ADDRESS + OFFSET_LEGAL_ACTION_COUNT)",
            "emu:write32(MAILBOX_ADDRESS + OFFSET_RESPONSE_SEQUENCE, response.sequence)",
            "emu:write8(MAILBOX_ADDRESS + OFFSET_RESPONSE_ACTION_INDEX, response.action_index)",
            "emu:write8(MAILBOX_ADDRESS + OFFSET_RESPONSE_STATUS, RESPONSE_READY)",
        ]

        self.assertEqual(self._all_emu_accesses(source), expected)
        self.assertNotEqual(
            self._all_emu_accesses(source + "\nemu:write8(0x02000000, 1)\n"),
            expected,
        )

    @staticmethod
    def _all_emu_accesses(source: str) -> list[str]:
        normalized = re.sub(r"\s+", " ", source)
        return re.findall(r"emu:(?:read|write)(?:8|16|32)\([^)]*\)", normalized)

    def test_response_commit_is_bounded_and_writes_only_in_commit_order(self) -> None:
        source = SCRIPT_PATH.read_text(encoding="utf-8")

        for contract in (
            "local function send_request(header)",
            "local function parse_response_line(line)",
            "local function response_matches_current(response)",
            "local function commit_response(response)",
            "#receive_buffer > MAX_LINE_BYTES",
            '"BAGB/1 REQUEST " .. header.sequence .. " " .. header.action_count .. "\\n"',
            "response.action_index < header.action_count",
            "emu:write32(MAILBOX_ADDRESS + OFFSET_RESPONSE_SEQUENCE, response.sequence)",
            "emu:write8(MAILBOX_ADDRESS + OFFSET_RESPONSE_ACTION_INDEX, response.action_index)",
            "emu:write8(MAILBOX_ADDRESS + OFFSET_RESPONSE_STATUS, RESPONSE_READY)",
        ):
            self.assertIn(contract, source)

        sequence_write = source.index(
            "emu:write32(MAILBOX_ADDRESS + OFFSET_RESPONSE_SEQUENCE, response.sequence)"
        )
        action_write = source.index(
            "emu:write8(MAILBOX_ADDRESS + OFFSET_RESPONSE_ACTION_INDEX, response.action_index)"
        )
        status_write = source.index(
            "emu:write8(MAILBOX_ADDRESS + OFFSET_RESPONSE_STATUS, RESPONSE_READY)"
        )
        self.assertLess(sequence_write, action_write)
        self.assertLess(action_write, status_write)

    def test_each_forwarded_sequence_can_commit_only_once(self) -> None:
        source = SCRIPT_PATH.read_text(encoding="utf-8")

        self.assertIn("local committed_sequence = nil", source)
        self.assertIn("committed_sequence ~= response.sequence", source)
        self.assertIn("committed_sequence = response.sequence", source)

    def test_coalesced_input_is_rejected_before_response_commit(self) -> None:
        source = SCRIPT_PATH.read_text(encoding="utf-8")

        self.assertIn("if newline_index < #receive_buffer then", source)
        self.assertIn('disconnect_client("multiple response lines in one receive")', source)

    def test_partial_request_send_never_marks_a_sequence_forwarded(self) -> None:
        source = SCRIPT_PATH.read_text(encoding="utf-8")

        self.assertIn("send_result ~= #request_line", source)
        partial_check = source.index("send_result ~= #request_line")
        forwarded_mark = source.index("forwarded_sequence = header.sequence")
        self.assertLess(partial_check, forwarded_mark)

    def test_identity_mismatch_stops_before_non_identity_mailbox_reads(self) -> None:
        source = SCRIPT_PATH.read_text(encoding="utf-8")

        self.assertIn("if magic ~= MAGIC or version ~= VERSION then", source)
        self.assertIn("if header == nil then", source)
        magic_read = source.index("emu:read32(MAILBOX_ADDRESS + OFFSET_MAGIC)")
        version_read = source.index("emu:read16(MAILBOX_ADDRESS + OFFSET_VERSION)")
        mismatch_guard = source.index("if magic ~= MAGIC or version ~= VERSION then")
        identity_reject = source.index("return nil", mismatch_guard)
        request_read = source.index("emu:read8(MAILBOX_ADDRESS + OFFSET_REQUEST_STATUS)")

        self.assertLess(magic_read, version_read)
        self.assertLess(version_read, mismatch_guard)
        self.assertLess(mismatch_guard, identity_reject)
        self.assertLess(identity_reject, request_read)

    def test_successful_new_request_clears_old_partial_response_before_forwarding(self) -> None:
        source = SCRIPT_PATH.read_text(encoding="utf-8")

        send_success_check = source.index("send_result ~= #request_line")
        clear_buffer = source.index('receive_buffer = ""', send_success_check)
        forwarded_mark = source.index("forwarded_sequence = header.sequence")
        self.assertLess(send_success_check, clear_buffer)
        self.assertLess(clear_buffer, forwarded_mark)


if __name__ == "__main__":
    unittest.main()
