"""Tests for the bounded BAGB/1 bridge-line protocol."""

from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest import mock


BRIDGE_DIRECTORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BRIDGE_DIRECTORY))

from bridge_protocol import (  # noqa: E402
    ACTION_KIND_MOVE,
    ACTION_KIND_SWITCH,
    ACTION_NONE,
    MAX_LEGAL_ACTIONS,
    MAX_LINE_BYTES,
    PROTOCOL,
    ProtocolError,
    Request,
    Response,
    format_response,
    parse_request,
    parse_response,
)
from bridge_protocol import (  # noqa: E402
    REQUEST_FRAME_SIZE,
    RESPONSE_FRAME_SIZE,
    ACTION_RECORD_SIZE,
    BATTLE_MODE_TRAINER_DOUBLE,
    MAX_ACTIONS_PER_BATTLER,
    VERSION,
    format_response_frame,
    parse_request_frame,
)
import test_responder  # noqa: E402


class FakeSocket:
    def __init__(
        self,
        received_chunks: list[bytes | OSError],
        send_error: OSError | None = None,
    ) -> None:
        self._received_chunks = list(received_chunks)
        self._send_error = send_error
        self.received_sizes: list[int] = []
        self.sent: list[bytes] = []
        self.timeout_values: list[float | None] = []
        self.closed = False

    def settimeout(self, value: float | None) -> None:
        self.timeout_values.append(value)

    def recv(self, size: int) -> bytes:
        self.received_sizes.append(size)
        if not self._received_chunks:
            return b""
        next_chunk = self._received_chunks.pop(0)
        if isinstance(next_chunk, OSError):
            raise next_chunk
        return next_chunk

    def sendall(self, data: bytes) -> None:
        if self._send_error is not None:
            raise self._send_error
        self.sent.append(data)

    def close(self) -> None:
        self.closed = True


class BridgeProtocolTests(unittest.TestCase):
    @staticmethod
    def _v4_double_payload() -> bytearray:
        payload = bytearray(1369)
        party_offset = 397
        legal_action_offset = 973
        for party_slot in range(6):
            payload[party_offset + party_slot * 96] = party_slot
            payload[party_offset + party_slot * 96 + 3] = ACTION_NONE
        payload[0:4] = (7).to_bytes(4, "little")
        payload[4] = BATTLE_MODE_TRAINER_DOUBLE
        payload[5] = 2
        payload[6:8] = (3).to_bytes(2, "little")
        payload[8] = 4
        payload[9:13] = bytes((1, 3, 2, 2))
        payload[legal_action_offset : legal_action_offset + ACTION_RECORD_SIZE] = bytes(
            (1, 0, ACTION_KIND_MOVE, 0, 3, ACTION_NONE, 2, 1, 0)
        )
        payload[
            legal_action_offset + ACTION_RECORD_SIZE : legal_action_offset + 2 * ACTION_RECORD_SIZE
        ] = bytes((1, 1, ACTION_KIND_SWITCH, ACTION_NONE, ACTION_NONE, 4, 0, 0, 0))
        right_offset = legal_action_offset + MAX_ACTIONS_PER_BATTLER * ACTION_RECORD_SIZE
        payload[right_offset : right_offset + ACTION_RECORD_SIZE] = bytes(
            (3, 0, ACTION_KIND_MOVE, 1, 0, ACTION_NONE, 3, 1, 1)
        )
        payload[right_offset + ACTION_RECORD_SIZE : right_offset + 2 * ACTION_RECORD_SIZE] = bytes(
            (3, 1, ACTION_KIND_SWITCH, ACTION_NONE, ACTION_NONE, 5, 0, 0, 0)
        )
        return payload

    def test_v4_double_request_frame_has_two_actor_keyed_action_lists(self) -> None:
        payload = self._v4_double_payload()
        frame = b"BAGB" + bytes((VERSION, 1)) + len(payload).to_bytes(2, "little") + bytes(payload)

        request = parse_request_frame(frame)

        self.assertEqual(request.sequence, 7)
        self.assertEqual(request.battle_mode, BATTLE_MODE_TRAINER_DOUBLE)
        self.assertEqual(request.controlled_battlers, (1, 3))
        self.assertEqual(request.battler_count, 4)
        self.assertEqual(request.actions_by_battler[1][0].target_battler, 3)
        self.assertEqual(request.actions_by_battler[1][1].party_slot, 4)
        self.assertEqual(request.actions_by_battler[3][0].target_battler, 0)
        self.assertEqual(request.actions_by_battler[3][1].party_slot, 5)

    def test_v5_two_trainer_double_requires_owner_labelled_party_metadata(self) -> None:
        payload = self._v4_double_payload()
        payload[4] = 3
        for party_slot in range(6):
            payload[397 + party_slot * 96 + 3] = 1 if party_slot < 3 else 3
        frame = b"BAGB" + bytes((5, 1)) + len(payload).to_bytes(2, "little") + bytes(payload)

        try:
            request = parse_request_frame(frame)
        except ProtocolError as error:
            self.fail(f"BAGB/5 two-trainer frame was rejected: {error}")

        self.assertEqual(request.battle_mode, 3)
        self.assertEqual(
            [request.payload[397 + party_slot * 96 + 3] for party_slot in range(6)],
            [1, 1, 1, 3, 3, 3],
        )

        v4_frame = b"BAGB" + bytes((4, 1)) + len(payload).to_bytes(2, "little") + bytes(payload)
        with self.assertRaises(ProtocolError):
            parse_request_frame(v4_frame)

    def test_v4_double_response_frame_contains_an_atomic_action_pair(self) -> None:
        frame = format_response_frame(7, ((1, 0), (3, 1)))

        self.assertEqual(len(frame), RESPONSE_FRAME_SIZE)
        self.assertEqual(frame, b"BAGB" + bytes((VERSION, 2, 9, 0, 7, 0, 0, 0, 2, 1, 0, 3, 1)))

    def test_v4_pair_response_rejects_a_duplicate_or_excess_actor(self) -> None:
        for actions in (((1, 0), (1, 1)), ((1, 0), (3, 1), (2, 0))):
            with self.subTest(actions=actions):
                with self.assertRaises(ProtocolError):
                    format_response_frame(7, actions)

    @staticmethod
    def _v4_single_payload() -> bytearray:
        payload = bytearray(1369)
        for party_slot in range(6):
            payload[397 + party_slot * 96] = party_slot
            payload[397 + party_slot * 96 + 3] = ACTION_NONE
        payload[4:13] = bytes((1, 1, 3, 0, 2, 1, ACTION_NONE, 0, 0))
        return payload

    def test_external_switching_uses_protocol_v5(self) -> None:
        self.assertEqual(VERSION, 5)

    def test_v4_single_request_frame_parses_move_and_switch_actions(self) -> None:
        payload = self._v4_single_payload()
        payload[0:4] = (7).to_bytes(4, "little")
        payload[11] = 2
        payload[973:982] = bytes((1, 0, ACTION_KIND_MOVE, 1, 0, ACTION_NONE, 2, 1, 0))
        payload[982:991] = bytes((1, 1, ACTION_KIND_SWITCH, ACTION_NONE, ACTION_NONE, 4, 0, 0, 0))
        frame = b"BAGB" + bytes((VERSION, 1)) + len(payload).to_bytes(2, "little") + bytes(payload)

        request = parse_request_frame(frame)

        self.assertEqual(len(frame), REQUEST_FRAME_SIZE)
        self.assertEqual(request.sequence, 7)
        self.assertEqual(request.controlled_battlers, (1,))
        self.assertEqual(request.turn_sequence, 3)
        self.assertEqual(request.battler_count, 2)
        self.assertEqual(request.actions_by_battler[1][0].action_index, 0)
        self.assertEqual(request.actions_by_battler[1][0].move_slot, 1)
        self.assertEqual(request.actions_by_battler[1][1].kind, ACTION_KIND_SWITCH)
        self.assertEqual(request.actions_by_battler[1][1].party_slot, 4)

    def test_v4_request_frame_rejects_wrong_or_extra_bytes(self) -> None:
        valid = b"BAGB" + bytes((VERSION, 1)) + (1369).to_bytes(2, "little") + bytes(1369)
        for frame in (valid[:-1], valid + b"x", b"BAGB" + bytes((3, 1)) + valid[6:]):
            with self.subTest(frame_length=len(frame)):
                with self.assertRaises(ProtocolError):
                    parse_request_frame(frame)

    def test_v4_single_response_frame_has_fixed_binary_shape(self) -> None:
        frame = format_response_frame(7, ((1, 9),))

        self.assertEqual(len(frame), RESPONSE_FRAME_SIZE)
        self.assertEqual(frame, b"BAGB" + bytes((VERSION, 2, 9, 0, 7, 0, 0, 0, 1, 1, 9, 255, 255)))

    def test_v4_request_rejects_a_malformed_switch_action(self) -> None:
        payload = self._v4_single_payload()
        payload[11] = 1
        payload[973:982] = bytes((1, 0, ACTION_KIND_SWITCH, 0, ACTION_NONE, 2, 0, 0, 0))
        frame = b"BAGB" + bytes((VERSION, 1)) + len(payload).to_bytes(2, "little") + bytes(payload)

        with self.assertRaises(ProtocolError):
            parse_request_frame(frame)

    def test_v4_request_rejects_noncontiguous_action_indexes(self) -> None:
        payload = self._v4_single_payload()
        payload[11] = 1
        payload[973:982] = bytes((1, 1, ACTION_KIND_MOVE, 0, 0, ACTION_NONE, 2, 1, 0))
        frame = b"BAGB" + bytes((VERSION, 1)) + len(payload).to_bytes(2, "little") + bytes(payload)

        with self.assertRaises(ProtocolError):
            parse_request_frame(frame)

    def test_v4_request_rejects_invalid_party_metadata(self) -> None:
        payload = self._v4_single_payload()
        payload[397:401] = bytes((2, 0, 1, 0))
        payload[11] = 1
        payload[973:982] = bytes((1, 0, ACTION_KIND_MOVE, 0, 0, ACTION_NONE, 2, 1, 0))
        frame = b"BAGB" + bytes((VERSION, 1)) + len(payload).to_bytes(2, "little") + bytes(payload)

        with self.assertRaises(ProtocolError):
            parse_request_frame(frame)

    def test_v4_response_accepts_the_last_bounded_action(self) -> None:
        self.assertEqual(format_response_frame(7, ((1, MAX_LEGAL_ACTIONS - 1),))[14], MAX_LEGAL_ACTIONS - 1)

    def test_request_parses_a_valid_bounded_line(self) -> None:
        self.assertEqual(
            parse_request(b"BAGB/1 REQUEST 7 3\n"),
            Request(sequence=7, action_count=3),
        )

    def test_request_parses_a_valid_exactly_96_byte_line(self) -> None:
        line = b"BAGB/1 REQUEST " + b"0" * 77 + b"7 3\n"
        self.assertEqual(len(line), MAX_LINE_BYTES)
        self.assertEqual(parse_request(line), Request(sequence=7, action_count=3))

    def test_response_parses_a_valid_bounded_line(self) -> None:
        self.assertEqual(
            parse_response(b"BAGB/1 RESPONSE 7 0\n"),
            Response(sequence=7, action_index=0),
        )

    def test_format_response_returns_the_exact_protocol_line(self) -> None:
        self.assertEqual(format_response(7, 0), b"BAGB/1 RESPONSE 7 0\n")

    def test_request_rejects_malformed_lines(self) -> None:
        invalid_lines = (
            b"BAGB/1 REQUEST 7 3",
            b"BAGB/1 REQUEST 7 3\n\n",
            b"BAGB/1 REQUEST 7 3\nextra",
            b"BAGB/2 REQUEST 7 3\n",
            b"BAGB/1 RESPONSE 7 3\n",
            b"BAGB/1 REQUEST 7\n",
            b"BAGB/1 REQUEST 7 3 extra\n",
            b"BAGB/1 REQUEST +7 3\n",
            b"BAGB/1 REQUEST -7 3\n",
            b"BAGB/1 REQUEST seven 3\n",
            b"BAGB/1 REQUEST 4294967296 3\n",
            b"BAGB/1 REQUEST 7 0\n",
            b"BAGB/1 REQUEST 7 5\n",
            b"BAGB/1 REQUEST 7 3\x00\n",
            b"BAGB/1 REQUEST 7 \xff\n",
            b"x" * 96 + b"\n",
        )

        for line in invalid_lines:
            with self.subTest(line=line):
                with self.assertRaises(ProtocolError):
                    parse_request(line)

    def test_response_rejects_malformed_lines(self) -> None:
        invalid_lines = (
            b"BAGB/1 RESPONSE 7 0",
            b"BAGB/1 RESPONSE 7 0\n\n",
            b"BAGB/2 RESPONSE 7 0\n",
            b"BAGB/1 REQUEST 7 1\n",
            b"BAGB/1 RESPONSE 7\n",
            b"BAGB/1 RESPONSE 7 0 extra\n",
            b"BAGB/1 RESPONSE +7 0\n",
            b"BAGB/1 RESPONSE -7 0\n",
            b"BAGB/1 RESPONSE 7 nope\n",
            b"BAGB/1 RESPONSE 4294967296 0\n",
            b"BAGB/1 RESPONSE 7 4\n",
            b"BAGB/1 RESPONSE 7 0\x00\n",
            b"BAGB/1 RESPONSE 7 \xff\n",
            b"x" * 96 + b"\n",
        )

        for line in invalid_lines:
            with self.subTest(line=line):
                with self.assertRaises(ProtocolError):
                    parse_response(line)

    def test_format_response_rejects_invalid_values(self) -> None:
        for sequence, action_index in (
            (-1, 0),
            (4294967296, 0),
            (7, -1),
            (7, 4),
            ("7", 0),
            (7, "0"),
        ):
            with self.subTest(sequence=sequence, action_index=action_index):
                with self.assertRaises(ProtocolError):
                    format_response(sequence, action_index)

    def test_protocol_constants_are_frozen(self) -> None:
        self.assertEqual(MAX_LINE_BYTES, 96)
        self.assertEqual(PROTOCOL, b"BAGB/1")

    def test_responder_rejects_a_host_override(self) -> None:
        with mock.patch.object(sys, "argv", ["test_responder.py", "--host", "127.0.0.2"]):
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    test_responder._parse_arguments()

    def test_responder_rejects_invalid_port_arguments(self) -> None:
        for port in ("0", "65536", "not-a-number"):
            with self.subTest(port=port):
                with mock.patch.object(sys, "argv", ["test_responder.py", "--port", port]):
                    with contextlib.redirect_stderr(io.StringIO()):
                        with self.assertRaises(SystemExit):
                            test_responder._parse_arguments()

    def test_responder_retries_loopback_connection_once(self) -> None:
        connected_socket = FakeSocket([])
        with mock.patch.object(
            test_responder.socket,
            "create_connection",
            side_effect=[OSError("not ready"), connected_socket],
        ) as create_connection:
            with mock.patch.object(test_responder.time, "sleep") as sleep:
                self.assertIs(test_responder._connect(57621), connected_socket)

        self.assertEqual(
            create_connection.call_args_list,
            [
                mock.call(("127.0.0.1", 57621), timeout=1),
                mock.call(("127.0.0.1", 57621), timeout=1),
            ],
        )
        sleep.assert_called_once_with(0.25)
        self.assertEqual(connected_socket.timeout_values, [None])

    def test_responder_reassembles_a_fragmented_request(self) -> None:
        connection = FakeSocket([b"BAGB/1 REQUEST 7 ", b"3\n", b""])

        test_responder._serve(connection)

        self.assertEqual(connection.sent, [b"BAGB/1 RESPONSE 7 0\n"])
        self.assertTrue(connection.closed)

    def test_responder_processes_coalesced_complete_requests(self) -> None:
        connection = FakeSocket([b"BAGB/1 REQUEST 7 1\nBAGB/1 REQUEST 8 4\n", b""])

        test_responder._serve(connection)

        self.assertEqual(
            connection.sent,
            [b"BAGB/1 RESPONSE 7 0\n", b"BAGB/1 RESPONSE 8 0\n"],
        )
        self.assertTrue(connection.closed)

    def test_responder_closes_on_malformed_input_without_a_response(self) -> None:
        connection = FakeSocket([b"BAGB/1 REQUEST 7 0\n"])

        test_responder._serve(connection)

        self.assertEqual(connection.sent, [])
        self.assertEqual(connection.received_sizes, [MAX_LINE_BYTES])
        self.assertTrue(connection.closed)

    def test_responder_closes_when_sending_a_valid_response_fails(self) -> None:
        connection = FakeSocket(
            [b"BAGB/1 REQUEST 7 1\n"],
            send_error=OSError("send failed"),
        )

        test_responder._serve(connection)

        self.assertEqual(connection.sent, [])
        self.assertTrue(connection.closed)

    def test_responder_closes_on_overflow_without_a_response(self) -> None:
        connection = FakeSocket([b"x" * MAX_LINE_BYTES, b"x"])

        test_responder._serve(connection)

        self.assertEqual(connection.sent, [])
        self.assertEqual(connection.received_sizes, [MAX_LINE_BYTES, MAX_LINE_BYTES])
        self.assertTrue(connection.closed)

    def test_responder_closes_cleanly_on_eof(self) -> None:
        connection = FakeSocket([b""])

        test_responder._serve(connection)

        self.assertEqual(connection.sent, [])
        self.assertTrue(connection.closed)

    def test_responder_closes_cleanly_on_receive_error(self) -> None:
        connection = FakeSocket([OSError("receive failed")])

        test_responder._serve(connection)

        self.assertEqual(connection.sent, [])
        self.assertTrue(connection.closed)


if __name__ == "__main__":
    unittest.main()
