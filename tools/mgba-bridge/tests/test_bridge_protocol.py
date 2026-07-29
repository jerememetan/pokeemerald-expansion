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
    MAX_LINE_BYTES,
    PROTOCOL,
    ProtocolError,
    Request,
    Response,
    format_response,
    parse_request,
    parse_response,
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
